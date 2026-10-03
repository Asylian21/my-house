"""Strict additive natural-lawn integration; safe to import outside Unreal.

The caller owns the map save/reload and Content inventory. These helpers change
only the visibility and detail-scaling of four receipt-bound legacy lawn HISMs.
The original lawn ground, meshes, materials, collision and transforms survive.
"""
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-lawn-native.py'
GENERATOR = 'scripts/unreal/exterior-lawn-natural.py'
MANAGED_GENERATOR = 'scripts/unreal/exterior-lawn-natural-managed.py'
COVERAGE_GENERATOR = 'scripts/unreal/exterior-lawn-coverage.py'
FINE_GENERATOR = 'scripts/unreal/exterior-lawn-fine.py'
UPRIGHT_GENERATOR = 'scripts/unreal/exterior-lawn-upright.py'
COVERAGE_OWNERS = (COVERAGE_GENERATOR, FINE_GENERATOR, UPRIGHT_GENERATOR)
MANAGED_OWNERS = (MANAGED_GENERATOR, *COVERAGE_OWNERS)
LEGACY_TAG = 'BreziPhotorealLawn'
LEGACY_GROUPS = tuple('LawnTuft'+str(i) for i in range(4))
LEGACY_MATERIAL = '/Game/Brezi/Photoreal/Lawn/Materials/M_blade_a208ebf785c91f00.M_blade_a208ebf785c91f00'
SCREENS = [1., .025, .007]
RENDER_FLAGS = ('cast_shadow', 'cast_hidden_shadow', 'affect_distance_field_lighting',
                'affect_dynamic_indirect_lighting', 'affect_indirect_lighting_while_hidden', 'visible_in_ray_tracing')
FAMILY = {f'lawn_natural_{g}_{i}' for g in range(2) for i in range(8)} | {
          f'lawn_natural_edge_{g}_{i}' for g in range(2) for i in range(2)}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def finite(values, count):
    return isinstance(values, (list, tuple)) and len(values) == count and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values)


def pinned(path, expected):
    path = (ROOT/path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == expected,
            'Natural lawn input path/hash differs: '+str(path))
    return path


def _source_context(plan):
    paths = [p for p, h in plan['inputFiles'].items() if p.endswith('/geometry/scene.json') and h == plan['sourceSceneSha256']]
    require(paths, 'Natural lawn source scene pin missing')
    # Managed successor provenance also pins the inherited byte-identical
    # scene copy. Every mirror must carry the same pinned OBJ frame.
    require(all(plan['inputFiles'].get(str(Path(p).parent/'dom-mm.obj')) == plan['sourceObjSha256'] for p in paths),
            'Natural lawn source mirror OBJ frame differs')
    geometry = Path(paths[0]).parent
    require(plan['inputFiles'].get(str(geometry/'dom-mm.obj')) == plan['sourceObjSha256'], 'Natural lawn OBJ frame pin differs')
    source_path = ROOT/'scripts/unreal/lawn-geometry.py'
    # The source-domain helper itself is stdlib-only; its sibling policy import
    # is also required by the ordinary standalone Python test runner.
    if str(source_path.parent) not in sys.path:
        sys.path.insert(0, str(source_path.parent))
    spec = importlib.util.spec_from_file_location('natural_lawn_source_domain', source_path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    scene, faces, boundary, exclusions, extra = module.source_context(geometry)
    require(plan['housePlacement'] == scene['housePlacement'], 'Natural lawn placement differs from actual source')
    require(digest(plan['exclusions']) == digest(exclusions), 'Natural lawn source exclusion masks differ')
    return faces, boundary, exclusions, extra


def _glb_geometry(path, include_frames=False):
    raw = Path(path).read_bytes()
    require(len(raw) >= 20 and struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Natural lawn GLB header differs')
    json_length, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4E4F534A, 'Natural lawn GLB JSON missing')
    data = json.loads(raw[20:20+json_length])
    offset = 20+json_length
    binary_length, kind = struct.unpack_from('<II', raw, offset)
    require(kind == 0x004E4942 and offset+8+binary_length == len(raw), 'Natural lawn GLB binary missing')
    binary = memoryview(raw)[offset+8:]
    result = {}
    for node in data['nodes']:
        require(node['name'] not in result and not any(k in node for k in ('matrix', 'translation', 'rotation', 'scale')),
                'Natural lawn geometry node transform/name differs')
        primitives = data['meshes'][node['mesh']]['primitives']
        require(len(primitives) == 1 and primitives[0].get('mode', 4) == 4, 'Natural lawn must use actual triangle geometry')
        primitive = primitives[0]
        accessor = data['accessors'][primitive['attributes']['POSITION']]
        require(accessor['componentType'] == 5126 and accessor['type'] == 'VEC3' and not accessor.get('sparse'),
                'Natural lawn positions must be ordinary float32')
        require(accessor['count'] > 0, 'Natural lawn decoded positions are empty')
        view = data['bufferViews'][accessor['bufferView']]
        require(view.get('buffer', 0) == 0, 'Natural lawn external buffer refused')
        start = view.get('byteOffset', 0)+accessor.get('byteOffset', 0); stride = view.get('byteStride', 12)
        require(stride >= 12 and start+max(0, accessor['count']-1)*stride+12 <= len(binary), 'Natural lawn position buffer truncated')
        positions = []
        for i in range(accessor['count']):
            x, y, z = struct.unpack_from('<3f', binary, start+i*stride)
            require(finite((x,y,z), 3), 'Natural lawn decoded position is non-finite')
            positions.append((100*x, 100*z, 100*y))
        indices = data['accessors'][primitive['indices']]
        require(indices['count'] > 0 and indices['count'] % 3 == 0 and indices['type'] == 'SCALAR'
                and indices['componentType'] in (5121,5123,5125) and not indices.get('sparse'),
                'Natural lawn decoded triangle count/type differs')
        index_view = data['bufferViews'][indices['bufferView']]
        size, fmt = {5121:(1,'B'),5123:(2,'H'),5125:(4,'I')}[indices['componentType']]
        start = index_view.get('byteOffset',0)+indices.get('byteOffset',0)
        require(index_view.get('buffer',0) == 0 and not index_view.get('byteStride')
                and start+indices['count']*size <= len(binary), 'Natural lawn index buffer differs')
        triangle_indices = struct.unpack_from('<'+fmt*indices['count'],binary,start)
        require(all(index < len(positions) for index in triangle_indices),
                'Natural lawn actual triangle indices escape vertices')
        require(data['materials'][primitive['material']]['name'] == 'lawn_natural_blade', 'Natural lawn decoded material family differs')
        result[node['name']] = {'positions':positions, 'triangles':indices['count']//3,
                              'indices': triangle_indices}
        if include_frames:
            def attribute(name, width):
                require(name in primitive['attributes'], 'Upright lawn actual frame attribute missing: '+name)
                a = data['accessors'][primitive['attributes'][name]]
                require(a['componentType'] == 5126 and a['type'] == 'VEC'+str(width)
                        and a['count'] == len(positions) and not a.get('sparse') and not a.get('normalized'),
                        'Upright lawn actual frame attribute type/count differs: '+name)
                v = data['bufferViews'][a['bufferView']]; step = v.get('byteStride', width*4)
                beginning = v.get('byteOffset', 0)+a.get('byteOffset', 0)
                require(v.get('buffer', 0) == 0 and step >= width*4 and beginning+(a['count']-1)*step+width*4 <= len(binary),
                        'Upright lawn actual frame attribute buffer differs: '+name)
                values = [struct.unpack_from('<'+'f'*width, binary, beginning+i*step) for i in range(a['count'])]
                require(all(finite(row, width) for row in values), 'Upright lawn actual frame attribute non-finite: '+name)
                return values
            normals = attribute('NORMAL', 3); tangents = attribute('TANGENT', 4)
            result[node['name']].update(normals=[(p[0], p[2], p[1]) for p in normals],
                tangents=[(p[0], p[2], p[1], -p[3]) for p in tangents],
                uv0=attribute('TEXCOORD_0', 2), uv1=attribute('TEXCOORD_1', 2), colors=attribute('COLOR_0', 4))
            require(data['materials'][primitive['material']].get('doubleSided') is True,
                    'Upright lawn actual leaf material must be two-sided')
    return result


def _inside_ring(point, ring):
    x, y = point; inside = False
    for a, b in zip(ring, ring[1:]+ring[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            inside = not inside
    return inside


def _distance(point, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]; size = dx*dx+dy*dy
    t = min(1., max(0., ((point[0]-a[0])*dx+(point[1]-a[1])*dy)/size)) if size else 0.
    return math.hypot(point[0]-a[0]-t*dx, point[1]-a[1]-t*dy)


def _inside_triangle(point, triangle):
    signs = [(b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])
             for a,b in zip(triangle, triangle[1:]+triangle[:1])]
    return min(signs) >= -1e-7 or max(signs) <= 1e-7


def _union_boundary(polygons):
    """External union edges, excluding shared edges between the keep polygons."""
    edges=[(a,b) for ring in polygons for a,b in zip(ring,ring[1:]+ring[:1]) if a!=b]
    boundary=[]
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    for a,b in edges:
        d=[b[0]-a[0],b[1]-a[1]];length=math.hypot(*d);splits={0.,1.}
        for c,e in edges:
            other=[e[0]-c[0],e[1]-c[1]];start=[c[0]-a[0],c[1]-a[1]];denominator=cross(d,other)
            if abs(denominator)>1e-9:
                t=cross(start,other)/denominator;u=cross(start,d)/denominator
                if 0<=t<=1 and 0<=u<=1:splits.add(t)
            else:
                for p in (c,e):
                    if _distance(p,a,b)<1e-7:
                        splits.add(min(1.,max(0.,((p[0]-a[0])*d[0]+(p[1]-a[1])*d[1])/(length*length))))
        cuts=sorted(splits)
        for lo,hi in zip(cuts,cuts[1:]):
            if hi-lo<1e-12:continue
            middle=[a[i]+d[i]*(lo+hi)*.5 for i in range(2)];normal=[-d[1]/length,d[0]/length]
            sides=[any(_inside_ring([middle[i]+sign*normal[i]*.0001 for i in range(2)],p)for p in polygons)for sign in (-1,1)]
            if sides[0]!=sides[1]:boundary.append(([a[i]+lo*d[i]for i in range(2)],[a[i]+hi*d[i]for i in range(2)]))
    require(boundary,'Natural lawn managed union has no external boundary')
    return boundary


def _managed_domain(plan):
    pin=plan['managedLawnPlan'];actual=pinned(pin['path'],pin['sha256'])
    require(plan['inputFiles'].get(str(actual)) == pin['sha256'], 'Natural lawn managed plan input pin missing')
    source=json.loads(actual.read_text());metadata=source['metadata'];polygons=source['managedLawnKeepPolygonsCm']
    require(metadata['activeDesign'] == plan['activeDesign'] and metadata['housePlacement'] == plan['housePlacement']
            and metadata['sourceObjSha256'] == plan['sourceObjSha256']
            and polygons == plan['managedLawnKeepPolygonsCm'] and polygons
            and all(len(p)>=3 and all(finite(v,2) for v in p)for p in polygons), 'Natural lawn managed source frame/domain differs')
    original_pin=plan['derivedFrom'];original_path=pinned(original_pin['path'],original_pin['sha256'])
    require(plan['inputFiles'].get(str(original_path)) == original_pin['sha256'], 'Natural lawn original plan input pin missing')
    original=json.loads(original_path.read_text())
    require(original['owner'] == GENERATOR and original['sourceSceneSha256'] == plan['sourceSceneSha256']
            and original['sourceObjSha256'] == plan['sourceObjSha256']
            and original['lawnDomainSourceMm'] == plan['sourceLawnDomainSourceMm'], 'Natural lawn managed source domain differs')
    return polygons,_union_boundary(polygons)


def _polygon_area(geometry):
    polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
    def area(ring):
        return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]+ring[:1])))*.5
    return sum(area(p[0])-sum(area(h) for h in p[1:]) for p in polygons)


