"""Bounded ČÚZK parcel context in the unchanged active C/B/B Unreal frame.

Python + Shapely 2.1.2 and the existing earcut package; no Unreal execution.
Legal XY comes from an immutable WFS snapshot. Surface finish, Z, paint/stakes
and vineyard planting are explicitly illustrative interpretations of the user's
orthophoto, not a survey, botanical identification or a proposed building plan.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context.py'
WFS = 'https://services.cuzk.gov.cz/wfs/inspire-cp-wfs.asp'
LICENSE_URL = 'https://cuzk.gov.cz/Predpisy/Podminky-poskytovani-prostor-dat-a-sitovych-sluzeb/Podminky-poskytovani-prostorovych-dat-CUZK.aspx'
SERVICE_TERMS_URL = 'https://cuzk.gov.cz/Predpisy/Podminky-poskytovani-prostor-dat-a-sitovych-sluzeb/Podminky-poskytovani-sitovych-sluzeb-CUZK.aspx'
QUERY = dict(service='WFS', version='2.0.0', request='GetFeature',
             typeNames='cp:CadastralParcel', srsName='urn:ogc:def:crs:EPSG::5514',
             bbox='-606900,-1202200,-606450,-1201830,urn:ogc:def:crs:EPSG::5514', count='500')
NS = {'gml': 'http://www.opengis.net/gml/3.2', 'cp': 'http://inspire.ec.europa.eu/schemas/cp/4.0'}
BOUNDS_CM = (-18000., -18000., 18000., 18000.)
PROTECTED_IDS = tuple('DOM_%05d' % i for i in [*range(2, 9), *range(48, 60)])
SEED = 60122620260926


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def immutable_write(path, data):
    path = Path(path)
    if path.exists():
        require(path.read_bytes() == data, 'Refuse to overwrite different evidence: ' + str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)


def json_bytes(data):
    return (json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def snapshot(output):
    """Fetch once, then reuse and verify that exact input; never refresh in place."""
    directory = output / 'inputs'
    xml_path, receipt_path = directory / 'cuzk-parcels.gml', directory / 'source-receipt.json'
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        require(sha(xml_path) == receipt['sha256'], 'WFS snapshot hash mismatch')
        require(receipt['query'] == QUERY, 'Snapshot query differs')
        return xml_path, receipt
    require(not xml_path.exists(), 'Unreceipted WFS input exists; inspect before retry')
    url = WFS + '?' + urllib.parse.urlencode(QUERY)
    with urllib.request.urlopen(url, timeout=45) as response:
        payload = response.read()
    root = ET.fromstring(payload)
    require(root.tag.endswith('FeatureCollection'), 'WFS did not return a FeatureCollection')
    require(root.attrib['numberReturned'] == root.attrib['numberMatched'], 'Incomplete WFS page')
    receipt = {'provider': 'Český úřad zeměměřický a katastrální (ČÚZK)',
               'attribution': '© ČÚZK, INSPIRE Cadastral Parcels, CC BY 4.0; retrieved 2026-09-26',
               'license': 'CC BY 4.0', 'licenseUrl': LICENSE_URL,
               'serviceTermsUrl': SERVICE_TERMS_URL, 'endpoint': WFS, 'url': url, 'query': QUERY,
               'retrievedAt': datetime.now(timezone.utc).isoformat(),
               'providerTimeStamp': root.attrib.get('timeStamp'),
               'featureCount': int(root.attrib['numberReturned']),
               'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload),
               'crs': 'EPSG:5514 (S-JTSK / Krovak East North)',
               'derivedGeometry': 'Integer millimetres, active C3 rotation and client house translation; UE centimetres',
               'accuracy': 'Cadastral boundary source, not a surveyed building or ground elevation',
               'ownerInformationRequestedOrStored': False}
    immutable_write(xml_path, payload)
    immutable_write(receipt_path, json_bytes(receipt))
    return xml_path, receipt


def parse_wfs(payload):
    root = ET.fromstring(payload)
    require(root.tag.endswith('FeatureCollection'), 'Invalid WFS root')
    result = []
    for feature in root.findall('.//cp:CadastralParcel', NS):
        polygons = []
        for polygon in feature.findall('.//gml:Polygon', NS):
            rings = []
            for kind in ('exterior', 'interior'):
                for node in polygon.findall('gml:' + kind + '/gml:LinearRing/gml:posList', NS):
                    values = list(map(float, node.text.split()))
                    require(len(values) % 2 == 0 and len(values) >= 8, 'Invalid two-dimensional ring')
                    ring = [[round(values[i] * 1000), round(values[i + 1] * 1000)] for i in range(0, len(values), 2)]
                    require(ring[0] == ring[-1], 'Unclosed legal polygon')
                    rings.append(ring)
            require(rings, 'Missing polygon outer ring')
            polygons.append(rings)
        label = feature.find('cp:label', NS).text
        result.append({'parcelNumber': label, 'featureId': feature.attrib['{' + NS['gml'] + '}id'],
                       'nationalReference': feature.find('cp:nationalCadastralReference', NS).text,
                       'registeredAreaM2': float(feature.find('cp:areaValue', NS).text),
                       'polygonsSjtskMm': polygons})
    require(result and len(result) == int(root.attrib['numberReturned']), 'WFS feature count mismatch')
    require(len(result) == len({r['featureId'] for r in result}), 'Duplicate WFS identity')
    return sorted(result, key=lambda row: row['parcelNumber'])


def js_round(value):
    return math.floor(value + .5)


def to_unreal(point_mm, scene):
    """Match sjtskToLocalMm exactly: round C3 first, THEN fractional translation."""
    datum, axes = scene['cadastralDatumSjtskMm'], scene['siteAxis']
    placement, center = scene['housePlacement']['translationMm'], scene['sceneCenterMm']
    dx, dy = point_mm[0] - datum['x'], point_mm[1] - datum['y']
    x = js_round(dx * axes['ux'] + dy * axes['uy']) - placement['x']
    y = js_round(dx * axes['vx'] + dy * axes['vy']) - placement['y']
    return ((x - center['x']) / 10, -(y - center['y']) / 10)


def cross(a, b, p):
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def area(points):
    return sum(a[0] * b[1] - a[1] * b[0] for a, b in zip(points, points[1:] + points[:1])) / 2


def ccw(points):
    return list(points) if area(list(points)) > 0 else list(reversed(points))


def halfplane(poly, a, b, inside=True):
    result = []
    for p, q in zip(poly, poly[1:] + poly[:1]):
        dp, dq = cross(a, b, p), cross(a, b, q)
        ip, iq = (dp >= -1e-8, dq >= -1e-8) if inside else (dp <= 1e-8, dq <= 1e-8)
        if ip:
            result.append(p)
        if ip != iq:
            t = dp / (dp - dq)
            result.append(tuple(p[k] + t * (q[k] - p[k]) for k in range(2)))
    return result


def intersect_convex(poly, cutter):
    for a, b in zip(cutter, cutter[1:] + cutter[:1]):
        poly = halfplane(poly, a, b)
        if len(poly) < 3:
            return []
    return poly


def subtract_convex(poly, cutter):
    """Partition convex poly minus convex cutter without area overlap."""
    result, remaining = [], poly
    for a, b in zip(cutter, cutter[1:] + cutter[:1]):
        outside = halfplane(remaining, a, b, False)
        if len(outside) >= 3 and abs(area(outside)) > 1e-6:
            result.append(outside)
        remaining = halfplane(remaining, a, b)
        if len(remaining) < 3 or abs(area(remaining)) < 1e-6:
            break
    return result


def bounds(poly):
    return (min(p[0] for p in poly), min(p[1] for p in poly),
            max(p[0] for p in poly), max(p[1] for p in poly))


def overlap(a, b):
    return a[0] < b[2] - 1e-7 and b[0] < a[2] - 1e-7 and a[1] < b[3] - 1e-7 and b[1] < a[3] - 1e-7


def earcut_many(polygons):
    # Earcut is already a repository dependency. Keep holes; never fill entire
    # road 6012/1 over its three interior blocks of private parcels.
    script = "import earcut,{flatten} from 'earcut'; let s=''; for await(const x of process.stdin)s+=x; console.log(JSON.stringify(JSON.parse(s).map(r=>{const f=flatten(r.map(p=>p.slice(0,-1)));return {points:Array.from({length:f.vertices.length/2},(_,i)=>f.vertices.slice(i*2,i*2+2)),indices:earcut(f.vertices,f.holes,2)}})));"
    run = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT,
                         input=json.dumps(polygons), capture_output=True, text=True, check=True)
    return json.loads(run.stdout)


def protected_source_triangles(obj_path):
    wanted = set(PROTECTED_IDS)
    vertices, triangles, current, found = [], [], None, set()
    for line in obj_path.open():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == 'v':
            vertices.append((float(parts[1]) / 10, -float(parts[2]) / 10))
        elif parts[0] == 'o':
            current = parts[1]
        elif parts[0] == 'f' and current in wanted:
            face = [vertices[int(p.split('/')[0]) - 1] for p in parts[1:]]
            for i in range(1, len(face) - 1):
                triangle = ccw([face[0], face[i], face[i + 1]])
                if abs(area(triangle)) > 1e-5:
                    triangles.append(triangle)
            found.add(current)
    require(found == wanted, 'Missing protected road/verge/access objects')
    return triangles


def within(point, ring):
    inside = False
    x, y = point
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            inside = not inside
    return inside


def in_polygons(point, polygons):
    return any(within(point, rings[0]) and not any(within(point, hole) for hole in rings[1:]) for rings in polygons)


def segment_distance(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = dx * dx + dy * dy
    t = min(1, max(0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length)) if length else 0
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def edge_clear(point, polygons, distance):
    return all(segment_distance(point, a, b) >= distance for rings in polygons for ring in rings
               for a, b in zip(ring, ring[1:]))


def ground_height(x, y, material):
    # The source DMR-labelled context is itself flat Z=-20cm, not a heightfield.
    # Keep explicit illustrative heights above it. Tracks align with existing
    # road's -11.5cm surface; short wavelength displacement is never geological.
    if material == 'context_track':
        return -11.5
    if material == 'context_parcel_line':
        return -17.15
    return -18.2 + .45 * math.sin(x * .0031 + y * .0024) + .3 * math.sin(x * .007 - y * .004)


class Mesh:
    def __init__(self, identity, material):
        self.identity, self.material = identity, material
        self.vertices, self.indices, self.uvs = [], [], []

    def triangle(self, a, b, c):
        if abs(cross(a, b, c)) < 1e-6:
            return
        if cross(a, b, c) > 0:
            b, c = c, b
        start = len(self.vertices)
        self.vertices.extend([list(a), list(b), list(c)])
        self.indices.extend([start, start + 1, start + 2])
        self.uvs.extend([[p[0] / 100, p[1] / 100] for p in (a, b, c)])

    def surface(self, poly, offset=0, depth=0):
        for i in range(1, len(poly) - 1):
            tri = (poly[0], poly[i], poly[i + 1])
            if abs(cross(*tri)) < 1e-6:
                continue
            edges = [(tri[0], tri[1], tri[2]), (tri[1], tri[2], tri[0]), (tri[2], tri[0], tri[1])]
            a, b, c = max(edges, key=lambda e: math.dist(e[0], e[1]))
            if math.dist(a, b) > 800 and depth < 16:
                mid = tuple((a[k] + b[k]) / 2 for k in range(2))
                self.surface([a, mid, c], offset, depth + 1)
                self.surface([mid, b, c], offset, depth + 1)
            else:
                self.triangle(*(tuple(p) + (ground_height(*p, self.material) + offset,) for p in tri))

    def data(self):
        return {'id': self.identity, 'material': self.material, 'verticesCm': self.vertices,
                'indices': self.indices, 'uvs': self.uvs, 'winding': 'clockwise',
                'nanite': True, 'collision': 'NoCollision'}


def classify(number):
    if number in ('6012/1', '6035/1', '6013', '6019'):
        return 'context_track'
    if number in ('6015', '6034'):
        return 'context_meadow'
    if number == '6041':
        return 'context_arable'
    if number in ('6022', '6029', '6030', '6031', '6032', '6033', '6040', '6045', '6049'):
        return 'context_crop'
    if number.startswith(('6012/', '6035/')):
        return 'context_fallow' if sum(map(ord, number)) % 3 == 0 else 'context_meadow'
    return 'context_fallow'


def stake_mesh():
    corners = [(x, y, z) for x, y, z in [(-2, -2, 0), (2, -2, 0), (2, 2, 0), (-2, 2, 0),
                                           (-2, -2, 32), (2, -2, 32), (2, 2, 32), (-2, 2, 32)]]
    vertices, indices, uvs = [], [], []
    for face in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        n = len(vertices)
        vertices.extend(corners[i] for i in face)
        indices.extend([n, n + 2, n + 1, n, n + 3, n + 2])
        uvs.extend([(0, 0), (1, 0), (1, 1), (0, 1)])
    return {'id': 'context_boundary_stake', 'material': 'context_boundary_post',
            'verticesCm': vertices, 'indices': indices, 'uvs': uvs,
            'winding': 'clockwise', 'nanite': False, 'collision': 'NoCollision'}


def shape_polygons(shape):
    """Closed outer/hole rings suitable for the existing Earcut pipeline."""
    if shape.is_empty:
        return []
    parts = [shape] if shape.geom_type == 'Polygon' else list(shape.geoms)
    return [[[list(p) for p in part.exterior.coords],
             *[[list(p) for p in hole.coords] for hole in part.interiors]]
            for part in parts if part.geom_type == 'Polygon' and part.area > 1]


def road_finish_polygons(number, polygons):
    """Keep legal perimeter exact; carve a narrower physical lane inside it.

