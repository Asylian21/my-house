"""Rotate coherent oak projection into eleven approved dining timber frames.

Only two new material assets and eleven visible PH component overrides are
authored. Existing assets, texture sampling, finish constants and source actors
remain unchanged. This module is called by the isolated Furniture importer.
"""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/realism-furniture-grain.py'
PREFIX = '/Game/Brezi/Realism/Furniture/Materials'
PROPOSAL = ROOT/'output/unreal/realism-grain-study-20260926-r1/grain-proposal.json'
ROLES = ('BreziRealism:coherent-metric-uv', 'BreziRealism:coherent-scan-normal')
BASIS = '''float3 N=normalize(NormalWS); float3 A=abs(N),T,V;
if(A.x>=A.y && A.x>=A.z){T=float3(0,-sign(N.x),0);V=float3(0,0,-1);}
else if(A.y>=A.z){T=float3(sign(N.y),0,0);V=float3(0,0,-1);}
else{T=float3(0,sign(N.z),0);V=float3(-1,0,0);}
'''


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts/unreal'/file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


study = module('furniture_grain_policy', 'realism-grain-study.py')
require, sha, read = study.require, study.sha, study.read


def frame_prefix(axis):
    require(axis in study.FRAMES, 'Unsupported dining grain axis')
    frame = study.FRAMES[axis]
    vector = lambda row: 'float3('+','.join(str(v) for v in row)+')'
    declarations = '\n'.join('const float3 F'+str(i)+'='+vector(row)+';' for i, row in enumerate(frame))
    # Preserve the geometric world normal for the normal-map suffix. Only the
    # dominant-face decision happens in member coordinates; T/V return to world.
    return ('float3 worldN=normalize(NormalWS);\n'+declarations+'\n'
            'float3 N=float3(dot(worldN,F0),dot(worldN,F1),dot(worldN,F2)); float3 A=abs(N),T,V;\n'
            + BASIS.split('\n', 1)[1]
            + 'T=F0*T.x+F1*T.y+F2*T.z;\nV=F0*V.x+F1*V.y+F2*V.z;\nN=worldN;\n')


def rotated_code(code, axis):
    require(code.startswith(BASIS), 'Unreviewed coherent oak basis')
    return frame_prefix(axis)+code[len(BASIS):]


def expected_graph(graph, axis):
    result = copy.deepcopy(graph)
    for role in ROLES:
        nodes = [node for node in result['nodes'] if node['role'] == role and node['class'] == 'MaterialExpressionCustom']
        require(len(nodes) == 1, 'Ambiguous coherent oak Custom node: '+role)
        node = nodes[0]
        node['values']['code'] = rotated_code(node['values']['code'], axis)
    return result


def validate_proposal(proposal, scene, photoreal):
    require(proposal['owner'] == 'scripts/unreal/realism-grain-study.py'
            and proposal['status'] == 'offline-proposal-validated', 'Unverified grain proposal')
    require(proposal['targetBindingCount'] == 11 and proposal['proposedNewMaterialCount'] == 2
            and proposal['axisCounts'] == {'X': 2, 'Y': 9}
            and proposal['baselineMaterialBindingCount'] == 110, 'Unreviewed grain scope')
    planned = study.selection(scene)
    rows = {row['sourceId']: row for row in proposal['objects']}
    require(len(rows) == len(proposal['objects']) == len(planned) == 11, 'Duplicate/missing grain members')
    require(photoreal['status'] == 'photoreal-import-validated', 'Unverified inherited PH geometry')
    for record in planned:
        row = rows[record['sourceId']]
        require(all(json.dumps(row[key], sort_keys=True) == json.dumps(value, sort_keys=True)
                    for key, value in record.items()), 'Dining member axis or semantics changed')
        overlay = photoreal['geometry']['objects']['PH_'+row['sourceId']]
        require(row['nativeVisualActor'] == overlay['actor'] and row['nativeVisualMesh'] == overlay['mesh']
                and overlay['sourceId'] == row['sourceId'] and row['materialSlot'] == 0
                and row['baselineMaterial'] == proposal['sourceMaterial'], 'Visible dining PH mapping differs')
    for axis in study.FRAMES:
        expected_graph(proposal['sourceMaterialGraph'], axis)
    period = [n for n in proposal['sourceMaterialGraph']['nodes'] if n['role'] == 'BreziRealism:scan-period']
    require(len(period) == 1 and period[0]['values']['r'] == 183.0, 'Original oak period changed')
    return rows


