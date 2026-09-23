"""Bounded enhancement of an already validated, isolated C/B/B native map.

Native: BREZI_ARCHVIZ_OUTPUT=<profile> UnrealEditor-Cmd ... -script=<this file>
After a caught failure, with the native process stopped:
    python3 -B scripts/unreal/archviz-import.py --restore <profile>
Recovery checks the exact failed disk state, restores only checkpointed map and
finish materials, and removes only new assets in reserved enhancement folders.
The baseline receipt and geometry packages are never rewritten.
"""
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/archviz-import.py'
HELPERS = [OWNER, 'scripts/unreal/archviz-materials.py', 'scripts/unreal/archviz-avatar.py',
           'scripts/unreal/archviz_lighting.py', 'scripts/unreal/archviz-material-inputs.json']
EXTENSIONS = {'.uasset', '.uexp', '.ubulk', '.umap'}
MAP = '/Game/Brezi/Maps/Brezi'


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def now(): return datetime.now(timezone.utc).isoformat()
def relative(path): return str(Path(path).resolve().relative_to(ROOT))


def write(path, data):
    path = Path(path); temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts/unreal' / filename)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def paths(output):
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT / 'output/unreal') and output != ROOT / 'output/unreal',
            'Archviz requires a selected isolated output/unreal profile')
    project = output / 'Project/BreziTwin'
    profile = read(output / 'profile.json')
    require(profile.get('archvizGame') is True and Path(profile['project']).resolve() == project,
            'Selected profile must explicitly declare archvizGame=true and its isolated project')
    require(Path(profile['geometry']).resolve() == output / 'geometry', 'Archviz geometry must belong to this output')
    return output, project, output / 'geometry', project / 'Content/Brezi', output / 'archviz-checkpoint'


def check_pins(pins):
    for name, expected in pins.items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == expected,
                'Archviz pinned input changed: ' + name)


def inventory(content):
    result = {}
    for file in sorted(content.rglob('*')):
        if file.is_file() and file.suffix in EXTENSIONS:
            require(file.resolve().is_relative_to(content.resolve()), 'Native package symlink escapes project')
            result[relative(file)] = sha(file)
    return result


def authorized_new(name, content):
    path = (ROOT / name).resolve()
    return any(path.is_relative_to(content / folder) for folder in ('Avatar/Michelle', 'Archviz/Textures'))


def check_changes(baseline, current, allowed, content):
    require(set(baseline).issubset(current), 'Enhancement deleted a baseline native package')
    for name, expected in baseline.items():
        require(name in allowed or current[name] == expected, 'Protected native package changed: ' + name)
    for name in current.keys() - baseline.keys():
        require(authorized_new(name, content), 'Enhancement created a package outside its reserved namespace: ' + name)


def baseline_inputs(output, project, geometry, baseline):
    pins = {relative(output / 'model-refresh-import-report.json'): sha(output / 'model-refresh-import-report.json'),
            relative(output / 'profile.json'): sha(output / 'profile.json')}
    for path, expected in {
        geometry / 'scene.json': baseline['sourceManifestSha256'],
        geometry / 'brezi-twin.glb': baseline['sourceGlbSha256'],
        geometry / 'walking.json': baseline['walkingSha256'],
        geometry / 'viewpoints.json': baseline['viewpointsSha256'],
        geometry / 'hidden-collision.json': baseline['hiddenCollision']['sourceContractSha256'],
        geometry / 'brezi-collision-only.glb': baseline['hiddenCollision']['sourceGlbSha256'],
        project / 'Content/Data/walking.json': baseline['walkingSha256'],
        project / 'Content/Data/hidden-collision.json': baseline['hiddenCollision']['sourceContractSha256'],
        geometry / 'doors.json': baseline['doors']['contractSha256'],
        project / 'Content/Data/doors.json': baseline['doors']['contractSha256'],
    }.items(): pins[relative(path)] = expected
    pins.update(baseline['pipelineFiles'])
    pins.update(read(geometry / 'scene.json')['sourceFiles'])
    bridge = read(geometry / 'bridge-report.json')
    pins.update(bridge['pipelineFiles']); pins.update(bridge['sourceFiles'])
    for name in ('bridge-report.json', 'validation.json'):
        pins[relative(geometry / name)] = sha(geometry / name)
    for texture in baseline['materials']['textures']: pins[texture['source']] = texture['sha256']
    host = read(output / 'model-import-process.json'); process_file = Path(host['processFile'])
    pins[relative(output / 'model-import-process.json')] = sha(output / 'model-import-process.json')
    pins[relative(process_file)] = host['processFileSha256']
    require(host['reportSha256'] == pins[relative(output / 'model-refresh-import-report.json')],
            'Baseline native process does not bind this exact import receipt')
    check_pins(pins)
    process = read(process_file)
    parse_time = lambda value: datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(process['code'] == 0 and parse_time(process['startedAt']) <= parse_time(baseline['generatedAt']) <= parse_time(process['endedAt']),
            'Baseline import has no successful contemporaneous native process')
    return pins


