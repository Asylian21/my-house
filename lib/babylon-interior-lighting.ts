import { RectAreaLight } from "@babylonjs/core/Lights/rectAreaLight";
import { Color3 } from "@babylonjs/core/Maths/math.color";
import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import { TransformNode } from "@babylonjs/core/Meshes/transformNode";
import type { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import type { Scene } from "@babylonjs/core/scene";
import { INTERIOR_LIGHTING, kitchenLightLuminance, kitchenTaskLightMultiplier, type KitchenLightFixture } from "./twin-interior-lighting";
import { sceneXM, sceneZM, MM_TO_M } from "./twin-render-frame";

type FixtureState = { fixture: KitchenLightFixture; light?: RectAreaLight; emitters: PBRMaterial[] };
const lights = new WeakMap<Scene, { factor: number; receiversDirty: boolean; fixtures: FixtureState[] }>();

/** Visual exposure matching for this browser scene, not a lumen/unit conversion.
 * Babylon 9.21 sends area intensity directly to LTC; the existing scene's sun
 * and exposure are artistic, so raw cd/m² would clip every kitchen surface.
 * Authored lumens and the native-export photometric contract remain unchanged.
 */
export const KITCHEN_BROWSER_LIGHT_PREVIEW_GAIN = 0.001;

export function createKitchenTaskLight(scene: Scene): void {
  if (lights.has(scene)) throw new Error("Kitchen task light already exists");
  const state = { factor: 0, receiversDirty: false, fixtures: INTERIOR_LIGHTING.fixtures.map(fixture => ({ fixture, emitters: [] } as FixtureState)) };
  lights.set(scene, state);
  const added = scene.onNewMeshAddedObservable.add(() => { state.receiversDirty = true; });
  const removed = scene.onMeshRemovedObservable.add(() => { state.receiversDirty = true; });
  const beforeRender = scene.onBeforeRenderObservable.add(() => {
    if (!state.receiversDirty) return;
    state.receiversDirty = false;
    for (const fixture of state.fixtures) if (fixture.light) fixture.light.includedOnlyMeshes = scene.meshes.filter(kitchenLightReceiver);
  });
  scene.onDisposeObservable.addOnce(() => {
    scene.onNewMeshAddedObservable.remove(added);
    scene.onMeshRemovedObservable.remove(removed);
    scene.onBeforeRenderObservable.remove(beforeRender);
    lights.delete(scene);
  });
}

/** Area-light range is not a shader cutoff in Babylon 9.21 and LTC has no
 * shadow caster. Restrict this local task-light preview to its own fitout and
 * separate living-room floors; never illuminate a merged whole-house batch.
 */
function kitchenLightReceiver(mesh: AbstractMesh): boolean {
  const sourceName = typeof mesh.metadata?.sourceName === "string" ? mesh.metadata.sourceName as string : mesh.name;
  if (sourceName.startsWith("KITCHEN-RUN · ")) return true;
  if (!sourceName.startsWith("1.03 ") || !sourceName.includes(" · podlaha ")) return false;
  mesh.computeWorldMatrix(true);
  const bounds = mesh.getBoundingInfo().boundingBox;
  return bounds.minimumWorld.x >= sceneXM(21543) - 0.001 && bounds.maximumWorld.x <= sceneXM(27541) + 0.001
    && bounds.minimumWorld.z >= sceneZM(19533) - 0.001 && bounds.maximumWorld.z <= sceneZM(11012) + 0.001;
}

/** Register only a dedicated diffuser material: shared room finishes stay untouched. */
export function registerKitchenLightEmitter(scene: Scene, fixtureId: string, material: PBRMaterial): void {
  const state = lights.get(scene);
  const fixture = state?.fixtures.find(item => item.fixture.id === fixtureId);
  if (!state || !fixture) throw new Error(`Kitchen light is not initialized: ${fixtureId}`);
  if (!fixture.emitters.includes(material)) fixture.emitters.push(material);
  updateEmitter(material, state.factor);
}

function updateEmitter(material: PBRMaterial, factor: number): void {
  // Visible opal surface; actual worktop illumination comes from the rect light.
  // Kept below the scene's bloom threshold to avoid a distracting white streak.
  material.emissiveColor.set(1, 0.72, 0.4).scaleInPlace(1.2 * factor);
}

function makeLight(scene: Scene, f: KitchenLightFixture): RectAreaLight {
  const p = f.light.positionPlanMm;
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
  light.renderPriority = 20;
  light.includedOnlyMeshes = scene.meshes.filter(kitchenLightReceiver);
  light.metadata = { interiorLightId: f.id, photometry: "Authored LTC browser preview; not photometrically calibrated",
    browserPreviewGain: KITCHEN_BROWSER_LIGHT_PREVIEW_GAIN,
    receivers: "kitchen fitout and separate living-room floors",
    shadowCastingSupported: false, sourceLumens: f.light.lumens, temperatureK: f.light.temperatureK };
  return light;
}

/** The scene owns the switch/dimming factor. This does not change sky or solar lighting. */
export function setKitchenTaskLightingNightAlpha(scene: Scene, nightAlpha: number): void {
  const factor = kitchenTaskLightMultiplier(nightAlpha);
  const state = lights.get(scene);
  if (!state) throw new Error("Kitchen task light is not initialized");
  state.factor = factor;
  // No LTC download or render-light allocation in the existing day-only preview/export.
  for (const fixture of state.fixtures) {
    for (const emitter of fixture.emitters) updateEmitter(emitter, factor);
    if (factor === 0 && !fixture.light) continue;
    const light = fixture.light ?? (fixture.light = makeLight(scene, fixture.fixture));
    light.intensity = kitchenLightLuminance(fixture.fixture) * KITCHEN_BROWSER_LIGHT_PREVIEW_GAIN * factor;
    light.setEnabled(factor > 0);
  }
}
