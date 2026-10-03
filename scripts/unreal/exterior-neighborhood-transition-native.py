"""Stdlib source gate for the isolated neighborhood transition study.

This returns binding proposals and additive HISM inputs only. It does not edit
source meshes, restore removed vegetation, create a material, or accept images.
The exact source-derived polygons have a separately pinned GEOS proof; every
decoded all-LOD circular crown is checked again here with ordinary Python.
"""
from collections import defaultdict
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighborhood-transition-native.py'
GENERATOR = 'scripts/unreal/exterior-neighborhood-transition-study.py'
GENERATOR_SHA = '970c87dee543bb7c0097841d67216a52c25f4880fa982d495f21207348957a75'
STUDY = ROOT / 'output/unreal/exterior-neighborhood-transition-20261001-r1-study'
PLAN_SHA = '2be538a9311282d9b8485d925fa070b3984b50cea852ea2e7406ed1699448ef5'
PROOF = ROOT / 'output/unreal/exterior-neighborhood-transition-validation-20261001-r2/source-proof.json'
PROOF_SHA = 'a527c4eda9ecb4ce0823c4128835e541e06cb5e15b9d5296b586d134e3122ce4'
CANOPY_SHA = '2788c643f4bd924f2fa72714d18ad009a7b4aa599ba86df58baf7582f765a172'
SUBSTRATE_SHA = 'c27e3b935d4486e6150e262a8309223e9f72e0ef6abb9f648af5c897283f692e'
DESIGN = {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
IDS = {'grass_medium_02_a', 'grass_medium_02_b', 'grass_medium_02_c'}
ACTUAL_VERTEX_COUNTS = {'grass_medium_02_a': [645, 422, 235],
                       'grass_medium_02_b': [1575, 1082, 602],
                       'grass_medium_02_c': [1072, 724, 418]}
MATERIAL = 'context_continuous_unbuilt_ground'
EPS = .00002


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1048576):
            result.update(block)
    return result.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def finite(value, length):
    return isinstance(value, (list, tuple)) and len(value) == length and all(
        type(v) in (int, float) and math.isfinite(v) for v in value)


def pinned(path, expected):
    path = (ROOT / path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == expected,
            'Transition source pin differs: ' + str(path))
    return path


def read_pin(record):
    return json.loads(pinned(record['path'], record['sha256']).read_text())


def _module(name, filename, expected):
    path = pinned(ROOT / 'scripts/unreal' / filename, expected)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _module('transition_source_geometry', 'exterior-canopy-native.py', CANOPY_SHA)
substrate = _module('transition_source_polygon_index', 'exterior-grove-substrate-native.py', SUBSTRATE_SHA)


def _approved():
    plan = json.loads(pinned(STUDY / 'transition-plan.json', PLAN_SHA).read_text())
    proof = json.loads(pinned(PROOF, PROOF_SHA).read_text())
    require(proof['plan'] == {'path': str(STUDY / 'transition-plan.json'), 'sha256': PLAN_SHA}
            and proof['validation']['status'] == 'verified-source-neighborhood-transition-study-native-pending'
            and proof['unitTestsCounted'] == 0 and proof['nativeVisualAccepted'] is False
            and proof['performanceAccepted'] is False, 'Transition independent source proof differs')
    return plan, proof


