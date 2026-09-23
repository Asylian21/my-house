"""Bind verified web door members to stable cooked runtime tags, at closed pose.

Call apply_doors_contract AFTER walking and hidden collision authoring. Call
verify_doors_contract only after saving and reloading the map. No mesh vertices,
materials, pivots or synthesized collision shapes are authored here.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = "scripts/unreal/doors.py"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_contract(scene, directory):
    directory = Path(directory)
    contract = json.loads((directory / "doors.json").read_text())
    require(contract.get("status") == "source-door-motion-validated" and contract.get("initialState") == "CLOSED",
            "Unvalidated source door motion contract")
    require(contract["sourceManifestSha256"] == sha(directory / "scene.json")
            and contract["sourceObjSha256"] == scene["objSha256"]
            and contract["hiddenCollisionSha256"] == sha(directory / "hidden-collision.json"), "Door source receipt is stale")
    for path, digest in contract["pipelineFiles"].items():
        require(sha(ROOT / path) == digest, "Door source pipeline changed: " + path)
    return contract, sha(directory / "doors.json")


def measure(unreal, component, member):
    origin, extent, _ = unreal.SystemLibrary.get_component_bounds(component)
    actual = {"min": [getattr(origin - extent, k) for k in ("x", "y", "z")],
              "max": [getattr(origin + extent, k) for k in ("x", "y", "z")]}
    error = max(abs(actual[k][axis] - member["closedBoundsCm"][k][axis]) for k in ("min", "max") for axis in range(3))
    require(error <= .05, "Door closed source bounds differ: " + member["sourceName"])
    expected = unreal.CollisionEnabled.QUERY_AND_PHYSICS if member["collision"] else unreal.CollisionEnabled.NO_COLLISION
    require(component.get_collision_enabled() == expected, "Door collision differs from source: " + member["sourceName"])
    if member["collision"]:
        body = component.get_editor_property("static_mesh").get_editor_property("body_setup")
        require(body.get_editor_property("collision_trace_flag") == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
                and component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN) == unreal.CollisionResponseType.ECR_BLOCK,
                "Door collider does not use blocking source triangles")
    require(component.is_visible() is not member["hidden"], "Door source visibility differs")
    return error


def apply_doors_contract(scene, directory):
    import unreal
    contract, digest = load_contract(scene, directory)
    runtime_digest = hashlib.sha1((Path(directory) / "doors.json").read_bytes()).hexdigest()
    actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    changes = []
    # Resolve every member before the first component mobility/tag mutation.
    for door in contract["doors"]:
        for member in door["members"]:
            id_ = member["sourceObjectId"]
            source_tag = "BreziSourceObjectId=" + id_ if member["hidden"] else id_
            matches = [actor for actor in actors if actor.actor_has_tag(source_tag) and not actor.actor_has_tag("BreziWalkSupportProxy")]
            require(len(matches) == 1, "Missing/ambiguous native door member: " + member["sourceName"])
            actor = matches[0]
            components = list(actor.get_components_by_class(unreal.StaticMeshComponent))
            require(len(components) == 1, "Door source actor component count differs")
            component = components[0]
            if member["hidden"]:
                require(actor.actor_has_tag("BreziSourceId=" + member["sourceId"]), "Hidden door member source identity differs")
            else:
                mesh = component.get_editor_property("static_mesh")
                require(unreal.EditorAssetLibrary.get_metadata_tag(mesh, "source_id") == member["sourceId"]
                        and unreal.EditorAssetLibrary.get_metadata_tag(mesh, "source_name") == member["sourceName"], "Door mesh source identity differs")
            require(not any(a.actor_has_tag("BreziWalkSupportProxy") and a.actor_has_tag("BreziSourceObjectId=" + id_) for a in actors),
                    "A moving door has a separate frozen walking support; explicit dynamic support export is required")
            error = measure(unreal, component, member)
            changes.append((actor, component, door, member, error))
    for actor, component, door, member, _ in changes:
        tags = [member["runtimeTag"], "BreziDoorId=" + door["id"], "BreziDoorContract=" + digest, "BreziDoorContractSha1=" + runtime_digest, "BreziDoorMovable"]
        for target, property_ in ((actor, "tags"), (component, "component_tags")):
            current = list(target.get_editor_property(property_))
            current_names = {str(value) for value in current}
            current.extend(unreal.Name(tag) for tag in tags if tag not in current_names)
            target.set_editor_property(property_, current)
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
    return {"status": "source-doors-bound-reload-pending", "contractSha256": digest,
            "doorCount": len(contract["doors"]), "architecturalDoorCount": len(contract["architecturalInventory"]),
            "memberCount": len(changes), "maxClosedBoundsErrorCm": max(c[4] for c in changes),
            "geometryModified": False, "nativeRuntimeVerified": False,
            "pipelineFiles": {OWNER: sha(__file__), "scripts/unreal/doors.mjs": sha(ROOT / "scripts/unreal/doors.mjs")}}


def verify_doors_contract(scene, directory):
    import unreal
    contract, digest = load_contract(scene, directory)
    runtime_digest = hashlib.sha1((Path(directory) / "doors.json").read_bytes()).hexdigest()
    actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    maximum, count = 0, 0
    for door in contract["doors"]:
        for member in door["members"]:
            matches = [a for a in actors if a.actor_has_tag(member["runtimeTag"]) and a.actor_has_tag("BreziDoorContract=" + digest) and a.actor_has_tag("BreziDoorContractSha1=" + runtime_digest)]
            require(len(matches) == 1, "Saved door binding missing or duplicated")
            component = matches[0].get_component_by_class(unreal.StaticMeshComponent)
            require(component.get_editor_property("mobility") == unreal.ComponentMobility.MOVABLE
                    and component.component_has_tag(member["runtimeTag"]), "Saved door member lost mobility/tags")
            maximum = max(maximum, measure(unreal, component, member)); count += 1
    require(sum(a.actor_has_tag("BreziDoorMovable") for a in actors) == count, "Unexpected door-bound native actors")
    return {"status": "source-doors-saved-reloaded-validated", "contractSha256": digest,
            "doorCount": len(contract["doors"]), "architecturalDoorCount": len(contract["architecturalInventory"]),
            "memberCount": count, "maxClosedBoundsErrorCm": maximum, "savedReloaded": True,
            "geometryModified": False, "nativeRuntimeVerified": False,
            "pipelineFiles": {OWNER: sha(__file__), "scripts/unreal/doors.mjs": sha(ROOT / "scripts/unreal/doors.mjs")}}
