"""Actual small-scale grove ground ecology beneath the 78 existing tree roots.

No tree is moved, added or rescaled. All new complete footprints remain inside
the frozen imagery-derived grove and existing canopy footprints, away from
private/source geometry, public roads, buildings and cultivated ground. Fallen
leaves, twigs, basal trunk flares and low plants are individual actual geometry;
there is no broad ground patch/decal. Existing lawful photo pixels remain exact.
"""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import struct
import sys

import numpy as np
from PIL import Image
import shapely
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-canopy-ecology.py'
REGION='village_nearest_grove'
SEED=601226300078
sys.path.insert(0,str(ROOT/'scripts/unreal'))


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):return json.loads(Path(path).read_text())


def write(path,value,compact=False):
    with Path(path).open('x')as stream:
        json.dump(value,stream,ensure_ascii=False,allow_nan=False,indent=None if compact else 2,
                  separators=(',',':')if compact else None);stream.write('\n')


def module(name):
    spec=importlib.util.spec_from_file_location(name.replace('-','_'),ROOT/'scripts/unreal'/f'{name}.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def domains(context,terrain,buildings,scene):
    helper=module('exterior-regional-vegetation')
    rows=[row for row in context['regionalVegetationPlacements']if row['regionId']==REGION]
    require(len(rows)==78,'Existing grove root census changed')
    region=next(row for row in context['regionalVegetationPolicy']['regions']if row['id']==REGION)
    grove=Polygon(region['polygonCm']);require(grove.is_valid,'Invalid existing grove boundary')
    blocked=helper.constraints(context,buildings,scene)
    agricultural=[]
    for mesh in context['meshes']:
        if mesh['material']not in ('context_crop','context_arable'):continue
        for i in range(0,len(mesh['indices']),3):
            p=Polygon([mesh['verticesCm'][j][:2]for j in mesh['indices'][i:i+3]])
            if p.area>1e-6:agricultural.append(p)
    blocked['cultivatedGround']=unary_union(agricultural)
    forbidden=unary_union(list(blocked.values()))
    crowns=unary_union([Point(row['positionCm'][:2]).buffer(row['radiusCm'],quad_segs=64)for row in rows])
    domain=grove.buffer(-10).intersection(crowns).difference(forbidden.buffer(75))
    require(domain.is_valid and 2500<domain.area/10000<4000,'Unexpected shade ecology domain')
    return rows,region,grove,crowns,blocked,domain,helper.GroundSampler(context,terrain)


class Mesh:
    def __init__(self):self.parts={};self.features=[]

    def add(self,key,points,uv,triangles,colors=None):
        part=self.parts.setdefault(key,{'positionsCm':[],'uv0':[],'uv1':[],'colors':[],'triangles':[]})
        start=len(part['positionsCm']);part['positionsCm'].extend([list(map(float,p))for p in points]);part['uv0'].extend(uv)
        part['uv1'].extend([[0,0]for _ in points]);part['colors'].extend(colors or [[1,1,1,1]for _ in points])
        part['triangles'].extend([[j+start for j in face]for face in triangles])

    def tube(self,key,path,radius,lod,feature):
        path=np.asarray(path);points=[];uv=[];faces=[];sides=[7,5,4][lod]
        for i,center in enumerate(path):
            tangent=path[min(i+1,len(path)-1)]-path[max(i-1,0)];tangent/=np.linalg.norm(tangent)
            a=np.cross(tangent,[0,0,1]if abs(tangent[2])<.95 else [0,1,0]);a/=np.linalg.norm(a);b=np.cross(tangent,a)
            r=radius*(1-.62*i/(len(path)-1))
            for j in range(sides+1):
                phi=math.tau*j/sides;points.append((center+(a*math.cos(phi)+b*math.sin(phi))*r).tolist())
                uv.append([j/sides*math.tau*radius/25,i/(len(path)-1)*float(np.linalg.norm(path[-1]-path[0]))/25])
        for i in range(len(path)-1):
            for j in range(sides):
                a=i*(sides+1)+j;b=a+sides+1;faces.extend([[a,a+1,b],[a+1,b+1,b]])
        self.add(key,points,uv,faces);self.features.append({'kind':feature,'pathCm':path.tolist(),'radiusCm':radius})

    def leaf(self,key,root,azimuth,length,aspect,tilt,roll,curl,lod,fallen=False,mirror=False):
        forward=np.array([math.cos(azimuth)*math.cos(tilt),math.sin(azimuth)*math.cos(tilt),math.sin(tilt)])
        side=np.array([-math.sin(azimuth),math.cos(azimuth),0.]);normal=np.cross(forward,side)
        side,normal=side*math.cos(roll)+normal*math.sin(roll),normal*math.cos(roll)-side*math.sin(roll)
        sections=[5,3,2][lod];columns=3 if lod<2 else 2;points=[];uv=[];faces=[];centers=[]
        for i in range(sections+1):
            t=i/sections
            # Whole photographed individual leaf with cupped/slightly curled
            # actual surface, not a whole-plant card or billboard.
            middle=np.asarray(root)+forward*length*t+normal*(math.sin(math.pi*t)*length*.14*curl-length*.06*t*t)
            centers.append(middle.tolist())
            for j in range(columns):
                u=j/(columns-1);w=length*aspect
                p=middle+side*(u-.5)*w+normal*(abs(2*u-1)*w*.08*math.sin(math.pi*t)*curl)
                points.append(p.tolist());uv.append([1-u if mirror else u,t])
        if fallen:
            # The complete leaf surface is tangent above the sampled ground;
            # even curled edges cannot be buried under the backdrop.
            low=min(p[2]for p in points)
            for p in points:p[2]+=.12-low
            for p in centers:p[2]+=.12-low
        for i in range(sections):
            for j in range(columns-1):
                a=i*columns+j;b=a+columns;faces.extend([[a,a+1,b],[a+1,b+1,b]])
        self.add(key,points,uv,faces);self.features.append({'kind':'fallen-leaf'if fallen else 'living-leaf',
            'lengthCm':length,'centerlineCm':centers,'sections':sections,'columns':columns,'photoMaterial':key})


def litter(variant,lod,aspects):
    rng=random.Random(SEED+variant*761);mesh=Mesh()
    for i in range(6):
        phi=rng.uniform(0,math.tau);r=rng.uniform(0,7)
        key='canopy_litter_oak'if(i+variant)%3 else'canopy_litter_green'
        mesh.leaf(key,[math.cos(phi)*r,math.sin(phi)*r,0],rng.uniform(-math.pi,math.pi),
                  rng.uniform(6.2,11.8),aspects[key],rng.uniform(-.09,.14),rng.uniform(-.22,.22),
                  rng.uniform(.6,1.35),lod,fallen=True,mirror=rng.random()<.5)
    return mesh


def twig(variant,lod,aspects):
    rng=random.Random(SEED+1900+variant*361);mesh=Mesh();length=rng.uniform(23,41);bend=rng.uniform(-4,4)
    section=[5,3,2][lod]
    def point(t):return [length*t-length*.5,bend*math.sin(math.pi*t),.21+.37*math.sin(math.pi*t)]
    radius=rng.uniform(.085,.16)
    axis=[point(i/section)for i in range(section+1)]
    mesh.tube('ph_tree_small_02_branches',axis,radius,lod,'fallen-twig-axis')
    for t,sign in((.42,-1),(.76,1)):
        at=t*section;index=min(section-1,int(at));fraction=at-index
        # The actual lower LOD axis is a polyline. Attach each fork to that
        # rendered centreline instead of the unsampled analytic curve.
        start=np.asarray(axis[index])*(1-fraction)+np.asarray(axis[index+1])*fraction
        end=start+[rng.uniform(5,11),sign*rng.uniform(4,9),.13]
        mesh.tube('ph_tree_small_02_branches',[start.tolist(),((start+end)*.5+[0,0,.16]).tolist(),end.tolist()],radius*.47,lod,'connected-fallen-twig-fork')
    return mesh


def herb(variant,lod,aspects):
    rng=random.Random(SEED+3900+variant*331);mesh=Mesh()
    for i in range(9):
        phi=i*2.39996323+rng.uniform(-.2,.2);height=rng.uniform(2.3,5.5);reach=rng.uniform(2,4)
        root=[math.cos(phi)*.5,math.sin(phi)*.5,0.];end=[math.cos(phi)*reach,math.sin(phi)*reach,height]
        path=[root,[(root[k]+end[k])*.5 for k in range(3)],end]
        mesh.tube('canopy_understory_stem',path,.065,lod,'living-petiole')
        mesh.leaf('regional_green_leaf',end,phi,rng.uniform(5,8.9),aspects['regional_green_leaf'],
                  rng.uniform(.05,.65),rng.uniform(-.35,.35),rng.uniform(.7,1.3),lod)
    return mesh


def grass(variant,lod,aspects):
    rng=random.Random(SEED+5700+variant*997);mesh=Mesh();sections=[6,4,3][lod]
    for i in range(18):
        phi=rng.uniform(-math.pi,math.pi);radius=math.sqrt(rng.random())*3.7
        root=np.array([math.cos(phi)*radius,math.sin(phi)*radius,0.]);h=rng.uniform(8,17);reach=rng.uniform(4,11);width=rng.uniform(.16,.29)
        points=[];uv=[];faces=[];centers=[]
        for j in range(sections+1):
            t=j/sections;forward=np.array([math.cos(phi),math.sin(phi),0.]);side=np.array([-forward[1],forward[0],0])
            middle=root+forward*reach*t*t+[0,0,h*math.sin(math.pi*.72*t)];centers.append(middle.tolist())
            w=width*(.2+.8*math.sin(math.pi*(.02+.92*t))**.8)*(1-.65*t)
            for k in range(3):
                points.append((middle+side*w*(k-1)*.5+[0,0,w*.15 if k==1 else 0]).tolist())
                uv.append([.9140625+.00390625*k/2,.3515625+.0625*t])
        for j in range(sections):
            a=j*3;b=a+3;faces.extend([[a,a+1,b],[a+1,b+1,b],[a+1,a+2,b+1],[a+2,b+2,b+1]])
        mesh.add('garden_blade_photo',points,uv,faces);mesh.features.append({'kind':'curved-shade-grass-blade',
            'sections':sections,'centerlineCm':centers,'photographicUv':'Frozen fully opaque green strip from original grass_medium_01 atlas'})
    return mesh


def flare(family,variant,lod,skeleton):
    rng=random.Random(SEED+7300+variant*71+sum(map(ord,family)));mesh=Mesh()
    tree=skeleton[family];trunk=tree['branches'][0];normalization=tree['sharedUniformScale'];height=[42,50][variant]
    source_points=np.asarray(trunk['points']);radius=trunk['radius']*100*normalization
    segments=[8,6,4][lod];sides=[20,14,10][lod];points=[];uv=[];faces=[];axes=[]
    def axis(z):
        t=z/(source_points[-1,2]*100*normalization)
        p=((1-t)**2*source_points[0]+2*t*(1-t)*source_points[1]+t*t*source_points[2])*100*normalization
        return [float(p[0]),float(-p[1]),z]
    phase=rng.uniform(-math.pi,math.pi)
    for i in range(segments+1):
        t=i/segments;z=-1.4+(height+1.4)*t;center=axis(max(0,z));center[2]=z;axes.append(center)
        actual_t=max(0,z)/(source_points[-1,2]*100*normalization)
        old_radius=(trunk['radius']*(1-actual_t)+trunk['tipRadius']*actual_t)*100*normalization
        spread=(1-t)**2;flare_radius=old_radius*(1+.84*spread)+.055
        for j in range(sides+1):
            angle=math.tau*j/sides
            buttress=1+.20*spread*(.5+.5*math.cos(5*angle+phase))
            points.append([center[0]+flare_radius*buttress*math.cos(angle),center[1]+flare_radius*buttress*math.sin(angle),z])
            uv.append([math.tau*radius*j/sides/25,(z+1.4)/25])
    for i in range(segments):
        for j in range(sides):
            a=i*(sides+1)+j;b=a+sides+1;faces.extend([[a,a+1,b],[a+1,b+1,b]])
    mesh.add('ph_tree_small_02_branches',points,uv,faces);mesh.features.append({'kind':'basal-flare-connected-to-existing-trunk-axis',
        'existingFamily':family,'trunkRadiusCm':radius,'axisCm':axes,'sourceSharedUniformScale':normalization,
        'maximumHorizontalReachCm':max(math.hypot(*p[:2])for p in points),
        'topRadiusClearanceOverExistingTrunkCm':.055,'buriedRootBaseCm':1.4})
    return mesh


def record(mid,mesh,lod):
    points=[p for part in mesh.parts.values()for p in part['positionsCm']]
    return {'nodeName':mid+'_LOD'+str(lod),'level':lod,'parts':mesh.parts,'features':mesh.features,
            'expectedBoundsCm':{key:[op(p[i]for p in points)for i in range(3)]for key,op in(('min',min),('max',max))},
            'radialEnvelopeCm':max(math.hypot(*p[:2])for p in points),
            'vertices':len(points),'triangles':sum(len(part['triangles'])for part in mesh.parts.values())}


def write_glb(path,records):
    natural=module('exterior-lawn-natural');binary=bytearray();keys=sorted({key for row in records for key in row['parts']})
    doc={'asset':{'version':'2.0','generator':OWNER},'scene':0,'scenes':[{'nodes':list(range(len(records)))}],
         'nodes':[],'meshes':[],'accessors':[],'bufferViews':[],'buffers':[],
         'materials':[{'name':key,'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],
             'metallicFactor':0,'roughnessFactor':.85}}for key in keys]}
    def accessor(rows,kind,component=5126,target=34962):
        rows=np.asarray(rows,dtype='<f4'if component==5126 else'<u4');binary.extend(b'\0'*(-len(binary)%4));start=len(binary);binary.extend(rows.tobytes())
        view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(binary)-start,'target':target})
        a={'bufferView':view,'componentType':component,'count':len(rows),'type':kind}
        if kind=='VEC3':a.update(min=rows.min(axis=0).tolist(),max=rows.max(axis=0).tolist())
        doc['accessors'].append(a);return len(doc['accessors'])-1
    def rotate(rows):return [[p[0],p[2],p[1]]for p in rows]
    for row in records:
        primitives=[]
        for key,part in row['parts'].items():
            normals,tangents=natural.basis(part)
            attrs={'POSITION':accessor(np.asarray(rotate(part['positionsCm']))*.01,'VEC3'),
                   'NORMAL':accessor(rotate(normals),'VEC3'),
                   'TANGENT':accessor([[*rotate([p[:3]])[0],-p[3]]for p in tangents],'VEC4'),
                   'TEXCOORD_0':accessor(part['uv0'],'VEC2'),'TEXCOORD_1':accessor(part['uv1'],'VEC2'),
                   'COLOR_0':accessor(part['colors'],'VEC4')}
            idx=accessor([i for a,b,c in part['triangles']for i in(a,c,b)],'SCALAR',5125,34963)
            primitives.append({'attributes':attrs,'indices':idx,'material':keys.index(key),'mode':4})
        doc['nodes'].append({'name':row['nodeName'],'mesh':len(doc['meshes'])});doc['meshes'].append({'name':row['nodeName'],'primitives':primitives})
    binary.extend(b'\0'*(-len(binary)%4));doc['buffers']=[{'byteLength':len(binary)}]
    raw=json.dumps(doc,separators=(',',':'),allow_nan=False).encode();raw+=b' '*(-len(raw)%4)
    with Path(path).open('xb')as stream:
        stream.write(struct.pack('<4sII',b'glTF',2,28+len(raw)+len(binary))+struct.pack('<II',len(raw),0x4e4f534a)+raw
            +struct.pack('<II',len(binary),0x004e4942)+binary)


