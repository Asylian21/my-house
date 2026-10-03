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
