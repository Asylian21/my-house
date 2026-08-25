import { HOUSE, SITE_SURFACES, type Point2Mm } from "./twin-site";

export type GarageVehicleAction = "park" | "unpark";

export type GarageParkingState =
  | "away"
  | "arriving"
  | "opening-to-park"
  | "parking"
  | "closing-after-park"
  | "parked"
  | "opening-to-leave"
  | "unparking"
  | "closing-after-leave"
  | "departing";

export interface GarageVehiclePose {
  readonly centerMm: Point2Mm;
  /** Plan heading in radians: 0 = +X, PI / 2 = from street into the garage. */
  readonly headingRad: number;
  readonly motion: "forward" | "reverse" | "still";
}

export interface GarageAnimationFrame {
  readonly state: GarageParkingState;
  readonly doorProgress: number;
  readonly vehicleVisible: boolean;
  readonly vehiclePose: GarageVehiclePose;
  readonly complete: boolean;
}

export interface GarageDoorPanelPose {
  readonly elevationM: number;
  readonly inwardOffsetM: number;
  readonly pitchRad: number;
}

const GARAGE_DOOR = HOUSE.facades.front.garageDoor;
const DRIVEWAY = SITE_SURFACES.driveway;

export const GARAGE_VEHICLE = Object.freeze({
  id: "GARAGE-VEHICLE-SKODA-SUPERB",
  label: "Škoda Superb",
  roomId: "ROOM-1-12",
  garageDoorId: GARAGE_DOOR.id,
  dimensionsMm: {
    // A restrained visual envelope tuned to the documented 4.785 m available
    // between the garage-door plane and the rear wall. The recognisable Superb
    // proportions are retained without clipping either closing leaf or wall.
    length: 4_640,
    // Width includes the mirrors; height is the complete visible envelope.
    width: 2_090,
    height: 1_481,
    wheelbase: 2_840,
  },
  /** Lowest tyre point sits this far above the vehicle root. */
  wheelGroundOffsetM: 0.015,
  door: {
    panelCount: 8,
    panelHeightM: GARAGE_DOOR.heightMm / 8 / 1_000,
    widthMm: GARAGE_DOOR.widthMm,
    heightMm: GARAGE_DOOR.heightMm,
    faceYmm: HOUSE.facades.front.faceYmm - 36,
    curveStartElevationM: 2.25,
    curveRadiusM: 0.3,
    openTravelM: 2.62,
  },
  route: {
    queueMm: {
      x: GARAGE_DOOR.startXmm + GARAGE_DOOR.widthMm / 2,
      y: -1_500,
    } satisfies Point2Mm,
    parkedMm: {
      x: GARAGE_DOOR.startXmm + GARAGE_DOOR.widthMm / 2,
      y: 5_370,
    } satisfies Point2Mm,
    // A 5.55 m quarter-turn keeps the street approach calm and has the car
    // fully aligned with the driveway at the asphalt edge.
    streetStartMm: { x: -10_000, y: -8_654 } satisfies Point2Mm,
    streetTurnStartMm: { x: 3_040, y: -8_654 } satisfies Point2Mm,
    streetTurnControl1Mm: { x: 6_105, y: -8_654 } satisfies Point2Mm,
    streetTurnControl2Mm: { x: 8_590, y: -6_169 } satisfies Point2Mm,
    drivewayEntryMm: {
      x: GARAGE_DOOR.startXmm + GARAGE_DOOR.widthMm / 2,
      y: DRIVEWAY.streetConnection.asphaltEdgeYmm,
    } satisfies Point2Mm,
    streetDepartureMm: { x: 15_000, y: -8_654 } satisfies Point2Mm,
  },
  driveway: {
    xMinMm: Math.min(...DRIVEWAY.polygonMm.map(({ x }) => x)),
    xMaxMm: Math.max(...DRIVEWAY.polygonMm.map(({ x }) => x)),
    asphaltEdgeYmm: DRIVEWAY.streetConnection.asphaltEdgeYmm,
    houseFaceYmm: DRIVEWAY.streetConnection.houseFaceYmm,
  },
} as const);

