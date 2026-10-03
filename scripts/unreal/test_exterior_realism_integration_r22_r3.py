"""Focused actual37-row retained material lookup fixtures; no native/GPU."""
import ast
import copy
import importlib.util
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('r22_r3_material_test',ROOT/'scripts/unreal/exterior-realism-integration-native-r22-r3.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
b=n.guard.load_donors();neighbor=n.guard.module('r22_r3_fixture_source','exterior-neighbor-finish-native-r3.py')
rows=neighbor.export_records(neighbor.guard.validated_candidate())


class MaterialLookup(unittest.TestCase):
    def test_actual_failed_r2_process_and410_pins_preserved(self):
        f=n.repair.failure_proof();self.assertEqual((f['pid'],f['exitCode'],f['sourcePinCount']),(49239,255,410))
        self.assertTrue(f['frozenFirstModuleOrderPassed']);self.assertTrue(f['failureBeforeMapSave'])

    def test_all37_rows_resolve_exact9_new_and4_original_assets(self):
        assets=n.neighbor_material_assets(b,rows);self.assertEqual((len(rows),len(assets)),(37,13))
        for row in rows:
            family=b['reports']['neighbors']['materials']['materials']if row['material']in b['reports']['neighbors']['materials']['materials']else b['base']['materials']['materials']
            self.assertEqual(assets[row['material']],family[row['material']]['asset'])
        self.assertEqual(set(assets)-set(b['reports']['neighbors']['materials']['materials']),
            {'context_boundary_post','context_village_roof','context_village_wall','context_wire'})

    def test_each_missing_original_retained_key_is_rejected(self):
        for key in ('context_boundary_post','context_village_roof','context_village_wall','context_wire'):
            value=copy.deepcopy(b);del value['base']['materials']['materials'][key]
            with self.subTest(key=key),self.assertRaises(RuntimeError):n.neighbor_material_assets(value,rows)

    def test_foreign_row_key_and_missing_new_graph_rejected(self):
        changed=copy.deepcopy(rows);changed[0]['material']='unapproved-material'
        with self.assertRaises(RuntimeError):n.neighbor_material_assets(b,changed)
        value=copy.deepcopy(b);del value['reports']['neighbors']['materials']['materials'][rows[0]['material']]
        with self.assertRaises(RuntimeError):n.neighbor_material_assets(value,rows)

    def test_actual_post_roof_default_slot_route_resolves_all37(self):
        assets=n.neighbor_material_assets(b,rows);by_path={b['reports']['neighbors']['meshes'][r['id']]:r for r in rows}
        class Mesh:
            def __init__(self,row):self.row=row
            def get_material(self,slot):
                self_outer=self;return SimpleNamespace(get_path_name=lambda:assets[self_outer.row['material']])
            def get_editor_property(self,key):
                return False if key=='has_navigation_data'else SimpleNamespace(get_editor_property=lambda key:False)
        u=SimpleNamespace(EditorAssetLibrary=SimpleNamespace(load_asset=lambda p:Mesh(by_path[p])))
        subsystem=SimpleNamespace(get_lod_build_settings=lambda mesh,lod:SimpleNamespace(get_editor_property=lambda key:key=='use_full_precision_u_vs'))
        h={'meshHelper':SimpleNamespace(static_mesh_subsystem=lambda u:subsystem),
            'neighbor':SimpleNamespace(native_mesh_proof=lambda u,mesh,row:{'id':row['id'],'wantedAsset':assets[row['material']]})}
        proof=n.neighbor_geometry_after_roof(u,b,h,rows,b['reports']['neighbors']['meshes'])
        self.assertEqual(set(proof),{r['id']for r in rows});self.assertEqual(len(proof),37)
        # Only this lookup route is mocked. No native geometry result is claimed.
        tree=ast.parse((ROOT/n.OWNER).read_text());main=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='main')
        assignments=[x for x in ast.walk(main)if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='neighbor_materials'for t in x.targets)]
        self.assertEqual(len(assignments),1);self.assertIn('neighbor_material_assets(bundle, neighbor_rows)',ast.unparse(assignments[0]))

    def test_frozen_first_nested_order_and_all_other_mutators_unchanged(self):
        helpers=n.helpers(b);self.assertFalse(helpers['moduleOrderWitness']['cacheDeletedOrReplaced'])
        def functions(file):return {x.name:ast.dump(x,include_attributes=False)for x in ast.parse((ROOT/'scripts/unreal'/file).read_text()).body if isinstance(x,ast.FunctionDef)}
        old=functions('exterior-realism-integration-native-r22-r2.py');new=functions('exterior-realism-integration-native-r22-r3.py')
        for key in ('full_witness','verify_materials','component_lookup','apply_leaf_and_visibility','roof_overrides'):
            self.assertEqual(old[key],new[key],key)
        n.repair.original_source_proof()


if __name__=='__main__':unittest.main(verbosity=2)
