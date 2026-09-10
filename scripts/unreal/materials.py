"""Bounded native PBR authoring for the already measured Brezi mesh assets.

Call apply_materials(scene_manifest, mesh_assets_by_id, output_dir) from the
existing import commandlet. No editor is launched here. Generated materials and
texture assets are owned exclusively below /Game/Brezi/MaterialsGenerated.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
CONTENT = "/Game/Brezi/MaterialsGenerated"
OWNER = "scripts/unreal/materials.py"
FUNCTION_ROOT = "/Engine/Functions/Engine_MaterialFunctions01/Texturing/"

# Project-owned inputs have no external download lock. Pin the audited bytes;
# recording an arbitrary current digest alone would not detect source drift.
PROJECT_SHA256 = {
    "public/assets/textures/lawn-albedo.jpg": "ef8a70c1a75189aa7610254128214a8a3cc208b96c86b3230ae08554360748c7",
    "public/assets/textures/lawn-normal.jpg": "39667d0adef19c7a099807a04ccfdaa580140a4f657a4af5b09d7659e915bbb3",
    "public/assets/textures/vinyl-oak-albedo.jpg": "7fe3d22bfb166239fbb758fd845bd8bd667e5a33075320441667c8c538ba4254",
    "public/assets/textures/vinyl-oak-normal.jpg": "ed2d81cfbb350d2ef581daa6fad97f356b1a9f640b1266ce22a3fef1d34464ee",
    "public/assets/textures/oak-veneer-albedo.jpg": "6638c505a9cbc8f6d55eafb04044bf129e020db5c7f3049779ddbd6ecdc22a9a",
    "public/assets/textures/oak-veneer-normal.jpg": "9b052b993e0d54780092b153597b72f09c3b3c05f8cc3420942e3beae1fc26ae",
    "public/assets/textures/boucle-taupe-albedo.jpg": "3e44df64378075b07b7308cda9b6cde1c31faa95f95a8a673fbfdd35cb3cf4f9",
    "public/assets/textures/boucle-taupe-normal.jpg": "330091afdd0a396040098f7b81f3200eabfa3c26e97b90b79e1d371854b33379",
    "public/assets/textures/rug-wool-taupe-albedo.jpg": "01e6d951ea580768d2c07e3988f3f8538f453c240dfe88b4cf50205608ca4dc3",
    "public/assets/textures/rug-wool-taupe-normal.jpg": "cc1725cd1bdc07caf776af8cef446115c5a5f9a0b225622fd4e61597c679d89a",
    "public/assets/textures/living-boucle-ecru-albedo.jpg": "b62ea6969ab726b9cf86ddf119ea312f15d04425245d9a5a089dc0ef27017408",
    "public/assets/textures/living-wool-sand-albedo.jpg": "2de75244e7d43729e5d6754742f4fdda25d6edc8ce03e7824c2adb14e85b4ea4",
    "public/assets/textures/living-natural-oak-albedo.jpg": "3a4b4434352fddb00bc338cf55128ea3c9f33d2fb98384bf2d3471575636bd52",
    "public/assets/textures/living-warm-stone-albedo.jpg": "eabe7b05be4ea951fa865caffe04a10e5f379245d29502bec3a5fbf797c80d9e",
    "public/assets/textures/stone-dark-normal.jpg": "2b132bf3cc6175f40a2906871600b4f812740c196f4952f7912b7fe8d00762a0",
    "public/assets/textures/metal-anthracite-normal.jpg": "db78996dc2e382a7ebdb1ad2ba967214e39501632e70b5b451b61449289cf470",
    "public/assets/textures/metal-anthracite-albedo.jpg": "2e0ab54ee5844543cbc704b719e6cdb25f7dbe596da6d767ac77b61b0c5ce57a",
    "public/assets/textures/gravel-albedo.jpg": "04fdf84a8cb33176c7bd5b1d3cd8047a75264d9775be0e4666beef7c7d380ae2",
    "public/assets/textures/gravel-normal.jpg": "15f15ad7d67c1a20c99106f93ab28ae7530f59f0c759421bcce8aa135f4317fc",
    "public/assets/textures/epoxy-grey-albedo.jpg": "47f67d2ab09e12ca49b77358b58ef8cbe211223f826c5e6e8a586f435af49286",
    "public/assets/textures/epoxy-grey-normal.jpg": "6e730eccf950637bd0c84b0ac20b640cc3eee051506c851ce0a11397f7c97d2b",
    "public/assets/textures/tile-porcelain-albedo.jpg": "2ab771f05ea77676574c3451f1f2549eb4e5b16d0d5f0c15bb6f1528ab790937",
    "public/assets/textures/tile-porcelain-normal.jpg": "311bf7517fca223409cdbc4fa01f19735b1b54b34a72b53d5d8a3d1f15dc8bc6",
    "public/assets/textures/stone-dark-albedo.jpg": "4b588edc9dac51f8b6430a428195b0d0d30ba782e4e3740406c3aca83a4172e8",
    "public/assets/textures/tile-wall-albedo.jpg": "449aa731d5e0c2872a4b70d868c99af4e3352eee32eae37915aaad5d8b93b0a1",
    "public/assets/textures/tile-wall-normal.jpg": "c977a6771ca9f25ff44cb42f0827959a97db53fae32924afa8fdf4ec48a61444",
    "public/assets/textures/child-woodland-albedo.png": "771f0e4e356f6b1d3cbef082ea01c916bc470341cb5321335e02e5449d5dfb8f",
    "public/assets/textures/child-garden-albedo.png": "284b5cbbbccf936ab0fbdc3ea5da3ea619938b652435905d6d430c3de1eb5b0e",
    "public/assets/vegetation/ornamental-grass-card.png": "0f603d68be529b3adcb37815704822abe8c68de5adadfb045732ecebaeb5daec",
    "public/assets/vegetation/perennial-cluster-card.png": "09c5b97195f823daa9cf9c4a36c6471e2e4c43804621532f66fd54fa60b9dbde",
}
LOCAL_NORMALS = {
    "vinyl-oak-albedo": "vinyl-oak-normal",
    "oak-veneer-albedo": "oak-veneer-normal",
    "boucle-taupe-albedo": "boucle-taupe-normal",
    "rug-wool-taupe-albedo": "rug-wool-taupe-normal",
    "living-boucle-ecru-albedo": "boucle-taupe-normal",
    "living-wool-sand-albedo": "rug-wool-taupe-normal",
    "living-natural-oak-albedo": "oak-veneer-normal",
    "living-warm-stone-albedo": "stone-dark-normal",
}
# Explicit white-source omissions from the first Metal render. The first value
# must match the recorded source texture; never infer a surface from white RGB.
STATIC_SURFACES = {
    "real-road-reserve": ("gravel-albedo.jpg", "gravel-normal.jpg", 0.9, 0.5),
    "kačírek · južná fasáda · pbr": ("gravel-albedo.jpg", "gravel-normal.jpg", 0.9, 0.5),
    "kačírek · východná fasáda · pbr": ("gravel-albedo.jpg", "gravel-normal.jpg", 0.9, 0.5),
    "kačírek · severný štít · pbr": ("gravel-albedo.jpg", "gravel-normal.jpg", 0.9, 0.5),
    "real-interior-epoxy": ("epoxy-grey-albedo.jpg", "epoxy-grey-normal.jpg", None, 0.2),
    "real-interior-tile": ("tile-porcelain-albedo.jpg", "tile-porcelain-normal.jpg", None, 0.45),
    "real-interior-worktop": ("stone-dark-albedo.jpg", "stone-dark-normal.jpg", None, 0.3),
    "real-interior-wall-tile": ("tile-wall-albedo.jpg", "tile-wall-normal.jpg", None, 0.4),
    "c-boy-109-print-art": ("child-woodland-albedo.png", None, None, 0),
    "c-girl-108-print-art": ("child-garden-albedo.png", None, None, 0),
}
PV_GRID_HLSL = r"""
// Native equivalent of photovoltaic-cell-grid in lib/babylon-scene.ts.
// The source canvas uses sRGB colors. Convert the completed color to linear.
float2 pixel = frac(UV) * float2(1024.0, 640.0);
float2 cellSize = float2(1024.0 / 10.0, 640.0 / 6.0);
float2 cell = floor(pixel / cellSize);
float2 p = pixel - cell * cellSize;
float2 edge = min(p - 7.0, cellSize - 7.0 - p);
float distanceToEdge = min(edge.x, edge.y);
float aa = max(fwidth(distanceToEdge), 0.75);
float coverage = saturate(0.5 + distanceToEdge / aa);
// Authored sRGB #121c25 cell; not a measured product color.
float3 fill = float3(18,28,37) / 255.0;
float3 color = lerp(float3(7,20,31) / 255.0, fill, coverage);
float busDistance = min(abs(pixel.x - 1024.0 / 3.0), abs(pixel.x - 2048.0 / 3.0));
float bus = saturate(0.5 + (1.5 - busDistance) / max(fwidth(pixel.x), 0.75));
color = lerp(color, float3(224,235,238) / 255.0, bus * 0.55);
float3 low = color / 12.92;
float3 high = pow((color + 0.055) / 1.055, 2.4);
return lerp(low, high, step(0.04045, color));
"""

# The source builder explicitly calls these cylinders "four ring marks".
# IDs and dimensions are checked before any native graph/asset is authored.
COOKTOP_IDS = frozenset({"DOM_00667", "DOM_00668", "DOM_00669", "DOM_00670"})
COOKTOP_RING_HLSL = r"""
float distanceToRing = abs(length(Position.xy - Center.xy) - RadiusCm);
float aa = max(fwidth(distanceToRing), 0.001);
return saturate(0.5 + (HalfWidthCm - distanceToRing) / aa);
"""
WOOD_GRAIN = {
    # Axis follows existing texturedBox UV: floor planks along U; vertical
    # cabinet face height along V. No source albedo/UV rotation is introduced.
    "real-interior-vinyl-oak": ("vinyl-oak-albedo", "U", 0.35),
    "real-interior-kitchen-front": ("oak-veneer-albedo", "V", 0.30),
    "real-hallway-wardrobe-smoked-oak": ("oak-veneer-albedo", "V", 0.42),
    "real-hallway-wardrobe-warm-oak": ("oak-veneer-albedo", "V", 0.38),
    "living warm cabinet | real-interior-living-cabinet": ("living-natural-oak-albedo", "V", 0.35),
    "living warm oak | real-interior-kitchen-front": ("living-natural-oak-albedo", "V", 0.35),
}
WOOD_GRAIN_HLSL = r"""
// Authored pore-scale finish, not a scan or measured wood product. Coordinates
// inherit source UV0. Derivative filtering fades unresolved grain at distance.
float along = lerp(UV.y, UV.x, AxisU);
float across = lerp(UV.x, UV.y, AxisU);
float bend = 0.0012 * sin(along * 17.0) + 0.0005 * sin(along * 43.0);
float p = (across + bend) * 180.0;
float q = (across + bend * 0.63) * 317.0 + along * 0.41;
float fp = 1.0 - smoothstep(0.2, 0.5, fwidth(p));
float fq = 1.0 - smoothstep(0.2, 0.5, fwidth(q));
float pores = 0.6 * sin(p * 6.2831853) * fp + 0.4 * sin(q * 6.2831853) * fq;
float slope = NormalSlope * (0.6 * cos(p * 6.2831853) * fp + 0.4 * cos(q * 6.2831853) * fq);
float2 detail = lerp(float2(slope, 0), float2(0, slope), AxisU);
float3 normal = normalize(lerp(float3(0,0,1), SourceNormal, SourceStrength) + float3(detail,0));
return float4(normal, clamp(BaseRoughness + RoughnessVariation * pores, 0.04, 0.96));
"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def linear(value):
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


