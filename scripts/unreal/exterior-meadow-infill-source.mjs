import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {isAbsolute, relative, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

export const MEADOW_INFILL_OWNER='scripts/unreal/exterior-meadow-infill-integration.py';
export const MEADOW_INFILL_STATUS='MEASURED_ADDITIVE_PARTIAL_MEADOW_PILOT_NOT_NATIVE_ACCEPTED';
export const MEADOW_INFILL_MATERIAL='ph_grass_medium_02';
const ROOT=resolve(fileURLToPath(new URL('../..',import.meta.url)));
const HELPER='scripts/unreal/exterior-meadow-infill-native.py';
const SOURCE_OWNER='scripts/unreal/exterior-meadow-infill-pilot.py';
const IDS=Array.from({length:6},(_,i)=>`parcel_low_meadow_${i}`);
const SOURCE_PINS={
  sourceInfillPlan:'526f51e02cba8a89292ad2b0a90a975c15b48189c985a1a35c92510caee1529a',
  sourceInfillGeometry:'645e6749e95f0e89054e769a39e62b8fa2ea58ebe7a69f759b5c25b4a2d46d4f',
  sourceOriginal120Library:'45005af44e90c91fee2cbab5dcde4730b556cabe585f95d357b73b6948d69fb3',
};
const GLB_SHA='77b712725d674a0df0178c5df3829d0fe59786ab05cc3463b151fa13cb1c8b1d';
const COVERAGE_SHA='0898b1a6af4028d02f803834e7199ed47d6bced1668ef3ffd8b0e50f4246b7f5';
const PH_GRAPH_SHA='2c933cabfa14ac5e3ed4e2c7b801be05bed6d121382da0dd7e6a3724b936c05a';
const GEOMETRY_PREFIX='/Game/Brezi/Exterior20260926/Geometry/';
const MATERIAL_ASSET='/Game/Brezi/Exterior20260926/Materials/M_ph_grass_medium_02.M_ph_grass_medium_02';
const SHA=value=>createHash('sha256').update(value).digest('hex');
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const finite=(value,min,max)=>typeof value==='number'&&Number.isFinite(value)&&value>=min&&value<=max;
const PIN_KEYS=['path','sha256'];
const EXTRA=['sourceInfillPlan','sourceInfillGeometry','sourceOriginal120Library'];
const windows=['exterior-parcels-hole','exterior-parcels-contact','exterior-canopy-lod-hole','exterior-canopy-lod-contact'];

function pin(value,report,root=ROOT) {
  assert(value&&typeof value==='object'&&!Array.isArray(value),'Meadow source pin missing');
  assert.deepEqual(Object.keys(value).sort(),PIN_KEYS,'Meadow source pin shape differs');
  assert(isAbsolute(value.path)&&value.path===resolve(value.path),'Meadow pin must use an absolute canonical path');
  const path=relative(root,value.path);
  assert(path&&!path.startsWith('../')&&!isAbsolute(path),'Meadow source pin escaped repository');
  assert(hash(value.sha256),'Meadow source pin hash differs');
  assert.equal(report.inputFiles?.[value.path],value.sha256,'Meadow source pin is absent from native input closure');
  return value;
}

async function readPin(value,report,root) {
  pin(value,report,root);
  const raw=await readFile(value.path);
  assert.equal(SHA(raw),value.sha256,'Meadow source pin drift: '+value.path);
  return JSON.parse(raw);
}

function sameAdapter(record,original,extras,changed) {
  assert.equal(record.owner,MEADOW_INFILL_OWNER);
  assert.equal(record.status,MEADOW_INFILL_STATUS);
  assert.deepEqual(Object.keys(record).sort(),[...new Set([...Object.keys(original),...extras])].sort(),
    'Meadow adapter has unreviewed metadata or claims');
  for(const [key,value] of Object.entries(original))if(!changed.includes(key))
    assert.deepEqual(record[key],value,'Meadow adapter changed source field: '+key);
}

function canonicalGroups(rows) {
  const groups=new Map();
  for(const [index,row] of rows.entries()) {
    assert.equal(row.id,`meadow_infill_${index}`,'Meadow root ordering differs');
    assert(IDS.includes(row.meshId));assert.equal(row.role,'grass');
    assert(Array.isArray(row.positionCm)&&row.positionCm.length===3&&row.positionCm.every(Number.isFinite));
    assert(Array.isArray(row.scale)&&row.scale.length===3&&row.scale.every(v=>finite(v,0,10)&&v>0));
    assert(finite(row.yawDeg,0,360));
    const [x,y]=row.positionCm.map(v=>Math.floor(v/400));
    const id=`EX_meadow_infill_${x}_${y}_${row.meshId.split('_').at(-1)}`;
    if(!groups.has(id))groups.set(id,{id,meshId:row.meshId,role:'grass',qualityDetail:true,cullEndCm:4000,
      castShadow:true,instances:[],cullStartCm:3200,collision:'NoCollision',canEverAffectNavigation:false,densityScaling:true});
    groups.get(id).instances.push({positionCm:row.positionCm,yawDeg:row.yawDeg,scale:row.scale});
  }
  return [...groups.values()];
}

function validateAudit(audit) {
  assert.equal(audit.status,'verified-source-additive-partial-meadow-pilot');
  for(const [key,value] of Object.entries({instances:33483,groups:101,masters:6,lods:18,insideSoilInstances:20646,outsideContactInstances:12837}))
    assert.equal(audit[key],value,'Meadow measured inventory differs: '+key);
  assert.deepEqual(audit.allLodTriangles,[1607184,1406286,1205388]);
  assert(Array.isArray(audit.actualHeightCm)&&audit.actualHeightCm.length===2
    &&audit.actualHeightCm.every(v=>finite(v,2,8))&&audit.actualHeightCm[0]<audit.actualHeightCm[1]);
  assert(finite(audit.minimumFullCrownSourceClearanceCm,.1,1),'Meadow complete crown clearance differs');
  assert(finite(audit.maximumRootGroundErrorCm,0,.000002),'Meadow root is detached from original ground');
  for(const key of ['all18DecodedGeometryFramesAnd12LeafLodsVerified','allLodCircularCrownsChecked',
    'source65GroundAndPrivateRoadBuildingMasksChecked','NoCollision','original120MastersPreserved',
    'original7000TransitionPlacementsPreserved','original47203RemovalIndicesPreserved'])assert.equal(audit[key],true,key);
  for(const key of ['canEverAffectNavigation','uniformFullGroundCoverClaim','nativeVerified','nativeAppearanceAccepted',
    'fullPhotorealismAccepted','performanceAccepted'])assert.equal(audit[key],false,key);
  assert.deepEqual(Object.keys(audit.projectedOpaqueCoverFractionByWindowAndLod).sort(),[...windows].sort());
  for(const values of Object.values(audit.projectedOpaqueCoverFractionByWindowAndLod))
    assert(Array.isArray(values)&&values.length===3&&values.every(v=>finite(v,0,1)),'Meadow partial coverage values differ');
}

/** Read the pinned source libraries, not owner-spoofed subsets of the126 library. */
export async function validateMeadowInfillPlan(report,plan,plants,{root=ROOT,preservedLibraryPin=null}={}) {
  const infill=report.meadowInfill;assert(infill,'Meadow source has no native import receipt');
  validateMeadowInfillReceipt(report);
  assert.equal(plan.schemaVersion,1);assert.equal(plan.kind,'authored-low-meadow-infill-pilot');
  assert.deepEqual(plan.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});
  assert.equal(plan.housePlacement.streetSetbackMm,3000);assert.equal(plan.housePlacement.eastSetbackMm,3000);
  assert.equal(plan.housePlacement.status,'CLIENT_REQUESTED_SETBACK');
  assert.equal(plan.owner,MEADOW_INFILL_OWNER);assert.equal(plan.status,MEADOW_INFILL_STATUS);
  for(const key of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','integrationAuthorized'])assert.equal(plan[key],false,key);
  pin({path:infill.plan,sha256:infill.planSha256},report,root);
  assert.deepEqual(plan,await readPin({path:infill.plan,sha256:infill.planSha256},report,root),'Meadow caller plan differs from pinned source');
  pin(infill.geometryManifest,report,root);assert.deepEqual(infill.geometryManifest,plan.infillGeometryManifest);
  assert.equal(report.plantGeometryManifest,resolve(report.plantGeometryManifest));
  const importedPin={path:report.plantGeometryManifest,sha256:report.inputFiles[report.plantGeometryManifest]};
  const imported=await readPin(importedPin,report,root);
  if(preservedLibraryPin) {
    assert.equal(imported.owner,'scripts/unreal/exterior-canopy-fullness-integration.py');
    assert.equal(imported.status,'FULLER_CANOPY_INTEGRATION_SOURCE_ONLY_NATIVE_PENDING');
    assert.deepEqual(imported.validatedOriginal126Subset,preservedLibraryPin);
    assert.equal(preservedLibraryPin.sha256,'a39e13e9b58821815fd783857e09e58d1023e4a64ab10e45a2a4da608954ceb9');
    assert.deepEqual(plants,await readPin(preservedLibraryPin,report,root),'Meadow preserved126 source copy differs');
    assert.equal(imported.meshes.length,135);
    assert.deepEqual(imported.meshes.slice(0,126),plants.meshes,'Fuller canopy changed the imported meadow126 prefix');
    assert.deepEqual(imported.meshes.slice(126).map(m=>m.sourceGrowthMasterId).sort(),
      ['broadleaf','upright','orchard'].flatMap(f=>['a','b','c'].map(v=>`canopy_growth_${f}_r1_${v}`)).sort());
  } else assert.deepEqual(plants,imported,'Meadow caller126 library differs from imported pinned source');
  for(const key of EXTRA) {
    pin(plan[key],report,root);assert.equal(plan[key].sha256,SOURCE_PINS[key]);
    assert.deepEqual(plants[key],plan[key]);
  }
  const [original,sourcePlan,sourceGeometry,extension,coverage,old120,old100]=await Promise.all([
    readPin(plan.sourceOriginal120Library,report,root),readPin(plan.sourceInfillPlan,report,root),
    readPin(plan.sourceInfillGeometry,report,root),readPin(plan.infillGeometryManifest,report,root),
    readPin(plan.coverageMeasurement,report,root),readPin(plants.validatedOriginal120Subset,report,root),
    readPin(plants.validatedOriginal100Subset,report,root),
  ]);
  assert.equal(sourcePlan.owner,SOURCE_OWNER);assert.equal(sourceGeometry.owner,SOURCE_OWNER);
  assert.equal(original.owner,'scripts/unreal/exterior-lawn-photo-integration.py');
  assert.equal(plan.coverageMeasurement.sha256,COVERAGE_SHA);
  assert.deepEqual(plan.geometryManifest,plan.sourceInfillGeometry);
  assert.deepEqual(plants.infillGeometryManifest,plan.infillGeometryManifest);
  assert.deepEqual(old120,original,'Meadow original120 copy differs');
  assert.equal(plants.validatedOriginal120Subset.sha256,plan.sourceOriginal120Library.sha256);
  assert.equal(plants.validatedOriginal100Subset.sha256,original.sourceOriginal100Library.sha256);
  assert.deepEqual(old100,await readPin(original.sourceOriginal100Library,report,root));
  for(const record of [plan,plants,extension]) {
    assert.equal(record.generatorSha256,plan.generatorSha256);
    assert(hash(record.generatorSha256));
    assert.deepEqual(record.inputFiles,plan.inputFiles,'Meadow source input closure differs');
    for(const [path,value] of Object.entries(record.inputFiles))pin({path,sha256:value},report,root);
  }
  for(const path of [resolve(root,MEADOW_INFILL_OWNER),resolve(root,HELPER)]) {
    const expected=report.pipelineFiles?.[path];assert(hash(expected),'Meadow native pipeline is unpinned');
    assert.equal(SHA(await readFile(path)),expected,'Meadow native pipeline source drift');
    if(path===resolve(root,MEADOW_INFILL_OWNER))assert.equal(expected,plan.generatorSha256);
  }
  sameAdapter(plan,sourcePlan,[...EXTRA,'status','infillGeometryManifest'],['owner','generatorSha256','inputFiles','status','groups']);
  sameAdapter(extension,sourceGeometry,[...EXTRA,'status'],['owner','generatorSha256','inputFiles','status']);
  sameAdapter(plants,original,[...EXTRA,'infillGeometryManifest','validatedOriginal120Subset','validatedOriginal100Subset'],
    ['owner','generatorSha256','inputFiles','status','meshes','revision']);
  assert.equal(original.meshes.length,120);assert.equal(sourceGeometry.meshes.length,6);
  assert.equal(plants.meshes.length,126);assert.equal(plants.meshes.reduce((n,m)=>n+m.lods.length,0),378);
  assert.deepEqual(plants.meshes,[...original.meshes,...sourceGeometry.meshes],'Meadow original120 prefix or appended six records differ');
  assert.deepEqual(sourceGeometry.meshes.map(m=>m.id),IDS);
  for(const mesh of sourceGeometry.meshes) {
    assert.equal(mesh.role,'grass');assert.equal(mesh.placementPolicy,'explicit-only');
    assert.deepEqual(mesh.materialKeys,[MEADOW_INFILL_MATERIAL]);assert.equal(Object.hasOwn(mesh,'lodScreenSizes'),false);
    assert.equal(mesh.glbSha256,GLB_SHA);pin({path:mesh.glbPath,sha256:mesh.glbSha256},report,root);
    assert.deepEqual(mesh.lods.map(l=>l.level),[0,1,2]);assert.deepEqual(mesh.lods.map(l=>l.triangles),[48,42,36]);
    assert.deepEqual(mesh.lods.map(l=>l.vertices),[68,64,60]);
    assert.deepEqual(mesh.lods.map(l=>l.nodeName),[0,1,2].map(l=>`${mesh.id}_LOD${l}`));
  }
  assert.equal(SHA(await readFile(sourceGeometry.meshes[0].glbPath)),GLB_SHA,'Meadow saved18-node GLB drift');
  assert.equal(plan.infillPlacements.length,33483);assert.equal(plan.groups.length,101);
  assert.deepEqual(plan.groups,canonicalGroups(plan.infillPlacements),'Meadow ordered root membership/native policy differs');
  assert.deepEqual(infill.groupIds,plan.groups.map(g=>g.id),'Meadow saved membership differs from canonical101 groups');
  for(const group of plan.groups) {
    const saved=report.geometry.groups[group.id];
    assert.equal(saved.instances,group.instances.length,'Meadow saved group population differs from source');
    assert.equal(saved.mesh,report.savedPlantReadback.find(m=>m.id===group.meshId).mesh,'Meadow saved group mesh differs from source');
  }
  const recipes=await readPin(original.sourceMaterialManifest,report,root);
  assert.deepEqual(await readPin(plan.materialManifest,report,root),{[MEADOW_INFILL_MATERIAL]:recipes[MEADOW_INFILL_MATERIAL]});
  assert.deepEqual(report.materials.materials[MEADOW_INFILL_MATERIAL].recipe,recipes[MEADOW_INFILL_MATERIAL],
    'Meadow changed original PH foliage recipe');
  assert.equal(coverage.uniformFullGroundCoverClaim,false);assert.equal(coverage.nativeAppearanceAccepted,false);
  assert.deepEqual(coverage.windows.map(w=>w.id),windows);
  const actualCoverage={};
  for(const window of coverage.windows) {
    assert.equal(window.sizeCm,100);assert.equal(window.pixelSizeMm,.25);assert.equal(window.resolution,4000);
    assert.deepEqual(window.lods.map(l=>l.lod),[0,1,2]);
    actualCoverage[window.id]=window.lods.map(l=>l.projectedOpaqueCoverFraction);
    for(const lod of window.lods) {
      assert(finite(lod.projectedOpaqueCoverFraction,0,1));assert(finite(lod.tenCmBinP10,0,1));
      assert(Math.abs(lod.uncoveredFraction-(1-lod.projectedOpaqueCoverFraction))<1e-12);
    }
  }
  assert.deepEqual(infill.audit.coverageMeasurement,plan.coverageMeasurement);
  assert.deepEqual(infill.audit.projectedOpaqueCoverFractionByWindowAndLod,actualCoverage,'Meadow audit borrows different coverage');
  assert.deepEqual(infill.audit.allLodTriangles,plan.audit.newTriangleBudgetByLod);
  assert(Math.abs(infill.audit.minimumFullCrownSourceClearanceCm-plan.audit.minimumFullCrownSourceClearanceCm)<.000002);
  assert.deepEqual(infill.audit.actualHeightCm,plan.audit.actualPlantHeightRangeCm);
  return {groups:plan.groups.length,instances:plan.infillPlacements.length,partialGroundCover:true,nativeAppearanceAccepted:false};
}

/** Saved native geometry proves import membership; it cannot accept appearance. */
export function validateMeadowInfillReceipt(report) {
  const infill=report.meadowInfill;if(!infill)return;
  pin({path:infill.plan,sha256:infill.planSha256},report);pin(infill.geometryManifest,report);
  validateAudit(infill.audit);pin(infill.audit.coverageMeasurement,report);
  assert.equal(infill.audit.coverageMeasurement.sha256,COVERAGE_SHA);
  assert.equal(infill.nativeAppearanceAccepted,false);assert.equal(infill.performanceAccepted,false);
  if(Object.hasOwn(infill,'fullPhotorealismAccepted'))assert.equal(infill.fullPhotorealismAccepted,false);
  assert.equal(infill.savedGroups,101);assert.equal(infill.savedInstances,33483);
  assert(Array.isArray(infill.groupIds)&&infill.groupIds.length===101&&new Set(infill.groupIds).size===101);
  assert.equal(report.savedGeometryReadback.allNewVisualsNoCollision,true,'Meadow native visual collision gate failed');
  const nativeIds=Object.keys(report.geometry.groups).filter(id=>id.startsWith('EX_meadow_infill_'));
  assert.deepEqual([...nativeIds].sort(),[...infill.groupIds].sort(),'Meadow saved group inventory is incomplete or undocumented');
  const masters=report.savedPlantReadback.filter(m=>m.id.startsWith('parcel_low_meadow_'));
  assert.deepEqual(masters.map(m=>m.id).sort(),IDS,'Meadow saved six master inventory differs');
  assert.equal(new Set(masters.map(m=>m.mesh)).size,6);
  for(const row of masters) {
    assert(row.mesh.startsWith(GEOMETRY_PREFIX)&&row.mesh.split('/').at(-1)===`${row.id}_LOD0.${row.id}_LOD0`);
    assert.deepEqual(row.lodTriangles,[48,42,36]);
    assert(Array.isArray(row.lodScreens)&&row.lodScreens.length===3&&row.lodScreens.every((v,i)=>Number.isFinite(v)&&Math.abs(v-[1,.15,.04][i])<1e-5),
      'Meadow standard grass LOD screen readback differs');
    assert.deepEqual(row.materials,[MATERIAL_ASSET],'Meadow saved PH material binding differs');
  }
  const material=report.materials.materials[MEADOW_INFILL_MATERIAL];
  assert.equal(material.asset,MATERIAL_ASSET);assert.equal(material.graphSha256,PH_GRAPH_SHA,'Meadow original native PH graph differs');
  assert.equal(material.recipe.sourceUrl,'https://polyhaven.com/a/grass_medium_02');assert.equal(material.recipe.license,'CC0-1.0');
  let instances=0;
  for(const id of infill.groupIds) {
    assert(/^EX_meadow_infill_-?\d+_-?\d+_[0-5]$/.test(id),'Meadow native group identity differs');
    const group=report.geometry.groups[id];assert(group,'Meadow saved group missing');
    assert(group.actor.startsWith('/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.'));
    assert(masters.some(m=>m.mesh===group.mesh),'Meadow group binds an unapproved mesh');
    assert(Number.isInteger(group.instances)&&group.instances>0);assert(hash(group.transformsSha256));
    assert.equal(group.cullStartCm,3200);assert.equal(group.cullEndCm,4000);assert.equal(group.qualityDetail,true);
    // Existing native receipts omit these per-group fields. Validate them if a
    // future readback exposes them; source policies are independently compared.
    for(const [key,value] of Object.entries({collision:'NoCollision',canEverAffectNavigation:false,densityScaling:true}))
      if(Object.hasOwn(group,key))assert.equal(group[key],value,'Meadow native group policy differs: '+key);
    instances+=group.instances;
  }
  assert.equal(instances,33483,'Meadow saved total population differs');
}