The widths are an explicit orthophoto interpretation. The cadastre establishes
ownership geometry, not pavement width. GEOS negative buffering preserves holes
and handles junctions without extruding invented rectangular roads.
"""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    legal = unary_union([Polygon(rings[0], rings[1:]) for rings in polygons])
    require(legal.is_valid, 'Invalid legal road polygon: ' + number)
    inset = 250 if number in ('6012/1', '6035/1') else 90
    core = legal.buffer(-inset, quad_segs=4, join_style='round')
    shoulders = legal.difference(core)
    require(abs(core.area + shoulders.area - legal.area) < .1, 'Road finish partition changed legal area')
    return [('core', 'context_track', shape_polygons(core), inset),
            ('shoulder', 'context_meadow', shape_polygons(shoulders), inset)]


def vineyard_prototypes():
    post = stake_mesh()
    post['id'], post['material'] = 'context_vine_post_prototype', 'context_vine_post'
    post['verticesCm'] = [[p[0] * 1.25, p[1] * 1.25, p[2] * 5] for p in post['verticesCm']]
    # Six-sided horizontal 5mm diameter wire; instance X scale adapts span.
    vertices = [[x, .25 * math.cos(i * math.tau / 6), .25 * math.sin(i * math.tau / 6)]
                for x in (0, 600) for i in range(6)]
    indices = []
    for i in range(6):
        j = (i + 1) % 6
        indices.extend([i, j, j + 6, i, j + 6, i + 6])
    for i in range(1, 5):
        indices.extend([0, i + 1, i, 6, 6 + i, 7 + i])
    # rural.write_glb derives outward normals as AC cross AB (clockwise).
    indices = [index for n in range(0, len(indices), 3)
               for index in (indices[n], indices[n + 2], indices[n + 1])]
    wire = {'id': 'context_vine_wire_prototype', 'material': 'context_wire',
            'verticesCm': vertices, 'indices': indices,
            'uvs': [[p[0] / 600, i % 6 / 6] for i, p in enumerate(vertices)],
            'winding': 'clockwise', 'nanite': False, 'collision': 'NoCollision'}
    return post, wire


def vineyard_trellis(rows, local, protected):
    from shapely.geometry import Polygon, LineString
    from shapely.ops import unary_union
    blockers = unary_union([Polygon(poly) for poly in protected]).buffer(20)
    post_instances, wire_instances = [], []
    for (number, row), points in rows.items():
        legal = unary_union([Polygon(rings[0], rings[1:]) for rings in local[number]])
        # Each row is already straight. Split around any missing plant stations.
        runs = []
        for point in points:
            if not runs or math.dist(runs[-1][-1], point) > 180:
                runs.append([])
            runs[-1].append(point)
        for run in runs:
            if len(run) < 3:
                continue
            a, b = run[0], run[-1]
            line = LineString([a, b])
            if not legal.covers(line.buffer(5)) or line.intersects(blockers):
                continue
            length = math.dist(a, b)
            bearing = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            divisions = math.ceil(length / 600)
            posts = [[a[k] + (b[k] - a[k]) * i / divisions for k in range(2)] for i in range(divisions + 1)]
            # Each short section gets its own measured-in-plan support heights.
            # Ground relief here is <1.5cm; horizontal wires at average height
            # stay within the 160cm post height without needing pitch support.
            for p in posts:
                post_instances.append({'positionCm': [*p, ground_height(*p, 'context_meadow')],
                                       'yawDeg': bearing, 'scale': [1, 1, 1]})
            for p, q in zip(posts, posts[1:]):
                z = (ground_height(*p, 'context_meadow') + ground_height(*q, 'context_meadow')) / 2
                for level in (90, 135):
                    wire_instances.append({'positionCm': [*p, z + level], 'yawDeg': bearing,
                                           'scale': [math.dist(p, q) / 600, 1, 1]})
    return [{'id': 'context_vine_posts', 'meshId': 'context_vine_post_prototype',
             'instances': post_instances, 'cullStartCm': 18000, 'cullEndCm': 35000,
             'castShadow': True, 'collision': 'NoCollision'},
            {'id': 'context_vine_wires', 'meshId': 'context_vine_wire_prototype',
             'instances': wire_instances, 'cullStartCm': 10000, 'cullEndCm': 22000,
             'castShadow': False, 'collision': 'NoCollision'}]


def safe_fragments(poly, exclusions, boundary):
    clipped = intersect_convex(ccw(poly), boundary)
    if len(clipped) < 3 or abs(area(clipped)) < 1e-5:
        return []
    pieces = [clipped]
    for exclude, box in exclusions:
        next_pieces = []
        for piece in pieces:
            next_pieces.extend(subtract_convex(piece, exclude) if overlap(bounds(piece), box) else [piece])
        pieces = next_pieces
        if not pieces:
            break
    return pieces


def build(scene_path, obj_path, parcels, receipt, reference_path):
    scene = json.loads(scene_path.read_text())
    require(scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'C/B/B required')
    require(scene['housePlacement']['streetSetbackMm'] == scene['housePlacement']['eastSetbackMm'] == 3000, 'Both setbacks must be 3000mm')
    by_number = {r['parcelNumber']: r for r in parcels}
    comparisons = []
    for embedded in scene['parcels']:
        ring = [[p['x'], p['y']] for p in embedded['sjtskRingMm']]
        require(by_number[embedded['parcelNumber']]['polygonsSjtskMm'][0][0] == ring,
                'Current WFS differs from authoritative embedded parcel: ' + embedded['parcelNumber'])
        comparisons.append(embedded['parcelNumber'])
    local = {r['parcelNumber']: [[[*map(lambda p: to_unreal(p, scene), ring)] for ring in rings]
                                 for rings in r['polygonsSjtskMm']] for r in parcels}
    flat_polygons, identities = [], []
    road_records, road_shoulders = [], []
    for number, polygons in local.items():
        finishes = road_finish_polygons(number, polygons) if classify(number) == 'context_track' else [('surface', classify(number), polygons, None)]
        for finish, material, finish_polygons, inset in finishes:
            if inset is not None:
                road_records.append({'parcelNumber': number, 'finish': finish, 'material': material,
                                     'insetCm': inset, 'polygonsCm': finish_polygons,
                                     'evidence': 'ILLUSTRATIVE_PHYSICAL_LANE_INSIDE_EXACT_LEGAL_ROAD'})
                if finish == 'shoulder':
                    road_shoulders.append((number, finish_polygons))
            for rings in finish_polygons:
                flat_polygons.append(rings)
                identities.append((number, finish, material))
    triangulations = earcut_many(flat_polygons)
    subject_triangles = []
    for (number, finish, material), data in zip(identities, triangulations):
        if number == '6012/26':
            subject_triangles.extend(ccw([data['points'][j] for j in data['indices'][i:i + 3]]) for i in range(0, len(data['indices']), 3))
    protected = subject_triangles + protected_source_triangles(obj_path)
    exclusions = [(p, bounds(p)) for p in protected]
    xmin, ymin, xmax, ymax = BOUNDS_CM
    boundary = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
    meshes, surface_records, parcel_boundaries = [], [], []
    for part, ((number, finish, material), data) in enumerate(zip(identities, triangulations)):
        if number == '6012/26' or number.startswith('st. '):
            continue
        mesh = Mesh('context_surface_' + number.replace('/', '_') + '_' + finish + '_' + str(part), material)
        kept_area = 0
        for i in range(0, len(data['indices']), 3):
            triangle = [data['points'][j] for j in data['indices'][i:i + 3]]
            for piece in safe_fragments(triangle, exclusions, boundary):
                kept_area += abs(area(piece)) / 10000
                mesh.surface(piece)
        if not mesh.indices:
            continue
        meshes.append(mesh.data())
        surface_records.append({'parcelNumber': number, 'featureId': by_number[number]['featureId'],
                                'meshId': mesh.identity, 'material': material, 'visibleAreaM2': kept_area, 'finish': finish,
                                'legalXY': 'WFS exterior and interior rings',
                                'finishAndElevation': 'ILLUSTRATIVE_ORTHOPHOTO_INTERPRETATION'})

    # Legal lines are confined to neighboring development plots. Farmland uses
    # crop/texture changes, avoiding a glowing cadastral grid across the horizon.
    line_mesh = Mesh('context_parcel_lines', 'context_parcel_line')
    seen_edges, vertex_candidates = set(), set()
    for number, polygons in local.items():
        if number in ('6012/26', '6012/1', '6035/1') or not number.startswith(('6012/', '6035/')):
            continue
        for rings in polygons:
            for ring in rings:
                for a, b in zip(ring, ring[1:]):
                    key = tuple(sorted((tuple(round(v, 4) for v in a), tuple(round(v, 4) for v in b))))
                    if key in seen_edges:
                        continue
                    seen_edges.add(key)
                    length = math.dist(a, b)
                    if length < 1:
                        continue
                    dx, dy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
                    fragments = 0
                    for start in range(0, math.ceil(length), 380):
                        end = min(length, start + 280)
                        p = (a[0] + start * dx, a[1] + start * dy)
                        q = (a[0] + end * dx, a[1] + end * dy)
                        poly = [(p[0] - dy * 3.5, p[1] + dx * 3.5), (p[0] + dy * 3.5, p[1] - dx * 3.5),
                                (q[0] + dy * 3.5, q[1] - dx * 3.5), (q[0] - dy * 3.5, q[1] + dx * 3.5)]
                        for piece in safe_fragments(poly, exclusions, boundary):
                            line_mesh.surface(piece, .20)
                            fragments += 1
                    if fragments:
                        parcel_boundaries.append({'parcelNumber': number, 'startCm': a, 'endCm': b,
                                                  'widthCm': 7, 'dashCm': 280, 'gapCm': 100,
                                                  'semantic': 'ILLUSTRATIVE_GROUND_MARKING_ON_LEGAL_XY'})
                        vertex_candidates.add(tuple(a))
    if line_mesh.indices:
        meshes.append(line_mesh.data())

    # Placement suggestions have crown/edge clearance. The native importer can
    # use authored low vineyard foliage without treating it as surveyed plants.
    rng = random.Random(SEED)
    trees, stakes, vine_rows = [], [], {}
    for number in ('6015', '6034'):
        polygons = local[number]
        all_points = [p for rings in polygons for ring in rings for p in ring]
        bx = bounds(all_points)
        bearing = -.035 if number == '6015' else -.045
        for row, ybase in enumerate(range(math.floor(max(ymin + 200, bx[1])) + 200,
                                          math.ceil(min(ymax - 200, bx[3])), 240)):
            for n, x in enumerate(range(math.floor(max(xmin + 200, bx[0])), math.ceil(min(xmax - 200, bx[2])), 110)):
                y = ybase + bearing * x
                p = (x + rng.uniform(-8, 8), y + rng.uniform(-6, 6))
                if not (xmin + 150 < p[0] < xmax - 150 and ymin + 150 < p[1] < ymax - 150):
                    continue
                if not in_polygons(p, polygons) or not edge_clear(p, polygons, 75):
                    continue
                if any(within(p, poly) or min(segment_distance(p, a, b) for a, b in zip(poly, poly[1:] + poly[:1])) < 160 for poly in protected):
                    continue
                height = rng.uniform(132, 148)
                vine_rows.setdefault((number, row), []).append((x, y))
                trees.append({'id': f'vine_{number}_{row}_{n}', 'semantic': 'vineyard-row',
                              'parcelNumber': number, 'positionCm': [p[0], p[1], ground_height(*p, 'context_meadow')],
                              'yawDeg': math.degrees(math.atan(bearing)) + rng.uniform(-8, 8),
                              'heightCm': height, 'crownDiameterCm': rng.uniform(95, 105),
                              'scale': [height / 140] * 3, 'rowIndex': row,
                              'evidence': 'ORTHOPHOTO_ROW_PATTERN_APPROXIMATION_NOT_SURVEYED'})
    for p in sorted(vertex_candidates, key=lambda p: (math.hypot(*p), p)):
        if len(stakes) >= 12:
            break
        if not (2500 < math.hypot(*p) < 8500) or not (xmin < p[0] < xmax and ymin < p[1] < ymax):
            continue
        if any(within(p, poly) or min(segment_distance(p, a, b) for a, b in zip(poly, poly[1:] + poly[:1])) < 35 for poly in protected):
            continue
        if any(math.dist(p, old['positionCm'][:2]) < 1100 for old in stakes):
            continue
        stakes.append({'id': 'boundary_stake_' + str(len(stakes)),
                       'positionCm': [p[0], p[1], ground_height(*p, 'context_meadow')],
                       'sizeCm': [4, 4, 32], 'material': 'context_boundary_post',
                       'evidence': 'ILLUSTRATIVE_STAKE_ON_LEGAL_CORNER_NOT_AS_BUILT'})

    # Four selective source windbreak locations retain a garden scale and shade;
    # the old double row of 54 tall tree instances is not reproduced. Full 3m
    # crown circles fit the 6014 margin and clear the protected subject/roads.
    rural_path = scene_path.parent / 'rural-context-geometry.json'
    rural = json.loads(rural_path.read_text())
    old_trees = [(group['id'], index, instance)
                 for group in rural['groups'] if group['meshId'].startswith('tree_bark_')
                 for index, instance in enumerate(group['instances'])]
    selected_trees = []
    for target_x in (-2100, -1150, -180, 910):
        choices = sorted(old_trees, key=lambda item: abs(item[2]['positionCm'][0] - target_x))
        for group_id, index, original in choices:
            point = original['positionCm'][:2]
            if not in_polygons(point, local['6014']) or not edge_clear(point, local['6014'], 160):
                continue
            if any(within(point, poly) or min(segment_distance(point, a, b) for a, b in zip(poly, poly[1:] + poly[:1])) < 160 for poly in protected):
                continue
            if any(math.dist(point, old['positionCm'][:2]) < 700 for old in selected_trees):
                continue
            selected_trees.append({'id': 'garden_margin_tree_' + str(len(selected_trees)),
                                   'semantic': 'garden-margin-tree', 'parcelNumber': '6014',
                                   'positionCm': [*point, ground_height(*point, 'context_fallow')],
                                   'yawDeg': original['yawDeg'], 'heightCm': 420,
                                   'crownDiameterCm': 300, 'scale': [1, 1, 1],
                                   'sourcePlacement': {'group': group_id, 'index': index},
                                   'evidence': 'EXISTING_CONTEXT_POSITION_RETAINED_AS_PLANTING_CONCEPT_NOT_SURVEYED'})
            break
    require(len(selected_trees) == 4, 'Could not select four canopy-safe garden margin trees')
    trees.extend(selected_trees)

    ground_cover = []
    ground_rng = random.Random(SEED + 91)
    cover_parcels = [(number, polygons) for number, polygons in local.items()
                     if number != '6012/26' and classify(number) in ('context_meadow', 'context_fallow')
                     and not number.startswith('st. ')]
    cover_parcels.extend(road_shoulders)
    for x in range(-7500, 8500, 140):
        for y in range(-7000, 8500, 140):
            point = [x + ground_rng.uniform(-48, 48), y + ground_rng.uniform(-48, 48)]
            distance = math.hypot(*point)
            if distance > 8500:
                continue
            cluster = .42 + .18 * math.sin(x * .006 + math.cos(y * .004)) + .14 * math.cos(y * .0035 - x * .002)
            if ground_rng.random() > cluster:
                continue
            number = next((n for n, polys in cover_parcels if in_polygons(point, polys) and edge_clear(point, polys, 40)), None)
            if number is None:
                continue
            if any(within(point, poly) or min(segment_distance(point, a, b) for a, b in zip(poly, poly[1:] + poly[:1])) < 45 for poly in protected):
                continue
            material = 'context_meadow' if classify(number) == 'context_track' else classify(number)
            height = ground_rng.uniform(12, 32) if material == 'context_meadow' else ground_rng.uniform(22, 52)
            ground_cover.append({'id': 'context_grass_' + str(len(ground_cover)),
                                 'semantic': 'meadow-tuft' if material == 'context_meadow' else 'dry-field-grass',
                                 'parcelNumber': number, 'positionCm': [*point, ground_height(*point, material)],
                                 'yawDeg': ground_rng.uniform(0, 360), 'heightCm': height,
                                 'radiusCm': 35, 'scale': [height / 30] * 3,
                                 'variant': ground_rng.randrange(4),
                                 'evidence': 'ILLUSTRATIVE_CLUSTERED_GROUND_COVER_NOT_SURVEYED'})
    groups = []
    if stakes:
        meshes.append(stake_mesh())
        groups.append({'id': 'context_boundary_stakes', 'meshId': 'context_boundary_stake',
                       'instances': [{'positionCm': row['positionCm'], 'yawDeg': 13 + i * 17, 'scale': [1, 1, 1]}
                                     for i, row in enumerate(stakes)],
                       'cullStartCm': 10000, 'cullEndCm': 14000, 'castShadow': True, 'collision': 'NoCollision'})
    meshes.extend(vineyard_prototypes())
    groups.extend(vineyard_trellis(vine_rows, local, protected))

    return {'schemaVersion': 1, 'owner': OWNER, 'status': 'authored-context-not-native-verified',
            'units': 'centimetres', 'axes': 'UE X=OBJ X/10, Y=-OBJ Y/10, Z=OBJ Z/10',
            'boundsCm': list(BOUNDS_CM), 'activeDesign': scene['activeDesign'],
            'housePlacement': scene['housePlacement'], 'sourceSceneSha256': sha(scene_path),
            'sourceObjSha256': sha(obj_path), 'generatorSha256': sha(Path(__file__)),
            'sourceEvidence': receipt,
            'referenceImage': {'path': str(reference_path), 'sha256': sha(reference_path),
                               'role': 'User-provided cadastral orthophoto, visual interpretation only; not redistributed as a runtime texture'},
            'existingParcelComparison': {'matched': comparisons, 'integerMillimetreRingsUnchanged': True},
            'meshes': meshes, 'groups': groups, 'treePlacements': trees, 'boundaryPosts': stakes,
            'groundCoverPlacements': ground_cover,
            'retainedTreeSource': {'path': str(rural_path), 'sha256': sha(rural_path),
                                   'count': len(selected_trees), 'minimumCanopyClearanceCm': 160},
            'parcelBoundaries': parcel_boundaries, 'surfaces': surface_records,
            'roadFinishPolicy': {'method': 'GEOS negative polygon buffer; exact legal polygon = narrow lane plus herb shoulders',
                                 'dependency': 'Shapely 2.1.2', 'parts': road_records,
                                 'legalBoundaryUnchanged': True, 'pavingWidthSurveyed': False},
            'vineyardPolicy': {'stationSpacingCm': 110, 'rowSpacingCm': 240, 'trellisPostMaximumSpacingCm': 600,
                               'wireDiameterCm': .5, 'wireHeightsCm': [90, 135], 'postSizeCm': [5, 5, 160],
                               'evidence': 'ORTHOPHOTO_PATTERN_AND_PLAUSIBLE_TRELLIS_INTERPRETATION_NOT_SURVEYED'},
            'parcels': parcels, 'protectedTrianglesCm': protected,
            'protectedSourceIds': list(PROTECTED_IDS),
            'heightPolicy': {'sourceFlatGroundCm': -20, 'fieldBaseCm': -18.2,
                             'fieldVariationCm': .75, 'trackCm': -11.5,
                             'legalElevationKnown': False, 'lineOffsetCm': .20},
            'views': [
                {'id': 'exterior-neighborhood', 'label': 'Okolie a skutočné parcely',
                 'eyeCm': [-11500, 12800, 10000], 'targetCm': [1200, -600, 0],
                 'horizontalFovDegrees': 60, 'source': OWNER},
                {'id': 'exterior-vineyard', 'label': 'Vinohrad za záhradou',
                 'eyeCm': [-2600, -5100, 190], 'targetCm': [1500, -2100, 130],
                 'horizontalFovDegrees': 64, 'source': OWNER},
                {'id': 'exterior-parcels', 'label': 'Susedné parcely pri ulici',
                 'eyeCm': [-5500, 4700, 230], 'targetCm': [1400, 1100, 90],
                 'horizontalFovDegrees': 65, 'source': OWNER},
                {'id': 'exterior-site-aerial', 'label': 'Pozemok a poľná krajina',
                 'eyeCm': [10500, -9500, 7000], 'targetCm': [-400, -900, 0],
                 'horizontalFovDegrees': 57, 'source': OWNER}],
            'replacedContextRecommendation': ['Hide rural road_extension_* visual actors only; retain original near-house roads, verges and all collisions',
                                               'Replace tall generic rear windbreak only after visual review with low 6015 vineyard belt and sparse field-margin trees'],
            'preserved': ['C/B/B', 'street setback 3000mm', 'east setback 3000mm', 'house geometry',
                          'subject parcel', 'original near-house road and access surfaces', 'all collision'],
            'limits': ['XY parcel boundaries are current WFS, not a survey of house placement',
                       'Ground heights are flat-context rendering assumptions, not DMR 5G height measurements',
                       'Land cover, vineyard species/rows, paint and stakes are visual interpretations of an undated orthophoto',
                       'No surrounding buildings are invented; no satellite image is used as a ground texture',
                       'Native rendering, material assignment, collision preservation and performance still require verification']}


def meadow_base(plan):
    """Dense low grass only on existing meadow triangles, with full footprint.

