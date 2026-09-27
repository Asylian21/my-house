"""Official 2D village footprints with explicitly estimated visual volumes.

No native execution. Footprints remain exact in the established C3 frame.
Wall/roof heights, roof construction and colors are authored approximations;
the WFS supplies no populated height or floor-count values for this snapshot.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess

from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-buildings.py'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def read(path):
    return json.loads(Path(path).read_text())


def cross(a, b, p):
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def area(ring):
    return sum(a[0] * b[1] - a[1] * b[0] for a, b in zip(ring, ring[1:] + ring[:1])) / 2


def canonical(ring, clockwise=False):
    points = list(ring[:-1] if ring[0] == ring[-1] else ring)
    return list(reversed(points)) if (area(points) < 0) != clockwise else points


class GroundSampler:
    """Barycentric Z on the exact rendered R4 triangles, including its joins."""
    def __init__(self, plan):
        self.triangles, self.shapes, self.ids = [], [], []
        for mesh in plan['meshes']:
            for i in range(0, len(mesh['indices']), 3):
                tri = [mesh['verticesCm'][j] for j in mesh['indices'][i:i + 3]]
                self.triangles.append(tri)
                self.shapes.append(Polygon([p[:2] for p in tri]))
                self.ids.append(mesh['id'])
        self.index = STRtree(self.shapes)

    def sample(self, xy):
        point = Point(xy)
        results = []
        for i in self.index.query(point):
            a, b, c = self.triangles[int(i)]
            denominator = cross(a, b, c)
            u, v = cross(xy, b, c) / denominator, cross(a, xy, c) / denominator
            w = 1 - u - v
            if min(u, v, w) >= -1e-8:
                results.append((u * a[2] + v * b[2] + w * c[2], self.ids[int(i)]))
        require(results, 'No actual terrain triangle below official footprint ' + str(xy))
        return max(results, key=lambda row: row[0])


class Mesh:
    def __init__(self, identity, material):
        self.record = {'id': identity, 'material': material, 'verticesCm': [], 'indices': [], 'uvs': [],
                       'winding': 'clockwise', 'nanite': False, 'collision': 'NoCollision',
                       'castShadow': True, 'maxDrawDistanceCm': 125000}

    def triangle(self, a, b, c, outward):
        ab, ac = [[p[k] - a[k] for k in range(3)] for p in (b, c)]
        normal = [ac[1] * ab[2] - ac[2] * ab[1], ac[2] * ab[0] - ac[0] * ab[2], ac[0] * ab[1] - ac[1] * ab[0]]
        if sum(v*v for v in normal) < 1e-10:
            return
        if sum(normal[k] * outward[k] for k in range(3)) < 0:
            b, c = c, b
        n = len(self.record['verticesCm'])
        self.record['verticesCm'].extend([a, b, c])
        self.record['indices'].extend([n, n + 1, n + 2])
        self.record['uvs'].extend([[p[0] / 100, p[1] / 100] for p in (a, b, c)])

    def face(self, points, outward):
        for i in range(1, len(points) - 1):
            self.triangle(points[0], points[i], points[i + 1], outward)


def triangulate(polygons):
    script = "import earcut,{flatten} from 'earcut'; let s=''; for await(const x of process.stdin)s+=x; console.log(JSON.stringify(JSON.parse(s).map(r=>{const f=flatten(r);return {points:Array.from({length:f.vertices.length/2},(_,i)=>f.vertices.slice(i*2,i*2+2)),indices:earcut(f.vertices,f.holes,2)}})));"
    return json.loads(subprocess.run(['node', '--input-type=module', '-e', script], input=json.dumps(polygons),
                                     text=True, capture_output=True, cwd=ROOT, check=True).stdout)


def simplified_collinear(ring):
    points = canonical(ring)
    changed = True
    while changed and len(points) > 3:
        changed = False
        for i in range(len(points)):
            a, p, b = points[i - 1], points[i], points[(i + 1) % len(points)]
            if abs(cross(a, b, p)) / max(math.dist(a, b), 1e-9) < .1:
                points.pop(i)
                changed = True
                break
    return points


def roofs(mesh, rings, eaves, rise, flat_data):
    shape = Polygon(rings[0], rings[1:])
    outer = simplified_collinear(rings[0])
    rectangle = shape.minimum_rotated_rectangle
    convex = shape.convex_hull.area - shape.area < .01
    if len(rings) == 1 and len(outer) == 4 and convex and shape.area / rectangle.area >= .985:
        if math.dist(outer[0], outer[1]) < math.dist(outer[1], outer[2]):
            outer = outer[1:] + outer[:1]
        a, b, c, d = outer
        near = [(a[k] + d[k]) / 2 for k in (0, 1)]
        far = [(b[k] + c[k]) / 2 for k in (0, 1)]
        length = math.dist(near, far)
        offset = min(length / 2, (math.dist(a, d) + math.dist(b, c)) / 4)
        unit = [(far[k] - near[k]) / length for k in (0, 1)]
        r1, r2 = [[near[k] + unit[k] * offset for k in (0, 1)], [far[k] - unit[k] * offset for k in (0, 1)]]
        require(shape.covers(Point(r1)) and shape.covers(Point(r2)), 'Hipped ridge leaves official footprint')
        a, b, c, d = [[*p, eaves] for p in (a, b, c, d)]
        r1, r2 = [*r1, eaves + rise], [*r2, eaves + rise]
        for face in ([a, b, r2, r1], [b, c, r2], [c, d, r1, r2], [d, a, r1]):
            mesh.face(face, [0, 0, 1])
        return 'ESTIMATED_LOW_HIPPED_RECTANGLE'
    if len(rings) == 1 and convex:
        center = shape.centroid
        apex = [center.x, center.y, eaves + rise]
        for a, b in zip(outer, outer[1:] + outer[:1]):
            mesh.triangle([*a, eaves], [*b, eaves], apex, [0, 0, 1])
        return 'ESTIMATED_LOW_HIPPED_CONVEX'
    for i in range(0, len(flat_data['indices']), 3):
        mesh.triangle(*[[*flat_data['points'][j], eaves] for j in flat_data['indices'][i:i + 3]], [0, 0, 1])
    return 'ESTIMATED_FLAT_COMPLEX_FOOTPRINT_FALLBACK'


def build(footprints_path, terrain_path, context_path, scene_path):
    source, terrain, context, scene = map(read, (footprints_path, terrain_path, context_path, scene_path))
    require(context['sourceSceneSha256'] == terrain['sourceSceneSha256'] == sha(scene_path), 'Building source frame differs')
    require(scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'C/B/B required')
    require(scene['housePlacement']['streetSetbackMm'] == scene['housePlacement']['eastSetbackMm'] == 3000, 'Setbacks changed')
    require(source['sourceEvidence']['heightAvailability']['buildingHeightPopulated'] == 0, 'Review changed source height evidence')
    for path, expected in source['sourceEvidence']['inputFiles'].items():
        require(sha(path) == expected, 'Building audit source pin differs: ' + path)
    import importlib.util
    spec = importlib.util.spec_from_file_location('village_context', ROOT / 'scripts/unreal/exterior-context.py')
    convert = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(convert)
    empty = unary_union([Polygon([convert.to_unreal(p, scene) for p in rings[0]],
                                  [[convert.to_unreal(p, scene) for p in hole] for hole in rings[1:]])
                         for parcel in context['parcels'] if parcel['parcelNumber'].startswith(('6012/', '6035/'))
                         for rings in parcel['polygonsSjtskMm']])
    protected = unary_union([Polygon(tri) for tri in context['protectedTrianglesCm']])
    sampler = GroundSampler(terrain)
    features = [row for row in source['features'] if row['sourceDistanceMetres'] <= 1000]
    flat_polygons = [rings for feature in features for rings in feature['polygonsCm']]
    roof_data = iter(triangulate([[canonical(ring, i > 0) for i, ring in enumerate(rings)] for rings in flat_polygons]))
    chunks, audit, styles, rejected = {}, [], Counter(), []
    for feature in features:
        shape = unary_union([Polygon(rings[0], rings[1:]) for rings in feature['polygonsCm']])
        data_for_feature = [next(roof_data) for rings in feature['polygonsCm']]
        require(feature['footprintValid'] and shape.is_valid, 'Invalid source building footprint')
        if shape.intersection(empty).area > 1 or shape.intersection(protected).area > 1:
            rejected.append(feature['id'])
            continue
        rng = random.Random(int(hashlib.sha256(feature['id'].encode()).hexdigest()[:12], 16))
        wall_height, roof_rise = rng.uniform(280, 330), rng.uniform(140, 175)
        material = 'context_village_darkroof' if rng.random() < .24 else 'context_village_roof'
        centroid = shape.centroid
        cell = (math.floor(centroid.x / 10000), math.floor(centroid.y / 10000))
        cell_name = '_'.join(('m' + str(-v)) if v < 0 else str(v) for v in cell)
        def chunk(mat):
            key = (cell, mat)
            if key not in chunks:
                chunks[key] = Mesh('village_' + cell_name + '_' + mat.replace('context_village_', ''), mat)
            return chunks[key]
        walls, roof = chunk('context_village_wall'), chunk(material)
        samples, perimeter_rings = [], []
        for rings in feature['polygonsCm']:
            subdivided = []
            for i, ring in enumerate(rings):
                points = canonical(ring, i > 0)
                divided = []
                for a, b in zip(points, points[1:] + points[:1]):
                    divisions = math.ceil(math.dist(a, b) / 250)
                    for j in range(divisions):
                        xy = [a[k] + (b[k] - a[k]) * j / divisions for k in (0, 1)]
                        z, source_mesh = sampler.sample(xy)
                        divided.append([*xy, z])
                        samples.append({'xyCm': xy, 'renderedGroundZCm': z, 'terrainMeshId': source_mesh})
                subdivided.append(divided)
            perimeter_rings.append(subdivided)
        eaves = max(row['renderedGroundZCm'] for row in samples) + wall_height
        for rings in perimeter_rings:
            for ring in rings:
                for a, b in zip(ring, ring[1:] + ring[:1]):
                    # Bury the visual foundation 8cm to avoid cracks where the
                    # coarse DEM triangle changes inside a short wall segment.
                    bottom_a, bottom_b = [a[0], a[1], a[2] - 8], [b[0], b[1], b[2] - 8]
                    normal = [b[1] - a[1], -(b[0] - a[0]), 0]
                    walls.face([bottom_a, bottom_b, [b[0], b[1], eaves], [a[0], a[1], eaves]], normal)
        roof_styles = [roofs(roof, rings, eaves, roof_rise, data) for rings, data in zip(feature['polygonsCm'], data_for_feature)]
        styles.update(roof_styles)
        audit.append({'id': feature['id'], 'polygonsCm': feature['polygonsCm'], 'cell': list(cell),
                      'wallMeshId': walls.record['id'], 'roofMeshId': roof.record['id'], 'roofMaterial': material,
                      'sourceDistanceMetres': feature['sourceDistanceMetres'], 'sourceAreaM2': feature['areaM2'],
                      'sourceHorizontalAccuracyM': feature['sourceHorizontalAccuracyM'],
                      'heightEvidence': 'AUTHORED_APPROXIMATION_NO_POPULATED_WFS_HEIGHT_OR_FLOOR_COUNT',
                      'estimatedWallHeightCm': wall_height, 'estimatedRoofRiseCm': roof_rise,
                      'eaveElevationCm': eaves, 'roofStyles': roof_styles,
                      'renderedGroundSamples': samples,
                      'groundRangeCm': [min(p['renderedGroundZCm'] for p in samples), max(p['renderedGroundZCm'] for p in samples)]})
    meshes = [chunk.record for chunk in chunks.values() if chunk.record['indices']]
    require(len(audit) == 651 and not rejected, 'Unexpected source footprints or empty-plot conflicts')
    require(all(len(mesh['indices']) // 3 < 20000 for mesh in meshes), 'Village chunk exceeds triangle budget')
    paths = [Path(__file__).resolve(), ROOT / 'scripts/unreal/exterior-context.py', footprints_path, terrain_path, context_path, scene_path]
    inputs = {str(path): sha(path) for path in paths}
    inputs.update(source['sourceEvidence']['inputFiles'])
    return {'schemaVersion': 1, 'owner': OWNER, 'status': 'native-compatible-not-native-verified',
            'units': 'centimetres', 'meshes': meshes, 'groups': [], 'buildings': audit,
            'activeDesign': scene['activeDesign'], 'housePlacement': scene['housePlacement'],
            'sourceSceneSha256': sha(scene_path), 'sourceObjSha256': context['sourceObjSha256'],
            'generatorSha256': sha(Path(__file__)), 'inputFiles': inputs,
            'sourceEvidence': source['sourceEvidence'], 'terrainPlan': {'path': str(terrain_path), 'sha256': sha(terrain_path)},
            'heightPolicy': {'evidence': 'ESTIMATED_VISUAL_MASSING_NOT_MEASURED_BUILDINGS',
                             'wallHeightRangeCm': [280, 330], 'roofRiseRangeCm': [140, 175],
                             'groundRole': 'Exact barycentric interpolation on rendered terrain R4 including its graphical joins and fallback',
                             'eavesFormula': 'highest sampled perimeter terrain Z + authored wall height',
                             'wallSamplingMaximumSpacingCm': 250, 'foundationBuryCm': 8},
            'renderPolicy': {'chunkCellCm': 10000, 'maxDrawDistanceCm': 125000, 'castShadow': True,
                             'allVisualsNoCollision': True, 'noRoadsAdded': True},
            'summary': {'buildingCount': len(audit), 'sourceFootprintsRejected': rejected, 'meshCount': len(meshes),
                        'chunkCellCount': len({tuple(row['cell']) for row in audit}),
                        'triangles': sum(len(mesh['indices']) // 3 for mesh in meshes), 'roofStyles': dict(styles),
                        'sourceHeightFieldsPopulated': 0},
            'limits': ['Footprints are official 2D source with declared estimated horizontal accuracy 1.5m; no centimetre survey precision claimed.',
                       'All wall heights, roof heights, roof forms and colors are authored conservative approximations.',
                       'Complex footprints use an explicit flat roof fallback; these are not claims of actual roof construction.',
                       'BuildingPart entrance points are excluded, and no volume is invented on development parcels.',
                       'Current WFS footprints and historical DMR terrain have different acquisition dates.',
                       'Native appearance, scale readback and performance remain to be verified.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('footprints', 'terrain', 'context', 'scene', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(ROOT / 'output/unreal'), 'Output must be isolated')
    require(not (output / 'building-plan.json').exists(), 'Building plan is immutable')
    plan = build(args.footprints.resolve(), args.terrain.resolve(), args.context.resolve(), args.scene.resolve())
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'building-plan.json').open('xb') as stream:
        stream.write(encode(plan))
    summary = {**plan['summary'], 'path': str(output / 'building-plan.json'), 'sha256': sha(output / 'building-plan.json')}
    with (output / 'summary.json').open('xb') as stream:
        stream.write(encode(summary))
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
