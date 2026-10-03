"""Single source adapter/export and immutable native plan; no Unreal calls."""
import importlib.util,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OWNER='scripts/unreal/exterior-context-parcel-boundary-native-study-r43.py'
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=module('_r43_study_guard',ROOT/'scripts/unreal/exterior-context-parcel-boundary-guards-r43.py');n=module('_r43_study_native',ROOT/'scripts/unreal/exterior-context-parcel-boundary-native-r43.py')
def encode_glb(rows):
 data=bytearray();views=[];accessors=[]
 def accessor(values,arity,component,target):
  while len(data)%4:data.append(0)
  start=len(data);fmt='<'+('f'if component==5126 else 'I')*arity
  for value in values:data.extend(struct.pack(fmt,*(value if isinstance(value,list)else [value])))
  view=len(views);views.append({'buffer':0,'byteOffset':start,'byteLength':len(data)-start,'target':target});a={'bufferView':view,'componentType':component,'count':len(values),'type':{1:'SCALAR',2:'VEC2',3:'VEC3'}[arity]}
  if arity==3 and target==34962:a.update(min=[min(v[i]for v in values)for i in range(3)],max=[max(v[i]for v in values)for i in range(3)])
  accessors.append(a);return len(accessors)-1
 meshes=[]
 for r in rows:
  attrs={'POSITION':accessor(r['gltfPositions'],3,5126,34962),'NORMAL':accessor(r['gltfNormals'],3,5126,34962),'TEXCOORD_0':accessor(r['uv0'],2,5126,34962)};ids=accessor(r['indices'],1,5125,34963);meshes.append({'name':r['id'],'primitives':[{'attributes':attrs,'indices':ids,'material':len(meshes),'mode':4}]})
 doc={'asset':{'version':'2.0','generator':OWNER},'scene':0,'scenes':[{'nodes':[0,1,2]}],'nodes':[{'name':r['id'],'mesh':i}for i,r in enumerate(rows)],'meshes':meshes,'materials':[{'name':r['material'],'doubleSided':False,'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':1}}for r in rows],'buffers':[{'byteLength':len(data)}],'bufferViews':views,'accessors':accessors}
 meta=json.dumps(doc,separators=(',',':'),allow_nan=False).encode();meta+=b' '*((-len(meta))%4);data.extend(b'\0'*((-len(data))%4));return struct.pack('<III',0x46546c67,2,28+len(meta)+len(data))+struct.pack('<II',len(meta),0x4e4f534a)+meta+struct.pack('<II',len(data),0x004e4942)+data