export const GARAGE_SEQUENCE = Object.freeze({
  park: {
    streetApproachEndMs: 1_800,
    streetTurnEndMs: 4_000,
    arrivalEndMs: 5_000,
    openingEndMs: 7_300,
    parkingEndMs: 11_800,
    totalMs: 14_100,
  },
  unpark: {
    openingEndMs: 2_300,
    straightReverseEndMs: 6_000,
    drivewayReverseEndMs: 7_000,
    streetReverseEndMs: 9_200,
    departureStartMs: 9_700,
    doorClosedMs: 11_500,
    totalMs: 12_500,
  },
} as const);

function clamp01(value: number) {
  return Math.max(0, Math.min(1, Number.isFinite(value) ? value : 0));
}

function smooth(value: number) {
  const t = clamp01(value);
  return t * t * (3 - 2 * t);
}

function lerp(start: number, end: number, progress: number) {
  return start + (end - start) * progress;
}

function stationaryPose(
  centerMm: Point2Mm,
  headingRad: number,
): GarageVehiclePose {
  return { centerMm, headingRad, motion: "still" };
}

function straightPose(
  start: Point2Mm,
  end: Point2Mm,
  progress: number,
  motion: "forward" | "reverse",
  headingRad = Math.atan2(end.y - start.y, end.x - start.x),
): GarageVehiclePose {
  const t = smooth(progress);
  return {
    centerMm: {
      x: lerp(start.x, end.x, t),
      y: lerp(start.y, end.y, t),
    },
    headingRad,
    motion,
  };
}

function cubicPose(
  points: readonly [Point2Mm, Point2Mm, Point2Mm, Point2Mm],
  progress: number,
  motion: "forward" | "reverse",
) {
  const t = smooth(progress);
  const oneMinusT = 1 - t;
  const [p0, p1, p2, p3] = points;
  const centerMm = {
    x:
      oneMinusT ** 3 * p0.x +
      3 * oneMinusT ** 2 * t * p1.x +
      3 * oneMinusT * t ** 2 * p2.x +
      t ** 3 * p3.x,
    y:
      oneMinusT ** 3 * p0.y +
      3 * oneMinusT ** 2 * t * p1.y +
      3 * oneMinusT * t ** 2 * p2.y +
      t ** 3 * p3.y,
  };
  let dx =
    3 * oneMinusT ** 2 * (p1.x - p0.x) +
    6 * oneMinusT * t * (p2.x - p1.x) +
    3 * t ** 2 * (p3.x - p2.x);
  let dy =
    3 * oneMinusT ** 2 * (p1.y - p0.y) +
    6 * oneMinusT * t * (p2.y - p1.y) +
    3 * t ** 2 * (p3.y - p2.y);
  if (motion === "reverse") {
    dx *= -1;
    dy *= -1;
  }
  return {
    centerMm,
    headingRad: Math.atan2(dy, dx),
    motion,
  } satisfies GarageVehiclePose;
}

const STREET_TURN_CURVE = [
  GARAGE_VEHICLE.route.streetTurnStartMm,
  GARAGE_VEHICLE.route.streetTurnControl1Mm,
  GARAGE_VEHICLE.route.streetTurnControl2Mm,
  GARAGE_VEHICLE.route.drivewayEntryMm,
] as const satisfies readonly [Point2Mm, Point2Mm, Point2Mm, Point2Mm];

const REVERSE_TO_STREET_CURVE = [
  GARAGE_VEHICLE.route.drivewayEntryMm,
  GARAGE_VEHICLE.route.streetTurnControl2Mm,
  GARAGE_VEHICLE.route.streetTurnControl1Mm,
  GARAGE_VEHICLE.route.streetTurnStartMm,
] as const satisfies readonly [Point2Mm, Point2Mm, Point2Mm, Point2Mm];

const PARKED_POSE = stationaryPose(
  GARAGE_VEHICLE.route.parkedMm,
  Math.PI / 2,
);
const QUEUE_POSE = stationaryPose(
  GARAGE_VEHICLE.route.queueMm,
  Math.PI / 2,
);
const STREET_EXIT_POSE = stationaryPose(
  GARAGE_VEHICLE.route.streetTurnStartMm,
  0,
);

