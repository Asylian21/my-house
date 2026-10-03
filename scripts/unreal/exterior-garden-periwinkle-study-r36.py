"""Source-only whole-original Periwinkle replacement of384 R34 low stars.

No Unreal, downloads or original-byte edits. All six original complete models
are kept in one GLB with the original BIN and accessor/attribute bytes exact;
only provider display translations and the external buffer URI are removed.
Contact is preserved by an explicit new-instance vertical bottom offset.
"""
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw
import shapely
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-periwinkle-study-r36.py'
OUT = ROOT/'output/unreal/exterior-garden-periwinkle-20261002-r36-source-study'
ASSETS = ROOT/'output/unreal/exterior-ph-periwinkle-reference-20261002-r1'
BASE = ROOT/'output/unreal/exterior-20261002-r34a'
REPORT = BASE/'garden-fern-only-native-report.json'
BASE_SHA = 'd233329bee2ffcb95419c8266ff8c1f50931ba8f642ded23ab20330f1d334cb8'
GARDEN = ROOT/'output/unreal/exterior-garden-organic-20261001-r1c-study/garden-plan.json'
GARDEN_SHA = 'e599442a7ec887d16ee6e58c7466f4a34bf9a7880ef538bd2861c80ad39523e6'
R34 = ROOT/'output/unreal/exterior-garden-fern-only-20261002-r34-study/fern-only-source-plan.json'
SUITE = ROOT/'output/unreal/exterior-validation-20260930-r1/qa/editor-pilot-r34a-fern-only-original-heroes-r24-1790929902886-hESEbO/editor-pilot-suite.json'
PREFIX = '/Game/Brezi/GardenPeriwinkle20261002R36'


def require(value, message):
    if not value: raise RuntimeError(message)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',',':'), allow_nan=False).encode()).hexdigest()
def pin(path):
    p=Path(path).resolve(); return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def read(path): return json.loads(Path(path).read_text())
def write(path, row):
    with Path(path).open('x') as f: json.dump(row,f,indent=2,allow_nan=False);f.write('\n')
