import { execFile, spawn } from 'node:child_process';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import { randomUUID, createHash } from 'node:crypto';
import assert from 'node:assert/strict';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'), exec=promisify(execFile);
const { sealStartupEntry }=await import(resolve(root,'scripts/unreal/startup-entry-package.mjs'));
const { requireIdleApp, resolveAppLaunch }=await import(resolve(root,'scripts/unreal/app-launch.mjs'));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
if (process.argv.length!==3 || process.argv[2]!=='--execute') {console.log('Plan: original and self-exec sandboxed AppKit stand-ins, no UE or windows. --execute requires root-reserved native interval.');process.exit(0);}
await requireIdleApp();
for(const name of ['UnrealEditor','UnrealEditor-Cmd']) {
  try { if((await exec('pgrep',['-x',name])).stdout.trim()) throw Error('UE process active'); }
  catch(error) { if(error.code!==1) throw error; }
}
const output=resolve(root,'output/unreal/startup-entry-fixtures',randomUUID()); await mkdir(output,{recursive:true});
const entry=resolve(root,'unreal/BreziTwin/Source/BreziTwin/BreziStartupEntry.cpp'), stub=resolve(output,'AppKitFixture.mm');
await writeFile(stub,"#import <AppKit/AppKit.h>\n#include <stdio.h>\n#include <unistd.h>\nint main(int argc, char** argv)\n{\n    @autoreleasepool {\n        NSDictionary* before = @{ @\"nativePid\": @(getpid()), @\"argc\": @(argc),\n            @\"arguments\": [[NSProcessInfo processInfo] arguments],\n            @\"bundleIdentifier\": [[NSBundle mainBundle] bundleIdentifier] ?: [NSNull null],\n            @\"bundlePath\": [[NSBundle mainBundle] bundlePath] ?: [NSNull null],\n            @\"phase\": @\"before-sharedApplication\" };\n        NSData* encoded = [NSJSONSerialization dataWithJSONObject:before options:0 error:nil];\n        fwrite(encoded.bytes, 1, encoded.length, stdout); puts(\"\"); fflush(stdout);\n        [NSApplication sharedApplication];\n        NSDictionary* after = @{ @\"nativePid\": @(getpid()), @\"phase\": @\"sharedApplication-ready\",\n            @\"arguments\": [[NSProcessInfo processInfo] arguments],\n            @\"bundleIdentifier\": [[NSBundle mainBundle] bundleIdentifier] ?: [NSNull null],\n            @\"activationPolicy\": @([[NSRunningApplication currentApplication] activationPolicy]) };\n        encoded = [NSJSONSerialization dataWithJSONObject:after options:0 error:nil];\n        fwrite(encoded.bytes, 1, encoded.length, stdout); puts(\"\"); fflush(stdout);\n    }\n    return 0;\n}\n");
const entitlements=resolve(output,'original-entitlements.plist');
await writeFile(entitlements,'<?xml version="1.0"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>com.apple.security.app-sandbox</key><true/><key>com.apple.security.get-task-allow</key><true/><key>com.apple.security.network.client</key><true/><key>com.apple.security.network.server</key><true/></dict></plist>');
const commands=[], cases=[], signatures={};
async function run(cmd,args) {const r=await exec(cmd,args,{maxBuffer:8*1024*1024});commands.push({command:cmd,args,stdout:r.stdout,stderr:r.stderr});return r;}
async function build(mode) {
  const app=resolve(output,mode,'BreziTwin.app'), mac=resolve(app,'Contents/MacOS'); await mkdir(mac,{recursive:true});await mkdir(resolve(app,'Contents/Resources'));
  await writeFile(resolve(app,'Contents/Info.plist'),'<?xml version="1.0"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>CFBundleIdentifier</key><string>local.brezi.twin</string><key>CFBundleExecutable</key><string>BreziTwin</string><key>CFBundlePackageType</key><string>APPL</string><key>CFBundleVersion</key><string>1</string><key>NSHighResolutionCapable</key><true/></dict></plist>');
  await writeFile(resolve(app,'Contents/Resources/fixture.txt'),'AppKit fixture only; no Unreal assets.\n');
  const executable=resolve(mac,'BreziTwin');
  await run('xcrun',['clang++','-arch','arm64','-mmacosx-version-min=14.0','-O2','-Wall','-Wextra','-Werror','-Wno-unused-parameter',stub,...(mode==='self-exec'?[entry,'-DBREZI_STARTUP_ENTRY_FIXTURE=1','-Wl,-e,_BreziMain']:[]),'-framework','AppKit','-o',executable]);
  await run('codesign',['--force','--sign','-','--entitlements',entitlements,app]);
  const sealing=mode==='self-exec'?await sealStartupEntry({app,source:entry,output:resolve(output,mode,'signing')}):null;
  await run('codesign',['--verify','--deep','--strict',app]);
  signatures[mode]={app,sealing,plistSha256:sha(await readFile(resolve(app,'Contents/Info.plist'))),engineSha256:sha(await readFile(executable)),entitlements:(await run('codesign',['--display','--entitlements','-','--xml',app])).stdout,
    engineEntitlements:(await run('codesign',['--display','--entitlements','-','--xml',executable])).stdout,loadCommands:(await run('xcrun',['otool','-l',executable])).stdout,symbols:(await run('xcrun',['nm','-n',executable])).stdout};
  const launch=mode==='self-exec'?await resolveAppLaunch(app):null;
  return {app,executable:launch?.executable??executable,engine:executable,launch};
}
async function invoke(mode, bundle, args) {
  const stdout=[],stderr=[],startedAt=new Date().toISOString(),child=spawn(bundle.executable,args,{stdio:['ignore','pipe','pipe']});
  child.stdout.on('data',b=>stdout.push(b));child.stderr.on('data',b=>stderr.push(b));let timedOut=false;
  const timer=setTimeout(()=>{timedOut=true;child.kill('SIGKILL');},10000);
  const outcome=await new Promise(accept=>{child.once('error',e=>accept({error:e.message,code:null,signal:null}));child.once('close',(code,signal)=>accept({code,signal}));});clearTimeout(timer);
  const row={mode,args,pid:child.pid,startedAt,endedAt:new Date().toISOString(),...outcome,timedOut,stdout:Buffer.concat(stdout).toString('utf8'),stderr:Buffer.concat(stderr).toString('utf8')};
  cases.push(row);await writeFile(resolve(output,`case-${cases.length}.json`),JSON.stringify(row,null,2)+'\n');return row;
}
const original=await build('original'), self=await build('self-exec');
const baseline=await invoke('original',original,[]);
const validArgs=[[],['a space','Žlté drevo','quotes" \' ` $(literal)',''],['-LLM','-DetectHitchesWithLLM'],['-LLM'],['/llm','/DetectHitchesWithLLM']];
for(const args of validArgs) await invoke('self-exec',self,args);
for(const args of [['-NOLLM'],['/nollm'],['-NoLlm=true'],['-LLM=0'],['-DetectHitchesWithLLM=false']]) await invoke('self-exec-reject',self,args);
const errors=[];const check=(ok,message)=>{if(!ok)errors.push(message);};
check(baseline.code===0 && baseline.signal===null && baseline.stdout.includes('sharedApplication-ready'),'Original sandboxed AppKit main failed');
for(const row of cases.filter(c=>c.mode==='self-exec')) {
  check(row.code===0 && row.signal===null && !row.timedOut,'Self-exec did not exit cleanly');
  const json=row.stdout.split('\n').filter(s=>s.startsWith('{')).map(s=>JSON.parse(s)), ready=json.find(j=>j.phase==='sharedApplication-ready');
  check(ready?.nativePid===row.pid && ready?.bundleIdentifier==='local.brezi.twin','AppKit PID/bundle identity missing');
  const canonical=row.args.includes('-LLM') && row.args.includes('-DetectHitchesWithLLM');
  const expected=[self.engine,...(canonical?[]:['-LLM','-DetectHitchesWithLLM']),...row.args];
  check(JSON.stringify(ready?.arguments)===JSON.stringify(expected),'Actual NSProcessInfo arguments differ');
  const enters=[...row.stderr.matchAll(/^BreziStartupEntry: pid=(\d+) phase=enter-engine forcedFlags=-LLM,-DetectHitchesWithLLM$/gm)];
  const reexecs=[...row.stderr.matchAll(/^BreziStartupEntry: pid=(\d+) phase=self-exec forcedFlags=-LLM,-DetectHitchesWithLLM$/gm)];
  check(enters.length===1 && Number(enters[0][1])===row.pid && reexecs.length===(canonical?0:1) && reexecs.every(m=>Number(m[1])===row.pid),'Self-exec entry count/PID differs');
}
for(const row of cases.filter(c=>c.mode==='self-exec-reject')) check(row.code===64 && row.signal===null && !row.stdout.includes('before-sharedApplication'),'Contradictory policy was not rejected before AppKit');
for(const bundle of [original,self]) await run('codesign',['--verify','--deep','--strict',bundle.app]);
check(signatures.original.entitlements===signatures['self-exec'].entitlements,'Original GUI entitlement dictionary changed');
const report={status:errors.length?'failed':'native-appkit-self-exec-fixture-passed',errors,output,cases,signatures,commands,
  sourceHashes:Object.fromEntries(await Promise.all([entry,stub,fileURLToPath(import.meta.url)].map(async f=>[f,sha(await readFile(f))]))),
  unrealExecuted:false,windowsCreated:false,gpuRenderingRequested:false,scope:'Original and self-exec AppKit registration, sealed linked-entry policy and actual process arguments tested. No UE, game content, Metal rendering or Finder activation proof.'};
await writeFile(resolve(output,'receipt.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,errors,receipt:resolve(output,'receipt.json'),cases:cases.length},null,2));process.exitCode=errors.length?1:0;
