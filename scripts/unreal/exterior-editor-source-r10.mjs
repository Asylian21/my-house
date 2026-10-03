// Closed six-donor R22 R3 saved scene reader. Native save and Editor screenshots
// remain distinct from appearance/performance/Shipping acceptance.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR9,validateProjectClosure} from './exterior-editor-source-r9.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-realism-integration-native-r22-r3.py';
const HELPER_SHA='f93ea98e9599ac85abd2842dc8c08d50f7977366fa1bb3ae35b5923bfd12cbae';
const PLAN_SHA='749d722da80886509105b4e4fa68da665aa2769a2345e46afa7cc1d989659e7f';
const REPAIR_SHA='e8bd3820bc1a459d15167c0167ac30fd05c5e5a9e620f7a792d25a300961b179';
const BASE_SHA='1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const CHECKER_SHA='a9f1baa96b892523b087cf1650419ed98b59f26297e8a4b443a450fbca63e70d';
const REPORT_SHA='999fc17ea7600136a2097aecefed3d846ff0d7e9baeb7f005480b113b60b1f40';
const R9_SHA='d290e390252519804fecb528431d770d5d95cb2d0ee74184c39a3ee9db1d0703';
const SCHEMA='brezi-exterior-realism-saved-donor-integration-r22';
const REPAIR_SCHEMA='brezi-exterior-realism-complete-neighbor-material-lookup-repair-r22-r3';
const exec=promisify(execFile),read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};

export function validateIntegratedHeader(r,{source,project}){
  assert.equal(r.schema,SCHEMA);assert.equal(r.repairSchema,REPAIR_SCHEMA);assert.equal(r.owner,OWNER);
  assert.equal(r.status,'verified-saved-six-donor-exterior-realism-integration');assert.equal(r.output,source);assert.equal(r.project,project);
  assert.equal(r.selectedPlan.sha256,PLAN_SHA);assert.equal(r.repairSupplement.sha256,REPAIR_SHA);assert.equal(r.baseNativeReport.sha256,BASE_SHA);
  for(const key of ['nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted','shippingPackageProduced',
    'nativeMaterialPackagesIndependentlyReloaded','nativeMeshPackagesIndependentlyReloaded','nativeNormalTangentReadbackAvailable','originalExteriorOwnershipSpoofed'])assert.equal(r[key],false);
  for(const key of ['savedMapUnloadedReloaded','originalR16Unchanged','sourceInputsUnchanged','donorFilesNeverMutated'])assert.equal(r[key],true);
  assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});
  assert.equal(r.actualFullSceneHismComponents,2312);assert.equal(r.actualFullSceneHismInstances,676944);
  assert.equal(r.actualRecordedExteriorHismGroups,1987);assert.equal(r.actualRecordedExteriorHismInstances,632538);
  assert.equal(r.scopedMaterialGraphs,56);assert.equal(r.scopedTextureObjects,84);assert.equal(r.originalPlantMastersPreserved,135);assert.equal(r.originalPlantLodsPreserved,405);
  assert.equal(r.combinedAppearanceGoNoGo,'NO_GO_UNTIL_MATCHED_NATIVE_COMBINED_REVIEW');assert.equal(r.knownReviewLimits.length,2);
  assert.equal(r.moduleOrderWitness.cacheDeletedOrReplaced,false);assert.equal(r.moduleOrderWitness.cachePreservedAcrossReusedHelpers,true);
  assert.equal(r.moduleOrderWitness.sha256,'5f9eb8ccc2688b7d17200696cd3498558743c60fc541f8b1fbb0e80a3ba94b9e');
}

export function validateIntegratedContent(before,after,packages,delta,viewHash){
  assert.equal(Object.keys(before).length,3975);assert.equal(Object.keys(after).length,4049);assert.equal(packages.length,74);
  assert.equal(new Set(packages.map(r=>r.relativeContentPath)).size,74);
  const expected=structuredClone(before);
  for(const r of packages){assert(!Object.hasOwn(before,r.relativeContentPath));expected[r.relativeContentPath]={sha256:r.sha256,bytes:r.bytes};}
  assert.deepEqual(Object.keys(after).sort(),Object.keys(expected).sort());
  const changed=Object.keys(before).filter(k=>after[k].sha256!==before[k].sha256||after[k].bytes!==before[k].bytes).sort();
  assert.deepEqual(changed,['Brezi/Maps/Brezi.umap','Data/viewpoints.json']);assert.equal(after['Data/viewpoints.json'].sha256,viewHash);
  for(const [key,row]of Object.entries(expected))if(!changed.includes(key))assert.deepEqual(after[key],row,`Protected original/copied bytes differ: ${key}`);
  assert.deepEqual(delta,{changedOriginalFiles:changed,newPackageFiles:packages.map(r=>r.relativeContentPath).sort(),newUassetPackages:74,
    originalContentFileCount:3975,savedContentFileCount:4049,originalNativeAssetsByteIdentical:3973,removedOriginalFiles:[]});
}

