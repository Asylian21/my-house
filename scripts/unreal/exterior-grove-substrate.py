"""Immutable photographic leaf-litter substrate within the exact old grove.

Offline source study only: original native ground, trees, collision and source
photographs are retained. No native editor or shared pipeline mutation occurs.
"""
import argparse
from datetime import datetime,timezone
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse

import numpy as np
from PIL import Image,ImageDraw,ImageFont
import shapely
from shapely.geometry import Point,Polygon

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OWNER='scripts/unreal/exterior-grove-substrate.py';ASSET='forest_leaves_04';MATERIAL='canopy_floor_litter'
PAGE='https://polyhaven.com/a/'+ASSET;TILE_CM=150.;STEP_CM=12.5;CHUNK_CM=1000.;FEATHER_CM=180.
FADE_CM=[12000.,18000.];MAX_DRAW_CM=18000;HEIGHT_LOW_CM=.12;HEIGHT_AMPLITUDE_CM=.68
ROLES={'albedo':'Diffuse','normal':'nor_gl','roughness':'Rough','displacement':'Displacement'}
INFO_SHA='ac5eea16f64d758bb12f67b68b8c609430c1a544e74f61b30105848cf237e90f'
FILES_SHA='2944bc194c4f8e66a4766a7a36c1e01bd6556d96e09e49104099ecb3b30bb741'
DEFAULT_CONTEXT=ROOT/'output/unreal/exterior-context-20260927-r8/context-plan.json'
DEFAULT_ECOLOGY=ROOT/'output/unreal/exterior-canopy-ecology-20260930-r3/canopy-ecology-plan.json'
DEFAULT_TERRAIN=ROOT/'output/unreal/exterior-terrain-20260926-r4/terrain-plan.json'
DEFAULT_BUILDINGS=ROOT/'output/unreal/exterior-buildings-20260926-r2/building-plan.json'
DEFAULT_SCENE=ROOT/'output/unreal/realism-20260926-r5/geometry/scene.json'


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as stream:
        while block:=stream.read(1024*1024):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())
def pin(path):return{'path':str(Path(path).resolve()),'sha256':sha(path)}
def write(path,value,compact=False):
    with Path(path).open('x')as stream:json.dump(value,stream,ensure_ascii=False,allow_nan=False,indent=None if compact else 2,separators=(',',':')if compact else None);stream.write('\n')


def module(name):
    if str(HERE)not in sys.path:sys.path.insert(0,str(HERE))
    spec=importlib.util.spec_from_file_location(name.replace('-','_'),HERE/(name+'.py'))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def curl(url):
    parsed=urlparse(url)
    require(parsed.scheme=='https'and parsed.hostname in('api.polyhaven.com','dl.polyhaven.org'),'Unexpected official provider source')
    result=subprocess.run(['curl','--fail','--location','--silent','--show-error','--proto','=https','--max-time','120',url],check=True,capture_output=True)
    require(0<len(result.stdout)<=40*1024*1024,'Provider response size outside bounded source scope')
    return result.stdout


