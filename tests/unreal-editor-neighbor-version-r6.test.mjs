// Selected-version CPU fixture only. No native launch, captured-image or
// appearance/performance/package acceptance is established by these tests.
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateNeighborNativeVersion} from '../scripts/unreal/exterior-editor-source-r6.mjs';
const root=fileURLToPath(new URL('../',import.meta.url)).replace(/\/$/,''),source=path.join(root,'output/unreal/exterior-20261001-r18b');
const owner='scripts/unreal/exterior-neighbor-finish-native-r3.py';
const report={schemaVersion:3,owner,status:'neighbor-finish-native-overlay-validated',nativeApplied:true,savedReloaded:true,
  pipelineFiles:{[path.join(root,owner)]:'5a64d2413944cd009d74f5bba7c99b6be4f7f2a04d23f88396366062ebe856ac'}};
test('CPU R18b selection rejects mixed old owner/schema, failed status and rehashed helper claims',()=>{
  validateNeighborNativeVersion(report,source,{root});
  for(const changed of [{...report,owner:'scripts/unreal/exterior-neighbor-finish-native-r2.py'},
    {...report,schemaVersion:2},{...report,status:'neighbor-finish-native-overlay-failed'},
    {...report,pipelineFiles:{[path.join(root,owner)]:'0'.repeat(64)}}])
    assert.throws(()=>validateNeighborNativeVersion(changed,source,{root}));
  assert.throws(()=>validateNeighborNativeVersion(report,path.join(root,'output/unreal/exterior-20261001-r18a'),{root}));
});
