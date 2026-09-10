"""Portable oak cleanup policy/lifecycle regressions.

Loads the real sibling production helper. All actor/asset doubles and fixtures
are local: no Unreal import, captured map, ignored study output, or repair mode.
These tests do not certify native API behavior, map idempotence, or rendering.
"""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


cleanup=load("oak_reimport", HERE/"oak_reimport.py")


def row(id_="DOM_00613",active=True):
    tv=id_ in cleanup.TV_IDS;keys=cleanup.TV_KEYS if tv else cleanup.FURNITURE_KEYS
    owner="scripts/unreal/tv-oak/tv_oak.py" if tv else "scripts/unreal/furniture-oak/furniture_oak.py"
    prefix="TVPhotoOak" if tv else "FurniturePhotoOak"
    name="M_TVCabinetPhotoOak" if tv else ("M_KitchenPhotoOak" if id_ in {"DOM_00613","DOM_00643","DOM_00647","DOM_00650"} else "M_DiningPhotoOak")
    material=f"/Game/Brezi/MaterialStudies/{prefix}/V_0123456789abcdef/Materials/{name}.{name}"
    source="/Game/Brezi/MaterialsGenerated/M_MAT_0039.M_MAT_0039"
    metadata={"ManualNote":"preserve exactly","BreziStoveOriginalFlags":"unrelated"}
    if active:metadata.update({keys[0]:"[]",keys[1]:"NATIVE-TV-CABINET-PHOTO-OAK-20260908-1" if tv else "NATIVE-NINE-BOX-PHOTO-OAK-20260908-1"})
    return {"id":id_,"actor":"/Game/Map.Map:PersistentLevel."+id_,"metadata":metadata,"materialOwner":owner if active else "", "effectiveMaterial":material if active else source,"meshMaterial":source,"overrides":[material] if active else []}


class Actor:
    def __init__(self,path):self.path=path
    def get_path_name(self):return self.path


class Assets:
    """Deliberately path-keyed to reproduce UE5.8 metadata inheritance."""
    def __init__(self,r):self.values={r["actor"]:copy.deepcopy(r["metadata"])};self.fail_key=None;self.writes=[]
    def get_metadata_tag_values(self,a):return dict(self.values[a.path])
    def remove_metadata_tag(self,a,k):
        self.writes.append(("remove",k))
        if self.fail_key==k:self.fail_key=None;raise RuntimeError("injected removal failure")
        self.values[a.path].pop(k,None)
    def set_metadata_tag(self,a,k,v):self.writes.append(("set",k));self.values[a.path][k]=v


class Actors:
    def __init__(self,success=True):self.success=success;self.calls=[]
    def destroy_actor(self,a):self.calls.append(a.path);return self.success


