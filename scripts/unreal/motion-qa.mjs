import { spawn, execFile } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { dirname, relative, resolve } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { crc32, inflateSync } from "node:zlib";
import { verifyPackagedPayload } from "./package-verify.mjs";
import { resolveAppLaunch, inspectLauncherExecution, requireIdleApp } from "./app-launch.mjs";
import { inspectAXInitializer } from "./ax-initializer-qa.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
export const AA_METHODS = Object.freeze({ fxaa: 1, taa: 2, tsr: 4, smaa: 5 });
const HISTORY_SETTING = "r.TSR.History.ScreenPercentage";
export function motionCaptureMode(name) {
  if (name !== "tsr100" && !Object.hasOwn(AA_METHODS, name)) throw new Error("Choose fxaa, taa, tsr, tsr100 or smaa");
  const antiAliasingMethod = name === "tsr100" ? 4 : AA_METHODS[name];
  return { mode: name, antiAliasingMethod, tsrHistoryScreenPercentage: antiAliasingMethod === 4 ? (name === "tsr100" ? 100 : 200) : null };
}
export function motionExecCmds(request) {
  const mode = motionCaptureMode(request?.mode);
  if (!equal(request, mode)) throw new Error("Motion capture request differs from its closed mode");
  return `-ExecCmds=r.SMAA.Quality 3,r.AntiAliasingMethod ${mode.antiAliasingMethod}`
    + (mode.tsrHistoryScreenPercentage === null ? "" : `,${HISTORY_SETTING} ${mode.tsrHistoryScreenPercentage}`);
}
const finite = (value) => typeof value === "number" && Number.isFinite(value);
const near = (a, b, tolerance) => finite(a) && finite(b) && Math.abs(a - b) <= tolerance;
const vector = (v, length) => Array.isArray(v) && v.length === length && v.every(finite);
const vectorsNear = (a, b, tolerance) => vector(a, b?.length) && a.every((v, i) => near(v, b[i], tolerance));
const size4k = (v) => vectorsNear(v, [3840, 2160], 0);
const canonical = (value) => value && typeof value === "object" && !Array.isArray(value)
  ? Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonical(value[key])]))
  : Array.isArray(value) ? value.map(canonical) : value;
const equal = (a, b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));

/** Also used on saved evidence: the requested history cannot be inferred from the measured history. */
export function inspectMotionRequest(runtime, request, args) {
  const errors = [];
  const commands = Array.isArray(args) ? args.filter((arg) => typeof arg === "string" && /^-ExecCmds=/i.test(arg)) : [];
  let expected;
  try {
    if (request === undefined) {
      // Original runs had precisely this command and no explicit history switch.
      // Their TSR mode is the 200% baseline; new history commands require request metadata.
      const legacy = commands.length === 1 && /^-ExecCmds=r\.SMAA\.Quality 3,r\.AntiAliasingMethod ([1245])$/.exec(commands[0]);
      if (!legacy) throw new Error("Saved legacy motion request lacks its exact original AA command");
      expected = motionCaptureMode(Object.keys(AA_METHODS).find((name) => AA_METHODS[name] === Number(legacy[1])));
    } else {
      expected = motionCaptureMode(request?.mode);
      if (!equal(request, expected) || commands.length !== 1 || commands[0] !== motionExecCmds(expected))
        throw new Error("Motion request or saved ExecCmds differs from its closed capture mode");
    }
    if (runtime?.requestedAA !== expected.antiAliasingMethod
      || Number(runtime?.qualitySettings?.["r.AntiAliasingMethod"]) !== expected.antiAliasingMethod)
      errors.push("Actual native AA differs from the capture request");
    if (expected.tsrHistoryScreenPercentage !== null
      && Number(runtime?.qualitySettings?.[HISTORY_SETTING]) !== expected.tsrHistoryScreenPercentage)
      errors.push(`Actual native TSR history differs from requested ${expected.tsrHistoryScreenPercentage}%`);
  } catch (error) { errors.push(error.message); }
  return { errors, expected: expected ?? null, requestSource: request === undefined ? "legacy-exact-aa-command" : "explicit-closed-mode" };
}

