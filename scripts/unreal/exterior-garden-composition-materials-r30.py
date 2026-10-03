"""Two NEW R30 graphs using unchanged original Fern02 and GrassMedium01 maps.

Private copies of the frozen writers retain their source recipe interpretation.
Only their asset namespace, owner and expression tags change. Provider fern
MASK and grass BLEND are distinct from the artistic UE masked-foliage choice.
Native texture settings are observable; decoded native pixels/GPU format and
appearance are not inferred from source PNG precision or an imported graph.
"""
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-composition-materials-r30.py'
SCHEMA = 'brezi-garden-composition-two-original-materials-r30'
PREFIX = '/Game/Brezi/GardenComposition20261002R30'
TAG = 'BreziGardenCompositionR30:'
RECIPE = ROOT/'output/unreal/exterior-garden-composition-20261002-r30-geometry-study/material-recipes.json'
RECIPE_SHA = '2ff4f9a84eb06e9bd1380034155e3c39c7ca52c7878996699f0b4a67bf66804d'
DELEGATES = {
    'fern': (ROOT/'scripts/unreal/exterior-garden-fern-materials-r25.py',
        '07de6de2e384802228b6316a15aca0fe327525084eb9141615508b1040fda34f', 23012),
    'grass': (ROOT/'scripts/unreal/exterior-curved-grass-materials-r3.py',
        'c149291fde2a5ae723adafc5d80619ee663103a57c50e60337cc83fe0c60a797', 17558)}
_PRIVATE = {}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(file):
    import hashlib
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def pin(file):
    file = Path(file).resolve()
    return {'path': str(file), 'sha256': sha(file), 'bytes': file.stat().st_size}


