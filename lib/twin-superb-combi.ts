export interface VehicleLoftStation {
  readonly x: number;
  readonly halfWidth: number;
  readonly baseY: number;
  readonly shoulderY: number;
  readonly crownY: number;
}

export interface VehicleLoftGeometry {
  readonly positions: readonly number[];
  readonly indices: readonly number[];
  readonly uvs: readonly number[];
}

export interface VehicleProfilePoint {
  readonly x: number;
  readonly y: number;
}

/** Official fourth-generation (2024+) Superb Combi geometry. */
export const GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM = Object.freeze({
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
} as const);

/** The revised garage holds the complete 4,902 mm production-length estate. */
export const GARAGE_SUPERB_VISUAL_LENGTH_SCALE = 1;
export const GARAGE_SUPERB_HALF_LENGTH_M =
  GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.length / 2_000;

/**
 * The detailed body was authored around the previous ±2.32 m envelope.
 * Expanding every longitudinal station through one helper keeps all panels,
 * glazing and trim registered while transverse and vertical dimensions stay
 * at their production values.
 */
export const GARAGE_SUPERB_AUTHORING_HALF_LENGTH_M = 2.32;
export const GARAGE_SUPERB_LONGITUDINAL_FACTOR =
  GARAGE_SUPERB_HALF_LENGTH_M / GARAGE_SUPERB_AUTHORING_HALF_LENGTH_M;
export const garageSuperbLongitudinalM = (authoredMetres: number) =>
  authoredMetres * GARAGE_SUPERB_LONGITUDINAL_FACTOR;

export const GARAGE_SUPERB_AXLES_M = Object.freeze({
  rearX:
    -GARAGE_SUPERB_HALF_LENGTH_M +
    GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.rearOverhang / 1_000,
  frontX:
    GARAGE_SUPERB_HALF_LENGTH_M -
    GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.frontOverhang / 1_000,
});

export const GARAGE_SUPERB_HALF_TRACKS_M = Object.freeze({
  rear: GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.rearTrack / 2_000,
  front: GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.frontTrack / 2_000,
});

export const GARAGE_SUPERB_WHEEL_M = Object.freeze({
  outerDiameter:
    GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.wheelOuterDiameter / 1_000,
  rimDiameter: GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.rimDiameter / 1_000,
  tireWidth: GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.tireWidth / 1_000,
  centerY:
    GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.wheelOuterDiameter / 2_000 + 0.015,
});

/** Painted lower body: long bonnet, low shoulder and asymmetric estate rear. */
export const GARAGE_SUPERB_BODY_STATIONS = Object.freeze([
  { x: garageSuperbLongitudinalM(-2.32), halfWidth: 0.71, baseY: 0.24, shoulderY: 0.63, crownY: 0.75 },
  { x: garageSuperbLongitudinalM(-2.27), halfWidth: 0.82, baseY: 0.2, shoulderY: 0.78, crownY: 0.87 },
  { x: garageSuperbLongitudinalM(-2.08), halfWidth: 0.89, baseY: 0.18, shoulderY: 0.87, crownY: 0.94 },
  { x: garageSuperbLongitudinalM(-1.72), halfWidth: 0.921, baseY: 0.164, shoulderY: 0.92, crownY: 0.99 },
  {
    x: GARAGE_SUPERB_AXLES_M.rearX,
    halfWidth: 0.9245,
    baseY: 0.158,
    shoulderY: 0.945,
    crownY: 1.012,
  },
  { x: garageSuperbLongitudinalM(-0.72), halfWidth: 0.9245, baseY: 0.154, shoulderY: 0.96, crownY: 1.025 },
  { x: garageSuperbLongitudinalM(0.18), halfWidth: 0.9245, baseY: 0.154, shoulderY: 0.965, crownY: 1.02 },
  { x: garageSuperbLongitudinalM(0.92), halfWidth: 0.923, baseY: 0.158, shoulderY: 0.945, crownY: 0.995 },
  {
    x: GARAGE_SUPERB_AXLES_M.frontX,
    halfWidth: 0.918,
    baseY: 0.164,
    shoulderY: 0.91,
    crownY: 0.95,
  },
  { x: garageSuperbLongitudinalM(1.77), halfWidth: 0.892, baseY: 0.18, shoulderY: 0.82, crownY: 0.875 },
  { x: garageSuperbLongitudinalM(2.08), halfWidth: 0.84, baseY: 0.205, shoulderY: 0.72, crownY: 0.79 },
  { x: garageSuperbLongitudinalM(2.27), halfWidth: 0.75, baseY: 0.24, shoulderY: 0.61, crownY: 0.7 },
  { x: garageSuperbLongitudinalM(2.32), halfWidth: 0.63, baseY: 0.29, shoulderY: 0.52, crownY: 0.61 },
] as const satisfies readonly VehicleLoftStation[]);

