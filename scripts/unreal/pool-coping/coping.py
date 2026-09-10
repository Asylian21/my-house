"""28 reversible native pool coping component overrides; no native action on import."""
import gc,hashlib,importlib.util,json,math
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'lib/twin-site.ts').is_file())
OWNER='scripts/unreal/pool-coping/coping.py'
IDS=tuple(f'DOM_{i:05d}' for i in range(1726,1754)); EXCLUDED=tuple(f'DOM_{i:05d}' for i in range(1817,1821)); SLOT='MAT_0102'
BASE='/Game/Brezi/Geometry/brezi-twin/Materials/MAT_0102.MAT_0102'
MAP='/Game/Brezi/Maps/Brezi'; SCENE_SHA='61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b'; OBJ_SHA='a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455'
HELPERS=('scripts/unreal/tv-oak/tv_oak.py',*[f'scripts/unreal/lawn-ground/{n}.py' for n in ('lawn_ground','source','graph')],'unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.h','unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.cpp')

def require(ok,message):
 if not ok:raise RuntimeError(message)
def sha(p):
 p=Path(p);require(p.is_file() and p.resolve()==p,'Missing/symlinked coping input: '+str(p));return hashlib.sha256(p.read_bytes()).hexdigest()
def values(v):return json.loads(json.dumps(v,allow_nan=False))
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def module(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
G=module('brezi_pool_coping_graph',HERE/'graph.py')
_HELPER=None
def helper():
 global _HELPER
 if _HELPER is None:_HELPER=module('brezi_pool_coping_world_helpers',ROOT/'scripts/unreal/lawn-ground/lawn_ground.py')
 return _HELPER
def native_scope():require(Path(__file__).resolve()==ROOT/OWNER,'Output-only coping draft cannot mutate native assets')
def path(obj):return obj.get_path_name() if obj else None
def mesh_path(id_):return f'/Game/Brezi/Geometry/brezi-twin/StaticMeshes/{id_}.{id_}'

def check_scene(scene,ref):
 require(set(ref['sourceRecords'])==set(IDS),'Coping source recipe escaped exact28 IDs')
 rows={r['id']:r for r in scene['objects'] if r['id'] in IDS}
 require(rows==ref['sourceRecords'] and len([r for r in scene['objects'] if r['id'] in IDS])==28,'Coping exact source records changed')
 require(all(r['materialSlots']==[SLOT] and r['triangles']==12 and r['enabled'] is True and r['instances']==1 for r in rows.values()),'Coping source slot/topology differs')
 require(scene['materials'][SLOT]==ref['sourceMaterial'] and ref['sourceMaterial']['name']=='real-stone' and ref['sourceMaterial']['roughness']==.9,'Coping source material changed')
 require(sorted(r['id'] for r in scene['objects'] if SLOT in r['materialSlots'])==list(IDS+EXCLUDED) and ref['excludedSharedSlotIds']==list(EXCLUDED),'Coping shared-slot scope changed')
 return rows

def read_source(p):
 vertices=[];uvs=[];rows={i:[] for i in IDS};current=slot=None
 for line in Path(p).read_text().splitlines():
  a=line.split()
  if not a:continue
  if a[0]=='v':vertices.append(tuple(map(float,a[1:4])))
  elif a[0]=='vt':uvs.append(tuple(map(float,a[1:3])))
  elif a[0]=='o':current=a[1]
  elif a[0]=='usemtl':slot=a[1]
  elif a[0]=='f' and current in rows:
   require(len(a)==4 and slot==SLOT,'Coping OBJ topology/slot differs');refs=[tuple(map(int,x.split('/')[:2])) for x in a[1:]]
   require(all(v>0 and t>0 for v,t in refs),'Coping OBJ indices unsupported');rows[current].append([(vertices[v-1],(uvs[t-1][0],1-uvs[t-1][1])) for v,t in refs])
 require(all(len(rows[i])==12 for i in IDS),'Coping OBJ triangle count differs')
 # This shader is scoped to six planar box faces, not arbitrary curved meshes.
 for id_,faces in rows.items():
  directions={}
  for tri in faces:
   p=[v[0] for v in tri];a=[p[1][k]-p[0][k] for k in range(3)];b=[p[2][k]-p[0][k] for k in range(3)];n=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];length=math.sqrt(sum(x*x for x in n));require(length>0,'Degenerate coping face');n=[x/length for x in n];axis=max(range(3),key=lambda k:abs(n[k]));require(abs(abs(n[axis])-1)<1e-8 and all(abs(n[k])<1e-8 for k in range(3) if k!=axis),'Coping face is not source axis-aligned');key=(axis,1 if n[axis]>0 else -1);directions[key]=directions.get(key,0)+1
  require(directions=={(axis,sign):2 for axis in range(3) for sign in (-1,1)},'Coping six-face topology differs: '+id_)
 return rows

