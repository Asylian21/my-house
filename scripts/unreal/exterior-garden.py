"""Replace twelve existing ornamental card triplets with safe 3D root plans.

Pure source geometry; no Unreal process. Nine roots stay within the original
mulch-bed geometry, moving only to the nearest full-crown-safe position. Three
existing roots outside those beds keep exact XY and their original card envelope.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path

from shapely.geometry import Polygon, Point, MultiPoint
from shapely.ops import unary_union, nearest_points

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden.py'
BED_IDS = ['DOM_01965', 'DOM_01966']
STEP_IDS = ['DOM_01961', 'DOM_01962', 'DOM_01963', 'DOM_01964']


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def write_once(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def source_geometry(path):
    wanted = set(BED_IDS + STEP_IDS + [f'DOM_{i:05}' for i in range(1967, 2003)])
    vertices, triangles, points, current = [], {key: [] for key in wanted}, {key: [] for key in wanted}, None
    for line in Path(path).open():
        row = line.split()
        if not row:
            continue
        if row[0] == 'v':
            vertices.append([float(row[1]) / 10, -float(row[2]) / 10, float(row[3]) / 10])
        elif row[0] == 'o':
            current = row[1]
        elif row[0] == 'f' and current in wanted:
            face = [vertices[int(p.split('/')[0]) - 1] for p in row[1:]]
            points[current].extend(face)
            triangles[current].extend([face[0], face[i], face[i + 1]] for i in range(1, len(face) - 1))
    require(all(points.values()), 'Missing original garden geometry')
    footprints = {key: unary_union([Polygon([p[:2] for p in tri]) for tri in triangles[key]
                                   if Polygon([p[:2] for p in tri]).area > 1e-7])
                  for key in BED_IDS + STEP_IDS}
    return triangles, points, footprints


def build(geometry):
    scene_path, obj_path = geometry / 'scene.json', geometry / 'dom-mm.obj'
    scene = json.loads(scene_path.read_text())
    require(scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'C/B/B required')
    require(scene['housePlacement']['streetSetbackMm'] == scene['housePlacement']['eastSetbackMm'] == 3000, 'Setbacks changed')
    source_records = {row['id']: row for row in scene['objects']}
    triangles, points, shapes = source_geometry(obj_path)
    obstacles = unary_union([shapes[key] for key in STEP_IDS])
    radii = [50, 50, 45, 55, 60, 60, 45, 45, 55, 45, 55, 50]
    heights = [105, 88, 100, 110, 82, 96, 110, 122, 125, 105, 114, 120]
    placements, audits = [], []
    for index, first in enumerate(range(1967, 2003, 3)):
        identities = [f'DOM_{first + i:05}' for i in range(3)]
        form = 'flowering' if index < 6 else 'grass'
        for identity in identities:
            record = source_records[identity]
            require(record['enabled'] and record['group'] == 'Landscape' and record['triangles'] == 2,
                    'Unexpected ornamental source object')
            require('krížená botanická karta' in record['sourceId'] and record['metadata']['babylonCheckCollisions'] is False,
                    'Source ornamental semantics changed')
        original = points[identities[0]]
        minimum = [min(p[k] for p in original) for k in range(3)]
        maximum = [max(p[k] for p in original) for k in range(3)]
        center = [(minimum[k] + maximum[k]) / 2 for k in (0, 1)]
        point = Point(center)
        bed = next((key for key in BED_IDS if shapes[key].covers(point)), None)
        radius = radii[index]
        original_envelope = MultiPoint([p[:2] for identity in identities for p in points[identity]]).convex_hull
        if bed:
            safe = shapes[bed].buffer(-radius - 2.01, quad_segs=64).difference(obstacles.buffer(radius + 4.01, quad_segs=64))
            require(not safe.is_empty, 'Original bed has no full-crown-safe position')
            moved = point if safe.covers(point) else nearest_points(point, safe)[1]
            xy = list(moved.coords[0])
            root_z = max(p[2] for p in points[bed]) + .2
            domain = shapes[bed]
            evidence = 'NEAREST_SAFE_ROOT_INSIDE_UNCHANGED_SOURCE_MULCH'
        else:
            xy = center
            moved = point
            root_z = minimum[2]
            domain = original_envelope
            evidence = 'EXACT_SOURCE_ROOT_OUTSIDE_TWO_MULCH_BEDS_WITHIN_ORIGINAL_CARD_ENVELOPE'
        # Boundary distance verifies a complete circular canopy, independent of
        # discretised circle rendering and including all possible yaw directions.
        edge_distance, step_distance = moved.distance(domain.boundary), moved.distance(obstacles)
        require(domain.covers(moved) and edge_distance >= radius, 'Full ornamental crown leaves source domain')
        require(step_distance >= radius + 4, 'Full ornamental crown obstructs original steps')
        if bed:
            require(moved.distance(shapes[bed].boundary) >= radius + 2, 'Bed safety margin lost')
        displacement = math.dist(center, xy)
        require(displacement <= 60, 'Unexpectedly large ornamental root move')
        a, b = max(itertools.combinations(original, 2), key=lambda pair: math.dist(pair[0][:2], pair[1][:2]))
        yaw = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        placement = {'id': 'garden_ornamental_' + str(index), 'role': 'ornamental', 'form': form,
                     'sourceIds': identities, 'sourceBedId': bed, 'positionCm': [*xy, root_z],
                     'heightCm': heights[index], 'radiusCm': radius, 'yawDeg': yaw,
                     'sourcePositionCm': [*center, minimum[2]], 'rootDisplacementCm': displacement,
                     'evidence': evidence, 'cullEndCm': 18000, 'collision': 'NoCollision'}
        placements.append(placement)
        audits.append({'id': placement['id'], 'insideOriginalBed': bool(bed),
                       'originalCardEnvelopeCm': list(original_envelope.exterior.coords),
                       'sourceDomainRingCm': list(domain.exterior.coords),
                       'minimumDomainEdgeDistanceCm': edge_distance, 'minimumStepDistanceCm': step_distance,
                       'crownToDomainEdgeClearanceCm': edge_distance - radius,
                       'crownToStepClearanceCm': step_distance - radius,
                       'rootDisplacementCm': displacement})
    require(sum(p['sourceBedId'] is None for p in placements) == 3, 'Outside-bed source root count differs')
    inputs = [scene_path, obj_path, Path(__file__).resolve()]
    return {'schemaVersion': 1, 'owner': OWNER, 'status': 'native-compatible-not-native-verified',
            'generatedAt': datetime.now(timezone.utc).isoformat(), 'units': 'centimetres',
            'activeDesign': scene['activeDesign'], 'housePlacement': scene['housePlacement'],
            'sourceSceneSha256': sha(scene_path), 'sourceObjSha256': sha(obj_path), 'generatorSha256': sha(Path(__file__)),
            'inputFiles': {str(path): sha(path) for path in inputs}, 'ornamentalPlacements': placements,
            'hideSourceIds': [identity for p in placements for identity in p['sourceIds']],
            'sourceMulchTrianglesCm': {key: triangles[key] for key in BED_IDS},
            'sourceStepTrianglesCm': {key: triangles[key] for key in STEP_IDS},
            'sourceCardPointsCm': {key: points[key] for key in points if key not in BED_IDS + STEP_IDS},
            'audit': {'status': 'PASS', 'placements': len(placements), 'sourceCards': 36,
                      'insideOriginalBeds': 9, 'outsideOriginalBedsExactXY': 3,
                      'maximumRootDisplacementCm': max(p['rootDisplacementCm'] for p in placements),
                      'minimumCrownToStepClearanceCm': min(p['crownToStepClearanceCm'] for p in audits),
                      'individual': audits},
            'preserved': ['C/B/B', 'both3000mmsetbacks', 'all architecture and original mulch boundaries', 'stepping stones', 'collision'],
            'limits': ['Source garden is an illustrative design, not surveyed vegetation.',
                       'Bounds of actual native ornamental prototypes must still be scaled to this full circular radius.',
                       'Native material/appearance/performance verification remains separate.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(ROOT / 'output/unreal'), 'Use isolated Unreal output')
    require(not (output / 'garden-plan.json').exists(), 'Garden output is immutable; choose a new directory')
    plan = build(args.geometry.resolve())
    write_once(output / 'garden-plan.json', encode(plan))
    summary = {'path': str(output / 'garden-plan.json'), 'sha256': sha(output / 'garden-plan.json'),
               **{key: value for key, value in plan['audit'].items() if key != 'individual'}}
    write_once(output / 'summary.json', encode(summary))
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
