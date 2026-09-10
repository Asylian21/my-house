// Pure saved-receipt gate; native/rendering validation is outside this function.
import { createHash } from 'node:crypto';
const ID='DOM_01375', SLOT='MAT_0046', OWNER='scripts/unreal/pendant-emitter/pendant_emitter.py';
const SOURCE='LIVING-103-DINING · centrálne závesné svietidlo · 2700 K difúzor';
const SCENE='61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b';
const OBJ='a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455';
const AREA=.12528184603012782, Y=[.2126,.7152,.0722], RGB=[1.9336010395474905,.8042255110086786,.19022622602211375];
const MESH=`/Game/Brezi/Geometry/brezi-twin/StaticMeshes/${ID}.${ID}`, SOURCE_MAT=`/Game/Brezi/Geometry/brezi-twin/Materials/${SLOT}.${SLOT}`;
const CONNECTIONS={BASE_COLOR:'base',ROUGHNESS:'roughness',METALLIC:'metallic',SPECULAR:'specular',EMISSIVE_COLOR:'emission'};
const need=(v,m)=>{if(!v)throw Error('Pendant emitter package gate: '+m);};
const digest=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const near=(a,b,e=1e-7)=>Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<=e;
const vec=(a,b,e=1e-7)=>Array.isArray(a)&&a.length===b.length&&a.every((v,i)=>near(v,b[i],e));
const sameIds=(a,b)=>Array.isArray(a)&&a.length===b.length&&[...a].sort().every((v,i)=>v===[...b].sort()[i]);
const ordered=x=>Array.isArray(x)?x.map(ordered):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,ordered(x[k])])):x;
const equal=(a,b)=>JSON.stringify(ordered(a))===JSON.stringify(ordered(b));
const sourceHash=x=>createHash('sha256').update(JSON.stringify(ordered(x))).digest('hex');
const packagePath=p=>{
  need(typeof p==='string'&&/^\/Game\/Brezi\/[A-Za-z0-9_/-]+\.[A-Za-z0-9_]+$/.test(p),'foreign asset path');
  return p.split('.')[0].replace('/Game/','unreal/BreziTwin/Content/')+'.uasset';
};

