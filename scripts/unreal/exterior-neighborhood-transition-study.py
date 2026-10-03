"""Isolated artist ground-condition and compact verge prototype for a future run.

The R10 cadastral ground, original vegetation removals, source scans, collision
and private site remain unchanged. This is a source-only proposal, not a native
material implementation or a claim about measured vegetation/land use.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random

import numpy as np
from PIL import Image, ImageDraw
import shapely
from shapely.geometry import Point, Polygon, shape, mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighborhood-transition-study.py'
DIAGNOSTIC = ROOT / 'output/unreal/exterior-neighborhood-seam-diagnostic-20261001-r1/diagnostic.json'
DIAGNOSTIC_SHA = '60c2712e1db2499997c5d8a36cf8eccb806b0710475d44efedf3068082be31f6'
CONTEXT = ROOT / 'output/unreal/exterior-context-20260927-r8/context-plan.json'
NEIGHBORHOOD = ROOT / 'output/unreal/exterior-context-20260930-r3/neighborhood-details.json'
BUILDINGS = ROOT / 'output/unreal/exterior-buildings-20260926-r2/building-plan.json'
MASTERS = ROOT / 'output/unreal/exterior-assets-greenery-20260930-r5/geometry-manifest.json'
NATIVE = ROOT / 'output/unreal/exterior-20261001-r10'
BOUNDS = [-18000., -18000., 18000., 18000.]
PROTOTYPES = ('grass_medium_02_a', 'grass_medium_02_b', 'grass_medium_02_c')
SPEC = importlib.util.spec_from_file_location('transition_diagnostic', ROOT / 'scripts/unreal/exterior-neighborhood-seam-diagnostic.py')
diag = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(diag)
require, read, sha, write, decode = diag.require, diag.read, diag.sha, diag.write, diag.glb_arrays


def condition(x, y):
    """A continuous artist condition field, independent of any parcel identifier."""
    def value(px, py, seed):
        ix, iy = np.floor(px), np.floor(py)
        fx, fy = px - ix, py - iy
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        def hashed(a, b):
            value = np.sin(a * 127.1 + b * 311.7 + seed) * 43758.5453
            return value - np.floor(value)
        lo = hashed(ix, iy) * (1 - fx) + hashed(ix + 1, iy) * fx
        hi = hashed(ix, iy + 1) * (1 - fx) + hashed(ix + 1, iy + 1) * fx
        return lo * (1 - fy) + hi * fy
    result = .55 * value(np.asarray(x) / 2400, np.asarray(y) / 2400, 31)
    result += .30 * value(np.asarray(x) / 1200 + 17, np.asarray(y) / 1200 + 17, 67)
    result += .15 * value(np.asarray(x) / 400 + 39, np.asarray(y) / 400 + 39, 109)
    return np.clip(result, .15, .85)


def common_response(x, y, meadow, fallow):
    amount = float(condition(x, y))
    return {'coverAmount': .34 + .40 * amount,
            'tint': [(1 - amount) * a + amount * b for a, b in zip(fallow['tint'], meadow['tint'])],
            'albedoScale': .74 + .04 * amount, 'normalStrength': .70 - .05 * amount}


def source_shapes(context, numbers):
    wanted = {row['meshId'] for row in context['surfaces'] if row['parcelNumber'] in numbers
              and row['finish'] == 'surface' and row['material'] in ('context_meadow', 'context_fallow')}
    meshes = [mesh for mesh in context['meshes'] if mesh['id'] in wanted]
    triangles, rows, index = diag.geometry(meshes)
    return meshes, unary_union(triangles), rows, index


def prototype_geometry(manifest):
    source = {mesh['id']: mesh for mesh in manifest['meshes']}
    cache, result = {}, {}
    for identity in PROTOTYPES:
        row = source[identity]
        path = Path(row['glbPath'])
        require(sha(path) == row['glbSha256'], 'Prototype GLB source changed')
        if path not in cache:
            cache[path] = decode(path)
        levels = []
        for level in row['lods']:
            positions, uvs, indices = cache[path][level['nodeName']]
            points = positions[:, [0, 2, 1]].astype(np.float64) * 100
            require(len(indices) // 3 == level['triangles'], 'Actual prototype triangle count differs')
            levels.append({'level': level['level'], 'points': points, 'uvs': uvs, 'indices': indices,
                           'triangles': len(indices) // 3})
        points = np.concatenate([value['points'] for value in levels])
        result[identity] = {'row': row, 'levels': levels, 'minZ': float(points[:, 2].min()), 'maxZ': float(points[:, 2].max()),
                            'radiusCm': float(np.linalg.norm(points[:, :2], axis=1).max())}
    return result


def transformed_points(points, placement):
    angle = math.radians(placement['yawDeg'])
    c, s = math.cos(angle), math.sin(angle)
    scaled = points * placement['scale']
    result = scaled.copy()
    result[:, 0], result[:, 1] = scaled[:, 0] * c - scaled[:, 1] * s, scaled[:, 0] * s + scaled[:, 1] * c
    return result + placement['positionCm']


def build(output):
    require(not output.exists(), 'Use a fresh immutable source study')
    require(sha(DIAGNOSTIC) == DIAGNOSTIC_SHA, 'Pinned seam diagnosis differs')
    context, neighborhood, buildings, manifest, report = map(read, (CONTEXT, NEIGHBORHOOD, BUILDINGS, MASTERS, NATIVE / 'exterior-import-report.json'))
    require(context['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'} and
            context['housePlacement']['streetSetbackMm'] == context['housePlacement']['eastSetbackMm'] == 3000, 'Canonical design differs')
    require(buildings['sourceSceneSha256'] == context['sourceSceneSha256'] and buildings['sourceObjSha256'] == context['sourceObjSha256'], 'Building source frame differs')
    footprints_path = DIAGNOSTIC.parent / 'soil-exposure-footprints.json'
    exposure = shape(read(footprints_path)['geometry'])
    numbers = {row['parcelNumber'] for row in neighborhood['groundDetails'] if row['authoredLandUse'] == 'ILLUSTRATIVE_MIXED_FALLOW_AND_WORN_ACCESS_UNBUILT'}
    meshes, domain, ground_rows, ground_index = source_shapes(context, numbers)
    require(len(numbers) == 65 and all('6012_26_' not in mesh['id'] for mesh in meshes), 'Exact unbuilt plot scope differs')
    protected = unary_union([Polygon(triangle) for triangle in context['protectedTrianglesCm']])
    roads = unary_union([Polygon([mesh['verticesCm'][index][:2] for index in mesh['indices'][start:start + 3]])
                         for mesh in context['meshes'] if mesh['material'] == 'context_track'
                         for start in range(0, len(mesh['indices']), 3)])
    building_shapes = [Polygon(rings[0], rings[1:]) for building in buildings['buildings'] for rings in building['polygonsCm']]
    blockers = protected.buffer(30).union(roads.buffer(20)).union(unary_union(building_shapes).buffer(150))
    allowed = domain.difference(blockers)
    # Entire tiny crowns stay outside the same full exposure footprint used to
    # remove original tufts. This adds an external low margin, never clipped
    # old clumps or new vegetation over the feather/body soil triangles.
    bands = allowed.intersection(exposure.buffer(34)).difference(exposure.buffer(.1))
    prototypes = prototype_geometry(manifest)
    paths = {Path(__file__).resolve(), ROOT / 'scripts/unreal/exterior-neighborhood-seam-diagnostic.py', DIAGNOSTIC,
             footprints_path, CONTEXT, NEIGHBORHOOD, BUILDINGS, MASTERS, NATIVE / 'exterior-import-report.json'}
    for prototype in prototypes.values():
        paths.add(Path(prototype['row']['glbPath']))
    for key in ('context_meadow', 'context_fallow'):
        recipe = report['materials']['materials'][key]['recipe']
        paths.update(Path(value['path']) for value in recipe['maps'].values())
        paths.update(Path(value['path']) for value in recipe['groundCover']['maps'].values())
    source_pins = {str(path): sha(path) for path in sorted(paths)}
    rng = random.Random(60122620261001)
    placements, budgets = [], [0, 0, 0]
    minx, miny, maxx, maxy = bands.bounds
    # A shuffled jittered grid avoids independent rows stamped on an edge.
    # Sparse low tufts complement the retained high meadow rather than doubling
    # its population. Actual source triangles prove every final placement.
    candidates = [(x + rng.uniform(-8, 8), y + rng.uniform(-8, 8))
                  for x in np.arange(minx, maxx, 22.) for y in np.arange(miny, maxy, 22.)]
    rng.shuffle(candidates)
    for x, y in candidates:
        point = Point(x, y)
        if not bands.covers(point):
            continue
        field = float(condition(x, y))
        if rng.random() > .30 + .40 * field:
            continue
        identity = rng.choices(PROTOTYPES, weights=[.78, .18, .04])[0]
        prototype = prototypes[identity]
        height = rng.uniform(3.8, 7.0)
        scale = height / (prototype['maxZ'] - prototype['minZ'])
        radius = prototype['radiusCm'] * scale
        crown = point.buffer(radius + .1, quad_segs=16)
        if not allowed.covers(crown) or crown.intersects(exposure) or not bands.covers(crown):
            continue
        hits = [ground_rows[int(index)] for index in ground_index.query(point, predicate='intersects')]
        if not hits:
            continue
        z = max(float(diag.barycentric([x, y], row['xyz']) @ np.asarray(row['xyz'])[:, 2]) for row in hits)
        triangles = [level['triangles'] for level in prototype['levels']]
        if budgets[0] + triangles[0] > 6500000:
            continue
        row = {'meshId': identity, 'positionCm': [x, y, z - prototype['minZ'] * scale], 'yawDeg': rng.uniform(0, 360),
               'scale': [scale] * 3, 'actualHeightCm': height, 'radiusCm': radius, 'sourceGroundMeshId': hits[0]['meshId'],
               'sourceGroundZCm': z, 'wholeCrownOutsideSoilExposure': True}
        placements.append(row)
        budgets = [a + b for a, b in zip(budgets, triangles)]
        if len(placements) >= 7000:
            break
    require(1000 <= len(placements) <= 7000 and budgets[0] <= 6500000, 'Compact margin population unexpected')
    output.mkdir(parents=True)
    size = 1024
    xs = BOUNDS[0] + (np.arange(size) + .5) * (BOUNDS[2] - BOUNDS[0]) / size
    ys = BOUNDS[3] - (np.arange(size) + .5) * (BOUNDS[3] - BOUNDS[1]) / size
    xx, yy = np.meshgrid(xs, ys)
    field = condition(xx, yy)
    pixels = np.zeros((size, size, 4), dtype=np.uint8)
    pixels[:, :, 0] = np.rint(field * 255).astype(np.uint8)
    pixels[:, :, 1] = 255
    pixels[:, :, 3] = 255
    image_path = output / 'continuous-ground-condition.png'
    Image.fromarray(pixels, 'RGBA').save(image_path)
    meadow = report['materials']['materials']['context_meadow']['recipe']
    fallow = report['materials']['materials']['context_fallow']['recipe']
    differences = []
    for x in np.linspace(5200, 6200, 101):
        for y in np.linspace(14800, 16400, 101):
            a = common_response(x, y, meadow, fallow)
            b = common_response(x + 1, y, meadow, fallow)
            differences.append(abs(a['coverAmount'] - b['coverAmount']))
    bindings = [{'sourceMeshId': mesh['id'], 'expectedMaterialKey': mesh['material'],
                 'proposedSharedMaterialKey': 'context_continuous_unbuilt_ground',
                 'nativeActor': report['geometry']['actors'][mesh['id']], 'nativeMesh': report['geometry']['meshes'][mesh['id']],
                 'sourceGeometrySha256': hashlib.sha256(json.dumps(mesh, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                 'sourceVerticesAndIndicesUnchanged': True} for mesh in meshes]
    groups = {}
    for row in placements:
        cell = [math.floor(row['positionCm'][index] / 3000) for index in (0, 1)]
        identity = 'EX_transition_' + '_'.join(map(str, cell)) + '_' + row['meshId']
        groups.setdefault(identity, {'id': identity, 'meshId': row['meshId'], 'instances': [], 'cullStartCm': 3200,
                                     'cullEndCm': 4000, 'castShadow': False, 'qualityDetail': False, 'collision': 'NoCollision'})['instances'].append(
                                         {key: row[key] for key in ('positionCm', 'yawDeg', 'scale')})
    proposal = {'schemaVersion': 1, 'owner': OWNER, 'generatorSha256': sha(__file__), 'status': 'source-only-neighborhood-transition-study-native-pending',
                'generatedAtUtc': datetime.now(timezone.utc).isoformat(), 'activeDesign': context['activeDesign'], 'housePlacement': context['housePlacement'],
                'sourceSceneSha256': context['sourceSceneSha256'], 'sourceObjSha256': context['sourceObjSha256'], 'inputFiles': source_pins,
                'sourceContext': {'path': str(CONTEXT), 'sha256': sha(CONTEXT)}, 'sourceNeighborhood': {'path': str(NEIGHBORHOOD), 'sha256': sha(NEIGHBORHOOD)},
                'sourceDiagnosis': {'path': str(DIAGNOSTIC), 'sha256': DIAGNOSTIC_SHA},
                'conditionTexture': {'path': str(image_path), 'sha256': sha(image_path), 'width': size, 'height': size,
                    'pixelFormat': 'RGBA8', 'sRGB': False, 'worldBoundsCm': BOUNDS,
                    'worldCmToUvRows': [[1 / 36000, 0, .5], [0, -1 / 36000, .5]],
                    'channels': {'R': 'Artist spatial condition0..1; no parcel label/photo/ownership input', 'G': 'Extent coverage1', 'B': 'Unused0', 'A': 'Opaque255'},
                    'use': 'Source prototype only; optional future ordinary linear mip sample. No material/runtime implementation included.'},
                'materialBindingProposal': bindings,
                'sharedPbrResponseProposal': {'materialKey': 'context_continuous_unbuilt_ground', 'kind': 'ground',
                    'reuseExactly': ['context_meadow/context_fallow shared sparse_grass earth maps', 'existing Grass004 groundCover maps', 'world-space metric UV/stochastic sampling', 'old ortho protection/camera-distance blend'],
                    'coverAmount': '.34+.40*Condition', 'tint': 'lerp(existing fallow tint,existing meadow tint,Condition)',
                    'albedoScale': '.74+.04*Condition', 'normalStrength': '.70-.05*Condition',
                    'allResponseRangesWithinExistingTwoRecipes': True, 'globalDarkening': False,
                    'privateLawnAndSourceAlbedosUnchanged': True, 'futureAdditionalMaterialCount': 1, 'futureOptionalAdditionalTextureCount': 1},
                'sourceResponseComparison': {'beforeClassCoverRanges': {'context_meadow': [.70, .78], 'context_fallow': [.30, .38]},
                    'beforeSameWorldPointClassCoverStep': .40, 'afterSameWorldPointClassCoverStep': 0.,
                    'afterMaximumOneCmCoverAmountChangeInObservedSeamRegion': max(differences),
                    'comparison': 'CPU authored cover/tint/scale parameters only, not a reconstruction of native pixels/lighting/PBR filtering.'},
                'transitionPlacements': placements, 'groups': list(groups.values()), 'prototypes': [prototypes[key]['row'] for key in PROTOTYPES],
                'edgeDomainCm': mapping(bands), 'targetGroundDomainCm': mapping(allowed),
                'edgePolicy': {'wholeCrownOutsideSameFullSoilFootprint': True, 'entireAllLodTrianglesInsideAllowedSourceGround': True,
                    'originalRemovalIndicesUnchanged': True, 'sourceRootsNeverRestoredOrMoved': True, 'newCompactHeightCm': [3.8, 7.0],
                    'outsideSoilMarginCm': .1, 'outerBandWidthCm': 34, 'protectedPrivateBufferCm': 30, 'roadBufferCm': 20,
                    'officialBuildingBufferCm': 150, 'cullDistancesCm': [3200, 4000]},
                'summary': {'unbuiltParcels': len(numbers), 'targetGroundMeshes': len(meshes), 'transitionInstances': len(placements),
                    'transitionGroups': len(groups), 'allLodTriangles': budgets, 'edgeDomainAreaM2': bands.area / 10000,
                    'conditionMinimum': float(field.min()), 'conditionMaximum': float(field.max())},
                'preservation': {'legalBoundariesUnchanged': True, 'sourceGroundAndCollisionUnchanged': True,
                    'officialBuildingsUnchanged': True, 'noFabricatedBuiltNeighbors': True, 'croppedArableVineyardDomainsDistinct': True,
                    'allOriginalVegetationUnchanged': True, 'originalWholeCrownRemovalsUnchanged': True},
                'nativeVisualAccepted': False, 'performanceAccepted': False,
                'limits': ['Artist finish/vegetation interpretation only; no measured land use, botany or surveying claims.',
                    'Existing source GLBs/PBR pixels are reused unchanged; new plants are source-only placement proposals.',
                    'Small external clumps can soften the crown-removal rim but do not repopulate the inner feather footprint.',
                    'A new shared material binding, shader contract and native same-view comparison are required before use. R11 keeps R10 context unchanged.']}
    for path, digest in source_pins.items():
        require(sha(path) == digest, 'Pinned original changed during study')
    write(output / 'transition-plan.json', proposal)
    write(output / 'material-response-proposal.json', proposal['sharedPbrResponseProposal'])
    write(output / 'prototype-manifest.json', {'schemaVersion': 1, 'owner': OWNER, 'sourceMasterManifest': {'path': str(MASTERS), 'sha256': sha(MASTERS)},
                                               'meshes': proposal['prototypes'], 'sourcePixelsAndGeometryUnmodified': True})
    write(output / 'summary.json', {'plan': str(output / 'transition-plan.json'), 'sha256': sha(output / 'transition-plan.json'), **proposal['summary'],
                                  'nativeVisualAccepted': False, 'performanceAccepted': False})
    print(json.dumps({'plan': str(output / 'transition-plan.json'), 'sha256': sha(output / 'transition-plan.json'), **proposal['summary']}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(ROOT / 'output/unreal'), 'Use fresh isolated Unreal output')
    build(output)


if __name__ == '__main__':
    main()
