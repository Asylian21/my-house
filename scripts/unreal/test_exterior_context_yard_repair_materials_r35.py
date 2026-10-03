"""Pure R35 graph delta fixtures, never native material acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('new_r35_material',ROOT/'scripts/unreal/exterior-context-yard-repair-materials-r35.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class MaterialDelta(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.v=json.loads((ROOT/'output/unreal/exterior-context-yard-20261002-r35-source-repair-proposal/backdrop-near-pbr-graph-variant.json').read_text())
 def test_actual_two_code_delta_restore(self):
  proof=m.validate_variant(self.v['originalFullGraph'],self.v['proposedGraph']);self.assertEqual(proof['nodeCount'],58);self.assertEqual(proof['originalNearCoefficient'],.30);self.assertEqual(proof['newNearCoefficient'],.65)
 def test_changed_texture_route_rejected(self):
  g=copy.deepcopy(self.v['proposedGraph']);n=next(n for n in g['nodes']if n['class']=='MaterialExpressionTextureSample');n['values']['texture']='/Game/Other/Texture.Texture'
  with self.assertRaises(RuntimeError):m.validate_variant(self.v['originalFullGraph'],g)
 def test_stale_zero_graph_baseline_rejected(self):
  g=copy.deepcopy(self.v['proposedGraph']);next(n for n in g['nodes']if n['role']=='BreziExterior:near-terrain-normal-strength')['values']['code']='return 0.65;'
  with self.assertRaises(RuntimeError):m.validate_variant(self.v['originalFullGraph'],g)
 def test_root_flag_or_extra_node_rejected(self):
  for delta in ('root','flag','node'):
   g=copy.deepcopy(self.v['proposedGraph'])
   if delta=='root':g['roots']['NORMAL']=['BreziExterior:world-position','']
   elif delta=='flag':g['flags']['two_sided']=not g['flags']['two_sided']
   else:g['nodes'].append(copy.deepcopy(g['nodes'][0]))
   with self.assertRaises(RuntimeError):m.validate_variant(self.v['originalFullGraph'],g)
if __name__=='__main__':unittest.main()
