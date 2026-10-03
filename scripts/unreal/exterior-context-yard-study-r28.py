"""Bounded artistic yard layout around three existing modeled entrances.

Source-only: official footprint XY is retained, but yards, door use, surfaces
and planting are illustrative. No road connection/legal yard boundary inferred.
Future native base must be an actually saved clean R27, which is not fabricated.
"""
import hashlib
import json
import math
from pathlib import Path
import random
import shutil
import sys

sys.dont_write_bytecode=True
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import LineString, Point, Polygon, box, shape, mapping
from shapely.ops import unary_union, triangulate
from shapely.strtree import STRtree

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-study-r28.py'
OUTPUT=ROOT/'output/unreal/exterior-context-yard-20261002-r28-study'
TARGETS=('BU.572063','BU.3800911','BU.3852341')
SOURCES={
 'context':'output/unreal/exterior-context-20260927-r8/context-plan.json',
 'terrain':'output/unreal/exterior-terrain-20260926-r4/terrain-plan.json',
 'buildings':'output/unreal/exterior-buildings-20260926-r2/building-plan.json',
 'details':'output/unreal/exterior-context-20260930-r3/neighborhood-details.json',
 'ecology':'output/unreal/exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json',
 'nativeR16':'output/unreal/exterior-20261001-r16a/exterior-import-report.json',
 'plantGeometry':'output/unreal/exterior-canopy-fullness-integration-20261001-r2/geometry-manifest.json',
 'r18Geometry':'output/unreal/exterior-neighbor-finish-20261001-r18-study/neighbor-finish-geometry.json',
 'views':'output/unreal/exterior-20261002-r22c/Project/BreziTwin/Content/Data/viewpoints.json',
 'doorProducer':'scripts/unreal/exterior-neighborhood.py',
}


def require(ok,message):
 if not ok:raise ValueError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def pin(path):return {'path':str(path),'sha256':sha(path),'bytes':Path(path).stat().st_size}
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(path,value):
 with Path(path).open('x')as f:json.dump(value,f,separators=(',',':'),allow_nan=False);f.write('\n')
def polygons(geom):
 if geom.is_empty:return []
 if geom.geom_type=='Polygon':return [geom]
 if not hasattr(geom,'geoms'):return []
 return [p for g in geom.geoms for p in polygons(g)]


def entrance(building):
 edges=[]
 for rings in building['polygonsCm']:
  ring=rings[0][:-1]
  area=sum(a[0]*b[1]-a[1]*b[0]for a,b in zip(ring,ring[1:]+ring[:1]))/2
  if area<0:ring=list(reversed(ring))
  for a,b in zip(ring,ring[1:]+ring[:1]):
   length=math.dist(a,b)
   if length>=240:edges.append((a,length,[(b[i]-a[i])/length for i in range(2)]))
 a,length,t=max(edges,key=lambda r:r[1]);require(length>650,'Frozen producer has no entrance on target')
 o=[t[1],-t[0]]
 return {'sourceId':building['id'],'edgeOriginCm':a,'edgeLengthCm':length,'tangent':t,'outward':o,
  'doorCenterCm':[a[i]+t[i]*77.5+o[i]*8 for i in range(2)]+[building['eaveElevationCm']-building['estimatedWallHeightCm']+6],
  'sourceDoorPanelLocal':{'leftCm':35,'rightCm':120,'frontCm':8,'bottomAboveFloorCm':6,'heightCm':208},
  'doorObservedInReality':False,'sourceProducer':'Exact frozen longest-edge entrance loop in exterior-neighborhood.py139..148'}


