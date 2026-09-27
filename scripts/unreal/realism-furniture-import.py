"""Bounded furniture refinements over a freshly inherited R4 scene.

Twenty existing PH upholstery visuals are hidden behind owned replacements.
Eleven distinct dining timber PH slots use two grain-axis material clones.
All original assets, source transforms/collision, and R4 door attachments survive.
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
OWNER = 'scripts/unreal/realism-furniture-import.py'
PREFIX = '/Game/Brezi/Realism/Furniture'
TAG = 'BreziRealismFurniture20260926'
MAP = '/Game/Brezi/Maps/Brezi'
MAP_FILE = 'Brezi/Maps/Brezi.umap'
SOURCE_IDS = [f'DOM_{i:05d}' for i in (1443,1444,1445,1446,1447,1448,1449,1452,1466,1473,1475,1482,1484,1491,1493,1500,1502,1509,1511,1518)]
MESH_IDS = ['RU_' + id_ for id_ in SOURCE_IDS]
GRAIN_IDS = [f'DOM_{i:05d}' for i in (1457,1458,1459,1460,1461,1474,1483,1492,1501,1510,1519)]


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
        require(any(Path(path).resolve().is_relative_to(content / 'Brezi/Realism' / part) for part in ('Furniture',)),
                'New asset outside furniture namespace')
        require(Path(path).suffix in ('.uasset', '.uexp', '.ubulk'), 'Unexpected furniture Content file')


def validate_manifest(manifest, scene, photoreal):
    require(manifest['owner'] == 'scripts/unreal/realism-upholstery-geometry.py', 'Unknown upholstery generator')
    require(manifest['status'] == 'offline-geometry-validated', 'Offline upholstery unverified')
    require(scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'Only C/B/B supported')
    require(sorted(manifest['sourceIds']) == SOURCE_IDS, 'Upholstery source scope differs')
    require(manifest['hiddenSourceIds'] == [], 'Original source actors must remain untouched')
    require(sorted(manifest['hiddenVisualSourceIds']) == ['PH_' + id_ for id_ in SOURCE_IDS], 'Existing visual hiding scope differs')
    require(sorted(row['id'] for row in manifest['objects']) == sorted(MESH_IDS), 'Upholstery mesh identities differ')
    records = {row['id']: row for row in scene['objects']}
    for row in manifest['objects']:
        id_ = row['id'].removeprefix('RU_')
        record = records[id_]
        require(row['sourceIds'] == [id_] and row['hiddenSourceIds'] == []
                and row['hiddenVisualSourceIds'] == ['PH_' + id_], 'Per-member source/visual scope differs')
        require(record['enabled'] and record['instances'] == 1, 'Unsupported source instancing/visibility')
        require(record['name'].startswith(('LIVING-103-SOFA-L ·', 'LIVING-103-DINING ·')), 'Source semantic scope differs')
        require(not any(record.get('metadata', {}).get(k) for k in ('doorMotion', 'walkSurface', 'dynamicCameraOccluder')), 'Dynamic source unsupported')
        require(row['materialBindings'] == [{'sourceId': id_, 'sourceSlot': 0, 'visualSourceId': 'PH_' + id_}], 'Upholstery material source differs')
        require(photoreal['geometry']['objects']['PH_' + id_]['sourceId'] == id_, 'Native PH visual identity missing')
        bounds = row['visualBoundsMm']
        expected = {'min': [bounds['min'][0]/10, -bounds['max'][1]/10, bounds['min'][2]/10],
                    'max': [bounds['max'][0]/10, -bounds['min'][1]/10, bounds['max'][2]/10]}
        require(all(math.isfinite(v) for pair in expected.values() for v in pair), 'Invalid upholstery bounds')
        require(max(abs(expected[k][i] - row['expectedWorldBoundsCm'][k][i]) for k in ('min', 'max') for i in range(3)) < 1e-5,
                'Upholstery coordinate conversion differs')


def expected_witness(original, changes, material_changes=()):
    result = copy.deepcopy(original)
    slots = set()
    for change in material_changes:
        identity = (change['actor'], change['component'], change['slot'])
        require(identity not in slots, 'Duplicate grain binding delta')
        slots.add(identity)
        require(change['actor'] in result, 'Grain binding actor absent')
        found = [c for c in result[change['actor']]['components'] if c['path'] == change['component']]
        require(len(found) == 1 and 'materials' in found[0], 'Grain binding component absent')
        c, slot = found[0], change['slot']
        require(type(slot) is int and 0 <= slot < len(c['materials']), 'Grain slot outside original component')
        require(c['materials'][slot] == change['before'], 'Grain binding baseline differs')
        require(change['after'].startswith('/Game/Brezi/Realism/Furniture/Materials/'), 'Grain replacement outside owned namespace')
        c['materials'][slot] = change['after']
    require(sorted(row['sourceId'] for row in material_changes) == GRAIN_IDS, 'Expected exactly eleven selected grain slots')
    require(sorted(row['sourceId'] for row in changes) == SOURCE_IDS, 'Unreported furniture visibility scope')
    components = set()
    for change in changes:
        require(change['visualSourceId'] == 'PH_' + change['sourceId'], 'Original source actor may not be hidden')
        require(change['component'] not in components, 'Duplicate furniture source component')
        components.add(change['component'])
        require(change['actor'] in result, 'Furniture source actor missing')
        found = [c for c in result[change['actor']]['components'] if c['path'] == change['component']]
        require(len(found) == 1 and 'mesh' in found[0], 'Furniture source component missing')
        c = found[0]
        require(c['visible'] and not c['hiddenInGame'], 'Furniture original was already hidden')
        require(change['before'] == {key: c[key] for key in ('visible', 'hiddenInGame', 'renderFlags')}, 'Furniture visibility baseline differs')
        c.update(visible=False, hiddenInGame=True, renderFlags={name: False for name in RENDER_FLAGS})
        require(change['after'] == {key: c[key] for key in ('visible', 'hiddenInGame', 'renderFlags')}, 'Furniture visibility delta differs')
    return result


def verify_witness(expected, actual, added):
    require(len(set(added)) == len(added) and not set(expected) & set(added), 'Furniture actor identities overlap')
    require(set(actual) == set(expected) | set(added), 'Unreported furniture actor addition/removal')
    for path, row in expected.items():
        require(actual[path] == row, 'Original geometry/transform/material/collision changed: ' + path)
    for path in added:
        row = actual[path]
        require(TAG in row['tags'] and not any(t.startswith(('DOM_', 'BreziDoor')) for t in row['tags']), 'Unowned furniture actor')
        for c in row['components']:
            if 'collision' in c:
                require('NO_COLLISION' in c['collision'] and not c['navigation'], 'Furniture gained collision/navigation')


def apply_geometry(u, actors, levels, manifest, artifact, photoreal):
    sources = {}
    by_path = {a.get_path_name(): a for a in actors.get_all_level_actors()}
    require(not any(a.actor_has_tag(TAG) for a in by_path.values()), 'Furniture already authored')
    for id_ in SOURCE_IDS:
        entry = photoreal['geometry']['objects']['PH_' + id_]
        actor = by_path[entry['actor']]
        meshes = list(actor.get_components_by_class(u.StaticMeshComponent))
        require(len(meshes) == 1 and meshes[0].get_editor_property('static_mesh').get_path_name() == entry['mesh'], 'PH upholstery visual identity differs')
        c = meshes[0]
        require(c.get_editor_property('mobility') == u.ComponentMobility.STATIC, 'Upholstery must remain static')
        require(c.is_visible() and not c.get_editor_property('hidden_in_game'), 'Existing upholstery visual already hidden')
        require(c.get_num_materials() == 1, 'Upholstery baseline material slots differ')
        sources[id_] = (actor, c)
    pipelines = []
    for source, name in [('GLTFSceneAssets', 'Assets'), ('GLTFMaterials', 'Materials'), ('LevelActors', 'Level')]:
        p = u.EditorAssetLibrary.duplicate_asset('/Game/Brezi/Pipeline/' + source, PREFIX + '/Pipeline/' + name)
        require(p is not None, 'Cannot duplicate furniture import pipeline')
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
    require(manager.import_scene(PREFIX + '/Geometry', manager.create_source_data(str(artifact / 'realism-upholstery.glb')), params), 'Furniture GLB import failed')
    selected = {row['id']: row for row in manifest['objects']}
    imported, added = {}, []
    for actor in actors.get_all_level_actors():
        if actor.get_path_name() in before:
            continue
        added.append(actor.get_path_name())
        actor.set_editor_property('tags', [*actor.tags, u.Name(TAG)])
        actor.set_folder_path('Brezi/Realism/Furniture')
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh')
            require(mesh is not None, 'Furniture imported without a mesh')
            names = set(re.findall(r'RU_DOM_[0-9]{5}', actor.get_actor_label() + ' ' + mesh.get_name()))
            require(len(names) == 1, 'Ambiguous imported furniture identity')
            id_ = names.pop()
            require(id_ not in imported and id_ in selected, 'Duplicate/unknown imported furniture')
            record = selected[id_]
            require(c.get_num_materials() == len(record['materialBindings']), 'Imported furniture material slot count differs')
            for index, binding in enumerate(record['materialBindings']):
                material = sources[binding['sourceId']][1].get_material(binding['sourceSlot'])
                require(material is not None, 'Furniture source material missing')
                c.set_material(index, material)
            c.set_mobility(u.ComponentMobility.STATIC)
            c.set_collision_profile_name('NoCollision')
            c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            c.set_editor_property('can_ever_affect_navigation', False)
            c.set_editor_property('generate_overlap_events', False)
            c.set_editor_property('cast_shadow', True)
            actor.set_actor_label(id_)
            u.EditorAssetLibrary.set_metadata_tag(mesh, 'BreziGeneratedBy', OWNER)
            u.EditorAssetLibrary.set_metadata_tag(mesh, 'BreziFurnitureSourceIds', json.dumps(record['sourceIds']))
            require(u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False), 'Cannot save furniture mesh')
            imported[id_] = {'actor': actor.get_path_name(), 'component': c.get_path_name(), 'mesh': mesh.get_path_name(),
                             'sourceIds': record['sourceIds'], 'materials': [c.get_material(i).get_path_name() for i in range(c.get_num_materials())]}
    require(set(imported) == set(selected), 'Furniture imported membership differs')
    changes = []
    for id_, (actor, c) in sorted(sources.items()):
        previous = {'visible': bool(c.get_editor_property('visible')), 'hiddenInGame': bool(c.get_editor_property('hidden_in_game')),
                    'renderFlags': {name: bool(c.get_editor_property(name)) for name in RENDER_FLAGS}}
        c.set_visibility(False, False)
        c.set_hidden_in_game(True, False)
        for name in RENDER_FLAGS:
            c.set_editor_property(name, False)
        changes.append({'sourceId': id_, 'visualSourceId': 'PH_' + id_, 'actor': actor.get_path_name(), 'component': c.get_path_name(), 'before': previous,
                        'after': {'visible': False, 'hiddenInGame': True, 'renderFlags': {name: False for name in RENDER_FLAGS}}})
    for p in pipelines:
        require(u.EditorAssetLibrary.save_loaded_asset(p, only_if_is_dirty=False), 'Cannot save furniture pipeline')
    require(u.EditorAssetLibrary.save_directory(PREFIX, only_if_is_dirty=True, recursive=True), 'Cannot save furniture asset namespace')
    return {'objects': imported, 'sourceRenderChanges': changes, 'addedActors': added}


def restore(output):
    output = Path(output).resolve()
    report = read(output / 'realism-furniture-report.json')
    require(report['status'] == 'failed', 'No failed furniture attempt')
    base = module('fixture_restore_paths', 'performance-optimize.py')
    source, output = base.checked_paths(report['sourceOutput'], output)
    require(report['output'] == str(output), 'Failed furniture report belongs elsewhere')
    try:
        os.kill(report['nativeProcessId'], 0)
    except ProcessLookupError:
        pass
    else:
        raise RuntimeError('Native furniture process is still running')
    content = output / 'Project/BreziTwin/Content'
    current = inventory(content)
    require(current == report['failedContentHashes'], 'Furniture Content drift after failure')
    before = report['beforeAssetHashes']
    validate_changes(before, current, content)
    backup = output / 'realism-furniture-checkpoint/Brezi.umap'
    require(sha(backup) == before[str(content / MAP_FILE)], 'Furniture map backup drift')
    require(read(output / 'performance-source.json')['content'] == before, 'Inherited furniture source drift')
    donor = source / 'Project/BreziTwin/Content'
    require(inventory(donor) == {str(donor / Path(p).relative_to(content)): value for p, value in before.items()}, 'Furniture donor changed')
    history = output / 'realism-furniture-history' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    history.mkdir(parents=True)
    shutil.copy2(content / MAP_FILE, history / 'failed-Brezi.umap')
    shutil.copy2(backup, content / MAP_FILE)
    for path in current.keys() - before.keys():
        target = history / 'failed-assets' / Path(path).relative_to(content)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(path, str(target))
    require(inventory(content) == before, 'Furniture restoration not exact')
    for name in ['realism-furniture-report.json', 'realism-furniture-process.json', 'realism-furniture.log', 'realism-furniture.log.json', 'realism-furniture-checkpoint']:
        path = output / name
        if path.exists():
            shutil.move(str(path), str(history / name))
    write(history / 'restoration.json', {'status': 'furniture-failure-restored', 'generatedAt': now(), 'contentHashes': before})
    print(json.dumps({'status': 'furniture-failure-restored', 'history': str(history)}))


def main():
    import unreal as u
    base = module('fixture_geometry_witness', 'performance-optimize.py')
    require(all(os.environ.get(k) for k in ('BREZI_MODEL_OUTPUT', 'BREZI_PERFORMANCE_SOURCE', 'BREZI_FURNITURE_OUTPUT')), 'Explicit inherited project and furniture artifact required')
    source, output = base.checked_paths(ROOT / os.environ['BREZI_PERFORMANCE_SOURCE'], ROOT / os.environ['BREZI_MODEL_OUTPUT'])
    artifact = (ROOT / os.environ['BREZI_FURNITURE_OUTPUT']).resolve()
    require(artifact.is_relative_to(ROOT / 'output/unreal') and not artifact.is_relative_to(output), 'Furniture artifact must be separate from target project')
    project = output / 'Project/BreziTwin'
    require(Path(u.Paths.project_dir()).resolve() == project, 'Wrong native furniture project')
    content = project / 'Content'
    before = inventory(content)
    provenance = read(output / 'performance-source.json')
    require(provenance['status'] == 'verified-scene-inherited' and provenance['donor'] == str(source) and provenance['content'] == before, 'Unverified furniture inheritance')
    require(not any((output / name).exists() for name in ('realism-furniture-report.json', 'realism-room-details-report.json', 'realism-fixtures-report.json', 'realism-import-report.json', 'performance-scene-report.json', 'nanite-study-report.json')), 'Furniture pass requires a fresh inherited output')
    donor = source / 'Project/BreziTwin/Content'
    source_before = inventory(donor)
    require({str(content / Path(p).relative_to(donor)): value for p, value in source_before.items()} == before, 'Furniture donor Content differs')
    manifest = read(artifact / 'geometry-report.json')
    geometry = output / 'geometry'
    scene = read(geometry / 'scene.json')
    photoreal_file = output / 'photoreal-import-report.json'
    photoreal = read(photoreal_file)
    require(provenance['receiptPins'].get(str(source / 'photoreal-import-report.json')) == sha(photoreal_file), 'Inherited PH receipt not pinned')
    validate_manifest(manifest, scene, photoreal)
    require(manifest['sourceSceneSha256'] == sha(geometry / 'scene.json') and manifest['sourceObjSha256'] == sha(geometry / 'dom-mm.obj')
            and manifest['photorealReportSha256'] == sha(photoreal_file) and manifest['glbSha256'] == sha(artifact / 'realism-upholstery.glb'), 'Furniture geometry input pins differ')
    generator = ROOT / 'scripts/unreal/realism-upholstery-geometry.py'
    require(manifest['generatorSha256'] == sha(generator), 'Furniture generator changed after export')
    require(manifest['generatorDependencies'] == {'scripts/unreal/realism-fixtures-geometry.py': sha(ROOT / 'scripts/unreal/realism-fixtures-geometry.py')}, 'Unexpected upholstery generator dependency')
    folder = output / 'realism-furniture-checkpoint'
    folder.mkdir(exist_ok=False)
    shutil.copy2(content / MAP_FILE, folder / 'Brezi.umap')
    pipeline = {str(ROOT / 'scripts/unreal' / name): sha(ROOT / 'scripts/unreal' / name)
                for name in ('realism-furniture-import.py', 'realism-upholstery-geometry.py', 'realism-furniture-grain.py', 'realism-grain-study.py', 'realism-room-details-import.py', 'realism-fixtures-import.py', 'performance-optimize.py', 'performance_scene_policy.py')}
    for path, value in manifest.get('generatorDependencies', {}).items():
        require(sha(ROOT / path) == value, 'Upholstery helper changed')
        pipeline[str(ROOT / path)] = value
    inputs = {str(p): sha(p) for p in [*sorted(geometry.rglob('*')), artifact / 'geometry-report.json', artifact / 'realism-upholstery.glb', photoreal_file] if p.is_file()}
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'pending', 'startedAt': now(), 'project': str(project),
              'output': str(output), 'sourceOutput': str(source), 'nativeProcessId': os.getpid(), 'artifact': str(artifact),
              'manifestSha256': sha(artifact / 'geometry-report.json'), 'sourceIds': SOURCE_IDS, 'hiddenSourceIds': [], 'hiddenVisualSourceIds': ['PH_' + id_ for id_ in SOURCE_IDS], 'beforeAssetHashes': before,
              'inputFiles': inputs, 'pipelineFiles': pipeline, 'renderedVerified': False}
    write(output / 'realism-furniture-report.json', report)
    try:
        actors = u.get_editor_subsystem(u.EditorActorSubsystem)
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(levels.load_level(MAP), 'Cannot load furniture baseline map')
        original = witness(base, u, actors)
        grain = module('brezi_realism_furniture_grain', 'realism-furniture-grain.py')
        report['grain'] = grain.apply(u, actors, output)
        report['materialBindingChanges'] = report['grain']['bindingChanges']
        changes = apply_geometry(u, actors, levels, manifest, artifact, photoreal)
        report.update(changes)
        expected = expected_witness(original, changes['sourceRenderChanges'], report['materialBindingChanges'])
        authored = witness(base, u, actors)
        verify_witness(expected, authored, changes['addedActors'])
        verify_geometry(u, actors, manifest, changes)
        require(levels.save_current_level(), 'Cannot save furniture map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False), 'Cannot unload furniture map')
        require(levels.load_level(MAP), 'Cannot reload furniture map')
        reloaded = witness(base, u, actors)
        verify_witness(expected, reloaded, changes['addedActors'])
        require(authored == reloaded, 'Saved furniture actor witness differs')
        readback = verify_geometry(u, actors, manifest, changes)
        report['savedGrainReadback'] = grain.verify(u, actors, report['grain'])
        for field in ('pipelineFiles', 'inputFiles'):
            for path, value in report['grain'].get(field, {}).items():
                absolute = str((ROOT / path).resolve())
                require(sha(absolute) == value, 'Grain input changed: ' + absolute)
                require(absolute not in report[field] or report[field][absolute] == value, 'Conflicting grain input pin')
                report[field][absolute] = value
        after = inventory(content)
        validate_changes(before, after, content)
        require(source_before == inventory(donor), 'Historical furniture donor Content changed')
        for path, value in {**report['pipelineFiles'], **report['inputFiles']}.items():
            require(sha(path) == value, 'Furniture authoring input changed during native import')
        report.update(status='realism-furniture-validated', savedReloaded=True, protectedContentUnchanged=True,
                      sourceGeometryCollisionAndTransformsPreserved=True, originalMaterialAssetsPreserved=True, materialBindingsAudited=True,
                      originalActorCount=len(original), finalActorCount=len(reloaded),
                      protectedActorWitnessSha256=digest(expected), savedProtectedActorWitnessSha256=digest({p: reloaded[p] for p in expected}),
                      authoredActorWitnessSha256=digest(authored), savedActorWitnessSha256=digest(reloaded),
                      savedGeometryReadback=readback, maxNativeBoundsErrorCm=max(row['maxErrorCm'] for row in readback),
                      afterAssetHashes=after, newAssets=sorted(after.keys() - before.keys()),
                      changedAssets=[{'path': p, 'beforeSha256': before[p], 'afterSha256': after[p]} for p in before if before[p] != after[p]])
        u.log('BREZI_REALISM_FURNITURE validated')
    except Exception as error:
        report.update(status='failed', error=str(error), failedContentHashes=inventory(content))
        raise
    finally:
        report['generatedAt'] = now()
        write(output / 'realism-furniture-report.json', report)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--restore':
        restore(sys.argv[2])
    else:
        main()