# Only this existing parcel surface receives the omitted lawn maps. The export
# preserved raw UV0 and the texture filename, but not Babylon's texture matrix.
# Bind the reconstruction to the exact exported builder/serializer bytes;
# source edits require reviewed pins, never silently guessed UV defaults.
LAWN_SOURCE_FILES = {
    "lib/babylon-scene.ts": "39b12a2396c5eef49db12af59dffdb365c25d629cd566b5f905de3d8328df678",
    "scripts/archviz/scene-export.ts": "7dbd423eb9de58a2343a86393dbc2f01f127fb82eccee76e8a7e3a459c423de6",
    "scripts/archviz/geometry.mjs": "7314811e22410a13e4274dcc8be98e8e78234372d6a97c3572468ce37df53839",
    "package-lock.json": "ed1898d285bb6361d6a3a079c1253ba7e2761b3d4785622d8d5065e87bbeafd4",
}
LAWN_ID, LAWN_SLOT = "DOM_00001", "MAT_0001"
LAWN_ASSET = "/Game/Brezi/Geometry/brezi-twin/StaticMeshes/DOM_00001.DOM_00001"


def parcel_lawn_recipe(scene):
    source = scene["materials"].get(LAWN_SLOT)
    expected = {"name": "real-grass", "color": [198 / 255, 210 / 255, 188 / 255],
                "roughness": 0.95, "metallic": 0, "alpha": 1,
                "texture": "/assets/textures/lawn-albedo.jpg", "emission": [0, 0, 0]}
    if source != expected:
        raise RuntimeError("Parcel lawn source material changed")
    matches = [r for r in scene["objects"] if LAWN_SLOT in r.get("materialSlots", [])]
    if len(matches) != 1 or matches[0].get("id") != LAWN_ID:
        raise RuntimeError("Parcel lawn must bind exactly DOM_00001/MAT_0001")
    record = matches[0]
    if (record.get("name") != "Parcela 6012/26 · 753 m²" or record.get("sourceId") != record["name"]
            or record.get("materialSlots") != [LAWN_SLOT] or record.get("materialNames") != ["real-grass"]
            or record.get("instances") != 1 or record.get("triangles") != 27 or record.get("enabled") is not True
            or record.get("metadata", {}).get("walkSurfaceId") != "parcel-6012-26"
            or record.get("boundsMm") != {"min": [-16146, -10800, -65], "max": [15987, 13697.000000000002, -65]}):
        raise RuntimeError("Parcel lawn source object/bounds/UV domain changed")
    text = {}
    for path, expected_sha in LAWN_SOURCE_FILES.items():
        file = ROOT / path
        if (scene.get("sourceFiles", {}).get(path) != expected_sha or not file.is_file()
                or file.resolve() != file or sha(file) != expected_sha):
            raise RuntimeError("Parcel lawn exported source binding changed: " + path)
        text[path] = file.read_text()
    builder = text["lib/babylon-scene.ts"]
    semantics = (
        'this.applyTexture(this.realisticMaterials.grass, "lawn-albedo", 12, 10, "lawn-normal", 0.4);',
        'this.realisticMaterials.grass.albedoColor = Color3.FromHexString("#c6d2bc");',
        'albedo.uScale = uScale;', 'albedo.vScale = vScale;',
        'bump.uScale = uScale;', 'bump.vScale = vScale;', 'bump.level = bumpLevel;',
    )
    polygon = builder.split("export function createFlatPolygonWithHoles(", 1)[-1].split("const triangulated = earcut", 1)[0]
    if (any(builder.count(s) != 1 for s in semantics)
            or polygon.count('(point.x - minX) / Math.max(1, maxX - minX),') != 1
            or polygon.count('(point.y - minY) / Math.max(1, maxY - minY),') != 1
            or 'uvs: Array.from(mesh.getVerticesData(VertexBuffer.UVKind) ?? [])' not in text["scripts/archviz/scene-export.ts"]
            or 'fmt(mesh.uvs[i])' not in text["scripts/archviz/geometry.mjs"]):
        raise RuntimeError("Parcel lawn UV reconstruction no longer matches exported source semantics")
    maps = {role: "public/assets/textures/lawn-" + role + ".jpg" for role in ("albedo", "normal")}
    for path in maps.values():
        file = ROOT / path
        if not file.is_file() or file.resolve() != file or sha(file) != PROJECT_SHA256[path]:
            raise RuntimeError("Parcel lawn texture missing, unavailable or changed: " + path)
    return {"kind": "project-uv", "maps": maps, "normalStrength": 0.4,
            "roughness": source["roughness"], "metallic": source["metallic"], "color": source["color"],
            "reconstructedUvScale": [12, 10],
            "provenance": "Existing project procedural lawn maps; source-bound restoration, not a photographed/measured lawn",
            "sourceBinding": {"objectId": LAWN_ID, "slot": LAWN_SLOT, "sourceFiles": dict(LAWN_SOURCE_FILES),
                "mapSha256": {p: PROJECT_SHA256[p] for p in maps.values()},
                "uv0ExportedWithoutTextureMatrix": True, "textureTransformReconstructed": True,
                "uvScale": [12, 10], "uvOffset": [0, 0], "uvRotationRadians": 0,
                "sourceNormalLevel": 0.4, "nativeGeometryUvValuesCompared": False,
                "geometryChanged": False, "collisionChanged": False, "otherSourceSurfacesChangedByRecipe": False}}


