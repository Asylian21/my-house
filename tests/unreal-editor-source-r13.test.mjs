import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateCleanHeader,validateCleanContent,validateCleanGrassControls,validateCleanReportNames} from '../scripts/unreal/exterior-editor-source-r13.mjs';
const root=fileURLToPath(new URL('../',import.meta.url)),source=path.join(root,'output/unreal/exterior-20261002-r27a');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),r=read(path.join(source,'realism-clean-integration-native-report.json'));
const options={source,project:path.join(source,'Project/BreziTwin')},plan=read(r.selectedPlan.path);

test('actual successful R27 header rejects failed/running/foreign receipts and evidence upgrades',()=>{
  validateCleanHeader(r,options);
  for(const[k,v]of [['status','failed'],['status','running'],['owner','scripts/unreal/exterior-realism-integration-native-r22-r3.py'],
    ['schema','brezi-exterior-realism-saved-donor-integration-r22'],['nativeProcessId',1],['nativeAppearanceAccepted',true],
    ['nativeNormalTangentReadbackAvailable',true],['nativeMaterialPackagesIndependentlyReloaded',true]]){
    const bad=structuredClone(r);bad[k]=v;assert.throws(()=>validateCleanHeader(bad,options));
  }
});

test('clean scope preserves original grass and rejects excluded R20/R23 donors or saved census drift',()=>{
  for(const[k,v]of [['originalGrassMemberMutationApisCalled',true],['seedRangeMutationApisCalled',true],
    ['actualFullSceneHismComponents',2312],['actualRecordedExteriorHismGroups',1987],['scopedTextureObjects',84],['excludedDonors',[]]]){
    const bad=structuredClone(r);bad[k]=v;assert.throws(()=>validateCleanHeader(bad,options));
  }
  const bad=structuredClone(r);bad.savedDonors.grass={};assert.throws(()=>validateCleanHeader(bad,options));
});

test('exact 59-package map and pinned-camera delta rejects original asset edits',()=>{
  const before=read(plan.baseContentInventory.path),after=read(r.afterContentInventory.path),packages=read(plan.copiedPackages.path);
  validateCleanContent(before,after,packages,r.assetDelta,plan.diagnosticViewpoints.sha256);
  const bad=structuredClone(after),key=Object.keys(before).find(k=>k!=='Brezi/Maps/Brezi.umap'&&k!=='Data/viewpoints.json');
  bad[key].sha256='0'.repeat(64);assert.throws(()=>validateCleanContent(before,bad,packages,r.assetDelta,plan.diagnosticViewpoints.sha256));
  assert.throws(()=>validateCleanContent(before,after,packages,r.assetDelta,'0'.repeat(64)));
});

test('copied package membership forbids excluded experimental namespaces and duplicate packages',()=>{
  const before=read(plan.baseContentInventory.path),after=read(r.afterContentInventory.path),packages=read(plan.copiedPackages.path);
  const bad=structuredClone(packages);bad[0].relativeContentPath='Brezi/CurvedGrass20261002R20/Meshes/x.uasset';
  assert.throws(()=>validateCleanContent(before,after,bad,r.assetDelta,plan.diagnosticViewpoints.sha256));
  const duplicate=structuredClone(packages);duplicate[0]=duplicate[1];
  assert.throws(()=>validateCleanContent(before,after,duplicate,r.assetDelta,plan.diagnosticViewpoints.sha256));
});

test('all8949 raw grass matrices, main seeds and custom data stay exact across save',()=>{
  const before=read(r.originalGrassControlsBefore.path),saved=read(r.originalGrassControlsSaved.path);validateCleanGrassControls(before,saved);
  for(const[k,v]of [['rawMatrixBinary64Sha256','0'.repeat(64)],['instancingRandomSeed',7],['customDataSha256','0'.repeat(64)],['instances',2229]]){
    const bad=structuredClone(saved);
    bad['EX_meadow_-3_2_LawnTuft0'][k]=v;assert.throws(()=>validateCleanGrassControls(before,bad));
  }
});

test('unreadable protected grass seed ranges cannot be promoted to verified preservation',()=>{
  const before=read(r.originalGrassControlsBefore.path),bad=structuredClone(before);
  bad['EX_meadow_-3_2_LawnTuft0'].additionalRandomSeeds.rangePreservationClaimed=true;
  assert.throws(()=>validateCleanGrassControls(bad,bad));
});

test('candidate requires its own known receipt and rejects copied base/donor/previous receipts',()=>{
  validateCleanReportNames(['realism-clean-integration-native-report.json','realism-clean-integration-native-process.json']);
  for(const name of ['exterior-import-report.json','realism-integration-native-report-r3.json','neighbor-finish-overlay-report-r3.json','foreground-overlay-report-r2.json'])
    assert.throws(()=>validateCleanReportNames(['realism-clean-integration-native-report.json',name]));
  assert.throws(()=>validateCleanReportNames(['realism-clean-integration-native-report-r2.json']));
});
