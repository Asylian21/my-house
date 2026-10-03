"""R39 source-only whole original PolyHaven prop placement study. No Unreal/import/export."""
import hashlib
import json
import math
import struct
from pathlib import Path

import numpy as np
from shapely import get_coordinates
from shapely.geometry import MultiPoint, Point, Polygon, mapping, shape
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighbor-props-source-study-r39.py'
OUT = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-source-study'
REFERENCE = ROOT/'output/unreal/exterior-ph-neighbor-props-reference-20261002-r1'
RECEIPT = REFERENCE/'original-download-receipt.json'
RECEIPT_SHA = '036ee6ce5d10637c3aa0e1bb7566dc1ac199391010e57d743875625dc13e1789'
LAYOUT = ROOT/'output/unreal/exterior-context-yard-20261002-r28-study/yard-layout.json'
FINISH = ROOT/'output/unreal/exterior-neighbor-finish-20261001-r18-study/neighbor-finish-geometry.json'
GROUND = ROOT/'output/unreal/exterior-context-yard-ground-20261002-r32-study-r5/yard-ground-study-plan.json'
CONTEXT = ROOT/'output/unreal/exterior-20261002-r37b/garden-yard-integration-native-report-r2.json'
CONTEXT_SHA = 'f589c0d813ccfc35eba928a91a4545e03b159622fffa7ae2ba247545053c4532'
COMPONENTS = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2), 5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}
WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    path = Path(path)
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def checked(row):
    path = Path(row['path'])
    require(sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], 'Pinned source changed')
    return path


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def accessor(document, buffers, index):
    a = document['accessors'][index]
    require('sparse' not in a, 'Unexpected sparse original accessor')
    view = document['bufferViews'][a['bufferView']]
    code, size = COMPONENTS[a['componentType']]
    width = WIDTHS[a['type']]
    stride = view.get('byteStride', size*width)
    start = view.get('byteOffset', 0)+a.get('byteOffset', 0)
    buf = buffers[view['buffer']]
    values = [list(struct.unpack_from('<'+code*width, buf, start+i*stride)) for i in range(a['count'])]
    require(not a.get('normalized', False), 'Unexpected normalized source accessor; preserve before extending decoder')
    return values


def document(path):
    path = Path(path)
    if path.suffix == '.gltf':
        d = read(path)
        buffers = [(path.parent/b['uri']).read_bytes() for b in d['buffers']]
    else:
        data = path.read_bytes()
        require(struct.unpack_from('<III', data) == (0x46546c67, 2, len(data)), 'Invalid GLB')
        offset = 12
        d, buffers = None, []
        while offset < len(data):
            length, kind = struct.unpack_from('<II', data, offset)
            chunk = data[offset+8:offset+8+length]
            if kind == 0x4e4f534a:
                d = json.loads(chunk)
            elif kind == 0x004e4942:
                buffers.append(chunk)
            offset += 8+length
        require(d is not None and len(buffers) == 1, 'Expected one unchanged GLB BIN')
    return d, buffers


