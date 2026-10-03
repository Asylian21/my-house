"""AST-only R45 texture/material/four-slot kernels; every mutation entry is blocked.

These kernels cannot select a base, save a map or launch Unreal. The future
bound owner must authenticate complete old scene/raw/material/texture controls
and independently prove the saved four-slot counterfactual and map+4 delta.
"""
import hashlib
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-clay-roof-photo-native-r45-draft.py'
CONTRACT = ROOT/'scripts/unreal/exterior-clay-roof-photo-contract-r45-draft.py'
POLICY = ROOT/'scripts/unreal/exterior-context-parcel-boundary-materials-r43.py'
POLICY_SHA = 'fad70bfdd0bd7b9eff2ee289f20a47b1c3d717b7bb683eecbe8d59ff72f873d9'


def module(name, path, expected=None):
    if expected is not None and hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise RuntimeError('Immutable primary/proven visible-policy helper differs')
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


g = module('_r45_unbound_source_contract', CONTRACT)


def require(ok, message):
    if not ok: raise RuntimeError(message)


def _metadata(u, obj, role, source=None, write=False):
    if write: g.require_native_binding()
    expected = {'BreziGeneratedBy': OWNER, 'BreziSourcePlanSha256': g.PROPOSAL_SHA,
        'BreziR45Role': role, 'BreziSourceLicense': 'CC0-1.0'}
    if source is not None: expected['BreziSourceSha256'] = source['sha256']
    for key, value in expected.items():
        if write: u.EditorAssetLibrary.set_metadata_tag(obj, key, value)
        require(u.EditorAssetLibrary.get_metadata_tag(obj, key) == value, 'Own R45 provenance metadata differs')
    return expected


def _texture_policy(u, channel):
    # Immutable helper supplies only neutral, supported visible24 values and
    # primary enum routing. Ownership, pixels and materials are never delegated.
    policy = module('_r45_immutable_visible_policy', POLICY, POLICY_SHA)
    return policy, policy.texture_values(u, 'normal' if channel == 'normalGL' else channel)


