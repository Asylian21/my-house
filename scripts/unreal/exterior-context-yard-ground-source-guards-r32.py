"""Independent stdlib source checks for one selected R32 proposal.

No Unreal import, native-base adoption or material/scene acceptance. The
actual R30 saved base is deliberately pending in the selected source plan.
"""
import importlib.util
from fractions import Fraction
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-ground-source-guards-r32.py'
PLAN=ROOT/'output/unreal/exterior-context-yard-ground-20261002-r32-study-r5/yard-ground-study-plan.json'
PLAN_SHA='8378d06f00e9a11dceff51e4eb12a270eff492d6f729f09d3dfd804de326f650'
spec=importlib.util.spec_from_file_location('r32_frozen_source_mask_and_ground_predicates',ROOT/'scripts/unreal/exterior-context-yard-native-guards-r28.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
require,read,sha,pin,check_pin,digest=(getattr(old,k)for k in('require','read','sha','pin','check_pin','digest'))
Q_PATH=ROOT/'scripts/unreal/exterior-context-yard-ground-quantization-r32-r5.py'


def source_module():
 spec=importlib.util.spec_from_file_location('r32_selected_exact_xy_source',Q_PATH)
 q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q);return q


def check_glb(file,meshes):
 raw=file.read_bytes();require(struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw)),'Selected generated GLB framing changed')
 size,kind=struct.unpack_from('<II',raw,12);require(kind==0x4e4f534a,'Selected generated JSON chunk changed')
 doc=json.loads(raw[20:20+size]);offset=20+size;length,kind=struct.unpack_from('<II',raw,offset)
 require(kind==0x004e4942 and offset+8+length==len(raw),'Selected generated binary chunk changed');blob=raw[offset+8:]
 def values(index,width,code):
  a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
  require(a['componentType']==(5126 if code=='f' else 5125),'Generated attribute component changed')
  start=v.get('byteOffset',0)+a.get('byteOffset',0);size2=struct.calcsize('<'+code*width)
  return [list(struct.unpack_from('<'+code*width,blob,start+i*size2))for i in range(a['count'])]
 require(len(doc['meshes'])==len(doc['nodes'])==len(meshes)==3 and 'materials'not in doc,'Exactly three generated masters required')
 for i,row in enumerate(meshes):
  node=doc['nodes'][i];mesh=doc['meshes'][i]
  require(node=={'name':row['id']+'_LOD0','mesh':i}and len(mesh['primitives'])==1,'Generated master transform/primitive changed')
  primitive=mesh['primitives'][0];attrs=primitive['attributes']
  expected={'POSITION':[[old.f32(x/100),old.f32(z/100),old.f32(y/100)]for x,y,z in row['verticesCm']],
   'NORMAL':[[old.f32(x),old.f32(z),old.f32(y)]for x,y,z in row['normals']],
   'TEXCOORD_0':[[old.f32(v)for v in p]for p in row['uv0']],
   'TEXCOORD_1':[[old.f32(v)for v in p]for p in row['uv1']]}
  require(set(attrs)==set(expected)and primitive['mode']==4,'Generated source attributes/mode changed')
  for key in expected:
   got=values(attrs[key],3 if key in('POSITION','NORMAL') else 2,'f')
   require(got==expected[key],'Written full source F32 attribute differs: '+key)
   if key=='POSITION':
    a=doc['accessors'][attrs[key]]
    require(a['min']==[min(p[k]for p in got)for k in range(3)]and a['max']==[max(p[k]for p in got)for k in range(3)],'Written bounds changed')
  require([v[0]for v in values(primitive['indices'],1,'I')]==row['indices'],'Written ordered full source topology changed')
 return {'writtenSourceGlbAllAttributesAndIndicesExactlyF32':True,'sourceTangentAttributePresent':False,'nativeExecuted':False}


