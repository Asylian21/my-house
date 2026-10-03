"""R20-only original PH grass maps with explicit sidecar-alpha foliage graph."""
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-curved-grass-materials.py'
PREFIX = '/Game/Brezi/CurvedGrass20261001R20'
TAG = 'BreziCurvedGrassR20:'
KEY = 'ph_original_grass_medium_01_r20'
SOURCE = ROOT / 'output/unreal/exterior-ph-vegetation-reference-20261001-r1/grass_medium_01/textures'
FILES = {
    'albedo': ('grass_medium_01_diff_2k.jpg', 'f768aa68daf14f37a92dd96621628a5252b169f4d94b4d1cc830d62cd3ac9e68'),
    'normal': ('grass_medium_01_nor_gl_2k.jpg', '245349ce6d1910b3b7474da6013452a5be993f9058be78e17171a0866a6889e9'),
    'arm': ('grass_medium_01_arm_2k.jpg', '7b593b1c470c1817b937bb3ca00da7e4b27ca00120e98b06b43bb3a7d5810aa1'),
    'alpha': ('grass_medium_01_alpha_2k.png', '4af2c3d5ebf167764ad3746f8c925dc4fbe28f0df023656599123cb593b793dd')}


def require(ok, message):
    if not ok: raise RuntimeError(message)


def f32(v): return struct.unpack('<f', struct.pack('<f', v))[0]


def canonical_recipe():
    return {'id': KEY, 'kind': 'original-polyhaven-curved-grass-masked-foliage',
        'maps': {role: {'path': str(SOURCE / name), 'sha256': digest} for role, (name, digest) in FILES.items()},
        'sourcePage': 'https://polyhaven.com/a/grass_medium_01', 'sourceLicense': 'CC0-1.0',
        'evidence': 'Original external model and photographic maps; no whole-plant scan claim.',
        'uvChannel': 0, 'providerSourceAlphaMode': 'BLEND', 'providerDiffuseAlphaIsOne': True,
        'nativeBlend': 'MASKED', 'nativeShading': 'TWOSIDEDFOLIAGE', 'twoSided': True,
        'explicitOpacitySource': 'alpha.R', 'opacityMaskClipValue': .5,
        'normalConvention': 'OPENGL', 'nativeNormalGreenFlip': True,
        'armChannels': {'R': 'AMBIENT_OCCLUSION', 'G': 'ROUGHNESS', 'B': 'METALLIC'},
        'providerMetallicFactor': 0., 'providerRoughnessFactor': 1., 'providerNormalScale': 1.,
        'providerBaseColorFactor': [1., 1., 1., 1.], 'aoMultipliedIntoBaseColor': False,
        'ueOnlySubsurfaceScale': .08, 'ueOnlySpecular': .5,
        'ueOnlyCalibrationNativeAppearanceAccepted': False, 'cameraFade': None, 'windDisplacementCm': 0,
        'sourcePixelsEdited': False, 'nativeApplied': False, 'nativeAppearanceAccepted': False}


def validate_recipe(recipe):
    require(recipe == canonical_recipe(), 'Original PH graph recipe/routes broadened or changed')
    for spec in recipe['maps'].values():
        source = Path(spec['path'])
        require(source.is_file() and not source.is_symlink()
                and hashlib.sha256(source.read_bytes()).hexdigest() == spec['sha256'], 'Original PH photographic source changed')
    return {'maps': 4, 'newMaterials': 1, 'explicitSeparateAlphaPngRequired': True,
            'normalGLGreenFlipRequired': True, 'armAOSeparatedFromAlbedo': True,
            'sourcePixelsEdited': False, 'nativeApplied': False}


def enum(u, group, name):
    target = name.replace('_', '').lower()
    matches = [getattr(getattr(u, group), n) for n in dir(getattr(u, group)) if n.replace('_', '').lower() == target]
    require(len(matches) == 1, 'Native enum unavailable/ambiguous: ' + group + '.' + name)
    return matches[0]


