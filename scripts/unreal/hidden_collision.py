"""Import only the separately captured, enabled hidden source collision hulls.

No actor is visible at any point after a mesh is attached. Saved/reloaded native
LOD0 triangles are compared individually; bounds are additional evidence only.
Pure input/triangle helpers can be tested without importing Unreal.
"""
import hashlib
import itertools
import json
import math
import re
import struct
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = "scripts/unreal/hidden_collision.py"
PREFIX = "/Game/Brezi/HiddenCollision"
TAG = "BreziHiddenCollision"
BOUNDS_TOLERANCE_CM = 0.02
TRIANGLE_TOLERANCE_CM = 0.005
PIPELINE_FILES = [OWNER, "scripts/unreal/hidden-collision-export.mjs",
    "scripts/archviz/scene-export.ts", "scripts/archviz/export.mjs",
    "unreal/BreziTwin/Source/BreziTwin/BreziCollisionAudit.h",
    "unreal/BreziTwin/Source/BreziTwin/BreziCollisionAudit.cpp"]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_report(directory, report, status):
    report.update(status=status, generatedAt=datetime.now(timezone.utc).isoformat())
    path = Path(directory).parent / "hidden-collision-report.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def read_glb_triangles(raw, records):
    """Strict reader for our own identity-node, one-primitive collision GLB."""
    require(len(raw) >= 28 and raw[:4] == b"glTF" and struct.unpack_from("<II", raw, 4) == (2, len(raw)), "Invalid hidden GLB header")
    size, kind = struct.unpack_from("<II", raw, 12)
    require(kind == 0x4e4f534a and 20+size+8 <= len(raw), "Invalid hidden GLB JSON")
    document = json.loads(raw[20:20+size])
    bin_size, bin_kind = struct.unpack_from("<II", raw, 20+size)
    binary = raw[28+size:]
    require(bin_kind == 0x004e4942 and len(binary) == bin_size, "Invalid hidden GLB BIN")
    require(not any(document.get(key) for key in ("materials", "textures", "images", "cameras", "animations", "skins")), "Hidden GLB contains unauthorized visual/animated content")
    require(document.get("scene") == 0 and len(document["scenes"]) == 1
            and document["scenes"][0]["nodes"] == list(range(len(document["nodes"]))), "Hidden GLB scene identity differs")

    def accessor(index, component, kind, size, code):
        value = document["accessors"][index]
        view = document["bufferViews"][value["bufferView"]]
        require(value["componentType"] == component and value["type"] == kind
                and not value.get("sparse") and not value.get("normalized") and view.get("buffer") == 0
                and "byteStride" not in view, "Unsupported collision accessor")
        start = view.get("byteOffset", 0) + value.get("byteOffset", 0)
        end = start + value["count"] * size
        require(0 <= start <= end <= len(binary) and end <= view.get("byteOffset", 0)+view["byteLength"], "Collision accessor exceeds its buffer")
        return list(struct.iter_unpack(code, binary[start:end]))

    result = {}
    for node in document["nodes"]:
        id_ = node["name"]
        require(id_ in records and id_ not in result and not any(key in node for key in ("matrix", "translation", "rotation", "scale", "children")), "Hidden node identity or transform differs")
        extra = node["extras"]
        require(extra.get("source_collision_id") == id_ and extra.get("source_id") == records[id_]["sourceId"]
                and extra.get("collision_only") is True and extra.get("render_authorized") is False, "Hidden node provenance differs")
        mesh = document["meshes"][node["mesh"]]
        require(mesh["name"] == id_ and len(mesh["primitives"]) == 1, "Merged or unexpected hidden primitive")
        primitive = mesh["primitives"][0]
        require(primitive.get("mode") == 4 and set(primitive["attributes"]) == {"POSITION"} and "material" not in primitive, "Hidden primitive has unsupported geometry")
        vertices = accessor(primitive["attributes"]["POSITION"], 5126, "VEC3", 12, "<fff")
        require(all(math.isfinite(v) for point in vertices for v in point), "Nonfinite hidden vertices")
        vertices = [(x*100, z*100, y*100) for x,y,z in vertices]
        indices = [item[0] for item in accessor(primitive["indices"], 5125, "SCALAR", 4, "<I")]
        require(len(indices) % 3 == 0 and all(index < len(vertices) for index in indices), "Invalid hidden triangle indices")
        require(len(indices)//3 == records[id_]["triangles"] and len(vertices) == records[id_]["vertices"], "Hidden source geometry counts differ")
        result[id_] = [tuple(vertices[index] for index in indices[i:i+3]) for i in range(0, len(indices), 3)]
    require(result.keys() == records.keys(), "Incomplete hidden GLB coverage")
    return result


def triangle_error(expected, actual, tolerance=TRIANGLE_TOLERANCE_CM):
    """Match all triangles/corners, permitting only index/vertex reordering."""
    require(len(expected) == len(actual) and len(expected) > 0, "Native collision triangle count differs")
    remaining = set(range(len(actual)))
    maximum = 0.0
    for triangle in expected:
        best = (math.inf, -1)
        for index in remaining:
            error = min(max(abs(a[k]-b[k]) for a,b in zip(triangle, permutation) for k in range(3))
                        for permutation in itertools.permutations(actual[index]))
            if error < best[0]:
                best = (error, index)
        require(best[0] <= tolerance, f"Native collision triangle changed by {best[0]} cm")
        remaining.remove(best[1])
        maximum = max(maximum, best[0])
    return maximum


def verify_inputs(scene, geometry_dir):
    directory = Path(geometry_dir)
    contract_path = directory / "hidden-collision.json"
    contract = json.loads(contract_path.read_text())
    require(contract.get("schemaVersion") == 1 and contract.get("status") == "auxiliary-source-exported-native-pending"
            and contract.get("coordinateSystem") == "unreal-centimeters", "Invalid hidden collision contract")
    require(contract["sourceManifestSha256"] == sha(directory / "scene.json") and contract["mainObjSha256"] == scene["objSha256"], "Hidden collision source manifest is stale")
    require(contract["mainObjSha256"] == sha(directory / "dom-mm.obj"), "Canonical OBJ changed")
    require(contract["supplementSha256"] == sha(directory / "brezi-collision-only.glb")
            and contract["sourceCaptureSha256"] == sha(directory / "hidden-collision-source.json"), "Hidden collision payload changed")
    issues = contract.get("gltfValidation", {})
    require(issues.get("numErrors") == 0 and issues.get("numWarnings") == 0 and issues.get("truncated") is False, "Hidden collision lacks complete Khronos validation")
    for name in ("scripts/unreal/hidden-collision-export.mjs", "scripts/archviz/scene-export.ts", "scripts/archviz/export.mjs"):
        require(scene["sourceFiles"].get(name) == sha(ROOT / name), "Hidden source exporter changed: " + name)
    eligible = [item for item in scene["skipped"] if item["enabled"] and item["babylonCheckCollisions"]]
    require(all(item["reason"] == "hidden-proxy-or-collider" for item in eligible), "Unsupported skipped source collider")
    require(len({item["sourceId"] for item in eligible}) == len(eligible), "Ambiguous hidden source ID")
    records = {}
    for record in contract["objects"]:
        id_ = "COLL_" + hashlib.sha256(record["sourceId"].encode()).hexdigest()[:20]
        require(record["id"] == id_ and id_ not in records and record["nativeRole"] == "blocking-only-never-a-floor", "Invalid hidden collider identity/role")
        require(record["runtimeTags"] == [TAG, "BreziSourceObjectId="+id_, "BreziSourceId="+record["sourceId"]], "Unexpected hidden runtime tags")
        require(not record["sourceMetadata"].get("walkSurface"), "A hidden collider cannot become a floor")
        bounds = record["nativeBoundsCm"]
        require(all(len(bounds[key]) == 3 and all(math.isfinite(value) for value in bounds[key]) for key in ("min", "max"))
                and all(bounds["min"][i] <= bounds["max"][i] for i in range(3)), "Invalid hidden bounds")
        records[id_] = record
    require(len(records) == len(eligible) and {r["sourceId"] for r in records.values()} == {r["sourceId"] for r in eligible}, "Hidden source coverage differs")
    triangles = read_glb_triangles((directory / "brezi-collision-only.glb").read_bytes(), records)
    return contract, records, triangles


def owned_asset(unreal, path):
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        return None
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset:
        require(unreal.EditorAssetLibrary.get_metadata_tag(asset, "BreziGeneratedBy") == OWNER, "Refusing to replace unowned hidden asset: " + path)
    return asset


def save(unreal, asset):
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "BreziGeneratedBy", OWNER)
    require(unreal.EditorAssetLibrary.save_loaded_asset(asset), "Hidden asset did not save: " + asset.get_path_name())


