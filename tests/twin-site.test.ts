import { describe, expect, it } from "vitest";

import {
  CADASTRAL_PARCELS,
  TERRACE_ZONES_D1,
  terraceZoneAreaM2,
  DEFAULT_LAYER_VISIBILITY,
  FOUNDATIONS,
  GARDEN_POOL,
  HOUSE,
  ROAD_CONTEXT,
  SITE_FENCE,
  SITE_SURFACES,
  SOURCES,
  UTILITY_ROUTES,
  foundationVolumeM3,
  findSource,
  lineLengthMm,
  polygonAreaM2,
  sjtskToLocalMm,
  updateFoundationWidth,
} from "../lib/twin-site";
import {
  GARDEN_CAMERA_ALPHA,
  GARDEN_CAMERA_BETA,
  TOP_CAMERA_ALPHA,
  arcRotateCameraHeightM,
  focusRadiusForBoundingSphere,
  gardenCameraForWidth,
  sceneDeltaForPlanSegment,
  sceneXM,
  sceneYawForPlanSegment,
  sceneZM,
  streetCameraForWidth,
} from "../lib/twin-render-frame";
import { segmentFacadeMm } from "../lib/twin-facade";
import { slatCenterDistancesMm } from "../lib/twin-fence";
import { roofHeightMm, roofMountTransform } from "../lib/twin-roof";

