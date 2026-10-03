# Original licensed English Oak USD pilot

This separate trial preserves the accepted Fab/NoAI original content. It does not generate replacement tree images/textures, train a model, replace the saved Březí scene, or promote a quality result.

The original archive contains five binary USDC layers and four DynamicWind JSON sidecars. Safe exclusive extraction preserved all nine files byte for byte. Standalone UE-bundled Python 3.11/OpenUSD 26.3 parsed the composed stages without starting Unreal. All trees are Y-up, metres, with a skeletal Nanite assembly root, the original bound skeleton and a PointInstancer referring to shared foliage parts. No defaultPrim or external image asset is authored. The only external layer dependency is the included `Tree_English_Oak_01_Foliage.usd`.

| Whole variant | Base source fan triangles | Unique referenced prototype source fan triangles | Assembly instances | Base plus expanded source fan estimate | Source height |
|---|---:|---:|---:|---:|---:|
| A | 965,969 | 222,854 | 345 | 14,220,792 | 17.664 m |
| B | 617,654 | 242,851 | 681 | 21,604,470 | 14.888 m |
| C | 897,184 | 242,943 | 505 | 16,607,056 | 13.227 m |
| D | 1,035,730 | 108,253 | 188 | 3,680,767 | 8.498 m |

These are source polygon fan estimates. Unique build inputs, expanded assembly costs, Nanite built resources, fallback meshes and actual rendered work are distinct. D is selected for this one bounded trial because its expanded source estimate is lowest. No source simplification, flattening, altered index order, texture substitution or crown scale is permitted.

The two original `UsdPreviewSurface` shaders contain only the authored linear diffuse constants: bark `[.142,.066,.031]`, foliage `[.087,.153,.021]`. There are no photographic textures, authored normal inputs or authored opacity inputs in this USD download. Geometric leaf outlines may still be meaningful. This is sufficient for an honest original-shape trial; it cannot establish photographic material fidelity. The DynamicWind sidecars are retained, but USDImporter does not establish automatic sidecar attachment. This trial does not claim wind evaluation.

The installed UE 5.8 Mac USD importer explicitly processes `NaniteAssemblyRootAPI` after base assets are imported. The forced `UsdStageAssetImportFactory` and `UsdStageImportOptions` preserve that route. Automated import explicitly disables actor import and external asset-cache reuse. Point-instancer collapsing is disabled within the own import process. Materials translate the original universal preview shaders. The helper verifies their original diffuse colors and zero authored texture parameters. It observes Nanite enablement and actual part references, while unavailable full-node/full-corner/N-T/GPU attribution remain false.

Root prepared an independent exact 4,218-file saved R32 clone. A CPU stager appends only the Editor `USDImporter` plugin to its descriptor. The native helper imports into `/Game/Brezi/EnglishOakPilot20261002R1`, creates a separate empty `Maps/EnglishOakPilot` world, duplicates only original native day sun/sky/atmosphere/cloud/fog/PostProcess actors, and compares observed daylight properties before and after serialization. It adds one whole D at native origin with unit scale and a 45×45 m neutral ground plane at Z=−2 cm. The source camera is eye `[2000,-2800,700]`, target `[0,0,650]`, horizontal FOV 58°. Source-bound fit is recorded; native visibility awaits rendering.

The original main map and every original project file remain byte exact except the declared own descriptor addition and one Data-only camera append. New packages must stay inside the own namespace. Main C/B/B, 3,000 mm setbacks, geometry, source roots, light actors and selectors remain protected. Root alone stages/launches native or GPU. Native saved results, rendering, appearance, performance, Shipping and package acceptance remain pending.
