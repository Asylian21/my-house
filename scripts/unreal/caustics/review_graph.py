#!/usr/bin/env python3
"""Review an exported UE action graph without executing it or changing its inputs."""
from pathlib import Path
import argparse, collections, hashlib, json, re, shlex, sys
sys.dont_write_bytecode = True


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def tbb_copy(action, engine, project):
    """Only the observed UE oneTBB copy action; never accept an arbitrary shell."""
    names = {'libtbb.12.17.dylib', 'libtbb.12.dylib', 'libtbb.dylib',
             'libtbbmalloc.2.17.dylib', 'libtbbmalloc.2.dylib', 'libtbbmalloc.dylib'}
    outer = shlex.split(action.get('CommandArguments', ''))
    need(action['CommandPath'] == '/bin/sh' and len(outer) == 2 and outer[0] == '-c', 'Expected exact TBB copy shell argv')
    inner = shlex.split(outer[1])
    need(len(inner) == 4 and inner[:2] == ['cp', '-f'], 'Expected one cp -f command')
    source, target = Path(inner[2]), Path(inner[3])
    need(source.name in names, 'Unsupported TBB filename')
    expected_source = engine / 'Engine/Source/ThirdParty/Intel/TBB/Deploy/oneTBB-2022.3.0/Mac/lib' / source.name
    expected_target = project / 'Binaries/Mac' / source.name
    need(source == expected_source and target == expected_target, 'TBB source/target does not match selected engine/project')
    need(not any(c in str(source) + str(target) for c in '$`"\\\r\n'), 'Unsupported shell characters in TBB paths')
    need(outer[1] == f'cp -f "{source}" "{target}"', 'TBB copy shell differs from exact generated command')
    need(Path(action['WorkingDirectory']) == engine / 'Engine/Source' and not action.get('ResponseFileContents'), 'Unexpected TBB copy working directory/response')
    need(action.get('ProducedItems') == [str(target)] and action.get('DeleteItems') == [str(target)], 'TBB copy output/deletion must equal target')
    need(source.resolve() == source and source.is_file() and not source.is_symlink(), 'TBB source missing or aliased')
    need(target.resolve() == target and not target.is_symlink() and (not target.exists() or target.is_file()), 'TBB destination is not a regular unaliased path')
    digest = sha(source.read_bytes())
    return {'action': action['Id'], 'source': str(source), 'sourceSha256': digest,
            'target': str(target), 'expectedOutputSha256': digest,
            'currentOutputSha256': sha(target.read_bytes()) if target.is_file() else None,
            'copyExecutedByReviewer': False}


