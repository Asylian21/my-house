// Purposeful yard QA camera copies. The actual native source remains external.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR22,validateProjectClosure} from './exterior-editor-source-r22.mjs';
import {validateYardCameraViews,validateYardCameraContent} from './exterior-editor-source-r18.mjs';
export {validateYardCameraViews,validateYardCameraContent};
export {validateProjectClosure};
const SCHEMA='brezi-saved-r30-r32-matched-context-yard-camera-qa-clone-r23';
const SUPPLEMENT_SCHEMA='brezi-purposeful-first-context-yard-matched-camera-r18';
const OWNER='scripts/unreal/exterior-context-yard-camera-stage-r23.py';
const STAGE_SHA='d922b612e0aee51b3a15683ef0bdc2e78ca295ce8d6870d54725eeb9cb8a7dfe';
const CAMERA_OWNER='scripts/unreal/exterior-context-yard-camera-r18.py';
const CAMERA_SHA='16e28f057703904765b89b4e42c7fd995cb4586d3abff6f928d95973878eb22d';
const SUPPLEMENT_SHA='768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1';
const R22_SHA='305191a1d44a26219f57d5ec66fb792c1b82e1358210398955f2cbe617ec48a4';
const HISTORICAL_READER_SHA='46035c3982ec8e977873c46c1ff8dfa5a69a10d1aaa2f0d1f216ce89bf87ed2f';
const CLONER_SHA='606917f12bdfc04b8c8728600163817628f9ddf7b766bc957a9477a96af07c5f';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const VIEW='exterior-context-yard-572063-close-r18';
const CASES={
 'exterior-20261002-r30b-yard-close-baseline-r23':{kind:'saved-r30b-original-shape-garden-yard-baseline',source:'exterior-20261002-r30b',
 report:'garden-composition-native-report-r3.json',sha256:'67f6b002cd4ad11e0c518815ebf0224e1bb1f932b94361ae91472137dedd776d',
 process:'garden-composition-native-r3-process.json',content:4078,pid:89358},
 'exterior-20261002-r32a-yard-close-candidate-r23':{kind:'saved-r32a-resolved-yard-ground-low-detail-candidate',source:'exterior-20261002-r32a',
 report:'context-yard-ground-native-report.json',sha256:'99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19',
 process:'context-yard-ground-native-process.json',content:4086,pid:5443}
};
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const sha=async file=>{const h=createHash('sha256');for await(const chunk of createReadStream(file))h.update(chunk);return h.digest('hex');};

