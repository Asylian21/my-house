// One emission-node edit and one material binding over immutable inherited R6.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
const sha=b=>createHash('sha256').update(b).digest('hex');
const read=async p=>JSON.parse(await readFile(p));
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
export const originalFlameMaterial='/Game/Brezi/Realism/Stove/Materials/M_Stove_Flames.M_Stove_Flames';
export const calibratedFlameMaterial='/Game/Brezi/Realism/StoveCalibration/Materials/M_Stove_Flames_512.M_Stove_Flames_512';
export function validateStoveCalibrationReceipt({report,source,project}) {
  assert.equal(report.schemaVersion,1);assert.equal(report.owner,'scripts/unreal/realism-stove-calibration-import.py');
  assert.equal(report.status,'realism-stove-calibration-validated');assert.equal(report.project,project);assert.equal(report.sourceOutput,source.donor);
  for(const field of ['savedReloaded','protectedContentUnchanged','sourceGeometryCollisionAndTransformsPreserved',
    'originalMaterialsPreserved','originalLightingExposureAndGlassPreserved'])assert.equal(report[field],true);
  assert.equal(report.emissionBefore,3);assert.equal(report.emissionAfter,512);
  assert.equal(report.bindingChanges.length,1);assert.deepEqual(report.bindingChanges,report.material.bindingChanges);
  const change=report.bindingChanges[0],m=report.material,saved=report.savedMaterialReadback;
  assert.equal(change.before,originalFlameMaterial);assert.equal(change.after,calibratedFlameMaterial);assert.equal(change.slot,0);
  assert.equal(change.actor,m.sourceTarget.actor);assert.equal(change.component,m.sourceTarget.component);
  assert.deepEqual(m.sourceTarget.materials,[originalFlameMaterial]);
  assert.deepEqual(m.ownedAssets,[calibratedFlameMaterial]);assert.deepEqual(Object.keys(m.materials),[calibratedFlameMaterial]);
  assert.deepEqual(m.originalGraphs,m.protectedGraphs);
  const graph=structuredClone(m.originalGraphs[originalFlameMaterial]);
  assert(graph,'Missing original flame graph');
  const nodes=graph.nodes.filter(n=>n.class==='MaterialExpressionCustom'&&n.role==='BreziRealismStove:density-weighted-fire-emission');
  assert.equal(nodes.length,1);const suffix='return tint*Density*3.0;';assert(nodes[0].values.code.endsWith(suffix));
  nodes[0].values.code=nodes[0].values.code.slice(0,-suffix.length)+'return tint*Density*512.0;';
  assert.equal(m.materials[calibratedFlameMaterial].sourceAsset,originalFlameMaterial);
  assert.deepEqual(m.materials[calibratedFlameMaterial].graph,graph,'Calibration modified more than the single emission scalar');
  const recipe=m.materials[calibratedFlameMaterial].recipe;
  assert.equal(recipe.before,3);assert.equal(recipe.after,512);assert.equal(recipe.exposureCompensation,false);assert.equal(recipe.otherGraphChanges,false);
  assert.deepEqual(m.sourceMaterialGraph,m.originalGraphs[originalFlameMaterial]);
  for(const role of ['flames','glass']) {
    const diagnostics=m.diagnosticsBefore[role];
    for(const field of ['blendMode','shadingModel','translucencyPass','refractionMethod','translucencyLightingMode'])assert.equal(typeof diagnostics[field],'string');
    for(const field of ['refractionInputConnected','disableDepthTest'])assert.equal(typeof diagnostics[field],'boolean');
    assert(Number.isInteger(diagnostics.sortPriority)&&Number.isFinite(diagnostics.sortDistanceOffset));
  }
  assert.deepEqual(m.diagnosticsBefore,m.diagnosticsAfter,'Calibration changed pass/refraction/sort state');
  assert.equal(saved.status,'saved-reloaded-validated');assert.equal(saved.savedReloaded,true);
  for(const field of ['materials','originalGraphs','protectedGraphs','sourceTarget','bindingChanges'])assert.deepEqual(saved[field],m[field]);
  assert.deepEqual(saved.diagnosticsReloaded,m.diagnosticsAfter,'Saved pass/refraction/sort state differs');
  assert(Number.isInteger(report.originalActorCount)&&report.originalActorCount>0);assert.equal(report.finalActorCount,report.originalActorCount);
  assert(hash(report.protectedActorWitnessSha256)&&hash(report.authoredActorWitnessSha256));
  assert.equal(report.savedProtectedActorWitnessSha256,report.protectedActorWitnessSha256);
  assert.equal(report.savedActorWitnessSha256,report.authoredActorWitnessSha256);
  assert.deepEqual(report.beforeAssetHashes,source.content);
  const map=resolve(project,'Content/Brezi/Maps/Brezi.umap'),clone=resolve(project,'Content/Brezi/Realism/StoveCalibration/Materials/M_Stove_Flames_512.uasset');
  assert.deepEqual(Object.keys(report.afterAssetHashes).sort(),[...Object.keys(source.content),clone].sort());
  for(const [path,value] of Object.entries(source.content))if(path!==map)assert.equal(report.afterAssetHashes[path],value,'Original asset changed');
  assert(hash(report.afterAssetHashes[clone])&&hash(report.afterAssetHashes[map]));assert.notEqual(report.afterAssetHashes[map],source.content[map]);
  assert.deepEqual(report.newAssets,[clone]);
  assert.deepEqual(report.changedAssets,[{path:map,beforeSha256:source.content[map],afterSha256:report.afterAssetHashes[map]}]);
  return report.afterAssetHashes;
}

