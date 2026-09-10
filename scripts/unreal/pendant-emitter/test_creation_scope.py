"""Portable CPU policy tests for the shared fresh-actor metadata boundary.

Uses the real ../oak_reimport.py and local UE-call doubles only. This is not
native reflection, source-geometry, saved-map or rendered-lighting evidence.
"""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

HELPER = Path(__file__).resolve().parents[1] / "oak_reimport.py"
SPEC = importlib.util.spec_from_file_location("creation_scope_oak_reimport", HELPER)
cleanup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cleanup)

OAK = frozenset({"BreziTVOakOriginalOverrides", "BreziTVOakRevision",
                 "BreziFurnitureOakOriginalOverrides", "BreziFurnitureOakRevision"})
PENDANT = frozenset({"BreziPendantOriginalState", "BreziPendantRevision"})
COMBINED = OAK | PENDANT
PENDANT_OWNER = "scripts/unreal/pendant-emitter/pendant_emitter.py"


class Named:
    def __init__(self, path):
        self.path = path

    def get_path_name(self):
        return self.path


def row(id_="DOM_01375"):
    return {"actor": "/Game/Fixture.Map:PersistentLevel.new_" + id_,
            "sourceIds": [id_],
            "metadata": {**{k: "historical" for k in COMBINED}, "ManualNote": "retain"},
            "bindings": [{"id": id_, "meshMaterial": ["/Game/Fixture/Base.Base"],
                          "effectiveMaterial": ["/Game/Fixture/Base.Base"],
                          "overrides": [], "materialOwner": ""}]}


class Assets:
    def __init__(self, rows):
        self.values = {r["actor"]: copy.deepcopy(r["metadata"]) for r in rows}
        self.tags = {}
        self.writes = []
        self.fail_once = None

    def get_metadata_tag_values(self, actor):
        return dict(self.values[actor.path])

    def get_metadata_tag(self, obj, key):
        return self.tags.get(obj.path, {}).get(key, "")

    def remove_metadata_tag(self, actor, key):
        self.writes.append(("remove", actor.path, key))
        if self.fail_once == (actor.path, key):
            self.fail_once = None
            raise RuntimeError("injected pendant key failure")
        self.values[actor.path].pop(key, None)

    def set_metadata_tag(self, actor, key, value):
        self.writes.append(("set", actor.path, key))
        self.values[actor.path][key] = value


def boundary_fixture(owner="", hierarchy_metadata=None):
    """One synthetic measured source and one meshless hierarchy actor."""
    r = row()
    assets = Assets([r])
    material = Named("/Game/Fixture/Base.Base")
    mesh = Named("/Game/Brezi/Geometry/brezi-twin/StaticMeshes/DOM_01375.DOM_01375")
    mesh.get_name = lambda: "DOM_01375"
    mesh.get_material = lambda slot: material
    mesh.get_editor_property = lambda name: [material] if name == "static_materials" else None
    component = SimpleNamespace(
        get_editor_property=lambda name: {"static_mesh": mesh, "override_materials": []}[name],
        get_num_materials=lambda: 1, get_material=lambda slot: material)
    actor = Named(r["actor"])
    actor.actor_has_tag = lambda tag: tag == "BreziGenerated"
    actor.get_editor_property = lambda name: ["BreziGenerated", "DOM_01375"]
    actor.get_components_by_class = lambda cls: [component]
    hierarchy = Named("/Game/Fixture.Map:PersistentLevel.hierarchy")
    hierarchy.actor_has_tag = lambda tag: tag == "BreziGenerated"
    hierarchy.get_editor_property = lambda name: ["BreziGenerated"]
    hierarchy.get_components_by_class = lambda cls: []
    assets.values[hierarchy.path] = hierarchy_metadata or {"ManualNote": "hierarchy untouched"}
    assets.tags[mesh.path] = {"source_object_id": "DOM_01375", "source_id": "synthetic-source"}
    assets.tags[material.path] = {"BreziGeneratedBy": owner}
    u = SimpleNamespace(EditorAssetLibrary=assets, StaticMeshComponent=object,
                        SystemLibrary=SimpleNamespace(get_component_bounds=lambda c: (
                            SimpleNamespace(x=5, y=-5, z=5), SimpleNamespace(x=5, y=5, z=5), 0)))
    records = {"DOM_01375": {"sourceId": "synthetic-source",
                              "boundsMm": {"min": [0, 0, 0], "max": [100, 100, 100]}}}
    return SimpleNamespace(u=u, assets=assets, actor=actor, hierarchy=hierarchy,
                           created=[actor, hierarchy], meshes={"DOM_01375": mesh}, records=records)