def _png_rgba(path):
    """Decode bounded ordinary RGBA8 PNG data, checking every chunk's CRC."""
    raw = Path(path).read_bytes()
    require(raw[:8] == b'\x89PNG\r\n\x1a\n' and len(raw) <= 12_000_000,
            'Transition condition PNG signature/size differs')
    cursor, header, payload, ended = 8, None, bytearray(), False
    while cursor < len(raw):
        require(cursor + 12 <= len(raw), 'Transition PNG chunk is truncated')
        length, kind = struct.unpack_from('>I4s', raw, cursor)
        end = cursor + 12 + length
        require(end <= len(raw) and zlib.crc32(raw[cursor + 4:end - 4]) & 0xffffffff
                == struct.unpack_from('>I', raw, end - 4)[0], 'Transition PNG chunk CRC differs')
        data = raw[cursor + 8:end - 4]
        if kind == b'IHDR':
            require(header is None and cursor == 8 and length == 13, 'Transition PNG header differs')
            header = struct.unpack('>IIBBBBB', data)
        elif kind == b'IDAT':
            require(header is not None and not ended, 'Transition PNG data order differs')
            payload.extend(data)
        elif kind == b'IEND':
            require(length == 0 and end == len(raw), 'Transition PNG end differs')
            ended = True
        else:
            require(kind[0] & 32, 'Transition PNG unsupported critical chunk')
        cursor = end
    require(header == (1024, 1024, 8, 6, 0, 0, 0) and ended,
            'Transition condition must be actual 1024x1024 noninterlaced RGBA8')
    expected_size = 1024 * (4096 + 1)
    decoder = zlib.decompressobj()
    packed = decoder.decompress(payload, expected_size + 1)
    require(len(packed) == expected_size and decoder.eof and not decoder.unused_data,
            'Transition PNG decompressed extent differs')
    rows, previous = [], bytearray(4096)
    for y in range(1024):
        offset = y * 4097
        mode, row = packed[offset], bytearray(packed[offset + 1:offset + 4097])
        require(mode <= 4, 'Transition PNG filter differs')
        for x in range(4096):
            a = row[x - 4] if x >= 4 else 0
            b = previous[x]
            c = previous[x - 4] if x >= 4 else 0
            if mode == 1: predictor = a
            elif mode == 2: predictor = b
            elif mode == 3: predictor = (a + b) // 2
            elif mode == 4:
                p = a + b - c
                distances = [abs(p - a), abs(p - b), abs(p - c)]
                predictor = (a, b, c)[distances.index(min(distances))]
            else: predictor = 0
            row[x] = (row[x] + predictor) & 255
        rows.append(bytes(row))
        previous = row
    return rows


def _axis_condition(coordinate, scale, shift):
    value = coordinate / scale + shift
    integer = math.floor(value)
    fraction = value - integer
    return integer, fraction * fraction * (3 - 2 * fraction)


@lru_cache(maxsize=40000)
def _lattice(x, y, seed):
    value = math.sin(x * 127.1 + y * 311.7 + seed) * 43758.5453
    return value - math.floor(value)


def _condition(x, y):
    result = 0.
    for scale, shift, seed, weight in ((2400, 0, 31, .55), (1200, 17, 67, .30), (400, 39, 109, .15)):
        ix, fx = _axis_condition(x, scale, shift)
        iy, fy = _axis_condition(y, scale, shift)
        lo = _lattice(ix, iy, seed) * (1 - fx) + _lattice(ix + 1, iy, seed) * fx
        hi = _lattice(ix, iy + 1, seed) * (1 - fx) + _lattice(ix + 1, iy + 1, seed) * fx
        result += (lo * (1 - fy) + hi * fy) * weight
    return min(.85, max(.15, result))


@lru_cache(maxsize=3)
def _condition_pixels(path, source_sha):
    require(sha(path) == source_sha, 'Transition condition pixels changed')
    rows = _png_rgba(path)
    minimum, maximum = 255, 0
    for y, row in enumerate(rows):
        cy = 18000 - (y + .5) * 36000 / 1024
        for x in range(1024):
            r, g, b, a = row[x * 4:x * 4 + 4]
            require(g == 255 and b == 0 and a == 255 and 38 <= r <= 217,
                    'Transition condition actual channels/range differ')
            expected = round(_condition(-18000 + (x + .5) * 36000 / 1024, cy) * 255)
            require(r == expected, 'Transition condition actual world-field pixels differ')
            minimum, maximum = min(minimum, r), max(maximum, r)
    return {'dimensions': [1024, 1024], 'actualRedRange': [minimum, maximum],
            'all1048576ConditionPixelsVerified': True, 'artistFieldOnly': True}


def _condition_texture(texture, approved):
    require(digest(texture) == digest(approved), 'Transition condition frame/interpretation/source differs')
    path = pinned(texture['path'], texture['sha256'])
    return _condition_pixels(str(path), texture['sha256'])


