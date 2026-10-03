// Additive purposefully arranged R28 yards on the actual clean R27 native base.
// The runtime appearance pilot remains independent of saved/source acceptance.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR13,validateProjectClosure} from './exterior-editor-source-r13.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-context-yard-native-r28-r2.py';
const HELPER_SHA='9a884bfea89eaa88ed0cfc239b83207e9e57f5b5094c2873886903b943cd96d2';
const SCHEMA='brezi-context-yard-purposeful-ground-and-shrubs-r28-r2';
const SOURCE_SHA='f0f03736fc1c6d0992e2746626e35750dcacd575770b06f5f1308511a0358cb3';
const PREFLIGHT_SHA='3482b79d8060305004ed9132c6bd67549fce634295e1fe39dfd14d60c221399a';
const REPAIR_SHA='ba75c0022da1a5ad9294a05a68beb6d33de02c1207b663d9c51226ab7255889a';
const BASE_SHA='5575c0e37a9d48733b5c7ed3746f1731cc2b7958634a845c87b9700ff4fc9498';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
// Actual saved R2 process pins. Rendered appearance and performance remain open.
const REPORT_SHA='dfbca65515fc08aea52515195ab5ef752fe07cdca622cd41964e99875ced2456',CHECKER_SHA='319e3a03cf70172f8d8386172c188e7227a9f4ce2ac9e794cd3ede08893edf4b',R13_SHA='d136d45fc96276677d0feec3a8160b20b55d2b6ac560e7b8361ad45655b407f4',NATIVE_PID=71235,TERMINAL_PINS=308;
const exec=promisify(execFile),read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};

export function validateYardHeader(r,{source,project}){
  assert.equal(r.schema,SCHEMA);assert.equal(r.owner,OWNER);assert.equal(r.status,'verified-saved-purposeful-context-yards-overlay');
  assert.equal(r.output,source);assert.equal(r.project,project);assert.equal(r.sourceGeometryPlan.sha256,SOURCE_SHA);
  assert.equal(r.sourcePreflight.sha256,PREFLIGHT_SHA);assert.equal(r.nativeApiRepairSupplement.sha256,REPAIR_SHA);
  assert.equal(r.baseNativeReport.sha256,BASE_SHA);
  for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified',
    'materialPackagesIndependentlyUnloaded','nativeNormalTangentReadbackAvailable','landUseOrDoorObserved','measuredElevation'])assert.equal(r[k],false);
  for(const k of ['nativeApplied','savedMapUnloadedReloaded','originalSavedR27Unchanged','sourceInputsUnchanged',
    'allOriginalActorPoliciesAndTransformsPreserved','originalPlantAssetsBytePreserved',
    'staticMeshEditorSubsystemVerifiedAvailable','assetEditorSubsystemVerifiedAvailable'])assert.equal(r[k],true);
  assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});
  assert.equal(r.originalActorCount,5343);assert.equal(r.savedActorCount,5350);assert.equal(r.newGroundActors,4);
  assert.equal(r.newHismGroups,3);assert.equal(r.newShrubRoots,13);assert.equal(r.newPackageCount,9);
  assert.equal(r.scopedMaterialGraphs,56);assert.equal(r.scopedTextureObjects,77);assert.equal(r.newTextureObjects,0);
  assert.equal(r.originalGrassMembersPreserved,8949);assert.equal(r.savedReadback.fullHismComponents,2312);
  assert.equal(r.savedReadback.fullHismInstances,676957);assert.equal(r.savedReadback.fullActorCounterfactualValidated,true);
}

export function validateYardReportNames(names){
  const selected='context-yard-native-report-r2.json';assert(names.includes(selected));
  assert(!names.some(n=>n!==selected&&/(?:exterior-import|native-report|overlay-report).*\.json$/.test(n)),
    'A yard overlay cannot inherit an original/donor/failed native report');
}

