// Closed actual R35 R2 yard repair and its independently staged frozen-R18 camera clone.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {validateProjectClosure} from './exterior-editor-source-r3.mjs';
import {validateYardCameraViews,validateYardCameraContent} from './exterior-editor-source-r18.mjs';
export {validateProjectClosure,validateYardCameraViews,validateYardCameraContent};
export const SCHEMA='brezi-context-yard-scoped-repair-native-r35';
export const REPORT_SHA='22f38c206686040bb8027b2f5cd7abc479ff2749a5edd78cafabed8191ecc7ed';
export const PLAN_SHA='866871425239ab51a3cd73086f5627219286b323793eedbc8f1c3fac3815d3e6';
export const PF_SHA='279ddd587003c15f0860acecd58ff948cae9689739b53f246f0af9ed11f3afed';
export const OWNER='scripts/unreal/exterior-context-yard-repair-native-r35-r2.py';
export const CHECKER_SHA='e0a8bac16cc5a656b526b2dc4e8f84864ee656d6a9f7adf701b6fc6ad1d36f06';
export const AUDIT_SHA='9b3b6d39979065bf09634cefe2126e4d3d4b54aa33b09cdf5561af73d3d25943';
export const HELPER_SHA='b6727fbd255329c2b8e513df6f32c837fa37ef53e78f4aeb9ff048904ac7ad94';
export const REPAIR_SCHEMA='brezi-context-yard-native-source-bundle-route-repair-r35-r2';
export const CAMERA_SCHEMA='brezi-saved-r35r2-yard-camera-qa-clone-r26';
export const CLONE_STATUS='verified-byte-identical-independent-apfs-saved-r35r2-yard-qa-clone-before-viewpoint-stage-r26';
export const STAGE_STATUS='verified-independent-saved-r35r2-yard-camera-data-only-qa-clone-r26';
export const SUPPLEMENT_SHA='768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1';
export const VIEW='exterior-context-yard-572063-close-r18';
export const COUNTS={originalActors:5360,savedActors:5360,fullHismComponents:2321,fullHismInstances:678197,
 originalEcologyRootsRetired:34,affectedOriginalEcologyGroups:8,retainedAffectedOriginalEcologyRoots:1919,originalEcologyRootsRetained:24739,
 reboundHardGroundComponents:2,reboundBackdropMaterialComponents:1,newMeshAssets:2,newMaterialGraphs:1,newTextureObjects:0,newPipelineAssets:3,newPackages:6,
 uniqueHardMeshTriangles:4519,scopedMaterialGraphs:64,scopedTextureObjects:95,contentFiles:4092,protectedFiles:132};
const SOURCE_NAME='exterior-20261002-r35b',QA_NAME='exterior-20261002-r35b-yard-close-candidate-r26';
const REPORT='context-yard-repair-native-report-r2.json';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const BASE_SHA='99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19';
const SOURCE_SHA='1abfb6c418efa64de951b1e1da2862aaab0b2145342a21052a51c4627abd41e4';
const R3_SHA='1fcbd62598fe9f2bd66a64c2b86355fdfdee357d82dd28068d78786b25688c7b';
const R18_SHA='46035c3982ec8e977873c46c1ff8dfa5a69a10d1aaa2f0d1f216ce89bf87ed2f';
const STAGER_SHA='9b961f39f727139d559449ca3fbbce3bd14a7949b363f72aeec11d6bd7efab79';
const read=async p=>JSON.parse(await fs.readFile(p,'utf8')),exec=promisify(execFile);
const sha=async p=>{const h=createHash('sha256');for await(const b of createReadStream(p))h.update(b);return h.digest('hex');};
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const same=(a,b)=>assert.deepEqual(a,b);

