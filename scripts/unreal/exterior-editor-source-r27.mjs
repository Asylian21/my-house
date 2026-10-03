// Closed six-original-form Periwinkle source. Actual R36 success pins are pending.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR24,validateProjectClosure} from './exterior-editor-source-r24.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-garden-periwinkle-native-r36-r2.py';
const HELPER_SHA='b86a99e06076fc90552544d154aee2a1d299b1799e7099dd9a31061315695763';
const SCHEMA='brezi-garden-original-periwinkle-composition-native-r36';
const PLAN_SHA='71de87f91926f059a7553e8553927151d8aa9873040dbb56d20d31203e37a640';
const SOURCE_SHA='93b4bc17203f10b5c14acd036dd942f8d2bf0b99ec1744e6638e7a29502a8b96';
const PREFLIGHT_SHA='0629127c96e608f34082040587a5b9c8120374290cdef7e76d89b490e799ca9c';
const BASE_SHA='d233329bee2ffcb95419c8266ff8c1f50931ba8f642ded23ab20330f1d334cb8';
const R24_SHA='18063e3ffd2cb8812ff4b516a52ea0dee8f0b3d9938f64404114ad2ca85817d7';
const REPORT_SHA='d2057c860c0b5135cd19beaee776145d89c3377a07ff08abee9537f6a15c765e',ROOT_AUDIT_SHA='a2be8c8a3d5c50ee60b5ee78d1426bb4c322d0de2bcb1c13a6734959159253e8',CHECKER_SHA='57d02087081031089f805ab080672acfcabd9f053b2856f711c91a84912ef7d0',NATIVE_PID=47851,TERMINAL_PIN_COUNT=588;
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const PREFIX='Brezi/GardenPeriwinkle20261002R36/';
const MODELS=Array.from({length:6},(_,i)=>`periwinkle_plant_0${i+1}_LOD0`);
const MODEL_COUNTS=[72,10,93,106,75,28],TRIANGLES=[11252,9096,5338,4108,3078,1478];
const COUNTS={originalActors:5354,savedActors:5360,fullHismComponents:2322,fullHismInstances:676957,
  originalGardenRoots:473,retainedOriginalGardenRoots:53,preservedR34FernRoots:36,newOriginalPeriwinkleRoots:384,
  newMeshAssets:6,newMaterialGraphs:1,newTextureObjects:5,newPipelineAssets:3,newPackages:15,
  scopedMaterialGraphs:61,scopedTextureObjects:96,contentFiles:4086,protectedFiles:132};
const read=async p=>JSON.parse(await fs.readFile(p,'utf8')),exec=promisify(execFile);
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};

