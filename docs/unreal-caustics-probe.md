# Isolated caustics diagnostic plugin

**Current water state, 9 September:** the diagnostic now consumes the saved twelve-wave material through a separate pinned binding. Two clean Metal captures passed independent transport validation. See [current water-binding evidence](unreal-caustics-water-binding.md). Historical four-wave receipts and identity-policy bytes described below remain preserved; no production light consumer is enabled.

**Isolated consumer controls, 9 September:** the separate candidate Editor now completes inactive, zero and constant native 4K composite controls. Constant RGB matches an explicitly declared empirical toward-zero model exactly; the original failed half-ULP result is preserved. See [consumer evidence and remaining physical integration](unreal-caustics-consumer.md). This does not enable production caustic lighting.

`unreal/BreziTwin/Plugins/BreziCausticsProbe` contains an optional diagnostic Mac plugin. **Native compilation and a second Metal capture completed with a clean process exit. That capture initially failed strict object-identity validation; a separate, unchanged copy now passes diagnostic source-transport validation with explicitly listed float32 ambiguities.** The result is 117,545 exact object matches, 215 listed ambiguities and zero unexplained mismatches. The original failed receipt and photon bytes are preserved. This is neither production caustic lighting nor photorealism evidence. The adopted policy is documented in [unreal-caustics-identity.md](unreal-caustics-identity.md); the earlier design is in [unreal-caustics-implementation.md](unreal-caustics-implementation.md).

The plugin descriptor has `EnabledByDefault: false`; enabling it needs no project descriptor or game-code change. Even when the module is built and loaded, it creates no view extension without `-BreziCausticsProbe`. That process flag permits the diagnostic atlas. `-BreziCausticsCapture` additionally requests one asynchronous readback. Console variables cannot bypass the process opt-in. The atlas has no consumer in scene materials, lights, postprocessing or production render targets. It adds no visual energy and modifies no actors or canonical geometry.

## Frozen source binding

`Resources/source-binding.json` records the authorized rebinding from scene `97f3af06…` to `61ba228f…`. Before rebinding, `output/unreal/hidden-collision-source-proof.json` and all source hashes were checked: the complete canonical OBJ remains `a42e9eb1…`; every field retained in all 45 receiver records matches the current canonical record; all 1,076 triangle positions, source face identities and 359 BVH nodes remain unchanged. Optics and viewpoint files retain their prior hashes. Only the scene SHA field in the receiver contract changed. The new complete contract SHA256 is `c7c8011b3d7623e8780c30ea77775472a0cab7ebefa0f5cb97528f96580d404a`.

The plugin pins the resource bytes in compiled code. SHA256 remains the receipt/capture identity; UE's public `FSHA1::HashBuffer` supplies a runtime byte-integrity check against the compiled resource pin. The parser reads the pinned byte buffer, then requires `Content/Data/walking.json` scene/OBJ provenance to match. This is a source-binding check, not a substitute for the application's saved-map/native collision validation. New geometry requires explicit receiver review and new pins; silently accepting another scene is forbidden.

The portable read-only validator verifies exact source OBJ faces when requested:

```sh
python3 unreal/BreziTwin/Plugins/BreziCausticsProbe/Tools/verify_contract.py --source-root /Users/davidzita/www/dom
node --test tests/unreal-caustics.test.mjs
```

The six Node test groups cover full BVH ownership and source pins, a synthetic positive photon/half-float atlas, ten corrupt/foreign/transport cases and 24 identity-policy cases. They reject modified policy bytes independently in the helper and validator, floor or BRDF reclassification, out-of-bound hits, Fresnel/Beer errors and energy-preserving atlas rearrangement. Gates remain active under `python -O`. Failed validation atomically replaces any earlier success receipt in the directory being validated; historical evidence must therefore be copied before revalidation. Tests use only CPU and the Python standard library.

## Build and opt-in execution — root-coordinated

Do not edit `.uproject` to enable this diagnostic for ordinary builds. UE5.8's `TargetRules.cs` exposes the singular build flag `-EnablePlugin=`; `PluginManager.cpp` exposes the plural runtime flag `-EnablePlugins=`. After the parent releases the build/GPU window, a project Editor build can include this one module:

