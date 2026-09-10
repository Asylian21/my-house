import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { VertexBuffer } from "@babylonjs/core/Buffers/buffer";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { Scene } from "@babylonjs/core/scene";
import { describe, expect, it } from "vitest";

import { buildOpening, type OpeningBuildContext, type OpeningSpec } from "../lib/babylon-openings";
import { createFoldedCurtainGeometry, type CurtainGeometry } from "../lib/twin-curtain-geometry";
import { sceneXM, sceneZM } from "../lib/twin-render-frame";

type V3 = [number, number, number];
const point = (values: number[], i: number): V3 => values.slice(i * 3, i * 3 + 3) as V3;
const sub = (a: V3, b: V3): V3 => a.map((v, i) => v - b[i]) as V3;
const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a: V3, b: V3) => a.reduce((sum, v, i) => sum + v * b[i], 0);

/** Independently weld UV/normal seams and check directed geometric edge use. */
function inspectShell(g: CurtainGeometry) {
  const vertices = g.positionsMm.length / 3;
  expect(g.normals).toHaveLength(vertices * 3);
  expect(g.uvs).toHaveLength(vertices * 2);
  expect([...g.positionsMm, ...g.normals, ...g.uvs].every(Number.isFinite)).toBe(true);
  const weld = new Map<string, number>();
  const keys = Array.from({ length: vertices }, (_, i) => {
    const key = point(g.positionsMm, i).map(v => v.toFixed(8)).join(",");
    if (!weld.has(key)) weld.set(key, weld.size);
    expect(Math.hypot(...point(g.normals, i))).toBeCloseTo(1, 10);
    return weld.get(key)!;
  });
  const edges = new Map<string, { count: number; direction: number }>();
  let volume = 0;
  for (let i = 0; i < g.indices.length; i += 3) {
    const ids = g.indices.slice(i, i + 3);
    expect(ids.every(id => Number.isInteger(id) && id >= 0 && id < vertices)).toBe(true);
    const [a, b, c] = ids.map(id => point(g.positionsMm, id));
    const normal = cross(sub(a, b), sub(c, b)); // Babylon clockwise convention.
    expect(Math.hypot(...normal)).toBeGreaterThan(0.001);
    for (const id of ids) expect(dot(normal, point(g.normals, id))).toBeGreaterThan(0);
    const uv = ids.map(id => g.uvs.slice(id * 2, id * 2 + 2));
    expect(Math.abs((uv[1][0] - uv[0][0]) * (uv[2][1] - uv[0][1]) -
      (uv[1][1] - uv[0][1]) * (uv[2][0] - uv[0][0]))).toBeGreaterThan(1e-12);
    volume += dot(a, cross(b, c)) / 6;
    for (let corner = 0; corner < 3; corner += 1) {
      const u = keys[ids[corner]], v = keys[ids[(corner + 1) % 3]];
      const key = `${Math.min(u, v)}:${Math.max(u, v)}`;
      const edge = edges.get(key) ?? { count: 0, direction: 0 };
      edge.count += 1; edge.direction += u < v ? 1 : -1; edges.set(key, edge);
    }
  }
  for (const edge of edges.values()) expect(edge).toEqual({ count: 2, direction: 0 });
  expect(volume).toBeLessThan(0); // Outward clockwise surface, not an inverted shell.
  return -volume;
}

