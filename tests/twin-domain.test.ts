import { describe, expect, it } from "vitest";

import {
  BREZI_6012_26_LOCAL_POLYGON_MM,
  BREZI_6012_26_PARCEL,
  BREZI_6012_26_SJTSK_RING_MM,
  CUZK_PARCEL_6012_26_SOURCE,
  NEARBY_PARCEL_REFERENCES,
  PROVENANCE_KINDS,
  S_JTSK_LOCAL_ORIGIN_MM,
  TWIN_LAYER_IDS,
  coordinateMm,
  createFoundationStrip,
  createTwinDomainState,
  foundationVolumeCubicMetres,
  foundationVolumeMm3,
  lineLengthMm,
  localToSjtskMm,
  pointMm,
  polygonAreaMm2,
  polygonAreaSquareMetres,
  polygonBoundsMm,
  positiveMm,
  sjtskMetresToMm,
  sjtskToLocalMm,
  undoLastFoundationWidthChange,
  updateFoundationWidth,
} from "../lib/twin-domain";

const projectSource = Object.freeze({
  id: "project:D1.1.001",
  provenance: PROVENANCE_KINDS.PROJECT_DESIGN,
  title: "Pôdorys základov",
  locator:
    "arch-docs/projektova dokumentace/D_Vykresova dokumentace/D1_ASR/D1.1.001_Pudorys zakladu.pdf",
});

function foundationF12() {
  return createFoundationStrip({
    id: "F-12",
    name: "Základový pás F-12",
    path: [
      { xMm: 0, yMm: 0 },
      { xMm: 8_420, yMm: 0 },
    ],
    widthMm: 400,
    heightMm: 600,
    baseElevationMm: -1_150,
    concreteType: "C16/20",
    status: "DESIGNED",
    sourceRefs: [projectSource],
  });
}

describe("canonical model constants", () => {
  it("defines the required provenance and layer vocabulary", () => {
    expect(Object.values(PROVENANCE_KINDS)).toEqual([
      "CADASTRE_CURRENT",
      "PROJECT_DESIGN",
      "PROVIDER_MAP",
      "EMAIL_AS_BUILT_REFERENCE",
      "INFERRED",
    ]);
    expect(TWIN_LAYER_IDS).toEqual([
      "parcel",
      "context",
      "road",
      "building",
      "foundations",
      "utilities",
    ]);
  });

  it("stores the exact current ČÚZK identity, ring and registered area", () => {
    expect(BREZI_6012_26_PARCEL.parcelNumber).toBe("6012/26");
    expect(BREZI_6012_26_PARCEL.nationalCadastralReference).toBe(
      "613908-6012/26",
    );
    expect(BREZI_6012_26_PARCEL.registeredAreaSquareMetres).toBe(753);
    expect(CUZK_PARCEL_6012_26_SOURCE.featureId).toBe("CP.94487880010");
    expect(BREZI_6012_26_SJTSK_RING_MM).toHaveLength(10);
    expect(BREZI_6012_26_SJTSK_RING_MM[0]).toEqual(
      pointMm(-606_686_450, -1_202_035_560),
    );
    expect(BREZI_6012_26_SJTSK_RING_MM.at(-1)).toEqual(
      BREZI_6012_26_SJTSK_RING_MM[0],
    );
    expect(NEARBY_PARCEL_REFERENCES.map((item) => item.parcelNumber)).toEqual([
      "6012/24",
      "6012/25",
      "6012/27",
      "6013",
      "6014",
      "6015",
    ]);
  });
});

describe("pure geometry", () => {
  it("computes the target parcel area without catastrophic S-JTSK cancellation", () => {
    expect(polygonAreaMm2(BREZI_6012_26_PARCEL.geometry)).toBe(752_520_950);
    expect(polygonAreaSquareMetres(BREZI_6012_26_PARCEL.geometry)).toBeCloseTo(
      752.52095,
      8,
    );
    expect(Math.round(polygonAreaSquareMetres(BREZI_6012_26_PARCEL.geometry))).toBe(
      BREZI_6012_26_PARCEL.registeredAreaSquareMetres,
    );
  });

  it("computes exact parcel bounds in integer millimetres", () => {
    expect(polygonBoundsMm(BREZI_6012_26_PARCEL.geometry)).toEqual({
      minXmm: -606_723_140,
      minYmm: -1_202_056_660,
      maxXmm: -606_685_750,
      maxYmm: -1_202_017_130,
      widthMm: 37_390,
      heightMm: 39_530,
    });
  });

  it("converts S-JTSK points to a stable local frame and back", () => {
    expect(S_JTSK_LOCAL_ORIGIN_MM).toEqual(
      pointMm(-606_703_380, -1_202_038_880),
    );
    const source = BREZI_6012_26_SJTSK_RING_MM[0];
    const local = sjtskToLocalMm(source);
    expect(local).toEqual(pointMm(16_930, 3_320));
    expect(localToSjtskMm(local)).toEqual(source);
    expect(BREZI_6012_26_LOCAL_POLYGON_MM.crs).toBe("LOCAL_MM");
    expect(BREZI_6012_26_LOCAL_POLYGON_MM.outerRing[0]).toEqual(local);
  });

  it("computes polyline length and foundation volume", () => {
    const line = [pointMm(0, 0), pointMm(3_000, 4_000)];
    expect(lineLengthMm(line)).toBe(5_000);

    const foundation = foundationF12();
    expect(lineLengthMm(foundation.path)).toBe(8_420);
    expect(foundationVolumeMm3(foundation)).toBe(2_020_800_000);
    expect(foundationVolumeCubicMetres(foundation)).toBeCloseTo(2.0208, 10);
  });
});

