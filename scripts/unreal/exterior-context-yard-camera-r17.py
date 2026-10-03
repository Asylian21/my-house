"""Source-only matched close camera for the first authored R28 cottage yard."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-camera-r17.py'
OUTPUT=ROOT/'output/unreal/exterior-context-yard-20261002-camera-r17-supplement'
SCHEMA='brezi-purposeful-first-context-yard-matched-camera-r17'
VIEW_ID='exterior-context-yard-572063-close-r17'
SOURCE=ROOT/'output/unreal/exterior-context-yard-20261002-r28-geometry-study/yard-geometry-plan.json'
SOURCE_SHA='f0f03736fc1c6d0992e2746626e35750dcacd575770b06f5f1308511a0358cb3'
BASE=ROOT/'output/unreal/exterior-20261002-r27a/realism-clean-integration-native-report.json'
BASE_SHA='5575c0e37a9d48733b5c7ed3746f1731cc2b7958634a845c87b9700ff4fc9498'
CANDIDATE=ROOT/'output/unreal/exterior-20261002-r28b/context-yard-native-report-r2.json'
CANDIDATE_SHA='dfbca65515fc08aea52515195ab5ef752fe07cdca622cd41964e99875ced2456'
s=importlib.util.spec_from_file_location('r17_frozen_camera_math',ROOT/'scripts/unreal/exterior-garden-fern-camera-r14.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
require,read,sha,pin,write,checked=(getattr(c,k)for k in('require','read','sha','pin','write','checked'))
require(sha(ROOT/c.OWNER)=='fa8b923ad0492e3d66108e43be26adbae9bdff14e6f11007ac989951f8649363','Frozen camera math changed')


def frame_points(view,points):
 f=c.unit(c.sub(view['targetCm'],view['eyeCm']));right=c.unit(c.cross(f,[0,0,1]));up=c.unit(c.cross(right,f));tan=math.tan(math.radians(view['horizontalFovDegrees']/2))
 result=[];distances=[]
 for point in points:
  d=c.sub(point,view['eyeCm']);depth=c.dot(d,f);require(depth>0,'Selected yard point lies behind close camera')
  result.append([c.dot(d,right)/(depth*tan),c.dot(d,up)/(depth*tan*9/16)]);distances.append(math.sqrt(c.dot(d,d)))
 maximum=[max(abs(p[k])for p in result)for k in range(2)];require(max(maximum)<1,'Selected whole yard does not fit proposed close camera')
 return {'pointsChecked':len(points),'maximumAbsoluteNormalizedXY':maximum,'entireSourceSupportInside16by9Frustum':True,
  'sourceEyeDistanceCm':[min(distances),max(distances)]}


def derive():
 require(sha(SOURCE)==SOURCE_SHA and sha(BASE)==BASE_SHA and sha(CANDIDATE)==CANDIDATE_SHA,'Exact actual yard source/native camera basis changed')
 plan=read(SOURCE);layout_plan=read(checked(plan['sourceLayout']));layout=read(checked(layout_plan['layout']));geometry=read(checked(plan['geometry']));native=read(CANDIDATE)
 require(native['status']=='verified-saved-purposeful-context-yards-overlay'and native['savedMapUnloadedReloaded']is True
  and native['nativeProcessId']==71235,'Only the actual saved R28b may supply the source camera')
 yard=next(r for r in layout['yards']if r['buildingSourceId']=='BU.572063');entrance=yard['entrance'];door=entrance['doorCenterCm'];out=entrance['outward'];tangent=entrance['tangent']
 supports=[];regions=[]
 for mesh in geometry['meshes']:
  span=next(s for s in mesh['sourceSurfaceRanges']if s['surfaceId'].startswith('yard_r28_BU_572063_'))
  ids=sorted(set(mesh['indices'][span['firstTriangle']*3:(span['firstTriangle']+span['triangles'])*3]));points=[mesh['verticesCm'][i]for i in ids]
  supports.extend(points);regions.append((span['surfaceId'],points))
 minmax=[[min(p[k]for p in supports),max(p[k]for p in supports)]for k in range(3)]
 center=[sum(v)/2 for v in minmax]
 # One purposeful perspective: thirteen metres outside the modeled door,
 # slight lateral offset, three metres above the retained source ground.
 view={'id':VIEW_ID,'label':'Susedný dvor · vstup, štrk a výsadba',
  'eyeCm':[door[k]+out[k]*1300+tangent[k]*200 for k in(0,1)]+[minmax[2][0]+300],
  'targetCm':[center[0],center[1],35.],'horizontalFovDegrees':62,
  'source':OWNER+': one artist source view, modeled entrance outward1300cm/lateral200cm, source-ground300cm eye; no survey or walking claim'}
 frames={identity:frame_points(view,points)for identity,points in regions}
 crowns=[]
 for root in native['savedReadback']['footprints']:
  if root['rootId']not in yard['plantIds']:continue
  source=next(r for r in layout['planting']if r['id']==root['rootId']);radius=source['radialEnvelopeCm'];xyz=source['positionCm']
  box=c.crown_box(xyz,radius,2.,root['actualNativeAbovePivotHeightCm'])
  crowns.append({'rootId':root['rootId'],'sourceWholeAllLodConservativeCrownFraming':c.frame_box(view,box)})
 require(len(crowns)==2,'Both first-yard shrub crowns must be framed')
 buildings=read(checked(layout_plan['inputFiles']['buildings']))['meshes']
 boxes=[]
 for mesh in buildings:
  points=mesh['verticesCm'];box=[[min(p[k]for p in points)for k in range(3)],[max(p[k]for p in points)for k in range(3)]];boxes.append((mesh['id'],box))
 eye_box=[[v-30 for v in view['eyeCm']],[v+30 for v in view['eyeCm']]]
 hits=[identity for identity,box in boxes if c.boxes_overlap(eye_box,box)];require(not hits,'Source camera eye intersects an original building box')
 audit={'sourceBuildingId':'BU.572063','sourceModeledDoor':entrance,'sourceYardAreaM2':sum(r['sourceAreaM2']for r in layout['surfaces']if r['buildingSourceId']=='BU.572063'),
  'sourceSurfaceFraming':frames,'sourceShrubCrownFraming':crowns,'sourceEyeClearanceBoxRadiusCm':30,
  'originalSourceBuildingMeshesChecked':len(boxes),'sourceEyeBuildingBoxHits':hits,
  'sourceOnlyCameraProposal':True,'nativeCameraTransformMeasured':False,'nativeFovMeasured':False,
  'nativeOcclusionOrPlantVisibilityMeasured':False,'raycastVisibilityClaimed':False,'physicalWalkingTraversalClaimed':False,
  'sourceDoorObservedInReality':False,'geometryOrPlantPlacementChanged':False,'lightingChanged':False}
 return view,audit,layout_plan,plan


def appended_bytes(original,view):
 doc=json.loads(original);require((json.dumps(doc,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()==original,'Original viewpoint serialization changed')
 require(doc['coordinateSystem']=='unreal-centimeters'and not any(v['id']==VIEW_ID for v in doc['views']),'Duplicate/unapproved close yard view')
 new=copy.deepcopy(doc);new['views'].append(view);prefix=json.dumps(doc['views'],indent=2,ensure_ascii=False).encode().rsplit(b'\n]',1)[0]
 require(json.dumps(new['views'],indent=2,ensure_ascii=False).encode().startswith(prefix+b','),'Original view rows lost byte-exact prefix')
 return(json.dumps(new,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()


def validated_supplement():
 row=read(OUTPUT/'context-yard-camera-supplement.json');require(row['schema']==SCHEMA and row['owner']==OWNER
  and row['status']=='source-only-purposeful-context-yard-camera-native-pending','Known source camera supplement required')
 for file,h in row['inputFiles'].items():require(sha(file)==h,'Frozen camera source changed')
 view,audit,_,_=derive();require(row['view']==view and row['sourceCameraAudit']==audit,'Source-derived yard camera/framing changed')
 require(checked(row['appendedViewpoints']).read_bytes()==appended_bytes(checked(row['originalViewpoints']).read_bytes(),view),'Exact camera prefix/append changed')
 require(row['baselineNativeReport']==pin(BASE)and row['candidateNativeReport']==pin(CANDIDATE),'Actual source pair changed')
 return row


def build():
 require(not OUTPUT.exists(),'Purposeful source camera output is immutable')
 view,audit,layout_plan,plan=derive();original=BASE.parent/'Project/BreziTwin/Content/Data/viewpoints.json';candidate=CANDIDATE.parent/'Project/BreziTwin/Content/Data/viewpoints.json'
 require(original.read_bytes()==candidate.read_bytes(),'Native baseline/candidate cameras must remain identical')
 payload=appended_bytes(original.read_bytes(),view);OUTPUT.mkdir();appended=OUTPUT/'viewpoints-original-prefix-plus-yard-close.json';appended.write_bytes(payload)
 snapshot=OUTPUT/'source-exterior-context-yard-camera-r17.py';snapshot.write_bytes((ROOT/OWNER).read_bytes())
 files=[SOURCE,BASE,CANDIDATE,checked(plan['sourceLayout']),checked(plan['geometry']),checked(layout_plan['layout']),checked(layout_plan['inputFiles']['buildings']),original,candidate,ROOT/OWNER,snapshot,ROOT/c.OWNER]
 row={'schema':SCHEMA,'owner':OWNER,'status':'source-only-purposeful-context-yard-camera-native-pending','inputFiles':{str(p):sha(p)for p in files},
  'baselineNativeReport':pin(BASE),'candidateNativeReport':pin(CANDIDATE),'selectedSourcePlan':pin(SOURCE),'originalViewpoints':pin(original),'appendedViewpoints':pin(appended),
  'view':view,'sourceCameraAudit':audit,'originalViewRowsByteExactPrefix':True,'lightingAndOriginalViewsUnchanged':True,
  'plantPlacementChanged':False,'nativeExecuted':False,'nativeCameraVerified':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False}
 write(OUTPUT/'context-yard-camera-supplement.json',row);validated_supplement();print(json.dumps({'supplement':pin(OUTPUT/'context-yard-camera-supplement.json'),'view':view,'audit':audit},indent=2))


if __name__=='__main__':build()
