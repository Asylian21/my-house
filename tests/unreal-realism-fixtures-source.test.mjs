import test from 'node:test';
import assert from 'node:assert/strict';
import {validateFixtureReceipt,fixtureSourceIds} from '../scripts/unreal/realism-fixtures-source.mjs';

const oldHash='1'.repeat(64),newHash='2'.repeat(64);
function fixture() {
  const project='/project',content=project+'/Content',map=content+'/Brezi/Maps/Brezi.umap';
  const source={donor:'/donor',content:{[map]:oldHash,[content+'/Brezi/Geometry/Sink.uasset']:oldHash,
    [content+'/Brezi/Realism/Materials/M_Wall.uasset']:oldHash}};
  const bounds={min:[0,-.1,0],max:[.1,0,.1]},visualBoundsMm={min:[0,0,0],max:[1,1,1]};
  const selections=[['RF_SINK_BOWL',fixtureSourceIds.slice(0,5)],['RF_SINK_DRAIN',[fixtureSourceIds[5]]],
    ['RF_SINK_SPOUT',[fixtureSourceIds[6]]],['RF_SINK_LEVER',[fixtureSourceIds[7]]]];
  const manifest={owner:'scripts/unreal/realism-fixtures-geometry.py',status:'offline-geometry-validated',sourceIds:fixtureSourceIds,
    objects:selections.map(([id,sourceIds])=>({id,sourceIds,expectedWorldBoundsCm:bounds,visualBoundsMm,
      materialBindings:[{sourceId:fixtureSourceIds[0],sourceSlot:0}]}))};
  const objects=Object.fromEntries(selections.map(([id,sourceIds])=>[id,{actor:id,component:id+'.component',sourceIds,
    mesh:'/Game/Brezi/Realism/Fixtures/'+id+'.'+id,materials:['/Game/Steel.Steel']}])) ;
  const renderFlags=Object.fromEntries(['cast_shadow','cast_hidden_shadow','affect_distance_field_lighting',
    'affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden','visible_in_ray_tracing'].map(name=>[name,false]));
  const materialBindingChanges=[{actor:'sofa',component:'sofa.component',slot:0,before:'/Game/Cloth.Cloth',after:'/Game/Brezi/Realism/Fabric/M_Cloth.M_Cloth'}];
  const newAssets=selections.map(([id])=>content+'/Brezi/Realism/Fixtures/'+id+'.uasset');
  newAssets.push(content+'/Brezi/Realism/Fabric/M_Cloth.uasset');
  const report={schemaVersion:1,owner:'scripts/unreal/realism-fixtures-import.py',status:'realism-fixtures-validated',project,sourceOutput:source.donor,
    savedReloaded:true,protectedContentUnchanged:true,sourceGeometryCollisionAndTransformsPreserved:true,originalMaterialAssetsPreserved:true,materialBindingsAudited:true,
    sourceIds:fixtureSourceIds,objects,savedGeometryReadback:selections.map(([id])=>({id,actor:id,boundsCm:bounds,expectedBoundsCm:bounds,maxErrorCm:0,materials:objects[id].materials,collision:'NoCollision'})),
    maxNativeBoundsErrorCm:0,sourceRenderChanges:fixtureSourceIds.map(id=>({sourceId:id,actor:id,component:id+'.source',
      before:{visible:true,hiddenInGame:false,renderFlags},after:{visible:false,hiddenInGame:true,renderFlags}})),
    materialBindingChanges,fabric:{bindingChanges:materialBindingChanges},savedFabricReadback:{status:'verified'},
    originalActorCount:9,finalActorCount:13,addedActors:selections.map(([id])=>id),protectedActorWitnessSha256:oldHash,
    savedProtectedActorWitnessSha256:oldHash,authoredActorWitnessSha256:newHash,savedActorWitnessSha256:newHash,
    beforeAssetHashes:source.content,afterAssetHashes:{...source.content,[map]:newHash,...Object.fromEntries(newAssets.map(path=>[path,newHash]))},
    newAssets,changedAssets:[{path:map,beforeSha256:oldHash,afterSha256:newHash}]};
  return {report,source,project,manifest,map};
}
test('four saved fixture meshes and bounded fabric changes preserve the inherited content contract',()=>{
  const f=fixture();assert.deepEqual(validateFixtureReceipt(f),f.report.afterAssetHashes);
});
test('fixture receipt rejects hiding any source outside the exact sink/faucet cohort',()=>{
  for(const mutate of [r=>r.sourceRenderChanges[0].sourceId='DOM_00001',r=>r.sourceRenderChanges.pop(),
    r=>r.sourceRenderChanges[0].component=r.sourceRenderChanges[1].component]) {
    const f=fixture();mutate(f.report);assert.throws(()=>validateFixtureReceipt(f));
  }
});
test('fixture receipt rejects native bounds drift, wrong axis and fabricated error metrics',()=>{
  for(const mutate of [f=>f.report.savedGeometryReadback[0].boundsCm={min:[0,-.1,0],max:[.2,0,.1]},
    f=>f.manifest.objects[0].visualBoundsMm={min:[0,0,0],max:[1,2,1]},f=>f.report.savedGeometryReadback[0].maxErrorCm=.001]) {
    const f=fixture();mutate(f);assert.throws(()=>validateFixtureReceipt(f),/bounds|conversion|error/);
  }
});
test('fixture stage cannot rewrite meshes, earlier realism materials or remove inherited data',()=>{
  for(const path of ['Brezi/Geometry/Sink.uasset','Brezi/Realism/Materials/M_Wall.uasset']) {
    const f=fixture();f.report.afterAssetHashes[f.project+'/Content/'+path]=newHash;
    assert.throws(()=>validateFixtureReceipt(f),/original asset/);
  }
  const f=fixture();delete f.report.afterAssetHashes[f.project+'/Content/Brezi/Geometry/Sink.uasset'];
  assert.throws(()=>validateFixtureReceipt(f),/original asset/);
});
test('new fixture/fabric assets cannot escape their narrow namespaces',()=>{
  for(const name of ['Brezi/Realism/Other/New.uasset','Brezi/Realism/Fixtures/../Other/New.uasset','Brezi/Realism/Fabric/script.py']) {
    const f=fixture(),path=f.project+'/Content/'+name;f.report.afterAssetHashes[path]=newHash;f.report.newAssets.push(path);
    assert.throws(()=>validateFixtureReceipt(f),/namespace/);
  }
});
test('saved source flags disable every contribution and fabric delta must be audited',()=>{
  for(const mutate of [r=>r.sourceRenderChanges[0].after.renderFlags.cast_shadow=true,r=>r.savedProtectedActorWitnessSha256=newHash,
    r=>r.fabric={bindingChanges:[]},r=>r.materialBindingChanges[0].after='/Game/Source.Source',r=>r.savedFabricReadback=null]) {
    const f=fixture();mutate(f.report);assert.throws(()=>validateFixtureReceipt(f));
  }
});
