"""Protection-only permission for geographic aerial RGB on context ground.

The mask excludes the authored subject site and official building footprints.
It never excludes roads, canopies, dark image pixels or cadastral field edges.
Original provider coverage is sampled separately by the material at mip zero.
All inputs and historical outputs are immutable; this writes a fresh revision.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image
import shapely
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-ortho-projection-mask.py'
SIZE=1024
KEYS=('context_meadow','context_fallow','context_crop','context_arable','context_track')


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def encode(value):return (json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def smooth(value):
    t=np.clip(value,0.,1.);return t*t*(3-2*t)


def source_module(filename,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def sample(image,world_points,rows):
    """GPU-like bilinear sampling using pixel-centre UV, with explicit extent."""
    xy=np.asarray(world_points,dtype=float)
    u=xy[:,0]*rows[0][0]+xy[:,1]*rows[0][1]+rows[0][2]
    v=xy[:,0]*rows[1][0]+xy[:,1]*rows[1][1]+rows[1][2]
    px=u*image.shape[1]-.5;py=v*image.shape[0]-.5
    x0=np.floor(px).astype(int);y0=np.floor(py).astype(int)
    fx=px-x0;fy=py-y0
    def fetch(x,y):return image[np.clip(y,0,image.shape[0]-1),np.clip(x,0,image.shape[1]-1)]
    weights=[(1-fx)*(1-fy),fx*(1-fy),(1-fx)*fy,fx*fy]
    values=sum(fetch(x,y)*w.reshape((-1,)+(1,)*(image.ndim-2))
               for (x,y),w in zip([(x0,y0),(x0+1,y0),(x0,y0+1),(x0+1,y0+1)],weights))
    inside=(u>=0)&(u<=1)&(v>=0)&(v<=1)
    return values,inside


def full_authored_site(subject,scene,obj_path):
    """Exact source face projections outside the already protected legal plot.

    Public roads/verges, landscape background and public/service context do not
    belong to the private authored site. Private entrance surfaces remain safe.
    Most house/garden faces are already inside the parcel, so only actual extra
    XY pieces need unioning; object bounding boxes are not used as protection.
    """
    groups={'Walls','Windows','Roof','Pool','Fence','Decking','Floors','Foundations','Interior','Landscape'}
    public={'DOM_%05d'%i for i in [0,*range(2,54),*range(2022,2028),2039]}
    selected={row['id']for row in scene['objects'] if row['id']not in public and
              (row['group']in groups or row['id']in {'DOM_%05d'%i for i in range(54,60)})}
    # Skip reading private objects whose complete XY bounds are already inside
    # the legal parcel. Other objects use their actual projected source faces.
    wanted=set()
    for row in scene['objects']:
        if row['id']not in selected:continue
        low,high=row['boundsMm']['min'],row['boundsMm']['max']
        rectangle=Polygon([(low[0]/10,-low[1]/10),(high[0]/10,-low[1]/10),
                           (high[0]/10,-high[1]/10),(low[0]/10,-high[1]/10)])
        if not subject.covers(rectangle):wanted.add(row['id'])
    vertices,extras,current=[],[],None
    for line in obj_path.open():
        p=line.split()
        if not p:continue
        if p[0]=='v':vertices.append([float(p[1])/10,-float(p[2])/10])
        elif p[0]=='o':current=p[1]
        elif p[0]=='f' and current in wanted:
            face=[vertices[int(k.split('/')[0])-1]for k in p[1:]]
            for i in range(1,len(face)-1):
                poly=Polygon([face[0],face[i],face[i+1]])
                if poly.area>1e-6 and not subject.covers(poly):extras.append(poly)
    return unary_union([subject,*extras]),{'authoredSourceObjectCount':len(selected),
          'objectsRequiringExactOutsideFaceReview':len(wanted),'outsideSourceFaceCount':len(extras),
          'outsideSourceGeometryAreaM2':unary_union(extras).difference(subject).area/10000 if extras else 0.,
          'excludedPublicObjectIds':sorted(public),'allPrivateGeometryXYProtected':True}


def build(context_path,buildings_path,scene_path,ortho_path,output):
    context,buildings,scene,ortho=map(read,(context_path,buildings_path,scene_path,ortho_path))
    require(context['sourceSceneSha256']==buildings['sourceSceneSha256']==sha(scene_path),'Projection scene frame differs')
    require(context['sourceObjSha256']==buildings['sourceObjSha256'],'Projection OBJ frame differs')
    obj_path=scene_path.parent/'dom-mm.obj'
    require(sha(obj_path)==context['sourceObjSha256'],'Projection source OBJ differs')
    require(context['activeDesign']==scene['activeDesign']==buildings['activeDesign']==
            {'variant':'C','livingLayout':'B','heatingLayout':'B'},'C/B/B required')
    require(scene['housePlacement']==context['housePlacement']==buildings['housePlacement'],'Projection house placement differs')
    require(scene['housePlacement']['streetSetbackMm']==scene['housePlacement']['eastSetbackMm']==3000,'Setbacks differ')
    require(ortho['worldFrame']['housePlacement']==context['housePlacement'],'Ortho house placement differs')
    require(ortho['inputFiles'].get(str(scene_path))==sha(scene_path),'Ortho scene pin differs')
    layer=next(row for row in ortho['layers']if row['id']=='detail2km')
    require(sha(layer['rgbaPath'])==layer['rgbaSha256'],'Provider ortho changed')
    convert=source_module('exterior-context.py','projection_context_frame')
    subject=unary_union([Polygon([convert.to_unreal(p,scene)for p in rings[0]],
                                 [[convert.to_unreal(p,scene)for p in hole]for hole in rings[1:]])
                         for parcel in context['parcels']if parcel['parcelNumber']=='6012/26'
                         for rings in parcel['polygonsSjtskMm']])
    require(subject.is_valid and subject.area>10000,'Subject legal parcel missing')
    private_site,site_audit=full_authored_site(subject,scene,obj_path)
    building_xy=unary_union([Polygon(rings[0],rings[1:])for row in buildings['buildings']for rings in row['polygonsCm']])
    building_buffer_cm=150.
    protected=unary_union([private_site,building_xy.buffer(building_buffer_cm)])
    ground=[m for m in context['meshes']if m['material']in KEYS]
    vertices=np.asarray([p for m in ground for p in m['verticesCm']],dtype=float)
    low,high=vertices[:,:2].min(axis=0),vertices[:,:2].max(axis=0)
    half=max(50000.,math.ceil(float(np.max(np.abs(vertices[:,:2]))+1000)/1000)*1000)
    extent=2*half;pixel_cm=extent/SIZE
    # Covers every four-sample bilinear footprint at mip zero, so original site
    # vertices never receive aerial RGB through an under-resolved mask edge.
    raster_guard_cm=math.sqrt(2)*pixel_cm
    guarded=protected.buffer(raster_guard_cm)
    feather_cm=300.
    xs=(np.arange(SIZE)+.5)*pixel_cm-half
    ys=half-(np.arange(SIZE)+.5)*pixel_cm
    x,y=np.meshgrid(xs,ys);points=shapely.points(x.ravel(),y.ravel())
    distance=shapely.distance(guarded,points).reshape((SIZE,SIZE))
    permission=np.rint(smooth(distance/feather_cm)*255).astype(np.uint8)
    rgba=np.zeros((SIZE,SIZE,4),dtype=np.uint8);rgba[:,:,0]=permission;rgba[:,:,1]=255;rgba[:,:,3]=255
    rows=[[1/extent,0.,.5],[0.,-1/extent,.5]]
    centroids=np.asarray([np.asarray(m['verticesCm'])[np.asarray(m['indices']).reshape(-1,3),:2].mean(axis=1)
                          for m in ground],dtype=object)
    centroids=np.concatenate(list(centroids)).astype(float)
    sampled,inside=sample(permission/255.,centroids,rows)
    centre_distance=shapely.distance(protected,shapely.points(centroids))
    safe=centre_distance>raster_guard_cm+feather_cm+math.sqrt(2)*pixel_cm
    require(inside.all() and np.all(sampled[safe]>=1-1e-9),'Ordinary context ground centroid lacks projection permission')
    # Native main-site sample guards include actual legal vertices and a dense
    # private-site representative grid; bilinear samples must remain exactly0.
    primary=np.asarray([list(p)for polygon in ([private_site]if private_site.geom_type=='Polygon'else private_site.geoms)
                         for p in polygon.exterior.coords],dtype=float)
    primary_permission,primary_inside=sample(permission/255.,primary,rows)
    require(primary_inside.all() and np.max(primary_permission)<1e-9,'Bilinear projection leaks into authored subject site')
    # Dark, road and canopy positions receive the same geometric permission.
    # A source luminance witness proves that image darkness was never a gate.
    ground_shapes=unary_union([Polygon([m['verticesCm'][j][:2]for j in m['indices'][i:i+3]])
                              for m in ground for i in range(0,len(m['indices']),3)])
    ordinary=shapely.covers(ground_shapes,points)&(distance.ravel()>feather_cm+math.sqrt(2)*pixel_cm)
    rgba_source=np.asarray(Image.open(layer['rgbaPath']),dtype=float)/255.
    sampled_ortho,in_ortho=sample(rgba_source,np.column_stack((x.ravel(),y.ravel())),layer['worldCmToUvRows'])
    rgb=sampled_ortho[:,:3];linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    lum=linear@np.array([.2126,.7152,.0722])
    dark=ordinary&in_ortho&(sampled_ortho[:,3]>.99)&(lum<.045)
    require(dark.any() and np.all(permission.ravel()[dark]==255),'Dark ordinary context was wrongly excluded')
    image_path=output/'protection-mask.png'
    output.mkdir(parents=True,exist_ok=True)
    require(not image_path.exists(),'Protection mask output is immutable')
    Image.fromarray(rgba).save(image_path)
    mask={'path':str(image_path),'sha256':sha(image_path),'width':SIZE,'height':SIZE,'pixelFormat':'RGBA8',
          'sRGB':False,'lossless':True,'worldCmToUvRows':rows,'worldBoundsCm':[-half,-half,half,half],
          'channels':{'R':'Smooth RGB projection permission;0=protected;1=ordinary context',
                      'G':'Mask geographic extent coverage1; explicit UV-bounds guard required',
                      'B':'Unused0','A':'Opaque255; original ortho provider alpha sampled separately'},
          'permissionMipPolicy':'Ordinary resident mips; geometric smoothing',
          'coverageMipPolicy':'Original provider ortho alpha and mask extent sampled/gated at mip0'}
    paths=[Path(__file__).resolve(),ROOT/'scripts/unreal/exterior-context.py',context_path,buildings_path,scene_path,obj_path,ortho_path,Path(layer['rgbaPath'])]
    witnesses=np.flatnonzero(dark)[::max(1,int(dark.sum())//12)][:12]
    return {'schemaVersion':1,'kind':'ortho-projection-protection','owner':OWNER,
            'generatorSha256':sha(Path(__file__)),'activeDesign':context['activeDesign'],
            'housePlacement':context['housePlacement'],'sourceSceneSha256':context['sourceSceneSha256'],
            'sourceObjSha256':context['sourceObjSha256'],'inputFiles':{str(p):sha(p)for p in paths},
            'orthoManifest':{'path':str(ortho_path),'sha256':sha(ortho_path)},'allowedMaterialKeys':list(KEYS),
            'texture':mask,'worldCmToUvRows':rows,'worldBoundsCm':[-half,-half,half,half],
            'policy':{'protectionOnly':True,'noDarkPixelExclusion':True,'noFieldBoundaryExclusion':True,
                      'noCanopyExclusion':True,'noRoadExclusion':True,'providerCoverageSeparate':True,
                      'subjectSiteProtected':True,'officialBuildingBufferCm':building_buffer_cm,
                      'rasterBilinearGuardCm':raster_guard_cm,'geometricFeatherCm':feather_cm,
                      'sourceGroundOrGeometryChanged':False},
            'subjectSiteAudit':site_audit,
            'summary':{'status':'PASS','textureCount':1,'width':SIZE,'height':SIZE,
                       'groundMaterialKeys':list(KEYS),'groundMeshCount':len(ground),
                       'groundBoundsCm':[low.tolist(),high.tolist()],'groundTriangleCentroids':len(centroids),
                       'ordinaryGroundCentroidsTested':int(safe.sum()),'ordinaryGroundCentroidMinimumPermission':float(sampled[safe].min()),
                       'primarySiteBoundarySamples':len(primary),'primarySiteMaximumPermission':float(primary_permission.max()),
                       'darkOrdinaryContextPixelsPermitted':int(dark.sum()),'darkOrdinaryMinimumPermission':float(permission.ravel()[dark].min()/255.),
                       'protectedPixels':int((permission==0).sum()),'featherPixels':int(((permission>0)&(permission<255)).sum()),
                       'ordinaryPixels':int((permission==255).sum()),'greenChannelMinimum':255,'greenChannelMaximum':255,
                       'blueChannelMaximum':0,'alphaChannelMinimum':255},
            'darkSourceWitnesses':[{'worldCm':[float(x.ravel()[i]),float(y.ravel()[i])],
                                    'sourceLinearLuminance':float(lum[i]),'permission':1.}for i in witnesses],
            'limits':['Aerial source currency2024 is inherited; projection is visual context, not current surveyed land condition.',
                      'Official building footprints retain their inherited accuracy; estimated height and finish are unaffected.',
                      'Aerial RGB includes original lighting/shadows; no de-lighting or botanical inference is asserted.',
                      'The protection mask is technical permission only; original imagery and provider coverage remain unchanged.',
                      'Native appearance and performance require a fresh import/cook/package and visual review.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('context','buildings','scene','ortho','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();output=args.output.resolve()
    require(output.is_relative_to(ROOT/'output/unreal'),'Projection output must be isolated')
    require(not output.exists(),'Use a fresh projection revision')
    plan=build(args.context.resolve(),args.buildings.resolve(),args.scene.resolve(),args.ortho.resolve(),output)
    manifest_path=output/'ortho-projection-manifest.json'
    with manifest_path.open('xb')as stream:stream.write(encode(plan))
    with(output/'summary.json').open('xb')as stream:stream.write(encode({'manifest':str(manifest_path),'sha256':sha(manifest_path),**plan['summary']}))
    with(output/'build-environment.json').open('xb')as stream:stream.write(encode({'pythonExecutable':sys.executable,'pythonVersion':sys.version,
         'numpyVersion':np.__version__,'shapelyVersion':shapely.__version__,'generatorSha256':plan['generatorSha256'],'manifestSha256':sha(manifest_path)}))
    print(json.dumps({'manifest':str(manifest_path),'sha256':sha(manifest_path),**plan['summary']}))


if __name__=='__main__':main()
