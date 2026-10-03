"""Freeze one measured import-order repair and failed-project CPU byte audit."""
import copy
import importlib.util
import re
import shutil
import subprocess
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
OWNER='scripts/unreal/exterior-realism-integration-study-r22-r3.py'
s=importlib.util.spec_from_file_location('r22_r2_study_repair',ROOT/'scripts/unreal/exterior-realism-integration-repair-r22-r3.py')
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)


def build():
    r.require(not r.STUDY.exists(),'R2 supplement is immutable; create a new revision')
    plan,bundle=r.guard.validate_plan();failure=r.failure_proof();r.STUDY.mkdir(parents=True)
    project=r.FAILED/'Project/BreziTwin';expected=copy.deepcopy(bundle['content'])
    expected.update({row['relativeContentPath']:{'sha256':row['sha256'],'bytes':row['bytes']}for row in bundle['packages']})
    content=r.g.inventory(project/'Content');protected=r.g.project_proof(project)
    r.require(content==expected and protected==bundle['protected'],'Failed native changed original/copy bytes before map')
    audit_path=r.STUDY/'failed-native-r22b-byte-audit.json'
    r.write(audit_path,{'schema':r.SCHEMA,'owner':OWNER,'status':'verified-failed-r22b-native-before-save-byte-identical',
        'generatedAt':r.now(),'failedProcess':failure,'project':str(project),'contentFileCount':len(content),
        'protectedFileCount':len(protected),'logicalContentBytes':sum(v['bytes']for v in content.values()),
        'logicalProtectedBytes':sum(v['bytes']for v in protected.values()),'expectedContentSha256':r.digest(expected),
        'actualContentSha256':r.digest(content),'protectedSha256':r.digest(protected),
        'mapAndViewpointsUnchanged':all(content[k]==bundle['content'][k]for k in ('Brezi/Maps/Brezi.umap','Data/viewpoints.json')),
        'allOriginalAndCopiedBytesUnchanged':True,'originalContentFiles':3975,'copiedPackages':74,
        'nativeMapReadbackPerformedByThisAudit':False,'nativeExecuted':False})
    start=time.monotonic();test=subprocess.run([sys.executable,'-B',str(r.sources()['tests'])],cwd=ROOT,capture_output=True,text=True)
    log_path=r.STUDY/'source-material-lookup-tests.log';log_path.write_text(test.stdout+test.stderr)
    match=re.search(r'Ran (\d+) tests? in ',test.stdout+test.stderr)
    test_path=r.STUDY/'source-material-lookup-tests.json'
    tests={'status':'passed'if test.returncode==0 else'failed','exitCode':test.returncode,
        'testCount':int(match.group(1))if match else None,'elapsedSeconds':time.monotonic()-start,
        'nativeExecuted':False,'scope':'Actual37-row9-new/4-retained resolution, missing/foreign-key rejection, both caller routes, frozen-first imports and preserved failure closure.',
        'log':r.pin(log_path)}
    r.write(test_path,tests);r.require(test.returncode==0 and tests['testCount']==6,'Focused CPU repair tests failed; preserve study')
    native=r.guard.module('r22_r2_actual_nested_load','exterior-realism-integration-native-r22-r3.py')
    helpers=native.helpers(bundle);rows=helpers['neighbor'].export_records(helpers['neighbor'].guard.validated_candidate())
    assets=native.neighbor_material_assets(bundle,rows);order_path=r.STUDY/'neighbor-material-lookup-study.json'
    r.write(order_path,{'schema':r.SCHEMA,'owner':OWNER,'status':'verified-cpu-all37-neighbor-material-keys-and-frozen-first-order',
        'policy':helpers['moduleOrderWitness'],'reusedHelpers':{k:r.pin(v.__file__)for k,v in helpers.items()if hasattr(v,'__file__')},
        'neighborMaterialLookup':{'rowCount':len(rows),'materialKeys':len(assets),'newMaterialKeys':9,'retainedMaterialKeys':4,
            'assets':assets,'sourceRowBindings':{row['id']:assets[row['material']]for row in rows}},
        'frozenPolicyFirst':True,'nativeExecuted':False,'unrealApiCalled':False})
    old=r.previous.validate_supplement();inputs=dict(old['inputFiles']);inputs[str(r.previous.SUPPLEMENT)]=r.sha(r.previous.SUPPLEMENT);owned={}
    for role,path in r.sources().items():
        snapshot=r.STUDY/('source-'+path.name);shutil.copyfile(path,snapshot)
        owned[role]={'live':r.pin(path),'snapshot':r.pin(snapshot)}
        for key in ('live','snapshot'):inputs[owned[role][key]['path']]=owned[role][key]['sha256']
    for path in (audit_path,test_path,order_path):inputs[str(path)]=r.sha(path)
    for key in ('raw','process','log','report'):record=failure[key];inputs[record['path']]=record['sha256']
    data={'schema':r.SCHEMA,'owner':OWNER,'status':'source-only-complete-neighbor-material-lookup-repair-native-pending',
        'generatedAt':r.now(),'selectedPlan':r.pin(r.guard.PLAN),'originalSources':r.original_source_proof(),
        'failure':failure,'failureContentAudit':r.pin(audit_path),'sourceTests':r.pin(test_path),'moduleOrderStudy':r.pin(order_path),
        'candidate':str(r.CANDIDATE),'sceneScopeUnchanged':True,
        'changedBehavior':'Resolve all37 neighbor rows through the same9-new-plus4-retained original material asset lookup; preserve R2 frozen-first module order',
        'audit':plan['audit'],'scopeAudit':plan['scopeAudit'],'ownedSources':owned,'inputFiles':inputs,
        'nativeExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,
        'shippingPackageProduced':False,'combinedAppearanceGoNoGo':plan['combinedAppearanceGoNoGo'],'knownReviewLimits':plan['knownReviewLimits']}
    r.write(r.SUPPLEMENT,data);r.validate_supplement()
    print(__import__('json').dumps({'supplement':r.pin(r.SUPPLEMENT),'native':r.pin(r.sources()['native']),
        'rootCopy':r.pin(r.sources()['rootCopy']),'sourcePins':len(inputs),'tests':6,'contentUnchanged':4049,'protectedUnchanged':132,'nativeExecuted':False}))


if __name__=='__main__':build()