def _managed_area(plan, polygons_cm):
    """Independent ring clipping against the two non-overlapping keep rectangles."""
    source = json.loads(plan['sourceLawnDomainSourceMm'])
    polygons = [source['coordinates']] if source['type'] == 'Polygon' else source['coordinates']
    total = 0.
    for keep in polygons_cm:
        xs=[p[0]*10 for p in keep];ys=[-p[1]*10 for p in keep]
        bounds=(min(xs),min(ys),max(xs),max(ys))
        require({tuple(p) for p in keep} == {(min(xs)/10,-min(ys)/10),(min(xs)/10,-max(ys)/10),
                (max(xs)/10,-min(ys)/10),(max(xs)/10,-max(ys)/10)}, 'Natural lawn managed rectangles differ')
        for polygon in polygons:
            areas=[]
            for ring in polygon:
                clipped=ring[:-1] if ring[0]==ring[-1] else ring[:]
                for axis,edge,greater in ((0,bounds[0],True),(0,bounds[2],False),(1,bounds[1],True),(1,bounds[3],False)):
                    points=[]
                    for a,b in zip(clipped,clipped[1:]+clipped[:1]):
                        ai=a[axis]>=edge if greater else a[axis]<=edge
                        bi=b[axis]>=edge if greater else b[axis]<=edge
                        if ai:points.append(a)
                        if ai!=bi:
                            t=(edge-a[axis])/(b[axis]-a[axis]);points.append([a[i]+t*(b[i]-a[i])for i in range(2)])
                    clipped=points
                areas.append(_polygon_area({'type':'Polygon','coordinates':[clipped]}) if clipped else 0.)
            total+=areas[0]-sum(areas[1:])
    return total/1e6


