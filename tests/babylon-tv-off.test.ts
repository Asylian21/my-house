import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { Matrix } from "@babylonjs/core/Maths/math.vector";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { Scene } from "@babylonjs/core/scene";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { buildInterior, type InteriorMaterials } from "../lib/babylon-interior";
import { serializeObj } from "../scripts/archviz/geometry.mjs";

const tvName = "LIVING-103-TV-WALL · 98-palcový televízor · čierne sklo";
const monitorPrefix = "OFFICE-FITOUT-2026-08-29 · MONITOR-40-21:9 · obrazový segment ";

function exportedMaterial(material: PBRMaterial) {
  return { name: material.name, color: material.albedoColor.asArray(), roughness: material.roughness,
    metallic: material.metallic, alpha: material.alpha, texture: material.albedoTexture?.name ?? null,
    emission: material.emissiveColor.asArray() };
}

describe("living TV off state keeps office display glass unchanged", () => {
  let engine: NullEngine, scene: Scene, materials: InteriorMaterials;
  beforeAll(() => {
    engine = new NullEngine();
    scene = new Scene(engine);
    const material = new PBRMaterial("test-context", scene);
    materials = buildInterior({ scene, anisotropy: 1, wall: material, soffit: material,
      glassFrame: material, chimneyMetal: material, timber: material,
      register: (mesh) => mesh, realisticOnly: (mesh) => mesh, castShadow: (mesh) => mesh });
  });
  afterAll(() => { scene.dispose(); engine.dispose(); });

  it("uses black off glass only on the 98-inch TV, preserving all nine emissive office segments", () => {
    const tv = scene.meshes.filter((mesh) => mesh.name === tvName);
    const monitors = scene.meshes.filter((mesh) => mesh.name.startsWith(monitorPrefix));
    expect(tv).toHaveLength(1);
    expect(monitors.map((mesh) => mesh.name)).toEqual(Array.from({ length: 9 }, (_, i) => `${monitorPrefix}${i + 1}`));
    expect(tv[0].material).toBe(materials.blackGlass);
    expect(monitors.every((mesh) => mesh.material === materials.tvScreen)).toBe(true);
    expect(exportedMaterial(materials.tvScreen)).toEqual({ name: "real-interior-tv-screen",
      color: [2 / 255, 5 / 255, 7 / 255], roughness: 0.035, metallic: 0.08, alpha: 1,
      texture: null, emission: [6 / 255, 17 / 255, 25 / 255] });
    expect(exportedMaterial(materials.blackGlass)).toEqual({ name: "real-interior-black-glass",
      color: [12 / 255, 14 / 255, 16 / 255], roughness: 0.08, metallic: 0.1, alpha: 1,
      texture: null, emission: [0, 0, 0] });
    expect([materials.tvScreen.clearCoat.isEnabled, materials.tvScreen.clearCoat.intensity,
      materials.tvScreen.clearCoat.roughness]).toEqual([true, 1, 0.025]);
    expect([materials.blackGlass.clearCoat.isEnabled, materials.blackGlass.clearCoat.intensity,
      materials.blackGlass.clearCoat.roughness]).toEqual([true, 0.8, 0.05]);
  });

  it("exports one changed display binding with identical monitor values and geometry/UV/normals", () => {
    const displays = scene.meshes.filter((mesh) => mesh.material === materials.blackGlass
      || mesh.name.startsWith(monitorPrefix) || mesh.name === tvName);
    const capture = (mesh: AbstractMesh) => {
      const world = mesh.computeWorldMatrix(true);
      return { name: mesh.name, sourceId: mesh.id, enabled: mesh.isEnabled(),
        positions: Array.from(mesh.getVerticesData("position")!), normals: Array.from(mesh.getVerticesData("normal")!),
        uvs: Array.from(mesh.getVerticesData("uv")!), indices: Array.from(mesh.getIndices()!),
        transforms: [Array.from(world.asArray())], normalTransforms: [Array.from(Matrix.Transpose(Matrix.Invert(world)).asArray())],
        materials: [exportedMaterial(mesh.material as PBRMaterial)],
        subMeshes: mesh.subMeshes.map((sub) => ({ start: sub.indexStart, count: sub.indexCount, material: sub.materialIndex })) };
    };
    const current = displays.map(capture);
    // Counterfactual prior binding on the same actual source meshes; no native export is claimed.
    const prior = current.map((mesh) => mesh.name === tvName
      ? { ...mesh, materials: [exportedMaterial(materials.tvScreen)] } : mesh);
    const before = { materials: {}, objects: [] }, after = { materials: {}, objects: [] };
    const beforeObj = [...serializeObj(prior, before)].join("");
    const afterObj = [...serializeObj(current, after)].join("");
    expect(after.materials).toEqual(before.materials);
    const blackGlassSlot = Object.entries(before.materials).find(([, material]) =>
      (material as { name: string }).name === "real-interior-black-glass")![0];
    expect(after.objects).toEqual(before.objects.map((row: { name: string }) => row.name === tvName
      ? { ...row, materialSlots: [blackGlassSlot], materialNames: ["real-interior-black-glass"], group: "Windows" } : row));
    // The existing name-based classifier also changes this object's OBJ group.
    expect(afterObj.replace(/^(usemtl|g) .*$/gm, "")).toBe(beforeObj.replace(/^(usemtl|g) .*$/gm, ""));
  });
});
