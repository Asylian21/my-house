"""Additive realism authoring over a verified, isolated inherited scene.

The saved map and new /Game/Brezi/Realism packages are the only writable
Content. Original geometry, collision, instances and asset bytes stay intact.
Run through model-refresh.mjs realism; this script never edits a donor.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/unreal'))
MAP = '/Game/Brezi/Maps/Brezi'
MAP_FILE = 'Brezi/Maps/Brezi.umap'
PREFIX = '/Game/Brezi/Realism/'
TAG = 'BreziRealism20260926'
OWNER = 'scripts/unreal/realism-import.py'


def require(value, message):
    if not value:
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
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def inventory(content):
    result = {}
    for path in sorted(content.rglob('*')):
        require(not path.is_symlink(), 'Content symlink is not supported: ' + str(path))
        if path.is_file():
            result[str(path.resolve())] = sha(path)
    return result


def validate_changes(before, after, content):
    content = Path(content).resolve()
    map_file = str(content / MAP_FILE)
    require(before.keys() <= after.keys(), 'Removed original Content file')
    for name, value in before.items():
        require(name == map_file or after[name] == value, 'Protected Content changed: ' + name)
    for name in after.keys() - before.keys():
        require(Path(name).is_relative_to(content / 'Brezi/Realism'), 'New asset outside realism namespace: ' + name)
        require(Path(name).suffix in ('.uasset', '.uexp', '.ubulk'), 'Unexpected new Content file: ' + name)


def restore(output):
    """Restore only a recorded failed native attempt, preserving its history."""
    output = Path(output).resolve()
    geometry = module('realism_restore_bounds', 'performance-optimize.py')
    report_file = output / 'realism-import-report.json'
    report = read(report_file)
    require(report.get('status') == 'failed', 'No recorded failed realism authoring')
    source, output = geometry.checked_paths(report['sourceOutput'], output)
    require(report['output'] == str(output) and report['project'] == str(output / 'Project/BreziTwin'), 'Failed report belongs to another output')
    try:
        os.kill(report['nativeProcessId'], 0)
    except ProcessLookupError:
        pass
    else:
        raise RuntimeError('Native authoring process is still running')
    content = output / 'Project/BreziTwin/Content'
    current = inventory(content)
    require(current == report['failedContentHashes'], 'Content changed after the recorded failure')
    before = report['beforeAssetHashes']
    validate_changes(before, current, content)
    backup = output / 'realism-checkpoint/Brezi.umap'
    require(sha(backup) == before[str(content / MAP_FILE)], 'Checkpoint map differs from original')
    require(read(output / 'performance-source.json')['content'] == before, 'Inherited source provenance changed')
    source_files = {str(source / 'Project/BreziTwin/Content' / Path(p).relative_to(content)): h for p, h in before.items()}
    require(inventory(source / 'Project/BreziTwin/Content') == source_files, 'Donor Content changed since the attempt')
    # Every guard above precedes mutation. Preserve both failed and restored maps.
    history = output / 'realism-history' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    history.mkdir(parents=True)
    shutil.copy2(content / MAP_FILE, history / 'failed-Brezi.umap')
    shutil.copy2(backup, content / MAP_FILE)
    removed = []
    for path in sorted(current.keys() - before.keys()):
        target = Path(path)
        archived = history / 'failed-assets' / target.relative_to(content)
        archived.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target), str(archived))
        removed.append(path)
    require(inventory(content) == before, 'Restoration did not produce exact inherited Content')
    for name in ['realism-import-report.json', 'realism-import-process.json', 'realism-import.log', 'realism-import.log.json', 'realism-checkpoint']:
        path = output / name
        if path.exists():
            shutil.move(str(path), str(history / name))
    write(history / 'restoration.json', {'status': 'failed-realism-restored-to-inherited-scene', 'generatedAt': now(),
          'removedOwnedFiles': removed, 'restoredContentHashes': before, 'donor': str(source)})
    print(json.dumps({'status': 'failed-realism-restored-to-inherited-scene', 'history': str(history)}))


def protected_witness(geometry, u, actors):
    rows = geometry.witness(u, actors)
    for actor in actors.get_all_level_actors():
        components = {c.get_name(): c for c in actor.get_components_by_class(u.SceneComponent)}
        for row in rows[actor.get_path_name()]['components']:
            row['path'] = components[row['name']].get_path_name()
    return rows


def expected_witness(before, changes):
    expected = copy.deepcopy(before)
    seen = set()
    for row in changes:
        identity = (row['actor'], row['component'], row['slot'])
        require(identity not in seen, 'Duplicate material binding change')
        seen.add(identity)
        require(row['actor'] in expected, 'Material change targets an absent original actor')
        components = [c for c in expected[row['actor']]['components'] if c['path'] == row['component']]
        require(len(components) == 1 and 'materials' in components[0], 'Unknown mesh component in material delta')
        materials = components[0]['materials']
        slot = row['slot']
        require(type(slot) is int and 0 <= slot < len(materials), 'Material slot outside original component')
        require(materials[slot] == row['before'], 'Material delta does not match original binding')
        require(isinstance(row['after'], str) and row['after'].startswith(PREFIX), 'Replacement material outside realism namespace')
        materials[slot] = row['after']
    return expected


def verify_witness(expected, actual, added):
    require(len(added) == len(set(added)), 'Duplicate added actor')
    require(set(actual) == set(expected) | set(added), 'Unreported actor addition/removal')
    require(not set(expected) & set(added), 'Added actor overwrites an original actor')
    for name, row in expected.items():
        require(actual[name] == row, 'Protected actor geometry/collision/instance witness changed: ' + name)
    for name in added:
        row = actual[name]
        require(TAG in row['tags'] and not any(t.startswith('DOM_') for t in row['tags']), 'New actor is not owned: ' + name)
        for component in row['components']:
            if 'collision' in component:
                require(component['collision'].endswith('NO_COLLISION: 0>') or 'NO_COLLISION' in component['collision'],
                        'Added environment actor has collision: ' + name)
                require(component['navigation'] is False, 'Added environment actor affects navigation: ' + name)


def main():
    import unreal as u
    geometry = module('realism_geometry_witness', 'performance-optimize.py')
    require(os.environ.get('BREZI_MODEL_OUTPUT') and os.environ.get('BREZI_PERFORMANCE_SOURCE'), 'Explicit isolated output and donor required')
    source, output = geometry.checked_paths(ROOT / os.environ['BREZI_PERFORMANCE_SOURCE'], ROOT / os.environ['BREZI_MODEL_OUTPUT'])
    project = output / 'Project/BreziTwin'
    require(Path(u.Paths.project_dir()).resolve() == project, 'Wrong native project')
    source_record = read(output / 'performance-source.json')
    require(source_record['status'] == 'verified-scene-inherited' and Path(source_record['donor']) == source, 'Unverified inherited source')
    require(not (output / 'realism-import-report.json').exists(), 'Use a fresh output; realism report already exists')
    require(not (output / 'performance-scene-report.json').exists() and not (output / 'nanite-study-report.json').exists(),
            'Realism authoring requires the exact inherited donor scene')
    content = project / 'Content'
    before = inventory(content)
    source_before = inventory(source / 'Project/BreziTwin/Content')
    require(before == source_record['content'], 'Inherited Content changed before realism authoring')
    require({str(content / Path(p).relative_to(source / 'Project/BreziTwin/Content')): h for p, h in source_before.items()} == before,
            'Donor and destination Content differ')
    folder = output / 'realism-checkpoint'
    folder.mkdir(exist_ok=False)
    shutil.copy2(content / MAP_FILE, folder / 'Brezi.umap')
    files = ['realism-import.py', 'realism-materials.py', 'realism-environment.py', 'performance-optimize.py', 'performance_scene_policy.py']
    pipeline = {str(ROOT / 'scripts/unreal' / name): sha(ROOT / 'scripts/unreal' / name) for name in files}
    inputs = {str(p): sha(p) for p in sorted((output / 'geometry').rglob('*')) if p.is_file()}
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'pending', 'startedAt': now(),
              'project': str(project), 'sourceOutput': str(source), 'output': str(output), 'nativeProcessId': os.getpid(),
              'beforeAssetHashes': before, 'pipelineFiles': pipeline, 'inputFiles': inputs,
              'renderedVerified': False, 'performanceAccepted': False}
    write(output / 'realism-import-report.json', report)
    try:
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        actors = u.get_editor_subsystem(u.EditorActorSubsystem)
        require(levels.load_level(MAP), 'Cannot load inherited map')
        original = protected_witness(geometry, u, actors)
        materials = module('brezi_realism_materials', 'realism-materials.py')
        environment = module('brezi_realism_environment', 'realism-environment.py')
        report['materials'] = materials.apply(u, actors, output)
        report['environment'] = environment.apply(u, actors, output)
        changes = report['materials'].get('bindingChanges', [])
        require(changes, 'Realism stage produced no material changes')
        added = report['environment'].get('addedActors', [])
        expected = expected_witness(original, changes)
        actual = protected_witness(geometry, u, actors)
        verify_witness(expected, actual, added)
        report['materialBindingChanges'] = changes
        report['addedActors'] = added
        report['ownedAssets'] = sorted(set(report['materials'].get('ownedAssets', []) + report['environment'].get('ownedAssets', [])))
        for path in report['ownedAssets']:
            require(path.startswith(PREFIX), 'Declared asset outside owned realism namespace')
            asset = u.EditorAssetLibrary.load_asset(path)
            require(asset is not None, 'Declared owned asset missing: ' + path)
            require(u.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False), 'Cannot save owned asset: ' + path)
        require(levels.save_current_level(), 'Cannot save realism map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False), 'Cannot unload realism map')
        require(levels.load_level(MAP), 'Cannot reload realism map')
        reloaded = protected_witness(geometry, u, actors)
        verify_witness(expected, reloaded, added)
        require(actual == reloaded, 'Saved actor witness differs from the authored scene')
        report['savedMaterialReadback'] = materials.verify(u, actors, report['materials'])
        report['savedEnvironmentReadback'] = environment.verify(u, actors, report['environment'])
        for sub in ('materials', 'environment'):
            for field in ('pipelineFiles', 'inputFiles'):
                for path, value in report[sub].get(field, {}).items():
                    absolute = str((ROOT / path).resolve())
                    require(sha(absolute) == value, 'Authoring input hash changed: ' + absolute)
                    require(absolute not in report[field] or report[field][absolute] == value, 'Conflicting input pin')
                    report[field][absolute] = value
            for path, value in report[sub].get('engineAssetPins', {}).items():
                absolute = str(Path(path).resolve())
                require(sha(absolute) == value, 'Engine asset changed: ' + absolute)
                report['inputFiles'][absolute] = value
        after = inventory(content)
        validate_changes(before, after, content)
        require(source_before == inventory(source / 'Project/BreziTwin/Content'), 'Donor Content changed')
        for field in ('pipelineFiles', 'inputFiles'):
            for path, value in report[field].items():
                require(sha(path) == value, 'Input changed during native authoring: ' + path)
        new_assets = sorted(set(after) - set(before))
        declared_packages = {path.split('.')[0].replace('/Game/', '') + '.uasset' for path in report['ownedAssets']}
        require({str(Path(p).relative_to(content)) for p in new_assets if p.endswith('.uasset')} == declared_packages,
                'Saved new packages do not match declared owned assets')
        report.update(status='realism-import-validated', savedReloaded=True, protectedContentUnchanged=True,
                      sourceTransformsMeshCollisionAndInstancesPreserved=True, originalActorCount=len(original), finalActorCount=len(reloaded),
                      protectedActorWitnessSha256=digest(expected), savedProtectedActorWitnessSha256=digest({k: reloaded[k] for k in expected}),
                      authoredActorWitnessSha256=digest(actual), savedActorWitnessSha256=digest(reloaded),
                      afterAssetHashes=after, newAssets=new_assets,
                      changedAssets=[{'path': p, 'beforeSha256': before[p], 'afterSha256': after[p]} for p in before if before[p] != after[p]],
                      limitations=['Material and environment authoring has passed native save/reload; rendered visual quality and performance need separate capture.'])
        u.log('BREZI_REALISM_IMPORT validated')
    except Exception as error:
        report.update(status='failed', error=str(error), failedContentHashes=inventory(content))
        raise
    finally:
        report['generatedAt'] = now()
        write(output / 'realism-import-report.json', report)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--restore':
        restore(sys.argv[2])
    else:
        main()
