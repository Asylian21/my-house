"""Bind the immutable source R5 to one actual successful R30b native clone."""
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-ground-native-study-r32.py'
s=importlib.util.spec_from_file_location('r32_actual_saved_base_binding',ROOT/'scripts/unreal/exterior-context-yard-ground-native-guards-r32.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
MATERIAL_READY=ROOT/'output/unreal/exterior-context-yard-ground-20261002-r32-material-readiness/material-source-readiness.json'
MATERIAL_READY_SHA='b62f1071698f78c437dae89ad2301a78f9c1a9d89e4cf29f4ea2e487bebb2017'


def main():
 g.require(not g.STUDY.exists(),'Fresh bound source output required')
 source,base=g.load_source(),g.saved_base();targets=g.target_components(base);clone=g.validate_clone(source,base)
 g.require(g.sha(MATERIAL_READY)==MATERIAL_READY_SHA,'Frozen material readiness changed');material=g.read(MATERIAL_READY)
 g.require(material['schema']=='brezi-context-yard-two-existing-pbr-material-copies-r32'
  and material['status']=='source-materials-guarded-cpu-ready-native-base-pending'
  and material['nativeBaseReport']is None and material['actualNativeBaseSelectionComplete']is False
  and material['nativeExecuted']is False and material['sourceInputsUnchanged']is True
  and material['inputFilesBefore']==material['inputFilesAfter'],'Exact separate material source readiness required')
 owned={key:g.pin(ROOT/'scripts/unreal'/name)for key,name in {
  'producer':'exterior-context-yard-ground-native-study-r32.py','native':'exterior-context-yard-ground-native-r32.py',
  'nativeGuards':'exterior-context-yard-ground-native-guards-r32.py','sourceGuards':'exterior-context-yard-ground-source-guards-r32.py',
  'nativeTests':'test_exterior_context_yard_ground_native_r32.py','sourceTests':'test_exterior_context_yard_ground_source_r32.py',
  'materials':'exterior-context-yard-ground-materials-r32.py','materialTests':'test_exterior_context_yard_ground_materials_r32.py'}.items()}
 files={r['path']:r['sha256']for r in source['plan']['inputFiles']};files.update(g.read(base['process']['receipt']['path'])['sourcePinsBeforeNative'])
 files.update(material['inputFilesBefore'])
 g.require(material['testsResult']['exitCode']==0 and material['testsResult']['testCount']==8,'Eight material fixtures required')
 g.check_pin(material['testsResult']['log']);files[material['testsResult']['log']['path']]=material['testsResult']['log']['sha256']
 for row in list(owned.values())+[g.pin(g.source.PLAN),base['reportPin'],clone,g.pin(MATERIAL_READY),g.pin(base['native'].guard.PLAN),
  g.pin(ROOT/base['native'].OWNER),g.pin(ROOT/base['native'].guard.OWNER),base['process']['receipt'],base['process']['raw'],base['process']['log'],
  base['audit'],base['report']['savedActorWitness'],base['report']['expectedActorWitness'],base['report']['beforeActorWitness'],base['report']['afterContentInventory'],base['report']['protectedProjectProof']]:
  files[row['path']]=row['sha256']
 for key in ['proposal','sourceGlb','materialCopyProposals','sourceOverlapDepthProof','sourceGlbValidation','generator','snapshot']:
  row=source['plan'][key];files[row['path']]=row['sha256']
 for key in ['originalMaterialsSaved','originalTreesSaved','originalGrassSaved','originalGardenControls','retainedGardenControlsSaved','newSourceNativeMeasurements']:
  row=base['report'][key];files[row['path']]=row['sha256']
 api_root=Path('/Users/Shared/Epic Games/UE_5.8/Engine/Source')
 primary={k:g.pin(api_root/p)for k,p in {
  'meshMaterialOverride':'Runtime/Engine/Private/Components/MeshComponent.cpp',
  'staticMeshBinding':'Runtime/Engine/Private/Components/StaticMeshComponent.cpp',
  'componentVisibility':'Runtime/Engine/Classes/Components/SceneComponent.h',
  'nativeInstanceStorage':'Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h'}.items()}
 for row in primary.values():files[row['path']]=row['sha256']
 files[str(ROOT/'docs/unreal-context-yard-ground-r32.md')]=g.sha(ROOT/'docs/unreal-context-yard-ground-r32.md')
 for path,h in files.items():g.require(g.sha(path)==h,'Consumed source changed before selection')
 tests={};g.STUDY.mkdir()
 for name,count in [('test_exterior_context_yard_ground_source_r32.py',14),('test_exterior_context_yard_ground_native_r32.py',10)]:
  path=ROOT/'scripts/unreal'/name;result=subprocess.run([sys.executable,'-B',str(path)],text=True,capture_output=True,timeout=120)
  log=g.STUDY/(name+'.log');log.write_text(result.stdout+result.stderr)
  g.require(result.returncode==0,'Final owned source/native fixture failed')
  tests[name]={'exitCode':result.returncode,'testCount':count,'source':g.pin(path),'log':g.pin(log),'nativeExecuted':False};files[str(log)]=g.sha(log)
 plan={'schema':g.SCHEMA,'owner':OWNER,'status':'source-ready-actual-saved-r30b-yard-ground-native-pending','createdAt':datetime.now(timezone.utc).isoformat(),
  'sourceStudy':g.pin(g.source.PLAN),'sourceSummary':source['summary'],'baseNativeReport':base['reportPin'],'baseNativeProcess':base['process'],
  'baseCurrentByteAudit':base['audit'],
  'baseNativeHelper':g.pin(ROOT/base['native'].OWNER),'baseNativeGuards':g.pin(ROOT/base['native'].guard.OWNER),'baseNativePlan':g.pin(base['native'].guard.PLAN),
  'initialRootClone':clone,'materialSourceReadiness':g.pin(MATERIAL_READY),'ownedSources':owned,'inputFiles':files,'cpuTests':tests,
  'primaryInstalledApiSources':primary,
  'targets':targets,'expectedCounts':g.COUNTS,'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},
  'operation':{'oldGroundMeshAndMaterialOverrides':2,'oldWornComponentVisibilityOnly':1,'newClippedSubstrateFloor':1,'newExistingMasterHismGroups':3,
   'newLowRoots':1274,'originalBedsAnd13ShrubsPreserved':True,'oldRootTransformOrSeedSetterAllowed':False,'newWorldPositionShaderOffsets':False},
  'geometryPolicy':{'generatedR21F32BasisAndWinding':True,'sourceXYQuantizedBeforeElevation':True,'exactZeroXYRegionsBeforeHeight':21,
   'postHeightFacesDiscarded':0,'positiveFootprintsDropped':False,'approximateAreaThresholdUsed':False,
   'fullNativeOrderedPositionUV0UV1CornersRequired':32878,'normalsNativeReadbackAvailable':False,'tangentsNativeReadbackAvailable':False},
  'sourceLimits':{'landUseAndPlacementArtistAuthored':True,'surveyedElevation':False,'ecologicalFitVerified':False,
   'sourceLeafCoverageIsAppearanceAcceptance':False,'nativeDitherPixelsVerified':False},
  'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}
 g.write(g.PLAN,plan);g.validate_plan();print(json.dumps({'selectedPlan':g.pin(g.PLAN),'expectedCounts':g.COUNTS,'clone':clone,'nativeExecuted':False}))


if __name__=='__main__':main()