def acquire(output):
    output=Path(output).resolve();require(output.is_relative_to(ROOT/'output/unreal')and not output.exists(),'Use fresh immutable acquisition directory')
    info_bytes=curl('https://api.polyhaven.com/info/'+ASSET);files_bytes=curl('https://api.polyhaven.com/files/'+ASSET)
    info,files=json.loads(info_bytes),json.loads(files_bytes)
    require(info['name']=='Forest Leaves 04'and info['authors']=={'Rob Tuytel':'All'}and all(abs(v-1500)<.001 for v in info['dimensions']),
            'Provider authors/physical source tile differs')
    output.mkdir(parents=True);(output/'info.json').write_bytes(info_bytes);(output/'files.json').write_bytes(files_bytes)
    maps={}
    for role,provider_role in ROLES.items():
        entry=files[provider_role]['2k']['png'];url=entry['url'];parsed=urlparse(url)
        require(parsed.hostname=='dl.polyhaven.org'and parsed.path.startswith('/file/ph-assets/Textures/png/2k/'+ASSET+'/')
                and 0<entry['size']<=40*1024*1024 and len(entry['md5'])==32,'Unexpected2K provider map metadata')
        payload=curl(url)
        require(len(payload)==entry['size']and hashlib.md5(payload).hexdigest()==entry['md5'],'Official provider byte count/MD5 differs: '+role)
        path=output/Path(parsed.path).name;path.write_bytes(payload)
        with Image.open(path)as image:require(image.size==(2048,2048),'Official map source dimensions differ')
        maps[role]={**pin(path),'url':url,'bytes':len(payload),'md5':entry['md5'],'width':2048,'height':2048,
            'providerRole':provider_role,'format':'png','resolution':'2k','sourcePixelsUnmodified':True,
            'usage':'Offline geometry only; no native texture import'if role=='displacement'else'Native original photographic PBR map'}
        print(json.dumps({'acquired':role,'bytes':len(payload),'sha256':maps[role]['sha256']}),flush=True)
    receipt={'schemaVersion':1,'owner':OWNER,'status':'PASS_ORIGINAL_PROVIDER_BYTES_NOT_NATIVE_ACCEPTED','assetId':ASSET,
        'license':'CC0-1.0','sourceUrl':PAGE,'author':'Rob Tuytel','physicalTileCm':TILE_CM,
        'acquiredAt':datetime.now(timezone.utc).isoformat(),'infoApi':{'url':'https://api.polyhaven.com/info/'+ASSET,**pin(output/'info.json')},
        'filesApi':{'url':'https://api.polyhaven.com/files/'+ASSET,**pin(output/'files.json')},'maps':maps,
        'sourcePixelsUnmodified':True,'scanAndSpeciesClaim':'Photographic provider surface, artistic site interpretation; exact site ecology/terrain/phenology not surveyed.'}
    write(output/'acquisition-receipt.json',receipt);return receipt


def feather_width(xy):
    xy=np.asarray(xy,dtype=float)
    return FEATHER_CM+22*np.sin(xy[:,0]/127+xy[:,1]/211)+13*np.sin(xy[:,0]/43-xy[:,1]/73+1.7)


def verified_acquisition(assets):
    assets=Path(assets).resolve();receipt=read(assets/'acquisition-receipt.json')
    require(receipt['schemaVersion']==1 and receipt['owner']==OWNER and receipt['assetId']==ASSET and
            receipt['status']=='PASS_ORIGINAL_PROVIDER_BYTES_NOT_NATIVE_ACCEPTED'and receipt['physicalTileCm']==TILE_CM and
            receipt['license']=='CC0-1.0'and receipt['sourceUrl']==PAGE and receipt['author']=='Rob Tuytel'and
            receipt['sourcePixelsUnmodified']is True,'Unreviewed photographic substrate acquisition')
    for key,filename,expected in(('infoApi','info.json',INFO_SHA),('filesApi','files.json',FILES_SHA)):
        require(receipt[key]=={'url':'https://api.polyhaven.com/'+('info'if key=='infoApi'else'files')+'/'+ASSET,**pin(assets/filename)}and
                receipt[key]['sha256']==expected,'Official provider API cache pin differs')
    info,files=read(assets/'info.json'),read(assets/'files.json')
    require(info['name']=='Forest Leaves 04'and info['authors']=={'Rob Tuytel':'All'}and
            all(abs(v-1500)<.001 for v in info['dimensions']),'Official provider physical scale/authorship differs')
    require(set(receipt['maps'])==set(ROLES),'Photographic source map roles differ')
    for role,provider_role in ROLES.items():
        mapping=receipt['maps'][role];entry=files[provider_role]['2k']['png'];actual=Path(mapping['path']).resolve()
        require(actual.parent==assets and actual.name==Path(urlparse(entry['url']).path).name and
                mapping['url']==entry['url']and mapping['bytes']==entry['size']==actual.stat().st_size and
                mapping['md5']==entry['md5']==hashlib.md5(actual.read_bytes()).hexdigest()and mapping['sha256']==sha(actual)and
                mapping['providerRole']==provider_role and mapping['format']=='png'and mapping['resolution']=='2k'and
                mapping['sourcePixelsUnmodified']is True,'Original provider source identity differs: '+role)
        with Image.open(actual)as image:
            require(image.format=='PNG'and image.size==(mapping['width'],mapping['height'])==(2048,2048),'Original map pixel format/dimensions differ')
    return receipt


