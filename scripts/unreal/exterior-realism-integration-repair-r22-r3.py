"""Closed module-order-only R22 repair. No native/scene execution on import."""
import copy
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-realism-integration-repair-r22-r3.py'
SCHEMA='brezi-exterior-realism-complete-neighbor-material-lookup-repair-r22-r3'
STUDY=ROOT/'output/unreal/exterior-realism-integration-20261002-r22-r3-supplement'
SUPPLEMENT=STUDY/'realism-integration-material-lookup-repair.json'
CANDIDATE=ROOT/'output/unreal/exterior-20261002-r22c'
FAILED=ROOT/'output/unreal/exterior-20261002-r22b'
COPY_OWNER='scripts/unreal/exterior-realism-integration-copy-r22-r3.py'
CLONE_STATUS='verified-byte-identical-independent-apfs-r22c-project-clone-before-realism-integration-native-r3'
INITIAL_STATUS='verified-original-r16-independent-apfs-r22c-clone-neighbor-material-lookup-repair-pending'
COPY_STATUS='verified-byte-identical-independent-apfs-saved-donor-packages-copied-neighbor-material-lookup-repair-r3'
NATIVE_OWNER='scripts/unreal/exterior-realism-integration-native-r22-r3.py'
ORIGINAL_SHA={'guards':'6b84bcb2a40625465bddd0abc32cb2d306b38666771b98ab481a7dafeaebf674',
    'native':'a1c18139712cbb33c54ba9dcaa5aead6f60fc9f0a24bc00ef94e4636c03e8b1d',
    'rootCopy':'6ded764c72beeea775ac607d50610f615df66913980fbf99f092ed7d0dd7eb00',
    'plan':'749d722da80886509105b4e4fa68da665aa2769a2345e46afa7cc1d989659e7f'}
s=importlib.util.spec_from_file_location('r22_r2_original_closed_guard',ROOT/'scripts/unreal/exterior-realism-integration-guards-r22.py')
guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
previous_handle=importlib.util.spec_from_file_location('r22_r3_frozen_order_repair',ROOT/'scripts/unreal/exterior-realism-integration-repair-r22-r2.py')
previous=importlib.util.module_from_spec(previous_handle);previous_handle.loader.exec_module(previous)
g=guard.g
require,read,write,sha,pin,check_pin,digest,now=(getattr(guard,k)for k in ('require','read','write','sha','pin','check_pin','digest','now'))


def sources():
    return {'native':ROOT/NATIVE_OWNER,'rootCopy':ROOT/COPY_OWNER,'repair':ROOT/OWNER,
        'producer':ROOT/'scripts/unreal/exterior-realism-integration-study-r22-r3.py',
        'tests':ROOT/'scripts/unreal/test_exterior_realism_integration_r22_r3.py',
        'design':ROOT/'docs/unreal-realism-integration-r22-r3.md'}


def original_source_proof():
    old=previous.original_source_proof()
    extra={'nativeR2':ROOT/'scripts/unreal/exterior-realism-integration-native-r22-r2.py',
        'copyR2':ROOT/'scripts/unreal/exterior-realism-integration-copy-r22-r2.py','supplementR2':previous.SUPPLEMENT}
    expected={'nativeR2':'55680ccca1b136746d7c91824fc6fc82be95e29d4e70f01e2dbec66426d4d0d4',
        'copyR2':'5a142625d83e542331a78ccd4925e09fa05e0c42122f90e88af031caddfcede9',
        'supplementR2':'51f0db4ca6d79c5967264c69208a585f33c31ec6c81afbecbfeca107917bdef6'}
    for key,path in extra.items():require(sha(path)==expected[key],'Frozen R22 R2 source changed: '+key)
    previous.validate_supplement()
    return {**old,**{key:pin(path)for key,path in extra.items()}}