ROOF_SLOT = "MAT_0087"
ROOF_SOURCE = {'name': 'real-roof', 'color': [1, 1, 1], 'roughness': 0.52, 'metallic': 0.18, 'alpha': 1, 'texture': '/assets/textures/metal-anthracite-albedo.jpg', 'emission': [0, 0, 0]}
ROOF_RECORD_HASHES = {'DOM_01483': 'f9098fce8ffc6a0487a7b97f6ba9c44ee65f53a83898235d5ae28d91f922307a', 'DOM_01484': '4b68f19b2c9088a0fea08307769188239dc937fcc34ecd9396173c5a99986cc5', 'DOM_01485': 'a73465ae20e803b9ff90e40d6b370b3734af46a164c5c98a894ac7df67ad6b19', 'DOM_01486': 'be9d016faf518aeab781e2639922d8be501898e6b23e8796cb83239d337839ef'}


def roof_source_binding(scene):
    """Only the four existing source roof faces; no inferred roof/edge selector."""
    if scene["materials"].get(ROOF_SLOT) != ROOF_SOURCE:
        raise RuntimeError("Roof source material changed")
    rows = [r for r in scene["objects"] if ROOF_SLOT in r["materialSlots"]]
    hashes = {r["id"]: hashlib.sha256(json.dumps(r, ensure_ascii=False, sort_keys=True,
              separators=(",", ":")).encode()).hexdigest() for r in rows}
    if len(rows) != 4 or hashes != ROOF_RECORD_HASHES:
        raise RuntimeError("Roof exact four-source scope changed")
    return {"sourceSlot": ROOF_SLOT, "sourceRecordHashes": hashes,
            "sourceTriangles": 8, "sourceGeometryOrUvAuthored": False,
            "sharedRoofEdgeSlotChanged": False}


def select_recipe(source, lock):
    """Explicit source-name rules; preserve every unhandled imported material."""
    name = source["name"]
    low = name.lower()
    if low == "real-roof":
        if source != ROOF_SOURCE:
            raise RuntimeError("Roof source material changed")
        return {"kind": "roof-coated-scalar", "maps": {}, "normalStrength": 0,
                "roughness": source["roughness"], "metallic": 0,
                "color": [linear(c / 255) for c in (56, 62, 66)],
                "provenance": "Existing RAL 7016 screen approximation; not a measured coating sample",
                "nativeDesignOverride": {"id": "NATIVE-ROOF-COATED-RAL7016-1",
                    "reason": "Smooth opaque pigmented coating on existing standing-seam roof faces; remove authored 15cm albedo/normal noise",
                    "sourceMaterial": source["name"], "sourceTexture": source["texture"],
                    "sourceMetallic": source["metallic"], "sourceRoughnessRetained": True,
                    "nativeFinish": "RAL7016 pigmented dielectric approximation",
                    "colorReusesExistingFrameApproximation": True, "measuredBrdf": False,
                    "geometryChanged": False, "uvChanged": False, "sharedEdgeSlotChanged": False}}
    if low == "real-solar":
        if source.get("texture") != "photovoltaic-cell-grid":
            raise RuntimeError("PV source DynamicTexture identity changed")
        return {"kind": "pv-grid-uv", "maps": {}, "normalStrength": 0,
                "roughness": source["roughness"], "metallic": source["metallic"], "color": source["color"],
                "clearCoat": 0.9, "clearCoatRoughness": 0.07,
                "provenance": "Native procedural transfer of existing photovoltaic-cell-grid DynamicTexture",
                "sourceShaderFile": "lib/babylon-scene.ts", "sourceShaderSha256": sha(ROOT / "lib/babylon-scene.ts"),
                "shaderCodeSha256": hashlib.sha256(PV_GRID_HLSL.encode()).hexdigest(),
                "uv": "Source UV0; source canvas1024x640,10x6 cells,7px insets,no cell outlines,3px busbars; derivative antialiasing"}
    if low in STATIC_SURFACES:
        albedo, normal, tile, strength = STATIC_SURFACES[low]
        if source.get("texture") != "/assets/textures/" + albedo:
            raise RuntimeError("Static surface source texture changed: " + name)
        maps = {"albedo": "public/assets/textures/" + albedo}
        if normal:
            maps["normal"] = "public/assets/textures/" + normal
        return {"kind": "project-world" if tile else "project-uv", "maps": maps,
                "tileMetres": tile, "normalStrength": strength,
                "roughness": source["roughness"], "metallic": source["metallic"], "color": source["color"],
                "provenance": "Existing project texture, SHA-256 pinned; no scan or measured product claim",
                "uv": "world period: existing metal normal 0.15m / gravel strip 0.9m recipe; otherwise source UV0 unchanged",
                "surfaceNote": "Anthracite coated roof retains authored roughness/metallic; wood selectors unaffected" if low == "real-roof" else "Restore the named source surface, without blanket white recoloring"}
    asset = None
    if low in {"real-wall", "real-soffit", "real-interior-wall", "real-interior-plaster", "real-interior-ceiling"}:
        asset = "white_plaster_02"
    elif low in {"real-deck", "real-timber", "real-timber-dark"} or low.startswith(("real-larch-", "terr-")):
        asset = "hinoki_planks"
    elif low == "real-road":
        asset = "asphalt_02"  # Explicit native design revision; source remains recorded as pavers.
    elif low in {"real-paving", "real-paving-entry", "real-concrete"}:
        asset = "concrete_pavement"
    elif low == "archviz-asphalt":
        asset = "asphalt_02"
    if asset:
        spec = lock["assets"][asset]
        maps = {role: "output/archviz/assets/" + spec["maps"][kind]["path"]
                for role, kind in (("albedo", "diffuse"), ("normal", "normal"), ("roughness", "roughness"))}
        recipe = {"kind": "photo-world", "asset": asset, "maps": maps,
                "tileMetres": spec["tileSizeMetres"], "normalStrength": 0.2 if asset == "white_plaster_02" else 0.55,
                "provenance": "Poly Haven CC0-1.0; existing asset lock", "roughness": source["roughness"],
                "metallic": 0, "color": [1, 1, 1], "plasterMix": asset == "white_plaster_02"}
        if low == "real-road":
            recipe["nativeDesignOverride"] = {"id": "NATIVE-BRIEF-20260908-STREET-ASPHALT", "date": "2026-09-08",
                "reason": "Explicit current brief requests asphalt; source street geometry and historical paver record retained",
                "sourceMaterial": name, "sourceFinish": "GREY_CONCRETE_BLOCK_PAVERS",
                "historicalSourceId": "SRC-CLIENT-STREET-PHOTO-20260825", "nativeFinish": "ASPHALT"}
        return recipe
    if low in {"real-glass-frame", "real-glass-frame-wood", "real-fence-metal", "real-roof-edge"}:
        recipe = {"kind": "ral-world", "maps": {"normal": "public/assets/textures/metal-anthracite-normal.jpg"},
                "tileMetres": 0.15, "normalStrength": 0.08, "roughness": 0.34, "metallic": 0.08,
                "color": [linear(c / 255) for c in (56, 62, 66)],
                "provenance": "Project procedural normal; RAL 7016 screen approximation, not measured sample"}
        if low == "real-glass-frame-wood":
            recipe["nativeDesignOverride"] = {"id": "NATIVE-BRIEF-20260908-WINDOW-RAL7016", "date": "2026-09-08",
                "reason": "Explicit current brief requests anthracite window frames; only this frame slot changes",
                "sourceMaterial": name, "sourceColor": source["color"], "nativeFinish": "RAL 7016 coating approximation",
                "geometryChanged": False, "otherTimberChanged": False}
        return recipe
    texture = source.get("texture") or ""
    stem = Path(texture).stem
    if low in WOOD_GRAIN and texture != "/assets/textures/" + WOOD_GRAIN[low][0] + ".jpg":
        raise RuntimeError("Interior wood source texture changed: " + name)
    if texture.startswith("/assets/textures/") and stem in LOCAL_NORMALS:
        recipe = {"kind": "project-uv", "maps": {"albedo": "public" + texture,
                "normal": "public/assets/textures/" + LOCAL_NORMALS[stem] + ".jpg"},
                "normalStrength": 0.16 if low.startswith("living warm sofa") else 0.35,
                "roughness": source["roughness"], "metallic": source["metallic"], "color": source["color"],
                "provenance": "Existing project procedural map; warm variants derive from the same generator",
                "uv": "source UV0 unchanged; no invented measured weave size"}
        if low in WOOD_GRAIN:
            expected, axis, strength = WOOD_GRAIN[low]
            if stem != expected:
                raise RuntimeError("Interior wood source texture changed: " + name)
            recipe["normalStrength"] = strength
            recipe["woodGrain"] = {"axis": axis, "cyclesPerSourceUV": [180, 317],
                "normalSlope": 0.018, "roughnessVariation": 0.018,
                "provenance": "Restrained procedural finish approximation over existing source maps; not measured pores or a photographed oak scan",
                "scale": "Inherits per-face source UV0 tile scale; no universal physical pore period is asserted",
                "orientation": "U follows authored floor plank length; V follows cabinet face height. Other faces inherit the existing per-face UV chart.",
                "shaderCodeSha256": hashlib.sha256(WOOD_GRAIN_HLSL.encode()).hexdigest()}
        return recipe
    cards = {"real-plant-grass": "/assets/vegetation/ornamental-grass-card.png",
             "real-plant-perennial": "/assets/vegetation/perennial-cluster-card.png"}
    if low in cards:
        if texture != cards[low]:
            raise RuntimeError("Foliage source texture changed: " + name)
        return {"kind": "masked-uv", "maps": {"albedo": "public" + texture}, "alphaCutoff": 0.28,
                "roughness": source["roughness"], "metallic": 0, "color": source["color"],
                "provenance": "Existing imagegen prototype PNG, not a photographed botanical source",
                "uv": "source UV0 unchanged; embedded PNG alpha; two-sided"}
    return None


