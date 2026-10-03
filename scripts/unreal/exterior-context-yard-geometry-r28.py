"""One source-only four-mesh yard realization of the frozen R28 layout.

Original layout, entrances and plants are retained. Ground comes from actual
source triangles. Two new material-copy proposals feather soil/worn edges;
no existing texture pixels/graphs or native projects are written here.
"""
from collections import Counter
import importlib.util
import json
import math
from pathlib import Path
import shutil
import struct
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-geometry-r28.py'
OUTPUT=ROOT/'output/unreal/exterior-context-yard-20261002-r28-geometry-study'
spec=importlib.util.spec_from_file_location('r28_selected_layout_guard',ROOT/'scripts/unreal/exterior-context-yard-source-guards-r28.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
p=guard.p;require,read,sha,pin,digest=guard.require,guard.read,guard.sha,guard.pin,guard.digest
import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon,Point,box,shape,mapping
from shapely.ops import unary_union

ROLES=('entry_walk','service_court','soil_bed','worn_edge')
PREFIX='/Game/Brezi/ContextYard20261002R28'
FEATHER={'entry_walk':0.,'service_court':0.,'soil_bed':18.,'worn_edge':8.}
DITHER=Path('/Users/Shared/Epic Games/UE_5.8/Engine/Content/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.uasset')


def write(path,value):
 with Path(path).open('x')as stream:json.dump(value,stream,separators=(',',':'),allow_nan=False);stream.write('\n')


def triangles(domain):
 """Constrained clipping in40cm cells: holes/edges cannot be bridged."""
 x0,y0,x1,y1=domain.bounds
 for x in range(math.floor(x0/40)*40,math.ceil(x1/40)*40,40):
  for y in range(math.floor(y0/40)*40,math.ceil(y1/40)*40,40):
   clipped=domain.intersection(box(x,y,x+40,y+40))
   for poly in p.polygons(clipped):
    for tri in constrained_delaunay_triangles(poly).geoms:
     if tri.area<1e-8:continue
     require(poly.covers(tri),'Constrained triangulation escaped clipped source domain')
     points=list(tri.exterior.coords)[:3];a,b,c=points
     if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])>0:points=[a,c,b]
     yield points


def smooth(value):
 x=min(1.,max(0.,value));return x*x*(3-2*x)


def make_mesh(role,rows,ground):
 vertices=[];uv0=[];uv1=[];indices=[];witnesses={};surface_ranges=[]
 for row in rows:
  domain=shape(row['domainCm']);width=FEATHER[role];first=len(indices)//3;lookup={};polys=[]
  def vertex(xy):
   key=tuple(float(v)for v in xy)
   if key in lookup:return lookup[key]
   edge=Point(xy).distance(domain.boundary)
   coverage=smooth(edge/(width*(.88+.12*math.sin(xy[0]/43+xy[1]/57))))if width else 1.
   source=ground.sample(xy)
   noise=.5+.5*math.sin(xy[0]/37+math.sin(xy[1]/53)*.4)*math.cos(xy[1]/61)
   relief=.02+(row['maximumAddedReliefCm']-.02)*(.25+.75*noise)*(coverage if width else 1.)
   i=len(vertices);vertices.append([*map(float,xy),source['zCm']+relief]);uv0.append([xy[0]/100,xy[1]/100]);uv1.append([coverage,0.])
   witnesses[str(i)]={'surfaceId':row['id'],'sourceGround':source,'reliefCm':relief};lookup[key]=i;return i
  for tri in triangles(domain):
   indices.extend(vertex(xy)for xy in tri);polys.append(Polygon(tri))
  covered=unary_union(polys)
  require(covered.symmetric_difference(domain).area<1e-5,'Source triangulation omitted or widened the reviewed layout')
  surface_ranges.append({'surfaceId':row['id'],'firstTriangle':first,'triangles':len(indices)//3-first,
   'sourceDomain':row['domainCm'],'areaM2':domain.area/10000,'coverageOutsideSourceAreaCm2':covered.difference(domain).area})
 normals=np.zeros((len(vertices),3));vs=np.asarray(vertices)
 for face in np.asarray(indices).reshape(-1,3):
  a,b,c=vs[face];normal=np.cross(c-a,b-a)
  require(normal[2]>0,'Source native clockwise ground face inverted')
  normals[face]+=normal
 normals/=np.linalg.norm(normals,axis=1)[:,None]
 return {'id':'context_yard_r28_'+role,'role':role,'verticesCm':vertices,'normals':normals.tolist(),'uv0':uv0,'uv1':uv1,'indices':indices,
  'winding':'clockwise','nanite':False,'collision':'NoCollision','canEverAffectNavigation':False,'castShadow':False,
  'maxDrawDistanceCm':24000,'materialKey':rows[0]['materialKey'],'featherWidthCm':width,'sourceSurfaceRanges':surface_ranges,
  'sourceGroundVertexWitnesses':witnesses,'nativeApplied':False}