/** Independent camera contract; tolerate 0.1 mm float interpolation, not one missed frame. */
export function expectedMotionPose(viewpoints, index) {
  const from = viewpoints.views.find((v) => v.id === "terrace"), to = viewpoints.views.find((v) => v.id === "pool");
  if (!from || !to || viewpoints.coordinateSystem !== "unreal-centimeters"
    || [from, to].some((v) => !vector(v.eyeCm, 3) || !vector(v.targetCm, 3) || !finite(v.horizontalFovDegrees)))
    throw new Error("Canonical terrace/pool viewpoint contract is invalid");
  const step = Math.min(48, Math.max(0, index - 3));
  const t = step / 48, smooth = t * t * t * (t * (t * 6 - 15) + 10);
  const lerp = (a, b) => a.map((v, i) => v + (b[i] - v) * smooth);
  const eyeCm = lerp(from.eyeCm, to.eyeCm), target = lerp(from.targetCm, to.targetCm);
  const delta = target.map((v, i) => v - eyeCm[i]), length = Math.hypot(...delta);
  const forward = delta.map((v) => v / length), horizontal = Math.hypot(forward[0], forward[1]);
  return { eyeCm, forward, up: [-forward[2] * forward[0] / horizontal, -forward[2] * forward[1] / horizontal, horizontal],
    horizontalFovDegrees: from.horizontalFovDegrees + (to.horizontalFovDegrees - from.horizontalFovDegrees) * smooth };
}

/** Validate the actual PNG stream and decoded row lengths; do not infer pixels from a filename. */
export function inspectMotionPng(bytes) {
  if (!Buffer.isBuffer(bytes) || bytes.length < 57 || !bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])))
    throw new Error("Missing or truncated PNG signature");
  let offset = 8, width, height, channels, ended = false;
  const data = [];
  while (offset < bytes.length) {
    if (offset + 12 > bytes.length) throw new Error("Truncated PNG chunk");
    const length = bytes.readUInt32BE(offset), type = bytes.toString("ascii", offset + 4, offset + 8);
    if (length > bytes.length - offset - 12) throw new Error("Truncated PNG chunk payload");
    const payload = bytes.subarray(offset + 8, offset + 8 + length);
    if (crc32(bytes.subarray(offset + 4, offset + 8 + length)) !== bytes.readUInt32BE(offset + 8 + length))
      throw new Error("PNG chunk CRC differs");
    if (offset === 8 && type !== "IHDR") throw new Error("PNG does not begin with IHDR");
    if (type === "IHDR") {
      if (width !== undefined || length !== 13) throw new Error("Invalid PNG IHDR");
      width = payload.readUInt32BE(0); height = payload.readUInt32BE(4);
      if (width !== 3840 || height !== 2160 || payload[8] !== 8 || ![2, 6].includes(payload[9])
        || payload[10] !== 0 || payload[11] !== 0 || payload[12] !== 0) throw new Error("PNG must be native 3840×2160 8-bit RGB/RGBA, non-interlaced");
      channels = payload[9] === 6 ? 4 : 3;
    } else if (type === "IDAT") data.push(payload);
    else if (type === "IEND") {
      if (length !== 0 || offset + 12 !== bytes.length) throw new Error("PNG has invalid IEND or trailing bytes");
      ended = true;
    }
    offset += length + 12;
  }
  if (!ended || !data.length) throw new Error("PNG lacks image data or IEND");
  const rowBytes = 1 + width * channels;
  const decoded = inflateSync(Buffer.concat(data), { maxOutputLength: rowBytes * height });
  if (decoded.length !== rowBytes * height) throw new Error("PNG decoded pixels are incomplete");
  for (let row = 0; row < height; ++row) if (decoded[row * rowBytes] > 4) throw new Error("PNG uses an invalid row filter");
  return { pixels: [width, height], bytes: bytes.length, sha256: sha(bytes), decodedPixelsVerified: true };
}