class Tests(unittest.TestCase):
    def test_exact_twelve_active_recipes_are_accepted(self):
        expected_tv={"DOM_01293","DOM_01296","DOM_01300"}
        expected_furniture={"DOM_00613","DOM_00643","DOM_00647","DOM_00650","DOM_01328","DOM_01345","DOM_01354","DOM_01363","DOM_01372"}
        self.assertEqual(cleanup.TV_IDS, expected_tv)
        self.assertEqual(cleanup.FURNITURE_IDS, expected_furniture)
        for id_ in expected_tv|expected_furniture:
            with self.subTest(id=id_):
                self.assertTrue(cleanup.plan_row(row(id_))["active"])

    def test_fresh_source_without_metadata_is_accepted(self):
        self.assertFalse(cleanup.plan_row(row(active=False))["active"])

    def test_foreign_override_without_metadata_is_rejected_even_with_empty_owner(self):
        r=row(active=False);r.update(overrides=["/Game/Manual.M"],effectiveMaterial="/Game/Manual.M")
        with self.assertRaisesRegex(RuntimeError,"foreign untracked"):cleanup.plan_row(r)

    def test_redundant_source_override_is_not_silently_normalized(self):
        r=row(active=False);r["overrides"]=[r["meshMaterial"]]
        with self.assertRaises(RuntimeError):cleanup.plan_row(r)

    def test_foreign_owner_or_namespace_is_rejected(self):
        for key,value in (("materialOwner","manual"),("effectiveMaterial","/Game/Other.M")):
            r=row();r[key]=value
            with self.assertRaises(RuntimeError):cleanup.plan_row(r)

    def test_stale_canonical_binding_with_owned_metadata_is_rejected(self):
        r=row();r.update(materialOwner="scripts/unreal/materials.py",effectiveMaterial=r["meshMaterial"],overrides=[])
        with self.assertRaisesRegex(RuntimeError,"foreign replacement"):cleanup.plan_row(r)

    def test_partial_revision_and_cross_scope_metadata_fail(self):
        for change in ({cleanup.FURNITURE_KEYS[1]:""},{cleanup.FURNITURE_KEYS[1]:"future"},{cleanup.TV_KEYS[0]:"[]"}):
            r=row();r["metadata"].update(change)
            with self.assertRaises(RuntimeError):cleanup.plan_row(r)

    def test_wrong_material_array_or_invalid_prior_recipe_fail(self):
        for values in ([],["/Game/Other.M"]):
            r=row();r["overrides"]=values
            with self.assertRaises(RuntimeError):cleanup.plan_row(r)
        for prior in ("{}","[2]","[false]","[\"\"]"):
            r=row();r["metadata"][cleanup.FURNITURE_KEYS[0]]=prior
            with self.assertRaises(RuntimeError):cleanup.plan_row(r)

    def test_path_keyed_metadata_reappears_without_cleanup(self):
        r=row();a=Actor(r["actor"]);assets=Assets(r);Actors().destroy_actor(a)
        replacement=Actor(r["actor"])
        self.assertEqual(assets.get_metadata_tag_values(replacement),r["metadata"])

    def test_cleanup_prevents_same_path_inheritance_and_preserves_other_keys(self):
        for id_ in ("DOM_00613", "DOM_01328", "DOM_01293"):
            with self.subTest(id=id_):
                r=row(id_);a=Actor(r["actor"]);assets=Assets(r);actors=Actors()
                plan=cleanup.plan_row(r)
                cleanup.destroy_with_cleanup(assets,actors,a,plan)
                self.assertEqual(actors.calls,[a.path])
                self.assertEqual(assets.get_metadata_tag_values(Actor(a.path)),
                                 {k:v for k,v in r["metadata"].items() if k not in plan["keys"]})

    def test_failed_destroy_restores_exact_metadata(self):
        r=row();assets=Assets(r);actors=Actors(False)
        with self.assertRaises(RuntimeError):cleanup.destroy_with_cleanup(assets,actors,Actor(r["actor"]),cleanup.plan_row(r))
        self.assertEqual(assets.values[r["actor"]],r["metadata"])

    def test_partial_cleanup_failure_restores_before_any_destroy(self):
        r=row();assets=Assets(r);assets.fail_key=cleanup.FURNITURE_KEYS[1];actors=Actors()
        with self.assertRaisesRegex(RuntimeError,"injected"):cleanup.destroy_with_cleanup(assets,actors,Actor(r["actor"]),cleanup.plan_row(r))
        self.assertEqual(assets.values[r["actor"]],r["metadata"]);self.assertEqual(actors.calls,[])

    def test_absent_and_explicit_empty_metadata_are_restored_distinctly(self):
        for meta in ({},{cleanup.FURNITURE_KEYS[0]:"",cleanup.FURNITURE_KEYS[1]:""}):
            r=row(active=False);r["metadata"].update(meta);assets=Assets(r)
            with self.assertRaises(RuntimeError):cleanup.destroy_with_cleanup(assets,Actors(False),Actor(r["actor"]),cleanup.plan_row(r))
            self.assertEqual(assets.values[r["actor"]],r["metadata"])

    def test_post_preflight_foreign_metadata_drift_stops_without_writes(self):
        r=row();plan=cleanup.plan_row(r);assets=Assets(r);assets.values[r["actor"]]["ManualNote"]="later edit";actors=Actors()
        with self.assertRaisesRegex(RuntimeError,"drift"):cleanup.destroy_with_cleanup(assets,actors,Actor(r["actor"]),plan)
        self.assertEqual(assets.writes,[]);self.assertEqual(actors.calls,[])

    def test_other_generated_actor_destruction_never_touches_metadata(self):
        r=row();assets=Assets(r);actors=Actors();cleanup.destroy_with_cleanup(assets,actors,Actor(r["actor"]))
        self.assertEqual(assets.writes,[])


    def test_unknown_source_id_is_rejected(self):
        r=row();r["id"]="DOM_99999"
        with self.assertRaisesRegex(RuntimeError,"Unexpected oak cleanup source ID"):
            cleanup.plan_row(r)

    def test_destroy_exception_restores_exact_metadata(self):
        class RaisingActors(Actors):
            def destroy_actor(self,a):
                self.calls.append(a.path)
                raise RuntimeError("injected destroy exception")
        for id_ in ("DOM_00613", "DOM_01293"):
            with self.subTest(id=id_):
                r=row(id_);assets=Assets(r);actors=RaisingActors()
                with self.assertRaisesRegex(RuntimeError,"injected destroy exception"):
                    cleanup.destroy_with_cleanup(assets,actors,Actor(r["actor"]),cleanup.plan_row(r))
                self.assertEqual(assets.values[r["actor"]],r["metadata"])
                self.assertEqual(actors.calls,[r["actor"]])

    def test_actor_identity_drift_stops_before_any_metadata_read_or_write(self):
        r=row();assets=Assets(r);actors=Actors()
        with self.assertRaisesRegex(RuntimeError,"drift"):
            cleanup.destroy_with_cleanup(assets,actors,Actor("/Game/Other.Actor"),cleanup.plan_row(r))
        self.assertEqual(assets.writes,[])
        self.assertEqual(actors.calls,[])