def preflight(output):
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal'), 'Furniture grain output outside workspace')
    proposal = read(PROPOSAL)
    pins = {str(PROPOSAL): sha(PROPOSAL), **proposal['inputPins']}
    for path, value in pins.items():
        require(sha(path) == value, 'Grain proposal input drift: '+path)
    receipt_path = output/'performance-source.json'
    inheritance = read(receipt_path)
    receipts = [(Path(path), value) for path, value in inheritance['receiptPins'].items()
                if Path(path).name == 'photoreal-import-report.json']
    require(inheritance['status'] == 'verified-scene-inherited' and len(receipts) == 1,
            'Inherited PH receipt missing or ambiguous')
    photoreal_path, photoreal_hash = receipts[0]
    require(sha(photoreal_path) == photoreal_hash, 'Inherited PH receipt drift')
    copied_photoreal_path = output/'photoreal-import-report.json'
    require(sha(copied_photoreal_path) == photoreal_hash, 'Copied inherited PH receipt drift')
    scene_path = output/'geometry/scene.json'
    source_scenes = [value for path, value in proposal['inputPins'].items() if Path(path).name == 'scene.json']
    require(source_scenes == [sha(scene_path)], 'Grain scene differs from approved proposal')
    scene = read(scene_path)
    photoreal = read(photoreal_path)
    rows = validate_proposal(proposal, scene, photoreal)
    relative_asset = Path(proposal['sourceMaterial'].split('.')[0].removeprefix('/Game/')).with_suffix('.uasset')
    asset_path = output/'Project/BreziTwin/Content'/relative_asset
    asset_pins = [value for path, value in proposal['inputPins'].items()
                  if Path(path).as_posix().endswith('/Content/'+relative_asset.as_posix())]
    require(asset_pins == [sha(asset_path)], 'Inherited living oak bytes differ from native graph evidence')
    pins.update({str(path): sha(path) for path in (receipt_path, photoreal_path, copied_photoreal_path, scene_path, asset_path)})
    return proposal, rows, pins


def components(u, actors):
    return {c.get_path_name(): (actor, c) for actor in actors.get_all_level_actors()
            for c in actor.get_components_by_class(u.StaticMeshComponent)}


def material_bindings(index, paths):
    return sorted([{'actor': actor.get_path_name(), 'component': c.get_path_name(), 'slot': slot,
                    'material': material.get_path_name()}
                   for actor, c in index.values() for slot in range(c.get_num_materials())
                   if (material := c.get_material(slot)) and material.get_path_name() in paths],
                  key=lambda row: (row['component'], row['slot']))


