"""Meaningful CPU guard fixtures. No Unreal boot or synthetic native-success receipt."""
import ast
import copy
import importlib.util
from pathlib import Path
import types
import unittest

ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r30_test_native',ROOT/'scripts/unreal/exterior-garden-composition-native-r30.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n);g=n.guard


def control(rows):
 return {'rootIds':[r['id']for r in rows],'recoveredValues':[[r['positionCm'],[0.,0.,0.,1.],r['scale']]for r in rows],
  'storedMatrices':[[[float(i),0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[*r['positionCm'],1.]]for i,r in enumerate(rows)],
  'mainRandomSeed':1234,'numCustomDataFloats':0,'customData':[],
  'additionalRandomSeedsReadbackAvailable':False,'seedRangesReconstructed':False}


class Guards(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=g.load_source();r=g.read(g.BASE/g.old.REPORT);cls.witness=g.read(g.check_pin(r['savedActorWitness']))
  cls.groups=g.bind_groups(cls.source,{'witness':cls.witness});cls.controls={v['actor']:control(v['rows'])for v in cls.groups.values()}
  cls.content=g.read(g.check_pin(r['afterContentInventory']))

 def test_01_actual_source_and_native_garden_mapping(self):
  self.assertEqual((len(self.source['placements']),len(self.source['retained']),len(self.groups)),(38,435,19))
  self.assertEqual(sum(m['triangles']for m in self.source['models'].values()),4478)
  self.assertEqual(sum(len(v['rows'])for v in self.groups.values()),473)

 def test_02_export_preserves_all_original_normals_uv_indices(self):
  producer=g.module('r30_fixture_original_decoder',self.source['draft']['producer']['path']);_,models=producer.source_models()
  proof=producer.decode_export(Path(g.check_pin(self.source['draft']['glb'])).read_bytes(),models)
  self.assertTrue(proof['originalNormalUvIndexBytesExact']);self.assertFalse(proof['sourceTangentsInvented'])

 def test_03_changed_uv_bytes_rejected(self):
  producer=g.module('r30_fixture_uv_decoder',self.source['draft']['producer']['path']);_,models=producer.source_models()
  raw=bytearray(Path(g.check_pin(self.source['draft']['glb'])).read_bytes());import json,struct
  length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);a=doc['accessors'][doc['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0']]
  offset=28+length+doc['bufferViews'][a['bufferView']]['byteOffset'];raw[offset]^=1
  with self.assertRaises(RuntimeError):producer.decode_export(bytes(raw),models)

 def test_04_reversed_original_winding_rejected(self):
  producer=g.module('r30_fixture_winding_decoder',self.source['draft']['producer']['path']);_,models=producer.source_models()
  raw=bytearray(Path(g.check_pin(self.source['draft']['glb'])).read_bytes());import json,struct
  length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);a=doc['accessors'][doc['meshes'][0]['primitives'][0]['indices']]
  offset=28+length+doc['bufferViews'][a['bufferView']]['byteOffset'];size={5123:2,5125:4}[a['componentType']]
  raw[offset+size:offset+3*size]=raw[offset+2*size:offset+3*size]+raw[offset+size:offset+2*size]
  with self.assertRaises(RuntimeError):producer.decode_export(bytes(raw),models)

 def test_05_forced_swap_removal_then_original_survivor_order(self):
  for f in self.source['proposal']['sourceGroupFilters']:
   rows=self.groups[f['groupId']]['rows'];order=g.swap_remove_order(len(rows),f['removeSourceOrderedIndices'])
   keep=[i for i in range(len(rows))if i not in f['removeSourceOrderedIndices']]
   self.assertEqual(set(order),set(keep));self.assertEqual([order[order.index(i)]for i in keep],keep)
   self.assertEqual(len(keep),f['retainedRows'])

 def test_06_duplicate_or_out_of_range_indices_rejected(self):
  for indices in [[3,3],[-1],[80],[4,3]]:
   with self.assertRaises(RuntimeError):g.swap_remove_order(80,indices)

 def test_07_survivor_control_fields_stay_exact(self):
  f=self.source['proposal']['sourceGroupFilters'][0];c=self.controls[self.groups[f['groupId']]['actor']];kept=g.expected_control(c,f['removeSourceOrderedIndices'])
  self.assertEqual((len(kept['rootIds']),kept['mainRandomSeed'],kept['customData']),(58,1234,[]))
  self.assertEqual(kept['storedMatrices'],[v for i,v in enumerate(c['storedMatrices'])if i not in f['removeSourceOrderedIndices']])
  self.assertEqual(c['rootIds'],[r['id']for r in self.groups[f['groupId']]['rows']])

 def test_08_unreviewed_custom_or_seed_reconstruction_rejected(self):
  c=control(self.source['garden']['gardenDetailPlacements'][:3])
  for key,value in [('numCustomDataFloats',1),('customData',[.5]),('seedRangesReconstructed',True),('additionalRandomSeedsReadbackAvailable',True)]:
   changed=copy.deepcopy(c);changed[key]=value
   with self.assertRaises(RuntimeError):g.expected_control(changed,[0])

 def test_09_exact_four_original_component_delta_only(self):
  result=g.expected_original(self.witness,self.groups,self.controls,self.source['proposal'])
  changed={k for k in self.witness if result[k]!=self.witness[k]}
  affected={self.groups[f['groupId']]['actor']for f in self.source['proposal']['sourceGroupFilters']+self.source['proposal']['wholeOneMemberHeroGroupRetirements']}
  self.assertEqual(changed,affected);self.assertEqual(len(changed),4);self.assertEqual(len(result),5351)
  self.assertEqual(self.witness[self.groups[self.source['proposal']['wholeOneMemberHeroGroupRetirements'][0]['groupId']]['actor']]['components'][0]['instanceCount'],1)

 def test_10_namespace_and_map_only_content_delta(self):
  packages=g.package_paths(self.source['models'])+[g.PREFIX+'/Material'+str(i)for i in range(10)]
  after=copy.deepcopy(self.content);after['Brezi/Maps/Brezi.umap']={'sha256':'candidate-map','bytes':1}
  for p in packages:after[p.removeprefix('/Game/')+'.uasset']={'sha256':'new-own-fixture','bytes':1}
  self.assertEqual(g.validate_content(self.content,after,packages)['newPackages'],18)
  for key in ['Data/viewpoints.json',next(k for k in self.content if k.endswith('.uasset'))]:
   bad=copy.deepcopy(after);bad[key]={'sha256':'changed-original','bytes':1}
   with self.assertRaises(RuntimeError):g.validate_content(self.content,bad,packages)
  bad=copy.deepcopy(after);bad['Foreign/Unlisted.uasset']={'sha256':'foreign','bytes':1}
  with self.assertRaises(RuntimeError):g.validate_content(self.content,bad,packages)

 def test_11_retained_path_has_no_transform_or_seed_setters(self):
  tree=ast.parse((ROOT/n.OWNER).read_text());function=next(v for v in tree.body if isinstance(v,ast.FunctionDef)and v.name=='filter_original')
  calls=[v for v in ast.walk(function)if isinstance(v,ast.Call)and isinstance(v.func,ast.Attribute)]
  self.assertFalse(any(v.func.attr in ['update_instance_transform','add_instance','add_instances']for v in calls))
  properties=[v.args[0].value for v in calls if v.func.attr=='set_editor_property'and isinstance(v.args[0],ast.Constant)]
  self.assertEqual(properties,['per_instance_sm_data'])

 def test_12_full_f32_native_mesh_guard_accepts_original_rejects_flip(self):
  row=self.source['models']['fern_02_a'];flip=[False]
  class Desc:
   def get_triangle_count(self):return row['triangles']
   def get_triangle_vertex_instance(self,tid,corner):return row['indices'][tid.id_value*3+([0,2,1][corner]if flip[0]else corner)]
   def get_vertex_instance_vertex(self,vi):return vi
   def get_vertex_position(self,i):return types.SimpleNamespace(**dict(zip('xyz',row['expectedNativeVerticesCm'][i])))
   def get_vertex_instance_uv(self,i,channel):return types.SimpleNamespace(**dict(zip('xy',row['uv0'][i])))
  settings={'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}
  mesh=types.SimpleNamespace(get_num_lods=lambda:1,get_editor_property=lambda k:[]if k=='static_materials'else False,
   get_static_mesh_description=lambda lod:Desc(),get_num_triangles=lambda lod:row['triangles'],get_num_sections=lambda lod:1,get_path_name=lambda:'source-fixture-only')
  mesh.get_editor_property=lambda k:[None]if k=='static_materials'else False
  subsystem=types.SimpleNamespace(get_lod_build_settings=lambda m,l:types.SimpleNamespace(get_editor_property=lambda k:settings[k]))
  u=types.SimpleNamespace(StaticMeshEditorSubsystem=object,get_editor_subsystem=lambda c:subsystem,TriangleID=lambda **kw:types.SimpleNamespace(**kw))
  proof=n.mesh_proof(u,mesh,row,subsystem);self.assertTrue(proof['fullOrderedNativeF32PositionUV0WindingVerified'])
  flip[0]=True
  with self.assertRaises(RuntimeError):n.mesh_proof(u,mesh,row,subsystem)


if __name__=='__main__':unittest.main(verbosity=2)
