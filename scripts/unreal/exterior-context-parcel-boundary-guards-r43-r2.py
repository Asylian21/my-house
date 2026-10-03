"""Exact selected R39c + authored R43 source contract. No historical replay."""
import copy, hashlib, importlib.util, json, math, struct, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-parcel-boundary-guards-r43-r2.py'
NATIVE_OWNER='scripts/unreal/exterior-context-parcel-boundary-native-r43-r2.py'
SCHEMA='brezi-selected-r39c-authored-open-boundary-native-r43'
PREFIX='/Game/Brezi/ParcelBoundary20261002R43';TAG='BreziParcelBoundaryR43:'
MATERIAL_ROLES=('wood','metal','gravel')
BASE=ROOT/'output/unreal/exterior-20261002-r39c';CANDIDATE=ROOT/'output/unreal/exterior-20261002-r43b';PROJECT=CANDIDATE/'Project/BreziTwin'
STUDY=ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-native-study-r2';PLAN=STUDY/'boundary-native-plan-r2.json'
SOURCE=ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-source-uv-repair-r2/boundary-source-plan-r2.json'
SOURCE_SHA='614b2f0857bdb90debef3cde81b16b0311791672b7640dbc7fc2971ca8422998'
GEOMETRY_SHA='17043c70469121d67c82878c0d4878ee6edda52ddc69639074f426d73abc5f2b'
DECISION=ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-root-source-selection-r1/root-source-diagram-selection-r1.json'
DECISION_SHA='cf2e3a46d85bd9a9322ff3e704da2d87ab7c67278b6fa781083eb80d2e4429d9'
READY=SOURCE.parent/'source-readiness/source-readiness.json';READY_SHA='ced49638f300366ce6a666cb0acb5a829f240d0a3effeafb138a9e6f6503363e'
CLONE=CANDIDATE/'garden-boundary-project-clone-r43-r2.json';CLONE_SHA='9afc1c6b8009497c122080cd6f371c1fe3119e83627443afcbdeeaf3f74f403d'
BASE_REPORT=BASE/'neighbor-props-native-report-r3.json';BASE_REPORT_SHA='118f451095730e2ff0e62304d959626d4a81be53f03e41dd2229fe91831f4da5'
BASE_PROCESS=BASE/'neighbor-props-native-r39-r3-process.json';BASE_PROCESS_SHA='2bbb88ee2d71a0d81469c267f263c22beaea4f2d49eba05618d9c8896c2e96e0'
BASE_AUDIT=BASE/'root-native-success-byte-audit-r39c-r3.json';BASE_AUDIT_SHA='7f70d6eb3c59e87305313ba35b7cf7324fde14e80507b5d06e3eaecce7f17ad5'
IMAGE=ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-image-base-selection-r1/root-image-base-selection-r1.json';IMAGE_SHA='211bacaa3573b94542ca97f6820a070dfa50f45db4f0ab4ec3731bece8af076d'
TEMPLATE='/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.StaticMeshActor_197'
IDENTITY=[[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]]
COUNTS={'beforeActors':5368,'savedActors':5371,'fullHismComponents':2329,'fullHismInstances':678205,'newStaticMeshActors':3,'newMeshes':3,'sourceMasterTriangles':12566,'newMaterialGraphs':3,'newTextureObjects':6,'newPipelineAssets':3,'newPackages':15,'beforeMaterialGraphs':69,'savedMaterialGraphs':72,'beforeTextureObjects':108,'savedTextureObjects':114,'beforeContentFiles':4124,'savedContentFiles':4139,'protectedFiles':132}
def require(ok,msg):
 if not ok:raise RuntimeError(msg)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):
 p=Path(p).resolve();return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def checked(r):
 require(type(r)is dict and set(r)=={'path','sha256','bytes'},'Exact file pin required');p=Path(r['path']);require(p.is_absolute()and p.resolve()==p and not p.is_symlink()and pin(p)==r,'Immutable consumed pin changed: '+str(p));return p
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x')as f:json.dump(v,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def module(n,p):
 p=checked(p)if isinstance(p,dict)else Path(p);s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def exact(a,b,msg):
 if isinstance(a,(int,float))and not isinstance(a,bool)and isinstance(b,(int,float))and not isinstance(b,bool):require(math.isfinite(a)and math.isfinite(b)and struct.pack('<d',float(a))==struct.pack('<d',float(b)),msg)
 elif isinstance(a,(list,tuple))and isinstance(b,type(a)):
  require(len(a)==len(b),msg)
  for x,y in zip(a,b):exact(x,y,msg)
 elif isinstance(a,dict)and isinstance(b,dict):
  require(set(a)==set(b),msg)
  for k in a:exact(a[k],b[k],msg)
 else:require(type(a)is type(b)and a==b,msg)
