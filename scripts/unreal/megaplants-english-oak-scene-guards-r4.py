"""Post-import-only scope, byte closure and explicit daylight subset for Oak R4."""
import importlib.util
from pathlib import Path

_p=Path(__file__).with_name('megaplants-english-oak-pilot-guards-r3.py')
_s=importlib.util.spec_from_file_location('oak_frozen_r3_scene_basis',_p)
original=importlib.util.module_from_spec(_s);_s.loader.exec_module(original)
ROOT=original.ROOT
SOURCE=original.SOURCE
OUTPUT=original.OUTPUT
PROJECT=original.PROJECT
BASE=original.BASE
PREFIX=original.PREFIX
MAP=PREFIX+'/Maps/EnglishOakPilotR4'
GROUND_MATERIAL=PREFIX+'/Materials/M_PilotNeutralGroundR4'
PLAN=SOURCE/'oak-usd-scene-plan-r4.json'
SCHEMA='brezi-original-licensed-english-oak-postimport-scene-r4'
AUDIT_SHA='042b53b773e893179ec3c70df7f4ecb6e31f4a2686c1489af4254b209c445990'
ORIGINAL_PLAN_SHA='5428489ce735bba97ef800bba5d632f728c39e24e734827234b92ce1088af772'
require=original.require
read=original.read
write=original.write
pin=original.pin
sha=original.sha
check_pin=original.check_pin
inventory=original.inventory

def scene_camera(plan):
    result=dict(plan['camera']);result['id']='english-oak-original-D-close-r4'
    result['source']='scripts/unreal/megaplants-english-oak-scene-study-r4.py: unchanged original whole-D source bounds and camera'
    return result

def expected_before(plan,base,audit):
    content=read(check_pin(base['afterContentInventory']))
    proof=read(check_pin(base['protectedProjectProof']))
    result={**{'Content/'+k:v for k,v in content.items()},**proof}
    preparation=read(check_pin(plan['projectPreparation']))
    for key,field in [('BreziTwin.uproject','descriptorAfter'),('Config/DefaultEngine.ini','startupConfigAfter')]:
        result[key]={k:preparation[field][k] for k in ('sha256','bytes')}
    require(audit['newContentFileCount']==39 and audit['newContentLogicalBytes']==209572529,
            'Actual complete preserved R3 package inventory required')
    require(all(k.startswith(PREFIX.removeprefix('/Game/')+'/OriginalUSD/') and k.endswith('.uasset')
                for k in audit['newContentFiles']),'Preserved USD package escaped original import namespace')
    result.update({'Content/'+k:v for k,v in audit['newContentFiles'].items()})
    require(len(result)==4257,'Exact4218 original files plus39 saved USD packages required')
    return result

def validate_plan():
    p=read(PLAN)
    require(p['schema']==SCHEMA and p['status']=='source-ready-original-saved-USD-scene-only-native-pending'
            and p['owner']=='scripts/unreal/megaplants-english-oak-scene-study-r4.py'
            and p['project']==str(PROJECT) and p['output']==str(OUTPUT) and p['map']==MAP,
            'Only the isolated R4 scene-only proposal is accepted')
    require(p['assetImportExecuted'] is False and p['nativeExecuted'] is False
            and p['fullLightingPropertyCloneClaimed'] is False,'No reimport or full property-copy claim allowed')
    require(p['originalSourcePlan']==pin(original.PLAN) and p['originalSourcePlan']['sha256']==ORIGINAL_PLAN_SHA,
            'Frozen original whole-D source plan required')
    source,base=original.validate_plan()
    require(p['camera']==scene_camera(source) and p['treePlacement']==source['treePlacement']
            and p['ground']==source['ground'] and p['groundMaterial']==GROUND_MATERIAL,
            'Original whole-D pose, camera or neutral ground changed')
    audit=read(check_pin(p['crashedImportByteAudit']))
    require(p['crashedImportByteAudit']['sha256']==AUDIT_SHA
            and audit['schema']=='brezi-original-oak-r3-scene-create-crash-byte-audit-root-r1'
            and audit['status']=='verified-original-main-assets-camera-unchanged-whole-USD-packages-preserved-after-probe-world-duplicate-crash'
            and audit['all4218OriginalR32SourceFilesExact'] is True
            and audit['all4216OwnNonDescriptorConfigFilesExact'] is True
            and audit['onlyOwnDescriptorAndStartupConfigChangeVerified'] is True
            and audit['mainMapAndOriginalCameraUnchanged'] is True and audit['probeMapCreated'] is False,
            'Actual preserved import/crash byte audit required')
    raw=read(check_pin(audit['process']));terminal=read(check_pin(audit['terminal']))
    require(raw['pid']==22444 and raw['code']==1 and terminal['reportSha256'] is None
            and terminal['sourcePinsUnchangedAfterNative'] is True,'Actual native crash, not invented native success, required')
    require(p['projectPreparation']==audit['preparation'] and p['initialRootClone']==audit['initialClone'],
            'Exact staged own R3 project basis required')
    log=check_pin(audit['nativeLog']).read_text(errors='replace')
    require('UEditorActorSubsystem::DuplicateActors' in log and 'SIGSEGV' in log
            and 'Failed to build Nanite Assembly' not in log,
            'Actual assembly-built/map-duplication crash diagnosis required')
    for row in p['inputFiles']:check_pin(row)
    before=expected_before(p,base,audit)
    require(read(check_pin(p['beforeInventory']))==before,'Selected complete saved source byte scope differs')
    return p,source,base,before

def validate_before(plan,before):
    require(inventory(PROJECT)==before,'Saved39 USD packages or original staged project bytes changed')
    require(inventory(BASE/'Project/BreziTwin')==read(check_pin(plan['originalSavedR32Inventory'])),
            'Original saved R32 source bytes changed')

def validate_delta(before,after):
    changed={k for k,v in before.items() if after.get(k)!=v}
    added=set(after)-set(before)
    expected={'Content/'+MAP.removeprefix('/Game/')+'.umap',
              'Content/'+GROUND_MATERIAL.removeprefix('/Game/')+'.uasset'}
    require(changed=={'Content/Data/viewpoints.json'} and added==expected,
            'Only one new own map/material plus one exact camera append allowed; all39 USD packages protected')
    require(set(before)<=set(after),'An original or saved USD package disappeared')
    return {'changedOriginalFiles':sorted(changed),'newFiles':sorted(added),
            'all39SavedOriginalUsdPackagesByteExact':True,'originalMainMapUnchanged':True}
