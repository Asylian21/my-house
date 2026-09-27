import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validateStoveCalibrationReceipt,originalFlameMaterial as old,calibratedFlameMaterial as calibrated} from '../scripts/unreal/realism-stove-calibration-source.mjs';
const a='1'.repeat(64),b='2'.repeat(64);
function fixture() {
  const native=JSON.parse(readFileSync(new URL('../output/unreal/realism-20260926-r6/realism-stove-report.json',import.meta.url)));
  const project='/project',map=project+'/Content/Brezi/Maps/Brezi.umap',clone=project+'/Content/Brezi/Realism/StoveCalibration/Materials/M_Stove_Flames_512.uasset';
  const source={donor:'/donor',content:{[map]:a,[project+'/Content/Original.uasset']:a}};
  const original=native.savedMaterialReadback.graphs[old],graph=structuredClone(original);
  const node=graph.nodes.find(n=>n.role==='BreziRealismStove:density-weighted-fire-emission');node.values.code=node.values.code.replace('return tint*Density*3.0;','return tint*Density*512.0;');
  const sourceTarget=native.objects.RFIRE_FLAMES;
  const bindingChanges=[{actor:sourceTarget.actor,component:sourceTarget.component,slot:0,before:old,after:calibrated}];
  const diagnostic={blendMode:'ADDITIVE',shadingModel:'UNLIT',translucencyPass:'AFTER_DOF',refractionMethod:'NONE',refractionInputConnected:false,translucencyLightingMode:'VOLUME',disableDepthTest:false,sortPriority:0,sortDistanceOffset:0};
  const material={sourceTarget,sourceMaterialGraph:original,bindingChanges,ownedAssets:[calibrated],originalGraphs:{[old]:original},protectedGraphs:{[old]:original},
    materials:{[calibrated]:{sourceAsset:old,graph,recipe:{before:3,after:512,exposureCompensation:false,otherGraphChanges:false}}},
    diagnosticsBefore:{flames:diagnostic,glass:diagnostic},diagnosticsAfter:{flames:diagnostic,glass:diagnostic}};
  const report={schemaVersion:1,owner:'scripts/unreal/realism-stove-calibration-import.py',status:'realism-stove-calibration-validated',project,sourceOutput:source.donor,
    savedReloaded:true,protectedContentUnchanged:true,sourceGeometryCollisionAndTransformsPreserved:true,originalMaterialsPreserved:true,originalLightingExposureAndGlassPreserved:true,
    emissionBefore:3,emissionAfter:512,bindingChanges,material,savedMaterialReadback:{...material,status:'saved-reloaded-validated',savedReloaded:true,diagnosticsReloaded:material.diagnosticsAfter},
    originalActorCount:2788,finalActorCount:2788,protectedActorWitnessSha256:a,savedProtectedActorWitnessSha256:a,authoredActorWitnessSha256:a,savedActorWitnessSha256:a,
    beforeAssetHashes:source.content,afterAssetHashes:{...source.content,[map]:b,[clone]:b},newAssets:[clone],changedAssets:[{path:map,beforeSha256:a,afterSha256:b}]};
  return JSON.parse(JSON.stringify({report,source,project,map,clone}));
}
test('accepts actual R6 graph with only one emission scalar, one clone and one binding',()=>{
  const f=fixture();assert.deepEqual(validateStoveCalibrationReceipt(f),f.report.afterAssetHashes);
});
test('rejects graph texture, UV, tint, blend or extra shader changes',()=>{
  for(const change of [g=>g.flags.twoSided=false,g=>g.nodes.find(n=>n.role.includes('flame-card-uv')).values.v_tiling=-1,
    g=>g.nodes.find(n=>n.role.includes('density-weighted-fire-emission')).values.code+='\n',g=>g.roots.EmissiveColor='wrong']) {
    const f=fixture();change(f.report.material.materials[calibrated].graph);assert.throws(()=>validateStoveCalibrationReceipt(f));
  }
});
test('rejects other bindings, scalar choices, absent diagnostics and pass/sort mutations',()=>{
  for(const change of [f=>f.report.bindingChanges.push(f.report.bindingChanges[0]),f=>f.report.material.materials[calibrated].recipe.after=256,
    f=>delete f.report.material.diagnosticsBefore.glass.translucencyPass,f=>f.report.savedMaterialReadback.diagnosticsReloaded.flames.sortPriority=1,
    f=>f.report.originalLightingExposureAndGlassPreserved=false]) {
    const f=fixture();change(f);assert.throws(()=>validateStoveCalibrationReceipt(f));
  }
});
test('rejects modified original bytes, extra assets, changed actors and missing saved witness',()=>{
  for(const change of [f=>f.report.afterAssetHashes[f.project+'/Content/Original.uasset']=b,f=>f.report.afterAssetHashes['/project/Content/other.uasset']=b,
    f=>f.report.finalActorCount++,f=>f.report.savedProtectedActorWitnessSha256=b]) {
    const f=fixture();change(f);assert.throws(()=>validateStoveCalibrationReceipt(f));
  }
});
