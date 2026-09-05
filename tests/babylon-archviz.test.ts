import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { Matrix, Quaternion, Vector3 } from "@babylonjs/core/Maths/math.vector";
import { CreateBox } from "@babylonjs/core/Meshes/Builders/boxBuilder.pure";
import { TransformNode } from "@babylonjs/core/Meshes/transformNode";
import { Scene } from "@babylonjs/core/scene";
import { describe, expect, it } from "vitest";

import { anchorToSource, matchingSource, sourceBounds, sourceRestBounds } from "../lib/babylon-archviz";
import { deriveArchvizRenderQualityProfile } from "../lib/twin-viewport-contract";

describe("Blender presentation keeps the live house authoritative", () => {
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