def verify_inputs(scene,geometry):
 geometry=Path(geometry);ref=json.loads((HERE/'inputs.json').read_text())
 require(ref['sceneSha256']==SCENE_SHA and ref['objSha256']==OBJ_SHA and sha(geometry/'scene.json')==SCENE_SHA and sha(geometry/'dom-mm.obj')==OBJ_SHA,'Coping source pins changed')
 require(values(scene)==json.loads((geometry/'scene.json').read_text()),'Coping supplied scene differs');rows=check_scene(scene,ref)
 require(ref['schemaVersion']==1 and ref['revision']=='POOL-COPING-PBR-1' and ref['source']['license']=='CC0-1.0' and ref['source']['measuredSiteMaterial'] is False and isinstance(ref['source']['physicalScaleProvenance'],str) and ref['source']['physicalScaleProvenance'],'Coping source/provenance policy differs')
 m=ref['material'];G.validate_parameters(m);require(m['tileMm']==ref['source']['tileMm'],'Coping declared mapping periods differ')
 require(set(ref['maps'])=={'Diffuse','nor_gl','Rough'},'Coping map roles differ')
 for role,v in ref['maps'].items():
  p=ROOT/v['path'];require(p.stat().st_size==v['bytes'] and sha(p)==v['sha256'] and hashlib.md5(p.read_bytes()).hexdigest()==v['md5'] and v['pixels']==[4096,4096],'Coping downloaded map differs: '+role)
 for n,h in ref['sourceIntentFiles'].items():require(sha(ROOT/n)==h,'Coping source builder changed')
 for n,h in ref['evidence'].items():require(sha(ROOT/n)==h,'Coping provider evidence changed')
 files={f'scripts/unreal/pool-coping/{n}':sha(HERE/n) for n in ('coping.py','graph.py','inputs.json')};files.update({n:sha(ROOT/n) for n in HELPERS})
 recipe={'reference':ref,'recipeInputs':files};serialized=json.dumps(recipe,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False);recipe_sha=digest(recipe);prefix=G.PREFIX+'/R_'+recipe_sha[:16]
 pipeline={**files,**ref['sourceIntentFiles'],**ref['evidence'],**{v['path']:v['sha256'] for v in ref['maps'].values()},'scripts/unreal/materials.py':sha(ROOT/'scripts/unreal/materials.py'),'scripts/unreal/pool-coping/package-gate.mjs':sha(HERE/'package-gate.mjs')}
 return {'reference':ref,'records':rows,'sourceFaces':read_source(geometry/'dom-mm.obj'),'recipe':recipe,'recipeCanonicalJson':serialized,'recipeSha256':recipe_sha,'pipelineFiles':pipeline,'candidate':{'maps':ref['maps']},'prefix':prefix,'materialPath':prefix+'/Materials/M_PoolCoping.M_PoolCoping'}

def binding_policy(current,effective,material,expected=None):
 if current==[]:require(effective==BASE and expected!='active','Pool coping canonical binding differs');return 'source'
 require(current==[material] and effective==material and expected!='source','Refusing foreign/untracked coping override');return 'active'