def create_library(materials,skeleton):
    aspects={}
    for key,recipe in materials.items():
        if key in('canopy_litter_oak','canopy_litter_green','regional_green_leaf'):
            with Image.open(recipe['maps']['albedo']['path'])as image:aspects[key]=image.width/image.height
    rows=[];records=[]
    families=[('litter',3,litter),('twig',3,twig),('herb',3,herb),('grass',2,grass)]
    for family,count,builder in families:
        for variant in range(count):
            mid=f'canopy_ecology_{family}_{variant}';lods=[]
            for lod in range(3):
                row=record(mid,builder(variant,lod,aspects),lod);records.append(row)
                lods.append({k:row[k]for k in('level','nodeName','vertices','triangles','expectedBoundsCm','radialEnvelopeCm')})
            rows.append({'id':mid,'role':'grass'if family=='grass'else'groundcover','placementPolicy':'explicit-only',
                         'ecologyFamily':family,'heightCm':max(l['expectedBoundsCm']['max'][2]for l in lods),
                         'materialKeys':sorted(records[-1]['parts']),'lods':lods})
    for source_family in('regional_broadleaf_a','regional_upright_b','regional_orchard_c'):
        for variant in range(2):
            mid=f'canopy_ecology_flare_{source_family}_{variant}';lods=[]
            for lod in range(3):
                row=record(mid,flare(source_family,variant,lod,skeleton),lod);records.append(row)
                lods.append({k:row[k]for k in('level','nodeName','vertices','triangles','expectedBoundsCm','radialEnvelopeCm')})
            rows.append({'id':mid,'role':'groundcover','placementPolicy':'explicit-only','ecologyFamily':'flare',
                'existingTreeFamily':source_family,'heightCm':max(l['expectedBoundsCm']['max'][2]for l in lods),
                'materialKeys':['ph_tree_small_02_branches'],'lods':lods})
    return rows,records


