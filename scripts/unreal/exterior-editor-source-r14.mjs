// Purposeful fern QA camera copies. The actual native source remains external.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR11,validateProjectClosure} from './exterior-editor-source-r11.mjs';
export {validateProjectClosure};
const SCHEMA='brezi-purposeful-original-fern-matched-camera-qa-clone-r14';
const SUPPLEMENT_SCHEMA='brezi-purposeful-original-fern-matched-camera-r14';
const OWNER='scripts/unreal/exterior-garden-fern-camera-stage-r14.py';
const STAGE_SHA='d0ceddabef4eccb7ee541e8820e50e73f4bedb28d5dd760fb033540fbe6718fb';
const CAMERA_OWNER='scripts/unreal/exterior-garden-fern-camera-r14.py';
const CAMERA_SHA='fa8b923ad0492e3d66108e43be26adbae9bdff14e6f11007ac989951f8649363';
const SUPPLEMENT_SHA='9081c0830b4c11eed3787abb5b0bc49ecfedd4a145040c20b09d3bef981298ea';
const R11_SHA='3cc0773b4e4df4b4239aa054cde8ae35c01e4b09abb0e177ad8f0fc4a1ead115';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const VIEW='exterior-garden-fern-close-r14';
const CASES={
  'exterior-20261002-r22c-fern-close-baseline-r14':{kind:'original-r22c-six-donor-garden-baseline',source:'exterior-20261002-r22c',
    report:'realism-integration-native-report-r3.json',sha256:'999fc17ea7600136a2097aecefed3d846ff0d7e9baeb7f005480b113b60b1f40',
    process:'realism-integration-native-r3-process.json',content:4049,pid:50344},
  'exterior-20261002-r25b-fern-close-candidate-r14':{kind:'saved-r25b-original-fern-single-root',source:'exterior-20261002-r25b',
    report:'garden-fern-native-report-r2.json',sha256:'dc96a4927a0b0ec0e8abb3740e7a918e65a6ba6a0881ba77bc29275c1445e0b2',
    process:'garden-fern-native-r2-process.json',content:4058,pid:60976},
};
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const sha=async file=>{const h=createHash('sha256');for await(const chunk of createReadStream(file))h.update(chunk);return h.digest('hex');};

export function validateFernCameraViews(original,supplement,appended){
  assert.equal(supplement.schema,SUPPLEMENT_SCHEMA);assert.equal(supplement.owner,CAMERA_OWNER);
  assert.equal(supplement.status,'source-only-purposeful-fern-camera-native-pending');
  for(const k of ['nativeExecuted','nativeCameraVerified','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','plantPlacementChanged'])assert.equal(supplement[k],false);
  assert.equal(supplement.originalViewRowsByteExactPrefix,true);assert.equal(supplement.lightingAndOriginalViewsUnchanged,true);
  const {views:oldViews,...oldRoot}=original,{views:newViews,...newRoot}=appended;
  assert.equal(original.coordinateSystem,'unreal-centimeters');assert.deepEqual(oldRoot,newRoot);
  assert.equal(newViews.length,oldViews.length+1);assert.deepEqual(newViews.slice(0,-1),oldViews);
  assert.deepEqual(newViews.at(-1),supplement.view);assert.equal(new Set(newViews.map(v=>v.id)).size,newViews.length);
  const view=supplement.view;assert.equal(view.id,VIEW);assert.equal(view.horizontalFovDegrees,62);
  assert.deepEqual(view.eyeCm,[1432.3084822728883,-377.1794510218074,130]);
  assert.deepEqual(view.targetCm,[1432.3084822728883,-627.1794510218074,50]);
  const a=supplement.sourceCameraAudit;assert.equal(a.rootId,'garden_ornamental_10');assert.equal(a.sourceSubjectTrianglesChecked,27);
  assert.deepEqual(a.sourceEyeContainingTriangleOrdinals,[25]);assert.equal(a.sourceEyeGroundElevationCm,-6.5);
  assert.equal(a.taggedSourceOccluderObjectsChecked,321);assert.deepEqual(a.sourceEyeClearanceBoxHits,[]);assert.deepEqual(a.sourceWholeCrownSightCorridorHits,[]);
  for(const k of ['original120cmFullCrownConservativeFraming','saved35cmFernFullCrownConservativeFraming']){
    assert.equal(a[k].entireBoxInsideSource16by9Frustum,true);assert(a[k].maximumAbsoluteNormalizedXY.every(v=>Number.isFinite(v)&&v>=0&&v<.96));
  }
  for(const k of ['nativeCameraTransformMeasured','nativeFovMeasured','nativeOcclusionOrPlantVisibilityMeasured',
    'untaggedPlantOcclusionChecked','physicalWalkingTraversalClaimed','geometryOrPlantPlacementChanged','lightingChanged'])assert.equal(a[k],false);
}

