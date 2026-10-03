"""R14 preview-first finite-station 3D grass geometry, isolated CPU only.

An actual quadratic centreline through the three source centres is sampled at
finite stations. Three transverse vertices form a shallow V/arc and smoothly
transported geometric normals; body edges genuinely bend between stations.
The source root/seeds and photograph are unchanged. Full-population budgets are
reported up front; no20-master/coverage/integration claim is made by a preview.
"""
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-lawn-arc-study.py'
FOLD_SCRIPT=ROOT/'scripts/unreal/exterior-lawn-folded-study.py'
FOLD_SHA='3434eb5884f9306307ed43ae03e0b7e54acefb3842c141136b47fa61adec087b'
MID='lawn_natural_0_3_LOD0'
PH_SOURCE=ROOT/'output/unreal/exterior-lawn-photo-variants-20261001-r3-study'
DONOR=ROOT/'output/unreal/exterior-lawn-tapered-integration-20261001-r1c'
MATERIAL='lawn_photographic_blade'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def pin(path):return{'path':str(Path(path).resolve()),'sha256':sha(path)}
def require(value,message):
    if not value:raise RuntimeError(message)
def write(path,value):
    with Path(path).open('x')as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def curve(centres,peak,t):
    # Lagrange interpolation: old root, source taper peak and tip remain actual
    # endpoints. Derivative transports an orthogonal transverse blade frame.
    weights=np.array([(t-peak)*(t-1)/peak, t*(t-1)/(peak*(peak-1)), t*(t-peak)/(1-peak)])
    derivatives=np.array([(2*t-peak-1)/peak,(2*t-1)/(peak*(peak-1)),(2*t-peak)/(1-peak)])
    return weights@centres,derivatives@centres