def decoded_model(asset, gltf):
    d, buffers = document(gltf)
    roots = d['scenes'][d.get('scene', 0)]['nodes']
    require(roots == list(range(len(d['nodes']))), 'Whole original scene roots must be retained')
    parts, points, triangles = [], [], []
    for node_index in roots:
        node = d['nodes'][node_index]
        require(not any(k in node for k in ('rotation', 'scale', 'matrix', 'children')), 'New source pose requires explicit decoder')
        translation = np.array(node.get('translation', [0., 0., 0.]), dtype=float)
        mesh = d['meshes'][node['mesh']]
        require(len(mesh['primitives']) == 1, 'Whole source primitive census changed')
        p = mesh['primitives'][0]
        require(p.get('mode', 4) == 4 and set(p['attributes']) == {'POSITION', 'NORMAL', 'TEXCOORD_0'}, 'Original attribute/triangle schema changed')
        attrs = {k: accessor(d, buffers, a) for k, a in p['attributes'].items()}
        ix = [r[0] for r in accessor(d, buffers, p['indices'])]
        require(len(ix) % 3 == 0 and max(ix) < len(attrs['POSITION']), 'Original topology invalid')
        posed = (np.array(attrs['POSITION'], dtype=float)+translation)[:, [0, 2, 1]]*100.
        base = len(points)
        points.extend(posed.tolist())
        triangles.extend([[base+i for i in ix[j:j+3]] for j in range(0, len(ix), 3)])
        parts.append({'nodeIndex': node_index, 'nodeName': node.get('name'), 'sourceNode': node,
            'sourceMeshName': mesh.get('name'), 'materialIndex': p['material'], 'vertexCount': len(posed),
            'triangleCount': len(ix)//3, 'originalAttributes': sorted(attrs), 'sourceAccessorHashes': {k: digest(v) for k, v in attrs.items()},
            'originalIndexSha256': digest(ix), 'translatedSourceBoundsCm': [posed.min(axis=0).tolist(), posed.max(axis=0).tolist()]})
    points = np.array(points, dtype=float)
    require(np.isfinite(points).all(), 'Nonfinite original source points')
    lo, hi = points.min(axis=0), points.max(axis=0)
    descriptor = {'id': asset, 'gltf': pin(gltf), 'bins': [pin(Path(gltf).parent/b['uri']) for b in d['buffers']],
        'scene': d['scenes'][d.get('scene', 0)], 'originalNodes': d['nodes'], 'parts': parts,
        'sourceMaterials': d['materials'], 'extensionsUsed': d.get('extensionsUsed', []),
        'vertexCount': len(points), 'triangleCount': len(triangles), 'completeAssemblyPartCount': len(parts),
        'sourceNativeBasisCm': 'centimetres [glTF X, glTF Z, glTF Y], original node translations retained; no new export',
        'boundsCm': [lo.tolist(), hi.tolist()], 'dimensionsCm': (hi-lo).tolist(),
        'wholeAssemblyPositionsSha256': digest(points.tolist()), 'wholeAssemblyIndicesSha256': digest(triangles),
        'sourceTangentPresent': False, 'nativeGeometryOrMaterialReadbackPerformed': False}
    return descriptor, points, triangles


def local_xy(yard, point):
    e = yard['entrance']
    q = np.array(point[:2])-e['edgeOriginCm']
    return [float(q @ e['tangent']), float(q @ e['outward'])]


def world_xy(yard, u, v):
    e = yard['entrance']
    return (np.array(e['edgeOriginCm'])+u*np.array(e['tangent'])+v*np.array(e['outward'])).tolist()


def rotation(points, yaw):
    r = math.radians(yaw)
    c, s = math.cos(r), math.sin(r)
    result = points.copy()
    result[:, 0] = c*points[:, 0]-s*points[:, 1]
    result[:, 1] = s*points[:, 0]+c*points[:, 1]
    return result


def floor_mesh(source_glb):
    d, buffers = document(source_glb)
    matches = [m for m in d['meshes'] if m['name'] == 'yard_ground_r32_service_court_LOD0']
    if not matches:
        matches = [m for m in d['meshes'] if 'service_court' in m['name']]
    require(len(matches) == 1, 'Exact original service court mesh required')
    p = matches[0]['primitives'][0]
    points = np.array(accessor(d, buffers, p['attributes']['POSITION']))[:, [0, 2, 1]]*100.
    points = points.astype(np.float32).astype(float)
    ix = [r[0] for r in accessor(d, buffers, p['indices'])]
    tris = [points[ix[i:i+3]] for i in range(0, len(ix), 3)]
    polygons = [Polygon(t[:, :2]) for t in tris]
    require(all(p.area > 0 for p in polygons), 'Service court source projection degeneracy')
    return tris, polygons, STRtree(polygons)


def bary_height(triangle, xy):
    a, b, c = triangle
    ab, ac = b[:2]-a[:2], c[:2]-a[:2]
    q = np.array(xy)-a[:2]
    determinant = ab[0]*ac[1]-ab[1]*ac[0]
    require(determinant != 0, 'Cannot interpolate a degenerate projection')
    u = (q[0]*ac[1]-q[1]*ac[0])/determinant
    v = (ab[0]*q[1]-ab[1]*q[0])/determinant
    return float(a[2]+u*(b[2]-a[2])+v*(c[2]-a[2]))


