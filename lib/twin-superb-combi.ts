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

/**
 * Painted upper body. The dense stations keep the fourth-generation Superb's
 * low, long estate silhouette readable from both the side and front three-
 * quarter views. The lower sill is split around the wheel openings below.
 */
export const GARAGE_SUPERB_BODY_STATIONS = Object.freeze([
  { x: -GARAGE_SUPERB_HALF_LENGTH_M, halfWidth: 0.83, baseY: 0.56, shoulderY: 0.77, crownY: 0.86 },
  { x: garageSuperbLongitudinalM(-2.24), halfWidth: 0.88, baseY: 0.55, shoulderY: 0.82, crownY: 0.9 },
  { x: garageSuperbLongitudinalM(-2.1), halfWidth: 0.912, baseY: 0.54, shoulderY: 0.86, crownY: 0.92 },
  { x: garageSuperbLongitudinalM(-1.94), halfWidth: 0.923, baseY: 0.535, shoulderY: 0.875, crownY: 0.93 },
  { x: garageSuperbLongitudinalM(-1.72), halfWidth: 0.9245, baseY: 0.53, shoulderY: 0.89, crownY: 0.94 },
  { x: garageSuperbLongitudinalM(-1.55), halfWidth: 0.9245, baseY: 0.527, shoulderY: 0.897, crownY: 0.947 },
  {
    x: GARAGE_SUPERB_AXLES_M.rearX,
    halfWidth: 0.9245,
    baseY: 0.525,
    shoulderY: 0.9,
    crownY: 0.95,
  },
  { x: garageSuperbLongitudinalM(-1.05), halfWidth: 0.9245, baseY: 0.52, shoulderY: 0.885, crownY: 0.925 },
  { x: garageSuperbLongitudinalM(-0.8), halfWidth: 0.9245, baseY: 0.517, shoulderY: 0.88, crownY: 0.92 },
  { x: garageSuperbLongitudinalM(-0.55), halfWidth: 0.9245, baseY: 0.515, shoulderY: 0.875, crownY: 0.915 },
  { x: garageSuperbLongitudinalM(-0.25), halfWidth: 0.9245, baseY: 0.515, shoulderY: 0.875, crownY: 0.915 },
  { x: garageSuperbLongitudinalM(0.05), halfWidth: 0.9245, baseY: 0.515, shoulderY: 0.875, crownY: 0.915 },
  { x: garageSuperbLongitudinalM(0.3), halfWidth: 0.9245, baseY: 0.517, shoulderY: 0.878, crownY: 0.918 },
  { x: garageSuperbLongitudinalM(0.55), halfWidth: 0.9245, baseY: 0.52, shoulderY: 0.88, crownY: 0.92 },
  { x: garageSuperbLongitudinalM(0.95), halfWidth: 0.923, baseY: 0.525, shoulderY: 0.885, crownY: 0.925 },
  { x: garageSuperbLongitudinalM(1.22), halfWidth: 0.921, baseY: 0.53, shoulderY: 0.89, crownY: 0.93 },
  {
    x: GARAGE_SUPERB_AXLES_M.frontX,
    halfWidth: 0.916,
    baseY: 0.535,
    shoulderY: 0.86,
    crownY: 0.89,
  },
  { x: garageSuperbLongitudinalM(1.67), halfWidth: 0.91, baseY: 0.54, shoulderY: 0.845, crownY: 0.875 },
  { x: garageSuperbLongitudinalM(1.88), halfWidth: 0.9, baseY: 0.545, shoulderY: 0.825, crownY: 0.855 },
  { x: garageSuperbLongitudinalM(2.08), halfWidth: 0.89, baseY: 0.55, shoulderY: 0.795, crownY: 0.825 },
  { x: garageSuperbLongitudinalM(2.24), halfWidth: 0.875, baseY: 0.555, shoulderY: 0.765, crownY: 0.795 },
  { x: GARAGE_SUPERB_HALF_LENGTH_M, halfWidth: 0.86, baseY: 0.56, shoulderY: 0.75, crownY: 0.82 },
] as const satisfies readonly VehicleLoftStation[]);

export const GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M = 0.39;

/**
 * Three independent lower shells leave real openings around all four wheels.
 * The previous continuous loft painted over the wheels in side elevation and
 * was the main reason the car read as a solid box rather than a road vehicle.
 */