def _source_meshes(context, neighborhood):
    numbers = {row['parcelNumber'] for row in neighborhood['groundDetails']
               if row['authoredLandUse'] == 'ILLUSTRATIVE_MIXED_FALLOW_AND_WORN_ACCESS_UNBUILT'}
    ids = {row['meshId'] for row in context['surfaces'] if row['parcelNumber'] in numbers
           and row['finish'] == 'surface' and row['material'] in ('context_meadow', 'context_fallow')}
    meshes = {row['id']: row for row in context['meshes'] if row['id'] in ids}
    require(len(meshes) == 65 and set(meshes) == ids, 'Transition exact original ground mesh set differs')
    return meshes


def _bindings(rows, meshes, report):
    require(len(rows) == 65 and len({row['sourceMeshId'] for row in rows}) == 65
            and {row['sourceMeshId'] for row in rows} == set(meshes), 'Transition65 binding inventory differs')
    for row in rows:
        identity = row['sourceMeshId']
        original = meshes[identity]
        require(set(row) == {'sourceMeshId', 'expectedMaterialKey', 'proposedSharedMaterialKey', 'nativeActor',
                            'nativeMesh', 'sourceGeometrySha256', 'sourceVerticesAndIndicesUnchanged'}
                and row['sourceGeometrySha256'] == digest(original)
                and row['expectedMaterialKey'] == original['material']
                and row['proposedSharedMaterialKey'] == MATERIAL
                and row['nativeActor'] == report['geometry']['actors'][identity]
                and row['nativeMesh'] == report['geometry']['meshes'][identity]
                and row['sourceVerticesAndIndicesUnchanged'] is True,
                'Transition original geometry/material/native binding differs: ' + identity)


def _library(prototypes, merged, original):
    require(len(prototypes) == 3 and {row['id'] for row in prototypes} == IDS,
            'Transition prototype subset differs')
    imported = {row['id']: row for row in merged['meshes']}
    require(len(imported) == len(merged['meshes']), 'Transition imported master IDs duplicated')
    originals = {row['id']: row for row in original['meshes']}
    decoded, measured = {}, {}
    for row in prototypes:
        key = row['id']
        require(digest(row) == digest(originals[key]) == digest(imported.get(key))
                and row['materialKeys'] == ['ph_grass_medium_02']
                and row['sharedLodOrientationMatrix'] == [[1., 0., 0., 0.], [0., 1., 0., 0.],
                                                        [0., 0., 1., 0.], [0., 0., 0., 1.]],
                'Transition original/imported prototype geometry/material differs')
        path = pinned(row['glbPath'], row['glbSha256'])
        if str(path) not in decoded:
            _primitive_inventory(path)
            decoded[str(path)] = base._glb_nodes(path)
        low, high, radius, triangles = math.inf, -math.inf, 0., []
        require([level['level'] for level in row['lods']] == [0, 1, 2], 'Transition all3LOD policy differs')
        for level in row['lods']:
            actual = decoded[str(path)][level['nodeName']]
            # Five frozen source manifest LOD vertex fields predate the exact
            # export. Preserve them as historical metadata, while enforcing
            # the independently decoded counts of the immutable actual GLB.
            require(actual['vertices'] == ACTUAL_VERTEX_COUNTS[key][level['level']]
                    and actual['triangles'] == level['triangles']
                    and actual['materials'] == {'ph_grass_medium_02'}
                    and all(abs(actual['bounds'][bound][i] - level['expectedBoundsCm'][bound][i]) <= EPS
                            for bound in ('min', 'max') for i in range(3)),
                    'Transition actual decoded LOD counts/bounds/materials differ')
            low, high = min(low, actual['bounds']['min'][2]), max(high, actual['bounds']['max'][2])
            radius = max(radius, actual['radius'])
            triangles.append(actual['triangles'])
        measured[key] = {'minZ': low, 'height': high - low, 'radius': radius, 'triangles': triangles,
                         'actualVerticesByLod': ACTUAL_VERTEX_COUNTS[key],
                         'historicalManifestVerticesByLod': [level['vertices'] for level in row['lods']]}
    return measured


