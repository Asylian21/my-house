import { describe, expect, it } from "vitest";

import {
  GARAGE_SEQUENCE,
  GARAGE_VEHICLE,
  garageActionForState,
  garageActionLabel,
  garageAnimationFrame,
  garageCinematicRequiresSafePosition,
  garageDoorPanelPose,
  garageParkingStatus,
  garageVehiclePlanCorners,
  garageVehicleSurfaceElevationM,
  type GarageVehicleAction,
} from "../lib/twin-garage";
import {
  GARAGE_SUPERB_AXLES_M,
  GARAGE_SUPERB_BODY_STATIONS,
  GARAGE_SUPERB_DLO,
  GARAGE_SUPERB_HALF_LENGTH_M,
  GARAGE_SUPERB_HALF_TRACKS_M,
  GARAGE_SUPERB_LOFT_RING_POINT_COUNT,
  GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM,
  GARAGE_SUPERB_VISUAL_LENGTH_SCALE,
  GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M,
  GARAGE_SUPERB_WHEEL_M,
  garageSuperbBodySideZ,
  garageSuperbDloBottomY,
  garageSuperbDloTopY,
  garageSuperbGlassZ,
  garageSuperbSectionAt,
  vehicleLoftBounds,
  vehicleLoftGeometry,
} from "../lib/twin-superb-combi";
import { INTERIOR_ROOMS } from "../lib/twin-interior";
import { GARAGE_DEPTH_REVISION, HOUSE, SITE_SURFACES } from "../lib/twin-site";

const maximumStationGapM = (stations: readonly { readonly x: number }[]) =>
  Math.max(
    ...stations
      .slice(1)
      .map((station, index) => station.x - stations[index].x),
  );