export function validatePendantEmitterReceipt(imported,scene){
  const r=imported?.pendantEmitter;
  need(r?.status==='native-pendant-emitter-saved-reload-validated'&&r.revision==='NATIVE-OPAQUE-PENDANT-800LM-20260908-1'
    &&r.nativeApplied===true&&r.activationStarted===true&&r.rollbackRequired===false&&r.rollbackAttempted===false,'missing successful saved native activation');
  need(sameIds(r.selectedIds,[ID])&&r.geometryChanged===false&&r.pointLightsAdded===0&&r.globalQualityChanges===false,'scope, geometry, added lights or quality changed');
  need(r.sourceManifestSha256===SCENE&&imported.sourceManifestSha256===SCENE&&r.sourceObjSha256===OBJ&&scene?.objSha256===OBJ,'source manifest/OBJ provenance differs');
  const records=scene.objects.filter(o=>o.id===ID),record=records[0];
  need(records.length===1&&record.sourceId===SOURCE&&sameIds(record.materialSlots,[SLOT])&&sameIds(record.materialNames,['real-interior-warm-light'])
    &&record.enabled===true&&record.instances===1&&record.triangles===2704&&record.metadata?.babylonCheckCollisions===false,'exact source globe differs');
  need(record.boundsMm?.min?.length===3&&record.boundsMm?.max?.length===3&&record.boundsMm.min.every((v,i)=>near(record.boundsMm.max[i]-v,200,1e-8)),'source globe dimensions differ');
  need(digest(r.sourceRecordSha256)&&r.sourceRecordSha256===sourceHash(record),'source record hash differs');
  const warm=scene.objects.filter(o=>o.materialSlots.includes(SLOT)).map(o=>o.id),protectedIds=[...new Set([...warm,'DOM_01373','DOM_01374'])].sort();
  need(warm.length===29&&new Set(warm).size===29&&protectedIds.length===31&&sameIds(r.protectedIds,protectedIds),'protected warm/cord/shade scope differs');
  for(const flag of ['twoMapReloads','savedReloadVerified','sourceMeshUvCollisionAndOtherFlagsAndAssetBytesUnchanged','other28WarmBindingsAndCordShadeUnchanged','actorLightInventoryUnchanged','workingColorSpaceGetters'])need(r.verification?.[flag]===true,'missing '+flag);
  need(r.nativeVertexAreaReadback===true&&r.renderFallbackAreaReadback===false&&r.rayTracingProxyTopologyVerified===false,'source geometry proof scope missing or overclaimed');
  const nativeGeometry=r.nativeSourceGeometryProof;
  need(nativeGeometry&&equal(nativeGeometry,r.savedReloadSourceGeometryProof),'source geometry saved reload proof differs');
  need(nativeGeometry.method==='public-source-MeshDescription-scalar-corner-getters'&&nativeGeometry.triangleCount===2704
    &&nativeGeometry.canonicalTriangleConnectivityAndWindingVerified===true&&nativeGeometry.matchedUniqueVertices===1302
    &&nativeGeometry.sourceAreaVerified===true&&nativeGeometry.renderFallbackAreaReadback===false&&nativeGeometry.canonicalPhotometryRenormalized===false
    &&nativeGeometry.rayTracingProxyTopologyVerified===false,'exact source topology/area readback absent or overclaimed');
  need(near(nativeGeometry.vertexToleranceMm,.002,1e-15)&&Number.isFinite(nativeGeometry.maximumVertexErrorMm)
    &&nativeGeometry.maximumVertexErrorMm>=0&&nativeGeometry.maximumVertexErrorMm<=.002
    &&near(nativeGeometry.areaToleranceM2,2.5e-7,1e-18)&&near(nativeGeometry.canonicalAreaM2,AREA,1e-12)
    &&near(nativeGeometry.sourceAreaM2,AREA,2.5e-7)&&near(nativeGeometry.areaDifferenceM2,nativeGeometry.sourceAreaM2-AREA,1e-15),'source vertex/area tolerance or arithmetic differs');
  need(nativeGeometry.normalFallbackTarget==='<NaniteFallbackTarget.PERCENT_TRIANGLES: 1>'&&nativeGeometry.fullNormalFallbackPolicyVerified===true
    &&nativeGeometry.legacyAutoMigrationValidated===false&&[2600,2704].includes(nativeGeometry.renderLod0Triangles),'normal fallback policy absent or legacy migration left active');
  const g=r.sourceGeometry,p=r.photometry;
  need(g?.triangles===2704&&g.zeroAreaPoleTriangles===104&&g.outwardNondegenerateTriangles===2600&&g.weldedVertices===1302&&g.weldedEdges===3900
    &&g.closedAfterPositionWeld===true&&near(g.weldPrecisionMm,.00001,1e-15)&&near(g.surfaceAreaM2,AREA,1e-12),'source area/topology proof differs');
  need(p?.authoredIntrinsicFluxLumens===800&&p.sourceLabelCctK===2700&&p.dayNightSamePower===true&&p.fluxIsVendorMeasured===false
    &&p.fluxDefinition==='Entire outward globe before opaque source shade occlusion; not delivered fixture lumens','intrinsic source-power definition differs');
  const luminance=800/(Math.PI*AREA),emission=RGB.map(v=>v*luminance);
  need(near(p.surfaceAreaM2,AREA,1e-12)&&near(p.luminanceCdPerM2,luminance,1e-8)&&vec(p.luminanceWeightsRGB,Y,1e-12)
    &&vec(p.colorNormalizedToY1,RGB,1e-12)&&vec(p.emissionRGB,emission,1e-8)&&near(p.reconstructedFluxLumens,800,1e-8),'photometric reconstruction differs');
  const space=r.workingColorSpace;
  need(space?.choiceValue===1&&space.choice==='EWorkingColorSpace::sRGB'&&space.settingsNativeGetters===true&&space.normalizationUsesExplicitRec709Weights===true,'missing BT.709 native settings readback');
  need(space.method==='typed-editor-RendererSettings-CDO'&&space.settingsClass==='/Script/Engine.RendererSettings'
    &&space.settingsObject==='/Script/Engine.Default__RendererSettings'&&space.renderThreadWorkingUniformReadback===false,'typed CDO identity absent or render-thread proof overclaimed');
  const coordinates={red:[.64,.33],green:[.30,.60],blue:[.15,.06],white:[.3127,.3290]};
  need(sameIds(Object.keys(space.chromaticities??{}),Object.keys(coordinates)),'working-space coordinate scope differs');
  for(const[k,v]of Object.entries(coordinates))need(vec(space.chromaticities[k],v,1e-6),'working-space coordinate differs: '+k);
  const surface=r.sourceSurfaceProof,sourceMaterial=scene.materials?.[SLOT];
  need(surface?.sourceMaterial===SOURCE_MAT&&surface.sourceParameterGetters===true&&sourceMaterial?.alpha===1
    &&vec(surface.base,sourceMaterial.color,1e-7)&&near(surface.roughness,sourceMaterial.roughness,1e-7)&&near(surface.metallic,0)&&near(surface.specular,0),'native canonical surface getters differ');
  need(digest(r.recipeSha256),'missing authored recipe hash');
  const material=`/Game/Brezi/MaterialStudies/PendantEmitter/V_${r.recipeSha256.slice(0,16)}/M_Pendant800lm.M_Pendant800lm`;
  need(sameIds(r.generatedAssetPaths,[material]),'expected exactly one versioned material');
  for(const proof of [r.stagedMaterialProof,r.savedReloadMaterialProof]){
    need(proof?.asset===material&&proof.recipeSha256===r.recipeSha256&&proof.graphNodeCount===5&&proof.nativeGraphGetters===true
      &&proof.opaque===true&&proof.defaultLit===true&&proof.twoSided===false&&proof.naniteUsage===true&&proof.worldPositionOffsetConnected===false
      &&proof.pixelDepthOffsetConnected===false&&proof.pointLightsAdded===0&&proof.timeDependent===false,'missing exact five-node opaque DefaultLit saved graph');
    need(sameIds(proof.connections?.map(c=>c.property),Object.keys(CONNECTIONS)),'material output connection scope differs');
    for(const c of proof.connections)need(c.sourceRole===CONNECTIONS[c.property]&&c.outputName===''&&c.nativeInputNodeVerified===true,'native constant output connection differs');
    const expected={base:surface.base,roughness:[surface.roughness],metallic:[surface.metallic],specular:[surface.specular],emission};
    need(sameIds(Object.keys(proof.nativeConstants??{}),Object.keys(expected)),'constant graph scope differs');
    for(const[k,values]of Object.entries(expected))need(Array.isArray(proof.nativeConstants[k])&&proof.nativeConstants[k].length===values.length
      &&values.every((v,i)=>near(proof.nativeConstants[k][i],v,Math.max(1e-7,Math.abs(v)*2e-7))),'saved native constant differs: '+k);
    const actualFlux=Math.PI*AREA*proof.nativeConstants.emission.reduce((sum,v,i)=>sum+v*Y[i],0);
    need(near(actualFlux,800,.0002)&&near(proof.authoredIntrinsicFluxReconstructedFromNativeConstants,actualFlux,1e-8),'native float32 emission no longer reconstructs 800 lm');
  }
  need(equal(r.stagedMaterialProof,r.savedReloadMaterialProof),'saved graph differs from staged material readback');
  const binding=r.bindings?.[0];
  need(r.bindings?.length===1&&binding.objectId===ID&&binding.sourceId===SOURCE&&binding.sourceSlot===SLOT&&binding.material===material
    &&binding.emissiveLightSource===true&&binding.savedReloadVerified===true,'exact saved source binding differs');
  const before=r.nativeSelectedBefore,after=r.nativeSelectedAfter;
  need(before&&after&&before.mesh===MESH&&after.mesh===MESH&&before.meshMaterial===SOURCE_MAT&&after.meshMaterial===SOURCE_MAT
    &&after.effectiveMaterial===material&&sameIds(after.overrides,[material])&&after.emissiveLightSource===true,'native source mesh/material binding differs');
  const stable=x=>Object.fromEntries(Object.entries(x).filter(([k])=>!['effectiveMaterial','overrides','emissiveLightSource'].includes(k)));
  need(equal(stable(before),stable(after))&&Number.isSafeInteger(after.triangles)&&after.triangles>0&&Number.isSafeInteger(after.uvChannels)&&after.uvChannels>=1
    &&after.triangles===nativeGeometry.renderLod0Triangles&&after.profile==='NoCollision'&&/NO_COLLISION/.test(after.collision)&&after.affectDynamicIndirectLighting===true&&after.visibleInRayTracing===true,'native topology/UV/collision/transport flags changed');
  for(const name of ['protectedComponentSnapshotBeforeSha256','protectedComponentSnapshotAfterSha256'])need(digest(r[name]),'missing native protected snapshot hash');
  const recipes=[OWNER,'scripts/unreal/pendant-emitter/source_geometry.py','scripts/unreal/pendant-emitter/emitter_reference.py','scripts/unreal/pendant-emitter/emitter_material.py','scripts/unreal/tv-oak/tv_oak.py','scripts/unreal/materials.py','unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.h','unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.cpp'];
  need(sameIds(Object.keys(r.pipelineFiles??{}),recipes),'exact authoring recipe inputs missing or expanded');
  for(const[path,h]of Object.entries(r.pipelineFiles))need(digest(h)&&imported.pipelineFiles?.[path]===h,'authoring recipe omitted from final import');
  const generatedBase=packagePath(material).replace(/\.uasset$/,'');
  need(digest(r.assetHashes?.[generatedBase+'.uasset'])&&Object.keys(r.assetHashes).every(p=>['.uasset','.uexp','.ubulk'].some(ext=>p===generatedBase+ext)),'exact generated material package required');
  need(r.canonicalAssetHashes&&Object.keys(r.canonicalAssetHashes).length>0,'preserved native asset hashes missing');
  for(const id of protectedIds)need(digest(r.canonicalAssetHashes[packagePath(`/Game/Brezi/Geometry/brezi-twin/StaticMeshes/${id}.${id}`)]),'protected source mesh hash omitted: '+id);
  for(const path of [SOURCE_MAT,before.effectiveMaterial])need(digest(r.canonicalAssetHashes[packagePath(path)]),'preserved selected material hash omitted');
  for(const table of [r.assetHashes,r.canonicalAssetHashes])for(const[path,h]of Object.entries(table))need(/^unreal\/BreziTwin\/Content\/Brezi\/[A-Za-z0-9_/-]+\.(?:uasset|uexp|ubulk)$/.test(path)
    &&digest(h)&&imported.finalAssetHashes?.[path]===h,'generated/preserved final asset closure differs');
  return{status:'native-pendant-emitter-package-inputs-validated',selectedIds:[ID],authoredIntrinsicFluxLumens:800,renderedTransportVerified:false};
}
