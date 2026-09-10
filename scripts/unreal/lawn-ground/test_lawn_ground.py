"""CPU source/math/preservation gates, never a native graph/runtime claim."""
import copy,hashlib,importlib.util,json,math,random,struct,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'lib/twin-site.ts').is_file())
def load(name):
 s=importlib.util.spec_from_file_location('test_lawn_'+name,HERE/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
S=load('source');H=load('shading');G=load('graph');W=load('lawn_ground')
class MathTests(unittest.TestCase):
 def test_partition_and_source_position(self):
  rng=random.Random(601226)
  for uv in [(-2.,3.),(0.,0.),(.5,.5),(1.,1.)]+[(rng.uniform(-25,25),rng.uniform(-25,25)) for _ in range(300)]:
   weights,verts=H.lattice(uv);self.assertTrue(all(0<=w<=1 for w in weights));self.assertAlmostEqual(sum(weights),1)
   for i in range(2):self.assertAlmostEqual(sum(w*v[i] for w,v in zip(weights,verts)),uv[i])
 def test_preserve_constant_maps(self):
  for uv in [(-.2,2.9),(.1,.4),(.7,.8)]:
   w,_=H.samples(uv)
   for value in [0,.263,1]:self.assertAlmostEqual(H.blend([value]*3,w),value)
 def test_linear_input_blend_preserves_bounds(self):
  rng=random.Random(20)
  for _ in range(200):
   w,_=H.samples((rng.random()*3,rng.random()*3));r=[rng.random() for _ in range(3)];v=H.blend(r,w)
   self.assertGreaterEqual(v,min(r)-1e-14);self.assertLessEqual(v,max(r)+1e-14)
  self.assertAlmostEqual(H.blend([.1,.4,.7],[.25,.5,.25]),.4)
  self.assertNotIn('pow',H.CODES['roughness']);self.assertNotIn('1.0 -',H.CODES['roughness'])
 def test_repeat_phase_changes_without_scale_or_rotation(self):
  uv=(.31,.23);w,coords=H.samples(uv);w2,c2=H.samples((uv[0]+1,uv[1]))
  [self.assertAlmostEqual(a,b) for a,b in zip(w,w2)];self.assertNotEqual(tuple((x%1,y%1) for x,y in coords),tuple((x%1,y%1) for x,y in c2))
  eps=1e-5
  for axis in range(2):
   q=list(uv);q[axis]+=eps;_,shifted=H.samples(q)
   for a,b in zip(coords,shifted):
    for i in range(2):self.assertAlmostEqual((b[i]-a[i])/eps,float(i==axis),places=8)
 def test_continuity_at_triangle_and_cell_edges(self):
  def field(uv):
   w,c=H.samples(uv);return H.blend([math.sin(2*math.pi*x)*math.cos(2*math.pi*y) for x,y in c],w)
  for p,axis in [((.4,.6),0),((1.,.3),0),((.3,1.),1),((-.4,-.6),0),((0.,0.),0)]:
   a=list(p);b=list(p);a[axis]-=1e-7;b[axis]+=1e-7
   self.assertLess(abs(field(a)-field(b)),3e-6)
 def test_normal_mixture_preserves_basis(self):
  w,_=H.samples((.2,.4));n=[(.3,.1,math.sqrt(.9)),(-.2,.2,math.sqrt(.92)),(.1,-.4,math.sqrt(.83))]
  mixed=[H.blend([v[i] for v in n],w) for i in range(3)];length=math.sqrt(sum(x*x for x in mixed));out=[x/length for x in mixed]
  self.assertAlmostEqual(sum(x*x for x in out),1);self.assertGreater(out[2],0)
  self.assertIn('lengthSquared > 1e-12',H.CODES['normal'])
 def test_source_physical_scale(self):
  self.assertAlmostEqual(32133/H.UV_SCALE[0],1400);self.assertAlmostEqual(24497/H.UV_SCALE[1],1400)
 def test_explicit_derivative_upstream_of_hash(self):
  self.assertEqual(H.CODES['gradientX'],'return ddx(UV);\n');self.assertEqual(H.CODES['gradientY'],'return ddy(UV);\n')
  self.assertTrue(all('ddx' not in H.CODES['phase'+str(i)] and 'ddy' not in H.CODES['phase'+str(i)] for i in range(3)))
 def test_nonfinite_and_unbounded_uv_refused(self):
  for uv in [(float('nan'),0),(0,float('inf')),(1e8,0)]:
   with self.assertRaises(ValueError):H.samples(uv)
class EffectiveRoughnessTests(unittest.TestCase):
 def test_endpoints_and_representative_provider_value(self):
  for raw,wanted in [(0,.72),(1,.95),(.263,.78049)]:self.assertAlmostEqual(H.effective_roughness(raw),wanted)
 def test_affine_variation_and_bounds_after_three_phase_blend(self):
  rng=random.Random(72)
  for _ in range(300):
   w,_=H.samples((rng.uniform(-10,10),rng.uniform(-10,10)));raw=[rng.random() for i in range(3)]
   value=H.effective_roughness(H.blend(raw,w));self.assertGreaterEqual(value,.72);self.assertLessEqual(value,.95)
   self.assertAlmostEqual(value,H.blend([H.effective_roughness(r) for r in raw],w))
  self.assertAlmostEqual(H.effective_roughness(.8)-H.effective_roughness(.2),.23*.6)
 def test_invalid_input_is_not_silently_clamped(self):
  for value in [-.001,1.001,float('nan'),float('inf')]:
   with self.assertRaises(ValueError):H.effective_roughness(value)
 def test_explicit_effective_shader_and_artist_claim(self):
  self.assertEqual(H.CODES['roughness'],'float value = A*W.x + B*W.y + C*W.z;\nreturn 0.72 + 0.23 * value;\n')
  self.assertEqual(H.ROUGHNESS_POLICY['bounds'],[.72,.95]);self.assertFalse(H.ROUGHNESS_POLICY['vendorRadiometricCalibration'])
  self.assertEqual(H.CODES['color'],'float3 value = A*W.x + B*W.y + C*W.z;\nreturn value;\n')
class ContractTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.scene=json.loads((ROOT/'output/unreal/geometry/scene.json').read_text());cls.geometry=ROOT/'output/unreal/geometry';cls.contract=S.verify_inputs(cls.scene,cls.geometry)
 def test_real_source_and_three_pinned_maps(self):
  self.assertEqual(set(self.contract['candidate']['maps']),{'Diffuse','nor_gl','Rough'});self.assertEqual(self.contract['reference']['material']['tintLinear'],[1,1,1]);self.assertEqual(self.contract['reference']['material']['roughness'],H.ROUGHNESS_POLICY)
 def test_exact_recipe_inputs_and_global_material_pin(self):
  self.assertIn('scripts/unreal/materials.py',self.contract['pipelineFiles']);self.assertNotIn('scripts/unreal/materials.py',self.contract['recipe']['recipeInputs'])
 def test_supplied_scene_drift_refused(self):
  scene=copy.deepcopy(self.scene);scene['materials']['MAT_0001']['roughness']=.5
  with self.assertRaises(RuntimeError):S.verify_inputs(scene,self.geometry)
 def test_real_obj_float32_position_uv_proof(self):
  source=S.read_source(self.geometry/'dom-mm.obj');rows=[];i=0
  f=lambda x:struct.unpack('f',struct.pack('f',x))[0]
  for tri in source:
   row=[]
   for p,uv in tri:
    row.append({'pCm':[f(p[0]/10),f(-p[1]/10),f(p[2]/10)],'uv0':list(map(f,uv)),'vertex':i,'instance':i});i+=1
   rows.append(row)
  snap={'rows':rows,'renderTriangles':27};self.assertEqual(S.source_proof(snap,source)['triangles'],27)
  bad=copy.deepcopy(snap);bad['rows'][0][0]['uv0'][0]+=.001
  with self.assertRaises(RuntimeError):S.source_proof(bad,source)
  bad=copy.deepcopy(snap);bad['rows'][0].reverse()
  with self.assertRaises(RuntimeError):S.source_proof(bad,source)
 def test_graph_registered_pbr_policy(self):
  self.assertEqual(len(G.expected_roles()),24);self.assertEqual(len(G.links()),48)
  for role in G.ROLES:
   for i in range(3):
    name=role+str(i)
    self.assertIn(('phase'+str(i),'',name,'UVs'),G.links());self.assertIn(('gradientX','',name,'DDX(UVs)'),G.links());self.assertIn(('gradientY','',name,'DDY(UVs)'),G.links())
  for node in ('color','normal','roughness'):self.assertIn(('weights','',node,'W'),G.links())
 def test_output_draft_mutation_refused_before_unreal_import(self):
  if Path(W.__file__).resolve()==ROOT/W.OWNER:self.skipTest('Already adopted; output guard is intentionally inactive')
  with self.assertRaisesRegex(RuntimeError,'Output-only'):W.apply_lawn_ground(self.scene,self.geometry)
class CacheRefusalTests(unittest.TestCase):
 def test_missing_exact_existing_conflict_and_symlink(self):
  R=load('restore_inputs')
  with tempfile.TemporaryDirectory(prefix='lawn-ground-cache-') as directory:
   p=Path(directory).resolve()/'map.jpg';spec={'bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}
   with self.assertRaises(RuntimeError):R.verify_file(p,spec)
   p.write_bytes(b'abc');R.verify_file(p,spec)
   p.write_bytes(b'abd')
   with self.assertRaises(RuntimeError):R.verify_file(p,spec)
   p.write_bytes(b'abc');link=p.with_name('link.jpg');link.symlink_to(p)
   with self.assertRaises(RuntimeError):R.verify_file(link,spec)
   dangling=p.with_name('absent.jpg');dangling.symlink_to(p.with_name('missing.jpg'))
   with self.assertRaises(RuntimeError):R.verify_file(dangling,spec)

class PreservationTests(unittest.TestCase):
 def setUp(self):
  self.before={'actors':{'lawn':{'components':[{'name':'mesh','materials':[S.BASE],'overrides':[]}]},'other':{'visible':True}},'grassInstanceCount':33769,'nativeGrassTransforms':'same','protectedAssetHashes':{'mesh':'abc'}}
  self.selected={'actor':'lawn','component':'mesh'}
 def candidate(self):
  a=copy.deepcopy(self.before);a['actors']['lawn']['components'][0].update(materials=['candidate'],overrides=['candidate']);return a
 def test_only_exact_selected_override_allowed(self):self.assertTrue(W.compare_world(self.before,self.candidate(),self.selected,['candidate']))
 def test_grass_density_or_transforms_drift_refused(self):
  for key,v in [('grassInstanceCount',33770),('nativeGrassTransforms','changed')]:
   a=self.candidate();a[key]=v
   with self.assertRaises(RuntimeError):W.compare_world(self.before,a,self.selected,['candidate'])
 def test_geometry_or_other_actor_drift_refused(self):
  a=self.candidate();a['protectedAssetHashes']['mesh']='changed'
  with self.assertRaises(RuntimeError):W.compare_world(self.before,a,self.selected,['candidate'])
  a=self.candidate();a['actors']['other']['visible']=False
  with self.assertRaises(RuntimeError):W.compare_world(self.before,a,self.selected,['candidate'])
 def test_restoration_exact_original_empty_array(self):
  self.assertTrue(W.compare_world(self.candidate(),self.before,self.selected,[]))
class RecoveryTests(unittest.TestCase):
 def setUp(self):
  from types import SimpleNamespace
  from unittest.mock import patch
  self.contract={'materialPath':'/Game/Brezi/LawnGround/R_test/Materials/M.M','recipeSha256':'a'*64}
  class Material:
   def __init__(self,p):self.p=p
   def get_path_name(self):return self.p
  self.material=Material(self.contract['materialPath'])
  self.metadata={'BreziGeneratedBy':G.OWNER,G.RECIPE_TAG:'a'*64,'source_material_slot':'MAT_0001'}
  self.u=SimpleNamespace(Material=Material,EditorAssetLibrary=SimpleNamespace(get_metadata_tag=lambda m,k:self.metadata.get(k,'')))
  self.before={'selected':{'actor':'lawn','component':'mesh','mesh':S.MESH,'meshMaterial':S.BASE,'nativeSnapshot':{'p':[1,2,3]},'sourceProof':{'triangles':27},'overrides':[]},'world':{'actors':{'lawn':{'components':[{'name':'mesh','materials':[S.BASE],'overrides':[]}]},'other':{'visible':True}},'grassInstanceCount':33769,'nativeGrassTransforms':'same','protectedAssetHashes':{'mesh':'abc'}}}
  self.current=copy.deepcopy(self.before['selected']);self.current['overrides']=[self.contract['materialPath']]
  self.world=copy.deepcopy(self.before['world']);self.world['actors']['lawn']['components'][0].update(materials=self.current['overrides'],overrides=self.current['overrides'])
  self.writes=[];self.bindings=list(self.current['overrides']);self.guard_modes=[]
  def guard(u,contract,geometry,expected=None,*,allow_failed_candidate_graph=False):
   self.guard_modes.append(allow_failed_candidate_graph)
   # Emulate the single failed native graph read while executing the real
   # candidate identity and the real recovery/protected-world policies.
   if not allow_failed_candidate_graph:raise RuntimeError('candidate graph failed')
   G.material_identity(u,self.material,contract)
   W.require(self.current['overrides'] in ([],[contract['materialPath']]),'foreign override')
   return copy.deepcopy(self.current)
  def write(u,c,paths):self.writes.append(list(paths));self.bindings=list(paths)
  component=SimpleNamespace(get_name=lambda:'mesh',get_material=lambda i:Material(self.bindings[0] if self.bindings else S.BASE))
  actor=SimpleNamespace(get_path_name=lambda:'lawn')
  for name,value in [('native_guard',guard),('snapshot_world',lambda u:copy.deepcopy(self.world)),('target',lambda u:(actor,component)),('common',lambda:SimpleNamespace(set_overrides=write)),('read_material',lambda u,c:(_ for _ in ()).throw(RuntimeError('candidate graph failed')))]:
   scope=patch.object(W,name,value);scope.start();self.addCleanup(scope.stop)
 def recover(self):W.restore_failed_binding(self.u,self.contract,None,self.before)
 def test_bad_candidate_graph_can_be_removed(self):
  self.recover();self.assertEqual(self.writes,[[]]);self.assertEqual(self.bindings,[]);self.assertEqual(self.guard_modes,[True])
 def test_forward_setter_still_requires_full_graph(self):
  with self.assertRaisesRegex(RuntimeError,'candidate graph failed'):W.set_binding(self.u,self.contract,None,[])
  self.assertEqual(self.writes,[]);self.assertEqual(self.guard_modes,[False])
 def test_foreign_owner_recipe_or_slot_refused_before_write(self):
  for key in self.metadata:
   with self.subTest(key=key):
    old=self.metadata[key];self.metadata[key]='foreign'
    with self.assertRaises(RuntimeError):self.recover()
    self.metadata[key]=old;self.assertEqual(self.writes,[])
 def test_foreign_material_path_and_type_refused(self):
  original=self.material
  self.material.p='foreign'
  with self.assertRaises(RuntimeError):self.recover()
  self.material=object()
  with self.assertRaises(RuntimeError):self.recover()
  self.material=original;self.assertEqual(self.writes,[])
 def test_foreign_override_refused_before_write(self):
  self.current['overrides']=['foreign']
  with self.assertRaises(RuntimeError):self.recover()
  self.assertEqual(self.writes,[])
 def test_selection_or_source_change_refused_before_write(self):
  for key in ('actor','component','mesh','meshMaterial','nativeSnapshot','sourceProof'):
   with self.subTest(key=key):
    old=self.current[key];self.current[key]='changed'
    with self.assertRaises(RuntimeError):self.recover()
    self.current[key]=old;self.assertEqual(self.writes,[])
 def test_protected_world_and_grass_change_refused(self):
  for key in ('grassInstanceCount','nativeGrassTransforms','protectedAssetHashes'):
   with self.subTest(key=key):
    old=self.world[key];self.world[key]='changed'
    with self.assertRaises(RuntimeError):self.recover()
    self.world[key]=old;self.assertEqual(self.writes,[])
  self.world['actors']['other']['visible']=False
  with self.assertRaises(RuntimeError):self.recover()
  self.assertEqual(self.writes,[])
 def test_unknown_prior_binding_refused(self):
  self.before['selected']['overrides']=['foreign']
  with self.assertRaises(RuntimeError):self.recover()
  self.assertEqual(self.writes,[])
 def test_cannot_claim_broken_previously_active_graph_restored(self):
  self.before['selected']['overrides']=[self.contract['materialPath']]
  self.before['world']=copy.deepcopy(self.world)
  with self.assertRaisesRegex(RuntimeError,'candidate graph failed'):self.recover()
  self.assertEqual(self.writes,[])

if __name__=='__main__':unittest.main()
