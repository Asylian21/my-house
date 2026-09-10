import { createServer } from "vite";
import { chromium } from "playwright";
import { mkdir, writeFile, readFile, readdir } from "node:fs/promises";
import { createWriteStream } from "node:fs";
import { once } from "node:events";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import proj4 from "proj4";
import { serializeObj, classify } from "./geometry.mjs";
import { buildHiddenCollisionGlb } from "../unreal/hidden-collision-export.mjs";
import gltfValidator from "gltf-validator";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const output = resolve(root, process.env.ARCHVIZ_OUTPUT ?? "output/archviz");
await mkdir(output, { recursive: true });
async function sourceHashes() {
  const names = (await readdir(resolve(root, "lib")))
    .filter((name) => name.endsWith(".ts")).sort().map((name) => `lib/${name}`);
  names.push("scripts/archviz/export.mjs", "scripts/archviz/scene-export.ts", "scripts/archviz/geometry.mjs", "scripts/unreal/hidden-collision-export.mjs", "scripts/unreal/interior-lighting.mjs", "package-lock.json");
  return Object.fromEntries(await Promise.all(names.map(async (name) => [name,
    createHash("sha256").update(await readFile(resolve(root, name))).digest("hex")])));
}
// Capture a stable input snapshot before Vite reads modules, and reject edits
// during capture rather than assigning fresh hashes to an older loaded scene.
const capturedSourceFiles = await sourceHashes();
const server = await createServer({
  root,
  configFile: false,
  // Export and the user's preview may run together; each needs its own optimizer cache.
  cacheDir: resolve(root, "node_modules/.vite-archviz"),
  publicDir: "public",
  server: { host: "127.0.0.1", port: 0 },
  logLevel: "error",
});
let browser;
try {
  await server.listen();
  const address = server.httpServer.address();
  browser = await chromium.launch({
    headless: true,
    args: [
      "--enable-webgl",
      "--ignore-gpu-blocklist",
      "--use-gl=angle",
      "--use-angle=swiftshader",
      "--enable-unsafe-swiftshader",
    ],
  });
  const page = await browser.newPage({
    viewport: { width: 1280, height: 720 },
  });
  page.on("pageerror", (e) => console.error(e.message));
  await page.goto(
    `http://127.0.0.1:${address.port}/scripts/archviz/export.html`,
  );
  await page.waitForFunction(() => window.archvizReady, undefined, {
    timeout: 180000,
  });
  const data = await page.evaluate(() => window.captureArchviz());
  if (JSON.stringify(await sourceHashes()) !== JSON.stringify(capturedSourceFiles)) {
    throw new Error("Source changed during scene capture; rerun the export");
  }
  const manifest = {
    schemaVersion: 1,
    generatedAt: new Date().toISOString(),
    sourceCommit: execFileSync("git", ["rev-parse", "HEAD"], {
      cwd: root,
      encoding: "utf8",
    }).trim(),
    sourceWorktreeStatus: execFileSync("git", ["status", "--short", "--", "lib", "scripts/archviz"], {
      cwd: root,
      encoding: "utf8",
    }).trim(),
    units: "millimetres",
    coordinateSystem: "right-handed Z-up",
    axes: "OBJ X=planX-15200, Y=planY-10800, Z=elevation; Blender import scale=0.001",
    precision:
      "Source dimensions preserved as integer mm; rendered float32 vertices retain sub-mm tolerance.",
    ...data.model,
    skipped: data.skipped,
    objects: [],
    materials: {},
  };
  manifest.sourceFiles = capturedSourceFiles;
  // EPSG:5514 S-JTSK/Krovak East North (same frame as twin-site).
  proj4.defs(
    "EPSG:5514",
    "+proj=krovak +lat_0=49.5 +lon_0=24.83333333333333 +alpha=30.28813975277778 +k=0.9999 +x_0=0 +y_0=0 +ellps=bessel +towgs84=589,76,480,0,0,0,0 +units=m +no_defs",
  );
  const origin = data.model.originSjtskMm;
  const ll = proj4("EPSG:5514", "EPSG:4326", [
    origin.x / 1000,
    origin.y / 1000,
  ]);
  const north = proj4("EPSG:4326", "EPSG:5514", [ll[0], ll[1] + 0.001]);
  const dx = north[0] - origin.x / 1000,
    dy = north[1] - origin.y / 1000;
  const a = data.model.siteAxis;
  manifest.geolocation = {
    latitude: ll[1],
    longitude: ll[0],
    timezone: "Europe/Prague",
    northAngleRadians: Math.atan2(dx * a.ux + dy * a.uy, dx * a.vx + dy * a.vy),
    method:
      "EPSG:5514 projection with 3-parameter datum approximation; true-north probe in WGS84",
    accuracy: "Geographic lighting location, not a surveying transformation.",
  };
  const stream = createWriteStream(resolve(output, "dom-mm.obj"));
  const hash = createHash("sha256");
  let triangles = 0;
  for (const chunk of serializeObj(data.meshes, manifest)) {
    hash.update(chunk);
    if (!stream.write(chunk)) await once(stream, "drain");
  }
  stream.end();
  await once(stream, "finish");
  manifest.objSha256 = hash.digest("hex");
  for (const object of manifest.objects) triangles += object.triangles;
  manifest.summary = {
    objects: manifest.objects.length,
    triangles,
    instances: manifest.objects.reduce((n, o) => n + o.instances, 0),
    groups: [
      ...new Set(
        manifest.objects.map((o) => classify(o.name, o.materialNames[0] ?? "")),
      ),
    ],
  };
  await writeFile(
    resolve(output, "scene.json"),
    JSON.stringify(manifest, null, 2),
  );
  // Independent supplemental namespace: never append these hulls to serializeObj(data.meshes).
  const hiddenCapture = { mainObjSha256: manifest.objSha256, colliders: data.hiddenCollisionMeshes };
  const hidden = buildHiddenCollisionGlb(manifest, hiddenCapture,
    createHash("sha256").update(await readFile(resolve(output, "scene.json"))).digest("hex"));
  const hiddenValidation = await gltfValidator.validateBytes(new Uint8Array(hidden.glb), { maxIssues: 0 });
  if (hiddenValidation.issues.numErrors || hiddenValidation.issues.numWarnings || hiddenValidation.issues.truncated)
    throw new Error("Hidden collision GLB did not pass full Khronos validation");
  await writeFile(resolve(output, "hidden-collision-source.json"), JSON.stringify(hiddenCapture));
  await writeFile(resolve(output, "brezi-collision-only.glb"), hidden.glb);
  await writeFile(resolve(output, "hidden-collision.json"), JSON.stringify({ ...hidden.contract,
    sourceCaptureSha256: createHash("sha256").update(JSON.stringify(hiddenCapture)).digest("hex"),
    gltfValidation: hiddenValidation.issues }, null, 2));
  const mtl = Object.entries(manifest.materials)
    .map(
      ([id, m]) =>
        `newmtl ${id}\nKd ${m.color.join(" ")}\nPr ${m.roughness}\nPm ${m.metallic}\nd ${m.alpha}\n`,
    )
    .join("\n");
  await writeFile(resolve(output, "dom-mm.mtl"), mtl);
  console.log(
    JSON.stringify(
      { output, ...manifest.summary, geolocation: manifest.geolocation },
      null,
      2,
    ),
  );
} finally {
  await browser?.close();
  await server.close();
}