describe("site evidence seed", () => {
  it("projects official GP points into the road-aligned local frame", () => {
    const subject = CADASTRAL_PARCELS.find((parcel) => parcel.isSubject);
    expect(subject?.areaM2).toBe(753);
    const local = subject?.sjtskRingMm.map(sjtskToLocalMm);
    expect(local?.[8]).toEqual({ x: 0, y: 0 });
    expect(local?.[0]).toEqual({ x: 28_194, y: 0 });
    expect(local?.[6]).toEqual({ x: 31_109, y: 24_497 });
    expect(local?.[7]).toEqual({ x: -946, y: 23_200 });
    expect(SOURCES.cadastre.href).toContain("inspire-cp-wfs");
  });

  it("uses the later D1 floor plan without reflection and retains C3 as provenance", () => {
    expect(HOUSE.derivedFootprintAreaM2).toBe(252.965);
    expect(HOUSE.lowerBar.widthMm).toBe(21_600);
    expect(HOUSE.detailedRevision.widthMm).toBe(21_600);
    expect(HOUSE.detailedRevision.active).toBe(true);
    expect(HOUSE.detailedRevision.placementStatus).toBe("INFERRED_ALIGNMENT");
    expect(HOUSE.coordinationRevision.widthMm).toBe(20_800);
    expect(HOUSE.coordinationRevision.documentedBuiltUpAreaM2).toBe(246.4);
    expect(HOUSE.orientation).toMatchObject({
      reflection: "NONE",
      garageVolumeSide: "LOCAL_X_MIN",
      garageAccessSide: "LOCAL_Y_MIN",
      wingSide: "LOCAL_X_MAX",
    });
    expect(HOUSE.roof.mainPlanLengthMm).toBe(HOUSE.lowerBar.widthMm);
    expect(HOUSE.roof).toMatchObject({
      sourceId: SOURCES.roofPlan.id,
      topology: "JOINED_CROSS_GABLE",
      mainHalfSpanMm: 4_100,
      wingOverallPlanLengthMm: HOUSE.maximumDepthMm,
      wingExtensionPlanLengthMm: HOUSE.wing.depthMm,
      documentedWingRoofOverallLengthMm: 19_085,
      wingEndOverhangMm: 50,
    });
    expect(HOUSE.footprintMm).toEqual([
      { x: 6_440, y: 3_000 },
      { x: 28_040, y: 3_000 },
      { x: 28_040, y: 22_035 },
      { x: 21_040, y: 22_035 },
      { x: 21_040, y: 11_200 },
      { x: 6_440, y: 11_200 },
      { x: 6_440, y: 3_000 },
    ]);
    expect(SOURCES.coordination.detail).toContain("konflikt");
  });

  it("models 6012/26 as an end parcel with two road-facing edges", () => {
    expect(ROAD_CONTEXT.id).toBe("ROAD-6012-1");
    expect(ROAD_CONTEXT.featureId).toBe("CP.94487856010");
    expect(ROAD_CONTEXT.nationalReference).toBe("613908-6012/1");
    expect(ROAD_CONTEXT.registeredAreaM2).toBe(10_647);
    expect(ROAD_CONTEXT.legalBoundaryStatus).toBe("CURRENT_REGISTER");
    expect(ROAD_CONTEXT.surfaceEnvelopeStatus).toBe(
      "CURRENT_REGISTER_CLIPPED_CONTEXT",
    );
    expect(ROAD_CONTEXT.pavedSurfaceStatus).toBe(
      "C3_DERIVED_NOT_AS_BUILT_SURVEY",
    );
    expect(ROAD_CONTEXT.frontAsphaltEdgeYmm).toBe(-3_104);
    expect(ROAD_CONTEXT.frontReservePolygonMm).toEqual([
      { x: -15_670, y: 5 },
      { x: 0, y: 0 },
      { x: 28_194, y: 0 },
      { x: 28_194, y: -3_104 },
      { x: -15_670, y: -3_104 },
      { x: -15_670, y: 5 },
    ]);
    expect(
      ROAD_CONTEXT.frontReserveSurfacePolygonsMm.map((ring) => {
        const xs = ring.map(({ x }) => x);
        return [Math.min(...xs), Math.max(...xs)];
      }),
    ).toEqual([
      [-15_670, 6_490],
      [10_690, 21_415],
      [22_915, 28_194],
    ]);
    expect(ROAD_CONTEXT.touchedBoundarySegments).toEqual([
      "160–136",
      "136–135–134–133–132–131–130",
    ]);
    expect(ROAD_CONTEXT.cornerPolygonMm.slice(0, 7)).toEqual([
      { x: 28_194, y: 0 },
      { x: 28_922, y: 98 },
      { x: 29_721, y: 418 },
      { x: 30_613, y: 1_235 },
      { x: 31_081, y: 2_185 },
      { x: 31_187, y: 3_000 },
      { x: 31_109, y: 24_497 },
    ]);
    expect(ROAD_CONTEXT.sideAsphaltOffsetMm).toBe(3_104);
    expect(ROAD_CONTEXT.cornerAsphaltEdgeMm).toEqual([
      { x: 28_194, y: -3_104 },
      { x: 29_677, y: -2_913 },
      { x: 31_301, y: -2_254 },
      { x: 33_120, y: -595 },
      { x: 34_068, y: 1_342 },
      { x: 34_291, y: 3_000 },
      { x: 34_213, y: 24_497 },
    ]);
    expect(ROAD_CONTEXT.cornerReserveSurfacePolygonsMm).toHaveLength(2);
    expect(ROAD_CONTEXT.cornerCarriagewayPolygonMm[0]).toEqual(
      ROAD_CONTEXT.cornerAsphaltEdgeMm[0],
    );
  });

  it("preserves D1 handedness at the Babylon render boundary", () => {
    expect(sceneXM(28_040)).toBeGreaterThan(sceneXM(6_440));
    expect(sceneZM(22_035)).toBeLessThan(sceneZM(3_000));
    expect(sceneDeltaForPlanSegment({ x: 0, y: 0 }, { x: 0, y: 1000 })).toEqual({
      dx: 0,
      dz: -1,
    });
    expect(
      sceneYawForPlanSegment({ x: 0, y: 0 }, { x: 0, y: 1000 }),
    ).toBeCloseTo(Math.PI / 2, 12);
    expect(
      sceneYawForPlanSegment({ x: 0, y: 0 }, { x: 1000, y: 0 }),
    ).toBeCloseTo(0, 12);
    expect(TOP_CAMERA_ALPHA).toBe(Math.PI / 2);
    // The hero camera sits inside the rear hedge and looks back at both legs
    // of the garden facade from a natural standing/elevated eye height.
    expect(GARDEN_CAMERA_ALPHA).toBeCloseTo(-2.38, 12);
    expect(Math.cos(GARDEN_CAMERA_ALPHA)).toBeLessThan(0);
    expect(Math.sin(GARDEN_CAMERA_ALPHA)).toBeLessThan(0);
    expect(GARDEN_CAMERA_BETA).toBeGreaterThan(1.46);
    expect(GARDEN_CAMERA_BETA).toBeLessThan(1.49);
  });

  it("keeps the approved Realita camera deterministic on desktop and mobile", () => {
    expect(gardenCameraForWidth(1600)).toEqual({
      alpha: GARDEN_CAMERA_ALPHA,
      beta: GARDEN_CAMERA_BETA,
      radius: 17.2,
      fov: 0.68,
      target: [1.6, 1.4, -0.9],
    });
    expect(gardenCameraForWidth(600)).toEqual(gardenCameraForWidth(1600));
    expect(gardenCameraForWidth(390)).toMatchObject({
      alpha: GARDEN_CAMERA_ALPHA,
      radius: 18.4,
      fov: 0.9,
      target: [1.8, 1.45, -0.95],
    });
    expect(gardenCameraForWidth(599)).toEqual(gardenCameraForWidth(390));
    expect(gardenCameraForWidth(1600).radius).toBeLessThan(
      gardenCameraForWidth(390).radius,
    );
    expect(arcRotateCameraHeightM(gardenCameraForWidth(1600))).toBeCloseTo(
      3.05,
      10,
    );
    expect(arcRotateCameraHeightM(gardenCameraForWidth(390))).toBeCloseTo(
      3.2,
      10,
    );
    expect(arcRotateCameraHeightM(streetCameraForWidth(1600))).toBeCloseTo(
      1.85,
      10,
    );
    expect(arcRotateCameraHeightM(streetCameraForWidth(390))).toBeCloseTo(
      2,
      10,
    );
    expect(streetCameraForWidth(390).radius).toBeGreaterThan(
      streetCameraForWidth(1600).radius,
    );
    expect(focusRadiusForBoundingSphere(4, 0.68, 16 / 9)).toBeLessThan(
      focusRadiusForBoundingSphere(4, 0.68, 9 / 16),
    );
    expect(focusRadiusForBoundingSphere(0, 0, 0)).toBe(4.5);
    expect(focusRadiusForBoundingSphere(100, 0.68, 16 / 9)).toBe(64);
  });

  it("keeps the hero facade and PV layout source-driven", () => {
    expect(HOUSE.facades.garden.faceYmm).toBe(11_200);
    expect(HOUSE.facades.garden.openings).toEqual([
      {
        id: "GARDEN-01",
        startXmm: 9_290,
        widthMm: 1_250,
        heightMm: 2_400,
        sillMm: 0,
      },
      {
        id: "GARDEN-02",
        startXmm: 11_840,
        widthMm: 2_500,
        heightMm: 2_400,
        sillMm: 0,
      },
      {
        id: "GARDEN-03",
        startXmm: 15_840,
        widthMm: 2_000,
        heightMm: 2_400,
        sillMm: 0,
      },
    ]);
    expect(HOUSE.facades.garden.larchFeature).toEqual({
      startXmm: 7_440,
      widthMm: 1_850,
      heightMm: 2_400,
      certainty: "INFERRED_FROM_LATER_PLAN",
    });
    expect(HOUSE.facades.wingEnd).toMatchObject({
      faceYmm: 22_035,
      startXmm: 21_040,
      widthMm: 7_000,
      opening: { widthMm: 2_400, heightMm: 2_400, sillMm: 0 },
    });
    expect(HOUSE.photovoltaics).toMatchObject({
      moduleCount: 6,
      wattsPerModule: 405,
      layout: "2x3_CLIENT_REVISION",
      roofFace: "WING_INNER",
      facing: "COURTYARD",
      placement: "GARDENWARD_ON_WING_INNER",
      towardTerraceId: "TERR-D1-WING",
      previousFirstModuleCenterMm: { x: 21_820, y: 12_600 },
      gardenShiftMm: 2_000,
      firstModuleCenterMm: { x: 21_820, y: 14_600 },
      rowStepMm: { x: 1_550, y: 0 },
      columnStepMm: { x: 0, y: 1_100 },
    });
    expect(HOUSE.photovoltaics.rows * HOUSE.photovoltaics.columns).toBe(
      HOUSE.photovoltaics.moduleCount,
    );
    expect(
      TERRACE_ZONES_D1.some(
        ({ id }) => id === HOUSE.photovoltaics.towardTerraceId,
      ),
    ).toBe(true);
    const photovoltaicCenters = Array.from(
      { length: HOUSE.photovoltaics.columns },
      (_, column) =>
        Array.from({ length: HOUSE.photovoltaics.rows }, (_, row) => ({
          x:
            HOUSE.photovoltaics.firstModuleCenterMm.x +
            row * HOUSE.photovoltaics.rowStepMm.x +
            column * HOUSE.photovoltaics.columnStepMm.x,
          y:
            HOUSE.photovoltaics.firstModuleCenterMm.y +
            row * HOUSE.photovoltaics.rowStepMm.y +
            column * HOUSE.photovoltaics.columnStepMm.y,
        })),
    ).flat();
    expect(photovoltaicCenters).toEqual([
      { x: 21_820, y: 14_600 },
      { x: 23_370, y: 14_600 },
      { x: 21_820, y: 15_700 },
      { x: 23_370, y: 15_700 },
      { x: 21_820, y: 16_800 },
      { x: 23_370, y: 16_800 },
    ]);
    expect(
      sceneZM(HOUSE.photovoltaics.firstModuleCenterMm.y) -
        sceneZM(HOUSE.photovoltaics.previousFirstModuleCenterMm.y),
    ).toBe(-2);
    for (const center of photovoltaicCenters) {
      const mount = roofMountTransform(
        HOUSE.photovoltaics.roofFace,
        center.x,
        center.y,
      );
      expect(mount.elevationMm).toBe(
        roofHeightMm(HOUSE.photovoltaics.roofFace, center.x, center.y),
      );
      expect(mount.elevationMm).toBeGreaterThan(HOUSE.eavesElevationMm);
      expect(mount.rotationXRad).toBe(0);
      expect(mount.rotationZRad).toBeGreaterThan(0);

      const frameHalfSlopePlanMm =
        ((HOUSE.photovoltaics.moduleSlopeLengthMm + 40) / 2) *
          Math.cos(mount.rotationZRad) +
        8 * Math.sin(mount.rotationZRad);
      const frameHalfRidgeMm =
        (HOUSE.photovoltaics.moduleRidgeWidthMm + 40) / 2;
      expect(center.x - frameHalfSlopePlanMm).toBeGreaterThanOrEqual(
        HOUSE.originMm.x + HOUSE.wing.xMm,
      );
      expect(center.x + frameHalfSlopePlanMm).toBeLessThanOrEqual(
        HOUSE.originMm.x + HOUSE.wing.xMm + HOUSE.roof.wingHalfSpanMm,
      );
      expect(center.y - frameHalfRidgeMm).toBeGreaterThanOrEqual(
        HOUSE.originMm.y + HOUSE.wing.yMm,
      );
      expect(center.y + frameHalfRidgeMm).toBeLessThanOrEqual(
        HOUSE.originMm.y + HOUSE.roof.wingOverallPlanLengthMm,
      );

      for (const chimney of HOUSE.chimneys) {
        const chimneyCapHalfMm = 290;
        const overlapsChimneyCap =
          center.x - frameHalfSlopePlanMm <
            chimney.centerMm.x + chimneyCapHalfMm &&
          center.x + frameHalfSlopePlanMm >
            chimney.centerMm.x - chimneyCapHalfMm &&
          center.y - frameHalfRidgeMm <
            chimney.centerMm.y + chimneyCapHalfMm &&
          center.y + frameHalfRidgeMm >
            chimney.centerMm.y - chimneyCapHalfMm;
        expect(overlapsChimneyCap).toBe(false);
      }
    }
    expect(
      Math.min(...photovoltaicCenters.map(({ y }) => y)) -
        (HOUSE.photovoltaics.moduleRidgeWidthMm + 40) / 2 -
        (HOUSE.chimneys[0].centerMm.y + 290),
    ).toBe(1_080);
    expect(HOUSE.facades.front.garageDoor).toMatchObject({
      id: "GARAGE-DOOR",
      startXmm: 6_940,
      widthMm: 3_300,
      heightMm: 2_400,
      sillMm: 0,
      access: "DIRECT_FROM_STREET",
      sourceId: SOURCES.clientRevision20260821.id,
    });
    expect(HOUSE.facades.front.openings[0]).toEqual(
      {
        id: "FRONT-02",
        startXmm: 11_715,
        widthMm: 1_250,
        heightMm: 750,
        sillMm: 1_750,
      },
    );
    expect(HOUSE.facades.front.openings.some(({ id }) => id === "FRONT-01")).toBe(
      false,
    );
    expect("garageDoor" in HOUSE.facades.west).toBe(false);
    expect(HOUSE.chimneys).toEqual([
      {
        id: "CHIMNEY-LIVING-103",
        centerMm: { x: 24_190, y: 12_700 },
        designCenterMm: { x: 24_190, y: 11_700 },
        gardenShiftMm: 1_000,
        zone: "MAIN_LIVING_AND_KITCHEN_1_03",
        baseSourceId: SOURCES.roofPlan.id,
        sourceId: SOURCES.clientRevision20260821.id,
      },
    ]);
    expect(
      sceneZM(HOUSE.chimneys[0].centerMm.y) -
        sceneZM(HOUSE.chimneys[0].designCenterMm.y),
    ).toBe(-1);
    expect(
      HOUSE.originMm.x +
        HOUSE.wing.xMm +
        HOUSE.roof.wingHalfSpanMm -
        (HOUSE.chimneys[0].centerMm.x + 290),
    ).toBe(60);
    expect(HOUSE.removedChimneys).toEqual([
      {
        id: "CHIMNEY-ROOM-109",
        centerMm: { x: 17_640, y: 7_250 },
        zone: "ROOM_1_09_ROOF_ZONE",
        sourceId: SOURCES.clientRevision20260821.id,
      },
    ]);
    expect(SOURCES.clientRevision20260821.kind).toBe("CLIENT_REVISION");
    expect(HOUSE.rainwaterDownpipes).toEqual([
      {
        id: "DS-01",
        xMm: 7_600,
        faceYmm: 11_200,
        sourceRouteId: "UTIL-RAIN-SOUTH",
        certainty: "VISUAL_INFERENCE",
      },
      {
        id: "DS-02",
        yMm: 21_700,
        faceXmm: 28_040,
        sourceRouteId: "UTIL-RAIN-NORTH",
        certainty: "VISUAL_INFERENCE",
      },
    ]);
    // The gable front of the porch is open: no downpipe may stand in it.
    for (const downpipe of HOUSE.rainwaterDownpipes) {
      expect("faceYmm" in downpipe && downpipe.faceYmm === HOUSE.porches.wingEnd.frontYmm).toBe(false);
    }
    expect(DEFAULT_LAYER_VISIBILITY.foundations).toBe(false);
    expect(DEFAULT_LAYER_VISIBILITY.contextNetworks).toBe(false);
  });

  it("retains exact current ZTI nodes and superseding tank capacities", () => {
    const water = UTILITY_ROUTES.find((route) => route.id === "UTIL-WATER");
    const sewer = UTILITY_ROUTES.find((route) => route.id === "UTIL-SEWER");
    expect(water?.pointsMm).toEqual([
      { x: 13_500, y: -1_689 },
      { x: 13_500, y: 1_415 },
      { x: 12_861, y: 1_415 },
      { x: 12_861, y: 3_000 },
    ]);
    expect(sewer?.pointsMm.at(-1)).toEqual({ x: 16_814, y: 1_483 });
    expect(SITE_SURFACES.timberTerrace.areaM2).toBe(53);
    expect(SOURCES.rainwater.detail).toContain("konflikt");
  });

  it("connects the relocated garage door directly to the street", () => {
    const drivewayXs = SITE_SURFACES.driveway.polygonMm.map(({ x }) => x);
    const drivewayYs = SITE_SURFACES.driveway.polygonMm.map(({ y }) => y);
    const garageDoor = HOUSE.facades.front.garageDoor;
    expect(SITE_SURFACES.driveway.polygonMm.slice(0, 2)).toEqual([
      { x: 6_490, y: HOUSE.facades.front.faceYmm },
      { x: 10_690, y: HOUSE.facades.front.faceYmm },
    ]);
    expect(Math.min(...drivewayXs)).toBeLessThan(garageDoor.startXmm);
    expect(Math.max(...drivewayXs)).toBeGreaterThan(
      garageDoor.startXmm + garageDoor.widthMm,
    );
    expect(Math.max(...drivewayYs)).toBe(HOUSE.facades.front.faceYmm);
    expect(Math.min(...drivewayYs)).toBeLessThan(0);
    expect((Math.min(...drivewayXs) + Math.max(...drivewayXs)) / 2).toBe(
      garageDoor.startXmm + garageDoor.widthMm / 2,
    );
    expect(SITE_SURFACES.driveway.areaM2).toBeCloseTo(4.2 * 6.104, 3);
    expect(SITE_SURFACES.driveway.placementStatus).toBe(
      "CLIENT_REVISION_WITH_C3_DERIVED_STREET_EDGE",
    );
    expect(SITE_SURFACES.driveway.sourceId).toBe(
      SOURCES.clientRevision20260821.id,
    );
    const electricity = UTILITY_ROUTES.find(
      (route) => route.id === "UTIL-ELECTRICITY",
    );
    expect(electricity?.revisionStatus).toBe("REVISION_CONFLICT");
    expect(DEFAULT_LAYER_VISIBILITY.electricity).toBe(false);
  });

  it("centers a separate 1.5 m pedestrian path on the main entrance", () => {
    const entryXs = SITE_SURFACES.entry.polygonMm.map(({ x }) => x);
    const entryYs = SITE_SURFACES.entry.polygonMm.map(({ y }) => y);
    expect([Math.min(...entryXs), Math.max(...entryXs)]).toEqual([
      21_415, 22_915,
    ]);
    expect(Math.max(...entryXs) - Math.min(...entryXs)).toBe(1_500);
    expect((Math.min(...entryXs) + Math.max(...entryXs)) / 2).toBe(22_165);
    expect(Math.max(...entryYs)).toBe(HOUSE.facades.front.faceYmm);
    expect(Math.min(...entryYs)).toBe(-3_104);
    expect(SITE_SURFACES.entry.accessOpeningId).toBe("FRONT-ENTRY");
    expect(SITE_SURFACES.entry.streetConnection).toMatchObject({
      cadastralBoundaryYmm: 0,
      asphaltEdgeYmm: -3_104,
    });
    expect(SITE_SURFACES.entry.placementStatus).toBe(
      "DESIGN_PROPOSAL_CENTERED_ON_MAIN_ENTRY",
    );
  });

  it("centers the visible side approach on EAST-03 instead of the old C3 bin pad", () => {
    const sideDoor = HOUSE.facades.east.openings.find(
      ({ id }) => id === "EAST-03",
    );
    const nextWindow = HOUSE.facades.east.openings.find(
      ({ id }) => id === "EAST-04",
    );
    expect(sideDoor).toBeDefined();
    expect(nextWindow).toBeDefined();

    const approach = SITE_SURFACES.sideEntryApproach;
    const source = SITE_SURFACES.supersededBinPad;
    expect(approach).toMatchObject({
      id: "SITE-SIDE-ENTRY-APPROACH",
      areaM2: 11.202,
      accessOpeningId: "EAST-03",
      placementStatus: "CLIENT_REVISION_ALIGNED_TO_SIDE_DOOR",
      sourceSurfaceId: source.id,
      sourceId: SOURCES.clientRevision20260821.id,
      streetConnection: {
        sideAsphaltOffsetMm: 3_104,
        privateAreaM2: 5.578,
        roadReserveAreaM2: 5.624,
      },
    });
    expect(source.placementStatus).toBe(
      "SUPERSEDED_BY_CLIENT_SIDE_ENTRY_ALIGNMENT",
    );
    expect(Math.max(...approach.polygonMm.map(({ x }) => x))).toBe(34_268);
    expect(Math.max(...approach.privatePolygonMm.map(({ x }) => x))).toBe(
      31_163,
    );

    const approachXs = approach.polygonMm.map(({ x }) => x);
    const approachYs = approach.polygonMm.map(({ y }) => y);
    const minX = Math.min(...approachXs);
    const minY = Math.min(...approachYs);
    const maxY = Math.max(...approachYs);
    const sideDoorEndY = sideDoor!.startYmm + sideDoor!.widthMm;
    expect(Math.abs(minX - HOUSE.facades.east.faceXmm)).toBeLessThanOrEqual(2);
    expect((minY + maxY) / 2).toBe(
      sideDoor!.startYmm + sideDoor!.widthMm / 2,
    );
    expect(sideDoor!.startYmm - minY).toBe(400);
    expect(maxY - sideDoorEndY).toBe(400);
    expect(maxY).toBeLessThan(nextWindow!.startYmm);

    const derivedAreaM2 =
      Math.abs(
        approach.polygonMm.slice(0, -1).reduce((twiceArea, point, index) => {
          const next = approach.polygonMm[index + 1];
          return twiceArea + point.x * next.y - next.x * point.y;
        }, 0),
      ) / 2_000_000;
    expect(derivedAreaM2).toBeCloseTo(approach.areaM2, 3);
  });

  it("translates the yellow garden enclosure and green gate without moving the garage drive", () => {
    expect(SITE_FENCE).toMatchObject({
      id: "SITE-FENCE",
      parcelId: "PARCEL-6012/26",
      enclosure: "PRIVATE_GARDEN",
      datumYmm: HOUSE.facades.front.faceYmm,
      specificationStatus: "CLIENT_SELECTION_PENDING",
      approvedHeightMm: null,
      approvedMaterial: null,
    });
    expect(SOURCES.clientFenceMarkup20260821.kind).toBe("CLIENT_REVISION");
    expect(SOURCES.clientGardenRevision20260821.kind).toBe("CLIENT_REVISION");
    expect(SOURCES.fenceDesignProposal20260821.kind).toBe("DESIGN_PROPOSAL");
    expect(SITE_FENCE.sourceIds.every((sourceId) => findSource(sourceId))).toBe(
      true,
    );
    expect(
      SITE_FENCE.vehicleGate.sourceIds.every((sourceId) =>
        findSource(sourceId),
      ),
    ).toBe(true);
    expect(
      SITE_FENCE.sidePedestrianGate.sourceIds.every((sourceId) =>
        findSource(sourceId),
      ),
    ).toBe(true);
    expect(SITE_FENCE.sidePedestrianGate.sourceIds).not.toContain(
      SOURCES.clientFenceMarkup20260821.id,
    );

    expect(SITE_FENCE.annotatedCenterlineRuns).toEqual([
      {
        id: "FENCE-MARKUP-FRONT-LEFT",
        label: "Ľavé čelné uzatvorenie záhrady",
        pointsMm: [{ x: -122, y: 3000 }, { x: 2235, y: 3000 }],
        alignment: "CLIENT_FRONT_DATUM",
      },
      {
        id: "FENCE-MARKUP-FRONT-RIGHT",
        label: "Pravé čelné uzatvorenie záhrady",
        pointsMm: [{ x: 28040, y: 3000 }, { x: 31187, y: 3000 }],
        alignment: "CLIENT_FRONT_DATUM",
      },
      {
        id: "FENCE-MARKUP-EAST",
        label: "Východná hranica záhrady",
        pointsMm: [{ x: 31187, y: 3000 }, { x: 31109, y: 24497 }],
        alignment: "CADASTRAL_BOUNDARY",
      },
      {
        id: "FENCE-MARKUP-REAR",
        label: "Zadná hranica záhrady",
        pointsMm: [{ x: 31109, y: 24497 }, { x: -946, y: 23200 }],
        alignment: "CADASTRAL_BOUNDARY",
      },
      {
        id: "FENCE-MARKUP-WEST",
        label: "Západná hranica záhrady",
        pointsMm: [{ x: -946, y: 23200 }, { x: -122, y: 3000 }],
        alignment: "CADASTRAL_BOUNDARY",
      },
    ]);
    const tracedLengthMm = SITE_FENCE.annotatedCenterlineRuns.reduce(
      (total, run) => total + lineLengthMm(run.pointsMm),
      0,
    );
    expect(tracedLengthMm).toBe(79_299);

    const gate = SITE_FENCE.vehicleGate;
    expect(gate).toMatchObject({
      role: "SECONDARY_GARDEN_VEHICLE_GATE",
      startMm: { x: 2235, y: 3000 },
      endMm: { x: 6435, y: 3000 },
      leafClosureEndMm: { x: 6440, y: 3000 },
      centerMm: { x: 4335, y: 3000 },
      clearWidthMm: 4200,
      accessGarageDoorId: null,
      markupStatus: "CLIENT_MARKUP_EXACT",
      mechanismProposal: "TRIPLE_TELESCOPIC_TRACKED_SLIDING",
      mechanismStatus: "DESIGN_PROPOSAL_REQUIRES_CLIENT_CONFIRMATION",
      panelCount: 3,
      endSupport: "HOUSE_FACADE_BRACKET",
      terminalFrameCenterMm: { x: 6400, y: 3000 },
      facadeReceiver: {
        centerMm: { x: 6434, y: 3045 },
        widthMm: 12,
      },
      supportPostCentersMm: [{ x: 2175, y: 3045 }],
      proposedStackEnvelopeMm: 1900,
      stackPocketStartMm: { x: 335, y: 3000 },
    });
    expect(Math.hypot(
      gate.endMm.x - gate.startMm.x,
      gate.endMm.y - gate.startMm.y,
    )).toBe(gate.clearWidthMm);
    expect(SITE_FENCE.houseClosure).toMatchObject({
      startMm: HOUSE.footprintMm[0],
      endMm: HOUSE.footprintMm[1],
    });
    expect(SITE_FENCE.houseClosure.startMm.x - gate.endMm.x).toBe(5);
    expect(gate.alignmentSourceId).toBe(
      SITE_SURFACES.supersededSideDriveway.id,
    );
    expect(gate.clearWidthMm / gate.panelCount).toBeLessThanOrEqual(
      gate.availableStackPocketMm,
    );
    expect(gate.startMm.x - gate.stackPocketStartMm.x).toBe(
      gate.proposedStackEnvelopeMm,
    );
    expect(gate.proposedStackEnvelopeMm).toBeLessThanOrEqual(
      gate.availableStackPocketMm,
    );
    const vehiclePostHalfMm = SITE_FENCE.visualProposal.gatePostSizeMm / 2;
    expect(gate.supportPostCentersMm[0].x + vehiclePostHalfMm).toBe(
      gate.startMm.x,
    );
    expect(gate.supportPostCentersMm[0].x + vehiclePostHalfMm).toBeLessThan(
      HOUSE.originMm.x,
    );
    expect(gate.supportPostCentersMm[0].x + vehiclePostHalfMm).toBeLessThan(
      Math.min(...SITE_SURFACES.driveway.polygonMm.map(({ x }) => x)),
    );
    const terminalFrameHalfMm = 35;
    expect(gate.terminalFrameCenterMm.x + terminalFrameHalfMm).toBeLessThan(
      HOUSE.originMm.x,
    );
    expect(gate.terminalFrameCenterMm.x + terminalFrameHalfMm).toBeLessThan(
      Math.min(...SITE_SURFACES.driveway.polygonMm.map(({ x }) => x)),
    );
    expect(
      gate.facadeReceiver.centerMm.x + gate.facadeReceiver.widthMm / 2,
    ).toBe(HOUSE.originMm.x);

    const archivedDrive = SITE_SURFACES.supersededSideDriveway;
    expect(archivedDrive).toMatchObject({
      placementStatus: "SUPERSEDED_BY_CLIENT_DIRECT_GARAGE_ACCESS",
      supersededById: SITE_SURFACES.driveway.id,
    });
    const archivedCrossSectionXs: number[] = [];
    for (let index = 1; index < archivedDrive.polygonMm.length; index += 1) {
      const start = archivedDrive.polygonMm[index - 1];
      const end = archivedDrive.polygonMm[index];
      if (
        start.y === end.y ||
        3000 < Math.min(start.y, end.y) ||
        3000 > Math.max(start.y, end.y)
      ) {
        continue;
      }
      const ratio = (3000 - start.y) / (end.y - start.y);
      archivedCrossSectionXs.push(start.x + (end.x - start.x) * ratio);
    }
    archivedCrossSectionXs.sort((left, right) => left - right);
    expect(archivedCrossSectionXs).toHaveLength(2);
    expect(Math.abs(archivedCrossSectionXs[0] - gate.startMm.x)).toBeLessThan(1);
    expect(Math.abs(archivedCrossSectionXs[1] - gate.endMm.x)).toBeLessThanOrEqual(5);
    expect(
      Math.abs(
        (archivedCrossSectionXs[0] + archivedCrossSectionXs[1]) / 2 -
          gate.centerMm.x,
      ),
    ).toBeLessThanOrEqual(3);

    const directDriveXs = SITE_SURFACES.driveway.polygonMm.map(({ x }) => x);
    expect([Math.min(...directDriveXs), Math.max(...directDriveXs)]).toEqual([
      6490,
      10690,
    ]);
    expect(gate.centerMm.x).not.toBe(
      HOUSE.facades.front.garageDoor.startXmm +
        HOUSE.facades.front.garageDoor.widthMm / 2,
    );
    expect(gate.endMm.x).toBeLessThan(Math.min(...directDriveXs));

    const exactWestX = (-946 * 3000) / 23200;
    expect(Math.abs(SITE_FENCE.annotatedCenterlineRuns[0].pointsMm[0].x - exactWestX)).toBeLessThan(1);
    const sideGate = SITE_FENCE.sidePedestrianGate;
    const sideDoor = HOUSE.facades.east.openings.find(
      ({ id }) => id === sideGate.accessOpeningId,
    );
    expect(sideDoor).toBeDefined();
    expect((sideGate.startMm.y + sideGate.endMm.y) / 2).toBe(
      sideDoor!.startYmm + sideDoor!.widthMm / 2,
    );
    expect(Math.hypot(
      sideGate.endMm.x - sideGate.startMm.x,
      sideGate.endMm.y - sideGate.startMm.y,
    )).toBeCloseTo(sideGate.clearWidthMm, 1);
    expect(sideGate.status).toBe(
      "DESIGN_PROPOSAL_REQUIRES_CLIENT_CONFIRMATION",
    );
    expect(SITE_FENCE.vehicleGate.infillTreatment).toBe(
      "SLATTED_ALUMINIUM",
    );
    expect(sideGate.infillTreatment).toBe("SOLID_ALUMINIUM");
    expect(Math.hypot(
      sideGate.physicalStartMm.x - sideGate.supportPostCentersMm[0].x,
      sideGate.physicalStartMm.y - sideGate.supportPostCentersMm[0].y,
    )).toBeCloseTo(60, 8);
    expect(Math.hypot(
      sideGate.supportPostCentersMm[1].x - sideGate.physicalEndMm.x,
      sideGate.supportPostCentersMm[1].y - sideGate.physicalEndMm.y,
    )).toBeCloseTo(60, 8);
    expect(SITE_FENCE.visualProposal).toMatchObject({
      status: "DESIGN_PROPOSAL",
      style: "HYBRID_LUXURY_PRIVACY",
      frontTreatment: "SLATTED_ALUMINIUM",
      sideTreatment: "SOLID_ALUMINIUM",
      rearTreatment: "LIVING_HEDGE",
      proposedHeightMm: 1600,
      finish: "FINE_TEXTURE_POWDER_COAT_RAL_7016",
      colorHex: "#252a2c",
      slatWidthMm: 60,
      slatPitchMm: 110,
      physicalBoundaryInsetMm: 100,
      solidPanelDepthMm: 52,
      solidPanelJointMm: 22,
      rearHedgeHeightMm: 1850,
      rearHedgeDepthMm: 900,
      rearHedgeCenterlineOffsetMm: 450,
      telescopicPanelOverlapMm: 100,
      telescopicPanelPlaneOffsetMm: 45,
    });

    const subject = CADASTRAL_PARCELS.find((parcel) => parcel.isSubject)!;
    const subjectRing = subject.sjtskRingMm.map(sjtskToLocalMm);
    const pointToSegmentDistance = (
      point: { x: number; y: number },
      start: { x: number; y: number },
      end: { x: number; y: number },
    ) => {
      const dx = end.x - start.x;
      const dy = end.y - start.y;
      const lengthSquared = dx * dx + dy * dy;
      const ratio =
        lengthSquared === 0
          ? 0
          : Math.max(
              0,
              Math.min(
                1,
                ((point.x - start.x) * dx + (point.y - start.y) * dy) /
                  lengthSquared,
              ),
            );
      return Math.hypot(
        point.x - (start.x + dx * ratio),
        point.y - (start.y + dy * ratio),
      );
    };
    const distanceToParcelMm = (point: { x: number; y: number }) =>
      Math.min(
        ...subjectRing.slice(1).map((end, index) =>
          pointToSegmentDistance(point, subjectRing[index], end),
        ),
      );

    for (const run of SITE_FENCE.fixedRuns) {
      if (run.alignment === "CLIENT_FRONT_DATUM") {
        expect(run.pointsMm.every(({ y }) => y === SITE_FENCE.datumYmm)).toBe(
          true,
        );
      } else {
        for (const point of run.pointsMm) {
          expect(distanceToParcelMm(point)).toBeLessThan(1);
        }
        for (let index = 1; index < run.pointsMm.length; index += 1) {
          const start = run.pointsMm[index - 1];
          const end = run.pointsMm[index];
          expect(
            distanceToParcelMm({
              x: (start.x + end.x) / 2,
              y: (start.y + end.y) / 2,
            }),
          ).toBeLessThan(1);
        }
      }
      for (let index = 1; index < run.pointsMm.length; index += 1) {
        const start = run.pointsMm[index - 1];
        const end = run.pointsMm[index];
        if (start.y !== SITE_FENCE.datumYmm || end.y !== SITE_FENCE.datumYmm) {
          continue;
        }
        const segmentMinX = Math.min(start.x, end.x);
        const segmentMaxX = Math.max(start.x, end.x);
        const crossesVehicleGate =
          Math.max(segmentMinX, gate.startMm.x) <
          Math.min(segmentMaxX, gate.endMm.x);
        expect(crossesVehicleGate).toBe(false);
      }
    }
    expect(
      SITE_FENCE.fixedRuns.find(
        ({ id }) => id === "FENCE-FIXED-EAST-UPPER",
      )?.pointsMm.at(-1),
    ).toEqual(sideGate.startMm);
    expect(
      SITE_FENCE.fixedRuns.find(
        ({ id }) => id === "FENCE-FIXED-EAST-LOWER",
      )?.pointsMm[0],
    ).toEqual(sideGate.endMm);

    const physicalById = new Map(
      SITE_FENCE.physicalFixedRuns.map((run) => [run.id, run]),
    );
    expect(
      Object.fromEntries(
        SITE_FENCE.physicalFixedRuns.map(({ id, treatment }) => [
          id,
          treatment,
        ]),
      ),
    ).toEqual({
      "FENCE-PHYSICAL-FRONT-LEFT": "SLATTED_ALUMINIUM",
      "FENCE-PHYSICAL-FRONT-RIGHT": "SLATTED_ALUMINIUM",
      "FENCE-PHYSICAL-EAST-UPPER": "SOLID_ALUMINIUM",
      "FENCE-PHYSICAL-EAST-LOWER": "SOLID_ALUMINIUM",
      "FENCE-PHYSICAL-REAR": "LIVING_HEDGE",
      "FENCE-PHYSICAL-WEST": "SOLID_ALUMINIUM",
    });
    expect(
      SITE_FENCE.physicalFixedRuns.every(
        ({ status }) =>
          status ===
          "DESIGN_PROPOSAL_REQUIRES_SURVEY_AND_CLIENT_CONFIRMATION",
      ),
    ).toBe(true);
    const physicalFrontLeft = physicalById.get("FENCE-PHYSICAL-FRONT-LEFT")!;
    const physicalFrontRight = physicalById.get("FENCE-PHYSICAL-FRONT-RIGHT")!;
    const physicalEastUpper = physicalById.get("FENCE-PHYSICAL-EAST-UPPER")!;
    const physicalEastLower = physicalById.get("FENCE-PHYSICAL-EAST-LOWER")!;
    const physicalRear = physicalById.get("FENCE-PHYSICAL-REAR")!;
    const physicalWest = physicalById.get("FENCE-PHYSICAL-WEST")!;
    expect(physicalFrontRight.pointsMm.at(-1)).toEqual(
      physicalEastUpper.pointsMm[0],
    );
    expect(physicalEastUpper.pointsMm.at(-1)).toEqual(
      sideGate.physicalStartMm,
    );
    expect(physicalEastLower.pointsMm[0]).toEqual(sideGate.physicalEndMm);
    expect(physicalEastLower.pointsMm.at(-1)).toEqual(
      physicalRear.pointsMm[0],
    );
    expect(physicalRear.pointsMm.at(-1)).toEqual(physicalWest.pointsMm[0]);
    expect(physicalWest.pointsMm.at(-1)).toEqual(
      physicalFrontLeft.pointsMm[0],
    );
    expect(physicalFrontRight.pointsMm.at(-1)).toMatchObject({
      x: expect.closeTo(31_086.9993, 2),
      y: expect.closeTo(3_000, 6),
    });
    expect(physicalEastLower.pointsMm.at(-1)).toMatchObject({
      x: expect.closeTo(31_009.378, 2),
      y: expect.closeTo(24_392.8873, 2),
    });
    expect(physicalRear.pointsMm.at(-1)).toMatchObject({
      x: expect.closeTo(-842.0059, 2),
      y: expect.closeTo(23_104.126, 2),
    });
    expect(physicalWest.pointsMm.at(-1)).toMatchObject({
      x: expect.closeTo(-21.9168, 2),
      y: expect.closeTo(3_000, 6),
    });
    for (const run of [
      physicalEastUpper,
      physicalEastLower,
      physicalRear,
      physicalWest,
    ]) {
      for (let index = 1; index < run.pointsMm.length; index += 1) {
        const start = run.pointsMm[index - 1];
        const end = run.pointsMm[index];
        const cadastralInsetMm = distanceToParcelMm({
          x: (start.x + end.x) / 2,
          y: (start.y + end.y) / 2,
        });
        expect(
          Math.abs(
            cadastralInsetMm -
              SITE_FENCE.visualProposal.physicalBoundaryInsetMm,
          ),
        ).toBeLessThan(1);
      }
    }
    expect(
      Math.abs(
        distanceToParcelMm(sideGate.physicalStartMm) -
          SITE_FENCE.visualProposal.physicalBoundaryInsetMm,
      ),
    ).toBeLessThan(1);
    expect(
      Math.abs(
        distanceToParcelMm(sideGate.physicalEndMm) -
          SITE_FENCE.visualProposal.physicalBoundaryInsetMm,
      ),
    ).toBeLessThan(1);
    expect(
      SITE_FENCE.visualProposal.physicalBoundaryInsetMm +
        SITE_FENCE.visualProposal.rearHedgeCenterlineOffsetMm -
        SITE_FENCE.visualProposal.rearHedgeDepthMm / 2,
    ).toBeGreaterThanOrEqual(100);
  });
});

