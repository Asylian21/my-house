"""Focused new source guards; no native calls or historical producer replay."""
import copy
import importlib.util
from pathlib import Path
import unittest
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r40_source_fixtures',ROOT/'scripts/unreal/exterior-garden-foreground-fern-study-r40.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


class SourceProposal(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.proposal=m.read(m.OUTPUT/'foreground-fern-source-plan.json')
  cls.data,cls.pins=m.load_inputs()
  cls.witness={v['actor']:cls.data['currentWitness'][v['actor']]for v in cls.proposal['historicalCurrentMembership']['groups'].values()}
  cls.raw={v['componentPath']:cls.data['currentRaw'][v['componentPath']]for v in cls.proposal['historicalCurrentMembership']['groups'].values()}
 def test_exact_source_23_selection_and_one_available_lod_no_binding(self):
  chosen=m.select_roots(self.data['periwinklePlan']['proposedPlacements'],self.data['stepGuard'])
  self.assertEqual([v['rootId']for v in chosen],list(m.IDS))
  self.assertEqual(len(self.proposal['placements']),23)
  self.assertEqual(sum(len(v['retainedRootIds'])for v in self.proposal['wholeOriginalGroupFiltersProposed'].values()),361)
  self.assertEqual(self.proposal['sourceBudget']['fernVariantCounts'],{'fern_02_a':8,'fern_02_c':8,'fern_02_d':7})
  self.assertTrue(all([v['index']for v in row['availableLods']]==[0]for row in self.proposal['models'].values()))
  self.assertTrue(all(self.proposal[k]is None for k in ('futureSelectedNativeBase','futureNativeProjectClone','futureNativeReport','futureRootImageDecision')))
  self.assertFalse(self.proposal['limits']['nativeAppearanceAccepted'])
 def test_source_selection_hidden_foreign_or_moved_root_rejects(self):
  for field,value in [('sourceBedId','DOM_01966'),('positionCm',[10000,10000,0]),('sourceCameraProjection',{'verticesInsideFrustum':0})]:
   rows=copy.deepcopy(self.data['periwinklePlan']['proposedPlacements']);next(v for v in rows if v['rootId']==m.IDS[0])[field]=value
   with self.subTest(field=field),self.assertRaises(RuntimeError):m.select_roots(rows,self.data['stepGuard'])
 def test_fresh_membership_raw_and_signed_zero_mutations_reject(self):
  self.assertTrue(m.validate_future_membership(self.proposal,self.witness,self.raw))
  group=next(iter(self.proposal['historicalCurrentMembership']['groups'].values()))
  for kind in ('order','mesh','matrix','seed','signed-zero'):
   w=copy.deepcopy(self.witness);raw=copy.deepcopy(self.raw);actor=w[group['actor']];component=actor['components'][0];control=raw[group['componentPath']]
   if kind=='order':component['orderedInstanceTransformsSha256']='0'*64
   elif kind=='mesh':component['mesh']='/Game/Foreign.Mesh'
   elif kind=='matrix':control['rawMatrixBinary64Sha256']='0'*64
   elif kind=='seed':control['mainRandomSeed']+=1
   else:actor['transform'][0][0]=-0.0
   with self.subTest(kind=kind),self.assertRaises(RuntimeError):m.validate_future_membership(self.proposal,w,raw)
 def test_whole_source_circles_inside_original_mask_and_overreach_rejects(self):
  guard=self.data['stepGuard'];garden=self.data['gardenPlan'];steps=guard.validated_steps(garden['sourceStepTrianglesCm']);bed=garden['sourceMulchTrianglesCm']['DOM_01965']
  for row in self.proposal['placements']:
   got=m.circle_guard(row['positionCm'][:2],row['immutablePreR36CircleRadiusCm'],bed,steps,guard)
   self.assertGreater(got['bedCircleClearanceCm'],0.)
   self.assertLess(row['proposedWholeFernRadiusCm'],row['immutablePreR36CircleRadiusCm'])
   self.assertEqual(row['positionCm'][:2],row['originalSourceRow']['positionCm'][:2])
   self.assertEqual(row['yawDeg'],row['originalSourceRow']['yawDeg'])
   self.assertEqual(row['allActualAvailableLodsChecked'],[0])
  row=self.proposal['placements'][0];distance=row['circleClearance']['bedBoundaryDistanceCm']
  with self.assertRaises(RuntimeError):m.circle_guard(row['positionCm'][:2],distance+1.,bed,steps,guard)
  with self.assertRaises(RuntimeError):m.circle_guard([-830,-1000],1.,bed,steps,guard)
 def test_invented_native_lod_or_reversed_source_contract_rejects(self):
  for kind in ('lod','winding'):
   data=dict(self.data);data['fernNativeReport']=copy.deepcopy(data['fernNativeReport']);data['fernDescriptor']=copy.deepcopy(data['fernDescriptor'])
   if kind=='lod':data['fernNativeReport']['nativeGeometryReadback']['fern_02_a']['lodCount']=3
   else:data['fernDescriptor']['models'][0]['sourceOriginalWindingPreserved']=False
   with self.subTest(kind=kind),self.assertRaises(RuntimeError):m.model_contract(data,dict(self.pins))


if __name__=='__main__':unittest.main(verbosity=2)
