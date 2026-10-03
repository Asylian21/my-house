// Closed original-USD probe reader. No legacy exterior report dispatch.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';

const exec=promisify(execFile);
const SCHEMA='brezi-original-licensed-english-oak-postimport-scene-r6';
const STATUS='saved-original-whole-D-from-preserved-USD-packages-explicit-daylight-subset-probe-r6';
const NATIVE_OWNER='scripts/unreal/megaplants-english-oak-scene-native-r6.py';
const NATIVE_SHA='83c1cd9071e64a63c08d300a80dbfa6ae23ffad0ee9d895f79da24bfd9d4f667';
const PLAN_SHA='fcbae7cab8c5c10db4c36bf0affd9b9020363a14db5d6ea9b92ab750874841d8';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
// Deliberately closed until the actual root-owned native process succeeds.
const FINAL_REPORT_SHA='933739a45dad7d95babb3dfc77231b2126ed9c0f022f8dba9c00d01ffc1633e9';
const FINAL_NATIVE_PID=30697;
const FINAL_CHECKER_SHA='75bf23144de52e2ea6904da2f99bd84710275a638948cdc70463b65d65342df6';
export const OAK_MAP='/Game/Brezi/EnglishOakPilot20261002R3/Maps/EnglishOakPilotR6';
export const OAK_VIEW='english-oak-original-D-close-r6';
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const sha=async p=>{const h=createHash('sha256');for await(const b of createReadStream(p))h.update(b);return h.digest('hex');};
const relativeOwned=p=>typeof p==='string'&&p.length>0&&!path.isAbsolute(p)&&path.normalize(p)===p&&!p.startsWith('../');

async function filesBelow(directory){
  const files=[];
  for(const entry of await fs.readdir(directory,{withFileTypes:true})){
    const file=path.join(directory,entry.name);assert(!entry.isSymbolicLink(),'Unmeasured source symlink: '+file);
    if(entry.isDirectory())files.push(...await filesBelow(file));else if(entry.isFile())files.push(file);
  }
  return files.sort();
}

