"""Owned stove visuals and animated fire over an immutable inherited scene.

Seven original visuals are suppressed; their mesh/collision/transforms remain.
All source materials, lights, glass, furniture and moving doors are protected.
"""
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/unreal'))
OWNER = 'scripts/unreal/realism-stove-import.py'
PREFIX = '/Game/Brezi/Realism/Stove'
TAG = 'BreziRealismStove20260926'
MAP = '/Game/Brezi/Maps/Brezi'
MAP_FILE = 'Brezi/Maps/Brezi.umap'
SOURCE_IDS = [f'DOM_{i:05d}' for i in (553,556,562,563,564,565,566)]
ROLE_SOURCES = {'shell': ['DOM_00553'], 'chamber': ['DOM_00553'], 'logs': ['DOM_00562','DOM_00563'],
                'flames': ['DOM_00564','DOM_00565','DOM_00566'], 'embers': ['DOM_00556']}
MESH_IDS = sorted('RFIRE_' + role.upper() for role in ROLE_SOURCES)
PROBE = ROOT / 'output/unreal/realism-fire-texture-probe-20260926-r1'


def _helper():
    spec = importlib.util.spec_from_file_location('frozen_room_detail_helpers', ROOT / 'scripts/unreal/realism-room-details-import.py')
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


helper = _helper()
require, sha, read, write, now, digest, module, inventory = (getattr(helper, name) for name in
    ('require', 'sha', 'read', 'write', 'now', 'digest', 'module', 'inventory'))
RENDER_FLAGS = helper.RENDER_FLAGS
witness = helper.witness
capture_bounds = helper.capture_bounds
verify_geometry = helper.helper.verify_geometry


def validate_changes(before, after, content):
    content = Path(content).resolve()
    require(before.keys() <= after.keys(), 'Removed original Content file')
    for path, value in before.items():
        require(path == str(content / MAP_FILE) or after[path] == value, 'Protected source asset changed: ' + path)
    for path in after.keys() - before.keys():
        require(any(Path(path).resolve().is_relative_to(content / 'Brezi/Realism' / part) for part in ('Stove',)),
                'New asset outside stove namespace')
        require(Path(path).suffix in ('.uasset', '.uexp', '.ubulk'), 'Unexpected stove Content file')


def validate_manifest(manifest, scene):
    require(manifest['owner'] == 'scripts/unreal/realism-stove-geometry.py', 'Unknown stove generator')
    require(manifest['status'] == 'offline-study-geometry-validated', 'Offline stove geometry unverified')
    require(scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'Only C/B/B supported')
    require(sorted(manifest['sourceIds']) == SOURCE_IDS and sorted(manifest['hiddenSourceIds']) == SOURCE_IDS, 'Stove source scope differs')
    require(sorted(row['id'] for row in manifest['objects']) == MESH_IDS, 'Stove mesh identities differ')
    records = {row['id']: row for row in scene['objects']}
    for id_ in SOURCE_IDS:
        require(manifest['sourceRecords'][id_] == records[id_], 'Stove source record drift: ' + id_)
        require(records[id_]['enabled'] and records[id_]['instances'] == 1 and not records[id_]['metadata'].get('doorMotion'), 'Stove source no longer static')
        require(records[id_]['name'].startswith('FIREPLACE-STOVE-B-2026-09-11 · '), 'Stove source semantics changed')
    preserved = [f'DOM_{i:05d}' for i in range(553,572) if f'DOM_{i:05d}' not in SOURCE_IDS]
    require(manifest['preservedSourceIds'] == preserved and 'DOM_00557' in preserved, 'Stove glass/trim preservation differs')
    require(manifest['sourceBodyCollisionPreserved'] and manifest['originalLightingUnchanged'], 'Unreviewed stove collision/lighting scope')
    for row in manifest['objects']:
        role = row['materialRole']
        require(row['id'] == 'RFIRE_' + role.upper() and row['role'] == role and row['sourceIds'] == ROLE_SOURCES[role], 'Stove role mapping differs')
        bounds = row['visualBoundsMm']
        expected = {'min': [bounds['min'][0]/10, -bounds['max'][1]/10, bounds['min'][2]/10],
                    'max': [bounds['max'][0]/10, -bounds['min'][1]/10, bounds['max'][2]/10]}
        require(all(math.isfinite(v) for pair in expected.values() for v in pair), 'Invalid stove bounds')
        require(max(abs(expected[k][i] - row['expectedWorldBoundsCm'][k][i]) for k in ('min', 'max') for i in range(3)) < 1e-5,
                'Stove coordinate conversion differs')


