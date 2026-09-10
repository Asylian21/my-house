"""CPU source/policy/rollback controls. No Unreal execution or asset writes."""
import copy,importlib.util,json,math,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('mulch_under_test',HERE/'mulch.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
SCENE=json.loads((M.ROOT/'output/unreal/geometry/scene.json').read_text());REF=json.loads((HERE/'inputs.json').read_text())

class SourceTests(unittest.TestCase):
 def test_current_inputs_hashes_source_and_physical_maps(self):
  c=M.verify_inputs(SCENE,M.ROOT/'output/unreal/geometry');self.assertEqual(set(c['records']),set(M.IDS));self.assertEqual([len(c['sourceFaces'][i]) for i in M.IDS],[5,3]);self.assertEqual(M.digest(c['recipe']),c['recipeSha256'])
 def test_scope_duplicate_source_geometry_and_shared_consumers_rejected(self):
  for kind in ('extra','duplicate','geometry','slot','rear-removal'):
   s=copy.deepcopy(SCENE);r=copy.deepcopy(REF)
   if kind=='extra':r['sourceRecords']['DOM_01692']={}
   elif kind=='duplicate':s['objects'].append(copy.deepcopy(r['sourceRecords'][M.IDS[0]]))
   elif kind=='geometry':next(x for x in s['objects'] if x['id']==M.IDS[0])['boundsMm']['min'][0]+=.01
   elif kind=='slot':s['materials']['MAT_0091']['color'][0]=.8
   else:s['objects']=[x for x in s['objects'] if x['id']!='DOM_01692']
   with self.subTest(kind=kind),self.assertRaises(RuntimeError):M.check_scene(s,r)
 def test_missing_or_symlink_map_is_refused(self):
  with self.assertRaises(RuntimeError):M.sha(HERE/'absent.jpg')
  role=REF['maps']['Diffuse'];bad=copy.deepcopy(REF);bad['maps']['Diffuse']['sha256']='0'*64
  with patch.object(M.json,'loads',side_effect=[bad,json.loads((M.ROOT/'output/unreal/geometry/scene.json').read_text())]):
   with self.assertRaisesRegex(RuntimeError,'downloaded map'):M.verify_inputs(SCENE,M.ROOT/'output/unreal/geometry')
 def test_output_native_entry_is_blocked_before_unreal_import(self):
  with patch.object(M,'__file__',str(M.ROOT/'output/unreal/noncanonical-mulch.py')):
   with self.assertRaisesRegex(RuntimeError,'Output-only'):M.native_scope()
 def test_two_metre_world_projection_and_image_v_normal_sign(self):
  self.assertEqual(M.G.UV_CODE,'return WorldPosition.xy / 200.0;');self.assertEqual(M.G.NORMAL_CODE,'return normalize(MapNormal);')
  project=lambda source:(source[0]/2000.,-source[1]/2000.)
  self.assertEqual(project((2000,0)),(1,0));self.assertEqual(project((0,2000)),(0,-1));self.assertEqual(project((-4000,-2000)),(-2,1))
  # Manufactured height increasing with image row V: GL Y is positive;
  # one native GL->DX flip gives negative world Y for UV V=+UE Y.
  slope=.4;gl=(0,slope,1);dx=(gl[0],-gl[1],gl[2]);n=tuple(x/math.sqrt(sum(y*y for y in dx)) for x in dx)
  self.assertLess(n[1],0);self.assertGreater(n[2],0);self.assertAlmostEqual(sum(x*x for x in n),1)
 def test_shader_has_no_extra_flip_or_roughness_remap(self):
  self.assertEqual(M.G.OUTPUTS[2],('ROUGHNESS','roughMap','R'));self.assertEqual(M.G.LINKS[-1],('normalMap','RGB','normal','MapNormal'));self.assertNotIn('-MapNormal',M.G.NORMAL_CODE)

class BindingTests(unittest.TestCase):
 def test_strict_source_active_foreign_prior_policy(self):
  p='/Game/Brezi/PlantingSurfaces/Mulch/R_x/Materials/M_Mulch.M_Mulch'
  self.assertEqual(M.binding_policy([],M.BASE,p),'source');self.assertEqual(M.binding_policy([p],p,p),'active')
  for a,e,expected in [(['/foreign'],'/foreign',None),([None],M.BASE,None),([],p,None),([],M.BASE,'active'),([p],p,'source')]:
   with self.assertRaises(RuntimeError):M.binding_policy(a,e,p,expected)
 def fixtures(self):
  selected={i:{'actor':i,'component':'Mesh','mesh':M.mesh_path(i),'meshMaterial':M.BASE,'nativeSnapshot':{},'sourceProof':{},'overrides':[],'state':'source','effectiveMaterial':M.BASE} for i in M.IDS}
  world={'actors':{i:{'components':[{'name':'Mesh','overrides':[],'materials':[M.BASE]}]} for i in [*M.IDS,'DOM_01692']},'grassInstanceCount':33769,'grassTransforms':'exact','protectedAssetHashes':{'source':'a'}}
  return selected,world
 def test_only_two_bindings_reconciled(self):
  s,w=self.fixtures();a=copy.deepcopy(w);wanted={i:['candidate'] for i in M.IDS}
  for i in M.IDS:a['actors'][i]['components'][0].update(overrides=['candidate'],materials=['candidate'])
  self.assertTrue(M.compare_world(w,a,s,wanted))
  for k in ('rear','grass','asset'):
   b=copy.deepcopy(a)
   if k=='rear':b['actors']['DOM_01692']['components'][0]['materials']=['candidate']
   elif k=='grass':b['grassTransforms']='changed'
   else:b['protectedAssetHashes']['source']='changed'
   with self.subTest(k=k),self.assertRaises(RuntimeError):M.compare_world(w,b,s,wanted)
 def test_failed_graph_can_be_removed_only_after_identity_and_world_preflight(self):
  s,w=self.fixtures();before={'selected':s,'world':w};candidate='candidate';current=copy.deepcopy(s);active=copy.deepcopy(w);writes=[]
  for i in M.IDS:current[i].update(state='active',overrides=[candidate],effectiveMaterial=candidate);active['actors'][i]['components'][0].update(overrides=[candidate],materials=[candidate])
  class Component:
   def __init__(self,i):self.i=i
   def get_name(self):return 'Mesh'
   def get_material(self,n):return types.SimpleNamespace(get_path_name=lambda:M.BASE)
  found={i:(types.SimpleNamespace(get_path_name=lambda i=i:i),Component(i)) for i in M.IDS}
  common=types.SimpleNamespace(components=lambda u,ids:found,set_overrides=lambda u,c,v:writes.append((c.i,v)))
  with patch.object(M,'native_guard',return_value=current) as guard,patch.object(M,'snapshot_world',return_value=active),patch.object(M,'helper',return_value=types.SimpleNamespace(common=lambda:common)):
   M.restore_failed_binding(object(),{'materialPath':candidate},before);guard.assert_called_once_with(unittest.mock.ANY,{'materialPath':candidate},allow_failed_graph=True)
  self.assertEqual(writes,[(i,[]) for i in M.IDS])
  writes.clear();current[M.IDS[1]]['actor']='foreign'
  with patch.object(M,'native_guard',return_value=current),patch.object(M,'snapshot_world',return_value=active),patch.object(M,'helper',return_value=types.SimpleNamespace(common=lambda:common)):
   with self.assertRaises(RuntimeError):M.restore_failed_binding(object(),{'materialPath':candidate},before)
  self.assertEqual(writes,[])
 def test_partial_override_failure_still_restores_both(self):
  s,w=self.fixtures();current=copy.deepcopy(s);current[M.IDS[0]]['overrides']=['candidate'];current[M.IDS[0]]['effectiveMaterial']='candidate'
  active=copy.deepcopy(w);active['actors'][M.IDS[0]]['components'][0].update(overrides=['candidate'],materials=['candidate'])
  self.assertTrue(M.compare_world(w,active,s,{i:current[i]['overrides'] for i in M.IDS}))

if __name__=='__main__':unittest.main()
