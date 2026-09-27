import test from 'node:test';
import assert from 'node:assert/strict';
import {validateFurnitureReceipt,furnitureSourceIds,grainSourceIds} from '../scripts/unreal/realism-furniture-source.mjs';
const oldHash='1'.repeat(64),newHash='2'.repeat(64);
function fixture() {
  const project='/project',content=project+'/Content',map=content+'/Brezi/Maps/Brezi.umap';
  const source={donor:'/donor',content:{[map]:oldHash,[content+'/Brezi/Geometry/Sofa.uasset']:oldHash,[content+'/Brezi/Realism/RoomDetails/Door.uasset']:oldHash}};
  const bounds={min:[0,-.1,0],max:[.1,0,.1]},visualBoundsMm={min:[0,0,0],max:[1,1,1]};
  const rows=furnitureSourceIds.map(sourceId=>({id:'RU_'+sourceId,sourceIds:[sourceId],hiddenSourceIds:[],hiddenVisualSourceIds:['PH_'+sourceId],
    expectedWorldBoundsCm:bounds,visualBoundsMm,materialBindings:[{sourceId,sourceSlot:0,visualSourceId:'PH_'+sourceId}]}));
  const hiddenVisualSourceIds=furnitureSourceIds.map(id=>'PH_'+id);
  const manifest={owner:'scripts/unreal/realism-upholstery-geometry.py',status:'offline-geometry-validated',sourceIds:furnitureSourceIds,
    hiddenSourceIds:[],hiddenVisualSourceIds,objects:rows};
  const objects=Object.fromEntries(rows.map(row=>[row.id,{actor:row.id,component:row.id+'.component',sourceIds:row.sourceIds,
    mesh:'/Game/Brezi/Realism/Furniture/Geometry/'+row.id+'.'+row.id,materials:['/Game/Cloth.Cloth']}])) ;
  const renderFlags=Object.fromEntries(['cast_shadow','cast_hidden_shadow','affect_distance_field_lighting',
    'affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden','visible_in_ray_tracing'].map(name=>[name,false]));
  const axes=['X','Y'],ownedAssets=axes.map(axis=>'/Game/Brezi/Realism/Furniture/Materials/Oak'+axis+'.Oak'+axis);
  const materialBindingChanges=grainSourceIds.map(sourceId=> {
    const axis=['DOM_01460','DOM_01461'].includes(sourceId)?'X':'Y';
    return {sourceId,axis,actor:'PH_'+sourceId,component:'PH_'+sourceId+'.component',slot:0,before:'/Game/OldOak.OldOak',after:ownedAssets[axes.indexOf(axis)]};
  });
  const newAssets=rows.map(row=>content+'/Brezi/Realism/Furniture/Geometry/'+row.id+'.uasset').concat(axes.map(axis=>content+'/Brezi/Realism/Furniture/Materials/Oak'+axis+'.uasset'));
  const materials=Object.fromEntries(ownedAssets.map((path,index)=>[path,{axis:axes[index],graph:{nodes:[],roots:{}}}]));
  const originalGraphs={'/Game/OldOak.OldOak':{nodes:[],roots:{}}};
  const report={schemaVersion:1,owner:'scripts/unreal/realism-furniture-import.py',status:'realism-furniture-validated',project,sourceOutput:source.donor,
    savedReloaded:true,protectedContentUnchanged:true,sourceGeometryCollisionAndTransformsPreserved:true,originalMaterialAssetsPreserved:true,materialBindingsAudited:true,
    sourceIds:furnitureSourceIds,hiddenSourceIds:[],hiddenVisualSourceIds,objects,
    savedGeometryReadback:rows.map(row=>({id:row.id,actor:row.id,boundsCm:bounds,expectedBoundsCm:bounds,maxErrorCm:0,materials:objects[row.id].materials,collision:'NoCollision'})),
    maxNativeBoundsErrorCm:0,sourceRenderChanges:furnitureSourceIds.map(id=>({sourceId:id,visualSourceId:'PH_'+id,actor:'PH_'+id,component:'PH_'+id+'.component',
      before:{visible:true,hiddenInGame:false,renderFlags},after:{visible:false,hiddenInGame:true,renderFlags}})),
    materialBindingChanges,grain:{bindingChanges:materialBindingChanges,ownedAssets,materials,originalGraphs,protectedGraphs:originalGraphs,originalBindingCount:110,protectedBindingCount:99,axisCounts:{X:2,Y:9}},
    savedGrainReadback:{status:'grain-materials-saved-verified',materials,bindingCount:11,protectedBindingCount:99},
    originalActorCount:100,finalActorCount:120,addedActors:rows.map(row=>row.id),protectedActorWitnessSha256:oldHash,
    savedProtectedActorWitnessSha256:oldHash,authoredActorWitnessSha256:newHash,savedActorWitnessSha256:newHash,
    beforeAssetHashes:source.content,afterAssetHashes:{...source.content,[map]:newHash,...Object.fromEntries(newAssets.map(path=>[path,newHash]))},
    newAssets,changedAssets:[{path:map,beforeSha256:oldHash,afterSha256:newHash}]};
  return structuredClone({report,source,project,manifest,map});
}
test('Furniture accepts20 PH visual replacements and11 exact grain overrides',()=> {
  const f=fixture();assert.deepEqual(validateFurnitureReceipt(f),f.report.afterAssetHashes);
});
test('original source furniture or unrelated PH components cannot be hidden',()=> {
  for(const mutate of [f=>f.report.hiddenSourceIds=['DOM_01443'],f=>f.report.sourceRenderChanges[0].visualSourceId='DOM_01443',
    f=>f.report.sourceRenderChanges[0].sourceId='DOM_00100',f=>f.manifest.objects[0].hiddenSourceIds=['DOM_01443']]) {
    const f=fixture();mutate(f);assert.throws(()=>validateFurnitureReceipt(f));
  }
});
test('grain correction rejects kitchen cohort, arbitraryaxes and extra material clones',()=> {
  for(const mutate of [f=>f.report.materialBindingChanges[0].sourceId='DOM_00644',f=>f.report.materialBindingChanges[0].axis='X',
    f=>f.report.materialBindingChanges[0].after='/Game/Brezi/Realism/Furniture/Materials/Third.Third',
    f=>f.report.grain.ownedAssets.push('/Game/Third.Third')]) {
    const f=fixture();mutate(f);assert.throws(()=>validateFurnitureReceipt(f));
  }
});
test('material binding source must reference the active PH upholstery slot',()=> {
  for(const mutate of [f=>f.manifest.objects[0].materialBindings[0].visualSourceId='DOM_01443',
    f=>f.manifest.objects[0].materialBindings[0].sourceSlot=1,f=>f.report.savedGeometryReadback[0].materials=['foreign']]) {
    const f=fixture();mutate(f);assert.throws(()=>validateFurnitureReceipt(f));
  }
});
test('R4 door asset bytes and original source geometry remain immutable',()=> {
  for(const path of ['Brezi/Geometry/Sofa.uasset','Brezi/Realism/RoomDetails/Door.uasset']) {
    const f=fixture();f.report.afterAssetHashes[f.project+'/Content/'+path]=newHash;assert.throws(()=>validateFurnitureReceipt(f),/original asset/);
  }
});
test('only Furniture packages can be added',()=> {
  for(const name of ['Brezi/Realism/Other/New.uasset','Brezi/Realism/Furniture/../Other/New.uasset','Brezi/Realism/Furniture/file.py']) {
    const f=fixture(),path=f.project+'/Content/'+name;f.report.afterAssetHashes[path]=newHash;f.report.newAssets.push(path);assert.throws(()=>validateFurnitureReceipt(f),/namespace/);
  }
});
test('saved bounds, lighting flags and original witnesses remain verified',()=> {
  for(const mutate of [f=>f.report.savedGeometryReadback[0].boundsCm={min:[0,-.1,0],max:[1,0,1]},
    f=>f.report.savedProtectedActorWitnessSha256=newHash,f=>f.report.sourceRenderChanges[0].after.renderFlags.cast_shadow=true,
    f=>f.report.savedGrainReadback=null]) {
    const f=fixture();mutate(f);assert.throws(()=>validateFurnitureReceipt(f));
  }
});
