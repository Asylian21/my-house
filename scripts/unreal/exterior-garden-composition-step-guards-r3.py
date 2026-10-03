"""Exact frozen 3D step projection, separate from the organic 2D bed union.

The original four closed step solids have duplicate projected floor/top faces
and vertical faces. They are not a triangulated 2D bed. All 112 nonzero raw
projected edges are retained in original order, including internal diagonals,
so clearance is at least as conservative as the frozen source proposal.
No step coordinates, bed predicate or native geometry are modified here.
"""
from collections import Counter
import hashlib
import json
import math

OWNER='scripts/unreal/exterior-garden-composition-step-guards-r3.py'
STEP_IDS=('DOM_01961','DOM_01962','DOM_01963','DOM_01964')
STEP_SHA='2c60c79284eb7d613994696d26055ec63e09a9c64be8c625968fd96cd55c5536'
POLICY={'owner':OWNER,'originalStepTrianglesSha256':STEP_SHA,'stepSolids':4,'sourceTriangles':48,
 'sourceVertices':32,'raw3DEdges':144,'unique3DEdges':72,'each3DEdgeMultiplicity':2,
 'orderedNonzeroProjectedRawEdges':112,'zeroProjectedRawEdges':32,
 'nondegenerateProjectedTriangles':16,'degenerateProjectedVerticalTriangles':32,
 'bedUnionBoundaryRecipeChanged':False,'projectedStepFacesTreatedAsBedTriangleUnion':False,
 'distanceRecipe':'Strict outside all nondegenerate projected triangles and circle radius < minimum distance to all112 original nonzero projected raw edges',
 'toleranceCm':0,'stepGeometrySurveyed':False,'nativeStepGeometryReadbackClaimed':False}


def require(ok,message):
 if not ok:raise RuntimeError(message)


def finite(values,count):
 return isinstance(values,(list,tuple))and len(values)==count and all(type(v)in(int,float)and math.isfinite(v)for v in values)


def area2(t):return(t[1][0]-t[0][0])*(t[2][1]-t[0][1])-(t[1][1]-t[0][1])*(t[2][0]-t[0][0])


def validated_steps(source):
 require(isinstance(source,dict)and set(source)==set(STEP_IDS),'Only exact four original step solids allowed')
 require(all(isinstance(source[k],list)and len(source[k])==12 for k in STEP_IDS),'Each original closed step has12 faces')
 require(all(isinstance(t,list)and len(t)==3 and all(finite(p,3)for p in t)for rows in source.values()for t in rows),
  'Original finite XYZ step triangles required')
 digest=hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 require(digest==STEP_SHA,'Frozen full original step coordinates/order differ')
 edges=[];nondegenerate=[];zero=0;vertices=set();raw3d=Counter()
 for key in STEP_IDS:
  rows=source[key];local={tuple(p)for t in rows for p in t};require(len(local)==8,'Eight original solid vertices required');vertices.update(local)
  for t in rows:
   for a,b in zip(t,t[1:]+t[:1]):
    require(a!=b,'Original 3D step edge cannot collapse')
    raw3d[tuple(sorted((tuple(a),tuple(b))))]+=1
    if a[:2]!=b[:2]:edges.append((a[:2],b[:2]))
    else:zero+=1
   if area2(t)!=0:nondegenerate.append([p[:2]for p in t])
 require(len(vertices)==32 and len(raw3d)==72 and set(raw3d.values())=={2}and sum(raw3d.values())==144,
  'Original closed 3D solid edge census differs')
 require(len(edges)==112 and zero==32 and len(nondegenerate)==16,'Exact projected original48-face/112-edge partition differs')
 return {'edges':edges,'triangles':nondegenerate,'policy':dict(POLICY)}


def point_inside(point,triangle):
 require(finite(point,2)and all(finite(p,2)for p in triangle)and len(triangle)==3 and area2(triangle)!=0,
  'Finite nondegenerate projected step triangle required')
 signs=[(b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])for a,b in zip(triangle,triangle[1:]+triangle[:1])]
 return all(v>=0 for v in signs)or all(v<=0 for v in signs)


def edge_distance(point,a,b):
 dx,dy=b[0]-a[0],b[1]-a[1];square=dx*dx+dy*dy
 require(square>0,'Zero projected vertical edges cannot enter distance calculation')
 t=max(0.,min(1.,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/square))
 return math.hypot(point[0]-a[0]-t*dx,point[1]-a[1]-t*dy)


def circle_clearance(steps,point,radius):
 require(finite(point,2)and type(radius)in(int,float)and math.isfinite(radius)and radius>0,'Finite positive native-matrix circle required')
 require(steps['policy']==POLICY and len(steps['edges'])==112 and len(steps['triangles'])==16,'Validated original step projection required')
 require(not any(point_inside(point,t)for t in steps['triangles']),'Native-matrix crown root lies within original projected steps')
 distance=min(edge_distance(point,a,b)for a,b in steps['edges'])
 require(math.isfinite(distance)and radius<distance,'Complete native-matrix crown circle intersects original projected step faces/edges')
 return {'minimumOriginalProjectedRawEdgeDistanceCm':distance,'circleClearanceCm':distance-radius,
  'sourceStepProjection':dict(POLICY),'fullCircleExcludesOriginalProjectedSteps':True,
  'numericInequalitiesExecuted':True,'freshDerivedFloatBitEqualityRequired':False}
