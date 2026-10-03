import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {validateIntegratedHeader,validateIntegratedContent,validateIntegratedReportNames,loadEditorSourceEvidence} from '../scripts/unreal/exterior-editor-source-r10.mjs';
const root=process.cwd(),source=path.join(root,'output/unreal/exterior-20261002-r22c'),project=path.join(source,'Project/BreziTwin');
const read=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const r=await read(path.join(source,'realism-integration-native-report-r3.json'));
const plan=await read(r.selectedPlan.path),before=await read(plan.baseContentInventory.path),after=await read(r.afterContentInventory.path),packages=await read(plan.copiedPackages.path);

test('actual saved R22 R3 header keeps full/recorded census and false acceptance',()=>{
  validateIntegratedHeader(r,{source,project});
});
test('old native owner, widened claims and confused populations are rejected',()=>{
  for(const[key,value]of [['owner','scripts/unreal/exterior-realism-integration-native-r22-r2.py'],['performanceAccepted',true],['savedMapUnloadedReloaded',false],['actualFullSceneHismInstances',632538]]){
    const changed=structuredClone(r);changed[key]=value;assert.throws(()=>validateIntegratedHeader(changed,{source,project}));
  }
});
test('actual74-copy/map-plus-camera Content delta is exact',()=>{
  validateIntegratedContent(before,after,packages,r.assetDelta,plan.diagnosticViewpoints.sha256);
});
test('original asset edits and copied package byte changes are rejected',()=>{
  const oldKey=Object.keys(before).find(k=>!['Brezi/Maps/Brezi.umap','Data/viewpoints.json'].includes(k));
  for(const key of [oldKey,packages[0].relativeContentPath]){
    const changed=structuredClone(after);changed[key].sha256='0'.repeat(64);
    assert.throws(()=>validateIntegratedContent(before,changed,packages,r.assetDelta,plan.diagnosticViewpoints.sha256));
  }
});
test('failed R22b native report cannot fall through to an older source reader',async()=>{
  await assert.rejects(loadEditorSourceEvidence(path.join(root,'output/unreal/exterior-20261002-r22b'),{root}));
});

test('plain R1 and previous repaired report coexistence is rejected',()=>{
  const selected='realism-integration-native-report-r3.json';validateIntegratedReportNames([selected,'realism-integration-native-r3.log']);
  for(const previous of ['realism-integration-native-report.json','realism-integration-native-report-r2.json','exterior-import-report.json'])
    assert.throws(()=>validateIntegratedReportNames([selected,previous]));
});
