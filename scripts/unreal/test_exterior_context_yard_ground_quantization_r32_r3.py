"""Exact-zero topology guards; CPU arithmetic only, no native acceptance."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('yard_quantization_r32_r3',Path(__file__).with_name('exterior-context-yard-ground-quantization-r32-r3.py'))
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)


def row(points,indices):
 return {'verticesCm':points,'indices':indices,'uv0':[[p[0]/100,p[1]/100]for p in points],
  'uv1':[[.5,.2]for p in points],'sourceGroundVertexWitnesses':{str(i):{'sourceId':i}for i in range(len(points))}}


class ExactTopologyTests(unittest.TestCase):
 def test_only_decoded_exact_zero_faces_removed_and_ids_preserved(self):
  r=row([[20000.,20000.,0.],[20000.,20000.0001,0.],[20000.0001,20000.,0.],
   [20000.,20000.,0.],[20000.,20001.,0.],[20001.,20000.,0.]],[0,1,2,3,4,5])
  actual=q.compact_exact_zero_faces(r);proof=actual['quantizedTopologyAccounting']
  self.assertEqual(proof['discardedFaceCount'],1);self.assertEqual(proof['retainedOriginalTriangleIds'],[1])
  self.assertEqual(proof['retainedOriginalVertexIds'],[3,4,5]);self.assertEqual(actual['indices'],[0,1,2])
  self.assertEqual(proof['discardedDecodedProjectedFootprintAreaCm2'],0.)
  self.assertEqual(proof['discardedExactZeroThreeDimensionalAreaFaces'][0]['decodedCrossProductCm2'],[0.,0.,0.])
  self.assertFalse(proof['approximateAreaThresholdUsed']);self.assertFalse(proof['nonzeroFacesDropped'])
  self.assertEqual(actual['sourceGroundVertexWitnesses']['0'],{'sourceId':3})
  self.assertEqual(len(r['indices']),6)

 def test_tiny_nonzero_face_is_retained_without_threshold(self):
  r=row([[0.,0.,0.],[0.,.00001,0.],[.00001,0.,0.]],[0,1,2])
  actual=q.compact_exact_zero_faces(r)
  self.assertEqual(actual['indices'],[0,1,2]);self.assertEqual(actual['quantizedTopologyAccounting']['discardedFaceCount'],0)

 def test_nonzero_vertical_quantized_face_is_rejected_not_pruned(self):
  r=row([[20000.,20000.,0.],[20000.,20000.0001,1.],[20001.,20000.,0.]],[0,1,2])
  self.assertNotEqual(q.cross(*q.native_points(r['verticesCm'])),[0.,0.,0.])
  with self.assertRaises(ValueError):q.compact_exact_zero_faces(r)

 def test_source_or_decoded_inverted_nonzero_face_rejected(self):
  clockwise=row([[0.,0.,0.],[0.,1.,0.],[1.,0.,0.]],[0,1,2])
  bad=row(clockwise['verticesCm'],[0,2,1])
  with self.assertRaises(ValueError):q.compact_exact_zero_faces(bad)
  with patch.object(q,'native_points',return_value=[clockwise['verticesCm'][0],clockwise['verticesCm'][2],clockwise['verticesCm'][1]]):
   with self.assertRaises(ValueError):q.compact_exact_zero_faces(clockwise)


if __name__=='__main__':unittest.main()
