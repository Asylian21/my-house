"""Generate the native Brezi map using UE 5.8 Interchange, then measure every mesh.

Run with UnrealEditor-Cmd <project> -run=pythonscript -script=<this file>
    -unattended -nosplash -nullrhi
BREZI_GEOMETRY selects the validated bridge directory. This script never imports
brezi-archive.glb. NullRHI validation proves geometry/assets only, not rendering.
"""
import hashlib
import json
import math
import os
import re
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/unreal"))
GEOMETRY = Path(os.environ.get("BREZI_GEOMETRY", ROOT / "output/unreal/geometry")).resolve()
REPORT_PATH = GEOMETRY.parent / "import-report.json"
MAP_PATH = "/Game/Brezi/Maps/Brezi"
CONTENT_PATH = "/Game/Brezi/Geometry"
GENERATED_TAG = "BreziGenerated"
TOLERANCE_CM = 0.05  # 0.5 mm; measured after native engine import, no fitting.
REPORT = {
    "schemaVersion": 1, "status": "pending", "generatedAt": None,
    "map": MAP_PATH, "source": "brezi-twin.glb", "archiveImported": False,
    "verification": {"nativeGeometryMeasured": False, "visualQualityVerified": False,
                     "native4KFrameRateMeasured": False},
    "limitations": [
        "Native material and optical graphs require cooked Metal visual acceptance; dynamic water caustics remain pending.",
        "Source camera-occluder/walk-surface triangles provide static collision; door interaction parity is pending.",
        "A successful import is not a rendered frame, packaged app, photorealism or statutory approval.",
    ],
}


def write_report(status):
    REPORT["status"] = status
    REPORT["generatedAt"] = datetime.now(timezone.utc).isoformat()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = REPORT_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(REPORT, ensure_ascii=False, indent=2) + "\n")
    temp.replace(REPORT_PATH)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(name):
    return json.loads((GEOMETRY / name).read_text())


def verify_inputs():
    scene = read_json("scene.json")
    bridge = read_json("bridge-report.json")
    receipt = read_json("validation.json")
    if receipt.get("status") != "geometry-validated":
        raise RuntimeError("The bridge has no successful current geometry validation")
    if sha(GEOMETRY / "walking.json") != receipt.get("walkingSha256"):
        raise RuntimeError("Walking contract changed after geometry validation")
    if sha(GEOMETRY / "scene.json") != bridge["sceneSha256"]:
        raise RuntimeError("Source manifest changed after conversion")
    if sha(GEOMETRY / "brezi-twin.glb") != bridge["files"]["brezi-twin.glb"]["sha256"]:
        raise RuntimeError("Runtime GLB checksum mismatch")
    for name, digest in {**bridge["sourceFiles"], **bridge["pipelineFiles"]}.items():
        if sha(ROOT / name) != digest:
            raise RuntimeError("Source changed after geometry validation: " + name)
    runtime_ids = set(bridge["files"]["brezi-twin.glb"]["objectIds"])
    archive_ids = set(bridge["files"]["brezi-archive.glb"]["objectIds"])
    if runtime_ids & archive_ids:
        raise RuntimeError("Runtime/archive object identities overlap")
    raw = (GEOMETRY / "brezi-twin.glb").read_bytes()
    if raw[:4] != b"glTF" or struct.unpack_from("<I", raw, 4)[0] != 2:
        raise RuntimeError("Expected a glTF 2 binary")
    chunk_length, chunk_type = struct.unpack_from("<II", raw, 12)
    if chunk_type != 0x4E4F534A:
        raise RuntimeError("GLB JSON chunk missing")
    gltf = json.loads(raw[20:20 + chunk_length])
    gltf_ids = [node.get("extras", {}).get("source_object_id")
                for node in gltf["nodes"] if "mesh" in node]
    if set(gltf_ids) != runtime_ids or len(gltf_ids) != len(runtime_ids):
        raise RuntimeError("GLB logical object set differs from bridge")
    records = {record["id"]: record for record in scene["objects"] if record["id"] in runtime_ids}
    if len(records) != len(runtime_ids):
        raise RuntimeError("Runtime object is absent from source manifest")
    REPORT.update({"sourceCommit": scene["sourceCommit"], "layoutId": scene["layoutId"],
                   "sourceGlbSha256": sha(GEOMETRY / "brezi-twin.glb"),
                   "sourceManifestSha256": bridge["sceneSha256"],
                   "viewpointsSha256": sha(GEOMETRY / "viewpoints.json"), "expectedObjects": len(records),
                   "walkingSha256": sha(GEOMETRY / "walking.json"),
                   "excludedArchiveObjects": len(archive_ids),
                   "coordinateMapping": "glTF metres [x,y,z] -> UE cm [100*x,100*z,100*y]; source OBJ mm [x,y,z] -> UE cm [x/10,-y/10,z/10]",
                   "boundsToleranceCm": TOLERANCE_CM,
                   "pipelineFiles": {"scripts/unreal/import_scene.py": sha(Path(__file__)),
                                     "scripts/unreal/walking.mjs": sha(ROOT / "scripts/unreal/walking.mjs"),
                                     "scripts/unreal/oak_reimport.py": sha(ROOT / "scripts/unreal/oak_reimport.py")},
                   "engineVersion": unreal.SystemLibrary.get_engine_version()})
    return scene, bridge, records, archive_ids


def generated(actor, label=None):
    actor.set_editor_property("tags", [*actor.get_editor_property("tags"), unreal.Name(GENERATED_TAG)])
    if label:
        actor.set_actor_label(label)
    return actor


