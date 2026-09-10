"""Opt-in native optical graphs for the already validated Brezi scene.

Call apply_optics(scene_manifest, mesh_assets_by_id, output_dir) in one existing
UE 5.8 commandlet. This module launches no process and has no import hook.
Only /Game/Brezi/OpticsGenerated assets and resolved imported mesh slots change.
No texture, displacement, actor, light, canonical vertex or water level changes.
"""
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
CONTENT = "/Game/Brezi/OpticsGenerated"
OWNER = "scripts/unreal/optics.py"
GLASS = {"real-glass", "real-bathroom-shower-glass", "real-interior-fireplace-glass"}
WATER = "real-pool-water"
TARGETS = GLASS | {WATER}
# First thin-surface A/B candidate. Only these exact source bindings stop
# sampling displaced scene color; Fresnel IOR, tint and roughness are retained.
THIN_SURFACE_SCOPE = {
    "real-glass": {"slot": "MAT_0015", "master": "M_ArchitecturalGlass", "ids": frozenset({
        "DOM_00133", "DOM_00145", "DOM_00153", "DOM_00174", "DOM_00192", "DOM_00210", "DOM_00224",
        "DOM_00240", "DOM_00256", "DOM_00266", "DOM_00282", "DOM_00287", "DOM_00302", "DOM_00307",
        "DOM_00322", "DOM_00340", "DOM_00372", "DOM_00390", "DOM_00408", "DOM_00413"})},
    "real-interior-fireplace-glass": {"slot": "MAT_0036", "master": "M_StoveGlass", "ids": frozenset({"DOM_00526"})},
}
DOCS = [
    "https://dev.epicgames.com/documentation/en-us/unreal-engine/single-layer-water-shading-model-in-unreal-engine",
    "https://dev.epicgames.com/documentation/en-us/unreal-engine/using-transparency-in-unreal-engine-materials",
    "https://dev.epicgames.com/documentation/en-us/unreal-engine/macos-development-requirements-for-unreal-engine",
]
ENGINE_EVIDENCE = [
    "Source/Editor/MaterialEditor/Private/MaterialEditingLibrary.cpp",
    "Source/Runtime/Engine/Public/Materials/MaterialExpressionSingleLayerWaterMaterialOutput.h",
    "Source/Runtime/Engine/Public/Materials/MaterialExpressionThinTranslucentMaterialOutput.h",
    "Source/Runtime/Engine/Classes/Engine/EngineTypes.h",
    "Shaders/Private/SingleLayerWaterShading.ush",
    "Shaders/Private/ThinTranslucentCommon.ush",
    "Shaders/Private/DistortionCommon.ush",
    "Source/Runtime/Engine/Private/Materials/MaterialShared.cpp",
    "Source/Runtime/Engine/Public/Materials/MaterialInstanceBasePropertyOverrides.h",
    "Config/Mac/DataDrivenPlatformInfo.ini",
]
# Visual starting coefficients, in reciprocal metres, not a measured water sample.
# The graph explicitly divides by 100 because the native output uses 1/cm.
ABSORPTION_PER_METRE = [0.13, 0.045, 0.02]
SCATTERING_PER_METRE = [0.002, 0.004, 0.006]
# Analytic normal ripples only. Values are authored visual parameters, not a
# surveyed wave state. Directions are UE world XY, wavelengths and heights in m.
# Twelve authored modes share the original total independent-phase slope power.
# Their directions and phases are deterministic choices, not measured site waves.
WAVES = [{'direction': [0.9547607995027975, 0.297374874077786],
  'wavelengthMetres': 0.38613701371430004,
  'amplitudeMetres': 0.00036783869184896917,
  'phaseCycles': 0.8030508075688771},
 {'direction': [-0.9048847407593247, 0.4256566761380935],
  'wavelengthMetres': 0.32994043234464987,
  'amplitudeMetres': 0.00031430516296357,
  'phaseCycles': 0.5351016151377543},
 {'direction': [0.3797068926649919, -0.9251068455387714],
  'wavelengthMetres': 0.2902322557572601,
  'amplitudeMetres': 0.0002764786837273154,
  'phaseCycles': 0.26715242270663175},
 {'direction': [0.34491664987334575, 0.9386333174569012],
  'wavelengthMetres': 0.247993205892883,
  'amplitudeMetres': 0.0002362412646371277,
  'phaseCycles': 0.999203230275509},
 {'direction': [-0.888368498960274, -0.4591311469014812],
  'wavelengthMetres': 0.21814733964942384,
  'amplitudeMetres': 0.00020780973902270888,
  'phaseCycles': 0.7312540378443861},
 {'direction': [0.9651939169235703, -0.26153528009378807],
  'wavelengthMetres': 0.18639919252087117,
  'amplitudeMetres': 0.00017756607811058496,
  'phaseCycles': 0.4633048454132629},
 {'direction': [-0.5350394123396292, 0.8448270990227907],
  'wavelengthMetres': 0.15927152276195344,
  'amplitudeMetres': 0.00015172393865587255,
  'phaseCycles': 0.19535565298214053},
 {'direction': [-0.17615109451445862, -0.9843631402594056],
  'wavelengthMetres': 0.1401032695526354,
  'amplitudeMetres': 0.00013346403366069331,
  'phaseCycles': 0.9274064605510173},
 {'direction': [0.7948160822084165, 0.6068503896866704],
  'wavelengthMetres': 0.11971329265859405,
  'amplitudeMetres': 0.00011404030021595225,
  'phaseCycles': 0.659457268119894},
 {'direction': [-0.9959941911187946, 0.08941795825010745],
  'wavelengthMetres': 0.10530585392498713,
  'amplitudeMetres': 0.00010031560346728655,
  'phaseCycles': 0.39150807568877166},
 {'direction': [0.6740141563471598, -0.7387184287965385],
  'wavelengthMetres': 0.08998013072670655,
  'amplitudeMetres': 8.571613806336648e-05,
  'phaseCycles': 0.1235588832576493},
 {'direction': [0.0020000665695739297, 0.9999979998648584],
  'wavelengthMetres': 0.07688484185658427,
  'amplitudeMetres': 7.324141081296573e-05,
  'phaseCycles': 0.855609690826526}]


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _receipt(path, report, status):
    report.update(status=status, generatedAt=datetime.now(timezone.utc).isoformat())
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def _hash_assets(assets):
    content = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()))
    result = {}
    for object_path in sorted(set(assets)):
        package = object_path.split(".", 1)[0]
        if not package.startswith((CONTENT + "/", "/Game/Brezi/Geometry/")):
            raise RuntimeError("Unexpected optics asset path: " + object_path)
        base = content / package[len("/Game/"):]
        if not base.with_suffix(".uasset").is_file():
            raise RuntimeError("Optical asset has not been saved: " + object_path)
        for suffix in (".uasset", ".uexp", ".ubulk"):
            file = base.with_suffix(suffix)
            if file.is_file():
                result[str(file.relative_to(ROOT))] = sha(file)
    return result


