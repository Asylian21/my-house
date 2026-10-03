"""R20 original curved-grass geometry and exact-root CPU guards."""
from collections import Counter
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-curved-grass-guards.py'
PREFIX = '/Game/Brezi/CurvedGrass20261001R20'
TAG = 'BreziCurvedGrass20261001R20'
MATERIAL_KEY = 'ph_original_grass_medium_01_r20'
SOURCE = ROOT / 'output/unreal/exterior-ph-vegetation-reference-20261001-r1/grass_medium_01'
SOURCE_GLTF_SHA = 'aed63929a83fb694e6884e3a5c0fdb962ab8cf9153830247c8201a482ff02664'
SOURCE_BIN_SHA = 'f4587cabdb96a2e96d8be644923dc954a248edfaaa717a0ff224cacb898bee1f'
BASE = ROOT / 'output/unreal/exterior-20261001-r16a'
SCHEMA = 'brezi-original-curved-grass-root-replacement-r1'
STATUS = 'source-only-original-curved-grass-root-replacement-native-pending'
MASTERS = {'small_a': {'node': 'grass_medium_01_small_a_LOD0', 'mesh': 0, 'triangles': 833, 'instances': 24},
           'small_b': {'node': 'grass_medium_01_small_b_LOD0', 'mesh': 6, 'triangles': 653, 'instances': 24},
           'tall_c': {'node': 'grass_medium_01_tall_c_LOD0', 'mesh': 5, 'triangles': 340, 'instances': 16}}
EVIDENCE_PLAN = ROOT / 'output/unreal/exterior-canopy-transmission-20261001-r1-study/canopy-transmission-plan.json'
EVIDENCE_PLAN_SHA = '2f9032afd061b5681844911959fb9247af8a1197a2c8cded78f1ee5cdbcd0ccb'
SHARED = ROOT / 'scripts/unreal/exterior-canopy-transmission-native.py'
SHARED_SHA = '10cc942f098e130f8f22f0acb9948f4381bdc0226d5db2af17a4665fd701bc6b'
old = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    spec = importlib.util.spec_from_file_location('curved_grass_immutable_generic', SHARED)
    common = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(common)
finally:
    sys.dont_write_bytecode = old
require, read, write, sha, pin, check_pin, digest, now = (
    getattr(common, key) for key in ('require', 'read', 'write', 'sha', 'pin', 'check_pin', 'digest', 'now'))
require(sha(SHARED) == SHARED_SHA, 'Immutable generic base helper changed')


def f32(v): return struct.unpack('<f', struct.pack('<f', v))[0]
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def norm(v): return math.sqrt(dot(v, v))
def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
def unit(v):
    length = norm(v)
    require(length > 1e-15, 'Undefined geometric tangent')
    return [x / length for x in v]


def accessor(document, binary, index):
    row = document['accessors'][index]
    require('sparse' not in row and not row.get('normalized', False), 'Unsupported sparse/normalized original accessor')
    view = document['bufferViews'][row['bufferView']]
    require(view.get('buffer', 0) == 0, 'Foreign original binary buffer')
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[row['type']]
    fmt = {5126: 'f', 5123: 'H', 5125: 'I'}[row['componentType']]
    size = struct.calcsize(fmt) * width
    stride = view.get('byteStride', size)
    start = view.get('byteOffset', 0) + row.get('byteOffset', 0)
    require(stride >= size and start >= 0 and start + (row['count'] - 1) * stride + size <= len(binary),
            'Original accessor outside its binary')
    return [list(struct.unpack_from('<' + fmt * width, binary, start + i * stride)) for i in range(row['count'])]


