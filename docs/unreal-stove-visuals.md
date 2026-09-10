# Native stove visual revision

Current priority, 8 September 2026: the user accepted leaving the current fire
effect for now. Further flame polishing and the output-only sparse-volume probe
are paused. Continue overall interior lighting, house materials, native 4K
performance and application controls; photorealistic fire is not a blocker for
that work. The observations below remain evidence of the current effect.

`scripts/unreal/stove-visuals/generate.py` builds an explicitly illustrative,
native-only derivative of the source stove. It reads and hashes `scene.json`
and `dom-mm.obj`; it never rewrites either file or changes the web/2D model.

Run the CPU-only generator and focused tests:

```sh
python3 scripts/unreal/stove-visuals/generate.py
python3 scripts/unreal/stove-visuals/test_stove_visuals.py
```

The generated `output/unreal/stove-visuals/stove-visuals.json` binds the GLB,
generator, exact eight source records and canonical source SHA values. Seven
proxies may change visibility: body DOM_00522, glow DOM_00525, logs
DOM_00531–00532 and flames DOM_00533–00535. Glass DOM_00526 is guarded and
retained. Pedestal, cap, trims, jambs, handle and flue remain unchanged.

The derivative keeps the source's actual 64-sided, 510 mm diameter exterior
polygon and elevations 30–1550 mm. A real opening follows the source 118° glass
sector at 430–1030 mm. Inward reveals meet a dark 245 mm radius firebox lining
at elevations 440–1020 mm. This is an authored chamber interpretation, not a
measured stove manufacturer's construction detail. The original body remains
the unchanged query collision authority, with its render, shadow and RT
contributions hidden after successful native validation.

Four derivative meshes contain 1,772 triangles: shell/reveals 752, chamber
336, irregular logs 672 and six crossed flame cards 12. All actual vertices,
including a decoded float32 GLB roundtrip, are checked against the exterior
envelope. Logs and cards must remain inside the smaller chamber and behind
the curved glass. The generator also rejects opaque triangles closing the
opening. Its source guards check exact IDs, names, revision, material slots,
triangle counts, query collision metadata, body dimensions, glass radius,
glass angular endpoints and source OBJ/manifest bounds.

Flames animate their opacity/emission through `flame.hlsl` and the material
Time node. No vertex displacement, physical combustion, calibrated lumens,
point light, smoke simulation or physical fire irradiance is claimed. Char
uses a separate rough, nonmetallic material with subdued emissive cracks;
logs no longer share the flame/glow material. Appearance, translucency sorting,
temporal stability and GPU cost require actual packaged Metal still/motion QA.

## Import integration

The new editor module starts no engine. Call it after the importer's existing
saved-map reload and canonical collision verification, before final map and
asset hashes:

```python
from stove_visuals import apply_stove_visuals
REPORT["stoveVisuals"] = apply_stove_visuals(scene, GEOMETRY)
REPORT["pipelineFiles"].update(REPORT["stoveVisuals"]["pipelineFiles"])
```

Include `REPORT["stoveVisuals"]` in the final asset-hash stage aggregation and
require its status `stove-visuals-saved-reloaded-validated` when the option is
enabled. The generator must be run before import. The read-only editor
`BreziCollisionAudit.ReadLod0Triangles` must permit the narrowly owned
`/Game/Brezi/VisualDetails/Stove/` namespace; the module fails closed without
complete native triangle readback. No extra UE plugin is required.

The module creates content under a SHA-bound revision namespace and separate
owned actors with `BreziVisualOf` metadata. New primitives have `NoCollision`,
no navigation data, no canonical DOM/source collision tags and no floor tags.
Canonical actors, components, static meshes, transforms, material packages and
collision profiles/responses are captured and compared across both reloads.