def clip_exact(subject,clip):
 """Exact rational intersection of clockwise convex triangle footprints."""
 def side(a,b,p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
 result=list(subject)
 for a,b in zip(clip,clip[1:]+clip[:1]):
  previous=result
  if not previous:return []
  result=[];p=previous[-1];sp=side(a,b,p)
  for c in previous:
   sc=side(a,b,c)
   if (sp<=0)!=(sc<=0):
    t=sp/(sp-sc);result.append(tuple(p[k]+t*(c[k]-p[k])for k in(0,1)))
   if sc<=0:result.append(c)
   p,sp=c,sc
  compact=[]
  for point in result:
   if not compact or point!=compact[-1]:compact.append(point)
  if len(compact)>1 and compact[0]==compact[-1]:compact.pop()
  result=compact
 return result


def signed_twice_area(points):
 return sum(a[0]*b[1]-a[1]*b[0]for a,b in zip(points,points[1:]+points[:1]))


def exact_height(triangle,xy):
 a,b,c=triangle;den=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);require(den!=0,'Depth footprint became zero')
 u=((b[0]-xy[0])*(c[1]-xy[1])-(b[1]-xy[1])*(c[0]-xy[0]))/den
 v=((c[0]-xy[0])*(a[1]-xy[1])-(c[1]-xy[1])*(a[0]-xy[0]))/den
 return u*a[2]+v*b[2]+(1-u-v)*c[2]


