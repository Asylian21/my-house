"""Independent read-only yard audit: raw OBJ parser, source planes, semantic exclusions.

Does not import exterior-yard, rural-geometry, meadow-blades or their helpers.
Writes only a new audit directory; never modifies the yard or source files.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def polygons(geometry):
    if geometry.geom_type == 'Polygon':
        yield geometry
    elif hasattr(geometry, 'geoms'):
        for child in geometry.geoms:
            yield from polygons(child)


def read_obj_triangles(path, wanted):
    vertices, records, current = [], {key: [] for key in wanted}, None
    with path.open() as stream:
        for line in stream:
            token = line.split()
            if not token:
                continue
            if token[0] == 'v':
                # Scene declaration: OBJ X=planX-centerX, Y=planY-centerY.
                vertices.append([float(token[1]) * .1, -float(token[2]) * .1, float(token[3]) * .1])
            elif token[0] == 'o':
                current = token[1]
            elif token[0] == 'f' and current in records:
                indices = [int(t.split('/')[0]) for t in token[1:]]
                face = [vertices[i-1 if i > 0 else i] for i in indices]
                for i in range(1, len(face)-1):
                    triangle = np.array([face[0], face[i], face[i+1]])
                    if Polygon(triangle[:, :2]).area > 1e-5:
                        records[current].append(triangle)
    return records


def audit(yard_path, output):
    yard_path, output = Path(yard_path).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('Use a new audit directory')
    yard = json.loads(yard_path.read_text())
    source_paths = {Path(path).name: Path(path) for path in yard['inputFiles']}
    scene = json.loads(source_paths['scene.json'].read_text())
    rural = json.loads(source_paths['rural-context-geometry.json'].read_text())
    pins = [{'path': path, 'expected': expected, 'actual': sha(path)} for path, expected in yard['inputFiles'].items()]
    for row in pins:
        row['pass'] = row['expected'] == row['actual']
    objects = {o['id']: o for o in scene['objects'] if o['enabled']}
    source_ids = set(yard['greenSourceMeshIds'])
    soil_materials = {'real-terrain', 'real-grass', 'real-road-reserve'}
    walk_ids = {key for key, row in objects.items() if row.get('metadata', {}).get('walkSurface') and not (set(row['materialNames']) & soil_materials)}
    mulch_ids = {key for key, row in objects.items() if 'real-mulch' in row['materialNames']}
    extra_pool_ids = {key for key, row in objects.items() if 'real-pool-water' in row['materialNames']}
    wanted = walk_ids | mulch_ids | extra_pool_ids
    obj_triangles = read_obj_triangles(source_paths['dom-mm.obj'], wanted)
    obj_shapes = {key: unary_union([Polygon(t[:, :2]) for t in records]) for key, records in obj_triangles.items()}
    empty_objects = [key for key, shape in obj_shapes.items() if shape.is_empty]
    cx, cy = scene['sceneCenterMm']['x'], scene['sceneCenterMm']['y']

    def from_plan(poly):
        return Polygon([((p['x']-cx)*.1, (cy-p['y'])*.1) for p in poly])

    scene_shapes = {key: from_plan(value['polygonMm']) for key, value in scene['surfaces'].items() if isinstance(value, dict) and value.get('polygonMm')}
    managed = unary_union([Polygon(p) for p in rural['managedLawnKeepPolygonsCm']])
    cutouts = unary_union([from_plan(p) for p in scene['lawnCutouts']])
    protected_original = unary_union([*(obj_shapes[key] for key in walk_ids), *scene_shapes.values(), managed])
    protected = unary_union([protected_original, *(obj_shapes[key] for key in mulch_ids | extra_pool_ids), cutouts])
    triangles, coords, identities = [], [], []
    mesh_domains = {}
    for mesh in rural['meshes']:
        if mesh['id'] not in source_ids:
            continue
        v = np.asarray(mesh['verticesCm'], dtype=float)
        local = []
        for ids in np.asarray(mesh['indices']).reshape(-1, 3):
            t = v[ids]
            polygon = Polygon(t[:, :2])
            if polygon.area > 1e-5:
                triangles.append(polygon)
                coords.append(t)
                identities.append(mesh['id'])
                local.append(polygon)
        mesh_domains[mesh['id']] = unary_union(local)
    ground = unary_union(triangles)
    poses = yard['yardBladePlacements']
    positions = np.array([row['positionCm'] for row in poses])
    radii = np.array([row['radiusCm'] for row in poses])
    points = shapely.points(positions[:, :2])
    edge_distance = shapely.distance(points, ground.boundary)
    protected_distance = shapely.distance(points, protected)
    original_distance = shapely.distance(points, protected_original)
    # Exact circular footprint criterion; no approximate polygon-buffer circle.
    outside_ground = ~shapely.covers(ground, points) | (edge_distance < radii - 1e-8)
    crown_collision = protected_distance < radii - 1e-8
    clearance_failure = protected_distance < 18 - 1e-8
    categories = {
        'interiorFloorsAndSlabs': unary_union([obj_shapes[key] for key in walk_ids if objects[key].get('metadata', {}).get('walkSurfaceKind') == 'interior']),
        'roadsPathsStepsDecks': unary_union([obj_shapes[key] for key in walk_ids if objects[key].get('metadata', {}).get('walkSurfaceKind') != 'interior']),
        'mulch': unary_union([obj_shapes[key] for key in mulch_ids]),
        'managedLawn': managed,
        'poolAndLawnCutouts': cutouts,
    }
    category_results = {}
    for key, shape in categories.items():
        distances = shapely.distance(points, shape)
        category_results[key] = {'rootsInside': int(shapely.contains(shape, points).sum()), 'crownsIntersecting': int((distances < radii-1e-8).sum()), 'rootsWithin18Cm': int((distances < 18-1e-8).sum()), 'minimumRootDistanceCm': float(distances.min())}
    # Solve each supporting triangle plane independently using a 3x3 matrix;
    # do not call the generator's barycentric helper or reproduce its formula.
    coords = np.asarray(coords)
    planes = np.linalg.solve(np.concatenate([coords[:, :, :2], np.ones((len(coords), 3, 1))], axis=2), coords[:, :, 2, None])[:, :, 0]
    pairs = STRtree(triangles).query(points, predicate='intersects')
    errors = np.full(len(poses), np.inf)
    supporting = np.zeros(len(poses), dtype=int)
    for point_index, triangle_index in pairs.T:
        if poses[point_index]['sourceMeshId'] != identities[triangle_index]:
            continue
        expected_z = np.dot([*positions[point_index, :2], 1.], planes[triangle_index])
        errors[point_index] = min(errors[point_index], abs(expected_z-positions[point_index, 2]))
        supporting[point_index] += 1
    frame_checks = []
    for surface_key in ('driveway', 'entry', 'sideEntryApproach'):
        semantic = scene['surfaces'][surface_key]['id']
        matching = [key for key in walk_ids if objects[key].get('metadata', {}).get('walkSurfaceId') == 'site-surface-'+semantic]
        obj_shape = unary_union([obj_shapes[key] for key in matching])
        polygon = scene_shapes[surface_key]
        frame_checks.append({'surface': surface_key, 'objects': matching, 'symmetricDifferenceCm2': polygon.symmetric_difference(obj_shape).area, 'hausdorffDistanceCm': polygon.hausdorff_distance(obj_shape)})
    missing_mulch_flag = [{'id': key, 'name': objects[key]['name'], 'rootCountInside': int(shapely.contains(obj_shapes[key], points).sum()), 'rootsWithin18Cm': int((shapely.distance(points, obj_shapes[key]) < 18).sum())} for key in sorted(mulch_ids-walk_ids)]
    findings = []
    if clearance_failure.any():
        findings.append({'severity': 'BLOCKING', 'reason': 'Yard roots violate protected semantic surface clearance', 'indices': np.flatnonzero(clearance_failure).tolist(), 'unflaggedMulchObjects': missing_mulch_flag})
    if not all(row['pass'] for row in pins):
        findings.append({'severity': 'BLOCKING', 'reason': 'An input pin no longer matches the source bytes'})
    expected_frame = scene['units'] == 'millimetres' and rural['units'] == 'centimetres' and (cx, cy) == (15200, 10800)
    checks = {
        'inputPins': all(row['pass'] for row in pins),
        'activeDesignAndSetbacks': scene['activeDesign'] == yard['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'} and scene['house']['placement']['streetSetbackMm'] == scene['house']['placement']['eastSetbackMm'] == 3000,
        'declaredCoordinateFrame': expected_frame,
        'planToObjSurfaceAgreement': all(row['hausdorffDistanceCm'] < 1e-6 for row in frame_checks),
        'selectedGroundMeshes': set(mesh_domains) == source_ids and len(source_ids) == 7,
        'finiteAndUniqueRoots': bool(np.isfinite(positions).all() and len(np.unique(positions, axis=0)) == len(positions)),
        'fullCrownsInsideGroundIncludingHoles': not bool(outside_ground.any()),
        'originalWalkSurfaceExclusions18Cm': bool((original_distance >= 18-1e-8).all()),
        'allSemanticProtectedSurfaces18Cm': not bool(clearance_failure.any()),
        'allSemanticProtectedSurfacesNoCrownOverlap': not bool(crown_collision.any()),
        'sourceTriangleZWithinRoundingTolerance': bool(np.all(errors <= 5.01e-6)),
        'crownRadiusAndHeightRange': bool(np.all((radii > 0) & (radii <= 14)) and all(7 <= row['heightCm'] <= 13 for row in poses)),
        'protectedObjTrianglesPresent': not empty_objects,
    }
    report = {'schema': 1, 'status': 'PASS' if all(checks.values()) else 'FAIL', 'auditMethod': 'Independent raw OBJ parser and semantic selection; exact full-circle distances; NumPy triangle-plane linear solve. No generator/helper imports.', 'yardPath': str(yard_path), 'yardSha256': sha(yard_path), 'auditorSha256': sha(__file__), 'checks': checks, 'inputPins': pins, 'instances': len(poses), 'perSource': dict(Counter(row['sourceMeshId'] for row in poses)), 'minimumGroundBoundaryDistanceCm': float(edge_distance.min()), 'minimumOriginalProtectedRootDistanceCm': float(original_distance.min()), 'minimumAllSemanticProtectedRootDistanceCm': float(protected_distance.min()), 'maximumGroundZErrorCm': float(errors.max()), 'supportingTriangleCountRange': [int(supporting.min()), int(supporting.max())], 'sourceAreaM2': ground.area/10000, 'groundComponents': len(list(polygons(ground))), 'groundHoles': sum(len(poly.interiors) for poly in polygons(ground)), 'fullCrownGroundViolations': int(outside_ground.sum()), 'protectedRootClearanceViolations': int(clearance_failure.sum()), 'protectedCrownIntersections': int(crown_collision.sum()), 'categoryResults': category_results, 'coordinateFrameChecks': frame_checks, 'protectedWalkObjects': sorted(walk_ids), 'allMulchObjects': sorted(mulch_ids), 'missingMulchWalkFlags': missing_mulch_flag, 'findings': findings, 'limitations': ['Source-level placement and geometry audit; native rendering and performance require separate UE capture.', '18 cm is the root-to-protected-surface clearance, leaving at least 4 cm after the 14 cm crown radius.', 'Both current and superseded scene surface polygons are conservatively excluded by the generator; this can leave extra bare area, not grass on paths.', 'This is illustrative green-season cover, not measured current vegetation.']}
    output.mkdir(parents=True)
    (output/'yard-independent-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    # Source-coordinate diagram, not a beauty-render claim.
    # SVG keeps source coordinates inspectable without a plotting dependency.
    xmin, ymin, xmax, ymax = ground.bounds
    width, height, pad = 1100, 1100, 55
    scale = min((width-2*pad)/(xmax-xmin), (height-2*pad)/(ymax-ymin))
    def pixel(x,y):
        return pad+(x-xmin)*scale, height-pad-(y-ymin)*scale
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="1100" height="1100" fill="white"/>',
           f'<text x="55" y="25" font-family="sans-serif" font-size="18">Independent yard audit: {report["status"]} — {len(poses)} roots, {int(clearance_failure.sum())} clearance violations</text>']
    for geometry, color in [(ground, '#ddd6bf'), (protected, '#9298a1'), (managed, '#bad7ce')]:
        for poly in polygons(geometry):
            paths = []
            for ring in [poly.exterior, *poly.interiors]:
                paths.append('M '+' L '.join(f'{x:.3f} {y:.3f}' for x,y in (pixel(x,y) for x,y in ring.coords))+' Z')
            svg.append(f'<path d="{" ".join(paths)}" fill="{color}" fill-rule="evenodd" stroke="white" stroke-width=".3"/>')
    for position,bad in zip(positions,clearance_failure):
        x,y=pixel(*position[:2]);color='#db2937' if bad else '#257246'
        svg.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{1.3 if bad else .7}" fill="{color}"/>')
    svg.extend(['<text x="55" y="1080" font-family="sans-serif" font-size="13">Green: yard roots. Red: protected clearance failure. Grey: hard surfaces/mulch. Blue-green: managed lawn. UE XY frame.</text>', '</svg>'])
    (output/'yard-placement-audit.svg').write_text('\n'.join(svg))
    print(json.dumps({key: report[key] for key in ['status','checks','instances','minimumGroundBoundaryDistanceCm','minimumOriginalProtectedRootDistanceCm','minimumAllSemanticProtectedRootDistanceCm','maximumGroundZErrorCm','protectedRootClearanceViolations','protectedCrownIntersections','categoryResults','missingMulchWalkFlags']},indent=2))
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--yard',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();audit(args.yard,args.output)
