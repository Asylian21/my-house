# Blender assets for the interactive DOM presentation

This pipeline reads the saved Cycles scene and prepares portable, textured glTF assets. It does not save or modify the source `.blend` file. Install these scripts under `scripts/archviz/web/` in the DOM repository.

Prerequisites: Blender 5.x, Python 3 with Pillow, the existing `output/archviz/dom-archviz.blend`, `output/archviz/scene.json`, and downloaded `output/archviz/assets` from the archviz pipeline.

Run from the repository root:

```sh
python3 scripts/archviz/web/prepare_textures.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/archviz/web/export_web.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/archviz/web/grass_placements.py
```

The default output is `output/archviz/web/`. Each script accepts `--root PATH` and `--output PATH`. Blender script arguments follow `--`; the two Blender scripts also accept `--source PATH` for a different saved source scene.

```sh
python3 scripts/archviz/web/prepare_textures.py --root /path/to/dom --output /path/to/assets
blender --background --python scripts/archviz/web/export_web.py -- --root /path/to/dom --output /path/to/assets --source /path/to/dom-archviz.blend
blender --background --python scripts/archviz/web/grass_placements.py -- --root /path/to/dom --output /path/to/assets --source /path/to/dom-archviz.blend
```

For a different source scene, `scene.json` must describe its same authoritative source objects and the original asset paths must remain available.

## Deliverables

- `export-manifest.json`: source hash, per-file checksums and sizes, exact source names, group metadata, triangle/material/image counts.
- `dom-architecture.glb`: roof, walls, windows, floors, decking and pool. Geometry retains source coordinates and fine bevels.
- `dom-interior-*.glb`: complete retained source interior in hosting-size chunks.
- `dom-landscape.glb`: original ground, hardscape and visible fence geometry.
- `dom-living.glb`: 249 actual Blender plant placements with five shared optimized meshes, scanned cutout base colors, roughness and normals.
- `dom-terrace.glb`: scanned table and two chairs.
- `dom-grass-prototype.glb` plus `grass-placements.json`: one shared scanned tuft and a deterministic density-controlled placement set.
- `credits.json`: asset attribution from `assets.lock.json`.

Each GLB embeds its textures and needs no external geometry decoder. Every asset stays under 20 MiB. Color, roughness and normal maps are at most 1K, with color adjustments baked into the source image maps. Explicit tangents keep normal maps portable. Cycles world-position box texture coordinates become metre-scaled face UVs; original cladding UV orientation is retained. Shared foliage is decimated once, not per plant instance. Grass geometry nodes are not expanded into large duplicated meshes.

## Integration contract

Authoritative glTF nodes retain `extras.source_name`, `source_id`, `source_group`, `source_enabled`, `source_export_id` and `source_bounds_mm`. Source names match the existing interactive meshes exactly. They allow the original collision proxy and animation control to remain authoritative while the imported mesh provides the visible model. All exported coordinates are metres, glTF right-handed Y-up. Blender `[x,y,z]` becomes glTF `[x,z,-y]`; apply the same glTF loader root transform as the source GLBs when using the grass placements.

Use `appearanceHiddenSourceNames` to suppress original illustrative vegetation, replaced terrace chairs and artificial water-reflection overlays after their replacement assets are ready. `disabledSourceNames` contains source-disabled objects, foundations and services and is not a request to remove those from the interactive model. The broader `hiddenSourceNames` array is diagnostic only.

Grass placement JSON has a flat `placements` array with stride 5: `[x,y,z,yawRadians,uniformScale]`, rotation about glTF +Y. The first `mobileCount` rows form a spatially shuffled, deterministic mobile subset. Placements come from the actual saved Geometry Nodes distribution and its original upward-ray surface exclusion, with a second 10cm paved-edge clearance and a 12cm pool clearance. Heights are read from the actual source mesh; the script does not assume a terrain height.

Tree foliage keeps complete scanned leaf cards with deterministic thinning; woody geometry has a separate simplification budget. Collapsing an entire tree together would shrink disconnected leaves and damage the trunk.

The GLBs retain physical transmission and IOR. The web integration uses full-resolution alpha-blended thin glass and the original animated water material. The web renderer supplies its own lighting, environment reflections, shadowing and transparency tuning. Global illumination and Cycles caustics are not baked into these meshes. See [the environment export](ENVIRONMENT.md) for the saved Blender HDR sky.

## Living-room finishes

`lib/babylon-living-palette.ts` applies a matte sand/taupe sofa, natural oak cabinetry and tables, limestone, ecru and muted olive accents to `LIVING-103-` objects. The native collision model and imported GLBs use the same room-scoped finish resolver. Shared bedroom, hallway, bathroom and kitchen materials retain their original finish. Imported materials are cloned before batching; source GLBs and the saved Blender file remain the unmodified export.

The current sofa uses `TAILORED` source names and the native rounded-box upholstery builder for broad flat cushions with 25–55 mm edge radii. The earlier capsule-shaped exported pieces no longer match these sources and stay disabled; the new sofa remains visible in both ArchViz and fallback. Its original floor footprints and navigation guards are preserved.

The four `public/assets/textures/living-*-albedo.jpg` files retain the grain of the existing material maps. Reproduce them with `python3 scripts/archviz/web/prepare_living_palette.py`; the default output is `output/archviz/living-palette/`. Normal and roughness maps retain their original scale. The renderer additionally uses warmer surface reflectance to balance these finishes against the saved blue daylight inside the shaded living room.
