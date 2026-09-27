import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {validateRealismReceipt,authoredRenderCapability,modelRenderProfileArgs} from '../scripts/unreal/realism-source.mjs';

const hash='a'.repeat(64),next='b'.repeat(64);
function fixture() {
  const project='/workspace/output/unreal/new/Project/BreziTwin',content=project+'/Content';
  const map=content+'/Brezi/Maps/Brezi.umap',mesh=content+'/Brezi/Geometry/Wall.uasset',asset=content+'/Brezi/Realism/M_Wall.uasset';
  const source={donor:'/workspace/output/unreal/donor',content:{[map]:hash,[mesh]:hash}};
  const changes=[{actor:'actor',component:'component',slot:0,before:'/Game/Old.Old',after:'/Game/Brezi/Realism/M_Wall.M_Wall'}];
  const report={schemaVersion:1,owner:'scripts/unreal/realism-import.py',status:'realism-import-validated',project,sourceOutput:source.donor,
    savedReloaded:true,protectedContentUnchanged:true,sourceTransformsMeshCollisionAndInstancesPreserved:true,
    beforeAssetHashes:source.content,afterAssetHashes:{[map]:next,[mesh]:hash,[asset]:next},newAssets:[asset],
    changedAssets:[{path:map,beforeSha256:hash,afterSha256:next}],protectedActorWitnessSha256:hash,savedProtectedActorWitnessSha256:hash,
    authoredActorWitnessSha256:next,savedActorWitnessSha256:next,originalActorCount:2,finalActorCount:3,addedActors:['cloud'],
    materialBindingChanges:changes,materials:{bindingChanges:changes},savedMaterialReadback:{status:'checked'},savedEnvironmentReadback:{status:'checked'},
    ownedAssets:['/Game/Brezi/Realism/M_Wall.M_Wall']};
  return {report,source,project,map,mesh,asset};
}
test('additive realism accepts new owned assets plus map overrides with unchanged source mesh',()=>{
  const f=fixture();assert.deepEqual(validateRealismReceipt(f),f.report.afterAssetHashes);
});
test('realism refuses original mesh/material/data byte mutation and removal',()=>{
  for(const deleted of [false,true]) {
    const f=fixture();if(deleted)delete f.report.afterAssetHashes[f.mesh];else f.report.afterAssetHashes[f.mesh]=next;
    assert.throws(()=>validateRealismReceipt(f),/original Content|protected source/);
  }
});
test('new assets cannot escape owned namespace through a sibling, traversal or side file',()=>{
  for(const path of ['Brezi/Other/X.uasset','Brezi/Realism/../Other/X.uasset','Brezi/Realism/script.py']) {
    const f=fixture(),file=f.project+'/Content/'+path;f.report.afterAssetHashes[file]=next;f.report.newAssets.push(file);
    assert.throws(()=>validateRealismReceipt(f),/namespace|Noncanonical|Unexpected/);
  }
});
test('realism requires native saved/reloaded invariants and matching protected witnesses',()=>{
  for(const mutate of [r=>r.savedReloaded=false,r=>r.savedProtectedActorWitnessSha256=next,r=>r.savedActorWitnessSha256=hash]) {
    const f=fixture();mutate(f.report);assert.throws(()=>validateRealismReceipt(f));
  }
});
test('all newly saved packages and all original changes must be reported',()=>{
  for(const mutate of [r=>r.newAssets=[],r=>r.ownedAssets=[],r=>r.changedAssets=[],r=>r.changedAssets[0].beforeSha256=next]) {
    const f=fixture();mutate(f.report);assert.throws(()=>validateRealismReceipt(f));
  }
});
test('material deltas cannot point outside namespace, duplicate a slot, or differ from module audit',()=>{
  for(const mutate of [r=>r.materialBindingChanges[0].after='/Game/Source.Source',
    r=>r.materialBindingChanges.push({...r.materialBindingChanges[0]}),r=>r.materials={bindingChanges:[]}]) {
    const f=fixture();mutate(f.report);assert.throws(()=>validateRealismReceipt(f));
  }
});
test('Cinematic launch is bound to the compiled native recipe and package pins',()=>{
  const path='/prepared/Source/BreziRenderQualityPolicy.h';
  const bytes=Buffer.from('inline constexpr int RecipeRevision = 3; enum class Profile { Native, Balanced, Performance, Cinematic };');
  const pins={[path]:createHash('sha256').update(bytes).digest('hex')};
  const capability=authoredRenderCapability(bytes,path,pins);
  assert.deepEqual(modelRenderProfileArgs('cinematic',capability,pins),['-BreziRenderProfile=cinematic']);
  assert.deepEqual(modelRenderProfileArgs('tsr67',capability,pins),['-BreziRenderProfile=balanced']);
  assert.deepEqual(modelRenderProfileArgs(undefined,undefined,{}),[]);
  assert.throws(()=>modelRenderProfileArgs('cinematic',capability,{}),/provenance/);
  assert.throws(()=>authoredRenderCapability(bytes,path,{[path]:hash}),/compiled source pins/);
});
test('legacy recipe cannot advertise or launch Cinematic, and arbitrary names are rejected',()=>{
  const path='/policy',bytes=Buffer.from('inline constexpr int RecipeRevision = 2; enum class Profile { Native, Balanced, Performance };');
  const pins={[path]:createHash('sha256').update(bytes).digest('hex')},cap=authoredRenderCapability(bytes,path,pins);
  assert(!cap.profiles.includes('cinematic'));assert.throws(()=>modelRenderProfileArgs('cinematic',cap,pins),/advertise/);
  assert.throws(()=>modelRenderProfileArgs('ultra',cap,pins),/Unknown/);
});
