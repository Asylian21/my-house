"""Six authored ornamental tufts; retain all eighteen source cards, no canonical asset writes."""
import gc, hashlib, importlib.util, itertools, json, math, re, struct, uuid
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'lib/twin-site.ts').is_file())
HERE=Path(__file__).resolve().parent
OWNER='scripts/unreal/ornamental-grass/ornamental.py'
PREFIX='/Game/Brezi/OrnamentalGrass'; TAG='BreziOrnamentalGrass'; DATA='BreziOrnamentalDescriptor'; MAP='/Game/Brezi/Maps/Brezi'
IDS=tuple('DOM_%05d'%i for i in range(1841,1859))
SCENE_SHA='61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b'
OBJ_SHA='a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455'
INPUTS=HERE/'inputs/authored-v1'
RUNS=ROOT/'output/unreal/ornamental-grass/native-runs'
TRANSMISSION=.35

def need(ok,message):
 if not ok:raise RuntimeError(message)
def sha(p):
 p=Path(p);need(p.is_file() and p.resolve()==p,'Missing or symlinked input '+str(p));return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(v):return json.loads(json.dumps(v,allow_nan=False))
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def module(name,relative):
 spec=importlib.util.spec_from_file_location(name,ROOT/relative);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

_HELPERS=None
def helpers():
 global _HELPERS
 if _HELPERS is None:_HELPERS=(module('brezi_ornamental_common','scripts/unreal/tv-oak/tv_oak.py'),module('brezi_ornamental_ground','scripts/unreal/lawn-ground/lawn_ground.py'),module('brezi_ornamental_assets','scripts/unreal/lawn-detail/native_assets.py'))
 return _HELPERS
def path(o):return o.get_path_name() if o else None

def compare_faces(actual,expected):
 """Spatially indexed bijection; cyclic winding only, retained duplicate multiplicity."""
 need(len(actual)==len(expected),'Triangle count differs');tol=.0002;buckets={}
 def cell(p):return tuple(math.floor(x/tol) for x in p)
 for i,tri in enumerate(expected):
  for shift in range(3):buckets.setdefault(cell(tri[shift][0]),[]).append((i,shift))
 used=set();pe=ue=0.
 for tri in actual:
  key=cell(tri[0][0]);found=None
  for delta in itertools.product((-1,0,1),repeat=3):
   for i,s in buckets.get(tuple(a+b for a,b in zip(key,delta)),()):
    if i in used:continue
    p=max(abs(tri[c][0][k]-expected[i][(c+s)%3][0][k]) for c in range(3) for k in range(3));v=max(abs(tri[c][1][k]-expected[i][(c+s)%3][1][k]) for c in range(3) for k in range(2))
    if p<=tol and v<=2e-6:found=(i,p,v);break
   if found:break
  need(found is not None,'Position, winding, UV0 or triangle multiplicity differs');i,p,v=found;used.add(i);pe=max(pe,p);ue=max(ue,v)
 return {'maximumPositionErrorCm':pe,'maximumUv0Error':ue,'triangleMultiplicityAndWindingVerified':True}

def native_faces(u,mesh):
 d=mesh.get_static_mesh_description(0);need(d is not None,'Source MeshDescription missing');rows=[];instances=set()
 for i in range(d.get_triangle_count()):
  t=u.TriangleID(id_value=i);need(d.is_triangle_valid(t),'Sparse triangle IDs unsupported');row=[]
  for c in range(3):
   vi=d.get_triangle_vertex_instance(t,c);need(d.is_vertex_instance_valid(vi),'Invalid corner');v=d.get_vertex_instance_vertex(vi);need(d.is_vertex_valid(v),'Invalid vertex')
   p=d.get_vertex_position(v);uv=d.get_vertex_instance_uv(vi,0);row.append(([float(p.x),float(p.y),float(p.z)],[float(uv.x),float(uv.y)]));instances.add(int(vi.id_value))
  rows.append(row)
 need(len(instances)==d.get_vertex_instance_count() and all(math.isfinite(x) for t in rows for p,uv in t for x in p+uv),'Incomplete or nonfinite native corner readback');return rows

