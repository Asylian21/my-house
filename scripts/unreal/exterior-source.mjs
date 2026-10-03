// A separate, reproducible exterior revision of an inherited C/B/B scene.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {validateNeighborhoodTransitionReceipt,validateNeighborhoodTransitionPlan} from './exterior-transition-source.mjs';
import {PHOTO_LAWN_OWNER,PHOTO_LAWN_STATUS,validatePhotographicLawnReceipt,validatePhotographicLawnPlan} from './exterior-lawn-photo-source.mjs';
import {validateMeadowInfillReceipt,validateMeadowInfillPlan} from './exterior-meadow-infill-source.mjs';
import {validateContinuousMeadowReceipt,validateContinuousMeadowPlan} from './exterior-meadow-continuous-source-r2.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex');
const read=async p=>JSON.parse(await readFile(p));
const isHash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const UPRIGHT_STATUS='MEASURED_UPRIGHT_MANAGED_LAWN_STUDY_NOT_NATIVE_ACCEPTED';
const TAPERED_OWNER='scripts/unreal/exterior-lawn-tapered-integration.py';
const TAPERED_STATUS='MEASURED_TAPERED_MANAGED_LAWN_NOT_NATIVE_ACCEPTED';
const LAWN_OWNER_STATUS={
  'scripts/unreal/exterior-lawn-natural.py':'PASS_STATIC_GEOMETRY_AND_CLEARANCE',
  'scripts/unreal/exterior-lawn-natural-managed.py':'PASS_STATIC_MANAGED_GEOMETRY_AND_CLEARANCE',
  'scripts/unreal/exterior-lawn-coverage.py':'PASS_STATIC_CONTINUOUS_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED',
  'scripts/unreal/exterior-lawn-fine.py':'PASS_STATIC_FINE_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED',
  'scripts/unreal/exterior-lawn-upright.py':UPRIGHT_STATUS,
  [TAPERED_OWNER]:TAPERED_STATUS,
  [PHOTO_LAWN_OWNER]:PHOTO_LAWN_STATUS,
};
const GROVE_OWNER_STATUS={
  canopyReplacement:{
    'scripts/unreal/exterior-canopy-masters.py':'verified-source-grove-canopy-replacement',
    'scripts/unreal/exterior-canopy-growth.py':'verified-source-grove-canopy-growth',
    'scripts/unreal/exterior-canopy-fullness-study.py':'verified-source-grove-canopy-fullness',
  },
  canopyEcology:{
    'scripts/unreal/exterior-canopy-ecology.py':'verified-source-grove-ecology',
    'scripts/unreal/exterior-canopy-ecology-unflared.py':'verified-source-grove-ecology',
  },
};
const finite=(v,n)=>Array.isArray(v)&&v.length===n&&v.every(Number.isFinite);