def texture_snapshot(tex):
    keys = ('srgb', 'flip_green_channel', 'compression_settings', 'address_x', 'address_y', 'lod_bias',
            'max_texture_size', 'virtual_texture_streaming', 'never_stream', 'mip_gen_settings',
            'power_of_two_mode', 'do_scale_mips_for_alpha_coverage')
    values = {}
    for key in keys:
        value = tex.get_editor_property(key)
        values[key] = value if isinstance(value, (bool, int, float, str)) else str(value)
    values['alphaCoverageThresholds'] = [float(getattr(tex.get_editor_property('alpha_coverage_thresholds'), axis)) for axis in 'xyzw']
    values['sourceEncoding'] = str(tex.get_editor_property('source_color_settings').get_editor_property('encoding_override'))
    values['pixels'] = [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()]
    return values


def check_graph(graph, texture_assets):
    require(set(texture_assets) == set(FILES), 'Exactly four original photographic map roles required')
    require(graph['roots']['BASE_COLOR'] == [TAG+'albedo', 'RGB']
            and graph['roots']['NORMAL'] == [TAG+'normal', 'RGB']
            and graph['roots']['OPACITY_MASK'] == [TAG+'alpha', 'R']
            and graph['roots']['AMBIENT_OCCLUSION'] == [TAG+'arm', 'R']
            and graph['roots']['ROUGHNESS'] == [TAG+'arm', 'G']
            and graph['roots']['METALLIC'] == [TAG+'metallic-provider-factor', '']
            and graph['roots']['SUBSURFACE_COLOR'] == [TAG+'ue-foliage-transmission', '']
            and graph['roots']['SPECULAR'] == [TAG+'ue-dielectric-specular', ''], 'Actual material map channels/roots differ')
    require(all(value is None for key, value in graph['roots'].items() if key not in
        ('BASE_COLOR','NORMAL','OPACITY_MASK','AMBIENT_OCCLUSION','ROUGHNESS','METALLIC','SUBSURFACE_COLOR','SPECULAR')),
        'Unexpected opacity/displacement/emissive material route')
    nodes = {node['role']: node for node in graph['nodes']}
    require(len(nodes) == 10, 'Unexpected foliage graph node')
    require(len(graph['nodes']) == 10, 'Duplicate foliage graph role')
    for role, asset in texture_assets.items():
        node = nodes[TAG+role]
        require(node['class'] == 'MaterialExpressionTextureSample' and node['values']['texture'] == asset,
                'Actual foliage map bound to another texture')
        require(node['inputs'] == [['UVs', TAG+'original-UV0', ''], ['Tex', None, None],
                                    ['Apply View MipBias', None, None]], 'Original UV0 map route differs')
    require(nodes[TAG+'original-UV0']['values'] == {'coordinate_index': 0, 'u_tiling': 1., 'v_tiling': 1.},
            'Original photographic UV scale/channel changed')
    require(nodes[TAG+'metallic-provider-factor']['inputs'] == [['A', TAG+'arm', 'B'], ['B', TAG+'provider-metallic-zero', '']],
            'Original metallic factor/channels differ')
    require(nodes[TAG+'provider-metallic-zero']['values']['r'] == 0.
            and nodes[TAG+'ue-subsurface-strength']['values']['r'] == f32(.08)
            and nodes[TAG+'ue-dielectric-specular']['values']['r'] == .5,
            'Actual physical/calibration constants differ')
    require(nodes[TAG+'ue-foliage-transmission']['inputs'] == [['A', TAG+'albedo', 'RGB'], ['B', TAG+'ue-subsurface-strength', '']],
            'Actual foliage transmission route differs')


