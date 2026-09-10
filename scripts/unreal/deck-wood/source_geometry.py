"""Read-only source-bound physical UV1 plan for five deck bindings; never writes UE assets."""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import itertools
import json
import math

TARGETS = {
    'DOM_01708': ('MAT_0095', 78), 'DOM_01710': ('MAT_0096', 71),
    'DOM_01713': ('MAT_0097', 47), 'DOM_01719': ('MAT_0098', 68),
    'DOM_01779': ('MAT_0104', 1),
}
POSITION_TOLERANCE_MM = .002
UV0_TOLERANCE = .000002
BAND_STARTS = (.021, .263, .5895)
U_PERIOD_MM, V_PERIOD_MM = 1440.0, 1500.0
HATCH = 'DOM_01779'


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sub(a, b): return tuple(x-y for x,y in zip(a,b))
def dot(a, b): return sum(x*y for x,y in zip(a,b))
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def length(a): return math.sqrt(dot(a,a))
def cyclic(p): return min(tuple(p[i:]+p[:i]) for i in range(3))
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def native_uv(uv): return (uv[0], 1.0-uv[1])  # Blender OBJ→glTF V convention; UE copies TEXCOORD_0.


def _face_geometry(triangles, lo, hi, axis, side):
    points={p for t in triangles for p in t['p']}
    require(len(triangles)==2 and len(points)==4, 'Box face must be exactly two triangles/four corners')
    require(len(set(triangles[0]['p']) & set(triangles[1]['p']))==2, 'Box face diagonal differs')
    normals=[cross(sub(t['p'][1],t['p'][0]),sub(t['p'][2],t['p'][0])) for t in triangles]
    require(dot(*normals)>0, 'Box face triangle winding is inconsistent')
    expected=(hi[(axis+1)%3]-lo[(axis+1)%3])*(hi[(axis+2)%3]-lo[(axis+2)%3])
    require(abs(sum(length(n)*.5 for n in normals)-expected)<=max(1e-5,expected*1e-10), 'Box face does not cover its rectangle exactly')
    # Four UV corners must form the same affine rectangle on both source triangles.
    uv_by_p={}
    for t in triangles:
        for p,uv in zip(t['p'],t['nativeUv0']):
            require(p not in uv_by_p or uv_by_p[p]==uv, 'Source UV0 seam crosses one planar box face')
            uv_by_p[p]=uv
    uvlo=tuple(min(uv[i] for uv in uv_by_p.values()) for i in range(2))
    uvhi=tuple(max(uv[i] for uv in uv_by_p.values()) for i in range(2))
    spans=sub(uvhi,uvlo)
    require(min(spans)>1e-8 and set(uv_by_p.values())==set(itertools.product(*zip(uvlo,uvhi))), 'Degenerate/nonrectangular source face UV0')
    t=triangles[0];a,b,c=t['p'];ua,ub,uc=t['nativeUv0'];d1,d2=sub(ub,ua),sub(uc,ua)
    determinant=d1[0]*d2[1]-d1[1]*d2[0]
    require(abs(determinant)>1e-12, 'Degenerate source UV0 Jacobian')
    e1,e2=sub(b,a),sub(c,a)
    du=tuple((e1[i]*d2[1]-e2[i]*d1[1])/determinant for i in range(3))
    dv=tuple((e2[i]*d1[0]-e1[i]*d2[0])/determinant for i in range(3))
    require(sum(abs(x)>1e-7 for x in du)==1 and sum(abs(x)>1e-7 for x in dv)==1 and abs(dot(du,dv))<1e-7, 'Source face UV0 axes are not distinct physical box axes')
    for p,uv in uv_by_p.items():
        rebuilt=tuple(a[i]+du[i]*(uv[0]-ua[0])+dv[i]*(uv[1]-ua[1]) for i in range(3))
        require(max(abs(x-y) for x,y in zip(p,rebuilt))<=1e-5, 'Source UV0 mapping is not affine across both triangles')
    return {'axis':axis,'side':side,'uExtentMm':length(du)*spans[0], 'vExtentMm':length(dv)*spans[1],
            'uDirectionSource':tuple(x/length(du) for x in du), 'vDirectionSource':tuple(x/length(dv) for x in dv),
            'nativeUv0Min':uvlo,'nativeUv0Max':uvhi,'outwardWinding':normals[0][axis]*(1 if side else -1)>0}


