import { KITCHEN_RUN } from "./twin-interior";

// One existing modeled strip. Photometry is authored, not a measured product.
const k = KITCHEN_RUN;
const centerX = (k.fridgeUnitRectMm.x1 + k.rectMm.x1) / 2;
const centerY = k.rectMm.y0 + k.upperCabinets.depthMm - 30;
const widthMm = k.rectMm.x1 - k.fridgeUnitRectMm.x1 - 40;
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
export const INTERIOR_LIGHTING = Object.freeze({
  schemaVersion: 1,
  provenance: "AUTHORED_VISUALIZATION_PROPOSAL",
  coordinateSystem: "PLAN_XY_ELEVATION_Z_MM",
  photometricConvention: "ONE_SIDED_RECT_LUMENS",
  vendorPhotometryAvailable: false,
  iesAvailable: false,
  fixtures: [KITCHEN_TASK_LIGHT],
} as const);

export function kitchenTaskLightMultiplier(nightAlpha: number): number {
  if (!Number.isFinite(nightAlpha) || nightAlpha < 0 || nightAlpha > 1)
    throw new Error("Kitchen night alpha must be within 0..1");
  const { dayMultiplier, nightMultiplier } = KITCHEN_TASK_LIGHT.light;
  return dayMultiplier + (nightMultiplier - dayMultiplier) * nightAlpha;
}

/** Explicit Lambertian approximation for Babylon LTC preview, not cross-renderer calibration. */
export function kitchenTaskLightLuminance(): number {
  const l = KITCHEN_TASK_LIGHT.light;
  return l.lumens / (Math.PI * (l.sourceWidthMm / 1000) * (l.sourceHeightMm / 1000));
}
