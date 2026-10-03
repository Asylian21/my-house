import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateRepairHeader,validateRepairReportNames,validateRepairContent,validateCameraStageHeader,
 validateYardCameraViews,loadEditorSourceEvidence,SCHEMA,REPORT_SHA,CAMERA_SCHEMA,STAGE_STATUS,SUPPLEMENT_SHA,VIEW}
 from '../scripts/unreal/exterior-editor-source-r26.mjs';
const root=fileURLToPath(new URL('../',import.meta.url)),source=path.join(root,'output/unreal/exterior-20261002-r35b');
const qa=path.join(root,'output/unreal/exterior-20261002-r35b-yard-close-candidate-r26');
const read=async p=>JSON.parse(await fs.readFile(p));
const report=await read(path.join(source,'context-yard-repair-native-report-r2.json'));
const before=await read(report.baseContentInventory.path),after=await read(report.afterContentInventory.path);
const packages=report.newPackages.map(v=>v.split('.')[0].replace(/^\/Game\//,'')+'.uasset');
const camera=await read(path.join(root,'output/unreal/exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json'));
const originalViews=await read(camera.originalViewpoints.path),appendedViews=await read(camera.appendedViewpoints.path);
const context={source,project:path.join(source,'Project/BreziTwin')};
test('actual executed R35R2 header remains source/native proof with false visual flags',()=>validateRepairHeader(report,context));
test('R1/failed/unknown owners, native PID and acceptance mutations reject',()=>{
 for(const[k,v]of [['owner','scripts/unreal/exterior-context-yard-repair-native-r35.py'],['status','failed'],['nativeProcessId',34679],['nativeAppearanceAccepted',true],['AdditionalRandomSeedsReadbackAvailable',true]]){
  const changed=structuredClone(report);changed[k]=v;assert.throws(()=>validateRepairHeader(changed,context));
 }
});
test('copied plain R1, unrelated donor and unknown report names reject',()=>{
 const selected='context-yard-repair-native-report-r2.json';validateRepairReportNames([selected,'root-native-success-byte-audit-r35b-r1.json']);
 for(const name of ['context-yard-repair-native-report.json','context-yard-ground-native-report.json','exterior-import-report.json','unknown-overlay-report.json'])assert.throws(()=>validateRepairReportNames([selected,name]));
 assert.throws(()=>validateRepairReportNames(['context-yard-repair-native-report.json']));
});
test('actual Content is only original map and six own packages',()=>validateRepairContent(before,after,packages,report.assetDelta));
test('extra package, modified camera, removed original or undeclared old asset rejects',()=>{
 const extra=structuredClone(after);extra['Brezi/ContextYardRepair20261002R35/foreign.uasset']={sha256:'a'.repeat(64),bytes:1};
 assert.throws(()=>validateRepairContent(before,extra,packages,report.assetDelta));
 for(const key of ['Data/viewpoints.json',Object.keys(before).find(k=>k.endsWith('.uasset')&&k!=='Brezi/Maps/Brezi.umap')]){
  const changed=structuredClone(after);changed[key]={sha256:'b'.repeat(64),bytes:123};assert.throws(()=>validateRepairContent(before,changed,packages,report.assetDelta));
 }
 const missing=structuredClone(after);delete missing[Object.keys(before)[0]];assert.throws(()=>validateRepairContent(before,missing,packages,report.assetDelta));
});
test('actual frozen R18 camera and old view prefix validate',()=>validateYardCameraViews(originalViews,camera,appendedViews));
test('camera framing change or altered original prefix rejects',()=>{
 for(const index of [0,appendedViews.views.length-1]){
  const changed=structuredClone(appendedViews);changed.views[index].eyeCm[0]+=1;assert.throws(()=>validateYardCameraViews(originalViews,camera,changed));
 }
});
const stageFixture=()=>({schema:CAMERA_SCHEMA,schemaVersion:1,owner:'scripts/unreal/exterior-context-yard-repair-camera-stage-r26.py',status:STAGE_STATUS,
 sourceNativeOutput:source,sourceNativeReport:{path:path.join(source,'context-yard-repair-native-report-r2.json'),sha256:REPORT_SHA},
 sourceNativeProcess:{path:path.join(source,'context-yard-repair-native-r2-process.json')},project:path.join(qa,'Project/BreziTwin'),
 cameraSupplement:{sha256:SUPPLEMENT_SHA},viewId:VIEW,originalContentFileCount:4092,protectedFileCount:132,changedContentFiles:['Data/viewpoints.json'],
 originalViewsPrefixPreserved:true,lightingUnchanged:true,nativeSourceUnchanged:true,allOriginalProjectFilesIndependentBeforeStage:true,
 sceneMapChanged:false,nativeExecuted:false,nativeCameraRuntimeVerified:false,nativeAppearanceAccepted:false,performanceAccepted:false,fullPhotorealismAccepted:false,
 shippingPackageProduced:false,currentVegetationVisibilityRecomputed:false,sourceValidationExitCode:0,
 cameraAuditScope:'FROZEN_R18_SOURCE_CAMERA_REUSED_NOT_CURRENT_R35_VEGETATION_VISIBILITY'});
test('only the exact independent camera QA clone can use the staged Data scope',()=>{
 const context={source:qa,root,names:['context-yard-repair-camera-stage-receipt-r26.json']};validateCameraStageHeader(stageFixture(),context);
 for(const[k,v]of [['sceneMapChanged',true],['nativeCameraRuntimeVerified',true],['currentVegetationVisibilityRecomputed',true],['sourceValidationExitCode',1],['changedContentFiles',['Brezi/Maps/Brezi.umap']]]){
  const changed=stageFixture();changed[k]=v;assert.throws(()=>validateCameraStageHeader(changed,context));
 }
 assert.throws(()=>validateCameraStageHeader(stageFixture(),{...context,names:['context-yard-repair-native-report-r2.json']}));
});
test('unknown R35a failed source and arbitrary camera-clone dispatch reject before IO',async()=>{
 for(const name of ['exterior-20261002-r35a','exterior-20261002-r35b-yard-close-unknown-r26'])await assert.rejects(loadEditorSourceEvidence(path.join(root,'output/unreal',name),{root}));
});
test('runtime is frozen R24 byte-identical after only reader/wrapper filename substitutions',async()=>{
 const old=(await fs.readFile(path.join(root,'scripts/unreal/exterior-editor-qa-r24.mjs'),'utf8')).replaceAll('exterior-editor-source-r24.mjs','exterior-editor-source-r26.mjs').replaceAll('exterior-editor-qa-r24.mjs','exterior-editor-qa-r26.mjs');
 assert.equal(await fs.readFile(path.join(root,'scripts/unreal/exterior-editor-qa-r26.mjs'),'utf8'),old);
});
