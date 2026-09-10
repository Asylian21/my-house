"""One reversible component-only lawn PBR override; no native action on import.

Native entrypoints refuse this output proposal until adopted at OWNER. Original
source material, geometry, UV, collision and grass instances are never edited.
"""
import gc,importlib.util,json,re
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'lib/twin-site.ts').is_file())
OWNER='scripts/unreal/lawn-ground/lawn_ground.py'
MAP='/Game/Brezi/Maps/Brezi'

def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
S=module('brezi_lawn_ground_source',HERE/'source.py')
G=module('brezi_lawn_ground_graph',HERE/'graph.py')
require=S.require

_COMMON=None
def common():
 global _COMMON
 if _COMMON is None:_COMMON=module('brezi_lawn_ground_common',ROOT/'scripts/unreal/tv-oak/tv_oak.py')
 return _COMMON
def verify_inputs(scene,geometry):return S.verify_inputs(scene,geometry)
def native_scope():require(Path(__file__).resolve()==ROOT/OWNER,'Output-only lawn ground draft cannot mutate native assets')
def path(obj):return obj.get_path_name() if obj else None

def transform(t):return {'p':[float(getattr(t.translation,k)) for k in 'xyz'],'q':[float(getattr(t.rotation,k)) for k in 'xyzw'],'s':[float(getattr(t.scale3d,k)) for k in 'xyz']}

def target(u):
 found=common().components(u,[S.ID]);a,c=found[S.ID]
 require(a.actor_has_tag('BreziGenerated'),'Lawn actor lacks generated provenance')
 return a,c

def native_guard(u,contract,geometry,expected=None,*,allow_failed_candidate_graph=False):
 a,c=target(u);mesh=c.get_editor_property('static_mesh');assets=u.EditorAssetLibrary
 require(mesh is not None and path(mesh)==S.MESH and c.get_num_materials()==1 and len(mesh.get_editor_property('static_materials'))==1 and mesh.get_num_sections(0)==1 and mesh.get_num_triangles(0)>0 and mesh.get_num_tex_coords(0)==1,'Lawn mesh/slot/UV/render topology differs')
 for key,value in {'source_object_id':S.ID,'source_id':contract['record']['sourceId'],'source_group':contract['record']['group'],'source_name':contract['record']['name']}.items():require(assets.get_metadata_tag(mesh,key)==value,'Lawn mesh source binding differs: '+key)
 require(transform(c.get_world_transform())=={'p':[0.,0.,0.],'q':[0.,0.,0.,1.],'s':[1.,1.,1.]},'Lawn source component transform changed')
 source=mesh.get_material(0)
 require(path(source)==S.BASE and assets.get_metadata_tag(source,'BreziGeneratedBy')=='scripts/unreal/materials.py' and assets.get_metadata_tag(source,'source_material_slot')==S.SLOT,'Canonical lawn base material changed')
 current=common().overrides(c);effective=path(c.get_material(0))
 if current==[]:
  require(effective==S.BASE and expected!='active','Canonical lawn effective binding differs or candidate absent');state='source'
 elif current==[contract['materialPath']]:
  require(effective==contract['materialPath'] and expected!='source','Owned lawn component binding differs')
  if allow_failed_candidate_graph:G.material_identity(u,c.get_material(0),contract)
  else:G.material_proof(u,c.get_material(0),contract,common())
  state='active'
 else:raise RuntimeError('Refusing foreign/untracked lawn component material override')
 snap=S.native_snapshot(u,mesh);proof=S.source_proof(snap,S.read_source(Path(geometry)/'dom-mm.obj'))
 return {'state':state,'actor':path(a),'component':c.get_name(),'mesh':path(mesh),'meshMaterial':path(source),'effectiveMaterial':effective,'overrides':current,'nativeSnapshot':snap,'sourceProof':proof}

