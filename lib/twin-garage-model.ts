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

/**
 * Modern Superb-inspired liftback body. The 4.64 m length is deliberately
 * shorter than the production car because it is the largest safe envelope
 * between this garage's rear wall and closed sectional door.
 */
export const GARAGE_SUPERB_BODY_STATIONS = Object.freeze([
  { x: -2.3, halfWidth: 0.76, baseY: 0.2, shoulderY: 0.58, crownY: 0.66 },
  { x: -2.2, halfWidth: 0.84, baseY: 0.19, shoulderY: 0.78, crownY: 0.88 },
  { x: -1.78, halfWidth: 0.91, baseY: 0.18, shoulderY: 0.9, crownY: 0.98 },
  { x: -1.346, halfWidth: 0.9245, baseY: 0.18, shoulderY: 0.95, crownY: 1.02 },
  { x: -0.45, halfWidth: 0.9245, baseY: 0.18, shoulderY: 0.98, crownY: 1.05 },
  { x: 0.65, halfWidth: 0.9245, baseY: 0.18, shoulderY: 0.97, crownY: 1.04 },
  { x: 1.494, halfWidth: 0.918, baseY: 0.18, shoulderY: 0.93, crownY: 0.99 },
  { x: 2.05, halfWidth: 0.84, baseY: 0.19, shoulderY: 0.82, crownY: 0.9 },
  { x: 2.3, halfWidth: 0.74, baseY: 0.22, shoulderY: 0.56, crownY: 0.64 },
] as const satisfies readonly VehicleLoftStation[]);

export const GARAGE_SUPERB_CABIN_STATIONS = Object.freeze([
  { x: -1.52, halfWidth: 0.63, baseY: 0.97, shoulderY: 1.0, crownY: 1.18 },
  { x: -1.2, halfWidth: 0.7, baseY: 0.97, shoulderY: 1.01, crownY: 1.4 },
  { x: -0.65, halfWidth: 0.75, baseY: 0.97, shoulderY: 1.02, crownY: 1.475 },
  { x: 0.2, halfWidth: 0.75, baseY: 0.97, shoulderY: 1.02, crownY: 1.496 },
  { x: 0.78, halfWidth: 0.7, baseY: 0.97, shoulderY: 1.01, crownY: 1.4 },
  { x: 1.08, halfWidth: 0.62, baseY: 0.97, shoulderY: 1.0, crownY: 1.2 },
] as const satisfies readonly VehicleLoftStation[]);

export const GARAGE_SUPERB_AXLES_M = Object.freeze({
  rearX: -1.346,
  frontX: 1.494,
});

const SECTION_POINT_COUNT = 10;

function stationRing(station: VehicleLoftStation) {
  const { x, halfWidth: width, baseY, shoulderY, crownY } = station;
  const lowerY = Math.min(shoulderY - 0.02, baseY + 0.16);
  return [
    [x, baseY, 0],
    [x, baseY + 0.01, -width * 0.72],
    [x, lowerY, -width],
    [x, shoulderY, -width],
    [x, crownY - 0.02, -width * 0.72],
    [x, crownY, 0],
    [x, crownY - 0.02, width * 0.72],
    [x, shoulderY, width],
    [x, lowerY, width],
    [x, baseY + 0.01, width * 0.72],
  ] as const;
}

/** Closed, capped and Z-symmetric loft data; Babylon computes smooth normals. */
export function vehicleLoftGeometry(
  stations: readonly VehicleLoftStation[],
): VehicleLoftGeometry {
  if (stations.length < 2) {
    throw new Error("Vehicle loft needs at least two stations.");
  }
  const positions: number[] = [];
  const uvs: number[] = [];
  for (let stationIndex = 0; stationIndex < stations.length; stationIndex += 1) {
    const stationProgress = stationIndex / (stations.length - 1);
    const ring = stationRing(stations[stationIndex]);
    for (let ringIndex = 0; ringIndex < ring.length; ringIndex += 1) {
      positions.push(...ring[ringIndex]);
      uvs.push(stationProgress, ringIndex / SECTION_POINT_COUNT);
    }
  }

  const indices: number[] = [];
  for (let stationIndex = 0; stationIndex < stations.length - 1; stationIndex += 1) {
    const start = stationIndex * SECTION_POINT_COUNT;
    const nextStart = start + SECTION_POINT_COUNT;
    for (let ringIndex = 0; ringIndex < SECTION_POINT_COUNT; ringIndex += 1) {
      const ringNext = (ringIndex + 1) % SECTION_POINT_COUNT;
      const a = start + ringIndex;
      const b = nextStart + ringIndex;
      const c = nextStart + ringNext;
      const d = start + ringNext;
      // Ring tangent x longitudinal tangent points out of the closed shell.
      indices.push(a, c, b, a, d, c);
    }
  }

  // The ring winding points toward +X. Reverse it on the rear cap.
  for (let ringIndex = 1; ringIndex < SECTION_POINT_COUNT - 1; ringIndex += 1) {
    indices.push(0, ringIndex + 1, ringIndex);
  }
  const frontStart = (stations.length - 1) * SECTION_POINT_COUNT;
  for (let ringIndex = 1; ringIndex < SECTION_POINT_COUNT - 1; ringIndex += 1) {
    indices.push(frontStart, frontStart + ringIndex, frontStart + ringIndex + 1);
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