def failure_proof():
    original_source_proof()
    raw_path=FAILED/'realism-integration-native-r2.log.json';process_path=FAILED/'realism-integration-native-r2-process.json'
    log_path=FAILED/'realism-integration-native-r2.log';report_path=FAILED/'realism-integration-native-report-r2.json'
    raw=read(raw_path);process=read(process_path);report=read(report_path)
    require(raw['code']==255 and raw['pid']==49239 and raw['signal']is None
        and raw['command']=='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
        and raw['args'][0]==str(FAILED/'Project/BreziTwin/BreziTwin.uproject')
        and '-script='+str(ROOT/'scripts/unreal/exterior-realism-integration-native-r22-r2.py')in raw['args']
        and '-run=pythonscript'in raw['args']and '-nullrhi'in raw['args'],'Actual failed R2 native process differs')
    require(process['processFile']==str(raw_path)and process['processFileSha256']==sha(raw_path)
        and process['logFile']==str(log_path)and process['logSha256']==sha(log_path)
        and process['reportSha256']==sha(report_path)=='a3c14f526db208e8a39470024f84d6ec606c04d15b4cc1c65cf401accd7f407b'
        and process['sourcePinsUnchangedAfterNative']is True and len(process['sourcePinsBeforeNative'])==410
        and process['controllerSha256BeforeNative']==process['controllerSha256AfterNative']==sha(process['controller']),
        'Actual failed R2 terminal/process/source witness differs')
    for path,value in process['sourcePinsBeforeNative'].items():require(sha(path)==value,'Failed R2 source pin changed: '+path)
    require(report['owner']=='scripts/unreal/exterior-realism-integration-native-r22-r2.py'and report['status']=='failed'
        and report['nativeProcessId']==49239 and report['error']=="'context_boundary_post'"
        and report['repairSupplement']==pin(previous.SUPPLEMENT)
        and report['moduleOrderWitness']==read(check_pin(previous.read(previous.SUPPLEMENT)['moduleOrderStudy']))['policy'],
        'Actual failure must retain successful frozen-first order and exact missing retained-material key')
    text=log_path.read_text()
    require('KeyError: \'context_boundary_post\''in text and 'neighbor_initial=h[\'neighbor\'].verify_scene'in text
        and not(FAILED/'realism-integration-witness-saved.json').exists(),'R2 must fail at retained-material validation before map save')
    return {'raw':pin(raw_path),'process':pin(process_path),'log':pin(log_path),'report':pin(report_path),'pid':49239,'exitCode':255,
        'sourcePinsUnchanged':True,'sourcePinCount':410,'nativeReportCreated':True,
        'failure':"'context_boundary_post'",'failureBeforeMapSave':True,'frozenFirstModuleOrderPassed':True}


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
    require(data['schema']==SCHEMA and data['owner']=='scripts/unreal/exterior-realism-integration-study-r22-r3.py'
        and data['status']=='source-only-complete-neighbor-material-lookup-repair-native-pending'
        and data['selectedPlan']==pin(guard.PLAN)and data['originalSources']==original_source_proof()
        and data['failure']==failure_proof(),'Closed module-order repair basis differs')
    require(data['candidate']==str(CANDIDATE)and data['sceneScopeUnchanged']is True
        and data['changedBehavior']=='Resolve all37 neighbor rows through the same9-new-plus4-retained original material asset lookup; preserve R2 frozen-first module order'
        and all(data[k]is False for k in ('nativeExecuted','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingPackageProduced')),
        'Repair cannot broaden the original scene scope or claim native acceptance')
    plan=read(guard.PLAN);require(data['audit']==plan['audit']and data['scopeAudit']==plan['scopeAudit'],'Original scope/audit changed')
    require(set(data['ownedSources'])==set(sources()),'Exact new owned source roles required')
    old_supplement=previous.validate_supplement();expected_inputs=dict(old_supplement['inputFiles']);expected_inputs[str(previous.SUPPLEMENT)]=sha(previous.SUPPLEMENT)
    for role,live in sources().items():
        record=data['ownedSources'][role];require(record['live']==pin(live)
            and Path(record['snapshot']['path'])==STUDY/('source-'+live.name)
            and check_pin(record['snapshot']).read_bytes()==live.read_bytes(),'New live/snapshot source differs: '+role)
        for key in ('live','snapshot'):expected_inputs[record[key]['path']]=record[key]['sha256']
    for key in ('failureContentAudit','sourceTests','moduleOrderStudy'):
        record=data[key];check_pin(record);expected_inputs[record['path']]=record['sha256']
    for key in ('raw','process','log','report'):
        record=data['failure'][key];expected_inputs[record['path']]=record['sha256']
    require(data['inputFiles']==expected_inputs,'New repair source closure changed')
    for source,value in expected_inputs.items():require(sha(source)==value,'New repair source pin changed: '+source)
    audit=read(check_pin(data['failureContentAudit']))
    require(audit['status']=='verified-failed-r22b-native-before-save-byte-identical'
        and audit['contentFileCount']==4049 and audit['protectedFileCount']==132
        and audit['mapAndViewpointsUnchanged']is True and audit['allOriginalAndCopiedBytesUnchanged']is True,
        'Actual failed project byte audit differs')
    tests=read(check_pin(data['sourceTests']));require(tests['status']=='passed'and tests['exitCode']==0 and tests['testCount']==6,
        'Focused module-order CPU tests must pass')
    order=read(check_pin(data['moduleOrderStudy']));require(order['status']=='verified-cpu-all37-neighbor-material-keys-and-frozen-first-order'
        and order['nativeExecuted']is False and order['policy']['cacheDeletedOrReplaced']is False
        and order['neighborMaterialLookup']['rowCount']==37 and order['neighborMaterialLookup']['materialKeys']==13
        and order['neighborMaterialLookup']['newMaterialKeys']==9 and order['neighborMaterialLookup']['retainedMaterialKeys']==4,
        'Actual nested CPU helper load study required')
    return data
