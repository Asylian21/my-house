"""Exact measured-pair CPU guards, not simulated native acceptance."""
import ast
import copy
import importlib.util
import math
from pathlib import Path
import unittest

def module(file):
    p=Path(__file__).with_name(file);s=importlib.util.spec_from_file_location(file,p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=module('megaplants-english-oak-scene-guards-r6.py')
n=module('megaplants-english-oak-scene-native-r6.py')

class GuardTests(unittest.TestCase):
    def test_actual4259_basis_preserves_failed_maps(self):
        _,_,_,before=g.old.validate_plan();audit=g.read(g.OUTPUT/'root-native-scene-failure-byte-audit-r5-r1.json')
        result=g.expected_before(audit,before);self.assertEqual(len(result),4259)
        for version in (4,5):self.assertIn('Content/'+g.PREFIX.removeprefix('/Game/')+'/Maps/EnglishOakPilotR'+str(version)+'.umap',result)
        bad=copy.deepcopy(audit);bad['newContentFiles']={}
        with self.assertRaises(RuntimeError):g.expected_before(bad,before)
    def test_exact_actual_source_copied_pair(self):
        source,copied,d=g.measured_lighting(g.pin(g.OUTPUT/'oak-usd-scene-lighting-differences-r5.json'))
        self.assertEqual(d['differenceCount'],4);self.assertFalse(g.binary64_equal(source,copied))
        expected=copy.deepcopy(source);expected[0]['transform'][1]=copied[0]['transform'][1]
        self.assertTrue(g.binary64_equal(expected,copied))
    def test_one_ulp_quaternion_or_sign_drift_rejected(self):
        _,copied,_=g.measured_lighting(g.pin(g.OUTPUT/'oak-usd-scene-lighting-differences-r5.json'))
        altered=copy.deepcopy(copied);altered[0]['transform'][1][0]=math.nextafter(altered[0]['transform'][1][0],math.inf)
        self.assertFalse(g.binary64_equal(altered,copied))
        altered=copy.deepcopy(copied);altered[0]['transform'][1]=[-v for v in altered[0]['transform'][1]]
        self.assertFalse(g.binary64_equal(altered,copied))
    def test_any_nontransform_or_other_transform_drift_rejected(self):
        _,copied,_=g.measured_lighting(g.pin(g.OUTPUT/'oak-usd-scene-lighting-differences-r5.json'))
        altered=copy.deepcopy(copied);altered[0]['components'][0]['properties']['intensity']+=1.
        self.assertFalse(g.binary64_equal(altered,copied))
        altered=copy.deepcopy(copied);altered[1]['transform'][0][0]=1e-15
        self.assertFalse(g.binary64_equal(altered,copied))
        self.assertFalse(g.binary64_equal([0.],[-0.]))
    def test_map_delta_preserves_all_failed_maps(self):
        old='Content/'+g.PREFIX.removeprefix('/Game/')+'/Maps/EnglishOakPilotR5.umap'
        before={'Content/Data/viewpoints.json':1,old:1}
        after={**before,'Content/Data/viewpoints.json':2,
            'Content/'+g.MAP.removeprefix('/Game/')+'.umap':1,
            'Content/'+g.GROUND_MATERIAL.removeprefix('/Game/')+'.uasset':1}
        self.assertTrue(g.validate_delta(before,after)['failedR4R5MapsByteExact'])
        after[old]=2
        with self.assertRaises(RuntimeError):g.validate_delta(before,after)
    def test_saved_readback_uses_measured_copied_without_epsilon(self):
        s=Path(n.__file__).read_text();ast.parse(s)
        self.assertIn('g.binary64_equal(observed_lights,measured_source)',s)
        self.assertIn('g.binary64_equal(copied_observed,measured_copied)',s)
        self.assertIn('g.binary64_equal(saved_light_values,expected_saved)',s)
        self.assertLess(s.index('g.write(saved_diff_receipt,'),s.index('g.require(g.binary64_equal(saved_light_values'))
        for token in ('AssetImportTask(', 'import_asset_tasks(', 'duplicate_actors(', 'WorldFactory(', 'epsilon='):
            self.assertNotIn(token,s)

if __name__=='__main__':unittest.main()