class Ground:
 def __init__(self,context,terrain,domain):
  self.rows=[];shapes=[];bounds=domain.bounds
  for mesh in context['meshes']+terrain['meshes']:
   if mesh['material']not in ('context_fallow','context_meadow','context_crop','context_arable','context_track','context_distant_terrain'):continue
   vs=np.asarray(mesh['verticesCm']);tri=vs[np.asarray(mesh['indices']).reshape(-1,3)]
   low,high=tri[:,:,:2].min(axis=1),tri[:,:,:2].max(axis=1)
   mask=(high[:,0]>=bounds[0])&(high[:,1]>=bounds[1])&(low[:,0]<=bounds[2])&(low[:,1]<=bounds[3])
   for ordinal in np.flatnonzero(mask):
    row=tri[ordinal];p=Polygon(row[:,:2])
    if p.area>1e-8:shapes.append(p);self.rows.append((mesh['id'],mesh['material'],int(ordinal),row.tolist()))
  self.index=STRtree(shapes)
 def sample(self,xy):
  records=[]
  for idx in self.index.query(Point(xy)):
   identity,material,ordinal,(a,b,c)=self.rows[int(idx)]
   d=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
   u=((b[0]-xy[0])*(c[1]-xy[1])-(b[1]-xy[1])*(c[0]-xy[0]))/d
   v=((c[0]-xy[0])*(a[1]-xy[1])-(c[1]-xy[1])*(a[0]-xy[0]))/d;w=1-u-v
   if min(u,v,w)>=-1e-7:records.append((u*a[2]+v*b[2]+w*c[2],identity,material,ordinal,[u,v,w]))
  require(records,'No actual source ground below yard')
  z,identity,material,ordinal,weights=max(records)
  return {'zCm':float(z),'meshId':identity,'material':material,'triangleOrdinal':ordinal,'barycentric':weights,'measuredElevation':False}


