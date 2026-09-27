"""Isolated R7 brightness-only material derivative and CPU shader pixel proof."""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'output/unreal/exterior-assets-20260927-r6/material-manifest.json'
KEY='ph_periwinkle_plant'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,o):Path(p).write_text(json.dumps(o,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def linear(a):return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def srgb(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
def smooth(a):
    a=np.clip(a,0,1);return a*a*(3-2*a)
def build(output):
    output=Path(output).resolve()
    if output.exists():raise ValueError('Use a new isolated output')
    before=json.loads(SOURCE.read_text());after=copy.deepcopy(before)
    recipe=after[KEY];assert recipe['leafCalibration']['brightness']==.78
    recipe['leafCalibration']['brightness']=.60
    restored=copy.deepcopy(after);restored[KEY]['leafCalibration']['brightness']=.78
    assert restored==before
    inputs={str(SOURCE):sha(SOURCE),str(Path(__file__).resolve()):sha(__file__)}
    for s in recipe['maps'].values():
        assert sha(s['path'])==s['sha256'];inputs[s['path']]=s['sha256']
    original=recipe['leafCalibration']['sourceMaterialManifest'];assert sha(original['path'])==original['sha256'];inputs[original['path']]=original['sha256']
    source=np.asarray(Image.open(recipe['maps']['albedo']['path']).convert('RGB'),dtype=np.float32)/255
    alpha=np.asarray(Image.open(recipe['maps']['alpha']['path']).convert('L'),dtype=np.float32)/255
    scan=linear(source);chroma=(scan[:,:,1]-np.maximum(scan[:,:,0],scan[:,:,2]))/np.maximum(scan[:,:,1],.00001)
    mask=smooth((chroma-.04)/(.18-.04));opaque=alpha>=.99
    pink=opaque&(scan[:,:,0]>scan[:,:,1]*1.1)&(scan[:,:,2]>scan[:,:,1]*1.05)
    green=opaque&(mask==1);unchanged=opaque&(mask==0)
    assert pink.sum()>100 and green.sum()>100 and unchanged.sum()>100
    tests=[];previews=[]
    for rnd in (0.,.5,1.):
        variation=.94+rnd*.12;tint=(1-rnd)*np.array([.97,1.015,.96])+rnd*np.array([1.035,.985,1.015])
        color=np.clip(scan*np.array(recipe['tint'])*tint*variation*recipe['albedoScale'],0,1)
        luma=color@np.array([.2126,.7152,.0722]);sat=luma[:,:,None]*(1-.88)+color*.88
        def calibrated(brightness):return color*(1-mask[:,:,None])+sat*brightness*mask[:,:,None]
        old,new=calibrated(.78),calibrated(.60)
        delta=np.abs(new-old)
        assert np.max(delta[pink])==0 and np.max(delta[unchanged])==0
        ratio=(new@np.array([.2126,.7152,.0722]))[green]/(old@np.array([.2126,.7152,.0722]))[green]
        assert np.max(np.abs(ratio-.60/.78))<1e-6
        tests.append({'instanceRandom':rnd,'opaquePinkPixels':int(pink.sum()),'pinkMaxChannelDelta':float(delta[pink].max()),'unchangedNonGreenPixels':int(unchanged.sum()),'nonGreenMaxChannelDelta':float(delta[unchanged].max()),'fullySelectedLeafPixels':int(green.sum()),'selectedLeafLumaRatioRange':[float(ratio.min()),float(ratio.max())]})
        if rnd==.5:
            for image in (old,new):
                visible=np.clip(srgb(image),0,1)*alpha[:,:,None]+.22*(1-alpha[:,:,None])
                previews.append(Image.fromarray(np.uint8(np.round(visible*255))).resize((700,700),Image.Resampling.LANCZOS))
    output.mkdir(parents=True);write(output/'material-manifest.json',after)
    canvas=Image.new('RGB',(1400,805),'#f7f6f2');draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    for i,picture in enumerate(previews):
        draw.text((i*700+12,14),f'CPU shader BaseColor / leaf brightness {(.78,.60)[i]:.2f}',font=font,fill='#222222');canvas.paste(picture,(i*700,50))
    draw.text((12,760),'NOT A NATIVE RENDER. Only green-chroma selected leaves change; pink flowers, alpha, UV and source image bytes are unchanged.',font=small,fill='#222222')
    draw.text((12,782),'Source: Poly Haven periwinkle_plant / Amal Kumar / CC0. Artist calibration, not measured plant reflectance.',font=small,fill='#222222');canvas.save(output/'cpu-leaf-brightness-comparison.png')
    proof={'schemaVersion':1,'status':'CPU_SHADER_PROOF_NOT_NATIVE_ACCEPTANCE','inputFiles':inputs,'outputMaterialManifest':{'path':str(output/'material-manifest.json'),'sha256':sha(output/'material-manifest.json')},'onlyChangedJsonPointer':'/ph_periwinkle_plant/leafCalibration/brightness','from':.78,'to':.60,'allOtherRecipeValuesEqual':True,'materialCount':len(after),'originalMapsUnmodified':True,'sourceRecipeAndR4ManifestUnmodified':True,'selector':'linear source green chroma, smoothstep .04/.18','tests':tests,'limitations':['CPU proof checks the exact BaseColor calibration equations at instanceRandom 0,.5,1. It does not prove native exposure, shading or perceived realism.','Original R5 leafCalibration purpose remains byte-identical because this derivative changes only the authorized brightness number. This receipt describes R7 intent.']}
    write(output/'leaf-calibration-proof.json',proof)
    print(json.dumps({'manifest':proof['outputMaterialManifest'],'tests':tests},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);build(p.parse_args().output)
