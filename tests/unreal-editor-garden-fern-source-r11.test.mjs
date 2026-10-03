// Actual saved receipts and adversarial fixtures; no new native/visual proof.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {validateFernHeader,validateFernContent,validateFernReportNames,loadEditorSourceEvidence} from '../scripts/unreal/exterior-editor-source-r11.mjs';
const root=process.cwd(),source=path.join(root,'output/unreal/exterior-20261002-r25b'),project=path.join(source,'Project/BreziTwin');
const read=async f=>JSON.parse(await fs.readFile(f,'utf8'));
const report=await read(path.join(source,'garden-fern-native-report-r2.json')),base=await read(report.baseNativeReport.path);
const before=await read(base.afterContentInventory.path),after=await read(report.afterContentInventory.path);
const packages=[report.changedComponent.afterMesh,report.materialReport.asset,...Object.values(report.materialReport.textures).map(r=>r.asset),...report.importPipelineAssets]
  .map(p=>p.split('.')[0].replace(/^\/Game\//,'')+'.uasset');
test('actual saved one-root R25b R2 header distinguishes smaller original shape and full scene',()=>validateFernHeader(report,{source,project}));
test('wrong owner, unsupported acceptance, mixed scene census and absent saved proof fail closed',()=>{
  for(const[key,value]of [['owner','scripts/unreal/exterior-garden-fern-native-r25.py'],['fullPhotorealismAccepted',true],['actualFullHismInstances',632538],['savedMapUnloadedReloaded',false]]){
    const r=structuredClone(report);r[key]=value;assert.throws(()=>validateFernHeader(r,{source,project}));
  }
  const r=structuredClone(report);r.nativeMeshReadback.lodProofs[1].triangles=2383;assert.throws(()=>validateFernHeader(r,{source,project}));
});
test('actual nine-package map-only original Content delta preserves camera and all old assets',()=>validateFernContent(before,after,packages,report.assetDelta));
test('camera edit, protected package edit and extra new asset fail',()=>{
  for(const key of ['Data/viewpoints.json',Object.keys(before).find(k=>k.endsWith('.uasset'))]){
    const changed=structuredClone(after);changed[key].sha256='0'.repeat(64);assert.throws(()=>validateFernContent(before,changed,packages,report.assetDelta));
  }
  const extra=structuredClone(after);extra['Brezi/GardenFern20261002R25/foreign.uasset']={sha256:'0'.repeat(64),bytes:1};assert.throws(()=>validateFernContent(before,extra,packages,report.assetDelta));
});
test('plain old fern report or copied native base coexistence is rejected',()=>{
  const selected='garden-fern-native-report-r2.json';validateFernReportNames([selected]);
  for(const name of ['garden-fern-native-report.json','exterior-import-report.json','realism-integration-native-report-r3.json'])assert.throws(()=>validateFernReportNames([selected,name]));
});
test('actual failed R25a cannot fall through to frozen prior reader',async()=>assert.rejects(loadEditorSourceEvidence(path.join(root,'output/unreal/exterior-20261002-r25a'),{root})));
