"""One isolated source-only continuous meadow layout candidate; no Unreal writes.

Original R8/R3 arrays remain frozen. The future candidate removes unbuilt soil
overlays, restores eligible original small crowns, and proposes height-only
changes over one world-space field. Plots are source plans, not native renders.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import shapely
from shapely.geometry import Polygon, shape, mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-meadow-continuous-study.py'
DESTINATION = ROOT / 'output/unreal/exterior-meadow-continuous-20261001-r1-study'
SOURCES = {
    'context': ('exterior-context-20260927-r8/context-plan.json', '4b0b72a5f39d5bec3915846abb159147a4cf73b65cbf920884ffe7dd762a4176'),
    'neighborhood': ('exterior-context-20260930-r3/neighborhood-details.json', '54a34a1cdbe372ad213a61a086abfb1267b7290b80e6a5029d24b0e58ee4b4cb'),
    'buildings': ('exterior-buildings-20260926-r2/building-plan.json', 'fd8b61e6fa5c462a851fab26a2ec5d5edcbec9d07bb80e1d6e7163b6568fb318'),
    'transition': ('exterior-neighborhood-transition-20261001-r1-study/transition-plan.json', '2be538a9311282d9b8485d925fa070b3984b50cea852ea2e7406ed1699448ef5'),
    'soil': ('exterior-neighborhood-seam-diagnostic-20261001-r1/soil-exposure-footprints.json', '5972d3bc5fc2ab5f9f8d535c7ee445a174cb598a9df4ef4b471e5cab2b34101e'),
    'infill': ('exterior-meadow-infill-20261001-r1b-study/meadow-infill-plan.json', '526f51e02cba8a89292ad2b0a90a975c15b48189c985a1a35c92510caee1529a'),
    'nativeReceipt': ('exterior-20261001-r14a/exterior-import-report.json', '36312e43a71de2c2a083a2d0abbc737ea18bb7ada25f2b7de23024dd256f4179'),
    'lawnPrototypes': ('rural-context-20260923-r4/lawn-geometry/prototypes.json', '226b8dc0313e526c356c834ea8a3a775aafe612732ac90b25819d0fa53a2ef62'),
}
EXPECTED_SOIL = {
    'neighborhood_m1_1_soil_exposure': (15068, 0),
    'neighborhood_0_1_soil_exposure': (28899, 0),
    'neighborhood_m1_0_soil_exposure': (16294, 0),
    'neighborhood_m2_0_soil_exposure': (9295, 0),
    'neighborhood_0_0_soil_exposure': (26501, 31),
    'neighborhood_m1_m1_soil_exposure': (4291, 103),
    'neighborhood_m2_m1_soil_exposure': (975, 96),
    'neighborhood_0_m1_soil_exposure': (2069, 414),
    'neighborhood_m2_m2_soil_exposure': (0, 269),
    'neighborhood_m1_m2_soil_exposure': (0, 76),
    'neighborhood_0_m2_soil_exposure': (0, 260),
    'neighborhood_1_m2_soil_exposure': (0, 294),
    'neighborhood_1_m1_soil_exposure': (0, 313),
    'neighborhood_1_0_soil_exposure': (0, 533),
    'neighborhood_1_1_soil_exposure': (0, 412),
}
CULTIVATED = ['6022', '6030', '6031', '6032', '6033', '6040', '6041']
ROOT_ARRAYS = ('meadowBladePlacements', 'meadowUnderstoryPlacements')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def encode(value):
    return (json.dumps(value, separators=(',', ':'), allow_nan=False) + '\n').encode()


def triangles(mesh):
    return np.asarray(mesh['verticesCm'], dtype=np.float64)[np.asarray(mesh['indices'], dtype=np.int64).reshape(-1, 3)]


def triangle_union(meshes):
    return unary_union([Polygon(row[:, :2]) for mesh in meshes for row in triangles(mesh)])


def value_noise(x, y, length, seed):
    # Continuous interpolation in world cm, shared by every parcel and root.
    x, y = np.asarray(x) / length, np.asarray(y) / length
    ix, iy = np.floor(x), np.floor(y)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    def hashed(a, b):
        v = np.sin(a * 127.1 + b * 311.7 + seed) * 43758.5453
        return v - np.floor(v)
    lo = hashed(ix, iy) * (1 - fx) + hashed(ix + 1, iy) * fx
    hi = hashed(ix, iy + 1) * (1 - fx) + hashed(ix + 1, iy + 1) * fx
    return lo * (1 - fy) + hi * fy


def smoothstep(a, b, value):
    t = np.clip((value - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def growth_field(x, y, roads):
    condition = (.55 * value_noise(x, y, 2400, 31) +
                 .30 * value_noise(x, y, 1200, 67) +
                 .15 * value_noise(x, y, 400, 109))
    # Only existing source road geometry supplies a disturbance edge. No
    # invented per-parcel track, mower lane, soil island or parcel-ID reset.
    distance = shapely.distance(shapely.points(x, y), roads)
    edge = 1 - smoothstep(20, 180, distance)
    tall = smoothstep(.54, .76, condition) * (1 - .85 * edge)
    fine = value_noise(x, y, 110, 173)
    blade_height = 5 + 2.5 * condition + 12 * tall + .9 * fine - .9 * edge
    understory_height = 2.2 + 3.1 * condition + 1.6 * tall + .5 * fine - .4 * edge
    return condition, tall, edge, blade_height, understory_height


def prototypes(source, native):
    result = {}
    require(len(source) == 12, 'Expected four original prototypes with three LODs')
    for variant in range(4):
        identity = f'LawnTuft{variant}'
        levels = sorted([row for row in source if row['variant'] == variant], key=lambda x: x['lod'])
        require([row['lod'] for row in levels] == [0, 1, 2], 'Prototype LOD ordering differs')
        point_sets, proof = [], []
        for row, expected in zip(levels, [256, 64, 24]):
            points = np.asarray(row['verticesMm'], dtype=np.float64) / 10
            faces = np.asarray(row['faces'], dtype=np.int64)
            normals = np.asarray(row['normals'], dtype=np.float64)
            require(points.ndim == 2 and points.shape[1] == 3 and np.isfinite(points).all(), 'Invalid prototype positions')
            require(faces.shape == (expected, 3) and faces.min() >= 0 and faces.max() < len(points), 'Invalid prototype connectivity/count')
            require(normals.shape == points.shape and np.isfinite(normals).all() and
                    np.allclose(np.linalg.norm(normals, axis=1), 1, atol=1e-5), 'Invalid prototype normals')
            for key in ('uv0', 'uv1'):
                uvs = np.asarray(row[key], dtype=np.float64)
                require(uvs.shape == (len(points), 2) and np.isfinite(uvs).all(), 'Invalid prototype UV decoder')
            vertices = points[faces]
            areas = np.linalg.norm(np.cross(vertices[:, 1] - vertices[:, 0], vertices[:, 2] - vertices[:, 0]), axis=1)
            require(np.all(areas > 1e-12), 'Degenerate prototype faces')
            point_sets.append(points)
            proof.append({'id': row['id'], 'lod': row['lod'], 'triangles': len(faces), 'vertices': len(points),
                          'decodedRecordSha256': object_sha(row)})
        points = np.concatenate(point_sets)
        report = native['nativeMeadow']['prototypes'][identity]
        require([p['triangles'] for p in report['lodProofs']] == [256, 64, 24] and
                all(p['triangleConnectivityWindingVerified'] and p['uvChannelsVerified'] == [0, 1] for p in report['lodProofs']),
                'Frozen R14 original native prototype readback differs')
        require(identity + '_LOD0.' in report['mesh'], 'Native original prototype path differs')
        result[identity] = {'id': identity, 'nativeMesh': report['mesh'], 'nativeMaterial': report['material'],
                            'lodScreens': report['lodScreens'], 'lodTriangles': [256, 64, 24],
                            'sourceMinZCm': float(points[:, 2].min()), 'sourceMaxZCm': float(points[:, 2].max()),
                            'sourceRadiusCm': float(np.linalg.norm(points[:, :2], axis=1).max()), 'decodedLods': proof,
                            'nativeReceiptOnlyProvesHistoricalOriginalAssets': True}
    return result


def soil_subsets(neighborhood, unbuilt, cultivated):
    omit_ids, unchanged_ids, replacements, records, plot_rows = [], [], [], [], []
    total_omit, total_keep, omitted_area, retained_area = 0, 0, 0., 0.
    # The triangle centroids are parcel-interior even when ring vertices sit on
    # the boundary. The 1e-6 cm tolerance handles floating point edge noise only.
    unbuilt, cultivated = unbuilt.buffer(1e-6), cultivated.buffer(1e-6)
    shapely.prepare(unbuilt)
    shapely.prepare(cultivated)
    for mesh in neighborhood['meshes']:
        if mesh['material'] != 'context_soil_exposure':
            continue
        rows = triangles(mesh)
        centers = rows[:, :, :2].mean(axis=1)
        points = shapely.points(centers)
        remove = shapely.covers(unbuilt, points)
        keep = shapely.covers(cultivated, points)
        require(np.all(remove ^ keep), 'Soil triangle is unclassified or ambiguously classified')
        remove_n, keep_n = int(remove.sum()), int(keep.sum())
        require((remove_n, keep_n) == EXPECTED_SOIL[mesh['id']], 'Measured soil membership changed')
        areas = np.abs(np.cross(rows[:, 1, :2] - rows[:, 0, :2], rows[:, 2, :2] - rows[:, 0, :2])) / 2 / 10000
        omitted_area += float(areas[remove].sum())
        retained_area += float(areas[keep].sum())
        total_omit += remove_n
        total_keep += keep_n
        record = {'sourceMeshId': mesh['id'], 'originalMeshSha256': object_sha(mesh),
                  'omittedTriangleCount': remove_n, 'retainedTriangleCount': keep_n,
                  'omittedAreaM2': float(areas[remove].sum()), 'retainedAreaM2': float(areas[keep].sum()),
                  'keepSourceTriangleOrdinals': np.flatnonzero(keep).tolist(),
                  'omitSourceTriangleOrdinals': np.flatnonzero(remove).tolist()}
        if not keep_n:
            omit_ids.append(mesh['id'])
            record['action'] = 'OMIT_UNBUILT_ONLY_OVERLAY'
        elif not remove_n:
            unchanged_ids.append(mesh['id'])
            record['action'] = 'KEEP_CULTIVATED_OVERLAY_EXACT'
        else:
            subset = copy.deepcopy(mesh)
            subset['indices'] = np.asarray(mesh['indices']).reshape(-1, 3)[keep].reshape(-1).tolist()
            # All original vertices/UVs and any normal/tangent arrays stay exact;
            # unused vertices are intentional. Only triangle indices are filtered.
            require(all(subset[k] == mesh[k] for k in mesh if k != 'indices'), 'Soil subset changed vertex attributes/metadata')
            require(subset['indices'] == [mesh['indices'][3 * i + k] for i in np.flatnonzero(keep) for k in range(3)],
                    'Soil subset changed triangle order/winding')
            record['action'] = 'REPLACE_WITH_EXACT_CULTIVATED_INDEX_SUBSET'
            record['replacementMeshSha256'] = object_sha(subset)
            record['attributeKeysUnchanged'] = [k for k in mesh if k != 'indices']
            record['normalsAndTangents'] = {k: 'EXACT_UNCHANGED' if k in mesh else 'ABSENT_IN_ORIGINAL_SOURCE_RECORD'
                                            for k in ('normals', 'tangents')}
            replacements.append(subset)
        records.append(record)
        plot_rows.append((rows, remove, keep))
    require(set(EXPECTED_SOIL) == {r['sourceMeshId'] for r in records}, 'Soil chunk inventory differs')
    require((total_omit, total_keep, len(omit_ids), len(replacements), len(unchanged_ids)) == (103392, 2801, 4, 4, 7),
            'Soil omission/subset aggregate differs')
    return {'omitMeshIds': omit_ids, 'unchangedCultivatedMeshIds': unchanged_ids, 'triangles': records,
            'omittedTriangles': total_omit, 'retainedTriangles': total_keep, 'omittedAreaM2': omitted_area,
            'retainedCultivatedAreaM2': retained_area, 'replacementRecordsFile': 'cultivated-soil-subsets.json',
            'futureNeighborhoodMeshCount': len(neighborhood['meshes']) - len(omit_ids),
            'futureNeighborhoodTriangles': neighborhood['summary']['triangles'] - total_omit,
            'wholeMixedMeshRecolorForbidden': True}, replacements, plot_rows


def ground_z_error(restored, meshes):
    lookup = {row['id']: row for row in meshes}
    grouped = {}
    for row in restored:
        grouped.setdefault(row['sourceGroundMeshId'], []).append(row)
    maximum = 0.
    for identity, placements in grouped.items():
        require(identity in lookup, 'Restored root source ground is outside target 65')
        xyz = triangles(lookup[identity])
        tree = STRtree([Polygon(t[:, :2]) for t in xyz])
        points = shapely.points([p['positionCm'][:2] for p in placements])
        pairs = tree.query(points, predicate='intersects')
        ground = np.full(len(placements), np.nan)
        for index, triangle in zip(*pairs):
            t = xyz[int(triangle)]
            x, y = placements[int(index)]['positionCm'][:2]
            a, b, c = t[:, :2]
            determinant = np.cross(b - a, c - a)
            require(abs(determinant) > 1e-12, 'Degenerate target ground triangle')
            u, v = np.cross(np.array([x, y]) - a, c - a) / determinant, np.cross(b - a, np.array([x, y]) - a) / determinant
            z = (1 - u - v) * t[0, 2] + u * t[1, 2] + v * t[2, 2]
            ground[int(index)] = z if np.isnan(ground[int(index)]) else max(z, ground[int(index)])
        require(np.isfinite(ground).all(), 'Restored root lacks source ground triangle')
        errors = np.abs(ground - [p['positionCm'][2] for p in placements])
        maximum = max(maximum, float(errors.max()))
    require(maximum < 1e-4, 'Restored original Z differs from actual source surface')
    return maximum


def root_candidate(context, neighborhood, allowed, roads, proto):
    shapely.prepare(allowed)
    restored, overrides, original_rows = [], {}, {}
    guards = {}
    for name in ROOT_ARRAYS:
        source = context[name]
        original_rows[name] = {'count': len(source), 'canonicalSha256': object_sha(source)}
        xy = np.asarray([p['positionCm'][:2] for p in source])
        points = shapely.points(xy)
        center_inside = shapely.covers(allowed, points)
        safe = center_inside & (shapely.distance(points, allowed.boundary) >= 14.1)
        removed_indices = neighborhood['groundDetailRemovedPlacementIndices'][name]
        require(removed_indices == sorted(set(removed_indices)), 'Original removal indices lack strict source ordering')
        removed = np.zeros(len(source), dtype=bool)
        removed[removed_indices] = True
        restore = np.flatnonzero(removed & safe)
        retained = np.flatnonzero(~removed & safe)
        guards[name] = {'removedCentersInsideAllowed': int(np.sum(removed & center_inside)),
                        'restoredFull141mmCrowns': len(restore), 'retainedHeightOnlyOverrides': len(retained),
                        'removedCenterValidCrownRejected': int(np.sum(removed & center_inside & ~safe))}
        condition, tall, edge, blades, low = growth_field(xy[:, 0], xy[:, 1], roads)
        heights = blades if name == 'meadowBladePlacements' else low
        overrides[name] = [[int(index), float(heights[index])] for index in retained]
        for index in restore:
            original = source[int(index)]
            require(original['radiusCm'] == 14, 'Only original 14 cm crowns may be restored')
            restored.append({'sourceArray': name, 'sourceIndex': int(index), 'originalRowSha256': object_sha(original),
                             'positionCm': original['positionCm'], 'yawDeg': original['yawDeg'], 'radiusCm': original['radiusCm'],
                             'originalHeightCm': original['heightCm'], 'proposedHeightCm': float(heights[index]),
                             'sourceGroundMeshId': original['sourceMeshId'], 'growthCondition': float(condition[index]),
                             'tallGrowthAmount': float(tall[index]), 'existingRoadEdgeDisturbance': float(edge[index])})
    require(len(restored) == 39834 and guards['meadowBladePlacements']['restoredFull141mmCrowns'] == 34447 and
            guards['meadowUnderstoryPlacements']['restoredFull141mmCrowns'] == 5387, 'Eligible ordered restoration differs')
    groups, rng = {}, random.Random(260920263)
    for row in restored:
        identity = f'LawnTuft{rng.randrange(4)}'
        prototype = proto[identity]
        x, y, z = row['positionCm']
        gid = f'EX_meadow_restored_{math.floor(x / 2000)}_{math.floor(y / 2000)}_{identity}'
        scale_xy = row['radiusCm'] / prototype['sourceRadiusCm']
        scale_z = row['proposedHeightCm'] / prototype['sourceMaxZCm']
        require(prototype['sourceMinZCm'] == 0, 'Original native prototype root is not zero')
        instance = {'positionCm': row['positionCm'], 'yawDeg': row['yawDeg'], 'scale': [scale_xy, scale_xy, scale_z],
                    'sourceArray': row['sourceArray'], 'sourceIndex': row['sourceIndex']}
        row.update(meshId=identity, groupId=gid, scale=instance['scale'])
        groups.setdefault(gid, {'id': gid, 'meshId': identity, 'nativeMesh': prototype['nativeMesh'],
                               'nativeMaterial': prototype['nativeMaterial'], 'instances': [], 'role': 'grass',
                               'qualityDetail': True, 'densityScaling': True, 'cullStartCm': 7200, 'cullEndCm': 9000,
                               'castShadow': False, 'collision': 'NoCollision', 'navigation': False})['instances'].append(instance)
    require(len(groups) == 164, 'Restoration grouping differs')
    return restored, list(groups.values()), overrides, guards, original_rows


def image_bytes(image):
    stream = io.BytesIO()
    image.save(stream, format='PNG')
    return stream.getvalue()


def polygons(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == 'Polygon':
        return [geometry]
    return [p for g in geometry.geoms for p in polygons(g)]


def plots(allowed, cultivated, soil, protected, roads, buildings, soil_rows, restored, bounds):
    size = 1100
    x0, y0, x1, y1 = bounds
    def pixel(xy):
        return ((xy[0] - x0) / (x1 - x0) * (size - 1), (y1 - xy[1]) / (y1 - y0) * (size - 1))
    def layer(geometry, fill, background=0):
        image = Image.new('L', (size, size), background)
        draw = ImageDraw.Draw(image)
        for p in polygons(geometry):
            draw.polygon([pixel(v) for v in p.exterior.coords], fill=fill)
            for ring in p.interiors:
                draw.polygon([pixel(v) for v in ring.coords], fill=background)
        return image
    xs = x0 + (np.arange(size) + .5) * (x1 - x0) / size
    ys = y1 - (np.arange(size) + .5) * (y1 - y0) / size
    xx, yy = np.meshgrid(xs, ys)
    condition, tall, edge, high, low = growth_field(xx.reshape(-1), yy.reshape(-1), roads)
    condition, tall, edge = [v.reshape(size, size) for v in (condition, tall, edge)]
    rgb = np.empty((size, size, 3), dtype=np.uint8)
    rgb[:, :, 0] = 73 + condition * 33 + edge * 19
    rgb[:, :, 1] = 110 + condition * 41 - tall * 20 - edge * 10
    rgb[:, :, 2] = 53 + condition * 16
    candidate = Image.new('RGB', (size, size), '#e0ddd1')
    candidate.paste(Image.fromarray(rgb), mask=layer(allowed, 255))
    before = Image.new('RGB', (size, size), '#e0ddd1')
    before.paste('#82a650', mask=layer(allowed, 255))
    before.paste('#775139', mask=layer(soil, 255))
    crop_soil = soil.intersection(cultivated)
    for image in (before, candidate):
        image.paste('#bdab72', mask=layer(cultivated, 255))
        image.paste('#775139', mask=layer(crop_soil, 255))
        image.paste('#929798', mask=layer(roads, 255))
        image.paste('#cb776d', mask=layer(protected, 255))
        image.paste('#797579', mask=layer(buildings, 255))
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 21)
    small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 17)
    def labelled(image, title, subtitle):
        result = Image.new('RGB', (size, size + 92), '#f8f7f2')
        result.paste(image, (0, 76))
        draw = ImageDraw.Draw(result)
        draw.text((16, 10), title, fill='#151e14', font=font)
        draw.text((16, 39), subtitle, fill='#3c4137', font=small)
        draw.text((16, size + 79), 'World X right / Y up; source coordinates in cm; 50 m scale shown below', fill='#3c4137', font=small)
        scale = round(5000 / (x1 - x0) * size)
        draw.line((size - scale - 24, size + 58, size - 24, size + 58), fill='black', width=4)
        draw.text((size - scale - 24, size + 30), '50 m', fill='black', font=small)
        return result
    left = labelled(before, 'R14 source layout: repeated brown soil overlays', 'Schematic source footprint colors; native light/material pixels are not represented')
    right = labelled(candidate, 'One continuous meadow source candidate', 'Only cultivated soil retained; lower sward with coherent taller islands; native pending')
    comparison = Image.new('RGB', (size * 2 + 16, size + 92), '#f8f7f2')
    comparison.paste(left, (0, 0))
    comparison.paste(right, (size + 16, 0))
    mask = Image.new('RGB', (size, size), '#e0ddd1')
    mask.paste('#c8d4b5', mask=layer(allowed, 255))
    mask_draw = ImageDraw.Draw(mask)
    for rows, remove, keep in soil_rows:
        for triangle, removed in zip(rows, remove):
            mask_draw.polygon([pixel(v) for v in triangle], fill='#b85b48' if removed else '#b79b49')
    mask.paste('#929798', mask=layer(roads, 255))
    mask.paste('#cb776d', mask=layer(protected, 255))
    mask = labelled(mask, 'Actual source soil triangle membership', 'Red: omit 103,392 unbuilt triangles; gold: retain all 2,801 cultivated triangles')
    roots = candidate.copy()
    root_draw = ImageDraw.Draw(roots)
    for row in restored:
        px, py = pixel(row['positionCm'])
        color = '#c5cc64' if row['sourceArray'] == 'meadowUnderstoryPlacements' else '#1a512f'
        root_draw.point((round(px), round(py)), fill=color)
    roots = labelled(roots, '39,834 exact ordered source roots proposed for restoration', 'Dark: 34,447 blade roots; yellow: 5,387 understory; whole 14.1 cm guard; no tall cover')
    data = {'planview-comparison.png': image_bytes(comparison), 'soil-triangle-mask.png': image_bytes(mask),
            'restored-root-map.png': image_bytes(roots)}
    field_image = np.zeros((size, size, 4), dtype=np.uint8)
    field_image[:, :, 0] = np.rint(condition * 255).astype(np.uint8)
    field_image[:, :, 1] = np.rint(tall * 255).astype(np.uint8)
    field_image[:, :, 2] = np.rint(edge * 255).astype(np.uint8)
    field_image[:, :, 3] = np.asarray(layer(allowed, 255))
    data['continuous-growth-field.png'] = image_bytes(Image.fromarray(field_image))
    return data, {'pixelDimensions': [size, size], 'worldBoundsCm': bounds,
                  'channels': {'R': 'condition', 'G': 'tall growth amount', 'B': 'disturbance from existing source road edges',
                               'A': 'allowed target mask'}, 'sRGB': False,
                  'worldCmToUvRows': [[1 / (x1 - x0), 0, -x0 / (x1 - x0)], [0, -1 / (y1 - y0), y1 / (y1 - y0)]],
                  'use': 'Source diagnostic; analytic field drives roots. Quantized PNG is not a native material input.'}


def build(output):
    require(output == DESTINATION and not output.exists(), 'Use the authorized fresh isolated R1 study directory')
    paths = {name: ROOT / 'output/unreal' / row[0] for name, row in SOURCES.items()}
    pins = {str(paths[name]): row[1] for name, row in SOURCES.items()}
    pins[str(ROOT / OWNER)] = sha(ROOT / OWNER)
    for name, path in paths.items():
        require(sha(path) == SOURCES[name][1], f'Frozen input pin differs: {name}')
    sources = {name: read(path) for name, path in paths.items()}
    context, neighborhood, buildings = [sources[name] for name in ('context', 'neighborhood', 'buildings')]
    transition, infill, native = [sources[name] for name in ('transition', 'infill', 'nativeReceipt')]
    require(context['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'} and
            context['housePlacement']['streetSetbackMm'] == context['housePlacement']['eastSetbackMm'] == 3000,
            'Active C/B/B and 3000 mm placement differs')
    for source in (neighborhood, buildings, transition, infill):
        require(all(source[key] == context[key] for key in ('activeDesign', 'housePlacement', 'sourceSceneSha256', 'sourceObjSha256')),
                'Frozen source frame or protected design differs')
    ids = {row['sourceMeshId'] for row in transition['materialBindingProposal']}
    meshes = [mesh for mesh in context['meshes'] if mesh['id'] in ids]
    require(len(meshes) == 65 and len(ids) == 65 and not any('6012_26_' in mesh['id'] for mesh in meshes), 'Target 65 identity differs')
    crop_ids = {row['meshId'] for row in context['surfaces'] if row['parcelNumber'] in CULTIVATED and row['finish'] == 'surface'}
    crop_meshes = [mesh for mesh in context['meshes'] if mesh['id'] in crop_ids]
    require(len(crop_meshes) == 7, 'Cultivated source parcel set differs')
    raw_domain, cultivated = triangle_union(meshes), triangle_union(crop_meshes)
    protected = unary_union([Polygon(t) for t in context['protectedTrianglesCm']])
    roads = triangle_union([m for m in context['meshes'] if m['material'] == 'context_track'])
    building_geometry = unary_union([Polygon(rings[0], rings[1:]) for b in buildings['buildings'] for rings in b['polygonsCm']])
    blockers = protected.buffer(30).union(roads.buffer(20)).union(building_geometry.buffer(150))
    allowed = raw_domain.difference(blockers)
    difference = allowed.symmetric_difference(shape(transition['targetGroundDomainCm'])).area
    require(difference < 1e-5 and allowed.symmetric_difference(shape(infill['allowedDomainCm'])).area < 1e-5,
            'Independently derived architectural/private/road/building domain differs')
    soil = shape(sources['soil']['geometry'])
    print('Verified frozen inputs and actual 65-surface domain', flush=True)
    soil_plan, subsets, soil_rows = soil_subsets(neighborhood, raw_domain, cultivated)
    proto = prototypes(sources['lawnPrototypes'], native)
    restored, groups, overrides, guard, original_arrays = root_candidate(context, neighborhood, allowed, roads, proto)
    max_z = ground_z_error(restored, meshes)
    require(len(transition['transitionPlacements']) == 7000 and len(transition['groups']) == 158 and
            len(infill['infillPlacements']) == 33483 and len(infill['groups']) == 101, 'Old visual retirement inventory differs')
    print('Validated exact soil triangle subsets and 39,834 restoration roots / 164 groups', flush=True)
    bounds = [-18000., -18000., 18000., 18000.]
    images, field_texture = plots(allowed, cultivated, soil, protected, roads, building_geometry, soil_rows, restored, bounds)
    heights = [row['proposedHeightCm'] for row in restored]
    override_count = sum(len(v) for v in overrides.values())
    nonsoil = [m for m in neighborhood['meshes'] if m['material'] != 'context_soil_exposure']
    preservation = {'protectedOriginalArrays': original_arrays,
                    'groundCoverPlacements': {'count': len(context['groundCoverPlacements']), 'canonicalSha256': object_sha(context['groundCoverPlacements']), 'heightOrPopulationChangesProposed': False},
                    'sourceContextGroupsSha256': object_sha(context['groups']), 'allSourceContextGroupsUnchanged': True,
                    'sourceGround65RecordsSha256': object_sha(meshes), 'sourceGround65TopologyAndMaterialSourceKeysUnchanged': True,
                    'protectedPrivateGeometrySha256': object_sha(context['protectedTrianglesCm']),
                    'officialBuildingsSha256': object_sha(buildings['buildings']),
                    'neighborhoodNonSoilMeshesSha256': object_sha(nonsoil), 'neighborhoodNonSoilMeshesUnchanged': len(nonsoil),
                    'neighborhoodBuildingRecordsSha256': object_sha(neighborhood['buildings']),
                    'lanePebblePlacementsSha256': object_sha(neighborhood['lanePebblePlacements']), 'lanePebblesUnchanged': len(neighborhood['lanePebblePlacements']),
                    'sourceRemovalIndicesSha256': object_sha(neighborhood['groundDetailRemovedPlacementIndices']),
                    'oldRemovalIndicesPreservedAsHistoryOnly': True, 'oldRemovalAppearanceConstraintRetired': True,
                    'cultivatedSourceParcels': CULTIVATED, 'allSevenCultivatedRowsAndMaterialsPreserved': True,
                    'houseCBBAndBoth3000mmSetbacksUnchanged': True, 'legalBoundariesAndGroundCollisionUnchanged': True,
                    'noOriginalFileModified': True}
    old_budget = [a + b for a, b in zip(transition['summary']['allLodTriangles'], [33483 * v for v in (48, 42, 36)])]
    restored_budget = [39834 * value for value in (256, 64, 24)]
    summary = {'targetUnbuiltParcels': 65, 'cultivatedParcelsPreserved': 7, 'allowedDomainAreaM2': allowed.area / 10000,
               'unbuiltSoilAreaRemovedM2': soil_plan['omittedAreaM2'], 'unbuiltSoilWithinAllowedM2': soil.intersection(allowed).area / 10000,
               'old15cmContactOutsideSoilM2': soil.buffer(15).difference(soil).intersection(allowed).area / 10000,
               'soilTrianglesOmitted': soil_plan['omittedTriangles'], 'cultivatedSoilTrianglesRetained': soil_plan['retainedTriangles'],
               'restoredInstances': len(restored), 'restoredGroups': len(groups), 'retainedHeightOnlyOverrides': override_count,
               'restoredAllLodTriangles': restored_budget, 'retiredOldVisualInstances': 40483, 'retiredOldVisualGroups': 259,
               'netInstanceDeltaAgainstR14': -649, 'netGroupDeltaAgainstR14': -95,
               'retiredOldVisualAllLodTriangles': old_budget, 'netPlantAllLodTriangleDeltaAgainstR14': [a - b for a, b in zip(restored_budget, old_budget)],
               'additionalScannedMeshes': 0, 'additionalGrassPrototypeAssets': 0, 'newPopulationBeyondOrderedRestoration': 0,
               'restoredProposedHeightRangeCm': [min(heights), max(heights)], 'sourceGroundMaximumRootZErrorCm': max_z}
    plan = {'schemaVersion': 1, 'owner': OWNER, 'generatorSha256': pins[str(ROOT / OWNER)],
            'status': 'MEASURED_CONTINUOUS_MEADOW_LAYOUT_SOURCE_ONLY_NATIVE_PENDING', 'generatedAtUtc': datetime.now(timezone.utc).isoformat(),
            'activeDesign': context['activeDesign'], 'housePlacement': context['housePlacement'],
            'sourceSceneSha256': context['sourceSceneSha256'], 'sourceObjSha256': context['sourceObjSha256'], 'inputFiles': pins,
            'candidateCount': 1, 'sweepOrGridOfCandidates': False, 'integrationAuthorized': False,
            'targetGroundDomainCm': mapping(allowed), 'materialBindingProposal': transition['materialBindingProposal'],
            'materialPolicy': {'shared65Binding': 'context_continuous_unbuilt_ground', 'existingPbrSourcePixelsAndBoundaryBindingsUnchanged': True,
                               'operativeExistingGroundCoverRange': [.40, .68], 'globalBaseRecolorProposed': False,
                               'soilMaterialRemainsOnCultivatedSubsets': 'context_soil_exposure', 'newMaterialAssets': 0},
            'soilOverlayProposal': soil_plan, 'cultivatedSubsetsFile': 'cultivated-soil-subsets.json',
            'restoredRootsFile': 'restored-roots.json', 'restoredGroupsFile': 'restored-groups.json',
            'heightOnlyOverridesFile': 'retained-height-overrides.json', 'nativeOriginalPrototypes': list(proto.values()),
            'growthField': {'kind': 'ONE_ARTIST_WORLD_SPACE_CONDITION_FIELD', 'units': 'cm', 'parcelIdentityInput': False,
                            'noiseLengthsCm': [2400, 1200, 400], 'noiseWeights': [.55, .30, .15], 'seeds': [31, 67, 109],
                            'fineHeightNoiseLengthCm': 110, 'fineHeightSeed': 173, 'tallSmoothstep': [.54, .76],
                            'existingSourceRoadEdgeSmoothstepCm': [20, 180],
                            'formula': 'C=.55*N2400+.30*N1200+.15*N400; E=1-smoothstep(20,180,distance(existing source roads)); T=smoothstep(.54,.76,C)*(1-.85*E); blades=5+2.5*C+12*T+.9*N110-.9*E; understory=2.2+3.1*C+1.6*T+.5*N110-.4*E',
                            'lowLayer': 'existing source understory roots', 'tallerIslands': 'existing and restored blade roots; height only',
                            'newTrackOrMowerLaneInvented': False, 'newPerParcelSoilIslandInvented': False,
                            'fieldDiagnostic': {'path': str(output / 'continuous-growth-field.png'), **field_texture}},
            'rootPolicy': {'sourceArrayOrder': list(ROOT_ARRAYS), 'withinArrayOrder': 'ascending frozen original index',
                           'appendRestoredOnlyRngSeed': 260920263, 'cellWidthCm': 2000, 'originalPositionsZXYAndYawUnchanged': True,
                           'rootRadiusCm': 14, 'wholeAllLodCrownGuardCm': 14.1, 'privateBufferCm': 30, 'sourceRoadBufferCm': 20,
                           'officialBuildingBufferCm': 150, 'excluded35cmGroundCoverRestoration': 449,
                           'retainedOverrideStage': 'After original R3 filtering, before native meadow grouping; replace height only without changing the random draw sequence',
                           'restoredGroupsStage': 'Append explicit new namespaced groups after retained historical groups', 'guardCounts': guard},
            'futureVisualRetirement': {'transitionPlan': str(paths['transition']), 'transitionGroupIds': [g['id'] for g in transition['groups']],
                                      'transitionInstances': 7000, 'pilotPlan': str(paths['infill']), 'pilotGroupIds': [g['id'] for g in infill['groups']],
                                      'pilotInstances': 33483, 'groupMaterialFieldBindingRetained': True,
                                      'oldSourceAndNativeArtifactsUnchanged': True, 'retirementActuallyAppliedToNative': False},
            'summary': summary, 'preservation': preservation,
            'plots': [{'path': str(output / name), 'sha256': hashlib.sha256(data).hexdigest(), 'evidence': 'SOURCE_PLAN_ONLY_NATIVE_PENDING'}
                      for name, data in images.items() if name != 'continuous-growth-field.png'],
            'nativeApplied': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False,
            'limits': ['Source layouts and height proposals only; no new Unreal map, native receipt, shader, GPU capture or performance measurement.',
                       'Root XY/jitter and LawnTuft0-3 meshes are inherited. The field improves morphology without guaranteeing the retained row pattern is invisible.',
                       'Shared ground textures currently provide 40-68 percent cover. Removing overlays restores that base; it does not prove close-range leaf coverage.',
                       'Full near LOD restoration costs 10.20 million triangles. Net near plant triangles increase 2.24 million against retired R14 detail; native performance remains pending.',
                       'PIL source plan colors visualize masks/height fields; they are not Unreal pixels, lighting, material response or a photorealism comparison.',
                       'Cultivation, growth and edge wear are artist interpretation. Only source geometry exclusions are preserved; no measured botany, actual use or survey accuracy is claimed.']}
    payloads = {'continuous-meadow-plan.json': encode(plan), 'cultivated-soil-subsets.json': encode(subsets),
                'restored-roots.json': encode(restored), 'restored-groups.json': encode(groups),
                'retained-height-overrides.json': encode({'schemaVersion': 1, 'rowFormat': ['originalSourceArrayIndex', 'proposedHeightCm'],
                                                         'onlyHeightMayChange': True, 'arrays': overrides}), **images}
    # Validate produced arrays by reading their serialized form before any write.
    decoded_groups = json.loads(payloads['restored-groups.json'])
    require(len(decoded_groups) == 164 and sum(len(g['instances']) for g in decoded_groups) == 39834, 'Serialized explicit group decoder differs')
    decoded_subsets = json.loads(payloads['cultivated-soil-subsets.json'])
    require(sum(len(m['indices']) // 3 for m in decoded_subsets) == 644, 'Mixed subset serialization lost cultivated triangles')
    for name, data in images.items():
        image = Image.open(io.BytesIO(data))
        image.load()
        require(image.format == 'PNG' and image.width > 0 and image.height > 0, f'PNG decoder failed: {name}')
    for path, digest in pins.items():
        require(sha(path) == digest, 'Frozen source changed during study')
    inventory = {name: {'path': str(output / name), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)} for name, data in payloads.items()}
    receipt = {'schemaVersion': 1, 'status': 'SOURCE_VALIDATION_PASS_NATIVE_PENDING', 'owner': OWNER, 'inputFiles': pins,
               'files': inventory, 'checks': {'frozenPinsUnchangedBeforeAfter': True, 'independentAllowedDomainSymmetricDifferenceCm2': difference,
                   'typedOriginalPrototypeDecoder12Lods': True, 'historicalNativeOriginalPrototypeLookupVerified': True,
                   'soilTrianglesAllClassifiedExactlyOnce': 106193, 'serializedMixedSubsetTriangles': 644,
                   'serializedRestorationGroups': 164, 'serializedRestorationInstances': 39834,
                   'originalRootPositionYawAndProvenanceRetained': True, 'wholeCrownMaskConflicts': 0,
                   'noNewGroundCoverPopulation': True, 'sourceArraysAndNonSoilDataRemainFrozen': True, 'fourPngDecodersPassed': True},
               'summary': summary, 'nativeApplied': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
               'performanceAccepted': False, 'integrationAuthorized': False}
    output.mkdir(parents=True)
    for name, data in payloads.items():
        with (output / name).open('xb') as file:
            file.write(data)
    with (output / 'source-validation.json').open('xb') as file:
        file.write(encode(receipt))
    for name, row in inventory.items():
        require(sha(output / name) == row['sha256'], 'Saved source output pin differs')
    print(json.dumps({'plan': str(output / 'continuous-meadow-plan.json'), 'sha256': sha(output / 'continuous-meadow-plan.json'),
                      **summary, 'nativeApplied': False, 'fullPhotorealismAccepted': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DESTINATION)
    args = parser.parse_args()
    build(args.output.resolve())


if __name__ == '__main__':
    main()