function validatePointedManagedCoverage(audit,shape) {
  assert(['upright','tapered'].includes(shape),'Unknown managed leaf shape');
  const coverageStatus=shape==='upright'?'MEASURED_UPRIGHT_STUDY_COVERAGE_NOT_NATIVE_ACCEPTED':'MEASURED_TAPERED_LAWN_COVERAGE_NOT_NATIVE_ACCEPTED';
  const boundaryStatus=shape==='upright'?'MEASURED_UPRIGHT_STUDY_BOUNDARY_COVERAGE_NOT_NATIVE_ACCEPTED':'MEASURED_TAPERED_LAWN_BOUNDARY_COVERAGE_NOT_NATIVE_ACCEPTED';
  assert.equal(audit.instances,102011);assert.equal(audit.groups,40);assert.equal(audit.edgeInstances,21144);
  assert.equal(audit.nearTriangleBudget,18571200);assert.deepEqual(audit.allInstancesTriangleBudgetByLod,[18571200,18571200,18571200]);
  assert.deepEqual(audit.leavesPerPatchEveryLod,{interior:64,boundary:48});
  assert.deepEqual(audit.lowLeaningLeavesPerPatch,{interior:16,boundary:12});
  for(const key of ['interiorCoverageTargetsMet','boundaryCoverageTargetsMet'])assert.equal(audit[key],true);
  for(const key of ['nativeVerified','nativeAppearanceAccepted','fullPhotorealismAccepted','integrationAuthorized'])assert.equal(audit[key],false);
  const coverage=audit.physicalCoverage;
  assert.equal(coverage?.status,coverageStatus,'Pointed lawn physical coverage status differs');
  assert.deepEqual(coverage.criteria,{minimumTopViewCoverage:.75,preferredTopViewCoverage:.80,
    minimumTenCmBinP10:.55,maximumPermittedBladeLossAcrossLods:0});
  assert.equal(coverage.windows.length,4);
  for(const window of coverage.windows) {
    assert.equal(window.resolution,4000);assert.equal(window.sizeCm,100);assert(finite(window.centerCm,2));
    assert.deepEqual(window.lods.map(r=>r.lod),[0,1,2]);
    for(const lod of window.lods) {
      assert(lod.projectedCoverage>=.75&&lod.projectedCoverage<=1,'Upright physical coverage gate failed');
      assert(lod.tenCmBinCoverageP10>.55&&lod.tenCmBinCoverageP10<=1);
      assert(lod.tenCmBinCoverageMinimum>=0&&lod.tenCmBinCoverageMinimum<=lod.tenCmBinCoverageP10);
      assert.equal(lod.bareTenCmBins,0);assert.equal(lod.studyTargetsMet,true);
    }
  }
  const boundary=audit.boundaryCoverage;
  assert.equal(boundary?.status,boundaryStatus,'Pointed lawn boundary coverage status differs');
  assert.deepEqual(boundary.criteria,{minimumPhysicalCoverByBoundaryBand:{'1to10mm':.12,'10to30mm':.40,'30to100mm':.50},outsideSourceDomainPermittedCm:0});
  assert.deepEqual(boundary.windows.map(w=>w.boundaryId),['deck','mulch']);
  for(const [index,window] of boundary.windows.entries()) {
    assert(finite(window.originCm,2)&&finite(window.axisUnitXY,2)&&finite(window.inwardUnitXY,2));
    const [a,b]=[[[-476,-650],[-476,-400]],[[-1124,-440],[-1016,-500]]][index];
    const length=Math.hypot(b[0]-a[0],b[1]-a[1]),axis=b.map((value,k)=>(value-a[k])/length);
    const inward=index===0?[-axis[1],axis[0]]:[axis[1],-axis[0]];
    assert.deepEqual(window.originCm,a,'Upright boundary source frame differs');
    assert(window.axisUnitXY.every((v,k)=>Math.abs(v-axis[k])<1e-9)&&window.inwardUnitXY.every((v,k)=>Math.abs(v-inward[k])<1e-9),'Upright boundary axes differ');
    assert.equal(window.widthCm,40);assert.equal(window.pixelSizeMm,.25);
    assert(Number.isFinite(window.lengthCm)&&Math.abs(window.lengthCm-length)<1e-9);
    assert.deepEqual(window.resolutionXY,[1600,Math.ceil(window.lengthCm/.025)]);
    assert(Number.isInteger(window.intersectingInstances)&&window.intersectingInstances>0);
    assert.deepEqual(window.lods.map(r=>r.lod),[0,1,2]);
    for(const lod of window.lods) {
      assert(lod.projectedCoverage>=0&&lod.projectedCoverage<=1);assert.equal(lod.studyTargetsMet,true);
      assert.equal(lod.boundaryBands.length,3);
      for(const [index,band] of lod.boundaryBands.entries()) {
        assert.deepEqual(band.distanceFromBoundaryMm,[[1,10],[10,30],[30,100]][index]);
        assert(band.physicalCoverFraction>[.12,.40,.50][index]&&band.physicalCoverFraction<=1,'Upright boundary leaf cover gate failed');
      }
    }
  }
}

