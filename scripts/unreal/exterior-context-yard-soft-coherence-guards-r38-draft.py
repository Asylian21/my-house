"""Unbound R38 draft contract. No scene, clone, or image decision is selected.

This module validates the frozen source artifact and a NEW sampling supplement.
It does not rerun the historical mask producer or treat its CPU proof as GPU proof.
A later immutable version must bind an image-selected base and independent clone.
"""
import copy
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-soft-coherence-guards-r38-draft.py'
SCHEMA = 'brezi-r38-soft-ground-unbound-native-draft'
SOURCE = ROOT/'output/unreal/exterior-context-yard-soft-coherence-20261002-r38-source-study/soft-ground-coherence-source-plan.json'
SOURCE_SHA = '6f3d44c7982d4da879e69045f036da02fd6aa5a8f1d815d7e733c2188a8ea92b'
GRAPHS_SHA = '77c11af97d6068643483011dcddf722c504e3fc2dbcac09af7cfea19a1aea584'
PNG_SHA = '23443c536f85052fb67e7ff0c6e1936709dec2f40860299770fa797719f47bdd'
PROOF_SHA = 'e0e08a176ec6085db2ce7a3b998e582b1a53e521c54075054aafb4bf81d974ae'
PREFIX = '/Game/Brezi/ContextYardSoftCoherence20261002R38'
TAG = 'BreziYardSoftR38:'
MASK_ASSET = PREFIX+'/Textures/T_soft_permission_r38.T_soft_permission_r38'
ASSETS = {k: PREFIX+'/Materials/M_'+k+'_soft_r38.M_'+k+'_soft_r38' for k in ('backdrop', 'substrate')}
ACTOR197 = '/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.StaticMeshActor_197'
DONOR668 = '/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.StaticMeshActor_668'
DRAFT_BINDING = {'selectedNativeBase': None, 'selectedNativeReport': None,
    'selectedRootImageDecision': None, 'projectClone': None, 'nativeEntryOwner': None}
SAMPLING_POLICY = {'srgb': False, 'sourceEncoding': 'TSE_NONE', 'compressionNone': True,
    'compressionSettings': 'TC_MASKS', 'mipGenSettings': 'TMGS_NO_MIPMAPS',
    'filter': 'TF_BILINEAR', 'addressX': 'TA_CLAMP', 'addressY': 'TA_CLAMP',
    'samplerSource': 'SSM_FROM_TEXTURE_ASSET', 'maskMipValueMode': 'TMVM_NONE', 'sampleChannel': 'R',
    'powerOfTwoMode': 'NONE', 'dimensions': [2048, 2048], 'downscaleDefault': 1.0,
    'downscalePerPlatformOverrides': {}, 'resizeDuringBuildXY': [0, 0],
    'lodBias': 0, 'maxTextureSize': 0, 'neverStream': True, 'virtualTextureStreaming': False,
    'alphaCoverageScaling': False, 'generatedArtistPermissionData': True,
    'sourcePhotoPixelsEdited': False, 'nativeTexelsDecoded': False,
    'nativeGpuPixelFormatVerified': False, 'nativeGpuOutsideEquivalenceVerified': False}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def file_pin(path):
    p = Path(path).resolve()
    return {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}


def pinned(row, expected=None):
    p = Path(row['path']).resolve()
    require(p.is_relative_to(ROOT) and p.is_file(), 'Missing workspace source input')
    require(file_pin(p) == row and (expected is None or row['sha256'] == expected), 'Frozen source pin differs: '+str(p))
    return p


def read(row, expected=None):
    return json.loads(pinned(row, expected).read_text())


def validate_policy(policy):
    require(policy == SAMPLING_POLICY, 'Closed bilinear/from-texture/NoMip/Clamp/uncompressed policy required')
    return copy.deepcopy(policy)


def proposed_native_graphs(source_graphs):
    """Explicit NEW draft adaptation, not a change to the frozen source graph.

The source mask copied Derivative mode but has no DDX/DDY ports. Installed
HLSLMaterialTranslator rejects that route. NoMip texture needs no explicit
derivatives; only the NEW mask sample mode is adapted, on both surfaces.
    """
    native = copy.deepcopy(source_graphs)
    for graph in native.values():
        matches = [n for n in graph['nodes'] if n['role'] == TAG+'fixed-world-yard-mask']
        require(len(matches) == 1 and matches[0]['values']['mip_value_mode'] == '<TextureMipValueMode.TMVM_DERIVATIVE: 3>'
            and matches[0]['inputs'] == [['UVs', TAG+'fixed-world-mask-uv', ''], ['Tex', None, None], ['Apply View MipBias', None, None]],
            'Exact frozen source mask template required')
        matches[0]['values']['mip_value_mode'] = '<TextureMipValueMode.TMVM_NONE: 0>'
    return native


