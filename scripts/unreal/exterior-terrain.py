"""Measured distant Czech relief, sampled from ČÚZK DMR 5G; no engine use.

Keeps near-house geometry untouched. XY is the existing active C3 frame; heights
are relative to a fresh 2m DMR sample, NOT the house finished-floor datum. A
300–900m authored join blends into the current flat context. Austrian/no-data
cells have a separately identified illustrative flat fallback. No guessed
mountains or vertical exaggeration are added.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import heapq
import io
import json
import math
from pathlib import Path
import struct
import urllib.parse
import urllib.request

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-terrain.py'
SERVICE = 'https://ags.cuzk.gov.cz/arcgis2/rest/services/dmr5g/ImageServer'
LICENSE_URL = 'https://cuzk.gov.cz/Predpisy/Podminky-poskytovani-prostor-dat-a-sitovych-sluzeb/Podminky-poskytovani-prostorovych-dat-CUZK.aspx'
GRID = 257
HALF_EXTENT_M = 8000
NEAR_RADIUS_CM = 30000
BLEND_END_CM = 90000
FLAT_BASE_CM = -25.0
COVERAGE_FADE_M = 600.0


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def write_once(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == payload, 'Refuse to overwrite evidence: ' + str(path))
    else:
        with path.open('xb') as stream:
            stream.write(payload)


def fetch(url):
    with urllib.request.urlopen(url, timeout=50) as response:
        return response.read()


def request_parameters(cx, cy, extent, size, format_, pixel_type):
    return {'bbox': ','.join(str(v) for v in [cx - extent, cy - extent, cx + extent, cy + extent]),
            'bboxSR': '5514', 'imageSR': '5514', 'size': str(size) + ',' + str(size),
            'format': format_, 'pixelType': pixel_type, 'renderingRule': '{"rasterFunction":"None"}',
            'interpolation': 'RSP_BilinearInterpolation', 'f': 'json'}


def pinned_export(directory, identity, parameters):
    receipt_path = directory / (identity + '-receipt.json')
    image_path = directory / (identity + ('.tif' if parameters['format'] == 'tiff' else '.png'))
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        require(receipt['parameters'] == parameters and sha(image_path) == receipt['sha256'], 'Pinned DEM input differs')
        return image_path, receipt
    require(not image_path.exists(), 'Unreceipted DEM input exists')
    url = SERVICE + '/exportImage?' + urllib.parse.urlencode(parameters)
    response = json.loads(fetch(url))
    require('href' in response and response['width'] > 0 and response['height'] > 0, 'DEM export failed')
    payload = fetch(response['href'])
    receipt = {'source': SERVICE, 'requestUrl': url, 'parameters': parameters, 'response': response,
               'retrievedAt': datetime.now(timezone.utc).isoformat(), 'bytes': len(payload),
               'sha256': hashlib.sha256(payload).hexdigest(), 'provider': 'ČÚZK',
               'license': 'CC BY 4.0', 'licenseUrl': LICENSE_URL,
               'attribution': '© ČÚZK, DMR 5G, CC BY 4.0; sampled and transformed for visualization'}
    write_once(image_path, payload)
    write_once(receipt_path, encode(receipt))
    return image_path, receipt


def decode_f32_tiff(payload):
    """Decode actual uncompressed float tiles, honoring offset=0 sparse tiles.

