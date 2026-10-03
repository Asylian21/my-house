// Closed actual selected garden plus scoped saved-yard adapter. Native saving is separate from appearance.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR27,validateProjectClosure} from './exterior-editor-source-r27.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-garden-yard-integration-native-r37-r2.py';
const HELPER_SHA='d0651c69e2d1d70563eac5e35746a85c3c06839b1d5c19c846b3dead1a90e188';
const SCHEMA='brezi-r37-clean-selected-garden-plus-saved-yard';
const PLAN_SHA='e571d1eab5d9635aa5ac9a43e71d5cdd0795633121318c2fdc24e664066aa303';
const PREFLIGHT_SHA='85814b5295b6157c3c8a421eb27c54c2604ad3ed863aea070768a36b6d6f93e5';
const BASE_SHA='d2057c860c0b5135cd19beaee776145d89c3377a07ff08abee9537f6a15c765e';
const R27_SHA='38642dce3917a2b507fcaffca02fa2441508244006a73f657dcfb1141af192d0';
const REPORT_FILENAME='garden-yard-integration-native-report-r2.json';
const REPORT_SHA='f589c0d813ccfc35eba928a91a4545e03b159622fffa7ae2ba247545053c4532',ROOT_AUDIT_SHA='5e2b2e057436049d4eabd34f3420d94b351c519094bfaed44cb10ddf24a56bf2',CHECKER_SHA='f08df551b0cbaf82e66d06b29d54d0c55a78d7ab653a62365fe6c9b5345c5eae',NATIVE_PID=54956,TERMINAL_PIN_COUNT=854;
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const COUNTS={originalActors:5360,savedActors:5364,fullHismComponents:2325,fullHismInstances:678197,
  addedActors:4,addedHismGroups:3,newRoots:1274,retiredOriginalEcologyRoots:34,retainedAffectedEcologyRoots:1919,
  newCopiedPackages:14,newTextureObjects:0,scopedMaterialGraphs:64,scopedTextureObjects:96,contentFiles:4100,protectedFiles:132};
const read=async p=>JSON.parse(await fs.readFile(p,'utf8')),exec=promisify(execFile);
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};
const packagePath=asset=>{assert(/^\/Game\/[A-Za-z0-9_/-]+\.[A-Za-z0-9_-]+$/.test(asset));return asset.slice(6).split('.')[0]+'.uasset';};

