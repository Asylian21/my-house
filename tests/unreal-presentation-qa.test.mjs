import test from "node:test";
import assert from "node:assert/strict";
import { inspectPresentation } from "../scripts/unreal/presentation-qa.mjs";
import { inspectAntiAliasing } from "../scripts/unreal/antialiasing-qa.mjs";

function observation(ui = false) {
  // Header-only parser input. This is not a rendered PNG or native evidence.
  const pixels = ui ? [1600, 925] : [3840, 2160], png = Buffer.alloc(24);
  Buffer.from("89504e470d0a1a0a", "hex").copy(png);
  png.writeUInt32BE(pixels[0], 16); png.writeUInt32BE(pixels[1], 20);
  return { png, runtime: { presentation: { initialized: true, separateSceneRenderTarget: true, fixedSceneSize: true,
    aspectContainerAttachedToWindow: true, windowHostViewportInterfaceValid: true,
    sceneViewportPixels: [3840, 2160], sceneRenderTargetPixels: [3840, 2160], windowInsideMonitorWorkArea: true,
    slateViewportDrawSizeScreenUnits: [1600, 900] },
  gameViewportWasAtLeast4KThroughoutBenchmark: true, viewportChangedDuringBenchmark: false,
  sceneRenderTargetWas4KThroughoutBenchmark: true, separateSceneRenderTargetThroughoutBenchmark: true,
  renderPercentagesNativeThroughoutBenchmark: true, minimumSceneRHITexturePixelsDuringBenchmark: [3840, 2160],
  rhi: "Metal", shaderPlatform: "METAL_SM6", renderSettings: { "r.ScreenPercentage": 100,
    "r.SecondaryScreenPercentage.GameViewport": 100, "r.DynamicRes.OperationMode": 0 },
  finalViewPostProcessSettings: { status: "observed-composed-main-view", unscaledViewWidth: 3840, unscaledViewHeight: 2160 },
  screenshotSaved: true, screenshotPixels: pixels,
  screenshotKind: ui ? "fitted-slate-ui-capture-actual-window-pixels" : "fixed-4k-scene-render-target-preserving-view-history" } };
}

test("a fitted UI capture may have fewer pixels than the native scene", () => {
  const { runtime, png } = observation(true);
  assert.equal(inspectPresentation(runtime, png, true).errors.length, 0);
  assert.equal(inspectPresentation(runtime, png, false).status, "failed");
});

test("scene-only capture must retain true 4K pixels", () => {
  const { runtime, png } = observation();
  assert.equal(inspectPresentation(runtime, png, false).errors.length, 0);
  png.writeUInt32BE(1920, 16);
  runtime.screenshotPixels[0] = 1920;
  assert.equal(inspectPresentation(runtime, png, false).status, "failed");
});

for (const [name, edit] of [
  ["clipped window", (r) => { r.presentation.windowInsideMonitorWorkArea = false; }],
  ["stretched aspect", (r) => { r.presentation.slateViewportDrawSizeScreenUnits = [1600, 1000]; }],
  ["lower resolution composed view", (r) => { r.finalViewPostProcessSettings.unscaledViewWidth = 1920; }],
  ["resolution upscaling", (r) => { r.renderSettings["r.ScreenPercentage"] = 50; }],
  ["unregistered outer viewport", (r) => { r.presentation.windowHostViewportInterfaceValid = false; }],
]) test(`rejects ${name}`, () => {
  const { runtime, png } = observation(); edit(runtime);
  assert.equal(inspectPresentation(runtime, png, false).status, "failed");
});

test("a handled startup ensure invalidates otherwise valid presentation evidence", () => {
  const { runtime, png } = observation();
  const result = inspectPresentation(runtime, png, false, "LogOutputDevice: Error: Ensure condition failed: SlateViewport.IsValid()");
  assert.equal(result.status, "failed");
  assert.ok(result.errors.some((error) => error.includes("handled ensure")));
});

function aaObservation() {
  // Synthetic acceptance input only; these strings are not GPU evidence.
  const runtime = observation().runtime;
  Object.assign(runtime.renderSettings, { "r.AntiAliasingMethod": 2, "r.TemporalAA.Quality": 2,
    "r.TemporalAA.Upsampling": 0, "r.TemporalAA.HistoryScreenPercentage": 100 });
  Object.assign(runtime.finalViewPostProcessSettings, { antiAliasingMethod: 2,
    showFlagPostProcessing: true, showFlagAntiAliasing: true, showFlagTemporalAA: true,
    renderThreadAntiAliasing: { status: "observed-render-thread-main-view", observedRenderThreadSamples: 540,
      antiAliasingMethod: 2, showFlagPostProcessing: true, showFlagAntiAliasing: true, showFlagTemporalAA: true,
      projectionJitterFinite: true, projectionJitterX: 0.0001, projectionJitterY: -0.0002,
      unscaledViewRectPixels: { width: 3840, height: 2160 }, familyRenderTargetWidth: 3840, familyRenderTargetHeight: 2160 } });
  runtime.gpuProfile = { status: "profile-log-observed", artifactSaved: true, artifactTruncated: false };
  return { runtime, profile: "GPU Profile for Frame 120\nTAA(Main Quality=High) 3840x2160 -> 3840x2160" };
}

test("AA acceptance requires the observed renderer and full-resolution executed pass", () => {
  const { runtime, profile } = aaObservation();
  assert.equal(inspectAntiAliasing(runtime, profile, "taa").status, "native-aa-experiment-observed");
  runtime.finalViewPostProcessSettings.renderThreadAntiAliasing.antiAliasingMethod = 1;
  assert.equal(inspectAntiAliasing(runtime, profile, "taa").status, "failed");
});

test("requested TAA cannot pass on a scaled or missing GPU main pass", () => {
  for (const profile of ["", "GPU Profile for Frame 120\nTAA(Main Quality=High) 1920x1080 -> 3840x2160"]) {
    assert.equal(inspectAntiAliasing(aaObservation().runtime, profile, "taa").status, "failed");
  }
});

test("spatial SMAA requires all three GPU stages and zero projection jitter", () => {
  const { runtime } = aaObservation();
  runtime.renderSettings["r.AntiAliasingMethod"] = 5;
  Object.assign(runtime.renderSettings, { "r.SMAA.Quality": 3, "r.SMAA.EdgeMode": 0, "r.SMAA.DebugVisualization": 0 });
  runtime.finalViewPostProcessSettings.antiAliasingMethod = 5;
  const rt = runtime.finalViewPostProcessSettings.renderThreadAntiAliasing;
  Object.assign(rt, { antiAliasingMethod: 5, projectionJitterX: 0, projectionJitterY: 0 });
  const profile = "GPU Profile for Frame 120\nSMAAedgeDetection\nSMAABlendingWeightCalculation\nSMAANeighborhoodBlending";
  assert.equal(inspectAntiAliasing(runtime, profile, "smaa").status, "native-aa-experiment-observed");
  assert.equal(inspectAntiAliasing(runtime, profile.replace("SMAANeighborhoodBlending", ""), "smaa").status, "failed");
  rt.projectionJitterX = 0.0001;
  assert.equal(inspectAntiAliasing(runtime, profile, "smaa").status, "failed");
});
