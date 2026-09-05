# Saved Blender sky for Babylon

`sky.hdr` and `sky.jpg` are 2048 × 1024 world-only equirectangular renders of the original `dom-archviz.blend` physical MULTIPLE_SCATTERING sky at 16 samples. No geometry or light objects were rendered. The source file was not saved or modified.

The HDR stores linear radiance with the original 0.23 world strength already applied. Its decoded RGB range is 0.00977 to 9.9375, verified with the repository's actual Babylon RGBE reader and cubemap converter. The JPG applies the original AgX Medium High Contrast view transform at 0 EV.

Native mapping is right-handed `[BlenderX, BlenderZ, -BlenderY]`. Set HDR rotationY to 0. Panorama u=.5 points toward +X, u=.75 toward +Z, u=.25 toward -Z, and the top toward +Y. An independent marker panorama verified this mapping.

The directional light ray direction is:

```ts
new Vector3(0.7560315132, -0.4734486639, 0.4519543052)
```

Source sun color is `(1, 0.93, 0.83)`, source sun energy is 3.5, and angular diameter is 0.545 degrees. The world sky's sun disc is disabled in the original source, so retain one separate shadow-casting directional light. Its date is 2026-09-04 16:30 +02:00.

Start `scene.environmentIntensity=1`, HDR gammaSpace=false, prefilter enabled, image-processing exposure=1. The source world strength is already in the file; do not multiply by 0.23 a second time. Direct light intensity 3.5 matches the numeric source value but renderer response still needs a visual check. Prefer the same linear HDR as a skybox so the scene applies tone mapping once.

For the JPG PhotoDome fallback, use `useDirectMapping:false`, `faceForward:false`, rotationY=0, and override `photoTexture.coordinatesMode=Texture.FIXED_EQUIRECTANGULAR_MODE`. PhotoDome's default reflected mapping is mirrored; the override matches this canonical panorama. The JPG already has AgX applied; disable extra tone mapping and use exposure=1/contrast=1 for its background material.

The separate portable `export_environment.py` belongs in `scripts/archviz/web/`. It takes the same `--root`, `--source` and `--output` arguments as the geometry scripts, plus `--width` (default 2048) and `--samples` (default 16).
