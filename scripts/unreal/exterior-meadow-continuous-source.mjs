// Typed host checks for one continuous meadow layout. Source morphology and
// historical assets remain distinct from current saved native membership.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createReadStream} from 'node:fs';
import {readFile} from 'node:fs/promises';
import {isAbsolute,relative,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT=resolve(fileURLToPath(new URL('../..',import.meta.url)));
export const CONTINUOUS_MEADOW_OWNER='scripts/unreal/exterior-meadow-continuous-study.py';
export const CONTINUOUS_MEADOW_STATUS='MEASURED_CONTINUOUS_MEADOW_LAYOUT_SOURCE_ONLY_NATIVE_PENDING';
export const CONTINUOUS_MEADOW_PLAN_SHA='cd199caee2846741049151887f6546ba0279e4beef1ce6bb5e36430085f7067d';
const GENERATOR_SHA='498426d153f8f5c2c0215a455e8bb2f919e228233d6e8e5c9d0c7bcdddb10518';
const HELPER='scripts/unreal/exterior-meadow-continuous-native.py';
const HELPER_SHA='b802493adfe5f87172b928bddf5c781b06cfad3c558f0c42cdf0b8fbcd0bf33a';
const STUDY='output/unreal/exterior-meadow-continuous-20261001-r1-study';
const MATERIAL='context_continuous_unbuilt_ground';
const DESIGN={variant:'C',heatingLayout:'B',livingLayout:'B'};
const SOURCE_FILES={
  'continuous-meadow-plan.json':CONTINUOUS_MEADOW_PLAN_SHA,
  'cultivated-soil-subsets.json':'a6defa3fcfcd95da79cfc2a9539689f80194ae6adce09d685181baeb6651e75c',
  'restored-roots.json':'a45b52d619ceb81c02db627aaffe30a3f52f32c02758a9c8f10feb20e26516cd',
  'restored-groups.json':'abd3a40ff5e2d37dd25f982b728cd976c48f7896fc6715fb1875f8513df5a1be',
  'retained-height-overrides.json':'011bf35de2b3b2a4eec362601c7627ecf2e3215a087baa35f2d2a73490800905',
  'source-validation.json':'7c7a742e17da1ad8a1f79da4822ca86be8c6e505c5c9329c01a4e21348971c34',
  'planview-comparison.png':'c907102a3773d909cebb4025bedbfc11a554182ee5090ebf0db5d1955e590826',
  'soil-triangle-mask.png':'e222355d194dce69f6eb465ac9eb7ca2e7e0925f1ccd69e8e43b972d78e9db09',
  'restored-root-map.png':'f7379843e91291f2ee9b13a563da8b18dfe36d700cc9109e29676f5f840a6860',
  'continuous-growth-field.png':'4a8dbef2f3bd08ae208d80074cc58e4fd3d11b96c32fada57b54275fc6ede3fe',
};
const isHash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const read=async p=>JSON.parse(await readFile(p));
async function sha(path) {
  const h=createHash('sha256');for await(const chunk of createReadStream(path))h.update(chunk);return h.digest('hex');
}
function pin(path,value,report,root=ROOT) {
  assert(isAbsolute(path)&&path===resolve(path),'Continuous pin path must be canonical');
  const local=relative(root,path);assert(local&&!local.startsWith('../')&&!isAbsolute(local),'Continuous pin escaped repository');
  assert(isHash(value)&&report.inputFiles?.[path]===value,'Continuous input pin missing or malformed: '+path);
}
async function readPin(path,value,report,root) {
  pin(path,value,report,root);assert.equal(await sha(path),value,'Continuous source pin drift: '+path);return read(path);
}
function falseFlags(record,keys) {for(const key of keys)assert.equal(record[key],false,'Continuous false source/acceptance flag differs: '+key);}
function transformBounds(saved) {
  for(const [key,limit] of [['maximumPositionErrorCm',.002],['maximumScaleError',1e-6],['maximumQuaternionErrorSignEquivalent',2e-6]])
    assert(Number.isFinite(saved[key])&&saved[key]>=0&&saved[key]<=limit,'Continuous saved transform bound failed: '+key);
}
function retired(receipt,label) {
  assert(receipt,'Continuous missing explicit retired '+label+' history');
  assert.equal(receipt.groupsRetiredByContinuousMeadow,true);
  assert.equal(receipt.appliedGroups,0);assert.equal(receipt.appliedInstances,0);
  for(const key of ['savedReadback','savedGroups','savedInstances'])assert(!Object.hasOwn(receipt,key),
    'Continuous retired '+label+' cannot borrow saved old membership: '+key);
  if(Object.hasOwn(receipt,'groupIds'))assert.deepEqual(receipt.groupIds,[],'Continuous retired membership must be historical, not applied');
}

export function validateContinuousMeadowReceipt(report) {
  const continuous=report.continuousMeadow;
  if(!continuous) {
    assert(!report.neighborhoodTransition?.groupsRetiredByContinuousMeadow&&!report.meadowInfill?.groupsRetiredByContinuousMeadow,
      'Retired visuals require a continuous meadow receipt');return;
  }
  pin(continuous.plan,continuous.planSha256,report);
  assert.equal(continuous.planSha256,CONTINUOUS_MEADOW_PLAN_SHA,'Continuous frozen plan hash differs');
  falseFlags(continuous,['nativeRenderedVerified','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted']);
  const audit=continuous.audit;assert.equal(audit.owner,HELPER);
  assert.equal(audit.status,'VERIFIED_STDLIB_CONTINUOUS_LAYOUT_SOURCE_INPUTS_NATIVE_PENDING');
  assert.equal(audit.sourceInputsValidated,true);
  falseFlags(audit,['nativeGeometryDecodedOrSaved','nativeApplied','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted',
    'domainBooleanUnionRecomputedHere']);
  for(const [key,value] of Object.entries({restoredGroups:164,restoredInstances:39834,retainedHeightOnlyOverrides:219807,
    omittedUnbuiltSoilTriangles:103392,retainedCultivatedSoilTriangles:2801,neighborhoodMeshes:143,neighborhoodTriangles:142105,
    materialBindings65:65,sourcePrototypeLodsDecoded:12,allChangedWhole141mmCrownsRechecked:259641,soilTriangleCentroidMembershipRechecked:106193}))
    assert.equal(audit[key],value,'Continuous source inventory differs: '+key);
  assert.deepEqual(audit.retainedArrayCounts,{meadowBladePlacements:348231,meadowUnderstoryPlacements:73941,groundCoverPlacements:2547});
  assert.deepEqual(audit.restoredAllLodSourceTriangles,[10197504,2549376,956016]);
  assert.equal(audit.nativeOriginalAssetLookupEvidence,'PINNED_HISTORICAL_R14_RECEIPT_ONLY');
  assert.equal(audit.domainEvidence,'PINNED_GEOS_SOURCE_PREFLIGHT_PLUS_STDLIB_PER_CROWN_MASK_CHECKS');
  assert.equal(audit.soilPartitionEvidence,'STDLIB_ORIGINAL_GROUND_CENTROID_MEMBERSHIP_AND_EXACT_SOURCE_TRIANGLE_ORDINALS');
  for(const key of ['authenticPrivateRoadBuildingMasksRechecked','worldHeightFieldRecomputedHere','fourDiagnosticPngStructuresValidated',
    'originalPositionsYawRadiusAndGround65Preserved','allSevenCultivatedSourceRowsPreserved','oldTransitionPilotClaimsAreHistoricalReferencesOnly'])
    assert.equal(audit[key],true,key);
  const saved=continuous.savedReadback;assert.equal(saved.status,'verified-saved-continuous-meadow-layout');
  for(const [key,value] of Object.entries({restoredGroups:164,restoredInstances:39834,heightOnlyOverrides:219807,
    soilTrianglesOmitted:103392,cultivatedRetained:2801,bindings:65}))assert.equal(saved[key],value,'Continuous saved inventory differs: '+key);
  for(const key of ['allNewVisualsNoCollision','orderedNativeTransformsVerifiedAfterReload','sourceGroundBoundsTopologyAndOriginVerified','retiredGroupsAbsent'])
    assert.equal(saved[key],true,key);
  falseFlags(saved,['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted']);transformBounds(saved);
  for(const [key,count] of [['groupIds',164],['retiredGroupIds',259]])assert(Array.isArray(saved[key])&&saved[key].length===count&&new Set(saved[key]).size===count,
    'Continuous saved membership inventory differs: '+key);
  assert(Array.isArray(saved.materialBindings)&&saved.materialBindings.length===65&&new Set(saved.materialBindings.map(r=>r.sourceMeshId)).size===65);
  assert(Array.isArray(saved.soilSubsets)&&saved.soilSubsets.length===4&&new Set(saved.soilSubsets.map(r=>r.sourceMeshId)).size===4);
  const groups=report.geometry.groups;
  assert.deepEqual(Object.keys(groups).filter(id=>id.startsWith('EX_meadow_restored_')).sort(),[...saved.groupIds].sort(),
    'Continuous restored group inventory incomplete or undocumented');
  for(const id of saved.retiredGroupIds)assert(!Object.hasOwn(groups,id),'Continuous retired native group is still present');
  assert(!Object.keys(groups).some(id=>id.startsWith('EX_transition_')||id.startsWith('EX_meadow_infill_')),'Continuous retired native visual survived');
  assert.equal(saved.groupIds.reduce((n,id)=>n+groups[id].instances,0),39834);
  assert.deepEqual(report.savedGeometryReadback,{meshCount:547,groupCount:1980,instanceCount:632026,allNewVisualsNoCollision:true});
  assert.equal(Object.keys(groups).length,1980);assert.equal(Object.values(groups).reduce((n,g)=>n+g.instances,0),632026);
  assert.equal(Object.keys(report.geometry.meshes).length,547);assert.equal(Object.keys(report.geometry.actors).length,544);
  retired(report.neighborhoodTransition,'transition');if(report.meadowInfill)retired(report.meadowInfill,'pilot');
  assert.deepEqual(report.activeDesign,DESIGN);assert.deepEqual(report.setbacksMm,{street:3000,east:3000});
}

export async function validateContinuousMeadowPlan(report,plan,{root=ROOT}={}) {
  validateContinuousMeadowReceipt(report);const continuous=report.continuousMeadow;assert(continuous);
  assert.equal(plan.owner,CONTINUOUS_MEADOW_OWNER);assert.equal(plan.status,CONTINUOUS_MEADOW_STATUS);
  assert.equal(plan.generatorSha256,GENERATOR_SHA);assert.equal(plan.schemaVersion,1);
  assert.deepEqual(plan.activeDesign,DESIGN);assert.equal(plan.housePlacement.streetSetbackMm,3000);assert.equal(plan.housePlacement.eastSetbackMm,3000);
  falseFlags(plan,['nativeApplied','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','integrationAuthorized','sweepOrGridOfCandidates']);
  assert.equal(plan.candidateCount,1);
  assert.deepEqual(plan,await readPin(continuous.plan,continuous.planSha256,report,root),'Continuous caller plan differs from frozen source');
  for(const [path,value] of Object.entries(plan.inputFiles)) {
    pin(path,value,report,root);assert.equal(await sha(path),value,'Continuous original authoring input drift: '+path);
  }
  for(const [name,value] of Object.entries(SOURCE_FILES)) {
    const path=resolve(root,STUDY,name);pin(path,value,report,root);assert.equal(await sha(path),value,'Continuous frozen sidecar drift: '+name);
  }
  for(const file of [CONTINUOUS_MEADOW_OWNER,HELPER]) {
    const path=resolve(root,file),expected=report.pipelineFiles?.[path];assert(isHash(expected),'Continuous pipeline source unpinned');
    assert.equal(await sha(path),expected,'Continuous native pipeline source drift');
    if(file===CONTINUOUS_MEADOW_OWNER)assert.equal(expected,GENERATOR_SHA);
    if(file===HELPER)assert.equal(expected,HELPER_SHA);
  }
  const groups=await read(resolve(root,STUDY,plan.restoredGroupsFile));const subsets=await read(resolve(root,STUDY,plan.cultivatedSubsetsFile));
  const saved=continuous.savedReadback;
  assert.deepEqual(saved.groupIds,groups.map(g=>g.id),'Continuous ordered restored group membership differs');
  const history=plan.futureVisualRetirement;assert.deepEqual(saved.retiredGroupIds,[...history.transitionGroupIds,...history.pilotGroupIds]);
  for(const group of groups) {
    const actual=report.geometry.groups[group.id];assert.equal(actual.instances,group.instances.length,'Continuous group source population differs');
    assert.equal(actual.mesh,group.nativeMesh);assert.equal(actual.cullStartCm,group.cullStartCm);assert.equal(actual.cullEndCm,group.cullEndCm);
    assert.equal(actual.qualityDetail,group.qualityDetail);assert(isHash(actual.transformsSha256));
    for(const [key,value] of Object.entries({collision:'NoCollision',canEverAffectNavigation:false,densityScaling:true}))
      if(Object.hasOwn(actual,key))assert.equal(actual[key],value);
    const prototype=report.nativeMeadow.prototypes[group.meshId];assert(prototype);assert.equal(prototype.mesh,group.nativeMesh);assert.equal(prototype.material,group.nativeMaterial);
  }
  for(const id of plan.soilOverlayProposal.omitMeshIds)assert(!Object.hasOwn(report.geometry.meshes,id)&&!Object.hasOwn(report.geometry.actors,id),
    'Continuous omitted unbuilt soil still has native geometry');
  for(const subset of subsets) {
    const row=saved.soilSubsets.find(r=>r.sourceMeshId===subset.id),source=plan.soilOverlayProposal.triangles.find(r=>r.sourceMeshId===subset.id);
    assert.equal(row.actor,report.geometry.actors[subset.id]);assert.equal(row.mesh,report.geometry.meshes[subset.id]);
    assert.equal(row.material,report.materials.materials.context_soil_exposure.asset);assert.equal(row.sourceGeometrySha256,source.replacementMeshSha256);
    assert.equal(row.triangles,subset.indices.length/3);assert.equal(row.triangleConnectivityWindingVerified,true);
    assert(Number.isInteger(row.descriptionVertices)&&row.descriptionVertices>0&&row.descriptionVertices<=subset.verticesCm.length,
      'Continuous native compacted subset vertex count differs');
    assert(Number.isFinite(row.maximumPositionErrorCm)&&row.maximumPositionErrorCm>=0&&row.maximumPositionErrorCm<=.002);
  }
  const transition=report.neighborhoodTransition;assert.deepEqual(transition.sourceMaterialBindings,plan.materialBindingProposal);
  assert.equal(transition.plan,history.transitionPlan);assert.equal(transition.planSha256,plan.inputFiles[history.transitionPlan]);
  pin(transition.plan,transition.planSha256,report,root);
  const topology=await readPin(transition.nativeTopologyBaseline.path,transition.nativeTopologyBaseline.sha256,report,root);
  assert.equal(transition.nativeTopologyBaseline.sha256,'be3733f6e20cca1080e352d85f66bc5cd063b39632326885330582d0ba1a641a');
  for(const source of plan.materialBindingProposal) {
    const row=saved.materialBindings.find(r=>r.sourceMeshId===source.sourceMeshId),original=topology.rows.find(r=>r.sourceMeshId===source.sourceMeshId);
    assert(row&&original);assert.equal(row.actor,report.geometry.actors[source.sourceMeshId]);assert.equal(row.mesh,report.geometry.meshes[source.sourceMeshId]);
    assert.equal(row.material,report.materials.materials[MATERIAL].asset);assert.equal(row.sourceGeometrySha256,source.sourceGeometrySha256);
    assert.equal(row.triangles,original.sourceTriangles);assert.equal(row.descriptionVertices,original.descriptionVertices);assert.equal(row.renderTriangles,original.renderTriangles);
  }
  const basisPath=Object.keys(plan.inputFiles).find(path=>path.endsWith('/exterior-20261001-r14a/exterior-import-report.json'));
  const basis=await readPin(basisPath,plan.inputFiles[basisPath],report,root);
  const retiredIds=new Set(saved.retiredGroupIds);
  const expectedGroups=[...Object.keys(basis.geometry.groups).filter(id=>!retiredIds.has(id)),...saved.groupIds];
  assert.deepEqual(Object.keys(report.geometry.groups).sort(),expectedGroups.sort(),'Continuous remaining native group membership differs');
  for(const [id,before] of Object.entries(basis.geometry.groups))if(!retiredIds.has(id))
    assert.deepEqual(Object.fromEntries(Object.entries(report.geometry.groups[id]).filter(([key])=>!['actor','transformsSha256'].includes(key))),
      Object.fromEntries(Object.entries(before).filter(([key])=>!['actor','transformsSha256'].includes(key))),
      'Continuous changed remaining native group population, mesh or policy');
  const omitted=new Set(plan.soilOverlayProposal.omitMeshIds);
  for(const key of ['meshes','actors'])assert.deepEqual(Object.keys(report.geometry[key]).sort(),Object.keys(basis.geometry[key]).filter(id=>!omitted.has(id)).sort(),
    'Continuous remaining native context geometry inventory differs');
  assert.deepEqual(report.materials.materials,basis.materials.materials,'Continuous changed original native material graphs');
  assert.deepEqual(report.materials.textures,basis.materials.textures,'Continuous changed original native textures');
  assert.deepEqual(report.materialReadback,basis.materialReadback);
  if(report.meadowInfill) {
    assert.equal(report.meadowInfill.plan,basis.meadowInfill.plan);assert.equal(report.meadowInfill.planSha256,basis.meadowInfill.planSha256);
    assert.deepEqual(report.meadowInfill.audit,basis.meadowInfill.audit);pin(report.meadowInfill.plan,report.meadowInfill.planSha256,report,root);
  }
  assert.equal(plan.summary.restoredGroups,saved.restoredGroups);assert.equal(plan.summary.restoredInstances,saved.restoredInstances);
  return {restoredGroups:164,restoredInstances:39834,retiredGroups:259,retiredInstances:40483,remainingGroups:1980,remainingInstances:632026,
    nativeAppearanceAccepted:false,performanceAccepted:false};
}
