"""Pinned grove-only tree replacement and additive ecology, stdlib-only.

No Unreal import, asset writes, scene mutations or native actor hiding occurs
here. The caller splices 78 validated rows into the untouched source context,
then creates ordinary new owned actors and verifies saved native transforms.
"""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-canopy-native.py'
CANOPY='scripts/unreal/exterior-canopy-masters.py'
GROWTH='scripts/unreal/exterior-canopy-growth.py'
ECOLOGY='scripts/unreal/exterior-canopy-ecology.py'
UNFLARED='scripts/unreal/exterior-canopy-ecology-unflared.py'
REGION='village_nearest_grove'
BARK='ph_tree_small_02_branches'
FAMILIES={'broadleaf':'regional_broadleaf_a','upright':'regional_upright_b','orchard':'regional_orchard_c'}
CANOPY_IDS={f'canopy_{family}_r1_{variant}'for family in FAMILIES for variant in 'abc'}
GROWTH_IDS={f'canopy_growth_{family}_r1_{variant}'for family in FAMILIES for variant in 'abc'}
GROWTH_STUDY=ROOT/'output/unreal/exterior-canopy-growth-20260930-r1c-study'
GROWTH_PINS={'geometry-manifest.json':'c5ce591bd04ca642fbe3b097b72bc3b09eedd913f6b65665ca93bca29fcfae89',
    'canopy-plan.json':'65e29a7bbced73ce3af4756a9d8a8efe58aba810a024bb73d8a853145412f6d8',
    'growth-skeletons.json':'0ac5857bd28c67f68d7a7ea70873655e524ad3f102d0634741c24afeba7e6301',
    'morphology-audit.json':'79265402640d92b6cefa493ee41a395dfd5089d9a51d97690e4810dd4ec18e97',
    'material-manifest.json':'555da7f3f36cb6b5843e578fa76b298bf47d4740e13c70e5e2397e1a325bb064'}
ECOLOGY_IDS={f'canopy_ecology_{family}_{i}'for family,n in [('litter',3),('twig',3),('herb',3),('grass',2)]for i in range(n)}|{
    f'canopy_ecology_flare_{source}_{i}'for source in FAMILIES.values()for i in range(2)}
CULLS={'litter':8000,'twig':10000,'herb':12000,'grass':10000,'flare':20000}


def require(ok,message):
    if not ok:raise RuntimeError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as stream:
        while block:=stream.read(1024*1024):h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def finite(value,n):
    return isinstance(value,(list,tuple))and len(value)==n and all(isinstance(v,(int,float))and not isinstance(v,bool)and math.isfinite(v)for v in value)


def pinned(path,expected):
    actual=(ROOT/path).resolve()
    require(actual.is_relative_to(ROOT)and actual.is_file()and sha(actual)==expected,'Grove source path/hash differs: '+str(actual))
    return actual


def read_pin(pin):return json.loads(pinned(pin['path'],pin['sha256']).read_text())


def _input_json(plan,suffix):
    paths=[p for p in plan['inputFiles']if p.endswith(suffix)]
    require(len(paths)==1,'Grove mandatory source pin ambiguous/missing: '+suffix)
    return json.loads(pinned(paths[0],plan['inputFiles'][paths[0]]).read_text())


