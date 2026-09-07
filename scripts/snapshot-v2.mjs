import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// The v2 branch preserves the complete repository at this commit. The public
// routes use a pinned copy so subsequent work on main cannot change this model.
const commit = "0bcbb57774fd551137c2b596a899a0432b148f28";
const root = fileURLToPath(new URL("../", import.meta.url));
const git = (...args) => execFileSync("git", args, { cwd: root, maxBuffer: 32 * 1024 * 1024 });
const replacements = [
  ["@/", "@/versions/v2/"],
  ["/assets/", "/v2-assets/assets/"],
  ['"/archviz/', '"/v2-assets/archviz/'],
  ["/koncept-2d", "/v2/koncept-2d"],
  ['href="/"', 'href="/v2"'],
];
const paths = git("ls-tree", "-r", "--name-only", commit, "app", "lib", "public")
  .toString()
  .trim()
  .split("\n")
  .filter((path) =>
    !["app/chatgpt-auth.ts", "app/layout.tsx"].includes(path)
    && !/^app\/v\d+\//.test(path)
    && !/^public\/v\d+-assets\//.test(path));
const files = [];

for (const source of paths) {
  const original = git("show", `${commit}:${source}`);
  const asset = source.startsWith("public/");
  const destination = asset
    ? source.replace("public/", "public/v2-assets/")
    : `versions/v2/${source}`;
  const content = asset
    ? original
    : Buffer.from(replacements.reduce((text, [from, to]) => text.replaceAll(from, to), original.toString()));
  await mkdir(dirname(resolve(root, destination)), { recursive: true });
  await writeFile(resolve(root, destination), content);
  files.push({ source, destination, sha256: createHash("sha256").update(original).digest("hex") });
}

await writeFile(resolve(root, "versions/v2/snapshot.json"), `${JSON.stringify({ branch: "v2", commit, replacements, files }, null, 2)}\n`);
console.log(`Preserved ${files.length} source files and assets from ${commit}.`);
