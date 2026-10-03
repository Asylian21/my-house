// Only the independent actual R38b clone with two exact Data insertions may dispatch.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadDirect,validateProjectClosure} from './exterior-editor-source-r29-r3.mjs';
import {validateTwoCameraViews,validateTwoCameraContent} from './exterior-editor-source-r29-r2.mjs';
export {validateProjectClosure,validateTwoCameraViews,validateTwoCameraContent};
const SOURCE_NAME='exterior-20261002-r38b',QA_NAME='exterior-20261002-r38b-two-camera-candidate-r29-r3';
const REPORT_SHA='077e36066dc49f2c3fa379893c39fc5659e8261385030d86266316e1bde9f2b9';
const PROCESS_SHA='c5fb163aa2989503b842d17dd464ec5baae88f881a3f543207101a7f640fa3e5';
const AUDIT_SHA='a30063dc99bd3fa3fcd7d202aa77209b74f36c06bde77a47fba1c071564c5edb';
const CLONE_SHA='08a3e767db06eaa2d96a7466533faa883b4f61100670999358fa4ca4fbe3c536';
const SUPPLEMENT_SHA='768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1';
const PROPOSAL_SHA='ab77379c4f97dd351b15c4e48d0791825ec3f5eab685efddc659bad6cb9ec996';
const COVERAGE_SHA='7289ae6b35179c75c55e3a43227d750c76be80d6b52b382d4d5b76d48833528f';
const TEMPLATE_SHA='b319d30f73c452a22cb63145f4d2854a7c80d05ef3c2d8bd0936f7016d50e23a';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
// Remain null until the direct reader and the one Data-only stage actually close.
const DIRECT_SHA='73562897b5fd762cb1c712bf65a591e3a742d4e22f998fe4f838138b97fb6ebf',STAGER_SHA='ce4658f17dc0d25b2b70f346c1955818b9d68acd6c612628de542593b9a1f6c3',STAGE_SHA='3808d7d6a63c81b3ac83ed9aa44912af64de1a588561c4debbfdd6316d72d020';
const SCHEMA='brezi-saved-r38r2-two-camera-data-only-qa-clone-r29-r3';
const STATUS='verified-independent-saved-r38r2-two-camera-data-only-qa-clone-r29-r3';
const CLONE_SCHEMA='brezi-saved-r38b-two-camera-qa-clone-r29-r3';
const CLONE_STATUS='verified-byte-identical-independent-apfs-saved-r38b-two-camera-qa-clone-before-viewpoint-stage-r29-r3';
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const sha=async p=>{const h=createHash('sha256');for await(const b of createReadStream(p))h.update(b);return h.digest('hex');};
const bytesSha=b=>createHash('sha256').update(b).digest('hex');
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);

export function validateCameraStageHeader(s,{source,root,names}){
  assert.equal(source,path.join(root,'output/unreal',QA_NAME));assert.equal(s.schema,SCHEMA);assert.equal(s.schemaVersion,1);
  assert.equal(s.owner,'scripts/unreal/exterior-soft-ground-camera-stage-r29-r3.py');assert.equal(s.status,STATUS);
  assert.equal(s.sourceNativeOutput,path.join(root,'output/unreal',SOURCE_NAME));
  for(const[k,h]of Object.entries({sourceNativeReport:REPORT_SHA,sourceNativeProcess:PROCESS_SHA,sourceCurrentByteAudit:AUDIT_SHA,projectClone:CLONE_SHA}))assert.equal(s[k].sha256,h);
  assert.equal(s.sourceNativeReport.path,path.join(s.sourceNativeOutput,'soft-ground-native-report-r2.json'));
  assert.equal(s.sourceNativeProcess.path,path.join(s.sourceNativeOutput,'soft-ground-native-r2-process.json'));
  assert.equal(s.sourceCurrentByteAudit.path,path.join(s.sourceNativeOutput,'root-native-success-byte-audit-r38b-r2.json'));
  assert.equal(s.project,path.join(source,'Project/BreziTwin'));assert.equal(s.frozenCloseSupplement.sha256,SUPPLEMENT_SHA);
  assert.equal(s.cameraProposal.sha256,PROPOSAL_SHA);assert.equal(s.appendedViewCount,2);
  assert.equal(s.originalContentFileCount,4103);assert.equal(s.protectedFileCount,132);
  assert.deepEqual(s.changedContentFiles,['Data/viewpoints.json']);
  for(const k of ['originalViewsPrefixPreserved','lightingUnchanged','nativeSourceUnchanged','allOriginalProjectFilesIndependentBeforeStage'])assert.equal(s[k],true);
  for(const k of ['sceneMapChanged','nativeExecuted','nativeCameraRuntimeVerified','nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted','shippingPackageProduced','currentVegetationVisibilityRecomputed','walkingOrCollisionAccepted'])assert.equal(s[k],false);
  assert.equal(s.sourceCameraScope,'FROZEN_R18_CLOSE_PLUS_R37_SOURCE_FRAMING_ONLY_GROUND_VIEW');
  assert(!names.some(n=>/exterior-import-report|native-report|overlay-report/.test(n)),'QA clone cannot carry copied native receipts');
}

