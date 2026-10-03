// Closed actual R34 fern-only source; all twelve ornamentals and41 flowers remain original.
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
const OWNER='scripts/unreal/exterior-garden-fern-only-native-r34.py';
const HELPER_SHA='667893df1a1fe8d3b8b78a713af5f35cb0afee66346c79b34a15176d3ead0ee5';
const SCHEMA='brezi-garden-fern-only-native-r34';
const PLAN_SHA='bc8227ee4c84be48b4859fb9b5ad47f8df390c889e0aa07933dd8df784c15b31';
const SOURCE_SHA='93839661f6b28054521ddf550388b8f2e5daa380fe93406e0c399a6ec807ceb2';
const PREFLIGHT_SHA='c576a977777ef33af745840dbdf734d34168816683c0ed199c9d7c9a920366f2';
const BASE_SHA='a11b95edf10e79fed7d1ff5c43b350634f825aedbf0ab58e8ee22642e73679fd';
const REPORT_SHA='d233329bee2ffcb95419c8266ff8c1f50931ba8f642ded23ab20330f1d334cb8';
const ROOT_AUDIT_SHA='c75becbc961f81dc5e0499399c0890eec50baecfabd3a514b5232abd1d7bca1e';
const R21_SHA='d11a0fe14db83a6e4919e4eac372be565cd59f8c254654f0230c3d34b32e270e';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const CHECKER_SHA='5bd91e61ae0cb4f3d437ad359bfddad42b4337cc21e131198f5f825b1e00571b';
const PREFIX='Brezi/GardenFernOnly20261002R34/';
const MODELS=['fern_02_a','fern_02_c','fern_02_d'];
const COUNTS={originalActors:5351,savedActors:5354,fullHismComponents:2316,fullHismInstances:676957,
  originalGardenRoots:473,retainedOriginalGardenRoots:437,newOriginalFernRoots:36,newMeshAssets:3,newMaterialGraphs:1,
  newTextureObjects:4,newPipelineAssets:3,newPackages:11,scopedMaterialGraphs:60,scopedTextureObjects:91,contentFiles:4071,protectedFiles:132};
const read=async p=>JSON.parse(await fs.readFile(p,'utf8')),exec=promisify(execFile);
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};

export function validateFernOnlyHeader(r,{source,project}){
  assert.equal(r.schema,SCHEMA);assert.equal(r.schemaVersion,1);assert.equal(r.owner,OWNER);
  assert.equal(r.status,'verified-saved-36-original-fern-garden-all-ornamentals-retained');
  assert.equal(r.output,source);assert.equal(r.project,project);assert.equal(r.nativeProcessId,21209);
  for(const[k,h]of Object.entries({selectedPlan:PLAN_SHA,sourceProposal:SOURCE_SHA,sourcePreflight:PREFLIGHT_SHA,baseNativeReport:BASE_SHA}))assert.equal(r[k].sha256,h);
  for(const k of ['nativeApplied','savedMapUnloadedReloaded','originalSavedR29Unchanged','sourceInputsUnchanged',
    'originalGarden437RawMatricesOrderMainSeedCustomDataExact','original8949GrassRawControlsExact','allOriginal78TreeRawControlsExact',
    'allOriginalGroveActorsFullWitnessExact','sourceHeightRoleChanges36Explicit','allOriginal12OrnamentalActorsAndMembersUnchanged','allOriginal41FlowersUnchanged','remaining384OriginalLowStarsUnchanged'])assert.equal(r[k],true);
  for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','ecologicalFitVerified','shippingVerified','packageVerified',
    'surveyedPlacementVerified','nativeNormalTangentReadbackAvailable','meshMaterialPackagesIndependentlyUnloaded','AdditionalRandomSeedsReadbackAvailable',
    'retainedTransformRecompositionPerformed','seedMutationPerformed','perInstanceShaderRandomValuePreservationClaimed','sourceGroundElevationSurveyed'])assert.equal(r[k],false);
  assert.equal(r.yardIntegrationApplied,false);assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});
  assert.deepEqual(r.actualCounts,COUNTS);assert.equal(r.uniqueSourceTriangles,3848);assert.equal(r.instancedSourceTriangles,46176);
  assert.deepEqual(Object.keys(r.newOwnedGroups),MODELS);assert.deepEqual(Object.keys(r.nativeGeometryReadback),MODELS);
  const ids=[];
  MODELS.forEach((model,i)=>{const row=r.newOwnedGroups[model],proof=r.nativeGeometryReadback[model];
    assert.equal(row.actor,'/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.BreziVegetationPatch_'+(2313+i));
    assert.equal(row.instances,12);assert.equal(row.rootIds.length,row.instances);ids.push(...row.rootIds);
    assert.equal(proof.asset,row.mesh);assert.equal(proof.lodCount,1);assert.equal(proof.triangles,[784,2248,816][i]);assert.equal(proof.sections,1);
    assert.equal(proof.fullOrderedNativeF32PositionUV0WindingVerified,true);assert(hashLike(proof.nativeCornerSha256));
    for(const k of ['originalProviderLodChainPresent','sourceTangentsPresent','nativeTangentGenerationNumericallyVerified','nativeNormalTangentReadbackAvailable','nativeNaniteRequested','meshPackageIndependentlyUnloaded'])assert.equal(proof[k],false);
    assert.equal(proof.sourceNormalBytesPreserved,true);assert.equal(proof.nativeTangentsRequestedFromOriginalUv,true);
  });
  assert.equal(ids.length,36);assert.equal(new Set(ids).size,36);
  assert(!ids.some(id=>id.startsWith('garden_ornamental_')),'All original ornamental roots must remain unchanged');
  assert.equal(r.originalPartialFilters.length,2);assert.equal(r.wholeOneMemberHeroRetirements.length,0);assert.equal(r.sourceCrownMaskProof.length,36);
  const material=r.materialReport;assert.equal(material.schema,'brezi-garden-fern-only-original-material-r34');assert.equal(material.owner,'scripts/unreal/exterior-garden-fern-only-materials-r34.py');assert.equal(material.materialCount,1);assert.equal(material.textureObjectCount,4);assert.equal(material.newPackageAssets.length,5);assert.equal(new Set(material.newPackageAssets).size,5);assert.equal(material.sourceAlphaBits,16);assert.equal(material.originalProviderAlphaMode,'MASK');assert.equal(material.sourceRecipe.sha256,'4f4de9417d0a3a3f5f6f2ef5f0fda70c8c9af88e7892da1d5f4ab3583a6d5cb6');
  assert(material.newPackageAssets.every(asset=>asset.startsWith('/Game/'+PREFIX+'Fern/')));for(const k of ['sourcePixelsEdited','nativeImportedPixelsDecoded','nativeSourcePixelFormatReadbackAvailable','nativeGpuPixelFormatReadbackAvailable','nativeAppearanceAccepted','fullPhotorealismAccepted'])assert.equal(material[k],false);
}

