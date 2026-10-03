"""Freeze exact R20 root serialization references; preserve all failed trials."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-curved-grass-repair-r4.py'
OUTPUT=ROOT/'output/unreal/exterior-curved-grass-20261002-r4-supplement'
FAILURE=ROOT/'output/unreal/exterior-20261002-r20c'
FAILURE_REPORT_SHA='2f2429dfdb6aa5565450281d91561a232af070dfbd2f2957643d0ea36143a18d'
SCHEMA='brezi-original-curved-grass-exact-native-transform-repair-r4'
STATUS='source-only-curved-grass-exact-native-transform-repair-pending'
sys.dont_write_bytecode=True


def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


previous=load('r20_r4_frozen_enum_repair','exterior-curved-grass-repair-r3.py')
transforms=load('r20_r4_exact_transform_guard','exterior-curved-grass-transform-guards-r4.py')
guard=previous.guard
require,read,write,sha,pin,check_pin=guard.require,guard.read,guard.write,guard.sha,guard.pin,guard.check_pin


def sources():
    return {'producer':ROOT/OWNER,'nativeHelper':ROOT/'scripts/unreal/exterior-curved-grass-native-r4.py',
        'transformGuards':ROOT/'scripts/unreal/exterior-curved-grass-transform-guards-r4.py',
        'tests':ROOT/'scripts/unreal/test_exterior_curved_grass_r4.py','design':ROOT/'docs/unreal-curved-grass-r4.md'}


def lineage():
    previous.validated_supplement()
    report=FAILURE/'curved-grass-native-report-r3.json';process=FAILURE/'curved-grass-native-r3-process.json'
    require(sha(report)==FAILURE_REPORT_SHA,'Preserved failed R20c report changed')
    failed=read(report)
    require(failed['status']=='failed' and failed['nativeProcessId']==39796
        and failed['error']=='Actual native yaw/rotation changed beyond double-matrix decomposition roundoff',
        'R4 repair is not based on the actual measured native insertion failure')
    p=read(process);raw=FAILURE/'curved-grass-native-r3.log.json';log=FAILURE/'curved-grass-native-r3.log'
    require(Path(p['processFile'])==raw and Path(p['logFile'])==log and sha(raw)==p['processFileSha256']
        and sha(log)==p['logSha256'] and p['reportSha256']==FAILURE_REPORT_SHA,
        'Preserved R3 failure process closure changed')
    run=read(raw)
    require(run['code']==255 and run['pid']==39796 and p['sourcePinsUnchangedAfterNative'] is True
        and len(p['sourcePinsBeforeNative'])==93
        and p['controllerSha256BeforeNative']==p['controllerSha256AfterNative']==sha(p['controller']),
        'Preserved actual R3 failure or source closure differs')
    for path,h in p['sourcePinsBeforeNative'].items():require(sha(path)==h,'Frozen actual R3 source pin changed')
    native=load('r20_r4_original_validation','exterior-curved-grass-native-r3.py')
    path=previous.previous.PLAN;plan=read(path);result=native.validate_plan(plan,path)
    probe,lookup=transforms.validated_probe(result[5],result[4])
    require(probe['originalPlan']==pin(path) and len(lookup)==64,'Exact64 probe/source binding changed')
    return report,process,probe,result


def validated_supplement():
    report,process,probe,result=lineage();value=read(OUTPUT/'curved-grass-repair-supplement.json')
    require(value['schema']==SCHEMA and value['owner']==OWNER and value['status']==STATUS
        and value['originalPlan']==pin(previous.previous.PLAN)
        and value['previousMeasuredRepair']==pin(previous.OUTPUT/'curved-grass-repair-supplement.json')
        and value['preservedFailureReport']==pin(report) and value['preservedFailureProcess']==pin(process)
        and value['faithfulTransformProbe']==pin(transforms.PROBE)
        and value['faithfulTransformProbeProcess']==pin(transforms.probe_process()[0])
        and value['transformComparisonPolicy']==transforms.policy()
        and value['numericalComparisonPolicy']==guard.policy(), 'Unregistered exact per-root R4 supplement')
    require(all(value[k] is False for k in ('nativeExecuted','nativeAppearanceAccepted','fullPhotorealismAccepted',
        'performanceAccepted','shippingPackageProduced','originalSourcePayloadsChanged','materialRecipeChanged',
        'generalNumericEpsilonIntroduced','unfaithfulConstructorProbeUsedForAcceptance')),
        'R4 source repair claims acceptance or widens source inputs')
    require(set(value['newSourceFiles'])==set(sources()),'R4 owned source closure differs')
    for role,path in sources().items():
        row=value['newSourceFiles'][role]
        require(check_pin(row['live'])==path and check_pin(row['snapshot']).parent==OUTPUT
            and row['live']['sha256']==row['snapshot']['sha256'],'R4 owned snapshot differs')
    for path,h in value['inputFiles'].items():require(sha(path)==h,'R4 pinned source input changed: '+path)
    tests=read(check_pin(value['sourceGuardTests']))
    require(tests['status']=='passed' and tests['exitCode']==0 and tests['testCount']==16
        and tests['nativeExecuted'] is False,'R4 exact serialization rejection tests failed')
    return value


def build():
    require(not OUTPUT.exists(),'R4 supplement is immutable; choose another revision for future changes')
    report,process,probe,result=lineage();OUTPUT.mkdir(parents=True)
    start=time.monotonic();test=subprocess.run([sys.executable,'-B',str(sources()['tests'])],cwd=ROOT,capture_output=True,text=True)
    log=OUTPUT/'source-guard-tests.log';log.write_text(test.stdout+test.stderr)
    match=re.search(r'Ran (\d+) tests? in ',test.stdout+test.stderr)
    tests={'owner':OWNER,'status':'passed'if test.returncode==0 else'failed','exitCode':test.returncode,
        'testCount':int(match.group(1))if match else None,'elapsedSeconds':time.monotonic()-start,'log':pin(log),
        'nativeExecuted':False,'scope':'Actual pinned native64 evidence; adversarial CPU double-bit/input/matrix/envelope rejection. No new native launch.'}
    write(OUTPUT/'source-guard-tests.json',tests)
    require(test.returncode==0 and tests['testCount']==16,'R4 CPU tests failed; preserve this output')
    owned={}
    for role,path in sources().items():
        snapshot=OUTPUT/('source-'+path.name);shutil.copyfile(path,snapshot)
        owned[role]={'live':pin(path),'snapshot':pin(snapshot)}
    original=result[1];actual=guard.common.inventory(FAILURE/'Project/BreziTwin/Content')
    require(set(original)<=set(actual)and all(original[k]==actual[k]for k in original),
        'Failed R20c changed an original native file')
    added=sorted(set(actual)-set(original))
    require(len(added)==11 and all(p.startswith('Brezi/CurvedGrass20261001R20/')and p.endswith('.uasset')for p in added),
        'Failed candidate does not contain exactly11 owned new packages')
    write(OUTPUT/'preserved-failure-content-proof.json',{'actualContent':actual,'originalNativeFileCount':3975,
        'originalFilesExact':True,'newFailedCandidateFiles':added,'mapFileExact':original['Brezi/Maps/Brezi.umap'],
        'nativeOutput':str(FAILURE),'failedAssetsUsedAsSuccessfulDonor':False})
    probe_process,p=transforms.probe_process();inputs=dict(p['sourcePinsBeforeNative'])
    inputs.update({str(report):sha(report),str(process):sha(process),str(transforms.PROBE):sha(transforms.PROBE),
        str(probe_process):sha(probe_process),p['processFile']:p['processFileSha256'],p['logFile']:p['logSha256'],
        str(previous.OUTPUT/'curved-grass-repair-supplement.json'):sha(previous.OUTPUT/'curved-grass-repair-supplement.json')})
    for entry in probe['engineSourceEvidence'].values():inputs[entry['path']]=entry['sha256']
    for row in owned.values():
        for entry in row.values():inputs[entry['path']]=entry['sha256']
    maximums={k:v for k,v in probe.items()if k.startswith('maximum')}
    write(OUTPUT/'curved-grass-repair-supplement.json',{'schema':SCHEMA,'owner':OWNER,'status':STATUS,
        'generatedAt':guard.now(),'originalPlan':pin(previous.previous.PLAN),
        'previousMeasuredRepair':pin(previous.OUTPUT/'curved-grass-repair-supplement.json'),
        'preservedFailureReport':pin(report),'preservedFailureProcess':pin(process),
        'preservedFailureContentProof':pin(OUTPUT/'preserved-failure-content-proof.json'),
        'faithfulTransformProbe':pin(transforms.PROBE),'faithfulTransformProbeProcess':pin(probe_process),
        'actualNativeReferenceProcessId':transforms.PROBE_PID,'measuredMaximumsFacts':maximums,
        'transformComparisonPolicy':transforms.policy(),'numericalComparisonPolicy':guard.policy(),
        'newSourceFiles':owned,'inputFiles':inputs,'sourceGuardTests':pin(OUTPUT/'source-guard-tests.json'),
        'nativeExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,
        'shippingPackageProduced':False,'originalSourcePayloadsChanged':False,'materialRecipeChanged':False,
        'generalNumericEpsilonIntroduced':False,'unfaithfulConstructorProbeUsedForAcceptance':False})
    validated_supplement()
    print(json.dumps({'supplement':pin(OUTPUT/'curved-grass-repair-supplement.json'),
        'nativeHelper':pin(sources()['nativeHelper']),'transformGuards':pin(sources()['transformGuards']),
        'tests':tests['testCount'],'nativeExecuted':False}))


if __name__=='__main__':build()
