// Constructed source/native-schema fixtures. These tests do not run Unreal,
// save native geometry, measure appearance or prove an R16 native import.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,mkdtemp,writeFile,rm} from 'node:fs/promises';
import {resolve} from 'node:path';
import test from 'node:test';
import {validateContinuousMeadowPlan,validateContinuousMeadowReceipt,CONTINUOUS_MEADOW_PLAN_SHA} from '../scripts/unreal/exterior-meadow-continuous-source.mjs';

const root=resolve(import.meta.dirname,'..'),directory=resolve(root,'output/unreal/exterior-meadow-continuous-20261001-r1-study');
const read=async p=>JSON.parse(await readFile(p)),hash=b=>createHash('sha256').update(b).digest('hex');
const planPath=resolve(directory,'continuous-meadow-plan.json'),plan=await read(planPath);
const sourceReceipt=await read(resolve(directory,'source-validation.json'));
const restored=await read(resolve(directory,plan.restoredGroupsFile)),subsets=await read(resolve(directory,plan.cultivatedSubsetsFile));
const basis=await read(resolve(root,'output/unreal/exterior-20261001-r14a/exterior-import-report.json'));
const topologyPath=basis.neighborhoodTransition.nativeTopologyBaseline.path,topology=await read(topologyPath);
const audit={owner:'scripts/unreal/exterior-meadow-continuous-native.py',status:'VERIFIED_STDLIB_CONTINUOUS_LAYOUT_SOURCE_INPUTS_NATIVE_PENDING',
  sourceInputsValidated:true,nativeGeometryDecodedOrSaved:false,nativeApplied:false,nativeAppearanceAccepted:false,fullPhotorealismAccepted:false,
  performanceAccepted:false,domainBooleanUnionRecomputedHere:false,restoredGroups:164,restoredInstances:39834,retainedHeightOnlyOverrides:219807,
  omittedUnbuiltSoilTriangles:103392,retainedCultivatedSoilTriangles:2801,neighborhoodMeshes:143,neighborhoodTriangles:142105,materialBindings65:65,
  sourcePrototypeLodsDecoded:12,allChangedWhole141mmCrownsRechecked:259641,soilTriangleCentroidMembershipRechecked:106193,
  retainedArrayCounts:{meadowBladePlacements:348231,meadowUnderstoryPlacements:73941,groundCoverPlacements:2547},
  restoredAllLodSourceTriangles:[10197504,2549376,956016],nativeOriginalAssetLookupEvidence:'PINNED_HISTORICAL_R14_RECEIPT_ONLY',
  domainEvidence:'PINNED_GEOS_SOURCE_PREFLIGHT_PLUS_STDLIB_PER_CROWN_MASK_CHECKS',
  soilPartitionEvidence:'STDLIB_ORIGINAL_GROUND_CENTROID_MEMBERSHIP_AND_EXACT_SOURCE_TRIANGLE_ORDINALS',
  authenticPrivateRoadBuildingMasksRechecked:true,worldHeightFieldRecomputedHere:true,fourDiagnosticPngStructuresValidated:true,
  originalPositionsYawRadiusAndGround65Preserved:true,allSevenCultivatedSourceRowsPreserved:true,oldTransitionPilotClaimsAreHistoricalReferencesOnly:true};
const template=structuredClone(basis);
Object.assign(template.inputFiles,plan.inputFiles);
for(const file of Object.values(sourceReceipt.files))template.inputFiles[file.path]=file.sha256;
template.inputFiles[resolve(directory,'source-validation.json')]=hash(await readFile(resolve(directory,'source-validation.json')));
for(const relative of ['scripts/unreal/exterior-meadow-continuous-study.py','scripts/unreal/exterior-meadow-continuous-native.py']) {
  const path=resolve(root,relative);template.pipelineFiles[path]=hash(await readFile(path));
}
const retiredIds=[...plan.futureVisualRetirement.transitionGroupIds,...plan.futureVisualRetirement.pilotGroupIds];
for(const id of retiredIds)delete template.geometry.groups[id];
for(const [index,g] of restored.entries())template.geometry.groups[g.id]={actor:`/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.TestContinuous_${index}`,
  mesh:g.nativeMesh,instances:g.instances.length,cullStartCm:g.cullStartCm,cullEndCm:g.cullEndCm,qualityDetail:g.qualityDetail,transformsSha256:'a'.repeat(64)};
for(const id of plan.soilOverlayProposal.omitMeshIds) {delete template.geometry.meshes[id];delete template.geometry.actors[id];}
for(const key of ['neighborhoodTransition','meadowInfill']) {
  const historical=template[key];for(const field of ['savedReadback','savedGroups','savedInstances','groupIds'])delete historical[field];
  Object.assign(historical,{groupsRetiredByContinuousMeadow:true,appliedGroups:0,appliedInstances:0});
}
template.savedGeometryReadback={meshCount:547,groupCount:1980,instanceCount:632026,allNewVisualsNoCollision:true};
template.continuousMeadow={plan:planPath,planSha256:CONTINUOUS_MEADOW_PLAN_SHA,audit,nativeRenderedVerified:false,
  nativeAppearanceAccepted:false,fullPhotorealismAccepted:false,performanceAccepted:false,
  savedReadback:{status:'verified-saved-continuous-meadow-layout',restoredGroups:164,restoredInstances:39834,heightOnlyOverrides:219807,
    soilTrianglesOmitted:103392,cultivatedRetained:2801,bindings:65,allNewVisualsNoCollision:true,
    orderedNativeTransformsVerifiedAfterReload:true,sourceGroundBoundsTopologyAndOriginVerified:true,retiredGroupsAbsent:true,
    nativeAppearanceAccepted:false,fullPhotorealismAccepted:false,performanceAccepted:false,
    maximumPositionErrorCm:.001,maximumScaleError:1e-7,maximumQuaternionErrorSignEquivalent:1e-7,
    groupIds:restored.map(g=>g.id),retiredGroupIds:retiredIds,materialBindings:structuredClone(basis.neighborhoodTransition.savedReadback.materialBindings),
    soilSubsets:subsets.map(s=>({sourceMeshId:s.id,actor:template.geometry.actors[s.id],mesh:template.geometry.meshes[s.id],
      material:template.materials.materials.context_soil_exposure.asset,
      sourceGeometrySha256:plan.soilOverlayProposal.triangles.find(r=>r.sourceMeshId===s.id).replacementMeshSha256,
      triangles:s.indices.length/3,descriptionVertices:new Set(s.indices).size,triangleConnectivityWindingVerified:true,maximumPositionErrorCm:.001}))}};