export function validateNaturalLawnPlan(report,plan) {
  const lawn=report.naturalLawn;
  assert(Object.hasOwn(LAWN_OWNER_STATUS,plan.owner),'Natural lawn plan owner differs');
  assert.equal(plan.audit.status,LAWN_OWNER_STATUS[plan.owner],'Natural lawn owner/status pair differs');
  assert.deepEqual(lawn.audit,plan.audit,'Natural lawn audit differs from pinned plan');
  assert.equal(plan.audit.instances,plan.lawnPlacements.length);assert.equal(plan.audit.groups,plan.groups.length);
  if(['scripts/unreal/exterior-lawn-upright.py',TAPERED_OWNER].includes(plan.owner)) {
    for(const key of ['coverageReceipt','boundaryCoverageReceipt']) {
      const pin=plan[key];
      assert(pin&&isHash(pin.sha256)&&report.inputFiles[pin.path]===pin.sha256,'Upright coverage source pin missing');
    }
    assert.deepEqual(lawn.coverageReceipt,plan.coverageReceipt,'Upright physical coverage pin differs from source plan');
    assert.deepEqual(lawn.boundaryCoverageReceipt,plan.boundaryCoverageReceipt,'Upright boundary coverage pin differs from source plan');
    validatePointedManagedCoverage(plan.audit,plan.owner===TAPERED_OWNER?'tapered':'upright');
  }
}

export function validateGrovePlanOwner(plan,key) {
  assert(Object.hasOwn(GROVE_OWNER_STATUS,key),'Unknown grove plan scope');
  assert(Object.hasOwn(GROVE_OWNER_STATUS[key],plan.owner),'Grove plan owner differs');
}

export function validateGrovePlanReceipt(report,plan,key) {
  validateGrovePlanOwner(plan,key);
  const grove=report[key];
  assert.equal(grove.validation.status,GROVE_OWNER_STATUS[key][plan.owner],'Grove plan owner/native status pair differs');
  assert.deepEqual(grove.audit,plan.audit,'Grove audit differs from pinned plan');
  const placements=key==='canopyReplacement'?plan.canopyPlacements:plan.ecologyPlacements;
  assert.equal(placements.length,grove.savedReadback.instances);
}

export function plantLodScreenSizes(row) {
  if(Object.hasOwn(row,'lodScreenSizes')) {
    const natural=row.id.startsWith('lawn_natural_')&&row.materialKeys.length===1&&row.materialKeys[0]==='lawn_natural_blade';
    const photo=/^lawn_photo_(?:[01]_[0-7]|edge_[01]_[01])$/.test(row.id)&&row.materialKeys.length===1&&row.materialKeys[0]==='lawn_photographic_blade';
    assert((natural||photo)&&row.role==='grass'&&row.placementPolicy==='explicit-only','Unreviewed plant LOD override');
    assert.deepEqual(row.lodScreenSizes,[1,.025,.007],'Unreviewed lawn LOD screens');
    return [1,.025,.007];
  }
  return row.role==='tree'?[1,.32,.10]:[1,.15,.04];
}