def expected_witness(original, changes):
    result = copy.deepcopy(original)
    require(sorted(row['sourceId'] for row in changes) == SOURCE_IDS, 'Unreported stove visibility scope')
    components = set()
    for change in changes:
        require(change['component'] not in components, 'Duplicate stove source component')
        components.add(change['component'])
        require(change['actor'] in result, 'Stove source actor missing')
        found = [c for c in result[change['actor']]['components'] if c['path'] == change['component']]
        require(len(found) == 1 and 'mesh' in found[0], 'Stove source component missing')
        c = found[0]
        require(c['visible'] and not c['hiddenInGame'], 'Stove original was already hidden')
        require(change['before'] == {key: c[key] for key in ('visible', 'hiddenInGame', 'renderFlags')}, 'Stove visibility baseline differs')
        c.update(visible=False, hiddenInGame=True, renderFlags={name: False for name in RENDER_FLAGS})
        require(change['after'] == {key: c[key] for key in ('visible', 'hiddenInGame', 'renderFlags')}, 'Stove visibility delta differs')
    return result


def verify_witness(expected, actual, added):
    require(len(set(added)) == len(added) and not set(expected) & set(added), 'Stove actor identities overlap')
    require(set(actual) == set(expected) | set(added), 'Unreported stove actor addition/removal')
    for path, row in expected.items():
        require(actual[path] == row, 'Original geometry/transform/material/collision changed: ' + path)
    for path in added:
        row = actual[path]
        require(TAG in row['tags'] and not any(t.startswith(('DOM_', 'BreziDoor')) for t in row['tags']), 'Unowned stove actor')
        for c in row['components']:
            if 'collision' in c:
                require('NO_COLLISION' in c['collision'] and not c['navigation'], 'Stove gained collision/navigation')