describe("immutable foundation history", () => {
  it("updates width immutably and keeps a source-backed history entry", () => {
    const initialFoundation = foundationF12();
    const initial = createTwinDomainState([initialFoundation]);
    const changed = updateFoundationWidth(initial, "F-12", 450, {
      id: "change:F-12:width:1",
      changedAt: "2026-08-18T10:00:00.000Z",
      reason: "Upresnenie pred betonážou",
      sourceRef: projectSource,
    });

    expect(changed).not.toBe(initial);
    expect(changed.foundations).not.toBe(initial.foundations);
    expect(changed.foundations[0]).not.toBe(initial.foundations[0]);
    expect(initial.foundations[0].widthMm).toBe(400);
    expect(changed.foundations[0].widthMm).toBe(450);
    expect(changed.revision).toBe(1);
    expect(changed.history).toEqual([
      expect.objectContaining({
        foundationId: "F-12",
        beforeWidthMm: 400,
        afterWidthMm: 450,
        sourceRef: projectSource,
        status: "APPLIED",
      }),
    ]);
  });

  it("undoes without mutating the changed state or erasing audit history", () => {
    const initial = createTwinDomainState([foundationF12()]);
    const changed = updateFoundationWidth(initial, "F-12", 450, {
      id: "change:F-12:width:1",
      changedAt: "2026-08-18T10:00:00.000Z",
      reason: "Upresnenie pred betonážou",
      sourceRef: projectSource,
    });
    const undone = undoLastFoundationWidthChange(changed);

    expect(changed.foundations[0].widthMm).toBe(450);
    expect(undone.foundations[0].widthMm).toBe(400);
    expect(undone.revision).toBe(2);
    expect(undone.history[0]).toEqual(
      expect.objectContaining({ status: "UNDONE", undoneRevision: 2 }),
    );
    expect(changed.history[0].status).toBe("APPLIED");
  });

  it("does not add a history entry for an unchanged value", () => {
    const initial = createTwinDomainState([foundationF12()]);
    const unchanged = updateFoundationWidth(initial, "F-12", 400, {
      id: "change:F-12:width:no-op",
      changedAt: "2026-08-18T10:00:00.000Z",
      reason: "Kontrola bez zmeny",
      sourceRef: projectSource,
    });
    expect(unchanged).toBe(initial);
  });
});

describe("validation", () => {
  it("rejects NaN, non-integer and non-positive dimensions", () => {
    expect(() => coordinateMm(Number.NaN)).toThrow(/finite integer/i);
    expect(() => coordinateMm(1.25)).toThrow(/finite integer/i);
    expect(() => positiveMm(0)).toThrow(/positive/i);
    expect(() => positiveMm(-1)).toThrow(/positive/i);
    expect(() => sjtskMetresToMm(-606_703.380_1)).toThrow(/integer millimetres/i);
  });

  it.each([
    [Number.NaN, 600],
    [400.5, 600],
    [0, 600],
    [-400, 600],
    [400, Number.NaN],
    [400, 0],
  ])("rejects invalid foundation dimensions width=%s height=%s", (width, height) => {
    expect(() =>
      createFoundationStrip({
        id: "invalid",
        name: "Invalid foundation",
        path: [
          { xMm: 0, yMm: 0 },
          { xMm: 1_000, yMm: 0 },
        ],
        widthMm: width,
        heightMm: height,
        baseElevationMm: -1_000,
        concreteType: "C16/20",
        status: "DESIGNED",
        sourceRefs: [projectSource],
      }),
    ).toThrow();
  });

  it("rejects degenerate lines and polygons", () => {
    expect(() => lineLengthMm([pointMm(0, 0), pointMm(0, 0)])).toThrow(
      /positive length/i,
    );
    expect(() =>
      polygonAreaMm2({
        crs: "LOCAL_MM",
        outerRing: [pointMm(0, 0), pointMm(1, 1), pointMm(2, 2)],
      }),
    ).toThrow(/positive area/i);
  });
});
