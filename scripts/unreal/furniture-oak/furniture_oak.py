"""Exact nine-component photo-oak overlay, staged output-only until adoption.

No mesh/UV/collision edits or geometry generation. Two explicit graph profiles
reuse the TV writer; native execution is guarded to the production script path.
"""
import importlib.util
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=next(p for p in Path(__file__).resolve().parents if (p/"lib/twin-site.ts").is_file())
OWNER="scripts/unreal/furniture-oak/furniture_oak.py"
PREFIX="/Game/Brezi/MaterialStudies/FurniturePhotoOak"
REVISION="NATIVE-NINE-BOX-PHOTO-OAK-20260908-1"
ORIGINAL="BreziFurnitureOakOriginalOverrides"
REVISION_TAG="BreziFurnitureOakRevision"


def reference():
    spec=importlib.util.spec_from_file_location("brezi_furniture_reference",Path(__file__).with_name("furniture_reference.py"))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def require(value,message):
    if not value:raise RuntimeError(message)


def _guard(u,common,ref,found,contract):
    common.guard_native_targets(u,found,contract,ref.IDS,ref.SLOTS)
    for id_ in ref.IDS:
        _,component=found[id_];mesh=component.get_editor_property("static_mesh")
        require(mesh.get_path_name()==f"/Game/Brezi/Geometry/brezi-twin/StaticMeshes/{id_}.{id_}","Foreign mesh shares source tag/bounds: "+id_)
        transform=component.get_world_transform()
        require(all(abs(float(getattr(transform.translation,k)))<1e-6 for k in ("x","y","z")),"Canonical furniture translation differs")
        require(all(abs(float(getattr(transform.rotation,k)))<1e-6 for k in ("x","y","z"))
                and abs(abs(float(transform.rotation.w))-1)<1e-6,"Canonical furniture rotation differs")


def _snapshot(u,common,ref,found):
    from materials import _asset_hashes
    result=common.snapshot(u,found)
    # Include original mesh materials even when a TV/component override is active.
    paths=[value[key] for value in result["components"].values() for key in ("mesh","meshMaterial","effectiveMaterial")]
    result["sourceAndEffectiveAssetHashes"]=_asset_hashes(paths)
    result["protectedTVMetadata"]={i:{key:u.EditorAssetLibrary.get_metadata_tag(found[i][0],key)
        for key in (common.ORIGINAL,common.REVISION_TAG)} for i in sorted(ref.TV_IDS)}
    return result


def _source_hashes(before):
    from materials import _asset_hashes
    return _asset_hashes([value[key] for value in before["components"].values() for key in ("mesh","meshMaterial","effectiveMaterial")])


def _reload(u,levels,map_path):
    require(levels.save_current_level(),"Furniture material map save failed")
    require(u.EditorLoadingAndSavingUtils.new_blank_map(False),"Furniture map unload failed")
    require(levels.load_level(map_path),"Furniture map reload failed")


def _write(path,report,status):
    report.update(status=status,generatedAt=datetime.now(timezone.utc).isoformat())
    temp=path.with_suffix(".tmp");temp.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n");temp.replace(path)


