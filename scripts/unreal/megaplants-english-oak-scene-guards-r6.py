"""Accept only the actual measured directional-light setter result, without epsilon."""
import copy
import importlib.util
from pathlib import Path
import struct

_p=Path(__file__).with_name('megaplants-english-oak-scene-guards-r5.py')
_s=importlib.util.spec_from_file_location('oak_frozen_scene_r5_basis',_p)
old=importlib.util.module_from_spec(_s);_s.loader.exec_module(old)
original=old.original
ROOT=old.ROOT;SOURCE=old.SOURCE;OUTPUT=old.OUTPUT;PROJECT=old.PROJECT;BASE=old.BASE;PREFIX=old.PREFIX
MAP=PREFIX+'/Maps/EnglishOakPilotR6';GROUND_MATERIAL=PREFIX+'/Materials/M_PilotNeutralGroundR6'
PLAN=SOURCE/'oak-usd-scene-plan-r6.json'
SCHEMA='brezi-original-licensed-english-oak-postimport-scene-r6'
AUDIT_SHA='c302131d550336876f304ba9049d9874173eb85ecfab1f76da2d5258832b5545'
DIFFERENCE_SHA='ed61e494685ece4e1beff6ad86bf5faf0f9557c1fc285bb88f3e9889f04d0b9b'
require=old.require;read=old.read;write=old.write;pin=old.pin;sha=old.sha;check_pin=old.check_pin;inventory=old.inventory

