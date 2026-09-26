// Narrow experimental receipt verifier. Production map-only migration remains separate.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=async file=>JSON.parse(await readFile(file));
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const sortedKeys=value=>Object.keys(value).sort();
const prefix='/Game/Brezi/Geometry/brezi-twin/StaticMeshes/';

export function validateDerivedBounds(before,after){
  assert(Array.isArray(before)&&Array.isArray(after)&&before.length===2&&after.length===2);
  assert([...before,...after].every(row=>Array.isArray(row)&&row.length===3),'Invalid derived bounds');
  let maximum=0;
  for(let row=0;row<2;row++)for(let axis=0;axis<3;axis++){
    const old=before[row][axis],value=after[row][axis];assert(Number.isFinite(old)&&Number.isFinite(value));
    const magnitude=Math.max(Math.abs(old),Math.abs(value));
    const ulp=magnitude?Math.max(2**-149,2**(Math.floor(Math.log2(magnitude))-23)):2**-149;
    const error=Math.abs(old-value);assert(error<=Math.min(ulp,.0002),'Derived bounds exceed one float32 ULP / 0.0002 cm');
    maximum=Math.max(maximum,error);
  }
  return maximum;
}

export function validateNaniteStudy({study,source,project,scene,doors}) {
  assert.equal(study.schemaVersion,1);
  assert.equal(study.status,'nanite-study-validated-unaccepted');
  assert.equal(study.owner,'scripts/unreal/nanite-study.py');
  assert.equal(study.experimental,true);assert.equal(study.accepted,false);
  assert.equal(study.renderedVerified,false);assert.equal(study.performanceAccepted,false);
  assert.equal(study.project,project);assert.equal(study.sourceOutput,source.donor);
  assert.equal(study.cohortLimit,128);
  for(const field of ['savedReloaded','protectedContentUnchanged','mapUnchanged','sourceGeometryMaterialsAndCollisionPreserved'])
    assert.equal(study[field],true,'Missing study invariant: '+field);
  assert.deepEqual(study.beforeAssetHashes,source.content);
  assert.deepEqual(sortedKeys(study.afterAssetHashes),sortedKeys(source.content),'Study Content inventory differs');
  assert(Object.values(study.afterAssetHashes).every(hash),'Invalid saved asset hash');
  assert(hash(study.actorWitnessSha256));assert.equal(study.savedActorWitnessSha256,study.actorWitnessSha256);
  assert(Number.isInteger(study.actorCount)&&study.actorCount>0);
  assert(Array.isArray(study.selected)&&study.selected.length>0&&study.selected.length<=128,'Invalid bounded study cohort');
  assert(Number.isInteger(study.attemptedCohortCount)&&study.attemptedCohortCount>=study.selected.length&&study.attemptedCohortCount<=128,
    'Transient preflight exceeded bounded cohort');
  assert.equal(study.savedMeshReadback.length,study.selected.length,'Missing saved mesh readback');
  const records=new Map(scene.objects.map(row=>[row.id,row]));
  const doorIds=new Set(doors.doors.flatMap(door=>door.members.map(member=>member.sourceObjectId)));
  const files=new Set(),ids=new Set();
  for(const [i,row] of study.selected.entries()) {
    assert(/^DOM_\d{5}$/.test(row.sourceId)&&!ids.has(row.sourceId),'Invalid or duplicate study source identity');ids.add(row.sourceId);
    const record=records.get(row.sourceId),metadata=record?.metadata??{};
    assert(record&&record.group==='Interior'&&record.enabled===true&&record.instances===1,'Study source is not interior decoration');
    assert(Number.isInteger(row.triangles)&&row.triangles>0&&row.triangles<512&&row.triangles===record.triangles,'Invalid small-mesh triangle count');
    assert(!doorIds.has(row.sourceId)&&!['doorMotion','dynamicCameraOccluder','walkSurface','cameraOccluder','babylonCheckCollisions'].some(key=>metadata[key]),'Study selected door or collision-bearing source');
    assert(!/dve[rř]|dvier|z[áa]rub|door|k[ľl]uč|klika|\bd\d+\.\d+\.|fireplace|flame/i.test([record.name,record.sourceId].join(' ')),
      'Study selected a fixed door part or stove/flame effect');
    assert(record.materialSlots.length&&record.materialSlots.every(slot=>scene.materials[slot].alpha>=.999),'Study selected translucent source');
    const relative='Brezi/Geometry/brezi-twin/StaticMeshes/'+row.sourceId+'.uasset';
    assert.equal(row.file,relative,'Study whitelist must contain exact source mesh assets');
    assert.equal(row.asset,prefix+row.sourceId+'.'+row.sourceId);
    assert.equal(row.naniteEnabledInitially,false,'Study asset was already Nanite');
    assert.equal(row.componentDisallowNanite,false,'Selected component disallows Nanite');
    assert(hash(row.witnessSha256),'Missing source mesh witness');
    const file=resolve(project,'Content',relative);assert(hash(source.content[file]),'Study selected absent source mesh');files.add(file);
    const saved=study.savedMeshReadback[i];
    assert.equal(saved.sourceId,row.sourceId);assert.equal(saved.naniteEnabled,true);
    assert.equal(saved.beforeWitnessSha256,row.witnessSha256,'Saved witness is not bound to the original source');
    assert.equal(saved.afterWitnessSha256,saved.beforeWitnessSha256,'Protected mesh witness changed');
    assert.deepEqual(saved.derivedBoundsBeforeCm,row.derivedBoundsBeforeCm);
    assert.equal(saved.derivedBoundsMaxErrorCm,validateDerivedBounds(saved.derivedBoundsBeforeCm,saved.derivedBoundsAfterCm));
  }
  const changed=Object.keys(source.content).filter(file=>study.afterAssetHashes[file]!==source.content[file]);
  assert.deepEqual(changed.sort(),[...files].sort(),'Study may alter only every selected source mesh; map/materials/other assets remain protected');
  return study.afterAssetHashes;
}

