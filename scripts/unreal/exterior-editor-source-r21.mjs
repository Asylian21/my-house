// Closed actual R30b/R3 garden replacement; source/native save is separate from appearance.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR19,validateProjectClosure} from './exterior-editor-source-r19.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-garden-composition-native-r30-r3.py';
const HELPER_SHA='bd2bc03f7e98811e53fc52729a178924e3d39bf124284c0287d9eb2fd57f24c6';
const SCHEMA='brezi-garden-composition-overlay-r30';
const PLAN_SHA='24587fc9d22d2e5d550f7a56b4fb144338918f4376f9db7b7016155d9d4bb90e';
const SOURCE_SHA='bd08b2c9bddc5e8ec4389df84afa841822993c0bf09f920663dce614654a7dd9';
const PREFLIGHT_SHA='ed34aba6b006b1978eec24ebe169a9e885d470969472ff4170b0597f2e587acc';
const BASE_SHA='a11b95edf10e79fed7d1ff5c43b350634f825aedbf0ab58e8ee22642e73679fd';
const REPORT_SHA='67f6b002cd4ad11e0c518815ebf0224e1bb1f932b94361ae91472137dedd776d';
const ROOT_AUDIT_SHA='fb3798681a7db54ea0c3ed74effaca1068a3bb486ea36c4736e6f88eff5ad7cb';
const R19_SHA='6ceda937eb4b9d2ebd2a5de17bcbbd58d692cf0bf142d55cc8c2db747810ade1';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const CHECKER_SHA='b3936c973ee289605c2e80c9066db22ad384e7afd394edfd5a882dbf569f5d89';
const PREFIX='Brezi/GardenComposition20261002R30/';
const MODELS=['fern_02_c','fern_02_a','fern_02_d','grass_medium_01_tall_a_LOD0','grass_medium_01_tall_c_LOD0'];
const COUNTS={originalActors:5351,savedActors:5356,fullHismComponents:2318,fullHismInstances:676957,
  originalGardenRoots:473,retainedOriginalGardenRoots:435,newOriginalShapeRoots:38,newMeshAssets:5,newMaterialGraphs:2,
  newTextureObjects:8,newPipelineAssets:3,newPackages:18,scopedMaterialGraphs:61,scopedTextureObjects:95,contentFiles:4078,protectedFiles:132};
const read=async p=>JSON.parse(await fs.readFile(p,'utf8')),exec=promisify(execFile);
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};

