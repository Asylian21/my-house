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
  WALK_SURFACE,
  WALK_SPEED_MPS,
  addWalkEscapeDirection,
  integrateAvatarVelocity,
  resolveWalkCollisionVelocity,
  shouldAutoRecoverWalk,
  shouldResetWalkCollisionCarry,
  shouldResolveWalkCollisionBatch,
  stepWalkCameraSurfaceHeight,
  stepWalkCameraBoom,
  stepWalkIndoorBlend,
  walkCameraRadiusForEnvironment,
  type FlightCommand,
  type WalkSurfaceKind,
} from "./twin-viewport-contract";
import {
  DEFAULT_WALK_AVATAR_ID,
  walkAvatarOption,
  type WalkAvatarId,
  type WalkAvatarOption,
} from "./twin-avatar";
import {
  DOORWAY_ASSIST,
  movementProgress,
  rotatePlanar,
  shouldAttemptDeflection,
  steerVelocityThroughPassages,
  type WalkPassage,
} from "./twin-walk-assist";

export const AVATAR_URL = walkAvatarOption(DEFAULT_WALK_AVATAR_ID).modelUrl;
export const AVATAR_DIFFUSE_URL =
  walkAvatarOption(DEFAULT_WALK_AVATAR_ID).diffuseUrl ?? "";

export interface AvatarPose {
  readonly x: number;
  readonly y: number;
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

interface WalkSurface {
  readonly mesh: AbstractMesh;
  readonly kind: WalkSurfaceKind;
  readonly id: string;
  readonly elevationOffsetM: number;
  readonly minimumX: number;
  readonly minimumZ: number;
  readonly maximumX: number;
  readonly maximumZ: number;
}

type WalkSurfaceSnapResult = "resolved" | "blocked-rise" | "missing";

interface LoadedAvatarRig {
  readonly id: WalkAvatarId;
  readonly root: AbstractMesh;
  readonly meshes: AbstractMesh[];
  readonly animationGroups: AnimationGroup[];
  readonly idle: AnimationGroup;
  readonly walk: AnimationGroup;
  readonly run: AnimationGroup;
}

const EMPTY_FLIGHT_COMMANDS: ReadonlySet<FlightCommand> = new Set();

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
 * Third-person walker: one shared kinematic controller, collider and chase
 * camera driving a selectable visual rig. The visual choice never owns the
 * player's position, so switching characters cannot teleport the walker or
 * alter architectural collisions.
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
  private selectedAvatarId: WalkAvatarId = DEFAULT_WALK_AVATAR_ID;
  private currentRig: LoadedAvatarRig | null = null;
  private readonly loadedRigs = new Map<WalkAvatarId, LoadedAvatarRig>();
  private readonly loadPromises = new Map<WalkAvatarId, Promise<LoadedAvatarRig>>();
  private active = false;
  private firstPerson = false;
  private sinceUserOrbitS = 10;
  private preferredCameraRadiusM = WALK_CAMERA.radiusM;
  private desiredCameraRadiusM = WALK_CAMERA.radiusM;
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
  private walkSurfaces: WalkSurface[] = [];
  private walkSurfaceSceneMeshCount = -1;
  private readonly surfaceProbeRay = new Ray(
    new Vector3(),
    new Vector3(0, -1, 0),
    WALK_SURFACE.maxStepUpM + WALK_SURFACE.maxDropM,
  );
  private surfaceY = 0;
  private cameraSurfaceY = 0;
  private surfaceKind: WalkSurfaceKind = "interior";
  private surfaceId: string | null = null;
  private surfaceValid = true;
  private indoorBlend = 1;
  private readonly intendedMovement = new Vector3();
  private readonly movementSinceCollisionSolve = new Vector3();
  private pendingMovementSecondsS = 0;
  private collisionBatchAccountedSecondsS = 0;
  private readonly movementSubstep = new Vector3();
  private readonly positionBeforeMove = new Vector3();
  private readonly positionBeforeSubstep = new Vector3();
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
  private blockedDirectionMask = 0;
  private blockedAttemptWindowS = 0;
  private autoRecoveryCooldownS = 0;
  private autoRecoveryCount = 0;
  private autoRecoveryAwaitingRelease = false;
  private passages: readonly WalkPassage[] = [];
  private deflectionCount = 0;
  private readonly deflectedSubstep = new Vector3();
  private readonly deflectedBestPosition = new Vector3();
  private readonly nudgeDisplacement = new Vector3();

  constructor(
    private readonly scene: Scene,
    private readonly onMeshLoaded: (mesh: AbstractMesh) => void,
    private readonly resolveAssetUrl: (url: string) => string = (url) => url,
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
    return this.currentRig?.id === this.selectedAvatarId;
  }

