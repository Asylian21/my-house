"""Source inputs and actual per-corner MeshDescription proof; CPU callable."""
import hashlib,importlib.util,json,math,xml.etree.ElementTree as ET
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'lib/twin-site.ts').is_file())
ID,SLOT='DOM_00001','MAT_0001'
MESH='/Game/Brezi/Geometry/brezi-twin/StaticMeshes/DOM_00001.DOM_00001'
BASE='/Game/Brezi/MaterialsGenerated/M_MAT_0001.M_MAT_0001'
OWNER='scripts/unreal/lawn-ground/lawn_ground.py'
SCENE_SHA='61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b'
OBJ_SHA='a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455'

def require(ok,message):
 if not ok:raise RuntimeError(message)
def sha(p):
 p=Path(p);require(p.is_file() and p.resolve()==p,'Missing/symlinked source '+str(p));return hashlib.sha256(p.read_bytes()).hexdigest()
def values(v):return json.loads(json.dumps(v,allow_nan=False))
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def input_path(path):
 prefix='scripts/unreal/lawn-ground/'
 return HERE/path[len(prefix):] if path.startswith(prefix) else ROOT/path

def verify_inputs(scene,geometry):
 geometry=Path(geometry);ref=json.loads((HERE/'reference.json').read_text())
 require(ref['sceneSha256']==SCENE_SHA and ref['objSha256']==OBJ_SHA and sha(geometry/'scene.json')==SCENE_SHA and sha(geometry/'dom-mm.obj')==OBJ_SHA,'Lawn source geometry pin changed')
 require(digest(scene)==digest(json.loads((geometry/'scene.json').read_text())),'Lawn supplied scene differs')
 rows=[r for r in scene['objects'] if r['id']==ID or SLOT in r['materialSlots']]
 require(len(rows)==1 and rows[0]==ref['sourceRecord'] and rows[0]['id']==ID and rows[0]['materialSlots']==[SLOT] and rows[0]['triangles']==27,'Lawn exact source scope changed')
 require(scene['materials'][SLOT]==ref['sourceMaterial'] and ref['sourceMaterial']['name']=='real-grass','Lawn source material changed')
 require(ref['provider']['approximateTileMetres']==[1.4,1.4] and ref['provider']['technique']=='Procedural' and ref['provider']['scanClaim'] is False,'Lawn provenance/scale changed')
 shader=module('brezi_lawn_ground_policy',HERE/'shading.py')
 require(ref['schemaVersion']==2 and ref['version']=='LAWN-GROUND-GRASS004-ARTIST-EFFECTIVE-ROUGHNESS-2' and ref['material']['roughness']==shader.ROUGHNESS_POLICY,'Lawn artist effective roughness policy changed')
 require(ref['material']['tintLinear']==[1,1,1] and ref['material']['normalStrength']==1 and ref['material']['metallic']==0 and ref['material']['specular']==.5 and ref['material']['noGeometryDisplacement'] is True,'Lawn albedo/normal/geometry policy changed')
 require(ref['sampling']=={'uv0Scale':[32133/1400,24497/1400],'phaseCount':3,'method':'barycentric-translation-only','textureSamples':9,'explicitContinuousGradients':True,'sameOffsetsAndWeightsAllMaps':True,'tangentBasisPreserved':True},'Lawn sampling policy changed')
 for path,expected in {**ref['evidence'],**ref['sourceIntentFiles']}.items():require(sha(input_path(path))==expected,'Lawn evidence/intent changed: '+path)
 require(set(ref['maps'])=={'Diffuse','nor_gl','Rough'},'Lawn PBR map roles differ')
 for role,v in ref['maps'].items():require((ROOT/v['path']).stat().st_size==v['bytes'] and sha(ROOT/v['path'])==v['sha256'],'Lawn map changed: '+role)
 builder=(ROOT/'lib/babylon-scene.ts').read_text()
 require('this.applyTexture(this.realisticMaterials.grass, "lawn-albedo", 12, 10, "lawn-normal", 0.4);' in builder and '(point.x - minX) / Math.max(1, maxX - minX),' in builder and '(point.y - minY) / Math.max(1, maxY - minY),' in builder,'Canonical raw UV0 semantics changed')
 mtlx=next(input_path(p) for p in ref['evidence'] if p.endswith('.mtlx'));xml=ET.parse(mtlx).getroot()
 rough=xml.find("open_pbr_surface/input[@name='specular_roughness']")
 require(rough is not None and rough.attrib.get('nodename')=='Grass004_4K_JPG_Roughness','Provider roughness workflow changed')
 tex=xml.find("tiledimage[@name='Grass004_4K_JPG_Roughness']")
 require(tex is not None and tex.attrib.get('type')=='float' and tex.find("input[@name='file']").attrib=={'type':'filename','value':'Grass004_4K-JPG_Roughness.jpg','name':'file'},'Provider linear roughness interpretation changed')
 common=ROOT/'scripts/unreal/tv-oak/tv_oak.py'
 files={str(Path('scripts/unreal/lawn-ground')/n):sha(HERE/n) for n in ('lawn_ground.py','graph.py','source.py','shading.py','reference.json')}
 files['scripts/unreal/tv-oak/tv_oak.py']=sha(common)
 for n in ('BreziRendererSettingsAudit.h','BreziRendererSettingsAudit.cpp'):files['unreal/BreziTwin/Source/BreziTwin/'+n]=sha(ROOT/'unreal/BreziTwin/Source/BreziTwin'/n)
 recipe={'reference':ref,'recipeInputs':files};recipe_json=json.dumps(recipe,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False);recipe_sha=digest(recipe);prefix='/Game/Brezi/LawnGround/R_'+recipe_sha[:16]
 # Entire helper files are in the global input closure. The unrelated shared
 # materials writer is not part of the owned lawn graph recipe identity.
 pipeline={**files,**ref['sourceIntentFiles'],**ref['evidence'],**{v['path']:v['sha256'] for v in ref['maps'].values()},'scripts/unreal/materials.py':sha(ROOT/'scripts/unreal/materials.py')}
 for name in ('restore_inputs.py','package-gate.mjs'):pipeline['scripts/unreal/lawn-ground/'+name]=sha(HERE/name)
 return {'reference':ref,'record':rows[0],'recipe':recipe,'recipeCanonicalJson':recipe_json,'recipeSha256':recipe_sha,'pipelineFiles':pipeline,'candidate':{'maps':ref['maps']},'prefix':prefix,'materialPath':prefix+'/Materials/M_LawnGround.M_LawnGround'}

