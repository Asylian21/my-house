# Lawn ground material

The full importer applies a component material override to `DOM_00001 / MAT_0001` after the LawnDetail pass. The canonical mesh material, millimetre geometry, source UV0, collision and 33,769 grass instances remain authoritative. The material uses ambientCG Grass004 4K colour, NormalGL and roughness maps; Grass004 is a CC0 procedural asset with an approximate 1.4 m tile, not a survey or photograph of the site.

`reference.json` pins the provider evidence and source files. `source.py` verifies the exported scene and matches native MeshDescription positions and UV0 to the source OBJ. `shading.py` blends three translated samples with shared weights and continuous UV gradients. Colour is sRGB and the normal map's green channel is flipped once. The provider roughness map remains linear input; the undisplaced turf base uses explicit artist effective roughness `0.72 + 0.23 * raw`, bounded to 0.72–0.95 for normalized input. This keeps local map variation but is neither the unmodified provider BRDF nor vendor/site radiometric calibration. No geometry displacement is applied.

Run from the repository root:

```sh
python3 -I -B scripts/unreal/lawn-ground/restore_inputs.py
python3 -I -B -m unittest discover -s scripts/unreal/lawn-ground -p 'test_*.py'
node --test scripts/unreal/lawn-ground/test-package-gate.mjs
npm run unreal:import
npm run unreal:package
```

On a fresh checkout, `restore_inputs.py --download` retrieves the three exact pinned ZIP members. Existing conflicting files are refused. The importer verifies inputs before replacing the map; the package gate requires a successful saved material and asset receipt.

The writer stages four owned assets, saves and reloads them before activation, then saves and reloads the selected override. It checks the source geometry and the surrounding scene after both roundtrips. On failure it attempts to restore the previous override, preserving exact ownership and protected scene checks even when the candidate graph is invalid. A failed restoration stays an explicit failure.

Before intentionally changing an already active recipe, restore its source binding using `restore_lawn_ground(scene, geometry)` under the matching existing writer. Restoration is an intermediate state that cannot pass the candidate package gate. The older LawnDetail preservation receipt describes that earlier stage; a final composition readback must account explicitly for this one later material change.

Native material validation and a successful cook do not establish visual quality or performance. Review the cooked application at the terrace camera in native 3840 × 2160, including texture repetition, roughness highlights and compatibility with the grass instances.

[Provider](https://ambientcg.com/view?id=Grass004) · [CC0 terms](https://docs.ambientcg.com/license/)