export function inspectMotionRun({ runtime, viewpoints, images, outcome, runtimeLog, payloadBefore, payloadAfter, captureRequest, args }) {
  const errors = [], check = (value, message) => { if (!value) errors.push(message); };
  const frameList = Array.isArray(runtime?.frames) ? runtime.frames : [], imageList = Array.isArray(images) ? images : [];
  check(runtime?.schemaVersion === 1 && runtime?.status === "motion-sequence-captured", "Native motion sequence did not complete");
  check(runtime?.path === "terrace-to-pool-existing-SelectView-quintic" && runtime?.simulationHz === 30
    && runtime?.warmupFrames === 240 && runtime?.preFrames === 4 && runtime?.motionFrames === 48 && runtime?.tailFrames === 12,
  "Native sequence schedule differs from 240 warmup + 4/48/12 frames at 30 simulation Hz");
  check(runtime?.warmupGameViews === 240 && runtime?.warmupRenderViews === 240 && runtime?.warmupRenderFramesConsecutive === true,
    "Warmup lacks 240 consecutive GT/RT main views");
  check(runtime?.fixedClockRestored === true && runtime?.qualitySettingsUnchanged === true, "Clock restoration or unchanged quality was not verified");
  const clock = runtime?.clock;
  check(clock && typeof clock.priorUseFixedFrameRate === "boolean" && typeof clock.priorUseFixedTimeStep === "boolean"
    && clock.priorUseFixedFrameRate === clock.currentUseFixedFrameRate && clock.priorUseFixedTimeStep === clock.currentUseFixedTimeStep
    && near(clock.priorFixedFrameRate, clock.currentFixedFrameRate, 0) && near(clock.priorFixedDeltaSeconds, clock.currentFixedDeltaSeconds, 0),
  "Clock restoration getters do not match the captured original state");
  check(runtime?.fpsMeasured === false && runtime?.worldTimeArtificiallyFrozen === false
    && runtime?.uiIncluded === false && runtime?.highResolutionScreenshotUsed === false, "Capture scope incorrectly freezes time, includes UI/high-resolution capture or claims FPS");
  const aa = runtime?.requestedAA, quality = runtime?.qualitySettings;
  check(Object.values(AA_METHODS).includes(aa) && Number(quality?.["r.AntiAliasingMethod"]) === aa, "Requested AA metadata differs");
  const requestValidation = inspectMotionRequest(runtime, captureRequest, args);
  errors.push(...requestValidation.errors);
  for (const [name, expected] of [["r.ScreenPercentage", 100], ["r.SecondaryScreenPercentage.GameViewport", 100], ["r.DynamicRes.OperationMode", 0]])
    check(quality?.[name] != null && Number(quality[name]) === expected, `Native quality setting differs: ${name}`);
  check(outcome?.code === 0 && outcome?.signal == null && !outcome?.timedOut && !outcome?.logTruncated && !outcome?.error,
    "Application did not exit cleanly");
  check(!/invalid ShaderMap|uncooked shader map|Failed to compile Material|Default Material will be used|Fatal error:|Assertion failed:|Ensure condition failed:|Handled ensure/i.test(runtimeLog ?? ""),
    "Runtime log contains a shader fallback, handled ensure or fatal error");
  check(payloadBefore?.status === "packaged-payload-unchanged" && payloadAfter?.status === "packaged-payload-unchanged", "Packaged payload was not verified before and after execution");
  check(Array.isArray(images) && images.length === 64 && new Set(images?.map((v) => v.file)).size === 64, "Expected exactly 64 distinct PNG artifacts");
  check(Array.isArray(runtime?.frames) && runtime.frames.length === 64, "Expected exactly 64 native frame records");
  for (const id of ["terrace", "pool"]) {
    const source = viewpoints?.views?.find((v) => v.id === id), actual = runtime?.sourceViewpoints?.[id];
    check(source && actual && source.id === actual.id && vectorsNear(source.eyeCm, actual.eyeCm, 0.00001)
      && vectorsNear(source.targetCm, actual.targetCm, 0.00001) && near(source.horizontalFovDegrees, actual.horizontalFovDegrees, 0.00001),
    `Native source viewpoint differs: ${id}`);
  }
  let prior = null;
  for (const [i, frame] of frameList.entries()) {
    if (!frame || typeof frame !== "object") { check(false, `Frame ${i}: malformed native frame`); continue; }
    const prefix = `Frame ${i}: `;
    check(i < 64 && frame.index === i && frame.file === `frame-${String(i).padStart(3, "0")}.png`
      && frame.phase === (i < 4 ? "pre" : i < 52 ? "motion" : "tail") && frame.motionStep === Math.min(48, Math.max(0, i - 3)), prefix + "frame index, filename or phase is out of order");
    const counters = [frame.requestFrameCounter, frame.captureFrameCounter, frame.gameViewFrameCounter, frame.renderFrameCounter];
    check(counters.every((n) => Number.isSafeInteger(n) && n > 0 && n === counters[0]) && frame.gameMainViewCount === 1 && frame.renderMainViewCount === 1
      && Number.isSafeInteger(frame.renderFamilyFrameNumber) && frame.renderFamilyFrameNumber > 0
      && frame.renderFamilyFrameNumber === frame.gameViewFamilyFrameNumber, prefix + "screenshot and exact GT/RT frame identities do not pair");
    if (prior) check(frame.requestFrameCounter === prior.requestFrameCounter + 1 && frame.renderFamilyFrameNumber === prior.renderFamilyFrameNumber + 1,
      prefix + "engine/render sequence has a gap or duplicate");
    const image = imageList.find((v) => v.file === frame.file);
    check(frame.pngSaved === true && image?.decodedPixelsVerified === true && /^[a-f0-9]{64}$/.test(image?.sha256 ?? "")
      && size4k(image?.pixels) && size4k(frame.screenshotPixels) && size4k(frame.renderTargetPixels) && size4k(frame.unscaledViewPixels), prefix + "actual PNG/render target is not verified native 4K");
    check(frame.antiAliasingMethod === aa && vector(frame.projectionJitter, 2) && frame.showFlagPostProcessing === true
      && frame.showFlagAntiAliasing === true && frame.cameraCut === false, prefix + "effective AA, finite jitter or preserved history is invalid");
    check(finite(frame.linearPreExposure) && frame.linearPreExposure > 0 && near(frame.exposureEV, Math.log2(1 / frame.linearPreExposure), 0.00001), prefix + "render exposure is invalid");
    check([frame.requestDeltaSeconds, frame.appDeltaSeconds, frame.worldDeltaSeconds, frame.realDeltaSeconds].every((n) => near(n, 1 / 30, 0.000001))
      && near(frame.worldSeconds, frame.requestWorldSeconds, 0.00001) && near(frame.realSeconds, frame.requestRealSeconds, 0.00001), prefix + "world/app/family simulation times differ");
    if (prior) check(near(frame.worldSeconds - prior.worldSeconds, 1 / 30, 0.00001) && near(frame.realSeconds - prior.realSeconds, 1 / 30, 0.00001), prefix + "simulation timeline has a gap");
    check([frame.requestWallSeconds, frame.captureWallSeconds, frame.pngWriteCompleteWallSeconds].every(finite)
      && frame.requestWallSeconds <= frame.captureWallSeconds && frame.captureWallSeconds <= frame.pngWriteCompleteWallSeconds
      && (!prior || frame.requestWallSeconds >= prior.pngWriteCompleteWallSeconds), prefix + "wall-time ordering is invalid");
    try {
      const expected = expectedMotionPose(viewpoints, i);
      check(vectorsNear(frame.eyeCm, expected.eyeCm, 0.01) && vectorsNear(frame.forward, expected.forward, 0.00002)
        && vectorsNear(frame.up, expected.up, 0.00002) && near(frame.viewFovDegrees, expected.horizontalFovDegrees, 0.001)
        && near(frame.horizontalFovDegrees, expected.horizontalFovDegrees, 0.001), prefix + "rendered camera does not follow the canonical quintic path (including Reduce Motion or input interruption)");
    } catch (error) { check(false, prefix + error.message); }
    prior = frame;
  }
  return { status: errors.length ? "failed" : "fixed-simulation-motion-evidence-validated", errors, requestValidation,
    verifiedScope: errors.length ? [] : ["64-consecutive-paired-rendered-4k-pngs", "canonical-quintic-camera-at-30-simulation-hz", "effective-render-aa-exposure-jitter", "clock-restored", "package-unchanged"],
    pending: ["human-motion-quality-review", "internal-raster-and-history-dimensions-from-gpu-pass-evidence", "real-time-performance"],
    staticPixelQualityMetrics: { status: "not-computed", excludedDynamicSubjects: ["water", "flames", "foliage"],
      reason: "Material time is not synchronized across startup; no dynamic-region mask or calibrated ground truth is asserted." },
    performanceAcceptance: "30 simulation Hz and synchronous screenshots are not measured rendering/display FPS." };
}

