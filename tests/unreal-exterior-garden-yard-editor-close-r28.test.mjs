// Changed-contract fixtures only. Constructed staging headers do not prove executed staging or visibility.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {validateCameraStageHeader,validateYardCameraViews,validateYardCameraContent} from '../scripts/unreal/exterior-editor-source-r28-close.mjs';
const root='/Users/davidzita/www/dom',source=root+'/output/unreal/exterior-20261002-r37b-yard-close-candidate-r28';
const clone=JSON.parse(await fs.readFile(source+'/garden-yard-camera-project-clone-r28.json'));
const supplement=JSON.parse(await fs.readFile(root+'/output/unreal/exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json'));
const original=JSON.parse(await fs.readFile(supplement.originalViewpoints.path)),appended=JSON.parse(await fs.readFile(supplement.appendedViewpoints.path));
const baseNames=['Project','garden-yard-camera-project-clone-r28.json','garden-yard-camera-stage-receipt-r28.json'];
function header(){return {schema:clone.schema,schemaVersion:1,owner:'scripts/unreal/exterior-garden-yard-camera-stage-r28.py',
 status:'verified-independent-saved-r37b-yard-camera-data-only-qa-clone-r28',sourceNativeOutput:root+'/output/unreal/exterior-20261002-r37b',
 sourceNativeReport:clone.sourceNativeReport,sourceNativeProcess:clone.sourceNativeProcess,sourceCurrentByteAudit:clone.sourceCurrentByteAudit,
 project:source+'/Project/BreziTwin',cameraSupplement:{sha256:'768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1'},viewId:'exterior-context-yard-572063-close-r18',
 originalContentFileCount:4100,protectedFileCount:132,changedContentFiles:['Data/viewpoints.json'],originalViewsPrefixPreserved:true,lightingUnchanged:true,
 nativeSourceUnchanged:true,allOriginalProjectFilesIndependentBeforeStage:true,sourceValidationExitCode:0,
 sceneMapChanged:false,nativeExecuted:false,nativeCameraRuntimeVerified:false,nativeAppearanceAccepted:false,performanceAccepted:false,
 fullPhotorealismAccepted:false,shippingPackageProduced:false,currentVegetationVisibilityRecomputed:false,
 cameraAuditScope:'FROZEN_R18_SOURCE_CAMERA_REUSED_NOT_CURRENT_R37_VEGETATION_VISIBILITY'};}
const valid=h=>validateCameraStageHeader(h,{root,source,names:baseNames});
test('one actual independent R37 clone may reuse historical R18 view while retaining visibility limits',()=>{
 valid(header());for(const change of [h=>h.nativeCameraRuntimeVerified=true,h=>h.currentVegetationVisibilityRecomputed=true,
  h=>h.changedContentFiles.push('Brezi/Maps/Brezi.umap'),h=>h.sourceNativeOutput=root+'/output/unreal/exterior-20261002-r35b']){
  const bad=structuredClone(header());change(bad);assert.throws(()=>valid(bad));}
 assert.throws(()=>validateCameraStageHeader(header(),{root,source,names:[...baseNames,'garden-yard-integration-native-report-r2.json']}));
});
test('appended view remains exact frozen R18 camera and original prefix',()=>{
 validateYardCameraViews(original,supplement,appended);
 const bad=structuredClone(appended);bad.views.at(-1).eyeCm[0]+=.01;assert.throws(()=>validateYardCameraViews(original,supplement,bad));
});
test('only exact viewpoint byte delta passes; map and shared material bytes cannot change',()=>{
 const before={'Data/viewpoints.json':{sha256:supplement.originalViewpoints.sha256,bytes:supplement.originalViewpoints.bytes},
  'Brezi/Maps/Brezi.umap':{sha256:'a'.repeat(64),bytes:10},'Brezi/Materials/M_ground.uasset':{sha256:'b'.repeat(64),bytes:20}};
 const after=structuredClone(before);after['Data/viewpoints.json']={sha256:supplement.appendedViewpoints.sha256,bytes:supplement.appendedViewpoints.bytes};
 validateYardCameraContent(before,after,supplement);for(const key of ['Brezi/Maps/Brezi.umap','Brezi/Materials/M_ground.uasset']){
  const bad=structuredClone(after);bad[key].bytes++;assert.throws(()=>validateYardCameraContent(before,bad,supplement));}
});