/** Top elevation of the road, graded driveway, threshold or garage floor. */
export function garageVehicleSurfaceElevationM(centerMm: Point2Mm) {
  const { asphaltEdgeYmm, houseFaceYmm } = GARAGE_VEHICLE.driveway;
  if (centerMm.y <= asphaltEdgeYmm) return -0.11;
  if (centerMm.y <= 0) {
    return (
      -0.11 +
      ((centerMm.y - asphaltEdgeYmm) / Math.max(1, -asphaltEdgeYmm)) * 0.08
    );
  }
  if (centerMm.y <= houseFaceYmm) {
    return -0.03 + (centerMm.y / Math.max(1, houseFaceYmm)) * 0.015;
  }
  // Bridge the facade build-up to the level 1.NP epoxy floor.
  const garageFloorStartYmm = 3_504;
  if (centerMm.y < garageFloorStartYmm) {
    return lerp(
      -0.015,
      0,
      (centerMm.y - houseFaceYmm) /
        (garageFloorStartYmm - houseFaceYmm),
    );
  }
  return 0;
}

/** Four exact plan corners of the complete mirror-to-mirror visual envelope. */
export function garageVehiclePlanCorners(pose: GarageVehiclePose) {
  const halfLength = GARAGE_VEHICLE.dimensionsMm.length / 2;
  const halfWidth = GARAGE_VEHICLE.dimensionsMm.width / 2;
  const forwardX = Math.cos(pose.headingRad);
  const forwardY = Math.sin(pose.headingRad);
  const sideX = -forwardY;
  const sideY = forwardX;
  return ([-1, 1] as const).flatMap((lengthSign) =>
    ([-1, 1] as const).map((widthSign) => ({
      x:
        pose.centerMm.x +
        lengthSign * halfLength * forwardX +
        widthSign * halfWidth * sideX,
      y:
        pose.centerMm.y +
        lengthSign * halfLength * forwardY +
        widthSign * halfWidth * sideY,
    })),
  );
}

/**
 * The walker must not be frozen in the car's swept parking lane or in the
 * sectional-door safety strip while the street cinematic is running.
 */
export function garageCinematicRequiresSafePosition(
  pointMm: Point2Mm,
  avatarClearanceMm = 400,
) {
  const clearance = Math.max(0, avatarClearanceMm);
  const laneHalfWidth = GARAGE_VEHICLE.dimensionsMm.width / 2 + clearance;
  const laneMinimumY = GARAGE_VEHICLE.door.faceYmm - clearance;
  const laneMaximumY =
    GARAGE_VEHICLE.route.parkedMm.y +
    GARAGE_VEHICLE.dimensionsMm.length / 2 +
    clearance;
  const inVehicleLane =
    Math.abs(pointMm.x - GARAGE_VEHICLE.route.parkedMm.x) <= laneHalfWidth &&
    pointMm.y >= laneMinimumY &&
    pointMm.y <= laneMaximumY;

  const doorMinimumX =
    GARAGE_VEHICLE.route.parkedMm.x - GARAGE_VEHICLE.door.widthMm / 2;
  const inDoorSafetyStrip =
    pointMm.x >= doorMinimumX - clearance &&
    pointMm.x <= doorMinimumX + GARAGE_VEHICLE.door.widthMm + clearance &&
    Math.abs(pointMm.y - GARAGE_VEHICLE.door.faceYmm) <= 700 + clearance;
  return inVehicleLane || inDoorSafetyStrip;
}

