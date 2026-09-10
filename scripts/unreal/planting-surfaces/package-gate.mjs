import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
function rootOf(p){while(!fs.existsSync(path.join(p,'lib/twin-site.ts'))){const n=path.dirname(p);if(n===p)throw Error('Project root unavailable');p=n;}return p;}
const root=rootOf(here), prefix='scripts/unreal/planting-surfaces/', ids=['DOM_01821','DOM_01822'], base='/Game/Brezi/Geometry/brezi-twin/Materials/MAT_0091.MAT_0091';
const sha=v=>crypto.createHash('sha256').update(v).digest('hex');
const hash=v=>typeof v==='string' && /^[0-9a-f]{64}$/.test(v);
const canonical=v=>Array.isArray(v)?v.map(canonical):v && typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const equal=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
function need(ok,message){if(!ok)throw Error('Mulch package gate: '+message);}
export function expectedMulchInputs(){
 const reference=JSON.parse(fs.readFileSync(path.join(here,'inputs.json'),'utf8'));
 const helpers=['scripts/unreal/tv-oak/tv_oak.py',...['lawn_ground','source','graph'].map(n=>`scripts/unreal/lawn-ground/${n}.py`),...['h','cpp'].map(x=>`unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.${x}`)];
 const recipeInputs=Object.fromEntries(['mulch.py','graph.py','inputs.json'].map(n=>[prefix+n,sha(fs.readFileSync(path.join(here,n)))]));
 for(const n of helpers)recipeInputs[n]=sha(fs.readFileSync(path.join(root,n)));
 const pipeline={...recipeInputs,...reference.sourceIntentFiles,...Object.fromEntries(Object.entries(reference.evidence).map(([n,h])=>[prefix+n,h])),...Object.fromEntries(Object.values(reference.maps).map(v=>[v.path,v.sha256])),'scripts/unreal/materials.py':sha(fs.readFileSync(path.join(root,'scripts/unreal/materials.py'))),[prefix+'package-gate.mjs']:sha(fs.readFileSync(path.join(here,'package-gate.mjs')))};
 for(const [n,h] of Object.entries(pipeline)){const p=n.startsWith(prefix)?path.join(here,n.slice(prefix.length)):path.join(root,n);need(fs.realpathSync(p)===p && sha(fs.readFileSync(p))===h,'input changed: '+n);}
 return {reference,recipeInputs,pipeline};
}
export function validateMulchReceipt(imported,expected=expectedMulchInputs()){
 const r=imported.plantingSurfaces;
 need(r?.status==='mulch-saved-reload-validated' && r.nativeApplied===true && r.restoring===false && r.activationStarted===true && r.actorMetadataWritten===false && equal(r.rollbackErrors,[]),'active saved stage absent');
 need(equal(r.selectedIds,ids) && r.sourceMaterialSlot==='MAT_0091' && equal(r.excludedSharedSlotIds,['DOM_01692']),'two-source scope differs');
 need(r.sourceManifestSha256===imported.sourceManifestSha256 && r.sourceManifestSha256===expected.reference.sceneSha256 && r.sourceObjSha256===expected.reference.objSha256,'canonical source differs');
 need(hash(r.recipeSha256) && typeof r.recipeCanonicalJson==='string' && sha(r.recipeCanonicalJson)===r.recipeSha256 && equal(JSON.parse(r.recipeCanonicalJson),r.recipe),'recipe hash differs');
 need(equal(r.recipe,{reference:expected.reference,recipeInputs:expected.recipeInputs}) && equal(r.pipelineFiles,expected.pipeline),'current recipe or pipeline differs');
 for(const [n,h] of Object.entries(expected.pipeline))need(imported.pipelineFiles?.[n]===h,'source missing from import closure: '+n);
 for(const phase of ['stagedReload','activeReload'])for(const flag of ['mapSaved','worldUnloaded','allFourOwnedAssetsAbsentBeforeReload','mapReloaded'])need(r[phase]?.[flag]===true,'saved absence/reload proof absent: '+phase+'/'+flag);
 for(const flag of ['exactTwoBindings','sourceVerticesUv0Unchanged','allOtherActorsAndGrassUnchanged','sourceBaseMaterialRetained','twoMapReloads','twoOwnedAssetUnloadAbsenceReadbacks','exactSavedGraphsEqual'])need(r.verification?.[flag]===true,'native preservation absent: '+flag);
 need(r.grassInstanceCount===33769 && imported.lawnDetail?.instanceCount===33769,'existing lawn detail differs');
 const owned=`/Game/Brezi/PlantingSurfaces/Mulch/R_${r.recipeSha256.slice(0,16)}`,material=owned+'/Materials/M_Mulch.M_Mulch';
 need(equal(Object.keys(r.selectedBefore??{}).sort(),ids) && equal(Object.keys(r.selectedAfter??{}).sort(),ids),'binding count differs');
 for(const [j,id] of ids.entries()){
  const a=r.selectedBefore[id],b=r.selectedAfter[id],mesh=`/Game/Brezi/Geometry/brezi-twin/StaticMeshes/${id}.${id}`;
  need(a.mesh===mesh && b.mesh===mesh && a.meshMaterial===base && b.meshMaterial===base && a.actor===b.actor && a.component===b.component && b.state==='active' && b.effectiveMaterial===material && equal(b.overrides,[material]),'active source binding differs: '+id);
  need((a.state==='source' && a.effectiveMaterial===base && equal(a.overrides,[])) || (a.state==='active' && a.effectiveMaterial===material && equal(a.overrides,[material])),'prior binding foreign: '+id);
  need(equal(a.nativeSnapshot,b.nativeSnapshot) && equal(a.sourceProof,b.sourceProof),'source readback changed: '+id);
  const p=b.sourceProof;need(p?.triangles===[5,3][j] && p.windingMultiplicityVerified===true && p.sourceToleranceMm===.002 && p.uv0Tolerance===.000002 && hash(p.snapshotSha256) && Number.isFinite(p.maximumPositionErrorMm) && p.maximumPositionErrorMm>=0 && p.maximumPositionErrorMm<=.002 && Number.isFinite(p.maximumUv0Error) && p.maximumUv0Error>=0 && p.maximumUv0Error<=.000002,'source position/UV proof missing: '+id);
 }
 const g=r.activeMaterialProof;need(equal(g,r.stagedMaterialProof) && g?.asset===material && g.recipeSha256===r.recipeSha256 && g.nodeCount===8 && g.linkCount===5 && g.textureSampleCount===3,'saved graph differs');
 for(const flag of ['exactGraphVerified','allInputsAccountedFor','worldSpaceNormal','roughnessRawLinear','implicitContinuousGradients','stockAutomaticViewMipBias'])need(g[flag]===true,'graph policy absent: '+flag);
 need(g.tileMm===2000 && g.normalStrength===1 && g.normalGreenFlipCount===1 && g.roughnessRemapped===false && g.sourceUvSampled===false && g.worldPositionOffsetConnected===false && g.pixelDepthOffsetConnected===false && g.metallic===0 && g.specular===.5 && equal(g.tintLinear,[1,1,1]) && equal(g.worldBasis,[[1,0,0],[0,1,0],[0,0,1]]),'physical mapping/PBR policy differs');
 const roles={albedo:'Diffuse',normalMap:'nor_gl',roughMap:'Rough'};need(equal(Object.keys(g.textures??{}).sort(),Object.keys(roles).sort()),'map roles differ');
 for(const [role,input] of Object.entries(roles)){const t=g.textures[role];need(t.asset===`${owned}/Textures/T_${role}.T_${role}` && t.sourceSha256===expected.reference.maps[input].sha256 && equal(t.pixels,[4096,4096]) && t.srgb===(role==='albedo') && t.greenFlipped===(role==='normalMap') && t.wrapXY===true && t.sourceDimensionReadback===true,'native texture proof differs: '+role);}
 const assetPrefix=`unreal/BreziTwin/Content/Brezi/PlantingSurfaces/Mulch/R_${r.recipeSha256.slice(0,16)}/`;
 need(Object.keys(r.assetHashes??{}).length>=4 && Object.keys(r.protectedAssetHashes??{}).length>=1878 && hash(r.sourcePreservationSnapshotSha256),'asset/source preservation receipt absent');
 for(const [n,h] of Object.entries(r.assetHashes))need(n.startsWith(assetPrefix) && hash(h) && imported.finalAssetHashes?.[n]===h,'owned asset omitted or changed');
 for(const n of ['Materials/M_Mulch.uasset',...Object.keys(roles).map(k=>`Textures/T_${k}.uasset`)])need(hash(r.assetHashes[assetPrefix+n]),'required native asset absent');
 for(const [n,h] of Object.entries(r.protectedAssetHashes))need(hash(h) && imported.finalAssetHashes?.[n]===h,'protected native asset changed or omitted');
 return {status:'mulch-package-inputs-validated',selectedIds:ids,recipeSha256:r.recipeSha256,renderedVerified:false};
}
