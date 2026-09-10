import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { buildWalkingContract, readWalkingConstants } from "../scripts/unreal/walking.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const validatorPath = resolve(root, "scripts/unreal/validate.mjs");

// Tiny valid glTF geometry keeps these integrity tests independent of Blender,
// Chromium, a locally exported house, and a particular developer's output path.
function glbFor(ids) {
  const binary = Buffer.alloc(44);
  [0, 0, 0, 1, 0, 0, 0, 1, 0].forEach((value, index) => binary.writeFloatLE(value, index * 4));
  [0, 1, 2].forEach((value, index) => binary.writeUInt16LE(value, 36 + index * 2));
  const document = {
    asset: { version: "2.0", generator: "unreal-export integrity fixture" },
    scene: 0,
    scenes: [{ nodes: ids.map((_, index) => index) }],
    nodes: ids.map((id) => ({ mesh: 0, extras: { source_object_id: id } })),
    meshes: [{ primitives: [{ attributes: { POSITION: 0 }, indices: 1 }] }],
    buffers: [{ byteLength: binary.length }],
    bufferViews: [
      { buffer: 0, byteOffset: 0, byteLength: 36, target: 34962 },
      { buffer: 0, byteOffset: 36, byteLength: 6, target: 34963 },
    ],
    accessors: [
      { bufferView: 0, componentType: 5126, count: 3, type: "VEC3", min: [0, 0, 0], max: [1, 1, 0] },
      { bufferView: 1, componentType: 5123, count: 3, type: "SCALAR" },
    ],
  };
  const rawJson = Buffer.from(JSON.stringify(document));
  const json = Buffer.alloc(Math.ceil(rawJson.length / 4) * 4, 0x20);
  rawJson.copy(json);
  const header = Buffer.alloc(20);
  header.write("glTF");
  header.writeUInt32LE(2, 4);
  header.writeUInt32LE(28 + json.length + binary.length, 8);
  header.writeUInt32LE(json.length, 12);
  header.write("JSON", 16);
  const binaryHeader = Buffer.alloc(8);
  binaryHeader.writeUInt32LE(binary.length, 0);
  binaryHeader.write("BIN\0", 4);
  return Buffer.concat([header, json, binaryHeader, binary]);
}

async function fixture(t) {
  const output = await mkdtemp(resolve(tmpdir(), "brezi-unreal-integrity-"));
  t.after(() => rm(output, { recursive: true, force: true }));
  const sourceFiles = { "package.json": sha(await readFile(resolve(root, "package.json"))) };
  const scene = {
    schemaVersion: 1, sourceCommit: "fixture", layoutId: "C-fixture", sourceFiles,
    units: "millimetres", coordinateSystem: "right-handed Z-up", sceneCenterMm: { x: 15200, y: 10800 },
    objects: ["Walls", "Windows", "Roof", "Floors", "Pool", "Fence", "Decking", "Site", "Foundations"].map((group, index) => ({
      id: `DOM_${index}`, name: group === "Pool" ? "Pool water" : group, group,
      sourceId: `fixture-${index}`,
      enabled: group !== "Foundations", instances: 1, triangles: 1,
      metadata: group === "Floors" ? { babylonCheckCollisions: false, walkSurface: true, walkSurfaceId: "fixture-floor",
        walkSurfaceKind: "interior", walkSurfaceElevationOffsetM: 0 } : { babylonCheckCollisions: group === "Walls" },
      materialNames: group === "Pool" ? ["real-pool-water"] : ["fixture"],
      boundsMm: group === "Pool"
        ? { min: [-3460, 2600, -12], max: [2540, 5300, -12] }
        : { min: [0, 0, 0], max: [1000, 1000, 0] },
    })),
    summary: { triangles: 9 }, pool: { waterLengthMm: 6000, waterWidthMm: 2700 },
    domain: { parcel: { geometry: { crs: "EPSG:5514", outerRing: [
      { xMm: -606686450, yMm: -1202035560 },
      { xMm: -606686040, yMm: -1202034950 },
      { xMm: -606685750, yMm: -1202034140 },
      { xMm: -606686450, yMm: -1202035560 },
    ] } } },
  };
  const obj = Buffer.from("# integrity fixture, geometry checked in Blender integration\n");
  const viewpoints = Buffer.from(JSON.stringify({ coordinateSystem: "unreal-centimeters", views: [] }));
  scene.objSha256 = sha(obj);
  const report = {
    schemaVersion: 1, status: "geometry-converted", sourceCommit: scene.sourceCommit,
    layoutId: scene.layoutId, sourceObjSha256: scene.objSha256, sourceFiles,
    viewpointsSha256: sha(viewpoints),
    pipelineFiles: { "scripts/unreal/validate.mjs": sha(await readFile(validatorPath)) },
    maxObjImportBoundsErrorMm: 0, maxGlbRoundtripBoundsErrorMm: 0,
    archiveReasons: { DOM_8: "source-disabled-or-technical" }, files: {},
  };
  const writeScene = async () => {
    const bytes = Buffer.from(JSON.stringify(scene));
    report.sceneSha256 = sha(bytes);
    await writeFile(resolve(output, "scene.json"), bytes);
    const viewport = await readFile(resolve(root, "lib/twin-viewport-contract.ts"));
    const walking = buildWalkingContract(scene, readWalkingConstants(viewport.toString("utf8")), {
      sceneSha256: sha(bytes), viewportSha256: sha(viewport),
      writerSha256: sha(await readFile(resolve(root, "scripts/unreal/walking.mjs"))),
    });
    await writeFile(resolve(output, "walking.json"), JSON.stringify(walking));
  };
  const writeReport = () => writeFile(resolve(output, "bridge-report.json"), JSON.stringify(report));
  const writeModel = async (name, ids) => {
    const bytes = glbFor(ids);
    report.files[name] = { sha256: sha(bytes), bytes: bytes.length, objects: ids.length, triangles: ids.length, objectIds: ids };
    await writeFile(resolve(output, name), bytes);
  };
  await writeFile(resolve(output, "dom-mm.obj"), obj);
  await writeFile(resolve(output, "viewpoints.json"), viewpoints);
  await writeScene();
  await writeModel("brezi-twin.glb", scene.objects.filter((o) => o.enabled).map((o) => o.id));
  await writeModel("brezi-archive.glb", ["DOM_8"]);
  await writeReport();
  const run = () => spawnSync(process.execPath, [validatorPath], {
    cwd: root, encoding: "utf8", env: { ...process.env, UNREAL_OUTPUT: output }, timeout: 20_000,
  });
  return { output, scene, report, run, writeScene, writeModel, writeReport };
}