def _primitive_inventory(path):
    """Verify all15 immutable source nodes/primitives and every attribute view."""
    raw = Path(path).read_bytes()
    require(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Transition GLB header differs')
    size, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a, 'Transition source GLB JSON missing')
    document = json.loads(raw[20:20 + size])
    cursor = 20 + size
    binary_size, kind = struct.unpack_from('<II', raw, cursor)
    require(kind == 0x004e4942 and cursor + 8 + binary_size == len(raw), 'Transition source binary differs')
    require(set(document) == {'asset', 'scene', 'scenes', 'nodes', 'materials', 'meshes',
                             'accessors', 'bufferViews', 'buffers'}
            and len(document['nodes']) == len(document['meshes']) == 15
            and {n['name'] for n in document['nodes']} == {
                'PH_grass_medium_02_' + letter + '_LOD' + str(lod) for letter in 'abcde' for lod in range(3)}
            and len(document['materials']) == 1 and document['materials'][0]['name'] == 'ph_grass_medium_02',
            'Transition source full node/primitive/material identity differs')
    used_accessors = set()
    binary = memoryview(raw)[cursor + 8:]
    for node in document['nodes']:
        require(set(node) == {'mesh', 'name'}, 'Transition source node deformation refused')
        mesh = document['meshes'][node['mesh']]
        require(mesh['name'] == node['name'] and len(mesh['primitives']) == 1,
                'Transition source primitive inventory differs')
        primitive = mesh['primitives'][0]
        require(set(primitive) == {'attributes', 'indices', 'material'} and primitive['material'] == 0
                and set(primitive['attributes']) == {'POSITION', 'NORMAL', 'TANGENT', 'TEXCOORD_0'},
                'Transition source primitive modifiers/attributes differ')
        position_count = document['accessors'][primitive['attributes']['POSITION']]['count']
        for role, index in {**primitive['attributes'], 'indices': primitive['indices']}.items():
            require(index not in used_accessors, 'Transition source accessor reused unexpectedly')
            used_accessors.add(index)
            accessor = document['accessors'][index]
            view = document['bufferViews'][accessor['bufferView']]
            require(set(accessor) <= {'bufferView', 'componentType', 'count', 'type', 'min', 'max'}
                    and set(view) == {'buffer', 'byteLength', 'byteOffset', 'target'} and view['buffer'] == 0
                    and type(accessor['count']) is int and accessor['count'] > 0,
                    'Transition source accessor/view modifiers differ')
            if role == 'indices':
                require(accessor['componentType'] in (5123, 5125) and accessor['type'] == 'SCALAR',
                        'Transition source index accessor differs')
                count, width = accessor['count'], 2 if accessor['componentType'] == 5123 else 4
            else:
                count = position_count
                number = {'POSITION': 3, 'NORMAL': 3, 'TANGENT': 4, 'TEXCOORD_0': 2}[role]
                width = number * 4
                require(accessor['componentType'] == 5126 and accessor['count'] == count
                        and accessor['type'] == 'VEC' + str(number), 'Transition source frame/UV count/type differs')
                start = view['byteOffset']
                require(start >= 0 and start + count * width <= binary_size, 'Transition attribute view truncated')
                require(all(all(math.isfinite(v) for v in struct.unpack_from('<' + 'f' * number, binary, start + i * width))
                            for i in range(count)), 'Transition actual source attribute is nonfinite')
            require(view['byteLength'] == count * width and 0 <= view['byteOffset']
                    and view['byteOffset'] + view['byteLength'] <= binary_size,
                    'Transition source accessor buffer coverage differs')
    require(used_accessors == set(range(len(document['accessors']))), 'Transition unexamined source accessor refused')
    return {'nodes': 15, 'primitives': 15, 'accessors': len(used_accessors), 'allAttributesIncluded': True}


def _triangle_polygons(meshes):
    polygons = []
    for mesh in meshes:
        vertices, indices = mesh['verticesCm'], mesh['indices']
        require(len(indices) % 3 == 0, 'Transition source ground triangle inventory differs')
        for offset in range(0, len(indices), 3):
            tri = [vertices[index][:2] for index in indices[offset:offset + 3]]
            if abs(substrate._cross(*tri)) > EPS: polygons.append([tri + [tri[0]]])
    return polygons


