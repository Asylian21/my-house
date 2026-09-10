"""One source-derived opaque emitter; native activation and visual QA pending.

Native entrypoints refuse noncanonical paths. No punctual lights, geometry, global
Lumen or exposure changes. A saved/reloaded receipt is not rendered validation.
"""
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p/"lib/twin-site.ts").is_file())
OWNER = "scripts/unreal/pendant-emitter/pendant_emitter.py"
PREFIX = "/Game/Brezi/MaterialStudies/PendantEmitter"
REVISION = "NATIVE-OPAQUE-PENDANT-800LM-20260908-1"
PRIOR = "BreziPendantOriginalState"
REVISION_TAG = "BreziPendantRevision"
FLAGS = {"emissiveLightSource":"emissive_light_source", "affectDynamicIndirectLighting":"affect_dynamic_indirect_lighting",
         "affectDistanceFieldLighting":"affect_distance_field_lighting", "visibleInRayTracing":"visible_in_ray_tracing", "castShadow":"cast_shadow"}


def load(path):
    spec = importlib.util.spec_from_file_location("brezi_pendant_"+Path(path).stem,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def reload_map(u, levels, path):
    require(levels.save_current_level(), "Pendant map save failed")
    require(u.EditorLoadingAndSavingUtils.new_blank_map(False), "Pendant map unload failed")
    require(levels.load_level(path), "Pendant map reload failed")


def write_report(path, report, status):
    report.update(status=status, generatedAt=datetime.now(timezone.utc).isoformat())
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
    temporary.replace(path)


def snapshot(u, common, found):
    from materials import _asset_hashes
    result = common.snapshot(u,found)
    for id_, (actor,c) in found.items():
        result["components"][id_].update({key:bool(c.get_editor_property(prop)) for key,prop in FLAGS.items()})
    result["canonicalAssetHashes"] = _asset_hashes([v[k] for v in result["components"].values() for k in ("mesh","meshMaterial","effectiveMaterial")])
    result["metadata"] = {id_:{key:u.EditorAssetLibrary.get_metadata_tag(actor,key) for key in (PRIOR,REVISION_TAG)} for id_,(actor,_) in found.items()}
    # All actor paths/classes must remain: this stage is forbidden from adding lights.
    result["worldActors"] = sorted((a.get_path_name(),a.get_class().get_path_name()) for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())
    return result


def source_guard(u, ref, common, found, contract, geometry_dir, allow_legacy_auto=False):
    from materials import _resolve_slot
    actor,c = found[ref.ID]
    mesh = c.get_editor_property("static_mesh")
    expected_mesh = "/Game/Brezi/Geometry/brezi-twin/StaticMeshes/"+ref.ID+"."+ref.ID
    require(mesh is not None and mesh.get_path_name() == expected_mesh, "Foreign mesh uses pendant source tag")
    # Render LOD is the normal Nanite fallback, not the source MeshDescription.
    require(mesh.get_num_triangles(0)>0 and mesh.get_num_tex_coords(0)>=1 and c.get_num_materials()==mesh.get_num_sections(0)==1, "Native pendant render topology/UV/slots differ")
    nanite = mesh.get_editor_property("nanite_settings")
    require(nanite.get_editor_property("enabled") and float(nanite.get_editor_property("fallback_percent_triangles")) == 1.0
            and float(nanite.get_editor_property("fallback_relative_error")) == 0.0
            and float(nanite.get_editor_property("keep_percent_triangles")) == 1.0
            and float(nanite.get_editor_property("trim_relative_error")) == 0.0, "Source globe Nanite/fallback policy differs")
    slots = mesh.get_editor_property("static_materials")
    require(len(slots) == 1 and _resolve_slot(slots[0],contract["record"],contract["scene"]["materials"]) == ref.SLOT, "Native pendant source slot differs")
    source = mesh.get_material(0)
    require(source.get_path_name() == "/Game/Brezi/Geometry/brezi-twin/Materials/MAT_0046.MAT_0046", "Native pendant source material differs")
    transform = c.get_world_transform()
    require(all(abs(float(getattr(transform.translation,k))) < 1e-6 and abs(float(getattr(transform.rotation,k))) < 1e-6 and abs(float(getattr(transform.scale3d,k))-1) < 1e-6 for k in ("x","y","z")) and abs(abs(float(transform.rotation.w))-1) < 1e-6, "Native source globe transform differs")
    lo,hi = contract["record"]["boundsMm"]["min"],contract["record"]["boundsMm"]["max"]
    origin,extent,_ = u.SystemLibrary.get_component_bounds(c)
    expected = [lo[0]/10,-hi[1]/10,lo[2]/10,hi[0]/10,-lo[1]/10,hi[2]/10]
    actual = [float(getattr(origin,k)-getattr(extent,k)) for k in ("x","y","z")]+[float(getattr(origin,k)+getattr(extent,k)) for k in ("x","y","z")]
    require(all(abs(a-b) < .002 for a,b in zip(actual,expected)), "Native globe bounds differ from source")
    require(c.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION, "Native globe unexpectedly has collision")
    require(c.get_editor_property("affect_dynamic_indirect_lighting") and c.get_editor_property("visible_in_ray_tracing"), "Pendant cannot contribute through current native GI/ray visibility")
    geometry=load(Path(__file__).with_name("source_geometry.py"))
    proof=geometry.read_and_verify(u,mesh,ref,Path(geometry_dir))
    target=nanite.get_editor_property("fallback_target")
    legacy=(allow_legacy_auto and target==u.NaniteFallbackTarget.AUTO)
    if legacy:
        # Explicit migration only for untouched source actors at full-import
        # pre-deletion. Active/untracked state never gets this exception.
        require(not any(u.EditorAssetLibrary.get_metadata_tag(actor,k) for k in (PRIOR,REVISION_TAG))
                and common.overrides(c)==[] and c.get_material(0)==source
                and not bool(c.get_editor_property("emissive_light_source")), "Legacy Auto migration requires untouched source pendant")
    else:
        require(target==u.NaniteFallbackTarget.PERCENT_TRIANGLES and mesh.get_num_triangles(0) in (2600,2704), "Full normal pendant fallback target/topology differs")
    proof.update(normalFallbackTarget=str(target),renderLod0Triangles=mesh.get_num_triangles(0),
                 fullNormalFallbackPolicyVerified=not legacy,legacyAutoMigrationValidated=legacy,rayTracingProxyTopologyVerified=False)
    return source,proof


def restore_component(u, common, actor, component, state, metadata):
    common.set_overrides(u,component,state["overrides"])
    component.set_emissive_light_source(state["emissiveLightSource"])
    require(bool(component.get_editor_property("emissive_light_source")) == state["emissiveLightSource"], "Pendant emitter flag restoration failed")
    for key,value in metadata.items():
        u.EditorAssetLibrary.set_metadata_tag(actor,key,value)


def recipe_hashes(ref,graph,common):
    files=[Path(__file__),Path(ref.__file__),Path(graph.__file__),Path(__file__).with_name("source_geometry.py"),Path(common.__file__),ROOT/"scripts/unreal/materials.py",
           ROOT/"unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.h",
           ROOT/"unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.cpp"]
    return {str(p.relative_to(ROOT)):ref.sha(p) for p in files}


def plan_reimport(row):
    """Strict live-actor policy; stale flags/bindings are never a recovery mode."""
    require(row["sourceId"]=="DOM_01375","Unexpected pendant cleanup source")
    metadata=row["metadata"];original=metadata.get(PRIOR,"");revision=metadata.get(REVISION_TAG,"")
    require(bool(original)==bool(revision),"Incomplete live pendant ownership metadata")
    if original:
        require(revision==REVISION and row["materialOwner"]==OWNER,"Foreign replacement of owned pendant override")
        require(row["overrides"]==[row["effectiveMaterial"]] and row["emissiveLightSource"] is True,"Owned pendant binding/emitter flag differs")
        recipe=row["recipeSha256"]
        require(isinstance(recipe,str) and re.fullmatch(r"[0-9a-f]{64}",recipe),"Pendant recipe provenance is missing")
        require(row["effectiveMaterial"]==PREFIX+"/V_"+recipe[:16]+"/M_Pendant800lm.M_Pendant800lm","Owned pendant material path differs")
        ref=load(Path(__file__).with_name("emitter_reference.py"));ref.validate_prior(json.loads(original))
    else:
        require(row["overrides"]==[] and row["effectiveMaterial"]==row["meshMaterial"] and row["materialOwner"]!=OWNER,"Untracked pendant component override")
        # Native UPrimitiveComponent initializes this flag false. Preserve a
        # caller's untracked true flag by refusing to destroy the actor.
        require(row["emissiveLightSource"] is False,"Untracked pendant emissive-source flag")
    return {"actor":row["actor"],"metadata":dict(metadata),"keys":(PRIOR,REVISION_TAG),"active":bool(original)}


def preflight_reimport(u,actors,scene,geometry_dir):
    """Pendant-specific live preflight; importer runs it before any actor deletion."""
    require(Path(__file__).resolve()==ROOT/OWNER,"Output-only pendant draft cannot mutate native assets")
    ref=load(Path(__file__).with_name("emitter_reference.py"));graph=load(Path(__file__).with_name("emitter_material.py"))
    common=load(ROOT/"scripts/unreal/tv-oak/tv_oak.py");contract=ref.verify_inputs(scene,geometry_dir);assets=u.EditorAssetLibrary
    selected=[]
    for actor in actors:
        if not actor.actor_has_tag("BreziGenerated"):continue
        tags={str(t) for t in actor.get_editor_property("tags")}
        metadata={str(k):str(v) for k,v in assets.get_metadata_tag_values(actor).items()}
        require(not {PRIOR,REVISION_TAG}.intersection(metadata) or ref.ID in tags,"Pendant ownership metadata on another live generated source")
        if ref.ID in tags:selected.append(actor)
    if not selected:return None
    require(len(selected)==1,"Duplicate live pendant source")
    actor=selected[0];cs=actor.get_components_by_class(u.StaticMeshComponent);require(len(cs)==1,"Live pendant component count differs")
    c=cs[0];source,source_proof=source_guard(u,ref,common,{ref.ID:(actor,c)},contract,geometry_dir,allow_legacy_auto=True)
    mesh=c.get_editor_property("static_mesh")
    require(assets.get_metadata_tag(mesh,"source_object_id")==ref.ID and assets.get_metadata_tag(mesh,"source_id")==ref.SOURCE_ID,"Live pendant mesh provenance differs")
    material=c.get_material(0);require(material is not None,"Live pendant material is missing")
    row={"sourceId":ref.ID,"actor":actor.get_path_name(),"metadata":{str(k):str(v) for k,v in assets.get_metadata_tag_values(actor).items()},
         "materialOwner":assets.get_metadata_tag(material,"BreziGeneratedBy"),"effectiveMaterial":material.get_path_name(),"meshMaterial":source.get_path_name(),
         "overrides":common.overrides(c),"emissiveLightSource":bool(c.get_editor_property("emissive_light_source")),"recipeSha256":assets.get_metadata_tag(material,"BreziPendantRecipeSha256")}
    plan=plan_reimport(row)
    plan["sourceGeometryProof"]=source_proof
    if plan["active"]:
        prior=json.loads(row["metadata"][PRIOR])
        require(all(p is None or u.load_object(None,p) is not None for p in prior["overrides"]),"Retained pendant source material missing")
        surface=graph.source_surface_proof(u,source,contract)
        recipe=ref.digest({"pipeline":recipe_hashes(ref,graph,common),"photometry":contract["photometry"],"surface":surface,"revision":REVISION})
        require(recipe==row["recipeSha256"],"Live pendant authoring recipe changed; explicit migration required")
        graph.working_space_proof(u,ref);graph.material_proof(u,material,contract,surface,recipe)
    return plan


def destroy_reimport_actor(assets,actor_system,actor,plan):
    """Remove only the pendant pair immediately before deleting its validated actor."""
    require(plan is not None and actor.get_path_name()==plan["actor"] and tuple(plan["keys"])==(PRIOR,REVISION_TAG),"Pendant destruction plan identity/scope differs")
    def current():return {str(k):str(v) for k,v in assets.get_metadata_tag_values(actor).items()}
    require(current()==plan["metadata"],"Live pendant metadata changed after preflight")
    expected={k:v for k,v in plan["metadata"].items() if k not in plan["keys"]}
    try:
        for key in plan["keys"]:
            if key in plan["metadata"]:assets.remove_metadata_tag(actor,key)
        require(current()==expected,"Pendant destruction cleanup changed unrelated metadata")
        require(actor_system.destroy_actor(actor),"Could not replace generated pendant actor")
    except Exception:
        for key in plan["keys"]:
            if key in plan["metadata"]:assets.set_metadata_tag(actor,key,plan["metadata"][key])
            else:assets.remove_metadata_tag(actor,key)
        require(current()==plan["metadata"],"Pendant deletion failure metadata rollback differs")
        raise


def execute(scene, geometry_dir, restore=False):
    require(Path(__file__).resolve() == ROOT/OWNER, "Output-only pendant draft cannot mutate native assets")
    import unreal as u
    from materials import _asset_hashes
    ref = load(Path(__file__).with_name("emitter_reference.py"))
    graph = load(Path(__file__).with_name("emitter_material.py"))
    common = load(ROOT/"scripts/unreal/tv-oak/tv_oak.py")
    report = {"schemaVersion":1,"revision":REVISION,"selectedIds":[ref.ID],"nativeApplied":False,"activationStarted":False,
              "rollbackRequired":False,"rollbackAttempted":False,"rollbackVerified":False,"rollbackErrors":[],
              "sourceStateVerifiedOnFailure":False,"geometryChanged":False,"renderedVerified":False,"pointLightsAdded":0,
              "globalQualityChanges":False,"nativeVertexAreaReadback":False,"renderFallbackAreaReadback":False,"rayTracingProxyTopologyVerified":False,
              "limitations":["800 intrinsic lm is authored, not measured lamp or delivered fixture flux.",
                             "Source shade is closed/capped; source-only quadrature estimated about 289 lm escaping before room transport, excluding shade interreflection.",
                             "A 20 cm bright emissive can remain noisy or under-light the room in Lumen; no global quality workaround is applied.",
                             "Native material/map reload proof does not measure shader working-space uniforms, rendered luminance, transport energy or 4K performance."]}
    report_path = Path(geometry_dir).parent/("pendant-emitter-restore-report.json" if restore else "pendant-emitter-report.json")
    before, found, map_path, material_path = None,None,None,None
    levels,assets = u.get_editor_subsystem(u.LevelEditorSubsystem),u.EditorAssetLibrary
    mutated = False
    try:
        write_report(report_path,report,"pending")
        contract = ref.verify_inputs(scene,geometry_dir)
        hashes = recipe_hashes(ref,graph,common)
        report.update(sourceManifestSha256=ref.SCENE_SHA,sourceObjSha256=ref.OBJ_SHA,sourceRecordSha256=contract["sourceRecordSha256"],
                      pipelineFiles=hashes,sourceGeometry=contract["geometry"],photometry=contract["photometry"],protectedIds=contract["protectedIds"])
        world = u.EditorLevelLibrary.get_editor_world()
        map_path = world.get_path_name().split(".")[0]
        require(map_path == "/Game/Brezi/Maps/Brezi" and assets.get_metadata_tag(world,"BreziGeneratedBy") == "scripts/unreal/import_scene.py", "Expected owned canonical Brezi map")
        found = common.components(u,contract["protectedIds"])
        source,source_proof = source_guard(u,ref,common,found,contract,geometry_dir)
        report["nativeSourceGeometryProof"]=source_proof
        report["nativeVertexAreaReadback"]=True
        surface = graph.source_surface_proof(u,source,contract)
        report["workingColorSpace"] = graph.working_space_proof(u,ref)
        report["sourceSurfaceProof"] = surface
        before = snapshot(u,common,found)
        report["nativeSelectedBefore"] = before["components"][ref.ID]
        report["protectedComponentSnapshotBeforeSha256"] = ref.digest(before["components"])
        actor,c = found[ref.ID]
        metadata = before["metadata"][ref.ID]
        require(bool(metadata[PRIOR]) == bool(metadata[REVISION_TAG]), "Incomplete pendant ownership state")
        prior = None
        if metadata[PRIOR]:
            require(metadata[REVISION_TAG] == REVISION and assets.get_metadata_tag(c.get_material(0),"BreziGeneratedBy") == OWNER, "Foreign replacement of owned pendant override")
            prior = json.loads(metadata[PRIOR])
            ref.validate_prior(prior)
            require(all(p is None or u.load_object(None,p) is not None for p in prior["overrides"]), "Retained pendant source material missing")
        recipe_sha = ref.digest({"pipeline":hashes,"photometry":contract["photometry"],"surface":surface,"revision":REVISION})
        report["recipeSha256"] = recipe_sha
        if restore:
            require(prior is not None,"No owned pendant override to restore")
            expected = ref.expected_components(before["components"],restored=prior)
            report["nativeApplied"] = True
        else:
            material = graph.create_material(u,PREFIX+"/V_"+recipe_sha[:16],contract,surface,recipe_sha)
            material_path = material.get_path_name()
            report["generatedAssetPaths"] = [material_path]
            del material,found,world,actor,c,source
            reload_map(u,levels,map_path)
            found = common.components(u,contract["protectedIds"])
            require(snapshot(u,common,found) == before,"Source state changed before pendant activation")
            report["stagedMaterialProof"] = graph.material_proof(u,u.load_object(None,material_path),contract,surface,recipe_sha)
            require(graph.working_space_proof(u,ref) == report["workingColorSpace"],"Working space drift before activation")
            expected = ref.expected_components(before["components"],material_path)
        actor,c = found[ref.ID]
        mutated = True
        report["activationStarted"] = True
        if restore:
            restore_component(u,common,actor,c,prior,{PRIOR:"",REVISION_TAG:""})
        else:
            if prior is None:
                prior = {"overrides":before["components"][ref.ID]["overrides"],"emissiveLightSource":before["components"][ref.ID]["emissiveLightSource"]}
            assets.set_metadata_tag(actor,PRIOR,metadata[PRIOR] or json.dumps(prior,sort_keys=True))
            assets.set_metadata_tag(actor,REVISION_TAG,REVISION)
            c.set_material(0,u.load_object(None,material_path))
            c.set_emissive_light_source(True)
            require(c.get_material(0).get_path_name() == material_path and bool(c.get_editor_property("emissive_light_source")),"Pendant activation readback failed")
        del found,actor,c
        reload_map(u,levels,map_path)
        found = common.components(u,contract["protectedIds"])
        _,saved_source_proof=source_guard(u,ref,common,found,contract,geometry_dir)
        require(saved_source_proof==source_proof,"Saved source geometry/fallback proof differs")
        report["savedReloadSourceGeometryProof"]=saved_source_proof
        after = snapshot(u,common,found)
        report["nativeSelectedAfter"] = after["components"][ref.ID]
        report["protectedComponentSnapshotAfterSha256"] = ref.digest(after["components"])
        require(after["components"] == expected,"Saved pendant/protected source mesh, UV, collision, flags or bindings differ")
        require(after["worldActors"] == before["worldActors"],"Pendant stage changed actor/light inventory")
        expected_metadata = {i:dict(v) for i,v in before["metadata"].items()}
        expected_metadata[ref.ID] = {PRIOR:"",REVISION_TAG:""} if restore else {PRIOR:metadata[PRIOR] or json.dumps(prior,sort_keys=True),REVISION_TAG:REVISION}
        require(after["metadata"] == expected_metadata,"Saved pendant/protected reversal metadata differs")
        require(_asset_hashes([v[k] for v in before["components"].values() for k in ("mesh","meshMaterial","effectiveMaterial")]) == before["canonicalAssetHashes"],"Pre-existing pendant/protected mesh or material bytes changed")
        require(graph.working_space_proof(u,ref) == report["workingColorSpace"],"Working color space changed")
        report.update(nativeApplied=not restore,canonicalAssetHashes=before["canonicalAssetHashes"],
                      bindings=[{"objectId":ref.ID,"sourceId":ref.SOURCE_ID,"sourceSlot":ref.SLOT,"material":expected[ref.ID]["effectiveMaterial"],
                                 "emissiveLightSource":expected[ref.ID]["emissiveLightSource"],"savedReloadVerified":True}],
                      verification={"twoMapReloads":not restore,"savedReloadVerified":True,"sourceMeshUvCollisionAndOtherFlagsAndAssetBytesUnchanged":True,
                                    "other28WarmBindingsAndCordShadeUnchanged":True,"actorLightInventoryUnchanged":True,"workingColorSpaceGetters":True})
        if not restore:
            report["savedReloadMaterialProof"] = graph.material_proof(u,u.load_object(None,material_path),contract,surface,recipe_sha)
            report["assetHashes"] = _asset_hashes([material_path])
        write_report(report_path,report,"source-overrides-restored" if restore else "native-pendant-emitter-saved-reload-validated")
        return report
    except Exception as error:
        report.update(error=str(error),rollbackRequired=mutated)
        if before:
            try:
                if u.EditorLevelLibrary.get_editor_world().get_path_name().split(".")[0] != map_path:
                    report["mapRecoveryAttempted"] = True
                    require(levels.load_level(map_path),"Pendant failure map recovery failed")
                if mutated:
                    report["rollbackAttempted"] = True
                    found = common.components(u,contract["protectedIds"])
                    actor,c = found[ref.ID]
                    restore_component(u,common,actor,c,before["components"][ref.ID],before["metadata"][ref.ID])
                    del found,actor,c
                    reload_map(u,levels,map_path)
                require(u.EditorLevelLibrary.get_editor_world().get_path_name().split(".")[0] == map_path,"Pendant failure left another map active")
                found = common.components(u,contract["protectedIds"])
                require(snapshot(u,common,found) == before,"Pendant failure did not preserve exact source state")
                report.update(rollbackVerified=mutated,sourceStateVerifiedOnFailure=True,nativeApplied=restore,
                              sourceStateCheckStage="saved-reloaded-rollback" if mutated else "saved-map-recovery" if report.get("mapRecoveryAttempted") else "live-before-activation")
            except Exception as rollback_error:
                report["rollbackErrors"].append(str(rollback_error))
        write_report(report_path,report,"restore-failed" if restore else "failed")
        raise


def apply_pendant_emitter(scene, geometry_dir):
    return execute(scene,geometry_dir)


def restore_pendant_emitter(scene, geometry_dir):
    return execute(scene,geometry_dir,restore=True)
