// Closed actual R25b repaired fern save; screenshot/appearance remain separate.
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
const OWNER='scripts/unreal/exterior-garden-fern-native-r25-r2.py';
const HELPER_SHA='010f7c38aeb0af81934c36b6bddbcd48f49b9bfc3703531833f2091c111d42a5';
const SOURCE_SHA='b3c1453765e310a47416507236c24adff2b3517b4bacd5a882fefa5c0df9709b';
const PREFLIGHT_SHA='726653cd4ab3b06df376e985a2edbd8d187bbaf96e06c72c745ed248ccbf0fb6';
const REPORT_SHA='dc96a4927a0b0ec0e8abb3740e7a918e65a6ba6a0881ba77bc29275c1445e0b2';
const BASE_SHA='999fc17ea7600136a2097aecefed3d846ff0d7e9baeb7f005480b113b60b1f40';
const R10_SHA='23652e2dd8969e57fa85c0e3cb935317cb452417964748fd66f4602720563756';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const CHECKER_SHA='af3d82d2df360819d777d025d72338c5bd834aa4c6a1139b65464b2f8ed71f07';
const SCHEMA='brezi-original-fern-own-garden-single-root-overlay-r25';
const PREFIX='Brezi/GardenFern20261002R25/';
const exec=promisify(execFile),read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};