def seat_on_floor(points, indices, floor):
    """Minimum source lift from all bottom triangle/floor intersection vertices.

    Degenerate XY faces use their minimum Z as a conservative lower envelope.
    No original prop or ground vertex is rewritten.
    """
    tris, polygons, tree = floor
    hull = MultiPoint(points[:, :2]).convex_hull
    candidates = list(tree.query(hull, predicate='intersects'))
    require(candidates and unary_union([polygons[i] for i in candidates]).covers(hull), 'Whole prop must sit over hard court')
    high_floor = max(float(tris[i][:, 2].max()) for i in candidates)
    low = float(points[:, 2].min())
    initial = high_floor-low
    lift, evaluated, degenerate = -math.inf, 0, 0
    for index in indices:
        triangle = points[index]
        if float(triangle[:, 2].min()) > low+(high_floor-min(float(tris[i][:, 2].min()) for i in candidates))+1.:
            continue  # all its points are already above the highest possible floor at the final minimum lift
        projection = MultiPoint(triangle[:, :2]).convex_hull
        area = projection.area
        for floor_index in tree.query(projection, predicate='intersects'):
            intersection = projection.intersection(polygons[floor_index])
            for xy in get_coordinates(intersection):
                z = bary_height(triangle, xy) if area > 0 else float(triangle[:, 2].min())
                lift = max(lift, bary_height(tris[floor_index], xy)-z)
                evaluated += 1
        if area == 0:
            degenerate += 1
    require(math.isfinite(lift) and lift <= initial+1e-8, 'Source bottom contact arithmetic failed')
    clearances = []
    for point in points:
        hits = tree.query(Point(point[:2]), predicate='intersects')
        require(len(hits), 'Prop vertex outside hard court')
        ground = max(bary_height(tris[i], point[:2]) for i in hits)
        clearances.append(float(point[2]+lift-ground))
    require(min(clearances) >= -1e-8, 'Source prop/floor intersection')
    return lift, {'sourceIntersectionSupportVerticesEvaluated': evaluated, 'conservativeDegenerateProjectedFaces': degenerate,
        'allDecodedVertexMinimumFloorClearanceCm': min(clearances),
        'sourceBottomContactIsConservativeTriangleSupport': True,
        'nativeBottomContactOrCollisionVerified': False, 'nativeFloorSampledAtPlacement': False}


def wall_support(yard, mesh):
    points, indices = mesh['verticesCm'], mesh['indices']
    triangles = []
    for start in range(0, len(indices), 3):
        p = [points[i] for i in indices[start:start+3]]
        local = [local_xy(yard, q) for q in p]
        if max(abs(q[1]) for q in local) < 1e-6:
            polygon = Polygon([[q[0], p[i][2]] for i, q in enumerate(local)])
            if polygon.area > 0:
                triangles.append(polygon)
    require(triangles, 'Source front wall solid triangles missing')
    return unary_union(triangles), len(triangles)


