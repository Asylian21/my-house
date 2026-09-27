// Separate receipt for a visual-only stove overlay on immutable inherited assets.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=async path=>JSON.parse(await readFile(path));
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const keys=value=>Object.keys(value).sort();
export const stoveSourceIds=[553,556,562,563,564,565,566].map(i=>'DOM_'+String(i).padStart(5,'0'));
const roleSources={shell:['DOM_00553'],chamber:['DOM_00553'],logs:['DOM_00562','DOM_00563'],flames:['DOM_00564','DOM_00565','DOM_00566'],embers:['DOM_00556']};
const stoveMeshIds=Object.keys(roleSources).map(role=>'RFIRE_'+role.toUpperCase()).sort();
const textureHashes={T_Fire_SubUV:'865a10d77419a7a5c80a89abbf2a738168cd79bfad1aab1397d3d5802ac6f33c',T_Fire_Tiled_D:'5fddf6ab9c5a32516248bdfce3cc9f2426a3b734d57f2c5bd1d26a93c6381252'};
const renderFlags=['affect_distance_field_lighting','affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden',
  'cast_hidden_shadow','cast_shadow','visible_in_ray_tracing'];

export function validateStoveReceipt({report,source,project,manifest}) {
  assert.equal(report.schemaVersion,1);assert.equal(report.owner,'scripts/unreal/realism-stove-import.py');
  assert.equal(report.status,'realism-stove-validated');assert.equal(report.project,project);assert.equal(report.sourceOutput,source.donor);
  for(const field of ['savedReloaded','protectedContentUnchanged','sourceGeometryCollisionAndTransformsPreserved','originalMaterialAssetsPreserved','materialBindingsAudited','originalLightingPreserved'])assert.equal(report[field],true);
  assert.equal(manifest.owner,'scripts/unreal/realism-stove-geometry.py');assert.equal(manifest.status,'offline-study-geometry-validated');
  assert.deepEqual(report.sourceIds,stoveSourceIds);assert.deepEqual([...manifest.sourceIds].sort(),stoveSourceIds);
  assert.deepEqual(report.hiddenSourceIds,stoveSourceIds);assert.deepEqual([...manifest.hiddenSourceIds].sort(),stoveSourceIds);
  assert.equal(report.experimentalRuntimePluginsEnabled,false);
  assert.deepEqual(manifest.objects.map(row=>row.id).sort(),stoveMeshIds);
  assert.deepEqual(keys(report.objects),stoveMeshIds);assert.equal(report.savedGeometryReadback.length,5);
  const expectedById=new Map(manifest.objects.map(row=>[row.id,row]));
  assert.deepEqual([...new Set(manifest.objects.flatMap(row=>row.sourceIds))].sort(),stoveSourceIds);
  let maximum=0;
  const checked=new Set();
  for(const row of report.savedGeometryReadback) {
    assert(!checked.has(row.id),'Duplicate stove readback');checked.add(row.id);
    const expected=expectedById.get(row.id);assert(expected,'Unknown stove readback');
    assert.deepEqual(row.expectedBoundsCm,expected.expectedWorldBoundsCm);
    assert.deepEqual(report.objects[row.id].sourceIds,expected.sourceIds);
    assert.equal(row.actor,report.objects[row.id].actor);assert.equal(row.collision,'NoCollision');
    assert(report.addedActors.includes(row.actor),'Stove readback actor not newly owned');
    assert.deepEqual(row.materials,report.objects[row.id].materials);
    assert.equal(row.materials.length,1);
    assert.equal(expected.id,'RFIRE_'+expected.materialRole.toUpperCase());
    assert.deepEqual(expected.sourceIds,roleSources[expected.materialRole]);
    assert.equal(report.objects[row.id].materialRole,expected.materialRole);
    assert.deepEqual(row.materials,[report.materials.materials[expected.materialRole]]);
    assert(report.objects[row.id].mesh.startsWith('/Game/Brezi/Realism/Stove/Geometry/'),'Stove mesh outside owned namespace');
    const converted={min:[expected.visualBoundsMm.min[0]/10,-expected.visualBoundsMm.max[1]/10,expected.visualBoundsMm.min[2]/10],
      max:[expected.visualBoundsMm.max[0]/10,-expected.visualBoundsMm.min[1]/10,expected.visualBoundsMm.max[2]/10]};
    let error=0;
    for(const axis of ['min','max'])for(let i=0;i<3;i++) {
      const value=row.boundsCm[axis][i],target=expected.expectedWorldBoundsCm[axis][i];
      assert(Number.isFinite(value)&&Number.isFinite(target));
      assert(Math.abs(converted[axis][i]-target)<1e-5,'Stove unit/axis conversion differs');
      error=Math.max(error,Math.abs(value-target));
    }
    assert(error<.05,'Native stove bounds exceed 0.5 mm');
    assert(Math.abs(row.maxErrorCm-error)<1e-9,'Misreported stove bounds error');maximum=Math.max(maximum,error);
  }
  assert.equal(report.maxNativeBoundsErrorCm,maximum);
  assert.deepEqual(report.sourceRenderChanges.map(row=>row.sourceId).sort(),stoveSourceIds);
  const componentIds=new Set();
  for(const row of report.sourceRenderChanges) {
    assert(!componentIds.has(row.component),'Duplicate hidden source component');componentIds.add(row.component);
    assert.equal(row.before.visible,true);assert.equal(row.before.hiddenInGame,false);
    assert.equal(row.after.visible,false);assert.equal(row.after.hiddenInGame,true);
    assert.deepEqual(keys(row.after.renderFlags),renderFlags);assert(Object.values(row.after.renderFlags).every(value=>value===false));
    assert.deepEqual(keys(row.before.renderFlags),renderFlags);assert(Object.values(row.before.renderFlags).every(value=>typeof value==='boolean'));
  }
  assert.deepEqual(report.materials.bindingChanges??[],[],'Stove helper changed original bindings');
  assert.deepEqual(keys(report.materials.materials),keys(roleSources));
  assert.equal(report.materials.ownedAssets.length,4);
  for(const role of ['chamber','logs','flames','embers']) {
    const path=report.materials.materials[role];
    assert(path.startsWith('/Game/Brezi/Realism/Stove/Materials/'),'Stove material outside owned namespace');
    assert(report.materials.ownedAssets.includes(path));
  }
  assert(!report.materials.ownedAssets.includes(report.materials.materials.shell),'Existing shell finish replaced');
  assert.deepEqual(report.materials.originalGraphs,report.materials.protectedGraphs);
  assert(report.savedMaterialReadback,'Missing saved material graph readback');
  assert.equal(report.savedMaterialReadback.status,'saved-reloaded-validated');
  assert.equal(report.savedMaterialReadback.savedReloaded,true);
  for(const field of ['materials','graphs','sourceBindings','originalGraphs','protectedGraphs','recipe','surfaces','textures'])
    assert.deepEqual(report.savedMaterialReadback[field],report.materials[field],'Saved stove material evidence differs: '+field);
  assert.deepEqual(keys(report.materials.graphs),[...report.materials.ownedAssets].sort());
  assert.deepEqual(keys(report.materials.sourceBindings),Array.from({length:19},(_,i)=>'DOM_'+String(553+i).padStart(5,'0')));
  assert.equal(report.materials.materials.shell,report.materials.sourceBindings.DOM_00553.material);
  for(const change of report.sourceRenderChanges) {
    const original=report.materials.sourceBindings[change.sourceId];
    assert.equal(change.actor,original.actor);assert.equal(change.component,original.component);
  }
  assert.deepEqual(keys(report.textures),keys(textureHashes));
  assert.deepEqual(report.savedTextureReadback,report.authoredTextureReadback);
  for(const [name,expectedHash] of Object.entries(textureHashes)) {
    const row=report.textures[name],saved=report.savedTextureReadback[name];
    const size=name==='T_Fire_SubUV'?[1024,1024]:[512,512];
    assert.equal(row.sha256,expectedHash);assert.equal(saved.sha256,expectedHash);
    assert.deepEqual(row.dependencies,[]);assert.deepEqual(saved.dependencies,[]);
    assert.equal(row.ownedPackage,'/Game/Brezi/Realism/Stove/Fire/Textures/'+name);
    assert.equal(saved.asset,row.ownedPackage+'.'+name);
    assert.deepEqual(row.nativeSize,size);assert.deepEqual(saved.nativeSize,size);
    assert.deepEqual(row.properties,saved.properties);
    assert.equal(row.copiedFile,resolve(project,'Content/Brezi/Realism/Stove/Fire/Textures/'+name+'.uasset'));
    assert.equal(report.afterAssetHashes[row.copiedFile],expectedHash,'Owned texture bytes changed');
    assert.equal(report.inputFiles[row.installedSource],expectedHash,'Missing installed texture pin');
  }
  assert(Number.isInteger(report.originalActorCount)&&report.originalActorCount>0);
  assert.equal(new Set(report.addedActors).size,report.addedActors.length);assert(report.addedActors.length>=5);
  assert.equal(report.finalActorCount,report.originalActorCount+report.addedActors.length);
  assert(hash(report.protectedActorWitnessSha256)&&hash(report.authoredActorWitnessSha256));
  assert.equal(report.savedProtectedActorWitnessSha256,report.protectedActorWitnessSha256);
  assert.equal(report.savedActorWitnessSha256,report.authoredActorWitnessSha256);
  assert.deepEqual(report.beforeAssetHashes,source.content);
  const content=resolve(project,'Content'),map=resolve(content,'Brezi/Maps/Brezi.umap'),after=report.afterAssetHashes;
  assert(Object.values(after).every(hash));
  for(const [path,value] of Object.entries(source.content)) {
    assert(Object.hasOwn(after,path),'Stove stage removed an original asset');
    if(path!==map)assert.equal(after[path],value,'Stove stage changed an original asset');
  }
  const added=keys(after).filter(path=>!Object.hasOwn(source.content,path));
  assert(added.length>=11);assert.deepEqual([...report.newAssets].sort(),added);
  for(const path of added)assert(path===resolve(path)&&path.startsWith(resolve(content,'Brezi/Realism/Stove')+'/')&&/\.(uasset|uexp|ubulk)$/.test(path),
    'New asset escaped stove namespace');
  const changed=keys(source.content).filter(path=>source.content[path]!==after[path]);
  assert.deepEqual(changed,[map]);assert.equal(report.changedAssets.length,1);
  assert.deepEqual(report.changedAssets[0],{path:map,beforeSha256:source.content[map],afterSha256:after[map]});
  return after;
}