export function validateYardCameraStageHeader(stage,{source,root,names}){
  const selected=CASES[path.basename(source)];assert(selected,'Unknown purposeful yard QA clone');
  assert.equal(path.dirname(source),path.join(root,'output/unreal'));
  assert.equal(stage.schema,SCHEMA);assert.equal(stage.owner,OWNER);assert.equal(stage.status,'verified-independent-saved-r30-r32-yard-camera-data-only-qa-clone-r23');
  assert.equal(stage.sourceKind,selected.kind);assert.equal(stage.sourceNativeOutput,path.join(root,'output/unreal',selected.source));
  assert.equal(stage.project,path.join(source,'Project/BreziTwin'));assert.equal(stage.sourceNativeReport.sha256,selected.sha256);
  assert.equal(stage.sourceNativeReport.path,path.join(stage.sourceNativeOutput,selected.report));
  assert.equal(stage.sourceNativeProcess.path,path.join(stage.sourceNativeOutput,selected.process));
  assert.equal(stage.cameraSupplement.sha256,SUPPLEMENT_SHA);assert.equal(stage.stagingHelper.sha256,STAGE_SHA);
  assert.equal(stage.sourceReader.sha256,R22_SHA);assert.equal(stage.historicalCameraReader.sha256,HISTORICAL_READER_SHA);assert.equal(stage.sourceValidationExitCode,0);
  assert.equal(stage.cameraAuditScope,'FROZEN_R18_ORIGINAL_R27_R28_SOURCE_ONLY_REUSED_CAMERA_NOT_CURRENT_R29_R32_VEGETATION_VISIBILITY');assert.equal(stage.currentR29TreesAndR32LowGrowthVisibilityRecomputed,false);
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
  const previous=fileURLToPath(new URL('exterior-editor-source-r22.mjs',import.meta.url));assert.equal(await sha(previous),R22_SHA);
  const names=await fs.readdir(source),filename='context-yard-camera-stage-receipt-r23.json';
  if(!names.includes(filename)){
    assert(!Object.hasOwn(CASES,path.basename(source))&&!/yard.*camera.*stage.*receipt/i.test(names.join('\n'))&&!/yard-close.*r23/.test(source),
      'Purposeful camera QA clone requires its exact known staged receipt');
    const e=await loadR22(source,{root});e.additionalClosureFiles.push(previous);return e;
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
  const e=await loadR22(stage.sourceNativeOutput,{root});
  assert.equal(e.nativeReceiptPath,stage.sourceNativeReport.path);assert.equal(e.summary.nativeProcessId,selected.pid);
  assert.equal(Object.keys(e.contentInventory).length,selected.content);assert.equal(Object.keys(e.projectProof).length,132);
  const originalReport=await pj(stage.sourceNativeReport);await pinned(stage.sourceNativeProcess);
  assert.deepEqual(stage.protectedProjectProof,originalReport.protectedProjectProof);const projectProof=await pj(stage.protectedProjectProof);
  assert.deepEqual(projectProof,e.projectProof);
  assert.equal(stage.stagingHelper.path,path.join(root,OWNER));await pinned(stage.stagingHelper);
  assert.equal(stage.sourceReader.path,previous);await pinned(stage.sourceReader);
  assert.equal(stage.historicalCameraReader.path,path.join(root,'scripts/unreal/exterior-editor-source-r18.mjs'));await pinned(stage.historicalCameraReader);
  assert.equal(stage.cameraSupplement.path,path.join(root,'output/unreal/exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json'));
  const supplement=await pj(stage.cameraSupplement);
  assert.equal(supplement.inputFiles[path.join(root,CAMERA_OWNER)],CAMERA_SHA);
  for(const [file,h]of Object.entries(supplement.inputFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  assert.equal(supplement.baselineNativeReport.sha256,'5575c0e37a9d48733b5c7ed3746f1731cc2b7958634a845c87b9700ff4fc9498');
  assert.equal(supplement.candidateNativeReport.sha256,'dfbca65515fc08aea52515195ab5ef752fe07cdca622cd41964e99875ced2456');
  const original=await pj(supplement.originalViewpoints),appended=await pj(supplement.appendedViewpoints);
  validateYardCameraViews(original,supplement,appended);assert.deepEqual(stage.view,supplement.view);assert.deepEqual(stage.historicalR18SourceCameraAudit,supplement.sourceCameraAudit);
  const project=path.join(source,'Project/BreziTwin');
  assert.equal(stage.viewpointFile.path,path.join(project,'Content/Data/viewpoints.json'));
  assert.deepEqual({sha256:stage.viewpointFile.sha256,bytes:stage.viewpointFile.bytes},{sha256:supplement.appendedViewpoints.sha256,bytes:supplement.appendedViewpoints.bytes});
  await pinned(stage.viewpointFile);assert.deepEqual(await read(stage.viewpointFile.path),appended);
  assert.equal(stage.afterContentInventory.path,path.join(source,'context-yard-camera-content-after-r23.json'));
  const contentInventory=await pj(stage.afterContentInventory);validateYardCameraContent(e.contentInventory,contentInventory,supplement);
  assert.equal(stage.projectClone.path,path.join(source,'context-yard-camera-project-clone-r23.json'));const clone=await pj(stage.projectClone);
  assert.equal(clone.schema,SCHEMA);assert.equal(clone.status,'verified-byte-identical-independent-apfs-saved-r30-r32-yard-qa-clone-before-viewpoint-stage-r23');
  assert.equal(clone.project,project);assert.equal(clone.sourceProject,e.project);assert.deepEqual(clone.sourceNativeReport,stage.sourceNativeReport);
  assert.equal(clone.owner,'scripts/unreal/exterior-context-yard-camera-clone-r23.py');assert.equal(clone.cloneHelper.sha256,CLONER_SHA);assert.equal(clone.cloneHelper.path,path.join(root,clone.owner));await pinned(clone.cloneHelper);assert.equal(clone.sourceKind,selected.kind);assert.deepEqual(clone.sourceNativeProcess,stage.sourceNativeProcess);assert.equal(clone.sourceCurrentByteAudit.path,path.join(stage.sourceNativeOutput,selected.pid===5443?'root-native-byte-audit-r32a.json':'root-native-byte-audit-r30b.json'));await pinned(clone.sourceCurrentByteAudit);assert.equal(clone.fullSavedSourceReaderValidationPending,true);
  assert.equal(clone.nativeExecuted,false);assert.equal(clone.viewpointStagingPending,true);assert.equal(clone.cameraSupplement,null);
  assert.equal(clone.fileCount,selected.content+132);assert.equal(clone.contentFiles,selected.content);assert.equal(clone.protectedFiles,132);
  const originalFiles={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...projectProof};
  const observed=new Set();assert.equal(clone.files.length,Object.keys(originalFiles).length);
  for(const row of clone.files){
    const relative=path.relative(project,row.destination);assert(Object.hasOwn(originalFiles,relative)&&!observed.has(relative));observed.add(relative);
    assert.equal(row.source,path.join(e.project,relative));assert.equal(row.independentInodes,true);assert.deepEqual({sha256:row.sha256,bytes:row.bytes},originalFiles[relative]);
    const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);
  }
  assert.equal(stage.sourceValidation.path,path.join(source,'context-yard-camera-source-validation-r23.json'));const validation=await pj(stage.sourceValidation);
  assert.equal(validation.scope,'CPU_EXISTING_SAVED_R21_R22_NATIVE_RECEIPT_AND_SOURCE_CHECKS');assert.equal(validation.sourceNativeOutput,stage.sourceNativeOutput);
  assert.deepEqual(validation.reader,stage.sourceReader);assert.deepEqual(validation.summary,e.summary);assert.equal(validation.nativeLaunchedByStaging,false);
  for(const[file,h]of Object.entries(validation.closureFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const file of [...e.additionalClosureFiles,previous,stage.stagingHelper.path,clone.cloneHelper.path,stage.historicalCameraReader.path,stage.projectClone.path,stage.cameraSupplement.path,supplement.originalViewpoints.path,supplement.appendedViewpoints.path,...Object.keys(supplement.inputFiles)])assert(Object.hasOwn(validation.closureFiles,file),`Recorded CPU source closure is missing ${file}`);
  const module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');assert.equal(await sha(module),MODULE_SHA);closure.add(module);
  const nativeModuleWitness={source:path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),destination:module,
    sha256:MODULE_SHA,bytes:2818384,independentInodes:true};
  const summary={...e.summary,mode:'saved-r30-r32-exact-r18-context-yard-camera-qa-clone',sourceNativeMode:e.mode,sourceKind:selected.kind,
    supplementalViews:1,historicalR18WholeOriginalYardAndTwoCrownSupportsFramed:true,currentR29TreesAndR32LowGrowthVisibilityRecomputed:false,nativeCameraRuntimeVerified:false,
    nativeAppearanceAccepted:false,performanceAccepted:false,fullPhotorealismAccepted:false};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:e.base,summary,contentInventory,projectProof,
    additionalClosureFiles:[...new Set([...e.additionalClosureFiles,...closure])],nativeModuleWitness,moduleWitnessSource:stage.projectClone,
    receiptSummary:{sourceNativeReport:stage.sourceNativeReport,sourceNativeProcess:stage.sourceNativeProcess,
      cameraStageReceipt:receiptPath,cameraSupplement:stage.cameraSupplement,originalNativeSourceUnchanged:true,
      sourceNativeEvidence:e.receiptSummary,summary}};
}
