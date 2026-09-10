import { spawn, execFile } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import { mkdir, readFile, writeFile, readdir, copyFile, realpath } from "node:fs/promises";
import { resolve, dirname, relative } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { verifyPackagedPayload } from "./package-verify.mjs";
import { resolveAppLaunch, inspectLauncherExecution, requireIdleApp } from "./app-launch.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const views = ["interior", "terrace", "pool", "street"];
const rejectedEntries = ["first-downward-hit-is-not-a-walk-surface", "no-radius-valid-support",
  "capsule-blocked-or-no-radius-valid-support"];
const passedEntry = "entry-floor-and-capsule-queries-passed";
const vector = (v) => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite);

/** This gate certifies one entry/standing observation, never traversal or keyboard input. */
export function inspectWalkingEvidence({ runtime, contract, auxiliary, view, mode, process: outcome, png, runtimeLog = "" }) {
  const errors = [], check = (condition, message) => { if (!condition) errors.push(message); };
  const w = runtime?.walking ?? {}, floorIds = new Set(contract.walkSurfaces.map((r) => r.objectId));
  check(views.includes(view) && ["audit", "standing"].includes(mode), "Unknown walking QA case");
  check(outcome?.code === 0 && outcome?.signal == null && !outcome?.timedOut && !outcome?.logTruncated && !outcome?.error,
    "Application did not exit cleanly");
  check(!/invalid ShaderMap|uncooked shader map|Failed to compile Material|Default Material will be used|Fatal error:|Assertion failed:|Ensure condition failed:|Handled ensure/i.test(runtimeLog),
    "Runtime log contains a shader fallback, handled ensure or fatal failure");
  check(runtime?.status === "capture-complete" && runtime.activeView === view, "Missing or wrong runtime capture");
  check(runtime?.frameInterval?.sampleCount === 300, "Missing 300 measured runtime frames");
  check(runtime?.gameViewportWasAtLeast4KThroughoutBenchmark === true
    && runtime?.viewportChangedDuringBenchmark === false, "Viewport was not stable native 4K");
  const settings = runtime?.renderSettings ?? {};
  check(settings["r.ScreenPercentage"] === 100 && settings["r.SecondaryScreenPercentage.GameViewport"] === 100
    && settings["r.DynamicRes.OperationMode"] === 0, "Render resolution used scaling or dynamic resolution");
  const dimensions = png?.length >= 24 && png.subarray(0, 8).toString("hex") === "89504e470d0a1a0a"
    ? [png.readUInt32BE(16), png.readUInt32BE(20)] : [];
  check(runtime?.screenshotSaved === true && dimensions[0] >= 3840 && dimensions[1] >= 2160
    && JSON.stringify(dimensions) === JSON.stringify(runtime?.screenshotPixels), "Missing or mismatched 4K PNG");
  check(w.contractLoaded === true && w.worldContractValidated === true
    && Array.isArray(w.worldContractErrors) && w.worldContractErrors.length === 0, "Native walking world contract failed");
  check(w.sceneSha256 === contract.provenance.sceneSha256, "Walking source scene hash differs");
  check(auxiliary?.sourceManifestSha256 === contract.provenance.sceneSha256
    && auxiliary?.objects?.length > 0 && w.expectedAuxiliaryBlockers === auxiliary.objects.length,
  "Hidden source collider contract or native count differs");
  check(w.expectedFloorObjects === contract.walkSurfaces.length
    && w.expectedOffsetObjects === contract.walkSurfaces.filter((r) => r.supportOffsetCm !== 0).length
    && w.expectedClosedBlockers === contract.capturedClosedBlockers.length, "Native source object counts differ");
  check(w.capsuleRadiusCm === contract.capsuleRadiusCm && w.capsuleHalfHeightCm === contract.capsuleHalfHeightCm
    && w.expectedEyeHeightCm === contract.eyeHeightCm, "Native body or eye dimensions differ");
  check(w.entryAttempts === 1, "Entry query did not execute exactly once");
  if (w.entryQueryStatus === passedEntry) {
    check(floorIds.has(w.entryLineHitObjectId) && floorIds.has(w.entrySupportObjectId), "Entry hit an unknown source floor");
    check(vector(w.lastEntryCapsuleCenterCm) && vector(w.lastEntryFloorHitCm) && w.supportQueries >= 2,
      "Missing actual entry line/capsule query observations");
  }
  if (mode === "audit") {
    check(w.cameraMode === "orbit" && w.successfulEntries === 0, "Read-only entry audit unexpectedly entered walking");
    check(w.entryQueryStatus === passedEntry || rejectedEntries.includes(w.entryQueryStatus), "No explicit geometric entry outcome");
  } else {
    check(w.entryQueryStatus === passedEntry && w.successfulEntries === 1 && w.cameraMode === "walking"
      && w.characterMovementMode === "Walking", "Standing case did not remain in native walking");
    check(floorIds.has(w.currentSupportObjectId), "Standing support is missing or unregistered");
    check(w.groundedEyeSamples >= 300 && w.unmeasuredOrAirborneEyeSamples === 0, "Standing eye was not continuously supported");
    for (const key of ["lastMeasuredEyeHeightCm", "minMeasuredEyeHeightCm", "maxMeasuredEyeHeightCm"])
      check(Number.isFinite(w[key]) && Math.abs(w[key] - contract.eyeHeightCm) <= 0.2, `${key} differs from the authored eye height`);
    check(Number.isFinite(w.maxEyeHeightErrorCm) && w.maxEyeHeightErrorCm <= 0.2, "Eye height error exceeds 2 mm");
    check(vector(w.currentCapsuleCenterCm) && vector(w.lastEntryCapsuleCenterCm)
      && Math.hypot(w.currentCapsuleCenterCm[0] - w.lastEntryCapsuleCenterCm[0],
        w.currentCapsuleCenterCm[1] - w.lastEntryCapsuleCenterCm[1]) <= 0.2, "Standing case drifted horizontally");
    check(w.controlledVerticalDrops === 0, "Standing case performed a drop");
  }
  return { status: errors.length ? "failed" : mode === "standing" ? "standing-native-validated" : "entry-audit-native-validated",
    view, mode, errors, entryOutcome: w.entryQueryStatus ?? null,
    verification: { sourceWorld: !errors.length, standing: !errors.length && mode === "standing",
      traversal: false, wallSliding: false, closedDoorTraversal: false, steps: false, drops: false, keyboard: false, accessibility: false },
    performanceAcceptance: "Frame timing is recorded; this gate makes no smoothness or photorealism claim." };
}

