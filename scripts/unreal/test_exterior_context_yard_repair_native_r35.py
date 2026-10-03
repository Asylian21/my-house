"""CPU source/schema fixtures; these are not Unreal execution evidence."""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

ROOT=Path(__file__).resolve().parents[2]
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
n=load('r35_new_native_fixture','exterior-context-yard-repair-native-r35.py')
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

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(NativeSourceFixtures)
 for file in ('test_exterior_context_yard_repair_materials_r35.py','test_exterior_context_yard_repair_guards_r35.py'):
  path=ROOT/'scripts/unreal'/file
  if not path.is_file():raise RuntimeError('Required final owned fixture missing: '+str(path))
  suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(load(file[:-3],file)))
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 raise SystemExit(not result.wasSuccessful())