def verify_glb(raw,rows):
 g.require(struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw)),'Exact own GLB2 required');size,kind=struct.unpack_from('<II',raw,12);g.require(kind==0x4e4f534a,'JSON chunk required');d=json.loads(raw[20:20+size]);offset=20+size;length,kind=struct.unpack_from('<II',raw,offset);g.require(kind==0x004e4942 and offset+8+length==len(raw),'Complete own binary chunk required');binary=raw[offset+8:];g.require(d['nodes']==[{'name':r['id'],'mesh':i}for i,r in enumerate(rows)]and len(d['meshes'])==3,'Exact identity scene nodes required')
 def values(index):
  a=d['accessors'][index];v=d['bufferViews'][a['bufferView']];arity={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']];fmt='<'+('f'if a['componentType']==5126 else 'I')*arity;stride=struct.calcsize(fmt);result=[list(struct.unpack_from(fmt,binary,v['byteOffset']+i*stride))for i in range(a['count'])];return [x[0]for x in result]if arity==1 else result
 for mesh,r in zip(d['meshes'],rows):
  p=mesh['primitives'][0];g.require(len(mesh['primitives'])==1 and p['mode']==4,'One full triangle section required')
  for attribute,field in [('POSITION','gltfPositions'),('NORMAL','gltfNormals'),('TEXCOORD_0','uv0')]:g.exact(values(p['attributes'][attribute]),r[field],'Written complete encoded source attribute differs')
  g.exact(values(p['indices']),r['indices'],'Written complete source triangle order differs')
 return {'completeEncodedPositionsNormalsUv0IndicesValidated':True,'identityNodes':3,'sourceNormalsNumericNativeReadbackAvailable':False,'encodedTriangles':12566}
def main():
 g.require(not g.STUDY.exists(),'One new source export/plan only');bundle=g.load_contract();g.STUDY.mkdir();glb=g.STUDY/'boundary-authored-r43.glb';raw=encode_glb(bundle['source']['exportRows']);glb.write_bytes(raw);proof=verify_glb(glb.read_bytes(),bundle['source']['exportRows']);g.write(g.STUDY/'export-readback.json',proof)
 owned=[ROOT/'scripts/unreal'/p for p in ('exterior-context-parcel-boundary-guards-r43.py','exterior-context-parcel-boundary-native-r43.py','exterior-context-parcel-boundary-native-study-r43.py','exterior-context-parcel-boundary-materials-r43.py','test_exterior_context_parcel_boundary_native_r43.py','test_exterior_context_parcel_boundary_materials_r43.py')]
 inputs=dict(bundle['base']['report']['inputFiles'])
 def add(p):inputs[str(Path(p).resolve())]=g.sha(p)
 for p in owned+[g.SOURCE,g.READY,g.DECISION,g.CLONE,g.BASE_REPORT,g.BASE_PROCESS,g.BASE_AUDIT,g.IMAGE,Path(bundle['source']['geometryPin']['path']),glb,g.STUDY/'export-readback.json']:add(p)
 for r in [bundle['base']['report'][k]for k in ('savedActorWitness','afterContentInventory','protectedProjectProof','rawInstanceControlsSaved','originalMaterialWitnessSaved','originalTextureWitnessSaved','newSourceNativeMeasurements','baseNativeReport')]:add(g.checked(r))
 for role in ('wood','gravel'):
  for r in bundle['source']['plan']['materials'][role]['maps'].values():add(g.checked({k:r[k]for k in ('path','sha256','bytes')}))
 for r in n.primary_api().values():add(g.checked(r))
 g.require(all(not Path(p).is_relative_to(g.PROJECT)for p in inputs),'Never pin future mutable candidate project files')
 plan={'schema':g.SCHEMA,'schemaVersion':1,'owner':OWNER,'nativeOwner':n.OWNER,'status':'accepted-authored-boundary-source-ready-native-pending','createdAt':n.now(),'binding':bundle['binding'],'sourcePlan':g.pin(g.SOURCE),'sourceGeometry':bundle['source']['geometryPin'],'sourceGlb':g.pin(glb),'exportReadback':g.pin(g.STUDY/'export-readback.json'),'exportRowsSha256':g.digest(bundle['source']['exportRows']),'sourceBinary64ArraysRemainImmutable':True,'basisPolicy':{'gltfPosition':'f32([sourceX,sourceZ,sourceY]/100)','gltfNormal':'f32([sourceNX,sourceNZ,sourceNY])','gltfUv0':'f32(sourceUv0)','exportTriangleCorners':[0,2,1],'nativePosition':'f32([encodedX,encodedZ,encodedY]*100)','nativeIndices':'same ordered nonmirrored GLB indices','sourceRightHandedFaceNormalPreservedInGlb':True,'nativeLeftHandedFaceNormalBasisExplicit':True,'nativeNormalTangentNumericReadbackPerformed':False},'newActorTemplate':bundle['base']['template'],'newActorPolicy':{'sameWorldObservedIdentityTemplate':g.TEMPLATE,'oldActorTransformSettersCalled':False,'newTransformReconstructed':False,'newCollision':'NoCollision','woodMetalCastShadow':True,'gravelCastShadow':False,'allOtherTemplateFlagsRetained':True},'expectedCounts':g.COUNTS,'expectedNewPackageAssets':g.expected_new_packages(),'primaryApi':n.primary_api(),'ownedSources':[g.pin(p)for p in owned],'inputFiles':inputs,'nativeExecuted':False,'gpuExecuted':False,'nativeAppearanceAccepted':False,'nativeCollisionOrContactVerified':False,'legalFencePlacementOrOwnershipClaimed':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'activeOutputPromoted':False}
 g.write(g.PLAN,plan);print(json.dumps({'plan':g.pin(g.PLAN),'sourceGlb':g.pin(glb),'inputFiles':len(inputs),'expectedCounts':g.COUNTS}),flush=True);n.preflight(g.STUDY/'source-preflight',bundle)
if __name__=='__main__':main()
