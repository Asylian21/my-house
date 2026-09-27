// Separate receipt for a visual-only fixture overlay on immutable inherited assets.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=async path=>JSON.parse(await readFile(path));
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const keys=value=>Object.keys(value).sort();
export const fixtureSourceIds=Array.from({length:8},(_,i)=>'DOM_'+String(759+i).padStart(5,'0'));
const fixtureMeshIds=['RF_SINK_BOWL','RF_SINK_DRAIN','RF_SINK_LEVER','RF_SINK_SPOUT'];
const renderFlags=['affect_distance_field_lighting','affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden',
  'cast_hidden_shadow','cast_shadow','visible_in_ray_tracing'];

export function validateFixtureReceipt({report,source,project,manifest}) {
  assert.equal(report.schemaVersion,1);assert.equal(report.owner,'scripts/unreal/realism-fixtures-import.py');
  assert.equal(report.status,'realism-fixtures-validated');assert.equal(report.project,project);assert.equal(report.sourceOutput,source.donor);
  for(const field of ['savedReloaded','protectedContentUnchanged','sourceGeometryCollisionAndTransformsPreserved','originalMaterialAssetsPreserved','materialBindingsAudited'])assert.equal(report[field],true);
  assert.equal(manifest.owner,'scripts/unreal/realism-fixtures-geometry.py');assert.equal(manifest.status,'offline-geometry-validated');
  assert.deepEqual(report.sourceIds,fixtureSourceIds);assert.deepEqual([...manifest.sourceIds].sort(),fixtureSourceIds);
  assert.deepEqual(manifest.objects.map(row=>row.id).sort(),fixtureMeshIds);
  assert.deepEqual(keys(report.objects),fixtureMeshIds);assert.equal(report.savedGeometryReadback.length,4);
  const expectedById=new Map(manifest.objects.map(row=>[row.id,row]));
  assert.deepEqual([...new Set(manifest.objects.flatMap(row=>row.sourceIds))].sort(),fixtureSourceIds);
  let maximum=0;
  const checked=new Set();
  for(const row of report.savedGeometryReadback) {
    assert(!checked.has(row.id),'Duplicate fixture readback');checked.add(row.id);
    const expected=expectedById.get(row.id);assert(expected,'Unknown fixture readback');
    assert.deepEqual(row.expectedBoundsCm,expected.expectedWorldBoundsCm);
    assert.deepEqual(report.objects[row.id].sourceIds,expected.sourceIds);
    assert.equal(row.actor,report.objects[row.id].actor);assert.equal(row.collision,'NoCollision');
    assert(report.addedActors.includes(row.actor),'Fixture readback actor not newly owned');
    assert.deepEqual(row.materials,report.objects[row.id].materials);
    assert.equal(row.materials.length,expected.materialBindings.length);
    assert(report.objects[row.id].mesh.startsWith('/Game/Brezi/Realism/Fixtures/'),'Fixture mesh outside owned namespace');
    const converted={min:[expected.visualBoundsMm.min[0]/10,-expected.visualBoundsMm.max[1]/10,expected.visualBoundsMm.min[2]/10],
      max:[expected.visualBoundsMm.max[0]/10,-expected.visualBoundsMm.min[1]/10,expected.visualBoundsMm.max[2]/10]};
    let error=0;
    for(const axis of ['min','max'])for(let i=0;i<3;i++) {
      const value=row.boundsCm[axis][i],target=expected.expectedWorldBoundsCm[axis][i];
      assert(Number.isFinite(value)&&Number.isFinite(target));
      assert(Math.abs(converted[axis][i]-target)<1e-5,'Fixture unit/axis conversion differs');
      error=Math.max(error,Math.abs(value-target));
    }
    assert(error<.05,'Native fixture bounds exceed 0.5 mm');
    assert(Math.abs(row.maxErrorCm-error)<1e-9,'Misreported fixture bounds error');maximum=Math.max(maximum,error);
  }
  assert.equal(report.maxNativeBoundsErrorCm,maximum);
  assert.deepEqual(report.sourceRenderChanges.map(row=>row.sourceId).sort(),fixtureSourceIds);
  const componentIds=new Set();
  for(const row of report.sourceRenderChanges) {
    assert(!componentIds.has(row.component),'Duplicate hidden source component');componentIds.add(row.component);
    assert.equal(row.before.visible,true);assert.equal(row.before.hiddenInGame,false);
    assert.equal(row.after.visible,false);assert.equal(row.after.hiddenInGame,true);
    assert.deepEqual(keys(row.after.renderFlags),renderFlags);assert(Object.values(row.after.renderFlags).every(value=>value===false));
    assert.deepEqual(keys(row.before.renderFlags),renderFlags);assert(Object.values(row.before.renderFlags).every(value=>typeof value==='boolean'));
  }
  assert(Array.isArray(report.materialBindingChanges)&&report.materialBindingChanges.length>0,'Missing bounded fabric correction');
  assert.deepEqual(report.materialBindingChanges,report.fabric.bindingChanges);
  assert(report.savedFabricReadback,'Missing saved fabric readback');
  const materialSlots=new Set();
  for(const row of report.materialBindingChanges) {
    assert(typeof row.actor==='string'&&typeof row.component==='string'&&Number.isInteger(row.slot)&&row.slot>=0);
    assert(row.after.startsWith('/Game/Brezi/Realism/Fabric/'),'Fabric binding outside owned namespace');
    const identity=JSON.stringify([row.actor,row.component,row.slot]);assert(!materialSlots.has(identity),'Duplicate fabric slot');materialSlots.add(identity);
  }
  assert(Number.isInteger(report.originalActorCount)&&report.originalActorCount>0);
  assert.equal(new Set(report.addedActors).size,report.addedActors.length);assert(report.addedActors.length>=4);
  assert.equal(report.finalActorCount,report.originalActorCount+report.addedActors.length);
  assert(hash(report.protectedActorWitnessSha256)&&hash(report.authoredActorWitnessSha256));
  assert.equal(report.savedProtectedActorWitnessSha256,report.protectedActorWitnessSha256);
  assert.equal(report.savedActorWitnessSha256,report.authoredActorWitnessSha256);
  assert.deepEqual(report.beforeAssetHashes,source.content);
  const content=resolve(project,'Content'),map=resolve(content,'Brezi/Maps/Brezi.umap'),after=report.afterAssetHashes;
  assert(Object.values(after).every(hash));
  for(const [path,value] of Object.entries(source.content)) {
    assert(Object.hasOwn(after,path),'Fixture stage removed an original asset');
    if(path!==map)assert.equal(after[path],value,'Fixture stage changed an original asset');
  }
  const added=keys(after).filter(path=>!Object.hasOwn(source.content,path));
  assert(added.length>=4);assert.deepEqual([...report.newAssets].sort(),added);
  for(const path of added)assert(path===resolve(path)&&['Fixtures','Fabric'].some(part=>path.startsWith(resolve(content,'Brezi/Realism',part)+'/'))&&/\.(uasset|uexp|ubulk)$/.test(path),
    'New asset escaped fixture/fabric namespace');
  const changed=keys(source.content).filter(path=>source.content[path]!==after[path]);
  assert.deepEqual(changed,[map]);assert.equal(report.changedAssets.length,1);
  assert.deepEqual(report.changedAssets[0],{path:map,beforeSha256:source.content[map],afterSha256:after[map]});
  return after;
}

