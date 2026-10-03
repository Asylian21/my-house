// Host checks for the opt-in source-derived neighborhood transition.
// Saved native readback is required; these checks do not accept appearance.
import assert from 'node:assert/strict';
import {validatePhotographicLawnReceipt} from './exterior-lawn-photo-source.mjs';

const OWNER='scripts/unreal/exterior-neighborhood-transition-study.py';
const KEY='context_continuous_unbuilt_ground';
const PLAN_SHA='2be538a9311282d9b8485d925fa070b3984b50cea852ea2e7406ed1699448ef5';
const GENERATOR_SHA='970c87dee543bb7c0097841d67216a52c25f4880fa982d495f21207348957a75';
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const pinned=(report,path,value)=>assert(hash(value)&&report.inputFiles[path]===value,'Missing transition input pin: '+path);

export function validateNeighborhoodTransitionReceipt(report) {
  const transition=report.neighborhoodTransition;
  if(!transition) {
    assert(!report.materials?.neighborhoodTransition,'Unbound transition material');
    return;
  }
  pinned(report,transition.plan,transition.planSha256);assert.equal(transition.planSha256,PLAN_SHA);
  const topology=transition.nativeTopologyBaseline;
  assert.equal(topology.sha256,'be3733f6e20cca1080e352d85f66bc5cd063b39632326885330582d0ba1a641a');
  pinned(report,topology.path,topology.sha256);
  for(const key of ['nativeRenderedVerified','nativeVisualAccepted','performanceAccepted'])assert.equal(transition[key],false);
  const audit=transition.validation;
  assert.equal(audit.status,'verified-source-neighborhood-transition-native-inputs');
  assert.equal(audit.owner,'scripts/unreal/exterior-neighborhood-transition-native.py');
  assert.deepEqual(audit.sourcePlan,{path:transition.plan,sha256:PLAN_SHA});
  assert.equal(audit.sourceGroundBindings,65);assert.equal(audit.groups,158);assert.equal(audit.instances,7000);
  assert.deepEqual(audit.allLodTriangles,[6351095,3487981,1584502]);
  assert.equal(audit.originalRemovalIndicesPreserved,47203);
  assert.equal(audit.originalVegetationRestoredOrMoved,0);assert.equal(audit.hiddenOriginalActors,0);
  for(const key of ['sourceGeometryAndOriginalMaterialsUnchanged','actualAllLodFullCircularCrownsAndSourceGroundChecked',
    'futureSharedMaterialMustPreserveFieldMacroAndProtectedCameraOrtho'])assert.equal(audit[key],true);
  for(const key of ['nativeVisualAccepted','performanceAccepted','surveyedLandUseBotanyOrElevation'])assert.equal(audit[key],false);
  assert.equal(audit.condition.all1048576ConditionPixelsVerified,true);
  for(const [path,value]of Object.entries(audit.inputFiles))pinned(report,path,value);
  const material=report.materials.neighborhoodTransition;
  assert.equal(material.status,'saved-continuous-unbuilt-ground-awaiting-native-reload');
  assert.equal(material.materialKey,KEY);assert.equal(material.plan,transition.plan);assert.equal(material.planSha256,PLAN_SHA);
  assert.deepEqual(material.sourcePlan,audit.sourcePlan);
  for(const key of ['original40GraphsUnchanged','fieldMacroAndProtectedCameraOrthoUnchanged'])assert.equal(material[key],true);
  for(const key of ['sourceGroundBindingsChanged','nativeAppearanceAccepted','nativeVisualAccepted','fullPhotorealismAccepted','performanceAccepted'])assert.equal(material[key],false);
  assert.equal(material.priorMaterialCount,40);assert.equal(material.finalMaterialCount,41);assert.equal(material.textureCount,74);
  let finalMaterials=41;
  if(report.materials.photographicLawn) {
    validatePhotographicLawnReceipt(report);
    finalMaterials=42;
  }
  assert.equal(Object.keys(report.materials.materials).length,finalMaterials);assert.equal(Object.keys(report.materials.textures).length,74);
  assert.deepEqual(report.materialReadback,{status:'verified-saved-exterior-materials',materials:finalMaterials,textures:74});
  const condition=material.condition;pinned(report,condition.path,condition.sha256);
  assert.equal(condition.role,'ground_condition');assert.deepEqual(condition.dimensions,[1024,1024]);
  assert.deepEqual(condition.worldCmToUvRows,[[1/36000,0,.5],[0,-1/36000,.5]]);
  assert.equal(condition.sourceLicense,'LicenseRef-Project-Authored');
  assert(condition.sourcePage.endsWith('/'+OWNER));pinned(report,condition.sourcePage,GENERATOR_SHA);
  assert.equal(condition.sRGB,false);assert.equal(condition.uncompressedRgba8,true);
  assert.equal(condition.compressionNonePropertyExposed,false);assert(!Object.hasOwn(condition,'compressionNone'));
  assert.equal(condition.uncompressedFormatBasis,'TC_VectorDisplacementmap -> NameBGRA8 (UE5.8 native source)');
  assert.equal(condition.compressionSettings,'TC_VECTOR_DISPLACEMENTMAP');assert.equal(condition.addressMode,'clamp');
  assert.equal(condition.mipGenSettings,'TMGS_FROM_TEXTURE_GROUP');assert.equal(condition.ordinaryMips,true);
  assert.equal(condition.automaticViewMipBias,false);assert.equal(condition.sourceEncodingOverride,'None');assert.equal(condition.sourceEncodingReadback,'TSE_NONE');
  const textures=Object.values(report.materials.textures).filter(row=>row.role==='ground_condition');
  assert.equal(textures.length,1);
  for(const [key,value]of Object.entries({sourcePath:condition.path,sourceSha256:condition.sha256,sourceLicense:condition.sourceLicense,
    sourcePage:condition.sourcePage,addressMode:'clamp',sourceEncodingOverride:'None',sourceEncodingReadback:'TSE_NONE',width:1024,height:1024}))assert.equal(textures[0][key],value);
  const saved=transition.savedReadback;
  assert.equal(saved.status,'verified-saved-neighborhood-transition');assert.equal(saved.instances,7000);
  for(const key of ['allNewVisualsNoCollision','sourceGroundBoundsTopologyAndOriginVerified','sourceTransformsComparedAfterReload'])assert.equal(saved[key],true);
  for(const key of ['nativeVisualAccepted','performanceAccepted'])assert.equal(saved[key],false);
  for(const [key,limit]of [['maximumPositionErrorCm',.002],['maximumScaleError',1e-6],['maximumQuaternionErrorSignEquivalent',2e-6]])
    assert(Number.isFinite(saved[key])&&saved[key]>=0&&saved[key]<=limit,'Transition saved transform bound failed: '+key);
  assert.equal(saved.materialBindings.length,65);assert.equal(new Set(saved.materialBindings.map(row=>row.sourceMeshId)).size,65);
  assert.equal(saved.groupIds.length,158);assert.equal(new Set(saved.groupIds).size,158);
}

