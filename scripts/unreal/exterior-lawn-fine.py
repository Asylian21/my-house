"""Fine, curved managed turf successor to visually rejected R7 ribbon cover.

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
OWNER = 'scripts/unreal/exterior-lawn-fine.py'
SEED = 601226300014
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
        low = i % 4 != 0
        angle, radius = rng.uniform(-math.pi, math.pi), math.sqrt(rng.random())*(.07 if compact and variant == 0 else .55 if compact else 4.7)
        height = rng.uniform(1.3, 2.3) if low else rng.uniform(2.9, 4.35)
        width = rng.uniform(.16, .24) if low else rng.uniform(.10, .17)
        reach = rng.uniform(4.8, 6.6) if low else rng.uniform(2.6, 4.2)
        if compact:
            # Near the boundary fine nearly upright leaves need a very small
            # actual footprint, rather than a broad radial patch or edge row.
            reach = rng.uniform(.35, .55) if variant == 0 else rng.uniform(2.3, 3.1)
            height *= .82 if variant == 0 else .95
            width *= .95 if variant == 0 else .97
        blades.append({'rootCm': [math.cos(angle)*radius, math.sin(angle)*radius],
            'angleRad': rng.uniform(-math.pi, math.pi), 'heightCm': height,
            'widthCm': width, 'reachCm': reach, 'low': low,
            'bendRad': rng.uniform(-.46, .46), 'rollRad': rng.uniform(-.52, .52),
            'twistRad': rng.uniform(-.56, .56), 'curlCm': rng.uniform(-.22, .22)*( .06 if compact and variant == 0 else .40 if compact else 1),
            'arch': rng.uniform(.065, .155), 'tipWidth': rng.uniform(.22, .48),
            'clipped': rng.random() < .90, 'tone': rng.uniform(.83, 1.05),
            'dry': growth == 1 and rng.random() < .07, 'bladeSeed': rng.random()})
    return blades


def center(blade, t):
    angle = blade['angleRad']+blade['bendRad']*t
    forward = np.array([math.cos(angle), math.sin(angle)])
    side = np.array([-forward[1], forward[0]])
    xy = np.array(blade['rootCm'])+forward*blade['reachCm']*(.16*t+.84*t*t)
    xy += side*blade['curlCm']*math.sin(math.pi*t)
    if blade['low']:
        z = blade['heightCm']*math.sin(math.pi*(.60+.04*blade['arch'])*t)
    else:
        z = blade['heightCm']*(t+blade['arch']*math.sin(math.pi*t)-.045*t*t)
    return np.array([*xy, z])


def mesh(variant, growth, lod, compact=False):
    points, uv, uv1, colors, triangles, ranges = [], [], [], [], [], []
    reference = mesh(variant, growth, 0, compact) if lod else None
    for index, blade in enumerate(blade_parameters(variant, growth, compact)):
        segments = 3 if lod == 0 and not compact else 2
        start = len(points); triangle_start = len(triangles); centers, rings, normals = [], [], []
        for level in range(segments+1):
            t = level/segments; middle = center(blade, t)
            tangent = center(blade, t+.0001)-center(blade, t-.0001); tangent /= np.linalg.norm(tangent)
            angle = blade['angleRad']+blade['bendRad']*t
            side = np.array([-math.sin(angle), math.cos(angle), 0.])
            normal = np.cross(tangent, side); normal /= np.linalg.norm(normal)
            # Rolling and twisting the actual cross-section gives varied
            # geometric normals; all leaves no longer face uniformly upward.
            roll = blade['rollRad']+blade['twistRad']*t+.16*math.sin(math.pi*t+blade['bladeSeed']*math.tau)
            side = side*math.cos(roll)+normal*math.sin(roll)
            normal = np.cross(tangent, side); normal /= np.linalg.norm(normal)
            width = blade['widthCm']*(.12*(1-t)+(blade['tipWidth'] if blade['clipped'] else .015)*t+.78*math.sin(math.pi*t)**.8)
            rgb = np.array([.78+.20*t, .87+.12*t, .76+.13*t])*(.72+.24*t)*blade['tone']
            if blade['dry']: rgb = rgb*(1-.16*t)+np.array([.78, .72, .53])*(.16*t)
            ring = []
            micro = compact and variant == 0
            us = [.5] if (compact and level == 0) or (micro and level == segments) or (lod == 2 and level == 0) else [0., 1.]
            for u in us:
                ring.append(len(points)); points.append((middle+side*width*(u-.5)).tolist())
                uv.append([u, t]); uv1.append([blade['bladeSeed'], float(growth)])
                colors.append([*np.clip(rgb, 0, 1).tolist(), 1.])
            rings.append(ring); centers.append(middle.tolist()); normals.append(normal.tolist())
        for first, second in zip(rings[:-1], rings[1:]):
            if len(first) == 1:
                triangles.append([first[0], second[1], second[0]])
            elif len(second) == 1:
                triangles.append([first[0], first[1], second[0]])
            else:
                triangles.extend([[first[0], first[1], second[0]], [first[1], second[1], second[0]]])
        def projected_area(p, faces):
            q = np.asarray(p)[np.asarray(faces)][:, :, :2]
            a, b = q[:, 1]-q[:, 0], q[:, 2]-q[:, 0]
            return float(abs(a[:, 0]*b[:, 1]-a[:, 1]*b[:, 0]).sum()*.5)
        actual_area = projected_area(points, triangles[triangle_start:])
        target_area, width_scale = actual_area, 1.
        if reference:
            near = reference['bladeRanges'][index]
            target_area = near['projectedTriangleAreaCm2']
            width_scale = float(np.clip(target_area/actual_area, .92, 1.14))
            # Compensate the measured area removed by curve simplification and
            # the tiny far basal triangle, rather than removing actual leaves.
            for ring, middle in zip(rings, centers):
                for vertex in ring:
                    points[vertex] = (np.asarray(middle)+(np.asarray(points[vertex])-middle)*width_scale).tolist()
            actual_area = projected_area(points, triangles[triangle_start:])
        ranges.append({'bladeIndex': index, 'vertexOffset': start, 'vertexCount': len(points)-start,
            'triangleOffset': triangle_start, 'triangleCount': len(triangles)-triangle_start,
            'segments': segments, 'centerlineCm': centers, 'sectionNormals': normals,
            'rootCm': blade['rootCm'], 'widthCm': blade['widthCm'], 'low': blade['low'],
            'clipped': blade['clipped'], 'dry': blade['dry'], 'rollRad': blade['rollRad'],
            'twistRad': blade['twistRad'], 'farBasalPoint': lod == 2,
            'microBoundaryPointedEnds': compact and variant == 0,
            'projectedTriangleAreaCm2': actual_area, 'nearProjectedTriangleAreaCm2': target_area,
            'lodProjectedAreaWidthScale': width_scale})
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
    target_density = 485+1115*(1-smooth((distance-3.0)/8.5))+12400*(1-smooth((distance-.8)/3.45))
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
        near += row['lods'][0]['triangles']; require(near <= BUDGET, 'Fine lawn near triangle budget exceeded')
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
    require(38000 < len(flat) < 75000, 'Unexpected fine lawn population')
    budgets = [sum(len(g['instances'])*lookup[g['meshId']]['lods'][lod]['triangles'] for g in groups.values()) for lod in range(3)]
    centers = np.array([r['positionCm'][:2] for r in flat])*10
    phase = [float(abs(np.exp(2j*np.pi*centers[:, k]/60).mean())) for k in range(2)]
    interior_centers = np.array([r['positionCm'][:2] for r in flat if not r['edge']])*10
    interior_phase = [float(abs(np.exp(2j*np.pi*interior_centers[:, k]/60).mean())) for k in range(2)]
    require(max(interior_phase) < .025, 'Fine lawn recreates interior lattice')
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
        result['rejectedR6aStudy'] = old['rejectedR6aStudy']; result['rejectedR7Study'] = old['lods']
        for lod, mask in enumerate(masks):
            r = result['lods'][lod]
            require(r['projectedCoverage'] > .70 and r['tenCmBinCoverageP10'] > .55, 'Fine leaves lose continuous interior cover')
            rgb = np.empty((*mask.shape, 3), dtype=np.uint8); rgb[:] = [208, 216, 186]; rgb[mask > 0] = [63, 97, 45]
            atlas.paste(Image.fromarray(rgb).resize((215, 215), Image.Resampling.BOX), (lod*300, index*230+15))
            draw.text((lod*300, index*230), f'ROI {index+1} LOD{lod}: {r["projectedCoverage"]:.1%}', fill='#192319')
        windows.append(result)
    atlas.save(output/'lawn-coverage-topview.png')
    return {'status': 'PASS_STATIC_PHYSICAL_COVERAGE_NOT_NATIVE_ACCEPTED', 'windows': windows,
        'criteria': {'minimumTopViewCoverage': .70, 'minimumTenCmBinP10': .55, 'maximumPermittedBladeLossAcrossLods': 0},
        'nativeAcceptanceRequired': 'Same garden/detail/edge native cameras must confirm fine blade scale, varied shading and continuous boundary; physical coverage is not realism.'}


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
        actual.update(boundaryId=name, rejectedR7Study=rejected['lods'])
        for lod, values in enumerate(actual['lods']):
            bands = [r['physicalCoverFraction'] for r in values['boundaryBands']]
            require(bands[0] > .12 and bands[1] > .40 and bands[2] > .50,
                    f'Fine lawn retains a broad bare boundary strip: {name} LOD{lod} {bands}')
        receipt.append(actual)
        for column, mask in enumerate([*masks, old_masks[0]]):
            rgb = np.empty((*mask.shape, 3), dtype=np.uint8); rgb[:] = [208, 216, 186]; rgb[mask > 0] = [63, 97, 45]
            tile_height = 550; tile_width = round(tile_height*40/length)
            atlas.paste(Image.fromarray(rgb).resize((tile_width, tile_height), Image.Resampling.BOX), (column*300, index*620+50))
            label = f'{name} '+(f'fine LOD{column}' if column < 3 else 'rejected R7 LOD0')
            draw.text((column*300, index*620), label, fill='#192319')
            values = actual['lods'][column] if column < 3 else rejected['lods'][0]
            draw.text((column*300, index*620+18), '1-10 /10-30 /30-100mm: '+ ' / '.join(f'{r["physicalCoverFraction"]:.0%}' for r in values['boundaryBands']), fill='#192319')
    atlas.save(output/'lawn-boundary-topview.png')
    return {'status': 'PASS_STATIC_BOUNDARY_LEAF_COVERAGE_NOT_NATIVE_ACCEPTED', 'windows': receipt,
        'method': '0.25mm raster of actual saved leaf triangles, exact native yaw/scale, touching exact source boundaries; no floor or image replacement.',
        'criteria': {'minimumPhysicalCoverByBoundaryBand': {'1to10mm': .12, '10to30mm': .40, '30to100mm': .50},
                     'outsideSourceDomainPermittedCm': 0},
        'limit': 'One millimetre all-LOD radial clearance remains mandatory; actual native edge softness, lighting and material continuity are separate gates.'}


def build(geometry, rural, original, prior, output):
    geometry, rural, original, prior, output = map(lambda p: Path(p).resolve(), (geometry, rural, original, prior, output))
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Use fresh immutable fine lawn output')
    scene, faces, grass, forbidden, source, domain, exclusions, extra, keep = cover.managed_source(geometry, rural, original)
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
                    'composition': f'{48 if compact else 64} fine curved and individually rolled leaves, every leaf retained allLOD; no patch card.'})
    groups, rows, audit = placements(domain, prototypes)
    inputs = {str(p): sha(p) for p in (Path(__file__), HERE/'exterior-lawn-coverage.py', HERE/'exterior-lawn-natural.py',
        HERE/'lawn-geometry.py', HERE/'vegetation.py', HERE/'performance_scene_policy.py', geometry/'scene.json', geometry/'dom-mm.obj',
        rural, rural.parent/'scene.json', rural.parent/'dom-mm.obj', original, prior/'lawn-natural-plan.json',
        prior/'geometry-manifest.json', prior/'material-manifest.json', prior/'lawn-coverage-receipt.json', prior/'lawn-qa-views.json',
        prior/'lawn-natural-prototypes.json')}
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
    audit.update(status='PASS_STATIC_FINE_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED', nativeVerified=False,
        sourceAreaM2=grass.area/1e6, fullSourceLawnM2=source.area/1e6, unmanagedSourceLawnExcludedM2=source.area/1e6-domain.area/10000,
        sourceTriangles=len(faces), exclusionUnionM2=forbidden.area/1e6, sourceMasksUnchanged=True, managedLawnKeepPolygonsPreserved=True,
        allLodGeometryVertices=sum(len(r['positionsCm']) for r in records), allLodGeometryTriangles=sum(len(r['triangles']) for r in records),
        extraExclusionSourceIds=extra, crownProof='Actual allLOD radial envelopes fit exact DOM1/exclusions and pinned managed keep union plus1mm; WPO forbidden.',
        boundaryPlacement='Smaller actual compact footprints and smooth adaptive population density; no independent border row.',
        leavesPerPatchEveryLod={'interior': 64, 'boundary': 48}, lowLeaningLeavesPerPatch={'interior': 48, 'boundary': 36},
        physicalCoverage=coverage, boundaryCoverage=boundary, densityPatchesPerM2=len(rows)/(domain.area/10000),
        bladesPerM2EveryLod=sum(48 if r['edge'] else 64 for r in rows)/(domain.area/10000))
    geometry_manifest = {'schema': 1, **common, 'units': 'metres', 'axes': 'glTF Y-up; Unreal native = [100*x,100*z,100*y]',
        'status': 'OFFLINE_NOT_NATIVE_ACCEPTED', 'meshes': prototypes, 'revision': 'Fine curved mown turf R1'}
    recipe = deepcopy(read(prior/'material-manifest.json')[MATERIAL])
    recipe.update(linearColor=[.04, .075, .025], roughness=.86, specular=.18, subsurfaceScale=.08,
        source='Original authored individual fine turf leaves, actual varied section angles and bounded vertex palette, no photographic claim',
        artDirection='Fine actual leaves, mild root-to-tip and individual leaf response; reduced lime brightness and SSS. Native review required.')
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
    manifest = {**common, 'status': 'PASS_STATIC_COVERAGE_NOT_NATIVE_ACCEPTED', 'geometryManifest': plan['geometryManifest'],
        **{key: {'path': str(output/name), 'sha256': sha(output/name)} for key, name in
           [('materialManifest', 'material-manifest.json'), ('plan', 'lawn-natural-plan.json'), ('geometryProof', 'lawn-natural-prototypes.json'),
            ('coverageReceipt', 'lawn-coverage-receipt.json'), ('glb', 'lawn-natural.glb')]}, 'audit': audit,
        'boundaryCoverageReceipt': common['boundaryCoverageReceipt'],
        'integrationContract': 'Same20 explicit lawn_natural masters/materialkey/screens;64 interior and48 boundary leaves allLOD. Identity-check exact4 inherited40437 lawninstances; preserve ground/collision and unmanaged rural vegetation. New native visual review required.'}
    write(output/'lawn-natural-manifest.json', manifest)
    cameras = deepcopy(read(prior/'lawn-qa-views.json'))
    cameras.update(owner=OWNER, generatorSha256=sha(__file__), managedLawnPlan=common['managedLawnPlan'], plan=manifest['plan'])
    write(output/'lawn-qa-views.json', cameras)
    return {k: v for k, v in audit.items() if k not in ('physicalCoverage', 'boundaryCoverage')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('geometry', 'rural', 'original', 'prior', 'output'): parser.add_argument('--'+key, required=True)
    args = parser.parse_args(); print(json.dumps(build(**vars(args))))