export async function verifyStoveCalibrationScene({root,output,project,source}) {
  const reportFile=resolve(output,'realism-stove-calibration-report.json'),report=await read(reportFile);
  const hostFile=resolve(output,'realism-stove-calibration-process.json'),host=await read(hostFile);
  const processFile=resolve(output,'realism-stove-calibration.log.json'),logFile=resolve(output,'realism-stove-calibration.log');
  assert.equal(host.processFile,processFile);assert.equal(host.logFile,logFile);
  const process=await read(processFile),profile=await read(resolve(output,'profile.json'));
  assert.equal(process.code,0);assert.equal(process.signal,null);assert.equal(process.pid,report.nativeProcessId);
  assert.equal(process.command,resolve(profile.engine,'Engine/Binaries/Mac/UnrealEditor-Cmd'));
  assert(process.args.includes(resolve(project,'BreziTwin.uproject'))&&process.args.includes('-run=pythonscript')
    &&process.args.includes('-script='+resolve(root,'scripts/unreal/realism-stove-calibration-import.py')),'Unrelated calibration native process');
  const start=Date.parse(report.startedAt),end=Date.parse(report.generatedAt);
  assert(start>=Date.parse(process.startedAt)&&end>=start&&end<=Date.parse(process.endedAt));
  for(const name of ['realism-stove-calibration-import.py','realism-stove-calibration-material.py','realism-room-details-import.py',
    'realism-fixtures-import.py','performance-optimize.py','performance_scene_policy.py'])assert(hash(report.pipelineFiles[resolve(root,'scripts/unreal',name)]));
  for(const [path,value] of Object.entries(source.geometry))assert.equal(report.inputFiles[path],value,'Unpinned inherited geometry');
  const donorPackage=await read(resolve(source.donor,'model-package.json')),donorReport=resolve(source.donor,'realism-stove-report.json');
  assert.equal(report.inputFiles[donorReport],donorPackage.inputs[donorReport]);
  assert.equal(report.inputFiles[donorReport],donorPackage.stove.reportSha256);
  assert.deepEqual(report.material.sourceTarget,(await read(donorReport)).objects.RFIRE_FLAMES);
  const inputs={[reportFile]:host.reportSha256,[hostFile]:sha(await readFile(hostFile)),[processFile]:host.processFileSha256,
    [logFile]:host.logSha256,...report.pipelineFiles,...report.inputFiles};
  for(const [path,value] of Object.entries(inputs))assert(hash(value)&&sha(await readFile(path))===value,'Calibration input changed: '+path);
  return {content:validateStoveCalibrationReceipt({report,source,project}),inputs,
    stoveCalibration:{status:report.status,report:reportFile,reportSha256:host.reportSha256,emissionBefore:3,emissionAfter:512,
      bindingCount:1,materialCount:1,nativeRenderedVerified:false}};
}
