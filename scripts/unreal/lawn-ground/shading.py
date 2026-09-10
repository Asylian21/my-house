"""Translation-only registered PBR sampling; no WPO/time or normal rotation."""
import math
UV_SCALE=(32133/1400,24497/1400)
# Decode provider roughness as linear data. The undisplaced turf base uses an
# explicit artist effective roughness; this is not vendor/site BRDF calibration.
ROUGHNESS_POLICY={'kind': 'artist-effective-undisplaced-turf', 'input': 'linear-provider-roughness', 'offset': 0.72, 'scale': 0.23, 'bounds': [0.72, 0.95], 'vendorRadiometricCalibration': False}
# Plain barycentric weights are shared by colour, decoded tangent normals and
# perceptual roughness. This is a material blend, not exact BRDF homogenization.
TRI='''float2 cell = floor(UV);
float2 f = UV - cell;
bool upper = f.x + f.y > 1.0;
float3 W = upper ? float3(f.x+f.y-1.0,1.0-f.x,1.0-f.y)
                 : float3(1.0-f.x-f.y,f.x,f.y);
'''
HASH='''uint h = asuint((int)vertex.x) * 0x9e3779b9u ^ asuint((int)vertex.y) * 0x85ebca6bu ^ 0x601226u;
h ^= h >> 16; h *= 0x7feb352du; h ^= h >> 15; h *= 0x846ca68bu; h ^= h >> 16;
float2 offset = float2(h & 65535u,h >> 16) / 65536.0;
return UV + offset;
'''
CODES={'scaledUV':'return UV0 * float2(32133.0/1400.0,24497.0/1400.0);\n',
       'weights':TRI+'return W;\n','gradientX':'return ddx(UV);\n','gradientY':'return ddy(UV);\n'}
for i in range(3):
 lower=('float2(0,0)','float2(1,0)','float2(0,1)')[i]
 upper=('float2(1,1)','float2(0,1)','float2(1,0)')[i]
 CODES['phase'+str(i)]=TRI+'float2 vertex = cell + (upper ? '+upper+' : '+lower+');\n'+HASH
for role in ('color','normal','roughness'):
 suffix='\nfloat lengthSquared = dot(value,value);\nreturn lengthSquared > 1e-12 ? value*rsqrt(lengthSquared) : float3(0,0,1);\n' if role=='normal' else '\nreturn value;\n'
 kind='float' if role=='roughness' else 'float3'
 if role=='roughness':suffix='\nreturn 0.72 + 0.23 * value;\n'
 CODES[role]=kind+' value = A*W.x + B*W.y + C*W.z;'+suffix
INPUTS={k:['UV'] for k in CODES}
INPUTS['scaledUV']=['UV0']
for role in ('color','normal','roughness'):INPUTS[role]=['A','B','C','W']
OUTPUT_TYPES={k:'CMOT_FLOAT2' for k in CODES}
OUTPUT_TYPES.update(weights='CMOT_FLOAT3',color='CMOT_FLOAT3',normal='CMOT_FLOAT3',roughness='CMOT_FLOAT1')

def lattice(uv):
 if len(uv)!=2 or not all(math.isfinite(x) and abs(x)<100000 for x in uv):raise ValueError('Invalid UV')
 x,y=map(math.floor,uv);a,b=uv[0]-x,uv[1]-y
 if a+b>1:return ((a+b-1,1-a,1-b),((x+1,y+1),(x,y+1),(x+1,y)))
 return ((1-a-b,a,b),((x,y),(x+1,y),(x,y+1)))

def offset(vertex):
 x,y=vertex
 h=(((x&0xffffffff)*0x9e3779b9)^((y&0xffffffff)*0x85ebca6b)^0x601226)&0xffffffff
 h^=h>>16;h=(h*0x7feb352d)&0xffffffff;h^=h>>15;h=(h*0x846ca68b)&0xffffffff;h^=h>>16
 return ((h&65535)/65536,(h>>16)/65536)

def samples(uv):
 w,v=lattice(uv)
 return w,tuple(tuple(x+y for x,y in zip(uv,offset(vertex))) for vertex in v)

def blend(values,weights):return sum(v*w for v,w in zip(values,weights))


def effective_roughness(raw):
 if not math.isfinite(raw) or not 0 <= raw <= 1:raise ValueError("Invalid linear provider roughness")
 return 0.72 + 0.23 * raw
