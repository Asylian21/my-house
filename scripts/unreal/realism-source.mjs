// Verify the additive native realism receipt without weakening inherited asset pins.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve, relative} from 'node:path';

const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=async path=>JSON.parse(await readFile(path));
const isHash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const keys=value=>Object.keys(value).sort();

export function authoredRenderCapability(policyBytes,sourcePolicyPath,sourcePins) {
  const bytes=Buffer.from(policyBytes),sourcePolicySha256=sha(bytes);
  assert.equal(sourcePins[sourcePolicyPath],sourcePolicySha256,'Render policy is not part of the compiled source pins');
  const revision=Number(bytes.toString().match(/RecipeRevision\s*=\s*(\d+)\s*;/)?.[1]);
  assert(Number.isInteger(revision)&&revision>=2,'Unrecognized native render recipe');
  const cinematic=revision>=3&&/enum class Profile[^;]*\bCinematic\b/.test(bytes.toString());
  const full=revision>=5&&/enum class Profile[^;]*\bRealtimeFull\b/.test(bytes.toString());
  return {schemaVersion:1,recipeRevision:revision,profiles:['native','balanced','performance',...(cinematic?['cinematic']:[]),...(full?['full']:[])],
    sourcePolicyPath,sourcePolicySha256};
}

export function modelRenderProfileArgs(value,capability,inputs) {
  if(value===undefined)return [];
  const name={tsr67:'balanced',tsr50:'performance'}[value]??value;
  assert(['native','balanced','performance','cinematic','full'].includes(name),'Unknown BREZI_RENDER_PROFILE');
  assert(capability?.schemaVersion===1&&capability.profiles.includes(name),'Package does not advertise this native render profile');
  assert(isHash(capability.sourcePolicySha256)&&inputs[capability.sourcePolicyPath]===capability.sourcePolicySha256,
    'Render profile capability is not bound to package source provenance');
  if(name==='cinematic')assert(capability.recipeRevision>=3,'Cinematic profile requires render recipe 3');
  if(name==='full')assert(capability.recipeRevision>=5,'Full profile requires render recipe 5');
  return ['-BreziRenderProfile='+name];
}

export function validateRealismReceipt({report,source,project}) {
  assert.equal(report.schemaVersion,1);
  assert.equal(report.owner,'scripts/unreal/realism-import.py');
  assert.equal(report.status,'realism-import-validated');
  assert.equal(report.project,project);assert.equal(report.sourceOutput,source.donor);
  for(const field of ['savedReloaded','protectedContentUnchanged','sourceTransformsMeshCollisionAndInstancesPreserved'])
    assert.equal(report[field],true,'Missing realism invariant: '+field);
  assert.deepEqual(report.beforeAssetHashes,source.content);
  const content=resolve(project,'Content'),map=resolve(content,'Brezi/Maps/Brezi.umap');
  const after=report.afterAssetHashes;
  assert(after&&Object.values(after).every(isHash),'Invalid realism content hashes');
  const newFiles=keys(after).filter(path=>!Object.hasOwn(source.content,path));
  for(const [path,value] of Object.entries(source.content)) {
    assert(Object.hasOwn(after,path),'Realism removed original Content');
    if(path!==map)assert.equal(after[path],value,'Realism altered a protected source asset: '+path);
  }
  for(const path of newFiles) {
    assert(path.startsWith(resolve(content,'Brezi/Realism')+'/'),'Realism new asset escaped its namespace');
    assert(/\.(uasset|uexp|ubulk)$/.test(path),'Unexpected realism Content file');
    assert.equal(resolve(path),path,'Noncanonical realism asset path');
  }
  assert.deepEqual([...report.newAssets].sort(),newFiles,'Incomplete realism new-asset manifest');
  assert(newFiles.length>0,'No authored realism assets');
  const changed=keys(source.content).filter(path=>source.content[path]!==after[path]);
  assert.deepEqual([...report.changedAssets].map(row=>row.path).sort(),changed,'Incomplete realism change manifest');
  for(const row of report.changedAssets) {
    assert.equal(row.path,map);assert.equal(row.beforeSha256,source.content[row.path]);assert.equal(row.afterSha256,after[row.path]);
  }
  assert(changed.includes(map),'Realism map was not saved');
  assert(isHash(report.protectedActorWitnessSha256));
  assert.equal(report.savedProtectedActorWitnessSha256,report.protectedActorWitnessSha256);
  assert(isHash(report.authoredActorWitnessSha256));assert.equal(report.savedActorWitnessSha256,report.authoredActorWitnessSha256);
  assert(Number.isInteger(report.originalActorCount)&&report.originalActorCount>0);
  assert.equal(new Set(report.addedActors).size,report.addedActors.length);
  assert.equal(report.finalActorCount,report.originalActorCount+report.addedActors.length);
  assert(Array.isArray(report.materialBindingChanges)&&report.materialBindingChanges.length>0);
  const bindingIds=new Set();
  for(const row of report.materialBindingChanges) {
    assert(typeof row.actor==='string'&&typeof row.component==='string'&&Number.isInteger(row.slot)&&row.slot>=0);
    assert(typeof row.after==='string'&&row.after.startsWith('/Game/Brezi/Realism/'));
    const key=JSON.stringify([row.actor,row.component,row.slot]);assert(!bindingIds.has(key),'Duplicate material delta');bindingIds.add(key);
  }
  assert.deepEqual(report.materialBindingChanges,report.materials.bindingChanges);
  assert(report.savedMaterialReadback&&report.savedEnvironmentReadback,'Missing saved native module readback');
  assert(Array.isArray(report.ownedAssets)&&new Set(report.ownedAssets).size===report.ownedAssets.length);
  const packages=report.ownedAssets.map(path=>{
    assert(path.startsWith('/Game/Brezi/Realism/')&&!path.includes('..'));
    return resolve(content,path.split('.')[0].slice('/Game/'.length)+'.uasset');
  }).sort();
  assert.deepEqual(packages,newFiles.filter(path=>path.endsWith('.uasset')),'Owned package manifest differs');
  return after;
}