def base_report(directory, contract):
    return {"schemaVersion": 1, "sourceContractSha256": sha(Path(directory)/"hidden-collision.json"),
            "sourceGlbSha256": contract["supplementSha256"], "sourceCaptureSha256": contract["sourceCaptureSha256"],
            "sourceManifestSha256": contract["sourceManifestSha256"], "namespace": PREFIX,
            "pipelineFiles": {name: sha(ROOT/name) for name in PIPELINE_FILES},
            "verification": {"nativeImported": False, "savedReloaded": False,
                             "collisionQueriesVerified": False, "runtimeWorldVerified": False,
                             "renderedInvisibilityVerified": False, "canonicalGeometryModified": False}}


def apply_hidden_collision_contract(scene, geometry_dir):
    import unreal
    report = {"schemaVersion": 1}
    write_report(geometry_dir, report, "pending")
    created = []
    try:
        contract, records, triangles = verify_inputs(scene, geometry_dir)
        report = base_report(geometry_dir, contract)
        assets, actor_system = unreal.EditorAssetLibrary, unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        registry = unreal.AssetRegistryHelpers.get_asset_registry()
        registry.scan_paths_synchronous([PREFIX, "/Interchange/Pipelines"], force_rescan=True)
        for path in assets.list_assets(PREFIX, recursive=True, include_folder=False):
            owned_asset(unreal, path)
        for actor in actor_system.get_all_level_actors():
            if actor.actor_has_tag(TAG):
                require(assets.get_metadata_tag(actor, "BreziGeneratedBy") == OWNER, "Unowned hidden collision actor")
                require(actor_system.destroy_actor(actor), "Could not replace owned hidden actor")
        pipeline_path = PREFIX + "/Pipeline/HiddenAssets"
        pipeline = owned_asset(unreal, pipeline_path)
        if pipeline is None:
            pipeline = assets.duplicate_asset("/Interchange/Pipelines/DefaultGLTFSceneAssetsPipeline.DefaultGLTFSceneAssetsPipeline", pipeline_path)
        require(pipeline is not None, "Hidden Interchange pipeline unavailable")
        pipeline.set_editor_property("use_source_name_for_asset", False)
        mesh_pipeline = pipeline.get_editor_property("mesh_pipeline")
        for key,value in {"combine_static_meshes_behavior": unreal.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,
                          "collision": False, "build_nanite": False, "generate_lightmap_u_vs": False}.items():
            mesh_pipeline.set_editor_property(key, value)
        pipeline.get_editor_property("common_meshes_properties").set_editor_property("remove_degenerates", False)
        material_pipeline = pipeline.get_editor_property("material_pipeline")
        material_pipeline.set_editor_property("import_materials", False)
        material_pipeline.get_editor_property("texture_pipeline").set_editor_property("import_textures", False)
        save(unreal, pipeline)
        manager = unreal.InterchangeManager.get_interchange_manager_scripted()
        params = unreal.ImportAssetParameters()
        for key,value in {"is_automated": True, "replace_existing": True, "force_show_dialog": False,
                          "override_pipelines": [unreal.SoftObjectPath(pipeline.get_path_name())]}.items():
            params.set_editor_property(key, value)
        before_actors = {actor.get_path_name() for actor in actor_system.get_all_level_actors()}
        require(manager.import_asset(PREFIX+"/Meshes", manager.create_source_data(str(Path(geometry_dir)/"brezi-collision-only.glb")), params), "Hidden asset-only import failed")
        require(before_actors == {actor.get_path_name() for actor in actor_system.get_all_level_actors()}, "Hidden asset import unexpectedly created scene actors")
        registry.scan_paths_synchronous([PREFIX], force_rescan=True)
        meshes = {}
        for path in assets.list_assets(PREFIX+"/Meshes", recursive=True, include_folder=False):
            mesh = assets.load_asset(path)
            require(isinstance(mesh, unreal.StaticMesh), "Unexpected hidden imported asset type")
            # The source/path preflight already protected prior assets. Mark all
            # newly created imports before later API checks so a failed attempt
            # can be safely retried without treating its own assets as unowned.
            save(unreal, mesh)
            matches = re.findall(r"COLL_[0-9a-f]{20}", mesh.get_name())
            require(len(matches) == 1 and matches[0] in records and matches[0] not in meshes, "Merged, stale or ambiguous hidden mesh")
            meshes[matches[0]] = mesh
        require(meshes.keys() == records.keys(), "Hidden native mesh coverage differs")
        for id_,mesh in meshes.items():
            body = mesh.get_editor_property("body_setup")
            require(body is not None, "Hidden mesh has no BodySetup")
            body.set_editor_property("never_needs_cooked_collision_data", False)
            body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            mesh.set_editor_property("lod_for_collision", 0)
            require(mesh.get_editor_property("complex_collision_mesh") is None, "Hidden mesh redirects its collision")
            require(not mesh.get_editor_property("nanite_settings").get_editor_property("enabled"), "Hidden mesh enabled Nanite")
            assets.set_metadata_tag(mesh, "BreziSourceCollisionId", id_)
            save(unreal, mesh)
            actor = actor_system.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator())
            require(actor is not None, "Hidden collider spawn failed")
            created.append(actor)
            actor.set_actor_hidden_in_game(True)
            actor.set_actor_label(id_+" · "+records[id_]["sourceName"])
            actor.set_folder_path("Brezi/HiddenCollision")
            tags = ["BreziGenerated", *records[id_]["runtimeTags"]]
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])
            assets.set_metadata_tag(actor, "BreziGeneratedBy", OWNER)
            component = actor.get_component_by_class(unreal.StaticMeshComponent)
            # All visibility flags are set before the first mesh attachment.
            component.set_visibility(False)
            component.set_hidden_in_game(True)
            component.set_cast_shadow(False)
            component.set_editor_property("cast_hidden_shadow", False)
            component.set_visible_in_ray_tracing(False)
            component.set_affect_distance_field_lighting(False)
            component.set_affect_dynamic_indirect_lighting(False)
            component.set_affect_indirect_lighting_while_hidden(False)
            component.set_receives_decals(False)
            component.set_editor_property("component_tags", [unreal.Name(tag) for tag in records[id_]["runtimeTags"]])
            component.set_static_mesh(mesh)
            component.set_collision_profile_name("BlockAll")
            component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            component.set_mobility(unreal.ComponentMobility.STATIC)
        report.update(measure_world(unreal, records, triangles))
        report["verification"]["nativeImported"] = True
        write_report(geometry_dir, report, "hidden-collision-authored-reload-pending")
        return report
    except Exception as error:
        for actor in created:
            actor_system.destroy_actor(actor)
        report["error"] = str(error)
        write_report(geometry_dir, report, "failed")
        raise


