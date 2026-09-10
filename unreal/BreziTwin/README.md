# Březí 6012/26 — Unreal macOS application

Initial Unreal Engine 5.8 C++ application scaffold. Geometry and camera coordinates are generated from the shared digital twin; this project does not maintain a second architectural model.

## Inputs

- `/Game/Brezi/Maps/Brezi`: generated scene, imported by the root project pipeline.
- `Content/Data/viewpoints.json`: generated camera data, packaged as Unreal File System data. Its contract is:

```json
{
  "coordinateSystem": "unreal-centimeters",
  "defaultView": "interior",
  "views": [
    {
      "id": "interior",
      "label": "Obývačka",
      "eyeCm": [0, 0, 165],
      "targetCm": [100, 0, 165],
      "horizontalFovDegrees": 75
    }
  ]
}
```

Those numeric values demonstrate the schema only. No fallback cameras or geometry are embedded in the runtime. Vectors must be finite, eye and target distinct, IDs unique, and horizontal FOV within 15–120 degrees. Invalid views are rejected with a log entry. Missing data is visible in the interface.

The glTF importer maps glTF `[x,y,z]` to Unreal `[x,z,y]` with metres converted to centimetres. For the existing Blender Z-up camera configuration, the matching conversion is `[x,y,z] → [100x,-100y,100z]`. The export/import validation must verify this against actual asset bounds before accepting the pipeline.

## Camera and interface

- Generated preset names appear in the bottom view selector; keys 1–4 choose their file order.
- Preset transitions use a 1.6 second quintic easing curve. “Obmedziť pohyb” makes view changes immediate.
- Hold the right mouse button or press F2 to navigate; arrows look around without a mouse. The wheel zooms in orbit.
- M or the camera toggle switches between orbit and validated walking. Walking uses WASD while navigating, Q for precision speed and Shift for faster travel. Tab / Shift+Tab move between controls; Enter / Space activate the focused control.
- F1 or “Ovládanie” opens the controls panel; Escape or “Zavrieť” closes it and restores focus to “Ovládanie”. Escape otherwise restores the cursor. Walking now uses ACharacter/CharacterMovement with source-tagged floors and swept capsule collision; actual traversal QA is still pending. No navigation mesh is required for manual walking. Presets leave walking before their cinematic transition, which can cross geometry.
- N or the daylight button switches an initial day/night lighting study. Imported directional/skylight actors are reused, preferably tagged `BreziSun` and `BreziSky`. Daylight values and orientation come from the imported map; night uses a provisional artistic lighting setup and is not a calculated lunar ephemeris.

The Slate interface uses Slovak text, three compact rounded panels (16 Slate units) and a subtle background blur with a bounded radius of 5. A short camera hint stays under the four views; full keyboard help and motion settings are in “Ovládanie”. The active view has a visible underline, so selection does not rely on color alone. Typography uses the engine's bundled font with restrained tracking and hierarchy; Apple system fonts are not copied or redistributed.

`NSWorkspace` accessibility preferences supply the default Reduce Motion setting and update live through `NSWorkspaceAccessibilityDisplayOptionsDidChangeNotification`. AppKit calls stay on the native main thread and changes are delivered to Unreal's game thread. An intentional “Obmedziť pohyb” choice overrides the system for the current session; “Použiť nastavenie macOS” resumes following it. Enabling reduced motion also completes an active preset transition immediately. Increased Contrast and Reduce Transparency disable the panel blur and make backgrounds opaque; increased contrast additionally strengthens the outlines and secondary text. No accessibility permission prompt is needed to read these display preferences.

Preferences update existing Slate attributes, so changing macOS settings does not recreate controls or steal focus. View buttons are rebuilt only when their source data changes. This is a prototype pending native screenshot and interaction review; native NSVisualEffectView vibrancy, full VoiceOver/accessibility verification and design-award criteria are not claimed.

Native widget accessibility is enabled with `Accessibility.Enable=1`. The Mac bridge is initialized once through the engine's public `FMacApplication::OnVoiceoverEnabled()` after the UI is created, using a synchronous main-thread call while retaining the platform application. This only exposes the Slate accessibility tree; it does not change macOS VoiceOver or start a separate TTS service. UE 5.8's own runtime VoiceOver observer has activation/deactivation disabled due to reported hangs, so this application activates the bridge for its own lifetime. An OnPreShutdown callback now synchronously disables the Mac bridge before Slate replaces its accessibility handler, allowing the engine to invalidate its native timer safely. Native QA must check tree population, activation and shutdown; an active bridge log is not proof of correct spoken interaction.

View buttons have explicit Slovak labels including the current-view state. Night, walking and reduced-motion settings use semantic checkboxes styled as toolbar controls. The controls panel uses a normal accessible button and stays in the same window, with Tab traversal and focus restoration; it avoids `SComboButton`, whose internal button UE 5.8 explicitly excludes from accessibility. Each accessible panel element has its own visibility binding because the Mac wrapper does not infer hidden ancestors. Non-pointer keyboard focus is visible. System preference changes continue to update the same controls in place. The window title is set to “Březí 6012/26” and retried for the first five seconds to accommodate late viewport creation. Runtime JSON now records the actual Slate title; native verification of the retry is pending.

