// Unconsumed R39 typed direct reader. Actual success and current-byte pins await root.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createReadStream} from 'node:fs';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {loadEditorSourceEvidence as loadR29,validateProjectClosure} from './exterior-editor-source-r29-r3.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-neighbor-props-native-r39-r3.py';
const SCHEMA='brezi-original-whole-neighbor-props-native-r39';
const REPORT_NAME='neighbor-props-native-report-r3.json';
export const ACTUAL=Object.freeze({reportSha:'118f451095730e2ff0e62304d959626d4a81be53f03e41dd2229fe91831f4da5',processSha:'2bbb88ee2d71a0d81469c267f263c22beaea4f2d49eba05618d9c8896c2e96e0',rawSha:'c8d059ca2b877d91d95ea2509dfedf323b1d773538af470b61cba32f73910598',auditSha:'7f70d6eb3c59e87305313ba35b7cf7324fde14e80507b5d06e3eaecce7f17ad5',checkerSha:'311dd636b5ad5613460e8c6244d07d0e53a2ab0365e46b0725a3f5b97f86c516',nativePid:94572,terminalPins:1294});
const PLAN_SHA='85ec3bb423fe8205b551629b2c4f374c715cd2adb2f5ea265c5dc38ada6aa7c5';
const PF_SHA='3bc9b4cb47603c572afb1502b4e591406d03b810084555bfc64f43f2d60be0b7';
const HELPER_SHA='8b49f73e164b99803c0cb2625590179719b56d757e987308ec7eb2c4bd66765d';
const BASE_SHA='077e36066dc49f2c3fa379893c39fc5659e8261385030d86266316e1bde9f2b9';
const SOURCE_PINS=1288;
const MONITOR_SHA='489b4c685d086f883b36ae040710708fae068f6197bead5e7c73f4b85174e50e';
const CLONE_SHA='c98868ea51686a34f68139e3f6cc48c2a4edff9516c92f23973bb8ca60f956b5';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const exec=promisify(execFile);
const R29_SHA='73562897b5fd762cb1c712bf65a591e3a742d4e22f998fe4f838138b97fb6ebf';
export const COUNTS=Object.freeze({beforeActors:5364,savedActors:5368,beforeHismComponents:2325,savedHismComponents:2329,
  beforeHismInstances:678197,savedHismInstances:678205,newActors:4,newInstances:8,newMeshes:4,newMaterialGraphs:3,
  newTextureObjects:11,newPipelineAssets:3,newPackages:21,beforeContentFiles:4103,savedContentFiles:4124,protectedFiles:132,
  beforeMaterialGraphs:66,savedMaterialGraphs:69,beforeTextureObjects:97,savedTextureObjects:108,sourceMasterTriangles:26601});
