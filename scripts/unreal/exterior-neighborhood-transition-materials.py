"""One opt-in continuous unbuilt-ground material using the existing ground graph.

No actor bindings, geometry, imagery, original material or source ground change.
The condition is an authored world field, distinct from aerial RGB/coverage data.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighborhood-transition-materials.py'
KEY = 'context_continuous_unbuilt_ground'
STUDY = ROOT / 'output/unreal/exterior-neighborhood-transition-20261001-r1-study'
PLAN = STUDY / 'transition-plan.json'
PLAN_SHA = '2be538a9311282d9b8485d925fa070b3984b50cea852ea2e7406ed1699448ef5'
PROOF = ROOT / 'output/unreal/exterior-neighborhood-transition-validation-20261001-r2/source-proof.json'
PROOF_SHA = 'a527c4eda9ecb4ce0823c4128835e541e06cb5e15b9d5296b586d134e3122ce4'
NATIVE = ROOT / 'scripts/unreal/exterior-neighborhood-transition-native.py'
NATIVE_SHA = '892313c1b985f9e7c291f2e3cc02edad38305ae0cc607c5a3240dc0c4b3b1e4a'
RECEIPT = ROOT / 'output/unreal/exterior-neighborhood-transition-native-validation-20261001-r1.json'
RECEIPT_SHA = 'a932aaf463f524917f9e37f886183ed42ef75e3a170e90b3b4f76fed118beac9'
RAW_REPORT = ROOT / 'output/unreal/exterior-20261001-r10/exterior-import-report.json'
RAW_REPORT_SHA = '09c0652f46104591843760b1f225f98af168fd7e6653ef85b33f912630cb9855'
CONDITION_SHA = '4416981ea522e7115a655e70169fa44814913f5907cfb0b6b1b9751a7752c360'
_N = None


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1048576):
            result.update(block)
    return result.hexdigest()


def pin(path, expected):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == expected,
            'Transition material dependency differs: ' + str(path))
    return path


def _native():
    global _N
    pin(NATIVE, NATIVE_SHA)
    if _N is None:
        spec = importlib.util.spec_from_file_location('transition_material_source_gate', NATIVE)
        _N = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_N)
    return _N


def prepare_transition(path):
    """Validate the exact approved source field/proofs before any native write."""
    require(isinstance(path, (str, Path)) and Path(path).resolve() == PLAN,
            'Transition materials require the exact frozen study plan path')
    plan = json.loads(pin(PLAN, PLAN_SHA).read_text())
    proof = json.loads(pin(PROOF, PROOF_SHA).read_text())
    receipt = json.loads(pin(RECEIPT, RECEIPT_SHA).read_text())
    require(receipt['status'] == 'PASS_STDLIB_TRANSITION_NATIVE_INPUT_TESTS_SOURCE_ONLY'
            and receipt['tests'] == receipt['testsPassed'] == 10 and receipt['testsFailed'] == receipt['exitCode'] == 0
            and receipt['sourceFiles'][str(NATIVE)] == NATIVE_SHA,
            'Transition actual native-input source test proof differs')
    inputs = {str(PLAN): PLAN_SHA, str(PROOF): PROOF_SHA, str(RECEIPT): RECEIPT_SHA,
              **receipt['inputFiles'], **receipt['sourceFiles'],
              receipt['log']['path']: receipt['log']['sha256']}
    for filename, expected in inputs.items():
        pin(filename, expected)
    require(proof['plan'] == {'path': str(PLAN), 'sha256': PLAN_SHA}
            and proof['validation']['status'] == 'verified-source-neighborhood-transition-study-native-pending'
            and plan['sharedPbrResponseProposal']['materialKey'] == KEY
            and plan['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
            and plan['housePlacement']['streetSetbackMm'] == plan['housePlacement']['eastSetbackMm'] == 3000
            and plan['nativeVisualAccepted'] is False and plan['performanceAccepted'] is False,
            'Transition source design/protection/response proof differs')
    native = _native()
    approved, _ = native._approved()
    require(native.digest(plan) == native.digest(approved), 'Transition frozen plan content differs')
    condition = plan['conditionTexture']
    require(condition['sha256'] == CONDITION_SHA and condition['worldBoundsCm'] == [-18000., -18000., 18000., 18000.]
            and condition['worldCmToUvRows'] == [[1/36000, 0, .5], [0, -1/36000, .5]],
            'Transition condition world affine differs')
    pixels = native._condition_texture(condition, approved['conditionTexture'])
    require(pixels['all1048576ConditionPixelsVerified'] is True,
            'Transition actual artist condition pixels were not verified')
    historical = json.loads(pin(RAW_REPORT, RAW_REPORT_SHA).read_text())
    original = {k: copy.deepcopy(historical['materials']['materials'][k]['recipe'])
                for k in ('context_meadow', 'context_fallow')}
    difference = {k for k in original['context_meadow'] if original['context_meadow'][k] != original['context_fallow'][k]}
    require(difference == {'coverRange', 'tint', 'albedoScale', 'normalStrength'},
            'Original meadow/fallow PBR, UV or geographic metadata are no longer shared')
    require(original['context_meadow']['coverRange'] == [.7, .78]
            and original['context_fallow']['coverRange'] == [.3, .38]
            and original['context_meadow']['albedoScale'] == .78 and original['context_fallow']['albedoScale'] == .74
            and original['context_meadow']['normalStrength'] == .65 and original['context_fallow']['normalStrength'] == .7,
            'Original response endpoints differ')
    for recipe in original.values():
        require(recipe['kind'] == 'ground' and recipe['tileCm'] == 200 and recipe['cropRows'] is False
                and set(recipe['maps']) == {'albedo', 'normal', 'roughness'}
                and set(recipe['groundCover']['maps']) == {'albedo', 'normal', 'roughness'}
                and all(k in recipe for k in ('fieldMacro', 'groundOrthophoto', 'projectionMask')),
                'Transition must retain existing ground maps and protected geographic layers')
    return {'plan': {'path': str(PLAN), 'sha256': PLAN_SHA}, 'conditionTexture': copy.deepcopy(condition),
            'conditionValidation': pixels, 'originalRecipes': original, 'inputFiles': inputs,
            'pipelineFiles': {str(NATIVE): NATIVE_SHA, str(Path(__file__).resolve()): sha(__file__)}}


def response(condition, fallow=(.86, .85, .78), meadow=(.86, .94, .86)):
    require(type(condition) in (int, float) and math.isfinite(condition), 'Nonfinite ground condition')
    c = min(.85, max(.15, condition))
    return {'condition': c, 'coverAmount': .34 + .40*c,
            'tint': [a + (b-a)*c for a, b in zip(fallow, meadow)],
            'albedoScale': .74 + .04*c, 'normalStrength': .70 - .05*c}


def append_transition(writer, materials, records, prepared, api):
    """Build with Writer.create, then rewire four inputs on this new graph only."""
    require(KEY not in materials and KEY not in records and len(materials) == len(records) == 40,
            'Transition append requires forty finalized originals and no previous shared material')
    require(writer.prefix == '/Game/Brezi/Exterior20260926' or writer.prefix.startswith('/Game/Brezi/Exterior20260926/'),
            'Transition material namespace escaped')
    require(len(writer.texture_report) == 73, 'Transition requires the finalized seventy-three-texture baseline')
    originals = copy.deepcopy(records)
    for key, expected in prepared['originalRecipes'].items():
        require(records[key]['recipe'] == expected and key in materials,
                'Transition finalized source recipe, geographic layer or response drift: ' + key)
        require(api['digest'](api['graph_snapshot'](writer.u, materials[key])) == records[key]['graphSha256'],
                'Transition existing material graph differs: ' + key)
    recipe = copy.deepcopy(records['context_meadow']['recipe'])
    material, entry = writer.create(KEY, recipe)
    nodes = {str(n.get_editor_property('desc')).removeprefix(api['TAG']): n
             for n in writer.lib.get_material_expressions(material)}
    require(len(nodes) == len(entry['graph']['nodes']), 'Transition clone node identities are ambiguous')
    texture = prepared['conditionTexture']
    condition_recipe = {'maps': {'ground_condition': {'path': texture['path'], 'sha256': texture['sha256']}},
                        'normalConvention': 'DirectX', 'license': 'LicenseRef-Project-Authored',
                        'sourceUrl': str(ROOT / 'scripts/unreal/exterior-neighborhood-transition-study.py'),
                        'addressMode': 'clamp', 'expectedDimensions': [1024, 1024]}
    uv = writer.custom(material, 'continuous-condition-world-uv',
                       'return float2(dot(float3(Position.xy,1),RowU),dot(float3(Position.xy,1),RowV));',
                       {'Position': (nodes['world-position'], ''),
                        **{name: (writer.vector(material, 'continuous-condition-'+name, row), '')
                           for name, row in zip(('RowU', 'RowV'), texture['worldCmToUvRows'])}}, 2)
    sample = writer.sample(material, 'ground_condition', condition_recipe, uv, '-world-condition')
    condition = writer.custom(material, 'continuous-condition-bounded', 'return clamp(Condition,.15,.85);',
                              {'Condition': (sample, 'R')}, 1)
    amount = writer.custom(material, 'continuous-ground-cover', 'return .34+.40*Condition;',
                           {'Condition': (condition, '')}, 1)
    for role in ('albedo', 'normal', 'roughness'):
        writer.connect(amount, '', nodes['groundcover-'+role], 'Amount')
    tint = writer.custom(material, 'continuous-ground-tint', 'return lerp(Fallow,Meadow,Condition);',
                         {'Fallow': (writer.vector(material, 'continuous-fallow-tint', prepared['originalRecipes']['context_fallow']['tint']), ''),
                          'Meadow': (nodes['linear-tint'], ''), 'Condition': (condition, '')})
    albedo = writer.custom(material, 'continuous-ground-albedo-response', 'return .74+.04*Condition;',
                           {'Condition': (condition, '')}, 1)
    strength = writer.custom(material, 'continuous-ground-normal-strength', 'return .70-.05*Condition;',
                             {'Condition': (condition, '')}, 1)
    writer.connect(tint, '', nodes['natural-ground-color'], 'Tint')
    writer.connect(albedo, '', nodes['natural-ground-color'], 'AlbedoScale')
    writer.connect(strength, '', nodes['world-ground-normal'], 'Strength')
    recipe['groundCondition'] = {**copy.deepcopy(texture), 'role': 'ground_condition',
                                 'sourceLicense': condition_recipe['license'], 'sourcePage': condition_recipe['sourceUrl'],
                                 'ordinaryLinearMips': True, 'automaticViewMipBias': False, 'sourceEncodingOverride': 'None'}
    recipe['continuousResponse'] = {'coverAmount': '.34+.40*C', 'tint': 'lerp(fallow,meadow,C)',
                                    'albedoScale': '.74+.04*C', 'normalStrength': '.70-.05*C',
                                    'conditionClamp': [.15, .85], 'sourceMaterial': 'context_meadow',
                                    'unchangedPbrUvFieldMacroAndProtectedOrtho': True}
    require(not list(writer.lib.recompile_material(material) or []), 'Continuous ground shader compilation failed')
    writer.assets.set_metadata_tag(material, 'BreziExteriorRecipe', json.dumps(recipe, sort_keys=True))
    require(writer.assets.save_loaded_asset(material, only_if_is_dirty=False), 'Cannot save continuous ground material')
    graph = api['graph_snapshot'](writer.u, material)
    require(len(graph['nodes']) <= 114, 'Continuous shared ground exceeded its isolated node budget')
    records[KEY] = {**entry, 'recipe': recipe, 'graph': graph, 'graphSha256': api['digest'](graph)}
    materials[KEY] = material
    require({k: v for k, v in records.items() if k != KEY} == originals, 'Original forty material reports changed')
    for key in originals:
        require(api['digest'](api['graph_snapshot'](writer.u, materials[key])) == originals[key]['graphSha256'],
                'An original material graph changed while appending transition')
    require(len(writer.texture_report) == 74, 'Continuous ground must add exactly one distinct texture')
    return {'status': 'saved-continuous-unbuilt-ground-awaiting-native-reload', 'owner': OWNER,
            'sourceSha256': sha(__file__), 'materialKey': KEY, 'sourcePlan': prepared['plan'],
            'plan': prepared['plan']['path'], 'planSha256': prepared['plan']['sha256'],
            'condition': {'path':texture['path'],'sha256':texture['sha256'],'role':'ground_condition',
                          'dimensions':[1024,1024],'worldCmToUvRows':texture['worldCmToUvRows'],
                          'sourceLicense':condition_recipe['license'],'sourcePage':condition_recipe['sourceUrl'],
                          'sRGB':False,'uncompressedRgba8':True,'compressionNonePropertyExposed':False,
                          'uncompressedFormatBasis':'TC_VectorDisplacementmap -> NameBGRA8 (UE5.8 native source)',
                          'compressionSettings':'TC_VECTOR_DISPLACEMENTMAP','addressMode':'clamp',
                          'mipGenSettings':'TMGS_FROM_TEXTURE_GROUP','ordinaryMips':True,
                          'automaticViewMipBias':False,'sourceEncodingOverride':'None','sourceEncodingReadback':'TSE_NONE'},
            'original40GraphsUnchanged':True,'priorMaterialCount':40,'finalMaterialCount':41,'textureCount':74,
            'conditionValidation': prepared['conditionValidation'], 'sourceMaterial': 'context_meadow',
            'originalMaterialsUnchanged': 40, 'additionalMaterials': 1, 'additionalTextures': 1,
            'fieldMacroAndProtectedCameraOrthoUnchanged': True, 'sourceGroundBindingsChanged': False,
            'artistInterpretation': True, 'surveyedLandUse': False, 'nativeVisualAccepted': False,
            'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted': False}