def native_guard(u,contract,expected=None,*,allow_failed_graph=False):
 h=helper();common=h.common();found=common.components(u,IDS);result={};graph_checked=False
 for id_ in IDS:
  a,c=found[id_];mesh=c.get_editor_property('static_mesh');require(a.actor_has_tag('BreziGenerated') and mesh is not None and path(mesh)==mesh_path(id_) and c.get_num_materials()==1 and len(mesh.get_editor_property('static_materials'))==1 and mesh.get_num_sections(0)==1 and mesh.get_num_triangles(0)>0 and mesh.get_num_tex_coords(0)==1,'Pool coping source mesh/slot/UV differs: '+id_)
  r=contract['records'][id_]
  for k,v in {'source_object_id':id_,'source_id':r['sourceId'],'source_group':r['group'],'source_name':r['name']}.items():require(u.EditorAssetLibrary.get_metadata_tag(mesh,k)==v,'Pool coping mesh source metadata differs: '+id_+'/'+k)
  require(h.transform(c.get_world_transform())=={'p':[0.,0.,0.],'q':[0.,0.,0.,1.],'s':[1.,1.,1.]},'Pool coping source transform differs')
  source=mesh.get_material(0);require(path(source)==BASE and str(mesh.get_editor_property('static_materials')[0].get_editor_property('material_slot_name'))==SLOT,'Pool coping canonical source material differs')
  overrides=common.overrides(c);effective=path(c.get_material(0));state=binding_policy(overrides,effective,contract['materialPath'],expected)
  if state=='active':
   if allow_failed_graph:G.identity(u,c.get_material(0),contract)
   elif not graph_checked:G.material_proof(u,c.get_material(0),contract,common);graph_checked=True
  snapshot=h.S.native_snapshot(u,mesh);proof=h.S.source_proof(snapshot,contract['sourceFaces'][id_])
  result[id_]={'state':state,'actor':path(a),'component':c.get_name(),'mesh':path(mesh),'meshMaterial':BASE,'effectiveMaterial':effective,'overrides':overrides,'nativeSnapshot':snapshot,'sourceProof':proof}
 return result

def snapshot_world(u):
 from materials import _asset_hashes
 world=helper().snapshot_world(u);paths={BASE}
 # Include LawnGround assets too; the reused reader excludes its own namespace.
 for actor in world['actors'].values():
  for c in actor['components']:
   paths.add(c['mesh']);paths.update(x for x in c['materials'] if x)
 paths={p for p in paths if p.startswith('/Game/Brezi/') and not p.startswith(G.PREFIX+'/')}
 world['protectedAssetHashes'].update(_asset_hashes(paths));world['protectedAssetHashes']={p:h for p,h in world['protectedAssetHashes'].items() if '/PoolCoping/' not in p}
 return world

def compare_world(before,after,selected,wanted):
 require(set(selected)==set(IDS) and set(wanted)==set(IDS),'Pool coping comparison escaped 28-source scope');expected=values(before)
 for id_ in IDS:
  s=selected[id_];c=[c for c in expected['actors'][s['actor']]['components'] if c['name']==s['component']];require(len(c)==1,'Pool coping snapshot target missing');c[0]['overrides']=list(wanted[id_]);c[0]['materials']=[wanted[id_][0] if wanted[id_] else BASE]
 require(values(after)==expected,'Pool coping changed protected source/actor/grass state');return True

def inspect(u,contract,expected=None):return {'selected':native_guard(u,contract,expected),'world':snapshot_world(u)}
def read_material(u,contract):return G.material_proof(u,u.load_object(None,contract['materialPath']),contract,helper().common())

def set_binding(u,contract,wanted):
 native_guard(u,contract);require(set(wanted)==set(IDS) and all(v in ([],[contract['materialPath']]) for v in wanted.values()),'Pool coping setter escaped scope')
 found=helper().common().components(u,IDS)
 for id_ in IDS:
  c=found[id_][1];helper().common().set_overrides(u,c,wanted[id_]);require(path(c.get_material(0))==(wanted[id_][0] if wanted[id_] else BASE),'Pool coping setter readback differs')

def restore_failed_binding(u,contract,before):
 current=native_guard(u,contract,allow_failed_graph=True)
 for id_ in IDS:
  for key in ('actor','component','mesh','meshMaterial','nativeSnapshot','sourceProof'):require(values(current[id_][key])==values(before['selected'][id_][key]),'Pool coping rollback source identity differs')
 compare_world(before['world'],snapshot_world(u),before['selected'],{i:current[i]['overrides'] for i in IDS})
 wanted={i:before['selected'][i]['overrides'] for i in IDS};require(all(v in ([],[contract['materialPath']]) for v in wanted.values()),'Pool coping rollback prior binding differs')
 if any(wanted.values()):read_material(u,contract)
 found=helper().common().components(u,IDS)
 for id_ in IDS:
  a,c=found[id_];require(path(a)==before['selected'][id_]['actor'] and c.get_name()==before['selected'][id_]['component'],'Pool coping rollback selection changed');helper().common().set_overrides(u,c,wanted[id_]);require(path(c.get_material(0))==(wanted[id_][0] if wanted[id_] else BASE),'Pool coping rollback readback differs')

