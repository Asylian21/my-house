"""Focused source layout counterfactuals; no Unreal or native execution."""
import copy
import importlib.util
from pathlib import Path
import unittest

s=importlib.util.spec_from_file_location('yard_r28_guard',Path(__file__).with_name('exterior-context-yard-source-guards-r28.py'))
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)


class YardSourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.plan,cls.layout,cls.masks,cls.data,cls.models,cls.audit=g.load_source()
 def reject(self,change):
  layout=copy.deepcopy(self.layout);change(layout)
  with self.assertRaises(ValueError):g.validate_geometry(layout,self.masks,self.data['buildings'],self.models)
 def test_actual_selected_layout(self):
  self.assertEqual((self.audit['surfaces'],self.audit['shrubs']),(12,13))
  self.assertGreater(self.audit['minimumConservativeCrownClearanceToUnbufferedExclusionsCm'],20)
 def test_disconnected_entry_surface(self):
  from shapely.affinity import translate
  from shapely.geometry import shape,mapping
  def change(v):
   row=next(r for r in v['surfaces']if r['role']=='entry_walk');row['domainCm']=mapping(translate(shape(row['domainCm']),xoff=5000))
  self.reject(change)
 def test_building_surface_intrusion(self):
  from shapely.geometry import shape,mapping,Polygon
  def change(v):
   row=v['surfaces'][0];building=next(b for b in self.data['buildings']['buildings']if b['id']==row['buildingSourceId'])
   row['domainCm']=mapping(shape(row['domainCm']).union(Polygon(building['polygonsCm'][0][0])))
  self.reject(change)
 def test_plant_moved_off_bed(self):
  self.reject(lambda v:v['planting'][0]['positionCm'].__setitem__(0,v['planting'][0]['positionCm'][0]+1000))
 def test_crown_scale_widened(self):
  self.reject(lambda v:v['planting'][0].__setitem__('uniformScale',v['planting'][0]['uniformScale']*1.2))
 def test_root_raised_from_source_ground(self):
  self.reject(lambda v:v['planting'][0]['positionCm'].__setitem__(2,v['planting'][0]['positionCm'][2]+1))
 def test_unverified_road_access_claim(self):
  self.reject(lambda v:v['yards'][0].__setitem__('streetConnectionProposed',True))


if __name__=='__main__':unittest.main()
