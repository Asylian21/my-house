// Purposeful yard QA camera copies. The actual native source remains external.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR16,validateProjectClosure} from './exterior-editor-source-r16.mjs';
export {validateProjectClosure};
const SCHEMA='brezi-purposeful-first-context-yard-matched-camera-qa-clone-r18';
const SUPPLEMENT_SCHEMA='brezi-purposeful-first-context-yard-matched-camera-r18';
const OWNER='scripts/unreal/exterior-context-yard-camera-stage-r18.py';
const STAGE_SHA='d68c3c4dffa78720f65a630299373d25851ba7806244e9fc3c929cdd545b0225';
const CAMERA_OWNER='scripts/unreal/exterior-context-yard-camera-r18.py';
const CAMERA_SHA='16e28f057703904765b89b4e42c7fd995cb4586d3abff6f928d95973878eb22d';
const SUPPLEMENT_SHA='768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1';
const R16_SHA='98b62be5543ff674833b8d259ff9068c6ad4b09cefba1d16f4405708db8b10d2';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const VIEW='exterior-context-yard-572063-close-r18';
const CASES={
  'exterior-20261002-r27a-yard-close-baseline-r18':{kind:'saved-r27-clean-exterior-yard-baseline',source:'exterior-20261002-r27a',
    report:'realism-clean-integration-native-report.json',sha256:'5575c0e37a9d48733b5c7ed3746f1731cc2b7958634a845c87b9700ff4fc9498',
    process:'realism-clean-integration-native-process.json',content:4034,pid:65450},
  'exterior-20261002-r28b-yard-close-candidate-r18':{kind:'saved-r28b-purposeful-context-yard-overlay',source:'exterior-20261002-r28b',
    report:'context-yard-native-report-r2.json',sha256:'dfbca65515fc08aea52515195ab5ef752fe07cdca622cd41964e99875ced2456',
    process:'context-yard-native-r2-process.json',content:4043,pid:71235},
};
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const sha=async file=>{const h=createHash('sha256');for await(const chunk of createReadStream(file))h.update(chunk);return h.digest('hex');};

export function validateYardCameraViews(original,supplement,appended){
  assert.equal(supplement.schema,SUPPLEMENT_SCHEMA);assert.equal(supplement.owner,CAMERA_OWNER);
  assert.equal(supplement.status,'source-only-purposeful-context-yard-camera-native-pending');
  for(const k of ['nativeExecuted','nativeCameraVerified','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','plantPlacementChanged'])assert.equal(supplement[k],false);
  assert.equal(supplement.originalViewRowsByteExactPrefix,true);assert.equal(supplement.lightingAndOriginalViewsUnchanged,true);
  const {views:oldViews,...oldRoot}=original,{views:newViews,...newRoot}=appended;
  assert.equal(original.coordinateSystem,'unreal-centimeters');assert.deepEqual(oldRoot,newRoot);
  assert.equal(newViews.length,oldViews.length+1);assert.deepEqual(newViews.slice(0,-1),oldViews);
  assert.deepEqual(newViews.at(-1),supplement.view);assert.equal(new Set(newViews.map(v=>v.id)).size,newViews.length);
  const view=supplement.view;assert.equal(view.id,VIEW);assert.equal(view.horizontalFovDegrees,76);
  assert.deepEqual(view.eyeCm,[6640.983714003573,25459.590170585514,140.01999999999998]);
  assert.deepEqual(view.targetCm,[6865.8403100834985,26153.231857971245,35]);
  const a=supplement.sourceCameraAudit;assert.equal(a.sourceBuildingId,'BU.572063');
  assert.equal(a.originalSourceBuildingMeshesChecked,237);assert.deepEqual(a.sourceEyeBuildingBoxHits,[]);
  assert.equal(a.sourceYardAreaM2,35.977642892473455);assert.equal(a.sourceOnlyCameraProposal,true);
  const roles=['entry_walk','service_court','soil_bed','worn_edge'];
  assert.deepEqual(Object.keys(a.sourceSurfaceFraming),roles.map(role=>'yard_r28_BU_572063_'+role));
  for(const [i,role]of roles.entries()){
    const frame=a.sourceSurfaceFraming['yard_r28_BU_572063_'+role];assert.equal(frame.pointsChecked,[112,125,166,281][i]);
    assert.equal(frame.entireSourceSupportInside16by9Frustum,true);assert(frame.maximumAbsoluteNormalizedXY.every(v=>Number.isFinite(v)&&v>=0&&v<1));
  }
  assert.deepEqual(a.sourceShrubCrownFraming.map(r=>r.rootId),['yard_r28_plant_0','yard_r28_plant_1']);
  for(const row of a.sourceShrubCrownFraming){const frame=row.sourceWholeAllLodConservativeCrownFraming;
    assert.equal(frame.entireBoxInsideSource16by9Frustum,true);assert(frame.maximumAbsoluteNormalizedXY.every(v=>Number.isFinite(v)&&v>=0&&v<.96));}
  assert.equal(a.originalVegetationSourceVolumesChecked,true);
  const vegetation=a.sourceVegetationVolumeAudit;
  assert.equal(vegetation.regionalSourceTreesAndShrubsChecked,1100);
  assert.equal(vegetation.originalContextTreeVineShrubRowsChecked,2824);
  assert.equal(vegetation.sourceGroveEcologyInstancesChecked,24773);
  assert.deepEqual(vegetation.sourceLowRootArraysChecked,{groundCoverPlacements:2996,meadowBladePlacements:382678,meadowUnderstoryPlacements:86248});
  assert.equal(vegetation.ownedR28ShrubsChecked,13);
  assert.equal(vegetation.sourceTreeLeafAndLowerWoodEyeAndCompleteCorridorClear,true);
  for(const key of ['sourceEyeTreeLeafHits','sourceCorridorTreeLeafHits','sourceEyeLowerBarkHits','sourceCorridorLowerBarkHits',
    'sourceContextTreeOrShrubHits','sourceEyeEcologyHits','sourceEyeYardShrubHits','sourceCorridorOtherYardShrubHits','sourceLowRootArrayHits'])assert.deepEqual(vegetation[key],[]);
  assert.deepEqual(vegetation.priorR17SourceEyeLeafCrownHits,['village_nearest_grove_15']);
  assert.equal(vegetation.sourceLowGrowthCorridorOverlapsRemain,68);
  assert.equal(vegetation.sourceCorridorEcologyHits.length,68);
  assert.equal(vegetation.sourceCompleteCorridorAllVegetationClear,false);
  assert.equal(vegetation.nativeRaycastExecuted,false);assert.equal(vegetation.nativeVisibilityVerified,false);
  for(const k of ['nativeCameraTransformMeasured','nativeFovMeasured','nativeOcclusionOrPlantVisibilityMeasured','raycastVisibilityClaimed',
    'physicalWalkingTraversalClaimed','sourceDoorObservedInReality','geometryOrPlantPlacementChanged','lightingChanged'])assert.equal(a[k],false);
}