export function validateProjectClosure({project,contentInventory,projectProof,closure}){
  const content=path.join(project,'Content');
  const actual=Object.keys(closure).filter(p=>p.startsWith(content+path.sep)).sort();
  assert.deepEqual(actual,Object.keys(contentInventory).map(p=>path.join(content,p)).sort(),'Own saved Content file-set differs');
  for(const[p,row]of Object.entries(contentInventory)){
    assert(relativeOwned(p));assert.deepEqual(closure[path.join(content,p)],row,'Own saved Content bytes differ: '+p);
  }
  const protectedPaths=Object.keys(closure).filter(p=>p===path.join(project,'BreziTwin.uproject')||
    ['Config','Source','Binaries'].some(folder=>p.startsWith(path.join(project,folder)+path.sep))).sort();
  assert.deepEqual(protectedPaths,Object.keys(projectProof).map(p=>path.join(project,p)).sort(),'Protected file-set differs');
  for(const[p,row]of Object.entries(projectProof)){
    assert(relativeOwned(p)&&(p==='BreziTwin.uproject'||/^(Config|Source|Binaries)\//.test(p)));
    assert.deepEqual(closure[path.join(project,p)],row,'Protected bytes differ: '+p);
  }
}

export function validateOakHeader(report,{source,root,names}){
  assert(FINAL_REPORT_SHA&&FINAL_NATIVE_PID&&FINAL_CHECKER_SHA,'Oak actual native success/checker binding is pending');
  assert.equal(source,path.join(root,'output/unreal/megaplants-english-oak-native-20261002-r3'));
  assert.equal(report.schema,SCHEMA);assert.equal(report.owner,NATIVE_OWNER);assert.equal(report.status,STATUS);
  assert.equal(report.nativeProcessId,FINAL_NATIVE_PID);assert.equal(report.project,path.join(source,'Project/BreziTwin'));
  assert.equal(report.map,OAK_MAP);assert.equal(report.selectedPlan.sha256,PLAN_SHA);
  assert(!names.some(n=>n==='exterior-import-report.json'||/^oak-usd-native-pilot-report/.test(n)||
    (/^oak-usd-scene-native-report/.test(n)&&!['oak-usd-scene-native-report-r4.json','oak-usd-scene-native-report-r5.json','oak-usd-scene-native-report-r6.json'].includes(n))),
    'Only selected R6 and its exact pinned R4/R5 failure histories may coexist');
  for(const k of ['nativeApplied','probeMapUnloadedReloaded','originalMainMapUnchanged','originalSavedR32ProjectUnchanged',
    'all39SavedOriginalUsdPackagesByteExact','exactMeasuredSetterAndReloadedLightingSubsetVerified','explicitObservedLightingSubsetCopiedAndReloaded'])assert.equal(report[k],true);
  for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified',
    'windSidecarImported','dynamicWindEvaluated','nativeFullGeometryCornerReadbackAvailable','importedNormalsTangentsPreserved',
    'actualNaniteGpuPassAttributedToTree','assetImportExecuted','walkingCollisionAccepted','matchedExteriorLightingPairClaimed',
    'fullLightingPropertyCloneClaimed','daylightCopiedByNativeActorDuplication','numericalToleranceApplied'])assert.equal(report[k],false);
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);
  const filename='oak-usd-scene-native-report-r6.json',reportPath=path.join(source,filename);
  const names=await fs.readdir(source),report=await read(reportPath);
  validateOakHeader(report,{source,root,names});assert.equal(await sha(reportPath),FINAL_REPORT_SHA);
  const closure=new Set([reportPath]);
  async function pinned(row){
    assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&/^[a-f0-9]{64}$/.test(row.sha256)
      &&Number.isInteger(row.bytes)&&row.bytes>=0,'Exact absolute regular file pin required');
    const s=await fs.lstat(row.path);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(s.size,row.bytes);assert.equal(await sha(row.path),row.sha256);
    closure.add(row.path);return row.path;
  }
  async function collector(value){
    if(Array.isArray(value)){for(const row of value)await collector(row);return;}
    if(value&&typeof value==='object'){
      if(typeof value.path==='string'&&typeof value.sha256==='string')await pinned(value);
      for(const[k,v]of Object.entries(value)){
        if(path.isAbsolute(k)&&typeof v==='string'&&/^[a-f0-9]{64}$/.test(v)){const s=await fs.lstat(k);await pinned({path:k,sha256:v,bytes:s.size});}
        await collector(v);
      }
    }
  }
  await collector(report);
  const rootAuditPath=path.join(source,'root-native-scene-success-byte-audit-r6-r1.json');
  const rootAudit=await read(await pinned({path:rootAuditPath,
    sha256:'1846bb514c8e78619df80f6e361646bab391f78783efce3a0cc7f9aa91efb92c',bytes:2152}));
  assert.equal(rootAudit.schema,'brezi-original-oak-r6-scene-success-byte-audit-root-r1');
  assert.equal(rootAudit.nativeReport.sha256,FINAL_REPORT_SHA);assert.equal(rootAudit.currentProjectFileCount,4261);
  for(const key of ['all4259OriginalOwnFilesExceptExactCameraAppendExact','all4218OriginalR32SourceFilesExact',
    'all39SavedOriginalUsdPackagesExact','failedR4R5MapsExact','originalMainMapExact',
    'cameraOriginalPrefixAndExactOneAppendVerified','savedLightingSubsetReferenceClosureAndZeroDifferenceVerified'])assert.equal(rootAudit[key],true);
  assert.equal(rootAudit.sourcePinsBeforeAndAfterExact,176);assert.deepEqual(rootAudit.projectDelta,report.projectDelta);
  assert.equal(rootAudit.newNativeActorOrMeshGeometryDecodeByThisCpuAudit,false);await collector(rootAudit);

  const plan=await read(await pinned(report.selectedPlan));assert.equal(plan.owner,'scripts/unreal/megaplants-english-oak-scene-study-r6.py');
  assert.equal(plan.schema,SCHEMA);assert.equal(plan.assetImportExecuted,false);assert.equal(plan.numericalToleranceApplied,false);for(const row of plan.inputFiles)await pinned(row);
  const originalR32Inventory=await read(await pinned(plan.originalSavedR32Inventory));
  const sourceProject=path.join(root,'output/unreal/exterior-20261002-r32a/Project/BreziTwin');
  assert.equal(Object.keys(originalR32Inventory).length,4218);
  const sourceFileSet=[path.join(sourceProject,'BreziTwin.uproject'),
    ...(await Promise.all(['Content','Config','Source','Binaries'].map(folder=>filesBelow(path.join(sourceProject,folder))))).flat()].sort();
  assert.deepEqual(sourceFileSet,Object.keys(originalR32Inventory).map(relative=>path.join(sourceProject,relative)).sort(),
    'Original R32 source file-set changed');
  for(const[relative,row]of Object.entries(originalR32Inventory)){
    assert(relativeOwned(relative));closure.add(path.join(sourceProject,relative));
    await pinned({path:path.join(sourceProject,relative),...row});
  }
  const nativePath=path.join(root,NATIVE_OWNER);assert.equal(await sha(nativePath),NATIVE_SHA);closure.add(nativePath);
  const checker=fileURLToPath(new URL('./megaplants-english-oak-editor-check-r6.py',import.meta.url));
  assert.equal(await sha(checker),FINAL_CHECKER_SHA);closure.add(checker);
  const {stdout}=await exec('/usr/bin/python3',['-B',checker,reportPath],{cwd:root,maxBuffer:1024*1024});
  const summary=JSON.parse(stdout);assert.equal(summary.nativeProcessId,FINAL_NATIVE_PID);assert.equal(summary.map,OAK_MAP);
  const preparation=await read(await pinned(report.projectPreparation));
  const clone=await read(await pinned(report.initialRootClone));
  assert.equal(clone.status,'verified-original-r32-independent-apfs-clone-before-english-oak-usd-pilot');
  assert.equal(clone.fileCount,4218);assert.equal(clone.project,report.project);assert.equal(clone.nativeExecuted,false);
  assert.equal(clone.selectedPlan,null);assert.equal(clone.pluginEnablementPending,true);
  for(const row of clone.files){
    const relative=path.relative(report.project,row.destination);assert(relativeOwned(relative));
    assert.equal(row.source,path.join(clone.sourceProject,relative));assert.equal(row.independentInodes,true);
    const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);
  }
  const rawPath=path.join(source,'oak-usd-scene-native-r6.log.json'),terminalPath=path.join(source,'oak-usd-scene-native-r6-process.json');
  const raw=await read(rawPath),terminal=await read(terminalPath);closure.add(rawPath);closure.add(terminalPath);
  assert.equal(raw.code,0);assert.equal(raw.signal,null);assert.equal(raw.pid,FINAL_NATIVE_PID);
  assert.equal(path.basename(raw.command),'UnrealEditor-Cmd');assert.equal(raw.args[0],path.join(report.project,'BreziTwin.uproject'));
  assert(raw.args.includes('-nullrhi')&&raw.args.includes('-run=pythonscript')&&raw.args.includes('-script='+nativePath));
  assert.equal(terminal.processFile,rawPath);assert.equal(terminal.processFileSha256,await sha(rawPath));
  assert.equal(terminal.logFile,path.join(source,'oak-usd-scene-native-r6.log'));assert.equal(terminal.logSha256,await sha(terminal.logFile));
  assert.equal(terminal.reportSha256,FINAL_REPORT_SHA);assert.equal(terminal.sourcePinsUnchangedAfterNative,true);
  assert.equal(terminal.controllerSha256BeforeNative,terminal.controllerSha256AfterNative);
  closure.add(terminal.logFile);await collector(terminal);
  assert.equal(terminal.diskGuard.nativeScratchCapEnforced,false);assert.equal(terminal.diskGuard.globalSpaceLossAttributedSolelyToPilot,false);
  const nativeLog=await fs.readFile(terminal.logFile,'utf8');
  assert(!nativeLog.includes('Failed to build Nanite Assembly')&&!nativeLog.includes('zero joint bindings'),
    'Original native assembly build failure must remain a failure');
  const crashAudit=await read(await pinned(report.crashedImportByteAudit));
  const originalImportLog=await fs.readFile(await pinned(crashAudit.nativeLog),'utf8');
  assert(!originalImportLog.includes('Failed to build Nanite Assembly'),'Original assembly build failure cannot be accepted');
  const importWarnings=report.observedOriginalImportWarnings;
  assert(importWarnings.every(line=>originalImportLog.includes(line)),'Original import warnings must remain bound to the actual R3 log');
  const project=report.project;
  const contentInventory=Object.fromEntries(Object.entries(report.afterInventory).filter(([p])=>p.startsWith('Content/')).map(([p,v])=>[p.slice(8),v]));
  const projectProof=Object.fromEntries(Object.entries(report.afterInventory).filter(([p])=>p==='BreziTwin.uproject'||/^(Config|Source|Binaries)\//.test(p)));
  assert.equal(Object.keys(projectProof).length,132);assert.equal(Object.keys(contentInventory).length,4129);assert.deepEqual(projectProof['BreziTwin.uproject'],
    {sha256:preparation.descriptorAfter.sha256,bytes:preparation.descriptorAfter.bytes});
  assert.deepEqual(projectProof['Config/DefaultEngine.ini'],
    {sha256:preparation.startupConfigAfter.sha256,bytes:preparation.startupConfigAfter.bytes});
  assert.deepEqual(report.nativeStartupReadback,{'r.Nanite.AllowAssemblies':1,'r.Nanite.Foliage':0});
  assert.equal(preparation.status,'verified-own-usd-plugin-and-startup-assembly-only-stage-native-pending-r3');
  const originalPlan=await read(await pinned(report.originalSourcePlan));
  assert.equal(originalPlan.sourceRevision,3);await collector(originalPlan);
  assert.deepEqual(preparation.startupConfigDelta,originalPlan.startupConfigDelta);
  const module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');
  const nativeModuleWitness=clone.files.find(r=>r.destination===module);assert(nativeModuleWitness&&nativeModuleWitness.sha256===MODULE_SHA);
  const originalDescriptor=await read(preparation.descriptorBefore.path),ownDescriptor=await read(preparation.descriptorAfter.path);
  assert.deepEqual(ownDescriptor,{...originalDescriptor,Plugins:[...originalDescriptor.Plugins,originalPlan.pluginAddition]});
  const views=await read(path.join(project,'Content/Data/viewpoints.json'));assert.deepEqual(views.views.at(-1),plan.camera);
  return {mode:summary.mode,project,map:OAK_MAP,nativeReceiptPath:reportPath,base:report,summary,
    contentInventory,projectProof,originalSourceProject:sourceProject,additionalClosureFiles:[...closure],nativeModuleWitness,moduleWitnessSource:report.initialRootClone,
    allowedViews:[OAK_VIEW],receiptSummary:{selectedPlan:report.selectedPlan,baseNativeReport:report.baseNativeReport,
      separateProbeMap:OAK_MAP,originalMainMapUnchanged:true,originalConstantMaterialsPreserved:true,
      nativeStartupReadback:report.nativeStartupReadback,editorRuntimeAssemblyCvarReadbackAvailable:false,
      explicitObservedLightingSubsetCopiedAndReloaded:true,fullLightingPropertyCloneClaimed:false,
      exactMeasuredSetterAndReloadedLightingSubsetVerified:true,numericalToleranceApplied:false,
      sourceGeometryOriginal:true,importedNormalsTangentsPreserved:false,nativeFullCornerProof:false,
      nativeImportWarnings:importWarnings,walkingAuditAvailable:false,summary}};
}
