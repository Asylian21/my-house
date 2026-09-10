// Pure proof gate; no native API, process or asset mutation.
const groups={kitchen:{ids:['DOM_00613','DOM_00643','DOM_00647','DOM_00650'],slot:'MAT_0039',rough:.55,grain:'verticalZ',name:'M_KitchenPhotoOak',palette:[1.578107059115973,1.8456267412673573,2.0627853302568844]},
  dining:{ids:['DOM_01328','DOM_01345','DOM_01354','DOM_01363','DOM_01372'],slot:'MAT_0080',rough:.68,grain:'longitudinalX',name:'M_DiningPhotoOak',palette:[1.4281032377635254,1.4204015551734712,1.3308024765112707]}};
const ids=Object.values(groups).flatMap(g=>g.ids).sort(),owner='scripts/unreal/furniture-oak/furniture_oak.py';
const digest=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x),near=(a,b,e)=>Number.isFinite(a)&&Math.abs(a-b)<=e;
const sameIds=(a,b)=>Array.isArray(a)&&a.length===b.length&&[...a].sort().every((x,i)=>x===[...b].sort()[i]);
const need=(v,m)=>{if(!v)throw Error('Furniture oak package gate: '+m);};
export function validateFurnitureOakReceipt(imported,scene){
  const r=imported?.furnitureOak;
  need(r?.status==='native-furniture-oak-saved-reload-validated'&&r.nativeApplied===true&&r.activationStarted===true&&r.rollbackRequired===false&&r.rollbackAttempted===false,'missing saved native activation');
  need(sameIds(r.selectedIds,ids)&&r.woodObjects===158&&r.preservedWoodObjects===149&&sameIds(r.protectedTVIds,['DOM_01293','DOM_01296','DOM_01300']),'exact nine-object scope differs');
  need(digest(r.sourceManifestSha256)&&r.sourceManifestSha256===imported.sourceManifestSha256&&digest(r.sourceObjSha256)&&r.sourceObjSha256===scene?.objSha256,'source hashes differ');
  for(const flag of ['newAssetsSavedBeforeActivation','twoMapReloads','nativeGraphGetters','other149WoodBindingsUnchanged','existingTVBindingsAndMetadataUnchanged','sourceMeshUvCollisionAndAssetBytesUnchanged'])need(r.verification?.[flag]===true,'missing '+flag);
  need(r.geometryChanged===false&&r.verification?.sourceWebTexturesChanged===false,'source mutation reported');
  need(sameIds(r.bindings?.map(b=>b.objectId),ids),'saved binding exception list differs');
  need(sameIds(Object.keys(r.groups??{}),Object.keys(groups))&&sameIds(Object.keys(r.stagedMaterialProofs??{}),Object.keys(groups))&&sameIds(Object.keys(r.savedReloadMaterialProofs??{}),Object.keys(groups)),'two material groups required');
  let prefix=null;const texturePaths={};
  for(const [name,g] of Object.entries(groups)){
    const recipe=r.groups[name],saved=r.savedReloadMaterialProofs[name];
    need(sameIds(recipe.selectedIds,g.ids)&&recipe.sourceSlot===g.slot&&recipe.sourceRoughness===g.rough&&recipe.grain===g.grain&&recipe.palette?.length===3&&recipe.palette.every((v,i)=>near(v,g.palette[i],1e-12)),'authored material recipe differs: '+name);
    need(typeof saved.asset==='string'&&new RegExp('^/Game/Brezi/MaterialStudies/FurniturePhotoOak/V_[a-f0-9]{16}/Materials/'+g.name+'\\.'+g.name+'$').test(saved.asset),'foreign material asset');
    const current=saved.asset.split('/Materials/')[0];need(prefix===null||prefix===current,'materials do not share an owned version');prefix=current;
    for(const proof of [r.stagedMaterialProofs[name],saved]){
      need(proof.asset===saved.asset&&proof.profileOwner===owner&&proof.materialName===g.name&&proof.graphNodes===19&&proof.worldSpaceNormal===true&&proof.sourceUVDependency===false&&proof.naniteUsage===true,'incomplete native graph proof');
      for(const [key,value] of Object.entries({period:183.00000429153442,baseRoughness:g.rough,roughAmplitude:.12,roughMean:.5304041633418962,normalStrength:.25,metallic:0,specular:.5}))need(near(proof.nativeScalarGetters?.[key],value,1e-5),'native scalar differs: '+key);
      for(const [key,values] of Object.entries({palette:g.palette,anchor:recipe.anchorCm}))need(Array.isArray(values)&&values.length===3&&proof.nativeVectorGetters?.[key]?.length===3&&values.every((v,i)=>near(proof.nativeVectorGetters[key][i],v,1e-4)),'native vector differs: '+key);
      for(const key of ['uv','normal','roughness'])need(digest(proof.shaderSha256?.[key])&&proof.shaderSha256[key]===saved.shaderSha256[key],'saved shader changed');
      for(const [role,suffix] of [['albedo','diff'],['normalMap','nor_gl'],['roughMap','rough']]){
        const t=proof.textures?.[role],source=`output/unreal/wood-study/oak_veneer_01_${suffix}_4k.jpg`;
        need(t?.pixels?.length===2&&t.pixels.every(x=>x===4096)&&t.sourceDimensionReadback===true&&t.wrapXY===true&&t.srgb===(role==='albedo')&&t.greenFlipped===(role==='normalMap')&&digest(t.sourceSha256)&&t.sourceSha256===r.pipelineFiles?.[source],'texture provenance differs');
        need(t.asset===`${prefix}/Textures/T_${role}.T_${role}`&&(!texturePaths[role]||texturePaths[role]===t.asset),'texture triplet is not shared');texturePaths[role]=t.asset;
      }
    }
    for(const id of g.ids){const b=r.bindings.find(x=>x.objectId===id),records=scene.objects.filter(o=>o.id===id);need(records.length===1&&b.sourceId===records[0].sourceId&&sameIds(records[0].materialSlots,[g.slot])&&b.sourceSlot===g.slot&&b.material===saved.asset&&b.savedReloadVerified===true&&Array.isArray(b.priorOverrides)&&digest(r.sourceRecordHashes?.[id]),'exact source binding differs: '+id);}
  }
  const recipes=[owner,'scripts/unreal/furniture-oak/furniture_reference.py','scripts/unreal/furniture-oak/longitudinal-basis.hlsl','scripts/unreal/tv-oak/tv_oak.py','scripts/unreal/tv-oak/oak_reference.py','scripts/unreal/tv-oak/oak-basis.hlsl','output/unreal/furniture-detail-study/roof-surface-transfer-v3/candidate.json'];
  need(recipes.every(p=>digest(r.pipelineFiles?.[p])),'missing recipe hashes');
  for(const [p,h]of Object.entries(r.pipelineFiles))need(digest(h)&&imported.pipelineFiles?.[p]===h,'recipe omitted from final import');
  const assetPrefix=prefix.replace('/Game/','unreal/BreziTwin/Content/')+'/';
  const expected=['Materials/M_KitchenPhotoOak','Materials/M_DiningPhotoOak','Textures/T_albedo','Textures/T_normalMap','Textures/T_roughMap'].map(p=>assetPrefix+p+'.uasset');
  need(sameIds(Object.keys(r.assetHashes??{}),expected),'exact five generated packages required');
  for(const [p,h]of Object.entries(r.assetHashes))need(digest(h)&&imported.finalAssetHashes?.[p]===h,'candidate asset omitted from final import');
  need(Object.keys(r.canonicalAssetHashes??{}).length>0,'missing preserved source hashes');
  for(const [p,h]of Object.entries(r.canonicalAssetHashes))need(digest(h)&&imported.finalAssetHashes?.[p]===h,'preserved asset differs');
  return{status:'native-furniture-oak-package-inputs-validated',selectedIds:[...ids]};
}