def validate_native_graphs(source_graphs, native_graphs):
    require(native_graphs == proposed_native_graphs(source_graphs), 'Only the two new owned mask samples may change Derivative to None')
    return {'newOwnedMaskMipValueMode': 'TMVM_NONE', 'sourceMaskMipValueMode': 'TMVM_DERIVATIVE',
        'changedNewNodeValuesPerGraph': 1, 'frozenSourceGraphsEdited': False, 'old58NodeValuesChanged': 0,
        'inheritedUv1RouteChanged': False, 'nativeShaderCompileMeasured': False}


def validate_graphs(original, graphs, dither):
    require(set(graphs) == {'backdrop', 'substrate'}, 'Only two graph proposals allowed')
    extras = []
    for key, wanted in (('backdrop', 70), ('substrate', 73)):
        graph = graphs[key]
        require(set(graph) == {'nodes', 'roots', 'flags'} and len(graph['nodes']) == wanted, 'Closed 70/73 graph shape required')
        nodes = graph['nodes']; roles = [n['role'] for n in nodes]
        require(len(roles) == len(set(roles)), 'Duplicate graph roles')
        new = [n for n in nodes if n['role'].startswith(TAG)]
        require(len(new) == 12, 'Exact twelve shared response nodes required')
        extras.append(new)
        old = [n for n in nodes if not n['role'].startswith(TAG) and n not in dither]
        require(old == original['nodes'], 'Any original 58-node value/input/UV/texture change rejected')
        roots = copy.deepcopy(original['roots'])
        for root, suffix in [('BASE_COLOR', 'color'), ('NORMAL', 'normal'), ('ROUGHNESS', 'roughness')]:
            roots[root] = [TAG+'final-'+suffix, '']
        flags = copy.deepcopy(original['flags'])
        if key == 'substrate':
            temporal = [n for n in dither if n['class'] == 'MaterialExpressionMaterialFunctionCall']
            require(len(temporal) == 1, 'One inherited dither function required')
            roots['OPACITY_MASK'] = [temporal[0]['role'], 'Result']
            flags.update(blend_mode='<BlendMode.BLEND_MASKED: 1>', opacity_mask_clip_value=.5)
        require(graph['roots'] == roots and graph['flags'] == flags, 'Only three response roots plus declared substrate opacity/flags allowed')
        require([n for n in nodes if n in dither] == (dither if key == 'substrate' else []), 'Exact inherited UV1/R/Dither route required')
    require(extras[0] == extras[1], 'Both surfaces must share the exact fixed-world response')
    by = {n['role']: n for n in extras[0]}
    mask = by[TAG+'fixed-world-yard-mask']
    require(mask['class'] == 'MaterialExpressionTextureSample' and mask['values']['texture'] == MASK_ASSET,
        'Only the new owned generated mask texture allowed')
    require(by[TAG+'fixed-world-mask-uv']['values']['code'] ==
        'return float2((Position.x-5300)/5400,(31500-Position.y)/6000);', 'Fixed world registration changed')
    return {'originalNodes': 58, 'sharedNewNodes': 12, 'opaqueNodes': 70, 'maskedNodes': 73,
        'sourceOutsideOriginalDirectBranch': True, 'gpuOutsideOriginalByteEquivalence': False}


