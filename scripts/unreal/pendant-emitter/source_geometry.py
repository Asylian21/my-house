"""Exact source triangle matching; Nanite render fallback is a separate proof."""
from collections import Counter, defaultdict
import itertools
import math

POSITION_TOLERANCE_MM = .002
AREA_TOLERANCE_M2 = .00000025


def require(ok, message):
    if not ok:raise RuntimeError(message)


def face_key(points):
    # Cyclic rotations preserve winding; a reversed triangle is different.
    return min(tuple(points[i:]+points[:i]) for i in range(3))


def area(triangles):
    values=[]
    for a,b,c in triangles:
        ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)]
        n=(ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0])
        values.append(math.sqrt(sum(x*x for x in n))/2/1e6)
    return math.fsum(values)


def compare_triangles(native_cm, source_mm, expected_area_m2):
    require(len(native_cm)==len(source_mm),'Native source triangle count differs from canonical OBJ')
    key=lambda p:tuple(round(float(x),5) for x in p)
    vertices={key(v) for t in source_mm for v in t};buckets=defaultdict(list)
    cell=lambda p:tuple(math.floor(x/POSITION_TOLERANCE_MM) for x in p)
    for v in vertices:buckets[cell(v)].append(v)
    expected=Counter(face_key([key(v) for v in t]) for t in source_mm)
    matched=Counter();native_mm=[];cache={};maximum=0.0
    for triangle in native_cm:
        require(len(triangle)==3,'Invalid native source triangle')
        row=[];mapped=[]
        for vertex in triangle:
            require(len(vertex)==3 and all(math.isfinite(x) for x in vertex),'Nonfinite native source vertex')
            point=(vertex[0]*10,-vertex[1]*10,vertex[2]*10);row.append(point)
            if point not in cache:
                bucket=cell(point);candidates=[]
                for delta in itertools.product((-1,0,1),repeat=3):
                    for v in buckets.get(tuple(bucket[i]+delta[i] for i in range(3)),()):
                        error=max(abs(point[i]-v[i]) for i in range(3))
                        if error<=POSITION_TOLERANCE_MM:candidates.append((v,error))
                require(len(candidates)==1,'Native source vertex has no unique canonical match within 0.002 mm')
                cache[point]=candidates[0]
            mapped.append(cache[point][0]);maximum=max(maximum,cache[point][1])
        native_mm.append(row);matched[face_key(mapped)]+=1
    require(matched==expected,'Native source triangle connectivity, multiplicity or winding differs')
    native_area=area(native_mm);difference=native_area-expected_area_m2
    require(abs(difference)<=AREA_TOLERANCE_M2,'Native source area differs beyond float bridge tolerance')
    return {'method':'public-source-MeshDescription-scalar-corner-getters','triangleCount':len(native_cm),
            'canonicalTriangleConnectivityAndWindingVerified':True,'matchedUniqueVertices':len(cache),
            'maximumVertexErrorMm':maximum,'vertexToleranceMm':POSITION_TOLERANCE_MM,
            'sourceAreaM2':native_area,'canonicalAreaM2':expected_area_m2,'areaDifferenceM2':difference,
            'areaToleranceM2':AREA_TOLERANCE_M2,'sourceAreaVerified':True,'renderFallbackAreaReadback':False,
            'canonicalPhotometryRenormalized':False}


def read_and_verify(u,mesh,ref,geometry_dir):
    source=ref.source_triangles(geometry_dir/'dom-mm.obj')
    description=mesh.get_static_mesh_description(0)
    require(description is not None and description.get_triangle_count()==len(source),'Exact source MeshDescription is missing')
    triangles=[]
    # The pinned Interchange source description has dense source triangle IDs.
    # Refuse holes rather than silently comparing an incomplete source set.
    for index in range(len(source)):
        triangle=u.TriangleID(id_value=index)
        require(description.is_triangle_valid(triangle),'Source triangle ID missing')
        row=[]
        for corner in range(3):
            instance=description.get_triangle_vertex_instance(triangle,corner)
            require(description.is_vertex_instance_valid(instance),'Source vertex instance invalid')
            vertex=description.get_vertex_instance_vertex(instance)
            require(description.is_vertex_valid(vertex),'Source vertex ID invalid')
            position=description.get_vertex_position(vertex)
            row.append(tuple(float(getattr(position,k)) for k in ('x','y','z')))
        triangles.append(row)
    return compare_triangles(triangles,source,ref.AREA_M2)
