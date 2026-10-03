"""Isolated upright pointed turf study after visually rejected R8 clippings.

Only fresh explicit lawn masters, their pinned managed placements and a bounded
authored leaf recipe are written. Original ground, collision, source lawn masks,
four inherited lawn groups and unmanaged rural vegetation stay unchanged.
Static physical coverage is a gate for native review, not photographic quality.
"""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import random
import sys

import numpy as np
import shapely
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OWNER = 'scripts/unreal/exterior-lawn-upright.py'
SEED = 601226300015
MATERIAL = 'lawn_natural_blade'
SCREENS = [1., .025, .007]
BUDGET = 20000000
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('fine_lawn_source_cover', HERE/'exterior-lawn-coverage.py')
cover = importlib.util.module_from_spec(spec); spec.loader.exec_module(cover)
natural = cover.natural
require, sha, write, read = cover.require, cover.sha, cover.write, cover.read


def blade_parameters(variant, growth, compact=False):
    rng = random.Random(SEED+variant*1777+int(compact)*8111)
    count = 48 if compact else 64
    blades = []
    for i in range(count):
        low = i % 4 == 0
        angle = rng.uniform(-math.pi, math.pi)
        radius = math.sqrt(rng.random())*(.07 if compact and variant == 0 else .55 if compact else 3.7)
        height = rng.uniform(3., 4.1) if low else rng.uniform(3.8, 5.85)
        width, reach = rng.uniform(.25, .40), rng.uniform(1.50, 2.00)
        if compact:
            reach = rng.uniform(.40, .63) if variant == 0 else rng.uniform(1.30, 1.85)
        blades.append({'rootCm': [math.cos(angle)*radius, math.sin(angle)*radius],
            'angleRad': rng.uniform(-math.pi, math.pi), 'heightCm': height,
            'widthCm': width, 'reachCm': reach, 'low': low,
            'bendRad': rng.uniform(-.32, .32), 'rollRad': rng.uniform(-.34, .34),
            'twistRad': rng.uniform(-.48, .48), 'curlCm': rng.uniform(-.13, .13)*(.16 if compact and variant == 0 else 1),
            'arch': rng.uniform(.10, .20), 'tipWidth': 0., 'clipped': False,
            'tone': rng.uniform(.83, 1.03), 'dry': growth == 1 and rng.random() < .06,
            'bladeSeed': rng.random()})
    return blades


def center(blade, t):
    angle = blade['angleRad']+blade['bendRad']*t
    forward = np.array([math.cos(angle), math.sin(angle)])
    side = np.array([-forward[1], forward[0]])
    xy = np.array(blade['rootCm'])+forward*blade['reachCm']*(.36*t+.64*t*t)
    xy += side*blade['curlCm']*math.sin(math.pi*t)
    z = blade['heightCm']*(t+blade['arch']*math.sin(math.pi*t)-.025*t*t)
    return np.array([*xy, z])


