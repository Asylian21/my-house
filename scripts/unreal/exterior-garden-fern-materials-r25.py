"""NEW R25 draft: one original Fern02 masked graph and four unchanged maps.

Source pixels are never converted or baked. The published 16-bit grayscale
alpha is sampled through normalized R; its source precision is distinct from
the unavailable native source/GPU pixel-format readback. TwoSidedFoliage and
the .08 transmission value are artistic UE settings, not measured optics.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-fern-materials-r25.py'
PREFIX = '/Game/Brezi/GardenFern20261002R25'
KEY = 'ph_original_fern_02_b_r25'
TAG = 'BreziGardenFernR25:'
SOURCE = ROOT/'output/unreal/exterior-garden-fern-20261002-r25-study/fern-pilot-source-plan.json'
SOURCE_SHA = 'b3c1453765e310a47416507236c24adff2b3517b4bacd5a882fefa5c0df9709b'
SOURCE_OWNER = 'scripts/unreal/exterior-garden-fern-study-r25.py'
SOURCE_PRODUCER_SHA = '30c08165145f91adcfca1d89ee33a6528445ec1b535b1c8e4c6e3d6922fd408e'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def checked(row):
    path = Path(row['path']).resolve()
    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == row['sha256']
            and path.stat().st_size == row['bytes'], 'Original fern map pin changed: '+str(path))
    return path


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def token(value):
    return str(value).split('.')[1].split(':')[0].replace('_', '').upper()


def enum(u, group, name):
    """Resolve only the installed enum spelling, including its known prefix."""
    key = name.replace('_', '').lower()
    prefix = {'MaterialShadingModel': 'msm', 'MaterialUsage': 'matusage'}.get(group, '')
    def normalized(symbol):
        value = symbol.replace('_', '').lower()
        return value[len(prefix):] if prefix and value.startswith(prefix) else value
    matches = [getattr(getattr(u, group), symbol) for symbol in dir(getattr(u, group))
               if normalized(symbol) == key]
    require(len(matches) == 1, 'Native enum missing/ambiguous '+group+'.'+name)
    return matches[0]


def preflight_enums(u):
    """Complete narrow enum surface; callable before any scene/asset change."""
    pairs = [('MaterialShadingModel', 'TWOSIDEDFOLIAGE'),
        ('MaterialUsage', 'INSTANCEDSTATICMESHES'),
        ('TextureCompressionSettings', 'TCDefault'), ('TextureCompressionSettings', 'TCNormalmap'),
        ('TextureCompressionSettings', 'TCMasks'), ('TextureSourceEncoding', 'TSESRGB'),
        ('TextureSourceEncoding', 'TSENONE'), ('MaterialSamplerType', 'SAMPLERTYPECOLOR'),
        ('MaterialSamplerType', 'SAMPLERTYPENORMAL'), ('MaterialSamplerType', 'SAMPLERTYPEMASKS')]
    proof = {group+'.'+name: str(enum(u, group, name)) for group, name in pairs}
    direct = {'BlendMode': ['BLEND_MASKED'], 'TextureAddress': ['TA_WRAP'],
        'TextureMipGenSettings': ['TMGS_FROM_TEXTURE_GROUP'], 'TexturePowerOfTwoSetting': ['NONE'],
        'MaterialProperty': ['MP_BASE_COLOR', 'MP_NORMAL', 'MP_ROUGHNESS', 'MP_METALLIC',
            'MP_SPECULAR', 'MP_OPACITY_MASK', 'MP_SUBSURFACE_COLOR']}
    for group, names in direct.items():
        for name in names:
            proof[group+'.'+name] = str(getattr(getattr(u, group), name))
    return proof


def validate_recipe(source_plan):
    """Strict frozen-plan interpretation; this grants no native acceptance."""
    require(sha(SOURCE) == SOURCE_SHA and sha(ROOT/SOURCE_OWNER) == SOURCE_PRODUCER_SHA,
            'Frozen original Fern source changed')
    frozen = json.loads(SOURCE.read_text())
    require(source_plan == frozen and source_plan['schema']
            == 'brezi-original-fern-own-garden-source-pilot-r25'
            and source_plan['owner'] == SOURCE_OWNER and source_plan['status']
            == 'source-only-original-fern-own-garden-pilot-native-base-pending',
            'Exact typed original Fern source plan required')
    require(all(source_plan['audit'][key] is False for key in (
        'nativeApplied', 'nativeGeometryReadbackPerformed', 'nativeAppearanceAccepted',
        'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified')),
        'Source plan cannot grant native or appearance acceptance')
    for path, digest in source_plan['inputFiles'].items():
        require(sha(path) == digest, 'Frozen original fern input changed: '+path)
    proposal = source_plan['materialProposal']
    original = proposal['originalGltfMaterial']
    pbr = original['pbrMetallicRoughness']
    alpha = proposal['explicitAlpha']
    require(original['alphaMode'] == 'MASK' and original['alphaCutoff'] == .5
            and original['doubleSided'] is True and 'occlusionTexture' not in original
            and pbr['metallicFactor'] == 0 and pbr.get('baseColorFactor', [1, 1, 1, 1]) == [1, 1, 1, 1]
            and pbr.get('roughnessFactor', 1) == 1 and original['normalTexture'].get('scale', 1) == 1,
            'Original glTF optical factors/no-occlusion policy changed')
    require(alpha['alphaSourceMode'] == 'I;16' and alpha['alphaSourceBits'] == 16
            and alpha['futureOpacityBinding'] == 'EXPLICIT_NORMALIZED_ALPHA_TEXTURE_R_TO_OPACITY_MASK'
            and alpha['cutoff'] == .5 and alpha['sourcePixelCount'] == 4194304
            and alpha['nativeTextureReadbackPerformed'] is False
            and proposal['normalFutureUnrealFlipGreen'] is True and proposal['twoSidedMasked'] is True
            and proposal['sourceTangentsAbsent'] is True and proposal['futureTangentGenerationRequired'] is True,
            'Explicit original 16-bit alpha/normal policy required')
    maps = {'albedo': proposal['baseColor'], 'normalGL': proposal['normalGL'],
            'ARM': proposal['arm'], 'alpha': alpha['requiredExplicitAlphaMap']}
    for row in maps.values():
        checked(row)
    return {'id': KEY, 'sourceStudy': pin(SOURCE), 'sourceMaterial': original, 'maps': maps,
        'uvSet': 0, 'blendMode': 'MASKED', 'twoSided': True,
        'shadingModel': 'TWOSIDEDFOLIAGE', 'opacityMask': 'normalized original alpha.R',
        'opacityMaskClipValue': .5, 'roughnessFactor': 1., 'metallicFactor': 0.,
        'normalScale': 1., 'baseColorFactor': [1., 1., 1., 1.], 'occlusionRoot': None,
        'worldPositionOffset': None, 'ueTransmissionStrength': .08, 'ueSpecular': .5,
        'ueOpticalCalibrationAccepted': False, 'sourceAlphaBits': 16, 'sourceAlphaMode': 'I;16',
        'sourcePixelEdits': False, 'ecologicalFitVerified': False}


def texture_snapshot(texture):
    keys = ('srgb', 'flip_green_channel', 'compression_settings', 'address_x', 'address_y',
        'lod_bias', 'max_texture_size', 'virtual_texture_streaming', 'never_stream',
        'mip_gen_settings', 'power_of_two_mode', 'do_scale_mips_for_alpha_coverage')
    result = {}
    for key in keys:
        value = texture.get_editor_property(key)
        result[key] = value if isinstance(value, (bool, int, float, str)) else str(value)
    result['alphaCoverageThresholds'] = [float(getattr(
        texture.get_editor_property('alpha_coverage_thresholds'), axis)) for axis in 'xyzw']
    result['sourceEncoding'] = str(texture.get_editor_property('source_color_settings')
                                   .get_editor_property('encoding_override'))
    result['pixels'] = [texture.blueprint_get_size_x(), texture.blueprint_get_size_y()]
    return result


def desired_texture_policy(u, role):
    return {'srgb': role == 'albedo', 'flip_green_channel': role == 'normalGL',
        'compression_settings': enum(u, 'TextureCompressionSettings',
            'TCNormalmap' if role == 'normalGL' else 'TCMasks' if role in ('ARM', 'alpha') else 'TCDefault'),
        'address_x': u.TextureAddress.TA_WRAP, 'address_y': u.TextureAddress.TA_WRAP,
        'lod_bias': 0, 'max_texture_size': 0, 'virtual_texture_streaming': False,
        'never_stream': False, 'mip_gen_settings': u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,
        'power_of_two_mode': u.TexturePowerOfTwoSetting.NONE,
        'do_scale_mips_for_alpha_coverage': role == 'alpha',
        'alpha_coverage_thresholds': u.Vector4(.5, 0, 0, 0) if role == 'alpha' else u.Vector4(0, 0, 0, 0)}


def check_texture_policy(u, snapshot, role):
    wanted = desired_texture_policy(u, role)
    for key, value in wanted.items():
        expected = [float(getattr(value, axis)) for axis in 'xyzw'] if key == 'alpha_coverage_thresholds' else (
            value if isinstance(value, (bool, int, float, str)) else str(value))
        require(snapshot['alphaCoverageThresholds' if key == 'alpha_coverage_thresholds' else key] == expected,
                'Native original fern texture policy differs: '+role+'.'+key)
    require(snapshot['pixels'] == [2048, 2048] and snapshot['sourceEncoding']
            == str(enum(u, 'TextureSourceEncoding', 'TSESRGB' if role == 'albedo' else 'TSENONE')),
            'Native map dimensions/color encoding differ')


def material_policy(material):
    keys = ('blend_mode', 'shading_model', 'two_sided', 'tangent_space_normal',
            'use_material_attributes', 'opacity_mask_clip_value')
    result = {}
    for key in keys:
        value = material.get_editor_property(key)
        result[key] = value if isinstance(value, (bool, int, float, str)) else str(value)
    return result


def check_material_policy(u, material):
    policy = material_policy(material)
    require(policy == {'blend_mode': str(u.BlendMode.BLEND_MASKED),
        'shading_model': str(enum(u, 'MaterialShadingModel', 'TWOSIDEDFOLIAGE')),
        'two_sided': True, 'tangent_space_normal': True, 'use_material_attributes': False,
        'opacity_mask_clip_value': f32(.5)}, 'Native masked fern material policy differs')
    return policy


def check_graph(graph, textures):
    tag = TAG+KEY+':'
    roots = {'BASE_COLOR': [tag+'albedo', 'RGB'], 'NORMAL': [tag+'normalGL', 'RGB'],
        'ROUGHNESS': [tag+'ARM', 'G'], 'METALLIC': [tag+'metallic-factor', ''],
        'SPECULAR': [tag+'dielectric-specular', ''], 'OPACITY_MASK': [tag+'alpha', 'R'],
        'SUBSURFACE_COLOR': [tag+'transmission', '']}
    require(all(graph['roots'][key] == value for key, value in roots.items())
            and all(value is None for key, value in graph['roots'].items() if key not in roots),
            'Fern graph has missing/extra roots, AO/WPO or an incorrect alpha route')
    nodes = {row['role']: row for row in graph['nodes']}
    wanted = {tag+key for key in ('uv', 'albedo', 'normalGL', 'ARM', 'alpha',
        'metallic-zero', 'metallic-factor', 'dielectric-specular', 'strength', 'transmission')}
    require(len(graph['nodes']) == len(nodes) == 10 and set(nodes) == wanted,
            'Exactly ten owned fern expressions required')
    uv = nodes[tag+'uv']
    require(uv['class'] == 'MaterialExpressionTextureCoordinate' and uv['values']
            == {'coordinate_index': 0, 'u_tiling': 1., 'v_tiling': 1.}, 'Original UV0 must remain identity')
    for role, asset in textures.items():
        row = nodes[tag+role]
        sampler = 'SAMPLERTYPENORMAL' if role == 'normalGL' else 'SAMPLERTYPEMASKS' if role in ('ARM', 'alpha') else 'SAMPLERTYPECOLOR'
        require(row['class'] == 'MaterialExpressionTextureSample' and row['values']['texture'] == asset
                and token(row['values']['sampler_type']) == sampler
                and row['inputs'] == [['UVs', tag+'uv', ''], ['Tex', None, None],
                    ['Apply View MipBias', None, None]], 'Original texture/UV route differs: '+role)
    for role, value in (('metallic-zero', 0.), ('dielectric-specular', .5), ('strength', .08)):
        row = nodes[tag+role]
        require(row['class'] == 'MaterialExpressionConstant' and row['values'] == {'r': f32(value)},
                'Explicit provisional fern factor differs: '+role)
    require(nodes[tag+'metallic-factor']['class'] == 'MaterialExpressionMultiply'
            and nodes[tag+'transmission']['class'] == 'MaterialExpressionMultiply'
            and nodes[tag+'metallic-factor']['inputs'] == [['A', tag+'ARM', 'B'], ['B', tag+'metallic-zero', '']]
            and nodes[tag+'transmission']['inputs'] == [['A', tag+'albedo', 'RGB'], ['B', tag+'strength', '']],
            'Metallic factor/explicit artistic transmission differs')
    return {'expressionCount': 10, 'normalizedOriginalAlphaRToOpacityMask': True,
        'uv0Identity': True, 'occlusionRoot': None, 'worldPositionOffset': None,
        'photographicPixelsUnmodified': True, 'nativeAppearanceAccepted': False}


def build_materials(u, source_plan, graph_snapshot):
    recipe = validate_recipe(source_plan)
    # Resolve every enum before creating any package. The source still has no
    # native base, and this function is called only by the separately gated entry.
    native_enums = preflight_enums(u)
    assets, lib = u.EditorAssetLibrary, u.MaterialEditingLibrary
    textures, texture_reports = {}, {}
    for role, row in recipe['maps'].items():
        name = 'T_'+KEY+'_'+role+'_'+row['sha256'][:16]
        asset = PREFIX+'/Textures/'+name
        require(not assets.does_asset_exist(asset), 'Fresh owned R25 texture namespace required')
        task = u.AssetImportTask()
        for key, value in {'filename': str(checked(row)), 'destination_path': PREFIX+'/Textures',
            'destination_name': name, 'automated': True, 'replace_existing': False, 'save': False}.items():
            task.set_editor_property(key, value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture = assets.load_asset(asset)
        require(isinstance(texture, u.Texture2D), 'Original fern map import failed')
        for key, value in desired_texture_policy(u, role).items():
            texture.set_editor_property(key, value)
        color = texture.get_editor_property('source_color_settings')
        color.set_editor_property('encoding_override', enum(u, 'TextureSourceEncoding',
            'TSESRGB' if role == 'albedo' else 'TSENONE'))
        texture.set_editor_property('source_color_settings', color)
        for key, value in {'BreziGeneratedBy': OWNER, 'BreziR25SourceRole': role,
            'BreziSourceLicense': 'CC0-1.0', 'BreziSourcePage': 'https://polyhaven.com/a/fern_02',
            'source_sha256': row['sha256']}.items():
            assets.set_metadata_tag(texture, key, value)
        require(assets.save_loaded_asset(texture, False), 'Cannot save owned original fern texture')
        snapshot = texture_snapshot(texture)
        check_texture_policy(u, snapshot, role)
        textures[role] = texture
        texture_reports[role] = {'asset': texture.get_path_name(), 'source': row, 'snapshot': snapshot,
            'sourceBits': 16 if role == 'alpha' else None, 'sourceMode': 'I;16' if role == 'alpha' else None,
            'nativeSourcePixelFormatReadbackAvailable': False, 'nativeGpuPixelFormatReadbackAvailable': False,
            'nativeImportedPixelsDecoded': False}
    name = 'M_'+KEY
    require(not assets.does_asset_exist(PREFIX+'/Materials/'+name), 'Fresh owned fern graph namespace required')
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(
        name, PREFIX+'/Materials', u.Material, u.MaterialFactoryNew())
    require(material, 'Cannot create owned fern material')
    for key, value in {'blend_mode': u.BlendMode.BLEND_MASKED,
        'shading_model': enum(u, 'MaterialShadingModel', 'TWOSIDEDFOLIAGE'), 'two_sided': True,
        'tangent_space_normal': True, 'use_material_attributes': False, 'opacity_mask_clip_value': .5}.items():
        material.set_editor_property(key, value)
    lib.set_base_material_usage(material, enum(u, 'MaterialUsage', 'INSTANCEDSTATICMESHES'), True)
    tag = TAG+KEY+':'
    def node(role, cls, **values):
        value = lib.create_material_expression(material, cls, -700, 0)
        require(value, 'Cannot create owned fern expression')
        value.set_editor_property('desc', tag+role)
        for key, item in values.items():
            value.set_editor_property(key, item)
        return value
    def connect(a, channel, b, input_):
        require(lib.connect_material_expressions(a, channel, b, input_), 'Cannot connect owned fern graph')
    def root(a, channel, property_):
        require(lib.connect_material_property(a, channel, getattr(u.MaterialProperty, 'MP_'+property_)),
                'Cannot connect owned fern root')
    uv = node('uv', u.MaterialExpressionTextureCoordinate, coordinate_index=0, u_tiling=1., v_tiling=1.)
    samples = {}
    for role, texture in textures.items():
        samples[role] = node(role, u.MaterialExpressionTextureSample, texture=texture,
            sampler_type=enum(u, 'MaterialSamplerType', 'SAMPLERTYPENORMAL' if role == 'normalGL'
                else 'SAMPLERTYPEMASKS' if role in ('ARM', 'alpha') else 'SAMPLERTYPECOLOR'))
        connect(uv, '', samples[role], 'UVs')
    zero = node('metallic-zero', u.MaterialExpressionConstant, r=0.)
    metal = node('metallic-factor', u.MaterialExpressionMultiply)
    connect(samples['ARM'], 'B', metal, 'A'); connect(zero, '', metal, 'B')
    specular = node('dielectric-specular', u.MaterialExpressionConstant, r=.5)
    strength = node('strength', u.MaterialExpressionConstant, r=.08)
    transmission = node('transmission', u.MaterialExpressionMultiply)
    connect(samples['albedo'], 'RGB', transmission, 'A'); connect(strength, '', transmission, 'B')
    for value, channel, property_ in [(samples['albedo'], 'RGB', 'BASE_COLOR'),
        (samples['normalGL'], 'RGB', 'NORMAL'), (samples['ARM'], 'G', 'ROUGHNESS'),
        (metal, '', 'METALLIC'), (specular, '', 'SPECULAR'), (samples['alpha'], 'R', 'OPACITY_MASK'),
        (transmission, '', 'SUBSURFACE_COLOR')]:
        root(value, channel, property_)
    compile_errors = list(lib.recompile_material(material) or [])
    require(not compile_errors, 'Owned fern shader compile failed: '+str(compile_errors))
    graph = graph_snapshot(u, material)
    audit = check_graph(graph, {role: texture.get_path_name() for role, texture in textures.items()})
    policy = check_material_policy(u, material)
    for key, value in {'BreziGeneratedBy': OWNER, 'BreziR25Recipe': json.dumps(recipe, sort_keys=True),
        'BreziSourceLicense': 'CC0-1.0', 'BreziSourcePage': 'https://polyhaven.com/a/fern_02'}.items():
        assets.set_metadata_tag(material, key, value)
    require(assets.save_loaded_asset(material, False), 'Cannot save owned fern material')
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'owned-original-fern-material-created',
        'asset': material.get_path_name(), 'recipe': recipe, 'graph': graph, 'policy': policy,
        'textures': texture_reports, 'compileErrors': compile_errors, 'materialCount': 1, 'textureCount': 4,
        'sourceStudy': pin(SOURCE), 'audit': audit, 'nativeAppearanceAccepted': False,
        'nativeEnumPreflight': native_enums,
        'nativeNormalTangentReadbackAvailable': False, 'nativeAlphaPixelsDecoded': False,
        'instancedStaticMeshUsage': bool(lib.has_material_usage(material, enum(u, 'MaterialUsage', 'INSTANCEDSTATICMESHES'))),
        'nativeSourcePixelFormatReadbackAvailable': False, 'nativeGpuPixelFormatReadbackAvailable': False,
        'ueOpticalCalibrationAccepted': False, 'sourceAlpha16BitDoesNotProveNativePixelFormat': True}
    return material, report


def verify_materials(u, report, source_plan, graph_snapshot):
    recipe = validate_recipe(source_plan)
    require(report['schemaVersion'] == 1 and report['owner'] == OWNER and report['status']
            == 'owned-original-fern-material-created' and report['sourceStudy'] == pin(SOURCE)
            and report['recipe'] == recipe and report['materialCount'] == 1 and report['textureCount'] == 4
            and set(report['textures']) == set(recipe['maps']) and report['compileErrors'] == [],
            'Typed one-graph/four-map fern receipt required')
    require(all(report[key] is False for key in ('nativeAppearanceAccepted', 'nativeNormalTangentReadbackAvailable',
        'nativeAlphaPixelsDecoded', 'nativeSourcePixelFormatReadbackAvailable',
        'nativeGpuPixelFormatReadbackAvailable', 'ueOpticalCalibrationAccepted')),
        'Material receipt cannot overstate readback or optical acceptance')
    require(report['nativeEnumPreflight'] == preflight_enums(u), 'Installed fern material enums changed')
    name = 'M_'+KEY
    require(report['asset'] == PREFIX+'/Materials/'+name+'.'+name, 'Foreign fern material path')
    assets = u.EditorAssetLibrary
    material = assets.load_asset(report['asset'])
    require(isinstance(material, u.Material) and graph_snapshot(u, material) == report['graph']
            and check_material_policy(u, material) == report['policy'], 'Saved fern graph/policy differs')
    require(report['instancedStaticMeshUsage'] is True and u.MaterialEditingLibrary.has_material_usage(
        material, enum(u, 'MaterialUsage', 'INSTANCEDSTATICMESHES')), 'Actual instanced fern material usage required')
    require(assets.get_metadata_tag(material, 'BreziGeneratedBy') == OWNER
            and assets.get_metadata_tag(material, 'BreziR25Recipe') == json.dumps(recipe, sort_keys=True),
            'Owned fern graph provenance changed')
    for role, row in report['textures'].items():
        source = recipe['maps'][role]
        name = 'T_'+KEY+'_'+role+'_'+source['sha256'][:16]
        require(row['source'] == source and row['asset'] == PREFIX+'/Textures/'+name+'.'+name,
                'Original fern texture identity differs')
        texture = assets.load_asset(row['asset'])
        require(isinstance(texture, u.Texture2D) and texture_snapshot(texture) == row['snapshot'],
                'Saved original fern texture settings differ')
        check_texture_policy(u, row['snapshot'], role)
        require(assets.get_metadata_tag(texture, 'BreziGeneratedBy') == OWNER
                and assets.get_metadata_tag(texture, 'source_sha256') == source['sha256']
                and assets.get_metadata_tag(texture, 'BreziR25SourceRole') == role,
                'Saved original fern texture provenance differs')
        require(row['sourceBits'] == (16 if role == 'alpha' else None)
                and row['sourceMode'] == ('I;16' if role == 'alpha' else None)
                and all(row[key] is False for key in ('nativeSourcePixelFormatReadbackAvailable',
                    'nativeGpuPixelFormatReadbackAvailable', 'nativeImportedPixelsDecoded')),
                'Source precision and unavailable native pixel readback must remain distinct')
    require(check_graph(report['graph'], {role: row['asset'] for role, row in report['textures'].items()})
            == report['audit'], 'Saved explicit fern graph audit differs')
    return material