def module(name, filename):
    p=ROOT/'scripts/unreal'/filename;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class Accessors:
    def __init__(self,doc,data): self.doc,self.data=doc,data
    def raw(self,index):
        a=self.doc['accessors'][index];v=self.doc['bufferViews'][a['bufferView']]
        require(v['buffer']==0 and 'sparse' not in a,'Original dense single BIN accessors required')
        width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        code={5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[a['componentType']]
        size=np.dtype(code).itemsize*width;start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',size)
        require(stride>=size and start+(a['count']-1)*stride+size<=len(self.data),'Original attribute extent differs')
        values=np.ndarray((a['count'],width),dtype=code,buffer=self.data,offset=start,strides=(stride,np.dtype(code).itemsize)).copy()
        raw=b''.join(self.data[start+i*stride:start+i*stride+size] for i in range(a['count']))
        return values,raw


def decode_provider():
    doc=read(ASSETS/'periwinkle_plant_2k.gltf');data=(ASSETS/'periwinkle_plant.bin').read_bytes()
    require(len(doc['buffers'])==1 and doc['buffers'][0]['byteLength']==len(data) and not doc.get('extensionsUsed'), 'Exact unextended original source required')
    decode=Accessors(doc,data);models={}
    wanted={'POSITION','NORMAL','TEXCOORD_0','TEXCOORD_1','COLOR_0','COLOR_1'}
    for node in doc['nodes']:
        require(not any(k in node for k in ('rotation','scale','matrix','children')), 'Only original display translations may be removed')
        mesh=doc['meshes'][node['mesh']];require(len(mesh['primitives'])==1,'Original one complete primitive per plant required')
        p=mesh['primitives'][0];require(set(p['attributes'])==wanted and p.get('mode',4)==4,'All two UV/color sets and indexed triangles must be retained')
        attrs={}; arrays={}
        for key,index in p['attributes'].items():
            a,raw=decode.raw(index);arrays[key]=a
            attrs[key]={'sourceAccessor':index,'accessor':doc['accessors'][index], 'orderedRawAttributeBytesSha256':hashlib.sha256(raw).hexdigest()}
        ids,indexraw=decode.raw(p['indices']);ids=ids[:,0].astype(np.int64)
        original=arrays['POSITION'];points=(original[:,[0,2,1]].astype(np.float64)*100).astype(np.float32).astype(np.float64)
        bottom=float(points[:,2].min());height=float(points[:,2].max()-bottom);radius=float(np.hypot(points[:,0],points[:,1]).max())
        require(len(ids)%3==0 and ids.min()>=0 and ids.max()<len(points) and np.isfinite(points).all(),'Complete finite original geometry required')
        require(np.all(arrays['COLOR_0']==255), 'COLOR0 optical-equivalence assumption requires actual all-white source')
        models[node['name']]={'id':node['name'],'sourceMeshIndex':node['mesh'],'sourceNodeDisplayTranslationRemoved':node.get('translation',[0,0,0]),
            'sourceVertices':len(points),'sourceTriangles':len(ids)//3,'originalNativeF32BottomCm':bottom,'originalHeightCm':height,'originalRadiusCm':radius,
            'originalBoundsCm':{'min':points.min(axis=0).tolist(),'max':points.max(axis=0).tolist()},'attributes':attrs,
            'sourceIndicesAccessor':p['indices'],'orderedRawIndexBytesSha256':hashlib.sha256(indexraw).hexdigest(),'originalMaterialIndex':p['material'],
            'sourceTangentPresent':False,'sourceColor0AllWhite':True,'sourceColor1OpticalOrWindMeaningAsserted':False,
            '_points':points,'_indices':ids}
    require(len(models)==6 and sum(m['sourceTriangles']for m in models.values())==34350,'All six whole provider models required')
    return doc,data,models


def export_original_glb(doc,data):
    adapted=copy.deepcopy(doc);adapted['buffers'][0].pop('uri')
    for n in adapted['nodes']:n.pop('translation',None)
    encoded=json.dumps(adapted,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode();encoded+=b' '*((-len(encoded))%4)
    binary=data+b'\0'*((-len(data))%4)
    glb=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary
    restored=copy.deepcopy(adapted);restored['buffers'][0]['uri']=doc['buffers'][0]['uri']
    for old,new in zip(doc['nodes'],restored['nodes']):
        if 'translation' in old:new['translation']=old['translation']
    require(restored==doc and binary[:len(data)]==data,'Only original display translation/buffer URI adapter permitted')
    return glb


def camera_matrix(camera):
    eye=np.array(camera['eyeCm'],dtype=float);forward=np.array(camera['targetCm'])-eye;forward/=np.linalg.norm(forward)
    right=np.array([forward[1],-forward[0],0.]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    return eye,np.column_stack([right,up,forward]),math.tan(math.radians(camera['horizontalFovDegrees']/2))
def project(points,camera):
    eye,basis,tangent=camera_matrix(camera);values=(points-eye)@basis;depth=values[:,2]
    xy=np.column_stack([960*(1+values[:,0]/(depth*tangent)),540*(1-values[:,1]/(depth*tangent/(1920/1080)))])
    inside=(depth>0)&(xy[:,0]>=0)&(xy[:,0]<=1920)&(xy[:,1]>=0)&(xy[:,1]<=1080)
    return xy,depth,inside
def pose(points,row,scale,bottom=0.):
    angle=math.radians(row['yawDeg']);c,s=math.cos(angle),math.sin(angle)
    result=points.copy();result[:,0]=scale*(c*points[:,0]-s*points[:,1])+row['positionCm'][0]
    result[:,1]=scale*(s*points[:,0]+c*points[:,1])+row['positionCm'][1]
    result[:,2]=scale*(points[:,2]-bottom)+row['positionCm'][2]
    return result


def choose(row,models,flowers):
    x,y=row['positionCm'][:2];field=.36*math.sin(x/210)+.34*math.cos(y/150)+.22*math.sin((x+y)/97)
    target=min(43.,max(18.,14.+.80*row['radiusCm']+3.*field))
    overlapping=[f for f in flowers if math.hypot(x-f['positionCm'][0],y-f['positionCm'][1])<row['radiusCm']+f['radiusCm']]
    if overlapping:target=min(target,min(f['actualHeightCm']for f in overlapping)*.90)
    # Larger whole specimens provide volume inside wide old envelopes; narrow
    # whole forms serve small circles/flower-adjacent positions, never flattening.
    if target>=30. and row['radiusCm']>=17.:
        suffix='01' if field>=-.15 else '02'
    elif target>=27.:suffix='03'
    elif target>=22.:suffix='04'
    elif target>=18.:suffix='05'
    else:suffix='06'
    m=models['periwinkle_plant_'+suffix+'_LOD0'];scale=min(target/m['originalHeightCm'],.99*row['radiusCm']/m['originalRadiusCm'])
    return m,scale,target,field,[f['id']for f in overlapping]


def current_source(report,garden,r34):
    require(sha(REPORT)==BASE_SHA and report['nativeApplied'] is report['savedMapUnloadedReloaded'] is True,'Actual saved R34 required')
    removed={p['rootId']for p in r34['proposedPlacements']};low=[r for r in garden['gardenDetailPlacements']if r['role']=='groundcover'and r['id']not in removed]
    flowers=[r for r in garden['gardenDetailPlacements']if r['role']=='ornamental'];heroes=garden['ornamentalPlacements']
    controls=read(report['retainedGardenControlsSaved']['path']);witness=read(report['savedActorWitness']['path']);byid={r['id']:r for r in low}
    groups=[]
    for key,binding in r34['originalGardenGroupBindings'].items():
        if not key.startswith('EX_groundcover_'):continue
        actor=binding['actor'];control=controls[actor];component=next(c for c in witness[actor]['components']if c['name']==binding['component'])
        require(set(control['rootIds'])<=set(byid) and component['instanceCount']==len(control['rootIds']) and digest(control['recoveredValues'])==component['orderedInstanceTransformsSha256'],'All original current low-group identities/order required')
        require(control['numCustomDataFloats']==0 and control['customData']==[], 'Exact observed zero custom-data retained')
        groups.append({'groupId':key,'actor':actor,'component':binding['component'],'currentMesh':component['mesh'],
            'currentRootCount':len(control['rootIds']),'rootIds':control['rootIds'],'originalRecoveredFramesSha256':digest(control['recoveredValues']),
            'originalStoredMatricesSha256':digest(control['storedMatrices']),'mainRandomSeed':control['mainRandomSeed'],
            'retireWholeComponentMembers':True,'componentActorDeleted':False,'retainedMembersInRetiredGroup':0,
            'additionalRandomSeedsReadbackAvailable':False,'noSeedSetterAllowed':True})
    require(len(low)==384 and len(flowers)==41 and len(heroes)==12 and len(removed)==36 and len(groups)==4
        and sum(g['currentRootCount']for g in groups)==384 and set(i for g in groups for i in g['rootIds'])==set(byid),'Only four current low-star groups may retire')
    return low,flowers,heroes,groups


def old_models(garden):
    manifest=read(garden['organicMasters']['path']);source=next(m for m in manifest['meshes']if m['id']=='garden_broadleaf_organic_a');raw=Path(source['glbPath']).read_bytes()
    length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);at=20+length;bl=struct.unpack_from('<I',raw,at)[0];data=raw[at+8:at+8+bl];decode=Accessors(doc,data);result={}
    for node in doc['nodes']:
        if node['name']not in ('garden_broadleaf_organic_a_LOD0','garden_broadleaf_organic_b_LOD0'):continue
        parts=[]
        for p in doc['meshes'][node['mesh']]['primitives']:
            a,_=decode.raw(p['attributes']['POSITION']);ids,_=decode.raw(p['indices']);points=(a[:,[0,2,1]].astype(float)*100).astype(np.float32).astype(float)
            parts.append({'points':points,'indices':ids[:,0].astype(np.int64)})
        result[node['name'][:-5]]=parts
    require(len(result)==2,'Both actual whole old source low masters required');return source['glbPath'],result


def support_image(rows,models,camera,proposed):
    im=Image.new('1',(1920,1080));draw=ImageDraw.Draw(im);faces=0
    for row in rows:
        if proposed:
            m=models[row['model']];parts=[{'points':m['_points'],'indices':m['_indices']}];scale=row['uniformScale'];bottom=0.
        else:parts=models[row['meshId']];scale=row['uniformScale'];bottom=0.
        for part in parts:
            world=pose(part['points'],row,scale,bottom);xy,depth,inside=project(world,camera)
            ids=part['indices'].reshape(-1,3);eligible=(depth[ids]>0).all(axis=1)&(xy[ids].max(axis=1)[:,0]>=0)&(xy[ids].min(axis=1)[:,0]<=1920)&(xy[ids].max(axis=1)[:,1]>=0)&(xy[ids].min(axis=1)[:,1]<=1080)
            for face in ids[eligible]:draw.polygon([tuple(p)for p in xy[face]],fill=1);faces+=1
    return im,faces


def source_plot(garden,old,placements,heroes,flowers):
    points=np.array([p[:2]for ts in garden['sourceMulchTrianglesCm'].values()for t in ts for p in t]);mn=points.min(axis=0)-40;mx=points.max(axis=0)+40
    width,height=1400,720;scale=min(1300/(mx[0]-mn[0]),580/(mx[1]-mn[1]))
    def xy(p):return 45+(p[0]-mn[0])*scale,665-(p[1]-mn[1])*scale
    lines=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 720" role="img" aria-label="R36 original whole Periwinkle source layout">',
        '<rect width="1400" height="720" fill="#f4f3ed"/><text x="35" y="32" font-family="sans-serif" font-size="23">R36 · všetkých 384 nízkych hviezdicových trsov → celé pôvodné periwinkle</text>',
        '<text x="35" y="56" font-family="sans-serif" font-size="14">Iba zdrojový návrh. Pôvodné kružnice sivé, nové zelené; 12 vysokých trsov a 41 kvetov bez zmeny. 36 fern zachovaných.</text>']
    for faces in garden['sourceMulchTrianglesCm'].values():
        for t in faces:lines.append('<polygon points="'+' '.join('%.2f,%.2f'%xy(p)for p in t)+'" fill="#c2a17c" stroke="#a28d72" stroke-width=".3"/>')
    for r in old:
        x,y=xy(r['positionCm']);lines.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="none" stroke="#575c59" stroke-opacity=".25" stroke-width=".6"/>'%(x,y,r['radiusCm']*scale))
    for r in placements:
        x,y=xy(r['positionCm']);lines.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="#497c47" fill-opacity=".64"><title>%s · %.2fcm</title></circle>'%(x,y,r['radiusCm']*scale,r['rootId'],r['heightCm']))
    for r in heroes+flowers:
        x,y=xy(r['positionCm']);lines.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="none" stroke="%s" stroke-width="1.4"/>'%(x,y,r['radiusCm']*scale,'#94548c'if r in heroes else'#d9efea'))
    lines.append('<text x="35" y="706" font-family="sans-serif" font-size="14">Kružnice sú obsahujúce obálky; nie listové pokrytie, geodetický podklad ani natívna viditeľnosť.</text></svg>')
    return '\n'.join(lines)


def main():
    require(not OUT.exists(),'Fresh R36 output only');require(sha(GARDEN)==GARDEN_SHA,'Original garden source changed')
    report,garden,r34=read(REPORT),read(GARDEN),read(R34);low,flowers,heroes,groups=current_source(report,garden,r34)
    doc,data,models=decode_provider();steps_helper=module('r36_exact_original_step_projection','exterior-garden-composition-step-guards-r3.py');steps=steps_helper.validated_steps(garden['sourceStepTrianglesCm'])
    beds={key:unary_union([Polygon([p[:2]for p in t])for t in faces])for key,faces in garden['sourceMulchTrianglesCm'].items()}
    for bed in beds.values():shapely.prepare(bed)
    suite=read(SUITE);case=next(c for c in suite['cases']if c['view']=='exterior-garden');require(case['outcome']['code']==0 and suite['sourceInputsUnchanged']is True,'Actual original garden source camera required');camera=case['sourceCamera']
    placements=[];vertex_count=0
    for row in low:
        m,scale,target,field,nearflowers=choose(row,models,flowers);radius=scale*m['originalRadiusCm'];world=pose(m['_points'],row,scale,m['originalNativeF32BottomCm'])
        bed=beds[row['sourceBedId']];distance=Point(row['positionCm'][:2]).distance(bed.boundary)
        require(scale>0 and radius<=.99*row['radiusCm'] and radius<distance,'Original bed/crown envelope escaped')
        require(bool(shapely.contains_xy(bed,world[:,0],world[:,1]).all()),'Full decoded source points escape bed')
        step=steps_helper.circle_clearance(steps,row['positionCm'][:2],radius);xy,depth,inside=project(world,camera);vertex_count+=len(world)
        root=list(row['positionCm']);root[2]-=scale*m['originalNativeF32BottomCm']
        placements.append({'rootId':row['id'],'originalRow':row,'sourceBedId':row['sourceBedId'],'model':m['id'],
            'positionCm':root,'sourceContactPositionCm':row['positionCm'],'newRootZOffsetCm':root[2]-row['positionCm'][2],
            'sourceRootXYAndYawPreserved':True,'yawDeg':row['yawDeg'],'uniformScale':scale,'scale':[scale]*3,'heightCm':scale*m['originalHeightCm'],
            'radiusCm':radius,'requestedHeightCm':target,'originalHeightCm':row['actualHeightCm'],'heightRoleChanged':True,
            'artistRole':'low-to-medium leafy perennial understory, deliberately taller than old flat star cards','growthField':field,
            'sourceFlowerEnvelopeNeighbors':nearflowers,'flowerAdjacentRequestedHeightCapFraction':.90,'allOriginalFlowerRootsAndHeightsUnchanged':True,
            'allFullSourceVerticesInsideOriginalBed':True,'fullCircleInsideOriginalBed':True,'fullCircleExcludesOriginalSteps':True,
            'oldCircularEnvelopeNotExpanded':True,'sourceVerticesChecked':len(world),'sourceTriangles':m['sourceTriangles'],
            'bedBoundaryClearanceCm':distance-radius,'stepBoundaryClearanceCm':step['circleClearanceCm'],
            'worldBoundsCm':{'min':world.min(axis=0).tolist(),'max':world.max(axis=0).tolist()},
            'sourceCameraProjection':{'allVerticesProjected':len(world),'verticesInsideFrustum':int(inside.sum()),
              'pixelBounds':{'min':xy.min(axis=0).tolist(),'max':xy.max(axis=0).tolist()},'camera':'exterior-garden','sourceProjectionOnly':True,
              'houseOrPlantOcclusionVerified':False,'nativeVisibleGainVerified':False}})
    original_glb,original_models=old_models(garden);before,before_triangles=support_image(low,original_models,camera,False);after,after_triangles=support_image(placements,models,camera,True)
    a,b=np.asarray(before,dtype=bool),np.asarray(after,dtype=bool)
    support={'method':'1920x1080 PIL raster of ALL projected source indexed triangle supports; unoccluded, no alpha test, clipped to image',
      'oldTriangleSupportPixels':int(a.sum()),'newTriangleSupportPixels':int(b.sum()),'sharedSupportPixels':int((a&b).sum()),
      'oldOnlySupportPixels':int((a&~b).sum()),'newOnlySupportPixels':int((b&~a).sum()),'rasterizedOldSourceTriangles':before_triangles,
      'rasterizedNewSourceTriangles':after_triangles,'sourceCamera':camera,'alphaPixelsMeasured':False,'visiblePlantOrLeafCoverageMeasured':False,
      'plantHouseTerrainOcclusionVerified':False,'rasterBoundaryErrorQuantified':False,'nativeAppearanceAccepted':False}
    # Exact geometry/envelope union, separate from optical triangle support.
    circle_old=unary_union([Point(r['positionCm'][:2]).buffer(r['radiusCm'],quad_segs=64)for r in low]);circle_new=unary_union([Point(r['positionCm'][:2]).buffer(r['radiusCm'],quad_segs=64)for r in placements])
    envelope={'method':'64segments/quadrant polygonal union of containing circles; not alpha/leaf/native visible coverage',
      'oldLowContainingCircleUnionM2':circle_old.area/10000,'newLowContainingCircleUnionM2':circle_new.area/10000,
      'oldOnlyContainingCircleUnionM2':circle_old.difference(circle_new).area/10000,'wholeNewCircleContainedInOldSameRootCircle':True,
      'polygonalCircleAreaApproximationRelativeError':1-256*math.sin(2*math.pi/256)/(2*math.pi),'leafCoverageMeasured':False}
    OUT.mkdir();glb=export_original_glb(doc,data);(OUT/'periwinkle-whole-originals.glb').write_bytes(glb)
    # Original external glTF images remain valid during mesh-only import. These
    # byte-identical copies are not the separately selected original PBR PNGs.
    for image in doc['images']:
        source=ASSETS/image['uri'];target=OUT/image['uri'];target.parent.mkdir(exist_ok=True);target.write_bytes(source.read_bytes());require(sha(source)==sha(target),'Original referenced image copy differs')
    published={k:{a:v for a,v in m.items()if not a.startswith('_')}for k,m in models.items()}
    write(OUT/'geometry-descriptor.json',{'schema':'brezi-garden-whole-original-periwinkle-geometry-r36','owner':OWNER,'models':published,
      'providerGltf':pin(ASSETS/'periwinkle_plant_2k.gltf'),'providerBin':pin(ASSETS/'periwinkle_plant.bin'),'sourceGlb':pin(OUT/'periwinkle-whole-originals.glb'),
      'originalBinPayloadByteExact':True,'allOriginalAccessorsAndAllSixAttributeSetsByteExact':True,'allOriginalIndicesOrderByteExact':True,
      'sourcePositionAttributesChanged':False,'displayNodeTranslationsRemoved':True,'wholeNewInstanceVerticalBottomOffsetDeclared':True,
      'nativeExpectedAxisBasis':'[float32(100*x),float32(100*z),float32(100*y)] original local provider positions',
      'originalProviderLodsPerMaster':1,'originalTangentPresent':False,'ueTangentRecomputeFromOriginalUv0Requested':True,'nativeNormalTangentReadbackAvailable':False,
      'nativeColor1ReadbackAvailable':False,'originalColor0AllWhite':True,'sourceColor1MeaningOrNativeShaderMappingClaimed':False,'nativeGeometryVerified':False})
    before.convert('L').save(OUT/'old-unoccluded-source-triangle-support.png');after.convert('L').save(OUT/'new-unoccluded-source-triangle-support.png')
    comparison=Image.new('RGB',(1920,2160),'#f4f3ed');comparison.paste(before.convert('RGB'),(0,0));comparison.paste(after.convert('RGB'),(0,1080));draw=ImageDraw.Draw(comparison)
    draw.rectangle((0,0,1920,40),fill='#183525');draw.text((20,12),'R34 OLD: full source triangles, unoccluded/no alpha/native visibility proof',fill='white')
    draw.rectangle((0,1080,1920,1120),fill='#183525');draw.text((20,1092),'R36 PROPOSED: full original Periwinkle triangles, same camera; source only',fill='white');comparison.save(OUT/'source-triangle-support-comparison.png')
    (OUT/'source-root-layout.svg').write_text(source_plot(garden,low,placements,heroes,flowers))
    png=ASSETS/'original-pbr-png-2k';maps={'albedo':png/'periwinkle_plant_diff_2k.png','normalGl':png/'periwinkle_plant_nor_gl_2k.png',
        'opacity':png/'periwinkle_plant_opacity_2k.png','roughness':png/'periwinkle_plant_rough_2k.png','translucency':png/'periwinkle_plant_translucency_2k.png'}
    recipe={'schema':'brezi-garden-original-periwinkle-material-recipe-r36','owner':OWNER,'status':'source-original-map-recipe-native-pending','prefix':PREFIX,
      'key':'ph_original_periwinkle_r36','sourceGltf':pin(ASSETS/'periwinkle_plant_2k.gltf'),'originalDownloadReceipt':pin(ASSETS/'original-download-receipt.json'),
      'originalPbrPngReceipt':pin(png/'original-pbr-download-receipt.json'),'maps':{k:pin(v)for k,v in maps.items()},'sourceOriginalAlphaMode':'BLEND',
      'proposedEngineBlendMode':'MASKED','originalDoubleSided':True,'engineShadingModel':'TwoSidedFoliage artistic proposal','alphaRoute':'original16bit opacity PNG normalized R -> OpacityMask cutoff0.5',
      'albedoSourceSrgb':True,'normalSourceLinear':True,'normalGlFlipGreen':True,'roughnessLinearNormalizedR':True,'translucencySourceSrgb':True,
      'baseColorFactor':[1,1,1,1],'roughnessFactor':1,'metallic':0,'normalScale':1,'uvChannel':0,'clipValue':.5,'specular':.5,
      'subsurfaceColorRoute':'unchanged original translucency RGB times explicit UE calibration0.08','subsurfaceCalibration':.08,
      'sourceOpticalModelExactlyReproduced':False,'sourceColor0AllWhite':True,'color1NotUsedByOriginalGltfMaterial':True,'wpoEnabled':False,'newGraphCount':1,'newTextureObjectCount':5,
      'sourcePixelsEdited':False,'roughPngVsArmGPixelEquivalenceClaimed':False,'actualNativeGpuPixelFormatVerified':False,'physicalOpticalCalibrationAccepted':False,
      'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False}
    write(OUT/'material-recipe.json',recipe);write(OUT/'source-camera-support.json',support);write(OUT/'source-envelope-coverage.json',envelope)
    inputs=[REPORT,GARDEN,R34,SUITE,Path(report['retainedGardenControlsSaved']['path']),Path(report['savedActorWitness']['path']),BASE/'root-native-byte-audit-r34a.json',
      ASSETS/'original-download-receipt.json',png/'original-pbr-download-receipt.json',ASSETS/'periwinkle_plant_2k.gltf',ASSETS/'periwinkle_plant.bin',Path(original_glb),
      ROOT/'scripts/unreal/exterior-garden-composition-step-guards-r3.py',ROOT/OWNER,*maps.values(),*(ASSETS/i['uri']for i in doc['images'])]
    counts={m:sum(p['model']==m for p in placements)for m in models};used=sum(n>0 for n in counts.values())
    plan={'schema':'brezi-garden-original-periwinkle-composition-source-r36','schemaVersion':1,'owner':OWNER,'status':'source-all384-low-stars-replaced-whole-original-periwinkle-native-pending',
      'createdAt':datetime.now(timezone.utc).isoformat(),'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},
      'actualNativeBase':{'report':pin(REPORT),'retainedGardenControls':report['retainedGardenControlsSaved'],'savedActorWitness':report['savedActorWitness'],
        'currentByteAudit':pin(BASE/'root-native-byte-audit-r34a.json'),'nativeApplied':True,'ownR36NativeApplied':False},
      'candidateOutputProposed':str(ROOT/'output/unreal/exterior-20261002-r36a'),'nativeClone':None,
      'retireWholeOriginalGroups':groups,'retiredOriginalLowRootIds':[r['id']for r in low],'proposedPlacements':placements,
      'preservedOriginalHeroRootIds':[r['id']for r in heroes],'preservedOriginalFlowerRootIds':[r['id']for r in flowers],'preservedR34FernRootIds':[r['rootId']for r in r34['proposedPlacements']],
      'sourceOriginalLowCount':384,'sourceNewWholeOriginalCount':384,'originalLowSourceRowsSha256':digest(low),'preservedOriginal53HeroFlowerSourceRowsSha256':digest(heroes+flowers),
      'providerModelCounts':counts,'sourceHeightPolicy':'Deliberate physical low-to-medium volume increase; uniform whole-model scale, old circle envelope not expanded; nearby flower envelope limits requested topheight to90% original flower height.',
      'sourceHeightRangeCm':[min(p['heightCm']for p in placements),max(p['heightCm']for p in placements)],'sourceOldHeightRangeCm':[min(r['actualHeightCm']for r in low),max(r['actualHeightCm']for r in low)],
      'sourceVerticesInsideBedsChecked':vertex_count,'sourceMinimumBedCircleClearanceCm':min(p['bedBoundaryClearanceCm']for p in placements),
      'sourceMinimumStepCircleClearanceCm':min(p['stepBoundaryClearanceCm']for p in placements),'sourceStepProjectionPolicy':steps['policy'],
      'geometryDescriptor':pin(OUT/'geometry-descriptor.json'),'sourceGlb':pin(OUT/'periwinkle-whole-originals.glb'),'materialRecipe':pin(OUT/'material-recipe.json'),
      'sourceCameraSupport':pin(OUT/'source-camera-support.json'),'sourceEnvelopeCoverage':pin(OUT/'source-envelope-coverage.json'),
      'sourceLayout':pin(OUT/'source-root-layout.svg'),'sourceSupportPlot':pin(OUT/'source-triangle-support-comparison.png'),
      'budget':{'uniqueProviderTriangles':34350,'uniqueProviderVertices':31801,'instancedProviderTriangles':sum(p['sourceTriangles']for p in placements),
        'newNonemptyHismGroupsProposed':used,'oldGroupsWholeRetired':4,'noSurvivorRebuildOrRandomSeedSetterRequired':True,'newMeshAssets':6,'newMaterialGraphs':1,'newTextureObjects':5,'newPipelineAssets':3,'newPackagesProposed':15,
        'expectedActors':5354+used,'expectedFullHismComponents':2316+used,'expectedFullHismInstances':676957,'expectedContentFiles':4086,'expectedProtectedProjectFiles':132,'performanceVerified':False},
      'nativeExecutionRequirements':{'loadOnlyActualSavedR34NativeHelperOwnerPinned':True,'whole4OldLowComponentsClearOnly':True,'allOtherOriginalActorsWitnessExact':True,
        'all12Heroes41Flowers36FernsActualRawMatrixOrderControlsExact':True,'newRootXYAndOriginalWrappedQuaternionCopied':True,
        'newPositiveUniformScaleAndVerticalSourceBottomOffsetDeclared':True,'meshlessFaithfulNewFrameMeasurementBeforeMutationRequired':True,
        'fullOriginalNativeF32PositionsUv0Uv1IndicesSectionsRequired':True,'nativeNormalTangentReadbackAvailable':False,'nativeColor1ReadbackAvailable':False,
        'noRetainedRootRecompositionOrSeedSetterAllowed':True,'AdditionalRandomSeedsReadbackAvailable':False,'shaderRandomIdentityPreservationClaimed':False},
      'futureYardIntegration':{'actualR35RepairDonorPending':True,'applyInSeparateCompositionAfterOwnGardenVisualReview':True,'yardAppliedHere':False},
      'inputFiles':{str(p.resolve()):sha(p)for p in inputs},'artistAuthoredUnsurveyedPlacement':True,'speciesEcologicalFitVerified':False,
      'sourceTriangleSupportIsNativeAlphaOrVisibleCoverage':False,'sourceMaskValidated':True,'nativeExecuted':False,'gpuExecuted':False,'nativeApplied':False,
      'nativeGeometryVerified':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}
    write(OUT/'periwinkle-source-plan.json',plan);(OUT/'source-producer.py').write_bytes((ROOT/OWNER).read_bytes())
    require(all(sha(p)==h for p,h in plan['inputFiles'].items()),'Original consumed source changed during source build')
    print(json.dumps({'plan':pin(OUT/'periwinkle-source-plan.json'),'counts':counts,'height':plan['sourceHeightRangeCm'],'triangles':plan['budget']['instancedProviderTriangles'],
      'sourceProjectedSupport':support,'containingCircleCoverage':envelope,'nativeApplied':False},allow_nan=False))


if __name__=='__main__':main()