def _upright_morphology(plan, meshes, decoded):
    """Owner-specific actual pointed leaf surfaces; no scientific Python runtime."""
    directory = Path(plan['geometryManifest']['path']).parent
    bundle = json.loads((directory/'lawn-natural-manifest.json').read_text())
    proof_pin = bundle.get('geometryProof', {})
    records = json.loads(pinned(proof_pin['path'], proof_pin['sha256']).read_text())
    require(len(records) == 60 and {r['nodeName'] for r in records} == set(decoded),
            'Upright lawn morphology proof inventory differs')
    lookup = {r['nodeName']: r for r in records}; normal_z = []
    def subtract(a, b): return [a[i]-b[i] for i in range(3)]
    def dot(a, b): return sum(x*y for x,y in zip(a,b))
    def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    for key, mesh in meshes.items():
        reference = decoded[key+'_LOD0']; edge = mesh['edgeMaster']; count = 48 if edge else 64
        require([l['triangles'] for l in mesh['lods']] == [count*3]*3,
                'Upright lawn actual three-panel leaf topology differs')
        for lod in mesh['lods']:
            actual = decoded[lod['nodeName']]; record = lookup[lod['nodeName']]; points = actual['positions']
            require(record['edgeMaster'] is edge and record['growthClass'] == mesh['growthClass']
                    and record['level'] == lod['level'] and len(record['bladeRanges']) == count
                    and len(points) == count*5 and len(record['positionsCm']) == len(points)
                    and all(finite(q,3) and max(abs(a-b) for a,b in zip(p,q)) < .00002
                            for p,q in zip(points,record['positionsCm'])), 'Upright lawn actual geometry/proof differs')
            require(all(actual[field] == reference[field] for field in
                    ('positions','indices','normals','tangents','uv0','uv1','colors')),
                    'Upright lawn allLOD leaf geometry was changed, widened or effaced')
            faces = [(a,c,b) for a,b,c in zip(actual['indices'][::3],actual['indices'][1::3],actual['indices'][2::3])]
            require(faces == [tuple(r) for r in record['triangles']], 'Upright lawn actual triangle proof differs')
            for p,n,t,uv,color in zip(points,actual['normals'],actual['tangents'],actual['uv0'],actual['colors']):
                require(abs(dot(n,n)-1)<.00001 and abs(dot(t[:3],t[:3])-1)<.00001
                        and abs(dot(n,t[:3]))<.00001 and abs(abs(t[3])-1)<.00001
                        and all(0<=v<=1 for v in uv) and all(0<=v<=1 for v in color) and color[3] == 1.,
                        'Upright lawn actual normal/tangent/UV/color frame differs')
            for face in faces:
                p,q,r = [points[i] for i in face]; geometric = cross(subtract(q,p),subtract(r,p)); length = math.sqrt(dot(geometric,geometric))
                average = [sum(actual['normals'][i][k] for i in face)/3 for k in range(3)]
                require(length>1e-9 and dot(geometric,average)>0, 'Upright lawn actual degenerate/opposed leaf faces')
                normal_z.append(abs(geometric[2]/length))
            for index, blade in enumerate(record['bladeRanges']):
                start = index*5; low = index%4 == 0
                require(blade['bladeIndex'] == index and blade['vertexOffset'] == start and blade['vertexCount'] == 5
                        and blade['triangleOffset'] == index*3 and blade['triangleCount'] == 3
                        and blade['segments'] == 2 and blade['low'] is low and blade['clipped'] is False
                        and blade['pointedTip'] is True and blade['lodProjectedAreaWidthScale'] == 1.,
                        'Upright lawn pointed anatomy/low-share proof differs')
                expected = [(start,start+1,start+2),(start+1,start+3,start+2),(start+2,start+3,start+4)]
                require(faces[index*3:index*3+3] == expected,
                        'Upright lawn actual leaf components/topology differ')
                base = [(points[start][k]+points[start+1][k])*.5 for k in range(3)]
                shoulder = [(points[start+2][k]+points[start+3][k])*.5 for k in range(3)]; tip = points[start+4]
                width = math.dist(points[start+2], points[start+3]); root_width = math.dist(points[start],points[start+1])
                reach = math.dist(base[:2],tip[:2]); height = (tip[2]-base[2])/.975
                lo,hi = ((.40,.63) if key.endswith('_0') else (1.30,1.85)) if edge else (1.50,2.)
                require(.25-.00002<=width<=.40+.00002 and abs(width-blade['widthCm'])<.00002
                        and abs(root_width-.82*width)<.00002 and lo-.00002<=reach<=hi+.00002
                        and abs(reach-blade['reachCm'])<.00002
                        and (3. if low else 3.8)-.00002<=height<=(4.1 if low else 5.85)+.00002
                        and abs(height-blade['heightCm'])<.00002
                        and max(abs(base[k]-blade['rootCm'][k]) for k in range(2))<.00002,
                        'Upright lawn decoded physical width/height/reach/root differs')
                for actual_center,declared in zip((base,shoulder,tip),blade['centerlineCm']):
                    require(finite(declared,3) and math.dist(actual_center,declared)<.00003,
                            'Upright lawn actual curved centerline proof differs')
                require(math.dist(shoulder,[base[k]+.78*(tip[k]-base[k]) for k in range(3)])>.04,
                        'Upright lawn actual leaf has no curvature')
                expected_uv = [(0.,0.),(1.,0.),(0.,.78),(1.,.78),(.5,1.)]
                require(all(max(abs(a-b) for a,b in zip(got,want))<.000001
                            for got,want in zip(actual['uv0'][start:start+5],expected_uv)),
                        'Upright lawn actual tip UV/topology differs')
    normal_z.sort(); median = normal_z[len(normal_z)//2]; mean = sum(normal_z)/len(normal_z)
    require(median<.45 and math.sqrt(sum((n-mean)**2 for n in normal_z)/len(normal_z))>.15,
            'Upright lawn actual surfaces are flat or have uniform normals')
    audit = plan['audit']
    require(audit['instances']==102011 and audit['groups']==40 and audit['edgeInstances']==21144
            and audit['interiorCoverageTargetsMet'] is True and audit['boundaryCoverageTargetsMet'] is True
            and all(audit[k] is False for k in ('nativeAppearanceAccepted','fullPhotorealismAccepted','integrationAuthorized')),
            'Upright lawn final source population/acceptance differs')
    old = audit['legacyLawnProof']; geometry,rows,pin,expected = _trimmed_legacy_placement(
        json.loads((ROOT/'output/unreal/realism-20260926-r5/photoreal-import-report.json').read_text()),
        json.loads((ROOT/'output/unreal/realism-20260926-r5/rural-import-report.json').read_text()),
        json.loads(pinned(old['plan']['path'],old['plan']['sha256']).read_text()))
    inspection = json.loads(pinned(old['inspection']['path'],old['inspection']['sha256']).read_text())
    require(inspection['contentUnchanged'] is True and inspection['nativeLawnInstanceCount']==40437
            and all(old[k]==expected[k] for k in expected) and old['nativeMutationPerformed'] is False,
            'Upright lawn original source/40437 trim proof differs')
    witnesses = {r['actor']:r for r in inspection['taggedLawnActors']}
    require(all(digest(_rural_values(witnesses[geometry['groups'][k]['actor']]['orderedInstanceTransforms']))
                ==expected['groups'][k]['transformsSha256'] for k in LEGACY_GROUPS),
            'Upright lawn actual old donor ordered identity differs')


def _coverage_claims(plan, meshes, decoded, managed):
    """Measure inexpensive native geometry/density claims; pixel raster stays external."""
    audit=plan['audit'];rows=plan['lawnPlacements'];areas={};triangles=[];vertices=0
    upright=plan['owner']==UPRIGHT_GENERATOR
    fine=plan['owner'] in (FINE_GENERATOR,UPRIGHT_GENERATOR)
    leaves,low_leaves=({'interior':64,'boundary':48},{'interior':16,'boundary':12} if upright else {'interior':48,'boundary':36}) if fine else (36,24)
    require(audit['leavesPerPatchEveryLod']==leaves and audit['lowLeaningLeavesPerPatch']==low_leaves
            and audit['managedLawnKeepPolygonsPreserved'] is True and audit['nativeVerified'] is False,
            'Natural lawn coverage policy differs')
    for key,mesh in meshes.items():
        expected_leaves=(48 if mesh['edgeMaster'] else 64) if fine else 36
        projected=[]
        for lod in mesh['lods']:
            measured=decoded[lod['nodeName']];points=measured['positions'];indices=measured['indices'];vertices+=len(points)
            parents=list(range(len(points)))
            def find(i):
                while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
                return i
            area=0.
            for offset in range(0,len(indices),3):
                a,b,c=indices[offset:offset+3];parents[find(b)]=find(a);parents[find(c)]=find(a)
                p,q,r=points[a],points[b],points[c]
                area+=abs((q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0]))*.5
            require(len({find(i)for i in range(len(points))})==lod.get('blades')==expected_leaves
                    and lod.get('minimumCurveSegments') in ((2,3) if fine else (2,)) and area>0,
                    'Natural lawn decoded leaf inventory/coverage differs')
            projected.append(area)
        require(all(.80<area/projected[0]<1.25 for area in projected[1:]), 'Natural lawn LOD projected coverage lost')
        areas[key]=projected
    for level in range(3):triangles.append(sum(meshes[r['meshId']]['lods'][level]['triangles'] for r in rows))
    require(triangles==audit['allInstancesTriangleBudgetByLod'] and triangles[0]==audit['nearTriangleBudget']<=20000000
            and vertices==audit['allLodGeometryVertices']
            and sum(d['triangles'] for d in decoded.values())==audit['allLodGeometryTriangles'],
            'Natural lawn measured LOD triangle budget differs')
    area=_polygon_area(json.loads(plan['lawnDomainSourceMm']))/1e6
    actual_area=_managed_area(plan,managed[0])
    full_area=_polygon_area(json.loads(plan['sourceLawnDomainSourceMm']))/1e6
    require(abs(area-actual_area)<1e-7 and abs(area-audit['exactAllowedDomainM2'])<1e-7
            and abs(full_area-audit['fullSourceLawnM2'])<1e-7
            and abs(full_area-area-audit['unmanagedSourceLawnExcludedM2'])<1e-7,
            'Natural lawn measured managed area/density differs')
    leaf_count=sum(meshes[r['meshId']]['lods'][0]['blades']for r in rows) if fine else 36*len(rows)
    require(abs(audit['densityPatchesPerM2']-len(rows)/area)<1e-9
            and abs(audit['bladesPerM2EveryLod']-leaf_count/area)<1e-8,
            'Natural lawn measured physical blade density differs')
    scales=[r['scale'][0] for r in rows];mean=sum(scales)/len(scales)
    sigma=math.sqrt(sum((s-mean)**2 for s in scales)/len(scales))
    require(all(abs(a-b)<1e-9 for a,b in zip([min(scales),max(scales)],audit['heightScaleRange']))
            and abs(sigma-audit['heightScaleStandardDeviation'])<1e-9, 'Natural lawn measured scale density differs')
    amplitudes=[abs(sum(complex(math.cos(r['positionCm'][axis]*10*math.tau/60),
                math.sin(r['positionCm'][axis]*10*math.tau/60))for r in rows)/len(rows))for axis in range(2)]
    require(all(abs(a-b)<1e-9 for a,b in zip(amplitudes,audit['sixtyMmLatticePhaseAmplitudeXY'])),
            'Natural lawn measured spatial density differs')
    if fine:
        interior=[r for r in rows if not r['edge']]
        phases=[abs(sum(complex(math.cos(r['positionCm'][axis]*10*math.tau/60),
                    math.sin(r['positionCm'][axis]*10*math.tau/60))for r in interior)/len(interior))for axis in range(2)]
        require(max(phases)<.025 and all(abs(a-b)<1e-9 for a,b in zip(phases,audit['interiorSixtyMmLatticePhaseAmplitudeXY'])),
                'Fine lawn interior repeats a source grid or phase proof differs')
    # The standalone high-resolution raster is pinned independently of claims
    # embedded in the plan; embedded Python does not need PIL/NumPy/Shapely.
    directory=Path(plan['geometryManifest']['path']).parent
    bundle=json.loads((directory/'lawn-natural-manifest.json').read_text())
    actual_geometry=json.loads(pinned(plan['geometryManifest']['path'],plan['geometryManifest']['sha256']).read_text())
    require(plan['coverageReceipt']==actual_geometry.get('coverageReceipt')==bundle['coverageReceipt'],
            'Natural lawn coverage receipt pin differs')
    require(bundle['plan']['sha256']==sha(bundle['plan']['path']) and digest(json.loads(Path(bundle['plan']['path']).read_text()))==digest(plan)
            and bundle['geometryManifest']==plan['geometryManifest'], 'Natural lawn coverage bundle plan pin differs')
    receipt=json.loads(pinned(bundle['coverageReceipt']['path'],bundle['coverageReceipt']['sha256']).read_text())
    receipt_status='MEASURED_UPRIGHT_STUDY_COVERAGE_NOT_NATIVE_ACCEPTED' if upright else 'PASS_STATIC_PHYSICAL_COVERAGE_NOT_NATIVE_ACCEPTED'
    criteria={'minimumTopViewCoverage':.75,'preferredTopViewCoverage':.80,'minimumTenCmBinP10':.55,'maximumPermittedBladeLossAcrossLods':0} if upright else {
        'minimumTopViewCoverage':.70,'minimumTenCmBinP10':.55,'maximumPermittedBladeLossAcrossLods':0}
    require(receipt==audit['physicalCoverage'] and receipt['status']==receipt_status and receipt['criteria']==criteria,
            'Natural lawn pinned physical coverage receipt differs')
    require(len(receipt['windows'])==4,'Natural lawn coverage sample inventory differs')
    for window in receipt['windows']:
        require(window['resolution']==4000 and window['sizeCm']==100 and finite(window['centerCm'],2)
                and [r['lod']for r in window['lods']]==[0,1,2], 'Natural lawn fine coverage sample differs')
        for lod in window['lods']:
            require((.75<=lod['projectedCoverage']<=1 if upright else .70<lod['projectedCoverage']<=1) and .55<lod['tenCmBinCoverageP10']<=1
                    and 0<=lod['tenCmBinCoverageMinimum']<=lod['tenCmBinCoverageP10']
                    and lod['bareTenCmBins']==0, 'Natural lawn actual physical coverage criteria failed')
            if upright:require(lod.get('studyTargetsMet') is True,'Upright lawn source coverage target claim differs')
    if fine:
        pin=plan.get('boundaryCoverageReceipt')
        require(pin and pin==actual_geometry.get('boundaryCoverageReceipt')==bundle.get('boundaryCoverageReceipt'),
                'Fine lawn boundary coverage receipt pin differs')
        boundary=json.loads(pinned(pin['path'],pin['sha256']).read_text())
        require(boundary==audit.get('boundaryCoverage') and
                boundary.get('status')==('MEASURED_UPRIGHT_STUDY_BOUNDARY_COVERAGE_NOT_NATIVE_ACCEPTED' if upright else 'PASS_STATIC_BOUNDARY_LEAF_COVERAGE_NOT_NATIVE_ACCEPTED') and
                boundary.get('criteria')=={'minimumPhysicalCoverByBoundaryBand':{'1to10mm':.12,'10to30mm':.40,'30to100mm':.50},
                    'outsideSourceDomainPermittedCm':0},'Fine lawn boundary coverage policy differs')
        windows=boundary.get('windows',[])
        require(len(windows)==2 and [w.get('boundaryId')for w in windows]==['deck','mulch'],
                'Fine lawn boundary sample inventory differs')
        source=json.loads(plan['lawnDomainSourceMm'])
        polygons=[source['coordinates']] if source['type']=='Polygon' else source['coordinates']
        def inside_native(point):
            p=[point[0]*10,-point[1]*10]
            return any(_inside_ring(p,poly[0]) and not any(_inside_ring(p,hole)for hole in poly[1:])for poly in polygons)
        for window,(a,b) in zip(windows,[([-476.,-650.],[-476.,-400.]),([-1124.,-440.],[-1016.,-500.])]):
            length=math.dist(a,b);axis=[(b[i]-a[i])/length for i in range(2)];inward=[-axis[1],axis[0]]
            midpoint=[(a[i]+b[i])*.5 for i in range(2)]
            if not inside_native([midpoint[i]+inward[i]for i in range(2)]):inward=[-v for v in inward]
            require(window.get('originCm')==a and finite(window.get('axisUnitXY'),2) and finite(window.get('inwardUnitXY'),2)
                    and all(abs(x-y)<1e-9 for x,y in zip(window['axisUnitXY'],axis))
                    and all(abs(x-y)<1e-9 for x,y in zip(window['inwardUnitXY'],inward))
                    and window.get('widthCm')==40. and abs(window.get('lengthCm',0)-length)<1e-9
                    and window.get('pixelSizeMm')==.25 and window.get('resolutionXY')==[1600,math.ceil(length/.025)],
                    'Fine lawn boundary frame/resolution differs')
            require(isinstance(window.get('intersectingInstances'),int) and window['intersectingInstances']>0 and
                    [r.get('lod')for r in window.get('lods',[])]==[0,1,2], 'Fine lawn boundary raster inventory differs')
            for lod in window['lods']:
                bands=lod.get('boundaryBands',[])
                require(0<=lod.get('projectedCoverage',-1)<=1 and len(bands)==3,
                        'Fine lawn boundary coverage values differ')
                for band,distances,minimum in zip(bands,[[1.,10.],[10.,30.],[30.,100.]],[.12,.40,.50]):
                    require(band.get('distanceFromBoundaryMm')==distances and
                            minimum<band.get('physicalCoverFraction',-1)<=1,'Fine lawn boundary leaf cover failed')
                if upright:require(lod.get('studyTargetsMet') is True,'Upright lawn source boundary target claim differs')


