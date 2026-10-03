"""Stdlib source-input guard for one frozen continuous meadow candidate.

This does not open Unreal or certify native geometry, pixels or performance.
The GEOS domain construction remains a pinned authoring preflight. Ordinary
Python rechecks every changed crown against that domain and actual original
private/road/building exclusions, source roots, prototypes and triangle data.
"""
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-meadow-continuous-native.py'
GENERATOR = 'scripts/unreal/exterior-meadow-continuous-study.py'
GENERATOR_SHA = '498426d153f8f5c2c0215a455e8bb2f919e228233d6e8e5c9d0c7bcdddb10518'
STUDY = ROOT / 'output/unreal/exterior-meadow-continuous-20261001-r1-study'
PLAN_SHA = 'cd199caee2846741049151887f6546ba0279e4beef1ce6bb5e36430085f7067d'
RECEIPT_SHA = '7c7a742e17da1ad8a1f79da4822ca86be8c6e505c5c9329c01a4e21348971c34'
PINS = {
    'continuous-meadow-plan.json': PLAN_SHA,
    'cultivated-soil-subsets.json': 'a6defa3fcfcd95da79cfc2a9539689f80194ae6adce09d685181baeb6651e75c',
    'restored-roots.json': 'a45b52d619ceb81c02db627aaffe30a3f52f32c02758a9c8f10feb20e26516cd',
    'restored-groups.json': 'abd3a40ff5e2d37dd25f982b728cd976c48f7896fc6715fb1875f8513df5a1be',
    'retained-height-overrides.json': '011bf35de2b3b2a4eec362601c7627ecf2e3215a087baa35f2d2a73490800905',
    'planview-comparison.png': 'c907102a3773d909cebb4025bedbfc11a554182ee5090ebf0db5d1955e590826',
    'soil-triangle-mask.png': 'e222355d194dce69f6eb465ac9eb7ca2e7e0925f1ccd69e8e43b972d78e9db09',
    'restored-root-map.png': 'f7379843e91291f2ee9b13a563da8b18dfe36d700cc9109e29676f5f840a6860',
    'continuous-growth-field.png': '4a8dbef2f3bd08ae208d80074cc58e4fd3d11b96c32fada57b54275fc6ede3fe',
    'source-validation.json': RECEIPT_SHA,
}
DELEGATES = {
    'exterior-neighborhood-transition-native.py': '892313c1b985f9e7c291f2e3cc02edad38305ae0cc607c5a3240dc0c4b3b1e4a',
    'exterior-canopy-native.py': '2788c643f4bd924f2fa72714d18ad009a7b4aa599ba86df58baf7582f765a172',
    'exterior-grove-substrate-native.py': 'c27e3b935d4486e6150e262a8309223e9f72e0ef6abb9f648af5c897283f692e',
}
DESIGN = {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
STATUS = 'MEASURED_CONTINUOUS_MEADOW_LAYOUT_SOURCE_ONLY_NATIVE_PENDING'
ARRAYS = ('meadowBladePlacements', 'meadowUnderstoryPlacements')
COUNTS = {'meadowBladePlacements': (382678, 34447, 186423), 'meadowUnderstoryPlacements': (86248, 5387, 33384)}
FALSE_FLAGS = ('nativeApplied', 'nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'integrationAuthorized')


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            result.update(block)
    return result.hexdigest()


def digest(value):
    try:
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError) as error:
        raise RuntimeError('Continuous invalid finite JSON source data') from error


def same(a, b):
    return digest(a) == digest(b)


def finite(value, length=None):
    if length is None:
        return type(value) in (int, float) and math.isfinite(value)
    return isinstance(value, (list, tuple)) and len(value) == length and all(finite(x) for x in value)


def pinned(path, expected):
    require(isinstance(path, (str, Path)) and isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected),
            'Continuous source pin type/format differs')
    path = (ROOT / path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == expected,
            'Continuous source pin drift or escaped path: ' + str(path))
    return path


def _json(path):
    return json.loads(Path(path).read_text())


