"""Fresh R14 measured20-master arc proposal; no scene or native integration.

LOD0:9-triangle finite-station curved/V-section leaves retaining the actual source
widest shoulder section rather than sampling an arbitrary t=.30 station. LOD1:byte-preserved
budgeted R14 folded source. LOD2:byte-preserved current R13 photographic source.
Near LOD is freshly rastered in the original four interior/two boundary ROIs.
Mid/far ROI metrics are transferred only after actual saved attribute/index byte
equality against the failed R2 source GLB has independently been established.
Failed original gates remain failures; density, optical response and targets
are not adjusted. Full close budget55.714M is explicitly not performance proof.
"""
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-lawn-arc-peak-study.py'
ARC=ROOT/'scripts/unreal/exterior-lawn-arc-study.py'
ARC_SHA='95c8470334e89e80c1b77026c99f4961a513466e6aa94cd0ff73286885ee5205'
FOLD=ROOT/'scripts/unreal/exterior-lawn-folded-study.py'
FOLD_SHA='3434eb5884f9306307ed43ae03e0b7e54acefb3842c141136b47fa61adec087b'
MID=ROOT/'output/unreal/exterior-lawn-folded-20261001-r1-study/adaptive/folded-lawn.glb'
MID_SHA='6ef075bc8216430ce3967cdb3339200e7ec380f6f6b026441c3ff8e5837b9ee7'
PHOTO=ROOT/'output/unreal/exterior-lawn-photo-variants-20261001-r3-study'
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


def peak_blade_mesh(source,meta,stations,identity):
    p=[];uv=[];uv1=[];colors=[];faces=[];ranges=[]
    for blade in meta['bladeRanges']:
        index=blade['bladeIndex'];offset=blade['vertexOffset'];original=source['positionsCm'][offset:offset+5]
        seed=float(source['uv1'][offset,0]);peak=blade['peakT']
        centres=np.array([(original[0]+original[1])/2,(original[2]+original[3])/2,original[4]])
        root_side=(original[1]-original[0]);root_side/=np.linalg.norm(root_side)
        shoulder_side=(original[3]-original[2]);shoulder_side/=np.linalg.norm(shoulder_side)
        root_width=float(np.linalg.norm(original[1]-original[0]));width=float(np.linalg.norm(original[3]-original[2]))
        first=len(p);tri_start=len(faces);rings=[];centerline=[];ridges=[]
        stations = [0., float(peak), .72, 1.]
        for t in stations:
            middle,tangent=curve(centres,peak,t);tangent/=np.linalg.norm(tangent)
            blend=min(1.,t/peak);side=root_side*(1-blend)+shoulder_side*blend
            side-=tangent*np.dot(tangent,side);side/=np.linalg.norm(side)
            normal=np.cross(tangent,side);normal/=np.linalg.norm(normal)
            # Deterministic transported torsion after the widest source section.
            twist=(seed-.5)*.28*max(0.,(t-peak)/(1-peak))
            side=side*math.cos(twist)+normal*math.sin(twist);normal=np.cross(tangent,side);normal/=np.linalg.norm(normal)
            width_at_t=root_width+(width-root_width)*t/peak if t<=peak else width*(1-t)/(1-peak)
            lo,hi=(0,2)if t<=peak else(2,4);a=0. if t<=peak else peak;b=peak if t<=peak else 1.;weight=(t-a)/(b-a)
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
                # The widest two source shoulder corners remain actual source
                # vertices; the new midpoint forms a real transverse ridge.
                if t==peak and u in (0.,1.):vertex=original[2+int(u)].copy()
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