export function walkingQaPlan(contract) {
  const refs = (records) => records.map(({ objectId, name, nativeBoundsCm, supportOffsetCm, doorId }) =>
    ({ objectId, name, nativeBoundsCm, ...(supportOffsetCm !== undefined ? { supportOffsetCm } : {}), ...(doorId ? { doorId } : {}) }));
  return { status: "prepared-not-executed", sourceSceneSha256: contract.provenance.sceneSha256,
    automated: views.flatMap((view) => ["audit", "standing"].map((mode) => ({ view, mode,
      command: `node scripts/unreal/walking-qa.mjs run ${view} --${mode}`,
      acceptance: mode === "audit" ? "Actual source line/capsule queries yield a documented outcome without relocation."
        : `Exactly one entry, stable ${contract.eyeHeightCm} cm eye (±2 mm), 300 grounded samples, no horizontal drift or drop.` }))),
    pendingNativeInteraction: [
      { case: "wall-and-corner", status: "pending-traversal-driver", sourceObjects: refs(contract.staticBlockers.filter((r) => r.cameraOccluder && !r.walkSurface).slice(0, 8)),
        acceptance: "From both sides drive straight and diagonally into actual source walls; capsule cannot cross, tangent sliding advances, release stops; record actual hit IDs and the path." },
      { case: "closed-door", status: "pending-traversal-driver", sourceObjects: refs(contract.capturedClosedBlockers.filter((r) => ["FRONT-ENTRY", "DOOR-101-102", "DOOR-102-104", "DOOR-102-105", "GARDEN-02"].includes(r.doorId))),
        acceptance: "Approach each captured closed leaf from both reachable sides. Capsule cannot cross the leaf plane; door stays at captured bounds. Opening animation is not implemented." },
      { case: "source-steps-and-seams", status: "pending-traversal-driver", sourceObjects: refs(contract.walkSurfaces.filter((r) => r.walkSurfaceId.startsWith("porch-step") || r.supportOffsetCm !== 0)),
        acceptance: `Traverse both directions over existing source steps/seams and exact support offsets. Step limit ${contract.maxStepHeightCm} cm. Do not invent a threshold fixture in the project geometry.` },
      { case: "pool-edge-and-shaft", status: "pending-traversal-driver", sourceObjects: refs(contract.walkSurfaces.filter((r) => /POOL/.test(r.walkSurfaceId))),
        acceptance: `Reject unsupported edges and drops >${contract.maxDropCm} cm; validate smaller source drops before vertical descent. Closed shaft hatch supports the body; the deep shaft floor cannot authorize a long fall.` },
      { case: "keyboard-and-focus", status: "pending-native-key-events",
        acceptance: "Real F2/WASD/arrows, precision Q, Shift boost, diagonal/straight travel, key release, Escape focus return, system shortcuts, and preset/mode changes. Native key events and visible focus are required; CLI entry is insufficient." }],
    limitation: "The current native flags do not drive traversal or keyboard input. Audit rejection is a query result, not successful walking." };
}

