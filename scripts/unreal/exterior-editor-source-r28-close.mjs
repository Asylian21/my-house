// Only the independent actual R37b clone with the exact frozen R18 appended camera may dispatch.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadDirect,validateProjectClosure} from './exterior-editor-source-r28.mjs';
import {validateYardCameraViews,validateYardCameraContent} from './exterior-editor-source-r18.mjs';
export {validateProjectClosure,validateYardCameraViews,validateYardCameraContent};
const SOURCE_NAME='exterior-20261002-r37b',QA_NAME='exterior-20261002-r37b-yard-close-candidate-r28';
const REPORT='garden-yard-integration-native-report-r2.json',REPORT_SHA='f589c0d813ccfc35eba928a91a4545e03b159622fffa7ae2ba247545053c4532';
const AUDIT_SHA='5e2b2e057436049d4eabd34f3420d94b351c519094bfaed44cb10ddf24a56bf2';
const CAMERA_SCHEMA='brezi-saved-r37b-yard-camera-qa-clone-r28';
const CLONE_STATUS='verified-byte-identical-independent-apfs-saved-r37b-yard-qa-clone-before-viewpoint-stage-r28';
const STAGE_STATUS='verified-independent-saved-r37b-yard-camera-data-only-qa-clone-r28';
const SUPPLEMENT_SHA='768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1';
const VIEW='exterior-context-yard-572063-close-r18';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const R18_SHA='46035c3982ec8e977873c46c1ff8dfa5a69a10d1aaa2f0d1f216ce89bf87ed2f';
const DIRECT_SHA='71d2a5d20b60f2be5e600617c51c4c6a6e823f7437fcd64e8379c01295d29123',STAGER_SHA='4c1125a21ca9c459fa6a01db1fa5ebb55e252894c5611e225401b90442afb8ea',STAGE_SHA='354e7f5b8f24d1c1c0855119fcafc74a5ceeb3cb0ec750120a7ae9356c5e7e17';
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const sha=async p=>{const h=createHash('sha256');for await(const b of createReadStream(p))h.update(b);return h.digest('hex');};
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const same=(a,b)=>assert.deepEqual(a,b);

export function validateCameraStageHeader(s,{source,root,names}){
 assert.equal(source,path.join(root,'output/unreal',QA_NAME));assert.equal(s.schema,CAMERA_SCHEMA);assert.equal(s.schemaVersion,1);
 assert.equal(s.owner,'scripts/unreal/exterior-garden-yard-camera-stage-r28.py');assert.equal(s.status,STAGE_STATUS);
 assert.equal(s.sourceNativeOutput,path.join(root,'output/unreal',SOURCE_NAME));assert.equal(s.sourceNativeReport.sha256,REPORT_SHA);
 assert.equal(s.sourceNativeReport.path,path.join(s.sourceNativeOutput,REPORT));assert.equal(s.sourceNativeProcess.path,path.join(s.sourceNativeOutput,'garden-yard-integration-native-r2-process.json'));assert.equal(s.sourceCurrentByteAudit.path,path.join(s.sourceNativeOutput,'root-native-success-byte-audit-r37b-r2.json'));assert.equal(s.sourceCurrentByteAudit.sha256,AUDIT_SHA);
 assert.equal(s.project,path.join(source,'Project/BreziTwin'));assert.equal(s.cameraSupplement.sha256,SUPPLEMENT_SHA);assert.equal(s.viewId,VIEW);
 assert.equal(s.originalContentFileCount,4100);assert.equal(s.protectedFileCount,132);same(s.changedContentFiles,['Data/viewpoints.json']);
 for(const k of ['originalViewsPrefixPreserved','lightingUnchanged','nativeSourceUnchanged','allOriginalProjectFilesIndependentBeforeStage'])assert.equal(s[k],true);
 for(const k of ['sceneMapChanged','nativeExecuted','nativeCameraRuntimeVerified','nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted','shippingPackageProduced','currentVegetationVisibilityRecomputed'])assert.equal(s[k],false);
 assert.equal(s.sourceValidationExitCode,0);assert(!names.some(n=>/exterior-import-report|native-report|overlay-report/.test(n)),'Camera clone cannot carry copied native receipts');
 assert.equal(s.cameraAuditScope,'FROZEN_R18_SOURCE_CAMERA_REUSED_NOT_CURRENT_R37_VEGETATION_VISIBILITY');
}