def write_glb(path,meshes):
 """Proven R21 axis route: native cm→glTF metres[x,z,y]."""
 binary=bytearray();accessors=[];views=[];exported=[];nodes=[]
 def accessor(values,kind,component=5126,target=34962):
  flat=[v for row in values for v in(row if isinstance(row,list)else[row])];binary.extend(b'\0'*((-len(binary))%4));start=len(binary)
  binary.extend(struct.pack('<'+('f'if component==5126 else'I')*len(flat),*flat));views.append({'buffer':0,'byteOffset':start,'byteLength':len(binary)-start,'target':target})
  entry={'bufferView':len(views)-1,'componentType':component,'count':len(values),'type':kind}
  if kind=='VEC3':entry.update(min=[min(v[k]for v in values)for k in range(3)],max=[max(v[k]for v in values)for k in range(3)])
  accessors.append(entry);return len(accessors)-1
 for mesh in meshes:
  attrs={'POSITION':accessor([[x/100,z/100,y/100]for x,y,z in mesh['verticesCm']],'VEC3'),
   'NORMAL':accessor([[x,z,y]for x,y,z in mesh['normals']],'VEC3'),'TEXCOORD_0':accessor(mesh['uv0'],'VEC2'),'TEXCOORD_1':accessor(mesh['uv1'],'VEC2')}
  name=mesh['id']+'_LOD0';exported.append({'name':name,'primitives':[{'attributes':attrs,'indices':accessor(mesh['indices'],'SCALAR',5125,34963),'mode':4}]});nodes.append({'name':name,'mesh':len(exported)-1})
 doc={'asset':{'version':'2.0','generator':OWNER},'scene':0,'scenes':[{'nodes':list(range(4))}],'nodes':nodes,'meshes':exported,
  'accessors':accessors,'bufferViews':views,'buffers':[{'byteLength':len(binary)}]}
 data=json.dumps(doc,separators=(',',':'),allow_nan=False).encode();data+=b' '*((-len(data))%4);binary+=b'\0'*((-len(binary))%4)
 Path(path).write_bytes(struct.pack('<III',0x46546c67,2,28+len(data)+len(binary))+struct.pack('<II',len(data),0x4e4f534a)+data+struct.pack('<II',len(binary),0x004e4942)+binary)


def decode_verify(path,meshes):
 data=path.read_bytes();require(struct.unpack_from('<III',data)==(0x46546c67,2,len(data)),'GLB header mismatch')
 size,kind=struct.unpack_from('<II',data,12);require(kind==0x4e4f534a,'GLB JSON type mismatch');doc=json.loads(data[20:20+size]);start=28+size
 bin_size,kind=struct.unpack_from('<II',data,20+size);require(kind==0x004e4942 and start+bin_size==len(data),'GLB BIN mismatch')
 blob=data[start:];require(len(doc['nodes'])==len(doc['meshes'])==4 and 'materials'not in doc,'Closed four unbound source meshes required')
 def values(index):
  a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
  xs=struct.unpack_from('<'+('f'if a['componentType']==5126 else'I')*(width*a['count']),blob,v['byteOffset'])
  return [list(xs[i:i+width])for i in range(0,len(xs),width)]
 f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
 audit=[]
 for m,entry in zip(meshes,doc['meshes']):
  primitive=entry['primitives'][0];attrs=primitive['attributes'];require(entry['name']==m['id']+'_LOD0'and len(entry['primitives'])==1 and set(attrs)=={'POSITION','NORMAL','TEXCOORD_0','TEXCOORD_1'},'GLB node/attribute mismatch')
  require(values(attrs['POSITION'])==[[f32(x/100),f32(z/100),f32(y/100)]for x,y,z in m['verticesCm']],'GLB source F32 positions changed')
  require(values(attrs['NORMAL'])==[[f32(x),f32(z),f32(y)]for x,y,z in m['normals']],'GLB source F32 normals changed')
  require(values(attrs['TEXCOORD_0'])==[[f32(v)for v in row]for row in m['uv0']]and values(attrs['TEXCOORD_1'])==[[f32(v)for v in row]for row in m['uv1']],'GLB source F32 UV channels changed')
  require([row[0]for row in values(primitive['indices'])]==m['indices'],'GLB source original topology changed')
  normals=values(attrs['NORMAL']);require(all(abs(sum(v*v for v in row)-1)<2e-7 for row in normals),'GLB normal normalization changed')
  audit.append({'id':m['id'],'vertices':len(m['verticesCm']),'triangles':len(m['indices'])//3,'orderedF32PositionNormalUv0Uv1AndIndicesVerified':True,
   'sourceNormalsComputedFromActualSurfaceGeometry':True,'sourceTangentsPresent':False,'nativeNormalTangentReadbackAvailable':False})
 return audit