def blade_mesh(source,meta,stations,identity):
    p=[];uv=[];uv1=[];colors=[];faces=[];ranges=[]
    for blade in meta['bladeRanges']:
        index=blade['bladeIndex'];offset=blade['vertexOffset'];original=source['positionsCm'][offset:offset+5]
        seed=float(source['uv1'][offset,0]);peak=blade['peakT']
        centres=np.array([(original[0]+original[1])/2,(original[2]+original[3])/2,original[4]])
        root_side=(original[1]-original[0]);root_side/=np.linalg.norm(root_side)
        shoulder_side=(original[3]-original[2]);shoulder_side/=np.linalg.norm(shoulder_side)
        root_width=float(np.linalg.norm(original[1]-original[0]));width=float(np.linalg.norm(original[3]-original[2]))
        first=len(p);tri_start=len(faces);rings=[];centerline=[];ridges=[]
        for t in stations:
            middle,tangent=curve(centres,peak,t);tangent/=np.linalg.norm(tangent)
            blend=min(1.,t/peak);side=root_side*(1-blend)+shoulder_side*blend
            side-=tangent*np.dot(tangent,side);side/=np.linalg.norm(side)
            normal=np.cross(tangent,side);normal/=np.linalg.norm(normal)
            # Deterministic transported torsion after the widest source section.
            twist=(seed-.5)*.28*max(0.,(t-peak)/(1-peak))
            side=side*math.cos(twist)+normal*math.sin(twist);normal=np.cross(tangent,side);normal/=np.linalg.norm(normal)
            width_at_t=root_width+(width-root_width)*t/peak if t<=peak else width*(1-t)/(1-peak)
            lo,hi=(0,2)if t<=peak else(2,4);a=0.if t<=peak else peak;b=peak if t<=peak else 1.;weight=(t-a)/(b-a)
            left_uv=source['uv0'][offset+lo]*(1-weight)+source['uv0'][offset+hi]*weight
            right_uv=source['uv0'][offset+(lo+1 if lo==0 else 3)]*(1-weight)+source['uv0'][offset+hi+(1 if hi==2 else 0)]*weight
            left_c=source['colors'][offset+lo]*(1-weight)+source['colors'][offset+hi]*weight
            right_c=source['colors'][offset+(lo+1 if lo==0 else 3)]*(1-weight)+source['colors'][offset+hi+(1 if hi==2 else 0)]*weight
            height=width_at_t*(.15+.055*((seed*11.17+index*.13)%1))
            ring=[]
            for u in ([0.,1.]if t==0. else[.5]if t==1. else[0.,.5,1.]):
                vertex=middle+side*width_at_t*(u-.5)+normal*height*(1-(2*u-1)**2)
                # Basal source vertices and final tip are byte-preserved floats;
                # the source keep polygons remain a strict crown constraint.
                if t==0.:vertex=original[int(u)].copy()
                if t==1.:vertex=original[4].copy()
                ring.append(len(p));p.append(vertex);uv.append(left_uv*(1-u)+right_uv*u)
                uv1.append(source['uv1'][offset]);colors.append(left_c*(1-u)+right_c*u)
            rings.append(ring);centerline.append(middle.tolist());ridges.append(height)
        for a,b in zip(rings,rings[1:]):
            if len(a)==2:
                faces.extend([[a[0],a[1],b[1]],[a[0],b[1],b[0]],[a[1],b[2],b[1]]])
            elif len(b)==1:faces.extend([[a[0],a[1],b[0]],[a[1],a[2],b[0]]])
            else:faces.extend([[a[0],a[1],b[0]],[a[1],b[1],b[0]],[a[1],a[2],b[1]],[a[2],b[2],b[1]]])
        ranges.append({'bladeIndex':index,'vertexOffset':first,'vertexCount':len(p)-first,'triangleOffset':tri_start,'triangleCount':len(faces)-tri_start,
                       'sourceRootCm':blade['rootCm'],'sourceSeed':seed,'sourcePeakT':peak,'stationsT':stations,
                       'centerlineCm':centerline,'ridgeHeightCm':ridges,'sourceWidthCm':width,'sourceLowLeaningLeaf':blade['low']})
    record={'nodeName':identity,'positionsCm':np.asarray(p),'uv0':np.asarray(uv),'uv1':np.asarray(uv1),
            'colors':np.asarray(colors),'triangles':np.asarray(faces),'bladeRanges':ranges}
    record['positionsCm']=(record['positionsCm'][:,[0,2,1]]/100).astype('<f4')[:,[0,2,1]].astype(float)*100
    for key in('uv0','uv1','colors'):record[key]=record[key].astype('<f4').astype(float)
    normals=np.zeros_like(record['positionsCm'])
    for face in record['triangles']:
        q=record['positionsCm'][face];normal=np.cross(q[1]-q[0],q[2]-q[0]);require(np.linalg.norm(normal)>1e-8,'Degenerate arc triangle');normals[face]+=normal
    normals/=np.linalg.norm(normals,axis=1)[:,None];record['normals']=normals
    return record