export function compareMotionRuns(a, b) {
  const errors = [], check = (value, message) => { if (!value) errors.push(message); };
  for (const [label, run] of [["A", a], ["B", b]]) check(run?.report?.status === "fixed-simulation-motion-evidence-validated"
    && run.report.errors?.length === 0 && run.runtime?.frames?.length === 64, `${label} lacks a validated full sequence`);
  for (const [label, run] of [["A", a], ["B", b]])
    errors.push(...inspectMotionRequest(run?.runtime, run?.report?.captureRequest, run?.report?.args).errors.map((error) => `${label}: ${error}`));
  for (const field of ["packageReceiptSha256", "sourceManifestSha256", "viewpointsSha256", "nativeSourceSha256"])
    check(/^[a-f0-9]{64}$/.test(a?.report?.[field] ?? "") && a.report[field] === b?.report?.[field], `Cross-AA provenance differs: ${field}`);
  const historyA = Number(a?.runtime?.qualitySettings?.[HISTORY_SETTING]), historyB = Number(b?.runtime?.qualitySettings?.[HISTORY_SETTING]);
  const historyComparison = a?.runtime?.requestedAA === 4 && b?.runtime?.requestedAA === 4
    && ((historyA === 100 && historyB === 200) || (historyA === 200 && historyB === 100));
  check(historyComparison || a?.runtime?.requestedAA !== b?.runtime?.requestedAA, "Choose different AA methods or exactly TSR history 100% versus 200%");
  const withoutChosenSetting = (quality = {}) => Object.fromEntries(Object.entries(quality)
    .filter(([key]) => key !== "r.AntiAliasingMethod" && !(historyComparison && key === HISTORY_SETTING)));
  check(equal(withoutChosenSetting(a?.runtime?.qualitySettings), withoutChosenSetting(b?.runtime?.qualitySettings)),
    "Cross-AA quality settings differ beyond the chosen AA method or permitted TSR history pair");
  const timeDifferences = [];
  for (let i = 0; i < 64; ++i) {
    const x = a?.runtime?.frames?.[i], y = b?.runtime?.frames?.[i];
    check(x?.antiAliasingMethod === a?.runtime?.requestedAA && y?.antiAliasingMethod === b?.runtime?.requestedAA,
      `Frame ${i}: comparison does not use the requested rendered AA methods`);
    check(x && y && x.index === y.index && x.phase === y.phase && vectorsNear(x.eyeCm, y.eyeCm, 0.001)
      && vectorsNear(x.forward, y.forward, 0.000002) && vectorsNear(x.up, y.up, 0.000002)
      && near(x.horizontalFovDegrees, y.horizontalFovDegrees, 0.0001), `Frame ${i}: cross-AA camera differs`);
    if (x && y) timeDifferences.push({ index: i, worldSecondsBMinusA: y.worldSeconds - x.worldSeconds,
      realSecondsBMinusA: y.realSeconds - x.realSeconds, platformSecondsBMinusA: y.requestWallSeconds - x.requestWallSeconds,
      exposureEVBMinusA: y.exposureEV - x.exposureEV });
  }
  return { status: errors.length ? "failed" : "matched-camera-aa-sequences", errors, timeDifferences,
    comparisonKind: historyComparison ? "tsr-history-screen-percentage" : "anti-aliasing-method",
    controlledDifference: historyComparison ? { setting: HISTORY_SETTING, a: historyA, b: historyB }
      : { setting: "r.AntiAliasingMethod", a: a?.runtime?.requestedAA, b: b?.runtime?.requestedAA },
    qualityWinner: null, fpsMeasured: false,
    staticPixelQualityMetrics: { status: "not-computed", excludedDynamicSubjects: ["water", "flames", "foliage"] },
    limitation: "Camera and simulation samples match; differing startup world/material times and exposure remain recorded. Review static architectural edges manually; dynamic subjects are excluded from numerical static-quality comparisons." };
}

