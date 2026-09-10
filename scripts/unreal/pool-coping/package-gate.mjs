import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
function rootOf(p){while(!fs.existsSync(path.join(p,'lib/twin-site.ts'))){const n=path.dirname(p);if(n===p)throw Error('Project root unavailable');p=n;}return p;}
const root=rootOf(here),prefix='scripts/unreal/pool-coping/',ids=Array.from({length:28},(_,i)=>`DOM_${String(1726+i).padStart(5,'0')}`),excluded=Array.from({length:4},(_,i)=>`DOM_${String(1817+i).padStart(5,'0')}`),base='/Game/Brezi/Geometry/brezi-twin/Materials/MAT_0102.MAT_0102';
const sha=v=>crypto.createHash('sha256').update(v).digest('hex');
const hash=v=>typeof v==='string' && /^[0-9a-f]{64}$/.test(v);
const canonical=v=>Array.isArray(v)?v.map(canonical):v && typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const equal=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
export const POOL_COPING_SHADER_HASHES={"uv":"36e7977983b0994b1fd36bd8e0962f36d22731577799abbed396b5d418356d23","normal":"77a9784efc7c29efdbd7cc3697df6767042898ba1911a2d794c5a99a68a7997b","color":"fe2975bccccb647482868866d5d16ab3b55070d23bd243058579176b39743db1","roughness":"ec473084e86778fe98b720aab528962ede8bcdbdaa1bb1151932cecfe2cfd381"};
const near=(a,b)=>typeof a==='number' && Number.isFinite(a) && Math.abs(a-b)<1e-6;
function need(ok,message){if(!ok)throw Error('Pool coping package gate: '+message);}
export function expectedPoolCopingInputs(){
 const reference=JSON.parse(fs.readFileSync(path.join(here,'inputs.json'),'utf8'));
 const helpers=['scripts/unreal/tv-oak/tv_oak.py',...['lawn_ground','source','graph'].map(n=>`scripts/unreal/lawn-ground/${n}.py`),...['h','cpp'].map(x=>`unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.${x}`)];
 const recipeInputs=Object.fromEntries(['coping.py','graph.py','inputs.json'].map(n=>[prefix+n,sha(fs.readFileSync(path.join(here,n)))]));
 for(const n of helpers)recipeInputs[n]=sha(fs.readFileSync(path.join(root,n)));
 const pipeline={...recipeInputs,...reference.sourceIntentFiles,...reference.evidence,...Object.fromEntries(Object.values(reference.maps).map(v=>[v.path,v.sha256])),'scripts/unreal/materials.py':sha(fs.readFileSync(path.join(root,'scripts/unreal/materials.py'))),[prefix+'package-gate.mjs']:sha(fs.readFileSync(path.join(here,'package-gate.mjs')))};
 for(const [n,h] of Object.entries(pipeline)){const p=path.join(root,n);need(fs.realpathSync(p)===p && sha(fs.readFileSync(p))===h,'input changed: '+n);}
 need(reference.schemaVersion===1 && reference.revision==='POOL-COPING-PBR-1' && reference.source.measuredSiteMaterial===false && reference.source.license==='CC0-1.0' && typeof reference.source.physicalScaleProvenance==='string' && reference.source.physicalScaleProvenance.length>0,'source provenance differs');
 need(equal(Object.keys(reference.sourceRecords).sort(),ids) && equal(reference.excludedSharedSlotIds,excluded) && Object.values(reference.sourceRecords).every(v=>v.triangles===12 && v.instances===1 && v.enabled===true && equal(v.materialSlots,['MAT_0102'])),'reference scope differs');
 return {reference,recipeInputs,pipeline};
}
export function validatePoolCopingReceipt(imported,expected=expectedPoolCopingInputs()){
 const r=imported.poolCoping,inactive=r?.status==='source-pool-coping-retained';
 need(r && (inactive || r.status==='pool-coping-saved-reload-validated') && r.nativeApplied===!inactive && r.restoring===false && r.actorMetadataWritten===false && equal(r.rollbackErrors,[]),'saved stage absent');
 need(equal(r.selectedIds,ids) && r.sourceMaterialSlot==='MAT_0102' && equal(r.excludedSharedSlotIds,excluded),'28-source scope differs');
 need(r.sourceManifestSha256===imported.sourceManifestSha256 && r.sourceManifestSha256===expected.reference.sceneSha256 && r.sourceObjSha256===expected.reference.objSha256,'canonical source differs');
 need(hash(r.recipeSha256) && typeof r.recipeCanonicalJson==='string' && sha(r.recipeCanonicalJson)===r.recipeSha256 && equal(JSON.parse(r.recipeCanonicalJson),r.recipe),'recipe hash differs');
 need(equal(r.recipe,{reference:expected.reference,recipeInputs:expected.recipeInputs}) && equal(r.pipelineFiles,expected.pipeline),'current recipe or pipeline differs');
 for(const [n,h] of Object.entries(expected.pipeline))need(imported.pipelineFiles?.[n]===h,'source missing from import closure: '+n);
 need(r.grassInstanceCount===33769 && imported.lawnDetail?.instanceCount===33769,'existing lawn detail differs');
 const owned=`/Game/Brezi/PoolCoping/R_${r.recipeSha256.slice(0,16)}`,material=owned+'/Materials/M_PoolCoping.M_PoolCoping';
 need(equal(Object.keys(r.selectedBefore??{}).sort(),ids) && equal(Object.keys(r.selectedAfter??{}).sort(),ids),'binding count differs');
 for(const id of ids){
  const a=r.selectedBefore[id],b=r.selectedAfter[id],mesh=`/Game/Brezi/Geometry/brezi-twin/StaticMeshes/${id}.${id}`;
  need(a.mesh===mesh && b.mesh===mesh && a.meshMaterial===base && b.meshMaterial===base && a.actor===b.actor && a.component===b.component,'source identity differs: '+id);
  need((a.state==='source' && a.effectiveMaterial===base && equal(a.overrides,[])) || (!inactive && a.state==='active' && a.effectiveMaterial===material && equal(a.overrides,[material])),'prior binding foreign: '+id);
  need(b.state===(inactive?'source':'active') && b.effectiveMaterial===(inactive?base:material) && equal(b.overrides,inactive?[]:[material]),'saved binding differs: '+id);
  need(equal(a.nativeSnapshot,b.nativeSnapshot) && equal(a.sourceProof,b.sourceProof),'source readback changed: '+id);
  const p=b.sourceProof;need(p?.triangles===12 && p.windingMultiplicityVerified===true && p.sourceToleranceMm===.002 && p.uv0Tolerance===.000002 && hash(p.snapshotSha256) && Number.isFinite(p.maximumPositionErrorMm) && p.maximumPositionErrorMm>=0 && p.maximumPositionErrorMm<=.002 && Number.isFinite(p.maximumUv0Error) && p.maximumUv0Error>=0 && p.maximumUv0Error<=.000002,'source position/UV proof missing: '+id);
  need(hash(r.protectedAssetHashes?.[`unreal/BreziTwin/Content/Brezi/Geometry/brezi-twin/StaticMeshes/${id}.uasset`]),'source mesh asset unpinned: '+id);
 }
 need(Object.keys(r.protectedAssetHashes??{}).length>=1878 && hash(r.sourcePreservationSnapshotSha256) && hash(r.protectedAssetHashes['unreal/BreziTwin/Content/Brezi/Geometry/brezi-twin/Materials/MAT_0102.uasset']),'source asset preservation absent');
 for(const [n,h] of Object.entries(r.protectedAssetHashes))need(!n.includes('/PoolCoping/') && hash(h) && imported.finalAssetHashes?.[n]===h,'protected native asset changed or omitted');
 if(inactive){
  need(r.sourceOverridesRetained===28 && r.candidateOverridesActive===0 && r.sourceObjectsDeleted===0 && r.sourceStateUnchangedAfterReload===true && equal(r.assetHashes,{}),'inactive source preservation differs');
  for(const flag of ['mapSaved','worldUnloaded','mapReloaded'])need(r.sourceReload?.[flag]===true,'inactive saved map proof absent');
  need(r.renderedVerified===false && r.sourceMaterialNativeParameterReadback===false,'inactive proof claims differ');
  return {status:'source-pool-coping-package-inputs-validated',selectedIds:ids,recipeSha256:r.recipeSha256,renderedVerified:false};
 }
 need(r.activationStarted===true,'activation proof absent');
 for(const phase of ['stagedReload','activeReload'])for(const flag of ['mapSaved','worldUnloaded','allFourOwnedAssetsAbsentBeforeReload','mapReloaded'])need(r[phase]?.[flag]===true,'saved absence/reload proof absent: '+phase+'/'+flag);
 for(const flag of ['exact28Bindings','sourceVerticesUv0Unchanged','allOtherActorsAndGrassUnchanged','sourceBaseMaterialRetained','twoMapReloads','twoOwnedAssetUnloadAbsenceReadbacks','exactSavedGraphsEqual'])need(r.verification?.[flag]===true,'native preservation absent: '+flag);
 const g=r.activeMaterialProof,m=expected.reference.material,q=m.roughness;
 need(equal(g,r.stagedMaterialProof) && g?.asset===material && g.recipeSha256===r.recipeSha256 && g.nodeCount===21 && g.linkCount===19 && g.textureSampleCount===3 && equal(g.parameters,m),'saved graph differs');
 for(const flag of ['exactGraphVerified','allInputsAccountedFor','worldSpaceNormal','roughnessRemapped','roughnessAuthoredNotMeasured','albedoAuthoredColorConversion','implicitContinuousGradientsWithinEachPlanarFace','stockAutomaticViewMipBias'])need(g[flag]===true,'graph policy absent: '+flag);
 need(g.mapping==='signed-dominant-axis-world-planar' && g.normalGreenFlipCount===1 && g.normalShaderGreenFlipCount===0 && g.sourceUvSampled===false && g.worldPositionOffsetConnected===false && g.pixelDepthOffsetConnected===false && g.sourceScaleProvenance===expected.reference.source.physicalScaleProvenance,'mapping/PBR policy differs');
 const scalars={period:m.tileMm/10,normalStrength:m.normalStrength,albedoMix:m.albedoMix,roughBase:q.base,roughAmplitude:q.amplitude,roughMean:q.mapMean,roughMin:q.min,roughMax:q.max,metallic:0,specular:.5};
 need(equal(Object.keys(g.nativeScalars??{}).sort(),Object.keys(scalars).sort()) && Object.entries(scalars).every(([k,v])=>near(g.nativeScalars[k],v)),'actual scalar readback differs');
 need(equal(Object.keys(g.nativeVectors??{}).sort(),['baseColor','tint']) && [['baseColor','baseColorLinear'],['tint','tintLinear']].every(([a,b])=>g.nativeVectors[a]?.length===3 && g.nativeVectors[a].every((v,i)=>near(v,m[b][i]))),'actual color readback differs');
 need(equal(g.shaderSha256,POOL_COPING_SHADER_HASHES) && g.renderedVerified===false && g.residentMipsVerified===false && g.nativeNormalTangentNumericProof===false,'shader/evidence boundary differs');
 const roles={albedo:'Diffuse',normalMap:'nor_gl',roughMap:'Rough'};need(equal(Object.keys(g.textures??{}).sort(),Object.keys(roles).sort()),'map roles differ');
 for(const [role,input] of Object.entries(roles)){const t=g.textures[role];need(t.asset===`${owned}/Textures/T_${role}.T_${role}` && t.sourceSha256===expected.reference.maps[input].sha256 && equal(t.pixels,[4096,4096]) && t.srgb===(role==='albedo') && t.greenFlipped===(role==='normalMap') && t.wrapXY===true && t.sourceDimensionReadback===true,'native texture proof differs: '+role);}
 const assetPrefix=`unreal/BreziTwin/Content/Brezi/PoolCoping/R_${r.recipeSha256.slice(0,16)}/`;
 need(Object.keys(r.assetHashes??{}).length>=4,'owned asset receipt absent');
 for(const [n,h] of Object.entries(r.assetHashes))need(n.startsWith(assetPrefix) && hash(h) && imported.finalAssetHashes?.[n]===h,'owned asset omitted or changed');
 for(const n of ['Materials/M_PoolCoping.uasset',...Object.keys(roles).map(k=>`Textures/T_${k}.uasset`)])need(hash(r.assetHashes[assetPrefix+n]),'required native asset absent');
 return {status:'pool-coping-package-inputs-validated',selectedIds:ids,recipeSha256:r.recipeSha256,renderedVerified:false};
}
