// Actual saved R46: five component material slots, two graphs/three photos.
// No previous saved consumer, source producer, geometry import or native call.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createReadStream} from 'node:fs';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {validateProjectClosure} from './exterior-editor-source-r31.mjs';
export {validateProjectClosure};

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const OWNER='scripts/unreal/exterior-burkea-clay-native-r46.py';
const SCHEMA='brezi-selected-r43b-burkea-and-clay-roof-material-native-r46';
const REPORT='combined-material-native-report-r46.json';
const SOURCE='output/unreal/exterior-20261002-r46a';
const STUDY='output/unreal/exterior-burkea-clay-20261002-r46-native-study';
const PLAN_SHA='75ecc7256fab9c031b00e5c9f36cce22d9ba7bdb1616d1b1ca230b07992a5929';
const PF_SHA='f00ae16b2edb3d65d0636675602630a0a1ab36db2dc3b6cef435694fa353e6c1';
const HELPER_SHA='5f22c171d838cea0edc6e4f5d57efd9a8e8aa1dfa0d42ace0fc564495b49a7fe';
const BASE_SHA='802756b95c06d01351cbdaee7b439ab10728e04f2d884fb971f111e735e9b5d4';
const CLONE_SHA='f05c88c14f37545b9675058870844b06eaef9c9de2790113d85ddd6980f65e3b';
const DECISION_SHA='869013e1e2b564aee21532acabcd737d0b8dda2e6bd78357e487469d647974d3';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const PREVIOUS_SHA='060aa2ee7c589fe33d9b307e4a79fdbc9b1342026820b1d83e63abde92bedf4c';
export const SOURCE_PINS=5657;
export const ACTUAL=Object.freeze({
 reportSha:'0d73546f2ae59f89376a2676ff5839d1be0a8344a986d586db32ccbe2623dced',
 processSha:'b2d7c972f8d4f3e64c7e20a9eaf45be29a26b5ba8f163f000483e9db60f42865',
 rawSha:'59b0a1abf3b806cb7351256908165194afd99f434ff6b70809d0797f9256bf2f',
 auditSha:'4b816e8b0b41d696cbf6a37e826c17124e460a7af1e7d5505aa9c2bbbca392cf',
 nativePid:65818,terminalPins:5664,
 monitorSha:'883c768f29c117b368110a4e2fe853290117b7f023824b64c6a63273a1646c65',
 checkerSha:'3b634652dd88fae38b5fba217dc4d3932df790c01499258e22075a6427eca9c1'
});
export const COUNTS=Object.freeze({originalActors:5371,savedActors:5371,fullHismComponents:2329,
 fullHismInstances:678205,originalMaterialGraphs:72,savedMaterialGraphs:74,originalTextureObjects:114,
 savedTextureObjects:117,originalContentFiles:4139,savedContentFiles:4144,protectedFiles:132,
 newMaterialGraphs:2,newTextureObjects:3,newPackages:5,changedMaterialSlots:5,newActors:0,newMeshes:0});
const TRUE_FLAGS=['nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged',
 'wholeActorCounterfactualValidated','all5371ActorFieldsExceptFiveDeclaredSlotsExact','all2329RawControlsExact',
 'all72OriginalGraphAuxObservedUsageExact','all114OriginalVisible24TexturePoliciesAndSelectedMetadataExact'];
const FALSE_FLAGS=['oldActorGeometryRootCollisionNavOrMeshDefaultSettersCalled','oldMaterialOrTextureSettersCalled',
 'nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','activeOutputPromoted',
 'physicalLeafOrRoofOpticsAccepted','nativeNormalTangentNumericReadbackPerformed','sourcePhotoPixelsEdited',
 'materialPackagesIndependentlyUnloaded','materialCompileDiagnosticsExhaustivelyRead',
 'additionalSeedRangesPreservationClaimed','cloudPhaseOrDynamicExposureLocked'];
const exec=promisify(execFile),read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const sha=async p=>{const h=createHash('sha256');for await(const b of createReadStream(p))h.update(b);return h.digest('hex');};
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);