def mesh(variant, growth, lod, compact=False):
    # Parallel sides over the blade body and an actual pointed terminal triangle.
    # Three real panels per leaf retain bent/torsioned normals at every distance.
    # The source-only study intentionally keeps identical geometry at all LODs,
    # so physical cover cannot improve through a wider distant replacement.
    points, uv, uv1, colors, triangles, ranges = [], [], [], [], [], []
    for index, blade in enumerate(blade_parameters(variant, growth, compact)):
        start = len(points); triangle_start = len(triangles); centers, rings, section_normals = [], [], []
        for t, us in ((0., [0., 1.]), (.78, [0., 1.]), (1., [.5])):
            middle = center(blade, t)
            tangent = center(blade, t+.0001)-center(blade, t-.0001); tangent /= np.linalg.norm(tangent)
            angle = blade['angleRad']+blade['bendRad']*t
            side = np.array([-math.sin(angle), math.cos(angle), 0.])
            normal = np.cross(tangent, side); normal /= np.linalg.norm(normal)
            roll = blade['rollRad']+blade['twistRad']*t
            side = side*math.cos(roll)+normal*math.sin(roll)
            normal = np.cross(tangent, side); normal /= np.linalg.norm(normal)
            width = blade['widthCm']*(.82 if t == 0 else 1. if t < 1 else 0.)
            rgb = np.array([.78+.20*t, .87+.12*t, .76+.13*t])*(.72+.24*t)*blade['tone']
            if blade['dry']: rgb = rgb*(1-.12*t)+np.array([.78, .72, .53])*(.12*t)
            ring = []
            for u in us:
                ring.append(len(points)); points.append((middle+side*width*(u-.5)).tolist())
                uv.append([u, t]); uv1.append([blade['bladeSeed'], float(growth)])
                colors.append([*np.clip(rgb, 0, 1).tolist(), 1.])
            rings.append(ring); centers.append(middle.tolist()); section_normals.append(normal.tolist())
        # Keep the physical basal edges on/above original ground; no ground edit.
        lift = max(0., -min(p[2] for p in points[start:]))
        for vertex in range(start, len(points)): points[vertex][2] += lift
        for q in centers: q[2] += lift
        first, shoulder, tip = rings
        triangles.extend([[first[0], first[1], shoulder[0]], [first[1], shoulder[1], shoulder[0]],
                          [shoulder[0], shoulder[1], tip[0]]])
        q = np.asarray(points)[np.asarray(triangles[triangle_start:])][:, :, :2]
        a, b = q[:, 1]-q[:, 0], q[:, 2]-q[:, 0]
        area = float(abs(a[:, 0]*b[:, 1]-a[:, 1]*b[:, 0]).sum()*.5)
        ranges.append({'bladeIndex': index, 'vertexOffset': start, 'vertexCount': 5,
            'triangleOffset': triangle_start, 'triangleCount': 3, 'segments': 2,
            'centerlineCm': centers, 'sectionNormals': section_normals, 'rootCm': blade['rootCm'],
            'widthCm': blade['widthCm'], 'heightCm': blade['heightCm'], 'reachCm': blade['reachCm'],
            'low': blade['low'], 'clipped': False, 'pointedTip': True, 'dry': blade['dry'],
            'rollRad': blade['rollRad'], 'twistRad': blade['twistRad'],
            'projectedTriangleAreaCm2': area, 'nearProjectedTriangleAreaCm2': area,
            'lodProjectedAreaWidthScale': 1., 'basalLiftCm': lift})
    record = {'nodeName': f'lawn_natural_{"edge_" if compact else ""}{growth}_{variant}_LOD{lod}',
        'variant': variant, 'growthClass': growth, 'edgeMaster': compact, 'level': lod,
        'positionsCm': points, 'uv0': uv, 'uv1': uv1, 'colors': colors, 'triangles': triangles, 'bladeRanges': ranges}
    record['expectedBoundsCm'] = {name: [op(p[k] for p in points) for k in range(3)] for name, op in [('min', min), ('max', max)]}
    record['radialEnvelopeCm'] = max(math.hypot(*p[:2]) for p in points)
    return record


def smooth(t):
    t = np.clip(t, 0, 1); return t*t*(3-2*t)


