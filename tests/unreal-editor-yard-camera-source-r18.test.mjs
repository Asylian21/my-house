// CPU source/staging fixtures; this is not native or appearance evidence.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateYardCameraViews,validateYardCameraContent,validateYardCameraStageHeader} from '../scripts/unreal/exterior-editor-source-r18.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));
const supplement=JSON.parse(fs.readFileSync(path.join(root,'output/unreal/exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json')));
const original=JSON.parse(fs.readFileSync(supplement.originalViewpoints.path)),appended=JSON.parse(fs.readFileSync(supplement.appendedViewpoints.path));
const copy=v=>structuredClone(v);
const source=path.join(root,'output/unreal/exterior-20261002-r28b-yard-close-candidate-r18');
// Constructed CPU header fixture: no stage or native receipt is fabricated on disk.
const receipt={schema:'brezi-purposeful-first-context-yard-matched-camera-qa-clone-r18',owner:'scripts/unreal/exterior-context-yard-camera-stage-r18.py',
 status:'verified-independent-purposeful-context-yard-camera-data-only-qa-clone',sourceKind:'saved-r28b-purposeful-context-yard-overlay',
 sourceNativeOutput:path.join(root,'output/unreal/exterior-20261002-r28b'),project:path.join(source,'Project/BreziTwin'),
 sourceNativeReport:{path:supplement.candidateNativeReport.path,sha256:supplement.candidateNativeReport.sha256},
 sourceNativeProcess:{path:path.join(root,'output/unreal/exterior-20261002-r28b/context-yard-native-r2-process.json')},
 cameraSupplement:{sha256:'768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1'},
 stagingHelper:{sha256:'d68c3c4dffa78720f65a630299373d25851ba7806244e9fc3c929cdd545b0225'},
 sourceReader:{sha256:'98b62be5543ff674833b8d259ff9068c6ad4b09cefba1d16f4405708db8b10d2'},sourceValidationExitCode:0,
 originalContentFileCount:4043,protectedFileCount:132,originalViewsPrefixPreserved:true,lightingUnchanged:true,nativeSourceUnchanged:true,
 allOriginalProjectFilesIndependentBeforeStage:true,sceneMapChanged:false,nativeExecuted:false,nativeCameraRuntimeVerified:false,
 nativeAppearanceAccepted:false,performanceAccepted:false,fullPhotorealismAccepted:false,shippingPackageProduced:false,
 changedContentFiles:['Data/viewpoints.json'],viewId:supplement.view.id};
test('frozen source camera preserves original views and lighting and frames exact first yard',()=>validateYardCameraViews(original,supplement,appended));
test('an original camera or sun mutation rejects an otherwise rehashed append',()=>{
  const old=copy(appended);old.views[0].eyeCm[0]+=1;assert.throws(()=>validateYardCameraViews(original,supplement,old));
  const sun=copy(appended);sun.sun={...sun.sun,unauthorizedIntensity:1};assert.throws(()=>validateYardCameraViews(original,supplement,sun));
});
test('source camera drift or fabricated native visibility is rejected',()=>{
  const shifted=copy(supplement);shifted.view.eyeCm[0]+=1;const payload=copy(appended);payload.views.at(-1).eyeCm[0]+=1;
  assert.throws(()=>validateYardCameraViews(original,shifted,payload));
  const native=copy(supplement);native.sourceCameraAudit.nativeFovMeasured=true;assert.throws(()=>validateYardCameraViews(original,native,appended));
});
test('only exact Data viewpoint bytes can change; map mutation or new packages reject',()=>{
  const before={'Data/viewpoints.json':{sha256:supplement.originalViewpoints.sha256,bytes:supplement.originalViewpoints.bytes},'Brezi/Maps/Brezi.umap':{sha256:'a'.repeat(64),bytes:12}};
  const after=copy(before);after['Data/viewpoints.json']={sha256:supplement.appendedViewpoints.sha256,bytes:supplement.appendedViewpoints.bytes};
  validateYardCameraContent(before,after,supplement);
  const map=copy(after);map['Brezi/Maps/Brezi.umap'].sha256='b'.repeat(64);assert.throws(()=>validateYardCameraContent(before,map,supplement));
  const extra=copy(after);extra['Brezi/Unowned.uasset']={sha256:'c'.repeat(64),bytes:1};assert.throws(()=>validateYardCameraContent(before,extra,supplement));
});
test('typed stage rejects wrong owner, source, count, unknown clone or copied native report',()=>{
  const context={source,root,names:['context-yard-camera-stage-receipt-r18.json']};validateYardCameraStageHeader(receipt,context);
  for(const mutation of [r=>{r.owner='scripts/unreal/exterior-garden-fern-camera-stage-r14.py';},r=>{r.sourceNativeOutput=path.join(root,'output/unreal/exterior-20261002-r28a');},r=>{r.originalContentFileCount=4034;}]){
    const bad=copy(receipt);mutation(bad);assert.throws(()=>validateYardCameraStageHeader(bad,context));}
  assert.throws(()=>validateYardCameraStageHeader(receipt,{...context,source:source+'-unknown'}));
  assert.throws(()=>validateYardCameraStageHeader(receipt,{...context,names:[...context.names,'context-yard-native-report-r2.json']}));
});

test('corrected crown diagnosis rejects falsely cleared short plants or native visibility',()=>{
 for(const mutate of [a=>{a.sourceVegetationVolumeAudit.sourceEyeTreeLeafHits=['village_nearest_grove_15'];},
  a=>{a.sourceVegetationVolumeAudit.sourceCompleteCorridorAllVegetationClear=true;},
  a=>{a.sourceVegetationVolumeAudit.nativeVisibilityVerified=true;},
  a=>{a.sourceVegetationVolumeAudit.priorR17SourceEyeLeafCrownHits=[];}]){
  const bad=copy(supplement);mutate(bad.sourceCameraAudit);assert.throws(()=>validateYardCameraViews(original,bad,appended));
 }
});
