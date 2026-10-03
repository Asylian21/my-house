"""Compose exact original126 plus nine selected fullness masters; no Unreal."""
from copy import deepcopy
import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-canopy-fullness-integration.py'


def helper():
    spec = importlib.util.spec_from_file_location('canopy_fullness_source_guard',ROOT/'scripts/unreal/exterior-canopy-fullness-native.py')
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result


def write(path,value):
    with Path(path).open('x') as stream: json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False); stream.write('\n')


def build(output):
    native = helper(); output = Path(output).resolve()
    native.require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(),'Use a fresh isolated fullness integration directory')
    selected = native.approved(); plan = selected['canopy-plan.json']; extension = selected['geometry-manifest.json']
    original = native.read_pin(native.fixed(native.BASE,'geometry-manifest.json',native.BASE_PINS)); inputs = native.integration_inputs()
    full = deepcopy(original); full.update(owner=OWNER,generatorSha256=native.sha(__file__),inputFiles=inputs,status=native.STATUS,
        meshes=deepcopy(original['meshes'])+deepcopy(extension['meshes']),
        revision='Exact ordered original126 retained; nine selected fuller connected crowns appended',
        sourceFullnessPlan=native.fixed(native.STUDY,'canopy-plan.json',native.STUDY_PINS),
        fullnessGeometryManifest=native.fixed(native.STUDY,'geometry-manifest.json',native.STUDY_PINS),
        sourceOriginal126Library=native.fixed(native.BASE,'geometry-manifest.json',native.BASE_PINS))
    native.require(len(full['meshes']) == 135 and sum(len(row['lods']) for row in full['meshes']) == 405,'Fullness135/405 inventory differs')
    # The unchanged truthful typed study plan is the next BREZI_EXTERIOR_CANOPY;
    # the library composer does not forward or impersonate a growth owner.
    output.mkdir()
    for name in ('material-manifest.json','photo-material-manifest.json'):
        (output/name).write_bytes(native.pinned(native.fixed(native.BASE,name,native.BASE_PINS)).read_bytes())
    (output/'original-meadow-geometry-manifest.json').write_bytes(native.pinned(native.fixed(native.BASE,'geometry-manifest.json',native.BASE_PINS)).read_bytes())
    full['validatedOriginal126Subset'] = native.pin(output/'original-meadow-geometry-manifest.json')
    write(output/'geometry-manifest.json',full)
    context = native.read_pin(plan['sourceContext'])
    validation = native.validated_replacements(plan,extension,context,full,plan['sourceSceneSha256'],plan['sourceObjSha256'])
    asset = {'schemaVersion':1,'owner':OWNER,'generatorSha256':native.sha(__file__),'inputFiles':inputs,
        'geometryManifest':native.pin(output/'geometry-manifest.json'),'plan':full['sourceFullnessPlan'],
        'fullnessGeometryManifest':full['fullnessGeometryManifest'],'materialManifest':native.pin(output/'material-manifest.json'),
        'photoMaterialManifest':full['photoMaterialManifest'],'preservedOriginal126Subset':full['validatedOriginal126Subset'],
        'integration':{'oldMasters':126,'newMasters':9,'totalMasters':135,'lods':405,'original24RecipesByteExact':True,
            'existing42NativeMaterials':True,'existing74NativeTextures':True,'noNewRecipes':True,'original78RootsYawAndScalesPreserved':True,
            'nonGroveRegionalRowsPreserved':1022,'allOriginalMeadowAndGardenAndLawnSourcesPreserved':True},
        'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False}
    write(output/'asset-manifest.json',asset)
    write(output/'integration-validation.json',{'owner':OWNER,'helper':native.pin(ROOT/native.OWNER),
        'plan':full['sourceFullnessPlan'],'geometryManifest':asset['geometryManifest'],'audit':validation['audit'],
        'nativeJobsRun':0,'nativeAppearanceAccepted':False,'performanceAccepted':False})
    for path,expected in inputs.items(): native.pinned({'path':path,'sha256':expected})
    return {'output':str(output),'plan':full['sourceFullnessPlan'],'geometryManifest':asset['geometryManifest'],
        'audit':validation['audit'],'nativeJobsRun':0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',required=True)
    print(json.dumps(build(**vars(parser.parse_args())),ensure_ascii=False))