def placements(domain, prototypes):
    rng = np.random.default_rng(SEED); xmin, ymin, xmax, ymax = domain.bounds
    # One homogeneous candidate cloud; footprint adaptation and acceptance
    # density change smoothly with distance, never an independent border line.
    maximum_density = 14000
    count = int((xmax-xmin)*(ymax-ymin)/10000*maximum_density)
    x, y = rng.uniform(xmin, xmax, count), rng.uniform(ymin, ymax, count)
    inside = shapely.contains_xy(domain, x, y); x, y = x[inside], y[inside]
    distance = shapely.distance(shapely.points(x, y), domain.boundary)
    target_density = 1250+350*(1-smooth((distance-3.0)/8.5))+12400*(1-smooth((distance-.8)/3.45))
    keep = rng.random(len(x)) < target_density/maximum_density
    x, y, distance = x[keep], y[keep], distance[keep]
    broad = natural.value_noise(x*10, -y*10, 2150., 30179)
    medium = natural.value_noise(x*10, -y*10, 690., 72917)
    dryness = natural.value_noise(x*10, -y*10, 1850., 83407)
    height = .94+.06*broad+.025*(medium-.5)
    lookup = {p['id']: p for p in prototypes}
    envelopes = {p['id']: max(l['radialEnvelopeCm'] for l in p['lods']) for p in prototypes}
    full_radius = max(envelopes[mid] for mid in lookup if not lookup[mid]['edgeMaster'])
    occupied, groups, rejected = defaultdict(list), {}, Counter()
    margin, near = math.inf, 0
    for a, b, d, h, dry in zip(x, y, distance, height, dryness):
        growth = int(dry > .74); scale = round(float(h*rng.uniform(.974, 1.026)), 6)
        compact = bool(d <= full_radius*scale+.1)
        if compact:
            variant = 1 if d > envelopes[f'lawn_natural_edge_{growth}_1']*scale+.1 else 0
        else:
            variant = int(rng.integers(8))
        mid = f'lawn_natural_{"edge_" if compact else ""}{growth}_{variant}'
        radius = envelopes[mid]*scale
        if d <= radius+.1: rejected['whole-crown-managed-clearance'] += 1; continue
        spacing = .45+1.95*float(smooth((d-.4)/11.))
        cell = math.floor(a/2.4), math.floor(b/2.4)
        if any((a-q[0])**2+(b-q[1])**2 < min(spacing, q[2])**2
               for dx in (-1, 0, 1) for dy in (-1, 0, 1)
               for q in occupied.get((cell[0]+dx, cell[1]+dy), [])):
            rejected['adaptive-root-spacing'] += 1; continue
        occupied[cell].append((a, b, spacing)); row = lookup[mid]
        near += row['lods'][0]['triangles']; require(near <= BUDGET, 'Upright study near triangle budget exceeded')
        native = [round(float(a), 5), round(float(b), 5), -6.5]
        gid = f'EX_lawn_natural_{math.floor(a/2000)}_{math.floor(b/2000)}_{"edge_" if compact else ""}{growth}_{variant}'
        group = groups.setdefault(gid, {'id': gid, 'meshId': mid, 'role': 'grass', 'cullEndCm': 4000,
            'qualityDetail': True, 'instances': []})
        group['instances'].append({'positionCm': native, 'yawDeg': round(float(rng.uniform(-180, 180)), 5),
            'scale': [scale]*3, 'edge': compact, 'clearanceMm': float(d)*10,
            'enclosingRadiusMm': radius*10+1, 'radiusCm': radius,
            'actualHeightCm': row['heightCm']*scale, 'growthClass': growth})
        margin = min(margin, (d-radius)*10-1)
    flat = [{'meshId': g['meshId'], **row} for g in groups.values() for row in g['instances']]
    require(38000 < len(flat) < 130000, 'Unexpected upright study population')
    budgets = [sum(len(g['instances'])*lookup[g['meshId']]['lods'][lod]['triangles'] for g in groups.values()) for lod in range(3)]
    centers = np.array([r['positionCm'][:2] for r in flat])*10
    phase = [float(abs(np.exp(2j*np.pi*centers[:, k]/60).mean())) for k in range(2)]
    interior_centers = np.array([r['positionCm'][:2] for r in flat if not r['edge']])*10
    interior_phase = [float(abs(np.exp(2j*np.pi*interior_centers[:, k]/60).mean())) for k in range(2)]
    require(max(interior_phase) < .025, 'Upright study recreates interior lattice')
    scales = np.array([r['scale'][0] for r in flat])
    return list(groups.values()), flat, {'instances': len(flat), 'groups': len(groups), 'edgeInstances': sum(r['edge'] for r in flat),
        'nearTriangleBudget': budgets[0], 'allInstancesTriangleBudgetByLod': budgets,
        'minimumAdditionalCrownClearanceMm': margin, 'exactAllowedDomainM2': domain.area/10000,
        'rootElevationCm': -6.5, 'perMesh': dict(Counter(r['meshId'] for r in flat)),
        'sixtyMmLatticePhaseAmplitudeXY': phase, 'interiorSixtyMmLatticePhaseAmplitudeXY': interior_phase,
        'heightScaleRange': [float(scales.min()), float(scales.max())],
        'heightScaleStandardDeviation': float(scales.std()), 'candidateDensityPerM2': maximum_density,
        'placementMethod': 'One homogeneous stochastic candidate population; smoothly adaptive root acceptance and footprint spacing, no independent border row or density holes.',
        'fieldScalesMm': [690, 1850, 2150], 'rejected': dict(rejected)}


