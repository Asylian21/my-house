// Separate receipt for a visual-only furniture overlay on immutable inherited assets.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=async path=>JSON.parse(await readFile(path));
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const keys=value=>Object.keys(value).sort();
export const furnitureSourceIds=[1443,1444,1445,1446,1447,1448,1449,1452,1466,1473,1475,1482,1484,1491,1493,1500,1502,1509,1511,1518].map(i=>'DOM_'+String(i).padStart(5,'0'));
const furnitureMeshIds=furnitureSourceIds.map(id=>'RU_'+id).sort();
export const grainSourceIds=[1457,1458,1459,1460,1461,1474,1483,1492,1501,1510,1519].map(i=>'DOM_'+String(i).padStart(5,'0'));
const grainAxis=id=>['DOM_01460','DOM_01461'].includes(id)?'X':'Y';
const renderFlags=['affect_distance_field_lighting','affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden',
  'cast_hidden_shadow','cast_shadow','visible_in_ray_tracing'];

export function validateFurnitureReceipt({report,source,project,manifest}) {
  assert.equal(report.schemaVersion,1);assert.equal(report.owner,'scripts/unreal/realism-furniture-import.py');
  assert.equal(report.status,'realism-furniture-validated');assert.equal(report.project,project);assert.equal(report.sourceOutput,source.donor);
  for(const field of ['savedReloaded','protectedContentUnchanged','sourceGeometryCollisionAndTransformsPreserved','originalMaterialAssetsPreserved','materialBindingsAudited'])assert.equal(report[field],true);
  assert.equal(manifest.owner,'scripts/unreal/realism-upholstery-geometry.py');assert.equal(manifest.status,'offline-geometry-validated');
  assert.deepEqual(report.sourceIds,furnitureSourceIds);assert.deepEqual([...manifest.sourceIds].sort(),furnitureSourceIds);
  assert.deepEqual(report.hiddenSourceIds,[]);assert.deepEqual(manifest.hiddenSourceIds,[]);
  const visualIds=furnitureSourceIds.map(id=>'PH_'+id);
  assert.deepEqual([...report.hiddenVisualSourceIds].sort(),visualIds);assert.deepEqual([...manifest.hiddenVisualSourceIds].sort(),visualIds);
  assert.deepEqual(manifest.objects.flatMap(row=>row.hiddenVisualSourceIds).sort(),visualIds);
  assert.deepEqual(manifest.objects.map(row=>row.id).sort(),furnitureMeshIds);
  assert.deepEqual(keys(report.objects),furnitureMeshIds);assert.equal(report.savedGeometryReadback.length,20);
  const expectedById=new Map(manifest.objects.map(row=>[row.id,row]));
  assert.deepEqual([...new Set(manifest.objects.flatMap(row=>row.sourceIds))].sort(),furnitureSourceIds);
  let maximum=0;
  const checked=new Set();
  for(const row of report.savedGeometryReadback) {
    assert(!checked.has(row.id),'Duplicate furniture readback');checked.add(row.id);
    const expected=expectedById.get(row.id);assert(expected,'Unknown furniture readback');
    assert.deepEqual(row.expectedBoundsCm,expected.expectedWorldBoundsCm);
    assert.deepEqual(report.objects[row.id].sourceIds,expected.sourceIds);
    assert.equal(row.actor,report.objects[row.id].actor);assert.equal(row.collision,'NoCollision');
    assert(report.addedActors.includes(row.actor),'Furniture readback actor not newly owned');
    assert.deepEqual(row.materials,report.objects[row.id].materials);
    assert.equal(row.materials.length,1);assert.deepEqual(expected.hiddenSourceIds,[]);
    assert.deepEqual(expected.sourceIds,[row.id.slice(3)]);
    assert.deepEqual(expected.materialBindings,[{sourceId:row.id.slice(3),sourceSlot:0,visualSourceId:'PH_'+row.id.slice(3)}]);
    assert(report.objects[row.id].mesh.startsWith('/Game/Brezi/Realism/Furniture/Geometry/'),'Furniture mesh outside owned namespace');
    const converted={min:[expected.visualBoundsMm.min[0]/10,-expected.visualBoundsMm.max[1]/10,expected.visualBoundsMm.min[2]/10],
      max:[expected.visualBoundsMm.max[0]/10,-expected.visualBoundsMm.min[1]/10,expected.visualBoundsMm.max[2]/10]};
    let error=0;
    for(const axis of ['min','max'])for(let i=0;i<3;i++) {
      const value=row.boundsCm[axis][i],target=expected.expectedWorldBoundsCm[axis][i];
      assert(Number.isFinite(value)&&Number.isFinite(target));
      assert(Math.abs(converted[axis][i]-target)<1e-5,'Furniture unit/axis conversion differs');
      error=Math.max(error,Math.abs(value-target));
    }
    assert(error<.05,'Native furniture bounds exceed 0.5 mm');
    assert(Math.abs(row.maxErrorCm-error)<1e-9,'Misreported furniture bounds error');maximum=Math.max(maximum,error);
  }
  assert.equal(report.maxNativeBoundsErrorCm,maximum);
  assert.deepEqual(report.sourceRenderChanges.map(row=>row.sourceId).sort(),furnitureSourceIds);
  const componentIds=new Set();
  for(const row of report.sourceRenderChanges) {
    assert.equal(row.visualSourceId,'PH_'+row.sourceId);
    assert(!componentIds.has(row.component),'Duplicate hidden source component');componentIds.add(row.component);
    assert.equal(row.before.visible,true);assert.equal(row.before.hiddenInGame,false);
    assert.equal(row.after.visible,false);assert.equal(row.after.hiddenInGame,true);
    assert.deepEqual(keys(row.after.renderFlags),renderFlags);assert(Object.values(row.after.renderFlags).every(value=>value===false));
    assert.deepEqual(keys(row.before.renderFlags),renderFlags);assert(Object.values(row.before.renderFlags).every(value=>typeof value==='boolean'));
  }
  assert(Array.isArray(report.materialBindingChanges)&&report.materialBindingChanges.length===11,'Missing bounded grain correction');
  assert.deepEqual(report.materialBindingChanges,report.grain.bindingChanges);
  assert(report.savedGrainReadback,'Missing saved grain readback');
  assert.equal(report.grain.originalBindingCount,110);assert.equal(report.grain.protectedBindingCount,99);
  assert.deepEqual(report.grain.axisCounts,{X:2,Y:9});
  assert.equal(report.savedGrainReadback.status,'grain-materials-saved-verified');
  assert.equal(report.savedGrainReadback.bindingCount,11);assert.equal(report.savedGrainReadback.protectedBindingCount,99);
  assert.deepEqual(report.savedGrainReadback.materials,report.grain.materials);
  assert.deepEqual(report.grain.originalGraphs,report.grain.protectedGraphs);assert.equal(keys(report.grain.originalGraphs).length,1);
  assert.deepEqual([...report.grain.ownedAssets].sort(),keys(report.grain.materials));
  assert.deepEqual(Object.values(report.grain.materials).map(row=>row.axis).sort(),['X','Y']);
  assert.deepEqual(report.materialBindingChanges.map(row=>row.sourceId).sort(),grainSourceIds);
  assert.equal(new Set(report.materialBindingChanges.map(row=>row.after)).size,2);
  assert.equal(report.grain.ownedAssets.length,2);
  const materialSlots=new Set();
  for(const row of report.materialBindingChanges) {
    assert.equal(row.axis,grainAxis(row.sourceId));assert.equal(report.grain.materials[row.after]?.axis,row.axis);
    assert(typeof row.actor==='string'&&typeof row.component==='string'&&Number.isInteger(row.slot)&&row.slot>=0);
    assert(row.after.startsWith('/Game/Brezi/Realism/Furniture/Materials/'),'Grain binding outside owned namespace');
    const identity=JSON.stringify([row.actor,row.component,row.slot]);assert(!materialSlots.has(identity),'Duplicate grain slot');materialSlots.add(identity);
  }
  assert(Number.isInteger(report.originalActorCount)&&report.originalActorCount>0);
  assert.equal(new Set(report.addedActors).size,report.addedActors.length);assert(report.addedActors.length>=20);
  assert.equal(report.finalActorCount,report.originalActorCount+report.addedActors.length);
  assert(hash(report.protectedActorWitnessSha256)&&hash(report.authoredActorWitnessSha256));
  assert.equal(report.savedProtectedActorWitnessSha256,report.protectedActorWitnessSha256);
  assert.equal(report.savedActorWitnessSha256,report.authoredActorWitnessSha256);
  assert.deepEqual(report.beforeAssetHashes,source.content);
  const content=resolve(project,'Content'),map=resolve(content,'Brezi/Maps/Brezi.umap'),after=report.afterAssetHashes;
  assert(Object.values(after).every(hash));
  for(const [path,value] of Object.entries(source.content)) {
    assert(Object.hasOwn(after,path),'Furniture stage removed an original asset');
    if(path!==map)assert.equal(after[path],value,'Furniture stage changed an original asset');
  }
  const added=keys(after).filter(path=>!Object.hasOwn(source.content,path));
  assert(added.length>=20);assert.deepEqual([...report.newAssets].sort(),added);
  for(const path of added)assert(path===resolve(path)&&path.startsWith(resolve(content,'Brezi/Realism/Furniture')+'/')&&/\.(uasset|uexp|ubulk)$/.test(path),
    'New asset escaped furniture namespace');
  const changed=keys(source.content).filter(path=>source.content[path]!==after[path]);
  assert.deepEqual(changed,[map]);assert.equal(report.changedAssets.length,1);
  assert.deepEqual(report.changedAssets[0],{path:map,beforeSha256:source.content[map],afterSha256:after[map]});
  return after;
}