def _geometry(mesh):
    box = mesh.get_bounding_box()
    return {"minCm": [float(box.min.x), float(box.min.y), float(box.min.z)],
            "maxCm": [float(box.max.x), float(box.max.y), float(box.max.z)],
            "vertices": mesh.get_num_vertices(0), "triangles": mesh.get_num_triangles(0),
            "slots": len(mesh.get_editor_property("static_materials"))}


def _slot(static_slot, record, sources):
    material = static_slot.get_editor_property("material_interface")
    tag = unreal.EditorAssetLibrary.get_metadata_tag(material, "source_material_slot") if material else ""
    names = [str(static_slot.get_editor_property("material_slot_name")),
             str(static_slot.get_editor_property("imported_material_slot_name")),
             material.get_name() if material else "", str(tag)]
    matches = {slot for name in names for slot in re.findall(r"MAT_\d+", name) if slot in sources}
    if len(matches) != 1:
        raise RuntimeError("Ambiguous source material metadata: " + record["id"] + " " + repr(names))
    slot = matches.pop()
    if slot not in record["materialSlots"]:
        raise RuntimeError("Native slot differs from canonical record: " + record["id"] + "/" + slot)
    return slot


def _validate_pool(scene, record):
    pool = scene["pool"]
    if (record.get("metadata") or {}).get("entityId") != pool["id"]:
        raise RuntimeError("Water material is used outside the canonical pool entity")
    if (pool["waterLengthMm"], pool["waterWidthMm"]) != (6000, 2700):
        raise RuntimeError("Canonical pool dimensions changed; review optical contract")
    low, high = record["boundsMm"]["min"], record["boundsMm"]["max"]
    center = scene["sceneCenterMm"]
    footprint = pool["waterFootprintMm"]
    expected_low = [min(p["x"] for p in footprint) - center["x"],
                    min(p["y"] for p in footprint) - center["y"], -12]
    expected_high = [max(p["x"] for p in footprint) - center["x"],
                     max(p["y"] for p in footprint) - center["y"], -12]
    errors = [abs(a - b) for actual, expected in ((low, expected_low), (high, expected_high))
              for a, b in zip(actual, expected)]
    if not all(math.isfinite(v) and v <= 0.5 for v in errors):
        raise RuntimeError("Pool water footprint or -12 mm level differs from canonical source")


