// Only the independent actual R39c clone with two exact Data insertions may dispatch.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadDirect,validateProjectClosure} from './exterior-editor-source-r30.mjs';
import {validateTwoCameraViews,validateTwoCameraContent} from './exterior-editor-source-r29-r2.mjs';
export {validateProjectClosure,validateTwoCameraViews,validateTwoCameraContent};
const SOURCE_NAME='exterior-20261002-r39c',QA_NAME='exterior-20261002-r39c-neighbor-props-two-camera-candidate-r30';
const REPORT_SHA='118f451095730e2ff0e62304d959626d4a81be53f03e41dd2229fe91831f4da5';
const PROCESS_SHA='2bbb88ee2d71a0d81469c267f263c22beaea4f2d49eba05618d9c8896c2e96e0';
const AUDIT_SHA='7f70d6eb3c59e87305313ba35b7cf7324fde14e80507b5d06e3eaecce7f17ad5';
const CLONE_SHA='5254c26639a576bcc69d58e9f0f605d00a7132722048429df0bbddd8cadc9e28';
const SUPPLEMENT_SHA='768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1';
const PROPOSAL_SHA='ab77379c4f97dd351b15c4e48d0791825ec3f5eab685efddc659bad6cb9ec996';
const COVERAGE_SHA='7289ae6b35179c75c55e3a43227d750c76be80d6b52b382d4d5b76d48833528f';
const TEMPLATE_SHA='b319d30f73c452a22cb63145f4d2854a7c80d05ef3c2d8bd0936f7016d50e23a';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
// Remain null until the direct reader and the one Data-only stage actually close.
const DIRECT_SHA='8bbcb822f0b6065a5839f85811b611cc3a4da880b6c0d1d4f9d5c0984a8c307f',STAGER_SHA='bc9ec11ea1da046b7a881e60f2335cafe2b400bc10a5d356cd2adb7802849e5c',STAGE_SHA='f52d06b5c595e27231ad8bea99e25c4b47d6604286db3b7fb743a8501fdc78a5';
const SCHEMA='brezi-saved-original-neighbor-props-r39r3-two-camera-data-only-qa-clone-r30';
const STATUS='verified-independent-saved-original-r39r3-two-camera-data-only-qa-clone-r30';
const CLONE_SCHEMA='brezi-original-neighbor-props-two-camera-independent-qa-project-clone-r30';
const CLONE_STATUS='verified-byte-identical-independent-apfs-actual-saved-r39c-before-two-camera-data-only-stage-r30';
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const sha=async p=>{const h=createHash('sha256');for await(const b of createReadStream(p))h.update(b);return h.digest('hex');};
const bytesSha=b=>createHash('sha256').update(b).digest('hex');
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);

