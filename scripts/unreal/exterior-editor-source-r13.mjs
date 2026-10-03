// Closed actual R27 four-donor save. Source/native/Editor appearance stay separate.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR10,validateProjectClosure} from './exterior-editor-source-r10.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-realism-clean-integration-native-r27.py';
const HELPER_SHA='2cdc51b8ebf6007f1493b06df969c3e04a1ec650b797897ebe2b18d9993ac8cc';
const PLAN_SHA='662ea41663142e22ff744530fd0337833389beaed1b1ca590e6a6cd53aa511a4';
const BASE_SHA='1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122';
const REPORT_SHA='5575c0e37a9d48733b5c7ed3746f1731cc2b7958634a845c87b9700ff4fc9498';
const CHECKER_SHA='46b7b997acfe7133e3a8c999930e1f679dc153ff98a52ff7796d10754b5d839c';
const R10_SHA='23652e2dd8969e57fa85c0e3cb935317cb452417964748fd66f4602720563756';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const SCHEMA='brezi-exterior-realism-clean-four-saved-donor-integration-r27';
const exec=promisify(execFile),read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};

export function validateCleanHeader(r,{source,project}){
  assert.equal(r.schema,SCHEMA);assert.equal(r.owner,OWNER);assert.equal(r.status,'verified-saved-four-donor-clean-exterior-realism-integration');
  assert.equal(r.output,source);assert.equal(r.project,project);assert.equal(r.selectedPlan.sha256,PLAN_SHA);assert.equal(r.baseNativeReport.sha256,BASE_SHA);
  for(const k of ['nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted','shippingPackageProduced',
    'nativeMaterialPackagesIndependentlyReloaded','nativeMeshPackagesIndependentlyReloaded','nativeNormalTangentReadbackAvailable',
    'originalExteriorOwnershipSpoofed','originalGrassMemberMutationApisCalled','seedRangeMutationApisCalled'])assert.equal(r[k],false);
  for(const k of ['savedMapUnloadedReloaded','originalR16Unchanged','sourceInputsUnchanged','donorFilesNeverMutated',
    'originalGrassRawMatricesAndObservedSeedControlsExact'])assert.equal(r[k],true);
  assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});
  assert.equal(r.nativeProcessId,65450);assert.equal(r.actualFullSceneHismComponents,2309);assert.equal(r.actualFullSceneHismInstances,676944);
  assert.equal(r.actualRecordedExteriorHismGroups,1984);assert.equal(r.actualRecordedExteriorHismInstances,632538);
  assert.equal(r.scopedMaterialGraphs,54);assert.equal(r.scopedTextureObjects,77);assert.equal(r.originalPlantMastersPreserved,135);assert.equal(r.originalPlantLodsPreserved,405);
  assert.equal(r.combinedAppearanceGoNoGo,'NO_GO_UNTIL_MATCHED_NATIVE_COMBINED_REVIEW');assert.equal(r.knownReviewLimits.length,3);
  assert.deepEqual(r.excludedDonors,['R20_CURVED_GRASS','R23_CREAM_ROOF']);assert.deepEqual(Object.keys(r.savedDonors).sort(),['foreground','leaf','neighbors','visibility']);
  assert.equal(r.moduleOrderWitness.cacheDeletedOrReplaced,false);assert.equal(r.moduleOrderWitness.cachePreservedAcrossReusedHelpers,true);
  assert.equal(r.moduleOrderWitness.sha256,'5f9eb8ccc2688b7d17200696cd3498558743c60fc541f8b1fbb0e80a3ba94b9e');
}