export function validateFernHeader(r,{source,project}){
  assert.equal(r.schema,SCHEMA);assert.equal(r.owner,OWNER);assert.equal(r.status,'verified-saved-original-fern-single-own-garden-root');
  assert.equal(r.output,source);assert.equal(r.project,project);assert.equal(r.selectedSourcePlan.sha256,SOURCE_SHA);
  assert.equal(r.sourcePreflight.sha256,PREFLIGHT_SHA);assert.equal(r.baseNativeReport.sha256,BASE_SHA);
  for(const key of ['savedMapUnloadedReloaded','nativeApplied','originalSavedR22Unchanged','sourceInputsUnchanged','inheritedPlantAssetsBytePreserved'])assert.equal(r[key],true);
  for(const key of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified',
    'nativeNormalTangentReadbackAvailable','materialPackagesIndependentlyReloaded','nativeMeshPackagesIndependentlyReloaded','inheritedPlantNativeLodsRemeasuredHere'])assert.equal(r[key],false);
  assert.deepEqual(r.activeDesign,{variant:'C',livingLayout:'B',heatingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});
  assert.equal(r.actualFullActorCount,5346);assert.equal(r.actualFullHismComponents,2312);assert.equal(r.actualFullHismInstances,676944);
  assert.equal(r.changedOriginalRoot,1);assert.equal(r.newActors,0);assert.equal(r.newRoots,0);
  assert.equal(r.originalScopedMaterialGraphsPreserved,56);assert.equal(r.originalScopedTextureObjectsPreserved,84);
  assert.equal(r.newMaterialGraphs,1);assert.equal(r.newTextureObjects,4);assert.equal(r.totalScopedMaterialGraphs,57);assert.equal(r.totalScopedTextureObjects,88);
  assert.equal(r.changedComponent.groupId,'EX_ornamental_0_-1_garden_feather_r3_b_18000');
  assert.equal(r.savedRootReadback.rootId,'garden_ornamental_10');assert.equal(r.savedRootReadback.heightEquivalenceClaimed,false);
  assert.equal(r.savedRootReadback.originalNativeRootXYZExact,true);assert.equal(r.savedRootReadback.recoveredTransformAndStoredMatrixExactActualMeasuredBinary64,true);
  assert.equal(r.nativeMeshReadback.nativeNormalTangentReadbackAvailable,false);assert.equal(r.nativeMeshReadback.originalProviderLodChainPresent,false);
  assert.deepEqual(r.nativeMeshReadback.lodProofs.map(x=>[x.lod,x.triangles,x.orderedNativeFloat32PositionUvWindingVerified]),[[0,2384,true],[1,2384,true],[2,2384,true]]);
  assert.equal(new Set(r.nativeMeshReadback.lodProofs.map(x=>x.nativeCornerSha256)).size,1);
}
export function validateFernReportNames(names){
  const name='garden-fern-native-report-r2.json';assert(names.includes(name));
  assert(!names.some(n=>n==='exterior-import-report.json'||(n!==name&&/^garden-fern-native-report/.test(n))
    ||/^realism-integration-native-report/.test(n)),'Fern candidate cannot contain a copied base or prior fern report');
}
export function validateFernContent(before,after,packages,delta){
  assert.equal(Object.keys(before).length,4049);assert.equal(Object.keys(after).length,4058);
  assert.equal(packages.length,9);assert.equal(new Set(packages).size,9);assert(packages.every(p=>p.startsWith(PREFIX)&&p.endsWith('.uasset')));
  const added=Object.keys(after).filter(k=>!Object.hasOwn(before,k)).sort();assert.deepEqual(added,[...packages].sort());
  const changed=Object.keys(before).filter(k=>!after[k]||after[k].sha256!==before[k].sha256||after[k].bytes!==before[k].bytes).sort();
  assert.deepEqual(changed,['Brezi/Maps/Brezi.umap']);assert.deepEqual(after['Data/viewpoints.json'],before['Data/viewpoints.json']);
  assert.deepEqual(delta,{changedFiles:changed,newFiles:added,removedFiles:[],newUassetPackages:9,originalViewpointsByteIdentical:true,protectedOriginalContentFilesByteIdentical:4048});
}
export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source),name='garden-fern-native-report-r2.json';
  const previous=fileURLToPath(new URL('exterior-editor-source-r10.mjs',import.meta.url));assert.equal(await sha(previous),R10_SHA);
  if(!names.includes(name)){
    assert(!/\/exterior-20261002-r25[a-z](?:-|$)/.test(source)&&!names.some(n=>/^garden-fern-native-report/.test(n)),
      'Fern candidate must have actual known successful repaired receipt');
    const evidence=await loadR10(source,{root});evidence.additionalClosureFiles.push(previous);return evidence;
  }
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r25b'));validateFernReportNames(names);
  const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,name),r=await read(receiptPath),closure=new Set([receiptPath,previous]);
  validateFernHeader(r,{source,project});assert.equal(await sha(receiptPath),REPORT_SHA);
  async function pinned(pin){
    assert(pin&&path.isAbsolute(pin.path)&&path.resolve(pin.path)===pin.path&&hashLike(pin.sha256)&&Number.isInteger(pin.bytes)&&pin.bytes>=0);
    const stat=await fs.lstat(pin.path);assert(stat.isFile()&&!stat.isSymbolicLink());assert.equal(stat.size,pin.bytes);assert.equal(await sha(pin.path),pin.sha256);
    closure.add(pin.path);return pin.path;
  }
  const pj=async pin=>read(await pinned(pin));
  const plan=await pj(r.selectedSourcePlan),pf=await pj(r.sourcePreflight),base=await pj(r.baseNativeReport);
  assert.equal(r.selectedSourcePlan.path,path.join(root,'output/unreal/exterior-garden-fern-20261002-r25-study/fern-pilot-source-plan.json'));
  assert.equal(r.sourcePreflight.path,path.join(root,'output/unreal/exterior-garden-fern-20261002-r25-native-r2-repair-preflight/source-preflight.json'));
  assert.equal(r.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261002-r22c/realism-integration-native-report-r3.json'));
  assert.deepEqual(r.inputFiles,pf.inputFiles);assert.equal(Object.keys(r.inputFiles).length,560);assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);
  assert.deepEqual(r.windingRepair,pf.windingRepair);assert.equal(r.sourceGeometry.sha256,'8cbf4b0760a33db5fc979642b41386ea3aa9d9e6b192217d27fec07a08ad2592');
  for(const[file,h]of Object.entries(r.inputFiles)){const stat=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:stat.size});}
  for(const key of ['beforeActorWitness','expectedActorWitness','savedActorWitness','originalMaterialsBefore','originalMaterialsSaved','nativeScaleMeasurement','sourceGeometry','baseNativeProcess'])await pinned(r[key]);
  const beforeContent=await pj(base.afterContentInventory),contentInventory=await pj(r.afterContentInventory),projectProof=await pj(r.protectedProjectProof);
  assert.deepEqual(r.protectedProjectProof,base.protectedProjectProof);assert.equal(Object.keys(projectProof).length,132);
  for(const[relative,row]of Object.entries(projectProof))assert(!path.isAbsolute(relative)&&path.normalize(relative)===relative&&!relative.startsWith('../')
    &&(relative==='BreziTwin.uproject'||/^(Config|Source|Binaries)\//.test(relative))&&hashLike(row.sha256)&&Number.isInteger(row.bytes));
  const packages=[r.changedComponent.afterMesh,r.materialReport.asset,...Object.values(r.materialReport.textures).map(x=>x.asset),...r.importPipelineAssets]
    .map(p=>p.split('.')[0].replace(/^\/Game\//,'')+'.uasset');
  validateFernContent(beforeContent,contentInventory,packages,r.assetDelta);
  const clone=await pj(r.projectClone);assert.equal(r.projectClone.path,path.join(source,'garden-fern-project-clone.json'));
  assert.equal(clone.schema,SCHEMA);assert.equal(clone.status,'verified-byte-identical-independent-apfs-r25b-original-r22-project-clone-before-fern-native');
  assert.equal(clone.project,project);assert.equal(clone.sourceProject,base.project);assert.equal(clone.fileCount,4181);
  assert.equal(clone.contentFiles,4049);assert.equal(clone.protectedFiles,132);assert.equal(clone.nativeExecuted,false);assert.equal(clone.nativePreflightPending,true);
  assert.equal(clone.sourcePreflight,null);assert.deepEqual(clone.sourcePlan,r.selectedSourcePlan);assert.deepEqual(clone.nativeBaseReport,r.baseNativeReport);
  const expectedOriginal={...Object.fromEntries(Object.entries(beforeContent).map(([key,row])=>['Content/'+key,row])),...projectProof};
  assert.equal(clone.files.length,4181);const observed=new Set();
  for(const row of clone.files){
    const relative=path.relative(project,row.destination);assert(Object.hasOwn(expectedOriginal,relative)&&!observed.has(relative));observed.add(relative);
    assert.equal(row.source,path.join(base.project,relative));assert.deepEqual({sha256:row.sha256,bytes:row.bytes},expectedOriginal[relative]);assert.equal(row.independentInodes,true);
    const[a,b]=await Promise.all([fs.stat(row.source),fs.stat(row.destination)]);assert(a.dev!==b.dev||a.ino!==b.ino);
  }
  const checker=path.join(root,'scripts/unreal/exterior-garden-fern-editor-check-r11.py');closure.add(checker);assert.equal(await sha(checker),CHECKER_SHA);
  const native=JSON.parse((await exec('python3',['-B',checker,receiptPath],{timeout:120000,maxBuffer:1024*1024})).stdout);
  const rawPath=path.join(source,'garden-fern-native-r2.log.json'),terminalPath=path.join(source,'garden-fern-native-r2-process.json');
  const raw=await read(rawPath),terminal=await read(terminalPath);
  assert.equal(terminal.processFile,rawPath);assert.equal(terminal.processFileSha256,await sha(rawPath));assert.equal(terminal.reportSha256,REPORT_SHA);
  assert.equal(terminal.logFile,path.join(source,'garden-fern-native-r2.log'));assert.equal(terminal.logSha256,await sha(terminal.logFile));
  assert.equal(raw.code,0);assert.equal(raw.signal,null);assert.equal(raw.pid,r.nativeProcessId);assert.equal(raw.pid,60976);
  assert(Number.isFinite(Date.parse(raw.startedAt))&&Date.parse(raw.endedAt)>=Date.parse(raw.startedAt));
  assert.equal(raw.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(raw.args[0],path.join(project,'BreziTwin.uproject'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+terminal.logFile])assert(raw.args.includes(arg));
  assert.equal(terminal.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(terminal.sourcePinsBeforeNative).length,563);
  assert.equal(terminal.controllerSha256BeforeNative,terminal.controllerSha256AfterNative);assert.equal(await sha(terminal.controller),terminal.controllerSha256BeforeNative);
  for(const[file,h]of Object.entries(terminal.sourcePinsBeforeNative)){const stat=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:stat.size});}
  for(const file of [rawPath,terminalPath,terminal.logFile,terminal.controller])closure.add(file);
  const module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),w=clone.files.find(row=>row.destination===module);
  assert(w&&w.source===path.join(base.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);
  assert.equal(await sha(module),MODULE_SHA);await pinned({path:w.source,sha256:w.sha256,bytes:w.bytes});closure.add(module);
  const summary={mode:'saved-original-fern-single-own-garden-root',nativeProcessId:60976,...native,protectedProjectFiles:132,
    sourcePinsUnchangedAfterNative:563,scope:'One original Fern02 clump at unchanged own-garden root; smaller35.273cm shape; no appearance acceptance.'};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],
    nativeModuleWitness:w,moduleWitnessSource:r.projectClone,receiptSummary:{baseNativeReport:r.baseNativeReport,selectedSourcePlan:r.selectedSourcePlan,
      sourcePreflight:r.sourcePreflight,windingRepair:r.windingRepair,savedMapUnloadedReloaded:true,materialPackagesIndependentlyReloaded:false,
      meshPackagesIndependentlyReloaded:false,summary}};
}