First, all new actors remain hidden while the map is saved, unloaded through
a blank map and reopened. Native LOD0 triangles, vertex containment, UVs,
materials and canonical invariants must pass. Only then are the seven source
proxies hidden and the four derivative actors activated. A second real
save/unload/reload repeats validation against the active state. Previous owned
layers remain hidden for reversible rollback. A failure restores prior source
flags/metadata, removes only actors from the current transaction, restores
previous layer visibility and writes an explicit failure receipt including
any rollback error.

`restore_stove_source_visibility()` is the explicit editor-only reversal. It
restores the saved original component flags and removes only owned stove
visual actors. It retains generated asset files and never alters canonical
geometry or query collision. After reversal the parent import/package receipt
must be regenerated before packaging; old success receipts are not current.

CPU tests and a valid GLB prove input scope and geometry checks. Native
save/reload, clean commandlet exit, successful cook, actual 4K appearance and
motion remain separate acceptance gates.

## Native import evidence, 8 September 2026

`output/unreal/stove-native-import-3.log` completed with process exit 0 and an
`import-validated` receipt. The stove stage passed both actual map reloads:
four native meshes, 1,772 LOD0 triangles, maximum vertex discrepancy
0.000053445 cm (0.00053445 mm). All four new primitives retained NoCollision
and disabled navigation. The seven original proxies were hidden, no canonical
objects were deleted, and the original glass and collision authority were
unchanged. The 57 auxiliary source blockers passed a further post-stove check.

This followed two preserved failures: a Python 3.9/3.11 binary64 derived-summary
rounding difference, then a ComponentMask pin name rejected by the native
material API. Derived summaries now allow only 1e-10 mm absolute error; physical
containment thresholds remain unchanged. The native mask input is `None`,
connected through the API's empty input name. A separate NullRHI smoke authored
and inspected all four graphs twice with exit 0, no errors/warnings and an
unchanged map SHA. Evidence lives in `output/unreal/stove-material-smoke/`.

The first import receipt correctly records `renderedVerified: false` and
`packagedVerified: false`. Metal cook, appearance and animated flame acceptance
require the subsequent standalone application build.

## Thin glass and additive flame study, 8 September 2026

The retained architectural and stove glass now use the guarded thin-surface
optics revision in `optics.py`: no screen-space refraction offset, with the
authored tint, roughness and IOR-derived Fresnel reflectance retained. This
avoids treating the zero-thickness stove pane or an architectural glazing
assembly as an unbounded optical medium. It is not a measured multi-pane model.

The flame material changed only from Translucent to Additive. Its Unlit
shading, opacity shape, relative 3–8 emission, Time animation and geometry
remain the same. Native graph getters verify the exact five-node graph, HLSL,
Time input, channel masks and absence of vertex displacement on both map
reloads. `output/unreal/additive-flame-native-import-1.log` exited 0; immutable
import and stove receipts are under `output/unreal/additive-flame-import-proof/`.

The initial packaged standing run crashed in the engine accessibility
initializer before producing an image. Its evidence is preserved in
`output/unreal/runtime/walking-interior-standing-hwrt-f78ab873-4eb6-4490-b9ad-7d85c8b5ab36/`.
After the application-scoped initializer repair, the same imported material
state passed standing native QA with exit 0 and no handled ensure in
`output/unreal/runtime/walking-interior-standing-hwrt-eb90f4c6-2801-4792-ae1f-74312d34027a/`.
The real 3840×2160 image shows straight patio glazing and the curved stove
reflections. The fire is still barely visible at this daylight exposure;
Additive alone has not achieved an acceptable flame appearance. Emission and
temporal appearance remain a controlled study, not a finished photoreal fire.

The later oak package also completed actual 4K daylight standing and night
captures. In `output/unreal/runtime/interior-night-hwrt-2ec8a012-1a84-4fba-b922-faf5e72c79fb/`,
the unchanged additive flames are clearly visible as three tall bright shapes.
The daylight standing capture in
`output/unreal/runtime/walking-interior-standing-hwrt-8e3850b3-9940-4ac2-afe8-2b476c619e2e/`
still shows weak fire. This confirms that the material renders and that daylight
exposure is a relevant constraint. It does not prove a suitable emission value
or realistic animated fire; any new intensity must be judged in both lighting
states before adoption.