OAK_KEYS = {
    "BreziTVOakOriginalOverrides", "BreziTVOakRevision",
    "BreziFurnitureOakOriginalOverrides", "BreziFurnitureOakRevision",
}


def fresh_row(id_="DOM_00613", path=None):
    source = "/Game/Fixture/Source.Source"
    return {
        "actor": path or "/Game/Map.Map:PersistentLevel.new_" + id_,
        "sourceIds": [id_],
        "metadata": {**{key: "historical orphan value" for key in OAK_KEYS},
                     "ManualNote": "unchanged", "BreziStoveOriginalFlags": "unrelated"},
        "bindings": [{"id": id_, "meshMaterial": [source],
                      "effectiveMaterial": [source], "overrides": [], "materialOwner": ""}],
    }


class FreshAssets:
    """Path-keyed metadata including orphan entries without live actors."""
    def __init__(self, rows):
        self.values = {r["actor"]: copy.deepcopy(r["metadata"]) for r in rows}
        self.asset_metadata = {}
        self.writes = []
        self.fail_once = None

    def get_metadata_tag_values(self, actor):
        return dict(self.values[actor.get_path_name()])

    def get_metadata_tag(self, asset, key):
        return self.asset_metadata.get(asset.get_path_name(), {}).get(key, "")

    def remove_metadata_tag(self, actor, key):
        path = actor.get_path_name()
        self.writes.append(("remove", path, key))
        if self.fail_once == (path, key):
            self.fail_once = None
            raise RuntimeError("injected fresh cleanup failure")
        self.values[path].pop(key, None)

    def set_metadata_tag(self, actor, key, value):
        path = actor.get_path_name()
        self.writes.append(("set", path, key))
        self.values[path][key] = value


class FixtureMesh(Actor):
    def __init__(self, id_):
        super().__init__(f"/Game/Brezi/Geometry/brezi-twin/StaticMeshes/{id_}.{id_}")
        self.id = id_
        self.materials = [Actor("/Game/Fixture/Source.Source"),
                          Actor("/Game/Fixture/Second.Second")]

    def get_name(self):
        return self.id

    def get_material(self, slot):
        return self.materials[slot]

    def get_editor_property(self, name):
        if name != "static_materials":
            raise AssertionError(name)
        return self.materials


class FixtureComponent:
    def __init__(self, mesh):
        self.mesh = mesh
        self.materials = list(mesh.materials)
        self.overrides = []
        # Synthetic CPU fixture: measured source mm -> Unreal cm with negated Y.
        self.origin = SimpleNamespace(x=15, y=-30, z=45)
        self.extent = SimpleNamespace(x=5, y=10, z=15)

    def get_editor_property(self, name):
        return {"static_mesh": self.mesh, "override_materials": self.overrides}[name]

    def get_num_materials(self):
        return len(self.materials)

    def get_material(self, slot):
        return self.materials[slot]


class FixtureActor(Actor):
    def __init__(self, path, components=(), ids=()):
        super().__init__(path)
        self.components = list(components)
        self.tags = ["BreziGenerated", *ids]

    def actor_has_tag(self, tag):
        return tag in self.tags

    def get_editor_property(self, name):
        if name != "tags":
            raise AssertionError(name)
        return self.tags

    def get_components_by_class(self, unused_class):
        return list(self.components)