def snapshot_world(u):
 """Plain values only, including all HISM transforms. No wrappers escape."""
 from materials import _asset_hashes
 world=u.EditorLevelLibrary.get_editor_world();require(world.get_path_name().split('.')[0]==MAP and u.EditorAssetLibrary.get_metadata_tag(world,'BreziGeneratedBy')=='scripts/unreal/import_scene.py','Expected owned Brezi map')
 rows={};asset_paths=set();source_ids=[];grass_count=0
 for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  tags=list(map(str,a.get_editor_property('tags')));source_ids += [t for t in tags if re.fullmatch('DOM_[0-9]{5}',t)]
  components=[]
  for c in a.get_components_by_class(u.StaticMeshComponent):
   mesh=c.get_editor_property('static_mesh')
   if not mesh:continue
   materials=[c.get_material(i) for i in range(c.get_num_materials())];asset_paths.add(path(mesh));asset_paths.update(path(m) for m in materials if m)
   asset_paths.update(path(m.get_editor_property('material_interface')) for m in mesh.get_editor_property('static_materials') if m.get_editor_property('material_interface'))
   r={'name':c.get_name(),'class':c.get_class().get_path_name(),'mesh':path(mesh),'transform':transform(c.get_world_transform()),'materials':[path(m) for m in materials],'overrides':common().overrides(c),'visible':bool(c.get_editor_property('visible')),'hiddenInGame':bool(c.get_editor_property('hidden_in_game')),'collision':str(c.get_collision_enabled()),'profile':str(c.get_collision_profile_name()),'pawn':str(c.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN)),'navigation':bool(c.get_editor_property('can_ever_affect_navigation')),'tags':list(map(str,c.get_editor_property('component_tags')))}
   for key in ('cast_shadow','visible_in_ray_tracing','affect_distance_field_lighting','affect_dynamic_indirect_lighting'):r[key]=bool(c.get_editor_property(key))
   if isinstance(c,u.InstancedStaticMeshComponent):
    values=[]
    for i in range(c.get_instance_count()):
     t=c.get_instance_transform(i,False)
     if isinstance(t,tuple) and len(t)==2 and t[0] is True:t=t[1]
     require(t is not None and hasattr(t,'translation'),'HISM native transform getter failed');values.append(transform(t))
    r.update(instanceCount=len(values),nativeInstancesSha256=S.digest(values),cullStart=int(c.get_editor_property('instance_start_cull_distance')),cullEnd=int(c.get_editor_property('instance_end_cull_distance')))
    if a.actor_has_tag('BreziLawnDetail'):grass_count+=len(values)
   components.append(r)
  rows[path(a)]={'class':a.get_class().get_path_name(),'tags':tags,'transform':transform(a.get_actor_transform()),'hidden':bool(a.get_editor_property('hidden')),'metadata':{str(k):str(v) for k,v in u.EditorAssetLibrary.get_metadata_tag_values(a).items()},'components':sorted(components,key=lambda c:c['name'])}
 require(len(source_ids)==len(set(source_ids))==1878 and S.ID in source_ids,'Canonical runtime source coverage differs')
 protected=[p for p in asset_paths if p.startswith('/Game/Brezi/') and not p.startswith(G.PREFIX+'/')]
 return {'actors':rows,'canonicalIds':sorted(source_ids),'grassInstanceCount':grass_count,'protectedAssetHashes':_asset_hashes(protected)}

def compare_world(before,after,selected,wanted):
 expected=S.values(before);r=expected['actors'][selected['actor']]
 cs=[c for c in r['components'] if c['name']==selected['component']];require(len(cs)==1,'Selected lawn component snapshot absent')
 cs[0]['overrides']=list(wanted);cs[0]['materials']=[wanted[0] if wanted else S.BASE]
 require(S.values(after)==expected,'Lawn override changed protected actor, geometry/UV asset, collision, grass state or unrelated binding')
 return True

def inspect(u,contract,geometry,expected=None):
 selected=native_guard(u,contract,geometry,expected);return {'selected':selected,'world':snapshot_world(u)}

def set_binding(u,contract,geometry,paths):
 native_guard(u,contract,geometry)
 require(paths in ([],[contract['materialPath']]),'Lawn setter refused unknown override array')
 _,c=target(u);common().set_overrides(u,c,paths)
 require(path(c.get_material(0))==(paths[0] if paths else S.BASE),'Lawn setter readback differs')

