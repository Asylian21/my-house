#!/usr/bin/env node
/**
 * CPU-only geometry regression for the garage Superb; run from the repo root:
 *   node tools/superb-geometry-check.mjs
 *   node tools/superb-geometry-check.mjs /absolute/path/to/babylon-garage-vehicle.ts
 */
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { createServer, normalizePath } from "vite";
import { NullEngine } from "@babylonjs/core/Engines/nullEngine.js";
import { Scene } from "@babylonjs/core/scene.js";
import { Vector3 } from "@babylonjs/core/Maths/math.vector.js";

const repoRoot = process.cwd();
const argument = process.argv[2] ?? "lib/babylon-garage-vehicle.ts";
const candidatePath = argument.startsWith("/@fs/")
  ? resolve(argument.slice(4))
  : resolve(repoRoot, argument.startsWith("/lib/") ? argument.slice(1) : argument);
const shapePath = join(dirname(candidatePath), "twin-superb-combi.ts");
const cacheDirectory = mkdtempSync(join(tmpdir(), "dom-vehicle-regression-"));
let vite;
let engine;
let scene;

try {
  vite = await createServer({
    root: repoRoot,
    configFile: false,
    cacheDir: cacheDirectory,
    optimizeDeps: { noDiscovery: true, include: [] },
    server: { middlewareMode: true },
    appType: "custom",
  });
  const { buildGarageSuperbVehicle } = await vite.ssrLoadModule(
    "/@fs" + normalizePath(candidatePath),
  );
  const shape = await vite.ssrLoadModule("/@fs" + normalizePath(shapePath));
  engine = new NullEngine();
  scene = new Scene(engine);
  scene.useRightHandedSystem = true;
  const startedAt = performance.now();
  const car = buildGarageSuperbVehicle(scene, {
    realisticOnly: () => {},
    castShadow: () => {},
    register: () => {},
  });
  const buildMs = performance.now() - startedAt;
  car.root.setEnabled(true);
  for (const mesh of scene.meshes) mesh.computeWorldMatrix(true);
  const body = scene.meshes.find(mesh => mesh.metadata?.vehiclePart === "body-shell");
  assert.ok(body, "The body shell must exist.");

  function worldPoints(mesh) {
    const positions = mesh.getVerticesData("position");
    const matrix = mesh.getWorldMatrix();
    assert.ok(positions?.length, mesh.name + " must have geometry.");
    assert.ok(Array.from(positions).every(Number.isFinite), mesh.name + " must be finite.");
    return Array.from({ length: positions.length / 3 }, (_, index) =>
      Vector3.TransformCoordinates(Vector3.FromArray(positions, index * 3), matrix),
    );
  }

  // Bin the actual projected body triangles into 10 cm cells. This checks
  // vertices AND triangle interiors without tens of thousands of mesh raycasts.
  const projectedGrids = new Map();
  function outwardSurfaceDepth(axis, direction, point) {
    const key = axis + "," + direction;
    const axes = [0, 1, 2].filter(value => value !== axis);
    let grid = projectedGrids.get(key);
    if (!grid) {
      grid = new Map();
      const positions = body.getVerticesData("position");
      const indices = body.getIndices();
      for (let index = 0; index < indices.length; index += 3) {
        const triangle = [indices[index], indices[index + 1], indices[index + 2]].map(vertex => [
          positions[vertex * 3 + axes[0]],
          positions[vertex * 3 + axes[1]],
          positions[vertex * 3 + axis] * direction,
        ]);
        const [a, b, c] = triangle;
        const determinant =
          (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1]);
        if (Math.abs(determinant) < 1e-12) continue;
        const entry = { triangle, determinant };
        const u0 = Math.floor(Math.min(a[0], b[0], c[0]) * 10);
        const u1 = Math.floor(Math.max(a[0], b[0], c[0]) * 10);
        const v0 = Math.floor(Math.min(a[1], b[1], c[1]) * 10);
        const v1 = Math.floor(Math.max(a[1], b[1], c[1]) * 10);
        for (let u = u0; u <= u1; u += 1) {
          for (let v = v0; v <= v1; v += 1) {
            const cellKey = u + "," + v;
            const entries = grid.get(cellKey) ?? [];
            entries.push(entry);
            grid.set(cellKey, entries);
          }
        }
      }
      projectedGrids.set(key, grid);
    }
    const xyz = point.asArray();
    const u = xyz[axes[0]], v = xyz[axes[1]];
    const cell = grid.get(Math.floor(u * 10) + "," + Math.floor(v * 10)) ?? [];
    let depth = -Infinity;
    for (const { triangle: [a, b, c], determinant } of cell) {
      const wa =
        ((b[1] - c[1]) * (u - c[0]) + (c[0] - b[0]) * (v - c[1])) / determinant;
      const wb =
        ((c[1] - a[1]) * (u - c[0]) + (a[0] - c[0]) * (v - c[1])) / determinant;
      const wc = 1 - wa - wb;
      if (Math.min(wa, wb, wc) < -1e-7) continue;
      depth = Math.max(depth, wa * a[2] + wb * b[2] + wc * c[2]);
    }
    return depth;
  }

  const panels = scene.meshes.filter(mesh => mesh.metadata?.conformingBodyPanel);
  assert.ok(panels.length >= 30, "The surface regression must cover the glazing and fascia panels.");
  let samplesChecked = 0;
  let minimumClearance = Infinity;
  for (const mesh of panels) {
    const part = mesh.metadata.vehiclePart;
    const vertices = worldPoints(mesh);
    const indices = mesh.getIndices();
    const samples = [...vertices];
    for (let index = 0; index < indices.length; index += 3) {
      samples.push(
        vertices[indices[index]]
          .add(vertices[indices[index + 1]])
          .add(vertices[indices[index + 2]])
          .scale(1 / 3),
      );
    }
    let axis, direction;
    if (["windshield", "rear-window"].includes(part)) {
      axis = 1; direction = 1;
    } else if (["side-glass", "window-pillar"].includes(part)) {
      axis = 2; direction = Math.sign(vertices[0].z);
    } else {
      axis = 0; direction = part.startsWith("rear") ? -1 : 1;
    }
    let checkedForPanel = 0;
    for (const point of samples) {
      const depth = outwardSurfaceDepth(axis, direction, point);
      if (!Number.isFinite(depth)) continue;
      const clearance = point.asArray()[axis] * direction - depth;
      assert.ok(
        clearance > 0.0028,
        mesh.name + " intersects or loses its 3 mm body clearance: " + clearance,
      );
      minimumClearance = Math.min(minimumClearance, clearance);
      checkedForPanel += 1;
    }
    assert.ok(checkedForPanel > 0, mesh.name + " must have a measurable body surface.");
    samplesChecked += checkedForPanel;
  }

  assert.equal(car.wheelSpins.length, 4);
  assert.equal(car.frontSteering.length, 2);
  for (const x of [0.2, 0.45, 0.66, 1.1, 1.5, 1.9]) {
    const epsilon = 1e-5;
    const crown = value => shape.garageSuperbSectionAt(value).roofY;
    const left = (crown(x) - crown(x - epsilon)) / epsilon;
    const right = (crown(x + epsilon) - crown(x)) / epsilon;
    assert.ok(Math.abs(left - right) < 0.002, "Crown tangent must be continuous at " + x);
    assert.ok(
      Math.abs((left + right) / 2) > (x < 1 ? 0.2 : 0.01),
      "Crown must not form a horizontal shelf at " + x,
    );
  }
  const wells = scene.meshes.filter(mesh => mesh.metadata?.vehiclePart === "wheel-well");
  assert.equal(wells.length, 4);
  for (const well of wells) {
    const halfTrack = well.position.x > 0
      ? shape.GARAGE_SUPERB_HALF_TRACKS_M.front
      : shape.GARAGE_SUPERB_HALF_TRACKS_M.rear;
    assert.ok(
      Math.abs(well.position.z) + 0.015 <=
        halfTrack - shape.GARAGE_SUPERB_WHEEL_M.tireWidth / 2 - 0.005,
      "Wheel well disc must remain behind the inner tyre edge.",
    );
  }
  const colliders = scene.meshes.filter(mesh => mesh.metadata?.vehicleCollider);
  assert.equal(colliders.length, 2);
  assert.ok(colliders.every(mesh => mesh.checkCollisions && !mesh.isVisible));

  const minimum = [Infinity, Infinity, Infinity];
  const maximum = [-Infinity, -Infinity, -Infinity];
  for (const mesh of scene.meshes) {
    for (const point of worldPoints(mesh)) {
      const xyz = point.asArray();
      for (let axis = 0; axis < 3; axis += 1) {
        minimum[axis] = Math.min(minimum[axis], xyz[axis]);
        maximum[axis] = Math.max(maximum[axis], xyz[axis]);
      }
    }
  }
  assert.ok(maximum[0] - minimum[0] < 5.0, "The complete car must stay within 5 m.");
  assert.ok(maximum[2] - minimum[2] < 2.1, "Mirrors must stay within the production envelope.");
  console.log(JSON.stringify({
    result: "passed",
    candidate: candidatePath,
    buildMs: Math.round(buildMs),
    panels: panels.length,
    samplesChecked,
    minimumClearanceMm: minimumClearance * 1000,
    meshes: scene.meshes.length,
    triangles: scene.meshes.reduce((count, mesh) => count + mesh.getTotalIndices() / 3, 0),
    bounds: { minimum, maximum },
  }, null, 2));
} finally {
  scene?.dispose();
  engine?.dispose();
  await vite?.close();
  rmSync(cacheDirectory, { recursive: true, force: true });
}
