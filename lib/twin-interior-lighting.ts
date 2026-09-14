import { ceilingElevationMm, INTERIOR_ROOMS, KITCHEN_DESIGN, KITCHEN_RUN } from "./twin-interior";

// The wall task strip and island line share the kitchen's authored geometry.
// Photometry is a visualization proposal, not a measured luminaire or lux study.
const k = KITCHEN_RUN;
const startX = KITCHEN_DESIGN.backWorktopRectMm.x0;
const centerX = (startX + k.rectMm.x1) / 2;
// Forward of the hood's filter opening, with a 5 mm lip shielding the strip.
const centerY = k.rectMm.y0 + k.upperCabinets.depthMm - 15;
const widthMm = k.rectMm.x1 - startX - 40;
const heightMm = 20;
const bodyThicknessMm = 12;
const emitterClearanceMm = 2;
export const KITCHEN_TASK_LIGHT = Object.freeze({
  id: "INT-KITCHEN-TASK-01",
  parentSourceId: k.id,
  designSourceId: k.designSourceId,
  kind: "RECT_UNDERCABINET",
  geometry: {
    sourceName: `${k.id} · LED lišta pod skrinkami`,
    bodyCenterPlanMm: [centerX, centerY, k.upperCabinets.bottomMm - bodyThicknessMm / 2],
    dimensionsMm: [widthMm, heightMm, bodyThicknessMm],
  },
  light: {
    positionPlanMm: [centerX, centerY, k.upperCabinets.bottomMm - bodyThicknessMm - emitterClearanceMm],
    directionPlan: [0, 0, -1],
    widthAxisPlan: [1, 0, 0],
    sourceWidthMm: widthMm,
    sourceHeightMm: heightMm,
    lumens: widthMm * 300 / 1000,
    temperatureK: 3000,
    attenuationRadiusMm: 2500,
    emitterClearanceMm,
    castsShadows: true,
    dayMultiplier: 0,
    nightMultiplier: 1,
  },
} as const);

const livingRoom = INTERIOR_ROOMS.find(room => room.id === "ROOM-1-03")!;
const pendantCenterX = 24701;
const pendantCenterY = 13340;
const pendantBottomMm = 2200;
const pendantBodyHeightMm = 25;
export const KITCHEN_ISLAND_LIGHT = Object.freeze({
  id: "INT-KITCHEN-ISLAND-01",
  parentSourceId: k.id,
  designSourceId: KITCHEN_DESIGN.id,
  kind: "RECT_PENDANT",
  geometry: {
    sourceName: `${k.id} · ISLAND-LIGHT · lineárne svietidlo nad ostrovčekom`,
    bodyCenterPlanMm: [pendantCenterX, pendantCenterY, pendantBottomMm + pendantBodyHeightMm / 2],
    dimensionsMm: [1800, 25, pendantBodyHeightMm],
  },
  suspension: [-600, 600].map(offset => {
    const xMm = pendantCenterX + offset;
    return {
      xMm, yMm: pendantCenterY, cableDiameterMm: 3,
      bottomMm: pendantBottomMm + pendantBodyHeightMm,
      ceilingMm: ceilingElevationMm(livingRoom, xMm),
      mountWidthMm: 30, mountDepthMm: 30, mountThicknessMm: 12,
      // Two slope samples let the tiny ceiling rose sit flush on the vault.
      ceilingLeftMm: ceilingElevationMm(livingRoom, xMm - 15),
      ceilingRightMm: ceilingElevationMm(livingRoom, xMm + 15),
    };
  }),
  light: {
    positionPlanMm: [pendantCenterX, pendantCenterY, pendantBottomMm - emitterClearanceMm],
    directionPlan: [0, 0, -1], widthAxisPlan: [1, 0, 0],
    sourceWidthMm: 1770, sourceHeightMm: 12,
    lumens: 1800, temperatureK: 3000, attenuationRadiusMm: 4000,
    emitterClearanceMm, castsShadows: true, dayMultiplier: 0, nightMultiplier: 1,
  },
} as const);

export const INTERIOR_LIGHTING = Object.freeze({
  schemaVersion: 1,
  provenance: "AUTHORED_VISUALIZATION_PROPOSAL",
  coordinateSystem: "PLAN_XY_ELEVATION_Z_MM",
  photometricConvention: "ONE_SIDED_RECT_LUMENS",
  vendorPhotometryAvailable: false,
  iesAvailable: false,
  fixtures: [KITCHEN_TASK_LIGHT, KITCHEN_ISLAND_LIGHT],
} as const);
export type KitchenLightFixture = typeof INTERIOR_LIGHTING.fixtures[number];

export function kitchenTaskLightMultiplier(nightAlpha: number): number {
  if (!Number.isFinite(nightAlpha) || nightAlpha < 0 || nightAlpha > 1)
    throw new Error("Kitchen night alpha must be within 0..1");
  const { dayMultiplier, nightMultiplier } = KITCHEN_TASK_LIGHT.light;
  return dayMultiplier + (nightMultiplier - dayMultiplier) * nightAlpha;
}

/** Explicit Lambertian approximation for Babylon LTC preview, not cross-renderer calibration. */
export function kitchenTaskLightLuminance(): number {
  return kitchenLightLuminance(KITCHEN_TASK_LIGHT);
}

export function kitchenLightLuminance(fixture: KitchenLightFixture): number {
  const l = fixture.light;
  return l.lumens / (Math.PI * (l.sourceWidthMm / 1000) * (l.sourceHeightMm / 1000));
}
