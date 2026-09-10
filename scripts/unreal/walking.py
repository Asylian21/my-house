"""Author source-triangle walking collision; runtime CharacterMovement is separate."""
import hashlib
import json
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
OWNER = "scripts/unreal/walking.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_tags(obj, values):
    current = list(obj.get_editor_property("tags" if isinstance(obj, unreal.Actor) else "component_tags"))
    names = {str(value) for value in current}
    current.extend(unreal.Name(value) for value in values if value not in names)
    obj.set_editor_property("tags" if isinstance(obj, unreal.Actor) else "component_tags", current)


def bounds(component):
    origin, extent, _ = unreal.SystemLibrary.get_component_bounds(component)
    return {"min": [getattr(origin, axis) - getattr(extent, axis) for axis in ("x", "y", "z")],
            "max": [getattr(origin, axis) + getattr(extent, axis) for axis in ("x", "y", "z")]}


def apply_walking_contract(scene, meshes_by_id, geometry_dir):
    from materials import _asset_hashes

    geometry_dir = Path(geometry_dir)
    contract_file = geometry_dir / "walking.json"
    contract = json.loads(contract_file.read_text())
    if contract["provenance"]["sceneSha256"] != sha(geometry_dir / "scene.json"):
        raise RuntimeError("Walking collision contract has a stale source manifest")
    if contract["provenance"]["sourceObjSha256"] != scene["objSha256"]:
        raise RuntimeError("Walking collision contract has a stale source OBJ")
    if contract["provenance"]["writerSha256"] != sha(ROOT / "scripts/unreal/walking.mjs"):
        raise RuntimeError("Walking collision exporter changed")
    actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    references = {}
    for actor in actor_system.get_all_level_actors():
        ids = [str(tag) for tag in actor.get_editor_property("tags") if str(tag) in meshes_by_id]
        if not ids:
            continue
        if len(ids) != 1 or ids[0] in references:
            raise RuntimeError("Walking canonical actor identity is ambiguous")
        components = [component for component in actor.get_components_by_class(unreal.StaticMeshComponent)
                      if component.get_editor_property("static_mesh") == meshes_by_id[ids[0]]]
        if len(components) != 1:
            raise RuntimeError("Walking canonical mesh component is ambiguous: " + ids[0])
        references[ids[0]] = (actor, components[0])
    required = {entry["objectId"] for key in ("walkSurfaces", "staticBlockers", "capturedClosedBlockers")
                for entry in contract[key]}
    if not required.issubset(references):
        raise RuntimeError("Walking contract refers to missing canonical actors")

    changed_meshes, supports, closed, static = {}, [], [], []

    def collision(component):
        mesh = component.get_editor_property("static_mesh")
        body = mesh.get_editor_property("body_setup")
        if not body:
            raise RuntimeError("Walking mesh lacks BodySetup")
        body.set_editor_property("never_needs_cooked_collision_data", False)
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        component.set_collision_profile_name("BlockAll")
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        component.set_mobility(unreal.ComponentMobility.STATIC)
        changed_meshes[mesh.get_path_name()] = mesh

    before = {id_: bounds(references[id_][1]) for id_ in required}
    for entry in contract["staticBlockers"]:
        actor, component = references[entry["objectId"]]
        collision(component)
        static.append({"objectId": entry["objectId"], "component": component.get_path_name(),
                       "collision": "source-triangles-complex-as-simple"})
    for entry in contract["capturedClosedBlockers"]:
        actor, component = references[entry["objectId"]]
        collision(component)
        for obj in (actor, component):
            add_tags(obj, entry["runtimeTags"])
        closed.append({"objectId": entry["objectId"], "doorId": entry["doorId"],
                       "actor": actor.get_path_name(), "component": component.get_path_name(),
                       "state": "captured-closed", "collision": "source-triangles-complex-as-simple"})

    for entry in contract["walkSurfaces"]:
        actor, component = references[entry["objectId"]]
        offset = entry["supportOffsetCm"]
        if offset != 0:
            source_component = component
            support = actor_system.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator())
            if not support:
                raise RuntimeError("Could not create exact translated walking support")
            support.set_actor_label("Podklad chôdze · " + entry["walkSurfaceId"])
            support.set_folder_path("Brezi/WalkingSupport")
            add_tags(support, ["BreziGenerated", *entry["runtimeTags"], *entry["supportRuntimeTags"]])
            component = support.get_component_by_class(unreal.StaticMeshComponent)
            component.set_mobility(unreal.ComponentMobility.MOVABLE)
            component.set_static_mesh(source_component.get_editor_property("static_mesh"))
            transform = source_component.get_world_transform()
            position = transform.translation
            position.z += offset
            transform.translation = position
            # EditorActorSubsystem relies on Typed Elements, which are absent
            # in this commandlet. Use the actor API, then verify actual bounds.
            support.set_actor_transform(transform, False, True)
            component.set_visibility(False)
            component.set_hidden_in_game(True)
            component.set_cast_shadow(False)
            component.set_visible_in_ray_tracing(False)
            component.set_affect_distance_field_lighting(False)
            add_tags(component, [*entry["runtimeTags"], *entry["supportRuntimeTags"]])
            add_tags(actor, ["BreziWalkVisualSource"])
            add_tags(source_component, ["BreziWalkVisualSource"])
            actual = bounds(component)
            expected = {key: [value + (offset if axis == 2 else 0)
                              for axis, value in enumerate(before[entry["objectId"]][key])]
                        for key in ("min", "max")}
            error = max(abs(actual[key][axis] - expected[key][axis])
                        for key in ("min", "max") for axis in range(3))
            if error > 0.001:
                raise RuntimeError("Walking support differs from its authored translation")
            supports.append({"objectId": entry["objectId"], "walkSurfaceId": entry["walkSurfaceId"],
                             "actor": support.get_path_name(), "component": component.get_path_name(),
                             "supportOffsetCm": offset, "nativeBoundsCm": actual,
                             "maxTranslationErrorCm": error, "visible": False,
                             "sourceMeshReused": component.get_editor_property("static_mesh").get_path_name()})
        else:
            for obj in (actor, component):
                add_tags(obj, entry["runtimeTags"])
        collision(component)

    for id_ in required:
        if bounds(references[id_][1]) != before[id_]:
            raise RuntimeError("Walking authoring changed canonical visual geometry: " + id_)
    for mesh in changed_meshes.values():
        if not unreal.EditorAssetLibrary.save_loaded_asset(mesh):
            raise RuntimeError("Walking collision mesh did not save")
    return {"status": "walking-collision-authored", "contractSha256": sha(contract_file),
            "surfaceCount": len(contract["walkSurfaces"]), "translatedSupportCount": len(supports),
            "staticBlockerCount": len(static), "staticBlockers": static,
            "capturedClosedBlockerCount": len(closed), "supports": supports, "closedBlockers": closed,
            "canonicalVisualBoundsUnchanged": True,
            "assetHashes": _asset_hashes(changed_meshes),
            "pipelineFiles": {OWNER: sha(Path(__file__)), "scripts/unreal/walking.mjs": sha(ROOT / "scripts/unreal/walking.mjs")},
            "verification": {"editorAssetsAuthored": True, "runtimeQueriesVerified": False,
                             "characterMovementVerified": False, "doorAnimationImplemented": False}}