def save_unload_reload(u,owned):
 levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(levels.save_current_level(),'Pool coping map save failed');require(u.EditorLoadingAndSavingUtils.new_blank_map(False),'Pool coping world unload failed');gc.collect();packages=[]
 for p in sorted(owned):
  require(p.startswith(G.PREFIX+'/'),'Pool coping package unload escaped scope');obj=u.find_object(None,p)
  if obj:
   require(u.EditorAssetLibrary.get_metadata_tag(obj,'BreziGeneratedBy')==OWNER,'Pool coping package owner differs');package=obj.get_outermost();require(package.get_path_name()==p.split('.')[0],'Pool coping package path differs');packages.append(package);del package
  del obj
 if packages:
  result=u.EditorLoadingAndSavingUtils.unload_packages(packages);require(isinstance(result,tuple) and len(result)==2 and result[0] is True and not str(result[1]),'Pool coping package unload failed: '+str(result))
 del packages;gc.collect();require(all(u.find_object(None,p) is None for p in owned),'Pool coping saved asset absence not proved');require(levels.load_level(MAP),'Pool coping saved map load failed')
 return {'mapSaved':True,'worldUnloaded':True,'allFourOwnedAssetsAbsentBeforeReload':True,'mapReloaded':True}

def preflight_reimport(u,actors,scene,geometry):
 native_scope();contract=verify_inputs(scene,geometry);selected=[a for a in actors if any(a.actor_has_tag(i) for i in IDS)]
 if not selected:return None
 require(len(selected)==28 and all(a.actor_has_tag('BreziGenerated') for a in selected),'Pool coping duplicate/foreign pre-existing actors');return native_guard(u,contract)

