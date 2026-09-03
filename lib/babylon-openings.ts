import type { Material } from "@babylonjs/core/Materials/material";
import type { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { CreateBox } from "@babylonjs/core/Meshes/Builders/boxBuilder.pure";
import { CreateCylinder } from "@babylonjs/core/Meshes/Builders/cylinderBuilder.pure";
import type { Mesh } from "@babylonjs/core/Meshes/mesh";
import { TransformNode } from "@babylonjs/core/Meshes/transformNode";
import type { Scene } from "@babylonjs/core/scene";

import {
  hingedDoorActorDisplacement,
  hingedDoorSweepIsClear,
  liftSlideSashLiftM,
  slidingDoorActorDisplacement,
  slidingDoorPathIsClear,
  type AnimatedDoorRegistration,
} from "./babylon-doors";
import type { LayerId, Point2Mm } from "./twin-site";
import { MM_TO_M, sceneXM as xM, sceneZM as zM } from "./twin-render-frame";
import type { WalkPassage } from "./twin-walk-assist";

export type OpeningKind = "window" | "door" | "sliding" | "fixed";

export interface FacadeOpeningStyleInput {
  readonly id: string;
  readonly kind?: OpeningKind;
  readonly frameWidthMm?: number;
}

export interface OpeningInteraction {
  readonly id: string;
  readonly label: string;
}

export function resolveFacadeOpeningStyle(
  opening: FacadeOpeningStyleInput,
  doorOpeningId: string,
): { readonly kind: OpeningKind; readonly frameWidthMm?: number } {
  return {
    kind: opening.id === doorOpeningId ? "door" : opening.kind ?? "window",
    frameWidthMm: opening.frameWidthMm,
  };
}

/**
 * Window and door joinery built the way a real aluminium/timber unit is made:
 * an outer frame seated 150 mm behind the facade face, sashes with their own
 * profiles, an insulated glass pane, a tilt-turn handle, a postformed interior
 * sill board with ears and an exterior aluminium sill with a drip edge.
 */
export interface OpeningSpec {
  readonly name: string;
  /** "Z": the wall runs along plan x and the facade face is a y value; "X": along y, face is x. */
  readonly axis: "Z" | "X";
  readonly faceMm: number;
  readonly centerMm: number;
  readonly widthMm: number;
  readonly heightMm: number;
  readonly sillMm: number;
  /** +1 when the exterior lies toward increasing plan coordinate. */
  readonly outward: -1 | 1;
  readonly wallThicknessMm: number;
  readonly kind: OpeningKind;
  readonly frameMaterial: PBRMaterial;
  /** Visible face width of the perimeter profile; defaults to a standard 78 mm frame. */
  readonly frameWidthMm?: number;
  /** Entity id attached to pickable parts. */
  readonly entityId?: string;
  /** Enables GTA-style walk interaction for a door, slider or portal. */
  readonly interaction?: OpeningInteraction;
  readonly curtains?: boolean;
}

export interface OpeningBuildContext {
  readonly scene: Scene;
  readonly materials: {
    readonly glass: PBRMaterial;
    readonly technicalGlass: Material;
    readonly sillInterior: PBRMaterial;
    readonly sillExterior: PBRMaterial;
    readonly handle: PBRMaterial;
    readonly doorLeaf: PBRMaterial;
    readonly curtain: PBRMaterial;
    readonly track: PBRMaterial;
  };
  register(mesh: AbstractMesh, layer: LayerId, entityId?: string): AbstractMesh;
  realisticOnly(mesh: AbstractMesh): AbstractMesh;
  castShadow(mesh: AbstractMesh): AbstractMesh;
  appearance(mesh: AbstractMesh, technical: Material, realistic: Material): AbstractMesh;
  registerAnimatedDoor?(door: AnimatedDoorRegistration): void;
}

/** Distance of the glazing plane behind the facade face (mm). */
export const GLAZING_PLANE_DEPTH_MM = 150;
const FRAME_DEPTH_MM = 90;
const FRAME_WIDTH_MM = 78;
const SASH_WIDTH_MM = 62;
const SASH_DEPTH_MM = 78;
const GLASS_THICKNESS_MM = 24;

interface Placed {
  readonly alongMm: number;
  readonly acrossMm: number;
}

function solid(
  context: OpeningBuildContext,
  spec: OpeningSpec,
  name: string,
  center: Placed,
  alongMm: number,
  acrossMm: number,
  heightM: number,
  elevationM: number,
  material: Material,
  options: { shadow?: boolean; pickable?: boolean } = {},
) {
  const plan: Point2Mm =
    spec.axis === "Z"
      ? { x: center.alongMm, y: center.acrossMm }
      : { x: center.acrossMm, y: center.alongMm };
  const width = (spec.axis === "Z" ? alongMm : acrossMm) * MM_TO_M;
  const depth = (spec.axis === "Z" ? acrossMm : alongMm) * MM_TO_M;
  const mesh = CreateBox(name, { width, depth, height: heightM }, context.scene);
  mesh.position.set(xM(plan.x), elevationM + heightM / 2, zM(plan.y));
  mesh.material = material;
  mesh.isPickable = options.pickable ?? false;
  mesh.receiveShadows = true;
  context.realisticOnly(mesh);
  if (options.shadow) context.castShadow(mesh);
  context.register(mesh, "building", options.pickable ? spec.entityId : undefined);
  return mesh;
}

/** Rectangular frame of four bars lying in the glazing plane. */
function frameRing(
  context: OpeningBuildContext,
  spec: OpeningSpec,
  label: string,
  startAlong: number,
  endAlong: number,
  bottomMm: number,
  topMm: number,
  barWidthMm: number,
  barDepthMm: number,
  acrossCenterMm: number,
  material: Material,
) {
  const meshes: Mesh[] = [];
  const barHeight = (topMm - bottomMm) * MM_TO_M;
  for (const [side, alongMm] of [
    ["ľavý", startAlong + barWidthMm / 2],
    ["pravý", endAlong - barWidthMm / 2],
  ] as const) {
    meshes.push(solid(
      context,
      spec,
      `${spec.name} · ${label} ${side} stĺpik`,
      { alongMm, acrossMm: acrossCenterMm },
      barWidthMm,
      barDepthMm,
      barHeight,
      bottomMm * MM_TO_M,
      material,
      { shadow: true },
    ));
  }
  for (const [part, elevationMm] of [
    ["spodný", bottomMm],
    ["horný", topMm - barWidthMm],
  ] as const) {
    meshes.push(solid(
      context,
      spec,
      `${spec.name} · ${label} ${part} priečnik`,
      { alongMm: (startAlong + endAlong) / 2, acrossMm: acrossCenterMm },
      endAlong - startAlong - 2 * barWidthMm,
      barDepthMm,
      barWidthMm * MM_TO_M,
      elevationMm * MM_TO_M,
      material,
      { shadow: true },
    ));
  }
  return meshes;
}

function glassPane(
  context: OpeningBuildContext,
  spec: OpeningSpec,
  label: string,
  startAlong: number,
  endAlong: number,
  bottomMm: number,
  topMm: number,
  acrossCenterMm: number,
) {
  const plan: Point2Mm =
    spec.axis === "Z"
      ? { x: (startAlong + endAlong) / 2, y: acrossCenterMm }
      : { x: acrossCenterMm, y: (startAlong + endAlong) / 2 };
  const alongM = (endAlong - startAlong + 16) * MM_TO_M;
  const mesh = CreateBox(
    `${spec.name} · ${label} izolačné dvojsklo`,
    {
      width: spec.axis === "Z" ? alongM : GLASS_THICKNESS_MM * MM_TO_M,
      depth: spec.axis === "Z" ? GLASS_THICKNESS_MM * MM_TO_M : alongM,
      height: (topMm - bottomMm + 16) * MM_TO_M,
    },
    context.scene,
  );
  mesh.position.set(xM(plan.x), ((topMm + bottomMm) / 2) * MM_TO_M, zM(plan.y));
  context.appearance(mesh, context.materials.technicalGlass, context.materials.glass);
  mesh.metadata = { ...(mesh.metadata ?? {}), entityId: spec.entityId };
  mesh.isPickable = true;
  // A moving leaf remains physical while its transform slides it out of the
  // clear opening; collision can no longer be inferred from a Slovak label.
  mesh.checkCollisions = true;
  context.register(mesh, "building");
  return mesh;
}

function handle(
  context: OpeningBuildContext,
  spec: OpeningSpec,
  alongMm: number,
  acrossMm: number,
  elevationM: number,
  vertical: boolean,
) {
  const plan: Point2Mm =
    spec.axis === "Z" ? { x: alongMm, y: acrossMm } : { x: acrossMm, y: alongMm };
  const lever = CreateCylinder(
    `${spec.name} · kľučka`,
    { height: vertical ? 0.3 : 0.13, diameter: 0.02, tessellation: 14 },
    context.scene,
  );
  lever.position.set(xM(plan.x), elevationM, zM(plan.y));
  if (!vertical) {
    // Lever hangs down from its rosette.
    lever.position.y -= 0.05;
  }
  lever.material = context.materials.handle;
  lever.isPickable = false;
  context.realisticOnly(lever);
  context.castShadow(lever);
  context.register(lever, "building");
  const rosette = CreateCylinder(
    `${spec.name} · rozeta kľučky`,
    { height: 0.012, diameter: 0.036, tessellation: 16 },
    context.scene,
  );
  rosette.position.set(xM(plan.x), elevationM + (vertical ? 0.15 : 0.02), zM(plan.y));
  rosette.rotation.x = spec.axis === "Z" ? Math.PI / 2 : 0;
  rosette.rotation.z = spec.axis === "Z" ? 0 : Math.PI / 2;
  rosette.material = context.materials.handle;
  rosette.isPickable = false;
  context.realisticOnly(rosette);
  context.register(rosette, "building");
  return [lever, rosette] as const;
}

function parentAtWorldTransform(meshes: readonly Mesh[], parent: TransformNode) {
  for (const mesh of meshes) {
    const worldPosition = mesh.position.clone();
    mesh.parent = parent;
    mesh.position.copyFrom(worldPosition.subtract(parent.position));
  }
}

function placedWorld(spec: OpeningSpec, alongMm: number, acrossMm: number) {
  return spec.axis === "Z"
    ? { x: xM(alongMm), z: zM(acrossMm) }
    : { x: xM(acrossMm), z: zM(alongMm) };
}

/** Clear walk-through envelope of the operable part of a facade opening. */
function facadePassage(
  spec: OpeningSpec,
  id: string,
  clearCenterAlongMm: number,
  clearWidthMm: number,
  acrossMm: number,
): WalkPassage {
  return {
    id,
    center: placedWorld(spec, clearCenterAlongMm, acrossMm),
    along: spec.axis === "Z" ? { x: 1, z: 0 } : { x: 0, z: 1 },
    halfClearWidthM: (clearWidthMm / 2) * MM_TO_M,
    halfDepthM: (spec.wallThicknessMm / 2) * MM_TO_M,
  };
}

export function buildOpening(context: OpeningBuildContext, spec: OpeningSpec): Mesh[] {
  const { outward } = spec;
  const inward = (depthMm: number) => spec.faceMm - outward * depthMm;
  const start = spec.centerMm - spec.widthMm / 2;
  const end = spec.centerMm + spec.widthMm / 2;
  const top = spec.sillMm + spec.heightMm;
  const planeAcross = inward(GLAZING_PLANE_DEPTH_MM);
  const frame = spec.frameMaterial;
  const frameWidthMm = spec.frameWidthMm ?? FRAME_WIDTH_MM;
  const built: Mesh[] = [];

  if (spec.kind === "window" || spec.kind === "fixed") {
    if (
      !Number.isFinite(frameWidthMm) ||
      frameWidthMm <= 0 ||
      frameWidthMm * 2 >= Math.min(spec.widthMm, spec.heightMm)
    ) {
      throw new Error(`Neplatná pohľadová šírka rámu pre ${spec.name}.`);
    }
    frameRing(context, spec, "rám", start, end, spec.sillMm, top, frameWidthMm, FRAME_DEPTH_MM, planeAcross, frame);
    const innerStart = start + frameWidthMm;
    const innerEnd = end - frameWidthMm;
    const innerBottom = spec.sillMm + frameWidthMm;
    const innerTop = top - frameWidthMm;
    const sashes = spec.kind === "window" ? (spec.widthMm >= 1500 ? 2 : 1) : 0;
    if (sashes === 0) {
      built.push(glassPane(context, spec, "pevné", innerStart, innerEnd, innerBottom, innerTop, planeAcross));
    } else {
      const mullion = sashes === 2 ? 70 : 0;
      const sashWidth = (innerEnd - innerStart - mullion) / sashes;
      if (mullion) {
        solid(
          context,
          spec,
          `${spec.name} · stredový stĺpik`,
          { alongMm: (innerStart + innerEnd) / 2, acrossMm: planeAcross },
          mullion,
          FRAME_DEPTH_MM,
          (innerTop - innerBottom) * MM_TO_M,
          innerBottom * MM_TO_M,
          frame,
        );
      }
      for (let index = 0; index < sashes; index += 1) {
        const sashStart = innerStart + index * (sashWidth + mullion);
        const sashEnd = sashStart + sashWidth;
        const sashAcross = inward(GLAZING_PLANE_DEPTH_MM + 18);
        frameRing(context, spec, `krídlo ${index + 1}`, sashStart, sashEnd, innerBottom, innerTop, SASH_WIDTH_MM, SASH_DEPTH_MM, sashAcross, frame);
        built.push(
          glassPane(
            context,
            spec,
            `krídlo ${index + 1}`,
            sashStart + SASH_WIDTH_MM,
            sashEnd - SASH_WIDTH_MM,
            innerBottom + SASH_WIDTH_MM,
            innerTop - SASH_WIDTH_MM,
            sashAcross,
          ),
        );
        // Tilt-turn handle on the interior face, on the lock side.
        const lockSide = index === 0 ? sashEnd - SASH_WIDTH_MM / 2 : sashStart + SASH_WIDTH_MM / 2;
        handle(
          context,
          spec,
          lockSide,
          inward(GLAZING_PLANE_DEPTH_MM + 18 + SASH_DEPTH_MM / 2 + 14),
          ((innerBottom + innerTop) / 2) * MM_TO_M,
          false,
        );
      }
    }
    if (spec.sillMm === 0) return built;
    // Exterior aluminium sill: 2 mm sheet with a 40 mm projection and a drip
    // edge; slightly sloped away from the frame.
    const extSillDepth = GLAZING_PLANE_DEPTH_MM - FRAME_DEPTH_MM / 2 + 40;
    const extSill = solid(
      context,
      spec,
      `${spec.name} · exteriérový hliníkový parapet`,
      { alongMm: spec.centerMm, acrossMm: spec.faceMm + outward * (40 - extSillDepth / 2) },
      spec.widthMm + 60,
      extSillDepth,
      0.004,
      spec.sillMm * MM_TO_M - 0.006,
      context.materials.sillExterior,
      { shadow: true },
    );
    extSill.rotation[spec.axis === "Z" ? "x" : "z"] = (spec.axis === "Z" ? -1 : 1) * outward * 0.07;
    solid(
      context,
      spec,
      `${spec.name} · okapnica parapetu`,
      { alongMm: spec.centerMm, acrossMm: spec.faceMm + outward * 38 },
      spec.widthMm + 60,
      4,
      0.024,
      spec.sillMm * MM_TO_M - 0.034,
      context.materials.sillExterior,
    );
    for (const alongMm of [start - 30, end + 30]) {
      solid(
        context,
        spec,
        `${spec.name} · bočnica parapetu`,
        { alongMm, acrossMm: spec.faceMm + outward * (40 - extSillDepth / 2) },
        3,
        extSillDepth,
        0.03,
        spec.sillMm * MM_TO_M - 0.006,
        context.materials.sillExterior,
      );
    }
    // Interior postformed sill board with 40 mm ears and a 40 mm nosing.
    const intSillDepth = spec.wallThicknessMm - (GLAZING_PLANE_DEPTH_MM + FRAME_DEPTH_MM / 2) + 40;
    solid(
      context,
      spec,
      `${spec.name} · vnútorný parapet`,
      {
        alongMm: spec.centerMm,
        acrossMm: inward(spec.wallThicknessMm + 40 - intSillDepth / 2),
      },
      spec.widthMm + 80,
      intSillDepth,
      0.038,
      spec.sillMm * MM_TO_M - 0.038,
      context.materials.sillInterior,
      { shadow: true },
    );
  }

  if (spec.kind === "sliding") {
    // Lift-and-slide door: a fixed leaf on the outer track and a sliding leaf
    // on the inner track, meeting with a 50 mm overlap; flush floor track.
    const outerAcross = inward(GLAZING_PLANE_DEPTH_MM - 22);
    const innerAcross = inward(GLAZING_PLANE_DEPTH_MM + 40);
    // Head and side frame.
    for (const [side, alongMm] of [
      ["ľavý", start + FRAME_WIDTH_MM / 2],
      ["pravý", end - FRAME_WIDTH_MM / 2],
    ] as const) {
      solid(context, spec, `${spec.name} · rám ${side} stĺpik`, { alongMm, acrossMm: planeAcross }, FRAME_WIDTH_MM, 150, spec.heightMm * MM_TO_M, 0, frame, { shadow: true });
    }
    solid(context, spec, `${spec.name} · rám horný priečnik`, { alongMm: spec.centerMm, acrossMm: planeAcross }, spec.widthMm - 2 * FRAME_WIDTH_MM, 150, FRAME_WIDTH_MM * MM_TO_M, (spec.heightMm - FRAME_WIDTH_MM) * MM_TO_M, frame, { shadow: true });
    solid(context, spec, `${spec.name} · podlahová koľajnica`, { alongMm: spec.centerMm, acrossMm: planeAcross }, spec.widthMm - 2 * FRAME_WIDTH_MM, 150, 0.022, 0, context.materials.track);
    const leafWidth = (spec.widthMm - 2 * FRAME_WIDTH_MM + 50) / 2;
    const leaves = [
      {
        label: "pevné krídlo",
        startAlong: start + FRAME_WIDTH_MM,
        across: outerAcross,
        moving: false,
      },
      {
        label: "posuvné krídlo",
        startAlong: end - FRAME_WIDTH_MM - leafWidth,
        across: innerAcross,
        moving: true,
      },
    ] as const;
    const movingRoot = spec.interaction
      ? new TransformNode(`${spec.interaction.id} · posuvný vozík`, context.scene)
      : null;
    const movingMeshes: Mesh[] = [];
    const movingCollisionMeshes: Mesh[] = [];
    let movingGlass: Mesh | null = null;
    for (const leaf of leaves) {
      const leafEnd = leaf.startAlong + leafWidth;
      const leafMeshes = frameRing(
        context,
        spec,
        leaf.label,
        leaf.startAlong,
        leafEnd,
        22,
        spec.heightMm - FRAME_WIDTH_MM,
        90,
        70,
        leaf.across,
        frame,
      );
      const glass = glassPane(
        context,
        spec,
        leaf.label,
        leaf.startAlong + 90,
        leafEnd - 90,
        22 + 90,
        spec.heightMm - FRAME_WIDTH_MM - 90,
        leaf.across,
      );
      built.push(glass);
      if (leaf.moving && movingRoot) {
        movingGlass = glass;
        movingMeshes.push(...leafMeshes, glass);
        movingCollisionMeshes.push(...leafMeshes, glass);
      }
    }
    // Vertical pull handle on the sliding leaf, both faces.
    const pullAlong = end - FRAME_WIDTH_MM - leafWidth + 45;
    for (const offset of [-52, 52]) {
      const handles = handle(
        context,
        spec,
        pullAlong,
        innerAcross + outward * offset,
        1.05,
        true,
      );
      if (movingRoot) movingMeshes.push(...handles);
    }
    if (movingRoot && movingGlass && spec.interaction) {
      parentAtWorldTransform(movingMeshes, movingRoot);
      for (const mesh of movingCollisionMeshes) mesh.checkCollisions = true;
      for (const mesh of movingMeshes) {
        mesh.metadata = {
          ...(mesh.metadata ?? {}),
          entityId: spec.interaction.id,
          doorId: spec.interaction.id,
          doorMotion: "SLIDING",
        };
      }
      movingGlass.metadata = {
        ...(movingGlass.metadata ?? {}),
        entityId: spec.interaction.id,
        doorId: spec.interaction.id,
        doorMotion: "SLIDING",
        cameraOccluder: true,
        dynamicCameraOccluder: true,
      };
      const movingStartAlong = end - FRAME_WIDTH_MM - leafWidth;
      const fixedStartAlong = start + FRAME_WIDTH_MM;
      const travelAlongMm = fixedStartAlong - movingStartAlong;
      const closedCenterAlong = movingStartAlong + leafWidth / 2;
      const openCenterAlong = closedCenterAlong + travelAlongMm;
      const closedCenter = placedWorld(spec, closedCenterAlong, innerAcross);
      const openCenter = placedWorld(spec, openCenterAlong, innerAcross);
      const travel = {
        x: openCenter.x - closedCenter.x,
        z: openCenter.z - closedCenter.z,
      };
      context.registerAnimatedDoor?.({
        id: spec.interaction.id,
        label: spec.interaction.label,
        kind: "SLIDING",
        interactionPoint: placedWorld(spec, spec.centerMm, planeAcross),
        // The sliding sash parks over the fixed one, so the walk-through is
        // exactly the sash's own closed footprint.
        passage: facadePassage(
          spec,
          spec.interaction.id,
          closedCenterAlong,
          leafWidth - 2 * 90,
          spec.faceMm - outward * (spec.wallThicknessMm / 2),
        ),
        apply: (progress) => {
          movingRoot.position.x = travel.x * progress;
          movingRoot.position.y = liftSlideSashLiftM(progress);
          movingRoot.position.z = travel.z * progress;
          for (const mesh of movingMeshes) mesh.computeWorldMatrix(true);
        },
        canOpen: (actor, progress = 0) =>
          slidingDoorPathIsClear(
            actor,
            closedCenter,
            openCenter,
            leafWidth * MM_TO_M / 2,
            0.08,
            progress,
            1,
          ),
        canClose: (actor, progress = 1) =>
          slidingDoorPathIsClear(
            actor,
            closedCenter,
            openCenter,
            leafWidth * MM_TO_M / 2,
            0.08,
            progress,
            0,
          ),
        actorDisplacement: (actor, progress) =>
          slidingDoorActorDisplacement(
            actor,
            closedCenter,
            openCenter,
            leafWidth * MM_TO_M / 2,
            0.08,
            progress,
          ),
      });
    }
  }

  if (spec.kind === "door") {
    frameRing(context, spec, "zárubňa", start, end, 0, top, FRAME_WIDTH_MM, 150, planeAcross, frame);
    const leafWidth = Math.round(spec.widthMm * 0.72);
    const leafStart = start + FRAME_WIDTH_MM;
    const sidelightStart = leafStart + leafWidth;
    const leaf = solid(
      context,
      spec,
      `${spec.name} · plné antracitové dverné krídlo`,
      { alongMm: leafStart + leafWidth / 2, acrossMm: planeAcross },
      leafWidth - 6,
      48,
      (top - FRAME_WIDTH_MM - 12) * MM_TO_M,
      0.006,
      context.materials.doorLeaf,
      { shadow: true, pickable: true },
    );
    solid(
      context,
      spec,
      `${spec.name} · stĺpik svetlíka`,
      { alongMm: sidelightStart + 30, acrossMm: planeAcross },
      60,
      150,
      (top - FRAME_WIDTH_MM) * MM_TO_M,
      0,
      frame,
    );
    built.push(glassPane(context, spec, "bočný svetlík", sidelightStart + 60, end - FRAME_WIDTH_MM, 0, top - FRAME_WIDTH_MM, planeAcross));
    const handleMeshes: Mesh[] = [];
    for (const offset of [-40, 40]) {
      handleMeshes.push(
        ...handle(
          context,
          spec,
          sidelightStart - 80,
          planeAcross + outward * offset,
          1.05,
          true,
        ),
      );
    }
    solid(context, spec, `${spec.name} · prah`, { alongMm: spec.centerMm, acrossMm: planeAcross }, spec.widthMm - 2 * FRAME_WIDTH_MM, 150, 0.02, 0, context.materials.track);
    leaf.checkCollisions = true;
    if (spec.interaction) {
      const hingeWorld = placedWorld(spec, leafStart, planeAcross);
      const hinge = new TransformNode(
        `${spec.interaction.id} · exteriérový pánt`,
        context.scene,
      );
      hinge.position.set(hingeWorld.x, 0, hingeWorld.z);
      parentAtWorldTransform([leaf, ...handleMeshes], hinge);
      for (const mesh of handleMeshes) {
        mesh.metadata = {
          ...(mesh.metadata ?? {}),
          entityId: spec.interaction.id,
          doorId: spec.interaction.id,
          doorMotion: "HINGED",
        };
        mesh.isPickable = true;
      }
      leaf.metadata = {
        ...(leaf.metadata ?? {}),
        entityId: spec.interaction.id,
        doorId: spec.interaction.id,
        doorMotion: "HINGED",
        cameraOccluder: true,
        dynamicCameraOccluder: true,
      };
      const openAngleRad =
        (spec.axis === "Z" ? -outward : outward) * (Math.PI / 2);
      const closedEndWorld = placedWorld(
        spec,
        leafStart + leafWidth,
        planeAcross,
      );
      context.registerAnimatedDoor?.({
        id: spec.interaction.id,
        label: spec.interaction.label,
        kind: "HINGED",
        interactionPoint: placedWorld(spec, spec.centerMm, planeAcross),
        // Only the leaf swings; the sidelight is fixed glazing.
        passage: facadePassage(
          spec,
          spec.interaction.id,
          leafStart + leafWidth / 2,
          leafWidth - 6,
          spec.faceMm - outward * (spec.wallThicknessMm / 2),
        ),
        apply: (progress) => {
          // Keep the closed transform canonically +0 even on leaves whose
          // opening direction is negative; strict scene contracts compare it.
          hinge.rotation.y = progress === 0 ? 0 : openAngleRad * progress;
          for (const mesh of handleMeshes) {
            mesh.computeWorldMatrix(true);
          }
          leaf.computeWorldMatrix(true);
        },
        canOpen: (actor, progress = 0) =>
          hingedDoorSweepIsClear(
            actor,
            hingeWorld,
            closedEndWorld,
            openAngleRad,
            0.048,
            progress,
            1,
          ),
        canClose: (actor, progress = 1) =>
          hingedDoorSweepIsClear(
            actor,
            hingeWorld,
            closedEndWorld,
            openAngleRad,
            0.048,
            progress,
            0,
          ),
        actorDisplacement: (actor, progress) =>
          hingedDoorActorDisplacement(
            actor,
            hingeWorld,
            closedEndWorld,
            openAngleRad,
            progress,
            0.048,
          ),
      });
    }
  }

  if (spec.curtains !== false && spec.kind !== "door") {
    const curtainWidthMm = Math.max(150, Math.min(420, spec.widthMm * 0.18));
    for (let index = 0; index < 2; index += 1) {
      solid(
        context,
        spec,
        `${spec.name} · záclona ${index + 1}`,
        {
          alongMm: spec.centerMm + (index === 0 ? -1 : 1) * (spec.widthMm / 2 - curtainWidthMm / 2 - 55),
          acrossMm: inward(spec.wallThicknessMm + 110 + (index % 2) * 18),
        },
        curtainWidthMm,
        16,
        Math.max(0.2, (spec.heightMm - 130) * MM_TO_M),
        (spec.sillMm + 65) * MM_TO_M,
        context.materials.curtain,
      );
    }
  }
  return built;
}