## Neutral controls for the emission study

The native writer now authors ten flame nodes. `BreziFlameEmissionScale`
defaults to 1 and multiplies RGB only; opacity remains the unchanged Custom
alpha. `BreziFlameStudyTimeSeconds` defaults to −1 and selects ordinary Time
for every negative value. At zero or above, it selects the exact supplied time;
the If equality threshold is zero. HLSL, UV0, geometry and the original 3–8
relative emission remain unchanged. These parameters enable a controlled
comparison; no brighter production default has been selected.

The isolated NullRHI smoke in
`output/unreal/flame-emission-study/smoke/b88158159c0f41d09ba6f7874973d78a/`
passed with exit 0 and no warnings/errors. It constructed one unique material,
verified ten nodes and eleven actual reflected connections, and twice unloaded
and reloaded the saved asset with the old object absent before each load. Its
host receipt hashes every existing Content/Brezi file before and after: all
existing assets and the map were unchanged; only the owned smoke asset was new.

`output/unreal/flame-study-native-import-1.log` subsequently completed the full
actual import with exit 0, including the ten-node proof after both saved-map
reloads, retained source collision and the three-cabinet oak stage. Immutable
receipts are in `output/unreal/flame-emission-study/native-import-proof/`.
Warnings were limited to the existing deprecated editor-world getter and
material-free invisible collision meshes. Metal cook and packaging then passed
in `output/unreal/flame-study-launcher-package-1.log`, including the new C++
study controls. The first actual launch failed during macOS AppKit registration
before engine initialization; see [startup evidence](unreal-startup-launcher.md).
The subsequent same-binary startup entry passed actual packaged rendering; see
the linked startup evidence. The controlled captures described below use that
entry.

## Controlled capture progress

The initial study rejected an obsolete `r.UsePreExposure` CVar that is absent
from this UE 5.8.2 source. The prerequisite now follows the installed engine's
actual eye-adaptation controls. Each captured frame still requires paired
game-thread/render-thread identity and exact public render-thread pre-exposure
readback. No production exposure value changed.

In `output/unreal/runtime/flame-study-deacb852-34c6-4ba1-a315-87b73fdb2ee4/`,
all four daylight scales (1, 4, 16, 64) and night scale 1 passed, each with an
untouched production baseline followed by a controlled frame after 240
independently recorded warmup frames. All four daylight runs had matching
projection jitter, source camera, source materials, quality and manual
pre-exposure. Daylight scale 4 remains nearly invisible; 16 is faint and 64
clearly reveals the three flame shapes. Night scale 1 already shows bright
flames. These observations do not select a production value or certify
photorealism.

Night scale 4 stopped after its baseline, at game frame 404, and exited 0.
The old diagnostic combined a material/compositing check and walking-mode
check into the same failure status, so the cause cannot be recovered from
its post-restoration report. A subsequent C++ revision records the first
failed predicate, exact material pointers/scalar reads, component and sun
state, camera mode and standing diagnostics before cleanup, and records the
final sun separately. Walking-mode failure now has a distinct status.
The native build passed in `output/unreal/flame-failure-observation-package-2.log`.
The complete repeat then passed all eight processes with clean exits and all
baseline/control checks in
`output/unreal/runtime/flame-study-c9ecfcef-ab2d-47de-89d2-c2d3cb5037b4/study.json`.
The previous interruption did not recur; its cause remains unknown.

Root inspected all eight native controlled PNGs. The tool displayed the 4K
files at 2048 × 1152, so this whole-room visual review is separate from a
pixel-level inspection. The [hashed visual review](../output/unreal/flame-emission-study/visual-review-20260908.json)
records the observations: stronger emission improves daylight visibility but
increases white clipping and night bloom, while retaining three candlelike
shapes. A scalar increase alone was not accepted as a photoreal-fire revision.
Production scale stays 1. These synchronous stills are neither animated-fire
nor frame-rate acceptance evidence.


