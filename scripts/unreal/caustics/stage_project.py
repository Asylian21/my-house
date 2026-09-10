#!/usr/bin/env python3
"""Stage canonical authoring inputs into a fresh managed project, keeping prior builds intact."""
from pathlib import Path
import argparse
import json
import subprocess
import sys

sys.dont_write_bytecode = True
import phase_runner as F
import native_process as H


def clone_tree(source, destination):
    """APFS copy-on-write shares storage, never mutable file identities."""
    H.need(source.is_dir() and not destination.exists(), 'Choose a fresh copy destination')
    subprocess.run(['/bin/cp', '-cR', str(source), str(destination)], check=True)


def authoring_rows(project):
    return {str(Path(p).relative_to(project)): digest
            for p, digest in F.project_pins(project).items()}


def stage(engine, previous_project, canonical_project, destination, output):
    engine, previous, canonical, destination, output = map(
        F.path, (engine, previous_project, canonical_project, destination, output))
    F.paths(engine, previous, destination.parent / 'runs')
    H.need(destination.is_relative_to(engine / '.brezi-managed'), 'Project must be managed')
    H.need(not destination.exists() and not output.exists(), 'Preserve existing output')
    H.need(not destination.is_relative_to(previous) and not previous.is_relative_to(destination),
           'New project must be separate from the previous project')
    H.need(not destination.is_relative_to(canonical) and not canonical.is_relative_to(destination),
           'Canonical authoring inputs must remain separate')
    H.need(output.is_relative_to(engine / '.brezi-managed') and not output.is_relative_to(destination),
           'Stage report must be outside the new project')
    before = authoring_rows(canonical)
    old = authoring_rows(previous)
    output.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=False)
    # Copy only explicit authoring inputs and optional local build caches. No Saved
    # runtime preferences, old archive, cooked output or receipt enters the project.
    for name in ('Source', 'Config', 'Build', 'Content'):
        if (canonical / name).is_dir():
            clone_tree(canonical / name, destination / name)
    subprocess.run(['/bin/cp', '-c', str(canonical / 'BreziTwin.uproject'), str(destination / 'BreziTwin.uproject')], check=True)
    cache_trees = []
    for name in ('Binaries', 'Intermediate'):
        if (previous / name).is_dir():
            clone_tree(previous / name, destination / name)
            cache_trees.append(name)
    (destination / 'Plugins').mkdir()
    for plugin in sorted((canonical / 'Plugins').iterdir()):
        H.need(plugin.is_dir() and not plugin.is_symlink(), 'Expected a real project plugin')
        target = destination / 'Plugins' / plugin.name
        target.mkdir()
        for item in sorted(plugin.iterdir()):
            if item.name in ('Binaries', 'Intermediate', 'Saved', '__pycache__'):
                continue
            if item.is_dir():
                clone_tree(item, target / item.name)
            else:
                H.need(item.is_file() and not item.is_symlink(), 'Expected a regular plugin file')
                subprocess.run(['/bin/cp', '-c', str(item), str(target / item.name)], check=True)
        for name in ('Binaries', 'Intermediate'):
            cache = previous / 'Plugins' / plugin.name / name
            if cache.is_dir():
                clone_tree(cache, target / name)
                cache_trees.append('Plugins/' + plugin.name + '/' + name)
    H.need(authoring_rows(canonical) == before == authoring_rows(destination),
           'Canonical authoring inputs changed during staging')
    H.need(authoring_rows(previous) == old, 'Previous project authoring inputs changed')
    for rel in before:
        H.need((canonical / rel).stat().st_ino != (destination / rel).stat().st_ino,
               'Staged authoring input aliases original file')
    # A reused object/binary is an incremental-build cache only. UBT must validate
    # and rebuild against the new source paths; this report never accepts a build.
    result = {
        'schemaVersion': 1, 'status': 'canonical-project-staged-build-pending',
        'engineRoot': str(engine), 'previousProject': str(previous),
        'canonicalProject': str(canonical), 'projectRoot': str(destination),
        'canonicalSourceHashes': before, 'previousAuthoringUnchanged': True,
        'distinctAuthoringInodes': True, 'copiedIncrementalCacheTrees': cache_trees,
        'canonicalChangesFromPrevious': [rel for rel in sorted(before.keys() | old.keys())
                                         if before.get(rel) != old.get(rel)],
        'newNativeBuildVerified': False,
    }
    H.save(output, result)
    return {'status': result['status'], 'project': str(destination),
            'report': str(output), 'sourceFiles': len(before)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('engine', 'previous-project', 'canonical-project', 'destination', 'output'):
        parser.add_argument('--' + name, required=True)
    try:
        print(json.dumps(stage(**vars(parser.parse_args())), indent=2))
    except Exception as error:
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr)
        sys.exit(1)