export function validateIntegratedReportNames(names,name='realism-integration-native-report-r3.json'){
  assert(names.includes(name));
  assert(!names.some(n=>n==='exterior-import-report.json'||(n!==name&&/^realism-integration-native-report/.test(n))
    ||/neighbor-finish-overlay-report|canopy-transmission-native-report|meadow-visibility-native-report|foreground-overlay-report|curved-grass-native-report|roof-pbr-native-report/.test(n)),
    'Integrated candidate cannot contain a copied base/donor/previous report');
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source),name='realism-integration-native-report-r3.json';
  const previous=fileURLToPath(new URL('exterior-editor-source-r9.mjs',import.meta.url));assert.equal(await sha(previous),R9_SHA);
  if(!names.includes(name)){
    assert(!source.endsWith('/exterior-20261002-r22c')&&!names.some(n=>/^realism-integration-native-report/.test(n)),'Integrated candidate must have its own successful known R3 receipt');
    const evidence=await loadR9(source,{root});evidence.additionalClosureFiles.push(previous);return evidence;
  }
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r22c'));
  validateIntegratedReportNames(names,name);
  const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,name),r=await read(receiptPath),closure=new Set([receiptPath,previous]);
  validateIntegratedHeader(r,{source,project});assert.equal(await sha(receiptPath),REPORT_SHA);
  async function pinned(pin){
    assert(pin&&path.isAbsolute(pin.path)&&path.resolve(pin.path)===pin.path&&hashLike(pin.sha256)&&Number.isInteger(pin.bytes)&&pin.bytes>=0);
    const s=await fs.lstat(pin.path);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(s.size,pin.bytes);assert.equal(await sha(pin.path),pin.sha256);
    closure.add(pin.path);return pin.path;
  }
  const pj=async pin=>read(await pinned(pin));
  assert.equal(r.selectedPlan.path,path.join(root,'output/unreal/exterior-realism-integration-20261002-r22-study/realism-integration-plan.json'));
  assert.equal(r.repairSupplement.path,path.join(root,'output/unreal/exterior-realism-integration-20261002-r22-r3-supplement/realism-integration-material-lookup-repair.json'));
  const plan=await pj(r.selectedPlan),repair=await pj(r.repairSupplement),base=await pj(r.baseNativeReport);
  assert.equal(r.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261001-r16a/exterior-import-report.json'));
  assert.deepEqual(r.inputFiles,repair.inputFiles);assert.equal(Object.keys(r.inputFiles).length,424);
  assert.deepEqual(r.ownedSources,repair.ownedSources);assert.deepEqual(r.originalOwnedSources,plan.ownedSources);assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);
  for(const[file,h]of Object.entries(r.inputFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const key of ['beforeActorWitness','expectedActorWitness','savedActorWitness','materialsBefore','materialsSaved','originalGeometryAfter','diagnosticViewpoints'])await pinned(r[key]);
  const beforeContent=await pj(plan.baseContentInventory),contentInventory=await pj(r.afterContentInventory),projectProof=await pj(r.protectedProjectProof);
  const packages=await pj(plan.copiedPackages);assert.deepEqual(r.protectedProjectProof,plan.baseProjectProof);assert.equal(Object.keys(projectProof).length,132);
  for(const[relative,row]of Object.entries(projectProof))assert(!path.isAbsolute(relative)&&path.normalize(relative)===relative&&!relative.startsWith('../')
    &&(relative==='BreziTwin.uproject'||/^(Config|Source|Binaries)\//.test(relative))&&hashLike(row.sha256)&&Number.isInteger(row.bytes));
  validateIntegratedContent(beforeContent,contentInventory,packages,r.assetDelta,plan.diagnosticViewpoints.sha256);
  const clone=await pj(r.projectClone),copied=await pj(r.copiedPackageReceipt);
  assert.equal(r.projectClone.path,path.join(source,'realism-integration-project-clone.json'));assert.equal(r.copiedPackageReceipt.path,path.join(source,'realism-integration-package-copy.json'));
  assert.equal(clone.status,'verified-byte-identical-independent-apfs-r22c-project-clone-before-realism-integration-native-r3');
  assert.equal(copied.status,'verified-byte-identical-independent-apfs-saved-donor-packages-copied-neighbor-material-lookup-repair-r3');
  for(const value of [clone,copied]){
    assert.equal(value.schema,SCHEMA);assert.equal(value.repairSchema,REPAIR_SCHEMA);assert.equal(value.owner,'scripts/unreal/exterior-realism-integration-copy-r22-r3.py');
    assert.deepEqual(value.repairSupplement,r.repairSupplement);assert.deepEqual(value.selectedPlan,r.selectedPlan);assert.deepEqual(value.baseNativeReport,r.baseNativeReport);
    assert.equal(value.project,project);assert.equal(value.nativeExecuted,false);await pinned(value.originalBaseCloneProof);
  }
  assert.equal(clone.originalFileCount,4107);assert.equal(clone.newCopiedPackageCount,74);assert.equal(clone.contentFileCount,4049);
  assert.deepEqual(clone.packageCopyReceipt,r.copiedPackageReceipt);assert.equal(clone.originalFilesIndependentAndByteIdentical,true);assert.equal(clone.copiedPackagesIndependentAndByteIdentical,true);
  assert.equal(copied.sceneMapChanged,false);assert.equal(copied.viewpointsChanged,false);assert.equal(copied.copiedPackageCount,74);
  assert.deepEqual(copied.copiedPackages,packages.map(row=>({...row,destination:path.join(project,'Content',row.relativeContentPath),independentInodes:true})));
  for(const row of copied.copiedPackages){const[a,b]=await Promise.all([fs.stat(row.source),fs.stat(row.destination)]);assert(a.dev!==b.dev||a.ino!==b.ino);}
  const checker=path.join(root,'scripts/unreal/exterior-realism-integration-editor-check-r10.py');closure.add(checker);assert.equal(await sha(checker),CHECKER_SHA);
  const native=JSON.parse((await exec('python3',['-B',checker,receiptPath],{timeout:120000,maxBuffer:1024*1024})).stdout);
  const processPath=path.join(source,'realism-integration-native-r3.log.json'),processReceiptPath=path.join(source,'realism-integration-native-r3-process.json');
  const proc=await read(processPath),p=await read(processReceiptPath);
  assert.equal(p.processFile,processPath);assert.equal(p.processFileSha256,await sha(processPath));assert.equal(p.reportSha256,await sha(receiptPath));
  assert.equal(p.logFile,path.join(source,'realism-integration-native-r3.log'));assert.equal(p.logSha256,await sha(p.logFile));
  assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,r.nativeProcessId);assert(Number.isInteger(proc.pid)&&proc.pid>0);
  assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));
  assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+p.logFile])assert(proc.args.includes(arg));
  assert.equal(p.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(p.sourcePinsBeforeNative).length,430);
  assert.equal(p.controllerSha256BeforeNative,p.controllerSha256AfterNative);assert.equal(await sha(p.controller),p.controllerSha256BeforeNative);
  for(const[file,h]of Object.entries(p.sourcePinsBeforeNative)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const file of [processPath,processReceiptPath,p.logFile,p.controller])closure.add(file);
  const w=r.nativeModuleWitness,module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');
  assert.equal(w.source,path.join(root,'output/unreal/exterior-20261001-r16a/Project/BreziTwin/Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));
  assert.equal(w.destination,module);assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);
  const[a,b]=await Promise.all([fs.stat(w.source),fs.stat(module)]);assert(a.dev!==b.dev||a.ino!==b.ino);assert.equal(b.size,w.bytes);assert.equal(await sha(module),MODULE_SHA);closure.add(module);closure.add(w.source);
  const summary={mode:'saved-six-donor-exterior-realism-integration',nativeProcessId:proc.pid,...native,protectedProjectFiles:132,
    sourcePinsUnchangedAfterNative:430,scope:'Combined six-donor REVIEW candidate; R20 coverage regression and R23 roof seams remain open.'};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],
    nativeModuleWitness:w,moduleWitnessSource:r.repairSupplement,receiptSummary:{baseNativeReport:r.baseNativeReport,selectedPlan:r.selectedPlan,
      repairSupplement:r.repairSupplement,savedDonors:r.savedDonors,savedMapUnloadedReloaded:true,materialPackagesIndependentlyReloaded:false,
      meshPackagesIndependentlyReloaded:false,summary}};
}
