# Original curved grass: exact native root serialization repair R4

The R20c third native trial imported the original three grass meshes and their
four photo maps, then stopped before saving its map. Its arbitrary 1e-12
quaternion comparison rejected the stored matrix's decomposition. All frozen
R1–R3 sources, source geometry, recipes, selection controls and failures remain
unchanged.

The first transient diagnostic reconstructed a quaternion with `unreal.Quat`.
That constructor narrowed its values and did not match the real helper input;
its result is preserved but is excluded from acceptance. The second probe
loaded the untouched original map read-only and captured actual original
`unreal.Transform` wrappers. It copied their translation and rotation directly,
exactly as the native helper does, and inserted the source uniform height fit
into three unregistered transient HISM components without a static mesh.

The faithful native probe PID 42431 exited 0. Every one of 64 pre-insertion
XYZ, quaternion and uniform scales matched exactly. All recovered XYZ remained
exact; all original 5306 actors and the saved map bytes remained unchanged.
Actual reflected `PerInstanceSMData.Transform` row planes were available for
every inserted instance. The installed current storage declaration is `FMatrix`;
the probe records double row planes, not a presumed FMatrix44f or GPU buffer.

Measured maxima are quaternion-component difference 6.879197211873134e-11,
rotation angle 5.617559289494492e-9 degrees, scale-component difference
2.5807511683240136e-10, derived height difference 1.7763568394002505e-15 cm,
derived radius difference 2.610866189911576e-9 cm. The largest decoded full
vertex radius is 13.999151868697306 cm, within the original 14 cm envelope.
These are measurements, not new numerical acceptance epsilons.

R4 requires the new input frame to equal its own original wrapped native frame
and source uniform scale exactly. Each recovered Transform and actual stored
FMatrix must match that root's corresponding faithful native probe row in every
binary64 bit, including signed zero. It repeats those checks after the map is
saved, unloaded and reloaded. It retains the source authored height, source
float32 positions/normals/UVs/indices/tangents, and both decoded and stored-matrix
full vertex radius limits. It rejects any changed root, matrix, scale, quaternion,
source height, missing storage readback or unrelated row; it introduces no
general numeric epsilon.

The R2 measured 66-path source-radius repair and the R3 exact enum preflight
remain delegated without edits. Original 42 graphs, 74 textures, all existing
static meshes and every other actor/member are still protected by their frozen
checks. The candidate changes exactly 64 existing taller meadow members in four
HISMs, creates three HISM groups and 11 owned native packages, and keeps all new
groups' culls at 7200/9000 cm. Three identical full-shape pilot LODs remain
explicit: 41104 population triangles each. No native performance or full visual
acceptance is claimed by the source supplement.

Root prepares a fresh independent original R16 clone at
`output/unreal/exterior-20261002-r20d/Project/BreziTwin`. Root alone launches
`exterior-curved-grass-native-r4.py` with the unchanged original
`BREZI_CURVED_GRASS_PLAN`, its original SHA256, and `BREZI_CURVED_GRASS_OUTPUT`
set to the new R20d output. It writes its own
`curved-grass-native-report-r4.json`; process files use the stem
`curved-grass-native-r4`. The truthful report owner is the new R4 helper and
repair schema is `brezi-original-curved-grass-exact-native-transform-repair-r4`.
Actual saved native success and matched original screenshots are still required.
