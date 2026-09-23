"""Short, authored polygon grass on the exact current C/B/B lawn domain.

CPU: python3 -B lawn-geometry.py --geometry <export> --output <lawn-geometry>
Native: apply_geometry(output, geometry, bladeMaterialPath), then save/reload
the map and verify_geometry(output, geometry, returned_report). No source actor
or collision is edited. The four HISM actors have three explicit mesh LODs.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import random
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/lawn-geometry.py'
PREFIX = '/Game/Brezi/Photoreal/Lawn/Meshes'
TAG = 'BreziPhotorealLawn'
PARCEL = 'DOM_00001'
SPACING_MM = 60.
GRID_JITTER = .16
EDGE_XY_SCALE = .24
EDGE_SPACING_MM = 28.
SCREENS = [1., .025, .007]
LOD_BLADES = [64, 32, 12]
LOD_TRIANGLES = [256, 64, 24]
EXTRA_SEMANTICS = [*[f'gravel-strip-{i}' for i in range(1, 4)],
                   *[f'garden-step-{i}' for i in range(1, 5)],
                   'mulch-bed-1', 'mulch-bed-2']


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')


def read(path):
    return json.loads(Path(path).read_text())


def artifact_key(path):
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def vegetation():
    path = ROOT/'scripts/unreal/vegetation.py'
    spec = importlib.util.spec_from_file_location('lawn_geometry_source', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def signed_area(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def inside_triangle(p, triangle):
    values = [signed_area(a, b, p) for a, b in zip(triangle, triangle[1:]+triangle[:1])]
    return min(values) >= -1e-7 or max(values) <= 1e-7


def inside_polygon(p, polygon):
    result = False
    for a, b in zip(polygon, polygon[1:]+polygon[:1]):
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < (b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:
            result = not result
    return result


def distance2(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    length = dx*dx+dy*dy
    t = min(1., max(0., ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length)) if length else 0.
    return (p[0]-a[0]-t*dx)**2+(p[1]-a[1]-t*dy)**2


def bounds(points):
    return {k: [f(p[i] for p in points) for i in range(3)] for k, f in [('min', min), ('max', max)]}


def source_context(geometry):
    geometry = Path(geometry).resolve()
    scene = read(geometry/'scene.json')
    require(scene['activeDesign'] == {'variant': 'C', 'livingLayout': 'B', 'heatingLayout': 'B'}, 'Only C/B/B is supported')
    require(scene['house']['placement']['streetSetbackMm'] == scene['house']['placement']['eastSetbackMm'] == 3000, 'Setbacks changed')
    rows = {r['id']: r for r in scene['objects']}
    require(rows[PARCEL]['enabled'] and rows[PARCEL]['materialSlots'] == ['MAT_0001']
            and rows[PARCEL]['materialNames'] == ['real-grass'] and rows[PARCEL]['triangles'] == 27, 'Wrong source lawn')
    extra = {}
    for semantic in EXTRA_SEMANTICS:
        matching = [r for r in scene['objects'] if r['enabled'] and r['metadata'].get('walkSurfaceId') == semantic]
        require(len(matching) == 1, 'Missing/ambiguous exclusion: '+semantic)
        extra[matching[0]['id']] = semantic
    v = vegetation()
    triangles = v.read_source_triangles(geometry/'dom-mm.obj', scene, {PARCEL, *extra})
    faces = [list(t) for t in triangles[PARCEL]]
    require({p[2] for t in faces for p in t} == {-65.}, 'Lawn elevation changed')
    counts = Counter(tuple(sorted((a, b))) for t in faces for a, b in zip(t, t[1:]+t[:1]))
    require(all(n <= 2 for n in counts.values()), 'Nonmanifold source lawn')
    boundary = [e for e, n in counts.items() if n == 1]
    exclusions = v.exclusion_polygons(scene)
    rect = scene['poolDeck']['outerBoundsMm']
    cx, cy = scene['sceneCenterMm']['x'], scene['sceneCenterMm']['y']
    exclusions.append({'id': 'POOL-DECK-OUTER-ENVELOPE', 'polygonSourceMm':
                       [[x-cx, y-cy] for x, y in [(rect['x0'], rect['y0']), (rect['x1'], rect['y0']),
                                               (rect['x1'], rect['y1']), (rect['x0'], rect['y1'])]]})
    for identity, semantic in extra.items():
        unique = {}
        for triangle in triangles[identity]:
            polygon = [tuple(p[:2]) for p in triangle]
            if abs(signed_area(*polygon)) > 1e-6:
                unique[tuple(sorted(polygon))] = polygon
        require(unique, 'Empty projected exclusion: '+identity)
        for i, polygon in enumerate(unique.values()):
            exclusions.append({'id': identity+'/'+str(i), 'semantic': semantic, 'polygonSourceMm': polygon})
    for record in exclusions:
        points = record['polygonSourceMm']
        record['boundsMm'] = [min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)]
    return scene, faces, boundary, exclusions, extra


def blade_parameters(variant):
    rng = random.Random(739131+variant*2707)
    result = []
    # Spread independent roots through a disk instead of making a radial crown.
    # Adjacent 60mm-spaced patches overlap, hiding the previous isolated tufts.
    for i in range(64):
        phase = i*math.pi*(3-math.sqrt(5))+rng.uniform(-.35, .35)
        radius = math.sqrt((i+rng.uniform(.15, .85))/64)*55.
        short = i % 2 == 1
        result.append({'root': [math.cos(phase)*radius, math.sin(phase)*radius],
                       'angle': rng.uniform(-math.pi, math.pi), 'height': rng.uniform(16., 27.) if short else rng.uniform(32., 45.),
                       'width': rng.uniform(1.7, 2.8) if short else rng.uniform(1.3, 2.5),
                       'lean': rng.uniform(24., 38.) if short else rng.uniform(14., 29.),
                       'twist': rng.uniform(-.7, .7), 'droop': rng.uniform(.12, .25),
                       'cutWidth': rng.uniform(.28, .56), 'short': short,
                       'seeds': [rng.random(), rng.random()]})
    return result


def prototype(variant, lod):
    """Fine bent ribbons with clipped tips, spread through an overlapping patch.

    Near LOD combines 32 curved three-segment canopy leaves with 32 lower,
    wider leaning leaves that cover the spaces at root level. This retains a
    256 triangle budget while improving curvature and projected coverage.
    """
    vertices, uvs, seeds, faces, blade_ranges = [], [], [], [], []
    params = blade_parameters(variant)
    count = LOD_BLADES[lod]
    chosen = [(i*64//count+(i % 2 if count == 32 else 0)) % 64 for i in range(count)]
    for i in chosen:
        b = params[i]
        base = len(vertices)
        levels = [0., 1/3, 2/3, 1.] if lod == 0 and not b['short'] else [0., 1.]
        for t in levels:
            angle = b['angle']+b['twist']*t
            forward = [math.cos(angle), math.sin(angle)]
            across = [-forward[1], forward[0]]
            width = b['width']*((1-t)*.75+t*b['cutWidth']+.45*math.sin(math.pi*t))
            bend = .2*t+.8*t*t
            center = [b['root'][j]+forward[j]*b['lean']*bend for j in range(2)]
            height = b['height']*(t+4*b['droop']*t*(1-t))
            for u in (0., 1.):
                vertices.append([center[0]+across[0]*(u-.5)*width,
                                 center[1]+across[1]*(u-.5)*width, height])
                uvs.append([u, t])
                seeds.append(b['seeds'])
        for level in range(len(levels)-1):
            a = base+level*2
            faces.extend([[a, a+1, a+3], [a, a+3, a+2]])
        blade_ranges.append({'bladeIndex': i, 'vertexOffset': base, 'vertexCount': len(vertices)-base,
                             'segments': len(levels)-1, 'short': b['short']})
    require(len(faces) == LOD_TRIANGLES[lod], 'Unexpected grass topology')
    normals = [[0., 0., 0.] for p in vertices]
    for a, b, c in faces:
        e = [vertices[b][k]-vertices[a][k] for k in range(3)]
        f = [vertices[c][k]-vertices[a][k] for k in range(3)]
        n = [e[1]*f[2]-e[2]*f[1], e[2]*f[0]-e[0]*f[2], e[0]*f[1]-e[1]*f[0]]
        require(sum(x*x for x in n) > 1e-9, 'Degenerate blade triangle')
        for index in (a, b, c):
            normals[index] = [normals[index][k]+n[k] for k in range(3)]
    normals = [[x/math.sqrt(sum(y*y for y in n)) for x in n] for n in normals]
    return {'id': f'LawnTuft{variant}_LOD{lod}', 'variant': variant, 'lod': lod, 'blades': count,
            'verticesMm': vertices, 'uv0': uvs, 'uv1': seeds, 'bladeRanges': blade_ranges,
            'normals': normals, 'faces': faces, 'boundsMm': bounds(vertices)}


def write_glb(path, prototypes):
    """GLTF metres/Y-up. Unreal import performs the one handedness conversion.

    Stored UV.y is root0/tip1; no Blender UV flip is involved in this writer.
    """
    binary = bytearray()
    accessors, views, meshes, nodes = [], [], [], []

    def accessor(values, kind, component=5126, target=34962):
        flat = [x for v in values for x in (v if isinstance(v, list) else [v])]
        while len(binary) % 4:
            binary.append(0)
        start = len(binary)
        binary.extend(struct.pack('<'+('f' if component == 5126 else 'H')*len(flat), *flat))
        view = len(views)
        views.append({'buffer': 0, 'byteOffset': start, 'byteLength': len(binary)-start, 'target': target})
        result = {'bufferView': view, 'componentType': component, 'count': len(values), 'type': kind}
        if kind == 'VEC3':
            result.update(min=[min(p[i] for p in values) for i in range(3)], max=[max(p[i] for p in values) for i in range(3)])
        index = len(accessors)
        accessors.append(result)
        return index

    for p in prototypes:
        positions = [[x/1000, z/1000, -y/1000] for x, y, z in p['verticesMm']]
        normals = [[x, z, -y] for x, y, z in p['normals']]
        attributes = {'POSITION': accessor(positions, 'VEC3'), 'NORMAL': accessor(normals, 'VEC3'),
                      'TEXCOORD_0': accessor(p['uv0'], 'VEC2'), 'TEXCOORD_1': accessor(p['uv1'], 'VEC2')}
        indices = accessor([i for f in p['faces'] for i in f], 'SCALAR', 5123, 34963)
        meshes.append({'name': p['id'], 'primitives': [{'attributes': attributes, 'indices': indices, 'material': 0}]})
        nodes.append({'name': p['id'], 'mesh': len(meshes)-1})
    document = {'asset': {'version': '2.0', 'generator': OWNER}, 'scene': 0,
                'scenes': [{'nodes': list(range(len(nodes)))}], 'nodes': nodes, 'meshes': meshes,
                'materials': [{'name': 'LawnBladePlaceholder', 'doubleSided': True,
                               'pbrMetallicRoughness': {'baseColorFactor': [.16, .24, .055, 1], 'metallicFactor': 0, 'roughnessFactor': .8}}],
                'accessors': accessors, 'bufferViews': views, 'buffers': [{'byteLength': len(binary)}]}
    js = json.dumps(document, separators=(',', ':')).encode()
    js += b' '*((-len(js)) % 4)
    binary += b'\0'*((-len(binary)) % 4)
    Path(path).write_bytes(struct.pack('<III', 0x46546c67, 2, 12+8+len(js)+8+len(binary))+
                           struct.pack('<II', len(js), 0x4e4f534a)+js+struct.pack('<II', len(binary), 0x004e4942)+binary)


def clearance(point, faces, boundary, exclusions):
    """Distance to the union complement; internal lawn triangle edges are ignored."""
    if not any(inside_triangle(point, f) for f in faces):
        return -1., 'outside-lawn'
    minimum = min(distance2(point, *edge) for edge in boundary)
    reason = 'source-boundary'
    for e in exclusions:
        box = e['boundsMm']
        # If the polygon's box is farther than the existing limiting edge,
        # neither its interior nor its edges can become the nearest exclusion.
        dx = max(box[0]-point[0], 0., point[0]-box[2])
        dy = max(box[1]-point[1], 0., point[1]-box[3])
        if dx*dx+dy*dy > minimum:
            continue
        polygon = e['polygonSourceMm']
        if inside_polygon(point, polygon):
            return -1., e['id']
        d = min(distance2(point, a, b) for a, b in zip(polygon, polygon[1:]+polygon[:1]))
        if d < minimum:
            minimum, reason = d, e['id']
    return math.sqrt(minimum), reason


def transformed_bounds(local, point, yaw, scale):
    angle = math.radians(yaw)
    c, s = math.cos(angle), math.sin(angle)
    result = []
    for x, y, z in itertools.product(*[(local['min'][i], local['max'][i]) for i in range(3)]):
        result.append([(point[0]+scale[0]*(c*x-s*y))/10,
                       -(point[1]+scale[1]*(s*x+c*y))/10, (point[2]+scale[2]*z)/10])
    return bounds(result)


def placements(scene, faces, boundary, exclusions, prototypes, spacing=SPACING_MM):
    require(50 <= spacing <= 120, 'Unreviewed grass spacing')
    rng = random.Random(6012260923)
    grouped = {i: [p for p in prototypes if p['variant'] == i] for i in range(4)}
    radii = {i: max(math.hypot(*p[:2]) for lod in lods for p in lod['verticesMm']) for i, lods in grouped.items()}
    groups = [{'id': f'LawnTuft{i}', 'variant': i, 'instances': [], 'boundsUnrealCm':
               {'min': [math.inf]*3, 'max': [-math.inf]*3}} for i in range(4)]
    rejected = Counter()
    occupied = {}
    minimum_margin = math.inf
    area_samples = grid_samples = edge_count = 0
    max_tip = -math.inf

    def attempt(point, edge=False):
        nonlocal minimum_margin, area_samples, grid_samples, edge_count, max_tip
        distance, reason = clearance(point, faces, boundary, exclusions)
        if not edge:
            grid_samples += 1
            if distance > 0:
                area_samples += 1
        if distance <= 0:
            rejected[reason] += 1
            return
        variant = rng.randrange(4)
        height_scale = rng.uniform(.85, 1.)
        xy_scale = height_scale*(EDGE_XY_SCALE if edge else rng.uniform(.94, 1.06))
        radius = radii[variant]*xy_scale+1.
        if distance <= radius:
            rejected['whole-tuft-envelope'] += 1
            return
        key = (math.floor(point[0]/20), math.floor(point[1]/20))
        if any((point[0]-q[0])**2+(point[1]-q[1])**2 < 18**2
               for i in range(-1, 2) for j in range(-1, 2) for q in occupied.get((key[0]+i, key[1]+j), [])):
            rejected['root-spacing'] += 1
            return
        occupied.setdefault(key, []).append(point)
        yaw = rng.uniform(-180, 180)
        scale = [xy_scale, xy_scale, height_scale]
        pos = [point[0], point[1], -65.]
        instance = {'positionUnrealCm': [pos[0]/10, -pos[1]/10, -6.5], 'yawDegreesUnreal': -yaw,
                    'scale': scale, 'edge': edge, 'clearanceMm': distance, 'enclosingRadiusMm': radius}
        group = groups[variant]
        group['instances'].append(instance)
        box = transformed_bounds(grouped[variant][0]['boundsMm'], pos, yaw, scale)
        for k, op in [('min', min), ('max', max)]:
            group['boundsUnrealCm'][k] = [op(a, b) for a, b in zip(group['boundsUnrealCm'][k], box[k])]
        minimum_margin = min(minimum_margin, distance-radius)
        max_tip = max(max_tip, -65+height_scale*grouped[variant][0]['boundsMm']['max'][2])
        edge_count += int(edge)

    box = bounds([p for f in faces for p in f])
    nx = math.ceil((box['max'][0]-box['min'][0])/spacing)
    ny = math.ceil((box['max'][1]-box['min'][1])/spacing)
    for ix in range(nx):
        for iy in range(ny):
            attempt([box['min'][0]+(ix+.5+rng.uniform(-GRID_JITTER, GRID_JITTER))*spacing,
                     box['min'][1]+(iy+.5+rng.uniform(-GRID_JITTER, GRID_JITTER))*spacing])
    # Compact tufts follow the real boundary at irregular 22–29 mm offsets.
    # Both sides are proposed; the exact domain test decides the grass side.
    # This fills the border without a regular 5 cm bare erosion strip.
    edges = list(boundary)
    edges.extend((a, b) for e in exclusions for a, b in zip(e['polygonSourceMm'], e['polygonSourceMm'][1:]+e['polygonSourceMm'][:1]))
    for a, b in edges:
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx, dy)
        if length < 1:
            continue
        n = max(1, int(length/EDGE_SPACING_MM))
        for i in range(n):
            t = (i+rng.uniform(.15, .85))/n
            offset = rng.uniform(22, 29)
            for sign in (-1, 1):
                attempt([a[0]+t*dx-sign*dy/length*offset, a[1]+t*dy+sign*dx/length*offset], True)
    count = sum(len(g['instances']) for g in groups)
    require(20000 <= count <= 130000, 'Unexpected grass instance budget')
    require(count*LOD_TRIANGLES[0] <= 26000000, 'Lawn near-LOD exceeds reviewed 26M triangle budget')
    return {'seed': 6012260923, 'gridSpacingMm': spacing, 'gridJitterFraction': GRID_JITTER,
            'groups': groups, 'instanceCount': count, 'edgeInstanceCount': edge_count,
            'exclusions': exclusions, 'sourceAreaM2': sum(abs(signed_area(*f))/2 for f in faces)/1e6,
            'availableAreaEstimateM2': area_samples*spacing*spacing/1e6,
            'availableAreaMethod': f'{spacing:g}mm jittered area quadrature before patch envelope erosion; estimate, not survey',
            'nominalInteriorBladesPerM2': LOD_BLADES[0]*1e6/(spacing*spacing),
            'edgePatchXyScale': EDGE_XY_SCALE, 'edgeRootSpacingMm': EDGE_SPACING_MM,
            'gridCandidates': grid_samples, 'rejected': dict(rejected), 'maximumTipElevationMm': max_tip,
            'proof': {'method': 'disk enclosing every LOD vertex, inside exact source triangle union and outside all exclusions',
                      'boundarySegmentCount': len(boundary), 'minimumAdditionalMarginMm': minimum_margin,
                      'extraClearanceMm': 1., 'maxWindDisplacementMm': 0., 'sourceTriangleCount': len(faces),
                      'rootElevationUnrealCm': -6.5, 'wpoAllowed': False},
            'allInstancesTriangleBudgetByLod': [count*t for t in LOD_TRIANGLES],
            'cullDistancesCm': [2500, 4000], 'lodScreenSizes': SCREENS}


def coverage_study(placement, prototypes, baseline):
    """Independent nearest-root analysis in a fixed 1m² camera-visible grass ROI.

    This measures distribution gaps, not shaded pixel coverage. A 5mm sample
    lattice bounds the continuous maximum nearest-root distance within +3.54mm.
    """
    region = [-6300., 4700., -5300., 5700.]

    def measure(plan, meshes):
        roots, centers = [], []
        local = {}
        for p in meshes:
            if p['lod'] != 0:
                continue
            base = [point for point, uv in zip(p['verticesMm'], p['uv0']) if uv[1] == 0]
            require(len(base) == 2*p['blades'], 'Root sampling expects paired blade base vertices')
            local[p['variant']] = [[(a+b)/2 for a, b in zip(base[i], base[i+1])] for i in range(0, len(base), 2)]
        for group in plan['groups']:
            for row in group['instances']:
                x, y = row['positionUnrealCm'][0]*10, -row['positionUnrealCm'][1]*10
                if not region[0]-150 <= x <= region[2]+150 or not region[1]-150 <= y <= region[3]+150:
                    continue
                centers.append((x, y))
                angle = -math.radians(row['yawDegreesUnreal'])
                c, s = math.cos(angle), math.sin(angle)
                for a, b, _ in local[group['variant']]:
                    roots.append((x+row['scale'][0]*(c*a-s*b), y+row['scale'][1]*(s*a+c*b)))

        def stats(points):
            bins = {}
            for p in points:
                bins.setdefault((math.floor(p[0]/20), math.floor(p[1]/20)), []).append(p)
            distances = []
            for ix in range(200):
                for iy in range(200):
                    x, y = region[0]+(ix+.5)*5, region[1]+(iy+.5)*5
                    bx, by = math.floor(x/20), math.floor(y/20)
                    nearby = [p for dx in range(-1, 2) for dy in range(-1, 2) for p in bins.get((bx+dx, by+dy), [])]
                    best = min(((x-a)**2+(y-b)**2 for a, b in nearby), default=math.inf)
                    if best >= 400:
                        nearby = [p for dx in range(-3, 4) for dy in range(-3, 4) for p in bins.get((bx+dx, by+dy), [])]
                        best = min(((x-a)**2+(y-b)**2 for a, b in nearby), default=math.inf)
                    if best >= 60**2:
                        nearby = [p for dx in range(-5, 6) for dy in range(-5, 6) for p in bins.get((bx+dx, by+dy), [])]
                        best = min(((x-a)**2+(y-b)**2 for a, b in nearby), default=math.inf)
                    require(math.isfinite(best) and best < 100**2, 'Coverage sample has no nearby root')
                    distances.append(math.sqrt(best))
            distances.sort()
            return {'sampleCount': len(distances), 'p50Mm': distances[len(distances)//2],
                    'p95Mm': distances[int(len(distances)*.95)], 'p99Mm': distances[int(len(distances)*.99)],
                    'maximumSampledMm': distances[-1], 'continuousMaximumUpperBoundMm': distances[-1]+math.sqrt(2)*2.5,
                    'fractionMoreThan10MmFromRoot': sum(d > 10 for d in distances)/len(distances)}
        return {'patchCenters': stats(centers), 'bladeRoots': stats(roots)}

    before = measure(read(baseline/'placement.json'), read(baseline/'prototypes.json'))
    after = measure(placement, prototypes)
    require(after['bladeRoots']['p99Mm'] < before['bladeRoots']['p99Mm']
            and after['bladeRoots']['maximumSampledMm'] < before['bladeRoots']['maximumSampledMm'],
            'New grass root distribution did not improve baseline holes')
    return {'regionSourceMm': region, 'regionAreaM2': 1, 'sampleSpacingMm': 5,
            'baseline': str(baseline), 'baselineInputs': {artifact_key(baseline/n): sha(baseline/n) for n in ('placement.json', 'prototypes.json')},
            'before': before, 'after': after, 'interpretation': 'nearest-root spacing only; not rendered canopy coverage or photorealism acceptance'}


def build(geometry, output):
    geometry, output = Path(geometry).resolve(), Path(output).resolve()
    require(not (output/'geometry-report.json').exists(), 'Use a new output directory; existing recipe is preserved')
    output.mkdir(parents=True, exist_ok=True)
    scene, faces, boundary, exclusions, extra = source_context(geometry)
    prototypes = [prototype(i, lod) for i in range(4) for lod in range(3)]
    write_glb(output/'lawn-prototypes.glb', prototypes)
    code = "import{readFile}from'node:fs/promises';import{validateBytes}from'gltf-validator';const r=await validateBytes(new Uint8Array(await readFile(process.argv[1])),{maxIssues:0});process.stdout.write(JSON.stringify(r.issues));"
    validation = json.loads(subprocess.check_output(['node', '--input-type=module', '-e', code, str(output/'lawn-prototypes.glb')], cwd=ROOT, text=True))
    require(validation['numErrors'] == 0, 'Invalid generated GLB')
    placement = placements(scene, faces, boundary, exclusions, prototypes)
    baseline = ROOT/'output/unreal/lawn-archviz-20260923-r2/lawn-geometry'
    study = coverage_study(placement, prototypes, baseline)
    write(output/'coverage-study.json', study)
    write(output/'placement.json', placement)
    write(output/'prototypes.json', prototypes)
    (output/'generator-source.py').write_bytes(Path(__file__).read_bytes())
    files = {artifact_key(p): sha(p) for p in [geometry/'scene.json', geometry/'dom-mm.obj',
             output/'lawn-prototypes.glb', output/'placement.json', output/'prototypes.json', output/'generator-source.py', output/'coverage-study.json']}
    files.update(study['baselineInputs'])
    pipeline = {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__).resolve(), ROOT/'scripts/unreal/vegetation.py',
                ROOT/'unreal/BreziTwin/Source/BreziTwin/BreziVegetationPatch.cpp', ROOT/'unreal/BreziTwin/Source/BreziTwin/BreziVegetationPatch.h']}
    detail_screens = []
    for p in prototypes:
        if p['lod'] == 0:
            size = [p['boundsMm']['max'][i]-p['boundsMm']['min'][i] for i in range(3)]
            # Unreal's projected bounding-sphere diameter at FOV58, distance1.56m;
            # include the smallest compact-edge XY and height scales.
            radius_mm = math.sqrt(sum((size[i]*.85*(EDGE_XY_SCALE if i < 2 else 1))**2 for i in range(3)))/2
            detail_screens.append(radius_mm/(1560*math.tan(math.radians(29))))
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'offline-lawn-geometry-validated',
              'generatedAt': datetime.now(timezone.utc).isoformat(), 'activeDesign': scene['activeDesign'],
              'sourceSceneSha256': sha(geometry/'scene.json'), 'sourceObjSha256': sha(geometry/'dom-mm.obj'),
              'sourceObjectId': PARCEL, 'sourceMaterialSlot': 'MAT_0001', 'extraExclusionObjectIds': extra,
              'inputFiles': files, 'pipelineFiles': pipeline, 'gltfValidation': validation,
              'instanceCount': placement['instanceCount'], 'edgeInstanceCount': placement['edgeInstanceCount'],
              'availableAreaEstimateM2': placement['availableAreaEstimateM2'], 'sourceAreaM2': placement['sourceAreaM2'],
              'prototypeCount': 4, 'lodTriangles': LOD_TRIANGLES, 'lodBlades': LOD_BLADES,
              'nominalInteriorBladesPerM2': placement['nominalInteriorBladesPerM2'],
              'coverageStudy': study,
              'bladeShape': {'canopyHeightMm': [32, 45], 'understoryHeightMm': [16, 27], 'widthMm': [1.3, 2.8], 'leanMm': [14, 38],
                             'rootPatchDiameterMm': 110, 'tip': 'clipped, 28–56% nominal width',
                             'nearLod': '32 curved three-segment leaves plus 32 low leaning leaves; independent azimuths',
                             'uv1': 'two stable per-blade seeds, constant along each leaf and preserved across LODs'},
              'proof': placement['proof'], 'maximumTipElevationMm': placement['maximumTipElevationMm'],
              'allInstancesTriangleBudgetByLod': placement['allInstancesTriangleBudgetByLod'],
              'lodDetailCameraEstimate': {'distanceM': 1.56, 'horizontalFovDegrees': 58,
                                         'minimumCompactTuftScreenSize': min(detail_screens),
                                         'lod1Threshold': SCREENS[1], 'estimatedLod': 0 if min(detail_screens) >= SCREENS[1] else 1,
                                         'method': 'projected bounding sphere; native LOD choice still requires visual QA'},
              'sourceMutations': [], 'collisionPolicy': 'All new HISM components NoCollision; original lawn remains visible and authoritative.',
              'visualQualityVerified': False, 'nativeImportVerified': False,
              'limits': ['Authored mown lawn, not a scanned or botanically measured plant.',
                         'The source parcel plane intentionally extends below the house; explicit exclusions remove all occupied ground.',
                         'Opaque blades have HISM culling and authored LODs; cull start is configured but opacity does not fade.',
                         'Native visual quality, shadows, LOD transitions and frame time require packaged QA.']}
    write(output/'geometry-report.json', report)
    print(json.dumps({k: report[k] for k in ['status', 'instanceCount', 'edgeInstanceCount', 'availableAreaEstimateM2',
                                            'maximumTipElevationMm', 'lodTriangles', 'allInstancesTriangleBudgetByLod', 'proof']}, indent=2))
    return report


def checked_inputs(output, geometry):
    output, geometry = Path(output).resolve(), Path(geometry).resolve()
    report = read(output/'geometry-report.json')
    require(report['owner'] == OWNER and report['sourceSceneSha256'] == sha(geometry/'scene.json')
            and report['sourceObjSha256'] == sha(geometry/'dom-mm.obj'), 'Lawn source pins differ')
    for path, expected in {**report['inputFiles'], **report['pipelineFiles']}.items():
        require(sha(ROOT/path) == expected, 'Lawn input changed: '+path)
    return report, read(output/'placement.json'), read(output/'prototypes.json')


def vec(value, axes=('x', 'y', 'z')):
    return [float(getattr(value, k)) for k in axes]


def native_transform(value):
    return {'p': vec(value.translation), 'q': vec(value.rotation, ('x', 'y', 'z', 'w')), 's': vec(value.scale3d)}


def source_witness(u):
    result = {}
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if a.actor_has_tag(TAG):
            continue
        for c in a.get_components_by_class(u.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh')
            if not mesh:
                continue
            identity = str(u.EditorAssetLibrary.get_metadata_tag(mesh, 'source_object_id'))
            key = a.get_path_name()+'/'+c.get_name()
            result[key] = {'id': identity, 'mesh': mesh.get_path_name(), 'transform': native_transform(c.get_world_transform()),
                           'actorTransform': native_transform(a.get_actor_transform()), 'actorHidden': bool(a.get_editor_property('hidden')),
                           'collision': str(c.get_collision_enabled()), 'profile': str(c.get_collision_profile_name()),
                           'pawn': str(c.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN)),
                           'materials': [c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())],
                           'visible': bool(c.get_editor_property('visible')), 'hiddenInGame': bool(c.get_editor_property('hidden_in_game'))}
    require(sum(r['id'] == PARCEL for r in result.values()) == 1, 'Missing/ambiguous native source lawn')
    lawn = next(r for r in result.values() if r['id'] == PARCEL)
    require(lawn['visible'] and not lawn['hiddenInGame'] and 'QUERY_AND_PHYSICS' in lawn['collision'], 'Source lawn render/collision policy changed')
    return result


def mesh_proof(u, mesh, prototype_record, lod):
    d = mesh.get_static_mesh_description(lod)
    require(d is not None and d.get_triangle_count() == len(prototype_record['faces']), 'Native grass LOD topology differs')
    expected = []
    for i, p in enumerate(prototype_record['verticesMm']):
        expected.append(([p[0]/10, -p[1]/10, p[2]/10], prototype_record['uv0'][i], prototype_record['uv1'][i]))
    max_position = max_uv = 0.
    actual_faces = []
    for i in range(d.get_triangle_count()):
        actual_face = []
        for corner in range(3):
            vi = d.get_triangle_vertex_instance(u.TriangleID(id_value=i), corner)
            p = vec(d.get_vertex_position(d.get_vertex_instance_vertex(vi)))
            uv = vec(d.get_vertex_instance_uv(vi, 0), ('x', 'y'))
            uv1 = vec(d.get_vertex_instance_uv(vi, 1), ('x', 'y'))
            matches = [(max(abs(a-b) for a, b in zip(p, point)),
                        max(abs(a-b) for a, b in zip(uv+uv1, wanted+seed)), index)
                       for index, (point, wanted, seed) in enumerate(expected)]
            pe, ue, index = min(matches)
            require(pe < .002 and ue < .00002, 'Native grass position/root-tip UV0/per-blade UV1 differs')
            max_position, max_uv = max(max_position, pe), max(max_uv, ue)
            actual_face.append(index)
        actual_faces.append(actual_face)
    cyclic = lambda f: min(tuple(f[i:]+f[:i]) for i in range(3))
    require(Counter(map(cyclic, actual_faces)) == Counter(map(cyclic, prototype_record['faces'])),
            'Native grass triangle connectivity/winding differs')
    require(mesh.get_num_triangles(lod) == len(prototype_record['faces']), 'Render triangle count differs')
    require(mesh.get_num_tex_coords(lod) == 2, 'Native grass must preserve exactly UV0 and seed UV1')
    return {'triangles': d.get_triangle_count(), 'maximumPositionErrorCm': max_position, 'maximumUVError': max_uv,
            'triangleConnectivityWindingVerified': True, 'uvChannelsVerified': [0, 1]}


def make_transform(u, row):
    angle = math.radians(row['yawDegreesUnreal'])/2
    result = u.Transform()
    result.set_editor_property('translation', u.Vector(*row['positionUnrealCm']))
    result.set_editor_property('rotation', u.Quat(0., 0., math.sin(angle), math.cos(angle)))
    result.set_editor_property('scale3d', u.Vector(*row['scale']))
    return result


def static_mesh_subsystem(u):
    """Load the owner module before querying its dynamically registered subsystem.

    A reflected StaticMeshEditorSubsystem class can already be visible to Python
    while its module has not run StartupModule in a NullRHI commandlet. The
    module-loaded notification registers UEditorSubsystem instances. Deprecated
    EditorStaticMeshLibrary simply repeats this lookup and cannot fix it.
    """
    subsystem = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    if subsystem is None:
        u.load_module('StaticMeshEditor')
        subsystem = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    require(subsystem is not None, 'StaticMeshEditor module loaded without its editor subsystem')
    # SetLodFromStaticMesh and SetLodBuildSettings dereference this dependency.
    # Fail cleanly before importing/mutating grass if the host lacks it.
    require(u.get_editor_subsystem(u.AssetEditorSubsystem) is not None, 'AssetEditorSubsystem unavailable for grass LOD construction')
    return subsystem


def finish_static_mesh_compilation(u, synchronous=False):
    """Editor-process-only barrier; never writes a project or runtime cvar.

    UE's standard compilation command is registered in StaticMeshCompiler.cpp
    and directly invokes FStaticMeshCompilingManager::FinishAllCompilation.
    Screen-size reads must follow completed PostLoad/PostEdit render-data work.
    """
    world = u.get_editor_subsystem(u.LevelEditorSubsystem).get_current_level().get_outer()
    if synchronous:
        u.SystemLibrary.execute_console_command(world, 'Editor.AsyncStaticMeshCompilation 0')
        require(u.SystemLibrary.get_console_variable_int_value('Editor.AsyncStaticMeshCompilation') == 0,
                'Cannot enable synchronous static mesh compilation for editor import')
    u.SystemLibrary.execute_console_command(world, 'Editor.AsyncStaticMeshCompilationFinishAll')


def checked_lod_screens(subsystem, mesh):
    screens = list(subsystem.get_lod_screen_sizes(mesh))
    require(len(screens) == 3 and all(abs(a-b) < 1e-6 for a, b in zip(screens, SCREENS)),
            'Native grass LOD screen sizes differ: '+mesh.get_path_name()+' actual='+repr(screens)+' expected='+repr(SCREENS))
    return screens


def apply_geometry(output, geometry, bladeMaterialPath):
    """Called only in native UE by the parent pipeline; caller saves/reloads map."""
    import unreal as u
    output, geometry = Path(output).resolve(), Path(geometry).resolve()
    offline, plan, prototypes = checked_inputs(output, geometry)
    subsystem = static_mesh_subsystem(u)
    finish_static_mesh_compilation(u, synchronous=True)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    assets = u.EditorAssetLibrary
    material = assets.load_asset(bladeMaterialPath)
    require(material is not None, 'Missing grass blade material')
    require(not any(a.actor_has_tag(TAG) for a in actors.get_all_level_actors()), 'Lawn already exists; use fresh map')
    before_source = source_witness(u)
    pipelines = []
    for source, name in [('GLTFSceneAssets', 'Assets'), ('GLTFMaterials', 'Materials'), ('LevelActors', 'Level')]:
        pipeline = assets.duplicate_asset('/Game/Brezi/Pipeline/'+source, PREFIX+'/Pipeline/'+name)
        require(pipeline, 'Cannot create lawn import pipeline')
        pipelines.append(pipeline)
    mp = pipelines[0].get_editor_property('mesh_pipeline')
    for name, value in [('combine_static_meshes_behavior', u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE),
                        ('collision', False), ('build_nanite', False), ('generate_lightmap_u_vs', False)]:
        mp.set_editor_property(name, value)
    common = pipelines[0].get_editor_property('common_meshes_properties')
    for name, value in [('remove_degenerates', False), ('recompute_normals', False), ('recompute_tangents', True),
                        ('use_high_precision_tangent_basis', True), ('use_full_precision_u_vs', True)]:
        common.set_editor_property(name, value)
    pipelines[2].set_editor_property('scene_hierarchy_type', u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
    params = u.ImportAssetParameters()
    for name, value in [('is_automated', True), ('replace_existing', False), ('force_show_dialog', False),
                        ('override_pipelines', [u.SoftObjectPath(p.get_path_name()) for p in pipelines]),
                        ('import_level', u.get_editor_subsystem(u.LevelEditorSubsystem).get_current_level())]:
        params.set_editor_property(name, value)
    old = {a.get_path_name() for a in actors.get_all_level_actors()}
    manager = u.InterchangeManager.get_interchange_manager_scripted()
    require(manager.import_scene(PREFIX, manager.create_source_data(str(output/'lawn-prototypes.glb')), params), 'Lawn Interchange import failed')
    imported, temporary = {}, []
    selected = {p['id']: p for p in prototypes}
    for actor in actors.get_all_level_actors():
        if actor.get_path_name() in old:
            continue
        temporary.append(actor)
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh')
            require(mesh and mesh.get_path_name().startswith(PREFIX+'/'), 'Foreign imported lawn mesh')
            matches = [name for name in selected if name in mesh.get_name()]
            require(len(matches) == 1 and matches[0] not in imported, 'Ambiguous lawn prototype import')
            imported[matches[0]] = mesh
            mesh.set_material(0, material)
            mesh.set_editor_property('has_navigation_data', False)
            assets.set_metadata_tag(mesh, 'BreziGeneratedBy', OWNER)
    require(set(imported) == set(selected), 'Incomplete lawn prototype import')
    lod_proofs = {}
    for variant in range(4):
        mesh = imported[f'LawnTuft{variant}_LOD0']
        for lod in (1, 2):
            require(subsystem.set_lod_from_static_mesh(mesh, lod, imported[f'LawnTuft{variant}_LOD{lod}'], 0, True) == lod,
                    'Cannot attach authored grass LOD')
        for lod in range(3):
            settings = subsystem.get_lod_build_settings(mesh, lod)
            settings.set_editor_property('use_full_precision_u_vs', True)
            settings.set_editor_property('generate_lightmap_u_vs', False)
            settings.set_editor_property('recompute_normals', False)
            subsystem.set_lod_build_settings(mesh, lod, settings)
        finish_static_mesh_compilation(u)
        lod_proofs[str(variant)] = [mesh_proof(u, mesh, selected[f'LawnTuft{variant}_LOD{lod}'], lod) for lod in range(3)]
        # SetLodScreenSizes does not Modify/MarkPackageDirty/PostEdit by itself.
        # Write it after the final build, then force serialization of the values.
        mesh.modify(True)
        require(subsystem.set_lod_screen_sizes(mesh, SCREENS), 'Cannot configure lawn LOD screen sizes')
        checked_lod_screens(subsystem, mesh)
        require(assets.save_loaded_asset(mesh, False), 'Cannot save lawn mesh')
    for mesh in imported.values():
        require(assets.save_loaded_asset(mesh), 'Cannot save imported lawn prototype')
    for actor in temporary:
        require(actors.destroy_actor(actor), 'Cannot remove temporary lawn import actor')
    groups = {}
    for group in plan['groups']:
        actor = actors.spawn_actor_from_class(u.load_class(None, '/Script/BreziTwin.BreziVegetationPatch'), u.Vector(0, 0, 0), u.Rotator())
        require(actor, 'Cannot spawn lawn HISM')
        actor.tags = [u.Name('BreziGenerated'), u.Name(TAG), u.Name('BreziPhotorealSource:'+PARCEL)]
        actor.set_actor_label(group['id']+' · krátky archviz trávnik')
        actor.set_folder_path('Brezi/Photoreal/Lawn')
        actor.set_actor_tick_enabled(False)
        c = actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(c, 'Missing lawn HISM component')
        mesh = imported[f'LawnTuft{group["variant"]}_LOD0']
        c.set_static_mesh(mesh)
        c.set_collision_profile_name('NoCollision')
        c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        c.set_editor_property('can_ever_affect_navigation', False)
        c.set_editor_property('generate_overlap_events', False)
        c.set_component_tick_enabled(False)
        c.set_cull_distances(*plan['cullDistancesCm'])
        c.set_editor_property('component_tags', [u.Name(TAG)])
        c.set_editor_property('cast_shadow', True)
        c.set_editor_property('visible_in_ray_tracing', True)
        c.set_editor_property('affect_distance_field_lighting', False)
        indices = list(c.add_instances([make_transform(u, row) for row in group['instances']], True, False, False))
        require(indices == list(range(len(group['instances']))), 'Lawn HISM insertion order differs')
        actor.synchronize_instance_bounds()
        groups[group['id']] = {'actor': actor.get_path_name(), 'mesh': mesh.get_path_name(), 'instances': len(indices), 'variant': group['variant']}
    for pipeline in pipelines:
        assets.save_loaded_asset(pipeline)
    require(source_witness(u) == before_source, 'Lawn stage changed canonical source')
    return {'owner': OWNER, 'geometryReportSha256': sha(output/'geometry-report.json'), 'groups': groups,
            'material': bladeMaterialPath, 'lodProofs': lod_proofs, 'sourceWitnessSha256': digest(before_source),
            'existingStaticMeshComponentsWitnessed': len(before_source), 'sourceUnchanged': True, 'savedReloaded': False,
            'editorCompilePolicy': 'synchronous static-mesh compilation in this editor process; no project/runtime config change',
            'inputFiles': {**offline['inputFiles'], str((output/'geometry-report.json').relative_to(ROOT)): sha(output/'geometry-report.json')},
            'pipelineFiles': offline['pipelineFiles'], 'visualQualityVerified': False}


def verify_geometry(output, geometry, report):
    import unreal as u
    output = Path(output).resolve()
    offline, plan, prototypes = checked_inputs(output, geometry)
    subsystem = static_mesh_subsystem(u)
    finish_static_mesh_compilation(u)
    require(report['owner'] == OWNER and report['geometryReportSha256'] == sha(output/'geometry-report.json'), 'Native lawn recipe differs')
    actors = {a.get_path_name(): a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    require({a.get_path_name() for a in actors.values() if a.actor_has_tag(TAG)} == {r['actor'] for r in report['groups'].values()}, 'Native lawn actor inventory differs')
    max_position = max_scale = max_rotation = max_bounds = 0.
    count = 0
    for group in plan['groups']:
        entry = report['groups'][group['id']]
        actor = actors[entry['actor']]
        c = actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        mesh = c.get_editor_property('static_mesh')
        require(mesh.get_path_name() == entry['mesh'] and mesh.get_material(0).get_path_name() == report['material']
                and c.get_material(0).get_path_name() == report['material'], 'Lawn mesh/material binding differs')
        require(c.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION and str(c.get_collision_profile_name()) == 'NoCollision'
                and not c.get_editor_property('can_ever_affect_navigation') and not c.get_editor_property('generate_overlap_events'), 'Lawn collision/navigation changed')
        require(c.is_visible() and not c.get_editor_property('hidden_in_game') and not actor.is_actor_tick_enabled()
                and not c.is_component_tick_enabled(), 'Lawn render/tick state differs')
        require(c.get_editor_property('instance_start_cull_distance') == 2500 and c.get_editor_property('instance_end_cull_distance') == 4000, 'Lawn cull distances differ')
        identity = native_transform(u.Transform())
        require(native_transform(actor.get_actor_transform()) == identity and native_transform(c.get_world_transform()) == identity, 'Lawn world transform differs')
        require(c.get_instance_count() == len(group['instances']), 'Native lawn instance count differs')
        for i, row in enumerate(group['instances']):
            value = c.get_instance_transform(i, False)
            if isinstance(value, tuple):
                require(len(value) == 2 and value[0] is True, 'Cannot read native lawn instance')
                value = value[1]
            actual, wanted = native_transform(value), native_transform(make_transform(u, row))
            pe = max(abs(a-b) for a, b in zip(actual['p'], wanted['p']))
            se = max(abs(a-b) for a, b in zip(actual['s'], wanted['s']))
            qe = min(max(abs(a-sign*b) for a, b in zip(actual['q'], wanted['q'])) for sign in (1, -1))
            require(pe < .002 and se < 2e-6 and qe < 2e-5, 'Lawn instance transform differs')
            max_position, max_scale, max_rotation = max(max_position, pe), max(max_scale, se), max(max_rotation, qe)
        origin, extent, _ = u.SystemLibrary.get_component_bounds(c)
        measured = {'min': vec(origin-extent), 'max': vec(origin+extent)}
        error = max(abs(measured[k][i]-group['boundsUnrealCm'][k][i]) for k in ('min', 'max') for i in range(3))
        require(error < .08, 'Lawn component bounds differ')
        max_bounds = max(max_bounds, error)
        for lod in range(3):
            mesh_proof(u, mesh, next(p for p in prototypes if p['variant'] == group['variant'] and p['lod'] == lod), lod)
        checked_lod_screens(subsystem, mesh)
        count += c.get_instance_count()
    require(digest(source_witness(u)) == report['sourceWitnessSha256'], 'Canonical lawn/source changed after reload')
    report.update(savedReloaded=True, nativeImportVerified=True, instanceCount=count, hismComponents=4,
                  maximumPositionErrorCm=max_position, maximumScaleError=max_scale, maximumRotationError=max_rotation,
                  maximumBoundsErrorCm=max_bounds, sourceUnchanged=True, collision='NoCollision', lodTriangles=LOD_TRIANGLES,
                  lodScreenSizes=SCREENS, cullDistancesCm=[2500, 4000], internalHismTreeBytesRead=False)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--geometry', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    build(args.geometry, args.output)
