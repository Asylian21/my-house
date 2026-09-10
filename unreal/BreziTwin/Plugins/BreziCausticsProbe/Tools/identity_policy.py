"""Reviewed, source-pinned float32 identity ambiguity for diagnostic terminal flux only.

Never rewrites photon records or equates production BRDF/material/floor identities.
Changing the exact policy bytes requires a reviewed update of both independent pins.
"""
import hashlib
import json
import math
import struct
from pathlib import Path

REVIEWED_POLICY_SHA256 = 'eebb440994ea88ed58a358e3412b5c72cf4ea72fffb701186ac904dbed17bd43'
UNEXPLAINED_MISMATCH_THRESHOLD = 0.001
FLOOR_ID = 'DOM_01720'
TERMINAL = 'nonfloor-first-hit-terminal-flux'
MAX_POINT_ERROR_METRES = 0.000002  # ceiling; local quantization/ULP budget must also pass
MAX_DIRECTION_COMPONENT = 0.999999999999


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def ulp32(value):
    value = abs(f32(value))
    bits = struct.unpack('<I', struct.pack('<f', value))[0]
    if bits >= 0x7f7fffff:
        return math.inf
    return struct.unpack('<f', struct.pack('<I', bits + 1))[0] - value


def dot(a, b): return sum(x*y for x, y in zip(a, b))
def sub(a, b): return tuple(x-y for x, y in zip(a, b))
def add(a, b): return tuple(x+y for x, y in zip(a, b))
def mul(a, s): return tuple(x*s for x in a)
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def length(a): return math.sqrt(dot(a, a))


def normal(triangle):
    a, b, c = triangle['verticesMetres']
    n = cross(sub(b, a), sub(c, a))
    size = length(n)
    if size <= 1e-20:
        raise ValueError('degenerate source triangle')
    return mul(n, 1/size)


def quantization(triangle):
    return [[abs(f32(value)-value) for value in v] for v in triangle['verticesMetres']]


def pair_certificate(a, b, receiver_classes):
    """Strictly bounded pair proof. Public only so rejection predicates can be adversarially tested."""
    if a['objectId'] == b['objectId']:
        raise ValueError('same object is not a cross-object ambiguity')
    if FLOOR_ID in [a['objectId'], b['objectId']]:
        raise ValueError('floor receiver can never be equivalent')
    if any(receiver_classes.get(t['objectId']) != TERMINAL for t in [a, b]):
        raise ValueError('different or unsupported optical receiver class')
    na, nb = normal(a), normal(b)
    if dot(na, nb) < 1-1e-12:
        raise ValueError('different signed source normals')
    # First reviewed policy is deliberately limited to axis-aligned flat pairs.
    # A general oblique interval plane proof is a future review, not an implicit extension.
    axes = [i for i, value in enumerate(na) if abs(value) >= MAX_DIRECTION_COMPONENT]
    if len(axes) != 1:
        raise ValueError('unreviewed oblique near-coincident pair')
    axis = axes[0]
    pa, pb = a['verticesMetres'][0][axis], b['verticesMetres'][0][axis]
    if not all(v[axis] == pa for v in a['verticesMetres']) or not all(v[axis] == pb for v in b['verticesMetres']):
        raise ValueError('nonplanar source plane')
    if f32(pa) != f32(pb):
        raise ValueError('planes do not collapse to the same uploaded float32 value')
    qa, qb = quantization(a), quantization(b)
    plane_bound = max(v[axis] for v in qa) + max(v[axis] for v in qb)
    if abs(pa-pb) > plane_bound + math.ulp(pa) + math.ulp(pb):
        raise ValueError('separation exceeds exact per-vertex quantization bound')
    return {'axis': axis, 'signedNormal': na, 'planeSourceA': pa, 'planeSourceB': pb,
            'uploadedPlane': f32(pa), 'sourcePlaneSeparationMetres': abs(pa-pb),
            'planeQuantizationBoundMetres': plane_bound,
            'vertexQuantizationAMetres': qa, 'vertexQuantizationBMetres': qb,
            'receiverClass': TERMINAL}


def intersect(origin, direction, triangle):
    a, b, c = triangle['verticesMetres']
    e1, e2 = sub(b, a), sub(c, a)
    p = cross(direction, e2)
    det = dot(e1, p)
    if abs(det) < 1e-12:
        return None
    delta = sub(origin, a)
    u = dot(delta, p)/det
    q = cross(delta, e1)
    v = dot(direction, q)/det
    t = dot(e2, q)/det
    # Only float64 bookkeeping tolerance; no global pixel/world tolerance for candidate membership.
    if u < -1e-12 or v < -1e-12 or u+v > 1+1e-12 or t <= 1e-7:
        return None
    return {'distance': t, 'point': add(origin, mul(direction, t)), 'barycentric': [1-u-v, u, v]}


