/** Seal an app-owned LC_MAIN startup policy after UAT and before final package hashes.
 * This draft deliberately supports the project's current local ad-hoc identity.
 */
import { execFile } from "node:child_process";
import { readFile, writeFile, mkdir, readdir, lstat } from "node:fs/promises";
import { createHash } from "node:crypto";
import { resolve, relative, dirname, isAbsolute } from "node:path";
import { promisify } from "node:util";
import { compareSignatureOnly } from "./macho-signature.mjs";
import { startupFlags, resolveAppLaunch } from "./app-launch.mjs";
import { inspectStartupEntry } from "./startup-entry.mjs";
const exec = promisify(execFile), sha = bytes => createHash("sha256").update(bytes).digest("hex");
async function inventory(app) {
  const result = {};
  async function walk(directory) {
    for (const name of await readdir(directory)) {
      const path = resolve(directory, name), stat = await lstat(path);
      if (stat.isSymbolicLink()) throw new Error("App payload contains a symlink");
      if (stat.isDirectory()) await walk(path); else if (stat.isFile()) result[relative(app, path)] = sha(await readFile(path));
      else throw new Error("Non-regular app payload");
    }
  }
  await walk(app); return result;
}
export async function prepareSealResources(app,beforeFiles,resources) {
  const prepared=[],seen=new Set();
  for(const entry of resources) {
    const path=entry.relativePath;
    if(typeof path!=='string' || isAbsolute(path) || relative(app,resolve(app,path))!==path
      || !/^Contents\/(?:Resources\/|UE\/.+\/Resources\/).+\.json$/.test(path)
      || path==='Contents/Resources/BreziStartupPolicy.json' || seen.has(path) || path in beforeFiles
      || !/^[a-f0-9]{64}$/.test(entry.sha256))throw Error('Invalid, duplicate, or existing additional seal resource');
    const bytes=await readFile(entry.source);
    if(sha(bytes)!==entry.sha256)throw Error('Additional seal resource changed: '+entry.source);
    JSON.parse(bytes.toString('utf8'));
    seen.add(path);prepared.push({...entry,bytes});
  }
  return prepared;
}
export async function sealStartupEntry({app,source,output,additionalResources=[]}) {
  await mkdir(output,{recursive:true});
  const commands=[];
  const run=async(command,args)=>{const result=await exec(command,args,{maxBuffer:8*1024*1024});commands.push({command,args,stdout:result.stdout,stderr:result.stderr});return result;};
  await run('codesign',['--verify','--deep','--strict',app]);
  const signingBefore=(await run('codesign',['--display','--verbose=4',app])).stderr;
  if(!/^Signature=adhoc$/m.test(signingBefore) || !/^Identifier=local\.brezi\.twin$/m.test(signingBefore))throw Error('Only reviewed local ad-hoc app identity is supported');
  const plist=resolve(app,'Contents/Info.plist'),game=resolve(app,'Contents/MacOS/BreziTwin'),policyFile=resolve(app,'Contents/Resources/BreziStartupPolicy.json');
  const entryName=(await run('/usr/libexec/PlistBuddy',['-c','Print :CFBundleExecutable',plist])).stdout.trim();
  if(entryName!=='BreziTwin')throw Error('Rebuild a fresh original GUI app; do not migrate a mutated helper bundle');
  const beforeFiles=await inventory(app);
  if(beforeFiles['Contents/MacOS/BreziStartupLauncher'] || beforeFiles['Contents/Resources/BreziStartupPolicy.json'])throw Error('Fresh archive required; obsolete helper or previous policy must not survive staging');
  const resources=await prepareSealResources(app,beforeFiles,additionalResources);
  const before=await readFile(game),linkedEntry=inspectStartupEntry(before),sourceBytes=await readFile(source);
  const entitlementsFile=resolve(output,'original-entitlements.plist'),originalText=(await run('codesign',['--display','--entitlements','-','--xml',app])).stdout;
  await writeFile(entitlementsFile,originalText);
  const originalEntitlements=JSON.parse((await run('plutil',['-convert','json','-o','-',entitlementsFile])).stdout);
  if(originalEntitlements['com.apple.security.app-sandbox']!==true || originalEntitlements['com.apple.security.inherit']!==undefined)
    throw Error('Expected original full GUI app sandbox, without helper inheritance');
  const policy={schemaVersion:2,status:'linked-self-exec-startup-policy',entryKind:'same-binary-self-exec',entryFile:'Contents/MacOS/BreziTwin',
    forcedFlags:[...startupFlags],entrySourceSha256:sha(sourceBytes),linkedEntry,sandboxPolicy:'original-main-executable-original-entitlements',
    scope:'App-owned LC_MAIN entry compiled into the original GUI executable. The policy intentionally has no full final executable hash; that hash belongs to the external signed-bundle receipt.'};
  await mkdir(dirname(policyFile),{recursive:true});await writeFile(policyFile,JSON.stringify(policy,null,2)+'\n');
  for(const entry of resources) {
    const path=resolve(app,entry.relativePath);
    await mkdir(dirname(path),{recursive:true});await writeFile(path,entry.bytes,{flag:'wx'});
  }
  // Original app identity and entitlements, one final outer signing pass. No nested
  // executable, Info.plist rewrite, copied code, private API or extra Mach rights.
  await run('codesign',['--force','--sign','-','--preserve-metadata=identifier,requirements,flags,runtime','--entitlements',entitlementsFile,app]);
  await run('codesign',['--verify','--deep','--strict',app]);
  const after=await readFile(game),proof=compareSignatureOnly(before,after),finalEntry=inspectStartupEntry(after);
  if(JSON.stringify(finalEntry)!==JSON.stringify(linkedEntry))throw Error('Signing changed linked entry or executable code');
  const finalText=(await run('codesign',['--display','--entitlements','-','--xml',app])).stdout;
  const finalEntitlementsFile=resolve(output,'final-entitlements.plist');await writeFile(finalEntitlementsFile,finalText);
  const finalEntitlements=JSON.parse((await run('plutil',['-convert','json','-o','-',finalEntitlementsFile])).stdout);
  const sort=v=>Array.isArray(v)?v.map(sort):v&&typeof v==='object'?Object.fromEntries(Object.entries(v).sort(([a],[b])=>a.localeCompare(b)).map(([k,item])=>[k,sort(item)])):v;
  if(JSON.stringify(sort(finalEntitlements))!==JSON.stringify(sort(originalEntitlements)))throw Error('Original GUI entitlements changed');
  const afterFiles=await inventory(app),allowedChanged=new Set(['Contents/MacOS/BreziTwin','Contents/_CodeSignature/CodeResources']);
  for(const [file,digest] of Object.entries(beforeFiles))if(!(file in afterFiles)||(!allowedChanged.has(file)&&afterFiles[file]!==digest))throw Error(`Unrelated payload changed: ${file}`);
  const allowedAdded=new Set(['Contents/Resources/BreziStartupPolicy.json',...resources.map(entry=>entry.relativePath)]);
  for(const file of Object.keys(afterFiles))if(!(file in beforeFiles)&&!allowedAdded.has(file))throw Error(`Unexpected new payload: ${file}`);
  for(const entry of resources)if(afterFiles[entry.relativePath]!==entry.sha256 || sha(await readFile(entry.source))!==entry.sha256)throw Error('Additional resource changed while sealing');
  if(sha(await readFile(source))!==sha(sourceBytes))throw Error('Entry source changed while sealing');
  await writeFile(resolve(output,'engine-before-header.bin'),before.subarray(0,proof.beforeStructure.commandsEnd));
  await writeFile(resolve(output,'engine-before-signature.bin'),before.subarray(proof.beforeStructure.signature.offset));
  const launch=await resolveAppLaunch(app);
  const report={status:'self-exec-entry-sealed-and-signed',generatedAt:new Date().toISOString(),app,commands,linkedEntry,proof,launch,
    additionalResources:resources.map(({bytes,...entry})=>entry),
    entrySourceSha256:sha(sourceBytes),beforeFiles,afterFiles,originalEntitlements,finalEntitlements,entitlementSemanticDiff:[],
    codeSignature:'deep-strict-valid',actualGameLaunchPending:true,
    scope:'The app binary intentionally gains a compiled entry point during build. This receipt separately proves final sealing changed only signature bytes/validated signing-size fields and the declared added JSON resources, not the already linked code or original Info.plist.'};
  await writeFile(resolve(output,'startup-entry-package.json'),JSON.stringify(report,null,2)+'\n');return report;
}
