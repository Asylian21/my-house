"""Closed R32 ground/detail counterfactual; actual saved R30b is mandatory.

This unconsumed native contract cannot adopt a failed or future native base.
It delegates immutable source/native guards and never spoofs older ownership.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-ground-native-guards-r32.py'
NATIVE_OWNER='scripts/unreal/exterior-context-yard-ground-native-r32.py'
SCHEMA='brezi-context-yard-resolved-ground-and-low-detail-native-r32'
PREFIX='/Game/Brezi/ContextYardGround20261002R32'
TAG='BreziContextYardGround20261002R32'
BASE=ROOT/'output/unreal/exterior-20261002-r30b'
CANDIDATE=ROOT/'output/unreal/exterior-20261002-r32a'
STUDY=ROOT/'output/unreal/exterior-context-yard-ground-20261002-r32-native-study'
PLAN=STUDY/'yard-ground-native-plan.json'
CLONE_STATUS='verified-original-r30b-independent-apfs-r32-clone-before-yard-ground-native'
MODELS=('grass_medium_02_a','grass_bermuda_clump_a','celandine_01_e')
COUNTS={'originalActors':5356,'savedActors':5360,'fullHismComponents':2321,'fullHismInstances':678231,
 'reboundGroundComponents':2,'hiddenWornEdgeComponents':1,'newFloorActors':1,'newHismGroups':3,'newRoots':1274,
 'groundTriangles':32878,'groundVertices':17095,'newMeshAssets':3,'newMaterialGraphs':2,'newTextureObjects':0,
 'newPipelineAssets':3,'newPackages':8,'scopedMaterialGraphs':63,'scopedTextureObjects':95,
 'contentFiles':4086,'protectedFiles':132}


def module(name,path):
 path=Path(path);path=path if path.is_absolute()else ROOT/'scripts/unreal'/path
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


source=module('r32_selected_independent_source','exterior-context-yard-ground-source-guards-r32.py')
require,read,sha,pin,check_pin,digest=(getattr(source,k)for k in('require','read','sha','pin','check_pin','digest'))
g=source.old.g
f32,cyclic,native_points,corners=(getattr(source.old,k)for k in('f32','cyclic','native_points','corners'))


def write(path,row):
 with Path(path).open('x')as f:json.dump(row,f,indent=2,allow_nan=False);f.write('\n')


def static_mesh_api():
 # Commandlet-compatible accessor was actually executed by saved R28b.
 old=module('r32_verified_r28_commandlet_accessor','exterior-context-yard-native-guards-r28-r2.py')
 old.api_repair();return old.static_mesh_api()


def load_source():
 plan,proposal,summary=source.load_source();layout=read(check_pin(proposal['retainedLayout']))
 layout_plan=read(ROOT/'output/unreal/exterior-context-yard-20261002-r28-study/yard-source-plan.json')
 data={k:read(check_pin(v))for k,v in layout_plan['inputFiles'].items()if k in('context','terrain','nativeR16','plantGeometry')}
 polygons=source.old.index_helper();masks={k:polygons._PolygonIndex(v)for k,v in read(check_pin(proposal['sourceExclusionMasks'])).items()}
 native={m['id']:m for m in data['nativeR16']['savedPlantReadback']}
 return {'plan':plan,'proposal':proposal,'layout':layout,'data':data,'summary':summary,'polygons':polygons,'masks':masks,
  'plantingDomains':{k:polygons._PolygonIndex(v)for k,v in proposal['plantingDomainsCm'].items()},
  'nativeMasters':{k:native[k]for k in MODELS},'recipes':read(check_pin(plan['materialCopyProposals']))}


def derive_base(report,terminal,r30,plan,bundle):
 require(report['schema']==r30.guard.SCHEMA and report['schemaVersion']==3 and report['owner']==r30.OWNER
  and report['status']==r30.STATUS and report['output']==str(BASE)and report['project']==str(BASE/'Project/BreziTwin')
  and report['nativeApplied']is True and report['savedMapUnloadedReloaded']is True
  and report['sourceInputsUnchanged']is True and terminal['pid']==report['nativeProcessId'],'Actual successful saved R30b header required')
 require(report['actualCounts']==r30.guard.COUNTS and report['selectedPlan']==pin(r30.guard.PLAN),'Exact executed R30 plan/counts required')
 require(all(report[k]is False for k in('nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified')),
  'Saved-base proof cannot become appearance/performance acceptance')
 before=read(check_pin(report['beforeActorWitness']));declared=read(check_pin(report['expectedActorWitness']));saved=read(check_pin(report['savedActorWitness']))
 require(before==bundle['base']['witness'],'R30 before differs from original R29')
 controls=read(check_pin(report['originalGardenControls']));measurements=read(check_pin(report['newSourceNativeMeasurements']))
 expected=r30.guard.expected_original(before,bundle['groups'],controls,bundle['source']['proposal'])
 require(set(report['newOwnedGroups'])==set(bundle['source']['models']),'R30 owned group scope differs')
 for model,row in report['newOwnedGroups'].items():
  fit=next(p for p in bundle['source']['placements']if p['model']==model)
  old_group=next(v for v in bundle['groups'].values()if fit['rootId']in[r['id']for r in v['rows']])
  require(row['rootIds']==measurements[model]['rootIds']and row['instances']==len(row['rootIds']), 'R30 root identity/count differs')
  expected[row['actor']]=r30.guard.added_expected(old_group['witness'],old_group['actor'],row['actor'],model,row['mesh'],row['material'],measurements[model])
 require(expected==declared==saved and digest(expected)==report['expectedActorWitnessSha256']==report['savedActorWitnessSha256'],
  'Actual R30 full counterfactual differs from source declaration')
 require(len(saved)==5356,'Original R30 full actor census differs')
 content=read(check_pin(report['afterContentInventory']));protected=read(check_pin(report['protectedProjectProof']))
 r30.guard.validate_content(bundle['base']['content'],content,report['newPackages'])
 require(len(content)==4078 and len(protected)==132,'Actual saved R30 Content/protected census differs')
 for before_key,after_key in [('originalMaterialsBefore','originalMaterialsSaved'),('originalTreesBefore','originalTreesSaved'),('originalGrassBefore','originalGrassSaved'),
  ('retainedGardenControlsBeforeSave','retainedGardenControlsSaved')]:
  require(read(check_pin(report[before_key]))==read(check_pin(report[after_key])),'Recorded R30 old controls differ')
 maps=module('r32_saved_r30_material_recipe',r30.guard.ROOT/'scripts/unreal/exterior-garden-composition-materials-r30.py')
 maps.validate_recipe(bundle['source']['recipe'])
 for model,row in report['nativeGeometryReadback'].items():
  expected_model=bundle['source']['models'][model]
  expected_corners=[r30.cyclic([tuple(expected_model['expectedNativeVerticesCm'][i]+expected_model['uv0'][i])for i in expected_model['indices'][j:j+3]])for j in range(0,len(expected_model['indices']),3)]
  require(model in bundle['source']['models']and row['fullOrderedNativeF32PositionUV0WindingVerified']is True
   and row['nativeCornerSha256']==digest(expected_corners)and row['triangles']==expected_model['triangles'],
   'R30 actual full corner readback missing')
 return {'report':report,'witness':saved,'content':content,'protected':protected,'r30Plan':plan,'r30Bundle':bundle,'native':r30,
  'project':BASE/'Project/BreziTwin','process':terminal}


def saved_base(binding=None):
 path=BASE/'garden-composition-native-report-r3.json';require(path.is_file(),'Actual R30b saved report remains pending')
 if binding is not None:require(binding['baseNativeReport']==pin(path),'Bound saved R30 bytes changed')
 native_path=ROOT/'scripts/unreal/exterior-garden-composition-native-r30-r3.py'
 if binding is not None:require(binding['baseNativeHelper']==pin(native_path),'Frozen R30 helper changed')
 r30=module('r32_actual_saved_R30b',native_path)
 if binding is not None:require(binding['baseNativeGuards']==pin(ROOT/r30.guard.OWNER),'Frozen R30 guard changed')
 require(r30.OWNER=='scripts/unreal/exterior-garden-composition-native-r30-r3.py','Closed R30 helper dispatch')
 p,b=r30.guard.validate_plan();report=read(path)
 terminal=source.old.clean.actual_terminal(path,BASE/'garden-composition-native-r3-process.json',r30.OWNER,'garden-composition-native-r3')
 audit_path=BASE/'root-native-byte-audit-r30b.json';require(sha(audit_path)=='fb3798681a7db54ea0c3ed74effaca1068a3bb486ea36c4736e6f88eff5ad7cb','Executed current base byte audit changed')
 audit=read(audit_path);require(audit['schema']=='brezi-garden-composition-r30b-byte-audit-root-r1'and audit['nativeReport']==pin(path)
  and audit['currentContentFiles']==4078 and audit['currentProtectedFiles']==132
  and all(audit[k]is True for k in('all4192OriginalR29ParentFilesCurrentByteExact','exact18NewOwnedPackages','fullCurrentActorWitnessMatchesSavedExpected','allFrozenPinsCurrentExact')),
  'Executed current successful base byte closure missing')
 base=derive_base(report,terminal,r30,p,b);base['reportPin']=pin(path);base['audit']=pin(audit_path);return base


def target_components(base):
 report=read(check_pin(source.read(source.PLAN)['diagnosticSavedNativeReport']))
 old_witness=read(check_pin(report['savedActorWitness']));targets={}
 for role in('entry_walk','service_court','worn_edge'):
  actor=report['addedActors']['context_yard_r28_'+role];row=base['witness'][actor]
  require(row==old_witness[actor]and len(row['components'])==1 and row['components'][0]['class']=='/Script/Engine.StaticMeshComponent',
   'Only unchanged original R28 source floor components may change')
  targets[role]={'actor':actor,'component':row['components'][0]['name'],'originalMesh':row['components'][0]['mesh'],
   'originalMaterials':row['components'][0]['materials']}
 return targets


def expected_original(before,targets,meshes,material_assets):
 expected=copy.deepcopy(before)
 require(set(targets)=={'entry_walk','service_court','worn_edge'},'Exact three old-floor actions required')
 for role in('entry_walk','service_court'):
  target=targets[role];row=expected[target['actor']]['components'][0]
  require(row['name']==target['component']and row['mesh']==target['originalMesh']and row['materials']==target['originalMaterials'], 'Declared old binding differs')
  row['mesh']=meshes['yard_ground_r32_'+role];row['materials']=[material_assets['yard_gravel_r32']]
  row['overrideMaterials']=[material_assets['yard_gravel_r32']]
 target=targets['worn_edge'];row=expected[target['actor']]['components'][0]
 require(row['name']==target['component']and row['visible']is True and row['hiddenInGame']is False,'Old worn edge visibility differs')
 row['visible']=False;row['hiddenInGame']=True
 return expected


def added_expected(base,targets,added,meshes,materials,measurements,bundle):
 floor_path=targets['entry_walk']['actor'];r28=read(check_pin(bundle['plan']['diagnosticSavedNativeReport']))
 group_path=r28['addedActors']['EX_context_yard_r28_shrub_broadleaf_a'];result={}
 require(set(added)=={'yard_ground_r32_yard_substrate'}|{'EX_yard_ground_r32_'+k for k in MODELS},'Only one substrate/three low groups may add')
 for identity,path in added.items():
  ground=identity=='yard_ground_r32_yard_substrate';original=floor_path if ground else group_path
  row=source.old.clean.relocate_template(copy.deepcopy(base['witness'][original]),original,path)
  row['label']=identity;row['tags']=sorted(['BreziGenerated',TAG]+([]if ground else['BreziLawnDetail']));c=row['components'][0]
  if ground:
   c['mesh']=meshes[identity];c['materials']=[materials['yard_substrate_r32']];c['overrideMaterials']=[]
  else:
   mid=identity.removeprefix('EX_yard_ground_r32_');master=bundle['nativeMasters'][mid]
   c['mesh']=master['mesh'];c['materials']=master['materials'];c['overrideMaterials']=[]
   c['instanceCount']=len(measurements[mid]['rootIds']);c['orderedInstanceTransformsSha256']=digest(measurements[mid]['recoveredValues'])
  result[path]=row
 return result


def validate_content(before,after,packages,map_changed=True):
 require(len(before)==4078 and len(packages)==len(set(packages))==8,'Exact4078 base plus8 fresh packages required')
 relatives={p.split('.')[0].removeprefix('/Game/')+'.uasset'for p in packages}
 require(all(p.startswith(PREFIX+'/')for p in packages)and not(set(before)&relatives)and set(after)==set(before)|relatives,
  'Only declared new owned packages allowed')
 changed=[k for k in before if before[k]!=after[k]]
 require(changed==(['Brezi/Maps/Brezi.umap']if map_changed else[]),'Any original Content outside own map changed')
 return {'changedOriginalFiles':changed,'newOwnedPackages':sorted(relatives),'originalContentFiles':4078,'savedContentFiles':4086,'newPackages':8}


def validate_clone(bundle,base):
 path=CANDIDATE/'context-yard-ground-project-clone.json';c=read(path);project=CANDIDATE/'Project/BreziTwin'
 require(c['schema']==SCHEMA and c['status']==CLONE_STATUS and c['sourceProject']==str(base['project'])and c['project']==str(project)
  and c['nativeBaseReport']==base['reportPin']and c['selectedSourcePlan']==pin(source.PLAN)and c['selectedNativePlan']is None
  and c['nativeExecuted']is False and c['fileCount']==len(c['files'])==4210,'Typed fresh actual R30b4210 file clone required')
 expected={'Content/'+k:v for k,v in base['content'].items()};expected.update(base['protected']);seen=set()
 for row in c['files']:
  a,b=Path(row['source']),Path(row['destination']);rel=b.relative_to(project).as_posix()
  require(rel in expected and rel not in seen and a==base['project']/rel and row['independentInodes']is True
   and {k:row[k]for k in('sha256','bytes')}==expected[rel]
   and a.stat().st_size==b.stat().st_size==row['bytes']and(a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),
   'Independent clone file identity/bytes/inodes differ');seen.add(rel)
 require(seen==set(expected),'Exact all4210 initial project files required')
 require(g.inventory(project/'Content')==base['content']and g.project_proof(project)==base['protected'],'Fresh cloned bytes differ')
 return pin(path)


def validate_plan():
 p=read(PLAN);require(p['schema']==SCHEMA and p['owner']=='scripts/unreal/exterior-context-yard-ground-native-study-r32.py'
  and p['status']=='source-ready-actual-saved-r30b-yard-ground-native-pending'and p['sourceStudy']==pin(source.PLAN)
  and p['expectedCounts']==COUNTS,'Exact saved-base-bound R32 source plan required')
 bundle=load_source();base=saved_base(p);targets=target_components(base)
 require(p['targets']==targets and p['baseNativePlan']==pin(base['native'].guard.PLAN),'Bound target/actual base plan differs')
 require(p['baseCurrentByteAudit']==base['audit'],'Bound current byte audit differs')
 for row in p['ownedSources'].values():check_pin(row)
 for path,value in p['inputFiles'].items():require(sha(path)==value,'Selected consumed source changed')
 require(all(p[k]is False for k in('nativeApplied','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified')),
  'A source binding cannot invent acceptance')
 return p,{'source':bundle,'base':base,'targets':targets}
