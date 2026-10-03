// Closed actual R32 yard ground/detail overlay; source/native save is separate from appearance.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR21,validateProjectClosure} from './exterior-editor-source-r21.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-context-yard-ground-native-r32.py';
const HELPER_SHA='c30e4f323e6dad88f69c957112e528c8c326eb45fd3f970cc8388d33466d0537';
const SCHEMA='brezi-context-yard-resolved-ground-and-low-detail-native-r32';
const PLAN_SHA='03c6e1a5ba25966c3f314c44908fa73cdd32e0097d25ba516f75e537940841b3';
const SOURCE_SHA='8378d06f00e9a11dceff51e4eb12a270eff492d6f729f09d3dfd804de326f650';
const PREFLIGHT_SHA='af2eb7c935c6354b384a375ad3127939d34fa14145b4f9a8deebd5e044a21684';
const BASE_SHA='67f6b002cd4ad11e0c518815ebf0224e1bb1f932b94361ae91472137dedd776d';
const REPORT_SHA='99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19';
const R21_SHA='d11a0fe14db83a6e4919e4eac372be565cd59f8c254654f0230c3d34b32e270e';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const CHECKER_SHA='731b30a47943ec31d882d72ba07c29bf6580c2414f11b63b03a31869ce912277';
const ROOT_AUDIT_SHA='5be46410d8abed8630ab5a706fd447dc69b2f4568de6d270b18520fde8978906';
const PREFIX='Brezi/ContextYardGround20261002R32/';
const COUNTS={originalActors:5356,savedActors:5360,fullHismComponents:2321,fullHismInstances:678231,
 reboundGroundComponents:2,hiddenWornEdgeComponents:1,newFloorActors:1,newHismGroups:3,newRoots:1274,
 groundTriangles:32878,groundVertices:17095,newMeshAssets:3,newMaterialGraphs:2,newTextureObjects:0,newPipelineAssets:3,newPackages:8,
 scopedMaterialGraphs:63,scopedTextureObjects:95,contentFiles:4086,protectedFiles:132};
const read=async p=>JSON.parse(await fs.readFile(p,'utf8')),exec=promisify(execFile);
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};