export async function verifyStoveScene({root,output,project,source}) {
  const reportFile=resolve(output,'realism-stove-report.json'),report=await read(reportFile);
  const hostFile=resolve(output,'realism-stove-process.json'),host=await read(hostFile);
  const processFile=resolve(output,'realism-stove.log.json'),logFile=resolve(output,'realism-stove.log');
  assert.equal(host.processFile,processFile);assert.equal(host.logFile,logFile);
  const process=await read(processFile),profile=await read(resolve(output,'profile.json'));
  assert.equal(process.code,0);assert.equal(process.signal,null);assert.equal(process.pid,report.nativeProcessId);
  assert.equal(process.command,resolve(profile.engine,'Engine/Binaries/Mac/UnrealEditor-Cmd'));
  assert(process.args.includes(resolve(project,'BreziTwin.uproject'))&&process.args.includes('-run=pythonscript')
    &&process.args.includes('-script='+resolve(root,'scripts/unreal/realism-stove-import.py')),'Unrelated stove native process');
  const start=Date.parse(report.startedAt),end=Date.parse(report.generatedAt);
  assert(start>=Date.parse(process.startedAt)&&end>=start&&end<=Date.parse(process.endedAt),'Stove report outside native process lifetime');
  for(const name of ['realism-stove-import.py','realism-stove-geometry.py','realism-stove-materials.py','realism-fire-texture-probe.py','realism-room-details-import.py','realism-fixtures-import.py','performance-optimize.py','performance_scene_policy.py','stove-visuals/generate.py'])
    assert(hash(report.pipelineFiles[resolve(root,'scripts/unreal',name)]),'Missing stove pipeline pin');
  for(const [path,value] of Object.entries(source.geometry))assert.equal(report.inputFiles[path],value,'Unpinned inherited geometry');
  const manifestFile=resolve(report.artifact,'geometry-report.json'),glbFile=resolve(report.artifact,'realism-stove-study.glb');
  assert.equal(report.inputFiles[manifestFile],report.manifestSha256);
  const manifest=await read(manifestFile);
  assert.equal(manifest.glbSha256,report.inputFiles[glbFile]);
  assert.equal(manifest.generatorSha256,report.pipelineFiles[resolve(root,'scripts/unreal/realism-stove-geometry.py')]);
  assert.equal(manifest.sourceSceneSha256,report.inputFiles[resolve(output,'geometry/scene.json')]);
  assert.equal(manifest.sourceObjSha256,report.inputFiles[resolve(output,'geometry/dom-mm.obj')]);
  assert.deepEqual(manifest.generatorDependencies,{'scripts/unreal/stove-visuals/generate.py':report.pipelineFiles[resolve(root,'scripts/unreal/stove-visuals/generate.py')]});
  const sourceScene=await read(resolve(output,'geometry/scene.json'));
  for(const id of stoveSourceIds)assert.deepEqual(manifest.sourceRecords[id],sourceScene.objects.find(row=>row.id===id));
  const proof=report.probeLogProof,probe=resolve(root,'output/unreal/realism-fire-texture-probe-20260926-r1');
  assert.equal(proof.path,resolve(probe,'native.log'));
  const probeLog=await readFile(proof.path),probeProcess=await read(resolve(probe,'native-process.json'));
  assert.equal(probeProcess.returncode,0);assert.equal(probeProcess.logSha256,proof.originalSha256);
  assert(Number.isInteger(proof.originalBytes)&&proof.originalBytes>0&&proof.originalBytes<=probeLog.length);
  assert.equal(sha(probeLog.subarray(0,proof.originalBytes)),proof.originalSha256,'Original probe log changed');
  assert.equal(sha(probeLog.subarray(proof.originalBytes)),proof.appendedSha256);
  assert.equal(probeLog.length-proof.originalBytes,proof.appendedBytes);
  if(proof.appendedBytes) {
    assert.equal(proof.appendedBytes,855);
    assert.equal(proof.appendedSha256,'a7258fe74f1f9b9d957da648c51d760a24da175914af4104595a01402f602fcb','Unreviewed probe log append');
    assert.equal(proof.appendClassification,'reviewed-benign-UnrealTrace-shutdown');
  } else assert.equal(proof.appendClassification,'none');
  assert.equal(sha(probeLog),proof.completeSha256);assert.equal(report.inputFiles[proof.path],proof.completeSha256);
  const inputs={[reportFile]:host.reportSha256,[hostFile]:sha(await readFile(hostFile)),[processFile]:host.processFileSha256,
    [logFile]:host.logSha256,...report.pipelineFiles,...report.inputFiles};
  for(const [path,value] of Object.entries(inputs)) {
    assert(hash(value),'Invalid stove input hash');assert.equal(sha(await readFile(path)),value,'Stove input changed: '+path);
  }
  const content=validateStoveReceipt({report,source,project,manifest});
  return {content,inputs,stove:{status:report.status,report:reportFile,reportSha256:host.reportSha256,
    sourceIds:stoveSourceIds,visualMeshCount:5,hiddenSourceCount:7,fireTextureCount:2,nativeRenderedVerified:false}};
}
