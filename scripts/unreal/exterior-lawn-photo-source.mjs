import assert from 'node:assert/strict';

export const PHOTO_LAWN_OWNER='scripts/unreal/exterior-lawn-photo-integration.py';
export const PHOTO_LAWN_STATUS='MEASURED_PHOTOGRAPHIC_MANAGED_LAWN_NOT_NATIVE_ACCEPTED';
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const number=(value,min,max)=>Number.isFinite(value)&&value>=min&&value<=max;
const centers=[[-630,-650],[-950,-860],[-1180,-950],[-630,-450]];

export function validatePhotographicLawnCoverage(audit) {
  assert.equal(audit.status,PHOTO_LAWN_STATUS);
  assert.equal(audit.instances,102011);assert.equal(audit.groups,40);
  assert.equal(audit.originalMasters,100);assert.equal(audit.additionalPhotoMasters,20);
  assert.equal(audit.mergedMasters,120);assert.equal(audit.mergedLods,360);
  assert.deepEqual(audit.allInstancesTriangleBudgetByLod,[18571200,18571200,18571200]);
  for(const key of ['allSourceGeometryExceptUv0TangentsPreserved','originalPlacementsPoliciesPreserved',
    'original100MasterRecordsPreserved'])assert.equal(audit[key],true,key);
  for(const key of ['nativeVerified','nativeAppearanceAccepted','fullPhotorealismAccepted',
    'performanceAccepted','integrationAuthorized'])assert.equal(audit[key],false,key);
  const physical=audit.physicalCoverage;
  assert.deepEqual(physical.criteria,{minimumTopViewCoverage:.75,preferredTopViewCoverage:.80,
    minimumTenCmBinP10:.55,maximumPermittedBladeLossAcrossLods:0});
  assert.equal(physical.windows.length,4);
  for(const [index,window] of physical.windows.entries()) {
    assert.deepEqual(window.centerCm,centers[index]);
    assert.equal(window.sizeCm,100);assert.equal(window.resolution,4000);
    assert.deepEqual(window.lods.map(row=>row.lod),[0,1,2]);
    for(const row of window.lods) {
      assert(number(row.projectedCoverage,.75,1),'Photographic lawn coverage failed');
      assert(number(row.tenCmBinCoverageP10,.55,1),'Photographic lawn P10 failed');
      assert(number(row.tenCmBinCoverageMinimum,0,row.tenCmBinCoverageP10));
      assert.equal(row.bareTenCmBins,0);assert.equal(row.studyTargetsMet,true);
    }
    for(const row of window.lods.slice(1))assert.deepEqual({...row,lod:0},window.lods[0],
      'Photographic lawn loses coverage across LODs');
  }
  const boundary=audit.boundaryCoverage;
  assert.deepEqual(boundary.criteria,{minimumPhysicalCoverByBoundaryBand:{'1to10mm':.12,'10to30mm':.40,'30to100mm':.50},outsideSourceDomainPermittedCm:0});
  assert.deepEqual(boundary.windows.map(row=>row.boundaryId),['deck','mulch']);
  for(const [index,window] of boundary.windows.entries()) {
    const [a,b]=[[[-476,-650],[-476,-400]],[[-1124,-440],[-1016,-500]]][index];
    const length=Math.hypot(b[0]-a[0],b[1]-a[1]);const axis=b.map((v,k)=>(v-a[k])/length);
    const inward=index===0?[-axis[1],axis[0]]:[axis[1],-axis[0]];
    assert.deepEqual(window.originCm,a);assert.equal(window.widthCm,40);assert.equal(window.pixelSizeMm,.25);
    assert(Math.abs(window.lengthCm-length)<1e-9);
    assert(window.axisUnitXY.every((v,k)=>Math.abs(v-axis[k])<1e-9));
    assert(window.inwardUnitXY.every((v,k)=>Math.abs(v-inward[k])<1e-9));
    assert.deepEqual(window.resolutionXY,[1600,Math.ceil(length/.025)]);
    assert.deepEqual(window.lods.map(row=>row.lod),[0,1,2]);
    for(const row of window.lods) {
      assert(number(row.projectedCoverage,0,1));assert.equal(row.studyTargetsMet,true);
      assert.equal(row.boundaryBands.length,3);
      for(const [bandIndex,band] of row.boundaryBands.entries()) {
        assert.deepEqual(band.distanceFromBoundaryMm,[[1,10],[10,30],[30,100]][bandIndex]);
        assert(number(band.physicalCoverFraction,[.12,.40,.50][bandIndex],1),'Photographic boundary coverage failed');
      }
    }
    for(const row of window.lods.slice(1))assert.deepEqual({...row,lod:0},window.lods[0]);
  }
}