describe("garage vehicle contract", () => {
  it("uses the direct street garage door rather than the garden gate", () => {
    expect(GARAGE_VEHICLE.garageDoorId).toBe("GARAGE-DOOR");
    expect(GARAGE_VEHICLE.garageDoorId).toBe(
      HOUSE.facades.front.garageDoor.id,
    );
    expect(SITE_SURFACES.driveway.accessOpeningId).toBe(
      GARAGE_VEHICLE.garageDoorId,
    );
  });

  it("keeps the visual vehicle wholly behind the closed leaf and before the rear wall", () => {
    const corners = garageVehiclePlanCorners(
      garageAnimationFrame("park", GARAGE_SEQUENCE.park.totalMs).vehiclePose,
    );
    const xs = corners.map(({ x }) => x);
    const ys = corners.map(({ y }) => y);
    const closedLeafInnerYmm = GARAGE_VEHICLE.door.faceYmm + 38;

    expect(Math.min(...ys)).toBeGreaterThan(closedLeafInnerYmm + 40);
    expect(Math.max(...ys)).toBeLessThan(
      GARAGE_DEPTH_REVISION.revisedGarageRearInnerFaceYmm - 40,
    );
    expect(Math.min(...xs)).toBeGreaterThan(6_944);
    expect(Math.max(...xs)).toBeLessThan(10_842);

    const loggia = HOUSE.porches.gardenLoggia;
    const loggiaDoorLeafWidthMm = Math.round(loggia.backDoor.widthMm * 0.72);
    const openLoggiaDoorTipYmm =
      loggia.backFaceYmm - 150 - loggiaDoorLeafWidthMm;
    expect(openLoggiaDoorTipYmm - Math.max(...ys)).toBeGreaterThanOrEqual(140);
    expect(Math.min(...ys) - closedLeafInnerYmm).toBeGreaterThanOrEqual(140);
    expect(GARAGE_VEHICLE.route.parkedMm.y).toBe(5_600);
    expect(GARAGE_VEHICLE.garageRevision).toEqual({
      sourceId: GARAGE_DEPTH_REVISION.sourceId,
      extensionMm: 1_000,
      rearInnerFaceYmm: GARAGE_DEPTH_REVISION.revisedGarageRearInnerFaceYmm,
    });
  });

  it("keeps the arrival queue centered in the documented driveway", () => {
    const queue = GARAGE_VEHICLE.route.queueMm;
    expect(queue.x).toBe(
      HOUSE.facades.front.garageDoor.startXmm +
        HOUSE.facades.front.garageDoor.widthMm / 2,
    );
    expect(queue.x).toBeGreaterThan(GARAGE_VEHICLE.driveway.xMinMm);
    expect(queue.x).toBeLessThan(GARAGE_VEHICLE.driveway.xMaxMm);
    expect(queue.y).toBeGreaterThan(
      GARAGE_VEHICLE.driveway.asphaltEdgeYmm,
    );
    expect(queue.y).toBeLessThan(GARAGE_VEHICLE.driveway.houseFaceYmm);
  });

  it("follows the road, graded driveway and level garage floor", () => {
    expect(
      garageVehicleSurfaceElevationM(GARAGE_VEHICLE.route.streetStartMm),
    ).toBeCloseTo(-0.11, 6);
    expect(
      garageVehicleSurfaceElevationM(GARAGE_VEHICLE.route.drivewayEntryMm),
    ).toBeCloseTo(-0.11, 6);
    expect(garageVehicleSurfaceElevationM({ x: 8_590, y: 0 })).toBeCloseTo(
      -0.03,
      6,
    );
    expect(garageVehicleSurfaceElevationM({ x: 8_590, y: 3_000 })).toBeCloseTo(
      -0.015,
      6,
    );
    expect(
      garageVehicleSurfaceElevationM(GARAGE_VEHICLE.route.parkedMm),
    ).toBe(0);
  });

  it("is fully aligned inside the driveway from the asphalt edge onward", () => {
    const timing = GARAGE_SEQUENCE.park;
    for (let elapsed = 0; elapsed <= timing.arrivalEndMs; elapsed += 10) {
      const pose = garageAnimationFrame("park", elapsed).vehiclePose;
      if (pose.centerMm.y < GARAGE_VEHICLE.driveway.asphaltEdgeYmm) continue;
      for (const corner of garageVehiclePlanCorners(pose)) {
        expect(corner.x).toBeGreaterThanOrEqual(
          GARAGE_VEHICLE.driveway.xMinMm,
        );
        expect(corner.x).toBeLessThanOrEqual(
          GARAGE_VEHICLE.driveway.xMaxMm,
        );
      }
    }
  });

  it("relocates only walkers in the swept lane or door safety strip", () => {
    const safeGaragePoint = INTERIOR_ROOMS.find(
      ({ id }) => id === GARAGE_VEHICLE.roomId,
    )!.standingPointMm;
    expect(garageCinematicRequiresSafePosition(safeGaragePoint)).toBe(false);
    expect(
      garageCinematicRequiresSafePosition(GARAGE_VEHICLE.route.parkedMm),
    ).toBe(true);
    expect(
      garageCinematicRequiresSafePosition({
        x: HOUSE.facades.front.garageDoor.startXmm + 120,
        y: HOUSE.facades.front.faceYmm,
      }),
    ).toBe(true);
  });
});

