"""New measured-difference trial, preserving the failed R4 scene attempt."""
import importlib.util
from pathlib import Path

_p=Path(__file__).with_name('megaplants-english-oak-scene-guards-r4.py')
_s=importlib.util.spec_from_file_location('oak_frozen_scene_r4_basis',_p)
old=importlib.util.module_from_spec(_s);_s.loader.exec_module(old)
original=old.original
ROOT=old.ROOT;SOURCE=old.SOURCE;OUTPUT=old.OUTPUT;PROJECT=old.PROJECT;BASE=old.BASE;PREFIX=old.PREFIX
MAP=PREFIX+'/Maps/EnglishOakPilotR5'
GROUND_MATERIAL=PREFIX+'/Materials/M_PilotNeutralGroundR5'
PLAN=SOURCE/'oak-usd-scene-plan-r5.json'
SCHEMA='brezi-original-licensed-english-oak-postimport-scene-r5'
AUDIT_SHA='6d39a6c606dcec5f62d45654ff1a4ea92001cb3013a8b7ab3b97e7a7a6ec5703'
require=old.require;read=old.read;write=old.write;pin=old.pin;sha=old.sha;check_pin=old.check_pin;inventory=old.inventory

def scene_camera(source):
    result=dict(source['camera']);result['id']='english-oak-original-D-close-r5'
    result['source']='scripts/unreal/megaplants-english-oak-scene-study-r5.py: unchanged original whole-D camera'
    return result

def expected_before(audit,old_before):
    require(audit['all4257OriginalOwnFilesExact'] is True
            and audit['all4218OriginalR32SourceFilesExact'] is True
            and audit['all39SavedOriginalUsdPackagesExact'] is True
            and audit['changedOriginalFiles']==[] and audit['newFileCount']==1
            and audit['newContentLogicalBytes']==6493,'Actual failed R4 original byte closure required')
    expected_key='Content/'+old.MAP.removeprefix('/Game/')+'.umap'
    require(set(audit['newContentFiles'])=={expected_key}
            and audit['newContentFiles'][expected_key]=={
                'sha256':'3b1fda27322c65d18c823753d913738eaf7ee3e3f7702a5621ce35ff918dc59b','bytes':6493},
            'Only the actual preserved R4 map is added to the old basis')
    result={**old_before,**audit['newContentFiles']}
    require(len(result)==4258 and read(check_pin(audit['currentAfterInventory']))==result,
            'Complete original-and-failed-map byte basis differs')
    return result

def validate_plan():
    p=read(PLAN)
    require(p['schema']==SCHEMA and p['owner']=='scripts/unreal/megaplants-english-oak-scene-study-r5.py'
            and p['status']=='source-ready-scene-only-lighting-difference-measurement-native-pending'
            and p['project']==str(PROJECT) and p['output']==str(OUTPUT) and p['map']==MAP,
            'Only own R5 scene measurement is accepted')
    _,source,base,old_before=old.validate_plan()
    require(p['previousScenePlan']==pin(old.PLAN) and p['camera']==scene_camera(source)
            and p['treePlacement']==source['treePlacement'] and p['ground']==source['ground']
            and p['groundMaterial']==GROUND_MATERIAL,'Original whole-D camera/pose or preserved R4 source differs')
    require(p['assetImportExecuted'] is False and p['nativeExecuted'] is False
            and p['numericalToleranceApplied'] is False and p['fullLightingPropertyCloneClaimed'] is False,
            'No reimport, inferred numerical fix, native success or full-light-copy claim allowed')
    audit=read(check_pin(p['failedSceneByteAudit']))
    require(p['failedSceneByteAudit']['sha256']==AUDIT_SHA
            and audit['schema']=='brezi-original-oak-r4-explicit-daylight-transfer-failure-byte-audit-root-r1'
            and audit['status']=='verified-original-usd-main-camera-unchanged-only-empty-new-R4-map-after-lighting-subset-mismatch'
            and audit['selectedPlan']==pin(old.PLAN),'Actual strict lighting mismatch audit required')
    raw=read(check_pin(audit['process']));terminal=read(check_pin(audit['terminal']));failed=read(check_pin(audit['report']))
    require(raw['pid']==27480 and raw['code']==255 and terminal['reportSha256']==audit['report']['sha256']
            and terminal['sourcePinsUnchangedAfterNative'] is True
            and failed['owner']=='scripts/unreal/megaplants-english-oak-scene-native-r4.py'
            and failed['nativeProcessId']==27480 and failed['status']=='failed-scene-only-attempt-preserved'
            and 'Explicit observed daylight/PP subset differs' in failed['error']
            and failed['assetImportExecuted'] is False and failed['nativeApplied'] is False,
            'Actual R4 failure must remain explicit')
    for row in p['inputFiles']:check_pin(row)
    before=expected_before(audit,old_before)
    require(p['beforeInventory']==audit['currentAfterInventory'],'Current exact R4 failure inventory required')
    return p,source,base,before

def validate_before(plan,before):
    require(inventory(PROJECT)==before,'Preserved R4 map/USD packages or original own project changed')
    require(inventory(BASE/'Project/BreziTwin')==read(check_pin(plan['originalSavedR32Inventory'])),
            'Original saved R32 source bytes changed')

def validate_delta(before,after):
    changed={k for k,v in before.items() if after.get(k)!=v};added=set(after)-set(before)
    require(changed=={'Content/Data/viewpoints.json'} and added=={
        'Content/'+MAP.removeprefix('/Game/')+'.umap','Content/'+GROUND_MATERIAL.removeprefix('/Game/')+'.uasset'}
        and set(before)<=set(after),'Only own R5 map/material/camera may change; failed R4 map and39 USD stay exact')
    return {'changedOriginalFiles':sorted(changed),'newFiles':sorted(added),
            'all39SavedOriginalUsdPackagesByteExact':True,'failedR4MapByteExact':True,'originalMainMapUnchanged':True}
