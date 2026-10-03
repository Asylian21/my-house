"""Closed CPU/native source guards for 38 original-shape garden replacements.

Retained native members are wrapped storage filtered/reordered directly. Their
Transform is never reconstructed and unavailable seed ranges are never set.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-garden-composition-guards-r30-r3.py'
NATIVE_OWNER='scripts/unreal/exterior-garden-composition-native-r30-r3.py'
SCHEMA='brezi-garden-composition-overlay-r30'
PREFIX='/Game/Brezi/GardenComposition20261002R30'
TAG='BreziGardenComposition20261002R30'
BASE=ROOT/'output/unreal/exterior-20261002-r29a'
CANDIDATE=ROOT/'output/unreal/exterior-20261002-r30b'
STUDY=ROOT/'output/unreal/exterior-garden-composition-20261002-r30-native-study-r3'
PLAN=STUDY/'garden-composition-native-plan-r3.json'
PROPOSAL=ROOT/'output/unreal/exterior-garden-composition-20261002-r30-study/garden-composition-source-proposal.json'
PROPOSAL_SHA='bd08b2c9bddc5e8ec4389df84afa841822993c0bf09f920663dce614654a7dd9'
GEOMETRY=ROOT/'output/unreal/exterior-garden-composition-20261002-r30-geometry-study'
DRAFT_SHA='103e56269728cb7d23494acbcf2c0b8c82c049dd7f73e8acce5e980396bdf334'
BASE_SHA='a11b95edf10e79fed7d1ff5c43b350634f825aedbf0ab58e8ee22642e73679fd'
BASE_AUDIT_SHA='58585420379b328bda796c3be5410d4e37ff552e4a0118101aadefa766e7d562'
CHECKER_SHA='c500720cd961cc3b1b163d1054b2a86487562eeff071422e517ccd31b179dd69'
CHECK_RECEIPT=ROOT/'output/unreal/exterior-original-tree-group-20261002-r29-editor-r19-source-audit/source-checker-receipt.json'
CHECK_RECEIPT_SHA='438f5ded6dd9f48269678d0e1b3431f087b2cce77d5944df329fd41390c46ecb'
CLONE_STATUS='verified-original-r29a-independent-apfs-r30-clone-before-garden-native'
COUNTS={'originalActors':5351,'savedActors':5356,'fullHismComponents':2318,'fullHismInstances':676957,
 'originalGardenRoots':473,'retainedOriginalGardenRoots':435,'newOriginalShapeRoots':38,
 'newMeshAssets':5,'newMaterialGraphs':2,'newTextureObjects':8,'newPipelineAssets':3,'newPackages':18,
 'scopedMaterialGraphs':61,'scopedTextureObjects':95,'contentFiles':4078,'protectedFiles':132}


def module(name,path):
 path=Path(path);path=path if path.is_absolute()else ROOT/'scripts/unreal'/path
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


old=module('r30_actual_saved_r29_readonly','exterior-original-tree-group-native-r29.py')
require,read,sha,pin,check_pin,digest,exact=(getattr(old,k)for k in('require','read','sha','pin','check_pin','digest','exact'))


def write(path,row):
 with Path(path).open('x')as f:json.dump(row,f,indent=2,allow_nan=False);f.write('\n')


def source_groups(garden):
 groups={}
 for role,key in [('groundcover','gardenDetailPlacements'),('ornamental','ornamentalPlacements')]:
  for row in garden[key]:
   kind='groundcover'if role=='groundcover'and row['role']=='groundcover'else'ornamental'
   label=f'EX_{kind}_{int(row["positionCm"][0]//5000)}_{int(row["positionCm"][1]//5000)}_{row["meshId"]}_{row["cullEndCm"]}'
   groups.setdefault(label,[]).append(row)
 return groups


step=module('r30_r3_original_3d_step_projection','exterior-garden-composition-step-guards-r3.py')


def load_source():
 require(sha(PROPOSAL)==PROPOSAL_SHA and sha(GEOMETRY/'source-native-draft.json')==DRAFT_SHA,'Frozen source proposal/export draft changed')
 p,d=read(PROPOSAL),read(GEOMETRY/'source-native-draft.json')
 require(p['schema']=='brezi-source-only-garden-composition-proposal-r30'and p['status']=='source-proposal-no-native-applied'
  and p['replacementCount']==38 and p['retainedRootCount']==435 and p['newPopulation']==0,'Exact bounded source proposal required')
 require(d['nativeBase']=={'report':None,'process':None,'selectionComplete':False,'required':'Actual saved R29 only after root process exit0; no future receipt fabricated'},'Historical pending-base draft changed')
 for row in p['inputFiles']:check_pin(row)
 for key in ['sourceProposal','geometry','glb','materialRecipes','producer']:check_pin(d[key])
 producer=module('r30_frozen_original_geometry',d['producer']['path']);proposal,models=producer.source_models()
 descriptor=read(check_pin(d['geometry']));expected=[{k:v for k,v in models[key].items()if not k.startswith('_')}for key in producer.MODELS]
 require(descriptor['models']==expected and descriptor['nativeApplied']is False,'Original decoded attribute/order/derived F32 export differs')
 producer.decode_export(Path(check_pin(d['glb'])).read_bytes(),models)
 garden_pin=next(r for r in p['inputFiles']if Path(r['path']).name=='garden-plan.json');garden=read(check_pin(garden_pin));step.validated_steps(garden['sourceStepTrianglesCm'])
 allrows=garden['gardenDetailPlacements']+garden['ornamentalPlacements'];placements=p['proposedPlacements'];ids=[r['rootId']for r in placements]
 require(len(allrows)==473 and len(ids)==len(set(ids))==38 and digest(allrows)==p['originalAllRowsSha256'],'Exact473 source rows/38 unique selected roots required')
 byid={r['id']:r for r in allrows};retained=[r for r in allrows if r['id']not in ids]
 require(len(retained)==435 and digest(retained)==p['retainedSourceRowsSha256'],'Ordered435 retained source rows differ')
 for index,row in enumerate(placements):
  require(row['originalRow']==byid[row['rootId']]and row['positionCm']==byid[row['rootId']]['positionCm']and row['yawDeg']==byid[row['rootId']]['yawDeg'],
   'Original root position/yaw/contact/role changed')
  require(row['model']in models and type(row['uniformScale'])is float and math.isfinite(row['uniformScale'])and row['uniformScale']>0
   and row['scale']==[row['uniformScale']]*3 and row['heightRoleChanged']is(index<36),'Uniform whole-shape role contract differs')
  require(row['radiusCm']<byid[row['rootId']]['radiusCm']and all(row[k]is True for k in ['allDecodedVerticesInsideOriginalBed','fullCircleInsideOriginalBed',
   'fullCircleExcludesOriginalSteps','oldCircularEnvelopeNotExpanded','sourceBottomShiftDeclared','sourceGroundAndRootContactPreserved']),'Whole original root/circle masks fail')
  require(index<36 or row['requestedHeightCm']==byid[row['rootId']]['actualHeightCm'],'Tall hero authored height recipe changed')
 groups=source_groups(garden)
 for f in p['sourceGroupFilters']:
  rows=groups[f['groupId']];remove=f['removeSourceOrderedIndices'];left=[r for i,r in enumerate(rows)if i not in remove]
  require(remove==sorted(set(remove))and [rows[i]['id']for i in remove]==f['removeRootIds']and set(f['removeRootIds'])<=set(ids)
   and digest(rows)==f['originalSourceOrderedRowsSha256']and digest(left)==f['retainedSourceOrderedRowsSha256']and len(left)==f['retainedRows'],
   'Exact source filter indices/member order differs')
 require([len(groups[f['groupId']])for f in p['sourceGroupFilters']]==[80,61]
  and [f['retainedRows']for f in p['sourceGroupFilters']]==[58,47]
  and [h['rootId']for h in p['wholeOneMemberHeroGroupRetirements']]==['garden_ornamental_6','garden_ornamental_7'],'Only reviewed2 partial+2 whole hero groups allowed')
 for h in p['wholeOneMemberHeroGroupRetirements']:require([r['id']for r in groups[h['groupId']]]==[h['rootId']],'Hero whole-group membership differs')
 require(p['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}and p['housePlacement']['streetSetbackMm']==p['housePlacement']['eastSetbackMm']==3000,'C/B/B3000 changed')
 require(all(p[k]is False for k in ['nativeApplied','nativeGeometryVerified','nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted','shippingVerified','packageVerified']),
  'Source cannot grant native/appearance acceptance')
 return {'proposal':p,'draft':d,'geometry':descriptor,'models':models,'garden':garden,'groups':groups,'placements':placements,'retained':retained,'recipe':read(check_pin(d['materialRecipes']))}


def saved_base():
 path=BASE/old.REPORT;require(sha(path)==BASE_SHA,'Exact actual saved R29 required');r=read(path)
 require(r['schema']==old.guard.SCHEMA and r['owner']==old.OWNER and r['status']==old.STATUS and r['nativeProcessId']==76135
  and r['savedMapUnloadedReloaded']is True and r['nativeApplied']is True and r['sourceInputsUnchanged']is True,'Actual saved R29/header differs')
 terminal=old.guard.yard.guard.clean.actual_terminal(path,BASE/'original-tree-group-native-process.json',r['owner'],'original-tree-group-native')
 audit_path=BASE/'root-native-byte-audit-r29.json';require(sha(audit_path)==BASE_AUDIT_SHA,'Actual R29 byte audit changed');audit=read(audit_path)
 require(audit['nativeReport']==pin(path)and audit['exitCode']==0 and audit['allCandidateSavedBytesMatch']is audit['allProtectedBytesMatch']is True,'Actual base byte closure failed')
 checker=ROOT/'scripts/unreal/exterior-original-tree-group-editor-check-r19.py';require(sha(checker)==CHECKER_SHA and sha(CHECK_RECEIPT)==CHECK_RECEIPT_SHA,'Executed independent R19 checker/proof changed')
 checked=read(CHECK_RECEIPT);require(checked['checker']==pin(checker)and checked['actualNativeReport']==pin(path)and checked['exitCode']==0
  and checked['summary']['wholeActorCounterfactualValidated']is True and checked['summary']['remaining74RawMatricesAndObservedControlsExact']is True,'Executed actual counterfactual/source-mask proof missing')
 content=read(check_pin(r['afterContentInventory']));protected=read(check_pin(r['protectedProjectProof']));witness=read(check_pin(r['savedActorWitness']))
 require(len(content)==4060 and len(protected)==132 and len(witness)==5351,'Actual base full census differs')
 plan,bundle=old.guard.validate_plan();require(pin(old.guard.PLAN)==r['selectedPlan'],'Actual base plan differs')
 return {'report':r,'reportPin':pin(path),'process':terminal,'audit':pin(audit_path),'checkerReceipt':pin(CHECK_RECEIPT),'witness':witness,
  'content':content,'protected':protected,'plan':plan,'bundle':bundle,'project':BASE/'Project/BreziTwin'}


def bind_groups(source,base):
 result={};labels={v['label']:k for k,v in base['witness'].items()}
 original=read(next(r['path']for r in source['proposal']['inputFiles']if Path(r['path']).name=='exterior-import-report.json'))['geometry']['groups']
 for label,rows in source['groups'].items():
  require(label in labels and label in original,'Source garden group absent from saved scene')
  actor=labels[label];w=base['witness'][actor];require(len(w['components'])==1,'Only original single HISM garden components allowed');c=w['components'][0]
  require(actor==original[label]['actor']and c['instanceCount']==len(rows)==original[label]['instances']
   and c['orderedInstanceTransformsSha256']==original[label]['transformsSha256']and c['mesh']==original[label]['mesh']
   and c['instanceCullCm']==[original[label]['cullStartCm'],original[label]['cullEndCm']],'Actual whole-garden source/native mapping differs')
  result[label]={'actor':actor,'component':c['name'],'rows':rows,'witness':w,'oldMesh':c['mesh']}
 require(len(result)==19 and sum(len(v['rows'])for v in result.values())==473,'All19 current garden groups/473 roots required')
 return result


def swap_remove_order(count,remove):
 require(type(count)is int and count>0 and isinstance(remove,list)and remove==sorted(set(remove))and all(type(i)is int and 0<=i<count for i in remove),
  'Unique valid original indices required')
 order=list(range(count))
 for i in reversed(remove):order[i]=order[-1];order.pop()
 return order


def expected_control(control,remove):
 require(control['numCustomDataFloats']==0 and control['customData']==[],'Only zero observed custom-data semantics are reviewed for partial removal')
 require(control['additionalRandomSeedsReadbackAvailable']is False and control['seedRangesReconstructed']is False,'Unavailable seed ranges cannot be inferred/reconstructed')
 keep=[i for i in range(len(control['rootIds']))if i not in remove];result=copy.deepcopy(control)
 for key in ['rootIds','recoveredValues','storedMatrices']:result[key]=[control[key][i]for i in keep]
 return result


def expected_original(before,groups,controls,proposal):
 expected=copy.deepcopy(before)
 for f in proposal['sourceGroupFilters']:
  actor=groups[f['groupId']]['actor'];row=expected[actor]['components'][0];control=expected_control(controls[actor],f['removeSourceOrderedIndices'])
  row['instanceCount']=len(control['rootIds']);row['orderedInstanceTransformsSha256']=digest(control['recoveredValues'])
 for f in proposal['wholeOneMemberHeroGroupRetirements']:
  row=expected[groups[f['groupId']]['actor']]['components'][0];require(row['instanceCount']==1,'Only single-member hero may whole-retire')
  row['instanceCount']=0;row['orderedInstanceTransformsSha256']=digest([])
 return expected


def added_expected(template,template_actor,actor,model,mesh,material,measurement):
 row=old.guard.yard.guard.clean.relocate_template(copy.deepcopy(template),template_actor,actor)
 row['label']='R30_'+model;row['tags']=sorted(['BreziGenerated',TAG]);row['detailDensityScaling']=False;row['actorTick']=False
 c=row['components'][0];c['mesh']=mesh;c['materials']=[material];c['overrideMaterials']=[]
 c['instanceCount']=len(measurement['rootIds']);c['orderedInstanceTransformsSha256']=digest(measurement['recoveredValues'])
 return row


def package_paths(models):
 paths=[PREFIX+'/Geometry/StaticMeshes/'+v['exportName']for v in models.values()]
 paths+=[PREFIX+'/Pipeline/'+k for k in ['Assets','Materials','Level']]
 return paths


def validate_content(before,after,packages,map_changed=True):
 require(len(before)==4060 and len(packages)==len(set(packages))==18,'Exact base4060 plus18 new packages required')
 relative={p.removeprefix('/Game/')+'.uasset'for p in packages}
 require(all(p.startswith(PREFIX+'/')and '.'not in p.removeprefix(PREFIX+'/')for p in packages)
  and not set(before)&relative and set(after)==set(before)|relative,'Only exact new owned18 packages allowed')
 changed=[k for k in before if before[k]!=after[k]];require(changed==(['Brezi/Maps/Brezi.umap']if map_changed else[]),'Any original Content outside own candidate map changed')
 return {'changedOriginalFiles':changed,'newOwnedPackages':sorted(relative),'originalContentFiles':4060,'savedContentFiles':4078,'newPackages':18}


def validate_clone(source,base):
 path=CANDIDATE/'garden-composition-project-clone.json';require(sha(path)=='32303b06564507106217751a587826a5f06db6110723344825d6378183385e15','Exact fresh R30b clone required');c=read(path);project=CANDIDATE/'Project/BreziTwin'
 require(c['schema']==SCHEMA and c['status']==CLONE_STATUS and c['sourceProject']==str(base['project'])and c['project']==str(project)
  and c['nativeBaseReport']==base['reportPin']and c['sourceProposal']==pin(PROPOSAL)and c['selectedPlan']is None
  and c['fileCount']==len(c['files'])==4192 and c['contentFiles']==4060 and c['protectedFiles']==132 and c['nativeExecuted']is False,'Typed own4192 clone differs')
 expected={'Content/'+k:v for k,v in base['content'].items()};expected.update(base['protected']);seen=set()
 for row in c['files']:
  a,b=Path(row['source']),Path(row['destination']);rel=b.relative_to(project).as_posix()
  require(rel in expected and rel not in seen and a==base['project']/rel and row['independentInodes']is True
   and {k:row[k]for k in ['sha256','bytes']}==expected[rel]and a.stat().st_size==b.stat().st_size==row['bytes']
   and(a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),'Original cloned row/inode/byte metadata differs');seen.add(rel)
 require(seen==set(expected),'Exact4192 clone relative membership required');return pin(path)


def failed_r30a_evidence():
 failed=ROOT/'output/unreal/exterior-20261002-r30a';report=failed/'garden-composition-native-report.json'
 terminal=failed/'garden-composition-native-process.json';audit=failed/'root-native-failure-byte-audit-r30a.json'
 snapshot=ROOT/'output/unreal/exterior-garden-composition-20261002-r30-native-study-r2/native-r30a-failure-source-snapshot/failure-source-receipt.json'
 require(sha(report)=='23d845195b2e9571cca8fc83035a819c289ea47a832b67f5d32afb3f49858133'
  and sha(terminal)=='a736a10ea21d9cd79dd26b9900c908f75124ebd7d3845ac0c13042ba10c15942'
  and sha(audit)=='94e7a2cd175ab2ae8e64476ebb91cf37f2fc98f14d43a30dd018f53078e20966'
  and sha(snapshot)=='0552925198cf9ff654aad83aef75ae766e03f5f20fcac387bb9453862f441e8b','Exact preserved failed native/terminal/root byte audit/snapshot required')
 r,t,a,snap=read(report),read(terminal),read(audit),read(snapshot);raw=Path(t['processFile']);log=Path(t['logFile']);process=read(raw)
 require(r['schema']==SCHEMA and r['owner']=='scripts/unreal/exterior-garden-composition-native-r30.py'and r['status']=='failed'
  and r['nativeProcessId']==85419 and r['nativeApplied']is False and r['error']=='Organic source bed is not a triangle union',
  'Only actual preserved R30a source-step failure allowed')
 require(raw==failed/'garden-composition-native.log.json'and log==failed/'garden-composition-native.log'
  and sha(raw)==t['processFileSha256']and sha(log)==t['logSha256']and t['reportSha256']==sha(report)
  and process['pid']==85419 and process['code']==255 and process['signal']is None
  and process['args'][0]==str(failed/'Project/BreziTwin/BreziTwin.uproject')
  and '-script='+str(ROOT/r['owner'])in process['args']and t['sourcePinsUnchangedAfterNative']is True
  and len(t['sourcePinsBeforeNative'])==447,'Actual failed255 process/source closure differs')
 require('source_footprints'in log.read_text()and 'mask._boundary(steps)'in log.read_text(),'Measured failure stack does not identify projected-step boundary misuse')
 require(a['schema']=='brezi-garden-composition-r30a-failure-byte-audit-root-r1'and a['nativeReport']==pin(report)and a['terminalProcess']==pin(terminal)
  and a['all4192OriginalCandidateFilesByteExact']is a['all4192OriginalR29ParentFilesByteExact']is a['allFrozenPinsCurrentExact']is a['mapByteUnchanged']is True
  and a['oldContentFiles']==a['currentContentFiles']==4060 and a['newFileCount']==0 and a['newFiles']==[]
  and a['frozenSourcePinCount']==447 and a['nativeApplied']is False,'Actual root negative asset/byte audit differs')
 require(snap['status']=='actual-native-r30a-failed-before-any-asset-or-original-scene-write'and snap['report']==pin(report)and snap['byteAudit']==pin(audit)
  and snap['pid']==85419 and snap['exitCode']==255 and len(snap['sourceFiles'])==10
  and snap['sourceInputsUnchanged']is True and snap['frozenInputsChanged']is False and snap['newNativeRunPerformedBySnapshot']is False,
  'Preserved failure source receipt differs')
 for pair in snap['sourceFiles']:
  check_pin(pair['original']);check_pin(pair['snapshot']);require(pair['original']['sha256']==pair['snapshot']['sha256'],'Frozen failure source snapshot changed')
 return {'nativeReport':pin(report),'terminalProcess':pin(terminal),'rawProcess':pin(raw),'nativeLog':pin(log),'failureByteAudit':pin(audit),
  'failureSourceSnapshot':pin(snapshot),'nativeProcessId':85419,'exitCode':255,'originalContentUnchanged':True,'newFiles':0,
  'diagnosis':'A closed3D four-step solid with48 original triangles has duplicate/degenerate projected faces; it is not a2D organic bed triangle union',
  'repair':'Separate frozen original3D-step projection guard; bed boundary remains unchanged; all112 original nonzero projected raw edges retained',
  'oldFrozenSourcesChanged':False,'sourceGeometryChanged':False,'nativeRetrySucceeded':False}


def validate_plan():
 source,base=load_source(),saved_base();p=read(PLAN)
 require(p['schema']==SCHEMA and p['schemaVersion']==3 and p['owner']=='scripts/unreal/exterior-garden-composition-native-study-r30-r3.py'
  and p['status']=='source-ready-actual-r29-base-garden-composition-native-pending'and p['sourceProposal']==pin(PROPOSAL)
  and p['sourceDraft']==pin(GEOMETRY/'source-native-draft.json')and p['baseNativeReport']==base['reportPin']and p['baseNativeProcess']==base['process']
  and p['baseCurrentByteAudit']==base['audit']and p['baseIndependentCheckerReceipt']==base['checkerReceipt']and p['expectedCounts']==COUNTS,
  'Only actual saved-base-bound source plan eligible')
 require(p['priorFailedNative']==failed_r30a_evidence() and p['stepProjectionPolicy']==step.POLICY and p['candidateOutput']==str(CANDIDATE),'Typed R30a failure evidence/fresh R30b/exact original step projection required')
 groups=bind_groups(source,base);require(p['originalGardenGroupBindings']=={k:{x:v[x]for x in ['actor','component','oldMesh']}for k,v in groups.items()},'Bound original19 group identities differ')
 require(p['retiredRootIds']==[r['rootId']for r in source['placements']]and p['newGroupOrder']==list(source['models']),'Bound exact38 roots/5 original forms differ')
 for row in p['ownedSources'].values():check_pin(row)
 for path,value in p['inputFiles'].items():require(sha(path)==value,'Bound consumed source changed')
 require(all(p[k]is False for k in ['nativeApplied','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified']),
  'Source binding cannot fabricate acceptance')
 return p,{'source':source,'base':base,'groups':groups}