def apply_geometry(u, actors, levels, manifest, artifact, materials):
    sources = {}
    for actor in actors.get_all_level_actors():
        require(not actor.actor_has_tag(TAG), 'Stove already authored')
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh')
            id_ = str(u.EditorAssetLibrary.get_metadata_tag(mesh, 'source_object_id')) if mesh else ''
            if id_ not in SOURCE_IDS:
                continue
            require(id_ not in sources, 'Duplicate stove source component')
            require(c.get_editor_property('mobility') == u.ComponentMobility.STATIC and c.is_visible()
                    and not c.get_editor_property('hidden_in_game'), 'Stove source must be visible and static')
            sources[id_] = (actor, c)
    require(sorted(sources) == SOURCE_IDS, 'Native stove sources missing')
    pipelines = []
    for source, name in [('GLTFSceneAssets', 'Assets'), ('GLTFMaterials', 'Materials'), ('LevelActors', 'Level')]:
        p = u.EditorAssetLibrary.duplicate_asset('/Game/Brezi/Pipeline/' + source, PREFIX + '/Pipeline/' + name)
        require(p is not None, 'Cannot duplicate stove import pipeline')
        pipelines.append(p)
    mesh_pipeline = pipelines[0].get_editor_property('mesh_pipeline')
    for name, value in [('combine_static_meshes_behavior', u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE),
                        ('collision', False), ('build_nanite', False), ('generate_lightmap_u_vs', False)]:
        mesh_pipeline.set_editor_property(name, value)
    pipelines[2].set_editor_property('scene_hierarchy_type', u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
    params = u.ImportAssetParameters()
    for name, value in [('is_automated', True), ('replace_existing', False), ('force_show_dialog', False),
                        ('override_pipelines', [u.SoftObjectPath(p.get_path_name()) for p in pipelines]), ('import_level', levels.get_current_level())]:
        params.set_editor_property(name, value)
    before = {a.get_path_name() for a in actors.get_all_level_actors()}
    manager = u.InterchangeManager.get_interchange_manager_scripted()
    require(manager.import_scene(PREFIX + '/Geometry', manager.create_source_data(str(artifact / 'realism-stove-study.glb')), params), 'Stove GLB import failed')
    selected = {row['id']: row for row in manifest['objects']}
    imported, added = {}, []
    for actor in actors.get_all_level_actors():
        if actor.get_path_name() in before:
            continue
        added.append(actor.get_path_name())
        actor.set_editor_property('tags', [*actor.tags, u.Name(TAG)])
        actor.set_folder_path('Brezi/Realism/Stove')
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh')
            require(mesh is not None, 'Stove imported without a mesh')
            names = set(re.findall(r'RFIRE_(?:SHELL|CHAMBER|LOGS|FLAMES|EMBERS)', actor.get_actor_label() + ' ' + mesh.get_name()))
            require(len(names) == 1, 'Ambiguous imported stove identity')
            id_ = names.pop()
            require(id_ not in imported and id_ in selected, 'Duplicate/unknown imported stove')
            record = selected[id_]
            require(c.get_num_materials() == 1, 'Imported stove material slot count differs')
            material = u.EditorAssetLibrary.load_asset(materials[record['materialRole']])
            require(material is not None, 'Stove role material missing')
            c.set_material(0, material)
            c.set_mobility(u.ComponentMobility.STATIC)
            c.set_collision_profile_name('NoCollision')
            c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            c.set_editor_property('can_ever_affect_navigation', False)
            c.set_editor_property('generate_overlap_events', False)
            c.set_editor_property('cast_shadow', record['materialRole'] != 'flames')
            if record['materialRole'] == 'flames':
                for flag in RENDER_FLAGS:
                    c.set_editor_property(flag, False)
            actor.set_actor_label(id_)
            u.EditorAssetLibrary.set_metadata_tag(mesh, 'BreziGeneratedBy', OWNER)
            u.EditorAssetLibrary.set_metadata_tag(mesh, 'BreziStoveSourceIds', json.dumps(record['sourceIds']))
            require(u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False), 'Cannot save stove mesh')
            imported[id_] = {'actor': actor.get_path_name(), 'component': c.get_path_name(), 'mesh': mesh.get_path_name(),
                             'sourceIds': record['sourceIds'], 'materialRole': record['materialRole'], 'materials': [c.get_material(i).get_path_name() for i in range(c.get_num_materials())]}
    require(set(imported) == set(selected), 'Stove imported membership differs')
    changes = []
    for id_, (actor, c) in sorted(sources.items()):
        previous = {'visible': bool(c.get_editor_property('visible')), 'hiddenInGame': bool(c.get_editor_property('hidden_in_game')),
                    'renderFlags': {name: bool(c.get_editor_property(name)) for name in RENDER_FLAGS}}
        c.set_visibility(False, False)
        c.set_hidden_in_game(True, False)
        for name in RENDER_FLAGS:
            c.set_editor_property(name, False)
        changes.append({'sourceId': id_, 'actor': actor.get_path_name(), 'component': c.get_path_name(), 'before': previous,
                        'after': {'visible': False, 'hiddenInGame': True, 'renderFlags': {name: False for name in RENDER_FLAGS}}})
    for p in pipelines:
        require(u.EditorAssetLibrary.save_loaded_asset(p, only_if_is_dirty=False), 'Cannot save stove pipeline')
    # Raw Epic texture packages are read-only copies, including during an engine
    # version PostLoad upgrade. Never recursively save their parent namespace.
    for folder in ('Geometry', 'Pipeline'):
        require(u.EditorAssetLibrary.save_directory(PREFIX + '/' + folder, only_if_is_dirty=True, recursive=True), 'Cannot save stove generated assets')
    return {'objects': imported, 'sourceRenderChanges': changes, 'addedActors': added}


