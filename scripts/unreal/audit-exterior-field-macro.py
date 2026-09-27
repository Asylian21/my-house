"""Read-only, independent geometry and encoding audit of one field-scalar manifest."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
import shapely
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True);p.add_argument('--output',required=True);args=p.parse_args()
m=read(args.manifest);inputs=m['inputFiles'];pins={k:sha(k)==v for k,v in inputs.items()}
context=read(next(k for k in inputs if k.endswith('context-plan.json')))
ortho=read(next(k for k in inputs if k.endswith('orthophoto-manifest.json')))
buildings=read(next(k for k in inputs if k.endswith('building-plan.json')))
a=np.asarray(Image.open(m['texture']['path']));labels=np.asarray(Image.open(m['summary']['domainTextureLabels']['path']))
h,w=a.shape[:2];lo_x,lo_y,hi_x,hi_y=m['worldBoundsCm'];dx=(hi_x-lo_x)/w;dy=(hi_y-lo_y)/h
xx=lo_x+(np.arange(w)+.5)*dx;yy=hi_y-(np.arange(h)+.5)*dy;x,y=np.meshgrid(xx,yy)
active=(a[:,:,3]>0)&(a[:,:,1]==255)&(a[:,:,2]==255);points=shapely.points(x[active],y[active])
site=ortho['worldFrame']['siteAxis'];origin=np.asarray(ortho['worldOriginNationalMetres']);u=np.array([site['ux'],site['uy']]);v=np.array([site['vx'],site['vy']])
assert abs(u@v)<1e-10 and abs(u@u-1)<1e-10 and abs(v@v-1)<1e-10
# Independent dot-product projection, not the generator's inverted matrix.
def parcel(row):
    polygons=[]
    for rings in row['polygonsSjtskMm']:
        converted=[]
        for ring in rings:
            delta=np.asarray(ring)/1000-origin
            converted.append(np.stack([delta@u*100,-delta@v*100],axis=-1))
        polygons.append(Polygon(converted[0],converted[1:]))
    return unary_union(polygons)
subject=unary_union([parcel(r) for r in context['parcels'] if r['parcelNumber']=='6012/26'])
roads=unary_union([parcel(r) for r in context['parcels'] if r['parcelNumber'] in ('6012/1','6035/1','6013','6019')])
protected=unary_union([Polygon(t) for t in context['protectedTrianglesCm']])
houses=unary_union([Polygon(r[0],r[1:]) for b in buildings['buildings'] for r in b['polygonsCm']])
canopy=unary_union([Polygon(r['polygonCm']) for r in context['regionalVegetationPolicy']['regions']])
clearances={name:float(np.min(shapely.distance(points,shape))) for name,shape in [('subject',subject),('roads',roads),('protected',protected),('houses',houses),('canopy',canopy)]}
mesh_by_id={r['id']:r for r in context['meshes']};minimum_field_distance=float('inf');outside=0;wrong_material=0
for row in m['fields']:
    use=active&(labels==row['id'])
    if not use.any():continue
    mesh=mesh_by_id[row['meshId']];vertices=np.asarray(mesh['verticesCm']);indices=np.asarray(mesh['indices']).reshape(-1,3)
    triangles=[Polygon(t[:,:2]) for t in vertices[indices] if Polygon(t[:,:2]).area>1e-5]
    domain=unary_union(triangles);samples=shapely.points(x[use],y[use])
    outside+=int(np.sum(~shapely.contains(domain,samples)))
    minimum_field_distance=min(minimum_field_distance,float(np.min(shapely.distance(samples,domain.boundary))))
    wrong_material+=int(row['material'] not in ('context_meadow','context_fallow','context_crop','context_arable') or row['finish']!='surface')
# Bilinear sampling support extends at most one pixel diagonally from active texels.
footprint_radius=float(np.hypot(dx,dy));min_world=np.min([x[active].min()-lo_x,hi_x-x[active].max(),y[active].min()-lo_y,hi_y-y[active].max()])
factor=np.clip(1+(a[:,:,0].astype(float)-128)*.70/255,*m['factorRange']);effect=1+(factor-1)*(a[:,:,3]/255)*((a[:,:,1]>=253)&(a[:,:,2]>=253))
checks={
 'allSourcePinsValid':all(pins.values()),'texturePinValid':sha(m['texture']['path'])==m['texture']['sha256'],
 'labelPinValid':sha(m['summary']['domainTextureLabels']['path'])==m['summary']['domainTextureLabels']['sha256'],
 'rgba1024Linear':a.shape==(1024,1024,4) and m['texture']['sRGB'] is False,
 'binaryDomainAndCoverage':set(np.unique(a[:,:,1])).issubset({0,255}) and set(np.unique(a[:,:,2])).issubset({0,255}),
 'activeDomainValid':bool(np.all((labels[active]>0)&(a[:,:,2][active]==255))),
 'neutralOutsideTrusted':bool(np.all(effect[a[:,:,1]==0]==1) and np.all(a[:,:,0][a[:,:,1]==0]==128)),
 'boundedFactor':bool(effect.min()>=m['factorRange'][0] and effect.max()<=m['factorRange'][1]),
 'eligibleMaterialSurfaceOnly':wrong_material==0,'activeInsideOriginalFieldGeometry':outside==0,
 'fullBilinearFootprintInsideOriginalField':minimum_field_distance>footprint_radius,
 'subjectClearance':clearances['subject']-footprint_radius>1000,'roadClearance':clearances['roads']-footprint_radius>300,
 'protectedClearance':clearances['protected']-footprint_radius>200,'houseClearance':clearances['houses']-footprint_radius>1000,
 'canopyClearance':clearances['canopy']-footprint_radius>1200,
 'radialSupportBelow255m':float(np.hypot(x[active],y[active]).max())+footprint_radius<25500,
 'textureRawUvInterior':float(min_world)>footprint_radius,
 'mip0ContainmentAndUncompressedData':m['sampling']['containmentMip']==0 and m['nativeTexturePolicy']['containmentSamplerMip']==0 and m['nativeTexturePolicy']['compression']=='TC_VectorDisplacementmap' and m['nativeTexturePolicy']['samplerType']=='LinearColor' and m['nativeTexturePolicy']['neverStream'] is True,
}
report={'schemaVersion':1,'manifest':{'path':str(Path(args.manifest).resolve()),'sha256':sha(args.manifest)},'auditor':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},'checks':checks,'allPass':all(checks.values()),'sourcePinCount':len(pins),'activeTexels':int(active.sum()),'maxFactorErrorAtEncodedNeutral':abs((1+(128/255-128/255)*.70)-1),'bilinearSupportRadiusCm':footprint_radius,'minimumActiveOriginalFieldBoundaryCm':minimum_field_distance,'minimumActiveClearancesCm':clearances,'maximumActiveRadiusCm':float(np.hypot(x[active],y[active]).max()),'limits':'Data-domain and prescribed-sampler audit only; native texture settings/material graph and final rendering require native QA.'}
Path(args.output).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');print(json.dumps(report,indent=2));assert report['allPass']