def coverage_receipt(records, rows, domain, prior, output):
    previous = read(prior/'lawn-coverage-receipt.json')
    windows = []; atlas = Image.new('RGB', (900, 4*230), '#ecebe3'); draw = ImageDraw.Draw(atlas)
    for index, old in enumerate(previous['windows']):
        c = old['centerCm']; require(domain.contains(shapely.box(c[0]-50, c[1]-50, c[0]+50, c[1]+50)), 'Interior coverage ROI differs')
        result, masks = cover.raster_coverage(records, rows, c)
        result['rejectedR6aStudy'] = old['rejectedR6aStudy']; result['rejectedR8Study'] = old['lods']
        for lod, mask in enumerate(masks):
            r = result['lods'][lod]
            r['studyTargetsMet'] = r['projectedCoverage'] >= .75 and r['tenCmBinCoverageP10'] >= .55 and r['bareTenCmBins'] == 0
            rgb = np.empty((*mask.shape, 3), dtype=np.uint8); rgb[:] = [208, 216, 186]; rgb[mask > 0] = [63, 97, 45]
            atlas.paste(Image.fromarray(rgb).resize((215, 215), Image.Resampling.BOX), (lod*300, index*230+15))
            draw.text((lod*300, index*230), f'ROI {index+1} LOD{lod}: {r["projectedCoverage"]:.1%}', fill='#192319')
        windows.append(result)
    atlas.save(output/'lawn-coverage-topview.png')
    return {'status': 'MEASURED_UPRIGHT_STUDY_COVERAGE_NOT_NATIVE_ACCEPTED', 'windows': windows,
        'criteria': {'minimumTopViewCoverage': .75, 'preferredTopViewCoverage': .80, 'minimumTenCmBinP10': .55, 'maximumPermittedBladeLossAcrossLods': 0},
        'nativeAcceptanceRequired': 'Same garden/detail/edge native cameras must confirm upright blade scale, varied shading and continuous boundary; physical coverage is not realism.'}


def boundary_raster(records, rows, origin, axis, inward, width_cm, length_cm, pixel_cm=.025):
    """Saved leaf triangles in a frame touching an exact source boundary."""
    lookup = {r['nodeName']: r for r in records}
    origin, axis, inward = map(np.asarray, (origin, axis, inward))
    frame = np.column_stack([inward, axis])
    width_px, height_px = math.ceil(width_cm/pixel_cm), math.ceil(length_cm/pixel_cm)
    nearby = []
    for row in rows:
        q = (np.asarray(row['positionCm'][:2])-origin)@frame; radius = row['radiusCm']
        if q[0]+radius > 0 and q[0]-radius < width_cm and q[1]+radius > 0 and q[1]-radius < length_cm:
            nearby.append(row)
    results, masks = [], []
    for lod in range(3):
        image = Image.new('L', (width_px, height_px), 0); draw = ImageDraw.Draw(image)
        for row in nearby:
            record = lookup[row['meshId']+'_LOD'+str(lod)]
            p = np.asarray(record['positionsCm'])[:, :2]*row['scale'][0]
            angle = math.radians(row['yawDeg']); c, s = math.cos(angle), math.sin(angle)
            p = ((p@np.array([[c, s], [-s, c]])+row['positionCm'][:2]-origin)@frame/pixel_cm).tolist()
            for face in record['triangles']: draw.polygon([tuple(p[i]) for i in face], fill=255)
        mask = np.asarray(image); masks.append(mask)
        bands = []
        for lo, hi in ((.1, 1.), (1., 3.), (3., 10.)):
            bands.append({'distanceFromBoundaryMm': [lo*10, hi*10],
                          'physicalCoverFraction': float((mask[:, math.ceil(lo/pixel_cm):math.floor(hi/pixel_cm)] > 0).mean())})
        results.append({'lod': lod, 'projectedCoverage': float((mask > 0).mean()), 'boundaryBands': bands})
    return {'originCm': origin.tolist(), 'axisUnitXY': axis.tolist(), 'inwardUnitXY': inward.tolist(),
            'widthCm': width_cm, 'lengthCm': length_cm, 'pixelSizeMm': pixel_cm*10,
            'resolutionXY': [width_px, height_px], 'intersectingInstances': len(nearby), 'lods': results}, masks