def restore(output):
    output = Path(output).resolve()
    report = read(output / 'realism-stove-report.json')
    require(report['status'] == 'failed', 'No failed stove attempt')
    base = module('fixture_restore_paths', 'performance-optimize.py')
    source, output = base.checked_paths(report['sourceOutput'], output)
    require(report['output'] == str(output), 'Failed stove report belongs elsewhere')
    try:
        os.kill(report['nativeProcessId'], 0)
    except ProcessLookupError:
        pass
    else:
        raise RuntimeError('Native stove process is still running')
    content = output / 'Project/BreziTwin/Content'
    current = inventory(content)
    require(current == report['failedContentHashes'], 'Stove Content drift after failure')
    before = report['beforeAssetHashes']
    validate_changes(before, current, content)
    backup = output / 'realism-stove-checkpoint/Brezi.umap'
    require(sha(backup) == before[str(content / MAP_FILE)], 'Stove map backup drift')
    require(read(output / 'performance-source.json')['content'] == before, 'Inherited stove source drift')
    donor = source / 'Project/BreziTwin/Content'
    require(inventory(donor) == {str(donor / Path(p).relative_to(content)): value for p, value in before.items()}, 'Stove donor changed')
    history = output / 'realism-stove-history' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    history.mkdir(parents=True)
    shutil.copy2(content / MAP_FILE, history / 'failed-Brezi.umap')
    shutil.copy2(backup, content / MAP_FILE)
    for path in current.keys() - before.keys():
        target = history / 'failed-assets' / Path(path).relative_to(content)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(path, str(target))
    require(inventory(content) == before, 'Stove restoration not exact')
    for name in ['realism-stove-report.json', 'realism-stove-process.json', 'realism-stove.log', 'realism-stove.log.json', 'realism-stove-checkpoint']:
        path = output / name
        if path.exists():
            shutil.move(str(path), str(history / name))
    write(history / 'restoration.json', {'status': 'stove-failure-restored', 'generatedAt': now(), 'contentHashes': before})
    print(json.dumps({'status': 'stove-failure-restored', 'history': str(history)}))


def log_prefix_proof(path, original_hash):
    """Keep original process evidence when a child daemon appends after exit."""
    data = Path(path).read_bytes()
    digest_ = hashlib.sha256()
    for index, byte in enumerate(data):
        digest_.update(bytes([byte]))
        if digest_.hexdigest() == original_hash:
            tail = data[index+1:]
            # Independently inspected append from this probe's UnrealTrace daemon:
            # optional settings absent, no sponsors, clean SIGTERM shutdown.
            require(not tail or (len(tail) == 855 and hashlib.sha256(tail).hexdigest()
                    == 'a7258fe74f1f9b9d957da648c51d760a24da175914af4104595a01402f602fcb'),
                    'Unexpected native probe log suffix; preserve evidence and investigate')
            return {'path': str(path), 'originalSha256': original_hash, 'originalBytes': index + 1,
                    'completeSha256': hashlib.sha256(data).hexdigest(), 'appendedBytes': len(data)-index-1,
                    'appendedSha256': hashlib.sha256(tail).hexdigest(),
                    'appendClassification': 'reviewed-benign-UnrealTrace-shutdown' if tail else 'none'}
    raise RuntimeError('Original native probe log is not an intact prefix')