class _BlockedCircles:
    """Full circle-versus-source-polygon checks, including small enclosed holes."""
    def __init__(self, polygons, margin=0., cell=500.):
        self.cell, self.margin, self.tiles = cell, margin, defaultdict(set)
        self.polygons = polygons
        for i, polygon in enumerate(polygons):
            points = [point for ring in polygon for point in ring]
            bounds = [min(p[0] for p in points) - margin, min(p[1] for p in points) - margin,
                      max(p[0] for p in points) + margin, max(p[1] for p in points) + margin]
            for x in range(math.floor(bounds[0] / cell), math.floor(bounds[2] / cell) + 1):
                for y in range(math.floor(bounds[1] / cell), math.floor(bounds[3] / cell) + 1):
                    self.tiles[x, y].add(i)

    def outside(self, point, radius):
        choices = set()
        for x in range(math.floor((point[0] - radius) / self.cell), math.floor((point[0] + radius) / self.cell) + 1):
            for y in range(math.floor((point[1] - radius) / self.cell), math.floor((point[1] + radius) / self.cell) + 1):
                choices.update(self.tiles.get((x, y), ()))
        for index in choices:
            polygon = self.polygons[index]
            require(not (base._inside_ring(point, polygon[0]) and
                         not any(base._inside_ring(point, hole) for hole in polygon[1:]))
                    and min(base._distance(point, a, b) for ring in polygon for a, b in zip(ring, ring[1:]))
                    + EPS >= radius + self.margin,
                    'Transition full crown intersects original private/road/building/soil source exclusion')


def _circle_inside(index, point, radius):
    require(index.contains(point) and index.distance(point, radius + 1.) + EPS >= radius,
            'Transition decoded full crown leaves source domain/outer band or crosses hole')


def _spatial(plan, context, neighborhood, buildings):
    domains = [substrate._PolygonIndex(plan[key]) for key in ('targetGroundDomainCm', 'edgeDomainCm')]
    exposure = [mesh for mesh in neighborhood['meshes'] if mesh['material'] == 'context_soil_exposure']
    blocked = [
        _BlockedCircles([[tri + [tri[0]]] for tri in context['protectedTrianglesCm']], 30),
        _BlockedCircles(_triangle_polygons([m for m in context['meshes'] if m['material'] == 'context_track']), 20),
        _BlockedCircles([[ring if ring[0] == ring[-1] else ring + [ring[0]] for ring in polygon]
                         for building in buildings['buildings'] for polygon in building['polygonsCm']], 150),
        _BlockedCircles(_triangle_polygons(exposure)),
    ]
    return domains, blocked


def _placements(rows, measured, domains, blocked, ground):
    require(len(rows) == 7000, 'Transition7000 placement inventory differs')
    counts, minimum, maximum, radius_max = [0, 0, 0], math.inf, -math.inf, 0.
    for row in rows:
        require(row['meshId'] in measured and finite(row['positionCm'], 3) and finite(row['scale'], 3)
                and row['scale'][0] == row['scale'][1] == row['scale'][2] and .1 <= row['scale'][0] <= .6
                and type(row['yawDeg']) in (int, float) and math.isfinite(row['yawDeg']) and 0 <= row['yawDeg'] < 360
                and row['wholeCrownOutsideSoilExposure'] is True, 'Transition placement scale/frame/policy differs')
        actual, scale = measured[row['meshId']], row['scale'][0]
        radius, height = actual['radius'] * scale, actual['height'] * scale
        require(type(row['radiusCm']) in (int, float) and type(row['actualHeightCm']) in (int, float)
                and abs(radius - row['radiusCm']) <= 1e-6 and abs(height - row['actualHeightCm']) <= 1e-6
                and 3.8 - 1e-6 <= height <= 7. + 1e-6, 'Transition decoded height/radius differs')
        z, identity = ground.sample(row['positionCm'][:2])
        require(type(row['sourceGroundZCm']) in (int, float) and abs(z - row['sourceGroundZCm']) <= 1e-6
                and abs(row['positionCm'][2] + actual['minZ'] * scale - z) <= 1e-6
                and row['sourceGroundMeshId'] in ground.mesh_ids_at(row['positionCm'][:2]),
                'Transition actual highest source triangle/contact/mesh differs')
        crown = radius + .1
        for domain in domains: _circle_inside(domain, row['positionCm'][:2], crown)
        for mask in blocked: mask.outside(row['positionCm'][:2], crown)
        counts = [a + b for a, b in zip(counts, actual['triangles'])]
        minimum, maximum, radius_max = min(minimum, height), max(maximum, height), max(radius_max, radius)
    require(counts == [6351095, 3487981, 1584502] and counts[0] <= 6500000,
            'Transition actual allLOD triangle budget differs')
    return {'instances': len(rows), 'allLodTriangles': counts, 'heightCm': [minimum, maximum],
            'maximumCrownRadiusCm': radius_max, 'wholeCircularCrownMarginCm': .1}


