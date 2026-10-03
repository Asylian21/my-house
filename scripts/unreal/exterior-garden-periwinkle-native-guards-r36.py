"""Stdlib R36 whole-original Periwinkle guard, bound to actual saved R34.

The complete provider attributes remain source evidence. Ordered native F32
positions/UV0/UV1 are a separate gate in the writer; colors and N/T have no
reflected native readback. Full-circle inequalities use actually measured
matrices, without comparing freshly derived libm statistics bit for bit.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-periwinkle-native-guards-r36.py'
SCHEMA = 'brezi-garden-original-periwinkle-composition-native-r36'
PREFIX = '/Game/Brezi/GardenPeriwinkle20261002R36'
TAG = 'BreziGardenPeriwinkleR36:'
CANDIDATE = ROOT/'output/unreal/exterior-20261002-r36a'
STUDY = ROOT/'output/unreal/exterior-garden-periwinkle-20261002-r36-native-study'
PLAN = STUDY/'periwinkle-native-plan.json'
PROPOSAL = ROOT/'output/unreal/exterior-garden-periwinkle-20261002-r36-source-study/periwinkle-source-plan.json'
PROPOSAL_SHA = '93b4bc17203f10b5c14acd036dd942f8d2bf0b99ec1744e6638e7a29502a8b96'
BASE = ROOT/'output/unreal/exterior-20261002-r34a'
BASE_REPORT = BASE/'garden-fern-only-native-report.json'
BASE_SHA = 'd233329bee2ffcb95419c8266ff8c1f50931ba8f642ded23ab20330f1d334cb8'
BASE_AUDIT_SHA = 'c75becbc961f81dc5e0499399c0890eec50baecfabd3a514b5232abd1d7bca1e'
CHECKER_SHA = '5bd91e61ae0cb4f3d437ad359bfddad42b4337cc21e131198f5f825b1e00571b'
MATERIAL_READY = ROOT/'output/unreal/exterior-garden-periwinkle-20261002-r36-material-readiness/material-source-readiness.json'
MATERIAL_READY_SHA = 'b814231523fb01e28a29ee277e1192bb7d6bed650459303f1201b913de71dc53'
CLONE_STATUS = 'verified-original-r34a-independent-apfs-r36-clone-before-major-low-plant-replacement'
MODELS = tuple('periwinkle_plant_%02d_LOD0'%i for i in range(1,7))
COUNTS = {'originalActors':5354,'savedActors':5360,'fullHismComponents':2322,'fullHismInstances':676957,
 'originalGardenRoots':473,'retainedOriginalGardenRoots':53,'preservedR34FernRoots':36,'newOriginalPeriwinkleRoots':384,
 'newMeshAssets':6,'newMaterialGraphs':1,'newTextureObjects':5,'newPipelineAssets':3,'newPackages':15,
 'scopedMaterialGraphs':61,'scopedTextureObjects':96,'contentFiles':4086,'protectedFiles':132}
CONTACT_POLICY = {'maximumArithmeticDeltaCm':1e-7,'scope':'Only minimum world-Z arithmetic after measured positive uniform matrix; not position/UV/topology tolerance',
 'freshDerivedFloatBitEqualityRequired':False,'surveyedGroundContactClaimed':False}


def require(ok,message):
 if not ok: raise RuntimeError(message)
def read(path): return json.loads(Path(path).read_text())
def write(path,value):
 with Path(path).open('x')as file:json.dump(value,file,indent=2,allow_nan=False);file.write('\n')
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def pin(path):
 p=Path(path).resolve();return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def check_pin(row):
 require(isinstance(row,dict)and set(row)in({'path','sha256'},{'path','sha256','bytes'}),'Exact typed file pin required')
 p=Path(row['path']);require(p.is_absolute()and p.is_file()and sha(p)==row['sha256']and ('bytes'not in row or p.stat().st_size==row['bytes']),'Frozen input bytes differ')
 return p
def module(name,filename):
 p=Path(filename);p=p if p.is_absolute()else ROOT/'scripts/unreal'/p
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def exact(a,b,message):
 def encoded(v):
  if isinstance(v,float): return ('float',struct.pack('<d',v))
  if isinstance(v,list): return [encoded(x)for x in v]
  if isinstance(v,dict): return {k:encoded(x)for k,x in v.items()}
  return (type(v).__name__,v)
 require(encoded(a)==encoded(b),message)
def component(row,name):
 rows=[c for c in row['components']if c['name']==name];require(len(rows)==1,'Exact original component membership required');return rows[0]
def cyclic(face):
 return min(tuple(tuple(x)for x in face[i:]+face[:i])for i in range(3))
def f32(value):return struct.unpack('<f',struct.pack('<f',value))[0]


class Accessors:
 def __init__(self,doc,data):self.doc,self.data=doc,data
 def raw(self,index):
  a=self.doc['accessors'][index];v=self.doc['bufferViews'][a['bufferView']]
  require(v['buffer']==0 and 'sparse'not in a,'Dense original single-BIN attributes required')
  width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];code={5126:'f',5123:'H',5125:'I',5121:'B'}[a['componentType']]
  fmt='<'+code*width;size=struct.calcsize(fmt);start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',size)
  require(a['count']>0 and stride>=size and start+(a['count']-1)*stride+size<=len(self.data),'Source accessor extent differs')
  raw=b''.join(self.data[start+i*stride:start+i*stride+size]for i in range(a['count']))
  return [list(struct.unpack_from(fmt,raw,i*size))for i in range(a['count'])],raw


def decode_models(proposal):
 d=read(check_pin(proposal['geometryDescriptor']));doc=read(check_pin(d['providerGltf']));data=check_pin(d['providerBin']).read_bytes()
 raw=check_pin(proposal['sourceGlb']).read_bytes();require(raw[:12]==struct.pack('<4sII',b'glTF',2,len(raw)),'Exact complete GLB header required')
 jl,jt=struct.unpack_from('<II',raw,12);require(jt==0x4e4f534a,'Original glTF JSON chunk required');adapted=json.loads(raw[20:20+jl]);at=20+jl
 bl,bt=struct.unpack_from('<II',raw,at);require(bt==0x004e4942 and at+8+bl==len(raw),'Complete original BIN chunk required')
 require(raw[at+8:at+8+len(data)]==data and all(x==0 for x in raw[at+8+len(data):]),'Provider BIN payload must remain byte exact')
 restored=copy.deepcopy(adapted);restored['buffers'][0]['uri']=doc['buffers'][0]['uri']
 for old,new in zip(doc['nodes'],restored['nodes']):
  if 'translation'in old:new['translation']=old['translation']
 require(restored==doc and len(adapted['nodes'])==6 and all(not any(k in n for k in ('translation','rotation','scale','matrix','children'))for n in adapted['nodes']),
  'Only provider display translations and external BIN URI may change')
 require(d['schema']=='brezi-garden-whole-original-periwinkle-geometry-r36'and d['originalBinPayloadByteExact']is True
  and d['allOriginalAccessorsAndAllSixAttributeSetsByteExact']is True and d['allOriginalIndicesOrderByteExact']is True
  and d['sourcePositionAttributesChanged']is d['nativeGeometryVerified']is d['nativeNormalTangentReadbackAvailable']is d['nativeColor1ReadbackAvailable']is False,
  'Source geometry descriptor overstates native evidence')
 decoder=Accessors(doc,data);models={};wanted={'POSITION','NORMAL','TEXCOORD_0','TEXCOORD_1','COLOR_0','COLOR_1'}
 for node in doc['nodes']:
  name=node['name'];mesh=doc['meshes'][node['mesh']];require(name in MODELS and len(mesh['primitives'])==1,'Exact six complete original models required')
  p=mesh['primitives'][0];require(set(p['attributes'])==wanted and p.get('mode',4)==4,'All six original attributes required')
  desc=d['models'][name];attrs={};arrays={}
  for key,index in p['attributes'].items():
   values,attribute=decoder.raw(index);arrays[key]=values;proof=desc['attributes'][key]
   require(proof['sourceAccessor']==index and proof['accessor']==doc['accessors'][index]and proof['orderedRawAttributeBytesSha256']==hashlib.sha256(attribute).hexdigest(),'Original ordered attribute proof differs')
   attrs[key]=proof
  ids,indexraw=decoder.raw(p['indices']);ids=[x[0]for x in ids];points=[[f32(100*x),f32(100*z),f32(100*y)]for x,y,z in arrays['POSITION']]
  require(len(ids)%3==0 and all(type(i)is int and 0<=i<len(points)for i in ids)and all(math.isfinite(x)for row in points for x in row),'Original complete finite topology required')
  require(desc['sourceIndicesAccessor']==p['indices']and desc['orderedRawIndexBytesSha256']==hashlib.sha256(indexraw).hexdigest()
   and desc['sourceVertices']==len(points)and desc['sourceTriangles']==len(ids)//3 and all(c==[255,255,255,255]for c in arrays['COLOR_0']),
   'Original census/indices/all-white COLOR0 differs')
  exact(desc['originalNativeF32BottomCm'],min(p[2]for p in points),'Serialized original F32 bottom differs')
  models[name]={'id':name,'exportName':name,'canonicalExportName':name,'originalSourceMeshName':mesh['name'],'materialKey':'ph_original_periwinkle_r36','expectedNativeVerticesCm':points,'uv0':arrays['TEXCOORD_0'],
   'uv1':arrays['TEXCOORD_1'],'indices':ids,'attributes':attrs,'vertices':len(points),'triangles':len(ids)//3,
   'originalNativeF32BottomCm':desc['originalNativeF32BottomCm'],'sourceDescriptor':desc,'sourceColor0AllWhite':True,
   'nativeColor0ReadbackAvailable':False,'nativeColor1ReadbackAvailable':False,'nativeNormalTangentReadbackAvailable':False}
 require(set(models)==set(MODELS)and sum(m['triangles']for m in models.values())==34350 and sum(m['vertices']for m in models.values())==31801,'Whole-provider geometry census differs')
 return d,{name:models[name]for name in MODELS}


def saved_base():
 require(sha(BASE_REPORT)==BASE_SHA and sha(ROOT/'scripts/unreal/exterior-garden-fern-only-editor-check-r24.py')==CHECKER_SHA,'Actual R34 report/checker changed')
 checker=module('r36_frozen_actual_r34_checker','exterior-garden-fern-only-editor-check-r24.py');g=checker.g
 r=read(BASE_REPORT);bundle=g.source_bundle();plan=read(check_pin(r['selectedPlan']));preflight=read(check_pin(r['sourcePreflight']))
 summary=checker.validate_saved(r,plan,bundle,preflight)
 process_path=BASE/'garden-fern-only-native-process.json';terminal=read(process_path);raw_path=Path(terminal['processFile']);raw=read(raw_path)
 require(raw['pid']==21209 and raw['code']==0 and raw['signal']is None and raw.get('endedAt') and terminal['reportSha256']==BASE_SHA
  and terminal['sourcePinsUnchangedAfterNative']is True and len(terminal['sourcePinsBeforeNative'])==472
  and sha(raw_path)==terminal['processFileSha256']and sha(terminal['logFile'])==terminal['logSha256'],'Actual closed R34 native process required')
 for path,value in terminal['sourcePinsBeforeNative'].items():require(sha(path)==value,'R34 terminal source bytes changed')
 audit_path=BASE/'root-native-byte-audit-r34a.json';require(sha(audit_path)==BASE_AUDIT_SHA,'Actual current R34 root byteaudit changed');audit=read(audit_path)
 require(audit['nativeReport']==pin(BASE_REPORT)and audit['terminal']==pin(process_path)and audit['currentContentFiles']==4071 and audit['currentProtectedFiles']==132
  and audit['all4192OriginalR29SourceFilesExact']is True and audit['onlyOldCandidateMapChanged']is True,'R34 byte closure differs')
 owner=ROOT/r['owner'];require(owner.is_file()and r['inputFiles'][str(owner)]==sha(owner),'Actual final R34 writer not pinned')
 native=module('r36_actual_saved_r34_native',owner)
 return {'report':r,'reportPin':pin(BASE_REPORT),'process':{'receipt':pin(process_path),'raw':pin(raw_path),'log':pin(terminal['logFile']),'pid':21209,'exitCode':0},
  'audit':pin(audit_path),'witness':read(check_pin(r['savedActorWitness'])),'content':read(check_pin(r['afterContentInventory'])),
  'protected':read(check_pin(r['protectedProjectProof'])),'project':Path(r['project']),'native':native,'bundle':bundle,'plan':plan,'preflight':preflight,'summary':summary}


def validate_source():
 require(sha(PROPOSAL)==PROPOSAL_SHA,'Frozen R36 source proposal changed');p=read(PROPOSAL)
 require(p['schema']=='brezi-garden-original-periwinkle-composition-source-r36'and p['schemaVersion']==1
  and p['owner']=='scripts/unreal/exterior-garden-periwinkle-study-r36.py'and p['status']=='source-all384-low-stars-replaced-whole-original-periwinkle-native-pending'
  and p['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}and p['setbacksMm']=={'street':3000,'east':3000},'Exact original source status/design required')
 for k in ('nativeExecuted','gpuExecuted','nativeApplied','nativeGeometryVerified','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified'):
  require(p[k]is False,'Source proposal fabricates acceptance')
 for path,value in p['inputFiles'].items():require(sha(path)==value,'Frozen proposal input bytes differ')
 d,models=decode_models(p);recipe=read(check_pin(p['materialRecipe']));base=saved_base()
 require(p['actualNativeBase']['report']==base['reportPin']and p['actualNativeBase']['savedActorWitness']==base['report']['savedActorWitness']
  and p['actualNativeBase']['currentByteAudit']==base['audit']and p['actualNativeBase']['retainedGardenControls']==base['report']['retainedGardenControlsSaved'],
  'R36 must bind actual saved R34, not another scene')
 original=read(check_pin(base['report']['retainedGardenControlsSaved']));oldferns=read(check_pin(base['report']['newSourceNativeMeasurements']))
 garden=base['bundle']['source']['garden'];allrows=garden['gardenDetailPlacements']+garden['ornamentalPlacements'];byid={r['id']:r for r in allrows}
 groups={}
 for row in p['retireWholeOriginalGroups']:
  actor=row['actor'];control=original[actor];c=component(base['witness'][actor],row['component'])
  require(row['rootIds']==control['rootIds']and row['currentRootCount']==c['instanceCount']==len(control['rootIds'])and row['currentMesh']==c['mesh']
   and row['originalRecoveredFramesSha256']==digest(control['recoveredValues'])==c['orderedInstanceTransformsSha256']
   and row['originalStoredMatricesSha256']==digest(control['storedMatrices'])and row['mainRandomSeed']==control['mainRandomSeed']
   and row['retireWholeComponentMembers']is True and row['componentActorDeleted']is False and row['retainedMembersInRetiredGroup']==0,
   'Exact current whole-group retirement identity differs')
  groups[row['groupId']]={'actor':actor,'component':row['component'],'witness':base['witness'][actor],'control':control,'rows':[byid[x]for x in control['rootIds']], 'source':row}
 require(len(groups)==4 and [len(g['control']['rootIds'])for g in groups.values()]==[58,47,146,133],'Exactly four current low groups/384 roots required')
 fits=p['proposedPlacements'];retired=[x for g in groups.values()for x in g['control']['rootIds']]
 require(len(fits)==384 and len({r['rootId']for r in fits})==384 and set(retired)==set(p['retiredOriginalLowRootIds'])=={r['rootId']for r in fits},'384 authoritative old roots required')
 for fit in fits:
  old=byid[fit['rootId']];m=models[fit['model']];require(fit['originalRow']==old and fit['sourceContactPositionCm']==old['positionCm']and fit['positionCm'][:2]==old['positionCm'][:2]
   and fit['yawDeg']==old['yawDeg']and fit['scale']==[fit['uniformScale']]*3 and type(fit['uniformScale'])is float and math.isfinite(fit['uniformScale'])and fit['uniformScale']>0,
   'Original XY/yaw/source identity and positive uniform whole-model scale required')
  exact(fit['positionCm'][2],old['positionCm'][2]-fit['uniformScale']*m['originalNativeF32BottomCm'],'Only explicit original model bottom contact offset allowed')
 require(len(p['preservedOriginalHeroRootIds'])==12 and len(p['preservedOriginalFlowerRootIds'])==41 and len(p['preservedR34FernRootIds'])==36
  and set(p['preservedOriginalHeroRootIds'])=={r['id']for r in garden['ornamentalPlacements']}
  and set(p['preservedOriginalFlowerRootIds'])=={r['id']for r in garden['gardenDetailPlacements']if r['role']=='ornamental'}
  and set(p['preservedR34FernRootIds'])=={x for m in oldferns.values()for x in m['rootIds']},'All12 heroes/41 flowers/36 ferns must remain')
 source={'proposal':p,'recipe':recipe,'models':models,'placements':fits,'garden':garden,'descriptor':d,'draft':{'glb':p['sourceGlb'],'geometry':p['geometryDescriptor']}}
 result={'source':source,'base':base,'groups':groups,'originalControls':original,'oldFernMeasurements':oldferns,'reference':base['bundle']}
 validate_native_controls(original,result);return result


source_bundle=validate_source


def validate_native_controls(controls,bundle):
 original=bundle['originalControls'];exact(controls,original,'All437 original raw matrices/order/mainseed/custom data must match actual R34')
 require(len(controls)==19 and sum(len(c['rootIds'])for c in controls.values())==437,'Actual19 components/437 old root mapping required')
 for actor,c in controls.items():
  require(c['numCustomDataFloats']==0 and c['customData']==[]and c['additionalRandomSeedsReadbackAvailable']is False and c['seedRangesReconstructed']is False,
   'Only observed mainseed/zero custom-data controls claimed')
  row=component(bundle['base']['witness'][actor],'Instances');require(row['instanceCount']==len(c['rootIds'])and row['orderedInstanceTransformsSha256']==digest(c['recoveredValues']),'Original current component frame hash differs')
 return True


def expected_original(before,bundle):
 require(before==bundle['base']['witness']and len(before)==5354,'All5354 original actors required');expected=copy.deepcopy(before)
 for g in bundle['groups'].values():
  c=component(expected[g['actor']],g['component']);c['instanceCount']=0;c['orderedInstanceTransformsSha256']=digest([])
 return expected


def empty_controls(bundle):
 rows=copy.deepcopy(bundle['originalControls'])
 for g in bundle['groups'].values():
  c=rows[g['actor']]
  for k in ('rootIds','recoveredValues','storedMatrices','customData'):c[k]=[]
 return rows


def added_expected(template,template_actor,actor,model,mesh,material,measurement):
 old=module('r36_original_template_relocation','exterior-garden-fern-only-native-guards-r34.py')
 row=old.old.guard.yard.guard.clean.relocate_template(copy.deepcopy(template),template_actor,actor)
 row['label']='R36_'+model;row['tags']=sorted(['BreziGenerated',TAG]);row['detailDensityScaling']=False;row['actorTick']=False
 c=component(row,'Instances');c['mesh']=mesh;c['materials']=[material];c['overrideMaterials']=[];c['instanceCount']=len(measurement['rootIds']);c['orderedInstanceTransformsSha256']=digest(measurement['recoveredValues'])
 return row


def validate_measurements(measurements,bundle):
 require(list(measurements)==list(MODELS),'Exact six new model measurement groups required');byid={i:(c,n)for c in bundle['originalControls'].values()for n,i in enumerate(c['rootIds'])}
 for model,m in measurements.items():
  fits=[r for r in bundle['source']['placements']if r['model']==model]
  require(m['rootIds']==[r['rootId']for r in fits]and len(m['inputValues'])==len(m['recoveredValues'])==len(m['storedMatrices'])==len(fits)
   and m['actualUnregisteredMeshlessTransientMeasurement']is True and m['wrappedOriginalXYAndRotationCopied']is True
   and m['hostQuaternionReconstructionPerformed']is False and m['sourceUniformScaleAssigned']is True,'Faithful wrapped old-root transient measurement required')
  for fit,value,recovered,matrix in zip(fits,m['inputValues'],m['recoveredValues'],m['storedMatrices']):
   control,index=byid[fit['rootId']];old=control['recoveredValues'][index];desired=[old[0][:2]+[fit['positionCm'][2]],old[1],fit['scale']]
   exact(value,desired,'Only declared Z bottom offset/uniform scale may alter wrapped input')
   exact(recovered[0],desired[0],'Native recovered declared translation differs');exact(matrix[3][:3],desired[0],'Actual stored declared translation differs')
   require(len(matrix)==4 and all(len(row)==4 and all(type(x)in(int,float)and math.isfinite(x)for x in row)for row in matrix)
    and matrix[0][3]==matrix[1][3]==matrix[2][3]==0 and matrix[3][3]==1,'Finite affine actual stored FMatrix required')
 return True


def source_footprints(measurements,bundle):
 validate_measurements(measurements,bundle);mask=module('r36_original_bed_predicates','exterior-garden-organic-native.py');step=module('r36_original112_step_predicates','exterior-garden-composition-step-guards-r3.py')
 garden=bundle['source']['garden'];steps=step.validated_steps(garden['sourceStepTrianglesCm']);boundaries={k:mask._boundary(v)for k,v in garden['sourceMulchTrianglesCm'].items()};byid={r['rootId']:r for r in bundle['source']['placements']};results=[]
 for model,m in measurements.items():
  points=bundle['source']['models'][model]['expectedNativeVerticesCm']
  for identity,value,matrix in zip(m['rootIds'],m['recoveredValues'],m['storedMatrices']):
   fit=byid[identity];root=value[0];triangles=garden['sourceMulchTrianglesCm'][fit['sourceBedId']]
   require(any(mask._triangle_inside(root[:2],t)for t in triangles),'Measured complete-circle root must be inside original bed union')
   radius=0.;minimum=float('inf');maximum=-float('inf')
   for p in points:
    q=[sum(p[j]*matrix[j][axis]for j in range(3))for axis in range(3)]
    radius=max(radius,math.hypot(q[0],q[1]));minimum=min(minimum,q[2]+matrix[3][2]);maximum=max(maximum,q[2]+matrix[3][2])
   distance=min(mask._distance(root[:2],a,b)for a,b in boundaries[fit['sourceBedId']]);stepsproof=step.circle_clearance(steps,root[:2],radius)
   require(radius<fit['originalRow']['radiusCm']and radius<distance,'Full actually measured source crown circle leaves original crown/bed')
   delta=minimum-fit['sourceContactPositionCm'][2];require(math.isfinite(delta)and abs(delta)<=CONTACT_POLICY['maximumArithmeticDeltaCm'],'Measured original bottom contact arithmetic exceeds declared cap')
   results.append({'rootId':identity,'model':model,'decodedSourceF32VerticesChecked':len(points),'actualStoredMatrix':matrix,'actualContainingCircleRadiusCm':radius,
    'bedBoundaryCircleClearanceCm':distance-radius,'stepBoundaryCircleClearanceCm':stepsproof['circleClearanceCm'],'sourceStepProjection':stepsproof,
    'actualMinimumWorldZCm':minimum,'originalAuthoredContactZCm':fit['sourceContactPositionCm'][2],'contactArithmeticDeltaCm':delta,'contactPolicy':CONTACT_POLICY,
    'actualHeightCm':maximum-minimum,'allSourceVerticesWithinMeasuredContainingCircle':True,'allVerticesAndFullCircleInOriginalBed':True,'fullCircleExcludesOriginalSteps':True,
    'vertexBedFitEstablishedByFullContainingCircle':True,'sourceNativeFloatGeometryProjectionIsGpuReadback':False,'nativeNormalTangentReadbackAvailable':False,
    'freshDerivedStatisticsBitEqualityRequired':False,'surveyedPlacementVerified':False})
 require(len(results)==384 and sum(r['decodedSourceF32VerticesChecked']for r in results)==1981184,'All384 complete measured original crowns required');return results


def package_paths(models):return [PREFIX+'/Geometry/StaticMeshes/'+m['exportName']for m in models.values()]+[PREFIX+'/Pipeline/'+k for k in ('Assets','Materials','Level')]
def validate_content(before,after,packages,map_changed=True):
 require(len(before)==4071 and len(packages)==len(set(packages))==15,'Exactly15 owned new packages required');relative={p.removeprefix('/Game/')+'.uasset'for p in packages}
 require(all(p.startswith(PREFIX+'/')and '.'not in p.removeprefix(PREFIX+'/')for p in packages)and not set(before)&relative and set(after)==set(before)|relative,'Only exact15 owned R36 packages allowed')
 changed=sorted(k for k in before if before[k]!=after[k]);require(changed==(['Brezi/Maps/Brezi.umap']if map_changed else []),'Original content outside map changed')
 return {'changedOriginalFiles':changed,'newOwnedPackages':sorted(relative),'originalContentFiles':4071,'savedContentFiles':4086,'newPackages':15}


def validate_clone(base):
 path=CANDIDATE/'garden-periwinkle-project-clone.json';require(sha(path)=='24a2afa5e0f239edd236fa401b4dda59a034eff5deb93718bb2329b69f8c84ee','Original R36 initial clone receipt changed');c=read(path);project=CANDIDATE/'Project/BreziTwin'
 require(c['schema']==SCHEMA and c['status']==CLONE_STATUS and c['sourceProject']==str(base['project'])and c['project']==str(project)
  and c['nativeBaseReport']==base['reportPin']and c['sourceProposal']is c['selectedPlan']is c['sourcePreflight']is None and c['nativeExecuted']is False
  and c['fileCount']==len(c['files'])==4203 and c['contentFiles']==4071 and c['protectedFiles']==132,'Exact typed original R34 clone provenance required')
 expected={'Content/'+k:v for k,v in base['content'].items()};expected.update(base['protected']);seen=set()
 for row in c['files']:
  a,b=Path(row['source']),Path(row['destination']);relative=b.relative_to(project).as_posix()
  require(relative in expected and relative not in seen and a==base['project']/relative and row['independentInodes']is True
   and {k:row[k]for k in ('sha256','bytes')}==expected[relative]and a.stat().st_size==row['bytes']
   and (a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),'Immutable initial clone membership/inode/source metadata differs')
  seen.add(relative)
 require(seen==set(expected),'Exact4203 initial clone membership differs');return pin(path)


def material_readiness():
 require(sha(MATERIAL_READY)==MATERIAL_READY_SHA,'Frozen R36 material readiness changed');r=read(MATERIAL_READY)
 require(r['schema']=='brezi-original-r36-periwinkle-material-source-readiness'
  and r['status']=='source-five-original-maps-API-contract-and11CPU-mutation-fixtures-ready-native-pending'
  and r['inputPinsBefore']==r['inputPinsAfter']and r['allInputPinsUnchanged']is True
  and r['tests']=={'passed':11,'failed':0,'exitCode':0,'nativeApiMocked':True}
  and r['selectedSourcePlan']==pin(PROPOSAL)and r['sourceRecipe']==read(PROPOSAL)['materialRecipe']
  and r['expectedMaterialGraphs']==1 and r['expectedTextureObjects']==5 and r['expectedMaterialPackages']==6
  and r['nativeMaterialApplied']is r['nativeAppearanceAccepted']is r['fullPhotorealismAccepted']is r['performanceAccepted']is False,
  'Owned source-only material closure differs')
 for row in r['inputPinsBefore']:check_pin(row)
 check_pin(r['actualCpuFixtureProcess'])
 return r


def validate_plan(bundle=None):
 # The writer/study may reuse its just-validated source packet. Native main
 # invokes the default branch; all plan/header/pin checks still execute here.
 if bundle is None:bundle=validate_source()
 else:
  require(set(bundle)=={'source','base','groups','originalControls','oldFernMeasurements','reference'}
   and bundle['source']['proposal']==read(PROPOSAL)and bundle['base']['reportPin']==pin(BASE_REPORT)
   and bundle['reference']is bundle['base']['bundle'],'Only the exact already-validated actual R34 source packet may be reused')
 p=read(PLAN)
 require(p['schema']==SCHEMA and p['schemaVersion']==1 and p['owner']=='scripts/unreal/exterior-garden-periwinkle-native-study-r36.py'
  and p['nativeOwner']=='scripts/unreal/exterior-garden-periwinkle-native-r36.py'
  and p['status']=='source-ready-exact-saved-r34-whole384-original-periwinkle-native-pending'
  and p['sourceProposal']==pin(PROPOSAL)and p['baseNativeReport']==bundle['base']['reportPin']and p['baseNativeProcess']==bundle['base']['process']
  and p['baseCurrentByteAudit']==bundle['base']['audit']and p['candidateOutput']==str(CANDIDATE)and p['projectClone']==validate_clone(bundle['base'])
  and p['expectedCounts']==COUNTS and p['newGroupOrder']==list(MODELS)and p['materialReadiness']==pin(MATERIAL_READY),'Exact actual R34/native R36 binding required')
 require(p['retiredRootIds']==[r['rootId']for r in bundle['source']['placements']]and p['wholeGroupRetirements']==bundle['source']['proposal']['retireWholeOriginalGroups']
  and p['activeDesign']==bundle['source']['proposal']['activeDesign']and p['setbacksMm']=={'street':3000,'east':3000},'Whole384 retirement/design differs')
 material_readiness()
 names={'exterior-garden-periwinkle-native-study-r36.py','exterior-garden-periwinkle-native-guards-r36.py','exterior-garden-periwinkle-native-r36.py','exterior-garden-periwinkle-materials-r36.py','test_exterior_garden_periwinkle_native_r36.py','test_exterior_garden_periwinkle_native_guards_r36.py'}
 require(set(p['ownedSources'])==names,'Exact six owned native sources required')
 for name,row in p['ownedSources'].items():require(Path(row['path'])==ROOT/'scripts/unreal'/name,'Owned source path differs');check_pin(row)
 for path,value in p['inputFiles'].items():require(sha(path)==value,'Consumed source changed')
 for k in ('nativeApplied','nativeExecuted','gpuExecuted','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified','yardIntegrationApplied','surveyedPlacementVerified'):require(p[k]is False,'Source nativeplan fabricates acceptance')
 return p,bundle