## Walking contract and evidence

`Content/Data/walking.json` supplies the 165 cm eye height, 22 cm capsule radius, native 85 cm capsule half-height, 50/115/240 cm/s speeds, 22 cm step limit and 78 cm drop limit. The capsule is an explicit adaptation of the source ellipsoid, not identical geometry. Runtime validates all required source floor/blocker IDs, tags, collision responses and bounds before entry. The 12 authored floor offsets require exact hidden source-mesh support proxies; the 38 captured closed blockers remain closed. Visible building geometry is unchanged.

Entry requires an actual downward source-floor hit, radius-valid CMC floor query and full-capsule overlap check at the current camera XY. Failure leaves orbit active with accessible feedback. CMC gravity, sliding and semantic floor/step checks drive movement; a bounded permitted drop clears lateral velocity before descent. The camera compensates Unreal's floor gap and measures its actual height against a floor hit. Native collision, passage, drop, step and keyboard traversal tests remain required.

`-BreziWalkAudit` performs current-view entry queries without entering walking; `-BreziWalk` attempts entry and records standing eye-height samples. Both enable the existing diagnostics report, adding a `walking` object with readiness, source IDs, query results, coordinates and measured eye-height errors. These flags alone do not perform traversal tests. Detailed implementation and acceptance notes are preserved in `output/unreal/walking-native-draft/README.md`; that draft was subsequently applied and compiled, so its original SHA application gate is intentionally no longer applicable.

## Rendering and native build

Mac Metal SM6; Lumen hardware tracing for the validated M5 Pro configuration; virtual shadow maps; Nanite enabled; native 100% render scale; dynamic resolution and motion blur disabled. Ray-tracing shader support and compute skin-cache shaders are enabled (`r.RayTracing=True`, `r.SkinCache.CompileShaders=1`), with `r.Lumen.HardwareRayTracing=True`. The root runtime QA compared this path with software Lumen successfully on this Mac before selecting the profile. A capability flag or a compiled permutation does not establish support on other Macs; verify the active path and frame evidence on each target. This profile does not imply smooth 4K performance. Temporal antialiasing does not reduce the configured input resolution.

Default window target is 3840×2160 with high-DPI support. This is a requested resolution, not evidence of a 4K render or fluid performance: the operating system may clamp the window to the attached display. Verify the actual backbuffer dimensions and captured frames. For benchmark launches specify `-ResX=3840 -ResY=2160 -ForceRes -windowed` and record viewport dimensions, RHI, frame times and device data.

```sh
"/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh" BreziTwinEditor Mac Development "$PWD/unreal/BreziTwin/BreziTwin.uproject" -WaitMutex
"/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun -project="$PWD/unreal/BreziTwin/BreziTwin.uproject" -noP4 -platform=Mac -clientconfig=Development -build -cook -stage -pak -package -archive -archivedirectory="$PWD/output/unreal"
```

Run those commands from the repository root after generating/importing the scene. Packaging requires that map and the data file exist. Local development builds are not notarized or distributed releases.

## Runtime measurement and screenshot capture

Launch a game runtime with these optional arguments:

```text
-ResX=3840 -ResY=2160 -ForceRes -windowed
-BreziView=street -BreziBenchmarkFrames=300 -BreziWarmupFrames=240
-BreziCapture4K -BreziExitAfterCapture
```

