"""Correct two proven patio cloth swatches without replacing their weave graph.

Resolve the original assets through the inherited, hash-pinned photoreal receipt.
Duplicate only those assets and reconnect BaseColor/SubsurfaceColor inside the
active MakeMaterialAttributes graph. Roughness, normals, AO and Cloth strength
remain byte-for-byte equivalent graph inputs. No native process starts here.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/realism-fabric.py'
PREFIX = '/Game/Brezi/Realism/Fabric'
TAG = 'BreziRealismFabric:'
SOURCE_OWNER = 'scripts/unreal/photoreal-interior.py'
SOURCES = {'real-fabric': '#e6e2d8', 'real-upholstery-dark': '#22292a'}
COLOR_PINS = {'basecolor', 'subsurfacecolor'}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def normalize(value):
    return re.sub(r'[^a-z0-9]', '', str(value).lower())


def hex_channels(value):
    return [int(value[i:i+2], 16)/255 for i in (1, 3, 5)]


def decode_srgb(value):
    require(math.isfinite(value) and 0 <= value <= 1, 'Invalid cloth sRGB channel')
    return value/12.92 if value <= .04045 else ((value+.055)/1.055)**2.4


def recipe(source, accepted):
    name = source['name']
    require(name in SOURCES and accepted['sourceName'] == name, 'Unreviewed cloth semantic target')
    encoded = hex_channels(SOURCES[name])
    require(source.get('texture') is None and source['alpha'] == 1 and source['metallic'] == 0
            and not any(source['emission']) and len(source['color']) == 3
            and all(abs(a-b) < 1e-8 for a, b in zip(source['color'], encoded)),
            'Cloth source is no longer the proven unconverted swatch: ' + name)
    prior = accepted['recipe']
    require(prior['kind'] == 'woven-linen' and prior['sourceTexturePatternRemoved']
            and len(prior['solidColorLinear']) == 3
            and all(abs(a-b) < 1e-8 for a, b in zip(prior['solidColorLinear'], encoded)),
            'Accepted cloth already corrected or uses another palette: ' + name)
    decoded = [decode_srgb(v) for v in encoded]
    return {'kind': 'source-srgb-cloth-correction', 'sourceName': name,
            'sourceSrgbHex': SOURCES[name], 'sourceFile': 'lib/babylon-scene.ts',
            'originalLinearInterpretation': encoded, 'decodedLinear': decoded,
            'correctionRatio': [a/b for a, b in zip(decoded, encoded)],
            'transfer': 'IEC 61966-2-1 sRGB decoded exactly once',
            'preservedClothRecipe': prior, 'changedAttributes': ['BaseColor', 'SubsurfaceColor'],
            'geometryModified': False}


def select_targets(scene, receipt):
    require(scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'},
            'Cloth correction requires canonical C/B/B')
    require(receipt['status'] == 'photoreal-import-validated' and receipt['savedReloaded'],
            'Accepted saved photoreal import required')
    result = {}
    for slot, accepted in receipt['interior']['materials'].items():
        name = accepted['sourceName']
        if name not in SOURCES:
            continue
        require(slot in scene['materials'] and name not in {r['sourceName'] for r in result.values()},
                'Ambiguous cloth source slot or name')
        r = recipe(scene['materials'][slot], accepted)
        path = accepted['asset']
        require(path.startswith('/Game/Brezi/Photoreal/Interior/Materials/') and path not in result,
                'Unexpected accepted cloth asset namespace or duplicate')
        result[path] = {'sourceSlot': slot, 'sourceName': name, 'accepted': accepted, 'recipe': r}
    require({r['sourceName'] for r in result.values()} == set(SOURCES), 'Exact two cloth targets missing')
    return result


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts/unreal'/file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def load_inputs(output):
    output = Path(output)
    receipt_path, process_path = output/'photoreal-import-report.json', output/'photoreal-import-process.json'
    source_path, scene_path = output/'performance-source.json', output/'geometry/scene.json'
    receipt, process, inherited, scene = map(read, (receipt_path, process_path, source_path, scene_path))
    expected = sha(receipt_path)
    require(process['reportSha256'] == expected, 'Photoreal report no longer matches its native process pin')
    inherited_pins = [h for p, h in inherited['receiptPins'].items() if Path(p).name == receipt_path.name]
    require(inherited['status'] == 'verified-scene-inherited' and inherited_pins == [expected],
            'Photoreal report is not pinned by exact scene inheritance')
    require(receipt['interior']['sourceManifestSha256'] == sha(scene_path), 'Cloth source scene changed')
    targets = select_targets(scene, receipt)
    source_file = ROOT/'lib/babylon-scene.ts'
    source_text = source_file.read_text()
    require('material.albedoColor = Color3.FromHexString(color);' in source_text,
            'Source generic swatch transfer changed; re-audit cloth')
    for name, swatch in SOURCES.items():
        require(re.search(r'pbrMaterial\(\s*this\.scene,\s*"'+re.escape(name)+r'",\s*"'+re.escape(swatch)+r'"', source_text),
                'Exact cloth constructor swatch no longer present: ' + name)
    files = {str(p.resolve()): sha(p) for p in (receipt_path, process_path, source_path, scene_path, source_file)}
    for asset, target in targets.items():
        relative = asset.split('.')[0].removeprefix('/Game/') + '.uasset'
        suffix = '/Content/' + relative
        pins = [value for path, value in receipt['finalAssetHashes'].items() if path.endswith(suffix)]
        actual = output/'Project/BreziTwin/Content'/relative
        require(len(pins) == 1 and actual.is_file() and sha(actual) == pins[0],
                'Accepted cloth package bytes changed: ' + asset)
        target['originalPackageSha256'] = pins[0]
        files[str(actual.resolve())] = pins[0]
    return targets, files


def actor_list(actors):
    return actors.get_all_level_actors() if hasattr(actors, 'get_all_level_actors') else list(actors)


def validate_attribute_inputs(rows):
    """Require two distinct active color inputs and a preserved Cloth mask."""
    result = {}
    for row in rows:
        key = normalize(row['pin'])
        require(key not in result, 'Ambiguous material attribute pin: ' + key)
        result[key] = row
    require(COLOR_PINS | {'clearcoat', 'normal', 'roughness', 'ambientocclusion'} <= set(result),
            'Cloth attribute graph lacks reviewed inputs')
    require(all(result[k]['node'] for k in COLOR_PINS | {'clearcoat', 'normal', 'roughness', 'ambientocclusion'}),
            'Cloth color, weave or mask attribute is disconnected')
    return result


def attributes(u, material):
    lib = u.MaterialEditingLibrary
    require(material.get_editor_property('use_material_attributes')
            and material.get_editor_property('shading_model') == u.MaterialShadingModel.MSM_CLOTH,
            'Expected active cloth MaterialAttributes shader')
    node = lib.get_material_property_input_node(material, u.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
    require(isinstance(node, u.MaterialExpressionMakeMaterialAttributes), 'Cloth uses an unreviewed attribute graph')
    pins = list(lib.get_material_expression_input_names(node))
    sources = list(lib.get_inputs_for_material_expression(material, node))
    require(len(pins) == len(sources), 'Cloth attribute input readback differs')
    rows, objects = [], {}
    for pin, source in zip(pins, sources):
        channel = str(lib.get_input_node_output_name_for_material_expression(node, source)) if source else ''
        if channel == 'None':
            channel = ''
        row = {'pin': str(pin), 'node': source.get_name() if source else None,
               'role': str(source.get_editor_property('desc')) if source else None, 'channel': channel}
        rows.append(row)
        if source:
            objects[normalize(pin)] = source
    return node, validate_attribute_inputs(rows), objects


def graph_snapshot(u, material):
    graph = module('fabric_graph_helper', 'photoreal-exterior.py').graph_snapshot(u, material)
    root, rows, _ = attributes(u, material)
    return {**graph, 'useMaterialAttributes': bool(material.get_editor_property('use_material_attributes')),
            'attributeRoot': root.get_name(), 'attributes': rows}


def protected_graph(graph):
    """Remove only declared new nodes/two color edges from a full graph witness."""
    result = copy.deepcopy(graph)
    result['nodes'] = [n for n in result['nodes'] if not n['role'].startswith(TAG)]
    for node in result['nodes']:
        if node['class'] == 'MaterialExpressionMakeMaterialAttributes':
            for entry in node['inputs']:
                if normalize(entry[0]) in COLOR_PINS:
                    entry[1:] = ['ALLOWED_COLOR_CORRECTION', '']
    for prop in ('BASE_COLOR', 'SUBSURFACE_COLOR'):
        if prop in result['roots']:
            result['roots'][prop] = 'ALLOWED_COLOR_CORRECTION'
    for key in COLOR_PINS:
        result['attributes'][key] = {'pin': result['attributes'][key]['pin'], 'colorCorrectionAllowed': True}
    return result


def create_material(u, original, spec):
    lib, assets = u.MaterialEditingLibrary, u.EditorAssetLibrary
    path = PREFIX + '/M_Cloth_' + digest({'original': original.get_path_name(), 'recipe': spec})[:16]
    require(not assets.does_asset_exist(path), 'Fabric stage requires a fresh output namespace: ' + path)
    material = assets.duplicate_asset(original.get_path_name(), path)
    require(material is not None, 'Cannot clone accepted cloth')
    before = graph_snapshot(u, material)
    root, pins, sources = attributes(u, material)
    ratio = lib.create_material_expression(material, u.MaterialExpressionConstant3Vector, -900, 0)
    require(ratio is not None, 'Cannot create cloth transfer constant')
    ratio.set_editor_property('desc', TAG+'srgb-to-linear-ratio')
    ratio.set_editor_property('constant', u.LinearColor(*spec['correctionRatio'], 1))
    for key, prop in (('basecolor', 'BASE_COLOR'), ('subsurfacecolor', 'SUBSURFACE_COLOR')):
        multiplier = lib.create_material_expression(material, u.MaterialExpressionMultiply, -600, 0)
        require(multiplier is not None, 'Cannot create cloth color transfer')
        multiplier.set_editor_property('desc', TAG+'corrected-'+key)
        require(lib.connect_material_expressions(sources[key], pins[key]['channel'], multiplier, 'A')
                and lib.connect_material_expressions(ratio, '', multiplier, 'B')
                and lib.connect_material_expressions(multiplier, '', root, pins[key]['pin'])
                and lib.connect_material_property(multiplier, '', getattr(u.MaterialProperty, 'MP_'+prop)),
                'Cloth color attribute reconnection failed')
    require(protected_graph(graph_snapshot(u, material)) == protected_graph(before),
            'Cloth correction changed another node, attribute, mask or shader flag')
    require(not list(lib.recompile_material(material)), 'Corrected cloth native compilation failed')
    assets.set_metadata_tag(material, 'BreziGeneratedBy', OWNER)
    assets.set_metadata_tag(material, 'BreziRealismFabricRecipe', json.dumps(spec, sort_keys=True))
    assets.set_metadata_tag(material, 'source_material_name', spec['sourceName'])
    require(assets.save_loaded_asset(material, only_if_is_dirty=False), 'Cannot save corrected cloth')
    return material, protected_graph(before)


def apply(u, actors, output):
    targets, input_files = load_inputs(output)
    interior = module('fabric_accepted_graph', 'photoreal-interior.py')
    planned, originals, counts = [], {}, {name: 0 for name in SOURCES}
    for actor in actor_list(actors):
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            for slot in range(component.get_num_materials()):
                material = component.get_material(slot)
                if not material or material.get_path_name() not in targets:
                    continue
                path = material.get_path_name()
                target = targets[path]
                if path not in originals:
                    require(u.EditorAssetLibrary.get_metadata_tag(material, 'BreziGeneratedBy') == SOURCE_OWNER
                            and u.EditorAssetLibrary.get_metadata_tag(material, 'BreziPhotorealInteriorRecipe') == json.dumps(target['accepted']['recipe'], sort_keys=True)
                            and interior.snapshot(u, material) == target['accepted']['graph'],
                            'Cloth no longer matches its hash-pinned accepted graph: ' + path)
                    originals[path] = graph_snapshot(u, material)
                planned.append((actor, component, slot, material, target))
                counts[target['sourceName']] += 1
    require(all(counts.values()), 'One or both accepted cloth targets have no native binding')
    report = {'schemaVersion': 1, 'status': 'authored-reload-pending', 'owner': OWNER,
              'pipelineFiles': {str(ROOT/'scripts/unreal'/name): sha(ROOT/'scripts/unreal'/name)
                                for name in ('realism-fabric.py', 'photoreal-interior.py', 'archviz-materials.py', 'photoreal-exterior.py')},
              'inputFiles': input_files, 'bindingChanges': [], 'ownedAssets': [], 'materials': {},
              'originalGraphs': originals, 'counts': counts, 'geometryModified': False,
              'collisionModified': False, 'nativeRenderedVerified': False,
              'limitations': ['Patio fabric geometry remains the accepted authored model, not a furniture scan.',
                             'Only two provenance-verified swatches change; existing weave, fuzz ratio, AO, roughness, normal and Cloth mask are retained.',
                             'Saved graph verification is separate from native rendered acceptance.']}
    created = {}
    for actor, component, slot, original, target in planned:
        source_path = original.get_path_name()
        if source_path not in created:
            material, protected = create_material(u, original, target['recipe'])
            created[source_path] = material
            path = material.get_path_name()
            report['ownedAssets'].append(path)
            report['materials'][path] = {'recipe': target['recipe'], 'sourceAsset': source_path,
                                         'originalPackageSha256': target['originalPackageSha256'],
                                         'protectedGraph': protected, 'graph': graph_snapshot(u, material)}
        material = created[source_path]
        component.set_material(slot, material)
        report['bindingChanges'].append({'actor': actor.get_path_name(), 'component': component.get_path_name(), 'slot': slot,
                                         'before': source_path, 'after': material.get_path_name(), 'sourceName': target['sourceName']})
    require(all(graph_snapshot(u, u.EditorAssetLibrary.load_asset(path)) == graph for path, graph in originals.items()),
            'An accepted original cloth graph changed')
    return report


def verify(u, actors, report):
    components = {c.get_path_name(): c for a in actor_list(actors) for c in a.get_components_by_class(u.StaticMeshComponent)}
    for row in report['bindingChanges']:
        component = components.get(row['component'])
        require(component and component.get_material(row['slot'])
                and component.get_material(row['slot']).get_path_name() == row['after'],
                'Saved cloth binding differs: ' + row['component'])
    for path, entry in report['materials'].items():
        material = u.EditorAssetLibrary.load_asset(path)
        require(material and u.EditorAssetLibrary.get_metadata_tag(material, 'BreziGeneratedBy') == OWNER
                and u.EditorAssetLibrary.get_metadata_tag(material, 'BreziRealismFabricRecipe') == json.dumps(entry['recipe'], sort_keys=True),
                'Saved cloth ownership or recipe differs')
        graph = graph_snapshot(u, material)
        require(graph == entry['graph'] and protected_graph(graph) == entry['protectedGraph'],
                'Saved cloth changed another attribute or graph node')
    for path, graph in report['originalGraphs'].items():
        require(graph_snapshot(u, u.EditorAssetLibrary.load_asset(path)) == graph,
                'Original cloth graph changed on saved reload')
    return {**report, 'status': 'saved-reloaded-validated', 'savedReloaded': True}
