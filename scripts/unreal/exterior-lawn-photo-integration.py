"""Compose additive photo lawn masters and an exact placement-only adapter.

The merged material manifest remains the original24 byte-for-byte. The single
new photographic recipe is separate, to append after the current41 graphs.
This command is source-only and creates a fresh output; it never opens Unreal.
"""
import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-lawn-photo-integration.py'


def helper():
    path = ROOT/'scripts/unreal/exterior-lawn-photo-native.py'
    spec = importlib.util.spec_from_file_location('photo_lawn_source_guard', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def build(study, output):
    native = helper()
    study = Path(study).resolve(); output = Path(output).resolve()
    native.require(study.is_relative_to(ROOT/'output/unreal') and study.is_dir(), 'Photo study path escaped or is missing')
    native.require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Use a fresh photo integration output')
    proposal_pin = native.pin(study/'lawn-photographic-proposal.json')
    proposal = native.read_pin(proposal_pin)
    photo = native.read_pin(proposal['geometryManifest'])
    inspected = native.inspect_study(proposal, photo, proposal['sourceSceneSha256'], proposal['sourceObjSha256'])
    inputs = native.integration_inputs(proposal, proposal_pin)
    common = {'owner': OWNER, 'generatorSha256': native.sha(__file__), 'inputFiles': inputs,
              'status': native.STATUS, 'sourcePhotographicStudy': proposal_pin,
              'sourceOriginal100Library': native.fixed(native.BASE, 'geometry-manifest.json', native.BASE_PINS),
              'sourcePlacementPlan': native.fixed(native.DONOR, 'lawn-natural-plan.json', native.DONOR_PINS)}
    extension = deepcopy(photo)
    extension.update(common)
    plan = deepcopy(inspected['originalPlan'])
    plan.update(common, kind='authored-photographic-lawn-replacement',
        audit=native.photo_audit(inspected, proposal), groups=native.transformed_groups(plan['groups']),
        photographicAlphaCoverage=proposal['photographicAlphaCoverage'], geometryProof=photo['geometryProof'])
    for row in plan['lawnPlacements']:
        row['meshId'] = native.MAPPING[row['meshId']]
    full = deepcopy(inspected['originalLibrary'])
    full.update(common, meshes=full['meshes']+deepcopy(extension['meshes']),
        sourceMaterialManifest=native.fixed(native.BASE, 'material-manifest.json', native.BASE_PINS),
        revision='Original100 masters preserved;20 separate photographically mapped managed-lawn masters added')
    native.require(len(full['meshes']) == 120 and sum(len(m['lods']) for m in full['meshes']) == 360,
                   'Photo additive master census differs')
    # All input proofs have passed before the first output write.
    output.mkdir()
    material_path = output/'material-manifest.json'
    material_path.write_bytes(native.pinned(native.fixed(native.BASE, 'material-manifest.json', native.BASE_PINS)).read_bytes())
    write(output/'photo-material-manifest.json', {native.MATERIAL: inspected['recipe']})
    recipe_pin = native.pin(output/'photo-material-manifest.json')
    plan['photoMaterialManifest'] = full['photoMaterialManifest'] = recipe_pin
    write(output/'photo-geometry-manifest.json', extension)
    extension_pin = native.pin(output/'photo-geometry-manifest.json')
    plan['geometryManifest'] = full['photoExtensionManifest'] = extension_pin
    write(output/'geometry-manifest.json', full)
    write(output/'lawn-natural-plan.json', plan)
    plan_pin = native.pin(output/'lawn-natural-plan.json')
    asset = {**common, 'schema': 1, 'schemaVersion': 1,
        'sourceOriginalAssetManifest': native.fixed(native.BASE, 'asset-manifest.json', native.BASE_PINS),
        'sourceMaterialManifest': native.fixed(native.BASE, 'material-manifest.json', native.BASE_PINS),
        'photoMaterialManifest': recipe_pin, 'photoExtensionManifest': extension_pin, 'plan': plan_pin,
        'replacementScope': {'original100MasterRecordsPreserved': True, 'additionalPhotoMasters': 20,
            'activeLawnGroupsRebound': 40, 'activeLawnInstancesUnchanged': 102011,
            'originalGroundCollisionTransformsPreserved': True, 'original24MaterialRecipesByteExact': True},
        'materialIntegration': {'appendAfterExistingTransitionMaterial': True, 'priorNativeGraphs': 41,
            'newPhotographicMaterialKey': native.MATERIAL, 'expectedNativeGraphs': 42, 'expectedNativeTextures': 74,
            'existing41GraphsMustRemainExact': True, 'usesSeparatePhotoMaterialManifest': True},
        'artistInterpretation': True, 'surveyedBotany': False, 'nativeAppearanceAccepted': False,
        'fullPhotorealismAccepted': False, 'performanceAccepted': False}
    write(output/'asset-manifest.json', asset)
    bundle = {**common, 'schemaVersion': 1, 'geometryManifest': extension_pin,
        'mergedGeometryManifest': native.pin(output/'geometry-manifest.json'), 'plan': plan_pin,
        'materialManifest': native.pin(material_path), 'photoMaterialManifest': recipe_pin,
        'assetManifest': native.pin(output/'asset-manifest.json'),
        'photographicAlphaCoverage': proposal['photographicAlphaCoverage'], 'geometryProof': photo['geometryProof'],
        'audit': plan['audit'], 'nativeAppearanceAccepted': False, 'performanceAccepted': False}
    write(output/'lawn-natural-manifest.json', bundle)
    old_views = native.DONOR/'lawn-qa-views.json'
    cameras = json.loads(old_views.read_text())
    cameras.update(owner=OWNER, generatorSha256=native.sha(__file__), plan=plan_pin,
                   priorCameraManifest=native.pin(old_views))
    write(output/'lawn-qa-views.json', cameras)
    validation = native.validate_photo(plan, extension, full, plan['sourceSceneSha256'], plan['sourceObjSha256'])
    for path, value in inputs.items():
        native.pinned({'path': path, 'sha256': value})
    return {'output': str(output), 'plan': plan_pin, 'geometryManifest': native.pin(output/'geometry-manifest.json'),
            'photoGeometryManifest': extension_pin, 'materialManifest': native.pin(material_path),
            'photoMaterialManifest': recipe_pin, 'masters': 120, 'lods': 360,
            'activeLawnInstances': 102011, 'activeLawnGroups': 40, 'validation': validation['audit'],
            'nativeAppearanceAccepted': False, 'performanceAccepted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', required=True); parser.add_argument('--output', required=True)
    print(json.dumps(build(**vars(parser.parse_args())), ensure_ascii=False))
