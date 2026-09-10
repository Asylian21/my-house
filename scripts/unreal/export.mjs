import { spawn } from "node:child_process";
import { mkdir, rm } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const output = resolve(root, process.env.UNREAL_OUTPUT ?? "output/unreal/geometry");
const blender = process.env.BLENDER_BIN ?? "/Applications/Blender.app/Contents/MacOS/Blender";
await mkdir(output, { recursive: true });
// An interrupted run must never retain an earlier successful validation receipt.
await rm(resolve(output, "validation.json"), { force: true });
await rm(resolve(output, "bridge-report.json"), { force: true });
async function run(bin, args, env = {}) {
  const code = await new Promise((accept, reject) => {
    const child = spawn(bin, args, { cwd: root, stdio: "inherit", env: { ...process.env, ...env } });
    child.once("error", reject);
    child.once("exit", accept);
  });
  if (code !== 0) throw new Error(`${bin} failed (${code})`);
}
await run(process.execPath, ["scripts/archviz/export.mjs"], { ARCHVIZ_OUTPUT: output });
await run(blender, ["--background", "--factory-startup", "--python-exit-code", "1",
  "--python", "scripts/unreal/convert.py", "--", "--output", output]);
await run(process.execPath, ["scripts/unreal/walking.mjs"], { UNREAL_OUTPUT: output });
await run(process.execPath, ["scripts/unreal/exterior-lighting.mjs"], { UNREAL_OUTPUT: output });
await run(process.execPath, ["scripts/unreal/interior-lighting.mjs"], { UNREAL_OUTPUT: output });
await run(process.execPath, ["scripts/unreal/validate.mjs"], { UNREAL_OUTPUT: output });
