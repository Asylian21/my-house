"""Domain scope and unit correctness for the semantic pool override."""
import importlib.util,json,math,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('water',Path(__file__).with_name('photoreal-water.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class WaterContractTest(unittest.TestCase):
    def fixture(self):
        base=m.ROOT/'output/unreal/photoreal-20260923'
        if not base.is_dir():self.skipTest('Local canonical fixture absent')
        return json.loads((base/'geometry/scene.json').read_text()),json.loads((base/'model-refresh-import-report.json').read_text())
    def test_pool_selected_by_semantics_not_ordinal(self):
        scene,report=self.fixture();selected=m.select_water(scene,report)
        self.assertEqual(len(selected),1);self.assertEqual(selected[0]['sourceName'],'real-pool-water')
        self.assertNotIn('water',selected[0]['sourceName'].split('-')[:-1])
        source_slot=selected[0]['sourceSlot'];renamed='MAT_TEST_REORDERED'
        scene['materials'][renamed]=scene['materials'].pop(source_slot)
        for b in report['materials']['bindings']:
            if b['sourceSlot']==source_slot:b['sourceSlot']=renamed
        for r in scene['objects']:
            r['materialSlots']=[renamed if x==source_slot else x for x in r['materialSlots']]
        self.assertEqual(m.select_water(scene,report)[0]['sourceSlot'],renamed)
    def test_reject_changed_water_geometry_or_archive(self):
        scene,report=self.fixture();b=m.select_water(scene,report)[0]
        record=next(r for r in scene['objects'] if r['id']==b['id']);record['boundsMm']['max'][2]+=10
        with self.assertRaisesRegex(RuntimeError,'flat canonical surface'):m.select_water(scene,report)
        scene['activeDesign']['variant']='A'
        with self.assertRaisesRegex(RuntimeError,'active C/B/B'):m.select_water(scene,report)
    def test_metre_to_native_centimetre_attenuation(self):
        self.assertEqual(m.transmittance(0),[1,1,1])
        for a,s,t in zip(m.ABSORPTION_PER_METRE,m.SCATTERING_PER_METRE,m.transmittance(1.4)):
            self.assertAlmostEqual(t,math.exp(-(a+s)*.01*140))
        self.assertTrue(all(.82<t<.97 for t in m.transmittance(1.4)))
        self.assertLess(m.transmittance(1.4)[0],m.transmittance(1.4)[2])
        self.assertEqual(m.recipe()['opacity'],0)
        self.assertFalse(m.recipe()['dynamicCaustics'])
        self.assertFalse(m.recipe()['geometryDisplacement'])
        with self.assertRaisesRegex(RuntimeError,'Invalid optical'):m.transmittance(-1)

if __name__=='__main__':unittest.main()