def boundary_receipt(records, rows, domain, prior, output):
    before_records = read(prior/'lawn-natural-prototypes.json'); before_rows = read(prior/'lawn-natural-plan.json')['lawnPlacements']
    # Deck edge is exact x=-476cm. Mulch edge uses the actual source hole
    # segment [-11600,4200]→[-9800,5200]mm, keeping its central 60%.
    windows = [('deck', [-476., -650.], [-476., -400.]),
               ('mulch', [-1124., -440.], [-1016., -500.])]
    atlas = Image.new('RGB', (1200, 1250), '#ecebe3'); draw = ImageDraw.Draw(atlas); receipt = []
    for index, (name, a, b) in enumerate(windows):
        a, b = np.asarray(a), np.asarray(b); length = float(np.linalg.norm(b-a)); axis = (b-a)/length
        inward = np.array([-axis[1], axis[0]])
        if not domain.contains(shapely.Point((a+b)*.5+inward)):
            inward *= -1
        rectangle = shapely.Polygon([a, b, b+inward*40, a+inward*40])
        require(domain.buffer(.00001).covers(rectangle), 'Boundary ROI escaped exact managed lawn')
        actual, masks = boundary_raster(records, rows, a, axis, inward, 40., length)
        rejected, old_masks = boundary_raster(before_records, before_rows, a, axis, inward, 40., length)
        actual.update(boundaryId=name, rejectedR8Study=rejected['lods'])
        for lod, values in enumerate(actual['lods']):
            bands = [r['physicalCoverFraction'] for r in values['boundaryBands']]
            values['studyTargetsMet'] = bands[0] > .12 and bands[1] > .40 and bands[2] > .50
        receipt.append(actual)
        for column, mask in enumerate([*masks, old_masks[0]]):
            rgb = np.empty((*mask.shape, 3), dtype=np.uint8); rgb[:] = [208, 216, 186]; rgb[mask > 0] = [63, 97, 45]
            tile_height = 550; tile_width = round(tile_height*40/length)
            atlas.paste(Image.fromarray(rgb).resize((tile_width, tile_height), Image.Resampling.BOX), (column*300, index*620+50))
            label = f'{name} '+(f'upright LOD{column}' if column < 3 else 'rejected R8 LOD0')
            draw.text((column*300, index*620), label, fill='#192319')
            values = actual['lods'][column] if column < 3 else rejected['lods'][0]
            draw.text((column*300, index*620+18), '1-10 /10-30 /30-100mm: '+ ' / '.join(f'{r["physicalCoverFraction"]:.0%}' for r in values['boundaryBands']), fill='#192319')
    atlas.save(output/'lawn-boundary-topview.png')
    return {'status': 'MEASURED_UPRIGHT_STUDY_BOUNDARY_COVERAGE_NOT_NATIVE_ACCEPTED', 'windows': receipt,
        'method': '0.25mm raster of actual saved leaf triangles, exact native yaw/scale, touching exact source boundaries; no floor or image replacement.',
        'criteria': {'minimumPhysicalCoverByBoundaryBand': {'1to10mm': .12, '10to30mm': .40, '30to100mm': .50},
                     'outsideSourceDomainPermittedCm': 0},
        'limit': 'One millimetre all-LOD radial clearance remains mandatory; actual native edge softness, lighting and material continuity are separate gates.'}


def preview(records, rows, roi_center, output):
    """Technical standalone projection of actual triangles, never native output."""
    lookup = {r['nodeName']: r for r in records}; center_xy = np.asarray(roi_center)
    image = Image.new('RGB', (1500, 900), '#d1d8c1'); draw = ImageDraw.Draw(image)
    camera = np.array([.35, .70, .62]); camera /= np.linalg.norm(camera)
    right = np.array([camera[1], -camera[0], 0.]); right /= np.linalg.norm(right)
    up = np.cross(right, camera); light = np.array([-.5, -.7, 1.]); light /= np.linalg.norm(light)
    selected, faces = [], []
    for row in rows:
        q = np.asarray(row['positionCm'][:2])-center_xy
        if max(abs(q)) > 12.5: continue
        record = lookup[row['meshId']+'_LOD0']; p = np.asarray(record['positionsCm'])*row['scale'][0]
        a = math.radians(row['yawDeg']); c, sn = math.cos(a), math.sin(a)
        p[:, :2] = p[:, :2]@np.array([[c, sn], [-sn, c]])+q
        selected.append(row)
        for face in record['triangles']:
            vertices = p[face]; n = np.cross(vertices[1]-vertices[0], vertices[2]-vertices[0]); n /= np.linalg.norm(n)
            shade = .42+.58*abs(float(n@light))
            color = np.asarray(record['colors'])[face, :3].mean(axis=0)
            rgb = np.sqrt(np.array([.04, .075, .025])*color)*255*shade
            points = np.column_stack([vertices@right, vertices@up])*35
            points[:, 0] += 745; points[:, 1] = 650-points[:, 1]
            faces.append((float((vertices@camera).mean()), [tuple(v) for v in points], tuple(np.clip(rgb, 0, 255).astype(int))))
    for _, points, rgb in sorted(faces, key=lambda r: r[0]): draw.polygon(points, fill=rgb)
    draw.rectangle((0, 0, 1500, 80), fill='#f0efe8')
    draw.text((18, 15), 'SOURCE STUDY: actual 25 x 25 cm leaf geometry, orthographic oblique projection; no native lighting/appearance claim.', fill='#202820')
    draw.text((18, 40), f'{len(selected)} real patches; pointed upright leaves, frozen dark recipe; original source floor unchanged. Coverage measured separately at 0.25mm.', fill='#202820')
    image.save(output/'upright-source-preview.png')