def original_meshes():
    source_file = SOURCE / 'grass_medium_01_2k.gltf'
    binary_file = SOURCE / 'grass_medium_01.bin'
    require(sha(source_file) == SOURCE_GLTF_SHA and sha(binary_file) == SOURCE_BIN_SHA, 'Original PH model source drifted')
    document, binary = read(source_file), binary_file.read_bytes()
    require(document['materials'][0] == {'alphaMode': 'BLEND', 'doubleSided': True, 'name': 'grass_medium_01',
            'normalTexture': {'index': 0}, 'pbrMetallicRoughness': {'baseColorTexture': {'index': 1},
            'metallicFactor': 0, 'metallicRoughnessTexture': {'index': 2}}}, 'Original provider material differs')
    result = {}
    for key, spec in MASTERS.items():
        nodes = [node for node in document['nodes'] if node['name'] == spec['node']]
        require(len(nodes) == 1 and nodes[0]['mesh'] == spec['mesh'], 'Original selected node/mesh differs')
        mesh = document['meshes'][spec['mesh']]
        require(len(mesh['primitives']) == 1, 'Original primitive population differs')
        primitive = mesh['primitives'][0]
        require(primitive.get('mode', 4) == 4 and primitive['material'] == 0
                and set(primitive['attributes']) == {'POSITION', 'NORMAL', 'TEXCOORD_0'}, 'Original attributes/material/topology differ')
        positions = accessor(document, binary, primitive['attributes']['POSITION'])
        normals = accessor(document, binary, primitive['attributes']['NORMAL'])
        uv = accessor(document, binary, primitive['attributes']['TEXCOORD_0'])
        indices = [value[0] for value in accessor(document, binary, primitive['indices'])]
        require(len(indices) == spec['triangles'] * 3 and len(normals) == len(uv) == len(positions), 'Original source counts differ')
        minimum_y = min(p[1] for p in positions)
        result[key] = {'id': 'curved_grass_r20_' + key, 'providerNode': nodes[0],
            'providerMeshName': mesh['name'], 'sourceAccessors': primitive, 'originalPositionsMetersYUp': positions,
            'originalNormalsYUp': normals, 'originalUV0': uv, 'originalIndices': indices,
            'originalMinimumYMeters': minimum_y, 'originalHeightCm': (max(p[1] for p in positions) - minimum_y) * 100,
            'originalRadialEnvelopeCm': max(math.hypot(p[0], p[2]) * 100 for p in positions)}
    return result


def computed_tangents(positions, normals, uv, indices):
    tangent = [[0., 0., 0.] for _ in positions]
    bitangent = [[0., 0., 0.] for _ in positions]
    minimum_uv_det = float('inf')
    for start in range(0, len(indices), 3):
        a, b, c = indices[start:start+3]
        e1, e2 = ([positions[b][i] - positions[a][i] for i in range(3)],
                  [positions[c][i] - positions[a][i] for i in range(3)])
        uv1, uv2 = ([uv[b][i] - uv[a][i] for i in range(2)], [uv[c][i] - uv[a][i] for i in range(2)])
        determinant = uv1[0] * uv2[1] - uv2[0] * uv1[1]
        minimum_uv_det = min(minimum_uv_det, abs(determinant))
        require(abs(determinant) > 1e-15, 'Original UV does not define a tangent frame')
        area = norm(cross(e1, e2)) * .5
        require(area > 1e-14, 'Original geometry has a degenerate triangle')
        t = [(e1[i] * uv2[1] - e2[i] * uv1[1]) / determinant for i in range(3)]
        bvec = [(e2[i] * uv1[0] - e1[i] * uv2[0]) / determinant for i in range(3)]
        for vertex in (a, b, c):
            for axis in range(3):
                tangent[vertex][axis] += t[axis] * area
                bitangent[vertex][axis] += bvec[axis] * area
    result = []
    for normal, t, b in zip(normals, tangent, bitangent):
        normal_unit = unit(normal)
        t = unit([t[i] - normal_unit[i] * dot(normal_unit, t) for i in range(3)])
        sign = -1. if dot(cross(normal_unit, t), b) < 0 else 1.
        result.append([f32(x) for x in t] + [sign])
    return result, {'method': 'Original UV derivatives; area-weighted vertex sum; Gram-Schmidt against provided normal; UV handedness.',
                    'providerTangentsPresent': False, 'fallbackFrames': 0, 'minimumOriginalUVDeterminant': minimum_uv_det}


