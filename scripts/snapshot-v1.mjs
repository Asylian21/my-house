import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// Keep the historical route pinned even when the v1 branch moves later.
const commit = "1057ed30e7a3d5b63a938acf47208ae1f3f296af";
const root = fileURLToPath(new URL("../", import.meta.url));
const git = (...args) => execFileSync("git", args, { cwd: root, maxBuffer: 32 * 1024 * 1024 });
const paths = git("ls-tree", "-r", "--name-only", commit, "app", "lib", "public/assets")
  .toString()
  .trim()
  .split("\n")
  .filter((path) => !["app/chatgpt-auth.ts", "app/layout.tsx", "app/page.tsx"].includes(path));
const files = [];

for (const source of paths) {
  const original = git("show", `${commit}:${source}`);
  const asset = source.startsWith("public/assets/");
  const destination = asset
    ? source.replace("public/assets/", "public/v1-assets/")
    : `versions/v1/${source}`;
  const content = asset
    ? original
    : Buffer.from(original.toString().replaceAll("@/", "@/versions/v1/").replaceAll("/assets/", "/v1-assets/"));
  await mkdir(dirname(resolve(root, destination)), { recursive: true });
  await writeFile(resolve(root, destination), content);
  files.push({
    source,
    destination,
    sha256: createHash("sha256").update(original).digest("hex"),
  });
}

await writeFile(resolve(root, "versions/v1/snapshot.json"), `${JSON.stringify({ commit, files }, null, 2)}\n`);
console.log(`Preserved ${files.length} source files and assets from ${commit}.`);