export function validatePeriwinkleHeader(r,{source,project},bindings={nativePid:NATIVE_PID}){
  assert.equal(r.schema,SCHEMA);assert.equal(r.schemaVersion,2);assert.equal(r.owner,OWNER);
  assert.equal(r.status,'verified-saved-384-original-periwinkle-low-garden-composition');
  assert.equal(r.repairSchema,'brezi-original-periwinkle-source-geometry-identity-repair-r2');
  assert.equal(r.immutableSourceGuard.sha256,'4dd86369ae79b80e58296329b0e1b183a45c26dd7f3b609f7795e42421804138');
  assert.equal(r.importIdentityEvidence.failedNativeProcess.pid,42780);assert.equal(r.importIdentityEvidence.failedNativeProcess.exitCode,255);
  assert.equal(r.importIdentityEvidence.failedNativeProcess.sourcePinCount,560);
  for(const key of ['nativeOriginalNodeLabelIdentityObserved','persistedPartialMeshDiagnosticAvailable','failedPartialFilesContainSavedMeshPackages',
    'sixMeshIdentityVerifiedByThisSourceReceipt','sourceGeometryOrExpectedCornerOrderChanged','originalSourceControlMathChanged','guardRelaxed'])assert.equal(r.importIdentityEvidence[key],false);
  assert.equal(r.allSixImportedMastersIdentifiedByFullSourceCorners,true);assert.equal(r.actorLabelsUsedForSourceMeshIdentity,false);
  assert.equal(r.observedNonrenderingImportContainers.length<=1,true);assert(hashLike(r.importTemporaryActorInventory.sha256));
  assert.equal(r.output,source);assert.equal(r.project,project);assert(Number.isInteger(bindings.nativePid)&&bindings.nativePid>0);assert.equal(r.nativeProcessId,bindings.nativePid);
  for(const[k,h]of Object.entries({selectedPlan:PLAN_SHA,sourceProposal:SOURCE_SHA,sourcePreflight:PREFLIGHT_SHA,baseNativeReport:BASE_SHA}))assert.equal(r[k].sha256,h);
  for(const k of ['nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged','originalSavedR34Unchanged',
    'allOriginal12Ornamentals41Flowers36FernsRawControlsExact','allOriginal8949GrassAnd78TreesRawControlsExact',
    'all384SourceOriginalRootsRetiredOnceAndReplacedOnce','allOriginalSourceSixAttributesAndIndexBinBytesPreserved','sourceHeightRoleChanges384Explicit'])assert.equal(r[k],true);
  for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified',
    'ecologicalFitVerified','surveyedPlacementVerified','nativeNormalTangentReadbackAvailable','nativeColor0Color1ReadbackAvailable',
    'meshMaterialPackagesIndependentlyUnloaded','AdditionalRandomSeedsReadbackAvailable','retainedTransformRecompositionPerformed',
    'seedMutationPerformed','perInstanceShaderRandomValuePreservationClaimed','yardIntegrationApplied','derivedContactFloatingPointBitEqualityClaimed','sourceGroundElevationSurveyed'])assert.equal(r[k],false);
  assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});
  assert.deepEqual(r.actualCounts,COUNTS);assert.equal(r.contactWorldBottomArithmeticCapCm,1e-7);
  assert.deepEqual(Object.keys(r.newOwnedGroups),MODELS);assert.deepEqual(Object.keys(r.nativeGeometryReadback),MODELS);
  const ids=[],actors=[];
  MODELS.forEach((model,i)=>{const row=r.newOwnedGroups[model],proof=r.nativeGeometryReadback[model];
    assert(row.actor.startsWith('/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.'));actors.push(row.actor);
    assert.equal(row.instances,MODEL_COUNTS[i]);assert.equal(row.rootIds.length,row.instances);ids.push(...row.rootIds);
    assert.equal(row.mesh,`/Game/${PREFIX}Geometry/StaticMeshes/${model}.${model}`);assert.equal(proof.asset,row.mesh);
    assert.equal(proof.lodCount,1);assert.equal(proof.sections,1);assert.equal(proof.triangles,TRIANGLES[i]);assert(hashLike(proof.nativeCornerSha256));
    assert.equal(proof.fullOrderedNativeF32PositionUV0UV1WindingVerified,true);assert.equal(proof.allSixOriginalSourceAttributeBytesPreserved,true);
    assert.equal(proof.nativeTangentsRequestedFromOriginalUv0,true);
    for(const k of ['originalProviderLodChainPresent','nativeNormalTangentReadbackAvailable','nativeColor0Color1ReadbackAvailable',
      'sourceTangentsPresent','nativeTangentGenerationNumericallyVerified','nativeNaniteRequested','meshPackageIndependentlyUnloaded'])assert.equal(proof[k],false);
  });
  assert.equal(new Set(actors).size,6);assert.equal(ids.length,384);assert.equal(new Set(ids).size,384);
  assert(!ids.some(id=>id.startsWith('garden_ornamental_')),'All original ornamentals remain');
  assert.equal(r.wholeOriginalLowGroupRetirements.length,4);const retired=[];
  for(const row of r.wholeOriginalLowGroupRetirements){assert(row.retiredRoots>0&&row.rootIds.length===row.retiredRoots);retired.push(...row.rootIds);
    assert.equal(row.entireComponentMembersCleared,true);for(const k of ['actorOrComponentDeleted','survivorRecompositionPerformed','seedSetterPerformed','AdditionalRandomSeedsReadbackAvailable','perInstanceShaderRandomValuePreservationClaimed'])assert.equal(row[k],false);}
  assert.deepEqual([...retired].sort(),[...ids].sort());assert.equal(new Set(r.wholeOriginalLowGroupRetirements.map(v=>v.actor)).size,4);
  assert.equal(r.sourceCrownMaskProof.length,384);assert.deepEqual(r.sourceCrownMaskProof.map(p=>p.rootId).sort(),[...ids].sort());
  for(const row of r.sourceCrownMaskProof){assert.equal(row.allVerticesAndFullCircleInOriginalBed,true);assert.equal(row.fullCircleExcludesOriginalSteps,true);
    assert(Number.isFinite(row.contactArithmeticDeltaCm)&&Math.abs(row.contactArithmeticDeltaCm)<=1e-7);assert.equal(row.freshDerivedStatisticsBitEqualityRequired,false);}
  assert.equal(r.originalSourceNodeNativeMeshBindings.length,6);assert.deepEqual(r.originalSourceNodeNativeMeshBindings.map(v=>v.sourceNodeId).sort(),MODELS);
  const temporaryActors=new Set(),importedMeshes=new Set();
  for(const row of r.originalSourceNodeNativeMeshBindings){const i=MODELS.indexOf(row.sourceNodeId),configured=r.nativeGeometryReadback[row.sourceNodeId];
    assert.equal(row.meshNameUsedForSourceIdentity,false);assert.equal(row.actorLabelUsedForSourceIdentity,false);assert.equal(row.uniqueTriangleCountUsedOnlyForCandidateRouting,true);
    assert.equal(row.sourceIdentityFromTriangleCountAlone,false);assert.equal(row.sourceIdentityFromActorOrMeshName,false);
    assert.equal(row.fullOrderedNativeF32PositionUV0UV1WindingVerified,true);assert.equal(row.triangles,TRIANGLES[i]);assert.equal(row.sections,1);
    assert.equal(row.nativeCornerSha256,configured.nativeCornerSha256);assert(row.asset.startsWith('/Game/'+PREFIX+'Geometry/'));
    assert.equal(typeof row.actualTemporaryActorLabel,'string');temporaryActors.add(row.actualTemporaryActor);importedMeshes.add(row.asset);
  }
  assert.equal(temporaryActors.size,6);assert.equal(importedMeshes.size,6);
  const m=r.materialReport;assert.equal(m.schema,'brezi-original-periwinkle-five-map-material-r36');assert.equal(m.owner,'scripts/unreal/exterior-garden-periwinkle-materials-r36.py');
  assert.equal(m.status,'owned-original-five-map-periwinkle-material-created');assert.equal(m.sourceRecipe.sha256,'04a7223f7e5ba93c88f6e7438d3776283a241782f4b00c52fba5c06c98cc1b98');
  assert.equal(m.materialCount,1);assert.equal(m.textureObjectCount,5);assert.equal(m.newPackageAssets.length,6);assert.equal(new Set(m.newPackageAssets).size,6);assert.deepEqual(m.compileErrors,[]);
  assert.equal(m.sourceOriginalAlphaMode,'BLEND');assert.equal(m.ownedUnrealBlendMode,'MASKED');assert.equal(m.sourcePngBits,16);assert.equal(m.source16BitDoesNotProveNativePixelFormat,true);
  assert(m.newPackageAssets.every(p=>p.startsWith('/Game/'+PREFIX)));assert.equal(new Set(Object.values(r.newOwnedGroups).map(v=>v.material)).size,1);
  for(const row of Object.values(r.newOwnedGroups))assert.equal(row.material,m.asset);
  for(const k of ['originalTexturePixelsEdited','nativeImportedPixelsDecoded','nativeSourcePixelFormatReadbackAvailable','nativeGpuPixelFormatReadbackAvailable',
    'nativeNormalTangentReadbackAvailable','materialPackagesIndependentlyUnloaded','sourceOpticalModelExactlyReproduced','physicalOpticalCalibrationAccepted','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted'])assert.equal(m[k],false);
}