export function validateNaturalLawnReceipt(report) {
  const lawn=report.naturalLawn;if(!lawn)return;
  assert(isHash(lawn.planSha256)&&report.inputFiles[lawn.plan]===lawn.planSha256,'Natural lawn plan must be pinned');
  assert(['PASS_STATIC_GEOMETRY_AND_CLEARANCE','PASS_STATIC_MANAGED_GEOMETRY_AND_CLEARANCE',
    'PASS_STATIC_CONTINUOUS_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED','PASS_STATIC_FINE_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED',UPRIGHT_STATUS,TAPERED_STATUS,PHOTO_LAWN_STATUS].includes(lawn.audit.status),'Natural lawn geometry audit missing');
  assert(Number.isInteger(lawn.audit.instances)&&lawn.audit.instances>0);
  assert(Number.isInteger(lawn.audit.groups)&&lawn.audit.groups>0);
  assert.equal(lawn.audit.sourceMasksUnchanged,true);
  if(['PASS_STATIC_CONTINUOUS_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED','PASS_STATIC_FINE_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED',UPRIGHT_STATUS,TAPERED_STATUS].includes(lawn.audit.status)) {
    const pin=lawn.coverageReceipt;
    assert(pin&&isHash(pin.sha256)&&report.inputFiles[pin.path]===pin.sha256,'Physical lawn coverage must be independently pinned');
  }
  if(['PASS_STATIC_FINE_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED',UPRIGHT_STATUS,TAPERED_STATUS].includes(lawn.audit.status)) {
    const pin=lawn.boundaryCoverageReceipt;
    assert(pin&&isHash(pin.sha256)&&report.inputFiles[pin.path]===pin.sha256,'Fine lawn boundary coverage must be independently pinned');
  }
  if([UPRIGHT_STATUS,TAPERED_STATUS].includes(lawn.audit.status))validatePointedManagedCoverage(lawn.audit,lawn.audit.status===TAPERED_STATUS?'tapered':'upright');
  if(lawn.audit.status===PHOTO_LAWN_STATUS)validatePhotographicLawnReceipt(report);
  const hidden=lawn.hiddenOriginalGroups;
  assert.equal(hidden.length,4);
  assert.deepEqual(hidden.map(r=>r.legacyLawnGroup).sort(),['LawnTuft0','LawnTuft1','LawnTuft2','LawnTuft3']);
  assert.equal(new Set(hidden.map(r=>r.actor)).size,4);
  assert.equal(hidden.reduce((n,r)=>n+r.preserved.instanceCount,0),40437);
  for(const row of hidden) {
    assert.equal(row.detailDensityScalingAfter,false,'Hidden old lawn must stay outside runtime detail scaling');
    assert(isHash(row.preserved.orderedInstanceTransformsSha256),'Missing preserved original transforms');
    assert(isHash(row.sourcePlacement.sha256),'Missing original placement pin');
    const trim=row.sourceRuralTrim;
    assert.equal(trim.membership,'ordered-source-placement-subset-of-pinned-rural-keep-polygons');
    for(const pin of [trim.report,trim.plan])assert(isHash(pin.sha256)&&report.inputFiles[pin.path]===pin.sha256,'Missing inherited trim pin');
    assert.equal(trim.group.kept,row.preserved.instanceCount);assert.equal(trim.group.sourceInstanceOrderPreserved,true);
    assert.equal(trim.group.before-trim.group.removed,trim.group.kept);
    assert(isHash(trim.group.transformsSha256),'Missing saved trimmed transforms');
    assert.deepEqual(report.sourceRenderChanges.find(r=>r.actor===row.actor&&r.component===row.component),row);
  }
  assert.deepEqual(lawn.savedReadback,{status:'verified-hidden-original-lawn',actors:4,instances:40437,
    originalMeshesMaterialsGroundAndCollisionPreserved:true,hiddenDetailDensityScalingDisabled:true});
}

export function validateGroveReceipt(report) {
  for(const key of ['canopyReplacement','canopyEcology']) {
    const grove=report[key];if(!grove)continue;
    assert(isHash(grove.planSha256)&&report.inputFiles[grove.plan]===grove.planSha256,'Grove plan must be pinned');
    assert.equal(grove.regionId,'village_nearest_grove');
    assert(Object.values(GROVE_OWNER_STATUS[key]).includes(grove.validation.status),'Grove native validation status differs');
    assert.equal(grove.hiddenOriginalActors,0,'Grove changes must not hide original actors');
    if(key==='canopyReplacement') {
      assert.equal(grove.trees,78);assert.equal(grove.deletedTrees,0);
      assert.equal(grove.nonGroveRegionalRowsPreserved,true);
    } else assert.equal(grove.sourceGroundUnchanged,true);
    assert(Array.isArray(grove.groupIds)&&grove.groupIds.length>0&&new Set(grove.groupIds).size===grove.groupIds.length);
    const groups=grove.groupIds.map(id=>{
      const group=report.geometry.groups[id];assert(group,'Saved grove group is missing');
      assert(group.mesh.startsWith('/Game/Brezi/Exterior20260926/Geometry/'));
      assert.equal(typeof group.qualityDetail,'boolean');
      if(key==='canopyReplacement')assert.equal(group.qualityDetail,false,'Tree crowns must retain their authored density');
      assert(Number.isInteger(group.instances)&&group.instances>0);
      assert(isHash(group.transformsSha256),'Saved ordered grove transforms are missing');
      return group;
    });
    const count=groups.reduce((n,g)=>n+g.instances,0);
    assert.equal(count,key==='canopyReplacement'?78:grove.audit.instances);
    if(key==='canopyEcology')assert.equal(groups.length,grove.audit.groups);
    assert.deepEqual(grove.savedReadback,{status:'verified-saved-grove-groups',groups:groups.length,instances:count,
      allNewVisualsNoCollision:true,orderedNativeTransformsVerifiedAfterReload:true});
  }
  const floor=report.groveSubstrate;
  if(floor) {
    assert(isHash(floor.planSha256)&&report.inputFiles[floor.plan]===floor.planSha256,'Grove substrate plan must be pinned');
    assert.equal(floor.regionId,'village_nearest_grove');
    assert.equal(floor.validation.status,'verified-source-grove-substrate');
    assert.equal(floor.sourceGroundUnchanged,true);assert.equal(floor.hiddenOriginalActors,0);
    assert(Array.isArray(floor.meshIds)&&floor.meshIds.length>0&&new Set(floor.meshIds).size===floor.meshIds.length);
    for(const id of floor.meshIds) {
      assert(id.startsWith('context_grove_substrate_'),'Grove substrate mesh identity differs');
      assert(report.geometry.actors[id],'Saved grove substrate actor is missing');
      assert(report.geometry.meshes[id]?.startsWith('/Game/Brezi/Exterior20260926/Geometry/'),'Saved grove substrate mesh is missing');
    }
    assert.deepEqual(floor.savedReadback,{status:'verified-saved-grove-substrate',meshes:floor.meshIds.length,
      allNewVisualsNoCollision:true,nativeMeshBindingsVerifiedAfterReload:true});
  }
}