```sh
'/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh' BreziTwinEditor Mac Development \
  -Project=/Users/davidzita/www/dom/unreal/BreziTwin/BreziTwin.uproject \
  -EnablePlugin=BreziCausticsProbe -Module=BreziCausticsProbe -WaitMutex
```

A separately coordinated Metal run can use the Editor binary in game mode:

```sh
'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor' \
  /Users/davidzita/www/dom/unreal/BreziTwin/BreziTwin.uproject \
  -game -EnablePlugins=BreziCausticsProbe -BreziCausticsProbe -BreziCausticsCapture -BreziView=pool -log
```

This diagnostic launch is not a standalone packaged app or 4K performance test. Do not use `-nullrhi` as GPU evidence. Leave enough frames for both readbacks and the async writer, and wait for `BREZI_CAUSTICS_CAPTURE <directory>` before ending the run. Normal teardown stops scheduling on `OnEnginePreExit`, drains render commands, and waits for an active file writer. A pending GPU readback logs `BREZI_CAUSTICS_CAPTURE_INCOMPLETE`; it never becomes a success receipt. Dynamic module reload is disabled.

The capture directory under `Saved/CausticsProbe/<uuid>` contains `capture.json`, the exact receiver contract, 48-byte float32 photon records, and a linear RGBA16F atlas. Validate a fresh capture, or a separate hash-verified copy when preserving a historical result:

```sh
python3 unreal/BreziTwin/Plugins/BreziCausticsProbe/Tools/validate_capture.py /absolute/capture/directory
```

Acceptance requires valid named source object/triangle ownership and footprint, separately reported exact object matches/listed ambiguities/unexplained mismatches, and an unexplained ratio strictly below 0.001. The pinned policy permits only 20 directed pairs of 12 exact triangles; each listed ambiguity must also pass its source-derived quantization/ULP bound and 2 micrometre hit cap. Existing gates require matching hit/path error below 2 mm, Fresnel error below 2e-5, Beer–Lambert relative error below 1e-4, CPU floor-flux agreement below 0.5%, half-float atlas flux error below 0.3%, and spatial L1 agreement below 1%. Synthetic fixtures receive a distinct status and are rejected by the native capture CLI. Passing applies to that frozen capture only and never claims exact triangle identity for every photon.

## Local API review and remaining execution risks

The implementation uses public UE5.8 headers: `SceneViewExtension.h` for the deferred post-base-pass callback, `RenderGraphUtils.h` for structured uploads/readback passes, `RHIGPUReadback.h` for buffer size and texture row-pitch lock APIs, and `PipelineStateCache.h` for graphics PSO binding. The required empty vertex declaration is declared by `CommonRenderResources.h`; static RHI state templates come from `RHIStaticStates.h`. The HLSL variable formerly named `sample` was renamed to avoid the interpolation keyword. Shared source buffers remain immutable, source UObject access stays on the game thread, and GPU work receives only copied data.

Module-only native compilation passed in 6.25 seconds after replacing the no-op legacy GPU scope with `RDG_EVENT_SCOPE_STAT` and the deprecated delegate with `FCoreDelegates::GetOnPostEngineInit()`. The second run exercised Metal shader binding, RGBA16F additive blending and readback layout, and exited cleanly. Independent validation of its copied capture passed the spatial/energy gates under the listed identity policy. Further runs must preserve compiler/runtime logs and fail on shader errors. A capture receipt is insufficient without a clean process exit and independent validation. No GPU time, frame-rate budget or 4K benefit is claimed here.

The model remains single refraction at the authored mean water plane. It uses the four authored normal waves, collimated sunlight, underwater first-hit occlusion and absorption/scattering extinction. It does not implement above-water solar visibility, a finite solar disk, multi-bounce transport, wall/step atlases, calibrated lux-to-RGB radiance or BRDF/pre-exposure integration. The floor atlas must not be added to full direct sunlight as emissive energy.

## First actual attempt, 8 September 2026

The direct Editor renderer PID 88110 exited with process code 1. Its log reports a fatal `FMacAccessibilityElement::dealloc` main-thread assertion at `MacAccessibilityElement.cpp:169`, reached through an Objective-C block release in `ProcessGameThreadEvents`. A preceding `SlateViewport.IsValid()` ensure came from `FDefaultGameMoviePlayer::WaitForMovieToFinish` → `RegisterGameViewport`. Both occurred in the native game's Editor `-game` startup, outside the caustics module. No native game source was modified in this probe task.

