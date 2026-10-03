"""Unbound, stdlib-only original R39 prop contract. No source regeneration.

Six physical assemblies use four original mesh parts. A future source revision
must bind a selected saved scene before any UObject or map operation.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighbor-props-contract-r39-draft.py'
PREFIX = '/Game/Brezi/NeighborProps20261002R39'
TAG = 'BreziNeighborPropsR39:'
SOURCE = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-source-study/neighbor-props-source-proposal.json'
SOURCE_SHA = 'a408e466ff67579b9ff6cc5c1534d27ca71f1d44dba83b8768f0137efef8f67a'
RECEIPT_SHA = '036ee6ce5d10637c3aa0e1bb7566dc1ac199391010e57d743875625dc13e1789'
MODEL_IDS = ('garden_hose_wall_mounted_01', 'planter_pot_clay', 'watering_can_metal_01')
EXPECTED_PARTS = {'garden_hose_wall_mounted_01': [344,11340], 'planter_pot_clay':[3080], 'watering_can_metal_01':[11837]}
FUTURE_BINDING = None

def require(ok, message):
    if not ok: raise RuntimeError(message)

def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def pin(p):
    p=Path(p).resolve();return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def checked(row):
    p=Path(row['path']);require(p.is_absolute() and p.resolve()==p and not p.is_symlink() and p.is_file()
      and row==pin(p),'Original exact source pin differs: '+str(p));return p

def require_bound(binding=None):
    # No binding supplied by a caller can make this draft mutate a scene.
    require(FUTURE_BINDING is not None and binding==FUTURE_BINDING,
      'R39 draft is unbound: root image selection, saved native base and independent clone are pending')
    raise RuntimeError('Only a NEW reviewed bound R39 owner may apply this draft')

def f32(v): return struct.unpack('<f',struct.pack('<f',v))[0]
def native_vec(p): return [f32(100*p[0]),f32(100*p[2]),f32(100*p[1])]
def accessor(d,buffers,index):
    a=d['accessors'][index];require(not a.get('sparse') and not a.get('normalized',False),'Original nonsparse unnormalized accessor required')
    codes={5121:('B',1),5123:('H',2),5125:('I',4),5126:('f',4)};widths={'SCALAR':1,'VEC2':2,'VEC3':3}
    require(a['componentType']in codes and a['type']in widths,'Unsupported original accessor shape')
    view=d['bufferViews'][a['bufferView']];code,size=codes[a['componentType']];width=widths[a['type']]
    start=view.get('byteOffset',0)+a.get('byteOffset',0);stride=view.get('byteStride',width*size);buf=buffers[view['buffer']]
    require(stride>=width*size and start+(a['count']-1)*stride+width*size<=len(buf),'Original accessor range escapes BIN')
    return [list(struct.unpack_from('<'+code*width,buf,start+i*stride))for i in range(a['count'])]

def decode_model(model):
    d=read(checked(model['gltf']));bins={Path(r['path']).name:checked(r).read_bytes()for r in model['bins']}
    require(d['asset']['version']=='2.0' and d['nodes']==model['originalNodes'] and d['materials']==model['sourceMaterials'],'Original nodes/materials changed')
    buffers=[]
    for b in d['buffers']:
        require(Path(b['uri']).name==b['uri'] and b['uri']in bins and len(bins[b['uri']])==b['byteLength'],'Exact original external BIN required')
        buffers.append(bins[b['uri']])
    require(d['scenes'][d.get('scene',0)]['nodes']==list(range(len(d['nodes']))),'Whole original scene roots required')
    parts=[]
    for node_index,node in enumerate(d['nodes']):
        require(set(node)<= {'mesh','name','translation'} and 'mesh'in node,'Source rotations/scales/hierarchy require a new explicit adapter')
        mesh=d['meshes'][node['mesh']];require(len(mesh['primitives'])==1,'One original primitive per part required')
        p=mesh['primitives'][0];require(p.get('mode',4)==4 and set(p['attributes'])=={'POSITION','NORMAL','TEXCOORD_0'},'All original P/N/UV0 must remain untouched')
        positions=accessor(d,buffers,p['attributes']['POSITION']);normals=accessor(d,buffers,p['attributes']['NORMAL']);uv=accessor(d,buffers,p['attributes']['TEXCOORD_0']);indices=[v[0]for v in accessor(d,buffers,p['indices'])]
        require(len(indices)%3==0 and all(0<=i<len(positions)for i in indices),'Original index range differs')
        original=model['parts'][node_index]
        require(len(positions)==original['vertexCount'] and len(indices)//3==original['triangleCount'] and p['material']==original['materialIndex']==0,'Original part/section count differs')
        parts.append({'key':model['id']+':'+str(node_index),'modelId':model['id'],'nodeIndex':node_index,'nodeName':node['name'],
          'originalSourceMeshName':mesh['name'],'triangles':len(indices)//3,'vertices':len(positions),'positions':positions,'normals':normals,'uv0':uv,'indices':indices,
          'nativeVerticesCm':[native_vec(v)for v in positions],'sourceNodeTranslationMeters':node.get('translation',[0.,0.,0.]),
          'proposedNativeNodeTranslationCm':native_vec(node.get('translation',[0.,0.,0.])),
          'nodeTranslationRouteActuallyMeasured':False,'sourceAttributeNames':sorted(p['attributes']),
          'sourceTangentPresent':False,'nativeNormalTangentReadbackAvailable':False})
    require([p['triangles']for p in parts]==EXPECTED_PARTS[model['id']],'Whole original model parts/counts differ')
    return parts

def material_recipe(model,receipt):
    require(len(model['sourceMaterials'])==1,'One provider material per original assembly required')
    source=model['sourceMaterials'][0];pbr=source['pbrMetallicRoughness'];require(source.get('alphaMode','OPAQUE')=='OPAQUE' and source['doubleSided'] is True
      and 'occlusionTexture'not in source and pbr.get('baseColorFactor',[1,1,1,1])==[1,1,1,1] and pbr.get('roughnessFactor',1)==1
      and source['normalTexture'].get('scale',1)==1,'Original opaque/two-sided core factors/no-AO differ')
    key=model['id'];roles={'albedo':'Diffuse','normalGL':'nor_gl','roughness':'Rough'}
    if key!='planter_pot_clay':roles['metallic']='Metal'
    maps={}
    for role,published in roles.items():
        rows=[r for r in receipt['files']if r['asset']==key and r['role']==published];require(len(rows)==1,'One exact published map per role required')
        maps[role]={k:rows[0][k]for k in ('path','sha256','bytes')}
    factor=pbr.get('metallicFactor',1);require(factor==(0 if key=='planter_pot_clay'else 1),'Original metallic factor differs')
    extensions=source.get('extensions',{})
    if key=='watering_can_metal_01':
        require(extensions=={'KHR_materials_specular':{'specularColorFactor':[0,0,0]},'KHR_materials_ior':{'ior':1.4500000476837158}},'Original can extensions changed')
    else:require(not extensions,'Unexpected optical extension')
    return {'key':key,'sourceGltf':model['gltf'],'originalMaterial':source,'maps':maps,'originalAlphaMode':'OPAQUE','blendMode':'OPAQUE','shadingModel':'DEFAULTLIT',
      'twoSided':True,'uvChannel':0,'normalGLFlipGreen':True,'roughnessChannel':'R','metallicChannel':'R'if factor else None,
      'metallicFactor':factor,'ueSpecular':0. if key=='watering_can_metal_01'else .5,'ambientOcclusionRoot':None,'worldPositionOffset':None,
      'originalTexturePixelsEdited':False,'originalPngAlternativeToReferencedJpeg':True,'pngVsReferencedJpegPixelEquivalenceClaimed':False,
      'dielectricF0Mapping':'zero F0 approximation'if key=='watering_can_metal_01'else 'default .04 F0 represented by UE Specular .5',
      'wateringCanGrazingEnergyPreserved':False,'wateringCanIorExactlyReproduced':False,'sourceOpticalModelExactlyReproduced':False,
      'sourceDoubleSidedBackfaceNormalSemanticsRequested':True,'nativeBackfaceNormalNumericsVerified':False,'nativeAppearanceAccepted':False}

def load_source():
    require(sha(SOURCE)==SOURCE_SHA,'Frozen source proposal changed');proposal=read(SOURCE);receipt=read(checked(proposal['originalDownloadReceipt']))
    require(proposal['originalDownloadReceipt']['sha256']==RECEIPT_SHA and proposal['futureNativeBase']is None and proposal['futureProjectClone']is None
      and proposal['futureNativeReport']is None and set(proposal['models'])==set(MODEL_IDS) and len(proposal['placements'])==6,'Only frozen unbound six-assembly source required')
    parts={k:decode_model(proposal['models'][k])for k in MODEL_IDS};recipes={k:material_recipe(proposal['models'][k],receipt)for k in MODEL_IDS}
    require(len([p for rows in parts.values()for p in rows])==4 and sum(p['triangles']for rows in parts.values()for p in rows)==26601,'Four original parts required')
    return {'proposal':proposal,'proposalPin':pin(SOURCE),'receipt':receipt,'parts':parts,'recipes':recipes,
      'selectedNativeBase':None,'projectClone':None,'nativeReport':None,'originalPhotoPixelsEdited':False}
