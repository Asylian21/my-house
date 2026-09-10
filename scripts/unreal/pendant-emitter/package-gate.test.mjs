import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {validatePendantEmitterReceipt} from './package-gate.mjs';
// Synthetic receipt shape/negative tests only. No UE, captured asset or rendered energy proof.
const H='a'.repeat(64), ID='DOM_01375', SLOT='MAT_0046', SOURCE='LIVING-103-DINING · centrálne závesné svietidlo · 2700 K difúzor';
const SCENE='61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b',OBJ='a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455';
const OWNER='scripts/unreal/pendant-emitter/pendant_emitter.py', MAT=`/Game/Brezi/MaterialStudies/PendantEmitter/V_${H.slice(0,16)}/M_Pendant800lm.M_Pendant800lm`;
const MESH=`/Game/Brezi/Geometry/brezi-twin/StaticMeshes/${ID}.${ID}`, BASE='/Game/Brezi/Geometry/brezi-twin/Materials/MAT_0046.MAT_0046';
const area=.12528184603012782,Y=[.2126,.7152,.0722],rgb=[1.9336010395474905,.8042255110086786,.19022622602211375],luminance=800/(Math.PI*area),emission=rgb.map(v=>v*luminance);
const ordered=x=>Array.isArray(x)?x.map(ordered):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,ordered(x[k])])):x;
const hash=x=>createHash('sha256').update(JSON.stringify(ordered(x))).digest('hex');
const packageFile=p=>p.split('.')[0].replace('/Game/','unreal/BreziTwin/Content/')+'.uasset';
function fixture(){
  const record={id:ID,sourceId:SOURCE,materialSlots:[SLOT],materialNames:['real-interior-warm-light'],enabled:true,instances:1,triangles:2704,metadata:{babylonCheckCollisions:false},boundsMm:{min:[9150,3850,1885],max:[9350,4050,2085]}};
  const others=Array.from({length:28},(_,i)=>({id:`DOM_${String(i).padStart(5,'0')}`,materialSlots:[SLOT]}));
  const scene={objSha256:OBJ,objects:[record,...others,{id:'DOM_01373',materialSlots:['MAT_0034']},{id:'DOM_01374',materialSlots:['MAT_0050']}],materials:{[SLOT]:{alpha:1,color:[1,.9411764705882353,.8470588235294118],roughness:.2}}};
  const protectedIds=scene.objects.map(o=>o.id),surface={sourceMaterial:BASE,sourceParameterGetters:true,base:scene.materials[SLOT].color,roughness:.2,metallic:0,specular:0};
  const native={mesh:MESH,meshMaterial:BASE,effectiveMaterial:BASE,overrides:[],emissiveLightSource:false,triangles:2600,uvChannels:1,profile:'NoCollision',collision:'CollisionEnabled.NO_COLLISION',affectDynamicIndirectLighting:true,visibleInRayTracing:true,translation:[0,0,0],rotation:[0,0,0,1],scale:[1,1,1]};
  const r={status:'native-pendant-emitter-saved-reload-validated',revision:'NATIVE-OPAQUE-PENDANT-800LM-20260908-1',nativeApplied:true,activationStarted:true,rollbackRequired:false,rollbackAttempted:false,selectedIds:[ID],geometryChanged:false,pointLightsAdded:0,globalQualityChanges:false,sourceManifestSha256:SCENE,sourceObjSha256:OBJ,sourceRecordSha256:hash(record),protectedIds,
    sourceGeometry:{triangles:2704,zeroAreaPoleTriangles:104,outwardNondegenerateTriangles:2600,weldedVertices:1302,weldedEdges:3900,closedAfterPositionWeld:true,weldPrecisionMm:.00001,surfaceAreaM2:area},
    photometry:{authoredIntrinsicFluxLumens:800,sourceLabelCctK:2700,dayNightSamePower:true,fluxIsVendorMeasured:false,fluxDefinition:'Entire outward globe before opaque source shade occlusion; not delivered fixture lumens',surfaceAreaM2:area,luminanceCdPerM2:luminance,luminanceWeightsRGB:Y,colorNormalizedToY1:rgb,emissionRGB:emission,reconstructedFluxLumens:800},
    workingColorSpace:{choiceValue:1,choice:'EWorkingColorSpace::sRGB',method:'typed-editor-RendererSettings-CDO',settingsClass:'/Script/Engine.RendererSettings',settingsObject:'/Script/Engine.Default__RendererSettings',renderThreadWorkingUniformReadback:false,settingsNativeGetters:true,normalizationUsesExplicitRec709Weights:true,chromaticities:{red:[.64,.33],green:[.30,.60],blue:[.15,.06],white:[.3127,.3290]}},sourceSurfaceProof:surface,recipeSha256:H,generatedAssetPaths:[MAT],
    nativeSelectedBefore:native,nativeSelectedAfter:{...structuredClone(native),effectiveMaterial:MAT,overrides:[MAT],emissiveLightSource:true},protectedComponentSnapshotBeforeSha256:H,protectedComponentSnapshotAfterSha256:H,
    verification:Object.fromEntries(['twoMapReloads','savedReloadVerified','sourceMeshUvCollisionAndOtherFlagsAndAssetBytesUnchanged','other28WarmBindingsAndCordShadeUnchanged','actorLightInventoryUnchanged','workingColorSpaceGetters'].map(k=>[k,true])),
    bindings:[{objectId:ID,sourceId:SOURCE,sourceSlot:SLOT,material:MAT,emissiveLightSource:true,savedReloadVerified:true}],pipelineFiles:{},assetHashes:{[packageFile(MAT)]:H},canonicalAssetHashes:{[packageFile(BASE)]:H}};
  for(const path of [OWNER,'scripts/unreal/pendant-emitter/source_geometry.py','scripts/unreal/pendant-emitter/emitter_reference.py','scripts/unreal/pendant-emitter/emitter_material.py','scripts/unreal/tv-oak/tv_oak.py','scripts/unreal/materials.py','unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.h','unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.cpp'])r.pipelineFiles[path]=H;
  for(const id of protectedIds)r.canonicalAssetHashes[packageFile(`/Game/Brezi/Geometry/brezi-twin/StaticMeshes/${id}.${id}`)]=H;
  const proof={asset:MAT,recipeSha256:H,graphNodeCount:5,nativeGraphGetters:true,opaque:true,defaultLit:true,twoSided:false,naniteUsage:true,worldPositionOffsetConnected:false,pixelDepthOffsetConnected:false,pointLightsAdded:0,timeDependent:false,
    connections:Object.entries({BASE_COLOR:'base',ROUGHNESS:'roughness',METALLIC:'metallic',SPECULAR:'specular',EMISSIVE_COLOR:'emission'}).map(([property,sourceRole])=>({property,sourceRole,outputName:'',nativeInputNodeVerified:true})),nativeConstants:{base:surface.base,roughness:[.2],metallic:[0],specular:[0],emission},authoredIntrinsicFluxReconstructedFromNativeConstants:Math.PI*area*emission.reduce((s,v,i)=>s+v*Y[i],0)};
  r.stagedMaterialProof=structuredClone(proof);r.savedReloadMaterialProof=structuredClone(proof);
  r.nativeVertexAreaReadback=true;r.renderFallbackAreaReadback=false;r.rayTracingProxyTopologyVerified=false;
  r.nativeSourceGeometryProof={method:'public-source-MeshDescription-scalar-corner-getters',triangleCount:2704,canonicalTriangleConnectivityAndWindingVerified:true,
    matchedUniqueVertices:1302,maximumVertexErrorMm:.0015220703,vertexToleranceMm:.002,sourceAreaM2:area+1.6692241e-7,canonicalAreaM2:area,
    areaDifferenceM2:1.6692241e-7,areaToleranceM2:2.5e-7,sourceAreaVerified:true,renderFallbackAreaReadback:false,canonicalPhotometryRenormalized:false,
    normalFallbackTarget:'<NaniteFallbackTarget.PERCENT_TRIANGLES: 1>',renderLod0Triangles:2600,fullNormalFallbackPolicyVerified:true,
    legacyAutoMigrationValidated:false,rayTracingProxyTopologyVerified:false};
  r.savedReloadSourceGeometryProof=structuredClone(r.nativeSourceGeometryProof);
  return{scene,imported:{pendantEmitter:r,sourceManifestSha256:SCENE,pipelineFiles:{...r.pipelineFiles},finalAssetHashes:{...r.assetHashes,...r.canonicalAssetHashes}}};
}
test('Complete synthetic source-scoped saved receipt passes package-input gate only',()=>{const x=fixture();assert.deepEqual(validatePendantEmitterReceipt(x.imported,x.scene),{status:'native-pendant-emitter-package-inputs-validated',selectedIds:[ID],authoredIntrinsicFluxLumens:800,renderedTransportVerified:false});});
test('Owned split bulk payload requires and accepts matching final closure',()=>{const x=fixture(),p=packageFile(MAT).replace('.uasset','.ubulk');x.imported.pendantEmitter.assetHashes[p]=H;x.imported.finalAssetHashes[p]=H;assert.doesNotThrow(()=>validatePendantEmitterReceipt(x.imported,x.scene));delete x.imported.finalAssetHashes[p];assert.throws(()=>validatePendantEmitterReceipt(x.imported,x.scene));});
const cases={
 'missing stage':x=>delete x.imported.pendantEmitter,
 'failed native stage':r=>r.status='failed',
 'restore receipt':r=>r.nativeApplied=false,
 'activation absent':r=>r.activationStarted=false,
 'rollback attempted':r=>r.rollbackAttempted=true,
 'second selected object':r=>r.selectedIds.push('DOM_01374'),
 'second native binding':r=>r.bindings.push(structuredClone(r.bindings[0])),
 'wrong source object':r=>r.bindings[0].objectId='DOM_01374',
 'wrong source label':r=>r.bindings[0].sourceId='not the globe',
 'wrong source slot':r=>r.bindings[0].sourceSlot='MAT_0034',
 'unregistered versioned material':r=>r.bindings[0].material=BASE,
 'source metadata stale':r=>r.sourceRecordSha256='b'.repeat(64),
 'source hash differs':r=>r.sourceManifestSha256='b'.repeat(64),
 '800 delivered-lumen claim':r=>r.photometry.fluxDefinition='delivered fixture lumens',
 'vendor measurement claim':r=>r.photometry.fluxIsVendorMeasured=true,
 '1600 lm':r=>r.photometry.authoredIntrinsicFluxLumens=1600,
 'wrong CCT':r=>r.photometry.sourceLabelCctK=6500,
 'night power switch':r=>r.photometry.dayNightSamePower=false,
 'sphere analytic area substituted':r=>r.sourceGeometry.surfaceAreaM2=4*Math.PI*.1*.1,
 'source emitting surface open':r=>r.sourceGeometry.closedAfterPositionWeld=false,
 'wrong luminance':r=>r.photometry.luminanceCdPerM2*=2,
 'legacy RGB weights':r=>r.photometry.luminanceWeightsRGB=[.3,.59,.11],
 'wide gamut setting':r=>r.workingColorSpace.choiceValue=2,
 'missing working-space getter':r=>r.workingColorSpace.settingsNativeGetters=false,
 'missing CDO bridge header':r=>delete r.pipelineFiles['unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.h'],
 'missing CDO bridge implementation':r=>delete r.pipelineFiles['unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.cpp'],
 'untyped working-space method':r=>r.workingColorSpace.method='inferred config',
 'foreign settings class':r=>r.workingColorSpace.settingsClass='/Script/Engine.DeveloperSettings',
 'foreign settings object':r=>r.workingColorSpace.settingsObject='/Script/Engine.Default__RendererSettings_2',
 'render-thread uniform overclaim':r=>r.workingColorSpace.renderThreadWorkingUniformReadback=true,
 'surface roughness changed':r=>r.sourceSurfaceProof.roughness=.5,
 'source base changed':r=>r.sourceSurfaceProof.base=[0,0,0],
 'one reload':r=>r.verification.twoMapReloads=false,
 'added punctual light':r=>r.pointLightsAdded=1,
 'quality workaround':r=>r.globalQualityChanges=true,
 'geometry mutation':r=>r.geometryChanged=true,
 'missing protected inventory':r=>r.verification.actorLightInventoryUnchanged=false,
 'other shared warm bindings changed':r=>r.verification.other28WarmBindingsAndCordShadeUnchanged=false,
 'unpreserved shade':r=>r.protectedIds.pop(),
 'emissive flag not saved':r=>r.nativeSelectedAfter.emissiveLightSource=false,
 'native UV changed':r=>r.nativeSelectedAfter.uvChannels=0,
 'native fallback topology changed':r=>r.nativeSelectedAfter.triangles++,
 'new collision':r=>r.nativeSelectedAfter.profile='BlockAll',
 'dynamic GI disabled':r=>r.nativeSelectedAfter.affectDynamicIndirectLighting=false,
 'foreign source mesh':r=>r.nativeSelectedAfter.mesh=BASE,
 'missing recipe input':r=>delete r.pipelineFiles[OWNER],
 'foreign generated package':r=>r.assetHashes['unreal/BreziTwin/Content/Brezi/Other.uasset']=H,
 'missing protected mesh hash':r=>delete r.canonicalAssetHashes[packageFile('/Game/Brezi/Geometry/brezi-twin/StaticMeshes/DOM_01374.DOM_01374')],
 'no preserved source material':r=>delete r.canonicalAssetHashes[packageFile(BASE)],
};
for(const[name,mutate]of Object.entries(cases))test('Reject '+name,()=>{const x=fixture();mutate(name==='missing stage'?x:x.imported.pendantEmitter);assert.throws(()=>validatePendantEmitterReceipt(x.imported,x.scene));});
for(const side of ['stagedMaterialProof','savedReloadMaterialProof'])for(const[name,mutate]of Object.entries({
 'sixth node':p=>p.graphNodeCount=6,'translucent':p=>p.opaque=false,'unlit':p=>p.defaultLit=false,'two sided':p=>p.twoSided=true,
 'dynamic graph':p=>p.timeDependent=true,'WPO':p=>p.worldPositionOffsetConnected=true,'PDO':p=>p.pixelDepthOffsetConnected=true,'missing native getters':p=>p.nativeGraphGetters=false,
 'wrong graph recipe':p=>p.recipeSha256='b'.repeat(64),'wrong node output':p=>p.connections[0].outputName='R',
 'missing output':p=>p.connections.pop(),'wrong output role':p=>p.connections[4].sourceRole='base','unverified connection':p=>p.connections[0].nativeInputNodeVerified=false,
 'brighter emission':p=>p.nativeConstants.emission[0]*=2,'NaN emission':p=>p.nativeConstants.emission[0]=NaN,'forged reconstruction':p=>p.authoredIntrinsicFluxReconstructedFromNativeConstants=1600,
}))test(`Reject ${side}: ${name}`,()=>{const x=fixture();mutate(x.imported.pendantEmitter[side]);assert.throws(()=>validatePendantEmitterReceipt(x.imported,x.scene));});
for(const kind of ['recipe','generated','preserved'])test('Reject missing final '+kind+' hash',()=>{const x=fixture();if(kind==='recipe')delete x.imported.pipelineFiles[OWNER];else delete x.imported.finalAssetHashes[packageFile(kind==='generated'?MAT:BASE)];assert.throws(()=>validatePendantEmitterReceipt(x.imported,x.scene));});