def prepare_world(actor_system, level_system, scene):
    # Repeated exports preserve manual actors; only our tagged generated actors
    # are replaced. Refuse to repurpose an unrelated pre-existing map.
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        asset = unreal.EditorAssetLibrary.load_asset(MAP_PATH)
        owner = unreal.EditorAssetLibrary.get_metadata_tag(asset, "BreziGeneratedBy")
        if owner != "scripts/unreal/import_scene.py":
            raise RuntimeError("Existing Brezi map is not owned by this generator")
        if not level_system.load_level(MAP_PATH):
            raise RuntimeError("Could not load generated Brezi map")
        from oak_reimport import preflight, destroy_with_cleanup
        actors = list(actor_system.get_all_level_actors())
        from lawn_ground import preflight_reimport as preflight_lawn_ground
        REPORT["lawnGroundPreDelete"] = preflight_lawn_ground(unreal, actors, scene, GEOMETRY)
        from mulch import preflight_reimport as preflight_mulch
        REPORT["mulchPreDelete"] = preflight_mulch(unreal, actors, scene, GEOMETRY)
        from ornamental import preflight_reimport as preflight_ornamental
        REPORT["ornamentalPreDelete"] = preflight_ornamental(unreal, actors, scene, GEOMETRY)
        from plaster import preflight_reimport as preflight_plaster
        REPORT["facadePlasterPreDelete"] = preflight_plaster(unreal, actors, scene, GEOMETRY)
        from coping import preflight_reimport as preflight_pool_coping
        REPORT["poolCopingPreDelete"] = preflight_pool_coping(unreal, actors, scene, GEOMETRY)
        oak_plans = preflight(unreal, actors, scene, GEOMETRY)
        from pendant_emitter import preflight_reimport, destroy_reimport_actor
        pendant_plan = preflight_reimport(unreal, actors, scene, GEOMETRY)
        if pendant_plan and pendant_plan["actor"] in oak_plans:
            raise RuntimeError("Pendant and oak destruction scopes overlap")
        REPORT["pendantActorCleanup"] = {"preflightVerified": True, "actor": pendant_plan["actor"] if pendant_plan else None,
                                         "sourceGeometryProof": pendant_plan["sourceGeometryProof"] if pendant_plan else None,
                                         "scope": "DOM_01375 pendant ownership pair only"}
        REPORT["oakActorCleanup"] = {"preflightVerified": True, "sourceIds": sorted(p["id"] for p in oak_plans.values()),
                                     "scope": "actor oak ownership keys only; no material or geometry repair"}
        for actor in actors:
            if actor.actor_has_tag(GENERATED_TAG):
                if pendant_plan and actor.get_path_name() == pendant_plan["actor"]:
                    destroy_reimport_actor(unreal.EditorAssetLibrary, actor_system, actor, pendant_plan)
                else:
                    destroy_with_cleanup(unreal.EditorAssetLibrary, actor_system, actor, oak_plans.get(actor.get_path_name()))
    elif not level_system.new_level(MAP_PATH):
        raise RuntimeError("Could not create Brezi map")
    world = unreal.EditorLevelLibrary.get_editor_world()
    unreal.EditorAssetLibrary.set_metadata_tag(world, "BreziGeneratedBy", "scripts/unreal/import_scene.py")
    if not level_system.save_current_level():
        raise RuntimeError("Could not save generated map ownership")


def pipeline_copy(source_name, name):
    source = "/Interchange/Pipelines/" + source_name + "." + source_name
    path = "/Game/Brezi/Pipeline/" + name
    asset = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else unreal.EditorAssetLibrary.duplicate_asset(source, path)
    if not asset:
        raise RuntimeError("Required Interchange pipeline unavailable: " + source_name)
    return asset


