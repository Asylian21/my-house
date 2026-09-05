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
  const skipped: { name: string; reason: string }[] = [];
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
      skipped.push({ name: mesh.name, reason });
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
        metadata: mesh.metadata,
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
    skipped,
    model: {
      house: site.HOUSE,
      pool: site.GARDEN_POOL,
      fence: site.SITE_FENCE,
      surfaces: site.SITE_SURFACES,
      terraces: site.TERRACE_ZONES_D1,
      poolDeck: site.POOL_SURROUND_DECK,
      poolShaft: site.POOL_TECHNOLOGY_SHAFT,
      foundations: site.FOUNDATIONS,
      utilities: site.UTILITY_ROUTES,
      parcels: site.CADASTRAL_PARCELS,
      lawnCutouts: site.PARCEL_LAWN_INTERIOR_CUTOUTS_MM,
      sources: site.SOURCES,
      originSjtskMm: site.SUBJECT_PARCEL_SJTSK_ORIGIN_MM,
      siteAxis: site.SITE_AXIS,
      sceneCenterMm: SCENE_CENTER_MM,
    },
    camera: {
      position: scene.activeCamera?.position.asArray(),
      target: Vector3.Zero().asArray(),
    },
  };
}

Object.assign(window, { captureArchviz: capture, archvizReady: true });
