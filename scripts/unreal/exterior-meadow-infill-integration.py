"""Fresh additive meadow library/plan; no Unreal or existing file mutations."""
import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-meadow-infill-integration.py'


def helper():
    spec = importlib.util.spec_from_file_location('meadow_infill_source_guard', ROOT/'scripts/unreal/exterior-meadow-infill-native.py')
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False); stream.write('\n')


def build(output):
    native = helper(); output = Path(output).resolve()
    native.require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Use a fresh isolated meadow integration directory')
    source_pin = native.fixed(native.STUDY, 'meadow-infill-plan.json', native.PINS)
    source = native.read_pin(source_pin)
    extension_source = native.read_pin(source['geometryManifest'])
    inspected = native.inspect_study(source, extension_source, source['sourceSceneSha256'], source['sourceObjSha256'])
    original = native.read_pin(native.fixed(native.PHOTO, 'geometry-manifest.json', native.PHOTO_PINS))
    original100 = native.module('exterior-lawn-photo-native.py').validated_base_library(original)
    inputs = native.integration_inputs()
    common = {'owner': OWNER, 'generatorSha256': native.sha(__file__), 'inputFiles': inputs,
        'status': native.STATUS, 'sourceInfillPlan': source_pin,
        'sourceInfillGeometry': source['geometryManifest'],
        'sourceOriginal120Library': native.fixed(native.PHOTO, 'geometry-manifest.json', native.PHOTO_PINS)}
    plan = deepcopy(source); plan.update(common, groups=native.native_groups(source['groups']))
    extension = deepcopy(extension_source); extension.update(common)
    full = deepcopy(original); full.update(common, meshes=deepcopy(original['meshes'])+deepcopy(extension_source['meshes']),
        revision='Ordered original120 masters unchanged; six explicit partial-pilot low meadow masters appended')
    native.require(len(full['meshes']) == 126 and sum(len(m['lods']) for m in full['meshes']) == 378,
                   'Meadow126 master378 LOD inventory differs')
    output.mkdir()
    for name in ('material-manifest.json', 'photo-material-manifest.json'):
        (output/name).write_bytes(native.pinned(native.fixed(native.PHOTO, name, native.PHOTO_PINS)).read_bytes())
    # Byte-identical old manifests retain their old owners for strict existing
    # photo/organic guards; no forwarding or owner spoofing is needed.
    (output/'original-photo-geometry-manifest.json').write_bytes(native.pinned(native.fixed(native.PHOTO, 'geometry-manifest.json', native.PHOTO_PINS)).read_bytes())
    old100_pin = original['sourceOriginal100Library']
    (output/'original-shape-geometry-manifest.json').write_bytes(native.pinned(old100_pin).read_bytes())
    write(output/'infill-geometry-manifest.json', extension)
    extension_pin = native.pin(output/'infill-geometry-manifest.json')
    plan['infillGeometryManifest'] = full['infillGeometryManifest'] = extension_pin
    full['validatedOriginal120Subset'] = native.pin(output/'original-photo-geometry-manifest.json')
    full['validatedOriginal100Subset'] = native.pin(output/'original-shape-geometry-manifest.json')
    write(output/'geometry-manifest.json', full)
    write(output/'meadow-infill-plan.json', plan)
    plan_pin = native.pin(output/'meadow-infill-plan.json')
    asset = {**common, 'schemaVersion': 1, 'geometryManifest': native.pin(output/'geometry-manifest.json'),
        'infillGeometryManifest': extension_pin, 'plan': plan_pin,
        'materialManifest': native.pin(output/'material-manifest.json'),
        'photoMaterialManifest': native.pin(output/'photo-material-manifest.json'),
        'preservation': source['preservation'],
        'integration': {'oldMasters': 120, 'newMasters': 6, 'totalMasters': 126, 'lods': 378,
            'newGroups': 101, 'newInstances': 33483, 'newTriangleBudgets': inspected['audit']['allLodTriangles'],
            'original24RecipesByteExact': True, 'existing42NativeMaterials': True, 'existing74NativeTextures': True,
            'noNewRecipes': True, 'geometryCollision': 'NoCollision', 'canEverAffectNavigation': False,
            'densityScaling': True, 'cullDistancesCm': [3200, 4000], 'lodScreens': native.LOD_SCREENS},
        'coverageMeasurement': source['coverageMeasurement'], 'uniformFullGroundCoverClaim': False,
        'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False}
    write(output/'asset-manifest.json', asset)
    validation = native.validated_infill(plan, extension, full, source['sourceSceneSha256'], source['sourceObjSha256'])
    write(output/'integration-validation.json', {'owner': OWNER, 'helper': native.pin(ROOT/native.OWNER),
        'plan': plan_pin, 'geometryManifest': native.pin(output/'geometry-manifest.json'),
        'audit': validation['audit'], 'nativeJobsRun': 0, 'nativeAppearanceAccepted': False, 'performanceAccepted': False})
    for path, expected in inputs.items(): native.pinned({'path': path, 'sha256': expected})
    native.require(native.same(original100, native.validated_libraries(full)['original100']), 'Meadow original100 subset changed')
    return {'output': str(output), 'plan': plan_pin, 'geometryManifest': native.pin(output/'geometry-manifest.json'),
        'infillGeometryManifest': extension_pin, 'audit': validation['audit'], 'nativeJobsRun': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', required=True)
    print(json.dumps(build(**vars(parser.parse_args())), ensure_ascii=False))