def import_geometry(actor_system, level_system):
    assets = pipeline_copy("DefaultGLTFSceneAssetsPipeline", "GLTFSceneAssets")
    gltf = pipeline_copy("DefaultGLTFPipeline", "GLTFMaterials")
    level = pipeline_copy("DefaultSceneLevelPipeline", "LevelActors")
    mesh_pipeline = assets.get_editor_property("mesh_pipeline")
    mesh_pipeline.set_editor_property("combine_static_meshes_behavior", unreal.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE)
    mesh_pipeline.set_editor_property("collision", False)
    mesh_pipeline.set_editor_property("build_nanite", False)  # selected opaque detailed meshes below
    mesh_pipeline.set_editor_property("generate_lightmap_u_vs", False)
    level.set_editor_property("scene_hierarchy_type", unreal.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
    for asset in (assets, gltf, level):
        if not unreal.EditorAssetLibrary.save_loaded_asset(asset):
            raise RuntimeError("Could not save generated import pipeline")
    params = unreal.ImportAssetParameters()
    params.set_editor_property("is_automated", True)
    params.set_editor_property("replace_existing", True)
    params.set_editor_property("force_show_dialog", False)
    params.set_editor_property("override_pipelines", [unreal.SoftObjectPath(p.get_path_name()) for p in (assets, gltf, level)])
    params.set_editor_property("import_level", level_system.get_current_level())
    manager = unreal.InterchangeManager.get_interchange_manager_scripted()
    data = manager.create_source_data(str(GEOMETRY / "brezi-twin.glb"))
    before = {actor.get_path_name() for actor in actor_system.get_all_level_actors()}
    if not manager.import_scene(CONTENT_PATH, data, params):
        raise RuntimeError("Synchronous Interchange import_scene returned false")
    actors = [actor for actor in actor_system.get_all_level_actors() if actor.get_path_name() not in before]
    for actor in actors:
        generated(actor)
    if not actors:
        raise RuntimeError("Interchange created no scene actors")
    return actors, before


def source_id(actor, component, records):
    mesh = component.get_editor_property("static_mesh")
    candidates = [actor.get_actor_label(), actor.get_name(), component.get_name(), mesh.get_name()]
    matches = set()
    for candidate in candidates:
        if candidate in records:
            matches.add(candidate)
        for found in re.findall(r"(?<![A-Za-z0-9])DOM_\d+(?!\d)", candidate):
            if found in records:
                matches.add(found)
    if len(matches) != 1:
        raise RuntimeError("Cannot uniquely resolve source identity for imported actor: " + actor.get_actor_label())
    return matches.pop()


def tuple3(vector):
    return [float(vector.x), float(vector.y), float(vector.z)]


def source_bounds_cm(record):
    low, high = record["boundsMm"]["min"], record["boundsMm"]["max"]
    return {"min": [low[0] / 10, -high[1] / 10, low[2] / 10],
            "max": [high[0] / 10, -low[1] / 10, high[2] / 10]}


def measured_bounds_cm(component):
    origin, extent, _ = unreal.SystemLibrary.get_component_bounds(component)
    return {"min": tuple3(origin - extent), "max": tuple3(origin + extent)}


def configure_and_measure(actors, records, bridge, archive_ids):
    objects, found, max_error, collisions, nanite_count = [], set(), 0.0, 0, 0
    assets_to_save, assets_by_id = {}, {}
    for actor in actors:
        components = actor.get_components_by_class(unreal.StaticMeshComponent)
        for component in components:
            mesh = component.get_editor_property("static_mesh")
            if not mesh:
                continue
            id_ = source_id(actor, component, records)
            if id_ in found or id_ in archive_ids:
                raise RuntimeError("Duplicate or archived logical object in runtime map: " + id_)
            found.add(id_)
            record = records[id_]
            actual, expected = measured_bounds_cm(component), source_bounds_cm(record)
            errors = [abs(actual[key][axis] - expected[key][axis]) for key in ("min", "max") for axis in range(3)]
            error = max(errors)
            if not all(math.isfinite(v) for v in errors) or error > TOLERANCE_CM:
                raise RuntimeError(f"{id_}: native world bounds differ by {error:.6f} cm (limit {TOLERANCE_CM})")
            max_error = max(max_error, error)
            metadata = record.get("metadata") or {}
            # Exact imported triangles, with no synthesized boxes or convex hulls.
            collide = bool(metadata.get("babylonCheckCollisions") or metadata.get("walkSurface")
                           or metadata.get("cameraOccluder")) and not bool(metadata.get("doorMotion")
                           or metadata.get("dynamicCameraOccluder"))
            if collide:
                body = mesh.get_editor_property("body_setup")
                if not body:
                    raise RuntimeError("Static mesh has no body setup: " + id_)
                body.set_editor_property("never_needs_cooked_collision_data", False)
                body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
                component.set_collision_profile_name("BlockAll")
                component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
                component.set_mobility(unreal.ComponentMobility.STATIC)
                collisions += 1
            else:
                # A Custom profile can reload the mesh's external default body
                # during later editor changes. Persist an explicit named profile.
                component.set_collision_profile_name("NoCollision")
                component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            opaque = all(bridge["materials"][slot]["alpha"] >= 0.999 for slot in record["materialSlots"])
            nanite = opaque and record["triangles"] >= 512 and not metadata.get("doorMotion")
            if nanite:
                settings = mesh.get_editor_property("nanite_settings")
                settings.set_editor_property("enabled", True)
                # Preserve the normal fallback; Auto substitutes a build-time error
                # even when the stored relative error is zero. Dedicated RT proxy
                # selection/topology remains a separate runtime verification.
                settings.set_editor_property("fallback_target", unreal.NaniteFallbackTarget.PERCENT_TRIANGLES)
                settings.set_editor_property("fallback_percent_triangles", 1.0)
                settings.set_editor_property("fallback_relative_error", 0.0)
                # The UI StaticMeshEditorSubsystem is absent in a commandlet.
                # Reflected property writes invoke PostEditChangeProperty and
                # rebuild the asset without requiring an interactive mesh editor.
                mesh.set_editor_property("nanite_settings", settings)
                observed = mesh.get_editor_property("nanite_settings")
                if (observed.get_editor_property("fallback_target") != unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
                    or float(observed.get_editor_property("fallback_percent_triangles")) != 1.0
                    or float(observed.get_editor_property("fallback_relative_error")) != 0.0):
                    raise RuntimeError("Full normal Nanite fallback policy readback differs: " + id_)
                nanite_count += 1
            actor.set_actor_label(id_ + " · " + record["name"])
            actor.set_folder_path("Brezi/" + record["group"])
            actor.set_editor_property("tags", [*actor.get_editor_property("tags"), unreal.Name(id_), unreal.Name("BreziGroup_" + record["group"])])
            for key, value in {"source_object_id": id_, "source_id": record["sourceId"],
                               "source_group": record["group"], "source_name": record["name"]}.items():
                unreal.EditorAssetLibrary.set_metadata_tag(mesh, key, str(value))
            assets_to_save[mesh.get_path_name()] = mesh
            assets_by_id[id_] = mesh
            objects.append({"id": id_, "group": record["group"], "asset": mesh.get_path_name(),
                            "sourceBoundsCm": expected, "nativeWorldBoundsCm": actual, "maxErrorCm": error,
                            "initialCollision": "source-triangles-complex-as-simple" if collide else "disabled",
                            "sourceBabylonCheckCollisions": metadata.get("babylonCheckCollisions"),
                            "collision": "source-triangles-complex-as-simple" if collide else "disabled",
                            "naniteEnabled": nanite,
                            "normalFallbackPolicy": {"target": str(observed.get_editor_property("fallback_target")),
                                "percentTriangles": float(observed.get_editor_property("fallback_percent_triangles")),
                                "relativeError": float(observed.get_editor_property("fallback_relative_error")),
                                "method": "native getters after reflected update/rebuild; not dedicated RT proxy proof"} if nanite else None,
                            "rayTracingProxyTopologyVerified": False})
    if found != set(records):
        raise RuntimeError("Missing native logical objects: " + ", ".join(sorted(set(records) - found)[:15]))
    for mesh in assets_to_save.values():
        if not unreal.EditorAssetLibrary.save_loaded_asset(mesh):
            raise RuntimeError("Failed to save static mesh: " + mesh.get_name())
    REPORT.update({"importedObjects": len(found), "initialStaticCollisionObjects": collisions,
                   "staticCollisionObjects": collisions, "naniteObjects": nanite_count,
                   "maxWorldBoundsErrorCm": max_error, "objects": sorted(objects, key=lambda r: r["id"])})
    REPORT["verification"]["nativeGeometryMeasured"] = True
    return assets_by_id


def measure_final_collision(actor_system):
    """Measure persisted collision after every authoring pass, including doors."""
    records = {record["id"]: record for record in REPORT["objects"]}
    required = {id_ for id_, record in records.items() if record["initialCollision"] != "disabled"}
    for key in ("staticBlockers", "closedBlockers"):
        required.update(entry["objectId"] for entry in REPORT["walking"].get(key, []))
    support_paths = {entry["component"] for entry in REPORT["walking"].get("supports", [])}
    found, supports, enabled, errors = set(), set(), 0, []
    for actor in actor_system.get_all_level_actors():
        ids = {str(tag) for tag in actor.get_editor_property("tags")} & records.keys()
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            path = component.get_path_name()
            if not ids and path not in support_paths:
                continue
            mode = component.get_collision_enabled()
            blocks = mode == unreal.CollisionEnabled.QUERY_AND_PHYSICS
            if mode not in (unreal.CollisionEnabled.NO_COLLISION, unreal.CollisionEnabled.QUERY_AND_PHYSICS):
                raise RuntimeError("Unexpected final collision mode: " + path)
            if blocks:
                mesh = component.get_editor_property("static_mesh")
                body = mesh.get_editor_property("body_setup") if mesh else None
                trace = body.get_editor_property("collision_trace_flag") if body else None
                response = component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)
                # UE can relabel a profile as Custom after enabling collision.
                # Actual query response and triangle mode determine walking.
                if trace != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE or response != unreal.CollisionResponseType.ECR_BLOCK:
                    errors.append({"sourceIds": sorted(ids), "component": path, "mesh": mesh.get_path_name() if mesh else None,
                                   "trace": str(trace), "profile": str(component.get_collision_profile_name()), "pawn": str(response)})
            if path in support_paths:
                if not blocks:
                    raise RuntimeError("Translated walking support lost collision: " + path)
                supports.add(path)
                continue
            if len(ids) != 1:
                raise RuntimeError("Ambiguous final collision source identity: " + path)
            id_ = next(iter(ids))
            if id_ in found:
                raise RuntimeError("Duplicate final collision component: " + id_)
            found.add(id_)
            if id_ in required and not blocks:
                raise RuntimeError("Required source collider was disabled by a later authoring pass: " + id_)
            records[id_]["collision"] = "source-triangles-complex-as-simple" if blocks else "disabled"
            records[id_]["finalCollisionMode"] = str(mode)
            records[id_]["finalCollisionProfile"] = str(component.get_collision_profile_name())
            records[id_]["finalPawnResponse"] = str(component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN))
            enabled += int(blocks)
    if found != records.keys() or supports != support_paths:
        raise RuntimeError("Final collision measurement did not cover every source and support")
    REPORT.update({"staticCollisionObjects": enabled, "supportCollisionObjects": len(supports),
                   "finalCollisionComponents": enabled + len(supports),
                   "collisionMeasurementStage": "after-all-native-authoring"})
    REPORT["collisionValidationErrors"] = errors
    if errors:
        raise RuntimeError(f"{len(errors)} final colliders no longer use blocking source triangles; "
                           f"first={errors[0]}")