def review(document, engine, project, graph_sha):
    E, P = Path(engine).resolve(), Path(project).resolve()
    actions = document.get('Actions')
    need(isinstance(actions, list) and actions, 'Empty/malformed Actions')
    ids = [a.get('Id') for a in actions]
    need(all(type(i) is int for i in ids) and len(ids) == len(set(ids)), 'Duplicate/invalid action IDs')
    by_id = dict(zip(ids, actions))
    issues, inputs, provider, links, outputs, deletes, copies = [], {}, [], [], {}, set(), []
    dependencies = {}
    plugin_root = P / 'Plugins/BreziCausticsProbe'

    def issue(i, why, value=None):
        issues.append([i, why] + ([] if value is None else [str(value)]))

    def permitted(p):
        return p.is_relative_to(E / 'Engine') or p.is_relative_to(P)

    def resolve(wd, value):
        return (wd / value).resolve()

    def read_input(i, p):
        if not permitted(p):
            issue(i, 'Foreign generated/source input', p)
            return ''
        if not p.is_file():
            issue(i, 'Missing generated/source input', p)
            return ''
        raw = p.read_bytes()
        inputs[str(p)] = sha(raw)
        text = raw.decode('utf-8', errors='replace')
        if 'output/unreal/engine-candidate/' in text:
            issue(i, 'Historical candidate reference in input', p)
        # Unity files and generated forced includes must not retain another clone.
        for match in re.finditer(r'^\s*#\s*include\s*["<]([^">]+)[">]', text, re.M):
            value = match.group(1)
            if '/.brezi-managed/' in value and not permitted(resolve(p.parent, value)):
                issue(i, 'Foreign managed include', value)
        return text

    for a in actions:
        i, kind = a['Id'], a.get('Type')
        wd = Path(a['WorkingDirectory']).resolve()
        if not permitted(wd):
            issue(i, 'Foreign working directory', wd)
        deps = a.get('PrerequisiteActions', [])
        need(isinstance(deps, list) and all(type(d) is int for d in deps), 'Malformed prerequisite IDs')
        dependencies[i] = set(deps)
        if len(deps) != len(set(deps)) or any(d not in by_id or d == i for d in deps):
            issue(i, 'Missing/self/duplicate prerequisite action')
        for field in ('ProducedItems', 'DeleteItems'):
            for value in a.get(field, []):
                p = resolve(wd, value)
                if not permitted(p):
                    issue(i, 'Foreign ' + field, p)
                if field == 'ProducedItems':
                    if str(p) in outputs:
                        issue(i, 'Duplicate produced path', p)
                    outputs[str(p)] = i
                else:
                    deletes.add(str(p))
        if 'output/unreal/engine-candidate/' in json.dumps(a):
            issue(i, 'Historical candidate reference in action')
        command = shlex.split(a.get('CommandArguments', ''))
        tokens = shlex.split('\n'.join(a.get('ResponseFileContents', [])))
        exe = Path(a['CommandPath'])
        if kind in ('Compile', 'Link'):
            if exe.name != 'clang++' or not str(exe).startswith('/Applications/Xcode.app/Contents/Developer/'):
                issue(i, 'Unexpected native compiler/linker', exe)
            if (kind == 'Compile') != ('-c' in tokens):
                issue(i, 'Compile/link command mode differs')
            if not command or any(not t.startswith('@') for t in command):
                issue(i, 'Expected compiler response-file argv')
            for token in command:
                if token.startswith('@'):
                    rsp = read_input(i, resolve(wd, token[1:]))
                    if shlex.split(rsp) != tokens:
                        issue(i, 'Response file differs from exported command', token[1:])
        elif kind == 'BuildProject':
            try:
                copied = tbb_copy(a, E, P)
                copies.append(copied)
                inputs[copied['source']] = copied['sourceSha256']
            except (ValueError, OSError) as error:
                issue(i, 'Unsupported copy action: ' + str(error))
        elif kind in ('CreateAppBundle', 'WriteMetadata'):
            dotnet = E / 'Engine/Binaries/ThirdParty/DotNet/10.0/mac-arm64/dotnet'
            ubt = str(E / 'Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll')
            managed = (exe == dotnet and command and command[0] == ubt and
                       ('-Mode=ApplePostBuildSync' if kind == 'CreateAppBundle' else '-Mode=WriteMetadata') in command)
            version = (kind == 'CreateAppBundle' and exe == Path('/bin/sh') and len(command) == 4 and
                       command[:3] == [str(E / 'Engine/Build/BatchFiles/Mac/UpdateVersionAfterBuild.sh'), str(P), 'Mac'] and command[3].isdigit())
            if not (managed or version):
                issue(i, 'Unexpected metadata/postbuild command')
            for token in command:
                if token.startswith(('-Input=', '-XmlConfigCache=')):
                    p = resolve(wd, token.split('=', 1)[1])
                    if not p.is_relative_to(P):
                        issue(i, 'Foreign postbuild input', p)
        else:
            issue(i, 'Unsupported action type', kind)
        forced = [resolve(wd, tokens[n + 1]) for n, t in enumerate(tokens[:-1]) if t == '-include']
        definitions = {p: read_input(i, p) for p in forced}
        for token in tokens:
            if token.endswith(('.cpp', '.mm', '.c', '.rsp', '.response')):
                read_input(i, resolve(wd, token))
            if '/.brezi-managed/' in str(resolve(wd, token.lstrip('@'))) and not token.startswith('-'):
                if not permitted(resolve(wd, token.lstrip('@'))):
                    issue(i, 'Foreign managed command input', token)
        objects = [resolve(wd, t) for t in tokens if t.endswith('.o')]
        produced = [resolve(wd, t) for t in a.get('ProducedItems', [])]
        is_provider = kind == 'Compile' and (any(p.is_relative_to(plugin_root) for p in produced) or
                                             any(p.name == 'Definitions.BreziCausticsProbe.h' for p in forced))
        if is_provider:
            defs = [(p, text) for p, text in definitions.items() if p.name == 'Definitions.BreziCausticsProbe.h' and p.is_relative_to(plugin_root)]
            values = [m.group(1).strip() for _, text in defs for m in re.finditer(r'^\s*#\s*define\s+BREZI_HAS_FLOOR_CAUSTICS_API\s+([^\r\n]+)', text, re.M)]
            enabled = len(defs) == 1 and values == ['1'] and not any('BREZI_HAS_FLOOR_CAUSTICS_API' in t for t in tokens)
            obj = [str(p) for p in produced if p.suffix == '.o']
            provider.append({'action': i, 'apiEnabled': enabled, 'definitions': [str(p) for p, _ in defs], 'objects': obj})
            if not enabled or not obj or not all(Path(p).is_relative_to(plugin_root) for p in obj):
                issue(i, 'Provider API definition/object scope missing or conflicting')
        if kind == 'Link':
            links.append({'action': i, 'objects': [str(p) for p in objects], 'products': [str(p) for p in produced]})
        if kind in ('Compile', 'Link'):
            for flag in ('-o', '-MF'):
                for n, token in enumerate(tokens[:-1]):
                    if token == flag and resolve(wd, tokens[n + 1]) not in produced:
                        issue(i, 'Response output missing from ProducedItems', tokens[n + 1])

    pending, ancestors = set(ids), {}
    while pending:
        ready = sorted(i for i in pending if dependencies[i].issubset(ancestors))
        if not ready:
            issue('graph', 'Cyclic or unresolved prerequisite graph')
            break
        for i in ready:
            ancestors[i] = set(dependencies[i])
            for d in dependencies[i]:
                ancestors[i].update(ancestors[d])
            pending.remove(i)
    for p in provider:
        matching = [link for link in links if p['action'] in ancestors.get(link['action'], set()) and
                    set(p['objects']).issubset(link['objects']) and any(
                        q == str(P / 'Binaries/Mac/BreziTwin') or q == str(plugin_root / 'Binaries/Mac/libUnrealEditor-BreziCausticsProbe.dylib')
                        for q in link['products'])]
        p['linkActions'] = [x['action'] for x in matching]
        if not matching:
            issue(p['action'], 'Provider object absent from target link response/prerequisites')
    if not provider:
        issue('graph', 'No provider compile action; current build acceptance requires actual compile evidence, not inferred cache reuse')
    # Current bytes are recorded, not represented as historical build execution.
    for name, digest in inputs.items():
        if not Path(name).is_file() or sha(Path(name).read_bytes()) != digest:
            issue('graph', 'Input changed during review', name)
    return {'schemaVersion': 1, 'status': 'failed' if issues else 'pass', 'issues': issues,
            'engineRoot': str(E), 'projectRoot': str(P), 'graphSha256': graph_sha,
            'actionCount': len(actions), 'types': dict(sorted(collections.Counter(a['Type'] for a in actions).items())),
            'providerCompileActions': provider, 'linkActions': links,
            'inspectedTextInputs': len(inputs) - len({row['source'] for row in copies}),
            'inspectedBinaryInputs': len({row['source'] for row in copies}),
            'copyActions': copies,
            'inputHashes': inputs, 'producedPaths': sorted(outputs), 'deletePaths': sorted(deletes),
            'sharedEngineProducedPaths': sorted(p for p in outputs if Path(p).is_relative_to(E / 'Engine')),
            'scope': 'Exported declared commands, path scope, DAG, provider definition and object-to-link inputs. Not native execution, a write sandbox, or symbol/runtime acceptance.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('engine', 'project', 'graph'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    E, P, graph = (x.resolve() for x in (a.engine, a.project, a.graph))
    need((E / '.brezi-isolated-engine').read_text().rstrip('\r\n') == str(E), 'Wrong engine marker')
    need(P.is_relative_to(E / '.brezi-managed') and (P / 'BreziTwin.uproject').is_file(), 'Wrong managed project')
    need(graph.is_relative_to(E / '.brezi-managed') and graph.name == 'actions.json', 'Wrong managed graph')
    output = (a.output or graph.parent / 'graph-review.json').absolute()
    need(output.resolve() == output and output.parent == graph.parent and not output.exists(), 'Choose a new review file alongside actions.json')
    raw = graph.read_bytes()
    result = review(json.loads(raw), E, P, sha(raw))
    need(graph.read_bytes() == raw, 'Graph changed during review')
    result.update(graphPath=str(graph), reviewerSha256=sha(Path(__file__).read_bytes()))
    with output.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'review': str(output), 'sha256': sha(output.read_bytes()),
                      'actionCount': result['actionCount'], 'issues': result['issues']}))
    return bool(result['issues'])


if __name__ == '__main__':
    raise SystemExit(main())