export const GARAGE_SUPERB_LOWER_BODY_SEGMENTS = Object.freeze([
  [
    { x: -GARAGE_SUPERB_HALF_LENGTH_M, halfWidth: 0.83, baseY: 0.19, shoulderY: 0.55, crownY: 0.6 },
    { x: garageSuperbLongitudinalM(-2.23), halfWidth: 0.885, baseY: 0.17, shoulderY: 0.59, crownY: 0.64 },
    { x: garageSuperbLongitudinalM(-2.02), halfWidth: 0.918, baseY: 0.155, shoulderY: 0.63, crownY: 0.68 },
    { x: GARAGE_SUPERB_AXLES_M.rearX - GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M, halfWidth: 0.9245, baseY: 0.15, shoulderY: 0.64, crownY: 0.69 },
  ],
  [
    { x: GARAGE_SUPERB_AXLES_M.rearX + GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M, halfWidth: 0.9245, baseY: 0.15, shoulderY: 0.625, crownY: 0.67 },
    { x: garageSuperbLongitudinalM(-0.55), halfWidth: 0.9245, baseY: 0.145, shoulderY: 0.61, crownY: 0.655 },
    { x: garageSuperbLongitudinalM(-0.15), halfWidth: 0.9245, baseY: 0.145, shoulderY: 0.608, crownY: 0.653 },
    { x: garageSuperbLongitudinalM(0.25), halfWidth: 0.9245, baseY: 0.145, shoulderY: 0.608, crownY: 0.653 },
    { x: garageSuperbLongitudinalM(0.45), halfWidth: 0.9245, baseY: 0.145, shoulderY: 0.61, crownY: 0.655 },
    { x: garageSuperbLongitudinalM(0.75), halfWidth: 0.923, baseY: 0.147, shoulderY: 0.615, crownY: 0.66 },
    { x: GARAGE_SUPERB_AXLES_M.frontX - GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M, halfWidth: 0.921, baseY: 0.15, shoulderY: 0.625, crownY: 0.67 },
  ],
  [
    { x: GARAGE_SUPERB_AXLES_M.frontX + GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M, halfWidth: 0.91, baseY: 0.16, shoulderY: 0.63, crownY: 0.68 },
    { x: garageSuperbLongitudinalM(2.08), halfWidth: 0.895, baseY: 0.17, shoulderY: 0.61, crownY: 0.66 },
    { x: garageSuperbLongitudinalM(2.25), halfWidth: 0.88, baseY: 0.19, shoulderY: 0.57, crownY: 0.62 },
    { x: GARAGE_SUPERB_HALF_LENGTH_M, halfWidth: 0.86, baseY: 0.23, shoulderY: 0.53, crownY: 0.58 },
  ],
] as const satisfies readonly (readonly VehicleLoftStation[])[]);

/** Glasshouse envelope used to verify the exact production height. */
export const GARAGE_SUPERB_CABIN_STATIONS = Object.freeze([
  { x: garageSuperbLongitudinalM(-2.04), halfWidth: 0.61, baseY: 0.855, shoulderY: 1.04, crownY: 1.2 },
  { x: garageSuperbLongitudinalM(-1.94), halfWidth: 0.67, baseY: 0.855, shoulderY: 1.14, crownY: 1.36 },
  { x: garageSuperbLongitudinalM(-1.78), halfWidth: 0.72, baseY: 0.858, shoulderY: 1.24, crownY: 1.445 },
  { x: garageSuperbLongitudinalM(-1.52), halfWidth: 0.755, baseY: 0.86, shoulderY: 1.3, crownY: 1.485 },
  { x: garageSuperbLongitudinalM(-1.3), halfWidth: 0.765, baseY: 0.861, shoulderY: 1.315, crownY: 1.492 },
  { x: garageSuperbLongitudinalM(-1.08), halfWidth: 0.772, baseY: 0.862, shoulderY: 1.325, crownY: 1.495 },
  { x: garageSuperbLongitudinalM(-0.8), halfWidth: 0.778, baseY: 0.862, shoulderY: 1.33, crownY: 1.497 },
  { x: garageSuperbLongitudinalM(-0.52), halfWidth: 0.78, baseY: 0.862, shoulderY: 1.33, crownY: 1.497 },
  { x: garageSuperbLongitudinalM(-0.25), halfWidth: 0.78, baseY: 0.862, shoulderY: 1.328, crownY: 1.496 },
  { x: garageSuperbLongitudinalM(0.02), halfWidth: 0.78, baseY: 0.862, shoulderY: 1.325, crownY: 1.495 },
  { x: garageSuperbLongitudinalM(0.4), halfWidth: 0.766, baseY: 0.86, shoulderY: 1.3, crownY: 1.48 },
  { x: garageSuperbLongitudinalM(0.68), halfWidth: 0.735, baseY: 0.858, shoulderY: 1.245, crownY: 1.43 },
  { x: garageSuperbLongitudinalM(0.92), halfWidth: 0.69, baseY: 0.855, shoulderY: 1.17, crownY: 1.34 },
  { x: garageSuperbLongitudinalM(1.1), halfWidth: 0.62, baseY: 0.852, shoulderY: 1.08, crownY: 1.2 },
  { x: garageSuperbLongitudinalM(1.2), halfWidth: 0.54, baseY: 0.85, shoulderY: 1.015, crownY: 1.07 },
] as const satisfies readonly VehicleLoftStation[]);

