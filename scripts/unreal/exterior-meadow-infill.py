"""Small, source-only low meadow pilot inside the existing bare parcel lobes.

Six new narrow, pointed twelve-leaf masters reuse the unchanged PH grass02
recipe. All original ground, soil overlays, removals and vegetation remain
untouched. Two actual source-camera sectors bound the cost; this is authored
ecology, not surveyed vegetation or a native visual/performance acceptance.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import struct

import numpy as np
from PIL import Image, ImageDraw
import shapely
from shapely.geometry import Point, Polygon, box, shape, mapping
from shapely.ops import unary_union, nearest_points

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-meadow-infill.py'
OUTPUT = ROOT/'output/unreal/exterior-meadow-infill-20261001-r1-study'
TRANSITION = ROOT/'output/unreal/exterior-neighborhood-transition-20261001-r1-study/transition-plan.json'
CONTEXT = ROOT/'output/unreal/exterior-context-20260927-r8/context-plan.json'
NEIGHBORHOOD = ROOT/'output/unreal/exterior-context-20260930-r3/neighborhood-details.json'
BUILDINGS = ROOT/'output/unreal/exterior-buildings-20260926-r2/building-plan.json'
FOOTPRINTS = ROOT/'output/unreal/exterior-neighborhood-seam-diagnostic-20261001-r1/soil-exposure-footprints.json'
LIBRARY = ROOT/'output/unreal/exterior-assets-shape-20261001-r1/geometry-manifest.json'
MATERIALS = LIBRARY.with_name('material-manifest.json')
UV_BODY = ROOT/'output/unreal/exterior-lawn-photo-uv-20261001-r2-study/closure.json'
CAMERAS = ROOT/'output/unreal/exterior-20261001-r12c/Project/BreziTwin/Content/Data/viewpoints.json'
REPORT = ROOT/'output/unreal/exterior-20261001-r12c/exterior-import-report.json'
OLD_BLADE = ROOT/'output/unreal/rural-context-20260923-r4/lawn-geometry/prototypes.json'
MATERIAL = 'ph_grass_medium_02'
SEED = 60122620261014
TARGET_ROOTS, MAX_ROOTS, MAX_NEAR_TRIANGLES = 36000, 40000, 2000000
SCENES = ('exterior-parcels', 'exterior-canopy-lod')
spec = importlib.util.spec_from_file_location('meadow_source_triangle_tools', ROOT/'scripts/unreal/exterior-neighborhood-seam-diagnostic.py')
diag = importlib.util.module_from_spec(spec); spec.loader.exec_module(diag)


def require(ok, message):
    if not ok: raise ValueError(message)


def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pin(path): return {'path': str(Path(path).resolve()), 'sha256': sha(path)}
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, separators=(',', ':'), allow_nan=False); stream.write('\n')


def smooth(value):
    t = np.clip(value, 0., 1.); return t*t*(3.-2.*t)


def noise(x, y, scale, seed):
    """World anchored interpolated hash noise, used only to author placements."""
    px, py = np.asarray(x)/scale, np.asarray(y)/scale
    ix, iy = np.floor(px), np.floor(py); fx, fy = smooth(px-ix), smooth(py-iy)
    def h(a, b):
        v = np.sin(a*127.1+b*311.7+seed)*43758.5453; return v-np.floor(v)
    return (h(ix, iy)*(1-fx)+h(ix+1, iy)*fx)*(1-fy)+(h(ix, iy+1)*(1-fx)+h(ix+1, iy+1)*fx)*fy


def source_domain():
    transition, context, neighborhood, buildings = map(read, (TRANSITION, CONTEXT, NEIGHBORHOOD, BUILDINGS))
    require(sha(TRANSITION) == '2be538a9311282d9b8485d925fa070b3984b50cea852ea2e7406ed1699448ef5', 'Frozen transition basis changed')
    require(context['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'C/B/B differs')
    require(context['housePlacement']['streetSetbackMm'] == context['housePlacement']['eastSetbackMm'] == 3000, 'Setbacks differ')
    require(all(d['sourceSceneSha256'] == context['sourceSceneSha256'] and d['sourceObjSha256'] == context['sourceObjSha256']
                for d in (transition, neighborhood, buildings)), 'Source frame differs')
    wanted = {r['sourceMeshId'] for r in transition['materialBindingProposal']}
    meshes = [r for r in context['meshes'] if r['id'] in wanted]
    require(len(meshes) == len(wanted) == 65, 'Exact65 ground surfaces required')
    triangles, ground_rows, ground_index = diag.geometry(meshes)
    original = unary_union(triangles)
    protected = unary_union([Polygon(t) for t in context['protectedTrianglesCm']]).buffer(30)
    roads = unary_union([Polygon([m['verticesCm'][i][:2] for i in m['indices'][j:j+3]])
                         for m in context['meshes'] if m['material'] == 'context_track'
                         for j in range(0, len(m['indices']), 3)]).buffer(20)
    solid = unary_union([Polygon(rings[0], rings[1:]) for b in buildings['buildings'] for rings in b['polygonsCm']]).buffer(150)
    blockers = protected.union(roads).union(solid)
    allowed = original.difference(blockers)
    require(allowed.symmetric_difference(shape(transition['targetGroundDomainCm'])).area < .00001, 'Actual source mask differs')
    soil = shape(read(FOOTPRINTS)['geometry'])
    views = {r['id']: r for r in read(CAMERAS)['views']}
    pilots = {}
    for scene in SCENES:
        view = views[scene]; eye = np.asarray(view['eyeCm'][:2]); aim = np.asarray(view['targetCm'][:2])-eye
        theta = math.atan2(aim[1], aim[0]); half = math.radians(view['horizontalFovDegrees']/2.)
        arc = [eye.tolist()]+[(eye+1200*np.array([math.cos(a), math.sin(a)])).tolist()
                             for a in np.linspace(theta-half, theta+half, 180)]+[eye.tolist()]
        sector = Polygon(arc)
        # Whole bare lobes close to the actual cameras, plus a contact band.
        # The variable authored outside width is checked separately per root.
        pilot = allowed.intersection(soil.buffer(100)).intersection(sector)
        pilots[scene] = {'view': view, 'geometry': pilot, 'sector': sector, 'angle': theta, 'half': half}
    pilot = unary_union([p['geometry'] for p in pilots.values()])
    return {'transition': transition, 'context': context, 'neighborhood': neighborhood, 'meshes': meshes,
            'allowed': allowed, 'blockers': blockers, 'soil': soil, 'pilot': pilot, 'pilots': pilots,
            'groundRows': ground_rows, 'groundIndex': ground_index}


def photo_uv(normalized, strip):
    t = np.asarray(normalized)[:, 1]; stations = np.linspace(0, 1, len(strip))
    low = np.interp(t, stations, strip[:, 1])+1.5/2048
    high = np.interp(t, stations, strip[:, 2])-1.5/2048
    require(np.all(high > low), 'Original connected photo strip collapsed')
    return np.column_stack([.768+(.352-.768)*t, low+(high-low)*np.asarray(normalized)[:, 0]])


def mesh(variant, lod, strip):
    rng = random.Random(SEED+variant*701)
    points, uv, uv1, colors, triangles, leaves = [], [], [], [], [], []
    # Four actual longitudinal V sections near, two mid, none far. All twelve
    # leaves, their root/peak/tip positions and narrow silhouette remain.
    folds = (4, 2, 0)[lod]
    maximum_height = (3.2, 4.1, 4.9, 5.8, 6.7, 7.5)[variant]
    for leaf in range(12):
        angle = rng.uniform(-math.pi, math.pi); radius = math.sqrt(rng.random())*1.05
        origin = np.array([math.cos(angle)*radius, math.sin(angle)*radius])
        heading = rng.uniform(-math.pi, math.pi); bend = rng.uniform(-.36, .36)
        height = maximum_height*rng.uniform(.66, 1.0)
        reach = rng.uniform(2.5, 4.25)*(1.0 if leaf % 4 else .82)
        width = rng.uniform(.22, .35); peak = rng.uniform(.33, .44)
        roll, twist = rng.uniform(-.24, .24), rng.uniform(-.46, .46)
        folded = leaf < folds; start = len(points); first = len(triangles); rings, centers = [], []
        def center(t):
            a = heading+bend*t; forward = np.array([math.cos(a), math.sin(a)])
            xy = origin+forward*reach*(.42*t+.58*t*t)
            z = height*(t+.13*math.sin(math.pi*t)-.035*t*t)
            return np.array([*xy, z])
        for t, us in ((0., [0., .5, 1.] if folded else [0., 1.]),
                      (peak, [0., .5, 1.] if folded else [0., 1.]), (1., [.5])):
            c = center(t); tangent = center(t+.0001)-center(t-.0001); tangent /= np.linalg.norm(tangent)
            side = np.array([-math.sin(heading+bend*t), math.cos(heading+bend*t), 0.])
            n = np.cross(tangent, side); n /= np.linalg.norm(n)
            side = side*math.cos(roll+twist*t)+n*math.sin(roll+twist*t)
            n = np.cross(tangent, side); n /= np.linalg.norm(n)
            actual_width = width*(.48 if t == 0 else 1. if t < 1 else 0.)
            ring = []
            for u in us:
                ridge = actual_width*.5*math.tan(.19) if folded and u == .5 and t < 1 else 0.
                ring.append(len(points)); points.append((c+side*actual_width*(u-.5)+n*ridge).tolist())
                uv.append([u, t]); uv1.append([leaf/12., variant/6.]); colors.append([1., 1., 1., 1.])
            rings.append(ring); centers.append(c.tolist())
        lift = max(0., -min(p[2] for p in points[start:]))
        for p in points[start:]: p[2] += lift
        for p in centers: p[2] += lift
        root, shoulder, tip = rings
        if folded:
            triangles.extend([[root[0], root[1], shoulder[0]], [root[1], shoulder[1], shoulder[0]],
                [root[1], root[2], shoulder[1]], [root[2], shoulder[2], shoulder[1]],
                [shoulder[0], shoulder[1], tip[0]], [shoulder[1], shoulder[2], tip[0]]])
        else:
            triangles.extend([[root[0], root[1], shoulder[0]], [root[1], shoulder[1], shoulder[0]],
                              [shoulder[0], shoulder[1], tip[0]]])
        leaves.append({'leaf': leaf, 'vertexOffset': start, 'vertexCount': len(points)-start,
                       'triangleOffset': first, 'triangleCount': len(triangles)-first,
                       'centerlineCm': centers, 'widthCm': width, 'heightCm': height, 'reachCm': reach,
                       'peakT': peak, 'folded': folded, 'pointedTip': True, 'tipWidthCm': 0.})
    mid = f'parcel_low_meadow_{variant}'
    p = np.asarray(points)
    return {'nodeName': mid+'_LOD'+str(lod), 'meshId': mid, 'level': lod, 'positionsCm': points,
            'uv0': photo_uv(uv, strip).tolist(), 'uv1': uv1, 'colors': colors, 'triangles': triangles,
            'leaves': leaves, 'expectedBoundsCm': {'min': p.min(0).tolist(), 'max': p.max(0).tolist()},
            'radialEnvelopeCm': float(np.linalg.norm(p[:, :2], axis=1).max())}


def basis(record):
    p, uv, faces = map(np.asarray, (record['positionsCm'], record['uv0'], record['triangles']))
    normal, tangent, bitangent = (np.zeros_like(p) for _ in range(3))
    for face in faces:
        a, b, c = face; e1, e2 = p[b]-p[a], p[c]-p[a]; n = np.cross(e1, e2)
        d1, d2 = uv[b]-uv[a], uv[c]-uv[a]; det = np.cross(d1, d2)
        require(np.dot(n, n) > 1e-14 and abs(det) > 1e-12, 'Degenerate leaf geometry/UV')
        normal[face] += n; tangent[face] += (e1*d2[1]-e2*d1[1])/det; bitangent[face] += (e2*d1[0]-e1*d2[0])/det
    normal /= np.linalg.norm(normal, axis=1)[:, None]
    tangent -= normal*(normal*tangent).sum(1)[:, None]; tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    sign = np.where((np.cross(normal, tangent)*bitangent).sum(1) < 0, -1., 1.)
    require(np.isfinite(normal).all() and np.isfinite(tangent).all(), 'Nonfinite geometry frame')
    return normal, np.column_stack([tangent, sign])


def write_glb(path, records):
    binary = bytearray(); doc = {'asset': {'version': '2.0', 'generator': OWNER}, 'scene': 0,
        'scenes': [{'nodes': list(range(len(records)))}], 'nodes': [], 'meshes': [], 'bufferViews': [], 'accessors': [],
        'materials': [{'name': MATERIAL, 'doubleSided': True, 'alphaMode': 'MASK', 'alphaCutoff': .333,
                       'pbrMetallicRoughness': {'baseColorFactor': [1., 1., 1., 1.], 'metallicFactor': 0., 'roughnessFactor': .8}}]}
    def acc(values, kind, dtype='<f4', target=34962):
        a = np.asarray(values, dtype=dtype); binary.extend(b'\0'*(-len(binary)%4)); start = len(binary); binary.extend(a.tobytes())
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': a.nbytes, 'target': target})
        row = {'bufferView': len(doc['bufferViews'])-1, 'componentType': 5126 if dtype == '<f4' else 5125,
               'count': len(a), 'type': kind}
        if kind == 'VEC3': row.update(min=a.min(0).tolist(), max=a.max(0).tolist())
        doc['accessors'].append(row); return len(doc['accessors'])-1
    for r in records:
        n, t = basis(r); p = np.asarray(r['positionsCm'])[:, [0, 2, 1]]/100
        gt = np.column_stack([t[:, :3][:, [0, 2, 1]], -t[:, 3]])
        attr = {'POSITION': acc(p, 'VEC3'), 'NORMAL': acc(n[:, [0, 2, 1]], 'VEC3'), 'TANGENT': acc(gt, 'VEC4'),
                'TEXCOORD_0': acc(r['uv0'], 'VEC2'), 'TEXCOORD_1': acc(r['uv1'], 'VEC2'), 'COLOR_0': acc(r['colors'], 'VEC4')}
        ids = acc(np.asarray(r['triangles'])[:, [0, 2, 1]].reshape(-1), 'SCALAR', '<u4', 34963)
        doc['meshes'].append({'name': r['nodeName'], 'primitives': [{'attributes': attr, 'indices': ids, 'material': 0}]})
        doc['nodes'].append({'name': r['nodeName'], 'mesh': len(doc['meshes'])-1})
    binary.extend(b'\0'*(-len(binary)%4)); doc['buffers'] = [{'byteLength': len(binary)}]
    raw = json.dumps(doc, separators=(',', ':')).encode(); raw += b' '*(-len(raw)%4)
    with Path(path).open('xb') as stream:
        stream.write(struct.pack('<4sII', b'glTF', 2, 28+len(raw)+len(binary)))
        stream.write(struct.pack('<II', len(raw), 0x4e4f534a)); stream.write(raw)
        stream.write(struct.pack('<II', len(binary), 0x004e4942)); stream.write(binary)


def decode_glb(path):
    raw = Path(path).read_bytes(); require(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Invalid GLB')
    count, kind = struct.unpack_from('<II', raw, 12); require(kind == 0x4e4f534a, 'Missing GLB JSON')
    doc = json.loads(raw[20:20+count]); size, kind = struct.unpack_from('<II', raw, 20+count)
    require(kind == 0x004e4942 and 28+count+size == len(raw), 'Invalid binary extent'); data = raw[28+count:]
    def acc(i):
        a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
        require('sparse' not in a and 'byteStride' not in v, 'Unexpected accessor packing')
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        return np.frombuffer(data, {5126: '<f4', 5125: '<u4', 5123: '<u2'}[a['componentType']],
            count=a['count']*width, offset=v.get('byteOffset', 0)+a.get('byteOffset', 0)).reshape(-1, width).astype(float)
    rows = []
    for node in doc['nodes']:
        prims = doc['meshes'][node['mesh']]['primitives']; require(len(prims) == 1, 'Unexpected multi primitive')
        primitive = prims[0]; a = primitive['attributes']; tang = acc(a['TANGENT'])
        rows.append({'nodeName': node['name'], 'positionsCm': acc(a['POSITION'])[:, [0, 2, 1]]*100,
            'normals': acc(a['NORMAL'])[:, [0, 2, 1]], 'tangents': np.column_stack([tang[:, :3][:, [0, 2, 1]], -tang[:, 3]]),
            'uv0': acc(a['TEXCOORD_0']), 'uv1': acc(a['TEXCOORD_1']) if 'TEXCOORD_1' in a else None,
            'colors': acc(a['COLOR_0']) if 'COLOR_0' in a else None,
            'triangles': acc(primitive['indices']).reshape(-1, 3).astype('int64')[:, [0, 2, 1]]})
    return doc, rows


def contact_width(x, y): return 75.+15.*np.sin(np.asarray(x)/110.)+10.*np.sin(np.asarray(y)/67.)


def pilot_weight(x, y, source):
    amount = np.zeros_like(np.asarray(x), dtype=float)
    for p in source['pilots'].values():
        eye = np.asarray(p['view']['eyeCm'][:2]); dx, dy = x-eye[0], y-eye[1]
        r = np.hypot(dx, dy); a = np.abs(np.arctan2(np.sin(np.arctan2(dy, dx)-p['angle']), np.cos(np.arctan2(dy, dx)-p['angle'])))
        weight = (1.-smooth((r-1000.)/200.))*(1.-smooth((a-(p['half']-.12))/.12))
        amount = np.maximum(amount, weight)
    return amount


def placements(source, decoded):
    rng = np.random.default_rng(SEED); radii, heights = {}, {}
    for v in range(6):
        points = np.concatenate([r['positionsCm'] for r in decoded if r['nodeName'].startswith(f'parcel_low_meadow_{v}_')])
        radii[v] = float(np.linalg.norm(points[:, :2], axis=1).max()); heights[v] = float(points[:, 2].max())
    xy = []
    for pilot in source['pilots'].values():
        xmin, ymin, xmax, ymax = pilot['geometry'].bounds
        xs, ys = np.meshgrid(np.arange(xmin, xmax, 2.45), np.arange(ymin, ymax, 2.45))
        x, y = xs.ravel(), ys.ravel(); x += rng.uniform(-1.08, 1.08, len(x)); y += rng.uniform(-1.08, 1.08, len(y))
        inside = shapely.contains_xy(pilot['geometry'], x, y); xy.extend(zip(x[inside], y[inside]))
    rng.shuffle(xy); points = np.asarray(xy); x, y = points.T
    distance = shapely.distance(shapely.points(x, y), source['pilot'].boundary)
    in_soil = shapely.contains_xy(source['soil'], x, y)
    soil_distance = shapely.distance(shapely.points(x, y), source['soil'].boundary)
    width = contact_width(x, y)
    contact = 1.-smooth(soil_distance/width)
    field = .7*noise(x, y, 110., 33)+.3*noise(x, y, 37., 117)
    islands = .10+.90*smooth((field-.25)/.48)
    density = (np.where(in_soil, .12+.55*islands, .15+.70*contact)) * pilot_weight(x, y, source)
    accepted = rng.random(len(x)) < density
    rows, occupied = [], defaultdict(list); rejected = Counter()
    for index in np.flatnonzero(accepted):
        a, b, d = float(x[index]), float(y[index]), float(distance[index])
        v = int(rng.integers(6)); scale = round(float(rng.uniform(.96, 1.045)), 6); radius = radii[v]*scale
        if heights[v]*scale > 8. or d <= radius+.1: rejected['full-pilot-crown'] += 1; continue
        if not in_soil[index] and soil_distance[index]+radius+.1 > width[index]: rejected['variable-contact-band'] += 1; continue
        cell = math.floor(a/2.45), math.floor(b/2.45)
        if any((a-p[0])**2+(b-p[1])**2 < 1.65**2 for dx in (-1, 0, 1) for dy in (-1, 0, 1)
               for p in occupied.get((cell[0]+dx, cell[1]+dy), [])):
            rejected['minimum-root-spacing'] += 1; continue
        point = Point(a, b)
        hits = [source['groundRows'][int(i)] for i in source['groundIndex'].query(point, predicate='intersects')]
        if not hits: rejected['missing-source-ground'] += 1; continue
        z = max(float(diag.barycentric([a, b], r['xyz']) @ np.asarray(r['xyz'])[:, 2]) for r in hits)
        row = {'id': f'meadow_infill_{len(rows)}', 'meshId': f'parcel_low_meadow_{v}', 'role': 'grass',
            'positionCm': [a, b, z], 'yawDeg': round(float(rng.uniform(0, 360)), 6), 'scale': [scale]*3,
            'sourceGroundMeshId': hits[0]['meshId'], 'sourceGroundZCm': z, 'radiusCm': radius,
            'actualHeightCm': heights[v]*scale, 'originalSoilInterior': bool(in_soil[index]),
            'wholeCrownClearanceCm': d-radius, 'contactWidthCm': float(width[index]),
            'authoredDensityField': float(field[index]), 'cameraPilotFade': float(pilot_weight(np.array(a), np.array(b), source))}
        rows.append(row); occupied[cell].append((a, b))
        if len(rows) >= TARGET_ROOTS: break
    require(1000 < len(rows) <= MAX_ROOTS and len(rows)*48 < MAX_NEAR_TRIANGLES, 'New infill budget differs')
    groups = {}
    for r in rows:
        v = r['meshId'].split('_')[-1]; cell = math.floor(r['positionCm'][0]/400), math.floor(r['positionCm'][1]/400)
        identity = f'EX_meadow_infill_{cell[0]}_{cell[1]}_{v}'
        g = groups.setdefault(identity, {'id': identity, 'meshId': r['meshId'], 'role': 'grass', 'qualityDetail': True,
            'cullEndCm': 4000, 'castShadow': True, 'instances': []})
        g['instances'].append({k: r[k] for k in ('positionCm', 'yawDeg', 'scale')})
    return rows, list(groups.values()), dict(rejected)


def transform(record, row):
    p = np.asarray(record['positionsCm'])*np.asarray(row['scale']); n = np.asarray(record['normals']).copy()
    a = math.radians(row['yawDeg']); c, s = math.cos(a), math.sin(a); rot = np.array([[c, -s], [s, c]])
    p[:, :2] = p[:, :2]@rot.T+row['positionCm'][:2]; p[:, 2] += row['positionCm'][2]
    n[:, :2] = n[:, :2]@rot.T
    return p, n


def sample(texture, uv, repeat=False):
    uv = np.asarray(uv); p = (uv % 1. if repeat else np.clip(uv, 0, 1))*np.array([texture.shape[1], texture.shape[0]])-.5
    lo = np.floor(p).astype('int64'); f = p-lo; hi = lo+1
    if repeat:
        lo %= [texture.shape[1], texture.shape[0]]; hi %= [texture.shape[1], texture.shape[0]]
    else:
        lo = np.clip(lo, [0, 0], [texture.shape[1]-1, texture.shape[0]-1]); hi = np.clip(hi, [0, 0], [texture.shape[1]-1, texture.shape[0]-1])
    a, b, c, d = texture[lo[..., 1], lo[..., 0]], texture[lo[..., 1], hi[..., 0]], texture[hi[..., 1], lo[..., 0]], texture[hi[..., 1], hi[..., 0]]
    fx, fy = f[..., 0], f[..., 1]
    if texture.ndim == 3: fx, fy = fx[..., None], fy[..., None]
    return (a*(1-fx)+b*fx)*(1-fy)+(c*(1-fx)+d*fx)*fy


def load_texture(path, alpha=False):
    image = Image.open(path)
    if alpha:
        a = np.asarray(image, dtype=float); return a/(65535. if a.max() > 255 else 255.)
    a = np.asarray(image.convert('RGB'), dtype=float)/255.
    return np.where(a <= .04045, a/12.92, ((a+.055)/1.055)**2.4)


def raster_leaf_window(decoded, rows, center, alpha, source):
    size, res = 100., 4000; low = np.asarray(center)-50.; lookup = {r['nodeName']: r for r in decoded}
    near = [r for r in rows if max(abs(np.asarray(r['positionCm'][:2])-center)) < 50+r['radiusCm']]
    results, masks = [], []
    xs = low[0]+(np.arange(res)+.5)*.025; ys = low[1]+(np.arange(res)+.5)*.025
    # Exact source hole mask is the denominator for the in-hole measurement.
    soil_mask = shapely.contains_xy(source['soil'], xs[None, :], ys[:, None])
    pilot_mask = shapely.contains_xy(source['pilot'], xs[None, :], ys[:, None])
    for lod in range(3):
        mask = np.zeros((res, res), dtype=bool)
        for row in near:
            r = lookup[row['meshId']+'_LOD'+str(lod)]; p, _ = transform(r, row); uv = np.asarray(r['uv0'])
            xy = (p[:, :2]-low)/.025
            for face in r['triangles']:
                q = xy[face]; lo = np.maximum(np.floor(q.min(0)).astype(int), 0); hi = np.minimum(np.ceil(q.max(0)).astype(int), res-1)
                if np.any(hi < lo): continue
                xx, yy = np.meshgrid(np.arange(lo[0], hi[0]+1)+.5, np.arange(lo[1], hi[1]+1)+.5)
                den = np.cross(q[1]-q[0], q[2]-q[0])
                if abs(den) < 1e-12: continue
                b = ((xx-q[0, 0])*(q[2, 1]-q[0, 1])-(yy-q[0, 1])*(q[2, 0]-q[0, 0]))/den
                c = ((q[1, 0]-q[0, 0])*(yy-q[0, 1])-(q[1, 1]-q[0, 1])*(xx-q[0, 0]))/den
                w = np.stack([1-b-c, b, c], axis=-1); inside = w.min(-1) >= -1e-9
                if not inside.any(): continue
                opaque = sample(alpha, w@uv[face]) >= .333
                mask[lo[1]:hi[1]+1, lo[0]:hi[0]+1] |= inside & opaque
        bins = mask.reshape(10, 400, 10, 400).mean((1, 3))
        eligible = soil_mask & pilot_mask
        results.append({'lod': lod, 'projectedOpaqueCoverFraction': float(mask.mean()),
            'originalHoleOpaqueCoverFraction': float(mask[eligible].mean()) if eligible.any() else None,
            'originalHoleWindowAreaM2': float(eligible.mean()), 'tenCmBinP10': float(np.quantile(bins, .1)),
            'tenCmBinsBelow20Percent': int((bins < .20).sum()), 'uncoveredFraction': 1.-float(mask.mean())})
        masks.append(mask)
    return {'centerCm': list(center), 'sizeCm': size, 'pixelSizeMm': .25, 'resolution': res,
            'instancesIntersectingWindow': len(near), 'lods': results}, masks


def choose_windows(source, rows):
    result = []
    for scene, pilot in source['pilots'].items():
        eye = np.asarray(pilot['view']['eyeCm'][:2]); direction = np.array([math.cos(pilot['angle']), math.sin(pilot['angle'])])
        choices = []
        region = source['soil'].intersection(pilot['geometry'])
        for poly in shapely.get_parts(region):
            if poly.area < 2500: continue
            p = shapely.maximum_inscribed_circle(poly, tolerance=2.).coords[0]
            xy = np.asarray(p); delta = xy-eye; distance = np.linalg.norm(delta)
            if 180 < distance < 1050:
                choices.append((abs(distance-650)-min(poly.area/500., 80.), xy))
        choices.sort(key=lambda r: r[0])
        require(choices, 'No actual near soil ROI')
        inside = choices[0][1]
        boundary = nearest_points(Point(inside), source['soil'].boundary)[1]
        edge = np.asarray(boundary.coords[0])
        result += [{'id': scene+'-hole', 'centerCm': inside.tolist()}, {'id': scene+'-contact', 'centerCm': edge.tolist()}]
    return result


def camera_frame(view, width, height):
    eye = np.asarray(view['eyeCm']); forward = np.asarray(view['targetCm'])-eye; forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0., 0., 1.]); right /= np.linalg.norm(right); up = np.cross(right, forward)
    focal = width/(2*math.tan(math.radians(view['horizontalFovDegrees']/2.)))
    return eye, forward, right, up, focal


def render_scene(source, decoded, rows, view, recipe, soil_recipe, ground_recipe, soil_meshes, old_scene, added=True, width=960, height=540, base_state=None):
    """CPU perspective-correct triangles/alpha. Source cameras, no native light claim."""
    if base_state is None:
        image = np.empty((height, width, 3)); image[:] = [.16, .19, .21]; depth = np.full((height, width), np.inf)
    else: image, depth = (a.copy() for a in base_state)
    eye, forward, right, up, focal = camera_frame(view, width, height)
    light = np.array([-.4, -.65, 1.]); light /= np.linalg.norm(light)
    albedo = load_texture(recipe['maps']['albedo']['path']); alpha = load_texture(recipe['maps']['alpha']['path'], True)
    soil = load_texture(soil_recipe['maps']['albedo']['path']); base = load_texture(ground_recipe['maps']['albedo']['path'])
    cover = load_texture(ground_recipe['groundCover']['maps']['albedo']['path'])
    def raster(p, n, uv, faces, kind, extra=None):
        camera = np.column_stack([(p-eye)@right, (p-eye)@up, (p-eye)@forward])
        packed = np.column_stack([camera, p, n, uv])
        if extra is not None: packed = np.column_stack([packed, extra])
        if kind in ('photo', 'native-blade'):
            q = np.column_stack([width/2+camera[:, 0]/np.maximum(camera[:, 2], .00001)*focal,
                                 height/2-camera[:, 1]/np.maximum(camera[:, 2], .00001)*focal])
            f = q[faces]; lo = np.ceil(f.min(1)-.5); hi = np.floor(f.max(1)-.5)
            possible = (hi >= lo).all(1) & (hi[:, 0] >= 0) & (hi[:, 1] >= 0) & (lo[:, 0] < width) & (lo[:, 1] < height)
            possible &= (camera[faces, 2].max(1) > 10) & (camera[faces, 2].min(1) < 2300)
            faces = faces[possible]
        for ids in faces:
            # Clip the actual ground triangles to the near/far camera planes,
            # retaining attributes. Leaf triangles are already local and small.
            data = packed[ids]
            clipping = () if data[:, 2].min() >= 10. and data[:, 2].max() <= 2300. else ((10., 1.), (2300., -1.))
            for bound, sign in clipping:
                out = []
                for i in range(len(data)):
                    a, b = data[i-1], data[i]; da, db = (a[2]-bound)*sign, (b[2]-bound)*sign
                    if (da >= 0) != (db >= 0): out.append(a+(b-a)*(da/(da-db)))
                    if db >= 0: out.append(b)
                data = np.asarray(out)
                if len(data) < 3: break
            if len(data) < 3: continue
            for j in range(1, len(data)-1):
                d = data[[0, j, j+1]]; z = d[:, 2]
                q = np.column_stack([width/2+d[:, 0]/z*focal, height/2-d[:, 1]/z*focal])
                lo = np.maximum(np.ceil(q.min(0)-.5).astype(int), [0, 0]); hi = np.minimum(np.floor(q.max(0)-.5).astype(int), [width-1, height-1])
                if np.any(hi < lo): continue
                xx, yy = np.meshgrid(np.arange(lo[0], hi[0]+1)+.5, np.arange(lo[1], hi[1]+1)+.5)
                den = np.cross(q[1]-q[0], q[2]-q[0])
                if abs(den) < 1e-12: continue
                b = ((xx-q[0, 0])*(q[2, 1]-q[0, 1])-(yy-q[0, 1])*(q[2, 0]-q[0, 0]))/den
                c = ((q[1, 0]-q[0, 0])*(yy-q[0, 1])-(q[1, 1]-q[0, 1])*(xx-q[0, 0]))/den
                w = np.stack([1-b-c, b, c], axis=-1); invz = w@(1/z); zp = 1./np.maximum(invz, 1e-12)
                region = depth[lo[1]:hi[1]+1, lo[0]:hi[0]+1]; inside = (w.min(-1) >= -1e-8) & (zp < region)
                if not inside.any(): continue
                attr = (w@(d[:, 3:]/z[:, None]))/np.maximum(invz[..., None], 1e-12)
                normal = attr[..., 3:6]; normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-12)
                if kind == 'photo':
                    u = attr[..., 6:8]; inside &= sample(alpha, u) >= .333
                    rgb = sample(albedo, u)*recipe['albedoScale']
                elif kind == 'native-blade':
                    # Original authored turf vertex response only; original
                    # native shader/SSS/shadow cannot be reproduced offline.
                    rgb = attr[..., 8:11]*np.array([.055, .12, .025])
                else:
                    xy = attr[..., :2]
                    rgb = sample(base, xy/ground_recipe['tileCm'], True)*np.asarray(ground_recipe['tint'])*ground_recipe['albedoScale']
                    grass = sample(cover, xy/ground_recipe['groundCover']['tileCm'], True)
                    amount = .40+.28*noise(xy[..., 0], xy[..., 1], 230., 71)
                    rgb = rgb*(1-amount[..., None])+grass*amount[..., None]
                    if kind == 'soil':
                        soil_rgb = sample(soil, xy/soil_recipe['tileCm'], True)*np.asarray(soil_recipe['tint'])*soil_recipe['albedoScale']
                        opacity = smooth(attr[..., 6])
                        rgb = soil_rgb*opacity[..., None]+rgb*(1-opacity[..., None])
                brightness = .38+1.15*np.abs(normal@light); rgb = np.clip(rgb*brightness[..., None], 0., 1.)
                if inside.any():
                    image[lo[1]:hi[1]+1, lo[0]:hi[0]+1][inside] = rgb[inside]; region[inside] = zp[inside]
    if base_state is None:
        for meshrow in source['meshes']:
            p = np.asarray(meshrow['verticesCm']); raster(p, np.tile([0., 0., 1.], (len(p), 1)), np.zeros((len(p), 2)), np.asarray(meshrow['indices']).reshape(-1, 3), 'ground')
        for m in soil_meshes:
            p = np.asarray(m['verticesCm']); raster(p, np.tile([0., 0., 1.], (len(p), 1)), np.asarray(m['uvs']), np.asarray(m['indices']).reshape(-1, 3), 'soil')
    lookup = {r['nodeName']: r for r in decoded}
    if base_state is None:
        for r, row, kind in old_scene:
            p, n = transform(r, row); raster(p, n, np.asarray(r['uv0']), r['triangles'], kind, r.get('colors')[:, :3] if kind == 'native-blade' else None)
    if added:
        for row in rows:
            delta = np.asarray(row['positionCm'])-eye
            if delta@forward < 0 or delta@forward > 1300 or abs(delta@right) > (delta@forward)*math.tan(math.radians(view['horizontalFovDegrees']/2.))+.2: continue
            r = lookup[row['meshId']+'_LOD0']; p, n = transform(r, row); raster(p, n, r['uv0'], r['triangles'], 'photo')
    srgb = np.where(image <= .0031308, image*12.92, 1.055*image**(1/2.4)-.055)
    return Image.fromarray(np.clip(srgb*255, 0, 255).astype('uint8')), (image, depth)


def original_preview_scene(source):
    library = {m['id']: m for m in read(LIBRARY)['meshes']}; cache = {}; old = []
    eyes = [np.asarray(p['view']['eyeCm'][:2]) for p in source['pilots'].values()]
    def near(row): return any(np.linalg.norm(np.asarray(row['positionCm'][:2])-eye) < 1500 for eye in eyes)
    for row in source['transition']['transitionPlacements']:
        if not near(row): continue
        m = library[row['meshId']]; path = Path(m['glbPath'])
        if path not in cache: cache[path] = {r['nodeName']: r for r in decode_glb(path)[1]}
        old.append((cache[path][m['lods'][0]['nodeName']], row, 'photo'))
    before = read(OLD_BLADE); lookup = {r['id']: r for r in before}; rng = random.Random(260920263)
    remove = source['neighborhood']['groundDetailRemovedPlacementIndices']; source_context = source['context']
    for category in ('meadowBladePlacements', 'meadowUnderstoryPlacements', 'yardBladePlacements'):
        omitted = set(remove.get(category, []))
        for index, row in enumerate(source_context.get(category, [])):
            if index in omitted: continue
            variant = rng.randrange(4)
            if not near(row): continue
            r = lookup[f'LawnTuft{variant}_LOD0']; allp = np.concatenate([np.asarray(q['verticesMm'])/10 for q in before if q['variant'] == variant])
            radius = np.linalg.norm(allp[:, :2], axis=1).max(); h = allp[:, 2].max()
            actual = {'positionsCm': np.asarray(r['verticesMm'])/10, 'normals': np.asarray(r['normals']),
                      'uv0': np.asarray(r['uv0']), 'triangles': np.asarray(r['faces']),
                      'colors': np.column_stack([np.tile([.82, .90, .75], (len(r['verticesMm']), 1)), np.ones(len(r['verticesMm']))])}
            native_row = {'positionCm': row['positionCm'], 'yawDeg': row['yawDeg'], 'scale': [row['radiusCm']/radius]*2+[row['heightCm']/h]}
            old.append((actual, native_row, 'native-blade'))
    return old


def source_measurement(source, records, decoded, rows, groups, rejected):
    lookup = {r['nodeName']: r for r in decoded}; xy = np.asarray([r['positionCm'][:2] for r in rows]); radii = np.asarray([r['radiusCm'] for r in rows])
    distance = shapely.distance(shapely.points(xy), source['allowed'].boundary)
    require(shapely.contains_xy(source['allowed'], xy[:, 0], xy[:, 1]).all() and (distance > radii+.1).all(), 'Actual full crown crossed source exclusion')
    minimum = float((distance-radii).min()); max_zerror = max(abs(r['positionCm'][2]-r['sourceGroundZCm']) for r in rows)
    areas = {}
    for r in decoded:
        q = r['positionsCm'][r['triangles'], :2]
        areas[r['nodeName']] = float(np.abs(np.cross(q[:, 1]-q[:, 0], q[:, 2]-q[:, 0])).sum()*.5)/10000
    area = [sum(areas[row['meshId']+'_LOD'+str(lod)]*row['scale'][0]**2 for row in rows) for lod in range(3)]
    budgets = [sum(len(g['instances'])*len(lookup[g['meshId']+'_LOD'+str(lod)]['triangles']) for g in groups) for lod in range(3)]
    require(budgets[0] < MAX_NEAR_TRIANGLES, 'New near triangles exceed2M')
    return {'status': 'MEASURED_SOURCE_LOW_MEADOW_PILOT_NOT_NATIVE_ACCEPTED', 'authorship': 'Artist ecology; no surveyed species/density/use claim',
        'allowed65GroundDomainM2': source['allowed'].area/10000, 'allSoilFootprintsM2': source['soil'].area/10000,
        'soilWithinAllowed65DomainM2': source['soil'].intersection(source['allowed']).area/10000,
        'pilotDomainM2': source['pilot'].area/10000, 'pilotSoilInteriorM2': source['pilot'].intersection(source['soil']).area/10000,
        'pilotOutsideContactM2': source['pilot'].difference(source['soil']).area/10000,
        'newInstances': len(rows), 'newGroups': len(groups), 'newMasters': 6, 'newLodNodes': 18,
        'newTriangleBudgetByLod': budgets, 'grossProjectedTriangleAreaM2ByLodBeforeOverlapOrAlpha': area,
        'fullCrownRadiusRangeCm': [min(r['radiusCm'] for r in rows), max(r['radiusCm'] for r in rows)],
        'actualPlantHeightRangeCm': [min(r['actualHeightCm'] for r in rows), max(r['actualHeightCm'] for r in rows)],
        'minimumFullCrownSourceClearanceCm': minimum, 'maximumRootToActualSourceGroundErrorCm': max_zerror,
        'insideSoilInstances': sum(r['originalSoilInterior'] for r in rows), 'outsideContactInstances': sum(not r['originalSoilInterior'] for r in rows),
        'pilotByCamera': {k: {'domainM2': p['geometry'].area/10000, 'insideSoilM2': p['geometry'].intersection(source['soil']).area/10000,
                             'cameraEyeCm': p['view']['eyeCm'], 'targetCm': p['view']['targetCm'], 'horizontalFovDegrees': p['view']['horizontalFovDegrees']}
                         for k, p in source['pilots'].items()}, 'candidateRejections': rejected,
        'limits': ['2M is additional source near-triangle cost, not total scene/native performance.',
                   'Only two softly faded12m camera pilots; no claim of all65 parcel coverage.',
                   'Gross triangle area is not opaque cover; savedGLB/alpha windows are measured separately.',
                   'Source ground elevations are inherited visualization data, not surveyed ground.'],
        'nativeVisualAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False}


def source_previews(source, decoded, rows, recipe, soil_recipe, ground_recipe, output):
    old_scene = original_preview_scene(source)
    inputs = {Path(m['glbPath']) for m in read(LIBRARY)['meshes'] if m['id'] in ('grass_medium_02_a', 'grass_medium_02_b', 'grass_medium_02_c')}
    for scene, pilot in source['pilots'].items():
        print('CPU source camera '+scene, flush=True)
        eye, forward, right, _, _ = camera_frame(pilot['view'], 960, 540)
        half = math.tan(math.radians(pilot['view']['horizontalFovDegrees']/2.))
        local_old = []
        for entry in old_scene:
            delta = np.asarray(entry[1]['positionCm'])-eye
            if 0. < delta@forward < 1500. and abs(delta@right) < delta@forward*half+20.:
                local_old.append(entry)
        near_soil = [m for m in source['neighborhood']['meshes'] if m['material'] == 'context_soil_exposure']
        plate = Image.new('RGB', (1920, 610), '#e9e6de'); draw = ImageDraw.Draw(plate)
        before, state = render_scene(source, decoded, rows, pilot['view'], recipe, soil_recipe, ground_recipe, near_soil, local_old, False)
        plate.paste(before, (0, 42))
        draw.text((10, 13), 'Original source floor/tall grass - '+scene, fill='#202820')
        after, _ = render_scene(source, decoded, rows, pilot['view'], recipe, soil_recipe, ground_recipe, near_soil, local_old, True, base_state=state)
        plate.paste(after, (960, 42))
        draw.text((970, 13), 'Added narrow low meadow pilot - '+scene, fill='#202820')
        draw.text((10, 590), 'CPU actual triangles/photo alpha; same original camera/FOV. Approximate PBR/light; native shadows/SSS/ortho/canopy omitted. No native acceptance.', fill='#202820')
        plate.save(output/(scene+'-source-comparison.png'))
        print('Preview ready '+str(output/(scene+'-source-comparison.png')), flush=True)
    return {str(p): sha(p) for p in inputs}


def build(output=OUTPUT):
    output = Path(output).resolve(); require(output == OUTPUT and not output.exists(), 'Use a fresh immutable study output')
    source = source_domain(); recipe = read(MATERIALS)[MATERIAL]
    strip = np.asarray(read(UV_BODY)['leafUvMapping']['stripStations']); require(strip.shape == (257, 3), 'Original photo strip differs')
    files = [Path(__file__), Path(diag.__file__), TRANSITION, CONTEXT, NEIGHBORHOOD, BUILDINGS, FOOTPRINTS, LIBRARY, MATERIALS, UV_BODY, CAMERAS, REPORT, OLD_BLADE]
    files += [Path(v['path']) for v in recipe['maps'].values()]
    report = read(REPORT); ground_recipe = report['materials']['materials']['context_meadow']['recipe']; soil_recipe = report['materials']['materials']['context_soil_exposure']['recipe']
    files += [Path(ground_recipe['maps']['albedo']['path']), Path(ground_recipe['groundCover']['maps']['albedo']['path']), Path(soil_recipe['maps']['albedo']['path'])]
    inputs = {str(p.resolve()): sha(p) for p in files}
    output.mkdir(parents=True)
    records = [mesh(v, l, strip) for v in range(6) for l in range(3)]
    write_glb(output/'low-meadow.glb', records); _, decoded = decode_glb(output/'low-meadow.glb')
    rows, groups, rejected = placements(source, decoded)
    measurement = source_measurement(source, records, decoded, rows, groups, rejected)
    write(output/'meadow-prototypes.json', records)
    masters = []
    lookup = {r['nodeName']: r for r in decoded}
    for variant in range(6):
        mid = f'parcel_low_meadow_{variant}'; lods = []
        for level in range(3):
            r = lookup[mid+'_LOD'+str(level)]; p = r['positionsCm']
            lods.append({'level': level, 'nodeName': r['nodeName'], 'vertices': len(p), 'triangles': len(r['triangles']),
                         'expectedBoundsCm': {'min': p.min(0).tolist(), 'max': p.max(0).tolist()}, 'radialEnvelopeCm': float(np.linalg.norm(p[:, :2], axis=1).max())})
        masters.append({'id': mid, 'role': 'grass', 'placementPolicy': 'explicit-only', 'materialKeys': [MATERIAL],
            'heightCm': max(l['expectedBoundsCm']['max'][2] for l in lods), 'lods': lods,
            'glbPath': str(output/'low-meadow.glb'), 'glbSha256': sha(output/'low-meadow.glb')})
    library = {'schemaVersion': 1, 'owner': OWNER, 'generatorSha256': sha(__file__), 'inputFiles': inputs,
               'axes': 'glTF Y-up; Unreal native=[100*x,100*z,100*y]', 'meshes': masters,
               'status': measurement['status'], 'nativeAccepted': False}
    write(output/'geometry-manifest.json', library); write(output/'material-manifest.json', {MATERIAL: recipe})
    write(output/'source-measurement.json', measurement)
    print('ActualGLB/layout ready: '+str(output/'low-meadow.glb')+' '+json.dumps({k: measurement[k] for k in ('pilotDomainM2', 'newInstances', 'newGroups', 'newTriangleBudgetByLod')}), flush=True)
    preview_inputs = source_previews(source, decoded, rows, recipe, soil_recipe, ground_recipe, output)
    alpha = load_texture(recipe['maps']['alpha']['path'], True); windows = choose_windows(source, rows); coverage = []
    for w in windows:
        print('Raster '+w['id'], flush=True)
        result, masks = raster_leaf_window(decoded, rows, w['centerCm'], alpha, source); result['id'] = w['id']; coverage.append(result)
        Image.fromarray(masks[0].astype('uint8')*255).resize((1000, 1000)).save(output/(w['id']+'-coverage.png'))
    write(output/'coverage-measurement.json', {'method': 'Actual savedGLB leaf triangles at0.25mm, original16bit PHalpha mip0 bilinear cutoff.333; newinfill only.',
        'windows': coverage, 'uniformFullGroundCoverClaim': False, 'nativeAppearanceAccepted': False})
    plan = {'schemaVersion': 1, 'kind': 'authored-low-meadow-infill-pilot', 'owner': OWNER, 'generatorSha256': sha(__file__),
        'activeDesign': source['context']['activeDesign'], 'housePlacement': source['context']['housePlacement'],
        'sourceSceneSha256': source['context']['sourceSceneSha256'], 'sourceObjSha256': source['context']['sourceObjSha256'],
        'inputFiles': inputs, 'sourceContext': pin(CONTEXT), 'sourceNeighborhood': pin(NEIGHBORHOOD), 'sourceTransition': pin(TRANSITION),
        'sourceBuildingPlan': pin(BUILDINGS), 'sourceSoilFootprints': pin(FOOTPRINTS), 'sourceCameras': pin(CAMERAS),
        'geometryManifest': pin(output/'geometry-manifest.json'), 'materialManifest': pin(output/'material-manifest.json'),
        'coverageMeasurement': pin(output/'coverage-measurement.json'), 'allowedDomainCm': mapping(source['allowed']), 'pilotDomainCm': mapping(source['pilot']),
        'infillPlacements': rows, 'groups': groups, 'audit': measurement,
        'preservation': {'original65GroundMeshesUnchanged': True, 'sourceGroundCollisionUnchanged': True,
            'old573SoilOverlaysUnchanged': True, 'originalTransitionPlacements7000Unchanged': True,
            'originalTransitionPlacementsSha256': digest(source['transition']['transitionPlacements']),
            'originalTransitionGroupsSha256': digest(source['transition']['groups']),
            'originalRemovalIndicesSha256': digest(source['neighborhood']['groundDetailRemovedPlacementIndices']),
            'originalRemovedPlacements': sum(map(len, source['neighborhood']['groundDetailRemovedPlacementIndices'].values())),
            'originalRootsNeverRestoredOrMoved': True, 'NoCollision': True},
        'policy': {'privateBufferCm': 30., 'roadBufferCm': 20., 'buildingBufferCm': 150., 'allLodCrownMarginCm': .1,
            'sourceGroundRootPlacement': 'Exact existing rendered source triangle barycentric Z; no raising original ground/soil.',
            'leafCountEveryLod': 12, 'nearTrianglesPerMaster': 48, 'foldedLeafCountByLod': [4, 2, 0],
            'heightCm': [2., 8.], 'widthMm': [2.2, 3.5], 'contactBandWidthCm': [50., 100.],
            'pilotDistanceFadeCm': [1000., 1200.], 'pilotAngularFadeRad': .12, 'cullEndCm': 4000,
            'qualityDetail': True, 'geometryCollision': 'NoCollision'},
        'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'integrationAuthorized': False}
    write(output/'meadow-infill-plan.json', plan)
    write(output/'asset-manifest.json', {'schemaVersion': 1, 'owner': OWNER, 'generatorSha256': sha(__file__), 'inputFiles': inputs,
        'geometry': pin(output/'geometry-manifest.json'), 'materials': pin(output/'material-manifest.json'), 'plan': pin(output/'meadow-infill-plan.json'),
        'nativeAccepted': False})
    for path, expected in inputs.items(): require(sha(path) == expected, 'Original source changed during study: '+path)
    write(output/'study-measurement.json', {'owner': OWNER, 'generatorSha256': sha(__file__), 'inputsUnchangedBeforeAfter': True,
        'inputFiles': inputs, 'previewInputs': preview_inputs, 'measurement': measurement, 'coverage': coverage,
        'preview': [pin(output/(scene+'-source-comparison.png')) for scene in SCENES],
        'nativeJobsRun': 0, 'nativeAccepted': False, 'performanceAccepted': False})
    return {'output': str(output), 'plan': pin(output/'meadow-infill-plan.json'), 'geometry': pin(output/'geometry-manifest.json'),
            'measurement': measurement, 'coverage': coverage, 'preview': [str(output/(s+'-source-comparison.png')) for s in SCENES]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, default=OUTPUT)
    print(json.dumps(build(**vars(parser.parse_args())), separators=(',', ':')))
