"""CPU source/policy/rollback controls. No Unreal execution or asset writes."""
import copy,importlib.util,json,math,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('coping_under_test',HERE/'coping.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
SCENE=json.loads((M.ROOT/'output/unreal/geometry/scene.json').read_text());REF=json.loads((HERE/'inputs.json').read_text())

class SourceTests(unittest.TestCase):
 def test_current_inputs_hashes_and_source_boxes(self):
  c=M.verify_inputs(SCENE,M.ROOT/'output/unreal/geometry');self.assertEqual(set(c['records']),set(M.IDS));self.assertEqual([len(c['sourceFaces'][i]) for i in M.IDS],[12]*28);self.assertEqual(M.digest(c['recipe']),c['recipeSha256'])
 def test_scope_duplicate_source_geometry_and_shared_consumers_rejected(self):
  for kind in ('extra','duplicate','geometry','slot','rear-removal'):
   s=copy.deepcopy(SCENE);r=copy.deepcopy(REF)
   if kind=='extra':r['sourceRecords']['DOM_01817']={}
   elif kind=='duplicate':s['objects'].append(copy.deepcopy(r['sourceRecords'][M.IDS[0]]))
   elif kind=='geometry':next(x for x in s['objects'] if x['id']==M.IDS[0])['boundsMm']['min'][0]+=.01
   elif kind=='slot':s['materials']['MAT_0102']['color'][0]=.8
   else:s['objects']=[x for x in s['objects'] if x['id']!='DOM_01817']
   with self.subTest(kind=kind),self.assertRaises(RuntimeError):M.check_scene(s,r)
 def test_missing_or_symlink_map_is_refused(self):
  with self.assertRaises(RuntimeError):M.sha(HERE/'absent.jpg')
  role=REF['maps']['Diffuse'];bad=copy.deepcopy(REF);bad['maps']['Diffuse']['sha256']='0'*64
  real_loads=json.loads
  with patch.object(M.json,'loads',side_effect=lambda text,*a,**k:bad if text==(HERE/'inputs.json').read_text() else real_loads(text,*a,**k)):
   with self.assertRaisesRegex(RuntimeError,'downloaded map'):M.verify_inputs(SCENE,M.ROOT/'output/unreal/geometry')
 def test_output_native_entry_is_blocked_before_unreal_import(self):
  with patch.object(M,'__file__',str(M.ROOT/'output/unreal/noncanonical-coping.py')):
   with self.assertRaisesRegex(RuntimeError,'Output-only'):M.native_scope()
 def test_actual_basis_vectors_for_six_signed_faces(self):
  import re
  # Read the actual HLSL basis literal rather than a second implementation.
  branches=re.findall(r'T=float3\(([^)]+)\); B=float3\(([^)]+)\);',M.G.BASIS)
  self.assertEqual(len(branches),3)
  dot=lambda a,b:sum(x*y for x,y in zip(a,b))
  cross=lambda a,b:(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
  for axis in range(3):
   for sign in (-1,1):
    n=[0,0,0];n[axis]=sign
    def vector(text):return tuple(sign if x=='s' else -sign if x=='-s' else float(x) for x in text.split(','))
    t,b=map(vector,branches[axis]);self.assertEqual(cross(t,b),tuple(n));self.assertEqual(dot(t,b),0)
    project=lambda p:(dot(p,t)/50,dot(p,b)/50)
    self.assertEqual(project([50*x for x in t]),(1,0));self.assertEqual(project([50*x for x in b]),(0,1))
    # Native GL->DX green flip happens once. A manufactured rising image-V
    # normal therefore tilts against B on every face, not against world Y.
    dx=(.2,-.4,1);world=[t[k]*dx[0]+b[k]*dx[1]+n[k]*dx[2] for k in range(3)]
    self.assertAlmostEqual(dot(world,b),-.4);self.assertAlmostEqual(dot(world,t),.2);self.assertEqual(dot(world,n),1)
  self.assertTrue(M.G.CODES['uv'].startswith(M.G.BASIS));self.assertTrue(M.G.CODES['normal'].startswith(M.G.BASIS))
  self.assertEqual(M.G.CODES['uv'][len(M.G.BASIS):],'return float2(dot(Position,T),dot(Position,B)) / PeriodCm;')
  self.assertEqual(M.G.CODES['normal'][len(M.G.BASIS):],'return normalize(T*(MapNormal.x*Strength) + B*(MapNormal.y*Strength) + N*MapNormal.z);')
  self.assertIn(('normalMap','RGB','normal','MapNormal'),M.G.LINKS)
 def test_gate_shader_hashes_match_actual_native_code(self):
  import re,hashlib
  hashes=json.loads(re.search(r'POOL_COPING_SHADER_HASHES=(\{[^;]+\});',(HERE/'package-gate.mjs').read_text()).group(1))
  self.assertEqual(hashes,{k:hashlib.sha256(v.encode()).hexdigest() for k,v in M.G.CODES.items()})
 def test_authored_pbr_bounds_and_bad_parameters(self):
  m=REF['material'];self.assertTrue(M.G.validate_parameters(m));r=m['roughness']
  remap=lambda raw:max(r['min'],min(r['max'],r['base']+r['amplitude']*(raw-r['mapMean'])))
  self.assertAlmostEqual(remap(r['mapMean']),.9);self.assertGreaterEqual(remap(0),.82);self.assertLessEqual(remap(1),.96)
  for base,tint in zip(m['baseColorLinear'],m['tintLinear']):
   self.assertGreaterEqual((1-m['albedoMix'])*base,0);self.assertLess((1-m['albedoMix'])*base+m['albedoMix']*tint,1)
  for kind in ('nan','color','displacement','metallic','roughness','dimensions'):
   bad=copy.deepcopy(m)
   if kind=='nan':bad['normalStrength']=float('nan')
   elif kind=='color':bad['baseColorLinear']=[.8392,.8235,.7765]
   elif kind=='displacement':bad['geometryDisplacement']=True
   elif kind=='metallic':bad['metallic']=1
   elif kind=='roughness':bad['roughness']['base']=.1
   else:bad['tileMm']=0
   with self.subTest(kind=kind),self.assertRaises(RuntimeError):M.G.validate_parameters(bad)
  self.assertEqual(M.G.CODES['color'],'return lerp(BaseColor, MapColor * Tint, Blend);')
  self.assertEqual(M.G.CODES['roughness'],'return clamp(Base + Amplitude * (MapR - Mean), Minimum, Maximum);')

class BindingTests(unittest.TestCase):
 def test_strict_source_active_foreign_prior_policy(self):
  p='/Game/Brezi/PoolCoping/R_x/Materials/M_PoolCoping.M_PoolCoping'
  self.assertEqual(M.binding_policy([],M.BASE,p),'source');self.assertEqual(M.binding_policy([p],p,p),'active')
  for a,e,expected in [(['/foreign'],'/foreign',None),([None],M.BASE,None),([],p,None),([],M.BASE,'active'),([p],p,'source')]:
   with self.assertRaises(RuntimeError):M.binding_policy(a,e,p,expected)
 def fixtures(self):
  selected={i:{'actor':i,'component':'Mesh','mesh':M.mesh_path(i),'meshMaterial':M.BASE,'nativeSnapshot':{},'sourceProof':{},'overrides':[],'state':'source','effectiveMaterial':M.BASE} for i in M.IDS}
  world={'actors':{i:{'components':[{'name':'Mesh','overrides':[],'materials':[M.BASE]}]} for i in [*M.IDS,'DOM_01817']},'grassInstanceCount':33769,'grassTransforms':'exact','protectedAssetHashes':{'source':'a'}}
  return selected,world
 def test_only_28_bindings_reconciled(self):
  s,w=self.fixtures();a=copy.deepcopy(w);wanted={i:['candidate'] for i in M.IDS}
  for i in M.IDS:a['actors'][i]['components'][0].update(overrides=['candidate'],materials=['candidate'])
  self.assertTrue(M.compare_world(w,a,s,wanted))
  for k in ('rear','grass','asset'):
   b=copy.deepcopy(a)
   if k=='rear':b['actors']['DOM_01817']['components'][0]['materials']=['candidate']
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
 def test_partial_override_failure_still_restores_all(self):
  s,w=self.fixtures();current=copy.deepcopy(s);current[M.IDS[0]]['overrides']=['candidate'];current[M.IDS[0]]['effectiveMaterial']='candidate'
  active=copy.deepcopy(w);active['actors'][M.IDS[0]]['components'][0].update(overrides=['candidate'],materials=['candidate'])
  self.assertTrue(M.compare_world(w,active,s,{i:current[i]['overrides'] for i in M.IDS}))

if __name__=='__main__':unittest.main()
