// Closed saved R38-r2 direct consumer. Native material readback remains separate from appearance.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR28,validateProjectClosure} from './exterior-editor-source-r28.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-context-yard-soft-coherence-native-r38-r2.py';
const SCHEMA='brezi-image-selected-fixed-world-soft-ground-material-overlay-r38';
const REPAIR='brezi-r38-visible-grayscale-texture-reflection-repair-r2';
const REPORT_NAME='soft-ground-native-report-r2.json';
const REPORT_SHA='077e36066dc49f2c3fa379893c39fc5659e8261385030d86266316e1bde9f2b9';
const PLAN_SHA='a7159a67452296998d3323011bd45095141c0e296907a276876b7f40012cf092';
const PF_SHA='c8827357e8455dd030fa35c0613bd8da7c0ff83dbc0052a93016fb44f74b2ecf';
const HELPER_SHA='e8bd757c0958f4245c4d2c2d7bbd577643b15150333ef5074047bb769f631998';
const BASE_SHA='f589c0d813ccfc35eba928a91a4545e03b159622fffa7ae2ba247545053c4532';
const R28_SHA='71d2a5d20b60f2be5e600617c51c4c6a6e823f7437fcd64e8379c01295d29123';
const AUDIT_SHA='a30063dc99bd3fa3fcd7d202aa77209b74f36c06bde77a47fba1c071564c5edb';
const PROCESS_SHA='c5fb163aa2989503b842d17dd464ec5baae88f881a3f543207101a7f640fa3e5';
const RAW_SHA='551dfc7c8b08d7374f23ade64ab73ce7b71ed61798bffaab21889588db77c4f1';
const MONITOR_SHA='32dd2661ec78718eef9e5503a1c411b565f6542400778a7b13c67fa8c93ab820';
const CLONE_SHA='a3710cf4d5b680454b9a8d770354fcea98818de461ee01c8ed1dc6c219a94910';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const CHECKER_SHA='75a39cdaa649efdf3696b5e4ddfa9b381c3a3788c097949519e24d2e460b0e11';
const NATIVE_PID=72504,SOURCE_PINS=1039,TERMINAL_PINS=1048;
export const COUNTS=Object.freeze({savedActors:5364,fullHismComponents:2325,fullHismInstances:678197,
  scopedMaterialGraphs:66,scopedTextureObjects:97,contentFiles:4103,protectedFiles:132,newPackages:3});
const prefix='/Game/Brezi/ContextYardSoftCoherence20261002R38';
export const materialAssets={backdrop:prefix+'/Materials/M_backdrop_soft_r38.M_backdrop_soft_r38',substrate:prefix+'/Materials/M_substrate_soft_r38.M_substrate_soft_r38'};
export const permissionAsset=prefix+'/Textures/T_soft_permission_r38.T_soft_permission_r38';
export const newAssets=[...Object.values(materialAssets),permissionAsset].sort();
export const actor197='/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.StaticMeshActor_197';
export const donor668='/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.StaticMeshActor_668';
const read=async p=>JSON.parse(await fs.readFile(p,'utf8')),exec=promisify(execFile);
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async p=>{const h=createHash('sha256');for await(const b of createReadStream(p))h.update(b);return h.digest('hex');};
const packagePath=a=>a.slice(6).split('.')[0]+'.uasset';

