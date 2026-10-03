// R2 constructed source/native-schema fixtures from stored R14/R15 witnesses.
// These tests do not run Unreal,
// save native geometry, measure appearance or prove an R16 native import.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,mkdtemp,writeFile,rm} from 'node:fs/promises';
import {resolve} from 'node:path';
import test from 'node:test';
import {validateContinuousMeadowPlan,validateContinuousMeadowReceipt,CONTINUOUS_MEADOW_PLAN_SHA} from '../scripts/unreal/exterior-meadow-continuous-source-r2.mjs';

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
const nativeBasis=await read(resolve(root,'output/unreal/exterior-20261001-r15a/exterior-import-report.json'));
const template=structuredClone(nativeBasis);
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


test('R2 source fixture accepts only the consumed9-master map and all23 fullness groups78 unchanged transforms',async()=>{
  assert.deepEqual(await validateContinuousMeadowPlan(fixture(),plan),{restoredGroups:164,restoredInstances:39834,retiredGroups:259,
    retiredInstances:40483,remainingGroups:1980,remainingInstances:632026,nativeAppearanceAccepted:false,performanceAccepted:false});
  assert.equal(template.canopyReplacement.groupIds.length,23);
  assert.equal(template.canopyReplacement.groupIds.reduce((n,id)=>n+template.geometry.groups[id].instances,0),78);
});

test('fullness owner/status and selected consumed source pins cannot be exchanged',async()=>{
  const malformed=fixture();malformed.canopyReplacement.validation.status='verified-source-grove-canopy-growth';
  await assert.rejects(validateContinuousMeadowPlan(malformed,plan),/verified-source-grove-canopy-fullness/);
  const changed=fixture();changed.canopyReplacement.planSha256='b'.repeat(64);changed.inputFiles[changed.canopyReplacement.plan]='b'.repeat(64);
  await assert.rejects(validateContinuousMeadowPlan(changed,plan),/consumed fullness plan/);
  const claimed=fixture();claimed.canopyReplacement.validation.nativeVerified=true;
  await assert.rejects(validateContinuousMeadowPlan(claimed,plan),/false source\/acceptance flag/);
});

test('self-consistently rehashed9-pair map and changed126 prefix cannot replace the frozen full135 source',async()=>{
  const temporary=await mkdtemp(resolve(root,'output/unreal/continuous-node-source-r2-fixture-'));
  try {
    const original=await read(template.plantGeometryManifest);
    for(const [name,mutate] of [
      ['swapped-map',m=>{[m.meshes[126].sourceGrowthMasterId,m.meshes[127].sourceGrowthMasterId]=[m.meshes[127].sourceGrowthMasterId,m.meshes[126].sourceGrowthMasterId];}],
      ['changed-prefix',m=>{m.meshes[0].heightCm+=1;}],
    ]) {
      const altered=structuredClone(original);mutate(altered);
      const path=resolve(temporary,name+'.json'),bytes=Buffer.from(JSON.stringify(altered));await writeFile(path,bytes);
      const r=fixture();r.plantGeometryManifest=path;r.inputFiles[path]=hash(bytes);
      await assert.rejects(validateContinuousMeadowPlan(r,plan),/full135 source library differs/);
    }
  } finally {await rm(temporary,{recursive:true,force:true});}
});

test('all23 mapped native mesh identities, counts, culls, detail and ordered transforms are mandatory',async()=>{
  const ids=template.canopyReplacement.groupIds;
  for(const mutate of [
    r=>{r.geometry.groups[ids[0]].mesh=basis.geometry.groups[basis.canopyReplacement.groupIds[0]].mesh;},
    r=>{r.geometry.groups[ids[0]].instances+=1;r.geometry.groups[ids[1]].instances-=1;},
    r=>{r.geometry.groups[ids[0]].cullEndCm=9000;},
    r=>{r.geometry.groups[ids[0]].qualityDetail=true;},
    r=>{r.geometry.groups[ids[0]].transformsSha256='b'.repeat(64);},
    r=>{[r.canopyReplacement.groupIds[0],r.canopyReplacement.groupIds[1]]=[r.canopyReplacement.groupIds[1],r.canopyReplacement.groupIds[0]];},
  ]) {
    const r=fixture();mutate(r);await assert.rejects(validateContinuousMeadowPlan(r,plan),/Continuous/);
  }
});

test('unrelated native groups cannot use the23-pair exception to change their identity, mesh or ordered transforms',async()=>{
  const id=Object.keys(template.geometry.groups).find(id=>id.startsWith('EX_regional_')&&!template.canopyReplacement.groupIds.includes(id));
  assert(id);
  for(const mutate of [
    r=>{r.geometry.groups[id].transformsSha256='b'.repeat(64);},
    r=>{r.geometry.groups[id].mesh=r.geometry.groups[r.canopyReplacement.groupIds[0]].mesh;},
    r=>{r.geometry.groups[id+'_canopy_fullness_forged']=r.geometry.groups[id];delete r.geometry.groups[id];},
  ]) {
    const r=fixture();mutate(r);await assert.rejects(validateContinuousMeadowPlan(r,plan),/Continuous/);
  }
});

test('the fullness mapping preserves strict zero-applied retired transition and pilot receipt boundaries',()=>{
  for(const mutate of [r=>{r.neighborhoodTransition.savedReadback=structuredClone(basis.neighborhoodTransition.savedReadback);},
    r=>{r.meadowInfill.appliedInstances=33483;},r=>{r.geometry.groups[retiredIds[0]]=structuredClone(basis.geometry.groups[retiredIds[0]]);}]) {
    const r=fixture();mutate(r);assert.throws(()=>validateContinuousMeadowReceipt(r));
  }
});
