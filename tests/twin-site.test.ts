import { describe, expect, it } from "vitest";

import {
  CADASTRAL_PARCELS,
  TERRACE_ZONES_D1,
  terraceZoneAreaM2,
  DEFAULT_LAYER_VISIBILITY,
  FOUNDATIONS,
  HOUSE,
  ROAD_CONTEXT,
  SITE_SURFACES,
  SOURCES,
  UTILITY_ROUTES,
  foundationVolumeM3,
  sjtskToLocalMm,
  updateFoundationWidth,
} from "../lib/twin-site";
import {
  GARDEN_CAMERA_ALPHA,
  GARDEN_CAMERA_BETA,
  TOP_CAMERA_ALPHA,
  gardenCameraForWidth,
  sceneDeltaForPlanSegment,
  sceneXM,
  sceneYawForPlanSegment,
  sceneZM,
} from "../lib/twin-render-frame";
import { segmentFacadeMm } from "../lib/twin-facade";
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
    expect(SOURCES.cadastre.href).toContain("inspire-cpx-wfs");
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
    expect(ROAD_CONTEXT.legalBoundaryStatus).toBe("CURRENT_REGISTER");
    expect(ROAD_CONTEXT.surfaceEnvelopeStatus).toBe("DESIGNED_APPROXIMATE");
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
    // The hero camera sits north-west of the house and looks back at the
    // covered gable porch, matching the approved reference framing.
    expect(GARDEN_CAMERA_ALPHA).toBeCloseTo(-2.03, 12);
    expect(Math.cos(GARDEN_CAMERA_ALPHA)).toBeLessThan(0);
    expect(Math.sin(GARDEN_CAMERA_ALPHA)).toBeLessThan(0);
    expect(GARDEN_CAMERA_BETA).toBeCloseTo(1.3, 12);
  });

  it("keeps the approved Realita camera deterministic on desktop and mobile", () => {
    expect(gardenCameraForWidth(1600)).toEqual({
      alpha: GARDEN_CAMERA_ALPHA,
      beta: GARDEN_CAMERA_BETA,
      radius: 30,
      fov: 0.55,
      target: [3.2, 1.6, -3],
    });
    expect(gardenCameraForWidth(600)).toEqual(gardenCameraForWidth(1600));
    expect(gardenCameraForWidth(390)).toEqual({
      alpha: GARDEN_CAMERA_ALPHA,
      beta: 1.22,
      radius: 38,
      fov: 0.8,
      target: [2.8, 1.4, -3.2],
    });
    expect(gardenCameraForWidth(599)).toEqual(gardenCameraForWidth(390));
    expect(gardenCameraForWidth(1600).radius).toBeLessThan(
      gardenCameraForWidth(390).radius,
    );
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
      placement: "ABOVE_KITCHEN",
      firstModuleCenterMm: { x: 22_000, y: 12_100 },
      rowStepMm: { x: 1_550, y: 0 },
      columnStepMm: { x: 0, y: 1_100 },
    });
    expect(HOUSE.photovoltaics.rows * HOUSE.photovoltaics.columns).toBe(
      HOUSE.photovoltaics.moduleCount,
    );
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
      { x: 22_000, y: 12_100 },
      { x: 23_550, y: 12_100 },
      { x: 22_000, y: 13_200 },
      { x: 23_550, y: 13_200 },
      { x: 22_000, y: 14_300 },
      { x: 23_550, y: 14_300 },
    ]);
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
        Math.cos(mount.rotationZRad);
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
    }
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
        id: "CHIMNEY-ROOM-109",
        centerMm: { x: 17_640, y: 7_250 },
        zone: "ROOM_1_09_ROOF_ZONE",
        sourceId: SOURCES.roofPlan.id,
      },
    ]);
    expect(HOUSE.removedChimneys).toEqual([
      {
        id: "CHIMNEY-LIVING-103",
        centerMm: { x: 24_190, y: 11_700 },
        zone: "MAIN_LIVING_AND_KITCHEN_1_03",
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
        xMm: 26_300,
        faceYmm: 22_035,
        sourceRouteId: "UTIL-RAIN-NORTH",
        certainty: "VISUAL_INFERENCE",
      },
    ]);
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
      "CLIENT_REVISION_DIRECT_STREET_ACCESS",
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
});

describe("data to geometry contract", () => {
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
