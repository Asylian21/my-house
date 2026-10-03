"""One source-only mapped garden boundary trial; no Unreal or native writer.

Mapped rings are geographic source evidence. New fences, internal separation,
gates and path use are an artistic proposal, not ownership or surveyed works.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import LineString, MultiPoint, Point, Polygon, box, mapping, shape
from shapely.ops import triangulate, unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-parcel-boundary-study-r43.py'
OUTPUT = ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-source-study'
SCHEMA = 'brezi-mapped-garden-open-boundary-source-trial-r43'
SELECTION = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-image-base-selection-r1/root-image-base-selection-r1.json'
SELECTION_SHA = '211bacaa3573b94542ca97f6820a070dfa50f45db4f0ab4ec3731bece8af076d'
CLONE = ROOT/'output/unreal/exterior-20261002-r43a/garden-boundary-project-clone-r43.json'
CLONE_SHA = 'a400b1ba098322006cbc8d3e398432a06c40b73a20b51c365da31610491fed98'
PATHS = {
    'context': 'output/unreal/exterior-context-20260927-r8/context-plan.json',
    'terrain': 'output/unreal/exterior-terrain-20260926-r4/terrain-plan.json',
    'buildings': 'output/unreal/exterior-buildings-20260926-r2/building-plan.json',
    'yards': 'output/unreal/exterior-context-yard-20261002-r28-study/yard-layout.json',
    'exclusions': 'output/unreal/exterior-context-yard-20261002-r28-study/source-exclusion-masks.json',
    'assetManifest': 'output/archviz/assets/manifest.json',
    'assetLock': 'scripts/archviz/assets.lock.json',
}
TARGETS = ('BU.572063', 'BU.3800911', 'BU.3852341')
PARCELS = ('4184/2', '4184/3', '4215/5')
EXPECTED = {
    'context': '4b0b72a5f39d5bec3915846abb159147a4cf73b65cbf920884ffe7dd762a4176',
    'terrain': '7106824dd0e489c1688cbe9569811a59314e8a56b6b5479000fa5d8f84fbdced',
    'yards': '3ba5829cef341736b76a5bfce33eb961e919e7d9374ab9aed842bb2e85061ada',
    'exclusions': 'cedd1bcc0a10ca3c2c0f91a4799c93f5430f1cbf7a4e0d1e8e121e574e816f62',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def checked(row):
    path = Path(row['path'])
    require(path.is_absolute() and path.is_file() and not path.is_symlink()
            and pin(path) == row, 'Frozen source bytes differ: '+str(path))
    return path


def write(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, separators=(',', ':'), allow_nan=False)
        f.write('\n')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def polygons(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == 'Polygon':
        return [geometry]
    if geometry.geom_type not in ('MultiPolygon', 'GeometryCollection'):
        return []
    return [p for g in geometry.geoms for p in polygons(g)]


def project_sjtsk(point):
    # Same C3 mm rounding/client placement/world axes as frozen exterior-context.py.
    dx, dy = point[0]+606705150, point[1]+1202056660
    x = math.floor(dx*.6632623694196262+dy*.7483869515911291+.5)-77.91340545401735
    y = math.floor(dx*-.7483869515911291+dy*.6632623694196262+.5)
    return [(x-15200)/10, -(y-10800)/10]


def parcel_polygon(row):
    return unary_union([Polygon([project_sjtsk(p) for p in rings[0]],
        [[project_sjtsk(p) for p in hole] for hole in rings[1:]]) for rings in row['polygonsSjtskMm']])


def validate_selection(selection):
    require(selection['schema'] == 'brezi-r39c-root-image-base-selection-r1'
            and selection['status'] == 'selected-saved-r39c-only-as-next-mapped-garden-open-boundary-r43-pilot-base'
            and selection['selectedNativeProcessId'] == 94572
            and selection['allFourOriginalPngsViewedByRoot'] is True
            and selection['localPropCueAcceptedForNextTrialOnly'] is True
            and selection['independentVisualPeerReceived'] is True
            and selection['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
            and selection['setbacksMm'] == {'street': 3000, 'east': 3000}
            and not any(selection[k] for k in ('fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified', 'activeOutputPromoted')),
            'Only actual image-selected R39c source base, no full acceptance')


def load_inputs():
    inputs = {key: pin(ROOT/path) for key, path in PATHS.items()}
    for key, expected in EXPECTED.items():
        require(inputs[key]['sha256'] == expected, 'Immutable R43 input differs: '+key)
    require(pin(SELECTION)['sha256'] == SELECTION_SHA, 'Actual root image selection differs')
    selection = read(SELECTION)
    validate_selection(selection)
    inputs['rootImageDecision'] = pin(SELECTION)
    for key in ('sourceNativeReport', 'sourceNativeProcess', 'sourceCurrentByteAudit', 'rootVisualReview'):
        checked(selection[key]); inputs[key] = selection[key]
    report, process, audit = (read(selection[k]['path']) for k in ('sourceNativeReport', 'sourceNativeProcess', 'sourceCurrentByteAudit'))
    raw_pin = pin(process['processFile']); raw = read(raw_pin['path'])
    require(raw_pin['sha256'] == process['processFileSha256'] and raw['pid'] == 94572
            and raw['code'] == 0 and raw['signal'] is None and process['sourcePinsUnchangedAfterNative'] is True,
            'Actual R39c root process envelope/raw native0 receipt required')
    inputs['rawNativeProcess'] = raw_pin
    require(report['nativeProcessId'] == 94572 and report['nativeApplied'] is True
            and report['savedMapUnloadedReloaded'] is True
            and audit['onlyOriginalMapChanged'] is True and audit['all1294FrozenSourcePinsExact'] is True,
            'Actual saved R39c/process0/current-byte boundary required')
    data = {key: read(row['path']) for key, row in inputs.items() if key in PATHS}
    require(data['context']['activeDesign'] == report['activeDesign']
            and report['setbacksMm'] == {'street': 3000, 'east': 3000}, 'C/B/B3000 changes forbidden')
    rows = [row for row in data['context']['parcels'] if row['parcelNumber'] in PARCELS]
    require(len(rows) == 3 and {r['featureId'] for r in rows} == {'CP.941088736', 'CP.941089736', 'CP.941103736'}, 'Three exact mapped garden/strip features required')
    data['parcelRows'] = rows
    data['parcels'] = {row['parcelNumber']: parcel_polygon(row) for row in rows}
    data['targetBuildings'] = [row for row in data['buildings']['buildings'] if row['id'] in TARGETS]
    data['feet'] = {row['id']: unary_union([Polygon(r[0], r[1:]) for r in row['polygonsCm']]) for row in data['targetBuildings']}
    require(len(data['feet']) == 3, 'Original three neighboring footprints required')
    data['hard'] = unary_union([shape(s['domainCm']) for s in data['yards']['surfaces'] if s['role'] in ('entry_walk', 'service_court')])
    data['beds'] = unary_union([shape(s['domainCm']) for s in data['yards']['surfaces'] if s['role'] == 'soil_bed'])
    data['exclusionShapes'] = {key: shape(value) for key, value in data['exclusions'].items()}
    data['cameras'] = [copy.deepcopy(row['sourceCamera']) for row in selection['actualCameraCaptures']]
    require({r['id'] for r in data['cameras']} == {'exterior-context-yard-572063-close-r18', 'exterior-neighborhood-ground-r38'}, 'Two exact closed camera rows required')
    data['selection'], data['inputFiles'] = selection, inputs
    return data


class Ground:
    """Clip whole ground faces under each proposed footprint, not a flat datum."""
    def __init__(self, meshes, domain):
        self.rows, shapes = [], []
        bounds = domain.bounds
        for mesh in meshes:
            if mesh['material'] not in ('context_fallow', 'context_meadow', 'context_crop', 'context_arable', 'context_track', 'context_distant_terrain'):
                continue
            vertices = np.asarray(mesh['verticesCm'], dtype=float)
            faces = vertices[np.asarray(mesh['indices']).reshape(-1, 3)]
            low, high = faces[:, :, :2].min(1), faces[:, :, :2].max(1)
            selected = (high[:, 0] >= bounds[0]) & (low[:, 0] <= bounds[2]) & (high[:, 1] >= bounds[1]) & (low[:, 1] <= bounds[3])
            for ordinal in np.flatnonzero(selected):
                face = faces[ordinal]; polygon = Polygon(face[:, :2])
                if polygon.area:
                    shapes.append(polygon)
                    self.rows.append((mesh['id'], int(ordinal), face))
        self.shapes, self.tree = shapes, STRtree(shapes)

    @staticmethod
    def plane(face, xy):
        a, b, c = face
        det = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        u = ((b[0]-xy[0])*(c[1]-xy[1])-(b[1]-xy[1])*(c[0]-xy[0]))/det
        v = ((c[0]-xy[0])*(a[1]-xy[1])-(c[1]-xy[1])*(a[0]-xy[0]))/det
        return float(u*a[2]+v*b[2]+(1-u-v)*c[2])

    def at(self, xy):
        point = Point(xy)
        rows = [(self.plane(self.rows[int(i)][2], xy), self.rows[int(i)][0], self.rows[int(i)][1])
                for i in self.tree.query(point) if self.shapes[int(i)].covers(point)]
        require(rows, 'Missing existing source ground under proposed point')
        z, name, triangle = max(rows)
        return {'zCm': z, 'meshId': name, 'triangleOrdinal': triangle}

    def footprint(self, footprint):
        clipped, source_faces, witnesses = [], [], []
        for i in self.tree.query(footprint):
            i = int(i); inter = self.shapes[i].intersection(footprint)
            for p in polygons(inter):
                clipped.append(p)
                source_faces.append(self.shapes[i])
                name, ordinal, face = self.rows[i]
                z = [self.plane(face, xy) for xy in p.exterior.coords]
                witnesses.append({'meshId': name, 'triangleOrdinal': ordinal, 'clippedAreaCm2': p.area,
                    'sourceZminCm': min(z), 'sourceZmaxCm': max(z)})
        # Certify containment against original shared source edges. Unioning
        # newly computed intersection vertices can introduce tiny GEOS slivers.
        require(clipped and unary_union(source_faces).covers(footprint), 'Whole proposed footprint lacks source ground support')
        # The highest point from every intersecting source face bounds all layers.
        return {'maximumExistingGroundZCm': max(r['sourceZmaxCm'] for r in witnesses),
            'wholeFootprintSourceFaceCoverage': True, 'intersectedSourceFaces': witnesses,
            'actualNativeContactVerified': False, 'surveyElevationVerified': False}


def shifted(a, b, west):
    a, b = np.asarray(a), np.asarray(b)
    unit = (b-a)/np.linalg.norm(b-a)
    normal = np.asarray([-unit[1], unit[0]])*(1 if west else -1)
    return a+25*normal+30*unit, b+25*normal-30*unit


def at_y(pair, y):
    a, b = pair
    return a+(b-a)*(y-a[1])/(b[1]-a[1])


def segment_layout(data):
    west = shifted([7577.008659454598, 26997.2], [8132.208659454598, 30982.8], True)
    east = shifted([7774.408659454598, 26966.6], [8334.808659454598, 30982.3], False)
    unit = (east[1]-east[0])/np.linalg.norm(east[1]-east[0])
    gate_a, gate_b = at_y(east, 30269), at_y(east, 30447)
    cross = data['parcels']['4184/2'].intersection(LineString([[5400, 28200], [8300, 28200]]))
    # Gate endpoints are inside faces of 8cm posts, so pedestrian clear width
    # remains exactly120cm. Eastern gate posts likewise sit beyond the opening.
    specs = [
        ('west-front', '4184/2', 'wood', west[0], at_y(west, 29460)),
        ('west-rear', '4184/2', 'wood', at_y(west, 30450), west[1]),
        ('east-south', '4184/3', 'metal', east[0], gate_a-4.05*unit),
        ('east-north', '4184/3', 'metal', gate_b+4.05*unit, east[1]),
        ('internal-west', '4184/2', 'wood', np.array([cross.bounds[0]+30, 28200]), np.array([6401.95, 28200])),
        ('internal-east', '4184/2', 'wood', np.array([6530.05, 28200]), np.array([cross.bounds[2]-30, 28200])),
    ]
    rows = [{'id': name, 'parcel': parcel, 'style': style, 'aCm': a.tolist(), 'bCm': b.tolist(),
        'heightCm': 90, 'maximumPostSpacingCm': 240, 'postWidthCm': 8,
        'railHeightsCm': [36, 77] if style == 'wood' else [24, 84],
        'railDepthHeightCm': [4, 7] if style == 'wood' else [3, 3],
        'mappedLegalFence': False, 'collisionProposed': False} for name, parcel, style, a, b in specs]
    gates = [
        {'id': 'east-entry-gate', 'parcel': '4184/3', 'style': 'metal',
         'hingesCm': [(gate_a-4.05*unit).tolist(), (gate_b+4.05*unit).tolist()],
         'leafDirections': [((np.array([unit[1], -unit[0]])-unit)/math.sqrt(2)).tolist(),
                            ((np.array([unit[1], -unit[0]])+unit)/math.sqrt(2)).tolist()],
         'leafWidthCm': float(np.linalg.norm(gate_b-gate_a)/2), 'openAngleDegrees': 135,
         'clearWidthCm': float(np.linalg.norm(gate_b-gate_a)), 'currentEntrySourceId': 'BU.3852341'},
        {'id': 'internal-entry-gate', 'parcel': '4184/2', 'style': 'wood',
         'hingesCm': [[6401.95, 28200]], 'leafDirections': [[0, 1]], 'leafWidthCm': 120,
         'openAngleDegrees': 90, 'clearWidthCm': 120, 'currentEntrySourceId': 'BU.3800911'},
    ]
    return rows, gates


def box_mesh(a, b, bottom, height, width, material, identity, parcel):
    a, b = np.asarray(a), np.asarray(b)
    direction = (b-a)/np.linalg.norm(b-a)
    side = np.array([-direction[1], direction[0]])
    half = np.array([np.linalg.norm(b-a)/2, width/2, height/2])
    bevel = .20 if material == 'wood' else .10
    require(min(half) > bevel, 'Bevel must leave positive real member thickness')
    # Truncated cuboid:6 broad faces,12 bevel strips,8 triangular corner caps.
    local = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                signs = np.array([sx, sy, sz])
                for axis in range(3):
                    p = signs*(half-bevel); p[axis] = signs[axis]*half[axis]; local.append(p)
    faces = []
    for axis in range(3):
        for sign in (-1, 1):
            n = np.zeros(3); n[axis] = sign
            faces.append((n, [p for p in local if p[axis] == sign*half[axis]]))
    for axes in ((0, 1), (0, 2), (1, 2)):
        for sa in (-1, 1):
            for sb in (-1, 1):
                n = np.zeros(3); n[axes[0]], n[axes[1]] = sa, sb
                selected = [p for p in local if ((p[axes[0]] == sa*half[axes[0]] and p[axes[1]] == sb*(half[axes[1]]-bevel))
                    or (p[axes[1]] == sb*half[axes[1]] and p[axes[0]] == sa*(half[axes[0]]-bevel)))]
                faces.append((n, selected))
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                n = np.array([sx, sy, sz], dtype=float)
                faces.append((n, [p for p in local if all(p[i]*n[i] > 0 for i in range(3))]))
    vertices, normals, uv, indices = [], [], [], []
    center = np.array([(a[0]+b[0])/2, (a[1]+b[1])/2, bottom+height/2])
    rotation = np.array([[direction[0], side[0], 0], [direction[1], side[1], 0], [0, 0, 1]])
    grain_axis = np.zeros(3); grain_axis[int(np.argmax(half))] = 1
    phase = int(hashlib.sha256(identity.encode()).hexdigest()[:8], 16)/2**32
    for normal, points in faces:
        normal /= np.linalg.norm(normal)
        u = grain_axis-normal*np.dot(grain_axis, normal)
        if np.linalg.norm(u) == 0:
            u = np.zeros(3); u[(int(np.argmax(half))+1)%3] = 1
        u /= np.linalg.norm(u); v = np.cross(normal, u)
        mean = np.mean(points, axis=0)
        points.sort(key=lambda p: math.atan2(np.dot(p-mean, v), np.dot(p-mean, u)))
        start = len(vertices)
        for p in points:
            vertices.append((rotation@p+center).tolist()); normals.append((rotation@normal).tolist())
            uv.append([float(np.dot(p, u)/150+phase), float(np.dot(p, v)/150+phase*.37)])
        for i in range(1, len(points)-1): indices.extend([start, start+i, start+i+1])
    return {'id': identity, 'material': material, 'parcel': parcel,
        'verticesCm': vertices, 'indices': indices, 'normals': normals, 'uv0': uv,
        'originalProviderGeometry': False, 'closedSolid': True, 'collision': False,
        'edgeBevelCm': bevel, 'sourceVertexPrecision': 'binary64 centimetres; future export/nativeF32 pending',
        'authoredMetricUvPolicy': 'own face UV0:long-member grain direction,150cm tile,stable per-member phase; original photos unchanged'}


def hinge_mesh(xy, z, parcel, identity):
    n, radius, h = 12, 2.5, 7
    vertices = [[xy[0]+radius*math.cos(2*math.pi*i/n), xy[1]+radius*math.sin(2*math.pi*i/n), zz]
                for zz in (z, z+h) for i in range(n)]
    vertices += [[*xy, z], [*xy, z+h]]
    indices = []
    for i in range(n):
        j = (i+1)%n
        indices += [i, j, j+n, i, j+n, i+n, 2*n, j, i, 2*n+1, i+n, j+n]
    split, normals, uv = [], [], []
    for face in np.asarray(indices).reshape(-1, 3):
        points = np.asarray(vertices)[face]
        n = np.cross(points[1]-points[0], points[2]-points[0]); n /= np.linalg.norm(n)
        for p in points:
            split.append(p.tolist()); normals.append(n.tolist()); uv.append([float(p[0]/150), float(p[2]/150)])
    return {'id': identity, 'material': 'metal', 'parcel': parcel, 'verticesCm': split,
        'indices': list(range(len(split))), 'normals': normals, 'uv0': uv,
        'originalProviderGeometry': False, 'closedSolid': True, 'collision': False}


def object_footprint(row):
    return MultiPoint(np.asarray(row['verticesCm'])[:, :2]).convex_hull


def signed_volume(row):
    vertices = np.asarray(row['verticesCm']); faces = vertices[np.asarray(row['indices']).reshape(-1, 3)]
    return float(np.einsum('ij,ij->i', faces[:, 0], np.cross(faces[:, 1], faces[:, 2])).sum()/6)


def validate_solids(objects, data, clear_path):
    feet = unary_union(list(data['feet'].values()))
    forbidden = unary_union([data['hard'], data['beds'], feet,
        data['exclusionShapes']['protected'], data['exclusionShapes']['subject'], data['exclusionShapes']['roads']])
    clearance = []
    for row in objects:
        require(row['closedSolid'] and signed_volume(row) > 0, 'Real positive-volume outward-wound solid required')
        footprint = object_footprint(row)
        require(data['parcels'][row['parcel']].covers(footprint), 'Proposed whole geometry leaves exact mapped garden')
        require(footprint.intersection(data['parcels']['4215/5']).area == 0, 'Mapped strip narrowed by new geometry')
        require(footprint.intersection(forbidden).area == 0, 'New solid crosses old building, court, bed, road or private area')
        require(footprint.intersection(clear_path).area == 0, 'Open gate/post obstructs pedestrian path')
        gap = min(footprint.distance(Point(r['positionCm'][:2]))-r['radialEnvelopeCm'] for r in data['yards']['planting'])
        require(gap > 0, 'New whole solid reaches existing whole shrub crown')
        clearance.append({'id': row['id'], 'buildingClearanceCm': footprint.distance(feet), 'shrubCrownClearanceCm': gap})
    return clearance


def build_geometry(data):
    segments, gates = segment_layout(data)
    ground = Ground(data['context']['meshes']+data['terrain']['meshes'], box(5600, 26900, 8500, 31100))
    objects, supports, openness = [], [], []
    for row in segments:
        a, b = np.asarray(row['aCm']), np.asarray(row['bCm'])
        length = float(np.linalg.norm(b-a)); direction = (b-a)/length
        count = math.ceil(length/row['maximumPostSpacingCm'])
        points = [a+(b-a)*i/count for i in range(count+1)]
        levels = []
        for ordinal, p in enumerate(points):
            post = box_mesh(p-4*direction, p+4*direction, 0, row['heightCm'], 8, row['style'], row['id']+':post:'+str(ordinal), row['parcel'])
            support = ground.footprint(object_footprint(post)); z = support['maximumExistingGroundZCm']
            for v in post['verticesCm']: v[2] += z
            objects.append(post); levels.append(z)
            supports.append({'objectId': post['id'], 'source': support})
        for ordinal, (start, end) in enumerate(zip(points, points[1:])):
            for rail, height in enumerate(row['railHeightsCm']):
                depth, rail_height = row['railDepthHeightCm']
                bottom = max(levels[ordinal:ordinal+2])+height-rail_height/2
                objects.append(box_mesh(start, end, bottom, rail_height, depth, row['style'], row['id']+f':rail:{ordinal}:{rail}', row['parcel']))
            if row['style'] == 'metal':
                for j in range(1, math.ceil(np.linalg.norm(end-start)/25)):
                    t = j/math.ceil(np.linalg.norm(end-start)/25); p = start+t*(end-start)
                    z = ground.at(p)['zCm']
                    objects.append(box_mesh(p-direction, p+direction, z+25.5, 57, 2, 'metal', row['id']+f':picket:{ordinal}:{j}', row['parcel']))
        occupied = 2*row['railDepthHeightCm'][1]/row['heightCm'] + 8*(count+1)/length
        if row['style'] == 'metal': occupied += 2/25
        require(1-occupied >= .70, 'Open boundary projected elevation must remain at least70percent open')
        openness.append({'segmentId': row['id'], 'conservativeFrontElevationOpenFraction': 1-occupied,
            'wholeCameraTransparencyOrVisibilityClaim': False})
        row['lengthCm'] = length
        row['sourcePostGroundZCm'] = levels
    for gate in gates:
        for ordinal, (hinge, d) in enumerate(zip(gate['hingesCm'], gate['leafDirections'])):
            hinge, d = np.asarray(hinge), np.asarray(d)
            end = hinge+d*gate['leafWidthCm']; ground_z = ground.at(hinge)['zCm']
            material = gate['style']; thickness = 3 if material == 'metal' else 4
            # An open, thick frame with two rails and narrow stiles; no opaque plane.
            for rail_z in (34, 76):
                objects.append(box_mesh(hinge, end, ground_z+rail_z, 6 if material == 'wood' else 3, thickness, material, gate['id']+f':leaf:{ordinal}:rail:{rail_z}', gate['parcel']))
            for stile, p in enumerate((hinge, end)):
                objects.append(box_mesh(p-2*d, p+2*d, ground_z+25, 57, thickness, material, gate['id']+f':leaf:{ordinal}:stile:{stile}', gate['parcel']))
            for hinge_z in (28, 70):
                objects.append(hinge_mesh(hinge.tolist(), ground_z+hinge_z, gate['parcel'], gate['id']+f':hinge:{ordinal}:{hinge_z}'))
    yard = next(y for y in data['yards']['yards'] if y['buildingSourceId'] == 'BU.3800911')
    e = yard['entrance']; terminal = [e['edgeOriginCm'][i]+325*e['tangent'][i]+650*e['outward'][i] for i in range(2)]
    path = LineString([[6466, 28200], terminal]).buffer(60, cap_style=2, join_style=2)
    require(data['parcels']['4184/2'].covers(path) and path.intersection(data['beds']).area == 0,
            'Connector must stay in mapped garden and avoid original beds')
    clear_path = unary_union([path, data['hard']])
    clearances = validate_solids(objects, data, clear_path)
    new_path = path.difference(data['hard'])
    footprint_witness = ground.footprint(new_path)
    floor_vertices, floor_indices = [], []
    for p in polygons(new_path):
        for triangle in triangulate(p):
            if not p.covers(triangle): continue
            xy = list(triangle.exterior.coords)[:-1]
            if Polygon(xy).exterior.is_ccw is False: xy.reverse()
            base = len(floor_vertices)
            floor_vertices.extend([[x, y, ground.at([x, y])['zCm']+.06] for x, y in xy])
            floor_indices.extend([base, base+1, base+2])
    require(floor_indices and unary_union([Polygon(np.asarray(floor_vertices)[face, :2]) for face in np.asarray(floor_indices).reshape(-1, 3)]).equals(new_path),
            'Whole connector must have a complete triangulation with no outside triangles')
    floor = {'id': 'internal-entry-connector', 'material': 'gravel', 'parcel': '4184/2',
        'verticesCm': floor_vertices, 'indices': floor_indices, 'closedSolid': False, 'collision': False,
        'sourceDomainCm': mapping(new_path), 'sourceAreaM2': new_path.area/10000,
        'widthCm': 120, 'sourceContactLiftCm': .06, 'sourceGround': footprint_witness,
        'nativeContactOrZFightVerified': False}
    floor['uv0'] = [[v[0]/200, v[1]/200] for v in floor_vertices]
    floor['normals'] = []
    for face in np.asarray(floor_indices).reshape(-1, 3):
        p = np.asarray(floor_vertices)[face]; n = np.cross(p[1]-p[0], p[2]-p[0]); n /= np.linalg.norm(n)
        floor['normals'].extend([n.tolist()]*3)
    merged = []
    for key in ('wood', 'metal', 'gravel'):
        mesh = {'id': 'r43_'+key, 'materialKey': key, 'verticesCm': [], 'normals': [], 'uv0': [], 'indices': [],
            'sourceObjectRanges': [], 'sectionCount': 1, 'collision': False,
            'attributesGeneratedForOwnGeometry': True, 'sourceVertexPrecision': 'binary64 centimetres; future GLB/nativeF32 pending'}
        for obj in objects+[floor]:
            if obj['material'] != key: continue
            start, face_start = len(mesh['verticesCm']), len(mesh['indices'])//3
            mesh['verticesCm'].extend(obj['verticesCm']); mesh['normals'].extend(obj['normals']); mesh['uv0'].extend(obj['uv0'])
            mesh['indices'].extend([start+i for i in obj['indices']])
            mesh['sourceObjectRanges'].append({'objectId': obj['id'], 'vertexStart': start, 'vertexCount': len(obj['verticesCm']),
                'triangleStart': face_start, 'triangleCount': len(obj['indices'])//3})
        require(mesh['verticesCm'] and len(mesh['normals']) == len(mesh['verticesCm']) == len(mesh['uv0']), 'Complete merged own P/N/UV0 record required')
        merged.append(mesh)
    geometry = {'schema': SCHEMA+'-authored-geometry', 'units': 'UE-world-centimetres-Z-up',
        'segments': segments, 'openGates': gates, 'objects': objects, 'connector': floor, 'meshes': merged,
        'sourceGroundFootprintProof': supports, 'sourceSolidClearances': clearances,
        'openness': openness, 'newSourceTriangles': sum(len(o['indices'])//3 for o in objects)+len(floor_indices)//3,
        'intendedNativeMeshCount': 3, 'intendedNativeStaticMeshActorCount': 3, 'intendedNewHismComponents': 0,
        'providerGeometryOrFenceAcquired': False, 'geometryExportedOrImported': False}
    return geometry


def clip_polygon(vertices, signed):
    result = []
    for a, b in zip(vertices, vertices[1:]+vertices[:1]):
        da, db = signed(a), signed(b)
        if da >= 0: result.append(a)
        if (da < 0) != (db < 0): result.append(a+(b-a)*da/(da-db))
    return result


def screen_support(rows, camera):
    eye = np.asarray(camera['eyeCm'], dtype=float); forward = np.asarray(camera['targetCm'], dtype=float)-eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, np.array([0., 0., 1.])); right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    tan_h = math.tan(math.radians(camera['horizontalFovDegrees'])/2); tan_v = tan_h/(16/9)
    shapes = []
    for row in rows:
        world = np.asarray(row['verticesCm'])-eye
        view = np.column_stack((world@right, world@up, world@forward))
        for face in np.asarray(row['indices']).reshape(-1, 3):
            p = list(view[face])
            for plane in (lambda v:v[2]-1, lambda v:v[2]*tan_h+v[0], lambda v:v[2]*tan_h-v[0],
                          lambda v:v[2]*tan_v+v[1], lambda v:v[2]*tan_v-v[1]):
                if not p: break
                p = clip_polygon(p, plane)
            if len(p) >= 3:
                xy = [[960+960*v[0]/v[2]/tan_h, 540-540*v[1]/v[2]/tan_v] for v in p]
                polygon = Polygon(xy)
                if polygon.area: shapes.append(polygon)
    return unary_union(shapes)


def house_proxy(data):
    rows = []
    for building in data['targetBuildings']:
        for polygon in polygons(data['feet'][building['id']]):
            ring = list(polygon.exterior.coords)[:-1]; bottom = min(r['renderedGroundZCm'] for r in building['renderedGroundSamples'])
            top = building['eaveElevationCm']; n = len(ring)
            vertices = [[x, y, z] for z in (bottom, top) for x, y in ring]
            indices = []
            for i in range(n):
                j = (i+1)%n; indices += [i, j, j+n, i, j+n, i+n]
            for triangle in triangulate(polygon):
                if polygon.covers(triangle):
                    base = len(vertices); vertices.extend([[x, y, top] for x, y in list(triangle.exterior.coords)[:-1]]); indices += [base, base+1, base+2]
            rows.append({'verticesCm': vertices, 'indices': indices})
    return rows


def camera_review(data, geometry):
    rows = geometry['objects']+[geometry['connector']]
    proxies = house_proxy(data)
    reviews = []
    for camera in data['cameras']:
        support = screen_support(rows, camera); house = screen_support(proxies, camera)
        by_segment = []
        for segment in geometry['segments']:
            projected = screen_support([o for o in geometry['objects'] if o['id'].startswith(segment['id']+':')], camera)
            by_segment.append({'segmentId': segment['id'], 'sourceProjectedAreaPixels': projected.area,
                'sourceScreenBoundsPixels': list(projected.bounds) if not projected.is_empty else None})
        reviews.append({'sourceCamera': camera, 'sourceProjectedNewGeometryAreaPixels': support.area,
            'sourceScreenAreaPercentWithoutOccluders': support.area/(1920*1080)*100,
            'sourceOverlapWithAuthoredWallAndEaveProxyPercent': support.intersection(house).area/support.area*100 if support.area else 0,
            'sourceScreenBoundsPixels': list(support.bounds) if not support.is_empty else None,
            'bySegment': by_segment, 'projectedSupportPixels': mapping(support), 'houseProxyPixels': mapping(house),
            'proxyDoesNotIncludeRoofCanopyAlphaOrDepthOrder': True, 'actualOcclusionOrVisibilityVerified': False,
            'nativeFovReadbackAvailable': False, 'cameraOrRendererChanged': False})
    return reviews


def material_proposals(data):
    result = {}; pins = {}
    for key, metric in (('wood_planks_grey', 150), ('gravel_floor_02', 200)):
        catalog = data['assetManifest'] if key in data['assetManifest']['assets'] else data['assetLock']
        row = catalog['assets'][key]
        require(catalog['license'] == 'CC0-1.0' and row['tileSizeMetres']*100 == metric, 'Original approved CC0 metric material required')
        maps = {}
        for role in ('diffuse', 'normal', 'roughness'):
            rec = row['maps'][role]; path = ROOT/'output/archviz/assets'/key/Path(rec['path']).name
            p = pin(path); require(p['bytes'] == rec['size'] and hashlib.md5(path.read_bytes()).hexdigest() == rec['md5'], 'Original provider photographic bytes differ')
            maps[role] = {**p, 'provider': rec, 'pixelEdits': False}; pins[key+':'+role] = p
        result['wood' if key == 'wood_planks_grey' else 'gravel'] = {'sourceAsset': key, 'metricTileCm': metric,
            'maps': maps, 'license': catalog['license'], 'proposedNormalGreenFlip': True,
            'displacementNotUsed': True, 'nativeGraphOrOpticsValidated': False}
    result['metal'] = {'source': 'own authored constant dark-metal PBR finish, no new image pixels',
        'baseColorLinear': [.055, .062, .067], 'metallic': 1, 'roughness': .62,
        'artisticUncalibrated': True, 'nativeGraphOrOpticsValidated': False}
    data['inputFiles'].update(pins)
    return result


def draw_diagram(path, data, geometry, reviews):
    image = Image.new('RGB', (1720, 1260), '#f2f0e9'); draw = ImageDraw.Draw(image)
    font_path = '/System/Library/Fonts/Supplemental/Arial.ttf'
    font = ImageFont.truetype(font_path, 18); title = ImageFont.truetype(font_path, 25); small = ImageFont.truetype(font_path, 15)
    draw.text((28, 20), 'R43 — mapped gardens, open authored boundaries and entry preservation', font=title, fill='#202f31')
    draw.text((28, 57), 'SOURCE TECHNICAL STUDY · illustrative fences/use · no ownership, surveyed height, collision or native visibility claim', font=small, fill='#4f5e61')
    bounds = (5300, 24650, 10100, 31350); scale = min(1000/(bounds[2]-bounds[0]), 1060/(bounds[3]-bounds[1]))
    def xy(p): return (35+(p[0]-bounds[0])*scale, 1140-(p[1]-bounds[1])*scale)
    def plot(geom, fill, outline=None, width=1):
        for p in polygons(geom):
            draw.polygon([xy(v) for v in p.exterior.coords], fill=fill)
            if outline: draw.line([xy(v) for v in p.exterior.coords], fill=outline, width=width)
            for hole in p.interiors: draw.polygon([xy(v) for v in hole.coords], fill='#f2f0e9')
    for key, color in (('4184/2', '#d9e3bf'), ('4184/3', '#c5dcce'), ('4215/5', '#eacb94')):
        plot(data['parcels'][key], color, '#53685b', 2)
        c = data['parcels'][key].representative_point(); draw.text(xy([c.x, c.y]), key, font=font, fill='#294539')
    for s in data['yards']['surfaces']:
        plot(shape(s['domainCm']), '#b5a697' if s['role'] in ('entry_walk', 'service_court') else '#b59b81')
    for building in data['targetBuildings']:
        plot(data['feet'][building['id']], '#cad0d1', '#425459', 2)
        c = data['feet'][building['id']].centroid; draw.text(xy([c.x, c.y]), building['id'].split('.')[1], font=font, fill='#203039')
    for plant in data['yards']['planting']:
        p = plant['positionCm']; r = plant['radialEnvelopeCm']; x, y = xy(p); rr = r*scale
        draw.ellipse((x-rr, y-rr, x+rr, y+rr), fill='#587c54', outline='#234a36')
    for s in geometry['segments']:
        draw.line([xy(s['aCm']), xy(s['bCm'])], fill='#876749' if s['style'] == 'wood' else '#324d5b', width=5)
    for o in geometry['objects']:
        if ':leaf:' in o['id']: plot(object_footprint(o), '#e18439')
    plot(shape(geometry['connector']['sourceDomainCm']), '#cfc2a2', '#9b8b6c', 2)
    colors = ['#bc4543', '#466ba2']
    for index, camera in enumerate(data['cameras']):
        eye, target = np.asarray(camera['eyeCm'][:2], dtype=float), np.asarray(camera['targetCm'][:2], dtype=float); d = target-eye; d /= np.linalg.norm(d)
        angle = math.radians(camera['horizontalFovDegrees']/2)
        rays = [eye+6100*np.array([d[0]*math.cos(a)-d[1]*math.sin(a), d[0]*math.sin(a)+d[1]*math.cos(a)]) for a in (-angle, angle)]
        for ray in rays: draw.line([xy(eye), xy(ray)], fill=colors[index], width=1)
        draw.line([xy(eye), xy(target)], fill=colors[index], width=2)
        x, y = xy(eye); draw.ellipse((x-6, y-6, x+6, y+6), fill=colors[index]); draw.text((x+8, y), 'C'+str(index+1), font=font, fill=colors[index])
    for index, review in enumerate(reviews):
        x0, y0, w, h = 1070, 105+index*415, 620, 348.75
        draw.rectangle((x0, y0, x0+w, y0+h), fill='#fafafa', outline='#adb7b8')
        for geom, color in ((shape(review['houseProxyPixels']), '#c8cece'), (shape(review['projectedSupportPixels']), '#ae794a')):
            for p in polygons(geom):
                draw.polygon([(x0+x/1920*w, y0+y/1080*h) for x, y in p.exterior.coords], fill=color)
        draw.text((x0, y0-25), 'C'+str(index+1)+' '+review['sourceCamera']['id'], font=small, fill=colors[index])
        draw.text((x0, y0+h+9), f"Source new support {review['sourceScreenAreaPercentWithoutOccluders']:.2f}% · wall/eave proxy overlap {review['sourceOverlapWithAuthoredWallAndEaveProxyPercent']:.1f}%", font=small, fill='#3b5055')
    lines = ['Six source segments; two open gates; optional120cm connector.',
             'Orange = actual thick open-gate geometry; grey = authored wall/eave proxy.',
             'Screen thumbnails are source projection, NOT a rendered visibility result.',
             'No roof/canopy alpha or depth ordering in this proxy comparison.',
             'Open strip and old13 shrubs/beds/courts preserved by full XY footprints.',
             'All source triangles under proposed post/path footprints sampled.',
             'Source terrain has near-flat authored Z; this is not a measured elevation.',
             'Future clone/native plan/report and visual acceptance remain pending.']
    for i, line in enumerate(lines): draw.text((1070, 957+i*26), line, font=small, fill='#34494d')
    draw.text((35, 1203), 'Geographic parcel outlines: ČÚZK CC BY4.0, frozen2026-09-26 data. Internal west-garden divider is explicitly illustrative.', font=small, fill='#3b5055')
    image.save(path)


def main():
    require(not OUTPUT.exists(), 'Exclusive new R43 source output required')
    data = load_inputs(); materials = material_proposals(data); geometry = build_geometry(data)
    clone_pin = pin(CLONE); require(clone_pin['sha256'] == CLONE_SHA, 'Actual prepared R43 clone receipt differs')
    clone = read(CLONE)
    require(clone['schema'] == 'brezi-image-selected-saved-r39c-garden-boundary-project-clone-r43'
            and clone['schemaVersion'] == 1 and clone['fileCount'] == 4256
            and clone['contentFiles'] == 4124 and clone['protectedFiles'] == 132
            and clone['nativeExecuted'] is False and clone['gardenBoundarySourceSelectionPending'] is True
            and clone['sourceNativeReport'] == data['selection']['sourceNativeReport']
            and clone['rootImageBaseSelection'] == pin(SELECTION), 'Only actual root-prepared clone, native acceptance pending')
    data['inputFiles']['rootPreparedCloneReceipt'] = clone_pin
    reviews = camera_review(data, geometry)
    OUTPUT.mkdir(parents=True)
    write(OUTPUT/'boundary-geometry.json', geometry)
    write(OUTPUT/'source-camera-projection.json', {'views': reviews, 'actualOcclusionOrVisibilityVerified': False})
    draw_diagram(OUTPUT/'mapped-garden-boundary-technical.png', data, geometry, reviews)
    shutil.copyfile(ROOT/OWNER, OUTPUT/'source-producer.py')
    plan = {'schema': SCHEMA, 'schemaVersion': 1, 'owner': OWNER,
        'status': 'source-only-mapped-open-boundary-geometry-and-camera-review-native-pending',
        'activeDesign': data['selection']['activeDesign'], 'setbacksMm': data['selection']['setbacksMm'],
        'inputFiles': data['inputFiles'], 'sourceSnapshot': pin(OUTPUT/'source-producer.py'),
        'selectedNativeBase': data['selection']['sourceNativeReport'], 'rootImageDecision': pin(SELECTION),
        'rootPreparedCloneReceipt': clone_pin, 'nativeCloneFullBytesRevalidatedBySourceProducer': False,
        'futureNativePlan': None, 'futureNativeReport': None,
        'mappedParcels': [{**r, 'worldCm': mapping(data['parcels'][r['parcelNumber']]),
            'computedSourceAreaM2': data['parcels'][r['parcelNumber']].area/10000} for r in data['parcelRows']],
        'twoHousesShareMapped4184_2': True, 'internalSeparationIllustrative': True,
        'strip4215_5UseOrAccessRightsVerified': False, 'legalFencePlacementOrOwnershipClaimed': False,
        'geometry': pin(OUTPUT/'boundary-geometry.json'), 'cameraProjection': pin(OUTPUT/'source-camera-projection.json'),
        'technicalDiagram': pin(OUTPUT/'mapped-garden-boundary-technical.png'), 'materials': materials,
        'audit': {'newSourceObjects': len(geometry['objects']), 'newSourceTriangles': geometry['newSourceTriangles'],
            'fenceCenterlineLengthM': sum(r['lengthCm'] for r in geometry['segments'])/100,
            'openGateCount': 2, 'existing13ShrubRootsRetained': True, 'connectorNewAreaM2': geometry['connector']['sourceAreaM2'],
            'existingActorOrRootOrMaterialFieldsChanged': 0, 'originalPhotoPixelsChanged': False,
            'fullFootprintSourceGroundFacesTraversed': True, 'sourceGeometryRenderedByUnreal': False,
            'nativeSourceAttributesOrContactVerified': False, 'nativeVisibilityVerified': False,
            'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'shippingVerified': False, 'activeOutputPromoted': False},
        'limits': ['Physical boundaries/gate use/path and metal finish are artistic; mapped cadastral rings do not prove ownership or surveyed fence alignment.',
            'Mapped4184/2 contains two source houses; the internal screen is not an invented legal parcel split.',
            'Existing BU.3852341 side yard crosses mapped strip/garden; fence omissions retain those authored surfaces and all original shrubs.',
            'Posts/hinges are real-thickness source geometry; no collision, gate animation, native ground contact or construction approval is established.',
            'All other old actors, grass/tree/garden roots and fields are a preservation requirement for future native, not a new native decode here.',
            '2D projection uses the actual source eye/target/FOV; wall/eave proxies lack roof/canopy/alpha/depth and cannot establish actual visible improvement.',
            'Source ground Z comes from unchanged existing meshes; horizontal building accuracy1.5m and authored elevation are distinct from geodetic survey.']}
    write(OUTPUT/'boundary-source-plan.json', plan)
    print(json.dumps({'plan': pin(OUTPUT/'boundary-source-plan.json'), 'geometry': plan['geometry'],
        'diagram': plan['technicalDiagram'], 'audit': plan['audit'], 'cameraReview': [{k:r[k] for k in ('sourceScreenAreaPercentWithoutOccluders', 'sourceOverlapWithAuthoredWallAndEaveProxyPercent')} for r in reviews]}))


if __name__ == '__main__':
    main()
