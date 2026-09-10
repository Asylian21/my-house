"""Live pendant policy/metadata regressions; no native UObject/API success claim."""
import ast
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("pendant_lifecycle",HERE/"pendant_emitter.py")
pendant=importlib.util.module_from_spec(spec);spec.loader.exec_module(pendant)


def fixture(active=True):
    recipe="a"*64
    source="/Game/Brezi/Geometry/brezi-twin/Materials/MAT_0046.MAT_0046"
    emitted=pendant.PREFIX+"/V_"+recipe[:16]+"/M_Pendant800lm.M_Pendant800lm"
    meta={"ManualNote":"keep","INTERCHANGE.source_object_id":"DOM_01375","BreziStoveOriginalFlags":"unrelated"}
    if active:meta.update({pendant.PRIOR:json.dumps({"overrides":[],"emissiveLightSource":False}),pendant.REVISION_TAG:pendant.REVISION})
    return {"sourceId":"DOM_01375","actor":"/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.GeneratedActualPath",
            "metadata":meta,"materialOwner":pendant.OWNER if active else "","effectiveMaterial":emitted if active else source,
            "meshMaterial":source,"overrides":[emitted] if active else [],"emissiveLightSource":active,"recipeSha256":recipe if active else ""}


class Actor:
    def __init__(self,path):self.path=path
    def get_path_name(self):return self.path


class Assets:
    def __init__(self,row):self.data=copy.deepcopy(row["metadata"]);self.calls=[];self.fail=None
    def get_metadata_tag_values(self,actor):return dict(self.data)
    def remove_metadata_tag(self,actor,key):
        self.calls.append(("remove",key))
        if key==self.fail:self.fail=None;raise RuntimeError("injected key removal failure")
        self.data.pop(key,None)
    def set_metadata_tag(self,actor,key,value):self.calls.append(("set",key));self.data[key]=value


class Actors:
    def __init__(self,success=True):self.success=success;self.calls=[]
    def destroy_actor(self,actor):self.calls.append(actor.path);return self.success


