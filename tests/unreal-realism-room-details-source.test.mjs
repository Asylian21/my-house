import test from 'node:test';
import assert from 'node:assert/strict';
import {validateRoomDetailReceipt,roomSourceIds,roomHiddenIds,roomMotionIds,roomMeshIds} from '../scripts/unreal/realism-room-details-source.mjs';
const oldHash='1'.repeat(64),newHash='2'.repeat(64);
function fixture() {
  const project='/project',content=project+'/Content',map=content+'/Brezi/Maps/Brezi.umap';
  const source={donor:'/donor',content:{[map]:oldHash,[content+'/Brezi/Geometry/Washer.uasset']:oldHash,[content+'/Brezi/Realism/Fixtures/Sink.uasset']:oldHash}};
  const bounds={min:[0,-.1,0],max:[.1,0,.1]},visualBoundsMm={min:[0,0,0],max:[1,1,1]};
  const numbers={BODY:0,CONTROLS:1,SELECTOR:2,DOOR_RIM:3,DOOR_GLASS:4,DOOR_HANDLE:5};
  const rows=roomMeshIds.map(id=> {
    const additive=id.startsWith('RD_SINK'),appliance=id.startsWith('RD_WASHER')?'WASHER':'DRYER';
    const number=additive?740:id.startsWith('RD_BOY')?(id.endsWith('BASE')?1225:1226):
      (appliance==='WASHER'?938:944)+numbers[id.replace('RD_'+appliance+'_','')];
    const sourceId='DOM_'+String(number).padStart(5,'0'),motionSourceId=roomMotionIds.includes(sourceId)?sourceId:null;
    return {id,sourceIds:[sourceId],hiddenSourceIds:additive?[]:[sourceId],mode:additive?'additive':'replacement',motionSourceId,
      doorId:motionSourceId?'BATH-105-'+appliance+'-DOOR':null,expectedWorldBoundsCm:bounds,visualBoundsMm,
      materialBindings:[{sourceId,sourceSlot:0}]};
  });
  const manifest={owner:'scripts/unreal/realism-room-details-geometry.py',status:'offline-geometry-validated',sourceIds:roomSourceIds,hiddenSourceIds:roomHiddenIds,
    objects:rows,motionBindings:Object.fromEntries(rows.filter(row=>row.motionSourceId).map(row=>[row.motionSourceId,{doorId:row.doorId}]))};
  const objects=Object.fromEntries(rows.map(row=>[row.id,{actor:row.id,component:row.id+'.component',sourceIds:row.sourceIds,motionSourceId:row.motionSourceId,
    attachParent:row.motionSourceId?row.motionSourceId+'.source':null,mesh:'/Game/Brezi/Realism/RoomDetails/'+row.id+'.'+row.id,materials:['/Game/Material.Material']}])) ;
  const renderFlags=Object.fromEntries(['cast_shadow','cast_hidden_shadow','affect_distance_field_lighting',
    'affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden','visible_in_ray_tracing'].map(name=>[name,false]));
  const passFlags={render_in_main_pass:true,render_in_depth_pass:true};
  const newAssets=rows.map(row=>content+'/Brezi/Realism/RoomDetails/'+row.id+'.uasset');
  const points=[[0,0,0],[10,0,0],[0,10,0],[0,0,10]];
  const report={schemaVersion:1,owner:'scripts/unreal/realism-room-details-import.py',status:'realism-room-details-validated',project,sourceOutput:source.donor,
    savedReloaded:true,protectedContentUnchanged:true,sourceGeometryCollisionAndTransformsPreserved:true,originalMaterialAssetsPreserved:true,
    originalMaterialBindingsPreserved:true,parentMotionVerified:true,
    movingSourceRenderPolicy:{visible:true,hiddenInGame:false,render_in_main_pass:false,render_in_depth_pass:false},sourceIds:roomSourceIds,hiddenSourceIds:roomHiddenIds,objects,
    savedGeometryReadback:rows.map(row=>({id:row.id,actor:row.id,boundsCm:bounds,expectedBoundsCm:bounds,maxErrorCm:0,materials:objects[row.id].materials,collision:'NoCollision',
      motionSourceId:row.motionSourceId,attachParent:objects[row.id].attachParent,mobility:row.motionSourceId?'Movable':'Static',sourceDoorContractVerified:!!row.motionSourceId})),
    maxNativeBoundsErrorCm:0,sourceRenderChanges:roomHiddenIds.map(id=>({sourceId:id,actor:id,component:id+'.source',
      before:{visible:true,hiddenInGame:false,renderFlags,passFlags},
      after:{visible:roomMotionIds.includes(id),hiddenInGame:!roomMotionIds.includes(id),renderFlags,
        passFlags:roomMotionIds.includes(id)?{render_in_main_pass:false,render_in_depth_pass:false}:passFlags}})),
    parentMotionAudit:rows.filter(row=>row.motionSourceId).map(row=>({id:row.id,sourceId:row.motionSourceId,doorId:row.doorId,parent:objects[row.id].attachParent,closedPoseRestored:true,
      samples:[0,.5,1].map((progress,index)=>({progress,sampleIndex:index,maxBasisErrorCm:0,expectedBasisPointsCm:points,actualBasisPointsCm:points}))})),
    originalActorCount:100,finalActorCount:118,addedActors:rows.map(row=>row.id),protectedActorWitnessSha256:oldHash,
    savedProtectedActorWitnessSha256:oldHash,authoredActorWitnessSha256:newHash,savedActorWitnessSha256:newHash,
    beforeAssetHashes:source.content,afterAssetHashes:{...source.content,[map]:newHash,...Object.fromEntries(newAssets.map(path=>[path,newHash]))},
    newAssets,changedAssets:[{path:map,beforeSha256:oldHash,afterSha256:newHash}]};
  return structuredClone({report,source,project,manifest,map});
}
test('room detail receipt preserves assets and verifies six moving visual parents',()=> {
  const f=fixture();assert.deepEqual(validateRoomDetailReceipt(f),f.report.afterAssetHashes);
});
test('door source must retain visibility and countertop must not be hidden',()=> {
  for(const mutate of [f=>f.report.sourceRenderChanges.find(row=>row.sourceId===roomMotionIds[0]).after.visible=false,
    f=>f.report.sourceRenderChanges.find(row=>row.sourceId===roomMotionIds[0]).after.hiddenInGame=true,
    f=>f.report.sourceRenderChanges.find(row=>row.sourceId===roomMotionIds[0]).after.passFlags.render_in_depth_pass=true,
    f=>f.report.sourceRenderChanges[0].after.passFlags={render_in_main_pass:false,render_in_depth_pass:false},
    f=>f.report.sourceRenderChanges[0].sourceId='DOM_00740',f=>f.manifest.objects.find(row=>row.id==='RD_SINK_CORNER_1').hiddenSourceIds=['DOM_00740']]) {
    const f=fixture();mutate(f);assert.throws(()=>validateRoomDetailReceipt(f));
  }
});
test('detached, frozen or untested moving visuals are rejected',()=> {
  for(const mutate of [f=>f.report.savedGeometryReadback.find(row=>row.motionSourceId).attachParent='other',
    f=>f.report.savedGeometryReadback.find(row=>row.motionSourceId).mobility='Static',f=>f.report.parentMotionAudit.pop(),
    f=>f.report.parentMotionAudit[0].samples.pop(),f=>f.report.parentMotionAudit[0].closedPoseRestored=false]) {
    const f=fixture();mutate(f);assert.throws(()=>validateRoomDetailReceipt(f));
  }
});
test('motion evidence recomputes errors and rejects fabricated successful measurements',()=> {
  for(const mutate of [f=>f.report.parentMotionAudit[0].samples[0].maxBasisErrorCm=.01,
    f=>f.report.parentMotionAudit[0].samples[0].actualBasisPointsCm=[[1,0,0],[10,0,0],[0,10,0],[0,0,10]],
    f=>f.report.parentMotionAudit[0].samples[0].actualBasisPointsCm[0][0]=NaN]) {
    const f=fixture();mutate(f);assert.throws(()=>validateRoomDetailReceipt(f));
  }
});
test('historical materials, geometry and collision assets are immutable',()=> {
  for(const path of ['Brezi/Geometry/Washer.uasset','Brezi/Realism/Fixtures/Sink.uasset']) {
    const f=fixture();f.report.afterAssetHashes[f.project+'/Content/'+path]=newHash;assert.throws(()=>validateRoomDetailReceipt(f),/original asset/);
  }
});
test('room stage cannot add outside its namespace or rewrite source UV packages',()=> {
  for(const name of ['Brezi/Realism/Other/New.uasset','Brezi/Realism/RoomDetails/../Other/New.uasset','Brezi/Realism/RoomDetails/file.py']) {
    const f=fixture(),path=f.project+'/Content/'+name;f.report.afterAssetHashes[path]=newHash;f.report.newAssets.push(path);assert.throws(()=>validateRoomDetailReceipt(f),/namespace/);
  }
});
test('room bounds and save reload witnesses reject drift',()=> {
  for(const mutate of [f=>f.report.savedGeometryReadback[0].boundsCm={min:[0,-.1,0],max:[1,0,1]},
    f=>f.report.savedProtectedActorWitnessSha256=newHash,f=>f.report.savedActorWitnessSha256=oldHash]) {
    const f=fixture();mutate(f);assert.throws(()=>validateRoomDetailReceipt(f));
  }
});
