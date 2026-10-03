"""Exclusive CPU material readiness on the selected immutable R36 source.

Reads original images, records truthful decoder limits and runs owned mocked
API fixtures. Creates no pixels/assets/project changes and never invokes UE.
"""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
sys.dont_write_bytecode = True
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-periwinkle-material-readiness-r36.py'
OUTPUT = ROOT/'output/unreal/exterior-garden-periwinkle-20261002-r36-material-readiness'
FILE = ROOT/'scripts/unreal/exterior-garden-periwinkle-materials-r36.py'
TEST = ROOT/'scripts/unreal/test_exterior_garden_periwinkle_materials_r36.py'
SOURCE_PLAN = ROOT/'output/unreal/exterior-garden-periwinkle-20261002-r36-source-study/periwinkle-source-plan.json'


def pin(path):
    p = Path(path).resolve()
    return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}


def require(ok,message):
    if not ok:raise RuntimeError(message)


def write(path,value):
    with path.open('x') as f:
        json.dump(value,f,indent=2,allow_nan=False)
        f.write('\n')


def main():
    require(not OUTPUT.exists(), 'One fresh material readiness output required')
    spec=importlib.util.spec_from_file_location('r36_readiness_own_material',FILE)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    recipe=json.loads(m.RECIPE.read_text());m.validate_recipe(recipe)
    require(pin(SOURCE_PLAN)['sha256']=='93b4bc17203f10b5c14acd036dd942f8d2bf0b99ec1744e6638e7a29502a8b96', 'Final selected geometry/material source changed')
    primary=Path('/Users/Shared/Epic Games/UE_5.8/Engine')
    input_paths=[FILE,TEST,Path(__file__),SOURCE_PLAN,m.RECIPE,m.DELEGATE,
        Path(recipe['sourceGltf']['path']),Path(recipe['originalDownloadReceipt']['path']),Path(recipe['originalPbrPngReceipt']['path']),
        m.REFERENCE/'api-files-original.json',m.REFERENCE/'periwinkle_plant.bin',
        *(Path(v['path'])for v in recipe['maps'].values()),
        primary/'Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h',
        primary/'Source/Runtime/Engine/Classes/Engine/EngineTypes.h',
        primary/'Source/Runtime/Engine/Classes/Engine/Texture.h',
        primary/'Shaders/Private/ShadingModels.ush']
    inputs=[pin(p)for p in input_paths]
    map_records=[]
    with Image.open(recipe['maps']['opacity']['path']) as im:
        opacity=np.asarray(im)
        require(im.mode=='I;16' and opacity.dtype==np.uint16 and im.size==(2048,2048), 'Actual normalized16-bit opacity source required')
        support=opacity>=32768
    for role,source in recipe['maps'].items():
        with Image.open(source['path']) as im:
            array=np.asarray(im)
            require(im.size==(2048,2048) and im.mode==('I;16' if role in ('opacity','roughness') else 'RGBA'), 'Original map dimensions/mode differ')
            color=im.info.get('oiio:ColorSpace')
            profile=im.info.get('icc_profile')
            map_records.append({'role':role,'source':source,'originalHeader':m.png_header(source['path']),
                'pillowDecodedMode':im.mode,'pillowDecodedArrayType':str(array.dtype),
                'pillowDecodedMinimum':int(array.min()),'pillowDecodedMaximum':int(array.max()),
                'meanOnSourceOpacityHalfSupport_PillowDecoded':np.mean(array[support],axis=0).tolist(),
                'sourceGamma':im.info.get('gamma'),'oiioColorSpace':color if isinstance(color,(str,int,float,type(None))) else repr(color),
                'iccProfileSha256':hashlib.sha256(profile).hexdigest() if profile else None,
                'color16BitReducedTo8ByThisPillowDecoder':role in ('albedo','normalGl','translucency'),
                'sourcePixelPrecisionFromOriginalPngHeader':16,'nativePixelPrecisionOrPixelsDecoded':False,
                'sourcePixelsEdited':False})
    OUTPUT.mkdir()
    snapshots=OUTPUT/'owned-source';snapshots.mkdir()
    for p in [FILE,TEST,Path(__file__)]:shutil.copyfile(p,snapshots/p.name)
    command=[str(Path(sys.executable).resolve()),'-B',str(TEST)]
    started=datetime.now(timezone.utc).isoformat();clock=time.monotonic()
    test=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    elapsed=time.monotonic()-clock
    with (OUTPUT/'cpu-fixtures.log').open('x') as stream:stream.write(test.stdout)
    process={'owner':OWNER,'command':command,'workingDirectory':str(ROOT),'startedAt':started,
        'elapsedSeconds':elapsed,'exitCode':test.returncode,'rawLog':pin(OUTPUT/'cpu-fixtures.log'),
        'evidenceScope':'Actual CPU execution with explicit fake UE API/assets only; no native import/compile/save/geometry/render evidence.',
        'unrealExecuted':False,'sourcePixelsEdited':False}
    write(OUTPUT/'cpu-fixture-process.json',process)
    require(test.returncode==0 and re.search(r'Ran 11 tests in ',test.stdout) and test.stdout.rstrip().endswith('OK'), 'Final11CPU material fixtures failed; preserve output')
    require(all(pin(p['path'])==p for p in inputs), 'Original material inputs changed during readiness')
    inspection={'schema':'brezi-original-r36-periwinkle-five-map-inspection-source-only','owner':OWNER,
        'images':map_records,'opacityNormalizedHalfSupportPixels':int(support.sum()),'sourcePixelCount':int(support.size),
        'opacityNormalizedHalfSupportFraction':float(support.mean()),
        'supportInterpretation':'Atlas support only, not projected visible leaf coverage or native alpha.',
        'normalDataOverride':'Original GL RGBA PNG contains color metadata; data/normal sampling explicitly disables sRGB and uses TSE_NONE, with UE green flip.',
        'roughOpacityDataOverride':'Original grayscale16-bit normalized R is linear; no source gamma correction is proposed.',
        'sourcePhotometricCalibrationMeasured':False,'sourcePixelsEdited':False,'nativeTexturesCreated':False}
    write(OUTPUT/'original-map-inspection.json',inspection)
    readiness={'schema':'brezi-original-r36-periwinkle-material-source-readiness','owner':OWNER,
        'status':'source-five-original-maps-API-contract-and11CPU-mutation-fixtures-ready-native-pending',
        'recordedAtUtc':datetime.now(timezone.utc).isoformat(),'sourceRecipe':pin(m.RECIPE),'selectedSourcePlan':pin(SOURCE_PLAN),
        'materialHelper':pin(FILE),'fixtureSource':pin(TEST),'producer':pin(__file__),
        'ownedSourceSnapshots':{p.name:pin(snapshots/p.name)for p in [FILE,TEST,Path(__file__)]},
        'inputPinsBefore':inputs,'inputPinsAfter':inputs,'allInputPinsUnchanged':True,
        'python':pin(sys.executable),'pythonVersion':sys.version,'numpyVersion':np.__version__,
        'pillowVersion':Image.__version__,'imageInspection':pin(OUTPUT/'original-map-inspection.json'),
        'actualCpuFixtureProcess':pin(OUTPUT/'cpu-fixture-process.json'),'tests':{'passed':11,'failed':0,'exitCode':0,'nativeApiMocked':True},
        'materialApi':{'preflight':'preflight_enums(u)','sourceValidation':'validate_recipe(recipe)',
            'build':'build_materials(u,recipe,graph_snapshot)->(material,report)',
            'savedReadback':'verify_materials(u,report,recipe,graph_snapshot)->material'},
        'prefix':m.PREFIX,'key':m.KEY,'newPackageAssets':m.package_assets(recipe),
        'expectedMaterialGraphs':1,'expectedTextureObjects':5,'expectedMaterialPackages':6,
        'expectedGraphExpressions':10,'sourceOriginalBlendMode':'BLEND','proposedEngineBlendMode':'MASKED',
        'explicitOpacity':'unchanged original16-bit opacity normalized R -> OpacityMask cutoff0.5',
        'normal':'unchanged original GLnormal RGB, linear normal sampler, UE green flip',
        'roughness':'unchanged original16-bit roughness normalized R, linear mask sampler',
        'subsurfaceColor':'original translucency sRGB RGB ×0.08 artistic UE calibration',
        'physicalOpticalCalibrationAccepted':False,'sourceOpticalModelExactlyReproduced':False,
        'sourceColor0UnityFactorPreservedByIdentityColor':True,'sourceColor1NativeMappingOrWindClaimed':False,
        'sourcePixelsEdited':False,'nativeMaterialApplied':False,'nativeImportedPixelsDecoded':False,
        'nativeGpuPixelFormatReadbackAvailable':False,'nativeNormalTangentReadbackAvailable':False,
        'materialPackagesIndependentlyUnloaded':False,'nativeBaseBound':None,'nativeAppearanceAccepted':False,
        'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False}
    write(OUTPUT/'material-source-readiness.json',readiness)
    print(json.dumps({'output':str(OUTPUT),'readiness':pin(OUTPUT/'material-source-readiness.json'),
        'helper':pin(FILE),'tests':11,'exitCode':test.returncode,'nativeExecuted':False}))


if __name__=='__main__':main()
