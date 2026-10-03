"""Focused source framing/vegetation/prefix guards; no staging or Unreal."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('yard_r18_source_camera_fixture',Path(__file__).with_name('exterior-context-yard-camera-r18.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


class YardCameraTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.view,cls.audit,_,_=c.derive()
  cls.supplement=c.validated_supplement()

 def test_actual_complete_four_regions_and_two_crowns_are_framed(self):
  self.assertEqual(self.view['id'],c.VIEW_ID)
  self.assertEqual(sum(r['pointsChecked']for r in self.audit['sourceSurfaceFraming'].values()),684)
  self.assertEqual(len(self.audit['sourceSurfaceFraming']),4)
  self.assertEqual(len(self.audit['sourceShrubCrownFraming']),2)
  self.assertEqual(self.audit['sourceEyeBuildingBoxHits'],[])
  self.assertFalse(self.audit['nativeOcclusionOrPlantVisibilityMeasured'])

 def test_actual_old_tree_crown_caught_new_eye_and_wood_clear(self):
  a=self.audit['sourceVegetationVolumeAudit']
  self.assertIn('village_nearest_grove_15',a['priorR17SourceEyeLeafCrownHits'])
  self.assertTrue(a['sourceTreeLeafAndLowerWoodEyeAndCompleteCorridorClear'])
  for key in ('sourceEyeTreeLeafHits','sourceCorridorTreeLeafHits','sourceEyeLowerBarkHits','sourceCorridorLowerBarkHits','sourceEyeEcologyHits'):
   self.assertEqual(a[key],[])
  leaf=a['selectivelyDecodedNearTreeParts'][0]['sourceAllLodLeafBoundsCm']
  self.assertLess(a['sourceEyeClearanceBoxCm'][1][2],leaf[0][2])

 def test_lower_growth_corridor_overlap_is_explicit_not_visibility_acceptance(self):
  a=self.audit['sourceVegetationVolumeAudit']
  self.assertEqual(a['sourceLowGrowthCorridorOverlapsRemain'],68)
  self.assertFalse(a['sourceCompleteCorridorAllVegetationClear'])
  self.assertFalse(a['nativeRaycastExecuted']);self.assertFalse(a['nativeVisibilityVerified'])

 def test_support_cone_separates_only_external_boxes(self):
  cone=c.occlusion.support_cone({'eyeCm':[0.,0.,0.]},[[10.,-1.,-1.],[10.,1.,1.]])
  self.assertTrue(c.occlusion.cone_overlap(cone,[[4.,-.2,-.2],[6.,.2,.2]]))
  self.assertFalse(c.occlusion.cone_overlap(cone,[[4.,10.,-.2],[6.,11.,.2]]))

 def test_behind_or_outside_frustum_rejected(self):
  forward=c.c.unit(c.c.sub(self.view['targetCm'],self.view['eyeCm']))
  behind=[a-b for a,b in zip(self.view['eyeCm'],forward)]
  with self.assertRaises(RuntimeError):c.frame_points(self.view,[behind])
  outside=[self.view['targetCm'][0]+100000,self.view['targetCm'][1],self.view['targetCm'][2]]
  with self.assertRaises(RuntimeError):c.frame_points(self.view,[outside])

 def test_append_preserves_original_rows_and_sun_duplicate_rejects(self):
  original=c.checked(self.supplement['originalViewpoints']).read_bytes();before=json.loads(original)
  after=json.loads(c.appended_bytes(original,self.view))
  self.assertEqual(after['views'][:-1],before['views'])
  self.assertEqual({k:v for k,v in after.items()if k!='views'},{k:v for k,v in before.items()if k!='views'})
  duplicate=copy.deepcopy(before);duplicate['views'].append(self.view)
  payload=(json.dumps(duplicate,indent=2,ensure_ascii=False)+'\n').encode()
  with self.assertRaises(RuntimeError):c.appended_bytes(payload,self.view)


if __name__=='__main__':unittest.main()
