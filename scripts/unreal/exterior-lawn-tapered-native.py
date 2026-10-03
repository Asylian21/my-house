"""Strict stdlib validation of the explicit covered-taper lawn successor.

No upright-owner forwarding and no native launch. Source-domain and legacy
visibility helpers are inherited only from an immutable receipt-pinned copy;
new geometry, morphology, source ownership and measured coverage are validated
here independently. Actual native appearance/performance remain unaccepted.
"""
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-lawn-tapered-native.py'
ADAPTER='scripts/unreal/exterior-lawn-tapered-integration.py'
STUDY_OWNER='scripts/unreal/exterior-lawn-tapered-covered.py'
STUDY=ROOT/'output/unreal/exterior-lawn-tapered-20261001-r2-study'
OUTPUT=ROOT/'output/unreal/exterior-lawn-tapered-integration-20261001-r1c'
STUDY_PINS={
    'lawn-tapered-plan.json':'cf128ad92b680969969190f4af5e33c8af8d511a9b016cd0fb1f60d2aad680ed',
    'geometry-manifest.json':'5676858f3f097889cd8895288adb0c9827089888ddbc7bae537625ad752b6fbc',
    'lawn-tapered-manifest.json':'85170be976db6f2331f4b4935a94151bf3a7e0dd7a158f0294cd1b3e9e338e6d',
    'lawn-tapered-prototypes.json':'f356a5a2ff014d5faa4647ac16e610e9b8c751ed3057ba48d95369b99b88c7fd',
    'material-manifest.json':'3612be84eb2f702807ea8b75bd061c71c3bdebd0dace940c8aea4b5cca162d56',
    'tapered-covered.glb':'4f99b430de0c7437dec8a30f4024eb419af8838ea25b8822bd7244c4ae30b2af',
    'geometry-validation.json':'690ad656af8339063e9375cb351286b4b48c0c49ff2696bd28bb8645fcea6e50'}
STUDY_SOURCE_SHA='38b19e99fd78cea3ffae5835d23bb60a6c266416de69a42c72393432badafbf4'
BASE=ROOT/'output/unreal/exterior-lawn-tapered-native-base-20261001-r1/exterior-lawn-native.py'
BASE_SHA='25746802f454aa39f0c590a05c06a23ba8a08c87389f1fe810485372912d3fa5'
POLICY_PINS={'lawn-geometry.py':'bc5bd49c01e880d45022a75ba80a3a3fd971272a86906a7a94d0618df4504d2f',
    'vegetation.py':'03ef25914526be546fd11abdd663e9d1a125c42a3f90972c5e0d13d2059ca60b',
    'performance_scene_policy.py':'5f9eb8ccc2688b7d17200696cd3498558743c60fc541f8b1fbb0e80a3ba94b9e'}
SCREENS=[1.,.025,.007]
FAMILY={f'lawn_natural_{g}_{i}' for g in range(2) for i in range(8)}|{f'lawn_natural_edge_{g}_{i}'for g in range(2)for i in range(2)}
STATUS='MEASURED_TAPERED_MANAGED_LAWN_NOT_NATIVE_ACCEPTED'
COVER_STATUS='MEASURED_TAPERED_LAWN_COVERAGE_NOT_NATIVE_ACCEPTED'
BOUNDARY_STATUS='MEASURED_TAPERED_LAWN_BOUNDARY_COVERAGE_NOT_NATIVE_ACCEPTED'
LEGACY_GROUPS=tuple('LawnTuft'+str(i)for i in range(4))
COVER_CRITERIA={'minimumTopViewCoverage':.75,'preferredTopViewCoverage':.8,'minimumTenCmBinP10':.55,'maximumPermittedBladeLossAcrossLods':0}
BOUNDARY_CRITERIA={'minimumPhysicalCoverByBoundaryBand':{'1to10mm':.12,'10to30mm':.40,'30to100mm':.50},'outsideSourceDomainPermittedCm':0}


def base_module():
    pinned(BASE,BASE_SHA)
    spec=importlib.util.spec_from_file_location('immutable_taper_domain_and_legacy_base',BASE)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.ROOT=ROOT
    return module


def hide_original_lawn(*args,**kwargs):
    return base_module().hide_original_lawn(*args,**kwargs)


def verify_hidden_lawn(*args,**kwargs):
    return base_module().verify_hidden_lawn(*args,**kwargs)

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
            'Tapered lawn input path/hash differs: '+str(path))
    return path

