"""Freeze a concrete six-actual-saved-donor integration proposal; no native."""
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-realism-integration-study-r22.py'
sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('r22_study_actual_saved_guards',ROOT/'scripts/unreal/exterior-realism-integration-guards-r22.py')
guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)


def sources():
    return {'producer':ROOT/OWNER,'native':ROOT/'scripts/unreal/exterior-realism-integration-native-r22.py',
        'guards':ROOT/'scripts/unreal/exterior-realism-integration-guards-r22.py','rootCopy':ROOT/'scripts/unreal/exterior-realism-integration-copy-r22.py',
        'tests':ROOT/'scripts/unreal/test_exterior_realism_integration_r22.py','design':ROOT/'docs/unreal-realism-integration-r22.md'}


def build():
    guard.require(not guard.STUDY.exists(),'Integration study is immutable; create a new revision if anything changes')
    bundle=guard.load_donors();guard.STUDY.mkdir(parents=True)
    start=time.monotonic();test=subprocess.run([sys.executable,'-B',str(sources()['tests'])],cwd=ROOT,capture_output=True,text=True)
    log=guard.STUDY/'source-guard-tests.log';log.write_text(test.stdout+test.stderr)
    match=re.search(r'Ran (\d+) tests? in ',test.stdout+test.stderr)
    tests={'status':'passed'if test.returncode==0 else'failed','exitCode':test.returncode,'testCount':int(match.group(1))if match else None,
        'elapsedSeconds':time.monotonic()-start,'nativeExecuted':False,'scope':'Actual saved donor/counterfactual/policy fixtures; no new native/GPU or appearance acceptance.',
        'log':guard.pin(log)}
    guard.write(guard.STUDY/'source-guard-tests.json',tests)
    guard.require(test.returncode==0 and tests['testCount']==12,'Integration CPU tests failed; preserve this output')
    files={}
    for name,key in (('originalBeforeWitness','before'),('originalExpectedWitness','expectedOriginal'),('addedActorTemplates','templates'),
        ('originalGeometryAfter','originalGeometryAfter'),('copiedPackages','packages')):
        path=guard.STUDY/(name+'.json');guard.write(path,bundle[key]);files[name]=guard.pin(path)
    owned={};inputs=dict(bundle['inputFiles'])
    for role,path in sources().items():
        destination=guard.STUDY/('source-'+path.name);shutil.copyfile(path,destination)
        owned[role]={'live':guard.pin(path),'snapshot':guard.pin(destination)}
        inputs[str(path)]=guard.sha(path);inputs[str(destination)]=guard.sha(destination)
    for entry in files.values():inputs[entry['path']]=entry['sha256']
    neighbor=bundle['reports']['neighbors'];view=Path(neighbor['project'])/'Content/Data/viewpoints.json'
    original=guard.read(guard.BASE/'Project/BreziTwin/Content/Data/viewpoints.json');current=guard.read(view)
    diagnostic=guard.read(guard.check_pin(neighbor['diagnosticViewpoint']['supplement']))
    guard.require(current['views'][:-1]==original['views']and len(current['views'])==len(original['views'])+1
        and current['views'][-1]==diagnostic['view']
        and {k:v for k,v in current.items()if k!='views'}=={k:v for k,v in original.items()if k!='views'},
        'Only exact original camera prefix plus R18 diagnostic view required')
    inputs[str(view)]=guard.sha(view)
    plan={'schema':guard.SCHEMA,'owner':OWNER,'status':'source-only-saved-donor-integration-native-pending','generatedAt':guard.now(),
        'baseNativeReport':guard.pin(guard.BASE/'exterior-import-report.json'),
        'baseContentInventory':bundle['evidence']['baseContentInventory'],'baseProjectProof':bundle['evidence']['baseProjectProof'],
        'reusedBaseEvidencePlan':guard.pin(ROOT/'output/unreal/exterior-canopy-transmission-20261001-r1-study/canopy-transmission-plan.json'),
        'donors':bundle['donors'],'audit':guard.EXPECTED,'scopeAudit':bundle['scopeAudit'],**files,
        'diagnosticViewpoints':guard.pin(view),'sourceGuardTests':guard.pin(guard.STUDY/'source-guard-tests.json'),
        'ownedSources':owned,'inputFiles':inputs,'activeDesign':bundle['base']['activeDesign'],'setbacksMm':bundle['base']['setbacksMm'],
        'nativeExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,
        'shippingPackageProduced':False,'originalArchitectureNavigationCollisionLightingChanged':False,
        'nativeCounterfactualUsesOnlyDeclaredOriginalFieldsAndSavedDonorNewTemplates':True,
        'roofGridSeamsAndCompletePhotorealismAcceptanceRemainOpen':True,
        'knownReviewLimits':['Parent viewed paired R20 close images: thinner curved blades also expose bare patches and reduce apparent cover; no appearance acceptance.',
            'Parent viewed R23 roof images: partial photographic detail gain with unresolved color/grid seams; no full realism acceptance.'],
        'combinedAppearanceGoNoGo':'NO_GO_UNTIL_MATCHED_NATIVE_COMBINED_REVIEW'}
    guard.write(guard.PLAN,plan);guard.validate_plan()
    print(__import__('json').dumps({'plan':guard.pin(guard.PLAN),'audit':guard.EXPECTED,'nativeHelper':guard.pin(sources()['native']),
        'rootCopyHelper':guard.pin(sources()['rootCopy']),'tests':12,'nativeExecuted':False}))


if __name__=='__main__':build()
