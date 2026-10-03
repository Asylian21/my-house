"""Adversarial CPU source receipt checks; no synthetic native evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest

p=Path(__file__).with_name('megaplants-english-oak-editor-check-r6.py')
s=importlib.util.spec_from_file_location('oak_actual_scene_editor_checker_r6',p)
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan,cls.source,cls.base,cls.before=c.g.validate_plan()
        cls.report=c.g.read(c.g.OUTPUT/c.n.REPORT)
    def check(self,report):return c.validate_report(report,self.plan,self.source,self.base,self.before)
    def test_actual_closed_receipt(self):
        self.assertEqual(self.check(self.report)['nativeAssemblyPartReferences'],11)
    def test_one_ulp_saved_light_or_unmeasured_intensity_rejects(self):
        import math
        row=copy.deepcopy(self.report)
        row['savedLightingObservedSubset'][0]['transform'][1][0]=math.nextafter(row['savedLightingObservedSubset'][0]['transform'][1][0],math.inf)
        with self.assertRaises(RuntimeError):self.check(row)
        row=copy.deepcopy(self.report);row['savedLightingObservedSubset'][0]['components'][0]['properties']['intensity']+=1.
        with self.assertRaises(RuntimeError):self.check(row)
    def test_old_map_or_preserved_usd_byte_change_rejects(self):
        for key in ['Content/Brezi/Maps/Brezi.umap',next(p for p in self.before if '/OriginalUSD/' in p)]:
            row=copy.deepcopy(self.report);row['afterInventory'][key]={**row['afterInventory'][key],'sha256':'0'*64}
            with self.assertRaises(RuntimeError):self.check(row)
    def test_node_completeness_and_wind_promotion_reject(self):
        for key in ['nativeAssemblyNodesReadbackAvailable','windSidecarImported','fullLightingPropertyCloneClaimed']:
            row=copy.deepcopy(self.report);row[key]=True
            with self.assertRaises(RuntimeError):self.check(row)

if __name__=='__main__':unittest.main()
