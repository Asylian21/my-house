"""Bounded technical field-luminance factors from licensed 2024 ortho.

This generates scalar data, not replacement aerial RGB or a native render.
All frozen inputs stay unchanged. Only a new output directory is written.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import shapely
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
ORTHO=ROOT/'output/unreal/exterior-ortho-20260926-r1/orthophoto-manifest.json'
CONTEXT=ROOT/'output/unreal/exterior-context-20260927-r8/context-plan.json'
BUILDINGS=ROOT/'output/unreal/exterior-buildings-20260926-r2/building-plan.json'
RENDER=ROOT/'output/unreal/exterior-20260927-r6/exterior-import-report.json'
OWNER='scripts/unreal/exterior-field-macro-r3.py'
KEYS=('context_meadow','context_fallow','context_crop','context_arable')
SIZE=1024
EXTENT=56000.
PIXEL_CM=EXTENT/SIZE


def map_coordinates(data, coords, order=1, mode='constant', cval=0):
    """Bilinear scalar sampling; explicit zero outside the valid pixel grid."""
    require(order==1 and mode=='constant' and cval==0,'Unsupported sampler')
    yy,xx=coords; xi=np.floor(xx).astype(int);yi=np.floor(yy).astype(int)
    dx=xx-xi;dy=yy-yi
    def fetch(ix,iy):
        valid=(ix>=0)&(iy>=0)&(ix<data.shape[1])&(iy<data.shape[0])
        return np.where(valid,data[np.clip(iy,0,data.shape[0]-1),np.clip(ix,0,data.shape[1]-1)],0)
    result=(fetch(xi,yi)*(1-dx)+fetch(xi+1,yi)*dx)*(1-dy)+(fetch(xi,yi+1)*(1-dx)+fetch(xi+1,yi+1)*dx)*dy
    return np.where((xx>=0)&(xx<=data.shape[1]-1)&(yy>=0)&(yy<=data.shape[0]-1),result,0)


def gaussian_filter(data,sigma,mode='constant',truncate=3):
    """Separable finite Gaussian; NumPy only to keep the pinned runtime usable."""
    require(mode=='constant','Unsupported Gaussian edge policy')
    radius=int(truncate*sigma+.5);x=np.arange(-radius,radius+1,dtype=float)
    kernel=np.exp(-.5*(x/sigma)**2);kernel/=kernel.sum()
    def pass_axis(array,axis):
        padding=[(0,0)]*2;padding[axis]=(radius,radius)
        return np.apply_along_axis(lambda row:np.convolve(row,kernel,mode='valid'),axis,np.pad(array,padding))
    return pass_axis(pass_axis(data,0),1)


def binary_dilation(data,iterations):
    for _ in range(iterations):
        p=np.pad(data,1);data=p[1:-1,1:-1]|p[:-2,1:-1]|p[2:,1:-1]|p[1:-1,:-2]|p[1:-1,2:]
    return data


def conservative_feather_distance(data):
    """Chebyshev distance lower-bounds Euclidean distance, capped beyond feather."""
    distance=np.zeros(data.shape,dtype=float);remaining=data.copy()
    for _ in range(8):
        distance+=remaining
        p=np.pad(remaining,1)
        remaining=np.logical_and.reduce([p[dy:dy+data.shape[0],dx:dx+data.shape[1]] for dy in range(3) for dx in range(3)])
    return distance*PIXEL_CM


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def require(ok,message):
    if not ok:raise ValueError(message)
def smooth(t):
    t=np.clip(t,0.,1.);return t*t*(3-2*t)
def linear(a):return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def srgb(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
def poly_iter(shape):
    if shape.geom_type=='Polygon':yield shape
    elif hasattr(shape,'geoms'):
        for child in shape.geoms:yield from poly_iter(child)


def build(output):
    output=Path(output).resolve();require(not output.exists(),'Use a new macro output')
    ortho,context,buildings,render=map(read,[ORTHO,CONTEXT,BUILDINGS,RENDER])
    layer=next(r for r in ortho['layers'] if r['id']=='detail2km')
    require(ortho['sourceCurrencyYear']==2024 and sha(layer['rgbaPath'])==layer['rgbaSha256'],'Ortho year/hash differs')
    require(context['activeDesign']=={'variant':'C','livingLayout':'B','heatingLayout':'B'},'C/B/B required')
    rgba=np.asarray(Image.open(layer['rgbaPath']),dtype=np.float32)/255
    axis=(np.arange(SIZE,dtype=np.float64)+.5)*PIXEL_CM-EXTENT/2
    x,y=np.meshgrid(axis,-axis)
    u=layer['worldCmToUvRows'][0][0]*x+layer['worldCmToUvRows'][0][1]*y+layer['worldCmToUvRows'][0][2]
    v=layer['worldCmToUvRows'][1][0]*x+layer['worldCmToUvRows'][1][1]*y+layer['worldCmToUvRows'][1][2]
    coords=np.array([v*layer['height']-.5,u*layer['width']-.5])
    sample=np.stack([map_coordinates(rgba[:,:,i],coords,order=1,mode='constant',cval=0) for i in range(4)],axis=-1)
    valid=(u>=0)&(u<=1)&(v>=0)&(v<=1)&(sample[:,:,3]>=.99)
    lum=np.dot(linear(sample[:,:,:3]),[.2126,.7152,.0722])
    loglum=np.log(np.maximum(lum,.0001))
    world=ortho['worldFrame'];site=world['siteAxis']
    nat_to_world=np.linalg.inv(np.array([[site['ux']*.01,-site['vx']*.01],[site['uy']*.01,-site['vy']*.01]]))
    origin=np.array(ortho['worldOriginNationalMetres'])
    def parcel_shape(row):
        out=[]
        for rings in row['polygonsSjtskMm']:
            converted=[[(nat_to_world@(np.asarray(p)/1000-origin)).tolist() for p in ring] for ring in rings]
            out.append(Polygon(converted[0],converted[1:]))
        return unary_union(out)
    subject=unary_union([parcel_shape(p) for p in context['parcels'] if p['parcelNumber']=='6012/26'])
    roads=unary_union([parcel_shape(p) for p in context['parcels'] if p['parcelNumber'] in ('6012/1','6035/1','6013','6019')])
    protected=unary_union([Polygon(tri) for tri in context['protectedTrianglesCm']])
    building_shapes=unary_union([Polygon(rings[0],rings[1:]) for b in buildings['buildings'] for rings in b['polygonsCm']])
    canopy=unary_union([Polygon(r['polygonCm']) for r in context['regionalVegetationPolicy']['regions']])
    excluded=unary_union([subject.buffer(1000),roads.buffer(300),protected.buffer(200),building_shapes.buffer(1000),canopy.buffer(1200)]).buffer(100)
    mesh_by_id={m['id']:m for m in context['meshes']}
    fields=[]
    for surface in context['surfaces']:
        if surface['material'] not in KEYS or surface['finish']!='surface':continue
        mesh=mesh_by_id[surface['meshId']];vertices=np.asarray(mesh['verticesCm']);ids=np.asarray(mesh['indices']).reshape(-1,3)
        pieces=[Polygon(t[:,:2]) for t in vertices[ids] if Polygon(t[:,:2]).area>1e-5]
        legal=unary_union(pieces)
        domain=legal.buffer(-150).difference(excluded).intersection(Point(0,0).buffer(25500,quad_segs=256))
        if domain.area>10000:fields.append({'source':surface,'legal':legal,'domain':domain})
    labels=np.zeros((SIZE,SIZE),dtype=np.uint16)
    preview_labels=np.zeros((SIZE,SIZE),dtype=np.uint16)
    field_records=[]
    band=np.zeros((SIZE,SIZE),dtype=np.float32)
    support=np.zeros((SIZE,SIZE),dtype=np.float32)
    shadow_removed=np.zeros((SIZE,SIZE),dtype=bool)
    for field_index,row in enumerate(fields,1):
        domain=row['domain'];xmin,ymin,xmax,ymax=domain.bounds
        cols=np.flatnonzero((axis>=xmin)&(axis<=xmax));rows=np.flatnonzero((-axis>=ymin)&(-axis<=ymax))
        if not len(rows) or not len(cols):continue
        sl=(slice(rows[0],rows[-1]+1),slice(cols[0],cols[-1]+1))
        inside=shapely.contains_xy(domain,x[sl],y[sl])&valid[sl]
        if inside.sum()<48:continue
        preview_labels[sl]=np.where(inside,field_index,preview_labels[sl])
        local_log=loglum[sl];values=local_log[inside];q=np.quantile(values,[.05,.1,.5,.9,.95]);median=q[2]
        mad=float(np.median(np.abs(values-median)))
        # Deep dark anomalies can be canopy shadows/objects. Exclude, never turn
        # them into dark-painted vegetation. This is conservative, not de-lighting.
        dark=inside&(local_log<min(median-2.5*max(mad,.08),math.log(.045)))
        dark=binary_dilation(dark,iterations=4)&inside
        trusted=inside&~dark
        if trusted.sum()<48:continue
        clipped=np.clip(local_log,q[1],q[3]);weight=trusted.astype(np.float32)
        fine_sigma=90/PIXEL_CM;broad_sigma=2200/PIXEL_CM
        def normalized(sigma):
            den=gaussian_filter(weight,sigma=sigma,mode='constant',truncate=3)
            num=gaussian_filter(clipped*weight,sigma=sigma,mode='constant',truncate=3)
            return np.divide(num,den,out=np.full_like(num,median),where=den>1e-5)
        contrast=normalized(fine_sigma)-normalized(broad_sigma)
        # Smoothly bound log contrast; cannot invent displacement or colour.
        local_band=.85*contrast
        distance=conservative_feather_distance(trusted)
        feather=smooth((distance-PIXEL_CM)/250)*trusted
        radius=np.hypot(x[sl],y[sl]);feather*=1-smooth((radius-21000)/4500)
        band[sl]=np.where(trusted,local_band,band[sl]);support[sl]=np.maximum(support[sl],feather)
        labels[sl]=np.where(trusted,field_index,labels[sl]);shadow_removed[sl]|=dark
        field_records.append({'id':field_index,**row['source'],'domainAreaM2':domain.area/10000,'trustedPixels':int(trusted.sum()),'darkOutlierPixelsRemoved':int(dark.sum()),'sourceLinearLumaQuantiles':np.exp(q).tolist(),'logContrastPercentiles':np.percentile(local_band[trusted],[1,10,50,90,99]).tolist()})
    hard=labels>0
    require(hard.any() and np.all(valid[hard]),'Empty or unsupported factor domain')
    require(not shapely.intersects_xy(excluded,x[hard],y[hard]).any(),'Protected domain entered')
    candidate_settings=[('moderate',[.75,1.10]),('strong',[.65,1.15])]
    output.mkdir(parents=True)
    Image.fromarray(labels).save(output/'field-labels-u16.png')
    Image.fromarray(np.uint8(shadow_removed)*255).save(output/'dark-outlier-exclusion.png')
    recipe_colors={}
    source_maps={}
    for key in KEYS:
        recipe=render['materials']['materials'][key]['recipe']
        colors=[]
        for item in [recipe,recipe['groundCover']]:
            spec=item['maps']['albedo'];source_maps[spec['path']]=spec['sha256']
            raw=np.array(Image.open(spec['path']).convert('RGB').resize((256,256),Image.Resampling.BOX),dtype=float)/255
            colors.append(linear(raw).mean((0,1)))
        cover=sum(recipe['coverRange'])/2
        recipe_colors[key]=((colors[0]*(1-cover)+colors[1]*cover)*np.array(recipe['tint'])*recipe['albedoScale']).tolist()
    proxy=np.full((SIZE,SIZE,3),.065,dtype=float)
    for row in field_records:proxy[preview_labels==row['id']]=recipe_colors[row['material']]
    candidates=[]
    preview_panels=[('2024 source reference / current RGB is NOT applied',np.uint8(np.clip(sample[:,:,:3]*255,0,255))),('CPU flat PBR mean BaseColor / no lighting',np.uint8(np.clip(srgb(proxy)*255,0,255)))]
    for name,bounds in candidate_settings:
        factor=np.clip(np.exp(band),*bounds)
        factor=np.where(hard,factor,1.)
        # Exact neutral byte128. This signed factor encoding is independent of
        # candidate bounds and supports standard mip filtering of R only.
        encoded=np.uint8(np.clip(np.round(128+(factor-1)*255/.70),0,255))
        texture=np.stack([encoded,np.uint8(hard)*255,np.uint8(valid)*255,np.uint8(np.round(support*255))],axis=-1)
        path=output/f'field-macro-{name}.png';Image.fromarray(texture,'RGBA').save(path)
        decoded=1+(texture[:,:,0].astype(float)-128)*.70/255
        applied=1+(np.clip(decoded,*bounds)-1)*(texture[:,:,3]/255)*hard
        applied=np.clip(applied,*bounds)
        stats={'factorPercentiles':np.percentile(applied[hard],[0,1,10,50,90,99,100]).tolist(),'factorStdDev':float(applied[hard].std()),'fractionMoreThan3PercentVariation':float(np.mean(np.abs(applied[hard]-1)>.03)),'weightedMean':float(applied[hard].mean()),'maximumQuantizationError':float(np.max(np.abs(decoded-factor))),'neutralOutsideExact':bool(np.all(applied[~hard]==1))}
        candidate={'name':name,'factorRange':bounds,'texture':{'path':str(path),'sha256':sha(path),'width':SIZE,'height':SIZE,'pixelFormat':'RGBA8','sRGB':False,'addressMode':'clamp'},'statistics':stats}
        candidates.append(candidate)
        preview_panels.append((f'CPU PBR BaseColor x {name} scalar [{bounds[0]:.2f},{bounds[1]:.2f}] / NOT native',np.uint8(np.clip(srgb(proxy*applied[:,:,None])*255,0,255))))
    # Technical four-panel source/data comparison with headings and footnote.
    panel_size=700;canvas=Image.new('RGB',(2*panel_size,2*(panel_size+50)+65),'#f7f6f2');draw=ImageDraw.Draw(canvas)
    font_path='/System/Library/Fonts/Supplemental/Arial.ttf'
    font=ImageFont.truetype(font_path,17);small=ImageFont.truetype(font_path,14)
    for i,(title,pixels) in enumerate(preview_panels):
        px=(i%2)*panel_size;py=(i//2)*(panel_size+50)
        draw.text((px+12,py+12),title,fill='#1f352c',font=font)
        image=Image.fromarray(pixels).resize((panel_size,panel_size),Image.Resampling.LANCZOS)
        canvas.paste(image,(px,py+50))
    draw.text((12,2*(panel_size+50)+8),'TECHNICAL CPU STUDY: no UE lighting, shadows, perspective, normals or acceptance claim. Existing field geometry stays unchanged.',fill='#333333',font=small)
    draw.text((12,2*(panel_size+50)+30),'Source: Ortofoto CR, CUZK 2024, CC BY 4.0. Extracted bounded luminance band; source RGB/alpha files unchanged. Grey = no effect.',fill='#333333',font=small)
    canvas.save(output/'cpu-field-macro-comparison.png')
    inputs={str(p):sha(p) for p in [ORTHO,CONTEXT,BUILDINGS,RENDER,Path(layer['rgbaPath']),Path(__file__)]}
    inputs.update(source_maps)
    manifest={'schemaVersion':1,'owner':OWNER,'status':'CPU_STUDY_NOT_NATIVE_ACCEPTED','sourceCurrencyYear':2024,'license':ortho['license'],'inputFiles':inputs,'sourceSceneSha256':context['sourceSceneSha256'],'sourceObjSha256':context['sourceObjSha256'],'allowedMaterialKeys':list(KEYS),'worldCmToUvRows':[[1/EXTENT,0,.5],[0,-1/EXTENT,.5]],'worldBoundsCm':[-EXTENT/2,-EXTENT/2,EXTENT/2,EXTENT/2],'fieldRadiusCm':25500,'radialFadeCm':[21000,25500],'encoding':{'R':'factor = 1 + (R - 128/255) * 0.70; clamp to candidate factorRange','G':'binary trusted field domain; sample mip0, require >=0.99','B':'provider coverage at derived texel; sample mip0, require >=0.99','A':'smooth field/dark-outlier/radial weight; sample mip0'},'sampling':{'factorMip':'normal derivative-selected mip for R; neutral1 outside','containmentMip':0,'rawUvValidityRequired':True,'hardContainmentThreshold':.99,'addressMode':'clamp','formula':'Valid=(all(UV>=0)&&all(UV<=1))*step(.99,G_mip0)*step(.99,B_mip0); Factor=clamp(1+(R_auto-128/255)*.70,min,max); BaseColorOut=BaseColorIn*lerp(1,Factor,A_mip0*Valid); all other outputs unchanged'},'derivation':{'source':'detail2km official on-line single export, original pixels pinned','luminance':'linear sRGB Rec709 weights','fineGaussianSigmaCm':90,'localIlluminationSigmaCm':2200,'perFieldWinsorQuantiles':[.1,.9],'logContrastGain':.85,'darkAnomalyPolicy':'below min(fieldMedianLog-2.5*max(MAD,.08), log(.045)); dilated4pixels and excluded','fieldInsetCm':150,'excludedRasterFilterGuardCm':100,'fieldFeatherCm':250,'subjectBufferCm':1000,'roadParcelBufferCm':300,'protectedBufferCm':200,'buildingBufferCm':1000,'annotatedCanopyBufferCm':1200,'season':'Illustrative green-season PBR base remains authoritative; source acquisition colour is not used'},'candidates':candidates,'fields':field_records,'summary':{'trustedPixels':int(hard.sum()),'trustedAreaM2':float(hard.sum()*PIXEL_CM**2/10000),'fieldCount':len(field_records),'darkOutlierPixelsRemoved':int(shadow_removed.sum()),'protectedIntersections':0,'unsupportedPixels':0,'domainTextureLabels':{'path':str(output/'field-labels-u16.png'),'sha256':sha(output/'field-labels-u16.png')}},'limitations':['Relative luminance still contains some acquisition appearance; this is not measured reflectance or proven shadow removal.','Field-internal pale tracks can remain as bounded scalar changes; no aerial RGB, normal, height, opacity or collision is imported.','The scalar does not identify tractors, current crops or management conditions.','CPU mean-PBR preview shows only BaseColor modulation, not photorealism or actual native exposure.']}
    write(output/'field-macro-study.json',manifest)
    print(json.dumps({'output':str(output),'summary':manifest['summary'],'candidates':[{k:v for k,v in c.items() if k!='texture'} for c in candidates]},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);args=p.parse_args();build(args.output)
