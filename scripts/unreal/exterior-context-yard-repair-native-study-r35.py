"""CPU-only binding of three frozen repair scopes to the actual R35 clone."""
from datetime import datetime,timezone
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-repair-native-study-r35.py'
s=importlib.util.spec_from_file_location('r35_owned_scoped_native',ROOT/'scripts/unreal/exterior-context-yard-repair-native-r35.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n);g=n.guard

def main():
 g.require(not n.PLAN.parent.exists(),'One fresh native study only')
 bundle=g.validate_source();base=bundle['base'];clone=n.clone_validation(bundle);h=n.helpers(bundle)
 g.require(g.COUNTS==n.COUNTS,'Guard/native canonical census contract differs')
 owned={name:g.pin(ROOT/'scripts/unreal'/name)for name in (
  'exterior-context-yard-repair-native-study-r35.py','exterior-context-yard-repair-native-r35.py',
  'exterior-context-yard-repair-guards-r35.py','exterior-context-yard-repair-materials-r35.py',
  'test_exterior_context_yard_repair_native_r35.py','test_exterior_context_yard_repair_guards_r35.py',
  'test_exterior_context_yard_repair_materials_r35.py')}
 files=dict(base['report']['inputFiles']);files.update(g.read(base['process']['receipt']['path'])['sourcePinsBeforeNative'])
 files.update(bundle['proposal']['inputFilesBefore'])
 def add_pin(row):
  g.check_pin(row);files[row['path']]=row['sha256']
 def nested_pins(value):
  if isinstance(value,dict):
   if set(value)in ({'path','sha256','bytes'},{'path','sha256'}):add_pin(value)
   else:
    for v in value.values():nested_pins(v)
  elif isinstance(value,list):
   for v in value:nested_pins(v)
 nested_pins(bundle['proposal'])
 for row in [*owned.values(),g.pin(g.PROPOSAL),clone,base['reportPin'],base['audit'],*base['process'].values()]:
  if isinstance(row,dict):add_pin(row)
 for key in ('savedActorWitness','beforeActorWitness','expectedActorWitness','afterContentInventory','protectedProjectProof',
  'originalControlsBefore','originalControlsSaved','sourcePreflight','selectedPlan'):
  add_pin(base['report'][key])
 add_pin(g.pin(ROOT/'scripts/unreal/exterior-context-yard-ground-editor-check-r22.py'))
 material_helper=g.pin(ROOT/'scripts/unreal/exterior-context-yard-ground-materials-r32.py');add_pin(material_helper)
 original_ecology=ROOT/'output/unreal/exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json'
 add_pin(g.pin(original_ecology));ecology=g.read(original_ecology);add_pin(g.pin(ecology['geometryManifest']['path']))
 add_pin(g.pin(ROOT/'output/unreal/exterior-canopy-ecology-20260930-r3/canopy-ecology.glb'))
 primary_root=Path('/Users/Shared/Epic Games/UE_5.8/Engine/Source')
 primary={key:g.pin(primary_root/path)for key,path in {
  'instanceStorageAndRemoval':'Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h',
  'nativeRemoveAtSwapImplementation':'Runtime/Engine/Private/InstancedStaticMesh.cpp',
  'orderedMeshDescriptionGetters':'Runtime/MeshDescription/Public/MeshDescriptionBase.h',
  'materialEditingApi':'Editor/MaterialEditor/Public/MaterialEditingLibrary.h',
  'componentMeshSetter':'Runtime/Engine/Classes/Components/StaticMeshComponent.h',
  'componentMaterialSetter':'Runtime/Engine/Classes/Components/PrimitiveComponent.h'}.items()}
 for row in primary.values():add_pin(row)
 for path,digest in files.items():g.require(g.sha(path)==digest,'Original consumed source changed before new selection: '+path)
 geometry=n.ecology_expected_geometry(bundle)
 row={'schema':n.SCHEMA,'schemaVersion':1,'owner':OWNER,'nativeOwner':n.OWNER,
  'status':'source-ready-exact-saved-r32-three-scoped-repairs-native-pending','createdAt':datetime.now(timezone.utc).isoformat(),
  'candidateOutput':str(n.CANDIDATE),'baseNativeReport':base['reportPin'],'baseNativeProcess':base['process'],'baseCurrentByteAudit':base['audit'],
  'sourceProposal':g.pin(g.PROPOSAL),'projectClone':clone,'ownedSources':owned,'inputFiles':files,
  'primaryInstalledApiSources':primary,'expectedCounts':n.COUNTS,'moduleOrderWitness':h['moduleOrderWitness'],
  'affectedOriginalEcologyGroupIndices':{k:v['selectedSourceIndices']for k,v in bundle['ecologyGroups'].items()},
  'sourceIndexedRootIdentityRule':'Exact original groupId + colon + decimal sourceGroupInstanceIndex; original rows have no authored ID.',
  'hardTargets':{k:{x:v[x]for x in ('actor','component','currentMesh','currentMaterials','currentOverrides')}for k,v in bundle['floorTargets'].items()},
  'backdropTarget':bundle['backdropTarget'],'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},
  'operation':{'wholeOriginalClumpsRetired':34,'originalAffectedSurvivorsRawMatricesAndOrderRequired':1919,'all13ShrubsAnd1274NewLowRootsRawControlsPreserved':True,
   'rootOrMatrixRecompositionAllowed':False,'seedSettersAllowed':False,'newActors':0,'hardGeometryChannelsPermitted':['TEXCOORD_1.R'],
   'originalHardPositionNormalIndexUv0Uv1GBytesPreserved':True,'backdropComponentSlotOnly':bundle['backdropTarget']['actualComponent'],
   'twoMaterialCustomNearCoefficients':[.30,.65],'allOther14BackdropMaterialComponentsPreserved':True},
  'geometryReadbackRequired':{'originalEcologyModels':len(geometry),'originalEcologyLods':24,'fullOriginalEcologyPositionUv0Uv1OrderedTriangles':sum(len(l['corners'])for v in geometry.values()for l in v['lods']),
   'sourceCornerPrimitiveMaterialOrderRequired':True,'hardNativePositionUv0Uv1OrderedTriangles':4519,'freshSelectedNativeStoredMatrixSourceThreeLodSupports':34,
   'fullNativeNormalTangentReadbackAvailable':False,'allSourceLodSupportIsNativeAlphaVisibility':False},
  'sourceEvidenceBoundary':{'hardUnionCoverageRecomputedInNative':False,'coverageRuleSourceCpuFrozenAndSerializedF32':True,
   'sourceCompleteCensusCandidates':49,'sourceCompleteCensusCrossings':34,'actualNativeFreshnessPending':True,
   'AdditionalRandomSeedsReadbackAvailable':False,'perInstanceShaderRandomPreservationClaimed':False,'surveyedGroundElevation':False,
   'materialPackagesIndependentlyUnloaded':False,'nativePixelsCausallyAttributed':False},
  'nativeApplied':False,'nativeExecuted':False,'gpuExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}
 n.validate_plan_header(row,bundle);n.PLAN.parent.mkdir()
 snapshots=n.PLAN.parent/'owned-source';snapshots.mkdir()
 for name,p in owned.items():(snapshots/name).write_bytes(Path(p['path']).read_bytes())
 row['ownedSourceSnapshots']={name:g.pin(snapshots/name)for name in owned}
 for p in row['ownedSourceSnapshots'].values():files[p['path']]=p['sha256']
 g.write(n.PLAN,row)
 g.require(n.input_files(row,bundle)=={**files,str(n.PLAN):g.sha(n.PLAN)},'Final selected source input closure differs')
 print({'selectedPlan':g.pin(n.PLAN),'expectedCounts':n.COUNTS,'inputFiles':len(files),'nativeExecuted':False})

if __name__=='__main__':main()
