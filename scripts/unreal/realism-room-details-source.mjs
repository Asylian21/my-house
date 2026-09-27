// Separate receipt for a visual-only room detail overlay on immutable inherited assets.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=async path=>JSON.parse(await readFile(path));
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const keys=value=>Object.keys(value).sort();
export const roomHiddenIds=[...Array.from({length:12},(_,i)=>938+i),1225,1226].map(i=>'DOM_'+String(i).padStart(5,'0'));
export const roomSourceIds=['DOM_00740',...roomHiddenIds];
export const roomMotionIds=[941,942,943,947,948,949].map(i=>'DOM_'+String(i).padStart(5,'0'));
export const roomMeshIds=['WASHER','DRYER'].flatMap(appliance=>['BODY','CONTROLS','SELECTOR','DOOR_RIM','DOOR_GLASS','DOOR_HANDLE'].map(part=>`RD_${appliance}_${part}`))
  .concat(['RD_BOY_LAMP_BASE','RD_BOY_LAMP_GLOBE',...Array.from({length:4},(_,i)=>`RD_SINK_CORNER_${i+1}`)]).sort();
const renderFlags=['affect_distance_field_lighting','affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden',
  'cast_hidden_shadow','cast_shadow','visible_in_ray_tracing'];

export function validateRoomDetailReceipt({report,source,project,manifest}) {
  assert.equal(report.schemaVersion,1);assert.equal(report.owner,'scripts/unreal/realism-room-details-import.py');
  assert.equal(report.status,'realism-room-details-validated');assert.equal(report.project,project);assert.equal(report.sourceOutput,source.donor);
  for(const field of ['savedReloaded','protectedContentUnchanged','sourceGeometryCollisionAndTransformsPreserved','originalMaterialAssetsPreserved','originalMaterialBindingsPreserved','parentMotionVerified'])assert.equal(report[field],true);
  assert.equal(manifest.owner,'scripts/unreal/realism-room-details-geometry.py');assert.equal(manifest.status,'offline-geometry-validated');
  assert.deepEqual(report.sourceIds,roomSourceIds);assert.deepEqual([...manifest.sourceIds].sort(),roomSourceIds);
  assert.deepEqual(report.movingSourceRenderPolicy,{visible:true,hiddenInGame:false,render_in_main_pass:false,render_in_depth_pass:false});
  assert.deepEqual(report.hiddenSourceIds,roomHiddenIds);assert.deepEqual([...manifest.hiddenSourceIds].sort(),roomHiddenIds);
  assert.deepEqual(manifest.objects.flatMap(row=>row.hiddenSourceIds).sort(),roomHiddenIds);
  assert.deepEqual(manifest.objects.filter(row=>row.motionSourceId).map(row=>row.motionSourceId).sort(),roomMotionIds);
  assert.deepEqual(keys(manifest.motionBindings),roomMotionIds);
  assert.deepEqual(manifest.objects.map(row=>row.id).sort(),roomMeshIds);
  assert.deepEqual(keys(report.objects),roomMeshIds);assert.equal(report.savedGeometryReadback.length,18);
  const expectedById=new Map(manifest.objects.map(row=>[row.id,row]));
  assert.deepEqual([...new Set(manifest.objects.flatMap(row=>row.sourceIds))].sort(),roomSourceIds);
  let maximum=0;
  const checked=new Set();
  for(const row of report.savedGeometryReadback) {
    assert(!checked.has(row.id),'Duplicate room detail readback');checked.add(row.id);
    const expected=expectedById.get(row.id);assert(expected,'Unknown room detail readback');
    assert.deepEqual(row.expectedBoundsCm,expected.expectedWorldBoundsCm);
    assert.deepEqual(report.objects[row.id].sourceIds,expected.sourceIds);
    assert.equal(row.actor,report.objects[row.id].actor);assert.equal(row.collision,'NoCollision');
    assert(report.addedActors.includes(row.actor),'Room detail readback actor not newly owned');
    assert.deepEqual(row.materials,report.objects[row.id].materials);
    assert.equal(row.materials.length,expected.materialBindings.length);
    const moving=!!expected.motionSourceId;
    assert.equal(row.motionSourceId,expected.motionSourceId);assert.equal(report.objects[row.id].motionSourceId,expected.motionSourceId);
    assert.equal(row.mobility,moving?'Movable':'Static');assert.equal(row.sourceDoorContractVerified,moving);
    if(moving) {
      const sourceChange=report.sourceRenderChanges.find(change=>change.sourceId===expected.motionSourceId);
      assert.equal(row.attachParent,sourceChange.component);assert.equal(report.objects[row.id].attachParent,sourceChange.component);
    }
    const additive=row.id.startsWith('RD_SINK_CORNER_');
    assert.equal(expected.mode,additive?'additive':'replacement');
    if(additive) {assert.deepEqual(expected.sourceIds,['DOM_00740']);assert.deepEqual(expected.hiddenSourceIds,[]);}
    else assert(expected.hiddenSourceIds.length>0);
    assert(report.objects[row.id].mesh.startsWith('/Game/Brezi/Realism/RoomDetails/'),'Room detail mesh outside owned namespace');
    const converted={min:[expected.visualBoundsMm.min[0]/10,-expected.visualBoundsMm.max[1]/10,expected.visualBoundsMm.min[2]/10],
      max:[expected.visualBoundsMm.max[0]/10,-expected.visualBoundsMm.min[1]/10,expected.visualBoundsMm.max[2]/10]};
    let error=0;
    for(const axis of ['min','max'])for(let i=0;i<3;i++) {
      const value=row.boundsCm[axis][i],target=expected.expectedWorldBoundsCm[axis][i];
      assert(Number.isFinite(value)&&Number.isFinite(target));
      assert(Math.abs(converted[axis][i]-target)<1e-5,'Room detail unit/axis conversion differs');
      error=Math.max(error,Math.abs(value-target));
    }
    assert(error<.05,'Native room detail bounds exceed 0.5 mm');
    assert(Math.abs(row.maxErrorCm-error)<1e-9,'Misreported room detail bounds error');maximum=Math.max(maximum,error);
  }
  assert.equal(report.maxNativeBoundsErrorCm,maximum);
  assert.deepEqual(report.sourceRenderChanges.map(row=>row.sourceId).sort(),roomHiddenIds);
  const componentIds=new Set();
  for(const row of report.sourceRenderChanges) {
    assert(!componentIds.has(row.component),'Duplicate hidden source component');componentIds.add(row.component);
    assert.equal(row.before.visible,true);assert.equal(row.before.hiddenInGame,false);
    assert.equal(row.after.visible,roomMotionIds.includes(row.sourceId));assert.equal(row.after.hiddenInGame,!roomMotionIds.includes(row.sourceId));
    assert.deepEqual(keys(row.after.renderFlags),renderFlags);assert(Object.values(row.after.renderFlags).every(value=>value===false));
    assert.deepEqual(keys(row.before.passFlags),['render_in_depth_pass','render_in_main_pass']);
    assert(Object.values(row.before.passFlags).every(value=>typeof value==='boolean'));
    assert.deepEqual(row.after.passFlags,roomMotionIds.includes(row.sourceId)?{render_in_main_pass:false,render_in_depth_pass:false}:row.before.passFlags);
    assert.deepEqual(keys(row.before.renderFlags),renderFlags);assert(Object.values(row.before.renderFlags).every(value=>typeof value==='boolean'));
  }
  assert.deepEqual(report.parentMotionAudit.map(row=>row.sourceId).sort(),roomMotionIds);
  for(const motion of report.parentMotionAudit) {
    const object=manifest.objects.find(row=>row.id===motion.id);assert(object);
    assert.equal(motion.sourceId,object.motionSourceId);assert.equal(motion.doorId,object.doorId);
    assert.equal(motion.parent,report.objects[motion.id].attachParent);assert.equal(motion.closedPoseRestored,true);
    assert.deepEqual(motion.samples.map(row=>row.progress),[0,.5,1]);
    assert.equal(new Set(motion.samples.map(row=>row.sampleIndex)).size,3);
    for(const row of motion.samples) {
      assert(Number.isInteger(row.sampleIndex)&&row.sampleIndex>=0&&Number.isFinite(row.maxBasisErrorCm)&&row.maxBasisErrorCm>=0&&row.maxBasisErrorCm<.005,'Moving overlay failed parent motion');
      assert.equal(row.expectedBasisPointsCm.length,4);assert.equal(row.actualBasisPointsCm.length,4);
      const errors=row.actualBasisPointsCm.map((point,index)=> {
        assert.equal(point.length,3);assert.equal(row.expectedBasisPointsCm[index].length,3);
        assert([...point,...row.expectedBasisPointsCm[index]].every(Number.isFinite));
        return Math.hypot(...point.map((value,axis)=>value-row.expectedBasisPointsCm[index][axis]));
      });
      assert(Math.abs(Math.max(...errors)-row.maxBasisErrorCm)<1e-9,'Misreported moving overlay error');
    }
  }
  assert(Number.isInteger(report.originalActorCount)&&report.originalActorCount>0);
  assert.equal(new Set(report.addedActors).size,report.addedActors.length);assert(report.addedActors.length>=18);
  assert.equal(report.finalActorCount,report.originalActorCount+report.addedActors.length);
  assert(hash(report.protectedActorWitnessSha256)&&hash(report.authoredActorWitnessSha256));
  assert.equal(report.savedProtectedActorWitnessSha256,report.protectedActorWitnessSha256);
  assert.equal(report.savedActorWitnessSha256,report.authoredActorWitnessSha256);
  assert.deepEqual(report.beforeAssetHashes,source.content);
  const content=resolve(project,'Content'),map=resolve(content,'Brezi/Maps/Brezi.umap'),after=report.afterAssetHashes;
  assert(Object.values(after).every(hash));
  for(const [path,value] of Object.entries(source.content)) {
    assert(Object.hasOwn(after,path),'Room detail stage removed an original asset');
    if(path!==map)assert.equal(after[path],value,'Room detail stage changed an original asset');
  }
  const added=keys(after).filter(path=>!Object.hasOwn(source.content,path));
  assert(added.length>=18);assert.deepEqual([...report.newAssets].sort(),added);
  for(const path of added)assert(path===resolve(path)&&path.startsWith(resolve(content,'Brezi/Realism/RoomDetails')+'/')&&/\.(uasset|uexp|ubulk)$/.test(path),
    'New asset escaped room-detail namespace');
  const changed=keys(source.content).filter(path=>source.content[path]!==after[path]);
  assert.deepEqual(changed,[map]);assert.equal(report.changedAssets.length,1);
  assert.deepEqual(report.changedAssets[0],{path:map,beforeSha256:source.content[map],afterSha256:after[map]});
  return after;
}