export function validateGardenCompositionHeader(r,{source,project}){
  assert.equal(r.schema,SCHEMA);assert.equal(r.schemaVersion,3);assert.equal(r.owner,OWNER);
  assert.equal(r.status,'verified-saved-38-original-shape-garden-composition');
  assert.equal(r.output,source);assert.equal(r.project,project);assert.equal(r.nativeProcessId,89358);
  for(const[k,h]of Object.entries({selectedPlan:PLAN_SHA,sourceProposal:SOURCE_SHA,sourcePreflight:PREFLIGHT_SHA,baseNativeReport:BASE_SHA}))assert.equal(r[k].sha256,h);
  for(const k of ['nativeApplied','savedMapUnloadedReloaded','originalSavedR29Unchanged','sourceInputsUnchanged',
    'originalGarden435RawMatricesOrderMainSeedCustomDataExact','original8949GrassRawControlsExact','allOriginal78TreeRawControlsExact',
    'allOriginalGroveActorsFullWitnessExact','sourceHeightRoleChanges36Explicit','twoTallHeroAuthoredSourceHeightRecipesPreserved'])assert.equal(r[k],true);
  for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','ecologicalFitVerified','shippingVerified','packageVerified',
    'surveyedPlacementVerified','nativeNormalTangentReadbackAvailable','meshMaterialPackagesIndependentlyUnloaded','AdditionalRandomSeedsReadbackAvailable',
    'retainedTransformRecompositionPerformed','seedMutationPerformed','perInstanceShaderRandomValuePreservationClaimed','sourceGroundElevationSurveyed'])assert.equal(r[k],false);
  assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});
  assert.deepEqual(r.actualCounts,COUNTS);assert.equal(r.uniqueSourceTriangles,4478);assert.equal(r.instancedSourceTriangles,46806);
  assert.deepEqual(Object.keys(r.newOwnedGroups),MODELS);assert.deepEqual(Object.keys(r.nativeGeometryReadback),MODELS);
  const ids=[];
  MODELS.forEach((model,i)=>{const row=r.newOwnedGroups[model],proof=r.nativeGeometryReadback[model];
    assert.equal(row.actor,'/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.BreziVegetationPatch_'+(2313+i));
    assert.equal(row.instances,i<3?12:1);assert.equal(row.rootIds.length,row.instances);ids.push(...row.rootIds);
    assert.equal(proof.asset,row.mesh);assert.equal(proof.lodCount,1);assert.equal(proof.triangles,[2248,784,816,290,340][i]);assert.equal(proof.sections,1);
    assert.equal(proof.fullOrderedNativeF32PositionUV0WindingVerified,true);assert(hashLike(proof.nativeCornerSha256));
    for(const k of ['originalProviderLodChainPresent','sourceTangentsPresent','nativeTangentGenerationNumericallyVerified','nativeNormalTangentReadbackAvailable','nativeNaniteRequested','meshPackageIndependentlyUnloaded'])assert.equal(proof[k],false);
    assert.equal(proof.sourceNormalBytesPreserved,true);assert.equal(proof.nativeTangentsRequestedFromOriginalUv,true);
  });
  assert.equal(ids.length,38);assert.equal(new Set(ids).size,38);
  assert.deepEqual(r.newOwnedGroups[MODELS[3]].rootIds,['garden_ornamental_6']);assert.deepEqual(r.newOwnedGroups[MODELS[4]].rootIds,['garden_ornamental_7']);
  assert.equal(r.originalPartialFilters.length,2);assert.equal(r.wholeOneMemberHeroRetirements.length,2);assert.equal(r.sourceCrownMaskProof.length,38);
}

export function validateGardenCompositionReportNames(names){
  const selected='garden-composition-native-report-r3.json';assert(names.includes(selected));
  assert(!names.some(n=>n!==selected&&/(?:exterior-import|native-report|overlay-report).*\.json$/.test(n)),
    'R30b cannot inherit an old, failed, donor or unknown native report');
}