export function requireActualBinding(actual=ACTUAL){
 for(const key of ['reportSha','processSha','rawSha','auditSha','checkerSha','monitorSha'])assert(hashLike(actual[key]),'R32 awaits exact saved/checker/current-byte closure');
 assert(Number.isInteger(actual.nativePid)&&actual.nativePid>0);assert(Number.isInteger(actual.terminalPins)&&actual.terminalPins>=SOURCE_PINS);
}

export function validateMaterialPilotHeader(r,plan,pf,{root=ROOT,actual=ACTUAL}={}){
 assert.equal(r.schema,SCHEMA);assert.equal(r.schemaVersion,1);assert.equal(r.owner,OWNER);
 assert.equal(r.status,'verified-saved-five-slot-burkea-and-clay-roof-material-pilot');assert.equal(r.nativeProcessId,actual.nativePid);
 assert.equal(r.project,path.join(root,SOURCE,'Project/BreziTwin'));assert.deepEqual(r.actualCounts,COUNTS);
 assert.equal(r.selectedPlan.path,path.join(root,STUDY,'combined-material-native-plan.json'));assert.equal(r.selectedPlan.sha256,PLAN_SHA);
 assert.equal(r.sourcePreflight.path,path.join(root,STUDY,'source-preflight/source-preflight.json'));assert.equal(r.sourcePreflight.sha256,PF_SHA);
 assert.equal(r.baseNativeReport.sha256,BASE_SHA);assert.equal(r.projectClone.sha256,CLONE_SHA);assert.equal(r.rootImageDecision.sha256,DECISION_SHA);
 assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);assert.equal(Object.keys(r.inputFiles).length,SOURCE_PINS);
 assert.equal(r.activeDesign,'C/B/B');assert.deepEqual(r.setbacksMm,[3000,3000]);
 for(const key of TRUE_FLAGS)assert.equal(r[key],true);for(const key of FALSE_FLAGS)assert.equal(r[key],false);
 assert.equal(r.combinedCaptureCannotIsolateLeafTransmissionFromRoofIndirectLighting,true);
 for(const v of [plan,pf]){assert.equal(v.schema,SCHEMA);assert.equal(v.schemaVersion,1);assert.deepEqual(v.binding,r.binding);assert.deepEqual(v.expectedCounts,COUNTS);assert.equal(v.nativeExecuted,false);assert.equal(v.gpuExecuted,false);}
 assert.equal(plan.owner,'scripts/unreal/exterior-burkea-clay-native-study-r46.py');assert.equal(plan.nativeOwner,OWNER);
 assert.equal(plan.status,'selected-five-slot-material-source-ready-native-pending');assert.equal(pf.owner,OWNER);assert.equal(pf.status,'five-slot-material-source-preflight-validated-native-pending');
 assert.deepEqual(pf.selectedPlan,r.selectedPlan);assert.deepEqual(pf.inputFiles,r.inputFiles);
 assert.deepEqual(r.inputFiles,{...plan.inputFiles,[r.selectedPlan.path]:PLAN_SHA});assert.equal(Object.keys(plan.inputFiles).length,SOURCE_PINS-1);
 assert.equal(pf.tests.exitCode,0);assert.equal(pf.tests.testCount,10);assert.equal(pf.tests.nativeApisActuallyExercised,false);assert.deepEqual(r.moduleOrderWitness,pf.moduleOrderWitness);
 assert.deepEqual(r.sourceProposals,plan.sourceProposals);assert.deepEqual(r.newPackages,plan.expectedNewPackages);
 assert.deepEqual(r.binding.selectedNativeReport,r.baseNativeReport);assert.deepEqual(r.binding.selectedNativeProcess,r.baseNativeProcess);
 assert.deepEqual(r.binding.selectedCurrentByteAudit,r.baseCurrentByteAudit);assert.deepEqual(r.binding.projectClone,r.projectClone);assert.deepEqual(r.binding.rootImageDecision,r.rootImageDecision);
 assert.equal(r.binding.nativeOwner,OWNER);assert.equal(r.binding.schema,SCHEMA);assert.equal(r.binding.schemaVersion,1);assert.equal(r.binding.candidateProject,r.project);
 for(const key of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','activeOutputPromoted'])assert.equal(r.binding[key],false);
 assert.equal(plan.oldCompleteMaterialGraphs,72);assert.equal(plan.oldCompleteVisible24TextureSnapshots,114);assert.equal(plan.previouslyUnrecordedAuxAndUsageCapturedBeforeAndSaved,3);
 assert.deepEqual(Object.fromEntries(Object.entries(plan.materialReaderDispatch).map(([k,v])=>[k,v.length])),{basic:60,neighbor:9,tree:3});
}