def native_boundary_fixture(ids=("DOM_00613", "DOM_00001")):
    """Small UE-call doubles, not a substitute for a real native import."""
    rows = [fresh_row(id_) for id_ in ids]
    assets = FreshAssets(rows)
    meshes, records, created = {}, {}, []
    for row_ in rows:
        id_ = row_["sourceIds"][0]
        mesh = FixtureMesh(id_)
        meshes[id_] = mesh
        records[id_] = {"sourceId": "fixture-source-" + id_,
                        "boundsMm": {"min": [100, 200, 300], "max": [200, 400, 600]}}
        assets.asset_metadata[mesh.path] = {
            "source_object_id": id_, "source_id": records[id_]["sourceId"]}
        created.append(FixtureActor(row_["actor"], [FixtureComponent(mesh)], [id_]))
    hierarchy = FixtureActor("/Game/Map.Map:PersistentLevel.hierarchy")
    assets.values[hierarchy.path] = {"HierarchyNote": "unchanged",
                                      "BreziStoveOriginalFlags": "unrelated"}
    created.append(hierarchy)
    manual_path = "/Game/Map.Map:PersistentLevel.manual"
    assets.values[manual_path] = {"ManualNote": "not returned by Interchange",
                                  "BreziFurnitureOakRevision": "preserve"}
    orphan_path = "/Game/Map.Map:PersistentLevel.unrelated_orphan"
    assets.values[orphan_path] = {"BreziTVOakRevision": "not a live imported actor"}
    u = SimpleNamespace(EditorAssetLibrary=assets, StaticMeshComponent=FixtureComponent,
                        SystemLibrary=SimpleNamespace(
                            get_component_bounds=lambda c: (c.origin, c.extent, 0)))
    return SimpleNamespace(u=u, assets=assets, meshes=meshes, records=records,
                           created=created, hierarchy=hierarchy,
                           pre_paths={manual_path}, manual_path=manual_path,
                           orphan_path=orphan_path)


