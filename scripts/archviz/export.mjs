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

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const output = resolve(root, process.env.ARCHVIZ_OUTPUT ?? "output/archviz");
await mkdir(output, { recursive: true });
const server = await createServer({
  root,
  configFile: false,
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
  const manifest = {
    schemaVersion: 1,
    generatedAt: new Date().toISOString(),
    sourceCommit: execFileSync("git", ["rev-parse", "HEAD"], {
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
  manifest.sourceFiles = {};
  for (const name of (await readdir(resolve(root, "lib")))
    .filter((n) => n.endsWith(".ts"))
    .sort()) {
    manifest.sourceFiles[`lib/${name}`] = createHash("sha256")
      .update(await readFile(resolve(root, "lib", name)))
      .digest("hex");
  }
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