export function validateYardGroundHeader(r,{source,project}){
 assert.equal(r.schema,SCHEMA);assert.equal(r.owner,OWNER);assert.equal(r.status,'verified-saved-resolved-context-yard-ground-and-low-detail');
 assert.equal(r.output,source);assert.equal(r.project,project);assert.equal(r.nativeProcessId,5443);assert.deepEqual(r.actualCounts,COUNTS);
 for(const[k,h]of Object.entries({selectedPlan:PLAN_SHA,sourceStudy:SOURCE_SHA,sourcePreflight:PREFLIGHT_SHA,baseNativeReport:BASE_SHA}))assert.equal(r[k].sha256,h);
 for(const k of ['nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged','originalSavedR30bUnchanged','existingRootsPreserved','originalBedsAnd13ShrubsPreserved','allGroundNativeOrderedF32PositionsUV0UV1WindingVerified'])assert.equal(r[k],true);
 for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified','materialPackagesIndependentlyUnloaded','nativeNormalTangentReadbackAvailable','measuredElevation','AdditionalRandomSeedsReadbackAvailable','existingMemberTransformOrSeedSetterUsed'])assert.equal(r[k],false);
 assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});assert.equal(r.newTextureObjects,0);
 assert.deepEqual(Object.keys(r.targets),['entry_walk','service_court','worn_edge']);assert.equal(new Set(Object.values(r.targets).map(v=>v.actor)).size,3);
 assert.deepEqual(Object.keys(r.addedActors),['yard_ground_r32_yard_substrate','EX_yard_ground_r32_grass_medium_02_a','EX_yard_ground_r32_grass_bermuda_clump_a','EX_yard_ground_r32_celandine_01_e']);assert.equal(new Set(Object.values(r.addedActors)).size,4);
 const s=r.savedReadback;assert.equal(s.fullActorCounterfactualValidated,true);assert.deepEqual(s.counts,COUNTS);assert.equal(s.nativeNormalTangentReadbackAvailable,false);assert.equal(s.nativeAppearanceAccepted,false);assert.equal(s.performanceAccepted,false);
 assert.equal(s.meshProofs.length,3);assert.deepEqual(s.meshProofs.map(v=>v.triangles),[1996,2523,28359]);
 for(const v of s.meshProofs){assert.equal(v.fullOrderedNativeGeometryVerified,true);assert.equal(v.nativeNormalTangentReadbackAvailable,false);assert(hashLike(v.nativeOrderedF32PositionUv0Uv1CornerSha256));}
 assert.equal(s.footprints.length,1274);assert.equal(new Set(s.footprints.map(v=>v.rootId)).size,1274);
 for(const v of s.footprints){assert.equal(v.allNativeLodVerticesAndContainingCircleInsideSourceMasks,true);assert.equal(v.originalShrubClearancePreserved,true);}
 const m=r.newMaterialReport;assert.equal(m.owner,'scripts/unreal/exterior-context-yard-ground-materials-r32.py');assert.equal(m.newMaterialGraphs,2);assert.equal(m.newTextureObjects,0);assert.equal(m.sharedTexturesUnchanged,true);
 assert.deepEqual(Object.keys(m.materials),['yard_gravel_r32','yard_substrate_r32']);assert.equal(m.newPackageAssets.length,2);
 for(const k of ['originalSourceTexturePixelsReimportedOrEdited','actualNativeTextureSourcePixelsDecoded','actualNativeTextureGpuPixelFormatVerified','nativeDitherCoveragePixelsMeasured','materialPackagesIndependentlyUnloaded','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified'])assert.equal(m[k],false);
}
export function validateYardGroundReportNames(names){
 const selected='context-yard-ground-native-report.json';assert(names.includes(selected));
 assert(!names.some(n=>n!==selected&&/(?:exterior-import|native-report|overlay-report).*\.json$/.test(n)),'R32 cannot inherit a failed, copied or unknown native report');
}
export function validateYardGroundContent(before,after,packages,delta){
 assert.equal(Object.keys(before).length,4078);assert.equal(Object.keys(after).length,4086);assert.equal(packages.length,8);assert.equal(new Set(packages).size,8);
 for(const p of packages)assert(p.startsWith(PREFIX)&&p.endsWith('.uasset')&&!Object.hasOwn(before,p));
 assert.deepEqual(Object.keys(after).sort(),[...Object.keys(before),...packages].sort());
 assert.deepEqual(Object.keys(before).filter(k=>JSON.stringify(before[k])!==JSON.stringify(after[k])),['Brezi/Maps/Brezi.umap']);
 assert.deepEqual(after['Data/viewpoints.json'],before['Data/viewpoints.json']);
 assert.deepEqual(delta,{changedOriginalFiles:['Brezi/Maps/Brezi.umap'],newOwnedPackages:[...packages].sort(),originalContentFiles:4078,savedContentFiles:4086,newPackages:8});
}
export async function loadEditorSourceEvidence(source,{root}={}){
 source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source),filename='context-yard-ground-native-report.json';
 const previous=fileURLToPath(new URL('exterior-editor-source-r21.mjs',import.meta.url));assert.equal(await sha(previous),R21_SHA);
 if(!names.includes(filename)){
  assert(!/^exterior-20261002-r32/.test(path.basename(source))&&!names.some(n=>/^context-yard-ground-native-report/.test(n)),'Running, failed or unknown R32 cannot delegate to an older receipt');
  const e=await loadR21(source,{root});e.additionalClosureFiles.push(previous);return e;
 }
 assert(hashLike(CHECKER_SHA)&&hashLike(ROOT_AUDIT_SHA),'Final actual checker/current-byte audit pins required');
 assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r32a'));validateYardGroundReportNames(names);
 const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,filename),r=await read(receiptPath),closure=new Set([receiptPath,previous]);validateYardGroundHeader(r,{source,project});assert.equal(await sha(receiptPath),REPORT_SHA);
 async function pinned(row){assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);const st=await fs.lstat(row.path);assert(st.isFile()&&!st.isSymbolicLink());assert.equal(st.size,row.bytes);assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;}
 const pj=async row=>read(await pinned(row));
 assert.equal(r.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261002-r30b/garden-composition-native-report-r3.json'));
 const e=await loadR21(path.dirname(r.baseNativeReport.path),{root});assert.equal(e.nativeReceiptPath,r.baseNativeReport.path);assert.equal(e.summary.savedActors,5356);for(const file of e.additionalClosureFiles)closure.add(file);const base=await pj(r.baseNativeReport);
 assert.equal(r.selectedPlan.path,path.join(root,'output/unreal/exterior-context-yard-ground-20261002-r32-native-study/yard-ground-native-plan.json'));const plan=await pj(r.selectedPlan);assert.deepEqual(plan.baseNativeReport,r.baseNativeReport);assert.deepEqual(plan.expectedCounts,COUNTS);assert.deepEqual(plan.targets,r.targets);assert.deepEqual(plan.sourceStudy,r.sourceStudy);await pinned(r.sourceStudy);
 assert.equal(r.sourcePreflight.path,path.join(root,'output/unreal/exterior-context-yard-ground-20261002-r32-native-study/source-preflight-r1/source-preflight.json'));const pf=await pj(r.sourcePreflight);
 assert.equal(pf.owner,OWNER);assert.equal(pf.status,'yard-ground-source-preflight-validated-native-pending');assert.equal(pf.nativeExecuted,false);assert.deepEqual(pf.selectedPlan,r.selectedPlan);assert.deepEqual(pf.baseNativeReport,r.baseNativeReport);assert.deepEqual(pf.projectClone,r.projectClone);assert.deepEqual(pf.inputFiles,r.inputFiles);assert.equal(Object.keys(r.inputFiles).length,528);assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);assert.equal(pf.testExitCode,0);await pinned(pf.testLog);await pinned(pf.testSource);
 assert.deepEqual(plan.baseNativeProcess,r.baseNativeProcess);for(const v of Object.values(r.baseNativeProcess))if(v&&typeof v==='object'&&Object.hasOwn(v,'path'))await pinned(v);
 for(const[file,h]of Object.entries(r.inputFiles)){const st=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:st.size});}
 for(const k of ['beforeActorWitness','expectedActorWitness','savedActorWitness','nativeSourceFrameMeasurements','originalControlsBefore','originalControlsSaved'])await pinned(r[k]);
 assert.deepEqual(await pj(r.beforeActorWitness),await pj(base.savedActorWitness));assert.deepEqual(await pj(r.originalControlsBefore),await pj(r.originalControlsSaved));
 const contentInventory=await pj(r.afterContentInventory),packages=r.newPackages.map(v=>{assert(v.startsWith('/Game/'));return v.split('.')[0].replace(/^\/Game\//,'')+'.uasset';});validateYardGroundContent(e.contentInventory,contentInventory,packages,r.assetDelta);
 assert.deepEqual(r.baseContentInventory,base.afterContentInventory);await pinned(r.baseContentInventory);assert.deepEqual(r.protectedProjectProof,base.protectedProjectProof);const projectProof=await pj(r.protectedProjectProof);assert.deepEqual(projectProof,e.projectProof);
 assert.equal(r.projectClone.path,path.join(source,'context-yard-ground-project-clone.json'));const clone=await pj(r.projectClone);assert.equal(clone.schema,SCHEMA);assert.equal(clone.status,'verified-original-r30b-independent-apfs-r32-clone-before-yard-ground-native');assert.equal(clone.project,project);assert.equal(clone.sourceProject,e.project);assert.equal(clone.fileCount,4210);assert.equal(clone.contentFiles,4078);assert.equal(clone.protectedFiles,132);assert.equal(clone.nativeExecuted,false);assert.equal(clone.selectedNativePlan,null);assert.deepEqual(clone.nativeBaseReport,r.baseNativeReport);assert.deepEqual(clone.selectedSourcePlan,r.sourceStudy);assert.deepEqual(plan.initialRootClone,r.projectClone);
 const originalFiles={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...projectProof},seen=new Set();assert.equal(clone.files.length,4210);
 for(const row of clone.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(originalFiles,relative)&&!seen.has(relative));seen.add(relative);assert.equal(row.source,path.join(e.project,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);assert.deepEqual({sha256:row.sha256,bytes:row.bytes},originalFiles[relative]);const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);}assert.equal(seen.size,4210);
 const views=await read(path.join(project,'Content/Data/viewpoints.json'));assert.deepEqual(views,await read(path.join(e.project,'Content/Data/viewpoints.json')));for(const id of ['exterior-garden','neighbor-finish-close-r18'])assert.equal(views.views.filter(v=>v.id===id).length,1);
 const checker=path.join(root,'scripts/unreal/exterior-context-yard-ground-editor-check-r22.py');assert.equal(await sha(checker),CHECKER_SHA);closure.add(checker);
 const native=JSON.parse((await exec('python3',['-B',checker,receiptPath],{timeout:240000,maxBuffer:1024*1024})).stdout);assert.equal(native.nativeProcessId,5443);
 const processPath=path.join(source,'context-yard-ground-native.log.json'),terminalPath=path.join(source,'context-yard-ground-native-process.json');const proc=await read(processPath),terminal=await read(terminalPath);assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,5443);assert.equal(terminal.reportSha256,REPORT_SHA);assert.equal(terminal.processFile,processPath);assert.equal(terminal.processFileSha256,await sha(processPath));assert.equal(terminal.logFile,path.join(source,'context-yard-ground-native.log'));assert.equal(terminal.logSha256,await sha(terminal.logFile));assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+terminal.logFile])assert(proc.args.includes(arg));assert.equal(terminal.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(terminal.sourcePinsBeforeNative).length,531);assert.equal(terminal.controllerSha256BeforeNative,terminal.controllerSha256AfterNative);assert.equal(await sha(terminal.controller),terminal.controllerSha256BeforeNative);
 for(const[file,h]of Object.entries(terminal.sourcePinsBeforeNative)){const st=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:st.size});}for(const f of [processPath,terminalPath,terminal.logFile,terminal.controller])closure.add(f);
 const auditPath=path.join(source,'root-native-byte-audit-r32a.json');assert.equal(await sha(auditPath),ROOT_AUDIT_SHA);closure.add(auditPath);const audit=await read(auditPath);
 assert.equal(audit.schema,'brezi-context-yard-ground-r32a-byte-audit-root-r1');assert.equal(audit.status,'actual-saved-r32a-current-byte-closure-validated');assert.equal(audit.nativeProcessId,5443);assert.equal(audit.nativeExitCode,0);
 assert.deepEqual(audit.nativeReport,{path:receiptPath,sha256:REPORT_SHA,bytes:(await fs.stat(receiptPath)).size});assert.equal(audit.currentContentFiles,4086);assert.equal(audit.currentProtectedFiles,132);assert.equal(audit.currentOwnProjectFiles,4218);assert.equal(audit.frozenSourcePinCount,531);assert.equal(audit.savedActorCount,5360);assert.equal(audit.savedHismComponents,2321);assert.equal(audit.savedHismInstances,678231);assert.deepEqual(audit.newOwnedPackages,[...packages].sort());assert.deepEqual(audit.originalCandidateChangedFiles,['Content/Brezi/Maps/Brezi.umap']);
 for(const key of ['all4210OriginalR30bParentFilesCurrentByteExact','allOriginalCandidateFilesExceptOwnMapByteExact','exact8NewOwnedPackages','savedRecordedActorWitnessMatchesDeclaredExpected','recordedOriginalControlsBeforeAndSavedExact','allFrozenPinsCurrentExact','nativeApplied'])assert.equal(audit[key],true);
 for(const key of ['freshNativeActorDecodePerformedByByteAudit','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified'])assert.equal(audit[key],false);
 for(const key of ['controller','terminalProcess','rawProcess','nativeLog','rootConfig','projectClone'])await pinned(audit[key]);assert.equal(audit.terminalProcess.path,terminalPath);assert.equal(audit.rawProcess.path,processPath);assert.deepEqual(audit.projectClone,r.projectClone);
 const w=r.nativeModuleWitness,module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');assert.equal(w.source,path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.destination,module);assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);for(const f of [module,w.source])await pinned({path:f,sha256:MODULE_SHA,bytes:w.bytes});
 const summary={...native,sourcePinsUnchangedAfterNative:531,scope:'R32 ground and1274 low roots REVIEW candidate on exact saved R30b; source/native saving is separate from appearance.'};
 return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:e.base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:w,moduleWitnessSource:r.projectClone,receiptSummary:{baseNativeReport:r.baseNativeReport,selectedPlan:r.selectedPlan,sourcePreflight:r.sourcePreflight,savedMapUnloadedReloaded:true,materialPackagesIndependentlyUnloaded:false,summary}};
}
