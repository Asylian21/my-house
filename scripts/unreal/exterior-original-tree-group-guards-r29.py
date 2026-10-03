"""Closed source/saved-donor guards for four existing grove roots; no Unreal."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-original-tree-group-guards-r29.py'
NATIVE_OWNER='scripts/unreal/exterior-original-tree-group-native-r29.py'
COPY_OWNER='scripts/unreal/exterior-original-tree-group-copy-r29.py'
STUDY_OWNER='scripts/unreal/exterior-original-tree-group-native-study-r29.py'
SCHEMA='brezi-original-tree-four-existing-grove-roots-overlay-r29'
BASE=ROOT/'output/unreal/exterior-20261002-r28b'
CANDIDATE=ROOT/'output/unreal/exterior-20261002-r29a'
DONOR=ROOT/'output/unreal/exterior-20261002-r24b'
STUDY=ROOT/'output/unreal/exterior-original-tree-group-20261002-r29-native-study-r1'
PLAN=STUDY/'original-tree-group-native-plan.json'
SOURCE=ROOT/'output/unreal/exterior-original-tree-group-20261002-r29-proposal/original-tree-group-source-proposal.json'
SOURCE_SHA='f3d0e2e2ebf42c4e39fedafb8dd7aba0c819e98c4b91a7388983af3557c45f57'
BASE_SHA='dfbca65515fc08aea52515195ab5ef752fe07cdca622cd41964e99875ced2456'
DONOR_SHA='869ed396ed7946cb0ea562d3f2da77f8dbd9f3d65777250b9686171697aa10f1'
CHECKER_SHA='319e3a03cf70172f8d8386172c188e7227a9f4ce2ac9e794cd3ede08893edf4b'
INITIAL_STATUS='verified-original-r28b-independent-apfs-r29-clone-before-tree-package-copy'
COPY_STATUS='verified-byte-identical-independent-apfs-r29-17-saved-tree-packages-before-native'
CLONE_STATUS='verified-byte-identical-independent-apfs-r29-project-clone-and17-tree-packages-before-native'
GROUP='EX_regional_1_4_canopy_fullness_broadleaf_r1_c_125000'
IDS=['village_nearest_grove_3','village_nearest_grove_11','village_nearest_grove_27','village_nearest_grove_30']
TAG='BreziOriginalTreeGroup20261002R29'
LABEL='R29_original_tree_group_3_11_27_30'


def module(name,file):
 p=ROOT/'scripts/unreal'/file;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


yard=module('r29_frozen_saved_yard_native','exterior-context-yard-native-r28-r2.py')
require,read,sha,pin,check_pin,digest=(getattr(yard,k)for k in('require','read','sha','pin','check_pin','digest'))
g=yard.guard.g


def write(path,value):
 with Path(path).open('x')as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def exact(a,b,message='Binary64 controls differ'):
 if isinstance(a,dict)and isinstance(b,dict):require(set(a)==set(b),message);[exact(a[k],b[k],message)for k in a]
 elif isinstance(a,list)and isinstance(b,list):require(len(a)==len(b),message);[exact(x,y,message)for x,y in zip(a,b)]
 elif type(a)is float and type(b)is float:require(struct.pack('<d',a)==struct.pack('<d',b),message)
 else:require(type(a)==type(b)and a==b,message)


def source():
 require(sha(SOURCE)==SOURCE_SHA,'Reviewed R29 source proposal changed');p=read(SOURCE)
 require(p['schema']=='brezi-original-tree-four-existing-grove-roots-source-proposal-r29'and p['owner']=='scripts/unreal/exterior-original-tree-group-study-r29.py'
  and p['selectedGroupId']==GROUP and p['selectedRootIds']==IDS and p['status']=='source-only-four-original-tree-root-proposal-review-required','Only reviewed whole4 group allowed')
 for row in p['inputFiles'].values():check_pin(row)
 for k in('rootSelection','originalGroupWitness','savedPackageProposal','sourceDiagram'):check_pin(p[k])
 rows=read(check_pin(p['rootSelection']));full=read(check_pin(p['inputFiles']['fullnessPlan']))
 originals=[r for r in full['canopyPlacements']if r['id']in IDS]
 require([r['rootId']for r in rows]==IDS and [r['originalSourceRow']for r in rows]==originals and [r['originalGroupIndex']for r in rows]==list(range(4)),
  'Selected roots must be exact unique ordered whole-group members')
 require(len(full['canopyPlacements'])==78 and p['allOtherGroveSourceRowsPreserved']==74
  and p['allOtherGroveRowsOrderedSha256']==digest([r for r in full['canopyPlacements']if r['id']not in IDS]),'Remaining74 source rows changed')
 require(p['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}and p['housePlacement']['streetSetbackMm']==p['housePlacement']['eastSetbackMm']==3000,'C/B/B3000 changed')
 for row in rows:
  fit=row['fit'];r=row['originalSourceRow'];require(fit['allTransformedSourceVertices']==1777278 and fit['circleRadiusCm']<r['radiusCm']
   and fit['uniformScale']>0 and fit['originalBasalRootAndYawPreserved']is True and fit['independentXYStretchApplied']is False
   and fit['sourceBasalRootCm']==r['positionCm'],'Full original whole-tree shape/root fit differs')
  masks=row['sourceMasks'];require(masks['wholeCircleInsideOriginalGrove']is True and masks['wholeTriangleGroveClearanceLowerBoundCm']>0
   and set(masks['exclusions'])=={'protected','subject','roads','buildings','cultivatedGround','managedLawn'}
   and all(v['fullCirclePass']is True and v['wholeTriangleClearanceLowerBoundCm']>75 for v in masks['exclusions'].values()),'All6 whole-crown forbidden masks required')
 for k in('nativeApplied','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','ecologicalFitVerified'):require(p[k]is False,'Source proposal fabricated acceptance')
 require(p['pendingNativeBase']['selectedNativeReport']is None and p['pendingNativeBase']['selectionComplete']is False,'Historical source proposal was rewritten')
 return p,rows,full


def actual_base():
 path=BASE/'context-yard-native-report-r2.json';require(sha(path)==BASE_SHA,'Exact actual saved R28b required');r=read(path)
 checker=ROOT/'scripts/unreal/exterior-context-yard-editor-check-r16.py';require(sha(checker)==CHECKER_SHA,'Frozen source-template R16 checker changed')
 check=module('r29_actual_saved_yard_counterfactual','exterior-context-yard-editor-check-r16.py')
 bundle,base=check.g.load_source(),check.g.saved_base();preflight=check.n.validate_preflight(check.PREFLIGHT,bundle,base)
 summary=check.validate_saved(r,bundle,base,preflight)
 process=yard.guard.clean.actual_terminal(path,BASE/'context-yard-native-r2-process.json',r['owner'],'context-yard-native-r2')
 require(summary['savedActors']==5350 and summary['fullSceneHismComponents']==2312 and summary['fullSceneHismInstances']==676957,'Actual full yard scene census differs')
 content=read(check_pin(r['afterContentInventory']));protected=read(check_pin(r['protectedProjectProof']));require(len(content)==4043 and len(protected)==132,'Actual base file census differs')
 witness=read(check_pin(r['savedActorWitness']));target=[(k,v)for k,v in witness.items()if v['label']==GROUP]
 require(len(target)==1 and len(target[0][1]['components'])==1 and target[0][1]['components'][0]['instanceCount']==4,'Exact whole4 native original group required')
 return {'report':r,'reportPin':pin(path),'process':process,'witness':witness,'content':content,'protected':protected,
  'yardBundle':bundle,'cleanBase':base,'summary':summary,'targetActor':target[0][0],'targetWitness':target[0][1]}


def saved_tree():
 path=DONOR/'original-tree-native-report-r2.json';require(sha(path)==DONOR_SHA,'Actual saved R24b donor changed');r=read(path)
 require(r['schemaVersion']==2 and r['owner']=='scripts/unreal/exterior-original-tree-native-r2.py'and r['status']=='verified-saved-single-original-tree-overlay'
  and r['savedMapUnloadedReloaded']is True,'Actual completed R24 donor required')
 process=yard.guard.clean.actual_terminal(path,DONOR/'original-tree-native-r2-process.json',r['owner'],'original-tree-native-r2')
 native=module('r29_original_mesh_readback','exterior-original-tree-native-r2.py');bundle=native.guard.load_source();preflight=read(check_pin(r['sourcePreflight']))
 require(r['nativeSourceGeometry']['sampledNativeTriangles']==4096 and r['nativeSourceGeometry']['sourceTriangles']==2062487
  and r['nativeSourceGeometry']['nativeFullPositionUV0UV1CornerReadbackPerformed']is False,'Honest sampled original-mesh proof required')
 inventory=read(check_pin(r['afterContentInventory']));packages=[]
 for relative in r['newContentPackages']:
  require(relative.startswith('Brezi/OriginalTree20261002R24/')and relative.endswith('.uasset'),'Unknown donor namespace')
  packages.append({'source':str(DONOR/'Project/BreziTwin/Content'/relative),'relativeContentPath':relative,**inventory[relative],'donorReport':pin(path)})
 require(len(packages)==len({x['relativeContentPath']for x in packages})==17,'Exactly17 existing tree packages required')
 witness=read(check_pin(r['savedActorWitness']));template=witness[r['newTree']['actor']]
 return {'report':r,'reportPin':pin(path),'process':process,'native':native,'sourceBundle':bundle,'preflight':preflight,
  'packages':packages,'template':template,'templateActor':r['newTree']['actor']}


def empty_original(before,target):
 result=copy.deepcopy(before);row=result[target];require(row['label']==GROUP and row['components'][0]['instanceCount']==4,'Only exact original whole group may retire')
 row['components'][0]['instanceCount']=0;row['components'][0]['orderedInstanceTransformsSha256']=digest([]);return result


def added_expected(template,template_actor,new_actor,measurement,culls):
 require(len(measurement['rootIds'])==4 and measurement['rootIds']==IDS and len(measurement['recoveredValues'])==4,'Unique exact4 replacement identities required')
 row=yard.guard.clean.relocate_template(copy.deepcopy(template),template_actor,new_actor);row['label']=LABEL;row['tags']=sorted(['BreziGenerated',TAG])
 c=row['components'][0];c['instanceCount']=4;c['orderedInstanceTransformsSha256']=digest(measurement['recoveredValues']);c['instanceCullCm']=culls
 return row


def validate_content(before,after,packages,map_changed=True):
 require(len(before)==4043 and len(packages)==17 and len({r['relativeContentPath']for r in packages})==17,'Exact existing-base+17 package scope required')
 known={r['relativeContentPath']:{'sha256':r['sha256'],'bytes':r['bytes']}for r in packages}
 require(not set(before)&set(known)and set(after)==set(before)|set(known),'Original or foreign package namespace collision')
 changed=[k for k in before if before[k]!=after[k]];require(changed==(['Brezi/Maps/Brezi.umap']if map_changed else[]),'Original Content changed outside candidate map')
 require(all(after[k]==v for k,v in known.items()),'Saved donor package bytes changed')
 return {'changedOriginalFiles':changed,'newCopiedPackageFiles':sorted(known),'originalContentFiles':4043,'savedContentFiles':4060,'copiedPackages':17,'newGeneratedAssetPackages':0}


def validate_plan(path=PLAN):
 require(Path(path).resolve()==PLAN,'Known R29 plan path required');plan=read(path);s,roots,full=source();base=actual_base();donor=saved_tree()
 require(plan['schema']==SCHEMA and plan['owner']==STUDY_OWNER and plan['status']=='source-native-plan-ready-four-original-grove-roots-actual-r28b-base'
  and plan['baseNativeReport']==base['reportPin']and plan['sourceProposal']==pin(SOURCE)and plan['savedTreeDonor']==donor['reportPin'],'Typed exact actual source/base/donor plan required')
 require(plan['baseContentInventory']==base['report']['afterContentInventory']and plan['baseProjectProof']==base['report']['protectedProjectProof']
  and plan['selectedRootIds']==IDS and plan['selectedGroupId']==GROUP and plan['originalGroupActor']==base['targetActor']
  and plan['rootFitReview']==s['rootSelection'],'Whole selected group/fit/camera source changed')
 require(plan['packageCount']==17 and read(check_pin(plan['copiedPackages']))==donor['packages'],'Exact native package rows differ')
 require(read(check_pin(plan['originalExpectedAfterWholeGroupRetirement']))==empty_original(base['witness'],base['targetActor'])
  and read(check_pin(plan['newActorTemplate']))==donor['template'],'Source-template counterfactual differs')
 require(plan['activeDesign']==s['activeDesign']and plan['setbacksMm']=={'street':3000,'east':3000}
  and plan['operation']=={'retiredOldMembers':4,'newOwnedMembers':4,'newOwnedActors':1,'otherGroveRootsPreserved':74,'oldGroupRemainingMembers':0,'newPopulation':0,
     'oldActorComponentDeleted':False,'retainedMemberReconstruction':False,'originalGrassMemberMutation':False,'seedRangeReconstruction':False},'Only exact whole4 replacement allowed')
 require(plan['expectedCounts']=={'originalActors':5350,'savedActors':5351,'fullHismComponents':2313,'fullHismInstances':676957,'groveOriginalRemainingRoots':74,
   'newOwnedTreeRoots':4,'scopedMaterialGraphs':59,'scopedTextureObjects':87,'copiedPackages':17,'contentFiles':4060,'protectedFiles':132},'Expected exact census differs')
 require(plan['newMemberPolicy']=={'prototypeActualDonorActor':donor['templateActor'],'oldCullStartEndCm':base['targetWitness']['components'][0]['instanceCullCm'],'NoCollision':True,'navigation':False,'qualityDetail':False,'windWPO':False,
  'sameWholeSourceUniformFit':True,'retainedWrappedOriginalXYZAndQuaternionCopyRequired':True,'commonBottomOriginShiftExplicit':True,'newRootPopulation':0},'Declared member policy changed')
 require(plan['readbackContract']=={'nativeMeshDescriptionTriangles':2062487,'nativeSampledTriangles':4096,'nativeUnsampledTriangles':2058391,'newMeasuredInstances':4,'fullStoredMatrixProjectedSourceVertices':7109112,
  'remainingOriginalGroveRootsRawControls':74,'originalGrassRawControls':8949,'originalNativeGeometryAndMaterialsLoadedFrom17SavedPackages':True,
  'newNativeGeometryGenerated':False,'nativeNormalsTangentsAvailable':False,'AdditionalRandomSeedsAvailable':False,'noGeneralFloatingPointToleranceIntroduced':True},'Known bounded readback proof changed')
 for key in('nativeApplied','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','ecologicalFitVerified'):require(plan[key]is False,'Plan grants unsupported acceptance')
 required={'guard':OWNER,'native':NATIVE_OWNER,'copy':COPY_OWNER,'study':STUDY_OWNER,'tests':'scripts/unreal/test_exterior_original_tree_group_r29.py'}
 require(set(plan['ownedSources'])==set(required),'Exact new owners required')
 for key,file in required.items():
  row=plan['ownedSources'][key];require(row['live']['path']==str(ROOT/file)and row['live']['sha256']==row['snapshot']['sha256']and check_pin(row['live'])!=check_pin(row['snapshot']),'Owned source snapshot differs: '+key)
 for p,h in plan['inputFiles'].items():require(sha(p)==h,'Consumed R29 source changed')
 return plan,{'source':s,'roots':roots,'fullness':full,'base':base,'donor':donor,'content':base['content'],'protected':base['protected'],'packages':donor['packages']}
