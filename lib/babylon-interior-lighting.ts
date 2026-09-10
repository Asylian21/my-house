import { RectAreaLight } from "@babylonjs/core/Lights/rectAreaLight";
import { Color3 } from "@babylonjs/core/Maths/math.color";
import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import { TransformNode } from "@babylonjs/core/Meshes/transformNode";
import type { Scene } from "@babylonjs/core/scene";
import { KITCHEN_TASK_LIGHT, kitchenTaskLightLuminance, kitchenTaskLightMultiplier } from "./twin-interior-lighting";
import { sceneXM, sceneZM, MM_TO_M } from "./twin-render-frame";

const lights = new WeakMap<Scene, { light?: RectAreaLight }>();

export function createKitchenTaskLight(scene: Scene): void {
  if (lights.has(scene)) throw new Error("Kitchen task light already exists");
  lights.set(scene, {});
  scene.onDisposeObservable.addOnce(() => lights.delete(scene));
}

function makeLight(scene: Scene): RectAreaLight {
  const f = KITCHEN_TASK_LIGHT, p = f.light.positionPlanMm;
  const orientation = new TransformNode(`${f.id} · source orientation`, scene);
  orientation.position.set(sceneXM(p[0]), p[2] * MM_TO_M, sceneZM(p[1]));
  // Babylon rectangle emits along local -Z; this maps it to world -Y (down).
  // Its width remains world +X and its height maps to world -Z (plan +Y).
  orientation.rotation.x = -Math.PI / 2;
  const light = new RectAreaLight(f.id, Vector3.Zero(),
    f.light.sourceWidthMm * MM_TO_M, f.light.sourceHeightMm * MM_TO_M, scene);
  light.parent = orientation;
  // Linear BT.709, Y=1 approximation at 3000 K (UE Planckian locus formula).
  // The current Babylon area-light implementation applies intensity directly;
  // INTENSITYMODE_LUMINOUSPOWER would not perform a lumen conversion.
  light.diffuse = new Color3(1.769649436, 0.844723160, 0.270703419);
  light.specular = light.diffuse.clone();
  light.range = f.light.attenuationRadiusMm * MM_TO_M;
  light.metadata = { interiorLightId: f.id, photometry: "Lambertian LTC approximation",
    shadowCastingSupported: false, sourceLumens: f.light.lumens, temperatureK: f.light.temperatureK };
  return light;
}

/** A time-of-day owner calls this with its existing interpolated factor; no independent clock. */
export function setKitchenTaskLightingNightAlpha(scene: Scene, nightAlpha: number): void {
  const factor = kitchenTaskLightMultiplier(nightAlpha);
  const state = lights.get(scene);
  if (!state) throw new Error("Kitchen task light is not initialized");
  // No LTC download or render-light allocation in the existing day-only preview/export.
  if (factor === 0 && !state.light) return;
  const light = state.light ?? (state.light = makeLight(scene));
  light.intensity = kitchenTaskLightLuminance() * factor;
  light.setEnabled(factor > 0);
}
