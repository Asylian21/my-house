import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import test from 'node:test';
import {MEADOW_INFILL_STATUS,validateMeadowInfillPlan,validateMeadowInfillReceipt} from '../scripts/unreal/exterior-meadow-infill-source.mjs';

const root=resolve(import.meta.dirname,'..');
const directory=resolve(root,'output/unreal/exterior-meadow-infill-integration-20261001-r1');
const read=async path=>JSON.parse(await readFile(path));
const sha=async path=>createHash('sha256').update(await readFile(path)).digest('hex');
const plan=await read(resolve(directory,'meadow-infill-plan.json'));
const plants=await read(resolve(directory,'geometry-manifest.json'));
const validation=await read(resolve(directory,'integration-validation.json'));
const baseline=await read(resolve(root,'output/unreal/exterior-20261001-r13a/exterior-import-report.json'));

// This constructed receipt exercises validation against actual frozen source
// and the R13 native schema. It is not an R14 native run or visual acceptance.
const report={inputFiles:{...baseline.inputFiles,...plan.inputFiles},pipelineFiles:{...baseline.pipelineFiles},
  plantGeometryManifest:resolve(directory,'geometry-manifest.json'),
  savedGeometryReadback:{...baseline.savedGeometryReadback},geometry:{groups:{...baseline.geometry.groups}},
  savedPlantReadback:structuredClone(baseline.savedPlantReadback),materials:structuredClone(baseline.materials),
  meadowInfill:{plan:resolve(directory,'meadow-infill-plan.json'),planSha256:validation.plan.sha256,
    geometryManifest:plan.infillGeometryManifest,audit:validation.audit,groupIds:plan.groups.map(g=>g.id),
    savedGroups:101,savedInstances:33483,nativeAppearanceAccepted:false,performanceAccepted:false}};
for(const path of [report.plantGeometryManifest,report.meadowInfill.plan,plan.infillGeometryManifest.path,
  plants.validatedOriginal120Subset.path,plants.validatedOriginal100Subset.path])report.inputFiles[path]=await sha(path);
for(const relative of ['scripts/unreal/exterior-meadow-infill-native.py','scripts/unreal/exterior-meadow-infill-integration.py']) {
  const path=resolve(root,relative);report.pipelineFiles[path]=await sha(path);
}
for(const mesh of plants.meshes.slice(120))report.savedPlantReadback.push({id:mesh.id,
  mesh:`/Game/Brezi/Exterior20260926/Geometry/TestMeadow/StaticMeshes/${mesh.id}_LOD0.${mesh.id}_LOD0`,
  lodTriangles:mesh.lods.map(l=>l.triangles),lodScreens:[1,.15000000596046448,.03999999910593033],
  materials:[baseline.materials.materials.ph_grass_medium_02.asset]});
for(const [index,group] of plan.groups.entries())report.geometry.groups[group.id]={
  actor:`/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.SourceTestMeadow_${index}`,
  mesh:report.savedPlantReadback.find(m=>m.id===group.meshId).mesh,instances:group.instances.length,
  cullStartCm:3200,cullEndCm:4000,qualityDetail:true,transformsSha256:'a'.repeat(64)};
const changed=mutate=>{const value=structuredClone(report);mutate(value);return value;};

test('actual frozen126 source library and33483 partial meadow roots validate with the native receipt schema',async()=>{
  assert.deepEqual(await validateMeadowInfillPlan(report,plan,plants),{
    groups:101,instances:33483,partialGroundCover:true,nativeAppearanceAccepted:false});
  assert.equal(plan.status,MEADOW_INFILL_STATUS);
  assert(report.meadowInfill.audit.projectedOpaqueCoverFractionByWindowAndLod['exterior-canopy-lod-hole'][0]<.12,
    'Partial low meadow must not borrow the managed lawn75percent gate');
});

test('source adapter cannot alter or reorder original120 masters',async()=>{
  for(const mutate of [p=>{p.meshes[0].heightCm+=1;},p=>{[p.meshes[0],p.meshes[1]]=[p.meshes[1],p.meshes[0]];}]) {
    const value=structuredClone(plants);mutate(value);
    await assert.rejects(validateMeadowInfillPlan(report,plan,value),/caller126 library differs/);
  }
});

test('source adapter cannot substitute the producer manifest for its native extension pin',async()=>{
  const value=structuredClone(plan);value.infillGeometryManifest=value.geometryManifest;
  await assert.rejects(validateMeadowInfillPlan(report,value,plants),/caller plan differs/);
  const receipt=changed(r=>{r.meadowInfill.geometryManifest=plan.geometryManifest;});
  await assert.rejects(validateMeadowInfillPlan(receipt,plan,plants));
});

test('source ordered root membership cannot be moved while keeping inventory counts',async()=>{
  const value=structuredClone(plan);value.groups[0].instances[0].positionCm[0]+=.25;
  await assert.rejects(validateMeadowInfillPlan(report,value,plants),/caller plan differs/);
});

