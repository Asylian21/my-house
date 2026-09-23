#!/usr/bin/env python3
"""Build every exported Game action, replacing only the broken nested Xcode handoff.

This runner is limited to the isolated source-material model refresh project.
It does not accept or alter historical continuous-caustics build receipts.
Use --check for a read-only preflight; no native tool runs in that mode.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
CLANG = Path('/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang++')
XCODE = Path('/Applications/Xcode.app/Contents/Developer/usr/bin/xcodebuild')


def need(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def utc():
    return datetime.now(timezone.utc).isoformat()


def regular(path):
    path = Path(path)
    need(path.is_file() and not path.is_symlink() and path.absolute() == path.resolve(),
         'Expected canonical regular input: ' + str(path))
    return path


def within(path, parent):
    return Path(path).resolve().is_relative_to(parent)


def source_pins(project):
    files = [regular(project / 'BreziTwin.uproject')]
    counter = project / 'Build/Mac/BreziTwin.PackageVersionCounter'
    for name in ('Source', 'Config', 'Build'):
        for path in sorted((project / name).rglob('*')):
            need(not path.is_symlink(), 'Symlink in staged sources: ' + str(path))
            if path.is_file() and path != counter and 'FileOpenOrder' not in path.parts:
                files.append(regular(path))
    return {str(path): sha(path) for path in files}


def target_build_product_hashes(project, target):
    """Pin the finalized Xcode executable and every native target build product.

    UAT stages the executable inside the .app, after Xcode strip/sign processing;
    the raw link output is a different file and cannot stand in for that payload.
    """
    products = target.get('BuildProducts')
    need(isinstance(products, list) and products, 'Target receipt has no native build products')
    result, executables = {}, []
    for product in products:
        need(product.get('Type') in ('RequiredResource', 'Executable', 'DynamicLibrary'),
             'Unreviewed native build product type')
        value = product.get('Path')
        need(isinstance(value, str) and value, 'Native build product path is missing')
        path = Path(value.replace('$(ProjectDir)', str(project)))
        need('$(' not in str(path) and path.is_absolute() and within(path, project / 'Binaries/Mac'),
             'Native build product escapes the staged Mac target: ' + value)
        regular(path)
        need(str(path) not in result and path.stat().st_size > 0,
             'Duplicate or empty native build product: ' + str(path))
        result[str(path)] = sha(path)
        if product['Type'] == 'Executable':
            executables.append(path)
    app_executable = project / 'Binaries/Mac/BreziTwin.app/Contents/MacOS/BreziTwin'
    need(executables == [app_executable], 'Target receipt does not identify the finalized Game app executable')
    need(str(project / 'Binaries/Mac/BreziTwin') in result, 'Target receipt lacks the raw Game link output')
    return result


def prepare_plan(output, engine, graph):
    project = output / 'Project/BreziTwin'
    need(within(output, ROOT / 'output/unreal') and output != ROOT / 'output/unreal', 'Use an isolated output/unreal directory')
    regular(project / 'BreziTwin.uproject')
    descriptor = json.loads((project / 'BreziTwin.uproject').read_text())
    need(not any(p.get('Name') == 'BreziCausticsProbe' and p.get('Enabled') for p in descriptor.get('Plugins', [])),
         'This runner excludes the historical caustics plugin')
    need('Mode=transport-continuous' not in (project / 'Config/DefaultGame.ini').read_text(), 'Continuous profile is not supported')
    need(within(graph, output), 'Action graph must belong to the selected model output')
    regular(graph)
    data = json.loads(graph.read_text())
    need(data.get('Environment') == {}, 'Unexpected exported build environment')
    actions = data.get('Actions', [])
    need(actions and len({a['Id'] for a in actions}) == len(actions), 'Missing or duplicate action IDs')
    dotnet = engine / 'Engine/Binaries/ThirdParty/DotNet/10.0/mac-arm64/dotnet'
    ubt = engine / 'Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll'
    version_script = engine / 'Engine/Build/BatchFiles/Mac/UpdateVersionAfterBuild.sh'
    cwd = engine / 'Engine/Source'
    inputs = {str(regular(graph)), str(regular(Path(__file__).resolve()))}
    phases = {'compile': [], 'copy': [], 'link': [], 'xcode': [], 'version': [], 'metadata': []}
    producers = {}
    for action in actions:
        need(Path(action['WorkingDirectory']).resolve() == cwd, 'Unexpected action working directory')
        args = shlex.split(action['CommandArguments'])
        command = Path(action['CommandPath'])
        outputs = action.get('ProducedItems', [])
        need(outputs and all(within(p, project) for p in outputs + action.get('DeleteItems', [])),
             'Action writes outside the staged project')
        for path in outputs:
            need(path not in producers, 'Multiple writers for output: ' + path)
            producers[path] = action['Id']
        if action['Type'] in ('Compile', 'Link'):
            need(command == CLANG and len(args) == 1 and args[0].startswith('@'), 'Unexpected compiler invocation')
            response = regular(Path(args[0][1:]))
            need(within(response, project / 'Intermediate'), 'Response file belongs to another project')
            actual = shlex.split(response.read_text(encoding='utf-8-sig'))
            expected = shlex.split('\n'.join(action.get('ResponseFileContents', [])))
            need(actual == expected, 'Response file differs from exported graph: ' + str(response))
            need('-o' in actual and within(actual[actual.index('-o') + 1], project), 'Compiler output escapes staged project')
            need(not any(token.startswith('@') and not token.startswith(('@loader_path/', '@executable_path/', '@rpath/'))
                         for token in actual), 'Nested response files require explicit review')
            inputs.add(str(response))
            for token in actual:
                if token.startswith('/') and Path(token).suffix in ('.cpp', '.mm', '.h') and Path(token).is_file():
                    need(within(token, project) or within(token, engine), 'Compiler source outside selected project/engine')
                    inputs.add(str(regular(Path(token))))
            phase = 'compile' if action['Type'] == 'Compile' else 'link'
            need((phase == 'compile') == ('-c' in actual), 'Compile/link kind does not match response')
            if phase == 'link':
                need(actual[actual.index('-o') + 1] == str(project / 'Binaries/Mac/BreziTwin'), 'Wrong Game executable')
        elif command == dotnet and args and Path(args[0]) == ubt:
            modes = [v for v in args if v.startswith('-Mode=')]
            need(len(modes) == 1 and modes[0] in ('-Mode=ApplePostBuildSync', '-Mode=WriteMetadata'), 'Unexpected UBT mode')
            phase = 'xcode' if modes[0] == '-Mode=ApplePostBuildSync' else 'metadata'
            need(action['Type'] == ('CreateAppBundle' if phase == 'xcode' else 'WriteMetadata'), 'UBT action kind differs')
            for prefix in ('-Input=', '-XmlConfigCache='):
                values = [v[len(prefix):] for v in args if v.startswith(prefix)]
                if prefix == '-Input=':
                    need(len(values) == 1, 'Missing native metadata input')
                for value in values:
                    need(within(value, project / 'Intermediate'), 'Native metadata belongs to another project')
                    inputs.add(str(regular(Path(value))))
            if phase == 'metadata':
                metadata_path = Path(next(v[7:] for v in args if v.startswith('-Input=')))
                metadata = json.loads(metadata_path.read_text())
                need(metadata['ProjectFile'] == str(project / 'BreziTwin.uproject')
                     and metadata['ReceiptFile'] == str(project / 'Binaries/Mac/BreziTwin.target'), 'Metadata target differs')
            inputs.add(str(regular(ubt)))
        elif command == Path('/bin/sh') and len(args) == 2 and args[0] == '-c' and action['Type'] == 'BuildProject':
            copy_args = shlex.split(args[1])
            need(len(copy_args) == 4 and copy_args[:2] == ['cp', '-f'], 'Unreviewed runtime dependency copy')
            source, destination = map(Path, copy_args[2:])
            tbb = engine / 'Engine/Source/ThirdParty/Intel/TBB/Deploy/oneTBB-2022.3.0/Mac/lib'
            allowed = {'libtbb.12.17.dylib', 'libtbb.12.dylib', 'libtbb.dylib',
                       'libtbbmalloc.2.17.dylib', 'libtbbmalloc.2.dylib', 'libtbbmalloc.dylib'}
            need(source.parent == tbb and source.name in allowed
                 and destination == project / 'Binaries/Mac' / source.name
                 and outputs == [str(destination)] and action.get('DeleteItems') == outputs,
                 'Runtime dependency copy differs from the installed engine TBB export')
            inputs.add(str(regular(source)))
            phase = 'copy'
        elif command == Path('/bin/sh') and len(args) == 4 and Path(args[0]) == version_script:
            need(args[1] == str(project) and args[2] == 'Mac' and args[3].isdigit(), 'Version action belongs to another target')
            phase = 'version'
            inputs.add(str(regular(version_script)))
        else:
            raise RuntimeError('Unreviewed action: ' + str(action['Id']))
        phases[phase].append(action)
    need(phases['compile'] and all(len(phases[p]) == 1 for p in ('link', 'xcode', 'version', 'metadata')),
         'Expected all project compiles and exactly one link/Xcode/version/metadata action')
    # Every compiled project source must participate in the final link closure.
    ids = {a['Id'] for a in actions}
    for action in actions:
        need(set(action.get('PrerequisiteActions', [])).issubset(ids), 'Graph has missing dependencies')
    order, completed = [], set()
    for group in ('compile', 'copy', 'link', 'xcode', 'version', 'metadata'):
        pending = list(phases[group])
        while pending:
            ready = next((a for a in pending if set(a.get('PrerequisiteActions', [])).issubset(completed)), None)
            need(ready is not None, 'Graph ordering is cyclic or differs from the reviewed handoff')
            order.append((group, ready)); completed.add(ready['Id']); pending.remove(ready)
    need(len(order) == len(actions), 'A graph action was omitted')
    # Pin generated UHT/PCH inputs and the actual Xcode project, without pinning outputs.
    for path in (project / 'Intermediate').rglob('*'):
        if path.is_file() and path.suffix in ('.h', '.cpp', '.mm', '.xcscheme', '.pbxproj', '.xcconfig'):
            if str(path) not in producers:
                inputs.add(str(regular(path)))
    workspace = project / 'Intermediate/ProjectFiles/BreziTwin_Mac_BreziTwin.xcworkspace'
    inputs.add(str(regular(workspace / 'contents.xcworkspacedata')))
    pins = source_pins(project)
    pins.update({p: sha(p) for p in sorted(inputs)})
    return project, cwd, dotnet, workspace, order, pins


def run_phase(argv, cwd, env, log_path, timeout):
    start = time.monotonic()
    row = {'argv': argv, 'cwd': str(cwd), 'startedAt': utc(), 'log': str(log_path)}
    child = None
    with log_path.open('wb') as log:
        try:
            child = subprocess.Popen(argv, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            row['pid'] = child.pid
            row['exitCode'] = child.wait(timeout=timeout)
        except BaseException as error:
            row['error'] = str(error)
            if child is not None and child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL); child.wait()
            row['exitCode'] = child.returncode if child else None
    row.update(endedAt=utc(), seconds=time.monotonic() - start, logSha256=sha(log_path))
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(os.environ.get('BREZI_MODEL_OUTPUT', ROOT / 'output/unreal/model-refresh-20260922')))
    parser.add_argument('--engine', type=Path, default=Path(os.environ.get('UNREAL_ENGINE_ROOT', '/Users/Shared/Epic Games/UE_5.8')))
    parser.add_argument('--graph', type=Path)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--phase-timeout', type=int, default=600)
    args = parser.parse_args()
    output, engine = args.output.resolve(), args.engine.resolve()
    graph = (args.graph or output / 'game-actions.json').resolve()
    project, cwd, dotnet, workspace, order, pins = prepare_plan(output, engine, graph)
    if args.check:
        print(json.dumps({'status': 'model-game-graph-preflight-validated', 'actions': len(order),
                          'compiles': sum(group == 'compile' for group, _ in order), 'pinnedFiles': len(pins), 'nativeExecuted': False}))
        return 0
    need(args.phase_timeout > 0, 'Invalid phase timeout')
    run = output / 'game-build-runs' / uuid.uuid4().hex
    (run / 'tmp').mkdir(parents=True)
    report_path = output / 'model-game-build.json'
    report = {'schemaVersion': 1, 'status': 'model-game-build-running', 'startedAt': utc(), 'project': str(project),
              'engine': str(engine), 'graph': str(graph), 'graphSha256': sha(graph), 'sourcePins': pins, 'phases': [],
              'scope': 'Every exported Game compile/link action; external equivalent Xcode finalization; generated version and metadata. No native runtime or rendered quality acceptance.',
              'replacedAction': 'ApplePostBuildSync only', 'runDirectory': str(run)}
    save(report_path, report); save(run / 'inputs-before.json', pins)
    env = os.environ.copy()
    for key in ('UBT_EXTRA_ARGS', 'UE_BUILD_FROM_XCODE', 'BREZI_UE_MAC_RENDERER_RULES', 'DYLD_INSERT_LIBRARIES'):
        env.pop(key, None)
    env.update(TMPDIR=str(run / 'tmp') + '/', UBT_NO_POST_DEPLOY='true', UE_SKIP_UBT_SDK_SETUP='0',
               PATH=str(dotnet.parent) + ':' + env.get('PATH', ''))
    try:
        for index, (group, action) in enumerate(order):
            argv = [action['CommandPath'], *shlex.split(action['CommandArguments'])]
            if group == 'xcode':
                argv = [str(XCODE), 'build', '-workspace', str(workspace), '-scheme', 'BreziTwin',
                        '-configuration', 'Development', '-destination', 'generic/platform=macOS',
                        'CODE_SIGN_ALLOW_ENTITLEMENTS_MODIFICATION=YES', 'UE_XCODE_BUILD_MODE=PostBuildSync',
                        '-hideShellScriptEnvironment', '-derivedDataPath', str(run / 'derived-data')]
            print(f'[{index + 1}/{len(order)}] {group}: {action.get("StatusDescription", action["Id"])}', flush=True)
            phase = run_phase(argv, cwd, env, run / f'{index:02d}-{group}.log', args.phase_timeout)
            phase.update(actionId=action['Id'], phase=group)
            report['phases'].append(phase); save(report_path, report)
            need(phase['exitCode'] == 0 and 'error' not in phase, 'Native phase failed; see ' + phase['log'])
            log = Path(phase['log']).read_text(errors='replace')
            need(not re.search(r'\*\* BUILD FAILED \*\*|The following build commands failed:', log), 'Native build reported failure')
            if group == 'xcode':
                need('** BUILD SUCCEEDED **' in log, 'External Xcode success footer missing')
            for path in action['ProducedItems']:
                need(Path(path).is_file() and Path(path).stat().st_size > 0, 'Native action output missing: ' + path)
            phase['outputHashes'] = {p: sha(p) for p in action['ProducedItems']}
            save(report_path, report)
        current = source_pins(project)
        expected_sources = {p: h for p, h in pins.items() if p in current or any(within(p, project / n) for n in ('Source', 'Config', 'Build')) or p == str(project / 'BreziTwin.uproject')}
        need(current == expected_sources, 'Staged source inventory changed during build')
        after = {p: sha(p) if Path(p).is_file() else None for p in pins}
        save(run / 'inputs-after.json', after)
        need(after == pins, 'Pinned source/graph/response inputs changed during build')
        raw = project / 'Binaries/Mac/BreziTwin'
        receipt = project / 'Binaries/Mac/BreziTwin.target'
        target = json.loads(receipt.read_text())
        need(target.get('TargetName') == 'BreziTwin' and target.get('Platform') == 'Mac'
             and target.get('Configuration') == 'Development', 'Generated target receipt identity differs')
        products = target_build_product_hashes(project, target)
        app_executable = project / 'Binaries/Mac/BreziTwin.app/Contents/MacOS/BreziTwin'
        report.update(status='model-game-build-validated', endedAt=utc(), rawExecutable=str(raw),
                      rawExecutableSha256=sha(raw), targetReceipt=str(receipt), targetReceiptSha256=sha(receipt),
                      buildProductHashes=products, appExecutable=str(app_executable),
                      appExecutableSha256=products[str(app_executable)],
                      allActionsExecuted=True, nativeRuntimeVerified=False)
    except BaseException as error:
        report.update(status='model-game-build-failed', endedAt=utc(), error=str(error))
        save(report_path, report); save(run / 'receipt.json', report)
        print(str(error), file=sys.stderr)
        return 1
    save(report_path, report); save(run / 'receipt.json', report)
    print(json.dumps({'status': report['status'], 'receipt': str(report_path), 'actions': len(report['phases'])}))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