def main():
 require(not OUTPUT.exists(),'Use a fresh isolated source study')
 data={k:read(ROOT/v)for k,v in SOURCES.items()if k!='doorProducer'}
 pins={k:pin(ROOT/v)for k,v in SOURCES.items()};native=data['nativeR16']
 require(pins['nativeR16']['sha256']=='1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122','Frozen original native basis differs')
 require(sha(ROOT/SOURCES['doorProducer'])==data['details']['generatorSha256'],'Frozen entrance producer differs')
 require(data['context']['activeDesign']==native['activeDesign']and native['setbacksMm']=={'street':3000,'east':3000},'C/B/B3000 differs')
 masks={k:shape(json.loads(v))for k,v in data['ecology']['exclusionDomainsCm'].items()}
 require(set(masks)=={'protected','subject','roads','buildings','cultivatedGround'},'Original exclusion masks differ')
 target_buildings=[next(b for b in data['buildings']['buildings']if b['id']==key)for key in TARGETS]
 feet={b['id']:unary_union([Polygon(r[0],r[1:])for r in b['polygonsCm']])for b in target_buildings}
 domains={key:feet[key].buffer(700).difference(unary_union([m.buffer(20)for m in masks.values()]))for key in TARGETS}
 all_domain=unary_union(list(domains.values()));ground=Ground(data['context'],data['terrain'],all_domain.buffer(50))
 surfaces=[];yards=[];roots=[];models={m['id']:m for m in data['plantGeometry']['meshes']}
 native_models={m['id']:m for m in native['savedPlantReadback']}
 colors={'entry_walk':(193,171,135),'service_court':(183,164,126),'soil_bed':(110,77,46),'worn_edge':(145,119,70)}
 recipes={'entry_walk':'context_track','service_court':'context_track','soil_bed':'context_garden_soil','worn_edge':'context_soil_exposure'}
 for index,b in enumerate(target_buildings):
  key=b['id'];door=entrance(b);a=door['edgeOriginCm'];t=door['tangent'];o=door['outward'];domain=domains[key]
  def world(s,d):return [a[i]+t[i]*s+o[i]*d for i in range(2)]
  def rectangle(s0,d0,s1,d1):return Polygon([world(s0,d0),world(s1,d0),world(s1,d1),world(s0,d1)])
  # Deliberate different uses: small cottage service court; long facade entry
  # court plus lateral planted strip; side-entry utility apron and two beds.
  width=(105,115,100)[index]
  pathline=LineString([world(77.5,21),world(77.5,190),world((250,325,205)[index],(370,430,350)[index]),world((250,325,205)[index],(585,650,560)[index])])
  walk=pathline.buffer(width/2,cap_style=2,join_style=1).intersection(domain)
  court=rectangle(*((120,365,500,685),(225,420,815,690),(105,350,535,650))[index]).intersection(domain).difference(walk)
  bed_defs=[[(505,175,760,595),(290,100,490,275)],[(840,175,1250,625),(405,130,705,300)],[(570,160,925,610),(145,125,430,265)]][index]
  beds=unary_union([rectangle(*r)for r in bed_defs]).intersection(domain).difference(unary_union([walk,court]).buffer(25))
  hard=unary_union([walk,court]);worn=hard.buffer(32).difference(hard).intersection(domain).difference(beds)
  row_geometries={'entry_walk':walk,'service_court':court,'soil_bed':beds,'worn_edge':worn}
  yard={'buildingSourceId':key,'sourceBuildingSha256':digest(b),'entrance':door,'layoutPurpose':[
   'Short gravel entry linked to an existing modeled small-cottage door and a restrained utility court; two shrub/soil pockets.',
   'Gravel entry walk leads to a wider front court; planting occupies a lateral strip rather than the access.',
   'West-facing modeled entrance receives a side utility apron with two differently shaped planted beds.'][index],
   'perimeterIsLegalParcelBoundary':False,'streetConnectionProposed':False,'drivewayOrVehicleAccessVerified':False,
   'authoredLocalEnvelopeCm':700,'entryWalkWidthCm':width,'surfaces':{},'maskDistancesCm':{k:feet[key].distance(m)for k,m in masks.items()if k!='buildings'}}
  for role,geometry in row_geometries.items():
   geometry=unary_union(polygons(geometry))
   require(not geometry.is_empty and geometry.is_valid,'Empty/invalid purposeful yard part')
   require(geometry.difference(domain).area<1e-5,'Yard detail leaves exact allowed envelope')
   surfaces.append({'id':'yard_r28_'+key.replace('.','_')+'_'+role,'buildingSourceId':key,'role':role,'materialKey':recipes[role],
    'domainCm':mapping(geometry),'sourceAreaM2':geometry.area/10000,'sourceVerticesMustUseHighestExistingGround':True,
    'maximumAddedReliefCm':{'entry_walk':1.5,'service_court':1.2,'soil_bed':.7,'worn_edge':.3}[role],
    'edgeTreatment':'Hard gravel core, narrow irregular soil transition; future native opacity feather required for soil/worn perimeter',
    'nativeApplied':False})
   yard['surfaces'][role]={'areaM2':geometry.area/10000,'geometrySha256':digest(mapping(geometry))}
  # Small shrubs are organized within the two functional beds. The longer
  # bed gets a staggered depth cluster, rather than a single uniform row.
  rng=random.Random(60122628+index);selected=[]
  for bed_index,local_box in enumerate(bed_defs):
   s0,d0,s1,d1=local_box
   points=[(s0+(s1-s0)*f,(d0+d1)/2+rng.uniform(-22,22))for f in (.25,.55,.80)]
   if bed_index==0:points.extend([((s0+s1)/2+rng.uniform(-10,10),(d0+d1)/2+offset)for offset in (-125,120)])
   for s,d in points:
    model_id='shrub_broadleaf_'+('abc'[(len(roots)+index)%3]);model=models[model_id]
    height=rng.uniform(58,88);scale=height/model['heightCm']
    radius=max(math.hypot(max(abs(l['expectedBoundsCm']['min'][0]),abs(l['expectedBoundsCm']['max'][0])),max(abs(l['expectedBoundsCm']['min'][1]),abs(l['expectedBoundsCm']['max'][1])))for l in model['lods'])*scale
    xy=world(s,d);footprint=Point(xy).buffer(radius/math.cos(math.pi/128),quad_segs=32)
    if not beds.covers(footprint)or not domain.covers(footprint):continue
    if any(math.dist(xy,r['positionCm'][:2])<radius+r['radialEnvelopeCm']+12 for r in roots):continue
    evidence=ground.sample(xy);minimum_z=min(l['expectedBoundsCm']['min'][2]for l in model['lods'])*scale
    root={'id':'yard_r28_plant_'+str(len(roots)),'buildingSourceId':key,'bedIndex':bed_index,'modelId':model_id,
     'positionCm':xy+[evidence['zCm']-minimum_z+.6],'yawDegrees':rng.uniform(-180,180),'uniformScale':scale,'heightCm':height,
     'radialEnvelopeCm':radius,'wholeCrownInsideAuthoredBedAndAllExclusions':True,'sourceGround':evidence,
     'sourceModeling':model['composition'],'nativeMesh':native_models[model_id]['mesh'],'nativeMaterials':native_models[model_id]['materials'],
     'sourceTrianglesByLOD':native_models[model_id]['lodTriangles'],'nativeApplied':False}
    roots.append(root);selected.append(root['id'])
  yard['plantIds']=selected;yards.append(yard)
 require(len(roots)>=9,'Too few meaningful whole-envelope shrubs in purposeful beds')
 material_refs={key:native['materials']['materials'][key]for key in set(recipes.values())}
 for key,row in material_refs.items():
  for role,rec in row['recipe']['maps'].items():
   path=Path(rec['path']);require(sha(path)==rec['sha256'],'Existing photographic pixels changed');pins[key+':'+role]=pin(path)
 for row in models.values():
  if row['id']in{r['modelId']for r in roots}:
   p=Path(row['glbPath']);require(sha(p)==row['glbSha256'],'Existing shrub source changed');pins[row['id']+':glb']=pin(p)
 for surface in surfaces:
  p=shape(surface['domainCm']);surface['groundWitnesses']=[{'xyCm':list(xy),'source':ground.sample(xy)}for polygon in polygons(p)for xy in list(polygon.exterior.coords)[:-1]]
 OUTPUT.mkdir(parents=True)
 write(OUTPUT/'yard-layout.json',{'yards':yards,'surfaces':surfaces,'planting':roots,'existingMaterialReferences':material_refs})
 write(OUTPUT/'source-exclusion-masks.json',{k:mapping(v)for k,v in masks.items()})
 draw_preview(OUTPUT,target_buildings,feet,yards,surfaces,roots,domains,data['views'],colors)
 snapshots=OUTPUT/'source-producer.py';shutil.copyfile(ROOT/OWNER,snapshots)
 audit={'sourceOnly':True,'targetBuildingCount':3,'originalBuildingFootprintsChanged':False,'existingArchitectureChanged':False,
  'surfaceCount':len(surfaces),'surfaceAreaM2':sum(r['sourceAreaM2']for r in surfaces),'shrubs':len(roots),
  'sourceInstanceTrianglesByLOD':[sum(r['sourceTrianglesByLOD'][lod]for r in roots)for lod in range(3)],
  'buildingExclusionBufferCm':20,'otherExclusionBufferCm':20,'newTreeRoots':0,'existingRootsRemoved':0,
  'originalNativeMaterialGraphsChanged':False,'newSourceTexturePixels':0,'nativeApplied':False,'nativeAppearanceAccepted':False,
  'performanceAccepted':False,'shippingAccepted':False,'fullPhotorealismAccepted':False}
 plan={'schema':'brezi-context-yard-artistic-source-layout-r28','owner':OWNER,'status':'source-only-layout-review-native-pending',
  'inputFiles':pins,'generator':pin(ROOT/OWNER),'snapshot':pin(snapshots),'layout':pin(OUTPUT/'yard-layout.json'),
  'masks':pin(OUTPUT/'source-exclusion-masks.json'),'activeDesign':native['activeDesign'],'setbacksMm':native['setbacksMm'],'audit':audit,
  'futureBase':'Actual saved clean R27 required; no future native report or asset receipt is asserted here',
  'limits':['Source entrance locations are artistic old model geometry, not observed real doors.',
   'Selected houses are outside the central authored parcel/land-use context. Local7m envelopes are not legal yard parcels.',
   'No road extension, vehicle route, fence/property boundary, terrain survey or new architecture is inferred.',
   'Preview is a marked source layout, not an Unreal render. Native source/material/whole scene guards and saved visual pairs are still required.',
   'Reused broadleaf shrubs are old seven-shoot authored source compositions with photo textures, not a whole-plant scan.']}
 write(OUTPUT/'yard-source-plan.json',plan)
 print(json.dumps({'plan':pin(OUTPUT/'yard-source-plan.json'),'audit':audit,'preview':str(OUTPUT/'yard-layout-preview.png')}))


