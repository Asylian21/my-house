import test from "node:test";
import assert from "node:assert/strict";
import { crc32, deflateSync } from "node:zlib";
import { compareMotionRuns, expectedMotionPose, inspectMotionPng, inspectMotionRun, inspectMotionRequest, motionCaptureMode, motionExecCmds } from "../scripts/unreal/motion-qa.mjs";

// Synthetic acceptance evidence, not simulated Unreal rendering or native API proof.
function fixture(aa = 2, mode = { 1: "fxaa", 2: "taa", 4: "tsr", 5: "smaa" }[aa]) {
  const captureRequest = motionCaptureMode(mode);
  const viewpoints = { coordinateSystem: "unreal-centimeters", views: [
    { id: "terrace", eyeCm: [-1050, -1070, 210], targetCm: [180, -30, 210], horizontalFovDegrees: 76.09408506365219 },
    { id: "pool", eyeCm: [-426, -660, 180], targetCm: [-46, -395, 60], horizontalFovDegrees: 74 },
  ] };
  const qualitySettings = { "r.AntiAliasingMethod": String(aa), "r.ScreenPercentage": "100", "r.SecondaryScreenPercentage.GameViewport": "100",
    "r.DynamicRes.OperationMode": "0", "r.Lumen.HardwareRayTracing": "1", "sg.ShadowQuality": "3",
    "r.TSR.History.ScreenPercentage": String(captureRequest.tsrHistoryScreenPercentage ?? 200) };
  const frames = Array.from({ length: 64 }, (_, i) => {
    const t = Math.min(1, Math.max(0, (i - 3) / 48)), alpha = 6 * t ** 5 - 15 * t ** 4 + 10 * t ** 3;
    const a = viewpoints.views[0], b = viewpoints.views[1];
    const eyeCm = a.eyeCm.map((v, k) => v * (1 - alpha) + b.eyeCm[k] * alpha);
    const delta = a.targetCm.map((v, k) => v * (1 - alpha) + b.targetCm[k] * alpha - eyeCm[k]);
    const forward = delta.map((v) => v / Math.hypot(...delta)), horizontal = Math.hypot(forward[0], forward[1]);
    return { index: i, phase: i < 4 ? "pre" : i < 52 ? "motion" : "tail", motionStep: Math.min(48, Math.max(0, i - 3)),
      file: `frame-${String(i).padStart(3, "0")}.png`, eyeCm, forward,
      up: [-forward[2] * forward[0] / horizontal, -forward[2] * forward[1] / horizontal, horizontal],
      horizontalFovDegrees: a.horizontalFovDegrees * (1 - alpha) + b.horizontalFovDegrees * alpha,
      viewFovDegrees: a.horizontalFovDegrees * (1 - alpha) + b.horizontalFovDegrees * alpha,
      requestFrameCounter: 800 + i, captureFrameCounter: 800 + i, gameViewFrameCounter: 800 + i, renderFrameCounter: 800 + i,
      gameViewFamilyFrameNumber: 320 + i, renderFamilyFrameNumber: 320 + i, gameMainViewCount: 1, renderMainViewCount: 1,
      pngSaved: true, screenshotPixels: [3840, 2160], renderTargetPixels: [3840, 2160], unscaledViewPixels: [3840, 2160],
      antiAliasingMethod: aa, projectionJitter: aa === 2 || aa === 4 ? [0.0001, -0.0001] : [0, 0],
      cameraCut: false, allowTemporalJitter: aa === 2 || aa === 4, showFlagPostProcessing: true, showFlagAntiAliasing: true,
      showFlagTemporalAA: true, primaryScreenPercentageMethod: 0, linearPreExposure: 1 / 1024, exposureEV: 10,
      requestDeltaSeconds: 1 / 30, appDeltaSeconds: 1 / 30, worldDeltaSeconds: 1 / 30, realDeltaSeconds: 1 / 30,
      worldSeconds: 10 + i / 30, requestWorldSeconds: 10 + i / 30, realSeconds: 11 + i / 30, requestRealSeconds: 11 + i / 30,
      requestWallSeconds: 1000 + 0.4 * i, captureWallSeconds: 1000.1 + 0.4 * i, pngWriteCompleteWallSeconds: 1000.3 + 0.4 * i };
  });
  return { viewpoints, captureRequest, args: ["-windowed", motionExecCmds(captureRequest), "-BreziMotionQA"],
    runtime: { schemaVersion: 1, status: "motion-sequence-captured", path: "terrace-to-pool-existing-SelectView-quintic",
    simulationHz: 30, warmupFrames: 240, preFrames: 4, motionFrames: 48, tailFrames: 12, requestedAA: aa,
    warmupGameViews: 240, warmupRenderViews: 240, warmupRenderFramesConsecutive: true,
    fixedClockRestored: true, qualitySettingsUnchanged: true, worldTimeArtificiallyFrozen: false, fpsMeasured: false,
    clock: { priorUseFixedFrameRate: false, currentUseFixedFrameRate: false, priorFixedFrameRate: 30, currentFixedFrameRate: 30,
      priorUseFixedTimeStep: false, currentUseFixedTimeStep: false, priorFixedDeltaSeconds: 1 / 30, currentFixedDeltaSeconds: 1 / 30 },
    uiIncluded: false, highResolutionScreenshotUsed: false, qualitySettings,
    sourceViewpoints: Object.fromEntries(viewpoints.views.map((v) => [v.id, structuredClone(v)])), frames },
  images: frames.map((frame) => ({ file: frame.file, pixels: [3840, 2160], bytes: 100000, sha256: "a".repeat(64), decodedPixelsVerified: true })),
  outcome: { code: 0, signal: null, timedOut: false, logTruncated: false }, runtimeLog: "Native clean completion",
  payloadBefore: { status: "packaged-payload-unchanged" }, payloadAfter: { status: "packaged-payload-unchanged" } };
}

