"""Narrow class-spawn repair over immutable R43 source/export; no re-export."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OWNER='scripts/unreal/exterior-context-parcel-boundary-native-study-r43-r2.py'
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=module('_r43_r2_study_guard',ROOT/'scripts/unreal/exterior-context-parcel-boundary-guards-r43-r2.py');n=module('_r43_r2_study_native',ROOT/'scripts/unreal/exterior-context-parcel-boundary-native-r43-r2.py')
def main():
 g.require(not g.STUDY.exists(),'One new R2 plan/preflight only');bundle=g.load_contract();g.validate_clone(bundle);g.STUDY.mkdir();old=g.read(g.R1_PLAN);evidence=g.repair_evidence();inputs=dict(g.read(g.R1_PREFLIGHT)['inputFiles'])
 owned=[ROOT/'scripts/unreal'/p for p in ('exterior-context-parcel-boundary-guards-r43-r2.py','exterior-context-parcel-boundary-native-r43-r2.py','exterior-context-parcel-boundary-native-study-r43-r2.py','test_exterior_context_parcel_boundary_native_r43_r2.py')]
 def add(p):inputs[str(Path(p).resolve())]=g.sha(p)
 for p in owned+[g.CLONE,g.FAILURE_AUDIT,g.R1_PLAN,g.R1_PREFLIGHT,g.R1_GLB]:add(p)
 for row in evidence.values():
  if isinstance(row,dict)and set(row)=={'path','sha256','bytes'}:add(g.checked(row))
 for row in n.primary_api().values():add(g.checked(row))
 g.require(all(not Path(p).is_relative_to(g.PROJECT)for p in inputs),'Never freeze future mutable R43b project files')
 plan={**old,'schemaVersion':2,'repairSchema':g.REPAIR_SCHEMA,'actorSpawnRepairEvidence':evidence,'owner':OWNER,'nativeOwner':n.OWNER,'createdAt':n.now(),'binding':bundle['binding'],'sourceGlb':g.pin(g.R1_GLB),'immutableOriginalPlan':g.pin(g.R1_PLAN),'immutableOriginalPreflight':g.pin(g.R1_PREFLIGHT),'sourceGeometryOrPhotoPixelsChanged':False,'encodedSourceExportRepeated':False,'newActorPolicy':{'authenticatedSourceTemplate':g.TEMPLATE,'creationRoute':'EditorActorSubsystem.spawn_actor_from_class(StaticMeshActor)','newClassDefaultFrameObservedBeforePolicy':True,'exactSignedZeroIdentityGate':True,'newActorTransformSettersCalled':False,'hostQuaternionReconstructionCalled':False,'oldActorOrComponentSettersCalled':False,'duplicationApisCalled':False,'pawnResponseSetterCalled':False,'derivedDrawCacheSetterCalled':False,'newCollision':'NoCollision','allOtherTemplateFlagsRetained':True},'primaryApi':n.primary_api(),'ownedSources':[g.pin(p)for p in owned],'inputFiles':inputs}
 g.write(g.PLAN,plan);print(json.dumps({'plan':g.pin(g.PLAN),'inputFiles':len(inputs),'expectedCounts':g.COUNTS}),flush=True);n.preflight(g.STUDY/'source-preflight',bundle)
if __name__=='__main__':main()