def checkpoint(output, content, baseline, source_inputs, materials, scene):
    folder = output / 'archviz-checkpoint'; path = folder / 'checkpoint.json'
    current = inventory(content)
    expected = {**baseline['finalAssetHashes'], relative(content / 'Maps/Brezi.umap'): baseline['mapFileSha256']}
    require(current == expected, 'Archviz requires the exact validated baseline native inventory')
    allowed = {relative(content / 'Maps/Brezi.umap')}
    for slot, entry in baseline['materials']['materials'].items():
        if not materials.recipe(scene['materials'][slot]): continue
        package = content.parent / entry['asset'].split('.', 1)[0].removeprefix('/Game/')
        allowed.update(relative(package.with_suffix(ext)) for ext in EXTENSIONS
                       if package.with_suffix(ext).is_file())
    require(not any(authorized_new(name, content) for name in current), 'Enhancement namespace is not empty')
    if path.exists():
        previous = read(path)
        require(previous['status'] == 'restored-baseline' and previous['baselineInventory'] == current
                and previous['inputFiles'] == source_inputs, 'Prior enhancement checkpoint requires explicit verified restore')
        attempt = previous['attempt'] + 1
    else:
        folder.mkdir(); attempt = 1
    backup = folder / 'baseline'; backup.mkdir(exist_ok=True)
    backup_pins = {}
    for name in sorted(allowed):
        source = ROOT / name; target = backup / source.relative_to(content)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists(): require(sha(target) == current[name], 'Checkpoint backup has unexpected bytes')
        else: shutil.copy2(source, target)
        backup_pins[name] = {'path': relative(target), 'sha256': current[name]}
    receipt = output / 'model-refresh-import-report.json'; saved = folder / 'baseline-import-report.json'
    if saved.exists(): require(saved.read_bytes() == receipt.read_bytes(), 'Checkpoint baseline receipt differs')
    else: shutil.copy2(receipt, saved)
    result = {'schemaVersion': 1, 'owner': OWNER, 'status': 'in-progress', 'attempt': attempt,
              'startedAt': now(), 'nativeProcessId': os.getpid(), 'output': relative(output), 'inputFiles': source_inputs,
              'baselineInventory': current, 'allowedModifiedPackages': sorted(allowed), 'backups': backup_pins,
              'baselineReportSha256': sha(receipt)}
    write(path, result); return result


def restore(output):
    output, project, geometry, content, folder = paths(output)
    state = read(folder / 'checkpoint.json')
    require(state.get('owner') == OWNER and state.get('status') == 'failed-recoverable'
            and state['output'] == relative(output), 'No caught, recoverable enhancement failure for this profile')
    try:
        os.kill(state['nativeProcessId'], 0)
    except ProcessLookupError:
        pass
    else:
        raise RuntimeError('Recorded native process is still running; wait for it to exit before restoring')
    check_pins(state['inputFiles'])
    current = inventory(content)
    require(current == state['failedInventory'], 'Native packages changed after recorded failure; refuse restore')
    check_changes(state['baselineInventory'], current, state['allowedModifiedPackages'], content)
    for name, entry in state['backups'].items():
        require(name in state['allowedModifiedPackages'] and (ROOT / name).resolve().is_relative_to(content),
                'Checkpoint restore destination is outside authorized packages')
        source = (ROOT / entry['path']).resolve()
        require(source.is_relative_to(folder / 'baseline') and sha(source) == state['baselineInventory'][name]
                and entry['sha256'] == state['baselineInventory'][name], 'Checkpoint backup identity differs')
    # Only run in ordinary Python after the commandlet has ended: loading live
    # packages while replacing their on-disk bytes is deliberately unsupported.
    require('unreal' not in sys.modules, 'Recovery must run outside the native editor process')
    for name in current.keys() - state['baselineInventory'].keys():
        require(authorized_new(name, content), 'Unowned recovery deletion')
        (ROOT / name).unlink()
    for name, entry in state['backups'].items(): shutil.copy2(ROOT / entry['path'], ROOT / name)
    require(inventory(content) == state['baselineInventory'], 'Recovered packages differ from baseline')
    state.update(status='restored-baseline', restoredAt=now()); write(folder / 'checkpoint.json', state)
    print('BREZI_ARCHVIZ_RESTORED ' + json.dumps({'output': str(output), 'geometryReimported': False, 'attempt': state['attempt']}))