  get avatarId() {
    return this.selectedAvatarId;
  }

  get activeAvatarId() {
    return this.currentRig?.id ?? null;
  }

  get isFirstPerson() {
    return this.firstPerson;
  }

  /** Loads and activates the selected glTF; safe to call repeatedly. */
  load(): Promise<void> {
    const requestedId = this.selectedAvatarId;
    return this.loadRig(requestedId).then((rig) => {
      if (this.selectedAvatarId === requestedId) this.activateRig(rig);
    });
  }

  /**
   * Selects a new visual rig. Before walkthrough entry this only records the
   * preference; during play the old rig remains visible until the new local
   * asset is completely ready.
   */
  setAvatar(id: WalkAvatarId, loadNow = this.active): Promise<void> {
    this.selectedAvatarId = id;
    if (!loadNow) return Promise.resolve();
    return this.loadRig(id)
      .then((rig) => {
        if (this.selectedAvatarId === id) this.activateRig(rig);
      })
      .catch((error: unknown) => {
        if (this.selectedAvatarId === id) {
          this.selectedAvatarId = this.currentRig?.id ?? DEFAULT_WALK_AVATAR_ID;
        }
        throw error;
      });
  }

  private loadRig(id: WalkAvatarId): Promise<LoadedAvatarRig> {
    const cached = this.loadedRigs.get(id);
    if (cached) return Promise.resolve(cached);
    const pending = this.loadPromises.get(id);
    if (pending) return pending;

    const option = walkAvatarOption(id);
    const promise = ImportMeshAsync(
      this.resolveAssetUrl(option.modelUrl),
      this.scene,
    )
      .then((result) => {
        const glbRoot =
          result.meshes.find((mesh) => mesh.name === "__root__") ??
          result.meshes[0];
        if (!glbRoot) throw new Error(`Avatar ${id} does not contain a scene root.`);
        glbRoot.parent = this.root;
        // All shipped choices are authored facing +z after glTF conversion.
        // A per-rig offset remains explicit so a future model cannot silently
        // break the controller's yaw = 0 heading contract.
        glbRoot.rotationQuaternion = null;
        glbRoot.rotation.set(0, option.headingOffsetRad, 0);
        glbRoot.scaling.setAll(option.modelScale);

        const meshes = result.meshes.filter(
          (mesh) => mesh.getTotalVertices() > 0,
        );
        const avatarDiffuse = this.createDiffuseOverride(option);
        for (const mesh of meshes) {
          mesh.isPickable = false;
          mesh.receiveShadows = true;
          mesh.checkCollisions = false;
          const material = mesh.material as PBRMaterial | null;
          if (material && "environmentIntensity" in material) {
            if (avatarDiffuse) material.albedoTexture = avatarDiffuse;
            material.environmentIntensity = 0.9;
          }
          this.onMeshLoaded(mesh);
        }

        const byName = (name: string) =>
          result.animationGroups.find((group) => group.name === name) ?? null;
        const idle = byName(option.clips.idle);
        const walk = byName(option.clips.walk);
        const run = byName(option.clips.run);
        if (!idle || !walk || !run) {
          glbRoot.dispose(false, true);
          for (const group of result.animationGroups) group.dispose();
          throw new Error(
            `Avatar ${id} is missing ${option.clips.idle}/${option.clips.walk}/${option.clips.run} locomotion clips.`,
          );
        }
        for (const group of result.animationGroups) {
          group.stop();
          group.reset();
          group.loopAnimation = true;
        }
        glbRoot.setEnabled(false);
        const rig: LoadedAvatarRig = {
          id,
          root: glbRoot,
          meshes,
          animationGroups: result.animationGroups,
          idle,
          walk,
          run,
        };
        this.loadedRigs.set(id, rig);
        this.occluderSceneMeshCount = -1;
        return rig;
      })
      .finally(() => {
        this.loadPromises.delete(id);
      });
    this.loadPromises.set(id, promise);
    return promise;
  }

  private createDiffuseOverride(option: WalkAvatarOption) {
    if (!option.diffuseUrl) return null;
    const texture = new Texture(this.resolveAssetUrl(option.diffuseUrl), this.scene, {
      invertY: false,
      samplingMode: Texture.TRILINEAR_SAMPLINGMODE,
      useSRGBBuffer: true,
    });
    texture.name = `Avatar · ${option.label} · albedo`;
    texture.gammaSpace = true;
    return texture;
  }

