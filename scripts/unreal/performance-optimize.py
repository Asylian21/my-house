"""Map-only rendering migration of an exact isolated Content clone.

Run in the cloned Editor project, with BREZI_MODEL_OUTPUT and
BREZI_PERFORMANCE_SOURCE set to distinct output/unreal directories. No source
mesh, material, collision, transform or instance is edited. The saved map is
reopened and its observable geometry/lighting contract compared before success.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/unreal'))
from performance_scene_policy import LUMEN_DEFAULTS, apply_detail, detail_policy, read_detail_flag, verify_detail

MAP = '/Game/Brezi/Maps/Brezi'
MAP_FILE = 'Brezi/Maps/Brezi.umap'
OWNER = 'scripts/unreal/performance-optimize.py'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def inventory(content):
    return {str(p.relative_to(content)): sha(p) for p in sorted(content.rglob('*')) if p.is_file()}


def validate_changes(before, after):
    require(before.keys() == after.keys(), 'Content file inventory changed')
    for path, value in before.items():
        require(path == MAP_FILE or after[path] == value, 'Protected content changed: '+path)


def checked_paths(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    parent = ROOT/'output/unreal'
    require(source.is_relative_to(parent) and output.is_relative_to(parent)
            and source != parent and output != parent, 'Output/source outside output/unreal')
    require(source != output and not source.is_relative_to(output)
            and not output.is_relative_to(source), 'Source and output must be independent')
    require(not (output/'model-package.json').exists(), 'Refuse to mutate a packaged historical output')
    pointer = parent/'model-refresh-current.json'
    if pointer.is_file():
        current = read(pointer)
        # The active-pointer schema has used output/profileRoot/modelOutput.
        for key in ('output', 'profileRoot', 'modelOutput'):
            if isinstance(current.get(key), str):
                require((ROOT/current[key]).resolve() != output, 'Refuse to mutate the active package')
    return source, output


def vec(value, axes='xyz'):
    return [float(getattr(value, key)) for key in axes]


def transform(value):
    return [vec(value.translation), vec(value.rotation, 'xyzw'), vec(value.scale3d)]


def instance_value(component, index):
    value = component.get_instance_transform(index, False)
    if isinstance(value, tuple) and len(value) == 2 and value[0] is True:
        value = value[1]
    require(value is not None and hasattr(value, 'translation'), 'Missing instance transform')
    return transform(value)


def light_witness(component):
    # Unreal struct repr includes its native memory address, which changes after
    # a legitimate unload/reload. Compare every protected light value directly.
    color = component.get_editor_property('light_color')
    return {'intensity': float(component.get_editor_property('intensity')),
            'light_color': [int(getattr(color, channel)) for channel in 'rgba'],
            'temperature': float(component.get_editor_property('temperature')),
            'cast_shadows': bool(component.get_editor_property('cast_shadows')),
            'mobility': str(component.get_editor_property('mobility'))}


def witness(u, actors):
    rows = {}
    for actor in actors.get_all_level_actors():
        components = []
        for c in actor.get_components_by_class(u.SceneComponent):
            row = {'name': c.get_name(), 'class': c.get_class().get_path_name(),
                   'transform': transform(c.get_world_transform()),
                   'tags': sorted(map(str, c.get_editor_property('component_tags'))),
                   'visible': bool(c.get_editor_property('visible')),
                   'hiddenInGame': bool(c.get_editor_property('hidden_in_game'))}
            if isinstance(c, u.PrimitiveComponent):
                row.update(collision=str(c.get_collision_enabled()),
                           collisionProfile=str(c.get_collision_profile_name()),
                           pawnResponse=str(c.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN)),
                           navigation=bool(c.get_editor_property('can_ever_affect_navigation')))
            if isinstance(c, u.StaticMeshComponent):
                mesh = c.get_editor_property('static_mesh')
                row.update(mesh=mesh.get_path_name() if mesh else None,
                           materials=[c.get_material(i).get_path_name() if c.get_material(i) else None
                                      for i in range(c.get_num_materials())])
            if isinstance(c, u.InstancedStaticMeshComponent):
                count = c.get_instance_count()
                row.update(instanceCount=count,
                           orderedInstanceTransformsSha256=digest([instance_value(c, i) for i in range(count)]))
            if isinstance(c, u.LightComponent):
                row.update(light=light_witness(c))
            components.append(row)
        rows[actor.get_path_name()] = {
            'class': actor.get_class().get_path_name(), 'label': actor.get_actor_label(),
            'transform': transform(actor.get_actor_transform()),
            'tags': sorted(map(str, actor.get_editor_property('tags'))),
            'hidden': bool(actor.get_editor_property('hidden')),
            'components': sorted(components, key=lambda c: c['name'])}
    return rows


def update_map(u, actors):
    volumes = [a for a in actors.get_all_level_actors()
               if isinstance(a, u.PostProcessVolume) and a.get_editor_property('unbound')]
    require(len(volumes) == 1, 'Expected exactly one unbound post-process volume')
    volume = volumes[0]
    settings = volume.get_editor_property('settings')
    previous = {name: {'value': settings.get_editor_property(name),
                      'override': bool(settings.get_editor_property('override_'+name))}
                for name in LUMEN_DEFAULTS}
    for name, value in LUMEN_DEFAULTS.items():
        settings.set_editor_property('override_'+name, True)
        settings.set_editor_property(name, value)
    volume.set_editor_property('settings', settings)
    details = []
    for actor in actors.get_all_level_actors():
        policy = detail_policy(map(str, actor.get_editor_property('tags')), actor.get_actor_label())
        if policy is None:
            continue
        c = actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(c and c.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION,
                'Detail must be an existing collisionless HISM: '+actor.get_path_name())
        require(not any(str(t).startswith('DOM_') for t in actor.get_editor_property('tags')),
                'Detail must not replace a source actor')
        before = {name: read_detail_flag(c, name) for name in policy['flags']}
        before['cullCm'] = [int(c.get_editor_property(name)) for name in
                            ('instance_start_cull_distance', 'instance_end_cull_distance')]
        apply_detail(c, policy)
        actor.synchronize_instance_bounds()
        details.append({'actor': actor.get_path_name(), 'instances': c.get_instance_count(),
                        'previous': before, 'policy': policy})
    require(any(row['policy']['kind'] == 'lawn' for row in details), 'No authored lawn found')
    return {'volume': volume.get_path_name(), 'previousLumen': previous,
            'lumen': LUMEN_DEFAULTS, 'details': details}


def verify_map(u, actors, changes):
    by_path = {a.get_path_name(): a for a in actors.get_all_level_actors()}
    settings = by_path[changes['volume']].get_editor_property('settings')
    for name, expected in LUMEN_DEFAULTS.items():
        require(settings.get_editor_property('override_'+name)
                and abs(float(settings.get_editor_property(name))-expected) < 1e-5,
                'Saved Lumen setting differs: '+name)
    readback = []
    for row in changes['details']:
        c = by_path[row['actor']].get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(c.get_instance_count() == row['instances'], 'Detail instance count changed')
        verify_detail(c, row['policy'])
        readback.append({'actor': row['actor'], 'instances': c.get_instance_count(),
                         'flags': {name: read_detail_flag(c, name) for name in row['policy']['flags']},
                         'cullCm': [int(c.get_editor_property(name)) for name in
                                    ('instance_start_cull_distance', 'instance_end_cull_distance')]})
    return readback


def main():
    import unreal as u
    require(os.environ.get('BREZI_MODEL_OUTPUT') and os.environ.get('BREZI_PERFORMANCE_SOURCE'),
            'Explicit BREZI_MODEL_OUTPUT and BREZI_PERFORMANCE_SOURCE required')
    source, output = checked_paths(ROOT/os.environ['BREZI_PERFORMANCE_SOURCE'], ROOT/os.environ['BREZI_MODEL_OUTPUT'])
    project = output/'Project/BreziTwin'
    require(Path(u.Paths.project_dir()).resolve() == project, 'Wrong native project')
    content = project/'Content'
    source_content = source/'Project/BreziTwin/Content'
    before = inventory(content)
    require(MAP_FILE in before and before == inventory(source_content), 'Content must be an exact source clone')
    folder = output/'performance-checkpoint'
    require(not (output/'performance-scene-report.json').exists(), 'Use a fresh output; report already exists')
    folder.mkdir(exist_ok=False)
    shutil.copy2(content/MAP_FILE, folder/'Brezi.umap')
    pins = {str(p.resolve()): sha(p) for p in (Path(__file__), ROOT/'scripts/unreal/performance_scene_policy.py')}
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'pending',
              'sourceOutput': str(source.relative_to(ROOT)), 'output': str(output.relative_to(ROOT)),
              'nativeProcessId': os.getpid(), 'pipelineFiles': pins,
              'baselineContentHashes': before,
              'beforeAssetHashes': {str(content/name): value for name, value in before.items()},
              'renderedVerified': False, 'performanceAccepted': False}
    write(output/'performance-scene-report.json', report)
    try:
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        actors = u.get_editor_subsystem(u.EditorActorSubsystem)
        require(levels.load_level(MAP), 'Cannot load cloned map')
        original = witness(u, actors)
        report['changes'] = update_map(u, actors)
        require(witness(u, actors) == original, 'In-memory geometry/light witness changed')
        require(levels.save_current_level(), 'Cannot save optimized map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False), 'Cannot unload optimized map')
        require(levels.load_level(MAP), 'Cannot reload optimized map')
        reloaded = witness(u, actors)
        require(reloaded == original, 'Saved geometry/light witness changed')
        readback = verify_map(u, actors, report['changes'])
        after = inventory(content)
        validate_changes(before, after)
        require(before == inventory(source_content), 'Historical source content changed')
        for name, value in pins.items():
            require(sha(ROOT/name) == value, 'Migration script changed while running')
        report.update(status='performance-scene-validated', savedReloaded=True,
                      protectedContentUnchanged=True, actorCount=len(original),
                      actorCountBefore=len(original), actorCountAfter=len(reloaded),
                      actorGeometryLightingWitnessSha256=digest(original),
                      savedActorGeometryLightingWitnessSha256=digest(reloaded),
                      savedDetailReadback=readback,
                      finalContentHashes=after,
                      afterAssetHashes={str(content/name): value for name, value in after.items()},
                      changedAssets=[{'path': name, 'beforeSha256': before[name], 'afterSha256': after[name]}
                                     for name in before if before[name] != after[name]],
                      sourceTransformsMaterialsCollisionAndInstancesPreserved=True,
                      limitations=['Native screenshot and frame/GPU measurements remain separate acceptance gates.',
                                   'No mesh merging, Nanite conversion, skylight or luminaire mutation.'])
        u.log('BREZI_PERFORMANCE_SCENE validated')
    except Exception as error:
        report.update(status='failed', error=str(error), failedContentHashes=inventory(content))
        raise
    finally:
        report['generatedAt'] = datetime.now(timezone.utc).isoformat()
        write(output/'performance-scene-report.json', report)


if __name__ == '__main__':
    main()
