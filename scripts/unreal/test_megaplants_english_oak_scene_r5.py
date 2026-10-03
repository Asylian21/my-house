"""Focused CPU guards; no simulated Unreal/native acceptance."""
import ast
import copy
import importlib.util
from pathlib import Path
import unittest

def module(file):
    p=Path(__file__).with_name(file);s=importlib.util.spec_from_file_location(file,p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=module('megaplants-english-oak-scene-guards-r5.py')
n=module('megaplants-english-oak-scene-native-r5.py')

class GuardTests(unittest.TestCase):
    def test_actual4258_basis_and_preserved_failed_map(self):
        _,_,_,before=g.old.validate_plan()
        audit=g.read(g.OUTPUT/'root-native-scene-failure-byte-audit-r4-r1.json')
        result=g.expected_before(audit,before);self.assertEqual(len(result),4258)
        bad=copy.deepcopy(audit);bad['newContentFiles']={}
        with self.assertRaises(RuntimeError):g.expected_before(bad,before)
    def test_only_new_scene_map_material_camera(self):
        before={'Content/Data/viewpoints.json':{'sha256':'old'}}
        old_map='Content/'+g.old.MAP.removeprefix('/Game/')+'.umap';before[old_map]={'sha256':'preserved'}
        after={**before,'Content/Data/viewpoints.json':{'sha256':'new'},
            'Content/'+g.MAP.removeprefix('/Game/')+'.umap':{},
            'Content/'+g.GROUND_MATERIAL.removeprefix('/Game/')+'.uasset':{}}
        self.assertTrue(g.validate_delta(before,after)['failedR4MapByteExact'])
        after[old_map]={'sha256':'changed'}
        with self.assertRaises(RuntimeError):g.validate_delta(before,after)
    def test_exact_numeric_and_nontransform_differences(self):
        left=[{'class':'Light','transform':[[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]],'intensity':8.}]
        right=copy.deepcopy(left);right[0]['transform'][1][0]=1e-16
        d=n.lighting_difference(left,right)
        self.assertEqual(d['differenceCount'],1);self.assertEqual(d['differences'][0]['path'],'$[0].transform[1][0]')
        self.assertGreater(d['quaternionRows'][0]['rotationAngleDifferenceDegrees'],0)
        right[0]['intensity']='8.0';d=n.lighting_difference(left,right)
        self.assertEqual(d['nonFloat64DifferenceCount'],1)
        self.assertEqual(d['differences'][0]['path'],'$[0].intensity')
    def test_signed_zero_and_type_are_explicit(self):
        d=n.lighting_difference([0.],[float('-0')]);self.assertEqual(d['differenceCount'],1)
        d=n.lighting_difference([True],[1]);self.assertEqual(d['nonFloat64DifferenceCount'],1)
    def test_diagnostic_written_before_strict_gate_without_reimport(self):
        p=Path(n.__file__);s=p.read_text();ast.parse(s)
        run=s[s.index('def run(u):'):]
        self.assertLess(run.index('g.write(diff_receipt,'),run.index("g.require(not differences['differences']"))
        for token in ('AssetImportTask(', 'import_asset_tasks(', 'duplicate_actors(', 'WorldFactory('):
            self.assertNotIn(token,s)
        self.assertIn('levels.new_level(g.MAP,False)',run)
        self.assertNotIn('tolerance=',run)

if __name__=='__main__':unittest.main()
