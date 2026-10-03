"""CPU API/schema fixtures; fake reflection is not native Periwinkle evidence.

The actual saved R34 source packet is loaded once. Twelve frozen stdlib guard
fixtures then share that packet, while actual UE import/readback remains pending.
"""
import copy
import importlib.util
import math
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r36_native_api_fixture',ROOT/'scripts/unreal/exterior-garden-periwinkle-native-r36-r2.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
g=n.guard
s=importlib.util.spec_from_file_location('r36_frozen_historical_label_boundary',ROOT/'scripts/unreal/exterior-garden-periwinkle-native-r36.py')
historical=importlib.util.module_from_spec(s);s.loader.exec_module(historical)

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
 def get_class(self):return NS(get_path_name=lambda:'/Script/Engine.StaticMesh')
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

 def test_06_historical_node_label_route_not_current_acceptance(self):
  found,proof=historical.imported_node_bindings(NS(StaticMeshComponent=object),self.b['source'],self.node_actors())
  self.assertEqual(set(found),set(self.b['source']['models']));self.assertTrue(all(r['meshNameUsedForSourceIdentity']is False for r in proof))
  self.assertEqual({r['originalProviderMeshName']for r in proof},{'tree','tree.001','tree.002','tree.003','tree.004','tree.048'})

 def test_07_historical_failed_label_boundary_retained(self):
  for label in ('foreign',g.MODELS[1]):
   rows=self.node_actors();rows[0].get_actor_label=lambda:label
   with self.assertRaises(RuntimeError):historical.imported_node_bindings(NS(StaticMeshComponent=object),self.b['source'],rows)

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

 def identity_api(self):
  return NS(ActorComponent='all',StaticMeshComponent='static',PrimitiveComponent='primitive',SceneComponent='scene',TriangleID=lambda id_value:NS(id_value=id_value))

 def identity_actors(self,container=True):
  values=[]
  def part(path,klass,mesh=None):
   return NS(get_path_name=lambda:path,get_class=lambda:NS(get_path_name=lambda:klass),get_name=lambda:path.rsplit('/',1)[-1],get_editor_property=lambda k:mesh)
  def actor(path,label,klass,parts,statics,primitives,scenes,parent=None,pose=None):
   mapping={'all':parts,'static':statics,'primitive':primitives,'scene':scenes}
   return NS(get_path_name=lambda:path,get_actor_label=lambda:label,get_class=lambda:NS(get_path_name=lambda:klass),
    get_components_by_class=lambda cls:list(mapping[cls]),get_actor_transform=lambda:Transform(pose),get_attach_parent_actor=lambda:parent)
  root=None
  if container:
   c=part('/Fixture/root/Root','/Script/Engine.SceneComponent')
   root=actor('/Fixture/root','Arbitrary container observation','/Script/Engine.Actor',[c],[],[],[c]);values.append(root)
  for index,row in enumerate(self.b['source']['models'].values()):
   mesh=Mesh(row);c=part('/Fixture/mesh'+str(index)+'/Mesh','/Script/Engine.StaticMeshComponent',mesh)
   values.append(actor('/Fixture/mesh'+str(index),'Unrelated observed label '+str(index),'/Script/Engine.StaticMeshActor',[c],[c],[c],[c],root))
  return values

 def identity(self,actors):
  u=self.identity_api();inventory=n.temporary_inventory(u,actors,{'tree':NS(transform_value=frame)})
  return n.geometry_identity_bindings(u,self.b['source'],actors,inventory),inventory

 def test_13_six_full_geometry_identities_ignore_all_observed_labels_with_container(self):
  (found,proof,containers),inventory=self.identity(self.identity_actors())
  self.assertEqual(set(found),set(g.MODELS));self.assertEqual(sum(p['triangles']for p in proof),34350)
  self.assertEqual(len(containers),1);self.assertEqual(inventory['actorCount'],7)
  self.assertTrue(all(p['uniqueTriangleCountUsedOnlyForCandidateRouting']and p['fullOrderedNativeF32PositionUV0UV1WindingVerified']for p in proof))
  self.assertTrue(all(p['actorLabelUsedForSourceIdentity']is False for p in proof))
  self.assertFalse(inventory['sourceMeshIdentityVerifiedAtThisCheckpoint'])
  self.assertEqual(len(self.identity(self.identity_actors(False))[0][0]),6)

 def test_14_count_routing_never_accepts_winding_uv1_section_or_duplicate(self):
  r=self.b['source']['models'][g.MODELS[0]]
  for kw in ({'reverse':True},{'uv1delta':.001},{'section':1}):
   with self.assertRaises(RuntimeError):n.imported_corner_identity(self.identity_api(),Mesh(r,**kw),r)
  rows=self.identity_actors(False)
  rows[0].get_components_by_class=lambda cls:rows[1].get_components_by_class(cls)
  with self.assertRaises(RuntimeError):self.identity(rows)

 def test_15_only_closed_identity_nonrendering_new_container_and_parents_allowed(self):
  for kind in ('class','pose','primitive','two-containers','external-parent','mesh-parent'):
   rows=self.identity_actors();root=rows[0]
   if kind=='class':root.get_class=lambda:NS(get_path_name=lambda:'/Script/Engine.PointLight')
   elif kind=='pose':root.get_actor_transform=lambda:Transform([[1.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]])
   elif kind=='primitive':
    previous=root.get_components_by_class;root.get_components_by_class=lambda cls:previous('scene')if cls=='primitive'else previous(cls)
   elif kind=='two-containers':
    other=copy.copy(root);other.get_path_name=lambda:'/Fixture/other';rows.append(other)
   elif kind=='external-parent':rows[1].get_attach_parent_actor=lambda:NS(get_path_name=lambda:'/Original/Existing')
   else:rows[1].get_attach_parent_actor=lambda:rows[2]
   with self.assertRaises(RuntimeError):self.identity(rows)

 def test_16_actual_import_checkpoint_precedes_false_import_and_unknown_actor_gates(self):
  class Pipeline:
   def get_editor_property(self,key):return self
   def set_editor_property(self,key,value):pass
   def get_path_name(self):return n.PREFIX+'/Pipeline/Fixture'
  class Parameters:
   def set_editor_property(self,key,value):pass
  for imported in (False,True):
   rows=self.identity_actors();rows[0].get_class=lambda:NS(get_path_name=lambda:'/Script/Engine.PointLight')
   api=self.identity_api();system=object();level=NS(get_current_level=lambda:object())
   api.EditorActorSubsystem='actors';api.LevelEditorSubsystem='level';api.get_editor_subsystem=lambda cls:system if cls=='actors'else level
   api.EditorAssetLibrary=NS(does_asset_exist=lambda p:False,duplicate_asset=lambda a,b:Pipeline())
   api.InterchangeCombineStaticMeshesBehavior=NS(DO_NOT_COMBINE=0);api.InterchangeSceneHierarchyType=NS(CREATE_LEVEL_ACTORS=0)
   api.ImportAssetParameters=Parameters;api.SoftObjectPath=lambda p:p
   api.InterchangeManager=NS(get_interchange_manager_scripted=lambda:NS(import_scene=lambda *a:imported,create_source_data=lambda p:p))
   h={'tree':NS(transform_value=frame),'meshHelper':NS(static_mesh_subsystem=lambda u:object(),finish_static_mesh_compilation=lambda u,synchronous:None)}
   with tempfile.TemporaryDirectory()as directory,patch.object(n,'actors',side_effect=[{}, {a.get_path_name():a for a in rows}]):
    checkpoint=Path(directory)
    with self.assertRaises(RuntimeError):n.import_geometry(api,self.b,{self.b['source']['recipe']['key']:object()},h,checkpoint)
    receipt=g.read(checkpoint/'import-temporary-actors-before-binding.json')
    self.assertEqual(receipt['actorCount'],7);self.assertEqual(receipt['actors'][0]['class'],'/Script/Engine.PointLight')
    self.assertFalse(receipt['sourceMeshIdentityVerifiedAtThisCheckpoint'])

 def test_17_mutation_measurement_and_saved_geometry_kernels_ast_exact_frozen_r1(self):
  import ast
  old=ast.parse((ROOT/historical.OWNER).read_text());new=ast.parse((ROOT/n.OWNER).read_text())
  names=('garden_controls','old_controls','measure','clear_original','apply_new','verify_new','mesh_proof','material_contract')
  def bodies(tree):return {v.name:ast.dump(v,include_attributes=False)for v in tree.body if isinstance(v,ast.FunctionDef)and v.name in names}
  self.assertEqual(bodies(old),bodies(new))
  self.assertEqual(g.import_identity_evidence()['failedNativeProcess']['exitCode'],255)
  self.assertFalse(g.import_identity_evidence()['persistedPartialMeshDiagnosticAvailable'])


def load_tests(loader,tests,pattern):
 path=ROOT/'scripts/unreal/test_exterior_garden_periwinkle_native_guards_r36_r2.py'
 spec=importlib.util.spec_from_file_location('r36_combined_guard_fixtures',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 @classmethod
 def reuse_actual_bundle(cls):cls.b=NativeRoutes.b;cls.m=module.fixtures(cls.b)
 module.Guards.setUpClass=reuse_actual_bundle
 tests.addTests(loader.loadTestsFromTestCase(module.Guards));return tests

if __name__=='__main__':unittest.main(verbosity=2)
