"""Closed module-order-only R22 repair. No native/scene execution on import."""
import copy
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-realism-integration-repair-r22-r2.py'
SCHEMA='brezi-exterior-realism-frozen-policy-order-repair-r22-r2'
STUDY=ROOT/'output/unreal/exterior-realism-integration-20261002-r22-r2-supplement'
SUPPLEMENT=STUDY/'realism-integration-order-repair.json'
CANDIDATE=ROOT/'output/unreal/exterior-20261002-r22b'
FAILED=ROOT/'output/unreal/exterior-20261002-r22a'
COPY_OWNER='scripts/unreal/exterior-realism-integration-copy-r22-r2.py'
CLONE_STATUS='verified-byte-identical-independent-apfs-r22b-project-clone-before-realism-integration-native-r2'
INITIAL_STATUS='verified-original-r16-independent-apfs-r22b-clone-native-order-repair-pending'
COPY_STATUS='verified-byte-identical-independent-apfs-saved-donor-packages-copied-native-order-repair-r2'
NATIVE_OWNER='scripts/unreal/exterior-realism-integration-native-r22-r2.py'
ORIGINAL_SHA={'guards':'6b84bcb2a40625465bddd0abc32cb2d306b38666771b98ab481a7dafeaebf674',
    'native':'a1c18139712cbb33c54ba9dcaa5aead6f60fc9f0a24bc00ef94e4636c03e8b1d',
    'rootCopy':'6ded764c72beeea775ac607d50610f615df66913980fbf99f092ed7d0dd7eb00',
    'plan':'749d722da80886509105b4e4fa68da665aa2769a2345e46afa7cc1d989659e7f'}
s=importlib.util.spec_from_file_location('r22_r2_original_closed_guard',ROOT/'scripts/unreal/exterior-realism-integration-guards-r22.py')
guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
g=guard.g
require,read,write,sha,pin,check_pin,digest,now=(getattr(guard,k)for k in ('require','read','write','sha','pin','check_pin','digest','now'))


def sources():
    return {'native':ROOT/NATIVE_OWNER,'rootCopy':ROOT/COPY_OWNER,'repair':ROOT/OWNER,
        'producer':ROOT/'scripts/unreal/exterior-realism-integration-study-r22-r2.py',
        'tests':ROOT/'scripts/unreal/test_exterior_realism_integration_r22_r2.py',
        'design':ROOT/'docs/unreal-realism-integration-r22-r2.md'}


def original_source_proof():
    paths={'guards':ROOT/'scripts/unreal/exterior-realism-integration-guards-r22.py',
        'native':ROOT/'scripts/unreal/exterior-realism-integration-native-r22.py',
        'rootCopy':ROOT/'scripts/unreal/exterior-realism-integration-copy-r22.py','plan':guard.PLAN}
    for role,path in paths.items():require(sha(path)==ORIGINAL_SHA[role],'Frozen R22 R1 source changed: '+role)
    return {role:pin(path)for role,path in paths.items()}


def failure_proof():
    original_source_proof()
    raw_path=FAILED/'realism-integration-native-r1.log.json';process_path=FAILED/'realism-integration-native-r1-process.json'
    log_path=FAILED/'realism-integration-native-r1.log';raw=read(raw_path);process=read(process_path)
    require(raw['code']==255 and raw['pid']==47497 and raw['signal']is None
        and raw['command']=='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
        and raw['args'][0]==str(FAILED/'Project/BreziTwin/BreziTwin.uproject')
        and '-script='+str(ROOT/'scripts/unreal/exterior-realism-integration-native-r22.py')in raw['args']
        and '-run=pythonscript'in raw['args']and '-nullrhi'in raw['args'],'Actual failed original native process differs')
    require(process['processFile']==str(raw_path)and process['processFileSha256']==sha(raw_path)
        and process['logFile']==str(log_path)and process['logSha256']==sha(log_path)
        and process['reportSha256']is None and process['sourcePinsUnchangedAfterNative']is True
        and len(process['sourcePinsBeforeNative'])==391
        and process['controllerSha256BeforeNative']==process['controllerSha256AfterNative']==sha(process['controller']),
        'Actual failed original terminal/process/source witness differs')
    for path,value in process['sourcePinsBeforeNative'].items():require(sha(path)==value,'Failed original source pin changed: '+path)
    text=log_path.read_text()
    require('Another performance policy is already imported'in text
        and 'h=helpers(bundle);reports=bundle' in text and 'importer,existing=g.frozen_modules' in text
        and not(FAILED/'realism-integration-native-report.json').exists(),'Failure must precede original scene/report opening')
    return {'raw':pin(raw_path),'process':pin(process_path),'log':pin(log_path),'pid':47497,'exitCode':255,
        'sourcePinsUnchanged':True,'sourcePinCount':391,'nativeReportCreated':False,
        'failure':'Another performance policy is already imported','failureBeforeMapLoad':True}


