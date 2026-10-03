"""Owned R43 materials; authenticated source/native binding precedes asset access.

Six original CC0 JPGs are imported unchanged. Three opaque DefaultLit graphs
use original UV0; the metal finish is an explicit artistic constant. This
module does not import Unreal, save packages or grant appearance acceptance.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-parcel-boundary-materials-r43.py'
SCHEMA = 'brezi-r43-three-boundary-materials-native-r1'
PREFIX = '/Game/Brezi/ParcelBoundary20261002R43'
TAG = 'BreziParcelBoundaryR43:'
SOURCE = ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-source-uv-repair-r2/boundary-source-plan-r2.json'
SOURCE_SHA = '614b2f0857bdb90debef3cde81b16b0311791672b7640dbc7fc2971ca8422998'
GUARD = ROOT/'scripts/unreal/exterior-context-parcel-boundary-guards-r43.py'
API = ROOT/'scripts/unreal/exterior-garden-fern-materials-r25.py'
API_SHA = '07de6de2e384802228b6316a15aca0fe327525084eb9141615508b1040fda34f'
SNAPSHOT = ROOT/'scripts/unreal/exterior-context-yard-soft-coherence-materials-r38-r2.py'
SNAPSHOT_SHA = '25752faff7f7dd1be03f8a2310ca033129628d33a613ae588a23c184bee06cca'
ROLES = ('wood', 'metal', 'gravel')
LIMITS = {'sourcePhotoPixelsEdited': False, 'nativeSourceTexelsDecoded': False,
    'nativeGpuPixelFormatVerified': False, 'nativeNormalTangentReadbackAvailable': False,
    'materialCompileDiagnosticsExhaustivelyRead': False,
    'materialPackagesIndependentlyUnloaded': False, 'physicalFinishCalibrated': False,
    'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
    'performanceAccepted': False, 'shippingVerified': False}


def require(ok, message):
    if not ok: raise ValueError(message)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
def pin(path):
    p = Path(path).resolve();return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
def checked(row):
    p = Path(row['path']);require(p.is_absolute() and p.resolve() == p and p.is_file() and not p.is_symlink()
        and sha(p) == row['sha256'] and p.stat().st_size == row['bytes'], 'Untouched original source pin required')
    return p
def module(name, path, expected=None):
    if expected is not None: require(sha(path) == expected, 'Frozen pure material API changed')
    s = importlib.util.spec_from_file_location(name, path);m = importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def api(): return module('_r43_private_proven_material_api', API, API_SHA)
def snapshots(): return module('_r43_private_visible24_texture_api', SNAPSHOT, SNAPSHOT_SHA)
def binding_guard(): return module('_r43_actual_native_material_binding', GUARD)


def validate_binding(bundle, binding):
    g = binding_guard();g.require_native_binding(binding)
    require(set(bundle) == {'source', 'base', 'binding'} and bundle['binding'] == binding,
        'Exact authenticated source/base/native packet required')
    source = bundle['source'];require(sha(SOURCE) == SOURCE_SHA and source['planPin'] == pin(SOURCE)
        and source['plan'] == json.loads(SOURCE.read_text()), 'Exact frozen UV-corrected R43 source required')
    return source


def validate_recipes(source):
    frozen = json.loads(SOURCE.read_text())
    require(sha(SOURCE) == SOURCE_SHA and source['planPin'] == pin(SOURCE)
        and source['plan']['materials'] == frozen['materials'], 'Three immutable original material proposals required')
    recipes = source['plan']['materials'];require(set(recipes) == set(ROLES), 'Only wood, metal and gravel allowed')
    for role in ('wood', 'gravel'):
        require(set(recipes[role]['maps']) == {'diffuse', 'normal', 'roughness'}
            and recipes[role]['license'] == 'CC0-1.0' and recipes[role]['proposedNormalGreenFlip'] is True
            and recipes[role]['displacementNotUsed'] is True, 'Original three-map source route differs')
        for row in recipes[role]['maps'].values(): checked(row);require(row['pixelEdits'] is False, 'No source pixel edits permitted')
    require(recipes['metal']['baseColorLinear'] == [.055, .062, .067]
        and recipes['metal']['metallic'] == 1 and recipes['metal']['roughness'] == .62
        and recipes['metal']['artisticUncalibrated'] is True, 'Only declared artistic metal finish allowed')
    assets_ = sorted([p for role in ROLES for p in [assets(role)[0], *assets(role)[1].values()]])
    require(len(assets_) == len(set(assets_)) == 9, 'Exactly three graphs and six original textures required')
    return recipes, assets_


def assets(role):
    require(role in ROLES, 'Unknown own material role')
    name = 'M_boundary_'+role+'_r43';material = PREFIX+'/Materials/'+name+'.'+name
    textures = {}
    if role != 'metal':
        for map_role in ('diffuse', 'normal', 'roughness'):
            name = 'T_'+role+'_'+map_role+'_r43';textures[map_role] = PREFIX+'/Textures/'+name+'.'+name
    return material, textures


def jpg_header(row):
    data = checked(row).read_bytes();require(data[:2] == b'\xff\xd8', 'Original published JPG required')
    i = 2
    while i < len(data):
        require(data[i] == 255, 'Invalid JPEG marker');i += 1
        while data[i] == 255: i += 1
        marker = data[i];i += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7: continue
        require(marker != 0xDA, 'JPEG dimensions absent before image payload')
        length = int.from_bytes(data[i:i+2], 'big');require(length >= 2, 'Invalid JPEG segment')
        if marker in (0xC0, 0xC1, 0xC2):
            bits = data[i+2];height = int.from_bytes(data[i+3:i+5], 'big');width = int.from_bytes(data[i+5:i+7], 'big');components = data[i+7]
            require((width, height, bits) == (2048, 2048, 8), 'Original source JPG dimensions/precision differ')
            return {'pixels': [width, height], 'sourceBits': bits, 'components': components,
                'nativeGpuPixelFormatVerified': False}
        i += length
    raise ValueError('Original JPG source dimensions unavailable')


def preflight_enums(u):
    d = api();pairs = [('MaterialShadingModel', 'DEFAULTLIT'),
        ('TextureCompressionSettings', 'TCDefault'), ('TextureCompressionSettings', 'TCNormalmap'),
        ('TextureCompressionSettings', 'TCMasks'), ('TextureSourceEncoding', 'TSESRGB'),
        ('TextureSourceEncoding', 'TSENONE'), ('MaterialSamplerType', 'SAMPLERTYPECOLOR'),
        ('MaterialSamplerType', 'SAMPLERTYPENORMAL'), ('MaterialSamplerType', 'SAMPLERTYPEMASKS')]
    proof = {group+'.'+name: str(d.enum(u, group, name)) for group, name in pairs}
    for group, names in {'BlendMode': ['BLEND_OPAQUE'], 'TextureAddress': ['TA_WRAP'],
        'TextureFilter': ['TF_DEFAULT'], 'TextureMipGenSettings': ['TMGS_FROM_TEXTURE_GROUP'],
        'TexturePowerOfTwoSetting': ['NONE'], 'MaterialProperty': ['MP_BASE_COLOR', 'MP_NORMAL',
            'MP_ROUGHNESS', 'MP_METALLIC', 'MP_SPECULAR']}.items():
        for name in names: proof[group+'.'+name] = str(getattr(getattr(u, group), name))
    return proof


def preflight_reflection(u):
    texture = u.get_default_object(u.Texture2D)
    for name in snapshots().FIELDS: texture.get_editor_property(name)
    texture.get_editor_property('source_color_settings').get_editor_property('encoding_override')
    down = texture.get_editor_property('downscale');down.get_editor_property('default');down.get_editor_property('per_platform')
    texture.get_editor_property('alpha_coverage_thresholds')
    for name in ('MaterialExpressionTextureCoordinate', 'MaterialExpressionTextureSample',
        'MaterialExpressionConstant', 'MaterialExpressionConstant3Vector', 'AssetImportTask', 'MaterialFactoryNew'):
        require(hasattr(u, name), 'Required reflected original-map API absent')
    return {'visibleTextureFields': 24, 'hiddenCompressionNoneAccessed': False,
        'readableBeforeImport': True, 'writableReflectionActuallyMeasured': False}


def texture_values(u, role):
    d = api();return {'srgb': role == 'diffuse', 'compression_settings': d.enum(u, 'TextureCompressionSettings',
        'TCDefault' if role == 'diffuse' else 'TCNormalmap' if role == 'normal' else 'TCMasks'),
        'mip_gen_settings': u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP, 'filter': u.TextureFilter.TF_DEFAULT,
        'address_x': u.TextureAddress.TA_WRAP, 'address_y': u.TextureAddress.TA_WRAP,
        'power_of_two_mode': u.TexturePowerOfTwoSetting.NONE, 'resize_during_build_x': 0, 'resize_during_build_y': 0,
        'lod_bias': 0, 'max_texture_size': 0, 'never_stream': False, 'virtual_texture_streaming': False,
        'flip_green_channel': role == 'normal', 'do_scale_mips_for_alpha_coverage': False,
        'adjust_brightness': 1., 'adjust_brightness_curve': 1., 'adjust_vibrance': 0.,
        'adjust_saturation': 1., 'adjust_rgb_curve': 1., 'adjust_hue': 0.,
        'adjust_min_alpha': 0., 'adjust_max_alpha': 1., 'chroma_key_texture': False}


def check_texture(u, row, role, asset):
    expected = {key: value if isinstance(value, (bool, int, float, str)) else str(value)
        for key, value in texture_values(u, role).items()}
    require(row['asset'] == asset and row['values'] == expected and row['size'] == [2048, 2048]
        and row['sourceEncoding'] == str(api().enum(u, 'TextureSourceEncoding', 'TSESRGB' if role == 'diffuse' else 'TSENONE'))
        and row['downscale'] == {'default': 1., 'perPlatform': {}} and row['alphaCoverageThresholds'] == [0., 0., 0., 0.],
        'Original map sampler/compression/encoding/adjustment policy differs')


def material_policy(u, material):
    d = api();row = d.material_policy(material)
    for key, value in {'blend_mode': str(u.BlendMode.BLEND_OPAQUE),
        'shading_model': str(d.enum(u, 'MaterialShadingModel', 'DEFAULTLIT')), 'two_sided': False,
        'tangent_space_normal': True, 'use_material_attributes': False}.items():
        require(row[key] == value, 'Owned opaque DefaultLit policy differs: '+key)
    return row


def validate_graph(graph, role, recipe, texture_paths):
    tag = TAG+role+':';nodes = {n['role']: n for n in graph['nodes']}
    expected_roles = ['color', 'metallic', 'roughness', 'specular'] if role == 'metal' else ['uv', 'diffuse', 'normal', 'roughness', 'metallic', 'specular']
    require(len(nodes) == len(graph['nodes']) == len(expected_roles) and set(nodes) == {tag+k for k in expected_roles}, 'Exact owned graph expressions required')
    roots = {'BASE_COLOR': [tag+('color' if role == 'metal' else 'diffuse'), '' if role == 'metal' else 'RGB'],
        'ROUGHNESS': [tag+'roughness', '' if role == 'metal' else 'R'], 'METALLIC': [tag+'metallic', ''], 'SPECULAR': [tag+'specular', '']}
    if role != 'metal': roots['NORMAL'] = [tag+'normal', 'RGB']
    require(all(graph['roots'][key] == value for key, value in roots.items())
        and all(value is None for key, value in graph['roots'].items() if key not in roots), 'Only declared PBR roots allowed; no AO/opacity/WPO/displacement')
    d = api()
    for key, value in [('metallic', 1. if role == 'metal' else 0.), ('specular', .5)] + ([('roughness', .62)] if role == 'metal' else []):
        require(nodes[tag+key]['class'] == 'MaterialExpressionConstant' and nodes[tag+key]['values'] == {'r': d.f32(value)}, 'Owned constant differs: '+key)
    if role == 'metal':
        require(nodes[tag+'color']['class'] == 'MaterialExpressionConstant3Vector'
            and nodes[tag+'color']['values'] == {'constant': [d.f32(v) for v in recipe['baseColorLinear']]+[1.]}, 'Explicit linear metal color differs')
    else:
        require(nodes[tag+'uv']['class'] == 'MaterialExpressionTextureCoordinate'
            and nodes[tag+'uv']['values'] == {'coordinate_index': 0, 'u_tiling': 1., 'v_tiling': 1.}, 'Original metric UV0 must remain identity')
        for map_role in ('diffuse', 'normal', 'roughness'):
            n = nodes[tag+map_role];sampler = 'SAMPLERTYPECOLOR' if map_role == 'diffuse' else 'SAMPLERTYPENORMAL' if map_role == 'normal' else 'SAMPLERTYPEMASKS'
            require(n['class'] == 'MaterialExpressionTextureSample' and n['values']['texture'] == texture_paths[map_role]
                and d.token(n['values']['sampler_type']) == sampler and n['inputs'] == [['UVs', tag+'uv', ''], ['Tex', None, None], ['Apply View MipBias', None, None]],
                'Original map/UV0/sampler differs: '+map_role)
    return {'uv0Identity': role != 'metal', 'originalPhotosUnmodified': True, 'ambientOcclusionRoot': None,
        'opacityRoot': None, 'worldPositionOffsetRoot': None, 'metalFinishArtistic': role == 'metal'}


def metadata(u, obj, role, source=None, write=False):
    wanted = {'BreziGeneratedBy': OWNER, 'BreziSourcePlanSha256': SOURCE_SHA,
        'BreziR43Role': role, 'BreziSourceLicense': 'CC0-1.0' if role.split(':')[0] in ('wood', 'gravel') else 'own-artistic-material'}
    if source: wanted['BreziSourceSha256'] = source['sha256']
    for key, value in wanted.items():
        if write: u.EditorAssetLibrary.set_metadata_tag(obj, key, value)
        require(u.EditorAssetLibrary.get_metadata_tag(obj, key) == value, 'Owned source metadata differs')
    return wanted


def build_materials(u, bundle, binding, graph_snapshot):
    source = validate_binding(bundle, binding);recipes, packages = validate_recipes(source)
    enum_proof = preflight_enums(u);reflection = preflight_reflection(u);d = api();snapshot = snapshots();lib = u.MaterialEditingLibrary;ea = u.EditorAssetLibrary
    materials = {};records = {}
    for role in ROLES:
        recipe = recipes[role];path, texture_paths = assets(role);textures = {};texture_records = {}
        for map_role, source_row in recipe.get('maps', {}).items():
            header = jpg_header(source_row);package, name = texture_paths[map_role].rsplit('.', 1)
            require(not ea.does_asset_exist(package), 'Fresh own texture namespace required')
            task = u.AssetImportTask()
            for key, value in {'filename': str(checked(source_row)), 'destination_path': package.rsplit('/', 1)[0],
                'destination_name': name, 'automated': True, 'replace_existing': False, 'save': False}.items(): task.set_editor_property(key, value)
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);texture = ea.load_asset(package)
            require(isinstance(texture, u.Texture2D) and texture.get_path_name() == texture_paths[map_role], 'Original source map import failed')
            for key, value in texture_values(u, map_role).items(): texture.set_editor_property(key, value)
            down = texture.get_editor_property('downscale');down.set_editor_property('default', 1.);down.set_editor_property('per_platform', {});texture.set_editor_property('downscale', down)
            texture.set_editor_property('alpha_coverage_thresholds', u.Vector4(0., 0., 0., 0.))
            color = texture.get_editor_property('source_color_settings');color.set_editor_property('encoding_override', d.enum(u, 'TextureSourceEncoding', 'TSESRGB' if map_role == 'diffuse' else 'TSENONE'));texture.set_editor_property('source_color_settings', color)
            meta = metadata(u, texture, role+':'+map_role, source_row, True);row = snapshot.texture_snapshot(u, texture);check_texture(u, row, map_role, texture_paths[map_role])
            textures[map_role] = texture;texture_records[map_role] = {'asset': texture_paths[map_role], 'source': source_row, 'sourceJpg': header, 'snapshot': row, 'metadata': meta}
        package, name = path.rsplit('.', 1);require(not ea.does_asset_exist(package), 'Fresh own material namespace required')
        material = u.AssetToolsHelpers.get_asset_tools().create_asset(name, package.rsplit('/', 1)[0], u.Material, u.MaterialFactoryNew());require(isinstance(material, u.Material), 'Cannot create own boundary material')
        for key, value in {'blend_mode': u.BlendMode.BLEND_OPAQUE, 'shading_model': d.enum(u, 'MaterialShadingModel', 'DEFAULTLIT'),
            'two_sided': False, 'tangent_space_normal': True, 'use_material_attributes': False}.items(): material.set_editor_property(key, value)
        def node(name, cls, **values):
            obj = lib.create_material_expression(material, cls, -700, 0);require(obj, 'Cannot create owned expression');obj.set_editor_property('desc', TAG+role+':'+name)
            for key, value in values.items(): obj.set_editor_property(key, value)
            return obj
        if role == 'metal':
            base = node('color', u.MaterialExpressionConstant3Vector, constant=u.LinearColor(*recipe['baseColorLinear'], 1.))
            roughness = node('roughness', u.MaterialExpressionConstant, r=.62);normal = None
        else:
            uv = node('uv', u.MaterialExpressionTextureCoordinate, coordinate_index=0, u_tiling=1., v_tiling=1.);samples = {}
            for map_role in ('diffuse', 'normal', 'roughness'):
                sampler = 'SAMPLERTYPECOLOR' if map_role == 'diffuse' else 'SAMPLERTYPENORMAL' if map_role == 'normal' else 'SAMPLERTYPEMASKS'
                samples[map_role] = node(map_role, u.MaterialExpressionTextureSample, texture=textures[map_role], sampler_type=d.enum(u, 'MaterialSamplerType', sampler));require(lib.connect_material_expressions(uv, '', samples[map_role], 'UVs'), 'Cannot connect original UV0')
            base = samples['diffuse'];normal = samples['normal'];roughness = samples['roughness']
        metallic = node('metallic', u.MaterialExpressionConstant, r=1. if role == 'metal' else 0.);specular = node('specular', u.MaterialExpressionConstant, r=.5)
        for obj, channel, prop in [(base, '' if role == 'metal' else 'RGB', 'BASE_COLOR'), (roughness, '' if role == 'metal' else 'R', 'ROUGHNESS'), (metallic, '', 'METALLIC'), (specular, '', 'SPECULAR')] + ([(normal, 'RGB', 'NORMAL')] if normal else []):
            require(lib.connect_material_property(obj, channel, getattr(u.MaterialProperty, 'MP_'+prop)), 'Cannot connect owned PBR root')
        errors = list(lib.recompile_material(material) or []);require(not errors, 'Owned graph compile errors: '+str(errors))
        graph = graph_snapshot(u, material);audit = validate_graph(graph, role, recipe, texture_paths)
        meta = metadata(u, material, role, write=True);materials[role] = material
        records[role] = {'asset': path, 'recipe': recipe, 'graph': graph, 'graphSha256': digest(graph), 'policy': material_policy(u, material),
            'metadata': meta, 'compileErrors': errors, 'textures': texture_records, 'graphAudit': audit}
    report = {'schema': SCHEMA, 'schemaVersion': 1, 'owner': OWNER, 'nativeBinding': binding,
        'sourcePlan': source['planPin'], 'materialCount': 3, 'textureObjectCount': 6, 'materials': records,
        'newPackageAssets': packages, 'nativeEnumPreflight': enum_proof, 'reflectionPreflight': reflection,
        'pureApiSources': [pin(API), pin(SNAPSHOT)], **LIMITS}
    return materials, report


def verify_materials(u, bundle, binding, report, graph_snapshot):
    source = validate_binding(bundle, binding);recipes, packages = validate_recipes(source)
    require(report['schema'] == SCHEMA and report['schemaVersion'] == 1 and report['owner'] == OWNER
        and report['nativeBinding'] == binding and report['sourcePlan'] == source['planPin']
        and report['materialCount'] == 3 and report['textureObjectCount'] == 6
        and set(report['materials']) == set(ROLES) and report['newPackageAssets'] == packages
        and report['pureApiSources'] == [pin(API), pin(SNAPSHOT)], 'Exact own complete material receipt required')
    for key, value in LIMITS.items(): require(report[key] is value, 'Material evidence limit changed: '+key)
    require(report['nativeEnumPreflight'] == preflight_enums(u), 'Native enum preflight differs')
    d = snapshots();result = {}
    for role in ROLES:
        row = report['materials'][role];recipe = recipes[role];path, texture_paths = assets(role)
        require(row['asset'] == path and row['recipe'] == recipe and set(row['textures']) == set(texture_paths), 'Material/recipe/map identity differs')
        material = u.EditorAssetLibrary.load_asset(path)
        require(isinstance(material, u.Material) and graph_snapshot(u, material) == row['graph']
            and digest(row['graph']) == row['graphSha256'] and material_policy(u, material) == row['policy']
            and metadata(u, material, role) == row['metadata'] and row['compileErrors'] == [], 'Saved owned graph/flags/metadata differs')
        require(validate_graph(row['graph'], role, recipe, texture_paths) == row['graphAudit'], 'Saved owned graph audit differs')
        for map_role, texture_row in row['textures'].items():
            require(texture_row['asset'] == texture_paths[map_role] and texture_row['source'] == recipe['maps'][map_role]
                and jpg_header(texture_row['source']) == texture_row['sourceJpg'], 'Original map source differs')
            texture = u.EditorAssetLibrary.load_asset(texture_row['asset']);require(isinstance(texture, u.Texture2D)
                and d.texture_snapshot(u, texture) == texture_row['snapshot']
                and metadata(u, texture, role+':'+map_role, texture_row['source']) == texture_row['metadata'], 'Saved original-map snapshot/metadata differs')
            check_texture(u, texture_row['snapshot'], map_role, texture_paths[map_role])
        result[role] = material
    return result
