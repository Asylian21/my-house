"""66 reversible exterior plaster component overrides; no native action on import."""
import gc,hashlib,importlib.util,json,math
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'lib/twin-site.ts').is_file())
OWNER='scripts/unreal/facade-plaster/plaster.py'
IDS=('DOM_00060', 'DOM_00068', 'DOM_00069', 'DOM_00070', 'DOM_00071', 'DOM_00072', 'DOM_00073', 'DOM_00074', 'DOM_00075', 'DOM_00076', 'DOM_00077', 'DOM_00078', 'DOM_00079', 'DOM_00080', 'DOM_00081', 'DOM_00082', 'DOM_00083', 'DOM_00084', 'DOM_00085', 'DOM_00086', 'DOM_00087', 'DOM_00088', 'DOM_00089', 'DOM_00090', 'DOM_00091', 'DOM_00092', 'DOM_00093', 'DOM_00094', 'DOM_00095', 'DOM_00096', 'DOM_00097', 'DOM_00098', 'DOM_00099', 'DOM_00100', 'DOM_00101', 'DOM_00102', 'DOM_00103', 'DOM_00104', 'DOM_00105', 'DOM_00106', 'DOM_00107', 'DOM_00108', 'DOM_00109', 'DOM_00110', 'DOM_00111', 'DOM_00112', 'DOM_00113', 'DOM_00114', 'DOM_00115', 'DOM_00116', 'DOM_00117', 'DOM_00118', 'DOM_00119', 'DOM_00120', 'DOM_00121', 'DOM_00122', 'DOM_00123', 'DOM_00124', 'DOM_00125', 'DOM_00139', 'DOM_00146', 'DOM_00148', 'DOM_00150', 'DOM_00152', 'DOM_00160', 'DOM_00161'); SLOT='MAT_0010'
BASE='/Game/Brezi/MaterialsGenerated/M_MAT_0010.M_MAT_0010'
MAP='/Game/Brezi/Maps/Brezi'; SCENE_SHA='61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b'; OBJ_SHA='a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455'
HELPERS=('scripts/unreal/tv-oak/tv_oak.py',*[f'scripts/unreal/lawn-ground/{n}.py' for n in ('lawn_ground','source','graph')],'unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.h','unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.cpp')

def require(ok,message):
 if not ok:raise RuntimeError(message)
def sha(p):
 p=Path(p);require(p.is_file() and p.resolve()==p,'Missing/symlinked plaster input: '+str(p));return hashlib.sha256(p.read_bytes()).hexdigest()