export function validatePeriwinkleReportNames(names){
  const selected='garden-periwinkle-native-report-r2.json';assert(names.includes(selected));
  assert(!names.some(n=>n!==selected&&/(?:exterior-import|native-report|overlay-report).*\.json$/.test(n)),'R36 cannot inherit old/failed/unknown native reports');
}

export function validatePeriwinkleContent(before,after,packages,delta){
  assert.equal(Object.keys(before).length,4071);assert.equal(Object.keys(after).length,4086);assert.equal(packages.length,15);assert.equal(new Set(packages).size,15);
  for(const p of packages)assert(p.startsWith(PREFIX)&&p.endsWith('.uasset')&&!Object.hasOwn(before,p));
  assert.deepEqual(Object.keys(after).sort(),[...Object.keys(before),...packages].sort());
  assert.deepEqual(Object.keys(before).filter(k=>JSON.stringify(before[k])!==JSON.stringify(after[k])),['Brezi/Maps/Brezi.umap']);
  assert.deepEqual(after['Data/viewpoints.json'],before['Data/viewpoints.json']);
  assert.deepEqual(delta,{changedOriginalFiles:['Brezi/Maps/Brezi.umap'],newOwnedPackages:[...packages].sort(),originalContentFiles:4071,savedContentFiles:4086,newPackages:15});
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source),filename='garden-periwinkle-native-report-r2.json';
  const previous=fileURLToPath(new URL('exterior-editor-source-r24.mjs',import.meta.url));assert.equal(await sha(previous),R24_SHA);
  if(!names.includes(filename)){
    assert(!/^exterior-20261002-r36/.test(path.basename(source))&&!names.some(n=>/^garden-periwinkle-native-report/.test(n)),'Running/failed/unknown R36 cannot delegate');
    const e=await loadR24(source,{root});e.additionalClosureFiles.push(previous);return e;
  }
  assert(hashLike(REPORT_SHA)&&hashLike(ROOT_AUDIT_SHA)&&hashLike(CHECKER_SHA)&&Number.isInteger(NATIVE_PID)&&Number.isInteger(TERMINAL_PIN_COUNT),'Actual closed R36 process/checker/root byte closure is required');
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r36b'));validatePeriwinkleReportNames(names);
  const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,filename),r=await read(receiptPath),closure=new Set([receiptPath,previous]);
  validatePeriwinkleHeader(r,{source,project});assert.equal(await sha(receiptPath),REPORT_SHA);
  async function pinned(row){assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);
    const s=await fs.lstat(row.path);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(s.size,row.bytes);assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;}
  const pj=async row=>read(await pinned(row));
  assert.equal(r.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261002-r34a/garden-fern-only-native-report.json'));
  const e=await loadR24(path.dirname(r.baseNativeReport.path),{root});assert.equal(e.nativeReceiptPath,r.baseNativeReport.path);assert.equal(e.summary.savedActors,5354);
  for(const file of e.additionalClosureFiles)closure.add(file);const baseReport=await pj(r.baseNativeReport);
  assert.equal(r.selectedPlan.path,path.join(root,'output/unreal/exterior-garden-periwinkle-20261002-r36-native-study-r2/periwinkle-native-plan-r2.json'));
  const plan=await pj(r.selectedPlan);assert.equal(plan.schemaVersion,2);assert.deepEqual(plan.repairSchema,r.repairSchema);assert.deepEqual(plan.importIdentityEvidence,r.importIdentityEvidence);assert.deepEqual(plan.immutableSourceGuard,r.immutableSourceGuard);await pinned(r.immutableSourceGuard);assert.deepEqual(plan.baseNativeReport,r.baseNativeReport);assert.deepEqual(plan.expectedCounts,COUNTS);
  assert.equal(r.sourcePreflight.path,path.join(root,'output/unreal/exterior-garden-periwinkle-20261002-r36-native-study-r2/source-preflight/source-preflight.json'));
  const pf=await pj(r.sourcePreflight);assert.equal(pf.owner,OWNER);assert.equal(pf.schemaVersion,2);assert.equal(pf.status,'source-preflight-validated-whole384-original-periwinkle-native-r2-pending');
  assert.deepEqual(pf.repairSchema,r.repairSchema);assert.deepEqual(pf.importIdentityEvidence,r.importIdentityEvidence);assert.deepEqual(pf.inputFiles,r.inputFiles);assert.equal(Object.keys(r.inputFiles).length,578);assert.equal(r.inputFiles[path.join(root,OWNER)],HELPER_SHA);
  assert.deepEqual(pf.expectedCounts,COUNTS);assert.deepEqual(pf.selectedPlan,r.selectedPlan);assert.equal(pf.tests.exitCode,0);assert.equal(pf.tests.testCount,29);await pinned(pf.tests.source);await pinned(pf.tests.log);
  assert.equal(pf.nativeExecuted,false);assert.equal(pf.gpuExecuted,false);assert.deepEqual(pf.moduleOrderWitness,r.moduleOrderWitness);
  for(const key of ['sourceProposal','baseCurrentByteAudit']){assert.deepEqual(r[key],plan[key]);await pinned(r[key]);}
  const sourceProposal=await pj(r.sourceProposal);assert.deepEqual(r.sourceGeometryDescriptor,sourceProposal.geometryDescriptor);await pinned(r.sourceGeometryDescriptor);
  assert.deepEqual(r.baseNativeProcess,plan.baseNativeProcess);assert.equal(r.baseNativeProcess.pid,21209);for(const k of ['receipt','raw','log'])await pinned(r.baseNativeProcess[k]);
  for(const[file,h]of Object.entries(r.inputFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const key of ['beforeActorWitness','expectedActorWitness','savedActorWitness','originalGardenControls','retainedGardenControlsBeforeSave','retainedGardenControlsSaved',
    'originalProtectedControlsBefore','originalProtectedControlsSaved','newSourceNativeMeasurements','importTemporaryActorInventory'])await pinned(r[key]);
  assert.deepEqual(await pj(r.beforeActorWitness),await pj(baseReport.savedActorWitness));
  const observed=await pj(r.importTemporaryActorInventory);assert.equal(observed.schema,r.repairSchema);assert.equal(observed.owner,OWNER);assert.equal(observed.schemaVersion,2);
  assert.equal(observed.scope,'ACTUAL_NEW_IMPORT_DELTA_BEFORE_ANY_BINDING_GATE');assert.equal(observed.actorLabelsUsedForSourceIdentity,false);
  assert.equal(observed.sourceMeshIdentityVerifiedAtThisCheckpoint,false);assert.equal(observed.originalR1TemporaryActorLabelsRecovered,false);
  assert.equal(observed.actorCount,6+r.observedNonrenderingImportContainers.length);assert.equal(observed.actors.length,observed.actorCount);
  assert.equal(new Set(observed.actors.map(v=>v.actor)).size,observed.actorCount);
  const byActor=new Map(observed.actors.map(v=>[v.actor,v])),containers=new Set(r.observedNonrenderingImportContainers.map(v=>v.actor));
  for(const row of observed.actors){assert.deepEqual(row.worldTransform,[[0,0,0],[0,0,0,1],[1,1,1]]);
    assert(row.attachParent===null||containers.has(row.attachParent));assert.deepEqual(row.components.map(v=>v.path).sort(),[...row.sceneComponents].sort());
    if(containers.has(row.actor)){assert.equal(row.class,'/Script/Engine.Actor');assert.deepEqual(row.primitiveComponents,[]);assert.deepEqual(row.staticMeshComponents,[]);assert(row.components.length<=1);assert.equal(row.attachParent,null);}
    else{assert(['/Script/Engine.StaticMeshActor','/Script/Engine.Actor'].includes(row.class));assert.equal(row.staticMeshComponents.length,1);assert.deepEqual(row.primitiveComponents,row.staticMeshComponents);}
  }
  for(const row of r.originalSourceNodeNativeMeshBindings){const a=byActor.get(row.actualTemporaryActor);assert(a);assert.equal(a.label,row.actualTemporaryActorLabel);
    assert.equal(a.components.find(v=>v.path===a.staticMeshComponents[0]).staticMesh,row.asset);}
  for(const row of r.observedNonrenderingImportContainers)assert.deepEqual(row,byActor.get(row.actor));
  const contentInventory=await pj(r.afterContentInventory),packages=r.newPackages.map(p=>{assert(p.startsWith('/Game/')&&!p.includes('.'));return p.replace(/^\/Game\//,'')+'.uasset';});
  validatePeriwinkleContent(e.contentInventory,contentInventory,packages,r.assetDelta);
  assert.deepEqual(r.baseContentInventory,baseReport.afterContentInventory);await pinned(r.baseContentInventory);
  assert.deepEqual(r.protectedProjectProof,baseReport.protectedProjectProof);const projectProof=await pj(r.protectedProjectProof);assert.deepEqual(projectProof,e.projectProof);
  assert.equal(r.projectClone.path,path.join(source,'garden-periwinkle-project-clone.json'));assert.deepEqual(r.projectClone,plan.projectClone);assert.deepEqual(r.projectClone,pf.projectClone);
  const clone=await pj(r.projectClone);assert.equal(clone.schema,SCHEMA);assert.equal(clone.status,'verified-original-r34a-independent-apfs-r36-clone-before-major-low-plant-replacement');
  assert.equal(clone.project,project);assert.equal(clone.sourceProject,e.project);assert.equal(clone.fileCount,4203);assert.equal(clone.contentFiles,4071);assert.equal(clone.protectedFiles,132);
  assert.equal(clone.nativeExecuted,false);assert.equal(clone.selectedPlan,null);assert.equal(clone.sourceProposal,null);assert.equal(clone.sourcePreflight,null);assert.deepEqual(clone.nativeBaseReport,r.baseNativeReport);
  const originalFiles={...Object.fromEntries(Object.entries(e.contentInventory).map(([k,v])=>['Content/'+k,v])),...projectProof},seen=new Set();assert.equal(clone.files.length,4203);
  for(const row of clone.files){const relative=path.relative(project,row.destination);assert(Object.hasOwn(originalFiles,relative)&&!seen.has(relative));seen.add(relative);assert.equal(row.source,path.join(e.project,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);assert.deepEqual({sha256:row.sha256,bytes:row.bytes},originalFiles[relative]);
    const[a,b]=await Promise.all([fs.stat(row.source),fs.lstat(row.destination)]);assert(b.isFile()&&!b.isSymbolicLink());assert(a.dev!==b.dev||a.ino!==b.ino);}
  // Initial clone membership is separate from the legitimately changed saved candidate map size.
  const views=await read(path.join(project,'Content/Data/viewpoints.json'));assert.deepEqual(views,await read(path.join(e.project,'Content/Data/viewpoints.json')));assert.equal(views.views.filter(v=>v.id==='exterior-garden').length,1);
  const checker=path.join(root,'scripts/unreal/exterior-garden-periwinkle-editor-check-r27.py');assert.equal(await sha(checker),CHECKER_SHA);closure.add(checker);
  const native=JSON.parse((await exec('python3',['-B',checker,receiptPath],{timeout:180000,maxBuffer:1024*1024})).stdout);
  assert.equal(native.nativeProcessId,NATIVE_PID);assert.equal(native.savedActors,5360);assert.equal(native.retainedOriginalGardenRoots,53);assert.equal(native.preservedR34FernRoots,36);assert.equal(native.newOriginalPeriwinkleRoots,384);
  assert.equal(native.fullNativeF32PositionUv0Uv1TopologyProofTriangles,34350);assert.equal(native.storedNewMatricesIndependentlyDecodedAfterSaveByCpuChecker,false);
  const processPath=path.join(source,'garden-periwinkle-native-r2.log.json'),terminalPath=path.join(source,'garden-periwinkle-native-r2-process.json');
  const proc=await read(processPath),terminal=await read(terminalPath);assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,NATIVE_PID);
  assert.equal(terminal.reportSha256,REPORT_SHA);assert.equal(terminal.processFile,processPath);assert.equal(terminal.processFileSha256,await sha(processPath));assert.equal(terminal.logFile,path.join(source,'garden-periwinkle-native-r2.log'));assert.equal(terminal.logSha256,await sha(terminal.logFile));
  assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+terminal.logFile])assert(proc.args.includes(arg));
  assert.equal(terminal.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(terminal.sourcePinsBeforeNative).length,TERMINAL_PIN_COUNT);assert.equal(terminal.controllerSha256BeforeNative,terminal.controllerSha256AfterNative);assert.equal(await sha(terminal.controller),terminal.controllerSha256BeforeNative);
  for(const[file,h]of Object.entries(terminal.sourcePinsBeforeNative)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const file of [processPath,terminalPath,terminal.logFile,terminal.controller])closure.add(file);
  const rootAuditPath=path.join(source,'root-native-success-byte-audit-r36b-r2.json');assert.equal(await sha(rootAuditPath),ROOT_AUDIT_SHA);closure.add(rootAuditPath);const audit=await read(rootAuditPath);
  assert.equal(audit.schema,'brezi-root-r36b-native-success-current-byte-audit-r2');
  assert.deepEqual(audit.report,{path:receiptPath,sha256:REPORT_SHA,bytes:(await fs.stat(receiptPath)).size});assert.deepEqual(audit.process,{path:terminalPath,sha256:await sha(terminalPath),bytes:(await fs.stat(terminalPath)).size});assert.deepEqual(audit.clone,r.projectClone);
  assert.equal(audit.expectedRootObservedPid,NATIVE_PID);assert.equal(audit.expectedRootObservedPins,TERMINAL_PIN_COUNT);
  assert.equal(audit.currentProjectFiles,4218);assert.equal(audit.currentContentFiles,4086);assert.equal(audit.protectedFiles,132);
  for(const key of ['all4203OriginalR34SourceFilesExact','all4202OriginalOwnFilesExceptMapExact','onlyOriginalMapAndFifteenNewOwnedPackagesChanged',
    'storedNativeFullCounterfactualEqual','storedOriginal53HeroFlowerAnd36FernControlsBeforeAfterExact'])assert.equal(audit[key],true);
  assert.deepEqual(audit.changedOriginalFiles,['Content/Brezi/Maps/Brezi.umap']);assert.deepEqual(audit.newOwnedFiles,packages.map(v=>'Content/'+v).sort());
  assert.equal(audit.sourcePinsBeforeAfterAndCurrentExact,TERMINAL_PIN_COUNT);assert.deepEqual(audit.actualStoredWitnessCounts,{actors:5360,hismComponents:2322,hismInstances:676957});
  assert.equal(audit.storedNew384SourceNativeRoots,384);assert.equal(audit.storedCompleteSourceVertexCircleChecks,1981184);assert.equal(audit.storedNativeOrderedPositionUv0Uv1Triangles,34350);
  for(const key of ['newNativeActorOrGeometryDecodeByThisCpuAudit','nativeAppearanceAccepted','fullPhotorealismAccepted'])assert.equal(audit[key],false);
  for(const key of ['byteHelper','rootAuditController'])await pinned(audit[key]);
  const w=r.nativeModuleWitness,module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');assert.equal(w.source,path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.destination,module);assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);
  for(const file of [module,w.source])await pinned({path:file,sha256:MODULE_SHA,bytes:w.bytes});
  const summary={...native,sourcePinsUnchangedAfterNative:TERMINAL_PIN_COUNT,scope:'All384 original low star roots replaced once by six original Periwinkle forms; 53 original heroes/flowers and36 ferns retained. Native saving is separate from matched appearance.'};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:e.base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:w,moduleWitnessSource:r.projectClone,
    receiptSummary:{baseNativeReport:r.baseNativeReport,selectedPlan:r.selectedPlan,sourcePreflight:r.sourcePreflight,original53HeroesFlowersAnd36FernsPreserved:true,yardIntegrationApplied:false,savedMapUnloadedReloaded:true,meshMaterialPackagesIndependentlyUnloaded:false,summary}};
}
