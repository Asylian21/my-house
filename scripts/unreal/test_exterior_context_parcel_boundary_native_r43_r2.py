"""Only R43 commandlet-spawn/binding changes; no historical13 suite replay."""
import copy,importlib.util,json,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
n=module('_r43_r2_spawn_fixture',ROOT/'scripts/unreal/exterior-context-parcel-boundary-native-r43-r2.py');g=n.g
class Class:
 def __init__(self,path):self.path=path
 def get_path_name(self):return self.path
class Component:
 def __init__(self,owner,identity):self.owner=owner;self.identity=identity;self.props={'cached_max_draw_distance':0.};self.calls=[];self.pawn='<CollisionResponseType.ECR_BLOCK: 2>'
 def get_owner(self):return self.owner
 def get_class(self):return Class('/Script/Engine.StaticMeshComponent')
 def get_attach_parent(self):return None
 def get_world_transform(self):return frame(self.identity)
 def get_editor_property(self,k):return self.props[k]
 def set_editor_property(self,k,v):self.calls.append((k,v));self.props[k]=v
 def set_static_mesh(self,v):self.props['mesh']=v;return True
 def set_material(self,k,v):self.props['material']=v
 def set_mobility(self,v):self.props['mobility']=v
 def set_collision_profile_name(self,v):self.props['collisionProfile']=v
 def set_collision_enabled(self,v):self.props['collision']=v
 def get_collision_response_to_channel(self,k):return self.pawn
 def set_component_tick_enabled(self,v):self.props['componentTick']=v
 def set_visibility(self,v,propagate):self.props['visible']=v
 def set_hidden_in_game(self,v,propagate):self.props['hiddenInGame']=v
 def set_cull_distance(self,v):self.props['ld_max_draw_distance']=v
class Actor:
 def __init__(self,path,identity):self.path=path;self.identity=identity;self.props={'tags':[]};self.c=Component(self,identity);self.calls=[]
 def get_path_name(self):return self.path
 def get_class(self):return Class('/Script/Engine.StaticMeshActor')
 def get_actor_transform(self):return frame(self.identity)
 def get_components_by_class(self,cls):return [self.c]
 def get_editor_property(self,k):return self.c if k in ('root_component','static_mesh_component')else self.props[k]
 def set_editor_property(self,k,v):self.calls.append((k,v));self.props[k]=v
 def set_actor_label(self,v):self.props['label']=v
 def set_actor_tick_enabled(self,v):self.props['actorTick']=v
 def set_actor_hidden_in_game(self,v):self.props['hidden']=v
 def duplicate_actor(self,*a):raise AssertionError('No duplicate route permitted')
def frame(rows):
 def vec(v,axes):return types.SimpleNamespace(**dict(zip(axes,v)))
 return types.SimpleNamespace(translation=vec(rows[0],'xyz'),rotation=vec(rows[1],'xyzw'),scale3d=vec(rows[2],'xyz'))