export function validateExteriorReceipt({report,source,project}) {
  assert.equal(report.schemaVersion,1);
  assert.equal(report.owner,'scripts/unreal/exterior-import.py');
  assert.equal(report.status,'exterior-import-validated');
  assert.equal(report.project,project);assert.equal(report.sourceOutput,source.donor);
  assert.deepEqual(report.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});
  assert.deepEqual(report.setbacksMm,{street:3000,east:3000});
  for(const key of ['savedReloaded','protectedContentUnchanged','sourceGeometryCollisionAndTransformsPreserved','originalMaterialAssetsPreserved'])
    assert.equal(report[key],true,'Missing exterior invariant: '+key);
  assert.deepEqual(report.beforeAssetHashes,source.content);
  const content=resolve(project,'Content'),map=resolve(content,'Brezi/Maps/Brezi.umap');
  const views=resolve(content,'Data/viewpoints.json'),after=report.afterAssetHashes;
  assert(Object.values(after).every(isHash));
  for(const [path,value] of Object.entries(source.content)) {
    assert(Object.hasOwn(after,path),'Exterior deleted original Content');
    if(path!==map&&path!==views)assert.equal(after[path],value,'Exterior changed original asset: '+path);
  }
  const added=Object.keys(after).filter(p=>!Object.hasOwn(source.content,p)).sort();
  assert(added.length>0);assert.deepEqual(report.newAssets,added);
  for(const path of added)assert(path===resolve(path)&&path.startsWith(resolve(content,'Brezi/Exterior20260926')+'/')&&/\.(uasset|uexp|ubulk)$/.test(path));
  const changed=Object.keys(source.content).filter(p=>source.content[p]!==after[p]).sort();
  assert(changed.includes(map));assert(changed.every(p=>p===map||p===views));
  assert.deepEqual(report.changedAssets.map(r=>r.path).sort(),changed);
  for(const row of report.changedAssets)assert.deepEqual(row,{path:row.path,beforeSha256:source.content[row.path],afterSha256:after[row.path]});
  assert.deepEqual(report.viewpoints.after.views.slice(0,report.viewpoints.before.views.length),report.viewpoints.before.views);
  const beforeOther={...report.viewpoints.before},afterOther={...report.viewpoints.after};delete beforeOther.views;delete afterOther.views;
  assert.deepEqual(afterOther,beforeOther,'Exterior changed original lighting or viewpoint settings');
  assert.equal(new Set(report.viewpoints.after.views.map(v=>v.id)).size,report.viewpoints.after.views.length);
  assert.equal(report.finalActorCount,report.originalActorCount+report.addedActors.length);
  assert.equal(new Set(report.addedActors).size,report.addedActors.length);
  for(const key of ['protectedActorWitnessSha256','authoredActorWitnessSha256'])assert(isHash(report[key]));
  assert.equal(report.savedProtectedActorWitnessSha256,report.protectedActorWitnessSha256);
  assert.equal(report.savedActorWitnessSha256,report.authoredActorWitnessSha256);
  assert(report.savedGeometryReadback.meshCount>0&&report.savedGeometryReadback.instanceCount>0);
  assert.equal(report.savedGeometryReadback.allNewVisualsNoCollision,true);
  assert(report.context.parcelCount>13);assert.equal(report.materialReadback.status,'verified-saved-exterior-materials');
  validateNaturalLawnReceipt(report);
  validateGroveReceipt(report);
  validateContinuousMeadowReceipt(report);
  if(!report.continuousMeadow) {
    validateNeighborhoodTransitionReceipt(report);
    validateMeadowInfillReceipt(report);
  }
  return after;
}