def classify_pair(origin, direction, photon, a, b, receiver_classes):
    proof = pair_certificate(a, b, receiver_classes)
    if len(photon) != 12 or not all(math.isfinite(v) for v in photon):
        raise ValueError('invalid photon record')
    if photon[3] != 1:
        raise ValueError('nonfloor status required; no floor/escape reclassification')
    if len(origin) != 3 or len(direction) != 3 or not all(math.isfinite(v) for v in (*origin, *direction)):
        raise ValueError('nonfinite source ray')
    if abs(length(direction)-1) > 1e-10:
        raise ValueError('source ray must be normalized')
    incidence = abs(dot(direction, proof['signedNormal']))
    if incidence < .25:
        raise ValueError('grazing rays require separate numerical review')
    ha, hb = intersect(origin, direction, a), intersect(origin, direction, b)
    if ha is None or hb is None:
        raise ValueError('source ray does not intersect both exact source triangle footprints')
    distance_bound = proof['planeQuantizationBoundMetres']/incidence
    # The exact axis-plane depth gap is separation / incidence. Pair certification
    # already proves separation <= the two exact rounding errors. Subtracting two
    # independently evaluated Moller distances adds irrelevant float64 cancellation.
    source_depth_gap = proof['sourcePlaneSeparationMetres']/incidence
    if source_depth_gap > distance_bound:
        raise ValueError('source first-hit depth gap exceeds pair quantization bound')
    # Position arithmetic/readback allows at most two float32 ULPs per coordinate
    # plus actual uploaded vertex error and projected source-plane collapse.
    # This is a narrow reviewed comparator budget, not a proof of arbitrary GPU instruction error.
    qa, qb = proof['vertexQuantizationAMetres'], proof['vertexQuantizationBMetres']
    budget = [max(v[i] for v in qa+qb) + 2*max(ulp32(ha['point'][i]), ulp32(hb['point'][i]))
              + abs(direction[i])*distance_bound for i in range(3)]
    if max(budget) > MAX_POINT_ERROR_METRES:
        raise ValueError('local ULP budget exceeds absolute reviewed cap')
    for hit in [ha, hb]:
        if any(abs(photon[i]-hit['point'][i]) > budget[i] for i in range(3)):
            raise ValueError('GPU hit lies outside source-derived per-axis quantization/ULP bound')
        if math.dist(photon[:3], hit['point']) > MAX_POINT_ERROR_METRES:
            raise ValueError('GPU hit exceeds absolute source point cap')
    path_budget = distance_bound + 2*max(ulp32(ha['distance']), ulp32(hb['distance']))
    if min(abs(photon[7]-h['distance']) for h in [ha, hb]) > path_budget:
        raise ValueError('GPU path lies outside source-derived depth bound')
    return {**proof, 'pointBudgetMetres': budget, 'pathBudgetMetres': path_budget,
            'sourceRayDistanceA': ha['distance'], 'sourceRayDistanceB': hb['distance'],
            'analyticSourceDepthGapMetres': source_depth_gap,
            'sourceRayHitA': ha['point'], 'sourceRayHitB': hb['point'],
            'observedPointDifferenceMetres': math.dist(photon[:3], ha['point']),
            'outcome': 'listed-f32-ambiguous-nonfloor-identity',
            'productionUseAllowed': False, 'sourceIdentityRewritten': False}


class IdentityPolicy:
    def __init__(self, contract_path, policy_path, reference_module):
        raw = Path(contract_path).read_bytes()
        policy_raw = Path(policy_path).read_bytes()
        if hashlib.sha256(policy_raw).hexdigest() != REVIEWED_POLICY_SHA256:
            raise ValueError('Unreviewed identity policy bytes')
        self.policy = json.loads(policy_raw)
        if self.policy['unexplainedMismatchThreshold'] != UNEXPLAINED_MISMATCH_THRESHOLD or self.policy['floorEquivalenceAllowed'] is not False:
            raise ValueError('Identity policy transport boundary changed')
        if hashlib.sha256(raw).hexdigest() != self.policy['sourceContractSha256']:
            raise ValueError('unreviewed receiver contract')
        self.contract = json.loads(raw)
        self.triangles = self.contract['triangles']
        self.object_ids = [r['id'] for r in self.contract['receiverObjects']]
        self.classes = self.policy['reviewedReceiverClasses']
        self.candidate_indices = set()
        for item in self.policy['reviewedTriangles']:
            i = item['index']
            if type(i) is not int or not 0 <= i < len(self.triangles) or digest(self.triangles[i]) != item['triangleSha256']:
                raise ValueError('unreviewed candidate triangle bytes')
            if [self.triangles[i]['objectId'], self.triangles[i]['sourceFaceIndex']] != item['identity']:
                raise ValueError('source candidate identity changed')
            self.candidate_indices.add(i)
        self.pairs = {tuple(pair) for pair in self.policy['reviewedDirectedPairs']}
        for ia, ib in self.pairs:
            if ia not in self.candidate_indices or ib not in self.candidate_indices:
                raise ValueError('pair is outside reviewed candidate set')
            pair_certificate(self.triangles[ia], self.triangles[ib], self.classes)
        bvh_triangles = []
        for t in self.triangles:
            a,b,c=t['verticesMetres']
            bvh_triangles.append({'a':a,'e1':sub(b,a),'e2':sub(c,a),'low':tuple(min(v[i] for v in [a,b,c]) for i in range(3)),'high':tuple(max(v[i] for v in [a,b,c]) for i in range(3))})
        self.bvh = reference_module.BVH(bvh_triangles)

    def explain(self, origin, direction, photon, expected_index):
        # The caller may not choose a convenient pair behind a different source blocker.
        hit, distance = self.bvh.first(origin, direction)
        if hit is None or hit[0] != expected_index:
            raise ValueError('claimed CPU triangle is not the independent source first hit')
        index = int(photon[10])
        oi = int(photon[9])
        if index != photon[10] or oi != photon[9] or not 0 <= oi < len(self.object_ids):
            raise ValueError('invalid exact GPU triangle/object indices')
        if (expected_index, index) not in self.pairs:
            raise ValueError('foreign triangle or unreviewed pair')
        if self.triangles[index]['objectId'] != self.object_ids[oi]:
            raise ValueError('GPU triangle belongs to another object')
        return classify_pair(origin, direction, photon, self.triangles[expected_index], self.triangles[index], self.classes)
