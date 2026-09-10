# Water-to-floor transport: native Editor proof

9 September 2026. The isolated UE 5.8.2 working version now connects the saved twelve-wave water model to the pool-floor lighting consumer, using incoming sun visibility from the current opaque ray-tracing scene. Both native **3840 × 2160** runs passed independent transport and stored-color validation. This is an opt-in Editor-game implementation; the standalone packaged app has not received this feature.

[Paired native proof](/Users/davidzita/www/dom/output/unreal/caustics-transport-consumer/reviews/two-phase.json) · [Phase 0](/Users/davidzita/www/dom/output/unreal/caustics-transport-consumer/reviews/phase0.json) · [Phase 0.125](/Users/davidzita/www/dom/output/unreal/caustics-transport-consumer/reviews/phase0125.json) · [Accepted native build](/Users/davidzita/www/dom/output/unreal/caustics-transport-consumer/accepted-editor.json)

| Frozen material phase | Native PID | Process duration | Blocked aperture rays | Maximum atlas flux error |
| --- | ---: | ---: | ---: | ---: |
| 0 s | 61414 | 66.46 s | 1,935 | 0.1155% |
| 0.125 s | 65723 | 55.02 s | 1,935 | 0.1150% |

Each run used 117,760 aperture samples: 115,825 clear, 1,935 blocked, none incomplete. The blocked packets contribute zero power; normalization retains the original sample count. All six source-distance controls passed. This exercises the actual blocked-packet branch as well as the clear branch.

The live source binding verified 45 receiver objects and the water surface, their saved assets/materials, identity world transforms, visibility and native source triangle correspondence. The receiver BVH contains 1,076 triangles; the water mesh has 4,608. Maximum matching GPU/source hit-position error was under 1.81 micrometres. Listed float32 ambiguities retain their separate source identities; no unexplained receiver mismatches were accepted.

The shader's own View uniform readback confirmed phases **0 and 0.125 seconds** and paired pre-exposure values. There is no photon-only phase offset. The two normalized irradiance atlases differ in **234,481 RGB channels**. Both captures add their stored contribution only to **570,909 owned floor pixels**: all **1,712,727 owned RGB channels** exactly match the declared binary16 toward-zero model; all **7,723,491 off-mask pixels**, alpha and pre/post-composite depth remain unchanged. The rounding model and validator hashes were frozen before these captures. This empirical storage model does not identify a particular Metal hardware stage.

[Full-range atlas maps, PNG](/Users/davidzita/www/dom/output/unreal/caustics-transport-consumer/inspections/two-phase-full-range/atlas-phases.png) · [PDF](/Users/davidzita/www/dom/output/unreal/caustics-transport-consumer/inspections/two-phase-full-range/atlas-phases.pdf) · [Plot inputs and hashes](/Users/davidzita/www/dom/output/unreal/caustics-transport-consumer/inspections/two-phase-full-range/plot.json)

The scientific maps use shared linear ranges 0–8 and −8–8 for both phases and their signed difference, with zero out-of-range samples. These ranges were selected for inspection after validation; they are not part of the numerical acceptance rule. The plot and both native stills were visually inspected. The final water view remains dominated by building reflections; this is not a visual claim that the whole scene has reached photorealism.

[Native 4K still, phase 0](/Users/davidzita/www/dom/output/unreal/caustics-active-study/candidate/UE_5.8/.brezi-managed/active/transport/transport-opaque-0.0-8b5fec009cb44b53b40dbea5df6e03d1/user/Saved/Diagnostics/pool-day-20260909T084054-4k.png) · [Native 4K still, phase 0.125](/Users/davidzita/www/dom/output/unreal/caustics-active-study/candidate/UE_5.8/.brezi-managed/active/transport/transport-opaque-0.125-8ca4048eb0e44b988da989c36019223b/user/Saved/Diagnostics/pool-day-20260909T084334-4k.png)

## Build and preserved scope

[Plugin overlay](/Users/davidzita/www/dom/output/unreal/caustics-transport-consumer/plugin-overlay/manifest.json) contains four modified and six new files over the prior 32-file provider. [One-line compilation correction](/Users/davidzita/www/dom/output/unreal/caustics-transport-consumer/compile-fix01/manifest.json) adapts a failure-message string to UE 5.8's shared JSON key type. The initial failed build remains recorded; the corrected native build exited zero and drained in 180.91 seconds. Renderer API/source, canonical geometry/materials, 2D/Babylon sources and the fire effect were preserved.

[Validator](/Users/davidzita/www/dom/output/unreal/caustics-transport-consumer/validation/manifest.json): 28 CPU tests pass normally and with `-O`. Scene binding has four CPU groups, the plotter nine. Each native host pinned 2,572 inputs before and after execution, retained 100% native rendering, TSR history 200%, hardware Lumen, Nanite and virtual shadows, and enforced process cleanup. The diagnostic additionally sets ray-tracing culling to zero and freezes material time explicitly.

## Remaining work

Incoming visibility is scoped to the current view's forced-opaque triangle TLAS. Culling zero and the six sentinels do not establish complete scene coverage, masked foliage, glass transmission, procedural geometry or exact native-to-canonical caster identity. Refraction uses the saved normal waves at the mean surface plane; it does not model displaced wave geometry, a finite solar disk or multiple bounces. The four HDR stages include actual Single Layer Water output, while an independent full GBuffer/BRDF and outgoing attenuation proof remains open.

The standalone build needs a reviewed source-to-cooked-material/geometry binding; the Editor's uncooked asset hash and MeshDescription checks must not simply be removed or claimed to work in a package. Continuous motion still needs visual review. This diagnostic recorded mean frame intervals of 67.39 and 66.54 ms (about 15 FPS); it is not a foreground-clean performance acceptance and does not meet the smoothness goal. Native 4K performance, overall materials/light and final application UI remain active work. No further fire polishing is planned.
