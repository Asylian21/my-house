"""World-space facade projection; no WPO, time dependency or geometry writes."""
import math

PERIOD_CM = 189.0
PITCH_CM = 5.0
JOINT_CM = .1953125
JOINT_SHADE = .42
NORMAL_STRENGTH = .35
BANDS = (.025, .103, .179, .256, .410, .565, .796, .9475)

# Identical code in every projection node and material. This deliberately has
# no material/object seed: adjacent coplanar source pieces share board phases.
BASIS = '''float3 N = normalize(NormalWS);
float3 T0 = Grain - N * dot(Grain,N);
if (dot(T0,T0) < 1e-8) {
    // Grain is parallel to a narrow end face; choose the least parallel axis.
    float3 A = (abs(N.x) <= abs(N.y) && abs(N.x) <= abs(N.z)) ? float3(1,0,0)
             : ((abs(N.y) <= abs(N.z)) ? float3(0,1,0) : float3(0,0,1));
    T0 = A - N * dot(A,N);
}
float3 T = normalize(T0);
float3 B = normalize(cross(N,T));
'''
COORD = BASIS + 'float3 P = Position - AnchorCm;\nfloat2 Q = float2(dot(P,T),dot(P,B));\n'
CODES = {
    'sampleUV': COORD + '''float board = floor(Q.y / 5.0);
uint h = asuint((int)board) ^ 0x6d2b79f5u;
h ^= h >> 16; h *= 0x7feb352du; h ^= h >> 15; h *= 0x846ca68bu; h ^= h >> 16;
const float bands[8] = {0.025,0.103,0.179,0.256,0.410,0.565,0.796,0.9475};
float phase = float((h >> 8) & 65535u) / 65536.0;
// Wrap only at the texture sampler; explicit gradients omit discontinuous hash/floor.
return float2(Q.x / 189.0 + phase, bands[h & 7u] + frac(Q.y / 5.0) * (5.0 / 189.0));
''',
    'gradientX': COORD + 'return ddx(Q / 189.0);\n',
    'gradientY': COORD + 'return ddy(Q / 189.0);\n',
    'joint': COORD + '''float width = 0.1953125 / 5.0;
float x = Q.y / 5.0 + width * 0.5;
float footprint = max(abs(ddx(x)) + abs(ddy(x)), 1e-5);
float lo = x - footprint * 0.5;
float hi = x + footprint * 0.5;
// Integral of a periodic stripe gives continuous derivative AA, including
// footprints spanning several slats. Its mean remains the source joint ratio.
float ilo = floor(lo)*width + min(frac(lo),width);
float ihi = floor(hi)*width + min(frac(hi),width);
return lerp(1.0,0.42,saturate((ihi-ilo)/footprint));
''',
    'normal': BASIS + '''// Texture import flips OpenGL green and decodes BC5 once.
return normalize(T * MapNormal.x * 0.35 + B * MapNormal.y * 0.35 + N * max(MapNormal.z,0.001));
''',
}
INPUTS = {role: ['Position', 'NormalWS', 'Grain', 'AnchorCm'] for role in
          ('sampleUV', 'gradientX', 'gradientY', 'joint')}
INPUTS['normal'] = ['NormalWS', 'Grain', 'MapNormal']


def basis(normal, grain):
    """CPU analytic counterpart for singularity/orientation tests only."""
    def dot(a, b): return sum(x*y for x, y in zip(a, b))
    def unit(a):
        n = math.sqrt(dot(a, a))
        if not math.isfinite(n) or n <= 0: raise ValueError('Invalid direction')
        return tuple(v/n for v in a)
    n = unit(normal)
    t = tuple(g-nv*dot(grain,n) for g,nv in zip(grain,n))
    if dot(t,t) < 1e-8:
        axis = min(range(3), key=lambda i: abs(n[i]))
        a = tuple(float(i == axis) for i in range(3))
        t = tuple(v-nv*dot(a,n) for v,nv in zip(a,n))
    t = unit(t)
    b = unit((n[1]*t[2]-n[2]*t[1], n[2]*t[0]-n[0]*t[2], n[0]*t[1]-n[1]*t[0]))
    return n,t,b


def board_uv(along_cm, cross_cm):
    board = math.floor(cross_cm/PITCH_CM)
    h = (board & 0xffffffff) ^ 0x6d2b79f5
    h ^= h >> 16; h = (h*0x7feb352d) & 0xffffffff
    h ^= h >> 15; h = (h*0x846ca68b) & 0xffffffff; h ^= h >> 16
    return (along_cm/PERIOD_CM + ((h >> 8) & 65535)/65536,
            BANDS[h & 7] + (cross_cm/PITCH_CM-board)*PITCH_CM/PERIOD_CM)


def joint_shade(cross_cm, footprint_boards):
    w = JOINT_CM/PITCH_CM
    x = cross_cm/PITCH_CM + w*.5
    f = max(abs(footprint_boards), 1e-5)
    def integral(v): return math.floor(v)*w + min(v-math.floor(v),w)
    coverage = min(1,max(0,(integral(x+f*.5)-integral(x-f*.5))/f))
    return 1 + (JOINT_SHADE-1)*coverage