def check_depth(meshes):
 """Every hard/underlay intersection vertex, using exact F32 rationals."""
 def triangles(mesh):
  points=[tuple(Fraction(v)for v in p)for p in old.native_points(mesh)]
  return [tuple(points[j]for j in mesh['indices'][i:i+3])for i in range(0,len(mesh['indices']),3)]
 soft=triangles(next(m for m in meshes if m['role']=='yard_substrate'));grid={};boxes=[]
 def bbox(tri):return (min(p[0]for p in tri),min(p[1]for p in tri),max(p[0]for p in tri),max(p[1]for p in tri))
 def keys(bounds):
  x0,y0,x1,y1=bounds
  return ((x,y)for x in range(x0//40,x1//40+1)for y in range(y0//40,y1//40+1))
 for i,t in enumerate(soft):
  box=bbox(t);boxes.append(box)
  for k in keys(box):grid.setdefault(k,[]).append(i)
 minimum=None;maximum=None;overlaps=extrema=0
 for mesh in meshes:
  if mesh['role']=='yard_substrate':continue
  for hard in triangles(mesh):
   hb=bbox(hard);candidates={i for k in keys(hb)for i in grid.get(k,[])}
   for i in candidates:
    sb=boxes[i]
    if hb[0]>sb[2]or hb[2]<sb[0]or hb[1]>sb[3]or hb[3]<sb[1]:continue
    intersection=clip_exact([p[:2]for p in hard],[p[:2]for p in soft[i]])
    if len(intersection)<3 or signed_twice_area(intersection)==0:continue
    require(signed_twice_area(intersection)<0,'Exact hard/underlay intersection inverted');overlaps+=1
    for xy in intersection:
     gap=exact_height(hard,xy)-exact_height(soft[i],xy);extrema+=1
     require(gap>0,'Exact F32 hard surface is coplanar with/below its underlay')
     minimum=gap if minimum is None else min(minimum,gap);maximum=gap if maximum is None else max(maximum,gap)
 require(overlaps>0 and extrema>0 and minimum>0,'Complete positive hard/underlay separation not observed')
 return {'independentExactRationalF32DepthValidated':True,'independentExactTriangleIntersections':overlaps,
  'independentExactIntersectionExtrema':extrema,'independentMinimumHardAboveUnderlayCm':float(minimum),
  'independentMaximumHardAboveUnderlayCm':float(maximum),'exactMinimumRational':[minimum.numerator,minimum.denominator],
  'exactMaximumRational':[maximum.numerator,maximum.denominator],'nativeExecuted':False}


def check_topology(piece,q):
 accounting=piece['quantizedTopologyAccounting'];planar=piece['quantizedPlanarPartition']
 require(accounting['discardedFaceCount']==0 and accounting['discardedExactZeroThreeDimensionalAreaFaces']==[]
  and accounting['discardedDecodedProjectedFootprintAreaCm2']==0. and accounting['approximateAreaThresholdUsed']is False
  and accounting['nonzeroFacesDropped']is False,'Post-height topology cannot discard or weaken nonzero faces')
 require(planar['wholeOriginalAuthoredCellPartitionConserved']is True
  and planar['allCoincidentFloorCoordinatesShareSingleHeightEvaluation']is True
  and planar['positiveAreaQuantizedRegionsDiscarded']is False and planar['approximateAreaThresholdUsed']is False,
  'XY-first cell footprint policy changed')
 zero=0
 for cell in planar['cells']:
  require(cell['wholeQuantizedCellUnionConservedExactly']is True and cell['positiveAreaPolygonsDropped']is False
   and cell['approximateAreaThresholdUsed']is False and cell['discardedQuantizedFootprintAreaCm2']==0.,'Quantized cell union changed')
  for region in cell['discardedBeforeHeightExactZeroProjectedRegions']:
   source=region['sourceProjectedPointsCm'];xy=region['quantizedProjectedPointsCm']
   require(xy==[[q.stable_native_coordinate(v)for v in p]for p in source]
    and region['quantizedProjectedAreaCm2']==0. and region['heightEvaluated']is False,
    'Zero projected region was not an exact pre-height native F32 conversion')
   a,b,c=xy;require((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])==0.,'A positive quantized floor region was discarded')
   zero+=1
 return zero


def check_geometry(proposal,layout,data,polygons,masks,q):
 require([r['role']for r in proposal['meshes']]==['entry_walk','service_court','yard_substrate'],'Exactly three source ground roles required')
 originals={r['id']:r for r in layout['surfaces']};triangles=vertices=zeros=0;corner_hashes={}
 for mesh in proposal['meshes']:
  vs,ids=mesh['verticesCm'],mesh['indices'];normals=mesh['normals'];uv0,uv1=mesh['uv0'],mesh['uv1']
  require(mesh['id']=='yard_ground_r32_'+mesh['role']and mesh['sourceWinding']=='clockwise'
   and mesh['nativeApplied']is False and mesh['nativeNormalTangentReadbackAvailable']is False,
   'Unknown ground master or native frame claim')
  require(len(vs)==len(normals)==len(uv0)==len(uv1)==len(mesh['sourceGroundVertexWitnesses'])
   and len(ids)%3==0 and all(type(i)is int and 0<=i<len(vs)for i in ids),'Source attributes/indices differ')
  for i,(point,n,uv,mask)in enumerate(zip(vs,normals,uv0,uv1)):
   require(old.finite(point,3)and old.finite(n,3)and old.finite(uv,2)and old.finite(mask,2)
    and n[2]>0. and abs(sum(v*v for v in n)-1.)<1e-12,'Nonfinite or nonunit source ground frame')
   require(uv==[point[0]/100.,point[1]/100.]and 0.<=mask[0]<=1. and 0.<=mask[1]<=1.,'Metric UV or coverage/layer channels changed')
   require(all(q.stable_native_coordinate(v)==v for v in point[:2]),'Floor XY no longer equals final native F32 positions')
   w=mesh['sourceGroundVertexWitnesses'][str(i)];z=old.ground_check(w,point,data)
   require(point[2]==z+w['artistAddedReliefCm']and 0.<w['artistAddedReliefCm']<=1.5,'Source ground/artist relief changed')
   require(all(not mask2.contains(point[:2])for mask2 in masks.values()),'Actual source floor enters an original exclusion')
  require(len(mesh['sourceSurfaceRanges'])==3,'Exactly three yard pieces per master required')
  for piece in mesh['sourceSurfaceRanges']:
   zeros+=check_topology(piece,q);identity=piece['sourcePieceId']
   if mesh['role']!='yard_substrate':
    original_id=identity.replace('yard_ground_r32_','yard_r28_')
    require(original_id in originals and piece['domainCm']==originals[original_id]['domainCm'],'Original hard authored footprint changed')
   domain=polygons._PolygonIndex(piece['quantizedPlanarPartition']['quantizedFloorDomainCm'])
   for offset in range(piece['firstTriangle']*3,(piece['firstTriangle']+piece['triangles'])*3,3):
    tri=[vs[i][:2]for i in ids[offset:offset+3]]
    require(polygons._cross(*tri)<0.,'A nonzero source floor face inverted or became degenerate')
    domain.triangle_inside(tri)
   require(piece['quantizedPlanarPartition']['authoredToProposedNativeF32FloorSymmetricDifferenceAreaCm2']>=0.,'Footprint drift missing')
  triangles+=len(ids)//3;vertices+=len(vs);corner_hashes[mesh['id']]=digest(old.corners(mesh))
 require(triangles==32878 and vertices==17095 and zeros==21,'Selected source topology census changed')
 return {'groundTriangles':triangles,'groundVertices':vertices,'exactZeroProjectedRegionsBeforeHeight':zeros,
  'postHeightFacesDiscarded':0,'sourceF32CornerHashes':corner_hashes,'nativeExecuted':False}


def check_roots(proposal,layout,data,polygons,masks):
 roots=proposal['planting'];require(len(roots)==1274 and len({r['id']for r in roots})==1274,'Exact selected new-root identities required')
 require(proposal['retainedShrubIds']==[r['id']for r in layout['planting']],'Original thirteen shrub roots changed')
 masters={r['id']:r for r in data['nativeR16']['savedPlantReadback']};models={r['id']:r for r in data['plantGeometry']['meshes']}
 domains={k:polygons._PolygonIndex(v)for k,v in proposal['plantingDomainsCm'].items()};count={};budget=[0,0,0]
 def source_points(model):
  file=Path(model['glbPath']);require(sha(file)==model['glbSha256'],'Existing three-LOD plant source changed')
  raw=file.read_bytes();require(struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw)),'Existing source GLB framing changed')
  length,kind=struct.unpack_from('<II',raw,12);require(kind==0x4e4f534a,'Existing source GLB JSON missing')
  doc=json.loads(raw[20:20+length]);blob=raw[28+length:];result=[]
  for lod in model['lods']:
   node=next(n for n in doc['nodes']if n.get('name')==lod['nodeName'])
   require(not any(k in node for k in('translation','rotation','scale','matrix')),'Existing source basis transform changed')
   for primitive in doc['meshes'][node['mesh']]['primitives']:
    a=doc['accessors'][primitive['attributes']['POSITION']];v=doc['bufferViews'][a['bufferView']]
    require(a['componentType']==5126 and a['type']=='VEC3','Existing source POSITION basis changed')
    offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12)
    for i in range(a['count']):
     x,z,y=struct.unpack_from('<fff',blob,offset+i*stride);result.append([x*100,y*100,z*100])
  require(result,'Empty source plant');return result
 decoded={key:source_points(models[key])for key in proposal['sourcePlantModels']}
 shrubs=layout['planting']
 for i,row in enumerate(roots):
  key=row['modelId'];require(key in('grass_medium_02_a','grass_bermuda_clump_a','celandine_01_e')and row['id']=='yard_ground_r32_plant_'+str(i),
   'Unselected plant shape or original-root replacement introduced')
  require(row['nativeMesh']==masters[key]['mesh']and row['nativeMaterials']==masters[key]['materials']
   and row['nativeLodTriangles']==masters[key]['lodTriangles'],'Existing native geometry/material/three-LOD route changed')
  require(row['nativeRootFrameMeasured']is False and row['nativeApplied']is False
   and old.finite(row['positionCm'],3)and math.isfinite(row['yawDegrees'])and row['uniformScale']>0.,'Root transform or evidence claim changed')
  require(row['uniformScale']==row['heightCm']/models[key]['heightCm'],'Declared authored uniform height fit differs')
  center=row['positionCm'][:2];radius=row['allLodSourceRadialEnvelopeCm'];domain=domains[row['buildingSourceId']]
  require(math.isfinite(radius)and radius>0. and radius==proposal['sourcePlantModels'][key]['sourceAllLodRadialEnvelopeCm']*row['uniformScale']
   and row['sourceAllLodVerticesChecked']==len(decoded[key]),'Source all-LOD radius/count binding changed')
  require(domain.contains(center)and domain.distance(center,radius+1)>radius,'Whole low-growth crown escapes its clipped planting domain')
  require(all(not mask.contains(center)and mask.distance(center,radius+21)>radius+20 for mask in masks.values()),'Whole crown enters an original source exclusion')
  for shrub in shrubs:
   require(math.dist(center,shrub['positionCm'][:2])>radius+shrub['radialEnvelopeCm']+12.,'New growth overlaps original conservative shrub circle')
  old.ground_check(row['sourceGround'],row['positionCm'],data)
  co,si=math.cos(math.radians(row['yawDegrees'])),math.sin(math.radians(row['yawDegrees']));scale=row['uniformScale']
  require(all(domain.contains([center[0]+scale*(co*x-si*y),center[1]+scale*(si*x+co*y)])for x,y,z in decoded[key]),
   'A full three-LOD original source vertex left the clipped planting domain')
  require(row['sourceAllLodContainingCircleInsidePlantingDomain']is True,'Missing full source crown containment')
  count[key]=count.get(key,0)+1
  for lod in range(3):budget[lod]+=row['nativeLodTriangles'][lod]
 require(count=={'grass_medium_02_a':900,'grass_bermuda_clump_a':234,'celandine_01_e':140}
  and budget==[1151654,672408,335832],'Actual selected source population/LOD cost changed')
 return {'newSourceRoots':1274,'retainedOriginalShrubs':13,'sourceTrianglesByLod':budget,
  'allThreeLodSourceVerticesIndependentlyInsidePlantingDomains':True,'sourceNativeFrameMeasured':False}


