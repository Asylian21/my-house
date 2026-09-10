# Native AA motion QA

`BreziMotionQA.cpp` and `.h` are integrated in the native player controller.
The Editor build and standalone macOS package passed on 8 September 2026.
No Pawn camera algorithm, source viewpoint, source geometry or production
quality default was changed. The component is dormant in an ordinary launch.

The component activates only with `-BreziMotionQA -BreziMotionAA=<1|2|4|5>` and optionally exits with `-BreziMotionExit`. The standalone runner supplies these flags and an isolated `UserDir`. It rejects old package/native source hashes and another active app/editor process.

```sh
node --test tests/unreal-motion-qa.test.mjs
node scripts/unreal/motion-qa.mjs capture taa
node scripts/unreal/motion-qa.mjs capture smaa
node scripts/unreal/motion-qa.mjs compare <first-run-directory> <second-run-directory>
```

Do not execute capture commands until the renderer slot is explicitly free. Capture is roughly 64 × 4K lossless PNG plus 240 rendered warmup frames, not a throughput benchmark. The runner bounds execution to 660 wall seconds; native timeout is 600 seconds.

The native sequence selects the source terrace camera instantly, establishes the existing engine fixed-rate clock at 30 simulation Hz, observes 240 consecutive GT/RT warmup main views, then captures 4 static frames. After frame 3's screenshot has completed, it calls the existing `SelectView("pool")`; the next 48 pawn ticks advance the unchanged 1.6-second quintic transition, followed by 12 tail frames. Reduce Motion is never changed: an instant jump fails the independent host source-camera gate.

Each normal no-UI/no-HighRes screenshot requires its request and captured callback `GFrameCounter` to equal both GT and RT `FSceneViewFamily::FrameCounter`. Exactly one main view on each thread is required. GT and RT `Family.FrameNumber` must match each other and progress consecutively; they are never equated to the engine frame counter. The callback has no latest-snapshot fallback. Missing screenshots, multiple view families, a delayed callback or any consecutive-frame gap fail the run.

Local UE5.8 source evidence for this pairing:

- `Engine/Source/Runtime/Renderer/Private/SceneRendering.cpp:5421–5450` sets the separate scene frame number and engine frame-counter copy before view extensions.
- `Engine/Source/Runtime/Engine/Private/UnrealClient.cpp:1866–1872` calls viewport Draw, canvas flush, then ProcessScreenShots.
- That file's `ReadPixels` (`61–76`) queues surface readback and flushes rendering commands before returning pixels.
- `GameViewportClient.cpp:2541–2588` broadcasts screenshot pixels only after successful viewport readback, resets the request, then broadcasts processed. The driver requests the following frame only on the next world tick.

The RT snapshot contains actual view-matrix origin, forward, up, projection-derived horizontal FOV, independently recorded `View.FOV`, normalized projection jitter, effective AA, render-target/unscaled-view dimensions, family world/real time and delta, and CPU pre-exposure. Platform wall time and app delta are separate fields. World `RealTimeSeconds` advances by the fixed supplied engine delta; it is not elapsed platform wall time.

`FSceneView` has no public `PreExposure` scalar in this engine. Public view-state `GetPreExposure()` returns the scalar assigned by `FViewInfo::UpdatePreExposure` (`PostProcessEyeAdaptation.cpp:1599`) from the same value copied into shader uniforms (`SceneRendering.cpp:1957`). It is sampled in the exact paired RT family while synchronous screenshot readback prevents a later engine frame from advancing. This is not GPU luminance or tonemap-output readback. No renderer-private header dependency was added.

All completion, failure, timeout and EndPlay paths restore captured engine/FApp clock settings once. Cancellation resets only this driver's matching outstanding screenshot and restores that request's screen-message flag. No screenshot/AA/quality cvars are changed by the component. The runner selects the requested AA method and sets `r.SMAA.Quality=3` in every isolated process. This keeps the quality snapshot identical across TAA, SMAA and TSR except for the chosen method. Production AA remains TSR with history percentage 200.

Host acceptance checks decoded 4K PNG dimensions/CRC/rows/hashes, all 64 frame identities, consecutive engine and scene frames, actual 30 Hz simulation deltas, source camera progression including roll and lens, exact clock restoration getters, runtime fallback/crash logs, unchanged package payload and same native/source provenance. Source-camera tolerances are 0.01 cm position, 0.00002 direction/up component, and 0.001 degree FOV; measured float32 source interpolation differs from double precision by at most 0.000559 cm for the current path. Cross-AA camera tolerance is tighter (0.001 cm, 0.000002 vector component, 0.0001 degree), and every quality setting except chosen AA must match.

The comparison writes a stepping A/B HTML viewer and time/exposure differences. World and material time are not artificially frozen. Water, flames and foliage are excluded from numerical static-quality metrics; currently no pixel quality score is computed. Successful evidence does not establish native display FPS, internal AA history/raster resolution, a quality winner, smooth real-time animation or photorealism.

## Native evidence, 8 September 2026

The first TAA and SMAA runs each passed all 64 decoded 3840×2160 PNGs,
consecutive paired GT/RT frame identities, canonical camera poses and simulation
deltas, exact clock restoration, unchanged package and clean process exit.
The app-scoped AX initializer receipt is copied, hashed and validated on every
motion capture and again when comparing saved evidence.

- TAA: `output/unreal/runtime/motion-taa-5708117b-d895-4bfa-a471-83a26ce74387/`
- SMAA Ultra: `output/unreal/runtime/motion-smaa-b455d4f3-cc3f-4320-864d-1bfb77425a46/`
- TSR history 200: `output/unreal/runtime/motion-tsr-098dac3b-4c02-49bb-93e8-280ca3e75a1d/`
- Validated comparison and stepping viewer: `output/unreal/runtime/motion-comparison-724b90e0-ad78-46a0-bb14-f782cfbd2806/`

All three used native 4K at 100/100 percent, dynamic resolution off, Lumen HWRT,
Nanite and virtual shadow maps. All recorded quality fields except AA match.
The source camera moves from terrace to pool; no input interrupts the path.
Visual inspection of frame 28 shows sharper fine detail with SMAA, but also
visible stair steps on diagonal roof edges. A single still does not establish
temporal stability or an AA quality winner. Default TSR remains unchanged.

The 40 focused host tests for motion and AX acceptance passed. They validate
rejection logic; the independent native evidence above establishes actual
rendered execution. TSR also passed all 64 frames; its validated TAA comparison
is in `output/unreal/runtime/motion-comparison-2c402e6b-7859-469b-ae9b-f8a75ac09ec9/`.
Full sequence visual review remains separate from the automated capture gates.