def converted_geometry(originals):
    result = []
    for key, row in originals.items():
        # Keep the original right-handed Y-up model in the GLB. UE's pinned
        # ConvertVec3 maps[x,z,y]. No reference-sheet node translation applies.
        positions = [[p[0], f32(p[1] - row['originalMinimumYMeters']), p[2]] for p in row['originalPositionsMetersYUp']]
        tangents, proof = computed_tangents(positions, row['originalNormalsYUp'], row['originalUV0'], row['originalIndices'])
        vertices_cm = [[f32(p[0] * 100), f32(p[2] * 100), f32(p[1] * 100)] for p in positions]
        result.append({'id': row['id'], 'kind': key, 'material': MATERIAL_KEY,
            'sourceNode': MASTERS[key]['node'], 'sourceMesh': MASTERS[key]['mesh'],
            'positionMetersYUp': positions, 'normalYUp': row['originalNormalsYUp'], 'uv0': row['originalUV0'],
            'indices': row['originalIndices'], 'tangentYUp': tangents, 'tangentProof': proof,
            'expectedNativeVerticesCm': vertices_cm,
            'expectedNativeNormals': [[v[0], v[2], v[1]] for v in row['originalNormalsYUp']],
            'rootShiftOriginalYMeters': row['originalMinimumYMeters'], 'displayNodeTransformApplied': False,
            'rootedHeightCm': max(p[2] for p in vertices_cm),
            'rootedRadialEnvelopeCm': max(math.hypot(*p[:2]) for p in vertices_cm),
            'triangles': MASTERS[key]['triangles'], 'vertices': len(positions),
            'lods': [{'level': level, 'triangles': MASTERS[key]['triangles'],
                     'representation': 'Identical copy of complete original LOD0; no provider LOD chain or simplification.'}
                    for level in range(3)],
            'normalSourcePreserved': True, 'originalUVIndexOrderPreserved': True,
            'geometryNativeVerified': False, 'nativeAppearanceAccepted': False})
    return result


def validate_geometry(rows, originals):
    require(len(rows) == len({r['id'] for r in rows}) == 3, 'Exactly three original masters required')
    expected = converted_geometry(originals)
    require(rows == expected, 'Source geometry changed outside original Y-root shift/computed tangents')
    require(sum(r['triangles'] * MASTERS[r['kind']]['instances'] for r in rows) == 41104, 'Fixed full pilot triangle cost differs')
    for row in rows:
        require(min(p[2] for p in row['expectedNativeVerticesCm']) == 0., 'New geometry is not rooted')
        require(max(abs(norm(v)-1) for v in row['normalYUp']) < 2e-7, 'Original provided normal unit error differs')
        require(max(abs(norm(v[:3])-1) for v in row['tangentYUp']) < 2e-7, 'Computed tangent is not unit')
        require(max(abs(dot(v, t[:3])) for v, t in zip(row['normalYUp'], row['tangentYUp'])) < 2e-7,
                'Computed tangent is not orthogonal')
    return {'originalMeshIdentitiesPreserved': True, 'displayNodeTranslationsIgnored': True,
            'originalPositionNormalUVIndexOrderPreservedExceptRootAndBasis': True,
            'computedTangentsFromOriginalUVVerified': True, 'newMasters': 3, 'pilotLODs': 9,
            'pilotTriangleCostsByLod': [41104, 41104, 41104], 'nativeGeometryVerified': False}