def load_source():
 require(sha(PLAN)==PLAN_SHA,'Only the selected R32 source candidate is accepted')
 plan=read(PLAN);require(plan['schema']=='brezi-context-yard-resolved-edge-and-clipped-low-growth-source-r32-r5'
  and plan['owner']=='scripts/unreal/exterior-context-yard-ground-study-r32-r5.py'
  and plan['selectedNativeBase']is None and plan['selectedNativeBasePending']is True,'Source cannot invent an actual R30 base')
 for row in plan['inputFiles']:check_pin(row)
 for key in('edgeDiagnosis','materialCopyProposals','sourceOverlapDepthProof','sourceGlbValidation'):check_pin(plan[key])
 require(check_pin(plan['generator']).read_bytes()==check_pin(plan['snapshot']).read_bytes(),'Selected producer snapshot changed')
 q=source_module();proposal=read(check_pin(plan['proposal']));layout=read(check_pin(proposal['retainedLayout']))
 lp=read(ROOT/'output/unreal/exterior-context-yard-20261002-r28-study/yard-source-plan.json')
 data={k:read(check_pin(v))for k,v in lp['inputFiles'].items()if k in('context','terrain','nativeR16','plantGeometry')}
 polygons=old.index_helper();masks={k:polygons._PolygonIndex(v)for k,v in read(check_pin(proposal['sourceExclusionMasks'])).items()}
 geometry=check_geometry(proposal,layout,data,polygons,masks,q);glb=check_glb(check_pin(plan['sourceGlb']),proposal['meshes']);depth=check_depth(proposal['meshes'])
 roots=check_roots(proposal,layout,data,polygons,masks)
 for key in('nativeApplied','nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted','shippingAccepted'):
  require(plan['audit'][key]is False,'Source proposal fabricates acceptance')
 require(plan['audit']['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}
  and plan['audit']['setbacksMm']=={'street':3000,'east':3000},'Main design/setbacks changed')
 return plan,proposal,{'scope':'INDEPENDENT_STDLIB_SELECTED_SOURCE_MASK_AND_FRAME_GUARDS_ONLY',**geometry,**glb,**depth,**roots,
  'nativeBasePending':True,'nativeExecuted':False,'nativeAppearanceAccepted':False,'performanceAccepted':False}


if __name__=='__main__':
 _,_,summary=load_source();print(json.dumps(summary,indent=2))