def _boards(object_id, triangles):
    boards=[]
    for board_index in range(len(triangles)//12):
        group=triangles[board_index*12:(board_index+1)*12]
        points={p for t in group for p in t['p']}
        require(len(points)==8, 'Source board must have exactly eight distinct corners')
        lo=tuple(min(p[i] for p in points) for i in range(3));hi=tuple(max(p[i] for p in points) for i in range(3))
        require(min(sub(hi,lo))>0 and points==set(itertools.product(*zip(lo,hi))), 'Source board is not an axial eight-corner box')
        if object_id==HATCH: require(max(abs(a-b) for a,b in zip(sub(hi,lo),(900,1100,55)))<1e-5, 'Hatch dimensions differ')
        else: require(abs(hi[2]-lo[2]-28)<1e-5 and 0<hi[1]-lo[1]<=145.00001, 'Plank width/thickness differs')
        faces=defaultdict(list)
        for t in group:
            planes=[(i,s) for i in range(3) for s in (0,1) if all(p[i]==(hi if s else lo)[i] for p in t['p'])]
            require(len(planes)==1 and len(set(t['p']))==3, 'Triangle is not a nondegenerate box face')
            faces[planes[0]].append(t)
        require(set(faces)==set(itertools.product(range(3),(0,1))), 'Missing source box face')
        seed=hashlib.sha256(('brezi-deck-physical-uv1-v1|'+object_id+'|'+str(board_index)).encode()).digest()
        u_phase=int.from_bytes(seed[:4],'big')/2**32
        band_index=seed[4]%len(BAND_STARTS)
        v_phase=(int.from_bytes(seed[5:9],'big')/2**32) if object_id==HATCH else BAND_STARTS[band_index]
        face_records=[]
        for (axis,side),items in sorted(faces.items()):
            face=_face_geometry(items,lo,hi,axis,side)
            require(object_id==HATCH or face['vExtentMm']<=145.00001, 'Plank face exceeds reviewed V strip width')
            for t in items:
                t['boardIndex']=board_index;t['face']=(axis,side)
                t['uv1']=[(u_phase+(uv[0]-face['nativeUv0Min'][0])/(face['nativeUv0Max'][0]-face['nativeUv0Min'][0])*face['uExtentMm']/U_PERIOD_MM,
                           v_phase+(uv[1]-face['nativeUv0Min'][1])/(face['nativeUv0Max'][1]-face['nativeUv0Min'][1])*face['vExtentMm']/V_PERIOD_MM)
                          for uv in t['nativeUv0']]
            face_records.append(face)
        require(all(f['outwardWinding'] for f in face_records), 'Source box shell winding must face outward')
        boards.append({'index':board_index,'boundsMm':{'min':lo,'max':hi},'dimensionsMm':sub(hi,lo),
                       'uPhase':u_phase,'vPhase':v_phase,'bandIndex':None if object_id==HATCH else band_index,'faces':face_records})
    return boards


def read_source(obj_path):
    """Return mapping keyed by the exact five DOM IDs; triangles retain source and native-oriented UV0."""
    points=[];uvs=[];normal_count=0;current=None;slot=None;seen=set();sha=hashlib.sha256()
    selected={i:[] for i in TARGETS}
    with Path(obj_path).open('rb') as stream:
        for line_no,raw in enumerate(stream,1):
            sha.update(raw);fields=raw.decode('utf8').split()
            if not fields: continue
            kind=fields[0]
            if kind in ('v','vt'):
                width=3 if kind=='v' else 2
                require(len(fields)==width+1, 'Unexpected canonical OBJ coordinate layout')
                value=tuple(map(float,fields[1:]));require(all(math.isfinite(v) for v in value),'Nonfinite source coordinate')
                (points if kind=='v' else uvs).append(value)
            elif kind=='vn': normal_count+=1
            elif kind=='o':
                current=fields[1];slot=None
                if current in TARGETS: require(current not in seen,'Duplicate selected source object');seen.add(current)
            elif kind=='usemtl': slot=fields[1]
            elif kind=='f' and slot in {x[0] for x in TARGETS.values()} and current not in TARGETS:
                raise RuntimeError('Selected deck slot is shared by an unregistered source object')
            elif kind=='f' and current in TARGETS:
                require(slot==TARGETS[current][0] and len(fields)==4, 'Selected source slot/triangulation differs')
                refs=[tuple(map(int,f.split('/'))) for f in fields[1:]]
                require(all(len(r)==3 and 0<r[0]<=len(points) and 0<r[1]<=len(uvs) and 0<r[2]<=normal_count for r in refs),'Invalid/relative source corner reference')
                p=[points[r[0]-1] for r in refs];uv=[uvs[r[1]-1] for r in refs]
                selected[current].append({'p':p,'sourceUv0':uv,'nativeUv0':[native_uv(x) for x in uv],'objFaceLine':line_no})
    require(seen==set(TARGETS),'Selected source set incomplete')
    result={}
    for object_id,triangles in selected.items():
        slot,count=TARGETS[object_id]
        require(len(triangles)==12*count,'Selected source triangle count differs')
        require(len({cyclic(t['p']) for t in triangles})==len(triangles),'Duplicate source triangle')
        boards=_boards(object_id,triangles)
        result[object_id]={'objectId':object_id,'slot':slot,'triangles':triangles,'boards':boards,
                           'sourceObjSha256':sha.hexdigest(),'sourceTopologySha256':digest([t['p'] for t in triangles]),
                           'mapping':{'uPeriodMm':U_PERIOD_MM,'vPeriodMm':V_PERIOD_MM,'bandStarts':BAND_STARTS,
                                      'uv0Bridge':'native=(OBJ.u,1-OBJ.v)','hatchSeparateFullPattern':object_id==HATCH,
                                      'uCropAppliedHere':False,'phaseSeed':'sha256 brezi-deck-physical-uv1-v1|DOM|boardIndex'}}
    return result


def _plan_native_rows(rows, instance_count, object_id, source):
    record=source[object_id];triangles=record['triangles']
    require(len(rows)==len(triangles),'Native source triangle count differs')
    unique={p for t in triangles for p in t['p']};buckets=defaultdict(list)
    cell=lambda p:tuple(math.floor(x/POSITION_TOLERANCE_MM) for x in p)
    for p in unique:buckets[cell(p)].append(p)
    expected={cyclic(t['p']):t for t in triangles};at_vertex=defaultdict(list)
    for t in triangles:
        for corner,p in enumerate(t['p']):at_vertex[p].append((t,corner))
    visited=Counter();cache={};planned={};uv0_read={};maximum=0.;uv_max=0.
    maximum_candidates=0;uv_disambiguations=0
    for row in rows:
        require(len(row)==3,'Native triangle corner count differs');candidate_sets=[];native_points=[]
        for item in row:
            p=item['p'];require(len(p)==3 and all(math.isfinite(v) for v in p),'Nonfinite native position')
            uv=item['uv0'];require(len(uv)==2 and all(math.isfinite(v) for v in uv),'Nonfinite native UV0')
            point=(p[0]*10,-p[1]*10,p[2]*10);native_points.append(point)
            if point not in cache:
                home=cell(point);candidates={}
                for delta in itertools.product((-1,0,1),repeat=3):
                    for candidate in buckets.get(tuple(home[i]+delta[i] for i in range(3)),()):
                        error=max(abs(point[i]-candidate[i]) for i in range(3))
                        if error<=POSITION_TOLERANCE_MM:candidates[candidate]=error
                require(candidates,'Native vertex has no source match within 0.002 mm')
                cache[point]=candidates
            candidate_sets.append(cache[point]);maximum_candidates=max(maximum_candidates,len(cache[point]))
        geometric=[];valid=[]
        for point in candidate_sets[0]:
            for target,shift in at_vertex[point]:
                # Cyclic rotations only: winding and connectivity remain exact source identities.
                if not all(target['p'][(c+shift)%3] in candidate_sets[c] for c in range(3)):continue
                geometric.append((target,shift))
                error=max(abs(row[c]['uv0'][k]-target['nativeUv0'][(c+shift)%3][k]) for c in range(3) for k in range(2))
                if error<=UV0_TOLERANCE:valid.append((target,shift,error))
        require(geometric,'Native triangle winding/connectivity differs')
        require(valid,'Native UV0 differs from verified OBJ→glTF UV convention')
        require(len(valid)==1,'Native triangle/UV0 has multiple canonical source matches')
        target,shift,error=valid[0];uv_max=max(uv_max,error)
        uv_disambiguations+=int(len(geometric)>1)
        key=cyclic(target['p']);visited[key]+=1
        maximum=max(maximum,max(candidate_sets[c][target['p'][(c+shift)%3]] for c in range(3)))
        for corner,item in enumerate(row):
            source_corner=(corner+shift)%3;uv=item['uv0'];idx=item['id']
            require(isinstance(idx,int) and idx>=0 and len(uv)==2 and all(math.isfinite(x) for x in uv),'Invalid native instance/UV0')
            error=max(abs(uv[i]-target['nativeUv0'][source_corner][i]) for i in range(2));uv_max=max(uv_max,error)
            require(error<=UV0_TOLERANCE,'Native UV0 differs from verified OBJ→glTF UV convention')
            desired=target['uv1'][source_corner]
            require(idx not in planned or max(abs(a-b) for a,b in zip(planned[idx],desired))<=1e-10,'Shared native vertex instance requests conflicting UV1')
            require(idx not in uv0_read or uv0_read[idx]==tuple(uv),'Repeated native UV0 read differs')
            planned[idx]=desired;uv0_read[idx]=tuple(uv)
    require(visited==Counter({k:1 for k in expected}),'Native triangle multiplicity/coverage differs')
    require(len(planned)==instance_count,'Native source vertex-instance coverage is incomplete')
    ids=sorted(planned);uv1=[planned[i] for i in ids]
    return {'ids':ids,'uv1':uv1,'proof':{'method':'public-source-MeshDescription-read-only-UV1-plan','objectId':object_id,
        'sourceObjSha256':record['sourceObjSha256'],'sourceTopologySha256':record['sourceTopologySha256'],
        'triangleCount':len(rows),'boardCount':len(record['boards']),'nativeVertexInstanceCount':instance_count,
        'nativeVertexInstanceCoverageComplete':True,'canonicalTriangleConnectivityMultiplicityAndWindingVerified':True,
        'maximumVertexErrorMm':maximum,'vertexToleranceMm':POSITION_TOLERANCE_MM,
        'matchingPolicy':'unique-canonical-triangle-cyclic-winding-plus-native-UV0',
        'maximumSourceVertexCandidatesWithinTolerance':maximum_candidates,'uv0DisambiguatedTriangleCount':uv_disambiguations,'maximumUv0Error':uv_max,'uv0Tolerance':UV0_TOLERANCE,
        'uv0NativeSha256':digest([[i,uv0_read[i]] for i in ids]),'uv1PlanSha256':digest(list(zip(ids,uv1))),
        'nativeUv0Preserved':True,'geometryMutationPerformed':False,'uvMutationPerformed':False,'savedReloadVerified':False,
        'axes':'UV1 positive axes agree with native UV0; native UV0=(OBJ.u,1-OBJ.v)',
        'mapping':record['mapping'],'hatchTopAxes':next((f for f in record['boards'][0]['faces'] if f['axis']==2 and f['side']==1),None) if object_id==HATCH else None}}


def read_and_plan(unreal, mesh, object_id, source):
    """Only public reflected read APIs. IDs are sorted integers; caller owns any later UV1 write/save/readback."""
    require(object_id in TARGETS and object_id in source,'Unregistered deck source')
    require(source[object_id]['slot']==TARGETS[object_id][0],'Source mapping slot differs')
    description=mesh.get_static_mesh_description(0)
    require(description is not None and description.get_triangle_count()==len(source[object_id]['triangles']),'Native source MeshDescription missing/count differs')
    rows=[]
    for index in range(description.get_triangle_count()):
        triangle=unreal.TriangleID(id_value=index)
        require(description.is_triangle_valid(triangle),'Native triangle ID holes are not supported by this bounded reader')
        row=[]
        for corner in range(3):
            instance=description.get_triangle_vertex_instance(triangle,corner)
            require(description.is_vertex_instance_valid(instance),'Invalid native vertex-instance ID')
            vertex=description.get_vertex_instance_vertex(instance)
            require(description.is_vertex_valid(vertex),'Invalid native vertex ID')
            p=description.get_vertex_position(vertex);uv=description.get_vertex_instance_uv(instance,0)
            row.append({'id':int(instance.id_value),'p':tuple(float(getattr(p,k)) for k in ('x','y','z')),'uv0':(float(uv.x),float(uv.y))})
        rows.append(row)
    return _plan_native_rows(rows,description.get_vertex_instance_count(),object_id,source)