- At least 240 warmup and 240 measured frames are enforced. The benchmark runs with the requested preset; `-BreziNight` selects the provisional night lighting study.
- Runtime JSON and screenshots are written to the project's `Saved/Diagnostics` directory. It records actual game viewport and accessible RHI render target dimensions, RHI/adapter/shader platform, renderer cvars and separate p50/p95/p99 distributions for wall-clock frame intervals, active CPU game/render threads and available RHI GPU timer values. Unavailable timers are reported as unavailable. These independent counters can lag each other; frame interval is never labelled GPU time.
- `-BreziCapture4K` uses a regular scene screenshot without Slate UI when the viewport is already exactly 3840×2160, preserving the warmed Lumen/TSR view history. Other viewport sizes use a 3840×2160 high-resolution capture fallback. The report records the actual `screenshotKind`; the fallback does **not** prove a native 4K viewport or framebuffer.
- `focusDuringBenchmark` records foreground sample counts and transitions using `FPlatformApplicationMisc::IsThisApplicationForeground`, active game-window samples, and scene-viewport keyboard-focus samples. These counts share the accepted wall-clock frame samples. A focused Slate control can legitimately make scene-viewport keyboard focus false; foreground state does not measure visual occlusion.
- `-BreziProfileGPU` requests one native `ProfileGPU` capture halfway through warmup (frame 120 by default), temporarily sets `r.ProfileGPU.ShowUI=0`, and observes the asynchronous UE 5.8 `LogRHI` profile output. A per-run `-gpu-profile.log` is saved only from observed output, with status/header/activity/file evidence in `gpuProfile`. This does not start an Unreal Insights trace. Unavailable commands, incomplete output, timeouts and truncated artifacts are explicit. Delayed profile work remains excluded from benchmark frames; any extra warmup is counted, and an unresolved profile aborts measurement after 30 seconds. The previous profiler-UI setting is restored after capture. Native runtime validation remains required.
- Render settings include TSR history percentage, precision/update/async modes, Lumen gather/reflection settings, front-layer project/scalability gates and Slate blur controls. `finalViewPostProcessSettings` observes the composed main view after postprocess blending and records its effective front-layer reflection view gate, GI/reflection methods and ray-lighting override. Actual material/pass execution still needs render evidence. These are observed settings: this diagnostics option does not change the inherited TSR history scale or the native 100% scene render scale.
- `-BreziCaptureUI` instead captures the current native viewport with Slate UI. If both screenshot flags are supplied, the UI capture takes precedence and uses the actual current viewport dimensions.
- `-BreziExitAfterCapture` requests a graceful exit only after the screenshot capture callback has synchronously saved a nonempty PNG and the processed callback has written the report, or after a reported failure/timeout. With benchmark-only arguments it exits after saving the measurement report.
- Default launches do not run diagnostics. Capturing is opt-in, and image readback/writing occurs after benchmark sampling so capture overhead is excluded from frame statistics.

## Evidence and remaining work

Source scaffold created; build evidence is recorded below as it is produced. No photorealism, 4K performance, collision, final-material, visual QA, packaged-app or design-award claim follows from configuration alone. Source web materials imported through glTF require Unreal-specific optical and lighting refinement, especially water and translucent glass.

- 2026-09-08: `BreziTwinEditor Mac Development` compiled and linked successfully on the local Apple Silicon machine with UE 5.8.2, Xcode Clang 21 and macOS SDK 26.5. Final incremental build completed in 10.95 seconds. Engine-required build settings V7 are used. This verifies C++/Slate API compatibility; it does not verify the generated scene or packaged runtime.
- 2026-09-08: `BreziTwin Mac Development` including runtime diagnostics compiled and linked successfully, and Xcode produced an ad-hoc signed `Binaries/Mac/BreziTwin.app`; final build after metadata refinement took 20.30 seconds. `file` confirms an arm64 Mach-O executable, `codesign --verify --deep --strict` succeeds, and `plutil` confirms `NSHighResolutionCapable=true`, bundle identifier `local.brezi.twin` and graphics/design app category. Unreal explicitly reports that this binary still requires a valid cooked/staged content directory. The engine emits a nonfatal warning about its missing `metal_irconverter_ext` include directory. The project supplies an explicit high-resolution-capable macOS plist template because Unreal's generated default sets that flag to false.
- 2026-09-08: Game Development compile after the AppKit accessibility observer and rounded Slate interface succeeded in 22.77 seconds. This includes the Objective-C++ bridge and ray-tracing-support configuration, with software Lumen still the default. Native interaction, actual accessibility preference changes and visual results remain to be checked in the packaged application.
- 2026-09-08: AX semantics/bootstrap, accessible in-window controls panel, keyboard traversal, clean title and viewport-history capture/focus diagnostics added. The vegetation importer can serialize `/Script/BreziTwin.BreziVegetationPatch` using its default HISM component `Instances`; runtime creates no planting geometry. Builds were deferred until the concurrent benchmark finished.
- 2026-09-08: The AX/diagnostics/vegetation snapshot compiled and linked successfully for both Editor Development (8.59 s final incremental build) and Game Development (24.65 s). The only source correction was declaring `FReply` as a class, matching UE's header under `-Werror,-Wmismatched-tags`. UHT generated the vegetation class and its `Instances` property. The Game arm64 bundle passes `codesign --verify --deep --strict` and retains `NSHighResolutionCapable=true`. Logs: `output/unreal/editor-native-ax-build.log` and `output/unreal/game-native-ax-build.log`. No cook/package or runtime was performed in this build window; Xcode reused existing staged content, so the refreshed development bundle is not evidence of a newly cooked distributable. Native AX/focus/capture QA remains pending.

- 2026-09-08: Applied ACharacter/CMC walking, source collision contract validation, keyboard navigation and walking diagnostics compiled for Editor Mac Development. The AX pre-shutdown fix, bounded title retry and read-only final-view postprocess observer compiled as well. The only C++ correction was resolving `ACharacter::SetBase(nullptr)` explicitly to the UE 5.8 `FMovementBaseInterfaceData*` overload. Final incremental compile/link succeeded without warnings in 5.49 s; the editor module is arm64. Evidence: `output/unreal/editor-walking-build.log` and `editor-walking-build-receipt.json` with source/module SHA256. Game target, import/cook and runtime validation are delegated to the root pipeline and were not run in this agent build window.
