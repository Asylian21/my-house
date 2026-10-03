# Isolated leaf transmission experiment R1

This experiment is source preparation for a native comparison. Appearance,
photorealism, Shipping-package and performance acceptance remain false.

The saved R16 native exterior contains 42 Material graphs, 74 Texture objects,
135 plant StaticMeshes / 405 LODs, and 23 fuller grove HISM groups / 78 trees.
The oak and green leaf graphs already use Masked / Two Sided Foliage. Their
`BreziExterior:leaf-transmission-scale` Constant is stored as the float32 value
of 0.08. The transmission expression is `return Color*Strength*Mask;` and feeds
Subsurface Color. The selected experiment changes only that Constant to the
float32 value of 0.24 in two new full Material duplicates.

The installed UE 5.8 `ShadingModels.ush` multiplies foliage direct transmission
by SubsurfaceColor; `DiffuseIndirectComposite.usf` also uses it for foliage
backface indirect light. This predicts a threefold multiplier for those terms,
not a threefold pixel brightness increase. It does not prove that low
transmission caused every dark canopy pixel or that 0.24 is physically correct.
Dense canopy interiors can correctly remain dark.

The duplicates live in `/Game/Brezi/CanopyTransmissionR1/Materials`. Only leaf
slot 1 on the exact 23 selected grove components receives an override. Bark
slot 0, all original StaticMesh material slots, all other uses of the green
leaf material, every original graph/texture, lighting, geometry, transforms,
collision, culls and quality/density flags are preserved. The saved map and
two new material packages are the only permitted Content byte changes.

`exterior-canopy-transmission-study.py` records the actual original R16 report,
all original Content hashes/bytes, protected Config/Source/Binaries/descriptor
bytes, the exact consumed native readback code, shader source evidence and the
new source closure. Its typed plan is derived from saved native group and
static-mesh bindings, not inferred from group names. CPU tests cover alias
scope, scalar-only graph mutation, protected asset edits, unexpected assets,
foreign overrides and transform/source drift. They are guard evidence only.

Root prepares a fresh independent R17 project clone from the original R16
Project directory. The R16 exterior report remains a read-only external pin;
it must not be copied into R17 as a current exterior report. APFS clones are
allowed; hardlinks and symlinks are rejected. Root alone launches the new
native helper with `BREZI_CANOPY_TRANSMISSION_PLAN`, its exact
`BREZI_CANOPY_TRANSMISSION_PLAN_SHA256`, and
`BREZI_CANOPY_TRANSMISSION_OUTPUT`.

The helper reads the original graphs from actual Material nodes, duplicates
them with Unreal's EditorAssetLibrary API, sets the one tagged Constant,
recompiles and saves them, applies the 23 component overrides, saves the map,
unloads it and reloads it. A complete actor/component witness from the frozen
native pipeline compares protected geometry, lights, instance transforms,
material bindings, culls, collision/navigation and render policy. Actual
original material/texture settings and every protected package byte are also
checked before and after. The separate `canopy-transmission-native-report.json`
records the observed process, changes and saved readback; it is not an exterior
import report. A failure preserves its receipt and candidate for diagnosis.

Material graphs are read after map reload; this does not claim an independent
material-package unload/reload. The subsequent fresh Editor-game process
loads the saved package bytes and provides that separate process evidence.
The original frozen Editor QA wrapper requires a new typed overlay adapter:
validate the original R16 report pin, completed overlay receipt and its
candidate Content inventory, including exactly the changed map and two new
Materials. Never replace the R16 report's original asset hashes with current
R17 hashes. Keep source/native/Editor-game/Shipping evidence separate.

Compare unchanged close and grove cameras under the same imported daylight,
cinematic screen settings and warmup. Inspect leaf modelling, backlit colour,
interior contrast and unintended colour washing using original native PNGs.
Keep the meadow cull-distance experiment separate. No geometry or texture
change belongs in this transmission trial.
