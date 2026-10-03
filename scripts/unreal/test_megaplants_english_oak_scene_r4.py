"""Bounded scene-only ownership/property-transfer guards, no Unreal execution."""
import ast
import copy
import importlib.util
from pathlib import Path
import types
import unittest

def load(name,file):
    path=Path(__file__).with_name(file);s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=load('oak_r4_test_guard','megaplants-english-oak-scene-guards-r4.py')
n=load('oak_r4_test_native','megaplants-english-oak-scene-native-r4.py')

class SceneGuards(unittest.TestCase):
    def test_actual_preserved_package_basis(self):
        original=g.read(g.original.PLAN);base=g.read(original['baseNativeReport']['path'])
        audit=g.read(g.OUTPUT/'root-native-crash-byte-audit-r3-r1.json')
        before=g.expected_before({'projectPreparation':audit['preparation']},base,audit)
        self.assertEqual(len(before),4257)
        self.assertEqual(sum('/OriginalUSD/' in k for k in before),39)
        bad=copy.deepcopy(audit);bad['newContentFileCount']=38
        with self.assertRaises(RuntimeError):g.expected_before({'projectPreparation':audit['preparation']},base,bad)
    def test_only_two_new_scene_files_and_camera(self):
        before={'Content/Brezi/Maps/Brezi.umap':{'sha256':'a','bytes':1},
                'Content/Data/viewpoints.json':{'sha256':'b','bytes':1},
                'Content/'+g.PREFIX.removeprefix('/Game/')+'/OriginalUSD/SK_Root.uasset':{'sha256':'c','bytes':1}}
        after=copy.deepcopy(before);after['Content/Data/viewpoints.json']['sha256']='d'
        after['Content/'+g.MAP.removeprefix('/Game/')+'.umap']={'sha256':'e','bytes':1}
        after['Content/'+g.GROUND_MATERIAL.removeprefix('/Game/')+'.uasset']={'sha256':'f','bytes':1}
        self.assertTrue(g.validate_delta(before,after)['all39SavedOriginalUsdPackagesByteExact'])
        for key in before:
            if key=='Content/Data/viewpoints.json':continue
            bad=copy.deepcopy(after);bad[key]['sha256']='x'
            with self.subTest(key=key),self.assertRaises(RuntimeError):g.validate_delta(before,bad)
        bad=copy.deepcopy(after);bad['Content/Outside.uasset']={'sha256':'x','bytes':1}
        with self.assertRaises(RuntimeError):g.validate_delta(before,bad)
        bad=copy.deepcopy(after);del bad[next(k for k in before if '/OriginalUSD/' in k)]
        with self.assertRaises(RuntimeError):g.validate_delta(before,bad)
    def test_old_actor_pointers_are_rejected(self):
        class Actor:
            def get_path_name(self):return '/Game/Source.Source:PersistentLevel.Sun'
        with self.assertRaises(RuntimeError):n.capture_property(types.SimpleNamespace(Actor=Actor),Actor())
    def test_wrapped_values_copied_and_assets_resolved_by_path(self):
        class Actor:pass
        class Struct:
            def __init__(self,value):self.value=value
            def copy(self):return Struct(self.value)
        class Asset:
            def get_path_name(self):return '/Engine/OriginalMaterial.OriginalMaterial'
        u=types.SimpleNamespace(Actor=Actor,load_asset=lambda path:('actual-asset',path))
        source=Struct(42);captured=n.capture_property(u,source);source.value=0
        self.assertEqual(captured['value'].value,42)
        self.assertEqual(n.resolve_property(u,n.capture_property(u,Asset())),('actual-asset','/Engine/OriginalMaterial.OriginalMaterial'))
        u.load_asset=lambda path:None
        with self.assertRaises(RuntimeError):n.resolve_property(u,{'kind':'asset-path','value':'/Engine/Missing'})
    def test_active_world_creation_without_import_or_duplication(self):
        path=Path(__file__).with_name('megaplants-english-oak-scene-native-r4.py')
        tree=ast.parse(path.read_text());calls=[(v.lineno,v.func.attr) for v in ast.walk(tree)
                if isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute)]
        self.assertFalse(any(attr in {'import_asset_tasks','AssetImportTask','duplicate_actors','WorldFactory'} for _,attr in calls))
        create=next(line for line,attr in calls if attr=='new_level')
        current=next(line for line,attr in calls if attr=='get_current_level')
        # Explicit light spawning is in a separate function, called only after
        # the current-level assertion; direct tree/ground spawns follow too.
        production=next(v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name=='run')
        direct=[v.lineno for v in ast.walk(production) if isinstance(v,ast.Call) and
                isinstance(v.func,ast.Attribute) and v.func.attr=='spawn_actor_from_class']
        copied=[v.lineno for v in ast.walk(production) if isinstance(v,ast.Call) and
                isinstance(v.func,ast.Name) and v.func.id=='spawn_light_values']
        self.assertLess(create,current);self.assertTrue(all(current<line for line in direct+copied))

if __name__=='__main__':unittest.main()