describe("modern Superb visual geometry", () => {
  it("builds a finite, capped and index-safe smooth body loft", () => {
    const geometry = vehicleLoftGeometry(GARAGE_SUPERB_BODY_STATIONS);
    const vertexCount =
      GARAGE_SUPERB_BODY_STATIONS.length * GARAGE_SUPERB_LOFT_RING_POINT_COUNT +
      2 * (GARAGE_SUPERB_LOFT_RING_POINT_COUNT + 1);
    expect(geometry.positions.length).toBe(vertexCount * 3);
    expect(geometry.uvs.length).toBe(vertexCount * 2);
    expect(geometry.positions.every(Number.isFinite)).toBe(true);
    expect(geometry.uvs.every(Number.isFinite)).toBe(true);
    expect(geometry.indices.length % 3).toBe(0);
    expect(Math.min(...geometry.indices)).toBe(0);
    expect(Math.max(...geometry.indices)).toBeLessThan(
      geometry.positions.length / 3,
    );
  });

  it("renders the complete production-size Superb Combi in the revised garage", () => {
    const body = vehicleLoftBounds(
      vehicleLoftGeometry(GARAGE_SUPERB_BODY_STATIONS),
    );
    expect(body.maximum[2] - body.minimum[2]).toBeCloseTo(1.849, 6);
    expect(body.maximum[0] - body.minimum[0]).toBeCloseTo(4.902, 6);
    expect(Math.max(Math.abs(body.minimum[0]), body.maximum[0])).toBeLessThanOrEqual(
      GARAGE_VEHICLE.dimensionsMm.length / 2_000,
    );
    expect(Math.max(Math.abs(body.minimum[2]), body.maximum[2])).toBeLessThanOrEqual(
      GARAGE_VEHICLE.dimensionsMm.width / 2_000,
    );
    expect(body.maximum[1] + GARAGE_VEHICLE.wheelGroundOffsetM).toBeCloseTo(
      GARAGE_VEHICLE.dimensionsMm.height / 1_000,
      6,
    );
    expect(GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM).toMatchObject({
      length: 4_902,
      bodyWidth: 1_849,
      mirrorWidth: 2_090,
      height: 1_482,
      wheelbase: 2_841,
      frontOverhang: 950,
      rearOverhang: 1_111,
      frontTrack: 1_580,
      rearTrack: 1_566,
      groundClearance: 139,
      tireWidth: 235,
      wheelOuterDiameter: 671,
      rimDiameter: 482.6,
    });
    expect(GARAGE_VEHICLE.dimensionsMm.width).toBe(
      GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.mirrorWidth,
    );
    expect(GARAGE_VEHICLE.dimensionsMm.height).toBe(
      GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.height,
    );
    expect(GARAGE_VEHICLE.dimensionsMm.length).toBe(
      GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.length,
    );
    expect(GARAGE_SUPERB_VISUAL_LENGTH_SCALE).toBe(1);
    expect(GARAGE_SUPERB_AXLES_M.frontX - GARAGE_SUPERB_AXLES_M.rearX).toBeCloseTo(
      GARAGE_VEHICLE.dimensionsMm.wheelbase / 1_000,
      3,
    );
    expect(GARAGE_SUPERB_HALF_LENGTH_M - GARAGE_SUPERB_AXLES_M.frontX).toBeCloseTo(
      GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.frontOverhang / 1_000,
      9,
    );
    expect(GARAGE_SUPERB_AXLES_M.rearX + GARAGE_SUPERB_HALF_LENGTH_M).toBeCloseTo(
      GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.rearOverhang / 1_000,
      9,
    );
  });

  it("uses production track and 19-inch wheel contracts", () => {
    expect(GARAGE_SUPERB_HALF_TRACKS_M.front * 2).toBeCloseTo(1.58, 9);
    expect(GARAGE_SUPERB_HALF_TRACKS_M.rear * 2).toBeCloseTo(1.566, 9);
    expect(GARAGE_SUPERB_WHEEL_M).toMatchObject({
      outerDiameter: 0.671,
      tireWidth: 0.235,
    });
    expect(GARAGE_SUPERB_WHEEL_M.rimDiameter).toBeCloseTo(0.4826, 9);
  });

  it("samples a smooth low modern-estate silhouette instead of a faceted box", () => {
    expect(GARAGE_SUPERB_BODY_STATIONS.length).toBeGreaterThanOrEqual(30);
    expect(GARAGE_SUPERB_LOFT_RING_POINT_COUNT).toBeGreaterThanOrEqual(20);
    expect(GARAGE_SUPERB_LOFT_RING_POINT_COUNT % 2).toBe(0);
    expect(maximumStationGapM(GARAGE_SUPERB_BODY_STATIONS)).toBeLessThanOrEqual(
      0.3,
    );

    // Long, nearly level Combi roof plateau between the pillars.
    const roofPeak = Math.max(
      ...GARAGE_SUPERB_BODY_STATIONS.map(({ roofY }) => roofY),
    );
    const roofPlateau = GARAGE_SUPERB_BODY_STATIONS.filter(
      ({ roofY }) => roofY >= roofPeak - 0.03,
    );
    expect(roofPeak).toBeCloseTo(1.467, 6);
    expect(roofPlateau.at(-1)!.x - roofPlateau[0].x).toBeGreaterThanOrEqual(
      1.5,
    );

    // Low bonnet falling toward the grille, well below the belt-and-glass.
    const bonnet = garageSuperbSectionAt(1.5);
    expect(bonnet.roofY).toBeLessThanOrEqual(0.95);
    expect(bonnet.roofY - bonnet.beltY).toBeLessThanOrEqual(0.08);

    // Fast windscreen: the crown drops from roof to bonnet over the cowl.
    expect(garageSuperbSectionAt(0.02).roofY).toBeGreaterThan(1.4);
    expect(garageSuperbSectionAt(0.78).roofY).toBeLessThan(1.0);

    // Raked tailgate with an integrated spoiler lip well above the belt.
    const tail = garageSuperbSectionAt(-2.451);
    expect(tail.roofY).toBeGreaterThanOrEqual(1.25);
    expect(tail.roofY).toBeLessThanOrEqual(1.35);
    expect(garageSuperbSectionAt(-1.9).roofY).toBeGreaterThan(1.4);
  });

  it("keeps the photographed day-light-opening proportions", () => {
    const glassLength =
      GARAGE_SUPERB_DLO.frontTipX - GARAGE_SUPERB_DLO.rearTipX;
    const lengthRatio =
      glassLength / (GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.length / 1_000);
    expect(lengthRatio).toBeGreaterThanOrEqual(0.62);
    expect(lengthRatio).toBeLessThanOrEqual(0.66);

    const samples = Array.from({ length: 25 }, (_, index) => {
      const x =
        GARAGE_SUPERB_DLO.rearTipX +
        ((GARAGE_SUPERB_DLO.frontTipX - GARAGE_SUPERB_DLO.rearTipX) * index) /
          24;
      return {
        x,
        bottom: garageSuperbDloBottomY(x),
        top: garageSuperbDloTopY(x),
      };
    });
    const glassHeight = Math.max(
      ...samples.map(({ top, bottom }) => top - bottom),
    );
    expect(glassHeight).toBeGreaterThanOrEqual(0.45);
    expect(glassHeight).toBeLessThanOrEqual(0.56);
    for (const sample of samples.slice(1, -1)) {
      expect(sample.top).toBeGreaterThan(sample.bottom);
      const glassZ = garageSuperbGlassZ(sample.x, sample.top);
      expect(glassZ).toBeGreaterThan(0.5);
      expect(glassZ).toBeLessThan(0.95);
    }
    // The tips close almost to the belt line at both pillar feet.
    expect(
      garageSuperbDloTopY(GARAGE_SUPERB_DLO.frontTipX) -
        garageSuperbDloBottomY(GARAGE_SUPERB_DLO.frontTipX),
    ).toBeLessThanOrEqual(0.02);
    expect(
      garageSuperbDloTopY(GARAGE_SUPERB_DLO.rearTipX) -
        garageSuperbDloBottomY(GARAGE_SUPERB_DLO.rearTipX),
    ).toBeLessThanOrEqual(0.02);
  });

  it("cuts real circular wheel arches into the single body shell", () => {
    expect(
      GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M -
        GARAGE_SUPERB_WHEEL_M.outerDiameter / 2,
    ).toBeCloseTo(0.0345, 6);
    for (const axleX of [
      GARAGE_SUPERB_AXLES_M.rearX,
      GARAGE_SUPERB_AXLES_M.frontX,
    ]) {
      // The arch apex clears the tyre by the full trim margin…
      expect(garageSuperbSectionAt(axleX).baseY).toBeCloseTo(
        GARAGE_SUPERB_WHEEL_M.centerY + GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M,
        6,
      );
      // …and the rocker returns to its low line just outside the opening.
      expect(
        garageSuperbSectionAt(axleX + GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M + 0.05)
          .baseY,
      ).toBeLessThan(0.2);
      expect(
        garageSuperbSectionAt(axleX - GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M - 0.05)
          .baseY,
      ).toBeLessThan(0.2);
    }
    // Rocker sits low between the arches; body side reaches full width there.
    expect(garageSuperbSectionAt(0).baseY).toBeLessThan(0.2);
    expect(garageSuperbBodySideZ(0, 0.6)).toBeCloseTo(0.9245, 3);
  });

  it("orients both duplicated loft caps toward the exterior", () => {
    const stations = GARAGE_SUPERB_BODY_STATIONS;
    const geometry = vehicleLoftGeometry(stations);
    const sideIndexCount =
      (stations.length - 1) * GARAGE_SUPERB_LOFT_RING_POINT_COUNT * 6;
    const normalX = (indexOffset: number) => {
      const [a, b, c] = geometry.indices.slice(indexOffset, indexOffset + 3);
      const point = (index: number) =>
        geometry.positions.slice(index * 3, index * 3 + 3);
      const [, ay, az] = point(a);
      const [, by, bz] = point(b);
      const [, cy, cz] = point(c);
      return (by - ay) * (cz - az) - (bz - az) * (cy - ay);
    };
    // Babylon is left-handed: ComputeNormals yields the OPPOSITE sign of this
    // right-handed cross product. Rear cap must face -X, nose cap +X.
    expect(normalX(sideIndexCount)).toBeGreaterThan(0);
    expect(
      normalX(
        sideIndexCount + GARAGE_SUPERB_LOFT_RING_POINT_COUNT * 3,
      ),
    ).toBeLessThan(0);
  });

  it("keeps every loft cross-section exactly symmetric around vehicle Z", () => {
    const stations = GARAGE_SUPERB_BODY_STATIONS;
    const { positions } = vehicleLoftGeometry(stations);
    for (let station = 0; station < stations.length; station += 1) {
      const zValues = Array.from(
        { length: GARAGE_SUPERB_LOFT_RING_POINT_COUNT },
        (_, ring) =>
          positions[
            (station * GARAGE_SUPERB_LOFT_RING_POINT_COUNT + ring) * 3 + 2
          ].toFixed(6),
      );
      for (const value of zValues) {
        expect(zValues).toContain((-Number(value)).toFixed(6));
      }
    }
  });
});