def validated_groups(plan, manifest, sceneSha, objSha):
    """Validate the pinned natural geometry manifest and return HISM groups.

    ``manifest`` is the natural library's geometry-manifest.json, before merging
    it into the full exterior library. Decoded GLB envelopes are measured again.
    Source masks are independently read; no Shapely/NumPy/Unreal is required.
    """
    for record in (plan, manifest):
        owner=record.get('owner')
        require(record.get('schemaVersion') == 1 and owner in (GENERATOR,*MANAGED_OWNERS),
                'Natural lawn generator/schema differs')
        require(record.get('activeDesign') == {'variant':'C','heatingLayout':'B','livingLayout':'B'}
                and record['housePlacement']['streetSetbackMm'] == record['housePlacement']['eastSetbackMm'] == 3000,
                'Natural lawn C/B/B or setbacks differ')
        require(record.get('sourceSceneSha256') == sceneSha and record.get('sourceObjSha256') == objSha,
                'Natural lawn source frame differs')
        require(record['generatorSha256'] == sha(ROOT/owner)
                and record['inputFiles'].get(str(ROOT/owner)) == record['generatorSha256'], 'Natural lawn generator pin differs')
        require(all(str(ROOT/'scripts/unreal'/name) in record['inputFiles'] for name in
                ('lawn-geometry.py','vegetation.py','performance_scene_policy.py')),
                'Natural lawn mandatory source policy pin missing')
        for path, value in record['inputFiles'].items(): pinned(path, value)
    require(plan['inputFiles'] == manifest['inputFiles'], 'Natural lawn source dependencies differ')
    require(plan['owner'] == manifest['owner'], 'Natural lawn generator ownership differs')
    actual_manifest = json.loads(pinned(**{'path':plan['geometryManifest']['path'], 'expected':plan['geometryManifest']['sha256']}).read_text())
    require(digest(actual_manifest) == digest(manifest), 'Natural lawn geometry manifest differs from plan pin')
    require(plan.get('kind') == 'authored-natural-lawn-replacement' and plan['sourceLawnId'] == 'DOM_00001'
            and plan['sourceLawnMaterial'] == 'MAT_0001' and plan['sourceElevationMm'] == -65
            and plan['sourceTriangleCount'] == 27 and plan['lodScreenSizes'] == SCREENS, 'Natural lawn source/LOD scope differs')
    require(plan['renderingPolicy'] == {'collision':'none','navigation':False,'windDisplacementCm':0,
            'qualityDetail':True,'densityScaling':True,'cullStartCm':3200,'cullEndCm':4000,
            'savedCastShadow':False,'savedVisibleInRayTracing':False}, 'Natural lawn render policy differs')
    replacement={'hideOnlyVerifiedInheritedLawnActors':True,'inheritedLawnTag':LEGACY_TAG,
            'inheritedLawnGroups':list(LEGACY_GROUPS),'sourceGroundAndCollisionUnchanged':True,'architectureUnchanged':True,
            'sharedOldBladeAssetsUnchanged':True,'meadowYardAndGardenUntouched':True}
    if plan['owner'] in MANAGED_OWNERS:replacement.update(managedOnly=True,completeCrownsInsideManagedKeep=True,unmanagedRuralGroundcoverPreserved=True)
    require(plan['replacementPolicy'] == replacement,'Natural lawn replacement scope differs')
    meshes = {m['id']:m for m in manifest['meshes']}
    require(len(meshes) == len(manifest['meshes']) == 20 and set(meshes) == FAMILY, 'Natural lawn mesh family differs')
    glbs = {(m['glbPath'],m['glbSha256']) for m in meshes.values()}
    require(len(glbs) == 1, 'Natural lawn GLB source is ambiguous')
    path, value = next(iter(glbs)); decoded = _glb_geometry(pinned(path, value), include_frames=plan['owner']==UPRIGHT_GENERATOR); envelopes = {}
    require(set(decoded) == {key+'_LOD'+str(i) for key in FAMILY for i in range(3)}, 'Natural lawn decoded LOD inventory differs')
    for key, mesh in meshes.items():
        require(mesh['role'] == 'grass' and mesh['placementPolicy'] == 'explicit-only'
                and mesh['materialKeys'] == ['lawn_natural_blade'] and mesh['lodScreenSizes'] == SCREENS
                and [lod['level'] for lod in mesh['lods']] == [0,1,2], 'Natural lawn mesh/LOD override differs')
        all_positions = []
        for lod in mesh['lods']:
            require(lod['nodeName'] == key+'_LOD'+str(lod['level']), 'Natural lawn LOD node identity differs')
            measured = decoded[lod['nodeName']]; positions = measured['positions']; all_positions.extend(positions)
            require(len(positions) == lod['vertices'] and measured['triangles'] == lod['triangles'], 'Natural lawn decoded vertex/triangle count differs')
            bounds = {name:[function(p[i] for p in positions) for i in range(3)] for name,function in [('min',min),('max',max)]}
            require(all(abs(bounds[name][i]-lod['expectedBoundsCm'][name][i]) < .00002 for name in bounds for i in range(3)), 'Natural lawn decoded bounds differ')
            radius = max(math.hypot(p[0],p[1]) for p in positions)
            root_valid=(-.01<=bounds['min'][2]<=.00002) if plan['owner']==FINE_GENERATOR else abs(bounds['min'][2])<.00002
            require(abs(radius-lod['radialEnvelopeCm']) < .00002 and root_valid, 'Natural lawn measured crown/root envelope differs')
        radius = max(math.hypot(p[0],p[1]) for p in all_positions); height = max(p[2] for p in all_positions)
        require(abs(height-mesh['heightCm']) < .00002, 'Natural lawn measured height differs')
        envelopes[key] = (radius,height)
    faces, source_edges, exclusions, extra = _source_context(plan)
    managed=_managed_domain(plan) if plan['owner'] in MANAGED_OWNERS else None
    domain = json.loads(plan['lawnDomainSourceMm'])
    require(domain['type'] in ('Polygon','MultiPolygon') and domain['coordinates'], 'Natural lawn domain polygon differs')
    polygons = [domain['coordinates']] if domain['type']=='Polygon' else domain['coordinates']
    rings = [ring for polygon in polygons for ring in polygon]
    require(all(len(ring) >= 4 and ring[0] == ring[-1] and all(finite(p,2) for p in ring) for ring in rings), 'Natural lawn domain rings invalid')
    edges = [(a,b) for ring in rings for a,b in zip(ring,ring[1:])]
    forbidden = [(r['polygonSourceMm'], r['boundsMm']) for r in exclusions]
    expected_status='PASS_STATIC_MANAGED_GEOMETRY_AND_CLEARANCE' if managed else 'PASS_STATIC_GEOMETRY_AND_CLEARANCE'
    if plan['owner'] in COVERAGE_OWNERS:expected_status='PASS_STATIC_CONTINUOUS_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED'
    if plan['owner']==FINE_GENERATOR:expected_status='PASS_STATIC_FINE_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED'
    if plan['owner']==UPRIGHT_GENERATOR:expected_status='MEASURED_UPRIGHT_MANAGED_LAWN_STUDY_NOT_NATIVE_ACCEPTED'
    audit = plan['audit']; require(audit['status'] == expected_status
        and audit['sourceMasksUnchanged'] is True and audit['sourceTriangles'] == 27
        and audit['extraExclusionSourceIds'] == extra and audit['rootElevationCm'] == -6.5,
        'Natural lawn clearance/source audit failed')
    if plan['owner']==UPRIGHT_GENERATOR:
        _upright_morphology(plan,meshes,decoded)
        _coverage_claims(plan,meshes,decoded,managed)
    groups = []; ids = set(); flattened = []; counts = Counter(); edge_count = 0; minimum_clearance = float('inf')
    for group in plan['groups']:
        key = group['meshId']; identity = group['id']
        require(key in meshes and identity.startswith('EX_lawn_natural_') and identity not in ids
                and group['role'] == 'grass' and group['qualityDetail'] is True and group['cullEndCm'] == 4000
                and group['instances'], 'Natural lawn HISM group scope differs')
        ids.add(identity); native_rows = []
        for row in group['instances']:
            p,s,yaw = row['positionCm'],row['scale'],row['yawDeg']
            require(finite(p,3) and finite(s,3) and max(s)-min(s) < 1e-9 and .60 <= s[0] <= 1.25
                    and isinstance(yaw,(int,float)) and not isinstance(yaw,bool) and math.isfinite(yaw) and -180 <= yaw <= 180
                    and p[2] == -6.5, 'Natural lawn placement/scale/elevation invalid')
            require(identity == 'EX_'+key.replace('lawn_natural_',
                    'lawn_natural_'+str(math.floor(p[0]/2000))+'_'+str(math.floor(p[1]/2000))+'_',1),
                    'Natural lawn spatial group identity differs')
            radius,height = envelopes[key]; radius *= s[0]; height *= s[0]
            require(radius <= 20 and abs(radius-row['radiusCm']) < .00005 and abs(height-row['actualHeightCm']) < .00005
                    and abs(row['enclosingRadiusMm']-(10*radius+1)) < .001, 'Natural lawn measured placement envelope differs')
            point = [p[0]*10,-p[1]*10]
            if managed:
                polygons_cm,boundary_cm=managed
                require(any(_inside_ring(p[:2],polygon)for polygon in polygons_cm)
                        and min(_distance(p[:2],a,b)for a,b in boundary_cm) > radius+.1,
                        'Natural lawn entire crown escaped actual managed keep union')
            inside = any(_inside_ring(point,polygon[0]) and not any(_inside_ring(point,hole) for hole in polygon[1:]) for polygon in polygons)
            clearance = min(_distance(point,a,b) for a,b in edges)
            require(inside and clearance > 10*radius+1 and abs(clearance-row['clearanceMm']) < .002, 'Natural lawn full crown escaped declared domain')
            require(any(_inside_triangle(point,t) for t in faces)
                    and min(_distance(point,a,b) for a,b in source_edges) > 10*radius+1,
                    'Natural lawn crown escaped actual source ground')
            for polygon, box in forbidden:
                if point[0]+10*radius+1 < box[0] or point[0]-10*radius-1 > box[2] or point[1]+10*radius+1 < box[1] or point[1]-10*radius-1 > box[3]:continue
                require(not _inside_ring(point,polygon) and min(_distance(point,a,b) for a,b in zip(polygon,polygon[1:]+polygon[:1])) > 10*radius+1,
                        'Natural lawn crown intersects actual source exclusion')
            require(row['edge'] is meshes[key]['edgeMaster'] and row['growthClass'] == meshes[key]['growthClass'], 'Natural lawn growth/edge family differs')
            minimum_clearance = min(minimum_clearance,clearance-row['enclosingRadiusMm'])
            edge_count += int(row['edge']); counts[key] += 1; flattened.append({'meshId':key,**row})
            native_rows.append({'positionCm':list(p),'yawDeg':yaw,'scale':list(s)})
        groups.append({'id':identity,'meshId':key,'role':'grass','cullEndCm':4000,'qualityDetail':True,'instances':native_rows})
    require(flattened == plan['lawnPlacements'] and len(flattened) == audit['instances'] and len(groups) == audit['groups']
            and edge_count == audit['edgeInstances'] and dict(counts) == audit['perMesh'], 'Natural lawn placement/audit inventory differs')
    require(abs(minimum_clearance-audit['minimumAdditionalCrownClearanceMm']) < .002, 'Natural lawn actual minimum crown clearance differs')
    if plan['owner'] in COVERAGE_OWNERS and plan['owner']!=UPRIGHT_GENERATOR:_coverage_claims(plan,meshes,decoded,managed)
    return groups