export function validateNeighborhoodTransitionPlan(report,plan,context,basis,topology) {
  validateNeighborhoodTransitionReceipt(report);
  const transition=report.neighborhoodTransition,material=report.materials.neighborhoodTransition,saved=transition.savedReadback;
  assert.equal(plan.owner,OWNER);assert.equal(plan.generatorSha256,GENERATOR_SHA);
  assert.equal(plan.status,'source-only-neighborhood-transition-study-native-pending');
  assert.deepEqual(plan.activeDesign,report.activeDesign);
  assert.equal(plan.housePlacement.streetSetbackMm,3000);assert.equal(plan.housePlacement.eastSetbackMm,3000);
  for(const value of Object.values(plan.preservation))assert.equal(value,true);
  assert.equal(plan.nativeVisualAccepted,false);assert.equal(plan.performanceAccepted,false);
  assert.deepEqual(transition.sourceMaterialBindings,plan.materialBindingProposal);
  assert.equal(plan.materialBindingProposal.length,65);assert.equal(plan.groups.length,158);assert.equal(plan.transitionPlacements.length,7000);
  assert.equal(material.condition.path,plan.conditionTexture.path);assert.equal(material.condition.sha256,plan.conditionTexture.sha256);
  assert.deepEqual(material.condition.worldCmToUvRows,plan.conditionTexture.worldCmToUvRows);
  assert.deepEqual(saved.groupIds,plan.groups.map(row=>row.id));
  assert.equal(topology.status,'VERIFIED_ACTUAL_ORIGINAL_AND_PROPOSED_NATIVE_GROUND_TOPOLOGY_IDENTICAL');
  assert.equal(topology.all65ActualNativeTopologyVertexCountsAndBoundsUnchanged,true);
  assert.equal(topology.allSourceDescriptionTriangleCountsExact,true);
  assert.equal(topology.sourceTriangles,3671);assert.equal(topology.descriptionTriangles,3671);assert.equal(topology.renderTriangles,3613);
  assert.equal(topology.rows.length,65);assert.equal(new Set(topology.rows.map(row=>row.sourceMeshId)).size,65);
  const sourceMeshes=new Map(context.meshes.map(row=>[row.id,row]));
  for(const row of plan.materialBindingProposal) {
    assert(['context_meadow','context_fallow'].includes(row.expectedMaterialKey));assert.equal(row.proposedSharedMaterialKey,KEY);
    assert.equal(row.sourceVerticesAndIndicesUnchanged,true);assert(hash(row.sourceGeometrySha256));
    const actual=saved.materialBindings.find(item=>item.sourceMeshId===row.sourceMeshId),source=sourceMeshes.get(row.sourceMeshId);
    assert(source);assert.equal(source.material,row.expectedMaterialKey);
    assert.equal(actual.actor,report.geometry.actors[row.sourceMeshId]);assert.equal(actual.mesh,report.geometry.meshes[row.sourceMeshId]);
    assert.equal(actual.material,report.materials.materials[KEY].asset);assert.equal(actual.sourceGeometrySha256,row.sourceGeometrySha256);
    assert.equal(actual.triangles,source.indices.length/3);
    const original=topology.rows.find(item=>item.sourceMeshId===row.sourceMeshId);assert(original);
    assert.equal(original.sourceGeometrySha256,row.sourceGeometrySha256);
    assert.equal(original.sourceTriangles,actual.triangles);assert.equal(original.descriptionTriangles,actual.triangles);
    assert.equal(actual.renderTriangles,original.renderTriangles);
    assert.equal(actual.descriptionVertices,original.descriptionVertices);assert.equal(actual.descriptionVertices,source.verticesCm.length);
  }
  let count=0;
  for(const group of plan.groups) {
    assert(group.id.startsWith('EX_transition_'));assert(['grass_medium_02_a','grass_medium_02_b','grass_medium_02_c'].includes(group.meshId));
    assert.equal(group.collision,'NoCollision');assert.equal(group.castShadow,false);assert.equal(group.qualityDetail,false);
    assert.equal(group.cullStartCm,3200);assert.equal(group.cullEndCm,4000);
    const actual=report.geometry.groups[group.id],plant=report.savedPlantReadback.find(row=>row.id===group.meshId);
    assert(actual&&plant);assert.equal(actual.mesh,plant.mesh);assert.equal(actual.instances,group.instances.length);
    assert.equal(actual.qualityDetail,false);assert.equal(actual.cullStartCm,3200);assert.equal(actual.cullEndCm,4000);
    assert(hash(actual.transformsSha256));count+=actual.instances;
  }
  assert.equal(count,7000);
  assert.equal(Object.keys(basis.materials.materials).length,40);assert.equal(Object.keys(basis.materials.textures).length,73);
  for(const [key,original]of Object.entries(basis.materials.materials)) {
    const actual=report.materials.materials[key];assert(actual);
    assert.equal(actual.graphSha256,original.graphSha256,'Original transition material graph changed: '+key);
    assert.deepEqual(actual.recipe,original.recipe,'Original transition material recipe changed: '+key);
  }
  for(const [key,original]of Object.entries(basis.materials.textures))assert.deepEqual(report.materials.textures[key],original,'Original texture changed: '+key);
}