export function reconstructMaterialCounterfactual(before,leaf,roof){
 assert.equal(Object.keys(before).length,5371);const out=structuredClone(before),historical=leaf.historicalObservationOnly;
 const actor=out[historical.targetActor];assert(actor);const components=actor.components.filter(c=>c.path===historical.targetComponent);assert.equal(components.length,1);
 const c=components[0];assert.equal(c.instanceCount,4);assert.equal(c.orderedInstanceTransformsSha256,historical.originalInstanceOrderSha256);
 assert.equal(c.materials[1],historical.sourceLeafMaterial);assert.deepEqual(c.overrideMaterials,[]);
 c.materials[1]=leaf.proposedMaterial.ownAsset;c.overrideMaterials=[null,leaf.proposedMaterial.ownAsset];
 assert.equal(roof.targets.length,4);const changed=new Set([historical.targetActor]);
 for(const row of roof.targets){assert(!changed.has(row.actor));changed.add(row.actor);const target=out[row.actor];assert(target);const parts=target.components.filter(v=>v.path===row.component);assert.equal(parts.length,1);const part=parts[0];assert.equal(row.slot,0);assert.equal(part.mesh,row.currentMesh);assert.equal(part.materials[0],row.currentMaterial);assert.deepEqual(part.overrideMaterials,row.currentOverrideMaterials);part.materials[0]=roof.proposedAssets.material;part.overrideMaterials=[roof.proposedAssets.material];}
 assert.equal(changed.size,5);return out;
}

export function validateMaterialContent(before,after,packages,delta){
 assert.equal(Object.keys(before).length,4139);assert.equal(Object.keys(after).length,4144);assert.equal(packages.length,5);
 const added=packages.map(a=>{assert(a.startsWith('/Game/Brezi/BurkeaTransmission20261002R44/')||a.startsWith('/Game/Brezi/ClayRoofPhoto20261002R45/'));return a.slice(6).split('.')[0]+'.uasset';}).sort();assert.equal(new Set(added).size,5);
 assert.deepEqual(Object.keys(after).sort(),[...Object.keys(before),...added].sort());
 const changed=Object.keys(before).filter(k=>{try{assert.deepEqual(before[k],after[k]);return false;}catch{return true;}}).sort();
 assert.deepEqual(changed,['Brezi/Maps/Brezi.umap']);assert.deepEqual(delta,{changedOriginalFiles:changed,newRelativeFiles:added});
}