def read_source(path):
 positions=[];uvs=[];rows=[];current=slot=None
 for line in Path(path).read_text().splitlines():
  a=line.split()
  if not a:continue
  if a[0]=='v':positions.append(tuple(map(float,a[1:4])))
  elif a[0]=='vt':uvs.append(tuple(map(float,a[1:3])))
  elif a[0]=='o':current=a[1]
  elif a[0]=='usemtl':slot=a[1]
  elif a[0]=='f' and current==ID:
   require(len(a)==4 and slot==SLOT,'Lawn source triangle/slot changed');refs=[tuple(map(int,v.split('/')[:2])) for v in a[1:]]
   require(all(v>0 and t>0 for v,t in refs),'Unsupported lawn source indices')
   rows.append([(positions[v-1],(uvs[t-1][0],1-uvs[t-1][1])) for v,t in refs])
 require(len(rows)==27,'Lawn source triangle count changed')
 return rows

def native_snapshot(u,mesh):
 d=mesh.get_static_mesh_description(0);require(d is not None and d.get_triangle_count()>0,'Missing lawn source MeshDescription');rows=[];instances=set()
 for index in range(d.get_triangle_count()):
  tri=u.TriangleID(id_value=index);require(d.is_triangle_valid(tri),'Lawn source triangle ID hole');row=[]
  for corner in range(3):
   instance=d.get_triangle_vertex_instance(tri,corner);require(d.is_vertex_instance_valid(instance),'Invalid lawn corner')
   vertex=d.get_vertex_instance_vertex(instance);require(d.is_vertex_valid(vertex),'Invalid lawn vertex')
   p=d.get_vertex_position(vertex);uv=d.get_vertex_instance_uv(instance,0);v={'pCm':[float(p.x),float(p.y),float(p.z)],'uv0':[float(uv.x),float(uv.y)],'vertex':int(vertex.id_value),'instance':int(instance.id_value)}
   require(all(math.isfinite(x) for x in v['pCm']+v['uv0']),'Nonfinite lawn source vertex/UV');row.append(v);instances.add(v['instance'])
  rows.append(row)
 require(len(instances)==d.get_vertex_instance_count(),'Incomplete lawn corner readback')
 return {'rows':rows,'vertexCount':d.get_vertex_count(),'instanceCount':len(instances),'renderTriangles':mesh.get_num_triangles(0),'renderSections':mesh.get_num_sections(0),'uvChannels':mesh.get_num_tex_coords(0)}

def source_proof(snapshot,source):
 require(len(snapshot['rows'])==len(source),'Lawn MeshDescription/source triangle count differs')
 remaining=set(range(len(source)));maximum=maximum_uv=0.
 for row in snapshot['rows']:
  actual=[([v['pCm'][0]*10,-v['pCm'][1]*10,v['pCm'][2]*10],v['uv0']) for v in row];matches=[]
  for i in remaining:
   best=None
   for j in range(3):
    wanted=source[i][j:]+source[i][:j]
    pe=max(abs(x-y) for (p,_),(q,_) in zip(actual,wanted) for x,y in zip(p,q));ue=max(abs(x-y) for (_,p),(_,q) in zip(actual,wanted) for x,y in zip(p,q))
    if pe<=.002 and ue<=.000002 and (best is None or (pe,ue)<best):best=(pe,ue)
   if best is not None:matches.append((i,*best))
  require(len(matches)==1,'Lawn source triangle missing/ambiguous/reversed or UV0 changed')
  i,pe,ue=matches[0];remaining.remove(i);maximum=max(maximum,pe);maximum_uv=max(maximum_uv,ue)
 require(not remaining,'Incomplete lawn source triangle coverage')
 return {'method':'public-MeshDescription-position-UV0-cyclic-match','triangles':len(source),'windingMultiplicityVerified':True,'sourceToleranceMm':.002,'maximumPositionErrorMm':maximum,'uv0Tolerance':.000002,'maximumUv0Error':maximum_uv,'snapshotSha256':digest(snapshot),'nativeNormalTangentValuesRead':False}
