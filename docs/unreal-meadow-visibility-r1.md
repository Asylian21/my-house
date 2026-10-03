# R19 visibility experiment

This source study selects one component-only distance experiment on the saved
original R16 project. It does not import models, change materials or place new
vegetation. All 601 exact target HISM components use start 18000/end 24000 cm:

- 471 original LawnTuft components /477117 roots, previously 7200/9000 cm. The
  original 20 m cells include meadow, understory and 15111 yard roots; all remain.
- 130 original canopy-ecology components /24773 roots, previously 8000–12000 cm
  ends, with their exact per-family starts preserved in the before receipt.

The parcel camera has real existing field vegetation outside90m. The distant
grove camera also has actual ecology roots outside its original 80–120 m ends.
240 m is selected; 360 m is a source count comparison only. Source instance and
triangle estimates are not renderer draw counters or performance evidence.

The close eye [5700,18300,145] has no low-plant root until 16.966 m. Its 2/5/10/15 m
centerline samples are 14.966/11.966/6.966/1.967 m from the nearest ecology root.
That foreground is unplanted. Raising a cull distance cannot repair it. The
existing ecology/substrate domain is the 3055.21 m² crown union inside the source
grove, with 10 cm inset and protected/subject/road/building/cultivated exclusions.
It sits on the explicit unresolved flat backdrop at Z−25 cm, not measured terrain.
A future new planting must use an independently reviewed placement/ground plan;
the current source masks cannot silently be widened into the empty foreground.

Installed UE 5.8 HISM code limits final distance by both foliage screen size and
instance end distance times ViewDistanceScale. LOD selection starts with index 1.
The study uses actual original prototype triangles [256,64,24], original native
LOD screens and source all-LOD AABBs/group-average scales. It assumes default
ViewDistanceScale 1/foliage.LODDistanceScale 1; those actual runtime cvars were not
recorded. Point frustum estimates omit bounds, occlusion, cluster overdraw,
dithered transitions and shadow passes. Native timings remain unaccepted.

The native helper must run only in a fresh root-prepared independent R19 project
clone. It reuses the immutable R16 base inventory/module and consumed-source
readback proof from the earlier transmission study, only as original base
evidence; it never invokes that experiment's material duplication or mutation.
Every source dependency is SHA pinned. The original 42 graphs/74 textures and all
135 plant StaticMeshes/405 LODs remain exact. No new native asset is allowed.

Native processing checks the original scene, changes only the 601 listed cull
pairs, saves and unloads/reloads the map, then requires the complete actor witness
to equal the exact before-scene counterfactual. Transforms, material bindings,
light, density, collision, shadows, ray tracing and all other render flags stay
equal. Only Brezi/Maps/Brezi.umap may change; original R16 bytes and all other Content,
Config/Source/Binaries/descriptor remain exact. The original import report is
never copied or overwritten. The separate overlay receipt records actual native
PID, saved culls, before/expected/after witness hashes and actual changed map.

Root command after preparing the fresh clone and waiting for native/GPU idle:

```sh
BREZI_MEADOW_VISIBILITY_PLAN=/Users/davidzita/www/dom/output/unreal/exterior-meadow-visibility-20261001-r1-study/meadow-visibility-plan.json \
BREZI_MEADOW_VISIBILITY_PLAN_SHA256=USE_FINAL_FROZEN_PLAN_SHA \
BREZI_MEADOW_VISIBILITY_OUTPUT=/Users/davidzita/www/dom/output/unreal/exterior-20261001-r19a \
"/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" \
/Users/davidzita/www/dom/output/unreal/exterior-20261001-r19a/Project/BreziTwin/BreziTwin.uproject \
-unattended -NullRHI -nosplash -ExecutePythonScript=/Users/davidzita/www/dom/scripts/unreal/exterior-meadow-visibility-native.py
```

Source CPU tests and estimates select a native trial only. Actual original R16
and saved R19 parcel/grove PNG pairs must later use identical camera/profile/
warmup settings in separate real runtime processes. No Shipping package, native
appearance, performance or full photorealism is accepted by this source study.