def build_materials(u, recipe, existing_graph_snapshot):
    validate_recipe(recipe)
    assets, lib = u.EditorAssetLibrary, u.MaterialEditingLibrary
    textures, reports = {}, {}
    for role, spec in recipe['maps'].items():
        name = 'T_R20_PhGrass_' + role + '_' + spec['sha256'][:16]
        path = PREFIX + '/Textures/' + name
        require(not assets.does_asset_exist(path), 'Fresh R20 texture namespace required')
        task = u.AssetImportTask()
        for key, value in {'filename': spec['path'], 'destination_path': PREFIX+'/Textures', 'destination_name': name,
                           'automated': True, 'replace_existing': False, 'save': False}.items(): task.set_editor_property(key, value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = assets.load_asset(path)
        require(isinstance(tex, u.Texture2D), 'Cannot import actual original texture')
        compression = enum(u, 'TextureCompressionSettings', 'TCNormalmap' if role == 'normal' else 'TCMasks' if role in ('arm', 'alpha') else 'TCDefault')
        for key, value in {'srgb': role == 'albedo', 'flip_green_channel': role == 'normal', 'compression_settings': compression,
            'address_x': u.TextureAddress.TA_WRAP, 'address_y': u.TextureAddress.TA_WRAP, 'lod_bias': 0,
            'max_texture_size': 0, 'virtual_texture_streaming': False, 'never_stream': False,
            'mip_gen_settings': u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP, 'power_of_two_mode': u.TexturePowerOfTwoSetting.NONE,
            'do_scale_mips_for_alpha_coverage': role == 'alpha',
            'alpha_coverage_thresholds': u.Vector4(.5, 0, 0, 0) if role == 'alpha' else u.Vector4(0, 0, 0, 0)}.items():
            tex.set_editor_property(key, value)
        color = tex.get_editor_property('source_color_settings')
        color.set_editor_property('encoding_override', enum(u, 'TextureSourceEncoding', 'TSESRGB' if role == 'albedo' else 'TSENONE'))
        tex.set_editor_property('source_color_settings', color)
        for key, value in {'BreziGeneratedBy': OWNER, 'source_sha256': spec['sha256'], 'BreziSourceLicense': 'CC0-1.0',
                           'BreziSourcePage': recipe['sourcePage'], 'BreziR20SourceRole': role}.items(): assets.set_metadata_tag(tex, key, value)
        require(assets.save_loaded_asset(tex, only_if_is_dirty=False), 'Cannot save original-map R20 texture')
        snapshot = texture_snapshot(tex)
        require(snapshot['pixels'] == [2048, 2048], 'Actual original map dimensions differ')
        textures[role] = tex
        reports[role] = {'asset': tex.get_path_name(), 'source': spec, 'role': role, 'snapshot': snapshot}
    name = 'M_' + KEY
    require(not assets.does_asset_exist(PREFIX+'/Materials/'+name), 'Fresh R20 Material required')
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(name, PREFIX+'/Materials', u.Material, u.MaterialFactoryNew())
    require(isinstance(material, u.Material), 'Cannot create R20 foliage Material')
    for key, value in {'blend_mode': u.BlendMode.BLEND_MASKED, 'shading_model': enum(u, 'MaterialShadingModel', 'TWOSIDEDFOLIAGE'),
            'two_sided': True, 'tangent_space_normal': True, 'use_material_attributes': False, 'opacity_mask_clip_value': .5}.items():
        material.set_editor_property(key, value)
    lib.set_base_material_usage(material, enum(u, 'MaterialUsage', 'INSTANCEDSTATICMESHES'), True)
    def node(role, cls, **values):
        result = lib.create_material_expression(material, cls, -600, 0)
        require(result is not None, 'Cannot create original grass expression')
        result.set_editor_property('desc', TAG+role)
        for key, value in values.items(): result.set_editor_property(key, value)
        return result
    def connect(a, channel, b, input_name):
        require(lib.connect_material_expressions(a, channel, b, input_name), 'Cannot connect original grass graph')
    def root(a, channel, property_name):
        require(lib.connect_material_property(a, channel, getattr(u.MaterialProperty, 'MP_'+property_name)), 'Cannot connect grass material root')
    uv = node('original-UV0', u.MaterialExpressionTextureCoordinate, coordinate_index=0, u_tiling=1., v_tiling=1.)
    samples = {}
    for role, texture in textures.items():
        sampler = enum(u, 'MaterialSamplerType', 'SAMPLERTYPENORMAL' if role == 'normal' else 'SAMPLERTYPEMASKS' if role in ('arm', 'alpha') else 'SAMPLERTYPECOLOR')
        sample = node(role, u.MaterialExpressionTextureSample, texture=texture, sampler_type=sampler)
        connect(uv, '', sample, 'UVs')
        samples[role] = sample
    metallic = node('metallic-provider-factor', u.MaterialExpressionMultiply)
    zero = node('provider-metallic-zero', u.MaterialExpressionConstant, r=0.)
    connect(samples['arm'], 'B', metallic, 'A'); connect(zero, '', metallic, 'B')
    strength = node('ue-subsurface-strength', u.MaterialExpressionConstant, r=.08)
    transmission = node('ue-foliage-transmission', u.MaterialExpressionMultiply)
    connect(samples['albedo'], 'RGB', transmission, 'A'); connect(strength, '', transmission, 'B')
    specular = node('ue-dielectric-specular', u.MaterialExpressionConstant, r=.5)
    for source, channel, property_name in [(samples['albedo'], 'RGB', 'BASE_COLOR'), (samples['normal'], 'RGB', 'NORMAL'),
        (samples['alpha'], 'R', 'OPACITY_MASK'), (samples['arm'], 'R', 'AMBIENT_OCCLUSION'),
        (samples['arm'], 'G', 'ROUGHNESS'), (metallic, '', 'METALLIC'), (transmission, '', 'SUBSURFACE_COLOR'), (specular, '', 'SPECULAR')]:
        root(source, channel, property_name)
    errors = list(lib.recompile_material(material) or [])
    require(not errors, 'Actual original grass graph compilation errors: ' + str(errors))
    for key, value in {'BreziGeneratedBy': OWNER, 'BreziR20Recipe': json.dumps(recipe, sort_keys=True),
                       'BreziR20AlphaSource': recipe['maps']['alpha']['sha256']}.items(): assets.set_metadata_tag(material, key, value)
    require(assets.save_loaded_asset(material, only_if_is_dirty=False), 'Cannot save original grass Material')
    graph = existing_graph_snapshot(u, material)
    check_graph(graph, {role: tex.get_path_name() for role, tex in textures.items()})
    return material, {'owner': OWNER, 'asset': material.get_path_name(), 'recipe': recipe, 'graph': graph,
        'shaderCompileErrors': errors, 'textures': reports, 'nativeAppearanceAccepted': False}


def verify_materials(u, report, existing_graph_snapshot):
    require(report['owner'] == OWNER and report['shaderCompileErrors'] == [], 'Unverified original grass graph report')
    require(set(report['textures']) == set(FILES), 'Unexpected original grass texture population')
    validate_recipe(report['recipe'])
    material = u.EditorAssetLibrary.load_asset(report['asset'])
    require(isinstance(material, u.Material) and material.get_path_name() == PREFIX+'/Materials/M_'+KEY+'.M_'+KEY,
            'Saved original grass Material missing/foreign')
    require(existing_graph_snapshot(u, material) == report['graph'], 'Saved grass graph changed')
    require(u.EditorAssetLibrary.get_metadata_tag(material, 'BreziR20Recipe') == json.dumps(report['recipe'], sort_keys=True),
            'Saved typed original grass recipe changed')
    require(u.EditorAssetLibrary.get_metadata_tag(material, 'BreziGeneratedBy') == OWNER
            and u.EditorAssetLibrary.get_metadata_tag(material, 'BreziR20AlphaSource') == FILES['alpha'][1],
            'Saved original grass Material owner/alpha proof differs')
    require(material.get_editor_property('blend_mode') == u.BlendMode.BLEND_MASKED
            and material.get_editor_property('shading_model') == enum(u, 'MaterialShadingModel', 'TWOSIDEDFOLIAGE')
            and material.get_editor_property('two_sided') is True and float(material.get_editor_property('opacity_mask_clip_value')) == .5
            and material.get_editor_property('tangent_space_normal') is True
            and material.get_editor_property('use_material_attributes') is False
            and u.MaterialEditingLibrary.has_material_usage(material, enum(u, 'MaterialUsage', 'INSTANCEDSTATICMESHES')),
            'Saved masked foliage interpretation changed')
    for role, row in report['textures'].items():
        require(row['role'] == role and row['source'] == report['recipe']['maps'][role], 'Foreign map receipt role/source')
        texture = u.EditorAssetLibrary.load_asset(row['asset'])
        require(isinstance(texture, u.Texture2D) and texture_snapshot(texture) == row['snapshot'], 'Saved original texture settings changed')
        require(u.EditorAssetLibrary.get_metadata_tag(texture, 'source_sha256') == row['source']['sha256']
                and u.EditorAssetLibrary.get_metadata_tag(texture, 'BreziGeneratedBy') == OWNER
                and u.EditorAssetLibrary.get_metadata_tag(texture, 'BreziR20SourceRole') == role
                and u.EditorAssetLibrary.get_metadata_tag(texture, 'BreziSourceLicense') == 'CC0-1.0', 'Saved map provenance changed')
    check_graph(report['graph'], {role: row['asset'] for role, row in report['textures'].items()})
    return material
