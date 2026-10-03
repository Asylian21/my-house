"""One CPU-only bound original props plan/preflight; no historical generation."""
from datetime import datetime,timezone
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-neighbor-props-native-study-r39-r2.py'
s=importlib.util.spec_from_file_location('_r39_owned_native_source',ROOT/'scripts/unreal/exterior-neighbor-props-native-r39-r2.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n);g=n.g


def main():
    g.require(not g.STUDY.exists(),'One fresh bound R39 source study only')
    bundle=g.load_contract();source,base=bundle['source'],bundle['base'];h=n.helpers(bundle);template=n.template_contract(bundle)
    g.require(g.sha(n.MATERIAL)==n.MATERIAL_SHA and g.sha(n.MATERIAL_READY)==n.MATERIAL_READY_SHA,'Frozen original material writer/readiness changed')
    ready=g.read(n.MATERIAL_READY)
    g.require(ready['fixtureRun']['exitCode']==0 and ready['nativeExecuted']is False,'Actual source-only nine-material-fixture receipt required')
    owned={file:g.pin(ROOT/'scripts/unreal'/file)for file in (
        'exterior-neighbor-props-native-study-r39-r2.py','exterior-neighbor-props-native-r39-r2.py','exterior-neighbor-props-guards-r39-r2.py',
        'exterior-neighbor-props-materials-r39.py','test_exterior_neighbor_props_native_r39_r2.py','test_exterior_neighbor_props_guards_r39_r2.py')}
    evidence=g.repair_evidence()
    files={**g.read(evidence['failedNativeProcess']['path'])['sourcePinsBeforeNative'],**base['report']['inputFiles'],**base['process']['sourcePinsBeforeNative']}
    def add(row):
        p=Path(row['path']);g.require(p.is_absolute()and p.is_file()and not p.is_symlink()and g.sha(p)==row['sha256'],
            'Actual pinned consumed original changed: '+str(p))
        if 'bytes'in row:g.require(p.stat().st_size==row['bytes'],'Exact consumed original size changed')
        files[str(p)]=row['sha256']
    def nested(value):
        if isinstance(value,dict):
            if {'path','sha256'}<=set(value):add(value)
            else:
                for v in value.values():nested(v)
        elif isinstance(value,list):
            for v in value:nested(v)
    nested(source['proposal']);nested(base['report']);nested(ready);nested(bundle['binding']);nested(evidence)
    primary=n.primary_api();nested(primary);nested(owned)
    for file in ('exterior-neighbor-props-native-r39.py','exterior-neighbor-props-native-study-r39.py','exterior-neighbor-props-guards-r39.py',
                 'test_exterior_neighbor_props_native_r39.py','test_exterior_neighbor_props_guards_r39.py',
                 'exterior-neighbor-props-contract-r39-draft.py','exterior-neighbor-props-native-r39-draft.py',
                 'exterior-neighbor-props-materials-r39-draft.py','test_exterior_neighbor_props_r39_draft.py'):
        add(g.pin(ROOT/'scripts/unreal'/file))
    add(g.pin(n.MATERIAL_READY))
    for path,value in files.items():g.require(g.sha(path)==value,'Frozen selected input changed before plan: '+path)
    g.STUDY.mkdir();snap=g.STUDY/'owned-source';snap.mkdir();snapshots={}
    for file,row in owned.items():
        target=snap/file;target.write_bytes(Path(row['path']).read_bytes());snapshots[file]=g.pin(target);add(snapshots[file])
    plan={'schema':g.SCHEMA,'schemaVersion':2,'owner':OWNER,'nativeOwner':n.OWNER,
        'status':'image-selected-whole-original-neighbor-props-source-ready-native-r2-pending','createdAt':datetime.now(timezone.utc).isoformat(),
        'binding':bundle['binding'],'repairSchema':g.REPAIR_SCHEMA,'repairEvidence':evidence,'nodePoseCalibration':bundle['nodePoseCalibration'],
        'privateMaterialBindingAdapter':n.material_adapter_evidence(),'candidateOutput':str(g.CANDIDATE),'sourceProposal':source['proposalPin'],
        'selectedNativeReport':base['reportPin'],'selectedNativeProcess':base['processPin'],'selectedCurrentByteAudit':base['auditPin'],
        'selectedRootImageDecision':g.pin(g.IMAGE_DECISION),'projectClone':g.pin(g.CLONE),'materialReadiness':g.pin(n.MATERIAL_READY),
        'ownedSources':owned,'ownedSourceSnapshots':snapshots,'inputFiles':files,'expectedCounts':g.COUNTS,
        'expectedNewPackageAssets':g.expected_new_packages(source),'templateActor':n.TEMPLATE,'templateActorWitness':template,
        'sourcePartOrder':[p['key']for rows in source['parts'].values()for p in rows],
        'sourceAssemblyOrder':[r['id']for r in source['proposal']['placements']],
        'sourceAssemblies':source['proposal']['placements'],'primaryApi':primary,'moduleOrderWitness':h['moduleOrderWitness'],
        'geometryIdentity':{'fourWholeOriginalMasters':4,'fullNativeOrderedF32PositionUV0SectionWindingTriangles':26601,
            'bothWholeHoseMeshesAndOriginalCoilNodeTranslationRequired':True,'triangleCountsOnlyRouteCandidates':True,
            'labelsOrNamesUsedForSourceIdentity':False,'originalExternalBinAndPNormalUV0IndicesUnchanged':True,
            'actualTemporaryObjectInventoryBeforeAnyGateRequired':True,'nativeNormalTangentNumericReadbackAvailable':False,
            'providerTangentsPresent':False,'generatedUvTangentsRequested':True,'sourceProviderLodChainPresent':False},
        'instancePosePolicy':{'authoredAssemblies':6,'composedSourcePartMembers':8,'oldTransformMatrixOrSeedSettersAllowed':False,
            'originalImportedUnbakedNodePoseRequired':True,'nativeComposeTransformsOfNodeThenAssemblyRoot':True,
            'independentActualRootTransformLocationPlusRotationScaleBeforeInsertionRequired':True,
            'exactMeasuredTransientAppliedSavedRecoveredAndFMatrixRequired':True,'sourceFloorWallContactOnly':True,
            'nativePhysicalContactCollisionSurveyVerified':False,'allSixAssembliesVisibleVerified':False},
        'originalPreservation':{'actors':5364,'rawInstanceComponents':2325,'rawInstanceMembers':678197,
            'fullMaterialGraphs':66,'previouslyRecordedUsageFlags':64,'newPreviouslyUnrecordedUsageObserveBeforeSaved':2,
            'visibleTextureSnapshotObjects':97,'visibleTextureFields':24,'hiddenCompressionNoneAccessed':False,
            'wholeSelectedSceneMapReplaced':False,'wholeOriginalCounterfactualBeforeAndSavedRequired':True},
        'opticalLimits':{'opaqueTwoSidedUV0OriginalPngAlternatives':True,'sourcePhotoPixelsEdited':False,
            'referencedJpegVersusOriginalPngPixelEquivalenceClaimed':False,'wateringCanSpecularZeroPreservesOnlyDielectricF0':True,
            'wateringCanMetalMapPreserved':True,'wateringCanGrazingIorOpticalEquivalenceClaimed':False},
        'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},
        'nativeExecuted':False,'gpuExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,
        'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,'activeOutputPromoted':False}
    g.write(g.PLAN,plan)
    print({'selectedPlan':g.pin(g.PLAN),'expectedCounts':g.COUNTS,'inputFiles':len(files),'nativeExecuted':False},flush=True)
    n.preflight(g.STUDY/'source-preflight',bundle=bundle)


if __name__=='__main__':main()
