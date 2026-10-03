# R20 original curved grass: isolated 64-root pilot

This source-only pilot replaces 64 existing retained continuous-meadow roots
near the original PARCELS camera. It adds no population and does not address
the source-empty foreground in the grove close view. C/B/B, both3000mm
setbacks, architecture, lighting, all original assets and other roots stay intact.

The original Poly Haven `grass_medium_01` glTF is CC0, credited as modeling
and photographic maps. It is not described as a whole-plant scan. Selected
original nodes are small_a (mesh 0, 833 triangles), small_b (mesh 6, 653), and
tall_c (mesh 5, 340), with 24/24/16 existing roots respectively. Reference-sheet node translations
are ignored. Original vertex X/Z, normals, UVs and ordered indices remain
unchanged; minimum Y is subtracted to root the model. The exported glTF stays
right-handed Y-up in metres; installed UE5.8 ConvertVec3 maps (X,Z,Y) to cm.
Original UV derivatives generate genuine orthogonal tangents with handedness.

All 64 chosen roots lie 7.47–10.67 m from the original camera in exactly four
retained LawnTuft groups. Uniform scaling preserves each original root XYZ,
authored yaw and 12.09–19.15 cm height. Every scaled source vertex stays inside
14 cm radius, within the original 141 mm whole-crown safety mask. The selected
source rows are recomputed from the pinned saved R16 placements, camera and
original LawnTuft prototypes. Managed photolawn's 102011 roots remain unchanged.

UE HISM removal forces RemoveAtSwap. The helper removes only the exact 64
indices in descending order and records the resulting retained original-index
permutation. Every retained decoded transform remains exactly identical; it
does not recreate thousands of unselected transforms. New groups copy the
selected native root translation/rotation into uniform height-fit transforms.
Matrix decomposition roundoff of a copied quaternion is bounded at 1e-12 per
component; authored source yaw is exact. Source-height readback error is bounded
at 1e-9 cm and actual all-vertex radius must still be ≤14 cm.

Three new masters each have three identical full copies of original LOD0.
This explicitly supplies no provider LOD chain or simplification. The pilot costs
41104 triangles at every LOD versus 16384 removed near triangles. Original meadow
LOD thresholds [1,.025,.007], 7200/9000 cm culls and quality-density flags remain.
Source costs are not native draw counts or performance acceptance.

One new masked TwoSidedFoliage graph binds the untouched separate original
alpha PNG red channel at clip .5. The original RGB JPEG has no useful alpha and
the provider glTF BLEND binding does not reference that sidecar. Original UV0
maps RGB directly to albedo, OpenGL normal with native green flip, ARM.R to AO,
ARM.G to roughness and ARM.B×provider factor 0 to metallic. AO never multiplies
albedo. UE-only subsurface .08 and specular .5 are explicit unaccepted shading
calibrations. Four new native texture objects retain the unchanged source pixels.

Only root may create an independent R20 clone and run the commandlet. The
helper requires original 3975 Content and 132 protected project files, original
recorder module/engine BuildId and all immutable consumed-source pins. It loads
the actual original saved R16 map and reads all existing geometry/materials.
Only the map and exact 11 new packages (3 meshes, 1 material, 4 textures,
3 pipelines) may differ. All original 42 graphs/74 textures and 135 plant
masters/405 LODs stay unchanged. Full before/expected/saved actor witnesses
permit only the 64-member deletion and 3 bounded new groups: 1983 groups,
5309 actors, 632026 instances.

Native success requires saved map unload/reload, full-scene witness equality,
all 9 original position/UV/topology/winding readbacks, correct material graph,
original member preservation, Content and protected project byte checks.
Python does not expose a full native normal/tangent readback here; exported
sourceframes and disabled native recomputation are verified separately.
Material/mesh package independent cold reload is not claimed. Appearance,
Shipping and performance remain unaccepted until root captures and reviews
the actual matched native views.

Root-only launch variables are `BREZI_CURVED_GRASS_PLAN`,
`BREZI_CURVED_GRASS_PLAN_SHA256` and `BREZI_CURVED_GRASS_OUTPUT`. The native script
is `scripts/unreal/exterior-curved-grass-native.py`; use UnrealEditor-Cmd with
`-unattended -nullrhi -run=pythonscript` and a unique own log. Source producer
`scripts/unreal/exterior-curved-grass-study.py` never launches native/GPU.