export function garageAnimationFrame(
  action: GarageVehicleAction,
  elapsedMs: number,
): GarageAnimationFrame {
  const elapsed = Math.max(0, Number.isFinite(elapsedMs) ? elapsedMs : 0);

  if (action === "park") {
    const timing = GARAGE_SEQUENCE.park;
    if (elapsed < timing.streetApproachEndMs) {
      return {
        state: "arriving",
        doorProgress: 0,
        vehicleVisible: true,
        vehiclePose: straightPose(
          GARAGE_VEHICLE.route.streetStartMm,
          GARAGE_VEHICLE.route.streetTurnStartMm,
          elapsed / timing.streetApproachEndMs,
          "forward",
        ),
        complete: false,
      };
    }
    if (elapsed < timing.streetTurnEndMs) {
      return {
        state: "arriving",
        doorProgress: 0,
        vehicleVisible: true,
        vehiclePose: cubicPose(
          STREET_TURN_CURVE,
          (elapsed - timing.streetApproachEndMs) /
            (timing.streetTurnEndMs - timing.streetApproachEndMs),
          "forward",
        ),
        complete: false,
      };
    }
    if (elapsed < timing.arrivalEndMs) {
      return {
        state: "arriving",
        doorProgress: 0,
        vehicleVisible: true,
        vehiclePose: straightPose(
          GARAGE_VEHICLE.route.drivewayEntryMm,
          GARAGE_VEHICLE.route.queueMm,
          (elapsed - timing.streetTurnEndMs) /
            (timing.arrivalEndMs - timing.streetTurnEndMs),
          "forward",
          Math.PI / 2,
        ),
        complete: false,
      };
    }
    if (elapsed < timing.openingEndMs) {
      return {
        state: "opening-to-park",
        doorProgress: smooth(
          (elapsed - timing.arrivalEndMs) /
            (timing.openingEndMs - timing.arrivalEndMs),
        ),
        vehicleVisible: true,
        vehiclePose: QUEUE_POSE,
        complete: false,
      };
    }
    if (elapsed < timing.parkingEndMs) {
      return {
        state: "parking",
        doorProgress: 1,
        vehicleVisible: true,
        vehiclePose: straightPose(
          GARAGE_VEHICLE.route.queueMm,
          GARAGE_VEHICLE.route.parkedMm,
          (elapsed - timing.openingEndMs) /
            (timing.parkingEndMs - timing.openingEndMs),
          "forward",
          Math.PI / 2,
        ),
        complete: false,
      };
    }
    if (elapsed < timing.totalMs) {
      return {
        state: "closing-after-park",
        doorProgress:
          1 -
          smooth(
            (elapsed - timing.parkingEndMs) /
              (timing.totalMs - timing.parkingEndMs),
          ),
        vehicleVisible: true,
        vehiclePose: PARKED_POSE,
        complete: false,
      };
    }
    return {
      state: "parked",
      doorProgress: 0,
      vehicleVisible: true,
      vehiclePose: PARKED_POSE,
      complete: true,
    };
  }

  const timing = GARAGE_SEQUENCE.unpark;
  if (elapsed < timing.openingEndMs) {
    return {
      state: "opening-to-leave",
      doorProgress: smooth(elapsed / timing.openingEndMs),
      vehicleVisible: true,
      vehiclePose: PARKED_POSE,
      complete: false,
    };
  }
  if (elapsed < timing.straightReverseEndMs) {
    return {
      state: "unparking",
      doorProgress: 1,
      vehicleVisible: true,
      vehiclePose: straightPose(
        GARAGE_VEHICLE.route.parkedMm,
        GARAGE_VEHICLE.route.queueMm,
        (elapsed - timing.openingEndMs) /
          (timing.straightReverseEndMs - timing.openingEndMs),
        "reverse",
        Math.PI / 2,
      ),
      complete: false,
    };
  }
  if (elapsed < timing.streetReverseEndMs) {
    if (elapsed < timing.drivewayReverseEndMs) {
      return {
        state: "unparking",
        doorProgress: 1,
        vehicleVisible: true,
        vehiclePose: straightPose(
          GARAGE_VEHICLE.route.queueMm,
          GARAGE_VEHICLE.route.drivewayEntryMm,
          (elapsed - timing.straightReverseEndMs) /
            (timing.drivewayReverseEndMs - timing.straightReverseEndMs),
          "reverse",
          Math.PI / 2,
        ),
        complete: false,
      };
    }
    return {
      state: "unparking",
      doorProgress: 1,
      vehicleVisible: true,
      vehiclePose: cubicPose(
        REVERSE_TO_STREET_CURVE,
        (elapsed - timing.drivewayReverseEndMs) /
          (timing.streetReverseEndMs - timing.drivewayReverseEndMs),
        "reverse",
      ),
      complete: false,
    };
  }
  if (elapsed < timing.departureStartMs) {
    return {
      state: "closing-after-leave",
      doorProgress: 1,
      vehicleVisible: true,
      vehiclePose: STREET_EXIT_POSE,
      complete: false,
    };
  }
  if (elapsed < timing.totalMs) {
    const doorProgress =
      elapsed >= timing.doorClosedMs
        ? 0
        : 1 -
          smooth(
            (elapsed - timing.departureStartMs) /
              (timing.doorClosedMs - timing.departureStartMs),
          );
    return {
      state:
        elapsed < timing.doorClosedMs
          ? "closing-after-leave"
          : "departing",
      doorProgress,
      vehicleVisible: true,
      vehiclePose: straightPose(
        GARAGE_VEHICLE.route.streetTurnStartMm,
        GARAGE_VEHICLE.route.streetDepartureMm,
        (elapsed - timing.departureStartMs) /
          (timing.totalMs - timing.departureStartMs),
        "forward",
        Math.PI,
      ),
      complete: false,
    };
  }
  return {
    state: "away",
    doorProgress: 0,
    vehicleVisible: false,
    vehiclePose: stationaryPose(
      GARAGE_VEHICLE.route.streetDepartureMm,
      Math.PI,
    ),
    complete: true,
  };
}

