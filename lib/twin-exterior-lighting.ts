import { HOUSE } from './twin-active-house';
import { GARDEN_POOL } from './twin-site';

export type LightingPointMm = readonly [number, number, number];

/** Existing illustrative bodies, extracted from the Babylon builder without relocation. */
export const EXTERIOR_LIGHTING_SOURCE_GEOMETRY = {
  terrace: {
    xPositionsMm: [22600, 26400],
    baseElevationMm: 3850,
    gableOffsetMm: 20,
    bodyOffsetFromGableMm: 55,
    diameterMm: 70,
    lengthMm: 170,
    tessellation: 24,
    bracket: { widthMm: 24, depthMm: 48, heightMm: 30, offsetFromGableMm: 24, baseOffsetMm: 70 },
  },
  pool: {
    offsetsFromCenterXmm: [-1150, 0, 1150],
    waterSurfaceElevationMm: -12,
    centerBelowWaterMm: 640,
    insetFromInnerWallMm: 8,
    diameterMm: 135,
    lengthMm: 22,
    tessellation: 24,
  },
} as const;

export interface ExteriorFixture {
  readonly id: string;
  readonly parentSourceId: string;
  readonly kind: 'terrace-wall-downlight' | 'pool-wall-underwater-inward';
  readonly geometry: {
    readonly sourceName: string;
    readonly bodyCenterPlanMm: LightingPointMm;
    readonly axisPlan: LightingPointMm;
    readonly diameterMm: number;
    readonly lengthMm: number;
    readonly tessellation: number;
    readonly capCenterPlanMm: LightingPointMm;
    readonly bracket?: {
      readonly name: string;
      readonly centerPlanMm: LightingPointMm;
      readonly sizePlanMm: LightingPointMm;
    };
  };
  readonly light: {
    readonly positionPlanMm: LightingPointMm;
    readonly directionPlan: LightingPointMm;
    /** UE cone-solid-angle lumen input, not measured integrated fixture output. */
    readonly nominalConeLumens: number;
    readonly peakCandela: number;
    readonly temperatureK: number;
    readonly innerConeHalfAngleDeg: number;
    readonly outerConeHalfAngleDeg: number;
    readonly sourceRadiusMm: number;
    readonly attenuationRadiusMm: number;
    readonly emitterProxyOffsetMm: number;
    readonly castsShadows: true;
    readonly dayMultiplier: 0;
    readonly nightMultiplier: 1;
  };
}

function lightAtCap(
  cap: LightingPointMm, direction: LightingPointMm, lumens: number, temperatureK: number,
  inner: number, outer: number, radiusMm: number, rangeMm: number,
): ExteriorFixture['light'] {
  // A finite source touching/intersecting its own cap can cause shadow artifacts.
  // This proxy offset is an authored rendering approximation; the body stays fixed.
  const offset = radiusMm + 2;
  return {
    positionPlanMm: [cap[0] + direction[0] * offset, cap[1] + direction[1] * offset, cap[2] + direction[2] * offset],
    directionPlan: direction,
    nominalConeLumens: lumens,
    peakCandela: lumens / (2 * Math.PI * (1 - Math.cos(outer * Math.PI / 180))),
    temperatureK,
    innerConeHalfAngleDeg: inner,
    outerConeHalfAngleDeg: outer,
    sourceRadiusMm: radiusMm,
    attenuationRadiusMm: rangeMm,
    emitterProxyOffsetMm: offset,
    castsShadows: true,
    dayMultiplier: 0,
    nightMultiplier: 1,
  };
}

const terrace = EXTERIOR_LIGHTING_SOURCE_GEOMETRY.terrace;
const gableYmm = HOUSE.porches.wingEnd.gablePlaneYmm + terrace.gableOffsetMm;
const terraceFixtures: readonly ExteriorFixture[] = terrace.xPositionsMm.map((x, i) => {
  const y = gableYmm + terrace.bodyOffsetFromGableMm;
  const cap: LightingPointMm = [x, y, terrace.baseElevationMm];
  return {
    id: `EXT-TERRACE-WALL-${String(i + 1).padStart(2, '0')}`,
    parentSourceId: HOUSE.porches.wingEnd.id,
    kind: 'terrace-wall-downlight',
    geometry: {
      sourceName: `Nástenné svietidlo štítu ${i + 1} · ilustračný koncept`,
      bodyCenterPlanMm: [x, y, terrace.baseElevationMm + terrace.lengthMm / 2],
      axisPlan: [0, 0, 1],
      diameterMm: terrace.diameterMm,
      lengthMm: terrace.lengthMm,
      tessellation: terrace.tessellation,
      capCenterPlanMm: cap,
      bracket: {
        name: `Nástenné svietidlo štítu ${i + 1} · konzola`,
        centerPlanMm: [x, gableYmm + terrace.bracket.offsetFromGableMm,
          terrace.baseElevationMm + terrace.bracket.baseOffsetMm + terrace.bracket.heightMm / 2],
        sizePlanMm: [terrace.bracket.widthMm, terrace.bracket.depthMm, terrace.bracket.heightMm],
      },
    },
    light: lightAtCap(cap, [0, 0, -1], 300, 2700, 25, 40, 20, 6000),
  };
});

const pool = EXTERIOR_LIGHTING_SOURCE_GEOMETRY.pool;
const poolFixtures: readonly ExteriorFixture[] = pool.offsetsFromCenterXmm.map((offset, i) => {
  const body: LightingPointMm = [
    GARDEN_POOL.centerMm.x + offset,
    GARDEN_POOL.centerMm.y + GARDEN_POOL.waterWidthMm / 2 - pool.insetFromInnerWallMm,
    pool.waterSurfaceElevationMm - pool.centerBelowWaterMm,
  ];
  // Babylon's existing cylinder +Y axis rotated +PI/2 around X becomes plan -Y.
  const cap: LightingPointMm = [body[0], body[1] - pool.lengthMm / 2, body[2]];
  return {
    id: `EXT-POOL-WALL-${String(i + 1).padStart(2, '0')}`,
    parentSourceId: GARDEN_POOL.id,
    kind: 'pool-wall-underwater-inward',
    geometry: {
      sourceName: `${GARDEN_POOL.label} · diskrétne zapustené podvodné svetlo ${i + 1}`,
      bodyCenterPlanMm: body,
      axisPlan: [0, -1, 0],
      diameterMm: pool.diameterMm,
      lengthMm: pool.lengthMm,
      tessellation: pool.tessellation,
      capCenterPlanMm: cap,
    },
    light: lightAtCap(cap, [0, -1, 0], 400, 4000, 35, 55, 55, 4500),
  };
});

/** Pure serializable source contract; renderer adapters convert coordinates once. */
export const EXTERIOR_LIGHTING = {
  schemaVersion: 1,
  provenance: 'AUTHORED_VISUALIZATION_PROPOSAL',
  coordinateSystem: 'PLAN_XY_ELEVATION_Z_MM',
  photometricConvention: 'UE_CONE_SOLID_ANGLE_LUMENS',
  vendorPhotometryAvailable: false,
  iesProfileAvailable: false,
  permitOrAsBuiltClaim: false,
  fixtures: [...terraceFixtures, ...poolFixtures],
} as const;
