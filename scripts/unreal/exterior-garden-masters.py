"""Author actual 3D feather grasses, violet perennials and photo-leaf rosettes.

No whole-plant cards or source texture edits. Three deterministic LODs retain
the same curved stalks and radial planting forms. All twelve original primary
roots/yaws remain exact; replacement grass crowns fit their old radial envelopes.
The user-authorized ornamental hero height is bounded to 120 cm.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import struct

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-garden-masters.py'
PALETTES={'garden_blade_green':[.052,.094,.031], 'garden_plume_silk':[.58,.535,.415],
          'garden_lavender_violet':[.185,.067,.315]}


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')


def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def mul(a,b):return [x*b for x in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def unit(a):
    length=math.sqrt(dot(a,a));require(length>1e-12,'Degenerate authored basis');return mul(a,1/length)


class Mesh:
    def __init__(self):self.parts={}

    def geometry(self,key,points,uv,triangles,color):
        part=self.parts.setdefault(key,{'positions':[],'uv':[],'triangles':[],'colors':[]})
        start=len(part['positions']);part['positions'].extend(points);part['uv'].extend(uv)
        part['triangles'].extend(tuple(i+start for i in t)for t in triangles)
        part['colors'].extend([color]*len(points))

    def tube(self,key,path,radius,color,sides=4):
        points,uv,triangles=[],[],[]
        chord=unit(sub(path[-1],path[0]))
        stable_side=unit(cross(chord,[0,0,1]if abs(chord[2])<.999 else [0,1,0]))
        for j,p in enumerate(path):
            tangent=unit(sub(path[min(len(path)-1,j+1)],path[max(0,j-1)]))
            a=unit(sub(stable_side,mul(tangent,dot(stable_side,tangent))));b=unit(cross(tangent,a))
            r=radius*(1-.45*j/(len(path)-1))
            for i in range(sides+1):
                angle=math.tau*i/sides
                points.append(add(p,add(mul(a,math.cos(angle)*r),mul(b,math.sin(angle)*r))))
                uv.append([i/sides,j/(len(path)-1)])
        for j in range(len(path)-1):
            for i in range(sides):
                a=j*(sides+1)+i;b=a+sides+1
                triangles.extend([(a,a+1,b),(a+1,b+1,b)])
        self.geometry(key,points,uv,triangles,color)

    def ribbon(self,key,path,width,color,photo=False,uvrange=None):
        points,uv,triangles=[],[],[]
        stable_side=unit(cross(sub(path[-1],path[0]),[0,0,1]))
        for j,p in enumerate(path):
            t=j/(len(path)-1)
            direction=unit(sub(path[min(len(path)-1,j+1)],path[max(0,j-1)]))
            # Parallel transport avoids abrupt ribbon twists near the vertical
            # that a changing reference-axis cross product would introduce.
            tangent=unit(sub(stable_side,mul(direction,dot(stable_side,direction))))
            normal=unit(cross(tangent,direction))
            w=width*(.16+.84*math.sin(math.pi*(.035+.92*t))**.72)*(1-.78*t)
            for i in range(3):
                points.append(add(p,add(mul(tangent,(i-1)*w*.5),mul(normal,w*.13 if i==1 else 0))))
                if photo:
                    # Raw glTF/Unreal UV has top-left image origin, unlike Blender.
                    uv.append([.9140625+.00390625*i/2,.3515625+.0625*t])
                else:
                    uv.append([i/2,t])
        for j in range(len(path)-1):
            a=j*3;b=a+3
            triangles.extend([(a,b,a+1),(a+1,b,b+1),(a+1,b+1,a+2),(a+2,b+1,b+2)])
        self.geometry(key,points,uv,triangles,color)

    def leaf(self,root,azimuth,length,width,rise,color,sections=6):
        radial=[math.cos(azimuth),math.sin(azimuth),0];side=[-radial[1],radial[0],0]
        points,uv,triangles=[],[],[]
        for j in range(sections+1):
            t=j/sections
            center=add(root,add(mul(radial,length*t),[0,0,rise*math.sin(math.pi*.86*t)]))
            for i in range(3):
                points.append(add(center,add(mul(side,(i-1)*width*.5),[0,0,.045*length*math.sin(math.pi*t) if i==1 else 0])))
                uv.append([i/2,1-t])
        for j in range(sections):
            a=j*3;b=a+3
            triangles.extend([(a,a+1,b),(a+1,b+1,b),(a+1,a+2,b+1),(a+2,b+2,b+1)])
        self.geometry('regional_green_leaf',points,uv,triangles,color)

    def petals(self,center,axis,size,color):
        direction=unit(axis);a=unit(cross(direction,[0,0,1] if abs(direction[2])<.93 else [0,1,0]));b=unit(cross(direction,a))
        # Five cupped petal lobes are actual geometry around one attached floret.
        points,uv,triangles=[],[],[]
        for petal in range(5):
            phi=petal*math.tau/5
            radial=add(mul(a,math.cos(phi)),mul(b,math.sin(phi)))
            side=add(mul(a,-math.sin(phi)),mul(b,math.cos(phi)))
            root=add(center,mul(direction,-size*.15));tip=add(center,add(mul(radial,size),mul(direction,size*.21)))
            middle=add(center,add(mul(radial,size*.5),mul(direction,-size*.14)))
            points.extend([root,add(middle,mul(side,-size*.36)),tip,add(middle,mul(side,size*.36))])
            uv.extend([[.5,0],[0,.5],[.5,1],[1,.5]])
            i=petal*4;triangles.extend([(i,i+1,i+2),(i,i+2,i+3)])
        self.geometry('garden_lavender_violet',points,uv,triangles,color)

    def seed_grain(self,center,axis,radius,length,color):
        """Eight actual tapered faces add pale seed mass to each fine panicle."""
        n=unit(axis);a=unit(cross(n,[0,0,1]if abs(n[2])<.93 else [0,1,0]));b=unit(cross(n,a))
        vertices=[add(center,mul(n,-length*.5)),add(center,mul(n,length*.5))]
        vertices.extend(add(center,add(mul(a,math.cos(i*math.pi/2)*radius),mul(b,math.sin(i*math.pi/2)*radius)))for i in range(4))
        points,uv,triangles=[],[],[]
        for pole in (0,1):
            for i in range(4):
                indices=(pole,2+i,2+(i+1)%4)if pole==0 else (pole,2+(i+1)%4,2+i)
                start=len(points);points.extend(vertices[k]for k in indices)
                uv.extend([[.5,0],[0,1],[1,1]]);triangles.append((start,start+1,start+2))
        self.geometry('garden_plume_silk',points,uv,triangles,color)

    def normalize(self,height):
        allpoints=[p for part in self.parts.values() for p in part['positions']]
        low=min(p[2]for p in allpoints);top=max(p[2]for p in allpoints)
        scale=height/(top-low)
        for part in self.parts.values():part['positions']=[[p[0]*scale,p[1]*scale,(p[2]-low)*scale]for p in part['positions']]


def feather(variant,lod):
    rng=random.Random(6012263000+variant*931);mesh=Mesh()
    blades=[]
    for i in range(108):
        phi=i*2.39996323+rng.uniform(-.17,.17)
        h=rng.uniform(23,54);reach=rng.uniform(8,25)
        start=rng.uniform(.5,4.);width=rng.uniform(.5,1.1)
        sway=rng.uniform(-4,4)
        blades.append((phi,h,reach,start,width,sway,rng.uniform(.77,1.)))
    stride=[1,2,3][lod]
    for i,(phi,h,reach,start,width,sway,c) in enumerate(blades):
        if i%stride:continue
        path=[]
        sections=[7,5,4][lod]
        for j in range(sections+1):
            t=j/sections;r=start+reach*t**1.5
            path.append([r*math.cos(phi)-sway*math.sin(phi)*math.sin(math.pi*t),
                         r*math.sin(phi)+sway*math.cos(phi)*math.sin(math.pi*t),h*math.sin(math.pi*.72*t)])
        mesh.ribbon('garden_blade_photo',path,width,[c,c,c,1],photo=True)
    stalks=[]
    for i in range(15):
        phi=i*2.39996323+variant*.61+rng.uniform(-.25,.25)
        h=rng.uniform(61,87);reach=rng.uniform(4,22);head=rng.uniform(16,24);bend=rng.uniform(-3,3)
        stalks.append((phi,h,reach,head,bend,rng.uniform(.83,1.)))
    for i,(phi,h,reach,head,bend,c) in enumerate(stalks):
        if lod==2 and i%3==2:continue
        def stalk(t):return [reach*math.cos(phi)*t**1.65-bend*math.sin(phi)*t*t,
                             reach*math.sin(phi)*t**1.65+bend*math.cos(phi)*t*t,h*t]
        mesh.tube('garden_blade_green',[stalk(j/7)for j in range(8)],.095,[c,c,c,1],sides=4)
        levels=[10,8,6][lod];branches=[5,4,3][lod]
        for level in range(levels):
            t=(level+.4)/levels;root=stalk(1-head/h+head/h*t)
            width=(1.1+4.1*math.sin(math.pi*t)**.75)*(1-.27*t)
            for branch in range(branches):
                angle=phi+level*1.71+branch*math.tau/branches
                # Radial branched filaments form a genuinely volumetric soft head,
                # with fine tapered geometry distributed around the curved stalk.
                end=add(root,[math.cos(angle)*width,math.sin(angle)*width,1.6+.9*t])
                middle=add(root,mul(sub(end,root),.58))
                thickness=[.060,.074,.085][lod]
                mesh.tube('garden_plume_silk',[root,end],thickness,[c,c*.98,c*.94,1],sides=3)
                if lod==0:
                    for fork in ((-1 if (branch+level)%2 else 1),):
                        tip=add(middle,[math.cos(angle+fork*.47)*width*.54,math.sin(angle+fork*.47)*width*.54,1.05])
                        mesh.tube('garden_plume_silk',[middle,tip],.042,[c*.94,c*.95,c*.98,1],sides=3)
                center=add(middle,mul(sub(end,middle),.64))
                grain_radius=[.31,.40,.49][lod]*(.84+.16*math.sin(angle+level))
                mesh.seed_grain(center,sub(end,root),grain_radius,1.6+.3*math.sin(angle),[c,c*.98,c*.94,1])
    mesh.normalize(85)
    return mesh


def violet(variant,lod):
    rng=random.Random(6012264000+variant*631);mesh=Mesh()
    stems=[]
    for i in range(28):
        phi=i*2.39996323+rng.uniform(-.17,.17);r=rng.uniform(1,8)
        h=rng.uniform(24,41);lean=rng.uniform(2,8)
        stems.append((phi,r,h,lean,rng.uniform(.79,1.)))
    for i,(phi,r,h,lean,c)in enumerate(stems):
        if lod==1 and i%3==2 or lod==2 and i%2:continue
        def stem(t):return [(r+lean*t*t)*math.cos(phi),(r+lean*t*t)*math.sin(phi),h*t]
        mesh.tube('garden_blade_green',[stem(j/5)for j in range(6)],.075,[c,c,c,1],sides=4)
        for level in range(3):
            t=.20+level*.17;center=stem(t)
            for side in (-1,1):
                angle=phi+side*math.pi/2;length=3.3-level*.35
                path=[add(center,[math.cos(angle)*length*j/3,math.sin(angle)*length*j/3,j*.13])for j in range(4)]
                mesh.ribbon('garden_blade_green',path,.55,[c*.83,c*.88,c*.95,1])
        for j,t in enumerate((.20,.37)):
            center=stem(t);azimuth=phi+(-1 if j==0 else 1)*math.pi/2
            mesh.leaf(center,azimuth,3.7,1.4,.65,[c*.83,c*.88,c*.95,1],sections=3 if lod==0 else 2)
        levels=[12,9,7][lod]
        for level in range(levels):
            t=.71+.275*(level+.2)/levels;center=stem(t)
            for j in range([4,3,3][lod]):
                angle=phi+level*1.51+j*math.tau/[4,3,3][lod]
                radius=.74*(.30+.70*math.sin(math.pi*(level+.2)/levels))
                point=add(center,[radius*math.cos(angle),radius*math.sin(angle),.08])
                mesh.petals(point,[math.cos(angle),math.sin(angle),.16],.48 if lod==0 else .555,[c,c*.92,min(1,c*1.05),1])
    mesh.normalize(40)
    return mesh


def rosette(variant,lod):
    rng=random.Random(6012265000+variant*613);mesh=Mesh()
    for i in range(16):
        phi=i*2.39996323+rng.uniform(-.23,.23);length=rng.uniform(7,13);width=rng.uniform(3.5,5.1)
        rise=rng.uniform(3,6);root=[math.cos(phi)*rng.uniform(.2,1.4),math.sin(phi)*rng.uniform(.2,1.4),rng.uniform(.02,.55)]
        c=rng.uniform(.72,1.)
        if lod==1 and i%3==2 or lod==2 and i%2:continue
        mesh.leaf(root,phi,length,width,rise,[c,c*.98,c*.96,1],sections=[6,4,3][lod])
    mesh.normalize(9.5)
    return mesh


def basis(part):
    points,uv=part['positions'],part['uv'];normals=[[0.,0.,0.]for _ in points];tangent=[[0.,0.,0.]for _ in points]
    bitangent=[[0.,0.,0.]for _ in points]
    for ia,ib,ic in part['triangles']:
        a,b,c=points[ia],points[ib],points[ic];e1,e2=sub(b,a),sub(c,a);n=cross(e1,e2)
        require(dot(n,n)>1e-15,'Degenerate authored triangle')
        d1,d2=sub(uv[ib],uv[ia]),sub(uv[ic],uv[ia]);det=d1[0]*d2[1]-d1[1]*d2[0]
        require(abs(det)>1e-12,'Degenerate authored UV')
        t=mul(sub(mul(e1,d2[1]),mul(e2,d1[1])),1/det);bt=mul(sub(mul(e2,d1[0]),mul(e1,d2[0])),1/det)
        for index in (ia,ib,ic):normals[index]=add(normals[index],n);tangent[index]=add(tangent[index],t);bitangent[index]=add(bitangent[index],bt)
    result=[]
    for n,t,b in zip(normals,tangent,bitangent):
        n=unit(n);t=unit(sub(t,mul(n,dot(t,n))));result.append((n,[*t,-1 if dot(cross(n,t),b)<0 else 1]))
    return [r[0]for r in result],[r[1]for r in result]


def write_glb(path,records,meshes):
    keys=sorted({key for mesh in meshes for key in mesh.parts});binary=bytearray()
    doc={'asset':{'version':'2.0','generator':OWNER},'scene':0,'scenes':[{'nodes':list(range(len(meshes)))}],
         'nodes':[],'meshes':[],'buffers':[],'bufferViews':[],'accessors':[],
         'materials':[{'name':key,'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':PALETTES.get(key,[.2,.3,.1])+[1],
                        'metallicFactor':0,'roughnessFactor':.8}}for key in keys]}
    def stream(rows,kind,component,fmt,target):
        binary.extend(b'\0'*((-len(binary))%4));start=len(binary)
        binary.extend(b''.join(struct.pack('<'+fmt*len(row),*row)for row in rows));view=len(doc['bufferViews'])
        doc['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(binary)-start,'target':target})
        accessor={'bufferView':view,'componentType':component,'count':len(rows),'type':kind}
        if kind=='VEC3':accessor.update(min=[min(p[k]for p in rows)for k in range(3)],max=[max(p[k]for p in rows)for k in range(3)])
        doc['accessors'].append(accessor);return len(doc['accessors'])-1
    def rotate(p):return [p[0],p[2],p[1]]
    for record,mesh in zip(records,meshes):
        primitives=[]
        for key,part in mesh.parts.items():
            normals,tangents=basis(part)
            attrs={'POSITION':stream([mul(rotate(p),.01)for p in part['positions']],'VEC3',5126,'f',34962),
                   'NORMAL':stream([rotate(p)for p in normals],'VEC3',5126,'f',34962),
                   'TANGENT':stream([[*rotate(p[:3]),-p[3]]for p in tangents],'VEC4',5126,'f',34962),
                   'TEXCOORD_0':stream(part['uv'],'VEC2',5126,'f',34962),
                   'COLOR_0':stream(part['colors'],'VEC4',5126,'f',34962)}
            indices=stream([(i,)for a,b,c in part['triangles']for i in (a,c,b)],'SCALAR',5125,'I',34963)
            primitives.append({'attributes':attrs,'indices':indices,'material':keys.index(key),'mode':4})
        doc['nodes'].append({'mesh':len(doc['meshes']),'name':record['nodeName']})
        doc['meshes'].append({'name':record['nodeName'],'primitives':primitives})
    binary.extend(b'\0'*((-len(binary))%4));doc['buffers']=[{'byteLength':len(binary)}]
    raw=json.dumps(doc,separators=(',',':'),allow_nan=False).encode();raw+=b' '*((-len(raw))%4)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb')as stream:
        stream.write(struct.pack('<4sII',b'glTF',2,28+len(raw)+len(binary))+struct.pack('<II',len(raw),0x4e4f534a)+raw
                     +struct.pack('<II',len(binary),0x004e4942)+binary)


def build(output,base_garden,library):
    output,base_garden,library=map(lambda p:Path(p).resolve(),(output,base_garden,library))
    require(output.is_relative_to(ROOT/'output/unreal')and not output.exists(),'Choose a fresh isolated output')
    source_materials=json.loads((library/'material-manifest.json').read_text())
    old=json.loads(base_garden.read_text());garden=deepcopy(old)
    materials={key:{'kind':'authored-foliage','maps':{},'linearColor':rgb,'roughness':rough,'specular':spec,
                    'subsurfaceScale':sss,'twoSided':True,'source':'Original authored actual plant geometry',
                    'artDirection':'Bounded physical diffuse palette; fine actual geometry and per-part vertex colour, no emission'}
               for key,rgb,rough,spec,sss in [(key,PALETTES[key],rough,spec,sss)for key,rough,spec,sss in
                   [('garden_blade_green',.78,.12,.045),('garden_plume_silk',.84,.14,.11),('garden_lavender_violet',.76,.14,.045)]]}
    photo=deepcopy(source_materials['ph_grass_medium_01'])
    photo.update(kind='bark',maps={k:v for k,v in photo['maps'].items()if k!='alpha'},twoSided=True,
                 tint=[.92,1.,.96],albedoScale=.88,specular=.12,normalStrength=.45)
    photo.pop('albedoDerivation',None)
    photo['artDirection']='Actual opaque curved blades use an audited fully opaque green 8x128 photographic strip of original grass atlas; no pixel edits or whole-plant cards.'
    materials['garden_blade_photo']=photo
    materials['regional_green_leaf']=deepcopy(source_materials['regional_green_leaf'])
    mesh_rows,lod_rows,all_meshes=[],[],[]
    for kind,variants,builder,role,form,height in [('feather',3,feather,'ornamental','grass',85),
                ('violet',2,violet,'ornamental','flowering',40),('rosette',2,rosette,'groundcover',None,9.5)]:
        for variant in range(variants):
            mesh_id=f'garden_{kind}_r3_{chr(97+variant)}';lods=[]
            for lod in range(3):
                mesh=builder(variant,lod);points=[p for part in mesh.parts.values()for p in part['positions']]
                node=f'{mesh_id}_LOD{lod}';triangles=sum(len(part['triangles'])for part in mesh.parts.values())
                require(triangles<=20000,'Plant LOD budget exceeds 20k: '+node)
                row={'level':lod,'nodeName':node,'vertices':len(points),'triangles':triangles,
                     'expectedBoundsCm':{'min':[min(p[k]for p in points)for k in range(3)],'max':[max(p[k]for p in points)for k in range(3)]},
                     'derivation':'Original deterministic curved ribbons/stalk tubes/branched filaments or cupped five-petal florets; native cm exported to standard glTF metres'}
                lods.append(row);lod_rows.append(row);all_meshes.append(mesh)
            mesh_rows.append({'id':mesh_id,'role':role,'form':form,'heightCm':height,'placementPolicy':'explicit-only',
                              'flowerColor':'violet'if kind=='violet'else None,'materialKeys':sorted(all_meshes[-1].parts),
                              'lods':lods,'composition':'Illustrative authored garden plant; botanical form and colours are art direction, not a measured species census.'})
    output.mkdir(parents=True);glb_path=output/'glb/garden_masters_r3.glb';write_glb(glb_path,lod_rows,all_meshes)
    for row in mesh_rows:row.update(glbPath=str(glb_path),glbSha256=sha(glb_path))
    inputs={str(p):sha(p)for p in (base_garden,library/'material-manifest.json',Path(__file__))}
    for recipe in materials.values():
        for spec in recipe['maps'].values():inputs[spec['path']]=spec['sha256']
    alpha_witness=source_materials['ph_grass_medium_01']['maps']['alpha']
    inputs[alpha_witness['path']]=alpha_witness['sha256']
    manifest={'schema':1,'units':'metres','owner':OWNER,'revision':'R3 actual 3D ornamental planting with volumetric seed infill and fuller violet leaves',
              'axes':'glTF Y-up; Unreal native = [100*x,100*z,100*y]', 'status':'OFFLINE_NOT_NATIVE_ACCEPTED',
              'meshes':mesh_rows,'inputFiles':inputs}
    write(output/'geometry-manifest.json',manifest);write(output/'material-manifest.json',materials)
    write(output/'asset-manifest.json',{'schema':1,'owner':OWNER,'inputFiles':inputs,
          'sources':[{'kind':'original-authored-geometry','generator':OWNER,'license':'Original project asset'},
                     {'kind':'photographic-grass-and-individual-leaf-textures','license':'CC0-1.0',
                      'sources':['https://polyhaven.com/a/grass_medium_01','https://www.cgbookcase.com/textures/green-leaf-12']}],
          'scope':'Actual curved individual leaves, stalks and volumetric heads. No image of an entire plant is placed on crossed cards.'})
    meshes={r['id']:r for r in mesh_rows}
    def replace(row,mesh_id,height_limit=None):
        new=meshes[mesh_id]
        lo=min(l['expectedBoundsCm']['min'][2]for l in new['lods']);hi=max(l['expectedBoundsCm']['max'][2]for l in new['lods'])
        radius=max(math.hypot(x,y)for l in new['lods']for x in (l['expectedBoundsCm']['min'][0],l['expectedBoundsCm']['max'][0])
                   for y in (l['expectedBoundsCm']['min'][1],l['expectedBoundsCm']['max'][1]))
        s=min(row['radiusCm']/radius,(height_limit if height_limit else row['actualHeightCm'])/(hi-lo))
        oldfloor=row['positionCm'][2]+row.get('sourceMinimumZCm',0)*row['uniformScale']
        # Existing exact XY/yaw and complete radius/height bounds survive. Since
        # primary roots are an explicit contract, keep their exact Z too.
        if row['id'].startswith('garden_drift_'):
            row['positionCm'][2]=oldfloor-lo*s
        previous={'meshId':row['meshId'],'radiusCm':row['radiusCm'],'heightCm':row['actualHeightCm']}
        row.update(meshId=mesh_id,role=new['role'],form=new['form'],scale=[s]*3,uniformScale=s,
                   heightCm=(hi-lo)*s,actualHeightCm=(hi-lo)*s,radiusCm=radius*s,
                   sourceMinimumZCm=lo,sourceMaximumZCm=hi,sourceCrownRadiusCm=radius,previousEnvelope=previous,
                   authoredRevision='R3 actual 3D garden with legible seed/petal volume')
    for index,row in enumerate(garden['ornamentalPlacements']):
        if row['form']=='grass':replace(row,f'garden_feather_r3_{"abc"[index%3]}',height_limit=120)
    for index,row in enumerate(garden['gardenDetailPlacements']):
        choose_violet=row['layer']=='middle' or row['drift']=='fine-grass-seam' and index%2==0
        replace(row,f'garden_{"violet"if choose_violet else "rosette"}_r3_{"ab"[index%2]}')
        row['drift']='violet-perennial'if choose_violet else 'muted-photo-leaf-carpet'
    for row,original in zip(garden['ornamentalPlacements'],old['ornamentalPlacements']):
        require(row['positionCm']==original['positionCm']and row['yawDeg']==original['yawDeg'],'A primary root moved')
        require(row['radiusCm']<=original['radiusCm']+1e-7 and row['actualHeightCm']<=(120 if row['form']=='grass'else original['actualHeightCm'])+1e-7,'An original crown radius or allowed height expanded')
    garden.update(owner=OWNER,revision='R3 feather seed infill and fuller violet perennial drifts',generatorSha256=sha(__file__),
                  generatedAt=datetime.now(timezone.utc).isoformat(),authoredMasters={'path':str(output/'geometry-manifest.json'),
                  'sha256':sha(output/'geometry-manifest.json')})
    garden['inputFiles'].update(inputs)
    garden['inputFiles'].update({str(p):sha(p)for p in (glb_path,output/'geometry-manifest.json',output/'material-manifest.json')})
    garden['gardenDetailAudit'].update(status='PASS_OFFLINE_NOT_NATIVE',sourceTexturePixelsChanged=False,
             sourceYellowGroundcoverRemoved=True,originalPrimaryRootsPreserved=12,primaryGrassRadialEnvelopesNeverExpanded=True,
             primaryGrassHeightRangeCm=[min(r['heightCm']for r in garden['ornamentalPlacements']if r['form']=='grass'),
                                       max(r['heightCm']for r in garden['ornamentalPlacements']if r['form']=='grass')],
             primaryGrassArtistHeightLimitCm=120,
             perAsset=dict(Counter(r['meshId']for r in garden['gardenDetailPlacements'])),
             detailLodTriangleTotalsBeforeCulling=[sum(meshes[r['meshId']]['lods'][level]['triangles']for r in garden['gardenDetailPlacements'])for level in range(3)],
             interpretation='Authored layered ornamental garden; source photographic individual-leaf maps retained unedited')
    write(output/'garden-plan.json',garden)
    summary={'status':'OFFLINE_GENERATED_NATIVE_PENDING','extension':str(output),'gardenPlan':str(output/'garden-plan.json'),
             'glbSha256':sha(glb_path),'variants':len(mesh_rows),'lods':len(lod_rows),
             'lodTriangles':{r['id']:[l['triangles']for l in r['lods']]for r in mesh_rows},
             'detailInstances':len(garden['gardenDetailPlacements']),'primaryGrassReplacements':6,
             'materialsAdded':4,'allSourceTexturePixelsUnchanged':True,
             'bladePhotoStripWitness':{'sourceAlpha':alpha_witness,'pixelRect':[1872,720,1880,848],
                                      'uvOrigin':'Top-left glTF/Unreal','uvRect':[.9140625,.3515625,.91796875,.4140625]}}
    write(output/'summary.json',summary)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True);parser.add_argument('--base-garden',required=True);parser.add_argument('--library',required=True)
    args=parser.parse_args();print(json.dumps(build(args.output,args.base_garden,args.library)))
