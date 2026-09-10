import { spawn, execFile } from "node:child_process";
import { access, mkdir, copyFile, readdir, readFile, writeFile, rm, rename } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";
import { promisify } from "node:util";
import { verifyPackage } from "./package-verify.mjs";
import { inspectLauncherExecution, requireIdleApp } from "./app-launch.mjs";
import { sealStartupEntry } from "./startup-entry-package.mjs";
import { inspectCookLog } from "./cook-log.mjs";
import { inspectPresentation } from "./presentation-qa.mjs";
import { inspectAntiAliasing } from "./antialiasing-qa.mjs";
import { inspectAXInitializer } from "./ax-initializer-qa.mjs";
import { validateTVOakReceipt } from "./tv-oak/package-gate.mjs";
import { validateFurnitureOakReceipt } from "./furniture-oak/package-gate.mjs";
import { validatePendantEmitterReceipt } from "./pendant-emitter/package-gate.mjs";
import { validateLawnDetailReceipt } from "./lawn-detail/package-gate.mjs";
import { validateLawnGroundReceipt } from "./lawn-ground/package-gate.mjs";
import { validateMulchReceipt } from "./planting-surfaces/package-gate.mjs";
import { validateOrnamentalReceipt } from "./ornamental-grass/package-gate.mjs";
import { validatePlasterReceipt } from "./facade-plaster/package-gate.mjs";
import { validatePoolCopingReceipt } from "./pool-coping/package-gate.mjs";
import { guardLegacyContinuousBuild } from "./caustics/build-gate.mjs";
import { loadSelectedPackage, verifySelectedPackage, renderProfileForAction } from "./package-resolver.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const engine = resolve(process.env.UNREAL_ENGINE_ROOT ?? "/Users/Shared/Epic Games/UE_5.8");
const project = resolve(root, "unreal/BreziTwin/BreziTwin.uproject");
const output = resolve(root, process.env.UNREAL_OUTPUT ?? "output/unreal/geometry");
const packaged = resolve(root, "output/unreal/package");
const [action, view = "street", ...qaOptions] = process.argv.slice(2);
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const exec = promisify(execFile);
const renderProfile = renderProfileForAction(action);
if ((process.env.BREZI_PACKAGE_REPORT !== undefined || process.env.BREZI_PACKAGE_REPORT_SHA256 !== undefined)
  && !["open", "qa", "qa-ui", "package-check"].includes(action))
  throw new Error("Explicit package selection is supported only by open, qa, qa-ui or package-check");