export function validateRepairHeader(r,{source,project}){
 assert.equal(r.schema,SCHEMA);assert.equal(r.schemaVersion,1);assert.equal(r.owner,OWNER);assert.equal(r.repairSchema,REPAIR_SCHEMA);
 assert.equal(r.status,'verified-saved-scoped-hardcourt-ecology-coverage-near-pbr-repair');assert.equal(r.output,source);assert.equal(r.project,project);assert.equal(r.nativeProcessId,37031);
 same(r.actualCounts,COUNTS);same(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});same(r.setbacksMm,{street:3000,east:3000});
 for(const[k,h]of Object.entries({selectedPlan:PLAN_SHA,sourcePreflight:PF_SHA,sourceProposal:SOURCE_SHA,baseNativeReport:BASE_SHA}))assert.equal(r[k].sha256,h);
 for(const k of ['nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged','originalSavedR32Unchanged','existingUnrelatedRootsMatricesPoliciesUnchanged','allOriginal8949GrassAnd78TreesRawControlsExact','allOriginalGardenRawControlsExact'])assert.equal(r[k],true);
 for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified','nativeNormalTangentReadbackAvailable','materialPackagesIndependentlyUnloaded','AdditionalRandomSeedsReadbackAvailable','perInstanceShaderRandomValuePreservationClaimed','sourceGroundElevationSurveyed','tallGardenCompositionApplied'])assert.equal(r[k],false);
 assert.equal(r.repairA.retiredRoots,34);assert.equal(r.repairA.affectedGroups,8);assert.equal(r.repairA.retainedAffectedRoots,1919);
 assert.equal(r.repairA.actualRemoveReadback.length,8);assert.equal(Object.keys(r.repairA.nativeSelectedEcologyGeometry).length,8);
 assert.equal(r.repairB.uniqueHardMeshTriangles,4519);assert.equal(r.repairB.onlySourceHardUv1CoverageRChanged,true);
 assert.equal(r.repairB.allOriginalPositionNormalsIndexUv0Uv1GSourceBytesPreserved,true);assert.equal(r.repairB.sourceCoveragePixelsCausallyProven,false);
 assert.equal(r.repairC.materialReport.graph.nodes.length,58);assert.equal(r.repairC.materialReport.newTextureObjects,0);
 assert.equal(r.repairC.nearResponseCoefficientOriginal,.30);assert.equal(r.repairC.nearResponseCoefficientProposed,.65);
}
export function validateRepairReportNames(names){
 assert(names.includes(REPORT));assert(!names.some(n=>n!==REPORT&&/(?:exterior-import|native-report|overlay-report).*\.json$/.test(n)),
 'R35 R2 cannot inherit a failed R1, copied, ambiguous or unknown native report');
}
export function validateRepairContent(before,after,packages,delta){
 assert.equal(Object.keys(before).length,4086);assert.equal(Object.keys(after).length,4092);assert.equal(packages.length,6);assert.equal(new Set(packages).size,6);
 for(const p of packages)assert(p.startsWith('Brezi/ContextYardRepair20261002R35/')&&p.endsWith('.uasset')&&!Object.hasOwn(before,p));
 same(Object.keys(after).sort(),[...Object.keys(before),...packages].sort());
 same(Object.keys(before).filter(k=>JSON.stringify(before[k])!==JSON.stringify(after[k])),['Brezi/Maps/Brezi.umap']);
 same(after['Data/viewpoints.json'],before['Data/viewpoints.json']);
 same(delta,{changedOriginalFiles:['Brezi/Maps/Brezi.umap'],newOwnedPackages:[...packages].sort(),originalContentFiles:4086,savedContentFiles:4092,newPackages:6});
}
export function validateCameraStageHeader(s,{source,root,names}){
 assert.equal(source,path.join(root,'output/unreal',QA_NAME));assert.equal(s.schema,CAMERA_SCHEMA);assert.equal(s.schemaVersion,1);
 assert.equal(s.owner,'scripts/unreal/exterior-context-yard-repair-camera-stage-r26.py');assert.equal(s.status,STAGE_STATUS);
 assert.equal(s.sourceNativeOutput,path.join(root,'output/unreal',SOURCE_NAME));assert.equal(s.sourceNativeReport.sha256,REPORT_SHA);
 assert.equal(s.sourceNativeReport.path,path.join(s.sourceNativeOutput,REPORT));assert.equal(s.sourceNativeProcess.path,path.join(s.sourceNativeOutput,'context-yard-repair-native-r2-process.json'));
 assert.equal(s.project,path.join(source,'Project/BreziTwin'));assert.equal(s.cameraSupplement.sha256,SUPPLEMENT_SHA);assert.equal(s.viewId,VIEW);
 assert.equal(s.originalContentFileCount,4092);assert.equal(s.protectedFileCount,132);same(s.changedContentFiles,['Data/viewpoints.json']);
 for(const k of ['originalViewsPrefixPreserved','lightingUnchanged','nativeSourceUnchanged','allOriginalProjectFilesIndependentBeforeStage'])assert.equal(s[k],true);
 for(const k of ['sceneMapChanged','nativeExecuted','nativeCameraRuntimeVerified','nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted','shippingPackageProduced','currentVegetationVisibilityRecomputed'])assert.equal(s[k],false);
 assert.equal(s.sourceValidationExitCode,0);assert(!names.some(n=>/exterior-import-report|native-report|overlay-report/.test(n)),'Camera clone cannot carry copied native receipts');
 assert.equal(s.cameraAuditScope,'FROZEN_R18_SOURCE_CAMERA_REUSED_NOT_CURRENT_R35_VEGETATION_VISIBILITY');
}