def apply(u, actors, output):
    proposal, rows, pins = preflight(output)
    snapshot = module('furniture_grain_snapshot', 'photoreal-exterior.py').graph_snapshot
    assets, editing = u.EditorAssetLibrary, u.MaterialEditingLibrary
    original = assets.load_asset(proposal['sourceMaterial'])
    require(original and snapshot(u, original) == proposal['sourceMaterialGraph'], 'Live original oak graph differs')
    index = components(u, actors)
    before_bindings = material_bindings(index, {proposal['sourceMaterial']})
    require(len(before_bindings) == 110, 'Living oak binding population changed')
    for row in rows.values():
        actor, c = index[row['nativeVisualComponent']]
        require(actor.get_path_name() == row['nativeVisualActor'] and c.is_visible()
                and not c.get_editor_property('hidden_in_game') and not actor.get_editor_property('hidden')
                and c.get_editor_property('mobility') == u.ComponentMobility.STATIC
                and c.get_editor_property('static_mesh').get_path_name() == row['nativeVisualMesh']
                and c.get_material(0) == original, 'Approved visible dining member no longer matches')
    pipeline = {str(ROOT/file): sha(ROOT/file) for file in (OWNER, 'scripts/unreal/realism-grain-study.py', 'scripts/unreal/photoreal-exterior.py')}
    report = {'owner': OWNER, 'status': 'authored-reload-pending', 'pipelineFiles': pipeline, 'inputFiles': pins,
              'bindingChanges': [], 'ownedAssets': [], 'materials': {}, 'axisCounts': {'X': 2, 'Y': 9},
              'originalGraphs': {original.get_path_name(): proposal['sourceMaterialGraph']},
              'protectedGraphs': {original.get_path_name(): proposal['sourceMaterialGraph']},
              'originalBindingCount': len(before_bindings), 'protectedBindingCount': len(before_bindings)-len(rows),
              'geometryModified': False, 'collisionModified': False, 'nativeRenderedVerified': False}
    clones = {}
    for axis in ('X', 'Y'):
        path = PREFIX+'/M_dining_oak_grain_'+axis
        require(not assets.does_asset_exist(path), 'Grain material already exists; use a fresh output')
        material = assets.duplicate_asset(original.get_path_name(), path)
        require(material and snapshot(u, material) == proposal['sourceMaterialGraph'], 'Grain duplicate differs before edit')
        for role in ROLES:
            nodes = [n for n in editing.get_material_expressions(material)
                     if n.get_class().get_name() == 'MaterialExpressionCustom' and n.get_editor_property('desc') == role]
            require(len(nodes) == 1, 'Ambiguous live grain Custom node')
            nodes[0].set_editor_property('code', rotated_code(nodes[0].get_editor_property('code'), axis))
        require(not list(editing.recompile_material(material)), 'Grain shader compilation failed')
        expected = expected_graph(proposal['sourceMaterialGraph'], axis)
        require(snapshot(u, material) == expected, 'Grain edit changed non-basis material graph')
        assets.set_metadata_tag(material, 'BreziGeneratedBy', OWNER)
        assets.set_metadata_tag(material, 'BreziFurnitureGrainAxis', axis)
        require(assets.save_loaded_asset(material, only_if_is_dirty=False), 'Cannot save grain material')
        clones[axis] = material
        report['ownedAssets'].append(material.get_path_name())
        report['materials'][material.get_path_name()] = {'axis': axis, 'originalAsset': original.get_path_name(), 'graph': expected}
    for row in rows.values():
        actor, c = index[row['nativeVisualComponent']]
        axis = row['worldGrainAxis']
        c.set_material(0, clones[axis])
        report['bindingChanges'].append({'actor': actor.get_path_name(), 'component': c.get_path_name(), 'slot': 0,
            'before': original.get_path_name(), 'after': clones[axis].get_path_name(), 'sourceName': study.SOURCE_NAME,
            'sourceId': row['sourceId'], 'axis': axis})
    replacements = {(r['component'], r['slot']): r['after'] for r in report['bindingChanges']}
    report['expectedBindings'] = [{**r, 'material': replacements.get((r['component'], r['slot']), r['material'])} for r in before_bindings]
    verify(u, actors, report)
    return report


def verify(u, actors, report):
    snapshot = module('furniture_grain_verify_snapshot', 'photoreal-exterior.py').graph_snapshot
    index = components(u, actors)
    require(report['owner'] == OWNER and len(report['ownedAssets']) == 2 and len(report['bindingChanges']) == 11,
            'Grain receipt scope differs')
    for path, graph in report['originalGraphs'].items():
        material = u.EditorAssetLibrary.load_asset(path)
        require(material and snapshot(u, material) == graph, 'Original oak graph changed')
    require(report['originalGraphs'] == report['protectedGraphs'], 'Original oak protection differs')
    for path, entry in report['materials'].items():
        material = u.EditorAssetLibrary.load_asset(path)
        require(material and u.EditorAssetLibrary.get_metadata_tag(material, 'BreziGeneratedBy') == OWNER
                and u.EditorAssetLibrary.get_metadata_tag(material, 'BreziFurnitureGrainAxis') == entry['axis']
                and snapshot(u, material) == entry['graph'], 'Saved grain graph or ownership differs')
        require(entry['graph'] == expected_graph(report['originalGraphs'][entry['originalAsset']], entry['axis']),
                'Saved grain changed protected finish')
    actual = material_bindings(index, set(report['originalGraphs']) | set(report['ownedAssets']))
    require(actual == report['expectedBindings'], 'Living oak binding outside approved eleven changed')
    for path, value in {**report['pipelineFiles'], **report['inputFiles']}.items():
        require(sha(path) == value, 'Grain provenance changed: '+path)
    return {'status': 'grain-materials-saved-verified', 'materials': report['materials'],
            'bindingCount': 11, 'protectedBindingCount': 99, 'nativeRenderedVerified': False}