def main():
 require(not OUTPUT.exists(),'Use a fresh isolated geometry output; reviewed layout is immutable')
 plan,layout,masks,data,models,mask_audit=guard.load_source()
 domain=unary_union([shape(row['domainCm'])for row in layout['surfaces']]);ground=p.Ground(data['context'],data['terrain'],domain.buffer(50))
 for root in layout['planting']:
  require(ground.sample(root['positionCm'][:2])==root['sourceGround'],'Actual source highest-ground plant contact differs')
 meshes=[make_mesh(role,[r for r in layout['surfaces']if r['role']==role],ground)for role in ROLES]
 require(sha(DITHER)=='e92577ec6d1ede4570eb7c8520ac63e82890cb7335cc9e389503406d145b72a7','Installed native dither source changed')
 recipes=[]
 for role in('soil_bed','worn_edge'):
  key=next(m['materialKey']for m in meshes if m['role']==role);original=layout['existingMaterialReferences'][key]
  recipes.append({'id':'context_yard_r28_'+role,'sourceNativeMaterial':original['asset'],'sourceGraphSha256':original['graphSha256'],
   'originalGraph':original['graph'],'baseRecipe':original['recipe'],'kind':'duplicate-existing-world-PBR-with-new-masked-UV1-dither-edge',
   'preserveAllExistingPBRRootsExceptOpacityMask':True,'newNodes':3,'newTextureObjects':0,'newMaterial':PREFIX+'/Materials/M_context_yard_r28_'+role,
   'featherCoverage':'UV1.x smooth source-boundary distance; serialized exact source values, not native pixels',
   'nativeDitherFunction':'/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.DitherTemporalAA',
   'installedDitherFunction':pin(DITHER),'nativeApplied':False,'nativeAppearanceAccepted':False})
 OUTPUT.mkdir(parents=True);write(OUTPUT/'yard-ground-geometry.json',{'meshes':meshes});write(OUTPUT/'yard-material-copy-recipes.json',recipes)
 write_glb(OUTPUT/'yard-ground.glb',meshes);glb_audit=decode_verify(OUTPUT/'yard-ground.glb',meshes)
 shutil.copyfile(ROOT/OWNER,OUTPUT/'geometry-producer.py')
 audit={'surfaceCount':12,'groundMeshes':4,'surfaceAreaM2':mask_audit['surfaceAreaM2'],'shrubs':13,
  'surfaceTriangles':sum(len(m['indices'])//3 for m in meshes),'surfaceVertices':sum(len(m['verticesCm'])for m in meshes),
  'newActorsProposed':7,'newHismGroupsProposed':3,'newMaterialGraphsProposed':2,'newTextureObjectsProposed':0,'newPackageCountProposed':9,
  'sourceShrubTrianglesByLod':plan['audit']['sourceInstanceTrianglesByLOD'],'allOriginalSceneActorsMustRemainExact':True,
  'maximumGroundReliefCm':max(w['reliefCm']for m in meshes for w in m['sourceGroundVertexWitnesses'].values()),
  'nativeApplied':False,'nativeAppearanceAccepted':False,'performanceAccepted':False,'fullPhotorealismAccepted':False,'shippingAccepted':False}
 write(OUTPUT/'yard-geometry-plan.json',{'schema':'brezi-context-yard-four-source-ground-meshes-r28','owner':OWNER,
  'status':'source-geometry-ready-actual-saved-clean-base-pending','sourceLayout':pin(guard.PLAN),'generator':pin(ROOT/OWNER),'snapshot':pin(OUTPUT/'geometry-producer.py'),
  'sourceGuard':pin(ROOT/guard.OWNER),'geometry':pin(OUTPUT/'yard-ground-geometry.json'),'glb':pin(OUTPUT/'yard-ground.glb'),
  'materialCopyRecipes':pin(OUTPUT/'yard-material-copy-recipes.json'),'sourceMaskAudit':mask_audit,'glbAudit':glb_audit,'audit':audit,
  'groundSourcePolicy':'Actual highest retained source terrain/context triangle at every vertex; artist microrelief only, no survey claim',
  'nativeBase':'Only actual saved clean R27 may be bound by later native preflight; no pending/future native result asserted',
  'nativeApplied':False,'nativeAppearanceAccepted':False,'performanceAccepted':False,'shippingAccepted':False})
 print(json.dumps({'plan':pin(OUTPUT/'yard-geometry-plan.json'),'audit':audit}))


if __name__=='__main__':main()