function comparisonFixture(aa, mode) {
  const evidence = fixture(aa, mode);
  return { runtime: evidence.runtime, report: { ...inspectMotionRun(evidence), packageReceiptSha256: "1".repeat(64),
    captureRequest: evidence.captureRequest, args: evidence.args,
    sourceManifestSha256: "2".repeat(64), viewpointsSha256: "3".repeat(64), nativeSourceSha256: "4".repeat(64) } };
}

test("64 paired source-camera samples pass without claiming display FPS or pixel quality", () => {
  const report = inspectMotionRun(fixture());
  assert.equal(report.status, "fixed-simulation-motion-evidence-validated", report.errors.join("\n"));
  assert.match(report.performanceAcceptance, /not measured/);
  assert.equal(report.staticPixelQualityMetrics.status, "not-computed");
  assert.deepEqual(report.staticPixelQualityMetrics.excludedDynamicSubjects, ["water", "flames", "foliage"]);
});

for (const [name, mutate, pattern] of [
  ["stale render snapshot", (e) => e.runtime.frames[8].renderFrameCounter--, /frame identities/],
  ["world ticks without rendered warmup", (e) => e.runtime.warmupRenderViews = 239, /Warmup lacks/],
  ["wrong scene family despite equal engine counter", (e) => e.runtime.frames[8].renderFamilyFrameNumber--, /frame identities|sequence/],
  ["multiple main views", (e) => e.runtime.frames[8].renderMainViewCount++, /frame identities/],
  ["camera delayed by one frame", (e) => e.runtime.frames[24].eyeCm = [...e.runtime.frames[23].eyeCm], /canonical quintic/],
  ["instant Reduce Motion camera", (e) => { for (let i = 4; i < 52; i++) e.runtime.frames[i].eyeCm = [...e.runtime.frames[63].eyeCm]; }, /canonical quintic/],
  ["correct eye but wrong look direction", (e) => e.runtime.frames[24].forward = [1, 0, 0], /canonical quintic/],
  ["correct direction but rolled camera", (e) => e.runtime.frames[24].up = [1, 0, 0], /canonical quintic/],
  ["changed lens", (e) => e.runtime.frames[24].horizontalFovDegrees += 0.1, /canonical quintic/],
  ["gap in both world and render counters", (e) => { for (const f of e.runtime.frames.slice(20)) for (const k of ["requestFrameCounter", "captureFrameCounter", "gameViewFrameCounter", "renderFrameCounter", "gameViewFamilyFrameNumber", "renderFamilyFrameNumber"]) f[k]++; }, /sequence has a gap/],
  ["missing PNG", (e) => e.images.pop(), /64 distinct/],
  ["unverified decoded PNG", (e) => e.images[20].decodedPixelsVerified = false, /actual PNG/],
  ["scaled renderer behind 4K PNG", (e) => e.runtime.frames[20].renderTargetPixels = [1920, 1080], /native 4K/],
  ["AA fallback", (e) => e.runtime.frames[20].antiAliasingMethod = 1, /effective AA/],
  ["nonfinite jitter", (e) => e.runtime.frames[20].projectionJitter[0] = NaN, /effective AA/],
  ["temporal history cut", (e) => e.runtime.frames[20].cameraCut = true, /preserved history/],
  ["unrestored fixed clock", (e) => e.runtime.fixedClockRestored = false, /Clock restoration/],
  ["restoration flag without restored getters", (e) => e.runtime.clock.currentUseFixedFrameRate = true, /Clock restoration/],
  ["fixed world clock", (e) => e.runtime.worldTimeArtificiallyFrozen = true, /freezes time/],
  ["real instead of fixed simulation delta", (e) => e.runtime.frames[20].appDeltaSeconds = 0.4, /simulation times/],
  ["family time from another frame", (e) => e.runtime.frames[20].worldSeconds += 1 / 30, /simulation times|timeline/],
  ["nonfinite exposure", (e) => e.runtime.frames[20].linearPreExposure = NaN, /exposure/],
  ["overlapping PNG write timeline", (e) => e.runtime.frames[20].requestWallSeconds -= 1, /wall-time/],
  ["source viewpoint drift", (e) => e.runtime.sourceViewpoints.terrace.eyeCm[0] += 1, /source viewpoint/],
  ["dynamic resolution", (e) => e.runtime.qualitySettings["r.DynamicRes.OperationMode"] = "1", /quality setting/],
  ["crash after success report", (e) => e.outcome.signal = "SIGSEGV", /exit cleanly/],
  ["runtime material fallback", (e) => e.runtimeLog = "Default Material will be used", /shader fallback/],
  ["package mutation", (e) => e.payloadAfter.status = "changed", /Packaged payload/],
]) test(`rejects ${name}`, () => { const e = fixture(); mutate(e); const report = inspectMotionRun(e); assert.equal(report.status, "failed"); assert.match(report.errors.join("\n"), pattern); });

