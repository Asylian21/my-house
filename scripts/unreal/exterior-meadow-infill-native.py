"""Stdlib gate for the frozen additive, deliberately partial meadow pilot.

The original120/100 libraries are returned without changing their owners or
records. Every new crown is measured from all18 saved GLB nodes and checked
against source ground, private/road/building exclusions and the frozen pilot.
This module neither opens Unreal nor accepts native appearance/performance.
"""
from collections import defaultdict
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-meadow-infill-native.py'
ADAPTER = 'scripts/unreal/exterior-meadow-infill-integration.py'
GENERATOR = 'scripts/unreal/exterior-meadow-infill-pilot.py'
GENERATOR_SHA = '96380aa5b394e20e85001505fdae55809cc4ff727e9bef7dd13f64e8d767649d'
STUDY = ROOT/'output/unreal/exterior-meadow-infill-20261001-r1b-study'
PINS = {
    'meadow-infill-plan.json': '526f51e02cba8a89292ad2b0a90a975c15b48189c985a1a35c92510caee1529a',
    'geometry-manifest.json': '645e6749e95f0e89054e769a39e62b8fa2ea58ebe7a69f759b5c25b4a2d46d4f',
    'low-meadow.glb': '77b712725d674a0df0178c5df3829d0fe59786ab05cc3463b151fa13cb1c8b1d',
    'coverage-measurement.json': '0898b1a6af4028d02f803834e7199ed47d6bced1668ef3ffd8b0e50f4246b7f5',
    'material-manifest.json': '9392bea375a87a991a2823446b6f3c88bc7fdd40a2b6570bbe0154690c93a25f',
    'study-measurement.json': '4e4d29076facd90aeaf958aeda3879e2ddce4d25ae4dbbf4ae697a4e0c72b4e9',
    'meadow-prototypes.json': '52f2140800d4468596ac77650a794bdaf7c75f0846153cd57f22a166091383b7',
}
PHOTO = ROOT/'output/unreal/exterior-lawn-photo-integration-20261001-r1'
PHOTO_PINS = {
    'geometry-manifest.json': '45005af44e90c91fee2cbab5dcde4730b556cabe585f95d357b73b6948d69fb3',
    'material-manifest.json': '42dbaddc637c479d30482b1524217d8e9c288ff89de8f64d9f38396a1e63fbbb',
    'photo-material-manifest.json': '9a0275363882594afb4b656ffbd7528866ad63366d03cf938bf562ac6ec5c88e',
    'asset-manifest.json': '47351ceffe7c2de0a949c652e9ce19216874a4ff589a6d4676860d0d450e6481',
}
DELEGATES = {
    'exterior-lawn-photo-native.py': 'df112210114638a108eec762d6165e47163b9b450f43613287193bab9f809dfa',
    'exterior-neighborhood-transition-native.py': '892313c1b985f9e7c291f2e3cc02edad38305ae0cc607c5a3240dc0c4b3b1e4a',
    'exterior-grove-substrate-native.py': 'c27e3b935d4486e6150e262a8309223e9f72e0ef6abb9f648af5c897283f692e',
    'exterior-canopy-native.py': '2788c643f4bd924f2fa72714d18ad009a7b4aa599ba86df58baf7582f765a172',
}
STATUS = 'MEASURED_ADDITIVE_PARTIAL_MEADOW_PILOT_NOT_NATIVE_ACCEPTED'
MATERIAL = 'ph_grass_medium_02'
DESIGN = {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
IDS = {f'parcel_low_meadow_{i}' for i in range(6)}
EPS = .000002
LOD_SCREENS = [1., .15, .04]
_INSPECTION_CACHE = {}
COMMON_EXTRA = {'sourceInfillPlan', 'sourceInfillGeometry', 'sourceOriginal120Library'}


def require(value, message):
    if not value: raise RuntimeError(message)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''): result.update(block)
    return result.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def same(a, b): return digest(a) == digest(b)


def pinned(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}, 'Meadow pin shape differs')
    path = (ROOT/value['path']).resolve()
    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == value['sha256'], 'Meadow source pin drift: '+str(path))
    return path


def pin(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), 'Meadow source path escaped or missing')
    return {'path': str(path), 'sha256': sha(path)}


