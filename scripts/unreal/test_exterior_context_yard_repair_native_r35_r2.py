"""CPU source/schema fixtures; these are not Unreal execution evidence."""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
n=load('r35_new_native_fixture','exterior-context-yard-repair-native-r35-r2.py')
g=n.guard

def actual_source_fixture():
 proposal=g.read(g.PROPOSAL);report=g.checked(proposal['actualNativeBase']);witness=g.checked(report['savedActorWitness'])
 ecology=g.read(ROOT/'output/unreal/exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json');source={v['id']:v for v in ecology['groups']}
 groups={}
 for row in proposal['repairAOriginalEcologyRetirements']['affectedGroups']:
  c=g.component(witness[row['actor']],row['component'])
  groups[row['groupId']]={**row,'sourceRows':source[row['groupId']]['instances'],'originalWitness':witness[row['actor']],'mesh':c['mesh'],'componentName':c['name']}
 decoded=g.decode_ecology(ROOT/'output/unreal/exterior-canopy-ecology-20260930-r3/canopy-ecology.glb',{v['modelId']for v in groups.values()})
 return {'ecologyGroups':groups,'ecologySourceModels':decoded,'base':{'report':report,'witness':witness},'backdropTarget':proposal['repairCSingleBackdropNearPbr']}

def v(values):return NS(**dict(zip('xyzw',values)))
class Description:
 def __init__(self,lod,bad):self.lod,self.bad=lod,bad
 def get_triangle_count(self):return len(self.lod['corners'])
 def get_triangle_polygon_group(self,t):return NS(id_value=self.lod['sections'][t.id_value]+(1 if self.bad=='section'and t.id_value==0 else 0))
 def get_triangle_vertex_instance(self,t,k):return (t.id_value,k)
 def get_vertex_instance_vertex(self,vi):return vi
 def corner(self,vi):
  t,k=vi;return self.lod['corners'][t][(2-k if self.bad=='winding'and t==0 else k)]
 def get_vertex_position(self,vi):return v(self.corner(vi)[:3])
 def get_vertex_instance_uv(self,vi,channel):
  values=list(self.corner(vi)[3+2*channel:5+2*channel])
  if self.bad=='uv'and vi==(0,0)and channel==1:values[0]=values[0]+.125
  return v(values)
class Mesh:
 def __init__(self,source,bad=None):self.source,self.bad=source,bad
 def get_num_lods(self):return 3
 def get_num_triangles(self,level):return len(self.source['lods'][level]['corners'])
 def get_num_sections(self,level):return len(self.source['materials'])
 def get_editor_property(self,key):
  if key=='static_materials':return list(range(len(self.source['materials'])))
  raise AssertionError(key)
 def get_material(self,index):return NS(get_path_name=lambda:self.source['materials'][index])
 def get_static_mesh_description(self,level):return Description(self.source['lods'][level],self.bad)

