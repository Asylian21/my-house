"""Source-only photo-body UV proposal; no UObject, scene or texture writes.

The existing managed lawn and its available three source LODs retain every
position, normal, color, UV1 and index byte. Only UV0 and its derived tangent
frame change. Original opaque photographic interiors are used directly.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-lawn-leaf-strip-study-r41-r2.py'
OUT = ROOT / 'output/unreal/exterior-lawn-leaf-strip-20261002-r41-source-study-r2'
PHOTO = ROOT / 'output/unreal/exterior-lawn-photo-variants-20261001-r3-study'
TAPERED = ROOT / 'output/unreal/exterior-lawn-tapered-integration-20261001-r1c'
R38 = ROOT / 'output/unreal/exterior-20261002-r38b'
ORIGINAL = ROOT / 'output/unreal/exterior-assets-20260926-r1/glb/grass_medium_02.glb'
SCHEMA = 'brezi-original-photo-lawn-leaf-body-uv-source-proposal-r41'
FAILURE = ROOT / 'output/unreal/exterior-lawn-leaf-strip-20261002-r41-failed-source-attempt-r1/failed-source-attempt.json'
FAILURE_SHA = 'c334dd3652434e317828031f85961438e1184c1046f183c7c2419ad0710bf53f'
NATIVE_MATERIAL = '/Game/Brezi/Exterior20260926/Materials/M_lawn_photographic_blade.M_lawn_photographic_blade'
# Authored interior choices from the actual original connected UV components.
# Pixel bounds are half-open; mapped UV endpoints are interior pixel centres.
BODIES = (
    {'id': 'horizontal_green', 'componentRoot': 25, 'vertices': 39, 'rect': [1236, 1931, 1471, 1955], 'weight': 40, 'axis': 0},
    {'id': 'upright_olive', 'componentRoot': 537, 'vertices': 26, 'rect': [1400, 1424, 1418, 1806], 'weight': 25, 'axis': 1},
    {'id': 'upright_green', 'componentRoot': 563, 'vertices': 41, 'rect': [1882, 667, 1925, 1714], 'weight': 25, 'axis': 1},
    {'id': 'dry_body', 'componentRoot': 64, 'vertices': 53, 'rect': [1003, 918, 1011, 1043], 'weight': 10, 'axis': 1},
)
PINS = {
    str(ORIGINAL): 'c09551da5f8138fc84fe50a05d6d8d4ce3cd6dd504e32cdc10ba5218b6dd386a',
    str(PHOTO / 'lawn-photographic-variants.glb'): 'ddb4402577e844ec5e70ca4417c0c686778cca4f35f6c766155313a6aae9aebd',
    str(PHOTO / 'geometry-manifest.json'): '4f671b902732999f542e301ab11cab3ca29e6718cdad1d5d8bd0da6b81781730',
    str(PHOTO / 'geometry-uv-tangent-proof.json'): '49f45c2d1e4a585c6ae993e3264f8fc83e1c37904caa3676f48057bbc83a25aa',
    str(PHOTO / 'material-manifest.json'): '9a0275363882594afb4b656ffbd7528866ad63366d03cf938bf562ac6ec5c88e',
    str(TAPERED / 'lawn-natural.glb'): '4f99b430de0c7437dec8a30f4024eb419af8838ea25b8822bd7244c4ae30b2af',
    str(TAPERED / 'lawn-natural-plan.json'): '0c13741cf2344ef809ac4427b4102a4917eefd508bc0b3c3746312029800c319',
    str(R38 / 'soft-ground-native-report-r2.json'): '077e36066dc49f2c3fa379893c39fc5659e8261385030d86266316e1bde9f2b9',
    str(R38 / 'soft-ground-checkpoint/saved-actors.json'): '750cb8609a15fd334900d474fce7c3e041d66a1fe650e350e594de386e83a634',
    str(R38 / 'soft-ground-checkpoint/raw-controls-saved.json'): '6fad46bb36d26340cda1f40f941544ef8724df2c93c20672f70b3c323c40710d',
    str(R38 / 'soft-ground-checkpoint/old-materials-saved.json'): '2de136442a53bf206a106d646f664b65499a3bba1abc8b92ec3e4806ac74649e',
}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate_replacement_bytes(before, after, ranges):
    require(len(before) == len(after), 'UV/tangent proposal changed original file size')
    changed = np.zeros(len(before), dtype=bool)
    for row in ranges:
        require(row['attribute'] in ('TEXCOORD_0', 'TANGENT') and 0 <= row['start'] < row['stop'] <= len(before),
                'Only bounded original UV0/tangent accessor ranges may change')
        require(not changed[row['start']:row['stop']].any(), 'Original modified accessors overlap')
        changed[row['start']:row['stop']] = True
    a, b = np.frombuffer(before, 'uint8'), np.frombuffer(after, 'uint8')
    require(np.array_equal(a[~changed], b[~changed]), 'Proposal changed bytes outside UV0/tangent ranges')
    return changed


def pin(path):
    p = Path(path).resolve()
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def glb(path):
    raw = Path(path).read_bytes()
    require(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Original GLB header changed')
    length, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a, 'Original GLB JSON missing')
    doc = json.loads(raw[20:20 + length])
    size, kind = struct.unpack_from('<II', raw, 20 + length)
    require(kind == 0x004e4942 and 28 + length + size == len(raw), 'Original GLB binary missing')
    binary_offset = 28 + length
    def accessor(index):
        a = doc['accessors'][index]
        view = doc['bufferViews'][a['bufferView']]
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: '<u1'}[a['componentType']]
        item = np.dtype(dtype).itemsize
        require('sparse' not in a and view.get('byteStride', width * item) == width * item, 'Unsupported original accessor layout')
        offset = binary_offset + view.get('byteOffset', 0) + a.get('byteOffset', 0)
        array = np.frombuffer(raw, dtype=dtype, count=a['count'] * width, offset=offset).reshape(-1, width).copy()
        return array, offset, array.nbytes
    rows = {}
    for node in doc['nodes']:
        p = doc['meshes'][node['mesh']]['primitives']
        require(len(p) == 1 and p[0].get('mode', 4) == 4 and not any(k in node for k in ('matrix', 'translation', 'rotation', 'scale')),
                'Original triangle-node basis changed')
        row = {key: accessor(value)[0] for key, value in p[0]['attributes'].items()}
        row['indices'] = accessor(p[0]['indices'])[0].reshape(-1, 3)
        rows[node['name']] = row
    return raw, doc, accessor, rows


def connected_components(row):
    parent = list(range(len(row['POSITION'])))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for face in row['indices']:
        for j in face[1:]:
            parent[find(int(j))] = find(int(face[0]))
    components = {}
    for i in range(len(parent)):
        components.setdefault(find(i), []).append(i)
    result = []
    for indices in components.values():
        selected = np.isin(row['indices'][:, 0], indices)
        require(np.all(np.isin(row['indices'][selected], indices)), 'Connected component split a source face')
        uv = row['TEXCOORD_0'][indices]
        result.append({'componentRoot': min(indices), 'sourceVertexIndices': indices,
                       'sourceTriangleIndices': np.nonzero(selected)[0].tolist(), 'vertices': len(indices),
                       'triangles': int(selected.sum()), 'uvBounds': [uv.min(0).tolist(), uv.max(0).tolist()]})
    return sorted(result, key=lambda r: r['componentRoot'])


def points_in_triangles(points, triangles):
    inside = np.zeros(len(points), dtype=bool)
    x, y = points[:, 0], points[:, 1]
    for t in triangles:
        den = (t[1, 1] - t[2, 1]) * (t[0, 0] - t[2, 0]) + (t[2, 0] - t[1, 0]) * (t[0, 1] - t[2, 1])
        if den == 0:
            continue
        a = ((t[1, 1] - t[2, 1]) * (x - t[2, 0]) + (t[2, 0] - t[1, 0]) * (y - t[2, 1])) / den
        b = ((t[2, 1] - t[0, 1]) * (x - t[2, 0]) + (t[0, 0] - t[2, 0]) * (y - t[2, 1])) / den
        inside |= (a >= 0) & (b >= 0) & (a + b <= 1)
    return inside


def body_certificate(body, source, components, alpha, original_rgb, padded_rgb):
    component = next(r for r in components if r['componentRoot'] == body['componentRoot'])
    require(component['vertices'] == body['vertices'], 'Selected original connected body identity changed')
    x0, y0, x1, y1 = body['rect']
    require(2 <= x0 < x1 < 2046 and 2 <= y0 < y1 < 2046, 'Body crop lacks original bilinear support')
    yy, xx = np.mgrid[y0:y1, x0:x1]
    p = np.column_stack([(xx.ravel() + .5) / 2048, (yy.ravel() + .5) / 2048])
    triangles = source['TEXCOORD_0'][source['indices'][component['sourceTriangleIndices']]].astype(float)
    require(points_in_triangles(p, triangles).all(), 'Body crop texel centres escape the selected original connected UV body')
    support = alpha[y0 - 2:y1 + 2, x0 - 2:x1 + 2]
    require(np.all(support == 65535), 'Complete original bilinear mip0 body support is not fully opaque')
    rgb = original_rgb[y0:y1, x0:x1, :3]
    require(np.array_equal(rgb, padded_rgb[y0:y1, x0:x1, :3]), 'Current padded map changed selected opaque photographic RGB')
    return {**deepcopy(body), 'originalComponent': component,
            'mappedUvBounds': [[(x0 + .5) / 2048, (y0 + .5) / 2048], [(x1 - .5) / 2048, (y1 - .5) / 2048]],
            'originalBodyTexelCentresTested': len(p), 'everyTestedCentreInsideOriginalUvTriangleUnion': True,
            'continuousOriginalUvTriangleUnionContainmentClaimed': False,
            'completeBilinearMip0SupportTexels': int(support.size), 'minimumSupportAlpha16': int(support.min()),
            'continuousMip0BilinearAlphaAtLeastClip': True, 'nativeMipsTsrOrVisibleCoverageVerified': False,
            'encodedSrgbRgb8Mean': rgb.mean((0, 1)).tolist(), 'encodedSrgbRgb8Stddev': rgb.std((0, 1)).tolist(),
            'encodedSrgbStatisticsAreNotNativeOrLinearColor': True, 'opaqueOriginalAndExistingPaddedRgbBytesEqual': True,
            'sourcePhotographicPixelsChanged': False}


def assign_bodies(mesh, blades):
    raw_counts = np.asarray([b['weight'] for b in BODIES], dtype=float) * blades / 100
    counts = np.floor(raw_counts).astype(int)
    for i in sorted(range(4), key=lambda x: (-float(raw_counts[x] - counts[x]), x))[:blades - int(counts.sum())]:
        counts[i] += 1
    ordered = sorted(range(blades), key=lambda x: hashlib.sha256((mesh + '/' + str(x)).encode()).digest())
    result = [None] * blades
    offset = 0
    for body, count in zip(BODIES, counts):
        for index in ordered[offset:offset + int(count)]:
            result[index] = body['id']
        offset += int(count)
    require(offset == blades and all(result), 'Every original whole blade needs one coherent photographic body')
    return result


def mapped_uv(normalized, body):
    require(normalized.shape == (5, 2) and np.isfinite(normalized).all() and normalized.min() >= 0 and normalized.max() <= 1,
            'Original five-vertex normalized UV controls changed')
    require(np.array_equal(normalized[[0, 1, 4]], [[0, 0], [1, 0], [.5, 1]]) and
            normalized[2, 0] == 0 and normalized[3, 0] == 1 and normalized[2, 1] == normalized[3, 1],
            'Original complete leaf root/mid/tip topology changed')
    lo, hi = np.asarray(body['mappedUvBounds'])
    out = np.empty((5, 2), dtype=float)
    axis, cross = body['axis'], 1 - body['axis']
    out[:, axis] = hi[axis] + (lo[axis] - hi[axis]) * normalized[:, 1]
    out[:, cross] = lo[cross] + (hi[cross] - lo[cross]) * normalized[:, 0]
    out = out.astype('<f4')
    require(np.all(out >= lo) and np.all(out <= hi), 'Float32 photo UV escaped its fully opaque support rectangle')
    return out


def tangent_frame(row, uv):
    p = row['POSITION'].astype(float)
    normals = row['NORMAL'].astype(float)
    ts = np.zeros_like(p)
    bs = np.zeros_like(p)
    uv_areas = []
    for face in row['indices']:
        q, v = p[face], uv[face].astype(float)
        e1, e2 = q[1] - q[0], q[2] - q[0]
        d1, d2 = v[1] - v[0], v[2] - v[0]
        det = d1[0] * d2[1] - d1[1] * d2[0]
        area = np.linalg.norm(np.cross(e1, e2))
        require(abs(det) > 1e-14 and area > 0, 'New photographic UV or preserved geometric triangle degenerate')
        ts[face] += ((e1 * d2[1] - e2 * d1[1]) / det) * area
        bs[face] += ((e2 * d1[0] - e1 * d2[0]) / det) * area
        uv_areas.append(abs(det) / 2)
    normals = normals / np.linalg.norm(normals, axis=1)[:, None]
    tangent = ts - normals * np.sum(normals * ts, axis=1)[:, None]
    lengths = np.linalg.norm(tangent, axis=1)
    require(np.all(lengths > 0), 'Derived source UV tangent cancelled')
    tangent /= lengths[:, None]
    handedness = np.sum(np.cross(normals, tangent) * bs, axis=1)
    require(np.all(handedness != 0), 'Derived UV bitangent orientation undefined')
    result = np.column_stack([tangent, np.where(handedness < 0, -1., 1.)]).astype('<f4')
    require(np.isfinite(result).all() and np.max(abs(np.linalg.norm(result[:, :3], axis=1) - 1)) < 1e-6 and
            np.max(abs(np.sum(normals * result[:, :3], axis=1))) < 1e-6, 'Derived float32 source tangent frame invalid')
    return result, {'minimumUvTriangleArea': min(uv_areas),
                    'maximumFloat32TangentUnitError': float(np.max(abs(np.linalg.norm(result[:, :3], axis=1) - 1))),
                    'maximumFloat32TangentNormalDot': float(np.max(abs(np.sum(normals * result[:, :3], axis=1))))}


def triangle_alpha_certificate(uv, faces, alpha, require_opaque=True):
    """All bilinear unit cells intersecting a source UV triangle, by SAT.

    Minima of the four support texels bound bilinear interpolation throughout
    each cell. This is a mip0 source certificate, never native mip/TSR proof.
    """
    minimum = 65535
    tested = 0
    for face in faces:
        t = uv[face].astype(float) * 2048 - .5
        lo = np.floor(t.min(0)).astype(int)
        hi = np.floor(t.max(0)).astype(int)
        require(np.all(lo >= 0) and np.all(hi + 1 < 2048), 'Source UV lacks bounded bilinear support')
        yy, xx = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
        centres = np.stack([xx + .5, yy + .5], axis=-1)
        overlap = np.ones(xx.shape, dtype=bool)
        for j in range(3):
            edge = t[(j + 1) % 3] - t[j]
            axis = np.asarray([-edge[1], edge[0]])
            tp = t @ axis
            cp = centres @ axis
            radius = .5 * abs(axis).sum()
            overlap &= (cp + radius >= tp.min()) & (cp - radius <= tp.max())
        x, y = xx[overlap], yy[overlap]
        values = np.minimum.reduce([alpha[y, x], alpha[y, x + 1], alpha[y + 1, x], alpha[y + 1, x + 1]])
        require(len(values), 'No original UV triangle support cells tested')
        minimum = min(minimum, int(values.min()))
        tested += len(values)
    passed = minimum / 65535 >= .3330000042915344
    if require_opaque:
        require(passed, 'Original source alpha can remove coverage at the unchanged material clip')
    return {'minimumBilinearSupportAlpha16': minimum, 'intersectingSupportCellsTestedWithRepetitions': tested,
            'conservativeContinuousMip0AlphaLowerBoundPassedClip': passed,
            'failedLowerBoundProvesActualTransparency': False, 'nativeMipOrOpticalCoverageVerified': False}


def sample_alpha(alpha, uv):
    p = uv * 2048 - .5
    lo = np.floor(p).astype(int)
    require(np.all(lo >= 0) and np.all(lo + 1 < 2048), 'Projected alpha lacks original bilinear support')
    f = p - lo
    x, y = lo[:, 0], lo[:, 1]
    return ((alpha[y, x] * (1 - f[:, 0]) + alpha[y, x + 1] * f[:, 0]) * (1 - f[:, 1]) +
            (alpha[y + 1, x] * (1 - f[:, 0]) + alpha[y + 1, x + 1] * f[:, 0]) * f[:, 1]) / 65535


def projection_masks(row, alpha):
    """Bounded exact raster comparison under a declared source convention.

    Pillow's touched-pixel opaque triangles are the geometric support. Alpha
    is sampled at pixel-centre barycentrics clamped to the triangle boundary
    for touched edge pixels. Union ignores depth occlusion. It is not a native
    camera, texture mip, MSAA/TSR or continuous full-population coverage proof.
    """
    p = row['POSITION'][:, [0, 2, 1]].astype(float) * 100
    results = []
    for axes, label in (((0, 1), 'groundXY'), ((0, 2), 'sideXZ'), ((1, 2), 'sideYZ')):
        q = p[:, axes]
        lo, hi = q.min(0), q.max(0)
        require(np.all(hi > lo), 'Source projection collapsed')
        q = 2 + (q - lo) / (hi - lo) * 507
        im = Image.new('L', (512, 512), 0)
        draw = ImageDraw.Draw(im)
        photo = np.zeros((512, 512), dtype=bool)
        for face in row['indices']:
            draw.polygon([tuple(v) for v in q[face]], fill=255)
            t = q[face]
            lower = np.maximum(np.floor(t.min(0)).astype(int) - 1, [0, 0])
            upper = np.minimum(np.ceil(t.max(0)).astype(int) + 1, [511, 511])
            if np.any(upper < lower):
                continue
            local = Image.new('L', tuple((upper - lower + 1).tolist()), 0)
            ImageDraw.Draw(local).polygon([tuple(v - lower) for v in t], fill=255)
            yy, xx = np.nonzero(np.asarray(local) > 0)
            den = (t[1, 1] - t[2, 1]) * (t[0, 0] - t[2, 0]) + (t[2, 0] - t[1, 0]) * (t[0, 1] - t[2, 1])
            if den == 0:
                continue
            x, y = xx + lower[0] + .5, yy + lower[1] + .5
            a = ((t[1, 1] - t[2, 1]) * (x - t[2, 0]) + (t[2, 0] - t[1, 0]) * (y - t[2, 1])) / den
            b = ((t[2, 1] - t[0, 1]) * (x - t[2, 0]) + (t[0, 0] - t[2, 0]) * (y - t[2, 1])) / den
            bary = np.maximum(np.column_stack([a, b, 1 - a - b]), 0)
            bary /= bary.sum(1)[:, None]
            passed = sample_alpha(alpha, bary @ row['TEXCOORD_0'][face].astype(float)) >= .3330000042915344
            photo[yy[passed] + lower[1], xx[passed] + lower[0]] = True
        mask = np.asarray(im) > 0
        require(not np.any(photo & ~mask), 'Source photo mask escaped geometric support')
        results.append(({'projection': label, 'sourceBoundsCm': [lo.tolist(), hi.tolist()], 'resolution': [512, 512],
                         'opaqueGeometricCoveredPixels': int(mask.sum()), 'opaqueGeometrySha256': hashlib.sha256(mask.tobytes()).hexdigest(),
                         'actualBilinearMip0AlphaCoveredPixels': int(photo.sum()), 'alphaMaskSha256': hashlib.sha256(photo.tobytes()).hexdigest()},
                        mask, photo))
    return results


def current_controls(source_plan, report, witness, raw, material_witness):
    require(report['status'] == 'verified-saved-image-selected-fixed-world-soft-ground-material-overlay' and
            report['nativeProcessId'] == 72504 and report['schemaVersion'] == 2, 'Actual recorded R38 source-basis report changed')
    require(source_plan['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'} and
            source_plan['housePlacement']['streetSetbackMm'] == source_plan['housePlacement']['eastSetbackMm'] == 3000,
            'Original C/B/B/setback source contract changed')
    records = []
    by_label = {row['id'].replace('lawn_natural_', 'lawn_photo_', 1): row for row in source_plan['groups']}
    for actor_path, actor in witness.items():
        components = [c for c in actor['components'] if c.get('materials') == [NATIVE_MATERIAL]]
        if not components:
            continue
        require(len(components) == 1 and actor['label'] in by_label, 'Unknown or duplicate actual managed-lawn group')
        component = components[0]
        source = by_label[actor['label']]
        mesh = source['meshId'].replace('lawn_natural_', 'lawn_photo_', 1)
        require(component['mesh'].endswith('/' + mesh + '_LOD0.' + mesh + '_LOD0') and
                component['instanceCount'] == len(source['instances']) and component['instanceCullCm'] == [3200, 4000] and
                actor['detailDensityScaling'] is True, 'Recorded actual lawn member/material/cull contract differs')
        require(raw[component['path']]['instances'] == component['instanceCount'], 'Recorded lawn raw membership differs')
        records.append({'actor': actor_path, 'sourceGroup': source['id'], 'sourceMeshId': mesh,
                        'recordedActorWitnessSha256': digest(actor), 'recordedComponentWitnessSha256': digest(component),
                        'recordedOrderedInstanceTransformsSha256': component['orderedInstanceTransformsSha256'],
                        'recordedRawControl': raw[component['path']], 'sourceOrderedInstancesSha256': digest(source['instances']),
                        'instances': component['instanceCount']})
    require(len(records) == 40 and sum(r['instances'] for r in records) == 102011 and
            set(by_label) == {witness[r['actor']]['label'] for r in records}, 'Actual/source managed-lawn scope must be exactly40/102011')
    material = material_witness[NATIVE_MATERIAL]
    require(material['graphSha256'] == '2c933cabfa14ac5e3ed4e2c7b801be05bed6d121382da0dd7e6a3724b936c05a',
            'Recorded original photographic material graph changed')
    return sorted(records, key=lambda r: r['actor']), material


def build():
    require(not OUT.exists(), 'One fresh R41 source-study directory only')
    inputs = {**PINS, str(Path(__file__).resolve()): sha(__file__), str(FAILURE): FAILURE_SHA}
    for row in json.loads(FAILURE.read_text())['sourceSnapshots']:
        inputs[row['immutableSnapshot']['path']] = row['immutableSnapshot']['sha256']
    recipe = json.loads((PHOTO / 'material-manifest.json').read_text())['lawn_photographic_blade']
    original_map = recipe['albedoDerivation']['sourceAlbedo']
    for row in [*recipe['maps'].values(), original_map]:
        inputs[row['path']] = row['sha256']
    for path, expected in inputs.items():
        require(sha(path) == expected, 'Pinned input changed: ' + path)
    original_rgb = np.asarray(Image.open(original_map['path']))
    padded_rgb = np.asarray(Image.open(recipe['maps']['albedo']['path']))
    alpha = np.asarray(Image.open(recipe['maps']['alpha']['path']))
    require(alpha.shape == (2048, 2048) and alpha.dtype.itemsize >= 2 and alpha.max() == 65535,
            'Original 16bit alpha layout changed')
    _, original_doc, _, original_rows = glb(ORIGINAL)
    source_body = original_rows['PH_grass_medium_02_a_LOD0']
    components = connected_components(source_body)
    require(len(components) == 18 and len({digest(c['uvBounds']) for c in components}) == 6,
            'Original connected photo-body census changed')
    bodies = [body_certificate(body, source_body, components, alpha, original_rgb, padded_rgb) for body in BODIES]
    body_by_id = {b['id']: b for b in bodies}
    raw_bytes, doc, accessor, old_rows = glb(PHOTO / 'lawn-photographic-variants.glb')
    _, normalized_doc, _, normalized_rows = glb(TAPERED / 'lawn-natural.glb')
    require(len(old_rows) == len(normalized_rows) == 60, 'All20 original managed-lawn masters×3 actual sourceLODs required')
    source_plan = json.loads((TAPERED / 'lawn-natural-plan.json').read_text())
    report = json.loads((R38 / 'soft-ground-native-report-r2.json').read_text())
    witness = json.loads((R38 / 'soft-ground-checkpoint/saved-actors.json').read_text())
    raw = json.loads((R38 / 'soft-ground-checkpoint/raw-controls-saved.json').read_text())
    material_witness = json.loads((R38 / 'soft-ground-checkpoint/old-materials-saved.json').read_text())
    controls, material = current_controls(source_plan, report, witness, raw, material_witness)
    new_bytes = bytearray(raw_bytes)
    ranges, nodes, assignments, alpha_cache = [], [], {}, {}
    for node in doc['nodes']:
        name = node['name']
        old = old_rows[name]
        normalized = normalized_rows[name.replace('lawn_photo_', 'lawn_natural_', 1)]
        for key in ('POSITION', 'NORMAL', 'COLOR_0', 'TEXCOORD_1', 'indices'):
            require(old[key].tobytes() == normalized[key].tobytes(), 'Normalized UV controls do not describe the exact current source geometry')
        require(len(old['POSITION']) % 5 == 0 and len(old['indices']) == len(old['POSITION']) * 3 // 5,
                'Original whole five-vertex/three-triangle blade topology differs')
        mesh_id, lod = name.rsplit('_LOD', 1)
        require(lod in ('0', '1', '2'), 'Unexpected available source LOD')
        allocation = assign_bodies(mesh_id, len(old['POSITION']) // 5)
        assignments.setdefault(mesh_id, allocation)
        require(assignments[mesh_id] == allocation, 'Photographic body changed across existing source LODs')
        new_uv = np.vstack([mapped_uv(normalized['TEXCOORD_0'][i * 5:i * 5 + 5], body_by_id[body])
                            for i, body in enumerate(allocation)])
        new_tangent, tangent_proof = tangent_frame(old, new_uv)
        p = doc['meshes'][node['mesh']]['primitives'][0]
        for key, replacement in (('TEXCOORD_0', new_uv), ('TANGENT', new_tangent)):
            _, offset, size = accessor(p['attributes'][key])
            require(replacement.nbytes == size, 'Existing UV/tangent accessor size changed')
            new_bytes[offset:offset + size] = replacement.tobytes()
            ranges.append({'node': name, 'attribute': key, 'start': offset, 'stop': offset + size})
        old_alpha_key = hashlib.sha256(old['TEXCOORD_0'].tobytes() + old['indices'].tobytes()).hexdigest()
        if old_alpha_key not in alpha_cache:
            alpha_cache[old_alpha_key] = triangle_alpha_certificate(old['TEXCOORD_0'], old['indices'], alpha, require_opaque=False)
        nodes.append({'node': name, 'meshId': mesh_id, 'lod': int(lod), 'triangles': len(old['indices']),
                      'vertices': len(old['POSITION']), 'wholeBladeBodyCounts': dict(Counter(allocation)),
                      'unchangedEncodedAttributeHashes': {k: hashlib.sha256(old[k].tobytes()).hexdigest()
                                                          for k in old if k not in ('TANGENT', 'TEXCOORD_0')},
                      'uv0EncodedSha256': hashlib.sha256(new_uv.tobytes()).hexdigest(),
                      'tangentEncodedSha256': hashlib.sha256(new_tangent.tobytes()).hexdigest(),
                      'baselineContinuousMip0AlphaCertificate': alpha_cache[old_alpha_key],
                      'newContinuousMip0AlphaCertificateFromOpaqueBodyRectangles': True,
                      'tangentFrame': tangent_proof})
    validate_replacement_bytes(raw_bytes, new_bytes, ranges)
    OUT.mkdir()
    glb_path = OUT / 'lawn-leaf-strip-source-proposal.glb'
    with glb_path.open('xb') as stream:
        stream.write(new_bytes)
    saved_bytes, saved_doc, _, saved_rows = glb(glb_path)
    header_end = min(r['start'] for r in ranges)
    require(saved_doc == doc and saved_bytes[:header_end] == raw_bytes[:header_end], 'Source GLB document/header changed')
    validate_replacement_bytes(raw_bytes, saved_bytes, ranges)
    for name, original in old_rows.items():
        require(set(saved_rows[name]) == set(original) and all(saved_rows[name][key].tobytes() == original[key].tobytes()
                    for key in original if key not in ('TANGENT', 'TEXCOORD_0')), 'Saved proposal changed an original geometry attribute')
    lods, projections = [], []
    for mesh, allocation in sorted(assignments.items()):
        trio = [saved_rows[mesh + '_LOD' + str(i)] for i in range(3)]
        require(all(all(r[k].tobytes() == trio[0][k].tobytes() for k in trio[0]) for r in trio[1:]),
                'Actual three identical source LODs diverged')
        lods.append({'meshId': mesh, 'availableSourceLods': [0, 1, 2], 'all3AttributeAndIndexBytesIdentical': True,
                     'bodyByWholeBladeIndex': allocation})
        old_projection, new_projection = projection_masks(old_rows[mesh + '_LOD0'], alpha), projection_masks(trio[0], alpha)
        pairs = []
        for (old_record, old_geometry, old_alpha), (new_record, new_geometry, new_alpha) in zip(old_projection, new_projection):
            require(np.array_equal(old_geometry, new_geometry), 'Opaque geometric ground or side support changed')
            require(not np.any(old_alpha & ~new_alpha), 'New photographic mapping lost an original covered source-raster pixel')
            # Projectively collapsed faces can occupy touched pixels with no
            # interpolable area; retain that convention for both photo masks.
            pairs.append({'original': old_record, 'proposal': new_record,
                          'originalCoveredPixelsLost': int((old_alpha & ~new_alpha).sum()),
                          'proposalCoveredPixelsAdded': int((new_alpha & ~old_alpha).sum()),
                          'opaqueGeometricSupportByteExact': True,
                          'alphaMasksExactlyEqual': bool(np.array_equal(old_alpha, new_alpha))})
        projections.append({'meshId': mesh, 'availableSourceLodsCovered': [0, 1, 2], 'orthographicBeforeAfter': pairs,
                            'originalOpaqueGeometryExactlyEqual': True, 'originalAlphaCoveredPixelsRetained': True,
                            'newContinuousMip0AlphaCertificateUsed': True})
    counts = Counter()
    population_triangles = population_blades = 0
    for r in controls:
        mesh = r['sourceMeshId']
        for body, count in Counter(assignments[mesh]).items():
            counts[body] += count * r['instances']
        population_triangles += len(saved_rows[mesh + '_LOD0']['indices']) * r['instances']
        population_blades += len(assignments[mesh]) * r['instances']
    require(population_triangles == 18571200 and population_blades == 6190400, 'Original modeled lawn budget changed')
    write(OUT / 'photo-body-selection.json', {'schema': SCHEMA, 'sourceOriginalGlb': pin(ORIGINAL),
          'sourceOriginalNode': 'PH_grass_medium_02_a_LOD0', 'connectedComponents': components,
          'distinctConnectedGeometryComponents': 18, 'distinctUvBounds': 6, 'selectedDistinctPhotoBodies': bodies,
          'bodyRectanglesAreArtistInteriorCrops': True, 'sourcePixelsUnmodified': True})
    write(OUT / 'uv-tangent-preservation.json', {'schema': SCHEMA, 'nodes': nodes, 'lodEquivalence': lods,
          'modifiedAccessorRanges': ranges, 'only120Uv0AndTangentAccessorRangesChanged': True,
          'documentAndAllOtherBinaryBytesUnchanged': True, 'positionNormalColorUv1IndexRootLayoutExact': True,
          'sourceUvDerivedTangents': True, 'nativeNormalTangentNumericReadbackPerformed': False})
    write(OUT / 'source-projection-coverage.json', {'schema': SCHEMA, 'prototypeOrthographicChecks': projections,
          'all60SourceLodsOpaqueGeometryAndOriginalAlphaCoveredRasterPixelsPreserved': True,
          'allOriginalAlphaMasksUnchangedClaimed': False,
          'rasterConvention': '512-square prototype-specific frame; Pillow touched-pixel triangles; clamped pixel-centre barycentrics; bilinear original mip0 alpha; depth-free union',
          'continuousOriginalAlphaCoveredGeometryCannotDecrease': True,
          'continuousRetentionBasis': 'All unchanged source triangle points map within new fully opaque rectangle support; every originally alpha-passing point still passes.',
          'completePopulationGroundRasterReplayed': False, 'nativeMipsTsrAlphaOrOpticalCoverageVerified': False,
          'projectionRasterOnlyModelsSourceGeometry': True})
    write(OUT / 'managed-lawn-recorded-controls.json', {'schema': SCHEMA, 'sourceBasisNativeReport': pin(R38 / 'soft-ground-native-report-r2.json'),
          'exactSourceGroups': controls, 'recordedNativeGroups': 40, 'recordedNativeMembers': 102011,
          'sourcePopulationGroupsUnmodified': True, 'freshNativeRootsOrMatricesDecoded': False,
          'futureCurrentSavedMembershipMustBeValidatedBeforeAnyNativeChoice': True})
    source_copy = OUT / 'generator-source.py'
    source_copy.write_bytes(Path(__file__).read_bytes())
    plan = {'schema': SCHEMA, 'schemaVersion': 1, 'owner': OWNER, 'createdAt': datetime.now(timezone.utc).isoformat(),
            'status': 'source-only-original-photo-body-uv-proposal-native-and-image-selection-pending',
            'revision': 2, 'firstFailedSourceAttempt': pin(FAILURE),
            'inputFiles': inputs, 'generatorSource': pin(source_copy), 'sourceBasisNativeReport': pin(R38 / 'soft-ground-native-report-r2.json'),
            'futureSelectedNativeBase': None, 'futureRootImageDecision': None, 'futureProjectClone': None,
            'futureNativePlan': None, 'futureNativeReport': None, 'futureActualNativeProcessId': None,
            'sourceGeometryProposal': pin(glb_path), 'photoBodySelection': pin(OUT / 'photo-body-selection.json'),
            'uvTangentPreservation': pin(OUT / 'uv-tangent-preservation.json'),
            'projectionCoverage': pin(OUT / 'source-projection-coverage.json'),
            'recordedManagedLawnControls': pin(OUT / 'managed-lawn-recorded-controls.json'),
            'originalMaterialRecipe': recipe, 'recordedNativeMaterialGraphSha256': material['graphSha256'],
            'proposedWholeBladePhotoWeightsPercent': {b['id']: b['weight'] for b in BODIES},
            'actualModeledPopulationWholeBladePhotoCounts': dict(counts),
            'actualModeledPopulationWholeBladePhotoPercent': {k: 100 * v / population_blades for k, v in counts.items()},
            'budget': {'masters': 20, 'availableSourceLodNodes': 60, 'sourceTrianglesAll60Nodes': sum(n['triangles'] for n in nodes),
                       'sourceInstancedTrianglesEachLod': population_triangles, 'sourceWholeBlades': population_blades,
                       'sourceGroups': 40, 'sourceMembers': 102011, 'newTextures': 0, 'newMaterialGraphs': 0,
                       'geometryVertexTriangleOrPopulationIncrease': 0, 'runtimeTriangleCostMeasured': False},
            'preservation': {'geometryPositionNormalIndexColorUv1Exact': True, 'allRootsOrderHeightsScalesMasksUnchanged': True,
                             'materialResponseAndOriginalFourMapBytesUnchanged': True, 'onlyUv0AndDerivedTangentsAdapted': True,
                             'newWorldMacroVariationOrPopulationChange': False},
            'appearanceRisks': ['New UV crop can stretch fine photographic features; this is an authored crop choice.',
                                'Brighter green and a minority dry-body crop may still look uniform or overly bright in native light.',
                                'Native mip filtering, alpha coverage and normal-map response remain unobserved.',
                                'The dry-body crop is only8 original texels wide; coarse native mips may mix outside its body, and this is an unobserved risk rather than a native failure.',
                                'Original curved-strip alpha coverage is measured separately; new fully opaque source interiors can add alpha-covered pixels within unchanged geometry.',
                                'Existing high lawn density and near-identical heights are deliberately preserved; no wear or usage pattern is introduced.'],
            'activeDesign': {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'},
            'setbacksMm': {'street': 3000, 'east': 3000}, 'nativeExecuted': False, 'gpuExecuted': False,
            'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False,
            'shippingVerified': False, 'activeOutputPromoted': False}
    write(OUT / 'leaf-strip-source-plan.json', plan)
    for path, expected in inputs.items():
        require(sha(path) == expected, 'Frozen original changed during source study: ' + path)
    html = '<!doctype html><meta charset="utf-8"><title>R41 original leaf-body crops</title><style>body{background:#111;color:#eee;font:16px system-ui;margin:24px}figure{position:relative;width:min(90vw,900px);margin:0}img{width:100%;display:block}svg{position:absolute;inset:0;width:100%;height:100%}li{margin:.5em}</style><h1>R41 · original photographic body selection</h1><p>Source-only artist UV proposal. Original image pixels, geometry, density and material response stay unchanged. No native appearance acceptance.</p><figure><img src="' + os.path.relpath(original_map['path'], OUT) + '"><svg viewBox="0 0 2048 2048">'
    for body, color in zip(bodies, ('#28e3c9', '#4ec4ff', '#feef76', '#f59eff')):
        x0, y0, x1, y1 = body['rect']
        html += f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="none" stroke="{color}" stroke-width="4"/><text x="{max(8,x0-130)}" y="{max(30,y0-10)}" fill="{color}" font-size="25">{body["id"]}</text>'
    html += '</svg></figure><ul>' + ''.join(f'<li>{b["id"]}: source component {b["componentRoot"]}, {b["weight"]}% target whole-blade mix; exact original alpha support=65535.</li>' for b in bodies) + '</ul><p>These overlays mark authored UV crops on the unchanged original atlas. Actual before/after alpha masks are compared under a bounded source raster convention; opaque geometric support is exact, and existing alpha-covered pixels are retained. This is not native mip or visible coverage proof. The8px dry core has an unresolved coarse-mip risk.</p>'
    (OUT / 'original-photo-body-selection.html').write_text(html)
    print(json.dumps({'plan': pin(OUT / 'leaf-strip-source-plan.json'), 'bodies': len(bodies), 'budget': plan['budget'],
                      'nativeExecuted': False}), flush=True)


if __name__ == '__main__':
    build()