class _Ground(base._Ground):
    def __init__(self, meshes):
        super().__init__({'meshes': list(meshes.values())}, {'meshes': []})

    def mesh_ids_at(self, point):
        choices = []
        for (a, b, c), identity, denominator in self.tiles[math.floor(point[0] / self.cell), math.floor(point[1] / self.cell)]:
            u = ((b[0] - point[0]) * (c[1] - point[1]) - (b[1] - point[1]) * (c[0] - point[0])) / denominator
            v = ((c[0] - point[0]) * (a[1] - point[1]) - (c[1] - point[1]) * (a[0] - point[0])) / denominator
            if min(u, v, 1 - u - v) >= -1e-8: choices.append(identity)
        return set(choices)


def _groups(groups, rows):
    require(len(groups) == 158 and len({g['id'] for g in groups}) == 158, 'Transition158 group inventory differs')
    expected = defaultdict(list)
    for row in rows:
        identity = 'EX_transition_' + '_'.join(str(math.floor(p / 3000)) for p in row['positionCm'][:2]) + '_' + row['meshId']
        expected[identity].append({k: row[k] for k in ('positionCm', 'yawDeg', 'scale')})
    require({g['id'] for g in groups} == set(expected), 'Transition exact tile/group identities differ')
    for group in groups:
        require(set(group) == {'id', 'meshId', 'instances', 'cullStartCm', 'cullEndCm', 'castShadow', 'qualityDetail', 'collision'}
                and group['meshId'] in IDS and group['id'].endswith('_' + group['meshId'])
                and group['collision'] == 'NoCollision' and group['castShadow'] is False and group['qualityDetail'] is False
                and type(group['cullStartCm']) is int and type(group['cullEndCm']) is int
                and (group['cullStartCm'], group['cullEndCm']) == (3200, 4000)
                and digest(group['instances']) == digest(expected[group['id']]),
                'Transition exact ordered native group transforms/policies differ')


