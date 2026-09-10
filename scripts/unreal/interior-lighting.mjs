import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, mkdir, writeFile, rename, rm } from "node:fs/promises";
import { dirname, isAbsolute, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { walkingBoundsToUnreal } from "./walking.mjs";
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const vec = (v) => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite);
const near = (a, b, tolerance = 0.1) => assert(Math.abs(a - b) <= tolerance, "Source fixture bounds disagree");

/** One source-owned rectangle; no native actor/tag/photometry guessing. */
export function buildInteriorLighting(scene, sceneSha256) {
  assert.equal(scene.units, "millimetres");
  for (const h of [sceneSha256, scene.objSha256]) assert.match(h, /^[a-f0-9]{64}$/);
  const s = scene.interiorLighting;
  assert.equal(s?.schemaVersion, 1);
  assert.equal(s.provenance, "AUTHORED_VISUALIZATION_PROPOSAL");
  assert.equal(s.coordinateSystem, "PLAN_XY_ELEVATION_Z_MM");
  assert.equal(s.photometricConvention, "ONE_SIDED_RECT_LUMENS");
  assert.equal(s.vendorPhotometryAvailable, false);
  assert.equal(s.iesAvailable, false);
  assert.equal(s.fixtures.length, 1);
  const f = s.fixtures[0], g = f.geometry, l = f.light;
  assert.equal(f.id, "INT-KITCHEN-TASK-01");
  assert.equal(f.parentSourceId, "KITCHEN-RUN");
  assert.equal(f.kind, "RECT_UNDERCABINET");
  assert.equal(typeof f.designSourceId, "string");
  assert(f.designSourceId.length > 0);
  assert.equal(g.sourceName, "KITCHEN-RUN · LED lišta pod skrinkami");
  for (const v of [g.bodyCenterPlanMm, g.dimensionsMm, l.positionPlanMm, l.directionPlan, l.widthAxisPlan]) assert(vec(v));
  // This first authored candidate has one closed shape/photometry; edits need a new reviewed contract.
  assert.deepEqual(g.dimensionsMm, [2260, 20, 12]);
  assert.deepEqual(l.directionPlan, [0, 0, -1]);
  assert.deepEqual(l.widthAxisPlan, [1, 0, 0]);
  assert.equal(l.sourceWidthMm, 2260); assert.equal(l.sourceHeightMm, 20);
  assert.equal(l.temperatureK, 3000); near(l.lumens, 678, 1e-9);
  assert.equal(l.attenuationRadiusMm, 2500); assert.equal(l.emitterClearanceMm, 2);
  assert.equal(l.castsShadows, true); assert.equal(l.dayMultiplier, 0); assert.equal(l.nightMultiplier, 1);
  near(l.positionPlanMm[0], g.bodyCenterPlanMm[0], 1e-9);
  near(l.positionPlanMm[1], g.bodyCenterPlanMm[1], 1e-9);
  near(l.positionPlanMm[2], g.bodyCenterPlanMm[2] - g.dimensionsMm[2] / 2 - l.emitterClearanceMm, 1e-9);
  assert(Number.isFinite(scene.sceneCenterMm?.x) && Number.isFinite(scene.sceneCenterMm?.y));
  const point = ([x,y,z]) => [(x-scene.sceneCenterMm.x)/10, (scene.sceneCenterMm.y-y)/10, z/10];
  const tagged = scene.objects.filter((o) => o.metadata?.interiorLightId != null);
  assert.equal(tagged.length, 1, "Exactly one interior light source tag required");
  const mesh = tagged[0];
  assert.equal(mesh.metadata.interiorLightId, f.id);
  assert.equal(mesh.name, g.sourceName); assert.match(mesh.id, /^DOM_[0-9]{5}$/);
  assert(mesh.enabled && mesh.instances === 1 && mesh.triangles === 12);
  const bounds = walkingBoundsToUnreal(mesh.boundsMm), center = point(g.bodyCenterPlanMm);
  center.forEach((n,i) => {
    near(n, (bounds.min[i]+bounds.max[i])/2);
    near(g.dimensionsMm[i]/10, bounds.max[i]-bounds.min[i]);
  });
  return { schemaVersion: 1, provenance: s.provenance, coordinateSystem: "UNREAL_XY_Z_CM",
    photometricConvention: s.photometricConvention, sceneSha256, objSha256: scene.objSha256,
    fixtures: [{ id: f.id, sourceTag: mesh.id, sourceName: mesh.name, designSourceId: f.designSourceId,
      meshPath: `/Game/Brezi/Geometry/brezi-twin/StaticMeshes/${mesh.id}.${mesh.id}`,
      bodyCenterCm: center, bodyDimensionsCm: g.dimensionsMm.map((n) => n/10),
      positionCm: point(l.positionPlanMm), direction: [0,0,-1], widthAxis: [1,0,0],
      sourceWidthCm: l.sourceWidthMm/10, sourceHeightCm: l.sourceHeightMm/10,
      lumens: l.lumens, temperatureK: l.temperatureK, attenuationRadiusCm: l.attenuationRadiusMm/10,
      emitterClearanceCm: l.emitterClearanceMm/10, castsShadows: true, dayMultiplier: 0, nightMultiplier: 1 }] };
}

export async function exportInteriorLighting({ rootDir = ROOT,
  scenePath = resolve(rootDir, "output/unreal/geometry/scene.json"),
  outputPath = resolve(dirname(scenePath), "interior-lighting.json") } = {}) {
  const bytes = await readFile(scenePath), scene = JSON.parse(bytes);
  assert(scene.sourceFiles?.["lib/twin-interior-lighting.ts"], "Shared interior-lighting source not captured");
  for (const [name, digest] of Object.entries(scene.sourceFiles)) {
    const path = resolve(rootDir, name), rel = relative(rootDir, path);
    assert(!isAbsolute(rel) && rel !== ".." && !rel.startsWith("../"));
    assert.equal(sha(await readFile(path)), digest, `Source changed after capture: ${name}`);
  }
  assert.equal(sha(await readFile(resolve(dirname(scenePath), "dom-mm.obj"))), scene.objSha256);
  const contract = buildInteriorLighting(scene, sha(bytes));
  const output = JSON.stringify(contract, null, 2) + "\n", temporary = `${outputPath}.${process.pid}.tmp`;
  assert.equal(sha(await readFile(scenePath)), contract.sceneSha256);
  await mkdir(dirname(outputPath), { recursive: true });
  // The maintained export regenerates this directory. Replace only a fully
  // validated contract, atomically, just like the exterior-lighting exporter.
  try { await writeFile(temporary, output); await rename(temporary, outputPath); }
  finally { await rm(temporary, { force: true }); }
  return { outputPath, sha256: sha(output), contract };
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const directory = resolve(ROOT, process.env.UNREAL_OUTPUT ?? "output/unreal/geometry");
  const result = await exportInteriorLighting({ scenePath: resolve(directory, "scene.json") });
  console.log(JSON.stringify({ outputPath: result.outputPath, sha256: result.sha256, fixtureCount: 1 }));
}