## Shape revision and instrumented reference, 8 September 2026

The new diagnostic mode was compiled and packaged successfully in
`output/unreal/flame-shape-instrument-package-1.log` (UAT exit 0). The combined
Unreal CPU suite passed 322 tests. Instrumentation was adopted separately from
the two material-recipe files, so the existing saved furniture map and original
shader could be captured with the same native code intended for the candidate.

The [reference index](../output/unreal/flame-shape-baseline-preservation/instrumented-baseline-index.json)
pins four successful original-shader runs: interior day/night and oblique night
have 62 images each; oblique day has two stills. Index 0 is ordinary production
Time=-1. Index 1 is phase 2 after a separate 240-frame warmup; sequence indices
2–61 advance the same transient material through exact float32 phases to 4 s
at 30 simulation Hz, without rebinding or restarting history. All runs passed
native 4K, source camera/stove axis, standing floor/eye, paired GT/RT frame,
material/glass/quality and restoration checks and exited cleanly. The oblique
source pose is a diagnostic viewpoint, not a revision of canonical house views.
Native endpoint entry does not prove walking the full approach.

The [root still review](../output/unreal/flame-shape-baseline-preservation/root-still-review.json)
inspected original-detail 3840 × 2160 phase-2 images, finding three separated
bright cores and thin vertical orange artifacts beside the oblique flame cards.
Full sampled-sequence visual comparison is still pending. These synchronous
readbacks and PNG encodes do not measure real-time playback or FPS.

The candidate shader `08a70ffa9d33bdddad0842b8d4a01e5737748acd6ff32cb21c4cc4ea3268172a`
changes alpha shape only: a connected lower body, unequal varying lobes, upper
breakup and four-edge fade. RGB/core/curl, production emission scale 1, default
ordinary Time=-1, geometry and glass are retained. The writer now reports
`emissionAndOpacityMatchPinnedShader` plus an explicit previous-shader relation;
it does not claim that alpha stayed unchanged. The exact two-recipe registry
retains historical baseline contract bytes. Its saved native import and package
both passed with exit 0 (`flame-shape-candidate-native-import-1.log` and
`flame-shape-candidate-native-package-1.log`). The saved getter confirms the
new shader and predecessor, ten nodes, eleven links and unchanged scale 1.

All four matching candidate arms passed the same native capture and restoration
checks: interior night `ae936637-03dd-4021-8ee1-64bc04d6ca73`, oblique night
`ace6bf80-f523-4698-8856-270282b48c3f`, interior day
`1ea2ea0d-0ab8-4ec8-add9-c8cb0f20d55b`, and oblique day
`7ff23915-8d3b-411f-894e-5ae99d077b27`, under `output/unreal/runtime/` with
their `flame-shape-<pose>-<state>-<mode>-` prefixes. The first three contain
62 images each; the last contains two stills. This establishes valid captures,
not a visual winner or real-time animation performance.

The [independent phase-2 night review](../output/unreal/flame-shape-phase2-night-independent-review.json)
finds a more connected lower fire and less uniform tips, but also pale planar
cores and conspicuous lower wedges in the oblique view. Root inspected the
original 4K interior-night candidate and also retained these material limits.
A later [root browser review](../output/unreal/flame-temporal-review/root-nine-phase-visual-review.json)
inspected the candidate's full source ROI at indices 1, 31 and 61 (phases 2, 3
and 4 seconds) in all three sequence conditions. The night wedges, wide pale
cores and vertical streaks remain in these sampled phases; at daylight scale 1
the fire is nearly invisible behind the reflected glazing. These nine inspected
states do not cover all 61 controlled frames or establish real-time playback.
Photorealism is not accepted.

The [import drift audit](../output/unreal/flame-shape-native-import-drift-audit.md)
prevents a strict shader-only A/B claim. Reimport rewrote all 1,878 canonical
mesh assets and many other saved assets; recorded object bounds, collision and
Nanite semantics match, but binary geometry/radiometric equivalence has not
been established. The native `__text` section matches across packages, while
other immutable Mach-O bytes differ. The temporal viewer therefore labels
these images visual context and keeps strict pair validation failed.