def coverage(xy,domain):
    distances=shapely.distance(shapely.points(np.asarray(xy)),domain.boundary)
    t=np.clip(distances/feather_width(xy),0,1)
    return t*t*(3-2*t)


def height_image(path):
    with Image.open(path)as image:
        require(image.size==(2048,2048),'Grove displacement source dimensions differ')
        array=np.asarray(image,dtype=float)
    if array.ndim==3:array=array[:,:,0]
    require(array.ndim==2 and np.isfinite(array).all()and np.ptp(array)>0,'Invalid original displacement data')
    # Temporary numerical low-pass only; original PNG bytes are never rewritten.
    # PIL GaussianBlur does not support F; use separable repeated box averaging
    # in float64 with wrapped periodic edges, avoiding conversion/quantisation.
    radius=16;filtered=array.copy()
    for axis in(0,1):
        filtered=sum(np.roll(filtered,k,axis=axis)for k in range(-radius,radius+1))/(2*radius+1)
    lo,hi=np.percentile(filtered,[1,99])
    return np.clip((filtered-lo)/max(hi-lo,1e-12),0,1)


def sample_height(xy,image):
    uv=np.mod(np.asarray(xy,dtype=float)/TILE_CM,1)*image.shape[0]-.5
    base=np.floor(uv).astype(np.int64);fraction=uv-base;size=image.shape[0]
    x,y=base[:,0]%size,base[:,1]%size;fx,fy=fraction[:,0],fraction[:,1]
    return(image[y,x]*(1-fx)*(1-fy)+image[y,(x+1)%size]*fx*(1-fy)+
           image[(y+1)%size,x]*(1-fx)*fy+image[(y+1)%size,(x+1)%size]*fx*fy)