class NativeSourceFixtures(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.bundle=actual_source_fixture();cls.expected=n.ecology_expected_geometry(cls.bundle)
 def api(self,bad=None):
  meshes={v['mesh']:Mesh(v,bad)for v in self.expected.values()}
  return NS(EditorAssetLibrary=NS(load_asset=lambda p:meshes[p]),TriangleID=lambda id_value:NS(id_value=id_value))
 def test_actual_eight_model_three_lod_shape_and_bound_native_assets(self):
  self.assertEqual(len(self.expected),8)
  self.assertEqual(sum(len(l['corners'])for v in self.expected.values()for l in v['lods']),5220)
  result=n.native_ecology_geometry(self.api(),self.bundle,{})
  self.assertEqual(len(result),8)
  self.assertTrue(all(v['nativeNormalTangentReadbackAvailable']is False for v in result.values()))
 def test_section_uv_and_winding_mutations_reject(self):
  for bad in ('section','uv','winding'):
   with self.subTest(bad=bad),self.assertRaises(RuntimeError):n.native_ecology_geometry(self.api(bad),self.bundle,{})
 def test_actual_source_rows_have_index_identity_without_invented_authored_id(self):
  for identity,row in self.bundle['ecologyGroups'].items():
   self.assertTrue(all('id'not in r for r in row['sourceRows']))
   self.assertEqual(row['originalInstances'],len(row['sourceRows']))
   self.assertEqual(len({identity+':'+str(i)for i in range(row['originalInstances'])}),row['originalInstances'])
 def test_conflicting_native_master_binding_rejects(self):
  altered=copy.deepcopy(self.bundle);key=next(iter(altered['ecologyGroups']));row=copy.deepcopy(altered['ecologyGroups'][key]);row['mesh']+='_foreign'
  altered['ecologyGroups']['foreign_group']=row
  with self.assertRaises(RuntimeError):n.ecology_expected_geometry(altered)
 def test_actual_floor_and_backdrop_binding_field_contract(self):
  report=self.bundle['base']['report'];witness=self.bundle['base']['witness'];targets={}
  for role in ('entry_walk','service_court'):
   row=report['targets'][role];c=g.component(witness[row['actor']],row['component'])
   self.assertNotEqual(row['originalMesh'],c['mesh'])
   targets[role]={**row,'currentMesh':c['mesh'],'currentMaterials':c['materials'],'currentOverrides':c['overrideMaterials']}
  calls=[]
  class C:
   def __init__(self,row):self.row=row
   def get_editor_property(self,key):
    self.assertion=key;return NS(get_path_name=lambda:self.row['currentMesh'])
   def get_num_materials(self):return len(self.row['currentMaterials'])
   def get_material(self,i):return NS(get_path_name=lambda:self.row['currentMaterials'][i])
   def set_static_mesh(self,mesh):calls.append(('mesh',self.row['actor'],mesh));return True
   def set_material(self,i,material):calls.append(('material',i,material))
  lookup={v['actor']:C(v)for v in targets.values()};back=self.bundle['backdropTarget'];lookup[back['actualActor']]=C({'actor':back['actualActor']})
  h={'cleanNative':NS(component_lookup=lambda u,a,c:lookup[a])}
  n.apply_bindings(None,{'floorTargets':targets,'backdropTarget':back},h,{k:'new:'+k for k in targets},'new:material')
  self.assertEqual(len(calls),3);self.assertEqual(calls[-1],('material',0,'new:material'))

class DependencyRouteFixtures(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  r32=n.module('r35_r2_actual_saved_source_fixture','exterior-context-yard-ground-native-r32.py')
  cls.source_plan,cls.packet=r32.guard.validate_plan()
  cls.report=g.read(ROOT/'output/unreal/exterior-20261002-r32a/context-yard-ground-native-report.json')
  cls.witness=g.checked(cls.report['savedActorWitness']);cls.old=g.checked(cls.report['originalControlsSaved'])
  cls.bundle={'base':{'sourceBundle':cls.packet,'report':cls.report,'witness':cls.witness}}
  cls.frames={}
  for folder,name in [('exterior-20261002-r28b','context-yard-native-report-r2.json'),('exterior-20261002-r32a','context-yard-ground-native-report.json')]:
   report=g.read(ROOT/'output/unreal'/folder/name);measured=g.checked(report['nativeSourceFrameMeasurements'])
   for model,row in measured.items():
    identity=('EX_context_yard_r28_' if folder.endswith('r28b') else 'EX_yard_ground_r32_')+model
    cls.frames[report['addedActors'][identity]]=row
 def fake_api(self,bad_old=False,bad_yard=False):
  components={};source=n.read(self.report['originalControlsSaved']['path']);calls=[]
  def transform(v):return NS(translation=NS(**dict(zip('xyz',v[0]))),rotation=NS(**dict(zip('xyzw',v[1]))),scale3d=NS(**dict(zip('xyz',v[2]))))
  for actor,row in self.frames.items():
   stored=row['actualMatrices'];frames=row['recoveredValues'];witness=self.witness[actor]['components'][0]
   class Component:
    def __init__(self,stored,frames,witness):self.stored,self.frames,self.witness=stored,frames,witness
    def get_instance_count(self):return len(self.frames)
    def get_editor_property(self,key):
     if key=='instancing_random_seed':return 17 # Fixture seed; native scene witness does not expose it.
     if key=='num_custom_data_floats':return 0
     if key=='per_instance_sm_custom_data':return []
     if key=='per_instance_sm_data':return [NS(get_editor_property=lambda key,m=m:NS(**{k:v(p)for k,p in zip(('x_plane','y_plane','z_plane','w_plane'),m)}))for m in self.stored]
     raise AssertionError(key)
   components[actor]=Component(stored,copy.deepcopy(frames),witness)
  if bad_yard:next(iter(components.values())).frames[0][0][0]+=.01
  base=copy.copy(self.bundle['base']);base['native']=NS(all_controls=lambda u,parent,h,witness:(calls.append(('parent',parent)),({'different':True} if bad_old else self.old))[1])
  h={'cleanNative':NS(component_lookup=lambda u,a,c:components[a]),'rural':NS(instance_value=lambda c,i:transform(c.frames[i]))}
  assets=NS(load_asset=lambda path:(calls.append(('asset',path)),NS(get_path_name=lambda:path))[1])
  def verify(u,h,recipes,originals,receipt):
   self.assertEqual(recipes,self.packet['source']['recipes']);self.assertEqual(set(originals),{'context_track','context_garden_soil'})
   self.assertEqual(receipt,self.report['newMaterialReport']);calls.append(('recipes',recipes));return {}
  return NS(EditorAssetLibrary=assets),{'base':base},h,NS(verify_saved=verify),calls
 def test_complete_base_controls_real_r32_packet_and_six_recorded_yard_groups(self):
  api,bundle,h,maps,calls=self.fake_api()
  with patch.object(n,'module',return_value=maps):result=n.base_controls(api,bundle,h,self.witness)
  self.assertIs(calls[0][1],self.packet['base'])
  self.assertEqual(result['actualOriginalR32Controls'],self.old)
  self.assertEqual(len(result['all13YardShrubsAnd1274LowRootsRawControls']),6)
  self.assertEqual(sum(r['instanceCount']for r in result['all13YardShrubsAnd1274LowRootsRawControls'].values()),1287)
  self.assertEqual([c[0]for c in calls],['parent','asset','asset','recipes'])
 def test_parent_control_and_yard_pose_changes_reject(self):
  for flag in ('old','yard'):
   api,bundle,h,maps,calls=self.fake_api(bad_old=flag=='old',bad_yard=flag=='yard')
   with self.subTest(flag=flag),patch.object(n,'module',return_value=maps),self.assertRaises(RuntimeError):n.base_controls(api,bundle,h,self.witness)
 def test_flat_recipe_foreign_recipe_and_failed_owner_reject(self):
  packet=copy.copy(self.packet);packet.pop('source');packet['recipes']=self.packet['source']['recipes']
  with self.assertRaises(RuntimeError):n.base_material_contract({'base':{'sourceBundle':packet}})
  packet=copy.copy(self.packet);packet['source']=copy.copy(packet['source']);packet['source']['recipes']=copy.deepcopy(packet['source']['recipes']);packet['source']['recipes'][0]['id']='foreign'
  with self.assertRaises(RuntimeError):n.base_material_contract({'base':{'sourceBundle':packet}})
  self.assertEqual(n.prior_failed_attempt()['report']['sha256'],'f7c4af362f1056e923391c6c72af50280a9dbfe519e3d2005efe32b099f5510c')

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(NativeSourceFixtures)
 suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(DependencyRouteFixtures))
 for file in ('test_exterior_context_yard_repair_materials_r35.py',):
  path=ROOT/'scripts/unreal'/file
  if not path.is_file():raise RuntimeError('Required final owned fixture missing: '+str(path))
  suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(load(file[:-3],file)))
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 raise SystemExit(not result.wasSuccessful())
