"""One fixed scene-linear emission correction over the immutable R6 fire.

Only the existing Custom expression's final multiplier changes, from 3 to 512.
No exposure compensation, texture, glass, ember, geometry or lighting edits.
Native translucency diagnostics are recorded for both the fire and its glass.
"""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/realism-stove-calibration-material.py'
DESTINATION = '/Game/Brezi/Realism/StoveCalibration/Materials/M_Stove_Flames_512'
SOURCE = '/Game/Brezi/Realism/Stove/Materials/M_Stove_Flames.M_Stove_Flames'
ROLE = 'BreziRealismStove:density-weighted-fire-emission'
RECIPE = {'kind': 'fixed-scene-linear-fire-emission-calibration', 'before': 3., 'after': 512.,
          'changedNode': ROLE, 'exposureCompensation': False, 'otherGraphChanges': False,
          'scope': 'authored candidate from native day/night exposure evidence, not measured fire photometry'}


def module(file):
    spec = importlib.util.spec_from_file_location('stove_calibration_'+file.replace('-', '_'), ROOT/'scripts/unreal'/file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


prior = module('realism-stove-materials.py')
require, sha, snapshot = prior.require, prior.sha, prior.graph_snapshot


def read(path):
    return json.loads(Path(path).read_text())


def calibrated_code(code):
    before, after = 'return tint*Density*3.0;', 'return tint*Density*512.0;'
    require(code == prior.emission_hlsl() and code.endswith(before) and code.count(before) == 1,
            'Fire emission no longer matches the exact reviewed R6 shader')
    return code[:-len(before)]+after


def expected_graph(graph):
    value = copy.deepcopy(graph)
    nodes = [n for n in value['nodes'] if n['role'] == ROLE and n['class'] == 'MaterialExpressionCustom']
    require(len(nodes) == 1, 'Missing or ambiguous R6 fire emission expression')
    nodes[0]['values']['code'] = calibrated_code(nodes[0]['values']['code'])
    return value


def preflight(output):
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal'), 'Calibration output must be isolated under output/unreal')
    inheritance_path = output/'performance-source.json'
    inheritance = read(inheritance_path)
    require(inheritance['status'] == 'verified-scene-inherited', 'Calibration requires verified scene inheritance')
    source = Path(inheritance['donor']).resolve()
    require(source != output and source.is_relative_to(ROOT/'output/unreal'), 'Invalid calibration donor')
    package_path = source/'model-package.json'
    require(inheritance['receiptPins'].get(str(package_path)) == sha(package_path), 'Inherited package pin changed')
    package = read(package_path)
    report_path = source/'realism-stove-report.json'
    report_sha = sha(report_path)
    require(package['inputs'].get(str(report_path)) == report_sha
            and package['stove']['reportSha256'] == report_sha, 'R6 stove report is not pinned by its package')
    stove = read(report_path)
    require(stove['status'] == 'realism-stove-validated' and stove['savedReloaded']
            and stove['protectedContentUnchanged'] and stove['originalMaterialAssetsPreserved'], 'Native R6 source is unverified')
    material_report = stove['savedMaterialReadback']
    require(material_report['status'] == 'saved-reloaded-validated'
            and material_report['materials']['flames'] == SOURCE, 'Unknown R6 flame source')
    target = stove['objects']['RFIRE_FLAMES']
    require(target['materials'] == [SOURCE] and target['materialRole'] == 'flames'
            and target['sourceIds'] == ['DOM_00564', 'DOM_00565', 'DOM_00566'], 'R6 flame binding identity changed')
    graph = material_report['graphs'][SOURCE]
    expected_graph(graph)
    relative = Path(SOURCE.split('.')[0].removeprefix('/Game/')).with_suffix('.uasset')
    original = Path(package['project'])/'Content'/relative
    copied = output/'Project/BreziTwin/Content'/relative
    expected_sha = package['inputs'].get(str(original))
    require(expected_sha and sha(original) == expected_sha and sha(copied) == expected_sha,
            'Original/copied R6 flame asset bytes differ from the accepted graph')
    pins = {str(p): sha(p) for p in (inheritance_path, package_path, report_path, original, copied)}
    return stove, target, graph, pins


def component_index(u, actors):
    return {c.get_path_name(): (a, c) for a in prior.actor_list(actors) for c in a.get_components_by_class(u.StaticMeshComponent)}


def match_component(index, target, material_path):
    require(target['component'] in index, 'Calibration target component missing')
    actor, component = index[target['component']]
    require(actor.get_path_name() == target['actor'] and component.get_num_materials() == 1
            and component.get_editor_property('static_mesh').get_path_name() == target['mesh']
            and component.get_material(0) and component.get_material(0).get_path_name() == material_path,
            'Calibration target actor, mesh, slot or material changed')
    return actor, component


def selected_bindings(index, materials):
    rows = []
    for actor, component in index.values():
        for slot in range(component.get_num_materials()):
            material = component.get_material(slot)
            if material and material.get_path_name() in materials:
                rows.append({'actor': actor.get_path_name(), 'component': component.get_path_name(),
                             'slot': slot, 'material': material.get_path_name()})
    return sorted(rows, key=lambda r: (r['component'], r['slot']))


def native_diagnostics(u, index, flame_target, glass_target):
    result = {}
    for role, target in (('flames', flame_target), ('glass', glass_target)):
        actor, component = index[target['component']]
        require(actor.get_path_name() == target['actor'], 'Diagnostic actor identity differs')
        material = component.get_material(0)
        refraction = u.MaterialEditingLibrary.get_material_property_input_node(material, u.MaterialProperty.MP_REFRACTION)
        result[role] = {
            'blendMode': str(material.get_editor_property('blend_mode')),
            'shadingModel': str(material.get_editor_property('shading_model')),
            'translucencyPass': str(material.get_editor_property('translucency_pass')),
            'refractionMethod': str(material.get_editor_property('refraction_method')),
            'refractionInputConnected': refraction is not None,
            'translucencyLightingMode': str(material.get_editor_property('translucency_lighting_mode')),
            'disableDepthTest': bool(material.get_editor_property('disable_depth_test')),
            'sortPriority': int(component.get_editor_property('translucency_sort_priority')),
            'sortDistanceOffset': float(component.get_editor_property('translucency_sort_distance_offset')),
        }
    return result


def apply(u, actors, output):
    stove, target, original_graph, pins = preflight(output)
    assets, lib = u.EditorAssetLibrary, u.MaterialEditingLibrary
    index = component_index(u, actors)
    actor, component = match_component(index, target, SOURCE)
    before = selected_bindings(index, {SOURCE, DESTINATION+'.'+DESTINATION.rsplit('/', 1)[1]})
    require(before == [{'actor': target['actor'], 'component': target['component'], 'slot': 0, 'material': SOURCE}],
            'R6 flame material is missing or shared beyond the approved component')
    original = assets.load_asset(SOURCE)
    require(original and snapshot(u, original) == original_graph
            and assets.get_metadata_tag(original, 'BreziGeneratedBy') == prior.OWNER,
            'Live R6 flame graph or owner differs from accepted source')
    originals = {**stove['savedMaterialReadback']['originalGraphs'], **stove['savedMaterialReadback']['graphs']}
    require(all(snapshot(u, assets.load_asset(path)) == graph for path, graph in originals.items()), 'Protected R6 stove graph drift')
    glass = stove['savedMaterialReadback']['sourceBindings']['DOM_00557']
    diagnostics_before = native_diagnostics(u, index, target, glass)
    require(not assets.does_asset_exist(DESTINATION), 'Calibration material already exists; use a fresh output')
    material = assets.duplicate_asset(SOURCE, DESTINATION)
    require(material and snapshot(u, material) == original_graph, 'R6 fire duplicate changed before calibration')
    nodes = [n for n in lib.get_material_expressions(material)
             if n.get_class().get_name() == 'MaterialExpressionCustom' and n.get_editor_property('desc') == ROLE]
    require(len(nodes) == 1, 'Ambiguous live fire emission expression')
    nodes[0].set_editor_property('code', calibrated_code(str(nodes[0].get_editor_property('code'))))
    expected = expected_graph(original_graph)
    require(snapshot(u, material) == expected, 'Calibration changed another node, texture, UV or flag')
    require(not list(lib.recompile_material(material)), 'Calibrated fire shader failed to compile')
    assets.set_metadata_tag(material, 'BreziGeneratedBy', OWNER)
    assets.set_metadata_tag(material, 'BreziStoveCalibrationRecipe', json.dumps(RECIPE, sort_keys=True))
    require(assets.save_loaded_asset(material, only_if_is_dirty=False), 'Cannot save calibrated flame material')
    require(snapshot(u, material) == expected, 'Calibrated graph changed during save')
    component.set_material(0, material)
    diagnostics_after = native_diagnostics(u, index, target, glass)
    require(diagnostics_after == diagnostics_before, 'Calibration changed translucency/refraction/sorting policy')
    require(all(snapshot(u, assets.load_asset(path)) == graph for path, graph in originals.items()), 'Original R6 graph changed')
    path = material.get_path_name()
    require(selected_bindings(index, {SOURCE, path}) == [{'actor': target['actor'], 'component': target['component'], 'slot': 0, 'material': path}],
            'Unexpected calibration binding population')
    return {'schemaVersion': 1, 'owner': OWNER, 'status': 'authored-reload-pending',
            'pipelineFiles': {str(ROOT/'scripts/unreal'/p): sha(ROOT/'scripts/unreal'/p) for p in
                              ('realism-stove-calibration-material.py', 'realism-stove-materials.py', 'photoreal-exterior.py')},
            'inputFiles': pins, 'sourceTarget': target, 'glassTarget': glass,
            'sourceMaterialGraph': original_graph, 'originalGraphs': originals, 'protectedGraphs': copy.deepcopy(originals),
            'materials': {path: {'sourceAsset': SOURCE, 'graph': expected, 'recipe': copy.deepcopy(RECIPE)}},
            'ownedAssets': [path], 'bindingChanges': [{'actor': actor.get_path_name(), 'component': component.get_path_name(),
                'slot': 0, 'before': SOURCE, 'after': path, 'sourceName': 'RFIRE_FLAMES'}],
            'diagnosticsBefore': diagnostics_before, 'diagnosticsAfter': diagnostics_after,
            'geometryModified': False, 'collisionModified': False, 'lightingModified': False,
            'glassModified': False, 'emberModified': False, 'nativeRenderedVerified': False,
            'limitations': ['Fixed scene-linear emission is an authored native calibration candidate; day/night appearance remains a separate gate.']}


def verify(u, actors, report):
    index = component_index(u, actors)
    require(len(report['bindingChanges']) == len(report['ownedAssets']) == len(report['materials']) == 1,
            'Calibration scope is no longer one material and binding')
    change = report['bindingChanges'][0]
    path = report['ownedAssets'][0]
    require(change['before'] == SOURCE and change['after'] == path and change['slot'] == 0, 'Saved calibration binding scope differs')
    match_component(index, report['sourceTarget'], path)
    material = u.EditorAssetLibrary.load_asset(path)
    require(material and u.EditorAssetLibrary.get_metadata_tag(material, 'BreziGeneratedBy') == OWNER
            and u.EditorAssetLibrary.get_metadata_tag(material, 'BreziStoveCalibrationRecipe') == json.dumps(RECIPE, sort_keys=True),
            'Saved calibration ownership or recipe changed')
    graph = snapshot(u, material)
    require(graph == report['materials'][path]['graph'] == expected_graph(report['sourceMaterialGraph']),
            'Saved calibrated graph changed beyond the single emission multiplier')
    for original_path, original_graph in report['originalGraphs'].items():
        require(snapshot(u, u.EditorAssetLibrary.load_asset(original_path)) == original_graph, 'Saved original stove graph changed')
    require(selected_bindings(index, {SOURCE, path}) == [{'actor': change['actor'], 'component': change['component'], 'slot': 0, 'material': path}],
            'Saved calibration binding population changed')
    diagnostics = native_diagnostics(u, index, report['sourceTarget'], report['glassTarget'])
    require(diagnostics == report['diagnosticsBefore'] == report['diagnosticsAfter'], 'Saved translucency/refraction/sorting diagnostics changed')
    return {**report, 'status': 'saved-reloaded-validated', 'savedReloaded': True, 'diagnosticsReloaded': diagnostics}