Consume frozen visible geometry: never regenerate cadastral roads or trellises.
An irregularly jittered and gently warped 65cm grid gives continuous coverage;
metre-scale density/height waves keep patches coherent rather than isolated.
"""
    from collections import Counter
    from shapely.geometry import Polygon, Point
    from shapely.ops import unary_union
    from shapely.prepared import prep
    from shapely.strtree import STRtree
    selected = {row['meshId']: row for row in plan['surfaces'] if row['material'] == 'context_meadow'}
    radius, limit, spacing, road_clearance = 22., 9000., 65., 25.
    extent = Point(0, 0).buffer(limit, quad_segs=256)
    shapes, records = [], []
    for mesh in plan['meshes']:
        if mesh['id'] not in selected:
            continue
        shape = unary_union([Polygon([mesh['verticesCm'][j][:2] for j in mesh['indices'][i:i + 3]])
                             for i in range(0, len(mesh['indices']), 3)]).intersection(extent)
        if shape.area > 1:
            shapes.append(shape)
            records.append(selected[mesh['id']])
    union = unary_union(shapes)
    protected = unary_union([Polygon(tri) for tri in plan['protectedTrianglesCm']])
    allowed = union.buffer(-radius - .01).difference(protected.buffer(road_clearance + .01))
    prepared = prep(allowed)
    index = STRtree(shapes)
    rng = random.Random(SEED + 5065)
    yaw = math.radians(23.)
    c, s = math.cos(yaw), math.sin(yaw)
    positions, source_counts, minimum_clearance = [], Counter(), float('inf')
    available_cells, rejected_density = 0, 0
    for gx in range(-12800, 12801, int(spacing)):
        for gy in range(-12800, 12801, int(spacing)):
            # Different jitter per cell and a long, bounded spatial warp avoid
            # aligned rows while retaining a reproducible near-uniform base.
            a = gx + rng.uniform(-23, 23) + 9 * math.sin(gy / 670)
            b = gy + rng.uniform(-23, 23) + 9 * math.sin(gx / 910 + 1.3)
            x, y = c * a - s * b, s * a + c * b
            if math.hypot(x, y) > limit - radius:
                continue
            point = Point(x, y)
            if not prepared.covers(point):
                continue
            # Precise boundary distances independently guard rounded offsets.
            if point.distance(union.boundary) < radius or point.distance(protected) < road_clearance:
                continue
            available_cells += 1
            broad = .50 + .24 * math.sin(x / 690 + .65 * math.sin(y / 950)) + .20 * math.cos(y / 540 - x / 1200)
            occupancy = .84 + .14 * max(0., min(1., broad))
            if rng.random() > occupancy:
                rejected_density += 1
                continue
            candidates = [int(i) for i in index.query(point) if shapes[int(i)].covers(point)]
            require(candidates, 'Meadow source mesh could not be resolved')
            record = records[min(candidates)]
            height = min(25., max(18., 18.5 + 5.7 * broad + rng.uniform(-.75, .75)))
            positions.append({'id': 'meadow_base_' + str(len(positions)), 'role': 'grass', 'semantic': 'dense-green-meadow-base',
                              'positionCm': [x, y, ground_height(x, y, 'context_meadow')],
                              'heightCm': height, 'radiusCm': radius, 'yawDeg': rng.uniform(0, 360),
                              'cullEndCm': limit, 'sourceMeshId': record['meshId'],
                              'parcelNumber': record['parcelNumber'], 'sourceFinish': record['finish'],
                              'evidence': 'ILLUSTRATIVE_CONTINUOUS_MEADOW_BASE_NOT_SURVEYED'})
            source_counts[record['meshId']] += 1
            minimum_clearance = min(minimum_clearance, point.distance(protected))
    require(20000 <= len(positions) <= 35000, 'Meadow base density outside approved bounded budget')
    areas = [{'meshId': r['meshId'], 'parcelNumber': r['parcelNumber'], 'finish': r['finish'],
              'areaM2': shape.area / 10000, 'instances': source_counts[r['meshId']],
              'instancesPerM2': source_counts[r['meshId']] / (shape.area / 10000)}
             for r, shape in zip(records, shapes)]
    shoulder_count = sum(row['instances'] for row in areas if row['finish'] == 'shoulder')
    require(shoulder_count > 1000, 'Road shoulders are missing meadow base')
    policy = {'source': 'Existing R4 context_meadow mesh XY union only', 'gridSpacingCm': spacing,
              'cellJitterCm': 23, 'gridRotationDegrees': 23, 'longWarpAmplitudeCm': 9,
              'densityFieldMetreScales': [5.4, 6.9, 9.5, 12], 'occupancyRange': [.84, .98],
              'heightRangeCm': [18, 25], 'radiusCm': radius, 'protectedSourceMinimumCenterClearanceCm': road_clearance,
              'maximumDistanceFromOriginCm': limit, 'cullStartCm': 7200, 'cullEndCm': limit,
              'nativeRole': 'grass_bermuda_clump only, no companion groundcover',
              'allVisualsNoCollision': True, 'evidence': 'ARTISTIC_MEADOW_DENSITY_NOT_SURVEYED',
              'audit': {'instances': len(positions), 'eligibleMeadowAreaM2': union.area / 10000,
                        'safeCenterDomainM2': allowed.area / 10000, 'eligibleGridCells': available_cells,
                        'rejectedDensityCells': rejected_density, 'shoulderInstances': shoulder_count,
                        'densityPerMeadowM2': len(positions) / (union.area / 10000),
                        'sumCrownCircleAreaFraction': len(positions) * math.pi * radius**2 / union.area,
                        'minimumProtectedClearanceCm': minimum_clearance, 'perSurface': areas}}
    return positions, policy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference-image', type=Path, required=True)
    parser.add_argument('--base-plan', type=Path, help='Derive dense meadow only; preserve every prior scene/placement field')
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(ROOT / 'output/unreal'), 'Context output must be inside output/unreal')
    plan_path = output / 'context-plan.json'
    require(not plan_path.exists(), 'Context plan already exists; use a fresh output directory')
    if args.base_plan:
        base_path = args.base_plan.resolve()
        plan = json.loads(base_path.read_text())
        require('meadowBasePlacements' not in plan, 'Meadow base already exists in source plan')
        for name in ('cuzk-parcels.gml', 'source-receipt.json'):
            immutable_write(output / 'inputs' / name, (base_path.parent / 'inputs' / name).read_bytes())
        require(plan['sourceSceneSha256'] == sha(args.geometry / 'scene.json') and plan['sourceObjSha256'] == sha(args.geometry / 'dom-mm.obj'), 'Frozen context source differs')
        preserved = {key: hashlib.sha256(json_bytes(value)).hexdigest() for key, value in plan.items() if key != 'generatorSha256'}
        previous_generator = plan['generatorSha256']
        plan['meadowBasePlacements'], plan['meadowBasePolicy'] = meadow_base(plan)
        plan['generatorSha256'] = sha(Path(__file__))
        plan['derivedFrom'] = {'path': str(base_path), 'sha256': sha(base_path), 'generatorSha256': previous_generator,
                               'preservedFieldHashes': preserved, 'changeScope': 'Add meadowBasePlacements only; original scene and placements unchanged'}
        import shapely
        paths = [base_path, base_path.parent / 'build-environment.json', Path(__file__).resolve(),
                 args.geometry.resolve() / 'scene.json', args.geometry.resolve() / 'dom-mm.obj',
                 args.geometry.resolve() / 'rural-context-geometry.json',
                 output / 'inputs/cuzk-parcels.gml', output / 'inputs/source-receipt.json']
        environment = {'python': sys.version, 'pythonExecutable': sys.executable,
                       'shapely': shapely.__version__, 'geos': shapely.geos_version_string,
                       'inputFiles': {str(p): sha(p) for p in paths},
                       'role': 'Dense meadow derived from frozen R4 geometry; all original scene fields unchanged'}
        immutable_write(output / 'build-environment.json', json_bytes(environment))
    else:
        source, receipt = snapshot(output)
        parcels = parse_wfs(source.read_bytes())
        plan = build(args.geometry / 'scene.json', args.geometry / 'dom-mm.obj', parcels, receipt, args.reference_image.resolve())
    immutable_write(plan_path, json_bytes(plan))
    summary = {'plan': str(plan_path), 'meshes': len(plan['meshes']), 'parcels': len(plan['parcels']),
               'triangles': sum(len(m['indices']) // 3 for m in plan['meshes']),
               'surfaces': len(plan['surfaces']), 'boundarySegments': len(plan['parcelBoundaries']),
               'vineyardPlants': sum(p['semantic'] == 'vineyard-row' for p in plan['treePlacements']),
               'gardenTrees': sum(p['semantic'] == 'garden-margin-tree' for p in plan['treePlacements']),
               'groundCover': len(plan['groundCoverPlacements']), 'stakes': len(plan['boundaryPosts']),
               'meadowBase': len(plan.get('meadowBasePlacements', [])),
               'sha256': sha(plan_path)}
    immutable_write(output / 'summary.json', json_bytes(summary))
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
