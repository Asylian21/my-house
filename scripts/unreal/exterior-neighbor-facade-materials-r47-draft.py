"""UNBOUND R47 material-copy kernel; no scene setters or runnable native entry.

Graph readers are supplied by a later authenticated owner and must include the
complete R18 neighbor flags/REFRACTION/WPO shape. This module does not invoke
historical producers, consumers or tests. Every UObject-capable route is gated.
"""
import copy
import hashlib
import json
from pathlib import Path
import types

GUARD_PATH = Path(__file__).with_name('exterior-neighbor-facade-guards-r47-draft.py')
g = types.ModuleType('r47_isolated_unbound_guard')
g.__file__ = str(GUARD_PATH)
exec(compile(GUARD_PATH.read_text(), str(GUARD_PATH), 'exec'), g.__dict__)
OWNER = 'scripts/unreal/exterior-neighbor-facade-materials-r47-draft.py'
SCHEMA = 'brezi-unbound-r47-two-scalar-existing-photo-material-copy'


def _source(bundle, binding):
    g.require_native_binding(binding)
    expected = g.load_contract()
    g.require(bundle == expected, 'Exact immutable source packet required')
    return bundle['source']


def _metadata(u, material, binding):
    g.require_native_binding(binding)
    # Installed EditorAssetLibrary.h exposes GetMetadataTagValues as a
    # BlueprintCallable TMap<FName,FString>, covering all inherited tags.
    return {str(k): str(v) for k, v in u.EditorAssetLibrary.get_metadata_tag_values(material).items()}


def _aux(u, material, binding):
    g.require_native_binding(binding)
    samples = {}; offsets = {}
    for node in u.MaterialEditingLibrary.get_material_expressions(material):
        role = str(node.get_editor_property('desc'))
        if isinstance(node, u.MaterialExpressionTextureSample):
            g.require(role not in samples, 'Unique sampler role required')
            samples[role] = str(node.get_editor_property('sampler_source'))
        if isinstance(node, u.MaterialExpressionWorldPosition):
            g.require(role not in offsets, 'Unique world-position role required')
            offsets[role] = str(node.get_editor_property('world_position_shader_offset'))
    return {'samplerSources': samples, 'worldPositionShaderOffsets': offsets}


def _usage(u, material, binding):
    g.require_native_binding(binding)
    def enum(token):
        normalized = token.replace('_', '').lower()
        values = [getattr(u.MaterialUsage, n) for n in dir(u.MaterialUsage)
            if n.replace('_', '').lower() == normalized]
        g.require(len(values) == 1, 'Exact MaterialUsage enum required: '+token)
        return values[0]
    return {key: bool(u.MaterialEditingLibrary.has_material_usage(material, enum(token)))
        for key, token in [('instancedStaticMeshes', 'MATUSAGE_INSTANCED_STATIC_MESHES'), ('nanite', 'MATUSAGE_NANITE')]}


def _state(u, material, binding, graph_snapshot):
    g.require_native_binding(binding)
    return {'asset': material.get_path_name(), 'graph': graph_snapshot(u, material),
        'aux': _aux(u, material, binding), 'usage': _usage(u, material, binding),
        'metadata': _metadata(u, material, binding)}


def _textures(u, source, binding, texture_snapshot):
    g.require_native_binding(binding)
    result = {}
    for role, row in source['originalMaps'].items():
        asset = row['nativeAsset']; texture = u.EditorAssetLibrary.load_asset(asset)
        g.require(isinstance(texture, u.Texture2D) and texture.get_path_name() == asset,
            'Exact original shared Texture2D required')
        result[role] = texture_snapshot(u, texture)
        g.require(result[role] == row['recordedNativeTexture'],
            'Original complete visible texture settings/metadata differ')
    return result


def validate_graph(graph, bundle):
    """Pure full-shape comparison, including all flags and root connections."""
    expected = g.load_contract()
    g.require(bundle == expected and graph == bundle['proposed']['graph']
        and g.digest(graph) == g.NEW_GRAPH_SHA, 'Complete two-scalar-only proposed graph required')
    return True


def _expected_metadata(original, source):
    result = copy.deepcopy(original)
    result.update({'BreziGeneratedBy': OWNER, 'BreziSourceOriginalMaterial': g.ORIGINAL,
        'BreziSourceOriginalGraphSha256': g.OLD_GRAPH_SHA, 'BreziSourceProposalSha256': g.SOURCE_SHA,
        'BreziR47ArtisticUncalibrated': 'true',
        'BreziR47Changes': json.dumps(source['proposedMaterial']['changes'], sort_keys=True, separators=(',', ':')),
        'BreziR47ReusesOriginalPhotos': json.dumps({k: r['nativeAsset'] for k, r in source['originalMaps'].items()}, sort_keys=True, separators=(',', ':'))})
    return result


def _verify_loaded(u, material, bundle, binding, report, graph_snapshot, texture_snapshot):
    source = _source(bundle, binding)
    actual = _state(u, material, binding, graph_snapshot)
    validate_graph(actual['graph'], bundle)
    g.require(actual == report['savedMaterialState'] and actual['asset'] == g.ASSET
        and actual['aux'] == bundle['proposed']['aux'] and actual['usage'] == bundle['proposed']['usage']
        and actual['metadata'] == _expected_metadata(report['originalMaterialState']['metadata'], source),
        'Loaded complete graph/aux/usage/all metadata differ')
    old = u.EditorAssetLibrary.load_asset(g.ORIGINAL)
    g.require(isinstance(old, u.Material) and _state(u, old, binding, graph_snapshot) == report['originalMaterialState'],
        'Original complete material state changed')
    g.require(_textures(u, source, binding, texture_snapshot) == report['originalTextureState'],
        'Original photo texture state changed')
    return material


