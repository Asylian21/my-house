"""One selected source-plan and one changed-contract CPU preflight; no Unreal."""
from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-burkea-clay-native-study-r46.py'
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=module('_r46_study_guard',ROOT/'scripts/unreal/exterior-burkea-clay-guards-r46.py')
n=module('_r46_study_native',ROOT/'scripts/unreal/exterior-burkea-clay-native-r46.py')
def main():
    g.require(not g.STUDY.exists(),'One new source-plan/preflight only');n.native_idle();bundle=g.load_contract();base=bundle['base'];inputs={}
    def add(path):
        path=Path(path).resolve();g.require(not path.is_relative_to(g.PROJECT),'Never freeze mutable future candidate map/packages')
        value=g.sha(path);g.require(str(path)not in inputs or inputs[str(path)]==value,'Conflicting exact source pin');inputs[str(path)]=value
    def pins(value):
        if isinstance(value,dict):
            if {'path','sha256','bytes'}<=set(value):add(g.checked({k:value[k]for k in ('path','sha256','bytes')}))
            for row in value.values():pins(row)
        elif isinstance(value,list):
            for row in value:pins(row)
    # Preserve immutable observer/module closure without rerunning any old
    # producer/checker. New actual saved receipts and canonical bytes are added.
    for path,value in base['report']['inputFiles'].items():
        g.require(g.sha(path)==value,'Actual selected observer input changed');add(path)
    pins(base['report']);pins(bundle['source']);pins(bundle['binding']);pins(g.read(g.DECISION));pins(g.read(g.CLONE)['rootController'])
    for key in ('processPin','rawProcessPin','auditPin'):add(g.checked(base[key]))
    for rel in base['content']:add(base['project']/'Content'/rel)
    for rel in base['protected']:add(base['project']/rel)
    own=[ROOT/'scripts/unreal'/s for s in ('exterior-burkea-clay-guards-r46.py','exterior-burkea-clay-native-r46.py',
        'exterior-burkea-clay-native-study-r46.py','test_exterior_burkea_clay_native_r46.py',
        'exterior-burkea-clay-base-packet-r46.py','exterior-clay-roof-materials-r46.py')]
    for path in own+[g.LEAF_KERNEL,g.LEAF_MATH]:add(path)
    roof=g.module('_r46_study_exact_roof_dependencies',g.ROOF,g.ROOF_SHA)
    for path,value in ((roof.CONTRACT,roof.CONTRACT_SHA),(roof.KERNEL,roof.KERNEL_SHA),(roof.POLICY,roof.POLICY_SHA)):
        g.fixed(path,value);add(path)
    add(ROOT/'scripts/unreal/test_exterior_context_parcel_boundary_materials_r43.py')
    for row in n.primary_api().values():add(g.checked(row))
    expected=g.expected_counterfactual(base['savedWitness'],bundle);g.STUDY.mkdir()
    plan={'schema':g.SCHEMA,'schemaVersion':1,'owner':OWNER,'nativeOwner':n.OWNER,'createdAt':n.now(),
        'status':'selected-five-slot-material-source-ready-native-pending','binding':bundle['binding'],
        'sourceProposals':{k:v['proposalPin']for k,v in bundle['source'].items()},'selectedNativeReport':base['reportPin'],
        'selectedNativeProcess':base['processPin'],'selectedCurrentByteAudit':base['auditPin'],'rootImageDecision':g.pin(g.DECISION),
        'projectClone':g.pin(g.CLONE),'expectedCounts':g.COUNTS,'expectedNewPackages':g.expected_packages(bundle['source']),
        'originalActorWitnessSha256':g.digest(base['savedWitness']),'expectedActorWitnessSha256':g.digest(expected),
        'originalRawControlsSha256':g.digest(base['rawControls']),
        'materialReaderDispatch':base['materialReaderDispatch'],'oldCompleteMaterialGraphs':72,'oldCompleteVisible24TextureSnapshots':114,
        'previouslyUnrecordedAuxAndUsageCapturedBeforeAndSaved':3,'sourceGeometryPixelsAndOldMaterialAssetsChanged':False,
        'allowedExistingComponentSetters':{'leaf':{'actor':g.leaf_math().ACTOR,'slot':1},
            'roof':[{'actor':r['actor'],'component':r['component'],'slot':0}for r in bundle['source']['roof']['proposal']['targets']]},
        'combinedCaptureCausalLimitation':g.read(g.DECISION)['combinedCaptureCausalLimitation'],
        'primaryApi':n.primary_api(),'ownedSources':[g.pin(path)for path in own], 'inputFiles':inputs,
        'nativeExecuted':False,'gpuExecuted':False,**n.LIMITS}
    g.write(g.PLAN,plan);print(json.dumps({'plan':g.pin(g.PLAN),'inputFiles':len(inputs),'expectedCounts':g.COUNTS}),flush=True)
    n.preflight(g.STUDY/'source-preflight',bundle)
if __name__=='__main__':main()