def sun_rotation(pitch_yaw_roll):
    if len(pitch_yaw_roll) != 3 or not all(math.isfinite(float(v)) for v in pitch_yaw_roll):
        raise RuntimeError("Solar rotation must contain finite pitch, yaw and roll degrees")
    pitch, yaw, roll = map(float, pitch_yaw_roll)
    # The UE Python positional constructor is (roll, pitch, yaw), unlike the
    # source sidecar and C++ FRotator. Named arguments preserve the solar frame.
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll)


def validate_sun_rotation(actor, source_degrees):
    rotation = actor.get_actor_rotation()
    actual = [float(rotation.pitch), float(rotation.yaw), float(rotation.roll)]
    angle_errors = [abs((value - expected + 180.0) % 360.0 - 180.0)
                    for value, expected in zip(actual, source_degrees)]
    if max(angle_errors) > 0.001:
        raise RuntimeError(f"Native solar rotation differs from source: {actual} != {source_degrees}")
    pitch, yaw = map(math.radians, source_degrees[:2])
    expected_forward = [math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)]
    forward = tuple3(actor.get_actor_forward_vector())
    if max(abs(value - expected) for value, expected in zip(forward, expected_forward)) > 0.00001:
        raise RuntimeError("Native directional light vector differs from the source solar direction")
    return actual, forward