def glb_faces(file,group):
 data=Path(file).read_bytes();need(sha(file)==group['sha256'] and struct.unpack_from('<III',data)==(0x46546c67,2,len(data)),'GLB bytes/header differ');chunks={};offset=12
 while offset<len(data):
  size,kind=struct.unpack_from('<II',data,offset);offset+=8;need(kind not in chunks and size%4==0 and offset+size<=len(data),'Malformed GLB chunk');chunks[kind]=data[offset:offset+size];offset+=size
 need(set(chunks)=={0x4e4f534a,0x004e4942},'Unexpected GLB chunks');doc=json.loads(chunks[0x4e4f534a]);binary=chunks[0x004e4942]
 need(len(doc['nodes'])==len(doc['meshes'])==1 and doc['nodes'][0]['mesh']==0 and not any(k in doc['nodes'][0] for k in ('matrix','translation','rotation','scale','children','skin')),'GLB root is not local identity')
 ps=doc['meshes'][0]['primitives'];need(len(ps)==1 and ps[0].get('mode',4)==4 and set(ps[0]['attributes'])=={'POSITION','NORMAL','TANGENT','TEXCOORD_0'} and 'targets' not in ps[0],'GLB primitive layout differs');p=ps[0]
 def accessor(index,kind):
  a=doc['accessors'][index];need(a['type']==kind and 'sparse' not in a and not a.get('normalized',False) and a['componentType'] in ((5121,5123,5125) if kind=='SCALAR' else (5126,)),'Unsupported GLB accessor');fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[kind];view=doc['bufferViews'][a['bufferView']];width=struct.calcsize('<'+fmt*n);stride=view.get('byteStride',width);start=view.get('byteOffset',0)+a.get('byteOffset',0)
  need(view.get('buffer',0)==0 and 0<a['count']<=20000 and stride>=width and start+(a['count']-1)*stride+width<=view.get('byteOffset',0)+view['byteLength']<=len(binary),'GLB accessor bounds/budget differ')
  rows=[struct.unpack_from('<'+fmt*n,binary,start+i*stride) for i in range(a['count'])];need(all(math.isfinite(v) for r in rows for v in r),'Nonfinite GLB');return rows
 attrs=p['attributes'];pos=accessor(attrs['POSITION'],'VEC3');uv=accessor(attrs['TEXCOORD_0'],'VEC2');normal=accessor(attrs['NORMAL'],'VEC3');tangent=accessor(attrs['TANGENT'],'VEC4');indices=[r[0] for r in accessor(p['indices'],'SCALAR')]
 need(len(pos)==len(uv)==len(normal)==len(tangent)==group['vertices'] and len(indices)==group['triangles']*3 and all(isinstance(i,int) and 0<=i<len(pos) for i in indices),'GLB topology differs')
 native=[[100*x,100*z,100*y] for x,y,z in pos] # Public GLTFCore ConvertVec3; UV0 copied unchanged.
 return [[(native[i],list(uv[i])) for i in indices[n:n+3]] for n in range(0,len(indices),3)]

def card_faces(file):
 p=[];uv=[];rows={i:[] for i in IDS};current=slot=None
 for line in Path(file).read_text().splitlines():
  f=line.split()
  if not f:continue
  if f[0]=='v':p.append(tuple(map(float,f[1:4])))
  elif f[0]=='vt':uv.append(tuple(map(float,f[1:3])))
  elif f[0]=='o':current=f[1]
  elif f[0]=='usemtl':slot=f[1]
  elif f[0]=='f' and current in rows:
   need(len(f)==4 and slot=='MAT_0004','Source card topology/slot differs');tri=[]
   for token in f[1:]:
    v,t=map(int,token.split('/')[:2]);need(v>0 and t>0,'Negative OBJ indices unsupported');x,y,z=p[v-1];a,b=uv[t-1];tri.append(([x/10,-y/10,z/10],[a,1-b]))
   rows[current].append(tri)
 need(all(len(r)==2 for r in rows.values()),'Exact eighteen two-triangle cards required');return rows

