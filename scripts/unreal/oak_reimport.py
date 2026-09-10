"""Retire only oak actor metadata at the full-import actor destruction boundary.

No repair mode: stale/foreign active bindings fail before any actor is deleted.
Standalone furniture/TV material authoring and their reversal recipes are unchanged.
"""
import json
import re

TV_IDS=frozenset(("DOM_01293","DOM_01296","DOM_01300"))
FURNITURE_IDS=frozenset(("DOM_00613","DOM_00643","DOM_00647","DOM_00650","DOM_01328","DOM_01345","DOM_01354","DOM_01363","DOM_01372"))
TV_KEYS=("BreziTVOakOriginalOverrides","BreziTVOakRevision")
FURNITURE_KEYS=("BreziFurnitureOakOriginalOverrides","BreziFurnitureOakRevision")
ALL_KEYS=frozenset(TV_KEYS+FURNITURE_KEYS)
PENDANT_KEYS=("BreziPendantOriginalState","BreziPendantRevision")
WITH_PENDANT_KEYS=ALL_KEYS|frozenset(PENDANT_KEYS)


def require(value,message):
    if not value:raise RuntimeError(message)


def metadata(assets,actor):
    return {str(k):str(v) for k,v in assets.get_metadata_tag_values(actor).items()}


def plan_row(row):
    """Pure policy; callers additionally prove source geometry and native graph."""
    id_=row["id"];is_tv=id_ in TV_IDS
    require(id_ in TV_IDS|FURNITURE_IDS,"Unexpected oak cleanup source ID")
    keys=TV_KEYS if is_tv else FURNITURE_KEYS
    meta=row["metadata"]
    require(not (ALL_KEYS-set(keys)).intersection(meta),"Foreign oak metadata scope: "+id_)
    original,revision=(meta.get(key,"") for key in keys)
    require(bool(original)==bool(revision),"Incomplete oak ownership metadata: "+id_)
    if original:
        expected_revision="NATIVE-TV-CABINET-PHOTO-OAK-20260908-1" if is_tv else "NATIVE-NINE-BOX-PHOTO-OAK-20260908-1"
        owner="scripts/unreal/tv-oak/tv_oak.py" if is_tv else "scripts/unreal/furniture-oak/furniture_oak.py"
        prefix="TVPhotoOak" if is_tv else "FurniturePhotoOak"
        name="M_TVCabinetPhotoOak" if is_tv else ("M_KitchenPhotoOak" if id_ in {"DOM_00613","DOM_00643","DOM_00647","DOM_00650"} else "M_DiningPhotoOak")
        require(revision==expected_revision,"Unknown oak revision: "+id_)
        require(row["materialOwner"]==owner and re.fullmatch(r"/Game/Brezi/MaterialStudies/"+prefix+r"/V_[0-9a-f]{16}/Materials/"+name+r"\."+name,row["effectiveMaterial"]),"Refusing foreign replacement of owned oak override: "+id_)
        require(row["overrides"]==[row["effectiveMaterial"]],"Owned oak override array differs: "+id_)
        prior=json.loads(original)
        require(isinstance(prior,list) and all(p is None or isinstance(p,str) and p for p in prior),"Invalid retained oak reversal recipe: "+id_)
    else:
        require(row["overrides"]==[] and row["effectiveMaterial"]==row["meshMaterial"],"Refusing foreign untracked oak component override: "+id_)
        require(row["materialOwner"] not in {"scripts/unreal/tv-oak/tv_oak.py","scripts/unreal/furniture-oak/furniture_oak.py"},"Oak material lacks reversal ownership: "+id_)
    return {"id":id_,"actor":row["actor"],"keys":keys,"metadata":dict(meta),"active":bool(original)}