/** Glasshouse envelope used to verify the exact production height. */
export const GARAGE_SUPERB_CABIN_STATIONS = Object.freeze([
  { x: garageSuperbLongitudinalM(-2.02), halfWidth: 0.61, baseY: 0.98, shoulderY: 1.09, crownY: 1.35 },
  { x: garageSuperbLongitudinalM(-1.82), halfWidth: 0.69, baseY: 0.98, shoulderY: 1.16, crownY: 1.43 },
  { x: garageSuperbLongitudinalM(-1.35), halfWidth: 0.748, baseY: 0.985, shoulderY: 1.25, crownY: 1.475 },
  { x: garageSuperbLongitudinalM(-0.55), halfWidth: 0.775, baseY: 0.99, shoulderY: 1.29, crownY: 1.497 },
  { x: garageSuperbLongitudinalM(0.2), halfWidth: 0.775, baseY: 0.99, shoulderY: 1.29, crownY: 1.49 },
  { x: garageSuperbLongitudinalM(0.68), halfWidth: 0.735, baseY: 0.985, shoulderY: 1.24, crownY: 1.43 },
  { x: garageSuperbLongitudinalM(1.02), halfWidth: 0.66, baseY: 0.98, shoulderY: 1.13, crownY: 1.28 },
  { x: garageSuperbLongitudinalM(1.18), halfWidth: 0.57, baseY: 0.975, shoulderY: 1.04, crownY: 1.1 },
] as const satisfies readonly VehicleLoftStation[]);

/** Thin painted roof shell. Glazing is modeled as independent panes. */
export const GARAGE_SUPERB_ROOF_STATIONS = Object.freeze([
  { x: garageSuperbLongitudinalM(-1.98), halfWidth: 0.55, baseY: 1.315, shoulderY: 1.345, crownY: 1.375 },
  { x: garageSuperbLongitudinalM(-1.76), halfWidth: 0.66, baseY: 1.39, shoulderY: 1.42, crownY: 1.45 },
  { x: garageSuperbLongitudinalM(-1.25), halfWidth: 0.71, baseY: 1.445, shoulderY: 1.472, crownY: 1.49 },
  { x: garageSuperbLongitudinalM(-0.5), halfWidth: 0.72, baseY: 1.452, shoulderY: 1.48, crownY: 1.497 },
  { x: garageSuperbLongitudinalM(0.18), halfWidth: 0.72, baseY: 1.445, shoulderY: 1.475, crownY: 1.49 },
  { x: garageSuperbLongitudinalM(0.66), halfWidth: 0.68, baseY: 1.39, shoulderY: 1.415, crownY: 1.44 },
  { x: garageSuperbLongitudinalM(0.91), halfWidth: 0.61, baseY: 1.27, shoulderY: 1.3, crownY: 1.33 },
] as const satisfies readonly VehicleLoftStation[]);

export const GARAGE_SUPERB_SIDE_WINDOWS = Object.freeze([
  {
    id: "front",
    points: [
      { x: garageSuperbLongitudinalM(0.04), y: 1.025 },
      { x: garageSuperbLongitudinalM(0.91), y: 1.01 },
      { x: garageSuperbLongitudinalM(0.67), y: 1.38 },
      { x: garageSuperbLongitudinalM(0.08), y: 1.445 },
    ],
  },
  {
    id: "rear",
    points: [
      { x: garageSuperbLongitudinalM(-0.93), y: 1.02 },
      { x: garageSuperbLongitudinalM(-0.04), y: 1.025 },
      { x: 0, y: 1.445 },
      { x: garageSuperbLongitudinalM(-0.75), y: 1.44 },
    ],
  },
  {
    id: "quarter",
    points: [
      { x: garageSuperbLongitudinalM(-1.69), y: 1 },
      { x: garageSuperbLongitudinalM(-1.01), y: 1.02 },
      { x: garageSuperbLongitudinalM(-0.83), y: 1.425 },
      { x: garageSuperbLongitudinalM(-1.49), y: 1.35 },
    ],
  },
] as const satisfies readonly {
  readonly id: string;
  readonly points: readonly VehicleProfilePoint[];
}[]);

export const GARAGE_SUPERB_LOFT_RING_POINT_COUNT = 14;