const fixture=()=>structuredClone(template);

test('source fixture accepts frozen continuous layout and truthful retired history with 1980 groups/632026 instances',async()=>{
  assert.deepEqual(await validateContinuousMeadowPlan(fixture(),plan),{restoredGroups:164,restoredInstances:39834,retiredGroups:259,
    retiredInstances:40483,remainingGroups:1980,remainingInstances:632026,nativeAppearanceAccepted:false,performanceAccepted:false});
  assert.equal(topology.rows.length,65);
});

test('self-consistently rehashed malformed plan cannot replace the frozen typed branch',async()=>{
  const temporary=await mkdtemp(resolve(root,'output/unreal/continuous-node-source-fixture-'));
  try {
    const altered=structuredClone(plan);altered.owner='scripts/unreal/exterior-meadow-infill-pilot.py';
    const path=resolve(temporary,'continuous-meadow-plan.json'),bytes=Buffer.from(JSON.stringify(altered));await writeFile(path,bytes);
    const r=fixture();r.continuousMeadow.plan=path;r.continuousMeadow.planSha256=hash(bytes);r.inputFiles[path]=hash(bytes);
    await assert.rejects(validateContinuousMeadowPlan(r,altered),/Continuous frozen plan hash differs/);
    const originalHash=fixture();await assert.rejects(validateContinuousMeadowPlan(originalHash,altered),/exterior-meadow-continuous-study/);
  } finally {await rm(temporary,{recursive:true,force:true});}
});

test('retired transition/pilot cannot retain old saved counts or coexist with current native geometry',()=>{
  for(const mutate of [r=>{r.neighborhoodTransition.savedReadback=structuredClone(basis.neighborhoodTransition.savedReadback);},
    r=>{r.meadowInfill.savedGroups=101;},r=>{r.neighborhoodTransition.appliedInstances=7000;},
    r=>{r.geometry.groups[retiredIds[0]]=structuredClone(basis.geometry.groups[retiredIds[0]]);}]) {
    const r=fixture();mutate(r);assert.throws(()=>validateContinuousMeadowReceipt(r));
  }
});

test('native restored group counts, ordered membership and remaining populations cannot be exchanged',async()=>{
  const r=fixture();r.geometry.groups[restored[0].id].instances+=1;r.geometry.groups[restored[1].id].instances-=1;
  await assert.rejects(validateContinuousMeadowPlan(r,plan),/source population differs/);
  const changed=fixture();[changed.continuousMeadow.savedReadback.groupIds[0],changed.continuousMeadow.savedReadback.groupIds[1]]=
    [changed.continuousMeadow.savedReadback.groupIds[1],changed.continuousMeadow.savedReadback.groupIds[0]];
  await assert.rejects(validateContinuousMeadowPlan(changed,plan),/ordered restored group membership differs/);
});

test('CBB setbacks, typed source pins and source/native acceptance boundaries remain explicit',()=>{
  for(const mutate of [r=>{r.setbacksMm.east=2500;},r=>{delete r.inputFiles[planPath];},
    r=>{r.continuousMeadow.audit.nativeGeometryDecodedOrSaved=true;},r=>{r.continuousMeadow.performanceAccepted=true;},
    r=>{r.continuousMeadow.savedReadback.maximumScaleError=Infinity;}]) {
    const r=fixture();mutate(r);assert.throws(()=>validateContinuousMeadowReceipt(r));
  }
});

test('soil subsets require used-face proof while allowing native unused-vertex compaction',async()=>{
  const r=fixture();r.continuousMeadow.savedReadback.soilSubsets[0].triangleConnectivityWindingVerified=false;
  await assert.rejects(validateContinuousMeadowPlan(r,plan));
  const changed=fixture();changed.continuousMeadow.savedReadback.soilSubsets[0].sourceGeometrySha256='b'.repeat(64);
  await assert.rejects(validateContinuousMeadowPlan(changed,plan));
});

test('65 saved ground bindings and unchanged material graphs cannot borrow historical membership verification',async()=>{
  const r=fixture();r.continuousMeadow.savedReadback.materialBindings[0].triangles+=1;
  await assert.rejects(validateContinuousMeadowPlan(r,plan));
  const changed=fixture();changed.materials.materials.context_meadow.graphSha256='b'.repeat(64);
  await assert.rejects(validateContinuousMeadowPlan(changed,plan),/changed original native material graphs/);
});
