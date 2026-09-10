# Continuous caustics delivery to the macOS app

The native provider now uses the water material’s live game time. The ordinary application enables it through `DefaultGame.ini`; diagnostic GPU readbacks remain opt-in. Cook commandlets only register the shader directory. Packaged execution validates the cooked content on a worker before activating the provider.

The subsequent user-authorized TSR scaling comparison is in [unreal-upscaling.md](unreal-upscaling.md): 4K output is retained, with 24.29 FPS at 67% and 34.22 FPS at 50% in the pool view. The earlier native100 measurements below remain historical evidence.

## Current evidence

The source closure is `output/unreal/caustics-delivery/source-closure-v3.json`. The matching Editor build completed with exit 0. Game compilation and linking completed, but the original UBT parent exited 6 during Xcode finalization. That failure is preserved. The same linked Game subsequently completed the actual Xcode, version and metadata actions with exit 0; `accepted-game.json` records this composite result without relabeling the failed UBT parent.

The Game build uses runtime `HasValidNaniteData()` where `IsNaniteEnabled()` is available only in Editor builds. Its provider functions are defined local text symbols in the monolithic binary, so inspection uses plain `nm`, not the global-only symbol filter.

Fresh cook02 completed in 55.45 seconds with exit 0. Archive02 completed in 35.00 seconds, with both nested Xcode actions successful. The final signed app contains 45 files (1,540,722,127 bytes); its package report is `output/unreal/caustics-delivery/reviews/package.json` (SHA256 `73b9d1d887f1bda6b3991c27773deac7df5d1c00335952ff00a70ccabd686a6f`). Full payload and strict deep signing checks passed.

Archive01 was explicitly rejected because Unreal AutomationTool returned 0 despite nested Xcode failures. The corrected runner checks those failures independently. The successful archive ran standard local UAT/Xcode. The generated pre-package project `.app` is preserved separately as immutable build history; raw linked Game and source inputs remained unchanged.

The packaged application completed a fresh corrected motion run as PID 79308 with native exit 0, all 64 original 3840×2160 images, advancing GPU time and a changing caustic atlas under the stationary pool camera. All GPU transport gates and invalid/overflow counters remained zero. Every stationary pool frame had positive receiver coverage. The result is `output/unreal/caustics-delivery/motion-qa-v2/runs/continuous-motion-5e7ec72d-2f92-4fa0-b05b-bc890d741775/validation.json`.

The initial PID 68074 capture and its validator rejection remain preserved: requiring visible pool-floor pixels in the distant terrace view was an incorrect test condition. The corrected condition was frozen before the fresh run and keeps all GPU error checks strict.

Four ordinary day views subsequently passed all 300 foreground samples, unchanged full payload, native 3840×2160 scene/RHI targets and 100% render percentages. The provider performed no GPU diagnostic readbacks; each screenshot was captured after timing. Each run used 600 warmup frames and the packaged Lumen HWRT, Nanite, VSM and TSR history200 settings.

| View | Mean frame time | Observed throughput | P95 frame time |
| --- | ---: | ---: | ---: |
| Pool | 65.917 ms | 15.17 FPS | 67.353 ms |
| Terrace | 53.206 ms | 18.79 FPS | 53.985 ms |
| Living room | 56.052 ms | 17.84 FPS | 56.786 ms |
| Street | 49.636 ms | 20.15 FPS | 50.559 ms |

The complete per-run records and original image paths are in `output/unreal/caustics-delivery/ordinary-summary.json`. These are instrumented wall-clock throughput observations including waits/VSync, not presentation-event measurements. The night image was captured, but its timing was rejected after loss of foreground state. Earlier rejected focus runs remain preserved. Smooth performance and final photorealism are still unmet.

A separate real GPU profile (PID13984) recorded 780 graphics events and a 63.987ms frame. Its later foreground timing failed, so the run remains failed. The saved table is useful for investigation only: Metal shares encoder time across event labels, so the 15.482ms attributed to `TSR ClearPrevTextures` is not the isolated cost of that clear shader. Existing split-encoder and TSR100 studies are documented in `unreal-performance-current.md` and `unreal-runtime-qa.md`; repeat experiments need a new concrete change or hypothesis.

## Packaging boundary

The cook starts from an explicit source snapshot. The cooked binding joins the previously measured Editor geometry and water data to the real cook, UAT response files and an actual UnrealPak IoStore listing. Runtime checks stream the physical container bytes off the game thread. This establishes content lineage and live scene compatibility; it does not claim that a packaged Game repeated the Editor-only triangle extraction.

`sealStartupEntry` accepts optional, hash-bound JSON resources. It checks the original archived signature first, installs declared resources and then signs the complete final bundle. This is how the detached cooked binding enters the app without modifying content after signing. Existing callers keep their prior behavior. The relevant package, startup-entry and resource tests passed (29 tests).

## Remaining work

- Improve performance from the measured 15–20 FPS range while preserving native 4K.
- Finish automatic phase orchestration and package-report integration. The reviewed plugin, configurations, engine overlay and phased helpers have been promoted into maintained source. The legacy continuous build/package path now fails before native execution because it cannot produce the required cooked binding; explicit phased commands are documented in `scripts/unreal/caustics/README.md`. This guard is not a completed one-command build workflow.
- Continue the visible material and UI improvements. Fire polishing is explicitly out of scope for this iteration.

The earlier two-phase Editor measurements remain documented in [unreal-caustics-transport.md](unreal-caustics-transport.md). They are historical numerical evidence, not performance measurements of the new packaged application.
