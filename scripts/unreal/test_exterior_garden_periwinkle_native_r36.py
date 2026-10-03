"""CPU API/schema fixtures; fake reflection is not native Periwinkle evidence.

The actual saved R34 source packet is loaded once. Twelve frozen stdlib guard
fixtures then share that packet, while actual UE import/readback remains pending.
"""
import copy
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r36_native_api_fixture',ROOT/'scripts/unreal/exterior-garden-periwinkle-native-r36.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
g=n.guard

class Value:
 def __init__(self,*v):self.v=list(v)
 def __getattr__(self,k):
  if k not in ('x','y','z','w'):raise AttributeError(k)
  return self.v['xyzw'.index(k)]
 def get_editor_property(self,k):return getattr(self,k)
 def set_editor_property(self,k,v):self.v['xyzw'.index(k)]=v

class Transform:
 def __init__(self,v=None):
  v=v or [[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]]
  self.translation,self.rotation,self.scale3d=[Value(*r)for r in v]
 def get_editor_property(self,k):return getattr(self,k)
 def set_editor_property(self,k,v):setattr(self,k,copy.deepcopy(v))

def frame(t):return [list(t.translation.v),list(t.rotation.v),list(t.scale3d.v)]

def matrix(t):
 p,q,ss=frame(t);x,y,z,w=q;scale=ss[0]
 return [[scale*(1-2*(y*y+z*z)),scale*2*(x*y+z*w),scale*2*(x*z-y*w),0.],
  [scale*2*(x*y-z*w),scale*(1-2*(x*x+z*z)),scale*2*(y*z+x*w),0.],
  [scale*2*(x*z+y*w),scale*2*(y*z-x*w),scale*(1-2*(x*x+y*y)),0.],p+[1.]]

class Component:
 def __init__(self,controls=None):
  self.controls=copy.deepcopy(controls or {'rootIds':[],'recoveredValues':[],'storedMatrices':[], 'mainRandomSeed':17,'numCustomDataFloats':0,'customData':[]})
  self.transforms=[Transform(v)for v in self.controls['recoveredValues']];self.sync=0
 def get_path_name(self):return '/Engine/Transient.FixtureHISM'
 def get_instance_count(self):return len(self.transforms)
 def get_editor_property(self,k):
  return {'static_mesh':None,'instancing_random_seed':self.controls['mainRandomSeed'],'num_custom_data_floats':self.controls['numCustomDataFloats'],'per_instance_sm_custom_data':self.controls['customData']}[k]
 def add_instance(self,t,world):self.transforms.append(copy.deepcopy(t));return len(self.transforms)-1
 def clear_instances(self):self.transforms=[]
 def get_owner(self):return self
 def synchronize_instance_bounds(self):self.sync+=1

class Description:
 def __init__(self,row,reverse=False,uv1delta=0.,section=0):self.row,self.reverse,self.uv1delta,self.section=row,reverse,uv1delta,section
 def get_triangle_count(self):return self.row['triangles']
 def get_triangle_polygon_group(self,t):return NS(id_value=self.section)
 def get_triangle_vertex_instance(self,t,c):
  face=self.row['indices'][t.id_value*3:t.id_value*3+3]
  if self.reverse:face=[face[0],face[2],face[1]]
  return face[c]
 def get_vertex_instance_vertex(self,i):return i
 def get_vertex_position(self,i):return Value(*self.row['expectedNativeVerticesCm'][i])
 def get_vertex_instance_uv(self,i,ch):
  v=list(self.row['uv0'if ch==0 else'uv1'][i]);v[0]+=self.uv1delta if ch==1 else 0.;return Value(*v)

class Mesh:
 def __init__(self,row,**kw):self.row,self.d=row,Description(row,**kw)
 def get_path_name(self):return n.PREFIX+'/Geometry/StaticMeshes/'+self.row['exportName']+'.'+self.row['exportName']
 def get_num_lods(self):return 1
 def get_editor_property(self,k):return {'static_materials':[1],'has_navigation_data':False}[k]
 def get_static_mesh_description(self,l):return self.d
 def get_num_triangles(self,l):return self.row['triangles']
 def get_num_sections(self,l):return 1