export function validateFernOnlyReportNames(names){
  const selected='garden-fern-only-native-report.json';assert(names.includes(selected));
  assert(!names.some(n=>n!==selected&&/(?:exterior-import|native-report|overlay-report).*\.json$/.test(n)),
    'R34a cannot inherit an old, failed, donor or unknown native report');
}

export function validateFernOnlyContent(before,after,packages,delta){
  assert.equal(Object.keys(before).length,4060);assert.equal(Object.keys(after).length,4071);assert.equal(packages.length,11);
  assert.equal(new Set(packages).size,11);for(const p of packages)assert(p.startsWith(PREFIX)&&p.endsWith('.uasset')&&!Object.hasOwn(before,p));
  assert.deepEqual(Object.keys(after).sort(),[...Object.keys(before),...packages].sort());
  assert.deepEqual(Object.keys(before).filter(k=>JSON.stringify(before[k])!==JSON.stringify(after[k])),['Brezi/Maps/Brezi.umap']);
  assert.deepEqual(after['Data/viewpoints.json'],before['Data/viewpoints.json']);
  assert.deepEqual(delta,{changedOriginalFiles:['Brezi/Maps/Brezi.umap'],newOwnedPackages:[...packages].sort(),originalContentFiles:4060,savedContentFiles:4071,newPackages:11});
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source),filename='garden-fern-only-native-report.json';
  const previous=fileURLToPath(new URL('exterior-editor-source-r21.mjs',import.meta.url));assert.equal(await sha(previous),R21_SHA);
  if(!names.includes(filename)){
    assert(!/^exterior-20261002-r34/.test(path.basename(source))&&!names.some(n=>/^garden-fern-only-native-report/.test(n)),
      'Running, failed or unknown R34 cannot delegate to an older receipt');
    const e=await loadR21(source,{root});e.additionalClosureFiles.push(previous);return e;
  }
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r34a'));validateFernOnlyReportNames(names);
  const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,filename),r=await read(receiptPath),closure=new Set([receiptPath,previous]);
  validateFernOnlyHeader(r,{source,project});assert.equal(await sha(receiptPath),REPORT_SHA);
  async function pinned(row){
    assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);
    const s=await fs.lstat(row.path);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(s.size,row.bytes);assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;
  }
  const pj=async row=>read(await pinned(row));
  assert.equal(r.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261002-r29a/original-tree-group-native-report.json'));
  const e=await loadR21(path.dirname(r.baseNativeReport.path),{root});assert.equal(e.nativeReceiptPath,r.baseNativeReport.path);assert.equal(e.summary.savedActors,5351);
  for(const file of e.additionalClosureFiles)closure.add(file);const baseReport=await pj(r.baseNativeReport);
  assert.equal(r.selectedPlan.path,path.join(root,'output/unreal/exterior-garden-fern-only-20261002-r34-native-study/fern-only-native-plan.json'));
  const plan=await pj(r.selectedPlan);assert.deepEqual(plan.baseNativeReport,r.baseNativeReport);assert.deepEqual(plan.expectedCounts,COUNTS);
  assert.equal(r.sourcePreflight.path,path.join(root,'output/unreal/exterior-garden-fern-only-20261002-r34-native-study/source-preflight/source-preflight.json'));
  const preflight=await pj(r.sourcePreflight);assert.deepEqual(r.inputFiles,preflight.inputFiles);assert.equal(Object.keys(r.inputFiles).length,453);
  assert.equal(preflight.owner,OWNER);assert.equal(preflight.schemaVersion,1);assert.equal(preflight.status,'source-preflight-validated-36-ferns-original-ornamentals-retained-native-pending');
  assert.equal(preflight.nativeExecuted,false);assert.deepEqual(preflight.selectedPlan,r.selectedPlan);assert.deepEqual(preflight.expectedCounts,COUNTS);
  assert.deepEqual(preflight.projectClone,plan.projectClone);assert.deepEqual(preflight.stepProjectionPolicy,r.stepProjectionPolicy);
  assert.equal(preflight.tests.exitCode,0);assert.equal(preflight.tests.testCount,10);await pinned(preflight.tests.log);
  assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);
  for(const key of ['sourceProposal','baseCurrentByteAudit']){assert.deepEqual(r[key],plan[key]);await pinned(r[key]);}
  const sourceProposal=await pj(r.sourceProposal);assert.deepEqual(r.sourceGeometryDescriptor,sourceProposal.geometryDescriptor);await pinned(r.sourceGeometryDescriptor);
  assert.deepEqual(r.baseNativeProcess,plan.baseNativeProcess);assert.equal(r.baseNativeProcess.pid,76135);
  for(const key of ['receipt','raw','log'])await pinned(r.baseNativeProcess[key]);
  for(const[file,h]of Object.entries(r.inputFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const key of ['beforeActorWitness','expectedActorWitness','savedActorWitness','originalGardenControls','retainedGardenControlsBeforeSave','retainedGardenControlsSaved',
    'newSourceNativeMeasurements','originalMaterialsBefore','originalMaterialsSaved','originalTreesBefore','originalTreesSaved','originalGrassBefore','originalGrassSaved'])await pinned(r[key]);
  assert.deepEqual(await pj(r.beforeActorWitness),await pj(baseReport.savedActorWitness));
  const contentInventory=await pj(r.afterContentInventory),packages=r.newPackages.map(p=>{assert(p.startsWith('/Game/')&&!p.includes('.'));return p.replace(/^\/Game\//,'')+'.uasset';});
  validateFernOnlyContent(e.contentInventory,contentInventory,packages,r.assetDelta);
  assert.deepEqual(r.baseContentInventory,baseReport.afterContentInventory);await pinned(r.baseContentInventory);
  assert.deepEqual(r.protectedProjectProof,baseReport.protectedProjectProof);const projectProof=await pj(r.protectedProjectProof);assert.deepEqual(projectProof,e.projectProof);
  assert.equal(r.projectClone.path,path.join(source,'garden-fern-only-project-clone.json'));const clone=await pj(r.projectClone);
  assert.equal(clone.schema,SCHEMA);assert.equal(clone.status,'verified-original-r29a-independent-apfs-r34-clone-before-fern-only-native');
  assert.equal(clone.project,project);assert.equal(clone.sourceProject,e.project);assert.equal(clone.fileCount,4192);assert.equal(clone.contentFiles,4060);assert.equal(clone.protectedFiles,132);
  assert.equal(clone.nativeExecuted,false);assert.equal(clone.selectedPlan,null);assert.deepEqual(clone.nativeBaseReport,r.baseNativeReport);assert.deepEqual(clone.sourceProposal,r.sourceProposal);
  assert.deepEqual(plan.projectClone,r.projectClone);
  const originalFiles={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...projectProof},seen=new Set();assert.equal(clone.files.length,4192);
  // These rows witness the immutable initial clone, not the legitimately changed saved candidate map size.
  for(const row of clone.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(originalFiles,relative)&&!seen.has(relative));seen.add(relative);
    assert.equal(row.source,path.join(e.project,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);
    assert.deepEqual({sha256:row.sha256,bytes:row.bytes},originalFiles[relative]);const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);
    assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);}
  assert.equal(seen.size,4192);
  const views=await read(path.join(project,'Content/Data/viewpoints.json'));assert.deepEqual(views,await read(path.join(e.project,'Content/Data/viewpoints.json')));
  for(const id of ['exterior-garden','neighbor-finish-close-r18'])assert.equal(views.views.filter(v=>v.id===id).length,1);
  assert(hashLike(CHECKER_SHA),'Actual final frozen checker pin required');const checker=path.join(root,'scripts/unreal/exterior-garden-fern-only-editor-check-r24.py');assert.equal(await sha(checker),CHECKER_SHA);closure.add(checker);
  const native=JSON.parse((await exec('python3',['-B',checker,receiptPath],{timeout:180000,maxBuffer:1024*1024})).stdout);
  assert.equal(native.nativeProcessId,21209);assert.equal(native.savedActors,5354);assert.equal(native.retainedOriginalGardenRoots,437);assert.equal(native.newOriginalFernRoots,36);
  assert.equal(native.fullNativeF32PositionUV0TopologyProofTriangles,3848);assert.equal(native.storedNewMatricesIndependentlyDecodedAfterSaveByCpuChecker,false);
  const processPath=path.join(source,'garden-fern-only-native.log.json'),terminalPath=path.join(source,'garden-fern-only-native-process.json');
  const proc=await read(processPath),terminal=await read(terminalPath);assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,21209);
  assert.equal(terminal.reportSha256,REPORT_SHA);assert.equal(terminal.processFile,processPath);assert.equal(terminal.processFileSha256,await sha(processPath));
  assert.equal(terminal.logFile,path.join(source,'garden-fern-only-native.log'));assert.equal(terminal.logSha256,await sha(terminal.logFile));
  assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));
  assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+terminal.logFile])assert(proc.args.includes(arg));
  assert.equal(terminal.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(terminal.sourcePinsBeforeNative).length,472);
  assert.equal(terminal.controllerSha256BeforeNative,terminal.controllerSha256AfterNative);assert.equal(await sha(terminal.controller),terminal.controllerSha256BeforeNative);
  for(const[file,h]of Object.entries(terminal.sourcePinsBeforeNative)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const file of [processPath,terminalPath,terminal.logFile,terminal.controller])closure.add(file);
  const rootAuditPath=path.join(source,'root-native-byte-audit-r34a.json');assert.equal(await sha(rootAuditPath),ROOT_AUDIT_SHA);closure.add(rootAuditPath);
  const audit=await read(rootAuditPath);assert.deepEqual(audit.nativeReport,{path:receiptPath,sha256:REPORT_SHA,bytes:(await fs.stat(receiptPath)).size});
  assert.equal(audit.currentContentFiles,4071);assert.equal(audit.currentProtectedFiles,132);assert.equal(audit.status,'verified-current-byte-closure-stored-native-witness-matches');assert.equal(audit.all4192OriginalR29SourceFilesExact,true);
  assert.equal(audit.onlyOldCandidateMapChanged,true);assert.equal(audit.newPackageCount,11);assert.deepEqual(audit.exactNewPackages,packages.sort());assert.equal(audit.rootPinsVerified,472);assert.equal(audit.storedNativeWitnessMatches,true);assert.equal(audit.freshNativeActorDecodePerformedByRootByteAudit,false);
  const w=r.nativeModuleWitness,module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');
  assert.equal(w.source,path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.destination,module);assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);
  for(const file of [module,w.source])await pinned({path:file,sha256:MODULE_SHA,bytes:w.bytes});
  const summary={...native,sourcePinsUnchangedAfterNative:472,scope:'36 fern-only low-root substitutions on exact saved R29; all12 original ornamentals and41 flowers remain. Native saving is separate from matched appearance.'};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:e.base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:w,moduleWitnessSource:r.projectClone,
    receiptSummary:{baseNativeReport:r.baseNativeReport,selectedPlan:r.selectedPlan,sourcePreflight:r.sourcePreflight,stepProjectionPolicy:r.stepProjectionPolicy,allOriginal12OrnamentalActorsAndMembersUnchanged:true,allOriginal41FlowersUnchanged:true,yardIntegrationApplied:false,savedMapUnloadedReloaded:true,meshMaterialPackagesIndependentlyUnloaded:false,summary}};
}
