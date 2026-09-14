/** User-supplied brief, 14 September 2026. Unknown survey/design values stay null. */
export const CLIENT_BRIEF = {
  revision: 'CLIENT-CONSTRUCTION-20260914-FULL-CAST-FOOTPRINT',
  source: 'Priame zadanie stavebníka a dve priložené fotografie, 14.09.2026',
  datum: {
    code: 'R0', elevationM: 184.2, relativeMm: 0,
    location: 'Najvyšší bod ulice pri rohu pracovne podľa stavebníka / informácie geodeta',
    evidence: 'CLIENT_REPORTED_SURVEY_VALUE', verticalSystem: null, xyMm: null,
    finishedFloorAboveRoadMm: null,
    modelZero: 'M0 = pôvodná hotová podlaha modelu; nie R0',
    streetCorniceLimitAboveRoadMm: 4500,
    finishedFloorDesignBy: 'PROJECT_DESIGN',
  },
  entrance: {
    minimumStepCount: 1, designStatus: 'COORDINATION_PROPOSAL',
    proposedRiserMm: 150, proposedLandingDepthMm: 1500,
    landingDropBelowFinishedFloorMm: null, landingSlopePercent: null,
    absoluteElevations: null,
    reference: 'Stupeň medzi miestnym prístupom a podestou; neurčuje výšku podlahy nad ulicou R0',
  },
  foundations: {
    system: 'MONOLITHIC_CAST_IN_PLACE', permanentConcreteBlocks: false,
    reportedCastScope: {
      statement: 'Doska je podľa stavebníka vyliata aj s lodžiou a krytou terasou.',
      includesLoggia: true, includesCoveredTerrace: true,
      extent: 'FULL_L_FOOTPRINT', evidence: 'CLIENT_REPORTED', surveyVerified: false,
      measuredBoundaryMm: null, measuredThicknessMm: null, existingRibLayout: null,
    },
    reportedExistingLowerStrip: {
      depthBelowLocalGroundMm: 600, widthMm: null, topAboveRoadMm: null,
      reinforcement: null, concreteReported: '16/20', verifiedConcreteDelivery: false,
    },
    requestedUpperStrip: { widthMm: 350, heightMm: 600, planOffsetToMasonryMm: null },
    requestedRibs: { heightMm: 600, widthMm: null, reinforcement: null, supportCondition: null },
    slab: { requestedThicknessRangeMm: [150, 200], selectedThicknessMm: null, topAboveRoadMm: null, topAboveUpperStripMm: null },
    fill: { requestedMaterial: 'Zhutnená zemina podľa stavebníka', verifiedSuitability: false, acceptanceParameters: null },
    concrete: { requestedClass: 'C16/20', designApprovedClass: null, exposureClass: null },
    photos: [
      'output/research/construction-site-20260914/01-concrete-strip-detail.png',
      'output/research/construction-site-20260914/02-foundation-overview.png',
    ],
    visibleObservation: 'Na detailnej fotografii je viditeľná trhlina a nerovnomerný povrch. Rozsah, príčina a závažnosť nie sú z fotografie určené.',
  },
  services: {
    waterAndWasteAboveStructuralSlab: true, drilledSlabPenetrations: false,
    heatedRoomExclusions: ['1.07', '1.12'],
    showerExcluded: true, showerInterpretation: 'Sprchová plocha v 1.05; nejde o potvrdené vylúčenie celej kúpeľne',
    hydronicCircuitDesign: null, floorAssemblyThicknessMm: null,
  },
  roof: {
    covering: 'Falcovaný plech / stojatá drážka', architecturalOverhangMm: 0,
    accessibleAtticExceptRoom: '1.03', atticUse: 'STORAGE_ONLY', atticUseConfirmedBy: 'CLIENT', atticDesignLoad: null,
    habitableAttic: false, floorStructure: 'TIMBER', concreteFloorSlab: false, concreteFloorTopping: false,
    structuralScheme: 'Drevené pôdne väzníky v pravidelnom trakte, samostatné drevené stropné polia v uzle L a osobitná katedrálová sústava nad obývačkou; dimenzovanie podľa reakcií a skladovania',
    structuralMemberSizes: null, structuralApproval: false,
  },
} as const;

/** All quantities in mm. A slab above the strip and flush top faces are distinct joints. */
export function floorFromFoundation(existingStripTopAboveRoadMm: number | null, slabTopAboveUpperStripMm: number | null, floorAssemblyMm: number | null) {
  if (existingStripTopAboveRoadMm === null || slabTopAboveUpperStripMm === null || floorAssemblyMm === null) return null;
  return existingStripTopAboveRoadMm + CLIENT_BRIEF.foundations.requestedUpperStrip.heightMm + slabTopAboveUpperStripMm + floorAssemblyMm;
}

/** No fallback to historical HOUSE.datumElevationM or an assumed floor offset. */
export function elevationBasis(modelElevationMm: number, floorOffsetMm: number | null = CLIENT_BRIEF.datum.finishedFloorAboveRoadMm) {
  return {
    modelMm: modelElevationMm,
    aboveRoadMm: floorOffsetMm === null ? null : modelElevationMm + floorOffsetMm,
    absoluteM: floorOffsetMm === null ? null : CLIENT_BRIEF.datum.elevationM + (modelElevationMm + floorOffsetMm) / 1000,
    absoluteBaseM: CLIENT_BRIEF.datum.elevationM + modelElevationMm / 1000,
    expression: `184.200 + ΔFFL + ${(modelElevationMm / 1000).toFixed(3)} m`,
  };
}
