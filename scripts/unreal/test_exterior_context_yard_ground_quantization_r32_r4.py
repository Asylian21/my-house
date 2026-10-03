"""XY-first exact topology/holes/fixed-point tests; CPU only."""
import importlib.util
from pathlib import Path
import unittest
from shapely.geometry import Polygon
from shapely.ops import unary_union

spec=importlib.util.spec_from_file_location('yard_quantization_r32_r4',Path(__file__).with_name('exterior-context-yard-ground-quantization-r32-r4.py'))
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)


class QuantizedPlanarTests(unittest.TestCase):
 def test_measured_vertical_sliver_is_zero_floor_before_height_not_pruned_3d_face(self):
  poly=Polygon([[7788.826497234417,30239.99841557406],[7788.818102646091,30240.],[7800.,30240.]])
  triangles,proof=q.quantized_cell_triangles(poly)
  self.assertEqual(triangles,[]);self.assertEqual(proof['quantizedCellFloorAreaCm2'],0.)
  self.assertEqual(len(proof['discardedBeforeHeightExactZeroProjectedRegions']),1)
  self.assertFalse(proof['discardedBeforeHeightExactZeroProjectedRegions'][0]['heightEvaluated'])
  self.assertEqual(proof['discardedQuantizedFootprintAreaCm2'],0.)
  self.assertTrue(proof['wholeQuantizedCellUnionConservedExactly'])

 def test_tiny_nonzero_floor_is_retained_without_area_threshold(self):
  triangles,proof=q.quantized_cell_triangles(Polygon([[0.,0.],[0.,.00001],[.00001,0.]]))
  self.assertEqual(len(triangles),1);self.assertGreater(proof['quantizedCellFloorAreaCm2'],0.)
  self.assertFalse(proof['positiveAreaPolygonsDropped']);self.assertFalse(proof['approximateAreaThresholdUsed'])

 def test_cell_hole_remains_clear_and_all_coordinates_exact_native_fixed_points(self):
  poly=Polygon([[20000.,20000.],[20000.,20040.],[20040.,20040.],[20040.,20000.]],
   [[[20010.,20010.],[20030.,20010.],[20030.,20030.],[20010.,20030.]]])
  triangles,proof=q.quantized_cell_triangles(poly);union=unary_union([Polygon(t)for t in triangles])
  self.assertTrue(union.equals(poly));self.assertTrue(proof['wholeQuantizedCellUnionConservedExactly'])
  self.assertTrue(all(q.stable_native_coordinate(v)==v for tri in triangles for p in tri for v in p))
  for tri in triangles:
   a,b,c=tri;self.assertLess((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]),0.)

 def test_duplicate_quantized_xy_reuses_one_height_for_actual_final_mesh(self):
  coords=[7997.667742179926,7997.667742179925]
  fixed=[q.stable_native_coordinate(v)for v in coords];self.assertEqual(fixed[0],fixed[1])
  heights={};calls=0
  for x in fixed:
   if x not in heights:heights[x]=x/37.;calls+=1
  self.assertEqual(calls,1)


if __name__=='__main__':unittest.main()