def build_materials(u, bundle, binding, graph_snapshot, texture_snapshot):
    source = _source(bundle, binding)  # Rejects before any u/EditorAssetLibrary access.
    assets = u.EditorAssetLibrary; lib = u.MaterialEditingLibrary
    old = assets.load_asset(g.ORIGINAL)
    g.require(isinstance(old, u.Material), 'Actual original Material required')
    original_state = _state(u, old, binding, graph_snapshot)
    g.require(original_state['asset'] == g.ORIGINAL and original_state['graph'] == bundle['original']['graph']
        and original_state['aux'] == bundle['original']['aux'] and original_state['usage'] == bundle['original']['usage'],
        'Current exact original22-node graph/aux/usage required')
    textures = _textures(u, source, binding, texture_snapshot)
    g.require(not assets.does_asset_exist(g.ASSET.split('.')[0]), 'Fresh own R47 namespace required')
    material = assets.duplicate_asset(g.ORIGINAL, g.ASSET.split('.')[0])
    g.require(isinstance(material, u.Material) and material.get_path_name() == g.ASSET,
        'One own material copy required')
    copied = _state(u, material, binding, graph_snapshot)
    g.require({k: v for k, v in copied.items() if k != 'asset'}
        == {k: v for k, v in original_state.items() if k != 'asset'}, 'Initial complete copied state differs')
    expressions = lib.get_material_expressions(material)
    nodes = {str(n.get_editor_property('desc')): n for n in expressions}
    g.require(len(nodes) == len(expressions) == 22
        and set(nodes) == {n['role'] for n in bundle['original']['graph']['nodes']}, 'Exact unique source expression roles required')
    for role, before, after in g.CHANGES:
        node = nodes[role]
        g.require(isinstance(node, u.MaterialExpressionConstant) and float(node.get_editor_property('r')) == before,
            'Authenticated source Constant.r differs')
        node.set_editor_property('r', after)
        g.require(float(node.get_editor_property('r')) == after, 'Exact requested F32 scalar readback required')
    for key, value in _expected_metadata(original_state['metadata'], source).items():
        if original_state['metadata'].get(key) != value:
            assets.set_metadata_tag(material, key, value)
    errors = list(lib.recompile_material(material) or [])
    g.require(errors == [], 'Copied material shader compile errors: '+str(errors))
    state = _state(u, material, binding, graph_snapshot)
    validate_graph(state['graph'], bundle)
    g.require(state['aux'] == bundle['proposed']['aux'] and state['usage'] == bundle['proposed']['usage']
        and state['metadata'] == _expected_metadata(original_state['metadata'], source),
        'Aux/usage/all inherited and own metadata must remain exact')
    # This is the only save call; no old graph, texture, scene or map is saved.
    g.require(assets.save_loaded_asset(material, False), 'Cannot save one own copied material')
    report = {'schema': SCHEMA, 'owner': OWNER, 'asset': g.ASSET,
        'sourceProposal': g.pin(g.SOURCE), 'originalMaterialState': original_state,
        'originalTextureState': textures, 'savedMaterialState': state,
        'originalGraphSha256': g.OLD_GRAPH_SHA, 'graphSha256': g.NEW_GRAPH_SHA,
        'newPackageAssets': [g.ASSET], 'materialCount': 1, 'newTextureObjectCount': 0,
        'onlyTwoConstantSettersCalled': True, 'originalMaterialOrTextureSettersCalled': False,
        'actorRootGeometryUvCollisionOrMapSettersCalled': False,
        'savedMaterialLoadedReadback': True, 'independentMaterialUnloadedReloaded': False,
        'sourcePixelsEdited': False, 'nativeAppearanceAccepted': False,
        'fullPhotorealismAccepted': False, 'performanceAccepted': False,
        'shippingVerified': False, 'activeOutputPromoted': False}
    loaded = assets.load_asset(g.ASSET)
    g.require(isinstance(loaded, u.Material), 'Saved own material must load')
    return _verify_loaded(u, loaded, bundle, binding, report, graph_snapshot, texture_snapshot), report


def verify_materials(u, bundle, binding, report, graph_snapshot, texture_snapshot):
    _source(bundle, binding)  # Reject before the first UObject/library access.
    g.require(report['schema'] == SCHEMA and report['owner'] == OWNER
        and report['asset'] == g.ASSET and report['sourceProposal'] == g.pin(g.SOURCE)
        and report['newPackageAssets'] == [g.ASSET] and report['materialCount'] == 1
        and report['newTextureObjectCount'] == 0, 'Exact one-copy report header required')
    material = u.EditorAssetLibrary.load_asset(g.ASSET)
    g.require(isinstance(material, u.Material), 'Saved own Material required')
    return _verify_loaded(u, material, bundle, binding, report, graph_snapshot, texture_snapshot)


def describe_draft():
    return {**g.describe_draft(), 'materialOwner': OWNER, 'materialSchema': SCHEMA,
        'functions': ['build_materials', 'verify_materials', 'validate_graph'],
        'sourceExpressionRolesRetained': True, 'onlyOwnMaterialSaved': True,
        'completeMetadataReadbackPlanned': True,
        'independentMaterialUnloadGpuPixelAppearanceVerified': False,
        'sceneIntegrationOwnerAndActualBase': None}


if __name__ == '__main__':
    raise RuntimeError('UNBOUND R47 material kernel has no producer/native entry')
