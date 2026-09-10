import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, mkdir, writeFile, rename, rm } from "node:fs/promises";
import { dirname, isAbsolute, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { walkingBoundsToUnreal } from "./walking.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const ids = ["EXT-TERRACE-WALL-01", "EXT-TERRACE-WALL-02", "EXT-POOL-WALL-01", "EXT-POOL-WALL-02", "EXT-POOL-WALL-03"];
function vector(value, name) {
  assert(Array.isArray(value) && value.length === 3 && value.every(Number.isFinite), `Invalid ${name}`);
  return value;
}
function positive(value, name) {
  assert(Number.isFinite(value) && value > 0, `Invalid ${name}`);
  return value;
}

/** Convert the captured shared lighting design; never infer lamp power from mesh emission. */
export function buildExteriorLighting(scene, sceneSha256) {
  assert.equal(scene.units, "millimetres");
  assert.match(sceneSha256, /^[a-f0-9]{64}$/);
  assert.match(scene.objSha256, /^[a-f0-9]{64}$/);
  const source = scene.exteriorLighting;
  assert.equal(source?.schemaVersion, 1);
  assert.equal(source.provenance, "AUTHORED_VISUALIZATION_PROPOSAL");
  assert.equal(source.coordinateSystem, "PLAN_XY_ELEVATION_Z_MM");
  assert.equal(source.photometricConvention, "UE_CONE_SOLID_ANGLE_LUMENS");
  assert.deepEqual(source.fixtures.map((f) => f.id).sort(), [...ids].sort(), "Exactly the five source fixtures are required");
  const center = scene.sceneCenterMm;
  assert(Number.isFinite(center?.x) && Number.isFinite(center?.y), "Missing scene origin");
  const point = (value) => {
    const [x, y, z] = vector(value, "plan point");
    return [(x - center.x) / 10, (center.y - y) / 10, z / 10];
  };
  const fixtures = source.fixtures.map((fixture) => {
    const matches = scene.objects.filter((o) => o.metadata?.exteriorLightId === fixture.id);
    assert.equal(matches.length, 1, `${fixture.id}: ambiguous/missing source mesh`);
    const mesh = matches[0], body = fixture.geometry, light = fixture.light;
    assert(mesh.enabled && mesh.instances === 1 && mesh.triangles > 0, `${fixture.id}: source mesh unavailable`);
    assert.match(mesh.id, /^DOM_[0-9]{5}$/);
    assert.equal(mesh.name, body.sourceName, `${fixture.id}: source name mismatch`);
    const bodyCenterCm = point(body.bodyCenterPlanMm);
    const bounds = walkingBoundsToUnreal(mesh.boundsMm);
    bodyCenterCm.forEach((n, i) => assert(Math.abs(n - (bounds.min[i] + bounds.max[i]) / 2) <= 0.1,
      `${fixture.id}: fixture centre differs from exported geometry`));
    const axis = vector(body.axisPlan, "fixture cylinder axis");
    assert(axis.filter((n) => Math.abs(n) === 1).length === 1 && axis.every((n) => n === 0 || Math.abs(n) === 1),
      "Fixture cylinder must retain its source cardinal axis");
    positive(body.diameterMm, "fixture diameter");
    positive(body.lengthMm, "fixture length");
    axis.forEach((n, i) => assert(Math.abs(bounds.max[i] - bounds.min[i]
      - (n === 0 ? body.diameterMm : body.lengthMm) / 10) <= 0.1,
    `${fixture.id}: fixture size differs from exported geometry`));
    const [dx, dy, dz] = vector(light.directionPlan, "light direction");
    assert(Math.abs(Math.hypot(dx, dy, dz) - 1) < 1e-6, "Light direction must be normalized");
    assert.equal(light.dayMultiplier, 0);
    assert.equal(light.nightMultiplier, 1);
    assert.equal(light.castsShadows, true);
    positive(light.nominalConeLumens, "lumens");
    assert(light.temperatureK >= 1700 && light.temperatureK <= 12000, "Invalid temperature");
    assert(Number.isFinite(light.innerConeHalfAngleDeg) && light.innerConeHalfAngleDeg >= 0
      && light.innerConeHalfAngleDeg < light.outerConeHalfAngleDeg
      && light.outerConeHalfAngleDeg < 89, "Invalid spotlight half angles");
    positive(light.sourceRadiusMm, "source radius");
    assert(positive(light.attenuationRadiusMm, "attenuation radius") > light.sourceRadiusMm);
    return {
      id: fixture.id, sourceTag: mesh.id, sourceName: mesh.name,
      meshPath: `/Game/Brezi/Geometry/brezi-twin/StaticMeshes/${mesh.id}.${mesh.id}`,
      bodyCenterCm, positionCm: point(light.positionPlanMm), direction: [dx, -dy, dz],
      nominalConeLumens: light.nominalConeLumens, temperatureK: light.temperatureK,
      innerConeHalfAngleDeg: light.innerConeHalfAngleDeg, outerConeHalfAngleDeg: light.outerConeHalfAngleDeg,
      sourceRadiusCm: light.sourceRadiusMm / 10, attenuationRadiusCm: light.attenuationRadiusMm / 10,
      castsShadows: true,
    };
  });
  assert.equal(new Set(fixtures.map((f) => f.sourceTag)).size, fixtures.length, "Source mesh reused by two fixtures");
  return { schemaVersion: 1, provenance: source.provenance, coordinateSystem: "UNREAL_XY_Z_CM",
    sceneSha256, objSha256: scene.objSha256, fixtures };
}

export async function exportExteriorLighting({ rootDir = ROOT,
  scenePath = resolve(rootDir, "output/unreal/geometry/scene.json"),
  outputPath = resolve(dirname(scenePath), "exterior-lighting.json") } = {}) {
  const bytes = await readFile(scenePath), scene = JSON.parse(bytes);
  assert(scene.sourceFiles?.["lib/twin-exterior-lighting.ts"], "Shared lighting source is not captured");
  for (const [name, digest] of Object.entries(scene.sourceFiles)) {
    const path = resolve(rootDir, name), rel = relative(rootDir, path);
    assert(!isAbsolute(rel) && rel !== ".." && !rel.startsWith("../"), "Source path escapes project");
    assert.equal(sha(await readFile(path)), digest, `Source changed since capture: ${name}`);
  }
  assert.equal(sha(await readFile(resolve(dirname(scenePath), "dom-mm.obj"))), scene.objSha256, "Source OBJ changed");
  const contract = buildExteriorLighting(scene, sha(bytes));
  assert.equal(sha(await readFile(scenePath)), contract.sceneSha256, "Scene changed during lighting export");
  const output = JSON.stringify(contract, null, 2) + "\n", temporary = `${outputPath}.${process.pid}.tmp`;
  await mkdir(dirname(outputPath), { recursive: true });
  try { await writeFile(temporary, output); await rename(temporary, outputPath); }
  finally { await rm(temporary, { force: true }); }
  return { outputPath, sha256: sha(output), contract };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const directory = resolve(ROOT, process.env.UNREAL_OUTPUT ?? "output/unreal/geometry");
  const result = await exportExteriorLighting({ scenePath: resolve(directory, "scene.json") });
  console.log(JSON.stringify({ outputPath: result.outputPath, sha256: result.sha256, fixtureCount: result.contract.fixtures.length }));
}