function stationRing(station: VehicleLoftStation) {
  const { x, halfWidth: width, baseY, shoulderY, crownY } = station;
  const lowerY = Math.min(shoulderY - 0.055, baseY + 0.17);
  const midY = Math.max(lowerY + 0.035, shoulderY - 0.2);
  return [
    [x, baseY, 0],
    [x, baseY + 0.006, -width * 0.62],
    [x, baseY + 0.035, -width * 0.86],
    [x, lowerY, -width],
    [x, midY, -width],
    [x, shoulderY, -width * 0.98],
    [x, crownY - 0.035, -width * 0.72],
    [x, crownY, 0],
    [x, crownY - 0.035, width * 0.72],
    [x, shoulderY, width * 0.98],
    [x, midY, width],
    [x, lowerY, width],
    [x, baseY + 0.035, width * 0.86],
    [x, baseY + 0.006, width * 0.62],
  ] as const;
}

function validateStations(stations: readonly VehicleLoftStation[]) {
  if (stations.length < 2) throw new Error("Vehicle loft needs at least two stations.");
  for (let index = 0; index < stations.length; index += 1) {
    const station = stations[index];
    if (
      ![
        station.x,
        station.halfWidth,
        station.baseY,
        station.shoulderY,
        station.crownY,
      ].every(Number.isFinite)
    ) {
      throw new Error(`Vehicle loft station ${index} must be finite.`);
    }
    if (
      station.halfWidth <= 0 ||
      station.baseY >= station.shoulderY ||
      station.shoulderY > station.crownY
    ) {
      throw new Error(`Vehicle loft station ${index} has an invalid profile.`);
    }
    if (index > 0 && station.x <= stations[index - 1].x) {
      throw new Error("Vehicle loft station X values must increase.");
    }
  }
}

/** Smooth shell with duplicated, outward-facing caps for crisp fascia normals. */
export function vehicleLoftGeometry(
  stations: readonly VehicleLoftStation[],
): VehicleLoftGeometry {
  validateStations(stations);
  const positions: number[] = [];
  const uvs: number[] = [];
  const minimumX = stations[0].x;
  const span = stations.at(-1)!.x - minimumX;
  for (const station of stations) {
    const progress = (station.x - minimumX) / span;
    for (const [ringIndex, point] of stationRing(station).entries()) {
      positions.push(...point);
      uvs.push(progress, ringIndex / GARAGE_SUPERB_LOFT_RING_POINT_COUNT);
    }
  }

  const indices: number[] = [];
  for (let station = 0; station < stations.length - 1; station += 1) {
    const start = station * GARAGE_SUPERB_LOFT_RING_POINT_COUNT;
    const nextStart = start + GARAGE_SUPERB_LOFT_RING_POINT_COUNT;
    for (let ring = 0; ring < GARAGE_SUPERB_LOFT_RING_POINT_COUNT; ring += 1) {
      const ringNext = (ring + 1) % GARAGE_SUPERB_LOFT_RING_POINT_COUNT;
      const a = start + ring;
      const b = nextStart + ring;
      const c = nextStart + ringNext;
      const d = start + ringNext;
      indices.push(a, c, b, a, d, c);
    }
  }

  for (const [stationIndex, rear] of [
    [0, true],
    [stations.length - 1, false],
  ] as const) {
    const station = stations[stationIndex];
    const ring = stationRing(station);
    const capStart = positions.length / 3;
    for (const point of ring) {
      positions.push(...point);
      uvs.push(0.5 + point[2] / (station.halfWidth * 2), 0.5);
    }
    const centre = positions.length / 3;
    const centreY = ring.reduce((sum, point) => sum + point[1], 0) / ring.length;
    positions.push(station.x, centreY, 0);
    uvs.push(0.5, 0.5);
    for (let ringIndex = 0; ringIndex < GARAGE_SUPERB_LOFT_RING_POINT_COUNT; ringIndex += 1) {
      const current = capStart + ringIndex;
      const next =
        capStart + ((ringIndex + 1) % GARAGE_SUPERB_LOFT_RING_POINT_COUNT);
      if (rear) indices.push(centre, next, current);
      else indices.push(centre, current, next);
    }
  }
  return { positions, indices, uvs };
}

export function vehicleLoftBounds(geometry: VehicleLoftGeometry) {
  const minimum = [Infinity, Infinity, Infinity];
  const maximum = [-Infinity, -Infinity, -Infinity];
  for (let index = 0; index < geometry.positions.length; index += 3) {
    for (let axis = 0; axis < 3; axis += 1) {
      const value = geometry.positions[index + axis];
      minimum[axis] = Math.min(minimum[axis], value);
      maximum[axis] = Math.max(maximum[axis], value);
    }
  }
  return { minimum, maximum } as const;
}
