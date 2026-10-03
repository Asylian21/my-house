# R17a — native leaf transmission comparison

R17a has now been saved and compared in a fresh native Editor-game process.
The observed change is small; photorealism, Shipping-package and performance
acceptance remain false.

On 1 October 2026, native PID 12506 completed with exit 0. The actual saved map
has exactly 23 leaf-slot overrides / 78 trees and two new Material packages;
the original 3,974 other Content files are byte-identical. Fresh Editor-game
PID 17892 completed the same close camera as the R16 baseline PID 14710.
Both original 1,920 × 1,080 PNGs were inspected independently. Leaf interiors
are slightly brighter but remain dark; repeated shapes, plain neighboring
houses and the flat green foreground are still visible. Configured camera,
lighting and postprocess settings match, while measured auto-exposure differs
by +0.01215 EV. Both runs have application foreground 0/300, so their timings
do not establish performance. The saved native graph/override proof and fresh
render proof are separate; the capture recorder does not enumerate materials.
The paired review is
`output/unreal/exterior-validation-20260930-r1/canopy-transmission-paired-editor-r16-r17-audit-r1.json`.
R17a remains a material candidate and has not replaced the active R5 package.


The original frozen method is in [unreal-canopy-transmission-r1.md](unreal-canopy-transmission-r1.md).
