# Short lawn detail

This additive Unreal layer places four CC0 Poly Haven Bermuda prototypes on
the canonical `DOM_00001` lawn. Heights are approximately 26–63 mm after scale.
The species, density and optical transmission are design choices; they are not
an as-built survey of the Březí vegetation.

`placement.py` reads the actual source OBJ triangles and exclusions. It also
excludes the nine source gravel, stepping-stone and mulch objects by their
projected geometry. A disk enclosing every transformed prototype vertex must
stay at least 1 mm inside the lawn and outside hardscape. The current seed
produces 33,769 tufts in four HISM components. Base geometry and walking
collision remain authoritative.

```sh
python3 -B scripts/unreal/lawn-detail/placement.py prepare
python3 -I -B -m unittest discover -s scripts/unreal/lawn-detail -p 'test_*.py'
node --test scripts/unreal/lawn-detail/package-gate.test.mjs
```

Preparation writes `output/unreal/lawn-detail/placement.json` and its pinned
`reference.json`. Import verifies those inputs before replacing the map;
it does not silently regenerate placements. `native_layer.py` runs after the
existing saved material passes and contributes its assets and inputs to the
final package closure. Assets live under `/Game/Brezi/LawnDetail/R_<recipe>`.

The masked foliage material uses original UV0 and four 1K maps, one OpenGL
normal green-channel conversion, .45 alpha cutoff and per-instance distance
fade from 6 to 12 m. These texture dimensions are separate from the required
native 3840 × 2160 render. Grass has no collision, navigation or tick, and does
not alter any canonical source actor. Shadow and ray-tracing participation
remain enabled.

Native source triangles, UV0, every instance transform, bounds and saved
material graph are checked. Numeric native normals/tangents and internal HISM
tree bytes are outside the reflected readback scope. Rendered foliage, fade,
shadows and frame time require a packaged Metal run; successful import alone
does not establish photorealism or smooth performance.