const sha=async p=>{const h=createHash('sha256');for await(const b of createReadStream(p))h.update(b);return h.digest('hex');};
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
export function requireActualBinding(actual=ACTUAL){
  for(const k of ['reportSha','processSha','rawSha','auditSha','checkerSha'])assert(hashLike(actual[k]),'Root successful saved report/current-byte/checker bindings remain pending');
  assert(Number.isInteger(actual.nativePid)&&actual.nativePid>0&&Number.isInteger(actual.terminalPins)&&actual.terminalPins>=SOURCE_PINS);
}
export function validatePropsReportNames(names){
  assert(names.includes(REPORT_NAME));
  assert(!names.some(n=>n!==REPORT_NAME&&/(?:exterior-import|native-report|overlay-report).*\.json$/.test(n)),'Failed, foreign or legacy reports cannot coexist');
}
export function validatePropsHeader(r,{root,source,actual=ACTUAL}){
  requireActualBinding(actual);assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r39c'));
  assert.equal(r.schema,SCHEMA);assert.equal(r.schemaVersion,3);assert.equal(r.owner,OWNER);
  assert.equal(r.repairSchema,'brezi-r39-exact-new-local-zero-constructor-repair-r3');
  assert.equal(r.binding.schemaVersion,3);assert.equal(r.binding.nativeOwner,OWNER);
  assert.equal(r.status,'verified-saved-six-whole-original-neighbor-prop-assemblies');assert.equal(r.nativeProcessId,actual.nativePid);
  assert.equal(r.project,path.join(source,'Project/BreziTwin'));assert.equal(r.output,source);assert.deepEqual(r.actualCounts,COUNTS);
  assert.equal(r.baseNativeReport.sha256,BASE_SHA);assert.equal(r.selectedPlan.sha256,PLAN_SHA);assert.equal(r.sourcePreflight.sha256,PF_SHA);
  assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);assert.equal(Object.keys(r.inputFiles).length,SOURCE_PINS);
  assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});
  for(const k of ['nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged','allOriginal5364ActorsAnd2325RawControlsExact',
    'allOriginal66MaterialGraphsAuxObservedUsageExact','allOriginal97TextureSettingsAndSourceBytesExact','allFourOriginalPartsFullNativeIdentityVerified',
    'allSixIntendedAssembliesAndOriginalHoseNodePosesIndependentlyCompared','allEightMeasuredPosesExactBeforeAppliedAndSaved'])assert.equal(r[k],true);
  for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified','activeOutputPromoted',
    'nativeNormalTangentReadbackAvailable','nativeGpuPixelFormatVerified','sourceOriginalGeometryAndPhotoPixelsEdited',
    'originalActorTransformInstanceOrMaterialSettersCalled','allSixAssemblyActorsIndividuallyVisibleVerified',
    'actualNativeSurfaceContactCollisionOrSurveyVerified','oldAdditionalRandomSeedRangesPreservationClaimed','nativeTangentsNumericallyVerified'])assert.equal(r[k],false);
}
export function validatePropsContent(before,after,newPackages,delta){
  assert.equal(Object.keys(before).length,4103);assert.equal(Object.keys(after).length,4124);assert.equal(newPackages.length,21);
  const added=newPackages.map(a=>{assert(a.startsWith('/Game/Brezi/NeighborProps20261002R39/'));return a.slice(6).split('.')[0]+'.uasset';}).sort();
  assert.equal(new Set(added).size,21);assert.deepEqual(Object.keys(after).sort(),[...Object.keys(before),...added].sort());
  assert(added.every(k=>!Object.hasOwn(before,k)));
  assert.deepEqual(Object.keys(before).filter(k=>{try{assert.deepEqual(before[k],after[k]);return false;}catch{return true;}}),['Brezi/Maps/Brezi.umap']);
  assert.deepEqual(delta,{newPackages,newRelativeContentFiles:added,onlyOriginalMapChanged:true});
}
export function validateOriginalActorPreservation(before,saved,groups){
  assert.equal(Object.keys(before).length,5364);assert.equal(Object.keys(saved).length,5368);
  const added=Object.values(groups).map(g=>g.actor).sort();assert.equal(added.length,4);assert.equal(new Set(added).size,4);
  assert.deepEqual(Object.keys(saved).sort(),[...Object.keys(before),...added].sort());
  for(const[key,row]of Object.entries(before))assert.deepEqual(saved[key],row);
  assert(added.every(key=>!Object.hasOwn(before,key)));
  const hisms=Object.values(saved).flatMap(row=>row.components).filter(c=>c.class==='/Script/Engine.HierarchicalInstancedStaticMeshComponent');
  assert.equal(hisms.length,2329);assert.equal(hisms.reduce((n,c)=>n+c.instanceCount,0),678205);
}
export function validateMeasuredRepairContract(r,plan,pf){
  for(const key of ['binding','repairSchema','repairEvidence','nodePoseCalibration','constructorRepairEvidence','constructorCalibration']){
    assert.deepEqual(r[key],plan[key]);assert.deepEqual(r[key],pf[key]);
  }
  assert.equal(plan.privateMaterialBindingAdapter.onlyPrivateModuleBindingLoaderChanged,true);
  assert.equal(plan.privateMaterialBindingAdapter.originalSourceAndMaterialGraphKernelsUnchanged,true);
  assert.equal(plan.privateMaterialBindingAdapter.originalModulesOrSourceFilesMutated,false);
  assert.equal(plan.privateMaterialBindingAdapter.sourcePacketNarrowedToOriginalThreeKeys,true);
  assert.deepEqual(r.privateMaterialBindingAdapter,plan.privateMaterialBindingAdapter);
  assert.equal(r.repairEvidence.failedNativeProcessId,29845);assert.equal(r.repairEvidence.failedNativeExitCode,255);
  assert.equal(r.repairEvidence.inheritedExecutedR1TestCount,30);assert.equal(r.repairEvidence.nativeFullGeometryAcceptedFromFailure,false);
  for(const key of ['originalMapSaveReached','sourceGeometryOrPixelsEdited','epsilonOrToleranceRelaxationProposed','partialFailedProjectMapCopied'])assert.equal(r.repairEvidence[key],false);
  const exact=r.constructorRepairEvidence;
  assert.equal(exact.failedNativeProcessId,47288);assert.equal(exact.failedNativeExitCode,255);
  assert.equal(exact.readOnlyCompositionProcessId,74650);assert.equal(exact.sixAuthoredAssemblyRoots,6);assert.equal(exact.eightOriginalPartMembers,8);
  for(const key of ['originalDesiredPositiveZeroPolicyPreserved','newLocalConditionalFiniteIntermediateOnly'])assert.equal(exact[key],true);
  for(const key of ['originalMapSaveReached','sourceGeometryOrPixelsEdited','epsilonOrToleranceRelaxationProposed','globalZeroCanonicalizationUsed','partialFailedProjectMapCopied','nativeFullGeometryAcceptedFromDiagnostic'])assert.equal(exact[key],false);
  assert.equal(Object.keys(r.nodePoseCalibration).length,4);
  const coil=r.nodePoseCalibration['garden_hose_wall_mounted_01:1'];
  assert.deepEqual(coil.expectedF64CentimeterTranslation,[-1.3036099262535572,6.431593745946884,-5.608365684747696]);
  assert.deepEqual(coil.originalProposedF32CentimeterTranslation,[-1.3036099672317505,6.431593894958496,-5.608365535736084]);
  assert.notDeepEqual(coil.expectedF64CentimeterTranslation,coil.originalProposedF32CentimeterTranslation);
  for(const row of Object.values(r.nodePoseCalibration)){
    assert.equal(row.epsilonOrToleranceUsed,false);assert.equal(row.originalSourceGeometryAndNodeJsonEdited,false);
    assert.equal(row.futureFullOriginalCornerIdentityRequired,true);assert.equal(row.checkpointLabelsUsedForFutureGeometryIdentity,false);
    if(row.actualNodePoseObservedInR1Failure)assert.deepEqual(row.actualObservedNativeNodePose[0],row.expectedF64CentimeterTranslation);
  }
}
export function validatePlanReportBindings(plan,r){
  for(const [planKey,reportKey]of [['sourceProposal','sourceProposal'],['selectedNativeReport','baseNativeReport'],
    ['selectedRootImageDecision','selectedRootImageDecision'],['projectClone','projectClone']])assert.deepEqual(plan[planKey],r[reportKey]);
  assert.deepEqual(plan.selectedNativeProcess,r.baseNativeProcess);assert.deepEqual(plan.selectedCurrentByteAudit,r.baseCurrentByteAudit);
}
export function validateConstructorMeasurements(measured,calibration){
  assert.equal(Object.keys(calibration.sixRootConstructors).length,6);
  assert.equal(Object.keys(calibration.sourceNodes).length,4);
  assert.equal(Object.keys(calibration.compositions).length,4);
  assert.equal(calibration.allOriginalDesiredValuesPreservedBinary64,true);
  assert.equal(calibration.nativeSerializationValuesMeasuredNotRelaxed,true);assert.equal(calibration.epsilonOrToleranceUsed,false);
  assert.deepEqual(Object.keys(measured).sort(),Object.keys(calibration.compositions).sort());
  for(const [key,row] of Object.entries(calibration.sixRootConstructors)){
    assert.deepEqual(row.actualValues,row.expectedValues);assert.deepEqual(row.exactMismatchPaths,[]);
    assert.equal(row.onlyZeroBitMismatchUsesIntermediate,true);assert.equal(row.allOtherValuesWrittenWithoutAdaptation,true);
    assert(Object.is(row.actualValues[1][0],0)&&Object.is(row.actualValues[1][1],0),'Original authored positive zero bits must be preserved');
  }
  for(const [key,row] of Object.entries(calibration.sourceNodes))assert.deepEqual(row.actualValues,row.expectedValues);
  for(const [key,row] of Object.entries(calibration.compositions)){
    assert.deepEqual(measured[key].assemblyRootIds,row.assemblyRootIds);
    for(const field of ['assemblyInputValues','originalImportedNodeValues','composedInputValues','recoveredValues','storedMatrices'])assert.deepEqual(measured[key][field],row[field]);
    assert(row.inputMismatchPaths.every(v=>Array.isArray(v)&&v.length===0));
    assert(row.matrixTranslationMismatchPaths.every(v=>Array.isArray(v)&&v.length===0));
    assert.equal(row.transientInstancesAfterClear,0);assert.equal(row.unownedMeshless,true);assert.equal(row.registeredOrAttached,false);
  }
}
export function validatePropsRootAudit(a,r,{reportPin,processPin,rawPin}){
  assert.equal(a.schema,'brezi-r39c-root-saved-whole-original-neighbor-props-byte-audit-r3');assert.equal(a.schemaVersion,3);
  assert.equal(a.status,'verified-saved-native0-only-original-map-changed-21-new-owned-packages-all1294-frozen-pins-exact');
  assert.deepEqual(a.nativeReport,reportPin);assert.deepEqual(a.nativeProcess,processPin);assert.deepEqual(a.rawNativeProcess,rawPin);
  assert.equal(a.nativeProcessId,ACTUAL.nativePid);assert.equal(a.exitCode,0);assert.equal(a.rootSessionClosedExitCode,0);
  assert.equal(a.project,r.project);assert.deepEqual(a.projectClone,r.projectClone);
  for(const k of ['candidateOriginal4234NonMapFilesExact','onlyOriginalMapChanged','selectedR38bAll4235FilesExact',
    'initialIndependentCloneRowsStillIndependent','all1294FrozenSourcePinsExact','all1288PreflightSourcePinsExact','failedAttemptEvidenceRetained'])assert.equal(a[k],true);
  assert.deepEqual(a.currentContentInventory,r.afterContentInventory);assert.deepEqual(a.currentProtectedProof,r.protectedProjectProof);
  assert.equal(a.currentContentFiles,4124);assert.equal(a.currentProtectedFiles,132);assert.equal(a.currentProjectFiles,4256);
  assert.deepEqual(a.newRelativeContentFiles,r.assetDelta.newRelativeContentFiles);
  assert.deepEqual(a.newOwnedPackageTypes,{meshes:4,materialGraphs:3,originalTextureObjects:11,pipelines:3});
  assert.deepEqual(a.actualCounts,COUNTS);assert.equal(Object.keys(a.savedNativeProofFlags).length,6);
  for(const [key,value]of Object.entries(a.savedNativeProofFlags)){assert.equal(value,true);assert.equal(r[key],value);}
  for(const k of ['newNativeActorOrAttributeDecodeByAudit','nativeAppearanceAccepted','fullPhotorealismAccepted',
    'performanceAccepted','shippingVerified','activeOutputPromoted'])assert.equal(a[k],false);
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source);
  const previous=path.join(root,'scripts/unreal/exterior-editor-source-r29-r3.mjs');assert.equal(await sha(previous),R29_SHA);
  if(!names.includes(REPORT_NAME)){
    assert(!/^exterior-20261002-r39/.test(path.basename(source))&&!names.some(n=>/^neighbor-props-native-report/.test(n)),
      'Pending, failed or unknown props cannot delegate to an older family');
    const e=await loadR29(source,{root});e.additionalClosureFiles.push(previous);return e;
  }
  requireActualBinding();validatePropsReportNames(names);
  const reportPath=path.join(source,REPORT_NAME),r=await read(reportPath),project=path.join(source,'Project/BreziTwin'),closure=new Set([previous]);
  validatePropsHeader(r,{root,source});assert.equal(await sha(reportPath),ACTUAL.reportSha);
  async function pinned(row){
    assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);
    const st=await fs.lstat(row.path);assert(st.isFile()&&!st.isSymbolicLink());assert.equal(st.size,row.bytes);
    assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;
  }
  const pj=async row=>read(await pinned(row));
  const ownPin=async(file,hash)=>{const row={path:file,sha256:hash,bytes:(await fs.stat(file)).size};await pinned(row);return row;};
  const reportPin=await ownPin(reportPath,ACTUAL.reportSha);
  assert.equal(r.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261002-r38b/soft-ground-native-report-r2.json'));
  const base=await pj(r.baseNativeReport),baseProject=path.join(path.dirname(r.baseNativeReport.path),'Project/BreziTwin');
  assert.equal(base.schemaVersion,2);assert.equal(base.status,'verified-saved-image-selected-fixed-world-soft-ground-material-overlay');
  assert.equal(base.nativeProcessId,72504);assert.equal(base.nativeApplied,true);assert.equal(base.savedMapUnloadedReloaded,true);
  const plan=await pj(r.selectedPlan),pf=await pj(r.sourcePreflight);
  assert.equal(r.selectedPlan.path,path.join(root,'output/unreal/exterior-neighbor-props-20261002-r39-native-study-r3/neighbor-props-native-plan-r3.json'));
  assert.equal(plan.schema,SCHEMA);assert.equal(plan.schemaVersion,3);assert.equal(plan.nativeOwner,OWNER);
  assert.equal(plan.owner,'scripts/unreal/exterior-neighbor-props-native-study-r39-r3.py');
  assert.equal(plan.status,'image-selected-whole-original-neighbor-props-source-ready-native-r3-pending');
  assert.equal(pf.schema,SCHEMA);assert.equal(pf.schemaVersion,3);assert.equal(pf.owner,OWNER);
  assert.equal(pf.status,'image-selected-whole-original-neighbor-props-preflight-validated-native-r3-pending');
  assert.equal(pf.tests.exitCode,0);assert.equal(pf.tests.testCount,9);await pinned(pf.tests.log);for(const row of pf.tests.sources)await pinned(row);
  assert.deepEqual(pf.selectedPlan,r.selectedPlan);assert.deepEqual(pf.inputFiles,r.inputFiles);validateMeasuredRepairContract(r,plan,pf);
  validatePlanReportBindings(plan,r);
  for(const key of ['sourceProposal','baseNativeProcess','baseCurrentByteAudit','selectedRootImageDecision'])await pinned(r[key]);
  for(const[file,hash]of Object.entries(r.inputFiles))await ownPin(file,hash);
  for(const[file,row]of Object.entries(plan.ownedSources)){
    await pinned(row);const snapshot=plan.ownedSourceSnapshots[file];assert.equal(snapshot.sha256,row.sha256);assert.equal(snapshot.bytes,row.bytes);await pinned(snapshot);
  }
  for(const row of Object.values(plan.primaryApi))await pinned(row);
  for(const key of ['failedNativeReport','failedNativeProcess','rootCurrentFailureByteAudit','observedOriginalNodeCheckpoint','inheritedExecutedR1Preflight'])await pinned(r.repairEvidence[key]);
  for(const value of Object.values(r.constructorRepairEvidence))if(value&&typeof value==='object'&&Object.hasOwn(value,'path'))await pinned(value);
  const constructorFailed=await pj(r.constructorRepairEvidence.failedNativeReport);assert.equal(constructorFailed.nativeProcessId,47288);assert.equal(constructorFailed.nativeApplied,false);
  const failed=await pj(r.repairEvidence.failedNativeReport);assert.equal(failed.nativeApplied,false);assert.equal(failed.savedMapUnloadedReloaded,false);
  assert.equal(failed.nativeProcessId,29845);
  const baseSaved=await pj(base.savedActorWitness),before=await pj(r.beforeActorWitness),expected=await pj(r.expectedActorWitness),saved=await pj(r.savedActorWitness);
  assert.deepEqual(before,baseSaved);assert.deepEqual(expected,saved);assert.equal(r.expectedActorWitnessSha256,r.savedActorWitnessSha256);
  validateOriginalActorPreservation(before,saved,r.newOwnedGroups);
  for(const[a,b]of [['rawInstanceControlsBefore','rawInstanceControlsSaved'],['originalMaterialWitnessBefore','originalMaterialWitnessSaved'],['originalTextureWitnessBefore','originalTextureWitnessSaved']])assert.deepEqual(await pj(r[a]),await pj(r[b]));
  assert.deepEqual(await pj(r.rawInstanceControlsBefore),await pj(base.rawInstanceControlsSaved));
  for(const phase of ['before','saved']){assert.equal(r.materialGraphDiagnosticFiles[phase].length,66);for(const row of r.materialGraphDiagnosticFiles[phase])await pinned(row);}
  const measured=await pj(r.newSourceNativeMeasurements);assert.equal(Object.keys(measured).length,4);validateConstructorMeasurements(measured,r.constructorCalibration);
  const built=await pj(r.newMaterialReport);assert.deepEqual(built,r.materialReport);assert.deepEqual(built.nativeBinding,r.binding);
  assert.equal(built.materialCount,3);assert.equal(built.textureObjectCount,11);assert.equal(built.newPackageAssets.length,14);
  assert(Object.values(built.materials).every(row=>row.instancedStaticMeshUsage===true&&row.compileErrors.length===0));
  const geometry=await pj(r.nativeGeometryReadbackReceipt);assert.deepEqual(geometry,r.nativeGeometryReadback);
  assert.equal(Object.keys(geometry).length,4);assert.equal(Object.values(geometry).reduce((v,row)=>v+row.triangles,0),26601);await pinned(r.importReadback);
  const baseContent=await pj(r.baseContentInventory);assert.deepEqual(r.baseContentInventory,base.afterContentInventory);
  const contentInventory=await pj(r.afterContentInventory);assert.deepEqual(r.newPackages,plan.expectedNewPackageAssets);
  validatePropsContent(baseContent,contentInventory,r.newPackages,r.assetDelta);
  assert.deepEqual(r.protectedProjectProof,base.protectedProjectProof);const projectProof=await pj(r.protectedProjectProof);assert.equal(Object.keys(projectProof).length,132);
  assert.equal(r.projectClone.sha256,CLONE_SHA);const clone=await pj(r.projectClone);
  assert.equal(clone.schema,'brezi-image-selected-saved-r38b-whole-props-project-clone-r39');assert.equal(clone.schemaVersion,3);
  assert.equal(clone.status,'verified-byte-identical-independent-apfs-image-selected-r38b-before-whole-original-neighbor-props-exact-local-zero-constructor-repair-r39-r3');
  assert.equal(clone.project,project);assert.equal(clone.sourceProject,baseProject);assert.equal(clone.fileCount,4235);assert.equal(clone.contentFiles,4103);assert.equal(clone.protectedFiles,132);
  assert.equal(clone.nativeExecuted,false);assert.deepEqual(clone.sourceNativeReport,r.baseNativeReport);assert.deepEqual(clone.sourceNativeProcess,r.baseNativeProcess);
  assert.deepEqual(clone.sourceCurrentByteAudit,r.baseCurrentByteAudit);assert.deepEqual(clone.rootImageBaseSelection,r.selectedRootImageDecision);
  const original={...Object.fromEntries(Object.entries(baseContent).map(([k,v])=>['Content/'+k,v])),...projectProof},seen=new Set();assert.equal(clone.files.length,4235);
  for(const row of clone.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(original,relative)&&!seen.has(relative));seen.add(relative);
    assert.equal(row.source,path.join(baseProject,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);
    assert.deepEqual({sha256:row.sha256,bytes:row.bytes},original[relative]);const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);
    assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);
  }
  assert.deepEqual([...seen].sort(),Object.keys(original).sort());await pinned(clone.rootController);
  const views=await read(path.join(project,'Content/Data/viewpoints.json'));assert.deepEqual(views,await read(path.join(baseProject,'Content/Data/viewpoints.json')));
  for(const id of ['exterior-garden','exterior-neighborhood','neighbor-finish-close-r18'])assert.equal(views.views.filter(v=>v.id===id).length,1);
  const rawPath=path.join(source,'neighbor-props-native-r39-r3.log.json'),processPath=path.join(source,'neighbor-props-native-r39-r3-process.json');
  const rawPin=await ownPin(rawPath,ACTUAL.rawSha),processPin=await ownPin(processPath,ACTUAL.processSha),raw=await read(rawPath),terminal=await read(processPath);
  assert.equal(raw.pid,ACTUAL.nativePid);assert.equal(raw.code,0);assert.equal(raw.signal,null);
  assert.equal(raw.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(raw.args[0],path.join(project,'BreziTwin.uproject'));
  assert(Number.isFinite(Date.parse(raw.startedAt))&&Date.parse(raw.endedAt)>=Date.parse(raw.startedAt));
  assert.equal(terminal.processFile,rawPath);assert.equal(terminal.processFileSha256,ACTUAL.rawSha);assert.equal(terminal.reportSha256,ACTUAL.reportSha);
  assert.equal(terminal.logFile,path.join(source,'neighbor-props-native-r39-r3.log'));await ownPin(terminal.logFile,terminal.logSha256);
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+terminal.logFile])assert(raw.args.includes(arg));
  assert.equal(terminal.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(terminal.sourcePinsBeforeNative).length,ACTUAL.terminalPins);
  for(const[file,hash]of Object.entries(r.inputFiles))assert.equal(terminal.sourcePinsBeforeNative[file],hash);
  for(const[file,hash]of Object.entries(terminal.sourcePinsBeforeNative))await ownPin(file,hash);
  assert.equal(terminal.controllerSha256BeforeNative,MONITOR_SHA);assert.equal(terminal.controllerSha256AfterNative,MONITOR_SHA);await ownPin(terminal.controller,MONITOR_SHA);
  const auditPath=path.join(source,'root-native-success-byte-audit-r39c-r3.json');await ownPin(auditPath,ACTUAL.auditSha);
  const audit=await read(auditPath);validatePropsRootAudit(audit,r,{reportPin,processPin,rawPin});
  await pinned(audit.rootController);await pinned(audit.byteValidationHelper);
  const w=r.nativeModuleWitness,module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');
  assert.equal(w.source,path.join(baseProject,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.destination,module);
  assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);for(const file of [module,w.source])await ownPin(file,MODULE_SHA);
  const checker=path.join(root,'scripts/unreal/exterior-neighbor-props-editor-check-r30.py');await ownPin(checker,ACTUAL.checkerSha);
  const checked=JSON.parse((await exec('python3',['-B',checker,reportPath],{timeout:240000,maxBuffer:2*1024*1024})).stdout);
  assert.equal(checked.nativeProcessId,ACTUAL.nativePid);assert.equal(checked.savedActors,5368);assert.equal(checked.fullHismComponents,2329);assert.equal(checked.fullHismInstances,678205);
  assert.equal(checked.wholeActorCounterfactualValidated,true);assert.equal(checked.freshNativeActorOrGeometryDecodePerformedByCpuChecker,false);
  const summary={...checked,sourceReceiptPins:SOURCE_PINS,sourcePinsUnchangedAfterNative:ACTUAL.terminalPins,
    scope:'Six original whole prop assemblies/eight mesh instances added; all selected garden/yard actors, raw roots, material and texture policies preserved. Visibility and realism require the actual original images.'};
  return {mode:summary.mode,project,nativeReceiptPath:reportPath,base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:w,moduleWitnessSource:r.projectClone,
    receiptSummary:{baseNativeReport:r.baseNativeReport,selectedPlan:r.selectedPlan,sourcePreflight:r.sourcePreflight,repairEvidence:r.repairEvidence,summary}};
}