def _common(plan,manifest,context,merged,sceneSha,objSha,owner,kind,ids):
    require(plan.get('schemaVersion')==1 and plan.get('owner')==owner and plan.get('kind')==kind
            and plan.get('regionId')==REGION,'Grove owner/schema/scope differs')
    for record in (plan,manifest):
        require(record.get('owner')==owner and record.get('schema',record.get('schemaVersion'))==1,
                'Grove geometry owner/schema differs')
        require(record['inputFiles'].get(str(ROOT/owner))==sha(ROOT/owner),'Grove generator pin differs')
        for path,value in record['inputFiles'].items():pinned(path,value)
    expected_inputs=dict(manifest['inputFiles'])
    if owner in (CANOPY,GROWTH):
        directory=Path(plan['geometryManifest']['path']).parent
        expected_inputs.update({plan['geometryManifest']['path']:plan['geometryManifest']['sha256'],
            str(directory/'growth-skeletons.json'):sha(directory/'growth-skeletons.json')})
    require(plan['inputFiles']==expected_inputs,'Grove source dependencies differ')
    require(read_pin(plan['sourceContext'])==context and plan['inputFiles'].get(plan['sourceContext']['path'])==plan['sourceContext']['sha256'],
            'Grove original source context differs')
    require(plan['sourceSceneSha256']==context['sourceSceneSha256']==sceneSha and
            plan['sourceObjSha256']==context['sourceObjSha256']==objSha,'Grove scene/OBJ frame differs')
    require(plan['activeDesign']==context['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}
            and plan['housePlacement']==context['housePlacement'] and
            plan['housePlacement']['streetSetbackMm']==plan['housePlacement']['eastSetbackMm']==3000,
            'Grove C/B/B or setbacks differ')
    if owner in (ECOLOGY,UNFLARED):
        require(plan['generatorSha256']==manifest['generatorSha256']==sha(ROOT/owner),'Grove ecology generator differs')
    require(read_pin(plan['geometryManifest'])==manifest,'Grove plan geometry manifest pin differs')
    axes='glTF Y-up; Unreal native = [100*x,100*z,100*y]' if owner in (CANOPY,GROWTH) else 'glTF Y-up; Unreal native=[100*x,100*z,100*y]'
    require(manifest['units']=='metres' and manifest['axes']==axes,
            'Grove geometry native coordinate axes differ')
    meshes={m['id']:m for m in manifest['meshes']};imported={m['id']:m for m in merged['meshes']}
    require(len(meshes)==len(manifest['meshes'])==len(ids)and set(meshes)==ids,'Grove explicit master family inventory differs')
    require(len(imported)==len(merged['meshes'])and all(imported.get(k)==m for k,m in meshes.items()),
            'Grove merged master subset differs')
    trees=[r for r in context['regionalVegetationPlacements']if r['regionId']==REGION]
    require(len(trees)==len({r['id']for r in trees})==78,'Grove original tree census differs')
    directory=Path(plan['geometryManifest']['path']).parent
    recipes=json.loads((directory/'material-manifest.json').read_text())
    old_recipes=_input_json(plan,'exterior-assets-20260927-r7/material-manifest.json')
    for key in (BARK,'regional_green_leaf'):
        require(recipes.get(key)==old_recipes[key],'Grove original bark/leaf recipe differs')
    if owner in (CANOPY,GROWTH):
        require(set(recipes)=={BARK,'regional_green_leaf','regional_oak_leaf'}and recipes['regional_oak_leaf']==old_recipes['regional_oak_leaf'],
                'Grove canopy material recipes differ')
    else:
        for key,source in [('canopy_litter_oak','regional_oak_leaf'),('canopy_litter_green','regional_green_leaf')]:
            recipe=recipes[key];old=old_recipes[source]
            require(recipe['maps']==old['maps']and recipe['sourceUrl']==old['sourceUrl']and recipe['license']=='CC0-1.0'
                    and 0<=recipe['subsurfaceScale']<=.03,'Grove litter photographic source/SSS differs')
    for recipe in recipes.values():
        for mapping in recipe.get('maps',{}).values():
            require(plan['inputFiles'].get(mapping['path'])==mapping['sha256'],'Grove photographic texture input pin missing')
            pinned(mapping['path'],mapping['sha256'])
    return meshes,trees,directory


def _glb_nodes(path,detailed=False):
    raw=Path(path).read_bytes()
    require(len(raw)>=28 and struct.unpack_from('<4sII',raw)==(b'glTF',2,len(raw)),'Grove GLB header differs')
    length,kind=struct.unpack_from('<II',raw,12);require(kind==0x4E4F534A,'Grove GLB JSON missing')
    document=json.loads(raw[20:20+length]);offset=20+length
    binary_length,kind=struct.unpack_from('<II',raw,offset)
    require(kind==0x004E4942 and offset+8+binary_length==len(raw),'Grove GLB binary extent differs')
    binary=memoryview(raw)[offset+8:]
    if detailed:
        require(set(document)=={'asset','scene','scenes','nodes','meshes','buffers','bufferViews','accessors','materials'}
            and document['asset']=={'version':'2.0','generator':GROWTH}
            and document['scene']==0 and document['scenes']==[{'nodes':[0,1,2]}]
            and len(document['nodes'])==len(document['meshes'])==3
            and document['buffers']==[{'byteLength':binary_length}],
            'Growth unmeasured scene/skin/animation/extension refused')
        require(all(set(node)=={'mesh','name'}and node['mesh']==i and
            set(document['meshes'][i])=={'name','primitives'}and document['meshes'][i]['name']==node['name']
            for i,node in enumerate(document['nodes'])),'Growth unmeasured node/mesh deformation refused')
    def accessor(index,expected_type,types):
        a=document['accessors'][index];require(a['type']==expected_type and a['componentType']in types
            and not a.get('sparse')and a['count']>0,'Grove actual accessor type differs')
        view=document['bufferViews'][a['bufferView']];require(view.get('buffer',0)==0,'Grove external buffer refused')
        if detailed:
            require(set(a)<={'bufferView','componentType','count','type','min','max'}and
                set(view)=={'buffer','byteOffset','byteLength','target'}and view['target']in(34962,34963)
                and isinstance(a['count'],int)and not isinstance(a['count'],bool),
                'Growth unmeasured accessor/view modifier refused')
        n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[expected_type]
        size,fmt={5121:(1,'B'),5123:(2,'H'),5125:(4,'I'),5126:(4,'f')}[a['componentType']]
        width=n*size;start=view.get('byteOffset',0)+a.get('byteOffset',0);stride=view.get('byteStride',width)
        require(stride>=width and start+(a['count']-1)*stride+width<=len(binary),'Grove accessor buffer truncated')
        if detailed:require(0<=start and start+a['count']*width==view['byteOffset']+view['byteLength']
            and view['byteLength']==a['count']*width,'Growth actual accessor view extent differs')
        return [struct.unpack_from('<'+fmt*n,binary,start+i*stride)for i in range(a['count'])]
    result={}
    for node in document['nodes']:
        require(node['name']not in result and not any(k in node for k in ('matrix','translation','rotation','scale','children')),
                'Grove GLB node identity/transform differs')
        parts={};details={};all_positions=[];triangle_count=0
        for primitive in document['meshes'][node['mesh']]['primitives']:
            require(primitive.get('mode',4)==4,'Grove must use actual triangle geometry')
            if detailed:require(set(primitive)=={'attributes','indices','material','mode'}and
                set(primitive['attributes'])=={'POSITION','NORMAL','TANGENT','TEXCOORD_0','COLOR_0'},
                'Growth unmeasured morph/primitive modifier refused')
            material=document['materials'][primitive['material']]['name'];require(material not in parts,'Grove primitive material duplicated')
            attrs=primitive['attributes'];p=accessor(attrs['POSITION'],'VEC3',(5126,))
            points=[(100*v[0],100*v[2],100*v[1])for v in p]
            require(all(finite(v,3)for v in points),'Grove decoded position is non-finite')
            indices=[v[0]for v in accessor(primitive['indices'],'SCALAR',(5121,5123,5125))]
            require(len(indices)%3==0 and all(0<=i<len(points)for i in indices),'Grove actual triangle indices escape vertices')
            if detailed:
                normals=accessor(attrs['NORMAL'],'VEC3',(5126,));tangents=accessor(attrs['TANGENT'],'VEC4',(5126,))
                uv=accessor(attrs['TEXCOORD_0'],'VEC2',(5126,));colours=accessor(attrs['COLOR_0'],'VEC4',(5126,))
                require(all(len(v)==len(points)for v in (normals,tangents,uv,colours)),'Growth actual attribute counts differ')
                for n,t,u,c in zip(normals,tangents,uv,colours):
                    require(finite(n,3)and finite(t,4)and finite(u,2)and finite(c,4)
                        and abs(sum(v*v for v in n)-1)<.00002 and abs(sum(v*v for v in t[:3])-1)<.00002
                        and abs(sum(a*b for a,b in zip(n,t)))<.00002 and t[3]in(-1,1)and c==(1.,1.,1.,1.),
                        'Growth actual normal/tangent/neutral colour differs')
                details[material]={'positionsCm':points,'indices':indices,'uv':uv,'normals':normals,'tangents':tangents}
            for offset in range(0,len(indices),3):
                a,b,c=[points[i]for i in indices[offset:offset+3]]
                q=[b[i]-a[i]for i in range(3)];r=[c[i]-a[i]for i in range(3)]
                cross=(q[1]*r[2]-q[2]*r[1],q[2]*r[0]-q[0]*r[2],q[0]*r[1]-q[1]*r[0])
                require(sum(v*v for v in cross)>1e-18,'Grove actual degenerate triangle refused')
                if detailed:
                    # The native axis reflection reverses winding; compare the
                    # stored glTF normals after the same reflection explicitly.
                    ns=[normals[i]for i in indices[offset:offset+3]]
                    mean=[sum(v[i]for v in ns)/3 for i in (0,2,1)]
                    require(sum(a*b for a,b in zip(cross,mean))<0,'Growth actual opposed face/normal refused')
            triangle_count+=len(indices)//3;all_positions.extend(points)
            # Only basal bark vertices are retained after measuring large crowns.
            parts[material]=[v for v in points if -.001<=v[2]<=50.001] if material==BARK else []
        bounds={name:[fn(p[i]for p in all_positions)for i in range(3)]for name,fn in [('min',min),('max',max)]}
        result[node['name']]={'vertices':len(all_positions),'triangles':triangle_count,'bounds':bounds,
            'radius':max(math.hypot(*p[:2])for p in all_positions),'materials':set(parts),'basal':parts.get(BARK,[])}
        if detailed:result[node['name']]['details']=details
    return result


def _measured_library(meshes,detailed=False):
    paths={(r['glbPath'],r['glbSha256'])for r in meshes.values()};decoded={}
    for path,value in paths:
        nodes=_glb_nodes(pinned(path,value),detailed=detailed);require(not(set(nodes)&set(decoded)),'Grove decoded LOD node duplicated');decoded.update(nodes)
    require(set(decoded)=={k+'_LOD'+str(i)for k in meshes for i in range(3)},'Grove actual LOD node inventory differs')
    envelopes={}
    for key,row in meshes.items():
        require(row['placementPolicy']=='explicit-only'and[row_lod['level']for row_lod in row['lods']]==[0,1,2],
                'Grove explicit geometry/LOD scope differs')
        low=math.inf;high=-math.inf;radius=0
        for lod in row['lods']:
            actual=decoded[lod['nodeName']];require(lod['nodeName']==key+'_LOD'+str(lod['level']),'Grove LOD node identity differs')
            require(actual['vertices']==lod['vertices']and actual['triangles']==lod['triangles']
                    and actual['materials']==set(row['materialKeys']),'Grove decoded geometry/material inventory differs')
            require(all(abs(actual['bounds'][name][i]-lod['expectedBoundsCm'][name][i])<.0002 for name in ('min','max')for i in range(3)),
                    'Grove actual decoded bounds differ')
            require(abs(actual['radius']-lod['radialEnvelopeCm'])<.0002,'Grove actual radial envelope differs')
            low=min(low,actual['bounds']['min'][2]);high=max(high,actual['bounds']['max'][2]);radius=max(radius,actual['radius'])
        if 'ecologyFamily' in row:
            require(abs(high-row['heightCm'])<.0002 and low>=(-1.401 if row['ecologyFamily']=='flare'else-.1),
                    'Grove ecology measured root-relative height differs')
        else:require(high-low<=row['heightCm']+.001,'Grove measured height envelope differs')
        envelopes[key]={'radius':radius,'height':high-low,'minZ':low,'maxZ':high}
    return envelopes,decoded


def _basal_compatibility(meshes,decoded,old_skeleton,audit):
    for key,row in meshes.items():
        old=old_skeleton[row['sourceFamily']];trunk=old['branches'][0];factor=old['sharedUniformScale']
        proof=audit['meshes'][key];require(proof['sourceFamily']==row['sourceFamily'],'Grove original basal family differs')
        expected=[];radii=[]
        for z in (0,10,25,40,50):
            t=z/(trunk['points'][-1][2]*100*factor)
            p=[sum(trunk['points'][j][i]*weight for j,weight in enumerate(((1-t)**2,2*t*(1-t),t*t)))for i in range(3)]
            expected.append([p[0]*100*factor,-p[1]*100*factor,z])
            radii.append((trunk['radius']*(1-t)+trunk['tipRadius']*t)*100*factor)
        require(all(math.dist(a,b)<1e-7 for a,b in zip(expected,proof['basalAxisSamplesCm']))
                and len(proof['basalAxisSamplesCm'])==len(proof['basalRadiiCm'])==5
                and all(abs(a-b)<1e-7 for a,b in zip(radii,proof['basalRadiiCm'])), 'Grove original lower50cm proof differs')
        for lod in row['lods']:
            for center,radius in zip(expected,radii):
                ring=[p for p in decoded[lod['nodeName']]['basal']if abs(p[2]-center[2])<.0001]
                require(len(ring)>=9 and math.dist(ring[0],ring[-1])<.0002,'Grove lower50cm decoded bark ring differs')
                ring=ring[:-1];mean=[sum(p[i]for p in ring)/len(ring)for i in range(2)]
                require(math.dist(mean,center[:2])<.0002 and all(abs(math.dist(p[:2],center[:2])-radius)<.0002 for p in ring),
                        'Grove lower50cm actual axis/radius incompatible')


def validated_replacements(plan,extension_manifest,source_context,imported_manifest,sceneSha,objSha):
    if plan.get('owner')==GROWTH:
        return _validated_growth(plan,extension_manifest,source_context,imported_manifest,sceneSha,objSha)
    meshes,trees,directory=_common(plan,extension_manifest,source_context,imported_manifest,sceneSha,objSha,CANOPY,'grove-only-canopy-replacement',CANOPY_IDS)
    require(plan['originalCanopyPlacements']==trees and len(plan['canopyPlacements'])==78,'Grove original roots/order differs')
    require(plan['policy']=={'preserveRootYawScaleHeightAndRadialEnvelope':True,'targetGroveOnly':True,
        'sourcePhotographsUnmodified':True,'speciesAgeAndExactRootNotSurveyed':True,'nativeAppearanceAccepted':False},'Grove replacement policy differs')
    old_meshes={r['id']:r for r in _input_json(plan,'exterior-assets-20260927-r7/geometry-manifest.json')['meshes']}
    envelopes,decoded=_measured_library(meshes)
    proof=json.loads((directory/'morphology-audit.json').read_text())
    _basal_compatibility(meshes,decoded,_input_json(plan,'exterior-regional-assets-20260927-r4/growth-skeletons.json'),proof)
    counts=Counter()
    for new,old in zip(plan['canopyPlacements'],trees):
        key=new['meshId'];require(key in meshes and new.get('sourceMeshId')==old['meshId']
                and {k:v for k,v in new.items()if k not in ('meshId','sourceMeshId')}=={k:v for k,v in old.items()if k!='meshId'},
                'Grove exact root/yaw/scale/metadata preservation failed')
        scale=new['scale'];require(finite(new['positionCm'],3)and finite(scale,3)and 0<scale[0]and max(scale)==min(scale),
                'Grove actual uniform transform invalid')
        mesh=meshes[key];require(mesh['role']=='tree'and mesh['sourceFamily']==old['meshId']
                and mesh['heightCm']==old_meshes[old['meshId']]['heightCm']
                and mesh['lods'][0]['triangles']<=old_meshes[old['meshId']]['lods'][0]['triangles'], 'Grove source family/height/budget differs')
        envelope=envelopes[key]
        require(envelope['radius']*scale[0]<=old['radiusCm']+.001 and envelope['height']*scale[0]<=old['heightCm']+.001
                and envelope['radius']<=old_meshes[old['meshId']]['radialEnvelopeCm']+.0002,
                'Grove replacement exceeds inherited full crown envelope')
        counts[key]+=1
    require(plan['audit']=={'originalRootsPreserved':78,'variants':9,'lods':27,'materialRecipesAdded':0,'perMesh':dict(counts)},'Grove replacement audit inventory differs')
    replacements={r['id']:r for r in plan['canopyPlacements']}
    all_rows=[replacements.get(r['id'],r)for r in source_context['regionalVegetationPlacements']]
    require(len(all_rows)==len(source_context['regionalVegetationPlacements'])and all(a==b for a,b in zip(all_rows,source_context['regionalVegetationPlacements'])if b['regionId']!=REGION),
            'Grove replacement altered non-grove source groups')
    return {'placements':deepcopy(plan['canopyPlacements']),'audit':{'status':'verified-source-grove-canopy-replacement',
        'masters':9,'lods':27,'instances':78,'deletedTrees':0,'hiddenOriginalActors':0,'allOriginalRootYawScaleMetadataPreserved':True,
        'nonGroveRegionalRowsPreserved':True,'allLodBasalCompatibilityHeightCm':50,'allDecodedEnvelopesInsideOriginal':True,
        'sourceMaterialsUnchanged':True,'sourceContext':deepcopy(plan['sourceContext']),
        'morphologyProof':{'path':str(directory/'morphology-audit.json'),'sha256':sha(directory/'morphology-audit.json')},
        'sourceSkeleton':{'path':str(next(Path(p)for p in plan['inputFiles']if p.endswith('exterior-regional-assets-20260927-r4/growth-skeletons.json'))),
            'sha256':next(v for p,v in plan['inputFiles'].items()if p.endswith('exterior-regional-assets-20260927-r4/growth-skeletons.json'))},
        'nativeAppearanceAccepted':False}}


def _growth_approved():
    # Approved immutable authoring data, not an appearance approval. A caller
    # cannot widen source limits or invent morphology by repinning its own JSON.
    return {name:json.loads(pinned(GROWTH_STUDY/name,value).read_text())for name,value in GROWTH_PINS.items()}


def _add(a,b):return [x+y for x,y in zip(a,b)]
def _sub(a,b):return [x-y for x,y in zip(a,b)]
def _mul(a,s):return [x*s for x in a]
def _dot(a,b):return sum(x*y for x,y in zip(a,b))
def _cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def _unit(a):
    length=math.sqrt(_dot(a,a));require(length>1e-12,'Growth zero direction refused');return _mul(a,1/length)
def _quadratic(points,t):return [points[0][i]*(1-t)**2+points[1][i]*2*t*(1-t)+points[2][i]*t*t for i in range(3)]


def _growth_axis(old,z):
    trunk=old['branches'][0];factor=old['sharedUniformScale']
    p=_quadratic(trunk['points'],z/(trunk['points'][-1][2]*100*factor))
    return [p[0]*100*factor,-p[1]*100*factor,z]


def _growth_radius(old,z):
    trunk=old['branches'][0];factor=old['sharedUniformScale'];t=z/(trunk['points'][-1][2]*100*factor)
    return (trunk['radius']*(1-t)+trunk['tipRadius']*t)*100*factor


def _growth_evaluate(branch,t):
    if branch['kind']!='trunk':return _quadratic(branch['points'],t)
    z=branch['height']*t
    return _growth_axis(branch['oldBasalAxis'],z)if z<=50 else _quadratic(branch['upperPoints'],(z-50)/(branch['height']-50))


def _growth_fit(point,fit):
    weight=min(1.,max(0.,(point[2]-50)/70));factor=1+(fit['outerXYFactor']-1)*weight
    return [point[0]*factor,point[1]*factor,point[2]if point[2]<=50 else 50+(point[2]-50)*fit['upperZFactor']]


def _growth_tube(branch,lod):
    """Independent stdlib reconstruction of stored connected bark surfaces."""
    order=branch['order'];segments=([12,6,4,2],[9,4,3,2],[7,3,2,1])[lod][order]
    sides=([14,9,6,4],[10,7,5,3],[8,5,4,3])[lod][order]
    ts={j/segments for j in range(segments+1)if order!=0 or not 50.<branch['height']*j/segments<70.}
    if order==0:ts.update(z/branch['height']for z in(0.,10.,25.,40.,50.)if z<branch['height'])
    ts=sorted(ts);path=[_growth_evaluate(branch,t)for t in ts]
    chord=_unit(_sub(path[-1],path[0]));reference=[0,0,1]if abs(chord[2])<.99 else[0,1,0]
    stable=[1,0,0]if order==0 else _unit(_cross(chord,reference));distance=0.;points=[];uv=[];faces=[]
    for j,(t,p)in enumerate(zip(ts,path)):
        tangent=_unit(_sub(path[min(len(path)-1,j+1)],path[max(0,j-1)]))
        a=_unit(_sub(stable,_mul(tangent,_dot(stable,tangent))));b=_unit(_cross(tangent,a))
        radius=branch['radius']*(1-t)**.83+branch['tipRadius']*t
        if order==0 and p[2]<=75.+1e-7:
            a,b=[1,0,0],[0,1,0]
            if p[2]<=50.+1e-7:radius=_growth_radius(branch['oldBasalAxis'],p[2])
        if j:distance+=math.dist(p,path[j-1])
        for k in range(sides+1):
            angle=math.tau*k/sides
            points.append(_add(p,_add(_mul(a,radius*math.cos(angle)),_mul(b,radius*math.sin(angle)))))
            uv.append([math.tau*branch['radius']*k/sides/25.,distance/25.])
    for j in range(len(path)-1):
        for k in range(sides):
            a=j*(sides+1)+k;b=a+sides+1;faces.extend([(a,a+1,b),(a+1,b+1,b)])
    return points,uv,faces


def _growth_leaf(leaf,lod,factor):
    along=leaf['along'];side=_unit(_cross(along,[0,0,1]));normal=_unit(_cross(side,along));roll=leaf['roll']
    side,normal=_add(_mul(side,math.cos(roll)),_mul(normal,math.sin(roll))),_add(_mul(normal,math.cos(roll)),_mul(side,-math.sin(roll)))
    length=leaf['length']*factor;width=length*leaf['aspect'];columns=[0,.5,1]if lod<2 else[0,1]
    points=[];uv=[];faces=[]
    for t in(0,.5,1):
        for u in columns:
            x=u-.5;fold=length*(leaf['curl']*math.sin(math.pi*t)+.025*math.sin(math.pi*t)*(1-abs(x)*2))
            twist=length*leaf['twist']*x*t
            points.append(_add(leaf['base'],_add(_mul(along,length*t),_add(_mul(side,width*x),_mul(normal,fold+twist)))))
            uv.append([1-u if leaf['mirror']else u,1-t])
    size=len(columns)
    for j in range(2):
        for k in range(size-1):
            a=j*size+k;b=a+size;faces.extend([(a,b,a+1),(a+1,b,b+1)])
    return points,uv,faces


def _growth_basis(positions,uv,faces):
    """Area-weighted surface normals and the photographic UV tangent frame."""
    normals=[[0.,0.,0.]for _ in positions];tangents=[[0.,0.,0.]for _ in positions];bitangents=[[0.,0.,0.]for _ in positions]
    for a,b,c in faces:
        e1,e2=_sub(positions[b],positions[a]),_sub(positions[c],positions[a]);normal=_cross(e1,e2)
        d1,d2=_sub(uv[b],uv[a]),_sub(uv[c],uv[a]);det=d1[0]*d2[1]-d1[1]*d2[0]
        require(abs(det)>1e-12,'Growth reconstructed photographic UV is degenerate')
        tangent=_mul(_sub(_mul(e1,d2[1]),_mul(e2,d1[1])),1/det)
        bitangent=_mul(_sub(_mul(e2,d1[0]),_mul(e1,d2[0])),1/det)
        for index in(a,b,c):
            normals[index]=_add(normals[index],normal);tangents[index]=_add(tangents[index],tangent)
            bitangents[index]=_add(bitangents[index],bitangent)
    frames=[]
    for normal,tangent,bitangent in zip(normals,tangents,bitangents):
        normal=_unit(normal);tangent=_unit(_sub(tangent,_mul(normal,_dot(tangent,normal))))
        handed=-1 if _dot(_cross(normal,tangent),bitangent)<0 else 1
        frames.append(([normal[0],normal[2],normal[1]],[tangent[0],tangent[2],tangent[1],-handed]))
    return frames


def _growth_piece(actual,cursor,piece,fit,label):
    offset,face_offset=cursor;positions,uv,faces=piece
    require(offset+len(positions)<=len(actual['positionsCm']),'Growth decoded '+label+' vertex count differs')
    fitted=[_growth_fit(p,fit)for p in positions]
    require(all(math.dist(p,q)<.00025 for p,q in zip(fitted,actual['positionsCm'][offset:offset+len(positions)])),
            'Growth actual '+label+' differs from connected source skeleton')
    require(all(math.dist(a,b)<.00002 for a,b in zip(uv,actual['uv'][offset:offset+len(uv)])),
            'Growth actual '+label+' photographic UV differs')
    indices=[offset+i for a,b,c in faces for i in(a,c,b)]
    require(actual['indices'][face_offset:face_offset+len(indices)]==indices,'Growth actual '+label+' topology differs')
    frames=_growth_basis(fitted,uv,faces)
    require(all(math.dist(n,actual['normals'][offset+i])<.00002 and math.dist(t,actual['tangents'][offset+i])<.00002
        for i,(n,t)in enumerate(frames)),'Growth actual area normal/UV tangent differs from connected surface')
    return offset+len(positions),face_offset+len(indices)


def _growth_morphology(meshes,decoded,morphology,proof,old_skeleton):
    require(set(morphology)==set(proof['meshes'])==GROWTH_IDS,'Growth skeleton/proof master inventory differs')
    for key,row in meshes.items():
        morph=morphology[key];branches=morph['branches'];leaves=morph['leaves'];clusters=morph['clusters'];audit=proof['meshes'][key]
        require(morph['sourceFamily']==row['sourceFamily']and morph['heightCm']==row['heightCm']
            and row['branches']==len(branches)and row['leafCount']==len(leaves)and row['clusterCount']==len(clusters),
            'Growth actual skeleton/leaf inventory differs')
        require(branches[0]['kind']=='trunk'and branches[0]['parent']is None and branches[0]['order']==0
            and branches[0]['oldBasalAxis']=={'branches':[old_skeleton[row['sourceFamily']]['branches'][0]],
                'sharedUniformScale':old_skeleton[row['sourceFamily']]['sharedUniformScale']},'Growth original lower trunk source differs')
        children=defaultdict(list)
        for i,branch in enumerate(branches[1:],1):
            parent,t=branch['parent'],branch['parentT']
            require(isinstance(parent,int)and not isinstance(parent,bool)and 0<=parent<i and 0<=t<=1
                and branch['kind']=='limb'and branch['order']in(1,3)and 0<branch['tipRadius']<branch['radius']
                and math.dist(branch['points'][0],_growth_evaluate(branches[parent],t))<1e-7,'Growth disconnected/untapered branch refused')
            children[parent].append(i)
        shoots={i for i,b in enumerate(branches)if b.get('terminalLeafShoot')is True}
        require(shoots and not any(i in children for i in shoots)and {l['branch']for l in leaves}==shoots,
            'Growth leaves must attach only to terminal connected shoots')
        for leaf in leaves:
            require(6.7<leaf['length']<12.8 and math.dist(leaf['base'],_growth_evaluate(branches[leaf['branch']],leaf['t']))<1e-7,
                    'Growth leaf anatomy/attachment differs')
        by_cluster=defaultdict(list)
        for i,l in enumerate(leaves):by_cluster[l['cluster']].append(i)
        require(set(by_cluster)==set(range(len(clusters)))and morph['growth']['leafClusterEllipsoids']is False,
                'Growth disconnected cluster inventory differs')
        extremes=set()
        for ids in by_cluster.values():
            for dimension in range(3):
                extremes.add(min(ids,key=lambda i:leaves[i]['base'][dimension]));extremes.add(max(ids,key=lambda i:leaves[i]['base'][dimension]))
        fit=morph['authoringFit'];require(fit==audit['authoringFit']and fit['basalLockHeightCm']==50.
            and fit['allLodsShareSameMap']is True and fit['actorScaleRemainsUniformAndUnchanged']is True,'Growth authoring frame differs')
        for cluster in clusters:
            require(math.dist(cluster['center'],_growth_evaluate(branches[cluster['branch']],1.))<1e-7,
                    'Growth terminal support center differs')
        require(len(audit['clusters'])==len(clusters)and all(a['id']==c['id']and a['branch']==c['branch']
            and math.dist(a['centerCm'],_growth_fit(c['center'],fit))<1e-7 for a,c in zip(audit['clusters'],clusters)),
                'Growth actual retained attachment centers differ')
        selections=[]
        for lod in range(3):
            selected=[i for i in range(len(leaves))if i%(1,2,4)[lod]==0 or i in extremes];selections.append(set(selected))
            require(audit['lodLeafIds'][str(lod)]==selected and row['lods'][lod]['leafCount']==len(selected),
                    'Growth nested leaf identities/LOD sampling differ')
            parts=decoded[key+'_LOD'+str(lod)]['details'];cursor=(0,0)
            for b in branches:cursor=_growth_piece(parts[BARK],cursor,_growth_tube(b,lod),fit,'branch surface')
            require(cursor==(len(parts[BARK]['positionsCm']),len(parts[BARK]['indices'])),'Growth bark hierarchy geometry differs')
            cursor=(0,0);part=parts[morph['leafMaterial']]
            for i in selected:
                factor=1. if i in extremes else(1.,1.18,1.60)[lod]
                cursor=_growth_piece(part,cursor,_growth_leaf(leaves[i],lod,factor),fit,'leaf tissue')
            require(cursor==(len(part['positionsCm']),len(part['indices'])),'Growth terminal leaf geometry differs')
        require(selections[2]<=selections[1]<=selections[0],'Growth nested leaf identity membership differs')


def _validated_growth(plan,manifest,context,merged,sceneSha,objSha):
    approved=_growth_approved();template=approved['geometry-manifest.json'];source_plan=approved['canopy-plan.json']
    require(set(plan)==set(source_plan)and set(manifest)==set(template),'Growth unreviewed source/census schema refused')
    require(all(manifest[k]==v for k,v in template.items()if k not in('meshes','inputFiles')),
            'Growth immutable authoring status/frame/metadata differs')
    require(manifest['inputFiles']==template['inputFiles']and plan['sourceContext']==source_plan['sourceContext'],
            'Growth original immutable source dependencies differ')
    meshes,trees,directory=_common(plan,manifest,context,merged,sceneSha,objSha,GROWTH,'isolated-grove-canopy-growth-study',GROWTH_IDS)
    require(plan['policy']==source_plan['policy']and plan['originalCanopyPlacements']==trees
        and len(plan['canopyPlacements'])==78,'Growth original root/collision/census policy differs')
    for new,old in zip(plan['canopyPlacements'],trees):
        choice=int(hashlib.sha256(old['id'].encode()).hexdigest()[:8],16)%3
        family=next(k for k,v in FAMILIES.items()if v==old['meshId'])
        expected=f'canopy_growth_{family}_r1_{"abc"[choice]}'
        require(new['meshId']==expected and new.get('sourceMeshId')==old['meshId']and
            {k:v for k,v in new.items()if k not in('meshId','sourceMeshId')}=={k:v for k,v in old.items()if k!='meshId'},
            'Growth exact original root/yaw/scale/variant/evidence preservation failed')
    trusted={m['id']:m for m in template['meshes']}
    for key,row in meshes.items():
        require({k:v for k,v in row.items()if k not in('glbPath','glbSha256')}==
                {k:v for k,v in trusted[key].items()if k not in('glbPath','glbSha256')},'Growth immutable height/radius/material/master limits differ')
    own_skeleton=directory/'growth-skeletons.json'
    require(plan['inputFiles'].get(str(own_skeleton))==GROWTH_PINS['growth-skeletons.json']
        and sha(own_skeleton)==GROWTH_PINS['growth-skeletons.json'],'Growth immutable connected skeleton pin differs')
    require(sha(directory/'morphology-audit.json')==GROWTH_PINS['morphology-audit.json']
        and sha(directory/'material-manifest.json')==GROWTH_PINS['material-manifest.json'],'Growth immutable morphology/recipe proof differs')
    morphology=json.loads(own_skeleton.read_text());proof=approved['morphology-audit.json']
    envelopes,decoded=_measured_library(meshes,detailed=True)
    old_skeleton=_input_json(plan,'exterior-regional-assets-20260927-r4/growth-skeletons.json')
    _basal_compatibility(meshes,decoded,old_skeleton,proof)
    _growth_morphology(meshes,decoded,morphology,proof,old_skeleton)
    reference=_input_json(plan,'exterior-canopy-masters-20260930-r1d/geometry-manifest.json')
    reference_rows={m['id']:m for m in reference['meshes']};reference_plan=_input_json(plan,'exterior-canopy-masters-20260930-r1d/canopy-plan.json')
    old_meshes={m['id']:m for m in _input_json(plan,'exterior-assets-20260927-r7/geometry-manifest.json')['meshes']}
    counts=Counter();budgets=[0,0,0]
    for new,old in zip(plan['canopyPlacements'],trees):
        key=new['meshId'];choice=int(hashlib.sha256(old['id'].encode()).hexdigest()[:8],16)%3
        family=next(k for k,v in FAMILIES.items()if v==old['meshId']);expected=f'canopy_growth_{family}_r1_{"abc"[choice]}'
        require(key==expected and new.get('sourceMeshId')==old['meshId']and
            {k:v for k,v in new.items()if k not in('meshId','sourceMeshId')}=={k:v for k,v in old.items()if k!='meshId'},
            'Growth exact original root/yaw/scale/variant/evidence preservation failed')
        scale=new['scale'];require(finite(scale,3)and max(scale)==min(scale)and scale[0]>0,'Growth uniform actor scale differs')
        mesh=meshes[key];actual=envelopes[key];limit=reference_rows[key.replace('canopy_growth_','canopy_')]
        require(mesh['role']=='tree'and mesh['sourceFamily']==old['meshId']and mesh['heightCm']==old_meshes[old['meshId']]['heightCm']
            and actual['minZ']>=-.0002 and abs(actual['maxZ']-limit['heightCm'])<.0002
            and actual['radius']<=limit['radialEnvelopeCm']+.0002 and actual['radius']*scale[0]<=old['radiusCm']+.001
            and actual['height']*scale[0]<=old['heightCm']+.001 and mesh['lods'][0]['triangles']<=limit['lods'][0]['triangles'],
            'Growth actual all-LOD original height/radius/near budget exceeded')
        for i in range(3):budgets[i]+=mesh['lods'][i]['triangles']
        counts[key]+=1
    require(plan['audit']=={'originalRootsPreserved':78,'variants':9,'lods':27,'materialRecipesAdded':0,'perMesh':dict(counts)},
            'Growth actual placement inventory differs')
    current_budgets=[sum(reference_rows[r['meshId']]['lods'][i]['triangles']for r in reference_plan['canopyPlacements'])for i in range(3)]
    require(budgets[0]<=current_budgets[0]==10041120,'Growth actual grove near triangle budget exceeded')
    require(len(context['regionalVegetationPlacements'])-78==1022,'Growth original non-grove inventory differs')
    replacements={r['id']:r for r in plan['canopyPlacements']};all_rows=[replacements.get(r['id'],r)for r in context['regionalVegetationPlacements']]
    require(all(a==b for a,b in zip(all_rows,context['regionalVegetationPlacements'])if b['regionId']!=REGION),
            'Growth altered non-grove source rows')
    return {'placements':deepcopy(plan['canopyPlacements']),'audit':{'status':'verified-source-grove-canopy-growth',
        'masters':9,'lods':27,'instances':78,'deletedTrees':0,'hiddenOriginalActors':0,'nonGroveRegionalRowsPreserved':1022,
        'allOriginalRootYawScaleMetadataPreserved':True,'allLodBasalCompatibilityHeightCm':50,'allDecodedEnvelopesInsideOriginal':True,
        'actualConnectedHierarchyAndTerminalLeafGeometryVerified':True,'actualNestedLeafIdentitiesVerified':True,
        'actualAreaNormalsAndUvTangentsVerified':True,
        'sourceMaterialsUnchanged':True,'collisionActorsChanged':False,'allInstancesTriangleBudgetByLod':budgets,
        'currentCanopyTriangleBudgetByLod':current_budgets,'farCostAccepted':False,'sourceContext':deepcopy(plan['sourceContext']),
        'morphologyProof':{'path':str(directory/'morphology-audit.json'),'sha256':sha(directory/'morphology-audit.json')},
        'sourceSkeleton':{'path':str(own_skeleton),'sha256':sha(own_skeleton)},'nativeAppearanceAccepted':False}}


def _inside_ring(point,ring):
    inside=False;x,y=point
    for a,b in zip(ring,ring[1:]+ring[:1]):
        if(a[1]>y)!=(b[1]>y)and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside


def _distance(point,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];size=dx*dx+dy*dy
    t=min(1.,max(0.,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/size))if size else 0
    return math.hypot(point[0]-a[0]-t*dx,point[1]-a[1]-t*dy)


class _Geo:
    def __init__(self,geometry,cell=250):
        if isinstance(geometry,str):geometry=json.loads(geometry)
        require(geometry['type']in('Polygon','MultiPolygon'),'Grove domain must be ordinary polygon geometry')
        self.polygons=geometry['coordinates']if geometry['type']=='MultiPolygon'else[geometry['coordinates']]
        self.bounds=[];self.edges=[];self.tiles=defaultdict(set);self.cell=cell
        for polygon in self.polygons:
            require(polygon and all(len(r)>=4 and r[0]==r[-1]and all(finite(p,2)for p in r)for r in polygon),'Grove polygon rings invalid')
            points=[p for r in polygon for p in r];self.bounds.append([min(p[0]for p in points),min(p[1]for p in points),max(p[0]for p in points),max(p[1]for p in points)])
            for ring in polygon:
                for a,b in zip(ring,ring[1:]):
                    index=len(self.edges);self.edges.append((a,b))
                    for x in range(math.floor(min(a[0],b[0])/cell),math.floor(max(a[0],b[0])/cell)+1):
                        for y in range(math.floor(min(a[1],b[1])/cell),math.floor(max(a[1],b[1])/cell)+1):self.tiles[x,y].add(index)
    def inside(self,point):
        return any(b[0]<=point[0]<=b[2]and b[1]<=point[1]<=b[3]and _inside_ring(point,p[0])and not any(_inside_ring(point,r)for r in p[1:])for p,b in zip(self.polygons,self.bounds))
    def clearance(self,point):
        x,y=[math.floor(p/self.cell)for p in point];best=math.inf;seen=set()
        for step in range(0,400):
            for dx in range(-step,step+1):
                for dy in range(-step,step+1):
                    if step and abs(dx)!=step and abs(dy)!=step:continue
                    for index in self.tiles.get((x+dx,y+dy),()):
                        if index not in seen:seen.add(index);best=min(best,_distance(point,*self.edges[index]))
            if best<step*self.cell:return best
        require(False,'Grove domain boundary search exceeded bounded extent')
    def outside_clear(self,point,margin):
        for p,b in zip(self.polygons,self.bounds):
            if point[0]+margin<b[0]or point[0]-margin>b[2]or point[1]+margin<b[1]or point[1]-margin>b[3]:continue
            require(not(_inside_ring(point,p[0])and not any(_inside_ring(point,h)for h in p[1:]))
                    and min(_distance(point,a,b)for ring in p for a,b in zip(ring,ring[1:]))>=margin,
                    'Grove full footprint intersects actual source exclusion')
    def area(self):
        def ring(r):return abs(sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(r,r[1:])))*.5
        return sum(ring(p[0])-sum(ring(h)for h in p[1:])for p in self.polygons)