export function validateCameraStageHeader(s,{source,root,names}){
  assert.equal(source,path.join(root,'output/unreal',QA_NAME));assert.equal(s.schema,SCHEMA);assert.equal(s.schemaVersion,1);
  assert.equal(s.owner,'scripts/unreal/exterior-neighbor-props-camera-stage-r30.py');assert.equal(s.status,STATUS);
  assert.equal(s.sourceNativeOutput,path.join(root,'output/unreal',SOURCE_NAME));
  for(const[k,h]of Object.entries({sourceNativeReport:REPORT_SHA,sourceNativeProcess:PROCESS_SHA,sourceCurrentByteAudit:AUDIT_SHA,projectClone:CLONE_SHA}))assert.equal(s[k].sha256,h);
  assert.equal(s.sourceNativeReport.path,path.join(s.sourceNativeOutput,'neighbor-props-native-report-r3.json'));
  assert.equal(s.sourceNativeProcess.path,path.join(s.sourceNativeOutput,'neighbor-props-native-r39-r3-process.json'));
  assert.equal(s.sourceCurrentByteAudit.path,path.join(s.sourceNativeOutput,'root-native-success-byte-audit-r39c-r3.json'));
  assert.equal(s.project,path.join(source,'Project/BreziTwin'));assert.equal(s.frozenCloseSupplement.sha256,SUPPLEMENT_SHA);
  assert.equal(s.cameraProposal.sha256,PROPOSAL_SHA);assert.equal(s.appendedViewCount,2);
  assert.equal(s.originalContentFileCount,4124);assert.equal(s.protectedFileCount,132);
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
  assert.equal(source,path.join(root,'output/unreal',QA_NAME),'Only actual staged R39c two-camera clone accepted');
  assert(hashLike(DIRECT_SHA)&&hashLike(STAGER_SHA)&&hashLike(STAGE_SHA),'Actual direct reader and closed Data stage pins are pending');
  const names=await fs.readdir(source),receiptPath=path.join(source,'neighbor-props-camera-stage-receipt-r30.json');
  assert.equal(await sha(receiptPath),STAGE_SHA);const stage=await read(receiptPath);
  validateCameraStageHeader(stage,{source,root,names});
  const direct=fileURLToPath(new URL('exterior-editor-source-r30.mjs',import.meta.url));assert.equal(await sha(direct),DIRECT_SHA);
  const template=fileURLToPath(new URL('exterior-editor-source-r29-r2.mjs',import.meta.url));assert.equal(await sha(template),TEMPLATE_SHA);
  const e=await loadDirect(stage.sourceNativeOutput,{root}),closure=new Set([...e.additionalClosureFiles,receiptPath,direct,template,fileURLToPath(import.meta.url)]);
  async function pinned(row){assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);
    const st=await fs.lstat(row.path);assert(st.isFile()&&!st.isSymbolicLink());assert.equal(st.size,row.bytes);assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;}
  const pj=async row=>read(await pinned(row));
  assert.equal(stage.sourceReader.path,direct);assert.equal(stage.sourceReader.sha256,DIRECT_SHA);await pinned(stage.sourceReader);
  assert.equal(stage.stagingHelper.path,path.join(root,'scripts/unreal/exterior-neighbor-props-camera-stage-r30.py'));assert.equal(stage.stagingHelper.sha256,STAGER_SHA);await pinned(stage.stagingHelper);
  for(const k of ['sourceNativeReport','sourceNativeProcess','sourceCurrentByteAudit'])await pinned(stage[k]);
  assert.equal(stage.frozenCloseSupplement.path,path.join(root,'output/unreal/exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json'));
  const supplement=await pj(stage.frozenCloseSupplement),proposal=await pj(stage.cameraProposal);
  assert.equal(stage.cameraProposal.path,path.join(root,'output/unreal/exterior-context-yard-soft-coherence-20261002-r38-editor-r29-r3-camera/camera-proposal.json'));
  assert.equal(proposal.sourceCoverageAudit.sha256,COVERAGE_SHA);await pinned(proposal.sourceCoverageAudit);
  assert.equal(proposal.nativeCameraRuntimeVerified,false);assert.equal(proposal.savedNativeReport.sha256,'077e36066dc49f2c3fa379893c39fc5659e8261385030d86266316e1bde9f2b9'); // Immutable historical source framing, not a current visibility proof.
  assert.equal(stage.sourceOriginalViewpoints.path,path.join(e.project,'Content/Data/viewpoints.json'));const originalPath=await pinned(stage.sourceOriginalViewpoints);
  const project=path.join(source,'Project/BreziTwin');assert.equal(stage.viewpointFile.path,path.join(project,'Content/Data/viewpoints.json'));
  const payloadPath=await pinned(stage.viewpointFile),original=await fs.readFile(originalPath),payload=await fs.readFile(payloadPath);
  assert.deepEqual(stage.views,[supplement.view,proposal.proposedView]);assert.equal(stage.protectedOriginalNonDataProjectFiles,4255);
  assert.equal(stage.originalDataByteInsertionProof.insertedBytes,1048);assert.equal(stage.originalDataByteInsertionProof.insertedBytesSha256,'480f82e38d3d2e7b2c8bdbe0f8dc3a7be016f1b25bdc03f5b4bba6ffa247c300');
  validateByteInsertion(original,payload,stage.originalDataByteInsertionProof,supplement.view,proposal.proposedView);
  assert.equal(stage.afterContentInventory.path,path.join(source,'neighbor-props-camera-content-after-r30.json'));
  const contentInventory=await pj(stage.afterContentInventory);validateTwoCameraContent(e.contentInventory,contentInventory,stage.viewpointFile);
  const clone=await pj(stage.projectClone);assert.equal(stage.projectClone.path,path.join(source,'neighbor-props-camera-project-clone-r30.json'));
  assert.equal(clone.schema,CLONE_SCHEMA);assert.equal(clone.schemaVersion,1);assert.equal(clone.status,CLONE_STATUS);
  assert.equal(clone.sourceProject,e.project);assert.equal(clone.project,project);assert.equal(clone.fileCount,4256);assert.equal(clone.contentFiles,4124);assert.equal(clone.protectedFiles,132);
  assert.equal(clone.nativeExecuted,false);assert.equal(clone.viewpointStagingPending,true);assert.equal(clone.fullSavedSourceReaderValidationPending,true);assert.equal(clone.cameraSupplement,null);
  for(const k of ['sourceNativeReport','sourceNativeProcess','sourceCurrentByteAudit'])assert.deepEqual(clone[k],stage[k]);
  await pinned(clone.byteValidationHelper);await pinned(clone.rootController);
  const originalFiles={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...e.projectProof},seen=new Set();
  assert.equal(clone.files.length,4256);
  for(const row of clone.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(originalFiles,relative)&&!seen.has(relative));seen.add(relative);
    assert.equal(row.source,path.join(e.project,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);
    assert.deepEqual({sha256:row.sha256,bytes:row.bytes},originalFiles[relative]);
    const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);}
  assert.deepEqual([...seen].sort(),Object.keys(originalFiles).sort());
  assert.equal(stage.sourceValidation.path,path.join(source,'neighbor-props-camera-source-validation-r30.json'));
  const validation=await pj(stage.sourceValidation);assert.equal(validation.scope,'CPU_CLOSED_SAVED_R39R3_NATIVE_RECEIPTS_AND_SOURCE_COUNTERFACTUAL');
  assert.deepEqual(validation.summary,e.summary);assert.equal(validation.nativeLaunchedByStaging,false);
  for(const[file,h]of Object.entries(validation.closureFiles)){const st=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:st.size});}
  for(const file of [...e.additionalClosureFiles,direct,stage.stagingHelper.path,stage.projectClone.path,stage.frozenCloseSupplement.path,stage.cameraProposal.path,proposal.sourceCoverageAudit.path])assert(Object.hasOwn(validation.closureFiles,file),'Stage missing immutable actual saved source/camera input');
  const nativeModuleWitness={source:path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),destination:path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),sha256:MODULE_SHA,bytes:2818384,independentInodes:true};
  await pinned({path:nativeModuleWitness.destination,sha256:MODULE_SHA,bytes:2818384});
  const summary={...e.summary,mode:'saved-r39r3-exact-two-camera-data-only-qa-clone',supplementalViews:2,currentVegetationVisibilityRecomputed:false,nativeCameraRuntimeVerified:false,walkingOrCollisionAccepted:false};
  return{...e,mode:summary.mode,project,nativeReceiptPath:receiptPath,summary,contentInventory,additionalClosureFiles:[...closure],nativeModuleWitness,moduleWitnessSource:stage.projectClone,
    receiptSummary:{sourceNativeReport:stage.sourceNativeReport,sourceNativeProcess:stage.sourceNativeProcess,cameraStageReceipt:receiptPath,twoCameraSourceProposal:stage.cameraProposal,sourceNativeEvidence:e.receiptSummary,summary}};
}
