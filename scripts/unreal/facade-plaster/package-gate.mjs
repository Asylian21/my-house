import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
let root=here;while(!fs.existsSync(path.join(root,'lib/twin-site.ts'))){const parent=path.dirname(root);if(parent===root)throw Error('Plaster root missing');root=parent;}
const owner='scripts/unreal/facade-plaster/plaster.py',base='/Game/Brezi/MaterialsGenerated/M_MAT_0010.M_MAT_0010';
const sceneHash='61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b',objHash='a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455';
const sha=v=>crypto.createHash('sha256').update(v).digest('hex'),hash=v=>typeof v==='string' && /^[a-f0-9]{64}$/.test(v);
const canon=v=>Array.isArray(v)?v.map(canon):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canon(v[k])])):v;
const equal=(a,b)=>JSON.stringify(canon(a))===JSON.stringify(canon(b));
function need(ok,m){if(!ok)throw Error('Plaster package gate: '+m);}
export function expectedPlasterInputs(){
 const source=fs.readFileSync(path.join(root,'output/unreal/geometry/scene.json'));need(sha(source)===sceneHash,'source scene changed');
 need(sha(fs.readFileSync(path.join(root,'output/unreal/geometry/dom-mm.obj')))===objHash,'source OBJ changed');
 const ids=JSON.parse(source).objects.filter(r=>r.materialSlots.includes('MAT_0010')).map(r=>r.id);need(ids.length===66,'source selection changed');
 const helpers=['scripts/unreal/tv-oak/tv_oak.py',...['lawn_ground','source','graph'].map(n=>`scripts/unreal/lawn-ground/${n}.py`),...['h','cpp'].map(x=>`unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.${x}`)];
 const files=Object.fromEntries([owner,'scripts/unreal/materials.py',...helpers].map(n=>{const p=path.join(root,n);need(fs.realpathSync(p)===p,'symlinked input');return [n,sha(fs.readFileSync(p))];}));
 need(files['scripts/unreal/materials.py']==='4f588f2825f555febade35e736663348f94ca0c37e836cc87ca1d7e15b5a15ed','source writer changed');
 const recipe={revision:'FACADE-PLASTER-NORMAL-1',selectedIds:ids,sourceManifestSha256:sceneHash,sourceObjSha256:objHash,baseMaterial:base,normalStrengthBefore:.2,normalStrength:.5,artistNormalWeightNotMeasured:true,recipeInputs:files};
 return {ids,recipe,pipeline:{...files,'scripts/unreal/facade-plaster/package-gate.mjs':sha(fs.readFileSync(path.join(here,'package-gate.mjs')))}};
}
export function validatePlasterReceipt(imported,expected=expectedPlasterInputs()){
 const r=imported.facadePlaster,{ids}=expected;
 if(r?.status==='source-plaster-retained-candidate-rejected'){
  need(r.nativeApplied===false && r.normalStrength===.2 && r.candidateNormalStrength===.5 && r.artistNormalWeightNotMeasured===true,'inactive normal policy differs');
  need(equal(r.selectedIds,ids) && r.sourceMaterialSlot==='MAT_0010' && r.sourceOverridesRetained===66 && r.candidateOverridesActive===0 && r.sourceObjectsDeleted===0,'inactive scope differs');
  need(r.sourceManifestSha256===sceneHash && imported.sourceManifestSha256===sceneHash && r.sourceObjSha256===objHash,'inactive source identity differs');
  need(hash(r.recipeSha256) && typeof r.recipeCanonicalJson==='string' && sha(r.recipeCanonicalJson)===r.recipeSha256 && equal(JSON.parse(r.recipeCanonicalJson),r.recipe) && equal(r.recipe,expected.recipe),'inactive recipe differs');
  need(equal(r.pipelineFiles,expected.pipeline),'inactive current pipeline differs');
  for(const [n,h] of Object.entries(expected.pipeline))need(imported.pipelineFiles?.[n]===h,'inactive missing import pipeline '+n);
  for(const f of ['mapSaved','worldUnloaded','mapReloaded'])need(r.sourceReload?.[f]===true,'inactive saved-map readback absent');
  need(r.sourceStateUnchangedAfterReload===true && hash(r.sourcePreservationSnapshotSha256) && r.grassInstanceCount===33769 && imported.lawnDetail?.instanceCount===33769,'inactive source/lawn preservation absent');
  need(equal(Object.keys(r.selectedAfter??{}).sort(),ids),'inactive exact binding count differs');
  for(const id of ids){const c=r.selectedAfter[id],mesh=`/Game/Brezi/Geometry/brezi-twin/StaticMeshes/${id}.${id}`,proof=c.sourceProof;
   need(c.state==='source' && c.mesh===mesh && c.meshMaterial===base && c.effectiveMaterial===base && equal(c.overrides,[]),'inactive source binding differs '+id);
   need(proof?.windingMultiplicityVerified===true && proof.sourceToleranceMm===.002 && proof.uv0Tolerance===.000002 && hash(proof.snapshotSha256),'inactive source vertex/UV proof absent '+id);
   const file=`unreal/BreziTwin/Content/Brezi/Geometry/brezi-twin/StaticMeshes/${id}.uasset`;
   need(hash(r.protectedAssetHashes?.[file]) && r.protectedAssetHashes[file]===imported.finalAssetHashes?.[file],'inactive source mesh asset absent '+id);
  }
  const g=r.sourceGraph,name=g?.normalMix;
  need(g?.nodeIdentity==='material-output-input-traversal-v1' && g.settings?.naniteUsage===true && g.settings.tangent_space_normal===false && Object.keys(g.nodes??{}).length===16 && name && Math.abs(g.nodes[name]?.properties?.const_alpha-.2)<1e-6,'inactive source material graph differs');
  need(g.textureAssets?.length===3 && Object.keys(g.textureAssetHashes??{}).length===3 && Object.keys(r.protectedAssetHashes??{}).length>=1878 && equal(r.assetHashes,{}),'inactive asset scope differs');
  need(hash(r.protectedAssetHashes['unreal/BreziTwin/Content/Brezi/MaterialsGenerated/M_MAT_0010.uasset']),'inactive base material unpinned');
  for(const [n,h] of Object.entries(r.protectedAssetHashes))need(!n.includes('/MaterialStudies/FacadePlaster/') && hash(h) && imported.finalAssetHashes?.[n]===h,'inactive protected asset changed/missing');
  for(const [n,h] of Object.entries(g.textureAssetHashes))need(hash(h) && r.protectedAssetHashes[n]===h,'inactive source texture unpinned');
  need(r.visualAcceptance==='candidate-rejected-in-two-native-4k-captures' && r.renderedVerified===false,'inactive visual status differs');
  return {status:'plaster-candidate-disabled-source-material-validated',selectedIds:ids,normalStrength:.2,candidateOverridesActive:0,renderedVerified:false};
 }
 need(r?.status==='plaster-saved-reload-validated' && r.nativeApplied===true && r.restoring===false && r.activationStarted===true && r.actorMetadataWritten===false && equal(r.rollbackErrors,[]),'saved active stage absent');
 need(equal(r.selectedIds,ids) && r.sourceMaterialSlot==='MAT_0010' && r.normalStrength===.5 && r.normalStrengthBefore===.2 && r.artistNormalWeightNotMeasured===true,'scope/normal policy differs');
 need(r.sourceManifestSha256===sceneHash && imported.sourceManifestSha256===sceneHash && r.sourceObjSha256===objHash,'source identity differs');
 need(hash(r.recipeSha256) && typeof r.recipeCanonicalJson==='string' && sha(r.recipeCanonicalJson)===r.recipeSha256 && equal(JSON.parse(r.recipeCanonicalJson),r.recipe) && equal(r.recipe,expected.recipe),'recipe differs');
 need(equal(r.pipelineFiles,expected.pipeline),'current pipeline differs');for(const [n,h] of Object.entries(expected.pipeline))need(imported.pipelineFiles?.[n]===h,'missing import pipeline '+n);
 for(const phase of ['stagedReload','activeReload'])for(const f of ['mapSaved','worldUnloaded','ownedMaterialAbsentBeforeReload','mapReloaded'])need(r[phase]?.[f]===true,'saved absence/reload absent');
 for(const f of ['exact66Bindings','sourceVerticesUv0Unchanged','allOtherActorsAndGrassUnchanged','sourceBaseMaterialRetained','twoMapReloads','twoOwnedMaterialUnloadAbsenceReadbacks','exactSavedGraphsEqual'])need(r.verification?.[f]===true,'preservation absent '+f);
 need(r.grassInstanceCount===33769 && imported.lawnDetail?.instanceCount===33769,'lawn preservation differs');
 const prefix=`/Game/Brezi/MaterialStudies/FacadePlaster/R_${r.recipeSha256.slice(0,16)}`,material=prefix+'/M_Plaster.M_Plaster';
 need(equal(Object.keys(r.selectedBefore??{}).sort(),ids) && equal(Object.keys(r.selectedAfter??{}).sort(),ids),'binding count differs');
 for(const id of ids){const a=r.selectedBefore[id],b=r.selectedAfter[id],mesh=`/Game/Brezi/Geometry/brezi-twin/StaticMeshes/${id}.${id}`;
  need(a.mesh===mesh && b.mesh===mesh && a.meshMaterial===base && b.meshMaterial===base && a.actor===b.actor && a.component===b.component && b.state==='active' && b.effectiveMaterial===material && equal(b.overrides,[material]),'binding differs '+id);
  need((a.state==='source' && equal(a.overrides,[]) && a.effectiveMaterial===base)||(a.state==='active' && equal(a.overrides,[material]) && a.effectiveMaterial===material),'foreign prior binding');
  need(equal(a.nativeSnapshot,b.nativeSnapshot) && equal(a.sourceProof,b.sourceProof) && b.sourceProof?.windingMultiplicityVerified===true && b.sourceProof.sourceToleranceMm===.002 && b.sourceProof.uv0Tolerance===.000002 && hash(b.sourceProof.snapshotSha256),'source vertex/UV proof differs');
 }
 const g=r.activeMaterialProof;need(equal(g,r.stagedMaterialProof) && g?.asset===material && g.recipeSha256===r.recipeSha256 && g.normalStrength===.5 && g.sourceNormalStrength===.2 && g.nodeCount===16 && g.textureObjectCount===3 && g.albedoSourceMix===.15 && g.worldTileCm===100 && g.onlyNormalLerpWeightChanged===true && g.nativeGraphGetterVerified===true && g.worldSpaceNormal===true && g.artistNormalWeightNotMeasured===true,'saved material differs');
 const graph=structuredClone(g.sourceGraph),name=graph?.normalMix;need(graph?.settings?.naniteUsage===true && graph.nodeIdentity==='material-output-input-traversal-v1','source Nanite usage or stable graph identity absent');need(name && Object.keys(graph.nodes??{}).length===16 && Math.abs(graph.nodes[name].properties.const_alpha-.2)<1e-6,'source graph proof absent');graph.nodes[name].properties.const_alpha=.5;need(equal(graph,g.savedGraph),'more than normal weight changed');
 const assetPrefix=`unreal/BreziTwin/Content/Brezi/MaterialStudies/FacadePlaster/R_${r.recipeSha256.slice(0,16)}/`;
 need(hash(r.assetHashes?.[assetPrefix+'M_Plaster.uasset']) && Object.keys(r.protectedAssetHashes??{}).length>=1878 && hash(r.sourcePreservationSnapshotSha256),'saved asset preservation absent');
 for(const [n,h] of Object.entries(r.assetHashes))need(n.startsWith(assetPrefix) && hash(h) && imported.finalAssetHashes?.[n]===h,'owned asset changed/missing');
 for(const [n,h] of Object.entries(r.protectedAssetHashes))need(hash(h) && imported.finalAssetHashes?.[n]===h,'protected asset changed/missing');
 for(const [n,h] of Object.entries(g.sourceGraph.textureAssetHashes??{}))need(hash(h) && r.protectedAssetHashes[n]===h && imported.finalAssetHashes?.[n]===h,'source texture changed/missing');
 return {status:'plaster-package-inputs-validated',selectedIds:ids,recipeSha256:r.recipeSha256,normalStrength:.5,renderedVerified:false};
}