def _thin_surface_scope(bindings, records, sources):
    """Fail before authoring if the 20 architectural + 1 stove scope drifts."""
    evidence = []
    for name, guard in THIN_SURFACE_SCOPE.items():
        slot = guard["slot"]
        if slot not in sources or sources[slot]["name"] != name:
            raise RuntimeError("Thin-surface source material identity changed: " + slot)
        selected = [(id_, index, actual_slot) for id_, _, index, actual_slot in bindings
                    if actual_slot == slot or sources[actual_slot]["name"] == name]
        if len(selected) != len(guard["ids"]) or {id_ for id_, _, _ in selected} != guard["ids"]:
            raise RuntimeError("Thin-surface source object scope changed: " + name)
        for id_, index, actual_slot in selected:
            record = records[id_]
            expected_triangles = 192 if name == "real-interior-fireplace-glass" else 16 if id_ == "DOM_00153" else 12
            if (actual_slot != slot or index != 0 or record["materialSlots"] != [slot]
                    or record["enabled"] is not True or record["instances"] != 1
                    or record["triangles"] != expected_triangles
                    or record["sourceId"] != record["name"]):
                raise RuntimeError("Thin-surface source binding changed: " + id_)
            if name == "real-interior-fireplace-glass" and record["sourceId"] != "FIREPLACE-STOVE-2026-08-24 · CURVED-GLASS · zaoblené panoramatické dvierka 118°":
                raise RuntimeError("Stove curved glass source identity changed")
            evidence.append({"objectId": id_, "sourceId": record["sourceId"], "sourceSlot": slot,
                             "sourceRecordSha256": digest(record), "triangles": expected_triangles,
                             "master": CONTENT + "/" + guard["master"], "requestedRefractionMethod": "RM_NONE"})
    return sorted(evidence, key=lambda record: record["objectId"])


