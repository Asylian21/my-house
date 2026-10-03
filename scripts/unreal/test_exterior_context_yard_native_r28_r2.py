"""Focused stdlib source/native contract fixtures; no Unreal launch."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest

s=importlib.util.spec_from_file_location('r28_owned_native_fixture',Path(__file__).with_name('exterior-context-yard-native-r28-r2.py'))
n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
g=n.guard


class YardNativeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.bundle=g.load_source();cls.base=g.saved_base()
 def test_generated_r21_glb_full_decode(self):
  rows=n.decode_glb(g.check_pin(self.bundle['plan']['glb']),self.bundle['geometry']['meshes'])
  self.assertEqual(sum(r['triangles']for r in rows),2969);self.assertEqual(len(rows),4)
 def test_changed_source_uv_rejected(self):
  meshes=copy.deepcopy(self.bundle['geometry']['meshes']);meshes[0]['uv1'][0][0]=.5
  with self.assertRaises(RuntimeError):n.decode_glb(g.check_pin(self.bundle['plan']['glb']),meshes)
 def test_actual_rural_source_adapter_all13(self):
  rural=g.module('r28_fixture_actual_rural','rural-import.py')
  class Transform:
   def __init__(self):self.properties={}
   def set_editor_property(self,k,v):self.properties[k]=v
  class U:
   Vector=staticmethod(lambda *v:list(v))
   Quat=staticmethod(lambda *v:list(v))
  U.Transform=Transform
  for root in self.bundle['layout']['planting']:
   before=copy.deepcopy(root);t=rural.instance_transform(U,n.root_record(root)).properties
   self.assertEqual(root,before);self.assertEqual(t['translation'],root['positionCm']);self.assertEqual(t['scale3d'],[root['uniformScale']]*3)
   angle=math.radians(root['yawDegrees'])/2;self.assertEqual(t['rotation'],[0.,0.,math.sin(angle),math.cos(angle)])
 def test_signed_zero_frame_drift_rejected(self):
  with self.assertRaises(RuntimeError):n.exact([0.,1.],[-0.,1.],'signed-zero drift')
 def graph(self):
  original=copy.deepcopy(self.bundle['recipes'][0]['originalGraph'])
  source=self.base['materials']['foreground']['graph'];nodes=[copy.deepcopy(v)for v in source['nodes']if v['role'].startswith('BreziForegroundR21:')]
  nodes=json.loads(json.dumps(nodes).replace('BreziForegroundR21:',g.NODE_TAG));variant=copy.deepcopy(original);variant['nodes']+=nodes
  variant['roots']['OPACITY_MASK']=[g.NODE_TAG+'temporal-dither','Result'];variant['flags']['blend_mode']='<BlendMode.BLEND_MASKED: 1>';variant['flags']['opacity_mask_clip_value']=.5
  return original,variant
 def test_three_node_feather_preserves_original_pbr(self):
  original,variant=self.graph();g.validate_graph_copy(original,variant)
  variant['roots']['NORMAL']=[g.NODE_TAG+'uv1','']
  with self.assertRaises(RuntimeError):g.validate_graph_copy(original,variant)
 def test_source_content_scope_rejects_original_change(self):
  before=self.base['content'];after=copy.deepcopy(before);after['Brezi/Maps/Brezi.umap']={'sha256':'f'*64,'bytes':1}
  packages=['Brezi/ContextYard20261002R28/Test'+str(i)+'.uasset'for i in range(9)]
  after.update({key:{'sha256':'a'*64,'bytes':1}for key in packages});g.validate_content(before,after,packages)
  key=next(k for k in before if k.endswith('.uasset'));after[key]={'sha256':'e'*64,'bytes':1}
  with self.assertRaises(RuntimeError):g.validate_content(before,after,packages)
 def test_real_clean_base_not_old_regression(self):
  self.assertEqual(self.base['reportPin']['sha256'],g.BASE_SHA);self.assertEqual(len(self.base['witness']),5343)
  self.assertEqual(self.base['report']['excludedDonors'],['R20_CURVED_GRASS','R23_CREAM_ROOF'])


class YardApiRepairTests(unittest.TestCase):
 def function(self):
  import ast
  from types import SimpleNamespace
  source=(Path(__file__).with_name('lawn-geometry.py')).read_text();tree=ast.parse(source)
  node=next(v for v in tree.body if isinstance(v,ast.FunctionDef)and v.name=='static_mesh_subsystem')
  scope={'require':g.require};exec(compile(ast.Module(body=[node],type_ignores=[]),'<frozen-accessor-fixture>','exec'),scope)
  return scope['static_mesh_subsystem'],SimpleNamespace
 def test_none_subsystem_loads_module_then_retries(self):
  function,NS=self.function();events=[];result=object();loaded=[]
  def get(cls):
   events.append(cls);return object()if cls=='Asset'else(result if loaded else None)
  u=NS(StaticMeshEditorSubsystem='Static',AssetEditorSubsystem='Asset',get_editor_subsystem=get,load_module=lambda name:loaded.append(name))
  self.assertIs(function(u),result);self.assertEqual(loaded,['StaticMeshEditor']);self.assertEqual(events,['Static','Static','Asset'])
 def test_available_subsystem_is_not_reloaded(self):
  function,NS=self.function();result=object();loaded=[]
  u=NS(StaticMeshEditorSubsystem='Static',AssetEditorSubsystem='Asset',get_editor_subsystem=lambda cls:result,load_module=lambda name:loaded.append(name))
  self.assertIs(function(u),result);self.assertEqual(loaded,[])
 def test_missing_subsystem_or_dependency_rejected(self):
  function,NS=self.function()
  for missing in ('Static','Asset'):
   u=NS(StaticMeshEditorSubsystem='Static',AssetEditorSubsystem='Asset',get_editor_subsystem=lambda cls:None if cls==missing else object(),load_module=lambda name:None)
   with self.assertRaises(RuntimeError):function(u)
 def test_both_geometry_readbacks_use_only_proven_accessor(self):
  import ast
  tree=ast.parse(Path(__file__).with_name('exterior-context-yard-native-r28-r2.py').read_text())
  for name in ('native_mesh_proof','native_master_vertices'):
   node=next(v for v in tree.body if isinstance(v,ast.FunctionDef)and v.name==name);text=ast.unparse(node)
   self.assertIn('guard.static_mesh_api().static_mesh_subsystem(u)',text);self.assertNotIn('u.get_editor_subsystem(u.StaticMeshEditorSubsystem)',text)


if __name__=='__main__':unittest.main()
