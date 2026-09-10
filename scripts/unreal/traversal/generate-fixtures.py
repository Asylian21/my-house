#!/usr/bin/env python3
"""Prepare bounded source fixtures. CPU validation does not certify native entry or traversal."""
from pathlib import Path
import argparse, hashlib, json, math
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
def digest(data): return hashlib.sha256(data).hexdigest()
def generate(contract_bytes, candidate_bytes, coplanar_bytes=None):
    if not __debug__: raise RuntimeError("Run without Python optimization; source validation must remain enabled")
    contract, candidates = json.loads(contract_bytes), json.loads(candidate_bytes)
    assert candidates['schemaVersion'] == 1
    assert candidates['sourceManifestSha256'] == contract['provenance']['sceneSha256'], 'Stale candidate source scene'
    assert candidates['contractSha256'] == digest(contract_bytes), 'Stale candidate contract'
    assert candidates['sourceObjSha256'] == contract['provenance']['sourceObjSha256'], 'Stale source OBJ'
    floors = {r['objectId']: r for r in contract['walkSurfaces']}
    blockers = {r['objectId']: r for r in contract['staticBlockers'] + contract['capturedClosedBlockers']}
    cases = []
    for candidate in candidates['cases']:
        target = blockers.get(candidate['targetObjectId'])
        assert target, f'Missing explicit source blocker {candidate["targetObjectId"]}'
        for side in ('min','max'):
            assert all(abs(a-b) <= .002 for a,b in zip(target['nativeBoundsCm'][side], candidate['targetBoundsCm'][side])), 'Source blocker bounds differ'
        for index, leg in enumerate(candidate['legs']):
            assert leg['supportObjectId'] in floors, 'Unknown source floor'
            eye, direction = leg['startEyeCandidateCm'], leg['direction']
            assert all(math.isfinite(x) for x in eye + direction)
            assert abs(math.sqrt(sum(x*x for x in direction))-1) < 1e-6 and direction[2] == 0
            assert abs(eye[2] - leg['cpuSourceTriangleFloorHeightCm'] - contract['eyeHeightCm']) < .002
            axis = {'x':0,'y':1}[candidate['movementAxis']]
            near = target['nativeBoundsCm']['min' if direction[axis]>0 else 'max'][axis]
            assert abs(leg['expectedNearColliderPlaneCm']-near)<.002
            assert abs(leg['expectedCapsuleCenterStopCm']-(near-direction[axis]*contract['capsuleRadiusCm']))<.002, 'Capsule stop differs from source radius'
            cases.append({'id': f'{candidate["id"]}-side-{index + 1}', 'blockerObjectId': target['objectId'],
                'supportObjectId': leg['supportObjectId'], 'eyeCm': eye, 'forward': direction, 'holdSeconds': 2,
                'sourceId': target['sourceId'], 'sourceBoundsCm': target['nativeBoundsCm'],
                'sourceRequiredState': target.get('requiredState'),
                'cpuFloorTriangleHeightCm': leg['cpuSourceTriangleFloorHeightCm'],
                'cpuNearColliderPlaneCm': leg['expectedNearColliderPlaneCm'],
                'derivation': 'Exact source OBJ vertical floor intersection; target bounds plane +/- 60 cm, no native XY adjustment.'})
    assert len(cases) == 6 and len({c['id'] for c in cases}) == 6
    assert coplanar_bytes, 'A current continuous source floor proof is required'
    proof_bytes = coplanar_bytes
    proof = json.loads(proof_bytes)
    assert proof['sourceManifestSha256'] == candidates['sourceManifestSha256'] and proof['contractSha256'] == digest(contract_bytes), 'Stale coplanar contract proof'
    assert proof['sourceObjSha256'] == candidates['sourceObjSha256'] and proof['candidatesSha256'] == digest(candidate_bytes), 'Stale coplanar source proof'
    assert proof['scriptSha256'] == digest((HERE / 'coplanar-supports.py').read_bytes()), 'Coplanar helper differs'
    assert proof['floorCount'] == len(floors) and proof['legCount'] == len(cases)
    for candidate, leg in zip(cases, proof['legs']):
        assert candidate['id'] == f"{leg['caseId']}-side-{leg['legIndex'] + 1}" and candidate['blockerObjectId'] == leg['targetObjectId'], 'Coplanar case identity differs'
        assert candidate['supportObjectId'] == leg['originalSupportObjectId'] and all(abs(a-b)<.002 for a,b in zip(candidate['eyeCm'][:2],leg['startXYCm'])), 'Coplanar start differs'
        axis = next(i for i,n in enumerate(candidate['forward']) if abs(n)>.99)
        end = candidate['eyeCm'][:2]
        end[axis] = candidate['cpuNearColliderPlaneCm'] - candidate['forward'][axis]*contract['capsuleRadiusCm']
        assert all(abs(a-b)<.002 for a,b in zip(end,leg['endXYCm'])), 'Coplanar end differs'
        assert leg['allowedSupportObjectIds'] and set(leg['allowedSupportObjectIds']) == {x['objectId'] for x in leg['continuousSupports']}, 'Unknown coplanar references'
        for support in leg['continuousSupports']:
            assert support['objectId'] in floors and support['intervalsNormalized'] == [[0,1]], 'Coplanar reference is not a complete source floor'
            assert support['supportOffsetCm'] == floors[support['objectId']]['supportOffsetCm']
            assert all(abs(z-candidate['cpuFloorTriangleHeightCm']) <= .02 for z in support['effectiveFloorHeightRangeCm']), 'Coplanar floor height differs'
        candidate['allowedSupportObjectIds'] = leg['allowedSupportObjectIds']
        candidate['floorHeightCm'] = candidate['cpuFloorTriangleHeightCm']
        candidate['sourceContinuousSupportProof'] = leg['continuousSupports']
    return {'schemaVersion': 1, 'status': 'source-fixtures-native-unexecuted', 'coordinateSystem': 'unreal-centimeters',
        'sceneSha256': contract['provenance']['sceneSha256'], 'contractSha256': digest(contract_bytes),
        'sourceObjSha256': candidates['sourceObjSha256'], 'candidateFileSha256': digest(candidate_bytes),
        'coplanarProofSha256': digest(proof_bytes),
        'simulationHz': [20,60], 'rateMeaning': 'Fixed simulation steps, not measured rendering FPS.',
        'cases': cases,
        'coverage': {'preparedLegs': len(cases), 'preparedRateCases': len(cases)*2,
            'nativeEntry': False, 'nativeTraversal': False, 'macOSKeyboard': False,
            'exactStepLimitCm': {'value': contract['maxStepHeightCm'], 'status': 'pending-no-threshold-fixture-created'},
            'exactDropLimitCm': {'value': contract['maxDropCm'], 'status': 'pending-no-threshold-fixture-created'}},
        'pendingSourceCandidates': [{k:r[k] for k in ('objectId','walkSurfaceId','nativeBoundsCm','supportOffsetCm')}
            for r in contract['walkSurfaces'] if r['walkSurfaceId'].startswith('porch-step')
                or r['supportOffsetCm'] != 0 or 'POOL' in r['walkSurfaceId']]}
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--geometry', type=Path, default=ROOT / 'output/unreal/geometry')
    parser.add_argument('--output', type=Path, default=ROOT / 'output/unreal/traversal-fixtures')
    args = parser.parse_args()
    out = generate((args.geometry / 'walking.json').read_bytes(),
                   (args.output / 'source-candidates.json').read_bytes(),
                   (args.output / 'coplanar-supports.json').read_bytes())
    (args.output / 'cases.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'status':out['status'], 'cases':len(out['cases']), 'sceneSha256':out['sceneSha256']}))