export async function verifyFurnitureScene({root,output,project,source}) {
  const reportFile=resolve(output,'realism-furniture-report.json'),report=await read(reportFile);
  const hostFile=resolve(output,'realism-furniture-process.json'),host=await read(hostFile);
  const processFile=resolve(output,'realism-furniture.log.json'),logFile=resolve(output,'realism-furniture.log');
  assert.equal(host.processFile,processFile);assert.equal(host.logFile,logFile);
  const process=await read(processFile),profile=await read(resolve(output,'profile.json'));
  assert.equal(process.code,0);assert.equal(process.signal,null);assert.equal(process.pid,report.nativeProcessId);
  assert.equal(process.command,resolve(profile.engine,'Engine/Binaries/Mac/UnrealEditor-Cmd'));
  assert(process.args.includes(resolve(project,'BreziTwin.uproject'))&&process.args.includes('-run=pythonscript')
    &&process.args.includes('-script='+resolve(root,'scripts/unreal/realism-furniture-import.py')),'Unrelated furniture native process');
  const start=Date.parse(report.startedAt),end=Date.parse(report.generatedAt);
  assert(start>=Date.parse(process.startedAt)&&end>=start&&end<=Date.parse(process.endedAt),'Furniture report outside native process lifetime');
  for(const name of ['realism-furniture-import.py','realism-upholstery-geometry.py','realism-furniture-grain.py','realism-grain-study.py','realism-room-details-import.py','realism-fixtures-import.py','performance-optimize.py','performance_scene_policy.py'])
    assert(hash(report.pipelineFiles[resolve(root,'scripts/unreal',name)]),'Missing furniture pipeline pin');
  for(const [path,value] of Object.entries(source.geometry))assert.equal(report.inputFiles[path],value,'Unpinned inherited geometry');
  const manifestFile=resolve(report.artifact,'geometry-report.json'),glbFile=resolve(report.artifact,'realism-upholstery.glb');
  assert.equal(report.inputFiles[manifestFile],report.manifestSha256);
  const manifest=await read(manifestFile);
  assert.equal(manifest.glbSha256,report.inputFiles[glbFile]);
  assert.equal(manifest.generatorSha256,report.pipelineFiles[resolve(root,'scripts/unreal/realism-upholstery-geometry.py')]);
  assert.equal(manifest.sourceSceneSha256,report.inputFiles[resolve(output,'geometry/scene.json')]);
  assert.equal(manifest.sourceObjSha256,report.inputFiles[resolve(output,'geometry/dom-mm.obj')]);
  const phFile=resolve(output,'photoreal-import-report.json'),photoreal=await read(phFile);
  assert.equal(manifest.photorealReportSha256,report.inputFiles[phFile]);assert.equal(report.inputFiles[phFile],source.receiptPins[resolve(source.donor,'photoreal-import-report.json')]);
  assert.deepEqual(manifest.generatorDependencies,{'scripts/unreal/realism-fixtures-geometry.py':report.pipelineFiles[resolve(root,'scripts/unreal/realism-fixtures-geometry.py')]});
  for(const change of report.sourceRenderChanges)assert.equal(change.actor,photoreal.geometry.objects[change.visualSourceId].actor,'May only hide exact existing PH visual');
  for(const change of report.materialBindingChanges)assert.equal(change.actor,photoreal.geometry.objects['PH_'+change.sourceId].actor,'May only override exact selected visible grain component');
  const inputs={[reportFile]:host.reportSha256,[hostFile]:sha(await readFile(hostFile)),[processFile]:host.processFileSha256,
    [logFile]:host.logSha256,...report.pipelineFiles,...report.inputFiles};
  for(const [path,value] of Object.entries(inputs)) {
    assert(hash(value),'Invalid furniture input hash');assert.equal(sha(await readFile(path)),value,'Furniture input changed: '+path);
  }
  const content=validateFurnitureReceipt({report,source,project,manifest});
  return {content,inputs,furniture:{status:report.status,report:reportFile,reportSha256:host.reportSha256,
    sourceIds:furnitureSourceIds,visualMeshCount:20,grainBindingCount:report.materialBindingChanges.length,nativeRenderedVerified:false}};
}
