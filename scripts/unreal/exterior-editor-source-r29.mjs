// UNBOUND R38 consumer draft. Every native/plan/process/camera binding is deliberately null.
// A saved report must close before this file can become a finalized immutable consumer.
import assert from 'node:assert/strict';
import path from 'node:path';
import {validateProjectClosure} from './exterior-editor-source-r28.mjs';
export {validateProjectClosure};

export const sourceContract = Object.freeze({
  owner:'scripts/unreal/exterior-context-yard-soft-coherence-native-r38.py',
  schema:'brezi-image-selected-fixed-world-soft-ground-material-overlay-r38',schemaVersion:1,
  reportName:'soft-ground-native-report.json',
  savedStatus:'verified-saved-image-selected-fixed-world-soft-ground-material-overlay',
  directSourceName:'exterior-20261002-r38a',
  baseSourceName:'exterior-20261002-r37b',
  baseReportSha256:'f589c0d813ccfc35eba928a91a4545e03b159622fffa7ae2ba247545053c4532',
  baseReaderSha256:'71d2a5d20b60f2be5e600617c51c4c6a6e823f7437fcd64e8379c01295d29123',
  moduleSha256:'2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574',
  expectedCounts:{savedActors:5364,fullHismComponents:2325,fullHismInstances:678197,
    scopedMaterialGraphs:66,scopedTextureObjects:97,contentFiles:4103,protectedFiles:132,newPackages:3},
  plannedViews:['exterior-garden','exterior-context-yard-572063-close-r18','exterior-neighborhood-ground-r38'],
  actualNativeReport:null,actualNativePlan:null,actualSourcePreflight:null,actualNativeProcess:null,
  actualNativeProcessId:null,actualRootTerminalSourcePinCount:null,actualRootCurrentByteAudit:null,
  actualQaClone:null,actualCameraSupplement:null,actualCameraStage:null,actualSavedChecker:null,
});
const prefix='/Game/Brezi/ContextYardSoftCoherence20261002R38';
export const materialAssets={
  backdrop:`${prefix}/Materials/M_backdrop_soft_r38.M_backdrop_soft_r38`,
  substrate:`${prefix}/Materials/M_substrate_soft_r38.M_substrate_soft_r38`,
};
export const permissionAsset=`${prefix}/Textures/T_soft_permission_r38.T_soft_permission_r38`;
export const newAssets=[...Object.values(materialAssets),permissionAsset].sort();
export const actor197='/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.StaticMeshActor_197';
export const donor668='/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.StaticMeshActor_668';

export function counterfactualTwoSlots(before,targets,selectedBaseReport){
  assert.deepEqual(Object.keys(targets).sort(),['backdrop','substrate']);
  assert.equal(targets.backdrop.actor,actor197);
  assert.equal(targets.substrate.actor,selectedBaseReport.newActorMapping[donor668]);
  assert.notEqual(targets.substrate.actor,actor197);
  const expected=structuredClone(before);
  for(const role of ['backdrop','substrate']){
    const target=targets[role];
    assert.deepEqual(Object.keys(target).sort(),['actor','component','originalMaterial','originalMesh']);
    const components=expected[target.actor]?.components.filter(c=>c.name===target.component);
    assert.equal(components?.length,1);const c=components[0];
    assert.equal(c.class,'/Script/Engine.StaticMeshComponent');
    assert.equal(c.mesh,target.originalMesh);assert.equal(c.materials[0],target.originalMaterial);
    assert(Array.isArray(c.overrideMaterials));
    c.materials[0]=materialAssets[role];
    if(c.overrideMaterials.length)c.overrideMaterials[0]=materialAssets[role];
    else c.overrideMaterials=[materialAssets[role]];
  }
  return expected;
}