def _glb_geometry(path, include_frames=False):
    raw = Path(path).read_bytes()
    require(len(raw) >= 20 and struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Tapered lawn GLB header differs')
    json_length, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4E4F534A, 'Tapered lawn GLB JSON missing')
    data = json.loads(raw[20:20+json_length])
    require(data.get('asset',{}).get('generator') == STUDY_OWNER and data.get('scene') == 0
            and len(data.get('scenes',[])) == 1 and data['scenes'][0].get('nodes') == list(range(60))
            and len(data.get('nodes',[])) == len(data.get('meshes',[])) == 60
            and not any(k in data for k in ('skins','animations','extensionsUsed','extensionsRequired'))
            and len(data.get('buffers',[])) == len(data.get('materials',[])) == 1
            and not data['buffers'][0].get('uri'), 'Tapered lawn decoded GLB scene/material inventory differs')
    offset = 20+json_length
    binary_length, kind = struct.unpack_from('<II', raw, offset)
    require(kind == 0x004E4942 and offset+8+binary_length == len(raw), 'Tapered lawn GLB binary missing')
    binary = memoryview(raw)[offset+8:]
    result = {}
    for node in data['nodes']:
        require(node['name'] not in result and not any(k in node for k in ('matrix', 'translation', 'rotation', 'scale')),
                'Tapered lawn geometry node transform/name differs')
        primitives = data['meshes'][node['mesh']]['primitives']
        require(len(primitives) == 1 and primitives[0].get('mode', 4) == 4, 'Tapered lawn must use actual triangle geometry')
        primitive = primitives[0]
        require(set(primitive.get('attributes',{})) == {'POSITION','NORMAL','TANGENT','TEXCOORD_0','TEXCOORD_1','COLOR_0'}
                and not any(k in node for k in ('children','skin','weights')) and not primitive.get('targets')
                and primitive.get('material') == 0, 'Tapered lawn foreign/deforming GLB surface rejected')
        accessor = data['accessors'][primitive['attributes']['POSITION']]
        require(accessor['componentType'] == 5126 and accessor['type'] == 'VEC3' and not accessor.get('sparse'),
                'Tapered lawn positions must be ordinary float32')
        require(accessor['count'] > 0, 'Tapered lawn decoded positions are empty')
        view = data['bufferViews'][accessor['bufferView']]
        require(view.get('buffer', 0) == 0, 'Tapered lawn external buffer refused')
        start = view.get('byteOffset', 0)+accessor.get('byteOffset', 0); stride = view.get('byteStride', 12)
        require(stride >= 12 and start+max(0, accessor['count']-1)*stride+12 <= len(binary), 'Tapered lawn position buffer truncated')
        positions = []
        for i in range(accessor['count']):
            x, y, z = struct.unpack_from('<3f', binary, start+i*stride)
            require(finite((x,y,z), 3), 'Tapered lawn decoded position is non-finite')
            positions.append((100*x, 100*z, 100*y))
        indices = data['accessors'][primitive['indices']]
        require(indices['count'] > 0 and indices['count'] % 3 == 0 and indices['type'] == 'SCALAR'
                and indices['componentType'] in (5121,5123,5125) and not indices.get('sparse'),
                'Tapered lawn decoded triangle count/type differs')
        index_view = data['bufferViews'][indices['bufferView']]
        size, fmt = {5121:(1,'B'),5123:(2,'H'),5125:(4,'I')}[indices['componentType']]
        start = index_view.get('byteOffset',0)+indices.get('byteOffset',0)
        require(index_view.get('buffer',0) == 0 and not index_view.get('byteStride')
                and start+indices['count']*size <= len(binary), 'Tapered lawn index buffer differs')
        triangle_indices = struct.unpack_from('<'+fmt*indices['count'],binary,start)
        require(all(index < len(positions) for index in triangle_indices),
                'Tapered lawn actual triangle indices escape vertices')
        require(data['materials'][primitive['material']]['name'] == 'lawn_natural_blade', 'Tapered lawn decoded material family differs')
        result[node['name']] = {'positions':positions, 'triangles':indices['count']//3,
                              'indices': triangle_indices}
        if include_frames:
            def attribute(name, width):
                require(name in primitive['attributes'], 'Tapered lawn actual frame attribute missing: '+name)
                a = data['accessors'][primitive['attributes'][name]]
                require(a['componentType'] == 5126 and a['type'] == 'VEC'+str(width)
                        and a['count'] == len(positions) and not a.get('sparse') and not a.get('normalized'),
                        'Tapered lawn actual frame attribute type/count differs: '+name)
                v = data['bufferViews'][a['bufferView']]; step = v.get('byteStride', width*4)
                beginning = v.get('byteOffset', 0)+a.get('byteOffset', 0)
                require(v.get('buffer', 0) == 0 and step >= width*4 and beginning+(a['count']-1)*step+width*4 <= len(binary),
                        'Tapered lawn actual frame attribute buffer differs: '+name)
                values = [struct.unpack_from('<'+'f'*width, binary, beginning+i*step) for i in range(a['count'])]
                require(all(finite(row, width) for row in values), 'Tapered lawn actual frame attribute non-finite: '+name)
                return values
            normals = attribute('NORMAL', 3); tangents = attribute('TANGENT', 4)
            result[node['name']].update(normals=[(p[0], p[2], p[1]) for p in normals],
                tangents=[(p[0], p[2], p[1], -p[3]) for p in tangents],
                uv0=attribute('TEXCOORD_0', 2), uv1=attribute('TEXCOORD_1', 2), colors=attribute('COLOR_0', 4))
            require(data['materials'][primitive['material']].get('doubleSided') is True,
                    'Tapered lawn actual leaf material must be two-sided')
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