The engine reached its first rendering frame, but no `Saved/CausticsProbe/*/capture.json` existed and no independent capture validation could run. No plugin shader compilation failure was observed; this does not prove a correct GPU atlas. Source input hashes remained unchanged during the run, and the actual UnrealEditor/UnrealEditor-Cmd/BreziTwin renderer process inventory was empty afterward. The module remains disabled by default.

Evidence: `output/unreal/caustics-probe-module-build.log` and `output/unreal/caustics-probe-runtime/76cc2b8e-6505-4570-9d0c-bf7d189becbe/{engine.log,stdout.log,process.json,probe-result.json,startup-sample.txt}`. The attempt used the native benchmark-only flags solely to request eventual normal exit, without a PNG capture flag. It is neither a packaged app test nor 4K performance proof. The parent subsequently fixed startup before the second attempt.

## Second capture and separate adopted-policy revalidation

The second renderer PID 93925 exited 0 with no ensure, fatal or shader-error marker and unchanged inputs during the run. Its [original process receipt](../output/unreal/caustics-probe-runtime/bfb7b327-9f1d-4006-9291-4a9fab416e56/process.json) records the exact flags and hashes. The [original strict failed validation](../output/unreal/caustics-probe-runtime/bfb7b327-9f1d-4006-9291-4a9fab416e56/Saved/CausticsProbe/A004EBD2-7345-9F86-0046-C39CA2E652E6/reference-validation.json) remains byte-identical: 215 of 117,760 object IDs differed, exceeding the former unpartitioned 0.1% gate.

All 215 differences are the explicitly listed pool-wall/coping triangle candidates whose source planes are 152 nanometres apart and collapse to one uploaded float32 plane. They retain distinct source identities. After policy review, only CPU validation ran on a fresh frozen copy: [revalidation report](../output/unreal/caustics-probe-revalidation/9d21158f-9c8c-458a-842e-634038c3333f/revalidation-report.json), [complete comparator receipt](../output/unreal/caustics-probe-revalidation/9d21158f-9c8c-458a-842e-634038c3333f/reference-validation.json) and [copy/hash manifest](../output/unreal/caustics-probe-revalidation/9d21158f-9c8c-458a-842e-634038c3333f/copy-manifest.json). The status is `GPU-capture-source-transport-validated-with-listed-f32-ambiguities`; exact/listed/unexplained counts are 117,545/215/0. Maximum listed hit difference is 0.473 micrometres; floor-atlas flux error is 0.1118%. The original total mismatch ratio remains reported. The threshold for unexplained mismatches remains strictly below 0.001. Revalidation launched no new GPU, engine or build.

## Read-only production-consumption assessment

The existing atlas cannot simply multiply lit scene color or feed water's Color Scale Behind Water input: both contain contributions beyond direct sunlight. UE's local `SingleLayerWaterShading.ush:201–212` already applies `exp(-verticalDepth * extinction)` to the fully lit underwater scene, then applies the water-to-camera transmittance at lines 221–238. The photon atlas already includes incoming Fresnel and extinction over each refracted path. A raw multiplication would duplicate incoming absorption; the outgoing view absorption must remain. This ordering agrees with Epic's [Single Layer Water description](https://dev.epicgames.com/documentation/en-us/unreal-engine/single-layer-water-shading-model-in-unreal-engine).

For a diffuse, unshadowed horizontal receiver only, a dimensionless correction to isolated stock direct sunlight would be `atlasRGB / (cosSun * exp(-extinctionRGB * depth))`. It should carry neither a second BRDF factor nor pre-exposure. UE's light pass applies exposure once at `DeferredLightPixelShaders.usf:455`. This equation is not sufficient for the current production floor: its roughness is 0.64 with specular response, the atlas retains no incident-direction distribution, and stock straight-ray shadows can be zero where a refracted path is illuminated. Division by an epsilon would invent energy. A complete consumer must replace the bounded direct-sun contribution, preserve other illumination, and evaluate the receiver BRDF with the refracted directions.