async function executeWalking(view, mode, renderer) {
  if (!views.includes(view) || !["audit", "standing"].includes(mode) || !["software", "hwrt"].includes(renderer)) throw new Error("Unknown walking run options");
  const exec = promisify(execFile);
  try { const p = await exec("pgrep", ["-x", "BreziTwin"]); if (p.stdout.trim()) throw new Error("BreziTwin is already running"); }
  catch (error) { if (error.code !== 1) throw error; }
  const geometry = resolve(root, process.env.UNREAL_OUTPUT ?? "output/unreal/geometry");
  const contractBytes = await readFile(resolve(geometry, "walking.json")), contract = JSON.parse(contractBytes);
  const auxiliaryBytes = await readFile(resolve(geometry, "hidden-collision.json")), auxiliary = JSON.parse(auxiliaryBytes);
  const packageBytes = await readFile(resolve(root, "output/unreal/package-report.json")), receipt = JSON.parse(packageBytes);
  const imported = JSON.parse(await readFile(resolve(geometry, "../import-report.json"), "utf8"));
  if (receipt.status !== "packaged" || receipt.mapFileSha256 !== imported.mapFileSha256
    || receipt.nativeAuthoredStateSha256 !== imported.nativeAuthoredStateSha256 || imported.walkingSha256 !== sha(contractBytes)
    || imported.hiddenCollision?.sourceContractSha256 !== sha(auxiliaryBytes))
    throw new Error("Walking contract and packaged map provenance differ; import and package again");
  const app = receipt.appPath;
  const payloadBefore = await verifyPackagedPayload(app, receipt.bundle);
  const launch = await resolveAppLaunch(app, receipt.bundle);
  await requireIdleApp();
  const invocation = `walking-${view}-${mode}-${renderer}-${randomUUID()}`;
  const sandbox = resolve(homedir(), "Library/Containers/local.brezi.twin/Data/Library/Application Support/BreziTwin/QA", invocation);
  const evidence = resolve(root, "output/unreal/runtime", invocation);
  await mkdir(sandbox, { recursive: true }); await mkdir(evidence, { recursive: true });
  const args = ["-windowed", "-ResX=1600", "-ResY=900", `-UserDir=${sandbox}/`,
    `-ExecCmds=r.Lumen.HardwareRayTracing ${renderer === "hwrt" ? 1 : 0}`, `-BreziView=${view}`,
    mode === "standing" ? "-BreziWalk" : "-BreziWalkAudit", "-BreziWarmupFrames=240", "-BreziBenchmarkFrames=300", "-BreziCapture4K", "-BreziExitAfterCapture"];
  const chunks = []; let bytes = 0, timedOut = false, logTruncated = false;
  const outcome = await new Promise((accept) => {
    const child = spawn(launch.executable, args, { cwd: root, stdio: ["ignore", "pipe", "pipe"] });
    let forcedExit;
    const stop = () => { child.kill("SIGTERM"); forcedExit ??= setTimeout(() => child.kill("SIGKILL"), 10000); };
    const timeout = setTimeout(() => { timedOut = true; stop(); }, 240000);
    for (const stream of [child.stdout, child.stderr]) stream.on("data", (chunk) => {
      bytes += chunk.length;
      if (bytes <= 64 * 1024 * 1024) chunks.push(chunk);
      else { logTruncated = true; stop(); }
    });
    child.once("error", (error) => { clearTimeout(timeout); clearTimeout(forcedExit); accept({ code: null, signal: null, error: error.message }); });
    child.once("close", (code, signal) => { clearTimeout(timeout); clearTimeout(forcedExit); accept({ code, signal, pid: child.pid, launch }); });
  });
  outcome.launchValidation = inspectLauncherExecution(launch, outcome, Buffer.concat(chunks).toString("utf8"));
  if (outcome.launchValidation.errors.length) outcome.error = outcome.launchValidation.errors.join("; ");
  outcome.timedOut = timedOut; outcome.logTruncated = logTruncated;
  await writeFile(resolve(evidence, "process.log"), Buffer.concat(chunks));
  await writeFile(resolve(evidence, "package.json"), packageBytes);
  await writeFile(resolve(evidence, "walking-contract.json"), contractBytes);
  await writeFile(resolve(evidence, "hidden-collision-contract.json"), auxiliaryBytes);
  let runtime = null, png = null, artifactError = null, payloadAfter = null;
  try {
    const diagnostics = await realpath(resolve(sandbox, "Saved/Diagnostics"));
    const reports = (await readdir(diagnostics)).filter((file) => file.endsWith(".json"));
    if (reports.length !== 1) throw new Error("Expected one report from this invocation");
    const reportPath = resolve(diagnostics, reports[0]);
    runtime = JSON.parse(await readFile(reportPath, "utf8"));
    await copyFile(reportPath, resolve(evidence, "runtime.json"));
    const screenshot = await realpath(runtime.screenshotPath);
    if (relative(diagnostics, screenshot).startsWith("..")) throw new Error("Screenshot is outside this invocation");
    png = await readFile(screenshot);
    await writeFile(resolve(evidence, "capture.png"), png);
  } catch (error) { artifactError = error.message; }
  try { payloadAfter = await verifyPackagedPayload(app, receipt.bundle); } catch (error) { artifactError = error.message; }
  const validation = inspectWalkingEvidence({ runtime, contract, auxiliary, view, mode, process: outcome, png, runtimeLog: Buffer.concat(chunks).toString("utf8") });
  if (artifactError || logTruncated) {
    validation.status = "failed"; validation.errors.push(artifactError ?? "Process log truncated");
    for (const key of Object.keys(validation.verification)) validation.verification[key] = false;
  }
  const report = { ...validation, generatedAt: new Date().toISOString(), process: outcome,
    sandboxDirectory: sandbox, args, packageReceiptSha256: sha(packageBytes), contractSha256: sha(contractBytes), auxiliaryContractSha256: sha(auxiliaryBytes),
    qaHelperSha256: sha(await readFile(fileURLToPath(import.meta.url))),
    packagePayloadVerifiedBefore: payloadBefore.status, packagePayloadVerifiedAfter: payloadAfter?.status ?? "failed",
    runtimeSha256: runtime ? sha(await readFile(resolve(evidence, "runtime.json"))) : null,
    screenshotSha256: png ? sha(png) : null,
    evidenceScope: "Packaged native entry/standing case; traversal and real keyboard interaction remain pending." };
  await writeFile(resolve(evidence, "walking-qa.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify({ reportPath: resolve(evidence, "walking-qa.json"), status: report.status, errors: report.errors }, null, 2));
  if (report.status === "failed") process.exitCode = 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [action = "plan", view = "interior", ...flags] = process.argv.slice(2);
  if (action === "plan") {
    const contract = JSON.parse(await readFile(resolve(root, process.env.UNREAL_OUTPUT ?? "output/unreal/geometry", "walking.json"), "utf8"));
    console.log(JSON.stringify(walkingQaPlan(contract), null, 2));
  } else if (action === "run") {
    if (flags.some((flag) => !["--audit", "--standing", "--software", "--hwrt"].includes(flag))
      || (flags.includes("--audit") && flags.includes("--standing")) || (flags.includes("--software") && flags.includes("--hwrt")))
      throw new Error("Choose --audit or --standing and --software or --hwrt");
    await executeWalking(view, flags.includes("--audit") ? "audit" : "standing", flags.includes("--hwrt") ? "hwrt" : "software");
  } else throw new Error("Expected plan or run <view> [--audit|--standing] [--software|--hwrt]");
}
