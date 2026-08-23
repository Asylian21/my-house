import type { AnimationGroup } from "@babylonjs/core/Animations/animationGroup";
import { ArcRotateCamera } from "@babylonjs/core/Cameras/arcRotateCamera";
import { Ray } from "@babylonjs/core/Culling/ray";
import { ImportMeshAsync } from "@babylonjs/core/Loading/sceneLoader";
import type { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { Texture } from "@babylonjs/core/Materials/Textures/texture";
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
  WALK_COLLISION_OFFSET_M,
  WALK_SPEED_MPS,
  integrateAvatarVelocity,
  stepWalkCameraBoom,
  type FlightCommand,
} from "./twin-viewport-contract";

export const AVATAR_URL = "/assets/avatar/avatar.glb";
export const AVATAR_DIFFUSE_URL =
  "/assets/avatar/michelle-light-diffuse.png";

export interface AvatarPose {
  readonly x: number;
  readonly z: number;
  readonly yaw: number;
}

interface CameraOccluder {
  readonly mesh: AbstractMesh;
  readonly minimumX: number;
  readonly minimumY: number;
  readonly minimumZ: number;
  readonly maximumX: number;
  readonly maximumY: number;
  readonly maximumZ: number;
}

/** Allocation-free broad phase; exact triangle picking follows every hit. */
function rayBoundsDistance(
  origin: Vector3,
  direction: Vector3,
  bounds: CameraOccluder,
  maxDistanceM: number,
  paddingM: number,
) {
  let near = 0;
  let far = maxDistanceM;

  let low = bounds.minimumX - paddingM;
  let high = bounds.maximumX + paddingM;
  if (Math.abs(direction.x) < 1e-9) {
    if (origin.x < low || origin.x > high) return null;
  } else {
    let entry = (low - origin.x) / direction.x;
    let exit = (high - origin.x) / direction.x;
    if (entry > exit) {
      const swap = entry;
      entry = exit;
      exit = swap;
    }
    near = Math.max(near, entry);
    far = Math.min(far, exit);
    if (near > far) return null;
  }

  low = bounds.minimumY - paddingM;
  high = bounds.maximumY + paddingM;
  if (Math.abs(direction.y) < 1e-9) {
    if (origin.y < low || origin.y > high) return null;
  } else {
    let entry = (low - origin.y) / direction.y;
    let exit = (high - origin.y) / direction.y;
    if (entry > exit) {
      const swap = entry;
      entry = exit;
      exit = swap;
    }
    near = Math.max(near, entry);
    far = Math.min(far, exit);
    if (near > far) return null;
  }

  low = bounds.minimumZ - paddingM;
  high = bounds.maximumZ + paddingM;
  if (Math.abs(direction.z) < 1e-9) {
    if (origin.z < low || origin.z > high) return null;
  } else {
    let entry = (low - origin.z) / direction.z;
    let exit = (high - origin.z) / direction.z;
    if (entry > exit) {
      const swap = entry;
      entry = exit;
      exit = swap;
    }
    near = Math.max(near, entry);
    far = Math.min(far, exit);
    if (near > far) return null;
  }
  return near <= maxDistanceM ? near : null;
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
  private active = false;
  private firstPerson = false;
  private sinceUserOrbitS = 10;
  private preferredCameraRadiusM = WALK_CAMERA.radiusM;
  private effectiveCameraRadiusM = WALK_CAMERA.radiusM;
  private cameraObstructed = false;
  private cameraOccluders: CameraOccluder[] = [];
  private readonly nearbyCameraOccluders: CameraOccluder[] = [];
  private occluderSceneMeshCount = -1;
  private lastOccluderStateSignature = 0;
  private readonly lastProbeTarget = new Vector3(
    Number.POSITIVE_INFINITY,
    Number.POSITIVE_INFINITY,
    Number.POSITIVE_INFINITY,
  );
  private lastProbeAlpha = Number.POSITIVE_INFINITY;
  private lastProbeBeta = Number.POSITIVE_INFINITY;
  private lastProbeDesiredRadiusM = Number.POSITIVE_INFINITY;
  private lastCameraHitDistanceM: number | null = null;
  private readonly cameraProbeDirection = new Vector3(0, 0, 1);
  private readonly cameraProbeRight = new Vector3(1, 0, 0);
  private readonly cameraProbeUp = new Vector3(0, 1, 0);
  private readonly cameraProbeOffsets = Array.from(
    { length: 5 },
    () => new Vector3(),
  );
  private readonly cameraProbeRays = Array.from(
    { length: 5 },
    () => new Ray(new Vector3(), new Vector3(0, 0, 1), WALK_CAMERA.maxRadiusM),
  );
  private readonly intendedMovement = new Vector3();
  private readonly movementSubstep = new Vector3();
  private readonly positionBeforeMove = new Vector3();
  private readonly actualMovement = new Vector3();
  private adaptiveVisibility = 1;
  private avatarMeshesEnabled: boolean | null = null;
  private lastAvatarOpacity = Number.NaN;
  private blockedForS = 0;
  private recoveryNeeded = false;
  private recoveryClearTravelM = 0;
  private readonly lastSafePosition = new Vector3(0, 0, 0);
  private readonly safeCandidatePosition = new Vector3(0, 0, 0);
  private safeTravelM = 0;

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
    // One authoritative capsule contract. The previous hidden +20 mm made the
    // 601 mm corridor and 680 mm framed openings unnecessarily sticky.
    this.collider.ellipsoid = new Vector3(
      WALK_COLLISION_ELLIPSOID_M.x,
      WALK_COLLISION_ELLIPSOID_M.y,
      WALK_COLLISION_ELLIPSOID_M.z,
    );
    this.collider.ellipsoidOffset = new Vector3(
      WALK_COLLISION_OFFSET_M.x,
      WALK_COLLISION_OFFSET_M.y,
      WALK_COLLISION_OFFSET_M.z,
    );

    this.camera = new ArcRotateCamera(
      "avatar-camera",
      -Math.PI / 2,
      WALK_CAMERA.betaRad,
      WALK_CAMERA.radiusM,
      this.cameraTarget.clone(),
      scene,
    );
    this.camera.lowerRadiusLimit = WALK_CAMERA.obstructionMinRadiusM;
    this.camera.upperRadiusLimit = WALK_CAMERA.maxRadiusM;
    this.camera.lowerBetaLimit = WALK_CAMERA.lowerBetaRad;
    this.camera.upperBetaLimit = WALK_CAMERA.upperBetaRad;
    this.camera.minZ = 0.04;
    this.camera.maxZ = 220;
    this.camera.fov = 0.95;
    this.camera.inertia = WALK_CAMERA.rotationInertia;
    this.camera.angularSensibilityX = WALK_CAMERA.angularSensibilityX;
    this.camera.angularSensibilityY = WALK_CAMERA.angularSensibilityY;
    this.camera.panningSensibility = 0;
    // Natural pinch writes the radius synchronously during the pointer event.
    // The adaptive boom can fold that into the preferred radius instead of
    // overwriting the gesture on the next frame.
    this.camera.useNaturalPinchZoom = true;
    this.camera.inputs.removeByType("ArcRotateCameraMouseWheelInput");
    this.camera.inputs.removeByType("ArcRotateCameraKeyboardMoveInput");
    // ArcRotateCamera collisions overwrite alpha/radius on contact. A cached
    // five-ray obstruction fan below keeps desired and rendered radii apart.
    this.camera.checkCollisions = false;
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
          this.avatarMeshesEnabled = null;
          this.lastAvatarOpacity = Number.NaN;
          const avatarDiffuse = new Texture(AVATAR_DIFFUSE_URL, this.scene, {
            invertY: false,
            samplingMode: Texture.TRILINEAR_SAMPLINGMODE,
            useSRGBBuffer: true,
          });
          avatarDiffuse.name = "Avatar · svetlá pokožka";
          avatarDiffuse.gammaSpace = true;
          for (const mesh of this.meshes) {
            mesh.isPickable = false;
            mesh.receiveShadows = true;
            const material = mesh.material as PBRMaterial | null;
            if (material && "environmentIntensity" in material) {
              material.albedoTexture = avatarDiffuse;
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
          this.setVisible(this.active && !this.firstPerson);
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
    this.setVisible(this.active && !firstPerson);
  }

  private setVisible(visible: boolean) {
    const opacity = visible ? this.adaptiveVisibility : 0;
    // Fade all the way to transparent before disabling the rig, avoiding the
    // old visible pop near one metre and redundant setEnabled calls per frame.
    const renderAvatar = opacity > 0.01;
    if (this.avatarMeshesEnabled !== renderAvatar) {
      for (const mesh of this.meshes) mesh.setEnabled(renderAvatar);
      this.avatarMeshesEnabled = renderAvatar;
    }
    if (
      !Number.isFinite(this.lastAvatarOpacity) ||
      Math.abs(opacity - this.lastAvatarOpacity) > 0.002
    ) {
      for (const mesh of this.meshes) mesh.visibility = opacity;
      this.lastAvatarOpacity = opacity;
    }
  }

  /** Places the walker and turns the chase camera behind it. */
  place(xM: number, zM: number, yawRad: number) {
    this.active = true;
    this.collider.position.set(xM, 0, zM);
    this.collider.computeWorldMatrix(true);
    this.lastSafePosition.copyFrom(this.collider.position);
    this.safeCandidatePosition.copyFrom(this.collider.position);
    this.safeTravelM = 0;
    this.blockedForS = 0;
    this.recoveryNeeded = false;
    this.recoveryClearTravelM = 0;
    this.root.position.set(xM, 0, zM);
    this.yaw = yawRad;
    this.root.rotation.set(0, yawRad, 0);
    this.velocity.setAll(0);
    this.effectiveCameraRadiusM = this.preferredCameraRadiusM;
    this.adaptiveVisibility = Math.max(
      0,
      Math.min(
        1,
        (this.effectiveCameraRadiusM - WALK_CAMERA.avatarFadeNearM) /
          (WALK_CAMERA.avatarFadeFarM - WALK_CAMERA.avatarFadeNearM),
      ),
    );
    this.cameraTarget.set(
      xM,
      WALK_CAMERA.targetHeightM +
        (WALK_CAMERA.closeTargetHeightM - WALK_CAMERA.targetHeightM) *
          (1 - this.adaptiveVisibility),
      zM,
    );
    this.camera.target.copyFrom(this.cameraTarget);
    // Camera behind the walker: the avatar looks along (sin yaw, 0, cos yaw)
    // in this right-handed scene; alpha measures from +x toward +z.
    this.camera.alpha = Math.atan2(-Math.cos(yawRad), -Math.sin(yawRad));
    this.camera.beta = WALK_CAMERA.betaRad;
    this.cameraObstructed = false;
    this.lastProbeTarget.setAll(Number.POSITIVE_INFINITY);
    this.camera.radius = this.effectiveCameraRadiusM;
    this.camera.inertialAlphaOffset = 0;
    this.camera.inertialBetaOffset = 0;
    this.camera.inertialRadiusOffset = 0;
    // Resolve the spherical pose now; the next before-render pass compresses
    // it before the view matrix is used, including on room relocation.
    this.camera.getViewMatrix();
    this.setVisible(!this.firstPerson);
  }

  deactivate() {
    this.active = false;
    this.setVisible(false);
    this.velocity.setAll(0);
    this.blockedForS = 0;
    this.recoveryNeeded = false;
    this.recoveryClearTravelM = 0;
  }

  noteCameraInput() {
    this.sinceUserOrbitS = 0;
  }

  get isBlocked() {
    return this.recoveryNeeded;
  }

  get cameraState() {
    return {
      desiredRadiusM: this.preferredCameraRadiusM,
      effectiveRadiusM: this.effectiveCameraRadiusM,
      obstructed: this.cameraObstructed,
    } as const;
  }

  /** Rewinds only a short distance to the latest unobstructed movement anchor. */
  recover() {
    // Keep the recovery request latched after input is released, giving a
    // novice enough time to reach R/the button without losing the safe rewind.
    if (this.recoveryNeeded) this.collider.position.copyFrom(this.lastSafePosition);
    this.collider.position.y = 0;
    this.collider.computeWorldMatrix(true);
    this.root.position.copyFrom(this.collider.position);
    this.velocity.setAll(0);
    this.blockedForS = 0;
    this.recoveryNeeded = false;
    this.recoveryClearTravelM = 0;
    this.safeTravelM = 0;
    this.safeCandidatePosition.copyFrom(this.collider.position);
    this.cameraTarget.set(
      this.collider.position.x,
      WALK_CAMERA.targetHeightM +
        (WALK_CAMERA.closeTargetHeightM - WALK_CAMERA.targetHeightM) *
          (1 - this.adaptiveVisibility),
      this.collider.position.z,
    );
    this.camera.alpha = Math.atan2(-Math.cos(this.yaw), -Math.sin(this.yaw));
    this.camera.beta = WALK_CAMERA.betaRad;
    this.camera.inertialAlphaOffset = 0;
    this.camera.inertialBetaOffset = 0;
    this.camera.inertialRadiusOffset = 0;
    this.sinceUserOrbitS = 10;
    this.camera.target.copyFrom(this.cameraTarget);
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
    const x = -Math.cos(this.camera.alpha);
    const z = -Math.sin(this.camera.alpha);
    const length = Math.hypot(x, z);
    return length > 1e-6
      ? { x: x / length, z: z / length }
      : { x: Math.sin(this.yaw), z: Math.cos(this.yaw) };
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
    const seconds = Math.min(50, Math.max(0, deltaMs)) / 1000;
    const intended = this.intendedMovement.set(
      next.x * seconds,
      0,
      next.z * seconds,
    );
    this.positionBeforeMove.copyFrom(this.collider.position);
    if (intended.lengthSquared() > 1e-12) {
      const substeps = Math.max(
        1,
        Math.ceil(intended.length() / WALK_CAMERA.maxMoveSubstepM),
      );
      intended.scaleToRef(1 / substeps, this.movementSubstep);
      this.collider.computeWorldMatrix(true);
      for (let index = 0; index < substeps; index += 1) {
        this.collider.moveWithCollisions(this.movementSubstep);
        // moveWithCollisions mutates position in place; force the hidden
        // collider's absolute matrix before the next substep/frame. Without
        // this, Babylon can resolve every step from a stale start and tunnel
        // through furniture during a sprint or a deterministic QA loop.
        this.collider.position.y = 0;
        this.collider.computeWorldMatrix(true);
      }
    }
    const moved = this.actualMovement
      .copyFrom(this.collider.position)
      .subtractInPlace(this.positionBeforeMove);
    moved.y = 0;
    const intendedDistance = intended.length();
    const movedDistance = moved.length();
    const progress = intendedDistance > 1e-5
      ? Math.max(
          0,
          Math.min(
            1,
            Vector3.Dot(moved, intended) / (intendedDistance * intendedDistance),
          ),
        )
      : 1;
    const collisionCorrectionM = Math.hypot(
      intended.x - moved.x,
      intended.z - moved.z,
    );
    const actualX = seconds > 1e-5 ? moved.x / seconds : 0;
    const actualZ = seconds > 1e-5 ? moved.z / seconds : 0;
    // Collision response is always authoritative. In particular, a shallow
    // wall slide must not retain the intended wall-normal velocity and hit the
    // same corner again on every frame.
    this.velocity.set(actualX, 0, actualZ);
    this.root.position.copyFrom(this.collider.position);

    const speed = Math.hypot(actualX, actualZ);
    const hasDirectionalInput =
      commands.has("forward") ||
      commands.has("backward") ||
      commands.has("left") ||
      commands.has("right");
    if (hasDirectionalInput && intendedDistance > 1e-7 && progress < 0.12) {
      this.blockedForS += seconds;
    } else {
      this.blockedForS = Math.max(0, this.blockedForS - seconds * 1.2);
    }
    if (this.blockedForS >= 0.3) {
      this.recoveryNeeded = true;
      this.recoveryClearTravelM = 0;
    }
    if (
      this.recoveryNeeded &&
      hasDirectionalInput &&
      progress > 0.72 &&
      movedDistance > 0.001
    ) {
      this.recoveryClearTravelM += movedDistance;
      if (this.recoveryClearTravelM >= 0.45) {
        this.recoveryNeeded = false;
        this.blockedForS = 0;
        this.recoveryClearTravelM = 0;
      }
    }
    if (
      progress > 0.97 &&
      collisionCorrectionM < 0.01 &&
      movedDistance > 0.001
    ) {
      this.safeTravelM += movedDistance;
      if (this.safeTravelM >= 0.14) {
        // Retain one proven-clear checkpoint behind the newest candidate.
        // Recovery therefore creates useful breathing room instead of moving
        // only a few centimetres when contact follows a checkpoint update.
        this.lastSafePosition.copyFrom(this.safeCandidatePosition);
        this.safeCandidatePosition.copyFrom(this.collider.position);
        this.safeTravelM = 0;
      }
    } else if (collisionCorrectionM >= 0.01) {
      this.safeTravelM = 0;
    }

    if (speed > 0.08) {
      const targetYaw = Math.atan2(actualX, actualZ);
      let delta = targetYaw - this.yaw;
      delta = Math.atan2(Math.sin(delta), Math.cos(delta));
      const turn = 1 - Math.exp(-seconds / WALK_CAMERA.turnTauS);
      this.yaw += delta * turn;
    }
    this.root.rotation.set(0, this.yaw, 0);

    // Chase camera: the target glides after the head with a short lag, and
    // when the player is not dragging it drifts back behind the walker while
    // walking — GTA-style, but without any camera drift while standing.
    const cameraStillMoving =
      Math.abs(this.camera.inertialAlphaOffset) +
        Math.abs(this.camera.inertialBetaOffset) >
      1e-4;
    this.sinceUserOrbitS = cameraStillMoving ? 0 : this.sinceUserOrbitS + seconds;
    if (
      !cameraStillMoving &&
      speed > 0.3 &&
      this.sinceUserOrbitS > WALK_CAMERA.recenterDelayS
    ) {
      const behind = Math.atan2(-Math.cos(this.yaw), -Math.sin(this.yaw));
      let delta = behind - this.camera.alpha;
      delta = Math.atan2(Math.sin(delta), Math.cos(delta));
      this.camera.alpha += delta * (1 - Math.exp(-seconds / WALK_CAMERA.recenterTauS));
    }
    const follow = 1 - Math.exp(-seconds / WALK_CAMERA.followTauS);
    this.cameraTarget.x += (this.collider.position.x - this.cameraTarget.x) * follow;
    this.cameraTarget.z += (this.collider.position.z - this.cameraTarget.z) * follow;
    const lagX = this.collider.position.x - this.cameraTarget.x;
    const lagZ = this.collider.position.z - this.cameraTarget.z;
    const lag = Math.hypot(lagX, lagZ);
    if (lag > WALK_CAMERA.maxTargetLagM) {
      const scale = WALK_CAMERA.maxTargetLagM / lag;
      this.cameraTarget.x = this.collider.position.x - lagX * scale;
      this.cameraTarget.z = this.collider.position.z - lagZ * scale;
    }
    const closeBlend = 1 - this.adaptiveVisibility;
    this.cameraTarget.y =
      WALK_CAMERA.targetHeightM +
      (WALK_CAMERA.closeTargetHeightM - WALK_CAMERA.targetHeightM) * closeBlend;
    // Probe and render from the exact same target height. The newly resolved
    // visibility affects next frame's target, forcing another probe then.
    if (!this.firstPerson) this.updateCameraObstruction(deltaMs);
    this.camera.target.copyFrom(this.cameraTarget);

    this.blendAnimations(speed);
    return speed;
  }

  private refreshCameraOccluders() {
    if (this.occluderSceneMeshCount === this.scene.meshes.length) return;
    const avatarMeshes = new Set(this.meshes);
    const occluders: CameraOccluder[] = [];
    for (const mesh of this.scene.meshes) {
      if (mesh === this.collider || avatarMeshes.has(mesh)) continue;
      if (mesh.getTotalVertices() === 0) continue;
      const metadata = mesh.metadata as {
        readonly cameraOccluder?: boolean;
        readonly walkCollisionOnly?: boolean;
      } | null;
      if (metadata?.walkCollisionOnly === true) continue;
      if (
        !mesh.checkCollisions &&
        metadata?.cameraOccluder !== true
      ) {
        continue;
      }
      mesh.computeWorldMatrix(true);
      const bounds = mesh.getBoundingInfo().boundingBox;
      occluders.push({
        mesh,
        minimumX: bounds.minimumWorld.x,
        minimumY: bounds.minimumWorld.y,
        minimumZ: bounds.minimumWorld.z,
        maximumX: bounds.maximumWorld.x,
        maximumY: bounds.maximumWorld.y,
        maximumZ: bounds.maximumWorld.z,
      });
    }
    this.cameraOccluders = occluders;
    this.occluderSceneMeshCount = this.scene.meshes.length;
    this.lastOccluderStateSignature = 0;
    this.lastProbeTarget.setAll(Number.POSITIVE_INFINITY);
  }

  private cameraHitDistance() {
    this.refreshCameraOccluders();
    // A layer can be toggled without changing mesh count or camera pose. Fold
    // enabled state into the cache key so a stationary view never keeps a
    // stale wall hit/miss. Visibility itself is intentionally ignored: walk
    // collisions remain authoritative through a technical/realistic handoff.
    let stateSignature = 0x811c9dc5;
    for (const occluder of this.cameraOccluders) {
      const enabled = !occluder.mesh.isDisposed() && occluder.mesh.isEnabled();
      stateSignature ^= occluder.mesh.uniqueId * 2 + (enabled ? 1 : 0);
      stateSignature = Math.imul(stateSignature, 0x01000193);
    }
    const targetMoved =
      Vector3.DistanceSquared(this.cameraTarget, this.lastProbeTarget) > 0.000225;
    const angleMoved =
      Math.abs(this.camera.alpha - this.lastProbeAlpha) > 0.003 ||
      Math.abs(this.camera.beta - this.lastProbeBeta) > 0.003;
    const zoomChanged =
      Math.abs(this.preferredCameraRadiusM - this.lastProbeDesiredRadiusM) > 0.008;
    if (
      !targetMoved &&
      !angleMoved &&
      !zoomChanged &&
      stateSignature === this.lastOccluderStateSignature
    ) {
      return this.lastCameraHitDistanceM;
    }
    this.lastOccluderStateSignature = stateSignature;
    this.lastProbeTarget.copyFrom(this.cameraTarget);
    this.lastProbeAlpha = this.camera.alpha;
    this.lastProbeBeta = this.camera.beta;
    this.lastProbeDesiredRadiusM = this.preferredCameraRadiusM;
    const sinBeta = Math.sin(this.camera.beta);
    const direction = this.cameraProbeDirection.set(
      Math.cos(this.camera.alpha) * sinBeta,
      Math.cos(this.camera.beta),
      Math.sin(this.camera.alpha) * sinBeta,
    );
    direction.normalize();
    Vector3.CrossToRef(Vector3.UpReadOnly, direction, this.cameraProbeRight);
    this.cameraProbeRight.normalize();
    Vector3.CrossToRef(direction, this.cameraProbeRight, this.cameraProbeUp);
    this.cameraProbeUp.normalize();
    this.cameraProbeOffsets[0].setAll(0);
    this.cameraProbeRight.scaleToRef(
      WALK_CAMERA.collisionProbeRadiusM,
      this.cameraProbeOffsets[1],
    );
    this.cameraProbeRight.scaleToRef(
      -WALK_CAMERA.collisionProbeRadiusM,
      this.cameraProbeOffsets[2],
    );
    this.cameraProbeUp.scaleToRef(
      WALK_CAMERA.collisionProbeRadiusM * 0.72,
      this.cameraProbeOffsets[3],
    );
    this.cameraProbeUp.scaleToRef(
      -WALK_CAMERA.collisionProbeRadiusM * 0.72,
      this.cameraProbeOffsets[4],
    );

    // One world scan builds a small local candidate set; the five fan rays
    // then touch only nearby geometry. Numeric bounds stay allocation-free in
    // the hot path, while every broad-phase hit is verified against triangles.
    this.nearbyCameraOccluders.length = 0;
    const rangeM =
      this.preferredCameraRadiusM + WALK_CAMERA.collisionProbeRadiusM + 0.04;
    const minX = this.cameraTarget.x - rangeM;
    const minY = this.cameraTarget.y - rangeM;
    const minZ = this.cameraTarget.z - rangeM;
    const maxX = this.cameraTarget.x + rangeM;
    const maxY = this.cameraTarget.y + rangeM;
    const maxZ = this.cameraTarget.z + rangeM;
    for (const occluder of this.cameraOccluders) {
      if (occluder.mesh.isDisposed() || !occluder.mesh.isEnabled()) continue;
      if (
        occluder.maximumX < minX ||
        occluder.minimumX > maxX ||
        occluder.maximumY < minY ||
        occluder.minimumY > maxY ||
        occluder.maximumZ < minZ ||
        occluder.minimumZ > maxZ
      ) {
        continue;
      }
      this.nearbyCameraOccluders.push(occluder);
    }

    let nearest = Number.POSITIVE_INFINITY;
    for (let index = 0; index < this.cameraProbeRays.length; index += 1) {
      const ray = this.cameraProbeRays[index];
      ray.origin.copyFrom(this.cameraTarget).addInPlace(this.cameraProbeOffsets[index]);
      ray.direction.copyFrom(direction);
      ray.length = this.preferredCameraRadiusM;
      for (const occluder of this.nearbyCameraOccluders) {
        const broadDistance = rayBoundsDistance(
          ray.origin,
          direction,
          occluder,
          this.preferredCameraRadiusM,
          0.01,
        );
        if (broadDistance === null || broadDistance >= nearest) continue;
        const pick = ray.intersectsMesh(occluder.mesh, false);
        if (
          pick.hit &&
          Number.isFinite(pick.distance) &&
          pick.distance >= 0 &&
          pick.distance <= this.preferredCameraRadiusM &&
          pick.distance < nearest
        ) {
          nearest = pick.distance;
        }
      }
    }
    this.lastCameraHitDistanceM = Number.isFinite(nearest) ? nearest : null;
    return this.lastCameraHitDistanceM;
  }

  private captureNativePinch() {
    const observedRadiusM = this.camera.radius;
    if (
      !Number.isFinite(observedRadiusM) ||
      !Number.isFinite(this.effectiveCameraRadiusM) ||
      this.effectiveCameraRadiusM < 1e-6 ||
      Math.abs(observedRadiusM - this.effectiveCameraRadiusM) < 0.004
    ) {
      return;
    }
    const multiplier = observedRadiusM / this.effectiveCameraRadiusM;
    this.preferredCameraRadiusM = Math.max(
      WALK_CAMERA.minRadiusM,
      Math.min(WALK_CAMERA.maxRadiusM, this.preferredCameraRadiusM * multiplier),
    );
    this.effectiveCameraRadiusM = this.cameraObstructed
      ? Math.max(
          WALK_CAMERA.obstructionMinRadiusM,
          Math.min(this.preferredCameraRadiusM, observedRadiusM),
        )
      : this.preferredCameraRadiusM;
    this.lastProbeDesiredRadiusM = Number.POSITIVE_INFINITY;
    this.sinceUserOrbitS = 0;
  }

  private updateCameraObstruction(deltaMs: number) {
    this.captureNativePinch();
    const boom = stepWalkCameraBoom({
      desiredRadiusM: this.preferredCameraRadiusM,
      currentRadiusM: this.effectiveCameraRadiusM,
      hitDistanceM: this.cameraHitDistance(),
      deltaMs,
      wasObstructed: this.cameraObstructed,
    });
    this.effectiveCameraRadiusM = boom.radiusM;
    this.cameraObstructed = boom.obstructed;
    this.camera.radius = boom.radiusM;
    this.camera.inertialRadiusOffset = 0;
    this.adaptiveVisibility = Math.max(
      0,
      Math.min(
        1,
        (boom.radiusM - WALK_CAMERA.avatarFadeNearM) /
          (WALK_CAMERA.avatarFadeFarM - WALK_CAMERA.avatarFadeNearM),
      ),
    );
    this.setVisible(this.active && !this.firstPerson);
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
    const next = this.preferredCameraRadiusM * Math.exp(pixels * 0.0032);
    this.preferredCameraRadiusM = Math.max(
      WALK_CAMERA.minRadiusM,
      Math.min(WALK_CAMERA.maxRadiusM, next),
    );
    if (this.preferredCameraRadiusM < this.effectiveCameraRadiusM) {
      this.effectiveCameraRadiusM = this.preferredCameraRadiusM;
      this.camera.radius = this.effectiveCameraRadiusM;
    }
  }

  dispose() {
    for (const group of [this.idle, this.walk, this.run]) group?.dispose();
    this.camera.dispose();
    this.collider.dispose();
    this.root.dispose(false, true);
  }
}