def _legacy_placement(report):
    lawn = report['lawn']; geometry = lawn['geometry']; inputs = geometry['inputFiles']
    require(lawn['sourceGroundRetained'] is True and lawn['savedReloaded'] is True
            and geometry['owner'] == 'scripts/unreal/lawn-geometry.py' and geometry['sourceUnchanged'] is True
            and geometry['nativeImportVerified'] is True and geometry['savedReloaded'] is True
            and geometry['instanceCount'] == 98344 and geometry['hismComponents'] == 4
            and geometry['collision'] == 'NoCollision' and geometry['lodScreenSizes'] == SCREENS
            and geometry['material'] == LEGACY_MATERIAL and set(geometry['groups']) == set(LEGACY_GROUPS), 'Inherited lawn receipt scope differs')
    candidates = [p for p,h in inputs.items() if p.endswith('/lawn-geometry/geometry-report.json') and h == geometry['geometryReportSha256']]
    require(len(candidates) == 1, 'Inherited lawn geometry receipt is ambiguous')
    receipt = pinned(candidates[0],geometry['geometryReportSha256']); placement = receipt.parent/'placement.json'
    key = str(placement.relative_to(ROOT)); require(key in inputs or str(placement) in inputs, 'Inherited lawn placement pin missing')
    expected = inputs.get(key,inputs.get(str(placement))); pinned(placement,expected)
    rows = json.loads(placement.read_text()); groups = {g['id']:g for g in rows['groups']}
    require(len(groups) == 4 and set(groups) == set(LEGACY_GROUPS)
            and rows['instanceCount'] == geometry['instanceCount'] == sum(len(g['instances']) for g in groups.values()),
            'Inherited lawn placement inventory differs')
    return geometry,groups,{'path':str(placement),'sha256':expected}