export async function verifyRoomDetailScene({root,output,project,source}) {
  const reportFile=resolve(output,'realism-room-details-report.json'),report=await read(reportFile);
  const hostFile=resolve(output,'realism-room-details-process.json'),host=await read(hostFile);
  const processFile=resolve(output,'realism-room-details.log.json'),logFile=resolve(output,'realism-room-details.log');
  assert.equal(host.processFile,processFile);assert.equal(host.logFile,logFile);
  const process=await read(processFile),profile=await read(resolve(output,'profile.json'));
  assert.equal(process.code,0);assert.equal(process.signal,null);assert.equal(process.pid,report.nativeProcessId);
  assert.equal(process.command,resolve(profile.engine,'Engine/Binaries/Mac/UnrealEditor-Cmd'));
  assert(process.args.includes(resolve(project,'BreziTwin.uproject'))&&process.args.includes('-run=pythonscript')
    &&process.args.includes('-script='+resolve(root,'scripts/unreal/realism-room-details-import.py')),'Unrelated room detail native process');
  const start=Date.parse(report.startedAt),end=Date.parse(report.generatedAt);
  assert(start>=Date.parse(process.startedAt)&&end>=start&&end<=Date.parse(process.endedAt),'Room detail report outside native process lifetime');
  for(const name of ['realism-room-details-import.py','realism-room-details-geometry.py','realism-fixtures-import.py','realism-fixtures-geometry.py','performance-optimize.py','performance_scene_policy.py'])
    assert(hash(report.pipelineFiles[resolve(root,'scripts/unreal',name)]),'Missing room detail pipeline pin');
  for(const [path,value] of Object.entries(source.geometry))assert.equal(report.inputFiles[path],value,'Unpinned inherited geometry');
  const manifestFile=resolve(report.artifact,'geometry-report.json'),glbFile=resolve(report.artifact,'realism-room-details.glb');
  assert.equal(report.inputFiles[manifestFile],report.manifestSha256);
  const manifest=await read(manifestFile);
  assert.equal(manifest.glbSha256,report.inputFiles[glbFile]);
  assert.equal(manifest.generatorSha256,report.pipelineFiles[resolve(root,'scripts/unreal/realism-room-details-geometry.py')]);
  assert.equal(manifest.sourceSceneSha256,report.inputFiles[resolve(output,'geometry/scene.json')]);
  assert.equal(manifest.sourceObjSha256,report.inputFiles[resolve(output,'geometry/dom-mm.obj')]);
  assert.equal(manifest.sourceDoorsSha256,report.inputFiles[resolve(output,'geometry/doors.json')]);
  assert.deepEqual(manifest.generatorDependencies,{'scripts/unreal/realism-fixtures-geometry.py':report.pipelineFiles[resolve(root,'scripts/unreal/realism-fixtures-geometry.py')]});
  const doors=await read(resolve(output,'geometry/doors.json'));
  for(const [sourceId,binding] of Object.entries(manifest.motionBindings)) {
    const door=doors.doors.find(row=>row.id===binding.doorId),member=door?.members.find(row=>row.sourceObjectId===sourceId);assert(member);
    assert.deepEqual(binding,{doorId:door.id,runtimeTag:member.runtimeTag,collision:member.collision,closedBoundsCm:member.closedBoundsCm});
  }
  for(const motion of report.parentMotionAudit)for(const sample of motion.samples)
    assert.equal(doors.progressSamples[sample.sampleIndex],sample.progress,'Motion audit did not exercise requested pose');
  const inputs={[reportFile]:host.reportSha256,[hostFile]:sha(await readFile(hostFile)),[processFile]:host.processFileSha256,
    [logFile]:host.logSha256,...report.pipelineFiles,...report.inputFiles};
  for(const [path,value] of Object.entries(inputs)) {
    assert(hash(value),'Invalid room detail input hash');assert.equal(sha(await readFile(path)),value,'Room detail input changed: '+path);
  }
  const content=validateRoomDetailReceipt({report,source,project,manifest});
  return {content,inputs,roomDetails:{status:report.status,report:reportFile,reportSha256:host.reportSha256,
    sourceIds:roomSourceIds,visualMeshCount:18,movingMeshCount:6,parentMotionVerified:true,nativeRenderedVerified:false}};
}