export function validateYardContent(before,after,packages,delta){
  assert.equal(Object.keys(before).length,4034);assert.equal(Object.keys(after).length,4043);
  assert.equal(packages.length,9);assert.equal(new Set(packages).size,9);
  for(const file of packages)assert(/^Brezi\/ContextYard20261002R28\/.+\.uasset$/.test(file)&&!Object.hasOwn(before,file));
  assert.deepEqual(Object.keys(after).sort(),[...Object.keys(before),...packages].sort());
  assert.deepEqual(Object.keys(before).filter(k=>JSON.stringify(before[k])!==JSON.stringify(after[k])),['Brezi/Maps/Brezi.umap']);
  assert.deepEqual(delta,{changedOriginalFiles:['Brezi/Maps/Brezi.umap'],newPackageFiles:[...packages].sort(),
    originalContentFiles:4034,savedContentFiles:4043,newPackages:9});
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source),filename='context-yard-native-report-r2.json';
  const previous=fileURLToPath(new URL('exterior-editor-source-r13.mjs',import.meta.url));
  assert(hashLike(R13_SHA),'Frozen R13 source pin required');assert.equal(await sha(previous),R13_SHA);
  if(!names.includes(filename)){
    assert(!/^exterior-20261002-r28/.test(path.basename(source))&&!names.some(n=>/^context-yard-native-report/.test(n)),
      'Failed/running/unknown R28 cannot delegate to another native receipt');
    const evidence=await loadR13(source,{root});evidence.additionalClosureFiles.push(previous);return evidence;
  }
  assert(hashLike(REPORT_SHA)&&hashLike(CHECKER_SHA)&&Number.isInteger(NATIVE_PID)&&Number.isInteger(TERMINAL_PINS),
    'Known saved R28 success pins are required');
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r28b'));validateYardReportNames(names);
  const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,filename),r=await read(receiptPath),closure=new Set([receiptPath,previous]);
  validateYardHeader(r,{source,project});assert.equal(await sha(receiptPath),REPORT_SHA);assert.equal(r.nativeProcessId,NATIVE_PID);
  async function pinned(pin){
    assert(pin&&path.isAbsolute(pin.path)&&path.resolve(pin.path)===pin.path&&hashLike(pin.sha256)&&Number.isInteger(pin.bytes)&&pin.bytes>=0);
    const s=await fs.lstat(pin.path);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(s.size,pin.bytes);assert.equal(await sha(pin.path),pin.sha256);
    closure.add(pin.path);return pin.path;
  }
  const pj=async pin=>read(await pinned(pin));
  assert.equal(r.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261002-r27a/realism-clean-integration-native-report.json'));
  const e=await loadR13(path.dirname(r.baseNativeReport.path),{root});for(const file of e.additionalClosureFiles)closure.add(file);
  assert.equal(e.nativeReceiptPath,r.baseNativeReport.path);assert.equal(e.summary.savedActors,5343);
  await pinned(r.baseNativeReport);
  assert.equal(r.sourceGeometryPlan.path,path.join(root,'output/unreal/exterior-context-yard-20261002-r28-geometry-study/yard-geometry-plan.json'));await pinned(r.sourceGeometryPlan);
  assert.equal(r.sourcePreflight.path,path.join(root,'output/unreal/exterior-context-yard-20261002-r28-native-preflight-r2/source-preflight.json'));
  const preflight=await pj(r.sourcePreflight);assert.deepEqual(r.inputFiles,preflight.inputFiles);assert.equal(Object.keys(r.inputFiles).length,303);
  assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);
  assert.equal(r.nativeApiRepairSupplement.path,path.join(root,'output/unreal/exterior-context-yard-20261002-r28-native-api-repair-r2/api-repair-supplement.json'));
  const repair=await pj(r.nativeApiRepairSupplement);assert.deepEqual(r.commandletSubsystemAccessor,repair.accessor);
  for(const[file,h]of Object.entries(r.inputFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const key of ['beforeActorWitness','expectedActorWitness','savedActorWitness','nativeSourceFrameMeasurements','afterContentInventory'])await pinned(r[key]);
  const contentInventory=await pj(r.afterContentInventory);validateYardContent(e.contentInventory,contentInventory,r.newContentPackages,r.assetDelta);
  assert.deepEqual(r.baseContentInventory,JSON.parse(await fs.readFile(r.baseNativeReport.path,'utf8')).afterContentInventory);
  const baseReport=await read(r.baseNativeReport.path);assert.deepEqual(r.protectedProjectProof,baseReport.protectedProjectProof);
  const projectProof=await pj(r.protectedProjectProof);assert.deepEqual(projectProof,e.projectProof);assert.equal(Object.keys(projectProof).length,132);
  assert.equal(r.projectClone.path,path.join(source,'context-yard-project-clone.json'));const clone=await pj(r.projectClone);
  assert.equal(clone.status,'verified-byte-identical-independent-apfs-r28b-project-clone-before-context-yard-native-r2');
  assert.deepEqual(clone.baseNativeReport,r.baseNativeReport);assert.deepEqual(clone.selectedSourceGeometry,r.sourceGeometryPlan);
  assert.equal(clone.nativeExecuted,false);assert.equal(clone.nativeApiRepairPending,true);assert.equal(clone.selectedNativeApiRepair,null);
  assert.equal(clone.fileCount,4166);assert.equal(clone.files.length,4166);
  const originalFiles={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...projectProof},seen=new Set();
  for(const row of clone.files){
    const relative=path.relative(project,row.destination);assert(Object.hasOwn(originalFiles,relative)&&!seen.has(relative));seen.add(relative);
    assert.equal(row.source,path.join(e.project,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);
    assert.deepEqual({sha256:row.sha256,bytes:row.bytes},originalFiles[relative]);
    const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);
  }
  assert.equal(seen.size,Object.keys(originalFiles).length);
  const views=await read(path.join(project,'Content/Data/viewpoints.json')),baseViews=await read(path.join(e.project,'Content/Data/viewpoints.json'));
  assert.deepEqual(views,baseViews);for(const id of ['neighbor-finish-close-r18','exterior-parcels'])assert.equal(views.views.filter(v=>v.id===id).length,1);
  closure.add(path.join(e.project,'Content/Data/viewpoints.json'));
  const checker=path.join(root,'scripts/unreal/exterior-context-yard-editor-check-r16.py');assert.equal(await sha(checker),CHECKER_SHA);closure.add(checker);
  const native=JSON.parse((await exec('python3',['-B',checker,receiptPath],{timeout:120000,maxBuffer:1024*1024})).stdout);
  const processPath=path.join(source,'context-yard-native-r2.log.json'),terminalPath=path.join(source,'context-yard-native-r2-process.json');
  const proc=await read(processPath),terminal=await read(terminalPath);
  assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,NATIVE_PID);assert.equal(terminal.reportSha256,REPORT_SHA);
  assert.equal(terminal.processFile,processPath);assert.equal(terminal.processFileSha256,await sha(processPath));
  assert.equal(terminal.logFile,path.join(source,'context-yard-native-r2.log'));assert.equal(terminal.logSha256,await sha(terminal.logFile));
  assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));
  assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+terminal.logFile])assert(proc.args.includes(arg));
  assert.equal(terminal.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(terminal.sourcePinsBeforeNative).length,TERMINAL_PINS);
  assert.equal(terminal.controllerSha256BeforeNative,terminal.controllerSha256AfterNative);assert.equal(await sha(terminal.controller),terminal.controllerSha256BeforeNative);
  for(const[file,h]of Object.entries(terminal.sourcePinsBeforeNative)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const file of [processPath,terminalPath,terminal.logFile,terminal.controller])closure.add(file);
  const w=r.nativeModuleWitness,module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');
  assert.equal(w.source,path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.destination,module);
  assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);
  await pinned({path:module,sha256:MODULE_SHA,bytes:w.bytes});await pinned({path:w.source,sha256:MODULE_SHA,bytes:w.bytes});
  const summary={...native,protectedProjectFiles:132,sourcePinsUnchangedAfterNative:TERMINAL_PINS,
    scope:'Purposefully arranged source yards REVIEW candidate on clean R27. Appearance/performance/Shipping remain open.'};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:e.base,summary,contentInventory,projectProof,
    additionalClosureFiles:[...closure],nativeModuleWitness:w,moduleWitnessSource:r.projectClone,
    receiptSummary:{baseNativeReport:r.baseNativeReport,sourceGeometryPlan:r.sourceGeometryPlan,sourcePreflight:r.sourcePreflight,
      nativeApiRepairSupplement:r.nativeApiRepairSupplement,savedMapUnloadedReloaded:true,summary}};
}
