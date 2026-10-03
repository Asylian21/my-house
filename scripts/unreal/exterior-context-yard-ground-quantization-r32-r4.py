"""Exact generated F32 topology accounting, never approximate face pruning."""
import copy
import math
import struct


def require(ok,message):
 if not ok:raise ValueError(message)


def f32(value):return struct.unpack('<f',struct.pack('<f',value))[0]


def native_points(points):
 return [[f32(f32(v/100.)*100.)for v in row]for row in points]


def cross(a,b,c):
 u=[b[k]-a[k]for k in range(3)];v=[c[k]-a[k]for k in range(3)]
 return [u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]


def stable_native_coordinate(value):
 require(math.isfinite(value),'Nonfinite source coordinate')
 original=value;seen=set()
 for _ in range(16):
  bits=struct.pack('<d',value);require(bits not in seen,'Generated F32 coordinate entered a cycle')
  seen.add(bits);next_value=f32(f32(value/100.)*100.)
  if struct.pack('<d',next_value)==bits:return value
  value=next_value
 raise ValueError('Generated F32 coordinate did not reach an exact fixed point')


def quantized_cell_triangles(poly):
 """Quantize a 2D cell/ring partition before any elevation is evaluated.

 Zero projected polygons are accounted before they can become nonzero
 vertical 3D faces. Retriangulation preserves the entire quantized 2D union.
 No positive-area polygon is discarded and no epsilon area cutoff is used.
 """
 from shapely import constrained_delaunay_triangles
 from shapely.geometry import Polygon
 from shapely.ops import unary_union
 original=[];quantized=[];zeros=[];orientations=0
 for tri in constrained_delaunay_triangles(poly).geoms:
  require(tri.area>0. and poly.covers(tri),'Source constrained cell face invalid')
  values=[list(p)for p in list(tri.exterior.coords)[:3]]
  original.append(tri)
  xy=[[stable_native_coordinate(v)for v in p]for p in values]
  polygon=Polygon(xy)
  if polygon.area==0.:
   zeros.append({'sourceTriangle':len(original)-1,'sourceProjectedPointsCm':values,
    'quantizedProjectedPointsCm':xy,'sourceProjectedAreaCm2':tri.area,
    'quantizedProjectedAreaCm2':0.,'heightEvaluated':False})
  else:
   require(polygon.is_valid,'Quantized positive cell face invalid')
   quantized.append(polygon)
 require(unary_union(original).symmetric_difference(poly).area<.001,'Original cell triangulation lost its source polygon')
 union=unary_union(quantized);retess=[];retess_polygons=[]
 parts=[union]if union.geom_type=='Polygon'else list(union.geoms)if union.geom_type=='MultiPolygon'else []
 require(parts or union.is_empty,'Quantized floor union contains nonpolygonal positive area')
 for part in parts:
  for tri in constrained_delaunay_triangles(part).geoms:
   require(tri.area>0. and part.covers(tri),'Quantized constrained face invalid')
   xy=[list(p)for p in list(tri.exterior.coords)[:3]]
   require(all(stable_native_coordinate(v)==v for p in xy for v in p),'Retriangulation introduced a nonfixed F32 coordinate')
   a,b,c=xy;det=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
   require(det!=0.,'Retriangulation introduced a zero footprint face')
   if det>0.:xy=[a,c,b]
   retess.append(xy);retess_polygons.append(Polygon(xy))
 require(unary_union(retess_polygons).equals(union),'Retriangulation changed the exact quantized floor union')
 proof={'originalSourceCellAreaCm2':poly.area,'quantizedCellFloorAreaCm2':union.area,
  'authoredToQuantizedCellSymmetricDifferenceAreaCm2':poly.symmetric_difference(union).area,
  'sourcePartitionTriangles':len(original),'quantizedRetessellatedTriangles':len(retess),
  'discardedBeforeHeightExactZeroProjectedRegions':zeros,'discardedQuantizedFootprintAreaCm2':0.,
  'wholeQuantizedCellUnionConservedExactly':True,'positiveAreaPolygonsDropped':False,'approximateAreaThresholdUsed':False}
 return retess,proof


def compact_exact_zero_faces(row):
 """Drop only faces whose decoded native-route 3D cross is exactly zero.

 Source positive-area faces remain recorded with their original identity.
 A vertical/sliver face with nonzero 3D area is rejected rather than dropped.
 Every nonzero clockwise face is retained without an epsilon threshold.
 """
 points=native_points(row['verticesCm']);kept=[];discarded=[];source_triangles=[]
 require(len(row['indices'])%3==0,'Source indices must contain full triangles')
 for offset in range(0,len(row['indices']),3):
  ids=row['indices'][offset:offset+3]
  source=[row['verticesCm'][i]for i in ids];decoded=[points[i]for i in ids]
  before=cross(*source);after=cross(*decoded)
  require(before[2]<0.,'Source clockwise face must have strictly positive floor footprint')
  if after==[0.,0.,0.]:
   discarded.append({'sourceTriangle':offset//3,'sourceIndices':ids,
    'sourcePositionsCm':source,'decodedNativeProposalPositionsCm':decoded,
    'sourceProjectedAreaCm2':-before[2]/2.,'decodedCrossProductCm2':after,
    'decodedThreeDimensionalAreaCm2':0.,'decodedProjectedFootprintAreaCm2':0.})
  else:
   require(after[2]<0.,'Nonzero decoded face must retain clockwise winding and a positive floor footprint')
   kept.extend(ids);source_triangles.append(offset//3)
 require(kept,'Topology cannot discard every face')
 used=sorted(set(kept));remap={old:new for new,old in enumerate(used)}
 result=copy.deepcopy(row)
 for key in ('verticesCm','uv0','uv1'):
  result[key]=[row[key][i]for i in used]
 result['indices']=[remap[i]for i in kept]
 if 'sourceGroundVertexWitnesses'in row:
  result['sourceGroundVertexWitnesses']={str(remap[i]):row['sourceGroundVertexWitnesses'][str(i)]for i in used}
 result['quantizedTopologyAccounting']={'scope':'Generated original-source topology versus proposed decoded native F32 positions; not actual UE readback',
  'originalSourceTriangles':len(row['indices'])//3,'retainedTriangles':len(kept)//3,
  'discardedExactZeroThreeDimensionalAreaFaces':discarded,'discardedFaceCount':len(discarded),
  'discardedDecodedProjectedFootprintAreaCm2':0.,'discardedSourceProjectedAreaCm2':sum(r['sourceProjectedAreaCm2']for r in discarded),
  'retainedOriginalTriangleIds':source_triangles,'retainedOriginalVertexIds':used,
  'approximateAreaThresholdUsed':False,'nonzeroFacesDropped':False,
  'everyRetainedDecodedFaceClockwiseAndPositiveFootprint':True,'nativeExecuted':False}
 return result
