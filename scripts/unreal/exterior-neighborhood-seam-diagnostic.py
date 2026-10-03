"""Source-bound forensic study of R10 parcel material and soil/turf seams.

Native images are observed evidence, never edited here. Pixel-to-ground mapping
is an offline camera/FOV construction, not GPU depth readback. All source and
native evidence remain immutable; this creates only a fresh external study.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct

import numpy as np
import shapely
from shapely.geometry import Point, Polygon, mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighborhood-seam-diagnostic.py'
NATIVE = ROOT / 'output/unreal/exterior-20261001-r10'
CONTEXT = ROOT / 'output/unreal/exterior-context-20260927-r8/context-plan.json'
NEIGHBORHOOD = ROOT / 'output/unreal/exterior-context-20260930-r3/neighborhood-details.json'
QA = ROOT / 'output/unreal/exterior-validation-20260930-r1/qa'
VIEWS = {
    'exterior-canopy-lod': ('after-exterior-r10-artifacts-1790841238025',
        [(1000, 850), (1100, 850), (1040, 900), (1070, 900), (1200, 1000), (1800, 900), (1100, 750), (1100, 780)]),
    'exterior-parcels': ('after-exterior-r10-context-artifacts-1790842281235',
        [(800, 900), (1100, 900), (1300, 850), (400, 1000)]),
    'exterior-neighborhood': ('after-exterior-r10-context-artifacts-1790842281235', []),
}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def geometry(meshes):
    triangles, rows = [], []
    for mesh in meshes:
        for start in range(0, len(mesh['indices']), 3):
            ids = mesh['indices'][start:start + 3]
            xyz = [mesh['verticesCm'][index] for index in ids]
            shape = Polygon([point[:2] for point in xyz])
            if shape.area <= 1e-10:
                continue
            triangles.append(shape)
            rows.append({'meshId': mesh['id'], 'material': mesh['material'], 'xyz': xyz,
                         'alpha': [mesh['uvs'][index][0] for index in ids]})
    return triangles, rows, STRtree(triangles)


def barycentric(xy, xyz):
    a, b, c = np.asarray(xyz)
    denominator = np.cross(b[:2] - a[:2], c[:2] - a[:2])
    require(abs(float(denominator)) > 1e-12, 'Degenerate ground triangle')
    v = np.cross(np.asarray(xy) - a[:2], c[:2] - a[:2]) / denominator
    w = np.cross(b[:2] - a[:2], np.asarray(xy) - a[:2]) / denominator
    return np.asarray([1 - v - w, v, w])


def glb_arrays(path):
    raw = Path(path).read_bytes()
    require(struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw)), 'Invalid native context GLB')
    length, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a, 'Missing GLB JSON')
    document = json.loads(raw[20:20 + length])
    offset = 20 + length
    binary_length, binary_kind = struct.unpack_from('<II', raw, offset)
    require(binary_kind == 0x004e4942 and offset + 8 + binary_length == len(raw), 'Invalid binary GLB extent')
    binary = raw[offset + 8:]

    def accessor(identity):
        value = document['accessors'][identity]
        view = document['bufferViews'][value['bufferView']]
        require('byteStride' not in view and 'sparse' not in value, 'Unexpected native accessor packing')
        components = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[value['type']]
        dtype = {5126: '<f4', 5125: '<u4', 5123: '<u2'}[value['componentType']]
        data = np.frombuffer(binary, dtype=dtype, count=value['count'] * components,
                             offset=view.get('byteOffset', 0) + value.get('byteOffset', 0))
        return data.reshape(value['count'], components)

    result = {}
    for mesh in document['meshes']:
        require(len(mesh['primitives']) == 1, 'Native context mesh has multiple primitives')
        primitive = mesh['primitives'][0]
        result[mesh['name']] = (accessor(primitive['attributes']['POSITION']),
                                accessor(primitive['attributes']['TEXCOORD_0']),
                                accessor(primitive['indices']).reshape(-1))
    return result


def source_ray_samples(view, runtime, pixels, surfaces, surface_rows, surface_tree, soil_rows, soil_tree):
    camera = runtime['walking']['presentationCamera']
    eye, forward = np.asarray(camera['eyeCm']), np.asarray(camera['forward'])
    require(np.max(np.abs(eye - view['eyeCm'])) < 1e-5, 'Actual camera/source origin differs')
    right = np.asarray([-forward[1], forward[0], 0.])
    right /= np.linalg.norm(right)
    up = np.cross(forward, right)
    tan = math.tan(math.radians(view['horizontalFovDegrees'] / 2))
    results = []
    for px, py in pixels:
        direction = forward + (px / 960 - 1) * tan * right + (1 - py / 540) * tan * 1080 / 1920 * up
        require(direction[2] < 0, 'Selected forensic ground pixel points upward')
        target_z = -18.2
        hits = []
        for _ in range(4):
            distance = (target_z - eye[2]) / direction[2]
            xyz = eye + distance * direction
            point = Point(xyz[:2])
            hits = [surface_rows[int(index)] for index in surface_tree.query(point, predicate='intersects')]
            require(hits, 'Forensic ground ray outside original context')
            target_z = max(float(barycentric(xyz[:2], value['xyz']) @ np.asarray(value['xyz'])[:, 2]) for value in hits)
        xy = xyz[:2].tolist()
        soil_hits = [soil_rows[int(index)] for index in soil_tree.query(Point(xy), predicate='intersects')]
        alpha = [float(barycentric(xy, row['xyz']) @ row['alpha']) for row in soil_hits]
        results.append({'pixel': [px, py], 'sourceProjectedXYCm': xy, 'sourceGroundZCm': target_z,
                        'surfaceHits': [{'meshId': row['meshId'], 'material': row['material']} for row in hits],
                        'soilHits': [{'meshId': row['meshId'], 'interpolatedUV0U': value} for row, value in zip(soil_hits, alpha)],
                        'projectionMethod': 'Pinned source horizontal FOV plus actual native lens origin/forward, iterated source triangle height; no GPU depth.'})
    return results


def build(output):
    require(not output.exists(), 'Use a new immutable diagnostic folder')
    snapshot_path = NATIVE / 'source-freeze/snapshot.json'
    require(sha(snapshot_path) == 'be9346973bb1240b4f8eafcf05093aca73b9bfee4c5e5252f61a8e5a2afca6c0', 'R10 sealed snapshot differs')
    frozen = read(snapshot_path)
    paths = {Path(__file__).resolve(), snapshot_path, NATIVE / 'exterior-import-report.json', NATIVE / 'model-package.json',
             NATIVE / 'exterior-context.glb', NATIVE / 'Project/BreziTwin/Content/Data/viewpoints.json',
             CONTEXT, NEIGHBORHOOD, ROOT / 'scripts/unreal/exterior-context.py',
             ROOT / 'scripts/unreal/exterior-neighborhood.py', ROOT / 'scripts/unreal/rural-import.py'}
    report, context, neighborhood = map(read, (NATIVE / 'exterior-import-report.json', CONTEXT, NEIGHBORHOOD))
    require(report['activeDesign'] == context['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'C/B/B differs')
    require(report['setbacksMm'] == {'street': 3000, 'east': 3000}, '3000mm setbacks differ')
    require(report['neighborhoodDetails']['plan'] == str(NEIGHBORHOOD), 'R10 uses another neighborhood')
    require(context['sourceSceneSha256'] == neighborhood['sourceSceneSha256'] and context['sourceObjSha256'] == neighborhood['sourceObjSha256'], 'Architectural source differs')
    views = {value['id']: value for value in read(NATIVE / 'Project/BreziTwin/Content/Data/viewpoints.json')['views']}
    for scene, (folder, _) in VIEWS.items():
        summary = read(QA / folder / 'summary.json')
        row = next(value for value in summary['results'] if value['scene'] == scene + '-day')
        evidence = Path(row['evidence'])
        paths.update([QA / folder / 'summary.json', evidence / 'runtime.json', evidence / 'qa.json', evidence / 'capture.png'])
    source_pins = {str(path): sha(path) for path in sorted(paths)}
    for path, digest in source_pins.items():
        if path in frozen['files']:
            require(frozen['files'][path]['sha256'] == digest, 'Original differs from R10 source freeze: ' + path)
    soil_meshes = [mesh for mesh in neighborhood['meshes'] if mesh['material'] == 'context_soil_exposure']
    ground_meshes = [mesh for mesh in context['meshes'] if mesh['id'].startswith('context_surface')]
    surface_shapes, surface_rows, surface_tree = geometry(ground_meshes)
    soil_shapes, soil_rows, soil_tree = geometry(soil_meshes)
    exposure = unary_union(soil_shapes)
    native = glb_arrays(NATIVE / 'exterior-context.glb')
    uv_receipts = []
    for mesh in soil_meshes:
        positions, uvs, indices = native[mesh['id'] + '_LOD0']
        expected = np.asarray([[x / 100, z / 100, y / 100] for x, y, z in mesh['verticesCm']], dtype=np.float32)
        require(np.array_equal(positions, expected) and np.array_equal(uvs, np.asarray(mesh['uvs'], dtype=np.float32))
                and np.array_equal(indices, mesh['indices']), 'Native exported soil topology/UV changed')
        require(np.min(uvs[:, 0]) == 0 and np.max(uvs[:, 0]) == 1 and np.max(np.abs(uvs[:, 1])) == 0, 'Soil edge/body coverage differs')
        uv_receipts.append({'meshId': mesh['id'], 'triangles': len(indices) // 3, 'vertices': len(positions),
                            'nativeMesh': report['geometry']['meshes'][mesh['id']], 'nativeActor': report['geometry']['actors'][mesh['id']],
                            'maxDrawDistanceCm': mesh['maxDrawDistanceCm'], 'UV0U': [0, 1],
                            'exportedFloat32PositionsUVAndIndicesExactlyMatch': True})
    material = report['materials']['materials']['context_soil_exposure']
    nodes = {node['role']: node for node in material['graph']['nodes']}
    require(nodes['BreziExterior:soil-exposure-coverage-uv0']['values']['coordinate_index'] == 0,
            'Native graph uses another UV channel')
    require(material['graph']['roots']['OPACITY_MASK'][0] == 'BreziExterior:soil-exposure-native-temporal-dither', 'Native soil coverage output differs')
    samples = {}
    for scene, (folder, pixels) in VIEWS.items():
        row = next(value for value in read(QA / folder / 'summary.json')['results'] if value['scene'] == scene + '-day')
        runtime = read(Path(row['evidence']) / 'runtime.json')
        require(sha(Path(row['evidence']) / 'runtime.json') == row['runtimeReportSha256'] and
                sha(Path(row['evidence']) / 'capture.png') == row['screenshotSha256'], 'Native QA artifact pin differs')
        samples[scene] = source_ray_samples(views[scene], runtime, pixels, surface_shapes, surface_rows, surface_tree, soil_rows, soil_tree)
    seam = samples['exterior-canopy-lod'][:4]
    require([value['surfaceHits'][0]['material'] for value in seam] == ['context_meadow', 'context_fallow', 'context_meadow', 'context_fallow']
            and all(not value['soilHits'] for value in seam), 'Measured rectangular seam cause differs')
    removed = neighborhood['groundDetailRemovedPlacementIndices']
    removal_audit = {}
    for name, indices in removed.items():
        rows = context[name]
        distances = shapely.distance(exposure, shapely.points([row['positionCm'][:2] for row in rows]))
        expected = [index for index, (distance, row) in enumerate(zip(distances, rows)) if distance <= row['radiusCm'] + 1. + 1e-7]
        require(expected == indices, 'Original whole-crown removal policy does not match source geometry: ' + name)
        removal_audit[name] = {'original': len(rows), 'removed': len(indices), 'retained': len(rows) - len(indices),
                               'wholeCrownMarginCm': 1, 'indicesIndependentlyRecomputed': True}
    for path, digest in source_pins.items():
        require(sha(path) == digest, 'Original changed during diagnosis')
    output.mkdir(parents=True)
    write(output / 'soil-exposure-footprints.json', {'source': str(NEIGHBORHOOD), 'sourceSha256': sha(NEIGHBORHOOD),
          'geometrySource': 'Union of all actual source soil mesh XY triangles, without padding', 'geometry': mapping(exposure)})
    result = {'schemaVersion': 1, 'owner': OWNER, 'generatorSha256': sha(__file__), 'status': 'source-seam-cause-verified-native-depth-not-measured',
              'generatedAtUtc': datetime.now(timezone.utc).isoformat(), 'source': str(NATIVE),
              'activeDesign': context['activeDesign'], 'housePlacement': context['housePlacement'],
              'sourceSceneSha256': context['sourceSceneSha256'], 'sourceObjSha256': context['sourceObjSha256'], 'inputFiles': source_pins,
              'nativeInputsUntouched': True, 'nativeImagesViewed': list(VIEWS), 'pixelGroundSamples': samples,
              'sourceSoilPatchesDeclared': len(neighborhood['groundDetailFeatheringPolicy']['partitions']),
              'actualSoilUnionConnectedPolygons': len(exposure.geoms) if exposure.geom_type == 'MultiPolygon' else 1,
              'soilFootprintAreaM2': exposure.area / 10000, 'soilFootprintPerimeterM': exposure.length / 100,
              'soilMeshes': uv_receipts, 'soilUVAndTopologyExactlyPreservedInExport': True,
              'nativeSoilMaterialAsset': material['asset'], 'nativeSoilRecipe': material['recipe'],
              'nativeSoilGraphReadback': material['graph'], 'removalAudit': removal_audit,
              'findings': [
                  {'cause': 'Arbitrary inherited parcel material discontinuity', 'evidence': 'Actual canopy-LOD rectangle separates context_surface_6035_19_surface_79 meadow and context_surface_6035_20_surface_80 fallow; source rays on both sides hit no soil exposure.',
                   'sourceRule': "classify(number) returns fallow when sum(map(ord, number)) % 3 == 0 for6012/ or6035/; this is artist classification, not measured land use."},
                  {'cause': 'Whole-crown removals expose the original smooth green substrate throughout the feather footprint and outside its rim',
                   'evidence': '47,203 recorded plant roots are removed against full573 source patch footprints, including the UV0U0..1 feather band; large clumps cannot remain cut by the ground layer.'},
              ], 'minimalProposal': {'targetMaterials': ['context_meadow', 'context_fallow'],
                  'preserve': ['Exact legal/source ground geometry and collision', 'C/B/B/private/3000mm frame', 'cropped/arable/vineyard domains', 'official building footprints', 'all original sources and native evidence'],
                  'ground': 'Use one common near-ground PBR recipe on authored meadow/fallow finishes; drive continuous spatial ground condition independently of legal edges. No global darkening.',
                  'edge': 'Keep old whole-crown removals. Add compact low-cover clumps with every decoded LOD triangle outside exact soil exposure and inside allowed original meadow/fallow ground, private/road/building exclusions.'},
              'nativeVisualAccepted': False, 'performanceAccepted': False, 'limits': 'CPU source diagnosis and exported topology proof only. Pixel mapping is source projection without GPU depth. Ground finish is illustrative authoring, not cadastral land-use or botanical evidence. A future native comparison must assess appearance.'}
    write(output / 'diagnostic.json', result)
    print(json.dumps({'diagnostic': str(output / 'diagnostic.json'), 'sha256': sha(output / 'diagnostic.json'),
                      'soilPatches': result['sourceSoilPatchesDeclared'], 'actualUnionPolygons': result['actualSoilUnionConnectedPolygons'],
                      'soilMeshes': len(soil_meshes), 'removedPlants': sum(len(values) for values in removed.values())}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(ROOT / 'output/unreal'), 'Use isolated Unreal output')
    build(output)


if __name__ == '__main__':
    main()
