"""Additive actual-R29 binding. Reviewed source proposal/export stay immutable."""
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-garden-composition-native-study-r30.py'
s=importlib.util.spec_from_file_location('r30_owned_actual_base_binding',ROOT/'scripts/unreal/exterior-garden-composition-guards-r30.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
READINESS=ROOT/'output/unreal/exterior-garden-composition-20261002-r30-material-readiness/material-source-readiness.json'
READINESS_SHA='f2a356551c1f33cd97a19b1cf4359659997a22fe9aecfbdd810d9623cf09d347'


def main():
 g.require(not g.STUDY.exists(),'Fresh actual-base binding path required');source,base=g.load_source(),g.saved_base();groups=g.bind_groups(source,base)
 clone=g.validate_clone(source,base);g.require(g.sha(READINESS)==READINESS_SHA,'Frozen six-fixture material readiness changed');material_ready=g.read(READINESS)
 g.require(material_ready['schema']=='brezi-garden-composition-material-r30-source-readiness'and material_ready['status']=='frozen-source-two-original-materials-native-pending'
  and material_ready['sourceOwnershipPinsUnchangedBeforeAndAfter']is True and material_ready['nativeExecuted']is False,'Typed material source readiness required')
 g.require(material_ready['cpuTests']['exitCode']==0 and material_ready['cpuTests']['passed']==6 and material_ready['cpuTests']['failed']==0,'Six actual CPU material fixtures required')
 g.check_pin(material_ready['cpuTests']['log'])
 maps=g.module('r30_owned_original_map_recipes','exterior-garden-composition-materials-r30.py');maps.validate_recipe(source['recipe'])
 owned={key:g.pin(ROOT/'scripts/unreal'/file)for key,file in {
  'native': 'exterior-garden-composition-native-r30.py','guards':'exterior-garden-composition-guards-r30.py',
  'producer':'exterior-garden-composition-native-study-r30.py','tests':'test_exterior_garden_composition_r30.py',
  'materials':'exterior-garden-composition-materials-r30.py','materialTests':'test_exterior_garden_composition_materials_r30.py'}.items()}
 files={row['path']:row['sha256']for row in source['proposal']['inputFiles']}
 files.update(g.read(base['process']['receipt']['path'])['sourcePinsBeforeNative'])
 files.update(material_ready['inputFiles'])
 files[material_ready['cpuTests']['log']['path']]=material_ready['cpuTests']['log']['sha256']
 for row in list(owned.values())+[g.pin(g.PROPOSAL),g.pin(g.GEOMETRY/'source-native-draft.json'),g.pin(READINESS),base['reportPin'],base['audit'],base['checkerReceipt'],
  clone,base['process']['receipt'],base['process']['raw'],base['process']['log'],base['report']['savedActorWitness'],base['report']['afterContentInventory'],base['report']['protectedProjectProof']]:files[row['path']]=row['sha256']
 for key in ['geometry','glb','materialRecipes','producer']:row=source['draft'][key];files[row['path']]=row['sha256']
 for row in owned.values():g.check_pin(row)
 g.STUDY.mkdir()
 plan={'schema':g.SCHEMA,'owner':OWNER,'status':'source-ready-actual-r29-base-garden-composition-native-pending','createdAt':datetime.now(timezone.utc).isoformat(),
  'sourceProposal':g.pin(g.PROPOSAL),'sourceDraft':g.pin(g.GEOMETRY/'source-native-draft.json'),'materialSourceReadiness':g.pin(READINESS),
  'baseNativeReport':base['reportPin'],'baseNativeProcess':base['process'],'baseCurrentByteAudit':base['audit'],'baseIndependentCheckerReceipt':base['checkerReceipt'],
  'initialRootClone':clone,'candidateOutput':str(g.CANDIDATE),'ownedSources':owned,'inputFiles':files,'expectedCounts':g.COUNTS,
  'originalGardenGroupBindings':{k:{x:v[x]for x in ['actor','component','oldMesh']}for k,v in groups.items()},
  'retiredRootIds':[r['rootId']for r in source['placements']],'newGroupOrder':list(source['models']),
  'activeDesign':source['proposal']['activeDesign'],'setbacksMm':{'street':3000,'east':3000},
  'operation':{'partialExistingComponents':2,'exactOriginalRemovedIndices':[r['removeSourceOrderedIndices']for r in source['proposal']['sourceGroupFilters']],
   'directPostRemovalWrappedStorageOrderOnly':True,'wholeOneMemberHeroRetirements':2,'newOwnedHismGroups':5,'newRootsPopulation':0,
   'sameOriginalXYZAndWrappedNativeRotation':True,'sourceAssignedWholeModelUniformScale':True,'originalRootContactHeightPreserved':True,
   'selectedNativeSourceRows':38,'retainedNativeSourceRows':435,'retainedMemberTransformRecomposition':False,'seedSetterPermitted':False,
   'additionalRandomSeedRangesReadbackAvailable':False,'randomShaderValuePreservationClaimed':False,'partialCustomDataFloatsMustBeZero':True},
  'geometryPolicy':{'uniqueSourceTriangles':4478,'instancedSourceTriangles':46806,'masters':5,'providerLodsPerMaster':1,
   'newFakeClonedLodsAllowed':False,'derivedTangentAttributeAuthored':False,'nativeTangentsRequestedFromOriginalUv':True,
   'normalTangentNativeReadbackAvailable':False,'sourceFloatBasis':'F32(100*x), F32(100*z), F32(100*F32(originalY-minOriginalY))',
   'originalNormalUvIndexBytesPreserved':True,'originalTriangleOrderAndWindingPreserved':True,'fullNativeF32PositionUV0CornerProofRequired':True,'naniteRequested':False},
  'readbackContract':{'all5351OriginalActorsCounterfactualOnly4ComponentCountsAndTransformDigests':True,'all435SurvivorRawMatricesRecoveredFramesOrderMainSeedCustomDataExact':True,
   'allOriginal78TreesAnd8949GrassRawControlsExact':True,'exact38NewMeasuredFramesAndStoredMatrices':True,'wholeSavedActorCount':5356,
   'old59Graphs87TexturesObservedAndByteProtected':True,'onlyOriginalContentMapChanges':True,'newOwnedPackages':18,'savedMapUnloadReloadRequired':True,
   'originalSourcePixelsUnchanged':True,'nativeNormalTangentReadbackAvailable':False},
  'sourceLimits':{'36LowHeightRoleChangesArtistAuthoredExplicit':True,'twoTallHeroSourceHeightRecipesPreserved':True,
   'sourceContainingCircleCoverage':source['proposal']['containingCircleSourceCoverage'],
   'containingCircleCoverageIsLeafOrVisibleCoverage':False,'gardenOccupancyOrHeightSurveyed':False,'ecologicalFitVerified':False,
   'sourceFrustumIsOcclusionOrNativeAppearanceProof':False,'matchedPurposefulEditorVisualStillRequired':True},
  'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}
 g.write(g.PLAN,plan);g.validate_plan();print(json.dumps({'plan':g.pin(g.PLAN),'clone':clone,'expectedCounts':g.COUNTS,'nativeExecuted':False}))


if __name__=='__main__':main()