def _rural_values(values):
    return [{'translation':v['p'],'rotation':v['q'],'scale3d':v['s']} for v in values]


def _trimmed_legacy_placement(report,rural_report,rural_plan):
    """Reconstruct the later rural trim from the original pinned placement.

    Photoreal import receipts describe the earlier full lawn. The inherited map
    uses the subsequent rural import's explicitly selected, ordered subset.
    """
    geometry,original,placement_pin = _legacy_placement(report)
    require(rural_report.get('owner') == 'scripts/unreal/rural-import.py'
            and rural_report.get('status') == 'rural-import-validated' and rural_report.get('savedReloaded') is True
            and rural_report.get('protectedBaselineAssetsUnchanged') is True and rural_report.get('sourceCollisionPreserved') is True
            and rural_report.get('activeDesign') == {'variant':'C','heatingLayout':'B','livingLayout':'B'}
            and rural_report.get('setbacksMm') == {'street':3000,'right':3000}, 'Inherited rural trim receipt scope differs')
    inputs=rural_report['inputFiles']
    plans=[(p,h) for p,h in inputs.items() if p.endswith('/geometry/rural-context-geometry.json')]
    photos=[(p,h) for p,h in inputs.items() if p.endswith('/photoreal-import-report.json')]
    require(len(plans)==len(photos)==1,'Inherited rural trim source pins ambiguous')
    plan_path=pinned(*plans[0]);photo_path=pinned(*photos[0])
    require(digest(json.loads(plan_path.read_text())) == digest(rural_plan)
            and digest(json.loads(photo_path.read_text())) == digest(report),'Inherited rural trim plan/photoreal pin differs')
    historical_report=plan_path.parent.parent/'rural-import-report.json'
    require(historical_report.is_file() and digest(json.loads(historical_report.read_text())) == digest(rural_report),
            'Inherited rural trim differs from historical saved receipt')
    metadata=rural_plan['metadata'];trim=rural_report['managedLawn'];polygons=rural_plan['managedLawnKeepPolygonsCm']
    require(metadata['activeDesign'] == rural_report['activeDesign']
            and metadata['housePlacement']['streetSetbackMm'] == metadata['housePlacement']['eastSetbackMm'] == 3000
            and metadata['sourceObjSha256'] == 'a86c83e68e14898fdeb3fd071c24a6bb82d3a6d0e61f52d8e9a757bce4a2634d'
            and polygons == trim['keepPolygonsCm'] and polygons
            and all(len(p)>=3 and all(finite(v,2) for v in p) for p in polygons), 'Inherited rural trim frame/domain differs')
    require(set(trim['groups']) == {geometry['groups'][key]['actor'] for key in LEGACY_GROUPS},
            'Inherited rural trim actor inventory differs')
    selected={};group_proof={}
    for key in LEGACY_GROUPS:
        before=original[key]['instances'];entry=trim['groups'][geometry['groups'][key]['actor']]
        keep=[row for row in before if any(_inside_ring(row['positionUnrealCm'][:2],p) for p in polygons)]
        require(entry['sourceInstanceOrderPreserved'] is True
                and entry['before'] == geometry['groups'][key]['instances'] == len(before)
                and entry['kept'] == len(keep) > 0 and entry['removed'] == len(before)-len(keep)
                and entry['maximumReinsertPositionErrorCm'] < .002 and entry['maximumReinsertScaleError'] < 2e-6
                and entry['maximumReinsertQuaternionError'] < 2e-5, 'Inherited rural ordered trim membership differs')
        require(all(isinstance(entry[k],str) and len(entry[k])==64 and all(c in '0123456789abcdef' for c in entry[k])
                for k in ('transformsSha256','originalSelectedTransformsSha256')), 'Inherited rural trim native transform pin missing')
        selected[key]={'id':key,'instances':keep};group_proof[key]=entry
    require(sum(len(g['instances']) for g in selected.values()) == trim['retained'] == 40437
            and sum(e['removed'] for e in group_proof.values()) == trim['removed'] == 57907,
            'Inherited rural trim total inventory differs')
    proof={'report':{'path':str(historical_report),'sha256':sha(historical_report)},
           'plan':{'path':str(plan_path),'sha256':plans[0][1]},'groups':group_proof,
           'originalInstances':98344,'retainedInstances':40437,'removedByHistoricalRuralImport':57907,
           'membership':'ordered-source-placement-subset-of-pinned-rural-keep-polygons'}
    return geometry,selected,placement_pin,proof