async function execute(aaName) {
  const captureRequest = motionCaptureMode(aaName), aa = captureRequest.antiAliasingMethod;
  for (const name of ["BreziTwin", "UnrealEditor"]) {
    try { const active = await promisify(execFile)("pgrep", ["-x", name]); if (active.stdout.trim()) throw new Error(`${name} is already running; motion QA requires its own renderer slot`); }
    catch (error) { if (error.code !== 1) throw error; }
  }
  const geometry = resolve(root, process.env.UNREAL_OUTPUT ?? "output/unreal/geometry");
  const [packageBytes, importBytes, sceneBytes, viewpointBytes] = await Promise.all([
    readFile(resolve(root, "output/unreal/package-report.json")), readFile(resolve(geometry, "../import-report.json")),
    readFile(resolve(geometry, "scene.json")), readFile(resolve(geometry, "viewpoints.json"))]);
  const receipt = JSON.parse(packageBytes), imported = JSON.parse(importBytes), viewpoints = JSON.parse(viewpointBytes);
  if (receipt.status !== "packaged" || imported.status !== "import-validated" || receipt.mapFileSha256 !== imported.mapFileSha256
    || receipt.nativeAuthoredStateSha256 !== imported.nativeAuthoredStateSha256 || imported.sourceManifestSha256 !== sha(sceneBytes)
    || imported.viewpointsSha256 !== sha(viewpointBytes)) throw new Error("Current source/import/package provenance differs; rebuild before motion QA");
  const nativeFiles = ["BreziMotionQA.cpp", "BreziMotionQA.h", "BreziPawn.cpp", "BreziPawn.h", "BreziPlayerController.cpp", "BreziPlayerController.h"]
    .map((file) => `unreal/BreziTwin/Source/BreziTwin/${file}`);
  const nativeHashes = {};
  for (const file of nativeFiles) {
    nativeHashes[file] = sha(await readFile(resolve(root, file)));
    if (receipt.nativeSourceFiles?.[file] !== nativeHashes[file]) throw new Error(`Packaged native source is stale: ${file}`);
  }
  const helperHashes = {};
  for (const file of ["scripts/unreal/motion-qa.mjs", "scripts/unreal/package-verify.mjs", "scripts/unreal/app-launch.mjs", "scripts/unreal/startup-entry.mjs", "scripts/unreal/ax-initializer-qa.mjs"])
    helperHashes[file] = sha(await readFile(resolve(root, file)));
  const app = receipt.appPath, payloadBefore = await verifyPackagedPayload(app, receipt.bundle);
  const launch = await resolveAppLaunch(app, receipt.bundle);
  await requireIdleApp();
  const invocation = `motion-${aaName}-${randomUUID()}`;
  const sandbox = resolve(homedir(), "Library/Containers/local.brezi.twin/Data/Library/Application Support/BreziTwin/QA", invocation);
  const evidence = resolve(root, "output/unreal/runtime", invocation);
  await mkdir(sandbox, { recursive: true }); await mkdir(evidence, { recursive: true });
  const args = ["-windowed", "-ResX=1600", "-ResY=900", `-UserDir=${sandbox}/`,
    motionExecCmds(captureRequest), "-BreziMotionQA", `-BreziMotionAA=${aa}`, "-BreziMotionExit"];
  const chunks = []; let bytes = 0, timedOut = false, logTruncated = false;
  const outcome = await new Promise((accept) => {
    const child = spawn(launch.executable, args, { cwd: root, stdio: ["ignore", "pipe", "pipe"] });
    let forcedExit;
    const stop = () => { child.kill("SIGTERM"); forcedExit ??= setTimeout(() => child.kill("SIGKILL"), 10000); };
    const timeout = setTimeout(() => { timedOut = true; stop(); }, 660000);
    process.once("SIGINT", stop); process.once("SIGTERM", stop);
    const done = (result) => { clearTimeout(timeout); clearTimeout(forcedExit); process.removeListener("SIGINT", stop); process.removeListener("SIGTERM", stop); accept(result); };
    for (const stream of [child.stdout, child.stderr]) stream.on("data", (chunk) => {
      bytes += chunk.length;
      if (bytes <= 64 * 1024 * 1024) chunks.push(chunk); else { logTruncated = true; stop(); }
    });
    child.once("error", (error) => done({ code: null, signal: null, error: error.message }));
    child.once("close", (code, signal) => done({ code, signal, pid: child.pid, launch }));
  });
  outcome.launchValidation = inspectLauncherExecution(launch, outcome, Buffer.concat(chunks).toString("utf8"));
  if (outcome.launchValidation.errors.length) outcome.error = outcome.launchValidation.errors.join("; ");
  Object.assign(outcome, { timedOut, logTruncated });
  const log = Buffer.concat(chunks), artifactErrors = [], images = [];
  await writeFile(resolve(evidence, "process.log"), log);
  await writeFile(resolve(evidence, "package.json"), packageBytes);
  await writeFile(resolve(evidence, "viewpoints.json"), viewpointBytes);
  let runtime = null, runtimeBytes = null, payloadAfter = null, axBytes = null;
  let axInitializer = inspectAXInitializer(null);
  try {
    axBytes = await readFile(resolve(sandbox, "Saved/Diagnostics/AX/initializer.json"));
    await writeFile(resolve(evidence, "ax-initializer.json"), axBytes);
    axInitializer = inspectAXInitializer(JSON.parse(axBytes));
  } catch (error) { artifactErrors.push(`AX initializer receipt: ${error.message}`); }
  artifactErrors.push(...axInitializer.errors);
  try {
    const diagnostics = resolve(sandbox, "Saved/Diagnostics/motion-qa");
    runtimeBytes = await readFile(resolve(diagnostics, "runtime.json")); runtime = JSON.parse(runtimeBytes);
    await writeFile(resolve(evidence, "runtime.json"), runtimeBytes);
    const files = (await readdir(diagnostics)).filter((name) => name.endsWith(".png")).sort();
    for (const file of files) {
      if (!/^frame-\d{3}\.png$/.test(file)) { artifactErrors.push(`Unexpected PNG artifact: ${file}`); continue; }
      const data = await readFile(resolve(diagnostics, file));
      await writeFile(resolve(evidence, file), data);
      try { images.push({ file, ...inspectMotionPng(data) }); } catch (error) { artifactErrors.push(`${file}: ${error.message}`); }
    }
  } catch (error) { artifactErrors.push(error.message); }
  try { payloadAfter = await verifyPackagedPayload(app, receipt.bundle); } catch (error) { artifactErrors.push(error.message); }
  for (const [file, digest] of Object.entries({ ...nativeHashes, ...helperHashes }))
    if (sha(await readFile(resolve(root, file))) !== digest) artifactErrors.push(`QA source changed during execution: ${file}`);
  const report = inspectMotionRun({ runtime, viewpoints, images, outcome, runtimeLog: log.toString("utf8"), payloadBefore, payloadAfter, captureRequest, args });
  report.errors.push(...artifactErrors);
  if (report.errors.length) { report.status = "failed"; report.verifiedScope = []; }
  Object.assign(report, { generatedAt: new Date().toISOString(), process: outcome, args, captureRequest, sandboxDirectory: sandbox, images,
    packageReceiptSha256: sha(packageBytes), sourceManifestSha256: sha(sceneBytes), viewpointsSha256: sha(viewpointBytes),
    nativeSourceSha256: sha(JSON.stringify(canonical(nativeHashes))), nativeHashes, helperHashes, runtimeSha256: runtimeBytes ? sha(runtimeBytes) : null,
    payloadBefore: payloadBefore.status, payloadAfter: payloadAfter?.status ?? "failed",
    axInitializer, axInitializerSha256: axBytes ? sha(axBytes) : null });
  await writeFile(resolve(evidence, "motion-qa.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify({ reportPath: resolve(evidence, "motion-qa.json"), status: report.status, errors: report.errors }, null, 2));
  if (report.status === "failed") process.exitCode = 1;
}

async function loadRun(directory) {
  const [reportBytes, runtimeBytes, viewpointBytes, log] = await Promise.all(["motion-qa.json", "runtime.json", "viewpoints.json", "process.log"].map((file) => readFile(resolve(directory, file))));
  const report = JSON.parse(reportBytes), runtime = JSON.parse(runtimeBytes), viewpoints = JSON.parse(viewpointBytes), images = [];
  const axBytes = await readFile(resolve(directory, "ax-initializer.json"));
  if (sha(axBytes) !== report.axInitializerSha256 || inspectAXInitializer(JSON.parse(axBytes)).status === "failed")
    throw new Error("Saved native AX initializer evidence is missing, changed or invalid");
  if (sha(runtimeBytes) !== report.runtimeSha256 || sha(viewpointBytes) !== report.viewpointsSha256) throw new Error("Saved motion evidence hash differs");
  for (const image of report.images ?? []) {
    if (!/^frame-\d{3}\.png$/.test(image.file)) throw new Error("Unsafe saved PNG path");
    const measured = inspectMotionPng(await readFile(resolve(directory, image.file)));
    if (measured.sha256 !== image.sha256) throw new Error(`Saved PNG changed: ${image.file}`);
    images.push({ file: image.file, ...measured });
  }
  const current = inspectMotionRun({ runtime, viewpoints, images, outcome: report.process, runtimeLog: log.toString("utf8"),
    payloadBefore: { status: report.payloadBefore }, payloadAfter: { status: report.payloadAfter }, captureRequest: report.captureRequest, args: report.args });
  if (current.status === "failed") throw new Error(`Saved sequence fails revalidation: ${current.errors.join("; ")}`);
  return { report, runtime };
}

async function compareDirectories(directoryA, directoryB) {
  const a = await loadRun(directoryA), b = await loadRun(directoryB), comparison = compareMotionRuns(a, b);
  const directory = resolve(root, "output/unreal/runtime", `motion-comparison-${randomUUID()}`);
  await mkdir(directory, { recursive: true });
  await writeFile(resolve(directory, "comparison.json"), JSON.stringify(comparison, null, 2) + "\n");
  if (comparison.status !== "failed") {
    const locations = [directoryA, directoryB].map((d) => relative(directory, resolve(d)).split("/").map(encodeURIComponent).join("/"));
    // A stepping viewer only: browser refresh and PNG loading are not native motion/FPS evidence.
    const source = JSON.stringify(locations).replaceAll("<", "\\u003c");
    const html = `<!doctype html><html lang="en"><meta charset="utf-8"><title>Matched AA camera frames</title><style>body{margin:24px;background:#111;color:#eee;font:16px system-ui}button,input{margin:8px}img{width:100%;height:auto}p{max-width:1000px}</style><h1>Matched camera frames</h1><p>PNG evidence at 3840×2160. Step through the same simulation frame; switch A/B to inspect static architectural edges. Animated water, flames and foliage have different startup material times. This viewer does not measure native FPS or score quality.</p><button id="which">A</button><input id="frame" type="range" min="0" max="63" value="0"><output id="label">0</output><img id="image" alt="Native AA comparison frame"><script>const roots=${source};let side=0;const frame=document.getElementById('frame'),label=document.getElementById('label'),image=document.getElementById('image'),which=document.getElementById('which');function update(){label.textContent=frame.value;image.src=roots[side]+'/frame-'+String(frame.value).padStart(3,'0')+'.png'}frame.oninput=update;which.onclick=()=>{side=1-side;which.textContent=side?'B':'A';update()};update();</script></html>`;
    await writeFile(resolve(directory, "index.html"), html);
  }
  console.log(JSON.stringify({ path: directory, ...comparison }, null, 2));
  if (comparison.status === "failed") process.exitCode = 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [command, ...args] = process.argv.slice(2);
  if (command === "capture" && args.length === 1) await execute(args[0]);
  else if (command === "compare" && args.length === 2) await compareDirectories(...args);
  else throw new Error("Usage: node scripts/unreal/motion-qa.mjs capture <fxaa|taa|tsr|tsr100|smaa> | compare <run-A-directory> <run-B-directory>");
}