def preflight(u,actors,scene,geometry_dir):
    """Read/validate every affected actor before prepare_world destroys anything."""
    import furniture_reference as ref
    common=ref.load_tv("tv_oak");contract=ref.verify_inputs(scene,geometry_dir)
    all_ids=TV_IDS|FURNITURE_IDS;found={};assets=u.EditorAssetLibrary
    for actor in actors:
        if not actor.actor_has_tag("BreziGenerated"):continue
        ids=all_ids.intersection(str(t) for t in actor.get_editor_property("tags"))
        meta=metadata(assets,actor)
        require(not ALL_KEYS.intersection(meta) or len(ids)==1,"Oak metadata on unknown generated actor")
        if not ids:continue
        require(len(ids)==1 and next(iter(ids)) not in found,"Duplicate/ambiguous generated oak source")
        id_=next(iter(ids));components=actor.get_components_by_class(u.StaticMeshComponent)
        require(len(components)==1,"Oak source component count differs")
        found[id_]=(actor,components[0])
    if not found:return {}
    require(set(found)==all_ids,"Generated oak source coverage differs")
    common.guard_native_targets(u,found,contract,all_ids,{**ref.SLOTS,**{i:"MAT_0078" for i in TV_IDS}})
    plans={}
    for id_,(actor,c) in sorted(found.items()):
        mesh=c.get_editor_property("static_mesh");record=contract["records"][id_]
        require(mesh.get_path_name()==f"/Game/Brezi/Geometry/brezi-twin/StaticMeshes/{id_}.{id_}","Foreign oak mesh path")
        require(assets.get_metadata_tag(mesh,"source_object_id")==id_ and assets.get_metadata_tag(mesh,"source_id")==record["sourceId"],"Oak mesh source provenance differs")
        transform=c.get_world_transform()
        require(all(abs(float(getattr(transform.translation,k)))<1e-6 for k in ("x","y","z")) and all(abs(float(getattr(transform.rotation,k)))<1e-6 for k in ("x","y","z")) and abs(abs(float(transform.rotation.w))-1)<1e-6,"Oak source transform differs")
        material=c.get_material(0);require(material is not None,"Oak effective material missing")
        row={"id":id_,"actor":actor.get_path_name(),"metadata":metadata(assets,actor),"materialOwner":assets.get_metadata_tag(material,"BreziGeneratedBy"),"effectiveMaterial":material.get_path_name(),"meshMaterial":mesh.get_material(0).get_path_name(),"overrides":common.overrides(c)}
        plan=plan_row(row)
        if plan["active"]:
            for path in json.loads(row["metadata"][plan["keys"][0]]):require(path is None or u.load_object(None,path) is not None,"Retained oak source material missing")
            if id_ in TV_IDS:common.material_proof(u,material,ref.load_tv("oak_reference").verify_inputs(scene,geometry_dir))
            else:
                group="kitchen" if id_ in ref.KITCHEN_IDS else "dining"
                common.material_proof(u,material,contract["groups"][group],contract["profiles"][group])
        plans[plan["actor"]]=plan
    return plans


def destroy_with_cleanup(assets,actor_system,actor,plan=None):
    """Presence-aware cleanup, compensating only this actor if deletion fails."""
    if plan is None:
        require(actor_system.destroy_actor(actor),"Could not replace generated actor")
        return
    require(actor.get_path_name()==plan["actor"] and metadata(assets,actor)==plan["metadata"],"Oak metadata drift after preflight")
    expected={k:v for k,v in plan["metadata"].items() if k not in plan["keys"]}
    try:
        for key in plan["keys"]:assets.remove_metadata_tag(actor,key)
        require(metadata(assets,actor)==expected,"Oak cleanup changed unrelated metadata or retained a key")
        require(actor_system.destroy_actor(actor),"Could not replace generated oak actor")
    except Exception:
        for key in plan["keys"]:
            if key in plan["metadata"]:assets.set_metadata_tag(actor,key,plan["metadata"][key])
            else:assets.remove_metadata_tag(actor,key)
        require(metadata(assets,actor)==plan["metadata"],"Oak metadata rollback differs after failed actor destruction")
        raise


def validate_creation_key_scope(key_scope):
    """Only the default oak4 or explicitly enabled oak4+pendant2 may be retired."""
    require(isinstance(key_scope,(tuple,list,set,frozenset)),"Unsupported fresh metadata key scope type")
    keys=tuple(key_scope)
    require(all(isinstance(k,str) for k in keys) and len(keys)==len(set(keys)) and frozenset(keys) in (ALL_KEYS,WITH_PENDANT_KEYS),"Unknown, partial or duplicated fresh metadata key scope")
    return tuple(sorted(keys))