export function validateFernCameraContent(before,after,supplement){
  assert.deepEqual(Object.keys(after).sort(),Object.keys(before).sort());
  assert.deepEqual(Object.keys(before).filter(k=>before[k].sha256!==after[k].sha256||before[k].bytes!==after[k].bytes).sort(),['Data/viewpoints.json']);
  assert.equal(before['Data/viewpoints.json'].sha256,supplement.originalViewpoints.sha256);
  assert.deepEqual(after['Data/viewpoints.json'],{sha256:supplement.appendedViewpoints.sha256,bytes:supplement.appendedViewpoints.bytes});
}

export function validateFernCameraStageHeader(stage,{source,root,names}){
  const selected=CASES[path.basename(source)];assert(selected,'Unknown purposeful fern QA clone');
  assert.equal(path.dirname(source),path.join(root,'output/unreal'));
  assert.equal(stage.schema,SCHEMA);assert.equal(stage.owner,OWNER);assert.equal(stage.status,'verified-independent-purposeful-fern-camera-data-only-qa-clone');
  assert.equal(stage.sourceKind,selected.kind);assert.equal(stage.sourceNativeOutput,path.join(root,'output/unreal',selected.source));
  assert.equal(stage.project,path.join(source,'Project/BreziTwin'));assert.equal(stage.sourceNativeReport.sha256,selected.sha256);
  assert.equal(stage.sourceNativeReport.path,path.join(stage.sourceNativeOutput,selected.report));
  assert.equal(stage.sourceNativeProcess.path,path.join(stage.sourceNativeOutput,selected.process));
  assert.equal(stage.cameraSupplement.sha256,SUPPLEMENT_SHA);assert.equal(stage.stagingHelper.sha256,STAGE_SHA);
  assert.equal(stage.sourceReader.sha256,R11_SHA);assert.equal(stage.sourceValidationExitCode,0);
  assert.equal(stage.originalContentFileCount,selected.content);assert.equal(stage.protectedFileCount,132);
  for(const k of ['originalViewsPrefixPreserved','lightingUnchanged','nativeSourceUnchanged','allOriginalProjectFilesIndependentBeforeStage'])assert.equal(stage[k],true);
  for(const k of ['sceneMapChanged','nativeExecuted','nativeCameraRuntimeVerified','nativeAppearanceAccepted',
    'performanceAccepted','fullPhotorealismAccepted','shippingPackageProduced'])assert.equal(stage[k],false);
  assert.deepEqual(stage.changedContentFiles,['Data/viewpoints.json']);assert.equal(stage.viewId,VIEW);
  assert(!names.some(n=>n==='exterior-import-report.json'||/native-report|overlay-report/.test(n)),'QA camera clone cannot carry a copied native report');
  return selected;
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);
  const previous=fileURLToPath(new URL('exterior-editor-source-r11.mjs',import.meta.url));assert.equal(await sha(previous),R11_SHA);
  const names=await fs.readdir(source),filename='garden-fern-camera-stage-receipt-r14.json';
  if(!names.includes(filename)){
    assert(!Object.hasOwn(CASES,path.basename(source))&&!/fern.*camera.*stage.*receipt/i.test(names.join('\n'))&&!/fern-close.*r14/.test(source),
      'Purposeful camera QA clone requires its exact known staged receipt');
    const e=await loadR11(source,{root});e.additionalClosureFiles.push(previous);return e;
  }
  const receiptPath=path.join(source,filename),stage=await read(receiptPath),closure=new Set([receiptPath,previous]);
  const selected=validateFernCameraStageHeader(stage,{source,root,names});
  async function pinned(row){
    assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&/^[a-f0-9]{64}$/.test(row.sha256)
      &&Number.isInteger(row.bytes)&&row.bytes>=0);
    const s=await fs.lstat(row.path);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(s.size,row.bytes);assert.equal(await sha(row.path),row.sha256);
    closure.add(row.path);return row.path;
  }
  const pj=async row=>read(await pinned(row));
  const e=await loadR11(stage.sourceNativeOutput,{root});
  assert.equal(e.nativeReceiptPath,stage.sourceNativeReport.path);assert.equal(e.summary.nativeProcessId,selected.pid);
  assert.equal(Object.keys(e.contentInventory).length,selected.content);assert.equal(Object.keys(e.projectProof).length,132);
  const originalReport=await pj(stage.sourceNativeReport);await pinned(stage.sourceNativeProcess);
  assert.deepEqual(stage.protectedProjectProof,originalReport.protectedProjectProof);const projectProof=await pj(stage.protectedProjectProof);
  assert.deepEqual(projectProof,e.projectProof);
  assert.equal(stage.stagingHelper.path,path.join(root,OWNER));await pinned(stage.stagingHelper);
  assert.equal(stage.sourceReader.path,previous);await pinned(stage.sourceReader);
  assert.equal(stage.cameraSupplement.path,path.join(root,'output/unreal/exterior-garden-fern-20261002-camera-r14-supplement/garden-fern-camera-supplement.json'));
  const supplement=await pj(stage.cameraSupplement);
  assert.equal(supplement.inputFiles[path.join(root,CAMERA_OWNER)],CAMERA_SHA);
  for(const [file,h]of Object.entries(supplement.inputFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  assert.equal(supplement.baselineNativeReport.sha256,CASES['exterior-20261002-r22c-fern-close-baseline-r14'].sha256);
  assert.equal(supplement.candidateNativeReport.sha256,CASES['exterior-20261002-r25b-fern-close-candidate-r14'].sha256);
  const original=await pj(supplement.originalViewpoints),appended=await pj(supplement.appendedViewpoints);
  validateFernCameraViews(original,supplement,appended);assert.deepEqual(stage.view,supplement.view);assert.deepEqual(stage.sourceCameraAudit,supplement.sourceCameraAudit);
  const project=path.join(source,'Project/BreziTwin');
  assert.equal(stage.viewpointFile.path,path.join(project,'Content/Data/viewpoints.json'));
  assert.deepEqual({sha256:stage.viewpointFile.sha256,bytes:stage.viewpointFile.bytes},{sha256:supplement.appendedViewpoints.sha256,bytes:supplement.appendedViewpoints.bytes});
  await pinned(stage.viewpointFile);assert.deepEqual(await read(stage.viewpointFile.path),appended);
  assert.equal(stage.afterContentInventory.path,path.join(source,'garden-fern-camera-content-after-r14.json'));
  const contentInventory=await pj(stage.afterContentInventory);validateFernCameraContent(e.contentInventory,contentInventory,supplement);
  assert.equal(stage.projectClone.path,path.join(source,'garden-fern-camera-project-clone-r14.json'));const clone=await pj(stage.projectClone);
  assert.equal(clone.schema,SCHEMA);assert.equal(clone.status,'verified-byte-identical-independent-apfs-purposeful-fern-qa-clone-before-viewpoint-stage-r14');
  assert.equal(clone.project,project);assert.equal(clone.sourceProject,e.project);assert.deepEqual(clone.sourceNativeReport,stage.sourceNativeReport);
  assert.equal(clone.nativeExecuted,false);assert.equal(clone.viewpointStagingPending,true);assert.equal(clone.cameraSupplement,null);
  assert.equal(clone.fileCount,selected.content+132);assert.equal(clone.contentFiles,selected.content);assert.equal(clone.protectedFiles,132);
  const originalFiles={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...projectProof};
  const observed=new Set();assert.equal(clone.files.length,Object.keys(originalFiles).length);
  for(const row of clone.files){
    const relative=path.relative(project,row.destination);assert(Object.hasOwn(originalFiles,relative)&&!observed.has(relative));observed.add(relative);
    assert.equal(row.source,path.join(e.project,relative));assert.equal(row.independentInodes,true);assert.deepEqual({sha256:row.sha256,bytes:row.bytes},originalFiles[relative]);
    const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);
  }
  assert.equal(stage.sourceValidation.path,path.join(source,'garden-fern-camera-source-validation-r14.json'));const validation=await pj(stage.sourceValidation);
  assert.equal(validation.scope,'CPU_EXISTING_SAVED_R10_R11_NATIVE_RECEIPT_AND_SOURCE_CHECKS');assert.equal(validation.sourceNativeOutput,stage.sourceNativeOutput);
  assert.deepEqual(validation.reader,stage.sourceReader);assert.deepEqual(validation.summary,e.summary);assert.equal(validation.nativeLaunchedByStaging,false);
  for(const[file,h]of Object.entries(validation.closureFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const file of [...e.additionalClosureFiles,previous,...Object.keys(supplement.inputFiles)])assert(Object.hasOwn(validation.closureFiles,file),`Recorded CPU source closure is missing ${file}`);
  const module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');assert.equal(await sha(module),MODULE_SHA);closure.add(module);
  const nativeModuleWitness={source:path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),destination:module,
    sha256:MODULE_SHA,bytes:2818384,independentInodes:true};
  const summary={...e.summary,mode:'purposeful-original-fern-matched-camera-qa-clone',sourceNativeMode:e.mode,sourceKind:selected.kind,
    supplementalViews:1,sourceWholeOldAndNewCrownInsideFrustum:true,nativeCameraRuntimeVerified:false,
    nativeAppearanceAccepted:false,performanceAccepted:false,fullPhotorealismAccepted:false};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:e.base,summary,contentInventory,projectProof,
    additionalClosureFiles:[...new Set([...e.additionalClosureFiles,...closure])],nativeModuleWitness,moduleWitnessSource:stage.projectClone,
    receiptSummary:{sourceNativeReport:stage.sourceNativeReport,sourceNativeProcess:stage.sourceNativeProcess,
      cameraStageReceipt:receiptPath,cameraSupplement:stage.cameraSupplement,originalNativeSourceUnchanged:true,
      sourceNativeEvidence:e.receiptSummary,summary}};
}
