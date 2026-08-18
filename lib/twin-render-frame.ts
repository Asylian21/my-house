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
export const STREET_CAMERA_ALPHA = Math.PI / 2;
export const AXONOMETRIC_CAMERA_ALPHA = Math.PI * 0.72;
// Hero garden view framed on the covered gable porch, matching the approved
// reference photograph: camera to the north-west of the house, slightly
// elevated, looking back at the garden facade and the porch corner.
export const GARDEN_CAMERA_ALPHA = -2.03;
export const GARDEN_CAMERA_BETA = 1.3;

export interface GardenCameraConfig {
  readonly alpha: number;
  readonly beta: number;
  readonly radius: number;
  readonly fov: number;
  readonly target: readonly [number, number, number];
}

export function gardenCameraForWidth(widthPx: number): GardenCameraConfig {
  if (widthPx < 600) {
    return {
      alpha: GARDEN_CAMERA_ALPHA,
      beta: 1.22,
      radius: 38,
      fov: 0.8,
      target: [2.8, 1.4, -3.2],
    };
  }
  return {
    alpha: GARDEN_CAMERA_ALPHA,
    beta: GARDEN_CAMERA_BETA,
    radius: 30,
    fov: 0.55,
    target: [3.2, 1.6, -3],
  };
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
