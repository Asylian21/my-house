"""Source-only near-grass camera; root explicitly stages independent QA clones."""
import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-curved-grass-camera-r1.py'
OUTPUT=ROOT/'output/unreal/exterior-curved-grass-20261002-camera-r1-supplement'
VIEW_ID='exterior-curved-grass-close'
PLAN=ROOT/'output/unreal/exterior-curved-grass-20261002-r1-study/curved-grass-plan.json'
PLAN_SHA='f43f3d224c9d43d70091a910e5618052fa942bb593ac55d3cc900eace8a8aa68'
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('grass_camera_frozen_guard',ROOT/'scripts/unreal/exterior-curved-grass-guards.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
require,sha,read,write,pin=g.require,g.sha,g.read,g.write,g.pin


def derive(plan):
    rows=read(g.check_pin(plan['rootSelection']));require(len(rows)==64,'Exact frozen 64 roots required')
    positions=[r['originalSourceRow']['positionCm'] for r in rows]
    centroid=[sum(p[i] for p in positions)/len(positions) for i in range(3)]
    forward=[plan['camera']['targetCm'][i]-plan['camera']['eyeCm'][i] for i in range(2)]
    length=math.sqrt(sum(v*v for v in forward));forward=[v/length for v in forward]
    # These are explicitly authored camera coordinates rounded to 1e-6 cm;
    # no scene geometry or selected root coordinate is rounded or changed.
    eye=[round(centroid[i]-175*forward[i],6) for i in range(2)]+[round(centroid[2]+75,6)]
    target=[round(v,6) for v in centroid[:2]]+[round(centroid[2]+15,6)]
    view={'id':VIEW_ID,'label':'Detail pôvodnej zakrivenej trávy','eyeCm':eye,'targetCm':target,
        'horizontalFovDegrees':65,'source':OWNER+': frozen selected-root centroid, 175 cm behind, 75/15 cm height.'}
    delta=[target[i]-eye[i] for i in range(3)];depth_length=math.sqrt(sum(v*v for v in delta))
    f=[v/depth_length for v in delta];right=[f[1],-f[0],0.]
    right_length=math.sqrt(sum(v*v for v in right));right=[v/right_length for v in right]
    up=g.cross(right,f);tan=math.tan(math.radians(65/2))
    visible=[]
    for row,p in zip(rows,positions):
        v=[p[i]-eye[i] for i in range(3)];d=g.dot(v,f)
        if d>0 and abs(g.dot(v,right))<d*tan and abs(g.dot(v,up))<d*tan*9/16:
            visible.append({'groupId':row['groupId'],'originalIndex':row['instanceIndex'],'kind':row['kind'],
                            'eyeDistanceCm':math.sqrt(sum(a*a for a in v))})
    require(len(visible)>=24 and {r['kind'] for r in visible}==set(g.MASTERS),'Close source frustum misses the pilot mix')
    audit={'selectedRootCount':64,'sourceRootCentroidCm':centroid,
        'sourceRootBoundsCm':[[min(p[i] for p in positions) for i in range(3)],[max(p[i] for p in positions) for i in range(3)]],
        'horizontalBehindCentroidCm':175,'eyeAboveMeanAuthoredGroundCm':75,'aimAboveMeanAuthoredGroundCm':15,
        'cameraCoordinateRoundingCm':1e-6,'rootCentersIn16by9Frustum':len(visible),
        'rootCenterEyeDistanceRangeCm':[min(r['eyeDistanceCm'] for r in visible),max(r['eyeDistanceCm'] for r in visible)],
        'sourceFrustumKinds':{k:sum(r['kind']==k for r in visible) for k in g.MASTERS},
        'visibleSelectedRootIdentities':[{k:v for k,v in r.items() if k!='eyeDistanceCm'} for r in visible],
        'rootCentersOnlyNotOcclusionOrNativeVisibility':True,'nativeCameraVerified':False}
    return view,audit


def appended_bytes(original,view):
    document=json.loads(original);require(not any(v['id']==VIEW_ID for v in document['views']),'Close view already present')
    # Original file uses this exact encoding; retaining its views prefix keeps
    # every pre-existing row byte-exact, with just a new comma and appended row.
    encoded=(json.dumps(document,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    require(encoded==original,'Original camera encoding changed; do not rewrite it')
    result=copy.deepcopy(document);result['views'].append(view)
    payload=(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    before=(json.dumps(document['views'],indent=2,ensure_ascii=False,allow_nan=False)).encode().rsplit(b'\n]',1)[0]
    after=(json.dumps(result['views'],indent=2,ensure_ascii=False,allow_nan=False)).encode()
    require(after.startswith(before+b','),'Existing camera rows lost byte-exact prefix')
    require({k:v for k,v in result.items() if k!='views'}=={k:v for k,v in document.items() if k!='views'}
            and result['views'][:-1]==document['views'],'Camera supplement changed existing data')
    return payload


def validated_supplement():
    require(sha(PLAN)==PLAN_SHA,'Frozen selected roots/plan changed');s=read(OUTPUT/'curved-grass-camera-supplement.json')
    require(s['owner']==OWNER and s['schema']=='brezi-original-curved-grass-close-camera-r1'
            and s['status']=='source-only-close-camera-native-pending','Unapproved grass camera supplement')
    for path,h in s['inputFiles'].items():require(sha(path)==h,'Grass camera source pin changed')
    plan=read(PLAN);view,audit=derive(plan)
    require(s['view']==view and s['sourceCameraAudit']==audit,'Close camera derivation changed')
    original=Path(g.check_pin(s['originalViewpoints']));payload=Path(g.check_pin(s['appendedViewpoints']))
    require(payload.read_bytes()==appended_bytes(original.read_bytes(),view),'Close camera payload/prefix changed')
    return s


def build():
    require(not OUTPUT.exists(),'Close camera supplements are immutable');require(sha(PLAN)==PLAN_SHA,'Frozen original grass plan changed')
    plan=read(PLAN);view,audit=derive(plan);original=g.check_pin(plan['sourceInputs']['camera'])
    payload=appended_bytes(original.read_bytes(),view);OUTPUT.mkdir(parents=True)
    file=OUTPUT/'viewpoints-r16-prefix-plus-grass-close.json';file.write_bytes(payload)
    snapshot=OUTPUT/'source-exterior-curved-grass-camera-r1.py';shutil.copyfile(ROOT/OWNER,snapshot)
    inputs={str(PLAN):PLAN_SHA,str(ROOT/OWNER):sha(ROOT/OWNER),str(snapshot):sha(snapshot),
            plan['rootSelection']['path']:plan['rootSelection']['sha256'],str(original):sha(original),
            str(ROOT/g.OWNER):sha(ROOT/g.OWNER)}
    write(OUTPUT/'curved-grass-camera-supplement.json',{'schema':'brezi-original-curved-grass-close-camera-r1',
        'owner':OWNER,'status':'source-only-close-camera-native-pending','generatedAt':g.now(),'inputFiles':inputs,
        'selectedGrassPlan':pin(PLAN),'originalViewpoints':pin(original),'appendedViewpoints':pin(file),
        'view':view,'sourceCameraAudit':audit,'originalViewRowsByteExactPrefix':True,
        'lightingAndOriginalViewsUnchanged':True,'vegetationPlacementChanged':False,'nativeExecuted':False,
        'nativeAppearanceAccepted':False,'performanceAccepted':False,'fullPhotorealismAccepted':False})
    validated_supplement();print(json.dumps({'supplement':pin(OUTPUT/'curved-grass-camera-supplement.json'),'view':view,'audit':audit}))


if __name__=='__main__':build()
