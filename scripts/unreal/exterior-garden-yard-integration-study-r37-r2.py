"""Bind selected actual R36b, root clone+14 packages and one focused CPU run."""
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-garden-yard-integration-study-r37-r2.py'
s=importlib.util.spec_from_file_location('r37_source_binding',ROOT/'scripts/unreal/exterior-garden-yard-integration-guards-r37-r2.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
TEST_COUNT=8


def main():
 b=g.selected_base();clone=g.validate_clone(b)
 g.require(not g.STUDY.exists(),'Exclusive new bound study required')
 cpp=b['project']/'Source/BreziTwin/BreziVegetationPatch.cpp';text=cpp.read_text()
 g.require(all(v in text for v in ('ABreziVegetationPatch::SynchronizeInstanceBounds','BuildTreeIfOutdated(false, true)',
                                  'UpdateBounds()','MarkRenderStateDirty()','MarkPackageDirty()')),
           'Selected native bounds/tree refresh source differs')
 clean=ROOT/'output/unreal/exterior-realism-clean-integration-20261002-r27-study/realism-clean-integration-plan.json'
 g.require(g.sha(clean)=='662ea41663142e22ff744530fd0337833389beaed1b1ca590e6a6cd53aa511a4','Frozen first helper evidence changed')
 owned={name:g.pin(ROOT/'scripts/unreal'/name)for name in (
  'exterior-garden-yard-integration-guards-r37-r2.py','exterior-garden-yard-integration-native-r37-r2.py',
  'exterior-garden-yard-integration-study-r37-r2.py','test_exterior_garden_yard_integration_r37_r2.py')}
 files=g.immutable_inputs(b)
 prior=g.prior_failed_attempt()
 for row in prior['files'].values():files[row['path']]=row['sha256']
 files.update(g.read(prior['files']['terminal']['path'])['sourcePinsBeforeNative'])
 for row in [*owned.values(),g.pin(cpp),g.pin(clean)]:files[row['path']]=row['sha256']
 before=dict(files);g.STUDY.mkdir()
 tests=ROOT/'scripts/unreal/test_exterior_garden_yard_integration_r37_r2.py'
 run=subprocess.run([sys.executable,'-B',str(tests)],text=True,capture_output=True,timeout=300)
 log=g.STUDY/'source-tests.log';log.write_text(run.stdout+run.stderr)
 g.require(run.returncode==0,'Bound R37 source/native fixtures failed; log preserved')
 for path,value in before.items():g.require(g.sha(path)==value,'Bound source changed during tests')
 snapshot={}
 for name,row in owned.items():
  path=g.STUDY/name;path.write_bytes(Path(row['path']).read_bytes());snapshot[name]=g.pin(path)
  files[str(path)]=snapshot[name]['sha256']
 files[str(log)]=g.sha(log)
 primary_root=Path('/Users/Shared/Epic Games/UE_5.8/Engine/Source')
 primary={name:g.pin(primary_root/path)for name,path in {
  'instanceStorage':'Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h',
  'hismRemoval':'Runtime/Engine/Private/HierarchicalInstancedStaticMesh.cpp',
  'componentVisibility':'Runtime/Engine/Classes/Components/SceneComponent.h',
  'meshMaterialOverride':'Runtime/Engine/Private/Components/MeshComponent.cpp'}.items()}
 for row in primary.values():files[row['path']]=row['sha256']
 plan={'schema':g.SCHEMA,'schemaVersion':2,'owner':OWNER,'nativeOwner':g.NATIVE_OWNER,
  'repairSchema':g.REPAIR_SCHEMA,'priorFailedAttempt':prior,'materialReaderDispatch':g.reader_dispatch(b),
  'status':'source-ready-selected-saved-r36b-yard-and-exact-graph-readers-r2-native-pending','createdAt':datetime.now(timezone.utc).isoformat(),
  'baseKey':b['key'],'baseNativeReport':b['reportPin'],'selectedRootReview':b['review'],
  'baseNativeProcess':b['process'],'baseCurrentByteAudit':b['audit'],'candidateOutput':str(g.CANDIDATE),
  'projectClone':clone,'draftReadiness':b['draftReadiness'],'donorInventory':g.pin(b['draftSource'].INVENTORY),
  'expectedCounts':g.counts(b['before'],b['donors'],b['report']),
  'newActorIdentityPolicy':'FRESH_NATIVE_SPAWN_MAPPING_BEFORE_CONFIGURATION_NO_EXISTING_ID_REUSE',
  'rootConstructorReplayPolicy':'ORIGINAL_R32_SOURCE_XYZ_YAW_SCALE_THEN_EXACT_INPUT_RECOVERED_MATRIX_AND_NATIVE_WRAPPED_ROWS',
  'synchronizeInstanceBoundsSource':g.pin(cpp),'frozenFirstHelperEvidence':g.pin(clean),
  'copiedPackageScope':b['donors']['inventory']['packages'],'targetOriginalActorWitnesses':b['donors']['inventory']['changedOriginalActorTargets'],
  'addedActorTemplates':b['donors']['inventory']['addedYardActorTemplates'],'ownedSources':owned,'sourceSnapshots':snapshot,
  'primaryInstalledApiSources':primary,'inputFiles':files,
  'cpuTests':{'source':g.pin(tests),'log':g.pin(log),'exitCode':run.returncode,'testCount':TEST_COUNT,'nativeExecuted':False},
  'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},
  'wholeR35MapOrR30GardenImported':False,'sourceGeometryRegenerated':False,'sourcePixelsEdited':False,
  'nativeApplied':False,'nativeExecuted':False,'gpuExecuted':False,'nativeAppearanceAccepted':False,
  'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,
  'nativeNormalTangentReadbackAvailable':False,'additionalRandomSeedRangesReadbackAvailable':False}
 g.write(g.PLAN,plan);g.validate_plan()
 print(json.dumps({'plan':g.pin(g.PLAN),'expectedCounts':plan['expectedCounts'],'sourceInputs':len(files),'cpuTests':TEST_COUNT,'nativeExecuted':False}))


if __name__=='__main__':main()