def _private(role):
    file, digest, size = DELEGATES[role]
    require(file.is_file() and not file.is_symlink() and sha(file) == digest
        and file.stat().st_size == size, 'Frozen original material writer changed: '+role)
    if role not in _PRIVATE:
        # No sys.modules publication or mutation of a previously loaded writer.
        spec = importlib.util.spec_from_file_location('_r30_private_original_'+role, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_key = module.KEY
        module.PREFIX = PREFIX+'/'+role.capitalize()
        module.OWNER = OWNER
        module.TAG = TAG+role+':'
        require(module.KEY == original_key, 'Original source recipe ID must remain unchanged')
        _PRIVATE[role] = module
    result = _PRIVATE[role]
    require(result.PREFIX == PREFIX+'/'+role.capitalize() and result.OWNER == OWNER
        and result.TAG == TAG+role+':' and result.KEY == {
            'fern': 'ph_original_fern_02_b_r25', 'grass': 'ph_original_grass_medium_01_r20'}[role],
        'Private R30 ownership/original recipe identity changed')
    return result


def preflight_enums(u):
    """Resolve BOTH complete enum surfaces before the first asset write."""
    return {'fern': _private('fern').preflight_enums(u),
            'grass': _private('grass').native_enum_preflight(u)}


def validate_recipe(recipe):
    require(RECIPE.is_file() and not RECIPE.is_symlink() and sha(RECIPE) == RECIPE_SHA
        and RECIPE.stat().st_size == 3744 and recipe == json.loads(RECIPE.read_text()),
        'Exact typed R30 two-original-map recipe required')
    require(recipe['schema'] == 'brezi-garden-composition-material-recipes-r30'
        and recipe['owner'] == 'scripts/unreal/exterior-garden-composition-geometry-r30.py'
        and recipe['status'] == 'source-two-original-map-recipes-native-pending'
        and recipe['prefix'] == PREFIX and recipe['newOwnTag'] == TAG
        and recipe['materialCount'] == 2 and recipe['textureObjectCount'] == 8,
        'R30 recipe owner/namespace/census differs')
    for key in ('nativeAppearanceAccepted', 'sourcePixelsEdited', 'nativeApplied'):
        require(recipe[key] is False, 'Source recipe cannot claim native acceptance')
    for key in ('sourceProposal', 'fernSourceStudy', 'fernDelegate', 'grassDelegate'):
        row = recipe[key]
        file = Path(row['path'])
        require(file.is_absolute() and str(file.resolve()) == row['path']
            and file.is_relative_to(ROOT) and not file.is_symlink()
            and row == pin(file), 'Original source/delegate pin differs: '+key)
    fern, grass = _private('fern'), _private('grass')
    require(recipe['fernDelegate'] == pin(DELEGATES['fern'][0])
        and recipe['grassDelegate'] == pin(DELEGATES['grass'][0])
        and recipe['fernSourceStudy'] == pin(fern.SOURCE), 'Wrong original writer/source')
    fern_recipe = fern.validate_recipe(json.loads(fern.SOURCE.read_text()))
    grass.validate_recipe(recipe['grassRecipe'])
    return {'fern': fern_recipe, 'grass': recipe['grassRecipe']}


def _grass_texture_policy(u, snapshot, role):
    g = _private('grass')
    desired = {'srgb': role == 'albedo', 'flip_green_channel': role == 'normal',
        'compression_settings': str(g.enum(u, 'TextureCompressionSettings',
            'TCNormalmap' if role == 'normal' else 'TCMasks' if role in ('arm', 'alpha') else 'TCDefault')),
        'address_x': str(u.TextureAddress.TA_WRAP), 'address_y': str(u.TextureAddress.TA_WRAP),
        'lod_bias': 0, 'max_texture_size': 0, 'virtual_texture_streaming': False,
        'never_stream': False, 'mip_gen_settings': str(u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP),
        'power_of_two_mode': str(u.TexturePowerOfTwoSetting.NONE),
        'do_scale_mips_for_alpha_coverage': role == 'alpha',
        'alphaCoverageThresholds': [.5, 0., 0., 0.] if role == 'alpha' else [0., 0., 0., 0.],
        'sourceEncoding': str(g.enum(u, 'TextureSourceEncoding', 'TSESRGB' if role == 'albedo' else 'TSENONE')),
        'pixels': [2048, 2048]}
    require(snapshot == desired, 'R30 original grass native texture policy differs: '+role)


def _graph(role, report):
    delegate = _private(role)
    textures = {key: value['asset'] for key, value in report['textures'].items()}
    delegate.check_graph(report['graph'], textures)
    require(report['owner'] == OWNER and report['asset'].startswith(delegate.PREFIX+'/Materials/')
        and all(asset.startswith(delegate.PREFIX+'/Textures/') for asset in textures.values()),
        'R30 material/texture escaped its owned role namespace')
    if role == 'grass':
        nodes = {node['role']: node for node in report['graph']['nodes']}
        for texture_role in textures:
            node = nodes[delegate.TAG+texture_role]
            sampler = 'SAMPLERTYPENORMAL' if texture_role == 'normal' else (
                'SAMPLERTYPEMASKS' if texture_role in ('arm', 'alpha') else 'SAMPLERTYPECOLOR')
            value = str(node['values']['sampler_type']).split('.')[1].split(':')[0].replace('_', '').upper()
            require(value == sampler, 'R30 grass sampler interpretation differs')
        require(nodes[delegate.TAG+'original-UV0']['class'] == 'MaterialExpressionTextureCoordinate',
            'R30 grass UV0 expression changed')
        for key in ('provider-metallic-zero', 'ue-subsurface-strength', 'ue-dielectric-specular'):
            require(nodes[delegate.TAG+key]['class'] == 'MaterialExpressionConstant', 'R30 grass factor type changed')
        for key in ('metallic-provider-factor', 'ue-foliage-transmission'):
            require(nodes[delegate.TAG+key]['class'] == 'MaterialExpressionMultiply', 'R30 grass channel operation changed')


def _metadata(u, material, role, role_report, write=False):
    assets = u.EditorAssetLibrary
    paths = [role_report['asset'], *[row['asset'] for row in role_report['textures'].values()]]
    for asset in paths:
        obj = material if asset == role_report['asset'] else assets.load_asset(asset)
        require(obj is not None, 'R30 owned original material asset missing')
        wanted = {'BreziGeneratedBy': OWNER, 'BreziR30MaterialRole': role,
            'BreziR30SourceRecipeSha256': RECIPE_SHA}
        for key, value in wanted.items():
            if write:
                assets.set_metadata_tag(obj, key, value)
            require(assets.get_metadata_tag(obj, key) == value, 'R30 explicit asset ownership differs')
        if write:
            require(assets.save_loaded_asset(obj, False), 'Cannot save R30 owned provenance')


def _package_assets(reports):
    require(set(reports) == {'fern', 'grass'}, 'Both owned R30 material roles required')
    result = []
    for role, report in reports.items():
        d = _private(role)
        require(report['asset'] == d.PREFIX+'/Materials/M_'+d.KEY+'.M_'+d.KEY,
            'R30 graph package identity differs')
        require(set(report['textures']) == ({'albedo', 'normalGL', 'ARM', 'alpha'} if role == 'fern'
            else {'albedo', 'normal', 'arm', 'alpha'}), 'R30 original map role census differs')
        result.append(report['asset'])
        for map_role, row in report['textures'].items():
            name = ('T_'+d.KEY+'_'+map_role+'_'+row['source']['sha256'][:16] if role == 'fern'
                else 'T_R20_PhGrass_'+map_role+'_'+row['source']['sha256'][:16])
            require(row['asset'] == d.PREFIX+'/Textures/'+name+'.'+name,
                'R30 original texture package identity differs')
            result.append(row['asset'])
    require(len(result) == len(set(result)) == 10, 'Exactly ten new R30 graph/texture packages required')
    return sorted(result)


def build_materials(u, recipe, graph_snapshot):
    source = validate_recipe(recipe)
    enum_proof = preflight_enums(u)
    fern, grass = _private('fern'), _private('grass')
    materials, reports = {}, {}
    materials['fern'], reports['fern'] = fern.build_materials(u, json.loads(fern.SOURCE.read_text()), graph_snapshot)
    materials['grass'], reports['grass'] = grass.build_materials(u, source['grass'], graph_snapshot)
    for role in ('fern', 'grass'):
        _graph(role, reports[role])
        _metadata(u, materials[role], role, reports[role], write=True)
    for role, row in reports['grass']['textures'].items():
        _grass_texture_policy(u, row['snapshot'], role)
    validate_recipe(recipe)
    report = {'schema': SCHEMA, 'owner': OWNER, 'status': 'owned-two-original-map-materials-created',
        'sourceRecipe': pin(RECIPE), 'recipe': recipe, 'materials': reports,
        'newPackageAssets': _package_assets(reports),
        'materialCount': 2, 'textureObjectCount': 8, 'nativeEnumPreflight': enum_proof,
        'nativeGraphsAndTextureSettingsObserved': True, 'sourcePixelsEdited': False,
        'providerFernAlphaMode': 'MASK', 'providerGrassAlphaMode': 'BLEND',
        'ownedUnrealBothBlendMode': 'MASKED', 'alphaRoute': 'original separate alpha.R to cutoff0.5',
        'sourceFernAlphaBits': 16, 'sourceAlphaBitsDoNotProveNativePixelFormat': True,
        'nativeImportedPixelsDecoded': False, 'nativeSourcePixelFormatReadbackAvailable': False,
        'nativeGpuPixelFormatReadbackAvailable': False, 'nativeNormalTangentReadbackAvailable': False,
        'materialPackagesIndependentlyUnloaded': False, 'nativeAppearanceAccepted': False,
        'ueOpticalCalibrationAccepted': False, 'performanceAccepted': False, 'fullPhotorealismAccepted': False}
    return materials, report


def verify_materials(u, report, recipe, graph_snapshot):
    validate_recipe(recipe)
    require(report['schema'] == SCHEMA and report['owner'] == OWNER
        and report['status'] == 'owned-two-original-map-materials-created'
        and report['sourceRecipe'] == pin(RECIPE) and report['recipe'] == recipe
        and set(report['materials']) == {'fern', 'grass'} and report['materialCount'] == 2
        and report['textureObjectCount'] == 8 and report['nativeEnumPreflight'] == preflight_enums(u)
        and report['nativeGraphsAndTextureSettingsObserved'] is True,
        'Typed R30 two-graph/eight-map saved receipt required')
    for key in ('sourcePixelsEdited', 'nativeImportedPixelsDecoded', 'nativeSourcePixelFormatReadbackAvailable',
        'nativeGpuPixelFormatReadbackAvailable', 'nativeNormalTangentReadbackAvailable',
        'materialPackagesIndependentlyUnloaded', 'nativeAppearanceAccepted', 'ueOpticalCalibrationAccepted',
        'performanceAccepted', 'fullPhotorealismAccepted'):
        require(report[key] is False, 'R30 material receipt overstates native/appearance evidence')
    require(report['providerFernAlphaMode'] == 'MASK' and report['providerGrassAlphaMode'] == 'BLEND'
        and report['ownedUnrealBothBlendMode'] == 'MASKED'
        and report['alphaRoute'] == 'original separate alpha.R to cutoff0.5'
        and report['sourceFernAlphaBits'] == 16 and report['sourceAlphaBitsDoNotProveNativePixelFormat'] is True,
        'Source-provider and owned UE alpha interpretations must remain distinct')
    require(report['newPackageAssets'] == _package_assets(report['materials']),
        'R30 package receipt differs from its exact two graphs/eight textures')
    fern, grass = _private('fern'), _private('grass')
    materials = {'fern': fern.verify_materials(u, report['materials']['fern'],
        json.loads(fern.SOURCE.read_text()), graph_snapshot),
        'grass': grass.verify_materials(u, report['materials']['grass'], graph_snapshot)}
    for role in ('fern', 'grass'):
        _graph(role, report['materials'][role])
        _metadata(u, materials[role], role, report['materials'][role])
    for role, row in report['materials']['grass']['textures'].items():
        _grass_texture_policy(u, row['snapshot'], role)
    return materials
