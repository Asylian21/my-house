"""CPU-only exact saved R30b/R3 garden receipt and counterfactual checker.

Native full F32 corner hashes are source-reconstructed. Source crown masks are
executed using the native-recorded matrices, with no fresh libm-stat bit match.
No Unreal boot, original file mutation, survey or appearance acceptance.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-garden-composition-editor-check-r21.py'
HELPER='scripts/unreal/exterior-garden-composition-native-r30-r3.py'
REPORT_SHA='67f6b002cd4ad11e0c518815ebf0224e1bb1f932b94361ae91472137dedd776d'
PLAN_SHA='24587fc9d22d2e5d550f7a56b4fb144338918f4376f9db7b7016155d9d4bb90e'
PREFLIGHT_SHA='ed34aba6b006b1978eec24ebe169a9e885d470969472ff4170b0597f2e587acc'
s=importlib.util.spec_from_file_location('r21_actual_frozen_r30b_r3',ROOT/HELPER)
n=importlib.util.module_from_spec(s);s.loader.exec_module(n);g=n.guard
PREFLIGHT=g.STUDY/'source-preflight/source-preflight.json'


def finite(row,width):
 return isinstance(row,list)and len(row)==width and all(type(v)in(int,float)and math.isfinite(v)for v in row)


def frame(value,matrix):
 n.require(isinstance(value,list)and len(value)==3 and all(finite(v,width)for v,width in zip(value,[3,4,3])), 'Finite native recovered Transform required')
 n.require(isinstance(matrix,list)and len(matrix)==4 and all(finite(v,4)for v in matrix),'Finite native stored FMatrix required')
 n.exact(matrix[3][:3],value[0],'Recorded native Transform/matrix XYZ differs')
 n.exact([matrix[i][3]for i in range(4)],[0.,0.,0.,1.],'Native matrix homogeneous fields differ')
 n.require(sum(v*v for v in value[1])>0,'Empty native quaternion')


def validate_saved_preflight(plan,bundle):
 # The immutable root clone describes BEFORE-native bytes. Its saved map now
 # legitimately differs in size. Keep source/pin validation exact without
 # executing frozen pre-native validate_clone against the changed saved map.
 n.require(n.sha(g.PLAN)==PLAN_SHA and n.sha(PREFLIGHT)==PREFLIGHT_SHA,'Exact executed source plan/preflight required')
 p=n.read(PREFLIGHT)
 n.require(p['schema']==g.SCHEMA and p['schemaVersion']==3 and p['owner']==HELPER
  and p['status']=='source-preflight-validated-38-garden-roots-native-pending'and p['nativeExecuted']is False
  and p['selectedPlan']==n.pin(g.PLAN)and p['projectClone']==plan['initialRootClone']and p['expectedCounts']==g.COUNTS
  and p['baseNativeReport']==bundle['base']['reportPin']and p['baseNativeProcess']==bundle['base']['process']
  and p['tests']['exitCode']==0 and p['tests']['testCount']==20 and p['stepProjectionPolicy']==g.step.POLICY
  and p['priorFailedNative']==plan['priorFailedNative'],'Immutable before-native preflight scope differs')
 expected=n.input_files(plan,bundle);expected[p['tests']['log']['path']]=p['tests']['log']['sha256']
 n.require(p['inputFiles']==expected and len(expected)==471 and p['primaryApi']==n.primary_api(),'Exact471 source input/API closure differs')
 for path,value in expected.items():n.require(n.sha(path)==value,'Frozen consumed source changed: '+path)
 n.check_pin(p['tests']['log']);return p


def validate_garden_controls(controls,source_groups,before):
 n.require(set(controls)=={v['actor']for v in source_groups.values()},'All19 original garden actors required')
 ids=[];native={}
 for group in source_groups.values():
  actor=group['actor'];row=controls[actor];roots=group['rows'];expected_ids=[v['id']for v in roots]
  n.require(set(row)=={'rootIds','recoveredValues','storedMatrices','mainRandomSeed','numCustomDataFloats','customData',
   'additionalRandomSeedsReadbackAvailable','seedRangesReconstructed'},'Closed original garden control schema required')
  n.exact(row['rootIds'],expected_ids,'Original garden source member order differs')
  n.require(len(row['recoveredValues'])==len(row['storedMatrices'])==len(roots)
   and n.digest(row['recoveredValues'])==before[actor]['components'][0]['orderedInstanceTransformsSha256'],'Original native frames not bound to immutable full witness')
  n.require(type(row['mainRandomSeed'])is int and row['numCustomDataFloats']==0 and row['customData']==[]
   and row['additionalRandomSeedsReadbackAvailable']is row['seedRangesReconstructed']is False,'Original observed controls/unknown range limit differs')
  for root,value,matrix in zip(roots,row['recoveredValues'],row['storedMatrices']):
   frame(value,matrix);n.exact(value[0],root['positionCm'],'Original garden native/source XYZ differs');native[root['id']]=value
  ids.extend(expected_ids)
 n.require(len(ids)==len(set(ids))==473,'Exactly473 unique original garden roots required');return native


def validate_measurements(measurements,source,original_native):
 n.require(set(measurements)==set(source['models']),'All five measured original masters required')
 for model,row in measurements.items():
  placements=[p for p in source['placements']if p['model']==model]
  n.require(row['rootIds']==[p['rootId']for p in placements]and len(placements)==(12 if model.startswith('fern_')else 1)
   and row['actualUnregisteredMeshlessTransientMeasurement']is row['wrappedOriginalXYZAndRotationCopied']is row['sourceUniformScaleAssigned']is True
   and row['hostQuaternionReconstructionPerformed']is row['nativeNormalTangentReadbackAvailable']is False,'Faithful measured original38 roots scope differs')
  n.require(len(row['inputValues'])==len(row['recoveredValues'])==len(row['storedMatrices'])==len(placements),'Measured native frame census differs')
  for fit,pre,recovered,matrix in zip(placements,row['inputValues'],row['recoveredValues'],row['storedMatrices']):
   n.require(isinstance(pre,list)and len(pre)==3 and all(finite(v,w)for v,w in zip(pre,[3,4,3])),'Invalid native input frame')
   old=original_native[fit['rootId']];n.exact(pre,[old[0],old[1],fit['scale']],'Wrapped original XYZ/quaternion/source scale differs')
   frame(recovered,matrix);n.exact(recovered[0],pre[0],'Native root/contact translation changed')
 return measurements


def validate_materials(report,source):
 maps=g.module('r21_frozen_material_checks','exterior-garden-composition-materials-r30.py');maps.validate_recipe(source['recipe'])
 n.require(report['schema']==maps.SCHEMA and report['owner']==maps.OWNER and report['status']=='owned-two-original-map-materials-created'
  and report['sourceRecipe']==n.pin(maps.RECIPE)and report['recipe']==source['recipe']and report['materialCount']==2 and report['textureObjectCount']==8
  and report['nativeGraphsAndTextureSettingsObserved']is True,'Exact two original-source material receipts required')
 for key in ['sourcePixelsEdited','nativeImportedPixelsDecoded','nativeSourcePixelFormatReadbackAvailable','nativeGpuPixelFormatReadbackAvailable',
  'nativeNormalTangentReadbackAvailable','materialPackagesIndependentlyUnloaded','nativeAppearanceAccepted','ueOpticalCalibrationAccepted',
  'performanceAccepted','fullPhotorealismAccepted']:n.require(report[key]is False,'Unsupported material evidence: '+key)
 n.require(report['providerFernAlphaMode']=='MASK'and report['providerGrassAlphaMode']=='BLEND'and report['ownedUnrealBothBlendMode']=='MASKED'
  and report['alphaRoute']=='original separate alpha.R to cutoff0.5'and report['sourceFernAlphaBits']==16
  and report['sourceAlphaBitsDoNotProveNativePixelFormat']is True,'Provider/UE mask and source pixel depth distinction differs')
 n.require(report['newPackageAssets']==maps._package_assets(report['materials']),'Exact two graph/eight texture object paths differ')
 for role,row in report['materials'].items():
  maps._graph(role,row)
  n.require(row['owner']==maps.OWNER and row['nativeAppearanceAccepted']is False,'Owned graph origin/acceptance differs')
  errors=row['compileErrors']if role=='fern'else row['shaderCompileErrors'];n.require(errors==[],'Native graph compiler errors present')
  for key,tex in row['textures'].items():
   p=tex['snapshot'];normal=key in ['normal','normalGL'];alpha=key=='alpha';albedo=key=='albedo'
   n.require(n.sha(tex['source']['path'])==tex['source']['sha256'],'Original unchanged map bytes differ')
   n.require(p['srgb']is albedo and p['flip_green_channel']is normal and p['pixels']==[2048,2048]
    and p['do_scale_mips_for_alpha_coverage']is alpha and p['alphaCoverageThresholds']==([.5,0.,0.,0.]if alpha else[0.,0.,0.,0.]),'Native color/normal/alpha texture policy differs')
   n.require(p['compression_settings']==('<TextureCompressionSettings.TC_NORMALMAP: 1>'if normal else'<TextureCompressionSettings.TC_DEFAULT: 0>'if albedo else'<TextureCompressionSettings.TC_MASKS: 2>')
    and p['sourceEncoding']==('<TextureSourceEncoding.TSE_S_RGB: 2>'if albedo else'<TextureSourceEncoding.TSE_NONE: 0>'),'Native original texture compression/encoding differs')
 return {role:row['asset']for role,row in report['materials'].items()}


def validate_saved(r,plan,bundle,preflight):
 require=n.require;get=lambda key:n.read(n.check_pin(r[key]));source,base,groups=bundle['source'],bundle['base'],bundle['groups']
 require(r['schema']==g.SCHEMA and r['schemaVersion']==3 and r['owner']==HELPER and r['status']==n.STATUS
  and r['output']==str(g.CANDIDATE)and r['project']==str(g.CANDIDATE/'Project/BreziTwin')and r['nativeProcessId']==89358,'Only exact saved R30b/R3 allowed')
 require(r['selectedPlan']==n.pin(g.PLAN)and r['sourceProposal']==plan['sourceProposal']and r['sourceDraft']==plan['sourceDraft']and r['sourcePreflight']==n.pin(PREFLIGHT)
  and r['baseNativeReport']==base['reportPin']and r['baseNativeProcess']==base['process']and r['baseCurrentByteAudit']==base['audit']
  and r['projectClone']==plan['initialRootClone']and r['priorFailedNative']==plan['priorFailedNative']and r['stepProjectionPolicy']==g.step.POLICY
  and r['moduleOrderWitness']==preflight['moduleOrderWitness']and r['inputFiles']==preflight['inputFiles'],'Exact saved source/base/input closure differs')
 require(r['actualCounts']==g.COUNTS and r['uniqueSourceTriangles']==4478 and r['instancedSourceTriangles']==46806,'Declared exact source/full-scene census differs')
 require(r['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}and r['setbacksMm']=={'street':3000,'east':3000},'C/B/B3000 changed')
 for key in ['nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged','originalSavedR29Unchanged','originalGarden435RawMatricesOrderMainSeedCustomDataExact',
  'original8949GrassRawControlsExact','allOriginal78TreeRawControlsExact','allOriginalGroveActorsFullWitnessExact','sourceHeightRoleChanges36Explicit','twoTallHeroAuthoredSourceHeightRecipesPreserved']:
  require(r[key]is True,'Missing saved/preservation gate: '+key)
 for key in ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified','ecologicalFitVerified',
  'surveyedPlacementVerified','nativeNormalTangentReadbackAvailable','meshMaterialPackagesIndependentlyUnloaded','AdditionalRandomSeedsReadbackAvailable',
  'retainedTransformRecompositionPerformed','seedMutationPerformed','perInstanceShaderRandomValuePreservationClaimed','sourceGroundElevationSurveyed']:
  require(r[key]is False,'Unsupported evidence: '+key)
 before,declared,saved=(get(k)for k in ['beforeActorWitness','expectedActorWitness','savedActorWitness'])
 require(before==base['witness']and len(before)==5351,'Full immutable original5351 witness differs')
 controls=get('originalGardenControls');original_native=validate_garden_controls(controls,groups,before)
 measured=validate_measurements(get('newSourceNativeMeasurements'),source,original_native)
 require(set(r['newOwnedGroups'])==set(source['models'])and len({v['actor']for v in r['newOwnedGroups'].values()})==5,'Only five unique owned original masters required')
 expected=g.expected_original(before,groups,controls,source['proposal']);materials=validate_materials(r['materialReport'],source)
 for model,new in r['newOwnedGroups'].items():
  m=measured[model];row=source['models'][model];mesh=g.PREFIX+'/Geometry/StaticMeshes/'+row['exportName']+'.'+row['exportName']
  require(new['rootIds']==m['rootIds']and new['instances']==len(m['rootIds'])and new['mesh']==mesh and new['material']==materials[row['materialKey']]
   and new['actor']not in expected,'Exact38 new root/group/mesh/material identity differs')
  fit=next(p for p in source['placements']if p['model']==model);template=next(v for v in groups.values()if fit['rootId']in [x['id']for x in v['rows']])
  expected[new['actor']]=g.added_expected(template['witness'],template['actor'],new['actor'],model,mesh,new['material'],m)
 require(expected==declared==saved and len(saved)==5356,'Entire5356 actor state exceeds exact four filtered components plus five immutable new templates')
 require([r[k]for k in ['beforeActorWitnessSha256','expectedActorWitnessSha256','savedActorWitnessSha256']]==[n.digest(v)for v in [before,expected,saved]],'Canonical complete actor digest differs')
 hisms=[c for a in saved.values()for c in a['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
 require(len(hisms)==2318 and sum(c['instanceCount']for c in hisms)==676957,'Saved full HISM population differs')
 retained_a,retained_b=get('retainedGardenControlsBeforeSave'),get('retainedGardenControlsSaved');n.exact(retained_a,retained_b,'Saved retained raw controls/order differ')
 desired=copy.deepcopy(controls);selected={p['rootId']for p in source['placements']}
 for actor,row in desired.items():
  keep=[i for i,identity in enumerate(row['rootIds'])if identity not in selected]
  for key in ['rootIds','recoveredValues','storedMatrices']:row[key]=[row[key][i]for i in keep]
  require(n.digest(row['recoveredValues'])==saved[actor]['components'][0]['orderedInstanceTransformsSha256'],'Retained source frames not bound to full saved witness')
 n.exact(retained_b,desired,'435 exact original source survivors/raw matrices/order/mainseed/custom data differ')
 require(sum(len(v['rootIds'])for v in desired.values())==435 and sum(v['instances']for v in r['newOwnedGroups'].values())==38,'473 original root identities/population changed')
 filters=[]
 for f in source['proposal']['sourceGroupFilters']:
  count=len(groups[f['groupId']]['rows']);filters.append({'actor':groups[f['groupId']]['actor'],'groupId':f['groupId'],
   'actualRemovedOriginalIndices':f['removeSourceOrderedIndices'],'removedRootIds':f['removeRootIds'],
   'nativeRemoveAtSwapSurvivorOrder':g.swap_remove_order(count,f['removeSourceOrderedIndices']),
   'restoredOriginalSurvivorOrder':[i for i in range(count)if i not in f['removeSourceOrderedIndices']],
   'directExistingWrappedStructOrderOnly':True,'survivorTransformRecompositionPerformed':False,'seedMutationPerformed':False,
   'additionalRandomSeedsReadbackAvailable':False,'perInstanceShaderRandomValuePreservationClaimed':False})
 require(r['originalPartialFilters']==filters and r['wholeOneMemberHeroRetirements']==source['proposal']['wholeOneMemberHeroGroupRetirements'],'Only reviewed2 partial/2 whole original groups may retire')
 require(set(r['nativeGeometryReadback'])==set(source['models']),'All five original native meshes required')
 for model,row in source['models'].items():
  corners=[n.cyclic([tuple(row['expectedNativeVerticesCm'][i]+row['uv0'][i])for i in row['indices'][j:j+3]])for j in range(0,len(row['indices']),3)]
  proof={'asset':r['newOwnedGroups'][model]['mesh'],'lodCount':1,'triangles':row['triangles'],'sections':1,'nativeCornerSha256':n.digest(corners),
   'fullOrderedNativeF32PositionUV0WindingVerified':True,'originalProviderLodChainPresent':False,'sourceNormalBytesPreserved':True,
   'sourceTangentsPresent':False,'nativeTangentsRequestedFromOriginalUv':True,'nativeTangentGenerationNumericallyVerified':False,
   'nativeNormalTangentReadbackAvailable':False,'nativeNaniteRequested':False,'meshPackageIndependentlyUnloaded':False}
  require(r['nativeGeometryReadback'][model]==proof,'Full4478 original F32 positions/UV0/order/winding or evidence tier differs')
 old_materials_a,old_materials_b=get('originalMaterialsBefore'),get('originalMaterialsSaved');require(old_materials_a==old_materials_b,'Original59 graphs/87 texture observed witnesses differ')
 require(old_materials_a['original56']==n.read(n.check_pin(base['report']['originalMaterialsSaved']))
  and old_materials_a['originalTree3']==base['bundle']['donor']['report']['materials']and old_materials_a['scopedMaterialGraphs']==59
  and old_materials_a['scopedTextureObjects']==87,'Old material source binding differs')
 grass_a,grass_b=get('originalGrassBefore'),get('originalGrassSaved');n.exact(grass_a,grass_b,'Original8949 grass raw controls differ')
 # R29 declared its executed preservation gate but did not emit a grass
 # sidecar. Bind to the actual clean-R27 saved sidecar already in the frozen
 # R29/R30 source chain, then to exact unchanged original actor identities.
 h=n.helpers(base);clean_path=h['cleanNative'].guard.CANDIDATE/h['cleanNative'].REPORT
 require(str(clean_path)in preflight['inputFiles']and n.sha(clean_path)==preflight['inputFiles'][str(clean_path)],'Actual immutable clean original-grass receipt not pinned')
 clean_report=n.read(clean_path);n.exact(grass_a,n.read(n.check_pin(clean_report['originalGrassControlsSaved'])),'Original8949 grass not bound to actual clean saved source')
 require(len(grass_a)==4 and sum(v['instances']for v in grass_a.values())==8949,'Exactly four original grass groups/8949 members required')
 for control in grass_a.values():
  actor=control['actor'];require(actor in before and saved[actor]==before[actor]and len(before[actor]['components'])==1
   and before[actor]['components'][0]['instanceCount']==control['instances']and control['additionalRandomSeeds']['available']is False
   and control['additionalRandomSeeds']['rangePreservationClaimed']is control['originalMemberMutationApisCalled']is control['seedRangeMutationApisCalled']is False,
   'Original grass actor/census/unavailable supplemental range limit differs')
 trees_a,trees_b=get('originalTreesBefore'),get('originalTreesSaved');n.exact(trees_a,trees_b,'Original78 tree raw controls differ')
 n.exact(trees_a['original74'],n.read(n.check_pin(base['report']['remaining74Saved'])),'Original74 grove roots not bound to R29')
 tree_measure=n.read(n.check_pin(base['report']['newOriginalTreeGroup']['measurement']))
 for key in ['recoveredValues','storedMatrices']:n.exact(trees_a['ownedR29Four'][key],tree_measure[key],'Original R29 four saved tree frames differ')
 require(r['baseContentInventory']==base['report']['afterContentInventory']and r['protectedProjectProof']==base['report']['protectedProjectProof'],'Exact protected original project proof differs')
 packages=g.package_paths(source['models'])+[p.split('.')[0]for p in r['materialReport']['newPackageAssets']]
 require(set(r['newPackages'])==set(packages)and len(r['newPackages'])==18
  and r['importPipelineAssets']==[g.PREFIX+'/Pipeline/'+p+'.'+p for p in ['Assets','Materials','Level']]
  and r['assetDelta']==g.validate_content(base['content'],get('afterContentInventory'),packages),'Only map plus exact18 owned packages allowed')
 fresh=n.source_footprints(source,measured);recorded=r['sourceCrownMaskProof']
 require([v['rootId']for v in recorded]==[v['rootId']for v in fresh]and len(recorded)==38,'All38 actual matrix source mask proofs required')
 for old,checked in zip(recorded,fresh):
  for key in ['rootId','model','decodedSourceF32VerticesChecked','actualStoredMatrix','oldContainingCircleRadiusCm',
   'originalNativeXYZExact','sourceHeightRoleChanged','actualHeightBitEqualityToSourceClaimed','allVerticesAndFullCircleInOriginalBed',
   'fullCircleExcludesOriginalSteps','sourceNativeFloatGeometryProjectionIsGpuReadback','normalTangentReadbackAvailable']:
   require(old[key]==checked[key],'Recorded source mask identity/geometry/evidence tier differs: '+key)
  require(all(type(old[k])in(int,float)and math.isfinite(old[k])and old[k]>0 for k in ['actualContainingCircleRadiusCm','bedBoundaryCircleClearanceCm','stepBoundaryCircleClearanceCm','aboveRootHeightCm']),
   'Recorded source circle/clearances fail')
  require(old['sourceStepProjection']['sourceStepProjection']==g.step.POLICY and old['sourceStepProjection']['fullCircleExcludesOriginalProjectedSteps']is True
   and old['sourceStepProjection']['numericInequalitiesExecuted']is True and old['sourceStepProjection']['freshDerivedFloatBitEqualityRequired']is False,'Exact48-face/112-edge projection evidence differs')
 return {'mode':'saved-38-original-shape-garden-composition','nativeProcessId':89358,'originalActors':5351,'savedActors':5356,'newActors':5,
  'fullSceneHismComponents':2318,'fullSceneHismInstances':676957,'originalGardenGroups':19,'originalGardenRoots':473,'retainedOriginalGardenRoots':435,
  'newOriginalShapeRoots':38,'lowFernRoleChanges':36,'tallHeroSourceHeightRecipesPreserved':2,'sourceFullProjectedVerticesChecked':32848,
  'scopedMaterialGraphs':61,'scopedTextureObjects':95,'newMeshAssets':5,'newPackages':18,'contentFiles':4078,'protectedProjectFiles':132,
  'wholeActorCounterfactualValidated':True,'exact435SurvivorRawMatricesOrderMainSeedCustomDataValidated':True,
  'measured38WrappedOriginalInputsBoundToSavedWitness':True,'savedNewStoredMatricesExactViaExecutedNativeGate':True,
  'savedNewStoredMatricesIndependentlyDecodedByCpuChecker':False,'original78Trees8949GrassControlsExact':True,
  'sourceFullVertexAndCircleBedStepMasksIndependentlyExecuted':True,'originalStepSolids':4,'originalStepTriangles':48,'originalProjectedStepEdges':112,
  'freshDerivedFootprintStatisticsComparedByExactEquality':False,'fullNativeF32PositionUV0TopologyProofTriangles':4478,'sourceInstancedTriangles':46806,
  'nativeNormalTangentReadbackAvailable':False,'nativeTangentGenerationNumericallyVerified':False,'AdditionalRandomSeedsReadbackAvailable':False,
  'perInstanceShaderRandomValuePreservationClaimed':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,
  'shippingVerified':False,'packageVerified':False,'sourceGroundElevationSurveyed':False,'containingCircleCoverageIsLeafOrVisibleCoverage':False,
  'scope':'Existing473 garden roots,38 original-shape replacements;36 low-height role changes artistic. Actual matched full-garden appearance remains open.'}


def main():
 path=Path(sys.argv[1]).resolve()if len(sys.argv)>1 else g.CANDIDATE/n.REPORT
 n.require(path==g.CANDIDATE/n.REPORT and n.sha(path)==REPORT_SHA,'Exact actual saved R30b/R3 report required')
 plan,bundle=g.validate_plan();preflight=validate_saved_preflight(plan,bundle);report=n.read(path)
 if '--guard-tests'in sys.argv:
  edits=['running','acceptance','population','root-order','partial-indices','native-corner','alpha-channel','alpha-srgb']
  for edit in edits:
   r=copy.deepcopy(report)
   if edit=='running':r['status']='running'
   elif edit=='acceptance':r['performanceAccepted']=True
   elif edit=='population':r['actualCounts']['newOriginalShapeRoots']=39
   elif edit=='root-order':r['newOwnedGroups']['fern_02_c']['rootIds'].reverse()
   elif edit=='partial-indices':r['originalPartialFilters'][0]['actualRemovedOriginalIndices']=[0]
   elif edit=='native-corner':r['nativeGeometryReadback']['fern_02_c']['nativeCornerSha256']='0'*64
   elif edit=='alpha-channel':r['materialReport']['materials']['fern']['graph']['roots']['OPACITY_MASK'][1]='A'
   elif edit=='alpha-srgb':r['materialReport']['materials']['grass']['textures']['alpha']['snapshot']['srgb']=True
   try:validate_saved(r,plan,bundle,preflight)
   except(RuntimeError,AssertionError):continue
   raise RuntimeError('Adversarial R21 guard accepted: '+edit)
  print(json.dumps({'status':'passed','adversarialFixtureCount':8,'nativeExecuted':False}));return
 print(json.dumps(validate_saved(report,plan,bundle,preflight),allow_nan=False))


if __name__=='__main__':main()