export async function verifyNaniteStudy({root,output,project,source}) {
  const reportFile=resolve(output,'nanite-study-report.json'),study=await read(reportFile);
  const hostFile=resolve(output,'nanite-study-process.json'),host=await read(hostFile);
  const donor=await read(resolve(source.donor,'model-package.json')),profile=await read(resolve(output,'profile.json'));
  const sceneFile=resolve(output,'geometry/scene.json'),doorsFile=resolve(output,'geometry/doors.json');
  assert.deepEqual(sortedKeys(study.inputFiles),[doorsFile,sceneFile].sort());
  const pipeline=['nanite-study.py','nanite_study_policy.py','performance-optimize.py','performance_scene_policy.py']
    .map(name=>resolve(root,'scripts/unreal',name));
  assert.deepEqual(sortedKeys(study.pipelineFiles),pipeline.sort());
  const expectedFiles={
    [reportFile]:host.reportSha256,
    [resolve(output,'nanite-study-state.json')]:study.stateFileSha256,
    ...study.inputFiles,...study.pipelineFiles,
  };
  let previousEnd=0;
  assert(Number.isInteger(study.mutationProcessId)&&study.mutationProcessId>0);
  assert(Number.isInteger(study.nativeProcessId)&&study.nativeProcessId>0&&study.nativeProcessId!==study.mutationProcessId,
    'Saved reload must be verified by a different native process');
  for(const stage of ['apply','verify']) {
    const processFile=resolve(output,'nanite-study-'+stage+'.log.json'),logFile=resolve(output,'nanite-study-'+stage+'.log');
    assert.equal(host[stage].processFile,processFile);assert.equal(host[stage].logFile,logFile);
    expectedFiles[processFile]=host[stage].processFileSha256;expectedFiles[logFile]=host[stage].logSha256;
    const process=await read(processFile);
    assert.equal(process.code,0);assert.equal(process.signal,null);
    assert.equal(process.command,resolve(donor.engine,'Engine/Binaries/Mac/UnrealEditor-Cmd'));
    assert(process.args.includes(resolve(project,'BreziTwin.uproject'))&&process.args.includes('-run=pythonscript')
      &&process.args.includes('-script='+resolve(root,'scripts/unreal/nanite-study.py')),'Unrelated native study process');
    assert.equal(process.pid,stage==='apply'?study.mutationProcessId:study.nativeProcessId);
    const time=Date.parse(stage==='apply'?study.appliedAt:study.generatedAt);
    assert(time>=Date.parse(process.startedAt)&&time<=Date.parse(process.endedAt),'Study evidence outside native process lifetime');
    assert(Date.parse(process.startedAt)>=previousEnd,'Study verification must start after the mutation process exits');
    previousEnd=Date.parse(process.endedAt);
  }
  for(const [file,digest] of Object.entries(expectedFiles)) {
    assert(hash(digest),'Missing study input hash: '+file);
    assert.equal(sha(await readFile(file)),digest,'Study input changed: '+file);
  }
  assert.equal(study.donorPackageSha256,source.receiptPins[resolve(source.donor,'model-package.json')]);
  assert.equal(donor.gameConfiguration,'Shipping');assert.equal(profile.gameConfiguration,'Shipping');assert(!donor.experimentalStudy);
  const gameFile=resolve(output,'model-game-build.json'),game=await read(gameFile);
  assert.equal(game.status,'model-game-build-reused-validated','Study must reuse the exact donor native binary');
  assert.equal(game.gameConfiguration,'Shipping');assert.equal(game.reuse.origin,source.donor);
  assert.equal(game.reuse.sourceAuthoringIdentical,true);assert.equal(game.reuse.linkedUUID,donor.linkedUUID);
  assert.equal(game.reuse.originalPackageReportSha256,study.donorPackageSha256);
  const donorGame=await read(resolve(source.donor,'model-game-build.json'));
  assert.equal(game.rawExecutableSha256,donorGame.rawExecutableSha256,'Native binary hash differs from study donor');
  for(const executable of [game.rawExecutable,donorGame.rawExecutable])
    assert.equal(sha(await readFile(executable)),game.rawExecutableSha256,'Native binary changed');
  const state=await read(resolve(output,'nanite-study-state.json'));
  assert.equal(state.selected.length,study.selected.length);
  for(const [i,row] of state.selected.entries()) {
    assert.equal(row.sourceId,study.selected[i].sourceId);assert.equal(row.witnessSha256,study.selected[i].witnessSha256);
    assert.equal(row.naniteEnabledInitially,false);
    assert.deepEqual(row.derivedBoundsBeforeCm,study.selected[i].derivedBoundsBeforeCm);
  }
  const scene=await read(sceneFile),doors=await read(doorsFile);
  assert.equal(doors.sourceManifestSha256,study.inputFiles[sceneFile]);
  const content=validateNaniteStudy({study,source,project,scene,doors});
  return {content,inputs:{...expectedFiles,[hostFile]:sha(await readFile(hostFile)),[gameFile]:sha(await readFile(gameFile))},
    experimentalStudy:{kind:'small-opaque-nanite',accepted:false,report:reportFile,reportSha256:host.reportSha256,
      donor:source.donor,cohort:study.selected.map(row=>row.sourceId)}};
}
