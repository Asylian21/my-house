import { readFileSync } from "node:fs";
import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { Matrix, Quaternion, Vector3 } from "@babylonjs/core/Maths/math.vector";
import { CreateBox } from "@babylonjs/core/Meshes/Builders/boxBuilder.pure";
import { Mesh } from "@babylonjs/core/Meshes/mesh";
import { TransformNode } from "@babylonjs/core/Meshes/transformNode";
import { Scene } from "@babylonjs/core/scene";
import { describe, expect, it } from "vitest";

import { anchorToSource, archvizMaterialForFaces, hasDuplicatedBackFaces, matchingSource, sourceBounds, sourceRestBounds } from "../lib/babylon-archviz";
import { deriveArchvizRenderQualityProfile } from "../lib/twin-viewport-contract";

describe("Blender presentation keeps the live house authoritative", () => {
  it.each([
    ["dom-architecture.glb", "Krytá terasa · štít nad vencom · interiérová omietka"],
    ["dom-interior-01.glb", "1.03 · južný štít podhľadu"],
  ])("isolates corrected gable normals from shared materials in %s", (file, sourceName) => {
    const bytes = readFileSync(new URL(`../public/assets/archviz/${file}`, import.meta.url));
    const gltf = JSON.parse(bytes.subarray(20, 20 + bytes.readUInt32LE(12)).toString());
    const gable = gltf.nodes.find((node: { extras?: { source_name?: string } }) =>
      node.extras?.source_name === sourceName,
    );
    expect(gable).toBeDefined();
    const exported = gltf.materials[gltf.meshes[gable.mesh].primitives[0].material];
    const engine = new NullEngine();
    const scene = new Scene(engine);
    try {
      const material = new PBRMaterial(exported.name, scene);
      material.backFaceCulling = !exported.doubleSided;
      material.twoSidedLighting = !!exported.doubleSided;
      const originalPolicy = [material.backFaceCulling, material.twoSidedLighting];
      const cache = new Map<PBRMaterial, PBRMaterial>();
      const corrected = archvizMaterialForFaces(material, true, cache);
      expect([corrected.backFaceCulling, corrected.twoSidedLighting]).toEqual([true, false]);
      expect(archvizMaterialForFaces(material, true, cache)).toBe(corrected);
      // The same exported material can also serve walls without reverse copies.
      expect(archvizMaterialForFaces(material, false, cache)).toBe(material);
      expect([material.backFaceCulling, material.twoSidedLighting]).toEqual(originalPolicy);
      material.dispose();
      expect(cache.size).toBe(0);
      expect(scene.materials).not.toContain(corrected);
    } finally { scene.dispose(); engine.dispose(); }
  });

  it("detects the complete duplicated back-face layout without changing ordinary solids", () => {
    const engine = new NullEngine();
    const scene = new Scene(engine);
    try {
      const solid = CreateBox("ceiling slab", { size: 1 }, scene);
      const doubled = CreateBox("double-sided solid", { size: 1, sideOrientation: Mesh.DOUBLESIDE }, scene);
      expect(hasDuplicatedBackFaces(solid)).toBe(false);
      expect(hasDuplicatedBackFaces(doubled)).toBe(true);
      expect(hasDuplicatedBackFaces(new Mesh("empty", scene))).toBe(false);
      const plant = new PBRMaterial("intentionally two-sided leaves", scene);
      plant.backFaceCulling = false;
      plant.twoSidedLighting = true;
      const cache = new Map<PBRMaterial, PBRMaterial>();
      const requiresCulling = plant.backFaceCulling && hasDuplicatedBackFaces(doubled);
      expect(archvizMaterialForFaces(plant, requiresCulling, cache)).toBe(plant);
      expect([plant.backFaceCulling, plant.twoSidedLighting]).toEqual([false, true]);
      const glass = new PBRMaterial("transparent pane", scene);
      glass.alpha = 0.2;
      glass.backFaceCulling = false;
      expect(archvizMaterialForFaces(glass, true, cache)).toBe(glass);
      expect(cache.size).toBe(0);
    } finally { scene.dispose(); engine.dispose(); }
  });

  it("bounds GPU surfaces on mobile Retina and large desktop screens", () => {
    for (const [widthPx, heightPx, isCoarsePointer] of [[390, 844, true], [1200, 850, false], [3840, 2160, false]] as const) {
      const profile = deriveArchvizRenderQualityProfile({ widthPx, heightPx, isCoarsePointer, devicePixelRatio: 3, maxMsaaSamples: 8 });
      expect(profile.renderPixelCount).toBeLessThan(2_205_000);
      expect(profile.pixelRatio).toBeLessThanOrEqual(isCoarsePointer ? 1.25 : 1.5);
      expect(profile.msaaSamples).toBe(2);
      expect(profile.hardwareScalingLevel * profile.pixelRatio).toBeCloseTo(1);
    }
  });

  it("converts exported millimetre Z-up bounds without mirroring the house", () => {
    const bounds = sourceBounds({ source_bounds_mm: JSON.stringify({ min: [-2000, 1000, 200], max: [4000, 6000, 3100] }) });
    expect(bounds?.minimum.asArray()).toEqual([-2, 0.2, -6]);
    expect(bounds?.maximum.asArray()).toEqual([4, 3.1, -1]);
  });

  it("distinguishes duplicate door-handle names and rejects a moved architectural source", () => {
    const engine = new NullEngine();
    const scene = new Scene(engine);
    try {
      const a = CreateBox("shared handle", { size: 0.04 }, scene);
      const b = CreateBox("shared handle", { size: 0.04 }, scene);
      a.id = b.id = "handle";
      a.position.set(1, 1.2, -2);
      b.position.set(1, 1.2, -2.12);
      const sources = [a, b].map((mesh) => ({ mesh, ...sourceRestBounds(mesh) }));
      const extras = {
        source_name: "shared handle", source_id: "handle",
        source_bounds_mm: { min: [980, 2100, 1180], max: [1020, 2140, 1220] },
      };
      expect(matchingSource(sources, extras)?.mesh).toBe(b);
      expect(matchingSource(sources, { ...extras, source_bounds_mm: { min: [985, 2100, 1180], max: [1025, 2140, 1220] } })).toBeNull();
    } finally { scene.dispose(); engine.dispose(); }
  });

  it("follows a door opened before its GLB arrives, including non-uniform scale", () => {
    const engine = new NullEngine();
    const scene = new Scene(engine);
    try {
      const hinge = new TransformNode("hinge", scene);
      hinge.position.set(4, 0.2, -3);
      const native = CreateBox("native collision door", { size: 1 }, scene);
      native.parent = hinge;
      native.position.set(0.4, 1, 0);
      native.scaling.set(0.8, 2, 0.05);
      native.checkCollisions = true;
      native.metadata = { doorId: "test-door", cameraOccluder: true };
      const rest = native.computeWorldMatrix(true).clone();
      const importedParent = new TransformNode("glTF parent", scene);
      importedParent.rotationQuaternion = Quaternion.RotationYawPitchRoll(0.3, 0.1, -0.2);
      const visual = CreateBox("textured door", { size: 1 }, scene);
      visual.parent = importedParent;
      visual.position.set(4.4, 1.2, -3);
      visual.scaling.set(0.8, 2, 0.05);
      const originalVisualWorld = visual.computeWorldMatrix(true).clone();
      // Simulate input while the GLB is downloading.
      hinge.rotation.y = 0.8;
      native.computeWorldMatrix(true);
      anchorToSource(visual, native, rest);
      native.visibility = 0;
      for (const angle of [0.8, 1.4, -0.4, 0]) {
        hinge.rotation.y = angle;
        const live = native.computeWorldMatrix(true);
        const expected = originalVisualWorld.multiply(Matrix.Invert(rest)).multiply(live);
        const actual = visual.computeWorldMatrix(true);
        for (const point of [Vector3.Zero(), new Vector3(0.5, 0.5, 0.5), new Vector3(-0.5, 0.2, 0)]) {
          expect(Vector3.Distance(Vector3.TransformCoordinates(point, actual), Vector3.TransformCoordinates(point, expected))).toBeLessThan(0.000002);
        }
      }
      expect(native.checkCollisions).toBe(true);
      expect(native.metadata.doorId).toBe("test-door");
      expect(visual.visibility).toBe(1);
      expect(visual.isEnabled()).toBe(true);
      native.setEnabled(false);
      expect(visual.isEnabled()).toBe(false);
    } finally { scene.dispose(); engine.dispose(); }
  });
});