def cooktop_recipe(record, slot, source):
    """Return the sole object-scoped override; fail if a pinned source drifts."""
    if record["id"] not in COOKTOP_IDS:
        return None
    if (record.get("name") != "KITCHEN-RUN · varná zóna"
            or record.get("sourceId") != "KITCHEN-RUN · varná zóna"
            or slot != "MAT_0041" or source["name"] != "real-interior-steel"
            or record.get("materialSlots") != [slot]
            or record.get("triangles") != 128):
        raise RuntimeError("Cooktop ring source identity changed: " + record["id"])
    bounds = record["boundsMm"]
    size = [hi - lo for lo, hi in zip(bounds["min"], bounds["max"])]
    if len(size) != 3 or any(abs(actual - expected) > 0.01 for actual, expected in zip(size, (200, 200, 2))):
        raise RuntimeError("Cooktop ring cylinder dimensions changed: " + record["id"])
    return {"kind": "cooktop-ring-mask", "maps": {}, "normalStrength": 0,
            "alphaCutoff": 0.5, "twoSided": False, "radiusCm": 9.8, "halfWidthCm": 0.1,
            "roughness": 0.45, "metallic": 0, "color": [linear(c / 255) for c in (115, 120, 124)],
            "shaderCodeSha256": hashlib.sha256(COOKTOP_RING_HLSL.encode()).hexdigest(),
            "provenance": "Source builder labels these four cylinders ring marks; 2mm printed ring is an authored visual interpretation, not a measured appliance",
            "nativeDesignOverride": {"id": "NATIVE-COOKTOP-FOUR-RING-MARKS", "objectIds": sorted(COOKTOP_IDS),
                "sourceMaterial": source["name"], "geometryChanged": False,
                "reason": "Mask the solid source cylinders to ring marks described by the source builder; preserve shared hood steel"}}


def _write_report(path, report, status):
    report["status"] = status
    report["generatedAt"] = datetime.now(timezone.utc).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def _asset_hashes(object_paths):
    """Hash saved packages, including split bulk payloads when present."""
    content_dir = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()))
    hashes = {}
    for object_path in sorted(set(object_paths)):
        package = object_path.split(".", 1)[0]
        if not package.startswith("/Game/Brezi/"):
            raise RuntimeError("Unexpected package in native material receipt: " + package)
        base = content_dir / package[len("/Game/"):]
        main = base.with_suffix(".uasset")
        if not main.is_file():
            raise RuntimeError("Generated native asset was not saved to disk: " + str(main))
        for extension in (".uasset", ".uexp", ".ubulk"):
            file = base.with_suffix(extension)
            if file.is_file():
                hashes[str(file.relative_to(ROOT))] = sha(file)
    return hashes


def ensure_nanite_materials(mesh_assets_by_id):
    """Persist effective Nanite usage for every material of each Nanite mesh.

    Interchange creates MaterialInstanceConstant assets whose shared plugin
    parents may not declare Nanite usage. UE 5.8 supports a usage override on
    the imported instance itself; no shared Engine/Interchange parent is edited.
    This is independent of the optional photo-material pass.
    """
    lib = unreal.MaterialEditingLibrary
    usage = unreal.MaterialUsage.MATUSAGE_NANITE
    materials, bindings = {}, []
    mesh_count = 0
    for object_id, mesh in sorted(mesh_assets_by_id.items()):
        if not mesh.get_editor_property("nanite_settings").get_editor_property("enabled"):
            continue
        mesh_count += 1
        slots = mesh.get_editor_property("static_materials")
        if not slots:
            raise RuntimeError("Nanite mesh has no material slots: " + object_id)
        for index, slot in enumerate(slots):
            material = slot.get_editor_property("material_interface")
            if not material:
                raise RuntimeError("Nanite material slot would use Default Material: " + object_id + "/" + str(index))
            path = material.get_path_name()
            if not path.startswith((CONTENT + "/", "/Game/Brezi/Geometry/")):
                raise RuntimeError("Cannot author Nanite usage outside generated scene assets: " + path)
            materials[path] = material
            bindings.append({"objectId": object_id, "slotIndex": index,
                             "slotName": str(slot.get_editor_property("material_slot_name")), "material": path})
    entries = []
    for path, material in sorted(materials.items()):
        before = bool(lib.has_material_usage(material, usage))
        chain, current, seen = [], material, set()
        while isinstance(current, unreal.MaterialInstanceConstant):
            if current.get_path_name() in seen:
                raise RuntimeError("Cyclic material parent chain: " + path)
            seen.add(current.get_path_name())
            current = current.get_editor_property("parent")
            if not current:
                raise RuntimeError("Nanite material instance has no parent: " + path)
            chain.append(current.get_path_name())
        if not isinstance(current, unreal.Material):
            raise RuntimeError("Nanite material has an unsupported base material type: " + path)
        if isinstance(material, unreal.MaterialInstanceConstant):
            # This explicitly persists the instance's own effective flag. Merely
            # enabling the base parent misses existing instance usage overrides.
            modified = not before or not lib.has_material_usage_override(material, usage)
            if modified:
                lib.set_material_usage_override(material, usage, True, True)
                lib.update_material_instance(material)
            mode = "instance-usage-override"
            if not lib.has_material_usage_override(material, usage):
                raise RuntimeError("Nanite instance usage override was not set: " + path)
        elif isinstance(material, unreal.Material):
            modified = not before
            if modified:
                lib.set_base_material_usage(material, usage, True)
                errors = list(lib.recompile_material(material))
                if errors:
                    raise RuntimeError("Nanite base material compilation failed: " + path + ": " + "; ".join(str(e) for e in errors))
            mode = "base-material-usage"
        else:
            raise RuntimeError("Unsupported Nanite material interface: " + path)
        if not lib.has_material_usage(material, usage):
            raise RuntimeError("Nanite material usage is still disabled: " + path)
        if modified and not unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
            raise RuntimeError("Failed to persist Nanite material usage: " + path)
        entries.append({"asset": path, "type": material.get_class().get_name(),
                        "usageBefore": before, "usageAfter": True, "mode": mode,
                        "parentChain": chain, "sharedParentsModified": False,
                        "modified": modified, "saved": True})
    hashes = _asset_hashes(materials.keys())
    report = {"schemaVersion": 1, "status": "nanite-material-usage-saved", "writerSha256": sha(__file__),
              "naniteMeshes": mesh_count, "uniqueMaterials": len(entries), "materialSlots": len(bindings),
              "missingUsageBefore": sum(not entry["usageBefore"] for entry in entries),
              "materials": entries, "bindings": bindings, "assetHashes": hashes,
              "verification": {"effectiveUsageFlagsVerified": True, "nativeAssetsSaved": True,
                               "cookedMetalFallbacksVerified": False},
              "limitations": ["Saved usage flags require a new cook and rendered Metal log check; this commandlet does not prove shader availability at runtime."]}
    report["nativeUsageSha256"] = hashlib.sha256(json.dumps({"writer": report["writerSha256"],
        "bindings": bindings, "assets": hashes}, sort_keys=True).encode()).hexdigest()
    unreal.log("BREZI_NANITE_MATERIALS " + json.dumps({key: report[key] for key in
                ("status", "naniteMeshes", "uniqueMaterials", "materialSlots", "missingUsageBefore")}))
    return report


