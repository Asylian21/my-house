"""Actual nested import-order and preserved-scene CPU checks; no Unreal."""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('r22_r2_test_repair',ROOT/'scripts/unreal/exterior-realism-integration-repair-r22-r2.py')
repair=importlib.util.module_from_spec(s);s.loader.exec_module(repair)


def isolated(body):
    return subprocess.run([sys.executable,'-B','-c',body],cwd=ROOT,capture_output=True,text=True)


BOOT="""import importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
root=Path.cwd()
def load(file,name):
 s=importlib.util.spec_from_file_location(name,root/'scripts/unreal'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
repair=load('exterior-realism-integration-repair-r22-r2.py','probe_repair')
plan=repair.read(repair.guard.PLAN)
evidence=repair.read(repair.check_pin(plan['reusedBaseEvidencePlan']))
"""


class OrderRepair(unittest.TestCase):
    def test_actual_failed_trial_is_before_map_with391_unchanged_pins(self):
        failure=repair.failure_proof()
        self.assertEqual((failure['pid'],failure['exitCode'],failure['sourcePinCount']),(47497,255,391))
        self.assertFalse(failure['nativeReportCreated'])

    def test_original_current_first_order_reproduces_actual_failure(self):
        result=isolated(BOOT+"""n=load('exterior-realism-integration-native-r22.py','old')
try:n.helpers({'evidence':evidence})
except RuntimeError as e:
 assert str(e)=='Another performance policy is already imported';print('original-order-rejected')
else:raise AssertionError('Original current-first order unexpectedly passed')
""")
        self.assertEqual(result.returncode,0,result.stderr);self.assertIn('original-order-rejected',result.stdout)

    def test_new_frozen_first_loads_all_actual_nested_helpers_without_cache_change(self):
        result=isolated(BOOT+"""n=load('exterior-realism-integration-native-r22-r2.py','new')
h=n.helpers({'evidence':evidence});cached=sys.modules['performance_scene_policy']
assert set(h)=={'neighbor','grass','foreground','roof','neighborMaterial','moduleOrderWitness','performance','importer','existing','rural','meshHelper'}
assert Path(cached.__file__).resolve()==Path(h['moduleOrderWitness']['path']).resolve()
assert cached.LUMEN_DEFAULTS is h['performance'].LUMEN_DEFAULTS
repair.g.frozen_modules(evidence);assert sys.modules['performance_scene_policy'] is cached
print(json.dumps(h['moduleOrderWitness']))
""")
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('"cacheDeletedOrReplaced": false',result.stdout)

    def test_foreign_cached_policy_stays_rejected_without_replacement(self):
        result=isolated(BOOT+"""from types import ModuleType
foreign=ModuleType('performance_scene_policy');foreign.__file__=str(root/'scripts/unreal/performance_scene_policy.py')
sys.modules['performance_scene_policy']=foreign
try:repair.g.frozen_modules(evidence)
except RuntimeError as e:assert str(e)=='Another performance policy is already imported'
else:raise AssertionError('Foreign cached policy was accepted')
assert sys.modules['performance_scene_policy'] is foreign
""")
        self.assertEqual(result.returncode,0,result.stderr)

    def test_every_scene_material_geometry_mutator_is_ast_exact_original(self):
        def functions(file):
            tree=ast.parse((ROOT/'scripts/unreal'/file).read_text())
            return {node.name:ast.dump(node,include_attributes=False)for node in tree.body if isinstance(node,ast.FunctionDef)}
        old=functions('exterior-realism-integration-native-r22.py');new=functions('exterior-realism-integration-native-r22-r2.py')
        for key in ('full_witness','verify_materials','component_lookup','apply_leaf_and_visibility','roof_overrides','neighbor_geometry_after_roof'):
            self.assertEqual(new[key],old[key],key)
        repair.original_source_proof()

    def test_cache_witness_rejects_changed_identity_even_at_same_frozen_path(self):
        result=isolated(BOOT+"""from types import ModuleType
repair.g.frozen_modules(evidence);cached=sys.modules['performance_scene_policy']
other=ModuleType('performance_scene_policy');other.__file__=cached.__file__
try:repair.policy_witness(evidence,other)
except RuntimeError as e:assert 'replaced' in str(e)
else:raise AssertionError('Different cache identity accepted')
assert sys.modules['performance_scene_policy'] is cached
""")
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main(verbosity=2)
