#!/usr/bin/env python3
"""Output-only source geometry proof. Does not launch UE or modify canonical data."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE
while not (ROOT/'package.json').is_file():
    if ROOT.parent == ROOT:
        raise RuntimeError('Repository root not found')
    ROOT = ROOT.parent
GEOMETRY = ROOT / 'output/unreal/geometry'
SOURCE_HELPER = ROOT / 'scripts/unreal/traversal/coplanar-supports.py'
spec = importlib.util.spec_from_file_location('floor_source_proof', SOURCE_HELPER)
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive():
    paths = [GEOMETRY/'scene.json', GEOMETRY/'dom-mm.obj', GEOMETRY/'walking.json',
             GEOMETRY/'hidden-collision.json', GEOMETRY/'viewpoints.json',
             ROOT/'output/unreal/stove-visuals/stove-visuals.json', SOURCE_HELPER, Path(__file__)]
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    walking = json.loads(paths[2].read_text())
    hidden = json.loads(paths[3].read_text())
    views = json.loads(paths[4].read_text())
    stove = json.loads(paths[5].read_text())
    scene_sha, obj_sha = sha(paths[0]), sha(paths[1])
    if (walking['provenance']['sceneSha256'] != scene_sha
            or walking['provenance']['sourceObjSha256'] != obj_sha
            or hidden['sourceManifestSha256'] != scene_sha
            or hidden['mainObjSha256'] != obj_sha
            or stove['sourceManifestSha256'] != scene_sha or stove['sourceObjSha256'] != obj_sha):
        raise ValueError('Canonical source hashes differ')
    interior = next(v for v in views['views'] if v['id'] == 'interior')
    body = stove['sourceRecords']['DOM_00522']['boundsMm']
    axis = [(body['min'][i]+body['max'][i])/2 for i in (0,1)]
    if axis != stove['stoveAxisSourceMm'] or walking['eyeHeightCm'] != 165 or walking['capsuleRadiusCm'] != 22:
        raise ValueError('Source stove axis or walking dimensions changed')
    axis_cm = [axis[0]/10, -axis[1]/10]
    # Authored diagnostic pose: source-facing +X side, 300 cm from cylinder axis,
    # -30 degrees in native XY. It is not an additional canonical house viewpoint.
    eye = [axis_cm[0] + 300*math.cos(math.pi/6), axis_cm[1]-150, 165]
    target = [*axis_cm, eye[2]]  # Horizontal look; existing walking/audit camera API supports it.
    start = interior['eyeCm']
    corridor_min = [min(start[i], eye[i])-22 for i in range(2)]
    corridor_max = [max(start[i], eye[i])+22 for i in range(2)]
    floors = {r['objectId']: r for r in walking['walkSurfaces']}
    triangles = proof.read_floor_triangles(paths[1], floors)
    covers = []
    for object_id, row in floors.items():
        top = [t for t in triangles[object_id] if all(abs(v[2]+row['supportOffsetCm']) < .02 for v in t)]
        if len(top) != 2:
            continue
        vertices = set(v[:2] for t in top for v in t)
        xs, ys = sorted({v[0] for v in vertices}), sorted({v[1] for v in vertices})
        if len(vertices) != 4 or len(xs) != 2 or len(ys) != 2 or vertices != {(x,y) for x in xs for y in ys}:
            continue
        shared = set(v[:2] for v in top[0]) & set(v[:2] for v in top[1])
        if len(shared) != 2:
            continue
        a,b = shared
        if a[0] == b[0] or a[1] == b[1]:
            continue  # Require opposite-corner diagonal, not two overlapping half rectangles.
        if not all(lo <= corridor_min[i] and hi >= corridor_max[i] for i,(lo,hi) in enumerate([xs,ys])):
            continue
        covers.append({'objectId':object_id, 'sourceId':row['sourceId'], 'supportOffsetCm':row['supportOffsetCm'],
                       'topSourceTrianglesCm':top, 'effectiveTopZCm':top[0][0][2]+row['supportOffsetCm'],
                       'proof':'Two source triangles share rectangle diagonal; full 22 cm expanded approach AABB lies inside their union.'})
    if not covers:
        raise ValueError('No source floor covers the full approach/capsule footprint')
    blockers = walking['staticBlockers'] + walking['capturedClosedBlockers'] + hidden['objects']
    blocked = []
    for row in blockers:
        bounds = row['nativeBoundsCm']
        if bounds['max'][2] <= .02 or bounds['min'][2] >= 173:
            continue
        lo, hi = 0.0, 1.0
        for i in range(2):
            delta = eye[i]-start[i]
            lower, upper = bounds['min'][i]-22, bounds['max'][i]+22
            if abs(delta) < 1e-12:
                if not lower <= start[i] <= upper:
                    lo,hi=1,0
                    break
            else:
                a,b = (lower-start[i])/delta,(upper-start[i])/delta
                lo,hi = max(lo,min(a,b)),min(hi,max(a,b))
        if lo <= hi:
            blocked.append(row.get('objectId',row.get('id')))
    if blocked:
        raise ValueError('Conservative approach prism hits source blocker bounds: '+str(blocked))
    return {'schemaVersion':1,'status':'cpu-source-reachable-candidate-native-query-pending',
            'sourceHashes':source_hashes, 'coordinateSystem':'unreal-centimeters',
            'sourceStoveAxisCm':axis_cm,'diagnosticRadiusCm':300,'diagnosticAzimuthDegrees':-30,
            'eyeCm':eye,'targetCm':target,'horizontalFovDegrees':interior['horizontalFovDegrees'],
            'sourceInterior':interior,'approachFootprintAabbCm':{'min':corridor_min,'max':corridor_max},
            'conservativeBlockedVerticalIntervalCm':[.02,173],
            'supportObjectIds':sorted(x['objectId'] for x in covers),'floorProof':covers,
            'checkedBlockerRecords':len(blockers),'blockedSourceObjectIds':blocked,
            'nativeEntryValidated':False,'nativeTraversalValidated':False,'nativeVisibilityValidated':False,
            'limitations':['CPU source AABB rejection is conservative and uses captured-closed state.',
                'This does not prove runtime collision registration, native capsule clearance, actual walking or glass visibility.',
                'Native endpoint entry must use unchanged CMC queries with no XY correction and only these floor IDs.',
                'The 173 cm top bound includes the 170 cm capsule and up to 3 cm floor clearance; runtime must report its actual bound.']}


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--stdout',action='store_true',required=True)
    parser.parse_args()
    print(json.dumps(derive(),indent=2,allow_nan=False))