for(const[name,mutate]of Object.entries({
 'missing source helper':r=>delete r.pipelineFiles['scripts/unreal/pendant-emitter/source_geometry.py'],
 'native source readback absent':r=>r.nativeVertexAreaReadback=false,
 'fallback area overclaim':r=>r.renderFallbackAreaReadback=true,
 'RT topology overclaim':r=>r.rayTracingProxyTopologyVerified=true,
 'source geometry reload differs':r=>r.savedReloadSourceGeometryProof.sourceAreaM2+=1e-8,
 'vertex tolerance expanded':r=>r.nativeSourceGeometryProof.vertexToleranceMm=.01,
 'vertex outside tolerance':r=>r.nativeSourceGeometryProof.maximumVertexErrorMm=.00201,
 'area outside tolerance':r=>{r.nativeSourceGeometryProof.sourceAreaM2=area+3e-7;r.nativeSourceGeometryProof.areaDifferenceM2=3e-7;},
 'incorrect area difference':r=>r.nativeSourceGeometryProof.areaDifferenceM2=0,
 'source triangles missing':r=>r.nativeSourceGeometryProof.triangleCount=2600,
 'unverified winding':r=>r.nativeSourceGeometryProof.canonicalTriangleConnectivityAndWindingVerified=false,
 'AUTO native fallback':r=>r.nativeSourceGeometryProof.normalFallbackTarget='<NaniteFallbackTarget.AUTO: 0>',
 'legacy migration retained':r=>r.nativeSourceGeometryProof.legacyAutoMigrationValidated=true,
 'fallback differs native snapshot':r=>r.nativeSourceGeometryProof.renderLod0Triangles=2704,
 'source photometry renormalized':r=>r.nativeSourceGeometryProof.canonicalPhotometryRenormalized=true,
}))test('Reject source proof: '+name,()=>{const x=fixture();mutate(x.imported.pendantEmitter);if(name!=='source geometry reload differs')x.imported.pendantEmitter.savedReloadSourceGeometryProof=structuredClone(x.imported.pendantEmitter.nativeSourceGeometryProof);assert.throws(()=>validatePendantEmitterReceipt(x.imported,x.scene));});