def verify_inputs(scene,geometry):
 geometry=Path(geometry);need(sha(geometry/'scene.json')==SCENE_SHA and sha(geometry/'dom-mm.obj')==OBJ_SHA and digest(scene)==digest(json.loads((geometry/'scene.json').read_text())),'Canonical source changed')
 report_file=INPUTS/'ornamental.json';ref=json.loads((HERE/'reference.json').read_text());need(sha(report_file)==ref['reportSha256'] and sha(INPUTS/'generate.py')==ref['generatorSha256'],'Authored input bytes differ');report=json.loads(report_file.read_text());need(report['status']=='authored-ornamental-geometry-validated' and report['sourceManifestSha256']==SCENE_SHA and report['sourceObjSha256']==OBJ_SHA and report['generatorSha256']==ref['generatorSha256'] and report['nativeApplied'] is False,'Generator proof differs');groups=report['groups'];need(len(groups)==6 and len({g['id'] for g in groups})==6,'Six unique ornamental groups required')
 need([i for g in groups for i in g['sourceIds']]==list(IDS),'Exact ordered source triplets required')
 records={r['id']:r for r in scene['objects'] if r['id'] in IDS};need(len(records)==18 and all(r['enabled'] and r['instances']==1 and r['triangles']==2 and r['materialSlots']==['MAT_0004'] and r['metadata']['babylonCheckCollisions'] is False for r in records.values()),'Canonical card identity differs')
 pins={'scripts/unreal/ornamental-grass/inputs/authored-v1/ornamental.json':sha(report_file),'scripts/unreal/ornamental-grass/inputs/authored-v1/generate.py':sha(INPUTS/'generate.py')};faces={}
 for p,h in report['sourceFiles'].items():need(sha(ROOT/p)==h,'Generator source changed '+p);pins[p]=h
 for g in groups:
  need(g['sourceRecordHashes']=={i:digest(records[i]) for i in g['sourceIds']} and all(g['verification'][k] is True for k in ('sourceRootPositionPreserved','allVerticesWithinSourceXYEnvelope','allVerticesWithinParcel','allLeafBasalRowsReachSourceSupport')),'Source geometry proof differs')
  need(re.fullmatch('[A-Za-z0-9_]+',g['id']) and Path(g['file']).name==g['file'] and g['triangles']==1584 and 0<g['vertices']<=20000,'Group ID/file/budget differs')
  need(all(math.isfinite(x) for x in g['rootUnrealCm']) and len(g['rootUnrealCm'])==3,'Nonfinite root')
  need(max(abs(a-b) for a,b in zip(g['rootUnrealCm'],[g['rootSourceMm'][0]/10,-g['rootSourceMm'][1]/10,g['rootSourceMm'][2]/10]))<1e-6,'Root coordinate conversion differs')
  m=g['material'];need(len(m['baseColorLinear'])==3 and all(0<=v<=1 for v in m['baseColorLinear']) and m['metallic']==0 and m['twoSided'] is True and 0<=m['roughness']<=1,'Material recipe differs')
  f=INPUTS/g['file'];pins['scripts/unreal/ornamental-grass/inputs/authored-v1/'+g['file']]=sha(f);faces[g['id']]=glb_faces(f,g)
 for f in ('ornamental.py','package-gate.mjs','reference.json'):pins['scripts/unreal/ornamental-grass/'+f]=sha(HERE/f)
 for f in ('scripts/unreal/tv-oak/tv_oak.py','scripts/unreal/lawn-ground/lawn_ground.py','scripts/unreal/lawn-ground/source.py','scripts/unreal/lawn-ground/graph.py','scripts/unreal/lawn-detail/native_assets.py','scripts/unreal/materials.py','unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.h','unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.cpp'):pins[f]=sha(ROOT/f)
 recipe_files={p:h for p,h in pins.items() if p!='scripts/unreal/materials.py'};recipe=digest({'files':recipe_files,'transmission':TRANSMISSION});return {'groups':groups,'faces':faces,'cards':card_faces(geometry/'dom-mm.obj'),'records':records,'pins':pins,'recipe':recipe,'prefix':PREFIX+'/R_'+recipe[:16]}

def source_state(u,contract,allow_scalar=False):
 common,ground,_=helpers();found=common.components(u,IDS);result={}
 for id_,(a,c) in found.items():
  mesh=c.get_editor_property('static_mesh');r=contract['records'][id_];need(a.actor_has_tag('BreziGenerated') and mesh and path(mesh)==f'/Game/Brezi/Geometry/brezi-twin/StaticMeshes/{id_}.{id_}','Card native identity differs')
  for k,v in {'source_object_id':id_,'source_id':r['sourceId'],'source_group':r['group'],'source_name':r['name']}.items():need(u.EditorAssetLibrary.get_metadata_tag(mesh,k)==v,'Card source metadata differs')
  need(ground.transform(c.get_world_transform())=={'p':[0.,0.,0.],'q':[0.,0.,0.,1.],'s':[1.,1.,1.]} and c.get_num_materials()==1 and common.overrides(c)==[] and c.get_material(0)==mesh.get_material(0),'Card transform/material override differs')
  base=mesh.get_material(0);authored=(path(base)=='/Game/Brezi/MaterialsGenerated/M_MAT_0004.M_MAT_0004' and u.EditorAssetLibrary.get_metadata_tag(base,'BreziGeneratedBy')=='scripts/unreal/materials.py' and u.EditorAssetLibrary.get_metadata_tag(base,'source_material_slot')=='MAT_0004')
  need((authored or allow_scalar and path(base)=='/Game/Brezi/Geometry/brezi-twin/Materials/MAT_0004.MAT_0004') and mesh.get_num_triangles(0)==2 and mesh.get_num_sections(0)==1 and mesh.get_num_tex_coords(0)==1 and c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION,'Card slot/UV/collision differs')
  faces=native_faces(u,mesh);proof=compare_faces(faces,contract['cards'][id_]);result[id_]={'actor':path(a),'component':c.get_name(),'visible':bool(c.get_editor_property('visible')),'hiddenInGame':bool(c.get_editor_property('hidden_in_game')),'actorHidden':bool(a.get_editor_property('hidden')),'nativeFacesSha256':digest(faces),'sourceProof':proof}
 return result