def binary64_equal(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,float):return struct.pack('>d',a)==struct.pack('>d',b)
    if isinstance(a,dict):return set(a)==set(b) and all(binary64_equal(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(binary64_equal(v,w) for v,w in zip(a,b))
    return a==b

def measured_lighting(reference):
    require(DIFFERENCE_SHA is not None and reference['sha256']==DIFFERENCE_SHA,'Actual R5 lighting difference binding pending')
    d=read(check_pin(reference));source=read(check_pin(d['source']));copied=read(check_pin(d['copied']))
    require(d['schema']==old.SCHEMA and d['owner']=='scripts/unreal/megaplants-english-oak-scene-native-r5.py'
            and d['nativeProcessId']==29290 and d['differenceCount']==4 and d['float64DifferenceCount']==4
            and d['nonFloat64DifferenceCount']==0 and d['numericalToleranceApplied'] is False
            and d['allDifferencesSameFloat32'] is True,'Only actual four-component native quaternion measurement is allowed')
    require([v['path'] for v in d['differences']]==['$[0].transform[1]['+str(i)+']' for i in range(4)]
            and source[0]['class']==copied[0]['class']=='/Script/Engine.DirectionalLight'
            and source[0]['transform'][0]==copied[0]['transform'][0]==[0.,0.,0.]
            and source[0]['transform'][2]==copied[0]['transform'][2]==[2.5,2.5,2.5],
            'Measurement escaped the fixed original directional-light quaternion')
    source_q=[-.10825402007862642,.39206601984475165,.24314251005520598,.880594698498671]
    copied_q=[-.10825402005063521,.3920660198008537,.24314251002798237,.8805946985291734]
    require(binary64_equal(source[0]['transform'][1],source_q)
            and binary64_equal(copied[0]['transform'][1],copied_q),'Actual measured binary64 pair differs')
    expected=copy.deepcopy(source);expected[0]['transform'][1]=copied_q
    require(binary64_equal(expected,copied),'Any unmeasured field changed in the actual copied subset')
    return source,copied,d

def scene_camera(source):
    result=dict(source['camera']);result['id']='english-oak-original-D-close-r6'
    result['source']='scripts/unreal/megaplants-english-oak-scene-study-r6.py: unchanged original whole-D camera'
    return result

def expected_before(audit,old_before):
    require(audit['all4258OriginalOwnFilesExact'] is True and audit['all4218OriginalR32SourceFilesExact'] is True
            and audit['all39SavedOriginalUsdPackagesExact'] is True and audit['changedOriginalFiles']==[]
            and audit['newFileCount']==1,'Actual strict R5 failure byte closure required')
    key='Content/'+old.MAP.removeprefix('/Game/')+'.umap'
    require(set(audit['newContentFiles'])=={key},'Only the actual preserved R5 map may join the old basis')
    result={**old_before,**audit['newContentFiles']}
    require(len(result)==4259 and read(check_pin(audit['currentAfterInventory']))==result,
            'Complete current original-and-failed-maps byte basis differs')
    return result

def validate_plan():
    require(AUDIT_SHA is not None,'Actual R5 failure byte audit binding pending')
    p=read(PLAN)
    require(p['schema']==SCHEMA and p['owner']=='scripts/unreal/megaplants-english-oak-scene-study-r6.py'
            and p['status']=='source-ready-scene-only-exact-measured-directional-setter-native-pending'
            and p['project']==str(PROJECT) and p['output']==str(OUTPUT) and p['map']==MAP,
            'Only own measured R6 scene attempt is accepted')
    previous,source,base,old_before=old.validate_plan()
    require(p['previousScenePlan']==pin(old.PLAN) and p['camera']==scene_camera(source)
            and p['treePlacement']==source['treePlacement'] and p['ground']==source['ground']
            and p['groundMaterial']==GROUND_MATERIAL,'Original whole-D pose/camera or previous proposal differs')
    require(p['assetImportExecuted'] is False and p['nativeExecuted'] is False
            and p['numericalToleranceApplied'] is False and p['fullLightingPropertyCloneClaimed'] is False,
            'No reimport, general numerical tolerance or full-light-copy claim allowed')
    audit=read(check_pin(p['failedSceneByteAudit']))
    require(p['failedSceneByteAudit']['sha256']==AUDIT_SHA and audit['selectedPlan']==pin(old.PLAN)
            and audit['schema']=='brezi-original-oak-r5-measured-quaternion-transfer-failure-byte-audit-root-r1'
            and audit['status']=='verified-original-usd-main-camera-unchanged-only-empty-new-R5-map-after-measured-four-quaternion-only-differences',
            'Actual measured strict-lighting-failure audit required')
    raw=read(check_pin(audit['process']));terminal=read(check_pin(audit['terminal']));failed=read(check_pin(audit['report']))
    require(raw['pid']==29290 and raw['code']==255 and terminal['reportSha256']==audit['report']['sha256']
            and terminal['sourcePinsUnchangedAfterNative'] is True and failed['owner']=='scripts/unreal/megaplants-english-oak-scene-native-r5.py'
            and failed['nativeProcessId']==29290 and failed['status']=='failed-scene-only-attempt-preserved'
            and 'actual complete difference receipt preserved' in failed['error'] and failed['nativeApplied'] is False,
            'Actual R5 failure must remain explicit')
    require(p['beforeInventory']==audit['currentAfterInventory'],'Current exact R5 failure inventory required')
    measured_lighting(p['measuredLightingReference'])
    for row in p['inputFiles']:check_pin(row)
    return p,source,base,expected_before(audit,old_before)

def validate_before(plan,before):
    require(inventory(PROJECT)==before,'Original own source/USD assets or failed R4/R5 maps changed')
    require(inventory(BASE/'Project/BreziTwin')==read(check_pin(plan['originalSavedR32Inventory'])),
            'Original saved R32 source bytes changed')

def validate_delta(before,after):
    changed={k for k,v in before.items() if after.get(k)!=v};added=set(after)-set(before)
    require(changed=={'Content/Data/viewpoints.json'} and added=={
        'Content/'+MAP.removeprefix('/Game/')+'.umap','Content/'+GROUND_MATERIAL.removeprefix('/Game/')+'.uasset'}
        and set(before)<=set(after),'Only own R6 map/material/camera may change; failed maps and39 USD stay exact')
    return {'changedOriginalFiles':sorted(changed),'newFiles':sorted(added),
        'all39SavedOriginalUsdPackagesByteExact':True,'failedR4R5MapsByteExact':True,'originalMainMapUnchanged':True}
