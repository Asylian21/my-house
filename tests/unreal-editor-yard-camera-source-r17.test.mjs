// CPU source/staging fixtures; this is not native or appearance evidence.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateYardCameraViews,validateYardCameraContent,validateYardCameraStageHeader} from '../scripts/unreal/exterior-editor-source-r17.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));
const supplement=JSON.parse(fs.readFileSync(path.join(root,'output/unreal/exterior-context-yard-20261002-camera-r17-supplement/context-yard-camera-supplement.json')));
const original=JSON.parse(fs.readFileSync(supplement.originalViewpoints.path)),appended=JSON.parse(fs.readFileSync(supplement.appendedViewpoints.path));
const copy=v=>structuredClone(v);
const source=path.join(root,'output/unreal/exterior-20261002-r28b-yard-close-candidate-r17');
const receipt=JSON.parse(fs.readFileSync(path.join(source,'context-yard-camera-stage-receipt-r17.json')));
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
  const context={source,root,names:['context-yard-camera-stage-receipt-r17.json']};validateYardCameraStageHeader(receipt,context);
  for(const mutation of [r=>{r.owner='scripts/unreal/exterior-garden-fern-camera-stage-r14.py';},r=>{r.sourceNativeOutput=path.join(root,'output/unreal/exterior-20261002-r28a');},r=>{r.originalContentFileCount=4034;}]){
    const bad=copy(receipt);mutation(bad);assert.throws(()=>validateYardCameraStageHeader(bad,context));}
  assert.throws(()=>validateYardCameraStageHeader(receipt,{...context,source:source+'-unknown'}));
  assert.throws(()=>validateYardCameraStageHeader(receipt,{...context,names:[...context.names,'context-yard-native-report-r2.json']}));
});
