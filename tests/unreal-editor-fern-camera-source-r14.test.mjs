// CPU source/staging contract fixtures, not a new native or appearance proof.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateFernCameraViews,validateFernCameraContent,validateFernCameraStageHeader} from '../scripts/unreal/exterior-editor-source-r14.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));
const supplement=JSON.parse(fs.readFileSync(path.join(root,'output/unreal/exterior-garden-fern-20261002-camera-r14-supplement/garden-fern-camera-supplement.json')));
const original=JSON.parse(fs.readFileSync(supplement.originalViewpoints.path)),appended=JSON.parse(fs.readFileSync(supplement.appendedViewpoints.path));
const copy=v=>structuredClone(v);
const source=path.join(root,'output/unreal/exterior-20261002-r25b-fern-close-candidate-r14');
function header(){return {schema:'brezi-purposeful-original-fern-matched-camera-qa-clone-r14',
  owner:'scripts/unreal/exterior-garden-fern-camera-stage-r14.py',status:'verified-independent-purposeful-fern-camera-data-only-qa-clone',
  sourceKind:'saved-r25b-original-fern-single-root',sourceNativeOutput:path.join(root,'output/unreal/exterior-20261002-r25b'),
  project:path.join(source,'Project/BreziTwin'),sourceNativeReport:supplement.candidateNativeReport,
  sourceNativeProcess:{path:path.join(root,'output/unreal/exterior-20261002-r25b/garden-fern-native-r2-process.json')},
  cameraSupplement:{sha256:'9081c0830b4c11eed3787abb5b0bc49ecfedd4a145040c20b09d3bef981298ea'},
  stagingHelper:{sha256:'d0ceddabef4eccb7ee541e8820e50e73f4bedb28d5dd760fb033540fbe6718fb'},
  sourceReader:{sha256:'3cc0773b4e4df4b4239aa054cde8ae35c01e4b09abb0e177ad8f0fc4a1ead115'},sourceValidationExitCode:0,
  originalContentFileCount:4058,protectedFileCount:132,originalViewsPrefixPreserved:true,lightingUnchanged:true,
  nativeSourceUnchanged:true,allOriginalProjectFilesIndependentBeforeStage:true,sceneMapChanged:false,nativeExecuted:false,
  nativeCameraRuntimeVerified:false,nativeAppearanceAccepted:false,performanceAccepted:false,fullPhotorealismAccepted:false,
  shippingPackageProduced:false,changedContentFiles:['Data/viewpoints.json'],viewId:'exterior-garden-fern-close-r14'};}
test('actual frozen source camera keeps all existing views and sun root fields',()=>validateFernCameraViews(original,supplement,appended));
test('an old camera or sun mutation rejects an otherwise rehashed append',()=>{
  const old=copy(appended);old.views[0].eyeCm[0]+=1;assert.throws(()=>validateFernCameraViews(original,supplement,old));
  const sun=copy(appended);sun.sun={...sun.sun,unauthorizedIntensity:1};assert.throws(()=>validateFernCameraViews(original,supplement,sun));
});
test('source camera drift or fabricated native visibility cannot pass',()=>{
  const shifted=copy(supplement);shifted.view.eyeCm[0]+=1;const payload=copy(appended);payload.views.at(-1).eyeCm[0]+=1;
  assert.throws(()=>validateFernCameraViews(original,shifted,payload));
  const native=copy(supplement);native.sourceCameraAudit.nativeFovMeasured=true;assert.throws(()=>validateFernCameraViews(original,native,appended));
});
test('content fixtures allow only exact camera bytes and reject map or new asset changes',()=>{
  const before={'Data/viewpoints.json':{sha256:supplement.originalViewpoints.sha256,bytes:supplement.originalViewpoints.bytes},'Brezi/Maps/Brezi.umap':{sha256:'a'.repeat(64),bytes:12}};
  const after=copy(before);after['Data/viewpoints.json']={sha256:supplement.appendedViewpoints.sha256,bytes:supplement.appendedViewpoints.bytes};
  validateFernCameraContent(before,after,supplement);
  const map=copy(after);map['Brezi/Maps/Brezi.umap'].sha256='b'.repeat(64);assert.throws(()=>validateFernCameraContent(before,map,supplement));
  const extra=copy(after);extra['Brezi/Unowned.uasset']={sha256:'c'.repeat(64),bytes:1};assert.throws(()=>validateFernCameraContent(before,extra,supplement));
});
test('typed stage fixture rejects old native owner, unknown output, copied report or wrong native source',()=>{
  const context={source,root,names:['garden-fern-camera-stage-receipt-r14.json']};validateFernCameraStageHeader(header(),context);
  const old=header();old.owner='scripts/unreal/exterior-curved-grass-camera-stage-r2.py';assert.throws(()=>validateFernCameraStageHeader(old,context));
  assert.throws(()=>validateFernCameraStageHeader(header(),{...context,source:source+'-unowned'}));
  assert.throws(()=>validateFernCameraStageHeader(header(),{...context,names:[...context.names,'garden-fern-native-report-r2.json']}));
  const wrong=header();wrong.sourceNativeOutput=path.join(root,'output/unreal/exterior-20261002-r25a');assert.throws(()=>validateFernCameraStageHeader(wrong,context));
});
