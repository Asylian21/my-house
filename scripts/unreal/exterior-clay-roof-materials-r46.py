"""R46 bound-ready roof kernels, blocked until a new coordinator binds them.

The frozen R45 source recipe/paths/tags are retained. Only three untouched
original maps and one opaque graph are created; this helper never changes
geometry, old materials, actors, component slots or a map.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-clay-roof-materials-r46.py'
SCHEMA = 'brezi-r46-bound-original-clay-roof-photo-material'
GUARD = ROOT/'scripts/unreal/exterior-burkea-clay-guards-r46.py'
CONTRACT = ROOT/'scripts/unreal/exterior-clay-roof-photo-contract-r45-draft.py'
CONTRACT_SHA = '0e956917e92e0c31bcf36123ff29db33f3630b0df97bc8d16548f13a5dd806d7'
KERNEL = ROOT/'scripts/unreal/exterior-clay-roof-photo-native-r45-draft.py'
KERNEL_SHA = '01d2e9d820404ceda16f191acc8b6b2ade50736596bb2586f5197419f8ecaf43'
POLICY = ROOT/'scripts/unreal/exterior-context-parcel-boundary-materials-r43.py'
POLICY_SHA = 'fad70bfdd0bd7b9eff2ee289f20a47b1c3d717b7bb683eecbe8d59ff72f873d9'
LIMITS = {'sourcePhotoPixelsEdited': False, 'nativeSourceTexelsDecoded': False,
    'native16BitSourcePrecisionVerified': False, 'nativePixelFormatOrTexelsReadBack': False,
    'nativeNormalTangentNumericReadbackPerformed': False, 'nativeNormalAppearanceVerified': False,
    'ridgeCourseContinuityVerified': False, 'materialPackagesIndependentlyUnloaded': False,
    'physicalRoofOpticsAccepted': False, 'nativeAppearanceAccepted': False,
    'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'shippingVerified': False}


def require(ok, message):
    if not ok: raise RuntimeError(message)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
def pin(path):
    p = Path(path).resolve();return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
def module(name, path, expected=None):
    if expected is not None: require(sha(path) == expected, 'Immutable original/proven material helper changed')
    s = importlib.util.spec_from_file_location(name, path);m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m);return m
def binding_guard(): return module('_r46_final_roof_binding_guard', GUARD)
def policy(): return module('_r46_private_proven_texture_policy', POLICY, POLICY_SHA)
def contract(): return module('_r46_private_frozen_roof_contract', CONTRACT, CONTRACT_SHA)
def kernel(): return module('_r46_private_frozen_roof_graph_validation', KERNEL, KERNEL_SHA)


def validate_binding(bundle, binding):
    # No CDO, asset lookup, import or material mutation may precede this gate.
    g = binding_guard();g.require_native_binding(binding)
    require(set(bundle) == {'source', 'base', 'binding'} and bundle['binding'] == binding
        and set(bundle['source']) == {'leaf', 'roof'}, 'Exact combined authenticated three-key packet required')
    roof = bundle['source']['roof'];c = contract();source = c.load_source()
    require(set(roof) == {'proposalPin', 'proposal'} and roof['proposalPin'] == pin(c.PROPOSAL)
        and roof['proposal'] == source, 'Exact immutable b1c2 original roof proposal required')
    return source


def metadata(u, obj, role, source=None, write=False):
    c = contract();expected = {'BreziGeneratedBy': OWNER, 'BreziR46Role': 'roof:'+role,
        'BreziR46RoofSourceProposalSha256': c.PROPOSAL_SHA, 'BreziSourceLicense': 'CC0-1.0'}
    if source is not None: expected['BreziSourceSha256'] = source['sha256']
    for key, value in expected.items():
        if write: u.EditorAssetLibrary.set_metadata_tag(obj, key, value)
        require(u.EditorAssetLibrary.get_metadata_tag(obj, key) == value, 'Owned R46 roof provenance differs')
    return expected


def preflight(u):
    p = policy();enums = p.preflight_enums(u);reflection = p.preflight_reflection(u)
    for cls in ('MaterialExpressionMultiply', 'LinearColor', 'Vector4', 'Texture2D', 'Material'):
        require(hasattr(u, cls), 'Required reflected roof graph API absent: '+cls)
    return enums, reflection


def _import_textures(u, source):
    p = policy();snapshot = p.snapshots();assets = u.EditorAssetLibrary
    textures, records = {}, {}
    require(set(source['source']['originalMaps']) == {'diffuse', 'normalGL', 'roughness'}, 'Only three original maps required')
    for channel, original in source['source']['originalMaps'].items():
        path = source['proposedAssets'][channel];package, name = path.rsplit('.', 1)
        require(not assets.does_asset_exist(package), 'Fresh own roof texture namespace required')
        task = u.AssetImportTask()
        for key, value in {'filename': original['path'], 'destination_path': package.rsplit('/', 1)[0],
            'destination_name': name, 'automated': True, 'replace_existing': False, 'save': False}.items():
            task.set_editor_property(key, value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);texture = assets.load_asset(package)
        require(isinstance(texture, u.Texture2D) and texture.get_path_name() == path, 'Original map import identity differs')
        role = 'normal' if channel == 'normalGL' else channel
        for key, value in p.texture_values(u, role).items(): texture.set_editor_property(key, value)
        down = texture.get_editor_property('downscale');down.set_editor_property('default', 1.)
        down.set_editor_property('per_platform', {});texture.set_editor_property('downscale', down)
        texture.set_editor_property('alpha_coverage_thresholds', u.Vector4(0., 0., 0., 0.))
        color = texture.get_editor_property('source_color_settings')
        color.set_editor_property('encoding_override', p.api().enum(u, 'TextureSourceEncoding',
            'TSESRGB' if channel == 'diffuse' else 'TSENONE'));texture.set_editor_property('source_color_settings', color)
        meta = metadata(u, texture, channel, original, True);observed = snapshot.texture_snapshot(u, texture)
        p.check_texture(u, observed, role, path)
        textures[channel] = texture
        records[channel] = {'asset': path, 'source': original, 'metadata': meta, 'snapshot': observed,
            'snapshotSha256': digest(observed),
            'native16BitSourcePrecisionVerified': False, 'nativePixelFormatOrTexelsReadBack': False}
    return textures, records


def _build(u, source, textures, graph_snapshot):
    p = policy();d = p.api();c = contract();lib = u.MaterialEditingLibrary;assets = u.EditorAssetLibrary
    path = source['proposedAssets']['material'];package, name = path.rsplit('.', 1)
    require(not assets.does_asset_exist(package), 'Fresh own roof material required')
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(name, package.rsplit('/', 1)[0], u.Material, u.MaterialFactoryNew())
    require(isinstance(material, u.Material) and material.get_path_name() == path, 'Own roof material creation failed')
    for key, value in {'blend_mode': u.BlendMode.BLEND_OPAQUE,
        'shading_model': d.enum(u, 'MaterialShadingModel', 'DEFAULTLIT'), 'two_sided': False,
        'tangent_space_normal': True, 'use_material_attributes': False}.items(): material.set_editor_property(key, value)
    def node(role, cls, **values):
        obj = lib.create_material_expression(material, cls, -700, 0);require(obj, 'Own roof expression creation failed')
        obj.set_editor_property('desc', c.TAG+role)
        for key, value in values.items(): obj.set_editor_property(key, value)
        return obj
    uv = node('uv', u.MaterialExpressionTextureCoordinate, coordinate_index=0, u_tiling=.25, v_tiling=-.25)
    samples = {}
    for channel, sampler in (('diffuse', 'SAMPLERTYPECOLOR'), ('normalGL', 'SAMPLERTYPENORMAL'), ('roughness', 'SAMPLERTYPEMASKS')):
        samples[channel] = node(channel, u.MaterialExpressionTextureSample, texture=textures[channel],
            sampler_type=d.enum(u, 'MaterialSamplerType', sampler))
        require(lib.connect_material_expressions(uv, '', samples[channel], 'UVs'), 'Shared original reflected UV link failed')
    sign = node('reflectionSign', u.MaterialExpressionConstant3Vector, constant=u.LinearColor(1., -1., 1., 1.))
    normal = node('normalReflection', u.MaterialExpressionMultiply)
    require(lib.connect_material_expressions(samples['normalGL'], 'RGB', normal, 'A')
        and lib.connect_material_expressions(sign, '', normal, 'B'), 'Decoded tangent-normal reflection link failed')
    metallic = node('metallic', u.MaterialExpressionConstant, r=0.);specular = node('specular', u.MaterialExpressionConstant, r=.5)
    for obj, output, prop in ((samples['diffuse'], 'RGB', 'BASE_COLOR'), (samples['roughness'], 'R', 'ROUGHNESS'),
        (normal, '', 'NORMAL'), (metallic, '', 'METALLIC'), (specular, '', 'SPECULAR')):
        require(lib.connect_material_property(obj, output, getattr(u.MaterialProperty, 'MP_'+prop)), 'Own roof PBR root link failed')
    meta = metadata(u, material, 'material', write=True)
    errors = list(lib.recompile_material(material) or []);require(errors == [], 'Own roof compile errors: '+str(errors))
    graph = graph_snapshot(u, material);audit = kernel().validate_graph(graph, source)
    flags = p.material_policy(u, material)
    require(graph['flags'] == flags, 'Full own roof graph/material flag readback differs')
    return material, {'asset': path, 'graph': graph, 'graphSha256': digest(graph), 'graphAudit': audit,
        'policy': flags, 'aux': p.snapshots().aux_snapshot(u, material), 'metadata': meta, 'compileErrors': errors}


def build_materials(u, bundle, binding, graph_snapshot):
    source = validate_binding(bundle, binding);enums, reflection = preflight(u)
    # All four names are rejected before importing any original map.
    require(all(not u.EditorAssetLibrary.does_asset_exist(a.split('.')[0]) for a in source['proposedAssets'].values()),
        'Fresh exact four-package roof namespace required')
    textures, records = _import_textures(u, source);material, row = _build(u, source, textures, graph_snapshot)
    packages = sorted(source['proposedAssets'].values());require(len(packages) == len(set(packages)) == 4, 'Only roof graph+three textures')
    for obj in [*textures.values(), material]:
        require(u.EditorAssetLibrary.save_loaded_asset(obj, only_if_is_dirty=False), 'Cannot save owned roof material/texture package')
    return material, {'schema': SCHEMA, 'schemaVersion': 1, 'owner': OWNER, 'nativeBinding': binding,
        'sourceProposal': bundle['source']['roof']['proposalPin'], 'material': row, 'textures': records,
        'newPackageAssets': packages, 'newMaterialGraphs': 1, 'newTextureObjects': 3,
        'fourOwnedPackagesSaved': True, 'nativeEnumPreflight': enums, 'reflectionPreflight': reflection,
        'pureApiSources': [pin(POLICY), pin(CONTRACT), pin(KERNEL)], **LIMITS}


def verify_materials(u, bundle, binding, report, graph_snapshot):
    source = validate_binding(bundle, binding);p = policy();snapshot = p.snapshots()
    require(report['schema'] == SCHEMA and report['schemaVersion'] == 1 and report['owner'] == OWNER
        and report['nativeBinding'] == binding and report['sourceProposal'] == bundle['source']['roof']['proposalPin']
        and report['newPackageAssets'] == sorted(source['proposedAssets'].values())
        and report['newMaterialGraphs'] == 1 and report['newTextureObjects'] == 3
        and report['fourOwnedPackagesSaved'] is True and set(report['textures']) == {'diffuse', 'normalGL', 'roughness'}
        and report['pureApiSources'] == [pin(POLICY), pin(CONTRACT), pin(KERNEL)], 'Exact complete saved R46 roof receipt required')
    for key, value in LIMITS.items(): require(report[key] is value, 'Owned roof evidence limit changed')
    require(report['nativeEnumPreflight'] == p.preflight_enums(u), 'Saved native roof enums differ')
    row = report['material'];material = u.EditorAssetLibrary.load_asset(source['proposedAssets']['material'])
    require(isinstance(material, u.Material) and material.get_path_name() == row['asset'] == source['proposedAssets']['material'],
        'Saved own roof material identity differs')
    graph = graph_snapshot(u, material);flags = p.material_policy(u, material)
    require(graph == row['graph'] and digest(graph) == row['graphSha256'] and graph['flags'] == flags == row['policy']
        and kernel().validate_graph(graph, source) == row['graphAudit'] and row['compileErrors'] == []
        and snapshot.aux_snapshot(u, material) == row['aux'] and metadata(u, material, 'material') == row['metadata'],
        'Saved full roof graph/five flags/auxiliary/metadata differs')
    for channel, texture_row in report['textures'].items():
        original = source['source']['originalMaps'][channel];path = source['proposedAssets'][channel]
        require(texture_row['asset'] == path and texture_row['source'] == original
            and texture_row['native16BitSourcePrecisionVerified'] is False
            and texture_row['nativePixelFormatOrTexelsReadBack'] is False, 'Original saved map source/evidence differs')
        texture = u.EditorAssetLibrary.load_asset(path);require(isinstance(texture, u.Texture2D)
            and texture.get_path_name() == path, 'Saved original-map identity differs')
        observed = snapshot.texture_snapshot(u, texture)
        require(observed == texture_row['snapshot'] and digest(observed) == texture_row['snapshotSha256']
            and metadata(u, texture, channel, original) == texture_row['metadata'],
            'Saved complete visible24 map settings/metadata differs')
        p.check_texture(u, observed, 'normal' if channel == 'normalGL' else channel, path)
    return material


if __name__ == '__main__':
    raise RuntimeError('R46 roof helper has no standalone native entry; final image/clone binding is pending')