describe("garage parking state machine", () => {
  it("runs arrival, opening, parking, closing and ends parked", () => {
    const timing = GARAGE_SEQUENCE.park;
    expect(garageAnimationFrame("park", 0).state).toBe("arriving");
    expect(
      garageAnimationFrame("park", timing.arrivalEndMs).state,
    ).toBe("opening-to-park");
    expect(
      garageAnimationFrame("park", timing.openingEndMs).state,
    ).toBe("parking");
    expect(
      garageAnimationFrame("park", timing.parkingEndMs).state,
    ).toBe("closing-after-park");

    const complete = garageAnimationFrame("park", timing.totalMs);
    expect(complete).toMatchObject({
      state: "parked",
      doorProgress: 0,
      vehicleVisible: true,
      complete: true,
    });
    expect(complete.vehiclePose.centerMm).toEqual(
      GARAGE_VEHICLE.route.parkedMm,
    );
  });

  it("opens, reverses to the street, closes and drives away", () => {
    const timing = GARAGE_SEQUENCE.unpark;
    expect(garageAnimationFrame("unpark", 0).state).toBe(
      "opening-to-leave",
    );
    expect(
      garageAnimationFrame("unpark", timing.openingEndMs).state,
    ).toBe("unparking");
    expect(
      garageAnimationFrame("unpark", timing.streetReverseEndMs).state,
    ).toBe("closing-after-leave");
    expect(
      garageAnimationFrame("unpark", timing.doorClosedMs).state,
    ).toBe("departing");

    const complete = garageAnimationFrame("unpark", timing.totalMs);
    expect(complete).toMatchObject({
      state: "away",
      doorProgress: 0,
      vehicleVisible: false,
      complete: true,
    });
  });

  it("never crosses the garage-door plane unless the leaf is fully open", () => {
    const doorY = HOUSE.facades.front.faceYmm;
    for (const action of ["park", "unpark"] as const) {
      const total =
        action === "park"
          ? GARAGE_SEQUENCE.park.totalMs
          : GARAGE_SEQUENCE.unpark.totalMs;
      for (let elapsed = 0; elapsed <= total; elapsed += 25) {
        const frame = garageAnimationFrame(action, elapsed);
        if (!frame.vehicleVisible || frame.vehiclePose.motion === "still") {
          continue;
        }
        const ys = garageVehiclePlanCorners(frame.vehiclePose).map(
          ({ y }) => y,
        );
        const minY = Math.min(...ys);
        const maxY = Math.max(...ys);
        if (minY < doorY && maxY > doorY) {
          expect(frame.doorProgress).toBe(1);
        }
      }
    }
  });

  it("has deterministic terminal states at common refresh rates", () => {
    const simulate = (action: GarageVehicleAction, fps: number) => {
      const total =
        action === "park"
          ? GARAGE_SEQUENCE.park.totalMs
          : GARAGE_SEQUENCE.unpark.totalMs;
      let elapsed = 0;
      while (elapsed < total) elapsed += 1_000 / fps;
      return garageAnimationFrame(action, elapsed);
    };

    for (const fps of [60, 144, 240]) {
      expect(simulate("park", fps).state).toBe("parked");
      expect(simulate("unpark", fps).state).toBe("away");
    }
  });

  it("exposes exactly one action only in stable terminal states", () => {
    expect(garageActionForState("away")).toBe("park");
    expect(garageActionForState("parked")).toBe("unpark");
    expect(garageActionForState("parking")).toBeNull();
    expect(garageActionForState("unparking")).toBeNull();
    expect(garageActionLabel("park")).toBe("Zaparkovať auto");
    expect(garageActionLabel("unpark")).toBe("Odparkovať auto");
    expect(garageParkingStatus("closing-after-leave")).toContain(
      "brána sa zatvára",
    );
  });
});

