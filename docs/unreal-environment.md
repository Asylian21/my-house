# Native macOS environment and import evidence

The native layer uses Unreal Engine 5.8.2 alongside the existing 2D documentation
and Babylon.js application. The TypeScript source and its validated assembled
geometry remain authoritative. Engine configuration, imported assets and a
successful build are separate from visual acceptance and measured frame rate.

## Repeatable environment audit

Run `node scripts/unreal/audit.mjs`. It writes
`output/unreal/environment.json` and prints the same JSON. `UNREAL_ENGINE_ROOT`
can select another installation; `UNREAL_AUDIT_OUTPUT` can select the report file.
The audit reads hardware, OS, SDK, compiler, installed engine version and native
Metal capabilities. It does not launch Unreal, install software or read accounts.
The report uses an explicit allowlist: no serials, UUIDs, usernames, hostnames,
device identities or raw command output are persisted.

The initial September 8, 2026 audit found:

| Item | Observed state |
| --- | --- |
| Hardware | MacBook Pro, M5 Pro, 18 CPU / 20 GPU cores, 48 GB unified memory |
| GPU | Metal 4; native Metal reports ray tracing support; Apple8 and Apple9 GPU families |
| System | macOS 26.6.2, arm64 |
| Display | Built-in 3456 × 2234, 120 Hz; no physical UHD display attached |
| Storage | About 1.31 TB physical APFS free; regenerate the audit for current capacity |
| Toolchain | Xcode 26.6, macOS SDK 26.5 |
| Installed tools | Unreal 5.8.2 (CL 56702186), Blender 5.2.1 LTS, Epic Launcher 20.2.9 |
| Shader compiler | Metal Toolchain was initially missing; installed during setup, then `metal --version` and `metallib` resolved successfully |

The engine's `Engine/Config/Apple/Apple_SDK.json` declares Xcode 26.1.1 as its
main version and permits 15.2.0–27.9.0. The installed 26.6 is inside that range.
This check does not replace compiling the project and shaders.

## Metal feature support

