"""Independent full-source ecology/hard-yard support census, CPU only.

No authored radius selects candidates. All three decoded source LODs contribute
to each model AABB; conservative transformed boxes discard distant groups and
roots before full triangle support intersection. Saved native group witnesses
bind mesh/count/order, without claiming fresh native per-root matrix decoding.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
import numpy as np
import shapely
from shapely.geometry import Point, Polygon, LineString, shape

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-attribution-completeness-r35.py'
OUT = ROOT/'output/unreal/exterior-context-yard-20261002-r35-source-completeness-r1'
INPUTS = {}


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def pin(path, expected=None):
    path = Path(path).resolve()
    require(path.is_file() and path.is_relative_to(ROOT) and not path.is_symlink(), 'Actual owned file required')
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    require(expected is None or h == expected, 'Input SHA differs: '+str(path))
    INPUTS[str(path)] = h
    return {'path': str(path), 'sha256': h, 'bytes': path.stat().st_size}


def read(path, expected=None):
    row = pin(path, expected)
    return json.loads(Path(row['path']).read_text())


def side(row):
    return read(row['path'], row['sha256'])


def glb(path):
    data = Path(path).read_bytes()
    require(data[:4] == b'glTF' and struct.unpack_from('<II', data, 4) == (2, len(data)), 'Original embedded GLB2 required')
    chunks = {}; at = 12
    while at < len(data):
        n, kind = struct.unpack_from('<II', data, at)
        require(at+8+n <= len(data) and kind not in chunks, 'Invalid/duplicate original GLB chunk')
        chunks[kind] = data[at+8:at+8+n]; at += 8+n
    require(at == len(data), 'Original GLB length differs')
    j = json.loads(chunks[0x4e4f534a]); binary = chunks[0x004e4942]
    require(len(j['buffers']) == 1 and 'uri' not in j['buffers'][0] and j['buffers'][0]['byteLength'] <= len(binary), 'Dense original binary required')
    def accessor(index):
        a = j['accessors'][index]; v = j['bufferViews'][a['bufferView']]
        require('sparse' not in a and not a.get('normalized', False) and v['buffer'] == 0, 'Original dense attribute required')
        size = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        dtype = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']])
        stride = v.get('byteStride', dtype.itemsize*size)
        start = v.get('byteOffset', 0)+a.get('byteOffset', 0)
        require(stride >= dtype.itemsize*size and a['count'] > 0 and start+(a['count']-1)*stride+size*dtype.itemsize <= len(binary), 'Original accessor range differs')
        return np.ndarray((a['count'], size), dtype=dtype, buffer=binary, offset=start, strides=(stride, dtype.itemsize)).copy()
    nodes = {}
    for node in j['nodes']:
        if 'mesh' not in node:
            continue
        require(not any(k in node for k in ('matrix', 'translation', 'rotation', 'scale')) and node['name'] not in nodes, 'Original node transforms cannot be ignored')
        parts = []
        for p in j['meshes'][node['mesh']]['primitives']:
            require(p.get('mode', 4) == 4 and 'indices' in p, 'Indexed original triangle mesh required')
            positions = accessor(p['attributes']['POSITION'])
            ids = accessor(p['indices']).reshape(-1).astype(np.int64)
            require(positions.dtype == np.dtype('<f4') and positions.shape[1] == 3 and np.isfinite(positions).all()
                    and len(ids)%3 == 0 and ids.min() >= 0 and ids.max() < len(positions), 'Finite original F32/index data required')
            # The converted vertices are expected UE source FLOAT centimetres,
            # not freshly decoded native vertices. Preserve the original bytes.
            cm = (positions[:, [0, 2, 1]]*np.float32(100)).astype(np.float32).astype(np.float64)
            parts.append({'positionsCm': cm, 'originalPositionsSha256': hashlib.sha256(positions.tobytes()).hexdigest(),
                          'indices': ids.reshape(-1, 3), 'originalIndexSequenceSha256': digest(ids.tolist())})
        nodes[node['name']] = parts
    return nodes


def overlap(a, b):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def support(points):
    xy = list(dict.fromkeys(tuple(float(x) for x in p[:2]) for p in points))
    if len(xy) == 1:
        return Point(xy[0])
    polygon = Polygon(xy) if len(xy) == 3 else None
    return polygon if polygon is not None and polygon.area > 0 else LineString(xy)


def frame(row):
    require(len(row['positionCm']) == len(row['scale']) == 3
            and all(math.isfinite(v) for v in row['positionCm']+row['scale']+[row['yawDeg']])
            and min(row['scale']) > 0, 'Finite original positive authored frame required')
    c, s = math.cos(math.radians(row['yawDeg'])), math.sin(math.radians(row['yawDeg']))
    return np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]], dtype=np.float64), np.array(row['scale']), np.array(row['positionCm'])


def transformed_bounds(corners, row):
    rotation, scale, root = frame(row)
    low, high = corners.min(axis=0), corners.max(axis=0)
    def product(interval, value):
        a, b = sorted([float(interval[0])*float(value), float(interval[1])*float(value)])
        return math.nextafter(a, -math.inf), math.nextafter(b, math.inf)
    def add(a, b):
        return math.nextafter(a[0]+b[0], -math.inf), math.nextafter(a[1]+b[1], math.inf)
    scaled = [product((low[i], high[i]), scale[i]) for i in range(3)]
    # Outward-rounded intervals enclose both scalar/FMA dot arithmetic. This
    # is a source broadphase bound, not an epsilon native pose comparison.
    xy = []
    for i in range(2):
        total = product(scaled[0], rotation[0, i])
        for j in range(1, 3):
            total = add(total, product(scaled[j], rotation[j, i]))
        xy.append(add(total, (float(root[i]), float(root[i]))))
    return [xy[0][0], xy[1][0], xy[0][1], xy[1][1]]


def intersects(group, index, row, lods, hard):
    rotation, scale, root = frame(row)
    bounds = [math.inf]*3+[-math.inf]*3
    hits, levels = set(), []
    for level, parts in enumerate(lods):
        count = Counter(); intersecting = triangles = vertices = 0
        for part in parts:
            world = (part['positionsCm']*scale)@rotation+root
            vertices += len(world)
            bounds[:3] = np.minimum(bounds[:3], world.min(axis=0)).tolist()
            bounds[3:] = np.maximum(bounds[3:], world.max(axis=0)).tolist()
            for face in part['indices']:
                triangle = support(world[face]); one = False
                for surface, domain in hard:
                    if triangle.intersects(domain):
                        count[surface['id']] += 1; hits.add(surface['id']); one = True
                intersecting += one; triangles += 1
        levels.append({'level': level, 'sourceVerticesDecoded': vertices, 'sourceTrianglesDecoded': triangles,
                       'projectedTriangleSupportsIntersectingHardFootprints': intersecting, 'hitsBySurface': dict(count)})
    if not hits:
        return None
    return {'groupId': group['id'], 'sourceGroupInstanceIndex': index, 'modelId': group['meshId'],
            'sourceFamily': row['ecologyFamily'], 'sourceRoot': row,
            'sourceAllLodWorldBoundsCm': {'min': bounds[:3], 'max': bounds[3:]},
            'intersectingHardSurfaceIds': sorted(hits), 'lodIntersections': levels,
            'allThreeSourceLodsDecoded': True, 'freshNativePerInstanceRawMatrixDecodedHere': False,
            'sourceLeafAlphaPixelsDecodedForIntersection': False, 'exactRenderedVisibleRootIdentityClaimed': False}


def main():
    require(not OUT.exists(), 'New source-only diagnostic directory required')
    started = datetime.now(timezone.utc).isoformat()
    pin(__file__)
    report = read(ROOT/'output/unreal/exterior-20261002-r32a/context-yard-ground-native-report.json', '99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19')
    witness = side(report['savedActorWitness'])
    r16 = read(ROOT/'output/unreal/exterior-20261001-r16a/exterior-import-report.json', '1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122')
    ecology = read(ROOT/'output/unreal/exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json', '27d66e0032c3b8648e5c74f80dc675efb3bee0a4efde00a1549a4502cc86b576')
    manifest = side(ecology['geometryManifest'])
    layout = read(ROOT/'output/unreal/exterior-context-yard-20261002-r28-study/yard-layout.json', '3ba5829cef341736b76a5bfce33eb961e919e7d9374ab9aed842bb2e85061ada')
    prior = read(ROOT/'output/unreal/exterior-context-yard-20261002-r35-source-diagnostic/source-attribution.json', 'f0ac8e38d58faa8409d5460b23888312d6ab20cc5b56d3ca5edcefc9b2e384fe')
    require(prior['nativeApplied'] is False and len(ecology['groups']) == 130
            and sum(len(g['instances']) for g in ecology['groups']) == 24773, 'Original ecology/pending source scope differs')
    hard = [(s, shape(s['domainCm'])) for s in layout['surfaces'] if s['role'] in ('entry_walk', 'service_court')]
    require(len(hard) == 6 and all(d.is_valid and not d.is_empty for _, d in hard), 'Exactly six existing hard footprints required')
    require([s['id'] for s, _ in hard] == prior['sourceHardSurfaceIds'], 'Hard/source scope differs')
    used_models = {g['meshId'] for g in ecology['groups']}
    all_models = {m['id']: m for m in manifest['meshes']}
    require(len(used_models) == 11 and used_models <= set(all_models), 'Exactly eleven used original ecology models required')
    models = {k: v for k, v in all_models.items() if k in used_models}
    files, summaries, corners, lods = {}, {}, {}, {}
    for model in models.values():
        path = pin(model['glbPath'], model['glbSha256'])['path']
        if path not in files:
            files[path] = glb(path)
        full = []; levels = []
        for level in range(3):
            name = model['id']+'_LOD'+str(level)
            require(name in files[path], 'Complete original three-LOD source required')
            parts = files[path][name]; full.extend(p['positionsCm'] for p in parts)
            levels.append({'level': level, 'sourceVertices': sum(len(p['positionsCm']) for p in parts),
                           'sourceTriangles': sum(len(p['indices']) for p in parts),
                           'parts': [{k: p[k] for k in ('originalPositionsSha256', 'originalIndexSequenceSha256')} for p in parts]})
        lods[model['id']] = [files[path][model['id']+'_LOD'+str(i)] for i in range(3)]
        points = np.concatenate(full); low, high = points.min(axis=0), points.max(axis=0)
        corners[model['id']] = np.array([[x, y, z] for x in (low[0], high[0]) for y in (low[1], high[1]) for z in (low[2], high[2])])
        summaries[model['id']] = {'allThreeLodExpectedSourceF32BoundsCm': {'min': low.tolist(), 'max': high.tolist()},
                                 'decodedFullSourceRadialEnvelopeCm': float(np.hypot(points[:, 0], points[:, 1]).max()), 'lods': levels}
    require(set(models) == used_models, 'Only original used ecology masters decoded')
    broad, circles, rows, group_summaries = set(), set(), [], []
    skipped_roots = candidate_roots = decoded_triangles = 0
    radius_underflow_max = 0.
    for group in ecology['groups']:
        native = r16['geometry']['groups'][group['id']]; actor = witness[native['actor']]
        components = [c for c in actor['components'] if c['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent']
        require(len(components) == 1, 'Unique original ecology component required')
        component = components[0]
        require(component['mesh'] == native['mesh'] and component['instanceCount'] == native['instances'] == len(group['instances'])
                and component['orderedInstanceTransformsSha256'] == native['transformsSha256'], 'Actual current native group/source order differs')
        require(component['transform'] == actor['transform'] == [[0., 0., 0.], [0., 0., 0., 1.], [1., 1., 1.]], 'Source roots need original identity actor/component frame')
        boxes = [transformed_bounds(corners[group['meshId']], row) for row in group['instances']]
        combined = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]
        near_group = [(s, d) for s, d in hard if overlap(combined, d.bounds)]
        for index, row in enumerate(group['instances']):
            key = (group['id'], index)
            if any(Point(row['positionCm'][:2]).distance(d) <= row['radiusCm'] for _, d in hard):
                circles.add(key)
            radius = summaries[group['meshId']]['decodedFullSourceRadialEnvelopeCm']*max(row['scale'][:2])
            radius_underflow_max = max(radius_underflow_max, radius-row['radiusCm'])
        if not near_group:
            skipped_roots += len(boxes)
            group_summaries.append({'groupId': group['id'], 'modelId': group['meshId'], 'roots': len(boxes),
                                    'conservativeSourceTransformedAabbCm': combined, 'overlappingHardSurfaceIds': [], 'sourceBoundsExcludedAllRoots': True})
            continue
        group_candidates = 0
        for index, (row, bound) in enumerate(zip(group['instances'], boxes)):
            near = [(s, d) for s, d in near_group if overlap(bound, d.bounds)]
            if not near:
                continue
            broad.add((group['id'], index)); candidate_roots += 1; group_candidates += 1
            found = intersects(group, index, row, lods[group['meshId']], near)
            decoded_triangles += sum(p['sourceTrianglesDecoded'] for p in (found['lodIntersections'] if found else
                [{'sourceTrianglesDecoded': sum(len(part['indices']) for part in parts)} for parts in lods[group['meshId']]]))
            if found:
                found.update(actualNativeActor=native['actor'], actualNativeComponent=component['path'],
                             wholeSavedGroupOrderedTransformSha256=component['orderedInstanceTransformsSha256'])
                rows.append(found)
        group_summaries.append({'groupId': group['id'], 'modelId': group['meshId'], 'roots': len(boxes),
                                'conservativeSourceTransformedAabbCm': combined,
                                'overlappingHardSurfaceIds': [s['id'] for s, _ in near_group],
                                'sourceBoundsExcludedAllRoots': False, 'fullModelAabbRootCandidates': group_candidates})
    prior_keys = {(r['groupId'], r['sourceGroupInstanceIndex']) for r in prior['selectedSourceRootCrossings']}
    selected = {(r['groupId'], r['sourceGroupInstanceIndex']) for r in rows}
    require(len(circles) == prior['originalEcologySourceCensus']['circleCandidatesNearSixHardSurfaces'] == 37
            and len(prior_keys) == 34 and candidate_roots == len(broad) and len(selected) == len(rows), 'Original comparison source census differs')
    families = Counter(row['sourceFamily'] for row in rows)
    affected = []
    for group in ecology['groups']:
        indices = sorted(i for name, i in selected if name == group['id'])
        if indices:
            native = r16['geometry']['groups'][group['id']]
            affected.append({'groupId': group['id'], 'actor': native['actor'], 'modelId': group['meshId'], 'originalInstances': len(group['instances']),
                             'selectedSourceIndices': indices, 'expectedRetainedSourceIndices': [i for i in range(len(group['instances'])) if i not in indices],
                             'originalSavedOrderedTransformsSha256': native['transformsSha256']})
    def keys(values):
        return [{'groupId': name, 'sourceGroupInstanceIndex': i} for name, i in sorted(values)]
    require(all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in INPUTS.items()), 'Frozen consumed input differs after diagnostic')
    result = {'schema': 'brezi-context-yard-full-source-support-completeness-r35', 'schemaVersion': 1, 'owner': OWNER,
              'status': 'full-source-three-lod-aabb-and-triangle-support-census-native-pending', 'startedAt': started,
              'endedAt': datetime.now(timezone.utc).isoformat(), 'interpreter': sys.executable,
              'versions': {'python': sys.version.split()[0], 'numpy': np.__version__, 'shapely': shapely.__version__},
              'actualNativeBase': pin(ROOT/'output/unreal/exterior-20261002-r32a/context-yard-ground-native-report.json'),
              'priorBoundedSourceDiagnostic': pin(ROOT/'output/unreal/exterior-context-yard-20261002-r35-source-diagnostic/source-attribution.json'),
              'activeDesign': report['activeDesign'], 'setbacksMm': report['setbacksMm'],
              'sourceHardSurfaces': [{'id': s['id'], 'sourceBoundsCm': list(d.bounds)} for s, d in hard],
              'modelFullSourceGeometry': summaries, 'groupConservativeSourceBounds': group_summaries,
              'census': {'originalGroups': 130, 'originalRoots': 24773, 'sourceModels': len(models), 'sourceLodsPerModel': 3,
                        'unusedManifestPrototypesOutsideSelectedRootScope': sorted(set(all_models)-used_models),
                        'nativeGroupMeshCountOrderHashesMatchOriginalR16': True,
                        'groupsExcludedByFullSourceAabb': sum(g['sourceBoundsExcludedAllRoots'] for g in group_summaries),
                        'rootsExcludedByGroupFullSourceAabb': skipped_roots, 'fullModelAabbRootCandidates': candidate_roots,
                        'sourceTrianglesDecodedForCandidateSupport': decoded_triangles,
                        'completeSourceTriangleSupportCrossings': len(rows), 'affectedGroups': len(affected), 'perFamily': dict(families),
                        'firstYardSourceCrossings': sum(any('BU_572063_' in s for s in row['intersectingHardSurfaceIds']) for row in rows),
                        'maximumDecodedSourceRadiusOverHistoricalRadiusCm': radius_underflow_max},
              'comparison': {'historicalRadiusCandidates': 37, 'historicalCrossings': 34,
                             'aabbCandidatesAddedVsRadius': keys(broad-circles), 'radiusCandidatesExcludedByAabb': keys(circles-broad),
                             'newTriangleSupportCrossingsAdded': keys(selected-prior_keys), 'priorTriangleSupportCrossingsRemoved': keys(prior_keys-selected)},
              'selectedSourceRootCrossings': rows, 'affectedOriginalGroups': affected,
              'sourceBasis': {'decodedPositionsOriginalFloat32': True, 'expectedSourceCm': 'float32(100*original glTF[x,z,y]); originals untouched',
                              'fullThreeLodAabbConservativeBoxCornersTransformed': True, 'authoredRadiusUsedToSelectNewCandidates': False,
                              'sourceAabbOutwardRoundedIntervalArithmetic': True,
                              'recordedAuthoredRootXYZYawScaleUsed': True, 'freshNativePerRootMatricesDecoded': False,
                              'nativeGroupBoundsNotAvailableInStoredWitness': True, 'perGroupSourceBoundsUsedInstead': True},
              'limitations': {'supportIntersectionsAreSourceGeometryNotAlphaVisibleCoverage': True,
                             'currentCameraVisibleBadPlantCountEstablished': False, 'freshNativePerRootPoseProofPerformed': False,
                             'sourcePosesBitEqualToNativeStoredFMatrixProvenHere': False, 'additionalRandomSeedRangesObserved': False,
                             'nativeRemovalAndSurvivorOrderMainSeedCustomDataProofRequired': True},
              'protectedScope': ['All8949 original managed-lawn members untouched', 'Own C/B/B architecture and both3000mm setbacks',
                                 'All78 trees, current473 garden roots,13yard shrubs and all original root/component/material controls'],
              'inputFilesBefore': dict(INPUTS), 'inputFilesAfter': dict(INPUTS), 'sourceInputsUnchanged': True,
              'nativeApplied': False, 'nativeExecuted': False, 'gpuExecuted': False, 'nativeAppearanceAccepted': False,
              'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'shippingVerified': False, 'packageVerified': False}
    OUT.mkdir()
    path = OUT/'source-completeness.json'
    path.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'receipt': pin(path), 'census': result['census'], 'comparison': result['comparison']}, allow_nan=False))


if __name__ == '__main__':
    main()