def _vec(value, axes='xyz'):
    return [float(getattr(value,k)) for k in axes]


def _transform(value):
    if isinstance(value,tuple):
        require(len(value) == 2 and value[0] is True, 'Cannot read inherited lawn transform'); value = value[1]
    result = {'p':_vec(value.translation),'q':_vec(value.rotation,'xyzw'),'s':_vec(value.scale3d)}
    require(all(finite(v,len(v)) for v in result.values()), 'Inherited lawn transform is non-finite')
    return result


def _preserved(u,actor,component):
    mesh = component.get_editor_property('static_mesh')
    values = [_transform(component.get_instance_transform(i,False)) for i in range(component.get_instance_count())]
    return {'mesh':mesh.get_path_name(),'material':component.get_material(0).get_path_name(),
            'instanceCount':len(values),'orderedInstanceTransformsSha256':digest(values),
            'actorTransform':_transform(actor.get_actor_transform()),'componentWorldTransform':_transform(component.get_world_transform()),
            'collision':str(component.get_collision_enabled()),'collisionProfile':str(component.get_collision_profile_name()),
            'cullDistancesCm':[int(component.get_editor_property(k)) for k in ('instance_start_cull_distance','instance_end_cull_distance')],
            'navigation':bool(component.get_editor_property('can_ever_affect_navigation')),
            'overlap':bool(component.get_editor_property('generate_overlap_events')),
            'actorTick':bool(actor.is_actor_tick_enabled()),'componentTick':bool(component.is_component_tick_enabled())}, values