def source_study():
    require(sha(RECEIPT) == RECEIPT_SHA and sha(CONTEXT) == CONTEXT_SHA, 'Actual reference contract changed')
    receipt = read(RECEIPT)
    require(receipt['fileCount'] == 26 and receipt['totalOriginalBytes'] == 159130454, 'Exact downloaded originals required')
    for row in receipt['files']:
        path = checked(row)
        require(path.stat().st_size == row['declaredBytes'] and hashlib.md5(path.read_bytes()).hexdigest() == row['declaredMd5'], 'Original published bytes/MD5 changed')
    layout, finish, ground, context = read(LAYOUT), read(FINISH), read(GROUND), read(CONTEXT)
    source_glb = checked(ground['sourceGlb'])
    saved = read(checked(context['savedActorWitness']))
    require(context['status'] == 'verified-saved-clean-selected-garden-and-yard-integration' and context['savedMapUnloadedReloaded'], 'Reference actual saved context required')
    models, data = {}, {}
    for asset in receipt['assetIds']:
        row = next(r for r in receipt['files'] if r['asset'] == asset and r['role'] == 'gltf')
        descriptor, points, triangles = decoded_model(asset, row['path'])
        models[asset], data[asset] = descriptor, (points, triangles)
    require(models['garden_hose_wall_mounted_01']['triangleCount'] == 11684 and models['garden_hose_wall_mounted_01']['completeAssemblyPartCount'] == 2, 'Both original hose parts must remain')
    require(models['planter_pot_clay']['triangleCount'] == 3080 and models['watering_can_metal_01']['triangleCount'] == 11837, 'Whole original model census changed')
    floor = floor_mesh(source_glb)
    placements = []
    specs = [('BU.572063', 'garden_hose_wall_mounted_01', 'wall', 400., 0., None),
        ('BU.572063', 'planter_pot_clay', 'court', 450., 625., 18.),
        ('BU.3800911', 'planter_pot_clay', 'court', 750., 625., -21.),
        ('BU.3800911', 'watering_can_metal_01', 'court', 700., 550., 43.),
        ('BU.3852341', 'garden_hose_wall_mounted_01', 'wall', 630., 0., None),
        ('BU.3852341', 'planter_pot_clay', 'court', 475., 575., 37.)]
    wall_refs = []
    for ordinal, (building, model, kind, u, v, yaw) in enumerate(specs):
        yard = next(y for y in layout['yards'] if y['buildingSourceId'] == building)
        e = yard['entrance']
        points, triangles = data[model]
        row = {'id': 'neighbor_prop_r39_'+str(ordinal), 'modelId': model, 'buildingSourceId': building,
            'role': 'wall-mounted-complete-hose' if kind == 'wall' else 'empty-clay-pot' if model == 'planter_pot_clay' else 'whole-watering-can',
            'uniformScale': 1., 'sourcePhysicalDimensionsCm': models[model]['dimensionsCm'],
            'wholeAssemblyPartCount': models[model]['completeAssemblyPartCount'], 'sourceTriangleCount': models[model]['triangleCount'],
            'sourceOnlyPlacement': True, 'nativeApplied': False, 'nativeVisibilityVerified': False}
        walk = shape(next(s['domainCm'] for s in layout['surfaces'] if s['buildingSourceId'] == building and s['role'] == 'entry_walk'))
        if kind == 'wall':
            yaw = math.degrees(math.atan2(-e['outward'][0], e['outward'][1]))
            v = -float(points[:, 1].min())
            position = [*world_xy(yard, u, v), -25.+120.]
            transformed = rotation(points, yaw)+position
            wall = next(m for m in finish['candidateMeshes'] if m['buildingSourceId'] == building and m['role'] == 'wall')
            solid, count = wall_support(yard, wall)
            projection = MultiPoint([[local_xy(yard, p)[0], p[2]] for p in transformed]).convex_hull
            require(solid.covers(projection), 'Whole hose wall projection overlaps a window/door/edge')
            # Exact source component exists in the actual saved reference; no fresh actor decode.
            found = [(actor, a) for actor, a in saved.items() if any((c.get('mesh') or '').endswith('/'+wall['id']+'_LOD0.'+wall['id']+'_LOD0') for c in a.get('components', []))]
            require(len(found) == 1, 'Actual saved reference wall binding missing')
            row['wallFit'] = {'nativeLocalPlusYAlignedWithSourceOutward': True, 'rotationPreservesHandedness': True,
                'sourceSolidFrontWallTriangleCount': count, 'wholeAssemblyProjectedHullInsideSolidFrontWall': True,
                'windowDoorOpeningsPreserved': True, 'wallProjectionBoundaryClearanceCm': projection.distance(solid.boundary),
                'sourceMountPlaneOutwardCm': float(min(local_xy(yard, p)[1] for p in transformed)),
                'mountRootHeightAboveAuthoredGroundCm': 120., 'sourceGroundCm': -25.,
                'physicalWaterConnectionOrSurveyedMountHeightVerified': False, 'nativeWallContactVerified': False,
                'referenceWallActor': found[0][0], 'referenceWallMesh': wall['id']}
            wall_refs.append(row['wallFit'])
        else:
            xy = world_xy(yard, u, v)
            transformed = rotation(points, yaw)
            transformed[:, :2] += xy
            court = shape(next(s['domainCm'] for s in layout['surfaces'] if s['buildingSourceId'] == building and s['role'] == 'service_court'))
            hull = MultiPoint(transformed[:, :2]).convex_hull
            require(court.covers(hull), 'Whole prop outside hard court')
            z, contact = seat_on_floor(transformed, triangles, floor)
            position = [*xy, z]
            transformed[:, 2] += z
            row['sourceBottomContact'] = contact
            row['courtFit'] = {'wholeDecodedProjectedHullInsideCourt': True, 'boundaryClearanceCm': hull.distance(court.boundary)}
        hull = MultiPoint(transformed[:, :2]).convex_hull
        door = Point(e['doorCenterCm'][:2])
        walk_clearance = hull.distance(walk)
        require(walk_clearance >= (1. if kind == 'wall' else 90.), 'Complete prop blocks the existing authored entry route')
        shrub_clearance = min(hull.distance(Point(p['positionCm'][:2]))-p['radialEnvelopeCm'] for p in layout['planting'])
        require(shrub_clearance > 0, 'Whole prop intersects existing containing shrub crown')
        row.update(positionCm=position, yawDegrees=yaw, facadeLocalUvCm=[u, v],
            sourceWorldBoundsCm=[transformed.min(axis=0).tolist(), transformed.max(axis=0).tolist()],
            projectedHullCm=mapping(hull), walkingRouteClearanceCm=walk_clearance,
            doorCenterClearanceCm=hull.distance(door), minimumExistingShrubContainingCircleClearanceCm=shrub_clearance,
            groundWalkingRouteUnchanged=True, wholeAssemblyPositionsWorldSha256=digest(transformed.tolist()))
        placements.append(row)
    for i, a in enumerate(placements):
        for b in placements[i+1:]:
            if a['buildingSourceId'] == b['buildingSourceId']:
                require(shape(a['projectedHullCm']).distance(shape(b['projectedHullCm'])) > 15., 'Props need distinct occupied footprint clearance')
    inputs = [pin(RECEIPT), pin(LAYOUT), pin(FINISH), pin(GROUND), pin(CONTEXT), context['savedActorWitness'], pin(source_glb)]
    return {'schema': 'brezi-whole-original-neighbor-props-source-proposal-r39', 'schemaVersion': 1, 'owner': OWNER,
        'status': 'source-only-six-whole-prop-placements-future-native-base-unselected',
        'originalDownloadReceipt': pin(RECEIPT), 'license': 'CC0', 'licenseUrl': 'https://polyhaven.com/license',
        'referenceSavedContextReport': pin(CONTEXT), 'referenceSavedContextIsSelectedFutureNativeBase': False,
        'futureNativeBase': None, 'futureProjectClone': None, 'futureNativeReport': None,
        'models': models, 'placements': placements, 'scope': {'wholeAssemblyRoots': 6, 'renderingSourceMeshInstances': 8,
            'hoseAssemblies': 2, 'clayPots': 3, 'wateringCans': 1, 'sourceTriangleInstances': 44445,
            'newNativeActorsOrComponents': None, 'oldActorsModified': 0, 'oldRootsMovedOrRemoved': 0},
        'inputFiles': inputs, 'all26DownloadedFilesPublishedMd5SizeAndSha256Exact': True,
        'sourcePhotoPixelsEdited': False, 'originalGltfBinAttributesIndicesNodePosesUnchanged': True,
        'nativeImported': False, 'nativeCollisionOrWalkabilityVerified': False, 'nativeAppearanceAccepted': False,
        'fullPhotorealismAccepted': False, 'shippingAccepted': False, 'performanceAccepted': False,
        'limits': ['Source arrangement is an authored habitation cue, not observed residents or installed plumbing.',
            'Future native base requires root selection after the separate R38 image outcome.',
            'Source normals and UV0 are original; tangents absent. Future native tangent/material readback remains pending.',
            'Watering-can KHR specular/IOR metadata remains original; native optical equivalence is unproven.',
            'Pots remain empty; no invented flowers or foliage.',
            'Conservative source floor support may leave a small measured contact gap on relief; native contact/pixels remain pending.',
            'Door route is authored geometry, not surveyed access, legal parcel proof, or a physical accessibility assessment.']}


