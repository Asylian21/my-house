"""Bounded R21 reflected-root repair guards; no Unreal or historical writes."""
import ast
import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('foreground_repair_r2',HERE/'exterior-canopy-foreground-native-r2.py')
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)


class Actor:
    def __init__(self):self.root=None;self.reads=[]
    def get_editor_property(self,name):
        if name!='root_component':raise AssertionError('Unknown reflected property')
        self.reads.append(name);return self.root
    # Intentionally no get_root_component: exactly the measured native failure.


class Component:
    def __init__(self,owner):self.owner=owner
    def get_owner(self):return self.owner


class ReflectedRootRepair(unittest.TestCase):
    def test_actual_missing_method_shape_uses_reflected_property(self):
        actor=Actor();component=Component(actor);actor.root=component
        self.assertTrue(n.owned_hism_root(actor,component));self.assertEqual(actor.reads,['root_component'])

    def test_root_and_owner_checks_are_both_required(self):
        actor=Actor();component=Component(actor);actor.root=Component(actor)
        self.assertFalse(n.owned_hism_root(actor,component))
        actor.root=component;component.owner=Actor();self.assertFalse(n.owned_hism_root(actor,component))

    def test_installed_primary_reflection_pin_and_new_version(self):
        row=n.primary_actor_api();self.assertEqual(row['sha256'],'255c6a18c75d860e38282c7ec1561a72c9f2d4b19b41043a0df5ba668659dba9');self.assertEqual(row['bytes'],255898)
        self.assertEqual(n.OWNER,'scripts/unreal/exterior-canopy-foreground-native-r2.py');self.assertEqual(n.REPORT,'foreground-overlay-report-r2.json')

    def test_geometry_material_and_population_algorithms_unchanged(self):
        old=ast.parse((HERE/'exterior-canopy-foreground-native.py').read_text());new=ast.parse((HERE/'exterior-canopy-foreground-native-r2.py').read_text())
        methods=lambda tree:{v.name:ast.dump(v,include_attributes=False)for v in tree.body if isinstance(v,ast.FunctionDef)}
        before,after=methods(old),methods(new)
        for key in ['write_glb','decode_glb','world_position_offsets','create_material','native_mesh_proof','import_floor','apply_scene']:
            self.assertEqual(before[key],after[key],key+' changed beyond the reflected-root repair')
        self.assertNotIn('get_root_component(', (HERE/'exterior-canopy-foreground-native-r2.py').read_text())


if __name__=='__main__':unittest.main()
