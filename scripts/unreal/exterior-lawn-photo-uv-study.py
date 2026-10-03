"""Isolated four-leaf photographic UV study; no native material/scene changes.

The immutable PH source island and cambered GLB are decoded independently.
The CPU plate is a diffuse-colour illustration, not Unreal PBR/SSS proof.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/unreal/exterior-lawn-photo-uv-20261001-r1-study'
PH = ROOT / 'output/unreal/exterior-assets-20260926-r1/grass_medium_02'
CAMBER = ROOT / 'output/unreal/exterior-lawn-camber-20261001-r1-study'
GLB = ROOT / 'output/unreal/exterior-assets-20260926-r1/glb/grass_medium_02.glb'
SOURCE_NODE = 'PH_grass_medium_02_a_LOD0'
PINS = {
    str(GLB): 'c09551da5f8138fc84fe50a05d6d8d4ce3cd6dd504e32cdc10ba5218b6dd386a',
    str(PH / 'info.json'): '52cef91e7823b20df8ec8c7ff015f3c0717820652c9790e72914136b63816dd2',
    str(PH / 'files-api.json'): '3e5e5b4b2ca39ac40a7acf9171a92557b819476adc4c1a3680d31b0b99a3b3af',
    str(PH / 'textures/grass_medium_02_diff_2k.png'): '04f7de9ee8e3fccbda48c6ef715b8bd30aa707c1605add5eb679fc6e7acb7d38',
    str(PH / 'textures/grass_medium_02_nor_dx_2k.png'): 'de5d3143fb993cbe86123ae28144fe9936ecc93ec1ebc9af7034da63abc2dbfc',
    str(PH / 'textures/grass_medium_02_rough_2k.png'): '4d42a3ee935c1aaeecfacd1d286a25075293990686ed949f0712d9ae039d0e91',
    str(PH / 'textures/grass_medium_02_alpha_2k.png'): 'c96abf8da86aa750ff6425b8ded78aa98cf61858834e3557ad2dcc5348359337',
    str(ROOT / 'output/unreal/exterior-alpha-20260926-r4/ph_grass_medium_02_diff_rgb_dilated.png'): '232ced222dbfef15cec3faaa39d86a6227e4ff2f9b7eddc19119693d66ddc0fe',
    str(CAMBER / 'cambered.glb'): '72614f72bb87ff1dca08f07fbc27880e3a92ae97749c828b2ff54f407b1ce3e9',
    str(CAMBER / 'camber-prototype.json'): 'a3fd1a57409039d4e73d8d2700ac107fe3874ae4052518614d9fa9b362d0e221',
    str(CAMBER / 'closure.json'): '3748734aca71fa6fa7cc8e22922d802ac57b764205a7c0ac8bc5f7bde7b0836a',
    str(ROOT / 'output/unreal/exterior-20261001-r11/exterior-import-report.json'): '6608bfdada21b9de8540dfead615a668a60cd1a2ff6cceab6c8c0eded0cd5e21',
}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok, message):
    if not ok: raise RuntimeError(message)
def write(path, value):
    with path.open('x') as stream: json.dump(value, stream, indent=2); stream.write('\n')


def decode(path):
    raw = Path(path).read_bytes()
    require(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Invalid source GLB')
    size, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a, 'Source JSON chunk differs')
    doc = json.loads(raw[20:20+size]); binary = raw[28+size:]
    def accessor(index):
        a = doc['accessors'][index]; view = doc['bufferViews'][a['bufferView']]
        width = {'SCALAR':1, 'VEC2':2, 'VEC3':3, 'VEC4':4}[a['type']]
        dtype = {5126:'<f4', 5123:'<u2', 5125:'<u4'}[a['componentType']]
        return np.frombuffer(binary, dtype, a['count']*width,
                             view.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width).copy()
    rows = {}
    for node in doc['nodes']:
        primitive = doc['meshes'][node['mesh']]['primitives'][0]
        rows[node['name']] = {k: accessor(v) for k,v in primitive['attributes'].items()}
        rows[node['name']]['indices'] = accessor(primitive['indices']).reshape(-1,3)
    return rows


def components(row):
    parent = list(range(len(row['POSITION'])))
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for a,b,c in row['indices']:
        parent[find(int(b))] = find(int(a)); parent[find(int(c))] = find(int(a))
    groups = {}
    for face in row['indices']: groups.setdefault(find(int(face[0])), []).append(face)
    return {key: np.asarray(faces) for key,faces in groups.items()}


def sample(image, uv):
    """GPU-like normalized UV pixel centres; direct V matches all source cards."""
    h,w = image.shape[:2]; p = np.asarray(uv)*[w,h]-.5
    p = np.clip(p, [0,0], [w-1,h-1]); lo = np.floor(p).astype(int); hi = np.minimum(lo+1,[w-1,h-1])
    f = p-lo
    if image.ndim == 3: f = f[...,None,:]
    a = image[lo[...,1],lo[...,0]]; b = image[lo[...,1],hi[...,0]]
    c = image[hi[...,1],lo[...,0]]; d = image[hi[...,1],hi[...,0]]
    return (a*(1-f[...,0])+b*f[...,0])*(1-f[...,1])+(c*(1-f[...,0])+d*f[...,0])*f[...,1]


def srgb_to_linear(rgb): return np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)


def render(row, uv, texture, alpha, recipe, mode, mean):
    """Identical actual camber vertices/light in all panels; albedo-only CPU."""
    width,height = 660,650; image = np.full((height,width,3), [.19,.19,.17]); depth = np.full((height,width), -np.inf)
    p,n,ix = row['p'],row['n'],row['ix']; camera=np.array([.22,.92,.42]);camera/=np.linalg.norm(camera)
    right=np.array([camera[1],-camera[0],0.]);right/=np.linalg.norm(right);up=np.cross(right,camera)
    light=np.array([-.4,-.65,1.]);light/=np.linalg.norm(light)
    screen=np.column_stack([p@right*100+width/2,height*.82-p@up*100,p@camera])
    stats = {'pixels':0,'alphaRejected':0,'linearAlbedoSum':[0.,0.,0.]}
    for face in ix:
        q=screen[face];lo=np.maximum(np.floor(q[:,:2].min(0)).astype(int),[0,0]);hi=np.minimum(np.ceil(q[:,:2].max(0)).astype(int),[width-1,height-1])
        if np.any(hi<lo):continue
        x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
        den=(q[1,1]-q[2,1])*(q[0,0]-q[2,0])+(q[2,0]-q[1,0])*(q[0,1]-q[2,1])
        if abs(den)<1e-12:continue
        a=((q[1,1]-q[2,1])*(x-q[2,0])+(q[2,0]-q[1,0])*(y-q[2,1]))/den
        b=((q[2,1]-q[0,1])*(x-q[2,0])+(q[0,0]-q[2,0])*(y-q[2,1]))/den;weights=np.stack([a,b,1-a-b],-1)
        z=weights@q[:,2];old=depth[lo[1]:hi[1]+1,lo[0]:hi[0]+1];inside=(weights.min(-1)>=-1e-8)&(z>old)
        photo_uv=weights@uv[face];mask=sample(alpha,photo_uv)>=recipe['opacityMaskClipValue']
        if mode=='photo':
            stats['alphaRejected']+=int((inside&~mask).sum());inside&=mask
            albedo=srgb_to_linear(sample(texture,photo_uv))*recipe['albedoScale']
        elif mode=='photo_mean':albedo=np.broadcast_to(mean,weights.shape)
        else:albedo=np.broadcast_to(np.array([.04,.075,.025]),weights.shape)
        normal=weights@n[face];normal/=np.maximum(np.linalg.norm(normal,axis=-1,keepdims=True),1e-12)
        brightness=.25+1.85*np.abs(normal@light)
        rgb=np.clip(albedo*brightness[...,None],0,1);region=image[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        region[inside]=rgb[inside];old[inside]=z[inside]
        stats['pixels']+=int(inside.sum());stats['linearAlbedoSum']=(np.array(stats['linearAlbedoSum'])+albedo[inside].sum(0)).tolist()
    result=np.where(image<=.0031308,image*12.92,1.055*image**(1/2.4)-.055)
    return Image.fromarray(np.clip(result*255,0,255).astype('uint8')),stats


def build():
    require(not OUT.exists(), 'Use a fresh immutable output directory')
    inputs = dict(PINS); inputs[str(Path(__file__).resolve())]=sha(__file__)
    for path,expected in inputs.items(): require(sha(path)==expected, 'Source changed: '+path)
    source = decode(GLB); require(len(source)==15, 'All15 source nodes required')
    files=json.loads((PH/'files-api.json').read_text()); provider={}
    for role,name in [('Diffuse','diff'),('nor_dx','nor_dx'),('Rough','rough'),('Alpha','alpha')]:
        path=PH/f'textures/grass_medium_02_{name}_2k.png';entry=files[role]['2k']['png'];raw=path.read_bytes()
        require(len(raw)==entry['size'] and hashlib.md5(raw).hexdigest()==entry['md5'], 'Official provider bytes differ')
        provider[role]={**entry,'path':str(path),'sha256':sha(path),'sourcePixelsUnmodified':True,'pngBitDepth':raw[24]}
    report=json.loads(Path(next(p for p in PINS if p.endswith('exterior-import-report.json'))).read_text())
    recipe=copy.deepcopy(report['materials']['materials']['ph_grass_medium_02']['recipe'])
    require(recipe['sourceUrl']=='https://polyhaven.com/a/grass_medium_02' and recipe['license']=='CC0-1.0'
            and recipe['maps']['albedo']['sha256']==PINS[str(ROOT/'output/unreal/exterior-alpha-20260926-r4/ph_grass_medium_02_diff_rgb_dilated.png')], 'Consumed photo recipe differs')
    texture=np.asarray(Image.open(recipe['maps']['albedo']['path']),dtype=float)/255
    alpha=np.asarray(Image.open(recipe['maps']['alpha']['path']),dtype=float)/65535
    require(texture.shape==(2048,2048,3) and alpha.shape==(2048,2048), 'Exact source map dimensions differ')
    # Source-connected horizontal olive-green leaf, not an arbitrary rectangle.
    island_faces=components(source[SOURCE_NODE])[25];island_ids=np.unique(island_faces)
    require((len(island_ids),len(island_faces))==(39,45), 'Exact connected source leaf differs')
    source_uv=source[SOURCE_NODE]['TEXCOORD_0'];domain=unary_union([Polygon(source_uv[f]) for f in island_faces])
    # Exclude the photographed curled distal hook; retain one coherent leaf body.
    # This is an explicitly disclosed artist UV choice, not a botanical survey.
    axis=[.768,.352];stations=np.linspace(0,1,257);strip=[]
    for t in stations:
        u=axis[0]+(axis[1]-axis[0])*t;line=domain.intersection(LineString([(u,0),(u,1)]))
        require(line.geom_type=='LineString' and not line.is_empty,'Leaf body source UV is not continuous')
        v0,v1=line.bounds[1],line.bounds[3]
        # Original photographic edge alpha is retained with a half-texel margin.
        strip.append([u,v0-.5/2048,v1+.5/2048])
    strip=np.asarray(strip)
    def remap(normalized):
        t=normalized[:,1];u=axis[0]+(axis[1]-axis[0])*t
        low=np.interp(t,stations,strip[:,1]);high=np.interp(t,stations,strip[:,2])
        return np.column_stack([u,low+(high-low)*normalized[:,0]])
    camber=decode(CAMBER/'cambered.glb')['lawn_natural_0_3_LOD0'];meta=json.loads((CAMBER/'camber-prototype.json').read_text())
    require(len(camber['POSITION'])==1344 and len(camber['indices'])==1792,'Frozen64leaf camber differs')
    p=camber['POSITION'][:,[0,2,1]].astype(float)*100;n=camber['NORMAL'][:,[0,2,1]].astype(float)
    indices=camber['indices'][:,[0,2,1]].astype('int64');normalized=camber['TEXCOORD_0'].astype(float);few={'p':[],'n':[],'ix':[]};uv=[];leaf_rows=[]
    for slot,leaf in enumerate((1,5,9,13)):
        b=meta['bladeRanges'][leaf];start=b['vertexOffset'];stop=start+b['vertexCount'];face_start=b['triangleOffset']
        require(b['vertexCount']==21 and b['triangleCount']==28,'Camber leaf topology differs')
        positions=p[start:stop].copy();positions[:,:2]+=np.array([(slot-1.5)*1.25,0])-np.asarray(b['rootCm'])
        offset=len(few['p'])-start;few['p'].extend(positions);few['n'].extend(n[start:stop]);few['ix'].extend(indices[face_start:face_start+28]+offset)
        mapped=remap(normalized[start:stop]);uv.extend(mapped);leaf_rows.append({'leafIndex':leaf,'seed':b['seed'],'normalizedUv':normalized[start:stop].tolist(),'photographicUv':mapped.tolist()})
    few={k:np.asarray(v) for k,v in few.items()};uv=np.asarray(uv)
    orientation=[]
    for name,row in source.items():
        centers=row['TEXCOORD_0'][row['indices']].mean(1);direct=sample(alpha,centers);flipped=centers.copy();flipped[:,1]=1-flipped[:,1]
        orientation.append({'node':name,'vertices':len(row['POSITION']),'triangles':len(row['indices']),
                            'uvBounds':[row['TEXCOORD_0'].min(0).tolist(),row['TEXCOORD_0'].max(0).tolist()],
                            'directAlphaTriangleCenterMean':float(direct.mean()),'flippedAlphaTriangleCenterMean':float(sample(alpha,flipped).mean()),
                            'connectedComponents':len(components(row))})
    require(all(r['directAlphaTriangleCenterMean']>r['flippedAlphaTriangleCenterMean'] for r in orientation),'Source UV orientation ambiguous')
    alpha_samples=[];rgb_samples=[]
    for face in few['ix']:
        for i in range(1,16):
            for j in range(1,16-i):
                bary=np.array([i,j,16-i-j])/16;point=bary@uv[face]
                alpha_samples.append(float(sample(alpha,point)));rgb_samples.append(sample(texture,point))
    samples=np.asarray(alpha_samples);rgb=np.asarray(rgb_samples)
    mean_control=srgb_to_linear(rgb[samples>.99]).mean(0)*recipe['albedoScale']
    OUT.mkdir();plate=Image.new('RGB',(1980,760),'#eeebe3');draw=ImageDraw.Draw(plate);stats={}
    for col,(label,mode) in enumerate([('R11 solid RGB response / same actual camber','solid'),('Uniform mean PH colour control / same camber','photo_mean'),('Real PH leaf colour + original alpha / same camber','photo')]):
        image,stats[mode]=render(few,uv,texture,alpha,recipe,mode,mean_control);plate.paste(image,(col*660,55));draw.text((col*660+10,20),label,fill='#202820')
    draw.text((12,716),'Four exact frozen camber leaves, unchanged21vertices/28triangles each. Rearranged roots only for display; same camera, light, normals and geometry in all panels.',fill='#202820')
    draw.text((12,738),'CPU diffuse-albedo illustration only: original roughness/normal maps pinned but not shaded; no Unreal subsurface, shadows, mips, performance or photorealism acceptance.',fill='#202820')
    image_path=OUT/'four-leaf-photographic-comparison.png';plate.save(image_path)
    record={'schemaVersion':1,'owner':str(Path(__file__).relative_to(ROOT)),'status':'SOURCE_ONLY_FOUR_LEAF_COHERENT_PHOTOGRAPHIC_UV_STUDY_NATIVE_PENDING',
        'inputFiles':inputs,'sourceMapsProviderProof':provider,'sourcePage':recipe['sourceUrl'],'license':recipe['license'],
        'sourceConnectedUVIsland':{'glb':str(GLB),'sha256':PINS[str(GLB)],'node':SOURCE_NODE,'componentRootVertex':25,'sourceVertexIndices':island_ids.tolist(),'vertices':39,'triangles':45,
                                'uvBounds':[source_uv[island_ids].min(0).tolist(),source_uv[island_ids].max(0).tolist()],
                                'originalUv0':source_uv[island_ids].tolist(),'originalTriangles':island_faces.tolist(),'artistBodyAxisU':axis,'photographedCurledTipExcluded':True},
        'leafUvMapping':{'mode':'normalizedcamber[u,t] -> original source-connected horizontal leaf body; measured source UV silhouette edges, direct V', 'stripStations':strip.tolist(),'leaves':leaf_rows},
        'all15SourceNodeUvAudit':orientation,'sourceGeometry':{'camberGlb':str(CAMBER/'cambered.glb'),'sha256':PINS[str(CAMBER/'cambered.glb')],'selectedLeafIndices':[1,5,9,13],
                                               'vertices':84,'triangles':112,'sameGeometryCameraNormalsAndLightAllPanels':True,'sourceLeavesGeometryUnchanged':True,'rearrangedRootsForDisplayOnly':True,'noPopulationOrDomainClaims':True},
        'photoRecipeUnchanged':recipe,'prospectiveShader':'Reuse existing PH foliage graph/maps in a distinct future few-leaf prototype; replace normalized UV0 only. No new global grass arrays or global recolouring.',
        'sampledPhotographicPixels':{'barycentricSampleCount':len(samples),'alphaAboveClipFraction':float((samples>=recipe['opacityMaskClipValue']).mean()),'alphaMean':float(samples.mean()),'srgbMean':rgb.mean(0).tolist(),'srgbStd':rgb.std(0).tolist()},
        'cpuPanelStatistics':stats,'matchedUniformPhotoControlLinearRGB':mean_control.tolist(),'image':{'path':str(image_path),'sha256':sha(image_path),'dimensions':[1980,760]},
        'limitations':['Existing decoded source PH albedo is the already consumed8bit nearest-opaque RGB padding derivative, not a new provider16bit import. Original provider diffuse/normal/roughness/alpha remain byte-exact and MD5-verified.',
                       'Only four leaves of one frozen camber master; no full lawn/density/coverage or spatial integration claim.',
                       'Three-panel albedo controls are CPU Lambert illustrations; normalDX/roughness source maps are pinned but not interpreted as a native tangent-space PBR shader.',
                       'Same source island repeats across these four comparison leaves; native texture repetition, alpha mip coverage and SSS require a separate future native prototype review.'],
        'preservedPriorAttempt':{'source':'output/unreal/exterior-lawn-photo-uv-attempts-20261001-r1/attempt1/source.py','log':'output/unreal/exterior-lawn-photo-uv-attempts-20261001-r1/attempt1/run.log','failure':'uint32 original indices rejected negative per-leaf index offset before any final study output was created; corrected by signedint64 local indexing.'},'nativeJobsRun':0,'nativeShaderAccepted':False,'nativeVisualAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'artistInterpretation':True,'speciesOrScannerClaim':False}
    for path,expected in inputs.items():require(sha(path)==expected,'Source changed during study: '+path)
    record['allInputHashesUnchangedAfterExecution']=True
    write(OUT/'study.json',record);print(json.dumps({'study':str(OUT/'study.json'),'sha256':sha(OUT/'study.json'),'image':str(image_path),'alphaClipFraction':record['sampledPhotographicPixels']['alphaAboveClipFraction']}))


if __name__=='__main__':build()