export async function verifyFixtureScene({root,output,project,source}) {
  const reportFile=resolve(output,'realism-fixtures-report.json'),report=await read(reportFile);
  const hostFile=resolve(output,'realism-fixtures-process.json'),host=await read(hostFile);
  const processFile=resolve(output,'realism-fixtures.log.json'),logFile=resolve(output,'realism-fixtures.log');
  assert.equal(host.processFile,processFile);assert.equal(host.logFile,logFile);
  const process=await read(processFile),profile=await read(resolve(output,'profile.json'));
  assert.equal(process.code,0);assert.equal(process.signal,null);assert.equal(process.pid,report.nativeProcessId);
  assert.equal(process.command,resolve(profile.engine,'Engine/Binaries/Mac/UnrealEditor-Cmd'));
  assert(process.args.includes(resolve(project,'BreziTwin.uproject'))&&process.args.includes('-run=pythonscript')
    &&process.args.includes('-script='+resolve(root,'scripts/unreal/realism-fixtures-import.py')),'Unrelated fixture native process');
  const start=Date.parse(report.startedAt),end=Date.parse(report.generatedAt);
  assert(start>=Date.parse(process.startedAt)&&end>=start&&end<=Date.parse(process.endedAt),'Fixture report outside native process lifetime');
  for(const name of ['realism-fixtures-import.py','realism-fixtures-geometry.py','realism-fabric.py','performance-optimize.py','performance_scene_policy.py'])
    assert(hash(report.pipelineFiles[resolve(root,'scripts/unreal',name)]),'Missing fixture pipeline pin');
  for(const [path,value] of Object.entries(source.geometry))assert.equal(report.inputFiles[path],value,'Unpinned inherited geometry');
  const manifestFile=resolve(report.artifact,'geometry-report.json'),glbFile=resolve(report.artifact,'realism-fixtures.glb');
  assert.equal(report.inputFiles[manifestFile],report.manifestSha256);
  const manifest=await read(manifestFile);
  assert.equal(manifest.glbSha256,report.inputFiles[glbFile]);
  assert.equal(manifest.generatorSha256,report.pipelineFiles[resolve(root,'scripts/unreal/realism-fixtures-geometry.py')]);
  assert.equal(manifest.sourceSceneSha256,report.inputFiles[resolve(output,'geometry/scene.json')]);
  assert.equal(manifest.sourceObjSha256,report.inputFiles[resolve(output,'geometry/dom-mm.obj')]);
  const inputs={[reportFile]:host.reportSha256,[hostFile]:sha(await readFile(hostFile)),[processFile]:host.processFileSha256,
    [logFile]:host.logSha256,...report.pipelineFiles,...report.inputFiles};
  for(const [path,value] of Object.entries(inputs)) {
    assert(hash(value),'Invalid fixture input hash');assert.equal(sha(await readFile(path)),value,'Fixture input changed: '+path);
  }
  const content=validateFixtureReceipt({report,source,project,manifest});
  return {content,inputs,fixtures:{status:report.status,report:reportFile,reportSha256:host.reportSha256,
    sourceIds:fixtureSourceIds,visualMeshCount:4,fabricBindingCount:report.materialBindingChanges.length,nativeRenderedVerified:false}};
}
