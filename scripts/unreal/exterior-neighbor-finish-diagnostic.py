"""One typed R18 close-view supplement; source-only, no Unreal imports.

R1 geometry/recipes and original R16 viewpoints remain frozen. Appending is
allowed only to an independent candidate/baseline clone, never original R16.
"""
import argparse
import copy
from datetime import datetime,timezone
import importlib.util
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-neighbor-finish-diagnostic.py'
OUTPUT=ROOT/'output/unreal/exterior-neighbor-finish-20261001-r2-supplement'
BASE=ROOT/'output/unreal/exterior-20261001-r16a/Project/BreziTwin'
VIEW_ID='neighbor-finish-close-r18'
STATUS='source-only-neighbor-finish-diagnostic-native-pending'
spec=importlib.util.spec_from_file_location('neighbor_diagnostic_guard',ROOT/'scripts/unreal/exterior-neighbor-finish-guards.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
require,sha,read,digest=guard.require,guard.sha,guard.read,guard.digest


def encoded(value):return (json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def pin(path):return {'path':str(path),'sha256':sha(path),'bytes':Path(path).stat().st_size}


def ground_sample(terrain,xy):
    found=[]
    for mesh in terrain['meshes']:
        for ordinal in range(len(mesh['indices'])//3):
            a,b,c=[mesh['verticesCm'][i] for i in mesh['indices'][ordinal*3:ordinal*3+3]]
            if not min(a[0],b[0],c[0])-1e-7<=xy[0]<=max(a[0],b[0],c[0])+1e-7 or not min(a[1],b[1],c[1])-1e-7<=xy[1]<=max(a[1],b[1],c[1])+1e-7:continue
            den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-12:continue
            w1=((b[1]-c[1])*(xy[0]-c[0])+(c[0]-b[0])*(xy[1]-c[1]))/den
            w2=((c[1]-a[1])*(xy[0]-c[0])+(a[0]-c[0])*(xy[1]-c[1]))/den;w3=1-w1-w2
            if min(w1,w2,w3)>=-1e-8:found.append({'meshId':mesh['id'],'triangleOrdinal':ordinal,'barycentric':[w1,w2,w3],'zCm':sum(w*p[2] for w,p in zip((w1,w2,w3),(a,b,c)))})
    require(found,'Diagnostic eye has no actual source terrain triangle');return max(found,key=lambda r:r['zCm'])


def derive_camera(village,context,terrain):
    building=next(b for b in village['buildings'] if b['id']=='BU.3800911')
    ring=guard.canonical(building['polygonsCm'][0][0]);a,b=max(zip(ring,ring[1:]+ring[:1]),key=lambda e:math.dist(*e))
    length=math.dist(a,b);t=[(b[k]-a[k])/length for k in (0,1)];out=[t[1],-t[0]];center=[(a[k]+b[k])/2 for k in (0,1)]
    eye_xy=[center[k]+out[k]*1300-t[k]*400 for k in (0,1)]
    sample=ground_sample(terrain,eye_xy);eye=[*eye_xy,sample['zCm']+170]
    floor=building['eaveElevationCm']-building['estimatedWallHeightCm'];target=[*center,floor+180]
    distances={b['id']:guard.footprint_distance(eye_xy,b['polygonsCm']) for b in village['buildings']}
    require(min(distances.values())>150,'Diagnostic eye intrudes original building envelope')
    protected=min((0. if guard.ring_inside(eye_xy,p) else min(guard.distance_segment(eye_xy,a,b) for a,b in zip(p,p[1:]+p[:1]))) for p in context['protectedTrianglesCm'])
    require(protected>150,'Diagnostic eye intrudes C/B/B/private exclusion')
    road_distance=min(0. if guard.ring_inside(eye_xy,[p[:2] for p in tri]) else min(guard.distance_segment(eye_xy,a[:2],b[:2]) for a,b in zip(tri,tri[1:]+tri[:1]))
                      for mesh in context['meshes'] if mesh['material']=='context_track' for tri in guard.triangles(mesh))
    rotation={'pitch':math.degrees(math.atan2(target[2]-eye[2],math.dist(target[:2],eye[:2]))),
              'yaw':math.degrees(math.atan2(target[1]-eye[1],target[0]-eye[0])),'roll':0.}
    view={'id':VIEW_ID,'label':'Susedné domy · detail R18','eyeCm':eye,'targetCm':target,'horizontalFovDegrees':68.,
          'source':OWNER+': exact original BU.3800911 longest facade + pinned source terrain',
          'presentation':{'intent':'Close diagnostic material and cut-window comparison; original R16 versus isolated R18 overlay',
          'sourceEvidence':'SOURCE_DERIVED_DIAGNOSTIC_OFF_FOOTPRINT_NOT_OBSERVED_STREET_OR_SURVEY_CAMERA',
          'eyeHeightAboveSourceTerrainCm':170,'selectedBuildingId':building['id'],'activeDesign':guard.DESIGN}}
    return view,{'selectedBuildingId':building['id'],'sourceFacadeEndpointsCm':[a,b],'facadeLengthCm':length,'outward':out,
                 'eyeOutwardOffsetCm':1300,'eyeAlongEdgeOffsetCm':-400,'sourceTerrainReadback':sample,
                 'sourceBuildingsChecked':len(distances),'minimumSourceBuildingDistanceCm':min(distances.values()),
                 'protectedPrivateDistanceCm':protected,'nearestAuthoredSourceRoadDistanceCm':road_distance,
                 'nativeTransformProposal':{'locationCm':eye,'rotationDegrees':rotation},
                 'selectedEyeDistancesCm':{k:distances[k] for k in guard.TARGETS},
                 'actualCameraNativeReadback':False,'observedStreetAccessClaimed':False,'surveyAccuracyClaimed':False}


def append_payload(original,view):
    require(original['coordinateSystem']=='unreal-centimeters' and isinstance(original['views'],list),'Original viewpoint schema differs')
    require(not any(v['id']==VIEW_ID for v in original['views']),'Diagnostic view already exists')
    result=copy.deepcopy(original);result['views'].append(copy.deepcopy(view));return result


def validated_supplement(path=None):
    path=Path(path or OUTPUT/'neighbor-finish-diagnostic-supplement.json');supplement=read(path)
    require(supplement['owner']==OWNER and supplement['schemaVersion']==1 and type(supplement['schemaVersion']) is int and supplement['status']==STATUS,'Unregistered diagnostic supplement')
    require(supplement['generatorSha256']==sha(ROOT/OWNER) and supplement['sourceStudy']['sha256']==guard.PLAN_SHA,'Diagnostic producer/study drift')
    require(supplement['activeDesign']==guard.DESIGN and supplement['setbacksMm']=={'street':3000,'east':3000},'Diagnostic C/B/B placement differs')
    for name,h in supplement['inputFiles'].items():require(sha(name)==h,'Diagnostic pinned source drift: '+name)
    for flag in ['nativeApplied','nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted']:require(supplement[flag] is False,'Diagnostic falsely claims acceptance')
    original=read(supplement['originalViewpoints']['path']);view,audit=derive_camera(read(supplement['villagePath']),read(supplement['contextPath']),read(supplement['terrainPath']))
    require(supplement['view']==view and supplement['sourceCameraAudit']==audit,'Diagnostic camera was not source-derived')
    payload=append_payload(original,view);expected=encoded(payload);payload_path=Path(supplement['appendedViewpoints']['path'])
    require(payload_path.read_bytes()==expected and supplement['appendedViewpoints']==pin(payload_path),'Diagnostic exact original-prefix/+1 payload differs')
    require(supplement['originalViewpoints']==pin(supplement['originalViewpoints']['path']),'Original viewpoint byte pin differs')
    return supplement


def append_to_clone(project,supplement=None):
    supplement=supplement or validated_supplement();project=Path(project).resolve()
    require(project.is_relative_to(ROOT/'output/unreal') and project!=BASE and not project.is_relative_to(BASE) and not BASE.is_relative_to(project),'Diagnostic append requires own independent R16 clone')
    destination=project/'Content/Data/viewpoints.json';original=Path(supplement['originalViewpoints']['path']);candidate=Path(supplement['appendedViewpoints']['path'])
    require(destination.is_file() and destination.stat().st_ino!=original.stat().st_ino,'Independent viewpoint inode required')
    require(destination.read_bytes() in [original.read_bytes(),candidate.read_bytes()],'Unreviewed clone viewpoint bytes')
    if destination.read_bytes()!=candidate.read_bytes():destination.write_bytes(candidate.read_bytes())
    return {'supplement':pin(OUTPUT/'neighbor-finish-diagnostic-supplement.json'),'viewpointFile':pin(destination),
            'viewId':VIEW_ID,'originalViewsPrefixPreserved':True,'appendedViews':1,'sourceCameraAudit':supplement['sourceCameraAudit']}


def build():
    require(not OUTPUT.exists(),'Fresh R2 supplement output required');bundle=guard.validated_candidate()
    village_path=ROOT/'output/unreal/exterior-buildings-20260926-r2/building-plan.json';context_path=ROOT/'output/unreal/exterior-context-20260927-r8/context-plan.json'
    village=read(village_path);terrain_path=Path(village['terrainPlan']['path']);require(sha(terrain_path)==village['terrainPlan']['sha256'],'Original source terrain drift')
    original=BASE/'Content/Data/viewpoints.json';view,audit=derive_camera(village,read(context_path),read(terrain_path))
    OUTPUT.mkdir();appended=OUTPUT/'viewpoints-r16-prefix-plus-close.json';appended.write_bytes(encoded(append_payload(read(original),view)))
    inputs={**bundle['inputPins'],str(original):sha(original),str(terrain_path):sha(terrain_path),str(ROOT/'scripts/unreal/exterior-neighbor-finish-guards.py'):sha(ROOT/'scripts/unreal/exterior-neighbor-finish-guards.py')}
    result={'schemaVersion':1,'owner':OWNER,'status':STATUS,'generatedAt':datetime.now(timezone.utc).isoformat(),'generatorSha256':sha(ROOT/OWNER),
            'sourceStudy':pin(guard.STUDY/'neighbor-finish-plan.json'),'activeDesign':guard.DESIGN,'setbacksMm':{'street':3000,'east':3000},
            'inputFiles':inputs,'villagePath':str(village_path),'contextPath':str(context_path),'terrainPath':str(terrain_path),
            'originalViewpoints':pin(original),'appendedViewpoints':pin(appended),'view':view,'sourceCameraAudit':audit,
            'changedCloneContentFiles':['Data/viewpoints.json'],'nativeApplied':False,'nativeAppearanceAccepted':False,'performanceAccepted':False,'fullPhotorealismAccepted':False,
            'limits':['Original footprints/volumes/heights are approximate source data, not surveyed building heights.','The eye is clear of all source buildings/private triangles; physical walking access and occluders are not certified.','Closest authored context road is explicitly measured; no new street or access route is invented.','Native baseline/candidate camera equality and visual acceptance remain pending.']}
    (OUTPUT/'neighbor-finish-diagnostic-supplement.json').write_bytes(encoded(result));validated_supplement();print(json.dumps({'supplement':str(OUTPUT),'view':view,'sourceCameraAudit':audit}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--append-to-clone');args=parser.parse_args()
    if args.append_to_clone:print(json.dumps(append_to_clone(args.append_to_clone)))
    else:build()