function pinning(closure){
 const pinned=async row=>{assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);
  const st=await fs.lstat(row.path);assert(st.isFile()&&!st.isSymbolicLink());assert.equal(st.size,row.bytes);assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;};
 return {pinned,pj:async row=>read(await pinned(row))};
}
export async function loadSavedRepairSource(source,{root}={}){
 source=path.resolve(source);root=path.resolve(root);assert.equal(source,path.join(root,'output/unreal',SOURCE_NAME));
 const names=await fs.readdir(source);validateRepairReportNames(names);
 const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,REPORT),r=await read(receiptPath);
 assert.equal(await sha(receiptPath),REPORT_SHA);validateRepairHeader(r,{source,project});
 const closure=new Set([receiptPath]);const{pinned,pj}=pinning(closure);
 for(const[file,h]of [['exterior-editor-source-r3.mjs',R3_SHA],['exterior-editor-source-r18.mjs',R18_SHA]]){
  const p=fileURLToPath(new URL(file,import.meta.url));assert.equal(await sha(p),h);closure.add(p);
 }
 const plan=await pj(r.selectedPlan),pf=await pj(r.sourcePreflight),base=await pj(r.baseNativeReport);
 assert.equal(r.selectedPlan.path,path.join(root,'output/unreal/exterior-context-yard-20261002-r35-native-study-r2/yard-repair-native-plan.json'));
 assert.equal(r.sourcePreflight.path,path.join(path.dirname(r.selectedPlan.path),'source-preflight-r2/source-preflight.json'));
 assert.equal(plan.nativeOwner,OWNER);assert.equal(plan.repairSchema,REPAIR_SCHEMA);same(plan.expectedCounts,COUNTS);same(pf.expectedCounts,COUNTS);
 for(const k of ['selectedPlan','projectClone','baseNativeReport','moduleOrderWitness','inputFiles'])same(pf[k],r[k]);
 assert.equal(pf.owner,OWNER);assert.equal(pf.status,'scoped-yard-repair-source-preflight-validated-native-pending');assert.equal(pf.nativeExecuted,false);assert.equal(pf.tests.exitCode,0);
 await pinned(pf.tests.source);await pinned(pf.tests.log);assert.equal(Object.keys(r.inputFiles).length,595);assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);
 for(const[file,h]of Object.entries(r.inputFiles)){const st=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:st.size});}
 for(const k of ['sourceProposal','beforeActorWitness','expectedActorWitness','savedActorWitness','originalEcologyControls','retainedEcologyBeforeSave','retainedEcologySaved','nativeFreshnessSupport','originalControlsBefore','originalControlsSaved','baseContentInventory','protectedProjectProof'])await pinned(r[k]);
 same(await pj(r.beforeActorWitness),await pj(base.savedActorWitness));same(await pj(r.originalControlsBefore),await pj(r.originalControlsSaved));
 same(r.baseContentInventory,base.afterContentInventory);same(r.protectedProjectProof,base.protectedProjectProof);
 const contentInventory=await pj(r.afterContentInventory),baseContent=await pj(r.baseContentInventory),projectProof=await pj(r.protectedProjectProof);
 const packages=r.newPackages.map(v=>{assert(v.startsWith('/Game/'));return v.split('.')[0].replace(/^\/Game\//,'')+'.uasset';});
 validateRepairContent(baseContent,contentInventory,packages,r.assetDelta);assert.equal(Object.keys(projectProof).length,132);
 const clone=await pj(r.projectClone);assert.equal(r.projectClone.path,path.join(source,'context-yard-repair-project-clone.json'));
 assert.equal(clone.schema,SCHEMA);assert.equal(clone.status,'verified-original-r32a-independent-apfs-r35-clone-before-scoped-yard-repair');
 assert.equal(clone.project,project);assert.equal(clone.sourceProject,path.join(root,'output/unreal/exterior-20261002-r32a/Project/BreziTwin'));
 assert.equal(clone.fileCount,4218);assert.equal(clone.contentFiles,4086);assert.equal(clone.protectedFiles,132);assert.equal(clone.nativeExecuted,false);assert.equal(clone.selectedPlan,null);assert.equal(clone.sourcePreflight,null);assert.equal(clone.nativePreflightPending,true);
 same(clone.nativeBaseReport,r.baseNativeReport);same(clone.sourceProposal,r.sourceProposal);await pinned(clone.byteValidationHelper);await pinned(clone.rootController);
 const initialFiles={...Object.fromEntries(Object.entries(baseContent).map(([k,v])=>['Content/'+k,v])),...projectProof},seen=new Set();assert.equal(clone.files.length,4218);
 for(const row of clone.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(initialFiles,relative)&&!seen.has(relative));seen.add(relative);
  assert.equal(row.source,path.join(clone.sourceProject,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);
  same({sha256:row.sha256,bytes:row.bytes},initialFiles[relative]);const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);
  await pinned({path:row.source,sha256:row.sha256,bytes:row.bytes});
 }assert.equal(seen.size,4218);
 const rawPath=path.join(source,'context-yard-repair-native-r2.log.json'),terminalPath=path.join(source,'context-yard-repair-native-r2-process.json');
 const raw=await read(rawPath),terminal=await read(terminalPath);assert.equal(raw.code,0);assert.equal(raw.signal,null);assert.equal(raw.pid,37031);
 assert.equal(raw.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(raw.args[0],path.join(project,'BreziTwin.uproject'));
 for(const a of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+path.join(source,'context-yard-repair-native-r2.log')])assert(raw.args.includes(a));
 assert(Number.isFinite(Date.parse(raw.startedAt))&&Date.parse(raw.endedAt)>=Date.parse(raw.startedAt));assert.equal(terminal.reportSha256,REPORT_SHA);
 assert.equal(terminal.processFile,rawPath);assert.equal(terminal.processFileSha256,await sha(rawPath));assert.equal(terminal.logFile,path.join(source,'context-yard-repair-native-r2.log'));assert.equal(terminal.logSha256,await sha(terminal.logFile));
 assert.equal(terminal.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(terminal.sourcePinsBeforeNative).length,603);assert.equal(terminal.controllerSha256BeforeNative,terminal.controllerSha256AfterNative);assert.equal(await sha(terminal.controller),terminal.controllerSha256BeforeNative);
 for(const[file,h]of Object.entries(terminal.sourcePinsBeforeNative)){const st=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:st.size});}
 for(const p of [rawPath,terminalPath,terminal.logFile,terminal.controller])closure.add(p);
 const auditPath=path.join(source,'root-native-success-byte-audit-r35b-r1.json');assert.equal(await sha(auditPath),AUDIT_SHA);closure.add(auditPath);const audit=await read(auditPath);
 assert.equal(audit.schema,'brezi-root-r35b-native-success-current-byte-audit-r1');same(audit.report,r?{path:receiptPath,sha256:REPORT_SHA,bytes:(await fs.stat(receiptPath)).size}:null);
 same(audit.process,{path:terminalPath,sha256:await sha(terminalPath),bytes:(await fs.stat(terminalPath)).size});same(audit.clone,r.projectClone);
 assert.equal(audit.currentProjectFiles,4224);assert.equal(audit.currentContentFiles,4092);assert.equal(audit.protectedFiles,132);assert.equal(audit.sourcePinsBeforeAfterAndCurrentExact,603);
 for(const k of ['all4218OriginalR32SourceFilesExact','all4217OriginalOwnFilesExceptMapExact','onlyOriginalMapAndSixNewOwnedPackagesChanged','storedNativeFullCounterfactualEqual','storedOriginalRawControlsAnd1919AffectedSurvivorsBeforeAfterExact'])assert.equal(audit[k],true);
 assert.equal(audit.newNativeActorOrGeometryDecodeByThisCpuAudit,false);same(audit.actualStoredWitnessCounts,{actors:5360,hismComponents:2321,hismInstances:678197});
 same(audit.changedOriginalFiles,['Content/Brezi/Maps/Brezi.umap']);same(audit.newOwnedFiles,packages.map(v=>'Content/'+v).sort());await pinned(audit.byteHelper);await pinned(audit.rootAuditController);
 const checker=path.join(root,'scripts/unreal/exterior-context-yard-repair-editor-check-r26.py');assert.equal(await sha(checker),CHECKER_SHA);closure.add(checker);
 const checked=JSON.parse((await exec('python3',['-B',checker,receiptPath],{timeout:300000,maxBuffer:1024*1024})).stdout);
 assert.equal(checked.nativeProcessId,37031);assert.equal(checked.fullActorCounterfactualValidated,true);assert.equal(checked.nativeEcologyTriangles,5220);assert.equal(checked.hardUv1ROnlyTriangles,4519);
 const w=r.nativeModuleWitness;assert.equal(w.source,path.join(clone.sourceProject,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.destination,path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);
 await pinned({path:w.source,sha256:w.sha256,bytes:w.bytes});await pinned({path:w.destination,sha256:w.sha256,bytes:w.bytes});
 const summary={...checked,sourcePinsUnchangedAfterNative:603,scope:'Saved R35 R2 three scoped yard repairs; appearance remains a separate original-image review.'};
 return{mode:summary.mode,project,nativeReceiptPath:receiptPath,base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:w,moduleWitnessSource:r.projectClone,
  receiptSummary:{selectedPlan:r.selectedPlan,sourcePreflight:r.sourcePreflight,baseNativeReport:r.baseNativeReport,actualNativeProcess:terminalPath,currentByteAudit:{path:auditPath,sha256:AUDIT_SHA},summary}};
}