class OpticsWriter:
    def __init__(self, report):
        self.report = report
        self.lib = unreal.MaterialEditingLibrary
        self.tools = unreal.AssetToolsHelpers.get_asset_tools()

    def asset(self, name, class_, factory):
        path = CONTENT + "/" + name
        existing = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
        if existing:
            if not isinstance(existing, class_) or unreal.EditorAssetLibrary.get_metadata_tag(existing, "BreziGeneratedBy") != OWNER:
                raise RuntimeError("Refusing to replace unowned optical asset: " + path)
            return existing
        asset = self.tools.create_asset(name, CONTENT, class_, factory)
        if not asset:
            raise RuntimeError("Cannot create optical asset: " + path)
        unreal.EditorAssetLibrary.set_metadata_tag(asset, "BreziGeneratedBy", OWNER)
        return asset

    def save(self, asset):
        unreal.EditorAssetLibrary.set_metadata_tag(asset, "writer_sha256", sha(__file__))
        if not unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False):
            raise RuntimeError("Cannot save optical asset: " + asset.get_path_name())

    def node(self, material, name, **properties):
        node = self.lib.create_material_expression(material, getattr(unreal, "MaterialExpression" + name))
        if not node:
            raise RuntimeError("Native optical expression unavailable: " + name)
        for key, value in properties.items():
            node.set_editor_property(key, value)
        return node

    def clear_graph(self, material):
        # UE 5.8 DeleteAllMaterialExpressions iterates GetExpressions() while
        # DeleteMaterialExpression removes from that same collection, skipping
        # old nodes on repeated authoring. Iterate a detached Python snapshot.
        old = list(self.lib.get_material_expressions(material))
        for expression in old:
            self.lib.delete_material_expression(material, expression)
        remaining = list(self.lib.get_material_expressions(material))
        if remaining:
            raise RuntimeError("Optical graph did not clear completely: " + material.get_path_name())
        return len(old)

    def validate_output(self, material, water, expected_refraction=None):
        expressions = list(self.lib.get_material_expressions(material))
        water_outputs = [node for node in expressions if isinstance(node, unreal.MaterialExpressionSingleLayerWaterMaterialOutput)]
        glass_outputs = [node for node in expressions if isinstance(node, unreal.MaterialExpressionThinTranslucentMaterialOutput)]
        outputs, other = (water_outputs, glass_outputs) if water else (glass_outputs, water_outputs)
        if len(outputs) != 1 or other:
            raise RuntimeError("Optical graph requires exactly one matching custom output: " + material.get_path_name())
        # Despite its old 'active material editor' documentation, the local
        # C++ implementation directly enumerates FExpressionInputIterator;
        # it also returns null for unconnected pins, so this works in a commandlet.
        names = list(self.lib.get_material_expression_input_names(outputs[0]))
        inputs = list(self.lib.get_inputs_for_material_expression(material, outputs[0]))
        expected = 4 if water else 2
        if len(names) != expected or len(inputs) != expected or any(node is None for node in inputs):
            raise RuntimeError("Optical custom output has missing input connections: " + material.get_path_name())
        method = material.get_editor_property("refraction_method")
        refraction_input = self.lib.get_material_property_input_node(material, unreal.MaterialProperty.MP_REFRACTION)
        specular_input = self.lib.get_material_property_input_node(material, unreal.MaterialProperty.MP_SPECULAR)
        if expected_refraction is not None:
            if method != expected_refraction:
                raise RuntimeError("Native optical refraction method differs: " + material.get_path_name() + ": " + str(method))
            if (refraction_input is None) != (expected_refraction == unreal.RefractionMode.RM_NONE):
                raise RuntimeError("Optical refraction input does not match the requested method: " + material.get_path_name())
        if specular_input is None or material.get_editor_property("two_sided"):
            raise RuntimeError("Optical Fresnel connection or source sidedness changed: " + material.get_path_name())
        result = {"expressionCount": len(expressions), "customOutputCount": len(outputs),
                "connectedOutputInputs": [str(name) for name in names], "refractionMethodNative": str(method),
                "refractionInputConnected": refraction_input is not None,
                "fresnelSpecularInputConnected": specular_input is not None, "twoSided": False}
        if water:
            result["waterNormalReadback"] = self.validate_water_normal(material)
        return result

    def validate_water_normal(self, material):
        """Read the actual MP_NORMAL graph; internal expression names are irrelevant."""
        def require(ok, message):
            if not ok:
                raise RuntimeError("Water normal readback: " + message)
        def output(value):
            return value[1] if isinstance(value, tuple) and len(value) == 2 and value[0] is True else value
        expressions = list(self.lib.get_material_expressions(material))
        visited, cosines = [], []
        def read(node, kind, pins=()):
            require(node in expressions and isinstance(node, getattr(unreal, "MaterialExpression" + kind)), "wrong node type: " + kind)
            if node not in visited:
                visited.append(node)
            names = list(self.lib.get_material_expression_input_names(node))
            inputs = list(self.lib.get_inputs_for_material_expression(material, node))
            require(len(names) == len(inputs), "input reflection alignment")
            connected = {re.sub(r"[^a-z0-9]", "", str(n).lower()): v for n, v in zip(names, inputs) if v is not None}
            require(len(connected) == sum(v is not None for v in inputs), "ambiguous input names")
            require(len(connected) == 1 if pins is None else set(connected) == set(pins), "unexpected connections: " + kind)
            for upstream in connected.values():
                channels = list(map(str, self.lib.get_material_expression_output_names(upstream)))
                require(channels and output(self.lib.get_input_node_output_name_for_material_expression(node, upstream)) == channels[0], "nondefault edge channel: " + kind)
            return connected
        def one(node, kind):
            return next(iter(read(node, kind, None).values()))
        def pair(node, kind):
            children = read(node, kind, ("a", "b"))
            return children["a"], children["b"]
        def scalar(node, expected):
            read(node, "Constant")
            actual = float(node.get_editor_property("r"))
            require(math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-7), "constant differs")
            return actual
        def vector(node, expected):
            read(node, "Constant3Vector")
            color = node.get_editor_property("constant")
            actual = [float(getattr(color, k)) for k in ("r", "g", "b")]
            require(all(math.isfinite(a) and math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-7) for a, b in zip(actual, expected)), "vector differs")
            return actual
        wave_count = len(WAVES)
        require(wave_count in (4, 12) and material.get_editor_property("tangent_space_normal") is False, "4/12-wave world normal policy differs")
        normal = self.lib.get_material_property_input_node(material, unreal.MaterialProperty.MP_NORMAL)
        require(normal is not None, "MP_NORMAL disconnected")
        require(output(self.lib.get_material_property_input_node_output_name(material, unreal.MaterialProperty.MP_NORMAL)) == list(map(str, self.lib.get_material_expression_output_names(normal)))[0], "MP_NORMAL output channel differs")
        gradient, up = pair(one(normal, "Normalize"), "Add")
        up_value = vector(up, [0, 0, 1])
        position_node = time_node = None
        rows = []
        for index in reversed(range(wave_count)):
            wave = WAVES[index]
            direction, length = wave["direction"], wave["wavelengthMetres"]
            gradient, weighted = pair(gradient, "Add")
            cosine, slope_node = pair(weighted, "Multiply")
            phase_node = one(cosine, "Cosine")
            require(cosine not in cosines, "reused wave cosine")
            cosines.append(cosine)
            period = float(cosine.get_editor_property("period"))
            require(period == 1.0, "Cosine period must be one cycle")
            travel, phase = pair(phase_node, "Add")
            spatial, temporal = pair(travel, "Add")
            position, position_vector = pair(spatial, "DotProduct")
            time, frequency_node = pair(temporal, "Multiply")
            read(position, "WorldPosition"); read(time, "Time")
            require(position_node is None or position == position_node, "waves do not share world position")
            require(time_node is None or time == time_node, "waves do not share Time")
            position_node, time_node = position, time
            require(position.get_editor_property("world_position_shader_offset") == unreal.WorldPositionIncludedOffsets.WPT_DEFAULT, "absolute position policy differs")
            require(time.get_editor_property("ignore_pause") is False and time.get_editor_property("override_period") is False, "Time pause/period policy differs")
            slope = 2 * math.pi * wave["amplitudeMetres"] / length
            rows.append({"index": index, "cosinePeriod": period,
                         "positionCyclesPerCm": vector(position_vector, [direction[0] / (100 * length), direction[1] / (100 * length), 0]),
                         "timeCyclesPerSecond": scalar(frequency_node, -math.sqrt(9.81 / (2 * math.pi * length))),
                         "phaseCycles": scalar(phase, wave["phaseCycles"]),
                         "slopeVector": vector(slope_node, [-slope * direction[0], -slope * direction[1], 0])})
        zero_value = vector(gradient, [0, 0, 0])
        require(sum(isinstance(n, unreal.MaterialExpressionCosine) for n in expressions) == wave_count, "extra or missing cosine")
        return {"status": "native-water-normal-graph-readback-validated", "normalOutputConnected": True,
                "worldSpaceNormal": True, "cosineCount": wave_count, "reachableExpressionCount": len(visited),
                "waves": list(reversed(rows)), "initialGradient": zero_value, "upVector": up_value,
                "absoluteWorldPositionCm": True, "sharedTime": True, "timeIgnoresPause": False,
                "timePeriodOverride": False, "defaultChannelsVerified": True,
                "internalNodeNamesUsed": False, "renderedVerified": False}

    def scalar(self, material, value, name=None):
        if name:
            return self.node(material, "ScalarParameter", parameter_name=name, default_value=value)
        return self.node(material, "Constant", r=value)

    def vector(self, material, values, name=None):
        color = unreal.LinearColor(*values, 1)
        if name:
            return self.node(material, "VectorParameter", parameter_name=name, default_value=color)
        return self.node(material, "Constant3Vector", constant=color)

    def connect(self, from_, to, input_name="", output_name=""):
        # Reflection returns display-shortened names; match the actual pin rather
        # than assuming CustomOutput properties use unspaced C++ identifiers.
        if input_name:
            normalize = lambda value: re.sub(r"[^a-z0-9]", "", str(value).lower())
            pins = self.lib.get_material_expression_input_names(to)
            matches = [str(pin) for pin in pins if normalize(pin) == normalize(input_name)]
            if len(matches) != 1:
                raise RuntimeError("Optical input pin not found: " + input_name + " in " + repr(list(pins)))
            input_name = matches[0]
        if not self.lib.connect_material_expressions(from_, output_name, to, input_name):
            raise RuntimeError("Native optical expression connection failed: " + input_name)

    def property(self, node, name):
        if not self.lib.connect_material_property(node, "", getattr(unreal.MaterialProperty, "MP_" + name)):
            raise RuntimeError("Native optical material property rejected: " + name)

    def binary(self, material, operation, a, b):
        node = self.node(material, operation)
        self.connect(a, node, "A")
        self.connect(b, node, "B")
        return node

    def ior_specular(self, material, value):
        ior = self.scalar(material, value, "IndexOfRefraction")
        one = self.scalar(material, 1)
        ratio = self.binary(material, "Divide", self.binary(material, "Subtract", ior, one),
                            self.binary(material, "Add", ior, one))
        f0 = self.binary(material, "Multiply", ratio, ratio)
        self.property(self.binary(material, "Divide", f0, self.scalar(material, 0.08)), "SPECULAR")
        return ior

    def water_normal(self, material):
        position = self.node(material, "WorldPosition")  # UE absolute position, cm.
        time = self.node(material, "Time")
        gradient = self.vector(material, [0, 0, 0])
        for wave in WAVES:
            direction, length = wave["direction"], wave["wavelengthMetres"]
            cycles = self.binary(material, "DotProduct", position,
                self.vector(material, [direction[0] / (100 * length), direction[1] / (100 * length), 0]))
            frequency = math.sqrt(9.81 / (2 * math.pi * length))
            phase = self.binary(material, "Add", cycles,
                self.binary(material, "Multiply", time, self.scalar(material, -frequency)))
            phase = self.binary(material, "Add", phase, self.scalar(material, wave["phaseCycles"]))
            cosine = self.node(material, "Cosine", period=1.0)
            self.connect(phase, cosine)
            slope = 2 * math.pi * wave["amplitudeMetres"] / length
            gradient = self.binary(material, "Add", gradient, self.binary(material, "Multiply", cosine,
                self.vector(material, [-slope * direction[0], -slope * direction[1], 0])))
        normal = self.node(material, "Normalize")
        self.connect(self.binary(material, "Add", gradient, self.vector(material, [0, 0, 1])), normal)
        self.property(normal, "NORMAL")

    def master(self, water, thin_surface=None):
        if thin_surface is not None and (water or thin_surface not in THIN_SURFACE_SCOPE):
            raise RuntimeError("Unsupported thin-surface optical master request")
        name = THIN_SURFACE_SCOPE[thin_surface]["master"] if thin_surface else "M_PoolWater" if water else "M_ThinGlass"
        source_family = thin_surface or (WATER if water else "real-bathroom-shower-glass")
        refraction = unreal.RefractionMode.RM_NONE if thin_surface else unreal.RefractionMode.RM_INDEX_OF_REFRACTION
        material = self.asset(name, unreal.Material, unreal.MaterialFactoryNew())
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE if water else unreal.BlendMode.BLEND_TRANSLUCENT)
        material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_SINGLE_LAYER_WATER if water else unreal.MaterialShadingModel.MSM_THIN_TRANSLUCENT)
        material.set_editor_property("two_sided", False)
        material.set_editor_property("tangent_space_normal", not water)
        material.set_editor_property("refraction_method", refraction)
        if water:
            material.set_editor_property("has_pixel_animation", True)
        else:
            material.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
            material.set_editor_property("screen_space_reflections", True)
        # Clear after property updates too: no editor-created or legacy custom
        # output may survive before the one authored below.
        removed = self.clear_graph(material)
        ior = self.ior_specular(material, 1.333 if water else 1.52)
        # RM_NONE only removes the scene-color distortion branch. The same
        # IndexOfRefraction parameter remains connected to Fresnel Specular.
        if not thin_surface:
            self.property(ior, "REFRACTION")
        self.property(self.scalar(material, 0), "METALLIC")
        self.property(self.vector(material, [0, 0, 0]), "BASE_COLOR")
        self.property(self.scalar(material, 0), "OPACITY")
        self.property(self.scalar(material, 0.035 if water else 0.025, "Roughness"), "ROUGHNESS")
        if water:
            output = self.node(material, "SingleLayerWaterMaterialOutput")
            for pin, values, parameter in (("ScatteringCoefficients", SCATTERING_PER_METRE, "ScatteringPerMetre"),
                                            ("AbsorptionCoefficients", ABSORPTION_PER_METRE, "AbsorptionPerMetre")):
                per_cm = self.binary(material, "Multiply", self.vector(material, values, parameter), self.scalar(material, 0.01))
                self.connect(per_cm, output, pin)
            self.connect(self.scalar(material, 0, "PhaseG"), output, "PhaseG")
            # Unit scale is deliberate: no painted or projected caustics claim.
            self.connect(self.vector(material, [1, 1, 1]), output, "ColorScaleBehindWater")
            self.water_normal(material)
        else:
            output = self.node(material, "ThinTranslucentMaterialOutput")
            self.connect(self.vector(material, [0.97, 0.985, 0.98], "TransmittanceColor"), output, "TransmittanceColor")
            self.connect(self.scalar(material, 1), output, "SurfaceCoverage")
        graph = self.validate_output(material, water, refraction)
        errors = list(self.lib.recompile_material(material))
        if errors:
            raise RuntimeError("Optical master graph compilation failed: " + "; ".join(str(e) for e in errors))
        self.save(material)
        if self.validate_output(material, water, refraction) != graph:
            raise RuntimeError("Optical graph topology changed during compile/save")
        self.report["masters"].append({"asset": material.get_path_name(), "shadingModel": "SingleLayerWater" if water else "ThinTranslucent",
                                       "compileErrors": errors, "removedExpressionCount": removed,
                                       "graph": graph, "saved": True, "refractionMethodNative": str(material.get_editor_property("refraction_method")),
                                       "refractionPolicy": "thin-surface-no-screen-offset-candidate" if thin_surface else "existing-index-of-refraction",
                                       "sourceFamily": source_family})
        return material

    def instance(self, slot, source, master):
        water = source["name"] == WATER
        name = "MI_" + slot + "_" + re.sub(r"[^A-Za-z0-9]", "_", source["name"])
        instance = self.asset(name, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        self.lib.set_material_instance_parent(instance, master)
        values = {"IndexOfRefraction": 1.333 if water else 1.52, "Roughness": source["roughness"]}
        scalar_names = {str(name) for name in self.lib.get_scalar_parameter_names(master)}
        for key, value in values.items():
            if key not in scalar_names:
                raise RuntimeError("Optical scalar parameter unavailable: " + key)
            # UE 5.8 MaterialEditingLibrary.cpp returns its initialized false
            # even after a successful scalar/vector write. Validate the named
            # parameter and effective getter value instead of that return value.
            self.lib.set_material_instance_scalar_parameter_value(instance, key, value)
        if not water:
            # Preserve source tint intent without treating GLB alpha as a measured
            # optical depth. This is a labelled initial visual approximation.
            tint = [max(0.001, min(1, 1 - source["alpha"] * (1 - channel))) for channel in source["color"]]
            if "TransmittanceColor" not in {str(name) for name in self.lib.get_vector_parameter_names(master)}:
                raise RuntimeError("Optical transmittance parameter unavailable")
            self.lib.set_material_instance_vector_parameter_value(instance, "TransmittanceColor", unreal.LinearColor(*tint, 1))
            actual = self.lib.get_material_instance_vector_parameter_value(instance, "TransmittanceColor")
            if any(not math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-7) for a, b in zip((actual.r, actual.g, actual.b), tint)):
                raise RuntimeError("Optical transmittance value did not persist")
            values["TransmittanceColor"] = tint
        self.lib.update_material_instance(instance)
        actual_parent = instance.get_editor_property("parent")
        expected_method = unreal.RefractionMode.RM_NONE if source["name"] in THIN_SURFACE_SCOPE else unreal.RefractionMode.RM_INDEX_OF_REFRACTION
        if actual_parent != master or actual_parent.get_editor_property("refraction_method") != expected_method:
            raise RuntimeError("Optical instance parent/refraction method did not persist: " + slot)
        for key in ("IndexOfRefraction", "Roughness"):
            actual = self.lib.get_material_instance_scalar_parameter_value(instance, key)
            if not math.isclose(actual, values[key], rel_tol=1e-6, abs_tol=1e-7):
                raise RuntimeError("Optical instance value did not persist: " + key)
        for key, value in {"source_material_slot": slot, "source_material_name": source["name"]}.items():
            unreal.EditorAssetLibrary.set_metadata_tag(instance, key, value)
        self.save(instance)
        self.report["instances"].append({"asset": instance.get_path_name(), "sourceSlot": slot, "sourceName": source["name"],
                                         "parameters": values, "saved": True, "parentMaster": actual_parent.get_path_name(),
                                         "refractionMethodNative": str(actual_parent.get_editor_property("refraction_method")),
                                         "refractionMethodReadback": "MaterialInstance parent Material.refraction_method; FMaterialResource::GetRefractionMode reads the base Material"})
        return instance