def place(rows,domain,trees,sampler):
    natural=module('exterior-lawn-natural');rng=np.random.default_rng(SEED);lookup={row['id']:row for row in rows}
    groups={};placements=[];fail=Counter();minimum=math.inf;ground_counts=Counter();family_counts=Counter()
    def add(mid,p,scale,yaw,tree_id=None):
        nonlocal minimum
        row=lookup[mid];radius=max(l['radialEnvelopeCm']for l in row['lods'])*scale
        point=Point(p);d=point.distance(domain.boundary)
        if not domain.contains(point)or d<radius+.1:fail['full-footprint-clearance']+=1;return False
        z,ground_id=sampler.sample(p)
        require(ground_id.startswith(('context_unresolved_flat_backdrop','context_distant_terrain_')),
                'Ecology crossed into incompatible authored/agricultural ground: '+ground_id)
        # Tiny discrete details touch original rendered ground. Existing tree
        # roots keep their exact elevated native origin for the basal attachment.
        native_z=z+.08
        if tree_id:native_z=next(tree['positionCm'][2]for tree in trees if tree['id']==tree_id)
        cull={'litter':8000,'twig':10000,'herb':12000,'grass':10000,'flare':20000}[row['ecologyFamily']]
        cell=f'{math.floor(p[0]/2500)}_{math.floor(p[1]/2500)}';gid=f'EX_{mid}_{cell}'
        group=groups.setdefault(gid,{'id':gid,'meshId':mid,'role':row['role'],'cullEndCm':cull,
            'qualityDetail':row['ecologyFamily']!='flare','instances':[]})
        instance={'positionCm':[float(p[0]),float(p[1]),float(native_z)],'yawDeg':float(yaw),'scale':[float(scale)]*3,
                  'radiusCm':radius,'actualHeightCm':row['heightCm']*scale,'clearanceCm':d,
                  'renderedGround':{'zCm':z,'meshId':ground_id,'measuredElevation':ground_id.startswith('context_distant_terrain_')},
                  'ecologyFamily':row['ecologyFamily']}
        if tree_id:instance['existingTreeId']=tree_id
        group['instances'].append(instance);placements.append({'meshId':mid,**instance})
        minimum=min(minimum,d-radius);ground_counts[ground_id]+=1;family_counts[row['ecologyFamily']]+=1;return True
    # Basal flare attachment retains existing root, yaw and scale exactly.
    for tree in trees:
        variant=int(hashlib.sha256(tree['id'].encode()).hexdigest()[:8],16)%2
        mid=f'canopy_ecology_flare_{tree["meshId"]}_{variant}'
        require(add(mid,tree['positionCm'][:2],tree['scale'][0],tree['yawDeg'],tree['id']),'Existing root cannot accept bounded basal contact')
    xmin,ymin,xmax,ymax=domain.bounds
    area=(xmax-xmin)*(ymax-ymin)/10000
    for family,rate in(('litter',10.),('twig',.52),('herb',.8),('grass',1.4)):
        count=int(area*rate);x=rng.uniform(xmin,xmax,count);y=rng.uniform(ymin,ymax,count)
        keep=shapely.contains_xy(domain,x,y);x,y=x[keep],y[keep]
        broad=natural.value_noise(x*10,y*10,2400.,60303);fine=natural.value_noise(x*10,y*10,390.,81721)
        threshold=(.30+.55*broad+.20*fine)if family=='litter'else(.26+.48*broad+.22*fine)
        keep=rng.random(len(x))<np.clip(threshold,.15,.92);x,y=x[keep],y[keep]
        variants=[row['id']for row in rows if row['ecologyFamily']==family]
        for a,b in zip(x,y):
            mid=variants[int(rng.integers(len(variants)))];scale=round(float(rng.uniform(.74,1.19)),6)
            add(mid,[float(a),float(b)],scale,float(rng.uniform(-180,180)))
    require(12000<family_counts['litter']<26000,'Unexpected discrete litter density')
    require(500<family_counts['herb']<3000 and 1000<family_counts['grass']<5000,'Unexpected ground community density')
    budgets=[sum(len(g['instances'])*lookup[g['meshId']]['lods'][lod]['triangles']for g in groups.values())for lod in range(3)]
    require(budgets[0]<5000000,'Grove ecology exceeds 5M near triangle budget')
    audit={'instances':len(placements),'groups':len(groups),'perFamily':dict(family_counts),'groundSources':dict(ground_counts),
           'minimumAdditionalWholeFootprintClearanceCm':minimum,'allInstancesTriangleBudgetByLod':budgets,'rejected':dict(fail),
           'placementMethod':'Continuous stochastic roots with smooth coherent 2.4m and39cm growth/litter fields, inside existing crowns only',
           'noBroadGroundPatchesOrDecals':True,'existingTreesPreserved':len(trees),'windDisplacementCm':0}
    return list(groups.values()),placements,audit