await guardLegacyContinuousBuild({ action, projectFile: project, engine });
async function requireIdleRenderer() {
  await requireIdleApp();
  let running;
  try { running = (await exec("pgrep", ["-x", "BreziTwin"])).stdout.trim(); }
  catch (error) { if (error.code !== 1) throw error; }
  if (running) throw new Error(`BreziTwin is already running (PID ${running.replaceAll("\n", ", ")}); close it before a standalone benchmark`);
}
async function nativeSources() {
  const files = {};
  async function scan(directory, skipped = new Set(["FileOpenOrder"])) {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      const file = resolve(directory, entry.name);
      if (entry.isDirectory() && !skipped.has(entry.name)) await scan(file, skipped);
      else if (entry.isDirectory()) continue; // Cooker-generated ordering logs, not source.
      else if (!entry.name.endsWith(".PackageVersionCounter") && entry.name !== ".DS_Store") {
        files[file.slice(root.length + 1)] = sha(await readFile(file));
      }
    }
  }
  for (const directory of ["Source", "Config", "Build"]) await scan(resolve(root, "unreal/BreziTwin", directory));
  // Optional project plugins carry native code, shaders and immutable resources.
  // Their generated binaries/intermediates are build output, never source pins.
  for (const directory of ["scripts/unreal/caustics", "scripts/unreal/engine-overlays/ue-5.8.2-floor-caustics"])
    await scan(resolve(root, directory), new Set(["__pycache__"]));
  const plugins = resolve(root, "unreal/BreziTwin/Plugins");
  let pluginsPresent = true;
  try { await access(plugins); }
  catch (error) { if (error.code !== "ENOENT") throw error; pluginsPresent = false; }
  if (pluginsPresent) await scan(plugins, new Set(["Binaries", "Intermediate", "Saved", "DerivedDataCache", "__pycache__", ".git"]));
  files["scripts/unreal/pool-coping/package-gate.mjs"] = sha(await readFile(resolve(root, "scripts/unreal/pool-coping/package-gate.mjs")));
  for (const file of ["unreal/BreziTwin/BreziTwin.uproject", "scripts/unreal/run.mjs", "scripts/unreal/package-resolver.mjs", "scripts/unreal/package-verify.mjs", "scripts/unreal/app-launch.mjs", "scripts/unreal/startup-entry.mjs", "scripts/unreal/startup-entry-package.mjs", "scripts/unreal/macho-signature.mjs", "scripts/unreal/cook-log.mjs", "scripts/unreal/presentation-qa.mjs", "scripts/unreal/antialiasing-qa.mjs", "scripts/unreal/ax-initializer-qa.mjs", "scripts/unreal/tv-oak/package-gate.mjs", "scripts/unreal/furniture-oak/package-gate.mjs", "scripts/unreal/pendant-emitter/package-gate.mjs", "scripts/unreal/lawn-detail/package-gate.mjs", "scripts/unreal/lawn-ground/package-gate.mjs", "scripts/unreal/planting-surfaces/package-gate.mjs", "scripts/unreal/ornamental-grass/package-gate.mjs", "scripts/unreal/facade-plaster/package-gate.mjs"]) {
    files[file] = sha(await readFile(resolve(root, file)));
  }
  return Object.fromEntries(Object.entries(files).sort(([a], [b]) => a.localeCompare(b)));
}
async function packagedApp() {
  const mac = resolve(packaged, "Mac");
  const apps = (await readdir(mac)).filter((name) => name.endsWith(".app"));
  if (apps.length !== 1) throw new Error(`Expected one packaged app in ${mac}; run unreal:package first`);
  return resolve(mac, apps[0]);
}
async function run(command, args, env = {}, logFile = null, nativeLaunch = null) {
  const startedAt = new Date().toISOString(); let pid = null;
  const chunks = [];
  let logBytes = 0, truncated = false;
  const result = await new Promise((accept, reject) => {
    const child = spawn(command, args, { cwd: root, stdio: logFile ? ["inherit", "pipe", "pipe"] : "inherit", env: { ...process.env, ...env } });
    pid = child.pid ?? null;
    if (logFile) {
      for (const [stream, destination] of [[child.stdout, process.stdout], [child.stderr, process.stderr]]) {
        stream.on("data", (chunk) => {
          destination.write(chunk);
          logBytes += chunk.length;
          if (logBytes <= 64 * 1024 * 1024) chunks.push(chunk);
          else truncated = true;
        });
      }
    }
    child.once("error", error => accept({ code: null, signal: null, error: error.message }));
    child.once("close", (code, signal) => accept({ code, signal }));
  });
  const log = logFile ? Buffer.concat(chunks) : null;
  if (logFile) await writeFile(logFile, log);
  if (nativeLaunch) {
    const launchValidation = inspectLauncherExecution(nativeLaunch, { ...result, pid }, log?.toString("utf8") ?? "");
    await writeFile(resolve(dirname(logFile), "process.json"), JSON.stringify({ command, args, pid, startedAt, endedAt: new Date().toISOString(), ...result, launch: nativeLaunch, launchValidation }, null, 2) + "\n");
    if (launchValidation.errors.length) throw new Error(launchValidation.errors.join("; "));
  }
  if (truncated) throw new Error(`Process log exceeded 64 MiB; full validation unavailable: ${logFile}`);
  if (result.code !== 0) throw new Error(`${command} failed (exit ${result.code}, signal ${result.signal ?? "none"})`);
  return log?.toString("utf8");
}
async function prepare() {
  await run(process.execPath, ["scripts/unreal/validate.mjs"]);
  await run(process.execPath, ["scripts/unreal/exterior-lighting.mjs"]);
  await mkdir(resolve(root, "unreal/BreziTwin/Content/Data"), { recursive: true });
  await copyFile(resolve(output, "viewpoints.json"), resolve(root, "unreal/BreziTwin/Content/Data/viewpoints.json"));
  await copyFile(resolve(output, "walking.json"), resolve(root, "unreal/BreziTwin/Content/Data/walking.json"));
  await copyFile(resolve(output, "hidden-collision.json"), resolve(root, "unreal/BreziTwin/Content/Data/hidden-collision.json"));
  await copyFile(resolve(output, "exterior-lighting.json"), resolve(root, "unreal/BreziTwin/Content/Data/exterior-lighting.json"));
}
if (action === "editor-build") {
  await run(resolve(engine, "Engine/Build/BatchFiles/Mac/Build.sh"), ["BreziTwinEditor", "Mac", "Development", project, "-WaitMutex"]);
} else if (action === "vegetation") {
  await run(process.env.BLENDER_BIN ?? "/Applications/Blender.app/Contents/MacOS/Blender",
    ["--background", "--factory-startup", "--disable-autoexec", "--python-exit-code", "1",
      "--python", "scripts/unreal/vegetation-convert.py", "--", "--hedge-detail",
      "--output", resolve(output, "../vegetation-prototypes")], { BREZI_GEOMETRY: output });
} else if (action === "import") {
  await prepare();
  let importError = null;
  try { await run(resolve(engine, "Engine/Binaries/Mac/UnrealEditor-Cmd"), [project, "-run=pythonscript",
    `-script=${resolve(root, "scripts/unreal/import_scene.py")}`, "-unattended", "-nosplash", "-nullrhi"], {
    BREZI_GEOMETRY: output, BREZI_APPLY_MATERIALS: process.env.BREZI_APPLY_MATERIALS ?? "1",
    BREZI_APPLY_OPTICS: process.env.BREZI_APPLY_OPTICS ?? "1",
    BREZI_APPLY_VEGETATION: process.env.BREZI_APPLY_VEGETATION ?? "1",
    BREZI_APPLY_WALKING: process.env.BREZI_APPLY_WALKING ?? "1",
  }); } catch (error) { importError = error; }
  const receiptPath = resolve(output, "../import-report.json");
  const importReceipt = JSON.parse(await readFile(receiptPath, "utf8"));
  importReceipt.hostProcess = { code: importError ? null : 0, cleanExit: !importError,
    ...(importError ? { error: importError.message } : {}) };
  if (importError) importReceipt.status = "import-process-failed";
  await writeFile(receiptPath, JSON.stringify(importReceipt, null, 2) + "\n");
  if (importError) throw importError;
} else if (action === "package-verify") {
  const appPath = await packagedApp();
  const report = { appPath, generatedAt: new Date().toISOString(), bundle: await verifyPackage(appPath, engine),
    verification: "Inspected existing bundle only; does not establish source provenance or runtime quality" };
  await writeFile(resolve(root, "output/unreal/bundle-verification.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify(report, null, 2));
} else if (action === "package") {
  await requireIdleRenderer();
  await prepare();
  const mapFile = resolve(root, "unreal/BreziTwin/Content/Brezi/Maps/Brezi.umap");
  await access(mapFile);
  const importReportFile = resolve(output, "../import-report.json");
  const importReportBytes = await readFile(importReportFile);
  const imported = JSON.parse(importReportBytes.toString("utf8"));
  if (imported.status !== "import-validated" || imported.hostProcess?.code !== 0 || !imported.hostProcess?.cleanExit
    || imported.sourceGlbSha256 !== sha(await readFile(resolve(output, "brezi-twin.glb")))
    || imported.sourceManifestSha256 !== sha(await readFile(resolve(output, "scene.json")))
    || imported.viewpointsSha256 !== sha(await readFile(resolve(output, "viewpoints.json")))
    || imported.walkingSha256 !== sha(await readFile(resolve(output, "walking.json")))
    || imported.mapFileSha256 !== sha(await readFile(mapFile))) {
    throw new Error("Unreal map/import receipt is stale; run unreal:import before packaging");
  }
  for (const [file, digest] of Object.entries(imported.pipelineFiles ?? {})) {
    if (sha(await readFile(resolve(root, file))) !== digest) throw new Error(`Native import recipe changed: ${file}`);
  }
  const hiddenCollision = imported.hiddenCollision;
  const hiddenInputs = {
    [resolve(output, "hidden-collision.json")]: hiddenCollision?.sourceContractSha256,
    [resolve(output, "brezi-collision-only.glb")]: hiddenCollision?.sourceGlbSha256,
    [resolve(output, "hidden-collision-source.json")]: hiddenCollision?.sourceCaptureSha256,
    [resolve(root, "unreal/BreziTwin/Content/Data/hidden-collision.json")]: hiddenCollision?.sourceContractSha256,
  };
  if (hiddenCollision?.status !== "hidden-collision-saved-reloaded-validated"
    || hiddenCollision.sourceManifestSha256 !== imported.sourceManifestSha256 || hiddenCollision.objectCount !== 57)
    throw new Error("Hidden source collision has not been imported, reloaded and validated");
  for (const [file, digest] of Object.entries(hiddenInputs)) {
    if (!digest || sha(await readFile(file)) !== digest) throw new Error(`Hidden collision import input changed: ${file}`);
  }
  const stoveVisuals = imported.stoveVisuals;
  if (stoveVisuals?.status !== "stove-visuals-saved-reloaded-validated"
    || stoveVisuals.sourceManifestSha256 !== imported.sourceManifestSha256
    || !stoveVisuals.collisionAuthorityPreserved || !stoveVisuals.savedReloaded
    || stoveVisuals.originalObjectsDeleted !== 0 || stoveVisuals.originalProxyObjectsHidden !== 7 || stoveVisuals.derivativeObjects !== 4)
    throw new Error("Stove visual revision has not preserved its sources and passed both saved-map checks");
  validateTVOakReceipt(imported, JSON.parse(await readFile(resolve(output, "scene.json"), "utf8")));
  validateFurnitureOakReceipt(imported, JSON.parse(await readFile(resolve(output, "scene.json"), "utf8")));
  validatePendantEmitterReceipt(imported, JSON.parse(await readFile(resolve(output, "scene.json"), "utf8")));
  if (imported.vegetation?.nativeApplied) validateLawnDetailReceipt(imported);
  const materials = imported.materials;
  if (materials?.status === "materials-authored") {
    if (imported.vegetation?.nativeApplied) {
      validatePlasterReceipt(imported);
      validatePoolCopingReceipt(imported);
      validateLawnGroundReceipt(imported);
      validateMulchReceipt(imported);
      validateOrnamentalReceipt(imported);
    }
    if (imported.deckWood?.status !== "deck-wood-authored-validated")
      throw new Error("Deck wood material pass is missing or unvalidated; run unreal:import");
    const facade = imported.facadeWood;
    if (facade?.status !== "facade-wood-authored-validated" || facade.objectCount !== 12 || facade.materialCount !== 10
      || facade.savedReadback?.status !== "facade-saved-state-readback-validated"
      || facade.savedReadback.recipeSha256 !== facade.recipeSha256)
      throw new Error("Facade wood has not passed source, material and saved-map checks; run unreal:import");
    for (const texture of materials.textures) {
      if (sha(await readFile(resolve(root, texture.path))) !== texture.sha256) throw new Error(`Material input changed: ${texture.path}`);
    }
  }
  const naniteMaterials = imported.naniteMaterials;
  if (naniteMaterials?.status !== "nanite-material-usage-saved") {
    throw new Error("Nanite material usage has not been saved and validated; run unreal:import");
  }
  if (!imported.nativeAuthoredStateSha256 || !Object.keys(imported.finalAssetHashes ?? {}).length) {
    throw new Error("Missing final combined native asset receipt; run unreal:import");
  }
  for (const [file, digest] of Object.entries(imported.finalAssetHashes)) {
    if (sha(await readFile(resolve(root, file))) !== digest) throw new Error(`Final native asset changed after import: ${file}`);
  }
  // Pin the exact map, recipes and source assets used by this cook. A valid
  // starting receipt alone cannot prove that another process left them intact.
  const importedInputs = {
    ...hiddenInputs,
    [importReportFile]: sha(importReportBytes),
    [resolve(output, "brezi-twin.glb")]: imported.sourceGlbSha256,
    [resolve(output, "scene.json")]: imported.sourceManifestSha256,
    [resolve(output, "viewpoints.json")]: imported.viewpointsSha256,
    [resolve(output, "walking.json")]: imported.walkingSha256,
    [resolve(root, "unreal/BreziTwin/Content/Data/viewpoints.json")]: imported.viewpointsSha256,
    [resolve(root, "unreal/BreziTwin/Content/Data/walking.json")]: imported.walkingSha256,
    [mapFile]: imported.mapFileSha256,
    ...Object.fromEntries(Object.entries({ ...imported.pipelineFiles, ...imported.finalAssetHashes })
      .map(([file, digest]) => [resolve(root, file), digest])),
    ...Object.fromEntries((materials?.textures ?? []).map((texture) => [resolve(root, texture.path), texture.sha256])),
  };
  const nativeSourceFiles = await nativeSources();
  await writeFile(resolve(root, "output/unreal/package-inputs.json"), JSON.stringify({
    status: "build-started", generatedAt: new Date().toISOString(), nativeSourceFiles, importedInputs,
    sourceGlbSha256: imported.sourceGlbSha256, mapFileSha256: imported.mapFileSha256,
  }, null, 2) + "\n");
  const cookLogFile = resolve(root, "output/unreal/package-cook.log");
  // Keep the stock Zen service sponsored by this full-package process through staging.
  await run(resolve(engine, "Engine/Binaries/Mac/ZenLaunch"),
    [project, `-SponsorProcessID=${process.pid}`, "-unattended"], {},
    resolve(root, "output/unreal/package-zen-launch.log"));
  // UAT may copy into an existing archive without removing our post-UAT sealed
  // resource. Preserve the entire previous archive, then build into a fresh one.
  // Renaming on the same filesystem preserves every prior byte without deletion.
  let previousArchive = null;
  let hasPreviousArchive = true;
  try { await access(packaged); }
  catch (error) { if (error.code !== "ENOENT") throw error; hasPreviousArchive = false; }
  if (hasPreviousArchive) {
    const history = resolve(root, "output/unreal/package-history", `before-build-${randomUUID()}`);
    await mkdir(history, { recursive: true });
    await rename(packaged, resolve(history, "archive"));
    previousArchive = { directory: resolve(history, "archive"), preservedAt: new Date().toISOString() };
    try {
      const priorReceipt = await readFile(resolve(root, "output/unreal/package-report.json"));
      await writeFile(resolve(history, "package-report.json"), priorReceipt);
      previousArchive.packageReceiptSha256 = sha(priorReceipt);
    } catch (error) { if (error.code !== "ENOENT") throw error; }
    await writeFile(resolve(history, "preservation.json"), JSON.stringify(previousArchive, null, 2) + "\n");
  }
  await mkdir(packaged, { recursive: true });
  // Keep the prior package receipt if source preflight fails. Invalidate it
  // only when the build may actually replace bytes in that application bundle.
  await rm(resolve(root, "output/unreal/package-report.json"), { force: true });
  const cookLog = await run(resolve(engine, "Engine/Build/BatchFiles/RunUAT.sh"), ["BuildCookRun", `-project=${project}`,
    "-noP4", "-platform=Mac", "-clientconfig=Development", "-build", "-cook", "-stage", "-pak",
    "-package", "-archive", `-archivedirectory=${packaged}`, "-utf8output", "-unattended"], {}, cookLogFile);
  const cook = { ...inspectCookLog(cookLog), logFile: cookLogFile, logSha256: sha(await readFile(cookLogFile)) };
  await writeFile(resolve(root, "output/unreal/cook-report.json"), JSON.stringify(cook, null, 2) + "\n");
  if (cook.status !== "cook-log-validated") throw new Error(`Material cook did not pass: ${cook.status}; inspect ${cookLogFile}`);
  const finalNativeSources = await nativeSources();
  if (JSON.stringify(finalNativeSources) !== JSON.stringify(nativeSourceFiles)) {
    const changed = [...new Set([...Object.keys(finalNativeSources), ...Object.keys(nativeSourceFiles)])]
      .filter((file) => finalNativeSources[file] !== nativeSourceFiles[file]);
    throw new Error(`Native source/configuration changed during packaging: ${changed.join(", ")}; inspect and rebuild`);
  }
  for (const [file, digest] of Object.entries(importedInputs)) {
    if (sha(await readFile(file)) !== digest) throw new Error(`Imported input changed during packaging: ${file}; import and rebuild`);
  }
  const appPath = await packagedApp();
  const startupEntry = await sealStartupEntry({ app: appPath, source: resolve(root, "unreal/BreziTwin/Source/BreziTwin/BreziStartupEntry.cpp"),
    output: resolve(root, "output/unreal/startup-entry-package", randomUUID()) });
  const bundle = await verifyPackage(appPath, engine);
  await writeFile(resolve(root, "output/unreal/package-report.json"), JSON.stringify({
    status: "packaged", generatedAt: new Date().toISOString(), packageDirectory: packaged,
    appPath, bundle, startupEntry, previousArchive, nativeSourceFiles, cook, importedInputs,
    sourceGlbSha256: imported.sourceGlbSha256, mapFileSha256: imported.mapFileSha256,
    nativeMaterialSha256: materials?.nativeAuthoredSha256 ?? null,
    nativeOpticsSha256: imported.optics?.nativeAuthoredSha256 ?? null,
    nativeVegetationStatus: imported.vegetation?.status ?? null,
    nativeAuthoredStateSha256: imported.nativeAuthoredStateSha256,
    naniteMaterialUsageSha256: naniteMaterials.nativeUsageSha256,
    verification: "Standalone payload, UFS dependencies and signature verified; runtime, 4K performance and visual quality require separate checks",
  }, null, 2) + "\n");
} else if (action === "package-check") {
  const selected = await loadSelectedPackage({ root });
  const verified = await verifySelectedPackage(selected);
  console.log(JSON.stringify({ status: "selected-package-verified", app: selected.app, ...selected.provenance,
    files: verified.payload.fileCount, signature: verified.signature, nativeAppLaunched: false }, null, 2));
} else if (action === "open") {
  if (!["street", "interior", "terrace", "pool"].includes(view) || qaOptions.length)
    throw new Error("Open accepts one camera preset: street, interior, terrace or pool");
  const selected = await loadSelectedPackage({ root });
  await verifySelectedPackage(selected);
  await requireIdleRenderer();
  const launchProfile = renderProfileForAction(action, process.env, selected.report.renderProfileInterface);
  console.log(JSON.stringify({ app: selected.app, package: selected.provenance, renderProfile: launchProfile,
    runtimeQualityAndPerformanceAccepted: false }, null, 2));
  // Respect the saved window size; the packaged viewport applies its Retina or explicit 4K output policy.
  await run("open", [selected.app, "--args", "-windowed", `-BreziView=${view}`, ...launchProfile.args]);
} else if (action === "qa" || action === "qa-ui") {
  await requireIdleRenderer();
  if (!["street", "interior", "terrace", "pool"].includes(view)) throw new Error("Unknown camera preset");
  const aaExperiment = qaOptions.includes("--taa") ? "taa" : qaOptions.includes("--smaa") ? "smaa" : null;
  if (qaOptions.some((flag) => !["--night", "--hwrt", "--software", "--history-100", "--profile-gpu", "--raygen", "--sort-trace-tiles", "--taa", "--smaa", "--ax-init-stress"].includes(flag))
    || (qaOptions.includes("--hwrt") && qaOptions.includes("--software"))
    || (qaOptions.includes("--raygen") && !qaOptions.includes("--hwrt"))
    || (qaOptions.includes("--taa") && qaOptions.includes("--smaa"))
    || (aaExperiment && (qaOptions.includes("--history-100") || !qaOptions.includes("--profile-gpu"))))
    throw new Error("Supported QA options: --night, --history-100, --profile-gpu, --sort-trace-tiles, --ax-init-stress, --hwrt or --software; --raygen requires --hwrt. Choose at most one of --taa/--smaa, with --profile-gpu and without TSR --history-100.");
  const selected = await loadSelectedPackage({ root });
  const { report: receipt, app } = selected;
  const { launch } = await verifySelectedPackage(selected);
  const invocation = `${view}-${qaOptions.includes("--night") ? "night" : "day"}-${qaOptions.includes("--hwrt") ? "hwrt" : qaOptions.includes("--software") ? "software" : "default"}${qaOptions.includes("--raygen") ? "-raygen" : ""}${qaOptions.includes("--history-100") ? "-history100" : ""}${aaExperiment ? `-${aaExperiment}` : ""}${qaOptions.includes("--sort-trace-tiles") ? "-sortedtraces" : ""}${qaOptions.includes("--profile-gpu") ? "-profile" : ""}-${randomUUID()}`;
  const qaRunnerSha256 = sha(await readFile(fileURLToPath(import.meta.url)));
  const renderCommands = [
    ...(qaOptions.includes("--hwrt") ? ["r.Lumen.HardwareRayTracing 1"] : []),
    ...(qaOptions.includes("--software") ? ["r.Lumen.HardwareRayTracing 0"] : []),
    ...(qaOptions.includes("--history-100") ? ["r.TSR.History.ScreenPercentage 100"] : []),
    ...(qaOptions.includes("--raygen") ? ["r.Lumen.HardwareRayTracing.Inline 0", "r.Lumen.HardwareRayTracing.Inline"] : []),
    ...(qaOptions.includes("--sort-trace-tiles") ? ["r.Lumen.RadianceCache.SortTraceTiles 1"] : []),
    ...(aaExperiment === "taa" ? ["r.AntiAliasingMethod 2", "r.TemporalAA.Quality 2", "r.TemporalAA.Upsampling 0", "r.TemporalAA.HistoryScreenPercentage 100"] : []),
    ...(aaExperiment === "smaa" ? ["r.AntiAliasingMethod 5", "r.SMAA.Quality 3", "r.SMAA.EdgeMode 0", "r.SMAA.DebugVisualization 0"] : []),
  ];
  // The signed Mac application is sandboxed. Its own container is writable;
  // arbitrary workspace paths are not, even when the host creates them first.
  const qaDirectory = resolve(homedir(), "Library/Containers/local.brezi.twin/Data/Library/Application Support/BreziTwin/QA", invocation);
  await mkdir(qaDirectory, { recursive: true });
  const evidenceDirectory = resolve(root, "output/unreal/runtime", invocation);
  await mkdir(evidenceDirectory, { recursive: true });
  await writeFile(resolve(evidenceDirectory, "package.json"), selected.reportBytes);
  await writeFile(resolve(evidenceDirectory, "package-selection.json"), JSON.stringify(selected.provenance, null, 2) + "\n");
  const runtimeLog = await run(launch.executable, ["-windowed", "-ResX=1600", "-ResY=900",
    `-UserDir=${qaDirectory}/`,
    ...(qaOptions.includes("--night") ? ["-BreziNight"] : []),
    ...(renderCommands.length ? [`-ExecCmds=${renderCommands.join(",")}`] : []),
    ...(qaOptions.includes("--profile-gpu") ? ["-BreziProfileGPU"] : []),
    ...(qaOptions.includes("--ax-init-stress") ? ["-BreziAXInitStress"] : []),
    `-BreziView=${view}`, "-BreziBenchmarkFrames=300", "-BreziWarmupFrames=240",
    action === "qa-ui" ? "-BreziCaptureUI" : "-BreziCapture4K", "-BreziExitAfterCapture"], {}, resolve(evidenceDirectory, "process.log"), launch);
  const { payload: payloadAfter } = await verifySelectedPackage(selected);
  const diagnosticsDirectory = resolve(qaDirectory, "Saved/Diagnostics");
  const reports = (await readdir(diagnosticsDirectory)).filter((file) => file.endsWith(".json"));
  if (reports.length !== 1) throw new Error(`Expected one report from this runtime invocation: ${diagnosticsDirectory}`);
  const reportPath = resolve(diagnosticsDirectory, reports[0]);
  const report = JSON.parse(await readFile(reportPath, "utf8"));
  if (report.status !== "capture-complete" || !report.screenshotSaved || report.activeView !== view
    || report.frameInterval?.sampleCount !== 300) throw new Error(`Runtime capture failed: ${reportPath}`);
  const png = await readFile(report.screenshotPath);
  if (png.subarray(0, 8).toString("hex") !== "89504e470d0a1a0a"
    || png.readUInt32BE(16) !== report.screenshotPixels[0] || png.readUInt32BE(20) !== report.screenshotPixels[1]) {
    throw new Error(`Screenshot bytes do not match runtime report: ${report.screenshotPath}`);
  }
  await copyFile(reportPath, resolve(evidenceDirectory, "runtime.json"));
  await copyFile(report.screenshotPath, resolve(evidenceDirectory, "capture.png"));
  const presentationValidation = inspectPresentation(report, png, action === "qa-ui", runtimeLog);
  const axReceiptBytes = await readFile(resolve(diagnosticsDirectory, "AX/initializer.json"));
  const axValidation = inspectAXInitializer(JSON.parse(axReceiptBytes), qaOptions.includes("--ax-init-stress"));
  await writeFile(resolve(evidenceDirectory, "ax-initializer.json"), axReceiptBytes);
  await writeFile(resolve(evidenceDirectory, "ax-initializer-qa.json"), JSON.stringify(axValidation, null, 2) + "\n");
  presentationValidation.errors.push(...axValidation.errors);
  if (presentationValidation.errors.length) presentationValidation.status = "failed";
  let gpuProfileArtifact = null;
  let profileText = "";
  if (report.gpuProfile?.artifactSaved === true) {
    const profile = await readFile(report.gpuProfile.artifactPath);
    profileText = profile.toString("utf8");
    await copyFile(report.gpuProfile.artifactPath, resolve(evidenceDirectory, "gpu-profile.log"));
    gpuProfileArtifact = { file: "gpu-profile.log", sha256: sha(profile), bytes: profile.length };
  }
  const antiAliasingValidation = aaExperiment ? inspectAntiAliasing(report, profileText, aaExperiment) : null;
  if (antiAliasingValidation) {
    await writeFile(resolve(evidenceDirectory, "antialiasing-qa.json"), JSON.stringify(antiAliasingValidation, null, 2) + "\n");
    presentationValidation.errors.push(...antiAliasingValidation.errors);
    if (presentationValidation.errors.length) presentationValidation.status = "failed";
  }
  await writeFile(resolve(evidenceDirectory, "presentation-qa.json"), JSON.stringify(presentationValidation, null, 2) + "\n");
  await writeFile(resolve(evidenceDirectory, "invocation.json"), JSON.stringify({
    generatedAt: new Date().toISOString(), view, qaOptions, qaRunnerSha256, launch, noExistingBreziProcessAtStart: true,
    packageGeneratedAt: receipt.generatedAt, packageSelection: selected.provenance, packagedPayloadHashes: receipt.bundle.payloadHashes,
    sourceGlbSha256: receipt.sourceGlbSha256, nativeMaterialSha256: receipt.nativeMaterialSha256,
    nativeAuthoredStateSha256: receipt.nativeAuthoredStateSha256,
    gpuProfileArtifact, presentationValidation, antiAliasingValidation, axValidation, axReceiptSha256: sha(axReceiptBytes), runtimeLogSha256: sha(runtimeLog),
    packagedPayloadVerifiedAfter: payloadAfter.status,
    runtimeReportSha256: sha(await readFile(reportPath)), screenshotSha256: sha(png),
  }, null, 2) + "\n");
  console.log(JSON.stringify({ reportPath: resolve(evidenceDirectory, "runtime.json"), screenshotPath: resolve(evidenceDirectory, "capture.png"),
    native4K: report.gameViewportWasAtLeast4KThroughoutBenchmark, frameInterval: report.frameInterval }, null, 2));
  if (presentationValidation.errors.length) throw new Error(`Native presentation QA failed: ${presentationValidation.errors.join("; ")}`);
} else {
  throw new Error("Expected editor-build, vegetation, import, package, package-verify, package-check, open, qa or qa-ui");
}
