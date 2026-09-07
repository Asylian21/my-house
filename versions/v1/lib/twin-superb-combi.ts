/**
 * Fourth-generation (2024+) Škoda Superb Combi exterior geometry.
 *
 * The body is a single smooth loft driven by continuous longitudinal curves
 * (belt line, roof line, plan taper, rocker with real wheel-arch cut-outs).
 * This replaces the earlier box-like three-shell construction that did not
 * resemble the client-supplied reference photographs.
 */

export interface VehicleSection {
  /** Longitudinal position; +X is the nose. */
  readonly x: number;
  /** Bottom edge of the painted body (rocker line or wheel-arch cut). */
  readonly baseY: number;
  /** Widest half-width of the section, reached at the shoulder crease. */
  readonly maxHalf: number;
  /** Belt line (bottom of the glasshouse / top of the fender). */
  readonly beltY: number;
  /** Half-width at the belt line. */
  readonly beltHalf: number;
  /** Crown of the section (roof, windscreen surface or hood centre). */
  readonly roofY: number;
  /** Half-width of the crown plateau. */
  readonly roofHalf: number;
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

/** Official fourth-generation (2024+) Superb Combi dimensions. */
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

/** The garage holds the complete 4,902 mm production-length estate. */
export const GARAGE_SUPERB_VISUAL_LENGTH_SCALE = 1;
export const GARAGE_SUPERB_HALF_LENGTH_M =
  GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.length / 2_000;

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

/** Radius of the circular wheel-arch opening cut into the body side. */
export const GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M = 0.37;

type CurveControls = readonly (readonly [number, number])[];

/** Smoothstep interpolation across ordered control points. */
function sampleCurve(controls: CurveControls, x: number): number {
  if (x <= controls[0][0]) return controls[0][1];
  const last = controls[controls.length - 1];
  if (x >= last[0]) return last[1];
  for (let index = 0; index < controls.length - 1; index += 1) {
    const [x0, y0] = controls[index];
    const [x1, y1] = controls[index + 1];
    if (x <= x1) {
      const t = (x - x0) / (x1 - x0);
      const smooth = t * t * (3 - 2 * t);
      return y0 + (y1 - y0) * smooth;
    }
  }
  return last[1];
}

/**
 * Reference-photo silhouette curves (metres, authored at production scale).
 * Belt line rises gently rearwards with the photographed quarter kick-up.
 */
const BELT_Y: CurveControls = [
  [-2.451, 0.985],
  [-2.1, 0.968],
  [-1.6, 0.938],
  [-1.0, 0.91],
  [-0.3, 0.888],
  [0.4, 0.877],
  [1.05, 0.872],
  [1.6, 0.868],
  [2.0, 0.858],
  [2.26, 0.842],
  [2.451, 0.815],
];

/** Crown line: tail spoiler, raked tailgate glass, long flat roof, fast
 * windscreen and an almost level bonnet falling toward the grille. */
const ROOF_Y: CurveControls = [
  [-2.451, 1.29],
  [-2.32, 1.336],
  [-2.1, 1.392],
  [-1.9, 1.421],
  [-1.72, 1.44],
  [-1.45, 1.454],
  [-1.1, 1.463],
  [-0.7, 1.467],
  [-0.3, 1.4655],
  [0.02, 1.452],
  [0.2, 1.375],
  [0.45, 1.212],
  [0.66, 1.05],
  [0.78, 0.968],
  [1.1, 0.94],
  [1.5, 0.9185],
  [1.9, 0.902],
  [2.2, 0.886],
  [2.36, 0.873],
  [2.451, 0.858],
];

/** Plan-view taper. Doors carry the full 1,849 mm production width. */
const MAX_HALF: CurveControls = [
  [-2.451, 0.66],
  [-2.42, 0.8],
  [-2.34, 0.856],
  [-2.2, 0.888],
  [-2.0, 0.908],
  [-1.7, 0.92],
  [-1.3, 0.9243],
  [-0.8, 0.9245],
  [0.5, 0.9245],
  [1.1, 0.9215],
  [1.55, 0.9135],
  [1.9, 0.902],
  [2.14, 0.89],
  [2.3, 0.876],
  [2.4, 0.858],
  [2.43, 0.842],
  [2.451, 0.8],
];

/** Shoulder tuck between the widest crease and the belt line. */
const BELT_FACTOR: CurveControls = [
  [-2.451, 0.93],
  [-2.1, 0.945],
  [-1.6, 0.958],
  [-0.6, 0.965],
  [0.8, 0.96],
  [1.6, 0.95],
  [2.1, 0.938],
  [2.451, 0.92],
];

/** Crown plateau width: narrow roof, wide flat bonnet, wide spoiler lip. */
const ROOF_HALF: CurveControls = [
  [-2.451, 0.6],
  [-2.2, 0.612],
  [-1.9, 0.616],
  [-1.5, 0.607],
  [-1.0, 0.6],
  [-0.4, 0.598],
  [0.02, 0.612],
  [0.3, 0.652],
  [0.55, 0.69],
  [0.78, 0.714],
  [1.2, 0.72],
  [1.7, 0.706],
  [2.1, 0.684],
  [2.3, 0.664],
  [2.451, 0.62],
];

/** Rocker line before the wheel-arch cut-outs are applied. */
const BASE_Y: CurveControls = [
  [-2.451, 0.26],
  [-2.36, 0.19],
  [-2.2, 0.16],
  [-1.9, 0.155],
  [1.9, 0.155],
  [2.05, 0.155],
  [2.25, 0.17],
  [2.38, 0.205],
  [2.451, 0.262],
];

function wheelArchCutY(x: number): number {
  let cut = 0;
  for (const axleX of [GARAGE_SUPERB_AXLES_M.rearX, GARAGE_SUPERB_AXLES_M.frontX]) {
    const dx = Math.abs(x - axleX);
    if (dx < GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M) {
      cut = Math.max(
        cut,
        GARAGE_SUPERB_WHEEL_M.centerY +
          Math.sqrt(GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M ** 2 - dx ** 2),
      );
    }
  }
  return cut;
}

/** Full cross-section parameters at any longitudinal position. */
export function garageSuperbSectionAt(x: number): VehicleSection {
  const clamped = Math.max(
    -GARAGE_SUPERB_HALF_LENGTH_M,
    Math.min(GARAGE_SUPERB_HALF_LENGTH_M, x),
  );
  const maxHalf = sampleCurve(MAX_HALF, clamped);
  const beltY = sampleCurve(BELT_Y, clamped);
  const beltHalf = maxHalf * sampleCurve(BELT_FACTOR, clamped);
  const roofY = Math.max(beltY + 0.03, sampleCurve(ROOF_Y, clamped));
  const roofHalf = Math.min(beltHalf * 0.98, sampleCurve(ROOF_HALF, clamped));
  const baseY = Math.max(sampleCurve(BASE_Y, clamped), wheelArchCutY(clamped));
  return { x: clamped, baseY, maxHalf, beltY, beltHalf, roofY, roofHalf };
}

/**
 * Dense sampling positions: extra stations trace the wheel-arch circles so
 * the openings read as real cut arches instead of rectangular notches.
 */
const STATION_XS: readonly number[] = [
  -2.451, -2.42, -2.36, -2.28, -2.16, -2.02, -1.9, -1.8, -1.76, -1.7, -1.6,
  -1.47, -1.34, -1.21, -1.08, -0.98, -0.92, -0.8, -0.7, -0.52, -0.34, -0.16,
  0.06, 0.28, 0.5, 0.7, 0.88, 1.04, 1.12, 1.22, 1.35, 1.501, 1.65, 1.78,
  1.88, 1.94, 2.02, 2.14, 2.26, 2.36, 2.42, 2.451,
];

export const GARAGE_SUPERB_BODY_STATIONS: readonly VehicleSection[] =
  Object.freeze(STATION_XS.map((x) => garageSuperbSectionAt(x)));

/**
 * Day-light opening (side glass band). The front tip sits at the A-pillar
 * foot, the rear tip closes behind the quarter window like the photographs.
 */
export const GARAGE_SUPERB_DLO = Object.freeze({
  frontTipX: 1.02,
  rearTipX: -2.08,
  bottomInsetM: 0.012,
  top: [
    [-2.08, 0.995],
    [-1.95, 1.24],
    [-1.7, 1.376],
    [-1.4, 1.398],
    [-0.8, 1.402],
    [-0.2, 1.396],
    [0.1, 1.372],
    [0.4, 1.2],
    [0.72, 1.02],
    [1.02, 0.884],
  ] as CurveControls,
} as const);

export function garageSuperbDloTopY(x: number): number {
  return sampleCurve(GARAGE_SUPERB_DLO.top, x);
}

export function garageSuperbDloBottomY(x: number): number {
  return garageSuperbSectionAt(x).beltY + GARAGE_SUPERB_DLO.bottomInsetM;
}

/** Outboard Z of the glasshouse surface (plus overlay offset) at height y. */
export function garageSuperbGlassZ(x: number, y: number): number {
  const section = garageSuperbSectionAt(x);
  const t = Math.max(
    0,
    Math.min(1, (y - section.beltY) / (section.roofY - section.beltY)),
  );
  // Piecewise width fraction mirroring the loft ring's glasshouse points so
  // the pane sits a constant few millimetres proud of the painted surface.
  const widthFraction =
    t <= 0.62
      ? t
      : t <= 0.88
        ? 0.62 + ((t - 0.62) / 0.26) * (0.92 - 0.62)
        : 0.92 + ((t - 0.88) / 0.12) * (1 - 0.92);
  return (
    section.beltHalf +
    (section.roofHalf - section.beltHalf) * Math.min(1, widthFraction) +
    0.006
  );
}

/** Outboard Z of the painted body side below the belt line at height y. */
export function garageSuperbBodySideZ(x: number, y: number): number {
  const section = garageSuperbSectionAt(x);
  const t = Math.max(
    0,
    Math.min(1, (y - section.baseY) / (section.beltY - section.baseY)),
  );
  if (t < 0.1) return section.maxHalf * (0.955 + t * 0.4);
  if (t < 0.32) return section.maxHalf * (0.995 + ((t - 0.1) / 0.22) * 0.005);
  if (t < 0.93) return section.maxHalf;
  return (
    section.maxHalf +
    ((t - 0.93) / 0.07) * (section.beltHalf - section.maxHalf)
  );
}

/**
 * Closed cross-section ring. Bottom is flat (dark underbody shows through
 * the arches), sides run nearly vertical to the shoulder crease, then the
 * glasshouse tumbles home toward the narrow crowned roof. Where the belt
 * and crown nearly meet (bonnet, tailgate) the glass segment collapses into
 * a rounded fender shoulder automatically.
 */
export const GARAGE_SUPERB_LOFT_RING_POINT_COUNT = 30;

function stationRing(section: VehicleSection) {
  const { x, baseY, maxHalf, beltY, beltHalf, roofY, roofHalf } = section;
  const sideSpan = beltY - baseY;
  const glassSpan = roofY - beltY;
  const glassZ = (t: number) => beltHalf + (roofHalf - beltHalf) * t;
  const half: readonly (readonly [number, number])[] = [
    [baseY, 0.5 * maxHalf],
    [baseY, 0.82 * maxHalf],
    [baseY + 0.018 * sideSpan, 0.955 * maxHalf],
    [baseY + 0.1 * sideSpan, 0.985 * maxHalf],
    [baseY + 0.32 * sideSpan, 0.998 * maxHalf],
    [baseY + 0.58 * sideSpan, 0.998 * maxHalf],
    [baseY + 0.8 * sideSpan, 0.996 * maxHalf],
    [baseY + 0.93 * sideSpan, maxHalf],
    [beltY, beltHalf],
    [beltY + 0.3 * glassSpan, glassZ(0.3)],
    [beltY + 0.62 * glassSpan, glassZ(0.62)],
    [beltY + 0.88 * glassSpan, glassZ(0.92)],
    [roofY - 0.012, roofHalf],
    [roofY - 0.002, 0.45 * roofHalf],
  ];
  return [
    [x, baseY, 0],
    ...half.map(([y, z]) => [x, y, -z] as const),
    [x, roofY, 0],
    ...[...half].reverse().map(([y, z]) => [x, y, z] as const),
  ] as const;
}

function validateSections(sections: readonly VehicleSection[]) {
  if (sections.length < 2) {
    throw new Error("Vehicle loft needs at least two sections.");
  }
  for (let index = 0; index < sections.length; index += 1) {
    const section = sections[index];
    if (
      ![
        section.x,
        section.baseY,
        section.maxHalf,
        section.beltY,
        section.beltHalf,
        section.roofY,
        section.roofHalf,
      ].every(Number.isFinite)
    ) {
      throw new Error(`Vehicle loft section ${index} must be finite.`);
    }
    if (
      section.maxHalf <= 0 ||
      section.roofHalf <= 0 ||
      section.baseY >= section.beltY ||
      section.beltY >= section.roofY
    ) {
      throw new Error(`Vehicle loft section ${index} has an invalid profile.`);
    }
    if (index > 0 && section.x <= sections[index - 1].x) {
      throw new Error("Vehicle loft section X values must increase.");
    }
  }
}

/** Smooth shell with duplicated, outward-facing caps for crisp fascia normals. */
export function vehicleLoftGeometry(
  sections: readonly VehicleSection[],
): VehicleLoftGeometry {
  validateSections(sections);
  const positions: number[] = [];
  const uvs: number[] = [];
  const minimumX = sections[0].x;
  const span = sections[sections.length - 1].x - minimumX;
  for (const section of sections) {
    const progress = (section.x - minimumX) / span;
    for (const [ringIndex, point] of stationRing(section).entries()) {
      positions.push(...point);
      uvs.push(progress, ringIndex / GARAGE_SUPERB_LOFT_RING_POINT_COUNT);
    }
  }

  const indices: number[] = [];
  for (let station = 0; station < sections.length - 1; station += 1) {
    const start = station * GARAGE_SUPERB_LOFT_RING_POINT_COUNT;
    const nextStart = start + GARAGE_SUPERB_LOFT_RING_POINT_COUNT;
    for (let ring = 0; ring < GARAGE_SUPERB_LOFT_RING_POINT_COUNT; ring += 1) {
      const ringNext = (ring + 1) % GARAGE_SUPERB_LOFT_RING_POINT_COUNT;
      const a = start + ring;
      const b = nextStart + ring;
      const c = nextStart + ringNext;
      const d = start + ringNext;
      indices.push(a, b, c, a, c, d);
    }
  }

  for (const [stationIndex, rear] of [
    [0, true],
    [sections.length - 1, false],
  ] as const) {
    const section = sections[stationIndex];
    const ring = stationRing(section);
    const capStart = positions.length / 3;
    for (const point of ring) {
      positions.push(...point);
      uvs.push(0.5 + point[2] / (section.maxHalf * 2), 0.5);
    }
    const centre = positions.length / 3;
    const centreY = ring.reduce((sum, point) => sum + point[1], 0) / ring.length;
    positions.push(section.x, centreY, 0);
    uvs.push(0.5, 0.5);
    for (
      let ringIndex = 0;
      ringIndex < GARAGE_SUPERB_LOFT_RING_POINT_COUNT;
      ringIndex += 1
    ) {
      const current = capStart + ringIndex;
      const next =
        capStart + ((ringIndex + 1) % GARAGE_SUPERB_LOFT_RING_POINT_COUNT);
      if (rear) indices.push(centre, current, next);
      else indices.push(centre, next, current);
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
