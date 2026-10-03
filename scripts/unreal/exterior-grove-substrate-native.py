"""Independent, read-only validation of a photographic grove floor overlay.

Only ordinary Python is used at native import time. The original ground,
trees, cadastral frame and every source mask remain untouched. Geometry is
measured from the context-compatible vertex/index arrays, rather than from
the authoring receipt's counts or containment assertions.
"""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-grove-substrate-native.py'
GENERATOR = 'scripts/unreal/exterior-grove-substrate.py'
REGION = 'village_nearest_grove'
MATERIAL = 'canopy_floor_litter'
SOURCE_URL = 'https://polyhaven.com/a/forest_leaves_04'
ECOLOGY = ROOT / 'output/unreal/exterior-canopy-ecology-20260930-r3/canopy-ecology-plan.json'
ECOLOGY_SHA = '681d311f3c904ff63a73f085daab3caa04b7ab134ffd84e8c8f2c1a54d5270fa'
INFO_SHA = 'ac5eea16f64d758bb12f67b68b8c609430c1a544e74f61b30105848cf237e90f'
FILES_SHA = '2944bc194c4f8e66a4766a7a36c1e01bd6556d96e09e49104099ecb3b30bb741'
DESIGN = {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
EPS = .00002

spec = importlib.util.spec_from_file_location('grove_substrate_original_constraints',
    ROOT / 'scripts/unreal/exterior-canopy-native.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
require, finite, digest = base.require, base.finite, base.digest


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def pinned(path, expected):
    path = (ROOT / path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == expected,
        'Substrate source path/hash differs: ' + str(path))
    return path


def read_pin(record):
    return json.loads(pinned(record['path'], record['sha256']).read_text())


def _cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _strict_triangle(point, triangle):
    values = [_cross(a, b, point) for a, b in zip(triangle, triangle[1:] + triangle[:1])]
    return min(values) > EPS or max(values) < -EPS


def _proper_intersection(a, b, c, d):
    x, y, u, v = _cross(a, b, c), _cross(a, b, d), _cross(c, d, a), _cross(c, d, b)
    return ((x > EPS and y < -EPS) or (x < -EPS and y > EPS)) and (
        (u > EPS and v < -EPS) or (u < -EPS and v > EPS))


class _PolygonIndex:
    """Exact rings with indexed edge queries and cached ordinary interior cells."""
    def __init__(self, geometry, cell=250.):
        if isinstance(geometry, str):
            geometry = json.loads(geometry)
        source = base._Geo(geometry, cell)
        self.polygons = source.polygons
        self.area = source.area()
        self.cell = cell
        self.edges = source.edges
        self.tiles = source.tiles
        self.interior = {}
        self.rings = []
        for polygon in self.polygons:
            rings = []
            for ring in polygon:
                bands = defaultdict(list)
                for a, b in zip(ring, ring[1:]):
                    for y in range(math.floor(min(a[1], b[1]) / cell),
                                   math.floor(max(a[1], b[1]) / cell) + 1):
                        bands[y].append((a, b))
                rings.append(bands)
            points = polygon[0]
            bounds = [min(p[0] for p in points), min(p[1] for p in points),
                      max(p[0] for p in points), max(p[1] for p in points)]
            self.rings.append((bounds, rings))

    def _ring_inside(self, point, bands):
        inside = False
        x, y = point
        for a, b in bands.get(math.floor(y / self.cell), ()):
            if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
                inside = not inside
        return inside

    def _inside(self, point):
        return any(bounds[0] <= point[0] <= bounds[2] and bounds[1] <= point[1] <= bounds[3]
            and self._ring_inside(point, rings[0])
            and not any(self._ring_inside(point, ring) for ring in rings[1:])
            for bounds, rings in self.rings)

    def _box_edges(self, bounds):
        indices = set()
        for x in range(math.floor(bounds[0] / self.cell), math.floor(bounds[2] / self.cell) + 1):
            for y in range(math.floor(bounds[1] / self.cell), math.floor(bounds[3] / self.cell) + 1):
                indices.update(self.tiles.get((x, y), ()))
        return indices

    def contains(self, point):
        key = (math.floor(point[0] / self.cell), math.floor(point[1] / self.cell))
        if not self.tiles.get(key):
            if key not in self.interior:
                self.interior[key] = self._inside([(v + .5) * self.cell for v in key])
            return self.interior[key]
        if any(base._distance(point, *self.edges[i]) <= EPS for i in self.tiles[key]):
            return True
        return self._inside(point)

    def distance(self, point, limit=215.):
        indices = self._box_edges([point[0] - limit, point[1] - limit,
                                   point[0] + limit, point[1] + limit])
        return min((base._distance(point, *self.edges[i]) for i in indices), default=math.inf)

    def triangle_inside(self, triangle):
        require(all(self.contains(point) for point in triangle),
            'Substrate actual triangle leaves original ecology domain')
        bounds = [min(p[0] for p in triangle), min(p[1] for p in triangle),
                  max(p[0] for p in triangle), max(p[1] for p in triangle)]
        for index in self._box_edges(bounds):
            a, b = self.edges[index]
            if max(a[0], b[0]) < bounds[0] - EPS or min(a[0], b[0]) > bounds[2] + EPS or \
               max(a[1], b[1]) < bounds[1] - EPS or min(a[1], b[1]) > bounds[3] + EPS:
                continue
            require(not (_strict_triangle(a, triangle) or _strict_triangle(b, triangle))
                and not any(_proper_intersection(a, b, c, d)
                    for c, d in zip(triangle, triangle[1:] + triangle[:1])),
                'Substrate actual triangle crosses source domain boundary/hole')


class _Crowns:
    def __init__(self, trees, cell=500.):
        self.cell = cell
        self.tiles = defaultdict(list)
        for row in trees:
            x, y = row['positionCm'][:2]
            radius = row['radiusCm']
            require(finite(row['positionCm'], 3) and math.isfinite(radius) and radius > 0,
                'Substrate original crown source invalid')
            for i in range(math.floor((x - radius) / cell), math.floor((x + radius) / cell) + 1):
                for j in range(math.floor((y - radius) / cell), math.floor((y + radius) / cell) + 1):
                    self.tiles[i, j].append((x, y, (radius + EPS) ** 2))

    def contains(self, point):
        return any((point[0] - x) ** 2 + (point[1] - y) ** 2 <= square
            for x, y, square in self.tiles.get((math.floor(point[0] / self.cell),
                                               math.floor(point[1] / self.cell)), ()))


class _Blockers:
    def __init__(self, masks, cell=500.):
        self.cell = cell
        self.tiles = defaultdict(list)
        for mask in masks:
            for polygon, bounds in zip(mask.polygons, mask.bounds):
                for x in range(math.floor(bounds[0] / cell), math.floor(bounds[2] / cell) + 1):
                    for y in range(math.floor(bounds[1] / cell), math.floor(bounds[3] / cell) + 1):
                        self.tiles[x, y].append(polygon)

    def outside(self, point):
        for polygon in self.tiles.get((math.floor(point[0] / self.cell),
                                        math.floor(point[1] / self.cell)), ()):
            require(not (base._inside_ring(point, polygon[0]) and
                not any(base._inside_ring(point, hole) for hole in polygon[1:]))
                and not any(base._distance(point, a, b) <= EPS
                    for ring in polygon for a, b in zip(ring, ring[1:])),
                'Substrate actual point intersects original private/road/building/agricultural exclusion')


def _png_dimensions(path):
    raw = Path(path).read_bytes()[:24]
    require(raw[:8] == b'\x89PNG\r\n\x1a\n' and raw[12:16] == b'IHDR',
        'Substrate provider image must be original PNG')
    return list(struct.unpack('>II', raw[16:24]))


def _sources(plan, source_context, scene_sha, obj_sha):
    require(plan.get('schemaVersion') == 1 and plan.get('owner') == GENERATOR and
        plan.get('kind') == 'grove-continuous-photographic-substrate' and plan.get('regionId') == REGION,
        'Substrate owner/schema/scope differs')
    require(plan['inputFiles'].get(str(ROOT / GENERATOR)) == sha(ROOT / GENERATOR),
        'Substrate generator pin differs')
    for path, expected in plan['inputFiles'].items():
        pinned(path, expected)
    for key in ('sourceContext', 'sourceEcology', 'sourceTerrain', 'sourceBuildings', 'sourceScene',
                'materialManifest', 'acquisitionManifest'):
        spec = plan[key]
        require(plan['inputFiles'].get(spec['path']) == spec['sha256'],
            'Substrate mandatory source pin missing: ' + key)
    require(read_pin(plan['sourceContext']) == source_context, 'Substrate original source context differs')
    require(Path(plan['sourceEcology']['path']).resolve() == ECOLOGY and
        plan['sourceEcology']['sha256'] == ECOLOGY_SHA,
        'Substrate original frozen ecology source differs')
    ecology = read_pin(plan['sourceEcology'])
    trees = [r for r in source_context['regionalVegetationPlacements'] if r['regionId'] == REGION]
    require(len(trees) == len({r['id'] for r in trees}) == 78 and
        plan['trees'] == ecology['existingTrees'] == trees, 'Substrate original 78 tree roots/order differ')
    require(plan['domainCm'] == ecology['ecologyDomainCm'],
        'Substrate domain differs from original frozen crown/mask intersection')
    require(plan['sourceRegion'] == ecology['sourceRegion'] == next(r for r in
        source_context['regionalVegetationPolicy']['regions'] if r['id'] == REGION),
        'Substrate original grove region differs')
    require(plan['sourceSceneSha256'] == source_context['sourceSceneSha256'] == scene_sha and
        plan['sourceObjSha256'] == source_context['sourceObjSha256'] == obj_sha and
        plan['sourceScene']['sha256'] == scene_sha, 'Substrate scene/OBJ frame differs')
    scene = read_pin(plan['sourceScene'])
    require(plan['activeDesign'] == source_context['activeDesign'] == scene['activeDesign'] == DESIGN and
        plan['housePlacement'] == source_context['housePlacement'] == scene['housePlacement'] and
        plan['housePlacement']['streetSetbackMm'] == plan['housePlacement']['eastSetbackMm'] == 3000,
        'Substrate C/B/B or 3000mm setbacks differ')
    terrain, buildings = read_pin(plan['sourceTerrain']), read_pin(plan['sourceBuildings'])
    for record in (terrain, buildings, ecology):
        # Historical terrain/building receipts predate their explicit OBJ field;
        # their byte-exact old ecology input pins below remain authoritative.
        require(record['sourceSceneSha256'] == scene_sha and record.get('sourceObjSha256', obj_sha) == obj_sha,
            'Substrate source ground/buildings/ecology frame differs')
    require(ecology['sourceContext'] == plan['sourceContext'] and
        ecology['activeDesign'] == DESIGN and ecology['housePlacement'] == plan['housePlacement'],
        'Substrate frozen ecology provenance differs')
    for key, suffix in (('sourceTerrain', 'exterior-terrain-20260926-r4/terrain-plan.json'),
                        ('sourceBuildings', 'exterior-buildings-20260926-r2/building-plan.json'),
                        ('sourceScene', 'realism-20260926-r5/geometry/scene.json')):
        original = [(p, value) for p, value in ecology['inputFiles'].items() if p.endswith(suffix)]
        require(len(original) == 1 and plan[key] == {'path': original[0][0], 'sha256': original[0][1]},
            'Substrate terrain/building/scene source differs from original ecology')
    obj_path = str(Path(plan['sourceScene']['path']).parent / 'dom-mm.obj')
    require(plan['inputFiles'].get(obj_path) == obj_sha and sha(pinned(obj_path, obj_sha)) == obj_sha,
        'Substrate original architectural OBJ pin missing')
    return trees, ecology, scene, terrain, buildings


def _smoothstep(value):
    value = min(1., max(0., value))
    return value * value * (3 - 2 * value)


def _feather_width(point):
    x, y = point
    return 180 + 22 * math.sin(x / 127 + y / 211) + 13 * math.sin(x / 43 - y / 73 + 1.7)


def _validate_photographic_sources(plan):
    acquisition = read_pin(plan['acquisitionManifest'])
    require(acquisition['schemaVersion'] == 1 and acquisition['assetId'] == 'forest_leaves_04'
        and acquisition['sourceUrl'] == SOURCE_URL and acquisition['license'] == 'CC0-1.0'
        and acquisition['physicalTileCm'] == 150 and acquisition['sourcePixelsUnmodified'] is True,
        'Substrate original photographic acquisition identity/scale/license differs')
    info, files = acquisition['infoApi'], acquisition['filesApi']
    require(info['url'] == 'https://api.polyhaven.com/info/forest_leaves_04' and info['sha256'] == INFO_SHA
        and files['url'] == 'https://api.polyhaven.com/files/forest_leaves_04' and files['sha256'] == FILES_SHA,
        'Substrate official frozen provider API response differs')
    for record in (info, files):
        require(plan['inputFiles'].get(record['path']) == record['sha256'],
            'Substrate official provider API source pin missing')
    actual_info, actual_files = read_pin(info), read_pin(files)
    require(len(actual_info['dimensions']) == 2 and
        all(abs(value - 1500) < .001 for value in actual_info['dimensions'])
        and 'Rob Tuytel' in actual_info['authors'], 'Substrate physical provider dimensions/author differs')
    roles = {'albedo': 'Diffuse', 'normal': 'nor_gl', 'roughness': 'Rough', 'displacement': 'Displacement'}
    require(set(acquisition['maps']) == set(roles), 'Substrate original provider map inventory differs')
    native_maps = {}
    for role, provider_role in roles.items():
        record = acquisition['maps'][role]
        provider = actual_files[provider_role]['2k']['png']
        require(record['providerRole'] == provider_role and record['format'] == 'png' and
            record['resolution'] == '2k' and record['sourcePixelsUnmodified'] is True and
            record['url'] == provider['url'] and record['md5'] == provider['md5'] and
            record['bytes'] == provider['size'] and record['width'] == record['height'] == 2048,
            'Substrate map differs from original official provider metadata')
        path = pinned(record['path'], record['sha256'])
        require(plan['inputFiles'].get(record['path']) == record['sha256'],
            'Substrate original provider image pin missing')
        require(path.stat().st_size == provider['size'] and
            hashlib.md5(path.read_bytes()).hexdigest() == provider['md5'] and
            _png_dimensions(path) == [2048, 2048], 'Substrate original provider image bytes/dimensions differ')
        if role != 'displacement':
            native_maps[role] = {'path': record['path'], 'sha256': record['sha256']}
    recipes = read_pin(plan['materialManifest'])
    require(set(recipes) == {MATERIAL}, 'Substrate must introduce exactly one ground recipe')
    recipe = recipes[MATERIAL]
    require(recipe['kind'] == 'ground' and recipe['maps'] == native_maps and recipe['sourceUrl'] == SOURCE_URL
        and recipe['license'] == 'CC0-1.0' and recipe['normalConvention'] == 'OpenGL'
        and recipe['tileCm'] == 150 and recipe['yawDegrees'] == 0 and recipe['featherUV'] is True
        and recipe['stochasticGround'] is False and recipe['cropRows'] is False
        and recipe['distanceFadeCm'] == [12000, 18000] and not recipe.get('groundCover')
        and recipe['opacityMaskClipValue'] == .333,
        'Substrate native material maps/physical UV/full-interior coverage recipe differs')
    return {'nativePhotographicMaps': 3, 'offlineProviderDisplacementMaps': 1,
        'providerPixelsUnchanged': True, 'providerApiInfoSha256': INFO_SHA, 'providerApiFilesSha256': FILES_SHA,
        'physicalTileCm': 150, 'nativeMaterialKey': MATERIAL,
        'materialManifest': deepcopy(plan['materialManifest']), 'acquisitionManifest': deepcopy(plan['acquisitionManifest'])}


def _validate_policy(plan):
    policy = plan['policy']
    expected = {'collision': 'none', 'navigation': False, 'windDisplacementCm': 0,
        'sourceGroundUnchanged': True, 'originalTreesUnchanged': True, 'protectedArchitectureUnchanged': True,
        'sourcePixelsUnmodified': True, 'exactOriginalEcologyDomain': True, 'physicalTileCm': 150,
        'meshStepCm': 12.5, 'featherCm': 180, 'featherWidthRangeCm': [145, 215],
        'featherWidthFormula': '180+22*sin(x/127+y/211)+13*sin(x/43-y/73+1.7), native world cm',
        'coverageFormula': 'smoothstep(0,1,clamp(distance(exactDomainBoundary)/featherWidth,0,1)) in UV0.x;UV0.y=0',
        'fullInteriorOpacity': 1, 'distanceFadeCm': [12000, 18000], 'maxDrawDistanceCm': 18000,
        'microreliefMinCm': .12, 'microreliefMaxCm': .8, 'microreliefPhotoUvRegistered': True,
        'stochasticGround': False, 'nativeAcceptanceRequired': True}
    require(all(policy.get(key) == value for key, value in expected.items()),
        'Substrate collision/frame/full-interior/feather/microrelief policy differs')


def _validate_meshes(meshes, domain, crowns, blockers, ground):
    require(isinstance(meshes, list) and meshes and len({m['id'] for m in meshes}) == len(meshes),
        'Substrate static mesh inventory missing/duplicated')
    counts = Counter()
    measured_ground = Counter()
    points = {}
    point_xy = []
    edges = {}
    area = 0.
    min_relief, max_relief = math.inf, -math.inf
    min_alpha, max_alpha = math.inf, -math.inf
    seen_triangles = set()
    for mesh in meshes:
        require(re.fullmatch(r'context_grove_substrate_[a-z0-9_-]+', mesh['id']) and
            mesh['material'] == MATERIAL and mesh['winding'] == 'clockwise' and
            mesh['nanite'] is False and mesh['collision'] == 'NoCollision' and
            mesh['castShadow'] is False and mesh['maxDrawDistanceCm'] == 18000 and
            not mesh.get('lods') and not mesh.get('groups'), 'Substrate native visual-only mesh policy differs')
        vertices, uvs, normals, indices = (mesh[k] for k in ('verticesCm', 'uvs', 'normals', 'indices'))
        require(vertices and len(vertices) == len(uvs) == len(normals) and indices and len(indices) % 3 == 0
            and all(isinstance(i, int) and not isinstance(i, bool) and 0 <= i < len(vertices) for i in indices),
            'Substrate actual vertex/UV/normal/index inventory differs')
        bounds = {name: [fn(v[i] for v in vertices) for i in range(3)]
            for name, fn in (('min', min), ('max', max))}
        require(mesh['bounds'] == bounds, 'Substrate actual bounds differ')
        require(mesh['sourceGround'] == {'id': 'context_unresolved_flat_backdrop', 'zCm': -25., 'measuredElevation': False},
            'Substrate unresolved source elevation claim differs')
        for point, uv, normal in zip(vertices, uvs, normals):
            require(finite(point, 3) and finite(uv, 2) and finite(normal, 3) and
                abs(math.dist(normal, [0, 0, 0]) - 1) < .002 and normal[2] > .96 and
                0 <= uv[0] <= 1 and uv[1] == 0, 'Substrate actual position/normal/alpha invalid')
            min_alpha, max_alpha = min(min_alpha, uv[0]), max(max_alpha, uv[0])
            if uv[0] <= 1e-8:
                counts['outerAlphaZeroVertices'] += 1
            if uv[0] >= 1 - 1e-12:
                counts['fullInteriorVertices'] += 1
            key = tuple(point[:2])
            if key in points:
                require(abs(points[key][0] - point[2]) < .00001 and abs(points[key][1] - uv[0]) < .00001,
                    'Substrate shared vertex height/alpha seam differs')
                continue
            xy = point[:2]
            require(domain.contains(xy) and crowns.contains(xy), 'Substrate actual point escaped original domain/crown union')
            blockers.outside(xy)
            source_z, source_id = ground.sample(xy)
            relief = point[2] - source_z
            require(source_id == 'context_unresolved_flat_backdrop' and abs(source_z + 25) < 1e-7 and
                .12 - EPS <= relief <= .12 + .68 * uv[0] + EPS,
                'Substrate actual geometry not on original source ground/low relief')
            min_relief, max_relief = min(min_relief, relief), max(max_relief, relief)
            measured_ground[source_id] += 1
            distance = domain.distance(xy)
            expected_alpha = _smoothstep(distance / _feather_width(xy))
            require(abs(uv[0] - expected_alpha) <= .00002,
                'Substrate feather alpha has a core hole or unsafe edge')
            if distance <= EPS:
                require(uv[0] <= .00002, 'Substrate original outer edge alpha must be zero')
            if distance >= 215:
                require(uv[0] >= .99998, 'Substrate full interior alpha must be one')
            points[key] = (point[2], uv[0], len(point_xy))
            point_xy.append(key)
        for offset in range(0, len(indices), 3):
            triangle3 = [vertices[i] for i in indices[offset:offset + 3]]
            triangle = [p[:2] for p in triangle3]
            signed = _cross(*triangle)
            require(signed < -1e-8, 'Substrate actual triangle degenerate or wrong native winding')
            require(max(math.dist(a, b) for a, b in zip(triangle, triangle[1:] + triangle[:1])) <= 12.5 * math.sqrt(2) + EPS,
                'Substrate actual mesh step exceeds independently guarded microgeometry scale')
            triangle_ids = [points[tuple(p)][2] for p in triangle]
            triangle_key = tuple(sorted(triangle_ids))
            require(triangle_key not in seen_triangles, 'Substrate duplicate projected triangle overlap')
            seen_triangles.add(triangle_key)
            for a, b in zip(triangle_ids, triangle_ids[1:] + triangle_ids[:1]):
                key = (min(a, b), max(a, b))
                sign = 1 if a < b else -1
                previous = edges.get(key, (0, 0))
                edges[key] = (previous[0] + 1, previous[1] + sign)
                require(edges[key][0] <= 2, 'Substrate projected topology has overlapping incident triangles')
            area += -signed / 2
            domain.triangle_inside(triangle)
            # Every actual edge midpoint and centroid is checked independently;
            # boundary intersections additionally reject unsampled small holes.
            samples = [[(a[i] + b[i]) / 2 for i in range(2)]
                for a, b in zip(triangle, triangle[1:] + triangle[:1])]
            samples.append([sum(p[i] for p in triangle) / 3 for i in range(2)])
            for xy in samples:
                require(domain.contains(xy) and crowns.contains(xy),
                    'Substrate triangle midpoint/centroid escaped original domain/crowns')
                blockers.outside(xy)
            counts['triangles'] += 1
        counts['vertices'] += len(vertices)
    require(counts['outerAlphaZeroVertices'] > 0 and counts['fullInteriorVertices'] > 0,
        'Substrate needs actual zero-alpha outer edges and opaque interior')
    require(abs(area - domain.area) <= max(.1, domain.area * .000001),
        'Substrate actual triangle area has holes, overlap or changed domain extent')
    boundary_edges = 0
    for (a, b), (count, orientation) in edges.items():
        if count == 2:
            require(orientation == 0, 'Substrate projected triangles have overlapping winding')
        else:
            first, last = point_xy[a], point_xy[b]
            middle = [(first[i] + last[i]) / 2 for i in range(2)]
            require(all(domain.distance(p, 1) <= EPS for p in (first, middle, last)),
                'Substrate actual topology has an interior gap or unmatched seam')
            boundary_edges += 1
    return {'meshes': len(meshes), **dict(counts), 'uniqueVertices': len(points),
        'conformingProjectedBoundaryEdges': boundary_edges,
        'areaM2': area / 10000, 'sourceDomainAreaM2': domain.area / 10000,
        'minimumReliefCm': min_relief, 'maximumReliefCm': max_relief,
        'alphaRange': [min_alpha, max_alpha],
        'actualRenderedGroundSources': dict(measured_ground)}


def validated_substrate(plan, source_context, scene_sha, obj_sha):
    trees, ecology, scene, terrain, buildings = _sources(plan, source_context, scene_sha, obj_sha)
    _validate_policy(plan)
    domain = _PolygonIndex(ecology['ecologyDomainCm'])
    crowns = _Crowns(trees)
    blockers = _Blockers(base._source_constraints(source_context, buildings, scene))
    measured = _validate_meshes(plan['meshes'], domain, crowns, blockers, base._Ground(source_context, terrain))
    photographic = _validate_photographic_sources(plan)
    audit = plan['audit']
    require(audit['status'] == 'PASS_STATIC_CONTINUOUS_PHOTOGRAPHIC_SUBSTRATE_NATIVE_PENDING' and
        audit['nativeVerified'] is False and audit['sourceGroundChanged'] is False and audit['sourcePixelsChanged'] is False
        and audit['originalTrees'] == 78 and audit['meshes'] == measured['meshes']
        and audit['vertices'] == measured['vertices'] and audit['triangles'] == measured['triangles']
        and audit['coreAlphaOneVertices'] == measured['fullInteriorVertices']
        and audit['outerAlphaZeroVertices'] == measured['outerAlphaZeroVertices']
        and abs(audit['domainAreaM2'] - measured['sourceDomainAreaM2']) < 1e-7
        and abs(audit['actualTriangleAreaM2'] - measured['areaM2']) < 1e-7
        and all(abs(a - b) < EPS for a, b in zip(audit['microreliefRangeCm'],
            (measured['minimumReliefCm'], measured['maximumReliefCm'])))
        and all(abs(a - b) < 1e-12 for a, b in zip(audit['alphaRange'], measured['alphaRange'])),
        'Substrate authoring receipt differs from independent actual geometry')
    return {'meshes': deepcopy(plan['meshes']), 'audit': {
        'status': 'verified-source-grove-substrate', 'regionId': REGION, **measured, **photographic,
        'existingTrees': 78, 'deletedTrees': 0, 'hiddenOriginalActors': 0, 'sourceGroundUnchanged': True,
        'allActualTriangleVerticesMidpointsAndCentroidsInsideOriginalCrownUnion': True,
        'allActualTrianglesInsideFrozenEcologyDomainAndSourceExclusions': True,
        'sourceElevationMeasured': False, 'nativeAppearanceAccepted': False,
        'sourceContext': deepcopy(plan['sourceContext']), 'sourceEcology': deepcopy(plan['sourceEcology'])}}
