"""Visual-only sink/faucet overlay on a fresh inherited realism project.

Only eight identified source components stop rendering. Their source assets,
transforms, material bindings and collision remain byte-/value-identical.
Imported geometry lives under /Game/Brezi/Realism/Fixtures. A separate bounded
cloth material correction changes only reported slots and creates Fabric assets.
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
OWNER = 'scripts/unreal/realism-fixtures-import.py'
PREFIX = '/Game/Brezi/Realism/Fixtures'
TAG = 'BreziRealismFixtures20260926'
MAP = '/Game/Brezi/Maps/Brezi'
MAP_FILE = 'Brezi/Maps/Brezi.umap'
SOURCE_IDS = [f'DOM_{i:05d}' for i in range(759, 767)]
MESH_IDS = ['RF_SINK_BOWL', 'RF_SINK_DRAIN', 'RF_SINK_SPOUT', 'RF_SINK_LEVER']
RENDER_FLAGS = ('cast_shadow', 'cast_hidden_shadow', 'affect_distance_field_lighting',
                'affect_dynamic_indirect_lighting', 'affect_indirect_lighting_while_hidden', 'visible_in_ray_tracing')


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts/unreal' / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def inventory(content):
    result = {}
    for p in sorted(content.rglob('*')):
        require(not p.is_symlink(), 'Content symlink is not supported')
        if p.is_file():
            result[str(p.resolve())] = sha(p)
    return result


def validate_changes(before, after, content):
    content = Path(content).resolve()
    require(before.keys() <= after.keys(), 'Removed original Content file')
    for path, value in before.items():
        require(path == str(content / MAP_FILE) or after[path] == value, 'Protected source asset changed: ' + path)
    for path in after.keys() - before.keys():
        require(any(Path(path).resolve().is_relative_to(content / 'Brezi/Realism' / part) for part in ('Fixtures', 'Fabric')),
                'New asset outside fixture/fabric namespace')
        require(Path(path).suffix in ('.uasset', '.uexp', '.ubulk'), 'Unexpected fixture Content file')


def validate_manifest(manifest, scene):
    require(manifest['owner'] == 'scripts/unreal/realism-fixtures-geometry.py', 'Unknown fixture generator')
    require(manifest['status'] == 'offline-geometry-validated', 'Offline fixture geometry is unverified')
    require(scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'Only C/B/B fixtures supported')
    require(sorted(manifest['sourceIds']) == SOURCE_IDS, 'Fixture scope must contain exactly eight sink/faucet sources')
    require(sorted(row['id'] for row in manifest['objects']) == sorted(MESH_IDS), 'Fixture mesh identities differ')
    require(sorted({id_ for row in manifest['objects'] for id_ in row['sourceIds']}) == SOURCE_IDS, 'Fixture per-mesh source coverage differs')
    records = {row['id']: row for row in scene['objects']}
    for id_ in SOURCE_IDS:
        record = records[id_]
        require(record['enabled'] and record['instances'] == 1, 'Fixture source visibility/instancing differs')
        require(record['name'].startswith('KITCHEN-RUN · drez ·') if id_ <= 'DOM_00764' else record['name'].startswith('KITCHEN-RUN · batéria ·'),
                'Source ID no longer denotes the authored kitchen fixture')
        require(not any(record.get('metadata', {}).get(key) for key in ('doorMotion', 'dynamicCameraOccluder', 'walkSurface')),
                'Fixture cannot hide a door, walk surface or dynamic source')
    for row in manifest['objects']:
        require(row['sourceIds'] and len(set(row['sourceIds'])) == len(row['sourceIds']), 'Duplicate or empty per-mesh source list')
        require(row['materialBindings'], 'Missing fixture material references')
        for binding in row['materialBindings']:
            require(binding['sourceId'] in SOURCE_IDS and type(binding['sourceSlot']) is int
                    and 0 <= binding['sourceSlot'] < len(records[binding['sourceId']]['materialSlots']), 'Invalid fixture source material slot')
        bounds = row['visualBoundsMm']
        expected = {'min': [bounds['min'][0]/10, -bounds['max'][1]/10, bounds['min'][2]/10],
                    'max': [bounds['max'][0]/10, -bounds['min'][1]/10, bounds['max'][2]/10]}
        require(all(math.isfinite(v) for pair in expected.values() for v in pair), 'Invalid fixture bounds')
        require(max(abs(expected[k][i] - row['expectedWorldBoundsCm'][k][i]) for k in ('min', 'max') for i in range(3)) < 1e-5,
                'Fixture coordinate conversion differs')


def witness(base, u, actors):
    rows = base.witness(u, actors)
    for actor in actors.get_all_level_actors():
        components = {c.get_name(): c for c in actor.get_components_by_class(u.SceneComponent)}
        for row in rows[actor.get_path_name()]['components']:
            c = components[row['name']]
            row['path'] = c.get_path_name()
            if isinstance(c, u.StaticMeshComponent):
                row['renderFlags'] = {name: bool(c.get_editor_property(name)) for name in RENDER_FLAGS}
    return rows


def expected_witness(original, changes, material_changes=()):
    result = copy.deepcopy(original)
    slots = set()
    for change in material_changes:
        identity = (change['actor'], change['component'], change['slot'])
        require(identity not in slots, 'Duplicate fabric binding delta')
        slots.add(identity)
        require(change['actor'] in result, 'Fabric binding actor absent')
        found = [c for c in result[change['actor']]['components'] if c['path'] == change['component']]
        require(len(found) == 1 and 'materials' in found[0], 'Fabric binding component absent')
        c, slot = found[0], change['slot']
        require(type(slot) is int and 0 <= slot < len(c['materials']), 'Fabric slot outside original component')
        require(c['materials'][slot] == change['before'], 'Fabric binding baseline differs')
        require(change['after'].startswith('/Game/Brezi/Realism/Fabric/'), 'Fabric replacement outside owned namespace')
        c['materials'][slot] = change['after']
    require(sorted(row['sourceId'] for row in changes) == SOURCE_IDS, 'Unreported fixture visibility scope')
    components = set()
    for change in changes:
        require(change['component'] not in components, 'Duplicate fixture source component')
        components.add(change['component'])
        require(change['actor'] in result, 'Fixture source actor missing')
        found = [c for c in result[change['actor']]['components'] if c['path'] == change['component']]
        require(len(found) == 1 and 'mesh' in found[0], 'Fixture source component missing')
        c = found[0]
        require(c['visible'] and not c['hiddenInGame'], 'Fixture original was already hidden')
        require(change['before'] == {key: c[key] for key in ('visible', 'hiddenInGame', 'renderFlags')}, 'Fixture visibility baseline differs')
        c.update(visible=False, hiddenInGame=True, renderFlags={name: False for name in RENDER_FLAGS})
        require(change['after'] == {key: c[key] for key in ('visible', 'hiddenInGame', 'renderFlags')}, 'Fixture visibility delta differs')
    return result


def verify_witness(expected, actual, added):
    require(len(set(added)) == len(added) and not set(expected) & set(added), 'Fixture actor identities overlap')
    require(set(actual) == set(expected) | set(added), 'Unreported fixture actor addition/removal')
    for path, row in expected.items():
        require(actual[path] == row, 'Original geometry/transform/material/collision changed: ' + path)
    for path in added:
        row = actual[path]
        require(TAG in row['tags'] and not any(t.startswith('DOM_') for t in row['tags']), 'Unowned fixture actor')
        for c in row['components']:
            if 'collision' in c:
                require('NO_COLLISION' in c['collision'] and not c['navigation'], 'Fixture gained collision/navigation')


def capture_bounds(u, component):
    origin, extent, _ = u.SystemLibrary.get_component_bounds(component)
    lo, hi = origin - extent, origin + extent
    return {'min': [float(lo.x), float(lo.y), float(lo.z)], 'max': [float(hi.x), float(hi.y), float(hi.z)]}


def apply_geometry(u, actors, levels, manifest, artifact):
    sources = {}
    for actor in actors.get_all_level_actors():
        require(not actor.actor_has_tag(TAG), 'Fixtures already authored')
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh')
            id_ = str(u.EditorAssetLibrary.get_metadata_tag(mesh, 'source_object_id')) if mesh else ''
            if id_ not in SOURCE_IDS:
                continue
            require(id_ not in sources, 'Duplicate fixture source component')
            require(c.get_editor_property('mobility') == u.ComponentMobility.STATIC, 'Fixture source must be static')
            sources[id_] = (actor, c)
    require(sorted(sources) == SOURCE_IDS, 'Native fixture sources missing')
    pipelines = []
    for source, name in [('GLTFSceneAssets', 'Assets'), ('GLTFMaterials', 'Materials'), ('LevelActors', 'Level')]:
        p = u.EditorAssetLibrary.duplicate_asset('/Game/Brezi/Pipeline/' + source, PREFIX + '/Pipeline/' + name)
        require(p is not None, 'Cannot duplicate fixture import pipeline')
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
    require(manager.import_scene(PREFIX, manager.create_source_data(str(artifact / 'realism-fixtures.glb')), params), 'Fixture GLB import failed')
    selected = {row['id']: row for row in manifest['objects']}
    imported, added = {}, []
    for actor in actors.get_all_level_actors():
        if actor.get_path_name() in before:
            continue
        added.append(actor.get_path_name())
        actor.set_editor_property('tags', [*actor.tags, u.Name(TAG)])
        actor.set_folder_path('Brezi/Realism/Fixtures')
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh')
            require(mesh is not None, 'Fixture imported without a mesh')
            names = set(re.findall(r'RF_SINK_(?:BOWL|DRAIN|SPOUT|LEVER)', actor.get_actor_label() + ' ' + mesh.get_name()))
            require(len(names) == 1, 'Ambiguous imported fixture identity')
            id_ = names.pop()
            require(id_ not in imported and id_ in selected, 'Duplicate/unknown imported fixture')
            record = selected[id_]
            require(c.get_num_materials() == len(record['materialBindings']), 'Imported fixture material slot count differs')
            for index, binding in enumerate(record['materialBindings']):
                material = sources[binding['sourceId']][1].get_material(binding['sourceSlot'])
                require(material is not None, 'Fixture source material missing')
                c.set_material(index, material)
            c.set_mobility(u.ComponentMobility.STATIC)
            c.set_collision_profile_name('NoCollision')
            c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            c.set_editor_property('can_ever_affect_navigation', False)
            c.set_editor_property('generate_overlap_events', False)
            c.set_editor_property('cast_shadow', True)
            actor.set_actor_label(id_)
            u.EditorAssetLibrary.set_metadata_tag(mesh, 'BreziGeneratedBy', OWNER)
            u.EditorAssetLibrary.set_metadata_tag(mesh, 'BreziFixtureSourceIds', json.dumps(record['sourceIds']))
            require(u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False), 'Cannot save fixture mesh')
            imported[id_] = {'actor': actor.get_path_name(), 'component': c.get_path_name(), 'mesh': mesh.get_path_name(),
                             'sourceIds': record['sourceIds'], 'materials': [c.get_material(i).get_path_name() for i in range(c.get_num_materials())]}
    require(set(imported) == set(selected), 'Fixture imported membership differs')
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
        require(u.EditorAssetLibrary.save_loaded_asset(p, only_if_is_dirty=False), 'Cannot save fixture pipeline')
    require(u.EditorAssetLibrary.save_directory(PREFIX, only_if_is_dirty=True, recursive=True), 'Cannot save fixture asset namespace')
    return {'objects': imported, 'sourceRenderChanges': changes, 'addedActors': added}


def verify_geometry(u, actors, manifest, changes):
    objects = {a.get_path_name(): a for a in actors.get_all_level_actors()}
    records = {r['id']: r for r in manifest['objects']}
    readback = []
    for id_, row in changes['objects'].items():
        actor = objects[row['actor']]
        found = [c for c in actor.get_components_by_class(u.StaticMeshComponent) if c.get_path_name() == row['component']]
        require(len(found) == 1, 'Saved fixture component missing')
        c = found[0]
        require(c.get_editor_property('static_mesh').get_path_name() == row['mesh'], 'Saved fixture mesh changed')
        require(c.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION and not c.get_editor_property('can_ever_affect_navigation'), 'Saved fixture collision/navigation enabled')
        require(c.is_visible() and not c.get_editor_property('hidden_in_game'), 'Saved fixture invisible')
        require([c.get_material(i).get_path_name() for i in range(c.get_num_materials())] == row['materials'], 'Saved fixture materials differ')
        bounds = capture_bounds(u, c)
        expected = records[id_]['expectedWorldBoundsCm']
        error = max(abs(bounds[k][i] - expected[k][i]) for k in ('min', 'max') for i in range(3))
        require(math.isfinite(error) and error < .05, 'Saved fixture bounds differ: ' + id_)
        readback.append({'id': id_, 'actor': row['actor'], 'boundsCm': bounds, 'expectedBoundsCm': expected,
                         'maxErrorCm': error, 'materials': row['materials'], 'collision': 'NoCollision'})
    return readback


def restore(output):
    output = Path(output).resolve()
    report = read(output / 'realism-fixtures-report.json')
    require(report['status'] == 'failed', 'No failed fixture attempt')
    base = module('fixture_restore_paths', 'performance-optimize.py')
    source, output = base.checked_paths(report['sourceOutput'], output)
    require(report['output'] == str(output), 'Failed fixture report belongs elsewhere')
    try:
        os.kill(report['nativeProcessId'], 0)
    except ProcessLookupError:
        pass
    else:
        raise RuntimeError('Native fixture process is still running')
    content = output / 'Project/BreziTwin/Content'
    current = inventory(content)
    require(current == report['failedContentHashes'], 'Fixture Content drift after failure')
    before = report['beforeAssetHashes']
    validate_changes(before, current, content)
    backup = output / 'realism-fixtures-checkpoint/Brezi.umap'
    require(sha(backup) == before[str(content / MAP_FILE)], 'Fixture map backup drift')
    require(read(output / 'performance-source.json')['content'] == before, 'Inherited fixture source drift')
    donor = source / 'Project/BreziTwin/Content'
    require(inventory(donor) == {str(donor / Path(p).relative_to(content)): value for p, value in before.items()}, 'Fixture donor changed')
    history = output / 'realism-fixtures-history' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    history.mkdir(parents=True)
    shutil.copy2(content / MAP_FILE, history / 'failed-Brezi.umap')
    shutil.copy2(backup, content / MAP_FILE)
    for path in current.keys() - before.keys():
        target = history / 'failed-assets' / Path(path).relative_to(content)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(path, str(target))
    require(inventory(content) == before, 'Fixture restoration not exact')
    for name in ['realism-fixtures-report.json', 'realism-fixtures-process.json', 'realism-fixtures.log', 'realism-fixtures.log.json', 'realism-fixtures-checkpoint']:
        path = output / name
        if path.exists():
            shutil.move(str(path), str(history / name))
    write(history / 'restoration.json', {'status': 'fixture-failure-restored', 'generatedAt': now(), 'contentHashes': before})
    print(json.dumps({'status': 'fixture-failure-restored', 'history': str(history)}))


def main():
    import unreal as u
    base = module('fixture_geometry_witness', 'performance-optimize.py')
    require(all(os.environ.get(k) for k in ('BREZI_MODEL_OUTPUT', 'BREZI_PERFORMANCE_SOURCE', 'BREZI_FIXTURES_OUTPUT')), 'Explicit inherited project and fixture artifact required')
    source, output = base.checked_paths(ROOT / os.environ['BREZI_PERFORMANCE_SOURCE'], ROOT / os.environ['BREZI_MODEL_OUTPUT'])
    artifact = (ROOT / os.environ['BREZI_FIXTURES_OUTPUT']).resolve()
    require(artifact.is_relative_to(ROOT / 'output/unreal') and not artifact.is_relative_to(output), 'Fixture artifact must be separate from target project')
    project = output / 'Project/BreziTwin'
    require(Path(u.Paths.project_dir()).resolve() == project, 'Wrong native fixture project')
    content = project / 'Content'
    before = inventory(content)
    provenance = read(output / 'performance-source.json')
    require(provenance['status'] == 'verified-scene-inherited' and provenance['donor'] == str(source) and provenance['content'] == before, 'Unverified fixture inheritance')
    require(not any((output / name).exists() for name in ('realism-fixtures-report.json', 'realism-import-report.json', 'performance-scene-report.json', 'nanite-study-report.json')), 'Fixture pass requires a fresh inherited output')
    donor = source / 'Project/BreziTwin/Content'
    source_before = inventory(donor)
    require({str(content / Path(p).relative_to(donor)): value for p, value in source_before.items()} == before, 'Fixture donor Content differs')
    manifest = read(artifact / 'geometry-report.json')
    geometry = output / 'geometry'
    scene = read(geometry / 'scene.json')
    validate_manifest(manifest, scene)
    require(manifest['sourceSceneSha256'] == sha(geometry / 'scene.json') and manifest['sourceObjSha256'] == sha(geometry / 'dom-mm.obj')
            and manifest['glbSha256'] == sha(artifact / 'realism-fixtures.glb'), 'Fixture geometry input pins differ')
    generator = ROOT / 'scripts/unreal/realism-fixtures-geometry.py'
    require(manifest['generatorSha256'] == sha(generator), 'Fixture generator changed after export')
    folder = output / 'realism-fixtures-checkpoint'
    folder.mkdir(exist_ok=False)
    shutil.copy2(content / MAP_FILE, folder / 'Brezi.umap')
    pipeline = {str(ROOT / 'scripts/unreal' / name): sha(ROOT / 'scripts/unreal' / name)
                for name in ('realism-fixtures-import.py', 'realism-fixtures-geometry.py', 'realism-fabric.py', 'performance-optimize.py', 'performance_scene_policy.py')}
    inputs = {str(p): sha(p) for p in [*sorted(geometry.rglob('*')), artifact / 'geometry-report.json', artifact / 'realism-fixtures.glb'] if p.is_file()}
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'pending', 'startedAt': now(), 'project': str(project),
              'output': str(output), 'sourceOutput': str(source), 'nativeProcessId': os.getpid(), 'artifact': str(artifact),
              'manifestSha256': sha(artifact / 'geometry-report.json'), 'sourceIds': SOURCE_IDS, 'beforeAssetHashes': before,
              'inputFiles': inputs, 'pipelineFiles': pipeline, 'renderedVerified': False}
    write(output / 'realism-fixtures-report.json', report)
    try:
        actors = u.get_editor_subsystem(u.EditorActorSubsystem)
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(levels.load_level(MAP), 'Cannot load fixture baseline map')
        original = witness(base, u, actors)
        fabric = module('brezi_realism_fixture_fabric', 'realism-fabric.py')
        report['fabric'] = fabric.apply(u, actors, output)
        report['materialBindingChanges'] = report['fabric']['bindingChanges']
        changes = apply_geometry(u, actors, levels, manifest, artifact)
        report.update(changes)
        expected = expected_witness(original, changes['sourceRenderChanges'], report['materialBindingChanges'])
        authored = witness(base, u, actors)
        verify_witness(expected, authored, changes['addedActors'])
        verify_geometry(u, actors, manifest, changes)
        require(levels.save_current_level(), 'Cannot save fixture map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False), 'Cannot unload fixture map')
        require(levels.load_level(MAP), 'Cannot reload fixture map')
        reloaded = witness(base, u, actors)
        verify_witness(expected, reloaded, changes['addedActors'])
        require(authored == reloaded, 'Saved fixture actor witness differs')
        readback = verify_geometry(u, actors, manifest, changes)
        report['savedFabricReadback'] = fabric.verify(u, actors, report['fabric'])
        for field in ('pipelineFiles', 'inputFiles'):
            for path, value in report['fabric'].get(field, {}).items():
                absolute = str((ROOT / path).resolve())
                require(sha(absolute) == value, 'Fabric input changed: ' + absolute)
                require(absolute not in report[field] or report[field][absolute] == value, 'Conflicting fabric input pin')
                report[field][absolute] = value
        after = inventory(content)
        validate_changes(before, after, content)
        require(source_before == inventory(donor), 'Historical fixture donor Content changed')
        for path, value in {**report['pipelineFiles'], **report['inputFiles']}.items():
            require(sha(path) == value, 'Fixture authoring input changed during native import')
        report.update(status='realism-fixtures-validated', savedReloaded=True, protectedContentUnchanged=True,
                      sourceGeometryCollisionAndTransformsPreserved=True, originalMaterialAssetsPreserved=True, materialBindingsAudited=True,
                      originalActorCount=len(original), finalActorCount=len(reloaded),
                      protectedActorWitnessSha256=digest(expected), savedProtectedActorWitnessSha256=digest({p: reloaded[p] for p in expected}),
                      authoredActorWitnessSha256=digest(authored), savedActorWitnessSha256=digest(reloaded),
                      savedGeometryReadback=readback, maxNativeBoundsErrorCm=max(row['maxErrorCm'] for row in readback),
                      afterAssetHashes=after, newAssets=sorted(after.keys() - before.keys()),
                      changedAssets=[{'path': p, 'beforeSha256': before[p], 'afterSha256': after[p]} for p in before if before[p] != after[p]])
        u.log('BREZI_REALISM_FIXTURES validated')
    except Exception as error:
        report.update(status='failed', error=str(error), failedContentHashes=inventory(content))
        raise
    finally:
        report['generatedAt'] = now()
        write(output / 'realism-fixtures-report.json', report)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--restore':
        restore(sys.argv[2])
    else:
        main()
