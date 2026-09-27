"""Grow short green groundcover on the existing bare yard and roadside surfaces."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-yard.py'


def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/f'{name}.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def build(source,output):
    source,output=Path(source).resolve(),Path(output).resolve()
    if output.exists():raise ValueError('Use a new yard output')
    grass=module('exterior-meadow-blades'); rural=module('rural-geometry')
    scene_path=source/'scene.json';obj_path=source/'dom-mm.obj';rural_path=source/'rural-context-geometry.json'
    scene=json.loads(scene_path.read_text());plan=json.loads(rural_path.read_text())
    grass.require(scene['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'},'C/B/B required')
    grass.require(scene['house']['placement']['streetSetbackMm']==scene['house']['placement']['eastSetbackMm']==3000,'Setbacks differ')
    selected=[m for m in plan['meshes'] if m['id'].startswith('verge_') or m['id'] in ('parcel_outer_raw_soil','rear_field_topsoil_mound')]
    grass.require(len(selected)==7,'Unexpected yard source selection')
    triangles=[];coords=[];ids=[]
    for mesh in selected:
        for i in range(0,len(mesh['indices']),3):
            xyz=[mesh['verticesCm'][j] for j in mesh['indices'][i:i+3]]
            triangle=Polygon([p[:2] for p in xyz])
            if triangle.area<.00001:continue
            triangles.append(triangle);coords.append(xyz);ids.append(mesh['id'])
    ground=unary_union(triangles)
    # Ground-level paths, all structural floor/slab footprints, decks, gravel,
    # stepping stones and mulch are protected by their actual OBJ triangles.
    wanted=[row['id'] for row in scene['objects'] if row['enabled'] and (row.get('metadata',{}).get('walkSurface') or 'real-mulch' in row['materialNames'])
            and row['id'] not in ('DOM_00000','DOM_00001','DOM_00002','DOM_00003','DOM_00004','DOM_00007','DOM_00008')]
    original=rural.read_obj(obj_path,wanted)
    protected=[Polygon([p[:2] for p in t]) for ts in original.values() for t in ts if Polygon([p[:2] for p in t]).area>.00001]
    protected.extend(Polygon(p) for p in plan['managedLawnKeepPolygonsCm'])
    for surface in scene['surfaces'].values():
        if isinstance(surface,dict) and surface.get('polygonMm'):
            protected.append(Polygon([((p['x']-15200)/10,(10800-p['y'])/10) for p in surface['polygonMm']]))
    protected=unary_union(protected)
    allowed=ground.buffer(-14.03).difference(protected.buffer(18.03))
    xmin,ymin,xmax,ymax=allowed.bounds;rng=np.random.default_rng(6012262026092706)
    x,y=np.meshgrid(np.arange(xmin,xmax,17.),np.arange(ymin,ymax,17.),indexing='ij')
    x=x.ravel()+rng.uniform(-5,5,x.size);y=y.ravel()+rng.uniform(-5,5,y.size)
    inside=shapely.contains_xy(allowed,x,y);x,y=np.round(x[inside],5),np.round(y[inside],5)
    z,sources=grass.sample_ground(x,y,triangles,np.array(coords),ids)
    heights=7.5+4.5*(.5+.25*np.sin(x/340)+.25*np.cos(y/270))+rng.uniform(-.4,.4,len(x))
    rows=[{'role':'grass','positionCm':[float(a),float(b),round(float(c),5)],'radiusCm':14.,'heightCm':round(float(h),3),
           'yawDeg':round(float(angle),3),'sourceMeshId':identity,'sourceFinish':'short-green-yard-cover'}
          for a,b,c,h,angle,identity in zip(x,y,z,heights,rng.uniform(0,360,len(x)),sources)]
    points=shapely.points(x,y)
    edge=float(shapely.distance(points,ground.boundary).min());obstacle=float(shapely.distance(points,protected).min())
    grass.require(edge>=14 and obstacle>=18,'Full yard crown clearance failed')
    inputs={str(p):grass.sha(p) for p in [scene_path,obj_path,rural_path,Path(__file__),ROOT/'scripts/unreal/exterior-meadow-blades.py',ROOT/'scripts/unreal/rural-geometry.py']}
    result={'schemaVersion':1,'owner':OWNER,'generatorSha256':grass.sha(__file__),'activeDesign':scene['activeDesign'],
            'sourceSceneSha256':grass.sha(scene_path),'sourceObjSha256':grass.sha(obj_path),'inputFiles':inputs,
            'greenSourceMeshIds':[m['id'] for m in selected],'yardBladePlacements':rows,
            'audit':{'status':'PASS','instances':len(rows),'perSource':dict(Counter(sources)),'sourceAreaM2':ground.area/10000,
                     'plantedDomainM2':allowed.area/10000,'minimumGroundBoundaryClearanceCm':edge,'minimumProtectedClearanceCm':obstacle,
                     'crownRadiusCm':14,'heightRangeCm':[float(min(heights)),float(max(heights))],
                     'protectedOriginalSourceIds':wanted,
                     'groundMethod':'Exact barycentric Z on existing rural source meshes; no geometry or collision edit'},
            'interpretation':'Illustrative maintained green-season groundcover requested by user; not a survey of current vegetation'}
    output.mkdir(parents=True);grass.write(output/'yard-plan.json',result,compact=True)
    grass.write(output/'yard-audit.json',result['audit'])
    return result['audit']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();print(json.dumps(build(args.source,args.output)))