class MaterialWriter:
    def __init__(self, lock, report):
        self.lock, self.report = lock, report
        self.tools = unreal.AssetToolsHelpers.get_asset_tools()
        self.lib = unreal.MaterialEditingLibrary
        self.cache = {}
        self.photomaps = {"output/archviz/assets/" + value["path"]: value
                          for asset in lock["assets"].values() for value in asset["maps"].values()}

    def owned(self, asset):
        if not asset.get_path_name().startswith(CONTENT + "/"):
            raise RuntimeError("Material writer cannot modify outside its generated namespace")
        if unreal.EditorAssetLibrary.get_metadata_tag(asset, "BreziGeneratedBy") != OWNER:
            raise RuntimeError("Refusing to replace an unowned generated-path asset: " + asset.get_path_name())

    def tag(self, asset, **values):
        unreal.EditorAssetLibrary.set_metadata_tag(asset, "BreziGeneratedBy", OWNER)
        for key, value in values.items():
            unreal.EditorAssetLibrary.set_metadata_tag(asset, key, str(value))

    def save(self, asset):
        if not unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False):
            raise RuntimeError("Failed to save generated asset: " + asset.get_path_name())

    def texture(self, relative, role):
        key = (relative, role)
        if key in self.cache:
            return self.cache[key]
        path = ROOT / relative
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if relative in self.photomaps:
            expected = self.photomaps[relative]
            if hashlib.md5(data).hexdigest() != expected["md5"]:
                raise RuntimeError("Photo map does not match source asset lock: " + relative)
        elif PROJECT_SHA256.get(relative) != digest:
            raise RuntimeError("Project map SHA-256 differs from audited bytes: " + relative)
        name = "T_" + re.sub(r"[^A-Za-z0-9_]", "_", path.stem) + "_" + role
        package = CONTENT + "/Textures/" + name
        texture = unreal.EditorAssetLibrary.load_asset(package) if unreal.EditorAssetLibrary.does_asset_exist(package) else None
        if texture:
            self.owned(texture)
            if unreal.EditorAssetLibrary.get_metadata_tag(texture, "source_sha256") != digest:
                raise RuntimeError("Generated texture has different source bytes; explicit regeneration required: " + package)
        else:
            task = unreal.AssetImportTask()
            for prop, value in {"filename": str(path), "destination_path": CONTENT + "/Textures",
                                "destination_name": name, "automated": True, "save": False,
                                "replace_existing": False, "factory": unreal.TextureFactory()}.items():
                task.set_editor_property(prop, value)
            self.tools.import_asset_tasks([task])
            results = task.get_objects()
            if len(results) != 1 or not isinstance(results[0], unreal.Texture2D):
                raise RuntimeError("Expected one imported Texture2D: " + relative)
            texture = results[0]
            if not texture.get_path_name().startswith(CONTENT + "/"):
                raise RuntimeError("Texture importer ignored the generated destination")
            self.tag(texture, source_path=relative, source_sha256=digest)
        texture.set_editor_property("srgb", role == "albedo")
        compression = {"normal": unreal.TextureCompressionSettings.TC_NORMALMAP,
                       "roughness": unreal.TextureCompressionSettings.TC_MASKS}.get(role, unreal.TextureCompressionSettings.TC_DEFAULT)
        texture.set_editor_property("compression_settings", compression)
        if role == "normal":
            texture.set_editor_property("flip_green_channel", True)
        if relative in ("public/assets/textures/lawn-albedo.jpg", "public/assets/textures/lawn-normal.jpg"):
            texture.set_editor_property("address_x", unreal.TextureAddress.TA_WRAP)
            texture.set_editor_property("address_y", unreal.TextureAddress.TA_WRAP)
        self.save(texture)
        self.report["textures"].append({"path": relative, "sha256": digest, "asset": texture.get_path_name(),
                "role": role, "srgb": role == "albedo", "normalGreenFlipped": role == "normal"})
        self.cache[key] = texture
        return texture

    def node(self, material, cls, **properties):
        node = self.lib.create_material_expression(material, cls, -600, 0)
        if not node:
            raise RuntimeError("Cannot create material node " + cls.__name__)
        for key, value in properties.items():
            node.set_editor_property(key, value)
        return node

    def scalar(self, material, value):
        return self.node(material, unreal.MaterialExpressionConstant, r=float(value))

    def vector(self, material, values):
        return self.node(material, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(*values, 1))

    def connect(self, origin, output, dest, pin):
        if not self.lib.connect_material_expressions(origin, output, dest, pin):
            raise RuntimeError(f"Could not connect {origin.get_name()}.{output} -> {dest.get_name()}.{pin}")

    def property(self, node, output, prop):
        if not self.lib.connect_material_property(node, output, prop):
            raise RuntimeError("Could not connect material property " + str(prop))

    def sample(self, material, texture, role, tile=None, coordinates=None):
        sampler = {"normal": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
                   "roughness": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS}.get(role, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
        if tile is None:
            sample = self.node(material, unreal.MaterialExpressionTextureSample, texture=texture, sampler_type=sampler)
            if coordinates is not None:
                inputs = [str(pin) for pin in self.lib.get_material_expression_input_names(sample)]
                if inputs.count("UVs") != 1:
                    raise RuntimeError("Parcel lawn texture UVs pin missing: " + repr(inputs))
                self.connect(coordinates, "", sample, "UVs")
            return sample, "RGB"
        object_node = self.node(material, unreal.MaterialExpressionTextureObject, texture=texture, sampler_type=sampler)
        function_name = "WorldAlignedNormal" if role == "normal" else "WorldAlignedTexture"
        # Some engine functions are not indexed by the commandlet AssetRegistry.
        # Load the verified package/object path directly from installed content.
        function = unreal.load_object(None, FUNCTION_ROOT + function_name + "." + function_name)
        if not function:
            raise RuntimeError("Required built-in material function missing: " + function_name)
        call = self.node(material, unreal.MaterialExpressionMaterialFunctionCall)
        if not call.set_material_function(function):
            raise RuntimeError("Could not initialize material function: " + function_name)
        inputs = self.lib.get_material_expression_input_names(call)
        outputs = self.lib.get_material_expression_output_names(call)
        def pin_name(names, target):
            matches = [str(name) for name in names if re.sub(r"[^a-z]", "", str(name).lower()) == target]
            if len(matches) != 1:
                raise RuntimeError(f"{function_name}: missing/unresolved {target} pin; got {list(names)}")
            return matches[0]
        self.connect(object_node, "", call, pin_name(inputs, "textureobject"))
        self.connect(self.vector(material, [tile * 100] * 3), "", call, pin_name(inputs, "texturesize"))
        return call, pin_name(outputs, "xyztexture")

    def parcel_lawn_uv_proof(self, material, coordinates, samples):
        """Read actual native graph inputs; this is not a GPU/UV vertex proof."""
        for key, value in {"coordinate_index": 0, "u_tiling": 12, "v_tiling": 10,
                           "un_mirror_u": False, "un_mirror_v": False}.items():
            if coordinates.get_editor_property(key) != value:
                raise RuntimeError("Parcel lawn native UV coordinate differs: " + key)
        if set(samples) != {"albedo", "normal"}:
            raise RuntimeError("Parcel lawn sample scope differs")
        for role, (sample, _) in samples.items():
            names = [str(pin) for pin in self.lib.get_material_expression_input_names(sample)]
            origins = list(self.lib.get_inputs_for_material_expression(material, sample))
            if len(names) != len(origins) or names.count("UVs") != 1 or origins[names.index("UVs")] != coordinates:
                raise RuntimeError("Parcel lawn UV0 scale not connected to " + role)
            texture = sample.get_editor_property("texture")
            path = "public/assets/textures/lawn-" + role + ".jpg"
            self.owned(texture)
            if (unreal.EditorAssetLibrary.get_metadata_tag(texture, "source_path") != path
                    or unreal.EditorAssetLibrary.get_metadata_tag(texture, "source_sha256") != PROJECT_SHA256[path]
                    or texture.get_editor_property("srgb") != (role == "albedo")
                    or texture.get_editor_property("address_x") != unreal.TextureAddress.TA_WRAP
                    or texture.get_editor_property("address_y") != unreal.TextureAddress.TA_WRAP
                    or (role == "normal" and texture.get_editor_property("flip_green_channel") is not True)):
                raise RuntimeError("Parcel lawn native source texture/color-space/wrap policy differs: " + role)
        return {"coordinateIndex": 0, "uTiling": 12, "vTiling": 10, "bothSamplesShareCoordinates": True,
                "sourceTextureTagsVerified": True, "wrapXY": True, "albedoSrgb": True, "normalGreenFlipped": True,
                "nativeGraphGetterVerified": True, "nativeGeometryUvValuesCompared": False,
                "savedReloadVerified": False, "renderedVerified": False}

    def pv_grid(self, material):
        input_ = unreal.CustomInput()
        input_.set_editor_property("input_name", "UV")
        node = self.node(material, unreal.MaterialExpressionCustom, inputs=[input_], code=PV_GRID_HLSL,
                         output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3,
                         description="Source photovoltaic-cell-grid; UV0; analytic antialiasing")
        coordinates = self.node(material, unreal.MaterialExpressionTextureCoordinate, coordinate_index=0)
        self.connect(coordinates, "", node, "UV")
        return node

    def custom(self, material, code, inputs, output_type, description):
        custom_inputs = []
        for name in inputs:
            input_ = unreal.CustomInput()
            input_.set_editor_property("input_name", name)
            custom_inputs.append(input_)
        node = self.node(material, unreal.MaterialExpressionCustom, inputs=custom_inputs,
                         code=code, output_type=output_type, description=description)
        for name, (origin, output) in inputs.items():
            self.connect(origin, output, node, name)
        return node

    def cooktop_ring(self, material, recipe):
        return self.custom(material, COOKTOP_RING_HLSL, {
            "Position": (self.node(material, unreal.MaterialExpressionWorldPosition), ""),
            "Center": (self.node(material, unreal.MaterialExpressionObjectPositionWS), ""),
            "RadiusCm": (self.scalar(material, recipe["radiusCm"]), ""),
            "HalfWidthCm": (self.scalar(material, recipe["halfWidthCm"]), ""),
        }, unreal.CustomMaterialOutputType.CMOT_FLOAT1, "Four source cooktop ring marks; centimetre mask")

    def wood_detail(self, material, source_normal, recipe):
        detail = recipe["woodGrain"]
        return self.custom(material, WOOD_GRAIN_HLSL, {
            "UV": (self.node(material, unreal.MaterialExpressionTextureCoordinate, coordinate_index=0), ""),
            "SourceNormal": source_normal,
            "SourceStrength": (self.scalar(material, recipe["normalStrength"]), ""),
            "AxisU": (self.scalar(material, 1 if detail["axis"] == "U" else 0), ""),
            "NormalSlope": (self.scalar(material, detail["normalSlope"]), ""),
            "RoughnessVariation": (self.scalar(material, detail["roughnessVariation"]), ""),
            "BaseRoughness": (self.scalar(material, recipe["roughness"]), ""),
        }, unreal.CustomMaterialOutputType.CMOT_FLOAT4, "Subtle UV-aligned authored wood finish; filtered pores")

    def roof_scalar_proof(self, material, recipe):
        if (material.get_editor_property("blend_mode") != unreal.BlendMode.BLEND_OPAQUE
                or material.get_editor_property("shading_model") != unreal.MaterialShadingModel.MSM_DEFAULT_LIT
                or material.get_editor_property("two_sided")
                or material.get_editor_property("use_material_attributes")
                or not self.lib.has_material_usage(material, unreal.MaterialUsage.MATUSAGE_NANITE)):
            raise RuntimeError("Roof opaque coated/Nanite policy differs")
        nodes = list(self.lib.get_material_expressions(material));seen = []
        actual = {}
        for prop, key, cls in [("BASE_COLOR", "color", unreal.MaterialExpressionConstant3Vector),
                               ("ROUGHNESS", "roughness", unreal.MaterialExpressionConstant),
                               ("METALLIC", "metallic", unreal.MaterialExpressionConstant)]:
            pid = getattr(unreal.MaterialProperty, "MP_" + prop)
            node = self.lib.get_material_property_input_node(material, pid)
            if not isinstance(node, cls):raise RuntimeError("Roof scalar node differs: " + key)
            value = node.get_editor_property("constant" if key == "color" else "r")
            value = [float(getattr(value, k)) for k in ("r", "g", "b")] if key == "color" else float(value)
            values = value if isinstance(value, list) else [value]
            wanted = recipe[key] if isinstance(recipe[key], list) else [recipe[key]]
            if not all(abs(a-b) <= 1e-7 for a,b in zip(values,wanted)):raise RuntimeError("Roof scalar value differs: " + key)
            output = self.lib.get_material_property_input_node_output_name(material, pid)
            if isinstance(output, tuple) and len(output) == 2 and output[0] is True:output = output[1]
            if output != list(self.lib.get_material_expression_output_names(node))[0]:raise RuntimeError("Roof scalar output channel differs")
            if any(n is not None for n in self.lib.get_inputs_for_material_expression(material,node)):raise RuntimeError("Roof scalar input unexpectedly connected")
            seen.append(node);actual[key] = value
        if len(nodes) != 3 or len(set(seen)) != 3 or set(nodes) != set(seen):raise RuntimeError("Roof unexpected material expressions")
        for prop in ("NORMAL", "SPECULAR", "WORLD_POSITION_OFFSET", "OPACITY", "OPACITY_MASK", "EMISSIVE_COLOR"):
            if self.lib.get_material_property_input_node(material,getattr(unreal.MaterialProperty,"MP_"+prop)) is not None:raise RuntimeError("Roof unexpected connected output: " + prop)
        if not unreal.BreziRendererSettingsAudit.has_no_pixel_depth_offset_connection(material):raise RuntimeError("Roof unexpected PDO")
        return {"asset": material.get_path_name(), "nodeCount": 3, "textureSampleCount": 0,
                "actualScalarValues": actual, "nativeGraphReadbackVerified": True,
                "roughnessIsAuthoredNotMeasured": True, "measuredBrdf": False,
                "sourceUvNotSampled": True, "renderedVerified": False}

    def make(self, slot, source, recipe, variant=None):
        if recipe["kind"] == "roof-coated-scalar" and (slot != ROOF_SLOT or variant is not None):
            raise RuntimeError("Roof scalar graph escaped source slot")
        if variant is not None and not re.fullmatch(r"[A-Za-z0-9_]+", variant):
            raise RuntimeError("Unsafe native material variant name")
        name = "M_" + slot + ("_" + variant if variant else "")
        package = CONTENT + "/" + name
        material = unreal.EditorAssetLibrary.load_asset(package) if unreal.EditorAssetLibrary.does_asset_exist(package) else None
        if material:
            self.owned(material)
            if not isinstance(material, unreal.Material):
                raise RuntimeError("Generated material path has wrong type: " + package)
            # UE 5.8 DeleteAllMaterialExpressions mutates its live expression
            # array during iteration. A snapshot prevents retained old nodes.
            for expression in list(self.lib.get_material_expressions(material)):
                self.lib.delete_material_expression(material, expression)
            if list(self.lib.get_material_expressions(material)):
                raise RuntimeError("Generated material graph did not clear: " + package)
        else:
            material = self.tools.create_asset(name, CONTENT, unreal.Material, unreal.MaterialFactoryNew())
            if not material:
                raise RuntimeError("Cannot create generated material: " + package)
            self.tag(material)
        self.tag(material, source_material_slot=slot, source_material_name=source["name"], writer_sha256=sha(__file__))
        world = recipe["kind"].endswith("world")
        masked = recipe["kind"] in {"masked-uv", "cooktop-ring-mask"}
        material.set_editor_property("two_sided", recipe.get("twoSided", masked))
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED if masked else unreal.BlendMode.BLEND_OPAQUE)
        material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_CLEAR_COAT if recipe.get("clearCoat") else unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
        material.set_editor_property("use_material_attributes", recipe["kind"] == "pv-grid-uv")
        material.set_editor_property("tangent_space_normal", not world)
        self.lib.set_base_material_usage(material, unreal.MaterialUsage.MATUSAGE_NANITE, True)
        if masked:
            material.set_editor_property("opacity_mask_clip_value", recipe["alphaCutoff"])
        tile = recipe.get("tileMetres") if world else None
        coordinates = None
        if recipe.get("reconstructedUvScale") is not None:
            if slot != LAWN_SLOT or recipe["reconstructedUvScale"] != [12, 10] or world:
                raise RuntimeError("UV reconstruction is reserved for the pinned parcel lawn")
            coordinates = self.node(material, unreal.MaterialExpressionTextureCoordinate, coordinate_index=0,
                                    u_tiling=12, v_tiling=10, un_mirror_u=False, un_mirror_v=False)
        samples = {role: self.sample(material, self.texture(path, role), role, tile, coordinates)
                   for role, path in recipe["maps"].items()}
        if recipe["kind"] == "pv-grid-uv":
            # MP_CustomData0/1 are hidden from the Python enum in UE 5.8.
            # The native MakeMaterialAttributes expression exposes named coat
            # inputs, avoiding numeric enum casts or unreflected property writes.
            attributes = self.node(material, unreal.MaterialExpressionMakeMaterialAttributes)
            normalize = lambda value: re.sub(r"[^a-z0-9]", "", str(value).lower())
            pins = list(self.lib.get_material_expression_input_names(attributes))
            for wanted, value in {"BaseColor": self.pv_grid(material),
                                  "Metallic": self.scalar(material, recipe["metallic"]),
                                  "Roughness": self.scalar(material, recipe["roughness"]),
                                  "ClearCoat": self.scalar(material, recipe["clearCoat"]),
                                  "ClearCoatRoughness": self.scalar(material, recipe["clearCoatRoughness"])}.items():
                matches = [str(pin) for pin in pins if normalize(pin) == normalize(wanted)]
                if len(matches) != 1:
                    raise RuntimeError("Native PV attribute pin missing: " + wanted + " in " + repr(pins))
                self.connect(value, "", attributes, matches[0])
            self.property(attributes, "", unreal.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
        elif "albedo" in samples:
            color_node, color_pin = samples["albedo"]
            if recipe.get("plasterMix"):
                mix = self.node(material, unreal.MaterialExpressionLinearInterpolate, const_alpha=0.15)
                self.connect(self.vector(material, [0.82, 0.80, 0.75]), "", mix, "A")
                self.connect(color_node, color_pin, mix, "B")
                color_node, color_pin = mix, ""
            elif recipe["color"] != [1, 1, 1]:
                multiply = self.node(material, unreal.MaterialExpressionMultiply)
                self.connect(color_node, color_pin, multiply, "A")
                self.connect(self.vector(material, recipe["color"]), "", multiply, "B")
                color_node, color_pin = multiply, ""
            self.property(color_node, color_pin, unreal.MaterialProperty.MP_BASE_COLOR)
            if masked:
                self.property(samples["albedo"][0], "A", unreal.MaterialProperty.MP_OPACITY_MASK)
        else:
            self.property(self.vector(material, recipe["color"]), "", unreal.MaterialProperty.MP_BASE_COLOR)
        if recipe["kind"] == "cooktop-ring-mask":
            self.property(self.cooktop_ring(material, recipe), "", unreal.MaterialProperty.MP_OPACITY_MASK)
        if "roughness" in samples:
            channel = self.node(material, unreal.MaterialExpressionComponentMask, r=True, g=False, b=False, a=False)
            self.connect(*samples["roughness"], channel, "")
            self.property(channel, "", unreal.MaterialProperty.MP_ROUGHNESS)
        elif recipe["kind"] != "pv-grid-uv" and not recipe.get("woodGrain"):
            self.property(self.scalar(material, recipe["roughness"]), "", unreal.MaterialProperty.MP_ROUGHNESS)
        if recipe["kind"] != "pv-grid-uv":
            self.property(self.scalar(material, recipe["metallic"]), "", unreal.MaterialProperty.MP_METALLIC)
        if recipe.get("woodGrain"):
            detail = self.wood_detail(material, samples["normal"], recipe)
            normal = self.node(material, unreal.MaterialExpressionComponentMask, r=True, g=True, b=True, a=False)
            roughness = self.node(material, unreal.MaterialExpressionComponentMask, r=False, g=False, b=False, a=True)
            self.connect(detail, "", normal, "")
            self.connect(detail, "", roughness, "")
            self.property(normal, "", unreal.MaterialProperty.MP_NORMAL)
            self.property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
        elif "normal" in samples:
            flat = self.node(material, unreal.MaterialExpressionVertexNormalWS) if world else self.vector(material, [0, 0, 1])
            mix = self.node(material, unreal.MaterialExpressionLinearInterpolate, const_alpha=recipe["normalStrength"])
            self.connect(flat, "", mix, "A")
            self.connect(*samples["normal"], mix, "B")
            normal = self.node(material, unreal.MaterialExpressionNormalize)
            self.connect(mix, "", normal, "")
            self.property(normal, "", unreal.MaterialProperty.MP_NORMAL)
        errors = list(self.lib.recompile_material(material))
        if errors:
            raise RuntimeError("Native material compilation failed: " + source["name"] + ": " + "; ".join(str(e) for e in errors))
        self.save(material)
        if recipe["kind"] == "roof-coated-scalar":
            self.report["roofSurface"]["nativeGraph"] = self.roof_scalar_proof(material, recipe)
        if coordinates is not None:
            self.report["parcelLawn"]["nativeUvGraph"] = self.parcel_lawn_uv_proof(material, coordinates, samples)
        self.report["materials"].append({"sourceSlot": slot, "sourceName": source["name"], "variant": variant,
                "asset": material.get_path_name(), "recipe": recipe, "compileErrors": errors,
                "saved": True, "visualValidation": "pending rendered Metal session"})
        return material


def _resolve_slot(static_slot, record, sources):
    material = static_slot.get_editor_property("material_interface")
    tagged = unreal.EditorAssetLibrary.get_metadata_tag(material, "source_material_slot") if material else ""
    candidates = [str(static_slot.get_editor_property("material_slot_name")),
                  str(static_slot.get_editor_property("imported_material_slot_name")),
                  material.get_name() if material else "", str(tagged)]
    matches = {found for candidate in candidates for found in re.findall(r"MAT_\d+", candidate) if found in sources}
    if len(matches) != 1:
        raise RuntimeError("Cannot resolve native source material slot for " + record["id"] + ": " + repr(candidates))
    slot = next(iter(matches))
    if slot not in record["materialSlots"]:
        raise RuntimeError("Native material slot not present in source record: " + record["id"] + "/" + slot)
    return slot


def apply_materials(scene_manifest, mesh_assets_by_id, output_dir):
    """Author allowlisted materials, assign by source slot, and save a receipt.

    output_dir is the same output/unreal directory as import-report.json.
    Unhandled source materials remain the Interchange scalar originals.
    Any missing verified texture/API/slot or material compile/save failure raises.
    """
    report_path = Path(output_dir) / "materials-report.json"
    report = {"schemaVersion": 1, "status": "pending", "sourceLayout": scene_manifest["layoutId"],
              "writerSha256": sha(__file__), "assetLockSha256": sha(ROOT / "scripts/archviz/assets.lock.json"),
              "sourceMaterialsSha256": hashlib.sha256(json.dumps(scene_manifest["materials"], sort_keys=True).encode()).hexdigest(),
              "namespace": CONTENT, "textures": [], "materials": [], "assignments": [], "preservedSourceSlots": [],
              "untransferredTexturedSlots": [], "nativeDesignOverrides": [],
              "verification": {"nativeGraphsCompiled": False, "nativeAssetsSaved": False,
                               "renderedMetalVerified": False, "photorealismVerified": False},
              "limitations": [
                  "Commandlet graph compilation and asset saving do not prove rendered Metal appearance or 4K performance.",
                  "Glass and pool water belong to the separate optics writer; this receipt makes no optical or caustic validation claim.",
                  "Existing plant cards keep their authored PNG alpha; they are historical imagegen prototypes, not new photographed vegetation.",
                  "The existing procedural interior maps are not photographed fabric/product scans; source UV0 remains unchanged.",
                  "OpenGL normal green-channel conversion is configured; final normal orientation requires the rendered native fixture.",
                  "Foliage alpha is preserved, but calibrated leaf transmission and species-specific scattering remain pending.",
                  "Hinoki photo texture retains the existing 1.89m recipe; deck board geometry stays 145mm/8mm gaps and no measured patina is claimed.",
                  "Six interior wood finishes add restrained UV-aligned procedural pores; these are not measured grain, and their filtering/appearance needs rendered Metal review.",
                  "Only four pinned source cooktop cylinders become 2mm masked ring marks; geometry/collision are unchanged and the ring width is an authored interpretation.",
              ]}
    _write_report(report_path, report, "pending")
    try:
        lock = json.loads((ROOT / "scripts/archviz/assets.lock.json").read_text())
        writer = MaterialWriter(lock, report)
        records = {r["id"]: r for r in scene_manifest["objects"]}
        sources = scene_manifest["materials"]
        lawn_recipe = parcel_lawn_recipe(scene_manifest)
        report["roofSurface"] = {"sourceBinding": roof_source_binding(scene_manifest), "nativeGraph": None}
        generated = {}
        assignments = []
        # Resolve every native slot before creating or replacing a material.
        for id_, mesh in mesh_assets_by_id.items():
            record = records[id_]
            for index, static_slot in enumerate(mesh.get_editor_property("static_materials")):
                slot = _resolve_slot(static_slot, record, sources)
                assignments.append((id_, mesh, index, slot))
        roof_assignments = [(id_, index) for id_, _, index, slot in assignments if slot == ROOF_SLOT]
        if sorted(roof_assignments) != [(id_, 0) for id_ in sorted(ROOF_RECORD_HASHES)]:
            raise RuntimeError("Native roof binding is not exactly four source meshes/slot0/MAT_0087")
        lawn_assignments = [(id_, index) for id_, _, index, slot in assignments if slot == LAWN_SLOT]
        if lawn_assignments != [(LAWN_ID, 0)]:
            raise RuntimeError("Native parcel lawn binding is not exactly DOM_00001/slot0/MAT_0001")
        lawn_mesh = mesh_assets_by_id[LAWN_ID]
        # GetNumTexCoords is the reflected BlueprintPure getter. GetNumUVChannels
        # on UStaticMesh is not a UFUNCTION in this engine and is not Python API.
        native_lawn_triangles = lawn_mesh.get_num_triangles(0)
        native_lawn_uv_channels = lawn_mesh.get_num_tex_coords(0)
        if (lawn_mesh.get_path_name() != LAWN_ASSET
                or native_lawn_triangles <= 0 or native_lawn_uv_channels != 1):
            raise RuntimeError("Native parcel lawn mesh identity/topology/UV channel changed")
        report["parcelLawn"] = {"sourceBinding": lawn_recipe["sourceBinding"], "nativeUvGraph": None,
                               "objectId": LAWN_ID, "sourceSlot": LAWN_SLOT,
                               "nativeMeshReadback": {"asset": lawn_mesh.get_path_name(),
                                   "renderLod0Triangles": native_lawn_triangles, "renderLod0UvChannels": native_lawn_uv_channels,
                                   "sourceTriangleCount": 27, "sourceNativeTriangleEquivalenceClaimed": False,
                                   "expectedUvChannels": 1, "uvExpectation": "single raw UV0 array in canonical export",
                                   "nativeUvGetter": "UStaticMesh.GetNumTexCoords"}}
        # Resolve and validate object overrides before any material mutation.
        # Material slot MAT_0041 is also used by the hood, so it cannot identify
        # a cooktop on its own. Keep the override key separate from source slots.
        if not COOKTOP_IDS.issubset(records) or not COOKTOP_IDS.issubset(mesh_assets_by_id):
            raise RuntimeError("Expected all four source cooktop objects in the native scene")
        overrides = {}
        for id_, _, _, slot in assignments:
            recipe = cooktop_recipe(records[id_], slot, sources[slot])
            if recipe:
                overrides[(id_, slot)] = recipe
        if {id_ for id_, _ in overrides} != COOKTOP_IDS:
            raise RuntimeError("Native slots did not resolve all four source cooktop objects")
        used = {slot for _, _, _, slot in assignments}
        for slot in sorted(used):
            recipe = lawn_recipe if slot == LAWN_SLOT else select_recipe(sources[slot], lock)
            if recipe:
                generated[slot] = writer.make(slot, sources[slot], recipe)
                if recipe.get("nativeDesignOverride"):
                    report["nativeDesignOverrides"].append({"slot": slot, **recipe["nativeDesignOverride"]})
            else:
                report["preservedSourceSlots"].append({"slot": slot, "name": sources[slot]["name"]})
                if sources[slot].get("texture"):
                    report["untransferredTexturedSlots"].append({"slot": slot, "name": sources[slot]["name"],
                        "texture": sources[slot]["texture"], "reason": "No verified native recipe in this pass; scalar import remains"})
        ring_recipe = next(iter(overrides.values()))
        ring = writer.make("MAT_0041", sources["MAT_0041"], ring_recipe, variant="CooktopRing")
        report["nativeDesignOverrides"].append({"slot": "MAT_0041", **ring_recipe["nativeDesignOverride"]})
        report["objectScopedSourceRecords"] = [records[id_] for id_ in sorted(COOKTOP_IDS)]
        changed = {}
        for id_, mesh, index, slot in assignments:
            target = ring if (id_, slot) in overrides else generated.get(slot)
            if not target:
                continue
            mesh.set_material(index, target)
            if mesh.get_material(index) != target:
                raise RuntimeError("Material assignment did not persist in memory: " + id_)
            changed[mesh.get_path_name()] = mesh
            report["assignments"].append({"objectId": id_, "slotIndex": index, "sourceSlot": slot,
                                          "material": target.get_path_name(),
                                          "objectScopedOverride": (id_, slot) in overrides})
        for mesh in changed.values():
            if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
                raise RuntimeError("Failed to save mesh material assignments: " + mesh.get_path_name())
        report.update({"authoredMaterialCount": len(report["materials"]), "importedTextureCount": len(report["textures"]),
                       "assignedSlots": len(report["assignments"]), "updatedMeshes": len(changed)})
        report["generatedAssetHashes"] = _asset_hashes([entry["asset"] for entry in [*report["textures"], *report["materials"]]])
        report["assignedMeshHashes"] = _asset_hashes(changed.keys())
        report["nativeAuthoredSha256"] = hashlib.sha256(json.dumps({
            "writer": report["writerSha256"], "source": report["sourceMaterialsSha256"],
            "generated": report["generatedAssetHashes"], "meshes": report["assignedMeshHashes"],
        }, sort_keys=True).encode()).hexdigest()
        report["verification"].update(nativeGraphsCompiled=True, nativeAssetsSaved=True)
        _write_report(report_path, report, "materials-authored")
        unreal.log("BREZI_MATERIALS " + json.dumps({key: report[key] for key in
                    ("status", "authoredMaterialCount", "importedTextureCount", "assignedSlots", "updatedMeshes")}))
        return report
    except Exception as error:
        report["error"] = str(error)
        _write_report(report_path, report, "failed")
        raise