def draw_preview(output,buildings,feet,yards,surfaces,roots,domains,views,colors):
 image=Image.new('RGB',(1600,1650),(236,236,224));draw=ImageDraw.Draw(image)
 font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
 title=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',28)
 bounds=unary_union(list(domains.values())+list(feet.values())).bounds
 scale=min(1350/(bounds[2]-bounds[0]),1250/(bounds[3]-bounds[1]))
 def xy(p):return (125+(p[0]-bounds[0])*scale,180+(bounds[3]-p[1])*scale)
 def paint(geometry,fill,outline):
  for polygon in polygons(geometry):
   draw.polygon([xy(p)for p in polygon.exterior.coords],fill=fill,outline=outline,width=2)
   for ring in polygon.interiors:draw.polygon([xy(p)for p in ring.coords],fill=(215,219,187))
 draw.text((45,25),'R28: PURPOSEFUL CONTEXT YARDS / SOURCE LAYOUT ONLY',font=title,fill=(31,40,38))
 draw.text((45,67),'Illustrative local courts and planted beds; no legal yard boundary or street access inferred.',font=font,fill=(54,65,54))
 for domain in domains.values():paint(domain,(219,226,196),(178,190,162))
 for row in surfaces:paint(shape(row['domainCm']),colors[row['role']],(92,83,64))
 for key,footprint in feet.items():
  paint(footprint,(178,184,188),(65,67,72));centroid=xy(footprint.centroid.coords[0]);draw.text((centroid[0]-70,centroid[1]-15),key,font=font,fill=(15,20,24))
 for root in roots:
  p=xy(root['positionCm']);r=root['radialEnvelopeCm']*scale
  draw.ellipse((p[0]-r,p[1]-r,p[0]+r,p[1]+r),fill=(75,105,52),outline=(32,65,30),width=2)
 for yard in yards:
  door=yard['entrance'];p=xy(door['doorCenterCm']);end=xy([door['doorCenterCm'][i]+door['outward'][i]*125 for i in range(2)])
  draw.line([p,end],fill=(177,47,34),width=5);draw.ellipse((p[0]-5,p[1]-5,p[0]+5,p[1]+5),fill=(177,47,34))
  draw.text((end[0]+9,end[1]),'existing modeled door',font=font,fill=(139,40,30))
 camera=next(v for v in views['views']if v['id']=='neighbor-finish-close-r18');p=xy(camera['eyeCm']);q=xy(camera['targetCm'])
 draw.line([p,q],fill=(31,95,165),width=3);draw.ellipse((p[0]-7,p[1]-7,p[0]+7,p[1]+7),fill=(31,95,165));draw.text((p[0]+12,p[1]),'actual close-camera XY',font=font,fill=(31,95,165))
 draw.line([(80,1470),(80+500*scale,1470)],fill=(20,20,20),width=4);draw.text((80,1485),'5 metres in source coordinates',font=font,fill=(25,25,25))
 for i,(role,color)in enumerate(colors.items()):
  x=480+(i%2)*470;y=1450+(i//2)*55
  draw.rectangle((x,y,x+32,y+28),fill=color,outline=(50,50,50));draw.text((x+44,y+2),role.replace('_',' '),font=font,fill=(30,35,29))
 draw.text((45,1590),'No native application, performance or photorealism acceptance. Architecture, roads and original vegetation stay intact.',font=font,fill=(69,48,35))
 image.save(output/'yard-layout-preview.png')


if __name__=='__main__':main()
