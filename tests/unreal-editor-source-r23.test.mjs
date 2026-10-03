// Constructed camera-stage source fixtures use stored inputs; no new native/camera proof.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {validateYardCameraViews,validateYardCameraContent,validateYardCameraStageHeader} from '../scripts/unreal/exterior-editor-source-r23.mjs';
const root='/Users/davidzita/www/dom',base=root+'/output/unreal/';
const supplement=JSON.parse(await fs.readFile(base+'exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json'));
const original=JSON.parse(await fs.readFile(supplement.originalViewpoints.path)),appended=JSON.parse(await fs.readFile(supplement.appendedViewpoints.path));
const source=base+'exterior-20261002-r32a-yard-close-candidate-r23';
const clone=JSON.parse(await fs.readFile(source+'/context-yard-camera-project-clone-r23.json'));
const report=JSON.parse(await fs.readFile(clone.sourceNativeReport.path));
const content=JSON.parse(await fs.readFile(report.afterContentInventory.path));
const staged={...content,'Data/viewpoints.json':{sha256:supplement.appendedViewpoints.sha256,bytes:supplement.appendedViewpoints.bytes}};
function fixture(){return {schema:'brezi-saved-r30-r32-matched-context-yard-camera-qa-clone-r23',owner:'scripts/unreal/exterior-context-yard-camera-stage-r23.py',status:'verified-independent-saved-r30-r32-yard-camera-data-only-qa-clone-r23',
 sourceKind:clone.sourceKind,sourceNativeOutput:base+'exterior-20261002-r32a',project:clone.project,sourceNativeReport:clone.sourceNativeReport,sourceNativeProcess:clone.sourceNativeProcess,
 cameraSupplement:{sha256:'768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1'},stagingHelper:{sha256:'d922b612e0aee51b3a15683ef0bdc2e78ca295ce8d6870d54725eeb9cb8a7dfe'},sourceReader:{sha256:'305191a1d44a26219f57d5ec66fb792c1b82e1358210398955f2cbe617ec48a4'},historicalCameraReader:{sha256:'46035c3982ec8e977873c46c1ff8dfa5a69a10d1aaa2f0d1f216ce89bf87ed2f'},
 cameraAuditScope:'FROZEN_R18_ORIGINAL_R27_R28_SOURCE_ONLY_REUSED_CAMERA_NOT_CURRENT_R29_R32_VEGETATION_VISIBILITY',currentR29TreesAndR32LowGrowthVisibilityRecomputed:false,
 sourceValidationExitCode:0,originalContentFileCount:4086,protectedFileCount:132,originalViewsPrefixPreserved:true,lightingUnchanged:true,nativeSourceUnchanged:true,allOriginalProjectFilesIndependentBeforeStage:true,
 sceneMapChanged:false,nativeExecuted:false,nativeCameraRuntimeVerified:false,nativeAppearanceAccepted:false,performanceAccepted:false,fullPhotorealismAccepted:false,shippingPackageProduced:false,
 changedContentFiles:['Data/viewpoints.json'],viewId:supplement.view.id};}
test('frozen exact R18 camera/prefix and constructed R32 stage/source delta validate',()=>{
 validateYardCameraViews(original,supplement,appended);validateYardCameraContent(content,staged,supplement);
 validateYardCameraStageHeader(fixture(),{source,root,names:[]});
});
test('camera drift or any original lighting/view change rejects',()=>{
 for(const change of [x=>x.views.at(-1).eyeCm[0]+=.00001,x=>x.views.at(-1).horizontalFovDegrees=75,
  x=>x.views[0].eyeCm[0]+=1,x=>x.coordinateSystem='meters']){
  const v=structuredClone(appended);change(v);assert.throws(()=>validateYardCameraViews(original,supplement,v));
 }
});
test('stage cannot claim current tree/low-growth visibility or native acceptance',()=>{
 for(const edit of [{currentR29TreesAndR32LowGrowthVisibilityRecomputed:true},{nativeCameraRuntimeVerified:true},{fullPhotorealismAccepted:true},
  {cameraAuditScope:'CURRENT_NATIVE_PROOF'},{sourceValidationExitCode:1}])assert.throws(()=>validateYardCameraStageHeader({...fixture(),...edit},{source,root,names:[]}));
});
test('copied native reports, foreign clone/output/source identities reject',()=>{
 assert.throws(()=>validateYardCameraStageHeader(fixture(),{source,root,names:['context-yard-ground-native-report.json']}));
 assert.throws(()=>validateYardCameraStageHeader(fixture(),{source:source+'-unknown',root,names:[]}));
 for(const edit of [{owner:'scripts/unreal/exterior-context-yard-camera-stage-r18.py'},{sourceKind:'saved-r28b-purposeful-context-yard-overlay'},
  {sourceNativeOutput:base+'exterior-20261002-r30b'},{changedContentFiles:['Brezi/Maps/Brezi.umap']}])
  assert.throws(()=>validateYardCameraStageHeader({...fixture(),...edit},{source,root,names:[]}));
});
test('map/material mutation or extra/missing packages cannot be a Data-only stage',()=>{
 const v=structuredClone(staged);v['Brezi/Maps/Brezi.umap'].bytes++;assert.throws(()=>validateYardCameraContent(content,v,supplement));
 assert.throws(()=>validateYardCameraContent(content,{...staged,'Brezi/extra.uasset':{sha256:'0'.repeat(64),bytes:1}},supplement));
 const missing=structuredClone(staged);delete missing[Object.keys(content)[0]];assert.throws(()=>validateYardCameraContent(content,missing,supplement));
});