def verify_avatar(u, report):
    require(report['status'] == 'avatar-import-validated', 'Avatar import did not validate')
    assets = u.EditorAssetLibrary; paths_ = report['assets']
    mesh, material, blend = [assets.load_asset(paths_[name]) for name in ('mesh', 'material', 'blendspace')]
    require(isinstance(mesh, u.SkeletalMesh) and isinstance(material, u.Material) and blend is not None,
            'Saved avatar asset types differ')
    skeleton = mesh.get_editor_property('skeleton')
    slots = list(mesh.get_editor_property('materials'))
    require(len(slots) == 1 and slots[0].get_editor_property('material_interface') == material
            and blend.get_editor_property('skeleton') == skeleton,
            'Saved avatar material/blendspace skeleton binding differs')
    require(u.MaterialEditingLibrary.has_material_usage(material, u.MaterialUsage.MATUSAGE_SKELETAL_MESH),
            'Saved avatar material lost skeletal usage')
    for name, path in paths_['animations'].items():
        clip = assets.load_asset(path)
        require(isinstance(clip, u.AnimSequence) and clip.get_editor_property('skeleton') == skeleton
                and abs(float(clip.get_play_length()) - report['nativeClipLengthsSeconds'][name]) < .001,
                'Saved avatar source animation differs: ' + name)
    samples = list(blend.get_editor_property('sample_data'))
    expected_samples = {paths_['animations'][name]: value for name, value in (('Idle', 0), ('Walk', 115), ('Run', 240))}
    actual_samples = {}
    for sample in samples:
        clip = sample.get_editor_property('animation'); value = sample.get_editor_property('sample_value')
        require(clip and abs(float(value.y)) < .001 and abs(float(value.z)) < .001,
                'Saved locomotion sample uses unexpected axes')
        actual_samples[clip.get_path_name()] = float(value.x)
    require(len(samples) == 3 and actual_samples == expected_samples, 'Saved locomotion blend samples differ')
    normal = assets.load_asset('/Game/Brezi/Avatar/Michelle/Textures/T_Michelle_Normal')
    require(normal and normal.get_editor_property('flip_green_channel') and not normal.get_editor_property('srgb')
            and normal.get_editor_property('compression_settings') == u.TextureCompressionSettings.TC_NORMALMAP,
            'Saved avatar glTF normal convention differs')
    return {'status': 'saved-bindings-validated', 'clipCount': 3, 'normalGreenFlipped': True,
            'nativeVisualVerified': False, 'nativeLocomotionVerified': False}