describe("data to geometry contract", () => {
  it("places the requested 5,6 × 3 m pool flush into the inner-L corner", () => {
    expect(GARDEN_POOL).toMatchObject({
      id: "POOL-COURTYARD-56X3",
      centerMm: { x: 14_940, y: 14_900 },
      waterLengthMm: 5_600,
      waterWidthMm: 3_000,
      waterAreaM2: 16.8,
      copingWidthMm: 300,
      proposedWaterDepthMm: 1_400,
      placementStatus:
        "CLIENT_REQUESTED_LAYOUT_REQUIRES_RAINWATER_COORDINATION",
      terraceConnection: {
        terraceId: "TERR-D1-GARDEN",
        copingEdgeYmm: 13_100,
        planGapMm: 0,
        contactLengthMm: 6_200,
        sharedTopElevationMm: 20,
      },
      wingDeckContact: {
        deckId: "TERR-D1-WING",
        edgeXmm: 18_040,
        planGapMm: 0,
        sharedTopElevationMm: 20,
      },
    });
    expect(GARDEN_POOL.waterFootprintMm[0]).toEqual(
      GARDEN_POOL.waterFootprintMm.at(-1),
    );
    const edgeLengthsMm = GARDEN_POOL.waterFootprintMm
      .slice(1)
      .map((end, index) => {
        const start = GARDEN_POOL.waterFootprintMm[index];
        return Math.hypot(end.x - start.x, end.y - start.y);
      })
      .sort((left, right) => left - right);
    expect(edgeLengthsMm).toEqual([3_000, 3_000, 5_600, 5_600]);
    expect(polygonAreaM2(GARDEN_POOL.waterFootprintMm)).toBe(16.8);
    expect(
      GARDEN_POOL.sourceIds.every((sourceId) => findSource(sourceId)),
    ).toBe(true);
    expect(SOURCES.clientExteriorRevision20260821.detail).toContain(
      "5,0 × 3,0 m",
    );
    expect(SOURCES.poolDesignProposal20260821.kind).toBe("DESIGN_PROPOSAL");
    expect(SOURCES.poolDesignProposal20260821.detail).toContain(
      "Pôvodná vodná plocha 4,0 × 2,5 m",
    );

    const copingXs = GARDEN_POOL.copingFootprintMm.map(({ x }) => x);
    const copingYs = GARDEN_POOL.copingFootprintMm.map(({ y }) => y);
    const poolBounds = {
      x0: Math.min(...copingXs),
      x1: Math.max(...copingXs),
      y0: Math.min(...copingYs),
      y1: Math.max(...copingYs),
    };
    const courtyardBounds = {
      x0: HOUSE.originMm.x,
      x1: HOUSE.originMm.x + HOUSE.wing.xMm,
      y0: HOUSE.originMm.y + HOUSE.lowerBar.depthMm,
      y1: HOUSE.originMm.y + HOUSE.maximumDepthMm,
    };
    expect(poolBounds.x0).toBeGreaterThan(courtyardBounds.x0);
    expect(poolBounds.x1).toBeLessThan(courtyardBounds.x1);
    expect(poolBounds.y0).toBeGreaterThan(courtyardBounds.y0);
    expect(poolBounds.y1).toBeLessThan(courtyardBounds.y1);
    expect(poolBounds.y0).toBe(
      GARDEN_POOL.terraceConnection.copingEdgeYmm,
    );
    expect(poolBounds.x1 - poolBounds.x0).toBe(
      GARDEN_POOL.terraceConnection.contactLengthMm,
    );
    const terraceContactMm = TERRACE_ZONES_D1.flatMap((zone) => zone.rectsMm)
      .filter((rect) => rect.y1 === poolBounds.y0)
      .reduce(
        (sum, rect) =>
          sum +
          Math.max(
            0,
            Math.min(poolBounds.x1, rect.x1) -
              Math.max(poolBounds.x0, rect.x0),
          ),
        0,
      );
    expect(terraceContactMm).toBe(
      GARDEN_POOL.terraceConnection.contactLengthMm,
    );

    // The coping east edge sits flush with the wing deck west edge, so the
    // pool fills the inner corner of the terrace L with no lawn strip.
    const wingDeckRect = TERRACE_ZONES_D1.find(
      (zone) => zone.id === GARDEN_POOL.wingDeckContact.deckId,
    )?.rectsMm[0];
    expect(wingDeckRect).toBeDefined();
    expect(poolBounds.x1).toBe(GARDEN_POOL.wingDeckContact.edgeXmm);
    expect(poolBounds.x1).toBe(wingDeckRect?.x0);

    for (const zone of TERRACE_ZONES_D1) {
      for (const rect of zone.rectsMm) {
        const overlaps =
          Math.max(poolBounds.x0, rect.x0) <
            Math.min(poolBounds.x1, rect.x1) &&
          Math.max(poolBounds.y0, rect.y0) <
            Math.min(poolBounds.y1, rect.y1);
        expect(overlaps).toBe(false);
      }
    }
    expect(Math.min(...Object.values(GARDEN_POOL.modelledClearancesMm))).toBe(0);
    expect(GARDEN_POOL.modelledClearancesMm.rainTankShell).toBe(1_787);
    expect(GARDEN_POOL.modelledClearancesMm.closestRainPipeShell).toBe(630);
    const reroutedRain = UTILITY_ROUTES.find(
      ({ id }) => id === "UTIL-RAIN-SOUTH",
    );
    expect(reroutedRain?.pointsMm).toEqual([
      { x: 7_600, y: 10_800 },
      { x: 7_600, y: 12_400 },
      { x: 11_000, y: 12_400 },
      { x: 11_000, y: 17_400 },
      { x: 16_900, y: 17_400 },
    ]);
    expect(reroutedRain?.sourceIds).toEqual([
      SOURCES.rainwater.id,
      SOURCES.clientExteriorRevision20260821.id,
      SOURCES.poolDesignProposal20260821.id,
    ]);
    const northRain = UTILITY_ROUTES.find(
      ({ id }) => id === "UTIL-RAIN-NORTH",
    );
    expect(northRain?.pointsMm).toEqual([
      { x: 26_300, y: 21_000 },
      { x: 22_400, y: 15_600 },
      { x: 18_800, y: 15_600 },
      { x: 18_800, y: 17_400 },
      { x: 16_900, y: 17_400 },
    ]);
    // Both preliminary legs share the bypass corridor 700 mm south of the
    // coping; minus the 70 mm pipe shell this keeps the documented ~0,63 m.
    const corridorGapMm = Math.min(
      ...northRain!.pointsMm.filter(({ y }) => y === 17_400).map(() => 17_400),
    );
    expect(corridorGapMm - GARDEN_POOL.copingFootprintMm[2].y - 70).toBe(630);
  });

  it("keeps the luxury fence raster at a fixed pitch with balanced margins", () => {
    const style = SITE_FENCE.visualProposal;
    const gateLengthMm = Math.hypot(
      SITE_FENCE.vehicleGate.leafClosureEndMm.x -
        SITE_FENCE.vehicleGate.startMm.x,
      SITE_FENCE.vehicleGate.leafClosureEndMm.y -
        SITE_FENCE.vehicleGate.startMm.y,
    );
    const panelLengthMm =
      (gateLengthMm +
        (SITE_FENCE.vehicleGate.panelCount - 1) *
          style.telescopicPanelOverlapMm) /
      SITE_FENCE.vehicleGate.panelCount;
    for (const lengthMm of [panelLengthMm]) {
      const centers = slatCenterDistancesMm(
        lengthMm,
        style.slatWidthMm,
        style.slatPitchMm,
      );
      expect(centers.length).toBeGreaterThan(1);
      for (let index = 1; index < centers.length; index += 1) {
        expect(centers[index] - centers[index - 1]).toBeCloseTo(
          style.slatPitchMm,
          10,
        );
      }
      const leftMarginMm = centers[0] - style.slatWidthMm / 2;
      const rightMarginMm =
        lengthMm - (centers.at(-1)! + style.slatWidthMm / 2);
      expect(leftMarginMm).toBeCloseTo(rightMarginMm, 10);
    }
  });

  it("cuts the street garage door and remaining front openings without overlap", () => {
    const garageDoor = HOUSE.facades.front.garageDoor;
    const openings = [
      {
        id: garageDoor.id,
        startMm: garageDoor.startXmm,
        widthMm: garageDoor.widthMm,
        heightMm: garageDoor.heightMm,
        sillMm: garageDoor.sillMm,
      },
      ...HOUSE.facades.front.openings.map((opening) => ({
        id: opening.id,
        startMm: opening.startXmm,
        widthMm: opening.widthMm,
        heightMm: opening.heightMm,
        sillMm: opening.sillMm,
      })),
    ];
    const segments = segmentFacadeMm(
      HOUSE.originMm.x,
      HOUSE.facades.east.faceXmm,
      HOUSE.eavesElevationMm,
      openings,
    );
    expect(segments).toContainEqual({
      startMm: garageDoor.startXmm,
      endMm: garageDoor.startXmm + garageDoor.widthMm,
      bottomMm: garageDoor.heightMm,
      topMm: HOUSE.eavesElevationMm,
    });
    expect(
      segments.some(
        ({ startMm, endMm, bottomMm }) =>
          startMm < garageDoor.startXmm + garageDoor.widthMm &&
          endMm > garageDoor.startXmm &&
          bottomMm === 0,
      ),
    ).toBe(false);
  });

  it("cuts the documented garden glazing out of the realistic shell", () => {
    const openings = HOUSE.facades.garden.openings.map((opening) => ({
      id: opening.id,
      startMm: opening.startXmm,
      widthMm: opening.widthMm,
      heightMm: opening.heightMm,
      sillMm: opening.sillMm,
    }));
    const segments = segmentFacadeMm(6_440, 21_040, 3_125, openings);
    expect(segments).toEqual([
      { startMm: 6_440, endMm: 9_290, bottomMm: 0, topMm: 3_125 },
      { startMm: 9_290, endMm: 10_540, bottomMm: 2_400, topMm: 3_125 },
      { startMm: 10_540, endMm: 11_840, bottomMm: 0, topMm: 3_125 },
      { startMm: 11_840, endMm: 14_340, bottomMm: 2_400, topMm: 3_125 },
      { startMm: 14_340, endMm: 15_840, bottomMm: 0, topMm: 3_125 },
      { startMm: 15_840, endMm: 17_840, bottomMm: 2_400, topMm: 3_125 },
      { startMm: 17_840, endMm: 21_040, bottomMm: 0, topMm: 3_125 },
    ]);
    const solidAreaMm2 = segments.reduce(
      (sum, segment) =>
        sum +
        (segment.endMm - segment.startMm) *
          (segment.topMm - segment.bottomMm),
      0,
    );
    expect(solidAreaMm2).toBe(31_825_000);
  });

  it("uses the rough wing opening while preserving the 2 400 mm clear frame", () => {
    const opening = HOUSE.facades.wingEnd.opening;
    const segments = segmentFacadeMm(21_040, 28_040, 3_125, [
      {
        id: opening.id,
        startMm: opening.roughOpeningStartXmm,
        widthMm: opening.roughOpeningWidthMm,
        heightMm: opening.heightMm,
        sillMm: opening.sillMm,
      },
    ]);
    expect(segments).toEqual([
      { startMm: 21_040, endMm: 21_540, bottomMm: 0, topMm: 3_125 },
      { startMm: 21_540, endMm: 24_040, bottomMm: 2_400, topMm: 3_125 },
      { startMm: 24_040, endMm: 28_040, bottomMm: 0, topMm: 3_125 },
    ]);
    expect(opening.startXmm - opening.roughOpeningStartXmm).toBe(50);
    expect(opening.widthMm).toBe(2_400);
    expect(
      segments.reduce(
        (sum, segment) =>
          sum +
          (segment.endMm - segment.startMm) *
            (segment.topMm - segment.bottomMm),
        0,
      ),
    ).toBe(15_875_000);
    expect(() =>
      segmentFacadeMm(0, 1_000, 3_000, [
        { id: "A", startMm: 100, widthMm: 600, heightMm: 2_000, sillMm: 0 },
        { id: "B", startMm: 650, widthMm: 200, heightMm: 2_000, sillMm: 0 },
      ]),
    ).toThrow(/B/);
  });

  it("changes width and volume immutably for the selected strip", () => {
    const source = FOUNDATIONS[0];
    const before = foundationVolumeM3(source);
    const changed = updateFoundationWidth(FOUNDATIONS, source.id, 900);
    const updated = changed[0];

    expect(changed).not.toBe(FOUNDATIONS);
    expect(updated).not.toBe(source);
    expect(source.widthMm).toBe(800);
    expect(updated.widthMm).toBe(900);
    expect(foundationVolumeM3(updated)).toBeCloseTo(before * (900 / 800), 10);
  });

  it.each([Number.NaN, 0, -1, 450.5])("rejects an invalid width: %s", (width) => {
    expect(() => updateFoundationWidth(FOUNDATIONS, "F-01", width)).toThrow();
  });
});


