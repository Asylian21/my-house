# Three-cabinet photographed oak

The native import now includes the candidate material for exactly `DOM_01293`, `DOM_01296`, and `DOM_01300`, the three planar TV cabinet bodies on `MAT_0078`. The oval coffee table `DOM_01326` sharing that source material is excluded. The six interior wood slots contain 158 total canonical objects: three selected and 155 preserved.

Status: native import, two saved-map reloads, Metal cook and actual packaged day/night 4K rendering passed on 8 September 2026. The three selected cabinets show the photographed grain. Close-detail inspection, lighting-direction checks, resident-mip evidence and motion acceptance remain pending; this is not a photorealism claim.

## Inputs and appearance

The unchanged Poly Haven [Oak Veneer 01](https://polyhaven.com/a/oak_veneer_01) 4K diffuse, OpenGL normal and roughness photographs are an illustrative CC0 material by Jenelle van Heerden, not a calibrated representation of the selected installed product. Source files, metadata, hashes and study measurements live in `output/unreal/wood-study/`. `scripts/unreal/tv-oak/oak_reference.py` pins the source scene/OBJ, exact object/material records, all 36 selected source triangles, photograph SHA-256/MD5 and 4096 × 4096 JPEG dimensions. The native import runs these source guards before replacing the map.

Restore this cache on another checkout before import with `python3 scripts/unreal/tv-oak/fetch_assets.py`. The three small historical recipe/measurement snapshots are preserved byte-for-byte in `scripts/unreal/tv-oak/inputs/`; their original study status describes when they were authored, not current native acceptance. The helper verifies all existing inputs before writing, downloads missing maps from their pinned HTTPS Poly Haven URLs, checks size/SHA-256/source MD5/JPEG dimensions and publishes each complete file atomically without overwriting different data. It does not alter the native assets. A fresh download of all three maps passed on this Mac in `output/unreal/tv-oak-fetch-check-20260908.json`; existing-file and conflicting-publication refusal checks also passed.

The material uses a world projection with a measured **183.00000429153442 cm** period and a common anchor derived from source bounds. Image V runs down world Z on vertical faces; the photographed grain is vertical on cabinet fronts. Top/bottom grain runs along cabinet depth X. Face seams are an authored veneer construction approximation. Every face must remain flat and aligned with the source axes; curved or smoothed replacements fail validation. Source geometry, collision, UVs and web textures are unchanged.

`oak-basis.hlsl` supplies the same signed basis to UV and normal expressions: `T × V = N`, where T follows image U and V image-down V. The OpenGL normal is imported with its green channel flipped, decoded with Unreal's Normal sampler, then transformed through the explicit world T/V/N basis. `tangent_space_normal` is false. Normal XY strength **0.25** is an authored appearance control. CPU tests establish mapping direction and handedness; cooked lighting direction still needs native visual verification.

Diffuse is sampled as sRGB and multiplied in linear light by `(1.4281032377635254, 1.4204015551734712, 1.3308024765112707)`. Saturation bounds albedo; five red texels out of 16,777,216 exceed 1, changing the global linear red mean by `1.99238e-8`. Green/blue global means are unchanged. A cabinet crops a different region and need not have the full-texture mean.

Roughness is `0.74 + 0.12 × (mapR − 0.5304041633418962)`, yielding `0.6763515004–0.7963515004` without clamp bias and preserving the authored full-texture mean of 0.74. Metallic 0 and specular 0.5 remain explicit. Palette, roughness and normal strength are appearance choices, not vendor calibration.

## Native integration and reversal

`scripts/unreal/import_scene.py` calls `apply_tv_oak(scene, geometry_dir)` after the stove stage and before the final saved-world collision and asset snapshots. It merges the returned `pipelineFiles` into import provenance and `assetHashes` into `finalAssetHashes`, so the final native-authored-state receipt covers the material, photographs, measurements and implementation.

New textures/material use a versioned owned namespace under `/Game/Brezi/MaterialStudies/TVPhotoOak/`. Existing shared materials and meshes are never edited. The module snapshots all 158 source wood actors, their geometry/material asset bytes and binding/transform/UV-count/collision settings. It saves the new assets and saves/unloads/reloads the map before activation, proving original state survived. Only then does it assign three component material overrides. A second save/unload/reload verifies all 155 other bindings, the selected bodies' unchanged geometry/collision/UVs, original asset bytes and native material/texture getters.

Native graph proof covers 19 nodes, input sources/output channels, exact shader bytes, physical period and authored constants, normal sampling, sRGB/compression/green conversion, wrap/mip settings, Nanite usage and absent WPO/opacity/emission. Texture dimension getters prove source dimensions, not resident mips. The receipt is `output/unreal/tv-oak-report.json`; success is reported only after the stage executes and its saved reload checks pass.

Prior override arrays are retained as metadata on the three owned actors. `restore_tv_oak(scene, geometry_dir)` reverses only those three overrides and verifies the saved/reloaded world. Apply and reversal restore the previous state on failure where possible and explicitly record rollback failures. No source assets or previous candidate versions are deleted. Re-running the full importer regenerates the source actors before applying the candidate again.

The first native attempt stopped while connecting the graph, before component activation: the texture input is exposed by `MaterialEditingLibrary` as `UVs`, although `TextureSample::GetInputName` internally calls it `Coordinates`. Both native connection and getter APIs apply `MaterialGraphNode::GetShortenPinName`. The corrected graph uses `UVs` and preflights every reflected input/output before connecting. Multiply retains A/B, Custom retains authored names, Saturate uses its first unnamed input, and texture outputs explicitly expose RGB/R. The new failure receipt distinguishes `activationStarted`, `rollbackRequired`, `rollbackAttempted`, `rollbackVerified` and live source-state verification before activation; retained generated asset paths are reported. An empty rollback error list alone is not evidence of a performed rollback.

Packaging calls the pure `scripts/unreal/tv-oak/package-gate.mjs` gate before cooking. It requires the successful native saved-reload status, exactly three unique bindings matched to canonical source IDs and `MAT_0078`, both graph/texture proofs, preservation flags and all recipe/new/preserved asset hashes merged into final import provenance. The gate itself is pinned in package native source inputs. Failed or missing oak stages cannot be packaged.

## CPU validation

```sh
python3 scripts/unreal/tv-oak/test_oak.py
node --test scripts/unreal/tv-oak/package-gate.test.mjs
python3 -m py_compile scripts/unreal/tv-oak/oak_reference.py scripts/unreal/tv-oak/tv_oak.py scripts/unreal/import_scene.py
```

The 17 Python CPU gates cover source identity and drift rejection, exact three-body scope and oval exclusion, all source edges' physical scale, six-face handedness, flat normals and signed red/green normal directions, normal strength, roughness centering, warm palette preservation and the observed native UV pin regression. The 24 JavaScript package-gate tests cover a synthetic accepted receipt and rejected missing/failed/ambiguous/stale proofs. They do not mock or execute native material graphs or produce native success evidence.

## Native and packaged evidence, 8 September 2026

`output/unreal/tv-oak-native-import-2.log` completed with exit 0. The resulting `tv-oak-report.json` records `native-tv-oak-saved-reload-validated`: three selected bindings, 155 preserved wood objects, all 19 native graph nodes, texture getters and both actual map reloads. The final import receipt is `import-validated` and covers 2,121 assets. The first failed attempt remains separately preserved in `output/unreal/tv-oak-import-attempt-1/`.

`output/unreal/tv-oak-native-package-1.log` completed the standalone Metal cook/package with exit 0. Native standing QA then passed in `output/unreal/runtime/walking-interior-standing-hwrt-8e3850b3-9940-4ac2-afe8-2b476c619e2e/`; the night run passed in `output/unreal/runtime/interior-night-hwrt-2ec8a012-1a84-4fba-b922-faf5e72c79fb/`. Both completed cleanly and produced actual 3840 × 2160 scene captures from the packaged application. Their package receipts preserve the tested payload identity.

Both images were visually inspected. Vertical wood grain is visible on the TV cabinet fronts in daylight and beside the light frame at night. Other kitchen wood retains its prior material. These are two different authored views/lighting states, not a controlled pixel comparison. This establishes visible rendering of the new material, but does not establish full-resolution mip residency, correct response to a moving light, final grain scale at close range or temporal quality. Those checks remain open. The internal Mac display is smaller than UHD; 4K here identifies the scene render target and captured image, not the physical display.