export function validateCleanContent(before,after,packages,delta,viewHash){
  assert.equal(Object.keys(before).length,3975);assert.equal(Object.keys(after).length,4034);assert.equal(packages.length,59);
  assert.equal(new Set(packages.map(r=>r.relativeContentPath)).size,59);
  const expected=structuredClone(before);
  for(const r of packages){
    assert(!Object.hasOwn(before,r.relativeContentPath));assert(r.relativeContentPath.endsWith('.uasset'));
    assert(/^(Brezi\/CanopyTransmissionR1|Brezi\/NeighborFinish20261001R18|Brezi\/CanopyForeground20261002R21)\//.test(r.relativeContentPath));
    expected[r.relativeContentPath]={sha256:r.sha256,bytes:r.bytes};
  }
  assert.deepEqual(Object.keys(after).sort(),Object.keys(expected).sort());
  const changed=Object.keys(before).filter(k=>after[k].sha256!==before[k].sha256||after[k].bytes!==before[k].bytes).sort();
  assert.deepEqual(changed,['Brezi/Maps/Brezi.umap','Data/viewpoints.json']);assert.equal(after['Data/viewpoints.json'].sha256,viewHash);
  for(const [key,row]of Object.entries(expected))if(!changed.includes(key))assert.deepEqual(after[key],row,`Original/copied asset bytes differ: ${key}`);
  assert.deepEqual(delta,{changedOriginalFiles:changed,newPackageFiles:packages.map(r=>r.relativeContentPath).sort(),newUassetPackages:59,
    originalContentFileCount:3975,savedContentFileCount:4034,originalNativeAssetsByteIdentical:3973,removedOriginalFiles:[]});
}

export function validateCleanGrassControls(before,saved){
  assert.deepEqual(saved,before);assert.deepEqual(Object.keys(saved).sort(),[0,1,2,3].map(i=>`EX_meadow_-3_2_LawnTuft${i}`));
  for(const [i,count]of [2230,2190,2288,2241].entries()){
    const row=saved[`EX_meadow_-3_2_LawnTuft${i}`];assert.equal(row.instances,count);assert(hashLike(row.rawMatrixBinary64Sha256)&&hashLike(row.customDataSha256));
    assert(Number.isInteger(row.instancingRandomSeed)&&Number.isInteger(row.numCustomDataFloats));
    assert.equal(row.originalMemberMutationApisCalled,false);assert.equal(row.seedRangeMutationApisCalled,false);
    assert.equal(row.additionalRandomSeeds.available,false);assert.equal(row.additionalRandomSeeds.rangeValuesObserved,false);
    assert.equal(row.additionalRandomSeeds.rangePreservationClaimed,false);assert.match(row.additionalRandomSeeds.error,/protected/);
  }
}

export function validateCleanReportNames(names){
  const name='realism-clean-integration-native-report.json';assert(names.includes(name));
  assert(!names.some(n=>n!==name&&(/(?:exterior-import|native-report|overlay-report).*\.json$/.test(n))),
    'A clean candidate cannot inherit an original/donor/failed report');
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source),name='realism-clean-integration-native-report.json';
  const previous=fileURLToPath(new URL('exterior-editor-source-r10.mjs',import.meta.url));assert.equal(await sha(previous),R10_SHA);
  if(!names.includes(name)){
    assert(!/^exterior-20261002-r27/.test(path.basename(source))&&!names.some(n=>/^realism-clean-integration-native-report/.test(n)),
      'Failed/running/unknown R27 candidate cannot inherit another native receipt');
    const evidence=await loadR10(source,{root});evidence.additionalClosureFiles.push(previous);return evidence;
  }
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r27a'));validateCleanReportNames(names);
  const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,name),r=await read(receiptPath),closure=new Set([receiptPath,previous]);
  validateCleanHeader(r,{source,project});assert.equal(await sha(receiptPath),REPORT_SHA);
  async function pinned(pin){
    assert(pin&&path.isAbsolute(pin.path)&&path.resolve(pin.path)===pin.path&&hashLike(pin.sha256)&&Number.isInteger(pin.bytes)&&pin.bytes>=0);
    const s=await fs.lstat(pin.path);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(s.size,pin.bytes);assert.equal(await sha(pin.path),pin.sha256);
    closure.add(pin.path);return pin.path;
  }
  const pj=async pin=>read(await pinned(pin));
  assert.equal(r.selectedPlan.path,path.join(root,'output/unreal/exterior-realism-clean-integration-20261002-r27-study/realism-clean-integration-plan.json'));
  assert.equal(r.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261001-r16a/exterior-import-report.json'));
  const plan=await pj(r.selectedPlan),base=await pj(r.baseNativeReport);assert.deepEqual(r.inputFiles,plan.inputFiles);assert.equal(Object.keys(r.inputFiles).length,247);
  assert.deepEqual(r.ownedSources,plan.ownedSources);assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);
  for(const[file,h]of Object.entries(r.inputFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const key of ['beforeActorWitness','expectedActorWitness','savedActorWitness','materialsBefore','materialsSaved','originalGeometryAfter',
    'originalGrassControlsBefore','originalGrassControlsSaved','diagnosticViewpoints'])await pinned(r[key]);
  validateCleanGrassControls(await pj(r.originalGrassControlsBefore),await pj(r.originalGrassControlsSaved));
  const before=await pj(plan.baseContentInventory),contentInventory=await pj(r.afterContentInventory),projectProof=await pj(r.protectedProjectProof),packages=await pj(plan.copiedPackages);
  assert.deepEqual(r.protectedProjectProof,plan.baseProjectProof);assert.equal(Object.keys(projectProof).length,132);
  for(const[relative,row]of Object.entries(projectProof))assert(!path.isAbsolute(relative)&&path.normalize(relative)===relative&&!relative.includes('..')
    &&(relative==='BreziTwin.uproject'||/^(Config|Source|Binaries)\//.test(relative))&&hashLike(row.sha256)&&Number.isInteger(row.bytes));
  validateCleanContent(before,contentInventory,packages,r.assetDelta,plan.diagnosticViewpoints.sha256);
  assert.deepEqual(Object.keys(base.afterAssetHashes).sort(),Object.keys(before).map(k=>path.join(base.project,'Content',k)).sort());
  for(const[relative,row]of Object.entries(before))assert.equal(row.sha256,base.afterAssetHashes[path.join(base.project,'Content',relative)]);
  const views=await pj(r.diagnosticViewpoints),originalViews=await read(path.join(base.project,'Content/Data/viewpoints.json'));
  assert.deepEqual({...views,views:views.views.slice(0,-1)},originalViews);assert.equal(views.views.length,originalViews.views.length+1);
  assert.equal(views.views.at(-1).id,'neighbor-finish-close-r18');
  for(const id of ['exterior-canopy-close','exterior-parcels','neighbor-finish-close-r18','exterior-garden'])assert.equal(views.views.filter(v=>v.id===id).length,1);
  closure.add(path.join(base.project,'Content/Data/viewpoints.json'));
  const clone=await pj(r.projectClone),copied=await pj(r.copiedPackageReceipt);
  assert.equal(r.projectClone.path,path.join(source,'realism-clean-integration-project-clone.json'));assert.equal(r.copiedPackageReceipt.path,path.join(source,'realism-clean-integration-package-copy.json'));
  assert.equal(clone.status,'verified-byte-identical-independent-apfs-r27-project-clone-and-59-native-packages-before-integration');
  assert.equal(copied.status,'verified-byte-identical-independent-apfs-59-clean-donor-packages-before-integration');
  for(const value of [clone,copied]){
    assert.equal(value.schema,SCHEMA);assert.equal(value.owner,'scripts/unreal/exterior-realism-clean-integration-copy-r27.py');assert.deepEqual(value.selectedPlan,r.selectedPlan);
    assert.deepEqual(value.baseNativeReport,r.baseNativeReport);assert.equal(value.project,project);assert.equal(value.nativeExecuted,false);await pinned(value.originalBaseCloneProof);
  }
  const pending=await pj(clone.originalBaseCloneProof);assert.deepEqual(copied.originalBaseCloneProof,clone.originalBaseCloneProof);
  assert.equal(pending.status,'verified-original-r16-independent-apfs-r27-clone-before-clean-package-copy');assert.equal(pending.selectedPlan,null);
  assert.equal(pending.nativeExecuted,false);assert.equal(pending.packageCopyPending,true);assert.equal(pending.fileCount,4107);assert.deepEqual(pending.baseNativeReport,r.baseNativeReport);
  assert.equal(clone.originalFileCount,4107);assert.equal(clone.newCopiedPackageCount,59);assert.equal(clone.contentFileCount,4034);
  assert.deepEqual(clone.packageCopyReceipt,r.copiedPackageReceipt);assert.deepEqual(clone.baseContentInventory,plan.baseContentInventory);assert.deepEqual(clone.baseProjectProof,plan.baseProjectProof);
  assert.equal(clone.originalFilesIndependentAndByteIdentical,true);assert.equal(clone.copiedPackagesIndependentAndByteIdentical,true);
  assert.equal(copied.sceneMapChanged,false);assert.equal(copied.viewpointsChanged,false);assert.equal(copied.copiedPackageCount,59);
  assert.equal(copied.originalContentFilesUnchanged,3975);assert.equal(copied.protectedOriginalFilesUnchanged,132);assert.equal(copied.originalGrassInstanceDataNeverWritten,true);
  assert.deepEqual(copied.excludedDonors,r.excludedDonors);
  assert.deepEqual(copied.copiedPackages,packages.map(row=>({...row,destination:path.join(project,'Content',row.relativeContentPath),independentInodes:true})));
  for(const row of copied.copiedPackages){const[a,b]=await Promise.all([fs.stat(row.source),fs.stat(row.destination)]);assert(a.dev!==b.dev||a.ino!==b.ino);closure.add(row.source);}
  const checker=path.join(root,'scripts/unreal/exterior-realism-clean-integration-editor-check-r13.py');closure.add(checker);assert.equal(await sha(checker),CHECKER_SHA);
  const native=JSON.parse((await exec('python3',['-B',checker,receiptPath],{timeout:120000,maxBuffer:1024*1024})).stdout);
  const processPath=path.join(source,'realism-clean-integration-native.log.json'),processReceiptPath=path.join(source,'realism-clean-integration-native-process.json');
  const proc=await read(processPath),terminal=await read(processReceiptPath);
  assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,r.nativeProcessId);assert.equal(terminal.reportSha256,REPORT_SHA);
  assert.equal(terminal.processFile,processPath);assert.equal(terminal.processFileSha256,await sha(processPath));
  assert.equal(terminal.logFile,path.join(source,'realism-clean-integration-native.log'));assert.equal(terminal.logSha256,await sha(terminal.logFile));
  assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));
  assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+terminal.logFile])assert(proc.args.includes(arg));
  assert.equal(terminal.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(terminal.sourcePinsBeforeNative).length,252);
  assert.equal(terminal.controllerSha256BeforeNative,terminal.controllerSha256AfterNative);assert.equal(await sha(terminal.controller),terminal.controllerSha256BeforeNative);
  for(const[file,h]of Object.entries(terminal.sourcePinsBeforeNative)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const file of [processPath,processReceiptPath,terminal.logFile,terminal.controller])closure.add(file);
  const w=r.nativeModuleWitness,module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');
  assert.equal(w.source,path.join(base.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.destination,module);
  assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);
  const[a,b]=await Promise.all([fs.stat(w.source),fs.stat(module)]);assert(a.dev!==b.dev||a.ino!==b.ino);
  await pinned({path:module,sha256:MODULE_SHA,bytes:w.bytes});await pinned({path:w.source,sha256:MODULE_SHA,bytes:w.bytes});
  const summary={...native,protectedProjectFiles:132,sourcePinsUnchangedAfterNative:252,
    scope:'Clean four-donor REVIEW candidate; original grass retained. Appearance/performance/Shipping acceptance stays open.'};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:w,
    moduleWitnessSource:r.selectedPlan,receiptSummary:{baseNativeReport:r.baseNativeReport,selectedPlan:r.selectedPlan,savedDonors:r.savedDonors,
      excludedDonors:r.excludedDonors,savedMapUnloadedReloaded:true,materialPackagesIndependentlyReloaded:false,meshPackagesIndependentlyReloaded:false,summary}};
}