describe("sectional garage door", () => {
  it("starts as eight vertical sections and finishes above the car", () => {
    const closed = Array.from(
      { length: GARAGE_VEHICLE.door.panelCount },
      (_, index) => garageDoorPanelPose(index, 0),
    );
    expect(closed.every(({ inwardOffsetM, pitchRad }) =>
      inwardOffsetM === 0 && pitchRad === 0,
    )).toBe(true);
    expect(closed[0].elevationM).toBeCloseTo(0.15, 6);
    expect(closed.at(-1)?.elevationM).toBeCloseTo(2.25, 6);

    const open = Array.from(
      { length: GARAGE_VEHICLE.door.panelCount },
      (_, index) => garageDoorPanelPose(index, 1),
    );
    expect(open.every(({ elevationM, pitchRad }) =>
      elevationM >= 2.54 && Math.abs(pitchRad - Math.PI / 2) < 1e-6,
    )).toBe(true);
    expect(open.at(-1)!.inwardOffsetM).toBeGreaterThan(
      open[0].inwardOffsetM,
    );
  });

  it("consumes already-eased controller progress without easing it twice", () => {
    const quarter = garageDoorPanelPose(0, 0.25);
    expect(quarter.elevationM).toBeCloseTo(
      GARAGE_VEHICLE.door.panelHeightM / 2 +
        GARAGE_VEHICLE.door.openTravelM * 0.25,
      6,
    );
  });
});
