"""Import the existing web Michelle rig into the isolated archviz profile.

Call apply_avatar(unreal, output_dir) after building the new Editor module, or
run this script in Unreal with BREZI_ARCHVIZ_OUTPUT pointing at that profile.
No source geometry, capsule, old package, engine content or shared pipeline is
modified. Native visual/animation/camera acceptance remains a separate run.
"""
import hashlib
import json
import os
import struct
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "/Game/Brezi/Avatar/Michelle"
OWNER = "scripts/unreal/archviz-avatar.py"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def source_asset(repo=ROOT):
    path = repo / "public/assets/avatar/avatar.glb"
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<III", data)
    require(magic == 0x46546C67 and version == 2 and length == len(data), "Invalid source avatar GLB")
    size, kind = struct.unpack_from("<II", data, 12)
    require(kind == 0x4E4F534A, "Avatar GLB requires JSON first")
    document = json.loads(data[20:20 + size])
    binary_offset = 20 + size
    binary_size, binary_kind = struct.unpack_from("<II", data, binary_offset)
    require(binary_kind == 0x004E4942, "Avatar GLB requires embedded binary")
    binary = data[binary_offset + 8:binary_offset + 8 + binary_size]
    names = [item.get("name") for item in document.get("animations", [])]
    require(sorted(names) == ["Idle", "Run", "Walk"], "Michelle must retain all three source locomotion clips")
    require(len(document.get("skins", [])) == 1 and len(document["skins"][0]["joints"]) >= 50,
            "Michelle must be the source skinned human, not replacement geometry")
    normal = next(image for image in document["images"] if "Normal" in image.get("name", ""))
    view = document["bufferViews"][normal["bufferView"]]
    offset = view.get("byteOffset", 0)
    normal_bytes = binary[offset:offset + view["byteLength"]]
    require(normal_bytes.startswith(b"\x89PNG\r\n\x1a\n"), "Source normal texture is not PNG")
    clips = {}
    for animation in document["animations"]:
        ranges = [document["accessors"][sampler["input"]] for sampler in animation["samplers"]]
        duration = max(float(accessor["max"][0]) for accessor in ranges) - min(float(accessor["min"][0]) for accessor in ranges)
        require(duration > .2, "Source animation has no meaningful duration")
        clips[animation["name"]] = {"durationSeconds": duration, "channels": len(animation["channels"])}
    return path, normal_bytes, {"id": "michelle", "model": str(path.relative_to(repo)),
        "modelSha256": hashlib.sha256(data).hexdigest(), "boneCount": len(document["skins"][0]["joints"]),
        "clips": clips, "visualHeightCm": 170, "collisionOwner": "unchanged native walking capsule"}