def write_glb(path, rows):
    document = {'asset': {'version': '2.0', 'generator': 'scripts/unreal/exterior-curved-grass-study.py'},
                'scene': 0, 'scenes': [{'nodes': list(range(3))}], 'nodes': [], 'meshes': [],
                'materials': [{'name': MATERIAL_KEY}], 'buffers': [], 'bufferViews': [], 'accessors': []}
    binary = bytearray()
    def put(values, kind, target):
        while len(binary) % 4: binary.append(0)
        start = len(binary)
        flat = [v for row in values for v in row] if kind != 'SCALAR' else values
        fmt = 'I' if kind == 'SCALAR' else 'f'
        block = struct.pack('<' + fmt * len(flat), *flat)
        binary.extend(block)
        document['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(block), 'target': target})
        record = {'bufferView': len(document['bufferViews']) - 1, 'componentType': 5125 if kind == 'SCALAR' else 5126,
                  'count': len(values), 'type': kind}
        if kind == 'VEC3':
            record.update(min=[min(v[i] for v in values) for i in range(3)], max=[max(v[i] for v in values) for i in range(3)])
        document['accessors'].append(record)
        return len(document['accessors']) - 1
    for index, row in enumerate(rows):
        attrs = {key: put(row[field], kind, 34962) for key, field, kind in (
            ('POSITION', 'positionMetersYUp', 'VEC3'), ('NORMAL', 'normalYUp', 'VEC3'),
            ('TEXCOORD_0', 'uv0', 'VEC2'), ('TANGENT', 'tangentYUp', 'VEC4'))}
        indices = put(row['indices'], 'SCALAR', 34963)
        name = row['id'] + '_LOD0'
        document['nodes'].append({'name': name, 'mesh': index})
        document['meshes'].append({'name': name, 'primitives': [{'attributes': attrs, 'indices': indices, 'material': 0, 'mode': 4}]})
    document['buffers'] = [{'byteLength': len(binary)}]
    text = json.dumps(document, separators=(',', ':')).encode()
    text += b' ' * ((-len(text)) % 4)
    Path(path).write_bytes(struct.pack('<4sII', b'glTF', 2, len(text) + len(binary) + 28)
                          + struct.pack('<II', len(text), 0x4e4f534a) + text
                          + struct.pack('<II', len(binary), 0x004e4942) + binary)


def decode_glb(path, rows):
    raw = Path(path).read_bytes()
    require(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'New GLB header differs')
    length, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a, 'New GLB JSON missing')
    document = json.loads(raw[20:20+length])
    size, kind = struct.unpack_from('<II', raw, 20+length)
    require(kind == 0x004e4942, 'New GLB BIN missing')
    binary = raw[28+length:28+length+size]
    require(len(document['nodes']) == len(document['meshes']) == len(rows) == 3, 'New GLB population differs')
    for index, row in enumerate(rows):
        require(document['nodes'][index] == {'name': row['id'] + '_LOD0', 'mesh': index}, 'A display transform was introduced')
        primitive = document['meshes'][index]['primitives'][0]
        for key, field in [('POSITION', 'positionMetersYUp'), ('NORMAL', 'normalYUp'), ('TEXCOORD_0', 'uv0'), ('TANGENT', 'tangentYUp')]:
            require(accessor(document, binary, primitive['attributes'][key]) == row[field], 'GLB original attribute changed: ' + key)
        require([v[0] for v in accessor(document, binary, primitive['indices'])] == row['indices'], 'GLB original index order changed')
    return {'sourceGLBDecoded': True, 'attributesIndexOrderAndRootShiftVerified': True,
            'masters': 3, 'serializedGLBLODs': 3, 'nativeCopiesNeededForIdenticalPilotLODs': 6,
            'nativeGeometryVerified': False}


