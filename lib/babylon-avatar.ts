import type { AnimationGroup } from "@babylonjs/core/Animations/animationGroup";
import { ArcRotateCamera } from "@babylonjs/core/Cameras/arcRotateCamera";
import { ImportMeshAsync } from "@babylonjs/core/Loading/sceneLoader";
import type { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { CreateBox } from "@babylonjs/core/Meshes/Builders/boxBuilder.pure";
import type { Mesh } from "@babylonjs/core/Meshes/mesh";
import { TransformNode } from "@babylonjs/core/Meshes/transformNode";
import type { Scene } from "@babylonjs/core/scene";
import "@babylonjs/loaders/glTF";

import {
  WALK_CAMERA,
  WALK_COLLISION_ELLIPSOID_M,
  WALK_SPEED_MPS,
  integrateAvatarVelocity,
  type FlightCommand,
} from "./twin-viewport-contract";

export const AVATAR_URL = "/assets/avatar/avatar.glb";

export interface AvatarPose {
  readonly x: number;
  readonly z: number;
  readonly yaw: number;
}

/**
 * Third-person walker: a rigged, textured human (Mixamo "Michelle" with the
 * Idle/Walk/Run locomotion clips retargeted onto her skeleton) driven by a
 * kinematic controller with acceleration, turning inertia and wall
 * collisions, and followed by an orbiting chase camera that cannot pass
 * through walls.
 */
export class AvatarController {
  readonly root: TransformNode;
  readonly camera: ArcRotateCamera;
  private readonly collider: Mesh;
  private readonly velocity = new Vector3(0, 0, 0);
  private yaw = 0;
  private readonly cameraTarget = new Vector3(0, WALK_CAMERA.targetHeightM, 0);
  private meshes: AbstractMesh[] = [];
  private idle: AnimationGroup | null = null;
  private walk: AnimationGroup | null = null;
  private run: AnimationGroup | null = null;
  private loaded = false;
  private loadPromise: Promise<void> | null = null;
  private firstPerson = false;
  private sinceUserOrbitS = 10;

  constructor(
    private readonly scene: Scene,
    private readonly onMeshLoaded: (mesh: AbstractMesh) => void,
  ) {
    this.root = new TransformNode("Avatar · chodec", scene);
    this.collider = CreateBox(
      "Avatar · kolízny elipsoid",
      { width: 0.1, height: 0.1, depth: 0.1 },
      scene,
    );
    this.collider.isVisible = false;
    this.collider.isPickable = false;
    this.collider.checkCollisions = false;
    // Whole-body capsule: 0.05 m above the floor up to 1.65 m, so door heads
    // (2 100) clear and low furniture still blocks.
    this.collider.ellipsoid = new Vector3(
      WALK_COLLISION_ELLIPSOID_M.x + 0.02,
      0.8,
      WALK_COLLISION_ELLIPSOID_M.z + 0.02,
    );
    this.collider.ellipsoidOffset = new Vector3(0, 0.85, 0);

    this.camera = new ArcRotateCamera(
      "avatar-camera",
      -Math.PI / 2,
      WALK_CAMERA.betaRad,
      WALK_CAMERA.radiusM,
      this.cameraTarget.clone(),
      scene,
    );
    this.camera.lowerRadiusLimit = WALK_CAMERA.minRadiusM;
    this.camera.upperRadiusLimit = WALK_CAMERA.maxRadiusM;
    this.camera.lowerBetaLimit = 0.35;
    this.camera.upperBetaLimit = 1.52;
    this.camera.minZ = 0.08;
    this.camera.maxZ = 220;
    this.camera.fov = 0.95;
    this.camera.inertia = 0.82;
    this.camera.angularSensibilityX = 620;
    this.camera.angularSensibilityY = 620;
    this.camera.panningSensibility = 0;
    this.camera.inputs.removeByType("ArcRotateCameraMouseWheelInput");
    this.camera.inputs.removeByType("ArcRotateCameraKeyboardMoveInput");
    this.camera.checkCollisions = true;
    this.camera.collisionRadius = new Vector3(0.22, 0.22, 0.22);
    this.camera.detachControl();
  }

  get isLoaded() {
    return this.loaded;
  }

  get isFirstPerson() {
    return this.firstPerson;
  }

  /** Loads the glTF once; safe to call repeatedly. */
  load(): Promise<void> {
    if (!this.loadPromise) {
      this.loadPromise = ImportMeshAsync(AVATAR_URL, this.scene)
        .then((result) => {
          const glbRoot = result.meshes.find((mesh) => mesh.name === "__root__") ?? result.meshes[0];
          glbRoot.parent = this.root;
          // Mixamo rigs face +z in glTF and this right-handed scene keeps
          // that, which matches the controller's yaw = 0 heading (0, 0, 1).
          glbRoot.rotation = new Vector3(0, 0, 0);
          glbRoot.rotationQuaternion = null;
          this.meshes = result.meshes.filter((mesh) => mesh.getTotalVertices() > 0);
          for (const mesh of this.meshes) {
            mesh.isPickable = false;
            mesh.receiveShadows = true;
            const material = mesh.material as PBRMaterial | null;
            if (material && "environmentIntensity" in material) {
              material.environmentIntensity = 0.9;
            }
            this.onMeshLoaded(mesh);
          }
          const byName = (name: string) =>
            result.animationGroups.find((group) => group.name === name) ?? null;
          this.idle = byName("Idle");
          this.walk = byName("Walk");
          this.run = byName("Run");
          for (const group of result.animationGroups) {
            group.stop();
            group.reset();
            group.loopAnimation = true;
          }
          for (const group of [this.idle, this.walk, this.run]) {
            if (!group) continue;
            group.play(true);
            group.weight = group === this.idle ? 1 : 0;
          }
          this.loaded = true;
          this.setVisible(!this.firstPerson);
        })
        .catch((error: unknown) => {
          this.loadPromise = null;
          throw error;
        });
    }
    return this.loadPromise;
  }

  setFirstPerson(firstPerson: boolean) {
    this.firstPerson = firstPerson;
    this.setVisible(!firstPerson);
  }

  private setVisible(visible: boolean) {
    for (const mesh of this.meshes) mesh.setEnabled(visible);
  }

  /** Places the walker and turns the chase camera behind it. */
  place(xM: number, zM: number, yawRad: number) {
    this.collider.position.set(xM, 0, zM);
    this.root.position.set(xM, 0, zM);
    this.yaw = yawRad;
    this.root.rotation.set(0, yawRad, 0);
    this.velocity.setAll(0);
    this.cameraTarget.set(xM, WALK_CAMERA.targetHeightM, zM);
    this.camera.target.copyFrom(this.cameraTarget);
    // Camera behind the walker: the avatar looks along (sin yaw, 0, cos yaw)
    // in this right-handed scene; alpha measures from +x toward +z.
    this.camera.alpha = Math.atan2(-Math.cos(yawRad), -Math.sin(yawRad));
    this.camera.beta = WALK_CAMERA.betaRad;
    this.camera.radius = WALK_CAMERA.radiusM;
    this.camera.inertialAlphaOffset = 0;
    this.camera.inertialBetaOffset = 0;
    this.camera.inertialRadiusOffset = 0;
    // Resolve the spherical pose into a position before the collider sees
    // it; otherwise the first frame collides from the stale old position and
    // flings the camera across the house.
    this.camera.checkCollisions = false;
    this.camera.getViewMatrix();
    this.camera.checkCollisions = true;
  }

  get pose(): AvatarPose {
    return { x: this.collider.position.x, z: this.collider.position.z, yaw: this.yaw };
  }

  /** Eye position for the first-person view. */
  get eyePosition() {
    return new Vector3(this.collider.position.x, 1.62, this.collider.position.z);
  }

  /** Unit forward of the chase camera on the ground plane. */
  private cameraForward(): { x: number; z: number } {
    const dx = this.camera.target.x - this.camera.position.x;
    const dz = this.camera.target.z - this.camera.position.z;
    const length = Math.hypot(dx, dz);
    if (length < 1e-4) return { x: Math.sin(this.yaw), z: Math.cos(this.yaw) };
    return { x: dx / length, z: dz / length };
  }

  /** Advances the walker by one frame. Returns the planar speed (m/s). */
  update(
    deltaMs: number,
    commands: ReadonlySet<FlightCommand>,
    modifiers: { boost: boolean; precision: boolean },
    headingOverride?: { x: number; z: number },
  ) {
    const forward = headingOverride ?? this.cameraForward();
    const next = integrateAvatarVelocity({
      velocity: { x: this.velocity.x, z: this.velocity.z },
      forward,
      commands,
      deltaMs,
      boost: modifiers.boost,
      precision: modifiers.precision,
    });
    this.velocity.set(next.x, 0, next.z);
    const seconds = Math.min(50, Math.max(0, deltaMs)) / 1000;
    const step = new Vector3(next.x * seconds, 0, next.z * seconds);
    if (step.lengthSquared() > 1e-12) {
      this.collider.moveWithCollisions(step);
      this.collider.position.y = 0;
    }
    this.root.position.copyFrom(this.collider.position);

    const speed = Math.hypot(next.x, next.z);
    if (speed > 0.08) {
      const targetYaw = Math.atan2(next.x, next.z);
      let delta = targetYaw - this.yaw;
      delta = Math.atan2(Math.sin(delta), Math.cos(delta));
      const turn = 1 - Math.exp(-seconds / WALK_CAMERA.turnTauS);
      this.yaw += delta * turn;
    }
    this.root.rotation.set(0, this.yaw, 0);

    // Chase camera: the target glides after the head with a short lag, and
    // when the player is not dragging it drifts back behind the walker while
    // walking — GTA-style, but without any camera drift while standing.
    const userOrbiting =
      Math.abs(this.camera.inertialAlphaOffset) + Math.abs(this.camera.inertialBetaOffset) > 1e-5;
    this.sinceUserOrbitS = userOrbiting ? 0 : this.sinceUserOrbitS + seconds;
    if (!userOrbiting && speed > 0.4 && this.sinceUserOrbitS > WALK_CAMERA.recenterDelayS) {
      const behind = Math.atan2(-Math.cos(this.yaw), -Math.sin(this.yaw));
      let delta = behind - this.camera.alpha;
      delta = Math.atan2(Math.sin(delta), Math.cos(delta));
      this.camera.alpha += delta * (1 - Math.exp(-seconds / WALK_CAMERA.recenterTauS));
    }
    const follow = 1 - Math.exp(-seconds / WALK_CAMERA.followTauS);
    this.cameraTarget.set(
      this.cameraTarget.x + (this.collider.position.x - this.cameraTarget.x) * follow,
      WALK_CAMERA.targetHeightM,
      this.cameraTarget.z + (this.collider.position.z - this.cameraTarget.z) * follow,
    );
    this.camera.target.copyFrom(this.cameraTarget);

    this.blendAnimations(speed);
    return speed;
  }

  private blendAnimations(speed: number) {
    if (!this.idle || !this.walk || !this.run) return;
    const idleWeight = 1 - Math.min(1, speed / 0.55);
    const runMix = Math.min(
      1,
      Math.max(0, (speed - WALK_SPEED_MPS.normal) / (WALK_SPEED_MPS.boost - WALK_SPEED_MPS.normal)),
    );
    const moving = 1 - idleWeight;
    this.idle.weight = idleWeight;
    this.walk.weight = moving * (1 - runMix);
    this.run.weight = moving * runMix;
    // Keep the feet planted: the clips were authored at ~1.4 m/s and ~3.3 m/s.
    this.walk.speedRatio = Math.max(0.55, Math.min(1.6, speed / 1.4));
    this.run.speedRatio = Math.max(0.7, Math.min(1.5, speed / 3.3));
  }

  /** Exponential zoom of the chase camera from a normalised wheel delta. */
  zoom(pixels: number) {
    const next = this.camera.radius * Math.exp(pixels * 0.0032);
    this.camera.radius = Math.max(
      WALK_CAMERA.minRadiusM,
      Math.min(WALK_CAMERA.maxRadiusM, next),
    );
  }

  dispose() {
    for (const group of [this.idle, this.walk, this.run]) group?.dispose();
    this.camera.dispose();
    this.collider.dispose();
    this.root.dispose(false, true);
  }
}