@lru_cache(maxsize=1)
def _module():
    for filename, expected in DELEGATES.items():
        pinned(ROOT / 'scripts/unreal' / filename, expected)
    path = ROOT / 'scripts/unreal/exterior-neighborhood-transition-native.py'
    spec = importlib.util.spec_from_file_location('continuous_source_geometry_guard', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


@lru_cache(maxsize=1)
def _bundle():
    approved = _json(pinned(STUDY / 'continuous-meadow-plan.json', PLAN_SHA))
    receipt = _json(pinned(STUDY / 'source-validation.json', RECEIPT_SHA))
    require(receipt['owner'] == GENERATOR and receipt['status'] == 'SOURCE_VALIDATION_PASS_NATIVE_PENDING' and
            all(receipt[key] is False for key in FALSE_FLAGS), 'Continuous source receipt status/acceptance differs')
    require(set(receipt['files']) == set(PINS) - {'source-validation.json'}, 'Continuous complete sidecar inventory differs')
    for name, expected in PINS.items():
        path = pinned(STUDY / name, expected)
        if name in receipt['files']:
            require(receipt['files'][name] == {'path': str(path), 'sha256': expected, 'bytes': path.stat().st_size},
                    'Continuous receipt sidecar path/hash/extent differs')
    require(same(approved['inputFiles'], receipt['inputFiles']), 'Continuous authoring input pin closure differs')
    sources = {}
    for path, expected in approved['inputFiles'].items():
        path = pinned(path, expected)
        if path.suffix == '.json':
            sources[path.name if path.name != 'exterior-import-report.json' else 'nativeReceipt'] = _json(path)
    sidecars = {name: _json(STUDY / name) for name in PINS if name.endswith('.json') and name not in ('continuous-meadow-plan.json', 'source-validation.json')}
    return approved, receipt, sources, sidecars


def _validate_identity(plan, context, neighborhood, transition, scene_sha, obj_sha, approved, sources):
    require(isinstance(plan, dict) and plan.get('owner') == GENERATOR and plan.get('generatorSha256') == GENERATOR_SHA and
            plan.get('status') == STATUS and type(plan.get('schemaVersion')) is int and plan['schemaVersion'] == 1,
            'Continuous typed owner/hash/status/schema differs')
    require(all(plan.get(key) is False for key in FALSE_FLAGS), 'Continuous native/realism/authorization claim differs')
    require(same(plan, approved), 'Continuous frozen plan content differs')
    require(plan['activeDesign'] == DESIGN and type(plan['housePlacement']['streetSetbackMm']) is int and
            type(plan['housePlacement']['eastSetbackMm']) is int and
            plan['housePlacement']['streetSetbackMm'] == plan['housePlacement']['eastSetbackMm'] == 3000,
            'Continuous C/B/B 3000 mm safeguards differ')
    require(isinstance(scene_sha, str) and isinstance(obj_sha, str) and
            plan['sourceSceneSha256'] == scene_sha == sources['context-plan.json']['sourceSceneSha256'] and
            plan['sourceObjSha256'] == obj_sha == sources['context-plan.json']['sourceObjSha256'], 'Continuous scene/OBJ source frame differs')
    require(same(context, sources['context-plan.json']), 'Continuous exact unfiltered frozen R8 source context differs')
    require(same(neighborhood, sources['neighborhood-details.json']), 'Continuous original neighborhood/removal indices differ')
    require(same(transition, sources['transition-plan.json']), 'Continuous historical transition source plan differs')


def _png_structure(path, dimensions):
    raw = Path(path).read_bytes()
    require(raw[:8] == b'\x89PNG\r\n\x1a\n', 'Continuous diagnostic PNG signature differs')
    cursor, header, payload, ended = 8, None, bytearray(), False
    while cursor < len(raw):
        require(cursor + 12 <= len(raw), 'Continuous truncated PNG chunk')
        length, kind = struct.unpack_from('>I4s', raw, cursor)
        end = cursor + length + 12
        require(end <= len(raw) and (zlib.crc32(raw[cursor + 4:end - 4]) & 0xffffffff) == struct.unpack_from('>I', raw, end - 4)[0],
                'Continuous diagnostic PNG CRC differs')
        data = raw[cursor + 8:end - 4]
        if kind == b'IHDR':
            require(header is None and cursor == 8 and length == 13, 'Continuous PNG header differs')
            header = struct.unpack('>IIBBBBB', data)
        elif kind == b'IDAT':
            require(header is not None and not ended, 'Continuous PNG data order differs')
            payload.extend(data)
        elif kind == b'IEND':
            require(length == 0 and end == len(raw), 'Continuous PNG end differs')
            ended = True
        else:
            require(kind[0] & 32, 'Continuous unsupported critical PNG chunk')
        cursor = end
    require(header is not None and header[:2] == dimensions and header[2] == 8 and header[3] in (2, 6) and
            header[4:] == (0, 0, 0) and ended, 'Continuous diagnostic PNG dimensions/format differs')
    stride = dimensions[0] * (3 if header[3] == 2 else 4) + 1
    decoder = zlib.decompressobj()
    packed = decoder.decompress(payload, stride * dimensions[1] + 1)
    require(len(packed) == stride * dimensions[1] and decoder.eof and not decoder.unused_data and
            all(packed[y * stride] <= 4 for y in range(dimensions[1])), 'Continuous PNG scanline extent/filter differs')


def _soil(plan, neighborhood, subsets, context):
    proposal = plan['soilOverlayProposal']
    records = {r['sourceMeshId']: r for r in proposal['triangles']}
    replacements = {m['id']: m for m in subsets}
    require(len(records) == 15 and len(replacements) == len(subsets) == 4, 'Continuous soil subset inventory differs')
    module = _module()
    unbuilt = module._source_meshes(context, neighborhood)
    cultivated = {row['parcelNumber'] for row in neighborhood['groundDetails']
                  if row['authoredLandUse'] == 'ILLUSTRATIVE_LATE_SEASON_CULTIVATED_ROWS'}
    require(cultivated == {'6022', '6030', '6031', '6032', '6033', '6040', '6041'}, 'Continuous exact seven cultivated source parcels differ')
    crop_ids = {row['meshId'] for row in context['surfaces'] if row['parcelNumber'] in cultivated and row['finish'] == 'surface'}
    crops = {row['id']: row for row in context['meshes'] if row['id'] in crop_ids}
    require(len(crops) == 7, 'Continuous seven cultivated source ground meshes differ')
    ground = module._Ground({**unbuilt, **crops})
    removed, kept, output, all_omit, all_keep = [], [], [], 0, 0
    for mesh in neighborhood['meshes']:
        if mesh['material'] != 'context_soil_exposure':
            output.append(deepcopy(mesh))
            continue
        require(mesh['id'] in records, 'Continuous unowned soil mesh')
        row = records[mesh['id']]
        require(row['originalMeshSha256'] == digest(mesh), 'Continuous original soil vertex/material source differs')
        omit, keep = row['omitSourceTriangleOrdinals'], row['keepSourceTriangleOrdinals']
        require(all(type(i) is int for i in omit + keep) and omit == sorted(set(omit)) and keep == sorted(set(keep)) and
                not set(omit).intersection(keep) and sorted(omit + keep) == list(range(len(mesh['indices']) // 3)),
                'Continuous complete soil triangle partition/order differs')
        require(len(omit) == row['omittedTriangleCount'] and len(keep) == row['retainedTriangleCount'], 'Continuous soil partition count differs')
        kept_ordinals = set(keep)
        for ordinal in range(len(mesh['indices']) // 3):
            vertices = [mesh['verticesCm'][i] for i in mesh['indices'][3*ordinal:3*ordinal+3]]
            center = [sum(v[axis] for v in vertices)/3 for axis in (0, 1)]
            ground_ids = ground.mesh_ids_at(center)
            is_crop, is_unbuilt = bool(ground_ids.intersection(crops)), bool(ground_ids.intersection(unbuilt))
            require(is_crop != is_unbuilt and (ordinal in kept_ordinals) is is_crop,
                    'Continuous soil triangle centroid original cultivated/unbuilt source membership differs')
        all_omit += len(omit)
        all_keep += len(keep)
        if not keep:
            require(row['action'] == 'OMIT_UNBUILT_ONLY_OVERLAY', 'Continuous unbuilt soil omission action differs')
            removed.append(mesh['id'])
        elif not omit:
            require(row['action'] == 'KEEP_CULTIVATED_OVERLAY_EXACT', 'Continuous cultivated soil keep action differs')
            kept.append(mesh['id'])
            output.append(deepcopy(mesh))
        else:
            require(row['action'] == 'REPLACE_WITH_EXACT_CULTIVATED_INDEX_SUBSET' and mesh['id'] in replacements,
                    'Continuous mixed cultivated subset action differs')
            replacement = replacements[mesh['id']]
            require(set(replacement) == set(mesh) and all(same(replacement[k], mesh[k]) for k in mesh if k != 'indices'),
                    'Continuous cultivated original vertices/UV/normals/tangents/material metadata changed')
            require(replacement['indices'] == [mesh['indices'][3 * i + k] for i in keep for k in range(3)] and
                    row['replacementMeshSha256'] == digest(replacement), 'Continuous cultivated triangle indices/winding/order changed')
            output.append(deepcopy(replacement))
    require(removed == proposal['omitMeshIds'] and kept == proposal['unchangedCultivatedMeshIds'] and
            (len(removed), len(kept), all_omit, all_keep, len(output)) == (4, 7, 103392, 2801, 143),
            'Continuous soil aggregate preservation differs')
    require(sum(len(m['indices']) // 3 for m in output) == 142105, 'Continuous neighborhood triangle budget differs')
    return output


def _prototypes(plan, source, historical):
    require(len(source) == 12, 'Continuous original prototype census differs')
    recorded = {row['id']: row for row in plan['nativeOriginalPrototypes']}
    require(len(recorded) == 4, 'Continuous original prototype metadata census differs')
    measured = {}
    for variant in range(4):
        identity = f'LawnTuft{variant}'
        levels = sorted([r for r in source if r['variant'] == variant], key=lambda r: r['lod'])
        require([r['lod'] for r in levels] == [0, 1, 2], 'Continuous prototype LOD order differs')
        points, costs = [], []
        for lod, row in enumerate(levels):
            require(row['id'] == f'{identity}_LOD{lod}' and all(finite(v, 3) for v in row['verticesMm']), 'Continuous prototype position decoder differs')
            count = len(row['verticesMm'])
            require(len(row['faces']) == (256, 64, 24)[lod] and all(isinstance(face, list) and len(face) == 3 and
                    all(type(i) is int and 0 <= i < count for i in face) for face in row['faces']), 'Continuous prototype index decoder differs')
            require(len(row['normals']) == count and all(finite(v, 3) and abs(sum(x*x for x in v) - 1) < 1e-5 for v in row['normals']),
                    'Continuous prototype source normal decoder differs')
            require(all(len(row[key]) == count and all(finite(v, 2) for v in row[key]) for key in ('uv0', 'uv1')),
                    'Continuous prototype source UV decoder differs')
            for face in row['faces']:
                a, b, c = [row['verticesMm'][i] for i in face]
                u, v = [b[j]-a[j] for j in range(3)], [c[j]-a[j] for j in range(3)]
                cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
                require(sum(x*x for x in cross) > 1e-12, 'Continuous degenerate source prototype triangle')
            decoded = recorded[identity]['decodedLods'][lod]
            require(decoded == {'id': row['id'], 'lod': lod, 'triangles': len(row['faces']), 'vertices': count,
                                'decodedRecordSha256': digest(row)}, 'Continuous prototype source decoder proof differs')
            points.extend([[v / 10 for v in p] for p in row['verticesMm']])
            costs.append(len(row['faces']))
        radius = max(math.hypot(p[0], p[1]) for p in points)
        minimum, height = min(p[2] for p in points), max(p[2] for p in points)
        row, old = recorded[identity], historical['nativeMeadow']['prototypes'][identity]
        require(minimum == row['sourceMinZCm'] == 0 and abs(height-row['sourceMaxZCm']) < 1e-12 and
                abs(radius-row['sourceRadiusCm']) < 1e-12 and row['lodTriangles'] == costs == [256, 64, 24] and
                row['nativeMesh'] == old['mesh'] and row['nativeMaterial'] == old['material'] and row['lodScreens'] == old['lodScreens'] and
                [p['triangles'] for p in old['lodProofs']] == costs and
                all(p['triangleConnectivityWindingVerified'] is True and p['uvChannelsVerified'] == [0, 1] for p in old['lodProofs']),
                'Continuous original source bounds/historical native asset lookup differs')
        measured[identity] = {'radiusCm': radius, 'heightCm': height, 'triangles': costs}
    return measured


def _spatial(plan, context, neighborhood, buildings):
    module = _module()
    ground = module._source_meshes(context, neighborhood)
    domain = module.substrate._PolygonIndex(plan['targetGroundDomainCm'])
    roads = module._triangle_polygons([m for m in context['meshes'] if m['material'] == 'context_track'])
    blocked = [module._BlockedCircles([[t + [t[0]]] for t in context['protectedTrianglesCm']], 30),
               module._BlockedCircles(roads, 20),
               module._BlockedCircles([[r if r[0] == r[-1] else r + [r[0]] for r in poly]
                       for b in buildings['buildings'] for poly in b['polygonsCm']], 150)]
    road_index = module.substrate._PolygonIndex({'type': 'MultiPolygon', 'coordinates': roads})
    return domain, blocked, module._Ground(ground), ground, road_index


def _safe(domain, point):
    return domain.contains(point) and domain.distance(point, 15.) >= 14.1 - 1e-8


def _crown(point, spatial, ground_id=None, source_z=None):
    domain, blocked, ground, _, _ = spatial
    require(finite(point, 3) and _safe(domain, point[:2]), 'Continuous whole 14.1cm crown leaves allowed source domain')
    for mask in blocked:
        mask.outside(point[:2], 14.1)
    if ground_id is not None:
        require(ground_id in ground.mesh_ids_at(point[:2]), 'Continuous root lost original source ground membership')
        z, _ = ground.sample(point[:2])
        require(abs(z-source_z) < .0001, 'Continuous original root Z differs from actual source ground')


@lru_cache(maxsize=100000)
def _lattice(x, y, seed):
    v = math.sin(x * 127.1 + y * 311.7 + seed) * 43758.5453
    return v - math.floor(v)


def _noise(x, y, length, seed):
    x, y = x / length, y / length
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3-2*fx), fy * fy * (3-2*fy)
    lo = _lattice(ix, iy, seed)*(1-fx) + _lattice(ix+1, iy, seed)*fx
    hi = _lattice(ix, iy+1, seed)*(1-fx) + _lattice(ix+1, iy+1, seed)*fx
    return lo*(1-fy) + hi*fy


def _step(a, b, value):
    t = max(0., min(1., (value-a)/(b-a)))
    return t*t*(3-2*t)


def _field(point, roads, name):
    x, y = point[:2]
    condition = sum(weight * _noise(x, y, length, seed) for length, seed, weight in ((2400, 31, .55), (1200, 67, .30), (400, 109, .15)))
    edge = 1 - _step(20, 180, roads.distance(point[:2], 181))
    tall, fine = _step(.54, .76, condition) * (1-.85*edge), _noise(x, y, 110, 173)
    height = 5+2.5*condition+12*tall+.9*fine-.9*edge if name == ARRAYS[0] else 2.2+3.1*condition+1.6*tall+.5*fine-.4*edge
    return height, condition, tall, edge


def _retained(context, neighborhood, overrides, spatial):
    require(set(overrides) == {'schemaVersion', 'rowFormat', 'onlyHeightMayChange', 'arrays'} and
            type(overrides['schemaVersion']) is int and overrides['schemaVersion'] == 1 and overrides['onlyHeightMayChange'] is True and
            overrides['rowFormat'] == ['originalSourceArrayIndex', 'proposedHeightCm'] and set(overrides['arrays']) == set(ARRAYS),
            'Continuous typed height-only override schema differs')
    output, checked = {}, 0
    for name in ARRAYS:
        rows = overrides['arrays'][name]
        require(len(context[name]) == COUNTS[name][0] and len(rows) == COUNTS[name][2], 'Continuous retained height override census differs')
        require(all(isinstance(row, list) and len(row) == 2 and type(row[0]) is int and finite(row[1]) and row[1] > 0 for row in rows),
                'Continuous typed finite height override differs')
        indices = [row[0] for row in rows]
        require(indices == sorted(set(indices)), 'Continuous height override original index order differs')
        removed = set(neighborhood['groundDetailRemovedPlacementIndices'][name])
        require(not removed.intersection(indices), 'Continuous height overrides include removed original roots')
        expected = [i for i, row in enumerate(context[name]) if i not in removed and _safe(spatial[0], row['positionCm'][:2])]
        require(indices == expected, 'Continuous exact full-crown-safe retained height override membership differs')
        changes = dict(rows)
        values = []
        for index, original in enumerate(context[name]):
            if index in removed:
                continue
            value = deepcopy(original)
            if index in changes:
                _crown(original['positionCm'], spatial)
                require(original['radiusCm'] == 14, 'Continuous retained original crown radius changed')
                height, *_ = _field(original['positionCm'], spatial[4], name)
                require(abs(changes[index]-height) < 1e-6, 'Continuous analytic world-space height field differs')
                value['heightCm'] = changes[index]
                checked += 1
            require(all(same(value[k], original[k]) for k in original if k != 'heightCm'), 'Continuous retained XY/Z/yaw/radius/source metadata changed')
            values.append(value)
        output[name] = values
    removed = set(neighborhood['groundDetailRemovedPlacementIndices']['groundCoverPlacements'])
    require(len(context['groundCoverPlacements']) == 2996 and len(removed) == 449, 'Continuous original tall cover source census differs')
    output['groundCoverPlacements'] = [deepcopy(row) for i, row in enumerate(context['groundCoverPlacements']) if i not in removed]
    require(checked == 219807, 'Continuous retained height-only count differs')
    return output


def _restored(plan, rows, groups, context, neighborhood, measured, spatial):
    require(len(rows) == 39834 and len(groups) == 164, 'Continuous restored root/group census differs')
    expected_pairs = [(name, i) for name in ARRAYS for i in neighborhood['groundDetailRemovedPlacementIndices'][name]
                      if _safe(spatial[0], context[name][i]['positionCm'][:2])]
    pairs = [(row['sourceArray'], row['sourceIndex']) for row in rows]
    require(pairs == expected_pairs and Counter(name for name, _ in pairs) == Counter({ARRAYS[0]: 34447, ARRAYS[1]: 5387}),
            'Continuous exact original removed root restoration membership/order differs')
    expected, rng = {}, random.Random(260920263)
    prototypes = {row['id']: row for row in plan['nativeOriginalPrototypes']}
    for row in rows:
        require(type(row['sourceIndex']) is int and row['sourceArray'] in ARRAYS and finite(row['positionCm'], 3) and
                finite(row['yawDeg']) and finite(row['scale'], 3) and finite(row['proposedHeightCm']) and row['proposedHeightCm'] > 0,
                'Continuous restored transform/provenance types differ')
        original = context[row['sourceArray']][row['sourceIndex']]
        require(row['originalRowSha256'] == digest(original) and same(row['positionCm'], original['positionCm']) and
                same(row['yawDeg'], original['yawDeg']) and row['radiusCm'] == original['radiusCm'] == 14 and
                row['originalHeightCm'] == original['heightCm'] and row['sourceGroundMeshId'] == original['sourceMeshId'],
                'Continuous restored original XY/Z/yaw/radius/source row changed')
        _crown(row['positionCm'], spatial, original['sourceMeshId'], original['positionCm'][2])
        height, condition, tall, edge = _field(row['positionCm'], spatial[4], row['sourceArray'])
        require(all(finite(row[key]) and abs(row[key]-value) < 1e-6 for key, value in
                    (('proposedHeightCm', height), ('growthCondition', condition), ('tallGrowthAmount', tall), ('existingRoadEdgeDisturbance', edge))),
                'Continuous restored coherent growth field differs')
        identity = f'LawnTuft{rng.randrange(4)}'
        actual, prototype = measured[identity], prototypes[identity]
        x, y = row['positionCm'][:2]
        gid = f'EX_meadow_restored_{math.floor(x/2000)}_{math.floor(y/2000)}_{identity}'
        scale = [14/actual['radiusCm'], 14/actual['radiusCm'], row['proposedHeightCm']/actual['heightCm']]
        require(row['meshId'] == identity and row['groupId'] == gid and all(abs(a-b) < 1e-12 for a, b in zip(row['scale'], scale)),
                'Continuous restored native prototype/scale/group proof differs')
        group = expected.setdefault(gid, {'id': gid, 'meshId': identity, 'nativeMesh': prototype['nativeMesh'],
            'nativeMaterial': prototype['nativeMaterial'], 'instances': [], 'role': 'grass', 'qualityDetail': True,
            'densityScaling': True, 'cullStartCm': 7200, 'cullEndCm': 9000, 'castShadow': False, 'collision': 'NoCollision', 'navigation': False})
        group['instances'].append({key: row[key] for key in ('positionCm', 'yawDeg', 'scale', 'sourceArray', 'sourceIndex')})
    return _native_groups(groups, list(expected.values()))


def _native_groups(groups, expected):
    require(len(groups) == len(expected) == 164 and same(groups, expected),
            'Continuous canonical ordered native group transforms/policies differ')
    result = deepcopy(groups)
    for group in result:
        group['canEverAffectNavigation'] = False
    return result


def validated_layout(plan, source_context, neighborhood, transition, scene_sha, obj_sha):
    """Return retained arrays, soil subsets and164 explicit original-asset groups.

    Requires exact unfiltered R8 context and original R3 neighborhood; do not
    apply the old R3 removal filter a second time to returned retained arrays.
    No old transition/pilot placements are returned or described as applied.
    """
    approved, receipt, sources, sidecars = _bundle()
    _validate_identity(plan, source_context, neighborhood, transition, scene_sha, obj_sha, approved, sources)
    input_pins = {**plan['inputFiles'], **{str(STUDY/name): expected for name, expected in PINS.items()},
                  **{str(ROOT/'scripts/unreal'/name): expected for name, expected in DELEGATES.items()},
                  str(ROOT/OWNER): sha(ROOT/OWNER)}
    for path, expected in input_pins.items():
        pinned(path, expected)
    require(receipt['checks']['frozenPinsUnchangedBeforeAfter'] is True and
            receipt['checks']['independentAllowedDomainSymmetricDifferenceCm2'] < 1e-5 and
            same(plan['targetGroundDomainCm'], transition['targetGroundDomainCm']), 'Continuous pinned source GEOS domain proof differs')
    for name, dimensions in (('planview-comparison.png', (2216, 1192)), ('soil-triangle-mask.png', (1100, 1192)),
                             ('restored-root-map.png', (1100, 1192)), ('continuous-growth-field.png', (1100, 1100))):
        _png_structure(STUDY/name, dimensions)
    meshes = _soil(plan, neighborhood, sidecars['cultivated-soil-subsets.json'], source_context)
    measured = _prototypes(plan, sources['prototypes.json'], sources['nativeReceipt'])
    spatial = _spatial(plan, source_context, neighborhood, sources['building-plan.json'])
    require(len(plan['materialBindingProposal']) == 65 and same(plan['materialBindingProposal'], transition['materialBindingProposal']),
            'Continuous exact65 material bindings differ')
    require(set(spatial[3]) == {row['sourceMeshId'] for row in plan['materialBindingProposal']} and
            all(row['sourceGeometrySha256'] == digest(spatial[3][row['sourceMeshId']]) and
                row['expectedMaterialKey'] == spatial[3][row['sourceMeshId']]['material'] and
                row['sourceVerticesAndIndicesUnchanged'] is True and row['proposedSharedMaterialKey'] == 'context_continuous_unbuilt_ground'
                for row in plan['materialBindingProposal']), 'Continuous base65 geometry/material source boundary differs')
    groups = _restored(plan, sidecars['restored-roots.json'], sidecars['restored-groups.json'], source_context, neighborhood, measured, spatial)
    retained = _retained(source_context, neighborhood, sidecars['retained-height-overrides.json'], spatial)
    infill = sources['meadow-infill-plan.json']
    require(len(transition['groups']) == 158 and len(transition['transitionPlacements']) == 7000 and
            len(infill['groups']) == 101 and len(infill['infillPlacements']) == 33483 and
            plan['futureVisualRetirement']['transitionGroupIds'] == [g['id'] for g in transition['groups']] and
            plan['futureVisualRetirement']['pilotGroupIds'] == [g['id'] for g in infill['groups']] and
            plan['futureVisualRetirement']['retirementActuallyAppliedToNative'] is False, 'Continuous historical retirement source references differ')
    retirement = [{'sourcePlan': {'path': plan['futureVisualRetirement'][key], 'sha256': plan['inputFiles'][plan['futureVisualRetirement'][key]]},
                   'historicalSourceGroups': count, 'historicalSourceInstances': instances, 'placementsReturnedForUse': 0,
                   'retirementActuallyAppliedToNative': False}
                  for key, count, instances in (('transitionPlan', 158, 7000), ('pilotPlan', 101, 33483))]
    for path, expected in input_pins.items():
        pinned(path, expected)
    audit = {'status': 'VERIFIED_STDLIB_CONTINUOUS_LAYOUT_SOURCE_INPUTS_NATIVE_PENDING', 'owner': OWNER,
        'sourceInputsValidated': True, 'nativeGeometryDecodedOrSaved': False, 'nativeApplied': False,
        'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False,
        'restoredInstances': 39834, 'restoredGroups': 164, 'retainedHeightOnlyOverrides': 219807,
        'retainedArrayCounts': {name: len(rows) for name, rows in retained.items()},
        'omittedUnbuiltSoilTriangles': 103392, 'retainedCultivatedSoilTriangles': 2801,
        'neighborhoodMeshes': len(meshes), 'neighborhoodTriangles': 142105, 'materialBindings65': 65,
        'restoredAllLodSourceTriangles': [10197504, 2549376, 956016], 'sourcePrototypeLodsDecoded': 12,
        'nativeOriginalAssetLookupEvidence': 'PINNED_HISTORICAL_R14_RECEIPT_ONLY',
        'allChangedWhole141mmCrownsRechecked': 259641, 'authenticPrivateRoadBuildingMasksRechecked': True,
        'soilTriangleCentroidMembershipRechecked': 106193,
        'soilPartitionEvidence': 'STDLIB_ORIGINAL_GROUND_CENTROID_MEMBERSHIP_AND_EXACT_SOURCE_TRIANGLE_ORDINALS',
        'domainBooleanUnionRecomputedHere': False, 'domainEvidence': 'PINNED_GEOS_SOURCE_PREFLIGHT_PLUS_STDLIB_PER_CROWN_MASK_CHECKS',
        'worldHeightFieldRecomputedHere': True, 'fourDiagnosticPngStructuresValidated': True,
        'originalPositionsYawRadiusAndGround65Preserved': True, 'allSevenCultivatedSourceRowsPreserved': True,
        'oldTransitionPilotClaimsAreHistoricalReferencesOnly': True}
    return {'plan': {'path': str(STUDY/'continuous-meadow-plan.json'), 'sha256': PLAN_SHA},
            'retainedContextArrays': retained, 'neighborhoodMeshes': meshes, 'restoredGroups': groups,
            'materialBindings65': deepcopy(plan['materialBindingProposal']), 'retirementHistoricalSourcePlans': retirement,
            'inputPins': input_pins, 'audit': audit}