class CreationScopeTests(unittest.TestCase):
    def test_legacy_scope_and_only_two_closed_sets_are_preserved(self):
        self.assertEqual(cleanup.ALL_KEYS, OAK)
        for container in (tuple, list, set, frozenset):
            for keys in (OAK, COMBINED):
                with self.subTest(container=container.__name__, keys=keys):
                    self.assertEqual(cleanup.validate_creation_key_scope(container(keys)), tuple(sorted(keys)))

    def test_malformed_partial_duplicate_and_arbitrary_scopes_are_rejected(self):
        invalid = [None, True, "BreziPendantRevision", {}, [], list(OAK)[:-1],
                   list(OAK) + [next(iter(OAK))], OAK | {"ManualNote"},
                   OAK | {"BreziPendantRevision"}, list(OAK) + [5], iter(OAK)]
        for scope in invalid:
            with self.subTest(scope=repr(scope)), self.assertRaises(RuntimeError):
                cleanup.validate_creation_key_scope(scope)

    def test_caller_mode_mismatch_fails_before_any_write(self):
        r = row()
        actors = {r["actor"]: Named(r["actor"])}
        for planned, selected in ((COMBINED, OAK), (OAK, COMBINED)):
            assets = Assets([r])
            plan = cleanup.plan_created_row(r, set(), planned)
            with self.subTest(planned=planned), self.assertRaises(RuntimeError):
                if selected == OAK:
                    cleanup.clear_created_metadata(assets, actors, [plan])
                else:
                    cleanup.clear_created_metadata(assets, actors, [plan], selected)
            self.assertEqual(assets.writes, [])

    def test_default_cleanup_retains_both_pendant_values_including_empty(self):
        r = row()
        r["metadata"]["BreziPendantOriginalState"] = ""
        assets = Assets([r])
        plan = cleanup.plan_created_row(r, set())
        count = cleanup.clear_created_metadata(assets, {r["actor"]: Named(r["actor"])}, [plan])
        self.assertEqual(count, 4)
        self.assertEqual(assets.values[r["actor"]], {k: v for k, v in r["metadata"].items() if k not in OAK})

    def test_explicit_combined_cleanup_changes_only_the_six_owned_keys(self):
        r = row("DOM_00001")  # Cross-scope orphan on a new non-pendant source.
        assets = Assets([r])
        plan = cleanup.plan_created_row(r, set(), COMBINED)
        count = cleanup.clear_created_metadata(assets, {r["actor"]: Named(r["actor"])}, [plan], COMBINED)
        self.assertEqual(count, 6)
        self.assertEqual(assets.values[r["actor"]], {"ManualNote": "retain"})
        self.assertEqual({key for _, _, key in assets.writes}, COMBINED)

    def test_later_actor_failure_restores_all_touched_keys_and_presence(self):
        rows = [row(), row("DOM_00001")]
        rows[0]["metadata"].pop("BreziTVOakRevision")
        rows[0]["metadata"]["BreziPendantOriginalState"] = ""
        assets = Assets(rows)
        before = copy.deepcopy(assets.values)
        plans = cleanup.plans_for_created_rows(rows, set(), {"DOM_01375", "DOM_00001"}, COMBINED)
        assets.fail_once = (rows[1]["actor"], "BreziPendantRevision")
        with self.assertRaisesRegex(RuntimeError, "injected pendant key failure"):
            cleanup.clear_created_metadata(assets, {r["actor"]: Named(r["actor"]) for r in rows}, plans, COMBINED)
        self.assertEqual(assets.values, before)
        self.assertTrue(any(op == "set" and path == rows[0]["actor"] for op, path, key in assets.writes))

    def test_freshness_and_late_metadata_drift_still_fail_before_writes(self):
        rows = [row(), row("DOM_00001")]
        with self.assertRaises(RuntimeError):
            cleanup.plans_for_created_rows(rows, {rows[1]["actor"]}, {"DOM_01375", "DOM_00001"}, COMBINED)
        plans = cleanup.plans_for_created_rows(rows, set(), {"DOM_01375", "DOM_00001"}, COMBINED)
        assets = Assets(rows)
        assets.values[rows[1]["actor"]]["ManualNote"] = "later edit"
        with self.assertRaises(RuntimeError):
            cleanup.clear_created_metadata(assets, {r["actor"]: Named(r["actor"]) for r in rows}, plans, COMBINED)
        self.assertEqual(assets.writes, [])

    def test_combined_boundary_propagates_scope_and_preserves_clean_hierarchy(self):
        f = boundary_fixture()
        before = copy.deepcopy(f.assets.values[f.hierarchy.path])
        result = cleanup.initialize_created_actors(f.u, f.created, set(), f.meshes, f.records, COMBINED)
        self.assertEqual(result["initializedOwnedKeys"], sorted(COMBINED))
        self.assertEqual(result["removedKeyCount"], 6)
        self.assertEqual(f.assets.values[f.hierarchy.path], before)
        self.assertFalse(result["packageOrphanMetadataCleared"])

    def test_combined_boundary_rejects_pendant_hierarchy_orphan_before_writes(self):
        f = boundary_fixture(hierarchy_metadata={"BreziPendantRevision": "historical"})
        with self.assertRaises(RuntimeError):
            cleanup.initialize_created_actors(f.u, f.created, set(), f.meshes, f.records, COMBINED)
        self.assertEqual(f.assets.writes, [])

    def test_pure_pendant_owner_rejected_only_in_explicit_combined_mode(self):
        r = row()
        r["bindings"][0]["materialOwner"] = PENDANT_OWNER
        self.assertEqual(cleanup.plan_created_row(r, set())["keys"], tuple(sorted(OAK)))
        with self.assertRaises(RuntimeError):
            cleanup.plan_created_row(r, set(), COMBINED)

    def test_boundary_pendant_owner_rejected_only_in_explicit_combined_mode(self):
        f = boundary_fixture(owner=PENDANT_OWNER)
        with self.assertRaises(RuntimeError):
            cleanup.initialize_created_actors(f.u, f.created, set(), f.meshes, f.records, COMBINED)
        self.assertEqual(f.assets.writes, [])
        f = boundary_fixture(owner=PENDANT_OWNER)
        result = cleanup.initialize_created_actors(f.u, f.created, set(), f.meshes, f.records)
        self.assertEqual(result["initializedOwnedKeys"], sorted(OAK))
        self.assertEqual(result["removedKeyCount"], 4)
        self.assertTrue(PENDANT.issubset(f.assets.values[f.actor.path]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