export function validateGardenYardHeader(r,{source,project},{nativePid=NATIVE_PID}={}){
  assert.equal(r.schema,SCHEMA);assert.equal(r.schemaVersion,2);assert.equal(r.owner,OWNER);
  assert.equal(r.status,'verified-saved-clean-selected-garden-and-yard-integration');
  assert.equal(r.repairSchema,'brezi-r37-exact-material-snapshot-reader-dispatch-r2');
  assert.equal(r.priorFailedAttempt.actualPid,53262);assert.equal(r.priorFailedAttempt.actualExitCode,255);assert.equal(r.priorFailedAttempt.sourcePinCount,832);
  assert.equal(r.priorFailedAttempt.failingAssetActuallyRecorded,false);assert.equal(r.priorFailedAttempt.sceneOrAssetMutationOccurred,false);
  assert.deepEqual(Object.keys(r.materialReaderDispatch),['basic','neighbor','tree']);assert.deepEqual(Object.values(r.materialReaderDispatch).map(v=>v.length),[49,9,3]);
  assert.equal(new Set(Object.values(r.materialReaderDispatch).flat()).size,61);
  assert.equal(r.materialGraphDiagnosticFiles.before.length,61);assert.equal(r.materialGraphDiagnosticFiles.saved.length,61);
  assert.equal(r.output,source);assert.equal(r.project,project);assert(Number.isInteger(nativePid)&&nativePid>0);assert.equal(r.nativeProcessId,nativePid);
  for(const[k,h]of Object.entries({selectedPlan:PLAN_SHA,sourcePreflight:PREFLIGHT_SHA,baseNativeReport:BASE_SHA}))assert.equal(r[k].sha256,h);
  for(const k of ['nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged','originalSelectedGardenUnchanged',
    'all384Periwinkle36Ferns12Heroes41FlowersRawControlsExact','all78Trees8949GrassAnd13YardShrubsRawControlsExact',
    'all1274ConstructorInputRecoveredStoredMatricesBinary64Exact','all1919SurvivorRawMatricesOrderMainSeedCustomDataExact'])assert.equal(r[k],true);
  for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified',
    'wholeR35MapOrR30GardenImported','materialPackagesIndependentlyUnloaded','nativeNormalTangentReadbackAvailable',
    'AdditionalRandomSeedsReadbackAvailable','perInstanceShaderRandomValuePreservationClaimed','existingTransformOrSeedSetterUsed'])assert.equal(r[k],false);
  assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});assert.deepEqual(r.actualCounts,COUNTS);
  const mapping=r.newActorMapping;assert.equal(Object.keys(mapping).length,4);assert.equal(new Set(Object.values(mapping)).size,4);
  for(const p of Object.values(mapping))assert(p.startsWith('/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.'));
  const m=r.materialReadback;assert.equal(m.scopedMaterialGraphs,64);assert.equal(Object.keys(m.graphs).length,64);assert.equal(m.scopedTextureObjects,96);
  assert.equal(m.textureAssets.length,96);assert.equal(new Set(m.textureAssets).size,96);assert.equal(m.newTextureObjects,0);
  assert.equal(m.originalTexturePackageBytesProtected,true);assert.equal(m.sharedNewYardTextureSettingsVerified,true);
  assert.equal(m.all96NativeTextureSettingsRecomputed,false);assert.equal(m.materialPackagesIndependentlyUnloaded,false);
  for(const p of Object.values(m.graphs))assert(hashLike(p.graphSha256));
  const g=r.geometryReadback;assert.equal(Object.values(g.ground).reduce((n,p)=>n+p.triangles,0),32878);
  assert.equal(g.newLowRootFootprints.length,1274);assert.equal(g.all1274ContainingCirclesAndNativeThreeLodVerticesInsideSourceMasks,true);
  assert.equal(g.nativeNormalTangentReadbackAvailable,false);
  assert.equal(Object.keys(g.originalEcology).length,8);const lods=Object.values(g.originalEcology).flatMap(v=>{assert.equal(v.lods.length,3);assert.equal(v.nativeNormalTangentReadbackAvailable,false);return v.lods;});
  assert.equal(lods.length,24);assert.equal(lods.reduce((n,v)=>n+v.triangles,0),5220);
  for(const p of lods){assert.equal(p.fullNativeSourcePositionUvTopologyWindingVerified,true);assert(hashLike(p.nativeOrderedF32PositionUv0Uv1CornersSha256));assert.equal(p.sourcePrimitives.reduce((n,v)=>n+v.triangles,0),p.triangles);}
  assert.equal(r.newPackages.length,14);assert.equal(new Set(r.newPackages).size,14);
}

export function validateGardenYardReportNames(names){
  assert(names.includes(REPORT_FILENAME));
  assert(!names.some(n=>n!==REPORT_FILENAME&&/(?:exterior-import|native-report|overlay-report).*\.json$/.test(n)),
    'Combined candidate cannot inherit failed, foreign or legacy native reports');
}

export function validateGardenYardContent(before,after,copies,delta){
  assert.equal(Object.keys(before).length,4086);assert.equal(Object.keys(after).length,4100);assert.equal(copies.length,14);
  const packages=copies.map(v=>v.relativeContentPath);assert.equal(new Set(packages).size,14);
  for(const row of copies){const p=row.relativeContentPath;assert.equal(p,packagePath(row.asset));
    assert(/^Brezi\/(?:ContextYardGround20261002R32|ContextYardRepair20261002R35)\/.+\.uasset$/.test(p));assert(!Object.hasOwn(before,p));
    assert.deepEqual(after[p],{sha256:row.source.sha256,bytes:row.source.bytes});}
  assert.deepEqual(Object.keys(after).sort(),[...Object.keys(before),...packages].sort());
  assert.deepEqual(Object.keys(before).filter(k=>JSON.stringify(before[k])!==JSON.stringify(after[k])),['Brezi/Maps/Brezi.umap']);
  assert.deepEqual(after['Data/viewpoints.json'],before['Data/viewpoints.json']);
  assert.deepEqual(delta,{newPackages:14,newPackageBytes:1787793,onlyOriginalMapChanged:true});
}

