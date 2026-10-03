"""Source-only original Poly Haven Fern02 fit; never imports Unreal or changes a scene.

Provider files stay byte exact. The decoded local mesh, rather than the provider's
four-clump display arrangement, is fitted uniformly at one existing garden root.
Derived binary64 measurements are source observations, not future UE equality gates.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-fern-study-r25.py'
REFERENCE = ROOT/'output/unreal/exterior-ph-fern-reference-20261002-r1'
OUTPUT = ROOT/'output/unreal/exterior-garden-fern-20261002-r25-study'
GARDEN = ROOT/'output/unreal/exterior-garden-organic-20261001-r1c-study/garden-plan.json'
GARDEN_SHA = 'e599442a7ec887d16ee6e58c7466f4a34bf9a7880ef538bd2861c80ad39523e6'
GARDEN_GUARD = ROOT/'scripts/unreal/exterior-garden-organic-native.py'
GARDEN_GUARD_SHA = '36737bb774b14eb95aafbd2d93d7317160d451cbea3cb6e572181e114536604b'
R16 = ROOT/'output/unreal/exterior-20261001-r16a/exterior-import-report.json'
ROOT_ID = 'garden_ornamental_10'
GROUP_ID = 'EX_ornamental_0_-1_garden_feather_r3_b_18000'
SELECTED_NODE = 'fern_02_b'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def value_sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def load_guard():
    require(sha(GARDEN_GUARD) == GARDEN_GUARD_SHA, 'Original own-garden guard changed')
    spec = importlib.util.spec_from_file_location('frozen_garden_source_guard_r25', GARDEN_GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decode(document, binaries):
    """Decode actual accessors, with offsets/stride, without scene display transforms."""
    require(document.get('asset', {}).get('version') == '2.0', 'glTF version differs')
    require(not document.get('extensionsRequired') and not document.get('extensionsUsed')
            and not document.get('skins') and not document.get('animations'),
            'Unreviewed glTF extensions, skins or animation')

    def accessor(index):
        row = document['accessors'][index]
        require(not row.get('sparse') and not row.get('normalized'), 'Sparse/normalized accessor unreviewed')
        component = {5126: ('f', 4), 5123: ('H', 2), 5125: ('I', 4)}
        require(row['componentType'] in component, 'Accessor component unreviewed')
        count = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}.get(row['type'])
        require(count is not None and row['count'] > 0, 'Accessor dimension/count invalid')
        code, size = component[row['componentType']]
        view = document['bufferViews'][row['bufferView']]
        raw = binaries[view['buffer']]
        base = view.get('byteOffset', 0)+row.get('byteOffset', 0)
        width = count*size
        stride = view.get('byteStride', width)
        require(stride >= width and base >= view.get('byteOffset', 0)
                and base+(row['count']-1)*stride+width <= view.get('byteOffset', 0)+view['byteLength']
                and view.get('byteOffset', 0)+view['byteLength'] <= len(raw), 'Accessor extent escapes buffer')
        rows = [struct.unpack_from('<'+code*count, raw, base+i*stride) for i in range(row['count'])]
        require(all(math.isfinite(v) for r in rows for v in r), 'Nonfinite source attribute')
        return rows

    result = []
    for node in document['nodes']:
        require(set(node) <= {'mesh', 'name', 'translation'} and 'mesh' in node,
                'Unreviewed provider local transform')
        mesh = document['meshes'][node['mesh']]
        require(len(mesh['primitives']) == 1, 'Unreviewed multiprimitive fern')
        primitive = mesh['primitives'][0]
        require(primitive.get('mode', 4) == 4 and not primitive.get('targets')
                and set(primitive['attributes']) == {'POSITION', 'NORMAL', 'TEXCOORD_0'},
                'Original fern attribute/topology contract differs')
        positions = accessor(primitive['attributes']['POSITION'])
        normals = accessor(primitive['attributes']['NORMAL'])
        uv = accessor(primitive['attributes']['TEXCOORD_0'])
        indices = [v[0] for v in accessor(primitive['indices'])]
        require(len(positions) == len(normals) == len(uv) and len(indices) % 3 == 0
                and all(isinstance(i, int) and 0 <= i < len(positions) for i in indices),
                'Original fern attribute/index counts differ')
        require(all(len(v) == 3 for v in positions+normals) and all(len(v) == 2 for v in uv),
                'Original fern attribute dimensions differ')
        native = [[100*x, 100*z, 100*y] for x, y, z in positions]
        bounds = {side: [fn(v[k] for v in native) for k in range(3)]
                  for side, fn in (('min', min), ('max', max))}
        source_accessor = document['accessors'][primitive['attributes']['POSITION']]
        require(list(map(list, zip(*[source_accessor['min'], source_accessor['max']])))
                == [[min(v[k] for v in positions), max(v[k] for v in positions)] for k in range(3)],
                'Actual source POSITION min/max differs from accessor')
        degenerate = 0
        opposed = 0
        degenerate_uv = 0
        for i in range(0, len(indices), 3):
            a, b, c = [positions[k] for k in indices[i:i+3]]
            d, e = [b[k]-a[k] for k in range(3)], [c[k]-a[k] for k in range(3)]
            cross = [d[1]*e[2]-d[2]*e[1], d[2]*e[0]-d[0]*e[2], d[0]*e[1]-d[1]*e[0]]
            norm = [sum(normals[k][q] for k in indices[i:i+3])/3 for q in range(3)]
            degenerate += sum(v*v for v in cross) <= 1e-20
            opposed += sum(cross[k]*norm[k] for k in range(3)) < 0
            a, b, c = [uv[k] for k in indices[i:i+3]]
            degenerate_uv += abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])) <= 1e-12
        result.append({'node': node['name'], 'meshIndex': node['mesh'], 'meshName': mesh['name'],
            'displayTranslationMetersNotApplied': node.get('translation', [0, 0, 0]),
            'vertices': len(positions), 'triangles': len(indices)//3, 'boundsCm': bounds,
            'radialEnvelopeCm': max(math.hypot(v[0], v[1]) for v in native),
            'maximumNormalSquaredLengthError': max(abs(sum(v*v for v in n)-1) for n in normals),
            'degenerateTriangles': degenerate, 'opposedMeanNormalTriangles': opposed,
            'degenerateUvTriangles': degenerate_uv,
            'uvBounds': {'min': [min(v[k] for v in uv) for k in range(2)],
                         'max': [max(v[k] for v in uv) for k in range(2)]},
            'sourceTangentsPresent': False, 'extensions': [],
            'positionSha256': value_sha(positions), 'normalSha256': value_sha(normals),
            'uvSha256': value_sha(uv), 'indicesSha256': value_sha(indices),
            '_nativePositions': native, '_positions': positions, '_normals': normals,
            '_uv': uv, '_indices': indices})
    return result


def fit(row, root, garden, guard):
    require(root['id'] == ROOT_ID and root['meshId'] == 'garden_feather_r3_b'
            and root['sourceBedId'] == 'DOM_01966' and root['yawDeg'] == -31,
            'Selected existing root identity changed')
    scale = min(root['radiusCm']/row['radialEnvelopeCm'],
                root['actualHeightCm']/row['boundsCm']['max'][2])
    require(math.isfinite(scale) and scale > 0, 'Uniform fit invalid')
    points = row['_nativePositions']
    radius = max(math.hypot(p[0]*scale, p[1]*scale) for p in points)
    triangles = garden['sourceMulchTrianglesCm'][root['sourceBedId']]
    boundary = guard._boundary(triangles)
    xy = root['positionCm'][:2]
    boundary_distance = min(guard._distance(xy, a, b) for a, b in boundary)
    require(any(guard._triangle_inside(xy, t) for t in triangles)
            and radius <= root['radiusCm']+1e-12 and radius < boundary_distance,
            'Complete fern containing circle escapes original own-garden bed')
    angle = math.radians(root['yawDeg'])
    c, s = math.cos(angle), math.sin(angle)
    world = [[xy[0]+scale*(c*p[0]-s*p[1]), xy[1]+scale*(s*p[0]+c*p[1]),
              root['positionCm'][2]+scale*p[2]] for p in points]
    require(all(any(guard._triangle_inside(p[:2], t) for t in triangles) for p in world),
            'Decoded full fern vertices leave unchanged mulch')
    step_triangles = [t for ts in garden['sourceStepTrianglesCm'].values() for t in ts]
    valid_step_triangles = []
    step_edges = []
    for t in step_triangles:
        a, b, c = t
        if abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])) > 1e-8:
            valid_step_triangles.append(t)
        for a, b in zip(t, t[1:]+t[:1]):
            if math.hypot(a[0]-b[0], a[1]-b[1]) > 1e-9:
                step_edges.append((a[:2], b[:2]))
    require(not any(guard._triangle_inside(xy, t) for t in valid_step_triangles),
            'Original root intersects projected hardscape')
    step_distance = min(guard._distance(xy, a, b) for a, b in step_edges)
    require(step_distance > radius, 'Full circular fern crown intersects source steps')
    return {'rootId': ROOT_ID, 'sourceBedId': root['sourceBedId'],
            'originalRoot': root, 'positionCm': root['positionCm'], 'yawDeg': root['yawDeg'],
            'uniformScale': scale, 'scale': [scale]*3, 'radialEnvelopeCm': radius,
            'abovePivotHeightCm': row['boundsCm']['max'][2]*scale,
            'belowPivotDepthCm': -row['boundsCm']['min'][2]*scale,
            'worldZCm': [min(p[2] for p in world), max(p[2] for p in world)],
            'originalAbovePivotHeightCm': root['actualHeightCm'],
            'sourceOriginPreserved': True, 'sceneDisplayTranslationsApplied': False,
            'uniformFitLimitingDimension': 'radius', 'allDecodedVerticesChecked': len(world),
            'completeContainingCircleInsideOriginalMulch': True,
            'circleToOriginalBedBoundaryClearanceCm': boundary_distance-radius,
            'sourceRootToBoundaryCm': boundary_distance,
            'sourceStepTrianglesChecked': len(step_triangles),
            'projectedNondegenerateStepTriangles': len(valid_step_triangles),
            'nonzeroProjectedStepEdgesChecked': len(step_edges),
            'circleToSourceStepMinimumClearanceCm': step_distance-radius,
            'groundOrHardscapeGeometryChanged': False,
            'sceneArchitectureMoved': False, 'otherGardenRootsMoved': False,
            'maskScope': 'ORIGINAL_OWN_GARDEN_BED_COMPLETE_TRIANGLE_UNION_AND_SOURCE_STEPS',
            'meadowPrivateParcelExclusionMaskUsed': False}


def validate_alpha():
    import numpy as np
    from PIL import Image
    original_diffuse = Image.open(REFERENCE/'textures/fern_02_diff_2k.jpg')
    alpha = Image.open(REFERENCE/'textures/fern_02_alpha_2k.png')
    values = np.asarray(alpha)
    require(original_diffuse.mode == 'RGB' and alpha.mode == 'I;16'
            and alpha.size == original_diffuse.size == (2048, 2048), 'Original alpha/diffuse schema differs')
    require(values.dtype == np.uint16 and int(values.max()) == 65535 and int(values.min()) == 0,
            'Original sixteen-bit alpha normalized range differs')
    return {'originalBaseColorJpegHasAlpha': False,
            'originalGltfMaskAloneProvidesLeafOpacity': False,
            'requiredExplicitAlphaMap': pin(REFERENCE/'textures/fern_02_alpha_2k.png'),
            'alphaSourceMode': alpha.mode, 'alphaSourceBits': 16,
            'futureOpacityBinding': 'EXPLICIT_NORMALIZED_ALPHA_TEXTURE_R_TO_OPACITY_MASK',
            'cutoff': .5, 'sourcePixelCount': int(values.size),
            'zeroPixels': int(np.count_nonzero(values == 0)),
            'onePixels': int(np.count_nonzero(values == 65535)),
            'atlasCoverageAtCutoff': float(np.count_nonzero(values >= 32768)/values.size),
            'nativeTextureReadbackPerformed': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    require(not args.output.exists(), 'Refusing to overwrite an existing source study')
    require(sha(GARDEN) == GARDEN_SHA, 'Original garden plan changed')
    guard = load_guard()
    input_paths = [Path(__file__), GARDEN, GARDEN_GUARD, R16]
    input_paths += sorted(p for p in REFERENCE.rglob('*') if p.is_file())
    inputs = {str(p.resolve()): sha(p) for p in input_paths}
    info = json.loads((REFERENCE/'provider-info.json').read_text())
    provider = json.loads((REFERENCE/'provider-files.json').read_text())
    downloads = json.loads((REFERENCE/'downloaded-files.json').read_text())
    require(info['name'] == 'Fern 02' and info['polycount'] == 6232, 'Provider asset metadata differs')
    expected = [('fern_02_2k.gltf', provider['gltf']['2k']['gltf'])]
    expected += list(provider['gltf']['2k']['gltf']['include'].items())
    expected += [('textures/fern_02_alpha_2k.png', provider['Alpha']['2k']['png']),
                 ('physical/fern_02_nor_gl_2k.png', provider['nor_gl']['2k']['png']),
                 ('physical/fern_02_arm_2k.png', provider['arm']['2k']['png'])]
    require(len(downloads) == len(expected) == 8, 'Original provider resource census differs')
    by_path = {r['path']: r for r in downloads}
    for relative, source in expected:
        raw = (REFERENCE/relative).read_bytes()
        r = by_path[relative]
        require(len(raw) == source['size'] == r['bytes'] == r['publishedBytes']
                and hashlib.md5(raw).hexdigest() == source['md5'] == r['md5'] == r['publishedMd5']
                and sha(REFERENCE/relative) == r['sha256'] and source['url'] == r['url'],
                'Published provider bytes/MD5/SHA mismatch: '+relative)
    doc = json.loads((REFERENCE/'fern_02_2k.gltf').read_text())
    bins = [(REFERENCE/b['uri']).read_bytes() for b in doc['buffers']]
    require(all(len(raw) == row['byteLength'] for raw, row in zip(bins, doc['buffers'])), 'glTF buffer byte census differs')
    rows = decode(doc, bins)
    require({r['node'] for r in rows} == {'fern_02_a', 'fern_02_b', 'fern_02_c', 'fern_02_d'}
            and sum(r['triangles'] for r in rows) == info['polycount'], 'Decoded original clump census differs')
    material = doc['materials'][0]
    require(len(doc['materials']) == 1 and material['alphaMode'] == 'MASK'
            and material['alphaCutoff'] == .5 and material['doubleSided'] is True
            and material['pbrMetallicRoughness']['metallicFactor'] == 0, 'Original fern material differs')
    garden = json.loads(GARDEN.read_text())
    roots = [r for r in garden['ornamentalPlacements'] if r['id'] == ROOT_ID]
    require(len(roots) == 1 and len(garden['ornamentalPlacements']) == 12
            and len(garden['gardenDetailPlacements']) == 461, 'Original garden placement census differs')
    r16 = json.loads(R16.read_text())
    group = r16['geometry']['groups'][GROUP_ID]
    require(r16['status'] == 'exterior-import-validated' and r16['savedReloaded'] is True
            and group['instances'] == 1 and group['cullStartCm'] == 14400
            and group['cullEndCm'] == 18000 and group['qualityDetail'] is False
            and group['transformsSha256'] == 'dfb6f59a2c17846d8a9a4155f83a198131171058c24556677a4da2d426fb1e68',
            'Existing actual saved garden root group differs')
    selected = next(r for r in rows if r['node'] == SELECTED_NODE)
    placement = fit(selected, roots[0], garden, guard)
    alpha = validate_alpha()
    output = args.output.resolve()
    output.mkdir()
    source_geometry = {k: selected[k] for k in ('_positions', '_normals', '_uv', '_indices')}
    (output/'selected-original-geometry.json').write_text(json.dumps(source_geometry, separators=(',', ':'))+'\n')
    audit = {'owner': OWNER, 'status': 'verified-decoded-original-fern-own-bed-source-only',
             'originalGeometryDecoded': True, 'publishedResourceBytesVerified': True,
             'fullOwnBedCrownChecked': True, 'artistPlantChoice': True, 'surveyedBotany': False,
             'wholePlantScannedGeometryProven': False, 'sourcePixelEditsPerformed': False,
             'originalGeometryAttributesChanged': False, 'nativeApplied': False,
             'nativeGeometryReadbackPerformed': False, 'nativeAppearanceAccepted': False,
             'fullPhotorealismAccepted': False, 'performanceAccepted': False,
             'shippingVerified': False}
    plan = {'schema': 'brezi-original-fern-own-garden-source-pilot-r25', 'owner': OWNER,
        'status': 'source-only-original-fern-own-garden-pilot-native-base-pending',
        'generatedAt': datetime.now(timezone.utc).isoformat(), 'generatorSha256': sha(__file__),
        'inputFiles': inputs, 'provider': {'assetId': 'fern_02', 'assetUrl': 'https://polyhaven.com/a/fern_02',
            'license': 'CC0', 'licenseUrl': 'https://polyhaven.com/license', 'authorCredits': info['authors'],
            'wholePlantScannedGeometryProven': False},
        'sourceGarden': pin(GARDEN), 'originalNativeRootBasis': pin(R16),
        'futureNativeBase': {'requiredRevision': 'ACTUALLY_SAVED_R22', 'availableAtGeneration': False,
                             'pin': None, 'nativePilotAuthorizedOrExecutedHere': False},
        'activeDesign': garden['activeDesign'], 'housePlacement': garden['housePlacement'],
        'sourceSceneSha256': garden['sourceSceneSha256'], 'sourceObjSha256': garden['sourceObjSha256'],
        'sourceGltf': pin(REFERENCE/'fern_02_2k.gltf'),
        'selectedOriginalGeometry': pin(output/'selected-original-geometry.json'),
        'allOriginalMeshMeasurements': [{k: v for k, v in r.items() if not k.startswith('_')} for r in rows],
        'selectedNode': SELECTED_NODE, 'selectionReason': 'Largest original authored clump; single root trial only',
        'placementProposal': placement, 'originalSavedGroup': {'id': GROUP_ID, **group},
        'preservation': {'otherOrnamentalRows': 11, 'otherDetailRows': 461,
            'otherOrnamentalRowsSha256': value_sha([r for r in garden['ornamentalPlacements'] if r['id'] != ROOT_ID]),
            'allDetailRowsSha256': value_sha(garden['gardenDetailPlacements']),
            'mulchAndStepTopologySha256': value_sha({k: garden[k] for k in ('sourceMulchTrianglesCm', 'sourceStepTrianglesCm')}),
            'layoutOrSourceGeometryEdited': False, 'oldSourceAssetsEdited': False},
        'materialProposal': {'originalGltfMaterial': material, 'explicitAlpha': alpha,
            'baseColor': pin(REFERENCE/'textures/fern_02_diff_2k.jpg'),
            'normalGL': pin(REFERENCE/'physical/fern_02_nor_gl_2k.png'),
            'arm': pin(REFERENCE/'physical/fern_02_arm_2k.png'),
            'normalFutureUnrealFlipGreen': True, 'baseColorFutureSRGB': True,
            'normalAndArmFutureSRGB': False, 'roughnessChannel': 'G', 'metallicConstant': 0,
            'aoFactorNativeDecisionPending': True, 'twoSidedMasked': True,
            'sourceTangentsAbsent': True, 'futureTangentGenerationRequired': True,
            'nativeMaterialGraphBuilt': False},
        'futureGeometryBudget': {'instances': 1, 'originalSelectedTriangles': selected['triangles'],
                                 'nativeLodPlanSelected': False, 'nativeLodsBuilt': 0},
        'limits': ['Uniform radius fit yields approximately 35 cm above pivot, replacing a 120 cm grass form.',
            'Original basal vertices extend below the unchanged root pivot; they are not lifted or trimmed.',
            'Provider MASK glTF references opaque JPEG: explicit normalized sixteen-bit Alpha.R is mandatory.',
            'Original TANGENT attribute is absent; native tangent generation and material readback remain future work.',
            'Source CPU or metadata measurements are not Unreal appearance, ecology, survey or performance proof.',
            'Future native base must be actual saved R22, separately pinned after completion.'], 'audit': audit}
    (output/'fern-pilot-source-plan.json').write_text(json.dumps(plan, indent=2, allow_nan=False)+'\n')
    (output/'source-download-receipt.json').write_text(json.dumps({'owner': OWNER,
        'status': 'verified-original-provider-resource-bytes-no-pixel-edits',
        'providerInfo': pin(REFERENCE/'provider-info.json'), 'providerFiles': pin(REFERENCE/'provider-files.json'),
        'assetPage': pin(REFERENCE/'provider-asset-page.html'), 'licensePage': pin(REFERENCE/'provider-license-page.html'),
        'downloadedResources': downloads, 'downloadedResourceBytes': sum(r['bytes'] for r in downloads),
        'license': 'CC0', 'allPublishedSizesAndMd5Matched': True, 'nativeImported': False}, indent=2)+'\n')
    require(all(sha(path) == digest for path, digest in inputs.items()), 'Consumed source inputs changed during study')
    receipt = {'owner': OWNER, 'status': audit['status'], 'inputPinsBefore': inputs,
        'inputPinsAfterUnchanged': True, 'files': {str(p.resolve()): pin(p) for p in sorted(output.iterdir())},
        'audit': audit, 'nativeBasePending': True}
    (output/'source-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({'status': audit['status'], 'plan': pin(output/'fern-pilot-source-plan.json'),
        'referenceResources': len(downloads), 'referenceBytes': sum(r['bytes'] for r in downloads),
        'selectedTriangles': selected['triangles'], 'uniformScale': placement['uniformScale'],
        'heightCm': placement['abovePivotHeightCm'], 'crownRadiusCm': placement['radialEnvelopeCm'],
        'fullBedClearanceCm': placement['circleToOriginalBedBoundaryClearanceCm'], 'nativeBasePending': True}))


if __name__ == '__main__':
    main()