def values(v):return json.loads(json.dumps(v,allow_nan=False))
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def module(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
PREFIX='/Game/Brezi/MaterialStudies/FacadePlaster'
WRITER_SHA='4f588f2825f555febade35e736663348f94ca0c37e836cc87ca1d7e15b5a15ed'
RECIPE_TAG='BreziFacadePlasterRecipe'
STRENGTH=.5
_HELPER=None
def helper():
 global _HELPER
 if _HELPER is None:_HELPER=module('brezi_plaster_world_helpers',ROOT/'scripts/unreal/lawn-ground/lawn_ground.py')
 return _HELPER
def native_scope():require(Path(__file__).resolve()==ROOT/OWNER,'Noncanonical plaster helper cannot mutate native assets')
def path(obj):return obj.get_path_name() if obj else None
def mesh_path(id_):return f'/Game/Brezi/Geometry/brezi-twin/StaticMeshes/{id_}.{id_}'

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
   require(len(a)==4 and slot==SLOT,'Plaster OBJ topology/slot differs');refs=[tuple(map(int,x.split('/')[:2])) for x in a[1:]]
   require(all(v>0 and t>0 for v,t in refs),'Plaster OBJ indices unsupported');rows[current].append([(vertices[v-1],(uvs[t-1][0],1-uvs[t-1][1])) for v,t in refs])
 return rows

def verify_inputs(scene,geometry):
 geometry=Path(geometry)
 require(sha(geometry/'scene.json')==SCENE_SHA and sha(geometry/'dom-mm.obj')==OBJ_SHA,'Plaster source geometry pin changed')
 require(values(scene)==json.loads((geometry/'scene.json').read_text()),'Plaster supplied scene differs')
 rows=[r for r in scene['objects'] if SLOT in r['materialSlots']]
 require(tuple(r['id'] for r in rows)==IDS and len(IDS)==66 and all(r['materialSlots']==[SLOT] and r['enabled'] is True and r['instances']==1 for r in rows),'Plaster exact exterior scope differs')
 require(scene['materials'][SLOT]['name']=='real-wall' and sha(ROOT/'scripts/unreal/materials.py')==WRITER_SHA,'Plaster base material/writer changed')
 faces=read_source(geometry/'dom-mm.obj');require(all(len(faces[r['id']])==r['triangles'] for r in rows),'Plaster source face count differs')
 files={n:sha(ROOT/n) for n in (OWNER,'scripts/unreal/materials.py',*HELPERS)}
 recipe={'revision':'FACADE-PLASTER-NORMAL-1','selectedIds':list(IDS),'sourceManifestSha256':SCENE_SHA,'sourceObjSha256':OBJ_SHA,'baseMaterial':BASE,'normalStrengthBefore':.2,'normalStrength':STRENGTH,'artistNormalWeightNotMeasured':True,'recipeInputs':files}
 serialized=json.dumps(recipe,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False);recipe_sha=digest(recipe);prefix=PREFIX+'/R_'+recipe_sha[:16]
 pipeline={**files,'scripts/unreal/facade-plaster/package-gate.mjs':sha(HERE/'package-gate.mjs')}
 return {'records':{r['id']:r for r in rows},'sourceFaces':faces,'recipe':recipe,'recipeCanonicalJson':serialized,'recipeSha256':recipe_sha,'pipelineFiles':pipeline,'prefix':prefix,'materialPath':prefix+'/M_Plaster.M_Plaster'}

def binding_policy(current,effective,material,expected=None):
 if current==[]:require(effective==BASE and expected!='active','Plaster canonical binding differs');return 'source'
 require(current==[material] and effective==material and expected!='source','Refusing foreign/untracked plaster override');return 'active'

def native_guard(u,contract,expected=None,*,allow_failed_graph=False):
 h=helper();common=h.common();found=common.components(u,IDS);result={};graph_checked=False
 for id_ in IDS:
  a,c=found[id_];mesh=c.get_editor_property('static_mesh');require(a.actor_has_tag('BreziGenerated') and mesh is not None and path(mesh)==mesh_path(id_) and c.get_num_materials()==1 and len(mesh.get_editor_property('static_materials'))==1 and mesh.get_num_sections(0)==1 and mesh.get_num_triangles(0)>0 and mesh.get_num_tex_coords(0)==1,'Plaster source mesh/slot/UV differs: '+id_)
  r=contract['records'][id_]
  for k,v in {'source_object_id':id_,'source_id':r['sourceId'],'source_group':r['group'],'source_name':r['name']}.items():require(u.EditorAssetLibrary.get_metadata_tag(mesh,k)==v,'Plaster mesh source metadata differs: '+id_+'/'+k)
  require(h.transform(c.get_world_transform())=={'p':[0.,0.,0.],'q':[0.,0.,0.,1.],'s':[1.,1.,1.]},'Plaster source transform differs')
  source=mesh.get_material(0);require(path(source)==BASE and str(mesh.get_editor_property('static_materials')[0].get_editor_property('material_slot_name'))==SLOT,'Plaster canonical source material differs')
  overrides=common.overrides(c);effective=path(c.get_material(0));state=binding_policy(overrides,effective,contract['materialPath'],expected)
  if state=='active':
   if allow_failed_graph:identity(u,c.get_material(0),contract)
   elif not graph_checked:material_proof(u,c.get_material(0),contract);graph_checked=True
  snapshot=h.S.native_snapshot(u,mesh);proof=h.S.source_proof(snapshot,contract['sourceFaces'][id_])
  result[id_]={'state':state,'actor':path(a),'component':c.get_name(),'mesh':path(mesh),'meshMaterial':BASE,'effectiveMaterial':effective,'overrides':overrides,'nativeSnapshot':snapshot,'sourceProof':proof}
 return result

def snapshot_world(u):
 from materials import _asset_hashes
 world=helper().snapshot_world(u);paths=set()
 # Include LawnGround assets too; the reused reader excludes its own namespace.
 for actor in world['actors'].values():
  for c in actor['components']:
   paths.add(c['mesh']);paths.update(x for x in c['materials'] if x)
 paths={p for p in paths if p.startswith('/Game/Brezi/') and not p.startswith(PREFIX+'/')}
 world['protectedAssetHashes'].update(_asset_hashes(paths));world['protectedAssetHashes'].update(base_graph(u)['textureAssetHashes']);world['protectedAssetHashes']={p:h for p,h in world['protectedAssetHashes'].items() if '/MaterialStudies/FacadePlaster/' not in p}
 return world

def compare_world(before,after,selected,wanted):
 require(set(selected)==set(IDS) and set(wanted)==set(IDS),'Plaster comparison escaped 66-source scope');expected=values(before)
 for id_ in IDS:
  s=selected[id_];c=[c for c in expected['actors'][s['actor']]['components'] if c['name']==s['component']];require(len(c)==1,'Plaster snapshot target missing');c[0]['overrides']=list(wanted[id_]);c[0]['materials']=[wanted[id_][0] if wanted[id_] else BASE]
 require(values(after)==expected,'Plaster changed protected source/actor/grass state');return True

def inspect(u,contract,expected=None):return {'selected':native_guard(u,contract,expected),'world':snapshot_world(u)}
def read_material(u,contract):return material_proof(u,u.load_object(None,contract['materialPath']),contract)

def set_binding(u,contract,wanted):
 native_guard(u,contract);require(set(wanted)==set(IDS) and all(v in ([],[contract['materialPath']]) for v in wanted.values()),'Plaster setter escaped scope')
 found=helper().common().components(u,IDS)
 for id_ in IDS:
  c=found[id_][1];helper().common().set_overrides(u,c,wanted[id_]);require(path(c.get_material(0))==(wanted[id_][0] if wanted[id_] else BASE),'Plaster setter readback differs')

def restore_failed_binding(u,contract,before):
 current=native_guard(u,contract,allow_failed_graph=True)
 for id_ in IDS:
  for key in ('actor','component','mesh','meshMaterial','nativeSnapshot','sourceProof'):require(values(current[id_][key])==values(before['selected'][id_][key]),'Plaster rollback source identity differs')
 compare_world(before['world'],snapshot_world(u),before['selected'],{i:current[i]['overrides'] for i in IDS})
 wanted={i:before['selected'][i]['overrides'] for i in IDS};require(all(v in ([],[contract['materialPath']]) for v in wanted.values()),'Plaster rollback prior binding differs')
 if any(wanted.values()):read_material(u,contract)
 found=helper().common().components(u,IDS)
 for id_ in IDS:
  a,c=found[id_];require(path(a)==before['selected'][id_]['actor'] and c.get_name()==before['selected'][id_]['component'],'Plaster rollback selection changed');helper().common().set_overrides(u,c,wanted[id_]);require(path(c.get_material(0))==(wanted[id_][0] if wanted[id_] else BASE),'Plaster rollback readback differs')

def save_unload_reload(u,owned):
 levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(levels.save_current_level(),'Plaster map save failed');require(u.EditorLoadingAndSavingUtils.new_blank_map(False),'Plaster world unload failed');gc.collect();packages=[]
 for p in sorted(owned):
  require(p.startswith(PREFIX+'/'),'Plaster package unload escaped scope');obj=u.find_object(None,p)
  if obj:
   require(u.EditorAssetLibrary.get_metadata_tag(obj,'BreziGeneratedBy')==OWNER,'Plaster package owner differs');package=obj.get_outermost();require(package.get_path_name()==p.split('.')[0],'Plaster package path differs');packages.append(package);del package
  del obj
 if packages:
  result=u.EditorLoadingAndSavingUtils.unload_packages(packages);require(isinstance(result,tuple) and len(result)==2 and result[0] is True and not str(result[1]),'Plaster package unload failed: '+str(result))
 del packages;gc.collect();require(all(u.find_object(None,p) is None for p in owned),'Plaster saved asset absence not proved');require(levels.load_level(MAP),'Plaster saved map load failed')
 return {'mapSaved':True,'worldUnloaded':True,'ownedMaterialAbsentBeforeReload':True,'mapReloaded':True}

def preflight_reimport(u,actors,scene,geometry):
 native_scope();contract=verify_inputs(scene,geometry);selected=[a for a in actors if any(a.actor_has_tag(i) for i in IDS)]
 if not selected:return None
 require(len(selected)==66 and all(a.actor_has_tag('BreziGenerated') for a in selected),'Plaster duplicate/foreign pre-existing actors');return native_guard(u,contract)

def execute(scene,geometry,restore=False):
 native_scope()
 import unreal as u
 from materials import _asset_hashes
 require(Path(u.Paths.project_dir()).resolve()==ROOT/'unreal/BreziTwin','Plaster unexpected project');contract=verify_inputs(scene,geometry);report_path=Path(geometry).parent/('facade-plaster-restore-report.json' if restore else 'facade-plaster-report.json')
 report={'status':'pending','nativeApplied':False,'restoring':restore,'selectedIds':list(IDS),'sourceMaterialSlot':SLOT,'normalStrength':STRENGTH,'normalStrengthBefore':.2,'artistNormalWeightNotMeasured':True,'sourceManifestSha256':SCENE_SHA,'sourceObjSha256':OBJ_SHA,'recipeSha256':contract['recipeSha256'],'recipe':contract['recipe'],'recipeCanonicalJson':contract['recipeCanonicalJson'],'pipelineFiles':contract['pipelineFiles'],'activationStarted':False,'actorMetadataWritten':False,'renderedVerified':False,'rollbackAttempted':False,'rollbackVerified':False,'rollbackErrors':[]}
 before=None;owned=set();mutated=False
 def write(status):
  report.update(status=status,generatedAt=datetime.now(timezone.utc).isoformat());tmp=report_path.with_suffix('.tmp');tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(report_path)
 try:
  before=inspect(u,contract,'active' if restore else None);report.update(selectedBefore=before['selected'],grassInstanceCount=before['world']['grassInstanceCount']);require(before['world']['grassInstanceCount']==33769,'Plaster requires complete LawnDetail stage')
  if restore:
   read_material(u,contract);owned={contract['materialPath']}
  else:owned=create_material(u,contract)
  require(owned=={contract['materialPath']},'Plaster owns only one duplicated material');hashes=_asset_hashes(owned);report['stagedReload']=save_unload_reload(u,owned)
  require(values(inspect(u,contract))==values(before),'Plaster source changed before activation');report['stagedMaterialProof']=read_material(u,contract);require(_asset_hashes(owned)==hashes,'Plaster staged asset bytes changed')
  wanted={i:[] if restore else [contract['materialPath']] for i in IDS};mutated=True;report['activationStarted']=True;set_binding(u,contract,wanted);report['activeReload']=save_unload_reload(u,owned)
  after=inspect(u,contract,'source' if restore else 'active');compare_world(before['world'],after['world'],before['selected'],wanted)
  for id_ in IDS:
   for k in ('nativeSnapshot','sourceProof'):require(values(before['selected'][id_][k])==values(after['selected'][id_][k]),'Plaster source vertex/UV readback changed')
  report['activeMaterialProof']=read_material(u,contract);require(values(report['activeMaterialProof'])==values(report['stagedMaterialProof']) and _asset_hashes(owned)==hashes,'Plaster active saved graph/assets differ')
  report.update(nativeApplied=not restore,selectedAfter=after['selected'],assetHashes=hashes,protectedAssetHashes=after['world']['protectedAssetHashes'],sourcePreservationSnapshotSha256=digest(before['world']),verification={k:True for k in ('exact66Bindings','sourceVerticesUv0Unchanged','allOtherActorsAndGrassUnchanged','sourceBaseMaterialRetained','twoMapReloads','twoOwnedMaterialUnloadAbsenceReadbacks','exactSavedGraphsEqual')})
  write('plaster-restored-saved-reload-validated' if restore else 'plaster-saved-reload-validated');return report
 except Exception as error:
  message=str(error);error.__traceback__=None;report.update(error=message,nativeApplied=False,retainedOwnedPaths=sorted(owned),partialOwnedAssetsMayExist=True);errors=[]
  if before:
   try:
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    if u.EditorLevelLibrary.get_editor_world().get_path_name().split('.')[0]!=MAP:require(levels.load_level(MAP),'Plaster rollback map load failed')
    if mutated:report['rollbackAttempted']=True;restore_failed_binding(u,contract,before);save_unload_reload(u,owned)
    require(values(inspect(u,contract))==values(before),'Plaster original state not restored');report.update(rollbackVerified=mutated,sourceStateVerifiedOnFailure=True)
   except Exception as problem:errors.append(str(problem));problem.__traceback__=None
  report['rollbackErrors']=errors;write('failed');raise RuntimeError(message+'; rollbackErrors='+str(errors)) from None

def apply_plaster(scene,geometry):return execute(scene,geometry)
def restore_plaster(scene,geometry):return execute(scene,geometry,True)

# Closed graph vocabulary of the pinned shared writer; unknown nodes fail before duplication.
NODE_PROPERTIES={
 'MaterialExpressionTextureObject':('texture','sampler_type'),
 'MaterialExpressionMaterialFunctionCall':('material_function',),
 'MaterialExpressionConstant3Vector':('constant',),
 'MaterialExpressionConstant':('r',),
 'MaterialExpressionLinearInterpolate':('const_a','const_b','const_alpha'),
 'MaterialExpressionComponentMask':('r','g','b','a'),
 'MaterialExpressionVertexNormalWS':(), 'MaterialExpressionNormalize':(),
}
def output_string(v):
 if isinstance(v,tuple) and len(v)==2 and v[0] is True:v=v[1]
 require(isinstance(v,str),'Plaster native output getter unavailable');return v

def canonical_graph(graph):
 """Ignore only transient UObject names; preserve directed edges and shared-node identity."""
 result=values(graph);nodes=result['nodes'];ids={};ordered={};visiting=set()
 require(isinstance(nodes,dict) and nodes and isinstance(result['outputs'],dict),'Plaster graph structure absent')
 def visit(name):
  require(name in nodes,'Plaster dangling expression reference')
  require(name not in visiting,'Plaster cyclic expression graph')
  if name in ids:return ids[name]
  stable='node_'+str(len(ids));ids[name]=stable;visiting.add(name);node=nodes[name];links=node['inputs']
  require(isinstance(links,list) and len({v['pin'] for v in links})==len(links),'Plaster ambiguous input pins')
  for link in links:
   require(set(link)=={'pin','node','output'} and isinstance(link['pin'],str),'Plaster input structure differs')
   if link['node'] is None:require(link['output'] is None,'Plaster disconnected input has an output channel')
   else:
    require(isinstance(link['output'],str),'Plaster edge output channel missing');link['node']=visit(link['node'])
  visiting.remove(name);ordered[stable]=node;return stable
 for prop,link in sorted(result['outputs'].items()):
  require(isinstance(prop,str),'Plaster output property missing')
  if link is not None:
   require(isinstance(link,list) and len(link)==2 and isinstance(link[1],str),'Plaster material output structure differs');link[0]=visit(link[0])
 require(set(ids)==set(nodes) and result['normalMix'] in ids,'Plaster disconnected/missing expression or normal lerp')
 result['nodes']=ordered;result['normalMix']=ids[result['normalMix']];result['nodeIdentity']='material-output-input-traversal-v1'
 return result

def graph_snapshot(u,m):
 require(isinstance(m,u.Material),'Plaster requires native Material');lib=u.MaterialEditingLibrary
 expressions=list(lib.get_material_expressions(m));require(len(expressions)==16,'Plaster pinned graph requires 16 nodes');nodes={};textures=set()
 for n in expressions:
  cls=n.get_class().get_name();require(cls in NODE_PROPERTIES and n.get_name() not in nodes,'Plaster unknown/duplicate expression: '+cls);props={}
  for k in NODE_PROPERTIES[cls]:
   value=n.get_editor_property(k)
   if k in ('texture','material_function'):
    require(value is not None,'Plaster missing source texture/function');props[k]=path(value)
    if k=='texture':textures.add(path(value))
   elif k=='constant':props[k]=[float(getattr(value,c)) for c in ('r','g','b','a')]
   elif k=='sampler_type':props[k]=str(value)
   else:props[k]=value
  names=list(map(str,lib.get_material_expression_input_names(n)));origins=list(lib.get_inputs_for_material_expression(m,n));require(len(names)==len(origins),'Plaster native input-name alignment differs');inputs=[]
  for name,origin in zip(names,origins):
   require(origin is None or origin in expressions,'Plaster graph escaped expression set')
   inputs.append({'pin':name,'node':origin.get_name() if origin else None,'output':output_string(lib.get_input_node_output_name_for_material_expression(n,origin)) if origin else None})
  nodes[n.get_name()]={'class':cls,'properties':props,'inputs':inputs,'outputs':list(map(str,lib.get_material_expression_output_names(n)))}
 properties={};connected={}
 for name in ('BASE_COLOR','METALLIC','SPECULAR','ROUGHNESS','ANISOTROPY','NORMAL','TANGENT','WORLD_POSITION_OFFSET','SUBSURFACE_COLOR','OPACITY','OPACITY_MASK','EMISSIVE_COLOR','AMBIENT_OCCLUSION','REFRACTION','MATERIAL_ATTRIBUTES'):
  prop=getattr(u.MaterialProperty,'MP_'+name);n=lib.get_material_property_input_node(m,prop)
  properties[name]=[n.get_name(),output_string(lib.get_material_property_input_node_output_name(m,prop))] if n else None
  if n:connected[name]=n
 require(set(connected)=={'BASE_COLOR','METALLIC','ROUGHNESS','NORMAL'} and u.BreziRendererSettingsAudit.has_no_pixel_depth_offset_connection(m),'Plaster unexpected material output')
 normal=connected['NORMAL'];require(isinstance(normal,u.MaterialExpressionNormalize),'Plaster MP_NORMAL is not Normalize');inputs=[n for n in lib.get_inputs_for_material_expression(m,normal) if n is not None];require(len(inputs)==1 and isinstance(inputs[0],u.MaterialExpressionLinearInterpolate),'Plaster Normalize input is not Lerp');mix=inputs[0]
 links={x['pin']:x['node'] for x in nodes[mix.get_name()]['inputs']};require(set(links)=={'A','B','Alpha'} and links['Alpha'] is None and nodes[links['A']]['class']=='MaterialExpressionVertexNormalWS' and nodes[links['B']]['class']=='MaterialExpressionMaterialFunctionCall' and nodes[links['B']]['properties']['material_function'].endswith('/WorldAlignedNormal.WorldAlignedNormal'),'Plaster normal lerp inputs differ')
 settings={k:str(m.get_editor_property(k)) if k in ('blend_mode','shading_model') else m.get_editor_property(k) for k in ('blend_mode','shading_model','two_sided','tangent_space_normal','use_material_attributes')}
 require(m.get_editor_property('blend_mode')==u.BlendMode.BLEND_OPAQUE and m.get_editor_property('shading_model')==u.MaterialShadingModel.MSM_DEFAULT_LIT and settings['two_sided'] is False and settings['tangent_space_normal'] is False and settings['use_material_attributes'] is False,'Plaster base rendering settings differ')
 settings['naniteUsage']=bool(lib.has_material_usage(m,u.MaterialUsage.MATUSAGE_NANITE));require(settings['naniteUsage'],'Plaster Nanite usage absent')
 color=connected['BASE_COLOR'];require(isinstance(color,u.MaterialExpressionLinearInterpolate) and abs(float(color.get_editor_property('const_alpha'))-.15)<1e-6,'Plaster existing 85/15 color mix differs')
 tiles=[n['properties']['constant'][:3] for n in nodes.values() if n['class']=='MaterialExpressionConstant3Vector'];require(tiles.count([100.,100.,100.])==3,'Plaster existing 1m world map scale differs')
 require(len(textures)==3,'Plaster existing texture set differs')
 from materials import _asset_hashes
 return canonical_graph({'nodes':nodes,'outputs':properties,'settings':settings,'normalMix':mix.get_name(),'textureAssets':sorted(textures),'textureAssetHashes':_asset_hashes(textures)})

def assert_only_normal_changed(before,after):
 expected=values(before);name=expected['normalMix'];require(abs(float(expected['nodes'][name]['properties']['const_alpha'])-.2)<1e-6,'Plaster source normal weight differs')
 expected['nodes'][name]['properties']['const_alpha']=STRENGTH
 require(values(after)==expected,'Plaster duplicate graph differs beyond the sole normal lerp weight');return True

def base_graph(u):
 m=u.load_object(None,BASE);require(m is not None,'Plaster base material absent')
 for k,v in {'BreziGeneratedBy':'scripts/unreal/materials.py','source_material_slot':SLOT,'writer_sha256':WRITER_SHA}.items():require(u.EditorAssetLibrary.get_metadata_tag(m,k)==v,'Plaster source material identity differs: '+k)
 return graph_snapshot(u,m)

def identity(u,m,contract):
 require(isinstance(m,u.Material) and path(m)==contract['materialPath'] and path(m).startswith(PREFIX+'/R_'),'Plaster owned material path/type differs')
 for k,v in {'BreziGeneratedBy':OWNER,RECIPE_TAG:contract['recipeSha256'],'source_material_slot':SLOT,'BreziPlasterSourceMaterial':BASE}.items():require(u.EditorAssetLibrary.get_metadata_tag(m,k)==v,'Plaster owned material identity differs: '+k)

def material_proof(u,m,contract):
 identity(u,m,contract);before=base_graph(u);after=graph_snapshot(u,m);assert_only_normal_changed(before,after)
 return {'asset':path(m),'recipeSha256':contract['recipeSha256'],'normalStrength':STRENGTH,'sourceNormalStrength':.2,'nodeCount':16,'textureObjectCount':3,'albedoSourceMix':.15,'worldTileCm':100,'onlyNormalLerpWeightChanged':True,'nativeGraphGetterVerified':True,'worldSpaceNormal':True,'artistNormalWeightNotMeasured':True,'sourceGraph':before,'savedGraph':after,'renderedVerified':False}

def create_material(u,contract):
 source=base_graph(u);a=u.EditorAssetLibrary;destination=contract['materialPath'];package=destination.split('.')[0]
 if a.does_asset_exist(package):material_proof(u,a.load_asset(package),contract);return {destination}
 m=a.duplicate_asset(BASE.split('.')[0],package);require(m is not None and path(m)==destination,'Plaster material duplication failed')
 for k,v in {'BreziGeneratedBy':OWNER,RECIPE_TAG:contract['recipeSha256'],'source_material_slot':SLOT,'BreziPlasterSourceMaterial':BASE}.items():a.set_metadata_tag(m,k,v)
 require(graph_snapshot(u,m)==source,'Plaster duplicate does not match source before change')
 normal=u.MaterialEditingLibrary.get_material_property_input_node(m,u.MaterialProperty.MP_NORMAL)
 matches=[n for n in u.MaterialEditingLibrary.get_inputs_for_material_expression(m,normal) if n is not None];require(len(matches)==1 and isinstance(matches[0],u.MaterialExpressionLinearInterpolate),'Plaster exact normal lerp absent')
 matches[0].set_editor_property('const_alpha',STRENGTH)
 errors=list(u.MaterialEditingLibrary.recompile_material(m));require(not errors,'Plaster compile failed: '+str(errors));material_proof(u,m,contract)
 require(a.save_loaded_asset(m,only_if_is_dirty=False),'Plaster material save failed');return {destination}