def snapshot(u):
 _,ground,_=helpers();s=ground.snapshot_world(u)
 from materials import _asset_hashes
 # Ground's own reader excludes its own namespace; this stage must protect it too.
 for row in s['actors'].values():
  for c in row['components']:
   for p in c['materials']:
    if p and p.startswith(ground.G.PREFIX+'/'):s['protectedAssetHashes'].update(_asset_hashes(u.EditorAssetLibrary.list_assets(p.split('/Materials/')[0],recursive=True,include_folder=False)))
 for actor,row in list(s['actors'].items()):
  if TAG in row['tags']:
   need(row['metadata'].get('BreziGeneratedBy')==OWNER,'Foreign ornamental tagged actor');del s['actors'][actor]
 prefix='unreal/BreziTwin/Content'+PREFIX.removeprefix('/Game')+'/'
 s['protectedAssetHashes']={p:h for p,h in s['protectedAssetHashes'].items() if not p.startswith(prefix)}
 return s

def expected_world(before,cards,visible=None):
 out=plain(before)
 if visible is not None:
  for id_,card in cards.items():
   cs=[c for c in out['actors'][card['actor']]['components'] if c['name']==card['component']];need(len(cs)==1,'Selected card missing from snapshot');cs[0]['visible']=visible[id_]
 return out

def layer(u,contract,states=('active',)):
 rows=[];assets=u.EditorAssetLibrary
 for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  owner=assets.get_metadata_tag(a,'BreziGeneratedBy')==OWNER;need(not owner or a.actor_has_tag(TAG),'Owned ornamental actor lost its tag')
  if not a.actor_has_tag(TAG):continue
  need(owner and a.actor_has_tag('BreziGenerated') and not any(re.fullmatch('DOM_[0-9]{5}',str(t)) for t in a.get_editor_property('tags')) and a.get_class().get_path_name()=='/Script/Engine.StaticMeshActor','Foreign ornamental actor')
  d=json.loads(assets.get_metadata_tag(a,DATA));need(d['state'] in states and re.fullmatch('[0-9a-f]{32}',d['transaction']) and re.fullmatch('[0-9a-f]{64}',d['recipe']),'Malformed owned descriptor')
  groups={g['id']:g for g in contract['groups']};need(d['groupId'] in groups and d['sourceIds']==groups[d['groupId']]['sourceIds'],'Ornamental source triplet differs')
  need(d['transform']=={'p':groups[d['groupId']]['rootUnrealCm'],'q':[0.,0.,0.,1.],'s':[1.,1.,1.]} and set(d['originalCardVisibility'])==set(d['sourceIds']) and all(type(v) is bool for v in d['originalCardVisibility'].values()),'Owned source root/prior visibility differs')
  cs=a.get_components_by_class(u.StaticMeshComponent);need(len(cs)==1,'Ornamental component count differs');c=cs[0];mesh=c.get_editor_property('static_mesh')
  need(mesh is not None and path(mesh)==d['mesh'] and path(c.get_material(0))==d['material'] and not c.get_editor_property('override_materials'),'Ornamental binding differs')
  for p in (mesh,c.get_material(0)):
   need(path(p).startswith(PREFIX+'/R_'+d['recipe'][:16]+'/') and assets.get_metadata_tag(p,'BreziGeneratedBy')==OWNER and assets.get_metadata_tag(p,'BreziOrnamentalRecipe')==d['recipe'],'Foreign owned asset')
  _,ground,_=helpers();need(ground.transform(a.get_actor_transform())==d['transform'] and ground.transform(c.get_world_transform())==d['transform'],'Ornamental transform changed')
  o,e,_=u.SystemLibrary.get_component_bounds(c);bounds={'min':[float(getattr(o,k)-getattr(e,k)) for k in 'xyz'],'max':[float(getattr(o,k)+getattr(e,k)) for k in 'xyz']}
  need(max(abs(bounds[k][i]-d['boundsUnrealCm'][k][i]) for k in ('min','max') for i in range(3))<=.05,'Ornamental native bounds differ')
  need(c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION and str(c.get_collision_profile_name())=='NoCollision' and not c.get_editor_property('can_ever_affect_navigation') and not c.is_component_tick_enabled() and not a.is_actor_tick_enabled(),'Ornamental collision/navigation/tick differs')
  need(c.get_editor_property('mobility')==u.ComponentMobility.STATIC and not a.get_editor_property('hidden') and not c.get_editor_property('hidden_in_game') and bool(c.get_editor_property('visible'))==(d['state']=='active'),'Ornamental visibility/mobility differs')
  for k in ('cast_shadow','visible_in_ray_tracing','affect_distance_field_lighting','affect_dynamic_indirect_lighting'):need(c.get_editor_property(k) is True,'Ornamental lighting policy differs')
  from materials import _asset_hashes
  need(_asset_hashes([d['mesh'],d['material']])==d['assetHashes'],'Owned ornamental saved asset changed')
  rows.append({'actor':path(a),'descriptor':d})
 keys=[(r['descriptor']['transaction'],r['descriptor']['groupId']) for r in rows];need(len(keys)==len(set(keys)),'Duplicate ornamental group');return rows

