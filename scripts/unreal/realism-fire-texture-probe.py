"""Isolated editor-only inspection of two installed Epic Texture2D assets.

Host: --prepare output, then (explicitly launched by operator) --run output.
Native: Python commandlet exports full PNG source data without saving assets.
No model project, runtime module, or shipping plugin is changed by this probe.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/realism-fire-texture-probe.py'
ENGINE = Path('/Users/Shared/Epic Games/UE_5.8')
SOURCE = ENGINE / 'Engine/Plugins/Runtime/NetworkPredictionExtras/Content/Art/Effects/Proto/Shared/Textures/Fire'
PREFIX = '/Game/Brezi/FireTextureProbe'
TEXTURES = {
    'T_Fire_SubUV': {'sha256': '865a10d77419a7a5c80a89abbf2a738168cd79bfad1aab1397d3d5802ac6f33c', 'size': [1024, 1024]},
    'T_Fire_Tiled_D': {'sha256': '5fddf6ab9c5a32516248bdfce3cc9f2426a3b734d57f2c5bd1d26a93c6381252', 'size': [512, 512]},
}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def checked_output(value):
    path = (ROOT / value).resolve()
    require(path.parent == ROOT / 'output/unreal' and path.name.startswith('realism-fire-texture-probe-'),
            'Probe needs its own named output/unreal/realism-fire-texture-probe-* directory')
    return path


def descriptor():
    return {'FileVersion': 3, 'EngineAssociation': '5.8', 'Category': 'Editor Probe',
            'Description': 'Local texture export evidence only; never a shipping game.',
            'DisableEnginePluginsByDefault': True,
            'Plugins': [{'Name': name, 'Enabled': True, 'TargetAllowList': ['Editor']}
                        for name in ('PythonScriptPlugin', 'EditorScriptingUtilities')]
                       + [{'Name': name, 'Enabled': False} for name in ('NetworkPredictionExtras', 'NetworkPrediction')],
            'TargetPlatforms': ['Mac']}


def png_info(path):
    data = Path(path).read_bytes()
    require(len(data) >= 33 and data[:8] == b'\x89PNG\r\n\x1a\n' and data[12:16] == b'IHDR', 'Export is not a PNG')
    width, height, depth, color = struct.unpack('>IIBB', data[16:26])
    require(width > 0 and height > 0 and depth in (8, 16), 'Unsupported PNG source export')
    return {'width': width, 'height': height, 'bitDepth': depth, 'colorType': color,
            'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def validate_dependencies(dependencies, package):
    allowed = {package, '/Script/CoreUObject', '/Script/Engine'}
    require(all(p in allowed for p in dependencies), 'Texture has external content/runtime dependency: ' + repr(dependencies))


def check_pins(prepared):
    for path, value in prepared['inputPins'].items():
        require(sha(path) == value, 'Probe input changed: ' + path)
    require(read(prepared['project']) == descriptor(), 'Probe project descriptor changed')


def prepare(value):
    output = checked_output(value)
    require(not output.exists(), 'Probe output already exists; preserve prior evidence and use a new revision')
    for name, spec in TEXTURES.items():
        source = SOURCE / (name + '.uasset')
        require(sha(source) == spec['sha256'], 'Installed Epic texture differs: ' + name)
        require(not any(source.with_suffix(ext).exists() for ext in ('.uexp', '.ubulk')), 'Unexpected split texture package')
    content = output / 'Project/Content/Brezi/FireTextureProbe'
    content.mkdir(parents=True)
    (output / 'exports').mkdir()
    project = output / 'Project/FireTextureProbe.uproject'
    write(project, descriptor())
    config = output / 'Project/Config/DefaultEngine.ini'
    config.parent.mkdir()
    config.write_text('[/Script/EngineSettings.GameMapsSettings]\nEditorStartupMap=/Engine/Maps/Entry\n'
                      'GameDefaultMap=/Engine/Maps/Entry\n\n[/Script/UnrealEd.EditorLoadingSavingSettings]\nbAutoSaveEnable=False\n')
    rows, pins = {}, {str(p): sha(p) for p in (Path(__file__).resolve(), project, config,
        ENGINE / 'Engine/Build/Build.version', SOURCE.parents[6] / 'NetworkPredictionExtras.uplugin')}
    for name, spec in TEXTURES.items():
        source, target = SOURCE / (name + '.uasset'), content / (name + '.uasset')
        shutil.copy2(source, target)
        pins.update({str(source): sha(source), str(target): sha(target)})
        rows[name] = {'installedSource': str(source), 'sourcePackage': '/NetworkPredictionExtras/Art/Effects/Proto/Shared/Textures/Fire/' + name,
                      'copiedFile': str(target), 'ownedPackage': PREFIX + '/' + name,
                      'sha256': spec['sha256'], 'expectedSize': spec['size']}
    result = {'schemaVersion': 1, 'owner': OWNER, 'status': 'prepared-native-not-run', 'generatedAt': now(),
              'output': str(output), 'project': str(project), 'engine': str(ENGINE), 'textures': rows, 'inputPins': pins,
              'shippingProjectTouched': False, 'runtimePluginEnabled': False}
    write(output / 'prepared.json', result)
    print(json.dumps({'status': result['status'], 'output': str(output), 'project': str(project)}))


def native():
    import unreal as u
    output = checked_output(os.environ['BREZI_FIRE_TEXTURE_PROBE'])
    prepared = read(output / 'prepared.json')
    check_pins(prepared)
    require(Path(u.Paths.project_dir()).resolve() == Path(prepared['project']).parent, 'Wrong native probe project')
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'pending', 'startedAt': now(), 'nativeProcessId': os.getpid(),
              'output': str(output), 'preparedSha256': sha(output / 'prepared.json'), 'textures': {}, 'renderedVerified': False}
    try:
        plugins = sorted(str(p) for p in u.PluginBlueprintLibrary.get_enabled_plugin_names())
        require(not {'NetworkPrediction', 'NetworkPredictionExtras'} & set(plugins), 'Experimental runtime plugin is enabled')
        report['enabledPlugins'] = plugins
        registry = u.AssetRegistryHelpers.get_asset_registry()
        registry.scan_paths_synchronous([PREFIX], True)
        options = u.AssetRegistryDependencyOptions()
        for field in ('include_soft_package_references', 'include_hard_package_references',
                      'include_game_package_references', 'include_editor_only_package_references'):
            options.set_editor_property(field, True)
        for field in ('include_searchable_names', 'include_soft_management_references', 'include_hard_management_references'):
            options.set_editor_property(field, False)
        for name, source in prepared['textures'].items():
            package = source['ownedPackage']
            texture = u.EditorAssetLibrary.load_asset(package)
            require(texture and texture.get_class().get_name() == 'Texture2D', 'Copied asset did not load as Texture2D: ' + name)
            require(texture.get_path_name() == package + '.' + name, 'Texture loaded outside owned package')
            dependencies = sorted(str(v) for v in registry.get_dependencies(u.Name(package), options))
            validate_dependencies(dependencies, package)
            properties = {}
            for field in ('srgb', 'compression_settings', 'lod_group', 'lod_bias', 'max_texture_size', 'mip_gen_settings',
                          'never_stream', 'virtual_texture_streaming', 'address_x', 'address_y', 'filter'):
                value = texture.get_editor_property(field)
                properties[field] = value if isinstance(value, (str, int, float, bool)) else str(value)
            dimensions = [int(texture.blueprint_get_size_x()), int(texture.blueprint_get_size_y())]
            require(dimensions == source['expectedSize'], 'Native texture resolution differs: ' + name)
            destination = output / 'exports' / (name + '.png')
            require(not destination.exists(), 'Preserve prior texture export')
            task = u.AssetExportTask()
            for field, value in [('object', texture), ('filename', str(destination)), ('automated', True),
                                 ('prompt', False), ('replace_identical', False), ('exporter', u.TextureExporterPNG())]:
                task.set_editor_property(field, value)
            require(u.Exporter.run_asset_export_task(task), 'Full source PNG export failed: ' + name)
            require(not list(task.get_editor_property('errors')), 'Texture exporter reported errors')
            exported = png_info(destination)
            require([exported['width'], exported['height']] == source['expectedSize'], 'Export is a thumbnail or reduced mip')
            report['textures'][name] = {**source, 'class': texture.get_class().get_name(), 'nativeSize': dimensions,
                'dependencies': dependencies, 'properties': properties, 'export': {'path': str(destination), **exported}}
        check_pins(prepared)
        report.update(status='native-full-textures-exported', originalAndCopiedAssetsUnchanged=True,
                      experimentalRuntimePluginsEnabled=False, contentDependenciesIndependent=True)
    except Exception as error:
        report.update(status='failed', error=str(error))
        raise
    finally:
        report['generatedAt'] = now()
        write(output / 'native-report.json', report)


def run(value):
    output = checked_output(value)
    prepared = read(output / 'prepared.json')
    check_pins(prepared)
    require(not (output / 'native-process.json').exists() and not (output / 'native-report.json').exists(), 'Preserve previous native probe attempt')
    command = [str(ENGINE / 'Engine/Binaries/Mac/UnrealEditor-Cmd'), prepared['project'], '-run=pythonscript',
               '-script=' + str(Path(__file__).resolve()), '-unattended', '-nop4', '-nosplash', '-nullrhi']
    process = {'command': command, 'startedAt': now(), 'preparedSha256': sha(output / 'prepared.json')}
    with (output / 'native.log').open('wb') as log:
        child = subprocess.Popen(command, cwd=ROOT, env={**os.environ, 'BREZI_FIRE_TEXTURE_PROBE': str(output)}, stdout=log, stderr=subprocess.STDOUT)
        process['pid'] = child.pid
        write(output / 'native-process.json', process)
        process['returncode'] = child.wait()
    process.update(endedAt=now(), logSha256=sha(output / 'native.log'))
    write(output / 'native-process.json', process)
    require(process['returncode'] == 0, 'Native texture probe failed; inspect native.log/report and preserve this revision')
    report = read(output / 'native-report.json')
    require(report['status'] == 'native-full-textures-exported' and report['nativeProcessId'] == process['pid'], 'Native export receipt missing or unrelated')
    require(report['preparedSha256'] == process['preparedSha256'], 'Native probe inputs differ')
    require(process['startedAt'] <= report['startedAt'] <= report['generatedAt'] <= process['endedAt'], 'Export outside native process lifetime')
    require(set(report['textures']) == set(TEXTURES), 'Incomplete native texture exports')
    for name, row in report['textures'].items():
        validate_dependencies(row['dependencies'], row['ownedPackage'])
        require(png_info(row['export']['path']) == {k: v for k, v in row['export'].items() if k != 'path'}, 'Export bytes changed')
    check_pins(prepared)
    write(output / 'verified.json', {'status': 'native-texture-probe-verified', 'generatedAt': now(),
        'reportSha256': sha(output / 'native-report.json'), 'processSha256': sha(output / 'native-process.json'),
        'preparedSha256': sha(output / 'prepared.json'), 'exports': {k: v['export'] for k, v in report['textures'].items()},
        'shippingProjectTouched': False, 'nativeRenderedVerified': False})
    print(json.dumps({'status': 'native-texture-probe-verified', 'output': str(output)}))


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--prepare':
        prepare(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == '--run':
        run(sys.argv[2])
    else:
        native()