export async function verifyRealismScene({root,output,project,source}) {
  const reportFile=resolve(output,'realism-import-report.json'),report=await read(reportFile);
  const hostFile=resolve(output,'realism-import-process.json'),host=await read(hostFile);
  const processFile=resolve(output,'realism-import.log.json'),logFile=resolve(output,'realism-import.log');
  assert.equal(host.processFile,processFile);assert.equal(host.logFile,logFile);
  const process=await read(processFile),profile=await read(resolve(output,'profile.json'));
  assert.equal(process.code,0);assert.equal(process.signal,null);assert.equal(process.pid,report.nativeProcessId);
  assert.equal(process.command,resolve(profile.engine,'Engine/Binaries/Mac/UnrealEditor-Cmd'));
  assert(process.args.includes(resolve(project,'BreziTwin.uproject'))&&process.args.includes('-run=pythonscript')
    &&process.args.includes('-script='+resolve(root,'scripts/unreal/realism-import.py')),'Unrelated realism native process');
  const start=Date.parse(report.startedAt),end=Date.parse(report.generatedAt);
  assert(start>=Date.parse(process.startedAt)&&end>=start&&end<=Date.parse(process.endedAt),'Realism evidence outside native process lifetime');
  for(const name of ['realism-import.py','realism-environment.py','realism-materials.py','performance-optimize.py','performance_scene_policy.py'])
    assert(isHash(report.pipelineFiles[resolve(root,'scripts/unreal',name)]),'Missing pipeline pin: '+name);
  for(const [path,value] of Object.entries(source.geometry))assert.equal(report.inputFiles[path],value,'Unpinned inherited geometry');
  const inputs={[reportFile]:host.reportSha256,[hostFile]:sha(await readFile(hostFile)),
    [processFile]:host.processFileSha256,[logFile]:host.logSha256,...report.pipelineFiles,...report.inputFiles};
  for(const [path,value] of Object.entries(inputs)) {
    assert(isHash(value),'Invalid realism input hash: '+path);
    assert.equal(sha(await readFile(path)),value,'Realism input changed: '+relative(root,path));
  }
  const content=validateRealismReceipt({report,source,project});
  return {content,inputs,realism:{status:report.status,report:reportFile,reportSha256:host.reportSha256,
    materialBindingCount:report.materialBindingChanges.length,addedActorCount:report.addedActors.length,nativeRenderedVerified:false}};
}
