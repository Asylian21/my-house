"""One owned R34 material using the unchanged original Fern02 atlas/writer.

The private writer retains its original source KEY and maps; only its owned
namespace/owner/tags change. This is source preparation, not native appearance.
"""
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-fern-only-materials-r34.py'
SCHEMA = 'brezi-garden-fern-only-original-material-r34'
PREFIX = '/Game/Brezi/GardenFernOnly20261002R34/Fern'
TAG = 'BreziGardenFernOnlyR34:'
KEY = 'ph_original_fern_02_b_r25'
RECIPE = ROOT/'output/unreal/exterior-garden-fern-only-20261002-r34-study/material-recipe.json'
RECIPE_SHA = '4f4de9417d0a3a3f5f6f2ef5f0fda70c8c9af88e7892da1d5f4ab3583a6d5cb6'
DELEGATE = ROOT/'scripts/unreal/exterior-garden-fern-materials-r25.py'
DELEGATE_SHA = '07de6de2e384802228b6316a15aca0fe327525084eb9141615508b1040fda34f'
_PRIVATE = None


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(file):
    import hashlib
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def pin(file):
    file = Path(file).resolve()
    return {'path': str(file), 'sha256': sha(file), 'bytes': file.stat().st_size}


def _private():
    global _PRIVATE
    require(DELEGATE.is_file() and not DELEGATE.is_symlink() and sha(DELEGATE) == DELEGATE_SHA
        and DELEGATE.stat().st_size == 23012, 'Frozen original fern writer changed')
    if _PRIVATE is None:
        spec = importlib.util.spec_from_file_location('_r34_private_original_fern', DELEGATE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        require(module.KEY == KEY, 'Original fern recipe identity differs')
        module.PREFIX, module.OWNER, module.TAG = PREFIX, OWNER, TAG
        _PRIVATE = module
    require((_PRIVATE.PREFIX, _PRIVATE.OWNER, _PRIVATE.TAG, _PRIVATE.KEY) == (PREFIX, OWNER, TAG, KEY),
        'Private R34 ownership or original recipe identity differs')
    return _PRIVATE


def preflight_enums(u):
    """Resolve the frozen complete enum surface before any asset creation."""
    return _private().preflight_enums(u)


def validate_recipe(recipe):
    require(RECIPE.is_file() and not RECIPE.is_symlink() and sha(RECIPE) == RECIPE_SHA
        and RECIPE.stat().st_size == 1546 and recipe == json.loads(RECIPE.read_text()),
        'Exact typed R34 one-original-fern recipe required')
    require(recipe['schema'] == 'brezi-garden-fern-only-material-recipe-r34'
        and recipe['owner'] == 'scripts/unreal/exterior-garden-fern-only-study-r34.py'
        and recipe['status'] == 'source-one-original-fern-map-recipe-native-pending'
        and recipe['prefix'] == PREFIX and recipe['newOwnerTag'] == TAG
        and recipe['privateSourceDelegateKeyMustRemainOriginal'] == KEY
        and recipe['sourceVariants'] == ['fern_02_a', 'fern_02_c', 'fern_02_d']
        and recipe['sameOriginalProviderMaterialAndAtlasForAllVariants'] is True
        and recipe['originalAlphaMode'] == 'MASK' and recipe['originalDoubleSided'] is True
        and recipe['materialCount'] == 1 and recipe['textureObjectCount'] == 4,
        'R34 original source/ownership/census differs')
    for key in ('sourcePixelsEdited', 'nativeR34Applied', 'nativeAppearanceAccepted'):
        require(recipe[key] is False, 'Source material recipe cannot grant native acceptance')
    d = _private()
    for key in ('sourcePlan', 'sourceDelegate'):
        row = recipe[key]
        file = Path(row['path'])
        require(file.is_absolute() and str(file.resolve()) == row['path'] and file.is_relative_to(ROOT)
            and not file.is_symlink() and row == pin(file), 'Original source pin differs: '+key)
    require(recipe['sourceDelegate'] == pin(DELEGATE) and recipe['sourcePlan'] == pin(d.SOURCE),
        'Wrong original fern source/delegate')
    return d.validate_recipe(json.loads(d.SOURCE.read_text()))


def _graph(report):
    d = _private()
    require(report['owner'] == OWNER, 'Graph owner differs')
    require(set(report['textures']) == {'albedo', 'normalGL', 'ARM', 'alpha'}, 'Original four map roles required')
    d.check_graph(report['graph'], {k: v['asset'] for k, v in report['textures'].items()})
    _package_assets(report)


def _package_assets(report):
    require(report['asset'] == PREFIX+'/Materials/M_'+KEY+'.M_'+KEY, 'Owned R34 graph identity differs')
    require(set(report['textures']) == {'albedo', 'normalGL', 'ARM', 'alpha'}, 'Original four map roles required')
    result = [report['asset']]
    for role, row in report['textures'].items():
        name = 'T_'+KEY+'_'+role+'_'+row['source']['sha256'][:16]
        require(row['asset'] == PREFIX+'/Textures/'+name+'.'+name, 'Owned R34 original map identity differs')
        result.append(row['asset'])
    require(len(result) == len(set(result)) == 5, 'Exactly five graph/map packages required')
    return sorted(result)


def _metadata(u, material, report, write=False):
    for path in _package_assets(report):
        obj = material if path == report['asset'] else u.EditorAssetLibrary.load_asset(path)
        require(obj is not None, 'Owned original fern asset missing')
        wanted = {'BreziGeneratedBy': OWNER, 'BreziR34SourceRecipeSha256': RECIPE_SHA,
            'BreziR34MaterialRole': 'fern'}
        for key, value in wanted.items():
            if write:
                u.EditorAssetLibrary.set_metadata_tag(obj, key, value)
            require(u.EditorAssetLibrary.get_metadata_tag(obj, key) == value, 'Owned R34 metadata differs')
        if write:
            require(u.EditorAssetLibrary.save_loaded_asset(obj, False), 'Cannot save R34 owned provenance')


def build_materials(u, recipe, graph_snapshot):
    validate_recipe(recipe)
    enums = preflight_enums(u)
    d = _private()
    material, delegated = d.build_materials(u, json.loads(d.SOURCE.read_text()), graph_snapshot)
    _graph(delegated)
    _metadata(u, material, delegated, write=True)
    validate_recipe(recipe)
    report = {'schema': SCHEMA, 'owner': OWNER, 'status': 'owned-original-fern-only-material-created',
        'sourceRecipe': pin(RECIPE), 'recipe': recipe, 'asset': delegated['asset'], 'delegate': delegated,
        'newPackageAssets': _package_assets(delegated), 'materialCount': 1, 'textureObjectCount': 4,
        'nativeEnumPreflight': enums, 'nativeGraphsAndTextureSettingsObserved': True,
        'originalProviderAlphaMode': 'MASK', 'ownedUnrealBlendMode': 'MASKED',
        'alphaRoute': 'unchanged original 16-bit PNG normalized R -> OpacityMask cutoff0.5',
        'sourceAlphaBits': 16, 'sourceAlphaBitsDoNotProveNativePixelFormat': True,
        'sourcePixelsEdited': False, 'nativeImportedPixelsDecoded': False,
        'nativeSourcePixelFormatReadbackAvailable': False, 'nativeGpuPixelFormatReadbackAvailable': False,
        'nativeNormalTangentReadbackAvailable': False, 'materialPackagesIndependentlyUnloaded': False,
        'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False}
    return material, report


def verify_materials(u, report, recipe, graph_snapshot):
    validate_recipe(recipe)
    require(report['schema'] == SCHEMA and report['owner'] == OWNER
        and report['status'] == 'owned-original-fern-only-material-created'
        and report['sourceRecipe'] == pin(RECIPE) and report['recipe'] == recipe
        and report['asset'] == report['delegate']['asset'] and report['materialCount'] == 1
        and report['textureObjectCount'] == 4 and report['nativeEnumPreflight'] == preflight_enums(u)
        and report['nativeGraphsAndTextureSettingsObserved'] is True
        and report['newPackageAssets'] == _package_assets(report['delegate']), 'Typed R34 material receipt differs')
    require(report['originalProviderAlphaMode'] == 'MASK' and report['ownedUnrealBlendMode'] == 'MASKED'
        and report['alphaRoute'] == recipe['alphaRoute'] and report['sourceAlphaBits'] == 16
        and report['sourceAlphaBitsDoNotProveNativePixelFormat'] is True, 'Original alpha interpretation differs')
    for key in ('sourcePixelsEdited', 'nativeImportedPixelsDecoded', 'nativeSourcePixelFormatReadbackAvailable',
        'nativeGpuPixelFormatReadbackAvailable', 'nativeNormalTangentReadbackAvailable',
        'materialPackagesIndependentlyUnloaded', 'nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted'):
        require(report[key] is False, 'Material receipt overstates source/native evidence')
    d = _private()
    material = d.verify_materials(u, report['delegate'], json.loads(d.SOURCE.read_text()), graph_snapshot)
    _graph(report['delegate'])
    _metadata(u, material, report['delegate'])
    return material