export function validatePhotographicLawnReceipt(report) {
  const audit=report.naturalLawn.audit;
  validatePhotographicLawnCoverage(audit);
  for(const key of ['photographicAlphaCoverage','oldBaseCoverageReceipt','oldBaseBoundaryCoverageReceipt']) {
    const pin=audit[key];assert(pin&&hash(pin.sha256)&&report.inputFiles[pin.path]===pin.sha256,
      'Photographic lawn source pin missing: '+key);
  }
  const material=report.materials.materials.lawn_photographic_blade;
  const provider=report.materials.materials.ph_grass_medium_02;
  assert(material&&provider,'Photographic lawn shader is missing');
  assert.deepEqual(material.recipe,provider.recipe);assert.equal(material.graphSha256,provider.graphSha256);
  assert.equal(Object.keys(report.materials.materials).length,42);
  assert.equal(Object.keys(report.materials.textures).length,74);
  const photo=report.materials.photographicLawn;
  assert.equal(photo.owner,'scripts/unreal/exterior-lawn-photo-materials-study.py');
  assert.equal(photo.status,'appended-photographic-lawn-material-awaiting-native-reload');
  assert(hash(photo.sourceSha256));
  assert(Object.entries(report.pipelineFiles).some(([path,value])=>path.endsWith('/'+photo.owner)&&value===photo.sourceSha256));
  assert(hash(photo.sourceManifest.sha256)&&report.inputFiles[photo.sourceManifest.path]===photo.sourceManifest.sha256);
  assert.equal(photo.materialKey,'lawn_photographic_blade');
  assert.equal(photo.newGraphSha256,material.graphSha256);assert.equal(photo.providerGraphSha256,provider.graphSha256);
  assert.equal(photo.newGraphEqualsProviderGraph,true);assert.equal(photo.uvChannel,0);
  assert.equal(photo.COLOR0Used,false);assert.equal(photo.regeneratedUv0TangentsRequired,true);
  assert.equal(photo.priorMaterials,41);assert.equal(photo.finalMaterials,42);
  assert.equal(photo.textures,74);assert.equal(photo.additionalTextures,0);
  assert.equal(photo.allPrior41ReportsAndGraphsUnchanged,true);
  assert.equal(photo.sourceEncodingOverridesAdded,0);
  assert.equal(photo.nativeVisualAccepted,false);assert.equal(photo.performanceAccepted,false);
}

export function validatePhotographicLawnPlan(report,plan,alphaReceipt) {
  assert.equal(plan.owner,PHOTO_LAWN_OWNER);assert.equal(plan.audit.status,PHOTO_LAWN_STATUS);
  assert.deepEqual(report.naturalLawn.audit,plan.audit);
  validatePhotographicLawnReceipt(report);
  assert.equal(alphaReceipt.status,'PASS_SOURCE_PHOTOGRAPHIC_ALPHA_COVERAGE_NATIVE_PENDING');
  assert.equal(alphaReceipt.opaqueBaselineReproducedExactly,true);
  assert.equal(alphaReceipt.pixelSizeMm,.25);assert.equal(alphaReceipt.alphaClipValue,.333);
  for(const key of ['sourceAlphaPixelsUnmodified','all3LodGeometryUvAndTangentByteEqualityVerified',
    'sameRasterCopiedToOtherLodsOnlyAfterExactByteEquality','allTargetsMet',
    'noDensityRootsGeometryOrSourceDomainChanges'])assert.equal(alphaReceipt[key],true,key);
  assert.equal(alphaReceipt.uniqueGeometryRasterRuns,6);assert.equal(alphaReceipt.nativeJobsRun,0);
  for(const key of ['nativeVisualAccepted','fullPhotorealismAccepted','performanceAccepted'])
    assert.equal(alphaReceipt[key],false,key);
  assert.deepEqual(plan.audit.physicalCoverage,alphaReceipt.physicalCoverage);
  assert.deepEqual(plan.audit.boundaryCoverage,alphaReceipt.boundaryCoverage);
  assert.equal(plan.groups.length,40);assert.equal(plan.lawnPlacements.length,102011);
  for(const group of plan.groups) {
    const actual=report.geometry.groups[group.id];assert(actual,'Photographic lawn group is missing');
    assert(group.meshId.startsWith('lawn_photo_'));
    const mesh=report.savedPlantReadback.find(row=>row.id===group.meshId);assert(mesh);
    assert.equal(actual.mesh,mesh.mesh);assert.equal(actual.instances,group.instances.length);
    assert.equal(actual.qualityDetail,group.qualityDetail);
    assert.equal(actual.cullEndCm,group.cullEndCm);
  }
}