  private activateRig(rig: LoadedAvatarRig) {
    if (this.currentRig === rig) {
      this.setVisible(this.active && !this.firstPerson);
      return;
    }
    if (this.currentRig) {
      for (const group of this.currentRig.animationGroups) group.stop();
      this.currentRig.root.setEnabled(false);
    }
    this.currentRig = rig;
    this.meshes = rig.meshes;
    this.idle = rig.idle;
    this.walk = rig.walk;
    this.run = rig.run;
    rig.root.setEnabled(true);
    for (const group of rig.animationGroups) {
      group.stop();
      group.reset();
    }
    for (const group of [rig.idle, rig.walk, rig.run]) {
      group.play(true);
      group.weight = group === rig.idle ? 1 : 0;
    }
    this.avatarMeshesEnabled = null;
    this.lastAvatarOpacity = Number.NaN;
    this.occluderSceneMeshCount = -1;
    this.setVisible(this.active && !this.firstPerson);
    this.blendAnimations(Math.hypot(this.velocity.x, this.velocity.z));
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

  private refreshWalkSurfaces() {
    if (this.walkSurfaceSceneMeshCount === this.scene.meshes.length) return;
    const surfaces: WalkSurface[] = [];
    for (const mesh of this.scene.meshes) {
      if (mesh === this.collider || mesh.getTotalVertices() === 0) continue;
      const metadata = mesh.metadata as {
        readonly walkSurface?: boolean;
        readonly walkSurfaceKind?: WalkSurfaceKind;
        readonly walkSurfaceId?: string;
        readonly walkSurfaceElevationOffsetM?: number;
      } | null;
      if (metadata?.walkSurface !== true) continue;
      mesh.computeWorldMatrix(true);
      const bounds = mesh.getBoundingInfo().boundingBox;
      surfaces.push({
        mesh,
        kind: metadata.walkSurfaceKind ?? "exterior",
        id: metadata.walkSurfaceId ?? mesh.name,
        elevationOffsetM: Number.isFinite(
          metadata.walkSurfaceElevationOffsetM,
        )
          ? (metadata.walkSurfaceElevationOffsetM ?? 0)
          : 0,
        minimumX: bounds.minimumWorld.x,
        minimumZ: bounds.minimumWorld.z,
        maximumX: bounds.maximumWorld.x,
        maximumZ: bounds.maximumWorld.z,
      });
    }
    this.walkSurfaces = surfaces;
    this.walkSurfaceSceneMeshCount = this.scene.meshes.length;
  }

  /**
   * Finds the highest tagged walk surface within one human-sized step/drop
   * window. A taller probe also rejects an exact raised-surface hit
   * inside the walker's body clearance, even when lower terrain exists below
   * it. Visual detail never becomes floor collision, and disabled drawing
   * layers remain valid geometry for walking.
   */
  private snapToWalkSurface(): WalkSurfaceSnapResult {
    this.refreshWalkSurfaces();
    const currentY = Number.isFinite(this.surfaceY)
      ? this.surfaceY
      : this.collider.position.y;
    const standingClearanceM =
      WALK_COLLISION_OFFSET_M.y + WALK_COLLISION_ELLIPSOID_M.y;
    const originY =
      currentY + standingClearanceM + WALK_SURFACE.probeHeadroomM;
    const probeLength =
      standingClearanceM +
      WALK_SURFACE.probeHeadroomM +
      WALK_SURFACE.maxDropM;
    this.surfaceProbeRay.origin.set(
      this.collider.position.x,
      originY,
      this.collider.position.z,
    );
    this.surfaceProbeRay.length = probeLength;

    let resolvedY = Number.NEGATIVE_INFINITY;
    let resolved: WalkSurface | null = null;
    let blockedByRise = false;
    for (const surface of this.walkSurfaces) {
      if (surface.mesh.isDisposed()) continue;
      if (
        this.collider.position.x < surface.minimumX - 0.015 ||
        this.collider.position.x > surface.maximumX + 0.015 ||
        this.collider.position.z < surface.minimumZ - 0.015 ||
        this.collider.position.z > surface.maximumZ + 0.015
      ) {
        continue;
      }
      const hit = this.surfaceProbeRay.intersectsMesh(surface.mesh, false);
      if (!hit.hit || !Number.isFinite(hit.distance)) continue;
      const hitY =
        (hit.pickedPoint?.y ?? originY - hit.distance) +
        surface.elevationOffsetM;
      if (hitY > currentY + WALK_SURFACE.maxStepUpM + 1e-4) {
        // AABB membership is only the broad phase: this branch is reached only
        // after an exact triangle hit at the proposed X/Z. Ignore a true
        // overhead that leaves the collision ellipsoid standing clearance.
        if (hitY <= currentY + standingClearanceM + 1e-4) {
          blockedByRise = true;
        }
        continue;
      }
      if (
        hitY < currentY - WALK_SURFACE.maxDropM - 1e-4 ||
        hitY <= resolvedY
      ) {
        continue;
      }
      resolvedY = hitY;
      resolved = surface;
    }

    if (blockedByRise) {
      this.collider.position.y = currentY;
      return "blocked-rise";
    }
    if (!resolved || !Number.isFinite(resolvedY)) {
      this.surfaceValid = this.walkSurfaces.length === 0;
      this.collider.position.y = currentY;
      return "missing";
    }
    this.surfaceY = resolvedY;
    this.surfaceKind = resolved.kind;
    this.surfaceId = resolved.id;
    this.surfaceValid = true;
    this.collider.position.y = resolvedY;
    return "resolved";
  }

  /**
   * Places the walker and turns the chase camera behind it. A surface hint is
   * needed for intentional level changes deeper than the normal step/drop
   * window, such as the controlled pool-shaft ladder transition.
   */
  place(xM: number, zM: number, yawRad: number, surfaceHintM = 0) {
    this.active = true;
    this.collider.position.set(xM, surfaceHintM, zM);
    this.surfaceY = surfaceHintM;
    this.snapToWalkSurface();
    this.collider.computeWorldMatrix(true);
    this.lastSafePosition.copyFrom(this.collider.position);
    this.safeCandidatePosition.copyFrom(this.collider.position);
    this.safeTravelM = 0;
    this.blockedForS = 0;
    this.recoveryNeeded = false;
    this.recoveryClearTravelM = 0;
    this.root.position.copyFrom(this.collider.position);
    this.yaw = yawRad;
    this.root.rotation.set(0, yawRad, 0);
    this.velocity.setAll(0);
    this.intendedMovement.setAll(0);
    this.movementSinceCollisionSolve.setAll(0);
    this.pendingMovementSecondsS = 0;
    this.collisionBatchAccountedSecondsS = 0;
    this.blockedDirectionMask = 0;
    this.blockedAttemptWindowS = 0;
    this.autoRecoveryCooldownS = 0;
    this.autoRecoveryAwaitingRelease = false;
    this.indoorBlend = this.surfaceKind === "interior" ? 1 : 0;
    this.desiredCameraRadiusM = walkCameraRadiusForEnvironment(
      this.preferredCameraRadiusM,
      this.indoorBlend,
    );
    this.effectiveCameraRadiusM = this.desiredCameraRadiusM;
    this.cameraSurfaceY = this.surfaceY;
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
      this.cameraSurfaceY +
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
    this.intendedMovement.setAll(0);
    this.movementSinceCollisionSolve.setAll(0);
    this.pendingMovementSecondsS = 0;
    this.collisionBatchAccountedSecondsS = 0;
    this.blockedForS = 0;
    this.recoveryNeeded = false;
    this.recoveryClearTravelM = 0;
    this.blockedDirectionMask = 0;
    this.blockedAttemptWindowS = 0;
    this.autoRecoveryAwaitingRelease = false;
  }

  noteCameraInput() {
    this.sinceUserOrbitS = 0;
  }

  get isBlocked() {
    return this.recoveryNeeded;
  }

  /** A successfully opening door explains the expected collision; no rewind. */
  clearBlockedIndicator() {
    this.blockedForS = 0;
    this.recoveryNeeded = false;
    this.recoveryClearTravelM = 0;
    this.blockedDirectionMask = 0;
    this.blockedAttemptWindowS = 0;
  }

  get cameraState() {
    return {
      requestedRadiusM: this.preferredCameraRadiusM,
      desiredRadiusM: this.desiredCameraRadiusM,
      effectiveRadiusM: this.effectiveCameraRadiusM,
      obstructed: this.cameraObstructed,
      indoorBlend: this.indoorBlend,
      surfaceY: this.surfaceY,
      cameraSurfaceY: this.cameraSurfaceY,
      surfaceKind: this.surfaceKind,
      surfaceId: this.surfaceId,
      surfaceValid: this.surfaceValid,
    } as const;
  }

  get recoveryState() {
    return {
      needed: this.recoveryNeeded,
      autoRecoveryCount: this.autoRecoveryCount,
      cooldownS: this.autoRecoveryCooldownS,
      attemptedDirectionMask: this.blockedDirectionMask,
      awaitingRelease: this.autoRecoveryAwaitingRelease,
      deflectionCount: this.deflectionCount,
    } as const;
  }

  /** Doorway envelopes the funnel assist may steer toward. */
  setPassages(passages: readonly WalkPassage[]) {
    this.passages = passages;
  }

  /**
   * Kinematic push from a moving door leaf. Runs through the same ellipsoid
   * collision and floor snapping as walking, so a wall behind the walker
   * still wins. Returns the share (0–1) of the requested push that was honoured.
   */
  nudge(dxM: number, dzM: number): number {
    if (!this.active) return 0;
    const distance = Math.hypot(dxM, dzM);
    if (!Number.isFinite(distance) || distance < 1e-6) return 1;
    this.positionBeforeMove.copyFrom(this.collider.position);
    this.moveColliderWithSurface(this.nudgeDisplacement.set(dxM, 0, dzM));
    const movedX = this.collider.position.x - this.positionBeforeMove.x;
    const movedZ = this.collider.position.z - this.positionBeforeMove.z;
    this.root.position.copyFrom(this.collider.position);
    // The camera target keeps its lag budget: shift it with the body so the
    // push reads as the door moving the person, not the person teleporting.
    this.cameraTarget.x += movedX;
    this.cameraTarget.z += movedZ;
    this.camera.target.copyFrom(this.cameraTarget);
    // A push is an external event; it must not count toward a stuck verdict.
    this.intendedMovement.setAll(0);
    this.movementSinceCollisionSolve.setAll(0);
    this.pendingMovementSecondsS = 0;
    this.collisionBatchAccountedSecondsS = 0;
    this.safeTravelM = 0;
    return movementProgress({ x: dxM, z: dzM }, { x: movedX, z: movedZ });
  }

  /** Rewinds only a short distance to the latest unobstructed movement anchor. */
  recover() {
    // Keep the recovery request latched after input is released, giving a
    // novice enough time to reach R/the button without losing the safe rewind.
    if (this.recoveryNeeded) this.collider.position.copyFrom(this.lastSafePosition);
    this.surfaceY = this.collider.position.y;
    this.snapToWalkSurface();
    this.collider.computeWorldMatrix(true);
    this.root.position.copyFrom(this.collider.position);
    this.velocity.setAll(0);
    this.intendedMovement.setAll(0);
    this.movementSinceCollisionSolve.setAll(0);
    this.pendingMovementSecondsS = 0;
    this.collisionBatchAccountedSecondsS = 0;
    this.blockedForS = 0;
    this.recoveryNeeded = false;
    this.recoveryClearTravelM = 0;
    this.blockedDirectionMask = 0;
    this.blockedAttemptWindowS = 0;
    this.autoRecoveryAwaitingRelease = false;
    this.safeTravelM = 0;
    this.safeCandidatePosition.copyFrom(this.collider.position);
    this.cameraSurfaceY = this.surfaceY;
    this.cameraTarget.set(
      this.collider.position.x,
      this.cameraSurfaceY +
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
    return {
      x: this.collider.position.x,
      y: this.surfaceY,
      z: this.collider.position.z,
      yaw: this.yaw,
    };
  }

  /** Eye position for the first-person view. */
  get eyePosition() {
    return new Vector3(
      this.collider.position.x,
      this.cameraSurfaceY + 1.62,
      this.collider.position.z,
    );
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
    const rawDirectionalInput =
      commands.has("forward") ||
      commands.has("backward") ||
      commands.has("left") ||
      commands.has("right");
    if (this.autoRecoveryAwaitingRelease && !rawDirectionalInput) {
      this.autoRecoveryAwaitingRelease = false;
    }
    const movementCommands = this.autoRecoveryAwaitingRelease
      ? EMPTY_FLIGHT_COMMANDS
      : commands;
    const forward = headingOverride ?? this.cameraForward();
    const integrated = integrateAvatarVelocity({
      velocity: { x: this.velocity.x, z: this.velocity.z },
      forward,
      commands: movementCommands,
      deltaMs,
      boost: modifiers.boost,
      precision: modifiers.precision,
    });
    // Doorway funnel: only ever rotates the heading toward an opening's
    // centreline, so the shoulder clears the lining without any speed change.
    const next =
      this.passages.length > 0 && !this.autoRecoveryAwaitingRelease
        ? steerVelocityThroughPassages(
            integrated,
            { x: this.collider.position.x, z: this.collider.position.z },
            this.passages,
          )
        : integrated;
    const seconds = Math.min(50, Math.max(0, deltaMs)) / 1000;
    this.autoRecoveryCooldownS = Math.max(
      0,
      this.autoRecoveryCooldownS - seconds,
    );
    this.blockedAttemptWindowS = Math.max(
      0,
      this.blockedAttemptWindowS - seconds,
    );
    if (this.blockedAttemptWindowS <= 0) this.blockedDirectionMask = 0;
    const hasDirectionalInput =
      rawDirectionalInput && !this.autoRecoveryAwaitingRelease;
    const intended = this.intendedMovement;
    const resetCollisionCarry = shouldResetWalkCollisionCarry(
      hasDirectionalInput,
      next,
      intended,
    );
    if (resetCollisionCarry) {
      intended.setAll(0);
      this.movementSinceCollisionSolve.setAll(0);
      this.pendingMovementSecondsS = 0;
      this.collisionBatchAccountedSecondsS = 0;
    }
    intended.x += next.x * seconds;
    intended.z += next.z * seconds;
    this.movementSinceCollisionSolve.x += next.x * seconds;
    this.movementSinceCollisionSolve.z += next.z * seconds;
    // Do not let wall-clock idle time turn the next sub-epsilon key press into
    // an immediate (and discarded) collision solve.
    if (!(resetCollisionCarry && !hasDirectionalInput)) {
      this.pendingMovementSecondsS += seconds;
    }
    const resolvedCollisionBatch = shouldResolveWalkCollisionBatch(
      this.movementSinceCollisionSolve,
      (this.pendingMovementSecondsS - this.collisionBatchAccountedSecondsS) *
        1000,
    );
    let moved = this.actualMovement.setAll(0);
    const intendedDistance = intended.length();
    let movedDistance = 0;
    let progress = 1;
    let collisionCorrectionM = 0;
    let actualX = next.x;
    let actualZ = next.z;
    let collisionBatchSecondsS = 0;
    let collisionAccountingSecondsS = 0;
    if (resolvedCollisionBatch) {
      collisionBatchSecondsS = this.pendingMovementSecondsS;
      collisionAccountingSecondsS = Math.max(
        0,
        collisionBatchSecondsS - this.collisionBatchAccountedSecondsS,
      );
      this.positionBeforeMove.copyFrom(this.collider.position);
      this.moveColliderWithSurface(intended);
      moved = this.actualMovement
        .copyFrom(this.collider.position)
        .subtractInPlace(this.positionBeforeMove);
      moved.y = 0;
      movedDistance = moved.length();
      progress = intendedDistance > 1e-5
        ? Math.max(
            0,
            Math.min(
              1,
              Vector3.Dot(moved, intended) / (intendedDistance * intendedDistance),
            ),
          )
        : 1;
      if (
        shouldAttemptDeflection(hasDirectionalInput, intendedDistance, progress)
      ) {
        // A jamb edge or a wardrobe corner caught the capsule. Try a few
        // steeper headings and keep the best one that still honours most of
        // the original intent; a flat wall rejects all of them and stays a wall.
        progress = this.tryDeflectedMove(intended, progress);
        moved = this.actualMovement
          .copyFrom(this.collider.position)
          .subtractInPlace(this.positionBeforeMove);
        moved.y = 0;
        movedDistance = moved.length();
      }
      collisionCorrectionM = Math.hypot(
        intended.x - moved.x,
        intended.z - moved.z,
      );
      const collisionVelocity = resolveWalkCollisionVelocity({
        terminal: next,
        intended,
        moved,
        elapsedMs: collisionBatchSecondsS * 1000,
      });
      actualX = collisionVelocity.x;
      actualZ = collisionVelocity.z;
      const retainRejectedMovement =
        hasDirectionalInput &&
        movedDistance <= 1e-5 &&
        collisionCorrectionM > 1e-5;
      if (retainRejectedMovement) {
        const carryDistanceM = intended.length();
        if (carryDistanceM > WALK_CAMERA.maxRejectedCollisionCarryM) {
          const carryScale =
            WALK_CAMERA.maxRejectedCollisionCarryM / carryDistanceM;
          intended.scaleInPlace(carryScale);
          this.pendingMovementSecondsS *= carryScale;
        }
        this.collisionBatchAccountedSecondsS =
          this.pendingMovementSecondsS;
        this.movementSinceCollisionSolve.setAll(0);
      } else {
        intended.setAll(0);
        this.movementSinceCollisionSolve.setAll(0);
        this.pendingMovementSecondsS = 0;
        this.collisionBatchAccountedSecondsS = 0;
      }
    }
    // A solved collision is authoritative. Unsolved high-refresh frames keep
    // integrating input until their real displacement clears Babylon's
    // epsilon; collision-free batches retain their terminal velocity rather
    // than replacing it with the batch-average acceleration.
    this.velocity.set(actualX, 0, actualZ);
    this.root.position.copyFrom(this.collider.position);

    let speed = Math.hypot(actualX, actualZ);
    if (resolvedCollisionBatch) {
      if (hasDirectionalInput && intendedDistance > 1e-7 && progress < 0.12) {
        this.blockedForS += collisionAccountingSecondsS;
        this.blockedAttemptWindowS = WALK_SURFACE.autoRecoveryAttemptWindowS;
        this.blockedDirectionMask = addWalkEscapeDirection(
          this.blockedDirectionMask,
          {
            x:
              Number(commands.has("right")) -
              Number(commands.has("left")),
            z:
              Number(commands.has("forward")) -
              Number(commands.has("backward")),
          },
        );
      } else {
        this.blockedForS = Math.max(
          0,
          this.blockedForS - collisionAccountingSecondsS * 1.2,
        );
        if (progress > 0.72 && movedDistance > 0.001) {
          this.blockedDirectionMask = 0;
          this.blockedAttemptWindowS = 0;
        }
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

      const rewindDistanceM = Math.hypot(
        this.collider.position.x - this.lastSafePosition.x,
        this.collider.position.z - this.lastSafePosition.z,
      );
      if (
        shouldAutoRecoverWalk({
          blockedForS: this.blockedForS,
          directionMask: this.blockedDirectionMask,
          rewindDistanceM,
          cooldownS: this.autoRecoveryCooldownS,
          hasDirectionalInput,
        })
      ) {
        this.collider.position.copyFrom(this.lastSafePosition);
        this.surfaceY = this.collider.position.y;
        this.snapToWalkSurface();
        this.collider.computeWorldMatrix(true);
        this.root.position.copyFrom(this.collider.position);
        this.velocity.setAll(0);
        this.intendedMovement.setAll(0);
        this.movementSinceCollisionSolve.setAll(0);
        this.pendingMovementSecondsS = 0;
        this.collisionBatchAccountedSecondsS = 0;
        this.blockedForS = 0;
        this.recoveryNeeded = false;
        this.recoveryClearTravelM = 0;
        this.blockedDirectionMask = 0;
        this.blockedAttemptWindowS = 0;
        this.autoRecoveryCooldownS = WALK_SURFACE.autoRecoveryCooldownS;
        this.autoRecoveryCount += 1;
        this.autoRecoveryAwaitingRelease = true;
        this.safeTravelM = 0;
        this.safeCandidatePosition.copyFrom(this.collider.position);
        actualX = 0;
        actualZ = 0;
        speed = 0;
      }
    }

    this.indoorBlend = stepWalkIndoorBlend(
      this.indoorBlend,
      this.surfaceKind === "interior",
      deltaMs,
    );
    this.desiredCameraRadiusM = walkCameraRadiusForEnvironment(
      this.preferredCameraRadiusM,
      this.indoorBlend,
    );
    this.cameraSurfaceY = stepWalkCameraSurfaceHeight(
      this.cameraSurfaceY,
      this.surfaceY,
      deltaMs,
    );

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
      (commands.has("forward") || commands.has("backward")) &&
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
      this.cameraSurfaceY +
      WALK_CAMERA.targetHeightM +
      (WALK_CAMERA.closeTargetHeightM - WALK_CAMERA.targetHeightM) * closeBlend;
    // Probe and render from the exact same target height. The newly resolved
    // visibility affects next frame's target, forcing another probe then.
    if (!this.firstPerson) this.updateCameraObstruction(deltaMs);
    this.camera.target.copyFrom(this.cameraTarget);

    this.blendAnimations(speed);
    return speed;
  }

  /**
   * One collision-resolved planar move from the current collider position,
   * split into short substeps with floor snapping after each.
   */
  private moveColliderWithSurface(displacement: Vector3) {
    const substeps = Math.max(
      1,
      Math.ceil(displacement.length() / WALK_CAMERA.maxMoveSubstepM),
    );
    displacement.scaleToRef(1 / substeps, this.movementSubstep);
    this.collider.computeWorldMatrix(true);
    for (let index = 0; index < substeps; index += 1) {
      this.positionBeforeSubstep.copyFrom(this.collider.position);
      this.collider.moveWithCollisions(this.movementSubstep);
      // moveWithCollisions mutates position in place; force the hidden
      // collider's absolute matrix before the next substep/frame. Without
      // this, Babylon can resolve every step from a stale start and tunnel
      // through furniture during a sprint or a deterministic QA loop.
      const surfaceResult = this.snapToWalkSurface();
      if (
        surfaceResult === "blocked-rise" ||
        (surfaceResult === "missing" && !this.surfaceValid)
      ) {
        // A missing floor or an unwalkable rise is an impassable edge, just
        // like a wall. Rewind the individual substep so a lower fallback
        // terrain can never carry the walker through raised geometry.
        this.collider.position.copyFrom(this.positionBeforeSubstep);
        this.surfaceY = this.positionBeforeSubstep.y;
        this.snapToWalkSurface();
      }
      this.collider.computeWorldMatrix(true);
    }
  }

  /**
   * Retries a mostly rejected move on deflected headings. The collider ends
   * on the best candidate (or back on the original result) and the achieved
   * share of the original intent is returned.
   */
  private tryDeflectedMove(intended: Vector3, originalProgress: number) {
    let bestProgress = originalProgress;
    this.deflectedBestPosition.copyFrom(this.collider.position);
    let bestSurfaceY = this.surfaceY;
    const originalSurfaceY = this.positionBeforeMove.y;
    for (const angleRad of DOORWAY_ASSIST.deflectionAnglesRad) {
      const rotated = rotatePlanar({ x: intended.x, z: intended.z }, angleRad);
      this.collider.position.copyFrom(this.positionBeforeMove);
      this.surfaceY = originalSurfaceY;
      this.moveColliderWithSurface(
        this.deflectedSubstep.set(rotated.x, 0, rotated.z),
      );
      const candidateProgress = movementProgress(
        { x: intended.x, z: intended.z },
        {
          x: this.collider.position.x - this.positionBeforeMove.x,
          z: this.collider.position.z - this.positionBeforeMove.z,
        },
      );
      if (
        candidateProgress >= DOORWAY_ASSIST.deflectMinimumProgress &&
        candidateProgress > bestProgress
      ) {
        bestProgress = candidateProgress;
        this.deflectedBestPosition.copyFrom(this.collider.position);
        bestSurfaceY = this.surfaceY;
      }
    }
    this.collider.position.copyFrom(this.deflectedBestPosition);
    this.surfaceY = bestSurfaceY;
    this.snapToWalkSurface();
    this.collider.computeWorldMatrix(true);
    if (bestProgress > originalProgress) this.deflectionCount += 1;
    return bestProgress;
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

  /** Refreshes only moving-door bounds without rescanning the full house. */
  invalidateDynamicCameraOccluders() {
    let refreshed = false;
    this.cameraOccluders = this.cameraOccluders.map((occluder) => {
      const metadata = occluder.mesh.metadata as {
        readonly dynamicCameraOccluder?: boolean;
      } | null;
      if (
        metadata?.dynamicCameraOccluder !== true ||
        occluder.mesh.isDisposed()
      ) {
        return occluder;
      }
      occluder.mesh.computeWorldMatrix(true);
      const bounds = occluder.mesh.getBoundingInfo().boundingBox;
      refreshed = true;
      return {
        mesh: occluder.mesh,
        minimumX: bounds.minimumWorld.x,
        minimumY: bounds.minimumWorld.y,
        minimumZ: bounds.minimumWorld.z,
        maximumX: bounds.maximumWorld.x,
        maximumY: bounds.maximumWorld.y,
        maximumZ: bounds.maximumWorld.z,
      };
    });
    if (refreshed) {
      this.lastProbeTarget.setAll(Number.POSITIVE_INFINITY);
      this.lastCameraHitDistanceM = null;
    }
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
      Math.abs(this.desiredCameraRadiusM - this.lastProbeDesiredRadiusM) > 0.008;
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
    this.lastProbeDesiredRadiusM = this.desiredCameraRadiusM;
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
      this.desiredCameraRadiusM + WALK_CAMERA.collisionProbeRadiusM + 0.04;
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
      ray.length = this.desiredCameraRadiusM;
      for (const occluder of this.nearbyCameraOccluders) {
        const broadDistance = rayBoundsDistance(
          ray.origin,
          direction,
          occluder,
          this.desiredCameraRadiusM,
          0.01,
        );
        if (broadDistance === null || broadDistance >= nearest) continue;
        const pick = ray.intersectsMesh(occluder.mesh, false);
        if (
          pick.hit &&
          Number.isFinite(pick.distance) &&
          pick.distance >= 0 &&
          pick.distance <= this.desiredCameraRadiusM &&
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
    this.desiredCameraRadiusM = walkCameraRadiusForEnvironment(
      this.preferredCameraRadiusM,
      this.indoorBlend,
    );
    this.effectiveCameraRadiusM = this.cameraObstructed
      ? Math.max(
          WALK_CAMERA.obstructionMinRadiusM,
          Math.min(this.desiredCameraRadiusM, observedRadiusM),
        )
      : this.desiredCameraRadiusM;
    this.lastProbeDesiredRadiusM = Number.POSITIVE_INFINITY;
    this.sinceUserOrbitS = 0;
  }

  private updateCameraObstruction(deltaMs: number) {
    this.captureNativePinch();
    const boom = stepWalkCameraBoom({
      desiredRadiusM: this.desiredCameraRadiusM,
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
    this.desiredCameraRadiusM = walkCameraRadiusForEnvironment(
      this.preferredCameraRadiusM,
      this.indoorBlend,
    );
    if (this.desiredCameraRadiusM < this.effectiveCameraRadiusM) {
      this.effectiveCameraRadiusM = this.desiredCameraRadiusM;
      this.camera.radius = this.effectiveCameraRadiusM;
    }
  }

  dispose() {
    for (const rig of this.loadedRigs.values()) {
      for (const group of rig.animationGroups) group.dispose();
    }
    this.loadedRigs.clear();
    this.loadPromises.clear();
    this.camera.dispose();
    this.collider.dispose();
    this.root.dispose(false, true);
  }
}
