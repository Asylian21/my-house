import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, writeFile, rm } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import validator from "gltf-validator";
import { buildWalkingContract, readWalkingConstants } from "./walking.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const out = resolve(root, process.env.UNREAL_OUTPUT ?? "output/unreal/geometry");
const sha = (buffer) => createHash("sha256").update(buffer).digest("hex");
await rm(resolve(out, "validation.json"), { force: true });
const sceneBytes = await readFile(resolve(out, "scene.json"));
const scene = JSON.parse(sceneBytes);
const report = JSON.parse(await readFile(resolve(out, "bridge-report.json"), "utf8"));
assert.equal(sha(sceneBytes), report.sceneSha256, "Source manifest changed after conversion");
assert.equal(sha(await readFile(resolve(out, "viewpoints.json"))), report.viewpointsSha256, "Viewpoints changed after conversion");
assert.equal(sha(await readFile(resolve(out, "dom-mm.obj"))), report.sourceObjSha256);
for (const [file, digest] of Object.entries({ ...report.sourceFiles, ...report.pipelineFiles })) {
  assert.equal(sha(await readFile(resolve(root, file))), digest, `Source changed: ${file}`);
}
assert(report.maxObjImportBoundsErrorMm < 0.5);
assert(report.maxGlbRoundtripBoundsErrorMm < 0.5);
const validations = {};
const foundIds = new Set();
for (const [name, info] of Object.entries(report.files)) {
  const glb = await readFile(resolve(out, name));
  assert.equal(sha(glb), info.sha256, name);
  const result = await validator.validateBytes(new Uint8Array(glb), { uri: name, maxIssues: 0 });
  validations[name] = result;
  assert.equal(result.issues.numErrors, 0, JSON.stringify(result.issues));
  assert.equal(result.issues.truncated, false, "glTF validation must inspect the whole asset");
  const gltf = JSON.parse(glb.toString("utf8", 20, 20 + glb.readUInt32LE(12)));
  const ids = gltf.nodes.filter((n) => n.mesh !== undefined).map((n) => n.extras?.source_object_id);
  assert.equal(ids.length, info.objects);
  assert.deepEqual([...ids].sort(), [...info.objectIds].sort());
  for (const id of ids) {
    assert(!foundIds.has(id), `Duplicate object across render/archive: ${id}`);
    foundIds.add(id);
  }
}
assert.deepEqual([...foundIds].sort(), scene.objects.map((o) => o.id).sort());
for (const object of scene.objects) {
  const overlay = ["odlesk vod", "kaustick", "odraz oblohy"].some((s) => object.name.toLowerCase().includes(s));
  const archived = !object.enabled || overlay;
  const filename = archived ? "brezi-archive.glb" : "brezi-twin.glb";
  assert(report.files[filename].objectIds.includes(object.id), `Archive boundary violated: ${object.id}`);
  assert.equal(Boolean(report.archiveReasons[object.id]), archived, `Archive reason mismatch: ${object.id}`);
}
for (const group of ["Walls", "Windows", "Roof", "Floors", "Pool", "Fence", "Decking", "Site", "Foundations"]) {
  assert(scene.objects.some((o) => o.group === group), `Missing group ${group}`);
}
const water = scene.objects.filter((o) => o.materialNames.includes("real-pool-water"));
assert.equal(water.length, 1);
assert.equal(scene.pool.waterLengthMm, 6000);
assert.equal(scene.pool.waterWidthMm, 2700);
assert(Math.abs(water[0].boundsMm.max[0] - water[0].boundsMm.min[0] - 6000) < 0.1);
assert(Math.abs(water[0].boundsMm.max[1] - water[0].boundsMm.min[1] - 2700) < 0.1);
assert(Math.abs(water[0].boundsMm.min[2] + 12) < 0.1, "Pool water elevation");
assert(report.files["brezi-twin.glb"].objectIds.includes(water[0].id), "Pool water must be in the render model");
assert.equal(scene.domain.parcel.geometry.crs, "EPSG:5514");
assert(scene.domain.parcel.geometry.outerRing.every((p) => Number.isSafeInteger(p.xMm) && Number.isSafeInteger(p.yMm)));
const walkingBytes = await readFile(resolve(out, "walking.json"));
const walking = JSON.parse(walkingBytes);
const viewportSource = await readFile(resolve(root, "lib/twin-viewport-contract.ts"));
const expectedWalking = buildWalkingContract(scene, readWalkingConstants(viewportSource.toString("utf8")), {
  sceneSha256: sha(sceneBytes), viewportSha256: sha(viewportSource),
  writerSha256: sha(await readFile(resolve(root, "scripts/unreal/walking.mjs"))),
});
// JSON represents both signed IEEE zeroes as 0; compare the serialized contract.
assert.deepEqual(walking, JSON.parse(JSON.stringify(expectedWalking)), "Walking contract differs from the current captured source");
const receipt = { status: "geometry-validated", generatedAt: new Date().toISOString(),
  sourceCommit: scene.sourceCommit, layoutId: scene.layoutId,
  objects: scene.objects.length, triangles: scene.summary.triangles,
  maxGlbRoundtripBoundsErrorMm: report.maxGlbRoundtripBoundsErrorMm,
  poolMm: [6000, 2700], files: Object.fromEntries(Object.entries(validations).map(([name, r]) => [name, r.issues])),
  walkingSha256: sha(walkingBytes),
  verification: "Khronos glTF validation + Blender roundtrip; this check does not verify Unreal import or runtime" };
await writeFile(resolve(out, "validation.json"), JSON.stringify(receipt, null, 2) + "\n");
console.log(JSON.stringify({ ...receipt, files: Object.fromEntries(Object.entries(receipt.files)
  .map(([name, issues]) => [name, { errors: issues.numErrors, warnings: issues.numWarnings, infos: issues.numInfos, truncated: issues.truncated }])) }, null, 2));
