# Kitchen and dining photographed oak

The current import iteration exposed a repeat-import metadata defect. The first
failed map retained furniture ownership keys at live actor paths while its new
components had canonical source materials. An exact, separately pinned repair
removed those 18 keys and passed a real save/reload check without changing other
actor metadata or the 158 wood components/assets. A subsequent full import still
failed: `DOM_00613`, for example, moved from `brezi-twin_node_613` to the historical
path `brezi-twin_node_2945`, whose orphan metadata survived the earlier cleanup.
The [second native diagnostic](../output/unreal/furniture-reimport-failure-2/diagnostic.json)
and [preservation check](../output/unreal/furniture-reimport-failure-2/diagnostic-preservation.json)
record the actual paths and unchanged failed map/reports. The strict furniture
guard correctly stopped before activation. The importer now also initializes the
four exact oak keys on freshly created source actors, after validating the whole
source set, every material slot and exclusion of pre-existing actors. Unrelated
metadata and the strict active-override guard are preserved.

Two subsequent full native imports passed consecutively with 1,878 source objects,
successful TV/furniture/stove saved-map checks and clean process exits; see the
[repeat-import evidence](../output/unreal/furniture-reimport-fix-v2-draft/repeat-import-validation.json).
Both new-actor passes removed zero keys after the earlier exact repairs and
pre-deletion cleanup. They validate normal repeated import. A subsequent
[native API fixture](../output/unreal/oak-metadata-native-fixture/run-cb7685a9-9c07-42f3-861a-22371e999424-process.json)
exercised actual fresh-actor removal in an unsaved map: eight oak metadata entries
were removed from two new source actors, including a non-oak source, while the
manual control actor and unrelated metadata were preserved. Native PID 16329
exited 0 in 21.64 seconds; all 2,243 canonical Content files and source pins were
unchanged over the full process interval. This proves the real UObject removal
branch, not recreation of a historical orphan path.
The complete suite passed 338 Node tests and 33 persistent Python tests. These
results establish import behavior, not binary-deterministic assets or photographic
appearance; the rendered evidence below belongs to the earlier package.

The native importer adopted two photographed oak materials on exactly nine existing components on 8 September 2026. The [preserved native receipt](../output/unreal/furniture-detail-study/native-proof/furniture-oak-report.json) records `native-furniture-oak-saved-reload-validated`, two actual saved-map reloads and preservation of the other 149 wood components. The [preserved full import](../output/unreal/furniture-detail-study/native-proof/import-report.json), generated at `2026-09-08T07:48:04.836662+00:00`, is `import-validated` with clean process exit 0. Metal packaging and two actual 4K captures subsequently passed; static visual inspection confirms visible photographed grain. The import-only receipt retains `renderedVerified: false`; subsequent rendered evidence is separate and does not establish resident mips, correct normal response or photorealism.

| Exact components | Source role | Source material | Original X × Y × Z bounds, mm |
| --- | --- | --- | --- |
| `DOM_00613` | Rear kitchen base cabinets | `MAT_0039` | 2300 × 581 × 760 |
| `DOM_00643` | Integrated refrigerator cabinet | `MAT_0039` | 600 × 581 × 2250 |
| `DOM_00647` | Peninsula cabinet body | `MAT_0039` | 4150 × 580 × 760 |
| `DOM_00650` | East return base cabinets | `MAT_0039` | 600 × 994 × 760 |
| `DOM_01328` | Dining tabletop | `MAT_0080` | 1400 × 800 × 52 |
| `DOM_01345`, `DOM_01354`, `DOM_01363`, `DOM_01372` | SW, SE, NW, NE chair upper rails | `MAT_0080` | 440 × 52 × 65 each |

Dimensions above are rounded source bounds, not new geometry or product specifications. The [source study](../output/unreal/furniture-detail-study/candidate.json) and [reference validator](../scripts/unreal/furniture-oak/furniture_reference.py) pin exact records and all 108 source triangles. Canonical mesh positions, source UVs, collision, navigation and web textures remain unchanged. Upholstery, legs, posts, aprons and the oval coffee table are excluded. The existing [three TV cabinet overrides](unreal-tv-oak.md), including their ownership metadata, are preserved. Rounded edges remain deferred.

The recipe reuses the pinned CC0 OakVeneer01 diffuse, OpenGL normal and roughness photographs by Jenelle van Heerden from the [original photo study](../output/unreal/wood-study/candidate.json). Each map is 4096 × 4096; the measured square period is **183.00000429153442 cm**. The common [TV asset restoration helper](../scripts/unreal/tv-oak/fetch_assets.py) verifies and restores that photo cache. Source scene SHA-256 is `61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b`; OBJ SHA-256 is `a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455`. Individual source, texture, implementation and generated asset hashes are retained in the receipts.

The separate furniture recipe is now preserved as a [current canonical input revision](../scripts/unreal/furniture-oak/inputs/lawn-material-transfer-v2/candidate.json): exactly 69,631 bytes pinned to SHA-256 `c5270c1219c7f83a78eb16ee3d35958873182eee1ad92c7baeb83493ae92179a`. The original [input snapshot](../scripts/unreal/furniture-oak/inputs/candidate.json) and [study](../output/unreal/furniture-detail-study/candidate.json) remain byte-for-byte unchanged. This new revision changes only the shared material-writer SHA for canonical lawn texture transfer; furniture geometry, photographs and recipe values remain identical. Its cache lives in `output/unreal/furniture-detail-study/lawn-material-transfer-v2/`. A fresh native receipt is required after import; historical receipts describe their original recipe versions. From the repository root, restore both ignored input caches before the normal geometry export/import workflow:

