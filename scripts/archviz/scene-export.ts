import { ACTIVE_LAYOUT_ID, INTERIOR_ROOMS, INTERIOR_WALLS, INTERIOR_DOORS } from "../../lib/twin-interior";
import { HOUSE as activeHouse } from "../../lib/twin-active-house";
import { BREZI_6012_26_PARCEL, PROVENANCE_KINDS } from "../../lib/twin-domain";
import { SERVICE_CORE_REVISION } from "../../lib/technical-design";
import { EngineStore } from "@babylonjs/core/Engines/engineStore";
import { VertexBuffer } from "@babylonjs/core/Buffers/buffer";
import { Mesh } from "@babylonjs/core/Meshes/mesh";
import { LinesMesh } from "@babylonjs/core/Meshes/linesMesh";
import { Matrix, Vector3 } from "@babylonjs/core/Maths/math.vector";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { StandardMaterial } from "@babylonjs/core/Materials/standardMaterial";
import { MultiMaterial } from "@babylonjs/core/Materials/multiMaterial";
import { createTwinScene } from "../../lib/babylon-scene";
import * as site from "../../lib/twin-site";
import { SCENE_CENTER_MM } from "../../lib/twin-render-frame";
import { DECK_BOARD_LAYOUT } from "../../lib/deck-boards";
import { EXTERIOR_LIGHTING } from "../../lib/twin-exterior-lighting";
import { INTERIOR_LIGHTING } from "../../lib/twin-interior-lighting";

// This page is served only by the local exporter, never by the public app.
const controller = createTwinScene(
  document.querySelector("canvas")!,
  () => {},
  () => {},
  () => {},
  { loadArchviz: false },
);
controller.update({
  foundations: site.FOUNDATIONS,
  selectionId: null,
  visibleLayers: Object.fromEntries(
    site.LAYERS.map((l) => [l.id, true]),
  ) as Record<site.LayerId, boolean>,
  viewMode: "realistic",
});
const scene = EngineStore.LastCreatedScene!;
scene.getEngine().stopRenderLoop();