describe("authored gathered curtain geometry", () => {
  it.each([[150, 200], [216, 1170], [378, 2170], [420, 2570]])(
    "preserves %s × %s mm coverage bounds, fabric thickness and closed UV seams",
    (width, height) => {
      const g = createFoldedCurtainGeometry(width, height);
      expect(createFoldedCurtainGeometry(width, height)).toEqual(g);
      expect(g.indices.length / 3).toBeLessThanOrEqual(1000);
      expect(g.foldPitchMm).toBeGreaterThanOrEqual(60);
      expect(g.foldPitchMm).toBeLessThanOrEqual(76);
      const axes = [0, 1, 2].map(axis => g.positionsMm.filter((_, i) => i % 3 === axis));
      for (const [axis, half] of [[0, width / 2], [1, height / 2], [2, 20.35]]) {
        expect(Math.min(...axes[axis])).toBeCloseTo(-half, 8);
        expect(Math.max(...axes[axis])).toBeCloseTo(half, 8);
      }
      const gridSize = (g.horizontalSegments + 1) * (g.verticalSegments + 1);
      for (let i = 0; i < gridSize; i += 1) {
        const separation = sub(point(g.positionsMm, i), point(g.positionsMm, i + gridSize));
        expect(Math.hypot(...separation)).toBeCloseTo(0.7, 9);
        expect(dot(point(g.normals, i), point(g.normals, i + gridSize))).toBeCloseTo(-1, 10);
        expect(dot(separation, point(g.normals, i))).toBeCloseTo(0.7, 9);
      }
      // Offset sheets remain ordered across the opening, without folded-over triangles.
      for (let side = 0; side < 2; side += 1) for (let y = 0; y <= g.verticalSegments; y += 1) {
        for (let x = 1; x <= g.horizontalSegments; x += 1) {
          const i = side * gridSize + y * (g.horizontalSegments + 1) + x;
          expect(g.positionsMm[i * 3]).toBeGreaterThan(g.positionsMm[(i - 1) * 3]);
          expect(g.uvs[i * 2]).toBeGreaterThan(g.uvs[(i - 1) * 2]);
        }
      }
      const volume = inspectShell(g);
      expect(volume).toBeGreaterThan(width * height * 0.7);
      expect(volume).toBeLessThan(width * height * 0.7 * 2.2);
    },
  );

  it("rejects missing faces, reversed winding and invalid input instead of accepting an open or inverted fabric shell", () => {
    const g = createFoldedCurtainGeometry(420, 2170);
    expect(() => inspectShell({ ...g, indices: g.indices.slice(3) })).toThrow();
    const reversed = [...g.indices]; [reversed[0], reversed[1]] = [reversed[1], reversed[0]];
    expect(() => inspectShell({ ...g, indices: reversed })).toThrow();
    for (const dimensions of [[NaN, 200], [150, Infinity], [0, 1000], [150, 0], [4000, 2000]]) {
      expect(() => createFoldedCurtainGeometry(...dimensions as [number, number])).toThrow(RangeError);
    }
  });

  it.each(["Z", "X"] as const)("keeps %s-wall window geometry and two curtain names, order, source centre and material", axis => {
    const engine = new NullEngine({ renderHeight: 64, renderWidth: 64, textureSize: 64 });
    const scene = new Scene(engine), registered: AbstractMesh[] = [];
    const material = (name: string) => new PBRMaterial(name, scene);
    const curtain = material("real-curtain"); curtain.alpha = 0.6; curtain.roughness = 0.96;
    const context: OpeningBuildContext = {
      scene, materials: { glass: material("glass"), technicalGlass: material("technical"), sillInterior: material("inside"),
        sillExterior: material("outside"), handle: material("handle"), doorLeaf: material("door"), curtain, track: material("track") },
      register: mesh => { registered.push(mesh); return mesh; }, realisticOnly: mesh => mesh, castShadow: mesh => mesh,
      appearance: (mesh, _technical, realistic) => { mesh.material = realistic; return mesh; },
    };
    const spec: OpeningSpec = { name: "Test opening", axis, faceMm: 9000, centerMm: 12000, widthMm: 2100,
      heightMm: 2300, sillMm: 200, outward: -1, wallThicknessMm: 530, kind: "fixed", frameMaterial: material("frame") };
    const snapshot = (meshes: AbstractMesh[]) => meshes.map(m => ({ name: m.name, position: m.position.asArray(),
      rotation: m.rotation.asArray(), positions: m.getVerticesData(VertexBuffer.PositionKind), indices: m.getIndices(),
      uvs: m.getVerticesData(VertexBuffer.UVKind), normals: m.getVerticesData(VertexBuffer.NormalKind), material: m.material?.name }));
    try {
      buildOpening(context, { ...spec, curtains: false });
      const baseline = snapshot(registered);
      for (const mesh of [...registered]) mesh.dispose(); registered.length = 0;
      buildOpening(context, spec);
      expect(snapshot(registered.slice(0, -2))).toEqual(baseline);
      const curtains = registered.slice(-2);
      expect(curtains.map(m => m.name)).toEqual(["Test opening · záclona 1", "Test opening · záclona 2"]);
      for (let i = 0; i < 2; i += 1) {
        const m = curtains[i]; m.computeWorldMatrix(true);
        const along = 12000 + (i === 0 ? -1 : 1) * (1050 - 378 / 2 - 55), across = 9000 + 530 + 110 + i * 18;
        const expected = axis === "Z" ? [sceneXM(along), 1.35, sceneZM(across)] : [sceneXM(across), 1.35, sceneZM(along)];
        m.position.asArray().forEach((value, j) => expect(value).toBeCloseTo(expected[j], 10));
        const box = m.getBoundingInfo().boundingBox;
        expect((axis === "Z" ? box.extendSizeWorld.x : box.extendSizeWorld.z) * 2).toBeCloseTo(0.378, 7);
        expect(box.minimumWorld.y).toBeCloseTo(0.265, 7);
        expect(box.maximumWorld.y).toBeCloseTo(2.435, 7);
        expect((axis === "Z" ? box.extendSizeWorld.z : box.extendSizeWorld.x) * 2).toBeLessThan(0.041);
        expect(m.material).toBe(curtain); expect(m.isPickable).toBe(false); expect(m.receiveShadows).toBe(true);
      }
      expect(curtain.alpha).toBe(0.6); expect(curtain.roughness).toBe(0.96);
    } finally { scene.dispose(); engine.dispose(); }
  });
});