def restore_failed_binding(u,contract,geometry,before):
 """Remove only an exactly identified failed candidate, not a foreign override.

 The full graph is intentionally not a precondition for discarding the failing
 candidate. Its owner/recipe, source geometry, prior target and all protected
 world state remain mandatory before the only write. No UObject escapes.
 """
 current=native_guard(u,contract,geometry,allow_failed_candidate_graph=True)
 for key in ('actor','component','mesh','meshMaterial','nativeSnapshot','sourceProof'):
  require(S.values(current[key])==S.values(before['selected'][key]),'Rollback source/selection differs: '+key)
 compare_world(before['world'],snapshot_world(u),before['selected'],current['overrides'])
 wanted=before['selected']['overrides']
 require(wanted in ([],[contract['materialPath']]),'Rollback prior override is not source/exact candidate')
 # Restoring an already-active old candidate cannot repair its corrupted graph.
 # Keep that failure explicit; never certify the broken graph as restored.
 if wanted:read_material(u,contract)
 actor,component=target(u)
 require(path(actor)==before['selected']['actor'] and component.get_name()==before['selected']['component'],'Rollback target changed before write')
 common().set_overrides(u,component,wanted)
 require(path(component.get_material(0))==(wanted[0] if wanted else S.BASE),'Rollback effective material differs')

def save_unload_reload(u,owned_paths):
 levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
 require(levels.save_current_level(),'Lawn map save failed')
 require(u.EditorLoadingAndSavingUtils.new_blank_map(False),'Lawn map unload failed')
 gc.collect();packages=[]
 for asset_path in sorted(owned_paths):
  require(asset_path.startswith(G.PREFIX+'/'),'Lawn package unload escaped owned scope')
  obj=u.find_object(None,asset_path)
  if obj:
   require(u.EditorAssetLibrary.get_metadata_tag(obj,'BreziGeneratedBy')==OWNER,'Refusing foreign package unload')
   package=obj.get_outermost();require(package.get_path_name()==asset_path.split('.')[0],'Lawn asset package differs');packages.append(package)
   del package
  del obj
 if packages:
  result=u.EditorLoadingAndSavingUtils.unload_packages(packages)
  require(isinstance(result,tuple) and len(result)==2 and result[0] is True and not str(result[1]),'Lawn owned package unload failed: '+str(result))
 del packages;gc.collect()
 require(all(u.find_object(None,p) is None for p in owned_paths),'Lawn old assets still loaded; saved disk roundtrip unproven')
 require(levels.load_level(MAP),'Lawn saved map reload failed')
 return {'mapSaved':True,'worldUnloaded':True,'allFourOwnedAssetsAbsentBeforeReload':True,'mapReloaded':True}

def read_material(u,contract):
 material=u.load_object(None,contract['materialPath']);require(material is not None,'Saved lawn material missing')
 return G.material_proof(u,material,contract,common())

def preflight_reimport(u,actors,scene,geometry):
 """Strict before-deletion guard. No actor metadata or cleanup is introduced."""
 native_scope();contract=verify_inputs(scene,geometry)
 selected=[a for a in actors if a.actor_has_tag(S.ID)]
 if not selected:return None
 require(len(selected)==1 and selected[0].actor_has_tag('BreziGenerated'),'Foreign/duplicate source lawn actor')
 return native_guard(u,contract,geometry)