def validated_transition(plan, source_context, imported_manifest, sceneSha, objSha):
    """Return exact65 proposed bindings +158 additive groups and measured audit."""
    approved, proof = _approved()
    require(plan['owner'] == GENERATOR and plan['generatorSha256'] == GENERATOR_SHA
            and sha(ROOT / GENERATOR) == GENERATOR_SHA and plan['status'] == approved['status'],
            'Transition owner/status/generator identity differs')
    require(plan['activeDesign'] == DESIGN and plan['housePlacement'] == approved['housePlacement']
            and plan['sourceSceneSha256'] == sceneSha == approved['sourceSceneSha256']
            and plan['sourceObjSha256'] == objSha == approved['sourceObjSha256'], 'Transition canonical source frame differs')
    require(plan['nativeVisualAccepted'] is False and plan['performanceAccepted'] is False
            and digest(plan['preservation']) == digest(approved['preservation'])
            and digest(plan['edgePolicy']) == digest(approved['edgePolicy'])
            and digest(plan['inputFiles']) == digest(approved['inputFiles']), 'Transition preservation/policy/source closure differs')
    require(digest(plan) == digest(approved), 'Transition frozen study plan differs')
    for path, value in plan['inputFiles'].items(): pinned(path, value)
    context = read_pin(plan['sourceContext'])
    require(digest(context) == digest(source_context) and plan['sourceContext'] == approved['sourceContext']
            and plan['sourceNeighborhood'] == approved['sourceNeighborhood'], 'Transition original source context differs')
    neighborhood = read_pin(plan['sourceNeighborhood'])
    require(sum(len(v) for v in neighborhood['groundDetailRemovedPlacementIndices'].values()) == 47203,
            'Transition original47203 whole-crown removals differ')
    for key in ('targetGroundDomainCm', 'edgeDomainCm', 'summary', 'sourceResponseComparison'):
        require(digest(plan[key]) == digest(approved[key]), 'Transition pinned source-derived domain/summary differs')
    require(digest(plan['sharedPbrResponseProposal']) == digest(approved['sharedPbrResponseProposal']),
            'Transition bounded PBR response/old ortho protection preservation differs')
    report_key = next(p for p in plan['inputFiles'] if p.endswith('/exterior-20261001-r10/exterior-import-report.json'))
    report = read_pin({'path': report_key, 'sha256': plan['inputFiles'][report_key]})
    recipe = report['materials']['materials']['ph_grass_medium_02']['recipe']
    require(recipe['sourceUrl'] == 'https://polyhaven.com/a/grass_medium_02' and recipe['license'] == 'CC0-1.0',
            'Transition original photographic leaf provenance differs')
    leaf_pins = {}
    for role, record in recipe['maps'].items():
        pinned(record['path'], record['sha256']);leaf_pins[record['path']] = record['sha256']
    require(leaf_pins == proof['validation']['originalLeafMaterialInputPins'], 'Transition original leaf pixel roles differ')
    # The future shader must retain these existing source recipes' fieldMacro,
    # orthophoto provider/protection/camera blend, PBR/UV and groundCover paths.
    old_response = {k: report['materials']['materials'][k]['recipe'] for k in ('context_meadow', 'context_fallow')}
    meshes = _source_meshes(context, neighborhood)
    _bindings(plan['materialBindingProposal'], meshes, report)
    master_key = next(p for p in plan['inputFiles'] if p.endswith('/exterior-assets-greenery-20260930-r5/geometry-manifest.json'))
    original = json.loads(pinned(master_key, plan['inputFiles'][master_key]).read_text())
    measured = _library(plan['prototypes'], imported_manifest, original)
    buildings_key = next(p for p in plan['inputFiles'] if p.endswith('/exterior-buildings-20260926-r2/building-plan.json'))
    buildings = json.loads(pinned(buildings_key, plan['inputFiles'][buildings_key]).read_text())
    domains, masks = _spatial(plan, context, neighborhood, buildings)
    actual = _placements(plan['transitionPlacements'], measured, domains, masks, _Ground(meshes))
    _groups(plan['groups'], plan['transitionPlacements'])
    pixels = _condition_texture(plan['conditionTexture'], approved['conditionTexture'])
    input_pins = {**plan['inputFiles'], **leaf_pins,
                  str(STUDY / 'transition-plan.json'): PLAN_SHA, str(PROOF): PROOF_SHA,
                  plan['conditionTexture']['path']: plan['conditionTexture']['sha256'],
                  str(ROOT / 'scripts/unreal/exterior-canopy-native.py'): CANOPY_SHA,
                  str(ROOT / 'scripts/unreal/exterior-grove-substrate-native.py'): SUBSTRATE_SHA}
    audit = {'status': 'verified-source-neighborhood-transition-native-inputs', 'owner': OWNER,
             'sourcePlan': {'path': str(STUDY / 'transition-plan.json'), 'sha256': PLAN_SHA},
             'independentSourceDomainProof': {'path': str(PROOF), 'sha256': PROOF_SHA},
             'sourceGroundBindings': 65, 'groups': 158, **actual, 'condition': pixels,
             'originalPhotographicLeafMapPins': leaf_pins,
             'inputFiles': input_pins,
             'sourceGlbInventory': {'nodes': 15, 'primitives': 15, 'accessors': 75,
                                   'allPrimitiveAccessorsIncluded': True, 'selectedLodNodes': 9},
             'decodedPrototypeVertexInventory': {k: {'actual': v['actualVerticesByLod'],
                                                     'historicalManifest': v['historicalManifestVerticesByLod']}
                                                for k, v in measured.items()},
             'originalSourceGroundRecipes': {k: digest(v) for k, v in old_response.items()},
             'futureSharedMaterialMustPreserveFieldMacroAndProtectedCameraOrtho': True,
             'sourceGeometryAndOriginalMaterialsUnchanged': True, 'originalRemovalIndicesPreserved': 47203,
             'originalVegetationRestoredOrMoved': 0, 'hiddenOriginalActors': 0,
             'actualAllLodFullCircularCrownsAndSourceGroundChecked': True,
             'artistInterpretation': True, 'surveyedLandUseBotanyOrElevation': False,
             'nativeVisualAccepted': False, 'performanceAccepted': False}
    return {'materialBindings': plan['materialBindingProposal'], 'groups': plan['groups'], 'audit': audit}