def encode(path,records,tangent_api):
    binary=bytearray();doc={'asset':{'version':'2.0','generator':OWNER},'scene':0,'scenes':[{'nodes':list(range(len(records)))}],
        'nodes':[],'meshes':[],'accessors':[],'bufferViews':[],'buffers':[],'materials':[{'name':MATERIAL,'doubleSided':True}]}
    def accessor(values,kind,dtype='<f4',target=34962):
        a=np.asarray(values,dtype=dtype);binary.extend(b'\0'*(-len(binary)%4));offset=len(binary);binary.extend(a.tobytes())
        doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':a.nbytes,'target':target})
        q={'bufferView':len(doc['bufferViews'])-1,'componentType':5126 if dtype=='<f4' else 5125,'count':len(a),'type':kind}
        if kind=='VEC3':q.update(min=a.min(0).tolist(),max=a.max(0).tolist())
        doc['accessors'].append(q);return len(doc['accessors'])-1
    for row in records:
        if 'sourceRaw' in row:raw=row['sourceRaw']
        else:
            n=row['normals'].astype('<f4').astype(float)
            t,_=tangent_api.tangent_frame(row['positionsCm'],n,row['uv0'],row['triangles'])
            raw={'POSITION':row['positionsCm'][:,[0,2,1]]/100,'NORMAL':n[:,[0,2,1]],
                 'TANGENT':np.column_stack([t[:,:3][:,[0,2,1]],-t[:,3]]),'TEXCOORD_0':row['uv0'],
                 'TEXCOORD_1':row['uv1'],'COLOR_0':row['colors'],'indices':row['triangles'][:,[0,2,1]]}
        attr={k:accessor(raw[k],kind)for k,kind in [('POSITION','VEC3'),('NORMAL','VEC3'),('TANGENT','VEC4'),
              ('TEXCOORD_0','VEC2'),('TEXCOORD_1','VEC2'),('COLOR_0','VEC4')]}
        ix=accessor(raw['indices'].reshape(-1),'SCALAR','<u4',34963)
        doc['nodes'].append({'name':row['nodeName'],'mesh':len(doc['meshes'])})
        doc['meshes'].append({'name':row['nodeName'],'primitives':[{'attributes':attr,'indices':ix,'material':0}]})
    binary.extend(b'\0'*(-len(binary)%4));doc['buffers']=[{'byteLength':len(binary)}]
    raw=json.dumps(doc,separators=(',',':'),allow_nan=False).encode();raw+=b' '*(-len(raw)%4)
    with path.open('xb')as f:
        f.write(struct.pack('<4sII',b'glTF',2,28+len(raw)+len(binary)));f.write(struct.pack('<II',len(raw),0x4e4f534a));f.write(raw)
        f.write(struct.pack('<II',len(binary),0x004e4942));f.write(binary)


def independent_frames(row,raw,source):
    p=row['positionsCm'];n=row['normals'];t=raw['TANGENT'][:,:3][:,[0,2,1]].astype(float);uv=row['uv0'];ix=row['triangles']
    require(np.isfinite(p).all()and np.isfinite(n).all()and np.isfinite(t).all()and np.isfinite(uv).all(),'Nonfinite saved attribute')
    require(np.max(abs(np.linalg.norm(n,axis=1)-1))<2e-6 and np.max(abs(np.linalg.norm(t,axis=1)-1))<2e-6,'Saved frames are not unit')
    require(np.max(abs(np.sum(n*t,axis=1)))<2e-6,'Saved tangent is not orthogonal')
    require(set(np.unique(raw['TANGENT'][:,3]))<={-1.,1.},'Saved tangent handedness invalid')
    require(ix.min()==0 and ix.max()<len(p),'Saved indices escape attributes')
    q=p[ix];cross=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);area=np.linalg.norm(cross,axis=1)/2
    mapped=uv[ix];a=mapped[:,1]-mapped[:,0];b=mapped[:,2]-mapped[:,0];det=a[:,0]*b[:,1]-a[:,1]*b[:,0]
    require(area.min()>1e-8 and abs(det).min()>1e-12,'Saved geometry or UV triangle degenerates')
    radius=float(np.linalg.norm(p[:,:2],axis=1).max());old_radius=float(np.linalg.norm(source['positionsCm'][:,:2],axis=1).max())
    require(radius<=old_radius+1e-6,'Actual allLOD radial crown grew')
    require(p[:,2].min()>=source['positionsCm'][:,2].min()-1e-6 and p[:,2].max()<=source['positionsCm'][:,2].max()+1e-6,'Actual source ground/vertical envelope escaped')
    return{'minimumTriangleAreaCm2':float(area.min()),'minimumUvTriangleArea':float(abs(det).min()/2),
           'maxNormalUnitError':float(np.max(abs(np.linalg.norm(n,axis=1)-1))),
           'maxTangentUnitError':float(np.max(abs(np.linalg.norm(t,axis=1)-1))),
           'maxNormalTangentDot':float(np.max(abs(np.sum(n*t,axis=1)))),
           'actualRadiusCm':radius,'sourceCircularCapCm':old_radius,'vertices':len(p),'triangles':len(ix),
           'allVerticesWithinOldActualCircularCrownAndZEnvelope':True}


