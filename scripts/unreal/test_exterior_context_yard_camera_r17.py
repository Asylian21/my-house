"""Focused CPU framing/prefix tests; no QA project staging or Unreal launch."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

s=importlib.util.spec_from_file_location('yard_r17_source_camera_fixture',Path(__file__).with_name('exterior-context-yard-camera-r17.py'))
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)


class YardCameraTests(unittest.TestCase):
 def test_actual_complete_four_regions_and_two_crowns_are_framed(self):
  view,audit,_,_=c.derive();self.assertEqual(view['id'],c.VIEW_ID)
  self.assertEqual(sum(r['pointsChecked']for r in audit['sourceSurfaceFraming'].values()),684)
  self.assertEqual(len(audit['sourceSurfaceFraming']),4);self.assertEqual(len(audit['sourceShrubCrownFraming']),2)
  self.assertEqual(audit['sourceEyeBuildingBoxHits'],[]);self.assertFalse(audit['nativeOcclusionOrPlantVisibilityMeasured'])
 def test_behind_or_outside_source_frustum_rejected(self):
  view,_,_,_=c.derive();forward=c.c.unit(c.c.sub(view['targetCm'],view['eyeCm']))
  behind=[a-b for a,b in zip(view['eyeCm'],forward)]
  with self.assertRaises(RuntimeError):c.frame_points(view,[behind])
  outside=[view['targetCm'][0]+100000,view['targetCm'][1],view['targetCm'][2]]
  with self.assertRaises(RuntimeError):c.frame_points(view,[outside])
 def test_only_one_view_append_keeps_original_camera_and_sun_root(self):
  row=c.validated_supplement();original=c.checked(row['originalViewpoints']).read_bytes();before=json.loads(original)
  after=json.loads(c.appended_bytes(original,row['view']))
  self.assertEqual(after['views'][:-1],before['views']);self.assertEqual(after['views'][-1],row['view'])
  self.assertEqual({k:v for k,v in after.items()if k!='views'},{k:v for k,v in before.items()if k!='views'})
  duplicate=copy.deepcopy(before);duplicate['views'].append(row['view']);payload=(json.dumps(duplicate,indent=2,ensure_ascii=False)+'\n').encode()
  with self.assertRaises(RuntimeError):c.appended_bytes(payload,row['view'])


if __name__=='__main__':unittest.main()
