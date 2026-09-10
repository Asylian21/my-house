# Native floor-light composite controls

9 September 2026. These preserved synthetic controls established the floor consumer at native 3840 × 2160. A subsequent [water-to-floor transport phase](/Users/davidzita/www/dom/docs/unreal-caustics-transport.md) connected and validated the twelve-wave producer and bounded opaque incoming visibility. Standalone delivery remains pending.

[Combined process, source and HDR evidence](/Users/davidzita/www/dom/output/unreal/caustics-active-study/reviews/current-controls-v4.json) records the matching Editor/provider binaries, 2,467 unchanged input pins, clean native exits and separate numerical validation. Source house geometry, imported materials, canonical project/package and fire effect were not changed in this phase.

| Control | Native PID | Run duration | Owned floor pixels | Numerical policy |
| --- | ---: | ---: | ---: | --- |
| inactive | 91283 | 49.79 s | 0 | legacy-ulp |
| zero | 89106 | 58.93 s | 571,635 | legacy-ulp |
| constant | 89666 | 52.41 s | 571,635 | toward-zero |

Inactive and zero have exactly unchanged before/after composite RGB, depth and alpha. Constant changes only the 571,635 floor pixels: all 1,714,905 owned RGB channels exactly equal the explicitly selected binary16 toward-zero model of the stored before-color plus stored contribution. All 7,722,765 off-mask pixels remain unchanged. All four HDR stages are finite and paired within each capture frame. The durations above are process durations, not FPS measurements.

## Corrected geometry eligibility

The original conservative intersection test accepted four empty world line batchers, whose bounds cover the entire world. This excluded all candidate floor pixels. The corrected [Renderer overlay](/Users/davidzita/www/dom/output/unreal/caustics-active-study/engine-exclusion-overlay-v4/manifest.json) inspects actual visible material mesh batches for non-Nanite proxies, keeps Nanite independent of potentially absent cached CPU relevance, and retains unknown ranges/material states conservatively. It has no class/name/size blacklist and does not trigger shader compilation from material lookup.

The [provider metadata overlay](/Users/davidzita/www/dom/output/unreal/caustics-active-study/plugin-overlay-v3/manifest.json) copies four actual game-thread line-batcher identities into the same-frame snapshot. The new native captures confirm IDs 2312–2315 are empty `LineBatchComponent` objects and none is an exclusion. Stair 2156 retains its previous bounds. The receipt does not identify why the other three previously considered stair bounds are absent from the new visible-mesh filter.

The preceding legacy rough-diffuse guard correction remains included: with Substrate disabled, the guard follows the active legacy rough-diffuse setting. No render-quality setting was reduced. The Editor/provider build completed cleanly in 150.27 seconds; the graph, API symbols and module mappings were reviewed before runtime.

## Explicit numerical model and preserved failure

The [original constant validation](/Users/davidzita/www/dom/output/unreal/caustics-active-study/reviews/constant-89666-original-validation-failure.json) failed its earlier half-ULP bound on 54,950 channels. It remains preserved, including the native failure receipt SHA256 `02827136ee075d34cdc767313d9fd4abdfd9889482a4bb1f05b820fd33a094e0`. Independent inspection then found exact toward-zero quantization for every owned RGB channel.

The separate [v2 validation](/Users/davidzita/www/dom/output/unreal/caustics-active-study/reviews/constant-89666-validation-v2.json) selects `--blend-rounding toward-zero` explicitly and requires exact binary16 output bits. The model was chosen after inspection of the original capture and before this offline revalidation. It uses no enlarged epsilon and does not infer the expected value from the measured output. Maximum error against that declared model is zero; maximum quantization against the ideal real-number sum is 0.000457763671875 in native pre-exposed linear units. Original renderer, capture, v1 validator and failed result stayed unchanged.

Apple's [MSL specification](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf), pp. 18 and 378, discusses texture-write rounding options and generic half conversion. It does not establish which fixed-function blending stage produced the observed rounding here. This evidence is an empirical stored-result model for the captured M5/Metal path, not a hardware-conformance claim.

The v2 validator passed 19 CPU test groups normally and with `-O`, including every finite binary16 pattern and adjacent interval, wrong-bit results, corrupted ownership and unchanged legacy checks. The scientific plotter passed 15 groups in both modes. [Fixed-curve before/after inspection](/Users/davidzita/www/dom/output/unreal/caustics-active-study/inspections/constant-89666/stages-1-2-rgb.png) and [numeric maps](/Users/davidzita/www/dom/output/unreal/caustics-active-study/inspections/constant-89666/composite-numeric-maps.png) were generated from verified native buffers and visually checked. The maps separate model residual from ideal-sum quantization.

## Scope and follow-up at the time of these controls

These are synthetic inactive/zero/constant controls. The four stages include the actual Single Layer Water result, but this phase does not independently prove the full refracted water path, a single Beer attenuation, effective GPU exposure uniforms or cross-run matched exposure/time. It provides no performance or photorealism acceptance.

The existing twelve-wave producer can supply normalized irradiance in the same RDG graph; it must not multiply sun magnitude or pre-exposure a second time. Whole-scene incoming sun visibility remains to be connected before physical lighting acceptance. The existing post-TLAS probe offers an opaque-scene path, with explicit limitations for culling, Nanite proxies, masked foliage and glass. A cooked app also needs a reviewed link from the saved water-material source binding to the cooked payload. The current loader's uncooked asset hash cannot simply be reused or removed for packaging.

The full project goal remains active, including native 4K smoothness and the final visual/UI quality. Further fire polishing is out of scope under the user's latest direction.
