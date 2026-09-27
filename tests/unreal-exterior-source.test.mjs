import test from 'node:test';
import assert from 'node:assert/strict';
import {validateExteriorReceipt} from '../scripts/unreal/exterior-source.mjs';

function fixture() {
  const a='1'.repeat(64),b='2'.repeat(64),project='/project';
  const map=project+'/Content/Brezi/Maps/Brezi.umap',views=project+'/Content/Data/viewpoints.json';
  const original=project+'/Content/Brezi/Geometry/House.uasset',added=project+'/Content/Brezi/Exterior20260926/Plant.uasset';
  const source={donor:'/donor',content:{[map]:a,[views]:a,[original]:a}};
  const before={sun:{intensity:80000},views:[{id:'interior',eyeCm:[0,0,160]}]};
  const report={schemaVersion:1,owner:'scripts/unreal/exterior-import.py',status:'exterior-import-validated',project,sourceOutput:source.donor,
    activeDesign:{variant:'C',heatingLayout:'B',livingLayout:'B'},setbacksMm:{street:3000,east:3000},
    savedReloaded:true,protectedContentUnchanged:true,sourceGeometryCollisionAndTransformsPreserved:true,originalMaterialAssetsPreserved:true,
    beforeAssetHashes:source.content,afterAssetHashes:{...source.content,[map]:b,[views]:b,[added]:b},newAssets:[added],
    changedAssets:[map,views].map(path=>({path,beforeSha256:a,afterSha256:b})),
    viewpoints:{before,after:{...structuredClone(before),views:[...structuredClone(before.views),{id:'exterior',eyeCm:[100,0,160]}]}},
    originalActorCount:100,finalActorCount:101,addedActors:['new-plant'],
    protectedActorWitnessSha256:a,savedProtectedActorWitnessSha256:a,authoredActorWitnessSha256:b,savedActorWitnessSha256:b,
    savedGeometryReadback:{meshCount:1,instanceCount:20,allNewVisualsNoCollision:true},
    context:{parcelCount:117},materialReadback:{status:'verified-saved-exterior-materials'}};
  return structuredClone({report,source,project,map,views,original,added,a,b});
}

test('exterior receipt accepts additive visuals with unchanged original architecture',()=>{
  const f=fixture();assert.deepEqual(validateExteriorReceipt(f),f.report.afterAssetHashes);
});
test('historical geometry and material packages cannot be rewritten or removed',()=>{
  for(const mutate of [f=>f.report.afterAssetHashes[f.original]=f.b,f=>delete f.report.afterAssetHashes[f.original]]){
    const f=fixture();mutate(f);assert.throws(()=>validateExteriorReceipt(f));
  }
});
test('a changed architectural selection, setback or saved witness rejects promotion',()=>{
  for(const mutate of [f=>f.report.activeDesign.variant='A',f=>f.report.setbacksMm.street=2800,
    f=>f.report.savedProtectedActorWitnessSha256=f.b,f=>f.report.savedActorWitnessSha256=f.a,
    f=>f.report.savedGeometryReadback.allNewVisualsNoCollision=false,f=>f.report.savedReloaded=false]){
    const f=fixture();mutate(f);assert.throws(()=>validateExteriorReceipt(f));
  }
});
test('new cameras cannot change existing views or sunlight',()=>{
  for(const mutate of [f=>f.report.viewpoints.after.views[0].eyeCm[0]=1,
    f=>f.report.viewpoints.after.sun={intensity:100},f=>f.report.viewpoints.after.views[1].id='interior']){
    const f=fixture();mutate(f);assert.throws(()=>validateExteriorReceipt(f));
  }
});
test('new exterior assets cannot escape their namespace',()=>{
  for(const suffix of ['../Other/Plant.uasset','Plant.py','/tmp/Plant.uasset']){
    const f=fixture(),path=f.project+'/Content/Brezi/Exterior20260926/'+suffix;
    f.report.afterAssetHashes[path]=f.b;f.report.newAssets=Object.keys(f.report.afterAssetHashes).filter(p=>!Object.hasOwn(f.source.content,p)).sort();
    assert.throws(()=>validateExteriorReceipt(f));
  }
});