function capture() {
  const hiddenCollisionMeshes: Record<string, unknown>[] = [];
  const skipped: { name: string; sourceId: string; reason: string; babylonCheckCollisions: boolean;
    cameraOccluder: boolean; walkSurface: boolean; enabled: boolean }[] = [];
  const meshes = scene.meshes.flatMap((mesh) => {
    const positions = mesh.getVerticesData(VertexBuffer.PositionKind);
    const indices = mesh.getIndices();
    const archived =
      site.FOUNDATIONS.some((f) => f.id === mesh.metadata?.entityId) ||
      site.UTILITY_ROUTES.some((r) => r.id === mesh.metadata?.entityId);
    const reason =
      mesh instanceof LinesMesh
        ? "technical-lines"
        : !positions || !indices?.length
          ? "no-triangles"
          : !mesh.isVisible ||
              ((!mesh.isEnabled() || mesh.visibility < 0.01) && !archived)
            ? "hidden-proxy-or-collider"
            : /sky|photodome|Ilustračné záhradné prostredie|Orientačný popis parcely|Pozemné katastrálne čiary|parcel-label|označenie parcely/i.test(
                  mesh.name,
                )
              ? "environment-or-label"
              : null;
    if (reason) {
      if (reason === "hidden-proxy-or-collider" && mesh.isEnabled() && !archived && mesh.checkCollisions) {
        const world = mesh.computeWorldMatrix(true);
        const transforms = mesh instanceof Mesh && mesh.hasThinInstances
          ? mesh.thinInstanceGetWorldMatrices().map((m) => m.multiply(world)) : [world];
        hiddenCollisionMeshes.push({
          name: mesh.name, sourceId: mesh.id, sourceEnabled: true, sourceHidden: true,
          sourceCheckCollisions: true, sourceArchived: false,
          metadata: { ...(mesh.metadata ?? {}), babylonCheckCollisions: mesh.checkCollisions },
          positions: Array.from(positions!), indices: Array.from(indices!),
          normals: Array.from(mesh.getVerticesData(VertexBuffer.NormalKind) ?? []),
          transforms: transforms.map((m) => Array.from(m.asArray())),
          normalTransforms: transforms.map((m) => Array.from(Matrix.Transpose(Matrix.Invert(m)).asArray())),
        });
      }
      skipped.push({ name: mesh.name, sourceId: mesh.id, reason, babylonCheckCollisions: mesh.checkCollisions,
        cameraOccluder: mesh.metadata?.cameraOccluder === true, walkSurface: mesh.metadata?.walkSurface === true,
        enabled: mesh.isEnabled() });
      return [];
    }
    const world = mesh.computeWorldMatrix(true);
    const transforms =
      mesh instanceof Mesh && mesh.hasThinInstances
        ? mesh.thinInstanceGetWorldMatrices().map((m) => m.multiply(world))
        : [world];
    const source =
      mesh.material instanceof MultiMaterial
        ? mesh.material.subMaterials
        : [mesh.material];
    const materials = source.map((m) => {
      const pbr = m instanceof PBRMaterial ? m : null;
      const standard = m instanceof StandardMaterial ? m : null;
      return {
        name: m?.name ?? "unassigned",
        color: (pbr?.albedoColor ?? standard?.diffuseColor)?.asArray() ?? [
          0.5, 0.5, 0.5,
        ],
        roughness: pbr?.roughness ?? 0.6,
        metallic: pbr?.metallic ?? 0,
        alpha: m?.alpha ?? 1,
        texture: pbr?.albedoTexture?.name ?? null,
        emission: (
          pbr?.emissiveColor ?? standard?.emissiveColor
        )?.asArray() ?? [0, 0, 0],
      };
    });
    return [
      {
        name: mesh.name,
        sourceId: mesh.id,
        enabled: mesh.isEnabled() && !archived,
        // Walls deliberately use AbstractMesh.checkCollisions without cameraOccluder metadata.
        // Preserve the actual source property, independent of labels/materials or native guesses.
        metadata: { ...(mesh.metadata ?? {}), babylonCheckCollisions: mesh.checkCollisions },
        positions: Array.from(positions!),
        normals: Array.from(
          mesh.getVerticesData(VertexBuffer.NormalKind) ?? [],
        ),
        uvs: Array.from(mesh.getVerticesData(VertexBuffer.UVKind) ?? []),
        indices: Array.from(indices!),
        transforms: transforms.map((m) => Array.from(m.asArray())),
        materials,
        subMeshes:
          mesh.subMeshes?.map((s) => ({
            start: s.indexStart,
            count: s.indexCount,
            material: s.materialIndex,
          })) ?? [],
        // Inverse-transpose normal matrices preserve non-uniform thin-instance scales.
        normalTransforms: transforms.map((m) =>
          Array.from(Matrix.Transpose(Matrix.Invert(m)).asArray()),
        ),
      },
    ];
  });
  return {
    meshes,
    hiddenCollisionMeshes,
    skipped,
    model: {
      house: activeHouse,
      layoutId: ACTIVE_LAYOUT_ID,
      domain: {
        parcel: BREZI_6012_26_PARCEL,
        provenanceKinds: PROVENANCE_KINDS,
        // Keep national coordinates; the legacy domain local frame is not SITE_AXIS.
        coordinateFrame: "EPSG:5514 integer millimetres",
      },
      revisions: {
        layoutId: ACTIVE_LAYOUT_ID,
        garageDepth: site.GARAGE_DEPTH_REVISION,
        serviceCore: SERVICE_CORE_REVISION,
        state: "checked-out source; browser-local edits are not included",
      },
      interior: { rooms: INTERIOR_ROOMS, walls: INTERIOR_WALLS, doors: INTERIOR_DOORS },
      pool: site.GARDEN_POOL,
      exteriorLighting: EXTERIOR_LIGHTING,
      interiorLighting: INTERIOR_LIGHTING,
      fence: site.SITE_FENCE,
      surfaces: site.SITE_SURFACES,
      terraces: site.TERRACE_ZONES_D1,
      poolDeck: site.POOL_SURROUND_DECK,
      deckBoardLayout: DECK_BOARD_LAYOUT,
      poolShaft: site.POOL_TECHNOLOGY_SHAFT,
      foundations: site.FOUNDATIONS,
      utilities: site.UTILITY_ROUTES,
      parcels: site.CADASTRAL_PARCELS,
      lawnCutouts: site.PARCEL_LAWN_INTERIOR_CUTOUTS_MM,
      sources: site.SOURCES,
      originSjtskMm: site.SUBJECT_PARCEL_SJTSK_ORIGIN_MM,
      siteAxis: site.SITE_AXIS,
      sceneCenterMm: SCENE_CENTER_MM,
      collisionProvenance: {
        checkCollisionsSource: "Babylon AbstractMesh.checkCollisions at scene capture",
        exportedCheckCollisionObjects: meshes.filter((mesh) => mesh.metadata.babylonCheckCollisions).length,
        skippedEnabledCheckCollisionObjects: skipped.filter((mesh) => mesh.enabled && mesh.babylonCheckCollisions).length,
        policy: "Export existing visible source triangles and their collision property; skipped hidden proxies are recorded, not invented or merged into visual geometry.",
      },
    },
    camera: {
      position: scene.activeCamera?.position.asArray(),
      target: Vector3.Zero().asArray(),
    },
  };
}

Object.assign(window, { captureArchviz: capture, archvizReady: true });