def preflight_reimport(u,actors,scene,geometry):
 contract=verify_inputs(scene,geometry);old=layer(u,contract);cards=source_state(u,contract,allow_scalar=not old)
 need(not old or len(old)==6 and len({r['descriptor']['transaction'] for r in old})==1,'Incomplete prior ornamental layer')
 if old:need(all(not c['visible'] for c in cards.values()),'Owned layer source card visibility drift')
 return {'status':'ornamental-pre-delete-validated','sourceObjectCount':len(cards),'ownedActorCount':len(old)}

class Assets:
 def __init__(self,u,contract):self.u=u;self.c=contract;self.prefix=contract['prefix'];self.a=u.EditorAssetLibrary;self.lib=u.MaterialEditingLibrary;self.tools=u.AssetToolsHelpers.get_asset_tools();self.paths=set()
 def own(self,o):
  need(o is not None and path(o).startswith(self.prefix+'/'),'Asset escaped namespace');self.a.set_metadata_tag(o,'BreziGeneratedBy',OWNER);self.a.set_metadata_tag(o,'BreziOrnamentalRecipe',self.c['recipe']);self.paths.add(path(o));return o
 def existing(self,p):
  o=self.a.load_asset(p) if self.a.does_asset_exist(p) else None
  if o:need(path(o).startswith(self.prefix+'/') and self.a.get_metadata_tag(o,'BreziGeneratedBy')==OWNER and self.a.get_metadata_tag(o,'BreziOrnamentalRecipe')==self.c['recipe'],'Foreign owned asset');self.paths.add(path(o))
  return o
 def save(self,o):need(self.a.save_loaded_asset(o,only_if_is_dirty=False),'Owned asset save failed')
 def spec(self,g):
  u=self.u;m=g['material'];return {'base':(u.MaterialExpressionConstant3Vector,{'constant':u.LinearColor(*m['baseColorLinear'],1)}),'rough':(u.MaterialExpressionConstant,{'r':m['roughness']}),'metal':(u.MaterialExpressionConstant,{'r':0.}),'transmission':(u.MaterialExpressionConstant3Vector,{'constant':u.LinearColor(*[v*TRANSMISSION for v in m['baseColorLinear']],1)}),'opacity':(u.MaterialExpressionConstant,{'r':.5})}
 def material_proof(self,m,g):
  u=self.u;_,_,api=helpers();need(self.existing(path(m))==m,'Material ownership differs')
  for k,v in {'blend_mode':u.BlendMode.BLEND_OPAQUE,'two_sided':True,'shading_model':api.enum(u,u.MaterialShadingModel,'TWOSIDEDFOLIAGE'),'tangent_space_normal':True,'use_material_attributes':False}.items():need(m.get_editor_property(k)==v,'Material policy differs '+k)
  expr=list(self.lib.get_material_expressions(m));nodes={self.a.get_metadata_tag(n,'BreziOrnamentalRole'):n for n in expr};spec=self.spec(g);need(len(expr)==len(nodes)==5 and nodes.keys()==spec.keys(),'Material node topology differs')
  for role,(cls,props) in spec.items():
   n=nodes[role];need(isinstance(n,cls),'Material node type differs')
   for k,w in props.items():
    v=n.get_editor_property(k);actual=[v.r,v.g,v.b,v.a] if k=='constant' else [v];wanted=[w.r,w.g,w.b,w.a] if k=='constant' else [w];need(max(abs(a-b) for a,b in zip(actual,wanted))<=1e-6,'Material scalar differs')
   need(not any(self.lib.get_inputs_for_material_expression(m,n)),'Constant graph acquired an input')
  outputs={'BASE_COLOR':'base','ROUGHNESS':'rough','METALLIC':'metal','SUBSURFACE_COLOR':'transmission','OPACITY':'opacity'}
  for p,role in outputs.items():
   prop=getattr(u.MaterialProperty,'MP_'+p);need(self.lib.get_material_property_input_node(m,prop)==nodes[role],'Material output differs '+p)
   need(api.output_name(self.lib.get_material_property_input_node_output_name(m,prop))==str(self.lib.get_material_expression_output_names(nodes[role])[0]),'Material output channel differs')
  for p in ('WORLD_POSITION_OFFSET','NORMAL','EMISSIVE_COLOR','OPACITY_MASK','SPECULAR','AMBIENT_OCCLUSION'):need(self.lib.get_material_property_input_node(m,getattr(u.MaterialProperty,'MP_'+p)) is None,'Unexpected material output '+p)
  need(u.BreziRendererSettingsAudit.has_no_pixel_depth_offset_connection(m) is True,'Unexpected pixel depth offset')
  return {'asset':path(m),'graphNodes':5,'opaque':True,'twoSidedFoliage':True,'baseColorLinear':g['material']['baseColorLinear'],'roughness':g['material']['roughness'],'metallic':0,'authoredTransmissionScale':TRANSMISSION,'opacity':.5,'noWpoPdo':True,'nativeNumericNormalsVerified':False}
 def material(self,g):
  u=self.u;_,_,api=helpers();name='M_'+g['id'];m=self.existing(self.prefix+'/Materials/'+name)
  if m is None:
   m=self.own(self.tools.create_asset(name,self.prefix+'/Materials',u.Material,u.MaterialFactoryNew()))
   for k,v in {'blend_mode':u.BlendMode.BLEND_OPAQUE,'two_sided':True,'shading_model':api.enum(u,u.MaterialShadingModel,'TWOSIDEDFOLIAGE'),'tangent_space_normal':True,'use_material_attributes':False}.items():m.set_editor_property(k,v)
   nodes={}
   for role,(cls,props) in self.spec(g).items():
    n=self.lib.create_material_expression(m,cls,-400,0);need(n is not None,'Material node creation failed');self.a.set_metadata_tag(n,'BreziOrnamentalRole',role)
    for k,v in props.items():n.set_editor_property(k,v)
    nodes[role]=n
   for prop,role in {'BASE_COLOR':'base','ROUGHNESS':'rough','METALLIC':'metal','SUBSURFACE_COLOR':'transmission','OPACITY':'opacity'}.items():need(self.lib.connect_material_property(nodes[role],'',getattr(u.MaterialProperty,'MP_'+prop)),'Material output creation failed')
   need(not list(self.lib.recompile_material(m)),'Material compiler error');self.save(m)
  self.material_proof(m,g);return m
 def create(self):
  u=self.u;_,_,api=helpers();pipeline=api.Assets.pipeline(self);registry=u.AssetRegistryHelpers.get_asset_registry();result={}
  for g in self.c['groups']:
   material=self.material(g);directory=self.prefix+'/Meshes/'+g['id'];paths=self.a.list_assets(directory,recursive=True,include_folder=False)
   if not paths:
    manager=u.InterchangeManager.get_interchange_manager_scripted();params=u.ImportAssetParameters()
    for k,v in {'is_automated':True,'replace_existing':False,'force_show_dialog':False,'override_pipelines':[u.SoftObjectPath(path(pipeline))]}.items():params.set_editor_property(k,v)
    need(manager.import_asset(directory,manager.create_source_data(str(INPUTS/g['file'])),params),'Ornamental GLB import failed');registry.scan_paths_synchronous([directory],force_rescan=True);paths=self.a.list_assets(directory,recursive=True,include_folder=False);need(len(paths)==1,'Unexpected imported assets')
    mesh=self.own(self.a.load_asset(paths[0]));need(isinstance(mesh,u.StaticMesh),'Imported object is not a mesh');mesh.set_material(0,material);mesh.set_editor_property('has_navigation_data',False);self.a.set_metadata_tag(mesh,'source_sha256',g['sha256']);self.save(mesh)
   need(len(paths)==1,'Unexpected mesh namespace');mesh=self.existing(paths[0]);need(self.a.get_metadata_tag(mesh,'source_sha256')==g['sha256'],'Mesh source GLB differs');result[g['id']]={'mesh':path(mesh),'material':path(material)}
  return result
 def prove(self,bindings):
  u=self.u;out={}
  for g in self.c['groups']:
   b=bindings[g['id']];mesh=self.existing(b['mesh']);material=self.existing(b['material']);need(isinstance(mesh,u.StaticMesh) and mesh.get_num_sections(0)==1 and mesh.get_num_triangles(0)==g['triangles'] and mesh.get_num_tex_coords(0)==1 and len(mesh.get_editor_property('static_materials'))==1 and mesh.get_material(0)==material,'Mesh topology/material differs')
   need(not mesh.get_editor_property('nanite_settings').get_editor_property('enabled') and not mesh.get_editor_property('has_navigation_data'),'Mesh Nanite/navigation policy differs');faces=native_faces(u,mesh);proof=compare_faces(faces,self.c['faces'][g['id']]);out[g['id']]={'mesh':path(mesh),'triangles':g['triangles'],'nativeFacesSha256':digest(faces),'sourceProof':proof,'material':self.material_proof(material,g)}
  return out