def draw(proposal):
    layout = read(LAYOUT)
    colors = {'entry_walk': '#b9b3a5', 'service_court': '#d3c6ab', 'soil_bed': '#a0ae79', 'worn_edge': '#e9e5d8'}
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1260 570"><rect width="1260" height="570" fill="#f7f7f2"/>']
    for column, yard in enumerate(layout['yards']):
        building = yard['buildingSourceId']
        ox, oy, scale = column*420+42, 76, .3
        def xy(world):
            u, v = local_xy(yard, world)
            return [ox+u*scale, oy+v*scale]
        parts.append(f'<text x="{ox}" y="35" font-family="sans-serif" font-size="19" fill="#18342c">{building}</text>')
        for role in ('worn_edge', 'soil_bed', 'service_court', 'entry_walk'):
            geometry = shape(next(s['domainCm'] for s in layout['surfaces'] if s['buildingSourceId'] == building and s['role'] == role))
            for polygon in list(geometry.geoms) if geometry.geom_type == 'MultiPolygon' else [geometry]:
                points = ' '.join(','.join(f'{n:.2f}' for n in xy(p)) for p in polygon.exterior.coords)
                parts.append(f'<polygon points="{points}" fill="{colors[role]}" stroke="#ffffff" stroke-width="1"/>')
        edge = yard['entrance']['edgeLengthCm']
        parts.append(f'<path d="M{ox},{oy}h{edge*scale}" stroke="#353e36" stroke-width="8"/>')
        parts.append(f'<path d="M{ox+35*scale},{oy}h{85*scale}" stroke="#fbfbf7" stroke-width="8"/>')
        for p in layout['planting']:
            if p['buildingSourceId'] == building:
                x, y = xy(p['positionCm'])
                parts.append(f'<circle cx="{x}" cy="{y}" r="{p["radialEnvelopeCm"]*scale}" fill="#607349" opacity=".6"/>')
        for row in proposal['placements']:
            if row['buildingSourceId'] != building:
                continue
            hull = shape(row['projectedHullCm'])
            points = ' '.join(','.join(f'{n:.2f}' for n in xy(p)) for p in hull.exterior.coords)
            parts.append(f'<polygon points="{points}" fill="#e79546" stroke="#5f3820" stroke-width="1.5"/>')
            x, y = xy(row['positionCm'])
            name = 'Hose' if row['role'].startswith('wall') else 'Pot' if row['role']=='empty-clay-pot' else 'Can'
            parts.append(f'<text x="{x+10}" y="{y+15}" font-family="sans-serif" font-size="12">{name} {row["id"].split("_")[-1]}</text>')
        parts.append(f'<text x="{ox}" y="340" font-family="sans-serif" font-size="12">Existing 105–115 cm entry walk stays clear.</text>')
    parts.append('<text x="40" y="400" font-family="sans-serif" font-size="17">SOURCE PLACEMENT ONLY · scale 1 · complete original assemblies</text>')
    parts.append('<text x="40" y="430" font-family="sans-serif" font-size="14">2 wall hoses (both parts), 3 empty clay pots, 1 watering can. No old geometry or planting moves.</text>')
    parts.append('<text x="40" y="458" font-family="sans-serif" font-size="14">Dark line: solid facade · white: door · gray/tan: walking/court · green: existing planting</text>')
    parts.append('<text x="40" y="490" font-family="sans-serif" font-size="14">Native base, contact, materials, visibility and full realism remain pending.</text></svg>')
    return ''.join(parts)


