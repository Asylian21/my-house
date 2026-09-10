/** Check native AA observations and executed GPU passes; never certify image or motion quality. */
export function inspectAntiAliasing(runtime, profileText, mode) {
  const errors = [], check = (value, message) => { if (!value) errors.push(message); };
  const expected = mode === "taa" ? 2 : mode === "smaa" ? 5 : null;
  const settings = runtime?.renderSettings ?? {}, view = runtime?.finalViewPostProcessSettings ?? {};
  const rt = view.renderThreadAntiAliasing ?? {};
  check(expected !== null, "Unknown AA experiment");
  check(settings["r.AntiAliasingMethod"] === expected && view.antiAliasingMethod === expected
    && rt.antiAliasingMethod === expected, "Requested, composed and rendered AA methods differ");
  check(rt.status === "observed-render-thread-main-view" && rt.observedRenderThreadSamples >= 300,
    "Missing render-thread AA observations");
  check(settings["r.ScreenPercentage"] === 100 && settings["r.SecondaryScreenPercentage.GameViewport"] === 100
    && settings["r.DynamicRes.OperationMode"] === 0, "AA experiment used scaling or dynamic resolution");
  check(rt.unscaledViewRectPixels?.width === 3840 && rt.unscaledViewRectPixels?.height === 2160
    && rt.familyRenderTargetWidth === 3840 && rt.familyRenderTargetHeight === 2160,
  "Rendered main view or family target was not native 4K");
  check(view.showFlagPostProcessing === true && view.showFlagAntiAliasing === true
    && rt.showFlagPostProcessing === true && rt.showFlagAntiAliasing === true,
  "AA or postprocessing was disabled");
  check(rt.projectionJitterFinite === true && Number.isFinite(rt.projectionJitterX) && Number.isFinite(rt.projectionJitterY),
    "Projection jitter was not measured");
  check(runtime?.gpuProfile?.status === "profile-log-observed" && runtime.gpuProfile.artifactSaved === true
    && runtime.gpuProfile.artifactTruncated === false && /GPU Profile for Frame/.test(profileText ?? ""),
  "Missing complete native GPU profile");
  if (mode === "taa") {
    check(settings["r.TemporalAA.Quality"] === 2 && settings["r.TemporalAA.Upsampling"] === 0
      && settings["r.TemporalAA.HistoryScreenPercentage"] === 100, "TAA quality, upsampling or history differs");
    check(view.showFlagTemporalAA === true && rt.showFlagTemporalAA === true, "Temporal AA show flag was disabled");
    check(/TAA\(Main Quality=High\) 3840x2160 -> 3840x2160/.test(profileText ?? ""),
      "No executed full-resolution high-quality TAA main pass");
  } else if (mode === "smaa") {
    check(settings["r.SMAA.Quality"] === 3 && settings["r.SMAA.EdgeMode"] === 0
      && settings["r.SMAA.DebugVisualization"] === 0, "SMAA quality, edge or debug mode differs");
    check(Math.abs(rt.projectionJitterX) <= 1e-12 && Math.abs(rt.projectionJitterY) <= 1e-12,
      "Spatial SMAA retained temporal projection jitter");
    check(["SMAAedgeDetection", "SMAABlendingWeightCalculation", "SMAANeighborhoodBlending"]
      .every((event) => profileText?.includes(event)), "The complete three-pass SMAA pipeline was not observed");
  }
  return { status: errors.length ? "failed" : "native-aa-experiment-observed", mode, errors,
    scope: "Requested and observed AA method, public view/target dimensions and named GPU passes. TAA pass events include internal input/output dimensions; SMAA events do not. Image sharpness, temporal stability and performance acceptance remain separate." };
}
