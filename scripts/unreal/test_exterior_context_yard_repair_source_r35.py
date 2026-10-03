"""CPU source fixtures only; no new native R35 proof."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('new_r35_source',ROOT/'scripts/unreal/exterior-context-yard-repair-study-r35.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

class SourceRepair(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.layout=s.read(ROOT/'output/unreal/exterior-context-yard-20261002-r28-study/yard-layout.json')
  cls.study=s.read(ROOT/'output/unreal/exterior-context-yard-ground-20261002-r32-study-r5/yard-ground-study-plan.json')
  cls.geometry=s.read(cls.study['proposal']['path']);cls.hard=[m for m in cls.geometry['meshes']if m['role']in('entry_walk','service_court')]
  cls.graph=s.read(ROOT/'output/unreal/exterior-20261001-r16a/exterior-import-report.json')['materials']['materials']['context_distant_terrain']['graph']
 def test_original_glb_only_two_coverage_channels_change(self):
  patches=[s.proposed_uv_patch(m,self.layout)for m in self.hard]
  original=Path(self.study['sourceGlb']['path']).read_bytes();after,proof=s.glb_channel_patch(self.study['sourceGlb']['path'],patches)
  self.assertEqual(len(after),len(original));self.assertTrue(proof['allBytesOutsideTwoHardUv1RChannelsExact']);self.assertTrue(proof['originalSubstrateEntireGeometryAndUv1Exact'])
  self.assertEqual(sum(p['sourceTriangles']for p in patches),4519)
  for p in patches:self.assertTrue(all(a[1]==b[1]for a,b in zip(p['originalUv1F32'],p['proposedUv1F32'])))
 def test_internal_join_gets_union_coverage_without_new_geometry(self):
  layout={'surfaces':[]}
  for i in range(3):
   for role,a,b in [('entry_walk',0,100),('service_court',100,200)]:layout['surfaces'].append({'id':role+str(i),'buildingSourceId':str(i),'role':role,'domainCm':{'type':'Polygon','coordinates':[[[a,0],[b,0],[b,100],[a,100],[a,0]]]}})
  mesh={'id':'fixture','role':'entry_walk','verticesCm':[[100,50,0],[0,50,0],[50,50,0]],'normals':[[0,0,1]]*3,'uv0':[[0,0]]*3,'uv1':[[0,0.2]]*3,'indices':[0,1,2],'sourceSurfaceRanges':[{'sourcePieceId':'entry_walk0','firstTriangle':0,'triangles':1}]}
  before=copy.deepcopy(mesh);p=s.proposed_uv_patch(mesh,layout)
  self.assertEqual(p['proposedUv1F32'][0][0],1.0);self.assertEqual(p['proposedUv1F32'][1][0],0.0);self.assertEqual(mesh,before)
 def test_actual_saved_graph_only_near_response_two_codes_change(self):
  after,proof=s.material_variant(self.graph);self.assertEqual(proof['actualSavedResponseCoefficient'],.30)
  self.assertEqual(len(after['nodes']),58);self.assertEqual(after['flags'],self.graph['flags']);self.assertEqual(after['roots'],self.graph['roots'])
  changed=[(a['role'],a,b)for a,b in zip(self.graph['nodes'],after['nodes'])if a!=b]
  self.assertEqual(len(changed),2)
  for _,a,b in changed:
   c=copy.deepcopy(b);c['values']['code']=a['values']['code'];self.assertEqual(c,a)
 def test_changed_original_earth_fraction_or_unknown_graph_is_rejected(self):
  patches=[s.proposed_uv_patch(m,self.layout)for m in self.hard];patches[0]['originalUv1F32'][0][1]=.8
  with self.assertRaisesRegex(RuntimeError,'Serialized R32 UV1'):s.glb_channel_patch(self.study['sourceGlb']['path'],patches)
  graph=copy.deepcopy(self.graph)
  for n in graph['nodes']:
   if n['role']=='BreziExterior:near-terrain-normal-strength':n['values']['code']='return 0.0;'
  with self.assertRaisesRegex(RuntimeError,'baseline differs'):s.material_variant(graph)

if __name__=='__main__':unittest.main()