def legacy_source_proof():
    """Read-only actual donor trim sequence, never an actor mutation."""
    helper = ROOT/'output/unreal/exterior-20260930-r8/source-freeze/scripts/unreal/exterior-lawn-native.py'
    require(sha(helper) == '8439b1b5e1e64ba08db47bad27a72065d807082f2253a56d92448befdbd403b0', 'Sealed R8 legacy helper differs')
    spec = importlib.util.spec_from_file_location('upright_legacy_native_proof', helper)
    native = importlib.util.module_from_spec(spec); spec.loader.exec_module(native)
    native.ROOT = ROOT  # Runtime workspace root for immutable standalone source snapshot.
    photoreal = ROOT/'output/unreal/realism-20260926-r5/photoreal-import-report.json'
    rural = ROOT/'output/unreal/realism-20260926-r5/rural-import-report.json'
    plan = ROOT/'output/unreal/rural-context-20260923-r4/geometry/rural-context-geometry.json'
    inspection = ROOT/'output/unreal/lawn-native-inspection-20260930-r1.json'
    geometry, rows, pin, proof = native._trimmed_legacy_placement(read(photoreal), read(rural), read(plan))
    actual = read(inspection); require(actual['contentUnchanged'] and actual['nativeLawnInstanceCount'] == 40437, 'Legacy inspection differs')
    witnesses = {r['actor']: r for r in actual['taggedLawnActors']}
    require([len(rows[k]['instances']) for k in native.LEGACY_GROUPS] == [10118, 10153, 10147, 10019], 'Legacy donor counts differ')
    for key in native.LEGACY_GROUPS:
        values = witnesses[geometry['groups'][key]['actor']]['orderedInstanceTransforms']
        require(native.digest(native._rural_values(values)) == proof['groups'][key]['transformsSha256'], 'Legacy ordered transforms differ')
    proof.update(status='VERIFIED_READ_ONLY_DONOR_FULL_SOURCE_AND_HISTORICAL_TRIM_IDENTITY', nativeMutationPerformed=False,
        inspectedNativeInstances=40437, inspection={'path': str(inspection), 'sha256': sha(inspection)})
    return proof, [photoreal, rural, plan, inspection, helper]


