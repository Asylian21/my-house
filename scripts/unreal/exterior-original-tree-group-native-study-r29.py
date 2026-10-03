"""Freeze one exact four-root saved-donor native plan; no Unreal or asset copy."""
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-original-tree-group-native-study-r29.py'
s=importlib.util.spec_from_file_location('r29_new_source_guard',ROOT/'scripts/unreal/exterior-original-tree-group-guards-r29.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)


def main():
 source,roots,full=g.source();base,donor=g.actual_base(),g.saved_tree();g.require(not g.STUDY.exists(),'One fresh immutable R29 native plan required')
 initial=g.CANDIDATE/'original-tree-group-base-clone-proof.json';clone=g.read(initial)
 g.require(clone['schema']==g.SCHEMA and clone['status']==g.INITIAL_STATUS and clone['nativeBaseReport']==base['reportPin']and clone['originalTreeSourceProposal']==g.pin(g.SOURCE)
  and clone['selectedPlan']is None and clone['fileCount']==4175 and clone['packageCopyPending']is True and clone['nativeExecuted']is False,'Actual root pending clone required')
 command=[sys.executable,'-B',str(ROOT/'scripts/unreal/test_exterior_original_tree_group_r29.py')];tested=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=120)
 g.require(tested.returncode==0,'Focused source/native-contract tests failed')
 g.STUDY.mkdir();(g.STUDY/'cpu-source-tests.log').write_text(tested.stdout+tested.stderr)
 g.write(g.STUDY/'copied-packages.json',donor['packages']);g.write(g.STUDY/'original-expected-after-whole-group-retirement.json',g.empty_original(base['witness'],base['targetActor']))
 g.write(g.STUDY/'new-actor-template.json',donor['template']);owned={}
 for key,file in [('guard',g.OWNER),('native',g.NATIVE_OWNER),('copy',g.COPY_OWNER),('study',OWNER),('tests','scripts/unreal/test_exterior_original_tree_group_r29.py')]:
  live=ROOT/file;snapshot=g.STUDY/live.name;snapshot.write_bytes(live.read_bytes());owned[key]={'live':g.pin(live),'snapshot':g.pin(snapshot)}
 inputs={};
 def collect(value):
  if isinstance(value,dict):
   if set(('path','sha256','bytes'))<=set(value)and isinstance(value['path'],str):g.check_pin({k:value[k]for k in('path','sha256','bytes')});inputs[value['path']]=value['sha256']
   for child in value.values():collect(child)
  elif isinstance(value,list):
   for child in value:collect(child)
 for value in(source,base['report'],donor['sourceBundle']['r1'],donor['sourceBundle']['r2'],base['process'],donor['process'],owned):collect(value)
 inputs.update(base['report']['inputFiles'])
 for role,file in [('baseNative','exterior-context-yard-native-r28-r2.py'),('baseChecker','exterior-context-yard-editor-check-r16.py'),('baseGuard','exterior-context-yard-native-guards-r28-r2.py'),
                   ('treeNative','exterior-original-tree-native-r2.py'),('treeGuard','exterior-original-tree-guards-r2.py'),('treeMaterial','exterior-original-tree-materials.py')]:
  p=ROOT/'scripts/unreal'/file;inputs[str(p)]=g.sha(p)
 for row in(g.pin(g.SOURCE),g.pin(initial),g.pin(g.STUDY/'cpu-source-tests.log'),base['reportPin'],donor['reportPin'],donor['report']['sourcePreflight']):inputs[row['path']]=row['sha256']
 plan={'schema':g.SCHEMA,'owner':OWNER,'status':'source-native-plan-ready-four-original-grove-roots-actual-r28b-base','createdAt':datetime.now(timezone.utc).isoformat(),
  'sourceProposal':g.pin(g.SOURCE),'baseNativeReport':base['reportPin'],'savedTreeDonor':donor['reportPin'],'baseContentInventory':base['report']['afterContentInventory'],'baseProjectProof':base['report']['protectedProjectProof'],
  'rootFitReview':source['rootSelection'],'selectedRootIds':g.IDS,'selectedGroupId':g.GROUP,'originalGroupActor':base['targetActor'],
  'originalExpectedAfterWholeGroupRetirement':g.pin(g.STUDY/'original-expected-after-whole-group-retirement.json'),'newActorTemplate':g.pin(g.STUDY/'new-actor-template.json'),
  'copiedPackages':g.pin(g.STUDY/'copied-packages.json'),'packageCount':17,'ownedSources':owned,'inputFiles':inputs,'activeDesign':source['activeDesign'],'setbacksMm':{'street':3000,'east':3000},
  'operation':{'retiredOldMembers':4,'newOwnedMembers':4,'newOwnedActors':1,'otherGroveRootsPreserved':74,'oldGroupRemainingMembers':0,'newPopulation':0,
    'oldActorComponentDeleted':False,'retainedMemberReconstruction':False,'originalGrassMemberMutation':False,'seedRangeReconstruction':False},
  'expectedCounts':{'originalActors':5350,'savedActors':5351,'fullHismComponents':2313,'fullHismInstances':676957,'groveOriginalRemainingRoots':74,
    'newOwnedTreeRoots':4,'scopedMaterialGraphs':59,'scopedTextureObjects':87,'copiedPackages':17,'contentFiles':4060,'protectedFiles':132},
  'newMemberPolicy':{'prototypeActualDonorActor':donor['templateActor'],'oldCullStartEndCm':base['targetWitness']['components'][0]['instanceCullCm'],'NoCollision':True,'navigation':False,'qualityDetail':False,'windWPO':False,
    'sameWholeSourceUniformFit':True,'retainedWrappedOriginalXYZAndQuaternionCopyRequired':True,'commonBottomOriginShiftExplicit':True,'newRootPopulation':0},
  'readbackContract':{'nativeMeshDescriptionTriangles':2062487,'nativeSampledTriangles':4096,'nativeUnsampledTriangles':2058391,'newMeasuredInstances':4,'fullStoredMatrixProjectedSourceVertices':7109112,
    'remainingOriginalGroveRootsRawControls':74,'originalGrassRawControls':8949,'originalNativeGeometryAndMaterialsLoadedFrom17SavedPackages':True,
    'newNativeGeometryGenerated':False,'nativeNormalsTangentsAvailable':False,'AdditionalRandomSeedsAvailable':False,'noGeneralFloatingPointToleranceIntroduced':True},
  'sourceReviewLimits':source['appearanceLimits']+['R29 actual new matrices/crowns are measured in a faithful transient before any target mutation and must save/reload exactly. CPU source counts are not render/performance acceptance.'],
  'tests':{'command':command,'exitCode':0,'testCount':8,'log':g.pin(g.STUDY/'cpu-source-tests.log'),'fixturesAreNativeProof':False},
  'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'ecologicalFitVerified':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}
 g.write(g.PLAN,plan);g.validate_plan()
 g.write(g.STUDY/'source-readiness.json',{'schema':g.SCHEMA,'owner':OWNER,'status':'verified-source-four-root-actual-r28b-native-plan-ready-package-copy-pending',
  'plan':g.pin(g.PLAN),'actualBasePid':base['process']['pid'],'actualDonorPid':donor['process']['pid'],'allInputPinsCurrentExact':True,'inputPinCount':len(inputs),'tests':plan['tests'],'nativeR29Executed':False,
  'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False})
 print(json.dumps({'plan':g.pin(g.PLAN),'readiness':g.pin(g.STUDY/'source-readiness.json'),'nativeExecuted':False}))


if __name__=='__main__':main()