test("comparison permits different startup material times and records them, with no AA winner", () => {
  const a = comparisonFixture(2), b = comparisonFixture(5);
  for (const frame of b.runtime.frames) { frame.worldSeconds += 0.2; frame.realSeconds += 0.3; frame.requestWallSeconds += 400; }
  const report = compareMotionRuns(a, b);
  assert.equal(report.status, "matched-camera-aa-sequences", report.errors.join("\n"));
  assert.ok(Math.abs(report.timeDifferences[0].worldSecondsBMinusA - 0.2) < 1e-9);
  assert.equal(report.qualityWinner, null); assert.equal(report.fpsMeasured, false);
});

test("closed capture modes explicitly pin TSR200 and TSR100 while retaining old AA commands", () => {
  assert.equal(motionExecCmds(motionCaptureMode("tsr")), "-ExecCmds=r.SMAA.Quality 3,r.AntiAliasingMethod 4,r.TSR.History.ScreenPercentage 200");
  assert.equal(motionExecCmds(motionCaptureMode("tsr100")), "-ExecCmds=r.SMAA.Quality 3,r.AntiAliasingMethod 4,r.TSR.History.ScreenPercentage 100");
  assert.equal(motionExecCmds(motionCaptureMode("taa")), "-ExecCmds=r.SMAA.Quality 3,r.AntiAliasingMethod 2");
  for (const unknown of ["tsr150", "tsr200", "TSR100", "constructor", "__proto__", null, undefined])
    assert.throws(() => motionCaptureMode(unknown), /Choose/);
  assert.throws(() => motionExecCmds({ ...motionCaptureMode("tsr100"), tsrHistoryScreenPercentage: 200 }), /closed mode/);
});