export function validateGardenYardRootAudit(a,r,{reportPin,processPin,nativePid=NATIVE_PID,terminalPins=TERMINAL_PIN_COUNT}={}){
  assert.equal(a.schema,'brezi-root-r37b-native-success-current-byte-audit-r2');
  assert.deepEqual(a.report,reportPin);assert.deepEqual(a.process,processPin);assert.deepEqual(a.clone,r.projectClone);
  assert.equal(a.expectedRootObservedPid,nativePid);assert.equal(a.expectedRootObservedPins,terminalPins);
  assert.equal(a.currentProjectFiles,4232);assert.equal(a.currentContentFiles,4100);assert.equal(a.protectedFiles,132);
  for(const k of ['all4218SelectedR36SourceProjectFilesExact','all4231PreparedOwnFilesExceptMapExact',
    'allFourteenCopiedDonorPackagesIndependentAndByteExact','storedFullSceneCounterfactualEqual',
    'storedProtectedGardenTreeGrassShrubControlsExact','storedNew1274Binary64ConstructorAndRawControlsExact',
    'stored1919EcologySurvivorsRawOrderSeedCustomExact'])assert.equal(a[k],true);
  assert.equal(a.nativeCreatedAssetPackages,0);assert.deepEqual(a.changedPreparedFiles,['Content/Brezi/Maps/Brezi.umap']);
  assert.equal(a.sourcePinsBeforeAfterAndCurrentExact,terminalPins);assert.deepEqual(a.actualStoredWitnessCounts,{actors:5364,hismComponents:2325,hismInstances:678197});
  assert.equal(a.retiredWholeEcologyRoots,34);assert.equal(a.storedOrderedNativeGroundTriangles,32878);
  assert.equal(a.storedScopedMaterialGraphs,64);assert.equal(a.storedScopedTextureObjects,96);
  assert.deepEqual(a.exactReaderDispatch,r.materialReaderDispatch);
  assert.deepEqual(a.actualCompleteGraphDiagnosticPins,[...r.materialGraphDiagnosticFiles.before,...r.materialGraphDiagnosticFiles.saved]);
  for(const k of ['newNativeActorOrGeometryDecodeByThisCpuAudit','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified'])assert.equal(a[k],false);
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source);
  const previous=fileURLToPath(new URL('exterior-editor-source-r27.mjs',import.meta.url));assert.equal(await sha(previous),R27_SHA);
  if(!names.includes(REPORT_FILENAME)){
    assert(!/^exterior-20261002-r37/.test(path.basename(source))&&!names.some(n=>/^garden-yard-integration-native-report/.test(n)),
      'Pending, failed or unknown R37 cannot delegate to an older saved family');
    const e=await loadR27(source,{root});e.additionalClosureFiles.push(previous);return e;
  }
  assert(hashLike(REPORT_SHA)&&hashLike(ROOT_AUDIT_SHA)&&hashLike(CHECKER_SHA)&&Number.isInteger(NATIVE_PID)&&Number.isInteger(TERMINAL_PIN_COUNT),
    'Actual successful combined report/process/checker/current-byte closure is not available');
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r37b'));validateGardenYardReportNames(names);
  const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,REPORT_FILENAME),r=await read(receiptPath),closure=new Set([receiptPath,previous]);
  validateGardenYardHeader(r,{source,project});assert.equal(await sha(receiptPath),REPORT_SHA);
  async function pinned(row){assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);
    const s=await fs.lstat(row.path);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(s.size,row.bytes);assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;}
  const pj=async row=>read(await pinned(row));
  assert.equal(r.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261002-r36b/garden-periwinkle-native-report-r2.json'));
  const e=await loadR27(path.dirname(r.baseNativeReport.path),{root});assert.equal(e.nativeReceiptPath,r.baseNativeReport.path);assert.equal(e.summary.savedActors,5360);
  for(const file of e.additionalClosureFiles)closure.add(file);const baseReport=await pj(r.baseNativeReport);
  assert.equal(r.selectedPlan.path,path.join(root,'output/unreal/exterior-garden-yard-integration-20261002-r37-native-study-r2/garden-yard-integration-plan-r2.json'));
  const plan=await pj(r.selectedPlan);assert.equal(plan.schema,SCHEMA);assert.equal(plan.schemaVersion,2);assert.equal(plan.nativeOwner,OWNER);
  assert.deepEqual(r.repairSchema,plan.repairSchema);assert.deepEqual(r.priorFailedAttempt,plan.priorFailedAttempt);assert.deepEqual(r.materialReaderDispatch,plan.materialReaderDispatch);
  for(const row of Object.values(r.priorFailedAttempt.files))await pinned(row);
  assert.equal(plan.baseKey,'R36b');assert.deepEqual(plan.expectedCounts,COUNTS);assert.deepEqual(plan.baseNativeReport,r.baseNativeReport);
  const pf=await pj(r.sourcePreflight);assert.equal(pf.schema,SCHEMA);assert.equal(pf.owner,OWNER);
  assert.equal(pf.status,'selected-garden-yard-source-preflight-validated-native-pending');assert.deepEqual(pf.selectedPlan,r.selectedPlan);
  assert.deepEqual(pf.expectedCounts,COUNTS);assert.deepEqual(pf.inputFiles,r.inputFiles);assert.equal(Object.keys(r.inputFiles).length,850);
  assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);assert.deepEqual(pf.moduleOrderWitness,r.moduleOrderWitness);assert.equal(pf.nativeExecuted,false);assert.equal(pf.gpuExecuted,false);
  assert.deepEqual(pf.cpuTests,plan.cpuTests);assert.equal(pf.cpuTests.exitCode,0);assert.equal(pf.cpuTests.testCount,8);await pinned(pf.cpuTests.source);await pinned(pf.cpuTests.log);
  assert.deepEqual(r.baseNativeProcess,plan.baseNativeProcess);assert.equal(r.baseNativeProcess.pid,47851);for(const key of ['receipt','raw','log'])await pinned(r.baseNativeProcess[key]);
  for(const key of ['baseCurrentByteAudit','selectedRootReview','donorInventory']){assert.deepEqual(r[key],plan[key]);await pinned(r[key]);}
  for(const[file,h]of Object.entries(r.inputFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const key of ['beforeActorWitness','expectedActorWitness','savedActorWitness','protectedControlsBefore','protectedControlsSaved',
    'originalConstructorReplay','newGroupNativeControlsSaved','retainedEcologySaved','retirementSourceSupport'])await pinned(r[key]);
  assert.deepEqual(await pj(r.beforeActorWitness),await pj(baseReport.savedActorWitness));
  assert.deepEqual(await pj(r.protectedControlsBefore),await pj(r.protectedControlsSaved));
  assert.deepEqual(Object.keys(r.newActorMapping).sort(),Object.keys(plan.addedActorTemplates).sort());
  const selectedAssets=Object.values(plan.materialReaderDispatch).flat();
  for(const phase of ['before','saved']){
    const directory=path.join(source,'garden-yard-checkpoint','material-graphs-'+phase);assert.equal(r.materialGraphDiagnosticDirectories[phase],directory);
    const assets=[];for(const row of r.materialGraphDiagnosticFiles[phase]){assert.equal(path.dirname(row.path),directory);const d=await pj(row);
      assert.equal(d.schema,r.repairSchema);assert(selectedAssets.includes(d.asset));assert(plan.materialReaderDispatch[d.reader]?.includes(d.asset));assets.push(d.asset);
      assert.equal(d.nativeGraphAcceptanceGranted,false);assert.equal(d.actualCompleteGraphSha256,d.recordedExpectedGraphSha256);assert.equal(d.actualCompleteGraphSha256,r.materialReadback.graphs[d.asset].graphSha256);
      if(d.completeRecordedGraphShapeAvailable){assert.deepEqual(d.fullGraphDifferences,[]);assert.deepEqual(d.actualCompleteGraph,d.recordedExpectedCompleteGraph);}else{assert.equal(d.fullGraphDifferences,null);assert.equal(d.recordedExpectedCompleteGraph,null);}
      const wanted=d.asset===baseReport.materialReport.asset?r.baseNativeReport:baseReport.originalProtectedControlsSaved;assert.deepEqual(d.expectedPinnedSource,wanted);await pinned(d.expectedPinnedSource);
    }assert.deepEqual([...assets].sort(),[...selectedAssets].sort());
  }
  const contentInventory=await pj(r.afterContentInventory);assert.deepEqual(r.newPackages,plan.copiedPackageScope.map(v=>v.asset));
  validateGardenYardContent(e.contentInventory,contentInventory,plan.copiedPackageScope,r.assetDelta);
  assert.deepEqual(r.baseContentInventory,baseReport.afterContentInventory);await pinned(r.baseContentInventory);
  assert.deepEqual(r.protectedProjectProof,baseReport.protectedProjectProof);const projectProof=await pj(r.protectedProjectProof);assert.deepEqual(projectProof,e.projectProof);
  assert.equal(r.projectClone.path,path.join(source,'garden-yard-project-clone.json'));assert.deepEqual(r.projectClone,plan.projectClone);assert.deepEqual(r.projectClone,pf.projectClone);
  const clone=await pj(r.projectClone);assert.equal(clone.schema,'brezi-garden-yard-clean-integration-project-clone-r37');assert.equal(clone.schemaVersion,1);
  assert.equal(clone.status,'verified-selected-r36b-independent-apfs-clone-plus-fourteen-exact-yard-donor-packages');assert.deepEqual(clone.nativeBaseReport,r.baseNativeReport);
  assert.equal(clone.project,project);assert.equal(clone.sourceProject,e.project);assert.equal(clone.fileCount,4218);assert.equal(clone.preparedProjectFiles,4232);
  assert.equal(clone.contentFiles,4086);assert.equal(clone.protectedFiles,132);assert.equal(clone.preparedContentFiles,4100);assert.equal(clone.donorPackageCount,14);
  assert.equal(clone.nativeExecuted,false);assert.equal(clone.nativePreflightPending,true);
  for(const key of ['selectedPlan','sourceProposal','sourcePreflight'])assert.equal(clone[key],null);
  assert.deepEqual(clone.rootBaseSelection,r.selectedRootReview);assert.deepEqual(clone.baseCurrentByteAudit,r.baseCurrentByteAudit);assert.deepEqual(clone.donorInventory,r.donorInventory);
  const originalFiles={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...projectProof},seen=new Set();assert.equal(clone.files.length,4218);
  for(const row of clone.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(originalFiles,relative)&&!seen.has(relative));seen.add(relative);
    assert.equal(row.source,path.join(e.project,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);
    assert.deepEqual({sha256:row.sha256,bytes:row.bytes},originalFiles[relative]);
    const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);}
  assert.deepEqual([...seen].sort(),Object.keys(originalFiles).sort());
  // Stored initial clone rows describe the original map; current saved map size may legitimately differ.
  const copyExpected=plan.copiedPackageScope.map(v=>({source:v.source.path,destination:path.join(project,'Content',v.relativeContentPath),
    sha256:v.source.sha256,bytes:v.source.bytes,independentInodes:true,relativeContentPath:v.relativeContentPath,donorReport:v.donorReport,asset:v.asset}));
  assert.deepEqual(clone.copiedDonorPackages,copyExpected);
  for(const row of copyExpected){const[s,d]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(d.isFile()&&!d.isSymbolicLink());
    assert.equal(s.size,row.bytes);assert.equal(d.size,row.bytes);assert(s.dev!==d.dev||s.ino!==d.ino);await pinned({path:row.source,sha256:row.sha256,bytes:row.bytes});await pinned({path:row.destination,sha256:row.sha256,bytes:row.bytes});}
  await pinned(clone.preparedContentInventory);await pinned(clone.byteValidationHelper);await pinned(clone.rootController);
  const views=await read(path.join(project,'Content/Data/viewpoints.json'));assert.deepEqual(views,await read(path.join(e.project,'Content/Data/viewpoints.json')));
  for(const view of ['exterior-garden','neighbor-finish-close-r18','exterior-neighborhood'])assert.equal(views.views.filter(v=>v.id===view).length,1);
  const checker=path.join(root,'scripts/unreal/exterior-garden-yard-editor-check-r28.py');assert.equal(await sha(checker),CHECKER_SHA);closure.add(checker);
  const native=JSON.parse((await exec('python3',['-B',checker,receiptPath],{timeout:240000,maxBuffer:1024*1024})).stdout);
  assert.equal(native.nativeProcessId,NATIVE_PID);assert.equal(native.savedActors,5364);assert.equal(native.fullHismInstances,678197);
  assert.equal(native.freshNativeActorOrGeometryDecodePerformedByCpuChecker,false);
  assert.equal(native.wholeActorCounterfactualValidated,true);assert.equal(native.fullHismComponents,2325);
  const processPath=path.join(source,'garden-yard-integration-native-r2.log.json'),terminalPath=path.join(source,'garden-yard-integration-native-r2-process.json');
  const proc=await read(processPath),terminal=await read(terminalPath);assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,NATIVE_PID);
  assert.equal(terminal.reportSha256,REPORT_SHA);assert.equal(terminal.processFile,processPath);assert.equal(terminal.processFileSha256,await sha(processPath));
  assert.equal(terminal.logFile,path.join(source,'garden-yard-integration-native-r2.log'));assert.equal(terminal.logSha256,await sha(terminal.logFile));
  assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));
  assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+terminal.logFile])assert(proc.args.includes(arg));
  assert.equal(terminal.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(terminal.sourcePinsBeforeNative).length,TERMINAL_PIN_COUNT);
  for(const [file,h]of Object.entries(r.inputFiles))assert.equal(terminal.sourcePinsBeforeNative[file],h);
  assert.equal(terminal.controllerSha256BeforeNative,terminal.controllerSha256AfterNative);assert.equal(await sha(terminal.controller),terminal.controllerSha256BeforeNative);
  for(const[file,h]of Object.entries(terminal.sourcePinsBeforeNative)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const file of [processPath,terminalPath,terminal.logFile,terminal.controller])closure.add(file);
  const rootAuditPath=path.join(source,'root-native-success-byte-audit-r37b-r2.json');assert.equal(await sha(rootAuditPath),ROOT_AUDIT_SHA);closure.add(rootAuditPath);
  const audit=await read(rootAuditPath),reportPin={path:receiptPath,sha256:REPORT_SHA,bytes:(await fs.stat(receiptPath)).size},processPin={path:terminalPath,sha256:await sha(terminalPath),bytes:(await fs.stat(terminalPath)).size};
  validateGardenYardRootAudit(audit,r,{reportPin,processPin});for(const key of ['byteHelper','rootAuditController'])await pinned(audit[key]);
  const w=r.nativeModuleWitness,module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');
  assert.equal(w.source,path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.destination,module);
  assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);
  for(const file of [module,w.source])await pinned({path:file,sha256:MODULE_SHA,bytes:w.bytes});
  const summary={...native,sourcePinsUnchangedAfterNative:TERMINAL_PIN_COUNT,scope:'Selected R36 garden retained exactly; four scoped yard actors and fourteen saved packages combined with34 ecology retirements. Saved native source checks remain separate from matched appearance.'};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:e.base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:w,moduleWitnessSource:r.projectClone,
    receiptSummary:{baseNativeReport:r.baseNativeReport,selectedPlan:r.selectedPlan,sourcePreflight:r.sourcePreflight,wholeSelectedGardenPreserved:true,savedMapUnloadedReloaded:true,meshMaterialPackagesIndependentlyUnloaded:false,summary}};
}