def main():
    import unreal as u
    output, project, geometry, content, folder = paths(os.environ['BREZI_ARCHVIZ_OUTPUT'])
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == project,
            'Native commandlet project differs from the explicitly selected archviz output')
    report_path = output / 'archviz-import-report.json'
    baseline_path = output / 'model-refresh-import-report.json'; baseline_bytes = baseline_path.read_bytes()
    baseline = json.loads(baseline_bytes)
    require(baseline['status'] == 'model-refresh-import-validated', 'A completed baseline import is required')
    inputs = baseline_inputs(output, project, geometry, baseline)
    baseline_sha = sha(baseline_path)
    sys.path.insert(0, str(ROOT / 'scripts/unreal'))
    source = module('archviz_source_import', 'model-refresh-import.py'); source.unreal = u
    materials = module('archviz_finish_import', 'archviz-materials.py')
    avatar = module('archviz_avatar_import', 'archviz-avatar.py')
    import archviz_lighting as lighting
    import import_scene as base
    from hidden_collision import verify_hidden_collision_contract
    from doors import verify_doors_contract
    base.GEOMETRY = geometry; base.REPORT = copy.deepcopy(baseline)
    scene, bridge, records, archive = base.verify_inputs(); source.validate_current_source(scene, records)
    asset_inputs = materials.load_inputs()
    for item in asset_inputs['assets'].values():
        for spec in item['maps'].values(): inputs[spec['path']] = spec['sha256']
    avatar.source_asset()
    for name in ('public/assets/avatar/avatar.glb', 'public/assets/avatar/michelle-light-diffuse.png'):
        inputs[name] = sha(ROOT / name)
    # Helper Python may change between a caught failure and restored retry. All
    # immutable baseline/source bytes stay in inputFiles; current recipes are
    # separately pinned in each attempt's final pipelineFiles.
    pipeline = {name: sha(ROOT / name) for name in HELPERS}; check_pins(inputs)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem); levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    require(u.EditorLoadingAndSavingUtils.new_blank_map(False), 'Could not unload startup map')
    require(levels.load_level(MAP), 'Could not load saved baseline map')
    before = source.verify_reloaded_world(base, actors, records, baseline['materials'])
    verify_hidden_collision_contract(scene, geometry); verify_doors_contract(scene, geometry)
    base.measure_final_collision(actors)
    state = checkpoint(output, content, baseline, inputs, materials, scene)
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'pending', 'startedAt': now(),
              'attempt': state['attempt'], 'baselineReportSha256': baseline_sha,
              'sourceManifestSha256': baseline['sourceManifestSha256'], 'sourceGlbSha256': baseline['sourceGlbSha256'],
              'activeDesign': scene['activeDesign'], 'map': MAP, 'pipelineFiles': pipeline, 'inputFiles': inputs,
              'baselineReadback': before, 'geometryReimported': False, 'nativeRenderedVerified': False}
    write(report_path, report)
    try:
        report['archvizLighting'] = lighting.apply_archviz_lighting(scene, actors)
        report['avatar'] = avatar.apply_avatar(u, output)
        report['archvizMaterials'] = materials.apply_archviz_materials(scene, geometry, baseline['materials'])
        require(levels.save_current_level(), 'Could not save enhanced map')
        require(u.EditorAssetLibrary.save_directory('/Game/Brezi', only_if_is_dirty=True, recursive=True), 'Could not save enhanced assets')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False), 'Could not unload enhanced map')
        require(levels.load_level(MAP), 'Could not reload enhanced map')
        report['archvizMaterials'] = materials.verify_archviz_materials(scene, geometry, report['archvizMaterials'])
        report['savedReadback'] = source.verify_reloaded_world(base, actors, records, baseline['materials'], report['archvizMaterials'])
        report['archvizLighting'] = lighting.verify_archviz_lighting(scene, actors)
        report['avatarReadback'] = verify_avatar(u, report['avatar'])
        report['hiddenCollision'] = verify_hidden_collision_contract(scene, geometry)
        report['doors'] = verify_doors_contract(scene, geometry)
        base.measure_final_collision(actors)
        report['finalCollisionComponents'] = base.REPORT['finalCollisionComponents']
        lighting_receipt = output / 'archviz-lighting-report.json'; write(lighting_receipt, report['archvizLighting'])
        check_pins(inputs); check_pins(pipeline)
        require(baseline_path.read_bytes() == baseline_bytes, 'Baseline receipt was modified by enhancement')
        current = inventory(content)
        check_changes(state['baselineInventory'], current, state['allowedModifiedPackages'], content)
        map_file = relative(content / 'Maps/Brezi.umap')
        report['mapFileSha256'] = current.pop(map_file)
        report['finalAssetHashes'] = current
        report['receiptPins'] = {relative(path): sha(path) for path in (baseline_path, output / 'avatar-import-report.json',
            output / 'archviz-materials-report.json', lighting_receipt)}
        report.update(status='archviz-import-validated', generatedAt=now(), savedReloaded=True,
            protectedGeometryPackagesUnchanged=True, changedBaselinePackages=[name for name, digest in state['baselineInventory'].items()
                if sha(ROOT / name) != digest])
        write(report_path, report)
        state.update(status='complete', completedAt=now(), reportSha256=sha(report_path)); write(folder / 'checkpoint.json', state)
        u.log('BREZI_ARCHVIZ_IMPORT ' + json.dumps({'status': report['status'], 'materialCount':len(report['archvizMaterials']['materials']),
              'lightCount':report['archvizLighting']['fixtureCount'], 'geometryReimported':False}))
    except Exception as error:
        report.update(status='failed', generatedAt=now(), error=str(error)); write(report_path, report)
        current = inventory(content)
        try:
            check_changes(state['baselineInventory'], current, state['allowedModifiedPackages'], content)
            state.update(status='failed-recoverable', failedAt=now(), failedInventory=current, error=str(error))
        except Exception as integrity_error:
            state.update(status='failed-protected-drift', failedAt=now(), error=str(error), integrityError=str(integrity_error))
        write(folder / 'checkpoint.json', state)
        raise


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--restore': restore(sys.argv[2])
    else: main()
