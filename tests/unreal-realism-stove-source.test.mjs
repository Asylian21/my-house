import test from 'node:test';
import assert from 'node:assert/strict';
import {validateStoveReceipt,stoveSourceIds} from '../scripts/unreal/realism-stove-source.mjs';
const oldHash='1'.repeat(64),newHash='2'.repeat(64);
function fixture() {
  const project='/project',content=project+'/Content',map=content+'/Brezi/Maps/Brezi.umap';
  const source={donor:'/donor',content:{[map]:oldHash,[content+'/Brezi/Geometry/Stove.uasset']:oldHash,
    [content+'/Brezi/Realism/RoomDetails/Door.uasset']:oldHash,[content+'/Brezi/Realism/Furniture/Materials/OakY.uasset']:oldHash}};
  const bounds={min:[0,-.1,0],max:[.1,0,.1]},visualBoundsMm={min:[0,0,0],max:[1,1,1]};
  const roles={shell:['DOM_00553'],chamber:['DOM_00553'],logs:['DOM_00562','DOM_00563'],flames:['DOM_00564','DOM_00565','DOM_00566'],embers:['DOM_00556']};
  const roleMaterials=Object.fromEntries(Object.keys(roles).map(role=>[role,role==='shell'?'/Game/Source/Shell.Shell':'/Game/Brezi/Realism/Stove/Materials/'+role+'.'+role]));
  const rows=Object.entries(roles).map(([role,sourceIds])=>({id:'RFIRE_'+role.toUpperCase(),role,materialRole:role,sourceIds,expectedWorldBoundsCm:bounds,visualBoundsMm}));
  const manifest={owner:'scripts/unreal/realism-stove-geometry.py',status:'offline-study-geometry-validated',sourceIds:stoveSourceIds,hiddenSourceIds:stoveSourceIds,objects:rows};
  const objects=Object.fromEntries(rows.map(row=>[row.id,{actor:row.id,component:row.id+'.component',sourceIds:row.sourceIds,materialRole:row.materialRole,
    mesh:'/Game/Brezi/Realism/Stove/Geometry/'+row.id+'.'+row.id,materials:[roleMaterials[row.role]]}]));
  const renderFlags=Object.fromEntries(['cast_shadow','cast_hidden_shadow','affect_distance_field_lighting','affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden','visible_in_ray_tracing'].map(name=>[name,false]));
  const ownedAssets=Object.entries(roleMaterials).filter(([role])=>role!=='shell').map(([,path])=>path);
  const textureHashes={T_Fire_SubUV:'865a10d77419a7a5c80a89abbf2a738168cd79bfad1aab1397d3d5802ac6f33c',T_Fire_Tiled_D:'5fddf6ab9c5a32516248bdfce3cc9f2426a3b734d57f2c5bd1d26a93c6381252'};
  const textures=Object.fromEntries(Object.entries(textureHashes).map(([name,hash])=>[name,{sha256:hash,dependencies:[],nativeSize:name==='T_Fire_SubUV'?[1024,1024]:[512,512],properties:{srgb:true},
    ownedPackage:'/Game/Brezi/Realism/Stove/Fire/Textures/'+name,copiedFile:content+'/Brezi/Realism/Stove/Fire/Textures/'+name+'.uasset',installedSource:'/EngineAssets/'+name+'.uasset'}]));
  const textureReadback=Object.fromEntries(Object.entries(textures).map(([name,row])=>[name,{sha256:row.sha256,dependencies:[],nativeSize:row.nativeSize,properties:row.properties,asset:row.ownedPackage+'.'+name}]));
  const newAssets=rows.map(row=>content+'/Brezi/Realism/Stove/Geometry/'+row.id+'.uasset')
    .concat(ownedAssets.map(path=>content+path.replace('/Game','').split('.')[0]+'.uasset')).concat(Object.values(textures).map(row=>row.copiedFile));
  const originalGraphs={'/Game/Source/Shell.Shell':{nodes:[],roots:{}}};
  const sourceBindings=Object.fromEntries(Array.from({length:19},(_,i)=>{const id='DOM_'+String(553+i).padStart(5,'0');return[id,{actor:id,component:id+'.component',material:roleMaterials.shell}];}));
  const materials={materials:roleMaterials,bindingChanges:[],ownedAssets,originalGraphs,protectedGraphs:originalGraphs,sourceBindings,
    graphs:Object.fromEntries(ownedAssets.map(path=>[path,{nodes:[],roots:{}}])),recipe:{},surfaces:{},textures:{}};
  const report={schemaVersion:1,owner:'scripts/unreal/realism-stove-import.py',status:'realism-stove-validated',project,sourceOutput:source.donor,
    savedReloaded:true,protectedContentUnchanged:true,sourceGeometryCollisionAndTransformsPreserved:true,originalMaterialAssetsPreserved:true,materialBindingsAudited:true,originalLightingPreserved:true,
    experimentalRuntimePluginsEnabled:false,sourceIds:stoveSourceIds,hiddenSourceIds:stoveSourceIds,objects,
    savedGeometryReadback:rows.map(row=>({id:row.id,actor:row.id,boundsCm:bounds,expectedBoundsCm:bounds,maxErrorCm:0,materials:objects[row.id].materials,collision:'NoCollision'})),
    maxNativeBoundsErrorCm:0,sourceRenderChanges:stoveSourceIds.map(id=>({sourceId:id,actor:id,component:id+'.component',
      before:{visible:true,hiddenInGame:false,renderFlags},after:{visible:false,hiddenInGame:true,renderFlags}})),
    materials,savedMaterialReadback:{...materials,status:'saved-reloaded-validated',savedReloaded:true},
    textures,savedTextureReadback:textureReadback,authoredTextureReadback:textureReadback,
    originalActorCount:100,finalActorCount:105,addedActors:rows.map(row=>row.id),protectedActorWitnessSha256:oldHash,
    savedProtectedActorWitnessSha256:oldHash,authoredActorWitnessSha256:newHash,savedActorWitnessSha256:newHash,
    inputFiles:Object.fromEntries(Object.values(textures).map(row=>[row.installedSource,row.sha256])),beforeAssetHashes:source.content,
    afterAssetHashes:{...source.content,[map]:newHash,...Object.fromEntries(newAssets.map(path=>[path,newHash])),...Object.fromEntries(Object.values(textures).map(row=>[row.copiedFile,row.sha256]))},
    newAssets,changedAssets:[{path:map,beforeSha256:oldHash,afterSha256:newHash}]};
  return structuredClone({report,source,project,manifest,map});
}
test('Stove accepts five visuals, seven exact visibility deltas and two independent textures',()=> {
  const f=fixture();assert.deepEqual(validateStoveReceipt(f),f.report.afterAssetHashes);
});
test('glass, shell finish, original bindings and light state cannot be changed',()=> {
  for(const mutate of [f=>f.report.sourceRenderChanges[0].sourceId='DOM_00557',f=>f.report.originalLightingPreserved=false,
    f=>f.report.materials.ownedAssets.push(f.report.materials.materials.shell),f=>f.report.materials.bindingChanges=[{actor:'stove'}]]) {
    const f=fixture();mutate(f);assert.throws(()=>validateStoveReceipt(f));
  }
});
test('material role and source membership cannot be reassigned',()=> {
  for(const mutate of [f=>f.manifest.objects[0].sourceIds=['DOM_00557'],f=>f.report.objects.RFIRE_FLAMES.materialRole='logs',
    f=>f.report.savedGeometryReadback[0].materials=['foreign'],f=>f.report.materials.materials.flames='/Game/Foreign.Foreign']) {
    const f=fixture();mutate(f);assert.throws(()=>validateStoveReceipt(f));
  }
});
test('runtime sample plugins, dependent textures and mutated installed texture bytes are rejected',()=> {
  for(const mutate of [f=>f.report.experimentalRuntimePluginsEnabled=true,f=>f.report.textures.T_Fire_SubUV.dependencies=['/Script/NetworkPredictionExtras'],
    f=>f.report.savedTextureReadback.T_Fire_SubUV.nativeSize=[128,128],f=>f.report.inputFiles[f.report.textures.T_Fire_SubUV.installedSource]=newHash,
    f=>f.report.afterAssetHashes[f.report.textures.T_Fire_SubUV.copiedFile]=newHash]) {
    const f=fixture();mutate(f);assert.throws(()=>validateStoveReceipt(f));
  }
});
test('old collision mesh, R4 door and R5 material bytes remain protected',()=> {
  for(const path of ['Brezi/Geometry/Stove.uasset','Brezi/Realism/RoomDetails/Door.uasset','Brezi/Realism/Furniture/Materials/OakY.uasset']) {
    const f=fixture();f.report.afterAssetHashes[f.project+'/Content/'+path]=newHash;assert.throws(()=>validateStoveReceipt(f),/original asset/);
  }
});
test('only owned Stove package additions with saved bounds/witness evidence are accepted',()=> {
  for(const mutate of [f=>{const path='/project/Content/Elsewhere/Bad.uasset';f.report.newAssets.push(path);f.report.afterAssetHashes[path]=newHash;},
    f=>f.report.savedGeometryReadback[0].boundsCm={min:[0,0,0],max:[1,1,1]},f=>f.report.savedProtectedActorWitnessSha256=newHash,
    f=>f.report.sourceRenderChanges[0].after.renderFlags.cast_shadow=true,f=>f.report.savedMaterialReadback=null]) {
    const f=fixture();mutate(f);assert.throws(()=>validateStoveReceipt(f));
  }
});