def _polygons(rings):return {'type':'MultiPolygon','coordinates':rings}


def _scene_native(point,scene):
    datum,axes=scene['cadastralDatumSjtskMm'],scene['siteAxis'];placement=scene['housePlacement']['translationMm'];center=scene['sceneCenterMm']
    dx,dy=point[0]-datum['x'],point[1]-datum['y']
    x=math.floor(dx*axes['ux']+dy*axes['uy']+.5)-placement['x'];y=math.floor(dx*axes['vx']+dy*axes['vy']+.5)-placement['y']
    return[(x-center['x'])/10,-(y-center['y'])/10]


def _source_constraints(context,buildings,scene):
    blocked={'protected':[[t+[t[0]]]for t in context['protectedTrianglesCm']],'subject':[],'roads':[],
        'buildings':[rings for building in buildings['buildings']for rings in building['polygonsCm']],'cultivatedGround':[]}
    for key in ('buildings',):
        blocked[key]=[[r if r[0]==r[-1]else r+[r[0]]for r in p]for p in blocked[key]]
    for parcel in context['parcels']:
        if parcel['parcelNumber']not in('6012/26','6012/1','6035/1','6013','6019'):continue
        key='subject'if parcel['parcelNumber']=='6012/26'else'roads'
        for polygon in parcel['polygonsSjtskMm']:
            rings=[[_scene_native(p,scene)for p in ring]for ring in polygon]
            blocked[key].append([r if r[0]==r[-1]else r+[r[0]]for r in rings])
    for mesh in context['meshes']:
        if mesh['material']not in('context_crop','context_arable'):continue
        for i in range(0,len(mesh['indices']),3):
            p=[mesh['verticesCm'][j][:2]for j in mesh['indices'][i:i+3]]
            if abs(sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(p,p[1:]+p[:1])))>2e-6:blocked['cultivatedGround'].append([p+[p[0]]])
    return[_Geo(_polygons(polygons))for polygons in blocked.values()if polygons]


