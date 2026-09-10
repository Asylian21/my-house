// Synthetic receipt tests: never native graph, GPU or packaged visual evidence.
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {expectedLawnGroundInputs,validateLawnGroundReceipt} from './package-gate.mjs';
const hash=x=>createHash('sha256').update(x).digest('hex');
const expected=expectedLawnGroundInputs();
const mesh='/Game/Brezi/Geometry/brezi-twin/StaticMeshes/DOM_00001.DOM_00001';
const base='/Game/Brezi/MaterialsGenerated/M_MAT_0001.M_MAT_0001';
function fixture() {
 const recipe={reference:structuredClone(expected.reference),recipeInputs:structuredClone(expected.recipeInputs)};
 const recipeCanonicalJson=JSON.stringify(recipe),recipeSha256=hash(recipeCanonicalJson);
 const prefix=`/Game/Brezi/LawnGround/R_${recipeSha256.slice(0,16)}`,assetPrefix=`unreal/BreziTwin/Content/Brezi/LawnGround/R_${recipeSha256.slice(0,16)}/`;
 const material=prefix+'/Materials/M_LawnGround.M_LawnGround';
 const sourceProof={triangles:27,windingMultiplicityVerified:true,sourceToleranceMm:.002,uv0Tolerance:.000002,maximumPositionErrorMm:.001,maximumUv0Error:1e-8,snapshotSha256:hash('synthetic source snapshot')};
 const selectedBefore={mesh,meshMaterial:base,actor:'synthetic actor',component:'synthetic mesh component',state:'source',effectiveMaterial:base,overrides:[],nativeSnapshot:{syntheticOnly:true},sourceProof};
 const selectedAfter={...selectedBefore,state:'active',effectiveMaterial:material,overrides:[material]};
 const roles={albedo:'Diffuse',normalMap:'nor_gl',roughMap:'Rough'};
 const textures=Object.fromEntries(Object.entries(roles).map(([r,s])=>[r,{asset:`${prefix}/Textures/T_${r}.T_${r}`,sourceSha256:expected.reference.maps[s].sha256,pixels:[4096,4096],srgb:r==='albedo',greenFlipped:r==='normalMap',wrapXY:true,sourceDimensionReadback:true}]));
 const graph={asset:material,recipeSha256,nodeCount:24,linkCount:48,exactGraphVerified:true,textureSampleCount:9,phaseCount:3,allGraphInputsAccountedFor:true,stockAutomaticViewMipBias:true,samplerSource:'SSM_FROM_TEXTURE_ASSET',sameWeightsAndOffsetsAllMaps:true,continuousUvGradients:true,tangentSpaceNormal:true,normalRotationApplied:false,normalStrength:1,roughnessInputMapLinear:true,roughnessInputInvertGammaOrSquare:false,roughnessRemapApplied:true,effectiveRoughness:structuredClone(expected.reference.material.roughness),artistTintLinear:[1,1,1],naniteUsage:true,pixelDepthOffsetConnected:false,worldPositionOffsetConnected:false,textures};
 const roundtrip={mapSaved:true,worldUnloaded:true,mapReloaded:true,allFourOwnedAssetsAbsentBeforeReload:true};
 const verification=Object.fromEntries(['nativeSourceVerticesUv0Compared','geometryUvCollisionAndSourceAssetsUnchanged','other1877SourceActorsUnchanged','allGrassInstancesAndPolicyUnchanged','sourceBaseMaterialRetained','twoMapReloads','twoOwnedAssetUnloadAbsenceReadbacks','exactSavedGraphsEqual','activeBindingVerified'].map(k=>[k,true]));
 const assetHashes=Object.fromEntries([`${assetPrefix}Materials/M_LawnGround.uasset`,...Object.keys(roles).map(r=>`${assetPrefix}Textures/T_${r}.uasset`)].map(p=>[p,hash(p)]));
 const protectedAssetHashes=Object.fromEntries(Array.from({length:1878},(_,i)=>[`unreal/BreziTwin/Content/Brezi/SyntheticTests/DOM_${i}.uasset`,hash(String(i))]));
 const lawnGround={status:'lawn-ground-saved-reload-validated',nativeApplied:true,restoring:false,recipeSha256,recipeCanonicalJson,recipe,pipelineFiles:structuredClone(expected.pipeline),sourceObjectId:'DOM_00001',sourceMaterialSlot:'MAT_0001',sourceManifestSha256:expected.reference.sceneSha256,sourceObjSha256:expected.reference.objSha256,actorMetadataWritten:false,grassInstanceCount:33769,stagedReload:{...roundtrip},activeReload:{...roundtrip},verification,selectedBefore,selectedAfter,stagedMaterialProof:structuredClone(graph),activeMaterialProof:structuredClone(graph),assetHashes,protectedAssetHashes,sourcePreservationSnapshotSha256:hash('synthetic preservation')};
 return {sourceManifestSha256:expected.reference.sceneSha256,pipelineFiles:structuredClone(expected.pipeline),lawnDetail:{instanceCount:33769},finalAssetHashes:{...assetHashes,...protectedAssetHashes},lawnGround};
}
test('closed synthetic receipt accepted with explicit rendered false',()=>{
 const value=validateLawnGroundReceipt(fixture(),expected);assert.equal(value.status,'lawn-ground-package-inputs-validated');assert.equal(value.renderedVerified,false);
});
const cases={
 'missing stage':x=>delete x.lawnGround,
 'failure status':x=>x.lawnGround.status='failed',
 'unapplied':x=>x.lawnGround.nativeApplied=false,
 'restoration intermediate':x=>x.lawnGround.restoring=true,
 'source object':x=>x.lawnGround.sourceObjectId='DOM_00002',
 'source slot':x=>x.lawnGround.sourceMaterialSlot='MAT_0002',
 'source scene':x=>x.sourceManifestSha256=hash('changed'),
 'source OBJ':x=>x.lawnGround.sourceObjSha256=hash('changed'),
 'recipe content':x=>x.lawnGround.recipe.reference.material.normalStrength=.4,
 'recipe bytes':x=>x.lawnGround.recipeCanonicalJson+=' ',
 'pipeline omission':x=>delete x.lawnGround.pipelineFiles['scripts/unreal/materials.py'],
 'pipeline final omission':x=>delete x.pipelineFiles['scripts/unreal/materials.py'],
 'first real absence':x=>x.lawnGround.stagedReload.allFourOwnedAssetsAbsentBeforeReload=false,
 'second reload':x=>x.lawnGround.activeReload.mapReloaded=false,
 'source vertices':x=>x.lawnGround.verification.nativeSourceVerticesUv0Compared=false,
 'grass changed':x=>x.lawnGround.grassInstanceCount++,
 'grass stage mismatch':x=>x.lawnDetail.instanceCount--,
 'actor metadata written':x=>x.lawnGround.actorMetadataWritten=true,
 'mesh identity':x=>x.lawnGround.selectedAfter.mesh=mesh+'foreign',
 'source mesh material':x=>x.lawnGround.selectedAfter.meshMaterial=base+'foreign',
 'foreign prior override':x=>x.lawnGround.selectedBefore.overrides=['/Game/Foreign'],
 'foreign effective':x=>x.lawnGround.selectedAfter.effectiveMaterial=base,
 'foreign override array':x=>x.lawnGround.selectedAfter.overrides.push(base),
 'selected actor differs':x=>x.lawnGround.selectedAfter.actor='other',
 'geometry snapshot changed':x=>x.lawnGround.selectedAfter.nativeSnapshot={changed:true},
 'source count':x=>{x.lawnGround.selectedBefore.sourceProof.triangles=28;},
 'source error NaN':x=>x.lawnGround.selectedBefore.sourceProof.maximumPositionErrorMm=NaN,
 'source error too large':x=>x.lawnGround.selectedBefore.sourceProof.maximumPositionErrorMm=.00201,
 'unmatched saved graph':x=>x.lawnGround.activeMaterialProof.nodeCount=23,
 'unrelated owned asset namespace':x=>x.lawnGround.assetHashes['unreal/BreziTwin/Content/Brezi/Other.uasset']=hash('x'),
 'missing protected source bytes':x=>delete x.finalAssetHashes[Object.keys(x.lawnGround.protectedAssetHashes)[0]],
 'changed owned bytes':x=>x.finalAssetHashes[Object.keys(x.lawnGround.assetHashes)[0]]=hash('different'),
};
for (const [label,mutate] of Object.entries(cases)) test('reject '+label,()=>{const x=fixture();mutate(x);assert.throws(()=>validateLawnGroundReceipt(x,expected));});
for (const [field,value] of Object.entries({allGraphInputsAccountedFor:false,stockAutomaticViewMipBias:false,samplerSource:'SSM_WRAP_WORLD_GROUP_SETTINGS',textureSampleCount:6,phaseCount:2,continuousUvGradients:false,tangentSpaceNormal:false,normalRotationApplied:true,normalStrength:.4,roughnessInputMapLinear:false,roughnessInputInvertGammaOrSquare:true,roughnessRemapApplied:false,artistTintLinear:[.8,.8,.8],naniteUsage:false,pixelDepthOffsetConnected:true,worldPositionOffsetConnected:true})) test('reject both saved graphs wrong '+field,()=>{
 const x=fixture();for(const k of ['activeMaterialProof','stagedMaterialProof'])x.lawnGround[k][field]=value;assert.throws(()=>validateLawnGroundReceipt(x,expected));
});
for (const [role,field,value] of [['albedo','srgb',false],['normalMap','greenFlipped',false],['roughMap','srgb',true],['roughMap','sourceSha256',hash('foreign')],['normalMap','pixels',[2048,2048]]]) test(`reject both saved texture ${role}.${field}`,()=>{
 const x=fixture();for(const k of ['activeMaterialProof','stagedMaterialProof'])x.lawnGround[k].textures[role][field]=value;assert.throws(()=>validateLawnGroundReceipt(x,expected));
});

for (const [field,value] of Object.entries({offset:0,scale:1,bounds:[0,1],kind:'vendor-calibrated',input:'srgb-provider-roughness',vendorRadiometricCalibration:true})) test('reject both effective roughness '+field,()=>{
 const x=fixture();for(const k of ['activeMaterialProof','stagedMaterialProof'])x.lawnGround[k].effectiveRoughness[field]=value;assert.throws(()=>validateLawnGroundReceipt(x,expected));
});
for (const field of ['roughnessMapDirectLinear','roughnessInvertGammaSquareOrRemap']) test('reject ambiguous legacy roughness '+field,()=>{
 const x=fixture();for(const k of ['activeMaterialProof','stagedMaterialProof'])x.lawnGround[k][field]=field==='roughnessMapDirectLinear';assert.throws(()=>validateLawnGroundReceipt(x,expected));
});
test('reject missing effective roughness in both graphs',()=>{const x=fixture();for(const k of ['activeMaterialProof','stagedMaterialProof'])delete x.lawnGround[k].effectiveRoughness;assert.throws(()=>validateLawnGroundReceipt(x,expected));});
