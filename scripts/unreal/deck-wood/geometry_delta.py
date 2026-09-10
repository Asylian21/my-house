"""Audit a newly exported deck layout against its retained complete source model.

Read-only for both exports. Unrelated topology, UV0, normals, model dimensions,
materials, and hidden collision must agree; a new report never replaces history.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[3]
DECK_IDS = {'DOM_01708', 'DOM_01710', 'DOM_01713', 'DOM_01719'}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def scan(path):
    arrays = {'v': [], 'vt': [], 'vn': []}
    objects, selected = {}, {}
    current, slot, digest, count = None, None, None, 0
    for line in Path(path).open():
        fields = line.split()
        if not fields:
            continue
        kind = fields[0]
        if kind in arrays:
            arrays[kind].append(tuple(map(float, fields[1:])))
        elif kind == 'o':
            if current is not None:
                objects[current] = {'sha256': digest.hexdigest(), 'triangles': count}
            current, slot, digest, count = fields[1], None, hashlib.sha256(), 0
            need(current not in objects, 'Duplicate object')
            if current in DECK_IDS:
                selected[current] = []
        elif kind == 'usemtl':
            slot = fields[1]
        elif kind == 'f':
            need(current and slot and len(fields) == 4, 'Unexpected OBJ face')
            refs = [tuple(int(v) if v else None for v in part.split('/')) for part in fields[1:]]
            need(all(len(r) == 3 and r[0] for r in refs), 'Missing OBJ face position')
            rows = [[arrays[k][r[i] - 1] if r[i] is not None else None
                for i, k in enumerate(('v', 'vt', 'vn'))] for r in refs]
            digest.update(json.dumps([slot, rows], separators=(',', ':')).encode())
            count += 1
            if current in selected:
                need(all(r[1] is not None for r in rows), 'Deck UV0 missing')
                selected[current].append({'p': [r[0] for r in rows],
                    'sourceUv0': [r[1] for r in rows],
                    'nativeUv0': [(r[1][0], 1 - r[1][1]) for r in rows]})
    if current is not None:
        objects[current] = {'sha256': digest.hexdigest(), 'triangles': count}
    return objects, selected


def audit(base, candidate, output):
    base, candidate, output = map(lambda p: Path(p).resolve(), (base, candidate, output))
    need(base != candidate and not output.exists(), 'Retain the prior export and use a new report')
    old, new = [json.loads((p / 'scene.json').read_text()) for p in (base, candidate)]
    for p, manifest in ((base, old), (candidate, new)):
        need(sha(p / 'dom-mm.obj') == manifest['objSha256'], 'OBJ hash differs from its manifest')
    for name, digest in new['sourceFiles'].items():
        need(sha(ROOT / name) == digest, 'Candidate source changed: ' + name)
    allowed_metadata = {'generatedAt', 'objSha256', 'summary', 'sourceFiles', 'sourceWorktreeStatus', 'deckBoardLayout', 'objects'}
    for key in old.keys() | new.keys():
        if key not in allowed_metadata:
            need(old.get(key) == new.get(key), 'Unrelated model metadata changed: ' + key)
    need(new['deckBoardLayout'] == {'revision': 'continuous-zone-grid-1', 'widthMm': 145,
        'jointMm': 8, 'thicknessMm': 28, 'topMm': 20, 'minimumCutWidthMm': 40}, 'Unknown deck construction revision')
    a, _ = scan(base / 'dom-mm.obj')
    b, selected_b = scan(candidate / 'dom-mm.obj')
    need(a.keys() == b.keys(), 'Object identity set changed')
    changed = sorted(k for k in a if a[k] != b[k])
    need(changed and set(changed) <= DECK_IDS, 'Non-deck geometry, UV0 or normals changed: ' + str(changed))
    records_a = {r['id']: r for r in old['objects']}
    records_b = {r['id']: r for r in new['objects']}
    need(records_a.keys() == a.keys() == records_b.keys(), 'Manifest/OBJ identity mismatch')
    for key, prior in records_a.items():
        after = records_b[key]
        for field in prior.keys() | after.keys():
            if key in changed and field in ('boundsMm', 'triangles'):
                continue
            need(prior.get(field) == after.get(field), f'Unrelated object property changed: {key}.{field}')
    spec = importlib.util.spec_from_file_location('deck_source_geometry', Path(__file__).with_name('source_geometry.py'))
    geometry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(geometry)
    boards = {k: geometry._boards(k, triangles) for k, triangles in selected_b.items()}
    for id_, rows in boards.items():
        need(len(rows) * 12 == b[id_]['triangles'], 'Incomplete deck box group')
        need(all(39.998 <= row['dimensionsMm'][1] <= 145.002 for row in rows), 'Fragile or oversized board cut')
        need(all(abs(row['boundsMm']['max'][2] - 20) < .002 for row in rows), 'Deck elevation changed')
    # Slice the actually exported pool boards at plan X=13000, away from butt joints.
    pool = boards['DOM_01719']
    def uncovered(start, end):
        return [y + .5 for y in range(start, end) if not any(
            r['boundsMm']['min'][0] < 13000 - 15200 < r['boundsMm']['max'][0]
            and r['boundsMm']['min'][1] <= y + .5 - 10800 <= r['boundsMm']['max'][1] for r in pool)]
    need(uncovered(16859, 16908) == [], '49 mm opening remains in the exported mesh')
    need(uncovered(17971, 18008) == [17996.5 + i for i in range(8)], '37 mm opening was not reduced to the regular joint')
    hatch = new['poolShaft']['hatch']['footprintMm']
    for row in pool:
        lo, hi = row['boundsMm']['min'], row['boundsMm']['max']
        overlap = max(0, min(hi[0] + 15200, hatch['x1']) - max(lo[0] + 15200, hatch['x0'])) * max(
            0, min(hi[1] + 10800, hatch['y1']) - max(lo[1] + 10800, hatch['y0']))
        need(overlap < .01, 'Exported board bridges the hatch')
    need(sha(base / 'brezi-collision-only.glb') == sha(candidate / 'brezi-collision-only.glb'), 'Hidden collision geometry changed')
    report = {'status': 'shared-deck-geometry-delta-validated', 'base': str(base), 'candidate': str(candidate),
        'baseSceneSha256': sha(base / 'scene.json'), 'candidateSceneSha256': sha(candidate / 'scene.json'),
        'baseObjSha256': old['objSha256'], 'candidateObjSha256': new['objSha256'],
        'changedObjectIds': changed, 'unchangedObjectCount': len(a) - len(changed),
        'objects': {k: {'before': a[k], 'after': b[k], 'boardCount': len(boards[k]),
            'minimumCutWidthMm': min(r['dimensionsMm'][1] for r in boards[k])} for k in sorted(DECK_IDS)},
        'modelDimensionsMaterialsAndHatchUnchanged': True, 'hiddenCollisionBytesUnchanged': True,
        'exportedPoolGap49Closed': True, 'exportedPoolGap37ReducedTo8': True,
        'nativeImportAccepted': False, 'packagedAppContainsRevision': False,
        'generatorSha256': sha(__file__), 'boxAuditSha256': sha(Path(__file__).with_name('source_geometry.py'))}
    output.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'candidate', 'output'):
        p.add_argument('--' + name, required=True)
    r = audit(**vars(p.parse_args()))
    print(json.dumps({k: r[k] for k in ('status', 'changedObjectIds', 'unchangedObjectCount', 'candidateObjSha256')}))
