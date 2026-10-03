"""Independent source proof and comparison for an unintegrated transition study."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageDraw
import shapely
from shapely.geometry import Point, Polygon, shape
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighborhood-transition-validation.py'
PLAN = ROOT / 'output/unreal/exterior-neighborhood-transition-20261001-r1-study/transition-plan.json'
SOURCE = ROOT / 'scripts/unreal/exterior-neighborhood-transition-study.py'
CONTEXT = ROOT / 'output/unreal/exterior-context-20260927-r8/context-plan.json'
NEIGHBORHOOD = ROOT / 'output/unreal/exterior-context-20260930-r3/neighborhood-details.json'
BUILDINGS = ROOT / 'output/unreal/exterior-buildings-20260926-r2/building-plan.json'
MASTERS = ROOT / 'output/unreal/exterior-assets-greenery-20260930-r5/geometry-manifest.json'
NATIVE = ROOT / 'output/unreal/exterior-20261001-r10'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while data := stream.read(1024 * 1024):
            h.update(data)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write('\n')


def mesh_shape(mesh):
    points = np.asarray(mesh['verticesCm'])[:, :2]
    ids = np.asarray(mesh['indices']).reshape(-1, 3)
    return unary_union([Polygon(tri) for tri in points[ids]])


def decode_glb_positions(path, node):
    raw = Path(path).read_bytes()
    require(struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw)), 'Bad prototype GLB header')
    size, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a, 'GLB JSON missing')
    gltf = json.loads(raw[20:20 + size])
    start = 20 + size
    length, kind = struct.unpack_from('<II', raw, start)
    require(kind == 0x004e4942 and start + 8 + length == len(raw), 'GLB binary extent differs')
    binary = raw[start + 8:]
    mesh = next(row for row in gltf['meshes'] if row['name'] == node)
    primitive = mesh['primitives'][0]
    position = gltf['accessors'][primitive['attributes']['POSITION']]
    view = gltf['bufferViews'][position['bufferView']]
    require(position['componentType'] == 5126 and position['type'] == 'VEC3' and 'byteStride' not in view, 'Position layout differs')
    points = np.frombuffer(binary, '<f4', count=position['count'] * 3,
                           offset=view.get('byteOffset', 0) + position.get('byteOffset', 0)).reshape(-1, 3)
    index = gltf['accessors'][primitive['indices']]
    require(index['type'] == 'SCALAR' and index['count'] % 3 == 0, 'Triangle index layout differs')
    return points[:, [0, 2, 1]].astype(np.float64) * 100, index['count'] // 3


def source_domains():
    context, neighborhood, buildings = map(read, (CONTEXT, NEIGHBORHOOD, BUILDINGS))
    numbers = {row['parcelNumber'] for row in neighborhood['groundDetails']
               if row['authoredLandUse'] == 'ILLUSTRATIVE_MIXED_FALLOW_AND_WORN_ACCESS_UNBUILT'}
    expected_ids = {row['meshId'] for row in context['surfaces'] if row['parcelNumber'] in numbers
                    and row['finish'] == 'surface' and row['material'] in ('context_meadow', 'context_fallow')}
    meshes = {mesh['id']: mesh for mesh in context['meshes'] if mesh['id'] in expected_ids}
    domain = unary_union([mesh_shape(mesh) for mesh in meshes.values()])
    protected = unary_union([Polygon(row) for row in context['protectedTrianglesCm']])
    roads = unary_union([mesh_shape(mesh) for mesh in context['meshes'] if mesh['material'] == 'context_track'])
    built = unary_union([Polygon(rings[0], rings[1:]) for building in buildings['buildings'] for rings in building['polygonsCm']])
    allowed = domain.difference(protected.buffer(30).union(roads.buffer(20)).union(built.buffer(150)))
    exposure = unary_union([mesh_shape(mesh) for mesh in neighborhood['meshes'] if mesh['material'] == 'context_soil_exposure'])
    band = allowed.intersection(exposure.buffer(34)).difference(exposure.buffer(.1))
    return context, meshes, allowed, exposure, band


def validate(plan, domains=None):
    require(plan['owner'] == 'scripts/unreal/exterior-neighborhood-transition-study.py' and plan['generatorSha256'] == sha(SOURCE), 'Generator pin differs')
    require(plan['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'} and
            plan['housePlacement']['streetSetbackMm'] == plan['housePlacement']['eastSetbackMm'] == 3000, 'Canonical C/B/B or placement differs')
    require(plan['sourceContext'] == {'path': str(CONTEXT), 'sha256': sha(CONTEXT)} and
            plan['sourceNeighborhood'] == {'path': str(NEIGHBORHOOD), 'sha256': sha(NEIGHBORHOOD)}, 'Original context/removals differ')
    for path, digest in plan['inputFiles'].items():
        require(sha(path) == digest, 'Current input differs: ' + path)
    context, meshes, allowed, exposure, band = domains or source_domains()
    ground_shapes, ground_vertices, ground_ids = [], [], []
    for identity, mesh in meshes.items():
        points = np.asarray(mesh['verticesCm'])
        for indices in np.asarray(mesh['indices']).reshape(-1, 3):
            xyz = points[indices]
            ground_shapes.append(Polygon(xyz[:, :2]))
            ground_vertices.append(xyz)
            ground_ids.append(identity)
    ground_index = STRtree(ground_shapes)
    require(shape(plan['targetGroundDomainCm']).symmetric_difference(allowed).area < .01 and
            shape(plan['edgeDomainCm']).symmetric_difference(band).area < .01, 'Self-declared domain differs from actual original source')
    bindings = plan['materialBindingProposal']
    require(len(bindings) == len(meshes) == 65 and {row['sourceMeshId'] for row in bindings} == set(meshes), 'Exact target source mesh set differs')
    for row in bindings:
        original = meshes[row['sourceMeshId']]
        digest = hashlib.sha256(json.dumps(original, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        require(row['sourceGeometrySha256'] == digest and row['expectedMaterialKey'] == original['material'] and
                row['proposedSharedMaterialKey'] == 'context_continuous_unbuilt_ground', 'Geometry/material override scope differs')
    actual = {row['id']: row for row in read(MASTERS)['meshes']}
    prototypes = {}
    for row in plan['prototypes']:
        require(row == actual[row['id']] and sha(row['glbPath']) == row['glbSha256'], 'Prototype is no longer original source')
        levels = [decode_glb_positions(row['glbPath'], level['nodeName']) for level in row['lods']]
        for (_, triangles), expected in zip(levels, row['lods']):
            require(triangles == expected['triangles'], 'Actual source triangles differ')
        points = np.concatenate([value[0] for value in levels])
        prototypes[row['id']] = (points, [value[1] for value in levels])
    require(set(prototypes) == {'grass_medium_02_a', 'grass_medium_02_b', 'grass_medium_02_c'}, 'Prototype scope differs')
    # Reuse is licensed/pixel-exact only after checking actual original maps;
    # a saved recipe alone does not prove files are still the source bytes.
    native_report = read(NATIVE / 'exterior-import-report.json')
    leaf_recipe = native_report['materials']['materials']['ph_grass_medium_02']['recipe']
    require(leaf_recipe['sourceUrl'] == 'https://polyhaven.com/a/grass_medium_02' and leaf_recipe['license'] == 'CC0-1.0',
            'Original leaf material provenance differs')
    leaf_pins = {}
    for role, value in leaf_recipe['maps'].items():
        require(sha(value['path']) == value['sha256'], 'Original leaf source pixels differ: ' + role)
        leaf_pins[value['path']] = value['sha256']
    counters = [0, 0, 0]
    crowns = []
    min_clearance, max_radius, min_height, max_height = math.inf, 0., math.inf, 0.
    for row in plan['transitionPlacements']:
        points, triangles = prototypes[row['meshId']]
        scales = row['scale']
        require(len(scales) == 3 and scales[0] == scales[1] == scales[2] and .1 <= scales[0] <= .6, 'Unexpected compact source scale')
        radius = float(np.linalg.norm(points[:, :2], axis=1).max()) * scales[0]
        height = float(np.ptp(points[:, 2])) * scales[0]
        require(abs(radius - row['radiusCm']) < 1e-6 and abs(height - row['actualHeightCm']) < 1e-6
                and 3.8 - 1e-6 <= height <= 7 + 1e-6, 'Declared source envelope differs from all decoded LOD points')
        require(abs(row['positionCm'][2] + points[:, 2].min() * scales[0] - row['sourceGroundZCm']) < 1e-6,
                'Lowest decoded source root loses ground contact')
        xy = np.asarray(row['positionCm'][:2])
        hits = list(ground_index.query(Point(xy), predicate='intersects'))
        require(hits, 'New root is not on an actual source ground triangle')
        heights = []
        for identity in hits:
            xyz = ground_vertices[int(identity)]
            a, b, c = xyz[:, :2]
            determinant = lambda p, q: p[0] * q[1] - p[1] * q[0]
            denominator = determinant(b - a, c - a)
            v = determinant(xy - a, c - a) / denominator
            w = determinant(b - a, xy - a) / denominator
            heights.append((float(np.asarray([1 - v - w, v, w]) @ xyz[:, 2]), ground_ids[int(identity)]))
        actual_z = max(value[0] for value in heights)
        require(abs(row['sourceGroundZCm'] - actual_z) < 1e-6 and row['sourceGroundMeshId'] in {value[1] for value in heights},
                'Untrusted declared ground Z/mesh differs from actual source triangles')
        # Convex circumscribed envelope contains every decoded vertex, and thus
        # every indexed triangle. The +.1cm circle exceeds the polygon's chord
        # sagitta; this avoids relying on inscribed-circle or midpoint claims.
        require((radius + .1) * math.cos(math.pi / 64) > radius, 'Circle envelope is not conservative')
        crown = Point(row['positionCm'][:2]).buffer(radius + .1, quad_segs=16)
        crowns.append(crown)
        counters = [a + b for a, b in zip(counters, triangles)]
        max_radius, min_height, max_height = max(max_radius, radius), min(min_height, height), max(max_height, height)
    # Vectorized GEOS checks verify full crowns, not roots or selected points.
    require(all(shapely.covers(allowed, crowns)) and not any(shapely.intersects(exposure, crowns)) and
            all(shapely.covers(band, crowns)), 'Actual all-LOD crown leaves allowed source band or overlaps protected/soil domain')
    require(counters == plan['summary']['allLodTriangles'] and counters[0] <= 6500000 and
            len(crowns) == plan['summary']['transitionInstances'] == 7000, 'Decoded population/budget differs')
    groups = plan['groups']
    require(len({row['id'] for row in groups}) == len(groups) == plan['summary']['transitionGroups'] and
            sum(len(row['instances']) for row in groups) == len(crowns), 'Group count differs')
    expected = [(row['meshId'], tuple(row['positionCm']), row['yawDeg'], tuple(row['scale'])) for row in plan['transitionPlacements']]
    actual_instances = [(group['meshId'], tuple(row['positionCm']), row['yawDeg'], tuple(row['scale'])) for group in groups for row in group['instances']]
    require(sorted(expected) == sorted(actual_instances), 'Grouped native transform inputs differ')
    require(all(row['collision'] == 'NoCollision' and row['castShadow'] is False and row['qualityDetail'] is False
                and (row['cullStartCm'], row['cullEndCm']) == (3200, 4000) for row in groups), 'Visual-only native group policy differs')
    texture = plan['conditionTexture']
    require(sha(texture['path']) == texture['sha256'] and texture['worldCmToUvRows'] == [[1 / 36000, 0, .5], [0, -1 / 36000, .5]]
            and texture['worldBoundsCm'] == [-18000., -18000., 18000., 18000.] and texture['sRGB'] is False, 'Condition texture/world mapping differs')
    pixels = np.asarray(Image.open(texture['path']))
    require(pixels.shape == (1024, 1024, 4) and np.all(pixels[:, :, 1] == 255) and np.all(pixels[:, :, 2] == 0)
            and np.all(pixels[:, :, 3] == 255) and pixels[:, :, 0].min() >= 38 and pixels[:, :, 0].max() <= 217, 'Condition channels/ranges differ')
    spec = importlib.util.spec_from_file_location('study_condition', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    coordinate = -18000 + (np.arange(1024) + .5) * 36000 / 1024
    xx, yy = np.meshgrid(coordinate, coordinate[::-1])
    expected_pixels = np.rint(module.condition(xx, yy) * 255).astype(np.uint8)
    require(np.array_equal(pixels[:, :, 0], expected_pixels), 'Condition texture has parcel-dependent or altered pixels')
    return {'status': 'verified-source-neighborhood-transition-study-native-pending', 'sourceMeshes': 65,
            'instances': len(crowns), 'groups': len(groups), 'allLodTriangles': counters,
            'sourceOnly': True, 'actualDecodedAllLodCrownsOutsideSoilAndInsideAllowedGround': True,
            'heightCm': [min_height, max_height], 'maximumCrownRadiusCm': max_radius,
            'conditionExactGeneratedPixelsVerified': True, 'originalGroundPrivateCollisionAndRemovalsUnchanged': True,
            'actualHighestRenderedSourceTriangleGroundZVerified': True, 'originalLeafMaterialInputPins': leaf_pins,
            'nativeVisualAccepted': False, 'performanceAccepted': False}


def project(view, point):
    eye = np.asarray(view['eyeCm'])
    forward = np.asarray(view['targetCm']) - eye
    forward /= np.linalg.norm(forward)
    right = np.asarray([-forward[1], forward[0], 0.])
    right /= np.linalg.norm(right)
    up = np.cross(forward, right)
    delta = np.asarray(point) - eye
    depth = delta @ forward
    tan = math.tan(math.radians(view['horizontalFovDegrees'] / 2))
    return [float(960 + 960 * (delta @ right) / (depth * tan)),
            float(540 - 960 * (delta @ up) / (depth * tan))]


def figures(output, plan):
    context = read(CONTEXT)
    target = {row['sourceMeshId']: row['expectedMaterialKey'] for row in plan['materialBindingProposal']}
    shapes = [(mesh_shape(mesh), target[mesh['id']]) for mesh in context['meshes'] if mesh['id'] in target]
    index = STRtree([row[0] for row in shapes])
    texture = np.asarray(Image.open(plan['conditionTexture']['path']))[:, :, 0] / 255
    width, height = 1200, 700
    image = Image.new('RGB', (width, height), '#f5f5f0')
    draw = ImageDraw.Draw(image)
    draw.text((20, 15), 'SOURCE COVER-MIX PARAMETERS ONLY / NO NATIVE RENDER OR LIGHTING', fill='#242424')
    draw.text((30, 48), 'R10: parcel-label meadow/fallow step', fill='#242424')
    draw.text((625, 48), 'Proposal: continuous world condition', fill='#242424')
    xmin, ymin, xmax, ymax = 4200., 14000., 7400., 18000.
    size = (540, 580)
    field = np.zeros((size[1], size[0], 3), np.uint8)
    old = field.copy()
    for py in range(size[1]):
        y = ymax - (py + .5) / size[1] * (ymax - ymin)
        for px in range(size[0]):
            x = xmin + (px + .5) / size[0] * (xmax - xmin)
            hits = index.query(Point(x, y), predicate='intersects')
            if len(hits):
                previous = .74 if shapes[int(hits[0])][1] == 'context_meadow' else .34
                u = min(1023, max(0, int((x + 18000) / 36000 * 1024)))
                v = min(1023, max(0, int((18000 - y) / 36000 * 1024)))
                after = .34 + .4 * texture[v, u]
                # This is a legend color for cover fraction, not sampled albedo.
                old[py, px] = [int(145 - 90 * previous), int(95 + 65 * previous), int(46 + 12 * previous)]
                field[py, px] = [int(145 - 90 * after), int(95 + 65 * after), int(46 + 12 * after)]
            else:
                old[py, px] = field[py, px] = [212, 212, 205]
    image.paste(Image.fromarray(old), (30, 80))
    image.paste(Image.fromarray(field), (625, 80))
    draw.text((30, 667), 'Identical source XY extent4200..7400 /14000..18000cm; legal/source triangles retained.', fill='#242424')
    image.save(output / 'source-cover-condition-comparison.png')
    viewpoints = read(NATIVE / 'Project/BreziTwin/Content/Data/viewpoints.json')['views']
    view = next(row for row in viewpoints if row['id'] == 'exterior-canopy-lod')
    corner_xy = [5698.608659454598, 16232.8]
    mesh = next(row for row in context['meshes'] if row['id'] == 'context_surface_6035_19_surface_79')
    vertex = min(mesh['verticesCm'], key=lambda point: math.dist(point[:2], corner_xy))
    receipt = {'sourceCornerCm': vertex, 'sourceProjectedPixel': project(view, vertex), 'observedNativeCornerApproxPixel': [1045, 756],
               'nativeCapture': {'path': str(ROOT / 'output/unreal/exterior-validation-20260930-r1/qa/after-exterior-r10-artifacts-1790841238025/exterior-canopy-lod-day-retina-cinematic-static-67daf34e-b07e-4583-afc0-b494efd9e541/capture.png'),
                                  'sha256': sha(ROOT / 'output/unreal/exterior-validation-20260930-r1/qa/after-exterior-r10-artifacts-1790841238025/exterior-canopy-lod-day-retina-cinematic-static-67daf34e-b07e-4583-afc0-b494efd9e541/capture.png')},
               'method': 'Actual source corner, source FOV and source eye/target matched by native runtime; approximate visually read corner, no GPU depth claim.'}
    write(output / 'source-corner-projection.json', receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=PLAN)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(ROOT / 'output/unreal') and not output.exists(), 'Use fresh validation output')
    plan = read(args.plan)
    result = validate(plan)
    output.mkdir(parents=True)
    figures(output, plan)
    write(output / 'source-proof.json', {'schemaVersion': 1, 'owner': OWNER, 'generatorSha256': sha(__file__),
                                       'generatedAtUtc': datetime.now(timezone.utc).isoformat(), 'plan': {'path': str(args.plan.resolve()), 'sha256': sha(args.plan)},
                                       'validation': result, 'unitTestsCounted': 0, 'nativeVisualAccepted': False, 'performanceAccepted': False})
    print(json.dumps({'receipt': str(output / 'source-proof.json'), 'sha256': sha(output / 'source-proof.json'), **result}))


if __name__ == '__main__':
    main()