def lighting(actor_system, views):
    zero = unreal.Vector(0, 0, 0)
    sun_data = views["sun"]
    sun = generated(actor_system.spawn_actor_from_class(unreal.DirectionalLight, zero,
        sun_rotation(sun_data["dayRotationDegrees"])), "Slnko · Březí")
    actual_rotation, actual_forward = validate_sun_rotation(sun, sun_data["dayRotationDegrees"])
    sun.set_editor_property("tags", [*sun.get_editor_property("tags"), unreal.Name("BreziSun")])
    light = sun.get_component_by_class(unreal.DirectionalLightComponent)
    light.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.set_intensity(float(sun_data["dayLux"]))
    light.set_atmosphere_sun_light(True)
    atmosphere = generated(actor_system.spawn_actor_from_class(unreal.SkyAtmosphere, zero), "Obloha · fyzikálna atmosféra")
    atmosphere.get_component_by_class(unreal.SkyAtmosphereComponent).set_mobility(unreal.ComponentMobility.MOVABLE)
    sky = generated(actor_system.spawn_actor_from_class(unreal.SkyLight, zero), "Obloha · nepriame svetlo")
    sky.set_editor_property("tags", [*sky.get_editor_property("tags"), unreal.Name("BreziSky")])
    sky_light = sky.get_component_by_class(unreal.SkyLightComponent)
    sky_light.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky_light.set_real_time_capture(True)
    sky_light.set_intensity(1.0)
    post = generated(actor_system.spawn_actor_from_class(unreal.PostProcessVolume, zero), "Expozícia · interiér a exteriér")
    post.set_editor_property("unbound", True)
    settings = post.get_editor_property("settings")
    values = {"auto_exposure_method": unreal.AutoExposureMethod.AEM_HISTOGRAM,
              "auto_exposure_min_brightness": -4.0, "auto_exposure_max_brightness": 16.0,
              "auto_exposure_bias": 0.0, "auto_exposure_speed_up": 3.0, "auto_exposure_speed_down": 1.0,
              "motion_blur_amount": 0.0}
    for key, value in values.items():
        settings.set_editor_property("override_" + key, True)
        settings.set_editor_property(key, value)
    post.set_editor_property("settings", settings)
    for actor in (sun, atmosphere, sky, post):
        actor.set_folder_path("Brezi/Environment")
    REPORT["lighting"] = {"directionalLux": float(light.get_editor_property("intensity")),
                          "sunRotationDegrees": actual_rotation, "sourceSunRotationDegrees": sun_data["dayRotationDegrees"],
                          "nativeSunForwardVector": actual_forward, "sunRotationValidated": True,
                          "dateTime": sun_data["dateTime"], "geolocation": sun_data["geolocation"],
                          "illuminanceNote": sun_data["illuminanceNote"], "skyAtmosphere": True,
                          "skyLightRealTimeCapture": True, "autoExposureRangeEV100": [-4, 16],
                          "visualValidation": "pending rendered Metal session"}