def build(geometry, rural, original, prior, output):
    geometry, rural, original, prior, output = map(lambda p: Path(p).resolve(), (geometry, rural, original, prior, output))
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Use fresh immutable upright lawn study output')
    scene, faces, grass, forbidden, source, domain, exclusions, extra, keep = cover.managed_source(geometry, rural, original)
    legacy, legacy_inputs = legacy_source_proof()
    records, prototypes = [], []
    for compact in (False, True):
        for growth in range(2):
            for variant in range(2 if compact else 8):
                lods = []
                for lod in range(3):
                    r = mesh(variant, growth, lod, compact); records.append(r)
                    lods.append({'level': lod, 'nodeName': r['nodeName'], 'vertices': len(r['positionsCm']),
                        'triangles': len(r['triangles']), 'expectedBoundsCm': r['expectedBoundsCm'],
                        'radialEnvelopeCm': r['radialEnvelopeCm'], 'blades': len(r['bladeRanges']), 'minimumCurveSegments': 2})
                prototypes.append({'id': f'lawn_natural_{"edge_" if compact else ""}{growth}_{variant}', 'role': 'grass',
                    'placementPolicy': 'explicit-only', 'heightCm': max(l['expectedBoundsCm']['max'][2] for l in lods),
                    'materialKeys': [MATERIAL], 'lodScreenSizes': SCREENS, 'lods': lods, 'growthClass': growth, 'edgeMaster': compact,
                    'composition': f'{48 if compact else 64} pointed upright-majority leaves, three actual bent/torsioned panels per leaf, identical allLOD; no patch card.'})
    groups, rows, audit = placements(domain, prototypes)
    inputs = {str(p): sha(p) for p in (Path(__file__), HERE/'exterior-lawn-fine.py', HERE/'exterior-lawn-coverage.py', HERE/'exterior-lawn-natural.py',
        HERE/'lawn-geometry.py', HERE/'vegetation.py', HERE/'performance_scene_policy.py', geometry/'scene.json', geometry/'dom-mm.obj',
        rural, rural.parent/'scene.json', rural.parent/'dom-mm.obj', original, prior/'lawn-natural-plan.json',
        prior/'geometry-manifest.json', prior/'material-manifest.json', prior/'lawn-coverage-receipt.json', prior/'lawn-qa-views.json',
        prior/'lawn-natural-prototypes.json')}
    inputs.update({str(p): sha(p) for p in legacy_inputs})
    common = {'schemaVersion': 1, 'owner': OWNER, 'generatorSha256': sha(__file__), 'inputFiles': inputs,
        'activeDesign': scene['activeDesign'], 'housePlacement': scene['house']['placement'],
        'sourceSceneSha256': sha(geometry/'scene.json'), 'sourceObjSha256': sha(geometry/'dom-mm.obj'),
        'managedLawnPlan': {'path': str(rural), 'sha256': sha(rural)}, 'managedLawnKeepPolygonsCm': keep,
        'derivedFrom': {'path': str(original), 'sha256': sha(original)}}
    output.mkdir(parents=True)
    glb = output/'lawn-natural.glb'; natural.OWNER = OWNER; natural.write_glb(glb, records)
    for row in prototypes: row.update(glbPath=str(glb), glbSha256=sha(glb))
    coverage = coverage_receipt(records, rows, domain, prior, output)
    write(output/'lawn-coverage-receipt.json', coverage)
    common['coverageReceipt'] = {'path': str(output/'lawn-coverage-receipt.json'), 'sha256': sha(output/'lawn-coverage-receipt.json')}
    boundary = boundary_receipt(records, rows, domain, prior, output)
    write(output/'lawn-boundary-receipt.json', boundary)
    common['boundaryCoverageReceipt'] = {'path': str(output/'lawn-boundary-receipt.json'), 'sha256': sha(output/'lawn-boundary-receipt.json')}
    audit.update(status='MEASURED_UPRIGHT_MANAGED_LAWN_STUDY_NOT_NATIVE_ACCEPTED', nativeVerified=False, legacyLawnProof=legacy,
        sourceAreaM2=grass.area/1e6, fullSourceLawnM2=source.area/1e6, unmanagedSourceLawnExcludedM2=source.area/1e6-domain.area/10000,
        sourceTriangles=len(faces), exclusionUnionM2=forbidden.area/1e6, sourceMasksUnchanged=True, managedLawnKeepPolygonsPreserved=True,
        allLodGeometryVertices=sum(len(r['positionsCm']) for r in records), allLodGeometryTriangles=sum(len(r['triangles']) for r in records),
        extraExclusionSourceIds=extra, crownProof='Actual allLOD radial envelopes fit exact DOM1/exclusions and pinned managed keep union plus1mm; WPO forbidden.',
        boundaryPlacement='Smaller actual compact footprints and smooth adaptive population density; no independent border row.',
        leavesPerPatchEveryLod={'interior': 64, 'boundary': 48}, lowLeaningLeavesPerPatch={'interior': 16, 'boundary': 12},
        physicalCoverage=coverage, boundaryCoverage=boundary, densityPatchesPerM2=len(rows)/(domain.area/10000),
        bladesPerM2EveryLod=sum(48 if r['edge'] else 64 for r in rows)/(domain.area/10000))
    audit.update(interiorCoverageTargetsMet=all(l['studyTargetsMet'] for w in coverage['windows'] for l in w['lods']),
        boundaryCoverageTargetsMet=all(l['studyTargetsMet'] for w in boundary['windows'] for l in w['lods']),
        nativeAppearanceAccepted=False, fullPhotorealismAccepted=False, integrationAuthorized=False,
        studyLimit='Three panels retain short curved and torsioned leaves; identical allLOD. Static coverage targets are reported truthfully, native owner unsupported until explicit integration.')
    geometry_manifest = {'schema': 1, **common, 'units': 'metres', 'axes': 'glTF Y-up; Unreal native = [100*x,100*z,100*y]',
        'status': 'OFFLINE_NOT_NATIVE_ACCEPTED', 'meshes': prototypes, 'revision': 'Upright pointed turf isolated source study R1'}
    recipe = deepcopy(read(prior/'material-manifest.json')[MATERIAL])
    # Exact bounded frozen fine recipe reused; material calibration is root-owned.
    require(recipe['linearColor'] == [.04, .075, .025], 'Frozen dark fine recipe differs')
    plan = {'kind': 'authored-natural-lawn-replacement', **common, 'seed': SEED, 'sourceLawnId': 'DOM_00001',
        'sourceLawnMaterial': 'MAT_0001', 'sourceElevationMm': -65, 'sourceTriangleCount': len(faces), 'exclusions': exclusions,
        'sourceLawnDomainSourceMm': shapely.to_geojson(source), 'lawnDomainSourceMm': shapely.to_geojson(cover.source_shape(domain)),
        'groups': groups, 'lawnPlacements': rows, 'lodScreenSizes': SCREENS,
        'renderingPolicy': deepcopy(read(prior/'lawn-natural-plan.json')['renderingPolicy']),
        'replacementPolicy': deepcopy(read(prior/'lawn-natural-plan.json')['replacementPolicy']), 'audit': audit}
    write(output/'geometry-manifest.json', geometry_manifest)
    plan['geometryManifest'] = {'path': str(output/'geometry-manifest.json'), 'sha256': sha(output/'geometry-manifest.json')}
    write(output/'material-manifest.json', {MATERIAL: recipe})
    write(output/'asset-manifest.json', {'schema': 1, **common, 'sources': [{'kind': 'original-authored-geometry', 'generator': OWNER,
        'license': 'Original project asset'}], 'scope': 'Exact inherited managed turf only; no surveyed vegetation or photographed scan claim.'})
    write(output/'lawn-natural-plan.json', plan, compact=True); write(output/'lawn-natural-prototypes.json', records, compact=True)
    write(output/'lawn-natural-audit.json', audit)
    preview(records, rows, coverage['windows'][0]['centerCm'], output)
    manifest = {**common, 'status': 'MEASURED_UPRIGHT_LAWN_STUDY_NOT_NATIVE_ACCEPTED', 'geometryManifest': plan['geometryManifest'],
        **{key: {'path': str(output/name), 'sha256': sha(output/name)} for key, name in
           [('materialManifest', 'material-manifest.json'), ('plan', 'lawn-natural-plan.json'), ('geometryProof', 'lawn-natural-prototypes.json'),
            ('coverageReceipt', 'lawn-coverage-receipt.json'), ('glb', 'lawn-natural.glb')]}, 'audit': audit,
        'boundaryCoverageReceipt': common['boundaryCoverageReceipt'],
        'integrationContract': 'Source-only unsupported owner until explicit future integration. Same20 explicit lawn_natural masters/frozen dark material/screens;64 interior and48 boundary pointed leaves allLOD,16/12 modestly leaning. Exact4 inherited40437 instance identity proven read-only; ground/collision/unmanaged vegetation preserved. New native review mandatory.'}
    write(output/'lawn-natural-manifest.json', manifest)
    cameras = deepcopy(read(prior/'lawn-qa-views.json'))
    cameras.update(owner=OWNER, generatorSha256=sha(__file__), managedLawnPlan=common['managedLawnPlan'], plan=manifest['plan'])
    write(output/'lawn-qa-views.json', cameras)
    return {k: v for k, v in audit.items() if k not in ('physicalCoverage', 'boundaryCoverage')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('geometry', 'rural', 'original', 'prior', 'output'): parser.add_argument('--'+key, required=True)
    args = parser.parse_args(); print(json.dumps(build(**vars(args))))