def reload(u,owned):
 levels=u.get_editor_subsystem(u.LevelEditorSubsystem);need(levels.save_current_level(),'Map save failed');need(u.EditorLoadingAndSavingUtils.new_blank_map(False),'Map unload failed');gc.collect();packages=[]
 for p in sorted(owned):
  o=u.find_object(None,p)
  if o:need(path(o).startswith(PREFIX+'/') and u.EditorAssetLibrary.get_metadata_tag(o,'BreziGeneratedBy')==OWNER,'Foreign package unload');packages.append(o.get_outermost())
  del o
 if packages:
  r=u.EditorLoadingAndSavingUtils.unload_packages(packages);need(isinstance(r,tuple) and r[0] is True and not str(r[1]),'Owned package unload failed')
 del packages;gc.collect();need(all(u.find_object(None,p) is None for p in owned),'Owned packages remain loaded');need(levels.load_level(MAP),'Map reload failed');return {'mapSaved':True,'worldUnloaded':True,'ownedAssetsAbsentBeforeReload':True,'mapReloaded':True}

def spawn(u,d):
 actor=u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(u.StaticMeshActor,u.Vector(*d['transform']['p']),u.Rotator());need(actor is not None,'Actor spawn failed');actor.set_editor_property('tags',[u.Name('BreziGenerated'),u.Name(TAG)]);u.EditorAssetLibrary.set_metadata_tag(actor,'BreziGeneratedBy',OWNER);u.EditorAssetLibrary.set_metadata_tag(actor,DATA,json.dumps(d,allow_nan=False));actor.set_actor_label('Okrasná tráva · '+d['groupId']);actor.set_actor_tick_enabled(False);c=actor.get_component_by_class(u.StaticMeshComponent);c.set_visibility(False);c.set_hidden_in_game(False);c.set_static_mesh(u.EditorAssetLibrary.load_asset(d['mesh']));c.set_mobility(u.ComponentMobility.STATIC);c.set_collision_profile_name('NoCollision');c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);c.set_editor_property('can_ever_affect_navigation',False);c.set_component_tick_enabled(False)
 for k in ('cast_shadow','visible_in_ray_tracing','affect_distance_field_lighting','affect_dynamic_indirect_lighting'):c.set_editor_property(k,True)
 c.set_visibility(d['state']=='active')

