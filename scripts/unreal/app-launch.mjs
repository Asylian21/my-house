import { execFile } from 'node:child_process';
import { readFile, lstat } from 'node:fs/promises';
import { resolve } from 'node:path';
import { promisify } from 'node:util';
import { createHash } from 'node:crypto';
import { inspectStartupEntry } from './startup-entry.mjs';
const exec=promisify(execFile),sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export const startupFlags=Object.freeze(['-LLM','-DetectHitchesWithLLM']);
export async function requireIdleApp() {
  for(const name of ['BreziTwin','BreziStartupLauncher']) {
    try {if((await exec('pgrep',['-x',name])).stdout.trim()) throw Error(`${name} is already running; close it before packaged QA`);}
    catch(error) {if(error.code!==1)throw error;}
  }
}
export function assertEntryName(name) {
  if(name!=='BreziTwin') throw Error('Expected original GUI CFBundleExecutable=BreziTwin with the validated app-owned LC_MAIN entry');
  return 'Contents/MacOS/BreziTwin';
}
export function inspectStartupPolicy(policy,entry) {
  if(policy?.schemaVersion!==2 || policy.status!=='linked-self-exec-startup-policy' || policy.entryKind!=='same-binary-self-exec' ||
     policy.entryFile!=='Contents/MacOS/BreziTwin' || JSON.stringify(policy.forcedFlags)!==JSON.stringify(startupFlags) ||
     !/^[a-f0-9]{64}$/.test(policy.entrySourceSha256) || policy.sandboxPolicy!=='original-main-executable-original-entitlements' ||
     JSON.stringify(policy.linkedEntry)!==JSON.stringify(entry) || policy.engineSha256!==undefined || policy.executableSha256!==undefined)
    throw Error('Invalid sealed schema2 startup policy, linked entry or circular binary-hash field');
}
export async function resolveAppLaunch(app,validatedBundle=null) {
  const name=(await exec('/usr/libexec/PlistBuddy',['-c','Print :CFBundleExecutable',resolve(app,'Contents/Info.plist')])).stdout.trim();
  const entryFile=assertEntryName(name),executable=resolve(app,entryFile),stat=await lstat(executable);
  if(!stat.isFile() || stat.isSymbolicLink() || !(stat.mode&0o111))throw Error('Invalid regular original GUI executable');
  try {await lstat(resolve(app,'Contents/MacOS/BreziStartupLauncher'));throw Error('Obsolete helper executable remains in bundle');}
  catch(error) {if(error.code!=='ENOENT')throw error;}
  const policyBytes=await readFile(resolve(app,'Contents/Resources/BreziStartupPolicy.json')),policy=JSON.parse(policyBytes),bytes=await readFile(executable),entry=inspectStartupEntry(bytes);
  inspectStartupPolicy(policy,entry);
  const digest=sha(bytes),launch={entryKind:'same-binary-self-exec',entryFile,engineFile:entryFile,executable,
    executableSha256:digest,engineSha256:digest,startupPolicySha256:sha(policyBytes),forcedFlags:[...startupFlags],
    entrySourceSha256:policy.entrySourceSha256,linkedEntry:entry};
  if(validatedBundle && (validatedBundle.status!=='bundle-validated' || JSON.stringify(validatedBundle.launch)!==JSON.stringify(launch)))
    throw Error('Current entry differs from the validated bundle receipt');
  return launch;
}
export function inspectLauncherExecution(launch,outcome,log) {
  const errors=[],text=String(log),pid=outcome?.pid;
  if(!Number.isSafeInteger(pid) || pid<=1)errors.push('Missing parent-observed child PID');
  const entries=[...text.matchAll(/^BreziStartupEntry: pid=(\d+) phase=enter-engine forcedFlags=-LLM,-DetectHitchesWithLLM$/gm)];
  const execs=[...text.matchAll(/^BreziStartupEntry: pid=(\d+) phase=self-exec forcedFlags=-LLM,-DetectHitchesWithLLM$/gm)];
  if(entries.length!==1 || Number(entries[0][1])!==pid || execs.length>1 || execs.some(m=>Number(m[1])!==pid) || (execs.length && execs[0].index>entries[0].index))
    errors.push('Entry/self-exec count, order or PID differs from the parent-owned process');
  if(/^BreziStartupEntry: (?:rejected=|execv-failed-errno=)/m.test(text) || /^BreziStartupLauncher:/m.test(text))errors.push('Rejected startup or obsolete helper path');
  if(!text.includes('Engine is initialized. Leaving FEngineLoop::Init()'))errors.push('Engine initialization after app entry was not observed');
  if(outcome?.code!==0 || outcome?.signal!=null)errors.push('Game process did not exit cleanly');
  if(launch?.entryKind!=='same-binary-self-exec' || JSON.stringify(launch?.forcedFlags)!==JSON.stringify(startupFlags))errors.push('Launch receipt does not pin self-exec policy');
  return {status:errors.length?'failed':'recorded-self-exec-entry-chain',errors,pid:pid??null,selfExecCount:execs.length,
    scope:'Original GUI executable remains the main app. Parent PID matches app entry and optional single self-exec marker before engine init. AppKit fixture independently checks actual NSProcessInfo arguments; native report PID checks remain separate.'};
}
