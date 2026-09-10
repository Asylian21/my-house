import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const hash = x => typeof x === 'string' && /^[a-f0-9]{64}$/.test(x);
const need = (x,m) => {if (!x) throw new Error(`Lawn ground: ${m}`);};
const stable = x => Array.isArray(x) ? x.map(stable) : x && typeof x === 'object' ? Object.fromEntries(Object.keys(x).sort().map(k => [k,stable(x[k])])) : x;
const equal = (a,b) => JSON.stringify(stable(a)) === JSON.stringify(stable(b));
const owner = 'scripts/unreal/lawn-ground/lawn_ground.py';
const base = '/Game/Brezi/MaterialsGenerated/M_MAT_0001.M_MAT_0001';
const mesh = '/Game/Brezi/Geometry/brezi-twin/StaticMeshes/DOM_00001.DOM_00001';
export function expectedLawnGroundInputs(here=path.dirname(fileURLToPath(import.meta.url))) {
  let root=here;
  while (!fs.existsSync(path.join(root,'lib/twin-site.ts'))) {const parent=path.dirname(root);need(parent!==root,'project root absent');root=parent;}
  const ref=JSON.parse(fs.readFileSync(path.join(here,'reference.json'),'utf8'));
  const files={};
  for (const name of ['lawn_ground.py','graph.py','source.py','shading.py','reference.json']) files[`scripts/unreal/lawn-ground/${name}`]=sha(fs.readFileSync(path.join(here,name)));
  for (const name of ['scripts/unreal/tv-oak/tv_oak.py','unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.h','unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.cpp']) files[name]=sha(fs.readFileSync(path.join(root,name)));
  const pipeline={...files,...ref.sourceIntentFiles,...ref.evidence,...Object.fromEntries(Object.values(ref.maps).map(v=>[v.path,v.sha256]))};
  for (const name of ['restore_inputs.py','package-gate.mjs']) pipeline[`scripts/unreal/lawn-ground/${name}`]=sha(fs.readFileSync(path.join(here,name)));
  pipeline['scripts/unreal/materials.py']=sha(fs.readFileSync(path.join(root,'scripts/unreal/materials.py')));
  for (const [file,wanted] of Object.entries(pipeline)) {
    const local=file.startsWith('scripts/unreal/lawn-ground/') ? path.join(here,file.slice('scripts/unreal/lawn-ground/'.length)) : path.join(root,file);
    need(fs.realpathSync(local)===local && sha(fs.readFileSync(local))===wanted,`source/evidence/map drift: ${file}`);
  }
  return {reference:ref,recipeInputs:files,pipeline};
}
export function validateLawnGroundReceipt(imported,expected=expectedLawnGroundInputs()) {
  const r=imported.lawnGround;
  need(r?.status==='lawn-ground-saved-reload-validated' && r.nativeApplied===true && r.restoring===false,'saved active candidate absent');
  need(hash(r.recipeSha256) && r.sourceObjectId==='DOM_00001' && r.sourceMaterialSlot==='MAT_0001' && r.sourceManifestSha256===imported.sourceManifestSha256 && r.sourceManifestSha256===expected.reference.sceneSha256 && r.sourceObjSha256===expected.reference.objSha256,'source scope differs');
  need(typeof r.recipeCanonicalJson==='string' && sha(r.recipeCanonicalJson)===r.recipeSha256 && equal(JSON.parse(r.recipeCanonicalJson),r.recipe),'recipe byte hash differs');
  need(equal(r.recipe?.reference,expected.reference) && equal(r.recipe?.recipeInputs,expected.recipeInputs),'current artist-effective turf recipe differs');
  need(equal(r.pipelineFiles,expected.pipeline),'pipeline closure differs');
  for (const [file,digest] of Object.entries(expected.pipeline)) need(hash(digest) && imported.pipelineFiles?.[file]===digest,`source omitted from final closure: ${file}`);
  for (const phase of ['stagedReload','activeReload']) need(r[phase]?.mapSaved===true && r[phase].worldUnloaded===true && r[phase].mapReloaded===true && r[phase].allFourOwnedAssetsAbsentBeforeReload===true,'real saved asset/map roundtrip absent');
  for (const flag of ['nativeSourceVerticesUv0Compared','geometryUvCollisionAndSourceAssetsUnchanged','other1877SourceActorsUnchanged','allGrassInstancesAndPolicyUnchanged','sourceBaseMaterialRetained','twoMapReloads','twoOwnedAssetUnloadAbsenceReadbacks','exactSavedGraphsEqual','activeBindingVerified']) need(r.verification?.[flag]===true,`native proof absent: ${flag}`);
  need(r.actorMetadataWritten===false && r.grassInstanceCount===33769 && imported.lawnDetail?.instanceCount===33769,'grass preservation or closed metadata scope differs');
  const prefix=`/Game/Brezi/LawnGround/R_${r.recipeSha256.slice(0,16)}`;
  const material=`${prefix}/Materials/M_LawnGround.M_LawnGround`;
  const before=r.selectedBefore,after=r.selectedAfter;
  need(before?.mesh===mesh && after?.mesh===mesh && before.meshMaterial===base && after.meshMaterial===base && after.state==='active' && after.effectiveMaterial===material && equal(after.overrides,[material]),'active final component binding differs');
  need((before.state==='source' && before.effectiveMaterial===base && equal(before.overrides,[])) || (before.state==='active' && before.effectiveMaterial===material && equal(before.overrides,[material])),'prior component binding is neither canonical nor exactly owned');
  need(before.actor===after.actor && before.component===after.component && equal(before.nativeSnapshot,after.nativeSnapshot) && equal(before.sourceProof,after.sourceProof),'native source geometry/UV readback differs');
  const proof=after.sourceProof;
  need(proof?.triangles===27 && proof.windingMultiplicityVerified===true && proof.sourceToleranceMm===.002 && proof.uv0Tolerance===.000002 && Number.isFinite(proof.maximumPositionErrorMm) && proof.maximumPositionErrorMm>=0 && proof.maximumPositionErrorMm<=.002 && Number.isFinite(proof.maximumUv0Error) && proof.maximumUv0Error>=0 && proof.maximumUv0Error<=.000002 && hash(proof.snapshotSha256),'source coordinate proof absent');
  const g=r.activeMaterialProof;
  need(equal(g,r.stagedMaterialProof) && g.asset===material && g.recipeSha256===r.recipeSha256 && g.nodeCount===24 && g.linkCount===48 && g.exactGraphVerified===true && g.textureSampleCount===9 && g.phaseCount===3,'saved graph proof differs');
  need(g.allGraphInputsAccountedFor===true && g.stockAutomaticViewMipBias===true && g.samplerSource==='SSM_FROM_TEXTURE_ASSET' && g.sameWeightsAndOffsetsAllMaps===true && g.continuousUvGradients===true && g.tangentSpaceNormal===true && g.normalRotationApplied===false && g.normalStrength===1 && g.roughnessInputMapLinear===true && g.roughnessInputInvertGammaOrSquare===false && g.roughnessRemapApplied===true && equal(g.effectiveRoughness,expected.reference.material.roughness) && !Object.hasOwn(g,'roughnessMapDirectLinear') && !Object.hasOwn(g,'roughnessInvertGammaSquareOrRemap') && equal(g.artistTintLinear,[1,1,1]) && g.naniteUsage===true && g.pixelDepthOffsetConnected===false && g.worldPositionOffsetConnected===false,'PBR/derivative/geometry policy differs');
  const roles={albedo:'Diffuse',normalMap:'nor_gl',roughMap:'Rough'};
  need(equal(Object.keys(g.textures).sort(),Object.keys(roles).sort()),'texture roles differ');
  for (const [role,input] of Object.entries(roles)) {
    const t=g.textures[role];need(t.asset===`${prefix}/Textures/T_${role}.T_${role}` && t.sourceSha256===expected.reference.maps[input].sha256 && equal(t.pixels,[4096,4096]) && t.srgb===(role==='albedo') && t.greenFlipped===(role==='normalMap') && t.wrapXY===true && t.sourceDimensionReadback===true,'texture source/normal/linear colour readback differs');
  }
  const assetPrefix=`unreal/BreziTwin/Content/Brezi/LawnGround/R_${r.recipeSha256.slice(0,16)}/`;
  need(Object.keys(r.assetHashes??{}).length>=4 && Object.keys(r.protectedAssetHashes??{}).length>=1878 && hash(r.sourcePreservationSnapshotSha256),'saved asset proof missing');
  for (const [file,digest] of Object.entries(r.assetHashes)) need(file.startsWith(assetPrefix) && hash(digest) && imported.finalAssetHashes?.[file]===digest,'owned material asset omitted or changed');
  for (const required of [`${assetPrefix}Materials/M_LawnGround.uasset`,...Object.keys(roles).map(role=>`${assetPrefix}Textures/T_${role}.uasset`)]) need(hash(r.assetHashes[required]),'required saved asset absent');
  for (const [file,digest] of Object.entries(r.protectedAssetHashes)) need(hash(digest) && imported.finalAssetHashes?.[file]===digest,'protected source asset changed or omitted');
  return {status:'lawn-ground-package-inputs-validated',sourceObjectId:'DOM_00001',recipeSha256:r.recipeSha256,renderedVerified:false};
}
