import { readFile } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const out = resolve(root, process.env.ARCHVIZ_OUTPUT ?? "output/archviz");
const d = JSON.parse(await readFile(resolve(out, "scene.json"), "utf8"));
const obj = await readFile(resolve(out, "dom-mm.obj"));
assert.equal(createHash("sha256").update(obj).digest("hex"), d.objSha256);
for (const group of [
  "Walls",
  "Windows",
  "Roof",
  "Floors",
  "Pool",
  "Fence",
  "Decking",
  "Site",
  "Foundations",
])
  assert(
    d.objects.some((o) => o.group === group),
    `Missing ${group}`,
  );
const water = d.objects.filter((o) =>
  o.materialNames.includes("real-pool-water"),
);
assert.equal(water.length, 1);
const b = water[0].boundsMm;
assert(
  Math.abs(b.max[0] - b.min[0] - d.pool.waterLengthMm) < 0.1,
  "Pool length",
);
assert(Math.abs(b.max[1] - b.min[1] - d.pool.waterWidthMm) < 0.1, "Pool width");
assert(Math.abs(b.min[2] + 12) < 0.1, "Pool elevation");
for (const o of d.objects) {
  assert(o.triangles > 0);
  assert(o.instances > 0);
  assert(Object.values(o.boundsMm).flat().every(Number.isFinite));
  assert(
    !/Ilustračné záhradné prostredie|Orientačný popis parcely/.test(o.name),
    "Sky/label leaked",
  );
}
const report = JSON.parse(
  await readFile(resolve(out, "build-report.json"), "utf8"),
);
assert(report.maxImportBoundsErrorMm < 0.5);
const glb = await readFile(resolve(out, "dom.glb"));
assert.equal(glb.toString("ascii", 0, 4), "glTF");
assert.equal(glb.readUInt32LE(4), 2);
assert.equal(glb.readUInt32LE(8), glb.length);
const gltf = JSON.parse(glb.toString("utf8", 20, 20 + glb.readUInt32LE(12)));
assert.equal(gltf.asset.version, "2.0");
assert.equal(
  gltf.nodes.filter((n) => n.extras?.source_id).length,
  d.objects.length,
);
for (const [file, expected] of Object.entries(d.sourceFiles ?? {})) {
  const hash = createHash("sha256")
    .update(await readFile(resolve(root, file)))
    .digest("hex");
  assert.equal(hash, expected, `Source changed after export: ${file}`);
}
if (process.argv.includes("--render")) {
  const png = await readFile(resolve(out, "garden-final.png"));
  const render = JSON.parse(
    await readFile(resolve(out, "garden-final-report.json"), "utf8"),
  );
  assert.equal(png.toString("ascii", 1, 4), "PNG");
  assert.equal(png.readUInt32BE(16), 3840);
  assert.equal(png.readUInt32BE(20), 2160);
  assert.equal(png[24], 16);
  assert.equal(render.status, "render-complete");
  assert.equal(render.sourceObjSha256, d.objSha256);
  assert(
    render.pipelineFiles?.["build.py"],
    "Missing render recipe provenance",
  );
  for (const [file, expected] of Object.entries(render.pipelineFiles)) {
    const hash = createHash("sha256")
      .update(await readFile(resolve(root, "scripts/archviz", file)))
      .digest("hex");
    assert.equal(
      hash,
      expected,
      `Renderer changed after PNG was made: ${file}`,
    );
  }
  assert.equal(
    createHash("sha256").update(png).digest("hex"),
    render.pngSha256,
  );
}
console.log(
  JSON.stringify(
    {
      objects: d.objects.length,
      triangles: d.summary.triangles,
      poolMm: [6000, 2700],
      maxImportBoundsErrorMm: report.maxImportBoundsErrorMm,
      glbBytes: glb.length,
    },
    null,
    2,
  ),
);
