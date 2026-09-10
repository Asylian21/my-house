/** Validate recorded rendering/presentation separately from visual or accessibility acceptance. */
export function inspectPresentation(runtime, png, includeUI, runtimeLog = "") {
  const errors = [], check = (condition, message) => { if (!condition) errors.push(message); };
  check(!/invalid ShaderMap|uncooked shader map|Failed to compile Material|Default Material will be used|Fatal error:|Assertion failed:|Ensure condition failed:|Handled ensure/i.test(runtimeLog),
    "Runtime log contains a shader fallback, handled ensure or fatal failure");
  const presentation = runtime?.presentation ?? {}, settings = runtime?.renderSettings ?? {};
  const is4K = (pixels) => Array.isArray(pixels) && pixels[0] === 3840 && pixels[1] === 2160;
  check(presentation.initialized === true && presentation.separateSceneRenderTarget === true
    && presentation.fixedSceneSize === true && presentation.aspectContainerAttachedToWindow === true
    && presentation.windowHostViewportInterfaceValid === true,
  "The separate fixed scene target and aspect container were not initialized");
  check(is4K(presentation.sceneViewportPixels) && is4K(presentation.sceneRenderTargetPixels)
    && runtime?.gameViewportWasAtLeast4KThroughoutBenchmark === true && runtime?.viewportChangedDuringBenchmark === false,
  "The scene did not retain a stable 3840 by 2160 target");
  check(runtime?.sceneRenderTargetWas4KThroughoutBenchmark === true && runtime?.separateSceneRenderTargetThroughoutBenchmark === true
    && runtime?.renderPercentagesNativeThroughoutBenchmark === true && is4K(runtime?.minimumSceneRHITexturePixelsDuringBenchmark),
  "The native GPU scene target and sampling percentages were not observed throughout the benchmark");
  check(runtime?.rhi === "Metal" && runtime?.shaderPlatform === "METAL_SM6"
    && settings["r.ScreenPercentage"] === 100 && settings["r.SecondaryScreenPercentage.GameViewport"] === 100
    && settings["r.DynamicRes.OperationMode"] === 0, "Native Metal SM6 rendering at 100 percent was not observed");
  const finalView = runtime?.finalViewPostProcessSettings ?? {};
  check(finalView.status === "observed-composed-main-view" && finalView.unscaledViewWidth === 3840
    && finalView.unscaledViewHeight === 2160, "The composed main view was not native 4K");
  check(presentation.windowInsideMonitorWorkArea === true, "The presentation window extends beyond its monitor work area");
  const draw = presentation.slateViewportDrawSizeScreenUnits;
  check(Array.isArray(draw) && draw.every(Number.isFinite) && draw[1] > 0
    && Math.abs(draw[0] - draw[1] * 16 / 9) <= 2, "The viewport presentation does not preserve 16:9 aspect");
  const dimensions = png?.length >= 24 && png.subarray(0, 8).toString("hex") === "89504e470d0a1a0a"
    ? [png.readUInt32BE(16), png.readUInt32BE(20)] : [];
  check(runtime?.screenshotSaved === true && dimensions.length === 2
    && JSON.stringify(dimensions) === JSON.stringify(runtime?.screenshotPixels), "Captured PNG dimensions do not match the runtime report");
  check(includeUI ? runtime?.screenshotKind === "fitted-slate-ui-capture-actual-window-pixels"
    : runtime?.screenshotKind === "fixed-4k-scene-render-target-preserving-view-history" && is4K(dimensions),
  "The screenshot does not match its declared scene or UI capture kind");
  return { status: errors.length ? "failed" : "fixed-4k-scene-and-fitted-presentation-validated", errors,
    screenshotPixels: dimensions, includesUI: includeUI,
    scope: "Recorded native scene resolution, aspect and fitted window only; onscreen control bounds, image quality, accessibility and motion remain separate checks." };
}