def render_preview(out,baseline,variants,meta,recipe,api):
    renderer=api.module('r14_arc_pinned_renderer',ROOT/'scripts/unreal/exterior-lawn-photo-uv-study.py')
    function=inspect.getsource(renderer.render)
    old='screen=np.column_stack([p@right*100+width/2,height*.82-p@up*100,p@camera])'
    new='screen=np.column_stack([(p@right-frame[0])*frame[2]+width/2,height-55-(p@up-frame[1])*frame[2],p@camera])'
    require(function.count(old)==1,'Pinned camera function differs');namespace=dict(renderer.__dict__)
    exec(compile(function.replace(old,new),'<r14_arc_new_cpu_camera>','exec'),namespace)
    texture=np.asarray(Image.open(recipe['maps']['albedo']['path']),dtype=float)/255
    alpha=np.asarray(Image.open(recipe['maps']['alpha']['path']),dtype=float)/65535
    selected=api.selection(baseline,meta)[:4]
    for few in(False,True):
        assembled=[]
        for label,row in [('Current R13 photographic5v3tri',baseline),('Quadratic centreline9v9tri',variants['three_segments']),('Quadratic centreline12v13tri',variants['four_segments'])]:
            if few:
                p=[];n=[];uv=[];ix=[]
                for slot,index in enumerate(selected):
                    b=row['bladeRanges'][index];a=b['vertexOffset'];count=b['vertexCount'];offset=len(p)-a
                    q=row['positionsCm'][a:a+count].copy();q[:,:2]+=np.array([(slot-1.5)*1.15,0])-np.asarray(b.get('sourceRootCm',b.get('rootCm')))
                    p.extend(q);n.extend(row['normals'][a:a+count]);uv.extend(row['uv0'][a:a+count]);ix.extend(row['triangles'][b['triangleOffset']:b['triangleOffset']+b['triangleCount']]+offset)
                item={'p':np.asarray(p),'n':np.asarray(n),'ix':np.asarray(ix)};uv=np.asarray(uv)
            else:item={'p':row['positionsCm'],'n':row['normals'],'ix':row['triangles']};uv=row['uv0']
            assembled.append((label,item,uv))
        camera=np.array([.22,.92,.42]);camera/=np.linalg.norm(camera);right=np.array([camera[1],-camera[0],0.]);right/=np.linalg.norm(right);up=np.cross(right,camera)
        allp=np.concatenate([item['p']for _,item,_ in assembled]);sx=allp@right;sy=allp@up
        namespace['frame']=[(sx.min()+sx.max())/2,sy.min(),min(570/np.ptp(sx),540/np.ptp(sy))]
        plate=Image.new('RGB',(1980,740),'#eeebe3');draw=ImageDraw.Draw(plate);stats={}
        for col,(label,item,uv)in enumerate(assembled):
            image,result=namespace['render'](item,uv,texture,alpha,recipe,'photo',None);plate.paste(image,(col*660,48));draw.text((col*660+12,16),label,fill='#202820');stats[label]=result
        draw.text((12,704),'Actual exported3D centreline/cross-section + same original PH photo. CPU geometric-normal diffuse only; original normalDX/roughness/SSS/native lighting/mips not shaded.',fill='#202820')
        draw.text((12,724),'Same four source leaf roots rearranged for display.'if few else'Same actual64 source leaf roots. UVs transported from the current source leaf body. Preview only; no full-population coverage/native acceptance.',fill='#202820')
        plate.save(out/('four-arc-leaves.png'if few else'arc-clump-comparison.png'));write(out/('four-render.json'if few else'clump-render.json'),stats)


