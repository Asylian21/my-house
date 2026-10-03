// Four whole-group original tree replacements; saved/source proof and appearance are separate.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR16,validateProjectClosure} from './exterior-editor-source-r16.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-original-tree-group-native-r29.py';
const HELPER_SHA='bcab2d0b5e03fdf05e04f4eb35bdb5288efb4f46a3d78ac4392d7c680ad42163';
const SCHEMA='brezi-original-tree-four-existing-grove-roots-overlay-r29';
const PLAN_SHA='fe36aa322f1a3c7cfce36be64c285f70dc8d90be67234032a99ec2e8dd3b5fd3';
const SOURCE_SHA='f3d0e2e2ebf42c4e39fedafb8dd7aba0c819e98c4b91a7388983af3557c45f57';
const PREFLIGHT_SHA='c803b0d46299effc724d54578070728b31d78b514a771c4b0f1a292d2f22e479';
const BASE_SHA='dfbca65515fc08aea52515195ab5ef752fe07cdca622cd41964e99875ced2456';
const DONOR_SHA='869ed396ed7946cb0ea562d3f2da77f8dbd9f3d65777250b9686171697aa10f1';
const REPORT_SHA='a11b95edf10e79fed7d1ff5c43b350634f825aedbf0ab58e8ee22642e73679fd';
const R16_SHA='98b62be5543ff674833b8d259ff9068c6ad4b09cefba1d16f4405708db8b10d2';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const CHECKER_SHA='c500720cd961cc3b1b163d1054b2a86487562eeff071422e517ccd31b179dd69';
const IDS=['village_nearest_grove_3','village_nearest_grove_11','village_nearest_grove_27','village_nearest_grove_30'];
const COUNTS={originalActors:5350,savedActors:5351,fullHismComponents:2313,fullHismInstances:676957,
  groveOriginalRemainingRoots:74,newOwnedTreeRoots:4,scopedMaterialGraphs:59,scopedTextureObjects:87,
  copiedPackages:17,contentFiles:4060,protectedFiles:132};
const read=async p=>JSON.parse(await fs.readFile(p,'utf8')),exec=promisify(execFile);
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};

export function validateOriginalTreeGroupHeader(r,{source,project}){
  assert.equal(r.schema,SCHEMA);assert.equal(r.owner,OWNER);assert.equal(r.status,'verified-saved-four-original-tree-existing-grove-roots');
  assert.equal(r.output,source);assert.equal(r.project,project);assert.equal(r.nativeProcessId,76135);
  for(const[k,h]of Object.entries({selectedPlan:PLAN_SHA,sourceProposal:SOURCE_SHA,sourcePreflight:PREFLIGHT_SHA,baseNativeReport:BASE_SHA,savedTreeDonor:DONOR_SHA}))assert.equal(r[k].sha256,h);
  for(const k of ['nativeApplied','savedMapUnloadedReloaded','originalSavedR28bUnchanged','sourceInputsUnchanged',
    'originalRemaining74RawMatricesAndObservedControlsExact','original8949GrassRawControlsExact'])assert.equal(r[k],true);
  for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','ecologicalFitVerified','shippingVerified','packageVerified',
    'nativeNormalTangentReadbackAvailable','nativeMaterialPackagesIndependentlyUnloaded','nativeMeshPackagesIndependentlyUnloaded',
    'selectedTreeNaniteRenderPassVerified','AdditionalRandomSeedsReadbackAvailable','seedRangeReconstructionPerformed',
    'retainedMemberReconstructionPerformed','sourceRootGroundElevationSurveyed','actualRuntimeDrawnTreeTriangleCountMeasured'])assert.equal(r[k],false);
  assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});
  assert.deepEqual(r.actualCounts,COUNTS);assert.equal(r.materialGraphAssets,59);assert.equal(r.textureAssets,87);assert.equal(r.sourceInputTrianglesAcross4Instances,8249948);
  assert.deepEqual(r.retiredOriginalGroup,{actor:'/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.BreziVegetationPatch_1739',
    groupId:'EX_regional_1_4_canopy_fullness_broadleaf_r1_c_125000',retiredSourceRootIds:IDS,retiredMembers:4,remainingMembers:0,actorComponentKept:true});
  const g=r.newOriginalTreeGroup;assert.deepEqual(g.rootIds,IDS);assert.equal(g.instances,4);assert.equal(g.orderedMeasuredTransformAndStoredMatrixSavedExact,true);
  assert.deepEqual(g.nativeStoredMatrixFullVertexMasks.map(v=>v.rootId),IDS);
  for(const v of g.nativeStoredMatrixFullVertexMasks){assert.equal(v.decodedFullOriginalVertices,1777278);assert.equal(v.completeOriginalTriangleInteriorsConservativelyProven,2062487);
    assert.equal(v.nativeStoredMatrixReadbackUsed,true);for(const k of ['float32ProjectionIsGpuReadback','sourceLandUseAndElevationSurveyed','normalTangentNativeReadbackAvailable'])assert.equal(v[k],false);}
}