Pillow alone yielded uninitialized-looking values in sparse DMR TIFF tiles.
Use Pillow for GeoTIFF metadata only, then decode pinned offsets explicitly.
The separate same-extent PNG alpha is the authority for per-pixel validity.
"""
    image = Image.open(io.BytesIO(payload))
    tags = image.tag_v2
    require(image.mode == 'F' and tags[258] == (32,) and tags[339] == (3,), 'DEM must be a single-band Float32 TIFF')
    require(tags[259] == 1, 'Only explicitly decoded uncompressed TIFF is accepted')
    require(tags[277] == 1 and tags[284] == 1, 'Unexpected TIFF sample layout')
    require(322 in tags and 323 in tags and 324 in tags and 325 in tags, 'DEM must have tiled data')
    width, height = image.size
    tile_width, tile_height = tags[322], tags[323]
    offsets, counts = tags[324], tags[325]
    columns = math.ceil(width / tile_width)
    values = [None] * (width * height)
    endian = '<' if payload[:2] == b'II' else '>' if payload[:2] == b'MM' else None
    require(endian is not None, 'Unknown TIFF byte order')
    sparse = 0
    for tile, (offset, count) in enumerate(zip(offsets, counts)):
        if not offset or not count:
            sparse += 1
            continue
        require(count == tile_width * tile_height * 4 and offset + count <= len(payload), 'Invalid DEM tile bounds')
        floats = struct.unpack(endian + 'f' * (count // 4), payload[offset:offset + count])
        tx, ty = (tile % columns) * tile_width, (tile // columns) * tile_height
        for local, value in enumerate(floats):
            x, y = tx + local % tile_width, ty + local // tile_width
            if x < width and y < height:
                values[y * width + x] = value
    return {'width': width, 'height': height, 'values': values,
            'tiePoint': list(tags[33922]), 'pixelScale': list(tags[33550]),
            'sparseTileCount': sparse, 'geoKeys': list(tags[34735])}


def masked_grid(tiff_payload, png_payload, extent):
    grid = decode_f32_tiff(tiff_payload)
    mask = Image.open(io.BytesIO(png_payload))
    require(mask.mode == 'RGBA' and mask.size == (grid['width'], grid['height']), 'DEM alpha mask differs')
    expected_scale = [(extent['xmax'] - extent['xmin']) / grid['width'],
                      (extent['ymax'] - extent['ymin']) / grid['height']]
    require(abs(grid['tiePoint'][3] - extent['xmin']) < 1e-6 and abs(grid['tiePoint'][4] - extent['ymax']) < 1e-6, 'DEM georeferencing differs')
    require(all(abs(grid['pixelScale'][i] - expected_scale[i]) < 1e-8 for i in (0, 1)), 'DEM pixel spacing differs')
    alpha = list(mask.getchannel('A').getdata())
    values = []
    for raw, opacity in zip(grid['values'], alpha):
        if opacity != 255:
            values.append(None)
        else:
            require(raw is not None and math.isfinite(raw), 'Valid DEM mask pixel has no raw elevation')
            require(100 < raw < 1000, 'Unexpected local terrain elevation; investigate rather than clamp')
            values.append(raw)
    grid['values'] = values
    grid['validSamples'] = sum(v is not None for v in values)
    grid['missingSamples'] = len(values) - grid['validSamples']
    grid['extent'] = extent
    return grid


def national_point(column, row, grid):
    extent = grid['extent']
    return [extent['xmin'] + (column + .5) * grid['pixelScale'][0],
            extent['ymax'] - (row + .5) * grid['pixelScale'][1]]


def local_xy_cm(point_m, scene):
    datum, axes = scene['cadastralDatumSjtskMm'], scene['siteAxis']
    correction, center = scene['housePlacement']['translationMm'], scene['sceneCenterMm']
    dx, dy = point_m[0] * 1000 - datum['x'], point_m[1] * 1000 - datum['y']
    x = math.floor(dx * axes['ux'] + dy * axes['uy'] + .5) - correction['x']
    y = math.floor(dx * axes['vx'] + dy * axes['vy'] + .5) - correction['y']
    return [(x - center['x']) / 10, -(y - center['y']) / 10]


def smoothstep(value):
    value = min(1, max(0, value))
    return value * value * (3 - 2 * value)


def height_cm(point_cm, height_m, reference_m, coverage_factor=1.0):
    factor = smoothstep((math.hypot(*point_cm) - NEAR_RADIUS_CM) / (BLEND_END_CM - NEAR_RADIUS_CM))
    return FLAT_BASE_CM + (height_m - reference_m) * 100 * factor * coverage_factor


def coverage_factors(grid):
    """Explicit graphical join to unknown flat backdrop, never changed raw DEM."""
    w, h = grid['width'], grid['height']
    distance = [math.inf] * (w * h)
    queue = []
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if grid['values'][i] is None or x in (0, w - 1) or y in (0, h - 1):
                distance[i] = 0
                heapq.heappush(queue, (0, i))
    while queue:
        d, i = heapq.heappop(queue)
        if d != distance[i]:
            continue
        x, y = i % w, i // w
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                j = ny * w + nx
                nd = d + math.hypot(dx * grid['pixelScale'][0], dy * grid['pixelScale'][1])
                if nd < distance[j]:
                    distance[j] = nd
                    heapq.heappush(queue, (nd, j))
    # One cell beyond the first invalid neighbor is flat, so valid and omitted
    # cell edges meet the fallback continuously even after quad validity gating.
    cell = max(grid['pixelScale'][:2]) * math.sqrt(2)
    return [smoothstep((d - cell) / COVERAGE_FADE_M) for d in distance]


def cross(a, b, p):
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def area(points):
    return sum(a[0] * b[1] - a[1] * b[0] for a, b in zip(points, points[1:] + points[:1])) / 2


def clip_halfplane(poly, a, b, inside):
    result = []
    for p, q in zip(poly, poly[1:] + poly[:1]):
        dp, dq = cross(a, b, p), cross(a, b, q)
        ip, iq = (dp >= 0, dq >= 0) if inside else (dp <= 0, dq <= 0)
        if ip:
            result.append(p)
        if ip != iq:
            t = dp / (dp - dq)
            result.append([p[k] + (q[k] - p[k]) * t for k in range(len(p))])
    return result


def subtract_inner(poly, inner):
    result, remaining = [], poly
    for a, b in zip(inner, inner[1:] + inner[:1]):
        outside = clip_halfplane(remaining, a, b, False)
        if len(outside) >= 3 and abs(area(outside)) > .01:
            result.append(outside)
        remaining = clip_halfplane(remaining, a, b, True)
        if len(remaining) < 3 or abs(area(remaining)) < .01:
            break
    return result


def terrain_meshes(grid, scene, reference):
    # Circumscribed polygon guarantees no part enters the protected 300m disc.
    sides = 96
    r = NEAR_RADIUS_CM / math.cos(math.pi / sides)
    inner = [[r * math.cos(i * math.tau / sides), r * math.sin(i * math.tau / sides)] for i in range(sides)]
    width, height = grid['width'], grid['height']
    factors = coverage_factors(grid)
    vertices = []
    for row in range(height):
        for col in range(width):
            value = grid['values'][row * width + col]
            if value is None:
                vertices.append(None)
            else:
                xy = local_xy_cm(national_point(col, row, grid), scene)
                # Store measured value until clipping, then evaluate blend at
                # the final generated XY so circle-boundary interpolation stays flat.
                vertices.append([*xy, value, factors[row * width + col]])
    chunks = {}
    omitted_cells, measured_cells = 0, 0
    for row in range(height - 1):
        for col in range(width - 1):
            points = [vertices[row * width + col], vertices[row * width + col + 1],
                      vertices[(row + 1) * width + col + 1], vertices[(row + 1) * width + col]]
            if any(p is None for p in points):
                omitted_cells += 1
                continue
            measured_cells += 1
            key = (row // 64, col // 64)
            chunk = chunks.setdefault(key, {'id': 'context_distant_terrain_%d_%d' % key,
                                           'material': 'context_distant_terrain', 'verticesCm': [],
                                           'indices': [], 'uvs': [], 'winding': 'clockwise',
                                           'nanite': True, 'collision': 'NoCollision', '_lookup': {}})
            for triangle in [[points[0], points[1], points[2]], [points[0], points[2], points[3]]]:
                distances = [math.hypot(p[0], p[1]) for p in triangle]
                if max(distances) < NEAR_RADIUS_CM:
                    continue
                # A triangle wholly farther than the circumscribed disc needs
                # no 96-edge clipping. Radial edge minima catch crossings.
                box_far = (min(p[0] for p in triangle) > r or max(p[0] for p in triangle) < -r
                           or min(p[1] for p in triangle) > r or max(p[1] for p in triangle) < -r)
                polygons = [triangle] if box_far else subtract_inner(triangle, inner)
                for polygon in polygons:
                    for i in range(1, len(polygon) - 1):
                        tri = [polygon[0], polygon[i], polygon[i + 1]]
                        if abs(cross(*tri)) < .01:
                            continue
                        if cross(*tri) > 0:
                            tri.reverse()
                        for point in tri:
                            v = [point[0], point[1], height_cm(point[:2], point[2], reference, point[3])]
                            identity = tuple(round(x, 5) for x in v)
                            index = chunk['_lookup'].get(identity)
                            if index is None:
                                index = len(chunk['verticesCm'])
                                chunk['_lookup'][identity] = index
                                chunk['verticesCm'].append(v)
                                chunk['uvs'].append([v[0] / 10000, v[1] / 10000])
                            chunk['indices'].append(index)
    meshes = []
    for chunk in chunks.values():
        chunk.pop('_lookup')
        if chunk['indices']:
            meshes.append(chunk)
    return meshes, {'measuredGridCells': measured_cells, 'omittedNoDataCells': omitted_cells,
                    'coverageJoinSamples': sum(v is not None and f < 1 for v, f in zip(grid['values'], factors))}


def flat_fallback(grid, scene):
    """Explicit unresolved backdrop only: no-data cells, outside DEM, near join."""
    mesh = {'id': 'context_unresolved_flat_backdrop', 'material': 'context_distant_terrain',
            'verticesCm': [], 'indices': [], 'uvs': [], 'winding': 'clockwise',
            'nanite': True, 'collision': 'NoCollision',
            'evidence': 'ILLUSTRATIVE_FLAT_FALLBACK_NO_MEASURED_HEIGHT_CLAIM'}
    def polygon(points):
        for i in range(1, len(points) - 1):
            tri = [points[0], points[i], points[i + 1]]
            if abs(cross(*tri)) < .01:
                continue
            if cross(*tri) > 0:
                tri.reverse()
            n = len(mesh['verticesCm'])
            mesh['verticesCm'].extend([[p[0], p[1], FLAT_BASE_CM] for p in tri])
            mesh['indices'].extend([n, n + 1, n + 2])
            mesh['uvs'].extend([[p[0] / 10000, p[1] / 10000] for p in tri])
    w, h = grid['width'], grid['height']
    for y in range(h - 1):
        for x in range(w - 1):
            ids = [y * w + x, y * w + x + 1, (y + 1) * w + x + 1, (y + 1) * w + x]
            if any(grid['values'][i] is None for i in ids):
                polygon([local_xy_cm(national_point(i % w, i // w, grid), scene) for i in ids])
    corners = [local_xy_cm(national_point(x, y, grid), scene) for x, y in [(0, 0), (w - 1, 0), (w - 1, h - 1), (0, h - 1)]]
    if area(corners) < 0:
        corners.reverse()
    outer = [[-3000000, -3000000, 0], [3000000, -3000000, 0], [3000000, 3000000, 0], [-3000000, 3000000, 0]]
    for piece in subtract_inner(outer, corners):
        polygon(piece)
    # Existing DOM_00000 is only 240x200m. WFS is not a complete square;
    # fill under all new context beyond that baseline to avoid open seams.
    radius = NEAR_RADIUS_CM / math.cos(math.pi / 96)
    disk = [[radius * math.cos(i * math.tau / 96), radius * math.sin(i * math.tau / 96), 0] for i in range(96)]
    protected_square = [[-12000, -10000], [12000, -10000], [12000, 10000], [-12000, 10000]]
    for piece in subtract_inner(disk, protected_square):
        polygon(piece)
    return mesh


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    scene_path, output = args.scene.resolve(), args.output.resolve()
    require(output.is_relative_to(ROOT / 'output/unreal'), 'Output must be isolated in output/unreal')
    require(not (output / 'terrain-plan.json').exists(), 'Terrain plan is immutable; use a new output directory')
    scene = json.loads(scene_path.read_text())
    require(scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'C/B/B required')
    require(scene['housePlacement']['streetSetbackMm'] == scene['housePlacement']['eastSetbackMm'] == 3000, 'Setbacks changed')
    cx, cy = scene['cadastralDatumSjtskMm']['x'] / 1000, scene['cadastralDatumSjtskMm']['y'] / 1000
    inputs = output / 'inputs'
    metadata_path = inputs / 'service-metadata.json'
    if not metadata_path.exists():
        write_once(metadata_path, fetch(SERVICE + '?f=pjson'))
    metadata = json.loads(metadata_path.read_text())
    require(metadata['pixelType'] == 'F32' and metadata['bandCount'] == 1, 'Unexpected official DEM service')
    # A bounded east/north shift retains the verified distant peak well inside
    # the outer join, rather than flattening a summit at the edge of the tile.
    raw_path, raw_receipt = pinned_export(inputs, 'dmr5g-16km-f32', request_parameters(cx + 1200, cy + 1000, HALF_EXTENT_M, GRID, 'tiff', 'F32'))
    mask_path, mask_receipt = pinned_export(inputs, 'dmr5g-16km-mask', request_parameters(cx + 1200, cy + 1000, HALF_EXTENT_M, GRID, 'png32', 'U8'))
    site_path, site_receipt = pinned_export(inputs, 'dmr5g-site-2m', request_parameters(cx, cy, 17, 17, 'tiff', 'F32'))
    site_mask_path, site_mask_receipt = pinned_export(inputs, 'dmr5g-site-mask', request_parameters(cx, cy, 17, 17, 'png32', 'U8'))
    require(raw_receipt['response']['extent'] == mask_receipt['response']['extent'], 'DEM/mask footprint differs')
    require(site_receipt['response']['extent'] == site_mask_receipt['response']['extent'], 'Reference/mask footprint differs')
    grid = masked_grid(raw_path.read_bytes(), mask_path.read_bytes(), raw_receipt['response']['extent'])
    site_grid = masked_grid(site_path.read_bytes(), site_mask_path.read_bytes(), site_receipt['response']['extent'])
    reference = site_grid['values'][8 * 17 + 8]
    require(reference is not None, 'No site height available for relative terrain anchor')
    meshes, counts = terrain_meshes(grid, scene, reference)
    meshes.append(flat_fallback(grid, scene))
    valid = [(i, z) for i, z in enumerate(grid['values']) if z is not None]
    peak_index, peak_z = max(valid, key=lambda item: item[1])
    peak_national = national_point(peak_index % GRID, peak_index // GRID, grid)
    peak_xy = local_xy_cm(peak_national, scene)
    input_paths = [scene_path, Path(__file__).resolve(), *sorted(inputs.iterdir())]
    plan = {'schemaVersion': 1, 'owner': OWNER, 'status': 'native-compatible-not-native-verified',
            'units': 'centimetres', 'axes': 'UE X=OBJ X/10, Y=-OBJ Y/10, Z=relative relief',
            'inputFiles': {str(path): sha(path) for path in input_paths if path.is_file()},
            'meshes': meshes, 'groups': [], 'sourceSceneSha256': sha(scene_path),
            'generatorSha256': sha(Path(__file__)), 'serviceMetadataSha256': sha(metadata_path),
            'activeDesign': scene['activeDesign'], 'housePlacement': scene['housePlacement'],
            'sourceEvidence': {'source': SERVICE, 'license': 'CC BY 4.0', 'licenseUrl': LICENSE_URL,
                               'attribution': raw_receipt['attribution'], 'heightSystem': 'Bpv (EPSG:8357)',
                               'crs': 'EPSG:5514', 'serviceNativeCellMetres': metadata['pixelSizeX'],
                               'acquisition': 'Service description: airborne laser scanning 2009–2013; current service snapshot does not establish current as-built terrain',
                               'raw': raw_receipt, 'validityMask': mask_receipt,
                               'reference': site_receipt, 'referenceValidityMask': site_mask_receipt},
            'grid': {'width': GRID, 'height': GRID, 'extent': grid['extent'],
                     'pixelSizeMetres': grid['pixelScale'][:2], 'valuesBpvMetres': grid['values'],
                     'validSamples': grid['validSamples'], 'missingSamples': grid['missingSamples'],
                     'missingPercent': 100 * grid['missingSamples'] / (GRID * GRID),
                     'minimumBpvMetres': min(z for i, z in valid), 'maximumBpvMetres': peak_z,
                     'rawSparseTileCount': grid['sparseTileCount'], **counts},
            'heightPolicy': {'referenceBpvMetres': reference, 'referenceNationalMetres': [cx, cy],
                             'referenceRole': 'Relative landscape anchor, NOT finished-floor or street survey datum',
                             'nearExclusionRadiusCm': NEAR_RADIUS_CM, 'blendEndRadiusCm': BLEND_END_CM,
                             'flatJoinElevationCm': FLAT_BASE_CM, 'verticalExaggeration': 1.0,
                             'coverageEdgeFadeMetres': COVERAGE_FADE_M,
                             'coverageEdgeFadeRole': 'Explicit graphical join to unresolved flat backdrop; raw Bpv samples unchanged',
                             'formula': 'Zcm=-25+(Hsample-Hreference)*100*nearRadialSmoothstep*coverageEdgeSmoothstep'},
            'noDataFallback': {'enabled': True, 'meshId': 'context_unresolved_flat_backdrop',
                               'heightCm': FLAT_BASE_CM, 'measured': False,
                               'scope': 'No-data cells including Austria, outside sampled rectangle, and 300m near join outside original DOM_00000 baseline rectangle',
                               'preservedOriginalBaselineBoundsCm': [-12000, -10000, 12000, 10000],
                               'replaceOriginalFlatVisualSourceIds': ['DOM_02039']},
            'peakSample': {'heightBpvMetres': peak_z, 'nationalMetres': peak_national,
                           'positionCm': [*peak_xy, height_cm(peak_xy, peak_z, reference)],
                           'distanceFromSceneMetres': math.hypot(*peak_xy) / 100},
            'limits': ['Measured relief uses only valid Czech coverage; Austria/no-data are a separately identified illustrative flat backdrop',
                       '16km square sampled to257x257 (~62m), interpolated distant relief; not original2m detail',
                       '300–900m radial blend is an explicit graphical join, not survey terrain',
                       'No house, parcel, original road, walking collision or FFL datum is changed',
                       'Existing infinite flat background can occlude measured valleys; importer must treat it separately',
                       'No current land-cover, forest canopy, building height or botanical reconstruction is claimed'],
            'summary': {'meshCount': len(meshes), 'vertices': sum(len(m['verticesCm']) for m in meshes),
                        'triangles': sum(len(m['indices']) // 3 for m in meshes)}}
    write_once(output / 'terrain-plan.json', encode(plan))
    summary = {**plan['summary'], 'referenceBpvMetres': reference,
               'validSamples': grid['validSamples'], 'missingSamples': grid['missingSamples'],
               'minMaxBpvMetres': [plan['grid']['minimumBpvMetres'], peak_z],
               'plan': str(output / 'terrain-plan.json'), 'sha256': sha(output / 'terrain-plan.json')}
    write_once(output / 'summary.json', encode(summary))
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
