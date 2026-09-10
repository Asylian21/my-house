# macOS application startup entry

The app-owned `BreziMain` entry is compiled into the original `BreziTwin` executable. Native compilation, sealed packaging and actual Unreal rendering passed on 8 September 2026. In `output/unreal/runtime/interior-day-hwrt-c0ce27be-c134-499b-845f-4c33cd3ea566/`, PID 74164 performed one same-PID self-exec, initialized Metal and AX, rendered 300 samples at native 3840 × 2160, and exited 0 with every packaged payload unchanged. Mean frame time was 54.391 ms and p95 was 59.542 ms; this does not meet a 60 FPS target.

Only the Mac Game target selects `-Wl,-e,_BreziMain`. The entry validates policy arguments, then self-executes the same executable once with canonical `-LLM` and `-DetectHitchesWithLLM` flags when needed. The second entry calls the unchanged engine `main`. This refreshes the real OS arguments before Foundation caches `NSProcessInfo.arguments`; it does not mutate the CRT, use a private API or add a helper process. The PID, original GUI bundle executable, Info.plist and original entitlement dictionary remain in place. Contradictory or valued policy flags are rejected. The Editor target does not select this entry.

The installed engine source is unchanged. UBT marks extra linker arguments as shared-environment-sensitive, so the Mac Game target sets `bOverrideBuildEnvironment` for this app's final link only; it does not add engine compiler definitions or request an engine rebuild. The actual binary contains distinct `_BreziMain` and original local `_main` symbols, and `LC_MAIN` resolves to `_BreziMain` inside the executable text section.

The motivation is the recorded [early startup crash](../output/unreal/manual-ui-20260908-v4/native-crash.ips): the main thread was returning from an LLM allocation scope while the game thread cleared LLM tracker state during command-line initialization. In the inspected UE 5.8.2 code, `-LLM` avoids that startup clear branch. `-DetectHitchesWithLLM` preserves the stock hitch heartbeat that enabling LLM would otherwise disable. This is a specific mechanism change, not proof that all startup races are eliminated.

## Observed A/B evidence

The [immutable revalidation](../output/unreal/llm-startup-study/revalidations/cd8b93ac-bbe8-41cf-aa89-7f165c2f241c/report.json) covers five alternating default trials and five LLM trials on the same original package. Both arms supplied `-DetectHitchesWithLLM`; only the LLM arm added `-LLM`. Each process completed 240 warmup frames and 240 measured frames at a native 3840 × 2160 scene target and 100% rendering, with all samples in the foreground.

All ten processes exited cleanly. The original race was not reproduced in either arm. The early Apple Event requests returned `-600`; later Launch Services activation of the observed PID succeeded, which does not prove delivery of that earlier event. Fresh processes do not imply cold shader, driver, disk or OS caches.

| Mean of five per-run means | Default | LLM | Observed difference |
| --- | ---: | ---: | ---: |
| Game-thread time | 0.848 ms | 1.160 ms | +0.312 ms |
| Frame time | 59.336 ms | 60.268 ms | +0.931 ms |
| GPU time | 58.967 ms | 59.894 ms | +0.926 ms |

The game-thread increase was present in all five pairs. The frame/GPU variation does not isolate LLM overhead from scheduling, thermal or cache drift. No memory-overhead measurement was captured. These results are neither a zero-crash-rate estimate nor a smoothness/FPS acceptance claim.

The initial host report rejected the LLM trials because it inspected stdout only. Every hashed saved engine log contained the strict positive LLM message. Revalidation checked log hashes, exact command line, unique process identity, native report identity and original artifact preservation. It wrote a new report; the original failed reports remain unchanged.

## Native AppKit evidence

The [12-case fixture](../output/unreal/startup-entry-fixtures/ab10da53-f271-45a3-a94e-99638dc2c474/receipt.json) checks the role that the first libc fixture missed. The original signed sandboxed GUI main initializes `NSApplication.sharedApplication`. The former helper architecture reproduces SIGABRT at that call. All five valid same-binary entry variants preserve the parent PID and accepted arguments, expose both canonical flags through actual `NSProcessInfo.arguments`, retain the bundle identifier and original entitlements, and initialize AppKit. Five conflicting variants are rejected before AppKit. No Unreal code, window or renderer was executed by this fixture.

## Sealing and packaged acceptance

Packaging must start from a fresh UAT archive with `CFBundleExecutable=BreziTwin`. A sealed schema-2 policy pins the linked entry, executable code-section hash, entry source hash and required flags. The full executable hash belongs to the external package receipt: placing that final hash inside its own signed resource would create a circular dependency. The entry checker requires a distinct original `_main` and an `LC_MAIN` offset resolving to `_BreziMain`, including when the original symbol is local.