export function validateGardenCompositionContent(before,after,packages,delta){
  assert.equal(Object.keys(before).length,4060);assert.equal(Object.keys(after).length,4078);assert.equal(packages.length,18);
  assert.equal(new Set(packages).size,18);for(const p of packages)assert(p.startsWith(PREFIX)&&p.endsWith('.uasset')&&!Object.hasOwn(before,p));
  assert.deepEqual(Object.keys(after).sort(),[...Object.keys(before),...packages].sort());
  assert.deepEqual(Object.keys(before).filter(k=>JSON.stringify(before[k])!==JSON.stringify(after[k])),['Brezi/Maps/Brezi.umap']);
  assert.deepEqual(after['Data/viewpoints.json'],before['Data/viewpoints.json']);
  assert.deepEqual(delta,{changedOriginalFiles:['Brezi/Maps/Brezi.umap'],newOwnedPackages:[...packages].sort(),originalContentFiles:4060,savedContentFiles:4078,newPackages:18});
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source),filename='garden-composition-native-report-r3.json';
  const previous=fileURLToPath(new URL('exterior-editor-source-r19.mjs',import.meta.url));assert.equal(await sha(previous),R19_SHA);
  if(!names.includes(filename)){
    assert(!/^exterior-20261002-r30/.test(path.basename(source))&&!names.some(n=>/^garden-composition-native-report/.test(n)),
      'Running, failed or unknown R30 cannot delegate to an older receipt');
    const e=await loadR19(source,{root});e.additionalClosureFiles.push(previous);return e;
  }
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r30b'));validateGardenCompositionReportNames(names);
  const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,filename),r=await read(receiptPath),closure=new Set([receiptPath,previous]);
  validateGardenCompositionHeader(r,{source,project});assert.equal(await sha(receiptPath),REPORT_SHA);
  async function pinned(row){
    assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);
    const s=await fs.lstat(row.path);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(s.size,row.bytes);assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;
  }
  const pj=async row=>read(await pinned(row));
  assert.equal(r.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261002-r29a/original-tree-group-native-report.json'));
  const e=await loadR19(path.dirname(r.baseNativeReport.path),{root});assert.equal(e.nativeReceiptPath,r.baseNativeReport.path);assert.equal(e.summary.savedActors,5351);
  for(const file of e.additionalClosureFiles)closure.add(file);const baseReport=await pj(r.baseNativeReport);
  assert.equal(r.selectedPlan.path,path.join(root,'output/unreal/exterior-garden-composition-20261002-r30-native-study-r3/garden-composition-native-plan-r3.json'));
  const plan=await pj(r.selectedPlan);assert.deepEqual(plan.baseNativeReport,r.baseNativeReport);assert.deepEqual(plan.expectedCounts,COUNTS);
  assert.equal(r.sourcePreflight.path,path.join(root,'output/unreal/exterior-garden-composition-20261002-r30-native-study-r3/source-preflight/source-preflight.json'));
  const preflight=await pj(r.sourcePreflight);assert.deepEqual(r.inputFiles,preflight.inputFiles);assert.equal(Object.keys(r.inputFiles).length,471);
  assert.equal(preflight.owner,OWNER);assert.equal(preflight.schemaVersion,3);assert.equal(preflight.status,'source-preflight-validated-38-garden-roots-native-pending');
  assert.equal(preflight.nativeExecuted,false);assert.deepEqual(preflight.selectedPlan,r.selectedPlan);assert.deepEqual(preflight.expectedCounts,COUNTS);
  assert.deepEqual(preflight.projectClone,plan.initialRootClone);assert.deepEqual(preflight.stepProjectionPolicy,r.stepProjectionPolicy);
  assert.equal(preflight.tests.exitCode,0);assert.equal(preflight.tests.testCount,20);await pinned(preflight.tests.log);
  assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);
  for(const key of ['sourceProposal','sourceDraft','baseCurrentByteAudit']){assert.deepEqual(r[key],plan[key]);await pinned(r[key]);}
  assert.deepEqual(r.baseNativeProcess,plan.baseNativeProcess);assert.equal(r.baseNativeProcess.pid,76135);
  for(const key of ['receipt','raw','log'])await pinned(r.baseNativeProcess[key]);
  for(const[file,h]of Object.entries(r.inputFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const key of ['beforeActorWitness','expectedActorWitness','savedActorWitness','originalGardenControls','retainedGardenControlsBeforeSave','retainedGardenControlsSaved',
    'newSourceNativeMeasurements','originalMaterialsBefore','originalMaterialsSaved','originalTreesBefore','originalTreesSaved','originalGrassBefore','originalGrassSaved'])await pinned(r[key]);
  assert.deepEqual(await pj(r.beforeActorWitness),await pj(baseReport.savedActorWitness));
  const contentInventory=await pj(r.afterContentInventory),packages=r.newPackages.map(p=>{assert(p.startsWith('/Game/')&&!p.includes('.'));return p.replace(/^\/Game\//,'')+'.uasset';});
  validateGardenCompositionContent(e.contentInventory,contentInventory,packages,r.assetDelta);
  assert.deepEqual(r.baseContentInventory,baseReport.afterContentInventory);await pinned(r.baseContentInventory);
  assert.deepEqual(r.protectedProjectProof,baseReport.protectedProjectProof);const projectProof=await pj(r.protectedProjectProof);assert.deepEqual(projectProof,e.projectProof);
  assert.equal(r.projectClone.path,path.join(source,'garden-composition-project-clone.json'));const clone=await pj(r.projectClone);
  assert.equal(clone.schema,SCHEMA);assert.equal(clone.status,'verified-original-r29a-independent-apfs-r30-clone-before-garden-native');
  assert.equal(clone.project,project);assert.equal(clone.sourceProject,e.project);assert.equal(clone.fileCount,4192);assert.equal(clone.contentFiles,4060);assert.equal(clone.protectedFiles,132);
  assert.equal(clone.nativeExecuted,false);assert.equal(clone.selectedPlan,null);assert.deepEqual(clone.nativeBaseReport,r.baseNativeReport);assert.deepEqual(clone.sourceProposal,r.sourceProposal);
  assert.deepEqual(plan.initialRootClone,r.projectClone);
  const originalFiles={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...projectProof},seen=new Set();assert.equal(clone.files.length,4192);
  // These rows witness the immutable initial clone, not the legitimately changed saved candidate map size.
  for(const row of clone.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(originalFiles,relative)&&!seen.has(relative));seen.add(relative);
    assert.equal(row.source,path.join(e.project,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);
    assert.deepEqual({sha256:row.sha256,bytes:row.bytes},originalFiles[relative]);const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);
    assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);}
  assert.equal(seen.size,4192);
  const views=await read(path.join(project,'Content/Data/viewpoints.json'));assert.deepEqual(views,await read(path.join(e.project,'Content/Data/viewpoints.json')));
  for(const id of ['exterior-garden','neighbor-finish-close-r18'])assert.equal(views.views.filter(v=>v.id===id).length,1);
  const checker=path.join(root,'scripts/unreal/exterior-garden-composition-editor-check-r21.py');assert.equal(await sha(checker),CHECKER_SHA);closure.add(checker);
  const native=JSON.parse((await exec('python3',['-B',checker,receiptPath],{timeout:180000,maxBuffer:1024*1024})).stdout);
  assert.equal(native.nativeProcessId,89358);assert.equal(native.savedActors,5356);assert.equal(native.retainedOriginalGardenRoots,435);assert.equal(native.newOriginalShapeRoots,38);
  assert.equal(native.fullNativeF32PositionUV0TopologyProofTriangles,4478);assert.equal(native.savedNewStoredMatricesIndependentlyDecodedByCpuChecker,false);
  const processPath=path.join(source,'garden-composition-native-r3.log.json'),terminalPath=path.join(source,'garden-composition-native-r3-process.json');
  const proc=await read(processPath),terminal=await read(terminalPath);assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,89358);
  assert.equal(terminal.reportSha256,REPORT_SHA);assert.equal(terminal.processFile,processPath);assert.equal(terminal.processFileSha256,await sha(processPath));
  assert.equal(terminal.logFile,path.join(source,'garden-composition-native-r3.log'));assert.equal(terminal.logSha256,await sha(terminal.logFile));
  assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));
  assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+terminal.logFile])assert(proc.args.includes(arg));
  assert.equal(terminal.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(terminal.sourcePinsBeforeNative).length,474);
  assert.equal(terminal.controllerSha256BeforeNative,terminal.controllerSha256AfterNative);assert.equal(await sha(terminal.controller),terminal.controllerSha256BeforeNative);
  for(const[file,h]of Object.entries(terminal.sourcePinsBeforeNative)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const file of [processPath,terminalPath,terminal.logFile,terminal.controller])closure.add(file);
  const rootAuditPath=path.join(source,'root-native-byte-audit-r30b.json');assert.equal(await sha(rootAuditPath),ROOT_AUDIT_SHA);closure.add(rootAuditPath);
  const audit=await read(rootAuditPath);assert.deepEqual(audit.nativeReport,{path:receiptPath,sha256:REPORT_SHA,bytes:(await fs.stat(receiptPath)).size});
  assert.equal(audit.currentContentFiles,4078);assert.equal(audit.currentProtectedFiles,132);assert.equal(audit.all4192OriginalR29ParentFilesCurrentByteExact,true);
  assert.equal(audit.exact18NewOwnedPackages,true);assert.equal(audit.fullCurrentActorWitnessMatchesSavedExpected,true);assert.equal(audit.allFrozenPinsCurrentExact,true);
  const w=r.nativeModuleWitness,module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');
  assert.equal(w.source,path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.destination,module);assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);
  for(const file of [module,w.source])await pinned({path:file,sha256:MODULE_SHA,bytes:w.bytes});
  const summary={...native,sourcePinsUnchangedAfterNative:474,scope:'38 original-shape garden replacements on exact saved R29;36 low-height role changes artistic. Matched appearance remains open.'};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:e.base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:w,moduleWitnessSource:r.projectClone,
    receiptSummary:{baseNativeReport:r.baseNativeReport,selectedPlan:r.selectedPlan,sourcePreflight:r.sourcePreflight,stepProjectionPolicy:r.stepProjectionPolicy,savedMapUnloadedReloaded:true,meshMaterialPackagesIndependentlyUnloaded:false,summary}};
}
