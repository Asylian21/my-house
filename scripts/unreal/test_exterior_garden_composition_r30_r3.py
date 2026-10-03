"""Meaningful CPU guard fixtures. No Unreal boot or synthetic native-success receipt."""
import ast
import copy
import importlib.util
from pathlib import Path
import types
import unittest

ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r30_test_native',ROOT/'scripts/unreal/exterior-garden-composition-native-r30-r3.py')
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

 def test_13_exact_original_closed_solids_projected_partition(self):
  source=self.source['garden']['sourceStepTrianglesCm'];steps=g.step.validated_steps(source)
  self.assertEqual((len(steps['edges']),len(steps['triangles'])),(112,16))
  self.assertEqual(steps['policy']['sourceTriangles'],48);self.assertEqual(steps['policy']['zeroProjectedRawEdges'],32)
  mask=g.module('r30_r3_frozen_bed_rejection_fixture','exterior-garden-organic-native.py')
  with self.assertRaisesRegex(RuntimeError,'not a triangle union'):mask._boundary([t for rows in source.values()for t in rows])
  for fit in self.source['placements']:
   self.assertTrue(mask._boundary(self.source['garden']['sourceMulchTrianglesCm'][fit['sourceBedId']]))

 def test_14_all112_raw_edges_match_frozen_source_proposal_recipe(self):
  import math
  source=self.source['garden']['sourceStepTrianglesCm'];steps=g.step.validated_steps(source)
  raw=[(a[:2],b[:2])for rows in source.values()for t in rows for a,b in zip(t,t[1:]+t[:1])if math.hypot(a[0]-b[0],a[1]-b[1])>1e-9]
  self.assertEqual(steps['edges'],raw)
  mask=g.module('r30_r3_source_edge_distance_fixture','exterior-garden-organic-native.py')
  for fit in self.source['placements']:
   point=fit['positionCm'][:2];radius=fit['radiusCm'];proof=g.step.circle_clearance(steps,point,radius)
   self.assertEqual(proof['minimumOriginalProjectedRawEdgeDistanceCm'],min(mask._distance(point,a,b)for a,b in raw))
   self.assertGreater(proof['circleClearanceCm'],0)

 def test_15_step_floor_boundary_and_intersecting_circles_rejected(self):
  steps=g.step.validated_steps(self.source['garden']['sourceStepTrianglesCm']);triangle=steps['triangles'][0]
  centre=[sum(p[axis]for p in triangle)/3 for axis in range(2)]
  for point in [centre,triangle[0]]:
   with self.assertRaises(RuntimeError):g.step.circle_clearance(steps,point,1.)
  point=self.source['placements'][0]['positionCm'][:2]
  distance=min(g.step.edge_distance(point,a,b)for a,b in steps['edges'])
  for radius in [distance,distance+1]:
   with self.assertRaises(RuntimeError):g.step.circle_clearance(steps,point,radius)

 def test_16_degenerate_vertical_faces_are_not_bed_triangles(self):
  source=self.source['garden']['sourceStepTrianglesCm'];vertical=[t for rows in source.values()for t in rows if g.step.area2(t)==0]
  self.assertEqual(len(vertical),32)
  with self.assertRaises(RuntimeError):g.step.point_inside([0.,0.],[p[:2]for p in vertical[0]])
  with self.assertRaises(RuntimeError):g.step.edge_distance([0.,0.],[1.,2.],[1.,2.])
  steps=g.step.validated_steps(source)
  for point,radius in [([float('nan'),0.],1.),([0.,0.],float('inf')),([0.,0.],True),([0.,0.],0.)]:
   with self.assertRaises(RuntimeError):g.step.circle_clearance(steps,point,radius)

 def test_17_changed_step_coordinates_order_or_membership_rejected(self):
  source=self.source['garden']['sourceStepTrianglesCm'];key=g.step.STEP_IDS[0]
  changed=copy.deepcopy(source);changed[key][0][0][2]+=.001
  with self.assertRaises(RuntimeError):g.step.validated_steps(changed)
  changed=copy.deepcopy(source);changed[key].pop()
  with self.assertRaises(RuntimeError):g.step.validated_steps(changed)
  changed=copy.deepcopy(source);changed[key][0][0][0]=float('nan')
  with self.assertRaises(RuntimeError):g.step.validated_steps(changed)
  changed=copy.deepcopy(source);changed[key][0],changed[key][1]=changed[key][1],changed[key][0]
  with self.assertRaises(RuntimeError):g.step.validated_steps(changed)

 def test_18_all38_source_only_matrices_reach_complete_footprint_guard(self):
  # This exercises the previously untested runtime source_footprints branch.
  # These are CPU source matrices, not a native Transform or success witness.
  import math
  measurements={}
  for model in self.source['models']:
   rows=[r for r in self.source['placements']if r['model']==model];frames=[];matrices=[]
   for r in rows:
    angle=math.radians(r['yawDeg']);c,s=math.cos(angle)*r['uniformScale'],math.sin(angle)*r['uniformScale']
    frames.append([r['positionCm'],[0.,0.,math.sin(angle/2),math.cos(angle/2)],r['scale']])
    matrices.append([[c,s,0.,0.],[-s,c,0.,0.],[0.,0.,r['uniformScale'],0.],[*r['positionCm'],1.]])
   measurements[model]={'rootIds':[r['rootId']for r in rows],'recoveredValues':frames,'storedMatrices':matrices}
  proof=n.source_footprints(self.source,measurements)
  self.assertEqual((len(proof),sum(r['decodedSourceF32VerticesChecked']for r in proof)),(38,32848))
  self.assertTrue(all(r['fullCircleExcludesOriginalSteps']and r['stepBoundaryCircleClearanceCm']>0 for r in proof))
  self.assertTrue(all(r['sourceStepProjection']['sourceStepProjection']==g.step.POLICY for r in proof))

 def test_19_actual_failed_process_and_byte_snapshot_remain_negative(self):
  evidence=g.failed_r30a_evidence()
  self.assertEqual((evidence['nativeProcessId'],evidence['exitCode'],evidence['newFiles']),(85419,255,0))
  self.assertFalse(evidence['nativeRetrySucceeded']);self.assertFalse(evidence['oldFrozenSourcesChanged'])

 def test_20_all_unrelated_native_algorithms_ast_exact_frozen_failure(self):
  def functions(path):return{v.name:ast.dump(v,include_attributes=False)for v in ast.parse(path.read_text()).body if isinstance(v,ast.FunctionDef)}
  before=functions(ROOT/'scripts/unreal/exterior-garden-composition-native-r30.py');after=functions(ROOT/n.OWNER)
  changed={k for k in before if before[k]!=after[k]}
  self.assertEqual(changed,{'source_footprints','preflight','validate_preflight','main'})
  # Source guards, import F32 winding, survivor filtering and all native setter
  # paths are unchanged; version/report and separate step guard are explicit.
  self.assertEqual(after['filter_original'],before['filter_original'])
  self.assertEqual(after['mesh_proof'],before['mesh_proof'])
  self.assertEqual(after['import_geometry'],before['import_geometry'])


if __name__=='__main__':unittest.main(verbosity=2)
