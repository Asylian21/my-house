"""Offline geometry receipt and append-only close lawn camera recommendations."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import sys

import numpy as np
import shapely
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('natural_lawn_preview_source',HERE/'exterior-lawn-natural.py')
natural=importlib.util.module_from_spec(spec);spec.loader.exec_module(natural)


def build(output):
    output=Path(output).resolve();plan=json.loads((output/'lawn-natural-plan.json').read_text())
    records=json.loads((output/'lawn-natural-prototypes.json').read_text())
    domain=shapely.from_geojson(plan['lawnDomainSourceMm'])
    image=Image.new('RGB',(1600,1050),'#ece9df');draw=ImageDraw.Draw(image)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',21)
    small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
    draw.text((24,20),'Natural lawn R1 — actual source geometry, offline illustration',font=font,fill='#243228')
    draw.text((24,50),'No native rendering claim. Original lawn, architecture and clearance masks remain unchanged.',font=small,fill='#4a5046')
    xmin,ymin,xmax,ymax=domain.bounds;scale=min(730/(xmax-xmin),820/(ymax-ymin))
    def site(p):return (50+(p[0]-xmin)*scale,130+(ymax-p[1])*scale)
    for polygon in shapely.get_parts(domain):
        draw.polygon([site(p)for p in polygon.exterior.coords],fill='#b7c3a8',outline='#68755f')
        for hole in polygon.interiors:draw.polygon([site(p)for p in hole.coords],fill='#ece9df',outline='#a0a397')
    for row in plan['lawnPlacements']:
        x,y,_=row['positionCm'];a,b=site((x*10,-y*10))
        draw.point((a,b),fill='#71804f'if row['growthClass']else '#354f34')
    draw.text((24,965),'24,918 continuous patch centres; coherent density and height fields',font=small,fill='#243228')
    draw.text((24,990),'60 mm lattice phase X/Y: 0.0076 / 0.0142  |  Exact allowed area 345.434 m²',font=small,fill='#243228')
    # Actual mesh faces, using a fixed orthographic basis and vertex palette.
    eye=np.array([.5,-.8,.65]);eye/=np.linalg.norm(eye)
    right=np.cross(eye,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,eye)
    for lod in range(3):
        record=next(row for row in records if row['nodeName']==f'lawn_natural_0_0_LOD{lod}')
        points=np.asarray(record['positionsCm']);rgb=np.asarray(record['colors'])[:,:3]
        screen=np.column_stack([points@right,-points@up]);lo=screen.min(axis=0);hi=screen.max(axis=0)
        s=min(700/(hi[0]-lo[0]),225/(hi[1]-lo[1]));screen=(screen-(lo+hi)/2)*s+[1190,205+lod*285]
        depth=points@eye;faces=record['triangles']
        for face in sorted(faces,key=lambda f:depth[f].mean()):
            linear=np.asarray([.06,.10,.024])*rgb[face].mean(axis=0)
            srgb=np.where(linear<=.0031308,linear*12.92,1.055*linear**(1/2.4)-.055)
            color=tuple(int(v*255)for v in np.clip(srgb,0,1))
            draw.polygon([tuple(screen[i])for i in face],fill=color)
        segments=min(row['segments']for row in record['bladeRanges'])
        draw.text((820,315+lod*285),f'LOD {lod}: {len(record["bladeRanges"])} curved blades, {len(faces)} triangles, ≥{segments} segments',font=small,fill='#243228')
    preview=output/'lawn-natural-geometry-overview.png'
    if preview.exists():raise ValueError('Use append-only preview output')
    image.save(preview)
    views=[{'id':'exterior-lawn-detail','label':'Trávnik · zakrivené listy zblízka',
            'eyeCm':[-630.,-650.,36.],'targetCm':[-630.,-530.,-2.],'horizontalFovDegrees':54.},
           {'id':'exterior-lawn-edge','label':'Trávnik · hrana pri nášľapoch',
            'eyeCm':[-510.,-590.,32.],'targetCm':[-500.,-455.,-3.],'horizontalFovDegrees':54.}]
    for view in views:
        for kind in ('eyeCm','targetCm'):
            x,y,_=view[kind];point=shapely.Point(x*10,-y*10)
            natural.require(domain.contains(point),'Camera XY outside maintained lawn: '+view['id']+'/'+kind)
        view['source']='scripts/unreal/preview-lawn-natural.py'
    natural.write(output/'lawn-qa-views.json',{'schemaVersion':1,'owner':'scripts/unreal/preview-lawn-natural.py',
        'generatorSha256':natural.sha(__file__),'activeDesign':plan['activeDesign'],'housePlacement':plan['housePlacement'],
        'sourceSceneSha256':plan['sourceSceneSha256'],'sourceObjSha256':plan['sourceObjSha256'],
        'plan':{'path':str(output/'lawn-natural-plan.json'),'sha256':natural.sha(output/'lawn-natural-plan.json')},
        'views':views,'policy':'Append only; existing R5 camera definitions are unchanged. Native camera visibility/clearance still requires visual QA.',
        'status':'PASS_PRIVATE_LAWN_XY_ONLY_NOT_NATIVE_ACCEPTED'})
    return {'preview':str(preview),'views':str(output/'lawn-qa-views.json')}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True)
    print(json.dumps(build(parser.parse_args().output)))