def plan_created_row(row,pre_import_actor_paths,key_scope=ALL_KEYS):
    """Pure policy for a proven fresh canonical actor, including cross-scope keys."""
    keys=validate_creation_key_scope(key_scope)
    require(row["actor"] not in pre_import_actor_paths,"Fresh actor reuses a surviving pre-import actor")
    ids=row["sourceIds"];bindings=row["bindings"]
    require(ids and len(ids)==len(set(ids)) and len(bindings)==len(ids) and {b["id"] for b in bindings}==set(ids),"Fresh canonical actor source binding coverage differs")
    for binding in bindings:
        require(binding["overrides"]==[] and binding["effectiveMaterial"]==binding["meshMaterial"],"Fresh source actor has a component material override: "+binding["id"]+" at "+row["actor"]+"; overrides="+repr(binding["overrides"])+"; effective="+repr(binding["effectiveMaterial"])+"; mesh="+repr(binding["meshMaterial"]))
        require(binding["materialOwner"] not in {"scripts/unreal/tv-oak/tv_oak.py","scripts/unreal/furniture-oak/furniture_oak.py"},"Fresh mesh material is an old oak override")
        require(frozenset(keys)!=WITH_PENDANT_KEYS or binding["materialOwner"]!="scripts/unreal/pendant-emitter/pendant_emitter.py","Fresh mesh material is an existing pendant override")
    return {"sourceIds":list(ids),"actor":row["actor"],"keys":keys,"metadata":dict(row["metadata"]),"fresh":True}


def plans_for_created_rows(rows,pre_import_actor_paths,expected_source_ids,key_scope=ALL_KEYS):
    keys=validate_creation_key_scope(key_scope)
    ids=[id_ for row in rows for id_ in row["sourceIds"]]
    require(len(ids)==len(set(ids)) and set(ids)==set(expected_source_ids),"Fresh canonical source coverage differs")
    require(len({r["actor"] for r in rows})==len(rows),"Fresh canonical actor paths are not unique")
    return [plan_created_row(row,pre_import_actor_paths,keys) for row in rows]


def clear_created_metadata(assets,actors_by_path,plans,key_scope=ALL_KEYS):
    """All plans are preflighted before writes; compensate exact keys on failure."""
    keys=validate_creation_key_scope(key_scope)
    for plan in plans:
        require(plan.get("fresh") is True and plan["actor"] in actors_by_path,"Missing validated fresh oak actor")
        require(tuple(plan["keys"])==keys and actors_by_path[plan["actor"]].get_path_name()==plan["actor"],"Fresh metadata plan key scope or actor identity differs")
        require(metadata(assets,actors_by_path[plan["actor"]])==plan["metadata"],"Fresh oak metadata drift before initialization")
    touched=[]
    try:
        for plan in plans:
            actor=actors_by_path[plan["actor"]];touched.append(plan)
            for key in plan["keys"]:
                if key in plan["metadata"]:assets.remove_metadata_tag(actor,key)
            require(metadata(assets,actor)=={k:v for k,v in plan["metadata"].items() if k not in plan["keys"]},"Fresh oak initialization changed unrelated metadata or retained a key")
    except Exception:
        for plan in reversed(touched):
            actor=actors_by_path[plan["actor"]]
            for key in plan["keys"]:
                if key in plan["metadata"]:assets.set_metadata_tag(actor,key,plan["metadata"][key])
                else:assets.remove_metadata_tag(actor,key)
            require(metadata(assets,actor)==plan["metadata"],"Fresh oak metadata rollback differs")
        raise
    return sum(key in plan["metadata"] for plan in plans for key in plan["keys"])


