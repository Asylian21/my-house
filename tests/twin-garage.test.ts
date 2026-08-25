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
  GARAGE_SUPERB_CABIN_STATIONS,
  vehicleLoftBounds,
  vehicleLoftGeometry,
} from "../lib/twin-garage-model";
import { GARAGE_FITOUT, INTERIOR_ROOMS } from "../lib/twin-interior";
import { HOUSE, SITE_SURFACES } from "../lib/twin-site";

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
    expect(Math.max(...ys)).toBeLessThan(7_749 - 40);
    expect(Math.min(...xs)).toBeGreaterThan(6_944);
    expect(Math.max(...xs)).toBeLessThan(10_842);
    expect(GARAGE_VEHICLE.dimensionsMm.height).toBeLessThan(
      GARAGE_FITOUT.rearWallShelves.clearBelowMm,
    );
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
  it("builds finite, capped and index-safe smooth lofts", () => {
    for (const stations of [
      GARAGE_SUPERB_BODY_STATIONS,
      GARAGE_SUPERB_CABIN_STATIONS,
    ]) {
      const geometry = vehicleLoftGeometry(stations);
      expect(geometry.positions.length).toBe(stations.length * 10 * 3);
      expect(geometry.positions.every(Number.isFinite)).toBe(true);
      expect(geometry.uvs.every(Number.isFinite)).toBe(true);
      expect(geometry.indices.length % 3).toBe(0);
      expect(Math.min(...geometry.indices)).toBe(0);
      expect(Math.max(...geometry.indices)).toBeLessThan(
        geometry.positions.length / 3,
      );
    }
  });

  it("matches modern proportions while staying inside the garage envelope", () => {
    const body = vehicleLoftBounds(
      vehicleLoftGeometry(GARAGE_SUPERB_BODY_STATIONS),
    );
    const cabin = vehicleLoftBounds(
      vehicleLoftGeometry(GARAGE_SUPERB_CABIN_STATIONS),
    );
    expect(body.maximum[2] - body.minimum[2]).toBeCloseTo(1.849, 6);
    expect(Math.max(Math.abs(body.minimum[0]), body.maximum[0])).toBeLessThanOrEqual(
      GARAGE_VEHICLE.dimensionsMm.length / 2_000,
    );
    expect(Math.max(Math.abs(body.minimum[2]), body.maximum[2])).toBeLessThanOrEqual(
      GARAGE_VEHICLE.dimensionsMm.width / 2_000,
    );
    expect(cabin.maximum[1] - GARAGE_VEHICLE.wheelGroundOffsetM).toBeCloseTo(
      GARAGE_VEHICLE.dimensionsMm.height / 1_000,
      6,
    );
    expect(GARAGE_VEHICLE.dimensionsMm.width).toBe(2_090);
    expect(GARAGE_SUPERB_AXLES_M.frontX - GARAGE_SUPERB_AXLES_M.rearX).toBeCloseTo(
      GARAGE_VEHICLE.dimensionsMm.wheelbase / 1_000,
      6,
    );
  });

  it("keeps every loft cross-section exactly symmetric around vehicle Z", () => {
    for (const stations of [
      GARAGE_SUPERB_BODY_STATIONS,
      GARAGE_SUPERB_CABIN_STATIONS,
    ]) {
      const { positions } = vehicleLoftGeometry(stations);
      for (let station = 0; station < stations.length; station += 1) {
        const zValues = Array.from({ length: 10 }, (_, ring) =>
          positions[(station * 10 + ring) * 3 + 2].toFixed(6),
        );
        for (const value of zValues) {
          expect(zValues).toContain((-Number(value)).toFixed(6));
        }
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
