"""Compose immutable exterior plant libraries without changing their sources."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def merge(base, extensions, output):
    base, output = Path(base).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('Use a new asset library output')
    inputs, libraries = {}, []
    for directory in [base, *map(lambda p: Path(p).resolve(), extensions)]:
        rows = {}
        for name in ('geometry-manifest.json', 'material-manifest.json', 'asset-manifest.json'):
            path = directory / name
            inputs[str(path)] = sha(path)
            rows[name] = json.loads(path.read_text())
        for manifest in (rows['geometry-manifest.json'], rows['asset-manifest.json']):
            for path, expected in manifest.get('inputFiles', {}).items():
                if sha(path) != expected:
                    raise ValueError('Changed library source: ' + path)
                if path in inputs and inputs[path] != expected:
                    raise ValueError('Conflicting library source: ' + path)
                inputs[path] = expected
        libraries.append(rows)
    geometry = copy.deepcopy(libraries[0]['geometry-manifest.json'])
    materials = copy.deepcopy(libraries[0]['material-manifest.json'])
    ids = {row['id'] for row in geometry['meshes']}
    if len(ids) != len(geometry['meshes']):
        raise ValueError('Duplicate base plant IDs')
    for library in libraries[1:]:
        for row in library['geometry-manifest.json']['meshes']:
            if row['id'] in ids:
                raise ValueError('Duplicate extension plant ID: ' + row['id'])
            ids.add(row['id'])
            geometry['meshes'].append(row)
        for key, recipe in library['material-manifest.json'].items():
            if key in materials and materials[key] != recipe:
                raise ValueError('Conflicting material recipe: ' + key)
            materials[key] = recipe
    for row in geometry['meshes']:
        if len(row['lods']) != 3 or sha(row['glbPath']) != row['glbSha256']:
            raise ValueError('Invalid plant LOD/source: ' + row['id'])
        if any(key not in materials for key in row['materialKeys']):
            raise ValueError('Missing plant material: ' + row['id'])
    for recipe in materials.values():
        for spec in recipe['maps'].values():
            if sha(spec['path']) != spec['sha256']:
                raise ValueError('Changed material map: ' + spec['path'])
    inputs[str(Path(__file__).resolve())] = sha(__file__)
    geometry.update(owner='scripts/unreal/exterior-assets-merge.py', inputFiles=inputs,
                    revision='Regional green landscape and garden morphology; inherited meshes preserved')
    sources = {'schema': 1, 'owner': 'scripts/unreal/exterior-assets-merge.py',
               'libraries': [str(base), *map(lambda p: str(Path(p).resolve()), extensions)],
               'sourceLibraries': [row['asset-manifest.json'] for row in libraries], 'inputFiles': inputs,
               'scope': 'Source libraries and their licenses remain explicit; no species survey is asserted'}
    output.mkdir(parents=True)
    for name, value in [('geometry-manifest.json', geometry), ('material-manifest.json', materials), ('asset-manifest.json', sources)]:
        (output / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    return {'output': str(output), 'meshes': len(geometry['meshes']), 'materials': len(materials)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True)
    parser.add_argument('--extension', action='append', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(merge(args.base, args.extension, args.output)))
