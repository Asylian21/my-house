/**
 * Pure render-boundary conversion for the Y-up Babylon scene.
 *
 * The authoritative model stays in integer millimetres with plan X/Y and
 * elevation Z. Babylon uses X/Z for the ground plane and Y for elevation, so
 * local plan Y must become negative world Z to preserve the floor-plan
 * handedness on screen.
 */
export const MM_TO_M = 0.001;

export const SCENE_CENTER_MM = Object.freeze({ x: 15_200, y: 10_800 });

export const TOP_CAMERA_ALPHA = Math.PI / 2;
export const PARCEL_CAMERA_ALPHA = Math.PI / 2;
export const PARCEL_LABEL_REFERENCE_RADIUS_M = 28;
export const PARCEL_LABEL_MAX_SCALE = 4.75;
export const STREET_CAMERA_ALPHA = 1.42;
export const AXONOMETRIC_CAMERA_ALPHA = Math.PI * 0.72;
// Human-scale hero view from inside the rear hedge. The old preset placed the
// eye 9.6–14.5 m above grade and outside the parcel, so it read as a drone shot
// and looked through the hedge. This angle keeps the pool in the foreground
// while looking back at both legs of the L-shaped garden facade.
export const GARDEN_CAMERA_ALPHA = -2.38;
export const GARDEN_CAMERA_BETA = Math.acos((3.05 - 1.4) / 17.2);

export interface GardenCameraConfig {
  readonly alpha: number;
  readonly beta: number;
  readonly radius: number;
  readonly fov: number;
  readonly target: readonly [number, number, number];
}

export function arcRotateCameraHeightM(config: GardenCameraConfig): number {
  return config.target[1] + config.radius * Math.cos(config.beta);
}

function betaForEyeHeight(
  targetY: number,
  radius: number,
  eyeHeightM: number,
): number {
  const normalized = Math.max(-1, Math.min(1, (eyeHeightM - targetY) / radius));
  return Math.acos(normalized);
}

export function gardenCameraForWidth(widthPx: number): GardenCameraConfig {
  if (widthPx < 600) {
    const target = [1.8, 1.45, -0.95] as const;
    const radius = 18.4;
    return {
      alpha: GARDEN_CAMERA_ALPHA,
      beta: betaForEyeHeight(target[1], radius, 3.2),
      radius,
      fov: 0.9,
      target,
    };
  }
  return {
    alpha: GARDEN_CAMERA_ALPHA,
    beta: GARDEN_CAMERA_BETA,
    radius: 17.2,
    fov: 0.68,
    target: [1.6, 1.4, -0.9],
  };
}

export function streetCameraForWidth(widthPx: number): GardenCameraConfig {
  const mobile = widthPx < 600;
  // Put the eye on the outer edge of the photographed carriageway, not on the
  // green terrain behind it. A deliberately low target tilts the lens through
  // the pavers and kerb so the road occupies the lower third of the frame.
  const radius = mobile ? 23 : 21;
  const target: readonly [number, number, number] = mobile
    ? [0.2, -0.55, -2]
    : [-0.4, -0.65, 0];
  return {
    alpha: STREET_CAMERA_ALPHA,
    beta: betaForEyeHeight(target[1], radius, mobile ? 2.05 : 1.9),
    radius,
    fov: mobile ? 0.92 : 0.78,
    target,
  };
}

/**
 * Cadastral orientation view centred between the subject row 6012/26–28 and
 * the opposite row 6012/23–25. It intentionally frames cadastral context,
 * while the existing top preset remains a tighter architectural floor-plan
 * view of the house.
 */
export function parcelCameraForWidth(widthPx: number): GardenCameraConfig {
  const mobile = widthPx < 600;
  return {
    alpha: PARCEL_CAMERA_ALPHA,
    beta: 0.065,
    radius: mobile ? 132 : 80,
    fov: mobile ? 0.9 : 0.82,
    target: [-29, 0, 22],
  };
}

/**
 * Ground labels grow with an overview camera's distance so their typography
 * keeps a useful screen size on both a desktop canvas and a narrow phone.
 * Close architectural views retain the true-size plaque, while the cap keeps
 * neighbouring parcel numbers from overlapping at the maximum orbit radius.
 */
export function parcelLabelScaleForRadius(radiusM: number): number {
  if (!Number.isFinite(radiusM)) return 1;
  return Math.min(
    PARCEL_LABEL_MAX_SCALE,
    Math.max(1, radiusM / PARCEL_LABEL_REFERENCE_RADIUS_M),
  );
}

export function focusRadiusForBoundingSphere(
  sphereRadiusM: number,
  verticalFovRad: number,
  aspectRatio: number,
  padding = 1.14,
): number {
  const radius = Math.max(0.01, sphereRadiusM);
  const verticalFov = Math.max(0.1, Math.min(Math.PI - 0.1, verticalFovRad));
  const aspect = Math.max(0.2, aspectRatio);
  const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * aspect);
  const limitingFov = Math.min(verticalFov, horizontalFov);
  const fitted =
    (radius / Math.max(0.08, Math.sin(limitingFov / 2))) *
    Math.max(1, padding);
  return Math.max(4.5, Math.min(64, fitted));
}

export interface PlanPointMm {
  readonly x: number;
  readonly y: number;
}

export function sceneXM(mm: number): number {
  return (mm - SCENE_CENTER_MM.x) * MM_TO_M;
}

export function sceneZM(mm: number): number {
  return (SCENE_CENTER_MM.y - mm) * MM_TO_M;
}

export function sceneDeltaForPlanSegment(
  start: PlanPointMm,
  end: PlanPointMm,
): { readonly dx: number; readonly dz: number } {
  return {
    dx: (end.x - start.x) * MM_TO_M,
    dz: (start.y - end.y) * MM_TO_M,
  };
}

export function sceneYawForPlanSegment(
  start: PlanPointMm,
  end: PlanPointMm,
): number {
  const { dx, dz } = sceneDeltaForPlanSegment(start, end);
  return -Math.atan2(dz, dx);
}