export function validateByteInsertion(original,payload,proof,closeView,groundView){
  const n=proof.insertionOffsetBytes,count=proof.insertedBytes;
  assert(Number.isInteger(n)&&n>0&&n<original.length&&Number.isInteger(count)&&count>0);
  assert.equal(proof.allOriginalDataBytesPreservedOutsideInsertion,true);
  assert.equal(proof.originalFileSha256,bytesSha(original));assert.equal(proof.originalPrefixSha256,bytesSha(original.subarray(0,n)));
  assert.equal(proof.originalSuffixSha256,bytesSha(original.subarray(n)));
  // Read the hash-bound Python insertion bytes directly. JS serialization would
  // erase authored float spelling (35.0 -> 35) despite an identical camera.
  const inserted=payload.subarray(n,n+count);
  assert.equal(inserted.length,count);assert.equal(inserted.subarray(0,2).toString(),',\n');
  assert.equal(proof.insertedBytesSha256,bytesSha(inserted));
  assert.deepEqual(JSON.parse('['+inserted.subarray(1).toString('utf8')+']'),[closeView,groundView]);
  assert.deepEqual(payload,Buffer.concat([original.subarray(0,n),inserted,original.subarray(n)]));
  validateTwoCameraViews(JSON.parse(original),closeView,groundView,JSON.parse(payload));
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);
  assert.equal(source,path.join(root,'output/unreal',QA_NAME),'Only actual staged R38b two-camera clone accepted');
  assert(hashLike(DIRECT_SHA)&&hashLike(STAGER_SHA)&&hashLike(STAGE_SHA),'Actual direct reader and closed Data stage pins are pending');
  const names=await fs.readdir(source),receiptPath=path.join(source,'soft-ground-camera-stage-receipt-r29-r3.json');
  assert.equal(await sha(receiptPath),STAGE_SHA);const stage=await read(receiptPath);
  validateCameraStageHeader(stage,{source,root,names});
  const direct=fileURLToPath(new URL('exterior-editor-source-r29-r3.mjs',import.meta.url));assert.equal(await sha(direct),DIRECT_SHA);
  const template=fileURLToPath(new URL('exterior-editor-source-r29-r2.mjs',import.meta.url));assert.equal(await sha(template),TEMPLATE_SHA);
  const e=await loadDirect(stage.sourceNativeOutput,{root}),closure=new Set([...e.additionalClosureFiles,receiptPath,direct,template,fileURLToPath(import.meta.url)]);
  async function pinned(row){assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);
    const st=await fs.lstat(row.path);assert(st.isFile()&&!st.isSymbolicLink());assert.equal(st.size,row.bytes);assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;}
  const pj=async row=>read(await pinned(row));
  assert.equal(stage.sourceReader.path,direct);assert.equal(stage.sourceReader.sha256,DIRECT_SHA);await pinned(stage.sourceReader);
  assert.equal(stage.stagingHelper.path,path.join(root,'scripts/unreal/exterior-soft-ground-camera-stage-r29-r3.py'));assert.equal(stage.stagingHelper.sha256,STAGER_SHA);await pinned(stage.stagingHelper);
  for(const k of ['sourceNativeReport','sourceNativeProcess','sourceCurrentByteAudit'])await pinned(stage[k]);
  assert.equal(stage.frozenCloseSupplement.path,path.join(root,'output/unreal/exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json'));
  const supplement=await pj(stage.frozenCloseSupplement),proposal=await pj(stage.cameraProposal);
  assert.equal(stage.cameraProposal.path,path.join(root,'output/unreal/exterior-context-yard-soft-coherence-20261002-r38-editor-r29-r3-camera/camera-proposal.json'));
  assert.equal(proposal.sourceCoverageAudit.sha256,COVERAGE_SHA);await pinned(proposal.sourceCoverageAudit);
  assert.equal(proposal.nativeCameraRuntimeVerified,false);assert.deepEqual(proposal.savedNativeReport,stage.sourceNativeReport);
  assert.equal(stage.sourceOriginalViewpoints.path,path.join(e.project,'Content/Data/viewpoints.json'));const originalPath=await pinned(stage.sourceOriginalViewpoints);
  const project=path.join(source,'Project/BreziTwin');assert.equal(stage.viewpointFile.path,path.join(project,'Content/Data/viewpoints.json'));
  const payloadPath=await pinned(stage.viewpointFile),original=await fs.readFile(originalPath),payload=await fs.readFile(payloadPath);
  assert.deepEqual(stage.views,[supplement.view,proposal.proposedView]);
  validateByteInsertion(original,payload,stage.originalDataByteInsertionProof,supplement.view,proposal.proposedView);
  assert.equal(stage.afterContentInventory.path,path.join(source,'soft-ground-camera-content-after-r29-r3.json'));
  const contentInventory=await pj(stage.afterContentInventory);validateTwoCameraContent(e.contentInventory,contentInventory,stage.viewpointFile);
  const clone=await pj(stage.projectClone);assert.equal(stage.projectClone.path,path.join(source,'soft-ground-camera-project-clone-r29-r3.json'));
  assert.equal(clone.schema,CLONE_SCHEMA);assert.equal(clone.schemaVersion,1);assert.equal(clone.status,CLONE_STATUS);
  assert.equal(clone.sourceProject,e.project);assert.equal(clone.project,project);assert.equal(clone.fileCount,4235);assert.equal(clone.contentFiles,4103);assert.equal(clone.protectedFiles,132);
  assert.equal(clone.nativeExecuted,false);assert.equal(clone.viewpointStagingPending,true);assert.equal(clone.fullSavedSourceReaderValidationPending,true);assert.equal(clone.cameraSupplement,null);
  for(const k of ['sourceNativeReport','sourceNativeProcess','sourceCurrentByteAudit'])assert.deepEqual(clone[k],stage[k]);
  await pinned(clone.byteValidationHelper);await pinned(clone.rootController);
  const originalFiles={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...e.projectProof},seen=new Set();
  assert.equal(clone.files.length,4235);
  for(const row of clone.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(originalFiles,relative)&&!seen.has(relative));seen.add(relative);
    assert.equal(row.source,path.join(e.project,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);
    assert.deepEqual({sha256:row.sha256,bytes:row.bytes},originalFiles[relative]);
    const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);}
  assert.deepEqual([...seen].sort(),Object.keys(originalFiles).sort());
  assert.equal(stage.sourceValidation.path,path.join(source,'soft-ground-camera-source-validation-r29-r3.json'));
  const validation=await pj(stage.sourceValidation);assert.equal(validation.scope,'CPU_CLOSED_SAVED_R38R2_NATIVE_RECEIPTS_AND_SOURCE_COUNTERFACTUAL');
  assert.deepEqual(validation.summary,e.summary);assert.equal(validation.nativeLaunchedByStaging,false);
  for(const[file,h]of Object.entries(validation.closureFiles)){const st=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:st.size});}
  for(const file of [...e.additionalClosureFiles,direct,stage.stagingHelper.path,stage.projectClone.path,stage.frozenCloseSupplement.path,stage.cameraProposal.path,proposal.sourceCoverageAudit.path])assert(Object.hasOwn(validation.closureFiles,file),'Stage missing immutable actual saved source/camera input');
  const nativeModuleWitness={source:path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),destination:path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),sha256:MODULE_SHA,bytes:2818384,independentInodes:true};
  await pinned({path:nativeModuleWitness.destination,sha256:MODULE_SHA,bytes:2818384});
  const summary={...e.summary,mode:'saved-r38r2-exact-two-camera-data-only-qa-clone',supplementalViews:2,currentVegetationVisibilityRecomputed:false,nativeCameraRuntimeVerified:false,walkingOrCollisionAccepted:false};
  return{...e,mode:summary.mode,project,nativeReceiptPath:receiptPath,summary,contentInventory,additionalClosureFiles:[...closure],nativeModuleWitness,moduleWitnessSource:stage.projectClone,
    receiptSummary:{sourceNativeReport:stage.sourceNativeReport,sourceNativeProcess:stage.sourceNativeProcess,cameraStageReceipt:receiptPath,twoCameraSourceProposal:stage.cameraProposal,sourceNativeEvidence:e.receiptSummary,summary}};
}
