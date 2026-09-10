"""Deterministic, explicitly authored fountain tufts; no scene/engine mutation."""
import argparse, hashlib, importlib.util, json, math, re, struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'lib/twin-site.ts').is_file())
SCENE=ROOT/'output/unreal/geometry/scene.json'
OBJ=SCENE.with_name('dom-mm.obj')
SCENE_SHA='61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b'
OBJ_SHA='a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455'
ROOTS=((-10500,4300,-35),(-7600,6000,-35),(7100,12500,-35),(12200,12250,-35),(13900,6300,-35),(14700,11300,-35))
SCALES=(1.05,1.18,1.24,1.02,1.08,1.16)
SUPPORT_IDS=('DOM_01821','DOM_01822','DOM_01692','DOM_00001')
REVISION='AUTHORED-GREEN-FOUNTAIN-72X6-20260909-1'
PALETTE=((71,104,45),(78,110,50),(68,98,43))

def require(ok,message):
    if not ok:raise ValueError(message)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def mul(a,s):return tuple(x*s for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(v):
    length=math.sqrt(dot(v,v));require(length>1e-12,'Degenerate direction');return mul(v,1/length)
def turn(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def area(p):return abs(sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p))))/2 if len(p)>2 else 0.
def hull(points):
    points=sorted(set(tuple(p[:2]) for p in points))
    def side(seq):
        result=[]
        for p in seq:
            while len(result)>1 and turn(result[-2],result[-1],p)<=0:result.pop()
            result.append(p)
        return result
    return side(points)[:-1]+side(reversed(points))[:-1]
def in_convex(p,ring,tol=1e-6):return all(turn(ring[i],ring[(i+1)%len(ring)],p)>=-tol for i in range(len(ring)))
def footprint(faces):
    # A box's lower face is not a second overlapping planting area. Select the
    # actual highest horizontal surface, never its AABB or duplicate bottom.
    horizontal=[f for f in faces if max(v[2] for v in f)-min(v[2] for v in f)<.001 and abs(turn(*f))>1e-6]
    require(horizontal,'Missing horizontal source support')
    top=max(v[2] for f in horizontal for v in f)
    result={}
    for face in horizontal:
        if abs(face[0][2]-top)>.001:continue
        p=[tuple(v[:2]) for v in face]
        if abs(turn(*p))>1e-6:
            if turn(*p)<0:p.reverse()
            result[tuple(sorted(p))]=p
    return list(result.values())
def inside(p,triangles):return any(in_convex(p,t) for t in triangles)
def clip(subject,clipper):
    result=list(subject)
    for a,b in zip(clipper,clipper[1:]+clipper[:1]):
        old=result;result=[]
        if not old:break
        for u,v in zip(old,old[1:]+old[:1]):
            du,dv=turn(a,b,u),turn(a,b,v)
            if du>=0:result.append(u)
            if (du>=0)!=(dv>=0):
                t=du/(du-dv);result.append((u[0]+t*(v[0]-u[0]),u[1]+t*(v[1]-u[1])))
    return result
def covered_triangle(tri,polygons):
    size=area(tri)
    if size<1e-7:return all(inside(p,polygons) for p in tri)
    covered=sum(area(clip(tri,p)) for p in polygons)
    return abs(covered-size)<=max(2e-5,size*1e-7)
def bounds(points):return {'min':[min(p[k] for p in points) for k in range(3)],'max':[max(p[k] for p in points) for k in range(3)]}

class Rng:
    def __init__(self,seed):self.seed=seed
    def next(self):
        self.seed=(1664525*self.seed+1013904223)&0xffffffff
        return self.seed/4294967296
    def between(self,a,b):return a+(b-a)*self.next()

