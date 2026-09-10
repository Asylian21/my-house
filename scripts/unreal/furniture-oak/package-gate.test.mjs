import test from 'node:test';
import assert from 'node:assert/strict';
import {validateFurnitureOakReceipt} from './package-gate.mjs';
// Synthetic report-shape tests only; these do not emulate or prove native APIs.
const hash='a'.repeat(64),prefix='/Game/Brezi/MaterialStudies/FurniturePhotoOak/V_aaaaaaaaaaaaaaaa',owner='scripts/unreal/furniture-oak/furniture_oak.py';
const groups={kitchen:{selectedIds:['DOM_00613','DOM_00643','DOM_00647','DOM_00650'],sourceSlot:'MAT_0039',sourceRoughness:.55,grain:'verticalZ',anchorCm:[759.1,-233.4,0],palette:[1.578107059115973,1.8456267412673573,2.0627853302568844]},dining:{selectedIds:['DOM_01328','DOM_01345','DOM_01354','DOM_01363','DOM_01372'],sourceSlot:'MAT_0080',sourceRoughness:.68,grain:'longitudinalX',anchorCm:[855,-448.1,70.8],palette:[1.4281032377635254,1.4204015551734712,1.3308024765112707]}};
function fixture(){
 const ids=Object.values(groups).flatMap(g=>g.selectedIds),scene={objSha256:hash,objects:ids.map(id=>({id,sourceId:'source-'+id,materialSlots:[groups.kitchen.selectedIds.includes(id)?'MAT_0039':'MAT_0080']}))};
 const r={status:'native-furniture-oak-saved-reload-validated',nativeApplied:true,activationStarted:true,rollbackRequired:false,rollbackAttempted:false,selectedIds:ids,protectedTVIds:['DOM_01293','DOM_01296','DOM_01300'],woodObjects:158,preservedWoodObjects:149,sourceManifestSha256:hash,sourceObjSha256:hash,geometryChanged:false,groups:structuredClone(groups),sourceRecordHashes:Object.fromEntries(ids.map(i=>[i,hash])),pipelineFiles:{},assetHashes:{},canonicalAssetHashes:{'unreal/BreziTwin/Content/Brezi/Geometry/source.uasset':hash},verification:{newAssetsSavedBeforeActivation:true,twoMapReloads:true,nativeGraphGetters:true,other149WoodBindingsUnchanged:true,existingTVBindingsAndMetadataUnchanged:true,sourceMeshUvCollisionAndAssetBytesUnchanged:true,sourceWebTexturesChanged:false},bindings:[],stagedMaterialProofs:{},savedReloadMaterialProofs:{}};
 for(const path of [owner,'scripts/unreal/furniture-oak/furniture_reference.py','scripts/unreal/furniture-oak/longitudinal-basis.hlsl','scripts/unreal/tv-oak/tv_oak.py','scripts/unreal/tv-oak/oak_reference.py','scripts/unreal/tv-oak/oak-basis.hlsl','output/unreal/furniture-detail-study/roof-surface-transfer-v3/candidate.json'])r.pipelineFiles[path]=hash;
 for(const [name,g]of Object.entries(groups)){
  const materialName=name==='kitchen'?'M_KitchenPhotoOak':'M_DiningPhotoOak',asset=`${prefix}/Materials/${materialName}.${materialName}`;
  const p={asset,profileOwner:owner,materialName,graphNodes:19,worldSpaceNormal:true,sourceUVDependency:false,naniteUsage:true,nativeScalarGetters:{period:183.00000429153442,baseRoughness:g.sourceRoughness,roughAmplitude:.12,roughMean:.5304041633418962,normalStrength:.25,metallic:0,specular:.5},nativeVectorGetters:{anchor:g.anchorCm,palette:g.palette},shaderSha256:{uv:hash,normal:hash,roughness:hash},textures:{}};
  for(const [role,suffix]of [['albedo','diff'],['normalMap','nor_gl'],['roughMap','rough']]){r.pipelineFiles[`output/unreal/wood-study/oak_veneer_01_${suffix}_4k.jpg`]=hash;p.textures[role]={asset:`${prefix}/Textures/T_${role}.T_${role}`,pixels:[4096,4096],sourceDimensionReadback:true,wrapXY:true,srgb:role==='albedo',greenFlipped:role==='normalMap',sourceSha256:hash};}
  r.stagedMaterialProofs[name]=structuredClone(p);r.savedReloadMaterialProofs[name]=structuredClone(p);
  r.bindings.push(...g.selectedIds.map(id=>({objectId:id,sourceId:'source-'+id,sourceSlot:g.sourceSlot,material:asset,savedReloadVerified:true,priorOverrides:[]})));
 }
 for(const name of ['Materials/M_KitchenPhotoOak','Materials/M_DiningPhotoOak','Textures/T_albedo','Textures/T_normalMap','Textures/T_roughMap'])r.assetHashes[prefix.replace('/Game/','unreal/BreziTwin/Content/')+'/'+name+'.uasset']=hash;
 return{scene,imported:{furnitureOak:r,sourceManifestSha256:hash,pipelineFiles:{...r.pipelineFiles},finalAssetHashes:{...r.assetHashes,...r.canonicalAssetHashes}}};
}
test('Synthetic complete two-reload receipt passes the exact package contract',()=>{const x=fixture();assert.equal(validateFurnitureOakReceipt(x.imported,x.scene).status,'native-furniture-oak-package-inputs-validated');});
const changes={
 'missing stage':x=>{delete x.imported.furnitureOak;},
 'extra oval binding':x=>{x.imported.furnitureOak.bindings[0].objectId='DOM_01326';},
 'lost TV preservation':x=>{x.imported.furnitureOak.verification.existingTVBindingsAndMetadataUnchanged=false;},
 'single reload':x=>{x.imported.furnitureOak.verification.twoMapReloads=false;},
 'source geometry changed':x=>{x.imported.furnitureOak.geometryChanged=true;},
 'source ID mismatch':x=>{x.scene.objects[0].sourceId='foreign';},
 'shared source slot mismatch':x=>{x.scene.objects[0].materialSlots=['MAT_0078'];},
 'kitchen reused TV palette':x=>{x.imported.furnitureOak.groups.kitchen.palette=groups.dining.palette;},
 'wrong dining grain':x=>{x.imported.furnitureOak.groups.dining.grain='verticalZ';},
 'wrong native roughness':x=>{x.imported.furnitureOak.savedReloadMaterialProofs.dining.nativeScalarGetters.baseRoughness=.74;},
 'incorrect native anchor':x=>{x.imported.furnitureOak.savedReloadMaterialProofs.kitchen.nativeVectorGetters.anchor[0]++;},
 'UV-based graph':x=>{x.imported.furnitureOak.savedReloadMaterialProofs.kitchen.sourceUVDependency=true;},
 'missing green flip':x=>{x.imported.furnitureOak.savedReloadMaterialProofs.dining.textures.normalMap.greenFlipped=false;},
 'unshared texture':x=>{x.imported.furnitureOak.savedReloadMaterialProofs.dining.textures.normalMap.asset+='foreign';},
 'changed saved shader':x=>{x.imported.furnitureOak.stagedMaterialProofs.dining.shaderSha256.uv='b'.repeat(64);},
 'missing recipe final hash':x=>{delete x.imported.pipelineFiles[owner];},
 'missing canonical asset final hash':x=>{delete x.imported.finalAssetHashes['unreal/BreziTwin/Content/Brezi/Geometry/source.uasset'];},
 'foreign generated package':x=>{x.imported.furnitureOak.assetHashes['foreign.uasset']=hash;},
 'unowned material':x=>{x.imported.furnitureOak.savedReloadMaterialProofs.dining.profileOwner='foreign';},
};
for(const [name,change]of Object.entries(changes))test('Reject '+name,()=>{const x=fixture();change(x);assert.throws(()=>validateFurnitureOakReceipt(x.imported,x.scene));});