test("Unreal bridge validator accepts an isolated valid container fixture", async (t) => {
  const f = await fixture(t);
  const result = f.run();
  assert.equal(result.status, 0, result.stderr);
  const receipt = JSON.parse(await readFile(resolve(f.output, "validation.json"), "utf8"));
  assert.equal(receipt.status, "geometry-validated");
  assert.equal(receipt.objects, 9);
  assert.match(receipt.verification, /does not verify Unreal import or runtime/);
});

test("modified source manifest fails and removes a previous success receipt", async (t) => {
  const f = await fixture(t);
  await writeFile(resolve(f.output, "validation.json"), '{"status":"geometry-validated"}');
  await writeFile(resolve(f.output, "scene.json"), JSON.stringify({ ...f.scene, layoutId: "changed" }));
  const result = f.run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Source manifest changed after conversion/);
  await assert.rejects(readFile(resolve(f.output, "validation.json")), { code: "ENOENT" });
});

test("stale source hash and modified GLB bytes independently fail integrity checks", async (t) => {
  const f = await fixture(t);
  const originalDigest = f.report.sourceFiles["package.json"];
  f.report.sourceFiles["package.json"] = "0".repeat(64);
  await f.writeReport();
  let result = f.run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Source changed: package.json/);
  f.report.sourceFiles["package.json"] = originalDigest;
  await f.writeReport();
  const bytes = await readFile(resolve(f.output, "brezi-twin.glb"));
  bytes[bytes.length - 1] ^= 1;
  await writeFile(resolve(f.output, "brezi-twin.glb"), bytes);
  result = f.run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /brezi-twin\.glb/);
});

test("duplicate object across active and archive models is rejected even with matching hashes", async (t) => {
  const f = await fixture(t);
  await f.writeModel("brezi-archive.glb", ["DOM_8", "DOM_0"]);
  await f.writeReport();
  const result = f.run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Duplicate object across render\/archive/);
});

test("technical foundation leakage into the active GLB is rejected despite consistent file hashes", async (t) => {
  const f = await fixture(t);
  await f.writeModel("brezi-twin.glb", f.scene.objects.filter((o) => o.id !== "DOM_0").map((o) => o.id));
  await f.writeModel("brezi-archive.glb", ["DOM_0"]);
  await f.writeReport();
  const result = f.run();
  assert.notEqual(result.status, 0, "An archived foundation was accepted in the active render model");
  assert.match(result.stderr, /Archive boundary violated/);
});

test("visible furniture survives misleading legacy Services and Foundations group names", async (t) => {
  const f = await fixture(t);
  f.scene.objects.push(
    { ...f.scene.objects[0], id: "DOM_9", group: "Services", name: "C-GARAGE-FITOUT · UTILITY-SINK · robustná nástenná batéria" },
    { ...f.scene.objects[0], id: "DOM_10", group: "Foundations", name: "OFFICE-FITOUT · MONITOR · subtílna stolová základňa" },
  );
  f.scene.summary.triangles = f.scene.objects.length;
  await f.writeScene();
  await f.writeModel("brezi-twin.glb", f.scene.objects.filter((o) => o.enabled).map((o) => o.id));
  await f.writeReport();
  const result = f.run();
  assert.equal(result.status, 0, result.stderr);
});

test("camera and sunlight sidecar changes invalidate the geometry receipt", async (t) => {
  const f = await fixture(t);
  await writeFile(resolve(f.output, "viewpoints.json"), JSON.stringify({ coordinateSystem: "changed" }));
  const result = f.run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Viewpoints changed after conversion/);
});

test("the pool datum cannot change while preserving only its plan dimensions", async (t) => {
  const f = await fixture(t);
  f.scene.objects.find((o) => o.group === "Pool").boundsMm.min[2] = 120;
  await f.writeScene();
  await f.writeReport();
  const result = f.run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Pool water elevation/);
});

test("walking changes cannot silently override source eye height or collision surfaces", async (t) => {
  const f = await fixture(t);
  const file = resolve(f.output, "walking.json");
  const walking = JSON.parse(await readFile(file, "utf8"));
  walking.eyeHeightCm += 10;
  await writeFile(file, JSON.stringify(walking));
  const result = f.run();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Walking contract differs from the current captured source/);
});
