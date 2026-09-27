"""Replace R5 meadow suggestions with bounded native low-poly blade clumps.

Consumes immutable visible meadow geometry; never edits the cadastral surfaces,
garden, road, vineyard, source material recipes or previous generation files.
All vegetation density and heights are visual interpretation, not survey data.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import shapely
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-meadow-blades.py'
RADIUS = 14.
ROAD_CLEARANCE = 16.
LIMIT = 9000.
SPACING = 17.
CHANGED = {'owner', 'generatorSha256', 'derivedFrom', 'meadowBasePlacements', 'meadowBasePolicy'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def write(path, value, compact=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = ((json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode()
            if compact else stable(value))
    with path.open('xb') as stream:
        stream.write(data)


def domains(plan):
    records = {r['meshId']: r for r in plan['surfaces'] if r['material'] == 'context_meadow'}
    all_triangles, all_coords, all_ids, per_surface = [], [], [], {}
    extent = Point(0, 0).buffer(LIMIT, quad_segs=256)
    for mesh in plan['meshes']:
        if mesh['id'] not in records:
            continue
        triangles = []
        for i in range(0, len(mesh['indices']), 3):
            coords = [mesh['verticesCm'][j] for j in mesh['indices'][i:i + 3]]
            triangle = Polygon([p[:2] for p in coords])
            if triangle.area < .00001:
                continue
            triangles.append(shapely.set_precision(triangle, .0001))
            all_triangles.append(triangle)
            all_coords.append(coords)
            all_ids.append(mesh['id'])
        shape = unary_union(triangles).intersection(extent)
        if shape.area > 1:
            per_surface[mesh['id']] = shape
    union = unary_union(list(per_surface.values()))
    protected = unary_union([Polygon(tri) for tri in plan['protectedTrianglesCm']])
    # Extra 0.02 cm guards rounding and polygon-buffer approximations. Distances
    # are subsequently checked against exact source boundaries, not just buffers.
    allowed = union.buffer(-RADIUS - .02).difference(protected.buffer(ROAD_CLEARANCE + .02))
    return records, union, protected, allowed, per_surface, all_triangles, np.array(all_coords), all_ids


def sample_ground(x, y, triangles, coords, mesh_ids):
    points = shapely.points(x, y)
    pairs = STRtree(triangles).query(points, predicate='within')
    indices, first = np.unique(pairs[0], return_index=True)
    require(len(indices) == len(points), 'A blade point is outside the original meadow triangles')
    triangle_indices = pairs[1, first]
    tri = coords[triangle_indices]
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    den = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    w1 = ((b[:, 1] - c[:, 1]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (y - c[:, 1])) / den
    w2 = ((c[:, 1] - a[:, 1]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (y - c[:, 1])) / den
    z = w1 * a[:, 2] + w2 * b[:, 2] + (1 - w1 - w2) * c[:, 2]
    return z, [mesh_ids[i] for i in triangle_indices]


def build(plan):
    records, union, protected, allowed, per_surface, triangles, coords, mesh_ids = domains(plan)
    rng = np.random.default_rng(6012262026092606)
    grid = np.arange(-12800., 12801., SPACING)
    gx, gy = np.meshgrid(grid, grid, indexing='ij')
    a = gx.ravel() + rng.uniform(-6, 6, gx.size) + 3 * np.sin(gy.ravel() / 730)
    b = gy.ravel() + rng.uniform(-6, 6, gx.size) + 3 * np.sin(gx.ravel() / 1010 + 1.3)
    yaw = math.radians(31.7)
    x, y = math.cos(yaw) * a - math.sin(yaw) * b, math.sin(yaw) * a + math.cos(yaw) * b
    radial = np.hypot(x, y) <= LIMIT - RADIUS
    x, y = x[radial], y[radial]
    # contains_xy executes in GEOS without allocating millions of Point objects.
    shapely.prepare(allowed)
    inside = shapely.contains_xy(allowed, x, y)
    x, y = x[inside], y[inside]
    available = len(x)
    broad = np.clip(.5 + .27 * np.sin(x / 680 + .6 * np.sin(y / 960)) + .24 * np.cos(y / 510 - x / 1270), 0, 1)
    occupancy = .90 + .08 * broad
    accepted = rng.random(len(x)) < occupancy
    x, y, broad = x[accepted], y[accepted], broad[accepted]
    x, y = np.round(x, 5), np.round(y, 5)
    height = np.round(np.clip(14.5 + 9.8 * broad + .8 * np.sin(x / 155 + y / 210) + rng.uniform(-.45, .45, len(x)), 14, 25), 3)
    angles = np.round(rng.uniform(0, 360, len(x)), 3)
    z, sources = sample_ground(x, y, triangles, coords, mesh_ids)
    placements = [{'role': 'grass', 'positionCm': [float(a), float(b), round(float(c), 5)],
                   'heightCm': float(h), 'radiusCm': RADIUS, 'yawDeg': float(angle),
                   'sourceMeshId': source, 'sourceFinish': records[source]['finish']}
                  for a, b, c, h, angle, source in zip(x, y, z, height, angles, sources)]
    require(350000 <= len(placements) <= 400000, 'Blade instance count outside approved 350k–400k range')
    counts = Counter(sources)
    surface_stats = [{'meshId': identity, 'parcelNumber': records[identity]['parcelNumber'],
                      'finish': records[identity]['finish'], 'areaM2': shape.area / 10000,
                      'instances': counts[identity], 'clustersPerMeadowM2': counts[identity] / (shape.area / 10000)}
                     for identity, shape in per_surface.items()]
    points = shapely.points(x, y)
    edge_clearance = shapely.distance(points, union.boundary)
    road_clearance = shapely.distance(points, protected)
    require(float(edge_clearance.min()) >= RADIUS, 'Full blade crown escapes meadow boundary')
    require(float(road_clearance.min()) >= ROAD_CLEARANCE, 'Blade source road clearance violated')
    density = len(placements) / (union.area / 10000)
    require(density >= 30, 'Global blade density is less than 30 clusters/m²')
    # Five-metre cells quantify continuity without confusing total crown circle
    # area with actual visible leaf coverage; local density fluctuates naturally.
    safe = allowed.intersection(Point(0, 0).buffer(LIMIT - RADIUS, quad_segs=256))
    cell_counts = Counter(zip(np.floor(x / 500).astype(int), np.floor(y / 500).astype(int)))
    tiles = []
    for i in range(-18, 18):
        for j in range(-18, 18):
            area = safe.intersection(box(i * 500, j * 500, (i + 1) * 500, (j + 1) * 500)).area / 10000
            if area >= 10:
                tiles.append({'cell': [i, j], 'safeAreaM2': area, 'instances': cell_counts[(i, j)],
                              'clustersPerSafeM2': cell_counts[(i, j)] / area})
    require(all(t['instances'] > 0 for t in tiles), 'An eligible five-metre meadow tile is empty')
    stats = {'status': 'PASS', 'instances': len(placements), 'meadowSurfaceCount': len(per_surface),
             'eligibleMeadowAreaM2': union.area / 10000, 'safeCenterDomainM2': safe.area / 10000,
             'eligibleGridCells': available, 'acceptedGridFraction': len(placements) / available,
             'clustersPerMeadowM2': density, 'shoulderInstances': sum(r['instances'] for r in surface_stats if r['finish'] == 'shoulder'),
             'minimumMeadowEdgeClearanceCm': float(edge_clearance.min()),
             'minimumProtectedClearanceCm': float(road_clearance.min()),
             'maximumCrownDistanceFromOriginCm': float(np.hypot(x, y).max()) + RADIUS,
             'groundMethod': 'Exact barycentric Z on unchanged original context_meadow triangles',
             'groundRoundingMaximumErrorCm': .000005, 'perSurface': surface_stats,
             'fiveMetreTileCount': len(tiles), 'emptyFiveMetreTileCount': 0,
             'minimumFiveMetreTileClustersPerSafeM2': min(t['clustersPerSafeM2'] for t in tiles),
             'fiveMetreTiles': tiles,
             'coverageLimitation': 'Cluster density and crowns are not measured opaque blade coverage or native performance proof'}
    policy = {'source': 'Frozen R5 context_meadow triangles; all source surfaces unchanged',
              'placementEvidence': 'ILLUSTRATIVE_CONTINUOUS_LOW_GRASS_NOT_SURVEYED',
              'gridSpacingCm': SPACING, 'cellJitterCm': 6, 'gridRotationDegrees': 31.7,
              'longWarpAmplitudeCm': 3, 'occupancyRange': [.90, .98],
              'densityFieldMetreScales': [5.1, 6.8, 9.6, 12.7], 'heightRangeCm': [14, 25],
              'radiusCm': RADIUS, 'protectedSourceMinimumCenterClearanceCm': ROAD_CLEARANCE,
              'maximumDistanceFromOriginCm': LIMIT, 'cullStartCm': 7200, 'cullEndCm': LIMIT,
              'nativeRole': 'Original nativeLawnTuft0–3 with blade_material, no scanned Bermuda or companion groundcover',
              'nativeScaleRequirement': 'Scale every LOD full world XY footprint to radius <=14cm; height14–25cm',
              'allVisualsNoCollision': True, 'audit': {k: v for k, v in stats.items() if k != 'fiveMetreTiles'}}
    return placements, policy, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--metadata-only', action='store_true', help='Correct generator metadata on frozen blades without regenerating any placement')
    args = parser.parse_args()
    base = args.base_plan.resolve()
    output = args.output.resolve()
    require(output.is_relative_to(ROOT / 'output/unreal'), 'Output must be inside output/unreal')
    require(not output.exists(), 'Immutable generation requires a new output directory')
    plan = json.loads(base.read_text())
    require(('meadowBladePlacements' in plan and 'meadowBasePlacements' not in plan) if args.metadata_only else
            ('meadowBasePlacements' in plan and 'meadowBladePlacements' not in plan), 'Unexpected base meadow revision')
    preserve = {k: hashlib.sha256(stable(v)).hexdigest() for k, v in plan.items() if k not in CHANGED}
    previous_generator = plan['generatorSha256']
    if args.metadata_only:
        removed = {}
        placements, policy = plan['meadowBladePlacements'], plan['meadowBladePolicy']
        stats = json.loads((base.parent / 'meadow-blade-audit.json').read_text())
        snapshot = base.parent / 'inputs/exterior-meadow-blades-r6.py'
        require(sha(snapshot) == previous_generator, 'Frozen source snapshot does not match previous generator')
    else:
        removed = {k: {'sha256': hashlib.sha256(stable(plan[k])).hexdigest(),
                       'count': len(plan[k]) if isinstance(plan[k], list) else None}
                   for k in ('meadowBasePlacements', 'meadowBasePolicy')}
        del plan['meadowBasePlacements'], plan['meadowBasePolicy']
        placements, policy, stats = build(plan)
    plan['meadowBladePlacements'], plan['meadowBladePolicy'] = placements, policy
    plan['owner'] = OWNER
    plan['generatorSha256'] = sha(__file__)
    plan['derivedFrom'] = {'path': str(base), 'sha256': sha(base), 'generatorSha256': previous_generator,
                           'preservedFieldHashes': preserve, 'removedFields': removed,
                           'changeScope': ('Generator owner/hash metadata only; every geometry and placement field exactly unchanged' if args.metadata_only else
                                           'Replace only R5 meadow base with native low-poly blades; geometry and other placement arrays unchanged')}
    parent_env = base.parent / 'build-environment.json'
    paths = [base, parent_env, Path(__file__).resolve(), Path(sys.executable).resolve(), Path(shapely.__file__).resolve(), Path(np.__file__).resolve()]
    if args.metadata_only:
        paths += [snapshot, base.parent / 'generator-source-snapshot.json', base.parent / 'meadow-blade-audit.json']
    parent_inputs = json.loads(parent_env.read_text())['inputFiles']
    inputs = {**parent_inputs, **{str(p): sha(p) for p in paths}}
    require(all(sha(p) == expected for p, expected in inputs.items()), 'A frozen input has changed')
    for name in ('cuzk-parcels.gml', 'source-receipt.json'):
        path = output / 'inputs' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write((base.parent / 'inputs' / name).read_bytes())
        inputs[str(path)] = sha(path)
    environment = {'python': sys.version, 'pythonExecutable': sys.executable, 'numpy': np.__version__,
                   'shapely': shapely.__version__, 'geos': shapely.geos_version_string,
                   'inputFiles': inputs, 'role': 'Native blade meadow with correctly pinned generator owner; source geometry preserved'}
    write(output / 'build-environment.json', environment)
    write(output / 'meadow-blade-audit.json', stats)
    write(output / 'context-plan.json', plan, compact=True)
    summary = {'plan': str(output / 'context-plan.json'), 'sha256': sha(output / 'context-plan.json'),
               'meadowBlades': len(placements), 'clustersPerMeadowM2': stats['clustersPerMeadowM2'],
               'shoulderInstances': stats['shoulderInstances'], 'meshes': len(plan['meshes']),
               'triangles': sum(len(m['indices']) // 3 for m in plan['meshes']),
               'generatorSha256': plan['generatorSha256'], 'sourceGeometryUnchanged': True}
    write(output / 'summary.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