def build(out):
    require(out.is_relative_to(ROOT/'output/unreal')and not out.exists(),'Use fresh preview output')
    require(sha(FOLD_SCRIPT)==FOLD_SHA,'Frozen previous study changed')
    api=load('r14_frozen_fold_utilities',FOLD_SCRIPT);inputs={str(p):h for p,h in api.PINS.items()}
    inputs[str(FOLD_SCRIPT)]=FOLD_SHA;inputs[str(Path(__file__).resolve())]=sha(__file__)
    recipe=read(PH_SOURCE/'material-manifest.json')[MATERIAL]
    for row in recipe['maps'].values():inputs[row['path']]=row['sha256']
    for p,h in inputs.items():require(sha(p)==h,'Pinned source changed: '+p)
    decoder=api.module('r14_arc_current_photo_reader',ROOT/'scripts/unreal/exterior-lawn-photo-variants.py')
    _,_,_,decoded=decoder.glb(PH_SOURCE/'lawn-photographic-variants.glb')
    source=api.native_record(decoded[MID.replace('lawn_natural_','lawn_photo_',1)])
    meta=next(m for m in read(DONOR/'lawn-natural-prototypes.json')if m['nodeName']==MID)
    source.update(bladeRanges=deepcopy(meta['bladeRanges']),nodeName=MID)
    tangent=api.module('r14_arc_tangent_transport',ROOT/'scripts/unreal/exterior-lawn-tapered-photo-uv-study.py')
    out.mkdir();variants={};measurements={}
    for key,stations in [('three_segments',[0.,.30,.72,1.]),('four_segments',[0.,.22,.52,.78,1.])]:
        record=blade_mesh(source,meta,stations,'lawn_arc_0_3_LOD0');folder=out/key;folder.mkdir()
        api.OWNER=OWNER;frames=api.write_glb(folder/'arc-prototype.glb',[record],tangent)
        _,_,_,actual=decoder.glb(folder/'arc-prototype.glb');saved=api.native_record(actual[record['nodeName']]);saved.update(bladeRanges=record['bladeRanges'],nodeName=record['nodeName'])
        require(np.array_equal(saved['positionsCm'],record['positionsCm'])and np.array_equal(saved['uv0'],record['uv0']),'Saved float32 geometry/UV differs')
        radius=float(np.linalg.norm(saved['positionsCm'][:,:2],axis=1).max());old_radius=float(np.linalg.norm(source['positionsCm'][:,:2],axis=1).max())
        require(radius<=old_radius+1e-6,'New finite-station crown exceeds source crown')
        require(saved['positionsCm'][:,2].min()>=source['positionsCm'][:,2].min()-1e-6 and saved['positionsCm'][:,2].max()<=source['positionsCm'][:,2].max()+1e-6,'Source vertical cap exceeded')
        norms=np.linalg.norm(saved['normals'],axis=1);require(np.max(abs(norms-1))<1e-6,'Saved normal is not unit')
        variants[key]=saved;triangles=len(saved['triangles'])//64
        width=[];curve_deflection=[]
        for b in saved['bladeRanges']:
            q=np.asarray(b['centerlineCm']);line=q[0]+(q[-1]-q[0])*np.asarray(stations)[:,None]
            curve_deflection.append(float(np.linalg.norm(q-line,axis=1).max()))
            width.append(max(b['ridgeHeightCm']))
        measurements[key]={'vertices':len(saved['positionsCm']),'triangles':len(saved['triangles']),'leaves':64,
                           'verticesPerLeaf':len(saved['positionsCm'])//64,'trianglesPerLeaf':triangles,'stationsT':stations,
                           'sourceRootAndTipVerticesPreserved':True,'sourceCrownsPreserved':True,'actualRadiusCm':radius,'sourceRadiusCm':old_radius,
                           'centrelineDeflectionFromStraightRootTipCm':[min(curve_deflection),max(curve_deflection)],
                           'ridgeHeightCm':[min(width),max(width)],'actualUvTriangleFrameMetrics':frames,
                           'prospectiveFullPopulationCloseTriangles':6190400*triangles,'baselinePopulationTriangles':18571200,
                           'fullPopulationCoverageMeasured':False,'all20MastersGenerated':False,'nativeJobsRun':0}
        write(folder/'prototype.json',{'record':{k:v.tolist()if isinstance(v,np.ndarray)else v for k,v in saved.items()},'measurements':measurements[key]})
    render_preview(out,source,variants,meta,recipe,api)
    for p,h in inputs.items():require(sha(p)==h,'Pinned source changed during preview: '+p)
    with(out/'study-source.py').open('x')as f:f.write(Path(__file__).read_text())
    receipt={'schemaVersion':1,'owner':OWNER,'generatorSha256':sha(__file__),'status':'PREVIEW_ONLY_FINITE_STATION_SOURCE_GEOMETRY_NATIVE_PENDING',
             'inputFiles':inputs,'profiles':measurements,'originalPhotographicMaterialUnchanged':True,
             'sameActualSourceLeafRootsSeedsAndEndpointCaps':True,'photographicPixelsUnmodified':True,
             'limits':['Only one64-leaf master generated; preview precedes20-master export and4-window coverage.','Curved XY outline differs from current straight leaf segments but all vertices fit its full source crown.','Three transverse samples are a coarse V/arc, not a smooth five-sample botanical cross-section.','All-close55.714M/80.475M budgets are explicit and unapproved; cheaper mid/far remains a future proposal.','CPU diffuse geometric normals only; no Unreal normalDX/roughness/SSS/mips/shadows/performance proof.'],
             'formalUnitTestsRun':0,'nativeJobsRun':0,'gpuJobsRun':0,'fullPopulationCoverageMeasured':False,'nativeVisualAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'integrationAuthorized':False}
    write(out/'preview.json',receipt);print(json.dumps({'preview':str(out/'preview.json'),'sha256':sha(out/'preview.json'),'prospectiveBudgets':{k:v['prospectiveFullPopulationCloseTriangles']for k,v in measurements.items()}}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'output/unreal/exterior-lawn-arc-20261001-r1-preview')
    build(parser.parse_args().output.resolve())