def main():
    require(not OUT.exists(), 'Do not overwrite a source study; create a new revision')
    proposal = source_study()
    OUT.mkdir()
    (OUT/'neighbor-props-source-proposal.json').write_text(json.dumps(proposal, indent=2, allow_nan=False)+'\n')
    (OUT/'neighbor-props-layout.svg').write_text(draw(proposal)+'\n')
    rows = ''.join(f'<tr><td>{k}</td><td>{m["completeAssemblyPartCount"]}</td><td>{m["triangleCount"]:,}</td><td>'+ ' × '.join(f'{n:.2f}' for n in m['dimensionsCm'])+'</td></tr>' for k,m in proposal['models'].items())
    html = '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>R39 original neighbor props source study</title><style>body{font:16px/1.5 system-ui;background:#f7f7f2;color:#18342c;margin:30px auto;max-width:1260px;padding:0 20px}img{width:100%;height:auto}td,th{padding:8px;text-align:left;border-bottom:1px solid #ccd3c8}a{color:#315d42}</style><h1>Restrained inhabited-yard props</h1><p>Six authored placements using complete original CC0 assets. Future native base remains unselected; this is a source fit proposal.</p><img src="neighbor-props-layout.svg" alt="Three source yards and six original prop placements"><table><tr><th>Original model</th><th>Parts</th><th>Triangles</th><th>Width × depth × height (cm)</th></tr>'+rows+'</table><p><a href="neighbor-props-source-proposal.json">Exact positions, original source metadata and measured clearances</a></p><p>No source pixels or geometry changed. Wall fit and floor support are source calculations; native contact, visibility, material equivalence and appearance remain unverified.</p>'
    (OUT/'neighbor-props-source-review.html').write_text(html+'\n')
    print(json.dumps({'proposal': pin(OUT/'neighbor-props-source-proposal.json'), 'diagram': pin(OUT/'neighbor-props-layout.svg'),
        'html': pin(OUT/'neighbor-props-source-review.html'), 'counts': proposal['scope'], 'placements': [{k:r[k] for k in ('id','positionCm','yawDegrees','walkingRouteClearanceCm')} for r in proposal['placements']]}))


if __name__ == '__main__':
    main()
