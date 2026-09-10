import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { lstat, readFile, readdir } from "node:fs/promises";
import { resolve, relative } from "node:path";
import { promisify } from "node:util";
import { resolveAppLaunch } from "./app-launch.mjs";

const exec = promisify(execFile);
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");

export const requiredUfsDependencies = ["BreziTwin/BreziTwin.uproject", "BreziTwin/Content/Data/viewpoints.json",
  "BreziTwin/Content/Data/walking.json", "BreziTwin/Content/Data/hidden-collision.json",
  "Engine/Content/Internationalization/icudt64l/cnvalias.icu"];

export function assertPackagedUfsDependencies(pakList) {
  for (const file of requiredUfsDependencies) {
    if (!pakList.includes(`"${file}"`)) throw new Error(`Missing packaged UFS dependency: ${file}`);
  }
  return [...requiredUfsDependencies];
}

async function inventory(app) {
  const appStat = await lstat(app);
  if (appStat.isSymbolicLink() || !appStat.isDirectory()) throw new Error("Package root must be a real app directory");
  const files = [];
  async function walk(directory) {
    for (const name of await readdir(directory)) {
      const file = resolve(directory, name);
      const stat = await lstat(file);
      if (stat.isSymbolicLink()) throw new Error(`Package must contain its payload, not symlinks: ${file}`);
      if (stat.isDirectory()) await walk(file);
      else if (stat.isFile()) files.push({ path: relative(app, file), bytes: stat.size });
      else throw new Error(`Package contains a non-regular payload: ${file}`);
    }
  }
  await walk(app);
  return files.sort((a, b) => a.path.localeCompare(b.path));
}

/** Hashing alone does not establish an executable, signed, or standalone package. */
export async function hashPackagedPayload(app) {
  const payloadHashes = {};
  for (const file of await inventory(app)) payloadHashes[file.path] = sha(await readFile(resolve(app, file.path)));
  return payloadHashes;
}

/** Bind a new QA/open operation to every file of the previously validated bundle. */
export async function verifyPackagedPayload(app, bundle) {
  if (bundle?.status !== "bundle-validated" || bundle.payloadHashScope !== "all-bundle-files"
    || !bundle.payloadHashes || !Object.keys(bundle.payloadHashes).length)
    throw new Error("No complete bundle payload receipt; package the application again");
  const actual = await hashPackagedPayload(app);
  const paths = [...new Set([...Object.keys(actual), ...Object.keys(bundle.payloadHashes)])];
  const changed = paths.filter((path) => actual[path] !== bundle.payloadHashes[path]);
  if (changed.length) throw new Error(`Packaged payload changed since validation: ${changed.slice(0, 8).join(", ")}`);
  return { status: "packaged-payload-unchanged", payloadHashScope: "all-bundle-files", fileCount: paths.length,
    payloadHashes: actual };
}

/** A successful UAT archive can still contain only a development executable. */
export async function verifyPackage(app, engine) {
  const files = await inventory(app);
  const required = ["Contents/MacOS/BreziTwin", "Contents/Resources/BreziStartupPolicy.json", "Contents/UE/UECommandLine.txt",
    ...["BreziTwin-Mac.pak", "BreziTwin-Mac.utoc", "BreziTwin-Mac.ucas", "global.utoc", "global.ucas"]
      .map((file) => `Contents/UE/BreziTwin/Content/Paks/${file}`)];
  for (const file of required) {
    if (!files.some((entry) => entry.path === file && entry.bytes > 0)) {
      throw new Error(`Incomplete standalone package: missing ${file}; UAT requires -package before -archive`);
    }
  }
  if (!files.some((entry) => entry.path.endsWith(".dylib"))) throw new Error("No bundled runtime libraries");
  await exec("codesign", ["--verify", "--deep", "--strict", app]);
  const { stdout: highDpi } = await exec("/usr/libexec/PlistBuddy", ["-c", "Print :NSHighResolutionCapable", resolve(app, "Contents/Info.plist")]);
  if (highDpi.trim() !== "true") throw new Error("Native Retina rendering disabled in application plist");
  const { stdout: pakList } = await exec(resolve(engine, "Engine/Binaries/Mac/UnrealPak"),
    [resolve(app, "Contents/UE/BreziTwin/Content/Paks/BreziTwin-Mac.pak"), "-List"], { maxBuffer: 32 * 1024 * 1024 });
  const ufsFiles = assertPackagedUfsDependencies(pakList);
  const launch = await resolveAppLaunch(app);
  const payloadHashes = await hashPackagedPayload(app);
  return { status: "bundle-validated", launch, bytes: files.reduce((sum, file) => sum + file.bytes, 0),
    fileCount: files.length, symbolicLinks: 0, codeSignature: "deep-strict-valid", highDpi: true,
    bundledUfsDependencies: ufsFiles, payloadHashScope: "all-bundle-files", payloadHashes };
}
