"""Freeze the measured R20 runtime repair without altering original payloads."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-curved-grass-repair-r2.py'
OUTPUT = ROOT/'output/unreal/exterior-curved-grass-20261002-r2-supplement'
PLAN = ROOT/'output/unreal/exterior-curved-grass-20261002-r1-study/curved-grass-plan.json'
PLAN_SHA = 'f43f3d224c9d43d70091a910e5618052fa942bb593ac55d3cc900eace8a8aa68'
STATUS = 'source-only-measured-curved-grass-runtime-repair-native-pending'
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('r20_repair_guard',ROOT/'scripts/unreal/exterior-curved-grass-guards-r2.py')
guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
require, read, write, sha, pin, check_pin, now = (getattr(guard,k) for k in ('require','read','write','sha','pin','check_pin','now'))


def sources():
    return {'producer': ROOT/OWNER, 'nativeHelper': ROOT/'scripts/unreal/exterior-curved-grass-native-r2.py',
        'geometryGuards': ROOT/guard.OWNER, 'ownershipReadback': ROOT/'scripts/unreal/exterior-curved-grass-readback-r2.py',
        'tests': ROOT/'scripts/unreal/test_exterior_curved_grass_r2.py', 'design': ROOT/'docs/unreal-curved-grass-r2.md'}


def lineage():
    guard.measured_probe(); require(sha(PLAN)==PLAN_SHA, 'Frozen original R20 plan changed')
    process = guard.PROBE.with_name('curved-grass-numeric-probe-r2-process.json')
    p = read(process)
    require(p['code']==0 and p['pid']==36984 and p['sourcePinsUnchanged'] is True
            and p['reportSha256']==guard.PROBE_SHA and len(p['sourcePins'])==47,
            'Actual numerical-only native process proof missing')
    for path, expected in p['sourcePins'].items(): require(sha(path)==expected, 'Measured probe source pin changed: '+path)
    require(p['args'][2] == '-script='+str(ROOT/guard.PROBE_OWNER) and '-nullrhi' in p['args'],
            'Actual process was not the approved numeric-only probe')
    return process, p


def validated_supplement(path=None):
    process, p = lineage(); path=Path(path or OUTPUT/'curved-grass-repair-supplement.json'); s=read(path)
    require(s['schema']=='brezi-original-curved-grass-measured-runtime-repair-r2'
            and s['owner']==OWNER and s['status']==STATUS and s['originalPlan']==pin(PLAN)
            and s['nativeRuntimeProbe']==pin(guard.PROBE) and s['nativeRuntimeProcess']==pin(process)
            and s['numericalComparisonPolicy']==guard.policy(), 'Unapproved R20 measured repair supplement')
    require(all(s[k] is False for k in ('nativeExecuted','nativeAppearanceAccepted','fullPhotorealismAccepted',
            'performanceAccepted','shippingPackageProduced','originalSourcePayloadsChanged')),
            'CPU repair supplement claims native acceptance or changed payload')
    require(set(s['newSourceFiles'])==set(sources()), 'Repair source closure differs')
    for role, live in sources().items():
        row=s['newSourceFiles'][role]
        require(check_pin(row['live'])==live and check_pin(row['snapshot']).parent==OUTPUT
                and row['live']['sha256']==row['snapshot']['sha256'], 'Repair live/snapshot closure changed')
    for filename, expected in s['inputFiles'].items(): require(sha(filename)==expected, 'Repair input pin changed: '+filename)
    tests=read(check_pin(s['sourceGuardTests']))
    require(tests['status']=='passed' and tests['exitCode']==0 and tests['nativeExecuted'] is False
            and tests['testCount']==13, 'Measured repair rejection fixtures did not pass')
    return s


def build():
    require(not OUTPUT.exists(), 'Measured repair outputs are immutable; choose a new revision for changes')
    process, p=lineage(); OUTPUT.mkdir(parents=True)
    start=time.monotonic()
    test=subprocess.run([sys.executable,'-B',str(sources()['tests'])],cwd=ROOT,capture_output=True,text=True)
    log=OUTPUT/'source-guard-tests.log'; log.write_text(test.stdout+test.stderr)
    count=re.search(r'Ran (\d+) tests? in ',test.stdout+test.stderr)
    result={'owner':OWNER,'status':'passed' if test.returncode==0 else 'failed','exitCode':test.returncode,
        'testCount':int(count.group(1)) if count else None,'elapsedSeconds':time.monotonic()-start,
        'log':pin(log),'nativeExecuted':False,'scope':'Measured radius-only rejection and separate ownership CPU fixtures.'}
    write(OUTPUT/'source-guard-tests.json',result)
    require(test.returncode==0 and result['testCount']==13,'Repair source tests failed; preserve this output')
    owned={}
    for role, source in sources().items():
        snapshot=OUTPUT/('source-'+source.name); shutil.copyfile(source,snapshot)
        owned[role]={'live':pin(source),'snapshot':pin(snapshot)}
    inputs=dict(p['sourcePins']); inputs.update({str(process):sha(process),str(guard.PROBE):guard.PROBE_SHA})
    for suffix in ('curved-grass-numeric-probe-r2.log','curved-grass-numeric-probe-r2-console.log',
                   'curved-grass-native-process.json','curved-grass-native.log.json','curved-grass-native.log'):
        file=process.with_name(suffix); require(file.is_file(),'Original probe/failure artifact missing');inputs[str(file)]=sha(file)
    for row in owned.values():
        for entry in row.values():inputs[entry['path']]=entry['sha256']
    write(OUTPUT/'curved-grass-repair-supplement.json',{'schema':'brezi-original-curved-grass-measured-runtime-repair-r2',
        'owner':OWNER,'status':STATUS,'generatedAt':now(),'originalPlan':pin(PLAN),'nativeRuntimeProbe':pin(guard.PROBE),
        'nativeRuntimeProcess':pin(process),'numericalComparisonPolicy':guard.policy(),'inputFiles':inputs,
        'newSourceFiles':owned,'sourceGuardTests':pin(OUTPUT/'source-guard-tests.json'),
        'originalGeometry':read(PLAN)['geometry'],'originalSourceGlb':read(PLAN)['sourceGlb'],
        'originalRootSelection':read(PLAN)['rootSelection'],
        'nativeExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,
        'performanceAccepted':False,'shippingPackageProduced':False,'originalSourcePayloadsChanged':False,
        'separateNewGroupOwnershipPolicy':{'originalExteriorTagSpoofed':False,'delegatedOriginalGroups':1980,
            'delegatedRetainedOriginalInstances':631962,'newOwnedGroups':3,'newOwnedInstances':64}})
    validated_supplement(); print(json.dumps({'supplement':pin(OUTPUT/'curved-grass-repair-supplement.json'),
        'nativeHelper':pin(sources()['nativeHelper']),'sourceTests':result['testCount'],'nativeExecuted':False}))


if __name__=='__main__':build()