[Unreal 5.8 release notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes)
announce Metal ray shaders and Mac path tracing, recommending macOS 26.4 or
newer for a driver fix. The more general
[macOS requirements page](https://dev.epicgames.com/documentation/unreal-engine/macos-development-requirements-for-unreal-engine?lang=en-US)
still contains a conflicting unsupported-HWRT row. Use the version-specific
release notes, installed engine source and actual runtime evidence together.

The installed engine's `Engine/Config/Mac/DataDrivenPlatformInfo.ini` enables
Lumen, ray tracing, ray shaders, inline ray tracing, path tracing and Nanite for
`METAL_SM6`. Its Metal device code checks `supportsRaytracing()` before enabling
ray tracing; the audited M5 Pro reports that capability. These facts establish
eligibility. They do not claim acceptable Lumen quality, native 4K frame rate,
working caustics or a photographically convincing scene.

Nanite is enabled by the import generator only for opaque static meshes with at
least 512 source triangles. Translucent materials and door-motion objects retain
their ordinary meshes. Source triangles are retained for collision/RT fallback.

## Headless import and its contract

`scripts/unreal/import_scene.py` runs inside the Unreal Python editor commandlet:

```sh
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" \
  "$PWD/unreal/BreziTwin/BreziTwin.uproject" \
  -run=pythonscript -script="$PWD/scripts/unreal/import_scene.py" \
  -unattended -nosplash -nullrhi
```

Set `BREZI_GEOMETRY` to override `output/unreal/geometry`. The script requires
the current validated `scene.json`, `bridge-report.json`, `validation.json`,
`viewpoints.json`, `walking.json` and runtime `brezi-twin.glb`. It checks source hashes and object
identities before importing. It never imports `brezi-archive.glb` into the
runtime map.

The generated map is `/Game/Brezi/Maps/Brezi`. Individual source `DOM_#####`
identities remain separate static mesh actors, tagged and grouped for selection.
Generated pipelines live in `/Game/Brezi/Pipeline` and imported geometry under
`/Game/Brezi/Geometry`. Repeated generation only replaces tagged generated
actors; an unrelated existing map is rejected. The runner then applies the native
PBR, optical, walking-collision and vegetation passes. These preserve the source
identities and record their inputs and final saved asset hashes separately.

Unreal 5.8.2's local glTF import source establishes this conversion:

```text
glTF metres [x, y, z] -> Unreal centimetres [100*x, 100*z, 100*y]
source OBJ millimetres [x, y, z] -> Unreal centimetres [x/10, -y/10, z/10]
```

`GLTFCore/Private/GLTF/ConversionUtilities.h` swaps Y/Z;
`InterchangeGltfPrivate.h` sets the conversion multiplier to 100;
`InterchangeGltfMesh.cpp` applies it to mesh positions and
`InterchangeGltfTranslator.cpp` to node translations. Do not add another unit
conversion or an extra axis reflection during native import.

The generator reads each imported component's actual native world bounds and
compares all six extents with its source record, with a maximum tolerance of
**0.05 cm / 0.5 mm per object**. Missing, duplicate and archived objects fail the
run. Source walk-surface/static camera-occluder metadata selects collision using
the imported triangles (`ComplexAsSimple`); the generator creates no box or
convex proxy. The walking pass also enables the 38 captured-closed door/hatch
blockers. Twelve hidden supports reuse the exact source floor mesh translated by
its declared walk-surface offset; original visible geometry stays unchanged.
Opening doors still needs native interaction parity work.

The environment contains a movable directional light tagged `BreziSun`, a
SkyAtmosphere and movable real-time SkyLight tagged `BreziSky`. Sun rotation
comes from the exported location/date calculation. The initial 80,000 lux value
is a clear-sky lighting input, not a measured site illuminance. Exposure uses a
histogram with an EV100 range of −4 to 16; this requires the project's extended
luminance-range setting. Final interior/exterior balance requires rendered QA.

Always construct the solar rotation with named Python arguments
`unreal.Rotator(pitch=..., yaw=..., roll=...)`. UE 5.8 Python's positional order is
`roll, pitch, yaw`, whereas the sidecar stores `pitch, yaw, roll`. The first
render exposed this mismatch: a requested −28.26° solar pitch became +30.87°,
placing the sun below the horizon and producing a black daytime sky. A read-only
native map probe confirmed the actual actor/component values. The corrected
generator checks both the stored Euler angles and forward vector against the
source before saving, and its receipt records the measured native rotation.

`output/unreal/import-report.json` starts as `pending`, becomes `failed` on an
exception and becomes `import-validated` only after native bounds checks and
asset/map saves. It includes source hashes, per-object bounds, collision and
Nanite state, and the saved map hash. Initial geometry collision and final
post-authoring collision are recorded separately, with the final state measured
from each native component. A NullRHI run does not render any frame.
Its report explicitly leaves visual quality and native 4K performance unverified.

The first successful native import on September 8, 2026 returned exit code 0:
all **1,878 runtime objects** were accounted for, **17 archive objects** stayed
outside the runtime map, and the maximum measured world-bounds error was
**0.009765625 mm**. It generated 155 triangle-collision objects, built 97 eligible
Nanite meshes and saved the 6.79 MB map. Current receipts supersede these initial
figures after further exports.

`npm run unreal:import` enables `BREZI_APPLY_MATERIALS`, `BREZI_APPLY_OPTICS`,
`BREZI_APPLY_VEGETATION` and `BREZI_APPLY_WALKING` by default. An explicit `0`
disables an individual pass and the receipt names that reduced mode. Every
requested pass must exist and succeed; an exception fails the import receipt.
Both reduced and complete imports still require rendered visual acceptance.

Before a full import on a checkout without the ignored photographed-wood cache,
run `python3 scripts/unreal/tv-oak/fetch_assets.py` followed by
`python3 scripts/unreal/furniture-oak/restore_inputs.py`. These restore pinned
photo/recipe inputs without overwriting different files. Native material
authoring still happens in the importer. See [TV oak](unreal-tv-oak.md) and
[kitchen/dining oak](unreal-furniture-materials.md) for scope and current evidence.

The package runner checks source, recipes, map and final asset hashes before and
after UAT. It rejects shader compiler failures and fallback-material messages
even if UAT exits successfully. Bundle verification includes both JSON contracts,
runtime dependencies, signature and a digest of every bundle file. QA checks
those digests again before launch. These checks establish provenance; they do
not establish frame rate or photographic quality.

## Remaining acceptance evidence

The isolated engine candidate completed an Editor Renderer build and ABI load,
then a fresh Mac cook on 8 September 2026. The [cook evidence](../output/unreal/engine-candidate/latest-cook-result.json)
records process exit 0 in 727 seconds and one real non-cache compilation each for
`FFloorCausticsPreparePS` (7,859 bytes) and `FFloorCausticsCompositePS` (3,942 bytes)
in `METAL_SM6`. The three requested floor/water/glass material packages have
saved shader maps. All 2,390 original project inputs were unchanged during that
isolated cook interval. The preserved raw audit is still failed: its two findings
are separately classified as the exact generated `CookerOpenOrder.log` and a
disclosed optional Zen startup warning. This is not a warning-free cook claim.

The candidate Editor dylib is insufficient for a standalone application. The
current Game linker response uses 38 statically linked Renderer objects, still
byte-identical to the installed engine's objects. The candidate Game Renderer compile is now complete as recorded below;
a complete Game link is still required before testing this engine change
inside `.app`. Shader compilation alone does not prove GPU dispatch, the enabled
caustics provider, energy conservation in the rendered image or performance.

Use a Metal renderer session and a packaged arm64 application to verify native
3840 × 2160 render dimensions, actual render scale, camera transitions, interior
walking, daytime/nighttime appearance and CPU/GPU frame time. A 4K render target
can be produced on this Mac; physical 1:1 UHD display inspection requires a
connected display with at least 3840 × 2160 pixels. Preserve separate evidence
for asset import, native build, packaged launch, rendered images and performance.

Installed binaries already avoid any new engine-account setup. If a new engine
installation becomes necessary, follow Epic's
[official installation procedure](https://dev.epicgames.com/documentation/en-us/unreal-engine/installing-and-setting-up-a-project).
The [5.8 release announcement](https://forums.unrealengine.com/t/unreal-engine-5-8-released/2729274)
also contains the version's hotfix history.


### Candidate Game Renderer graph, 8 September 2026

The isolated Game project preparation and UBT action export have now passed.
The frozen source copy contains 70 files; only the generated package counter
and editor file-open-order log differed from the earlier planning snapshot.
Preparation preserved 11,251 candidate output files using independent APFS
copies and changed no existing candidate files outside the new run.

The [root graph review](../output/unreal/engine-candidate/game-renderer-graph-plan/root-initial-graph-review.json)
records 43 compile actions: one Game Engine PCH, 38 Renderer unity units, and
separate DeferredShadingRenderer, FloorCausticsRendering, LightRendering and
SingleLayerWaterRendering units. All 42 Renderer actions depend on the Game PCH.
Its shared definitions are WITH_EDITOR=0, WITH_EDITORONLY_DATA=0 and
IS_MONOLITHIC=1. UBT exited successfully in 4.33 seconds. No C++ action or link
was executed. The subsequent audit verified 467 explicit input files, all 381
Renderer source units and the 86 generated changes. The actual UBT managed
importer/linker then validated the adapted graph's 43 actions and 42 edges in
7.48 seconds, without executing a native compiler. Its
[postcheck](../output/unreal/engine-candidate/game-renderer-managed-preparation-postcheck.json)
confirmed unchanged source/critical pins, both copies of all 11,251 backups and
the frozen project snapshot. This managed preparation preceded the native
compile recorded below; complete Game linking remains pending.
Later controller and renderer-settings helper changes in the main project are
not part of that frozen copy. The original engine and prior closed Editor
ABI/cook receipts remain unchanged.


### Candidate Game Renderer native compilation

The [native compilation result](../output/unreal/engine-candidate/latest-game-renderer-compile-result.json)
records all 43 real compile actions, native exit 0 and 151.07 seconds for PID
66248. There are 42 Game Renderer objects, a Game PCH and 43 nonempty dependency
files. Every one of the four separate overlay units includes its own source
and both FloorCaustics headers, with no original installed-engine include path.
The 43 stock UBT action-result files each match the frozen command, compiler
version and response and report success/exit 0. No link or GPU run occurred.

The original host audit remains failed and preserved: its output allowlist
missed 43 normal UBT action-result JSON files (with .bin names) and one cloned
project XmlConfigCache.bin. A separate read-only classification identifies all
44 files, 502,339 bytes, within the candidate and cites their stock UBT writers.
No installed engine or root source/config was changed during the closed
compile interval; both root snapshots match. The host saw only the dotnet
process in its process group, so independent compiler concurrency was not
measured. Four parallel actions were configured and logged by UBT. The final
process inventory was empty before the root resumed its separate stock build.

The frozen Game project copy remains older than the main project's navigation
and camera fixes. A complete monolithic Game link must explicitly consume the
42 new objects before a current candidate app, enabled caustics provider and
native GPU result can be claimed. Fresh products must be backed up before any
UBT graph export that may invalidate/delete outdated outputs.

### Current project and monolithic Game link

The next isolated snapshot now contains all 72 current project files, including
the navigation action, clean camera lens, day/night camera-cut correction and
renderer-settings helper. The prior 70-file source snapshot and completed
Renderer products remain backed up. A full Game metadata export succeeded
without executing its native actions; the exact Link response includes the
42 candidate Renderer objects. Its 0–62 compile/link subset was imported by
the actual UBT managed code and verified as 63 actions, 80 dependency edges
and 125 declared products.

The [current Game compile/link result](../output/unreal/engine-candidate/latest-game-link-result.json)
then passed with no audit errors: PID 77275, native exit 0, 63/63 actions,
140.13 seconds in UBT (140.90 seconds in the host). It produced 61 objects,
one PCH, 62 dependency files and the monolithic Game executable. The process
monitor captured all 63 matching compiler/link drivers, observed at most four
concurrently and drained its owned descendants. Current root/clone sources,
protected installed-engine inputs and fresh independent backups remained
unchanged over this closed interval.

This closes Game compilation and linking. The subsequent Content copy passed:
2,244 Content files, 2,127 final imported asset hashes, three runtime Data
contracts and exactly the two current Editor-module files were verified.
The new Game executable remained byte-identical. Root source/Content, the
complete stock payload/receipt and installed engine remained unchanged.

The current project then completed all nine bundle postbuild actions and a
fresh full map cook: commandlet PID 87007 exited 0 in 121.68 seconds, producing
7,384 cooked files. Both new floor shader types are present in this cook; their
code came from the verified warm cache, so this does not claim fresh shader
compilation. The direct-commandlet receipt preserves and separately classifies
the optional Zen service warning and generated CookerOpenOrder bookkeeping.

UAT PID 89909 completed stage/package/archive with exit 0 (21.39 seconds).
The separate candidate app contains 37 regular files, 1,352,625,798 bytes,
verified bundled UFS/Data dependencies and a deep/strict local ad-hoc signature.
Sealing preserved the linked Game code; packaging changed only the validated
signature and its corresponding LINKEDIT sizes. Earlier cache-isolation,
process-supervision and signature-comparison host failures remain recorded
alongside their specific corrections. They are not successful native runs.

This closes creation of the candidate app. Subsequent standalone pool and
terrace runs both passed continuous native 3840 × 2160 rendering with unchanged
Lumen HWRT, Nanite, VSM and TSR200 settings. Each observed all 300 benchmark
samples in the foreground with an active window and keyboard focus, then
exited normally with clean logs, drained AX queues and unchanged bundle/input
hashes. The [candidate package and runtime pointer](../output/unreal/engine-candidate/latest-candidate-package.json)
links the separate immutable package and both runtime receipts.

Observed mean frame intervals were 55.93 ms at the pool and 47.00 ms on the
terrace (about 17.9 and 21.3 FPS). These single-view runs do not meet the smooth
interactive goal or establish a performance improvement over another build.
Visual acceptance remains open. The stock app/receipt, root source and Content,
and installed engine stayed unchanged through package finalization and these
runtime checks. The new floor caustics renderer was dormant: no registered
provider or floor irradiance transport was exercised on GPU.