def execute(scene,geometry,restore=False):
 native_scope()
 import unreal as u
 from materials import _asset_hashes
 require(Path(u.Paths.project_dir()).resolve()==ROOT/'unreal/BreziTwin','Pool coping unexpected project');contract=verify_inputs(scene,geometry);report_path=Path(geometry).parent/('pool-coping-restore-report.json' if restore else 'pool-coping-report.json')
 report={'status':'pending','nativeApplied':False,'restoring':restore,'selectedIds':list(IDS),'sourceMaterialSlot':SLOT,'excludedSharedSlotIds':list(EXCLUDED),'sourceManifestSha256':SCENE_SHA,'sourceObjSha256':OBJ_SHA,'recipeSha256':contract['recipeSha256'],'recipe':contract['recipe'],'recipeCanonicalJson':contract['recipeCanonicalJson'],'pipelineFiles':contract['pipelineFiles'],'activationStarted':False,'actorMetadataWritten':False,'renderedVerified':False,'rollbackAttempted':False,'rollbackVerified':False,'rollbackErrors':[]}
 before=None;owned=set();mutated=False
 def write(status):
  report.update(status=status,generatedAt=datetime.now(timezone.utc).isoformat());tmp=report_path.with_suffix('.tmp');tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(report_path)
 try:
  before=inspect(u,contract,'active' if restore else None);report.update(selectedBefore=before['selected'],grassInstanceCount=before['world']['grassInstanceCount']);require(before['world']['grassInstanceCount']==33769,'Pool coping requires complete LawnDetail stage')
  if restore:
   proof=read_material(u,contract);owned={contract['materialPath'],*[v['asset'] for v in proof['textures'].values()]}
  else:material_path,owned=G.create_material(u,contract,helper().common())
  require(len(owned)==4,'Pool coping requires material plus three maps');hashes=_asset_hashes(owned);report['stagedReload']=save_unload_reload(u,owned)
  require(values(inspect(u,contract))==values(before),'Pool coping source changed before activation');report['stagedMaterialProof']=read_material(u,contract);require(_asset_hashes(owned)==hashes,'Pool coping staged asset bytes changed')
  wanted={i:[] if restore else [contract['materialPath']] for i in IDS};mutated=True;report['activationStarted']=True;set_binding(u,contract,wanted);report['activeReload']=save_unload_reload(u,owned)
  after=inspect(u,contract,'source' if restore else 'active');compare_world(before['world'],after['world'],before['selected'],wanted)
  for id_ in IDS:
   for k in ('nativeSnapshot','sourceProof'):require(values(before['selected'][id_][k])==values(after['selected'][id_][k]),'Pool coping source vertex/UV readback changed')
  report['activeMaterialProof']=read_material(u,contract);require(values(report['activeMaterialProof'])==values(report['stagedMaterialProof']) and _asset_hashes(owned)==hashes,'Pool coping active saved graph/assets differ')
  report.update(nativeApplied=not restore,selectedAfter=after['selected'],assetHashes=hashes,protectedAssetHashes=after['world']['protectedAssetHashes'],sourcePreservationSnapshotSha256=digest(before['world']),verification={k:True for k in ('exact28Bindings','sourceVerticesUv0Unchanged','allOtherActorsAndGrassUnchanged','sourceBaseMaterialRetained','twoMapReloads','twoOwnedAssetUnloadAbsenceReadbacks','exactSavedGraphsEqual')})
  write('pool-coping-restored-saved-reload-validated' if restore else 'pool-coping-saved-reload-validated');return report
 except Exception as error:
  message=str(error);error.__traceback__=None;report.update(error=message,nativeApplied=False,retainedOwnedPaths=sorted(owned),partialOwnedAssetsMayExist=True);errors=[]
  if before:
   try:
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    if u.EditorLevelLibrary.get_editor_world().get_path_name().split('.')[0]!=MAP:require(levels.load_level(MAP),'Pool coping rollback map load failed')
    if mutated:report['rollbackAttempted']=True;restore_failed_binding(u,contract,before);save_unload_reload(u,owned)
    require(values(inspect(u,contract))==values(before),'Pool coping original state not restored');report.update(rollbackVerified=mutated,sourceStateVerifiedOnFailure=True)
   except Exception as problem:errors.append(str(problem));problem.__traceback__=None
  report['rollbackErrors']=errors;write('failed');raise RuntimeError(message+'; rollbackErrors='+str(errors)) from None

def apply_pool_coping(scene,geometry):return execute(scene,geometry)
def restore_pool_coping(scene,geometry):return execute(scene,geometry,True)

def retain_source(scene,geometry):
 """Default/source-only path: no authoring or setters; prove saved bindings."""
 native_scope()
 import unreal as u
 require(Path(u.Paths.project_dir()).resolve()==ROOT/'unreal/BreziTwin','Pool coping unexpected project');contract=verify_inputs(scene,geometry);before=inspect(u,contract,'source');require(before['world']['grassInstanceCount']==33769,'Pool coping requires complete LawnDetail stage')
 reload=save_unload_reload(u,set());after=inspect(u,contract,'source');require(values(after)==values(before),'Pool coping source changed across saved-map reload')
 return {'status':'source-pool-coping-retained','nativeApplied':False,'restoring':False,'selectedIds':list(IDS),'sourceMaterialSlot':SLOT,'excludedSharedSlotIds':list(EXCLUDED),'sourceManifestSha256':SCENE_SHA,'sourceObjSha256':OBJ_SHA,'recipeSha256':contract['recipeSha256'],'recipe':contract['recipe'],'recipeCanonicalJson':contract['recipeCanonicalJson'],'pipelineFiles':contract['pipelineFiles'],'sourceOverridesRetained':28,'candidateOverridesActive':0,'sourceObjectsDeleted':0,'actorMetadataWritten':False,'selectedBefore':before['selected'],'selectedAfter':after['selected'],'sourceReload':{k:reload[k] for k in ('mapSaved','worldUnloaded','mapReloaded')},'sourceStateUnchangedAfterReload':True,'sourcePreservationSnapshotSha256':digest(before['world']),'grassInstanceCount':after['world']['grassInstanceCount'],'protectedAssetHashes':after['world']['protectedAssetHashes'],'assetHashes':{},'rollbackErrors':[],'renderedVerified':False,'sourceMaterialNativeParameterReadback':False}