def initialize_created_actors(u,created_actors,pre_import_actor_paths,assets_by_id,records,key_scope=ALL_KEYS):
    """Initialize only actual newly imported canonical actors after source measurement.

    Actor paths can revive arbitrary historical oak entries. No existing actor
    or package-wide orphan entry is edited. Meshless hierarchy actors are only
    recorded; every expected source ID must map to its measured mesh component.
    """
    keys=validate_creation_key_scope(key_scope)
    assets=u.EditorAssetLibrary;paths=[a.get_path_name() for a in created_actors]
    require(len(paths)==len(set(paths)) and not set(paths).intersection(pre_import_actor_paths),"Interchange returned duplicate or pre-existing actors")
    require(set(assets_by_id)==set(records),"Fresh measured source mesh coverage differs")
    rows=[];hierarchy=[];actors_by_path={a.get_path_name():a for a in created_actors}
    for actor in created_actors:
        require(actor.actor_has_tag("BreziGenerated"),"Interchange actor lacks current generator tag")
        tagged=set(str(t) for t in actor.get_editor_property("tags")) & records.keys()
        components=[c for c in actor.get_components_by_class(u.StaticMeshComponent) if c.get_editor_property("static_mesh") is not None]
        meta=metadata(assets,actor)
        if not components:
            require(not tagged,"Fresh hierarchy actor carries a measured source identity")
            require(not set(keys).intersection(meta),"Unexpected orphan override keys on fresh noncanonical hierarchy actor: "+actor.get_path_name())
            hierarchy.append({"actor":actor.get_path_name(),"metadata":meta})
            continue
        bindings=[]
        for c in components:
            mesh=c.get_editor_property("static_mesh");id_=mesh.get_name()
            require(id_ in records and id_ in tagged and assets_by_id.get(id_)==mesh,"Fresh actor is not bound to its source-validated mesh: "+id_+" at "+actor.get_path_name())
            record=records[id_]
            require(mesh.get_path_name()==f"/Game/Brezi/Geometry/brezi-twin/StaticMeshes/{id_}.{id_}","Fresh canonical mesh path differs")
            require(assets.get_metadata_tag(mesh,"source_object_id")==id_ and assets.get_metadata_tag(mesh,"source_id")==record["sourceId"],"Fresh mesh source provenance differs")
            origin,extent,_=u.SystemLibrary.get_component_bounds(c)
            lo,hi=record["boundsMm"]["min"],record["boundsMm"]["max"]
            expected=[lo[0]/10,-hi[1]/10,lo[2]/10,hi[0]/10,-lo[1]/10,hi[2]/10]
            actual=[float(getattr(origin,k)-getattr(extent,k)) for k in ("x","y","z")]+[float(getattr(origin,k)+getattr(extent,k)) for k in ("x","y","z")]
            require(all(abs(a-b)<=.05 for a,b in zip(actual,expected)),"Fresh canonical world bounds differ from measured source")
            count=c.get_num_materials()
            require(count==len(mesh.get_editor_property("static_materials")) and count>0,"Fresh component source material coverage differs")
            overrides=[m.get_path_name() if m else None for m in c.get_editor_property("override_materials")]
            # Each slot is checked; the row keeps native material arrays intact.
            effective=[];source=[];owners=[]
            for slot in range(count):
                material=c.get_material(slot);base=mesh.get_material(slot)
                require(material is not None and base is not None,"Fresh source material missing")
                effective.append(material.get_path_name());source.append(base.get_path_name());owners.append(assets.get_metadata_tag(material,"BreziGeneratedBy"))
            require(not set(owners).intersection({"scripts/unreal/tv-oak/tv_oak.py","scripts/unreal/furniture-oak/furniture_oak.py"}),"Fresh source contains an existing oak override")
            require(frozenset(keys)!=WITH_PENDANT_KEYS or "scripts/unreal/pendant-emitter/pendant_emitter.py" not in owners,"Fresh source contains an existing pendant override")
            bindings.append({"id":id_,"meshMaterial":source,"effectiveMaterial":effective,"overrides":overrides,"materialOwner":""})
        require({b["id"] for b in bindings}==tagged,"Fresh actor source tags/component identities differ")
        rows.append({"actor":actor.get_path_name(),"sourceIds":sorted(tagged),"metadata":meta,"bindings":bindings})
    plans=plans_for_created_rows(rows,pre_import_actor_paths,records.keys(),keys)
    removed=clear_created_metadata(assets,actors_by_path,plans,keys)
    require(all(metadata(assets,actors_by_path[h["actor"]])==h["metadata"] for h in hierarchy),"Hierarchy metadata changed during source initialization")
    affected=[{"sourceIds":p["sourceIds"],"actor":p["actor"],"removedKeys":sorted(set(keys).intersection(p["metadata"]))} for p in plans if set(keys).intersection(p["metadata"])]
    return {"sourceIds":sorted(records),"createdActorPaths":paths,"preImportActorPaths":sorted(pre_import_actor_paths),
            "sourceActorPaths":{id_:p["actor"] for p in plans for id_ in p["sourceIds"]},"hierarchyActorPaths":[h["actor"] for h in hierarchy],
            "hierarchyMetadataUnchanged":True,"freshnessVerified":True,"sourceMeshIdentityAndGeometryVerified":True,
            "emptySourceOverridesVerified":True,"removedKeyCount":removed,"affectedActors":affected,"otherMetadataUnchanged":True,
            "metadataReadbackVerified":True,"activeOverrideGuardUnchanged":True,"packageOrphanMetadataCleared":False,
            "initializedOwnedKeys":list(keys)}