export function garageDoorPanelPose(
  panelIndex: number,
  progress: number,
): GarageDoorPanelPose {
  const door = GARAGE_VEHICLE.door;
  const safeIndex = Math.max(
    0,
    Math.min(door.panelCount - 1, Math.trunc(panelIndex)),
  );
  const distanceM =
    (safeIndex + 0.5) * door.panelHeightM +
    clamp01(progress) * door.openTravelM;
  const curveLengthM = (Math.PI / 2) * door.curveRadiusM;
  const curveDistanceM = distanceM - door.curveStartElevationM;

  if (curveDistanceM <= 0) {
    return {
      elevationM: distanceM,
      inwardOffsetM: 0,
      pitchRad: 0,
    };
  }
  if (curveDistanceM < curveLengthM) {
    const angle = curveDistanceM / door.curveRadiusM;
    return {
      elevationM:
        door.curveStartElevationM +
        Math.sin(angle) * door.curveRadiusM,
      inwardOffsetM: (1 - Math.cos(angle)) * door.curveRadiusM,
      pitchRad: angle,
    };
  }
  return {
    elevationM: door.curveStartElevationM + door.curveRadiusM,
    inwardOffsetM:
      door.curveRadiusM + (curveDistanceM - curveLengthM),
    pitchRad: Math.PI / 2,
  };
}

export function garageActionForState(
  state: GarageParkingState,
): GarageVehicleAction | null {
  if (state === "away") return "park";
  if (state === "parked") return "unpark";
  return null;
}

export function garageActionLabel(action: GarageVehicleAction) {
  return action === "park" ? "Zaparkovať auto" : "Odparkovať auto";
}

export function garageParkingStatus(state: GarageParkingState) {
  switch (state) {
    case "away":
      return "Auto čaká na ulici";
    case "arriving":
      return "Superb prichádza k bráne";
    case "opening-to-park":
      return "Garážová brána sa otvára";
    case "parking":
      return "Superb parkuje do garáže";
    case "closing-after-park":
      return "Brána sa zatvára za autom";
    case "parked":
      return "Superb je zaparkovaný";
    case "opening-to-leave":
      return "Garážová brána sa otvára";
    case "unparking":
      return "Superb vyparkúva na ulicu";
    case "closing-after-leave":
      return "Superb odchádza · brána sa zatvára";
    case "departing":
      return "Superb odchádza po ulici";
  }
}
