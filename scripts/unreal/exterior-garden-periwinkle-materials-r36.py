"""Owned original five-map Periwinkle material; CPU/source validation is not render proof.

The provider glTF uses BLEND with JPEG color. This explicit UE proposal uses
the separately published 16-bit opacity PNG and TwoSidedFoliage, preserving
original pixels/UV0. Its translucency calibration is artistic, not photometry.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-periwinkle-materials-r36.py'
SCHEMA = 'brezi-original-periwinkle-five-map-material-r36'
PREFIX = '/Game/Brezi/GardenPeriwinkle20261002R36'
KEY = 'ph_original_periwinkle_r36'
TAG = 'BreziGardenPeriwinkleR36:'
RECIPE = ROOT/'output/unreal/exterior-garden-periwinkle-20261002-r36-source-study/material-recipe.json'
RECIPE_SHA = '04a7223f7e5ba93c88f6e7438d3776283a241782f4b00c52fba5c06c98cc1b98'
SOURCE_OWNER = 'scripts/unreal/exterior-garden-periwinkle-study-r36.py'
REFERENCE = ROOT/'output/unreal/exterior-ph-periwinkle-reference-20261002-r1'
ROLES = ('albedo', 'normalGl', 'opacity', 'roughness', 'translucency')
DELEGATE = ROOT/'scripts/unreal/exterior-garden-fern-materials-r25.py'
DELEGATE_SHA = '07de6de2e384802228b6316a15aca0fe327525084eb9141615508b1040fda34f'
_PRIVATE = None


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def pin(path):
    p = Path(path).resolve()
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}


def checked(row):
    p = Path(row['path'])
    require(p.is_absolute() and str(p.resolve()) == row['path'] and not p.is_symlink()
        and p.is_file() and p.is_relative_to(REFERENCE) and row == pin(p), 'Original Periwinkle input pin changed')
    return p


def _private():
    """Reuse frozen pure enum/property observations without changing its owner."""
    global _PRIVATE
    require(DELEGATE.is_file() and not DELEGATE.is_symlink() and sha(DELEGATE) == DELEGATE_SHA
        and DELEGATE.stat().st_size == 23012, 'Frozen original material API helper changed')
    if _PRIVATE is None:
        spec = importlib.util.spec_from_file_location('_r36_private_original_material_api', DELEGATE)
        _PRIVATE = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_PRIVATE)
    require(_PRIVATE.OWNER == 'scripts/unreal/exterior-garden-fern-materials-r25.py'
        and _PRIVATE.PREFIX == '/Game/Brezi/GardenFern20261002R25', 'Frozen API helper ownership changed')
    return _PRIVATE


def preflight_enums(u):
    return _private().preflight_enums(u)


def png_header(path):
    data = Path(path).read_bytes()[:33]
    require(data[:8] == b'\x89PNG\r\n\x1a\n' and data[12:16] == b'IHDR', 'Original PNG required')
    w, h, bits, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', data[16:29])
    require((w, h, bits) == (2048, 2048, 16) and compression == filtering == 0 and interlace == 0,
        'Original map size/bit depth/encoding changed')
    return {'pixels': [w, h], 'sourceBits': bits, 'pngColorType': color}


def validate_recipe(recipe):
    require(RECIPE_SHA is not None and RECIPE.is_file() and not RECIPE.is_symlink() and sha(RECIPE) == RECIPE_SHA
        and recipe == json.loads(RECIPE.read_text()), 'Exact selected R36 material source recipe required')
    require(recipe['schema'] == 'brezi-garden-original-periwinkle-material-recipe-r36'
        and recipe['owner'] == SOURCE_OWNER and recipe['status'] == 'source-original-map-recipe-native-pending'
        and recipe['prefix'] == PREFIX and recipe['key'] == KEY, 'R36 recipe ownership differs')
    require(tuple(recipe['maps']) == ROLES and recipe['newGraphCount'] == 1 and recipe['newTextureObjectCount'] == 5,
        'Exactly one original Periwinkle graph and five maps required')
    for key in ('sourceGltf', 'originalDownloadReceipt', 'originalPbrPngReceipt'):
        checked(recipe[key])
    original = json.loads(checked(recipe['sourceGltf']).read_text())
    require(len(original['materials']) == 1, 'One original provider material required')
    mat = original['materials'][0]
    require(mat == {'alphaMode': 'BLEND', 'doubleSided': True, 'name': 'periwinkle_plant',
        'normalTexture': {'index': 0}, 'pbrMetallicRoughness': {'baseColorTexture': {'index': 1},
            'metallicFactor': 0, 'metallicRoughnessTexture': {'index': 2}}}, 'Original glTF optical factors changed')
    receipts = json.loads(checked(recipe['originalPbrPngReceipt']).read_text())
    role_map = {'albedo': 'Diffuse', 'normalGl': 'nor_gl', 'opacity': 'opacity', 'roughness': 'Rough', 'translucency': 'translucency'}
    source_maps = {r['role']: r['actual'] for r in receipts['files']}
    require(receipts['license'] == 'CC0' and len(source_maps) == 5 and receipts['sourcePixelsEdited'] is False,
        'Original CC0 source-map receipt changed')
    for role in ROLES:
        require(recipe['maps'][role] == source_maps[role_map[role]], 'Map role is not the original source: '+role)
        header = png_header(checked(recipe['maps'][role]))
        require(header['pngColorType'] == (0 if role in ('opacity', 'roughness') else 6), 'Original color/data map shape differs')
    require(recipe['sourceOriginalAlphaMode'] == 'BLEND' and recipe['proposedEngineBlendMode'] == 'MASKED'
        and recipe['originalDoubleSided'] is True and recipe['engineShadingModel'] == 'TwoSidedFoliage artistic proposal'
        and recipe['alphaRoute'] == 'original16bit opacity PNG normalized R -> OpacityMask cutoff0.5'
        and recipe['clipValue'] == .5, 'Original/proposed alpha or shading scope differs')
    require(all(recipe[k] is True for k in ('albedoSourceSrgb', 'normalSourceLinear', 'normalGlFlipGreen',
        'roughnessLinearNormalizedR', 'translucencySourceSrgb', 'sourceColor0AllWhite', 'color1NotUsedByOriginalGltfMaterial')),
        'Original map/color-coordinate policy differs')
    require(recipe['baseColorFactor'] == [1,1,1,1] and recipe['roughnessFactor'] == 1
        and recipe['metallic'] == 0 and recipe['normalScale'] == 1 and recipe['uvChannel'] == 0
        and recipe['specular'] == .5 and recipe['subsurfaceCalibration'] == .08
        and recipe['subsurfaceColorRoute'] == 'unchanged original translucency RGB times explicit UE calibration0.08',
        'Declared original factors or provisional transmission calibration differ')
    for key in ('sourceOpticalModelExactlyReproduced', 'wpoEnabled', 'sourcePixelsEdited',
        'roughPngVsArmGPixelEquivalenceClaimed', 'actualNativeGpuPixelFormatVerified',
        'physicalOpticalCalibrationAccepted', 'nativeAppearanceAccepted', 'fullPhotorealismAccepted'):
        require(recipe[key] is False, 'Source recipe overstates evidence: '+key)
    return recipe


def desired_texture_policy(u, role):
    require(role in ROLES, 'Unknown original map role')
    d = _private()
    return {'srgb': role in ('albedo', 'translucency'), 'flip_green_channel': role == 'normalGl',
        'compression_settings': d.enum(u, 'TextureCompressionSettings', 'TCNormalmap' if role == 'normalGl'
            else 'TCMasks' if role in ('opacity','roughness') else 'TCDefault'),
        'address_x': u.TextureAddress.TA_WRAP, 'address_y': u.TextureAddress.TA_WRAP,
        'lod_bias': 0, 'max_texture_size': 0, 'virtual_texture_streaming': False, 'never_stream': False,
        'mip_gen_settings': u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,
        'power_of_two_mode': u.TexturePowerOfTwoSetting.NONE,
        'do_scale_mips_for_alpha_coverage': role == 'opacity',
        'alpha_coverage_thresholds': u.Vector4(.5,0,0,0) if role == 'opacity' else u.Vector4(0,0,0,0)}


def check_texture_policy(u, snapshot, role):
    d = _private()
    for key, value in desired_texture_policy(u, role).items():
        expected = [float(getattr(value, a)) for a in 'xyzw'] if key == 'alpha_coverage_thresholds' else (
            value if isinstance(value, (bool,int,float,str)) else str(value))
        require(snapshot['alphaCoverageThresholds' if key == 'alpha_coverage_thresholds' else key] == expected,
            'Original Periwinkle texture policy differs: '+role+'.'+key)
    encoding = d.enum(u, 'TextureSourceEncoding', 'TSESRGB' if role in ('albedo','translucency') else 'TSENONE')
    require(snapshot['sourceEncoding'] == str(encoding) and snapshot['pixels'] == [2048,2048],
        'Original source encoding/dimensions differ: '+role)


def check_material_policy(u, material):
    d = _private()
    policy = d.material_policy(material)
    require(policy == {'blend_mode': str(u.BlendMode.BLEND_MASKED),
        'shading_model': str(d.enum(u,'MaterialShadingModel','TWOSIDEDFOLIAGE')),
        'two_sided': True, 'tangent_space_normal': True, 'use_material_attributes': False,
        'opacity_mask_clip_value': d.f32(.5)}, 'Native masked Periwinkle policy differs')
    return policy


def texture_asset(role, source):
    name = 'T_'+KEY+'_'+role+'_'+source['sha256'][:16]
    return PREFIX+'/Textures/'+name+'.'+name


def package_assets(recipe):
    name = 'M_'+KEY
    result = [PREFIX+'/Materials/'+name+'.'+name] + [texture_asset(role, recipe['maps'][role]) for role in ROLES]
    require(len(result) == len(set(result)) == 6, 'Exactly six owned material/texture packages required')
    return sorted(result)


def check_graph(graph, textures):
    d = _private()
    tag = TAG+KEY+':'
    roots = {'BASE_COLOR': [tag+'albedo','RGB'], 'NORMAL': [tag+'normalGl','RGB'],
        'ROUGHNESS': [tag+'roughness','R'], 'METALLIC': [tag+'metallic-zero',''],
        'SPECULAR': [tag+'dielectric-specular',''], 'OPACITY_MASK': [tag+'opacity','R'],
        'SUBSURFACE_COLOR': [tag+'transmission','']}
    require(all(graph['roots'][k] == v for k,v in roots.items())
        and all(v is None for k,v in graph['roots'].items() if k not in roots),
        'Wrong alpha/channel/transmission/AO/WPO graph root')
    nodes = {r['role']:r for r in graph['nodes']}
    required = {tag+r for r in ROLES+('uv','metallic-zero','dielectric-specular','strength','transmission')}
    require(len(graph['nodes']) == len(nodes) == 10 and set(nodes) == required and set(textures) == set(ROLES),
        'Exactly ten uniquely tagged original Periwinkle expressions required')
    uv = nodes[tag+'uv']
    require(uv['class'] == 'MaterialExpressionTextureCoordinate' and uv['values']
        == {'coordinate_index':0,'u_tiling':1.,'v_tiling':1.}, 'Original identity UV0 required')
    for role in ROLES:
        n = nodes[tag+role]
        sampler = 'SAMPLERTYPENORMAL' if role == 'normalGl' else 'SAMPLERTYPEMASKS' if role in ('opacity','roughness') else 'SAMPLERTYPECOLOR'
        require(n['class'] == 'MaterialExpressionTextureSample' and n['values']['texture'] == textures[role]
            and d.token(n['values']['sampler_type']) == sampler and n['inputs']
            == [['UVs',tag+'uv',''],['Tex',None,None],['Apply View MipBias',None,None]], 'Original texture/UV/sampler route differs: '+role)
    for role,value in [('metallic-zero',0.),('dielectric-specular',.5),('strength',.08)]:
        require(nodes[tag+role]['class'] == 'MaterialExpressionConstant'
            and nodes[tag+role]['values'] == {'r':d.f32(value)}, 'Declared optical factor differs: '+role)
    require(nodes[tag+'transmission']['class'] == 'MaterialExpressionMultiply'
        and nodes[tag+'transmission']['inputs'] == [['A',tag+'translucency','RGB'],['B',tag+'strength','']],
        'Actual original translucency map must drive subsurface color')
    return {'expressionCount':10, 'identityOriginalUV0':True, 'originalOpacityNormalizedR':True,
        'originalRoughnessNormalizedR':True, 'transmissionSource':'original photographic translucency RGB ×0.08',
        'albedoAlphaIgnored':True, 'ambientOcclusionRoot':None, 'worldPositionOffset':None,
        'sourcePixelsEdited':False, 'physicalOpticalCalibrationAccepted':False}


def _metadata(u, obj, role, source=None, write=False):
    wanted = {'BreziGeneratedBy':OWNER,'BreziR36SourceRecipeSha256':RECIPE_SHA,
        'BreziR36MaterialRole':role,'BreziSourceLicense':'CC0-1.0',
        'BreziSourcePage':'https://polyhaven.com/a/periwinkle_plant'}
    if source is not None:
        wanted['source_sha256'] = source['sha256']
    if role == 'material':
        wanted['BreziR36Recipe'] = json.dumps(json.loads(RECIPE.read_text()),sort_keys=True)
    for key,value in wanted.items():
        if write:
            u.EditorAssetLibrary.set_metadata_tag(obj,key,value)
        require(u.EditorAssetLibrary.get_metadata_tag(obj,key) == value, 'Owned Periwinkle metadata differs: '+key)
    if write:
        require(u.EditorAssetLibrary.save_loaded_asset(obj,False), 'Cannot save owned original Periwinkle asset')
    return wanted


def build_materials(u, recipe, graph_snapshot):
    validate_recipe(recipe)
    enums = preflight_enums(u)  # Resolve every enum before writing any package.
    d, lib, assets = _private(), u.MaterialEditingLibrary, u.EditorAssetLibrary
    textures, reports = {}, {}
    for role,source in recipe['maps'].items():
        path = texture_asset(role,source)
        package,name = path.rsplit('.',1)
        require(not assets.does_asset_exist(package), 'Fresh owned Periwinkle texture namespace required')
        task = u.AssetImportTask()
        for key,value in {'filename':str(checked(source)), 'destination_path':PREFIX+'/Textures',
            'destination_name':name, 'automated':True, 'replace_existing':False, 'save':False}.items():
            task.set_editor_property(key,value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture = assets.load_asset(package)
        require(isinstance(texture,u.Texture2D) and texture.get_path_name() == path, 'Original Periwinkle PNG import failed')
        for key,value in desired_texture_policy(u,role).items():
            texture.set_editor_property(key,value)
        color = texture.get_editor_property('source_color_settings')
        color.set_editor_property('encoding_override', d.enum(u,'TextureSourceEncoding',
            'TSESRGB' if role in ('albedo','translucency') else 'TSENONE'))
        texture.set_editor_property('source_color_settings',color)
        metadata = _metadata(u,texture,role,source,write=True)
        snapshot = d.texture_snapshot(texture)
        check_texture_policy(u,snapshot,role)
        textures[role] = texture
        reports[role] = {'asset':path,'source':source,'sourcePngHeader':png_header(checked(source)),
            'snapshot':snapshot,'metadata':metadata,'nativeImportedPixelsDecoded':False,
            'nativeSourcePixelFormatReadbackAvailable':False,'nativeGpuPixelFormatReadbackAvailable':False}
    name = 'M_'+KEY
    require(not assets.does_asset_exist(PREFIX+'/Materials/'+name), 'Fresh owned Periwinkle graph namespace required')
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(name,PREFIX+'/Materials',u.Material,u.MaterialFactoryNew())
    require(isinstance(material,u.Material), 'Cannot create owned Periwinkle material')
    for key,value in {'blend_mode':u.BlendMode.BLEND_MASKED,'shading_model':d.enum(u,'MaterialShadingModel','TWOSIDEDFOLIAGE'),
        'two_sided':True,'tangent_space_normal':True,'use_material_attributes':False,'opacity_mask_clip_value':.5}.items():
        material.set_editor_property(key,value)
    usage = d.enum(u,'MaterialUsage','INSTANCEDSTATICMESHES')
    lib.set_base_material_usage(material,usage,True)
    tag = TAG+KEY+':'
    def node(role,cls,**values):
        n = lib.create_material_expression(material,cls,-700,0)
        require(n, 'Cannot create Periwinkle expression')
        n.set_editor_property('desc',tag+role)
        for key,value in values.items():
            n.set_editor_property(key,value)
        return n
    def connect(a,channel,b,input_):
        require(lib.connect_material_expressions(a,channel,b,input_), 'Cannot connect original Periwinkle graph')
    uv = node('uv',u.MaterialExpressionTextureCoordinate,coordinate_index=0,u_tiling=1.,v_tiling=1.)
    samples = {}
    for role,texture in textures.items():
        sampler = 'SAMPLERTYPENORMAL' if role == 'normalGl' else 'SAMPLERTYPEMASKS' if role in ('opacity','roughness') else 'SAMPLERTYPECOLOR'
        samples[role] = node(role,u.MaterialExpressionTextureSample,texture=texture,
            sampler_type=d.enum(u,'MaterialSamplerType',sampler))
        connect(uv,'',samples[role],'UVs')
    zero = node('metallic-zero',u.MaterialExpressionConstant,r=0.)
    specular = node('dielectric-specular',u.MaterialExpressionConstant,r=.5)
    strength = node('strength',u.MaterialExpressionConstant,r=recipe['subsurfaceCalibration'])
    transmission = node('transmission',u.MaterialExpressionMultiply)
    connect(samples['translucency'],'RGB',transmission,'A'); connect(strength,'',transmission,'B')
    for n,channel,property_ in [(samples['albedo'],'RGB','BASE_COLOR'),(samples['normalGl'],'RGB','NORMAL'),
        (samples['roughness'],'R','ROUGHNESS'),(zero,'','METALLIC'),(specular,'','SPECULAR'),
        (samples['opacity'],'R','OPACITY_MASK'),(transmission,'','SUBSURFACE_COLOR')]:
        require(lib.connect_material_property(n,channel,getattr(u.MaterialProperty,'MP_'+property_)), 'Cannot bind original Periwinkle graph root')
    errors = list(lib.recompile_material(material) or [])
    require(not errors, 'Original Periwinkle shader compile failed: '+str(errors))
    graph = graph_snapshot(u,material)
    audit = check_graph(graph,{r:t.get_path_name() for r,t in textures.items()})
    policy = check_material_policy(u,material)
    metadata = _metadata(u,material,'material',write=True)
    report = {'schema':SCHEMA,'owner':OWNER,'status':'owned-original-five-map-periwinkle-material-created',
        'sourceRecipe':pin(RECIPE),'recipe':recipe,'asset':material.get_path_name(),'graph':graph,'graphSha256':digest(graph),
        'policy':policy,'textures':reports,'metadata':metadata,'compileErrors':errors,'audit':audit,
        'nativeEnumPreflight':enums,'newPackageAssets':package_assets(recipe),'materialCount':1,'textureObjectCount':5,
        'instancedStaticMeshUsage':bool(lib.has_material_usage(material,usage)),
        'sourceOriginalAlphaMode':'BLEND','ownedUnrealBlendMode':'MASKED','sourcePngBits':16,
        'source16BitDoesNotProveNativePixelFormat':True,'originalTexturePixelsEdited':False,
        'nativeImportedPixelsDecoded':False,'nativeSourcePixelFormatReadbackAvailable':False,
        'nativeGpuPixelFormatReadbackAvailable':False,'nativeNormalTangentReadbackAvailable':False,
        'materialPackagesIndependentlyUnloaded':False,'sourceOpticalModelExactlyReproduced':False,
        'physicalOpticalCalibrationAccepted':False,'nativeAppearanceAccepted':False,
        'fullPhotorealismAccepted':False,'performanceAccepted':False}
    validate_recipe(recipe)
    return material,report


def verify_materials(u, report, recipe, graph_snapshot):
    validate_recipe(recipe)
    require(report['schema'] == SCHEMA and report['owner'] == OWNER and report['status']
        == 'owned-original-five-map-periwinkle-material-created' and report['sourceRecipe'] == pin(RECIPE)
        and report['recipe'] == recipe and report['materialCount'] == 1 and report['textureObjectCount'] == 5
        and report['newPackageAssets'] == package_assets(recipe) and report['compileErrors'] == []
        and report['nativeEnumPreflight'] == preflight_enums(u), 'Typed six-package Periwinkle receipt differs')
    require(report['sourceOriginalAlphaMode'] == 'BLEND' and report['ownedUnrealBlendMode'] == 'MASKED'
        and report['sourcePngBits'] == 16 and report['source16BitDoesNotProveNativePixelFormat'] is True,
        'Original/proposed alpha and pixel-evidence scope changed')
    for key in ('originalTexturePixelsEdited','nativeImportedPixelsDecoded','nativeSourcePixelFormatReadbackAvailable',
        'nativeGpuPixelFormatReadbackAvailable','nativeNormalTangentReadbackAvailable','materialPackagesIndependentlyUnloaded',
        'sourceOpticalModelExactlyReproduced','physicalOpticalCalibrationAccepted','nativeAppearanceAccepted',
        'fullPhotorealismAccepted','performanceAccepted'):
        require(report[key] is False, 'Periwinkle material receipt overstates evidence: '+key)
    require(set(report['textures']) == set(ROLES) and report['asset'] == PREFIX+'/Materials/M_'+KEY+'.M_'+KEY,
        'Foreign graph or incomplete original maps')
    material = u.EditorAssetLibrary.load_asset(report['asset'])
    require(isinstance(material,u.Material) and graph_snapshot(u,material) == report['graph']
        and digest(report['graph']) == report['graphSha256'] and check_material_policy(u,material) == report['policy'],
        'Saved original Periwinkle graph/settings differ')
    usage = _private().enum(u,'MaterialUsage','INSTANCEDSTATICMESHES')
    require(report['instancedStaticMeshUsage'] is True and u.MaterialEditingLibrary.has_material_usage(material,usage),
        'Instanced Periwinkle usage required')
    require(_metadata(u,material,'material') == report['metadata'], 'Owned graph metadata witness differs')
    for role,row in report['textures'].items():
        source = recipe['maps'][role]
        require(row['source'] == source and row['asset'] == texture_asset(role,source)
            and row['sourcePngHeader'] == png_header(checked(source)), 'Original Periwinkle source texture identity differs')
        texture = u.EditorAssetLibrary.load_asset(row['asset'])
        require(isinstance(texture,u.Texture2D) and _private().texture_snapshot(texture) == row['snapshot'],
            'Saved original Periwinkle map settings differ')
        check_texture_policy(u,row['snapshot'],role)
        require(_metadata(u,texture,role,source) == row['metadata'], 'Owned map metadata witness differs')
        require(all(row[k] is False for k in ('nativeImportedPixelsDecoded','nativeSourcePixelFormatReadbackAvailable',
            'nativeGpuPixelFormatReadbackAvailable')), 'Source precision is not native pixel readback')
    require(check_graph(report['graph'],{r:t['asset'] for r,t in report['textures'].items()}) == report['audit'],
        'Saved original Periwinkle graph audit differs')
    return material