def _circle_in_crowns(point,radius,trees):
    intervals=[];circles=[]
    for tree in trees:
        center=tree['positionCm'][:2];r=tree['radiusCm'];d=math.dist(point,center)
        if d+radius<=r:return True
        if d>=r+radius or d==0:continue
        alpha=math.acos(max(-1.,min(1.,(d*d+radius*radius-r*r)/(2*d*radius))))
        angle=math.atan2(center[1]-point[1],center[0]-point[0])%math.tau;lo,hi=angle-alpha,angle+alpha
        if lo<0:intervals.extend([(0,hi),(lo+math.tau,math.tau)])
        elif hi>math.tau:intervals.extend([(lo,math.tau),(0,hi-math.tau)])
        else:intervals.append((lo,hi))
        circles.append((center,r))
    end=0.
    for lo,hi in sorted(intervals):
        if lo>end+1e-10:return False
        end=max(end,hi)
    if end<math.tau-1e-10:return False
    # Exclude a hole wholly within the small footprint: uncovered neighborhoods
    # of any pairwise source-circle boundary intersection must lie outside it.
    for i,(a,ra)in enumerate(circles):
        for b,rb in circles[i+1:]:
            d=math.dist(a,b)
            if not abs(ra-rb)<d<ra+rb:continue
            along=(ra*ra-rb*rb+d*d)/(2*d);height=math.sqrt(max(0,ra*ra-along*along));v=[(b[j]-a[j])/d for j in range(2)]
            for sign in(-1,1):
                p=[a[0]+along*v[0]-sign*height*v[1],a[1]+along*v[1]+sign*height*v[0]]
                if math.dist(p,point)>=radius:continue
                for dx,dy in((.0001,0),(-.0001,0),(0,.0001),(0,-.0001)):
                    q=[p[0]+dx,p[1]+dy]
                    if math.dist(q,point)<radius and not any(math.dist(q,t['positionCm'][:2])<=t['radiusCm']for t in trees):return False
    return True


