"""Isolated source study: original tapered lawn + real PH body UVs.

Only TEXCOORD_0 and regenerated TANGENT bytes differ in the new GLB. The
original100-master library, geometry, old41 material graphs and all placements
remain immutable inputs. Coverage is measured with actual original alpha at
mip0 using the exact previous0.25mm Pillow triangle footprint convention.
No native process, GPU task, population change or photographic conversion.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-lawn-photo-variants.py'
OUT = ROOT / 'output/unreal/exterior-lawn-photo-variants-20261001-r3-study'
DONOR = ROOT / 'output/unreal/exterior-lawn-tapered-integration-20261001-r1c'
FOUR = ROOT / 'output/unreal/exterior-lawn-tapered-photo-uv-20261001-r1-study'
BASE = ROOT / 'output/unreal/exterior-assets-shape-20261001-r1'
MATERIAL = 'lawn_photographic_blade'
PHOTO_BODY_INSET_PIXELS = 1.0
PINS = {
    str(DONOR / 'lawn-natural.glb'): '4f99b430de0c7437dec8a30f4024eb419af8838ea25b8822bd7244c4ae30b2af',
    str(DONOR / 'lawn-natural-plan.json'): '0c13741cf2344ef809ac4427b4102a4917eefd508bc0b3c3746312029800c319',
    str(DONOR / 'geometry-manifest.json'): 'a86d0832d5ce554bcb2ccebcb0a3cc066e5937912183db513c0ffccba893f455',
    str(DONOR / 'lawn-natural-prototypes.json'): 'f356a5a2ff014d5faa4647ac16e610e9b8c751ed3057ba48d95369b99b88c7fd',
    str(DONOR / 'lawn-coverage-receipt.json'): 'a58daf34108c3af5dc3d955f90739c93b552629c6bcfd28de60630cc2653269b',
    str(DONOR / 'lawn-boundary-coverage-receipt.json'): '8030643bed70088bbbddba344f534a3825d170e2759540d24f107a2d4237bac0',
    str(FOUR / 'release.json'): 'd7edf268500379a48606fb55439cb43653debc995acb11014709bd53dfdc1b90',
    str(FOUR / 'closure.json'): '5b26b0d5c622102cd5d8cd8cab29e5eea5e667a2d7b60a42e35673bdf9d9180d',
    str(ROOT / 'scripts/unreal/exterior-lawn-tapered-photo-uv-study.py'): 'cc9e19d66d661160707b63a8f256a412351d3a025185f96be5d9e89050510dd2',
    str(BASE / 'geometry-manifest.json'): '23c9df25473bb966ec96a8c2170f8abb6a1d6ad1172e1a0552a5e472d8e104a9',
    str(BASE / 'material-manifest.json'): '42dbaddc637c479d30482b1524217d8e9c288ff89de8f64d9f38396a1e63fbbb',
    str(BASE / 'asset-manifest.json'): '695068542a1785d0fef991de6cf671f0a14b32095e50cda005cf0bc80c530927',
    str(ROOT / 'output/unreal/exterior-20261001-r12c/exterior-import-report.json'): '3a3824b05aff496a7df45cc033b88a64d3c3de73cf9c0c747bd88a21427904ee',
}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def pin(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def glb(path):
    raw = Path(path).read_bytes()
    require(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Invalid GLB header')
    size, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a, 'GLB JSON missing')
    doc = json.loads(raw[20:20 + size])
    byte_count, kind = struct.unpack_from('<II', raw, 20 + size)
    require(kind == 0x004e4942 and 28 + size + byte_count == len(raw), 'GLB binary missing')
    binary = bytearray(raw[28 + size:])

    def accessor(index):
        a = doc['accessors'][index]
        view = doc['bufferViews'][a['bufferView']]
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        dtype = {5126: '<f4', 5125: '<u4'}[a['componentType']]
        require('sparse' not in a and view.get('byteStride', width * 4) == width * 4,
                'Unexpected sparse/interleaved accessor')
        start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        array = np.frombuffer(binary, dtype, a['count'] * width, start).reshape(-1, width).copy()
        return array, start, array.nbytes

    rows = {}
    for node in doc['nodes']:
        primitive = doc['meshes'][node['mesh']]['primitives'][0]
        rows[node['name']] = {key: accessor(value)[0] for key, value in primitive['attributes'].items()}
        rows[node['name']]['indices'] = accessor(primitive['indices'])[0].reshape(-1, 3)
    return doc, binary, accessor, rows


def save_glb(path, doc, binary):
    source = json.dumps(doc, separators=(',', ':'), allow_nan=False).encode()
    source += b' ' * (-len(source) % 4)
    require(len(binary) % 4 == 0, 'Unexpected source buffer padding')
    with Path(path).open('xb') as stream:
        stream.write(struct.pack('<4sII', b'glTF', 2, 28 + len(source) + len(binary)))
        stream.write(struct.pack('<II', len(source), 0x4e4f534a))
        stream.write(source)
        stream.write(struct.pack('<II', len(binary), 0x004e4942))
        stream.write(binary)


def source_id(identity):
    require(identity.startswith('lawn_natural_'), 'Unexpected source lawn ID')
    return identity.replace('lawn_natural_', 'lawn_photo_', 1)


def rgba_alpha_sample(alpha, uv):
    """Existing source bilinear mip0 sample; no source map conversion."""
    p = np.clip(np.asarray(uv) * 2048 - .5, 0, 2047)
    lo = np.floor(p).astype(int)
    hi = np.minimum(lo + 1, 2047)
    f = p - lo
    return ((alpha[lo[:, 1], lo[:, 0]] * (1 - f[:, 0]) + alpha[lo[:, 1], hi[:, 0]] * f[:, 0]) * (1 - f[:, 1]) +
            (alpha[hi[:, 1], lo[:, 0]] * (1 - f[:, 0]) + alpha[hi[:, 1], hi[:, 0]] * f[:, 0]) * f[:, 1])


def alpha_footprint(records, placements, specification, alpha, boundary=False):
    """Reproduce sealed Pillow footprint, then sample actual alpha on it.

    The previous opaque raster includes edge pixels touched by a polygon. UV
    interpolation uses pixel centres; such conservative edge pixels are mapped
    to the convex triangle boundary by clamping/renormalizing barycentrics.
    Both the opaque and alpha metrics retain that exact original convention.
    This is not a claim about MSAA/TAA/native texture mips or distant opacity.
    """
    if boundary:
        origin = np.asarray(specification['originCm'])
        frame = np.column_stack([specification['inwardUnitXY'], specification['axisUnitXY']])
        pixel = .025
        width, height = specification['resolutionXY']
        nearby = []
        for row in placements:
            q = (np.asarray(row['positionCm'][:2]) - origin) @ frame
            r = row['radiusCm']
            if q[0] + r > 0 and q[0] - r < specification['widthCm'] and q[1] + r > 0 and q[1] - r < specification['lengthCm']:
                nearby.append(row)
    else:
        center = np.asarray(specification['centerCm'])
        origin = center - specification['sizeCm'] / 2
        frame = np.eye(2)
        pixel = specification['sizeCm'] / specification['resolution']
        width = height = specification['resolution']
        nearby = [row for row in placements if abs(row['positionCm'][0] - center[0]) < 50 + row['radiusCm']
                  and abs(row['positionCm'][1] - center[1]) < 50 + row['radiusCm']]
    opaque_image = Image.new('L', (width, height), 0)
    opaque_draw = ImageDraw.Draw(opaque_image)
    scratch = Image.new('L', (width, height), 0)
    scratch_draw = ImageDraw.Draw(scratch)
    previous_box = None
    photo = np.zeros((height, width), dtype=bool)
    stats = {'conservativeRasterEdgePixels': 0, 'evaluatedAlphaPixels': 0,
             'uvTriangleDegenerateProjectionSkipped': 0}
    for row_number, row in enumerate(nearby):
        record = records[row['meshId'] + '_LOD0']
        p = np.asarray(record['positionsCm'])[:, :2] * row['scale'][0]
        angle = math.radians(row['yawDeg'])
        c, s = math.cos(angle), math.sin(angle)
        p = ((p @ np.array([[c, s], [-s, c]]) + row['positionCm'][:2] - origin) @ frame / pixel)
        for face in record['triangles']:
            q = p[face]
            opaque_draw.polygon([tuple(point) for point in q], fill=255)
            lo = np.maximum(np.floor(q.min(0)).astype(int) - 1, [0, 0])
            hi = np.minimum(np.ceil(q.max(0)).astype(int) + 1, [width - 1, height - 1])
            if np.any(hi < lo):
                continue
            if previous_box is not None:
                scratch.paste(0, previous_box)
            box = (int(lo[0]), int(lo[1]), int(hi[0] + 1), int(hi[1] + 1))
            scratch_draw.polygon([tuple(point) for point in q], fill=255)
            local = scratch.crop(box)
            previous_box = box
            region = photo[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
            candidates = (np.asarray(local) > 0) & ~region
            yy, xx = np.nonzero(candidates)
            if not len(xx):
                continue
            denominator = ((q[1, 1] - q[2, 1]) * (q[0, 0] - q[2, 0]) +
                           (q[2, 0] - q[1, 0]) * (q[0, 1] - q[2, 1]))
            if abs(denominator) < 1e-12:
                stats['uvTriangleDegenerateProjectionSkipped'] += 1
                continue
            x, y = xx + lo[0] + .5, yy + lo[1] + .5
            a = ((q[1, 1] - q[2, 1]) * (x - q[2, 0]) + (q[2, 0] - q[1, 0]) * (y - q[2, 1])) / denominator
            b = ((q[2, 1] - q[0, 1]) * (x - q[2, 0]) + (q[0, 0] - q[2, 0]) * (y - q[2, 1])) / denominator
            bary = np.column_stack([a, b, 1 - a - b])
            stats['conservativeRasterEdgePixels'] += int((bary.min(1) < 0).sum())
            bary = np.maximum(bary, 0)
            bary /= bary.sum(1)[:, None]
            passed = rgba_alpha_sample(alpha, bary @ record['uv0'][face]) >= .333
            region[yy[passed], xx[passed]] = True
            stats['evaluatedAlphaPixels'] += len(xx)
        if row_number % 200 == 0:
            print(json.dumps({'coverageProgress': specification.get('boundaryId', specification.get('centerCm')),
                              'instances': row_number, 'total': len(nearby)}), flush=True)
    opaque = np.asarray(opaque_image) > 0
    require(not np.any(photo & ~opaque), 'Alpha footprint escaped opaque source geometry')
    return opaque, photo, len(nearby), stats


def interior_metrics(mask):
    fractions = mask.reshape(10, 400, 10, 400).mean(axis=(1, 3))
    return {'projectedCoverage': float(mask.mean()), 'tenCmBinCoverageMinimum': float(fractions.min()),
            'tenCmBinCoverageP10': float(np.quantile(fractions, .1)), 'bareTenCmBins': int((fractions < .20).sum())}


def boundary_metrics(mask):
    bands = [{'distanceFromBoundaryMm': [lo * 10, hi * 10],
              'physicalCoverFraction': float(mask[:, math.ceil(lo / .025):math.floor(hi / .025)].mean())}
             for lo, hi in ((.1, 1.), (1., 3.), (3., 10.))]
    return {'projectedCoverage': float(mask.mean()), 'boundaryBands': bands}


def build():
    require(not OUT.exists(), 'Use a fresh immutable output directory')
    inputs = dict(PINS)
    inputs[str(Path(__file__).resolve())] = sha(__file__)
    few = json.loads((FOUR / 'closure.json').read_text())
    prior_uv = json.loads(Path(few['derivedUvBodyFrom']['path']).read_text())
    inputs[few['derivedUvBodyFrom']['path']] = few['derivedUvBodyFrom']['sha256']
    inputs[prior_uv['sourceConnectedUVIsland']['glb']] = prior_uv['sourceConnectedUVIsland']['sha256']
    for path, expected in few['inputFiles'].items():
        if '/grass_medium_02/' in path or '/exterior-alpha-' in path or path.endswith('exterior-lawn-photo-uv-study.py'):
            inputs[path] = expected
    inputs[str(ROOT / 'scripts/unreal/exterior-alpha-dilate.py')] = few['originalPhotoRecipe']['albedoDerivation']['sourceGenerator']['sha256']
    source_plan = json.loads((DONOR / 'lawn-natural-plan.json').read_text())
    require(source_plan['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'Canonical source design differs')
    require(source_plan['housePlacement']['streetSetbackMm'] == 3000 and
            source_plan['housePlacement']['eastSetbackMm'] == 3000, 'Source setbacks differ')
    require(len(source_plan['lawnPlacements']) == 102011 and len(source_plan['groups']) == 40, 'Source population differs')
    source_library = json.loads((DONOR / 'geometry-manifest.json').read_text())
    base = json.loads((BASE / 'geometry-manifest.json').read_text())
    require(len(source_library['meshes']) == 20 and len(base['meshes']) == 100, 'Original source libraries differ')
    for row in base['meshes']:
        inputs[row['glbPath']] = row['glbSha256']
    for path, expected in inputs.items():
        require(sha(path) == expected, 'Initial source hash differs: ' + path)
    original_doc, original_binary, accessor, originals = glb(DONOR / 'lawn-natural.glb')
    require(len(originals) == 60, 'All original60 LOD nodes required')
    uv_function = load_module('frozen_four_leaf_tangent_frame', ROOT / 'scripts/unreal/exterior-lawn-tapered-photo-uv-study.py')
    source_proof = json.loads((DONOR / 'lawn-natural-prototypes.json').read_text())
    metadata = {row['nodeName']: row for row in source_proof}
    strip = np.asarray(prior_uv['leafUvMapping']['stripStations'])
    require(strip.shape == (257, 3), 'Approved photo body strip differs')
    stations = np.linspace(0, 1, 257)
    new_doc = deepcopy(original_doc)
    new_binary = bytearray(original_binary)
    changed_ranges = []
    node_proofs = []
    for old_node, new_node in zip(original_doc['nodes'], new_doc['nodes']):
        name = old_node['name']
        source = originals[name]
        meta = metadata[name]
        primitive = original_doc['meshes'][old_node['mesh']]['primitives'][0]
        require(len(source['POSITION']) == len(meta['bladeRanges']) * 5 and
                len(source['indices']) == len(meta['bladeRanges']) * 3,
                'Source five-vertex/three-triangle leaf topology differs')
        normalized = source['TEXCOORD_0'].astype(float)
        t = normalized[:, 1]
        low, high = np.interp(t, stations, strip[:, 1]), np.interp(t, stations, strip[:, 2])
        # The approved four-leaf strip originally extends half a texel outside
        # the source connected silhouette. Crop this bounded body one original
        # texel inward; source photograph/alpha/cutoff/geometry stay untouched.
        low += (.5 + PHOTO_BODY_INSET_PIXELS) / 2048
        high -= (.5 + PHOTO_BODY_INSET_PIXELS) / 2048
        require(np.all(high > low), 'Photo body crop collapsed the source leaf width')
        mapped = np.column_stack([.768 + (.352 - .768) * t,
                                  low + (high - low) * normalized[:, 0]]).astype('<f4')
        positions = source['POSITION'][:, [0, 2, 1]].astype(float) * 100
        normals = source['NORMAL'][:, [0, 2, 1]].astype(float)
        triangles = source['indices'][:, [0, 2, 1]].astype('int64')
        native_tangent, triangles_metrics = uv_function.tangent_frame(positions, normals, mapped.astype(float), triangles)
        gltf_tangent = native_tangent[:, [0, 2, 1, 3]].copy()
        gltf_tangent[:, 3] *= -1
        gltf_tangent = gltf_tangent.astype('<f4')
        require(np.isfinite(mapped).all() and np.isfinite(gltf_tangent).all() and
                np.max(np.abs(np.linalg.norm(gltf_tangent[:, :3], axis=1) - 1)) < 1e-6 and
                np.max(np.abs(np.sum(gltf_tangent[:, :3] * source['NORMAL'], axis=1))) < 1e-6,
                'Actual float32 UV/tangent frame invalid')
        for key, replacement in [('TEXCOORD_0', mapped), ('TANGENT', gltf_tangent)]:
            _, offset, size = accessor(primitive['attributes'][key])
            require(replacement.nbytes == size, 'Source UV/tangent buffer length differs')
            new_binary[offset:offset + size] = replacement.tobytes()
            changed_ranges.append([offset, offset + size, key, name])
        new_node['name'] = source_id(name)
        new_doc['meshes'][old_node['mesh']]['name'] = source_id(name)
        raw_attributes = {key: hashlib.sha256(value.tobytes()).hexdigest()
                          for key, value in source.items() if key not in ('TANGENT', 'TEXCOORD_0')}
        node_proofs.append({'sourceNode': name, 'photoNode': source_id(name),
                            'vertices': len(source['POSITION']), 'triangles': len(source['indices']),
                            'blades': len(meta['bladeRanges']), 'unchangedAttributeEncodedHashes': raw_attributes,
                            'minimumUvTriangleArea': min(row['uvArea'] for row in triangles_metrics),
                            'maximumFloat32TangentUnitError': float(np.max(np.abs(np.linalg.norm(gltf_tangent[:, :3], axis=1) - 1))),
                            'maximumFloat32TangentNormalDot': float(np.max(np.abs(np.sum(gltf_tangent[:, :3] * source['NORMAL'], axis=1)))),
                            'uv0Range': [mapped.min(0).tolist(), mapped.max(0).tolist()]})
    changed = np.zeros(len(new_binary), dtype=bool)
    for start, stop, key, name in changed_ranges:
        require(not changed[start:stop].any(), 'Unexpected shared UV/tangent accessor')
        changed[start:stop] = True
    before_bytes, after_bytes = np.frombuffer(original_binary, 'uint8'), np.frombuffer(new_binary, 'uint8')
    require(np.array_equal(before_bytes[~changed], after_bytes[~changed]), 'Non-UV/tangent geometry bytes changed')
    require(new_doc['materials'] == original_doc['materials'], 'Original embedded material definitions changed')
    new_doc['asset']['generator'] = OWNER + '; original source: ' + original_doc['asset'].get('generator', '')
    OUT.mkdir()
    original_dir = OUT / 'original-source'
    original_dir.mkdir()
    for path in sorted(set([DONOR / 'lawn-natural.glb', DONOR / 'geometry-manifest.json', DONOR / 'lawn-natural-plan.json',
                            DONOR / 'lawn-natural-prototypes.json', DONOR / 'lawn-coverage-receipt.json',
                            DONOR / 'lawn-boundary-coverage-receipt.json', BASE / 'geometry-manifest.json',
                            BASE / 'material-manifest.json', BASE / 'asset-manifest.json'])):
        name = ('base100-' if path.parent == BASE else 'tapered-') + path.name
        with (original_dir / name).open('xb') as stream:
            stream.write(path.read_bytes())
        require(sha(original_dir / name) == sha(path), 'Independent original source copy differs')
    with (OUT / 'source.py').open('x') as stream:
        stream.write(Path(__file__).read_text())
    save_glb(OUT / 'lawn-photographic-variants.glb', new_doc, new_binary)
    saved_doc, saved_binary, _, saved_rows = glb(OUT / 'lawn-photographic-variants.glb')
    records = {}
    all_lod_equivalence = []
    for row in source_library['meshes']:
        identity = row['id']
        pair = []
        for lod in range(3):
            old_name, new_name = identity + '_LOD' + str(lod), source_id(identity) + '_LOD' + str(lod)
            old, new = originals[old_name], saved_rows[new_name]
            for key in ('POSITION', 'NORMAL', 'COLOR_0', 'TEXCOORD_1', 'indices'):
                require(new[key].tobytes() == old[key].tobytes(), 'Actual saved source geometry bytes differ: ' + old_name + '/' + key)
            points_cm = (new['POSITION'][:, [0, 2, 1]] * 100).astype(float)
            require({'min': points_cm.min(0).tolist(), 'max': points_cm.max(0).tolist()} == row['lods'][lod]['expectedBoundsCm'],
                    'Actual native saved bounds differ: ' + old_name)
            records[old_name] = {'positionsCm': points_cm, 'triangles': new['indices'][:, [0, 2, 1]].astype('int64'),
                                 'uv0': new['TEXCOORD_0'].astype(float), 'normals': new['NORMAL'][:, [0, 2, 1]].astype(float),
                                 'colors': new['COLOR_0'].astype(float)}
            pair.append(new)
        require(all(all(pair[lod][key].tobytes() == pair[0][key].tobytes() for key in pair[0]) for lod in (1, 2)),
                'Saved photo geometry/UV/tangent attributes differ across identical original LODs')
        all_lod_equivalence.append({'sourceMeshId': identity, 'photoMeshId': source_id(identity),
                                    'all3LodAttributesAndIndexBytesIdentical': True})
    require(np.array_equal(np.frombuffer(saved_binary, 'uint8')[~changed], before_bytes[~changed]),
            'Saved source geometry binary differs outside UV/tangent ranges')
    geometry_proof = {'schemaVersion': 1, 'status': 'VERIFIED_ORIGINAL_TAPERED_GEOMETRY_BYTES_ONLY_UV0_TANGENT_CHANGED',
                      'nodes': node_proofs, 'meshes': 20, 'lods': 60, 'allLodEquivalence': all_lod_equivalence,
                      'allPositionNormalColorUv1IndicesAndBoundsExact': True, 'allSourceLeafRootLayoutPreserved': True,
                      'embeddedOriginalMaterialDefinitionsUnchanged': True,
                      'only120Uv0AndTangentAccessorRangesModified': True, 'changedBufferRanges': changed_ranges,
                      'photographicUvMapping': {'sourceBodyRelease': pin(FOUR / 'release.json'),
                                               'sourceConnectedUvIsland': prior_uv['sourceConnectedUVIsland'],
                                               'sourceBodyAxisU': [.768, .352], 'sourceStripStations': strip.tolist(),
                                               'sourceSilhouetteInwardCropPixels': PHOTO_BODY_INSET_PIXELS,
                                               'shiftFromPreviousHalfTexelOuterMarginPixels': .5 + PHOTO_BODY_INSET_PIXELS,
                                               'sourceTextureDimensions': [2048, 2048], 'sourcePhotoAndAlphaPixelsUnmodified': True,
                                               'artistUvCropOnlyNoBotanicalOrSurveyClaim': True},
                      'nativeJobsRun': 0, 'nativeShaderAccepted': False, 'fullPhotorealismAccepted': False}
    write(OUT / 'geometry-uv-tangent-proof.json', geometry_proof)
    original_coverage = json.loads((DONOR / 'lawn-coverage-receipt.json').read_text())
    original_boundary = json.loads((DONOR / 'lawn-boundary-coverage-receipt.json').read_text())
    recipe = deepcopy(few['originalPhotoRecipe'])
    current = json.loads(Path(next(p for p in inputs if p.endswith('exterior-20261001-r12c/exterior-import-report.json'))).read_text())
    require(current['materials']['materials']['ph_grass_medium_02']['recipe'] == recipe, 'Actual current PH recipe differs')
    alpha = np.asarray(Image.open(recipe['maps']['alpha']['path']), dtype=float) / 65535
    require(alpha.shape == (2048, 2048), 'Original source alpha dimensions differ')
    physical, edges = [], []
    atlas = Image.new('RGB', (1380, 4 * 350), '#eeebe3')
    draw = ImageDraw.Draw(atlas)
    for index, specification in enumerate(original_coverage['windows']):
        opaque, photo, instance_count, stats = alpha_footprint(records, source_plan['lawnPlacements'], specification, alpha)
        old = interior_metrics(opaque)
        baseline = {key: value for key, value in specification['lods'][0].items() if key not in ('lod', 'studyTargetsMet')}
        require(old == baseline and instance_count == specification['instancesIntersectingWindow'], 'Opaque raster no longer exactly reproduces a58')
        measured = interior_metrics(photo)
        targets = measured['projectedCoverage'] >= .75 and measured['tenCmBinCoverageP10'] >= .55 and measured['bareTenCmBins'] == 0
        physical.append({**{k: v for k, v in specification.items() if k != 'lods'}, 'opaqueSourceMetrics': old,
                         'lods': [{'lod': lod, **measured, 'studyTargetsMet': targets} for lod in range(3)],
                         'alphaLostCoverageAbsolute': old['projectedCoverage'] - measured['projectedCoverage'],
                         'alphaRasterStatistics': stats})
        for column, (name, mask) in enumerate([('Original geometry', opaque), ('Photo + alpha', photo), ('Alpha loss pixels', opaque & ~photo)]):
            image = np.empty((*mask.shape, 3), dtype='uint8')
            image[:] = [216, 222, 200]
            image[mask] = [49, 83, 35] if column < 2 else [200, 106, 40]
            atlas.paste(Image.fromarray(image).resize((320, 320), Image.Resampling.BOX), (column * 460 + 15, index * 350 + 25))
            draw.text((column * 460 + 15, index * 350 + 5), f'ROI{index+1} {name}: {float(mask.mean()):.4%}', fill='#202820')
        print(json.dumps({'completedInterior': index + 1, 'original': old, 'photo': measured, 'targetsMet': targets}), flush=True)
    atlas.save(OUT / 'physical-coverage-source-comparison.png')
    edge_atlas = Image.new('RGB', (1380, 900), '#eeebe3')
    edge_draw = ImageDraw.Draw(edge_atlas)
    for index, specification in enumerate(original_boundary['windows']):
        opaque, photo, instance_count, stats = alpha_footprint(records, source_plan['lawnPlacements'], specification, alpha, True)
        old = boundary_metrics(opaque)
        baseline = {key: value for key, value in specification['lods'][0].items() if key not in ('lod', 'studyTargetsMet')}
        require(old == baseline and instance_count == specification['intersectingInstances'], 'Opaque edge raster no longer exactly reproduces803')
        measured = boundary_metrics(photo)
        targets = all(row['physicalCoverFraction'] > gate for row, gate in zip(measured['boundaryBands'], (.12, .40, .50)))
        edges.append({**{k: v for k, v in specification.items() if k != 'lods'}, 'opaqueSourceMetrics': old,
                      'lods': [{'lod': lod, **measured, 'studyTargetsMet': targets} for lod in range(3)],
                      'alphaLostCoverageAbsolute': old['projectedCoverage'] - measured['projectedCoverage'],
                      'alphaRasterStatistics': stats})
        # Show the first10cm band across the exact full source edge length.
        for column, (name, mask) in enumerate([('Original', opaque), ('Photo + alpha', photo), ('Loss', opaque & ~photo)]):
            image = np.empty((mask.shape[0], 400, 3), dtype='uint8')
            image[:] = [216, 222, 200]
            image[mask[:, :400]] = [49, 83, 35] if column < 2 else [200, 106, 40]
            edge_atlas.paste(Image.fromarray(image).resize((200, 400), Image.Resampling.BOX), (column * 460 + 100, index * 450 + 30))
            edge_draw.text((column * 460 + 15, index * 450 + 10), f'{specification["boundaryId"]} {name}, source first10cm', fill='#202820')
        print(json.dumps({'completedBoundary': specification['boundaryId'], 'photo': measured, 'targetsMet': targets}), flush=True)
    edge_atlas.save(OUT / 'boundary-coverage-source-comparison.png')
    passed = all(lod['studyTargetsMet'] for window in physical + edges for lod in window['lods'])
    coverage = {'schemaVersion': 1, 'status': 'PASS_SOURCE_PHOTOGRAPHIC_ALPHA_COVERAGE_NATIVE_PENDING' if passed else 'FAILED_SOURCE_PHOTOGRAPHIC_ALPHA_COVERAGE',
                'sourceCoverage': pin(DONOR / 'lawn-coverage-receipt.json'), 'sourceBoundaryCoverage': pin(DONOR / 'lawn-boundary-coverage-receipt.json'),
                'opaqueBaselineReproducedExactly': True, 'physicalCoverage': {'criteria': original_coverage['criteria'], 'windows': physical},
                'boundaryCoverage': {'criteria': original_boundary['criteria'], 'windows': edges},
                'pixelSizeMm': .25, 'alphaClipValue': .333, 'sourceAlpha': recipe['maps']['alpha'],
                'sourceAlphaPixelsUnmodified': True, 'alphaSampling': 'Original2048 16bit grayscale, normalized pixel centres, bilinear mip0 directV.',
                'edgeConvention': 'Exact original Pillow conservative polygon fill. Pixel centres outside geometric triangle are clamped and renormalized into convex barycentric coordinates; recorded separately.',
                'all3LodGeometryUvAndTangentByteEqualityVerified': True, 'uniqueGeometryRasterRuns': 6,
                'sameRasterCopiedToOtherLodsOnlyAfterExactByteEquality': True,
                'allTargetsMet': passed, 'noDensityRootsGeometryOrSourceDomainChanges': True,
                'nativeJobsRun': 0, 'nativeVisualAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False}
    write(OUT / 'photographic-alpha-coverage-receipt.json', coverage)
    variant_library = deepcopy(source_library)
    variant_library.update(owner=OWNER, generatorSha256=sha(__file__), inputFiles=inputs,
                           status='SOURCE_ONLY_PHOTOGRAPHIC_UV_VARIANTS_NATIVE_PENDING',
                           geometryProof=pin(OUT / 'geometry-uv-tangent-proof.json'),
                           photographicAlphaCoverage=pin(OUT / 'photographic-alpha-coverage-receipt.json'))
    bindings = []
    for row in variant_library['meshes']:
        identity = row['id']
        row.update(id=source_id(identity), sourceMeshId=identity, materialKeys=[MATERIAL],
                   glbPath=str(OUT / 'lawn-photographic-variants.glb'), glbSha256=sha(OUT / 'lawn-photographic-variants.glb'))
        for lod in row['lods']:
            lod['nodeName'] = source_id(lod['nodeName'])
        bindings.append({'sourceMeshId': identity, 'meshId': row['id'], 'materialKey': MATERIAL})
    write(OUT / 'geometry-manifest.json', variant_library)
    write(OUT / 'material-manifest.json', {MATERIAL: recipe})
    texture_metadata = {key: value for key, value in current['materials']['textures'].items()
                        if value['sourceSha256'] in [record['sha256'] for record in recipe['maps'].values()]}
    native_input_study = {'schemaVersion': 1, 'sourceNativeReport': pin(Path(next(p for p in inputs if p.endswith('exterior-20261001-r12c/exterior-import-report.json')))),
                          'currentPhotographicRecipe': recipe, 'currentPhotographicGraphSha256': current['materials']['materials']['ph_grass_medium_02']['graphSha256'],
                          'existingSourceNativeTextureMetadata': texture_metadata,
                          'existingAlbedoPngHeader': {'bitDepth': Path(recipe['maps']['albedo']['path']).read_bytes()[24],
                                                    'colorType': Path(recipe['maps']['albedo']['path']).read_bytes()[25]},
                          'originalAlphaPngHeader': {'bitDepth': Path(recipe['maps']['alpha']['path']).read_bytes()[24],
                                                    'colorType': Path(recipe['maps']['alpha']['path']).read_bytes()[25]},
                          'knownInterpretation': 'Existing derived8bit RGB sRGB albedo, native saved sourceEncodingReadbackTSE_NONE; original16bit linear alpha. NormalDX/roughness stay existing linear roles.',
                          'nativeGraphContract': {'sourceNormalsPreservedByImporter': True, 'nativeTangentsRecomputedByCurrentImporter': True,
                                                  'sourceTangentTransportDoesNotImplyExactSavedNativeTangents': True,
                                                  'photographicShaderIgnoresPreservedColor0': True,
                                                  'currentPhotographicVariationUsesPerInstanceRandom': True,
                                                  'nativeAlphaMipCoverageThreshold': .333, 'nativeAutomaticViewMipBias': True,
                                                  'intendedMaterialRebind': 'External manifest binds lawn_photographic_blade; embedded source GLB material stays lawn_natural_blade.'},
                          'unknowns': ['No GPU RGB/alpha sampling of this source in this study; original saved report generic verification is separate inherited evidence.',
                                       'Source mip0 coverage does not prove native compression, generated alpha mips, TAA or distance fade coverage.',
                                       'Regenerated tangent frames are independently testable geometry evidence; normalDX shading, roughness and SSS appearance remain native unknowns.',
                                       'One source body repeated through all prototypes may expose repetition; no new phase/island arrays or species/scanner claim.'],
                          'original41GraphsUnchangedByThisStudy': True, 'nativeJobsRun': 0}
    write(OUT / 'source-photographic-native-metadata-study.json', native_input_study)
    proposal = {'schemaVersion': 1, 'kind': 'source-only-photographic-tapered-lawn-variants', 'owner': OWNER,
                'generatorSha256': sha(__file__), 'activeDesign': source_plan['activeDesign'], 'housePlacement': source_plan['housePlacement'],
                'sourceSceneSha256': source_plan['sourceSceneSha256'], 'sourceObjSha256': source_plan['sourceObjSha256'],
                'sourcePlacementPlan': pin(DONOR / 'lawn-natural-plan.json'), 'sourceOriginal100Library': pin(BASE / 'geometry-manifest.json'),
                'inputFiles': inputs, 'geometryManifest': pin(OUT / 'geometry-manifest.json'), 'materialManifest': pin(OUT / 'material-manifest.json'),
                'prototypeBindings': bindings, 'placements': 102011, 'groups': 40, 'allPopulationTriangleBudgets': [18571200] * 3,
                'photographicAlphaCoverage': pin(OUT / 'photographic-alpha-coverage-receipt.json'),
                'sourceOnlyCoverageReady': passed, 'allSourceGeometryAndPlacementsUnchanged': True,
                'old100MastersAnd41GraphsPreserved': True, 'requiresIndependentReviewAndExplicitNativeIntegration': True,
                'requiresNarrowSourceDerivationAlias': 'New key lawn_photographic_blade must explicitly alias exact existing ph_grass_medium_02 receipt and four map hashes; immutable original receipt must remain unchanged.',
                'populationIntegrationContract': 'Keep original100 masters, add20 photographic variants. Replace40 active lawn group meshIds only; never append a second102011-instance lawn population.',
                'noNativeIntegrationPerformed': True, 'nativeVisualAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False}
    write(OUT / 'lawn-photographic-proposal.json', proposal)
    for path, expected in inputs.items():
        require(sha(path) == expected, 'Source changed during study: ' + path)
    write(OUT / 'closure.json', {'schemaVersion': 1, 'owner': OWNER, 'status': 'FROZEN_SOURCE_ONLY_PHOTOGRAPHIC_LAWN_VARIANTS_COVERAGE_READY' if passed else 'FROZEN_SOURCE_ONLY_PHOTOGRAPHIC_LAWN_VARIANTS_COVERAGE_FAILED',
                                'inputFiles': inputs, 'outputFiles': {str(path): sha(path) for path in sorted(OUT.rglob('*')) if path.is_file()},
                                'allInputsUnchangedBeforeAndAfter': True, 'sourceOnlyCoverageReady': passed,
                                'proposedMaterialKey': MATERIAL, 'meshes': 20, 'lods': 60, 'sourcePlacements': 102011,
                                'onlyUv0AndTangentsChanged': True, 'noProviderPixelsChanged': True,
                                'unitTestsRun': 0, 'nativeJobsRun': 0, 'nativeVisualAccepted': False,
                                'fullPhotorealismAccepted': False, 'performanceAccepted': False})
    print(json.dumps({'closure': pin(OUT / 'closure.json'), 'coverage': pin(OUT / 'photographic-alpha-coverage-receipt.json'),
                      'sourceOnlyCoverageReady': passed, 'geometry': pin(OUT / 'geometry-manifest.json')}), flush=True)


if __name__ == '__main__':
    build()
