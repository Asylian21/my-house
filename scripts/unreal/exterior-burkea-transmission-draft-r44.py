"""UNBOUND R44 trial: one own leaf graph copy and one four-member HISM slot.

The recorded R39 observations locate the existing material and component;
they do not select a future R43 native base. No Unreal import, native entry,
project/asset mutation or old source producer is invoked by this module.
"""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-burkea-transmission-draft-r44.py'
SCHEMA = 'brezi-unbound-four-existing-burkea-leaf-transmission-trial-r44'
OUTPUT = ROOT/'output/unreal/exterior-burkea-transmission-20261002-r44-source-proposal'
HISTORICAL_REPORT = ROOT/'output/unreal/exterior-20261002-r39c/neighbor-props-native-report-r3.json'
REPORT_SHA = '118f451095730e2ff0e62304d959626d4a81be53f03e41dd2229fe91831f4da5'
LEAF = '/Game/Brezi/OriginalTree20261002R24/Materials/M_ph_original_tree_small_02_leaves_r24.M_ph_original_tree_small_02_leaves_r24'
ACTOR = '/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.BreziVegetationPatch_2312'
COMPONENT = ACTOR+'.Instances'
OWN_MATERIAL = '/Game/Brezi/BurkeaTransmission20261002R44/Materials/M_burkea_leaf_transmission_r44.M_burkea_leaf_transmission_r44'
STRENGTH_ROLE = 'BreziOriginalTreeR24:ph_original_tree_small_02_leaves_r24:strength'
OLD_STRENGTH = struct.unpack('<f', struct.pack('<f', .08))[0]
NEW_STRENGTH = struct.unpack('<f', struct.pack('<f', .24))[0]
EXPECTED_SOURCE_GRAPH_SHA = '3a79ac112253cd25724d7c8d729098d0fb97c7f77395c18ca358ee658b10a338'
EXPECTED_INSTANCE_ORDER_SHA = '90ed39ffc2fc18e9c82730e7376a79447a206f7944c15744b2032b0099b8b507'
FUTURE = {'selectedNativeBase': None, 'rootR43ImageDecision': None,
    'projectClone': None, 'nativePlan': None, 'nativePreflight': None,
    'nativeReport': None, 'nativeProcess': None, 'nativeProcessId': None,
    'currentByteAudit': None, 'actualCounts': None, 'beforeAfterOriginalImages': None}


def require(ok, message):
    if not ok: raise ValueError(message)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
def pin(path):
    p = Path(path).resolve();return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
def checked(row):
    p = Path(row['path']);require(p.is_absolute() and p.resolve() == p and p.is_file()
        and not p.is_symlink() and pin(p) == row, 'Exact historical observation pin required');return p
def read(path): return json.loads(Path(path).read_text())


def proposed_graph(record):
    require(record['asset'] == LEAF and record['reader'] == 'tree'
        and digest(record['graph']) == record['graphSha256'] == EXPECTED_SOURCE_GRAPH_SHA,
        'Exact specialized actual source leaf graph required')
    graph = copy.deepcopy(record['graph']);nodes = [n for n in graph['nodes'] if n['role'] == STRENGTH_ROLE]
    require(len(nodes) == 1 and nodes[0]['class'] == 'MaterialExpressionConstant'
        and nodes[0]['inputs'] == [] and nodes[0]['values'] == {'r': OLD_STRENGTH},
        'Exact original transmission strength required')
    nodes[0]['values']['r'] = NEW_STRENGTH
    return graph


def expected_scene(before, historical_target, own_material=OWN_MATERIAL):
    """Pure whole-witness counterfactual, independent of a future actual actor count."""
    require(own_material == OWN_MATERIAL and ACTOR in before
        and digest(before[ACTOR]) == digest(historical_target), 'Exact unchanged four-member target required')
    result = copy.deepcopy(before);components = result[ACTOR]['components']
    target = [c for c in components if c['path'] == COMPONENT]
    require(len(target) == 1 and target[0]['instanceCount'] == 4
        and target[0]['orderedInstanceTransformsSha256'] == EXPECTED_INSTANCE_ORDER_SHA
        and target[0]['materials'][1] == LEAF and target[0]['overrideMaterials'] == [],
        'Exact original membership/default-slot binding required')
    # SetMaterial(1) is expected to create a sparse override array; slot0 stays
    # null/default and slot2 continues to resolve the original trunk material.
    target[0]['materials'][1] = own_material
    target[0]['overrideMaterials'] = [None, own_material]
    return result