class _Ground:
    def __init__(self,context,terrain):
        self.tiles=defaultdict(list);self.cell=2000
        ground={'context_fallow','context_meadow','context_crop','context_arable','context_track'}
        for mesh in [m for m in context['meshes']if m['material']in ground]+terrain['meshes']:
            for i in range(0,len(mesh['indices']),3):
                tri=[mesh['verticesCm'][j]for j in mesh['indices'][i:i+3]];a,b,c=tri
                denominator=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
                if abs(denominator)<2e-6:continue
                xs=[p[0]for p in tri];ys=[p[1]for p in tri]
                for x in range(math.floor(min(xs)/self.cell),math.floor(max(xs)/self.cell)+1):
                    for y in range(math.floor(min(ys)/self.cell),math.floor(max(ys)/self.cell)+1):self.tiles[x,y].append((tri,mesh['id'],denominator))
    def sample(self,p):
        choices=[]
        for(a,b,c),mid,d in self.tiles[math.floor(p[0]/self.cell),math.floor(p[1]/self.cell)]:
            u=((b[0]-p[0])*(c[1]-p[1])-(b[1]-p[1])*(c[0]-p[0]))/d
            v=((c[0]-p[0])*(a[1]-p[1])-(c[1]-p[1])*(a[0]-p[0]))/d;w=1-u-v
            if min(u,v,w)>=-1e-8:choices.append((a[2]*u+b[2]*v+c[2]*w,mid))
        require(choices,'Grove ecology root has no actual rendered source ground');return max(choices)