def apply_avatar(unreal, output_dir):
    output = Path(output_dir).resolve()
    expected_project = output / "Project/BreziTwin"
    actual_project = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
    require(actual_project == expected_project, "Avatar import must run in the selected isolated archviz project")
    report_path = output / "avatar-import-report.json"
    report = {"schemaVersion": 1, "status": "pending", "owner": OWNER,
              "project": str(actual_project), "prefix": PREFIX,
              "nativeVisualVerified": False, "nativeLocomotionVerified": False}

    def write(status):
        report.update(status=status, generatedAt=datetime.now(timezone.utc).isoformat())
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    try:
        glb, normal_bytes, source = source_asset()
        report["source"] = source
        diffuse = ROOT / "public/assets/avatar/michelle-light-diffuse.png"
        report["source"]["diffuseSha256"] = hashlib.sha256(diffuse.read_bytes()).hexdigest()
        assets = unreal.EditorAssetLibrary
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        registry = unreal.AssetRegistryHelpers.get_asset_registry()
        registry.scan_paths_synchronous([PREFIX, "/Interchange/Pipelines"], force_rescan=True)
        for path in assets.list_assets(PREFIX, recursive=True, include_folder=False):
            require(str(assets.get_metadata_tag(assets.load_asset(path), "BreziGeneratedBy")) == OWNER,
                    "Refusing to overwrite an unowned avatar asset: " + path)

        def save(asset):
            require(asset is not None, "Native avatar asset creation failed")
            assets.set_metadata_tag(asset, "BreziGeneratedBy", OWNER)
            require(assets.save_loaded_asset(asset, only_if_is_dirty=False), "Could not save " + asset.get_path_name())
            return asset

        def load_or_duplicate(source_path, target):
            return assets.load_asset(target) if assets.does_asset_exist(target) else assets.duplicate_asset(source_path, target)

        pipeline = load_or_duplicate("/Interchange/Pipelines/DefaultGLTFSceneAssetsPipeline.DefaultGLTFSceneAssetsPipeline", PREFIX + "/Pipeline/GLTFAssets")
        require(pipeline is not None, "Missing owned GLTF asset pipeline")
        pipeline.set_editor_property("use_source_name_for_asset", False)
        mesh_pipeline = pipeline.get_editor_property("mesh_pipeline")
        mesh_pipeline.set_editor_property("import_static_meshes", False)
        mesh_pipeline.set_editor_property("import_skeletal_meshes", True)
        mesh_pipeline.set_editor_property("create_physics_asset", False)
        animation_pipeline = pipeline.get_editor_property("animation_pipeline")
        animation_pipeline.set_editor_property("import_animations", True)
        animation_pipeline.set_editor_property("import_bone_tracks", True)
        animation_pipeline.set_editor_property("use30_hz_to_bake_bone_animation", True)
        save(pipeline)
        manager = unreal.InterchangeManager.get_interchange_manager_scripted()
        parameters = unreal.ImportAssetParameters()
        for key, value in {"is_automated": True, "replace_existing": True, "force_show_dialog": False,
                           "override_pipelines": [unreal.SoftObjectPath(pipeline.get_path_name())]}.items():
            parameters.set_editor_property(key, value)
        require(manager.import_asset(PREFIX + "/Imported", manager.create_source_data(str(glb)), parameters),
                "Interchange skeletal avatar import failed")
        registry.scan_paths_synchronous([PREFIX], force_rescan=True)
        imported = [assets.load_asset(path) for path in assets.list_assets(PREFIX + "/Imported", recursive=True, include_folder=False)]
        meshes = [asset for asset in imported if isinstance(asset, unreal.SkeletalMesh)]
        animations = [asset for asset in imported if isinstance(asset, unreal.AnimSequence)]
        require(len(meshes) == 1, "Expected exactly the one source Michelle skeletal mesh")
        for asset in imported:
            save(asset)
        mesh = load_or_duplicate(meshes[0].get_path_name(), PREFIX + "/SK_Michelle")
        native_clips = {}
        for clip in ("Idle", "Walk", "Run"):
            matches = [asset for asset in animations if clip.lower() in asset.get_name().lower()]
            require(len(matches) == 1, "Missing or ambiguous native source animation: " + clip)
            native_clips[clip] = matches[0]
            native_clips[clip].set_editor_property("enable_root_motion", False)
            native_clips[clip].set_editor_property("force_root_lock", True)
            save(native_clips[clip])
        bounds = mesh.get_bounds()
        height = float(bounds.box_extent.z) * 2
        require(80 <= height <= 250, "Imported skeletal height has incorrect axes or units: " + str(height))
        report["importedMeshHeightCm"] = height

        source_dir = output / "avatar-source"
        source_dir.mkdir(exist_ok=True)
        normal_path = source_dir / "michelle-normal.png"
        normal_path.write_bytes(normal_bytes)

        def texture(path, name, normal=False):
            task = unreal.AssetImportTask()
            for key, value in {"filename": str(path), "destination_path": PREFIX + "/Textures",
                               "destination_name": name, "automated": True, "replace_existing": True, "save": True}.items():
                task.set_editor_property(key, value)
            tools.import_asset_tasks([task])
            asset = assets.load_asset(PREFIX + "/Textures/" + name)
            require(isinstance(asset, unreal.Texture2D), "Avatar texture import failed")
            asset.set_editor_property("srgb", not normal)
            if normal:
                asset.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
                # glTF tangents use the opposite green-channel convention;
                # mirror InterchangeGltfTranslator's normal texture setting.
                asset.set_editor_property("flip_green_channel", True)
            return save(asset)

        albedo = texture(diffuse, "T_Michelle_Light")
        normal = texture(normal_path, "T_Michelle_Normal", True)
        material_path = PREFIX + "/M_Michelle"
        material = assets.load_asset(material_path) if assets.does_asset_exist(material_path) else tools.create_asset(
            "M_Michelle", PREFIX, unreal.Material, unreal.MaterialFactoryNew())
        require(material is not None, "Avatar material creation failed")
        lib = unreal.MaterialEditingLibrary
        lib.delete_all_material_expressions(material)
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        material.set_editor_property("two_sided", True)

        def node(kind, **properties):
            expression = lib.create_material_expression(material, kind, -400, 0)
            for key, value in properties.items():
                expression.set_editor_property(key, value)
            return expression

        diffuse_node = node(unreal.MaterialExpressionTextureSample, texture=albedo, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
        normal_node = node(unreal.MaterialExpressionTextureSample, texture=normal, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        require(lib.connect_material_property(diffuse_node, "RGB", unreal.MaterialProperty.MP_BASE_COLOR), "Missing avatar albedo binding")
        require(lib.connect_material_property(normal_node, "RGB", unreal.MaterialProperty.MP_NORMAL), "Missing avatar normal binding")
        for property_, value in ((unreal.MaterialProperty.MP_ROUGHNESS, .78), (unreal.MaterialProperty.MP_METALLIC, 0), (unreal.MaterialProperty.MP_SPECULAR, .3)):
            require(lib.connect_material_property(node(unreal.MaterialExpressionConstant, r=value), "", property_), "Missing avatar surface parameter")
        opacity = node(unreal.MaterialExpressionScalarParameter, parameter_name="AvatarOpacity", default_value=1)
        dither = node(unreal.MaterialExpressionMaterialFunctionCall)
        # Installed engine functions need not be indexed by the commandlet's
        # AssetRegistry. Load the verified package/object directly, as the other
        # native material importers do for WorldAlignedTexture/Normal.
        fade_path = "/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.DitherTemporalAA"
        fade_function = unreal.load_object(None, fade_path)
        require(fade_function is not None, "Missing installed temporal avatar fade package: " + fade_path)
        require(dither.set_material_function(fade_function), "Could not bind native temporal avatar fade")
        report["fadeFunction"] = fade_function.get_path_name()
        pins = [str(pin) for pin in lib.get_material_expression_input_names(dither)]
        alpha = next((pin for pin in pins if "alpha" in pin.lower()), None)
        require(alpha and lib.connect_material_expressions(opacity, "", dither, alpha), "Could not wire the avatar fade input")
        require(lib.connect_material_property(dither, "", unreal.MaterialProperty.MP_OPACITY_MASK), "Missing avatar fade output")
        lib.set_base_material_usage(material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH, True)
        require(not list(lib.recompile_material(material)), "Native avatar material compilation failed")
        require(lib.has_material_usage(material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH),
                "Avatar material is missing its cooked skeletal-mesh shader permutation")
        save(material)
        slots = mesh.get_editor_property("materials")
        require(len(slots) == 1, "Michelle must retain the one source body material slot")
        slot = slots[0]
        slot.set_editor_property("material_interface", material)
        slots[0] = slot
        mesh.set_editor_property("materials", slots)
        save(mesh)
        saved_slots = mesh.get_editor_property("materials")
        require(len(saved_slots) == 1 and saved_slots[0].get_editor_property("material_interface") == material,
                "Saved Michelle body slot is not bound to the owned light material")
        blend = unreal.BreziAvatarBlendSpace.create_locomotion_asset(PREFIX + "/BS_Locomotion",
            native_clips["Idle"], native_clips["Walk"], native_clips["Run"])
        require(blend is not None, "Native blendspace rejected the source skeleton or animation durations")
        save(blend)
        registry.scan_paths_synchronous([PREFIX], force_rescan=True)
        report["assets"] = {"mesh": mesh.get_path_name(), "material": material.get_path_name(),
                            "blendspace": blend.get_path_name(),
                            "animations": {key: value.get_path_name() for key, value in native_clips.items()}}
        report["nativeClipLengthsSeconds"] = {key: float(value.get_play_length()) for key, value in native_clips.items()}
        for name, duration in report["nativeClipLengthsSeconds"].items():
            require(abs(duration - source["clips"][name]["durationSeconds"]) < .1,
                    "Imported animation duration differs from source: " + name)
        report["cookDirectory"] = "/Game/Brezi/Avatar"
        report["normalGreenFlipped"] = bool(normal.get_editor_property("flip_green_channel"))
        require(report["normalGreenFlipped"], "Saved avatar normal convention differs from glTF import")
        report["verification"] = "Imported skeletal asset, matching native clips and material saved; rendered body, animation and swept camera require native app review."
        write("avatar-import-validated")
        return report
    except Exception as error:
        report["error"] = str(error)
        write("failed")
        raise


if __name__ == "__main__":
    import unreal
    apply_avatar(unreal, os.environ.get("BREZI_ARCHVIZ_OUTPUT", ROOT / "output/unreal/archviz-game-20260922"))