def probe_inputs():
    probe = module('frozen_fire_probe', 'realism-fire-texture-probe.py')
    prepared, verified, report, process = [read(PROBE / name) for name in
        ('prepared.json', 'verified.json', 'native-report.json', 'native-process.json')]
    require(verified['status'] == 'native-texture-probe-verified' and report['status'] == 'native-full-textures-exported', 'Native fire texture proof absent')
    for key, name in [('reportSha256', 'native-report.json'), ('processSha256', 'native-process.json'), ('preparedSha256', 'prepared.json')]:
        require(verified[key] == sha(PROBE / name), 'Native texture probe receipt drift')
    require(process['returncode'] == 0 and process['pid'] == report['nativeProcessId'], 'Fire probe process differs')
    log_proof = log_prefix_proof(PROBE / 'native.log', process['logSha256'])
    require(process['preparedSha256'] == report['preparedSha256'] == sha(PROBE / 'prepared.json'), 'Fire probe inputs differ')
    require(process['startedAt'] <= report['startedAt'] <= report['generatedAt'] <= process['endedAt'], 'Fire probe lifetime differs')
    require(report['originalAndCopiedAssetsUnchanged'] and not report['experimentalRuntimePluginsEnabled'], 'Unverified probe isolation')
    require(not any(name.startswith('NetworkPrediction') for name in report['enabledPlugins']), 'Sample runtime plugin enabled in probe')
    require(set(report['textures']) == set(probe.TEXTURES), 'Fire probe texture scope differs')
    probe.check_pins(prepared)
    pins = dict(prepared['inputPins'])
    pins.update({str(PROBE / name): sha(PROBE / name) for name in ('prepared.json', 'verified.json', 'native-report.json', 'native-process.json', 'native.log')})
    for name, row in report['textures'].items():
        require(row['dependencies'] == [] and row['nativeSize'] == probe.TEXTURES[name]['size'], 'Unexpected fire texture dependencies/dimensions')
        require(row['sha256'] == probe.TEXTURES[name]['sha256'] == sha(row['installedSource']), 'Installed fire texture drift')
        require(probe.png_info(row['export']['path']) == {k: v for k, v in row['export'].items() if k != 'path'}, 'Full fire texture export drift')
        pins[row['export']['path']] = row['export']['sha256']
    return report['textures'], pins, log_proof


def texture_readback(u, textures):
    require(not any(str(name).startswith('NetworkPrediction') for name in u.PluginBlueprintLibrary.get_enabled_plugin_names()), 'Sample runtime plugin enabled')
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.scan_paths_synchronous([PREFIX + '/Fire/Textures'], True)
    options = u.AssetRegistryDependencyOptions()
    for field in ('include_soft_package_references', 'include_hard_package_references', 'include_game_package_references', 'include_editor_only_package_references'):
        options.set_editor_property(field, True)
    for field in ('include_searchable_names', 'include_soft_management_references', 'include_hard_management_references'):
        options.set_editor_property(field, False)
    result = {}
    for name, row in textures.items():
        package = PREFIX + '/Fire/Textures/' + name
        texture = u.EditorAssetLibrary.load_asset(package)
        require(texture and texture.get_class().get_name() == 'Texture2D' and texture.get_path_name() == package + '.' + name, 'Owned fire texture failed to load')
        dependencies = sorted(str(p) for p in registry.get_dependencies(u.Name(package), options))
        require(dependencies == [], 'Owned fire texture has unexpected dependency')
        size = [int(texture.blueprint_get_size_x()), int(texture.blueprint_get_size_y())]
        require(size == row['nativeSize'], 'Owned fire texture resolution differs')
        properties = {}
        for field, expected in row['properties'].items():
            value = texture.get_editor_property(field)
            properties[field] = value if isinstance(value, (str, int, float, bool)) else str(value)
            require(properties[field] == expected, 'Owned fire texture property differs: ' + field)
        require(sha(row['copiedFile']) == row['sha256'] == sha(row['installedSource']), 'Owned or installed texture bytes changed')
        result[name] = {'asset': texture.get_path_name(), 'dependencies': dependencies, 'nativeSize': size, 'properties': properties, 'sha256': row['sha256']}
    return result


def copy_textures(u, project, originals):
    folder = project / 'Content/Brezi/Realism/Stove/Fire/Textures'
    folder.mkdir(parents=True, exist_ok=True)
    require(not any(folder.iterdir()), 'Owned fire texture folder is not empty')
    result = copy.deepcopy(originals)
    for name, row in result.items():
        destination = folder / (name + '.uasset')
        shutil.copy2(row['installedSource'], destination)
        row['copiedFile'] = str(destination)
        row['ownedPackage'] = PREFIX + '/Fire/Textures/' + name
    return result, texture_readback(u, result)