def validated_ecology(plan,extension_manifest,source_context,imported_manifest,sceneSha,objSha):
    owner=plan.get('owner');require(owner in (ECOLOGY,UNFLARED),'Grove ecology generator differs')
    meshes,trees,directory=_common(plan,extension_manifest,source_context,imported_manifest,sceneSha,objSha,owner,'grove-ground-ecology',ECOLOGY_IDS)
    if owner==UNFLARED:
        original=read_pin(plan['sourceEcology'])
        require(original['owner']==ECOLOGY and original['regionId']==REGION and
                plan['inputFiles'].get(plan['sourceEcology']['path'])==plan['sourceEcology']['sha256'],
                'Unflared ecology original source pin differs')
        for path,value in original['inputFiles'].items():pinned(path,value)
        original_geometry=read_pin(original['geometryManifest'])
        require(extension_manifest['meshes']==original_geometry['meshes'],'Unflared ecology changed original detail geometry')
        kept=[g for g in original['groups']if meshes[g['meshId']]['ecologyFamily']!='flare']
        removed=[g for g in original['groups']if meshes[g['meshId']]['ecologyFamily']=='flare']
        expected_rows=[r for r in original['ecologyPlacements']if r['ecologyFamily']!='flare']
        require(plan['groups']==kept and Counter(map(digest,plan['ecologyPlacements']))==Counter(map(digest,expected_rows)),
                'Unflared ecology changed non-collar placements')
        require(len(removed)==36 and sum(len(g['instances'])for g in removed)==78 and
                plan['existingTrees']==original['existingTrees'] and plan['ecologyDomainCm']==original['ecologyDomainCm'],
                'Unflared ecology removal/tree/domain scope differs')
        require(plan['audit']['collarRemoval']=={'sourcePlan':plan['sourceEcology'],'removedInstances':78,'removedGroups':36,
            'retainedNonCollarRowsSha256':digest(expected_rows),'retainedNonCollarGroupsSha256':digest(kept),
            'originalTreeTransformsChanged':False,'inheritedNativeActorsHidden':0},'Unflared ecology exact removal proof differs')
    require(plan['existingTrees']==trees and plan['sourceRegion']==next(r for r in source_context['regionalVegetationPolicy']['regions']if r['id']==REGION),
            'Grove ecology original tree roots/region differ')
    require(plan['policy']=={'collision':'none','navigation':False,'windDisplacementCm':0,'existingTreeTransformsPreserved':True,
        'broadGroundPatches':False,'privateGeometryUnchanged':True,'textureSourcePixelsUnchanged':True},'Grove ecology collision/ground policy differs')
    bundle=json.loads((directory/'canopy-ecology-manifest.json').read_text())
    for key in('plan','geometryManifest','materialManifest','geometryProof','glb'):read_path=pinned(bundle[key]['path'],bundle[key]['sha256'])
    require(read_pin(bundle['plan'])==plan and bundle['geometryManifest']==plan['geometryManifest'],'Grove ecology immutable plan proof differs')
    envelopes,_=_measured_library(meshes)
    domain=_Geo(plan['ecologyDomainCm']);region=_Geo({'type':'Polygon','coordinates':[plan['sourceRegion']['polygonCm']+[plan['sourceRegion']['polygonCm'][0]]]})
    terrain=_input_json(plan,'exterior-terrain-20260926-r4/terrain-plan.json');buildings=_input_json(plan,'exterior-buildings-20260926-r2/building-plan.json')
    scene=_input_json(plan,'realism-20260926-r5/geometry/scene.json')
    require(sha(next(p for p in plan['inputFiles']if p.endswith('/geometry/scene.json')))==sceneSha
            and buildings['sourceSceneSha256']==sceneSha,'Grove ecology actual building/scene source differs')
    blocked=_source_constraints(source_context,buildings,scene);ground=_Ground(source_context,terrain)
    tree_lookup={r['id']:r for r in trees};flares=Counter();ids=set();groups=[];flat=[];counts=Counter();grounds=Counter();minimum=math.inf;budgets=[0,0,0]
    for group in plan['groups']:
        key=group['meshId'];require(key in meshes,'Grove ecology mesh family differs');mesh=meshes[key];family=mesh['ecologyFamily']
        require(group['id']not in ids and group['role']==mesh['role']and mesh['role']==('grass'if family=='grass'else'groundcover')
                and group['cullEndCm']==CULLS[family]and group['qualityDetail']is(family!='flare')and group['instances'],
                'Grove ecology HISM render/quality policy differs')
        ids.add(group['id']);native=[]
        for row in group['instances']:
            p,s,yaw=row['positionCm'],row['scale'],row['yawDeg']
            require(finite(p,3)and finite(s,3)and max(s)==min(s)and .2<=s[0]<=1.9
                    and isinstance(yaw,(int,float))and not isinstance(yaw,bool)and math.isfinite(yaw)and -180<=yaw<=180,
                    'Grove ecology uniform placement transform invalid')
            require(group['id']==f'EX_{key}_{math.floor(p[0]/2500)}_{math.floor(p[1]/2500)}'and row['ecologyFamily']==family,
                    'Grove ecology spatial group/family differs')
            radius=envelopes[key]['radius']*s[0];height=mesh['heightCm']*s[0]
            require(radius<85 and abs(radius-row['radiusCm'])<.0002 and abs(height-row['actualHeightCm'])<.0002,
                    'Grove ecology decoded footprint/height differs')
            require(domain.inside(p[:2]),'Grove ecology full footprint escaped pinned domain')
            clearance=domain.clearance(p[:2]);require(clearance>radius+.1
                    and abs(clearance-row['clearanceCm'])<.0002,'Grove ecology full footprint escaped pinned domain')
            require(region.inside(p[:2])and region.clearance(p[:2])>=radius+10 and _circle_in_crowns(p[:2],radius,trees),
                    'Grove ecology full footprint escaped original crown/grove union')
            for mask in blocked:mask.outside_clear(p[:2],radius+75)
            z,mid=ground.sample(p[:2]);evidence=row['renderedGround']
            require(abs(z-evidence['zCm'])<1e-7 and mid==evidence['meshId']
                    and evidence['measuredElevation']is mid.startswith('context_distant_terrain_'), 'Grove ecology source rendered ground differs')
            if family=='flare':
                tree_id=row.get('existingTreeId');require(tree_id in tree_lookup,'Grove ecology flare tree identity differs');old=tree_lookup[tree_id]
                require(p==old['positionCm']and yaw==old['yawDeg']and s==old['scale']and mesh['existingTreeFamily']==old['meshId']
                        and radius<old['radiusCm'],'Grove ecology exact existing basal transform differs');flares[tree_id]+=1
            else:require('existingTreeId'not in row and abs(p[2]-(z+.08))<1e-8,'Grove ecology elevation/root scope differs')
            minimum=min(minimum,clearance-radius);counts[family]+=1;grounds[mid]+=1;flat.append({'meshId':key,**row})
            for level in range(3):budgets[level]+=mesh['lods'][level]['triangles']
            native.append({'positionCm':list(p),'yawDeg':yaw,'scale':list(s)})
        groups.append({k:deepcopy(group[k])for k in('id','meshId','role','cullEndCm','qualityDetail')});groups[-1]['instances']=native
    audit=plan['audit']
    expected_flares={} if owner==UNFLARED else {r['id']:1 for r in trees}
    instances,group_count=(24773,130) if owner==UNFLARED else (24851,166)
    require(Counter(map(digest,flat))==Counter(map(digest,plan['ecologyPlacements']))and dict(flares)==expected_flares,
            'Grove ecology exact placement membership/78 flares differs')
    require(audit['status']=='PASS_STATIC_GEOMETRY_AND_EXCLUSION'and audit['nativeVerified']is False
            and len(flat)==audit['instances']==instances and len(groups)==audit['groups']==group_count
            and dict(counts)==audit['perFamily']and dict(grounds)==audit['groundSources']and budgets==audit['allInstancesTriangleBudgetByLod']
            and budgets[0]<5000000 and abs(minimum-audit['minimumAdditionalWholeFootprintClearanceCm'])<.0002
            and abs(domain.area()/10000-audit['domainAreaM2'])<1e-7 and audit['existingTreesPreserved']==audit['originalTreeCount']==78
            and audit['sourceGroundChanged']is False and audit['providerPixelsChanged']is False,
            'Grove ecology actual inventory/area/budget audit differs')
    return {'groups':groups,'audit':{'status':'verified-source-grove-ecology','masters':17,'lods':51,'instances':instances,'groups':group_count,
        'qualityDetailGroups':sum(g['qualityDetail']for g in groups),'basalGroups':sum(not g['qualityDetail']for g in groups),
        'existingTrees':78,'deletedTrees':0,'hiddenOriginalActors':0,'exactBasalRootYawScalePreserved':True,
        'allDecodedWholeFootprintsInsideOriginalGroveCrownsAndActualSourceExclusions':True,'sourceGroundUnchanged':True,
        'minimumAdditionalWholeFootprintClearanceCm':minimum,'allInstancesTriangleBudgetByLod':budgets,
        'sourceContext':deepcopy(plan['sourceContext']),'geometryProof':deepcopy(bundle['geometryProof']),
        'nativeAppearanceAccepted':False}}
