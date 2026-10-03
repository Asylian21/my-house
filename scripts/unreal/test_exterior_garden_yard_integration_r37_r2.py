"""Only the NEW graph-reader/diagnostic/R2 provenance fixtures; no UE calls."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r37_reader_r2_fixtures',ROOT/'scripts/unreal/exterior-garden-yard-integration-native-r37-r2.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n);g=n.guard


class Repair(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.b=g.selected_base();g.validate_clone(cls.b);cls.routes=g.reader_dispatch(cls.b)
  cls.recorded=g.read(g.checked(cls.b['report']['originalProtectedControlsSaved']))
  cls.graphs={};textures=set();n._material_records(cls.recorded,cls.graphs,textures);n._material_records(cls.b['report']['materialReport'],cls.graphs,textures)

 def test_01_exact_selected61_partition_and_no_unknown_asset_fallback(self):
  self.assertEqual({k:len(v)for k,v in self.routes.items()},{'basic':49,'neighbor':9,'tree':3})
  assets=set().union(*map(set,self.routes.values()));self.assertEqual(assets,set(self.graphs))
  unknown='/Game/Brezi/NeighborFinish20261001R18/Materials/M_unselected.M_unselected'
  with self.assertRaises(RuntimeError):n.selected_graph_snapshot(None,NS(get_path_name=lambda:unknown),unknown,self.b,{})

 def test_02_dispatch_executes_only_declared_snapshot_owner(self):
  calls=[];generic=lambda u,m: calls.append('basic')or{'route':'basic'}
  neighbor=lambda u,m,existing:calls.append('neighbor')or{'route':'neighbor'}
  tree=lambda u,m,existing:calls.append('tree')or{'route':'tree'}
  h={'existing':NS(graph_snapshot=generic),'neighborMaterial':NS(graph_snapshot=neighbor),'treeMaterials':NS(graph_snapshot=tree)}
  for route,assets in self.routes.items():
   for asset in assets:
    calls.clear();value,got=n.selected_graph_snapshot(None,NS(get_path_name=lambda asset=asset:asset),asset,self.b,h)
    self.assertEqual((got,value,calls),(route,{'route':route},[route]))

 def test_03_neighbor_recorded_extended_schema_is_not_generic_and_stays_exact(self):
  neighbor=self.recorded['originalMaterials']['original56']['clean']['neighbor']['materials']
  for row in neighbor.values():
   graph=row['graph'];basic=copy.deepcopy(graph);basic['roots'].pop('REFRACTION')
   basic['flags'].pop('translucency_lighting_mode');basic['flags'].pop('refraction_method')
   for node in basic['nodes']:node['values'].pop('world_position_shader_offset',None)
   self.assertNotEqual(g.digest(basic),g.digest(graph))
   self.assertTrue({'REFRACTION'}<=set(graph['roots']))
   self.assertTrue({'translucency_lighting_mode','refraction_method'}<=set(graph['flags']))
   with tempfile.TemporaryDirectory()as folder:
    record={'sha256':g.digest(graph),'graph':graph};directory=Path(folder)
    n.compare_recorded_graph(row['asset'],record,graph,'neighbor',self.b['report']['originalProtectedControlsSaved'],directory,0)
    with self.assertRaises(RuntimeError):n.compare_recorded_graph(row['asset'],record,basic,'neighbor',self.b['report']['originalProtectedControlsSaved'],directory,1)

 def test_04_tree_khr_offset_scalars_cannot_be_dropped_or_mutated(self):
  trees=self.recorded['originalMaterials']['originalTree3']['materials'];found=0
  for row in trees.values():
   for at,node in enumerate(row['graph']['nodes']):
    if node['class']!='MaterialExpressionConstant2Vector':continue
    found+=1;self.assertEqual(set(node['values']),{'r','g'})
    for mutation in ({},dict(node['values'],g=node['values']['g']+1e-9)):
     bad=copy.deepcopy(row['graph']);bad['nodes'][at]['values']=mutation
     with tempfile.TemporaryDirectory()as folder:
      with self.assertRaises(RuntimeError):n.compare_recorded_graph(row['asset'],{'sha256':g.digest(row['graph']),'graph':row['graph']},bad,'tree',self.b['report']['originalProtectedControlsSaved'],Path(folder),0)
  self.assertEqual(found,1)

 def test_05_failed_graph_checkpoint_exists_before_raise_and_keeps_complete_observation(self):
  asset=self.routes['neighbor'][0];expected=self.graphs[asset];bad=copy.deepcopy(expected['graph']);bad['roots']['REFRACTION']=['tampered','']
  with tempfile.TemporaryDirectory()as folder:
   checkpoint=Path(folder);directory=checkpoint/'material-graphs-before';directory.mkdir()
   with self.assertRaisesRegex(RuntimeError,asset):n.compare_recorded_graph(asset,expected,bad,'neighbor',self.b['report']['originalProtectedControlsSaved'],directory,0)
   got=json.loads((directory/'graph-000.json').read_text())
   self.assertEqual(got['actualCompleteGraph'],bad);self.assertEqual(got['recordedExpectedCompleteGraph'],expected['graph'])
   self.assertEqual(got['expectedPinnedSource'],self.b['report']['originalProtectedControlsSaved'])
   self.assertTrue(got['fullGraphDifferences']);self.assertEqual(got['reader'],'neighbor')
   closure=n.material_graph_diagnostic_files(checkpoint)
   self.assertEqual(closure,{'before':[g.pin(directory/'graph-000.json')],'saved':[]})

 def test_06_hash_only_original_graph_does_not_accept_changed_graph_or_digest(self):
  expected={'sha256':g.digest({'recorded':'original'})}
  with tempfile.TemporaryDirectory()as folder:
   with self.assertRaises(RuntimeError):n.compare_recorded_graph(self.routes['basic'][0],expected,{'recorded':'changed'},'basic',self.b['report']['originalProtectedControlsSaved'],Path(folder),0)
   got=json.loads((Path(folder)/'graph-000.json').read_text());self.assertFalse(got['completeRecordedGraphShapeAvailable'])
   self.assertIsNone(got['fullGraphDifferences']);self.assertNotEqual(got['recordedExpectedGraphSha256'],got['actualCompleteGraphSha256'])

 def test_07_exact_failed_r1_and_fresh_r2_clone_header(self):
  prior=g.prior_failed_attempt();self.assertEqual((prior['actualPid'],prior['actualExitCode'],prior['sourcePinCount']),(53262,255,832))
  self.assertFalse(prior['failingAssetActuallyRecorded']);self.assertFalse(prior['sceneOrAssetMutationOccurred'])
  self.assertEqual(g.CANDIDATE.name,'exterior-20261002-r37b');self.assertEqual(g.validate_clone(self.b),g.CLONE_PIN)
  actual=g.read(prior['files']['audit']['path']);original=g.read
  bad=copy.deepcopy(actual);bad['noCandidateMapOrPackageByteChange']=False
  with patch.object(g,'read',side_effect=lambda path:bad if str(path)==prior['files']['audit']['path']else original(path)):
   with self.assertRaises(RuntimeError):g.prior_failed_attempt()

 def test_08_unmodified_scene_geometry_and_raw_control_kernels_are_ast_exact_r1(self):
  def functions(path):return{f.name:ast.dump(f,include_attributes=False)for f in ast.parse(path.read_text()).body if isinstance(f,ast.FunctionDef)}
  old=functions(ROOT/'scripts/unreal/exterior-garden-yard-integration-native-r37.py');new=functions(ROOT/n.OWNER)
  keys=['validate_project','_raw_control','protected_controls','_material_records','geometry_readback','apply_declared_scene','verify_reloaded_scene']
  self.assertEqual({k:old[k]for k in keys},{k:new[k]for k in keys})
  self.assertIn('world_position_shader_offset',(ROOT/'scripts/unreal/exterior-neighbor-finish-materials.py').read_text())
  self.assertIn("('r','g')",(ROOT/'scripts/unreal/exterior-original-tree-materials.py').read_text())


if __name__=='__main__':unittest.main(verbosity=2)