Public `ULightComponent::SetLightFunctionMaterial` and scale/fade setters exist, but a light function is an unsuitable HDR consumer here. The legacy shader reduces RGB to grayscale and writes an 8-bit UNORM shadow mask (`LightFunctionPixelShader.usf:62–78`, `LightRendering.cpp:1897`); the atlas is also 8-bit UNORM (`LightFunctionAtlas.cpp:704`). The frozen photon atlas peaks at 3.40625/3.98047/4.15625 per unit incident sunlight, corresponding to diffuse no-shadow correction peaks of approximately 8.65/9.00/9.10. Clamping those peaks would lose focusing energy. Atlas-compatible materials cannot depend on world position, depth or the GBuffer; see Epic's [Light Function restrictions](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-light-functions-in-unreal-engine). That page still says directional lights bypass the atlas, while this local UE5.8 branch's `CanLightUsesAtlasForUnbatchedLight` checks material compatibility without a directional-type exclusion. The HDR/receiver-isolation blockers apply to either route.

The smallest viable next prototype remains diagnostic above-water sun visibility. Public `FXRenderingUtils.h:89` exposes `UE::FXRenderingUtils::RayTracing::GetRayTracingSceneViewRDG`; `SceneViewExtension.h` exposes the post-TLAS callback and inline-ray-tracing flags. Use only the already active HWRT main view, bind the per-view TLAS in the same RDG graph, convert source metres to translated-world centimetres and trace opposite the incident travel direction. Record blocked/unblocked results against source-derived rays and view/culling settings. A TLAS miss alone is not full optical visibility: the scene is camera-culled, Nanite defaults to a fallback mesh, and the stock inline helper forces opaque treatment of masked leaves. Correct leaf alpha, transmission and off-camera coverage remain unresolved. A separate source-pinned above-water BVH is a fallback for explicitly covered static opaque geometry; collision traces and the current 45 pool-receiver BVH are insufficient.

A later owned HDR direct-light pass can in principle run before SingleLayerWater color composition using public render-extension stages, with a strict source receiver mask and coordinated light-channel exclusion of the stock floor sun. The public post-opaque callback is too late, and post-base occurs before post-TLAS, so same-frame visibility must be scheduled carefully. This is a proposed integration path, not an implemented or validated consumer. No emissive material, global sunlight rescale, BRDF change or production binding was added during this assessment.

## Opaque solar visibility controls on Metal, 8 September 2026

The optional plugin now includes a separate, opt-in diagnostic using the
public `PostTLASBuild_RenderThread` callback and current-view TLAS SRV. Six
source-pinned rays exercise three unblocked pool samples and three off-aperture
roof hits. Game-thread sun/cvar observations are paired by scene identity,
engine frame counter and render-family number. The same actual view supplies
the shader uniform buffer. This does not inject any light or change the
existing photon transport shader or receiver ambiguity policy.

The first native attempt preserved a handled shader-binding ensure for an
unbound `View` parameter, and remains rejected:
`output/unreal/solar-probe-runtime/pool-173efa46-80d3-42dc-b603-e8af2a548523/`.
The corrected module compiled in 7.44 seconds. Two subsequent actual
Editor-game Metal processes exited 0 with clean logs and passed independent
buffer/source validation:

- Pool: `output/unreal/solar-probe-runtime/pool-a21bcddf-647f-40ee-b1d2-602338e12609/`, PID 22720.
- Street: `output/unreal/solar-probe-runtime/street-1e610afd-442e-4fe4-adf3-4a8e7e3622ea/`, PID 23080.

`output/unreal/solar-probe-runtime/comparison-4f58bc4d-5a0a-4c84-b8a5-ec4fce98555a.json`
revalidates both original buffers, logs and process receipts. The cameras are
22.9098 m apart; all six classifications match. Maximum hit-distance change
between the views is 0.0000007153 cm. A separate `.inputs.json` sidecar proves
that all recorded scene/map, game/module binary and source inputs were also
identical between those runs and unchanged during each process.

The roof controls originate 2 cm before exact source faces; the maximum pool-
view distance discrepancy is 0.000098 cm. Their native TLAS IDs are recorded
but are not asserted to be canonical DOM IDs. The positive controls are away
from the water aperture and do not imply a roof shadow on the pool. This is
bounded opaque visibility evidence for six rays and two views, not complete
optical occlusion, alpha-tested foliage, glass transmission, general camera
independence, standalone-app delivery or production caustics. The plugin
remains disabled by default, and `productionLightingBound` remains false.