export async function loadEditorSourceEvidence(source,{root}={}){
 source=path.resolve(source);root=path.resolve(root);
 if(source===path.join(root,'output/unreal',SOURCE_NAME))return loadSavedRepairSource(source,{root});
 assert.equal(source,path.join(root,'output/unreal',QA_NAME),'Only actual saved R35R2 or its exact staged QA clone is accepted');
 const names=await fs.readdir(source),receiptPath=path.join(source,'context-yard-repair-camera-stage-receipt-r26.json'),stage=await read(receiptPath);
 validateCameraStageHeader(stage,{source,root,names});assert(hashLike(STAGER_SHA),'Final reviewed stager pin required');
 const e=await loadSavedRepairSource(stage.sourceNativeOutput,{root}),closure=new Set(e.additionalClosureFiles);const{pinned,pj}=pinning(closure);closure.add(receiptPath);
 const currentReader=fileURLToPath(import.meta.url);assert.equal(stage.sourceReader.path,currentReader);assert.equal(stage.sourceReader.sha256,await sha(currentReader));await pinned(stage.sourceReader);
 assert.equal(stage.stagingHelper.path,path.join(root,'scripts/unreal/exterior-context-yard-repair-camera-stage-r26.py'));assert.equal(stage.stagingHelper.sha256,STAGER_SHA);await pinned(stage.stagingHelper);
 assert.equal(stage.historicalCameraReader.path,path.join(root,'scripts/unreal/exterior-editor-source-r18.mjs'));assert.equal(stage.historicalCameraReader.sha256,R18_SHA);await pinned(stage.historicalCameraReader);
 await pinned(stage.sourceNativeReport);await pinned(stage.sourceNativeProcess);assert.equal(stage.sourceCurrentByteAudit.sha256,AUDIT_SHA);await pinned(stage.sourceCurrentByteAudit);
 const supplement=await pj(stage.cameraSupplement);assert.equal(stage.cameraSupplement.path,path.join(root,'output/unreal/exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json'));
 for(const[file,h]of Object.entries(supplement.inputFiles)){const st=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:st.size});}
 const original=await pj(supplement.originalViewpoints),appended=await pj(supplement.appendedViewpoints);validateYardCameraViews(original,supplement,appended);same(stage.view,supplement.view);same(stage.historicalR18SourceCameraAudit,supplement.sourceCameraAudit);
 const project=path.join(source,'Project/BreziTwin');assert.equal(stage.viewpointFile.path,path.join(project,'Content/Data/viewpoints.json'));same(await pj(stage.viewpointFile),appended);
 same({sha256:stage.viewpointFile.sha256,bytes:stage.viewpointFile.bytes},{sha256:supplement.appendedViewpoints.sha256,bytes:supplement.appendedViewpoints.bytes});
 assert.equal(stage.afterContentInventory.path,path.join(source,'context-yard-repair-camera-content-after-r26.json'));const contentInventory=await pj(stage.afterContentInventory);validateYardCameraContent(e.contentInventory,contentInventory,supplement);
 const clone=await pj(stage.projectClone);assert.equal(stage.projectClone.path,path.join(source,'context-yard-repair-camera-project-clone-r26.json'));
 assert.equal(stage.projectClone.sha256,'521542e3745bda5ec41457e8b8c46490b421dced393ea6d832e05495156218f1');
 assert.equal(clone.schema,CAMERA_SCHEMA);assert.equal(clone.status,CLONE_STATUS);assert.equal(clone.project,project);assert.equal(clone.sourceProject,e.project);assert.equal(clone.fileCount,4224);assert.equal(clone.contentFiles,4092);assert.equal(clone.protectedFiles,132);
 for(const k of ['nativeExecuted'])assert.equal(clone[k],false);for(const k of ['viewpointStagingPending','fullSavedSourceReaderValidationPending'])assert.equal(clone[k],true);assert.equal(clone.cameraSupplement,null);
 for(const k of ['sourceNativeReport','sourceNativeProcess','sourceCurrentByteAudit'])same(clone[k],stage[k]);await pinned(clone.byteValidationHelper);await pinned(clone.rootController);
 const expectedFiles={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...e.projectProof},seen=new Set();assert.equal(clone.files.length,4224);
 for(const row of clone.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(expectedFiles,relative)&&!seen.has(relative));seen.add(relative);assert.equal(row.source,path.join(e.project,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);same({sha256:row.sha256,bytes:row.bytes},expectedFiles[relative]);const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);}assert.equal(seen.size,4224);
 assert.equal(stage.sourceValidation.path,path.join(source,'context-yard-repair-camera-source-validation-r26.json'));
 const validation=await pj(stage.sourceValidation);assert.equal(validation.scope,'CPU_SAVED_R35R2_NATIVE_RECEIPTS_AND_SOURCE_COUNTERFACTUAL');assert.equal(validation.sourceNativeOutput,stage.sourceNativeOutput);same(validation.summary,e.summary);same(validation.reader,stage.sourceReader);assert.equal(validation.nativeLaunchedByStaging,false);
 for(const[file,h]of Object.entries(validation.closureFiles)){const st=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:st.size});}
 for(const file of [...e.additionalClosureFiles,currentReader,stage.stagingHelper.path,stage.projectClone.path,stage.historicalCameraReader.path,stage.cameraSupplement.path,supplement.originalViewpoints.path,supplement.appendedViewpoints.path,...Object.keys(supplement.inputFiles)])assert(Object.hasOwn(validation.closureFiles,file),'Stage missing actual saved source/camera closure');
 same(await pj(stage.protectedProjectProof),e.projectProof);
 const nativeModuleWitness={source:path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),destination:path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),sha256:MODULE_SHA,bytes:2818384,independentInodes:true};
 await pinned({path:nativeModuleWitness.destination,sha256:MODULE_SHA,bytes:2818384});
 const summary={...e.summary,mode:'saved-r35r2-exact-r18-yard-camera-qa-clone',supplementalViews:1,currentVegetationVisibilityRecomputed:false,nativeCameraRuntimeVerified:false};
 return{...e,mode:summary.mode,project,nativeReceiptPath:receiptPath,summary,contentInventory,additionalClosureFiles:[...closure],nativeModuleWitness,moduleWitnessSource:stage.projectClone,
 receiptSummary:{sourceNativeReport:stage.sourceNativeReport,sourceNativeProcess:stage.sourceNativeProcess,cameraStageReceipt:receiptPath,cameraSupplement:stage.cameraSupplement,sourceNativeEvidence:e.receiptSummary,summary}};
}
