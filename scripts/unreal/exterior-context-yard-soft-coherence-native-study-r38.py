"""One CPU-only final R38 source/preflight closure, never launches Unreal."""
import ast
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-soft-coherence-native-study-r38.py'
s=importlib.util.spec_from_file_location('r38_final_native_source',ROOT/'scripts/unreal/exterior-context-yard-soft-coherence-native-r38.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n);g=n.g
def now():return datetime.now(timezone.utc).isoformat()


def main():
    g.require(not g.STUDY.exists(),'New final study only; previous evidence is immutable')
    g.STUDY.mkdir();preflight_dir=g.STUDY/'source-preflight';preflight_dir.mkdir()
    bundle=g.load_contract();g.validate_clone(bundle);h=n.helpers(bundle);n.graph_records(bundle)
    owned=[ROOT/'scripts/unreal'/name for name in (
        'exterior-context-yard-soft-coherence-guards-r38.py','exterior-context-yard-soft-coherence-native-r38.py',
        'exterior-context-yard-soft-coherence-materials-r38.py','exterior-context-yard-soft-coherence-native-study-r38.py',
        'test_exterior_context_yard_soft_coherence_native_r38.py','test_exterior_context_yard_soft_coherence_materials_r38.py')]
    original={str(p):g.sha(p)for p in owned}
    for p in owned:ast.parse(p.read_text(),filename=str(p))
    command=[sys.executable,'-B','-m','unittest','test_exterior_context_yard_soft_coherence_native_r38','test_exterior_context_yard_soft_coherence_materials_r38','-v']
    log=preflight_dir/'cpu-guards.log';started=now();clock=time.monotonic()
    result=subprocess.run(command,cwd=ROOT/'scripts/unreal',stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=90)
    log.write_text(result.stdout)
    tests={'command':command,'startedAt':started,'completedAt':now(),'elapsedSeconds':time.monotonic()-clock,'exitCode':result.returncode,
        'expectedCases':18,'log':g.pin(log),'nativeExecuted':False,'mockedUObjectApisOnly':True}
    g.require(result.returncode==0 and 'Ran 18 tests'in result.stdout,'Final bounded18 CPU cases must pass; failure log preserved')
    g.require(all(g.sha(p)==v for p,v in original.items()),'Owned final sources changed during executed tests')
    files=g.input_files(bundle)
    for p in owned:files[str(p)]=g.sha(p)
    primary=Path('/Users/Shared/Epic Games/UE_5.8/Engine/Source')
    apis=[primary/p for p in ('Editor/MaterialEditor/Public/MaterialEditingLibrary.h',
        'Runtime/Engine/Classes/Engine/Texture.h','Runtime/Engine/Classes/Engine/TextureDefines.h',
        'Runtime/Engine/Classes/Engine/EngineTypes.h','Runtime/Engine/Public/Materials/MaterialExpressionTextureSample.h',
        'Runtime/Engine/Private/Materials/HLSLMaterialTranslator.cpp')]
    for p in apis:files[str(p)]=g.sha(p)
    policy=g.ROOT/'output/unreal/exterior-context-yard-soft-coherence-20261002-r38-native-draft-r2/native-policy-supplement.json'
    native_graphs=policy.with_name('proposed-native-graphs.json')
    for p in (policy,native_graphs,log):files[str(p)]=g.sha(p)
    g.require(g.read(native_graphs)==bundle['nativeGraphs'],'Exact immutable native mip adaptation required')
    g.require(all(g.sha(p)==v for p,v in files.items()),'Final full consumed source closure differs')
    snapshots=g.STUDY/'source-snapshots';snapshots.mkdir()
    sources={}
    for p in owned:
        destination=snapshots/p.name;shutil.copyfile(p,destination)
        sources[p.name]={'live':g.pin(p),'snapshot':g.pin(destination)}
    plan={'schema':g.SCHEMA,'schemaVersion':1,'owner':n.OWNER,'producer':OWNER,
        'status':'image-selected-soft-ground-source-validated-native-pending','createdAt':now(),'binding':bundle['binding'],
        'sourceStudy':bundle['source'],'nativeMaterialGraphs':g.pin(native_graphs),'nativeSamplingSupplement':g.pin(policy),
        'baseNativeReport':bundle['base']['reportPin'],'baseNativeProcess':bundle['base']['process'],'baseCurrentByteAudit':bundle['base']['audit'],
        'selectedRootImageDecision':bundle['base']['selection'],'projectClone':bundle['base']['clone'],
        'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},
        'targets':bundle['targets'],'expectedActorWitnessSha256':g.digest(bundle['expected']),
        'expectedCounts':{'actors':5364,'hismComponents':2325,'hismInstances':678197,'originalMaterialGraphs':64,'originalTextureObjects':96,
            'newMaterialGraphs':2,'newTextureObjects':1,'newPackages':3,'contentFiles':4103,'protectedFiles':132},
        'newPackageAssets':sorted([*g.ASSETS.values(),g.MASK_ASSET]),'samplingPolicy':bundle['samplingPolicy'],
        'nativeGraphAdaptation':g.validate_native_graphs(bundle['graphs'],bundle['nativeGraphs']),
        'moduleOrderWitness':h['moduleOrderWitness'],'ownedSources':sources,'primaryApiFiles':[g.pin(p)for p in apis],
        'cpuTests':tests,'sourceAstParseCount':len(owned),'inputFiles':files,
        'nativeExecuted':False,'newGeometry':0,'newActors':0,'originalPhotoPixelsEdited':False,'historicalSourceGeneratorsReplayed':False,
        'sourceBilinearFieldProofInheritedWithoutRasterReplay':True,'nativeMaskPropertyPolicyMeasured':False,
        'nativeTexelsDecoded':False,'nativeGpuPixelFormatVerified':False,'nativeGpuOutsideEquivalenceVerified':False,
        'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,
        'activeOutputPromoted':False}
    g.write(g.PLAN,plan)
    # The actual selected header, pins and immutable clone provenance are read
    # again; no inherited geometry or source polygon producer is executed.
    n.validate_plan(bundle)
    pf={'schema':g.SCHEMA,'schemaVersion':1,'owner':n.OWNER,'status':'image-selected-soft-ground-source-preflight-validated-native-pending',
        'completedAt':now(),'selectedPlan':g.pin(g.PLAN),'binding':bundle['binding'],'cpuTests':tests,'sourceAstParseCount':len(owned),
        'moduleOrderWitness':h['moduleOrderWitness'],'inputFiles':{**files,str(g.PLAN):g.sha(g.PLAN)},'nativeExecuted':False,
        'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False}
    pf_path=preflight_dir/'source-preflight.json';g.write(pf_path,pf);n.validate_preflight(pf_path,plan,bundle)
    frozen={**pf['inputFiles'],str(pf_path):g.sha(pf_path)}
    for row in sources.values():frozen[row['snapshot']['path']]=row['snapshot']['sha256']
    freeze_path=g.STUDY/'source-freeze.json';g.write(freeze_path,{'schema':g.SCHEMA,'owner':OWNER,'status':'frozen-source-only-native-pending',
        'sourceFiles':frozen,'sourceFilesCount':len(frozen),'allCurrentBytesExact':all(g.sha(p)==v for p,v in frozen.items()),'nativeExecuted':False})
    ready={'schema':g.SCHEMA,'owner':OWNER,'status':'READY-source-only-root-native-pending','selectedPlan':g.pin(g.PLAN),
        'sourcePreflight':g.pin(pf_path),'sourceFreeze':g.pin(freeze_path),'nativeHelper':g.pin(ROOT/n.OWNER),
        'cpuTests':tests,'sourceFilesCount':len(frozen),'sourceAstParseCount':len(owned),'peerReview':{'root':'bounded-read-pending-or-parent-recorded','materialAuthor':'bounded-full-native-api-scope-PASS'},
        'environment':{'BREZI_SOFT_GROUND_OUTPUT':str(g.CANDIDATE),'BREZI_SOFT_GROUND_PLAN_SHA256':g.sha(g.PLAN),
            'BREZI_SOFT_GROUND_PREFLIGHT':str(pf_path),'BREZI_SOFT_GROUND_PREFLIGHT_SHA256':g.sha(pf_path)},
        'reportFile':n.REPORT,'processStem':'soft-ground-native-r1','nativeExecuted':False,'nativeAppearanceAccepted':False,
        'fullPhotorealismAccepted':False,'performanceAccepted':False,'activeOutputPromoted':False}
    ready_path=g.STUDY/'source-readiness.json';g.write(ready_path,ready)
    print(json.dumps({'readiness':g.pin(ready_path),'plan':g.pin(g.PLAN),'preflight':g.pin(pf_path),'freeze':g.pin(freeze_path),
        'tests':18,'sourceFilesCount':len(frozen),'environment':ready['environment']}))


if __name__=='__main__':main()