def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
def expected_binding():
 for p,s in ((SOURCE,SOURCE_SHA),(DECISION,DECISION_SHA),(READY,READY_SHA),(CLONE,CLONE_SHA),(BASE_REPORT,BASE_REPORT_SHA),(BASE_PROCESS,BASE_PROCESS_SHA),(BASE_AUDIT,BASE_AUDIT_SHA),(IMAGE,IMAGE_SHA)):require(sha(p)==s,'Selected immutable input changed: '+str(p))
 return {'schema':SCHEMA,'schemaVersion':2,'nativeOwner':NATIVE_OWNER,'repairSchema':REPAIR_SCHEMA,'actorSpawnRepairEvidence':repair_evidence(),'sourcePlan':pin(SOURCE),'rootSourceDecision':pin(DECISION),'sourceReadiness':pin(READY),'selectedNativeReport':pin(BASE_REPORT),'selectedNativeProcess':pin(BASE_PROCESS),'selectedCurrentByteAudit':pin(BASE_AUDIT),'selectedRootImageDecision':pin(IMAGE),'projectClone':pin(CLONE),'candidateProject':str(PROJECT),'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'activeOutputPromoted':False}
def require_native_binding(binding):require(digest(binding)==digest(expected_binding()),'Exact selected source/base/clone binding required');return True
def export_rows(geometry):
 rows=[]
 for m in geometry['meshes']:
  p=[[f32(v[0]/100),f32(v[2]/100),f32(v[1]/100)]for v in m['verticesCm']];indices=[m['indices'][i+j]for i in range(0,len(m['indices']),3)for j in (0,2,1)]
  rows.append({'id':m['id'],'material':m['materialKey'],'sourceVerticesCm':m['verticesCm'],'sourceNormals':m['normals'],'sourceUv0':m['uv0'],'sourceIndices':m['indices'],'sourceObjectRanges':m['sourceObjectRanges'],'gltfPositions':p,'gltfNormals':[[f32(n[0]),f32(n[2]),f32(n[1])]for n in m['normals']],'uv0':[[f32(v)for v in uv]for uv in m['uv0']],'indices':indices,'expectedNativeVerticesCm':[[f32(v[0]*100),f32(v[2]*100),f32(v[1]*100)]for v in p],'exportWindingPolicy':'source-triangle-corners-0-2-1','sourceGeometrySha256':GEOMETRY_SHA})
 return rows
def validate_export(row,source):
 require(row['id']==source['id']and row['material']==source['materialKey']and row['sourceGeometrySha256']==GEOMETRY_SHA,'Authored source identity differs')
 exact(row,export_rows({'meshes':[source]})[0],'Complete source P/N/UV/index and encoded F32 export differs')
 require(len(row['indices'])//3 in (3256,9308,2)and all(type(i)is int and 0<=i<len(row['gltfPositions'])for i in row['indices']),'Complete source topology required');return True
def texture_subset(full,snapshot):
 require(full['size']==snapshot['pixels']and full['sourceEncoding']==snapshot['sourceEncoding']and full['alphaCoverageThresholds']==snapshot['alphaCoverageThresholds'],'Selected new texture source dimensions/encoding/alpha changed')
 for k,v in snapshot.items():
  if k in ('pixels','sourceEncoding','alphaCoverageThresholds'):continue
  require(full['values'][k]==v,'Selected new texture policy changed: '+k)
def load_contract():
 binding=expected_binding();plan=read(SOURCE);geometry=read(checked(plan['geometry']));decision=read(DECISION);clone=read(CLONE);report=read(BASE_REPORT);process=read(BASE_PROCESS);audit=read(BASE_AUDIT)
 require(plan['schemaVersion']==2 and sha(plan['geometry']['path'])==GEOMETRY_SHA and plan['selectedNativeBase']==pin(BASE_REPORT)and plan['rootImageDecision']==pin(IMAGE),'Only corrected selected source R2 permitted')
 require(decision['correctedSourcePlan']==pin(SOURCE)and decision['geometry']==plan['geometry']and decision['status']=='accepted-only-for-native-trial-three-authored-open-boundary-masters'and decision['scope']['existingGeometryRootsAndCollisionMustRemainExact'],'Exact scoped source-diagram decision required')
 require(report['nativeProcessId']==94572 and report['nativeApplied']is True and report['savedMapUnloadedReloaded']is True and report['sourceInputsUnchanged']is True and report['status']=='verified-saved-six-whole-original-neighbor-prop-assemblies','Actual saved R39c required')
 require(process['reportSha256']==BASE_REPORT_SHA and process['sourcePinsUnchangedAfterNative']is True and len(process['sourcePinsBeforeNative'])==1294 and audit['exitCode']==audit['rootSessionClosedExitCode']==0 and audit['nativeReport']==pin(BASE_REPORT)and audit['nativeProcess']==pin(BASE_PROCESS),'Actual terminal/current R39c proof required')
 for p,s in process['sourcePinsBeforeNative'].items():require(sha(p)==s,'Actual parent terminal pin changed: '+p)
 witness=read(checked(report['savedActorWitness']));require(len(witness)==5368 and digest(witness)==report['savedActorWitnessSha256'],'Complete current source actor witness required')
 mats=read(checked(report['originalMaterialWitnessSaved']));tex=read(checked(report['originalTextureWitnessSaved']));require(len(mats)==66 and len(tex)==97,'Complete actual old graph/texture saved records required')
 records={a:{'graph':v['graph'],'route':v['reader'],'aux':v['aux'],'usage':v['usage'],'usageRecorded':True,**({'metadata':v['metadata']}if 'metadata'in v else {})}for a,v in mats.items()}
 for v in report['materialReport']['materials'].values():
  require(v['compileErrors']==[]and digest(v['graph'])==v['graphSha256'],'Selected original new graph receipt differs')
  records[v['asset']]={'graph':v['graph'],'route':'basic','aux':None,'usage':{'instancedStaticMeshes':True},'usageRecorded':False,'metadata':v['metadata']}
  for t in v['textures'].values():require(t['asset']not in tex,'Distinct original new texture required');tex[t['asset']]={'asset':t['asset'],'partialSnapshot':t['snapshot'],'metadata':t['metadata']}
 require(len(records)==69 and len(tex)==108,'Exact69/108 selected native asset scope required')
 r38report=read(checked(report['baseNativeReport']));r37report=read(checked(r38report['baseNativeReport']));native_path=ROOT/r38report['owner'];require(sha(native_path)==report['inputFiles'][str(native_path)],'Protected actual observer changed')
 native=module('_r43_frozen_r38_observers',native_path)
 template=witness[TEMPLATE];require(template['class']=='/Script/Engine.StaticMeshActor'and len(template['components'])==1,'Authentic identity policy template required');exact(template['transform'],IDENTITY,'Recorded template actor identity differs');exact(template['components'][0]['transform'],IDENTITY,'Recorded template component identity differs')
 require(template['components'][0]['collision']=='<CollisionEnabled.NO_COLLISION: 0>'and template['components'][0]['navigation']is False,'Template visual-only scope differs')
 source={'planPin':pin(SOURCE),'plan':plan,'geometryPin':plan['geometry'],'geometry':geometry,'exportRows':export_rows(geometry),'glbPin':None}
 require({r['material']for r in source['exportRows']}==set(MATERIAL_ROLES)and sum(len(r['indices'])//3 for r in source['exportRows'])==12566,'Three complete authored masters required')
 for row,m in zip(source['exportRows'],geometry['meshes']):validate_export(row,m)
 for role in ('wood','gravel'):
  for m in plan['materials'][role]['maps'].values():checked({k:m[k]for k in ('path','sha256','bytes')});require(m['pixelEdits']is False,'Original photo pixels must remain immutable')
 base={'report':report,'reportPin':pin(BASE_REPORT),'processPin':pin(BASE_PROCESS),'auditPin':pin(BASE_AUDIT),'savedWitness':witness,'content':read(checked(report['afterContentInventory'])),'protected':read(checked(report['protectedProjectProof'])),'project':BASE/'Project/BreziTwin','materialRecords':records,'textureRecords':tex,'rawControls':read(checked(report['rawInstanceControlsSaved'])),'measurements':read(checked(report['newSourceNativeMeasurements'])),'native':native,'readerPacket':{'base':{'report':r37report}},'template':template}
 require(len(base['content'])==4124 and len(base['protected'])==132 and len(base['rawControls'])==2325,'Current bytes/raw original control shapes differ')
 validate_clone_header(clone,base,binding);return {'source':source,'base':base,'binding':binding}
def validate_clone_header(clone,base,binding):
 require(clone['schema']=='brezi-image-selected-saved-r39c-garden-boundary-project-clone-r43'and clone['schemaVersion']==1 and clone['status']=='verified-byte-identical-independent-apfs-image-selected-r39c-before-authored-garden-boundaries-r43'and clone['sourceNativeReport']==binding['selectedNativeReport']and clone['sourceNativeProcess']==binding['selectedNativeProcess']and clone['sourceCurrentByteAudit']==binding['selectedCurrentByteAudit']and clone['rootImageBaseSelection']==binding['selectedRootImageDecision']and clone['project']==str(PROJECT)and clone['sourceProject']==str(base['project'])and clone['nativeExecuted']is False and clone['previousFailedAttemptAudit']==pin(FAILURE_AUDIT),'Initial independent clone provenance differs')
 expected={'Content/'+k:v for k,v in base['content'].items()};expected.update(base['protected']);require(clone['fileCount']==len(clone['files'])==len(expected)==4256,'Initial clone census differs');seen=set()
 for row in clone['files']:
  dst=Path(row['destination']);rel=dst.relative_to(PROJECT).as_posix();require(rel not in seen and row['source']==str(base['project']/rel)and row['independentInodes']is True and {k:row[k]for k in ('sha256','bytes')}==expected[rel],'Initial clone row differs');seen.add(rel)
 require(seen==set(expected),'Initial clone scope differs')
def inventories(project):
 result={}
 for p in Path(project).rglob('*'):
  if p.is_file()and (p.relative_to(project).parts[0]in ('Content','Config','Source','Binaries')or p.relative_to(project).as_posix()=='BreziTwin.uproject'):
   require(not p.is_symlink(),'Project symlink forbidden');result[p.relative_to(project).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
 return {k[8:]:v for k,v in result.items()if k.startswith('Content/')},{k:v for k,v in result.items()if not k.startswith('Content/')}
def validate_clone(bundle,after=False):
 base=bundle['base'];validate_clone_header(read(CLONE),base,bundle['binding'])
 for row in read(CLONE)['files']:
  src,dst=Path(row['source']),Path(row['destination']);require(src.stat().st_ino!=dst.stat().st_ino,'Independent cloned files required')
 content,protected=inventories(PROJECT);original,original_protected=inventories(base['project']);require(original==base['content']and protected==original_protected==base['protected'],'Original canonical bytes or protected132 changed')
 if not after:require(content==base['content'],'Pristine R43 Content must equal selected R39c')
 return content
def expected_new_packages():
 assets=[]
 for role in MATERIAL_ROLES:
  name='M_boundary_'+role+'_r43';assets.append(PREFIX+'/Materials/'+name+'.'+name)
  name='boundary_'+role+'_r43';assets.append(PREFIX+'/Geometry/StaticMeshes/'+name+'.'+name)
 for role in ('wood','gravel'):
  for channel in ('diffuse','normal','roughness'):
   name='T_'+role+'_'+channel+'_r43';assets.append(PREFIX+'/Textures/'+name+'.'+name)
 for n in ('Assets','Materials','Level'):assets.append(PREFIX+'/Pipeline/'+n+'.'+n)
 require(len(set(assets))==15,'Exact15 packages required');return sorted(assets)
def validate_content_delta(before,after):
 require(len(before)==4124 and len(after)==4139 and set(before)<=set(after),'Only15 own Content packages permitted')
 changed=sorted(k for k in before if before[k]!=after[k]);require(changed==['Brezi/Maps/Brezi.umap'],'Only original map may change')
 new=sorted(set(after)-set(before));wanted=sorted(a.split('.')[0].replace('/Game/','')+'.uasset'for a in expected_new_packages());require(new==wanted,'Unexpected owned import/redirector/content package delta');return {'changedOriginalFiles':changed,'newRelativeFiles':new}
def relocate(v,old,new):
 if isinstance(v,str):return v.replace(old,new)
 if isinstance(v,list):return [relocate(x,old,new)for x in v]
 if isinstance(v,dict):return {k:relocate(x,old,new)for k,x in v.items()}
 return copy.deepcopy(v)
def added_expected(bundle,role,path,mesh,material):
 require(role in MATERIAL_ROLES and path not in bundle['base']['savedWitness'],'New role/path required');r=relocate(bundle['base']['template'],TEMPLATE,path);r['label']='EX_boundary_r43_'+role;r['tags']=[TAG+role];c=r['components'][0];c['mesh']=mesh;c['materials']=c['overrideMaterials']=[material]
 for key in ('renderFlags','neighborRenderPolicy'):c[key]['cast_shadow']=role!='gravel'
 return r
def expected_counterfactual(before,added):
 require(len(before)==5368 and digest(before)==read(BASE_REPORT)['savedActorWitnessSha256']and len(added)==3 and not set(before)&set(added),'Exact original5368+three additions required');r=copy.deepcopy(before);r.update(copy.deepcopy(added));return r


REPAIR_SCHEMA='brezi-r43-commandlet-class-spawn-exact-template-policy-r2'
FAILED=ROOT/'output/unreal/exterior-20261002-r43a'
FAILURE_AUDIT=FAILED/'root-native-crash-byte-audit-r43a.json'
FAILURE_AUDIT_SHA='5dd5e5162d5c645520006c2b1a99fe48c01ae4a0f95b3a7538dbcf54a3d85182'
R1_PLAN=ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-native-study/boundary-native-plan.json'
R1_PLAN_SHA='7ec408b12249b0f9291bd45341b5c41a0b10c54addaba4c488b0b34ab24de546'
R1_PREFLIGHT=R1_PLAN.parent/'source-preflight/source-preflight.json'
R1_PREFLIGHT_SHA='7759865e7d08d7a7783b90d6cc75ee09b89f9c5b308aae0db87adfbf8dcb137a'
R1_GLB=R1_PLAN.parent/'boundary-authored-r43.glb';R1_GLB_SHA='802acdeef5ab2b46214390358370cb5f4ee7bab3266ec13f4287bfea4abd0995'
CRASH=Path('/Users/davidzita/Library/Application Support/Epic/UnrealEngine/5.8/Saved/Crashes/CrashReport-UE-BreziTwin-pid-36431-64E861A12C4DFC461CF862AF2560709C')/'CrashContext.runtime-xml'

def validate_failed_attempt(audit,report,process,raw):
 require(audit['schema']=='brezi-root-r43a-native-duplicate-actor-crash-byte-audit'and audit['schemaVersion']==1 and audit['exitCode']==audit['rootSessionClosedExitCode']==raw['code']==1 and raw['pid']==report['nativeProcessId']==audit['nativeProcessId']==36431,'Actual crashed R1 terminal required')
 require(report['schema']==SCHEMA and report['schemaVersion']==1 and report['owner']=='scripts/unreal/exterior-context-parcel-boundary-native-r43.py'and report['status']=='running'and report['nativeApplied']is False and report['savedMapUnloadedReloaded']is False,'Uncaught native crash must not be recast as saved/Python success')
 require(process['reportSha256']==audit['nativeReport']['sha256']and process['processFileSha256']==audit['rawNativeProcess']['sha256']and process['sourcePinsUnchangedAfterNative']is True and len(process['sourcePinsBeforeNative'])==1330,'Exact actual R1 process closure required')
 require(audit['original4256DestinationAndCanonicalSourceFilesExact']is True and audit['originalMapAndProtected132Unchanged']is True and audit['all1330FrozenTerminalSourcePinsExact']is True and audit['currentNativeReportRemainsRunningAndIsNotAccepted']is True and audit['nativeIdleAfter']==[],'Failure preserves original source/map and all frozen inputs')
 require(len(audit['newOwnedPartialPackages'])==15 and audit['futureFreshCloneMustUseOnlySavedCanonicalR39c']is True,'Retained partial artifacts are not the next base');return True

def repair_evidence():
 require(sha(FAILURE_AUDIT)==FAILURE_AUDIT_SHA and sha(R1_PLAN)==R1_PLAN_SHA and sha(R1_PREFLIGHT)==R1_PREFLIGHT_SHA and sha(R1_GLB)==R1_GLB_SHA,'Frozen failure/source proof changed')
 audit=read(FAILURE_AUDIT);report=read(checked(audit['nativeReport']));process=read(checked(audit['nativeProcess']));raw=read(checked(audit['rawNativeProcess']));validate_failed_attempt(audit,report,process,raw)
 require('UEditorActorSubsystem::DuplicateActors'in CRASH.read_text(),'Actual duplicate crash stack required')
 identity=FAILED/'boundary-checkpoint/import-full-identities.json';proof=read(identity)
 require(set(proof)==set(MATERIAL_ROLES)and sum(r['triangles']for r in proof.values())==12566 and all(r['sourceGeometrySha256']==GEOMETRY_SHA and r['nativeAppearanceOrContactAccepted']is False for r in proof.values()),'Complete observed pre-crash mesh identities required')
 return {'failedNativeReport':audit['nativeReport'],'failedNativeProcess':audit['nativeProcess'],'failedRawNativeProcess':audit['rawNativeProcess'],'rootFailureByteAudit':pin(FAILURE_AUDIT),'actualCrashContext':pin(CRASH),'completedImportGeometryProof':pin(identity),'immutableOriginalPlan':pin(R1_PLAN),'immutableOriginalPreflight':pin(R1_PREFLIGHT),'immutableEncodedGeometry':pin(R1_GLB),'actualFailedProcessId':36431,'actualFailedExitCode':1,'actualSavedMapProduced':False,'duplicationStackObserved':True,'exactNullPointerIdentityMeasured':False,'inventoryOrCompilationCauseRejected':True,'newRoute':'spawn_actor_from_class-StaticMeshActor-own-only','newRouteObservedInThisBoundaryNative':False,'nativeAppearanceAccepted':False}