def main():
    write_report("pending")  # Remove any stale prior success before touching assets.
    scene, bridge, records, archive_ids = verify_inputs()
    from hidden_collision import apply_hidden_collision_contract, verify_hidden_collision_contract, verify_inputs as verify_hidden_inputs
    verify_hidden_inputs(scene, GEOMETRY)  # Fail before replacing the map on stale auxiliary geometry.
    sys.path.insert(0, str(ROOT / "scripts/unreal/tv-oak"))
    from oak_reference import verify_inputs as verify_oak_inputs
    from tv_oak import apply_tv_oak
    verify_oak_inputs(scene, GEOMETRY)  # Pin photo inputs and exact three-body scope before map replacement.
    sys.path.insert(0, str(ROOT / "scripts/unreal/furniture-oak"))
    from furniture_reference import verify_inputs as verify_furniture_oak_inputs
    from furniture_oak import apply_furniture_oak
    verify_furniture_oak_inputs(scene, GEOMETRY)  # Exact nine boxes and pinned photos before replacing the map.
    sys.path.insert(0, str(ROOT / "scripts/unreal/pendant-emitter"))
    from emitter_reference import verify_inputs as verify_pendant_emitter_inputs
    from pendant_emitter import apply_pendant_emitter
    verify_pendant_emitter_inputs(scene, GEOMETRY)  # Exact source globe area/power before replacing the map.
    sys.path.insert(0, str(ROOT / "scripts/unreal/lawn-ground"))
    from lawn_ground import verify_inputs as verify_lawn_ground_inputs, apply_lawn_ground
    verify_lawn_ground_inputs(scene, GEOMETRY)  # Refuse missing PBR/source inputs before world replacement.
    materials_requested = os.environ.get("BREZI_APPLY_MATERIALS") == "1"
    vegetation_requested = os.environ.get("BREZI_APPLY_VEGETATION") == "1"
    # The first authored tuft failed the native 4K visual review. Keep it opt-in
    # for further experiments while the default app retains the source planting.
    ornamental_requested = os.environ.get("BREZI_APPLY_ORNAMENTAL") == "1"
    # Stronger plaster normals introduced repeatable patches in two native 4K
    # captures. Retain the source material unless explicitly studying the candidate.
    plaster_requested = os.environ.get("BREZI_APPLY_FACADE_PLASTER") == "1"
    pool_coping_requested = os.environ.get("BREZI_APPLY_POOL_COPING", "1") == "1"
    sys.path.insert(0, str(ROOT / "scripts/unreal/planting-surfaces"))
    from mulch import verify_inputs as verify_mulch_inputs, apply_mulch
    sys.path.insert(0, str(ROOT / "scripts/unreal/ornamental-grass"))
    from ornamental import (verify_inputs as verify_ornamental_inputs, apply_ornamental,
                            source_state as ornamental_source_state, layer as ornamental_layer)
    sys.path.insert(0, str(ROOT / "scripts/unreal/facade-plaster"))
    from plaster import (verify_inputs as verify_plaster_inputs, apply_plaster,
                         inspect as inspect_plaster, base_graph as plaster_base_graph,
                         save_unload_reload as reload_plaster_map, digest as plaster_digest)
    sys.path.insert(0, str(ROOT / "scripts/unreal/pool-coping"))
    from coping import (verify_inputs as verify_pool_coping_inputs, apply_pool_coping,
                        retain_source as retain_source_pool_coping)
    if materials_requested and vegetation_requested:
        verify_plaster_inputs(scene, GEOMETRY)
        verify_pool_coping_inputs(scene, GEOMETRY)
    if materials_requested and vegetation_requested:
        verify_mulch_inputs(scene, GEOMETRY)
        verify_ornamental_inputs(scene, GEOMETRY)
    if vegetation_requested:
        sys.path.insert(0, str(ROOT / "scripts/unreal/lawn-detail"))
        from placement import verify_inputs as verify_lawn_inputs
        from native_layer import apply_lawn_detail
        verify_lawn_inputs(scene, GEOMETRY)
    if materials_requested:
        sys.path.insert(0, str(ROOT / "scripts/unreal/deck-wood"))
        from deck_wood import verify_inputs as verify_deck_wood_inputs, apply_deck_wood
        verify_deck_wood_inputs(scene, GEOMETRY)  # CPU/source checks before any world mutation.
        sys.path.insert(0, str(ROOT / "scripts/unreal/facade-wood"))
        from facade_wood import verify_inputs as verify_facade_wood_inputs, apply_facade_wood, validate_saved_facade_wood
        verify_facade_wood_inputs(scene, GEOMETRY)
    # A Python commandlet does not perform the interactive editor's asset scan.
    unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous(
        ["/Interchange/Pipelines", "/Game/Brezi"], force_rescan=True)
    actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    level_system = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    prepare_world(actor_system, level_system, scene)
    actors, pre_import_actor_paths = import_geometry(actor_system, level_system)
    assets_by_id = configure_and_measure(actors, records, bridge, archive_ids)
    from oak_reimport import initialize_created_actors, WITH_PENDANT_KEYS
    REPORT["oakActorInitialization"] = initialize_created_actors(
        unreal, actors, pre_import_actor_paths, assets_by_id, records, key_scope=WITH_PENDANT_KEYS)
    sys.path.insert(0, str(ROOT / "scripts/unreal"))
    from materials import apply_materials, ensure_nanite_materials, _asset_hashes
    if materials_requested:
        REPORT["materials"] = apply_materials(scene, assets_by_id, GEOMETRY.parent)
    else:
        REPORT["materials"] = {"status": "scalar-gltf-pbr", "nativeMaterialPassRequested": False}
        REPORT["deckWood"] = {"status": "not-requested", "nativeMaterialPassRequested": False}
        REPORT["facadeWood"] = {"status": "not-requested", "nativeMaterialPassRequested": False}
    if os.environ.get("BREZI_APPLY_OPTICS") == "1":
        from optics import apply_optics
        REPORT["optics"] = apply_optics(scene, assets_by_id, GEOMETRY.parent)
        REPORT["pipelineFiles"]["scripts/unreal/optics.py"] = sha(ROOT / "scripts/unreal/optics.py")
    else:
        REPORT["optics"] = {"status": "imported-scalar-optics", "nativeOpticsRequested": False}
    if os.environ.get("BREZI_APPLY_WALKING") == "1":
        from walking import apply_walking_contract
        REPORT["walking"] = apply_walking_contract(scene, assets_by_id, GEOMETRY)
        REPORT["pipelineFiles"].update(REPORT["walking"]["pipelineFiles"])
    else:
        REPORT["walking"] = {"status": "source-static-collision-only", "runtimeWalkingVerified": False}
    REPORT["hiddenCollision"] = apply_hidden_collision_contract(scene, GEOMETRY)
    REPORT["pipelineFiles"].update(REPORT["hiddenCollision"]["pipelineFiles"])
    REPORT["naniteMaterials"] = ensure_nanite_materials(assets_by_id)
    REPORT["pipelineFiles"]["scripts/unreal/materials.py"] = sha(ROOT / "scripts/unreal/materials.py")
    if materials_requested:
        # The base Nanite writer owns its original asset namespaces. The deck
        # stage validates its own Nanite usage and preserves final hatch body settings.
        REPORT["deckWood"] = apply_deck_wood(scene, assets_by_id, GEOMETRY)
        REPORT["pipelineFiles"].update(REPORT["deckWood"]["pipelineFiles"])
        REPORT["facadeWood"] = apply_facade_wood(scene, assets_by_id, GEOMETRY)
        REPORT["pipelineFiles"].update(REPORT["facadeWood"]["pipelineFiles"])
    if vegetation_requested:
        from vegetation import apply_hedge_detail
        REPORT["vegetation"] = apply_hedge_detail(scene, GEOMETRY.parent)
        REPORT["pipelineFiles"].update(REPORT["vegetation"]["pipelineFiles"])
    else:
        REPORT["vegetation"] = {"status": "source-proxy-vegetation", "nativeApplied": False}
    measure_final_collision(actor_system)
    lighting(actor_system, read_json("viewpoints.json"))
    world = unreal.EditorLevelLibrary.get_editor_world()
    unreal.EditorAssetLibrary.set_metadata_tag(world, "BreziGeneratedBy", "scripts/unreal/import_scene.py")
    unreal.EditorAssetLibrary.set_metadata_tag(world, "BreziSourceGLBSHA256", REPORT["sourceGlbSha256"])
    if not level_system.save_current_level():
        raise RuntimeError("Generated map did not save")
    if not unreal.EditorAssetLibrary.save_directory(CONTENT_PATH, only_if_is_dirty=True, recursive=True):
        raise RuntimeError("Imported assets did not all save")
    # Reopen from disk through a blank map, so auxiliary validation cannot read
    # merely the still-live actors that were just authored. No assets are generated here.
    actors.clear()
    del world
    if not unreal.EditorLoadingAndSavingUtils.new_blank_map(False):
        raise RuntimeError("Could not unload the generated map for serialized collision verification")
    if not level_system.load_level(MAP_PATH):
        raise RuntimeError("Could not reopen the saved generated map")
    REPORT["hiddenCollision"] = verify_hidden_collision_contract(scene, GEOMETRY)
    measure_final_collision(actor_system)
    from stove_visuals import apply_stove_visuals
    REPORT["stoveVisuals"] = apply_stove_visuals(scene, GEOMETRY)
    REPORT["pipelineFiles"].update(REPORT["stoveVisuals"]["pipelineFiles"])
    REPORT["tvOak"] = apply_tv_oak(scene, GEOMETRY)
    REPORT["pipelineFiles"].update(REPORT["tvOak"]["pipelineFiles"])
    REPORT["furnitureOak"] = apply_furniture_oak(scene, GEOMETRY)
    REPORT["pipelineFiles"].update(REPORT["furnitureOak"]["pipelineFiles"])
    REPORT["pendantEmitter"] = apply_pendant_emitter(scene, GEOMETRY)
    REPORT["pipelineFiles"].update(REPORT["pendantEmitter"]["pipelineFiles"])
    if materials_requested:
        # The saved map has been reopened by the visual stages. Validate the
        # actual final component bindings and serialized facade material graphs.
        REPORT["facadeWood"]["savedReadback"] = validate_saved_facade_wood(
            scene, assets_by_id, GEOMETRY, REPORT["facadeWood"])
    if vegetation_requested:
        REPORT["lawnDetail"] = apply_lawn_detail(scene, GEOMETRY)
        REPORT["pipelineFiles"].update(REPORT["lawnDetail"]["pipelineFiles"])
    else:
        REPORT["lawnDetail"] = {"status": "not-requested", "nativeApplied": False}
    if materials_requested and vegetation_requested:
        REPORT["lawnGround"] = apply_lawn_ground(scene, GEOMETRY)
        REPORT["pipelineFiles"].update(REPORT["lawnGround"]["pipelineFiles"])
    else:
        REPORT["lawnGround"] = {"status": "not-requested", "nativeApplied": False}
    if materials_requested and vegetation_requested:
        REPORT["plantingSurfaces"] = apply_mulch(scene, GEOMETRY)
        REPORT["pipelineFiles"].update(REPORT["plantingSurfaces"]["pipelineFiles"])
        if ornamental_requested:
            REPORT["ornamentalGrass"] = apply_ornamental(scene, GEOMETRY)
        else:
            ornamental_contract = verify_ornamental_inputs(scene, GEOMETRY)
            source_cards = ornamental_source_state(unreal, ornamental_contract)
            if ornamental_layer(unreal, ornamental_contract) or not all(
                    c["visible"] and not c["hiddenInGame"] and not c["actorHidden"]
                    for c in source_cards.values()):
                raise RuntimeError("Rejected ornamental prototype is still active or source cards are hidden")
            REPORT["ornamentalGrass"] = {
                "status": "source-cards-retained-prototype-rejected", "nativeApplied": False,
                "recipeExcludesReadOnlyMaterialsHelper": True,
                "recipeSha256": ornamental_contract["recipe"], "pipelineFiles": ornamental_contract["pins"],
                "sourceManifestSha256": REPORT["sourceManifestSha256"],
                "sourceObjSha256": sha(GEOMETRY / "dom-mm.obj"),
                "sourceIds": sorted(source_cards), "sourceAfter": source_cards,
                "newActorCount": 0, "sourceCardsHidden": 0, "sourceCardsRetained": 18,
                "sourceObjectsDeleted": 0, "visualAcceptance": "prototype-rejected-in-native-4k-review",
            }
        REPORT["pipelineFiles"].update(REPORT["ornamentalGrass"]["pipelineFiles"])
    else:
        REPORT["plantingSurfaces"] = {"status": "not-requested", "nativeApplied": False}
        REPORT["ornamentalGrass"] = {"status": "not-requested", "nativeApplied": False}
    if materials_requested and vegetation_requested:
        if plaster_requested:
            REPORT["facadePlaster"] = apply_plaster(scene, GEOMETRY)
        else:
            plaster_contract = verify_plaster_inputs(scene, GEOMETRY)
            plaster_before = inspect_plaster(unreal, plaster_contract, "source")
            plaster_graph = plaster_base_graph(unreal)
            if (abs(plaster_graph["nodes"][plaster_graph["normalMix"]]["properties"]["const_alpha"] - 0.2) > 1e-6
                    or plaster_before["world"]["grassInstanceCount"] != 33769):
                raise RuntimeError("Canonical plaster normal weight or retained grass differs")
            plaster_reload = reload_plaster_map(unreal, set())
            plaster_after = inspect_plaster(unreal, plaster_contract, "source")
            if plaster_after != plaster_before or plaster_base_graph(unreal) != plaster_graph:
                raise RuntimeError("Source plaster state changed after saved-map reload")
            REPORT["facadePlaster"] = {
                "status": "source-plaster-retained-candidate-rejected", "nativeApplied": False,
                "selectedIds": list(plaster_contract["records"]), "sourceMaterialSlot": "MAT_0010",
                "sourceManifestSha256": REPORT["sourceManifestSha256"],
                "sourceObjSha256": sha(GEOMETRY / "dom-mm.obj"),
                "recipeSha256": plaster_contract["recipeSha256"], "recipe": plaster_contract["recipe"],
                "recipeCanonicalJson": plaster_contract["recipeCanonicalJson"],
                "pipelineFiles": plaster_contract["pipelineFiles"],
                "normalStrength": 0.2, "candidateNormalStrength": 0.5,
                "artistNormalWeightNotMeasured": True, "sourceOverridesRetained": 66,
                "candidateOverridesActive": 0, "sourceObjectsDeleted": 0,
                "selectedAfter": plaster_after["selected"], "sourceGraph": plaster_graph,
                "sourceReload": plaster_reload, "sourceStateUnchangedAfterReload": True,
                "grassInstanceCount": plaster_after["world"]["grassInstanceCount"],
                "sourcePreservationSnapshotSha256": plaster_digest(plaster_before["world"]),
                "protectedAssetHashes": plaster_after["world"]["protectedAssetHashes"],
                "assetHashes": {}, "visualAcceptance": "candidate-rejected-in-two-native-4k-captures",
                "renderedVerified": False,
            }
        REPORT["pipelineFiles"].update(REPORT["facadePlaster"]["pipelineFiles"])
    else:
        REPORT["facadePlaster"] = {"status": "not-requested", "nativeApplied": False}
    if materials_requested and vegetation_requested:
        REPORT["poolCoping"] = (apply_pool_coping(scene, GEOMETRY) if pool_coping_requested
                                else retain_source_pool_coping(scene, GEOMETRY))
        REPORT["pipelineFiles"].update(REPORT["poolCoping"]["pipelineFiles"])
    else:
        REPORT["poolCoping"] = {"status": "not-requested", "nativeApplied": False}
    # The visual stages perform further save/reload cycles. Recheck the
    # entire collision authority against the final world, not an earlier map.
    REPORT["hiddenCollision"] = verify_hidden_collision_contract(scene, GEOMETRY)
    measure_final_collision(actor_system)
    REPORT["auxiliaryCollisionObjects"] = REPORT["hiddenCollision"]["objectCount"]
    REPORT["totalCollisionComponentsIncludingAuxiliary"] = REPORT["finalCollisionComponents"] + REPORT["auxiliaryCollisionObjects"]
    # Verify the persisted world exists, keeping runtime/render claims separate.
    map_file = Path(unreal.Paths.project_content_dir()) / "Brezi/Maps/Brezi.umap"
    if not map_file.is_file():
        raise RuntimeError("Saved Brezi.umap was not found")
    REPORT["savedMapBytes"] = map_file.stat().st_size
    REPORT["mapFileSha256"] = sha(map_file)
    # Pin every imported geometry package and its current local materials,
    # including meshes that did not need a later photo/optical override.
    geometry_paths = set()
    for mesh in assets_by_id.values():
        geometry_paths.add(mesh.get_path_name())
        for slot in mesh.get_editor_property("static_materials"):
            material = slot.get_editor_property("material_interface")
            if material and material.get_path_name().startswith("/Game/Brezi/"):
                geometry_paths.add(material.get_path_name())
    REPORT["geometryAssetHashes"] = _asset_hashes(geometry_paths)
    # Material/optical passes can legitimately write different slots of the
    # same mesh. Individual receipts describe each pass; this final snapshot
    # describes the persisted combined result after every pass and world save.
    asset_files = set(REPORT["geometryAssetHashes"])
    for stage in (REPORT["materials"], REPORT["deckWood"], REPORT["facadeWood"], REPORT["optics"], REPORT["naniteMaterials"], REPORT["vegetation"], REPORT["lawnDetail"], REPORT["lawnGround"], REPORT["plantingSurfaces"], REPORT["ornamentalGrass"], REPORT["walking"], REPORT["hiddenCollision"], REPORT["stoveVisuals"], REPORT["tvOak"], REPORT["furnitureOak"], REPORT["pendantEmitter"]):
        for key in ("generatedAssetHashes", "assignedMeshHashes", "assetHashes"):
            asset_files.update(stage.get(key, {}))
    asset_files.update(REPORT["lawnGround"].get("protectedAssetHashes", {}))
    asset_files.update(REPORT["plantingSurfaces"].get("protectedAssetHashes", {}))
    asset_files.update(REPORT["ornamentalGrass"].get("protectedAssetHashes", {}))
    asset_files.update(REPORT["facadePlaster"].get("assetHashes", {}))
    asset_files.update(REPORT["facadePlaster"].get("protectedAssetHashes", {}))
    asset_files.update(REPORT["poolCoping"].get("assetHashes", {}))
    asset_files.update(REPORT["poolCoping"].get("protectedAssetHashes", {}))
    asset_files.update(REPORT["furnitureOak"]["canonicalAssetHashes"])
    asset_files.update(REPORT["pendantEmitter"]["canonicalAssetHashes"])
    REPORT["finalAssetHashes"] = {file: sha(ROOT / file) for file in sorted(asset_files)}
    REPORT["nativeAuthoredStateSha256"] = hashlib.sha256(json.dumps({
        "map": REPORT["mapFileSha256"], "pipeline": REPORT["pipelineFiles"],
        "assets": REPORT["finalAssetHashes"], "source": REPORT["sourceGlbSha256"],
    }, sort_keys=True).encode()).hexdigest()
    write_report("import-validated")
    unreal.log("BREZI_IMPORT " + json.dumps({"status": REPORT["status"], "objects": REPORT["importedObjects"],
                                            "maxErrorCm": REPORT["maxWorldBoundsErrorCm"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        REPORT["error"] = str(exc).replace(str(ROOT), "<repository>").replace(str(Path.home()), "<user>")
        write_report("failed")
        raise
