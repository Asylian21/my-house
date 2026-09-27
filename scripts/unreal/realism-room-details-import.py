"""Bounded room visual overlay with separately attached native appliance door actors.

Original assets, transforms, collision, material bindings and door tags are immutable.
Only fourteen source components stop rendering; moving source visibility stays true.
Four countertop patches are additive. Frozen fixture helpers supply common witnesses.
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
OWNER = 'scripts/unreal/realism-room-details-import.py'
PREFIX = '/Game/Brezi/Realism/RoomDetails'
TAG = 'BreziRealismRoomDetails20260926'
MAP = '/Game/Brezi/Maps/Brezi'
MAP_FILE = 'Brezi/Maps/Brezi.umap'
HIDDEN_IDS = [f'DOM_{i:05d}' for i in [*range(938, 950), 1225, 1226]]
SOURCE_IDS = ['DOM_00740', *HIDDEN_IDS]
MOTION_IDS = [f'DOM_{i:05d}' for i in [941, 942, 943, 947, 948, 949]]
MESH_IDS = [f'RD_{appliance}_{part}' for appliance in ('WASHER', 'DRYER')
            for part in ('BODY', 'CONTROLS', 'SELECTOR', 'DOOR_RIM', 'DOOR_GLASS', 'DOOR_HANDLE')] + [
                'RD_BOY_LAMP_BASE', 'RD_BOY_LAMP_GLOBE', *[f'RD_SINK_CORNER_{i}' for i in range(1, 5)]]
PASS_FLAGS = ('render_in_main_pass', 'render_in_depth_pass')
RENDER_FLAGS = ('cast_shadow', 'cast_hidden_shadow', 'affect_distance_field_lighting',
                'affect_dynamic_indirect_lighting', 'affect_indirect_lighting_while_hidden', 'visible_in_ray_tracing')


def _helper():
    spec = importlib.util.spec_from_file_location('frozen_fixture_helpers', ROOT / 'scripts/unreal/realism-fixtures-import.py')
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


helper = _helper()
require, sha, read, write, now, digest, module, inventory = (getattr(helper, name) for name in
    ('require', 'sha', 'read', 'write', 'now', 'digest', 'module', 'inventory'))


def validate_changes(before, after, content):
    content = Path(content).resolve()
    require(before.keys() <= after.keys(), 'Removed original Content file')
    for path, value in before.items():
        require(path == str(content / MAP_FILE) or after[path] == value, 'Protected source asset changed: ' + path)
    for path in after.keys() - before.keys():
        require(any(Path(path).resolve().is_relative_to(content / 'Brezi/Realism' / part) for part in ('RoomDetails',)),
                'New asset outside room-detail namespace')
        require(Path(path).suffix in ('.uasset', '.uexp', '.ubulk'), 'Unexpected room detail Content file')


def validate_manifest(manifest, scene, doors):
    require(manifest['owner'] == 'scripts/unreal/realism-room-details-geometry.py', 'Unknown room detail generator')
    require(manifest['status'] == 'offline-geometry-validated', 'Unverified offline room details')
    require(scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'Only C/B/B supported')
    require(sorted(manifest['sourceIds']) == SOURCE_IDS and sorted(manifest['hiddenSourceIds']) == HIDDEN_IDS,
            'Room detail source/hiding scope differs')
    require(manifest['referenceSourceIds'] == ['DOM_00759'], 'Unexpected room detail reference')
    require(sorted(row['id'] for row in manifest['objects']) == sorted(MESH_IDS), 'Room detail mesh identities differ')
    require(sorted({id_ for row in manifest['objects'] for id_ in row['sourceIds']}) == SOURCE_IDS, 'Room detail source coverage differs')
    require(sorted(id_ for row in manifest['objects'] for id_ in row['hiddenSourceIds']) == HIDDEN_IDS, 'Repeated/unreported hidden room source')
    require(sorted(row['motionSourceId'] for row in manifest['objects'] if row['motionSourceId']) == MOTION_IDS, 'Moving visual scope differs')
    require(sorted(manifest['motionBindings']) == MOTION_IDS, 'Moving source scope differs')
    members = {r['sourceObjectId']: (d['id'], r) for d in doors['doors'] for r in d['members']}
    records = {row['id']: row for row in scene['objects']}
    for id_ in SOURCE_IDS:
        record = records[id_]
        require(record['enabled'] and record['instances'] == 1, 'Room source instancing/visibility differs')
        prefix = ('KITCHEN-RUN · pracovná doska ostrovčeka' if id_ == 'DOM_00740' else
                  'BATHROOM-FITOUT-STACKED-LAUNDRY-' if id_ < 'DOM_01225' else 'C-BOY-109 · DESK ·')
        require(record['name'].startswith(prefix), 'Source ID no longer denotes the selected room detail')
        metadata = record.get('metadata', {})
        require(not metadata.get('walkSurface') and bool(metadata.get('dynamicCameraOccluder')) == (id_ in MOTION_IDS), 'Unexpected walk surface/camera occluder')
        require(bool(metadata.get('doorMotion')) == (id_ in MOTION_IDS), 'Unexpected moving room source')
    for id_, binding in manifest['motionBindings'].items():
        door, member = members[id_]
        require(binding == {**{key: member[key] for key in ('runtimeTag', 'collision', 'closedBoundsCm')}, 'doorId': door}, 'Door source contract differs')
        require(not member['hidden'] and door in ('BATH-105-WASHER-DOOR', 'BATH-105-DRYER-DOOR'), 'Unexpected door semantics')
    for row in manifest['objects']:
        require(row['sourceIds'] and len(set(row['sourceIds'])) == len(row['sourceIds']), 'Invalid per-mesh source list')
        additive = row['id'].startswith('RD_SINK_CORNER_')
        require(row['mode'] == ('additive' if additive else 'replacement'), 'Room detail mode differs')
        require((row['sourceIds'] == ['DOM_00740'] and not row['hiddenSourceIds']) if additive else bool(row['hiddenSourceIds']), 'Unexpected additive/replacement scope')
        if row['motionSourceId']:
            require(row['sourceIds'] == [row['motionSourceId']] and row['hiddenSourceIds'] == row['sourceIds'], 'Door overlay source differs')
            require(row['doorId'] == manifest['motionBindings'][row['motionSourceId']]['doorId'], 'Door overlay identity differs')
        else:
            require(row['doorId'] is None, 'Static detail declares door')
        require(row['materialBindings'], 'Missing room material references')
        for binding in row['materialBindings']:
            require(binding['sourceId'] in SOURCE_IDS and type(binding['sourceSlot']) is int
                    and 0 <= binding['sourceSlot'] < len(records[binding['sourceId']]['materialSlots']), 'Invalid room source material slot')
        bounds = row['visualBoundsMm']
        expected = {'min': [bounds['min'][0]/10, -bounds['max'][1]/10, bounds['min'][2]/10],
                    'max': [bounds['max'][0]/10, -bounds['min'][1]/10, bounds['max'][2]/10]}
        require(all(math.isfinite(v) for pair in expected.values() for v in pair), 'Invalid room bounds')
        require(max(abs(expected[k][i] - row['expectedWorldBoundsCm'][k][i]) for k in ('min', 'max') for i in range(3)) < 1e-5,
                'Room detail coordinate conversion differs')


def witness(base, u, actors):
    rows = helper.witness(base, u, actors)
    for actor in actors.get_all_level_actors():
        components = {c.get_path_name(): c for c in actor.get_components_by_class(u.SceneComponent)}
        for row in rows[actor.get_path_name()]['components']:
            parent = components[row['path']].get_attach_parent()
            row['attachParent'] = parent.get_path_name() if parent else None
            row['mobility'] = str(components[row['path']].get_editor_property('mobility'))
            if isinstance(components[row['path']], u.StaticMeshComponent):
                row['passFlags'] = {name: bool(components[row['path']].get_editor_property(name)) for name in PASS_FLAGS}
    return rows


def expected_witness(original, changes):
    result = copy.deepcopy(original)
    require(sorted(row['sourceId'] for row in changes) == HIDDEN_IDS, 'Unreported room visibility scope')
    components = set()
    for change in changes:
        require(change['component'] not in components, 'Duplicate room source component')
        components.add(change['component'])
        found = [c for c in result[change['actor']]['components'] if c['path'] == change['component']]
        require(len(found) == 1 and 'mesh' in found[0], 'Room source component missing')
        c = found[0]
        require(c['visible'] and not c['hiddenInGame'], 'Room original was already hidden')
        require(change['before'] == {key: c[key] for key in ('visible', 'hiddenInGame', 'renderFlags', 'passFlags')}, 'Room visibility baseline differs')
        moving = change['sourceId'] in MOTION_IDS
        c.update(visible=moving, hiddenInGame=not moving, renderFlags={name: False for name in RENDER_FLAGS},
                 passFlags={name: False for name in PASS_FLAGS} if moving else c['passFlags'])
        require(change['after'] == {key: c[key] for key in ('visible', 'hiddenInGame', 'renderFlags', 'passFlags')}, 'Room visibility delta differs')
    return result


def verify_witness(expected, actual, added):
    require(len(set(added)) == len(added) and not set(expected) & set(added), 'Room detail actor identities overlap')
    require(set(actual) == set(expected) | set(added), 'Unreported room detail actor addition/removal')
    for path, row in expected.items():
        require(actual[path] == row, 'Original geometry/transform/material/collision changed: ' + path)
    for path in added:
        row = actual[path]
        require(TAG in row['tags'] and not any(t.startswith(('DOM_', 'BreziDoor')) for t in row['tags']), 'Unowned room detail actor')
        for c in row['components']:
            if 'collision' in c:
                require('NO_COLLISION' in c['collision'] and not c['navigation'], 'Room detail gained collision/navigation')


def capture_bounds(u, component):
    origin, extent, _ = u.SystemLibrary.get_component_bounds(component)
    lo, hi = origin - extent, origin + extent
    return {'min': [float(lo.x), float(lo.y), float(lo.z)], 'max': [float(hi.x), float(hi.y), float(hi.z)]}


def apply_geometry(u, actors, levels, manifest, artifact):
    sources = {}
    for actor in actors.get_all_level_actors():
        require(not actor.actor_has_tag(TAG), 'Room details already authored')
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh')
            id_ = str(u.EditorAssetLibrary.get_metadata_tag(mesh, 'source_object_id')) if mesh else ''
            if id_ not in SOURCE_IDS:
                continue
            require(id_ not in sources, 'Duplicate room detail source component')
            require(c.get_editor_property('mobility') == (u.ComponentMobility.MOVABLE if id_ in MOTION_IDS else u.ComponentMobility.STATIC), 'Room source mobility differs')
            sources[id_] = (actor, c)
    require(sorted(sources) == SOURCE_IDS, 'Native room detail sources missing')
    pipelines = []
    for source, name in [('GLTFSceneAssets', 'Assets'), ('GLTFMaterials', 'Materials'), ('LevelActors', 'Level')]:
        p = u.EditorAssetLibrary.duplicate_asset('/Game/Brezi/Pipeline/' + source, PREFIX + '/Pipeline/' + name)
        require(p is not None, 'Cannot duplicate room detail import pipeline')
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
    require(manager.import_scene(PREFIX, manager.create_source_data(str(artifact / 'realism-room-details.glb')), params), 'Room detail GLB import failed')
    selected = {row['id']: row for row in manifest['objects']}
    imported, added = {}, []
    for actor in actors.get_all_level_actors():
        if actor.get_path_name() in before:
            continue
        added.append(actor.get_path_name())
        actor.set_editor_property('tags', [*actor.tags, u.Name(TAG)])
        actor.set_folder_path('Brezi/Realism/RoomDetails')
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh')
            require(mesh is not None, 'Room detail imported without a mesh')
            names = set(re.findall(r'RD_(?:WASHER|DRYER)_(?:BODY|CONTROLS|SELECTOR|DOOR_RIM|DOOR_GLASS|DOOR_HANDLE)|RD_BOY_LAMP_(?:BASE|GLOBE)|RD_SINK_CORNER_[1-4]', actor.get_actor_label() + ' ' + mesh.get_name()))
            require(len(names) == 1, 'Ambiguous imported room detail identity')
            id_ = names.pop()
            require(id_ not in imported and id_ in selected, 'Duplicate/unknown imported room detail')
            record = selected[id_]
            require(c.get_num_materials() == len(record['materialBindings']), 'Imported room detail material slot count differs')
            for index, binding in enumerate(record['materialBindings']):
                material = sources[binding['sourceId']][1].get_material(binding['sourceSlot'])
                require(material is not None, 'Room detail source material missing')
                c.set_material(index, material)
            c.set_mobility(u.ComponentMobility.MOVABLE if record['motionSourceId'] else u.ComponentMobility.STATIC)
            c.set_collision_profile_name('NoCollision')
            c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            c.set_editor_property('can_ever_affect_navigation', False)
            c.set_editor_property('generate_overlap_events', False)
            c.set_editor_property('cast_shadow', True)
            c.set_render_in_main_pass(True)
            c.set_render_in_depth_pass(True)
            actor.set_actor_label(id_)
            parent_path = None
            if record['motionSourceId']:
                parent = sources[record['motionSourceId']][1]
                require(actor.root_component == c, 'Moving visual must be the separate actor root')
                require(actor.attach_to_component(parent, u.Name('None'), u.AttachmentRule.KEEP_WORLD,
                        u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False), 'Cannot attach room visual to moving source')
                parent_path = parent.get_path_name()
            u.EditorAssetLibrary.set_metadata_tag(mesh, 'BreziGeneratedBy', OWNER)
            u.EditorAssetLibrary.set_metadata_tag(mesh, 'BreziRoomDetailSourceIds', json.dumps(record['sourceIds']))
            require(u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False), 'Cannot save room detail mesh')
            imported[id_] = {'actor': actor.get_path_name(), 'component': c.get_path_name(), 'mesh': mesh.get_path_name(),
                             'sourceIds': record['sourceIds'], 'motionSourceId': record['motionSourceId'], 'attachParent': parent_path, 'materials': [c.get_material(i).get_path_name() for i in range(c.get_num_materials())]}
    require(set(imported) == set(selected), 'Room detail imported membership differs')
    changes = []
    for id_, (actor, c) in sorted(sources.items()):
        if id_ not in HIDDEN_IDS:
            continue
        previous = {'visible': bool(c.get_editor_property('visible')), 'hiddenInGame': bool(c.get_editor_property('hidden_in_game')),
                    'renderFlags': {name: bool(c.get_editor_property(name)) for name in RENDER_FLAGS},
                    'passFlags': {name: bool(c.get_editor_property(name)) for name in PASS_FLAGS}}
        c.set_visibility(id_ in MOTION_IDS, False)
        c.set_hidden_in_game(id_ not in MOTION_IDS, False)
        if id_ in MOTION_IDS:
            c.set_render_in_main_pass(False)
            c.set_render_in_depth_pass(False)
        for name in RENDER_FLAGS:
            c.set_editor_property(name, False)
        changes.append({'sourceId': id_, 'actor': actor.get_path_name(), 'component': c.get_path_name(), 'before': previous,
                        'after': {'visible': id_ in MOTION_IDS, 'hiddenInGame': id_ not in MOTION_IDS,
                                  'renderFlags': {name: False for name in RENDER_FLAGS},
                                  'passFlags': {name: False for name in PASS_FLAGS} if id_ in MOTION_IDS else previous['passFlags']}})
    for p in pipelines:
        require(u.EditorAssetLibrary.save_loaded_asset(p, only_if_is_dirty=False), 'Cannot save room detail pipeline')
    require(u.EditorAssetLibrary.save_directory(PREFIX, only_if_is_dirty=True, recursive=True), 'Cannot save room detail asset namespace')
    return {'objects': imported, 'sourceRenderChanges': changes, 'addedActors': added}


def component_index(u, actors):
    return {c.get_path_name(): c for a in actors.get_all_level_actors() for c in a.get_components_by_class(u.SceneComponent)}


def verify_geometry(u, actors, manifest, changes):
    readback = helper.verify_geometry(u, actors, manifest, changes)
    components = component_index(u, actors)
    for row in readback:
        record = changes['objects'][row['id']]
        c = components[record['component']]
        parent = c.get_attach_parent()
        parent_path = parent.get_path_name() if parent else None
        moving = bool(record['motionSourceId'])
        require(all(c.get_editor_property(name) for name in PASS_FLAGS), 'New room visual render passes disabled')
        require(c.get_editor_property('mobility') == (u.ComponentMobility.MOVABLE if moving else u.ComponentMobility.STATIC), 'Saved room visual mobility differs')
        if moving:
            require(parent_path == record['attachParent'], 'Saved room motion parent differs')
            require(parent.is_visible() and not parent.get_editor_property('hidden_in_game'), 'Moving original visibility violates native door contract')
            require(len(parent.get_owner().get_components_by_class(u.StaticMeshComponent)) == 1, 'Original native door acquired a component')
            require(not any(parent.get_editor_property(name) for name in PASS_FLAGS), 'Original door render passes still enabled')
            binding = manifest['motionBindings'][record['motionSourceId']]
            require(parent.component_has_tag(u.Name(binding['runtimeTag'])) and parent.get_owner().actor_has_tag('BreziDoorId=' + binding['doorId']), 'Native door tags differ')
            require((parent.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION) == binding['collision'], 'Native door collision differs')
            bounds = capture_bounds(u, parent)
            require(max(abs(bounds[k][i] - binding['closedBoundsCm'][k][i]) for k in ('min','max') for i in range(3)) < .05, 'Native parent closed bounds differ')
        row.update(motionSourceId=record['motionSourceId'], attachParent=parent_path,
                   mobility='Movable' if moving else 'Static', sourceDoorContractVerified=moving)
    return readback


def pose_transform(u, values):
    require(len(values) == 16 and all(math.isfinite(v) for v in values), 'Invalid door pose')
    # Door motion is a rigid rotation around world Z, serialized column-major.
    yaw = math.atan2(values[1], values[0])
    c, s = math.cos(yaw), math.sin(yaw)
    expected = [c,s,0,0,-s,c,0,0,0,0,1,0,*values[12:15],1]
    require(max(abs(a-b) for a,b in zip(values,expected)) < 1e-5, 'Unsupported non-planar door pose')
    result = u.Transform()
    result.translation = u.Vector(*values[12:15])
    result.rotation = u.Quat(0, 0, math.sin(yaw/2), math.cos(yaw/2))
    result.scale3d = u.Vector(1, 1, 1)
    return result


def motion_audit(u, actors, doors, manifest, changes):
    components = component_index(u, actors)
    members = {r['sourceObjectId']: r for d in doors['doors'] for r in d['members']}
    source_changes = {r['sourceId']: r for r in changes['sourceRenderChanges']}
    samples = [(value, min(range(len(doors['progressSamples'])), key=lambda i: abs(doors['progressSamples'][i]-value))) for value in (0,.5,1)]
    basis = [u.Vector(*point) for point in ((0,0,0),(10,0,0),(0,10,0),(0,0,10))]
    rows = []
    for id_, record in sorted(changes['objects'].items()):
        source_id = record['motionSourceId']
        if not source_id:
            continue
        visual = components[record['component']]
        parent = components[source_changes[source_id]['component']]
        parent_rest, visual_rest = parent.get_world_transform(), visual.get_world_transform()
        member = members[source_id]
        sample_rows = []
        try:
            for progress, index in samples:
                # Door leaf and handle motion have identical samples for these six selected members.
                require(member['poses'][index] == member['handlePoses'][index], 'Unexpected independent handle motion')
                delta = pose_transform(u, member['poses'][index])
                parent.set_world_transform(u.MathLibrary.compose_transforms(parent_rest, delta), False, True)
                actual = visual.get_world_transform()
                error = 0.0
                expected_points, actual_points = [], []
                for point in basis:
                    expected = u.MathLibrary.transform_location(delta, u.MathLibrary.transform_location(visual_rest, point))
                    observed = u.MathLibrary.transform_location(actual, point)
                    expected_points.append([float(expected.x), float(expected.y), float(expected.z)])
                    actual_points.append([float(observed.x), float(observed.y), float(observed.z)])
                    error = max(error, math.sqrt(sum((expected_points[-1][i]-actual_points[-1][i])**2 for i in range(3))))
                require(error < .005, 'Door overlay did not follow native parent: ' + id_)
                require(visual.is_visible() and not visual.get_editor_property('hidden_in_game'), 'Door overlay hidden by parent')
                sample_rows.append({'progress': progress, 'sampleIndex': index, 'maxBasisErrorCm': error, 'expectedBasisPointsCm': expected_points, 'actualBasisPointsCm': actual_points})
        finally:
            parent.set_world_transform(parent_rest, False, True)
        rows.append({'id': id_, 'sourceId': source_id, 'doorId': manifest['motionBindings'][source_id]['doorId'],
                     'parent': parent.get_path_name(), 'samples': sample_rows, 'closedPoseRestored': True})
    require(sorted(row['sourceId'] for row in rows) == MOTION_IDS, 'Missing motion audit members')
    return rows


def restore(output):
    output = Path(output).resolve()
    report = read(output / 'realism-room-details-report.json')
    require(report['status'] == 'failed', 'No failed room detail attempt')
    base = module('fixture_restore_paths', 'performance-optimize.py')
    source, output = base.checked_paths(report['sourceOutput'], output)
    require(report['output'] == str(output), 'Failed room detail report belongs elsewhere')
    try:
        os.kill(report['nativeProcessId'], 0)
    except ProcessLookupError:
        pass
    else:
        raise RuntimeError('Native room detail process is still running')
    content = output / 'Project/BreziTwin/Content'
    current = inventory(content)
    require(current == report['failedContentHashes'], 'Room detail Content drift after failure')
    before = report['beforeAssetHashes']
    validate_changes(before, current, content)
    backup = output / 'realism-room-details-checkpoint/Brezi.umap'
    require(sha(backup) == before[str(content / MAP_FILE)], 'Room detail map backup drift')
    require(read(output / 'performance-source.json')['content'] == before, 'Inherited room detail source drift')
    donor = source / 'Project/BreziTwin/Content'
    require(inventory(donor) == {str(donor / Path(p).relative_to(content)): value for p, value in before.items()}, 'Room detail donor changed')
    history = output / 'realism-room-details-history' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    history.mkdir(parents=True)
    shutil.copy2(content / MAP_FILE, history / 'failed-Brezi.umap')
    shutil.copy2(backup, content / MAP_FILE)
    for path in current.keys() - before.keys():
        target = history / 'failed-assets' / Path(path).relative_to(content)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(path, str(target))
    require(inventory(content) == before, 'Room detail restoration not exact')
    for name in ['realism-room-details-report.json', 'realism-room-details-process.json', 'realism-room-details.log', 'realism-room-details.log.json', 'realism-room-details-checkpoint']:
        path = output / name
        if path.exists():
            shutil.move(str(path), str(history / name))
    write(history / 'restoration.json', {'status': 'room-detail-failure-restored', 'generatedAt': now(), 'contentHashes': before})
    print(json.dumps({'status': 'room-detail-failure-restored', 'history': str(history)}))


def main():
    import unreal as u
    base = module('fixture_geometry_witness', 'performance-optimize.py')
    require(all(os.environ.get(k) for k in ('BREZI_MODEL_OUTPUT', 'BREZI_PERFORMANCE_SOURCE', 'BREZI_ROOM_DETAILS_OUTPUT')), 'Explicit inherited project and room detail artifact required')
    source, output = base.checked_paths(ROOT / os.environ['BREZI_PERFORMANCE_SOURCE'], ROOT / os.environ['BREZI_MODEL_OUTPUT'])
    artifact = (ROOT / os.environ['BREZI_ROOM_DETAILS_OUTPUT']).resolve()
    require(artifact.is_relative_to(ROOT / 'output/unreal') and not artifact.is_relative_to(output), 'Room detail artifact must be separate from target project')
    project = output / 'Project/BreziTwin'
    require(Path(u.Paths.project_dir()).resolve() == project, 'Wrong native room detail project')
    content = project / 'Content'
    before = inventory(content)
    provenance = read(output / 'performance-source.json')
    require(provenance['status'] == 'verified-scene-inherited' and provenance['donor'] == str(source) and provenance['content'] == before, 'Unverified room detail inheritance')
    require(not any((output / name).exists() for name in ('realism-room-details-report.json', 'realism-fixtures-report.json', 'realism-import-report.json', 'performance-scene-report.json', 'nanite-study-report.json')), 'Room detail pass requires a fresh inherited output')
    donor = source / 'Project/BreziTwin/Content'
    source_before = inventory(donor)
    require({str(content / Path(p).relative_to(donor)): value for p, value in source_before.items()} == before, 'Room detail donor Content differs')
    manifest = read(artifact / 'geometry-report.json')
    geometry = output / 'geometry'
    scene = read(geometry / 'scene.json')
    doors = read(geometry / 'doors.json')
    validate_manifest(manifest, scene, doors)
    require(manifest['sourceSceneSha256'] == sha(geometry / 'scene.json') and manifest['sourceObjSha256'] == sha(geometry / 'dom-mm.obj')
            and manifest['sourceDoorsSha256'] == sha(geometry / 'doors.json') and manifest['glbSha256'] == sha(artifact / 'realism-room-details.glb'), 'Room detail geometry input pins differ')
    generator = ROOT / 'scripts/unreal/realism-room-details-geometry.py'
    require(manifest['generatorSha256'] == sha(generator), 'Room detail generator changed after export')
    require(manifest['generatorDependencies'] == {'scripts/unreal/realism-fixtures-geometry.py': sha(ROOT / 'scripts/unreal/realism-fixtures-geometry.py')}, 'Room generator helper changed')
    folder = output / 'realism-room-details-checkpoint'
    folder.mkdir(exist_ok=False)
    shutil.copy2(content / MAP_FILE, folder / 'Brezi.umap')
    pipeline = {str(ROOT / 'scripts/unreal' / name): sha(ROOT / 'scripts/unreal' / name)
                for name in ('realism-room-details-import.py', 'realism-room-details-geometry.py', 'realism-fixtures-import.py', 'realism-fixtures-geometry.py', 'performance-optimize.py', 'performance_scene_policy.py')}
    inputs = {str(p): sha(p) for p in [*sorted(geometry.rglob('*')), artifact / 'geometry-report.json', artifact / 'realism-room-details.glb'] if p.is_file()}
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'pending', 'startedAt': now(), 'project': str(project),
              'output': str(output), 'sourceOutput': str(source), 'nativeProcessId': os.getpid(), 'artifact': str(artifact),
              'manifestSha256': sha(artifact / 'geometry-report.json'), 'sourceIds': SOURCE_IDS, 'hiddenSourceIds': HIDDEN_IDS, 'beforeAssetHashes': before,
              'inputFiles': inputs, 'pipelineFiles': pipeline, 'renderedVerified': False,
              'movingSourceRenderPolicy': {'visible': True, 'hiddenInGame': False, 'render_in_main_pass': False, 'render_in_depth_pass': False}}
    write(output / 'realism-room-details-report.json', report)
    try:
        actors = u.get_editor_subsystem(u.EditorActorSubsystem)
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(levels.load_level(MAP), 'Cannot load room detail baseline map')
        original = witness(base, u, actors)
        changes = apply_geometry(u, actors, levels, manifest, artifact)
        report.update(changes)
        expected = expected_witness(original, changes['sourceRenderChanges'])
        authored = witness(base, u, actors)
        verify_witness(expected, authored, changes['addedActors'])
        verify_geometry(u, actors, manifest, changes)
        require(levels.save_current_level(), 'Cannot save room detail map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False), 'Cannot unload room detail map')
        require(levels.load_level(MAP), 'Cannot reload room detail map')
        reloaded = witness(base, u, actors)
        verify_witness(expected, reloaded, changes['addedActors'])
        require(authored == reloaded, 'Saved room detail actor witness differs')
        readback = verify_geometry(u, actors, manifest, changes)
        report['parentMotionAudit'] = motion_audit(u, actors, doors, manifest, changes)
        require(witness(base, u, actors) == reloaded, 'Native motion probe failed to restore exact closed scene')
        after = inventory(content)
        validate_changes(before, after, content)
        require(source_before == inventory(donor), 'Historical room detail donor Content changed')
        for path, value in {**report['pipelineFiles'], **report['inputFiles']}.items():
            require(sha(path) == value, 'Room detail authoring input changed during native import')
        report.update(status='realism-room-details-validated', savedReloaded=True, protectedContentUnchanged=True,
                      sourceGeometryCollisionAndTransformsPreserved=True, originalMaterialAssetsPreserved=True, originalMaterialBindingsPreserved=True, parentMotionVerified=True,
                      originalActorCount=len(original), finalActorCount=len(reloaded),
                      protectedActorWitnessSha256=digest(expected), savedProtectedActorWitnessSha256=digest({p: reloaded[p] for p in expected}),
                      authoredActorWitnessSha256=digest(authored), savedActorWitnessSha256=digest(reloaded),
                      savedGeometryReadback=readback, maxNativeBoundsErrorCm=max(row['maxErrorCm'] for row in readback),
                      afterAssetHashes=after, newAssets=sorted(after.keys() - before.keys()),
                      changedAssets=[{'path': p, 'beforeSha256': before[p], 'afterSha256': after[p]} for p in before if before[p] != after[p]])
        u.log('BREZI_REALISM_ROOM_DETAILS validated')
    except Exception as error:
        report.update(status='failed', error=str(error), failedContentHashes=inventory(content))
        raise
    finally:
        report['generatedAt'] = now()
        write(output / 'realism-room-details-report.json', report)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--restore':
        restore(sys.argv[2])
    else:
        main()
