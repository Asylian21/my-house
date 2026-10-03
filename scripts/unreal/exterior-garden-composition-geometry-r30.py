"""NEW source-only R30 export: five whole originals, declared bottom shifts only.

Provider NORMAL/UV0/index bits and order survive. POSITION keeps X/Z and
receives one explicitly derived F32 Y bottom translation. No tangent attribute
is invented. Native proof is pending and uses original winding, not a flip.
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

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-garden-composition-geometry-r30.py'
OUT=ROOT/'output/unreal/exterior-garden-composition-20261002-r30-geometry-study'
PROPOSAL=ROOT/'output/unreal/exterior-garden-composition-20261002-r30-study/garden-composition-source-proposal.json'
PROPOSAL_SHA='bd08b2c9bddc5e8ec4389df84afa841822993c0bf09f920663dce614654a7dd9'
PREFIX='/Game/Brezi/GardenComposition20261002R30'
MODELS=['fern_02_a','fern_02_c','fern_02_d','grass_medium_01_tall_a_LOD0','grass_medium_01_tall_c_LOD0']


def require(ok,msg):
 if not ok:raise RuntimeError(msg)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):
 p=Path(p).resolve();return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def write(p,x):
 with Path(p).open('x')as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')


def accessor(doc,buffers,i):
 a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
 require(not a.get('sparse')and not a.get('normalized'),'Unsupported source accessor')
 n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];code,size={5126:('f',4),5123:('H',2),5125:('I',4)}[a['componentType']]
 base=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',n*size);raw=buffers[v['buffer']]
 require(stride>=n*size and base>=v.get('byteOffset',0)and base+(a['count']-1)*stride+n*size<=v.get('byteOffset',0)+v['byteLength']<=len(raw),'Accessor escapes buffer')
 rows=[struct.unpack_from('<'+code*n,raw,base+k*stride)for k in range(a['count'])]
 require(all(math.isfinite(x)for r in rows for x in r),'Nonfinite source attributes')
 encoded=b''.join(struct.pack('<'+code*n,*r)for r in rows)
 return rows,encoded,a['componentType'],a['type']


def source_models():
 require(sha(PROPOSAL)==PROPOSAL_SHA,'Frozen R30 proposal changed');p=read(PROPOSAL)
 require(p['schema']=='brezi-source-only-garden-composition-proposal-r30'and p['replacementCount']==38 and p['retainedRootCount']==435
  and p['nativeApplied']is False and p['fullPhotorealismAccepted']is False,'Typed frozen38/435 source required')
 for row in p['inputFiles']:require(pin(row['path'])==row,'Frozen R30 input changed')
 paths=[ROOT/'output/unreal/exterior-ph-fern-reference-20261002-r1/fern_02_2k.gltf',ROOT/'output/unreal/exterior-ph-vegetation-reference-20261001-r1/grass_medium_01/grass_medium_01_2k.gltf']
 result={}
 for path in paths:
  d=read(path);raw=[(path.parent/b['uri']).read_bytes()for b in d['buffers']]
  require(not d.get('extensionsUsed')and not d.get('skins')and not d.get('animations'),'Unreviewed original model extension')
  for node in d['nodes']:
   if node['name']not in MODELS:continue
   require(set(node)<= {'name','mesh','translation'},'Unreviewed provider display transform')
   mesh=d['meshes'][node['mesh']];require(len(mesh['primitives'])==1,'Exactly one original primitive required');primitive=mesh['primitives'][0]
   require(set(primitive['attributes'])=={'POSITION','NORMAL','TEXCOORD_0'}and primitive.get('mode',4)==4,'Original attributes/mode differ')
   attrs={k:accessor(d,raw,i)for k,i in primitive['attributes'].items()};index=accessor(d,raw,primitive['indices'])
   pos=attrs['POSITION'][0];norm=attrs['NORMAL'][0];uv=attrs['TEXCOORD_0'][0];indices=[r[0]for r in index[0]]
   require(len(pos)==len(norm)==len(uv)and len(indices)%3==0 and all(0<=i<len(pos)for i in indices),'Original topology/count differs')
   bottom=min(v[1]for v in pos);rooted=[(v[0],f32(v[1]-bottom),v[2])for v in pos]
   name='R30_'+node['name'].removesuffix('_LOD0')+'_LOD0'
   result[node['name']]={'id':node['name'],'exportName':name,'materialKey':'fern'if node['name'].startswith('fern_')else'grass',
    'providerGltf':pin(path),'providerBinary':pin(path.parent/d['buffers'][0]['uri']),'displayTranslationNotApplied':node.get('translation',[0,0,0]),
    'vertices':len(pos),'triangles':len(indices)//3,'sourceBottomYF32Meters':bottom,'derivedBottomShiftOnly':True,'sourceTangentsPresent':False,
    'sourceAttributeByteSha256':{k:hashlib.sha256(v[1]).hexdigest()for k,v in attrs.items()},'sourceIndexByteSha256':hashlib.sha256(index[1]).hexdigest(),
    'derivedPositionByteSha256':hashlib.sha256(b''.join(struct.pack('<fff',*v)for v in rooted)).hexdigest(),
    'positionMeters':[list(v)for v in rooted],'normal':[list(v)for v in norm],'uv0':[list(v)for v in uv],'indices':indices,
    'indexComponentType':index[2],'expectedNativeVerticesCm':[[f32(100*x),f32(100*z),f32(100*y)]for x,y,z in rooted],
    'expectedNativeNormalTangentReadbackAvailable':False,'sourceOriginalWindingPreserved':True,
    '_originalPosition':pos,'_attributeBytes':attrs,'_indexBytes':index[1]}
 require(set(result)==set(MODELS)and sum(r['triangles']for r in result.values())==4478,'Five exact original4478 triangle forms required')
 return p,result


def glb_bytes(models):
 binary=bytearray();views=[];accessors=[];meshes=[];nodes=[]
 def add(rows,raw,component,kind,target):
  binary.extend(b'\0'*((-len(binary))%4));offset=len(binary);binary.extend(raw);view=len(views)
  views.append({'buffer':0,'byteOffset':offset,'byteLength':len(raw),'target':target});a={'bufferView':view,'componentType':component,'count':len(rows),'type':kind}
  if kind=='VEC3'and component==5126:a.update(min=[min(r[k]for r in rows)for k in range(3)],max=[max(r[k]for r in rows)for k in range(3)])
  accessors.append(a);return len(accessors)-1
 for key in MODELS:
  row=models[key];position=row['positionMeters'];attrs={'POSITION':add(position,b''.join(struct.pack('<fff',*v)for v in position),5126,'VEC3',34962)}
  for role in ['NORMAL','TEXCOORD_0']:
   src=row['_attributeBytes'][role];attrs[role]=add(*src,34962)
  indices=add([(v,)for v in row['indices']],row['_indexBytes'],row['indexComponentType'],'SCALAR',34963)
  meshes.append({'name':row['exportName'],'primitives':[{'attributes':attrs,'indices':indices,'mode':4}]});nodes.append({'name':row['exportName'],'mesh':len(meshes)-1})
 doc={'asset':{'version':'2.0','generator':OWNER},'scene':0,'scenes':[{'nodes':list(range(5))}],'nodes':nodes,'meshes':meshes,'accessors':accessors,'bufferViews':views,'buffers':[{'byteLength':len(binary)}]}
 encoded=json.dumps(doc,separators=(',',':'),allow_nan=False).encode();encoded+=b' '*((-len(encoded))%4);binary.extend(b'\0'*((-len(binary))%4))
 return struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary


def decode_export(raw,models):
 magic,version,length=struct.unpack_from('<III',raw);require((magic,version,length)==(0x46546c67,2,len(raw)),'GLB header differs')
 size,kind=struct.unpack_from('<II',raw,12);require(kind==0x4e4f534a,'JSON chunk missing');d=json.loads(raw[20:20+size]);size2,kind2=struct.unpack_from('<II',raw,20+size)
 require(kind2==0x004e4942 and 28+size+size2==len(raw),'BIN chunk differs');binary=raw[28+size:]
 require(len(d['nodes'])==len(d['meshes'])==5 and not d.get('materials')and not d.get('textures'),'Only five geometry forms required')
 for i,key in enumerate(MODELS):
  row=models[key];require(d['nodes'][i]=={'name':row['exportName'],'mesh':i},'Node identity/transform changed');p=d['meshes'][i]['primitives'][0]
  require(set(p['attributes'])=={'POSITION','NORMAL','TEXCOORD_0'}and p['mode']==4,'Original attributes changed')
  for role in ['NORMAL','TEXCOORD_0']:
   require(accessor(d,[binary],p['attributes'][role])[1]==row['_attributeBytes'][role][1],'Original attribute bytes changed: '+role)
  require(accessor(d,[binary],p['indices'])[1]==row['_indexBytes'],'Original triangle order/winding changed')
  require(accessor(d,[binary],p['attributes']['POSITION'])[0]==[tuple(v)for v in row['positionMeters']],'Declared derived F32 root positions differ')
 return {'originalNormalUvIndexBytesExact':True,'positionBottomShiftExplicitF32':True,'providerPositionXZBitsPreserved':True,'originalWindingPreserved':True,
  'nodes':5,'triangles':4478,'nativeReadbackPerformed':False,'sourceTangentsInvented':False}


def main():
 require(not OUT.exists(),'Fresh isolated geometry directory required');proposal,models=source_models();OUT.mkdir()
 data=glb_bytes(models);audit=decode_export(data,models);(OUT/'garden-composition-originals.glb').write_bytes(data)
 descriptor={'schema':'brezi-garden-composition-original-geometry-r30','owner':OWNER,'status':'source-original-geometry-exported-native-pending',
  'sourceProposal':pin(PROPOSAL),'models':[{k:v for k,v in models[key].items()if not k.startswith('_')}for key in MODELS],
  'originalSourceAttributesPreservedExceptDeclaredBottomShift':True,'nativeNormalTangentReadbackAvailable':False,'nativeApplied':False,'audit':audit}
 write(OUT/'geometry-descriptor.json',descriptor)
 fern_delegate=ROOT/'scripts/unreal/exterior-garden-fern-materials-r25.py';grass_delegate=ROOT/'scripts/unreal/exterior-curved-grass-materials-r3.py'
 grass=module('r30_source_original_grass_recipe',grass_delegate)
 recipes={'schema':'brezi-garden-composition-material-recipes-r30','owner':OWNER,'status':'source-two-original-map-recipes-native-pending','sourceProposal':pin(PROPOSAL),'prefix':PREFIX,
  'newOwnTag':'BreziGardenCompositionR30:','fernSourceStudy':pin(ROOT/'output/unreal/exterior-garden-fern-20261002-r25-study/fern-pilot-source-plan.json'),
  'fernDelegate':pin(fern_delegate),'grassDelegate':pin(grass_delegate),'grassRecipe':grass.canonical_recipe(),'materialCount':2,'textureObjectCount':8,
  'nativeAppearanceAccepted':False,'sourcePixelsEdited':False,'nativeApplied':False}
 write(OUT/'material-recipes.json',recipes)
 plan={'schema':'brezi-garden-composition-native-source-draft-r30','owner':OWNER,'status':'source-geometry-exported-native-base-pending','sourceProposal':pin(PROPOSAL),
  'geometry':pin(OUT/'geometry-descriptor.json'),'glb':pin(OUT/'garden-composition-originals.glb'),'materialRecipes':pin(OUT/'material-recipes.json'),'producer':pin(ROOT/OWNER),
  'originalRootsReplaced':38,'sourceRowsRetained':435,'newRootPopulation':0,'newMeshAssets':5,'newMaterialGraphs':2,'newTextureObjects':8,'newImportPipelineAssets':3,
  'proposedNewNonemptyHismGroups':5,'emptiedOriginalOneMemberHeroComponents':2,'partiallyFilteredOriginalComponents':2,
  'nativeBase':{'report':None,'process':None,'selectionComplete':False,'required':'Actual saved R29 only after root process exit0; no future receipt fabricated'},
  'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False}
 write(OUT/'source-native-draft.json',plan);print(json.dumps({'draft':pin(OUT/'source-native-draft.json'),'geometry':pin(OUT/'geometry-descriptor.json'),'glb':pin(OUT/'garden-composition-originals.glb'),'materialRecipes':pin(OUT/'material-recipes.json'),'audit':audit}))


if __name__=='__main__':main()