export function validateOriginalTreeGroupReportNames(names){
  const selected='original-tree-group-native-report.json';assert(names.includes(selected));
  assert(!names.some(n=>n!==selected&&/(?:exterior-import|native-report|overlay-report).*\.json$/.test(n)),
    'R29 cannot inherit an old, donor, failed or unknown native report');
}

export function validateOriginalTreeGroupContent(before,after,packages,delta){
  assert.equal(Object.keys(before).length,4043);assert.equal(Object.keys(after).length,4060);assert.equal(packages.length,17);
  const keys=packages.map(r=>r.relativeContentPath);assert.equal(new Set(keys).size,17);
  for(const r of packages){assert(/^Brezi\/OriginalTree20261002R24\/.+\.uasset$/.test(r.relativeContentPath));assert(!Object.hasOwn(before,r.relativeContentPath));
    assert.deepEqual(after[r.relativeContentPath],{sha256:r.sha256,bytes:r.bytes});}
  assert.deepEqual(Object.keys(after).sort(),[...Object.keys(before),...keys].sort());
  assert.deepEqual(Object.keys(before).filter(k=>JSON.stringify(before[k])!==JSON.stringify(after[k])),['Brezi/Maps/Brezi.umap']);
  assert.deepEqual(delta,{changedOriginalFiles:['Brezi/Maps/Brezi.umap'],newCopiedPackageFiles:[...keys].sort(),
    originalContentFiles:4043,savedContentFiles:4060,copiedPackages:17,newGeneratedAssetPackages:0});
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source),filename='original-tree-group-native-report.json';
  const previous=fileURLToPath(new URL('exterior-editor-source-r16.mjs',import.meta.url));assert.equal(await sha(previous),R16_SHA);
  if(!names.includes(filename)){
    assert(!/^exterior-20261002-r29/.test(path.basename(source))&&!names.some(n=>/^original-tree-group-native-report/.test(n)),
      'Running, failed or unknown R29 cannot delegate to an older receipt');
    const e=await loadR16(source,{root});e.additionalClosureFiles.push(previous);return e;
  }
  assert(hashLike(CHECKER_SHA),'Final actual source-template checker pin required');
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r29a'));validateOriginalTreeGroupReportNames(names);
  const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,filename),r=await read(receiptPath),closure=new Set([receiptPath,previous]);
  validateOriginalTreeGroupHeader(r,{source,project});assert.equal(await sha(receiptPath),REPORT_SHA);
  async function pinned(row){
    assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);
    const s=await fs.lstat(row.path);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(s.size,row.bytes);assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;
  }
  const pj=async row=>read(await pinned(row));
  assert.equal(r.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261002-r28b/context-yard-native-report-r2.json'));
  const e=await loadR16(path.dirname(r.baseNativeReport.path),{root});assert.equal(e.nativeReceiptPath,r.baseNativeReport.path);assert.equal(e.summary.savedActors,5350);
  for(const file of e.additionalClosureFiles)closure.add(file);const baseReport=await pj(r.baseNativeReport);
  assert.equal(r.savedTreeDonor.path,path.join(root,'output/unreal/exterior-20261002-r24b/original-tree-native-report-r2.json'));const donor=await pj(r.savedTreeDonor);
  assert.equal(r.selectedPlan.path,path.join(root,'output/unreal/exterior-original-tree-group-20261002-r29-native-study-r1/original-tree-group-native-plan.json'));
  const plan=await pj(r.selectedPlan);assert.deepEqual(plan.baseNativeReport,r.baseNativeReport);assert.deepEqual(plan.savedTreeDonor,r.savedTreeDonor);
  assert.equal(r.sourcePreflight.path,path.join(root,'output/unreal/exterior-original-tree-group-20261002-r29-native-study-r1/source-preflight/source-preflight.json'));
  const preflight=await pj(r.sourcePreflight);assert.deepEqual(r.inputFiles,preflight.inputFiles);assert.equal(Object.keys(r.inputFiles).length,385);
  assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);
  assert.deepEqual(r.sourceProposal,plan.sourceProposal);await pinned(r.sourceProposal);
  for(const[file,h]of Object.entries(r.inputFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const key of ['beforeActorWitness','expectedActorWitness','savedActorWitness','remaining74Before','remaining74Saved','originalMaterialsBefore','originalMaterialsSaved'])await pinned(r[key]);
  await pinned(r.newOriginalTreeGroup.measurement);
  assert.deepEqual(r.nativeSourceGeometry,donor.nativeSourceGeometry);assert.deepEqual(r.naniteResourceReadback,donor.naniteResourceReadback);
  assert.equal(r.nativeSourceGeometry.sampledNativeTriangles,4096);assert.equal(r.nativeSourceGeometry.sourceTriangles,2062487);
  assert.equal(r.nativeSourceGeometry.nativeFullPositionUV0UV1CornerReadbackPerformed,false);
  assert.equal(r.newOriginalTreeGroup.mesh,donor.newMesh);assert.deepEqual(r.newOriginalTreeGroup.materialAssets,Object.values(donor.materials.materials).map(v=>v.asset));
  const packages=await pj(r.copiedPackages);assert.deepEqual(r.copiedPackages,plan.copiedPackages);
  const contentInventory=await pj(r.afterContentInventory);validateOriginalTreeGroupContent(e.contentInventory,contentInventory,packages,r.assetDelta);
  assert.deepEqual(r.baseContentInventory,baseReport.afterContentInventory);await pinned(r.baseContentInventory);
  assert.deepEqual(r.protectedProjectProof,baseReport.protectedProjectProof);const projectProof=await pj(r.protectedProjectProof);assert.deepEqual(projectProof,e.projectProof);
  assert.equal(r.projectClone.path,path.join(source,'original-tree-group-project-clone.json'));const clone=await pj(r.projectClone);
  assert.equal(r.packageCopyReceipt.path,path.join(source,'original-tree-group-package-copy.json'));const copied=await pj(r.packageCopyReceipt);
  for(const v of [clone,copied]){assert.equal(v.schema,SCHEMA);assert.equal(v.owner,'scripts/unreal/exterior-original-tree-group-copy-r29.py');
    assert.deepEqual(v.selectedPlan,r.selectedPlan);assert.deepEqual(v.baseNativeReport,r.baseNativeReport);assert.deepEqual(v.sourceProposal,r.sourceProposal);assert.equal(v.project,project);assert.equal(v.nativeExecuted,false);}
  assert.equal(clone.status,'verified-byte-identical-independent-apfs-r29-project-clone-and17-tree-packages-before-native');
  assert.equal(copied.status,'verified-byte-identical-independent-apfs-r29-17-saved-tree-packages-before-native');assert.deepEqual(clone.packageCopyReceipt,r.packageCopyReceipt);
  assert.deepEqual(clone.originalBaseCloneProof,copied.originalBaseCloneProof);assert.equal(clone.originalBaseCloneProof.path,path.join(source,'original-tree-group-base-clone-proof.json'));
  const initial=await pj(clone.originalBaseCloneProof);assert.equal(initial.schema,SCHEMA);assert.equal(initial.status,'verified-original-r28b-independent-apfs-r29-clone-before-tree-package-copy');
  assert.deepEqual(initial.nativeBaseReport,r.baseNativeReport);assert.deepEqual(initial.originalTreeSourceProposal,r.sourceProposal);
  assert.equal(initial.nativeExecuted,false);assert.equal(initial.selectedPlan,null);assert.equal(initial.packageCopyPending,true);assert.equal(initial.fileCount,4175);
  const originalFiles={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...projectProof},seen=new Set();assert.equal(initial.files.length,4175);
  for(const row of initial.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(originalFiles,relative)&&!seen.has(relative));seen.add(relative);
    assert.equal(row.source,path.join(e.project,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);
    assert.deepEqual({sha256:row.sha256,bytes:row.bytes},originalFiles[relative]);const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);
    assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);}
  assert.equal(seen.size,Object.keys(originalFiles).length);assert.equal(clone.contentFileCount,4060);assert.equal(clone.originalFileCount,4175);
  assert.equal(clone.newCopiedPackageCount,17);assert.equal(copied.copiedPackageCount,17);
  assert.equal(clone.originalFilesIndependentAndByteIdentical,true);assert.equal(clone.copiedPackagesIndependentAndByteIdentical,true);
  assert.deepEqual(copied.copiedPackages,packages.map(v=>({...v,destination:path.join(project,'Content',v.relativeContentPath),independentInodes:true})));
  for(const row of copied.copiedPackages){assert.equal(row.source,path.join(root,'output/unreal/exterior-20261002-r24b/Project/BreziTwin/Content',row.relativeContentPath));
    for(const file of [row.source,row.destination])await pinned({path:file,sha256:row.sha256,bytes:row.bytes});
    const[a,b]=await Promise.all([fs.stat(row.source),fs.stat(row.destination)]);assert(a.dev!==b.dev||a.ino!==b.ino);}
  for(const k of ['sceneMapChanged','viewpointsChanged','geometryImportedOrGenerated','originalActorOrMemberMutationApisCalled'])assert.equal(copied[k],false);
  const views=await read(path.join(project,'Content/Data/viewpoints.json'));assert.deepEqual(views,await read(path.join(e.project,'Content/Data/viewpoints.json')));
  for(const id of ['exterior-canopy-close','neighbor-finish-close-r18'])assert.equal(views.views.filter(v=>v.id===id).length,1);
  const checker=path.join(root,'scripts/unreal/exterior-original-tree-group-editor-check-r19.py');assert.equal(await sha(checker),CHECKER_SHA);closure.add(checker);
  const native=JSON.parse((await exec('python3',['-B',checker,receiptPath],{timeout:180000,maxBuffer:1024*1024})).stdout);
  assert.equal(native.nativeProcessId,76135);assert.equal(native.savedActors,5351);
  const processPath=path.join(source,'original-tree-group-native.log.json'),terminalPath=path.join(source,'original-tree-group-native-process.json');
  const proc=await read(processPath),terminal=await read(terminalPath);assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,76135);
  assert.equal(terminal.reportSha256,REPORT_SHA);assert.equal(terminal.processFile,processPath);assert.equal(terminal.processFileSha256,await sha(processPath));
  assert.equal(terminal.logFile,path.join(source,'original-tree-group-native.log'));assert.equal(terminal.logSha256,await sha(terminal.logFile));
  assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));
  assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+terminal.logFile])assert(proc.args.includes(arg));
  assert.equal(terminal.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(terminal.sourcePinsBeforeNative).length,387);
  assert.equal(terminal.controllerSha256BeforeNative,terminal.controllerSha256AfterNative);assert.equal(await sha(terminal.controller),terminal.controllerSha256BeforeNative);
  for(const[file,h]of Object.entries(terminal.sourcePinsBeforeNative)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const file of [processPath,terminalPath,terminal.logFile,terminal.controller])closure.add(file);
  const w=r.nativeModuleWitness,module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');
  assert.equal(w.source,path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.destination,module);assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);
  for(const file of [module,w.source])await pinned({path:file,sha256:MODULE_SHA,bytes:w.bytes});
  const summary={...native,protectedProjectFiles:132,sourcePinsUnchangedAfterNative:387,
    scope:'Four original tree replacements REVIEW candidate on exact saved R28b. Source/sample counts do not grant render, appearance or performance acceptance.'};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:e.base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:w,moduleWitnessSource:r.projectClone,
    receiptSummary:{baseNativeReport:r.baseNativeReport,savedTreeDonor:r.savedTreeDonor,selectedPlan:r.selectedPlan,sourcePreflight:r.sourcePreflight,savedMapUnloadedReloaded:true,summary}};
}
