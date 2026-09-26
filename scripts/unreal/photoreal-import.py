"""Isolated additive look development after the validated archviz import.

Only the map and new /Game/Brezi/Photoreal assets may change. Baseline material,
geometry, avatar, collision and door packages remain byte-identical. Run through
model-refresh.mjs photoreal; restore a failed attempt only after its process exits.
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
MAP = '/Game/Brezi/Maps/Brezi'
OWNER = 'scripts/unreal/photoreal-import.py'
EXTENSIONS = {'.uasset', '.uexp', '.ubulk', '.umap'}


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def relative(path): return str(Path(path).resolve().relative_to(ROOT))
def now(): return datetime.now(timezone.utc).isoformat()
def write(path, value): Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts/unreal' / filename)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def inventory(content):
    return {relative(p): sha(p) for p in sorted(content.rglob('*')) if p.is_file() and p.suffix in EXTENSIONS}


def validate_changes(before, after, content):
    map_file = relative(content / 'Maps/Brezi.umap')
    require(set(before) <= set(after), 'Removed a baseline asset')
    for name, digest in before.items():
        require(name == map_file or after[name] == digest, 'Protected package changed: ' + name)
    for name in after.keys() - before.keys():
        require((ROOT/name).is_relative_to(content/'Photoreal'), 'New asset outside Photoreal: ' + name)


def restore(output):
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal'), 'Output outside workspace')
    state = read(output/'photoreal-checkpoint/state.json')
    require(state['status'] == 'failed-recoverable', 'No recoverable recorded failure')
    try: os.kill(state['nativeProcessId'], 0)
    except ProcessLookupError: pass
    else: raise RuntimeError('Native process is still running')
    content = output/'Project/BreziTwin/Content/Brezi'
    current = inventory(content)
    require(current == state['failedInventory'], 'Assets changed after failure')
    validate_changes(state['baselineInventory'], current, content)
    map_file = content/'Maps/Brezi.umap'
    backup = output/'photoreal-checkpoint/Brezi.umap'
    require(sha(backup) == state['baselineInventory'][relative(map_file)], 'Backup map differs')
    history = output/'photoreal-history'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    history.mkdir(parents=True)
    for file in [output/'photoreal-import-report.json', output/'photoreal-import.log', output/'photoreal-import.log.json', output/'photoreal-checkpoint/state.json']:
        if file.is_file(): shutil.copy2(file, history/file.name)
    shutil.copy2(backup, map_file)
    for name in current.keys() - state['baselineInventory'].keys(): (ROOT/name).unlink()
    require(inventory(content) == state['baselineInventory'], 'Restore not exact')
    state['status'] = 'restored'; write(output/'photoreal-checkpoint/state.json', state)


def main():
    import unreal as u
    output = Path(os.environ['BREZI_PHOTOREAL_OUTPUT']).resolve()
    require(output.is_relative_to(ROOT/'output/unreal'), 'Require isolated output')
    project = output/'Project/BreziTwin'; content = project/'Content/Brezi'; geometry = output/'geometry'
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == project, 'Wrong native project')
    baseline_file = output/'archviz-import-report.json'; baseline = read(baseline_file)
    require(baseline['status'] == 'archviz-import-validated', 'Validated archviz baseline required')
    before = inventory(content)
    require(before == {**baseline['finalAssetHashes'], relative(content/'Maps/Brezi.umap'): baseline['mapFileSha256']}, 'Native baseline inventory changed')
    require(not any((ROOT/k).is_relative_to(content/'Photoreal') for k in before), 'Fresh Photoreal namespace required')
    inputs = {relative(baseline_file): sha(baseline_file), **baseline['inputFiles'], **baseline['pipelineFiles'], **baseline['receiptPins']}
    for name, digest in inputs.items(): require(sha(ROOT/name) == digest, 'Baseline pinned input changed: ' + name)
    sys.path.insert(0, str(ROOT/'scripts/unreal'))
    source = module('photoreal_source', 'model-refresh-import.py'); source.unreal = u
    import import_scene as base
    baseline_source = read(output/'model-refresh-import-report.json')
    base.GEOMETRY = geometry; base.REPORT = copy.deepcopy(baseline_source)
    scene, bridge, records, archive = base.verify_inputs()
    actors = u.get_editor_subsystem(u.EditorActorSubsystem); levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    require(u.EditorLoadingAndSavingUtils.new_blank_map(False), 'Unload startup map failed')
    require(levels.load_level(MAP), 'Load baseline failed')
    source.verify_reloaded_world(base, actors, records, baseline_source['materials'], baseline['archvizMaterials'])
    folder = output/'photoreal-checkpoint'; folder.mkdir(exist_ok=True)
    backup = folder/'Brezi.umap'
    if backup.exists(): require(sha(backup) == sha(content/'Maps/Brezi.umap'), 'Checkpoint drift')
    else: shutil.copy2(content/'Maps/Brezi.umap', backup)
    state = {'owner':OWNER, 'status':'in-progress', 'nativeProcessId':os.getpid(), 'baselineInventory':before}
    write(folder/'state.json', state)
    report = {'schemaVersion':1, 'owner':OWNER, 'status':'pending', 'startedAt':now(),
              'baselineReportSha256':sha(baseline_file), 'activeDesign':scene['activeDesign'],
              'inputFiles':inputs, 'nativeRenderedVerified':False, 'sourceGeometryPreserved':True}
    report['pipelineFiles'] = {relative(p):sha(p) for p in sorted((ROOT/'scripts/unreal').glob('photoreal-*')) if p.is_file()}
    report['pipelineFiles'][relative(ROOT/'scripts/unreal/performance_scene_policy.py')] = sha(ROOT/'scripts/unreal/performance_scene_policy.py')
    try:
        exterior = module('photoreal_exterior','photoreal-exterior.py')
        interior = module('photoreal_interior','photoreal-interior.py')
        lighting = module('photoreal_lighting','photoreal-lighting.py')
        details = module('photoreal_geometry','photoreal-geometry.py')
        water = module('photoreal_water','photoreal-water.py')
        report['exterior'] = exterior.apply_photoreal_exterior(scene, geometry, baseline_source['materials'], actors)
        report['interior'] = interior.apply_photoreal_interior(scene, geometry, baseline_source['materials'])
        report['water'] = water.apply_water(scene, geometry, baseline_source['materials'])
        report['lighting'] = lighting.apply_lighting(actors)
        double_glass = None
        if os.environ.get('BREZI_PHOTOREAL_DOUBLE_GLASS') == '1':
            double_glass = module('photoreal_double_glass', 'glass-double-reflection.py')
            report['pipelineFiles'][relative(ROOT/'scripts/unreal/glass-double-reflection.py')] = sha(ROOT/'scripts/unreal/glass-double-reflection.py')
            report['doubleGlass'] = double_glass.apply_glass(scene, geometry, baseline_source['materials'])
        report['geometry'] = details.apply_geometry(output/'photoreal-geometry', geometry)
        lawn = None
        deck_shadow = None
        if os.environ.get('BREZI_PHOTOREAL_LAWN') == '1':
            deck_shadow = module('photoreal_deck_shadow', 'photoreal-deck-shadow.py')
            report['deckShadow'] = deck_shadow.apply_deck(scene, geometry)
            lawn = module('photoreal_lawn', 'photoreal-lawn.py')
            report['lawn'] = lawn.apply_lawn(scene, geometry, baseline_source['materials'])
        require(levels.save_current_level(), 'Save photoreal map failed')
        require(u.EditorAssetLibrary.save_directory('/Game/Brezi/Photoreal', only_if_is_dirty=True, recursive=True), 'Save detail packages failed')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False), 'Unload enhanced map failed')
        require(levels.load_level(MAP), 'Reload enhanced map failed')
        report['exterior'] = exterior.verify_photoreal_exterior(scene, geometry, report['exterior'], actors)
        report['interior'] = interior.verify_photoreal_interior(scene, geometry, report['interior'])
        report['water'] = water.verify_water(scene, geometry, report['water'])
        report['lighting'] = lighting.verify_lighting(actors, report['lighting'])
        report['geometry'] = details.verify_geometry(output/'photoreal-geometry', geometry, report['geometry'])
        if double_glass is not None:
            report['doubleGlass'] = double_glass.verify_glass(scene, geometry, report['doubleGlass'])
        if lawn is not None:
            report['lawn'] = lawn.verify_lawn(scene, geometry, report['lawn'])
        if deck_shadow is not None:
            report['deckShadow'] = deck_shadow.verify_deck(scene, geometry, report['deckShadow'])
        from hidden_collision import verify_hidden_collision_contract
        from doors import verify_doors_contract
        report['hiddenCollision'] = verify_hidden_collision_contract(scene, geometry)
        report['doors'] = verify_doors_contract(scene, geometry)
        current = inventory(content); validate_changes(before, current, content)
        report['mapFileSha256'] = current.pop(relative(content/'Maps/Brezi.umap'))
        report['finalAssetHashes'] = current
        for name in ('exterior', 'interior', 'water', 'doubleGlass', 'lawn', 'deckShadow'):
            if name not in report: continue
            for filename, digest in report[name].get('pipelineFiles', {}).items():
                require(sha(ROOT/filename)==digest, 'Executed helper changed: '+filename)
                require(filename not in report['pipelineFiles'] or report['pipelineFiles'][filename]==digest,
                        'Conflicting helper recipe pin: '+filename)
                report['pipelineFiles'][filename]=digest
            for filename, digest in report[name].get('inputFiles', {}).items():
                require(sha(ROOT/filename)==digest, 'Executed helper input changed: '+filename)
                require(filename not in inputs or inputs[filename]==digest, 'Conflicting helper input pin: '+filename)
                inputs[filename]=digest
        for name in ('exterior','interior','lawn'):
            if name not in report: continue
            for texture in report[name].get('textures',[]):
                path = texture.get('source')
                if path:
                    digest = sha(ROOT/path)
                    require(path not in inputs or inputs[path]==digest, 'Conflicting texture pin: '+path)
                    inputs[path] = digest
        for file in sorted((output/'photoreal-geometry').rglob('*')):
            if file.is_file(): inputs[relative(file)] = sha(file)
        for name, digest in inputs.items(): require(sha(ROOT/name) == digest, 'Input changed during import: ' + name)
        for name, digest in report['pipelineFiles'].items(): require(sha(ROOT/name) == digest, 'Recipe changed during import: ' + name)
        report.update(status='photoreal-import-validated', generatedAt=now(), savedReloaded=True,
                      protectedBaselineAssetsUnchanged=True)
        write(output/'photoreal-import-report.json', report)
        state.update(status='complete', reportSha256=sha(output/'photoreal-import-report.json')); write(folder/'state.json',state)
        u.log('BREZI_PHOTOREAL_IMPORT validated')
    except Exception as error:
        report.update(status='failed', generatedAt=now(), error=str(error)); write(output/'photoreal-import-report.json', report)
        current = inventory(content)
        try: validate_changes(before, current, content); state['status']='failed-recoverable'
        except Exception: state['status']='failed-protected-drift'
        state['failedInventory']=current; write(folder/'state.json',state)
        raise


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--restore': restore(sys.argv[2])
    else: main()