def build(context_path,terrain_path,buildings_path,scene_path,assets,output):
    context_path,terrain_path,buildings_path,scene_path,assets,output=map(lambda p:Path(p).resolve(),
        (context_path,terrain_path,buildings_path,scene_path,assets,output))
    require(output.is_relative_to(ROOT/'output/unreal')and not output.exists(),'Use a new immutable isolated ecology output')
    context,terrain,buildings,scene=map(read,(context_path,terrain_path,buildings_path,scene_path))
    require(context['activeDesign']=={'variant':'C','livingLayout':'B','heatingLayout':'B'},'C/B/B required')
    require(context['activeDesign']==scene['activeDesign']and context['housePlacement']==scene['house']['placement'],'Canonical source design/placement differs')
    require(context['housePlacement']['streetSetbackMm']==context['housePlacement']['eastSetbackMm']==3000,'3000 mm setbacks required')
    require(context['sourceSceneSha256']==terrain['sourceSceneSha256']==buildings['sourceSceneSha256']==sha(scene_path),'Source scene frame differs')
    require(context['sourceObjSha256']==buildings['sourceObjSha256']==sha(scene_path.parent/'dom-mm.obj'),'Source OBJ frame differs')
    require(buildings['activeDesign']==context['activeDesign']and buildings['housePlacement']==context['housePlacement'],'Building source frame differs')
    tree_roots,region,grove,crowns,blocked,domain,sampler=domains(context,terrain,buildings,scene)
    materials_source=assets/'material-manifest.json';base=read(materials_source)
    photo=ROOT/'output/unreal/exterior-garden-masters-20260930-r3/material-manifest.json'
    skeleton_path=ROOT/'output/unreal/exterior-regional-assets-20260927-r4/growth-skeletons.json';skeleton=read(skeleton_path)
    materials={key:deepcopy(base[key])for key in('ph_tree_small_02_branches','regional_green_leaf')}
    materials['garden_blade_photo']=deepcopy(read(photo)['garden_blade_photo'])
    for key,source,tint in [('canopy_litter_oak','regional_oak_leaf',[.76,.41,.18]),('canopy_litter_green','regional_green_leaf',[.72,.42,.17])]:
        materials[key]=deepcopy(base[source]);materials[key].update(tint=tint,albedoScale=.82,
            subsurfaceScale=.025,specular=.09,normalStrength=.7,
            artDirection='Dry fallen individual-leaf response from unchanged original CC0 photo maps; seasonal colour is illustrative, not measured site phenology.')
    materials['canopy_understory_stem']={'kind':'authored-foliage','maps':{},'linearColor':[.046,.074,.022],
        'roughness':.85,'specular':.12,'subsurfaceScale':.06,'twoSided':True,
        'source':'Original authored actual short petiole geometry','artDirection':'Small bounded green stems, no emission or wind displacement.'}
    rows,records=create_library(materials,skeleton);groups,placements,audit=place(rows,domain,tree_roots,sampler)
    inputs={str(p):sha(p)for p in(context_path,terrain_path,buildings_path,scene_path,scene_path.parent/'dom-mm.obj',
        materials_source,assets/'geometry-manifest.json',photo,skeleton_path,Path(__file__),
        ROOT/'scripts/unreal/exterior-regional-vegetation.py',ROOT/'scripts/unreal/exterior-context.py',
        ROOT/'scripts/unreal/exterior-lawn-natural.py')}
    for recipe in materials.values():
        for tex in recipe['maps'].values():require(sha(tex['path'])==tex['sha256'],'Changed photographic input');inputs[tex['path']]=tex['sha256']
    common={'schemaVersion':1,'owner':OWNER,'generatorSha256':sha(__file__),'sourceSceneSha256':context['sourceSceneSha256'],
        'sourceObjSha256':context['sourceObjSha256'],'activeDesign':context['activeDesign'],'housePlacement':context['housePlacement'],
        'inputFiles':inputs}
    audit.update(status='PASS_STATIC_GEOMETRY_AND_EXCLUSION',nativeVerified=False,domainAreaM2=domain.area/10000,
        originalGroveAreaM2=grove.area/10000,existingCanopyUnionM2=crowns.area/10000,
        originalTreeCount=78,regionId=REGION,sourceGroundChanged=False,providerPixelsChanged=False,
        fullFootprintPolicy='All LOD vertex radial envelope with uniform scale must fit exact grove inset10cm, existing crown union, and outside all protected/road/building/private/cultivated polygons buffered75cm, plus0.1cm margin.',
        groundEvidence='Existing highest rendered source context/terrain triangles only; unresolved flat backdrop is explicitly not measured terrain.',
        remainingCanopyMorphologyIssue='Only three repeated existing tree crown skeletons; uniformly clean upright basal stems. Root contact and ecology are this revision scope; canopy architecture/species/age are still illustrative.')
    output.mkdir(parents=True);glb=output/'canopy-ecology.glb';write_glb(glb,records)
    for row in rows:row.update(glbPath=str(glb),glbSha256=sha(glb))
    library={**common,'schema':1,'units':'metres','axes':'glTF Y-up; Unreal native=[100*x,100*z,100*y]',
        'status':'OFFLINE_NOT_NATIVE_ACCEPTED','meshes':rows,'revision':'Grove ground contact and individual ecological details R1'}
    write(output/'geometry-manifest.json',library);write(output/'material-manifest.json',materials)
    write(output/'asset-manifest.json',{'schema':1,**common,'sources':[{'kind':'original-authored-small-geometry','license':'Original project asset'},
        {'kind':'unchanged-photographic-individual-leaf-bark-and-grass-maps','license':'CC0-1.0',
         'sources':['https://www.cgbookcase.com/textures/oak-leaf-01','https://www.cgbookcase.com/textures/green-leaf-12',
                    'https://polyhaven.com/a/tree_small_02','https://polyhaven.com/a/grass_medium_01']}],
        'scope':'Illustrative seasonal ground ecology within existing observed canopy region; no added trees or census/species survey.'})
    plan={**common,'kind':'grove-ground-ecology','regionId':REGION,'sourceContext':{'path':str(context_path),'sha256':sha(context_path)},
        'existingTrees':tree_roots,'sourceRegion':region,'ecologyDomainCm':shapely.to_geojson(domain),
        'exclusionDomainsCm':{key:shapely.to_geojson(value)for key,value in blocked.items()},'groups':groups,
        'ecologyPlacements':placements,'geometryManifest':{'path':str(output/'geometry-manifest.json'),'sha256':sha(output/'geometry-manifest.json')},
        'policy':{'collision':'none','navigation':False,'windDisplacementCm':0,'existingTreeTransformsPreserved':True,
            'broadGroundPatches':False,'privateGeometryUnchanged':True,'textureSourcePixelsUnchanged':True},'audit':audit}
    write(output/'canopy-ecology-plan.json',plan,compact=True);write(output/'canopy-ecology-prototypes.json',records,compact=True)
    write(output/'canopy-ecology-audit.json',audit)
    manifest={**common,'status':'PASS_STATIC_NOT_NATIVE_ACCEPTED','audit':audit,
        'plan':{'path':str(output/'canopy-ecology-plan.json'),'sha256':sha(output/'canopy-ecology-plan.json')},
        'geometryManifest':plan['geometryManifest'],
        'materialManifest':{'path':str(output/'material-manifest.json'),'sha256':sha(output/'material-manifest.json')},
        'geometryProof':{'path':str(output/'canopy-ecology-prototypes.json'),'sha256':sha(output/'canopy-ecology-prototypes.json')},
        'glb':{'path':str(glb),'sha256':sha(glb)},
        'integrationContract':'Merge explicit-only library and append exact ecology groups. Hide nothing. Existing canopy/lawn/ground/source assets and transforms remain unchanged; verify saved geometry and group transforms in the next isolated native candidate.'}
    write(output/'canopy-ecology-manifest.json',manifest);return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in('context','terrain','buildings','scene','assets','output'):parser.add_argument('--'+key,required=True)
    a=parser.parse_args();print(json.dumps(build(a.context,a.terrain,a.buildings,a.scene,a.assets,a.output)))
