"""Meaningful source-only counterexamples for the selected R32 ground proposal."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r32_source_guard',ROOT/'scripts/unreal/exterior-context-yard-ground-source-guards-r32.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)


class SourceGuards(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.plan=g.read(g.PLAN);cls.proposal=g.read(cls.plan['proposal']['path']);cls.layout=g.read(cls.proposal['retainedLayout']['path']);cls.q=g.source_module()

 def piece(self):return copy.deepcopy(self.proposal['meshes'][0]['sourceSurfaceRanges'][0])

 def test_no_post_height_approximate_pruning(self):
  p=self.piece();p['quantizedTopologyAccounting']['approximateAreaThresholdUsed']=True
  with self.assertRaisesRegex(Exception,'Post-height topology'):g.check_topology(p,self.q)

 def test_no_nonzero_three_dimensional_face_dropped(self):
  p=self.piece();p['quantizedTopologyAccounting']['discardedFaceCount']=1
  with self.assertRaisesRegex(Exception,'Post-height topology'):g.check_topology(p,self.q)

 def test_positive_quantized_floor_cannot_be_reported_zero(self):
  p=self.piece();cell=p['quantizedPlanarPartition']['cells'][0]
  cell['discardedBeforeHeightExactZeroProjectedRegions']=[{'sourceProjectedPointsCm':[[0.,0.],[1.,0.],[0.,1.]],
   'quantizedProjectedPointsCm':[[0.,0.],[1.,0.],[0.,1.]],'quantizedProjectedAreaCm2':0.,'heightEvaluated':False}]
  with self.assertRaisesRegex(Exception,'positive quantized floor'):g.check_topology(p,self.q)

 def test_before_height_zero_is_not_allowed_after_lifting(self):
  p=self.piece();cell=p['quantizedPlanarPartition']['cells'][0]
  cell['discardedBeforeHeightExactZeroProjectedRegions']=[{'sourceProjectedPointsCm':[[0.,0.],[1.,0.],[2.,0.]],
   'quantizedProjectedPointsCm':[[0.,0.],[1.,0.],[2.,0.]],'quantizedProjectedAreaCm2':0.,'heightEvaluated':True}]
  with self.assertRaisesRegex(Exception,'pre-height native F32'):g.check_topology(p,self.q)

 def test_cell_union_loss_rejected(self):
  p=self.piece();p['quantizedPlanarPartition']['cells'][0]['wholeQuantizedCellUnionConservedExactly']=False
  with self.assertRaisesRegex(Exception,'Quantized cell union'):g.check_topology(p,self.q)

 def test_original_selected_glb_full_attributes_and_order(self):
  actual=g.check_glb(Path(self.plan['sourceGlb']['path']),self.proposal['meshes'])
  self.assertTrue(actual['writtenSourceGlbAllAttributesAndIndicesExactlyF32'])
  self.assertFalse(actual['sourceTangentAttributePresent'])

 def test_written_uv_mask_mutation_rejected(self):
  meshes=copy.deepcopy(self.proposal['meshes']);meshes[0]['uv1'][0][0]=.125
  with self.assertRaisesRegex(Exception,'TEXCOORD_1'):g.check_glb(Path(self.plan['sourceGlb']['path']),meshes)

 def test_written_ordered_indices_mutation_rejected(self):
  meshes=copy.deepcopy(self.proposal['meshes']);a=meshes[0]['indices'];a[0],a[1]=a[1],a[0]
  with self.assertRaisesRegex(Exception,'ordered full source topology'):g.check_glb(Path(self.plan['sourceGlb']['path']),meshes)

 def test_unknown_generated_glb_mesh_rejected(self):
  meshes=copy.deepcopy(self.proposal['meshes']);meshes[0]['id']='unselected_new_mesh'
  with self.assertRaisesRegex(Exception,'master transform'):g.check_glb(Path(self.plan['sourceGlb']['path']),meshes)

 def test_no_selected_source_native_base_fabrication(self):
  self.assertIsNone(self.plan['selectedNativeBase']);self.assertIs(self.plan['selectedNativeBasePending'],True)
  self.assertFalse(self.plan['audit']['nativeApplied']);self.assertFalse(self.plan['audit']['nativeAppearanceAccepted'])

 def tiny_depth(self,height):
  vertices=[[0.,0.,height],[0.,1.,height],[1.,0.,height]]
  return [{'role':'entry_walk','verticesCm':vertices,'indices':[0,1,2]},
   {'role':'yard_substrate','verticesCm':[[x,y,0.]for x,y,z in vertices],'indices':[0,1,2]}]

 def test_exact_coplanar_underlay_rejected(self):
  with self.assertRaisesRegex(Exception,'coplanar with/below'):g.check_depth(self.tiny_depth(0.))

 def test_inverted_layer_depth_rejected(self):
  with self.assertRaisesRegex(Exception,'coplanar with/below'):g.check_depth(self.tiny_depth(-.001))

 def test_tiny_positive_depth_is_preserved_without_epsilon_pruning(self):
  result=g.check_depth(self.tiny_depth(.00000001))
  self.assertGreater(result['independentMinimumHardAboveUnderlayCm'],0.)
  self.assertEqual(result['independentExactTriangleIntersections'],1)

 def test_disjoint_depth_does_not_fabricate_complete_proof(self):
  meshes=self.tiny_depth(1.);meshes[1]['verticesCm']=[[x+50,y,z]for x,y,z in meshes[1]['verticesCm']]
  with self.assertRaisesRegex(Exception,'not observed'):g.check_depth(meshes)


if __name__=='__main__':unittest.main(verbosity=2)
