"""Strict stdlib guard for additive photographic lawn masters.

The old tapered validator owns every original crown, source-domain and legacy
identity check. This module does not weaken it: it validates the pinned original
plan first, then permits only UV0/tangent bytes and explicit new identities.
Source alpha coverage is an independently pinned mip0 raster, not native proof.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-lawn-photo-native.py'
ADAPTER = 'scripts/unreal/exterior-lawn-photo-integration.py'
PHOTO_GENERATOR = 'scripts/unreal/exterior-lawn-photo-variants.py'
PHOTO_SOURCE_SHA = '7d57758086df5a4305282cbe18e913364566c7b7c4ebc5242146418cb78b9a85'
SELECTED = ROOT/'output/unreal/exterior-lawn-photo-variants-20261001-r3-study'
SELECTED_PINS = {
    'lawn-photographic-proposal.json': '6ba9d124cb425b70c8e1a6454c2386fcfdc6d070b09b7c6c650e15ed730c7e70',
    'geometry-manifest.json': '4f671b902732999f542e301ab11cab3ca29e6718cdad1d5d8bd0da6b81781730',
    'geometry-uv-tangent-proof.json': '49f45c2d1e4a585c6ae993e3264f8fc83e1c37904caa3676f48057bbc83a25aa',
    'photographic-alpha-coverage-receipt.json': '0b6e9e163fb48182e2669c1111a851d5b8cff7fa5f48ff3a5ebb2b8637a16118',
    'lawn-photographic-variants.glb': 'ddb4402577e844ec5e70ca4417c0c686778cca4f35f6c766155313a6aae9aebd',
    'material-manifest.json': '9a0275363882594afb4b656ffbd7528866ad63366d03cf938bf562ac6ec5c88e',
}
OLD_HELPER = 'scripts/unreal/exterior-lawn-tapered-native.py'
OLD_HELPER_SHA = '957aec64d6d705cec3a8dc9ead0f64f94be26099bf839c2f63d344e9adba9dc6'
DONOR = ROOT/'output/unreal/exterior-lawn-tapered-integration-20261001-r1c'
BASE = ROOT/'output/unreal/exterior-assets-shape-20261001-r1'
DONOR_PINS = {
    'lawn-natural-plan.json': '0c13741cf2344ef809ac4427b4102a4917eefd508bc0b3c3746312029800c319',
    'geometry-manifest.json': 'a86d0832d5ce554bcb2ccebcb0a3cc066e5937912183db513c0ffccba893f455',
    'lawn-natural.glb': '4f99b430de0c7437dec8a30f4024eb419af8838ea25b8822bd7244c4ae30b2af',
    'lawn-coverage-receipt.json': 'a58daf34108c3af5dc3d955f90739c93b552629c6bcfd28de60630cc2653269b',
    'lawn-boundary-coverage-receipt.json': '8030643bed70088bbbddba344f534a3825d170e2759540d24f107a2d4237bac0',
}
BASE_PINS = {
    'geometry-manifest.json': '23c9df25473bb966ec96a8c2170f8abb6a1d6ad1172e1a0552a5e472d8e104a9',
    'material-manifest.json': '42dbaddc637c479d30482b1524217d8e9c288ff89de8f64d9f38396a1e63fbbb',
    'asset-manifest.json': '695068542a1785d0fef991de6cf671f0a14b32095e50cda005cf0bc80c530927',
}
MATERIAL = 'lawn_photographic_blade'
STATUS = 'MEASURED_PHOTOGRAPHIC_MANAGED_LAWN_NOT_NATIVE_ACCEPTED'
STUDY_STATUS = 'SOURCE_ONLY_PHOTOGRAPHIC_UV_VARIANTS_NATIVE_PENDING'
COVER_STATUS = 'PASS_SOURCE_PHOTOGRAPHIC_ALPHA_COVERAGE_NATIVE_PENDING'
VALIDATION_STATUS = 'verified-source-photographic-managed-lawn'
UV_SOURCE = ROOT/'output/unreal/exterior-lawn-photo-uv-20261001-r2-study/closure.json'
UV_SOURCE_SHA = '0f8d979480f24bbbe6524a88a27faa83f5d454b65da3b9effc13b5bb9b4343d3'
SCREENS = [1., .025, .007]
FAMILY = {f'lawn_natural_{g}_{i}' for g in range(2) for i in range(8)} | {
    f'lawn_natural_edge_{g}_{i}' for g in range(2) for i in range(2)}
MAPPING = {key: key.replace('lawn_natural_', 'lawn_photo_', 1) for key in FAMILY}
PHOTO_FAMILY = set(MAPPING.values())
PRESERVED = ('POSITION', 'NORMAL', 'COLOR_0', 'TEXCOORD_1', 'indices')
ATTRIBUTES = {'POSITION': 3, 'NORMAL': 3, 'TANGENT': 4,
              'TEXCOORD_0': 2, 'TEXCOORD_1': 2, 'COLOR_0': 4}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def same(a, b):
    return digest(a) == digest(b)


def pin(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), 'Photo source path escaped or is missing')
    return {'path': str(path), 'sha256': sha(path)}


def pinned(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}, 'Photo source pin shape differs')
    path = (ROOT/value['path']).resolve()
    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == value['sha256'],
            'Photo source path/hash drift: '+str(path))
    return path


def read_pin(value):
    return json.loads(pinned(value).read_text())


def fixed(directory, name, values):
    return {'path': str(directory/name), 'sha256': values[name]}


def old_module():
    path = pinned({'path': str(ROOT/OLD_HELPER), 'sha256': OLD_HELPER_SHA})
    spec = importlib.util.spec_from_file_location('immutable_photo_taper_delegate', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hide_original_lawn(*args, **kwargs):
    return old_module().hide_original_lawn(*args, **kwargs)


def verify_hidden_lawn(*args, **kwargs):
    return old_module().verify_hidden_lawn(*args, **kwargs)


def _number(value, lower=None, upper=None):
    return (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
            and (lower is None or value >= lower) and (upper is None or value <= upper))


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _sub(a, b):
    return [x-y for x, y in zip(a, b)]


def _cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def _unit(a):
    length = math.sqrt(_dot(a, a))
    require(length > 1e-10, 'Photo tangent frame is undefined')
    return [v/length for v in a]


def _glb(path):
    raw = Path(path).read_bytes()
    require(len(raw) >= 28 and struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)),
            'Photo GLB header differs')
    length, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a and length % 4 == 0, 'Photo GLB JSON chunk differs')
    document = json.loads(raw[20:20+length])
    offset = 20+length
    require(offset+8 <= len(raw), 'Photo GLB binary is missing')
    size, kind = struct.unpack_from('<II', raw, offset)
    require(kind == 0x004e4942 and offset+8+size == len(raw), 'Photo GLB binary chunk differs')
    binary = raw[offset+8:]
    require(document.get('scene') == 0 and len(document.get('scenes', [])) == 1
            and document['scenes'][0].get('nodes') == list(range(60))
            and len(document.get('nodes', [])) == len(document.get('meshes', [])) == 60
            and len(document.get('buffers', [])) == len(document.get('materials', [])) == 1
            and not document['buffers'][0].get('uri')
            and document['buffers'][0]['byteLength'] == len(binary)
            and not any(k in document for k in ('skins', 'animations', 'extensionsUsed', 'extensionsRequired')),
            'Photo GLB scene/buffer inventory differs')
    nodes = {}
    for node in document['nodes']:
        require(set(node) == {'name', 'mesh'} and node['name'] not in nodes,
                'Photo GLB node transform or identity differs')
        mesh = document['meshes'][node['mesh']]
        require(len(mesh['primitives']) == 1, 'Photo GLB extra primitive refused')
        primitive = mesh['primitives'][0]
        require(set(primitive) <= {'attributes', 'indices', 'material', 'mode'}
                and primitive.get('mode', 4) == 4 and primitive.get('material') == 0
                and set(primitive['attributes']) == set(ATTRIBUTES), 'Photo GLB primitive attributes differ')
        values = {}; encoded = {}; ranges = {}
        for name, width in {**ATTRIBUTES, 'indices': 1}.items():
            index = primitive['indices'] if name == 'indices' else primitive['attributes'][name]
            accessor = document['accessors'][index]
            kind = 'SCALAR' if width == 1 else 'VEC'+str(width)
            component = 5125 if name == 'indices' else 5126
            require(accessor['type'] == kind and accessor['componentType'] == component
                    and _number(accessor['count'], 1) and isinstance(accessor['count'], int)
                    and not accessor.get('sparse') and not accessor.get('normalized'),
                    'Photo GLB accessor type/count differs: '+name)
            view = document['bufferViews'][accessor['bufferView']]
            require(view.get('buffer', 0) == 0 and view.get('byteStride', width*4) == width*4,
                    'Photo GLB accessor stride/buffer differs')
            start = view.get('byteOffset', 0)+accessor.get('byteOffset', 0)
            stop = start+accessor['count']*width*4
            require(0 <= start < stop <= len(binary)
                    and stop <= view.get('byteOffset', 0)+view['byteLength'], 'Photo GLB accessor bounds differ')
            blob = binary[start:stop]
            fmt = '<'+('I' if name == 'indices' else 'f')*width
            rows = list(struct.iter_unpack(fmt, blob))
            require(name == 'indices' or all(all(_number(v) for v in row) for row in rows),
                    'Photo GLB frame is non-finite')
            values[name] = rows; encoded[name] = blob; ranges[name] = (start, stop)
        count = len(values['POSITION'])
        require(all(len(values[name]) == count for name in ATTRIBUTES)
                and len(values['indices']) % 3 == 0
                and all(0 <= row[0] < count for row in values['indices']), 'Photo GLB index/frame inventory differs')
        nodes[node['name']] = {'values': values, 'encoded': encoded, 'ranges': ranges}
    return document, binary, nodes


def _uv_expected(old_uv, stations, inset_pixels):
    u, t = old_uv
    require(0 <= u <= 1 and 0 <= t <= 1, 'Photo original UV outside normalized leaf')
    position = t*256
    lower = min(255, int(math.floor(position))); blend = position-lower
    low = stations[lower][1]+(stations[lower+1][1]-stations[lower][1])*blend
    high = stations[lower][2]+(stations[lower+1][2]-stations[lower][2])*blend
    low += inset_pixels/2048.; high -= inset_pixels/2048.
    require(low < high, 'Photo provider body inset collapses')
    return (_f32(.768+(.352-.768)*t), _f32(low+(high-low)*u))


def _tangents(values):
    points = [(100*p[0], 100*p[2], 100*p[1]) for p in values['POSITION']]
    normals = [_unit((n[0], n[2], n[1])) for n in values['NORMAL']]
    uv = values['TEXCOORD_0']; indices = [row[0] for row in values['indices']]
    tangents = [[0., 0., 0.] for _ in points]; bitangents = deepcopy(tangents)
    minimum = float('inf')
    for start in range(0, len(indices), 3):
        a, c, b = indices[start:start+3]
        e1, e2 = _sub(points[b], points[a]), _sub(points[c], points[a])
        d1, d2 = _sub(uv[b], uv[a]), _sub(uv[c], uv[a])
        determinant = d1[0]*d2[1]-d1[1]*d2[0]
        area = math.sqrt(_dot(_cross(e1, e2), _cross(e1, e2)))*.5
        require(abs(determinant) > 1e-12 and area > 1e-8, 'Photo geometry/UV triangle is degenerate')
        minimum = min(minimum, abs(determinant)*.5)
        tangent = [(e1[i]*d2[1]-e2[i]*d1[1])/determinant for i in range(3)]
        bitangent = [(-e1[i]*d2[0]+e2[i]*d1[0])/determinant for i in range(3)]
        for index in (a, b, c):
            for axis in range(3):
                tangents[index][axis] += tangent[axis]*area
                bitangents[index][axis] += bitangent[axis]*area
    for i, actual in enumerate(values['TANGENT']):
        normal = normals[i]; tangent = tangents[i]
        projected = _unit([tangent[j]-normal[j]*_dot(normal, tangent) for j in range(3)])
        handedness = 1. if _dot(_cross(normal, projected), bitangents[i]) > 0 else -1.
        expected = (projected[0], projected[2], projected[1], -handedness)
        require(actual[3] in (-1., 1.) and max(abs(a-b) for a, b in zip(actual, expected)) < 2e-6,
                'Photo actual regenerated tangent/handedness differs from UV')
    return minimum


def geometry_delta(original_path, photo_path, original_manifest, photo_manifest, inset_pixels=1.5):
    """Decode all primitives/accessors; compare raw bytes outside UV0/tangents."""
    require(inset_pixels == 1.5 and not isinstance(inset_pixels, bool), 'Photo body inset must match the measured original provider strip')
    before, original_binary, originals = _glb(original_path)
    after, photo_binary, photos = _glb(photo_path)
    expected = deepcopy(before)
    expected['asset']['generator'] = PHOTO_GENERATOR+'; original source: '+before['asset'].get('generator', '')
    for node in expected['nodes']:
        node['name'] = node['name'].replace('lawn_natural_', 'lawn_photo_', 1)
        expected['meshes'][node['mesh']]['name'] = node['name']
    require(same(after, expected), 'Photo GLB metadata/material/accessor delta exceeds permitted node names')
    source_rows = {row['id']: row for row in original_manifest['meshes']}
    require(len(source_rows) == len(original_manifest['meshes']) == 20 and set(source_rows) == FAMILY,
            'Photo original twenty-master family differs')
    _manifest_delta(original_manifest, photo_manifest)
    stations = read_pin({'path': str(UV_SOURCE), 'sha256': UV_SOURCE_SHA})['leafUvMapping']['stripStations']
    require(len(stations) == 257 and all(len(row) == 3 and all(_number(v, 0, 1) for v in row) for row in stations),
            'Photo original provider body stations differ')
    allowed = []; witnesses = []; vertex_count = triangle_count = 0
    for row in original_manifest['meshes']:
        for lod in row['lods']:
            name = lod['nodeName']; photo_name = name.replace('lawn_natural_', 'lawn_photo_', 1)
            require(name in originals and photo_name in photos, 'Photo mapped LOD is missing')
            old, new = originals[name], photos[photo_name]
            require(all(old['encoded'][key] == new['encoded'][key] for key in PRESERVED),
                    'Photo original POSITION/NORMAL/COLOR0/UV1/index bytes changed: '+name)
            require(len(new['values']['POSITION']) == lod['vertices']
                    and len(new['values']['indices'])//3 == lod['triangles'], 'Photo actual LOD counts differ')
            require(all(new['values']['TEXCOORD_0'][i] == _uv_expected(old_uv, stations, inset_pixels)
                        for i, old_uv in enumerate(old['values']['TEXCOORD_0'])), 'Photo body UV mapping differs')
            minimum = _tangents(new['values'])
            vertex_count += lod['vertices']; triangle_count += lod['triangles']
            for key in ('TEXCOORD_0', 'TANGENT'):
                require(old['ranges'][key] == new['ranges'][key], 'Photo UV/tangent accessor range changed')
                allowed.append((*new['ranges'][key], key, name))
            witnesses.append({'sourceNode': name, 'photoNode': photo_name, 'vertices': lod['vertices'],
                'triangles': lod['triangles'], 'blades': lod['blades'],
                'unchangedAttributeEncodedHashes': {key: hashlib.sha256(new['encoded'][key]).hexdigest() for key in PRESERVED},
                'minimumUvTriangleArea': minimum})
        first = photos[MAPPING[row['id']]+'_LOD0']['encoded']
        require(all(photos[MAPPING[row['id']]+'_LOD'+str(l)]['encoded'] == first for l in (1, 2)),
                'Photo actual all-LOD attribute byte identity differs')
    require(len(original_binary) == len(photo_binary) and len(allowed) == 120
            and set(photos) == {photo+'_LOD'+str(l) for photo in PHOTO_FAMILY for l in range(3)},
            'Photo sixty-LOD inventory differs')
    offset = 0
    for start, stop, _, _ in sorted(allowed):
        require(start >= offset and original_binary[offset:start] == photo_binary[offset:start],
                'Photo binary changed outside independent UV/tangent ranges')
        offset = stop
    require(original_binary[offset:] == photo_binary[offset:], 'Photo binary tail changed')
    return {'nodes': witnesses, 'changedBufferRanges': [list(row) for row in allowed],
            'allLodGeometryVertices': vertex_count, 'allLodGeometryTriangles': triangle_count,
            'meshes': 20, 'lods': 60, 'decodedAllPrimitivesAndAccessors': True,
            'rawPositionNormalColorUv1IndexBytesPreserved': True,
            'allOriginalBoundsAndRootLayoutPreserved': True, 'onlyUv0AndTangentBufferRangesModified': True,
            'nativeTangentsStillRecomputedByImporter': True}


def _manifest_delta(original, photo):
    require(isinstance(photo.get('meshes'), list) and len(photo['meshes']) == 20,
            'Photo extension must have exactly twenty masters')
    paths = set()
    for source, actual in zip(original['meshes'], photo['meshes']):
        expected = deepcopy(source)
        expected.update(id=MAPPING[source['id']], sourceMeshId=source['id'], materialKeys=[MATERIAL],
                        glbPath=actual.get('glbPath'), glbSha256=actual.get('glbSha256'))
        for lod in expected['lods']:
            lod['nodeName'] = lod['nodeName'].replace('lawn_natural_', 'lawn_photo_', 1)
        require(same(actual, expected) and actual['role'] == 'grass'
                and actual['placementPolicy'] == 'explicit-only' and actual['lodScreenSizes'] == SCREENS,
                'Photo source master mapping/bounds/policy differs')
        paths.add((actual['glbPath'], actual['glbSha256']))
    require(len(paths) == 1, 'Photo extension GLB identity is ambiguous')


def _coverage(value, source_coverage, source_boundary, recipe):
    require(value.get('schemaVersion') == 1 and value.get('status') == COVER_STATUS
            and value.get('allTargetsMet') is True and value.get('opaqueBaselineReproducedExactly') is True
            and value.get('sourceAlphaPixelsUnmodified') is True
            and value.get('noDensityRootsGeometryOrSourceDomainChanges') is True
            and value.get('all3LodGeometryUvAndTangentByteEqualityVerified') is True
            and value.get('sameRasterCopiedToOtherLodsOnlyAfterExactByteEquality') is True
            and value.get('uniqueGeometryRasterRuns') == 6 and value.get('nativeJobsRun') == 0
            and all(value.get(k) is False for k in ('nativeVisualAccepted', 'fullPhotorealismAccepted', 'performanceAccepted')),
            'Photo coverage source status/policy failed')
    require(same(value['sourceCoverage'], fixed(DONOR, 'lawn-coverage-receipt.json', DONOR_PINS))
            and same(value['sourceBoundaryCoverage'], fixed(DONOR, 'lawn-boundary-coverage-receipt.json', DONOR_PINS))
            and same(value['sourceAlpha'], recipe['maps']['alpha'])
            and value['pixelSizeMm'] == .25 and value['alphaClipValue'] == .333,
            'Photo alpha/source raster pins or cutoff changed')
    physical, boundary = value['physicalCoverage'], value['boundaryCoverage']
    require(same(physical['criteria'], source_coverage['criteria'])
            and same(boundary['criteria'], source_boundary['criteria'])
            and len(physical['windows']) == 4 and len(boundary['windows']) == 2, 'Photo coverage criteria/windows differ')
    minimum = 1.; minimum_p10 = 1.; boundary_minima = [1., 1., 1.]
    for window, old in zip(physical['windows'], source_coverage['windows']):
        for field in ('centerCm', 'sizeCm', 'resolution', 'method', 'instancesIntersectingWindow'):
            require(same(window[field], old[field]), 'Photo coverage window frame/population differs')
        expected = {k: old['lods'][0][k] for k in ('projectedCoverage', 'tenCmBinCoverageMinimum', 'tenCmBinCoverageP10', 'bareTenCmBins')}
        require(same(window['opaqueSourceMetrics'], expected), 'Photo opaque source baseline not reproduced')
        require([row['lod'] for row in window['lods']] == [0, 1, 2]
                and all(same(row, window['lods'][0] | {'lod': i}) for i, row in enumerate(window['lods'])),
                'Photo all-LOD raster identity differs')
        for row in window['lods']:
            coverage, p10 = row['projectedCoverage'], row['tenCmBinCoverageP10']
            require(_number(coverage, .75, expected['projectedCoverage']) and _number(p10, .55, 1)
                    and _number(row['tenCmBinCoverageMinimum'], 0, p10)
                    and row['bareTenCmBins'] == 0 and not isinstance(row['bareTenCmBins'], bool)
                    and row['studyTargetsMet'] is True, 'Photo alpha physical coverage gate failed')
            minimum = min(minimum, coverage); minimum_p10 = min(minimum_p10, p10)
        require(abs(window['alphaLostCoverageAbsolute']-(expected['projectedCoverage']-window['lods'][0]['projectedCoverage'])) < 1e-12,
                'Photo alpha loss claim differs')
    for window, old in zip(boundary['windows'], source_boundary['windows']):
        for field in ('boundaryId', 'originCm', 'axisUnitXY', 'inwardUnitXY', 'widthCm', 'lengthCm',
                      'pixelSizeMm', 'resolutionXY', 'intersectingInstances'):
            require(same(window[field], old[field]), 'Photo boundary raster frame/population differs')
        require([row['lod'] for row in window['lods']] == [0, 1, 2]
                and all(same(row, window['lods'][0] | {'lod': i}) for i, row in enumerate(window['lods'])),
                'Photo boundary all-LOD identity differs')
        require(same(window['opaqueSourceMetrics'], {k: old['lods'][0][k] for k in ('projectedCoverage', 'boundaryBands')}),
                'Photo boundary opaque source baseline not reproduced')
        for row in window['lods']:
            require(row['studyTargetsMet'] is True and _number(row['projectedCoverage'], 0, 1)
                    and len(row['boundaryBands']) == 3, 'Photo boundary coverage policy differs')
            for i, (band, interval, threshold) in enumerate(zip(row['boundaryBands'], ([1, 10], [10, 30], [30, 100]), (.12, .40, .50))):
                require(same(band['distanceFromBoundaryMm'], [float(v) for v in interval])
                        and _number(band['physicalCoverFraction'], threshold, 1),
                        'Photo actual boundary alpha coverage gate failed')
                boundary_minima[i] = min(boundary_minima[i], band['physicalCoverFraction'])
    return {'minimumProjectedAlphaCoverage': minimum, 'minimumTenCmBinP10': minimum_p10,
            'minimumBoundaryCoverFractions': boundary_minima, 'fourPhysicalAndTwoBoundaryWindowsVerified': True,
            'alphaRasterIsMip0SourceEvidenceOnly': True}


def inspect_study(proposal, photo_manifest, scene_sha, obj_sha):
    """Validate source study independently before composing any new file."""
    original_plan = read_pin(fixed(DONOR, 'lawn-natural-plan.json', DONOR_PINS))
    original_manifest = read_pin(fixed(DONOR, 'geometry-manifest.json', DONOR_PINS))
    original_library = read_pin(fixed(BASE, 'geometry-manifest.json', BASE_PINS))
    recipes = read_pin(fixed(BASE, 'material-manifest.json', BASE_PINS))
    recipe = recipes['ph_grass_medium_02']
    require(same(proposal, read_pin(fixed(SELECTED, 'lawn-photographic-proposal.json', SELECTED_PINS)))
            and same(photo_manifest, read_pin(fixed(SELECTED, 'geometry-manifest.json', SELECTED_PINS)))
            and sha(ROOT/PHOTO_GENERATOR) == PHOTO_SOURCE_SHA,
            'Photo selected measured R3 study/source differs')
    for name in SELECTED_PINS:
        pinned(fixed(SELECTED, name, SELECTED_PINS))
    for record in (proposal, photo_manifest):
        require(record.get('schemaVersion') == 1 and record.get('owner') == PHOTO_GENERATOR
                and record.get('generatorSha256') == sha(ROOT/PHOTO_GENERATOR), 'Photo study owner/source differs')
        require(record['activeDesign'] == original_plan['activeDesign']
                and same(record['housePlacement'], original_plan['housePlacement'])
                and record['sourceSceneSha256'] == scene_sha == original_plan['sourceSceneSha256']
                and record['sourceObjSha256'] == obj_sha == original_plan['sourceObjSha256'], 'Photo study source frame differs')
        for path, expected in record['inputFiles'].items():
            pinned({'path': path, 'sha256': expected})
    require(same(proposal['inputFiles'], photo_manifest['inputFiles'])
            and proposal['kind'] == 'source-only-photographic-tapered-lawn-variants'
            and photo_manifest['status'] == STUDY_STATUS and proposal['sourceOnlyCoverageReady'] is True
            and proposal['placements'] == 102011 and proposal['groups'] == 40
            and proposal['allPopulationTriangleBudgets'] == [18571200]*3
            and proposal['noNativeIntegrationPerformed'] is True
            and all(proposal[k] is False for k in ('nativeVisualAccepted', 'fullPhotorealismAccepted', 'performanceAccepted')),
            'Photo study population/readiness/acceptance differs')
    require(same(proposal['sourcePlacementPlan'], fixed(DONOR, 'lawn-natural-plan.json', DONOR_PINS))
            and same(proposal['sourceOriginal100Library'], fixed(BASE, 'geometry-manifest.json', BASE_PINS))
            and same(read_pin(proposal['geometryManifest']), photo_manifest), 'Photo study original source/extension pin differs')
    require(same(read_pin(proposal['materialManifest']), {MATERIAL: recipe}), 'Photo material must copy exact original provider recipe')
    _manifest_delta(original_manifest, photo_manifest)
    expected_bindings = [{'sourceMeshId': m['id'], 'meshId': MAPPING[m['id']], 'materialKey': MATERIAL}
                         for m in original_manifest['meshes']]
    require(same(proposal['prototypeBindings'], expected_bindings), 'Photo source-to-master bindings differ')
    coverage_pin = proposal['photographicAlphaCoverage']
    require(same(coverage_pin, photo_manifest['photographicAlphaCoverage']), 'Photo alpha receipt pin differs')
    coverage = read_pin(coverage_pin)
    coverage_result = _coverage(coverage, read_pin(fixed(DONOR, 'lawn-coverage-receipt.json', DONOR_PINS)),
        read_pin(fixed(DONOR, 'lawn-boundary-coverage-receipt.json', DONOR_PINS)), recipe)
    path, value = photo_manifest['meshes'][0]['glbPath'], photo_manifest['meshes'][0]['glbSha256']
    delta = geometry_delta(pinned(fixed(DONOR, 'lawn-natural.glb', DONOR_PINS)),
        pinned({'path': path, 'sha256': value}), original_manifest, photo_manifest)
    proof = read_pin(photo_manifest['geometryProof'])
    require(proof['status'] == 'VERIFIED_ORIGINAL_TAPERED_GEOMETRY_BYTES_ONLY_UV0_TANGENT_CHANGED'
            and proof['meshes'] == 20 and proof['lods'] == 60 and proof['nativeJobsRun'] == 0
            and proof['nativeShaderAccepted'] is False and proof['fullPhotorealismAccepted'] is False
            and proof['allPositionNormalColorUv1IndicesAndBoundsExact'] is True
            and proof['allSourceLeafRootLayoutPreserved'] is True
            and proof['embeddedOriginalMaterialDefinitionsUnchanged'] is True
            and proof['only120Uv0AndTangentAccessorRangesModified'] is True
            and same(proof['changedBufferRanges'], delta['changedBufferRanges'])
            and len(proof['nodes']) == 60, 'Photo independent raw geometry proof differs')
    for actual, measured in zip(proof['nodes'], delta['nodes']):
        require(all(same(actual[key], measured[key]) for key in ('sourceNode', 'photoNode', 'vertices', 'triangles',
                    'blades', 'unchangedAttributeEncodedHashes'))
                and abs(actual['minimumUvTriangleArea']-measured['minimumUvTriangleArea']) < 1e-12,
                'Photo declared node proof differs from decoded GLB')
    original_groups = old_module().validated_groups(original_plan, original_manifest, scene_sha, obj_sha)
    return {'originalPlan': original_plan, 'originalManifest': original_manifest, 'originalLibrary': original_library,
            'recipe': recipe, 'originalGroups': original_groups, 'coverage': coverage,
            'coverageValidation': coverage_result, 'geometryValidation': delta}


def transformed_groups(groups):
    result = deepcopy(groups)
    for group in result:
        require(group['meshId'] in MAPPING and group['id'].startswith('EX_lawn_natural_'), 'Photo original active group identity differs')
        group['meshId'] = MAPPING[group['meshId']]
        group['id'] = group['id'].replace('EX_lawn_natural_', 'EX_lawn_photo_', 1)
    return result


def integration_inputs(proposal, proposal_pin):
    """Only directly consumed source/geometry/coverage and original proof inputs."""
    source = read_pin(fixed(DONOR, 'lawn-natural-plan.json', DONOR_PINS))
    base = read_pin(fixed(BASE, 'geometry-manifest.json', BASE_PINS))
    inputs = {}
    def add(path, value):
        require(path not in inputs or inputs[path] == value, 'Photo source input hash conflict')
        pinned({'path': path, 'sha256': value}); inputs[path] = value
    for mapping in (source['inputFiles'], base['inputFiles'], proposal['inputFiles']):
        for path, value in mapping.items(): add(path, value)
    for item in ([proposal_pin, proposal['geometryManifest'], proposal['materialManifest'],
                  proposal['photographicAlphaCoverage'], read_pin(proposal['geometryManifest'])['geometryProof']]
                 + [fixed(BASE, name, BASE_PINS) for name in BASE_PINS]
                 + [fixed(DONOR, name, DONOR_PINS) for name in DONOR_PINS]
                 + [pin(ROOT/OWNER), pin(ROOT/ADAPTER), {'path': str(ROOT/OLD_HELPER), 'sha256': OLD_HELPER_SHA}]):
        add(item['path'], item['sha256'])
    return inputs


def validated_base_library(photo_full_manifest):
    """Return the actual original100 only after validating exact additive120."""
    source = read_pin(fixed(BASE, 'geometry-manifest.json', BASE_PINS))
    require(photo_full_manifest.get('owner') == ADAPTER
            and photo_full_manifest.get('generatorSha256') == sha(ROOT/ADAPTER), 'Photo full library owner/source differs')
    extension = read_pin(photo_full_manifest['photoExtensionManifest'])
    proposal = read_pin(photo_full_manifest['sourcePhotographicStudy'])
    require(same(photo_full_manifest['sourcePhotographicStudy'],
                 fixed(SELECTED, 'lawn-photographic-proposal.json', SELECTED_PINS)),
            'Photo full library must use the measured selected R3 study')
    study_extension = read_pin(proposal['geometryManifest'])
    _manifest_delta(read_pin(fixed(DONOR, 'geometry-manifest.json', DONOR_PINS)), study_extension)
    require(same(extension['meshes'], study_extension['meshes']) and extension['owner'] == ADAPTER
            and extension['generatorSha256'] == sha(ROOT/ADAPTER), 'Photo full library extension drift')
    require(same(photo_full_manifest['meshes'], source['meshes']+extension['meshes'])
            and len(photo_full_manifest['meshes']) == 120
            and sum(len(m['lods']) for m in photo_full_manifest['meshes']) == 360
            and same(photo_full_manifest['sourceOriginal100Library'], fixed(BASE, 'geometry-manifest.json', BASE_PINS))
            and same(photo_full_manifest['sourceMaterialManifest'], fixed(BASE, 'material-manifest.json', BASE_PINS))
            and same(read_pin(photo_full_manifest['photoMaterialManifest']), {MATERIAL:
                read_pin(fixed(BASE, 'material-manifest.json', BASE_PINS))['ph_grass_medium_02']}),
            'Photo full library must preserve ordered original100 plus exact20; base recipes unchanged')
    for key, value in source.items():
        if key not in {'meshes', 'owner', 'generatorSha256', 'inputFiles', 'revision', 'status'}:
            require(same(photo_full_manifest.get(key), value), 'Photo full library original frame metadata differs: '+key)
    expected_inputs = integration_inputs(proposal, photo_full_manifest['sourcePhotographicStudy'])
    require(same(photo_full_manifest['inputFiles'], expected_inputs)
            and same(extension['inputFiles'], expected_inputs), 'Photo full library input ownership differs')
    for row in photo_full_manifest['meshes']:
        pinned({'path': row['glbPath'], 'sha256': row['glbSha256']})
    return source


def validate_photo(plan, manifest, imported_merged_manifest, scene_sha, obj_sha):
    """Validate an explicit adapter; return native groups and compact evidence."""
    for record in (plan, manifest):
        require(record.get('schemaVersion') == 1 and record.get('owner') == ADAPTER
                and record.get('generatorSha256') == sha(ROOT/ADAPTER)
                and record.get('status') == STATUS, 'Photo integration owner/status/source differs')
        for path, expected in record['inputFiles'].items():
            pinned({'path': path, 'sha256': expected})
    require(same(plan['inputFiles'], manifest['inputFiles'])
            and same(read_pin(plan['geometryManifest']), manifest), 'Photo integration manifest/closure differs')
    proposal = read_pin(plan['sourcePhotographicStudy'])
    require(same(plan['inputFiles'], integration_inputs(proposal, plan['sourcePhotographicStudy'])),
            'Photo integration selected input ownership differs')
    study_manifest = read_pin(proposal['geometryManifest'])
    validation = inspect_study(proposal, study_manifest, scene_sha, obj_sha)
    source = validation['originalPlan']
    require(same(manifest['meshes'], study_manifest['meshes'])
            and plan['kind'] == 'authored-photographic-lawn-replacement'
            and same(plan['sourcePlacementPlan'], fixed(DONOR, 'lawn-natural-plan.json', DONOR_PINS))
            and same(plan['sourceOriginal100Library'], fixed(BASE, 'geometry-manifest.json', BASE_PINS)),
            'Photo integration source/geometry delta differs')
    changed = {'kind', 'owner', 'generatorSha256', 'inputFiles', 'geometryManifest', 'audit', 'status',
               'groups', 'lawnPlacements', 'geometryProof'}
    for key, value in source.items():
        if key not in changed:
            require(same(plan.get(key), value), 'Photo original source/domain/policy field differs: '+key)
    expected_groups = transformed_groups(source['groups'])
    expected_rows = deepcopy(source['lawnPlacements'])
    for row in expected_rows:
        row['meshId'] = MAPPING[row['meshId']]
    require(same(plan['groups'], expected_groups) and same(plan['lawnPlacements'], expected_rows),
            'Photo active roots/yaws/scales/groups/policies changed')
    require(same(plan['photographicAlphaCoverage'], proposal['photographicAlphaCoverage'])
            and same(plan['geometryProof'], study_manifest['geometryProof']), 'Photo integration alpha/geometry proof drift')
    require(same(plan['audit'], photo_audit(validation, proposal)), 'Photo integration measured audit differs')
    if imported_merged_manifest is not None:
        validated_base_library(imported_merged_manifest)
        require(same(imported_merged_manifest['photoExtensionManifest'], plan['geometryManifest']),
                'Photo integration imported extension differs')
    groups = transformed_groups(validation['originalGroups'])
    audit = {'status': VALIDATION_STATUS, 'instances': 102011, 'groups': 40,
        'original100MasterRecordsPreserved': True, 'additionalPhotoMasters': 20, 'mergedMasters': 120, 'mergedLods': 360,
        'sourcePlacementPlan': fixed(DONOR, 'lawn-natural-plan.json', DONOR_PINS),
        'legacyValidator': {'path': str(ROOT/OLD_HELPER), 'sha256': OLD_HELPER_SHA},
        'allSourceGeometryExceptUv0TangentsPreserved': True, 'allOrderedPlacementsPoliciesPreserved': True,
        'legacy40437IdentityAndAllOriginalCrownChecksDelegatedUnchanged': True,
        'photographicAlphaCoverage': plan['photographicAlphaCoverage'], **validation['coverageValidation'],
        'allPopulationTriangleBudgets': [18571200]*3, 'sourceGroundCollisionArchitectureAndSetbacksPreserved': True,
        'nativeVerified': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
        'performanceAccepted': False}
    return {'groups': groups, 'audit': audit}


def photo_audit(validation, proposal):
    audit = deepcopy(validation['originalPlan']['audit'])
    audit.update(status=STATUS, instances=102011, groups=40,
        perMesh={MAPPING[k]: v for k, v in audit['perMesh'].items()}, originalMasters=100,
        additionalPhotoMasters=20, mergedMasters=120, mergedLods=360,
        allSourceGeometryExceptUv0TangentsPreserved=True, originalPlacementsPoliciesPreserved=True,
        original100MasterRecordsPreserved=True, sourceAuditSha256=digest(validation['originalPlan']['audit']),
        photographicAlphaCoverage=proposal['photographicAlphaCoverage'],
        physicalCoverage=deepcopy(validation['coverage']['physicalCoverage']),
        boundaryCoverage=deepcopy(validation['coverage']['boundaryCoverage']),
        oldBaseCoverageReceipt=fixed(DONOR, 'lawn-coverage-receipt.json', DONOR_PINS),
        oldBaseBoundaryCoverageReceipt=fixed(DONOR, 'lawn-boundary-coverage-receipt.json', DONOR_PINS),
        artistInterpretation=True, photographicMapsLicense='CC0-1.0', surveyedBotany=False,
        nativeVerified=False, nativeAppearanceAccepted=False, fullPhotorealismAccepted=False,
        performanceAccepted=False, integrationAuthorized=False)
    return audit


def validated_groups(plan, manifest, scene_sha, obj_sha):
    return validate_photo(plan, manifest, None, scene_sha, obj_sha)['groups']