export function validateSoftGroundReportNames(names){
  assert(names.includes(REPORT_NAME));
  assert(!names.some(n=>n!==REPORT_NAME&&/(?:exterior-import|native-report|overlay-report).*\.json$/.test(n)),
    'Saved R38 cannot inherit failed, foreign or legacy native reports');
}
export function validateSoftGroundHeader(r,{source,root,nativePid=NATIVE_PID}){
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r38b'));
  assert.equal(r.schema,SCHEMA);assert.equal(r.schemaVersion,2);assert.equal(r.owner,OWNER);assert.equal(r.repairSchema,REPAIR);
  assert.equal(r.status,'verified-saved-image-selected-fixed-world-soft-ground-material-overlay');
  assert.equal(r.output,source);assert.equal(r.project,path.join(source,'Project/BreziTwin'));assert.equal(r.nativeProcessId,nativePid);
  assert.deepEqual(r.actualCounts,COUNTS);assert.equal(r.baseNativeReport.sha256,BASE_SHA);
  for(const[k,h]of Object.entries({selectedPlan:PLAN_SHA,sourcePreflight:PF_SHA,projectClone:CLONE_SHA}))assert.equal(r[k].sha256,h);
  assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});
  assert.deepEqual(r.newPackages,newAssets);assert.equal(r.newActors,0);assert.equal(r.newMeshes,0);
  for(const k of ['nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged','allOriginalRawMatricesMainSeedsCustomDataExact',
    'nativeMaskPropertyPolicyVerified','original64MaterialGraphsAndAuxExact','original96TextureSettingsAndPackagesExact'])assert.equal(r[k],true);
  for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified',
    'activeOutputPromoted','nativeGpuOutsideEquivalenceVerified','nativeGpuPixelFormatVerified','nativeTexelsDecoded',
    'freshNativeGeometryAttributeReadback','nativeNormalTangentReadbackAvailable','originalGeometryAndRootMutationApisCalled',
    'sourcePhotoPixelsEdited','additionalSeedRangesPreservationClaimed'])assert.equal(r[k],false);
}
export function counterfactualTwoSlots(before,targets,base){
  assert.deepEqual(Object.keys(targets).sort(),['backdrop','substrate']);assert.equal(targets.backdrop.actor,actor197);
  assert.equal(targets.substrate.actor,base.newActorMapping[donor668]);assert.equal(targets.substrate.actor,donor668);
  assert.notEqual(targets.substrate.actor,actor197);const expected=structuredClone(before);
  for(const role of ['backdrop','substrate']){const t=targets[role];assert.deepEqual(Object.keys(t).sort(),['actor','component','originalMaterial','originalMesh']);
    const rows=expected[t.actor]?.components.filter(c=>c.name===t.component);assert.equal(rows?.length,1);const c=rows[0];
    assert.equal(c.class,'/Script/Engine.StaticMeshComponent');assert.equal(c.mesh,t.originalMesh);assert.equal(c.materials[0],t.originalMaterial);
    assert(Array.isArray(c.overrideMaterials));c.materials[0]=materialAssets[role];
    if(c.overrideMaterials.length)c.overrideMaterials[0]=materialAssets[role];else c.overrideMaterials=[materialAssets[role]];
  }return expected;
}
export function validateSoftGroundContent(before,after,delta){
  assert.equal(Object.keys(before).length,4100);assert.equal(Object.keys(after).length,4103);const added=newAssets.map(packagePath).sort();
  assert.deepEqual(Object.keys(after).sort(),[...Object.keys(before),...added].sort());
  assert(added.every(k=>!Object.hasOwn(before,k)));assert.deepEqual(Object.keys(before).filter(k=>{try{assert.deepEqual(before[k],after[k]);return false;}catch{return true;}}),['Brezi/Maps/Brezi.umap']);
  assert.deepEqual(delta,{newPackages:3,newRelativeContentFiles:added,onlyOriginalMapChanged:true});
}
export function validateSoftGroundRootAudit(a,r,{reportPin,processPin,rawPin}){
  assert.equal(a.schema,'brezi-root-r38-current-byte-and-stored-native-evidence-audit');assert.equal(a.schemaVersion,2);
  assert.equal(a.status,'verified-current-r38-bytes-and-stored-native-two-slot-counterfactual');assert.equal(a.nativeProcessId,NATIVE_PID);
  assert.deepEqual(a.nativeReport,reportPin);assert.deepEqual(a.nativeProcess,processPin);assert.deepEqual(a.rawNativeProcess,rawPin);
  for(const k of ['projectClone','baseNativeReport','selectedPlan','sourcePreflight','selectedRootImageDecision','repairEvidence','repairSchema','assetDelta','savedActorWitnessSha256'])assert.deepEqual(a[k],r[k]);
  for(const[k,v]of Object.entries({currentProjectFiles:4235,currentContentFiles:4103,protectedFiles:132,newPackages:3,sourceReceiptPins:SOURCE_PINS,
    terminalRootSourcePins:TERMINAL_PINS,unchangedOriginalBaseContentFiles:4100,unchangedOriginalBaseProtectedFiles:132}))assert.equal(a[k],v);
  for(const k of ['allSourceAndTerminalPinsCurrentExact','fullStoredCounterfactualIndependentlyReconstructed','all2325RawControls678197MembersBeforeAndSavedExact',
    'all64OriginalGraphsAuxUsage96TexturesExact','actualCompiled70And73GraphsNativeMaskPropertyPolicyValidated'])assert.equal(a[k],true);
  for(const k of ['freshNativeActorOrAttributeDecodeExecuted','nativeTexelsDecoded','nativeGpuOutsideEquivalenceVerified','nativeGpuPixelFormatVerified',
    'nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified','activeOutputPromoted'])assert.equal(a[k],false);
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source);
  const previous=fileURLToPath(new URL('exterior-editor-source-r28.mjs',import.meta.url));assert.equal(await sha(previous),R28_SHA);
  if(!names.includes(REPORT_NAME)){
    assert(!/^exterior-20261002-r38/.test(path.basename(source))&&!names.some(n=>/^soft-ground-native-report/.test(n)),
      'Pending, failed or unknown R38 cannot delegate to an older family');
    const e=await loadR28(source,{root});e.additionalClosureFiles.push(previous);return e;
  }
  assert(hashLike(CHECKER_SHA),'Final actual saved checker pin is required');validateSoftGroundReportNames(names);
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r38b'));
  const receiptPath=path.join(source,REPORT_NAME),r=await read(receiptPath),project=path.join(source,'Project/BreziTwin'),closure=new Set([previous]);
  validateSoftGroundHeader(r,{source,root});assert.equal(await sha(receiptPath),REPORT_SHA);
  async function pinned(row){assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);
    const s=await fs.lstat(row.path);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(s.size,row.bytes);assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;}
  const pj=async row=>read(await pinned(row));
  const ownPin=async(p,h)=>{const row={path:p,sha256:h,bytes:(await fs.stat(p)).size};await pinned(row);return row;};
  const reportPin=await ownPin(receiptPath,REPORT_SHA);
  assert.equal(r.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261002-r37b/garden-yard-integration-native-report-r2.json'));
  const e=await loadR28(path.dirname(r.baseNativeReport.path),{root});assert.equal(e.nativeReceiptPath,r.baseNativeReport.path);assert.equal(e.summary.savedActors,5364);
  for(const file of e.additionalClosureFiles)closure.add(file);const base=await pj(r.baseNativeReport);
  assert.equal(r.selectedPlan.path,path.join(root,'output/unreal/exterior-context-yard-soft-coherence-20261002-r38-native-study-r2/soft-ground-native-plan-r2.json'));
  const plan=await pj(r.selectedPlan),pf=await pj(r.sourcePreflight);
  for(const q of [plan,pf]){assert.equal(q.schema,SCHEMA);assert.equal(q.schemaVersion,2);assert.equal(q.owner,OWNER);assert.equal(q.repairSchema,REPAIR);assert.equal(q.nativeExecuted,false);}
  assert.equal(plan.status,'image-selected-soft-ground-source-validated-native-pending');assert.equal(pf.status,'image-selected-soft-ground-source-preflight-validated-native-pending');
  assert.deepEqual(pf.selectedPlan,r.selectedPlan);assert.deepEqual(pf.cpuTests,plan.cpuTests);assert.equal(pf.cpuTests.exitCode,0);assert.equal(pf.cpuTests.expectedCases,20);await pinned(pf.cpuTests.log);
  for(const k of ['binding','inputFiles','moduleOrderWitness'])assert.deepEqual(pf[k],r[k]);assert.equal(Object.keys(r.inputFiles).length,SOURCE_PINS);assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);
  for(const k of ['binding','repairEvidence','sourceStudy','projectClone','baseNativeReport','baseNativeProcess','baseCurrentByteAudit','selectedRootImageDecision'])assert.deepEqual(plan[k],r[k]);
  for(const k of ['baseNativeProcess','baseCurrentByteAudit','selectedRootImageDecision','sourceStudy'])await pinned(r[k]);
  for(const[file,h]of Object.entries(r.inputFiles))await ownPin(file,h);
  for(const pair of Object.values(plan.ownedSources)){assert.deepEqual(pair.live.sha256,pair.snapshot.sha256);await pinned(pair.live);await pinned(pair.snapshot);}
  await pinned(plan.nativeMaterialGraphs);await pinned(plan.nativeSamplingSupplement);for(const row of plan.primaryApiFiles)await pinned(row);
  const evidence=r.repairEvidence;assert.equal(evidence.actualFailureProcessId,66232);assert.equal(evidence.actualReflectionProbeProcessId,67918);
  assert.equal(evidence.runtimeGetterAvailabilityVerified,true);assert.equal(evidence.runtimeSetterAvailabilityVerified,false);
  for(const k of ['failedNativeReport','failedNativeProcess','failureByteAudit','readOnlyReflectionProbe','reflectionProbeProcess'])await pinned(evidence[k]);
  const failed=await pj(evidence.failedNativeReport),probe=await pj(evidence.readOnlyReflectionProbe);
  assert.equal(failed.nativeApplied,false);assert.equal(failed.nativeProcessId,66232);assert.equal(probe.nativeProcessId,67918);
  const before=await pj(r.beforeActorWitness),declared=await pj(r.expectedActorWitness),saved=await pj(r.savedActorWitness);
  assert.deepEqual(before,await pj(base.savedActorWitness));assert.equal(Object.keys(before).length,5364);
  const expected=counterfactualTwoSlots(before,plan.targets,base);assert.deepEqual(declared,expected);assert.deepEqual(saved,expected);
  assert.equal(r.expectedActorWitnessSha256,r.savedActorWitnessSha256);assert.equal(r.savedActorWitnessSha256,plan.expectedActorWitnessSha256);
  for(const[a,b]of [['rawInstanceControlsBefore','rawInstanceControlsSaved'],['originalMaterialWitnessBefore','originalMaterialWitnessSaved'],['originalTextureWitnessBefore','originalTextureWitnessSaved']])assert.deepEqual(await pj(r[a]),await pj(r[b]));
  for(const phase of ['before','saved']){assert.equal(r.materialGraphDiagnosticFiles[phase].length,64);for(const row of r.materialGraphDiagnosticFiles[phase])await pinned(row);}
  const built=await pj(r.newMaterialReport);assert.deepEqual(built,r.newMaterials);assert.deepEqual(built.nativeGraphAdaptation,plan.nativeGraphAdaptation);
  assert.deepEqual(built.newPackageAssets,newAssets);assert.deepEqual(built.samplingPolicy,plan.samplingPolicy);
  assert.equal(built.reflectionPreflight.textureFieldCount,24);assert.equal(built.reflectionPreflight.hiddenCompressionNonePropertyAccessed,false);
  assert(!Object.hasOwn(built.maskTexture.values,'compression_none'));assert.equal(built.samplingPolicy.maskSamplerType,'SAMPLERTYPE_LINEAR_GRAYSCALE');
  assert.equal(built.samplingPolicy.compressionSettings,'TC_GRAYSCALE');assert.equal(built.samplingPolicy.maskMipValueMode,'TMVM_NONE');
  assert.equal(built.nativeGpuPixelFormatVerified,false);assert.equal(built.nativeTexelsDecoded,false);
  for(const role of ['backdrop','substrate']){assert.equal(built.materials[role].graph.nodes.length,role==='backdrop'?70:73);assert.equal(built.materials[role].asset,materialAssets[role]);}
  const contentInventory=await pj(r.afterContentInventory);validateSoftGroundContent(e.contentInventory,contentInventory,r.assetDelta);
  assert.deepEqual(r.baseContentInventory,base.afterContentInventory);await pinned(r.baseContentInventory);
  assert.deepEqual(r.protectedProjectProof,base.protectedProjectProof);const projectProof=await pj(r.protectedProjectProof);assert.deepEqual(projectProof,e.projectProof);
  assert.equal(r.projectClone.path,path.join(source,'soft-ground-project-clone-r38.json'));const clone=await pj(r.projectClone);
  assert.equal(clone.schema,'brezi-image-selected-saved-r37b-soft-ground-project-clone-r38');assert.equal(clone.schemaVersion,2);
  assert.equal(clone.status,'verified-byte-identical-independent-apfs-image-selected-r37b-before-scoped-soft-ground-native-repair-r38');
  assert.equal(clone.project,project);assert.equal(clone.sourceProject,e.project);assert.equal(clone.fileCount,4232);assert.equal(clone.contentFiles,4100);assert.equal(clone.protectedFiles,132);assert.equal(clone.nativeExecuted,false);
  assert.deepEqual(clone.sourceNativeReport,r.baseNativeReport);assert.deepEqual(clone.sourceNativeProcess,r.baseNativeProcess);assert.deepEqual(clone.sourceCurrentByteAudit,r.baseCurrentByteAudit);
  assert.deepEqual(clone.sourceStudy,r.sourceStudy);assert.deepEqual(clone.rootImageBaseSelection,r.selectedRootImageDecision);
  const original={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...projectProof},seen=new Set();assert.equal(clone.files.length,4232);
  for(const row of clone.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(original,relative)&&!seen.has(relative));seen.add(relative);
    assert.equal(row.source,path.join(e.project,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);assert.deepEqual({sha256:row.sha256,bytes:row.bytes},original[relative]);
    const[s,d]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(d.isFile()&&!d.isSymbolicLink());assert(s.dev!==d.dev||s.ino!==d.ino);}
  assert.deepEqual([...seen].sort(),Object.keys(original).sort());await pinned(clone.byteValidationHelper);await pinned(clone.rootController);
  const views=await read(path.join(project,'Content/Data/viewpoints.json'));assert.deepEqual(views,await read(path.join(e.project,'Content/Data/viewpoints.json')));
  for(const id of ['exterior-garden','exterior-neighborhood','neighbor-finish-close-r18'])assert.equal(views.views.filter(v=>v.id===id).length,1);
  const rawPath=path.join(source,'soft-ground-native-r2.log.json'),processPath=path.join(source,'soft-ground-native-r2-process.json');
  const rawPin=await ownPin(rawPath,RAW_SHA),processPin=await ownPin(processPath,PROCESS_SHA),raw=await read(rawPath),t=await read(processPath);
  assert.equal(raw.pid,NATIVE_PID);assert.equal(raw.code,0);assert.equal(raw.signal,null);assert.equal(raw.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');
  assert.equal(raw.args[0],path.join(project,'BreziTwin.uproject'));assert(Number.isFinite(Date.parse(raw.startedAt))&&Date.parse(raw.endedAt)>=Date.parse(raw.startedAt));
  assert.equal(t.processFile,rawPath);assert.equal(t.processFileSha256,RAW_SHA);assert.equal(t.reportSha256,REPORT_SHA);assert.equal(t.logFile,path.join(source,'soft-ground-native-r2.log'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+t.logFile])assert(raw.args.includes(arg));
  await ownPin(t.logFile,t.logSha256);assert.equal(t.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(t.sourcePinsBeforeNative).length,TERMINAL_PINS);
  assert.equal(t.controllerSha256BeforeNative,MONITOR_SHA);assert.equal(t.controllerSha256AfterNative,MONITOR_SHA);await ownPin(t.controller,MONITOR_SHA);
  for(const[file,h]of Object.entries(r.inputFiles))assert.equal(t.sourcePinsBeforeNative[file],h);for(const[file,h]of Object.entries(t.sourcePinsBeforeNative))await ownPin(file,h);
  const auditPath=path.join(source,'root-native-success-byte-audit-r38b-r2.json');await ownPin(auditPath,AUDIT_SHA);const audit=await read(auditPath);
  validateSoftGroundRootAudit(audit,r,{reportPin,processPin,rawPin});await pinned(audit.auditController);
  const w=r.nativeModuleWitness,module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');assert.equal(w.source,path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));
  assert.equal(w.destination,module);assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);for(const file of [module,w.source])await ownPin(file,MODULE_SHA);
  const checker=path.join(root,'scripts/unreal/exterior-context-yard-soft-coherence-editor-check-r29-r3.py');await ownPin(checker,CHECKER_SHA);
  const native=JSON.parse((await exec('python3',['-B',checker,receiptPath],{timeout:240000,maxBuffer:1024*1024})).stdout);
  assert.equal(native.mode,'verified-saved-r38r2-two-slot-soft-ground-editor-source');assert.equal(native.nativeProcessId,NATIVE_PID);assert.equal(native.originalActors,5364);assert.equal(native.savedActors,5364);
  assert.equal(native.fullHismComponents,2325);assert.equal(native.fullHismInstances,678197);assert.equal(native.wholeActorCounterfactualValidated,true);assert.equal(native.freshNativeActorOrGeometryDecodePerformedByCpuChecker,false);
  const summary={...native,sourcePinsUnchangedAfterNative:TERMINAL_PINS,sourceReceiptPins:SOURCE_PINS,
    scope:'Two material slot0 overrides and one artist permission texture; all saved geometry, roots, raw controls and old material/texture policies preserved. Pixel appearance and outside equivalence require the actual images.'};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:e.base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:w,moduleWitnessSource:r.projectClone,
    receiptSummary:{baseNativeReport:r.baseNativeReport,selectedPlan:r.selectedPlan,sourcePreflight:r.sourcePreflight,repairEvidence:r.repairEvidence,savedMapUnloadedReloaded:true,materialPackagesIndependentlyUnloaded:false,summary}};
}