for (const mode of ["tsr", "tsr100"]) test(`${mode} validates actual history, and the saved request survives JSON round-trip`, () => {
  const saved = JSON.parse(JSON.stringify(fixture(4, mode)));
  const report = inspectMotionRun(saved);
  assert.equal(report.status, "fixed-simulation-motion-evidence-validated", report.errors.join("\n"));
  assert.deepEqual(inspectMotionRequest(saved.runtime, saved.captureRequest, saved.args).errors, []);
  assert.equal(report.requestValidation.expected.tsrHistoryScreenPercentage, mode === "tsr" ? 200 : 100);
  assert.ok(report.pending.includes("internal-raster-and-history-dimensions-from-gpu-pass-evidence"));
});

for (const [name, mutate, pattern] of [
  ["requested100 but actual200", (e) => e.runtime.qualitySettings["r.TSR.History.ScreenPercentage"] = "200", /history differs/],
  ["missing native history", (e) => delete e.runtime.qualitySettings["r.TSR.History.ScreenPercentage"], /history differs/],
  ["unrecognized native history150", (e) => e.runtime.qualitySettings["r.TSR.History.ScreenPercentage"] = "150", /history differs/],
  ["history changed during sequence", (e) => e.runtime.qualitySettingsUnchanged = false, /unchanged quality/],
  ["null request metadata", (e) => e.captureRequest = null, /Choose/],
  ["tampered request100 metadata200", (e) => e.captureRequest.tsrHistoryScreenPercentage = 200, /closed capture mode/],
  ["saved command requests200 metadata100", (e) => e.args[1] = motionExecCmds(motionCaptureMode("tsr")), /closed capture mode/],
  ["duplicate ExecCmds", (e) => e.args.push(e.args[1]), /closed capture mode/],
  ["new command without request metadata", (e) => delete e.captureRequest, /exact original/],
  ["actual AA fallback with matching self metadata", (e) => { e.runtime.requestedAA = 2; e.runtime.qualitySettings["r.AntiAliasingMethod"] = "2"; }, /Actual native AA/],
]) test(`saved TSR100 evidence rejects ${name}`, () => {
  const saved = JSON.parse(JSON.stringify(fixture(4, "tsr100"))); mutate(saved);
  const report = inspectMotionRun(saved);
  assert.equal(report.status, "failed"); assert.match(report.errors.join("\n"), pattern);
});

test("legacy exact commands remain revalidatable; they cannot silently request history100", () => {
  for (const aa of [1, 2, 4, 5]) {
    const e = fixture(aa); delete e.captureRequest;
    e.args[1] = `-ExecCmds=r.SMAA.Quality 3,r.AntiAliasingMethod ${aa}`;
    assert.equal(inspectMotionRun(e).status, "fixed-simulation-motion-evidence-validated");
    if (aa === 4) {
      e.runtime.qualitySettings["r.TSR.History.ScreenPercentage"] = "100";
      assert.match(inspectMotionRun(e).errors.join("\n"), /requested 200/);
    }
    e.args[1] += ",r.TSR.History.ScreenPercentage 100";
    assert.match(inspectMotionRun(e).errors.join("\n"), /exact original/);
  }
});

test("comparison admits only the symmetric TSR100/200 history delta, without a winner or FPS claim", () => {
  const a = comparisonFixture(4, "tsr"), b = comparisonFixture(4, "tsr100");
  for (const [x, y, expected] of [[a, b, [200, 100]], [b, a, [100, 200]]]) {
    const report = compareMotionRuns(x, y);
    assert.equal(report.status, "matched-camera-aa-sequences", report.errors.join("\n"));
    assert.equal(report.comparisonKind, "tsr-history-screen-percentage");
    assert.deepEqual(report.controlledDifference, { setting: "r.TSR.History.ScreenPercentage", a: expected[0], b: expected[1] });
    assert.equal(report.qualityWinner, null); assert.equal(report.fpsMeasured, false);
  }
  delete a.report.captureRequest;
  a.report.args[1] = "-ExecCmds=r.SMAA.Quality 3,r.AntiAliasingMethod 4";
  assert.equal(compareMotionRuns(a, b).status, "matched-camera-aa-sequences");
});