def build(out):
    require(out.is_relative_to(ROOT/'output/unreal')and not out.exists(),'Use fresh immutable arc source output')
    for p,h in [(ARC,ARC_SHA),(FOLD,FOLD_SHA),(MID,MID_SHA)]:require(sha(p)==h,'Frozen selected source changed: '+str(p))
    arc=load('r14_selected_arc_function',ARC);fold=load('r14_source_raster_utilities',FOLD)
    inputs={str(p):h for p,h in fold.PINS.items()};inputs.update({str(ARC):ARC_SHA,str(FOLD):FOLD_SHA,str(MID):MID_SHA,
                                                              str(Path(__file__).resolve()):sha(__file__)})
    recipe=read(PHOTO/'material-manifest.json')[MATERIAL]
    for row in recipe['maps'].values():inputs[row['path']]=row['sha256']
    for p,h in inputs.items():require(sha(p)==h,'Pinned source changed before execution: '+p)
    api=fold.module('r14_current_photo_decode',ROOT/'scripts/unreal/exterior-lawn-photo-variants.py')
    tangent=fold.module('r14_existing_photographic_tangent',ROOT/'scripts/unreal/exterior-lawn-tapered-photo-uv-study.py')
    _,_,_,originals=api.glb(PHOTO/'lawn-photographic-variants.glb');_,_,_,middle=api.glb(MID)
    library=read(PHOTO/'geometry-manifest.json');plan=read(DONOR/'lawn-natural-plan.json');prior=read(PHOTO/'photographic-alpha-coverage-receipt.json')
    require(plan['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}and
            plan['housePlacement']['streetSetbackMm']==plan['housePlacement']['eastSetbackMm']==3000,'Protected source frame differs')
    require(len(plan['lawnPlacements'])==102011 and len(plan['groups'])==40,'Source ordered population differs')
    meta={m['nodeName']:m for m in read(DONOR/'lawn-natural-prototypes.json')}
    records=[];masters=[];baselines={};primitive_proofs=[]
    for item in library['meshes']:
        old=item['sourceMeshId'];identity=old.replace('lawn_natural_','lawn_arc_',1)
        raw=originals[old.replace('lawn_natural_','lawn_photo_',1)+'_LOD0'];source=fold.native_record(raw)
        source.update(bladeRanges=deepcopy(meta[old+'_LOD0']['bladeRanges']),nodeName=old+'_LOD0');baselines[old+'_LOD0']=source
        near=peak_blade_mesh(source,meta[old+'_LOD0'],[0.,float(meta[old+'_LOD0']['bladeRanges'][0]['peakT']),.72,1.],identity+'_LOD0');near['level']=0;records.append(near)
        for lod,table,prefix in [(1,middle,'lawn_folded_'),(2,originals,'lawn_photo_')]:
            source_raw=table[old.replace('lawn_natural_',prefix,1)+'_LOD'+str(lod)]
            row=fold.native_record(source_raw);row.update(nodeName=identity+'_LOD'+str(lod),level=lod,sourceRaw=source_raw);records.append(row)
        masters.append({'id':identity,'sourceMeshId':old,'sourcePhotographicMeshId':item['id'],'role':'grass',
                        'placementPolicy':'explicit-only','materialKeys':[MATERIAL],'lodScreenSizes':[1,.025,.007],
                        'sourceRadialCrownCapCm':float(np.linalg.norm(source['positionsCm'][:,:2],axis=1).max()),'lods':[]})
    previous=ROOT/'output/unreal/exterior-lawn-arc-20261001-r2-study'
    previous_glb=previous/'lawn-arc.glb';previous_coverage=previous/'alpha-coverage-receipt.json'
    require(sha(previous_glb)=='8a7a1da0ab0d2d183481e0b174f200c15c9936e4be9bef51e94275adc33ff7b5' and
            sha(previous_coverage)=='c3a0312fae1a0319d36e33b7d7b57e48f940677fa1020e9d078231605a6168f1','Frozen R2 measured source changed')
    inputs[str(previous_glb)]=sha(previous_glb);inputs[str(previous_coverage)]=sha(previous_coverage)
    _,_,_,previous_saved=api.glb(previous_glb);previous_receipt=read(previous_coverage)
    out.mkdir();glb=out/'lawn-arc.glb';encode(glb,records,tangent)
    _,_,_,saved=api.glb(glb);by_name={};source_lod_records={0:{},1:{},2:{}}
    for row in records:
        raw=saved[row['nodeName']];actual=fold.native_record(raw);actual.update(nodeName=row['nodeName'],level=row['level'])
        identity,lod=row['nodeName'].rsplit('_LOD',1);source_id=identity.replace('lawn_arc_','lawn_natural_',1)
        measured=independent_frames(actual,raw,baselines[source_id+'_LOD0'])
        if row['level']>0:
            require(set(raw)==set(row['sourceRaw'])and all(raw[k].tobytes()==row['sourceRaw'][k].tobytes()for k in raw),
                    'Exact selected mid/far source attribute/index bytes changed')
            require(all(raw[k].tobytes()==previous_saved[row['nodeName']][k].tobytes()for k in raw),
                    'Transferred ROI mid/far source differs from actual measured R2 geometry')
            measured['allSelectedSourceAttributeAndIndexBytesExact']=True
            measured['allMeasuredR2AttributeAndIndexBytesExact']=True
        else:
            actual['bladeRanges']=row['bladeRanges']
            for blade,old in zip(row['bladeRanges'],meta[source_id+'_LOD0']['bladeRanges']):
                p=actual['positionsCm'][blade['vertexOffset']:blade['vertexOffset']+blade['vertexCount']]
                q=baselines[source_id+'_LOD0']['positionsCm'][old['vertexOffset']:old['vertexOffset']+5]
                require(np.array_equal(p[:2],q[:2])and np.array_equal(p[-1],q[-1]),'Selected original root/tip positions changed')
        by_name[row['nodeName']]=actual;source_lod_records[row['level']][source_id+'_LOD0']=actual
        primitive_proofs.append({'node':row['nodeName'],'lod':row['level'],**measured})
        master=next(m for m in masters if m['id']==identity)
        master['lods'].append({'level':row['level'],'nodeName':row['nodeName'],'vertices':len(actual['positionsCm']),
                              'triangles':len(actual['triangles']),'expectedBoundsCm':{'min':actual['positionsCm'].min(0).tolist(),'max':actual['positionsCm'].max(0).tolist()},
                              'radialEnvelopeCm':measured['actualRadiusCm'],'leaves':48 if 'edge_'in identity else 64})
    lookup={m['sourceMeshId']:m for m in masters}
    budgets=[sum(len(g['instances'])*lookup[g['meshId']]['lods'][lod]['triangles']for g in plan['groups'])for lod in range(3)]
    require(budgets==[55713600,19914778,18571200],'Measured population triangles differ from declared proposal')
    alpha=np.asarray(Image.open(recipe['maps']['alpha']['path']),dtype=float)/65535
    results={'physicalCoverage':[],'boundaryCoverage':[]}
    for lod in range(3):
        for kind,windows,boundary in [('physicalCoverage',prior['physicalCoverage']['windows'],False),('boundaryCoverage',prior['boundaryCoverage']['windows'],True)]:
            for index,window in enumerate(windows):
                if lod>0:
                    matching=[r for r in previous_receipt[kind]if r['lod']==lod]
                    result=deepcopy(matching[index]);result['byteIdenticalMeasuredGeometryReceipt']=pin(previous_coverage)
                    result['coverageRasterFreshThisExecution']=False;results[kind].append(result)
                    continue
                print(json.dumps({'phase':'actual-distinct-LOD-alpha-raster','lod':lod,'roi':window.get('boundaryId',window.get('centerCm'))}),flush=True)
                opaque,photo,count,stats=api.alpha_footprint(source_lod_records[lod],plan['lawnPlacements'],window,alpha,boundary)
                metrics=api.boundary_metrics(photo)if boundary else api.interior_metrics(photo)
                met=all(b['physicalCoverFraction']>threshold for b,threshold in zip(metrics['boundaryBands'],(.12,.40,.50)))if boundary else(metrics['projectedCoverage']>=.75 and metrics['tenCmBinCoverageP10']>=.55 and metrics['bareTenCmBins']==0)
                result={k:v for k,v in window.items()if k not in('lods','intersectingInstances')};result.update(lod=lod,intersectingInstances=count,
                            **metrics,opaqueCoverage=float(opaque.mean()),studyTargetsMet=met,alphaSampleStats=stats,currentPhotoBaseline=window['lods'][lod],coverageRasterFreshThisExecution=True)
                results[kind].append(result)
                filename=('boundary_'+window['boundaryId']if boundary else'coverage_'+str(index))+'_LOD'+str(lod)+'.png'
                Image.fromarray(np.uint8(photo)*255).resize((600,600)if not boundary else(240,600),Image.Resampling.BOX).save(out/filename)
    all_original_met=all(row['studyTargetsMet']for rows in results.values()for row in rows)
    for m in masters:m.update(glbPath=str(glb),glbSha256=sha(glb),heightCm=max(q['expectedBoundsCm']['max'][2]for q in m['lods']))
    common={'schemaVersion':1,'owner':OWNER,'generatorSha256':sha(__file__),'activeDesign':plan['activeDesign'],'housePlacement':plan['housePlacement'],
            'sourceSceneSha256':plan['sourceSceneSha256'],'sourceObjSha256':plan['sourceObjSha256'],'sourcePlacementPlan':pin(DONOR/'lawn-natural-plan.json'),
            'inputFiles':inputs,'nativeVisualAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'integrationAuthorized':False}
    write(out/'geometry-manifest.json',{'schema':1,**common,'units':'metres','axes':'glTF Y-up; Unreal native=[100*x,100*z,100*y]',
                                      'status':'SOURCE_ONLY_ARC_GEOMETRY_NATIVE_PENDING','meshes':masters})
    write(out/'material-manifest.json',{MATERIAL:recipe})
    write(out/'geometry-validation.json',{**common,'status':'MEASURED_ACTUAL_SAVED_ARC_MID_FAR_ATTRIBUTES_SOURCE_ONLY',
          'masters':20,'lods':60,'primitiveMeasurements':primitive_proofs,'normalsTangentsAndUvTopologyMeasuredFromActualSavedGlb':True,'actualSourcePeakShoulderCornersPreserved':True,
          'midAndFarAllAttributesAndIndicesMatchExactSelectedFrozenSourceBytes':True,'fullCircularSourceCrownsAndOriginalNearRootTipPointsPreserved':True,
          'noCollisionWpoDensityOrPlacementChanges':True,'populationTriangleBudgetByLod':budgets,'formalUnitTestsRun':0})
    write(out/'alpha-coverage-receipt.json',{**common,'status':'PASS_ALL_ORIGINAL_SOURCE_ALPHA_TARGETS_NATIVE_PENDING'if all_original_met else'FAILED_ORIGINAL_SOURCE_ALPHA_TARGETS_NO_NATIVE_INTEGRATION',
          'criteria':{'physical':prior['physicalCoverage']['criteria'],'boundary':prior['boundaryCoverage']['criteria']},
          'pixelSizeMm':.25,'alphaClipValue':.333,'photographicAlphaPixelsUnmodified':True,
          'all18DistinctLodRoisMeasuredOrByteIdentical':True,'freshActualLodRoisRastered':6,'byteIdenticalMeasuredCoverageMetricsTransferred':12,'transferredMetricsSource':pin(previous_coverage),'allOriginalTargetsMet':all_original_met,**results,
          'method':'Actual exported float32 triangles, source native yaw/scale, old0.25mm conservative Pillow footprint and actual2048bilinear alpha. Native MSAA/TAA/mips/SSS not simulated.',
          'nativeJobsRun':0,'formalUnitTestsRun':0})
    # Compare actual current, selected close geometry and original cheaper mid.
    near=by_name['lawn_arc_0_3_LOD0'];mid=by_name['lawn_arc_0_3_LOD1']
    # Mid ranges differ because7 source leaves have an extra ridge vertex.
    selected=fold.selection(baselines['lawn_natural_0_3_LOD0'],meta['lawn_natural_0_3_LOD0']);offset=0;tri=0;ranges=[]
    for b in meta['lawn_natural_0_3_LOD0']['bladeRanges']:
        folded=b['bladeIndex']in selected;vc=6 if folded else 5;tc=5 if folded else 3
        ranges.append({'bladeIndex':b['bladeIndex'],'vertexOffset':offset,'vertexCount':vc,'triangleOffset':tri,'triangleCount':tc,'sourceRootCm':b['rootCm']});offset+=vc;tri+=tc
    mid['bladeRanges']=ranges
    renderer_source=inspect.getsource(arc.render_preview).replace("'Quadratic centreline9v9tri'","'Close LOD0:9tri curved leaf'").replace("'Quadratic centreline12v13tri'","'Mid LOD1:budgeted5tri folds'")
    namespace=dict(arc.__dict__);exec(compile(renderer_source,'<r14_actual_lod_preview_labels>','exec'),namespace)
    namespace['render_preview'](out,baselines['lawn_natural_0_3_LOD0'],{'three_segments':near,'four_segments':mid},meta['lawn_natural_0_3_LOD0'],recipe,fold)
    for p,h in inputs.items():require(sha(p)==h,'Pinned source changed during execution: '+p)
    with(out/'study-source.py').open('x')as f:f.write(Path(__file__).read_text())
    proposal={**common,'status':'MEASURED_ARC_PROPOSAL_SOURCE_ONLY_NATIVE_PENDING'if all_original_met else'FAILED_ORIGINAL_COVERAGE_ARC_PROPOSAL_SOURCE_ONLY_NO_GO',
              'geometryManifest':pin(out/'geometry-manifest.json'),'materialManifest':pin(out/'material-manifest.json'),
              'geometryValidation':pin(out/'geometry-validation.json'),'photographicAlphaCoverage':pin(out/'alpha-coverage-receipt.json'),
              'sourceMidPrototype':pin(MID),'sourceFarPhotographicPrototype':pin(PHOTO/'lawn-photographic-variants.glb'),
              'activeReplacementMeshMapping':{m['sourceMeshId']:m['id']for m in masters},'instances':102011,'groups':40,'masters':20,'lods':60,
              'allOrderedPlacementRootYawScaleAndExistingSourcePrivateMasksPreserved':True,'populationTriangleBudgetByLod':budgets,
              'all18OriginalAlphaTargetsMet':all_original_met,'prospectiveMaterialKey':MATERIAL,'opticalRecipeAndOriginalPixelsUnchanged':True,
              'limits':['55.714M close geometry is an explicit new cost; no native performance or selectedLOD visibility proof.','9v9tri V/arc near, adaptive6v5/5v3mid and original5v3far differ visibly; LOD transition quality is unmeasured.','Original protected source circle and endpoint constraints preserved; no botanical species or survey claim.','Original source widest shoulder corners retained; no target, placement, floor, density, alpha threshold or shader changes.','CPU diffuse/geometric normals only; photo normalDX, roughness, SSS, runtime mips and native lighting remain unverified.'],
              'formalUnitTestsRun':0,'nativeJobsRun':0,'gpuJobsRun':0}
    write(out/'lawn-arc-proposal.json',proposal)
    print(json.dumps({'proposal':str(out/'lawn-arc-proposal.json'),'sha256':sha(out/'lawn-arc-proposal.json'),
                      'budgets':budgets,'allOriginalTargetsMet':all_original_met,'coverageByLod':{str(lod):[r['projectedCoverage']for r in results['physicalCoverage']if r['lod']==lod]for lod in range(3)}}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'output/unreal/exterior-lawn-arc-20261001-r3-study')
    build(parser.parse_args().output.resolve())