def _polygon_area(geometry):
    polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
    def area(ring):
        return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]+ring[:1])))*.5
    return sum(area(p[0])-sum(area(h) for h in p[1:]) for p in polygons)

def _coverage_claims(plan, meshes, decoded, managed):
    """Measure inexpensive native geometry/density claims; pixel raster stays external."""
    audit=plan['audit'];rows=plan['lawnPlacements'];areas={};triangles=[];vertices=0
    upright=True
    fine=True
    leaves,low_leaves=({'interior':64,'boundary':48},{'interior':16,'boundary':12} if upright else {'interior':48,'boundary':36}) if fine else (36,24)
    require(audit['leavesPerPatchEveryLod']==leaves and audit['lowLeaningLeavesPerPatch']==low_leaves
            and audit['managedLawnKeepPolygonsPreserved'] is True and audit['nativeVerified'] is False,
            'Tapered lawn coverage policy differs')
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
                    'Tapered lawn decoded leaf inventory/coverage differs')
            projected.append(area)
        require(all(.80<area/projected[0]<1.25 for area in projected[1:]), 'Tapered lawn LOD projected coverage lost')
        areas[key]=projected
    for level in range(3):triangles.append(sum(meshes[r['meshId']]['lods'][level]['triangles'] for r in rows))
    require(triangles==audit['allInstancesTriangleBudgetByLod'] and triangles[0]==audit['nearTriangleBudget']<=20000000
            and vertices==audit['allLodGeometryVertices']
            and sum(d['triangles'] for d in decoded.values())==audit['allLodGeometryTriangles'],
            'Tapered lawn measured LOD triangle budget differs')
    area=_polygon_area(json.loads(plan['lawnDomainSourceMm']))/1e6
    actual_area=base_module()._managed_area(plan,managed[0])
    full_area=_polygon_area(json.loads(plan['sourceLawnDomainSourceMm']))/1e6
    require(abs(area-actual_area)<1e-7 and abs(area-audit['exactAllowedDomainM2'])<1e-7
            and abs(full_area-audit['fullSourceLawnM2'])<1e-7
            and abs(full_area-area-audit['unmanagedSourceLawnExcludedM2'])<1e-7,
            'Tapered lawn measured managed area/density differs')
    leaf_count=sum(meshes[r['meshId']]['lods'][0]['blades']for r in rows) if fine else 36*len(rows)
    require(abs(audit['densityPatchesPerM2']-len(rows)/area)<1e-9
            and abs(audit['bladesPerM2EveryLod']-leaf_count/area)<1e-8,
            'Tapered lawn measured physical blade density differs')
    scales=[r['scale'][0] for r in rows];mean=sum(scales)/len(scales)
    sigma=math.sqrt(sum((s-mean)**2 for s in scales)/len(scales))
    require(all(abs(a-b)<1e-9 for a,b in zip([min(scales),max(scales)],audit['heightScaleRange']))
            and abs(sigma-audit['heightScaleStandardDeviation'])<1e-9, 'Tapered lawn measured scale density differs')
    amplitudes=[abs(sum(complex(math.cos(r['positionCm'][axis]*10*math.tau/60),
                math.sin(r['positionCm'][axis]*10*math.tau/60))for r in rows)/len(rows))for axis in range(2)]
    require(all(abs(a-b)<1e-9 for a,b in zip(amplitudes,audit['sixtyMmLatticePhaseAmplitudeXY'])),
            'Tapered lawn measured spatial density differs')
    if fine:
        interior=[r for r in rows if not r['edge']]
        phases=[abs(sum(complex(math.cos(r['positionCm'][axis]*10*math.tau/60),
                    math.sin(r['positionCm'][axis]*10*math.tau/60))for r in interior)/len(interior))for axis in range(2)]
        require(max(phases)<.025 and all(abs(a-b)<1e-9 for a,b in zip(phases,audit['interiorSixtyMmLatticePhaseAmplitudeXY'])),
                'Tapered lawn interior repeats a source grid or phase proof differs')
    # The standalone high-resolution raster is pinned independently of claims
    # embedded in the plan; embedded Python does not need PIL/NumPy/Shapely.
    directory=Path(plan['geometryManifest']['path']).parent
    bundle=json.loads((directory/'lawn-natural-manifest.json').read_text())
    actual_geometry=json.loads(pinned(plan['geometryManifest']['path'],plan['geometryManifest']['sha256']).read_text())
    require(plan['coverageReceipt']==actual_geometry.get('coverageReceipt')==bundle['coverageReceipt'],
            'Tapered lawn coverage receipt pin differs')
    require(bundle['plan']['sha256']==sha(bundle['plan']['path']) and digest(json.loads(Path(bundle['plan']['path']).read_text()))==digest(plan)
            and bundle['geometryManifest']==plan['geometryManifest'], 'Tapered lawn coverage bundle plan pin differs')
    receipt=json.loads(pinned(bundle['coverageReceipt']['path'],bundle['coverageReceipt']['sha256']).read_text())
    receipt_status=COVER_STATUS if upright else 'PASS_STATIC_PHYSICAL_COVERAGE_NOT_NATIVE_ACCEPTED'
    criteria={'minimumTopViewCoverage':.75,'preferredTopViewCoverage':.80,'minimumTenCmBinP10':.55,'maximumPermittedBladeLossAcrossLods':0} if upright else {
        'minimumTopViewCoverage':.70,'minimumTenCmBinP10':.55,'maximumPermittedBladeLossAcrossLods':0}
    require(receipt==audit['physicalCoverage'] and receipt['status']==receipt_status and receipt['criteria']==criteria,
            'Tapered lawn pinned physical coverage receipt differs')
    require(len(receipt['windows'])==4,'Tapered lawn coverage sample inventory differs')
    for window in receipt['windows']:
        require(window['resolution']==4000 and window['sizeCm']==100 and finite(window['centerCm'],2)
                and [r['lod']for r in window['lods']]==[0,1,2], 'Tapered lawn fine coverage sample differs')
        for lod in window['lods']:
            require((.75<=lod['projectedCoverage']<=1 if upright else .70<lod['projectedCoverage']<=1) and .55<lod['tenCmBinCoverageP10']<=1
                    and 0<=lod['tenCmBinCoverageMinimum']<=lod['tenCmBinCoverageP10']
                    and lod['bareTenCmBins']==0, 'Tapered lawn actual physical coverage criteria failed')
            if upright:require(lod.get('studyTargetsMet') is True,'Tapered lawn source coverage target claim differs')
    if fine:
        pin=plan.get('boundaryCoverageReceipt')
        require(pin and pin==actual_geometry.get('boundaryCoverageReceipt')==bundle.get('boundaryCoverageReceipt'),
                'Tapered lawn boundary coverage receipt pin differs')
        boundary=json.loads(pinned(pin['path'],pin['sha256']).read_text())
        require(boundary==audit.get('boundaryCoverage') and
                boundary.get('status')==(BOUNDARY_STATUS if upright else 'PASS_STATIC_BOUNDARY_LEAF_COVERAGE_NOT_NATIVE_ACCEPTED') and
                boundary.get('criteria')=={'minimumPhysicalCoverByBoundaryBand':{'1to10mm':.12,'10to30mm':.40,'30to100mm':.50},
                    'outsideSourceDomainPermittedCm':0},'Tapered lawn boundary coverage policy differs')
        windows=boundary.get('windows',[])
        require(len(windows)==2 and [w.get('boundaryId')for w in windows]==['deck','mulch'],
                'Tapered lawn boundary sample inventory differs')
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
                    'Tapered lawn boundary frame/resolution differs')
            require(isinstance(window.get('intersectingInstances'),int) and window['intersectingInstances']>0 and
                    [r.get('lod')for r in window.get('lods',[])]==[0,1,2], 'Tapered lawn boundary raster inventory differs')
            for lod in window['lods']:
                bands=lod.get('boundaryBands',[])
                require(0<=lod.get('projectedCoverage',-1)<=1 and len(bands)==3,
                        'Tapered lawn boundary coverage values differ')
                for band,distances,minimum in zip(bands,[[1.,10.],[10.,30.],[30.,100.]],[.12,.40,.50]):
                    require(band.get('distanceFromBoundaryMm')==distances and
                            minimum<band.get('physicalCoverFraction',-1)<=1,'Tapered lawn boundary leaf cover failed')
                if upright:require(lod.get('studyTargetsMet') is True,'Tapered lawn source boundary target claim differs')