export function validateYardCameraContent(before,after,supplement){
  assert.deepEqual(Object.keys(after).sort(),Object.keys(before).sort());
  assert.deepEqual(Object.keys(before).filter(k=>before[k].sha256!==after[k].sha256||before[k].bytes!==after[k].bytes).sort(),['Data/viewpoints.json']);
  assert.equal(before['Data/viewpoints.json'].sha256,supplement.originalViewpoints.sha256);
  assert.deepEqual(after['Data/viewpoints.json'],{sha256:supplement.appendedViewpoints.sha256,bytes:supplement.appendedViewpoints.bytes});
}

export function validateYardCameraStageHeader(stage,{source,root,names}){
  const selected=CASES[path.basename(source)];assert(selected,'Unknown purposeful yard QA clone');
  assert.equal(path.dirname(source),path.join(root,'output/unreal'));
  assert.equal(stage.schema,SCHEMA);assert.equal(stage.owner,OWNER);assert.equal(stage.status,'verified-independent-purposeful-context-yard-camera-data-only-qa-clone');
  assert.equal(stage.sourceKind,selected.kind);assert.equal(stage.sourceNativeOutput,path.join(root,'output/unreal',selected.source));
  assert.equal(stage.project,path.join(source,'Project/BreziTwin'));assert.equal(stage.sourceNativeReport.sha256,selected.sha256);
  assert.equal(stage.sourceNativeReport.path,path.join(stage.sourceNativeOutput,selected.report));
  assert.equal(stage.sourceNativeProcess.path,path.join(stage.sourceNativeOutput,selected.process));
  assert.equal(stage.cameraSupplement.sha256,SUPPLEMENT_SHA);assert.equal(stage.stagingHelper.sha256,STAGE_SHA);
  assert.equal(stage.sourceReader.sha256,R16_SHA);assert.equal(stage.sourceValidationExitCode,0);
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
  const previous=fileURLToPath(new URL('exterior-editor-source-r16.mjs',import.meta.url));assert.equal(await sha(previous),R16_SHA);
  const names=await fs.readdir(source),filename='context-yard-camera-stage-receipt-r18.json';
  if(!names.includes(filename)){
    assert(!Object.hasOwn(CASES,path.basename(source))&&!/yard.*camera.*stage.*receipt/i.test(names.join('\n'))&&!/yard-close.*r18/.test(source),
      'Purposeful camera QA clone requires its exact known staged receipt');
    const e=await loadR16(source,{root});e.additionalClosureFiles.push(previous);return e;
  }
  const receiptPath=path.join(source,filename),stage=await read(receiptPath),closure=new Set([receiptPath,previous]);
  const selected=validateYardCameraStageHeader(stage,{source,root,names});
  async function pinned(row){
    assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&/^[a-f0-9]{64}$/.test(row.sha256)
      &&Number.isInteger(row.bytes)&&row.bytes>=0);
    const s=await fs.lstat(row.path);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(s.size,row.bytes);assert.equal(await sha(row.path),row.sha256);
    closure.add(row.path);return row.path;
  }
  const pj=async row=>read(await pinned(row));
  const e=await loadR16(stage.sourceNativeOutput,{root});
  assert.equal(e.nativeReceiptPath,stage.sourceNativeReport.path);assert.equal(e.summary.nativeProcessId,selected.pid);
  assert.equal(Object.keys(e.contentInventory).length,selected.content);assert.equal(Object.keys(e.projectProof).length,132);
  const originalReport=await pj(stage.sourceNativeReport);await pinned(stage.sourceNativeProcess);
  assert.deepEqual(stage.protectedProjectProof,originalReport.protectedProjectProof);const projectProof=await pj(stage.protectedProjectProof);
  assert.deepEqual(projectProof,e.projectProof);
  assert.equal(stage.stagingHelper.path,path.join(root,OWNER));await pinned(stage.stagingHelper);
  assert.equal(stage.sourceReader.path,previous);await pinned(stage.sourceReader);
  assert.equal(stage.cameraSupplement.path,path.join(root,'output/unreal/exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json'));
  const supplement=await pj(stage.cameraSupplement);
  assert.equal(supplement.inputFiles[path.join(root,CAMERA_OWNER)],CAMERA_SHA);
  for(const [file,h]of Object.entries(supplement.inputFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  assert.equal(supplement.baselineNativeReport.sha256,CASES['exterior-20261002-r27a-yard-close-baseline-r18'].sha256);
  assert.equal(supplement.candidateNativeReport.sha256,CASES['exterior-20261002-r28b-yard-close-candidate-r18'].sha256);
  const original=await pj(supplement.originalViewpoints),appended=await pj(supplement.appendedViewpoints);
  validateYardCameraViews(original,supplement,appended);assert.deepEqual(stage.view,supplement.view);assert.deepEqual(stage.sourceCameraAudit,supplement.sourceCameraAudit);
  const project=path.join(source,'Project/BreziTwin');
  assert.equal(stage.viewpointFile.path,path.join(project,'Content/Data/viewpoints.json'));
  assert.deepEqual({sha256:stage.viewpointFile.sha256,bytes:stage.viewpointFile.bytes},{sha256:supplement.appendedViewpoints.sha256,bytes:supplement.appendedViewpoints.bytes});
  await pinned(stage.viewpointFile);assert.deepEqual(await read(stage.viewpointFile.path),appended);
  assert.equal(stage.afterContentInventory.path,path.join(source,'context-yard-camera-content-after-r18.json'));
  const contentInventory=await pj(stage.afterContentInventory);validateYardCameraContent(e.contentInventory,contentInventory,supplement);
  assert.equal(stage.projectClone.path,path.join(source,'context-yard-camera-project-clone-r18.json'));const clone=await pj(stage.projectClone);
  assert.equal(clone.schema,SCHEMA);assert.equal(clone.status,'verified-byte-identical-independent-apfs-purposeful-context-yard-qa-clone-before-viewpoint-stage-r18');
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
  assert.equal(stage.sourceValidation.path,path.join(source,'context-yard-camera-source-validation-r18.json'));const validation=await pj(stage.sourceValidation);
  assert.equal(validation.scope,'CPU_EXISTING_SAVED_R13_R16_NATIVE_RECEIPT_AND_SOURCE_CHECKS');assert.equal(validation.sourceNativeOutput,stage.sourceNativeOutput);
  assert.deepEqual(validation.reader,stage.sourceReader);assert.deepEqual(validation.summary,e.summary);assert.equal(validation.nativeLaunchedByStaging,false);
  for(const[file,h]of Object.entries(validation.closureFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const file of [...e.additionalClosureFiles,previous,...Object.keys(supplement.inputFiles)])assert(Object.hasOwn(validation.closureFiles,file),`Recorded CPU source closure is missing ${file}`);
  const module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');assert.equal(await sha(module),MODULE_SHA);closure.add(module);
  const nativeModuleWitness={source:path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),destination:module,
    sha256:MODULE_SHA,bytes:2818384,independentInodes:true};
  const summary={...e.summary,mode:'purposeful-first-context-yard-matched-camera-qa-clone',sourceNativeMode:e.mode,sourceKind:selected.kind,
    supplementalViews:1,sourceWholeFirstYardAndTwoCrownSupportsInsideFrustum:true,nativeCameraRuntimeVerified:false,
    nativeAppearanceAccepted:false,performanceAccepted:false,fullPhotorealismAccepted:false};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:e.base,summary,contentInventory,projectProof,
    additionalClosureFiles:[...new Set([...e.additionalClosureFiles,...closure])],nativeModuleWitness,moduleWitnessSource:stage.projectClone,
    receiptSummary:{sourceNativeReport:stage.sourceNativeReport,sourceNativeProcess:stage.sourceNativeProcess,
      cameraStageReceipt:receiptPath,cameraSupplement:stage.cameraSupplement,originalNativeSourceUnchanged:true,
      sourceNativeEvidence:e.receiptSummary,summary}};
}