def load_contract():
    p = file_pin(SOURCE)
    require(p['sha256'] == SOURCE_SHA, 'Frozen R38 source plan changed')
    plan = read(p)
    require(plan['schema'] == 'brezi-fixed-world-yard-soft-ground-coherence-source-r38' and
        plan['schemaVersion'] == 1 and plan['status'] == 'source-only-material-coherence-proposal-native-base-pending', 'Exact frozen source-only plan required')
    require(all(plan[k] is None for k in DRAFT_BINDING), 'Frozen source must remain unbound')
    require(plan['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'} and
        plan['setbacksMm'] == {'street': 3000, 'east': 3000}, 'C/B/B and setbacks required')
    graphs = read(plan['materialGraphs'], GRAPHS_SHA)
    proof = read(plan['permissionFieldProof'], PROOF_SHA)
    png = pinned(plan['permissionField'], PNG_SHA).read_bytes()
    require(png[:8] == b'\x89PNG\r\n\x1a\n' and png[12:16] == b'IHDR' and
        struct.unpack('>IIBBBBB', png[16:29]) == (2048, 2048, 8, 0, 0, 0, 0), 'Original generated L8 PNG header required')
    require(proof['layout']['dimensions'] == [2048, 2048] and proof['exactZeroAllFourImageBorders'] is True
        and proof['exhaustiveNonzeroCenterDistanceGuardChecked'] is True and proof['sourceBilinearSupportInsideQuantizedMask'] is True,
        'Frozen CPU permission-field proof required')
    require(proof['minimumNonzeroCenterBoundaryDistanceCm'] > proof['layout']['minimumCenterToMaskBoundaryCm']
        and proof['nativeGpuBoundaryZeroVerified'] is False, 'Source margin and GPU boundary limits required')
    original = read(plan['inputs']['backdropR35'])['repairC']['materialReport']['graph']
    substrate = read(plan['inputs']['groundR32'])['newMaterialReport']['materials']['yard_substrate_r32']['graph']
    wanted = ['uv1', 'coverage-r', 'temporal-dither']
    by = {n['role']: n for n in substrate['nodes']}
    dither = [by['BreziYardGroundR32:yard_substrate_r32:'+r] for r in wanted]
    # graph snapshots are role-sorted; the dither port/root is identified independently.
    ordered_dither = sorted(dither, key=lambda n: n['role'])
    audit = validate_graphs(original, graphs, ordered_dither)
    return {'source': p, 'plan': plan, 'graphs': graphs, 'nativeGraphs': proposed_native_graphs(graphs), 'originalGraph': original,
        'originalBackdropAsset': plan['targets']['backdropOriginalActor197']['historicalWitness']['components'][0]['materials'][0],
        'originalSubstrateAsset': plan['targets']['substrateDonorActor668']['historicalWitness']['components'][0]['materials'][0],
        'ditherNodes': ordered_dither, 'fieldProof': proof, 'samplingPolicy': copy.deepcopy(SAMPLING_POLICY), 'graphAudit': audit}


def draft_contract(bundle):
    return {'schema': SCHEMA, 'schemaVersion': 1, 'owner': OWNER, 'status': 'source-only-unbound-native-and-material-draft',
        **copy.deepcopy(DRAFT_BINDING), 'sourceStudy': bundle['source'], 'samplingPolicy': validate_policy(bundle['samplingPolicy']),
        'plannedNewPackageAssets': sorted([*ASSETS.values(), MASK_ASSET]),
        'nativeGraphAdaptation': validate_native_graphs(bundle['graphs'], bundle['nativeGraphs']),
        'targets': {'backdrop': {'originalActor': ACTOR197, 'component': 'StaticMeshComponent0', 'slot': 0},
            'substrate': {'exactDonorActor': DONOR668, 'actualActor': None, 'futureResolver': 'selected saved report.newActorMapping[exactDonorActor]', 'slot': 0}},
        'historicalCpuDomainProofReplayedByDraft': False, 'oldGraphSamplerSourceAndWorldPositionReadbackRequired': True,
        'nativeImportedTexelsDecoded': False, 'nativeGpuPixelFormatVerified': False, 'nativeOutsideEquivalenceVerified': False,
        'nativeApplied': False, 'nativeAppearanceAccepted': False, 'performanceAccepted': False,
        'fullPhotorealismAccepted': False, 'shippingVerified': False, 'packageVerified': False}


def require_native_binding(binding):
    # This draft cannot be made runnable by passing an invented accepted flag.
    raise RuntimeError('R38 draft is unbound: image-selected saved base and a fresh clone require a NEW finalized immutable native revision')


def counterfactual_two_slots(before, targets):
    """Pure future kernel, not a base validator or receipt of applied changes."""
    require(set(targets) == {'backdrop', 'substrate'}, 'Exactly two explicit target refs required')
    require(targets['backdrop']['actor'] == ACTOR197 and targets['substrate']['actor'] != ACTOR197,
        'Original actor197 and independently mapped substrate actor required')
    expected = copy.deepcopy(before)
    for key, target in targets.items():
        require(set(target) == {'actor', 'component', 'originalMesh', 'originalMaterial'}, 'Closed target kernel schema required')
        require(target['actor'] in expected, 'Target absent from supplied witness')
        components = [c for c in expected[target['actor']]['components'] if c['name'] == target['component']]
        require(len(components) == 1, 'Unambiguous component required')
        c = components[0]
        require(c['mesh'] == target['originalMesh'] and c['materials'] and c['materials'][0] == target['originalMaterial'], 'Declared original component differs')
        c['materials'][0] = ASSETS[key]
        overrides = c['overrideMaterials']
        if overrides:
            overrides[0] = ASSETS[key]
        else:
            c['overrideMaterials'] = [ASSETS[key]]
    return expected
