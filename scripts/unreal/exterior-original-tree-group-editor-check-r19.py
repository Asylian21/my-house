"""CPU-only strict saved R29 receipt checker; source projections are not GPU proof."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-original-tree-group-editor-check-r19.py'
HELPER='scripts/unreal/exterior-original-tree-group-native-r29.py'
REPORT_SHA='a11b95edf10e79fed7d1ff5c43b350634f825aedbf0ab58e8ee22642e73679fd'
s=importlib.util.spec_from_file_location('r19_frozen_actual_r29_native',ROOT/HELPER)
n=importlib.util.module_from_spec(s);s.loader.exec_module(n);g=n.guard
PREFLIGHT=g.STUDY/'source-preflight/source-preflight.json'


def finite(row,width):
 return isinstance(row,list)and len(row)==width and all(type(v)in(int,float)and math.isfinite(v)for v in row)


def validate_measurement(row,bundle):
 require=n.require
 require(row['rootIds']==g.IDS and row['nativeUnregisteredTransientMeasurement']is True
  and row['originalXYZAndWrappedRotationCopied']is True and row['oldActorOrMemberMutatedDuringMeasurement']is False
  and row['nativeMatrixProjectionIsGpuReadback']is False and row['normalTangentNativeReadbackAvailable']is False,'Exact faithful4 transient measurement scope required')
 require(len(row['inputValues'])==len(row['recoveredValues'])==len(row['storedMatrices'])==4,'Only4 measured frames required')
 for source,pre,recovered,matrix in zip(bundle['roots'],row['inputValues'],row['recoveredValues'],row['storedMatrices']):
  require(all(isinstance(v,list)and len(v)==3 and all(finite(a,w)for a,w in zip(v,[3,4,3]))for v in(pre,recovered)),'Invalid finite recorded native Transform')
  require(isinstance(matrix,list)and len(matrix)==4 and all(finite(v,4)for v in matrix),'Invalid native FMatrix')
  # XYZ/bottom offsets and authored scale are frozen serialized controls.
  # Quaternion recovery is native-recorded and is not recomposed with host trig.
  n.exact(pre[0],source['fit']['proposedNativeInstanceOriginCm'],'Measured source/common-bottom XYZ differs')
  n.exact(pre[2],[source['fit']['uniformScale']]*3,'Measured authored source scale differs')
  n.exact(recovered[0],pre[0],'Recovered root position differs from native input')
  n.exact(matrix[3][:3],pre[0],'Stored root matrix translation differs')
  n.exact([matrix[i][3]for i in range(4)],[0.,0.,0.,1.],'Homogeneous matrix differs')
  require(sum(v*v for v in pre[1])>0 and sum(v*v for v in recovered[1])>0,'Empty recorded native quaternion')
 return row


def validate_saved(r,plan,bundle,preflight):
 require=n.require
 get=lambda key:n.read(n.check_pin(r[key]))
 require(r['schema']==g.SCHEMA and r['owner']==HELPER and r['status']==n.STATUS
  and r['output']==str(g.CANDIDATE)and r['project']==str(g.CANDIDATE/'Project/BreziTwin'),'Only exact actual saved R29 eligible')
 require(r['nativeProcessId']==76135 and r['selectedPlan']==n.pin(g.PLAN)and r['sourceProposal']==plan['sourceProposal']
  and r['baseNativeReport']==plan['baseNativeReport']and r['savedTreeDonor']==plan['savedTreeDonor']and r['sourcePreflight']==n.pin(PREFLIGHT)
  and r['inputFiles']==preflight['inputFiles']and r['moduleOrderWitness']==preflight['moduleOrderWitness'],'Exact actual source/base/preflight scope differs')
 require(r['actualCounts']==plan['expectedCounts']and r['materialGraphAssets']==59 and r['textureAssets']==87 and r['sourceInputTrianglesAcross4Instances']==8249948,'Actual declared source/full-scene counters differ')
 require(r['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}and r['setbacksMm']=={'street':3000,'east':3000},'C/B/B3000 changed')
 for key in('nativeApplied','savedMapUnloadedReloaded','originalSavedR28bUnchanged','sourceInputsUnchanged','originalRemaining74RawMatricesAndObservedControlsExact','original8949GrassRawControlsExact'):
  require(r[key]is True,'Saved/preservation gate missing: '+key)
 for key in('nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','ecologicalFitVerified','shippingVerified','packageVerified',
  'nativeNormalTangentReadbackAvailable','nativeMaterialPackagesIndependentlyUnloaded','nativeMeshPackagesIndependentlyUnloaded','selectedTreeNaniteRenderPassVerified',
  'AdditionalRandomSeedsReadbackAvailable','seedRangeReconstructionPerformed','retainedMemberReconstructionPerformed','sourceRootGroundElevationSurveyed','actualRuntimeDrawnTreeTriangleCountMeasured'):
  require(r[key]is False,'Unsupported acceptance/readback claim: '+key)
 require(r['nativeSourceGeometry']==bundle['donor']['report']['nativeSourceGeometry']and r['naniteResourceReadback']==bundle['donor']['report']['naniteResourceReadback'],'Exact saved donor geometry/resource proof differs')
 geometry=r['nativeSourceGeometry'];require(geometry['sourceTriangles']==2062487 and geometry['sampledNativeTriangles']==4096
  and geometry['nativeFullPositionUV0UV1CornerReadbackPerformed']is False,'Honest4096 sample/fullsource distinction missing')
 measurement=validate_measurement(n.read(n.check_pin(r['newOriginalTreeGroup']['measurement'])),bundle)
 new=r['newOriginalTreeGroup'];require(new['rootIds']==g.IDS and new['instances']==4 and new['orderedMeasuredTransformAndStoredMatrixSavedExact']is True
  and new['mesh']==bundle['donor']['report']['newMesh']and new['materialAssets']==[v['asset']for v in bundle['donor']['report']['materials']['materials'].values()],'Exact new saved4 tree/member/material source identities differ')
 retired={'actor':bundle['base']['targetActor'],'groupId':g.GROUP,'retiredSourceRootIds':g.IDS,'retiredMembers':4,'remainingMembers':0,'actorComponentKept':True}
 require(r['retiredOriginalGroup']==retired,'Only whole exact4 old members may retire')
 before,declared,saved=(get(k)for k in('beforeActorWitness','expectedActorWitness','savedActorWitness'))
 require(before==bundle['base']['witness']and len(before)==5350,'Full original5350 scene differs')
 expected=g.empty_original(before,bundle['base']['targetActor']);require(new['actor']not in expected,'New identity replaced an original actor')
 expected[new['actor']]=g.added_expected(bundle['donor']['template'],bundle['donor']['templateActor'],new['actor'],measurement,bundle['base']['targetWitness']['components'][0]['instanceCullCm'])
 require(expected==declared==saved and len(saved)==5351,'Saved entire5351 actor state differs from frozen template counterfactual')
 require([r[k]for k in('beforeActorWitnessSha256','expectedActorWitnessSha256','savedActorWitnessSha256')]==[n.digest(v)for v in(before,expected,saved)],'Canonical full actor digest differs')
 c=saved[new['actor']]['components'][0];require(c['orderedInstanceTransformsSha256']==n.digest(measurement['recoveredValues']),'Saved ordered native measured4 transforms differ')
 hisms=[c for a in saved.values()for c in a['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
 require(len(hisms)==2313 and sum(c['instanceCount']for c in hisms)==676957,'Actual whole HISM census differs')
 a,b=get('remaining74Before'),get('remaining74Saved');n.exact(a,b,'Remaining74 observed raw matrices/controls differ')
 require(sum(len(v['rootIds'])for v in a.values())==74 and all(v['additionalRandomSeedsReadbackAvailable']is False and v['seedRangesReconstructed']is False for v in a.values()),'Honest remaining74 raw control proof differs')
 groups={}
 for row in bundle['fullness']['canopyPlacements']:
  label=f'EX_regional_{int(row["positionCm"][0]//5000)}_{int(row["positionCm"][1]//5000)}_{row["meshId"]}_{row["cullEndCm"]}'
  if label!=g.GROUP:groups.setdefault(label,[]).append(row)
 require(len(groups)==22,'Exactly22 preserved original source groups required')
 paths={}
 for label,rows in groups.items():
  matches=[path for path,witness in before.items()if witness['label']==label]
  require(len(matches)==1,'Preserved source group actor identity ambiguous');path=matches[0];paths[path]=rows
 require(set(a)==set(paths)and len({root for v in a.values()for root in v['rootIds']})==74,'Exact unique preserved74 source/actor identities required')
 for path,rows in paths.items():
  control=a[path];n.exact(control['rootIds'],[row['id']for row in rows],'Preserved source member order differs')
  require(len(control['recoveredValues'])==len(control['storedMatrices'])==len(rows),'Preserved source/member frame census differs')
  frame_sha=n.digest(control['recoveredValues'])
  require(frame_sha==before[path]['components'][0]['orderedInstanceTransformsSha256']==saved[path]['components'][0]['orderedInstanceTransformsSha256'],
   'Preserved74 sidecar frames are not bound to original/saved full component witness')
  for row,value in zip(rows,control['recoveredValues']):n.exact(value[0],row['positionCm'],'Preserved original source XYZ differs')
 require(get('originalMaterialsBefore')==get('originalMaterialsSaved'),'Original material/texture observed witnesses differ')
 require(r['baseContentInventory']==plan['baseContentInventory']and r['protectedProjectProof']==plan['baseProjectProof']and r['copiedPackages']==plan['copiedPackages'],'Exact immutable Content/project/package source differs')
 require(r['assetDelta']==g.validate_content(bundle['content'],get('afterContentInventory'),bundle['packages']),'Only map plus17 byte-exact copied packages allowed')
 recorded=new['nativeStoredMatrixFullVertexMasks'];require([v['rootId']for v in recorded]==g.IDS and len(recorded)==4,'All4 recorded matrix-footprint identities required')
 # Execute independent source-mask predicates from all source vertices and the
 # actual matrices. Do not compare newly computed libm statistics to old doubles.
 h=n.helpers(bundle);fresh=n.footprint(bundle,h,measurement)
 for old,checked in zip(recorded,fresh):
  require(old['decodedFullOriginalVertices']==checked['decodedFullOriginalVertices']==1777278 and old['nativeStoredMatrixReadbackUsed']is checked['nativeStoredMatrixReadbackUsed']is True
   and old['completeOriginalTriangleInteriorsConservativelyProven']==checked['completeOriginalTriangleInteriorsConservativelyProven']==2062487
   and old['float32ProjectionIsGpuReadback']is checked['float32ProjectionIsGpuReadback']is False
   and old['normalTangentNativeReadbackAvailable']is checked['normalTangentNativeReadbackAvailable']is False,'Source/full-matrix evidence tier differs')
  require(old['allVertexContainingCircleRadiusCm']>0 and old['originalGroveCircleClearanceCm']>0
   and all(v>75 for v in old['sourceExclusionCircleClearancesCm'].values()),'Recorded conservative source masks fail')
 return {'mode':'saved-four-original-tree-existing-grove-roots','nativeProcessId':r['nativeProcessId'],'originalActors':5350,'savedActors':5351,'newActors':1,
  'fullSceneHismComponents':2313,'fullSceneHismInstances':676957,'remainingOriginalGroveRoots':74,'newOriginalTreeRoots':4,'originalGrassMembersPreserved':8949,
  'scopedMaterialGraphs':59,'scopedTextureObjects':87,'newPackages':17,'contentFiles':4060,'protectedProjectFiles':132,
  'wholeActorCounterfactualValidated':True,'faithfulTransientFramesBoundToSavedTransforms':True,'remaining74RawMatricesAndObservedControlsExact':True,
  'sourceFullVertexMasksIndependentlyExecuted':True,'freshDerivedFootprintStatisticsComparedByExactEquality':False,'originalWrappedRotationCopyBoundToExecutedNativeGate':True,
  'sourceTriangles':2062487,'nativeSampledTriangles':4096,'nativeUnsampledTriangles':2058391,'nativeFullCornerReadback':False,'nativeNormalTangentReadbackAvailable':False,
  'nativeRenderFallbackTriangles':geometry['renderFallbackTriangles'],'nativeRenderFallbackSections':geometry['renderFallbackSections'],
  'nativeNaniteResourceInputTriangles':r['naniteResourceReadback']['nativeResourceInputTriangles'],
  'nativeNaniteResourceInputVertices':r['naniteResourceReadback']['nativeResourceInputVertices'],'resourceCountsAreSelectedRenderPassProof':False,
  'selectedTreeNaniteRenderPassVerified':False,'AdditionalRandomSeedsReadbackAvailable':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,
  'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,'scope':'Four original source shapes at existing grove roots; matched native appearance and render-pass evidence remain open.'}


def main():
 path=Path(sys.argv[1]).resolve()if len(sys.argv)>1 else g.CANDIDATE/n.REPORT
 n.require(path==g.CANDIDATE/n.REPORT and n.sha(path)==REPORT_SHA,'Only exact actual R29 saved report allowed')
 plan,bundle=g.validate_plan();preflight=n.validate_preflight(PREFLIGHT,plan);report=n.read(path)
 if '--guard-tests'in sys.argv:
  # Header mutations stop before expensive source-vertex projection. These
  # adversarial guards are CPU fixtures, not a second native/geometry run.
  edits=[('status','running'),('nativeFullPositionUV0UV1CornerReadbackPerformed',True),('retiredMembers',3),('instanceCount',5)]
  for key,value in edits:
   altered=copy.deepcopy(report)
   if key=='nativeFullPositionUV0UV1CornerReadbackPerformed':altered['nativeSourceGeometry'][key]=value
   elif key=='retiredMembers':altered['retiredOriginalGroup'][key]=value
   elif key=='instanceCount':altered['newOriginalTreeGroup']['instances']=value
   else:altered[key]=value
   try:validate_saved(altered,plan,bundle,preflight)
   except(RuntimeError,AssertionError):continue
   raise RuntimeError('Adversarial R19 guard unexpectedly accepted: '+key)
  print(json.dumps({'status':'passed','adversarialFixtureCount':4,'nativeExecuted':False}));return
 summary=validate_saved(report,plan,bundle,preflight)
 print(json.dumps(summary,allow_nan=False))


if __name__=='__main__':main()