def apply_optics(scene_manifest, mesh_assets_by_id, output_dir):
    """Author the four canonical optical slot families; preserve mesh geometry.

    Receipt status distinguishes native graph/asset authoring from cooked Metal
    validation. Raising after any failure prevents a successful import receipt.
    """
    report_path = Path(output_dir) / "optics-report.json"
    report = {"schemaVersion": 1, "status": "pending", "namespace": CONTENT,
              "writerSha256": sha(__file__), "sourceCanonicalJsonSha256": digest(scene_manifest),
              "sourceLayout": scene_manifest["layoutId"], "masters": [], "instances": [], "assignments": [],
              "preservedAliases": [], "geometry": {}, "engineVersion": unreal.SystemLibrary.get_engine_version(),
              "primaryDocumentation": DOCS, "engineEvidenceHashes": {},
              "water": {"ior": 1.333, "waterLevelMm": -12, "footprintMm": [6000, 2700],
                        "absorptionPerMetre": ABSORPTION_PER_METRE, "scatteringPerMetre": SCATTERING_PER_METRE,
                        "nativeCoefficientUnit": "1/cm; per-metre parameters multiplied by 0.01",
                        "waves": WAVES, "displacement": False, "colorScaleBehindWater": [1, 1, 1],
                        "dynamicCaustics": False, "volumeDepth": "scene depth to existing canonical basin; no new volume mesh"},
              "verification": {"nativeGraphsCompiled": False, "nativeAssetsSaved": False, "geometryUnchanged": False,
                               "cookedMetalVerified": False, "photorealismVerified": False},
              "limitations": [
                  "Metal SM6 shader cooking and rendered reflection/refraction require a separate native runtime test.",
                  "SingleLayerWater uses scene color/depth; off-screen refraction and multiple overlapping water layers are limited.",
                  "No dynamic caustics are generated. ColorScaleBehindWater is exactly one.",
                  "Thin glass models surface transmission and Fresnel; canonical 24mm glazing assemblies are not measured multi-pane optical stacks.",
                  "Tint, absorption, scattering and ripple values are initial visual recipes, not measured product or water samples.",
                  "Proposed pool depth is a design value. Underwater camera/volumetric fog and spectral dispersion remain pending.",
                  "The sink water alias using a shower-glass source slot is preserved for a separate material revision.",
                  "Only 20 guarded architectural panes and the guarded stove pane use separate RM_NONE masters as a thin-surface A/B candidate; Fresnel IOR1.52, tint, roughness and geometry remain. This is not calibrated slab or multipane optics.",
                  "Flame blending, emission, animation, exposure and light intensity are unchanged for this glass-only comparison; dark flame silhouettes can remain for a later isolated revision.",
              ]}
    _receipt(report_path, report, "pending")
    rollback, changed = [], {}
    try:
        source_file = Path(output_dir) / "geometry/scene.json"
        if source_file.is_file():
            if json.loads(source_file.read_text()) != scene_manifest:
                raise RuntimeError("Optics scene argument differs from the adjacent source manifest")
            report["sourceSceneFileSha256"] = sha(source_file)
        engine = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.engine_dir()))
        report["engineEvidenceHashes"] = {path: sha(engine / path) for path in ENGINE_EVIDENCE}
        sources = scene_manifest["materials"]
        records = {record["id"]: record for record in scene_manifest["objects"]}
        bindings = []
        for object_id, mesh in sorted(mesh_assets_by_id.items()):
            record = records[object_id]
            if not any(sources[slot]["name"] in TARGETS for slot in record["materialSlots"]):
                continue
            if not mesh.get_path_name().startswith("/Game/Brezi/Geometry/"):
                raise RuntimeError("Optics cannot change an unowned mesh: " + mesh.get_path_name())
            if unreal.EditorAssetLibrary.get_metadata_tag(mesh, "source_object_id") != object_id:
                raise RuntimeError("Optical mesh source metadata differs: " + object_id)
            for index, static_slot in enumerate(mesh.get_editor_property("static_materials")):
                slot = _slot(static_slot, record, sources)
                name = sources[slot]["name"]
                if name not in TARGETS:
                    continue
                if name == "real-bathroom-shower-glass" and "UTILITY-SINK" in record["name"]:
                    report["preservedAliases"].append({"objectId": object_id, "sourceSlot": slot,
                        "reason": "Canonical source calls this a thin water layer; shared shower-glass slot is not glass identity."})
                    continue
                if mesh.get_editor_property("nanite_settings").get_editor_property("enabled"):
                    raise RuntimeError("Optical source unexpectedly uses Nanite; review mesh policy: " + object_id)
                if name == WATER:
                    _validate_pool(scene_manifest, record)
                bindings.append((object_id, mesh, index, slot))
                report["geometry"][object_id] = {"before": _geometry(mesh), "sourceBoundsMm": record["boundsMm"]}
        used = {slot for _, _, _, slot in bindings}
        if {sources[slot]["name"] for slot in used} != TARGETS:
            raise RuntimeError("Optics requires every canonical glass and pool family in the supplied runtime mesh map")
        if sum(sources[slot]["name"] == WATER for _, _, _, slot in bindings) != 1:
            raise RuntimeError("Expected exactly one canonical pool water mesh")
        report["thinSurfaceRevision"] = {"id": "NATIVE-THIN-SURFACE-RM-NONE-AB-20260908", "status": "candidate-native-readback-pending",
                                         "architecturalPaneCount": 20, "stovePaneCount": 1,
                                         "sourceBindings": _thin_surface_scope(bindings, records, sources),
                                         "fresnelIorPreserved": 1.52, "waterAndShowerPolicyChanged": False,
                                         "flameMaterialChanged": False, "calibratedPhysicalSlab": False}
        writer = OpticsWriter(report)
        masters = {WATER: writer.master(True), "real-bathroom-shower-glass": writer.master(False)}
        masters.update({name: writer.master(False, thin_surface=name) for name in THIN_SURFACE_SCOPE})
        instances = {slot: writer.instance(slot, sources[slot], masters[sources[slot]["name"]]) for slot in sorted(used)}
        for object_id, mesh, index, slot in bindings:
            rollback.append((mesh, index, mesh.get_material(index)))
            mesh.set_material(index, instances[slot])
            if mesh.get_material(index) != instances[slot]:
                raise RuntimeError("Optical slot assignment failed: " + object_id)
            changed[mesh.get_path_name()] = mesh
            report["assignments"].append({"objectId": object_id, "mesh": mesh.get_path_name(), "slotIndex": index,
                                          "sourceSlot": slot, "sourceId": records[object_id]["sourceId"],
                                          "material": instances[slot].get_path_name(),
                                          "parentMaster": instances[slot].get_editor_property("parent").get_path_name(),
                                          "refractionMethodNative": str(instances[slot].get_editor_property("parent").get_editor_property("refraction_method"))})
        for object_id, mesh, _, _ in bindings:
            after = _geometry(mesh)
            if report["geometry"][object_id]["before"] != after:
                raise RuntimeError("Optical authoring changed canonical mesh geometry: " + object_id)
            report["geometry"][object_id]["after"] = after
        for mesh in changed.values():
            if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
                raise RuntimeError("Could not save optical mesh binding: " + mesh.get_path_name())
        report["generatedAssetHashes"] = _hash_assets([entry["asset"] for entry in report["masters"] + report["instances"]])
        report["assignedMeshHashes"] = _hash_assets(changed.keys())
        report["authoredMasterCount"] = len(report["masters"])
        report["authoredInstanceCount"] = len(report["instances"])
        report["updatedMeshes"] = len(changed)
        report["nativeAuthoredSha256"] = digest({"writer": report["writerSha256"], "source": report["sourceCanonicalJsonSha256"],
            "engine": report["engineEvidenceHashes"], "generated": report["generatedAssetHashes"], "meshes": report["assignedMeshHashes"]})
        report["verification"].update(nativeGraphsCompiled=True, nativeAssetsSaved=True, geometryUnchanged=True)
        report["thinSurfaceRevision"]["status"] = "candidate-authored-native-getters-validated-render-pending"
        _receipt(report_path, report, "optics-authored")
        unreal.log("BREZI_OPTICS " + json.dumps({key: report[key] for key in ("status", "authoredMasterCount", "authoredInstanceCount", "updatedMeshes")}))
        return report
    except Exception as error:
        report["error"] = str(error)
        report["rollbackErrors"] = []
        for mesh, index, previous in reversed(rollback):
            try:
                mesh.set_material(index, previous)
            except Exception as rollback_error:
                report["rollbackErrors"].append(str(rollback_error))
        for mesh in changed.values():
            if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
                report["rollbackErrors"].append("Could not save restored slot: " + mesh.get_path_name())
        _receipt(report_path, report, "failed")
        raise