test('meadow plan source and saved geometry require typed input pins',()=>{
  for(const mutate of [
    r=>{delete r.inputFiles[r.meadowInfill.plan];},
    r=>{r.meadowInfill.planSha256='not-a-hash';},
    r=>{r.meadowInfill.geometryManifest.extra=true;},
    r=>{r.meadowInfill.geometryManifest.path='/tmp/escaped-meadow.json';},
  ])assert.throws(()=>validateMeadowInfillReceipt(changed(mutate)));
});

test('source65 crowns, old7000 transition roots, and old47203 removals remain explicit receipt invariants',()=>{
  for(const key of ['allLodCircularCrownsChecked','source65GroundAndPrivateRoadBuildingMasksChecked',
    'original120MastersPreserved','original7000TransitionPlacementsPreserved','original47203RemovalIndicesPreserved'])
    assert.throws(()=>validateMeadowInfillReceipt(changed(r=>{r.meadowInfill.audit[key]=false;})));
  assert.throws(()=>validateMeadowInfillReceipt(changed(r=>{r.meadowInfill.audit.minimumFullCrownSourceClearanceCm=.099;})));
  assert.throws(()=>validateMeadowInfillReceipt(changed(r=>{r.meadowInfill.audit.maximumRootGroundErrorCm=.1;})));
});

test('partial source coverage cannot establish native appearance, performance, or complete photorealism',()=>{
  for(const key of ['uniformFullGroundCoverClaim','nativeVerified','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted'])
    assert.throws(()=>validateMeadowInfillReceipt(changed(r=>{r.meadowInfill.audit[key]=true;})));
  assert.throws(()=>validateMeadowInfillReceipt(changed(r=>{r.meadowInfill.nativeAppearanceAccepted=true;})));
  assert.throws(()=>validateMeadowInfillReceipt(changed(r=>{r.meadowInfill.performanceAccepted=true;})));
});

test('native receipt coverage must agree with actual pinned partial raster measurements',async()=>{
  const value=changed(r=>{r.meadowInfill.audit.projectedOpaqueCoverFractionByWindowAndLod['exterior-parcels-hole']=[.8,.8,.8];});
  await assert.rejects(validateMeadowInfillPlan(value,plan,plants),/borrows different coverage/);
});

test('native101 group membership rejects missing, duplicated, undocumented, and inflated populations',()=>{
  for(const mutate of [
    r=>{delete r.geometry.groups[r.meadowInfill.groupIds[0]];},
    r=>{r.meadowInfill.groupIds[1]=r.meadowInfill.groupIds[0];},
    r=>{r.geometry.groups.EX_meadow_infill_999_999_0=structuredClone(r.geometry.groups[r.meadowInfill.groupIds[0]]);},
    r=>{r.geometry.groups[r.meadowInfill.groupIds[0]].instances+=1;},
    r=>{r.meadowInfill.savedInstances+=1;},
  ])assert.throws(()=>validateMeadowInfillReceipt(changed(mutate)));
});

test('native populations cannot swap individual groups while retaining the33483 total',async()=>{
  const value=changed(r=>{
    r.geometry.groups[r.meadowInfill.groupIds[0]].instances+=1;
    r.geometry.groups[r.meadowInfill.groupIds[1]].instances-=1;
  });
  validateMeadowInfillReceipt(value);
  await assert.rejects(validateMeadowInfillPlan(value,plan,plants),/group population differs/);
});

test('saved18 LODs require48/42/36 triangles and inherited standard grass screens',()=>{
  for(const mutate of [
    r=>{r.savedPlantReadback.at(-1).lodTriangles[1]=48;},
    r=>{r.savedPlantReadback.at(-1).lodScreens=[1,.025,.007];},
    r=>{r.savedPlantReadback.pop();},
    r=>{r.savedPlantReadback.at(-1).mesh=r.savedPlantReadback.at(-2).mesh;},
  ])assert.throws(()=>validateMeadowInfillReceipt(changed(mutate)));
});

test('meadow native mesh bindings must retain the existing photographic PH material and graph',()=>{
  for(const mutate of [
    r=>{r.savedPlantReadback.at(-1).materials=[r.materials.materials.lawn_photographic_blade.asset];},
    r=>{r.materials.materials.ph_grass_medium_02.graphSha256='b'.repeat(64);},
    r=>{r.geometry.groups[r.meadowInfill.groupIds[0]].mesh=r.savedPlantReadback[0].mesh;},
  ])assert.throws(()=>validateMeadowInfillReceipt(changed(mutate)));
});

test('saved groups retain3200/4000 culls and detail policy without asserting unavailable readback fields',()=>{
  for(const mutate of [
    r=>{r.geometry.groups[r.meadowInfill.groupIds[0]].cullEndCm=9000;},
    r=>{r.geometry.groups[r.meadowInfill.groupIds[0]].qualityDetail=false;},
    r=>{r.savedGeometryReadback.allNewVisualsNoCollision=false;},
    r=>{r.geometry.groups[r.meadowInfill.groupIds[0]].collision='QueryAndPhysics';},
    r=>{r.geometry.groups[r.meadowInfill.groupIds[0]].canEverAffectNavigation=true;},
    r=>{r.geometry.groups[r.meadowInfill.groupIds[0]].densityScaling=false;},
  ])assert.throws(()=>validateMeadowInfillReceipt(changed(mutate)));
});
