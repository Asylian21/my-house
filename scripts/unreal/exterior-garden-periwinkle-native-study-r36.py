"""CPU-only exact saved-R34 binding for six complete original Periwinkle forms."""
from datetime import datetime,timezone
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-garden-periwinkle-native-study-r36.py'
s=importlib.util.spec_from_file_location('r36_owned_native_source_producer',ROOT/'scripts/unreal/exterior-garden-periwinkle-native-r36.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n);g=n.guard


def main():
 g.require(not g.STUDY.exists(),'One fresh R36 native study only')
 bundle=g.validate_source();base=bundle['base'];clone=g.validate_clone(base);ready=g.material_readiness();h=n.helpers(base)
 owned={name:g.pin(ROOT/'scripts/unreal'/name)for name in (
  'exterior-garden-periwinkle-native-study-r36.py','exterior-garden-periwinkle-native-guards-r36.py',
  'exterior-garden-periwinkle-native-r36.py','exterior-garden-periwinkle-materials-r36.py',
  'test_exterior_garden_periwinkle_native_r36.py','test_exterior_garden_periwinkle_native_guards_r36.py')}
 files=dict(base['report']['inputFiles']);files.update(g.read(base['process']['receipt']['path'])['sourcePinsBeforeNative']);files.update(bundle['source']['proposal']['inputFiles'])
 def add(row):g.check_pin(row);files[row['path']]=row['sha256']
 def nested(value):
  if isinstance(value,dict):
   if set(value)in ({'path','sha256'},{'path','sha256','bytes'}):add(value)
   else:
    for v in value.values():nested(v)
  elif isinstance(value,list):
   for v in value:nested(v)
 nested(bundle['source']['proposal']);nested(base['report']);nested(base['process']);nested(ready)
 for row in [*owned.values(),g.pin(g.PROPOSAL),clone,base['reportPin'],base['audit'],g.pin(g.MATERIAL_READY)]:add(row)
 primary=n.primary_api()
 for row in primary.values():add(row)
 g.require({m['materialKey']for m in bundle['source']['models'].values()}=={bundle['source']['recipe']['key']},'Source recipe/model key differs')
 for path,value in files.items():g.require(g.sha(path)==value,'Original consumed bytes changed before native selection: '+path)
 g.STUDY.mkdir();snapshot=g.STUDY/'owned-source';snapshot.mkdir()
 snapshots={}
 for name,row in owned.items():
  target=snapshot/name;target.write_bytes(Path(row['path']).read_bytes());snapshots[name]=g.pin(target);add(snapshots[name])
 row={'schema':g.SCHEMA,'schemaVersion':1,'owner':OWNER,'nativeOwner':n.OWNER,
  'status':'source-ready-exact-saved-r34-whole384-original-periwinkle-native-pending','createdAt':datetime.now(timezone.utc).isoformat(),
  'candidateOutput':str(g.CANDIDATE),'sourceProposal':g.pin(g.PROPOSAL),'baseNativeReport':base['reportPin'],'baseNativeProcess':base['process'],
  'baseCurrentByteAudit':base['audit'],'projectClone':clone,'materialReadiness':g.pin(g.MATERIAL_READY),
  'ownedSources':owned,'ownedSourceSnapshots':snapshots,'inputFiles':files,'expectedCounts':g.COUNTS,'newGroupOrder':list(g.MODELS),
  'retiredRootIds':[r['rootId']for r in bundle['source']['placements']], 'wholeGroupRetirements':bundle['source']['proposal']['retireWholeOriginalGroups'],
  'activeDesign':bundle['source']['proposal']['activeDesign'],'setbacksMm':{'street':3000,'east':3000},
  'moduleOrderWitness':h['moduleOrderWitness'],'primaryInstalledApiSources':primary,
  'originalNodeBinding':{'identity':'Original glTF source node actor label, followed by full native ordered corner proof and owned canonical rename',
   'meshNameUsedForSourceIdentity':False,'sourceNodes':[{k:r[k]for k in ('id','originalSourceMeshName','canonicalExportName')}for r in bundle['source']['models'].values()],
   'sourceLabelPrimaryChainPinned':True,'actualImportedActorLabelsVerified':False},
  'geometryReadbackRequired':{'completeOriginalForms':6,'originalProviderLodsPerForm':1,'uniqueSourceVertices':31801,'uniqueNativeTriangles':34350,
   'allSourceAttributes':['POSITION','NORMAL','TEXCOORD_0','TEXCOORD_1','COLOR_0','COLOR_1'],'sourceTangentsPresent':False,
   'originalBinAndWrittenIndicesUnchanged':True,'fullNativeF32PositionUv0Uv1OrderedWindingGateBeforeOldClear':True,
   'nativeNormalTangentColor0Color1ReadbackAvailable':False,'originalProviderLodChainClaimed':False},
  'wholeGroupRetirementPolicy':{'entireFourComponentsOnly':True,'originalActorsAndComponentsDeleted':False,'survivorTransformRecompositionPerformed':False,
   'oldLowRoots384ReplacedOnce':True,'preservedOriginalHeroes':12,'preservedOriginalFlowers':41,'preservedOriginalR34Ferns':36,
   'additionalRandomSeedsReadbackAvailable':False,'seedRangeReconstructionPerformed':False,'seedSettersAllowed':False},
  'rootMeasurementPolicy':{'originalWrappedXYAndQuaternionCopyRequired':True,'hostQuaternionReconstructionAllowed':False,
   'newUniformScaleAndExplicitBottomOffsetDeclared':True,'actualTransientRecoveredFramesAndStoredFMatrixBeforeMutationRequired':True,
   'nativeSavedRecoveredAndStoredMatrixExactEqualityRequired':True,'contactArithmeticPolicy':g.CONTACT_POLICY,
   'all384CompleteSourceCrownsCheckedThroughMeasuredStoredMatrix':True,'sourceCrownVertexChecksRequired':1981184,
   'freshNativeStoredMatricesMeasured':False,'sourceAuthoredHeightRoleChangeExplicit':True},
  'nativeApplied':False,'nativeExecuted':False,'gpuExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,
  'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,'yardIntegrationApplied':False,'surveyedPlacementVerified':False}
 g.write(g.PLAN,row)
 print({'selectedPlan':g.pin(g.PLAN),'expectedCounts':g.COUNTS,'inputFiles':len(files),'nativeExecuted':False},flush=True)
 n.preflight(g.STUDY/'source-preflight',bundle=bundle)

if __name__=='__main__':main()