def selected_source():
    pinned(ROOT/STUDY_OWNER,STUDY_SOURCE_SHA)
    for name,value in STUDY_PINS.items():pinned(STUDY/name,value)
    return json.loads((STUDY/'lawn-tapered-plan.json').read_text()),json.loads((STUDY/'geometry-manifest.json').read_text())


def _vsub(a,b):return [x-y for x,y in zip(a,b)]
def _dot(a,b):return sum(x*y for x,y in zip(a,b))
def _cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def _unit(a):
    length=math.sqrt(_dot(a,a));require(length>1e-12,'Tapered lawn zero geometry frame')
    return [x/length for x in a]


def _tapered_morphology(meshes,decoded,records,old_records):
    """Read actual five-vertex leaves, including independent triangle-derived frames."""
    lookup={r['nodeName']:r for r in records};old={r['nodeName']:r for r in old_records};nz=[]
    require(len(records)==len(lookup)==60 and set(lookup)==set(decoded),'Tapered anatomy inventory differs')
    for key,mesh in meshes.items():
        count=48 if mesh['edgeMaster'] else 64;reference=decoded[key+'_LOD0']
        for lod in mesh['lods']:
            actual=decoded[lod['nodeName']];record=lookup[lod['nodeName']];prior=old[lod['nodeName']];points=actual['positions']
            require(len(points)==count*5 and actual['triangles']==count*3 and len(record['bladeRanges'])==count,
                    'Tapered actual leaf count/topology differs')
            require(all(actual[field]==reference[field]for field in ('positions','indices','normals','tangents','uv0','uv1','colors')),
                    'Tapered leaf identity lost across LODs')
            require(len(record['positionsCm'])==len(points) and all(math.dist(p,q)<.00002 for p,q in zip(points,record['positionsCm'])),
                    'Tapered decoded positions differ from frozen anatomy')
            faces=[(a,c,b)for a,b,c in zip(actual['indices'][::3],actual['indices'][1::3],actual['indices'][2::3])]
            require(faces==[tuple(t)for t in record['triangles']],'Tapered actual triangle proof differs')
            normal=[[0.,0.,0.]for _ in points];tangent=[[0.,0.,0.]for _ in points];bitangent=[[0.,0.,0.]for _ in points]
            for a,b,c in faces:
                e1,e2=_vsub(points[b],points[a]),_vsub(points[c],points[a]);n=_cross(e1,e2)
                d1,d2=_vsub(actual['uv0'][b],actual['uv0'][a]),_vsub(actual['uv0'][c],actual['uv0'][a]);det=d1[0]*d2[1]-d1[1]*d2[0]
                require(_dot(n,n)>1e-14 and abs(det)>1e-12,'Tapered degenerate geometry/UV')
                nz.append(abs(_unit(n)[2]));t=[(e1[i]*d2[1]-e2[i]*d1[1])/det for i in range(3)];bt=[(e2[i]*d1[0]-e1[i]*d2[0])/det for i in range(3)]
                for index in (a,b,c):
                    for axis in range(3):normal[index][axis]+=n[axis];tangent[index][axis]+=t[axis];bitangent[index][axis]+=bt[axis]
            for index,(p,n,t,uv,color)in enumerate(zip(points,actual['normals'],actual['tangents'],actual['uv0'],actual['colors'])):
                expected_n=_unit(normal[index]);expected_t=_unit([tangent[index][i]-expected_n[i]*_dot(expected_n,tangent[index])for i in range(3)])
                handed=-1. if _dot(_cross(expected_n,expected_t),bitangent[index])<0 else 1.
                require(math.dist(n,expected_n)<.00002 and math.dist(t[:3],expected_t)<.00002 and t[3]==handed,
                        'Tapered actual normals/tangents differ from triangles/UV')
                require(all(0<=v<=1 for v in uv) and all(0<=v<=1 for v in color) and color[3]==1.,'Tapered UV/opaque color differs')
            for index,blade in enumerate(record['bladeRanges']):
                start=index*5;oldblade=prior['bladeRanges'][index];peak=actual['uv0'][start+2][1]
                require(blade['bladeIndex']==index and blade['vertexOffset']==start and blade['vertexCount']==5
                        and blade['triangleOffset']==index*3 and blade['triangleCount']==3 and blade['clipped']is False
                        and blade['low']is (index%4==0),'Tapered actual component/low share differs')
                require(faces[index*3:index*3+3]==[(start,start+1,start+2),(start+1,start+3,start+2),(start+2,start+3,start+4)],
                        'Tapered actual disconnected/panel topology differs')
                uv_expected=[(0.,0.),(1.,0.),(0.,peak),(1.,peak),(.5,1.)]
                require(.36-.000002<=peak<=.45+.000002 and abs(peak-blade['peakT'])<.000002
                        and all(math.dist(a,b)<.000001 for a,b in zip(actual['uv0'][start:start+5],uv_expected)),
                        'Tapered early maximum/pointed tip differs')
                root=[(points[start][i]+points[start+1][i])*.5 for i in range(3)]
                shoulder=[(points[start+2][i]+points[start+3][i])*.5 for i in range(3)];tip=points[start+4]
                width=math.dist(points[start+2],points[start+3]);rootwidth=math.dist(points[start],points[start+1])
                require(.32-.00002<=width<=.46+.00002 and abs(width-blade['widthCm'])<.00002
                        and .56-.00002<=rootwidth/width<=.62+.00002 and abs(rootwidth/width-blade['rootWidthFraction'])<.00002
                        and rootwidth<=.82*oldblade['widthCm']+.00002 and blade['tipWidthCm']==0.,'Tapered physical width/root/tip differs')
                for actualcenter,declared in zip((root,shoulder,tip),blade['centerlineCm']):
                    require(finite(declared,3) and math.dist(actualcenter,declared)<.00003,'Tapered curved centerline differs')
                require(math.dist(shoulder,[root[i]+peak*(tip[i]-root[i])for i in range(3)])>.03,
                        'Tapered actual leaf lost curvature')
                require(math.dist(root[:2],oldblade['rootCm'][:2])<.00002
                        and abs(math.dist(root[:2],tip[:2])-oldblade['reachCm'])<.00002
                        and abs((tip[2]-root[2])/.975-oldblade['heightCm'])<.00002
                        and blade['heightCm']==oldblade['heightCm'] and blade['reachCm']==oldblade['reachCm'],
                        'Tapered source root/height/reach changed')
                oldcolors=prior['colors'][oldblade['vertexOffset']:oldblade['vertexOffset']+oldblade['vertexCount']]
                for channel in range(3):
                    mean=sum(actual['colors'][start+j][channel]for j in range(5))/5
                    require(abs(mean-sum(c[channel]for c in oldcolors)/len(oldcolors))<.000001
                            and abs(actual['colors'][start+4][channel]/actual['colors'][start][channel]-1.12)<.000002,
                            'Tapered mean color/tip-root response changed')
    nz.sort();mean=sum(nz)/len(nz)
    require(nz[len(nz)//2]<.45 and math.sqrt(sum((n-mean)**2 for n in nz)/len(nz))>.15,
            'Tapered surfaces are flat/uniform')


def _legacy_proof(plan,base):
    old=plan['audit']['legacyLawnProof']
    geometry,rows,pin,expected=base._trimmed_legacy_placement(
        json.loads((ROOT/'output/unreal/realism-20260926-r5/photoreal-import-report.json').read_text()),
        json.loads((ROOT/'output/unreal/realism-20260926-r5/rural-import-report.json').read_text()),
        json.loads(pinned(old['plan']['path'],old['plan']['sha256']).read_text()))
    inspection=json.loads(pinned(old['inspection']['path'],old['inspection']['sha256']).read_text())
    require(inspection['contentUnchanged']is True and inspection['nativeLawnInstanceCount']==40437
            and all(old[k]==expected[k]for k in expected) and old['nativeMutationPerformed']is False,
            'Tapered original40437 trim/source proof differs')
    witnesses={r['actor']:r for r in inspection['taggedLawnActors']}
    for key in LEGACY_GROUPS:
        values=witnesses[geometry['groups'][key]['actor']]['orderedInstanceTransforms']
        require(digest([{'translation':v['p'],'rotation':v['q'],'scale3d':v['s']}for v in values])==expected['groups'][key]['transformsSha256'],
                'Tapered actual inherited ordered identity differs')


def validated_groups(plan,manifest,sceneSha,objSha):
    """Explicit new owner, immutable study ancestry, measured geometry and actual crowns."""
    source,source_library=selected_source();base=base_module()
    expected_inputs=dict(source['inputFiles'])
    expected_inputs.update({str(STUDY/name):value for name,value in STUDY_PINS.items()})
    expected_inputs.update({str(BASE):BASE_SHA,str(ROOT/OWNER):sha(ROOT/OWNER),str(ROOT/ADAPTER):sha(ROOT/ADAPTER)})
    viewsource=Path(source['priorPlan']['path']).parent/'lawn-qa-views.json'
    view_sha='b410444ba9a2e2bf8847351fcb0b6263af4fa692bb0156283aff21499159f6e4'
    pinned(viewsource,view_sha);expected_inputs[str(viewsource)]=view_sha
    for name,value in POLICY_PINS.items():expected_inputs[str(ROOT/'scripts/unreal'/name)]=value
    for record in (plan,manifest):
        require(record.get('schemaVersion')==1 and record.get('owner')==ADAPTER
                and record.get('generatorSha256')==sha(ROOT/ADAPTER),'Tapered explicit adapter owner/schema/pin differs')
        require(record['inputFiles']==expected_inputs,'Tapered selected-source closure differs')
        for path,value in record['inputFiles'].items():pinned(path,value)
        require(record['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}
                and record['housePlacement']==source['housePlacement']
                and record['housePlacement']['streetSetbackMm']==record['housePlacement']['eastSetbackMm']==3000,
                'Tapered C/B/B placement/setbacks differ')
        require(record['sourceSceneSha256']==sceneSha==source['sourceSceneSha256']
                and record['sourceObjSha256']==objSha==source['sourceObjSha256'],'Tapered source frame differs')
    mutable={'owner','generatorSha256','inputFiles','geometryManifest','audit','status','coverageReceipt','boundaryCoverageReceipt','geometryProof','selectedStudy','priorCameraManifest'}
    for key,value in source.items():
        if key not in mutable:require(plan.get(key)==value,'Tapered original policy/rows field differs: '+key)
    require(plan.get('selectedStudy')=={'path':str(STUDY/'lawn-tapered-manifest.json'),'sha256':STUDY_PINS['lawn-tapered-manifest.json']},'Tapered selected study differs')
    actual_manifest=json.loads(pinned(plan['geometryManifest']['path'],plan['geometryManifest']['sha256']).read_text())
    require(digest(actual_manifest)==digest(manifest),'Tapered manifest differs from plan pin')
    require(manifest['status']==plan['status']==plan['audit']['status']==STATUS,'Tapered pending-native status differs')
    directory=Path(plan['geometryManifest']['path']).parent
    bundle=json.loads((directory/'lawn-natural-manifest.json').read_text())
    require(bundle['owner']==ADAPTER and bundle['generatorSha256']==sha(ROOT/ADAPTER) and bundle['inputFiles']==expected_inputs
            and bundle['status']==STATUS and bundle['geometryProof']==plan['geometryProof']
            and bundle['coverageReceipt']==plan['coverageReceipt'] and bundle['boundaryCoverageReceipt']==plan['boundaryCoverageReceipt'],
            'Tapered bundle/proof ownership differs')
    material=bundle['materialManifest'];require(material['sha256']==STUDY_PINS['material-manifest.json'],'Tapered recipe changed')
    pinned(material['path'],material['sha256'])
    assetpin=bundle['assetManifest'];asset=json.loads(pinned(assetpin['path'],assetpin['sha256']).read_text())
    require(asset['owner']==ADAPTER and asset['inputFiles']==expected_inputs and asset['generatorSha256']==sha(ROOT/ADAPTER)
            and asset['nativeAppearanceAccepted']is False and asset['performanceAccepted']is False,
            'Tapered asset provenance/acceptance differs')
    meshes={m['id']:m for m in manifest['meshes']};source_meshes={m['id']:m for m in source_library['meshes']}
    require(len(meshes)==len(manifest['meshes'])==20 and set(meshes)==FAMILY,'Tapered master family differs')
    paths={(m['glbPath'],m['glbSha256'])for m in meshes.values()};require(len(paths)==1,'Tapered ambiguous geometry')
    path,value=next(iter(paths));require(value==STUDY_PINS['tapered-covered.glb'],'Tapered selected GLB byte identity differs')
    decoded=_glb_geometry(pinned(path,value),True)
    require(set(decoded)=={k+'_LOD'+str(l)for k in FAMILY for l in range(3)},'Tapered decoded LOD inventory differs')
    prior=json.loads(pinned(source['priorPlan']['path'],source['priorPlan']['sha256']).read_text())
    priorlibrary=json.loads((Path(source['priorPlan']['path']).parent/'geometry-manifest.json').read_text());oldmesh={m['id']:m for m in priorlibrary['meshes']}
    envelopes={}
    for key,mesh in meshes.items():
        for field,want in source_meshes[key].items():
            if field not in ('glbPath','composition'):require(mesh.get(field)==want,'Tapered selected master metadata differs: '+field)
        require(mesh['role']=='grass' and mesh['placementPolicy']=='explicit-only' and mesh['materialKeys']==['lawn_natural_blade']
                and mesh['lodScreenSizes']==SCREENS and [l['level']for l in mesh['lods']]==[0,1,2],'Tapered mesh/LOD policy differs')
        points=[]
        for lod in mesh['lods']:
            actual=decoded[lod['nodeName']];p=actual['positions'];points.extend(p)
            bounds={n:[op(q[i]for q in p)for i in range(3)]for n,op in [('min',min),('max',max)]}
            radius=max(math.hypot(q[0],q[1])for q in p)
            require(len(p)==lod['vertices'] and actual['triangles']==lod['triangles']
                    and all(abs(bounds[n][i]-lod['expectedBoundsCm'][n][i])<.00002 for n in bounds for i in range(3))
                    and abs(radius-lod['radialEnvelopeCm'])<.00002 and abs(bounds['min'][2])<.00002,
                    'Tapered decoded counts/bounds/root differ')
        radius=max(math.hypot(p[0],p[1])for p in points);height=max(p[2]for p in points)
        require(abs(height-mesh['heightCm'])<.00002 and radius<=max(l['radialEnvelopeCm']for l in oldmesh[key]['lods'])+.00002
                and height<=oldmesh[key]['heightCm']+.00002,'Tapered actual envelope exceeds original source')
        envelopes[key]=(radius,height)
    proof=plan['geometryProof'];require(proof['sha256']==STUDY_PINS['lawn-tapered-prototypes.json'],'Tapered selected anatomy pin differs')
    records=json.loads(pinned(proof['path'],proof['sha256']).read_text())
    oldrecords=json.loads((Path(source['priorPlan']['path']).parent/'lawn-natural-prototypes.json').read_text())
    _tapered_morphology(meshes,decoded,records,oldrecords)
    _legacy_proof(plan,base)
    faces,source_edges,exclusions,extra=base._source_context(plan);managed=base._managed_domain(plan)
    polygons=json.loads(plan['lawnDomainSourceMm']);polygons=[polygons['coordinates']]if polygons['type']=='Polygon'else polygons['coordinates']
    edges=[(a,b)for polygon in polygons for ring in polygon for a,b in zip(ring,ring[1:])]
    audit=plan['audit']
    require(audit['sourceMasksUnchanged']is True and audit['sourceTriangles']==27 and audit['extraExclusionSourceIds']==extra
            and audit['rootElevationCm']==-6.5 and all(audit[k]is False for k in ('nativeVerified','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','integrationAuthorized')),
            'Tapered source/acceptance policy differs')
    _coverage_claims(plan,meshes,decoded,managed)
    selected=json.loads((STUDY/'lawn-tapered-manifest.json').read_text())['variant']['measurements']
    require(audit['physicalCoverage']['windows']==selected['physicalCoverage'] and [{k:v for k,v in w.items()if k!='boundaryId'}for w in audit['boundaryCoverage']['windows']]==selected['boundaryCoverage'],
            'Tapered measured receipts differ from selected actual geometry')
    groups=[];counts=Counter();flattened=[];minimum=float('inf');ids=set()
    for group in plan['groups']:
        key,identity=group['meshId'],group['id'];require(key in meshes and identity not in ids and group['role']=='grass'
            and group['qualityDetail']is True and group['cullEndCm']==4000 and group['instances'],'Tapered group policy differs');ids.add(identity)
        native=[]
        for row in group['instances']:
            p,s,yaw=row['positionCm'],row['scale'],row['yawDeg']
            require(finite(p,3) and finite(s,3) and max(s)-min(s)<1e-9 and .6<=s[0]<=1.25 and p[2]==-6.5
                    and isinstance(yaw,(int,float)) and not isinstance(yaw,bool) and math.isfinite(yaw) and -180<=yaw<=180,'Tapered transform differs')
            require(identity=='EX_'+key.replace('lawn_natural_','lawn_natural_'+str(math.floor(p[0]/2000))+'_'+str(math.floor(p[1]/2000))+'_',1),
                    'Tapered spatial group identity differs')
            radius,height=(v*s[0]for v in envelopes[key]);point=[10*p[0],-10*p[1]]
            require(radius<=row['radiusCm']+.00002 and height<=row['actualHeightCm']+.00002
                    and abs(row['enclosingRadiusMm']-(10*row['radiusCm']+1))<.001,'Tapered retained conservative envelope differs')
            clearance=min(_distance(point,a,b)for a,b in edges);minimum=min(minimum,clearance-10*radius-1)
            require(any(_inside_ring(point,poly[0])and not any(_inside_ring(point,h)for h in poly[1:])for poly in polygons)
                    and clearance>10*radius+1 and abs(clearance-row['clearanceMm'])<.002,'Tapered actual crown escaped declared source domain')
            require(any(_inside_ring(p[:2],polygon)for polygon in managed[0])
                    and min(_distance(p[:2],a,b)for a,b in managed[1])>radius+.1,'Tapered actual crown escaped managed keep')
            require(any(_inside_triangle(point,t)for t in faces) and min(_distance(point,a,b)for a,b in source_edges)>10*radius+1,
                    'Tapered crown escaped actual source ground')
            for ex in exclusions:
                poly,box=ex['polygonSourceMm'],ex['boundsMm'];r=10*radius+1
                if point[0]+r<box[0]or point[0]-r>box[2]or point[1]+r<box[1]or point[1]-r>box[3]:continue
                require(not _inside_ring(point,poly) and min(_distance(point,a,b)for a,b in zip(poly,poly[1:]+poly[:1]))>r,'Tapered crown intersects source exclusion')
            require(row['edge']is meshes[key]['edgeMaster'] and row['growthClass']==meshes[key]['growthClass'],'Tapered leaf family differs')
            counts[key]+=1;flattened.append({'meshId':key,**row});native.append({'positionCm':list(p),'yawDeg':yaw,'scale':list(s)})
        groups.append({'id':identity,'meshId':key,'role':'grass','cullEndCm':4000,'qualityDetail':True,'instances':native})
    require(flattened==plan['lawnPlacements'] and len(flattened)==audit['instances']==102011 and len(groups)==audit['groups']==40
            and sum(int(r['edge'])for r in flattened)==audit['edgeInstances']==21144 and dict(counts)==audit['perMesh'],'Tapered population/group inventory differs')
    require(abs(minimum-audit['minimumAdditionalCrownClearanceMm'])<.002,'Tapered actual crown clearance differs')
    return groups