## Edge derivative: imported, packaged and captured, 8 September 2026

The [edge derivative revision](../output/unreal/flame-edge-derivative-draft/README.md)
has now been adopted. Its sole HLSL change replaces `fwidth(p.x)` with
`fwidth(UV.x)` to avoid differentiating the wrapped phase coordinate. Shader
SHA `45b0871f6776cc197686ff19cb8e7253babdc0c1ca41943d479f504a76f137bc`
is explicitly the successor of
`08a70ffa9d33bdddad0842b8d4a01e5737748acd6ff32cb21c4cc4ea3268172a`.
The saved graph retains ten nodes, emission scale 1 and default Time=-1;
its metadata records a changed alpha revision and agreement with the pinned
shader, not unchanged alpha relative to its predecessor.

The immutable [import receipt](../output/unreal/runtime/flame-shape-interior-night-sequence-2c650ba8-929f-443e-bcc5-d17a95cd85cb/import.json)
records `import-validated`, clean exit 0 and successful stove save/reload checks.
The copied [package receipt](../output/unreal/runtime/flame-shape-interior-night-sequence-2c650ba8-929f-443e-bcc5-d17a95cd85cb/package.json)
records completed cook without reported shader fallback and a verified standalone
bundle/signature. Their SHA values are respectively
`ffe997d87aaf840f21e5cd7c03110c102b2c6dae0c0323d447051c0d16f97cea`
and `b85a0e0c1054dc62d9f30362fb524a65e45859ff5ccbb185bea2fa3e107ec8ce`.
The [capture contract](../output/unreal/runtime/flame-shape-interior-night-sequence-2c650ba8-929f-443e-bcc5-d17a95cd85cb/contract.json)
pins source scene `61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b`
and source OBJ `a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455`.

The [interior-night sequence](../output/unreal/runtime/flame-shape-interior-night-sequence-2c650ba8-929f-443e-bcc5-d17a95cd85cb/flame-study.json)
passed with PID 8464, exit 0, no remaining renderer and unchanged packaged payload
before/after. All 62 original PNG hashes and 3840 × 2160 dimensions were verified.
Index 0 uses ordinary Time=-1; index 1 captures phase 2 after its separate
240-frame warmup; indices 2–61 advance to phase 4 at 30 simulation Hz. All frames
retain exact screenshot/GT/RT pairing, scale 1 and 100% render settings, with
HWRT Lumen, Nanite, VSM and TSR history 200. Material/component state, camera
mode and clock were restored after capture.

This is capture and provenance evidence only. Synchronous readback/PNG encoding
does not establish FPS or real-time playback; strict shader-only A/B equivalence
has not been established. Visual findings, including whether edge leakage is
reduced, remain a separate review. This derivative does not address the broad
lower silhouette, intersecting flame planes or log-contact geometry.


The [oblique-night sequence](../output/unreal/runtime/flame-shape-oblique-night-sequence-3595c080-22af-4add-bdac-37bf9d65c395/flame-study.json)
also passed the native capture validator with 62 original 4K PNGs and clean
process exit. The first attempt was refused because a separate ordinary app
instance had been opened by UI attachment after the previous capture ended;
that exact owned process was closed before the successful retry.

The [root visual review](../output/unreal/flame-edge-native-proof/root-six-phase-review.json)
inspected phases 2, 3 and 4 seconds for both night views using original-image
CSS crops. Pale broad cores, sharp lower sheet corners and the regular orange
log grid remain visible. The oblique view clearly exposes crossed flame cards
and incomplete fuel contact. This is not accepted as photoreal fire. The
mathematical derivative fix remains useful, but it does not replace volume and
material work. These six sampled frames do not establish full motion quality,
HDR clipping, brightness calibration or a controlled shader-only comparison.