def validate_copy_graph(observed, original_record):
    require(digest(observed) == digest(proposed_graph(original_record)),
        'Only encoded .08 to .24 transmission coefficient may change')
    return True


def apply_trial(*args, **kwargs):
    raise RuntimeError('UNBOUND R44: future image-selected R43/base/clone/native proof is absent')


def emit_proposal():
    require(all(v is None for v in FUTURE.values()) and not OUTPUT.exists(), 'One unbound source proposal only')
    require(sha(HISTORICAL_REPORT) == REPORT_SHA, 'Recorded original R39 observer changed')
    report = read(HISTORICAL_REPORT)
    require(report['nativeProcessId'] == 94572 and report['savedMapUnloadedReloaded'] is True,
        'Historical actual saved observation required')
    material_pin = report['originalMaterialWitnessSaved'];witness_pin = report['savedActorWitness']
    record = read(checked(material_pin))[LEAF];witness = read(checked(witness_pin));target = witness[ACTOR]
    require(len(target['components']) == 1 and target['components'][0]['path'] == COMPONENT
        and record['usage'] == {'instancedStaticMeshes': True, 'nanite': True},
        'Historical one-component/four-tree usage identity differs')
    graph = proposed_graph(record);expected_scene(witness, target)
    textures = [n['values']['texture'] for n in record['graph']['nodes'] if n['class'] == 'MaterialExpressionTextureSample']
    require(len(textures) == len(set(textures)) == 4, 'All four original leaf photo references must remain exact')
    original_recipe_path = ROOT/'output/unreal/exterior-original-tree-20261002-r24-study/original-tree-material-proposal.json'
    require(sha(original_recipe_path) == 'a1eeff310781feb0d4956161e3e6e81d806355ab8acf6b383c32e6b2f912b8b0', 'Historical original photo recipe changed')
    original_recipe = next(r for r in read(original_recipe_path) if r['id'] == 'ph_original_tree_small_02_leaves_r24')
    photos = {**original_recipe['sourceMaps'], 'alpha': original_recipe['alphaSource']}
    require(set(photos) == {'albedo', 'normalGL', 'ARM', 'alpha'}, 'Exact four original published photo roles required')
    photo_pins = {role: {k: row[k] for k in ('path', 'sha256', 'bytes')} for role, row in photos.items()}
    for role, row in photo_pins.items():
        checked(row)
        sample = next(n for n in record['graph']['nodes'] if n['role'].endswith(':'+role))
        require(row['sha256'][:16] in sample['values']['texture'], 'Original published photo/native-reference identity differs')
    shader = Path('/Users/Shared/Epic Games/UE_5.8/Engine/Shaders/Private/ShadingModels.ush')
    code = shader.read_text();expression = 'Lighting.Transmission = AreaLight.FalloffColor * (AreaLight.Falloff * WrapNoL * Scatter) * SubsurfaceColor;'
    require(expression in code and 'half3 SubsurfaceColor = ExtractSubsurfaceColor(GBuffer);' in code,
        'Installed primary illustrative transmission equation changed')
    image = ROOT/'output/unreal/exterior-validation-20260930-r1/qa/editor-pilot-r39c-whole-original-neighbor-props-r30-1790963761054-81YFO4/exterior-neighborhood-ground-r38-aQ2IvK/userdir/Saved/Diagnostics/exterior-neighborhood-ground-r38-day-20261002T175803-scene.png'
    require(sha(image) == 'fa5fcd42c58254e41e05b32af9069e2b37c52fece898fb3e61ca31fd6c114a07', 'Original reviewed ground image changed')
    packet = {'schema': SCHEMA, 'schemaVersion': 1, 'owner': OWNER,
        'status': 'source-only-unbound-artistic-transmission-trial-native-and-images-pending',
        'historicalObservationOnly': {'nativeReport': pin(HISTORICAL_REPORT),
            'savedMaterialWitness': material_pin, 'savedActorWitness': witness_pin,
            'sourceLeafMaterial': LEAF, 'sourceGraphReader': 'tree', 'sourceGraphSha256': record['graphSha256'],
            'targetActor': ACTOR, 'targetComponent': COMPONENT, 'targetActorSha256': digest(target),
            'originalGroupLabel': target['label'], 'treeMembers': 4, 'originalInstanceOrderSha256': EXPECTED_INSTANCE_ORDER_SHA,
            'rawInheritedControlWitness': report['rawInstanceControlsSaved'],
            'additionalFourPropsCalibration': report['newSourceNativeMeasurements'], 'reviewedOriginalGroundPng': pin(image)},
        'futureBinding': FUTURE, 'proposedMaterial': {'ownAsset': OWN_MATERIAL,
            'operation': 'duplicate the exact observed leaf Material into a fresh owned namespace',
            'originalGraph': record['graph'], 'expectedOwnGraph': graph, 'expectedOwnGraphSha256': digest(graph),
            'onlyNodeSetter': {'role': STRENGTH_ROLE, 'property': 'r', 'oldEncodedF32': OLD_STRENGTH,
                'newArtisticAuthoredValue': .24, 'newEncodedF32': NEW_STRENGTH},
            'fourSharedTextureAssets': textures, 'originalAux': record['aux'], 'originalObservedUsage': record['usage'],
            'originalPublishedPhotoRecipe': pin(original_recipe_path), 'fourUntouchedOriginalPhotoFiles': photo_pins,
            'alphaClipBaseColorNormalArmUvFlagsAndOtherNodesUnchanged': True,
            'materialMetadataMustDeclareOwnOwnerAndArtisticCalibration': True},
        'sceneDelta': {'existingTargetComponents': 1, 'existingTargetTreeMembers': 4,
            'setter': 'new material on existing component slot1 only', 'allowedWitnessFields': ['materials[1]', 'overrideMaterials'],
            'expectedSparseOverrideMaterials': [None, OWN_MATERIAL], 'newActors': 0, 'newGeometry': 0,
            'newMaterialPackagesProposed': 1, 'newTextureObjects': 0, 'existingMeshDefaultSlotsEdited': False,
            'originalMaterialOrTextureSettersCalled': False, 'rootMatrixSeedOrCustomDataSettersCalled': False,
            'allCurrent2329RawGroupsBeforeAndSavedBinary64ExactRequired': True,
            'fullFutureActorCounterfactualAndProtectedProjectClosureRequired': True,
            'onlyOldContentMapChangedAndOneOwnMaterialPackageRequired': True},
        'primaryShaderRationale': {'source': pin(shader), 'function': 'TwoSidedBxDF', 'illustrativeEquation': expression,
            'legacyPrimaryEquationLinearInSubsurfaceColor': True, 'currentGpuShaderBranchObserved': False,
            'coefficientRatioRequested': 3.0, 'pixelBrightnessRatioClaimed': False},
        'independentOriginalImageObservation': 'Many underside/shaded leaf silhouettes in the actual ground view are near black; the original leaf photo contains medium olive detail. Transmission is a plausible contributor, not an isolated measured cause.',
        'intendedVisualEffect': 'Lift some back-lit leaf color/detail while retaining the original photographic leaf texture and masks.',
        'limits': ['.24 is an explicit artistic trial, not measured leaf transmittance or physical subsurface calibration.',
            'The primary legacy equation supplies a mechanism; the active native GPU shader/pixel response has not been measured.',
            'The trial does not change repeated crown silhouette, foliage/card orientation, density, species, deep shadows or flat ground/house detail.',
            'Increased transmission may look pale or glowing; acceptance requires actual original before/after PNGs with matched camera/static lighting/render and separately reported EV/cloud phase.',
            'All2329 raw controls, old material/texture bytes and other actors require fresh before/saved native comparison; historical pins do not establish a selected future R43 base.',
            'Numeric native normals/tangents, additional seed ranges, wind, collision, performance and full realism remain unverified.'],
        'activeDesign': 'C/B/B', 'setbacksMm': [3000, 3000], 'nativeExecuted': False, 'gpuExecuted': False,
        'actualMaterialOrSceneMutationPerformed': False, 'sourcePhotoPixelsEdited': False,
        'nativeAppearanceAccepted': False, 'physicalLeafOpticsAccepted': False, 'fullPhotorealismAccepted': False,
        'performanceAccepted': False, 'shippingVerified': False, 'activeOutputPromoted': False}
    OUTPUT.mkdir();(OUTPUT/'burkea-transmission-source-proposal.json').write_text(json.dumps(packet, indent=2, sort_keys=True, allow_nan=False)+'\n')
    return pin(OUTPUT/'burkea-transmission-source-proposal.json')


if __name__ == '__main__':
    raise RuntimeError('UNBOUND draft has no native/project entry; source emission is a separate reviewed CPU action')