def source_candidates(placements, prototypes, camera):
    height = {r['id'].split('_LOD')[0]: max(v[2] for v in r['verticesMm']) / 10
              for r in prototypes if r['lod'] == 0}
    radius = {key: max(math.hypot(v[0], v[1]) / 10 for r in prototypes if r['id'].startswith(key + '_LOD')
                       for v in r['verticesMm']) for key in height}
    direction = [camera['targetCm'][i] - camera['eyeCm'][i] for i in range(3)]
    forward = unit(direction)
    right = unit([forward[1], -forward[0], 0.])
    up = cross(right, forward)
    tangent = math.tan(math.radians(camera['horizontalFovDegrees'] / 2))
    result = []
    for group in placements:
        if not group['id'].startswith('EX_meadow_') or group['id'].startswith('EX_meadow_restored_'): continue
        require(group['meshId'] in height, 'Foreign original retained meadow prototype')
        for index, row in enumerate(group['instances']):
            delta = [row['positionCm'][i] - camera['eyeCm'][i] for i in range(3)]
            distance, depth = norm(delta), dot(delta, forward)
            authored_height = height[group['meshId']] * row['scale'][2]
            if not (400 <= distance <= 1500 and authored_height >= 12 and depth > 0
                    and abs(dot(delta, right)) < depth * tangent and abs(dot(delta, up)) < depth * tangent * 9 / 16): continue
            old_radius = radius[group['meshId']] * row['scale'][0]
            require(abs(old_radius - 14.) < 1e-9, 'Old source crown safety is not14cm')
            result.append({'groupId': group['id'], 'instanceIndex': index, 'oldMasterId': group['meshId'],
                'originalSourceRow': copy.deepcopy(row), 'authoredHeightCm': authored_height,
                'cameraDistanceCm': distance, 'originalAllLodRadiusCm': old_radius})
    return sorted(result, key=lambda r: (r['cameraDistanceCm'], r['groupId'], r['instanceIndex']))


def select_roots(candidates, geometry):
    by_kind = {r['kind']: r for r in geometry}
    selected, identities = [], set()
    # Constrained short/medium original clumps get their exact24 roots first;
    # the tall shape then uses remaining taller roots. All are retained source.
    for kind in ('small_b', 'small_a', 'tall_c'):
        mesh, spec = by_kind[kind], MASTERS[kind]
        suitable = [row for row in candidates if (row['groupId'], row['instanceIndex']) not in identities
                    and row['authoredHeightCm'] / mesh['rootedHeightCm'] * mesh['rootedRadialEnvelopeCm'] <= 13.9999]
        require(len(suitable) >= spec['instances'], 'Insufficient visible retained roots fitting the original full shape')
        # Round-robin1m source cells spreads the bounded64trial, then fill
        # repeated cells by their measured camera distance; no new roots.
        cells = {}
        for row in suitable:
            xy = row['originalSourceRow']['positionCm']
            cells.setdefault((math.floor(xy[0]/100), math.floor(xy[1]/100)), []).append(row)
        ordered = []
        while cells:
            for key in list(cells):
                ordered.append(cells[key].pop(0))
                if not cells[key]: del cells[key]
        chosen = ordered[:spec['instances']]
        for row in chosen:
            scale = row['authoredHeightCm'] / mesh['rootedHeightCm']
            actual_radius = max(math.hypot(p[0] * scale, p[1] * scale) for p in mesh['expectedNativeVerticesCm'])
            require(actual_radius <= 14. and abs(mesh['rootedHeightCm'] * scale - row['authoredHeightCm']) < 1e-12,
                    'Uniform original-shape height/radius fit failed')
            identities.add((row['groupId'], row['instanceIndex']))
            selected.append({**row, 'newMasterId': mesh['id'], 'kind': kind, 'uniformScale': scale,
                'newSourceRow': {'positionCm': row['originalSourceRow']['positionCm'],
                                 'yawDeg': row['originalSourceRow']['yawDeg'], 'scale': [scale] * 3},
                'scaledAllVertexRadiusCm': actual_radius,
                'allVertexWholeCrownSafetyRadiusCm': 14., 'originalExclusionCrownRadiusCm': 14.1})
    return sorted(selected, key=lambda r: (r['groupId'], r['instanceIndex']))