class PendantLifecycleTests(unittest.TestCase):
    def test_active_recipe_and_unmodified_source_are_distinct_valid_states(self):
        self.assertTrue(pendant.plan_reimport(fixture())["active"])
        self.assertFalse(pendant.plan_reimport(fixture(False))["active"])

    def test_stale_live_keys_with_source_binding_are_rejected(self):
        r=fixture();source=fixture(False)
        for key in ("materialOwner","effectiveMaterial","overrides","emissiveLightSource"):r[key]=source[key]
        with self.assertRaisesRegex(RuntimeError,"Foreign replacement"):pendant.plan_reimport(r)

    def test_foreign_identity_revision_owner_or_material_path_is_rejected(self):
        for key,value in (("sourceId","DOM_01374"),("materialOwner","manual"),("effectiveMaterial","/Game/Manual.Material"),("recipeSha256","")):
            r=fixture();r[key]=value
            with self.subTest(key=key),self.assertRaises(RuntimeError):pendant.plan_reimport(r)
        for key,value in ((pendant.REVISION_TAG,"future"),(pendant.PRIOR,"")):
            r=fixture();r["metadata"][key]=value
            with self.assertRaises(RuntimeError):pendant.plan_reimport(r)

    def test_active_emitter_false_or_extra_override_is_rejected(self):
        for key,value in (("emissiveLightSource",False),("overrides",[]),("overrides",["/Game/Manual.M"])):
            r=fixture();r[key]=value
            with self.assertRaises(RuntimeError):pendant.plan_reimport(r)

    def test_untracked_override_or_emitter_flag_is_protected(self):
        for key,value in (("emissiveLightSource",True),("overrides",["/Game/Manual.M"]),("effectiveMaterial","/Game/Manual.M"),("materialOwner",pendant.OWNER)):
            r=fixture(False);r[key]=value
            with self.assertRaises(RuntimeError):pendant.plan_reimport(r)

    def test_retained_flag_and_override_schema_is_not_coerced(self):
        for prior in ({"overrides":[],"emissiveLightSource":1},{"overrides":[False],"emissiveLightSource":False},{"overrides":[]}):
            r=fixture();r["metadata"][pendant.PRIOR]=json.dumps(prior)
            with self.assertRaises(ValueError):pendant.plan_reimport(r)

    def test_cleanup_only_removes_two_owned_keys(self):
        r=fixture();assets=Assets(r);actors=Actors();a=Actor(r["actor"])
        pendant.destroy_reimport_actor(assets,actors,a,pendant.plan_reimport(r))
        self.assertEqual(assets.data,{k:v for k,v in r["metadata"].items() if k not in (pendant.PRIOR,pendant.REVISION_TAG)})
        self.assertEqual(actors.calls,[a.path])
        self.assertEqual({k for _,k in assets.calls},{pendant.PRIOR,pendant.REVISION_TAG})

    def test_destroy_failure_restores_present_absent_and_empty_keys_exactly(self):
        empty=fixture(False);empty["metadata"].update({pendant.PRIOR:"",pendant.REVISION_TAG:""})
        for r in (fixture(),fixture(False),empty):
            assets=Assets(r)
            with self.assertRaisesRegex(RuntimeError,"Could not replace"):pendant.destroy_reimport_actor(assets,Actors(False),Actor(r["actor"]),pendant.plan_reimport(r))
            self.assertEqual(assets.data,r["metadata"])

    def test_partial_removal_failure_restores_before_destroy(self):
        r=fixture();assets=Assets(r);assets.fail=pendant.REVISION_TAG;actors=Actors()
        with self.assertRaisesRegex(RuntimeError,"injected"):pendant.destroy_reimport_actor(assets,actors,Actor(r["actor"]),pendant.plan_reimport(r))
        self.assertEqual(assets.data,r["metadata"]);self.assertEqual(actors.calls,[])

    def test_foreign_key_plan_or_actor_identity_refused_before_any_mutation(self):
        for change in ({"keys":(pendant.PRIOR,"ManualNote")},{"actor":"/Game/Other.Actor"}):
            r=fixture();assets=Assets(r);actors=Actors();plan=pendant.plan_reimport(r);plan.update(change)
            with self.assertRaises(RuntimeError):pendant.destroy_reimport_actor(assets,actors,Actor(r["actor"]),plan)
            self.assertEqual(assets.calls,[]);self.assertEqual(actors.calls,[])

    def test_metadata_drift_after_preflight_is_preserved_and_rejected(self):
        r=fixture();assets=Assets(r);plan=pendant.plan_reimport(r);assets.data["ManualNote"]="new edit";actors=Actors()
        with self.assertRaisesRegex(RuntimeError,"changed after"):pendant.destroy_reimport_actor(assets,actors,Actor(r["actor"]),plan)
        self.assertEqual(assets.calls,[]);self.assertEqual(assets.data["ManualNote"],"new edit")

    def test_output_only_native_preflight_refuses_before_unreal_calls(self):
        # Keep this guard meaningful after the proposal is adopted canonically.
        with tempfile.TemporaryDirectory(dir=pendant.ROOT/"output/unreal",prefix="pendant-preflight-guard-") as directory:
            path=Path(directory)/"pendant_emitter.py";path.write_bytes((HERE/"pendant_emitter.py").read_bytes())
            spec=importlib.util.spec_from_file_location("pendant_preflight_guard",path)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            with self.assertRaisesRegex(RuntimeError,"Output-only"):module.preflight_reimport(None,None,None,None)

    def test_importer_has_both_preflights_before_deletion_and_explicit_six_key_mode(self):
        path=HERE.parent/"import_scene.py"
        if not path.is_file():self.skipTest("Importer wiring is checked only in the complete proposal tree")
        tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="prepare_world")
        calls={n.func.id:n.lineno for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertLess(calls["preflight"],calls["destroy_reimport_actor"]);self.assertLess(calls["preflight_reimport"],calls["destroy_with_cleanup"])
        init=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="initialize_created_actors"]
        self.assertEqual(len(init),1)
        self.assertTrue(any(k.arg=="key_scope" and isinstance(k.value,ast.Name) and k.value.id=="WITH_PENDANT_KEYS" for k in init[0].keywords))


if __name__=="__main__":unittest.main(verbosity=2)