def apply_furniture_oak(scene,geometry_dir):
    require(Path(__file__).resolve()==ROOT/OWNER,"Output-only furniture draft cannot mutate native assets")
    import unreal as u
    from materials import _asset_hashes
    ref=reference();common=ref.load_tv("tv_oak");contract=ref.verify_inputs(scene,geometry_dir)
    files=[Path(__file__),Path(__file__).with_name("furniture_reference.py"),Path(__file__).with_name("longitudinal-basis.hlsl"),
           Path(common.__file__),Path(common.__file__).with_name("oak_reference.py"),Path(common.__file__).with_name("oak-basis.hlsl"),ref.STUDY/"candidate.json"]
    files += [ROOT/spec["path"] for spec in contract["candidate"]["maps"].values()]
    files += [ROOT/"public"/contract["scene"]["materials"][slot]["texture"].lstrip("/") for slot in ("MAT_0039","MAT_0080")]
    hashes={str(path.relative_to(ROOT)):ref.sha(path) for path in files};prefix=PREFIX+"/V_"+ref.digest(hashes)[:16]
    writers={name:common.Writer(u,prefix,group,contract["profiles"][name]) for name,group in contract["groups"].items()}
    report_path=Path(geometry_dir).parent/"furniture-oak-report.json"
    report={"schemaVersion":1,"status":"pending","revision":REVISION,"nativeApplied":False,"renderedVerified":False,"geometryChanged":False,
            "activationStarted":False,"rollbackRequired":False,"rollbackAttempted":False,"rollbackVerified":False,
            "selectedIds":sorted(ref.IDS),"protectedTVIds":sorted(ref.TV_IDS),"woodObjects":158,"preservedWoodObjects":149,
            "sourceManifestSha256":ref.load_tv("oak_reference").SCENE_SHA,"sourceObjSha256":ref.load_tv("oak_reference").OBJ_SHA,
            "sourceRecordHashes":{i:ref.digest(contract["records"][i]) for i in sorted(ref.IDS)},"pipelineFiles":hashes,
            "periodCm":ref.PERIOD_CM,"normalStrength":ref.NORMAL_STRENGTH,
            "groups":{name:{"selectedIds":group["selectedIds"],"sourceSlot":group["sourceSlot"],"grain":group["grain"],"anchorCm":group["anchorCm"],
                             "sourceRoughness":group["sourceRoughness"],"palette":contract["profiles"][name]["palette"]} for name,group in contract["groups"].items()},
            "limitations":["Photographed CC0 veneer candidate, not measured product/finish or solid-oak end grain.",
                           "No rounded geometry. Per-face veneer seams and transverse end faces require visual review.",
                           "Native getter/reload proof is not cooked Metal, resident-mip, appearance or performance proof."]}
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);assets=u.EditorAssetLibrary
    before=None;metadata={};map_path=None;mutated=False
    try:
        _write(report_path,report,"pending")
        world=u.EditorLevelLibrary.get_editor_world();map_path=world.get_path_name().split(".")[0]
        require(map_path=="/Game/Brezi/Maps/Brezi" and assets.get_metadata_tag(world,"BreziGeneratedBy")=="scripts/unreal/import_scene.py","Expected owned canonical map")
        found=common.components(u,contract["woodIds"]);_guard(u,common,ref,found,contract);before=_snapshot(u,common,ref,found)
        for id_ in sorted(ref.IDS):
            actor,component=found[id_];metadata[id_]={key:assets.get_metadata_tag(actor,key) for key in (ORIGINAL,REVISION_TAG)}
            existing=metadata[id_]
            require(bool(existing[ORIGINAL])==bool(existing[REVISION_TAG]),"Incomplete furniture override ownership metadata")
            if existing[ORIGINAL]:
                require(existing[REVISION_TAG]==REVISION and assets.get_metadata_tag(component.get_material(0),"BreziGeneratedBy")==OWNER,"Refusing foreign replacement of an owned furniture override")
                previous=json.loads(existing[ORIGINAL]);require(isinstance(previous,list),"Invalid retained source override recipe")
                for path in previous:require(path is None or isinstance(path,str) and u.load_object(None,path) is not None,"Retained source material missing")
        del found,world
        material_paths={name:writer.material().get_path_name() for name,writer in writers.items()}
        bindings={id_:material_paths["kitchen" if id_ in ref.KITCHEN_IDS else "dining"] for id_ in ref.IDS}
        _reload(u,levels,map_path);found=common.components(u,contract["woodIds"])
        require(_snapshot(u,common,ref,found)==before,"Source state changed before furniture activation")
        require(all(assets.get_metadata_tag(found[i][0],key)==value for i,values in metadata.items() for key,value in values.items()),"Source ownership metadata changed before furniture activation")
        report["stagedMaterialProofs"]={name:common.material_proof(u,u.load_object(None,path),contract["groups"][name],contract["profiles"][name]) for name,path in material_paths.items()}
        loaded={name:u.load_object(None,path) for name,path in material_paths.items()};require(all(loaded.values()),"Saved furniture material missing")
        mutated=True;report["activationStarted"]=True
        for id_ in sorted(ref.IDS):
            actor,component=found[id_]
            if not metadata[id_][ORIGINAL]:assets.set_metadata_tag(actor,ORIGINAL,json.dumps(before["components"][id_]["overrides"]))
            assets.set_metadata_tag(actor,REVISION_TAG,REVISION)
            component.set_material(0,loaded["kitchen" if id_ in ref.KITCHEN_IDS else "dining"])
            require(component.get_material(0).get_path_name()==bindings[id_],"Furniture override activation failed")
        del found,loaded
        _reload(u,levels,map_path);found=common.components(u,contract["woodIds"]);_guard(u,common,ref,found,contract)
        after=_snapshot(u,common,ref,found)
        require(after["components"]==ref.expected_components(before["components"],bindings),"Saved furniture/source geometry, collision, UV or other binding changed")
        require(after["protectedTVMetadata"]==before["protectedTVMetadata"],"Existing TV ownership metadata changed")
        require(_source_hashes(before)==before["sourceAndEffectiveAssetHashes"],"Pre-existing mesh/source/effective material asset bytes changed")
        for id_ in ref.IDS:
            actor=found[id_][0];expected_original=metadata[id_][ORIGINAL] or json.dumps(before["components"][id_]["overrides"])
            require(assets.get_metadata_tag(actor,ORIGINAL)==expected_original and assets.get_metadata_tag(actor,REVISION_TAG)==REVISION,"Saved reversal metadata differs")
        report["savedReloadMaterialProofs"]={name:common.material_proof(u,u.load_object(None,path),contract["groups"][name],contract["profiles"][name]) for name,path in material_paths.items()}
        owned_paths=set().union(*(writer.paths for writer in writers.values()))
        report.update(nativeApplied=True,assetHashes=_asset_hashes(owned_paths),canonicalAssetHashes=before["sourceAndEffectiveAssetHashes"],
                      bindings=[{"objectId":i,"sourceId":contract["records"][i]["sourceId"],"sourceSlot":ref.SLOTS[i],"material":bindings[i],
                                 "priorOverrides":before["components"][i]["overrides"],"savedReloadVerified":True} for i in sorted(ref.IDS)],
                      verification={"newAssetsSavedBeforeActivation":True,"twoMapReloads":True,"nativeGraphGetters":True,
                                    "other149WoodBindingsUnchanged":True,"existingTVBindingsAndMetadataUnchanged":True,
                                    "sourceMeshUvCollisionAndAssetBytesUnchanged":True,"sourceWebTexturesChanged":False})
        _write(report_path,report,"native-furniture-oak-saved-reload-validated");return report
    except Exception as error:
        report.update(error=str(error),nativeApplied=False,rollbackRequired=mutated,retainedGeneratedAssetPaths=sorted(set().union(*(w.paths for w in writers.values()))),sourceStateVerifiedOnFailure=False)
        errors=[]
        if before:
            try:
                if mutated:
                    report["rollbackAttempted"]=True
                    if u.EditorLevelLibrary.get_editor_world().get_path_name().split(".")[0]!=map_path:require(levels.load_level(map_path),"Furniture rollback map load failed")
                    found=common.components(u,contract["woodIds"])
                    for id_ in sorted(ref.IDS):
                        actor,component=found[id_];common.set_overrides(u,component,before["components"][id_]["overrides"])
                        for key,value in metadata[id_].items():assets.set_metadata_tag(actor,key,value)
                    del found
                    _reload(u,levels,map_path)
                require(u.EditorLevelLibrary.get_editor_world().get_path_name().split(".")[0]==map_path,"Furniture failure left another world active")
                found=common.components(u,contract["woodIds"])
                require(_snapshot(u,common,ref,found)==before,"Furniture failure did not preserve source state")
                require(all(assets.get_metadata_tag(found[i][0],k)==v for i,values in metadata.items() for k,v in values.items()),"Furniture failure metadata differs")
                report.update(rollbackVerified=mutated,sourceStateVerifiedOnFailure=True,sourceStateCheckStage="saved-reloaded-rollback" if mutated else "live-before-activation")
            except Exception as rollback_error:errors.append(str(rollback_error))
        report["rollbackErrors"]=errors;_write(report_path,report,"failed");raise


