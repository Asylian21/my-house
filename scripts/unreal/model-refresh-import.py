"""Import the current C/B/B source into a NEW isolated native project.

BREZI_GEOMETRY points to a freshly validated bridge directory. This bounded
geometry refresh deliberately has a separate receipt from the historical
photographic-material/optics pipeline, whose pinned object IDs are not reusable
after a model revision. BREZI_MODEL_MATERIALS_ONLY=1 updates only verified owned
material graphs in a prior successful refresh; it never reimports geometry.
"""
import hashlib
import json
import math
import os
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = "scripts/unreal/model-refresh-import.py"
GEOMETRY = Path(os.environ.get("BREZI_GEOMETRY", ROOT / "output/unreal/geometry")).resolve()
REPORT_PATH = GEOMETRY.parent / "model-refresh-import-report.json"
MATERIALS_PATH = "/Game/Brezi/ModelRefresh/Materials"
EXPECTED_DESIGN = {"variant": "C", "heatingLayout": "B", "livingLayout": "B"}
REPORT = {
    "schemaVersion": 1, "status": "pending", "map": "/Game/Brezi/Maps/Brezi",
    "scope": "current-source-model-refresh", "archiveImported": False,
    "verification": {"nativeGeometryMeasured": False, "savedReloaded": False,
                     "sourceMaterialBindingsVerified": False, "visualQualityVerified": False,
                     "native4KFrameRateMeasured": False, "historicalVisualPipelineAccepted": False},
    "limitations": [
        "Native bounds, collision triangles, material graphs and serialized bindings are measured; rendered appearance requires separate Metal review.",
        "Source albedo uses UV0 with source-derived kitchen rotation and stable exterior tiling. Per-object cloned texture offsets, detailed normals and historical photographic recipes remain outside this pass.",
        "PV and pavement use explicitly reported representative colors from their source procedural canvas; the full cell/block shaders are not reconstructed.",
        "Translucent materials preserve source alpha and PBR factors; optical calibration, dynamic water caustics and historical material acceptance are not claimed.",
        "Door authoring verifies source members, initial closed pose and movable query collision. Animation, user input and room traversal require separate native runtime checks.",
    ],
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_report(status):
    REPORT.update(status=status, generatedAt=datetime.now(timezone.utc).isoformat())
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = REPORT_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(REPORT, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(REPORT_PATH)


def validate_current_source(scene, records):
    require(scene.get("activeDesign") == EXPECTED_DESIGN,
            "Refresh requires an explicitly exported activeDesign C/B/B")
    require(scene.get("layoutId", "").startswith("C-"), "Refresh source is not layout C")
    require(records and all(record.get("enabled") is True for record in records.values()),
            "Runtime source includes disabled/archived objects")
    placement = scene.get("house", {}).get("placement", {})
    require(placement.get("streetSetbackMm") == 3000 and placement.get("eastSetbackMm") == 3000,
            "Source does not preserve the requested 3000 mm street/east setbacks")
    groups = {
        "kitchen": [r for r in records.values() if r.get("sourceId", "").startswith("KITCHEN-RUN")],
        "windows": [r for r in records.values() if r.get("group") == "Windows"],
        "interior": [r for r in records.values() if r.get("group") == "Interior"],
    }
    require(all(groups.values()), "Source lacks kitchen, windows or interior geometry")
    return {name: [{"id": r["id"], "sourceId": r["sourceId"], "name": r["name"],
                    "sourceBoundsMm": r["boundsMm"], "materialNames": r["materialNames"]}
                   for r in sorted(items, key=lambda r: r["id"])] for name, items in groups.items()}


@lru_cache(maxsize=4)
def source_text(relative):
    return (ROOT / relative).read_text()


def source_uv_transform(source, scene_text=None, kitchen_text=None):
    """Recover only unambiguous current source texture transforms, by name."""
    scene_text = source_text("lib/babylon-scene.ts") if scene_text is None else scene_text
    kitchen_text = source_text("lib/babylon-kitchen.ts") if kitchen_text is None else kitchen_text
    result = {"scale": [1.0, 1.0], "offset": [0.0, 0.0], "rotationRadians": 0.0,
              "source": "exported UV0; no material transform recovered", "exactSourceTransform": False}
    # Parse the current method call rather than maintaining a second numeric
    # authority. Semantic source names are stable across reordered DOM IDs.
    members = {"real-grass": "grass", "real-terrain": "terrain", "real-wall": "wall",
               "real-timber": "timber", "real-deck": "deck", "real-roof": "roof",
               "real-fence-metal": "fenceMetal", "real-gravel": "gravel", "real-concrete": "concrete",
               "real-chimney": "chimney", "real-paving": "paving", "real-paving-entry": "pavingEntry",
               "real-road-reserve": "roadReserve"}
    member = members.get(source["name"])
    if member:
        pattern = (r'this\.applyTexture\(\s*this\.realisticMaterials\.' + re.escape(member)
                   + r',\s*"([^"\n]+)"\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,')
        matches = re.findall(pattern, scene_text)
        require(len(matches) == 1, "Current source texture scale is ambiguous: " + source["name"])
        name, u_scale, v_scale = matches[0]
        require(source.get("texture") == "/assets/textures/" + name + ".jpg", "Source texture scale name mismatch")
        result.update(scale=[float(u_scale), float(v_scale)], exactSourceTransform=True,
                      source="lib/babylon-scene.ts:applyTexture(realisticMaterials." + member + ")")
    if source["name"] == "Kitchen 2026 · prírodný dub":
        # Cabinet vertices now carry continuous, vertical, metric UVs. The
        # scanned veneer repeats every 1.83 m; adding the historic 90-degree
        # texture rotation would turn this authored grain sideways again.
        require(source.get("texture") == "/assets/textures/kitchen/living-natural-oak-albedo.jpg"
                and len(re.findall(r'const\s+oakTexture\s*=\s*oak\.albedoTexture\s+as\s+Texture\s*;', kitchen_text)) == 1
                and len(re.findall(r'\boakTexture\.uScale\s*=\s*oakTexture\.vScale\s*=\s*1\s*/\s*1\.83\s*;', kitchen_text)) == 1
                and re.findall(r'\boakTexture\.(uScale|vScale|uOffset|vOffset|wAng)\s*=', kitchen_text) == ["uScale", "vScale"]
                and not re.search(r'\(oak\.albedoTexture\s+as\s+Texture\)\.(?:uScale|vScale|uOffset|vOffset|wAng)\s*=', kitchen_text),
                "Current kitchen oak metric scale is not the reviewed source transform")
        result.update(scale=[1 / 1.83, 1 / 1.83], exactSourceTransform=True,
                      source="lib/babylon-kitchen.ts:oakTexture.uScale=oakTexture.vScale=1/1.83; authored metric UV0")
    return result


def native_uv_affine(transform):
    """Conjugate Babylon UV transform by the Blender glTF V-axis flip.

    OBJ retains Babylon UVs; Blender's glTF exporter writes (u, 1-v).
    Its JPEG/PNG origin is the same as Unreal's imported Texture2D. Therefore
    native coordinates use F * T * F, including source rotation about (0.5,0.5).
    """
    su, sv = transform["scale"]
    ou, ov = transform["offset"]
    angle = transform["rotationRadians"]
    cosine, sine = math.cos(angle), math.sin(angle)
    # Babylon first scales, then rotates around the scaled half-UV center.
    a, b, d, e = cosine * su, -sine * sv, sine * su, cosine * sv
    c, f = 0.5 * su - 0.5 * a - 0.5 * b + ou, 0.5 * sv - 0.5 * d - 0.5 * e + ov
    return [[a, -b, b + c], [-d, e, 1 - e - f]]


def srgb_hex_linear(value):
    require(re.fullmatch(r"#[0-9a-fA-F]{6}", value), "Invalid procedural fallback color")
    channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    return [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]


def uv_shader(transform):
    rows = native_uv_affine(transform)
    return "return float2(" + ", ".join(
        "UV.x * %.12g + UV.y * %.12g + %.12g" % tuple(row) for row in rows) + ");"


def procedural_fallback(source, scene_text=None):
    scene_text = source_text("lib/babylon-scene.ts") if scene_text is None else scene_text
    identity = (source["name"], source.get("texture"))
    if identity == ("real-solar", "photovoltaic-cell-grid"):
        colors = re.findall(r'solarContext\.fillStyle\s*=\s*"(#[0-9a-fA-F]{6})"', scene_text)
        require(len(colors) == 2, "Current source PV canvas colors are ambiguous")
        return {"color": srgb_hex_linear(colors[1]), "sourceSrgbHex": colors[1],
                "source": "lib/babylon-scene.ts:solarContext.fillStyle (cell fill)",
                "kind": "representative-source-cell-color", "fullProceduralShaderTransferred": False}
    if identity == ("real-road", "street-grey-block-paver-albedo"):
        colors = re.findall(r'paverContext\.fillStyle\s*=\s*"(#[0-9a-fA-F]{6})"', scene_text)
        require(len(colors) == 1, "Current source pavement canvas background is ambiguous")
        return {"color": srgb_hex_linear(colors[0]), "sourceSrgbHex": colors[0],
                "source": "lib/babylon-scene.ts:paverContext.fillStyle (canvas base)",
                "kind": "representative-source-pavement-base-color", "fullProceduralShaderTransferred": False}
    return None


def material_recipe(source):
    """No ordinal IDs or historical recipe assumptions: consume current values."""
    values = [*source["color"], source["roughness"], source["metallic"], source["alpha"], *source["emission"]]
    require(len(source["color"]) == 3 and len(source["emission"]) == 3
            and all(isinstance(v, (int, float)) and math.isfinite(v) for v in values),
            "Invalid source PBR values: " + source["name"])
    require(all(0 <= v <= 1 for v in source["color"])
            and all(0 <= source[k] <= 1 for k in ("roughness", "metallic", "alpha"))
            and all(v >= 0 for v in source["emission"]), "Source PBR values are out of range")
    texture = source.get("texture")
    relative = None
    if texture and texture.startswith("/assets/"):
        candidate = Path("public") / texture.lstrip("/")
        require(".." not in candidate.parts and (ROOT / candidate).resolve().is_relative_to(ROOT / "public/assets"),
                "Source texture escapes public/assets")
        require(candidate.suffix.lower() in (".jpg", ".jpeg", ".png"), "Unsupported source albedo format")
        relative = candidate.as_posix()
    elif texture and ("/" in texture or "\\" in texture):
        raise RuntimeError("Unsupported source texture path: " + texture)
    translucent = source["alpha"] < 0.999
    # Alpha-bearing source cards must not become opaque rectangular billboards.
    masked = bool(relative and relative.endswith(".png") and not translucent)
    fallback = procedural_fallback(source)
    return {"name": source["name"], "color": fallback["color"] if fallback else source["color"], "roughness": source["roughness"],
            "metallic": source["metallic"], "alpha": source["alpha"], "emission": source["emission"],
            "texture": relative, "unsupportedProceduralTexture": texture if texture and not relative else None,
            "blend": "translucent" if translucent else "masked" if masked else "opaque",
            "twoSided": True, "uv": "source UV0 with recorded source-derived affine transform",
            "uvTransform": source_uv_transform(source), "proceduralFallback": fallback}


class SourceMaterialWriter:
    def __init__(self, reuse=False):
        self.assets = unreal.EditorAssetLibrary
        self.tools = unreal.AssetToolsHelpers.get_asset_tools()
        self.lib = unreal.MaterialEditingLibrary
        self.textures = {}
        self.entries = {}
        self.reuse = reuse

    def save(self, asset):
        self.assets.set_metadata_tag(asset, "BreziGeneratedBy", OWNER)
        require(self.assets.save_loaded_asset(asset, only_if_is_dirty=False),
                "Could not save refresh asset: " + asset.get_path_name())

    def node(self, material, kind, **properties):
        expression = self.lib.create_material_expression(material, kind, -600, 0)
        require(expression is not None, "Could not create native material expression")
        for key, value in properties.items():
            expression.set_editor_property(key, value)
        return expression

    def scalar(self, material, value):
        return self.node(material, unreal.MaterialExpressionConstant, r=float(value))

    def vector(self, material, value):
        return self.node(material, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(*value, 1))

    def connect(self, source, output, target, pin):
        require(self.lib.connect_material_expressions(source, output, target, pin), "Native material connection failed")

    def output(self, node, output, prop):
        require(self.lib.connect_material_property(node, output, prop), "Native material output connection failed")

    def texture(self, relative):
        if relative in self.textures:
            return self.textures[relative][0]
        path = ROOT / relative
        digest = sha(path)
        name = "T_" + re.sub(r"[^A-Za-z0-9_]", "_", path.stem) + "_" + digest[:12]
        package = MATERIALS_PATH + "/Textures/" + name
        if self.assets.does_asset_exist(package):
            texture = self.assets.load_asset(package)
            require(self.reuse and isinstance(texture, unreal.Texture2D)
                    and self.assets.get_metadata_tag(texture, "BreziGeneratedBy") == OWNER
                    and self.assets.get_metadata_tag(texture, "source_path") == relative
                    and self.assets.get_metadata_tag(texture, "source_sha256") == digest
                    and texture.get_editor_property("srgb") is True,
                    "Existing source texture does not belong to the verified refresh: " + package)
            self.textures[relative] = (texture, {"source": relative, "sha256": digest, "asset": texture.get_path_name(), "srgb": True})
            return texture
        require(not self.reuse, "Materials-only refresh cannot introduce a previously unverified texture: " + relative)
        task = unreal.AssetImportTask()
        for prop, value in {"filename": str(path), "destination_path": MATERIALS_PATH + "/Textures",
                            "destination_name": name, "automated": True, "save": False,
                            "replace_existing": False, "factory": unreal.TextureFactory()}.items():
            task.set_editor_property(prop, value)
        self.tools.import_asset_tasks([task])
        results = task.get_objects()
        require(len(results) == 1 and isinstance(results[0], unreal.Texture2D), "Source texture import failed: " + relative)
        texture = results[0]
        require(texture.get_path_name().startswith(MATERIALS_PATH + "/Textures/"), "Texture imported outside refresh namespace")
        texture.set_editor_property("srgb", True)
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
        texture.set_editor_property("address_x", unreal.TextureAddress.TA_WRAP)
        texture.set_editor_property("address_y", unreal.TextureAddress.TA_WRAP)
        self.assets.set_metadata_tag(texture, "source_path", relative)
        self.assets.set_metadata_tag(texture, "source_sha256", digest)
        self.save(texture)
        self.textures[relative] = (texture, {"source": relative, "sha256": digest, "asset": texture.get_path_name(), "srgb": True})
        return texture

    def make(self, slot, recipe):
        require(re.fullmatch(r"MAT_\d+", slot), "Invalid current source material slot")
        path = MATERIALS_PATH + "/M_" + slot
        if self.reuse:
            material = self.assets.load_asset(path)
            require(isinstance(material, unreal.Material)
                    and self.assets.get_metadata_tag(material, "BreziGeneratedBy") == OWNER
                    and self.assets.get_metadata_tag(material, "source_material_slot") == slot
                    and self.assets.get_metadata_tag(material, "source_material_name") == recipe["name"],
                    "Existing source material is not owned by this refresh: " + slot)
            for expression in list(self.lib.get_material_expressions(material)):
                self.lib.delete_material_expression(material, expression)
            require(not list(self.lib.get_material_expressions(material)), "Refresh material graph did not clear")
        else:
            material = self.tools.create_asset("M_" + slot, MATERIALS_PATH, unreal.Material, unreal.MaterialFactoryNew())
        require(material is not None, "Could not create source material: " + slot)
        self.assets.set_metadata_tag(material, "source_material_slot", slot)
        self.assets.set_metadata_tag(material, "source_material_name", recipe["name"])
        self.assets.set_metadata_tag(material, "source_recipe_json", json.dumps(recipe, sort_keys=True))
        material.set_editor_property("two_sided", recipe["twoSided"])
        material.set_editor_property("blend_mode", {
            "opaque": unreal.BlendMode.BLEND_OPAQUE, "masked": unreal.BlendMode.BLEND_MASKED,
            "translucent": unreal.BlendMode.BLEND_TRANSLUCENT}[recipe["blend"]])
        material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
        if recipe["blend"] == "translucent":
            material.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
            self.output(self.scalar(material, recipe["alpha"]), "", unreal.MaterialProperty.MP_OPACITY)
        else:
            self.lib.set_base_material_usage(material, unreal.MaterialUsage.MATUSAGE_NANITE, True)
        color, color_output = self.vector(material, recipe["color"]), ""
        if recipe["texture"]:
            sample = self.node(material, unreal.MaterialExpressionTextureSample,
                               texture=self.texture(recipe["texture"]), sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
            coordinates = self.node(material, unreal.MaterialExpressionTextureCoordinate, coordinate_index=0)
            input_ = unreal.CustomInput()
            input_.set_editor_property("input_name", "UV")
            mapping = self.node(material, unreal.MaterialExpressionCustom, inputs=[input_],
                                code=uv_shader(recipe["uvTransform"]),
                                output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT2,
                                description="BreziModelRefreshSourceUV")
            self.connect(coordinates, "", mapping, "UV")
            self.connect(mapping, "", sample, "UVs")
            multiply = self.node(material, unreal.MaterialExpressionMultiply)
            self.connect(sample, "RGB", multiply, "A")
            self.connect(color, "", multiply, "B")
            color, color_output = multiply, ""
            if recipe["blend"] == "masked":
                material.set_editor_property("opacity_mask_clip_value", 0.45)
                self.output(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK)
        self.output(color, color_output, unreal.MaterialProperty.MP_BASE_COLOR)
        self.output(self.scalar(material, recipe["roughness"]), "", unreal.MaterialProperty.MP_ROUGHNESS)
        self.output(self.scalar(material, recipe["metallic"]), "", unreal.MaterialProperty.MP_METALLIC)
        if any(recipe["emission"]):
            self.output(self.vector(material, recipe["emission"]), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        errors = list(self.lib.recompile_material(material))
        require(not errors, "Native refresh material compilation failed: " + slot + ": " + str(errors))
        nanite_usage = bool(self.lib.has_material_usage(material, unreal.MaterialUsage.MATUSAGE_NANITE))
        require(recipe["blend"] == "translucent" or nanite_usage, "Refresh base material lacks effective Nanite usage: " + slot)
        self.save(material)
        self.entries[slot] = {"asset": material.get_path_name(), "recipe": recipe,
                              "nativeBlendMode": str(material.get_editor_property("blend_mode")),
                              "nativeType": material.get_class().get_name(), "naniteUsage": nanite_usage,
                              "nativeRecompileErrors": [], "cookedMetalShaderAvailabilityVerified": False}
        return material


def apply_source_materials(scene, meshes, reuse=False):
    from materials import _resolve_slot
    records = {record["id"]: record for record in scene["objects"]}
    assignments = []
    for id_, mesh in sorted(meshes.items()):
        for index, slot in enumerate(mesh.get_editor_property("static_materials")):
            source_slot = _resolve_slot(slot, records[id_], scene["materials"])
            assignments.append((id_, mesh, index, source_slot))
    writer = SourceMaterialWriter(reuse=reuse)
    materials = {slot: writer.make(slot, material_recipe(scene["materials"][slot]))
                 for slot in sorted({assignment[3] for assignment in assignments})}
    bindings = []
    for id_, mesh, index, slot in assignments:
        if not reuse:
            mesh.set_material(index, materials[slot])
        require(mesh.get_material(index) == materials[slot], "Source material assignment failed: " + id_)
        bindings.append({"id": id_, "index": index, "sourceSlot": slot, "asset": materials[slot].get_path_name()})
    if not reuse:
        for mesh in meshes.values():
            writer.save(mesh)
    return {"status": "source-pbr-materials-authored", "materials": writer.entries,
            "textures": [value[1] for value in writer.textures.values()], "bindings": bindings,
            "historicalPhotoRecipesApplied": False, "renderedVerified": False}


def verify_reloaded_world(base, actor_system, records, material_report, detail_report=None):
    expected_bindings = {(entry["id"], entry["index"]): entry for entry in material_report["bindings"]}
    found, bound, errors = set(), set(), []
    for actor in actor_system.get_all_level_actors():
        ids = {str(tag) for tag in actor.get_editor_property("tags")} & records.keys()
        if not ids:
            continue
        require(len(ids) == 1, "Reloaded source identity is ambiguous")
        id_ = next(iter(ids))
        require(id_ not in found, "Reloaded source identity is duplicated: " + id_)
        components = [c for c in actor.get_components_by_class(unreal.StaticMeshComponent) if c.get_editor_property("static_mesh")]
        require(len(components) == 1, "Reloaded canonical actor has a different component count")
        component = components[0]
        mesh = component.get_editor_property("static_mesh")
        expected, actual = base.source_bounds_cm(records[id_]), base.measured_bounds_cm(component)
        delta = max(abs(expected[k][axis] - actual[k][axis]) for k in ("min", "max") for axis in range(3))
        require(math.isfinite(delta) and delta <= base.TOLERANCE_CM, "Reloaded geometry differs: " + id_)
        errors.append(delta)
        for index in range(component.get_num_materials()):
            key = (id_, index)
            material = component.get_material(index)
            require(key in expected_bindings and material is not None
                    and material.get_path_name() == expected_bindings[key]["asset"], "Reloaded component material differs: " + id_)
            require(mesh.get_material(index) == material, "Unexpected component material override: " + id_)
            bound.add(key)
        found.add(id_)
    require(found == records.keys() and bound == expected_bindings.keys(), "Reloaded geometry/material coverage differs")
    for slot, entry in material_report["materials"].items():
        material = unreal.EditorAssetLibrary.load_asset(entry["asset"])
        require(material is not None and str(material.get_editor_property("blend_mode")) == entry["nativeBlendMode"],
                "Reloaded material blend differs: " + slot)
        require(unreal.EditorAssetLibrary.get_metadata_tag(material, "source_recipe_json") == json.dumps(entry["recipe"], sort_keys=True),
                "Reloaded material source recipe differs: " + slot)
        if "naniteUsage" in entry:
            require(bool(unreal.MaterialEditingLibrary.has_material_usage(material, unreal.MaterialUsage.MATUSAGE_NANITE)) == entry["naniteUsage"]
                    and (entry["recipe"]["blend"] == "translucent" or entry["naniteUsage"]),
                    "Reloaded base material lost Nanite usage: " + slot)
        if entry["recipe"]["blend"] == "translucent":
            opacity = unreal.MaterialEditingLibrary.get_material_property_input_node(material, unreal.MaterialProperty.MP_OPACITY)
            require(opacity is not None and abs(float(opacity.get_editor_property("r")) - entry["recipe"]["alpha"]) < 1e-6,
                    "Reloaded glazing/translucency lost source alpha: " + slot)
        if entry["recipe"].get("uvTransform") and entry["recipe"]["texture"]:
            expressions = list(unreal.MaterialEditingLibrary.get_material_expressions(material))
            mappings = [node for node in expressions if isinstance(node, unreal.MaterialExpressionCustom)
                        and node.get_editor_property("description") == "BreziModelRefreshSourceUV"]
            samples = [node for node in expressions if isinstance(node, unreal.MaterialExpressionTextureSample)
                       and not (detail_report and slot in detail_report["materials"]
                                and str(node.get_editor_property("desc")).startswith("BreziArchvizDetail:"))]
            require(len(mappings) == 1 and len(samples) == 1
                    and mappings[0].get_editor_property("code") == uv_shader(entry["recipe"]["uvTransform"]),
                    "Reloaded source UV graph differs: " + slot)
            names = [str(pin) for pin in unreal.MaterialEditingLibrary.get_material_expression_input_names(samples[0])]
            inputs = list(unreal.MaterialEditingLibrary.get_inputs_for_material_expression(material, samples[0]))
            require(names.count("UVs") == 1 and inputs[names.index("UVs")] == mappings[0],
                    "Reloaded source UV mapping is disconnected: " + slot)
        if entry["recipe"].get("proceduralFallback"):
            color = unreal.MaterialEditingLibrary.get_material_property_input_node(material, unreal.MaterialProperty.MP_BASE_COLOR)
            value = color.get_editor_property("constant") if color else None
            require(value is not None and max(abs(getattr(value, name) - expected) for name, expected
                                              in zip(("r", "g", "b"), entry["recipe"]["color"])) < 1e-6,
                    "Reloaded procedural fallback color differs: " + slot)
    return {"objectCount": len(found), "materialBindingCount": len(bound), "maxBoundsErrorCm": max(errors),
            "sourceAlphaVerified": True, "canonicalWorldBoundsVerified": True}


def verify_material_refresh_receipt(previous, geometry, project_content, repository=ROOT):
    """Fail before opening/mutating the existing map on any unapproved drift."""
    require(previous.get("status") == "model-refresh-import-validated", "Materials refresh requires a successful prior native receipt")
    source_files = {
        geometry / "scene.json": previous["sourceManifestSha256"],
        geometry / "brezi-twin.glb": previous["sourceGlbSha256"],
        geometry / "walking.json": previous["walkingSha256"],
        geometry / "viewpoints.json": previous["viewpointsSha256"],
        geometry / "hidden-collision.json": previous["hiddenCollision"]["sourceContractSha256"],
        geometry / "brezi-collision-only.glb": previous["hiddenCollision"]["sourceGlbSha256"],
        project_content / "Brezi/Maps/Brezi.umap": previous["mapFileSha256"],
    }
    if previous.get("doors"):
        source_files[geometry / "doors.json"] = previous["doors"]["contractSha256"]
        source_files[project_content / "Data/doors.json"] = previous["doors"]["contractSha256"]
    require(previous.get("finalAssetHashes") and OWNER in previous.get("pipelineFiles", {}), "Prior refresh has incomplete asset/writer pins")
    protected_content = (project_content / "Brezi").resolve()
    for relative, digest in previous["finalAssetHashes"].items():
        path = (repository / relative).resolve()
        require(path.is_relative_to(protected_content), "Prior asset receipt points outside this isolated project's Brezi content")
        source_files[path] = digest
    for relative, digest in previous["pipelineFiles"].items():
        if relative != OWNER:
            source_files[repository / relative] = digest
    for texture in previous["materials"]["textures"]:
        source_files[repository / texture["source"]] = texture["sha256"]
    for path, digest in source_files.items():
        require(path.is_file() and sha(path) == digest, "Materials refresh input drift: " + str(path))
    return {"verifiedInputFiles": len(source_files), "allowedChangedPipelineFile": OWNER,
            "previousWriterSha256": previous["pipelineFiles"][OWNER], "currentWriterSha256": sha(repository / OWNER)}


def canonical_meshes(actor_system, records):
    meshes = {}
    for actor in actor_system.get_all_level_actors():
        ids = {str(tag) for tag in actor.get_editor_property("tags")} & records.keys()
        if not ids:
            continue
        require(len(ids) == 1, "Material refresh source actor is ambiguous")
        id_ = next(iter(ids))
        components = [c for c in actor.get_components_by_class(unreal.StaticMeshComponent) if c.get_editor_property("static_mesh")]
        require(id_ not in meshes and len(components) == 1, "Material refresh source components differ")
        meshes[id_] = components[0].get_editor_property("static_mesh")
    require(meshes.keys() == records.keys(), "Material refresh source geometry coverage differs")
    return meshes


def main():
    global unreal
    import unreal
    sys.path.insert(0, str(ROOT / "scripts/unreal"))
    import import_scene as base
    from walking import apply_walking_contract
    from hidden_collision import apply_hidden_collision_contract, verify_hidden_collision_contract, verify_inputs as verify_hidden_inputs
    from materials import _asset_hashes
    from doors import apply_doors_contract, verify_doors_contract

    base.GEOMETRY = GEOMETRY
    base.REPORT = REPORT
    materials_only = os.environ.get("BREZI_MODEL_MATERIALS_ONLY") == "1"
    previous = None
    project_content = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()))
    if materials_only:
        previous_bytes = REPORT_PATH.read_bytes()
        previous = json.loads(previous_bytes)
        preflight = verify_material_refresh_receipt(previous, GEOMETRY, project_content)
        previous_digest = hashlib.sha256(previous_bytes).hexdigest()
        backup = REPORT_PATH.with_name("model-refresh-import-before-materials-" + previous_digest[:16] + ".json")
        if backup.exists():
            require(backup.read_bytes() == previous_bytes, "Prior refresh backup path has conflicting contents")
        else:
            backup.write_bytes(previous_bytes)
        limitations = REPORT["limitations"]
        REPORT.update(deepcopy(previous))
        REPORT["limitations"] = limitations
        REPORT["materialsRefresh"] = {**preflight, "previousReportSha256": previous_digest,
                                       "previousReportBackup": str(backup.relative_to(ROOT)),
                                       "mode": "owned-material-graphs-only", "geometryReimported": False}
        REPORT["verification"].update(savedReloaded=False, sourceMaterialBindingsVerified=False)
    write_report("pending")
    scene, bridge, records, archive_ids = base.verify_inputs()
    REPORT["activeDesign"] = scene.get("activeDesign")
    REPORT["semantics"] = validate_current_source(scene, records)
    verify_hidden_inputs(scene, GEOMETRY)
    # Every real source image must exist before creating native content.
    recipes = {slot: material_recipe(source) for slot, source in scene["materials"].items()}
    for recipe in recipes.values():
        if recipe["texture"]:
            require((ROOT / recipe["texture"]).is_file(), "Source albedo is absent: " + recipe["texture"])
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.scan_paths_synchronous(["/Interchange/Pipelines", "/Game/Brezi"], force_rescan=True)
    assets = unreal.EditorAssetLibrary
    actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    level_system = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if materials_only:
        require(unreal.EditorLoadingAndSavingUtils.new_blank_map(False), "Could not unload startup map")
        require(level_system.load_level(base.MAP_PATH), "Could not load existing refresh map")
        world = unreal.EditorLevelLibrary.get_editor_world()
        require(assets.get_metadata_tag(world, "BreziGeneratedBy") == OWNER
                and assets.get_metadata_tag(world, "BreziSourceGLBSHA256") == previous["sourceGlbSha256"],
                "Existing map is not owned by this exact model refresh")
        del world
        REPORT["materialsRefresh"]["before"] = verify_reloaded_world(base, actor_system, records, previous["materials"])
        REPORT["hiddenCollision"] = verify_hidden_collision_contract(scene, GEOMETRY)
        base.measure_final_collision(actor_system)
        meshes = canonical_meshes(actor_system, records)
        actors = []
        REPORT["materials"] = apply_source_materials(scene, meshes, reuse=True)
    else:
        require(not assets.does_asset_exist(base.MAP_PATH)
                and not assets.list_assets("/Game/Brezi", recursive=True, include_folder=False),
                "Model refresh only accepts a fresh isolated project with empty /Game/Brezi content")
        require(level_system.new_level(base.MAP_PATH), "Could not create empty refresh map")
        require(not any(a.get_components_by_class(unreal.StaticMeshComponent) for a in actor_system.get_all_level_actors()),
                "New refresh map unexpectedly contains visual geometry")
        actors, _ = base.import_geometry(actor_system, level_system)
        meshes = base.configure_and_measure(actors, records, bridge, archive_ids)
        REPORT["materials"] = apply_source_materials(scene, meshes)
        REPORT["walking"] = apply_walking_contract(scene, meshes, GEOMETRY)
        REPORT["hiddenCollision"] = apply_hidden_collision_contract(scene, GEOMETRY)
        REPORT["doors"] = apply_doors_contract(scene, GEOMETRY)
        base.lighting(actor_system, base.read_json("viewpoints.json"))
    base.measure_final_collision(actor_system)
    world = unreal.EditorLevelLibrary.get_editor_world()
    assets.set_metadata_tag(world, "BreziGeneratedBy", OWNER)
    assets.set_metadata_tag(world, "BreziSourceGLBSHA256", REPORT["sourceGlbSha256"])
    require(level_system.save_current_level(), "Could not save refreshed map")
    require(assets.save_directory("/Game/Brezi", only_if_is_dirty=True, recursive=True), "Could not save refreshed content")
    # Drop live actor/mesh wrappers before opening the persisted world again.
    actors.clear()
    meshes.clear()
    del world
    require(unreal.EditorLoadingAndSavingUtils.new_blank_map(False), "Could not unload refreshed map")
    require(level_system.load_level(base.MAP_PATH), "Could not reload refreshed map")
    REPORT["savedReadback"] = verify_reloaded_world(base, actor_system, records, REPORT["materials"])
    REPORT["hiddenCollision"] = verify_hidden_collision_contract(scene, GEOMETRY)
    if REPORT.get("doors"):
        REPORT["doors"] = verify_doors_contract(scene, GEOMETRY)
    base.measure_final_collision(actor_system)
    REPORT["auxiliaryCollisionObjects"] = REPORT["hiddenCollision"]["objectCount"]
    REPORT["totalCollisionComponentsIncludingAuxiliary"] = REPORT["finalCollisionComponents"] + REPORT["auxiliaryCollisionObjects"]
    map_file = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())) / "Brezi/Maps/Brezi.umap"
    require(map_file.is_file(), "Refreshed native map was not persisted")
    REPORT["mapFileSha256"] = sha(map_file)
    REPORT["savedMapBytes"] = map_file.stat().st_size
    paths = [path for path in assets.list_assets("/Game/Brezi", recursive=True, include_folder=False)
             if path.split(".", 1)[0] != base.MAP_PATH]
    REPORT["finalAssetHashes"] = _asset_hashes(paths)
    if previous:
        allowed = set()
        for entry in previous["materials"]["materials"].values():
            package = project_content / entry["asset"].split(".", 1)[0].removeprefix("/Game/")
            allowed.update(str(package.with_suffix(extension).relative_to(ROOT)) for extension in (".uasset", ".uexp", ".ubulk"))
        require(REPORT["finalAssetHashes"].keys() == previous["finalAssetHashes"].keys(), "Materials refresh changed the native asset inventory")
        changed = [path for path, digest in previous["finalAssetHashes"].items() if REPORT["finalAssetHashes"][path] != digest]
        require(set(changed).issubset(allowed), "Materials refresh modified a protected mesh/texture/collision package: "
                + ", ".join(sorted(set(changed) - allowed)[:5]))
        REPORT["materialsRefresh"].update(changedMaterialPackages=changed, protectedAssetPackagesUnchanged=True,
                                           protectedAssetCount=sum(path not in allowed for path in previous["finalAssetHashes"]))
    REPORT["pipelineFiles"] = {name: sha(ROOT / name) for name in (
        OWNER, "scripts/unreal/import_scene.py", "scripts/unreal/materials.py",
        "scripts/unreal/walking.py", "scripts/unreal/walking.mjs", "scripts/unreal/hidden_collision.py",
        "scripts/unreal/doors.py", "scripts/unreal/doors.mjs")}
    REPORT["sourceMaterialSha256"] = hashlib.sha256(json.dumps(scene["materials"], sort_keys=True).encode()).hexdigest()
    REPORT["materials"]["shaderReadiness"] = {"baseMaterialNaniteUsagePersisted": True,
                                               "nativeGraphRecompileErrors": 0, "savedGraphsVerified": True,
                                               "targetMetalCookAndRuntimeRequired": True,
                                               "runtimeDefaultMaterialFallbacksVerifiedAbsent": False}
    REPORT["verification"].update(savedReloaded=True, sourceMaterialBindingsVerified=True)
    write_report("model-refresh-import-validated")
    unreal.log("BREZI_MODEL_REFRESH " + json.dumps({"status": REPORT["status"], "objects": REPORT["importedObjects"],
                                                  "maxErrorCm": REPORT["savedReadback"]["maxBoundsErrorCm"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        REPORT["error"] = str(error).replace(str(ROOT), "<repository>").replace(str(Path.home()), "<user>")
        write_report("failed")
        raise
