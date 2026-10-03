"""Freeze read-only original R16 raw-matrix capture plan; never launches native."""
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
OWNER='scripts/unreal/exterior-realism-grass-coverage-probe-study-r2.py'
s=importlib.util.spec_from_file_location('coverage_raw_matrix_study',ROOT/'scripts/unreal/exterior-realism-grass-coverage-probe-guards-r2.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)


def build():
    g.require(not g.STUDY.exists(),'Source probe study is immutable; use a new revision')
    basis,bundle,donor,original,groups=g.source_basis();previous=g.previous_failure();g.STUDY.mkdir(parents=True)
    project=g.n.guard.BASE/'Project/BreziTwin'
    content=g.n.g.inventory(project/'Content');protected=g.n.g.project_proof(project)
    g.require(content==bundle['content']and protected==bundle['protected'],'Original R16 changed after failed read-only probe')
    audit_path=g.STUDY/'failed-probe-original-r16-byte-audit.json'
    g.write(audit_path,{'status':'verified-original-r16-all4107-files-byte-exact-after-failed-readonly-probe-r1',
        'completedAt':g.now(),'project':str(project),'contentFileCount':len(content),'protectedFileCount':len(protected),
        'contentInventorySha256':g.digest(content),'protectedProjectSha256':g.digest(protected),'originalMapUnchanged':True,
        'nativeExecuted':False,'previousFailedProbe':previous})
    start=time.monotonic();test=subprocess.run([sys.executable,'-B',str(g.sources()['tests'])],cwd=ROOT,capture_output=True,text=True)
    log=g.STUDY/'cpu-guards.log';log.write_text(test.stdout+test.stderr)
    match=re.search(r'Ran (\d+) tests? in ',test.stdout+test.stderr)
    tests={'status':'passed'if test.returncode==0 else'failed','exitCode':test.returncode,'testCount':int(match.group(1))if match else None,
        'elapsedSeconds':time.monotonic()-start,'log':g.pin(log),'nativeExecuted':False}
    test_path=g.STUDY/'cpu-guards.json';g.write(test_path,tests)
    g.require(test.returncode==0 and tests['testCount']==8,'Source probe CPU guards failed; preserve study')
    engine=Path('/Users/Shared/Epic Games/UE_5.8/Engine')
    evidence={key:g.pin(engine/path)for key,path in {
        'instanceStructAndReflectedFields':'Source/Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h',
        'rawArrayValueSetTracking':'Source/Runtime/Engine/Private/InstancedStaticMesh.cpp',
        'hismRawArrayTreeRebuild':'Source/Runtime/Engine/Private/HierarchicalInstancedStaticMesh.cpp',
        'ownerCallable':'Source/Runtime/Engine/Classes/Components/ActorComponent.h',
        'pythonObjectPropertyApi':'Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyWrapperObject.cpp'}.items()}
    inputs=dict(g.n.repair.validate_supplement()['inputFiles']);inputs[str(g.n.repair.SUPPLEMENT)]=g.sha(g.n.repair.SUPPLEMENT);owned={}
    for role,path in g.sources().items():
        snapshot=g.STUDY/('source-'+path.name);shutil.copyfile(path,snapshot)
        owned[role]={'live':g.pin(path),'snapshot':g.pin(snapshot)}
        for key in ('live','snapshot'):inputs[owned[role][key]['path']]=owned[role][key]['sha256']
    for record in evidence.values():inputs[record['path']]=record['sha256']
    for record in previous.values():inputs[record['path']]=record['sha256']
    inputs[str(audit_path)]=g.sha(audit_path)
    inputs[str(test_path)]=g.sha(test_path)
    plan={'schema':g.SCHEMA,'owner':OWNER,'status':'source-only-original-grass-raw-matrix-probe-native-pending','generatedAt':g.now(),
        'sourceProject':str(g.n.guard.BASE/'Project/BreziTwin'),'probeOutput':str(g.OUTPUT),
        'baseNativeReport':basis['baseNativeReport'],'baseContentInventory':basis['baseContentInventory'],'baseProjectProof':basis['baseProjectProof'],
        'originalComposerPlan':g.pin(g.n.guard.PLAN),'frozenComposerRepair':g.pin(g.n.repair.SUPPLEMENT),
        'originalSavedGrassDonor':basis['donors']['grass']['report'],'originalMembers':donor['originalMembersBefore'],
        'groupControls':groups,'groupCounts':g.GROUP_COUNTS,'instances':8949,
        'futureRestorationCullPolicyCm':[18000,24000],'engineSourceEvidence':evidence,'ownedSources':owned,'inputFiles':inputs,'sourceTests':g.pin(test_path),
        'previousFailedProbe':previous,'failedProbeOriginalByteAudit':g.pin(audit_path),
        'propertyRepair':{'cppPropertyName':'AdditionalRandomSeeds','cppStructFields':['StartInstanceIndex','RandomSeed'],
            'pythonSnakeCaseExportNotAssumed':True,'unavailableRangesRecordedWithoutInventingEmptyList':True,
            'rawMatrixReadinessSeparateFromSupplementalSeedObservability':True},
        'nativeExecuted':False,'sourceSceneMutated':False,'appearanceAccepted':False,'performanceAccepted':False,'shippingAccepted':False,
        'transientSetterExperimentsAllowed':True,'transientActorsSpawnedOrComponentsRegistered':False,
        'scope':'Capture all original4-group matrices and test exact double reconstruction only in unowned transient meshless HISM objects; no map/component/asset saves or writes.'}
    g.write(g.PLAN,plan);g.validate_plan()
    print(__import__('json').dumps({'plan':g.pin(g.PLAN),'native':g.pin(g.sources()['native']),'sourcePins':len(inputs),'tests':8,
        'groups':4,'instances':8949,'nativeExecuted':False}))


if __name__=='__main__':build()