def mock_u():return types.SimpleNamespace(Name=str,ActorComponent=object,StaticMeshActor=Actor,ComponentMobility=types.SimpleNamespace(STATIC='<ComponentMobility.STATIC: 0>'),CollisionEnabled=types.SimpleNamespace(NO_COLLISION='<CollisionEnabled.NO_COLLISION: 0>'),CollisionChannel=types.SimpleNamespace(ECC_PAWN='pawn'))
class Contracts(unittest.TestCase):
 BUNDLE=None
 @classmethod
 def setUpClass(cls):cls.b=cls.BUNDLE or g.load_contract()
 def test01_actual_failure_binding_is_not_saved_success(self):
  evidence=g.repair_evidence();self.assertEqual(evidence['actualFailedProcessId'],36431);self.assertFalse(evidence['actualSavedMapProduced']);g.require_native_binding(self.b['binding'])
  audit=g.read(g.FAILURE_AUDIT);report=g.read(g.checked(audit['nativeReport']));process=g.read(g.checked(audit['nativeProcess']));raw=g.read(g.checked(audit['rawNativeProcess']));report['status']=n.STATUS;report['nativeApplied']=True
  with self.assertRaises(RuntimeError):g.validate_failed_attempt(audit,report,process,raw)
  bad=copy.deepcopy(self.b['binding']);bad['candidateProject']=str(g.ROOT/'output/unreal/exterior-20261002-r43a/Project/BreziTwin')
  with self.assertRaises(RuntimeError):g.require_native_binding(bad)
 def test02_three_new_only_explicit_template_policies(self):
  u=mock_u();policy=self.b['base']['template']['components'][0]
  for role in g.MATERIAL_ROLES:
   a=Actor('/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.fixture_r2_'+role,copy.deepcopy(g.IDENTITY));c=n.configure_new_actor(u,a,self.b,{g.TEMPLATE},role,'own-mesh','own-material')
   self.assertEqual(a.props['tags'],[g.TAG+role]);self.assertFalse(a.props['actorTick']);self.assertEqual(c.props['collisionProfile'],'NoCollision');self.assertFalse(c.props['can_ever_affect_navigation']);self.assertFalse(c.props['componentTick']);self.assertEqual(c.props['cast_shadow'],role!='gravel')
   for k,v in {**policy['neighborRenderPolicy'],**policy['additionalRenderFlags'],**policy['passFlags']}.items():self.assertEqual(c.props[k],role!='gravel'if k=='cast_shadow'else v)
   self.assertNotIn('cached_max_draw_distance',[k for k,v in c.calls]);self.assertFalse(any('transform'in k for k,v in c.calls));self.assertEqual(c.props['material'],'own-material')
 def test03_old_actor_or_wrong_root_cannot_receive_setters(self):
  u=mock_u();a=Actor(g.TEMPLATE,copy.deepcopy(g.IDENTITY))
  with self.assertRaises(RuntimeError):n.configure_new_actor(u,a,self.b,{g.TEMPLATE},'wood','mesh','material')
  self.assertEqual(a.calls,[]);self.assertEqual(a.c.calls,[])
  a=Actor('/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.fixture_bad_owner',copy.deepcopy(g.IDENTITY));a.c.owner=None
  with self.assertRaises(RuntimeError):n.configure_new_actor(u,a,self.b,set(),'wood','mesh','material')
  self.assertEqual(a.calls,[])
 def test04_observed_signed_zero_is_checkpointed_before_rejection(self):
  u=mock_u();identity=copy.deepcopy(g.IDENTITY);identity[1][1]=-0.;a=Actor('/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.fixture_zero',identity);old=Actor(g.TEMPLATE,copy.deepcopy(g.IDENTITY));system=types.SimpleNamespace(spawn_actor_from_class=lambda *args:a)
  u.EditorActorSubsystem=object;u.Vector=lambda *v:v;u.Rotator=lambda:None;u.get_editor_subsystem=lambda cls:system
  with tempfile.TemporaryDirectory()as tmp,patch.object(n,'actors',return_value={g.TEMPLATE:old}):
   with self.assertRaises(RuntimeError):n.apply_new(u,self.b,{},dict.fromkeys(g.MATERIAL_ROLES),dict.fromkeys(g.MATERIAL_ROLES),Path(tmp))
   got=json.loads((Path(tmp)/'new-class-spawn-observations.json').read_text());self.assertEqual(len(got['actualObservations']),1);self.assertIn('-0.0',json.dumps(got));self.assertFalse(got['originalActorSettersCalled'])
  self.assertEqual(a.calls,[]);self.assertEqual(old.calls,[])
 def test05_private_material_adapter_and_derived_policy_reject(self):
  first=n.private_material_builder();second=n.private_material_builder();self.assertIsNot(first,second);self.assertIs(first.binding_guard(),g);self.assertIs(first.validate_binding(self.b,self.b['binding']),self.b['source'])
  self.assertEqual(n.sha(n.MATERIAL),'fad70bfdd0bd7b9eff2ee289f20a47b1c3d717b7bb683eecbe8d59ff72f873d9');a=Actor('/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.fixture_cache',copy.deepcopy(g.IDENTITY));a.c.props['cached_max_draw_distance']=1.
  with self.assertRaises(RuntimeError):n.configure_new_actor(mock_u(),a,self.b,set(),'metal','mesh','material')
if __name__=='__main__':unittest.main()