def source_context():
    require(sha(SCENE)==SCENE_SHA and sha(OBJ)==OBJ_SHA,'Source geometry changed')
    scene=json.loads(SCENE.read_text());records={r['id']:r for r in scene['objects']}
    builder=(ROOT/'lib/babylon-scene.ts').read_text()
    ground=re.search(r'const GROUND_Y = (-?[0-9.]+);',builder)
    require(ground is not None and float(ground.group(1))*1000==-35,'Source builder root elevation changed')
    spec=importlib.util.spec_from_file_location('source_vegetation',ROOT/'scripts/unreal/vegetation.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    ids={f'DOM_{i:05}' for i in range(1841,1859)}
    faces=v.read_source_triangles(OBJ,scene,ids|set(SUPPORT_IDS))
    for i,root in enumerate(ROOTS):
        for card in range(3):
            id_=f'DOM_{1841+i*3+card:05}';r=records[id_]
            require(r['materialSlots']==['MAT_0004'] and r['instances']==1 and r['enabled'] and r['triangles']==2,'Card scope differs')
            require(r['sourceId']==f'Okrasná tráva {i+1} · ilustračný koncept · krížená botanická karta {card+1}','Card source identity differs')
        p=[v for f in faces[f'DOM_{1841+i*3:05}'] for v in f]
        require(all(abs((min(v[k] for v in p)+max(v[k] for v in p))/2-root[k])<.001 for k in (0,1)),'Source root differs')
        require(abs(max(v[2] for v in p)-min(v[2] for v in p)-1280*SCALES[i])<.001,'Source card scale differs')
        for card in range(3):
            pts=[v for f in faces[f'DOM_{1841+i*3+card:05}'] for v in f]
            derived_z=(min(v[2] for v in pts)+max(v[2] for v in pts))/2-1280*SCALES[i]*.48-(25 if card==2 else 0)
            require(abs(derived_z-root[2])<.001,'Source card root Z differs from builder')
    return records,faces

def leaf_geometry(rng,index,height):
    ring='inner' if index<24 else 'middle' if index<52 else 'outer'
    h,reach={'inner':((.79,1.),(90,210)),'middle':((.60,.86),(190,350)),'outer':((.38,.63),(320,460))}[ring]
    h=height*rng.between(*h);reach=rng.between(*reach)
    phi=index*math.pi*(3-math.sqrt(5))+rng.between(-.22,.22)
    radial=(math.cos(phi),math.sin(phi),0);widthdir=(-math.sin(phi),math.cos(phi),0)
    start=rng.between(5,26);base=rng.between(1.2,3.3);width=rng.between(11,23)
    sway=rng.between(-.10,.10);points=[];uv=[]
    for section in range(6):
        t=section/6;radius=start+reach*t**1.4
        center=add(mul(radial,radius),mul(widthdir,sway*reach*math.sin(math.pi*t)*t))
        center=add(center,(0,0,h*math.sin(math.pi*.7*t)))
        deriv=add(mul(radial,1.4*reach*max(t,1e-5)**.4),(0,0,h*math.pi*.7*math.cos(math.pi*.7*t)))
        up=unit(cross(deriv,widthdir));w=(base*(1-t)+width*math.sin(math.pi*t)**.7)*(1-.25*t)
        for offset,u in ((-.5,0),(0,.5),(.5,1)):
            points.append(add(add(center,mul(widthdir,w*offset)),mul(up,w*.12 if offset==0 else 0)));uv.append((u,t))
    points.append(add(mul(radial,start+reach),(0,0,h*math.sin(math.pi*.7))));uv.append((.5,1))
    indices=[]
    for s in range(5):
        a,b=s*3,(s+1)*3
        indices.extend(((a,b,a+1),(a+1,b,b+1),(a+1,b+1,a+2),(a+2,b+1,b+2)))
    indices.extend(((15,18,16),(16,18,17)))
    return points,uv,indices,{'ring':ring,'heightParameterMm':h,'reachParameterMm':reach,'maxWidthParameterMm':width,'azimuth':phi}

def make_group(index,records,faces):
    root=ROOTS[index];ids=[f'DOM_{1841+index*3+c:05}' for c in range(3)]
    original=[p for id_ in ids for face in faces[id_] for p in face];envelope=hull(original)
    supports={id_:footprint(faces[id_]) for id_ in SUPPORT_IDS}
    bed_ids=[id_ for id_ in SUPPORT_IDS[:-1] if inside(root[:2],supports[id_])]
    require(inside(root[:2],supports['DOM_00001']),'Original root outside parcel')
    # Never fabricate or move a bed. Where a real bed contains the root, every
    # generated point and projected triangle is additionally clipped to its union.
    bed=supports[bed_ids[0]] if bed_ids else None
    support_id=bed_ids[0] if bed_ids else 'DOM_00001'
    support_top=max(p[2] for face in faces[support_id] for p in face)
    burial=32. if index==3 else 0.
    height=1280*SCALES[index]*.75;rng=Rng(601226+index*1009);positions=[];uvs=[];triangles=[];leaves=[]
    for leaf in range(72):
        points,uv,indices,params=leaf_geometry(rng,leaf,height)
        # Anchor stays exactly source-root. Only the lowest three vertices of
        # group4's leaves extend down32mm into the actual source lawn surface.
        points=[(p[0],p[1],p[2]-(burial if n<3 else 0)) for n,p in enumerate(points)]
        scale=1.
        for attempt in range(80):
            candidate=[(p[0]*scale,p[1]*scale,p[2]) for p in points]
            world=[add(root,p) for p in candidate]
            valid=all(in_convex(p,envelope) and inside(p,supports['DOM_00001']) and (bed is None or inside(p,bed)) for p in world)
            if valid and (bed is None or all(covered_triangle([world[i][:2] for i in tri],bed) for tri in indices)):break
            scale*=.94
        else:raise ValueError('Cannot retain exact root and geometry support')
        require(scale>.06,'Source edge cannot support useful leaf width')
        base=len(positions);positions.extend(candidate);uvs.extend(uv);triangles.extend(tuple(base+i for i in t) for t in indices)
        leaves.append(dict(params,xyEnvelopeScale=scale))
    normals=[(0,0,0)]*len(positions);tans=[(0,0,0)]*len(positions);bitans=[(0,0,0)]*len(positions)
    for a,b,c in triangles:
        e1,e2=sub(positions[b],positions[a]),sub(positions[c],positions[a]);n=cross(e1,e2)
        require(dot(n,n)>1e-10,'Degenerate leaf triangle')
        u1,u2=sub(uvs[b],uvs[a]),sub(uvs[c],uvs[a]);det=u1[0]*u2[1]-u1[1]*u2[0]
        require(abs(det)>1e-9,'Degenerate leaf UV triangle')
        t=mul(sub(mul(e1,u2[1]),mul(e2,u1[1])),1/det);bt=mul(sub(mul(e2,u1[0]),mul(e1,u2[0])),1/det)
        for i in (a,b,c):normals[i]=add(normals[i],n);tans[i]=add(tans[i],t);bitans[i]=add(bitans[i],bt)
    normals=[unit(n) for n in normals];tangents=[]
    for n,t,b in zip(normals,tans,bitans):
        t=unit(sub(t,mul(n,dot(n,t))));tangents.append((*t,-1. if dot(cross(n,t),b)<0 else 1.))
    rgb=PALETTE[index%len(PALETTE)]
    linear=[v/255/12.92 if v/255<=.04045 else ((v/255+.055)/1.055)**2.4 for v in rgb]
    return {'id':f'ORNAMENTAL_GRASS_{index+1:02}','sourceIds':ids,'rootSourceMm':list(root),'rootUnrealCm':[root[0]/10,-root[1]/10,root[2]/10],
            'sourceRecordHashes':{i:digest(records[i]) for i in ids},'sourceGroupXYEnvelopeMm':envelope,'sourceBedIdsAtRoot':bed_ids,
            'supportPolicy':'existing-mulch-polygon' if bed else 'original-root-on-parcel-no-mulch-bed',
            'sourceSupportId':support_id,'sourceSupportTopZMm':support_top,'authoredLowestRowExtensionMm':burial,
            'rootZProof':'GROUND_Y=-0.035 in actual builder and recovered independently from all3sourcecardcentres',
            'originalCardEnvelopeWithinBed':bool(bed and all(inside(p,bed) for p in envelope)),
            'authoredHeightParameterMm':height,'originalCardHeightMm':1280*SCALES[index],
            'material':{'baseColorSRGB8':list(rgb),'baseColorLinear':linear,'roughness':.72,'metallic':0,'twoSided':True,'alphaMode':'OPAQUE','measuredReflectance':False},
            'positions':positions,'normals':normals,'tangents':tangents,'uvs':uvs,'indices':triangles,'leaves':leaves}

def write_glb(group,path):
    # Source Z-up metres → standard glTF Y-up; UE importer maps (X,Z,Y).
    rotate=lambda p:(p[0],p[2],-p[1])
    pos=[tuple(f32(v/1000) for v in rotate(p)) for p in group['positions']]
    norm=[tuple(f32(v) for v in rotate(p)) for p in group['normals']]
    tan=[(*[f32(v) for v in rotate(p[:3])],p[3]) for p in group['tangents']]
    uv=[tuple(f32(v) for v in p) for p in group['uvs']]
    doc={'asset':{'version':'2.0','generator':REVISION},'scene':0,'scenes':[{'nodes':[0]}],
         'nodes':[{'mesh':0,'name':group['id']}],'meshes':[],'buffers':[],'bufferViews':[],'accessors':[],
         'materials':[{'name':'AuthoredGreenFoliage','doubleSided':True,'alphaMode':'OPAQUE','pbrMetallicRoughness':{
             'baseColorFactor':group['material']['baseColorLinear']+[1.],'metallicFactor':0.,'roughnessFactor':.72}}]}
    binary=bytearray()
    def data(rows,kind,component,fmt,target):
        binary.extend(b'\0'*((-len(binary))%4));offset=len(binary)
        binary.extend(b''.join(struct.pack('<'+fmt*len(r),*r) for r in rows));view=len(doc['bufferViews'])
        doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(binary)-offset,'target':target})
        a={'bufferView':view,'componentType':component,'count':len(rows),'type':kind}
        if kind=='VEC3':a.update(bounds(rows))
        doc['accessors'].append(a);return len(doc['accessors'])-1
    attrs={'POSITION':data(pos,'VEC3',5126,'f',34962),'NORMAL':data(norm,'VEC3',5126,'f',34962),'TANGENT':data(tan,'VEC4',5126,'f',34962),'TEXCOORD_0':data(uv,'VEC2',5126,'f',34962)}
    indices=data([(i,) for tri in group['indices'] for i in tri],'SCALAR',5123,'H',34963)
    doc['meshes']=[{'name':group['id'],'primitives':[{'attributes':attrs,'indices':indices,'material':0,'mode':4}]}]
    binary.extend(b'\0'*((-len(binary))%4));doc['buffers']=[{'byteLength':len(binary)}]
    js=canonical(doc).encode();js+=b' '*((-len(js))%4)
    raw=struct.pack('<4sII',b'glTF',2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
    path.write_bytes(raw)
    return [[1000*x,-1000*z,1000*y] for x,y,z in pos]

def verify_group(group,decoded,faces):
    require(len(decoded)==1368 and len(group['indices'])==1584,'Unexpected generated budget')
    require(all(math.isfinite(v) for p in decoded for v in p),'Nonfinite decoded vertex')
    require(max(abs(a-b) for p,q in zip(group['positions'],decoded) for a,b in zip(p,q))<.001,'GLB float32 position quantization')
    root=group['rootSourceMm'];world=[add(root,p) for p in decoded]
    require(all(in_convex(p,group['sourceGroupXYEnvelopeMm'],.002) for p in world),'Decoded point escaped exact source envelope')
    bed=footprint(faces[group['sourceBedIdsAtRoot'][0]]) if group['sourceBedIdsAtRoot'] else None
    require(all(inside(p,footprint(faces['DOM_00001'])) for p in world),'Decoded point escaped parcel')
    require(all(world[i][2]<=group['sourceSupportTopZMm'] for i in range(len(world)) if i%19<3),'A leaf basal row floats above its actual source support')
    require(bed is None or all(inside(p,bed) for p in world),'Decoded point escaped bed')
    require(bed is None or all(covered_triangle([world[i][:2] for i in tri],bed) for tri in group['indices']),'Triangle spans outside bed')
    for tri in group['indices']:
        a,b,c=[decoded[i] for i in tri];require(dot(cross(sub(b,a),sub(c,a)),cross(sub(b,a),sub(c,a)))>1e-10,'Decoded degenerate triangle')
    for n,t in zip(group['normals'],group['tangents']):require(abs(dot(n,n)-1)<1e-6 and abs(dot(t[:3],t[:3])-1)<1e-6 and abs(dot(n,t[:3]))<1e-6,'Invalid tangent basis')
    return {'sourceRootPositionPreserved':True,'allVerticesWithinSourceXYEnvelope':True,'bedPolygonChecked':bed is not None,
            'allVerticesWithinParcel':True,'allLeafBasalRowsReachSourceSupport':True,
            'allVerticesWithinBed':True if bed else None,'allProjectedTrianglesWithinBed':True if bed else None,
            'bedException':None if bed else 'Original root outside all three checked source mulch polygons; not moved and no bed invented.',
            'nativeImportVerified':False,'nativeNormalsVerified':False,'renderedVerified':False,'speciesCalibrated':False}

def generate(output):
    require(not output.exists(),'Use a new output directory; never overwrite earlier candidate')
    records,faces=source_context();output.mkdir(parents=True);groups=[]
    for i in range(6):
        group=make_group(i,records,faces);file=group['id'].lower()+'.glb';decoded=write_glb(group,output/file);proof=verify_group(group,decoded,faces)
        world=[add(group['rootSourceMm'],p) for p in decoded];native=[[p[0]/10,-p[1]/10,p[2]/10] for p in world]
        row={k:v for k,v in group.items() if k not in ('positions','normals','tangents','uvs','indices')}
        row.update(file=file,sha256=sha(output/file),vertices=len(decoded),triangles=len(group['indices']),leafCount=72,segmentsPerLeaf=6,
                   localBoundsMetres=bounds([mul(p,.001) for p in decoded]),boundsSourceMm=bounds(world),boundsUnrealCm=bounds(native),verification=proof)
        groups.append(row)
    report={'schemaVersion':1,'status':'authored-ornamental-geometry-validated','revision':REVISION,'seed':601226,
        'generatorSha256':sha(__file__),'sourceManifestSha256':SCENE_SHA,'sourceObjSha256':OBJ_SHA,
        'sourceFiles':{str(p.relative_to(ROOT)):sha(p) for p in (SCENE,OBJ,ROOT/'lib/babylon-scene.ts',ROOT/'scripts/unreal/vegetation.py')},
        'groups':groups,'sourceIds':[id_ for g in groups for id_ in g['sourceIds']],
        'geometryIsAuthoredIllustrativeCandidate':True,'isScannedAsset':False,'nativeApplied':False,
        'heightPolicy':'0.75 x source first-card height, an explicit authored visual correction; not a measured species or change to canonical geometry',
        'palettePolicy':'Three authored green diffuse colours in sRGB8 converted to linear; no texture/photos or radiometric calibration',
        'broadCreamPlumes':False,'canonicalSourceActorsModified':False,'roadsideCardsModified':False,'perennialsModified':False}
    (output/'ornamental.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    require(a.output.resolve().is_relative_to(HERE),'Output must remain inside this study')
    report=generate(a.output.resolve());print(json.dumps({'status':report['status'],'groups':len(report['groups']),'triangles':sum(g['triangles'] for g in report['groups']),'output':str(a.output)}))