export function validateRootAudit(a,r,{reportPin,processPin,rawPin}){
 assert.equal(a.schema,'brezi-r46a-root-saved-five-slot-material-byte-audit-r1');assert.equal(a.schemaVersion,1);
 assert.equal(a.status,'verified-saved-native0-only-original-map-changed-five-new-owned-material-photo-packages-all5664-frozen-pins-exact');
 assert.deepEqual(a.nativeReport,reportPin);assert.deepEqual(a.nativeProcess,processPin);assert.deepEqual(a.rawNativeProcess,rawPin);assert.equal(a.nativeProcessId,ACTUAL.nativePid);assert.equal(a.exitCode,0);assert.equal(a.rootSessionClosedExitCode,0);assert.deepEqual(a.nativeIdleAfter,[]);
 assert.equal(a.project,r.project);assert.deepEqual(a.projectClone,r.projectClone);assert.deepEqual(a.currentContentInventory,r.afterContentInventory);assert.deepEqual(a.currentProtectedProof,r.protectedProjectProof);
 assert.equal(a.currentProjectFiles,4276);assert.equal(a.currentContentFiles,4144);assert.equal(a.currentProtectedFiles,132);assert.deepEqual(a.actualCounts,COUNTS);assert.deepEqual(a.newRelativeContentFiles,r.assetDelta.newRelativeFiles);assert.deepEqual(a.newOwnedPackageTypes,{materials:2,textures:3});
 for(const key of ['candidateOriginal4270NonMapFilesExact','onlyOriginalMapChanged','selectedR43bAll4271FilesExact','initialIndependentCloneRowsStillIndependent','all5664FrozenSourcePinsExact','all5657PreflightSourcePinsExact'])assert.equal(a[key],true);
 const keys=TRUE_FLAGS.filter(k=>!['nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged'].includes(k));assert.deepEqual(Object.keys(a.savedNativeProofFlags).sort(),[...keys].sort());for(const key of keys){assert.equal(a.savedNativeProofFlags[key],true);assert.equal(r[key],true);}
 for(const key of ['newNativeActorOrAttributeDecodeByAudit','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','activeOutputPromoted'])assert.equal(a[key],false);
}

