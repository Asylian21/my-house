#!/usr/bin/env python3
"""Derive current six source approaches and prove floor triangles before native QA."""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('floor_proof', HERE / 'coplanar-supports.py')
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)


def prepare(geometry, output):
    selections = json.loads((HERE / 'source-specs.json').read_text())
    contract_path = geometry / 'walking.json'
    contract = json.loads(contract_path.read_text())
    if contract['provenance']['sourceObjSha256'] != proof.sha(geometry / 'dom-mm.obj'):
        raise ValueError('Walking source OBJ provenance differs')
    if contract['provenance']['sceneSha256'] != proof.sha(geometry / 'scene.json'):
        raise ValueError('Walking source scene provenance differs')
    floors = {row['objectId']: row for row in contract['walkSurfaces']}
    blockers = {row['objectId']: row for row in contract['staticBlockers'] + contract['capturedClosedBlockers']}
    triangles = proof.read_floor_triangles(geometry / 'dom-mm.obj', floors)
    cases = []
    for selected in selections['cases']:
        target = blockers.get(selected['targetObjectId'])
        if not target or target['sourceId'] != selected['targetSourceId']:
            raise ValueError('Selected source obstacle identity changed; review the selected case')
        bounds = target['nativeBoundsCm']
        axis = {'x': 0, 'y': 1}[selected['movementAxis']]
        cross_axis = 1 - axis
        transverse = selected['transverse'].get('cm', (bounds['min'][cross_axis] + bounds['max'][cross_axis]) / 2)
        case = {'id': selected['id'], 'targetObjectId': target['objectId'], 'targetSourceId': target['sourceId'],
                'targetBoundsCm': bounds, 'movementAxis': selected['movementAxis'], 'legs': [],
                'status': 'cpu-source-floor-checked-native-entry-and-traversal-pending'}
        for index, direction in enumerate([1, -1]):
            support_spec = selected['supports'][index]
            floor = floors.get(support_spec['objectId'])
            if not floor or floor['sourceId'] != support_spec['sourceId']:
                raise ValueError('Selected source floor identity changed; review the selected case')
            plane = bounds['min' if direction > 0 else 'max'][axis]
            xy = [0.0, 0.0]
            xy[axis], xy[cross_axis] = plane - direction * 60, transverse
            hits = []
            for triangle in triangles[floor['objectId']]:
                weights = proof.barycentric_xy(xy, triangle)
                if weights and min(weights) >= -1e-8:
                    hits.append(sum(w * p[2] for w, p in zip(weights, triangle)) + floor['supportOffsetCm'])
            if not hits:
                raise ValueError('Selected source floor has no triangle under the approach start')
            floor_z = max(hits)
            forward = [0, 0, 0]
            forward[axis] = direction
            case['legs'].append({'startEyeCandidateCm': [*xy, floor_z + contract['eyeHeightCm']],
                                 'supportObjectId': floor['objectId'], 'direction': forward,
                                 'expectedNearColliderPlaneCm': plane,
                                 'expectedCapsuleCenterStopCm': plane - direction * contract['capsuleRadiusCm'],
                                 'cpuSourceTriangleFloorHeightCm': floor_z,
                                 'cpuVerticalEyeClearanceCm': contract['eyeHeightCm']})
        cases.append(case)
    output.mkdir(parents=True, exist_ok=True)
    candidates = {'schemaVersion': 1, 'status': 'cpu-candidates-native-pending',
                  'sourceManifestSha256': proof.sha(geometry / 'scene.json'),
                  'contractSha256': proof.sha(contract_path), 'sourceObjSha256': proof.sha(geometry / 'dom-mm.obj'),
                  'sourceSpecsSha256': proof.sha(HERE / 'source-specs.json'), 'cases': cases}
    (output / 'source-candidates.json').write_text(json.dumps(candidates, indent=2, ensure_ascii=False) + '\n')
    subprocess.run([sys.executable, str(HERE / 'coplanar-supports.py'), '--geometry', str(geometry),
                    '--candidates', str(output / 'source-candidates.json'), '--output', str(output / 'coplanar-supports.json')], check=True)
    subprocess.run([sys.executable, str(HERE / 'generate-fixtures.py'), '--geometry', str(geometry),
                    '--output', str(output)], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--geometry', type=Path, default=ROOT / 'output/unreal/geometry')
    parser.add_argument('--output', type=Path, default=ROOT / 'output/unreal/traversal-fixtures')
    args = parser.parse_args()
    prepare(args.geometry.resolve(), args.output.resolve())