def read_pin(value): return json.loads(pinned(value).read_text())
def fixed(directory, name, pins): return {'path': str(directory/name), 'sha256': pins[name]}
def finite(row, size): return isinstance(row, (list, tuple)) and len(row) == size and all(type(v) in (int, float) and math.isfinite(v) for v in row)


@lru_cache(maxsize=4)
def module(filename):
    path = pinned({'path': str(ROOT/'scripts/unreal'/filename), 'sha256': DELEGATES[filename]})
    spec = importlib.util.spec_from_file_location('meadow_delegate_'+filename.replace('-', '_'), path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def native_groups(rows):
    """Canonical source order plus explicit native collision/navigation policy."""
    result = []
    for row in rows:
        group = deepcopy(row)
        group.update(cullStartCm=3200, collision='NoCollision', canEverAffectNavigation=False, densityScaling=True)
        result.append(group)
    return result


def _groups(groups, rows):
    expected = {}
    for row in rows:
        cell = [math.floor(v/400) for v in row['positionCm'][:2]]
        identity = f'EX_meadow_infill_{cell[0]}_{cell[1]}_'+row['meshId'].rsplit('_', 1)[1]
        group = expected.setdefault(identity, {'id': identity, 'meshId': row['meshId'], 'role': 'grass',
            'qualityDetail': True, 'cullEndCm': 4000, 'castShadow': True, 'instances': []})
        group['instances'].append({k: row[k] for k in ('positionCm', 'yawDeg', 'scale')})
    require(len(expected) == 101 and same(groups, list(expected.values())), 'Meadow ordered101 group transforms/policies differ')
    return native_groups(groups)


def _glb(path):
    raw = Path(path).read_bytes()
    require(len(raw) >= 28 and struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Meadow GLB header differs')
    length, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a, 'Meadow GLB JSON missing')
    doc = json.loads(raw[20:20+length]); offset = 20+length
    size, kind = struct.unpack_from('<II', raw, offset); data = raw[offset+8:]
    require(kind == 0x004e4942 and len(data) == size and doc['buffers'] == [{'byteLength': size}]
        and set(doc) == {'asset', 'scene', 'scenes', 'nodes', 'meshes', 'buffers', 'bufferViews', 'accessors', 'materials'}
        and doc['asset'] == {'version': '2.0', 'generator': GENERATOR} and doc['scene'] == 0
        and doc['scenes'] == [{'nodes': list(range(18))}] and len(doc['nodes']) == len(doc['meshes']) == 18
        and len(doc['materials']) == 1 and doc['materials'][0]['name'] == MATERIAL,
        'Meadow GLB scene/material/transform inventory differs')
    def accessor(index, kind, width, indices=False):
        a = doc['accessors'][index]; view = doc['bufferViews'][a['bufferView']]
        require(set(a) <= {'bufferView', 'componentType', 'count', 'type', 'min', 'max'}
            and a['componentType'] == (5125 if indices else 5126) and a['type'] == kind
            and type(a['count']) is int and a['count'] > 0 and set(view) == {'buffer', 'byteOffset', 'byteLength', 'target'}
            and view['buffer'] == 0 and view['target'] == (34963 if indices else 34962)
            and view['byteLength'] == a['count']*width*4 and 0 <= view['byteOffset'] <= len(data)-view['byteLength'],
            'Meadow GLB accessor packing differs')
        return list(struct.iter_unpack('<'+('I' if indices else 'f')*width,
            data[view['byteOffset']:view['byteOffset']+view['byteLength']]))
    result = {}
    attrs = {'POSITION': ('VEC3', 3), 'NORMAL': ('VEC3', 3), 'TANGENT': ('VEC4', 4),
             'TEXCOORD_0': ('VEC2', 2), 'TEXCOORD_1': ('VEC2', 2), 'COLOR_0': ('VEC4', 4)}
    for i, node in enumerate(doc['nodes']):
        require(set(node) == {'name', 'mesh'} and node['mesh'] == i and node['name'] not in result,
                'Meadow node transform/identity differs')
        mesh = doc['meshes'][i]
        require(set(mesh) == {'name', 'primitives'} and mesh['name'] == node['name'] and len(mesh['primitives']) == 1,
                'Meadow primitive inventory differs')
        p = mesh['primitives'][0]
        require(set(p) == {'attributes', 'indices', 'material'} and p['material'] == 0 and set(p['attributes']) == set(attrs),
                'Meadow primitive modifier/attributes differ')
        values = {k: accessor(p['attributes'][k], *v) for k, v in attrs.items()}
        values['indices'] = [v[0] for v in accessor(p['indices'], 'SCALAR', 1, True)]
        count = len(values['POSITION'])
        require(all(len(values[k]) == count for k in attrs) and len(values['indices']) % 3 == 0
            and all(0 <= v < count for v in values['indices'])
            and all(all(finite(v, len(v)) for v in values[k]) for k in attrs), 'Meadow GLB attribute/index extent differs')
        result[node['name']] = values
    require(set(result) == {f'{key}_LOD{lod}' for key in IDS for lod in range(3)}, 'Meadow exact18 LOD nodes differ')
    return result


def _geometry(manifest, prototypes, decoded):
    require(len(manifest['meshes']) == 6 and {m['id'] for m in manifest['meshes']} == IDS
        and len(prototypes) == 18 and {r['nodeName'] for r in prototypes} == set(decoded), 'Meadow six master census differs')
    controls = {r['nodeName']: r for r in prototypes}; measured = {}
    for master in manifest['meshes']:
        require(master['role'] == 'grass' and master['placementPolicy'] == 'explicit-only'
            and master['materialKeys'] == [MATERIAL] and [v['level'] for v in master['lods']] == [0, 1, 2]
            and master['glbPath'] == str(STUDY/'low-meadow.glb') and master['glbSha256'] == PINS['low-meadow.glb'],
            'Meadow explicit master/material/source differs')
        all_points, costs, centers = [], [], []
        for lod, row in enumerate(master['lods']):
            name = master['id']+'_LOD'+str(lod); require(row['nodeName'] == name, 'Meadow LOD identity differs')
            v = decoded[name]; points = [(100*p[0], 100*p[2], 100*p[1]) for p in v['POSITION']]
            normals = [(n[0], n[2], n[1]) for n in v['NORMAL']]
            faces = [v['indices'][i:i+3] for i in range(0, len(v['indices']), 3)]
            require(len(points) == row['vertices'] == (68, 64, 60)[lod] and len(faces) == row['triangles'] == (48, 42, 36)[lod],
                    'Meadow actual LOD vertices/triangles differ')
            bounds = {k: [f(p[axis] for p in points) for axis in range(3)] for k, f in (('min', min), ('max', max))}
            radius = max(math.hypot(p[0], p[1]) for p in points)
            require(same(bounds, row['expectedBoundsCm']) and abs(radius-row['radialEnvelopeCm']) < 1e-12
                and abs(bounds['min'][2]) < EPS, 'Meadow decoded actual bounds/root envelope differ')
            for n, t, color in zip(v['NORMAL'], v['TANGENT'], v['COLOR_0']):
                require(abs(sum(x*x for x in n)-1) < .000002 and abs(sum(x*x for x in t[:3])-1) < .000002
                    and abs(sum(a*b for a, b in zip(n, t))) < .000002 and t[3] in (-1., 1.)
                    and color == (1., 1., 1., 1.), 'Meadow decoded normal/tangent/colour invalid')
            for a, c, b in faces:
                e = [points[b][j]-points[a][j] for j in range(3)]; f = [points[c][j]-points[a][j] for j in range(3)]
                cross = [e[1]*f[2]-e[2]*f[1], e[2]*f[0]-e[0]*f[2], e[0]*f[1]-e[1]*f[0]]
                require(sum(x*x for x in cross) > 1e-10
                    and sum(cross[j]*sum(normals[k][j] for k in (a, b, c)) for j in range(3)) > 0,
                    'Meadow decoded leaf winding/degeneracy differs')
            prototype = controls[name]
            require(len(prototype['leaves']) == 12 and len(prototype['positionsCm']) == len(points)
                and all(max(abs(a-b) for a, b in zip(p, q)) < EPS for p, q in zip(points, prototype['positionsCm'])),
                'Meadow actual vertices differ from pinned twelve-leaf controls')
            vertex_offset, triangle_offset, leaf_centers = 0, 0, []
            for leaf, control in enumerate(prototype['leaves']):
                folded = leaf < (4, 2, 0)[lod]; nv, nt = (7, 6) if folded else (5, 3)
                require(control['leaf'] == leaf and control['vertexOffset'] == vertex_offset and control['triangleOffset'] == triangle_offset
                    and control['vertexCount'] == nv and control['triangleCount'] == nt and control['folded'] is folded
                    and control['pointedTip'] is True and control['tipWidthCm'] == 0
                    and .22 <= control['widthCm'] <= .35 and .33 <= control['peakT'] <= .44
                    and all(vertex_offset <= k < vertex_offset+nv for f in faces[triangle_offset:triangle_offset+nt] for k in f),
                    'Meadow true leaf partition/folded topology/width differs')
                tip = points[vertex_offset+nv-1]
                require(max(abs(a-b) for a, b in zip(tip, control['centerlineCm'][2])) < EPS,
                        'Meadow actual pointed terminal detached from centerline')
                leaf_centers.append(control['centerlineCm']); vertex_offset += nv; triangle_offset += nt
            require(vertex_offset == len(points) and triangle_offset == len(faces), 'Meadow unowned extra leaf geometry differs')
            centers.append(leaf_centers); all_points.extend(points); costs.append(len(faces))
        require(same(centers[0], centers[1]) and same(centers[0], centers[2]), 'Meadow LOD drops/moves a leaf centerline')
        height = max(p[2] for p in all_points)
        require(abs(height-master['heightCm']) < 1e-12, 'Meadow measured master height differs')
        measured[master['id']] = {'radius': max(math.hypot(p[0], p[1]) for p in all_points), 'height': height, 'triangles': costs}
    return measured


def _spatial(plan, context, neighborhood, buildings):
    transition = module('exterior-neighborhood-transition-native.py')
    substrate = module('exterior-grove-substrate-native.py')
    domains = [substrate._PolygonIndex(plan[k]) for k in ('allowedDomainCm', 'pilotDomainCm')]
    soil = substrate._PolygonIndex(read_pin(plan['sourceSoilFootprints'])['geometry'])
    blocked = [
        transition._BlockedCircles([[tri+[tri[0]]] for tri in context['protectedTrianglesCm']], 30),
        transition._BlockedCircles(transition._triangle_polygons([m for m in context['meshes'] if m['material'] == 'context_track']), 20),
        transition._BlockedCircles([[r if r[0] == r[-1] else r+[r[0]] for r in poly]
            for b in buildings['buildings'] for poly in b['polygonsCm']], 150),
    ]
    meshes = transition._source_meshes(context, neighborhood)
    return domains, soil, blocked, transition._Ground(meshes)


def _placements(rows, measured, domains, soil, blocked, ground):
    require(len(rows) == 33483, 'Meadow33483 additive root census differs')
    minimum, max_error, costs, lo, hi = math.inf, 0., [0, 0, 0], math.inf, -math.inf
    interior = 0
    for index, row in enumerate(rows):
        require(row['id'] == f'meadow_infill_{index}' and row['meshId'] in IDS and row['role'] == 'grass'
            and finite(row['positionCm'], 3) and finite(row['scale'], 3) and row['scale'][0] == row['scale'][1] == row['scale'][2]
            and .96 <= row['scale'][0] <= 1.045 and type(row['yawDeg']) in (int, float) and math.isfinite(row['yawDeg'])
            and 0 <= row['yawDeg'] < 360, 'Meadow root identity/uniform scale/frame differs')
        actual = measured[row['meshId']]; scale = row['scale'][0]
        radius, height = actual['radius']*scale, actual['height']*scale
        require(abs(radius-row['radiusCm']) < EPS and abs(height-row['actualHeightCm']) < EPS and 2 <= height <= 8,
                'Meadow decoded full crown height/radius differs')
        point = row['positionCm'][:2]; distances = []
        for domain in domains:
            d = domain.distance(point, radius+1.); distances.append(d)
            require(domain.contains(point) and d+1e-8 >= radius+.1, 'Meadow full decoded crown leaves allowed/pilot domain')
        for mask in blocked: mask.outside(point, radius+.1)
        z, identity = ground.sample(point)
        error = abs(z-row['positionCm'][2]); max_error = max(max_error, error)
        require(error < EPS and abs(z-row['sourceGroundZCm']) < EPS and row['sourceGroundMeshId'] in ground.mesh_ids_at(point),
                'Meadow root not on exact highest source65 ground triangle')
        is_soil = soil.contains(point); require(row['originalSoilInterior'] is is_soil, 'Meadow source soil membership differs')
        width = 75+15*math.sin(point[0]/110)+10*math.sin(point[1]/67)
        require(abs(width-row['contactWidthCm']) < 1e-10 and 50 <= width <= 100,
                'Meadow source variable contact band differs')
        if not is_soil:
            require(soil.distance(point, width+radius+1.)+radius+.1 <= width+1e-8,
                    'Meadow full crown exceeds outside soil contact width')
        costs = [a+b for a, b in zip(costs, actual['triangles'])]
        interior += is_soil; minimum = min(minimum, distances[0]-radius); lo, hi = min(lo, height), max(hi, height)
    require(costs == [1607184, 1406286, 1205388] and costs[0] <= 2000000 and interior == 20646,
            'Meadow actual LOD population budget/interior count differs')
    return {'instances': len(rows), 'groups': 101, 'masters': 6, 'lods': 18, 'allLodTriangles': costs,
        'actualHeightCm': [lo, hi], 'minimumFullCrownSourceClearanceCm': minimum,
        'maximumRootGroundErrorCm': max_error, 'insideSoilInstances': interior, 'outsideContactInstances': len(rows)-interior,
        'all18DecodedGeometryFramesAnd12LeafLodsVerified': True, 'allLodCircularCrownsChecked': True,
        'source65GroundAndPrivateRoadBuildingMasksChecked': True, 'NoCollision': True, 'canEverAffectNavigation': False}


def inspect_study(plan, manifest, scene_sha, obj_sha):
    approved = read_pin(fixed(STUDY, 'meadow-infill-plan.json', PINS))
    require(same(plan, approved) and same(manifest, read_pin(fixed(STUDY, 'geometry-manifest.json', PINS))),
            'Meadow immutable selected study plan/geometry differs')
    require(plan['owner'] == GENERATOR and plan['generatorSha256'] == GENERATOR_SHA and sha(ROOT/GENERATOR) == GENERATOR_SHA
        and plan['activeDesign'] == DESIGN and plan['sourceSceneSha256'] == scene_sha and plan['sourceObjSha256'] == obj_sha
        and plan['housePlacement']['streetSetbackMm'] == plan['housePlacement']['eastSetbackMm'] == 3000
        and all(plan[k] is False for k in ('nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'integrationAuthorized')),
        'Meadow canonical owner/source/frame/acceptance differs')
    for path, expected in plan['inputFiles'].items(): pinned({'path': path, 'sha256': expected})
    require(same(manifest['inputFiles'], plan['inputFiles']), 'Meadow geometry source closure differs')
    context, neighborhood, transition, buildings = [read_pin(plan[k]) for k in
        ('sourceContext', 'sourceNeighborhood', 'sourceTransition', 'sourceBuildingPlan')]
    require(all(d['sourceSceneSha256'] == scene_sha and d['sourceObjSha256'] == obj_sha for d in (context, neighborhood, transition, buildings))
        and same(context['activeDesign'], DESIGN) and same(context['housePlacement'], plan['housePlacement'])
        and same(plan['allowedDomainCm'], transition['targetGroundDomainCm']), 'Meadow source frame/65 ground domain differs')
    preservation = plan['preservation']
    require(len(transition['transitionPlacements']) == 7000 and digest(transition['transitionPlacements']) == preservation['originalTransitionPlacementsSha256']
        and digest(transition['groups']) == preservation['originalTransitionGroupsSha256']
        and digest(neighborhood['groundDetailRemovedPlacementIndices']) == preservation['originalRemovalIndicesSha256']
        and sum(len(v) for v in neighborhood['groundDetailRemovedPlacementIndices'].values()) == preservation['originalRemovedPlacements'] == 47203,
        'Meadow original7000 rows/groups or47203 removal indices changed')
    original_recipe = read_pin(fixed(PHOTO, 'material-manifest.json', PHOTO_PINS))[MATERIAL]
    require(same(read_pin(plan['materialManifest']), {MATERIAL: original_recipe})
        and original_recipe['sourceUrl'] == 'https://polyhaven.com/a/grass_medium_02' and original_recipe['license'] == 'CC0-1.0',
        'Meadow original photographic PBR recipe/provenance differs')
    coverage = read_pin(fixed(STUDY, 'coverage-measurement.json', PINS))
    require(coverage['uniformFullGroundCoverClaim'] is False and coverage['nativeAppearanceAccepted'] is False
        and len(coverage['windows']) == 4 and all(len(w['lods']) == 3 for w in coverage['windows']),
        'Meadow partial measured coverage must not claim full lawn acceptance')
    prototypes = read_pin(fixed(STUDY, 'meadow-prototypes.json', PINS))
    measurement = read_pin(fixed(STUDY, 'study-measurement.json', PINS))
    require(measurement['nativeJobsRun'] == 0 and measurement['nativeAccepted'] is False
        and measurement['performanceAccepted'] is False and same(measurement['measurement'], plan['audit']),
            'Meadow original source-only measured proof differs')
    for name in ('low-meadow.glb', 'meadow-prototypes.json'):
        pinned(fixed(STUDY, name, PINS))
    cache_key = (scene_sha, obj_sha)
    if cache_key in _INSPECTION_CACHE:
        return deepcopy(_INSPECTION_CACHE[cache_key])
    decoded = _glb(pinned(fixed(STUDY, 'low-meadow.glb', PINS)))
    measured = _geometry(manifest, prototypes, decoded)
    domains, soil, blocked, ground = _spatial(plan, context, neighborhood, buildings)
    audit = _placements(plan['infillPlacements'], measured, domains, soil, blocked, ground)
    groups = _groups(plan['groups'], plan['infillPlacements'])
    audit.update(status='verified-source-additive-partial-meadow-pilot', coverageMeasurement=plan['coverageMeasurement'],
        projectedOpaqueCoverFractionByWindowAndLod={w['id']: [v['projectedOpaqueCoverFraction'] for v in w['lods']] for w in coverage['windows']},
        uniformFullGroundCoverClaim=False, original120MastersPreserved=True, original7000TransitionPlacementsPreserved=True,
        original47203RemovalIndicesPreserved=True, nativeVerified=False, nativeAppearanceAccepted=False,
        fullPhotorealismAccepted=False, performanceAccepted=False)
    result = {'groups': groups, 'audit': audit, 'measured': measured, 'recipe': original_recipe}
    _INSPECTION_CACHE[cache_key] = deepcopy(result)
    return result


def integration_inputs():
    plan = read_pin(fixed(STUDY, 'meadow-infill-plan.json', PINS))
    original = read_pin(fixed(PHOTO, 'geometry-manifest.json', PHOTO_PINS))
    result = {}
    def add(path, expected):
        require(path not in result or result[path] == expected, 'Meadow input pin conflict')
        pinned({'path': path, 'sha256': expected}); result[path] = expected
    for inputs in (plan['inputFiles'], original['inputFiles']):
        for path, expected in inputs.items(): add(path, expected)
    for directory, values in ((STUDY, PINS), (PHOTO, PHOTO_PINS)):
        for name, expected in values.items(): add(str(directory/name), expected)
    for name, expected in DELEGATES.items(): add(str(ROOT/'scripts/unreal'/name), expected)
    for path in (ROOT/ADAPTER, ROOT/OWNER):
        add(str(path), sha(path))
    return result


def validated_libraries(full_manifest):
    """Actual original120 and100 records, with their unmodified old owners."""
    original = read_pin(fixed(PHOTO, 'geometry-manifest.json', PHOTO_PINS))
    extension = read_pin(fixed(STUDY, 'geometry-manifest.json', PINS))
    require(full_manifest.get('owner') == ADAPTER and full_manifest.get('generatorSha256') == sha(ROOT/ADAPTER)
        and full_manifest.get('status') == STATUS and same(full_manifest['sourceOriginal120Library'], fixed(PHOTO, 'geometry-manifest.json', PHOTO_PINS))
        and same(full_manifest['sourceInfillGeometry'], fixed(STUDY, 'geometry-manifest.json', PINS))
        and same(full_manifest['inputFiles'], integration_inputs())
        and same(full_manifest['meshes'], original['meshes']+extension['meshes'])
        and len(full_manifest['meshes']) == 126 and sum(len(m['lods']) for m in full_manifest['meshes']) == 378,
        'Meadow full126 library must preserve ordered original120 plus exact6')
    require(set(full_manifest) == set(original) | COMMON_EXTRA | {'infillGeometryManifest', 'validatedOriginal120Subset', 'validatedOriginal100Subset'}
        and same(full_manifest['sourceInfillPlan'], fixed(STUDY, 'meadow-infill-plan.json', PINS)),
        'Meadow full library unreviewed metadata/claims differ')
    changed = {'owner', 'generatorSha256', 'inputFiles', 'status', 'meshes', 'revision'}
    for key, value in original.items():
        if key not in changed: require(same(full_manifest.get(key), value), 'Meadow original120 metadata differs: '+key)
    base = module('exterior-lawn-photo-native.py').validated_base_library(original)
    require(full_manifest['validatedOriginal120Subset']['sha256'] == PHOTO_PINS['geometry-manifest.json']
        and same(read_pin(full_manifest['validatedOriginal120Subset']), original)
        and full_manifest['validatedOriginal100Subset']['sha256'] == original['sourceOriginal100Library']['sha256']
        and same(read_pin(full_manifest['validatedOriginal100Subset']), base), 'Meadow exact old-owner subset copies differ')
    return {'original120': original, 'original100': base}


def validated_infill(plan, manifest, full_manifest, scene_sha, obj_sha, source_context=None):
    approved = read_pin(fixed(STUDY, 'meadow-infill-plan.json', PINS))
    extension = read_pin(fixed(STUDY, 'geometry-manifest.json', PINS))
    inputs = integration_inputs()
    for record, old in ((plan, approved), (manifest, extension)):
        require(record.get('owner') == ADAPTER and record.get('generatorSha256') == sha(ROOT/ADAPTER)
            and record.get('status') == STATUS and same(record['inputFiles'], inputs), 'Meadow adapter owner/closure differs')
        extra = {'status'} | COMMON_EXTRA | ({'infillGeometryManifest'} if record is plan else set())
        require(set(record) == set(old) | extra
            and same(record['sourceInfillPlan'], fixed(STUDY, 'meadow-infill-plan.json', PINS))
            and same(record['sourceInfillGeometry'], fixed(STUDY, 'geometry-manifest.json', PINS))
            and same(record['sourceOriginal120Library'], fixed(PHOTO, 'geometry-manifest.json', PHOTO_PINS)),
            'Meadow adapter unreviewed metadata/claims differ')
        changed = {'owner', 'generatorSha256', 'inputFiles', 'status', 'groups'}
        for key, value in old.items():
            if key not in changed: require(same(record.get(key), value), 'Meadow selected source/policy/domain differs: '+key)
    require(same(plan['sourceInfillPlan'], fixed(STUDY, 'meadow-infill-plan.json', PINS))
        and same(plan['groups'], native_groups(approved['groups']))
        and same(read_pin(plan['infillGeometryManifest']), manifest), 'Meadow native canonical group/extension differs')
    if full_manifest is not None:
        validated_libraries(full_manifest)
        require(same(full_manifest['infillGeometryManifest'], plan['infillGeometryManifest']), 'Meadow imported extension pin differs')
    if source_context is not None:
        require(same(source_context, read_pin(approved['sourceContext'])), 'Meadow caller original context differs')
    result = inspect_study(approved, extension, scene_sha, obj_sha)
    result['inputPins'] = inputs
    return {k: result[k] for k in ('groups', 'audit', 'inputPins')}


def validated_groups(plan, manifest, scene_sha, obj_sha):
    return validated_infill(plan, manifest, None, scene_sha, obj_sha)['groups']