def policy_witness(evidence,before=None):
    record=evidence['frozenPipeline'][str(ROOT/'scripts/unreal/performance_scene_policy.py')]
    expected=check_pin(record);cached=sys.modules.get('performance_scene_policy')
    require(cached is not None and Path(cached.__file__).resolve()==expected.resolve(),
        'Frozen policy must already be loaded from the exact consumed snapshot')
    require(before is None or cached is before,'Reused helper replaced the frozen cached policy')
    return {'path':str(expected),'sha256':sha(expected),'bytes':expected.stat().st_size,
        'cachePreservedAcrossReusedHelpers':True,'cacheDeletedOrReplaced':False}


def validate_supplement(path=SUPPLEMENT):
    require(Path(path).resolve()==SUPPLEMENT,'Only exact new R22 R2 supplement is eligible')
    data=read(path)
    require(data['schema']==SCHEMA and data['owner']=='scripts/unreal/exterior-realism-integration-study-r22-r2.py'
        and data['status']=='source-only-frozen-policy-order-repair-native-pending'
        and data['selectedPlan']==pin(guard.PLAN)and data['originalSources']==original_source_proof()
        and data['failure']==failure_proof(),'Closed module-order repair basis differs')
    require(data['candidate']==str(CANDIDATE)and data['sceneScopeUnchanged']is True
        and data['changedBehavior']=='Load frozen pipeline before every reused/current helper; preserve exact frozen policy cache'
        and all(data[k]is False for k in ('nativeExecuted','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingPackageProduced')),
        'Repair cannot broaden the original scene scope or claim native acceptance')
    plan=read(guard.PLAN);require(data['audit']==plan['audit']and data['scopeAudit']==plan['scopeAudit'],'Original scope/audit changed')
    require(set(data['ownedSources'])==set(sources()),'Exact new owned source roles required')
    expected_inputs=dict(plan['inputFiles']);expected_inputs[str(guard.PLAN)]=sha(guard.PLAN)
    for role,live in sources().items():
        record=data['ownedSources'][role];require(record['live']==pin(live)
            and Path(record['snapshot']['path'])==STUDY/('source-'+live.name)
            and check_pin(record['snapshot']).read_bytes()==live.read_bytes(),'New live/snapshot source differs: '+role)
        for key in ('live','snapshot'):expected_inputs[record[key]['path']]=record[key]['sha256']
    for key in ('failureContentAudit','sourceTests','moduleOrderStudy'):
        record=data[key];check_pin(record);expected_inputs[record['path']]=record['sha256']
    for key in ('raw','process','log'):
        record=data['failure'][key];expected_inputs[record['path']]=record['sha256']
    require(data['inputFiles']==expected_inputs,'New repair source closure changed')
    for source,value in expected_inputs.items():require(sha(source)==value,'New repair source pin changed: '+source)
    audit=read(check_pin(data['failureContentAudit']))
    require(audit['status']=='verified-failed-r22a-native-before-map-byte-identical'
        and audit['contentFileCount']==4049 and audit['protectedFileCount']==132
        and audit['mapAndViewpointsUnchanged']is True and audit['allOriginalAndCopiedBytesUnchanged']is True,
        'Actual failed project byte audit differs')
    tests=read(check_pin(data['sourceTests']));require(tests['status']=='passed'and tests['exitCode']==0 and tests['testCount']==6,
        'Focused module-order CPU tests must pass')
    order=read(check_pin(data['moduleOrderStudy']));require(order['status']=='verified-cpu-frozen-first-nested-module-order'
        and order['nativeExecuted']is False and order['policy']['cacheDeletedOrReplaced']is False,
        'Actual nested CPU helper load study required')
    return data
