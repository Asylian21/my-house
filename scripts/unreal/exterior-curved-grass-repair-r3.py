"""Freeze R20's narrow native enum repair; keep R1/R2 and failures immutable."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-curved-grass-repair-r3.py'
OUTPUT=ROOT/'output/unreal/exterior-curved-grass-20261002-r3-supplement'
FAILURE=ROOT/'output/unreal/exterior-20261002-r20b'
FAILURE_REPORT_SHA='e0bd2fc08ad2b21bdb189ba8df60caa127a832fff6e9d3bf9ebd4e75da973860'
STATUS='source-only-curved-grass-native-enum-repair-pending'
sys.dont_write_bytecode=True
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
previous=load('r20_r3_frozen_numeric_repair','exterior-curved-grass-repair-r2.py')
guard=previous.guard;require,read,write,sha,pin,check_pin=guard.require,guard.read,guard.write,guard.sha,guard.pin,guard.check_pin


def sources():
    return {'producer':ROOT/OWNER,'nativeHelper':ROOT/'scripts/unreal/exterior-curved-grass-native-r3.py',
        'materials':ROOT/'scripts/unreal/exterior-curved-grass-materials-r3.py',
        'tests':ROOT/'scripts/unreal/test_exterior_curved_grass_r3.py','design':ROOT/'docs/unreal-curved-grass-r3.md'}


def headers():
    engine=Path('/Users/Shared/Epic Games/UE_5.8/Engine')
    paths={'engineTypes':engine/'Source/Runtime/Engine/Classes/Engine/EngineTypes.h',
        'textureDefines':engine/'Source/Runtime/Engine/Classes/Engine/TextureDefines.h',
        'materialInterface':engine/'Source/Runtime/Engine/Public/Materials/MaterialInterface.h',
        'sceneTypes':engine/'Source/Runtime/Engine/Public/SceneTypes.h'}
    tokens={'engineTypes':['MSM_TwoSidedFoliage','BLEND_Masked','SAMPLERTYPE_Color','SAMPLERTYPE_Normal','SAMPLERTYPE_Masks'],
        'textureDefines':['TC_Default','TC_Normalmap','TC_Masks','TSE_sRGB','TSE_None','TA_Wrap','TMGS_FromTextureGroup','None'],
        'materialInterface':['MATUSAGE_InstancedStaticMeshes'],
        'sceneTypes':['MP_BaseColor','MP_Normal','MP_OpacityMask','MP_AmbientOcclusion','MP_Roughness','MP_Metallic','MP_SubsurfaceColor','MP_Specular']}
    for key,path in paths.items():
        text=path.read_text()
        require(all(re.search(r'\b'+re.escape(token)+r'\b',text) for token in tokens[key]),'Installed primary enum declaration changed: '+key)
    frozen=read(previous.PLAN)['baseNativeReport']['path'];base=read(frozen)
    evidence=read(previous.PLAN)['reusedBaseEvidencePlan'];snapshot=read(check_pin(evidence))['consumedSourceSnapshot']['path']
    # Use the exact consumed native producer, not a possibly later shared file.
    material=Path(snapshot).parent/'workspace/scripts/unreal/exterior-materials.py'
    require(material.is_file(),'Frozen successful exterior enum producer missing')
    text=material.read_text();require("replace('MSM', '').replace('MATUSAGE', '') == token" in text,
            'Proven exact prefix-normalized enum algorithm changed')
    return {'primaryHeaders':{key:pin(path) for key,path in paths.items()},'declaredCppTokens':tokens,
        'provenFrozenExteriorMaterials':pin(material),'normalization':'Exact underscore removal; only MSM/MaterialShadingModel and MATUSAGE/MaterialUsage prefix removal; unique full token.',
        'allRequestedMaterialEnumsResolvedBeforeAnyAssetWrites':True,'nativeRuntimeEnumReadbackPending':True}


def lineage():
    previous.validated_supplement();report=FAILURE/'curved-grass-native-report-r2.json'
    require(sha(report)==FAILURE_REPORT_SHA,'Preserved failed R20b report changed');value=read(report)
    require(value['status']=='failed' and value['nativeProcessId']==38515
            and value['error']=='Native enum unavailable/ambiguous: MaterialShadingModel.TWOSIDEDFOLIAGE'
            and value['baseGeometryReadback']=={'meshCount':547,'groupCount':1980,'instanceCount':632026,'allNewVisualsNoCollision':True},
            'R3 repair is not based on the measured enum failure')
    process=FAILURE/'curved-grass-native-r2-process.json';p=read(process);raw=Path(p['processFile']);run=read(raw)
    require(run['code']==255 and run['pid']==38515 and p['reportSha256']==FAILURE_REPORT_SHA
            and sha(raw)==p['processFileSha256'] and sha(p['logFile'])==p['logSha256']
            and p['sourcePinsUnchangedAfterNative'] is True and len(p['sourcePinsBeforeNative'])==70,
            'Preserved failed actual process/source closure changed')
    for file,h in p['sourcePinsBeforeNative'].items():require(sha(file)==h,'Frozen R2 source pin changed')
    return report,process,p


def validated_supplement():
    report,process,p=lineage();s=read(OUTPUT/'curved-grass-repair-supplement.json')
    require(s['schema']=='brezi-original-curved-grass-native-enum-repair-r3' and s['owner']==OWNER and s['status']==STATUS
            and s['previousMeasuredRepair']==pin(previous.OUTPUT/'curved-grass-repair-supplement.json')
            and s['preservedFailureReport']==pin(report) and s['preservedFailureProcess']==pin(process)
            and s['originalPlan']==pin(previous.PLAN) and s['numericalComparisonPolicy']==guard.policy()
            and s['enumSourceEvidence']==headers(),'Unregistered enum-only R3 supplement')
    require(all(s[k] is False for k in ('nativeExecuted','nativeAppearanceAccepted','fullPhotorealismAccepted',
        'performanceAccepted','shippingPackageProduced','originalSourcePayloadsChanged','materialRecipeChanged')),
        'R3 source repair claims native acceptance/changed recipe')
    require(set(s['newSourceFiles'])==set(sources()),'R3 source closure differs')
    for role,path in sources().items():
        row=s['newSourceFiles'][role];require(check_pin(row['live'])==path and check_pin(row['snapshot']).parent==OUTPUT
            and row['live']['sha256']==row['snapshot']['sha256'],'R3 source snapshot differs')
    for path,h in s['inputFiles'].items():require(sha(path)==h,'R3 source input changed: '+path)
    test=read(check_pin(s['sourceGuardTests']));require(test['status']=='passed' and test['testCount']==6
        and test['exitCode']==0 and test['nativeExecuted'] is False,'R3 enum rejection tests failed')
    return s


def build():
    require(not OUTPUT.exists(),'R3 supplement is immutable; choose a new revision for changes')
    report,process,p=lineage();evidence=headers();OUTPUT.mkdir(parents=True)
    start=time.monotonic();test=subprocess.run([sys.executable,'-B',str(sources()['tests'])],cwd=ROOT,capture_output=True,text=True)
    log=OUTPUT/'source-guard-tests.log';log.write_text(test.stdout+test.stderr);match=re.search(r'Ran (\d+) tests? in ',test.stdout+test.stderr)
    tests={'owner':OWNER,'status':'passed' if test.returncode==0 else 'failed','exitCode':test.returncode,
        'testCount':int(match.group(1))if match else None,'elapsedSeconds':time.monotonic()-start,
        'log':pin(log),'nativeExecuted':False,'scope':'Synthetic enum fixtures plus actual original-plan CPU validation; not Unreal enum runtime proof.'}
    write(OUTPUT/'source-guard-tests.json',tests);require(test.returncode==0 and tests['testCount']==6,'R3 CPU repair tests failed; preserve this output')
    owned={}
    for role,path in sources().items():
        snapshot=OUTPUT/('source-'+path.name);shutil.copyfile(path,snapshot);owned[role]={'live':pin(path),'snapshot':pin(snapshot)}
    original=read(read(previous.PLAN)['baseContentInventory']['path']);actual=guard.common.inventory(FAILURE/'Project/BreziTwin/Content')
    require(set(original)<=set(actual) and all(original[k]==actual[k] for k in original),'Failed R20b altered an original native file')
    added=sorted(set(actual)-set(original));require(len(added)==4 and all(p.startswith('Brezi/CurvedGrass20261001R20/Textures/')and p.endswith('.uasset')for p in added),'Failed candidate has unexpected assets')
    write(OUTPUT/'preserved-failure-content-proof.json',{'actualContent':actual,'originalNativeFileCount':3975,
        'originalFilesExact':True,'newFailedCandidateFiles':added,'mapFileExact':original['Brezi/Maps/Brezi.umap'],'nativeOutput':str(FAILURE)})
    inputs=dict(p['sourcePinsBeforeNative']);inputs.update({str(report):sha(report),str(process):sha(process),
        p['processFile']:p['processFileSha256'],p['logFile']:p['logSha256'],str(previous.OUTPUT/'curved-grass-repair-supplement.json'):sha(previous.OUTPUT/'curved-grass-repair-supplement.json')})
    for row in evidence['primaryHeaders'].values():inputs[row['path']]=row['sha256']
    inputs[evidence['provenFrozenExteriorMaterials']['path']]=evidence['provenFrozenExteriorMaterials']['sha256']
    for row in owned.values():
        for entry in row.values():inputs[entry['path']]=entry['sha256']
    write(OUTPUT/'curved-grass-repair-supplement.json',{'schema':'brezi-original-curved-grass-native-enum-repair-r3','owner':OWNER,
        'status':STATUS,'generatedAt':guard.now(),'originalPlan':pin(previous.PLAN),
        'previousMeasuredRepair':pin(previous.OUTPUT/'curved-grass-repair-supplement.json'),
        'numericalComparisonPolicy':guard.policy(),'preservedFailureReport':pin(report),'preservedFailureProcess':pin(process),
        'preservedFailureContentProof':pin(OUTPUT/'preserved-failure-content-proof.json'),'enumSourceEvidence':evidence,
        'newSourceFiles':owned,'inputFiles':inputs,'sourceGuardTests':pin(OUTPUT/'source-guard-tests.json'),
        'nativeExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,
        'shippingPackageProduced':False,'originalSourcePayloadsChanged':False,'materialRecipeChanged':False})
    validated_supplement();print(json.dumps({'supplement':pin(OUTPUT/'curved-grass-repair-supplement.json'),
        'nativeHelper':pin(sources()['nativeHelper']),'materialHelper':pin(sources()['materials']),'tests':tests['testCount'],'nativeExecuted':False}))


if __name__=='__main__':build()