The policy is added before one final code-signing pass with the original entitlement dictionary. Deep/strict signature verification, unchanged Info.plist, original full GUI sandbox and every unrelated bundle payload file are required. The thin-arm64 signature checker permits only the signing blob and exactly classified signature-size metadata to change during this final sealing step. This is separate from the intentional earlier compilation of the app-owned entry. Local ad-hoc signing does not establish notarization or distribution readiness.

Runtime helpers resolve the original executable and sealed policy, pin the complete payload, and require the parent PID to match the entry and optional single self-exec marker before engine initialization and clean exit. Native-report PID checks remain independent. The actual packaged run above passed the UserDir, assets, Metal, 4K and AX lifecycle checks. Fixture success alone is insufficient.

Before a later UAT build, the packaging helper atomically preserves any previous archive under `output/unreal/package-history/before-build-<uuid>/`, including the old receipt bytes and their hash. The new UAT archive starts empty so stale sealed resources cannot survive a rebuild. The diagnostic package in `output/unreal/flame-failure-observation-package-2.log` passed this path, compilation, Metal cook and full payload sealing.

## LaunchServices and manual window observation

`output/unreal/runtime/launch-services-interior-dc7f51dd-03f7-4fa7-9417-08bfb731bac5/` records a launch through `/usr/bin/open -n -W` with the exact signed application URL. Neither LLM flag was supplied by the host. Kernel argv readback subsequently contained both entry-inserted flags. The observer bound PID 93779 using its executable path, uid and birth timestamp; the 300-sample native 4K capture completed before manual UI input.

CUA attached to that existing application. The F1 panel opened, Tab moved through panel controls, Escape closed the panel, the pool preset reached its final camera view, and N produced a visibly different night state. Some immediate AX observations preceded the asynchronous camera or focus update. This run does not establish every focus transition, reverse Tab, physical keyboard input or VoiceOver speech. The on-screen window was 800 × 450 points on the internal Retina display; the separate rendered scene target was 3840 × 2160.

After CUA sent Cmd+Q, the kernel `EVFILT_PROC/NOTE_EXITSTATUS` event recorded wait status 0, normal exit code 0 for PID 93779; `open -W` independently exited 0. No timeout cleanup or forced signal occurred. AX shutdown drained and all 37 bundle-file hashes were unchanged. The first host report incorrectly failed its strict boolean check because Objective-C boxed `WIFEXITED` as numeric `1`.

The [immutable revalidation](../output/unreal/launch-services-observer/revalidations/cff46636-2192-4d27-a0dc-b436335ac484/report.json) passed while preserving all 13 original files, including the failed report. It derives normal exit only from the original raw zero kernel wait status, the same pinned PID and matching exit-event objects. The native key trace independently confirms the forward panel Tab ring `0 → 1 → 2 → 0`; it does not prove reverse Tab. The repaired helper explicitly boxes a BOOL and passed native compilation and 52 pure tests, but this was revalidation of the existing run, not another application launch. This is a LaunchServices observation, not a literal Finder mouse-click test or proof that every possible startup race is resolved.

The corrected observer subsequently executed against the UI spacing package:
`output/unreal/runtime/launch-services-interior-126ba0f9-9362-46d2-8d90-4d39b806d93d/`.
PID 7861 passed the complete LaunchServices lifecycle directly, with no host
revalidation: native 4K readiness, one same-PID self-exec, kernel exit 0 after
Cmd+Q, separate `open` exit 0, drained AX and unchanged package payload. The
[manual UI review](../output/unreal/runtime/launch-services-interior-126ba0f9-9362-46d2-8d90-4d39b806d93d/manual-ui-review.json)
covers settled 800- and 600-point windows, the compact dock, a visible walking
failure message, Enter dismissal and focus restoration. It retains the CUA
and physical-display limitations separately.

## Retained failed helper attempt

The previous `BreziStartupLauncher` architecture completed native compilation, Metal cook and deep/strict signing, and its eight libc stand-in cases passed. Its first actual Unreal run nevertheless failed before engine initialization. Evidence is retained in `output/unreal/runtime/interior-day-hwrt-963c4919-c179-4d65-adbf-30f086001fd2/`: parent/launcher/engine PID 65614 matched, then SIGABRT occurred after approximately 2.6 seconds. The crash and unified log show that the inherited helper sandbox denied lookup of `com.apple.coreservices.launchservicesd`, so AppKit could not obtain an application serial number. There is no rendered image from that attempt.

The failed application is preserved at `output/unreal/package-history/helper-startup-failed-20260908/BreziTwin.app`, with all 38 payload hashes verified against its original receipt. The earlier working oak application is independently preserved under `output/unreal/package-history/tv-oak-before-launcher-20260908/`. Neither historical receipt is rewritten by the replacement entry work.
