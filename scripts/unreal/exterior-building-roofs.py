"""Refine only R1 complex flat roofs into low inferred distance-field roofs.

The official 2D footprints, all facade meshes, foundation samples, terrain frame
and render policy remain unchanged. Roof form and pitch are visual estimates.
"""
import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import shapely
from shapely.geometry import MultiPoint, Point, Polygon

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('base_buildings', ROOT / 'scripts/unreal/exterior-buildings.py')
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
FALLBACK = 'ESTIMATED_FLAT_COMPLEX_FOOTPRINT_FALLBACK'
STYLE = 'ESTIMATED_CAPPED_DISTANCE_HIP_COMPLEX_FOOTPRINT'
CAP_CM = 150.
SLOPE = .65
GRID_CM = 200.


def polygons(shape):
    if shape.is_empty:
        return []
    if shape.geom_type == 'Polygon':
        return [shape] if shape.area > .00001 else []
    if not hasattr(shape, 'geoms'):
        return []
    return [part for child in shape.geoms for part in polygons(child)]


def roof_cells(rings, flat):
    """Interior-point Delaunay clipped exactly to the official polygon.

Boundary samples preserve the eaves; a global 2m grid plus an interior point in
each original constrained triangle supports even narrow wings and courtyards.
This is a coarse visual height field, explicitly not an inferred actual roof.
"""
    shape = Polygon(rings[0], rings[1:])
    points = []
    for ring in rings:
        ring = base.canonical(ring)
        for a, b in zip(ring, ring[1:] + ring[:1]):
            n = max(1, math.ceil(math.dist(a, b) / GRID_CM))
            points.extend([a[k] + (b[k] - a[k]) * j / n for k in (0, 1)] for j in range(n))
    for i in range(0, len(flat['indices']), 3):
        tri = [flat['points'][j] for j in flat['indices'][i:i + 3]]
        # Triangle incenter keeps a meaningful point inside even sliver wings.
        weights = [math.dist(tri[1], tri[2]), math.dist(tri[0], tri[2]), math.dist(tri[0], tri[1])]
        length = sum(weights)
        if length:
            points.append([sum(p[k] * w for p, w in zip(tri, weights)) / length for k in (0, 1)])
    min_x, min_y, max_x, max_y = shape.bounds
    for i in range(math.floor(min_x / GRID_CM), math.ceil(max_x / GRID_CM) + 1):
        for j in range(math.floor(min_y / GRID_CM), math.ceil(max_y / GRID_CM) + 1):
            p = Point(i * GRID_CM, j * GRID_CM)
            if shape.contains(p) and p.distance(shape.boundary) > 10:
                points.append([p.x, p.y])
    triangles = shapely.delaunay_triangles(MultiPoint(points)).geoms
    cells = [cell for tri in triangles for cell in polygons(tri.intersection(shape))]
    base.require(cells, 'Complex footprint produced no roof cells')
    return shape, [[[list(p) for p in cell.exterior.coords]] +
                   [[list(p) for p in ring.coords] for ring in cell.interiors] for cell in cells]


