"""Fresh framing-only closeup of the immutable four-leaf photo UV study.

Reuses its exact CPU renderer; camera scale/centre alone changes to fit all leaves.
No native jobs, shader edits, photographic pixel edits or population proposals.
"""
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/unreal/exterior-lawn-photo-uv-20261001-r2-study'
PRIOR=ROOT/'output/unreal/exterior-lawn-photo-uv-20261001-r1-study/study.json'
PRIOR_SHA='6201fe71d0463a4a44722ea0a4fb44bac8b1ba9794371586ad5704a39b93dae5'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    assert not OUT.exists() and sha(PRIOR)==PRIOR_SHA
    old=json.loads(PRIOR.read_text());inputs=dict(old['inputFiles']);inputs[str(PRIOR)]=PRIOR_SHA;inputs[str(Path(__file__).resolve())]=sha(__file__)
    for path,expected in inputs.items():assert sha(path)==expected,path
    source=ROOT/'scripts/unreal/exterior-lawn-photo-uv-study.py'
    spec=importlib.util.spec_from_file_location('frozen_coherent_uv_render',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    row=m.decode(m.CAMBER/'cambered.glb')['lawn_natural_0_3_LOD0'];meta=json.loads((m.CAMBER/'camber-prototype.json').read_text())
    p=row['POSITION'][:,[0,2,1]].astype(float)*100;n=row['NORMAL'][:,[0,2,1]].astype(float);ix=row['indices'][:,[0,2,1]].astype('int64')
    few={'p':[],'n':[],'ix':[]};uv=[];normalized=[];uv1=[]
    for slot,leaf in enumerate((1,5,9,13)):
        b=meta['bladeRanges'][leaf];start=b['vertexOffset'];stop=start+b['vertexCount'];offset=len(few['p'])-start
        positions=p[start:stop].copy();positions[:,:2]+=np.array([(slot-1.5)*1.25,0])-np.asarray(b['rootCm'])
        few['p'].extend(positions);few['n'].extend(n[start:stop]);few['ix'].extend(ix[b['triangleOffset']:b['triangleOffset']+28]+offset)
        uv.extend(old['leafUvMapping']['leaves'][slot]['photographicUv']);normalized.extend(old['leafUvMapping']['leaves'][slot]['normalizedUv']);uv1.extend(row['TEXCOORD_1'][start:stop])
    few={k:np.asarray(v) for k,v in few.items()};uv=np.asarray(uv);assert len(few['p'])==84 and len(few['ix'])==112
    recipe=old['photoRecipeUnchanged'];texture=np.asarray(Image.open(recipe['maps']['albedo']['path']),dtype=float)/255
    alpha=np.asarray(Image.open(recipe['maps']['alpha']['path']),dtype=float)/65535
    # Reuse every sampling/shading operation; replace the single screen-frame line.
    original=inspect.getsource(m.render)
    old_frame='screen=np.column_stack([p@right*100+width/2,height*.82-p@up*100,p@camera])'
    new_frame='''sx=p@right;sy=p@up;view_scale=min((width-90)/np.ptp(sx),(height-110)/np.ptp(sy))
    screen=np.column_stack([(sx-(sx.min()+sx.max())/2)*view_scale+width/2,height-55-(sy-sy.min())*view_scale,p@camera])'''
    assert original.count(old_frame)==1
    framed=original.replace(old_frame,new_frame);namespace=dict(m.__dict__);exec(compile(framed,'<framing-only-coherent-uv-cpu>','exec'),namespace)
    OUT.mkdir();plate=Image.new('RGB',(1980,760),'#eeebe3');draw=ImageDraw.Draw(plate);stats={}
    for col,(label,mode) in enumerate([('Solid authored RGB / identical decoded camber','solid'),('Uniform matched PH mean / identical camber','photo_mean'),('Original PH photo colour + alpha / identical camber','photo')]):
        image,stats[mode]=namespace['render'](few,uv,texture,alpha,recipe,mode,np.asarray(old['matchedUniformPhotoControlLinearRGB']))
        plate.paste(image,(col*660,55));draw.text((col*660+10,20),label,fill='#202820')
    draw.text((12,716),'Same four21vertex/28triangle leaves, unchanged source normals/geometry; same fitted camera/light. Original photograph colour differences, veins, blemishes and alpha edge are retained.',fill='#202820')
    draw.text((12,738),'Source-only CPU diffuse comparison: photo normalDX/roughness pinned but not shaded. No Unreal PBR/SSS/mips/native shadows/performance or full lawn coverage proof.',fill='#202820')
    image=OUT/'four-leaf-photographic-closeup.png';plate.save(image)
    geometry={'positionsCm':few['p'].tolist(),'normals':few['n'].tolist(),'indices':few['ix'].tolist(),'photographicUv0':uv.tolist(),'originalNormalizedUv0':normalized,'originalUv1':np.asarray(uv1).tolist(),
              'selectedLeafIndices':[1,5,9,13],'sourceLocalRootRearrangementForDisplayOnly':True,'vertices':84,'triangles':112,'sourceGeometryUnchanged':True}
    with (OUT/'four-leaf-uv-prototype.json').open('x') as stream:json.dump(geometry,stream,indent=2);stream.write('\n')
    with (OUT/'renderer-framing-only.py').open('x') as stream:stream.write(framed)
    source_copy=OUT/'source.py'
    with source_copy.open('x') as stream:stream.write(Path(__file__).read_text())
    for path,expected in inputs.items():assert sha(path)==expected,path
    receipt={'schemaVersion':1,'status':'FROZEN_SOURCE_ONLY_MATCHED_FOUR_LEAF_PHOTOGRAPHIC_UV_CLOSEUP_NATIVE_PENDING','owner':str(Path(__file__).relative_to(ROOT)),
             'inputFiles':inputs,'derivedFrom':{'path':str(PRIOR),'sha256':PRIOR_SHA},'sourceConnectedUVIsland':old['sourceConnectedUVIsland'],'sourceRecipe':recipe,
             'sourceMapsProviderProof':old['sourceMapsProviderProof'],'all15SourceNodeUvAudit':old['all15SourceNodeUvAudit'],
             'sourceGeometry':old['sourceGeometry'],'leafUvMapping':old['leafUvMapping'],'photographicSampleProof':old['sampledPhotographicPixels'],
             'geometry':{'path':str(OUT/'four-leaf-uv-prototype.json'),'sha256':sha(OUT/'four-leaf-uv-prototype.json'),'vertices':84,'triangles':112},
             'image':{'path':str(image),'sha256':sha(image),'dimensions':[1980,760]},'cpuPanelStatistics':stats,'cameraFramingOnlyChangeFromR1':True,
             'renderSource':{'path':str(OUT/'renderer-framing-only.py'),'sha256':sha(OUT/'renderer-framing-only.py')},'sourceCopy':{'path':str(source_copy),'sha256':sha(source_copy)},
             'allInputHashesUnchangedBeforeAndAfter':True,'licensing':'Existing PH CC0-1.0 photograph and source UVs; authored camber/UV transport, no scanner/species/survey claim.',
             'prospectiveShader':old['prospectiveShader'],'limitations':old['limitations'],
             'nativeJobsRun':0,'nativeShaderAccepted':False,'nativeVisualAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False}
    with (OUT/'closure.json').open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    print(json.dumps({'closure':str(OUT/'closure.json'),'sha256':sha(OUT/'closure.json'),'image':str(image),'imageSha256':sha(image),'sourceSha256':sha(__file__)}))


if __name__=='__main__':build()
