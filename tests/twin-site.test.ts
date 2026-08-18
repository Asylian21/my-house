import { describe, expect, it } from "vitest";

import {
  CADASTRAL_PARCELS,
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
      garageSide: "LOCAL_X_MIN",
      wingSide: "LOCAL_X_MAX",
    });
    expect(HOUSE.roof.mainPlanLengthMm).toBe(HOUSE.lowerBar.widthMm);
    expect(HOUSE.roof.wingPlanLengthMm).toBe(HOUSE.wing.depthMm);
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
    expect(GARDEN_CAMERA_ALPHA).toBeCloseTo(-Math.PI * 0.44, 12);
    expect(Math.cos(GARDEN_CAMERA_ALPHA)).toBeGreaterThan(0);
    expect(Math.sin(GARDEN_CAMERA_ALPHA)).toBeLessThan(0);
    expect(GARDEN_CAMERA_BETA).toBeCloseTo(1.43, 12);
  });

  it("keeps the approved Realita camera deterministic on desktop and mobile", () => {
    expect(gardenCameraForWidth(1600)).toEqual({
      alpha: GARDEN_CAMERA_ALPHA,
      beta: GARDEN_CAMERA_BETA,
      radius: 28,
      fov: 0.58,
      target: [2.5, 1.4, -2],
    });
    expect(gardenCameraForWidth(600)).toEqual(gardenCameraForWidth(1600));
    expect(gardenCameraForWidth(390)).toEqual({
      alpha: GARDEN_CAMERA_ALPHA,
      beta: 1.4,
      radius: 37,
      fov: 0.86,
      target: [4.8, 1.5, -4],
    });
    expect(gardenCameraForWidth(599)).toEqual(gardenCameraForWidth(390));
    expect(gardenCameraForWidth(1600).radius).toBeLessThan(
      gardenCameraForWidth(390).radius,
    );
  });

  it("keeps the hero facade and PV layout source-driven", () => {
    expect(HOUSE.facades.garden.faceYmm).toBe(11_200);
    expect(HOUSE.facades.garden.openings).toEqual([
      { id: "GARDEN-01", startXmm: 7_440, widthMm: 3_200, heightMm: 2_400, sillMm: 0 },
      { id: "GARDEN-02", startXmm: 11_840, widthMm: 2_500, heightMm: 2_400, sillMm: 0 },
      { id: "GARDEN-03", startXmm: 15_840, widthMm: 2_000, heightMm: 2_400, sillMm: 0 },
    ]);
    expect(HOUSE.facades.wingEnd).toMatchObject({
      faceYmm: 22_035,
      startXmm: 21_040,
      widthMm: 7_000,
      opening: { widthMm: 2_400, heightMm: 2_400, sillMm: 0 },
    });
    expect(HOUSE.photovoltaics).toMatchObject({
      moduleCount: 6,
      wattsPerModule: 405,
      roofFace: "LOCAL_Y_MIN",
    });
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

  it("does not silently overlap the active D1 garage with stale C3 coordination", () => {
    expect(Math.max(...SITE_SURFACES.driveway.polygonMm.map(({ x }) => x))).toBe(
      HOUSE.originMm.x,
    );
    expect(SITE_SURFACES.driveway.placementStatus).toBe(
      "INFERRED_D1_CONNECTION",
    );
    const electricity = UTILITY_ROUTES.find(
      (route) => route.id === "UTIL-ELECTRICITY",
    );
    expect(electricity?.revisionStatus).toBe("REVISION_CONFLICT");
    expect(DEFAULT_LAYER_VISIBILITY.electricity).toBe(false);
  });
});

describe("data to geometry contract", () => {
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
      { startMm: 6_440, endMm: 7_440, bottomMm: 0, topMm: 3_125 },
      { startMm: 7_440, endMm: 10_640, bottomMm: 2_400, topMm: 3_125 },
      { startMm: 10_640, endMm: 11_840, bottomMm: 0, topMm: 3_125 },
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
    expect(solidAreaMm2).toBe(27_145_000);
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