def main():
    import unreal as u
    base = module('stove_geometry_witness', 'performance-optimize.py')
    require(all(os.environ.get(k) for k in ('BREZI_MODEL_OUTPUT', 'BREZI_PERFORMANCE_SOURCE', 'BREZI_STOVE_OUTPUT')), 'Explicit inherited project and stove artifact required')
    source, output = base.checked_paths(ROOT / os.environ['BREZI_PERFORMANCE_SOURCE'], ROOT / os.environ['BREZI_MODEL_OUTPUT'])
    artifact = (ROOT / os.environ['BREZI_STOVE_OUTPUT']).resolve()
    require(artifact.is_relative_to(ROOT / 'output/unreal') and not artifact.is_relative_to(output), 'Stove artifact must be separate from target project')
    project = output / 'Project/BreziTwin'
    require(Path(u.Paths.project_dir()).resolve() == project, 'Wrong native stove project')
    content = project / 'Content'
    before = inventory(content)
    provenance = read(output / 'performance-source.json')
    require(provenance['status'] == 'verified-scene-inherited' and provenance['donor'] == str(source) and provenance['content'] == before, 'Unverified stove inheritance')
    require(not any((output / name).exists() for name in ('realism-stove-report.json', 'realism-furniture-report.json', 'realism-room-details-report.json', 'realism-fixtures-report.json', 'realism-import-report.json', 'performance-scene-report.json', 'nanite-study-report.json')), 'Stove pass requires a fresh inherited output')
    donor = source / 'Project/BreziTwin/Content'
    source_before = inventory(donor)
    require({str(content / Path(p).relative_to(donor)): value for p, value in source_before.items()} == before, 'Stove donor Content differs')
    manifest = read(artifact / 'geometry-report.json')
    geometry = output / 'geometry'
    scene = read(geometry / 'scene.json')
    validate_manifest(manifest, scene)
    require(manifest['sourceSceneSha256'] == sha(geometry / 'scene.json') and manifest['sourceObjSha256'] == sha(geometry / 'dom-mm.obj')
            and manifest['glbSha256'] == sha(artifact / 'realism-stove-study.glb'), 'Stove geometry input pins differ')
    require(manifest['generatorSha256'] == sha(ROOT / 'scripts/unreal/realism-stove-geometry.py'), 'Stove generator changed after export')
    require(manifest['generatorDependencies'] == {'scripts/unreal/stove-visuals/generate.py': sha(ROOT / 'scripts/unreal/stove-visuals/generate.py')}, 'Unexpected stove geometry dependency')
    originals, probe_pins, probe_log_proof = probe_inputs()
    pipeline = {str(ROOT / 'scripts/unreal' / name): sha(ROOT / 'scripts/unreal' / name) for name in
        ('realism-stove-import.py', 'realism-stove-geometry.py', 'realism-stove-materials.py', 'realism-fire-texture-probe.py',
         'realism-room-details-import.py', 'realism-fixtures-import.py', 'performance-optimize.py', 'performance_scene_policy.py', 'stove-visuals/generate.py')}
    inputs = {str(p): sha(p) for p in [*sorted(geometry.rglob('*')), artifact / 'geometry-report.json', artifact / 'realism-stove-study.glb'] if p.is_file()}
    inputs.update(probe_pins)
    engine = Path(read(PROBE / 'prepared.json')['engine'])
    uv_files = [engine / ('Engine/Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/' + name)
                for name in ('GLTF/GLTFMesh.cpp', 'GLTF/GLTFAccessor.cpp', 'GLTFMeshFactory.cpp')]
    inputs.update({str(path): sha(path) for path in uv_files})
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'pending', 'startedAt': now(), 'project': str(project),
              'output': str(output), 'sourceOutput': str(source), 'nativeProcessId': os.getpid(), 'artifact': str(artifact),
              'manifestSha256': sha(artifact / 'geometry-report.json'), 'sourceIds': SOURCE_IDS, 'hiddenSourceIds': SOURCE_IDS,
              'beforeAssetHashes': before, 'inputFiles': inputs, 'pipelineFiles': pipeline, 'probeLogProof': probe_log_proof,
              'uvConventionEvidence': {'sourceFiles': [str(path) for path in uv_files], 'mapping': 'glTF TEXCOORD_0 copied unchanged; V=0 card bottom, V=1 top'},
              'renderedVerified': False}
    folder = output / 'realism-stove-checkpoint'
    folder.mkdir(exist_ok=False)
    shutil.copy2(content / MAP_FILE, folder / 'Brezi.umap')
    write(output / 'realism-stove-report.json', report)
    try:
        actors = u.get_editor_subsystem(u.EditorActorSubsystem)
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(levels.load_level(MAP), 'Cannot load stove baseline map')
        original = witness(base, u, actors)
        report['textures'], report['authoredTextureReadback'] = copy_textures(u, project, originals)
        materials = module('brezi_realism_stove_materials', 'realism-stove-materials.py')
        report['materials'] = materials.apply(u, actors, output)
        require(report['materials'].get('bindingChanges', []) == [], 'Stove helper may not change original material bindings')
        require(set(report['materials']['materials']) == set(ROLE_SOURCES), 'Stove material roles differ')
        changes = apply_geometry(u, actors, levels, manifest, artifact, report['materials']['materials'])
        report.update(changes)
        expected = expected_witness(original, changes['sourceRenderChanges'])
        authored = witness(base, u, actors)
        verify_witness(expected, authored, changes['addedActors'])
        verify_geometry(u, actors, manifest, changes)
        require(levels.save_current_level(), 'Cannot save stove map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False), 'Cannot unload stove map')
        require(levels.load_level(MAP), 'Cannot reload stove map')
        reloaded = witness(base, u, actors)
        verify_witness(expected, reloaded, changes['addedActors'])
        require(authored == reloaded, 'Saved stove actor witness differs')
        readback = verify_geometry(u, actors, manifest, changes)
        report['savedMaterialReadback'] = materials.verify(u, actors, report['materials'])
        report['savedTextureReadback'] = texture_readback(u, report['textures'])
        require(report['savedTextureReadback'] == report['authoredTextureReadback'], 'Saved fire texture state differs')
        for field in ('pipelineFiles', 'inputFiles'):
            for path, value in report['materials'].get(field, {}).items():
                absolute = str((ROOT / path).resolve())
                require(sha(absolute) == value, 'Stove material input changed: ' + absolute)
                require(absolute not in report[field] or report[field][absolute] == value, 'Conflicting stove input pin')
                report[field][absolute] = value
        after = inventory(content)
        validate_changes(before, after, content)
        require(source_before == inventory(donor), 'Historical stove donor Content changed')
        for path, value in {**report['pipelineFiles'], **report['inputFiles']}.items():
            require(sha(path) == value, 'Stove authoring input changed during native import')
        report.update(status='realism-stove-validated', savedReloaded=True, protectedContentUnchanged=True,
                      sourceGeometryCollisionAndTransformsPreserved=True, originalMaterialAssetsPreserved=True, originalLightingPreserved=True,
                      materialBindingsAudited=True, experimentalRuntimePluginsEnabled=False,
                      originalActorCount=len(original), finalActorCount=len(reloaded),
                      protectedActorWitnessSha256=digest(expected), savedProtectedActorWitnessSha256=digest({p: reloaded[p] for p in expected}),
                      authoredActorWitnessSha256=digest(authored), savedActorWitnessSha256=digest(reloaded),
                      savedGeometryReadback=readback, maxNativeBoundsErrorCm=max(row['maxErrorCm'] for row in readback),
                      afterAssetHashes=after, newAssets=sorted(after.keys() - before.keys()),
                      changedAssets=[{'path': p, 'beforeSha256': before[p], 'afterSha256': after[p]} for p in before if before[p] != after[p]])
        u.log('BREZI_REALISM_STOVE validated')
    except Exception as error:
        report.update(status='failed', error=str(error), failedContentHashes=inventory(content))
        raise
    finally:
        report['generatedAt'] = now()
        write(output / 'realism-stove-report.json', report)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--restore':
        restore(sys.argv[2])
    else:
        main()