for (const [name, mutate, pattern] of [
  ["same TSR history", (b) => { b.runtime.qualitySettings["r.TSR.History.ScreenPercentage"] = "200"; b.report.captureRequest = motionCaptureMode("tsr"); b.report.args[1] = motionExecCmds(b.report.captureRequest); }, /Choose different/],
  ["history150", (b) => b.runtime.qualitySettings["r.TSR.History.ScreenPercentage"] = "150", /history differs/],
  ["shadow quality drift", (b) => b.runtime.qualitySettings["sg.ShadowQuality"] = "2", /quality settings/],
  ["history update quality drift", (b) => b.runtime.qualitySettings["r.TSR.History.UpdateQuality"] = "1", /quality settings/],
  ["rendered AA fallback", (b) => b.runtime.frames[15].antiAliasingMethod = 2, /rendered AA/],
  ["package provenance drift", (b) => b.report.packageReceiptSha256 = "5".repeat(64), /provenance/],
]) test(`TSR history comparison rejects ${name}`, () => {
  const a = comparisonFixture(4, "tsr"), b = comparisonFixture(4, "tsr100"); mutate(b);
  const report = compareMotionRuns(a, b);
  assert.equal(report.status, "failed"); assert.match(report.errors.join("\n"), pattern);
});

test("cross-AA comparisons still forbid history drift even when one arm is TSR100", () => {
  const taa = comparisonFixture(2), tsr100 = comparisonFixture(4, "tsr100");
  assert.match(compareMotionRuns(taa, tsr100).errors.join("\n"), /quality settings/);
  assert.equal(compareMotionRuns(taa, comparisonFixture(4, "tsr")).status, "matched-camera-aa-sequences");
});
for (const [name, mutate, pattern] of [
  ["cross-AA source revision", (b) => b.report.sourceManifestSha256 = "9".repeat(64), /provenance/],
  ["cross-AA camera shift", (b) => b.runtime.frames[20].eyeCm[0] += 0.02, /camera differs/],
  ["cross-AA lens shift", (b) => b.runtime.frames[20].horizontalFovDegrees += 0.01, /camera differs/],
  ["cross-AA quality downgrade", (b) => b.runtime.qualitySettings["sg.ShadowQuality"] = "1", /quality settings/],
  ["failed evidence reused", (b) => b.report.status = "failed", /validated full sequence/],
]) test(`rejects ${name}`, () => { const a = comparisonFixture(2), b = comparisonFixture(5); mutate(b); const report = compareMotionRuns(a, b); assert.equal(report.status, "failed"); assert.match(report.errors.join("\n"), pattern); });

test("canonical quintic has exact endpoints and zero-displacement pre/tail frames", () => {
  const { viewpoints } = fixture();
  assert.deepEqual(expectedMotionPose(viewpoints, 0), expectedMotionPose(viewpoints, 3));
  assert.deepEqual(expectedMotionPose(viewpoints, 51), expectedMotionPose(viewpoints, 63));
  assert.deepEqual(expectedMotionPose(viewpoints, 0).eyeCm, viewpoints.views[0].eyeCm);
  assert.deepEqual(expectedMotionPose(viewpoints, 63).eyeCm, viewpoints.views[1].eyeCm);
});

const chunk = (name, data) => { const out = Buffer.alloc(data.length + 12); out.writeUInt32BE(data.length); out.write(name, 4); data.copy(out, 8); out.writeUInt32BE(crc32(out.subarray(4, 8 + data.length)), 8 + data.length); return out; };
function png(width = 3840, truncatePixels = false) {
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(width); ihdr.writeUInt32BE(2160, 4); ihdr[8] = 8; ihdr[9] = 6;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(Buffer.alloc(truncatePixels ? 10 : (width * 4 + 1) * 2160))), chunk("IEND", Buffer.alloc(0))]);
}
test("PNG gate decodes the actual 4K stream; rejects scaled, truncated or incomplete data", () => {
  const image = png();
  assert.deepEqual(inspectMotionPng(image).pixels, [3840, 2160]);
  assert.throws(() => inspectMotionPng(png(1920)), /native 3840/);
  assert.throws(() => inspectMotionPng(image.subarray(0, -5)), /Truncated/);
  assert.throws(() => inspectMotionPng(png(3840, true)), /incomplete/);
  const corrupt = Buffer.from(image); corrupt[20] ^= 1;
  assert.throws(() => inspectMotionPng(corrupt), /CRC/);
});
