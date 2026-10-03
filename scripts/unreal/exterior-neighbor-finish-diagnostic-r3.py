"""R3 diagnostic numerical guard: unchanged camera, three measured 1ULP audits.

The original R2 helper/supplement/payload remain immutable. UE Python3.11
differs from host Python only in three math distance audit scalars, measured by
the native numeric-only probe. Every camera coordinate and other field is exact.
"""
import argparse
import copy
from datetime import datetime,timezone
import importlib.util
import json
import math
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-neighbor-finish-diagnostic-r3.py'
OUTPUT=ROOT/'output/unreal/exterior-neighbor-finish-20261001-r3-supplement'
ORIGINAL=ROOT/'scripts/unreal/exterior-neighbor-finish-diagnostic.py'
ORIGINAL_SHA='52bc4aea5b0bd994a74692a6c956176995d044ad84300ef373afb3f3b98a1d08'
R2=ROOT/'output/unreal/exterior-neighbor-finish-20261001-r2-supplement/neighbor-finish-diagnostic-supplement.json'
R2_SHA='f1692dd83cd5caa15800845b5e31a18eeecbf22cc8587f4fc55bcf8a66293b18'
PROBE=ROOT/'output/unreal/exterior-20261001-r18a/neighbor-finish-diagnostic-runtime-probe.json'
PROBE_SHA='aee18304fff16169612160f5e4f5d19937be75c75c8737ed9e0a3310d023d109'
PROBE_PRODUCER=ROOT/'scripts/unreal/exterior-neighbor-finish-diagnostic-runtime-probe.py'
PROBE_PRODUCER_SHA='ea2d9355a0f5cb2b40fb5f8508d87c445a2a673e404076344fb84541e2c357bc'
ALLOWED_PATHS=frozenset({'$.audit.protectedPrivateDistanceCm','$.audit.nearestAuthoredSourceRoadDistanceCm',
                         '$.audit.selectedEyeDistancesCm.BU.3800911'})
ABSOLUTE_CAP_CM=4e-12
spec=importlib.util.spec_from_file_location('neighbor_original_diagnostic_r2',ORIGINAL)
original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
require,sha,read,pin=original.require,original.sha,original.read,original.pin
VIEW_ID=original.VIEW_ID;BASE=original.BASE;STATUS=original.STATUS


def compare_camera(expected,actual,path='$'):
    """Exact typed recursive equality except the3 observed float distance audits."""
    if type(expected) is not type(actual):return False
    if isinstance(expected,dict):return set(expected)==set(actual) and all(compare_camera(v,actual[k],path+'.'+k) for k,v in expected.items())
    if isinstance(expected,list):return len(expected)==len(actual) and all(compare_camera(a,b,path+'['+str(i)+']') for i,(a,b) in enumerate(zip(expected,actual)))
    if type(expected) is float:
        if not math.isfinite(expected) or not math.isfinite(actual):return False
        if expected==actual:return True
        return path in ALLOWED_PATHS and abs(expected-actual)<=ABSOLUTE_CAP_CM and abs(expected-actual)<=max(math.ulp(expected),math.ulp(actual))
    return expected==actual


def policy():return {'floatAuditPaths':sorted(ALLOWED_PATHS),'maximumLargerUlpDelta':1,'maximumAbsoluteDeltaCm':ABSOLUTE_CAP_CM,
                     'cameraAndAllOtherFieldsExact':True,'integerBooleanStringTypesExact':True}


def measured_probe():
    require(sha(ORIGINAL)==ORIGINAL_SHA and sha(R2)==R2_SHA and sha(PROBE)==PROBE_SHA and sha(PROBE_PRODUCER)==PROBE_PRODUCER_SHA,'Immutable measured diagnostic lineage changed')
    p=read(PROBE);require(p['status']=='native-embedded-python-diagnostic-comparison-only' and p['sourceHelperSha256']==ORIGINAL_SHA and p['sourceSupplementSha256']==R2_SHA,'Unregistered native numerical probe')
    require(p['nonNumericMismatchCount']==0 and p['sceneLoadedOrChanged'] is False and p['assetCallsExecuted'] is False and p['nativeApplied'] is False,'Probe exceeds numerical-only scope')
    require(len(p['differences'])==3 and {r['path'] for r in p['differences']}==ALLOWED_PATHS and all(r['finite'] is True and r['deltaInLargerUlps']==1 and r['absoluteDelta']<=ABSOLUTE_CAP_CM for r in p['differences']),'Observed numerical differences escape3 exact1ULP audit paths')
    require(p['expectedView']==p['actualView'] and compare_camera({'view':p['expectedView'],'audit':p['expectedAudit']},{'view':p['actualView'],'audit':p['actualAudit']}),'Measured camera/other fields changed')
    return p