class NativeRoutes(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.b=g.validate_source()
 def facade(self):
  components={actor:Component(c)for actor,c in self.b['originalControls'].items()}
  tree=NS(transform_value=frame,instance_value=lambda c,i:copy.deepcopy(c.transforms[i]),matrix=lambda c,i:c.controls['storedMatrices'][i]if c.controls['storedMatrices']else matrix(c.transforms[i]))
  return components,{'tree':tree,'cleanNative':NS(component_lookup=lambda u,a,c:components[a])}
 def api(self):return NS(HierarchicalInstancedStaticMeshComponent=Component,Transform=Transform,Vector=Value,new_object=lambda cls:cls())
 def proof_api(self):return NS(TriangleID=lambda id_value:NS(id_value=id_value))
 def subsystem(self):
  settings={'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}
  return NS(get_lod_build_settings=lambda m,l:NS(get_editor_property=lambda k:settings[k]))

 def test_01_actual_four_key_helper_delegate(self):
  b=self.b['base'];self.assertEqual(set(b['bundle']),{'source','base','groups','reference'})
  h=n.helpers(b);self.assertIn('moduleOrderWitness',h);self.assertIn('tree',h);self.assertIn('existing',h)

 def test_02_wrong_base_packet_rejected(self):
  b=dict(self.b['base']);b['bundle']={k:v for k,v in b['bundle'].items()if k!='reference'}
  with self.assertRaises(RuntimeError):n.helpers(b)

 def test_03_original_recipe_model_dictionary_key(self):
  key=self.b['source']['recipe']['key'];self.assertEqual(key,'ph_original_periwinkle_r36')
  self.assertEqual(n.material_contract(self.b['source'],{key:object()}).keys(),{key})
  with self.assertRaises(RuntimeError):n.material_contract(self.b['source'],{'periwinkle':object()})

 def test_04_full_six_mesh_corner_route(self):
  rows=[n.mesh_proof(self.proof_api(),Mesh(r),r,self.subsystem())for r in self.b['source']['models'].values()]
  self.assertEqual(sum(r['triangles']for r in rows),34350)
  self.assertTrue(all(r['fullOrderedNativeF32PositionUV0UV1WindingVerified']for r in rows));self.assertFalse(any(r['nativeColor0Color1ReadbackAvailable']for r in rows))

 def test_05_wrong_native_winding_uv1_and_section_rejected(self):
  r=next(iter(self.b['source']['models'].values()))
  for kw in ({'reverse':True},{'uv1delta':.001},{'section':1}):
   with self.assertRaises(RuntimeError):n.mesh_proof(self.proof_api(),Mesh(r,**kw),r,self.subsystem())

 def node_actors(self):
  actors=[]
  for i,(node,row)in enumerate(self.b['source']['models'].items()):
   mesh=NS(get_path_name=lambda name=row['originalSourceMeshName']:n.PREFIX+'/Geometry/'+name+'.'+name)
   c=NS(get_editor_property=lambda k,m=mesh:m)
   actors.append(NS(get_actor_label=lambda v=node:v,get_components_by_class=lambda u,v=c:[v],get_path_name=lambda j=i:'/Fixture/'+str(j)))
  return actors

 def test_06_node_actor_identity_ignores_foreign_mesh_names(self):
  found,proof=n.imported_node_bindings(NS(StaticMeshComponent=object),self.b['source'],self.node_actors())
  self.assertEqual(set(found),set(self.b['source']['models']));self.assertTrue(all(r['meshNameUsedForSourceIdentity']is False for r in proof))
  self.assertEqual({r['originalProviderMeshName']for r in proof},{'tree','tree.001','tree.002','tree.003','tree.004','tree.048'})

 def test_07_duplicate_unknown_source_node_rejected(self):
  for label in ('foreign',g.MODELS[1]):
   rows=self.node_actors();rows[0].get_actor_label=lambda:label
   with self.assertRaises(RuntimeError):n.imported_node_bindings(NS(StaticMeshComponent=object),self.b['source'],rows)

 def test_08_all384_actual_saved_frame_route_not_source_z_spelling(self):
  cs,h=self.facade();before={a:[frame(t)for t in c.transforms]for a,c in cs.items()}
  # Construct a one-ULP source annotation difference; actual384 frames remain
  # the immutable saved controls. This is a fixture, not observed R36 drift.
  b=dict(self.b);b['source']=dict(self.b['source']);b['source']['placements']=copy.deepcopy(self.b['source']['placements'])
  source=b['source']['placements'][0]['originalRow']['positionCm'];source[2]=math.nextafter(source[2],float('inf'))
  values,measurements=n.measure(self.api(),b,h)
  self.assertEqual(sum(len(v)for v in values.values()),384);self.assertTrue(g.validate_measurements(measurements,self.b))
  self.assertEqual(before,{a:[frame(t)for t in c.transforms]for a,c in cs.items()})
  byid={i:control['recoveredValues'][j]for control in self.b['originalControls'].values()for j,i in enumerate(control['rootIds'])}
  self.assertTrue(any(byid[r['rootId']][0][2]!=r['originalRow']['positionCm'][2]for r in b['source']['placements']))

 def test_09_wrong_actual_original_frame_rejected(self):
  cs,h=self.facade();group=next(iter(self.b['groups'].values()));cs[group['actor']].transforms[0].rotation.v[2]+=.001
  with self.assertRaises(RuntimeError):n.measure(self.api(),self.b,h)

 def test_10_whole_four_clear_no_retained_recomposition(self):
  cs,h=self.facade();proof=n.clear_original(None,self.b,h,self.b['originalControls'])
  self.assertEqual(sum(r['retiredRoots']for r in proof),384)
  for a,c in cs.items():self.assertEqual(c.get_instance_count(),0 if a in {v['actor']for v in self.b['groups'].values()}else len(self.b['originalControls'][a]['rootIds']))

 def test_11_partial_or_custom_component_clear_rejected(self):
  for kind in ('partial','custom'):
   cs,h=self.facade();a=next(iter(self.b['groups'].values()))['actor'];controls=copy.deepcopy(self.b['originalControls'])
   if kind=='partial':cs[a].transforms.pop()
   else:controls[a]['numCustomDataFloats']=1;controls[a]['customData']=[.2]
   with self.assertRaises(RuntimeError):n.clear_original(None,self.b,h,controls)

 def test_12_actual_old_controls_nested_packet_all36_fern_route(self):
  b=self.b;base=b['base'];old=base['native'];r=base['report'];cs={};scene=b['base']['witness']
  for model,row in r['newOwnedGroups'].items():
   m=b['oldFernMeasurements'][model];cs[row['actor']]=Component({'rootIds':m['rootIds'],'recoveredValues':m['recoveredValues'],'storedMatrices':m['storedMatrices'],'mainRandomSeed':17,'numCustomDataFloats':0,'customData':[]})
  h={'tree':NS(transform_value=frame,instance_value=lambda c,i:copy.deepcopy(c.transforms[i]),matrix=lambda c,i:c.controls['storedMatrices'][i]),
   'cleanNative':NS(component_lookup=lambda u,a,c:cs[a],original_grass_controls=lambda u,b:g.read(g.check_pin(r['originalGrassSaved']))),
   'cleanBundle':object(),'existing':NS(graph_snapshot=object())}
  fakeMaps=NS(verify_materials=lambda u,report,recipe,snap:object());fakeU=NS(EditorAssetLibrary=NS(load_asset=lambda p:object()))
  with patch.object(old,'old_materials',side_effect=lambda u,parent,hh:g.read(g.check_pin(r['originalMaterialsSaved']))),patch.object(old,'old_tree_controls',side_effect=lambda u,parent,hh:g.read(g.check_pin(r['originalTreesSaved']))),patch.object(old,'verify_new')as verify,patch.object(g,'module',return_value=fakeMaps):
   result=n.old_controls(fakeU,b,h,scene);verify.assert_called_once()
  self.assertEqual(sum(len(c['rootIds'])for c in result['preserved36FernControls'].values()),36)
  self.assertIs(b['reference'],base['bundle'])


def load_tests(loader,tests,pattern):
 path=ROOT/'scripts/unreal/test_exterior_garden_periwinkle_native_guards_r36.py'
 spec=importlib.util.spec_from_file_location('r36_combined_guard_fixtures',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 @classmethod
 def reuse_actual_bundle(cls):cls.b=NativeRoutes.b;cls.m=module.fixtures(cls.b)
 module.Guards.setUpClass=reuse_actual_bundle
 tests.addTests(loader.loadTestsFromTestCase(module.Guards));return tests

if __name__=='__main__':unittest.main(verbosity=2)
