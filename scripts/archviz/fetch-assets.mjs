import { readFile, writeFile, mkdir } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";

const here = dirname(fileURLToPath(import.meta.url));
const lock = JSON.parse(
  await readFile(resolve(here, "assets.lock.json"), "utf8"),
);
const output = resolve(
  here,
  "../../",
  process.env.ARCHVIZ_OUTPUT ?? "output/archviz",
  "assets",
);
const files = [];
for (const asset of Object.values(lock.assets))
  files.push(...Object.values(asset.maps));
for (const model of Object.values(lock.models))
  files.push(model, ...Object.values(model.include));
console.log("Powered by Poly Haven · CC0 · verified asset lock");
let downloaded = 0,
  cached = 0;
async function fetchOne(file) {
  const path = resolve(output, file.path);
  const checksum = (buffer) => createHash("md5").update(buffer).digest("hex");
  try {
    if (checksum(await readFile(path)) === file.md5) {
      cached++;
      return;
    }
  } catch {
    /* Missing cache entry is downloaded below. */
  }
  const response = await fetch(file.url, {
    headers: { "User-Agent": "DOM-ArchViz/1.0" },
    signal: AbortSignal.timeout(120000),
  });
  if (!response.ok) throw new Error(`${response.status}: ${file.url}`);
  const data = Buffer.from(await response.arrayBuffer());
  if (checksum(data) !== file.md5)
    throw new Error(`Asset checksum mismatch: ${file.path}`);
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, data);
  downloaded++;
}
for (let i = 0; i < files.length; i += 4) {
  const results = await Promise.allSettled(files.slice(i, i + 4).map(fetchOne));
  const failed = results.find((r) => r.status === "rejected");
  if (failed) throw failed.reason;
}
console.log(
  JSON.stringify({ files: files.length, downloaded, cached, output }),
);