def restore_furniture_oak(scene,geometry_dir):
    """Exact nine-object reversal, with atomic preflight and saved/reloaded proof."""
    require(Path(__file__).resolve()==ROOT/OWNER,"Output-only furniture draft cannot mutate native assets")
    import unreal as u
    ref=reference();common=ref.load_tv("tv_oak");contract=ref.verify_inputs(scene,geometry_dir)
    assets=u.EditorAssetLibrary;levels=u.get_editor_subsystem(u.LevelEditorSubsystem);world=u.EditorLevelLibrary.get_editor_world();map_path=world.get_path_name().split(".")[0]
    require(map_path=="/Game/Brezi/Maps/Brezi" and assets.get_metadata_tag(world,"BreziGeneratedBy")=="scripts/unreal/import_scene.py","Expected owned canonical map")
    found=common.components(u,contract["woodIds"]);_guard(u,common,ref,found,contract);before=_snapshot(u,common,ref,found);metadata={};restored={}
    for id_ in sorted(ref.IDS):
        actor,component=found[id_];metadata[id_]={k:assets.get_metadata_tag(actor,k) for k in (ORIGINAL,REVISION_TAG)}
        require(metadata[id_][ORIGINAL] and metadata[id_][REVISION_TAG]==REVISION and assets.get_metadata_tag(component.get_material(0),"BreziGeneratedBy")==OWNER,"No owned furniture override to restore")
        values=json.loads(metadata[id_][ORIGINAL]);require(isinstance(values,list),"Invalid reversal material recipe")
        for path in values:require(path is None or isinstance(path,str) and u.load_object(None,path) is not None,"Retained source material missing")
        restored[id_]=values
    report={"schemaVersion":1,"revision":REVISION,"selectedIds":sorted(ref.IDS),"nativeApplied":True,"rollbackErrors":[]};path=Path(geometry_dir).parent/"furniture-oak-restore-report.json"
    try:
        for id_ in sorted(ref.IDS):
            actor,component=found[id_];common.set_overrides(u,component,restored[id_]);assets.set_metadata_tag(actor,ORIGINAL,"");assets.set_metadata_tag(actor,REVISION_TAG,"")
        del found,world
        _reload(u,levels,map_path);found=common.components(u,contract["woodIds"]);after=_snapshot(u,common,ref,found)
        expected={i:dict(v) for i,v in before["components"].items()}
        for id_,values in restored.items():expected[id_].update(overrides=values,effectiveMaterial=values[0] if values and values[0] else expected[id_]["meshMaterial"])
        require(after["components"]==expected and after["protectedTVMetadata"]==before["protectedTVMetadata"],"Reversal changed source or protected state")
        require(_source_hashes(before)==before["sourceAndEffectiveAssetHashes"],"Reversal changed pre-existing asset bytes")
        require(all(not assets.get_metadata_tag(found[i][0],k) for i in ref.IDS for k in (ORIGINAL,REVISION_TAG)),"Reversal metadata was not cleared")
        report.update(nativeApplied=False,savedReloadVerified=True,other149WoodBindingsUnchanged=True);_write(path,report,"source-overrides-restored");return report
    except Exception as error:
        report["error"]=str(error)
        try:
            if u.EditorLevelLibrary.get_editor_world().get_path_name().split(".")[0]!=map_path:require(levels.load_level(map_path),"Reversal rollback map load failed")
            found=common.components(u,contract["woodIds"])
            for id_ in sorted(ref.IDS):
                actor,component=found[id_];common.set_overrides(u,component,before["components"][id_]["overrides"])
                for key,value in metadata[id_].items():assets.set_metadata_tag(actor,key,value)
            del found
            _reload(u,levels,map_path);found=common.components(u,contract["woodIds"])
            require(_snapshot(u,common,ref,found)==before,"Reversal rollback did not restore active candidate")
            require(all(assets.get_metadata_tag(found[i][0],k)==v for i,values in metadata.items() for k,v in values.items()),"Reversal rollback metadata differs")
            report["rollbackVerified"]=True
        except Exception as rollback_error:report["rollbackErrors"].append(str(rollback_error))
        _write(path,report,"restore-failed");raise
