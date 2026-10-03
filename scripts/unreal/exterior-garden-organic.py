"""Artist geometry study: attached white flowers and irregular broadleaf clumps.

Only four white hero rows and 420 lower clump rows receive proposed new mesh IDs.
All 473 garden roots/yaws/scales and original beds remain exact. Existing leaf,
shoot and cream plume recipes/maps are reused unedited. CPU previews of decoded
GLB triangles are anatomical studies, not native appearance or surveyed botany.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import struct

import numpy as np
from PIL import Image, ImageDraw
import shapely
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-organic.py'
OUTPUT = ROOT/'output/unreal/exterior-garden-organic-20261001-r1-study'
REPORT = ROOT/'output/unreal/exterior-20261001-r10/exterior-import-report.json'
GARDEN = ROOT/'output/unreal/exterior-garden-flower-masters-20260930-r1c/garden-plan.json'
LIBRARY = ROOT/'output/unreal/exterior-assets-greenery-20260930-r5/geometry-manifest.json'
MATERIALS = LIBRARY.parent/'material-manifest.json'
HELPER = ROOT/'scripts/unreal/exterior-garden-masters.py'
HELPER_SHA = '7e40c7a09f2fe0b02ff6b7c8d875e8b1aecccf164d2544572c542de865461254'
LEAF_UV = (.28, .30, .73, .74)
ALLOWED = ('garden_blade_green', 'garden_plume_silk', 'regional_green_leaf')
MAPPING = {'ornamental_white_a': 'garden_white_organic_a', 'ornamental_white_b': 'garden_white_organic_b',
    'garden_rosette_r3_a': 'garden_broadleaf_organic_a', 'garden_rosette_r3_b': 'garden_broadleaf_organic_b'}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def pin(path): return {'path': str(Path(path).resolve()), 'sha256': sha(path)}
def require(ok, text):
    if not ok: raise ValueError(text)
def write(path, value):
    with Path(path).open('x') as stream: json.dump(value, stream, separators=(',', ':'), allow_nan=False); stream.write('\n')


require(sha(HELPER) == HELPER_SHA, 'Frozen garden GLB exporter changed')
spec = importlib.util.spec_from_file_location('frozen_organic_mesh', HELPER)
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
base.OWNER = OWNER  # In-memory exporter label; the frozen source is never written.
add, sub, mul, unit, cross = base.add, base.sub, base.mul, base.unit, base.cross


class Organic:
    def __init__(self):
        self.mesh = base.Mesh(); self.branches = []; self.leaves = []; self.flowers = []

    def tube(self, path, radius, parent=None, parent_t=None, kind='shoot', tone=.88, sides=5):
        index = len(self.branches)
        self.mesh.tube('garden_blade_green', path, radius, [tone*.93, tone, tone*.92, 1.], sides=sides)
        self.branches.append({'id': index, 'pathCm': path, 'parent': parent, 'parentT': parent_t,
            'kind': kind, 'radiusCm': radius})
        return index

    def leaf(self, anchor, direction, length, width, curl, twist, age, parent, lod):
        axis = np.array(unit(direction)); side = np.array(unit(cross(axis.tolist(), [0, 0, 1] if abs(axis[2]) < .96 else [0, 1, 0])))
        normal = np.cross(side, axis); count = (7, 5, 4)[lod]
        part = self.mesh.parts.setdefault('regional_green_leaf', {'positions': [], 'uv': [], 'triangles': [], 'colors': []})
        start = len(part['positions']); first_triangle = len(part['triangles'])
        points, uv, triangles, centers = [list(anchor)], [[.505, LEAF_UV[3]]], [], [list(anchor)]
        for j in range(1, count):
            t = j/count; roll = twist*t
            lateral = side*math.cos(roll)+normal*math.sin(roll)
            surface = np.cross(lateral, axis)
            middle = np.asarray(anchor)+axis*length*t+normal*(curl*length*math.sin(math.pi*.88*t))
            middle += side*(.028*length*math.sin(math.pi*t)*(1 if twist >= 0 else -1))
            span = width*math.sin(math.pi*t)**.78
            for k in range(3):
                x = k-1
                fold = span*(.11*(1-abs(x))+.025*x*x)*math.sin(math.pi*t)
                points.append((middle+lateral*x*span*.5+surface*fold).tolist())
                uv.append([LEAF_UV[0]+(LEAF_UV[2]-LEAF_UV[0])*k/2, LEAF_UV[3]-(LEAF_UV[3]-LEAF_UV[1])*t])
            centers.append(middle.tolist())
        tip = np.asarray(anchor)+axis*length+normal*(curl*length*math.sin(math.pi*.88))
        tip_index = len(points); points.append(tip.tolist()); uv.append([.505, LEAF_UV[1]]); centers.append(tip.tolist())
        triangles.extend([(0, 2, 1), (0, 3, 2)])
        for j in range(count-2):
            a = 1+j*3; b = a+3
            triangles.extend([(a,a+1,b), (a+1,b+1,b), (a+1,a+2,b+1), (a+2,b+2,b+1)])
        a = 1+(count-2)*3
        triangles.extend([(a,a+1,tip_index), (a+1,a+2,tip_index)])
        self.mesh.geometry('regional_green_leaf', points, uv, triangles, [1.,1.,1.,1.])
        self.leaves.append({'parentPetiole': parent, 'anchorCm': list(anchor), 'direction': direction,
            'lengthCm': length, 'widthCm': width, 'curlRatio': curl, 'twistRad': twist, 'age': age,
            'vertexOffset': start, 'vertexCount': len(points), 'triangleOffset': first_triangle,
            'triangleCount': len(triangles), 'centerlineCm': centers, 'pointedTip': True,
            'materialKey': 'regional_green_leaf', 'uvRect': LEAF_UV})

    def petals(self, center, axis, size, phase, parent, lod):
        n = unit(axis); a = unit(cross(n, [0,0,1] if abs(n[2]) < .96 else [0,1,0])); b = unit(cross(n,a))
        self.tube([center,add(center,mul(n,-size*.16))],size*.13,parent,1.,'flower-receptacle',tone=.83,sides=5)
        key = 'garden_plume_silk'; start = len(self.mesh.parts.get(key, {}).get('positions', []))
        for petal in range(4):
            angle = phase+petal*math.tau/4
            radial = add(mul(a, math.cos(angle)), mul(b, math.sin(angle)))
            lateral = add(mul(a, -math.sin(angle)), mul(b, math.cos(angle)))
            points, uv, triangles, colors = [], [], [], []
            for j, t in enumerate((0., .50, 1.)):
                width = size*(.10 if j == 0 else .43 if j == 1 else .14)
                for k in range(3):
                    x = k-1
                    cup = size*(-.16*(1-t)**2+.04*math.sin(math.pi*t)+.18*t*t+.12*x*x*math.sin(math.pi*t))
                    p = add(center, add(mul(radial, size*(.10+.90*t)), add(mul(lateral,x*width),mul(n,cup))))
                    points.append(p); uv.append([k/2,t])
                    shade = .82+.14*t
                    colors.append([shade*.93,shade*.96,shade,1.])
            for j in range(2):
                for k in range(2):
                    i = j*3+k; q = i+3
                    triangles.extend([(i,i+1,q), (i+1,q+1,q)])
            self.mesh.geometry(key, points, uv, triangles, [1.,1.,1.,1.])
            self.mesh.parts[key]['colors'][-len(points):] = colors
        self.flowers.append({'parentPedicel': parent, 'centerCm': center, 'axis': axis, 'radiusCm': size,
            'petalCount': 4, 'vertexOffset': start, 'vertexCount': 36, 'triangleCount': 32,
            'materialKey': key, 'actualCuppedPetals': True})

    def fit(self, height, radius):
        points = np.array([p for part in self.mesh.parts.values() for p in part['positions']])
        low, high = points[:,2].min(), points[:,2].max()
        scale = min(height/(high-low), radius/np.linalg.norm(points[:,:2],axis=1).max())
        def transform(p): return [p[0]*scale, p[1]*scale, (p[2]-low)*scale]
        for part in self.mesh.parts.values(): part['positions'] = [transform(p) for p in part['positions']]
        for row in self.branches:
            row['pathCm'] = [transform(p) for p in row['pathCm']]; row['radiusCm'] *= scale
        for row in self.leaves:
            row['anchorCm'] = transform(row['anchorCm']); row['centerlineCm'] = [transform(p) for p in row['centerlineCm']]
            row['lengthCm'] *= scale; row['widthCm'] *= scale
        for row in self.flowers: row['centerCm'] = transform(row['centerCm']); row['radiusCm'] *= scale
        return {'appliedIsotropicScale': scale, 'originalMinimumZCm': float(low),
            'leafCount': len(self.leaves), 'flowers': len(self.flowers), 'branches': self.branches,
            'leaves': self.leaves, 'inflorescences': self.flowers,
            'artistInterpretation': 'Illustrative garden shrub/broadleaf growth; no site species census or surveyed botany.'}


def curve(path, t):
    f = t*(len(path)-1); i = min(int(f),len(path)-2); s = f-i
    return add(mul(path[i],1-s),mul(path[i+1],s))


def white(variant, lod):
    rng = random.Random(6010010900+variant*179); model = Organic(); nodes = []
    main = [[0.,0.,0.],[-.6+variant*.7,.5,21.],[1.3, -.9,42.],[-.6,1.1,64.]]
    main_id = model.tube(main, .47, kind='rooted-main', sides=(6,5,4)[lod])
    for index in range(12+variant*2):
        t = .04+.022*index; root = curve(main,t); az = rng.uniform(-math.pi,math.pi)
        reach = rng.uniform(30,44)*(1.1 if math.cos(az-.3)>.3 else .90)
        top = [root[0]+reach*math.cos(az), root[1]+reach*math.sin(az), rng.uniform(55,74)]
        middle = add(root,mul(sub(top,root),.53)); middle[2] += rng.uniform(1.2,3.4)
        path = [root,middle,top]; branch = model.tube(path,rng.uniform(.21,.31),main_id,t,'flowering-shoot',sides=(5,4,4)[lod])
        nodes.append((path,branch,az,index))
        for level, node_t in enumerate((.13,.27,.42,.57,.73,.87)):
            anchor = curve(path,node_t); phase = az+level*1.7+rng.uniform(-.37,.37)
            for opposite in (0,1):
                theta = phase+opposite*math.pi+rng.uniform(-.15,.15)
                direction = [math.cos(theta),math.sin(theta),rng.uniform(-.16,.28)]
                end = add(anchor,mul(unit(direction),rng.uniform(.65,1.15)))
                petiole = model.tube([anchor,end],.061,branch,node_t,'leaf-petiole',sides=3)
                length = rng.uniform(6.3,10.2)*(1-.08*level)
                model.leaf(end,direction,length,length*rng.uniform(.44,.59),rng.uniform(-.035,.13),
                    rng.uniform(-.35,.35),'young' if level>=4 else 'mature',petiole,lod)
        if index%3 != 1:
            start = curve(path,.61); theta = az+(-1 if index%2 else 1)*rng.uniform(.75,1.1)
            end = add(start,[rng.uniform(7.,10.)*math.cos(theta),rng.uniform(7.,10.)*math.sin(theta),rng.uniform(9.,14.)])
            subpath = [start,add(start,mul(sub(end,start),.52)),end]
            child = model.tube(subpath,.13,branch,.61,'axillary-shoot',sides=(4,4,3)[lod])
            nodes.append((subpath,child,theta,index+20))
            for node_t in (.36,.70):
                center = curve(subpath,node_t)
                for opposite in (0,1):
                    theta_leaf = theta+math.pi/2+opposite*math.pi+rng.uniform(-.22,.22)
                    direction = [math.cos(theta_leaf),math.sin(theta_leaf),rng.uniform(-.15,.35)]
                    end_leaf = add(center,mul(unit(direction),.65))
                    petiole = model.tube([center,end_leaf],.045,child,node_t,'leaf-petiole',sides=3)
                    model.leaf(end_leaf,direction,rng.uniform(4.5,6.7),rng.uniform(2.2,3.5),rng.uniform(.025,.15),
                        rng.uniform(-.38,.38),'young',petiole,lod)
    for path, branch, az, index in nodes:
        root = path[-1]; spread = rng.uniform(3.2,4.5)
        for floret in range(8+index%3):
            phi = rng.uniform(-math.pi,math.pi); radial = spread*math.sqrt(rng.random())
            center = add(root,[radial*math.cos(phi),radial*math.sin(phi),rng.uniform(1.3,3.8)])
            middle = add(root,mul(sub(center,root),.57)); middle[2] += .28
            pedicel = model.tube([root,middle,center],.035,branch,1.,'floret-pedicel',tone=.87,sides=3)
            axis = [rng.uniform(-.3,.3),rng.uniform(-.3,.3),1.]
            model.petals(center,axis,rng.uniform(.76,1.08),phi,pedicel,lod)
    proof = model.fit(77.8,55.5)
    return model.mesh, proof


def clump(variant, lod):
    rng = random.Random(6010012000+variant*131); model = Organic()
    root = [[0.,0.,0.],[3.7,-1.8,.17],[7.6,-3.1,.24]] if variant == 0 else [[0.,0.,0.],[2.8,1.6,.17],[6.8,3.1,.24]]
    root_id = model.tube(root,.085,kind='creeping-root',sides=(4,4,3)[lod])
    counts = (5,6,5) if variant == 0 else (5,6,7,5)
    for shoot, count in enumerate(counts):
        t = .16+.21*shoot; anchor = curve(root,t); phase = rng.uniform(-math.pi,math.pi)
        end = add(anchor,[rng.uniform(1.2,3.0)*math.cos(phase),rng.uniform(1.2,3.0)*math.sin(phase),rng.uniform(1.0,2.2)])
        stem = [anchor,add(anchor,mul(sub(end,anchor),.47)),end]
        branch = model.tube(stem,.064,root_id,t,'broadleaf-shoot',sides=3)
        for index in range(count):
            node_t = .22+.73*index/max(1,count-1); center = curve(stem,node_t)
            az = phase+index*2.22+rng.uniform(-.53,.53)
            age = 'young' if index==count-1 else 'mature' if index%3 else 'older'
            vertical = rng.uniform(.70,.94) if age=='young' else rng.uniform(-.015,.21)
            direction = [math.cos(az),math.sin(az),vertical]
            tip = add(center,mul(unit(direction),rng.uniform(.75,1.9)))
            petiole = model.tube([center,add(center,mul(sub(tip,center),.53)),tip],.032,branch,node_t,'leaf-petiole',sides=3)
            length = rng.uniform(5.8,7.8) if age=='young' else rng.uniform(8.,13.6)
            width = length*rng.uniform(.39,.60)
            model.leaf(tip,direction,length,width,rng.uniform(-.08,.12) if age!='young' else rng.uniform(.05,.12),
                rng.uniform(-.47,.47),age,petiole,lod)
    proof = model.fit(9.3,23.5)
    return model.mesh, proof


def decode_glb(path):
    raw = Path(path).read_bytes(); magic, version, length = struct.unpack_from('<4sII',raw)
    require((magic,version,length)==(b'glTF',2,len(raw)), 'Bad GLB header')
    count, kind = struct.unpack_from('<II',raw,12); require(kind==0x4e4f534a,'No GLB JSON')
    doc = json.loads(raw[20:20+count]); size, kind = struct.unpack_from('<II',raw,20+count)
    require(kind==0x004e4942 and 28+count+size==len(raw),'No GLB binary'); binary=raw[28+count:]
    def values(index):
        a=doc['accessors'][index]; v=doc['bufferViews'][a['bufferView']]; width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
        stride=v.get('byteStride',np.dtype(dtype).itemsize*width)
        arr=np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(stride,np.dtype(dtype).itemsize)).astype(float)
        if a.get('normalized'): arr/=255 if a['componentType']==5121 else 65535
        return arr
    result={}
    for node in doc['nodes']:
        parts=[]
        for p in doc['meshes'][node['mesh']]['primitives']:
            a=p['attributes']; tangent=values(a['TANGENT']) if 'TANGENT' in a else None
            parts.append({'materialKey':doc['materials'][p['material']]['name'],
                'positionsCm':values(a['POSITION'])[:,[0,2,1]]*100,
                'normals':values(a['NORMAL'])[:,[0,2,1]],
                'tangents':np.column_stack([tangent[:,:3][:,[0,2,1]],-tangent[:,3]]) if tangent is not None else None,
                'uv':values(a['TEXCOORD_0']), 'colors':values(a['COLOR_0']) if 'COLOR_0' in a else np.ones((len(values(a['POSITION'])),4)),
                'triangles':values(p['indices']).astype(int).reshape(-1,3)[:,[0,2,1]]})
        result[node['name']]=parts
    return doc,result


def textures(recipes):
    result={}
    for key,r in recipes.items():
        if not r.get('maps'): continue
        with Image.open(r['maps']['albedo']['path']) as im: rgb=np.array(im.convert('RGB'),dtype=float)/255
        linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
        alpha=None
        if r['maps'].get('alpha'):
            with Image.open(r['maps']['alpha']['path']) as im: alpha=np.array(im.convert('L'),dtype=float)/255
        result[key]=(linear,alpha)
    return result


def render(parts, row, recipes, maps, compact=False, side=False):
    w,h=600,620; rgb=np.full((h,w,3),[.19,.19,.17]); depth=np.full((h,w),-np.inf)
    eye=np.array([.18,.93,.31 if side else .68]);eye/=np.linalg.norm(eye)
    right=np.array([eye[1],-eye[0],0.]);right/=np.linalg.norm(right);up=np.cross(right,eye)
    light=np.array([-.43,-.68,1.]);light/=np.linalg.norm(light)
    pixels_per_cm=18 if compact else 7.2; centered_z=4 if compact else 25
    angle=math.radians(row['yawDeg']);c,s=math.cos(angle),math.sin(angle);rotation=np.array([[c,s],[-s,c]])
    for part in parts:
        key=part['materialKey'];recipe=recipes[key];p=part['positionsCm'].copy()*row['uniformScale'];n=part['normals'].copy()
        p[:,:2]=p[:,:2]@rotation;n[:,:2]=n[:,:2]@rotation;p[:,2]-=centered_z
        screen=np.column_stack([p@right*pixels_per_cm+w/2,h*.57-p@up*pixels_per_cm,p@eye])
        for face in part['triangles']:
            q=screen[face];lo=np.maximum(np.floor(q[:,:2].min(axis=0)).astype(int),[0,0]);hi=np.minimum(np.ceil(q[:,:2].max(axis=0)).astype(int),[w-1,h-1])
            if np.any(hi<lo):continue
            x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
            den=(q[1,1]-q[2,1])*(q[0,0]-q[2,0])+(q[2,0]-q[1,0])*(q[0,1]-q[2,1])
            if abs(den)<1e-10:continue
            a=((q[1,1]-q[2,1])*(x-q[2,0])+(q[2,0]-q[1,0])*(y-q[2,1]))/den
            b=((q[2,1]-q[0,1])*(x-q[2,0])+(q[0,0]-q[2,0])*(y-q[2,1]))/den;weights=np.stack([a,b,1-a-b],axis=-1)
            z=weights@q[:,2];current=depth[lo[1]:hi[1]+1,lo[0]:hi[0]+1];inside=(weights.min(axis=-1)>=-1e-8)&(z>current)
            if not inside.any():continue
            if key in maps:
                photo,alpha=maps[key];uv=weights@part['uv'][face]
                u=np.clip(np.rint(uv[:,:,0]*(photo.shape[1]-1)).astype(int),0,photo.shape[1]-1)
                v=np.clip(np.rint(uv[:,:,1]*(photo.shape[0]-1)).astype(int),0,photo.shape[0]-1)
                color=photo[v,u]*recipe.get('albedoScale',1.)*np.array(recipe.get('tint',[1,1,1]))
                if alpha is not None:
                    au=np.clip(np.rint(uv[:,:,0]*(alpha.shape[1]-1)).astype(int),0,alpha.shape[1]-1)
                    av=np.clip(np.rint(uv[:,:,1]*(alpha.shape[0]-1)).astype(int),0,alpha.shape[0]-1)
                    inside&=alpha[av,au]>=recipe.get('opacityMaskClipValue',.333)
            else:color=(weights@part['colors'][face][:,:3])*np.array(recipe['linearColor'])
            normal=weights@n[face];normal/=np.maximum(np.linalg.norm(normal,axis=-1,keepdims=True),1e-12)
            diffuse=.27+1.25*np.abs(normal@light)
            rgb[lo[1]:hi[1]+1,lo[0]:hi[0]+1][inside]=np.clip(color*diffuse[:,:,None],0,1)[inside];current[inside]=z[inside]
    display=np.where(rgb<=.0031308,rgb*12.92,1.055*rgb**(1/2.4)-.055)
    return Image.fromarray(np.clip(display*255,0,255).astype('uint8'))


def build(output=OUTPUT):
    output=Path(output).resolve();require(output==OUTPUT and not output.exists(),'Use fresh isolated immutable organic garden study output')
    report,garden,library,all_materials=map(read,(REPORT,GARDEN,LIBRARY,MATERIALS))
    require(report['savedReloaded'] and report['gardenPlanting']['instances']==461 and report['gardenPlanting']['ornamentalReplacements']==12,'R10 completed garden basis differs')
    require(report['plantGeometryManifest']==str(LIBRARY) and len(library['meshes'])==96,'Exact current96 master basis differs')
    for path in (GARDEN,LIBRARY,MATERIALS,HELPER):require(report['inputFiles'].get(str(path),report['pipelineFiles'].get(str(path)))==sha(path),'R10 source pin differs: '+str(path))
    require(garden['activeDesign']==report['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'},'C/B/B differs')
    require(garden['housePlacement']['streetSetbackMm']==garden['housePlacement']['eastSetbackMm']==3000,'Required setbacks differ')
    inputs={str(p):sha(p)for p in (Path(__file__),HELPER,REPORT,GARDEN,LIBRARY,MATERIALS)}
    for p in (ROOT/'output/unreal/realism-20260926-r5/geometry/scene.json',ROOT/'output/unreal/realism-20260926-r5/geometry/dom-mm.obj'):
        require(report['inputFiles'][str(p)]==sha(p),'Source architecture witness differs');inputs[str(p)]=sha(p)
    recipes={k:deepcopy(all_materials[k])for k in ALLOWED}
    for key in (*ALLOWED,'ph_shrub_01_ornamental'):
        for entry in all_materials[key].get('maps',{}).values():require(sha(entry['path'])==entry['sha256'],'Existing photo changed');inputs[entry['path']]=entry['sha256']
    old={r['id']:r for r in library['meshes'] if r['id'] in MAPPING};require(len(old)==4,'Old selected master inventory differs')
    for row in old.values():require(sha(row['glbPath'])==row['glbSha256'],'Old master geometry changed');inputs[row['glbPath']]=row['glbSha256']
    for name in ('lawn-tapered-plan.json','lawn-tapered-manifest.json','geometry-validation.json'):
        path=ROOT/'output/unreal/exterior-lawn-tapered-20261001-r2-study'/name;inputs[str(path)]=sha(path)
    output.mkdir(parents=True);meshes=[];lods=[];geometry=[];morphology={}
    for source,new_id in MAPPING.items():
        variant=0 if source.endswith('_a')else 1;white_kind=source.startswith('ornamental_white');rows=[];proofs=[]
        for lod in range(3):
            mesh,proof=(white if white_kind else clump)(variant,lod);points=np.array([p for part in mesh.parts.values()for p in part['positions']])
            triangles=sum(len(part['triangles'])for part in mesh.parts.values());require(triangles<=20000,'Fresh owned garden master exceeded20k triangles')
            row={'level':lod,'nodeName':new_id+'_LOD'+str(lod),'vertices':len(points),'triangles':triangles,
                'expectedBoundsCm':{'min':points.min(axis=0).tolist(),'max':points.max(axis=0).tolist()},
                'radialEnvelopeCm':float(np.linalg.norm(points[:,:2],axis=1).max()),'derivation':'Actual connected branch/petiole tubes and curved folded individual photographic leaves; real cupped cream florets'}
            rows.append(row);lods.append(row);geometry.append(mesh);proofs.append(proof)
        meshes.append({'id':new_id,'sourceMeshId':source,'role':old[source]['role'],'form':old[source].get('form'),
            'flowerColor':'white'if white_kind else None,'placementPolicy':'explicit-only','heightCm':max(l['expectedBoundsCm']['max'][2]for l in rows),
            'materialKeys':sorted(geometry[-1].parts),'lods':rows,'composition':'Artist interpretation, not surveyed site botany or scanned whole-plant geometry.'})
        morphology[new_id]=proofs
    base.PALETTES={k:recipes[k]['linearColor']for k in ALLOWED if recipes[k].get('linearColor')}
    glb=output/'garden-organic.glb';base.write_glb(glb,lods,geometry)
    _,decoded=decode_glb(glb)
    for mesh in meshes:
        mesh.update(glbPath=str(glb),glbSha256=sha(glb))
        for lod in mesh['lods']:
            parts=decoded[lod['nodeName']];p=np.concatenate([part['positionsCm']for part in parts]);lod.update(
                expectedBoundsCm={'min':p.min(axis=0).tolist(),'max':p.max(axis=0).tolist()},radialEnvelopeCm=float(np.linalg.norm(p[:,:2],axis=1).max()))
    manifest={'schema':1,'owner':OWNER,'generatorSha256':sha(__file__),'units':'metres','axes':'glTF Y-up; Unreal native = [100*x,100*z,100*y]',
        'status':'MEASURED_ARTIST_ORGANIC_GARDEN_STUDY_NOT_NATIVE_ACCEPTED','meshes':meshes,'inputFiles':inputs,'sourceLibrary':pin(LIBRARY)}
    write(output/'geometry-manifest.json',manifest);write(output/'material-manifest.json',recipes);write(output/'morphology-audit.json',morphology)
    write(output/'asset-manifest.json',{'schema':1,'owner':OWNER,'inputFiles':inputs,'sourceLibrary':pin(LIBRARY),
        'sources':[{'kind':'original-authored-branch-leaf-and-floret-geometry','generator':OWNER,'license':'Original project asset'},
            {'kind':'unchanged-photographic-individual-leaf','sourceUrl':recipes['regional_green_leaf']['sourceUrl'],
             'license':recipes['regional_green_leaf']['license'],'maps':recipes['regional_green_leaf']['maps']}],
        'scope':'Four explicit new garden masters only; exact existing leaf/shoot/plume recipes, no original atlas pixels or library masters replaced.'})
    proposed=deepcopy(garden);replacements=[];byid={m['id']:m for m in meshes}
    beds={key:shapely.union_all([Polygon([p[:2]for p in tri])for tri in triangles])for key,triangles in garden['sourceMulchTrianglesCm'].items()}
    for collection in ('ornamentalPlacements','gardenDetailPlacements'):
        for row in proposed[collection]:
            source=row['meshId']
            if source not in MAPPING:continue
            replacement=MAPPING[source];master=byid[replacement];radius=max(l['radialEnvelopeCm']for l in master['lods'])*row['uniformScale']
            height=max(l['expectedBoundsCm']['max'][2]for l in master['lods'])*row['uniformScale']
            require(radius<=row['radiusCm']+1e-5 and height<=row['actualHeightCm']+1e-5,'Existing conservative garden crown/height expanded')
            root=shapely.Point(row['positionCm'][:2]);clearance=float(root.distance(beds[row['sourceBedId']].boundary)-radius)
            require(beds[row['sourceBedId']].contains(root)and clearance>0,'Complete proposed crown escaped original mulch')
            replacements.append({'id':row['id'],'sourceMeshId':source,'meshId':replacement,'actualRadiusCm':radius,'actualHeightCm':height,
                'originalConservativeRadiusCm':row['radiusCm'],'originalConservativeHeightCm':row['actualHeightCm'],'fullCrownToOriginalBedClearanceCm':clearance})
            row.update(meshId=replacement,sourceMeshId=source)
    require(len(replacements)==424,'Expected4 white+420 low-clump replacement scope differs')
    audit={'status':manifest['status'],'gardenInstances':461,'heroInstances':12,'whiteHeroReplacements':4,'lowerClumpReplacements':420,
        'all473OriginalTransformsUnchanged':True,'unchangedOtherGardenRows':49,'sourceBedGroundArchitectureCollisionUnchanged':True,
        'sourceTexturePixelsAndRecipesUnchanged':True,'measuredReplacements':replacements,'oldMasterCount':96,'newMasterCount':4,
        'newLodCount':12,'artistInterpretation':True,'surveyedBotany':False,'nativeVerified':False,'nativeAppearanceAccepted':False,
        'performanceAccepted':False,'integrationAuthorized':False,
        'sourceMetadataPolicy':'Original row metadata retained as conservative source witnesses; measured new envelopes live in measuredReplacements.'}
    crown={'schemaVersion':1,'owner':OWNER,'status':'verified-decoded-organic-garden-crowns-not-native-accepted',
        'sourceGarden':pin(GARDEN),'sourceNativeImport':pin(REPORT),'sourceLibrary':pin(LIBRARY),
        'geometryManifest':pin(output/'geometry-manifest.json'),'glb':pin(glb),
        'activeDesign':garden['activeDesign'],'housePlacement':garden['housePlacement'],
        'sourceSceneSha256':garden['sourceSceneSha256'],'sourceObjSha256':garden['sourceObjSha256'],
        'originalSourceMulchTrianglesCm':garden['sourceMulchTrianglesCm'],'instances':424,'measuredReplacements':replacements,
        'completeActualAllLodCircularCrownsInsideOriginalBeds':True,'rootsYawsUniformScalesUnchanged':True,
        'sourceGroundArchitectureCollisionUnchanged':True,'minimumFullCrownToBedEdgeCm':min(r['fullCrownToOriginalBedClearanceCm']for r in replacements),
        'nativeAppearanceAccepted':False,'performanceAccepted':False,'integrationAuthorized':False}
    write(output/'crown-validation.json',crown)
    proposed.update(owner=OWNER,generatorSha256=sha(__file__),inputFiles=inputs,sourceGarden=pin(GARDEN),sourceNativeImport=pin(REPORT),
        originalOrnamentalPlacements=garden['ornamentalPlacements'],originalGardenDetailPlacements=garden['gardenDetailPlacements'],
        organicStudy=audit,organicMasters=pin(output/'geometry-manifest.json'),organicCrownProof=pin(output/'crown-validation.json'))
    write(output/'garden-plan.json',proposed)
    display_recipes={**recipes,'ph_shrub_01_ornamental':all_materials['ph_shrub_01_ornamental']};maps=textures(display_recipes)
    hero=next(r for r in garden['ornamentalPlacements']if r['meshId']=='ornamental_white_a')
    low=next(r for r in garden['gardenDetailPlacements']if r['meshId']=='garden_rosette_r3_a')
    old_white=decode_glb(old['ornamental_white_a']['glbPath'])[1][old['ornamental_white_a']['lods'][0]['nodeName']]
    old_low=decode_glb(old['garden_rosette_r3_a']['glbPath'])[1][old['garden_rosette_r3_a']['lods'][0]['nodeName']]
    columns=[('R10 white hero',old_white,hero,False),('Organic white hero',decoded['garden_white_organic_a_LOD0'],hero,False),
        ('R10 lower clump',old_low,low,True),('Organic lower clump',decoded['garden_broadleaf_organic_a_LOD0'],low,True)]
    atlas=Image.new('RGB',(2400,1360),'#eeeae1');draw=ImageDraw.Draw(atlas)
    for col,(label,parts,row,compact)in enumerate(columns):
        for view in range(2):atlas.paste(render(parts,row,display_recipes,maps,compact,bool(view)),(col*600,70+view*620))
        draw.text((col*600+12,20),label,fill='#202820')
    draw.text((12,1325),'Decoded GLB CPU comparison: same transform/camera/light within each pair; actual original source RGB+alpha, authored palette. No Unreal/encoding/shadow acceptance.',fill='#202820')
    atlas.save(output/'organic-side-by-side.png')
    bundle={'schemaVersion':1,'owner':OWNER,'generatorSha256':sha(__file__),'inputFiles':inputs,'status':manifest['status'],
        'sourceNativeImport':pin(REPORT),'sourceGarden':pin(GARDEN),'sourceLibrary':pin(LIBRARY),'geometryManifest':pin(output/'geometry-manifest.json'),
        'materialManifest':pin(output/'material-manifest.json'),'plan':pin(output/'garden-plan.json'),'morphology':pin(output/'morphology-audit.json'),
        'assetManifest':pin(output/'asset-manifest.json'),'crownValidation':pin(output/'crown-validation.json'),
        'glb':pin(glb),'preview':pin(output/'organic-side-by-side.png'),'audit':audit,
        'previewPolicy':'Actual decoded triangles/UV/alpha with existing diffuse values; CPU photographic RGB assumes standard sRGB display interpretation, not a claim about native texture encoding. Geometry normals only; no normal maps, native SSS/shadows/GI.',
        'limits':['Artist geometry and garden composition, not surveyed botany.','No source recipes/maps/pixels, original96 masters, source geometry/collision or roots/yaws/scales changed.',
            'Selected original metadata remains source witness; typed measured envelopes prove bounds. No native integration or performance acceptance.']}
    write(output/'garden-organic-manifest.json',bundle)
    return {'output':str(output),'manifest':pin(output/'garden-organic-manifest.json'),'plan':bundle['plan'],'preview':bundle['preview'],
        'trianglesByMaster':{r['id']:[l['triangles']for l in r['lods']]for r in meshes},'audit':{k:audit[k]for k in ('whiteHeroReplacements','lowerClumpReplacements','unchangedOtherGardenRows','nativeAppearanceAccepted')}}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default=str(OUTPUT))
    print(json.dumps(build(**vars(parser.parse_args()))))