def _import_textures_kernel(u, source, texture_snapshot):
    g.require_native_binding()  # Before any UObject/CDO/import operation.
    policy = module('_r45_immutable_visible_policy', POLICY, POLICY_SHA)
    policy.preflight_enums(u); policy.preflight_reflection(u)
    textures, records = {}, {}
    for channel, original in source['source']['originalMaps'].items():
        path = source['proposedAssets'][channel]; package, name = path.rsplit('.', 1)
        require(not u.EditorAssetLibrary.does_asset_exist(package), 'Fresh own texture namespace required')
        task = u.AssetImportTask()
        for key, value in {'filename': original['path'], 'destination_path': package.rsplit('/', 1)[0],
            'destination_name': name, 'automated': True, 'replace_existing': False, 'save': False}.items():
            task.set_editor_property(key, value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture = u.EditorAssetLibrary.load_asset(package)
        require(isinstance(texture, u.Texture2D) and texture.get_path_name() == path, 'Original map import identity differs')
        _, values = _texture_policy(u, channel)
        for key, value in values.items(): texture.set_editor_property(key, value)
        down = texture.get_editor_property('downscale'); down.set_editor_property('default', 1.)
        down.set_editor_property('per_platform', {}); texture.set_editor_property('downscale', down)
        texture.set_editor_property('alpha_coverage_thresholds', u.Vector4(0., 0., 0., 0.))
        color = texture.get_editor_property('source_color_settings')
        color.set_editor_property('encoding_override', policy.api().enum(u, 'TextureSourceEncoding',
            'TSESRGB' if channel == 'diffuse' else 'TSENONE'))
        texture.set_editor_property('source_color_settings', color)
        meta = _metadata(u, texture, channel, original, True)
        observed = texture_snapshot(u, texture)
        policy.check_texture(u, observed, 'normal' if channel == 'normalGL' else channel, path)
        textures[channel] = texture
        records[channel] = {'asset': path, 'source': original, 'metadata': meta, 'snapshot': observed,
            'native16BitSourcePrecisionVerified': False, 'nativePixelFormatOrTexelsReadBack': False}
    require(set(textures) == {'diffuse', 'normalGL', 'roughness'}, 'Only the three original maps may be imported')
    return textures, records


def validate_graph(graph, source):
    tag = g.TAG; nodes = {n['role']: n for n in graph['nodes']}
    roles = ('uv', 'diffuse', 'normalGL', 'roughness', 'reflectionSign', 'normalReflection', 'metallic', 'specular')
    require(len(nodes) == len(graph['nodes']) == 8 and set(nodes) == {tag+r for r in roles}, 'Exactly eight own graph nodes required')
    require(nodes[tag+'uv']['class'] == 'MaterialExpressionTextureCoordinate'
        and nodes[tag+'uv']['values'] == {'coordinate_index': 0, 'u_tiling': .25, 'v_tiling': -.25},
        'Original UV0 must only undergo explicit metric V reflection in the shader')
    require(nodes[tag+'reflectionSign']['class'] == 'MaterialExpressionConstant3Vector'
        and nodes[tag+'reflectionSign']['values'] == {'constant': [1., -1., 1., 1.]},
        'Decoded normal Y correction must remain separate from GL import green flip')
    for channel, sampler in (('diffuse', 'SAMPLERTYPE_COLOR'), ('normalGL', 'SAMPLERTYPE_NORMAL'), ('roughness', 'SAMPLERTYPE_MASKS')):
        n = nodes[tag+channel]
        require(n['class'] == 'MaterialExpressionTextureSample' and n['values']['texture'] == source['proposedAssets'][channel]
            and sampler in n['values']['sampler_type']
            and n['inputs'] == [['UVs', tag+'uv', ''], ['Tex', None, None], ['Apply View MipBias', None, None]],
            'Every original sample must share the same reflected UV0')
    require(nodes[tag+'normalReflection']['class'] == 'MaterialExpressionMultiply'
        and nodes[tag+'normalReflection']['inputs'] == [['A', tag+'normalGL', 'RGB'], ['B', tag+'reflectionSign', '']],
        'Normal reflection must act on the decoded tangent normal')
    for key, scalar in (('metallic', 0.), ('specular', .5)):
        require(nodes[tag+key]['class'] == 'MaterialExpressionConstant' and nodes[tag+key]['values'] == {'r': scalar},
            'Declared uncalibrated opaque dielectric constant differs')
    roots = {'BASE_COLOR': [tag+'diffuse', 'RGB'], 'ROUGHNESS': [tag+'roughness', 'R'],
        'NORMAL': [tag+'normalReflection', ''], 'METALLIC': [tag+'metallic', ''], 'SPECULAR': [tag+'specular', '']}
    require(all(graph['roots'][key] == value for key, value in roots.items())
        and all(value is None for key, value in graph['roots'].items() if key not in roots),
        'Only declared PBR roots; no displacement/WPO/AO/opacity/tint')
    return {'nodeCount': 8, 'photoUvScale': [.25, -.25], 'decodedTangentNormalSign': [1, -1, 1],
        'meshUvAndTangentFrameEdited': False, 'nativeNormalAppearanceVerified': False,
        'ridgeCourseContinuityVerified': False}


def _build_material_kernel(u, source, textures, graph_snapshot):
    g.require_native_binding()  # This draft cannot be activated by caller data.
    policy = module('_r45_immutable_visible_policy', POLICY, POLICY_SHA); d = policy.api(); lib = u.MaterialEditingLibrary
    path = source['proposedAssets']['material']; package, name = path.rsplit('.', 1)
    require(not u.EditorAssetLibrary.does_asset_exist(package), 'Fresh own material namespace required')
    m = u.AssetToolsHelpers.get_asset_tools().create_asset(name, package.rsplit('/', 1)[0], u.Material, u.MaterialFactoryNew())
    require(isinstance(m, u.Material), 'Own material creation failed')
    for key, value in {'blend_mode': u.BlendMode.BLEND_OPAQUE,
        'shading_model': d.enum(u, 'MaterialShadingModel', 'DEFAULTLIT'), 'two_sided': False,
        'tangent_space_normal': True, 'use_material_attributes': False}.items(): m.set_editor_property(key, value)
    def node(role, cls, **values):
        obj = lib.create_material_expression(m, cls, -700, 0); require(obj, 'Own expression creation failed')
        obj.set_editor_property('desc', g.TAG+role)
        for key, value in values.items(): obj.set_editor_property(key, value)
        return obj
    uv = node('uv', u.MaterialExpressionTextureCoordinate, coordinate_index=0, u_tiling=.25, v_tiling=-.25)
    samples = {}
    for channel, sampler in (('diffuse', 'SAMPLERTYPECOLOR'), ('normalGL', 'SAMPLERTYPENORMAL'), ('roughness', 'SAMPLERTYPEMASKS')):
        samples[channel] = node(channel, u.MaterialExpressionTextureSample, texture=textures[channel],
            sampler_type=d.enum(u, 'MaterialSamplerType', sampler))
        require(lib.connect_material_expressions(uv, '', samples[channel], 'UVs'), 'Shared reflected UV link failed')
    sign = node('reflectionSign', u.MaterialExpressionConstant3Vector, constant=u.LinearColor(1., -1., 1., 1.))
    normal = node('normalReflection', u.MaterialExpressionMultiply)
    require(lib.connect_material_expressions(samples['normalGL'], 'RGB', normal, 'A')
        and lib.connect_material_expressions(sign, '', normal, 'B'), 'Decoded tangent normal reflection link failed')
    metallic = node('metallic', u.MaterialExpressionConstant, r=0.)
    specular = node('specular', u.MaterialExpressionConstant, r=.5)
    for obj, output, prop in ((samples['diffuse'], 'RGB', 'BASE_COLOR'), (samples['roughness'], 'R', 'ROUGHNESS'),
        (normal, '', 'NORMAL'), (metallic, '', 'METALLIC'), (specular, '', 'SPECULAR')):
        require(lib.connect_material_property(obj, output, getattr(u.MaterialProperty, 'MP_'+prop)), 'Own PBR root link failed')
    errors = list(lib.recompile_material(m) or []); require(not errors, 'Own material compile errors: '+str(errors))
    graph = graph_snapshot(u, m); audit = validate_graph(graph, source); meta = _metadata(u, m, 'material', write=True)
    return m, {'asset': path, 'graph': graph, 'graphSha256': g.digest(graph), 'graphAudit': audit,
        'metadata': meta, 'compileErrors': errors, 'nativeNormalTangentNumericReadbackPerformed': False,
        'nativeOpticalCalibrationVerified': False, 'nativeAppearanceAccepted': False}


def _apply_four_slots_kernel(u, source, target_components, material):
    g.require_native_binding()
    require(set(target_components) == {t['component'] for t in source['targets']}
        and material.get_path_name() == source['proposedAssets']['material'], 'Exactly four authenticated targets required')
    for target in source['targets']:
        component = target_components[target['component']]
        require(component.get_path_name() == target['component']
            and component.get_editor_property('static_mesh').get_path_name() == target['currentMesh']
            and component.get_num_materials() == 1
            and component.get_material(0).get_path_name() == target['currentMaterial'], 'Before-set target mesh/slot differs')
    for target in source['targets']:
        target_components[target['component']].set_material(0, material)
    return {'changedComponents': [t['component'] for t in source['targets']], 'onlySlot': 0,
        'oldMeshDefaultMaterialSettersCalled': False, 'oldGeometryRootOrCollisionSettersCalled': False}


def import_textures(*args, **kwargs):
    g.require_native_binding()


def build_materials(*args, **kwargs):
    g.require_native_binding()


def apply(*args, **kwargs):
    g.require_native_binding()


if __name__ == '__main__':
    g.require_native_binding()