def hide_original_lawn(u,actors,source_photoreal_report,source_rural_report,source_rural_plan):
    """Preflight every identity/transform, then hide only four inherited HISMs."""
    geometry,placements,placement_pin,trim_proof = _trimmed_legacy_placement(source_photoreal_report,source_rural_report,source_rural_plan)
    lookup = {a.get_path_name():a for a in actors.get_all_level_actors()}
    wanted = {geometry['groups'][key]['actor'] for key in LEGACY_GROUPS}
    require(len(wanted) == 4 and {p for p,a in lookup.items() if a.actor_has_tag(LEGACY_TAG)} == wanted, 'Inherited lawn actor/tag inventory differs')
    checked = []
    identity = {'p':[0.,0.,0.],'q':[0.,0.,0.,1.],'s':[1.,1.,1.]}
    for variant,key in enumerate(LEGACY_GROUPS):
        receipt = geometry['groups'][key]; actor = lookup[receipt['actor']]
        component = actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(component is not None and isinstance(component,u.HierarchicalInstancedStaticMeshComponent)
                and actor.get_editor_property('instances') == component and actor.root_component == component
                and component.get_owner() == actor and actor.actor_has_tag('BreziPhotorealSource:DOM_00001'),
                'Inherited lawn actor/component identity differs')
        mesh = component.get_editor_property('static_mesh')
        expected_mesh = '/Game/Brezi/Photoreal/Lawn/Meshes/lawn-prototypes/StaticMeshes/'+key+'_LOD0.'+key+'_LOD0'
        require(receipt['variant'] == variant and receipt['mesh'] == expected_mesh and mesh is not None
                and mesh.get_path_name() == expected_mesh and component.get_num_materials() == 1
                and component.get_material(0).get_path_name() == mesh.get_material(0).get_path_name() == LEGACY_MATERIAL,
                'Inherited lawn mesh/material identity differs')
        rows = placements[key]['instances']
        trim_entry=trim_proof['groups'][key]
        require(trim_entry['kept'] == len(rows) == component.get_instance_count(), 'Inherited trimmed lawn instance count differs')
        preserved,values = _preserved(u,actor,component)
        require(actor.get_path_name()+'/'+component.get_name() == trim_entry['component']
                and digest(_rural_values(values)) == trim_entry['transformsSha256'],
                'Inherited trimmed lawn native ordered transform pin differs')
        require(preserved['actorTransform'] == preserved['componentWorldTransform'] == identity
                and component.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION and preserved['collisionProfile'] == 'NoCollision'
                and not preserved['navigation'] and not preserved['overlap'], 'Inherited lawn transform/collision identity differs')
        for actual,row in zip(values,rows):
            angle = math.radians(row['yawDegreesUnreal'])/2; target = [0.,0.,math.sin(angle),math.cos(angle)]
            require(max(abs(a-b) for a,b in zip(actual['p'],row['positionUnrealCm'])) < .002
                    and max(abs(a-b) for a,b in zip(actual['s'],row['scale'])) < 2e-6
                    and min(max(abs(a-sign*b) for a,b in zip(actual['q'],target)) for sign in (1,-1)) < 2e-5,
                    'Inherited lawn instance transform identity differs')
        require(component.is_visible() and not component.get_editor_property('hidden_in_game'), 'Inherited lawn already hidden')
        checked.append((actor,component,{'actor':actor.get_path_name(),'component':component.get_path_name(),
            'reason':'replace-verified-photoreal-lawn-with-natural-curved-blades','legacyLawnGroup':key,
            'preserved':preserved,'sourcePlacement':placement_pin,
            'sourceRuralTrim':{'report':trim_proof['report'],'plan':trim_proof['plan'],
                'group':trim_entry,'membership':trim_proof['membership']},
            'detailDensityScalingBefore':bool(actor.get_detail_density_scaling()),'detailDensityScalingAfter':False}))
    for actor,component,row in checked:
        require(actor.set_detail_density_scaling(False) and not actor.get_detail_density_scaling(), 'Cannot disable hidden inherited lawn detail scaling')
        component.set_visibility(False,False); component.set_hidden_in_game(True,False)
        for flag in RENDER_FLAGS:component.set_editor_property(flag,False)
    return [row for actor,component,row in checked]


def verify_hidden_lawn(u,actors,changes):
    """Check the saved legacy visibility delta and unchanged native identities."""
    require(len(changes) == 4 and {r['legacyLawnGroup'] for r in changes} == set(LEGACY_GROUPS), 'Hidden inherited lawn receipt inventory differs')
    lookup = {a.get_path_name():a for a in actors.get_all_level_actors()}
    wanted = {r['actor'] for r in changes}
    require(len(wanted) == 4 and {p for p,a in lookup.items() if a.actor_has_tag(LEGACY_TAG)} == wanted, 'Reloaded inherited lawn actor/tag inventory differs')
    total = 0
    for row in changes:
        actor = lookup[row['actor']]; component = actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(component is not None and component.get_path_name() == row['component']
                and isinstance(component,u.HierarchicalInstancedStaticMeshComponent)
                and actor.get_editor_property('instances') == component and actor.root_component == component
                and component.get_owner() == actor and actor.actor_has_tag('BreziPhotorealSource:DOM_00001'),
                'Reloaded inherited lawn component identity differs')
        require(not component.is_visible() and component.get_editor_property('hidden_in_game')
                and all(not component.get_editor_property(flag) for flag in RENDER_FLAGS)
                and not actor.get_detail_density_scaling() and row['detailDensityScalingAfter'] is False,
                'Reloaded hidden inherited lawn render/density flags differ')
        preserved,values = _preserved(u,actor,component)
        require(preserved == row['preserved'] and component.get_editor_property('static_mesh').get_material(0).get_path_name() == LEGACY_MATERIAL
                and component.get_num_materials() == 1, 'Reloaded inherited lawn transforms/material/count/collision changed')
        pinned(row['sourcePlacement']['path'],row['sourcePlacement']['sha256']); total += len(values)
        trim=row['sourceRuralTrim'];pinned(trim['report']['path'],trim['report']['sha256']);pinned(trim['plan']['path'],trim['plan']['sha256'])
        require(digest(_rural_values(values)) == trim['group']['transformsSha256'], 'Reloaded inherited rural trim transforms differ')
    return {'status':'verified-hidden-original-lawn','actors':4,'instances':total,'originalMeshesMaterialsGroundAndCollisionPreserved':True,
            'hiddenDetailDensityScalingDisabled':True}
