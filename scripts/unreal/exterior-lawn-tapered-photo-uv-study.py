"""Photo-only, four-leaf CPU study on byte-preserved R11 tapered geometry.

No population plan, native shader, GPU task, image conversion or scene change.
The existing PH connected UV body is transported to the original five-vertex
leaves. Only UV0 and its tangent frame change; original root layout is retained.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/unreal/exterior-lawn-tapered-photo-uv-20261001-r1-study'
DONOR = ROOT / 'output/unreal/exterior-lawn-tapered-integration-20261001-r1c'
PRIOR = ROOT / 'output/unreal/exterior-lawn-photo-uv-20261001-r2-study/closure.json'
MODULE = ROOT / 'scripts/unreal/exterior-lawn-photo-uv-study.py'
NODE = 'lawn_natural_0_3_LOD0'
LEAVES = (1, 5, 9, 13)
PINS = {
    str(PRIOR): '0f8d979480f24bbbe6524a88a27faa83f5d454b65da3b9effc13b5bb9b4343d3',
    str(MODULE): 'e313373d21c8a49b80a878dade66649c6c6809f1d543b9128ca69e1ba9053850',
    str(DONOR / 'lawn-natural.glb'): '4f99b430de0c7437dec8a30f4024eb419af8838ea25b8822bd7244c4ae30b2af',
    str(DONOR / 'geometry-manifest.json'): 'a86d0832d5ce554bcb2ccebcb0a3cc066e5937912183db513c0ffccba893f455',
    str(DONOR / 'material-manifest.json'): '3612be84eb2f702807ea8b75bd061c71c3bdebd0dace940c8aea4b5cca162d56',
    str(DONOR / 'lawn-natural-prototypes.json'): 'f356a5a2ff014d5faa4647ac16e610e9b8c751ed3057ba48d95369b99b88c7fd',
    str(ROOT / 'output/unreal/exterior-20261001-r11/exterior-import-report.json'): '6608bfdada21b9de8540dfead615a668a60cd1a2ff6cceab6c8c0eded0cd5e21',
    str(ROOT / 'scripts/unreal/exterior-materials.py'): 'b661d9d6a05684b6f72afc61b16826b739f80cead3c5314f891a21c9329be720',
    str(ROOT / 'scripts/unreal/exterior-neighborhood-transition-materials.py'): '662614c68dd958fb1f54982691f26b434c1f0af625c5cae5068cb9a247ef6cdd',
    str(ROOT / 'scripts/unreal/test_exterior_neighborhood_transition_materials.py'): 'f1641308a1be15a040cfa3f759730e02544a0183db46d820bf2b561f1d8b826d',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise RuntimeError(message)


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def tangent_frame(p, source_normals, uv, ix):
    """Area-weighted UV derivatives, Gram-Schmidt and signed bitangent.

    Normals are read-only. Their unit-normal copy is used for projection so the
    source float32 normal bytes can be retained without silently normalizing them.
    """
    normals = source_normals / np.linalg.norm(source_normals, axis=1)[:, None]
    tangents = np.zeros_like(p)
    bitangents = np.zeros_like(p)
    face_metrics = []
    for face in ix:
        e1, e2 = p[face[1]] - p[face[0]], p[face[2]] - p[face[0]]
        du1, du2 = uv[face[1]] - uv[face[0]], uv[face[2]] - uv[face[0]]
        det = float(du1[0] * du2[1] - du1[1] * du2[0])
        area = float(np.linalg.norm(np.cross(e1, e2)) / 2)
        require(abs(det) > 1e-12 and area > 1e-8, 'Degenerate UV/geometry triangle')
        t = (e1 * du2[1] - e2 * du1[1]) / det
        b = (-e1 * du2[0] + e2 * du1[0]) / det
        tangents[face] += t * area
        bitangents[face] += b * area
        face_metrics.append({'indices': face.tolist(), 'uvDeterminant': det,
                             'areaCm2': area, 'uvArea': abs(det) / 2,
                             'dPositionDuCm': t.tolist(), 'dPositionDvCm': b.tolist()})
    tangents -= normals * np.sum(normals * tangents, axis=1)[:, None]
    lengths = np.linalg.norm(tangents, axis=1)
    require(np.all(lengths > 1e-10), 'Undefined transported tangent')
    tangents /= lengths[:, None]
    signs = np.sign(np.sum(np.cross(normals, tangents) * bitangents, axis=1))
    require(np.all(np.abs(signs) == 1), 'Undefined tangent handedness')
    result = np.column_stack([tangents, signs])
    require(np.isfinite(result).all(), 'Non-finite transported tangent')
    return result, face_metrics


def build():
    require(not OUT.exists(), 'Use a fresh immutable study directory')
    inputs = dict(PINS)
    inputs[str(Path(__file__).resolve())] = sha(__file__)
    for path, expected in inputs.items():
        require(sha(path) == expected, 'Initial source pin differs: ' + path)
    prior = json.loads(PRIOR.read_text())
    renderer = Path(prior['renderSource']['path'])
    inputs[str(renderer)] = prior['renderSource']['sha256']
    island = prior['sourceConnectedUVIsland']
    inputs[island['glb']] = island['sha256']
    recipe = prior['sourceRecipe']
    for record in recipe['maps'].values():
        inputs[record['path']] = record['sha256']
    for record in prior['sourceMapsProviderProof'].values():
        inputs[record['path']] = record['sha256']
    inputs[recipe['albedoDerivation']['sourceGenerator']['path']] = recipe['albedoDerivation']['sourceGenerator']['sha256']
    ph = ROOT / 'output/unreal/exterior-assets-20260926-r1/grass_medium_02'
    inputs[str(ph / 'info.json')] = '52cef91e7823b20df8ec8c7ff015f3c0717820652c9790e72914136b63816dd2'
    inputs[str(ph / 'files-api.json')] = '3e5e5b4b2ca39ac40a7acf9171a92557b819476adc4c1a3680d31b0b99a3b3af'
    for path, expected in inputs.items():
        require(sha(path) == expected, 'Source pin differs: ' + path)
    spec = importlib.util.spec_from_file_location('immutable_photo_uv_cpu_functions', MODULE)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    source = old.decode(DONOR / 'lawn-natural.glb')[NODE]
    require(len(source['POSITION']) == 320 and len(source['indices']) == 192,
            'Selected frozen R11 master is not 64 five-vertex/three-triangle leaves')
    prototypes = json.loads((DONOR / 'lawn-natural-prototypes.json').read_text())
    meta = next(row for row in prototypes if row['nodeName'] == NODE)
    artist = json.loads((DONOR / 'material-manifest.json').read_text())['lawn_natural_blade']
    require(artist['kind'] == 'authored-foliage' and artist['maps'] == {}
            and artist['linearColor'] == [.04, .075, .025], 'Original authored response differs')
    r11 = json.loads(Path(next(p for p in PINS if p.endswith('exterior-import-report.json'))).read_text())
    native_artist = r11['materials']['materials']['lawn_natural_blade']['recipe']
    require(native_artist == {**artist, 'tint': [1., 1., 1.]},
            'Source authored recipe differs beyond the finalized identity tint')
    artist = native_artist
    require(r11['materials']['materials']['ph_grass_medium_02']['recipe'] == recipe,
            'Photo recipe is not the actual unchanged R11 PH recipe')
    ids, face_ids, selected_meta = [], [], []
    for leaf in LEAVES:
        row = meta['bladeRanges'][leaf]
        require(row['bladeIndex'] == leaf and row['vertexCount'] == 5 and row['triangleCount'] == 3,
                'Unexpected source leaf topology')
        ids.extend(range(row['vertexOffset'], row['vertexOffset'] + 5))
        face_ids.extend(range(row['triangleOffset'], row['triangleOffset'] + 3))
        selected_meta.append(row)
    ids, face_ids = np.asarray(ids), np.asarray(face_ids)
    raw = {key: values[ids].copy() for key, values in source.items() if key != 'indices'}
    original_faces = source['indices'][face_ids].copy()
    inverse = {int(value): index for index, value in enumerate(ids)}
    local_faces = np.asarray([[inverse[int(v)] for v in f] for f in original_faces], dtype='int64')
    p = raw['POSITION'][:, [0, 2, 1]].astype(float) * 100
    n = raw['NORMAL'][:, [0, 2, 1]].astype(float)
    ix = local_faces[:, [0, 2, 1]]
    normalized = raw['TEXCOORD_0'].astype(float)
    strip = np.asarray(prior['leafUvMapping']['stripStations'], dtype=float)
    stations = np.linspace(0, 1, 257)
    require(strip.shape == (257, 3) and strip[0, 0] == .768 and strip[-1, 0] == .352,
            'Approved photographed body axis differs')
    t = normalized[:, 1]
    low, high = np.interp(t, stations, strip[:, 1]), np.interp(t, stations, strip[:, 2])
    uv = np.column_stack([.768 + (.352 - .768) * t, low + (high - low) * normalized[:, 0]])
    tangents, triangle_metrics = tangent_frame(p, n, uv, ix)
    old_t = raw['TANGENT'][:, [0, 2, 1]].astype(float)
    old_t /= np.linalg.norm(old_t, axis=1)[:, None]
    rotation = np.degrees(np.arccos(np.clip(np.sum(old_t * tangents[:, :3], axis=1), -1, 1)))
    texture = np.asarray(Image.open(recipe['maps']['albedo']['path']), dtype=float) / 255
    alpha = np.asarray(Image.open(recipe['maps']['alpha']['path']), dtype=float) / 65535
    require(texture.shape == (2048, 2048, 3) and alpha.shape == (2048, 2048), 'Exact existing atlas dimensions differ')
    files = json.loads((ph / 'files-api.json').read_text())
    for role, record in prior['sourceMapsProviderProof'].items():
        actual = Path(record['path']).read_bytes()
        provider = files[role]['2k']['png']
        require(len(actual) == provider['size'] and hashlib.md5(actual).hexdigest() == provider['md5'],
                'Official original provider pixels differ')
    ph_rows = old.decode(Path(island['glb']))
    ph_row = ph_rows[island['node']]
    faces = old.components(ph_row)[island['componentRootVertex']]
    require(np.array_equal(faces, np.asarray(island['originalTriangles'])), 'Original connected PH island topology differs')
    domain = unary_union([Polygon(ph_row['TEXCOORD_0'][f]) for f in faces])
    barycentric = np.asarray([[i, j, 64 - i - j] for i in range(1, 64)
                             for j in range(1, 64 - i)], dtype=float) / 64
    samples, rgb, weights, island_inside = [], [], [], []
    for face, metrics in zip(ix, triangle_metrics):
        points = barycentric @ uv[face]
        samples.extend(old.sample(alpha, points))
        rgb.extend(old.sample(texture, points))
        weights.extend(np.full(len(points), metrics['areaCm2'] / len(points)))
        island_inside.extend(domain.covers(Point(point)) for point in points)
    samples, rgb, weights = np.asarray(samples), np.asarray(rgb), np.asarray(weights)
    opaque = samples > .99
    require(opaque.any(), 'No reliable original photographic colour samples')
    photolinear = old.srgb_to_linear(rgb) * recipe['albedoScale']
    mean = np.average(photolinear[opaque], axis=0, weights=weights[opaque])
    # Reuse the exact previous fitted renderer. One authored-control line changes
    # to include the actual R11 VertexColor*linearColor response, not solid RGB.
    render_code = renderer.read_text()
    prior_control = 'else:albedo=np.broadcast_to(np.array([.04,.075,.025]),weights.shape)'
    current_control = "else:albedo=(weights@row['colors'][face][:,:3])*np.asarray(artist_recipe['linearColor'])"
    require(render_code.count(prior_control) == 1, 'Frozen CPU control implementation differs')
    render_code = render_code.replace(prior_control, current_control)
    render_code = render_code.replace('Identical actual camber vertices/light in all panels;', 'Identical original R11 tapered vertices/light in all panels;')
    namespace = dict(old.__dict__)
    namespace['artist_recipe'] = artist
    exec(compile(render_code, '<r11-tapered-photo-only-cpu>', 'exec'), namespace)
    few = {'p': p, 'n': n, 'ix': ix, 'colors': raw['COLOR_0'].astype(float)}
    # In-memory checks occur before any new output is created.
    for key in ('POSITION', 'NORMAL', 'COLOR_0', 'TEXCOORD_1'):
        require(np.array_equal(raw[key], source[key][ids]), 'Source attribute changed: ' + key)
    require(np.array_equal(ids[local_faces], original_faces), 'Index connectivity changed')
    require(np.max(np.abs(np.sum(tangents[:, :3] * n, axis=1))) < 1e-12, 'Transported tangent not orthogonal')
    require(np.max(np.abs(np.linalg.norm(tangents[:, :3], axis=1) - 1)) < 1e-12, 'Transported tangent not unit length')
    OUT.mkdir()
    with (OUT / 'renderer.py').open('x') as stream:
        stream.write(render_code)
    with (OUT / 'source.py').open('x') as stream:
        stream.write(Path(__file__).read_text())
    plate = Image.new('RGB', (1980, 760), '#eeebe3')
    draw = ImageDraw.Draw(plate)
    stats = {}
    for col, (label, mode) in enumerate([
            ('Actual R11 vertex RGB gradient / original tapered shape', 'solid'),
            ('Uniform area-matched PH mean / same original shape', 'photo_mean'),
            ('Existing PH leaf colour + original alpha / same shape', 'photo')]):
        image, stats[mode] = namespace['render'](few, uv, texture, alpha, recipe, mode, mean)
        plate.paste(image, (col * 660, 55))
        draw.text((col * 660 + 10, 20), label, fill='#202820')
        image.save(OUT / (mode + '-panel.png'))
    draw.text((12, 716), 'Same R11 leaves1/5/9/13: 20 original vertices, 12 original triangles, original root positions/normals/UV1/vertex colours. Only UV0 and regenerated tangents differ.', fill='#202820')
    draw.text((12, 738), 'CPU albedo only; photo panel alone uses original alpha. NormalDX, roughness, SSS, native mips/shadows and all-lawn coverage/performance remain unverified.', fill='#202820')
    plate.save(OUT / 'four-original-tapered-leaf-photo-comparison.png')
    gltf_tangents = tangents[:, [0, 2, 1, 3]].copy()
    gltf_tangents[:, 3] *= -1
    prototype = {
        'sourceNode': NODE, 'selectedLeafIndices': list(LEAVES),
        'sourceGlobalVertexIndices': ids.tolist(), 'sourceGlobalTriangleIndices': face_ids.tolist(),
        'sourceGlobalTrianglesGltf': original_faces.tolist(), 'localIndicesGltf': local_faces.tolist(),
        'nativeIndices': ix.tolist(), 'originalGltfAttributes': {k: v.tolist() for k, v in raw.items()},
        'positionsCm': p.tolist(), 'normals': n.tolist(), 'colors': raw['COLOR_0'].tolist(),
        'originalUv1': raw['TEXCOORD_1'].tolist(), 'photographicUv0': uv.tolist(),
        'transportedNativeTangents': tangents.tolist(), 'transportedGltfTangents': gltf_tangents.tolist(),
        'originalLeafMetadata': selected_meta,
        'boundsCm': {'min': p.min(0).tolist(), 'max': p.max(0).tolist()},
        'vertices': 20, 'triangles': 12, 'rootPositionsRearranged': False,
        'nativeImportOrPopulationPlan': False,
    }
    write(OUT / 'four-leaf-uv-prototype.json', prototype)
    # JSON readback is independently compared to raw decoded source attributes.
    saved = json.loads((OUT / 'four-leaf-uv-prototype.json').read_text())
    attributes_proof = {}
    for key, values in raw.items():
        actual = np.asarray(saved['originalGltfAttributes'][key], dtype=values.dtype)
        require(actual.tobytes() == source[key][ids].tobytes(), 'Saved source attribute bits differ: ' + key)
        attributes_proof[key] = {'selectedSourceEncodedSha256': hashlib.sha256(values.tobytes()).hexdigest(),
                                 'dtype': str(values.dtype), 'shape': list(values.shape),
                                 'savedOriginalFloat32BitsExact': True}
    require(np.array_equal(np.asarray(saved['positionsCm']), p) and
            np.array_equal(np.asarray(saved['nativeIndices']), ix), 'Saved native shape differs')
    proof = {
        'status': 'VERIFIED_FOUR_ORIGINAL_TAPERED_LEAVES_PHOTO_UV_AND_TANGENT_SOURCE_ONLY',
        'sourceAttributes': attributes_proof, 'vertices': 20, 'triangles': 12,
        'allOriginalRootPositionsNormalsColorsUv1IndicesAndBoundsExact': True,
        'onlyUv0AndTangentFrameDiffer': True, 'newTangentNormalsUsedOnlyAsReadOnlyBasis': True,
        'triangleUvAndDerivativeMetrics': triangle_metrics,
        'allTriangleUvAreasNonzero': True, 'allTrianglePhysicalAreasUnchanged': True,
        'tangentMaxOrthogonalityError': float(np.max(np.abs(np.sum(tangents[:, :3] * n, axis=1)))),
        'tangentMaxUnitLengthError': float(np.max(np.abs(np.linalg.norm(tangents[:, :3], axis=1) - 1))),
        'oldToNewTangentDegrees': {'min': float(rotation.min()), 'median': float(np.median(rotation)), 'max': float(rotation.max())},
        'tangentWCounts': {str(int(sign)): int((tangents[:, 3] == sign).sum()) for sign in (-1, 1)},
        'actualOriginalVertexColor': {'min': raw['COLOR_0'][:, :3].min(0).tolist(),
                                     'max': raw['COLOR_0'][:, :3].max(0).tolist(),
                                     'nativeAuthoredEquation': 'VertexColor.RGB * linearColor',
                                     'includedInCpuOriginalControl': True},
        'uvCoverage': {'method': '1953 strict-interior barycentric samples per original triangle, 64 subdivisions; physical-area weighting',
                       'sampleCount': len(samples), 'meanAlphaAreaWeighted': float(np.average(samples, weights=weights)),
                       'clipValue': recipe['opacityMaskClipValue'],
                       'alphaAboveClipSampleFraction': float(np.mean(samples >= recipe['opacityMaskClipValue'])),
                       'alphaAboveClipAreaWeightedFraction': float(np.average(samples >= recipe['opacityMaskClipValue'], weights=weights)),
                       'insideOriginalConnectedIslandAreaWeightedFraction': float(np.average(island_inside, weights=weights)),
                       'opaqueMeanSampleCount': int(opaque.sum()), 'matchedPhotographicMeanLinearRGB': mean.tolist(),
                       'maskedSurfaceCoverageIsNotWholeLawnCoverage': True},
        'sourceBoundsCm': prototype['boundsCm'], 'savedBoundsCm': saved['boundsCm'],
        'nativeShaderAccepted': False, 'nativeVisualAccepted': False,
        'fullPhotorealismAccepted': False, 'performanceAccepted': False,
    }
    write(OUT / 'geometry-uv-tangent-proof.json', proof)
    for path, expected in inputs.items():
        require(sha(path) == expected, 'Source changed during execution: ' + path)
    outputs = {str(path): sha(path) for path in sorted(OUT.iterdir())}
    closure = {
        'schemaVersion': 1, 'owner': str(Path(__file__).relative_to(ROOT)),
        'status': 'FROZEN_SOURCE_ONLY_FOUR_ORIGINAL_R11_TAPERED_LEAF_PHOTOGRAPHIC_UV_COMPARISON',
        'inputFiles': inputs, 'outputFiles': outputs, 'allInputHashesUnchangedBeforeAndAfter': True,
        'derivedUvBodyFrom': {'path': str(PRIOR), 'sha256': PINS[str(PRIOR)], 'priorCamberGeometryNotUsed': True},
        'sourceConnectedUvIsland': island, 'originalPhotoRecipe': recipe, 'originalArtistRecipe': artist,
        'sourceMapsProviderProof': prior['sourceMapsProviderProof'], 'all15SourceNodeUvAudit': prior['all15SourceNodeUvAudit'],
        'image': {'path': str(OUT / 'four-original-tapered-leaf-photo-comparison.png'),
                  'sha256': sha(OUT / 'four-original-tapered-leaf-photo-comparison.png'), 'dimensions': [1980, 760]},
        'geometry': {'path': str(OUT / 'four-leaf-uv-prototype.json'), 'sha256': sha(OUT / 'four-leaf-uv-prototype.json'),
                     'vertices': 20, 'triangles': 12, 'sourcePositionsUnchanged': True, 'sourceRootLayoutUnchanged': True},
        'proof': {'path': str(OUT / 'geometry-uv-tangent-proof.json'), 'sha256': sha(OUT / 'geometry-uv-tangent-proof.json')},
        'cpuPanelStatistics': stats, 'matchedPhotoMeanLinearRGB': mean.tolist(),
        'controls': {'sameGeometryCameraNormalsAndLight': True, 'originalAuthoredVertexGradientIncluded': True,
                     'photographicAlbedoScaleUnchanged': .5, 'photoOriginalAlphaOnlyPhotoPanel': True,
                     'uniformPhotoMeanPhysicalAreaWeightedOverAlphaAbove99Percent': True},
        'licensing': 'Existing PH CC0-1.0 grass_medium_02 photo and connected source UV island; artist UV transport, no species/scanner/survey claim.',
        'limitations': ['Only four original leaves; no all-master, population/domain or whole-lawn coverage acceptance.',
                        'No native shader, SSS, normal-map, roughness, mips, shadows or GPU evidence.',
                        'Regenerated tangents are geometry/UV proof only; photo normalDX is not shaded in the CPU comparison.',
                        'Original source photograph and existing padded8bit derivative are unchanged; no new photographic conversion.',
                        'One coherent island repeated across a lawn would need separately bounded source-island/phase variation.',
                        'Photo panel retains original alpha and can discard surface pixels, unlike the two opaque controls.'],
        'unitTestsRun': 0, 'nativeJobsRun': 0, 'nativeShaderAccepted': False,
        'nativeVisualAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False,
        'excludedFromCurrentR12cCandidate': True,
    }
    write(OUT / 'closure.json', closure)
    print(json.dumps({'closure': str(OUT / 'closure.json'), 'sha256': sha(OUT / 'closure.json'),
                      'image': closure['image'], 'sourceSha256': sha(__file__),
                      'uvCoverage': proof['uvCoverage'], 'tangentDegrees': proof['oldToNewTangentDegrees']}))


if __name__ == '__main__':
    build()