function pinning(closure){
 const pinned=async row=>{assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);
  const st=await fs.lstat(row.path);assert(st.isFile()&&!st.isSymbolicLink());assert.equal(st.size,row.bytes);assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;};
 return {pinned,pj:async row=>read(await pinned(row))};
}
export async function loadEditorSourceEvidence(source,{root}={}){
 source=path.resolve(source);root=path.resolve(root);
 assert.equal(source,path.join(root,'output/unreal',QA_NAME),'Only the actual R37b exact staged QA clone is accepted');
 const names=await fs.readdir(source),receiptPath=path.join(source,'garden-yard-camera-stage-receipt-r28.json'),stage=await read(receiptPath);
 validateCameraStageHeader(stage,{source,root,names});assert(hashLike(STAGER_SHA)&&hashLike(DIRECT_SHA)&&hashLike(STAGE_SHA),'Final actual direct-reader/stager/receipt pins required');assert.equal(await sha(receiptPath),STAGE_SHA);
 const e=await loadDirect(stage.sourceNativeOutput,{root}),closure=new Set(e.additionalClosureFiles);const{pinned,pj}=pinning(closure);closure.add(receiptPath);
 const currentReader=fileURLToPath(import.meta.url),directReader=fileURLToPath(new URL('exterior-editor-source-r28.mjs',import.meta.url));closure.add(currentReader);assert.equal(stage.sourceReader.path,directReader);assert.equal(stage.sourceReader.sha256,DIRECT_SHA);await pinned(stage.sourceReader);
 assert.equal(stage.stagingHelper.path,path.join(root,'scripts/unreal/exterior-garden-yard-camera-stage-r28.py'));assert.equal(stage.stagingHelper.sha256,STAGER_SHA);await pinned(stage.stagingHelper);
 assert.equal(stage.historicalCameraReader.path,path.join(root,'scripts/unreal/exterior-editor-source-r18.mjs'));assert.equal(stage.historicalCameraReader.sha256,R18_SHA);await pinned(stage.historicalCameraReader);
 await pinned(stage.sourceNativeReport);await pinned(stage.sourceNativeProcess);assert.equal(stage.sourceCurrentByteAudit.sha256,AUDIT_SHA);await pinned(stage.sourceCurrentByteAudit);
 const supplement=await pj(stage.cameraSupplement);assert.equal(stage.cameraSupplement.path,path.join(root,'output/unreal/exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json'));
 for(const[file,h]of Object.entries(supplement.inputFiles)){const st=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:st.size});}
 const original=await pj(supplement.originalViewpoints),appended=await pj(supplement.appendedViewpoints);validateYardCameraViews(original,supplement,appended);same(stage.view,supplement.view);same(stage.historicalR18SourceCameraAudit,supplement.sourceCameraAudit);
 const project=path.join(source,'Project/BreziTwin');assert.equal(stage.viewpointFile.path,path.join(project,'Content/Data/viewpoints.json'));same(await pj(stage.viewpointFile),appended);
 same({sha256:stage.viewpointFile.sha256,bytes:stage.viewpointFile.bytes},{sha256:supplement.appendedViewpoints.sha256,bytes:supplement.appendedViewpoints.bytes});
 assert.equal(stage.afterContentInventory.path,path.join(source,'garden-yard-camera-content-after-r28.json'));const contentInventory=await pj(stage.afterContentInventory);validateYardCameraContent(e.contentInventory,contentInventory,supplement);
 const clone=await pj(stage.projectClone);assert.equal(stage.projectClone.path,path.join(source,'garden-yard-camera-project-clone-r28.json'));
 assert.equal(stage.projectClone.sha256,'f07a32ebb18ad367fb3d9c8de76dc1e72331b4bff3785b7ca7a28d6c0a2d2bd5');
 assert.equal(clone.schema,CAMERA_SCHEMA);assert.equal(clone.schemaVersion,1);assert.equal(clone.status,CLONE_STATUS);assert.equal(clone.project,project);assert.equal(clone.sourceProject,e.project);assert.equal(clone.fileCount,4232);assert.equal(clone.contentFiles,4100);assert.equal(clone.protectedFiles,132);
 for(const k of ['nativeExecuted'])assert.equal(clone[k],false);for(const k of ['viewpointStagingPending','fullSavedSourceReaderValidationPending'])assert.equal(clone[k],true);assert.equal(clone.cameraSupplement,null);
 for(const k of ['sourceNativeReport','sourceNativeProcess','sourceCurrentByteAudit'])same(clone[k],stage[k]);await pinned(clone.byteValidationHelper);await pinned(clone.rootController);
 const expectedFiles={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...e.projectProof},seen=new Set();assert.equal(clone.files.length,4232);
 for(const row of clone.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(expectedFiles,relative)&&!seen.has(relative));seen.add(relative);assert.equal(row.source,path.join(e.project,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);same({sha256:row.sha256,bytes:row.bytes},expectedFiles[relative]);const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);}assert.equal(seen.size,4232);
 assert.equal(stage.sourceValidation.path,path.join(source,'garden-yard-camera-source-validation-r28.json'));
 const validation=await pj(stage.sourceValidation);assert.equal(validation.scope,'CPU_SAVED_R37R2_NATIVE_RECEIPTS_AND_SOURCE_COUNTERFACTUAL');assert.equal(validation.sourceNativeOutput,stage.sourceNativeOutput);same(validation.summary,e.summary);same(validation.reader,stage.sourceReader);assert.equal(validation.nativeLaunchedByStaging,false);
 for(const[file,h]of Object.entries(validation.closureFiles)){const st=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:st.size});}
 for(const file of [...e.additionalClosureFiles,directReader,stage.stagingHelper.path,stage.projectClone.path,stage.historicalCameraReader.path,stage.cameraSupplement.path,supplement.originalViewpoints.path,supplement.appendedViewpoints.path,...Object.keys(supplement.inputFiles)])assert(Object.hasOwn(validation.closureFiles,file),'Stage missing actual saved source/camera closure');
 same(await pj(stage.protectedProjectProof),e.projectProof);
 const nativeModuleWitness={source:path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),destination:path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),sha256:MODULE_SHA,bytes:2818384,independentInodes:true};
 await pinned({path:nativeModuleWitness.destination,sha256:MODULE_SHA,bytes:2818384});
 const summary={...e.summary,mode:'saved-r37r2-exact-r18-yard-camera-qa-clone',supplementalViews:1,currentVegetationVisibilityRecomputed:false,nativeCameraRuntimeVerified:false};
 return{...e,mode:summary.mode,project,nativeReceiptPath:receiptPath,summary,contentInventory,additionalClosureFiles:[...closure],nativeModuleWitness,moduleWitnessSource:stage.projectClone,
 receiptSummary:{sourceNativeReport:stage.sourceNativeReport,sourceNativeProcess:stage.sourceNativeProcess,cameraStageReceipt:receiptPath,cameraSupplement:stage.cameraSupplement,sourceNativeEvidence:e.receiptSummary,summary}};
}