export async function loadEditorSourceEvidence(source,{root}={}){
 requireActualBinding();source=path.resolve(source);root=path.resolve(root);assert.equal(source,path.join(root,SOURCE),'Only saved R46 accepted');
 const names=await fs.readdir(source);assert(names.includes(REPORT));assert(!names.some(n=>n!==REPORT&&/native-report.*\.json$/.test(n)),'No copied/failed/foreign native-family dispatch');
 const project=path.join(source,'Project/BreziTwin'),reportPath=path.join(source,REPORT),closure=new Set();
 async function pinned(row){assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);const st=await fs.lstat(row.path);assert(st.isFile()&&!st.isSymbolicLink());assert.equal(st.size,row.bytes);assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;}
 const pj=async row=>read(await pinned(row));const ownPin=async(file,hash)=>{const row={path:file,sha256:hash,bytes:(await fs.stat(file)).size};await pinned(row);return row;};
 async function pinTree(value){if(Array.isArray(value)){for(const v of value)await pinTree(v);}else if(value&&typeof value==='object'){if(['path','sha256','bytes'].every(k=>Object.hasOwn(value,k)))await pinned({path:value.path,sha256:value.sha256,bytes:value.bytes});for(const v of Object.values(value))await pinTree(v);}}
 await ownPin(path.join(root,'scripts/unreal/exterior-editor-source-r31.mjs'),PREVIOUS_SHA);
 const reportPin=await ownPin(reportPath,ACTUAL.reportSha),r=await read(reportPath),plan=await pj(r.selectedPlan),pf=await pj(r.sourcePreflight);
 validateMaterialPilotHeader(r,plan,pf,{root});await pinTree(plan);await pinTree(r);
 const base=await pj(r.baseNativeReport),baseProject=path.join(path.dirname(r.baseNativeReport.path),'Project/BreziTwin');
 assert.equal(base.owner,'scripts/unreal/exterior-context-parcel-boundary-native-r43-r2.py');assert.equal(base.schemaVersion,2);assert.equal(base.status,'verified-saved-three-authored-open-boundary-masters');assert.equal(base.nativeProcessId,44798);assert.equal(base.nativeApplied,true);assert.equal(base.savedMapUnloadedReloaded,true);
 const decision=await pj(r.rootImageDecision);assert.equal(decision.schema,'brezi-r43b-root-image-base-selection-r1');assert.equal(decision.schemaVersion,1);assert.equal(decision.status,'selected-saved-r43b-only-as-next-combined-leaf-and-clay-roof-material-pilot-base');assert.equal(decision.allFourOriginalPngsViewedByRoot,true);assert.equal(decision.independentVisualPeerReceived,true);assert.deepEqual(decision.sourceNativeReport,r.baseNativeReport);await pinTree(decision);
 const leaf=await pj(r.sourceProposals.leaf),roof=await pj(r.sourceProposals.roof),before=await pj(r.beforeActorWitness),expected=await pj(r.expectedActorWitness),saved=await pj(r.savedActorWitness);
 assert.deepEqual(before,await pj(base.savedActorWitness));assert.deepEqual(expected,reconstructMaterialCounterfactual(before,leaf,roof));assert.deepEqual(saved,expected);assert.equal(r.expectedActorWitnessSha256,r.savedActorWitnessSha256);
 const hism=Object.values(saved).flatMap(a=>a.components).filter(c=>c.class==='/Script/Engine.HierarchicalInstancedStaticMeshComponent');assert.equal(hism.length,2329);assert.equal(hism.reduce((n,c)=>n+c.instanceCount,0),678205);
 const raw=await pj(r.rawInstanceControlsBefore);assert.equal(Object.keys(raw).length,2329);assert.deepEqual(raw,await pj(base.rawInstanceControlsSaved));assert.deepEqual(await pj(r.rawInstanceControlsSaved),raw);
 const old=await pj(r.originalAssetWitnessBefore);assert.deepEqual(await pj(r.originalAssetWitnessSaved),old);assert.deepEqual(Object.keys(old).sort(),['graphs','textures']);assert.equal(Object.keys(old.graphs).length,72);assert.equal(Object.keys(old.textures).length,114);
 const built=await pj(r.newMaterialReport);assert.deepEqual(built,r.materialReport);const newReadback=await pj(r.savedNewMaterialReadback);assert.deepEqual(Object.keys(built).sort(),['leaf','roof']);assert.deepEqual(newReadback.leaf,Object.fromEntries(['asset','graph','aux','usage'].map(k=>[k,built.leaf[k]])));assert.deepEqual(newReadback.roof,Object.fromEntries(['asset','graph','aux'].map(k=>[k,built.roof.material[k]])));
 assert.deepEqual(built.roof.nativeBinding,r.binding);assert.equal(built.roof.newMaterialGraphs,1);assert.equal(built.roof.newTextureObjects,3);assert.equal(built.roof.fourOwnedPackagesSaved,true);assert.deepEqual([...built.leaf.newPackageAssets,...built.roof.newPackageAssets].sort(),r.newPackages);
 const contentInventory=await pj(r.afterContentInventory),baseContent=await pj(base.afterContentInventory);validateMaterialContent(baseContent,contentInventory,r.newPackages,r.assetDelta);assert.deepEqual(r.protectedProjectProof,base.protectedProjectProof);const projectProof=await pj(r.protectedProjectProof);assert.equal(Object.keys(projectProof).length,132);
 const clone=await pj(r.projectClone);assert.equal(clone.schema,'brezi-image-selected-saved-r43b-combined-material-project-clone-r46');assert.equal(clone.schemaVersion,1);assert.equal(clone.status,'verified-byte-identical-independent-apfs-image-selected-saved-r43b-before-five-slot-material-pilot-r46');assert.equal(clone.project,project);assert.equal(clone.sourceProject,baseProject);assert.equal(clone.nativeExecuted,false);assert.equal(clone.materialPilotPending,true);assert.deepEqual(clone.nativeIdleAfter,[]);assert.deepEqual(clone.sourceImageSelection,r.rootImageDecision);assert.deepEqual(clone.sourceNativeReport,r.baseNativeReport);assert.deepEqual(clone.sourceNativeProcess,r.baseNativeProcess);assert.deepEqual(clone.sourceCurrentByteAudit,r.baseCurrentByteAudit);assert.equal(clone.fileCount,4271);assert.equal(clone.files.length,4271);assert.equal(clone.contentFiles,4139);assert.equal(clone.protectedFiles,132);
 const original={...Object.fromEntries(Object.entries(baseContent).map(([k,v])=>['Content/'+k,v])),...projectProof},seen=new Set();
 for(const row of clone.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(original,relative)&&!seen.has(relative));seen.add(relative);assert.equal(row.source,path.join(baseProject,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);assert.deepEqual({sha256:row.sha256,bytes:row.bytes},original[relative]);const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);}assert.deepEqual([...seen].sort(),Object.keys(original).sort());await pinned(clone.rootController);
 assert.deepEqual(await fs.readFile(path.join(project,'Content/Data/viewpoints.json')),await fs.readFile(path.join(baseProject,'Content/Data/viewpoints.json')));
 for(const[file,hash]of Object.entries(r.inputFiles))await ownPin(file,hash);
 for(const[relative,row]of Object.entries(contentInventory))await pinned({path:path.join(project,'Content',relative),...row});
 for(const[relative,row]of Object.entries(projectProof))await pinned({path:path.join(project,relative),...row});
 const processPin=await ownPin(path.join(source,'combined-material-native-r46-process.json'),ACTUAL.processSha),rawPin=await ownPin(path.join(source,'combined-material-native-r46.log.json'),ACTUAL.rawSha),terminal=await read(processPin.path),rawProcess=await read(rawPin.path);
 assert.equal(rawProcess.pid,ACTUAL.nativePid);assert.equal(rawProcess.code,0);assert.equal(rawProcess.signal,null);assert.equal(rawProcess.args[0],path.join(project,'BreziTwin.uproject'));assert.equal(terminal.reportSha256,ACTUAL.reportSha);assert.equal(terminal.processFile,rawPin.path);assert.equal(terminal.processFileSha256,ACTUAL.rawSha);assert.equal(terminal.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(terminal.sourcePinsBeforeNative).length,ACTUAL.terminalPins);
 for(const[file,hash]of Object.entries(r.inputFiles))assert.equal(terminal.sourcePinsBeforeNative[file],hash);for(const[file,hash]of Object.entries(terminal.sourcePinsBeforeNative))await ownPin(file,hash);
 assert.equal(terminal.controllerSha256BeforeNative,ACTUAL.monitorSha);assert.equal(terminal.controllerSha256AfterNative,ACTUAL.monitorSha);await ownPin(terminal.controller,ACTUAL.monitorSha);await ownPin(terminal.logFile,terminal.logSha256);for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+terminal.logFile])assert(rawProcess.args.includes(arg));
 const audit=await pj(await ownPin(path.join(source,'root-native-success-byte-audit-r46a-r1.json'),ACTUAL.auditSha));validateRootAudit(audit,r,{reportPin,processPin,rawPin});await pinTree(audit);
 const w=r.nativeModuleWitness;assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);assert.equal(w.destination,path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.source,path.join(baseProject,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));for(const file of [w.source,w.destination])await ownPin(file,MODULE_SHA);
 const checker=path.join(root,'scripts/unreal/exterior-burkea-clay-editor-check-r32.py');await ownPin(checker,ACTUAL.checkerSha);
 const checked=JSON.parse((await exec('python3',['-B',checker,reportPath],{timeout:240000,maxBuffer:2*1024*1024})).stdout);assert.equal(checked.mode,'saved-r46-five-slot-material-pilot');assert.equal(checked.nativeProcessId,ACTUAL.nativePid);assert.equal(checked.savedActors,5371);assert.equal(checked.fullHismComponents,2329);assert.equal(checked.fullHismInstances,678205);assert.equal(checked.wholeActorCounterfactualValidated,true);assert.equal(checked.freshNativeActorOrGeometryDecodePerformedByCpuChecker,false);
 const summary={...checked,sourceReceiptPins:SOURCE_PINS,sourcePinsUnchangedAfterNative:ACTUAL.terminalPins,scope:'Only leaf slot1 and four roof slot0 overrides; original geometry, all raw roots/default slots and collision retained. Native appearance remains pending; combined images cannot isolate indirect-light effects.'};
 return{mode:summary.mode,project,nativeReceiptPath:reportPath,base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:w,moduleWitnessSource:r.projectClone,receiptSummary:{baseNativeReport:r.baseNativeReport,selectedPlan:r.selectedPlan,sourcePreflight:r.sourcePreflight,rootImageDecision:r.rootImageDecision,summary}};
}
