// CPU receipt/source fixtures. These tests do not execute Unreal or prove appearance.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateOriginalTreeGroupHeader,validateOriginalTreeGroupReportNames,validateOriginalTreeGroupContent} from '../scripts/unreal/exterior-editor-source-r19.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));
const source=path.join(root,'output/unreal/exterior-20261002-r29a'),project=path.join(source,'Project/BreziTwin');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const report=read(path.join(source,'original-tree-group-native-report.json'));

test('actual typed receipt fields satisfy the bounded CPU header contract',()=>{
  validateOriginalTreeGroupHeader(report,{source,project});
  const unsupported=structuredClone(report);unsupported.selectedTreeNaniteRenderPassVerified=true;
  assert.throws(()=>validateOriginalTreeGroupHeader(unsupported,{source,project}));
});

test('duplicate roots and partial original-group retirement reject',()=>{
  for(const mutate of [r=>r.newOriginalTreeGroup.rootIds[1]=r.newOriginalTreeGroup.rootIds[0],r=>r.retiredOriginalGroup.remainingMembers=1]){
    const fixture=structuredClone(report);mutate(fixture);assert.throws(()=>validateOriginalTreeGroupHeader(fixture,{source,project}));
  }
});

test('coexisting copied, failed or unknown native reports reject',()=>{
  const selected='original-tree-group-native-report.json';validateOriginalTreeGroupReportNames([selected,'original-tree-group-native-process.json']);
  for(const other of ['exterior-import-report.json','original-tree-native-report-r2.json','original-tree-group-native-report-r2.json'])
    assert.throws(()=>validateOriginalTreeGroupReportNames([selected,other]));
});

test('exact 17 saved packages plus map accept; foreign original change and changed package reject',()=>{
  const before=read(report.baseContentInventory.path),after=read(report.afterContentInventory.path),packages=read(report.copiedPackages.path);
  validateOriginalTreeGroupContent(before,after,packages,report.assetDelta);
  const old=structuredClone(after),key=Object.keys(before).find(k=>k!=='Brezi/Maps/Brezi.umap');old[key].sha256='0'.repeat(64);
  assert.throws(()=>validateOriginalTreeGroupContent(before,old,packages,report.assetDelta));
  const changed=structuredClone(after);changed[packages[0].relativeContentPath].sha256='0'.repeat(64);
  assert.throws(()=>validateOriginalTreeGroupContent(before,changed,packages,report.assetDelta));
});
