"""Compose a new library from the sealed R10 basis and explicit shape studies.

Only the twenty managed lawn masters may be replaced. Four new garden masters
are additive; every other old mesh and all photographic recipes survive. This
does not import Unreal assets or accept their appearance.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-greenery-shape-library.py'
BASE = ROOT/'output/unreal/exterior-assets-greenery-20260930-r5'
BASE_PINS = {
    'geometry-manifest.json': '0849b3bf615bac261630cc2e97257c47e0e7641695a3859494690a5c7279c2b8',
    'material-manifest.json': '42dbaddc637c479d30482b1524217d8e9c288ff89de8f64d9f38396a1e63fbbb',
    'asset-manifest.json': 'dea3ce4b7528b78bf04fe4d192be7b79cf9ed9620547d239a42db428b67ca79c',
}
LAWN_IDS = {f'lawn_natural_{g}_{i}' for g in range(2) for i in range(8)} | {
    f'lawn_natural_edge_{g}_{i}' for g in range(2) for i in range(2)}
GARDEN_IDS = {'garden_white_organic_a', 'garden_white_organic_b',
              'garden_broadleaf_organic_a', 'garden_broadleaf_organic_b'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def source_pin(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), 'Source is outside the workspace or missing')
    return {'path': str(path), 'sha256': sha(path)}


def combine(base, lawn, garden):
    """Pure inventory/recipe conservation checks, also used by source tests."""
    old_geometry, old_materials = base
    lawn_geometry, lawn_materials = lawn
    garden_geometry, garden_materials = garden
    old = {r['id']: r for r in old_geometry['meshes']}
    replacement = {r['id']: r for r in lawn_geometry['meshes']}
    additions = {r['id']: r for r in garden_geometry['meshes']}
    require(lawn_geometry.get('owner') == 'scripts/unreal/exterior-lawn-tapered-integration.py'
            and garden_geometry.get('owner') == 'scripts/unreal/exterior-garden-organic-bushy.py',
            'Use the explicit covered taper adapter and reviewed bushy garden source')
    require(len(old) == len(old_geometry['meshes']) == 96 and LAWN_IDS <= old.keys(),
            'Sealed R10 master inventory differs')
    require(len(replacement) == len(lawn_geometry['meshes']) == 20 and set(replacement) == LAWN_IDS,
            'Only the exact twenty managed lawn masters may be replaced')
    require(len(additions) == len(garden_geometry['meshes']) == 4 and set(additions) == GARDEN_IDS
            and not (additions.keys() & old.keys()), 'Garden extension must add exactly four new identities')
    for key, row in replacement.items():
        require(row['role'] == 'grass' and row['placementPolicy'] == 'explicit-only'
                and row['materialKeys'] == old[key]['materialKeys'] == ['lawn_natural_blade']
                and row['lodScreenSizes'] == old[key]['lodScreenSizes'] == [1., .025, .007],
                'Unreviewed lawn recipe, placement or LOD replacement')
        require(row['heightCm'] <= old[key]['heightCm']+.00001
                and max(l['radialEnvelopeCm'] for l in row['lods']) <=
                    max(l['radialEnvelopeCm'] for l in old[key]['lods'])+.00001,
                'Replacement grows beyond the sealed lawn crown')
    materials = deepcopy(old_materials)
    for extension in (lawn_materials, garden_materials):
        for key, recipe in extension.items():
            require(key in materials and recipe == materials[key],
                    'Shape-only candidate cannot alter or add a material recipe: '+key)
    geometry = deepcopy(old_geometry)
    geometry['meshes'] = [deepcopy(replacement.get(row['id'], row)) for row in old_geometry['meshes']]
    geometry['meshes'].extend(deepcopy(garden_geometry['meshes']))
    require(len(geometry['meshes']) == 100 and sum(len(m['lods']) for m in geometry['meshes']) == 300,
            'Combined shape inventory differs')
    require(all(row == old[row['id']] for row in geometry['meshes']
                if row['id'] in old and row['id'] not in LAWN_IDS),
            'An unrelated original master changed')
    return geometry, materials


def build(lawn, garden, output):
    lawn, garden, output = map(lambda p: Path(p).resolve(), (lawn, garden, output))
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(),
            'Use a fresh external library output')
    inputs = {}
    libraries = []
    for directory in (BASE, lawn, garden):
        data = {}
        for name in ('geometry-manifest.json', 'material-manifest.json', 'asset-manifest.json'):
            pin = source_pin(directory/name)
            if directory == BASE:
                require(pin['sha256'] == BASE_PINS[name], 'Sealed R10 library differs: '+name)
            inputs[pin['path']] = pin['sha256']
            data[name] = read(pin['path'])
        for manifest in (data['geometry-manifest.json'], data['asset-manifest.json']):
            for path, expected in manifest.get('inputFiles', {}).items():
                actual = source_pin(path)
                require(actual['sha256'] == expected and inputs.get(actual['path'], expected) == expected,
                        'Library source changed or conflicts: '+path)
                inputs[actual['path']] = expected
        libraries.append(data)
    geometry, materials = combine(*[(d['geometry-manifest.json'], d['material-manifest.json']) for d in libraries])
    for row in geometry['meshes']:
        require(len(row['lods']) == 3 and sha(row['glbPath']) == row['glbSha256']
                and all(key in materials for key in row['materialKeys']), 'Plant LOD/GLB/recipe source differs: '+row['id'])
        inputs[str(Path(row['glbPath']).resolve())] = row['glbSha256']
    for recipe in materials.values():
        for texture in recipe['maps'].values():
            actual = source_pin(texture['path'])
            require(actual['sha256'] == texture['sha256'], 'Provider texture bytes changed')
            inputs[actual['path']] = actual['sha256']
    inputs[str(Path(__file__).resolve())] = sha(__file__)
    geometry.update(owner=OWNER, generatorSha256=sha(__file__), inputFiles=inputs,
                    revision='Long pointed managed lawn and connected organic garden shapes; original surroundings retained')
    sources = {'schema': 1, 'owner': OWNER, 'sourceSha256': sha(__file__), 'inputFiles': inputs,
               'libraries': [str(BASE), str(lawn), str(garden)],
               'sourceLibraries': [d['asset-manifest.json'] for d in libraries],
               'replacementScope': {'managedLawnMasters': sorted(LAWN_IDS), 'newGardenMasters': sorted(GARDEN_IDS),
                                    'unrelatedOriginalMastersUnchanged': 76, 'materialRecipesUnchanged': True},
               'nativeAppearanceAccepted': False, 'performanceAccepted': False,
               'scope': 'Artist interpretation of plant growth; no botanical or geodetic survey is asserted'}
    output.mkdir(parents=True)
    for name, value in [('geometry-manifest.json', geometry), ('material-manifest.json', materials), ('asset-manifest.json', sources)]:
        with (output/name).open('x') as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False); stream.write('\n')
    return {'output': str(output), 'masters': 100, 'lods': 300, 'materials': len(materials),
            'sourcePins': len(inputs), 'nativeAppearanceAccepted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lawn', required=True); parser.add_argument('--garden', required=True); parser.add_argument('--output', required=True)
    print(json.dumps(build(**vars(parser.parse_args()))))