export async function verifyExteriorScene({root,output,project,source}) {
  const file=resolve(output,'exterior-import-report.json'),report=await read(file);
  const hostFile=resolve(output,'exterior-import-process.json'),host=await read(hostFile);
  const processFile=resolve(output,'exterior-import.log.json'),logFile=resolve(output,'exterior-import.log');
  assert.equal(host.processFile,processFile);assert.equal(host.logFile,logFile);
  const process=await read(processFile),profile=await read(resolve(output,'profile.json'));
  assert.equal(process.code,0);assert.equal(process.signal,null);assert.equal(process.pid,report.nativeProcessId);
  assert.equal(process.command,resolve(profile.engine,'Engine/Binaries/Mac/UnrealEditor-Cmd'));
  assert(process.args.includes(resolve(project,'BreziTwin.uproject'))&&process.args.includes('-run=pythonscript')&&process.args.includes('-script='+resolve(root,'scripts/unreal/exterior-import.py')));
  assert(Date.parse(report.startedAt)>=Date.parse(process.startedAt)&&Date.parse(report.generatedAt)<=Date.parse(process.endedAt));
  const inputs={[file]:host.reportSha256,[hostFile]:sha(await readFile(hostFile)),[processFile]:host.processFileSha256,[logFile]:host.logSha256,...report.pipelineFiles,...report.inputFiles};
  for(const [path,value] of Object.entries(inputs)){assert(isHash(value));assert.equal(sha(await readFile(path)),value,'Exterior input changed: '+path);}
  const content=validateExteriorReceipt({report,source,project});
  const manifests=Object.keys(report.inputFiles).filter(p=>p.endsWith('/geometry-manifest.json'));
  assert(manifests.length>0);
  // New composite libraries explicitly name the imported master. Their old
  // library and garden provenance remains pinned without being mistaken for it.
  let primary=report.plantGeometryManifest;
  if(primary)assert(manifests.includes(primary),'Imported plant master must be pinned');
  else {
    assert.equal(new Set(manifests.map(path=>report.inputFiles[path])).size,1,'Ambiguous exterior plant geometry manifests');
    primary=manifests[0];
  }
  const plants=await read(primary);
  if(report.meadowInfill&&!report.continuousMeadow) {
    const preservedLibraryPin=plants.owner==='scripts/unreal/exterior-canopy-fullness-integration.py'
      ?plants.validatedOriginal126Subset:null;
    const meadowPlants=preservedLibraryPin?await read(preservedLibraryPin.path):plants;
    await validateMeadowInfillPlan(report,await read(report.meadowInfill.plan),meadowPlants,{root,preservedLibraryPin});
  }
  if(report.neighborhoodTransition&&!report.continuousMeadow) {
    const plan=await read(report.neighborhoodTransition.plan);
    const context=await read(plan.sourceContext.path);
    const basisPath=Object.keys(plan.inputFiles).find(path=>path.endsWith('/exterior-20261001-r10/exterior-import-report.json'));
    assert(basisPath&&report.inputFiles[basisPath]===plan.inputFiles[basisPath],'Transition original material basis must be pinned');
    validateNeighborhoodTransitionPlan(report,plan,context,await read(basisPath),await read(report.neighborhoodTransition.nativeTopologyBaseline.path));
  }
  if(report.continuousMeadow)await validateContinuousMeadowPlan(report,await read(report.continuousMeadow.plan),{root});
  if(plants.meshes.some(m=>m.id.startsWith('lawn_natural_')||m.id.startsWith('lawn_photo_')))assert(report.naturalLawn,'Imported natural lawn has no saved replacement witness');
  if(report.naturalLawn) {
    const plan=await read(report.naturalLawn.plan);
    validateNaturalLawnPlan(report,plan);
    if(plan.owner===PHOTO_LAWN_OWNER)validatePhotographicLawnPlan(report,plan,await read(plan.audit.photographicAlphaCoverage.path));
    if(['scripts/unreal/exterior-lawn-upright.py',TAPERED_OWNER].includes(plan.owner))for(const [key,body] of [
      ['coverageReceipt','physicalCoverage'],['boundaryCoverageReceipt','boundaryCoverage']]) {
      const external=await read(plan[key].path);
      assert.deepEqual(external,plan.audit[body],'Upright pinned external coverage differs from source plan');
      assert.deepEqual(external,report.naturalLawn.audit[body],'Upright pinned external coverage differs from native receipt');
    }
  }
  for(const key of ['canopyReplacement','canopyEcology'])if(report[key]) {
    const grove=report[key],plan=await read(grove.plan);
    validateGrovePlanReceipt(report,plan,key);
    if(key==='canopyEcology')for(const group of plan.groups) {
      assert(grove.groupIds.includes(group.id),'Ecology plan group missing from saved membership');
      const actual=report.geometry.groups[group.id];
      assert.equal(actual.instances,group.instances.length);
      assert.equal(actual.qualityDetail,group.qualityDetail);
      assert.equal(actual.cullStartCm,Math.trunc(group.cullEndCm*.8));assert.equal(actual.cullEndCm,group.cullEndCm);
      assert.equal(actual.mesh,report.savedPlantReadback.find(r=>r.id===group.meshId).mesh);
    }
  }
  if(report.groveSubstrate) {
    const floor=report.groveSubstrate,plan=await read(floor.plan);
    assert.equal(plan.owner,'scripts/unreal/exterior-grove-substrate.py');
    assert.deepEqual(floor.audit,plan.audit,'Grove substrate audit differs from pinned plan');
    assert.deepEqual(floor.meshIds,plan.meshes.map(m=>m.id),'Grove substrate saved mesh inventory differs');
    assert.equal(report.materials.materials.canopy_floor_litter.recipe.sourceUrl,'https://polyhaven.com/a/forest_leaves_04');
    assert.equal(report.materials.materials.canopy_floor_litter.recipe.stochasticGround,false);
    assert.equal(report.materials.materials.canopy_floor_litter.recipe.tileCm,150);
  }
  assert.deepEqual(report.savedPlantReadback.map(r=>r.id).sort(),plants.meshes.map(r=>r.id).sort());
  for(const row of report.savedPlantReadback){
    const expected=plants.meshes.find(m=>m.id===row.id);
    assert(row.mesh.startsWith('/Game/Brezi/Exterior20260926/Geometry/'));
    assert.deepEqual(row.lodTriangles,expected.lods.map(l=>l.triangles));
    const screens=plantLodScreenSizes(expected);
    assert.equal(row.lodScreens.length,3);assert(row.lodScreens.every((n,i)=>Math.abs(n-screens[i])<1e-5));
    assert.deepEqual([...row.materials].sort(),expected.materialKeys.map(k=>report.materials.materials[k].asset).sort());
  }
  const saved=await read(resolve(project,'Content/Data/viewpoints.json'));assert.deepEqual(saved,report.viewpoints.after);
  return {content,inputs,exterior:{status:report.status,report:file,reportSha256:host.reportSha256,parcelCount:report.context.parcelCount,instanceCount:report.savedGeometryReadback.instanceCount,nativeRenderedVerified:false,
    ...(report.regionalVegetation?{regionalVegetation:report.regionalVegetation}:{}),
    ...(report.naturalLawn?{naturalLawn:report.naturalLawn}:{}),
    ...(report.canopyReplacement?{canopyReplacement:report.canopyReplacement}:{}),
    ...(report.canopyEcology?{canopyEcology:report.canopyEcology}:{}),
    ...(report.groveSubstrate?{groveSubstrate:report.groveSubstrate}:{}),
    ...(report.neighborhoodTransition?{neighborhoodTransition:report.neighborhoodTransition}:{}),
    ...(report.meadowInfill?{meadowInfill:report.meadowInfill}:{}),
    ...(report.continuousMeadow?{continuousMeadow:report.continuousMeadow}:{}),
    ...(report.seasonalFields?{seasonalFields:report.seasonalFields}:{}),
    ...(report.fieldMacro?{fieldMacro:report.fieldMacro}:{}),
    ...(report.orthophoto?{orthophoto:report.orthophoto}:{})}};
}
