"""Root-only READ-ONLY observation of preserved R2 USD import assets.

No import, property setter, actor/map operation, or asset save is performed.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'output/unreal/megaplants-english-oak-native-20261002-r1'
READINESS = OUTPUT / 'oak-usd-partial-diagnostic-readiness-r1.json'
REPORT = OUTPUT / 'oak-usd-partial-assets-diagnostic-r1.json'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


g = module('oak_partial_source_guard', ROOT / 'scripts/unreal/megaplants-english-oak-pilot-guards-r2.py')


def optional_property(obj, key, convert):
    try:
        return {'available': True, 'value': convert(obj.get_editor_property(key))}
    except Exception as error:
        return {'available': False, 'limitation': str(error)}


def run(u):
    readiness = g.read(READINESS)
    g.require(readiness['status'] == 'source-ready-read-only-existing-partial-oak-assets-diagnostic', 'Exact diagnostic readiness required')
    for row in readiness['inputFiles']:
        g.check_pin(row)
    before = g.read(g.check_pin(readiness['currentPartialInventory']))
    g.require(Path(u.Paths.project_dir()).resolve() == g.PROJECT, 'Diagnostic must use existing failed R2 project only')
    g.require(g.inventory(g.PROJECT) == before, 'Preserved partial project bytes changed before diagnostic')
    source_before = g.inventory(g.BASE / 'Project/BreziTwin')
    g.require(not REPORT.exists(), 'Never overwrite diagnostic history')
    rows = []
    paths = u.EditorAssetLibrary.list_assets(g.PREFIX + '/OriginalUSD', recursive=True, include_folder=False)
    for path in paths:
        asset = u.load_asset(path)
        g.require(asset is not None, 'Existing partial asset could not load: ' + path)
        row = {'path': asset.get_path_name(), 'name': asset.get_name(), 'class': asset.get_class().get_path_name(),
               'metadataTags': {str(k): str(v) for k, v in u.EditorAssetLibrary.get_metadata_tag_values(asset).items()}}
        if isinstance(asset, (u.StaticMesh, u.SkeletalMesh)):
            settings = asset.get_editor_property('nanite_settings')
            row['naniteEnabledSetting'] = bool(settings.get_editor_property('enabled'))
            def assembly_value(assembly):
                parts = assembly.get_editor_property('parts')
                result = {'parts': []}
                for part in parts:
                    part_path = u.SystemLibrary.break_soft_object_path(part.get_editor_property('mesh_object_path'))
                    part_asset = u.load_asset(part_path)
                    result['parts'].append({'path': part_path,
                                            'class': part_asset.get_class().get_path_name() if part_asset else None})
                result['nodes'] = optional_property(assembly, 'nodes', lambda nodes: {
                    'count': len(nodes),
                    'partIndices': [int(n.get_editor_property('part_index')) for n in nodes]})
                return result
            row['assembly'] = optional_property(settings, 'nanite_assembly_data', assembly_value)
            def user_data_value(values):
                return [{'class': item.get_class().get_path_name(),
                         'primPaths': optional_property(item, 'prim_paths', lambda a: [str(x) for x in a]),
                         'originalHash': optional_property(item, 'original_hash', str)} for item in values]
            row['usdUserData'] = optional_property(asset, 'asset_user_data', user_data_value)
        if isinstance(asset, u.MaterialInstanceConstant):
            row['parent'] = asset.get_editor_property('parent').get_path_name()
            row['vectorParameters'] = {str(n): [v.r, v.g, v.b, v.a] for n in
                u.MaterialEditingLibrary.get_vector_parameter_names(asset)
                for v in [u.MaterialEditingLibrary.get_material_instance_vector_parameter_value(asset, n)]}
            row['authoredTextureParameterCount'] = len(asset.get_editor_property('texture_parameter_values'))
        rows.append(row)
    g.require(g.inventory(g.PROJECT) == before, 'Read-only diagnostic changed preserved partial project bytes')
    g.require(g.inventory(g.BASE / 'Project/BreziTwin') == source_before, 'Read-only diagnostic changed original saved R32')
    for row in readiness['inputFiles']:
        g.check_pin(row)
    result = {'schema': 'brezi-original-oak-preserved-partial-usd-assets-read-only-diagnostic-r1',
              'owner': 'scripts/unreal/megaplants-english-oak-partial-diagnostic-r1.py',
              'status': 'completed-read-only-original-partial-usd-asset-observation',
              'nativeProcessId': os.getpid(), 'readiness': g.pin(READINESS), 'assets': rows,
              'assetCount': len(rows), 'startupAllowAssemblies': u.SystemLibrary.get_console_variable_int_value('r.Nanite.AllowAssemblies'),
              'startupNaniteFoliage': u.SystemLibrary.get_console_variable_int_value('r.Nanite.Foliage'),
              'partialProjectInventoryBeforeAndAfter': readiness['currentPartialInventory'],
              'partialProjectUnchanged': True, 'originalSavedR32ProjectUnchanged': True,
              'assetImportExecuted': False, 'assetOrMapSaveExecuted': False, 'sceneMutationExecuted': False,
              'nativeFullGeometryCornerReadbackAvailable': False, 'importedNormalsTangentsPreserved': False,
              'assemblyCompletenessAccepted': False, 'nativeAppearanceAccepted': False,
              'performanceAccepted': False, 'fullPhotorealismAccepted': False}
    g.write(REPORT, result)
    print(json.dumps({'report': g.pin(REPORT), 'assetCount': len(rows)}))


if __name__ == '__main__':
    import unreal
    run(unreal)