def measure_world(unreal, records, source_triangles):
    from materials import _asset_hashes
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    found, measured, asset_paths = set(), [], set()
    asset_paths.add(PREFIX+"/Pipeline/HiddenAssets.HiddenAssets")
    for actor in actors:
        if not actor.actor_has_tag(TAG):
            continue
        require(unreal.EditorAssetLibrary.get_metadata_tag(actor, "BreziGeneratedBy") == OWNER, "Hidden actor lost ownership")
        components = actor.get_components_by_class(unreal.StaticMeshComponent)
        require(len(components) == 1, "Hidden actor component count differs")
        component = components[0]
        tags = {str(tag) for tag in component.get_editor_property("component_tags")}
        ids = {tag.removeprefix("BreziSourceObjectId=") for tag in tags if tag.startswith("BreziSourceObjectId=")}
        require(len(ids) == 1, "Ambiguous hidden component identity")
        id_ = ids.pop()
        require(id_ in records and id_ not in found and set(records[id_]["runtimeTags"]).issubset(tags)
                and "BreziWalkSurface" not in tags, "Unexpected hidden component identity/tags")
        found.add(id_)
        mesh = component.get_editor_property("static_mesh")
        require(mesh is not None and mesh.get_path_name().startswith(PREFIX+"/")
                and unreal.EditorAssetLibrary.get_metadata_tag(mesh, "BreziSourceCollisionId") == id_, "Hidden actor mesh identity differs")
        flags = {name: bool(component.get_editor_property(name)) for name in
                 ("visible", "hidden_in_game", "cast_shadow", "cast_hidden_shadow", "visible_in_ray_tracing",
                  "affect_distance_field_lighting", "affect_dynamic_indirect_lighting", "affect_indirect_lighting_while_hidden")}
        require(flags["hidden_in_game"] and not any(value for key,value in flags.items() if key != "hidden_in_game"), "Hidden collision influences rendering")
        require(str(component.get_collision_profile_name()) == "BlockAll"
                and component.get_collision_enabled() == unreal.CollisionEnabled.QUERY_AND_PHYSICS
                and component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN) == unreal.CollisionResponseType.ECR_BLOCK,
                "Hidden source collider is not actually blocking Pawn")
        body = mesh.get_editor_property("body_setup")
        require(body and body.get_editor_property("collision_trace_flag") == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
                and not body.get_editor_property("never_needs_cooked_collision_data")
                and mesh.get_editor_property("lod_for_collision") == 0
                and mesh.get_editor_property("complex_collision_mesh") is None
                and not mesh.get_editor_property("nanite_settings").get_editor_property("enabled"), "Hidden collision uses a different geometry representation")
        aggregate = body.get_editor_property("agg_geom")
        simple_shapes = {name: len(aggregate.get_editor_property(name)) for name in (
            "sphere_elems", "box_elems", "sphyl_elems", "convex_elems", "tapered_capsule_elems",
            "level_set_elems", "skinned_level_set_elems", "ml_level_set_elems", "skinned_triangle_mesh_elems")}
        require(not any(simple_shapes.values()), "Hidden source mesh gained synthesized simple collision")
        transform = component.get_world_transform()
        # UStaticMesh::GetNumTriangles uses GetRenderData's async-property wait.
        # Finish the existing import/build before the strictly read-only C++ reader.
        require(mesh.get_num_triangles(0) == records[id_]["triangles"], "Native hidden triangle count changed")
        local = list(unreal.BreziCollisionAudit.read_lod0_triangles(mesh))
        require(len(local) == records[id_]["triangles"]*3, "Native hidden triangle readback unavailable or incomplete")
        world = [unreal.MathLibrary.transform_location(transform, point) for point in local]
        points = [(float(p.x),float(p.y),float(p.z)) for p in world]
        require(all(math.isfinite(value) for point in points for value in point), "Nonfinite native collision vertex")
        actual_triangles = [tuple(points[i:i+3]) for i in range(0,len(points),3)]
        geometry_error = triangle_error(source_triangles[id_], actual_triangles)
        origin, extent, _ = unreal.SystemLibrary.get_component_bounds(component)
        actual = {"min": [getattr(origin,k)-getattr(extent,k) for k in ("x","y","z")],
                  "max": [getattr(origin,k)+getattr(extent,k) for k in ("x","y","z")]}
        bound_error = max(abs(actual[key][i]-records[id_]["nativeBoundsCm"][key][i]) for key in ("min","max") for i in range(3))
        require(math.isfinite(bound_error) and bound_error <= BOUNDS_TOLERANCE_CM, "Native hidden bounds differ")
        asset_paths.add(mesh.get_path_name())
        measured.append({"id":id_, "sourceId":records[id_]["sourceId"], "actor":actor.get_path_name(),
                         "component":component.get_path_name(), "asset":mesh.get_path_name(), "triangles":len(actual_triangles),
                         "maxTriangleErrorCm":geometry_error, "maxBoundsErrorCm":bound_error,
                         "nativeBoundsCm":actual, "visibility":flags, "simpleCollisionShapes":simple_shapes,
                         "collisionProfile":"BlockAll", "collision":"source-triangles-complex-as-simple"})
    require(found == records.keys(), "Saved hidden actors do not cover the source contract")
    return {"objectCount":len(measured), "triangleCount":sum(item["triangles"] for item in measured),
            "maxBoundsErrorCm":max((item["maxBoundsErrorCm"] for item in measured),default=0),
            "maxTriangleErrorCm":max((item["maxTriangleErrorCm"] for item in measured),default=0),
            "objects":sorted(measured,key=lambda item:item["id"]), "assetHashes":_asset_hashes(asset_paths)}


def verify_hidden_collision_contract(scene, geometry_dir):
    """Call only after saving and reopening the generated map (no authoring)."""
    import unreal
    report = {"schemaVersion": 1}
    write_report(geometry_dir, report, "pending-saved-reload-verification")
    try:
        contract, records, triangles = verify_inputs(scene, geometry_dir)
        report = base_report(geometry_dir, contract)
        report.update(measure_world(unreal, records, triangles))
        report["verification"].update(nativeImported=True, savedReloaded=True, nativeTrianglesMeasured=True,
                                      persistedVisibilityFlagsVerified=True)
        write_report(geometry_dir, report, "hidden-collision-saved-reloaded-validated")
        return report
    except Exception as error:
        report["error"] = str(error)
        write_report(geometry_dir, report, "failed")
        raise