def validate_selection(selected, placements, prototypes, camera, geometry):
    expected = select_roots(source_candidates(placements, prototypes, camera), geometry)
    require(selected == expected and len({(r['groupId'], r['instanceIndex']) for r in selected}) == 64,
            'Pilot roots/height/yaw/scale/retained identity changed')
    require(Counter(r['kind'] for r in selected) == {'small_a': 24, 'small_b': 24, 'tall_c': 16}, 'Fixed64mix differs')
    require({r['groupId'] for r in selected} == {'EX_meadow_-3_2_LawnTuft' + str(i) for i in range(4)},
            'Pilot escapes the measured four retained components')
    return {'selectedRoots': 64, 'affectedOriginalGroups': 4, 'newGroups': 3, 'newInstances': 64,
            'removedInstances': 64, 'netPopulationChange': 0, 'minimumCameraDistanceCm': min(r['cameraDistanceCm'] for r in selected),
            'maximumCameraDistanceCm': max(r['cameraDistanceCm'] for r in selected),
            'authoredHeightRangeCm': [min(r['authoredHeightCm'] for r in selected), max(r['authoredHeightCm'] for r in selected)],
            'maximumNewScaledVertexRadiusCm': max(r['scaledAllVertexRadiusCm'] for r in selected),
            'rootYawAuthoredHeightPreserved': True, 'uniformOriginalShapeScalingOnly': True,
            'restoredRootsSelected': 0, 'managedLawnInstancesChanged': 0, 'nativeVerified': False}


def native_instance_value(component, index):
    value = component.get_instance_transform(index, False)
    if isinstance(value, tuple) and len(value) == 2 and value[0] is True: value = value[1]
    require(value is not None and hasattr(value, 'translation'), 'Actual native instance transform unavailable')
    return [[float(getattr(value.translation, axis)) for axis in 'xyz'],
            [float(getattr(value.rotation, axis)) for axis in 'xyzw'],
            [float(getattr(value.scale3d, axis)) for axis in 'xyz']]


def expected_original_witness(before, selected, original_instances, base_groups):
    result = copy.deepcopy(before)
    changes = []
    for group_id in sorted({r['groupId'] for r in selected}):
        original = base_groups[group_id]
        removed = {r['instanceIndex'] for r in selected if r['groupId'] == group_id}
        values = original_instances[group_id]
        require(len(values) == original['instances'] and digest(values) == original['transformsSha256'],
                'Actual original ordered transform witness differs')
        actor = result[original['actor']]
        components = [c for c in actor['components'] if c.get('mesh') == original['mesh']]
        require(len(components) == 1, 'Original target component ambiguous')
        c = components[0]
        require(c['instanceCount'] == len(values) and c['orderedInstanceTransformsSha256'] == digest(values),
                'Original target before witness differs')
        retained_indices = retained_swap_indices(len(values), removed)
        retained = [values[index] for index in retained_indices]
        require(len(values) - len(retained) == len(removed), 'Root removal selection differs')
        c['instanceCount'] = len(retained)
        c['orderedInstanceTransformsSha256'] = digest(retained)
        changes.append({'groupId': group_id, 'actor': original['actor'], 'component': c['path'],
                        'removedOriginalIndices': sorted(removed), 'originalInstances': len(values),
                        'retainedOriginalIndicesInNativeOrder': retained_indices,
                        'retainedInstances': len(retained), 'originalTransformsSha256': digest(values),
                        'retainedTransformsSha256': digest(retained)})
    require(len(changes) == 4 and sum(len(r['removedOriginalIndices']) for r in changes) == 64,
            'Exactly64members in four original groups required')
    return result, changes


def retained_swap_indices(count, removed):
    """UE5.8 HISM RemoveInstancesInternal forces descending RemoveAtSwap.

    Preserve the original stored matrices instead of decomposing/recreating
    every retained instance. Native ordering changes exactly as this function.
    """
    require(len(removed) == len(set(removed)) and all(type(i) is int and 0 <= i < count for i in removed),
            'Duplicate/out-of-bounds native root removal')
    indices = list(range(count))
    for index in sorted(removed, reverse=True):
        indices[index] = indices[-1]
        indices.pop()
    require(set(indices) == set(range(count)) - set(removed), 'Native removal changed an unselected member')
    return indices
