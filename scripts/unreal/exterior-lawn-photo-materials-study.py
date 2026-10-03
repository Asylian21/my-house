"""One isolated photographic turf material; no shared source or native writes.

The proposed hook appends AFTER the forty-one finalized R12c materials. Its
recipe is the exact existing PH grass recipe, including its inherited response.
Only the new key aliases the immutable padded-albedo provenance entry. The CLI
replays frozen Writer/transition code in the existing source-only Unreal shim;
it never compiles a native shader or establishes rendered appearance/coverage.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-lawn-photo-materials-study.py'
KEY = 'lawn_photographic_blade'
PROVIDER_KEY = 'ph_grass_medium_02'
REPORT = ROOT / 'output/unreal/exterior-20261001-r12c/exterior-import-report.json'
REPORT_SHA = '3a3824b05aff496a7df45cc033b88a64d3c3de73cf9c0c747bd88a21427904ee'
VEGETATION = ROOT / 'output/unreal/exterior-assets-shape-20261001-r1/material-manifest.json'
VEGETATION_SHA = '42dbaddc637c479d30482b1524217d8e9c288ff89de8f64d9f38396a1e63fbbb'
FROZEN = ROOT / 'output/unreal/exterior-20261001-r12c/source-freeze/scripts/unreal'
BASE_SHA = 'b661d9d6a05684b6f72afc61b16826b739f80cead3c5314f891a21c9329be720'
SHIM_SHA = 'bcd784a5e7c6ee9956a87a97185abd19a064e562f3b18b4748fe33f46d33bd9e'
TRANSITION_SHA = '662614c68dd958fb1f54982691f26b434c1f0af625c5cae5068cb9a247ef6cdd'
ENGINE_DITHER = Path('/Users/Shared/Epic Games/UE_5.8/Engine/Content/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.uasset')
ENGINE_DITHER_SHA = 'e92577ec6d1ede4570eb7c8520ac63e82890cb7335cc9e389503406d145b72a7'
MAP_SHAS = {
    'albedo': '232ced222dbfef15cec3faaa39d86a6227e4ff2f9b7eddc19119693d66ddc0fe',
    'normal': 'de5d3143fb993cbe86123ae28144fe9936ecc93ec1ebc9af7034da63abc2dbfc',
    'roughness': '4d42a3ee935c1aaeecfacd1d286a25075293990686ed949f0712d9ae039d0e91',
    'alpha': 'c96abf8da86aa750ff6425b8ded78aa98cf61858834e3557ad2dcc5348359337'
}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def pin(path, expected=None):
    path = Path(path).resolve()
    require((path.is_relative_to(ROOT) or (path == ENGINE_DITHER and expected == ENGINE_DITHER_SHA))
            and path.is_file(), 'Missing project or exact inherited engine input: ' + str(path))
    value = sha(path)
    require(expected is None or value == expected, 'Exact input drift: ' + str(path))
    return {'path': str(path), 'sha256': value}


def baseline():
    pin(REPORT, REPORT_SHA)
    pin(VEGETATION, VEGETATION_SHA)
    result = read(REPORT)
    require(result['status'] == 'exterior-import-validated' and result['savedReloaded'] is True,
            'Baseline must be the actual saved/reloaded R12c import')
    materials = result['materials']
    require(len(materials['materials']) == 41 and len(materials['textures']) == 74,
            'Baseline material/texture counts differ')
    original = read(VEGETATION)[PROVIDER_KEY]
    require(original == materials['materials'][PROVIDER_KEY]['recipe'], 'Provider recipe differs from saved baseline')
    require(set(original['maps']) == set(MAP_SHAS)
            and {k: v['sha256'] for k, v in original['maps'].items()} == MAP_SHAS,
            'Photographic map identities differ')
    for spec in original['maps'].values():
        pin(spec['path'], spec['sha256'])
    return materials, original


def validate_recipe_alias(key, recipe, materials_api):
    """Only this exact new-key recipe delegates the old, untouched proof entry."""
    _, original = baseline()
    require(key == KEY and recipe == original, 'Photo alias requires the exact inherited provider recipe')
    require(materials_api.source_encoding_proof(recipe, PROVIDER_KEY) is None,
            'No new photographic source-encoding correction is authorized')
    # The derived report is indexed by the original provider key. No receipt,
    # image, padded atlas or alpha is rewritten to manufacture a new entry.
    return materials_api.derivation_inputs(PROVIDER_KEY, recipe)


def prepared_recipe(materials_api):
    _, original = baseline()
    validated = materials_api.prepare_manifest({PROVIDER_KEY: copy.deepcopy(original)})['materials'][PROVIDER_KEY]
    require(validated == original, 'Provider validation changed its recipe')
    validate_recipe_alias(KEY, validated, materials_api)
    return copy.deepcopy(validated)


def validate_photo_manifest(value, materials_api):
    require(isinstance(value, dict) and set(value) == {KEY}, 'Photo sidecar must contain exactly the new material key')
    recipe = prepared_recipe(materials_api)
    require(value[KEY] == recipe, 'Photo sidecar changed the inherited provider recipe')
    return recipe


def prepare(photo_manifest, materials_api):
    source = pin(photo_manifest)
    recipe = validate_photo_manifest(read(source['path']), materials_api)
    inputs = validate_recipe_alias(KEY, recipe, materials_api)
    inputs.update({str(REPORT): REPORT_SHA, str(VEGETATION): VEGETATION_SHA,
                   source['path']: source['sha256'], str(Path(__file__).resolve()): sha(__file__)})
    inputs.update({v['path']: v['sha256'] for v in recipe['maps'].values()})
    return {'materialKey': KEY, 'recipe': recipe, 'sourceManifest': source, 'inputFiles': inputs,
            'pipelineFiles': {str(Path(__file__).resolve()): sha(__file__)}}


def append_photographic_material(writer, materials, records, materials_api, prepared):
    """Proposed opt-in hook, after transition append; preserves all prior graphs."""
    native, original = baseline()
    require(set(materials) == set(records) == set(native['materials'])
            and len(materials) == 41 and len(writer.texture_report) == 74,
            'Photo hook requires the finalized forty-one-material baseline')
    require(KEY not in records and writer.prefix == native['prefix'], 'Photo namespace/key differs')
    before_records = copy.deepcopy(records)
    before_textures = copy.deepcopy(writer.texture_report)
    for key in records:
        require(records[key]['recipe'] == native['materials'][key]['recipe'], 'An inherited recipe changed: ' + key)
        require(materials_api.digest(materials_api.graph_snapshot(writer.u, materials[key])) == records[key]['graphSha256'],
                'An incoming material graph differs: ' + key)
    require(prepared == prepare(prepared['sourceManifest']['path'], materials_api), 'Prepared photo sidecar/input pins differ')
    recipe = copy.deepcopy(prepared['recipe'])
    inputs = copy.deepcopy(prepared['inputFiles'])
    material, entry = writer.create(KEY, recipe)
    # Exact same graph construction, map identities and texture cache entries
    # as the provider shader. COLOR0 is intentionally unused in this baseline.
    require(entry['graph'] == records[PROVIDER_KEY]['graph'], 'Photo graph is not the exact provider graph')
    require(writer.texture_report == before_textures, 'Photo append imported or changed a texture')
    materials[KEY] = material
    records[KEY] = entry
    require({k: v for k, v in records.items() if k != KEY} == before_records,
            'Photo append changed an inherited report')
    for key in before_records:
        require(materials_api.digest(materials_api.graph_snapshot(writer.u, materials[key])) == before_records[key]['graphSha256'],
                'Photo append changed an inherited graph: ' + key)
    require(len(materials) == len(records) == 42 and len(writer.texture_report) == 74,
            'Photo append budget differs')
    return {'status': 'appended-photographic-lawn-material-awaiting-native-reload',
            'owner': OWNER, 'sourceSha256': sha(__file__), 'materialKey': KEY,
            'sourceManifest': copy.deepcopy(prepared['sourceManifest']), 'providerRecipeAlias': PROVIDER_KEY,
            'newGraphSha256': entry['graphSha256'], 'providerGraphSha256': records[PROVIDER_KEY]['graphSha256'],
            'newGraphEqualsProviderGraph': True, 'COLOR0Used': False, 'uvChannel': 0,
            'regeneratedUv0TangentsRequired': True, 'priorMaterials': 41,
            'finalMaterials': 42, 'textures': 74, 'additionalTextures': 0,
            'allPrior41ReportsAndGraphsUnchanged': True, 'sourceEncodingOverridesAdded': 0,
            'inputFiles': inputs, 'pipelineFiles': {str(Path(__file__).resolve()): sha(__file__)},
            'nativeVisualAccepted': False, 'performanceAccepted': False}


def load_frozen(path, expected, name):
    pin(path, expected)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rebase_frozen_paths(module):
    """A copied source retains __file__; only its explicit project paths move."""
    old = module.ROOT
    for key, value in list(vars(module).items()):
        if isinstance(value, Path) and value.is_relative_to(old):
            setattr(module, key, ROOT / value.relative_to(old))
    require(module.ROOT == ROOT, 'Frozen project paths were not explicitly rebased')


ENUM_VALUES = {
    'BLEND_MASKED': 'MASKED', 'BLEND_OPAQUE': 'OPAQUE', 'MSM_TWO_SIDED_FOLIAGE': 'FOLIAGE',
    'MSM_DEFAULT_LIT': 'DEFAULT_LIT', 'SAMPLERTYPE_COLOR': 'COLOR', 'SAMPLERTYPE_NORMAL': 'NORMAL',
    'SAMPLERTYPE_MASKS': 'MASKS', 'TMVM_NONE': 'DEFAULT',
    'CMOT_FLOAT1': 'FLOAT1', 'CMOT_FLOAT2': 'FLOAT2', 'CMOT_FLOAT3': 'FLOAT3', 'CMOT_FLOAT4': 'FLOAT4'
}


def comparable_graph(value):
    """Only native float32 storage, enum display and disconnected UI pins differ."""
    if isinstance(value, float):
        return struct.unpack('<f', struct.pack('<f', value))[0]
    if isinstance(value, str):
        if value.startswith('/Game/'):
            return value.split('.', 1)[0]
        match = re.fullmatch(r'<\w+\.(\w+): \d+>', value)
        return ENUM_VALUES.get(match[1], value) if match else value
    if isinstance(value, list):
        return [comparable_graph(v) for v in value]
    if isinstance(value, dict):
        return {k: comparable_graph([r for r in v if r[1] is not None] if k == 'inputs' else v)
                for k, v in value.items()}
    return value


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def study(out):
    out = Path(out).resolve()
    require(out.is_relative_to(ROOT / 'output/unreal') and not out.exists(), 'Use a fresh study output')
    native, original = baseline()
    before = {str(Path(__file__).resolve()): sha(__file__), str(REPORT): REPORT_SHA, str(VEGETATION): VEGETATION_SHA,
              str(FROZEN / 'exterior-materials.py'): BASE_SHA,
              str(FROZEN / 'test_exterior_materials.py'): SHIM_SHA,
              str(FROZEN / 'exterior-neighborhood-transition-materials.py'): TRANSITION_SHA}
    before.update(native['inputFiles'])
    for path, expected in before.items():
        pin(path, expected)
    out.mkdir(parents=True)
    write(out / 'material-manifest.json', {KEY: original})
    fixture = load_frozen(FROZEN / 'test_exterior_materials.py', SHIM_SHA, 'lawn_photo_source_fixture')
    api = fixture.M
    require(sha(api.__file__) == BASE_SHA, 'Shim did not load the exact frozen material writer')
    rebase_frozen_paths(api)
    transition = load_frozen(FROZEN / 'exterior-neighborhood-transition-materials.py', TRANSITION_SHA, 'lawn_photo_frozen_transition')
    rebase_frozen_paths(transition)
    unreal = fixture.fake_unreal()
    writer = api.Writer(unreal, native['prefix'], unreal.engine_function)
    materials, records = {}, {}
    for key, entry in native['materials'].items():
        if key != transition.KEY:
            materials[key], records[key] = writer.create(key, copy.deepcopy(entry['recipe']))
    prepared = {'plan': copy.deepcopy(native['neighborhoodTransition']['sourcePlan']),
                'conditionTexture': copy.deepcopy(read(native['neighborhoodTransition']['sourcePlan']['path'])['conditionTexture']),
                'conditionValidation': copy.deepcopy(native['neighborhoodTransition']['conditionValidation']),
                'originalRecipes': {key: copy.deepcopy(records[key]['recipe']) for key in ('context_meadow', 'context_fallow')}}
    transition.append_transition(writer, materials, records, prepared,
                                 {k: getattr(api, k) for k in ('digest', 'graph_snapshot', 'TAG')})
    inherited = copy.deepcopy(records)
    inherited_textures = copy.deepcopy(writer.texture_report)
    prepared_photo = prepare(out / 'material-manifest.json', api)
    receipt = append_photographic_material(writer, materials, records, api, prepared_photo)
    new_graph = records[KEY]['graph']
    require(comparable_graph(new_graph) == comparable_graph(native['materials'][PROVIDER_KEY]['graph']),
            'Proposed shader differs from the actual native provider graph')
    require(all(key not in new_graph['roots'] or new_graph['roots'][key] is None
                for key in ('WORLD_POSITION_OFFSET', 'EMISSIVE_COLOR')), 'Photo shader adds displacement or emissive')
    require(not any(node['class'] == 'MaterialExpressionVertexColor' for node in new_graph['nodes']),
            'Photo baseline silently changed the vertex-colour response')
    failures = []
    for field, value in [('uvScale', 2), ('normalConvention', 'OpenGL'), ('tint', [.9, 1, 1]),
                         ('subsurfaceScale', .2), ('opacityMaskClipValue', .2), ('sourceEncodingOverride', 'sRGB')]:
        bad = copy.deepcopy(original); bad[field] = value
        try:
            validate_recipe_alias(KEY, bad, api)
        except RuntimeError:
            failures.append(field)
        else:
            raise RuntimeError('Changed recipe was accepted: ' + field)
    for label, value in [('oldProviderKey', {PROVIDER_KEY: original}),
                         ('extraMaterial', {KEY: original, 'unexpected_material': original}),
                         ('changedPhotoBody', {KEY: {**original, 'uvScale': 2}})]:
        try:
            validate_photo_manifest(value, api)
        except RuntimeError:
            failures.append(label)
        else:
            raise RuntimeError('Changed sidecar was accepted: ' + label)
    for path, expected in before.items():
        pin(path, expected)
    write(out / 'source-graphs.json', {'prior41': inherited, 'newMaterial': records[KEY]})
    write(out / 'source-textures.json', inherited_textures)
    contract = {'schemaVersion': 1, 'owner': OWNER, 'materialKey': KEY,
                'status': 'SOURCE_ONLY_PHOTOGRAPHIC_LAWN_MATERIAL_NATIVE_PENDING',
                'sourceSha256': sha(__file__), 'baselineImport': pin(REPORT, REPORT_SHA),
                'providerKey': PROVIDER_KEY, 'recipe': original, 'appendOrdering': 'after finalized transition41, before final material report',
                'api': {'prepare': 'prepare(photo_manifest_path, materials_api)',
                        'append': 'append_photographic_material(writer, materials, records, materials_api, prepared)',
                        'sidecar': pin(out / 'material-manifest.json')},
                'derivationAlias': {'newKey': KEY, 'existingReceiptKey': PROVIDER_KEY,
                    'guard': 'Exact inherited recipe, four source SHA identities and original derivation proof; no receipt rewrite'},
                'sourceGraphNodes': len(new_graph['nodes']), 'budget': receipt,
                'textureInterpretation': {'UV': 'TEXCOORD_0 scale1; directV; no world triplanar mapping',
                    'normal': 'DirectX normal sample; tangent-space normal enabled; green channel unchanged; regenerated UV0 tangents required',
                    'albedo': 'Existing padded RGB8, sampler Color, sRGB true, sourceEncoding TSE_NONE unchanged',
                    'alpha': 'Original 16bitgray, linear Masks, alphaR cutoff.333; coverage-preserving texture mips retained',
                    'roughness': 'Original 16bitgray, linear Masks; inherited clamp.38-.98',
                    'response': 'Exact inherited albedoScale.5/normalStrength1/specular.281021893/SSS.3/opacity.65 and narrow per-instance variation',
                    'COLOR0': 'Retained geometry attribute intentionally unused by exact provider shader'},
                'officialSources': ['https://polyhaven.com/a/grass_medium_02', 'https://polyhaven.com/license',
                    'https://dev.epicgames.com/documentation/en-us/unreal-engine/shading-models-in-unreal-engine'],
                'nativePrerequisites': ['All20 source variants preserve original geometry/roots and regenerate correct UV0 tangent frames.',
                    'Actual PHalpha bilinear mip0 coverage passes all4 exact selected a58 interior windows and803 boundary windows.',
                    'Saved/reloaded prior41 material graphs and74 texture identities remain exact; only new lawn key/bindings differ.',
                    'Actual Shipping Metal matched garden/detail/edge original PNGs demonstrate benefit; source graph/CPU pixels do not establish it.'],
                'nativeShaderCompiled': False, 'nativeVisualAccepted': False, 'fullPhotorealismAccepted': False,
                'performanceAccepted': False, 'globalCoverageAccepted': False}
    write(out / 'contract.json', contract)
    proof = {'status': 'PASS_SOURCE_SHIM_PHOTOGRAPHIC_APPEND_NATIVE_PENDING', 'owner': OWNER,
             'sourceSha256': sha(__file__), 'inputFiles': before,
             'checks': {'replayedOriginal40AndExactTransitionAppend': True, 'prior41GraphsAndRecordsByteExactAfterPhotoAppend': True,
                'all74TextureRecordsUnchangedAndNoExtraImports': True, 'new19NodeGraphMatchesActualProviderNativeSemantics': True,
                'nativeGraphComparisonNormalization': 'float32 stored values, enum display names and disconnected native UI pins only',
                'unexpectedRecipeVariantsRejected': failures, 'allInputHashesUnchangedAfterStudy': True},
             'sourceOnly': True, 'nativeShaderCompiled': False, 'nativeVisualAccepted': False,
             'performanceAccepted': False, 'globalCoverageAccepted': False,
             'outputs': {str(out / name): sha(out / name) for name in ('contract.json', 'material-manifest.json', 'source-graphs.json', 'source-textures.json')}}
    write(out / 'source-proof.json', proof)
    print(json.dumps({'status': proof['status'], 'receipt': pin(out / 'source-proof.json'), 'materials': 42,
                      'textures': 74, 'newNodes': len(new_graph['nodes']), 'nativeShaderCompiled': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    study(parser.parse_args().output)
