import { describe, expect, it } from "vitest";

import {
  GARAGE_SEQUENCE,
  GARAGE_VEHICLE,
  garageActionForState,
  garageActionLabel,
  garageAnimationFrame,
  garageDoorPanelPose,
  garageParkingStatus,
  garageVehiclePlanCorners,
  garageVehicleSurfaceElevationM,
  type GarageVehicleAction,
} from "../lib/twin-garage";
import { GARAGE_FITOUT } from "../lib/twin-interior";
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