export function validateSoftGroundHeader(r,{source,root,nativePid}){
  assert.equal(source,path.join(root,'output/unreal',sourceContract.directSourceName));
  assert.equal(r.schema,sourceContract.schema);assert.equal(r.schemaVersion,1);assert.equal(r.owner,sourceContract.owner);
  assert.equal(r.status,sourceContract.savedStatus);assert.equal(r.output,source);
  assert.equal(r.project,path.join(source,'Project/BreziTwin'));assert(Number.isInteger(nativePid)&&nativePid>0);
  assert.equal(r.nativeProcessId,nativePid);assert.deepEqual(r.actualCounts,sourceContract.expectedCounts);
  assert.equal(r.baseNativeReport.sha256,sourceContract.baseReportSha256);
  assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});
  assert.deepEqual(r.setbacksMm,{street:3000,east:3000});
  assert.deepEqual(r.newPackages,newAssets);assert.equal(r.newActors,0);assert.equal(r.newMeshes,0);
  for(const key of ['nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged',
    'allOriginalRawMatricesMainSeedsCustomDataExact','nativeMaskPropertyPolicyVerified',
    'original64MaterialGraphsAndAuxExact','original96TextureSettingsAndPackagesExact'])assert.equal(r[key],true);
  for(const key of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified',
    'packageVerified','activeOutputPromoted','nativeGpuOutsideEquivalenceVerified','nativeGpuPixelFormatVerified',
    'nativeTexelsDecoded','freshNativeGeometryAttributeReadback','nativeNormalTangentReadbackAvailable',
    'originalGeometryAndRootMutationApisCalled','sourcePhotoPixelsEdited','additionalSeedRangesPreservationClaimed'])assert.equal(r[key],false);
}

export function validateSoftGroundContent(before,after,delta){
  assert.equal(Object.keys(before).length,4100);assert.equal(Object.keys(after).length,4103);
  const packages=newAssets.map(a=>a.slice(6).split('.')[0]+'.uasset').sort();
  for(const file of packages){assert(!Object.hasOwn(before,file));assert(Object.hasOwn(after,file));}
  assert.deepEqual(Object.keys(after).sort(),[...Object.keys(before),...packages].sort());
  assert.deepEqual(Object.keys(before).filter(k=>{
    try{assert.deepEqual(before[k],after[k]);return false;}catch{return true;}
  }),['Brezi/Maps/Brezi.umap']);
  assert.deepEqual(after['Data/viewpoints.json'],before['Data/viewpoints.json']);
  assert.equal(delta.newPackages,3);assert.equal(delta.onlyOriginalMapChanged,true);
}

export const requiredFinalProof=Object.freeze([
  'Delegate the exact frozen R28 reader on selected actual R37b; no failed/foreign native report fallback.',
  'Bind successful R38 owner/report/plan/preflight/native commandlet PID0/controller/log/root audit/source-pin count.',
  'Before witness equals actual R37b saved full5364 witness; independently rebuild only two declared slot0/override-array changes; compare declared and reloaded saved witness.',
  'Pin every old/raw controls-before/saved sidecar for all2325 HISM/678197 instances; binary64 matrix SHA/order/mainseed/custom-data remain exact.',
  'Bind all64 full old graphs, samplerSources/worldPositionShaderOffsets/usage and all96 native texture settings before/saved, plus128 complete graph diagnostics with exact historical specialized readers.',
  'Bind exact two70/73-node proposed native graphs, original58 nodes, unchanged original photo maps and NoMipNone adaptation; native sampler/WorldPosition auxiliary readback required.',
  'Bind the new source L8 permission PNG and actual imported texture policy: linear, bilinear, from-texture-asset sampler, clamp, CompressionNone, no mipmaps; native texels/GPU format/containment/outside pixel equality remain unproved.',
  'Current4103Content+132 protected, exact3 new packages, only original Map changes; cloned source R37 bytes and original Recipe4 module independent/exact.',
  'A separate own QA clone must append exactly the frozen R18 close camera plus ONE source-only ground-overview camera; original Data prefix and all other files exact.',
  'The prospective ground overview is only source framing at19.3–68.8m. Ground/tree/wall/native visibility and walking/collision acceptance are not established.',
]);

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);
  assert.equal(source,path.join(root,'output/unreal',sourceContract.directSourceName),
    'Unbound R38 draft cannot delegate to a historical source or invent a camera-stage source');
  assert(Object.entries(sourceContract).filter(([key])=>key.startsWith('actual')).every(([,value])=>value!==null),
    'R38 editor draft is unbound: actual native/report/plan/process/audit/checker/QA camera stage are not available');
  throw new Error('A NEW finalized saved-R38 consumer must implement the recorded requiredFinalProof before any native launch');
}