def validated_supplement(path=None):
    measured_probe();path=Path(path or OUTPUT/'neighbor-finish-diagnostic-supplement.json');s=read(path);r2=read(R2)
    require(s['owner']==OWNER and type(s['schemaVersion']) is int and s['schemaVersion']==3 and s['status']==STATUS,'Unregistered R3 diagnostic supplement')
    require(s['generatorSha256']==sha(ROOT/OWNER) and s['numericalComparisonPolicy']==policy() and s['originalR2Supplement']==pin(R2) and s['nativeRuntimeProbe']==pin(PROBE) and s['nativeRuntimeProbeProducer']==pin(PROBE_PRODUCER),'R3 producer/numerical policy/lineage changed')
    for name,h in s['inputFiles'].items():require(sha(name)==h,'R3 pinned source changed: '+name)
    for key in ['sourceStudy','activeDesign','setbacksMm','villagePath','contextPath','terrainPath','originalViewpoints','view','sourceCameraAudit','changedCloneContentFiles','nativeApplied','nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted','limits']:
        require(compare_camera(s[key],r2[key],'$.reference.'+key),'R3 changes original diagnostic source/camera semantics/types: '+key)
    view,audit=original.derive_camera(read(s['villagePath']),read(s['contextPath']),read(s['terrainPath']))
    require(compare_camera({'view':s['view'],'audit':s['sourceCameraAudit']},{'view':view,'audit':audit}),'R3 derived camera differs beyond measured3 audit1ULP boundary')
    require(s['originalViewpoints']==pin(s['originalViewpoints']['path']),'Original viewpoint bytes drift')
    payload=Path(s['appendedViewpoints']['path']);require(s['appendedViewpoints']==pin(payload) and payload.read_bytes()==Path(r2['appendedViewpoints']['path']).read_bytes(),'R3 camera payload must remain byte-exact R2 prefix+one original row')
    return s


def append_to_clone(project,supplement=None):
    s=supplement or validated_supplement();project=Path(project).resolve()
    require(project.is_relative_to(ROOT/'output/unreal') and project!=BASE and not project.is_relative_to(BASE) and not BASE.is_relative_to(project),'R3 append requires independent candidate/baseline clone')
    destination=project/'Content/Data/viewpoints.json';source=Path(s['originalViewpoints']['path']);candidate=Path(s['appendedViewpoints']['path'])
    require(destination.is_file() and destination.stat().st_ino!=source.stat().st_ino,'Independent viewpoint inode required')
    require(destination.read_bytes() in [source.read_bytes(),candidate.read_bytes()],'Unreviewed clone viewpoint data')
    if destination.read_bytes()!=candidate.read_bytes():destination.write_bytes(candidate.read_bytes())
    return {'supplement':pin(OUTPUT/'neighbor-finish-diagnostic-supplement.json'),'viewpointFile':pin(destination),'viewId':VIEW_ID,
            'originalViewsPrefixPreserved':True,'appendedViews':1,'sourceCameraAudit':s['sourceCameraAudit']}


def build():
    require(not OUTPUT.exists(),'Fresh R3 source supplement required');measured_probe();r2=read(R2);s=copy.deepcopy(r2)
    OUTPUT.mkdir();payload=OUTPUT/'viewpoints-r16-prefix-plus-close.json';shutil.copy2(r2['appendedViewpoints']['path'],payload)
    s.update(schemaVersion=3,owner=OWNER,generatedAt=datetime.now(timezone.utc).isoformat(),generatorSha256=sha(ROOT/OWNER),
             originalR2Supplement=pin(R2),nativeRuntimeProbe=pin(PROBE),nativeRuntimeProbeProducer=pin(PROBE_PRODUCER),originalDiagnosticProducer=pin(ORIGINAL),numericalComparisonPolicy=policy(),appendedViewpoints=pin(payload))
    s['inputFiles'].update({str(R2):R2_SHA,str(ORIGINAL):ORIGINAL_SHA,str(PROBE):PROBE_SHA,str(PROBE_PRODUCER):PROBE_PRODUCER_SHA,r2['appendedViewpoints']['path']:r2['appendedViewpoints']['sha256']})
    receipt=OUTPUT/'neighbor-finish-diagnostic-supplement.json';receipt.write_bytes(original.encoded(s));validated_supplement();print(json.dumps({'supplement':pin(receipt),'appendedViewpoints':pin(payload),'policy':policy()}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--append-to-clone');args=parser.parse_args()
    if args.append_to_clone:print(json.dumps(append_to_clone(args.append_to_clone)))
    else:build()