```sh
python3 scripts/unreal/tv-oak/fetch_assets.py
python3 scripts/unreal/furniture-oak/restore_inputs.py
```

The [furniture helper](../scripts/unreal/furniture-oak/restore_inputs.py) validates the canonical snapshot before publication, atomically restores only a missing output recipe, verifies matching existing bytes and refuses conflicts or symlink inputs/targets. It performs no download or native import and leaves the recipe/graph unchanged. Its [13 filesystem tests](../scripts/unreal/furniture-oak/test_restore_inputs.py) cover temporary destinations, preserved existing inode/mtime, corrupted inputs, symlinks, concurrent publication and invocation from another working directory; all pass on host Python 3.9 and bundled Python 3.11.

`M_KitchenPhotoOak` runs grain vertically on upright faces, anchored at `(759.0999794, -233.3999910, 0)` native cm. `M_DiningPhotoOak` runs grain along X on broad faces, anchored at `(855, -448.0999924, 70.8000027)` cm. Both use a signed world projection and matching normal basis; source UV scale is not reused. Transverse veneer on end faces is an authored approximation. The OpenGL normal imports with green flipped and authored XY strength **0.25**.

The linear albedo multipliers are `(1.57810706, 1.84562674, 2.06278533)` for kitchen and `(1.42810324, 1.42040156, 1.33080248)` for dining, retaining their separate full-texture warm palette targets. Roughness is `sourceMean + 0.12 × (map − 0.5304041633418962)`, with means **0.55** and **0.68** respectively. These are appearance controls, not measured finish calibration; each visible crop can have a different mean.

The [furniture stage](../scripts/unreal/furniture-oak/furniture_oak.py) runs after TV oak and before final collision/hash snapshots. It reuses the TV writer's optional material profile and creates five owned packages—two materials and one shared texture triplet—under `/Game/Brezi/MaterialStudies/FurniturePhotoOak/V_98605b7ea8333e4f/`. Before activation it saves the new assets, saves/unloads/reloads the map and verifies original bindings, bytes and metadata. After assigning exactly nine slot-0 component overrides, a second saved-map reload verifies the intended bindings and preserved state. Both stages read back the complete 19-node graphs, shader bytes, scalar/vector values and texture settings. These are map reloads, not a claim of forced material-package unloading.

Original override arrays are retained in dedicated actor metadata. `restore_furniture_oak(scene, geometry_dir)` preflights all nine ownership records, restores those arrays and validates a saved/reloaded world. Failure after activation attempts restoration of the previous arrays and metadata; the receipt distinguishes required, attempted and verified rollback and records errors. Preactivation failure checks unchanged live state without claiming rollback. Source assets and previous generated versions are retained. This successful native import did not exercise rollback: its required/attempted/verified flags are all false.

The [package gate](../scripts/unreal/furniture-oak/package-gate.mjs) requires exact bindings, both native graph proofs, preservation flags and merged recipe/generated/preserved asset provenance. Adopted CPU checks passed: [254 Unreal tests](../output/unreal/furniture-detail-study/adopted-unreal-tests.log), [17 furniture tests](../output/unreal/furniture-detail-study/adopted-furniture-tests-2.log) and [17 TV tests](../output/unreal/furniture-detail-study/adopted-tv-tests.log). The [native import log](../output/unreal/furniture-native-import-1.log) is separate engine evidence.

The [Metal package log](../output/unreal/furniture-native-package-1.log) completed with exit 0 in 138.90 seconds. The [day standing capture](../output/unreal/runtime/walking-interior-standing-hwrt-53bf6a06-6019-448a-a2fd-60de6c30d2ab/capture.png) passed native standing, 300 measured frames and payload preservation. The [night orbit capture](../output/unreal/runtime/interior-night-hwrt-6374bb5e-98b8-42cb-9a91-c0ac7063b809/capture.png) passed presentation and drained accessibility shutdown with unchanged packaged bytes. Both are actual 3840 × 2160 renders, inspected at the tool's displayed 2048 × 1152. They use different camera modes, not a controlled pixel comparison.

The [separate visual review](../output/unreal/furniture-detail-study/native-proof/visual-review.json) pins both images and reports, plus preserved import/package receipts. Vertical grain is visible on the tall kitchen cabinet and peninsula; longitudinal grain is visible on the tabletop and upper chair rails. Night reveals the same grain in dim light. Strong grain contrast and square edges remain; the bright lamp bulb does not yet give convincing room illumination. Keep this material adoption for continued iteration, with close normal response, face seams, resident mips and moving-view quality still open.

Day frame interval was **66.43 ms mean / 72.69 ms P95**; night was **66.67 / 73.73 ms**, about 15 FPS. Both reports record **0/300 application-foreground and active-window samples**. These are background rendering observations; they do not establish interactive performance or isolate the material cost. A separate fully active-window run is required. The physical internal display is below UHD; 4K identifies the scene render target and captured image.