describe("documented D1 covered porches and terrace zones", () => {
  it("keeps the wing porch recessed 2 500 mm behind the gable plane", () => {
    const porch = HOUSE.porches.wingEnd;
    expect(porch.frontYmm).toBe(HOUSE.facades.wingEnd.faceYmm);
    expect(porch.frontYmm - porch.glazingFaceYmm).toBe(porch.clearDepthMm);
    expect(porch.glazing.startXmm).toBe(
      HOUSE.facades.wingEnd.opening.roughOpeningStartXmm,
    );
    expect(porch.glazing.widthMm).toBe(
      HOUSE.facades.wingEnd.opening.roughOpeningWidthMm,
    );
    expect(porch.backWall.startXmm).toBe(
      porch.glazing.startXmm + porch.glazing.widthMm,
    );
    expect(porch.cornerPillar.sizeMm).toBe(500);
    // The porch is open to the roof: the larch gable sits on the recessed
    // plane, so nothing closes the front above the opening.
    expect(porch.openToRoof).toBe(true);
    expect(porch.gablePlaneYmm).toBe(porch.glazingFaceYmm);
    expect(porch.ceilingClearanceMm).toBeGreaterThan(0);
    expect(porch.westOpening.endYmm - porch.westOpening.startYmm).toBe(2_000);
    expect(HOUSE.facades.wingWest.wallEndYmm).toBe(porch.westOpening.startYmm);
  });

  it("keeps the garden loggia recess consistent with the facade opening", () => {
    const loggia = HOUSE.porches.gardenLoggia;
    expect(loggia.faceYmm).toBe(HOUSE.facades.garden.faceYmm);
    expect(loggia.openingEndXmm - loggia.openingStartXmm).toBe(3_200);
    expect(loggia.backDoor.widthMm).toBe(1_250);
    expect(loggia.backLarch.endXmm).toBe(loggia.backDoor.startXmm);
    expect(loggia.faceYmm - loggia.backFaceYmm).toBe(2_953);
    expect(HOUSE.facades.west.loggiaOpening.startYmm).toBeGreaterThan(
      loggia.backFaceYmm,
    );
    expect(
      HOUSE.facades.west.loggiaOpening.startYmm +
        HOUSE.facades.west.loggiaOpening.widthMm,
    ).toBeLessThan(loggia.faceYmm);
  });

  it("matches the documented 84,35 m² terrace total within drawing tolerance", () => {
    const documented = TERRACE_ZONES_D1.reduce(
      (sum, zone) => sum + zone.documentedAreaM2,
      0,
    );
    expect(documented).toBeCloseTo(84.35, 10);
    for (const zone of TERRACE_ZONES_D1) {
      const derived = terraceZoneAreaM2(zone);
      expect(
        Math.abs(derived - zone.documentedAreaM2),
        zone.id,
      ).toBeLessThan(0.75);
    }
    const porchZone = TERRACE_ZONES_D1.find((zone) => zone.covered);
    expect(porchZone?.id).toBe("TERR-D1-PORCH");
  });
});