def alter(u,tx,state=None,remove=False):
 system=u.get_editor_subsystem(u.EditorActorSubsystem)
 for a in system.get_all_level_actors():
  if not a.actor_has_tag(TAG):continue
  need(u.EditorAssetLibrary.get_metadata_tag(a,'BreziGeneratedBy')==OWNER,'Foreign ornamental tag');d=json.loads(u.EditorAssetLibrary.get_metadata_tag(a,DATA))
  if d['transaction']!=tx:continue
  if remove:need(system.destroy_actor(a),'Owned actor deletion failed')
  else:d['state']=state;u.EditorAssetLibrary.set_metadata_tag(a,DATA,json.dumps(d,allow_nan=False));a.get_component_by_class(u.StaticMeshComponent).set_visibility(state=='active')

def set_cards(u,visible):
 common,_,_=helpers()
 for i,(_,c) in common.components(u,IDS).items():c.set_visibility(visible[i])

def apply_ornamental(scene,geometry):
 need(Path(__file__).resolve()==ROOT/OWNER,'Output-only ornamental draft cannot mutate assets')
 import unreal as u
 from materials import _asset_hashes
 need(Path(u.Paths.project_dir()).resolve()==ROOT/'unreal/BreziTwin','Unexpected native project');contract=verify_inputs(scene,geometry);writer=Assets(u,contract);tx=uuid.uuid4().hex;destination=RUNS/tx;destination.mkdir(parents=True,exist_ok=False)
 report={'status':'pending','nativeApplied':False,'recipeSha256':contract['recipe'],'recipeExcludesReadOnlyMaterialsHelper':True,'pipelineFiles':contract['pins'],'transaction':tx,'nativeProcessId':__import__('os').getpid(),'sourceManifestSha256':SCENE_SHA,'sourceObjSha256':OBJ_SHA,'sourceIds':list(IDS),'renderedVerified':False,'performanceAccepted':False,'actorMetadataWrittenToSources':False,'nativeNumericNormalsVerified':False};before=None;cards=None;old=[];changed=False
 def write(): (destination/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
 def pinned():
  for p,h in contract['pins'].items():need(sha(ROOT/p)==h,'Input changed '+p)
 try:
  cards=source_state(u,contract);old=layer(u,contract);need(not old or len(old)==6 and len({r['descriptor']['transaction'] for r in old})==1,'Incomplete previous layer');before=snapshot(u);write();bindings=writer.create();proof=writer.prove(bindings);owned=set(writer.paths);hashes=_asset_hashes(owned)
  report['stagedReload']=reload(u,owned);need(writer.prove(bindings)==proof and snapshot(u)==before and source_state(u,contract)==cards and _asset_hashes(owned)==hashes,'Staged source/assets changed');pinned()
  original={i:c['visible'] for i,c in cards.items()}
  if old:
   original={i:v for r in old for i,v in r['descriptor']['originalCardVisibility'].items()};need(set(original)==set(IDS) and all(not c['visible'] for c in cards.values()),'Previous source visibility contract differs')
  changed=True
  for g in contract['groups']:
   b=bindings[g['id']];d={'groupId':g['id'],'sourceIds':g['sourceIds'],'recipe':contract['recipe'],'transaction':tx,'state':'staged','mesh':b['mesh'],'material':b['material'],'assetHashes':_asset_hashes(b.values()),'transform':{'p':g['rootUnrealCm'],'q':[0.,0.,0.,1.],'s':[1.,1.,1.]},'boundsUnrealCm':g['boundsUnrealCm'],'originalCardVisibility':{i:original[i] for i in g['sourceIds']}};spawn(u,d)
  report['stagedActorsReload']=reload(u,owned);need(len(layer(u,contract,('active','staged')))==len(old)+6 and snapshot(u)==before,'Staged actors altered non-owned world')
  for old_tx in {r['descriptor']['transaction'] for r in old}:alter(u,old_tx,'retiring')
  set_cards(u,{i:False for i in IDS});alter(u,tx,'active');report['activeReload']=reload(u,owned)
  need(snapshot(u)==expected_world(before,cards,{i:False for i in IDS}) and writer.prove(bindings)==proof,'Active layer changed protected world/assets')
  need(len(layer(u,contract,('active','retiring')))==len(old)+6,'Active layer coverage differs')
  for old_tx in {r['descriptor']['transaction'] for r in old}:alter(u,old_tx,remove=True)
  report['finalReload']=reload(u,owned);final=layer(u,contract);need(len(final)==6 and {r['descriptor']['transaction'] for r in final}=={tx},'Final six-actor layer differs');need(snapshot(u)==expected_world(before,cards,{i:False for i in IDS}) and writer.prove(bindings)==proof and _asset_hashes(owned)==hashes,'Final saved world/assets differ');after=source_state(u,contract)
  for i in IDS:need({**after[i],'visible':cards[i]['visible']}==cards[i],'Source card changed beyond visibility')
  pinned();report.update(mapFileSha256=sha(ROOT/'unreal/BreziTwin/Content/Brezi/Maps/Brezi.umap'),status='ornamental-saved-reload-validated',nativeApplied=True,groups=final,meshProofs=proof,sourceBefore=cards,sourceAfter=after,assetHashes=hashes,protectedAssetHashes=before['protectedAssetHashes'],sourcePreservationSnapshotSha256=digest(before),sourceObjectsDeleted=0,sourceCardsHidden=18,newActorCount=6,collision=False,navigation=False,tick=False,stagedProofEqualsFinal=True,priorLayerRemoved=bool(old));write();return report
 except Exception as error:
  message=str(error);error.__traceback__=None;report.update(status='failed',error=message,rollbackAttempted=changed,rollbackVerified=False)
  if before is not None:
   try:
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);need(u.EditorLoadingAndSavingUtils.new_blank_map(False) and levels.load_level(MAP),'Rollback map load failed')
    if changed:alter(u,tx,remove=True)
    if changed:
     for old_tx in {r['descriptor']['transaction'] for r in old}:alter(u,old_tx,remove=True)
     for row in old:spawn(u,row['descriptor'])
    set_cards(u,{i:c['visible'] for i,c in cards.items()});reload(u,writer.paths);need(snapshot(u)==before and source_state(u,contract)==cards,'Rollback protected state differs');restored=layer(u,contract);need(sorted((r['descriptor'] for r in restored),key=lambda d:d['groupId'])==sorted((r['descriptor'] for r in old),key=lambda d:d['groupId']),'Rollback layer differs');report['rollbackVerified']=changed;report['sourceStateVerifiedOnFailure']=True
   except Exception as failure:report['rollbackError']=str(failure);failure.__traceback__=None
  write();raise RuntimeError(message) from None