def execute(scene,geometry,restore=False):
 native_scope()
 import unreal as u
 from materials import _asset_hashes
 require(Path(u.Paths.project_dir()).resolve()==ROOT/'unreal/BreziTwin','Unexpected native project')
 contract=verify_inputs(scene,geometry);report_path=Path(geometry).parent/'lawn-ground-report.json'
 report={'status':'pending','nativeApplied':False,'restoring':bool(restore),'recipeSha256':contract['recipeSha256'],'recipe':contract['recipe'],'recipeCanonicalJson':contract['recipeCanonicalJson'],'pipelineFiles':contract['pipelineFiles'],'sourceObjectId':S.ID,'sourceMaterialSlot':S.SLOT,'sourceManifestSha256':S.SCENE_SHA,'sourceObjSha256':S.OBJ_SHA,'renderedVerified':False,'activationStarted':False,'rollbackAttempted':False,'rollbackVerified':False,'actorMetadataWritten':False}
 before=None;owned_paths=set();mutated=False
 def write(status):
  report.update(status=status,generatedAt=datetime.now(timezone.utc).isoformat());tmp=report_path.with_suffix('.tmp');tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(report_path)
 try:
  before=inspect(u,contract,geometry,'active' if restore else None)
  expected_ids=sorted(r['id'] for r in scene['objects'] if r['enabled'] and r['instances']>0)
  require(before['world']['canonicalIds']==expected_ids,'Native source IDs differ from runtime source set')
  require(before['world']['grassInstanceCount']==33769,'Run lawn ground after the complete source-pinned lawn detail stage')
  report.update(selectedBefore=before['selected'],grassInstanceCount=before['world']['grassInstanceCount'])
  if restore:
   proof=read_material(u,contract);owned_paths={contract['materialPath'],*[v['asset'] for v in proof['textures'].values()]};report['stagedMaterialProof']=proof
  else:
   _,owned_paths=G.create_material(u,contract,common())
  require(len(owned_paths)==4,'Lawn expected material+three texture assets')
  owned_hashes=_asset_hashes(owned_paths)
  report['stagedReload']=save_unload_reload(u,owned_paths)
  staged=inspect(u,contract,geometry,'active' if before['selected']['state']=='active' else 'source')
  require(S.values(staged)==S.values(before),'Source changed before lawn activation')
  report['stagedMaterialProof']=read_material(u,contract)
  require(_asset_hashes(owned_paths)==owned_hashes,'Staged lawn saved asset bytes changed')
  wanted=[] if restore else [contract['materialPath']]
  mutated=True;report['activationStarted']=True;set_binding(u,contract,geometry,wanted)
  report['activeReload']=save_unload_reload(u,owned_paths)
  after=inspect(u,contract,geometry,'source' if restore else 'active')
  compare_world(before['world'],after['world'],before['selected'],wanted)
  require(S.values(after['selected']['nativeSnapshot'])==S.values(before['selected']['nativeSnapshot']),'Lawn native source vertices/UV0 changed')
  report['activeMaterialProof']=read_material(u,contract)
  require(S.values(report['activeMaterialProof'])==S.values(report['stagedMaterialProof']),'Saved active lawn material differs from staged proof')
  require(_asset_hashes(owned_paths)==owned_hashes,'Lawn assets changed after active reload')
  report.update(nativeApplied=not restore,selectedAfter=after['selected'],assetHashes=owned_hashes,protectedAssetHashes=after['world']['protectedAssetHashes'],verification={'nativeSourceVerticesUv0Compared':True,'geometryUvCollisionAndSourceAssetsUnchanged':True,'other1877SourceActorsUnchanged':True,'allGrassInstancesAndPolicyUnchanged':True,'sourceBaseMaterialRetained':True,'twoMapReloads':True,'twoOwnedAssetUnloadAbsenceReadbacks':True,'exactSavedGraphsEqual':True,'activeBindingVerified':True},sourcePreservationSnapshotSha256=S.digest(before['world']))
  write('lawn-ground-restored-saved-reload-validated' if restore else 'lawn-ground-saved-reload-validated');return report
 except Exception as error:
  message=str(error);error.__traceback__=None;report.update(error=message,nativeApplied=False,retainedOwnedPaths=sorted(owned_paths),retainedOwnedNamespace=contract['prefix'],partialOwnedAssetsMayExist=True);rollback=[]
  if before:
   try:
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    current=u.EditorLevelLibrary.get_editor_world().get_path_name().split('.')[0]
    if current!=MAP:require(levels.load_level(MAP),'Rollback could not load original map')
    if mutated:
     report['rollbackAttempted']=True;restore_failed_binding(u,contract,geometry,before);save_unload_reload(u,owned_paths)
    now=inspect(u,contract,geometry)
    require(S.values(now)==S.values(before),'Lawn original source state was not restored')
    report.update(rollbackVerified=mutated,sourceStateVerifiedOnFailure=True)
   except Exception as problem:
    rollback.append(str(problem));problem.__traceback__=None
  report.update(rollbackErrors=rollback);write('failed');raise RuntimeError(message+'; rollbackErrors='+str(rollback)) from None

def apply_lawn_ground(scene,geometry):return execute(scene,geometry)
def restore_lawn_ground(scene,geometry):return execute(scene,geometry,True)