/** Thin painted roof shell. Glazing is modeled as independent panes. */
export const GARAGE_SUPERB_ROOF_STATIONS = Object.freeze([
  { x: garageSuperbLongitudinalM(-1.98), halfWidth: 0.57, baseY: 1.34, shoulderY: 1.385, crownY: 1.42 },
  { x: garageSuperbLongitudinalM(-1.82), halfWidth: 0.65, baseY: 1.41, shoulderY: 1.445, crownY: 1.47 },
  { x: garageSuperbLongitudinalM(-1.58), halfWidth: 0.7, baseY: 1.45, shoulderY: 1.475, crownY: 1.49 },
  { x: garageSuperbLongitudinalM(-1.2), halfWidth: 0.725, baseY: 1.465, shoulderY: 1.486, crownY: 1.497 },
  { x: garageSuperbLongitudinalM(-0.95), halfWidth: 0.73, baseY: 1.468, shoulderY: 1.487, crownY: 1.497 },
  { x: garageSuperbLongitudinalM(-0.7), halfWidth: 0.732, baseY: 1.468, shoulderY: 1.487, crownY: 1.497 },
  { x: garageSuperbLongitudinalM(-0.44), halfWidth: 0.733, baseY: 1.467, shoulderY: 1.486, crownY: 1.496 },
  { x: garageSuperbLongitudinalM(-0.18), halfWidth: 0.732, baseY: 1.466, shoulderY: 1.485, crownY: 1.495 },
  { x: garageSuperbLongitudinalM(0.04), halfWidth: 0.728, baseY: 1.458, shoulderY: 1.48, crownY: 1.49 },
  { x: garageSuperbLongitudinalM(0.25), halfWidth: 0.72, baseY: 1.45, shoulderY: 1.472, crownY: 1.485 },
  { x: garageSuperbLongitudinalM(0.52), halfWidth: 0.69, baseY: 1.415, shoulderY: 1.442, crownY: 1.46 },
  { x: garageSuperbLongitudinalM(0.72), halfWidth: 0.62, baseY: 1.335, shoulderY: 1.365, crownY: 1.39 },
] as const satisfies readonly VehicleLoftStation[]);

export const GARAGE_SUPERB_SIDE_WINDOWS = Object.freeze([
  {
    id: "front",
    points: [
      { x: garageSuperbLongitudinalM(0.04), y: 0.858 },
      { x: garageSuperbLongitudinalM(1.08), y: 0.852 },
      { x: garageSuperbLongitudinalM(0.64), y: 1.415 },
      { x: garageSuperbLongitudinalM(0.06), y: 1.458 },
    ],
  },
  {
    id: "rear",
    points: [
      { x: garageSuperbLongitudinalM(-1.18), y: 0.858 },
      { x: garageSuperbLongitudinalM(-0.04), y: 0.858 },
      { x: garageSuperbLongitudinalM(0.01), y: 1.458 },
      { x: garageSuperbLongitudinalM(-1.08), y: 1.452 },
    ],
  },
  {
    id: "quarter",
    points: [
      { x: garageSuperbLongitudinalM(-1.91), y: 0.855 },
      { x: garageSuperbLongitudinalM(-1.22), y: 0.858 },
      { x: garageSuperbLongitudinalM(-1.12), y: 1.448 },
      { x: garageSuperbLongitudinalM(-1.54), y: 1.425 },
      { x: garageSuperbLongitudinalM(-1.88), y: 1.075 },
    ],
  },
] as const satisfies readonly {
  readonly id: string;
  readonly points: readonly VehicleProfilePoint[];
}[]);

export const GARAGE_SUPERB_LOFT_RING_POINT_COUNT = 20;

function stationRing(station: VehicleLoftStation) {
  const { x, halfWidth: width, baseY, shoulderY, crownY } = station;
  const sideSpan = shoulderY - baseY;
  const roofSpan = crownY - shoulderY;
  return [
    [x, baseY, 0],
    [x, baseY + sideSpan * 0.02, -width * 0.56],
    [x, baseY + sideSpan * 0.08, -width * 0.82],
    [x, baseY + sideSpan * 0.2, -width * 0.96],
    [x, baseY + sideSpan * 0.4, -width],
    [x, baseY + sideSpan * 0.65, -width],
    [x, baseY + sideSpan * 0.84, -width * 0.995],
    [x, shoulderY, -width * 0.98],
    [x, shoulderY + roofSpan * 0.45, -width * 0.91],
    [x, crownY - roofSpan * 0.1, -width * 0.75],
    [x, crownY, 0],
    [x, crownY - roofSpan * 0.1, width * 0.75],
    [x, shoulderY + roofSpan * 0.45, width * 0.91],
    [x, shoulderY, width * 0.98],
    [x, baseY + sideSpan * 0.84, width * 0.995],
    [x, baseY + sideSpan * 0.65, width],
    [x, baseY + sideSpan * 0.4, width],
    [x, baseY + sideSpan * 0.2, width * 0.96],
    [x, baseY + sideSpan * 0.08, width * 0.82],
    [x, baseY + sideSpan * 0.02, width * 0.56],
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
