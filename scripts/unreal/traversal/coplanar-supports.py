#!/usr/bin/env python3
"""CPU source-triangle proof of coplanar floor coverage along each approach.

Does not query native collision, capsule clearance, or renderer state. Coordinates
are source OBJ Z-up millimetres converted to native [x/10,-y/10,z/10] cm, then
the authored walking supportOffsetCm is applied only to the query height.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def barycentric_xy(point, tri):
    a, b, c = tri
    denominator = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
    if abs(denominator) < 1e-10:
        return None
    u = ((b[1]-c[1])*(point[0]-c[0]) + (c[0]-b[0])*(point[1]-c[1])) / denominator
    v = ((c[1]-a[1])*(point[0]-c[0]) + (a[0]-c[0])*(point[1]-c[1])) / denominator
    return (u, v, 1-u-v)


def triangle_interval(start, end, triangle, offset, floor_z, height_tolerance=0.02):
    """Exact affine segment clipping against projected triangle + height slab."""
    start_weights = barycentric_xy(start, triangle)
    end_weights = barycentric_xy(end, triangle)
    if start_weights is None:
        return None
    lower, upper = 0.0, 1.0
    start_z = sum(w*p[2] for w, p in zip(start_weights, triangle)) + offset
    end_z = sum(w*p[2] for w, p in zip(end_weights, triangle)) + offset
    constraints = [(a, b, -1e-10) for a,b in zip(start_weights,end_weights)]
    # z must remain within the explicit coplanarity tolerance for the interval.
    constraints.extend([(start_z,end_z,floor_z-height_tolerance),
                        (-start_z,-end_z,-floor_z-height_tolerance)])
    for a, b, minimum in constraints:
        delta = b-a
        if abs(delta) < 1e-14:
            if a < minimum:
                return None
        elif delta > 0:
            lower = max(lower, (minimum-a)/delta)
        else:
            upper = min(upper, (minimum-a)/delta)
        if lower > upper:
            return None
    if upper-lower < 1e-10:
        return None
    return ([lower, upper], [start_z+(end_z-start_z)*t for t in (lower, upper)])


def merge(intervals):
    result = []
    for start,end in sorted(intervals):
        if result and start <= result[-1][1]+1e-8:
            result[-1][1] = max(result[-1][1],end)
        else:
            result.append([start,end])
    return result


def read_floor_triangles(path, floor_ids):
    vertices = []
    faces = {key: [] for key in floor_ids}
    current = None
    with path.open() as source:
        for line in source:
            if line.startswith('v '):
                x,y,z = map(float,line.split()[1:4])
                vertices.append((x/10,-y/10,z/10))
            elif line.startswith('o '):
                current = line.split()[1]
            elif current in faces and line.startswith('f '):
                indexes = [int(item.split('/')[0])-1 for item in line.split()[1:]]
                if len(indexes) != 3 or any(i < 0 or i >= len(vertices) for i in indexes):
                    raise ValueError('Expected valid source triangle indices')
                faces[current].append(tuple(vertices[i] for i in indexes))
    if any(not value for value in faces.values()):
        raise ValueError('Missing source floor geometry')
    return faces


def main():
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument('--geometry', type=Path, default=base/'geometry')
    parser.add_argument('--candidates', type=Path, default=base/'walking-traversal-candidates.json')
    parser.add_argument('--output', type=Path, default=base/'walking-traversal-coplanar-supports.json')
    args = parser.parse_args()
    contract_path, obj_path = args.geometry/'walking.json', args.geometry/'dom-mm.obj'
    contract, candidates = json.loads(contract_path.read_text()), json.loads(args.candidates.read_text())
    for expected, path in [('contractSha256',contract_path),('sourceObjSha256',obj_path),
                           ('sourceManifestSha256',args.geometry/'scene.json')]:
        if candidates[expected] != sha(path):
            raise ValueError(f'Stale candidate binding: {expected}')
    floors = {item['objectId']: item for item in contract['walkSurfaces']}
    triangles = read_floor_triangles(obj_path, floors)
    legs = []
    for case in candidates['cases']:
        axis = {'x':0,'y':1}[case['movementAxis']]
        for index,leg in enumerate(case['legs']):
            start = leg['startEyeCandidateCm'][:2]
            end = start[:]
            end[axis] = leg['expectedCapsuleCenterStopCm']
            full,partial = [],[]
            for object_id,floor in floors.items():
                intersections = [hit for triangle in triangles[object_id]
                    if (hit := triangle_interval(start,end,triangle,floor['supportOffsetCm'],
                                                   leg['cpuSourceTriangleFloorHeightCm']))]
                if not intersections:
                    continue
                intervals = merge([item[0] for item in intersections])
                item = {'objectId':object_id,'walkSurfaceId':floor['walkSurfaceId'],
                        'supportOffsetCm':floor['supportOffsetCm'],
                        'intervalsNormalized':intervals,'contributingSourceTriangles':len(intersections),
                        'effectiveFloorHeightRangeCm':[
                            min(v for hit in intersections for v in hit[1]),
                            max(v for hit in intersections for v in hit[1])]}
                if len(intervals)==1 and intervals[0][0]<=1e-8 and intervals[0][1]>=1-1e-8:
                    full.append(item)
                else:
                    partial.append(item)
            allowed = [item['objectId'] for item in full]
            if leg['supportObjectId'] not in allowed:
                raise ValueError(f'Original selected support has incomplete path: {case["id"]}/{index}')
            legs.append({'caseId':case['id'],'legIndex':index,'targetObjectId':case['targetObjectId'],
                         'startXYCm':start,'endXYCm':end,'originalSupportObjectId':leg['supportObjectId'],
                         'allowedSupportObjectIds':allowed,'continuousSupports':full,
                         'partialSupportsNotAllowed':partial})
    report = {'schemaVersion':1,'status':'cpu-continuous-source-floor-proof-native-pending',
              'sourceManifestSha256':sha(args.geometry/'scene.json'),'sourceObjSha256':sha(obj_path),
              'contractSha256':sha(contract_path),'candidatesSha256':sha(args.candidates),
              'scriptSha256':sha(Path(__file__)), 'floorCount':len(floors),'legCount':len(legs),
              'heightToleranceCm':0.02,'coordinateTransform':'OBJ mm -> UE cm [x/10,-y/10,z/10]',
              'coverage':'Continuous XY centerline from source eye XY to expected capsule stop. Affine barycentric triangle intervals, authored support offset, coplanar height slab.',
              'legs':legs,'verification':{'sourceFloorCenterlineCoverage':True,
                  'capsuleDiskCoverage':False,'nativeEntryLineHit':False,'nativeCapsuleSupport':False,
                  'nativeOverlapClearance':False,'actualInputTraversal':False}}
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'output':str(args.output),'legCount':len(legs),
                      'supports':[{'case':x['caseId'],'leg':x['legIndex'],'ids':x['allowedSupportObjectIds']} for x in legs]},indent=2))


if __name__ == '__main__':
    # Simple bounded regressions: complete triangle interior, outside, wrong height.
    triangle = ((0,0,0),(4,0,0),(0,4,0))
    assert triangle_interval((.1,.1),(1,1),triangle,0,0)[0] == [0,1]
    assert triangle_interval((5,5),(6,6),triangle,0,0) is None
    assert triangle_interval((.1,.1),(1,1),triangle,0,1) is None
    assert merge([[.5,1],[0,.5]]) == [[0,1]]
    main()
