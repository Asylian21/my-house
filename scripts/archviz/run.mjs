import { spawn } from "node:child_process";
import { access, mkdir } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "../..");
const [command = "render", ...rest] = process.argv.slice(2);
const output = resolve(root, process.env.ARCHVIZ_OUTPUT ?? "output/archviz");
await mkdir(output, { recursive: true });
const run = (bin, args) =>
  new Promise((resolve, reject) => {
    const child = spawn(bin, args, {
      cwd: root,
      stdio: "inherit",
      env: { ...process.env, PLAYWRIGHT_SKIP_BROWSER_GC: "1" },
    });
    child.on("error", reject);
    child.on("exit", (code) =>
      code === 0 ? resolve() : reject(new Error(`${bin} exited ${code}`)),
    );
  });
let blender = process.env.BLENDER_BIN;
if (!blender) {
  try {
    await access("/Applications/Blender.app/Contents/MacOS/Blender");
    blender = "/Applications/Blender.app/Contents/MacOS/Blender";
  } catch {
    blender = "blender";
  }
}
if (command === "setup") {
  await run(process.execPath, [
    resolve(root, "node_modules/playwright/cli.js"),
    "install",
    "chromium",
    "--only-shell",
  ]);
  await run(process.execPath, [resolve(here, "fetch-assets.mjs")]);
  await run(blender, ["--version"]);
} else if (command === "open") {
  const args = [
    resolve(output, "dom-archviz.blend"),
    "--python",
    resolve(here, "open.py"),
  ];
  if (
    process.platform === "darwin" &&
    blender.endsWith("/Contents/MacOS/Blender")
  )
    await run("open", [
      "-n",
      "-a",
      resolve(dirname(blender), "../.."),
      "--args",
      ...args,
    ]);
  else await run(blender, args);
} else if (["preview", "render", "build"].includes(command)) {
  await run(process.execPath, [resolve(here, "fetch-assets.mjs")]);
  await run(process.execPath, [resolve(here, "export.mjs")]);
  await run(blender, [
    "--background",
    "--factory-startup",
    "--python-exit-code",
    "1",
    "--python",
    resolve(here, "build.py"),
    "--",
    "--output",
    output,
    "--quality",
    command === "preview" ? "preview" : "final",
    ...(command === "build" ? [] : ["--render"]),
    ...rest,
  ]);
} else throw new Error("Expected setup, build, preview, render, or open");