class FreshActorTests(unittest.TestCase):
    def initialize(self, fixture):
        return cleanup.initialize_created_actors(
            fixture.u, fixture.created, fixture.pre_paths, fixture.meshes, fixture.records)

    def test_old_live_path_cleanup_cannot_clear_different_orphan_path(self):
        old = row()
        old["actor"] = "/Game/Map.Map:PersistentLevel.node613"
        new = fresh_row(path="/Game/Map.Map:PersistentLevel.node2945")
        assets = FreshAssets([old, new])
        orphan_before = copy.deepcopy(assets.values[new["actor"]])
        cleanup.destroy_with_cleanup(assets, Actors(), Actor(old["actor"]), cleanup.plan_row(old))
        self.assertEqual(assets.values[new["actor"]], orphan_before)
        plans = cleanup.plans_for_created_rows([new], {old["actor"]}, {"DOM_00613"})
        count = cleanup.clear_created_metadata(assets, {new["actor"]: Actor(new["actor"])}, plans)
        self.assertEqual(count, 4)
        self.assertEqual(assets.values[new["actor"]],
                         {k: v for k, v in orphan_before.items() if k not in OAK_KEYS})

    def test_all_twelve_oak_sources_and_non_oak_cross_scope_orphans_are_supported(self):
        ids = cleanup.TV_IDS | cleanup.FURNITURE_IDS | {"DOM_00001"}
        rows = [fresh_row(id_) for id_ in sorted(ids)]
        plans = cleanup.plans_for_created_rows(rows, set(), ids)
        self.assertEqual(len(plans), 13)
        self.assertTrue(all(set(plan["keys"]) == OAK_KEYS for plan in plans))

    def test_fresh_scope_rejects_missing_duplicate_foreign_sources_and_duplicate_paths(self):
        rows = [fresh_row("DOM_00613"), fresh_row("DOM_00001")]
        bad_cases = [rows[:1], rows + [copy.deepcopy(rows[0])]]
        foreign = copy.deepcopy(rows)
        foreign[1]["sourceIds"] = ["DOM_99999"]
        foreign[1]["bindings"][0]["id"] = "DOM_99999"
        bad_cases.append(foreign)
        paths = copy.deepcopy(rows)
        paths[1]["actor"] = paths[0]["actor"]
        bad_cases.append(paths)
        for bad in bad_cases:
            with self.subTest(rows=bad), self.assertRaises(RuntimeError):
                cleanup.plans_for_created_rows(bad, set(), {"DOM_00613", "DOM_00001"})

    def test_fresh_row_rejects_existing_actor_and_active_or_foreign_materials(self):
        r = fresh_row()
        with self.assertRaisesRegex(RuntimeError, "pre-import actor"):
            cleanup.plan_created_row(r, {r["actor"]})
        cases = [
            {"overrides": ["/Game/Manual.M"]},
            {"effectiveMaterial": ["/Game/Manual.M"]},
            {"materialOwner": "scripts/unreal/tv-oak/tv_oak.py"},
            {"materialOwner": "scripts/unreal/furniture-oak/furniture_oak.py"},
        ]
        for change in cases:
            bad = copy.deepcopy(r)
            bad["bindings"][0].update(change)
            with self.subTest(change=change), self.assertRaises(RuntimeError):
                cleanup.plan_created_row(bad, set())

    def test_incomplete_per_actor_binding_coverage_is_rejected(self):
        r = fresh_row()
        for field, value in (("sourceIds", []), ("bindings", []),
                             ("sourceIds", ["DOM_00613", "DOM_00613"])):
            bad = copy.deepcopy(r)
            bad[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(RuntimeError):
                cleanup.plan_created_row(bad, set())

    def test_all_fresh_metadata_is_checked_before_first_write(self):
        rows = [fresh_row("DOM_00613"), fresh_row("DOM_00001")]
        plans = cleanup.plans_for_created_rows(rows, set(), {"DOM_00613", "DOM_00001"})
        assets = FreshAssets(rows)
        assets.values[rows[-1]["actor"]]["ManualNote"] = "concurrent edit"
        actors = {r["actor"]: Actor(r["actor"]) for r in rows}
        with self.assertRaisesRegex(RuntimeError, "drift"):
            cleanup.clear_created_metadata(assets, actors, plans)
        self.assertEqual(assets.writes, [])

    def test_failure_on_later_actor_restores_all_touched_keys_with_presence(self):
        rows = [fresh_row("DOM_00613"), fresh_row("DOM_00001")]
        rows[0]["metadata"].pop("BreziTVOakRevision")
        rows[0]["metadata"]["BreziTVOakOriginalOverrides"] = ""
        plans = cleanup.plans_for_created_rows(rows, set(), {"DOM_00613", "DOM_00001"})
        assets = FreshAssets(rows)
        before = copy.deepcopy(assets.values)
        assets.fail_once = (rows[1]["actor"], sorted(OAK_KEYS)[1])
        actors = {r["actor"]: Actor(r["actor"]) for r in rows}
        with self.assertRaisesRegex(RuntimeError, "injected fresh cleanup failure"):
            cleanup.clear_created_metadata(assets, actors, plans)
        self.assertEqual(assets.values, before)
        self.assertTrue(any(op == "set" and path == rows[0]["actor"]
                            for op, path, key in assets.writes))

    def test_unvalidated_or_missing_fresh_actor_is_rejected_without_writes(self):
        r = fresh_row()
        plan = cleanup.plan_created_row(r, set())
        for actors, fresh in (({}, True), ({r["actor"]: Actor(r["actor"])}, False)):
            assets = FreshAssets([r])
            bad = dict(plan, fresh=fresh)
            with self.subTest(fresh=fresh), self.assertRaises(RuntimeError):
                cleanup.clear_created_metadata(assets, actors, [bad])
            self.assertEqual(assets.writes, [])

    def test_malformed_key_scope_or_actor_identity_fails_before_writes(self):
        r = fresh_row()
        plan = cleanup.plan_created_row(r, set())
        for case in ("extra-key", "missing-key", "actor-path"):
            assets = FreshAssets([r])
            bad = copy.deepcopy(plan)
            actor = Actor(r["actor"])
            if case == "extra-key":
                bad["keys"] = (*bad["keys"], "ManualNote")
            elif case == "missing-key":
                bad["keys"] = bad["keys"][:-1]
            else:
                actor = Actor("/Game/Other.Actor")
            with self.subTest(case=case), self.assertRaises(RuntimeError):
                cleanup.clear_created_metadata(assets, {r["actor"]: actor}, [bad])
            self.assertEqual(assets.writes, [])

    def test_new_actor_without_oak_metadata_requires_no_writes(self):
        r = fresh_row("DOM_00001")
        r["metadata"] = {"ManualNote": "unchanged"}
        assets = FreshAssets([r])
        plan = cleanup.plan_created_row(r, set())
        count = cleanup.clear_created_metadata(assets, {r["actor"]: Actor(r["actor"])}, [plan])
        self.assertEqual(count, 0)
        self.assertEqual(assets.writes, [])
        self.assertEqual(assets.values[r["actor"]], r["metadata"])

    def test_source_bound_initializer_preserves_hierarchy_manual_and_other_orphans(self):
        f = native_boundary_fixture(tuple(sorted(cleanup.TV_IDS | cleanup.FURNITURE_IDS | {"DOM_00001"})))
        before = copy.deepcopy(f.assets.values)
        receipt = self.initialize(f)
        self.assertEqual(receipt["sourceIds"], sorted(f.records))
        self.assertEqual(receipt["removedKeyCount"], 52)
        self.assertEqual(receipt["hierarchyActorPaths"], [f.hierarchy.path])
        self.assertFalse(receipt["packageOrphanMetadataCleared"])
        for path in (f.hierarchy.path, f.manual_path, f.orphan_path):
            self.assertEqual(f.assets.values[path], before[path])
            self.assertFalse(any(written_path == path for _, written_path, _ in f.assets.writes))
        self.assertTrue(all(key in OAK_KEYS for _, _, key in f.assets.writes))

    def test_source_boundary_rejects_duplicate_preexisting_and_untagged_created_actors(self):
        for case in ("duplicate", "preexisting", "untagged"):
            f = native_boundary_fixture()
            if case == "duplicate":
                f.created.append(f.created[0])
            elif case == "preexisting":
                f.pre_paths.add(f.created[0].path)
            else:
                f.created[0].tags.remove("BreziGenerated")
            with self.subTest(case=case), self.assertRaises(RuntimeError):
                self.initialize(f)
            self.assertEqual(f.assets.writes, [])

    def test_source_boundary_rejects_wrong_mesh_identity_path_provenance_and_bounds(self):
        for case in ("identity", "path", "object-id", "source-id", "bounds", "tag"):
            f = native_boundary_fixture()
            actor = f.created[0]
            component = actor.components[0]
            mesh = component.mesh
            if case == "identity":
                f.meshes[mesh.id] = FixtureMesh(mesh.id)
            elif case == "path":
                mesh.path = "/Game/Foreign.Mesh"
            elif case == "object-id":
                f.assets.asset_metadata[mesh.path]["source_object_id"] = "DOM_99999"
            elif case == "source-id":
                f.assets.asset_metadata[mesh.path]["source_id"] = "different source"
            elif case == "bounds":
                component.origin.x += 1
            else:
                actor.tags.remove(mesh.id)
            with self.subTest(case=case), self.assertRaises(RuntimeError):
                self.initialize(f)
            self.assertEqual(f.assets.writes, [])

    def test_source_boundary_checks_every_material_slot_and_empty_override_array(self):
        for case in ("second-slot", "extra-override", "oak-owner", "count", "missing"):
            f = native_boundary_fixture()
            c = f.created[0].components[0]
            if case == "second-slot":
                c.materials[1] = Actor("/Game/Foreign.Material")
            elif case == "extra-override":
                c.overrides = [None]
            elif case == "oak-owner":
                f.assets.asset_metadata[c.materials[1].path] = {
                    "BreziGeneratedBy": "scripts/unreal/tv-oak/tv_oak.py"}
            elif case == "count":
                c.materials.pop()
            else:
                c.materials[1] = None
            with self.subTest(case=case), self.assertRaises(RuntimeError):
                self.initialize(f)
            self.assertEqual(f.assets.writes, [])

    def test_source_boundary_rejects_missing_measured_coverage_and_tagged_hierarchy(self):
        for case in ("asset", "actor", "hierarchy-source-tag", "hierarchy-orphan-key"):
            f = native_boundary_fixture()
            if case == "asset":
                f.meshes.pop("DOM_00001")
            elif case == "actor":
                f.created.pop(1)
            elif case == "hierarchy-source-tag":
                f.hierarchy.tags.append("DOM_00613")
            else:
                f.assets.values[f.hierarchy.path]["BreziTVOakRevision"] = "orphan value"
            with self.subTest(case=case), self.assertRaises(RuntimeError):
                self.initialize(f)
            self.assertEqual(f.assets.writes, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