def source(context_path,ecology_path,terrain_path,buildings_path,scene_path):
    context,ecology,terrain,buildings,scene=map(read,(context_path,ecology_path,terrain_path,buildings_path,scene_path))
    require(ecology['owner']=='scripts/unreal/exterior-canopy-ecology.py'and ecology['sourceContext']==pin(context_path),
            'Exact source ecology/context pin differs')
    require(ecology['sourceSceneSha256']==sha(scene_path)==context['sourceSceneSha256']and
            ecology['sourceObjSha256']==sha(Path(scene_path).parent/'dom-mm.obj')==context['sourceObjSha256'],'Grove source scene/OBJ frame differs')
    require(context['activeDesign']==ecology['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}and
            context['housePlacement']==ecology['housePlacement']and
            context['housePlacement']['streetSetbackMm']==context['housePlacement']['eastSetbackMm']==3000,'Grove C/B/B or setbacks differ')
    for path,value in ecology['inputFiles'].items():require(sha(path)==value,'Frozen ecology input drift: '+path)
    base=module('exterior-canopy-ecology');trees,region,grove,crowns,blocked,domain,sampler=base.domains(context,terrain,buildings,scene)
    require(trees==ecology['existingTrees']and region==ecology['sourceRegion']and
            shapely.equals_exact(domain,shapely.from_geojson(ecology['ecologyDomainCm']),1e-7),'Grove exact original crown/domain differs')
    return context,ecology,trees,region,domain,sampler


def mesh_records(domain,sampler,height):
    minx,miny,maxx,maxy=domain.bounds;records=[]
    for ix in range(math.floor(minx/CHUNK_CM),math.floor(maxx/CHUNK_CM)+1):
      for iy in range(math.floor(miny/CHUNK_CM),math.floor(maxy/CHUNK_CM)+1):
        tile=domain.intersection(shapely.box(ix*CHUNK_CM,iy*CHUNK_CM,(ix+1)*CHUNK_CM,(iy+1)*CHUNK_CM))
        if tile.is_empty or tile.area<1:continue
        xx=np.arange(ix*CHUNK_CM,(ix+1)*CHUNK_CM,STEP_CM);yy=np.arange(iy*CHUNK_CM,(iy+1)*CHUNK_CM,STEP_CM)
        xy=np.stack(np.meshgrid(xx,yy,indexing='ij'),axis=-1).reshape(-1,2)
        boxes=shapely.box(xy[:,0],xy[:,1],xy[:,0]+STEP_CM,xy[:,1]+STEP_CM)
        inside=shapely.covers(tile,boxes);intersects=shapely.intersects(tile,boxes)
        triangles=[]
        for(x,y)in xy[inside]:triangles.extend([[[x,y],[x,y+STEP_CM],[x+STEP_CM,y]],[[x+STEP_CM,y],[x,y+STEP_CM],[x+STEP_CM,y+STEP_CM]]])
        clipped=shapely.intersection(boxes[intersects&~inside],tile)
        def polygon_members(value):
            if value.geom_type=='Polygon':yield value
            elif hasattr(value,'geoms'):
                for member in value.geoms:yield from polygon_members(member)
        for item in clipped:
            for polygon in polygon_members(item):
                if polygon.area<1e-8:continue
                for triangle in shapely.constrained_delaunay_triangles(polygon).geoms:
                    p=np.asarray(triangle.exterior.coords[:-1]);ab,ac=p[1]-p[0],p[2]-p[0];area=ab[0]*ac[1]-ab[1]*ac[0]
                    if abs(area)<1e-7:continue
                    if area>0:p=p[[0,2,1]]
                    triangles.append(p.tolist())
        lookup={};points=[];indices=[]
        for triangle in triangles:
            face=[]
            for point in triangle:
                # Welding shares every grid edge and source ring intersection.
                key=tuple(round(float(v),8)for v in point)
                if key not in lookup:lookup[key]=len(points);points.append(list(key))
                face.append(lookup[key])
            if len(set(face))==3:indices.extend(face)
        xy=np.asarray(points);alpha=coverage(xy,domain);offset=HEIGHT_LOW_CM+HEIGHT_AMPLITUDE_CM*sample_height(xy,height)*alpha
        source_z=[];ground_counts={}
        for point in points:
            z,mid=sampler.sample(point)
            require(mid=='context_unresolved_flat_backdrop'and abs(z+25)<1e-7,'Substrate crossed non-fallback retained source ground: '+mid)
            source_z.append(z);ground_counts[mid]=ground_counts.get(mid,0)+1
        vertices=np.column_stack((xy,np.asarray(source_z)+offset));faces=np.asarray(indices,dtype=int).reshape(-1,3)
        a,b,c=vertices[faces[:,0]],vertices[faces[:,1]],vertices[faces[:,2]]
        face_normals=np.cross(c-a,b-a);require(np.all(face_normals[:,2]>1e-7),'Substrate winding/degenerate geometry differs')
        normals=np.zeros_like(vertices)
        for column in range(3):np.add.at(normals,faces[:,column],face_normals)
        normals/=np.linalg.norm(normals,axis=1)[:,None]
        record={'id':f'context_grove_substrate_{ix}_{iy}','material':MATERIAL,'verticesCm':vertices.tolist(),
            'normals':normals.tolist(),'uvs':np.column_stack((alpha,np.zeros_like(alpha))).tolist(),'indices':indices,
            'bounds':{'min':vertices.min(axis=0).tolist(),'max':vertices.max(axis=0).tolist()},'winding':'clockwise',
            'nanite':False,'collision':'NoCollision','castShadow':False,'maxDrawDistanceCm':MAX_DRAW_CM,
            'sourceGround':{'id':'context_unresolved_flat_backdrop','zCm':-25.,'measuredElevation':False},
            'microreliefRangeCm':[float(offset.min()),float(offset.max())]}
        records.append(record)
        print(json.dumps({'mesh':record['id'],'vertices':len(points),'triangles':len(indices)//3}),flush=True)
    require(records,'Empty grove substrate geometry');return records


def build(context_path,ecology_path,terrain_path,buildings_path,scene_path,assets,output):
    paths=list(map(lambda p:Path(p).resolve(),(context_path,ecology_path,terrain_path,buildings_path,scene_path,assets,output)))
    context_path,ecology_path,terrain_path,buildings_path,scene_path,assets,output=paths
    require(output.is_relative_to(ROOT/'output/unreal')and not output.exists(),'Use fresh immutable substrate output')
    context,ecology,trees,region,domain,sampler=source(context_path,ecology_path,terrain_path,buildings_path,scene_path)
    receipt=verified_acquisition(assets)
    height=height_image(receipt['maps']['displacement']['path']);meshes=mesh_records(domain,sampler,height)
    vertices=np.asarray([p for mesh in meshes for p in mesh['verticesCm']]);alphas=np.asarray([p[0]for mesh in meshes for p in mesh['uvs']])
    area=sum(abs(sum(a[0]*b[1]-b[0]*a[1]for a,b in zip([mesh['verticesCm'][i]for i in mesh['indices'][j:j+3]],
        [mesh['verticesCm'][i]for i in mesh['indices'][j+1:j+3]+mesh['indices'][j:j+1]])))*.5
        for mesh in meshes for j in range(0,len(mesh['indices']),3))
    require(abs(area-domain.area)<.01,'Actual continuous substrate triangle area differs from exact domain')
    inputs={str(p):sha(p)for p in[HERE/'exterior-grove-substrate.py',HERE/'exterior-canopy-ecology.py',
        HERE/'exterior-regional-vegetation.py',HERE/'exterior-context.py',HERE/'rural-import.py',HERE/'performance_scene_policy.py',
        context_path,ecology_path,terrain_path,buildings_path,scene_path,scene_path.parent/'dom-mm.obj',assets/'acquisition-receipt.json',
        assets/'info.json',assets/'files.json',*[Path(m['path'])for m in receipt['maps'].values()]]}
    common={'schemaVersion':1,'owner':OWNER,'generatorSha256':sha(__file__),'inputFiles':inputs,
        'activeDesign':deepcopy(context['activeDesign']),'housePlacement':deepcopy(context['housePlacement']),
        'sourceSceneSha256':context['sourceSceneSha256'],'sourceObjSha256':context['sourceObjSha256'],
        'sourceContext':pin(context_path),'sourceEcology':pin(ecology_path),'sourceTerrain':pin(terrain_path),
        'sourceBuildings':pin(buildings_path),'sourceScene':pin(scene_path),'acquisitionManifest':pin(assets/'acquisition-receipt.json')}
    recipe={'kind':'ground','maps':{k:{'path':receipt['maps'][k]['path'],'sha256':receipt['maps'][k]['sha256']}for k in('albedo','normal','roughness')},
        'license':'CC0-1.0','sourceUrl':PAGE,'normalConvention':'OpenGL','tileCm':TILE_CM,'yawDegrees':0.,'stochasticGround':False,
        'tint':[.94,.96,1.],'normalStrength':.85,'macroStrength':.035,'albedoScale':.86,'cropRows':False,
        'featherUV':True,'opacityMaskClipValue':.333,'distanceFadeCm':FADE_CM,
        'artDirection':'Continuous original photographic autumn forest litter, physically scaled1.5m and registered provider-derived actual microrelief. Artistic site interpretation, not measured native terrain.'}
    policy={'collision':'none','navigation':False,'windDisplacementCm':0,'sourceGroundUnchanged':True,'originalTreesUnchanged':True,
        'protectedArchitectureUnchanged':True,'sourcePixelsUnmodified':True,'exactOriginalEcologyDomain':True,
        'physicalTileCm':TILE_CM,'meshStepCm':STEP_CM,'featherCm':FEATHER_CM,'featherWidthRangeCm':[145.,215.],
        'featherWidthFormula':'180+22*sin(x/127+y/211)+13*sin(x/43-y/73+1.7), native world cm',
        'coverageFormula':'smoothstep(0,1,clamp(distance(exactDomainBoundary)/featherWidth,0,1)) in UV0.x;UV0.y=0',
        'fullInteriorOpacity':1.,'distanceFadeCm':FADE_CM,'maxDrawDistanceCm':MAX_DRAW_CM,
        'sourceGroundEvidence':'Existing context_unresolved_flat_backdrop at−25cm, explicitly not measured elevation',
        'microreliefMinCm':HEIGHT_LOW_CM,'microreliefMaxCm':HEIGHT_LOW_CM+HEIGHT_AMPLITUDE_CM,
        'microreliefSource':'Original provider Displacement2K PNG, temporary separable33pixel periodic float box low-pass,1/99 percentile normalization; actual worldXY/150cm bilinear sampling.',
        'microreliefPhotoUvRegistered':True,'stochasticGround':False,'nativeAcceptanceRequired':True}
    audit={'status':'PASS_STATIC_CONTINUOUS_PHOTOGRAPHIC_SUBSTRATE_NATIVE_PENDING','nativeVerified':False,
        'meshes':len(meshes),'vertices':len(vertices),'triangles':sum(len(m['indices'])//3 for m in meshes),
        'domainAreaM2':domain.area/10000,'actualTriangleAreaM2':area/10000,'originalTrees':len(trees),
        'sourceGroundChanged':False,'sourcePixelsChanged':False,'coreAlphaOneVertices':int((alphas>=1-1e-12).sum()),
        'outerAlphaZeroVertices':int((alphas<=1e-8).sum()),'microreliefRangeCm':[float(vertices[:,2].min()+25),float(vertices[:,2].max()+25)],
        'alphaRange':[float(alphas.min()),float(alphas.max())]}
    output.mkdir(parents=True);write(output/'material-manifest.json',{MATERIAL:recipe})
    write(output/'geometry-manifest.json',{'schema':1,**common,'units':'metres','meshes':[],
        'status':'STATIC_CONTEXT_MESH_RECORDS_IN_PLAN_NOT_PLANT_MASTER_LIBRARY','revision':'Photographic grove litter1'})
    write(output/'asset-manifest.json',{'schema':1,**common,'sources':[{'kind':'photographic-PBR','assetId':ASSET,'license':'CC0-1.0','sourceUrl':PAGE,
        'sourcePixelsUnmodified':True}],'scope':'One licensed new ground recipe; static context meshes remain in the pinned plan; zero old asset/material edits.'})
    plan={'kind':'grove-continuous-photographic-substrate',**common,'inputFiles':{**inputs,str(output/'material-manifest.json'):sha(output/'material-manifest.json')},'regionId':region['id'],'sourceRegion':region,
        'trees':deepcopy(trees),'domainCm':shapely.to_geojson(domain),'meshes':meshes,'policy':policy,'audit':audit,
        'materialManifest':pin(output/'material-manifest.json')}
    write(output/'grove-substrate-plan.json',plan,compact=True)
    write(output/'grove-substrate-audit.json',audit)
    module('rural-import').write_glb(output/'grove-substrate-preview.glb',plan)
    manifest={**common,'status':audit['status'],'plan':pin(output/'grove-substrate-plan.json'),'materialManifest':plan['materialManifest'],
        'geometryManifest':pin(output/'geometry-manifest.json'),'previewGeometry':pin(output/'grove-substrate-preview.glb'),
        'audit':audit,'nativeAcceptance':False}
    write(output/'grove-substrate-manifest.json',manifest)
    preview(plan,receipt,output)
    return audit


def preview(plan,receipt,output):
    # Numerical source preview at the actual R7 floor-root area, not a native
    # screenshot or synthetic photoreal render. Original maps remain immutable.
    tree=next(r for r in plan['trees']if r['id']=='village_nearest_grove_3');center=np.asarray(tree['positionCm'][:2])
    axis=np.linspace(-300,300,900);x,y=np.meshgrid(axis+center[0],axis+center[1]);xy=np.column_stack((x.ravel(),y.ravel()))
    with Image.open(receipt['maps']['albedo']['path'])as image:photo=np.asarray(image.convert('RGB'))/255
    uv=np.mod(xy/TILE_CM,1);px=(uv[:,0]*2048).astype(int);py=(uv[:,1]*2048).astype(int)
    color=photo[py,px];domain=shapely.from_geojson(plan['domainCm']);alpha=coverage(xy,domain)
    inside=shapely.contains_xy(domain,xy[:,0],xy[:,1]);alpha*=inside
    background=np.tile(np.array([.43,.47,.29]),(len(xy),1));colors=color*alpha[:,None]+background*(1-alpha[:,None])
    height=sample_height(xy,height_image(receipt['maps']['displacement']['path']))*HEIGHT_AMPLITUDE_CM*alpha+HEIGHT_LOW_CM
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',23)
    small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',19)
    canvas=Image.new('RGB',(2400,950),'#f0f0e8');draw=ImageDraw.Draw(canvas)
    draw.text((25,20),'OFFLINE SOURCE STUDY: native lighting, material readback and visual acceptance pending',font=font,fill='#161915')
    labels=['Original source RGB: physical1.5m tile,6m square','Registered actual mesh height0.12–0.80cm','Boundary coverage: opaque interior, soft edge']
    panels=[colors.reshape(900,900,3),np.repeat(((height-HEIGHT_LOW_CM)/HEIGHT_AMPLITUDE_CM).reshape(900,900,1),3,axis=2),np.repeat(alpha.reshape(900,900,1),3,axis=2)]
    for i,(label,panel)in enumerate(zip(labels,panels)):
        image=Image.fromarray(np.uint8(np.clip(panel[::-1],0,1)*255)).resize((760,760),Image.Resampling.LANCZOS)
        canvas.paste(image,(20+i*800,95));draw.text((20+i*800,62),label,font=small,fill='#161915')
        draw.text((20+i*800,865),'World XY +/-3m around preserved grove tree_3',font=small,fill='#161915')
    draw.text((25,910),'Source elevation -25cm is an unmeasured retained backdrop. Photograph bytes and original ground stay unchanged.',font=small,fill='#161915')
    canvas.save(output/'grove-substrate-source-preview.png')
    contact=Image.new('RGB',(1600,520),'#f0f0e8');draw=ImageDraw.Draw(contact)
    for i,role in enumerate(ROLES):
        with Image.open(receipt['maps'][role]['path'])as image:
            if role in('roughness','displacement'):
                data=np.asarray(image);require(data.ndim==2,'Provider scalar preview format differs')
                # Display the declared 16-bit PNG sample range, without a
                # contrast stretch or any mutation of the original map.
                panel=Image.fromarray(np.uint8(data.astype(float)/65535*255)).convert('RGB')
            else:panel=image.convert('RGB')
            panel=panel.resize((380,380),Image.Resampling.LANCZOS)
        contact.paste(panel,(10+i*400,65));draw.text((10+i*400,30),role+' original2K PNG',font=small,fill='#161915')
    draw.text((15,475),'Official CC0 Poly Haven forest_leaves_04; originals unedited. Displacement is offline geometry only.',font=small,fill='#161915')
    contact.save(output/'grove-substrate-original-maps-preview.png')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--acquire');p.add_argument('--assets');p.add_argument('--output')
    p.add_argument('--context',default=str(DEFAULT_CONTEXT));p.add_argument('--ecology',default=str(DEFAULT_ECOLOGY))
    p.add_argument('--terrain',default=str(DEFAULT_TERRAIN));p.add_argument('--buildings',default=str(DEFAULT_BUILDINGS));p.add_argument('--scene',default=str(DEFAULT_SCENE))
    a=p.parse_args()
    if a.acquire:print(json.dumps(acquire(a.acquire)))
    else:
        require(a.assets and a.output,'Specify --assets and fresh --output')
        print(json.dumps(build(a.context,a.ecology,a.terrain,a.buildings,a.scene,a.assets,a.output)))