def build(source_path):
    old = base.read(source_path)
    for path, expected in old['inputFiles'].items():
        base.require(base.sha(path) == expected, 'Frozen R1 input differs: ' + path)
    plan = copy.deepcopy(old)
    flat_specs = [(row['id'], index, rings, style)
                  for row in old['buildings']
                  for index, (rings, style) in enumerate(zip(row['polygonsCm'], row['roofStyles']))]
    flat_data = base.triangulate([[base.canonical(ring, index > 0) for index, ring in enumerate(rings)]
                                 for _, _, rings, _ in flat_specs])
    prepared, cells, ranges = {}, [], {}
    for (identity, index, rings, style), flat in zip(flat_specs, flat_data):
        if style == FALLBACK:
            shape, pieces = roof_cells(rings, flat)
            ranges[(identity, index)] = (len(cells), len(cells) + len(pieces))
            cells.extend(pieces)
            prepared[(identity, index)] = shape
    cell_data = base.triangulate(cells)
    roof_chunks, styles, audits = {}, Counter(), []
    data_by_key = {(identity, index): flat for (identity, index, _, _), flat in zip(flat_specs, flat_data)}
    for row in plan['buildings']:
        identity = row['id']
        mesh_id = row['roofMeshId']
        if mesh_id not in roof_chunks:
            roof_chunks[mesh_id] = base.Mesh(mesh_id, row['roofMaterial'])
        mesh = roof_chunks[mesh_id]
        new_styles, details = [], []
        for index, (rings, old_style) in enumerate(zip(row['polygonsCm'], row['roofStyles'])):
            if old_style != FALLBACK:
                style = base.roofs(mesh, rings, row['eaveElevationCm'], row['estimatedRoofRiseCm'], data_by_key[(identity, index)])
                base.require(style == old_style, 'Simple R1 roof style changed unexpectedly')
            else:
                shape = prepared[(identity, index)]
                start, end = ranges[(identity, index)]
                triangle_start = len(mesh.record['indices']) // 3
                max_rise, eave_error = 0., 0.
                for data in cell_data[start:end]:
                    for i in range(0, len(data['indices']), 3):
                        vertices = []
                        for j in data['indices'][i:i + 3]:
                            xy = data['points'][j]
                            distance = Point(xy).distance(shape.boundary)
                            rise = min(CAP_CM, distance * SLOPE)
                            max_rise = max(max_rise, rise)
                            if distance < .00001:
                                eave_error = max(eave_error, rise)
                            vertices.append([*xy, row['eaveElevationCm'] + rise])
                        mesh.triangle(*vertices, [0, 0, 1])
                style = STYLE
                details.append({'polygonIndex': index, 'previousStyle': old_style, 'style': style,
                                'maximumRenderedRiseCm': max_rise, 'maximumEaveRiseErrorCm': eave_error,
                                'triangles': len(mesh.record['indices']) // 3 - triangle_start})
            new_styles.append(style)
            styles[style] += 1
        row['roofStyles'] = new_styles
        if details:
            row['roofRefinement'] = {'evidence': 'AUTHORED_APPROXIMATION_NOT_ROOF_MEASUREMENT',
                                     'capCm': CAP_CM, 'slopeRatio': SLOPE, 'details': details,
                                     'originalR1EstimatedRoofRiseCm': row['estimatedRoofRiseCm']}
            row['estimatedRoofRiseCm'] = max(d['maximumRenderedRiseCm'] for d in details)
            audits.append({'id': identity, **row['roofRefinement']})
    plan['meshes'] = [copy.deepcopy(mesh) if mesh['material'] == 'context_village_wall' else roof_chunks[mesh['id']].record
                      for mesh in old['meshes']]
    base.require(all(len(mesh['indices']) // 3 < 20000 for mesh in plan['meshes']), 'Roof chunk exceeds 20k triangle budget')
    changed = {'meshes', 'buildings', 'generatorSha256', 'owner', 'inputFiles', 'heightPolicy', 'summary', 'limits'}
    plan['derivedFrom'] = {'path': str(source_path), 'sha256': base.sha(source_path),
                           'preservedFieldHashes': {k: hashlib.sha256(base.encode(v)).hexdigest() for k, v in old.items() if k not in changed},
                           'changeScope': 'Complex flat roofs only; footprints/facades/foundations/frame/render policy unchanged'}
    plan['owner'] = 'scripts/unreal/exterior-building-roofs.py'
    plan['generatorSha256'] = base.sha(__file__)
    plan['inputFiles'].update({str(source_path): base.sha(source_path), str(Path(__file__).resolve()): base.sha(__file__)})
    plan['heightPolicy']['complexRoof'] = {'method': 'Clipped interior Delaunay; eavesZ + min(150cm, 0.65 * distanceToOfficialBoundaryCm)',
                                          'maximumRiseCm': CAP_CM, 'slopeRatio': SLOPE, 'interiorGridSpacingCm': GRID_CM,
                                          'allHolesRetained': True, 'evidence': 'ESTIMATED_VISUAL_ROOF_NOT_SURVEYED'}
    plan['summary'].update({'triangles': sum(len(m['indices']) // 3 for m in plan['meshes']), 'roofStyles': dict(styles),
                            'complexBuildingsRefined': len(audits), 'largestChunkTriangles': max(len(m['indices']) // 3 for m in plan['meshes'])})
    plan['limits'] = [line for line in plan['limits'] if 'explicit flat roof fallback' not in line]
    plan['limits'].append('Complex footprints have a capped distance-field hip-like estimate; actual roof shape/pitch/ridge/height are unknown.')
    return plan, {'status': 'GEOMETRY_GENERATED_NOT_NATIVE_VERIFIED', 'refinements': audits, **plan['summary']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    base.require(output.is_relative_to(ROOT / 'output/unreal') and not output.exists(), 'Use a fresh isolated output directory')
    plan, audit = build(args.base_plan.resolve())
    output.mkdir(parents=True)
    for name, value in [('building-plan.json', plan), ('roof-refinement-audit.json', audit)]:
        with (output / name).open('xb') as stream:
            stream.write(base.encode(value))
    summary = {**plan['summary'], 'path': str(output / 'building-plan.json'), 'sha256': base.sha(output / 'building-plan.json')}
    with (output / 'summary.json').open('xb') as stream:
        stream.write(base.encode(summary))
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
