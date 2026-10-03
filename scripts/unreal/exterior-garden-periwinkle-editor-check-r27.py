"""CPU decoder for actual saved R36; source skeleton until root closes native.

This does not invoke Unreal. Full source corner hashes and measured-matrix
inequalities are independently decoded; native post-save matrix comparisons
remain executed-writer evidence, not a fresh CPU engine readback.
"""
import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-garden-periwinkle-editor-check-r27.py'
s=importlib.util.spec_from_file_location('r27_frozen_periwinkle_source_guard_r2',ROOT/'scripts/unreal/exterior-garden-periwinkle-native-guards-r36-r2.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
REPORT=g.CANDIDATE/'garden-periwinkle-native-report-r2.json'
REPORT_SHA='d2057c860c0b5135cd19beaee776145d89c3377a07ff08abee9537f6a15c765e'
NATIVE_PID=47851
ROOT_AUDIT=g.CANDIDATE/'root-native-success-byte-audit-r36b-r2.json'
ROOT_AUDIT_SHA='a2be8c8a3d5c50ee60b5ee78d1426bb4c322d0de2bcb1c13a6734959159253e8'
PLAN_SHA='71de87f91926f059a7553e8553927151d8aa9873040dbb56d20d31203e37a640'
PREFLIGHT_SHA='0629127c96e608f34082040587a5b9c8120374290cdef7e76d89b490e799ca9c'
SOURCE_PIN_COUNT=578
NATIVE_OWNER='scripts/unreal/exterior-garden-periwinkle-native-r36-r2.py'


def side(row):return g.read(g.check_pin(row))


def validate_terminal_and_root_audit(r):
 g.require(g.sha(ROOT_AUDIT)==ROOT_AUDIT_SHA,'Actual independent root byte audit differs')
 audit=g.read(ROOT_AUDIT);terminal_path=g.CANDIDATE/'garden-periwinkle-native-r2-process.json'
 raw_path=g.CANDIDATE/'garden-periwinkle-native-r2.log.json';terminal,raw=g.read(terminal_path),g.read(raw_path)
 g.require(raw['pid']==NATIVE_PID and raw['code']==0 and raw['signal']is None
  and raw['command']=='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
  and raw['args'][0]==str(g.CANDIDATE/'Project/BreziTwin/BreziTwin.uproject')
  and '-script='+str(ROOT/NATIVE_OWNER)in raw['args']and '-nullrhi'in raw['args'],'Actual R36b process0 required')
 g.require(terminal['processFile']==str(raw_path)and terminal['processFileSha256']==g.sha(raw_path)
  and terminal['reportSha256']==REPORT_SHA and terminal['sourcePinsUnchangedAfterNative']is True
  and len(terminal['sourcePinsBeforeNative'])==588 and g.sha(terminal['logFile'])==terminal['logSha256']
  and terminal['controllerSha256BeforeNative']==terminal['controllerSha256AfterNative']==g.sha(terminal['controller']),
  'Actual root process/log/588 sealed source closure differs')
 expected_files=sorted('Content/'+p.removeprefix('/Game/')+'.uasset'for p in r['newPackages'])
 g.require(audit['schema']=='brezi-root-r36b-native-success-current-byte-audit-r2'
  and audit['report']==g.pin(REPORT)and audit['process']==g.pin(terminal_path)and audit['clone']==r['projectClone']
  and audit['expectedRootObservedPid']==NATIVE_PID and audit['expectedRootObservedPins']==588
  and audit['currentProjectFiles']==4218 and audit['currentContentFiles']==4086 and audit['protectedFiles']==132
  and audit['all4203OriginalR34SourceFilesExact']is audit['all4202OriginalOwnFilesExceptMapExact']
      is audit['onlyOriginalMapAndFifteenNewOwnedPackagesChanged']is True
  and audit['changedOriginalFiles']==['Content/Brezi/Maps/Brezi.umap']and audit['newOwnedFiles']==expected_files
  and audit['sourcePinsBeforeAfterAndCurrentExact']==588 and audit['storedNativeFullCounterfactualEqual']is True
  and audit['actualStoredWitnessCounts']=={'actors':5360,'hismComponents':2322,'hismInstances':676957}
  and audit['storedOriginal53HeroFlowerAnd36FernControlsBeforeAfterExact']is True
  and audit['storedNew384SourceNativeRoots']==384 and audit['storedCompleteSourceVertexCircleChecks']==1981184
  and audit['storedNativeOrderedPositionUv0Uv1Triangles']==34350
  and audit['newNativeActorOrGeometryDecodeByThisCpuAudit']is audit['nativeAppearanceAccepted']
      is audit['fullPhotorealismAccepted']is False,'Actual independent root current-byte/stored-witness scope differs')
 for key in ('byteHelper','rootAuditController'):g.check_pin(audit[key])


def validate_header(r):
 g.require(type(NATIVE_PID)is int and NATIVE_PID>0 and isinstance(REPORT_SHA,str)and len(REPORT_SHA)==64,'Saved R36 native binding is still pending')
 g.require(r['schema']==g.SCHEMA and r['schemaVersion']==2 and r['owner']==NATIVE_OWNER
  and r['status']=='verified-saved-384-original-periwinkle-low-garden-composition'and r['nativeProcessId']==NATIVE_PID
  and r['output']==str(g.CANDIDATE)and r['project']==str(g.CANDIDATE/'Project/BreziTwin'),'Only actual saved R36 accepted')
 true=('nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged','originalSavedR34Unchanged',
  'allOriginal12Ornamentals41Flowers36FernsRawControlsExact','allOriginal8949GrassAnd78TreesRawControlsExact',
  'all384SourceOriginalRootsRetiredOnceAndReplacedOnce','allOriginalSourceSixAttributesAndIndexBinBytesPreserved','sourceHeightRoleChanges384Explicit',
  'allSixImportedMastersIdentifiedByFullSourceCorners')
 false=('nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified',
  'ecologicalFitVerified','surveyedPlacementVerified','nativeNormalTangentReadbackAvailable','nativeColor0Color1ReadbackAvailable',
  'meshMaterialPackagesIndependentlyUnloaded','AdditionalRandomSeedsReadbackAvailable','retainedTransformRecompositionPerformed',
  'seedMutationPerformed','perInstanceShaderRandomValuePreservationClaimed','yardIntegrationApplied',
  'derivedContactFloatingPointBitEqualityClaimed','sourceGroundElevationSurveyed','actorLabelsUsedForSourceMeshIdentity')
 g.require(all(r[k]is True for k in true)and all(r[k]is False for k in false),'Native limits/retained source scope overstated')
 g.require(r['actualCounts']==g.COUNTS and r['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}
  and r['setbacksMm']=={'street':3000,'east':3000}and r['contactWorldBottomArithmeticCapCm']==1e-7
  and r['repairSchema']==g.REPAIR_SCHEMA and r['immutableSourceGuard']==g.pin(g.ORIGINAL_GUARD)
  and r['importIdentityEvidence']==g.import_identity_evidence(),'Exact R36 R2 counters/design/contact/import policy required')


def enum_token(value,class_name,tokens):
 g.require(isinstance(value,str),'Recorded native enum string required');match=re.fullmatch(r'<'+re.escape(class_name)+r'\.([A-Za-z0-9_]+): [0-9]+>',value)
 g.require(match and match.group(1).replace('_','').upper()in tokens,'Unknown recorded native enum policy: '+str(value))


def material_source_contract(report,source):
 maps=g.module('r27_frozen_original_periwinkle_material','exterior-garden-periwinkle-materials-r36.py');maps.validate_recipe(source['recipe']);recipe=source['recipe']
 g.require(report['schema']==maps.SCHEMA and report['owner']==maps.OWNER and report['status']=='owned-original-five-map-periwinkle-material-created'
  and report['sourceRecipe']==g.pin(maps.RECIPE)and report['recipe']==recipe and report['materialCount']==1 and report['textureObjectCount']==5
  and report['newPackageAssets']==maps.package_assets(recipe)and report['compileErrors']==[]and report['instancedStaticMeshUsage']is True
  and report['asset']==g.PREFIX+'/Materials/M_'+recipe['key']+'.M_'+recipe['key']and report['graphSha256']==g.digest(report['graph']),
  'One original five-map graph/six material packages required')
 g.require(report['sourceOriginalAlphaMode']=='BLEND'and report['ownedUnrealBlendMode']=='MASKED'and report['sourcePngBits']==16
  and report['source16BitDoesNotProveNativePixelFormat']is True,'Original16-bit/proposed masked scope differs')
 for k in ('originalTexturePixelsEdited','nativeImportedPixelsDecoded','nativeSourcePixelFormatReadbackAvailable','nativeGpuPixelFormatReadbackAvailable',
  'nativeNormalTangentReadbackAvailable','materialPackagesIndependentlyUnloaded','sourceOpticalModelExactlyReproduced','physicalOpticalCalibrationAccepted',
  'nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted'):g.require(report[k]is False,'Material evidence overstated')
 g.require(set(report['textures'])==set(recipe['maps']),'All original five map roles required')
 audit=maps.check_graph(report['graph'],{k:v['asset']for k,v in report['textures'].items()});g.require(audit==report['audit'],'Recorded optical graph policy differs')
 policy=report['policy'];enum_token(policy['blend_mode'],'BlendMode',{'BLENDMASKED'});enum_token(policy['shading_model'],'MaterialShadingModel',{'MSMTWOSIDEDFOLIAGE'})
 g.require(policy['two_sided']is policy['tangent_space_normal']is True and policy['use_material_attributes']is False and policy['opacity_mask_clip_value']==.5,'Owned masked foliage policy differs')
 for role,row in report['textures'].items():
  g.require(row['source']==recipe['maps'][role]and row['asset']==maps.texture_asset(role,recipe['maps'][role])
   and row['sourcePngHeader']==maps.png_header(g.check_pin(row['source'])),'Original PNG/source texture role differs')
  snapshot=row['snapshot'];color=role in ('albedo','translucency')
  g.require(snapshot['pixels']==[2048,2048]and snapshot['srgb']is color and snapshot['flip_green_channel']is(role=='normalGl')
   and snapshot['do_scale_mips_for_alpha_coverage']is(role=='opacity')and snapshot['alphaCoverageThresholds']==([.5,0.,0.,0.]if role=='opacity'else[0.,0.,0.,0.])
   and snapshot['lod_bias']==0 and snapshot['max_texture_size']==0 and snapshot['virtual_texture_streaming']is snapshot['never_stream']is False,'Original map color/GL/alpha/mip policy differs')
  enum_token(snapshot['compression_settings'],'TextureCompressionSettings',{'TCNORMALMAP'}if role=='normalGl'else{'TCMASKS'}if role in ('opacity','roughness')else{'TCDEFAULT'})
  enum_token(snapshot['sourceEncoding'],'TextureSourceEncoding',{'TSESRGB'}if color else{'TSENONE'})
  for axis in ('address_x','address_y'):enum_token(snapshot[axis],'TextureAddress',{'TAWRAP'})
  enum_token(snapshot['mip_gen_settings'],'TextureMipGenSettings',{'TMGSFROMTEXTUREGROUP'});enum_token(snapshot['power_of_two_mode'],'TexturePowerOfTwoSetting',{'NONE'})
  for k in ('nativeImportedPixelsDecoded','nativeSourcePixelFormatReadbackAvailable','nativeGpuPixelFormatReadbackAvailable'):g.require(row[k]is False,'Texture pixel format/readback overstated')
 return report['asset']


def validate_import_identity(r,source,before,saved):
 inventory=side(r['importTemporaryActorInventory'])
 g.require(inventory['schema']==g.REPAIR_SCHEMA and inventory['schemaVersion']==2 and inventory['owner']==NATIVE_OWNER
  and inventory['scope']=='ACTUAL_NEW_IMPORT_DELTA_BEFORE_ANY_BINDING_GATE'
  and inventory['actorLabelsUsedForSourceIdentity']is inventory['sourceMeshIdentityVerifiedAtThisCheckpoint']
      is inventory['originalR1TemporaryActorLabelsRecovered']is inventory['nativeAppearanceAccepted']
      is inventory['fullPhotorealismAccepted']is False,'Actual pre-binding checkpoint scope differs')
 rows=inventory['actors'];paths=[v['actor']for v in rows]
 g.require(inventory['actorCount']==len(rows)in(6,7)and len(set(paths))==len(paths)
  and not set(paths)&set(before)and not set(paths)&set(saved),'Only fully removed owned temporary actor delta required')
 containers=[v for v in rows if not v['staticMeshComponents']]
 g.require(len(containers)<=1 and r['observedNonrenderingImportContainers']==containers,'Closed observed nonrendering container differs')
 container_paths={v['actor']for v in containers};identity=[[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]]
 proofs=r['originalSourceNodeNativeMeshBindings']
 g.require(len(proofs)==6 and {v['sourceNodeId']for v in proofs}==set(g.MODELS)
  and len({v['asset']for v in proofs})==6,'Exactly six unique full-source geometry identity rows required')
 g.source_triangle_count_bindings(source['models'])
 for row in rows:
  parts={v['path']for v in row['components']}
  g.require(row['worldTransform']==identity and parts==set(row['sceneComponents']),
   'Identity import pose/only scene-component scope differs')
  if row in containers:
   g.require(row['class']=='/Script/Engine.Actor'and not row['primitiveComponents']
    and len(parts)<=1 and row['attachParent']is None,'Only closed new nonrendering scene container allowed')
   continue
  g.require(row['class']in('/Script/Engine.StaticMeshActor','/Script/Engine.Actor')
   and len(row['staticMeshComponents'])==1 and row['primitiveComponents']==row['staticMeshComponents']
   and (row['attachParent']is None or row['attachParent']in container_paths),'Exact imported primitive/parent scope differs')
  selected=[v for v in proofs if v['actualTemporaryActor']==row['actor']]
  g.require(len(selected)==1,'Each mesh temporary actor must bind one exact source geometry')
  proof=selected[0];model=proof['sourceNodeId'];desc=source['models'][model]
  meshpart=[v for v in row['components']if v['path']==row['staticMeshComponents'][0]]
  g.require(len(meshpart)==1 and meshpart[0]['staticMesh']==proof['asset']
   and proof['asset'].startswith(g.PREFIX+'/Geometry/')and proof['actualTemporaryActorLabel']==row['label']
   and proof['originalProviderMeshName']==desc['originalSourceMeshName']and proof['triangles']==desc['triangles']
   and proof['sections']==1 and proof['nativeCornerSha256']==r['nativeGeometryReadback'][model]['nativeCornerSha256'],
   'Observed native mesh/source/full-corner identity differs')
  g.require(proof['fullOrderedNativeF32PositionUV0UV1WindingVerified']is True
   and proof['uniqueTriangleCountUsedOnlyForCandidateRouting']is True
   and proof['navigationAndBuildSettingsNotRequiredForInitialSourceIdentity']is True,
   'Full source identity is required beyond count routing')
  for key in ('sourceIdentityFromTriangleCountAlone','sourceIdentityFromActorOrMeshName',
              'nativeNormalTangentColor0Color1ReadbackAvailable','meshNameUsedForSourceIdentity','actorLabelUsedForSourceIdentity'):
   g.require(proof[key]is False,'Import identity/readback evidence overstated')
 g.require(sum(v['triangles']for v in proofs)==34350,'All34350 native original source identity triangles required')


def validate_saved(r,plan,bundle,preflight):
 validate_header(r);source,base=bundle['source'],bundle['base']
 g.require(r['selectedPlan']==g.pin(g.PLAN)and r['selectedPlan']['sha256']==PLAN_SHA and r['sourceProposal']==g.pin(g.PROPOSAL)
  and r['sourceGeometryDescriptor']==source['draft']['geometry']and r['sourcePreflight']['sha256']==PREFLIGHT_SHA
  and r['baseNativeReport']==base['reportPin']and r['baseNativeProcess']==base['process']and r['baseCurrentByteAudit']==base['audit']
  and r['projectClone']==plan['projectClone']==preflight['projectClone'],'Actual R34/selected source/clone binding differs')
 g.require(plan['expectedCounts']==g.COUNTS and plan['wholeGroupRetirements']==source['proposal']['retireWholeOriginalGroups']
  and plan['nativeApplied']is False and preflight['schema']==g.SCHEMA and preflight['schemaVersion']==2 and preflight['owner']==NATIVE_OWNER
  and preflight['status']=='source-preflight-validated-whole384-original-periwinkle-native-r2-pending'and preflight['nativeExecuted']is False
  and preflight['selectedPlan']==r['selectedPlan']and preflight['tests']['exitCode']==0 and preflight['tests']['testCount']==29
  and preflight['repairSchema']==g.REPAIR_SCHEMA and preflight['importIdentityEvidence']==plan['importIdentityEvidence']==r['importIdentityEvidence']
  and preflight['expectedCounts']==g.COUNTS and r['inputFiles']==preflight['inputFiles']and type(SOURCE_PIN_COUNT)is int
  and len(r['inputFiles'])==SOURCE_PIN_COUNT,'Exact executed source-only R2 preflight required')
 for path,value in r['inputFiles'].items():g.require(g.sha(path)==value,'Consumed frozen source changed')
 g.check_pin(preflight['tests']['log']);g.require(r['moduleOrderWitness']==preflight['moduleOrderWitness'],'Executed frozen-first helper order differs')
 before,declared,saved=(side(r[k])for k in ('beforeActorWitness','expectedActorWitness','savedActorWitness'))
 g.require(before==base['witness']and len(before)==5354,'Actual5354 original R34 actors required')
 for key,value in (('beforeActorWitnessSha256',before),('expectedActorWitnessSha256',declared),('savedActorWitnessSha256',saved)):
  g.require(r[key]==g.digest(value),'Full actor canonical hash differs')
 original=side(r['originalGardenControls']);g.validate_native_controls(original,bundle)
 retained=side(r['retainedGardenControlsSaved']);g.exact(side(r['retainedGardenControlsBeforeSave']),retained,'Original53 retained controls changed during save')
 g.exact(retained,g.empty_controls(bundle),'Whole384 clearing changed any original53 hero/flower frame/seed/custom data')
 measurements=side(r['newSourceNativeMeasurements']);g.validate_measurements(measurements,bundle)
 material=material_source_contract(r['materialReport'],source);expected=g.expected_original(before,bundle)
 g.require(list(r['newOwnedGroups'])==list(r['nativeGeometryReadback'])==list(measurements)==list(g.MODELS),'Only exact six whole-original forms required')
 newactors=[];triangles=0
 for model in g.MODELS:
  row=r['newOwnedGroups'][model];m=measurements[model];desc=source['models'][model];fits=[p for p in source['placements']if p['model']==model]
  mesh=g.PREFIX+'/Geometry/StaticMeshes/'+desc['exportName']+'.'+desc['exportName']
  g.require(row['rootIds']==m['rootIds']==[p['rootId']for p in fits]and row['instances']==len(fits)and row['actor']not in before
   and row['actor'].startswith('/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.BreziVegetationPatch_')and row['mesh']==mesh and row['material']==material,'Exact source/new actor/master binding differs')
  newactors.append(row['actor']);group=next(v for v in bundle['groups'].values()if fits[0]['rootId']in v['control']['rootIds'])
  expected[row['actor']]=g.added_expected(group['witness'],group['actor'],row['actor'],model,mesh,material,m)
  corners=[g.cyclic([desc['expectedNativeVerticesCm'][i]+desc['uv0'][i]+desc['uv1'][i]for i in desc['indices'][j:j+3]])for j in range(0,len(desc['indices']),3)]
  proof=r['nativeGeometryReadback'][model]
  g.require(proof['asset']==mesh and proof['lodCount']==proof['sections']==1 and proof['triangles']==desc['triangles']
   and proof['nativeCornerSha256']==g.digest(corners)and proof['fullOrderedNativeF32PositionUV0UV1WindingVerified']is True
   and proof['allSixOriginalSourceAttributeBytesPreserved']is True and proof['nativeTangentsRequestedFromOriginalUv0']is True,'Full original native orderedP/UV0/UV1/winding proof differs')
  for k in ('originalProviderLodChainPresent','nativeNormalTangentReadbackAvailable','nativeColor0Color1ReadbackAvailable','sourceTangentsPresent',
   'nativeTangentGenerationNumericallyVerified','nativeNaniteRequested','meshPackageIndependentlyUnloaded'):g.require(proof[k]is False,'Native geometry evidence overstated')
  triangles+=proof['triangles']
 g.require(len(set(newactors))==6 and triangles==34350 and expected==declared==saved and len(saved)==5360,'Whole5360 exact counterfactual/six forms differs')
 validate_import_identity(r,source,before,saved)
 hisms=[c for a in saved.values()for c in a['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
 g.require(len(hisms)==2322 and sum(c['instanceCount']for c in hisms)==676957,'Full saved HISM population differs')
 retire=r['wholeOriginalLowGroupRetirements'];g.require(len(retire)==4 and sum(p['retiredRoots']for p in retire)==384,'Exact four entire low groups retired required')
 for actual,group in zip(retire,bundle['groups'].values()):
  g.require(actual['actor']==group['actor']and actual['rootIds']==group['control']['rootIds']and actual['retiredRoots']==len(group['rows'])
   and actual['entireComponentMembersCleared']is True and actual['actorOrComponentDeleted']is actual['survivorRecompositionPerformed']is actual['seedSetterPerformed']is False,
   'Whole-group retirement source membership/scope differs')
 oldbefore,oldafter=(side(r[k])for k in ('originalProtectedControlsBefore','originalProtectedControlsSaved'));g.exact(oldbefore,oldafter,'Original tree/grass/material/fern controls changed')
 for key,basekey in (('originalMaterials','originalMaterialsSaved'),('originalTrees','originalTreesSaved'),('original8949Grass','originalGrassSaved')):
  g.exact(oldafter[key],side(base['report'][basekey]),'Actual preserved R34 control sidecar differs')
 g.require(oldafter['originalFernMaterialReport']==base['report']['materialReport'],'Original R34 fern material changed')
 ferncontrols=oldafter['preserved36FernControls'];g.require(len(ferncontrols)==3 and sum(len(c['rootIds'])for c in ferncontrols.values())==36,'All36 original ferns preserved required')
 for model,row in base['report']['newOwnedGroups'].items():
  control=ferncontrols[row['actor']];m=bundle['oldFernMeasurements'][model]
  for key in ('rootIds','recoveredValues','storedMatrices'):g.exact(control[key],m[key],'Original36 fern frame/raw order differs')
  g.require(before[row['actor']]==saved[row['actor']]and control['numCustomDataFloats']==0 and control['customData']==[],'Original fern policy/custom data differs')
 fresh=g.source_footprints(measurements,bundle);g.require(len(fresh)==len(r['sourceCrownMaskProof'])==384,'All384 complete source-matrix mask checks required')
 for actual,independent in zip(r['sourceCrownMaskProof'],fresh):
  for key in ('rootId','model','decodedSourceF32VerticesChecked','actualStoredMatrix','allSourceVerticesWithinMeasuredContainingCircle',
   'allVerticesAndFullCircleInOriginalBed','fullCircleExcludesOriginalSteps','vertexBedFitEstablishedByFullContainingCircle','contactPolicy'):
   g.exact(actual[key],independent[key],'Measured source/mask identity differs')
  g.require(all(type(actual[k])in(int,float)and math.isfinite(actual[k])and actual[k]>0 for k in ('actualContainingCircleRadiusCm','bedBoundaryCircleClearanceCm','stepBoundaryCircleClearanceCm'))
   and math.isfinite(actual['contactArithmeticDeltaCm'])and abs(actual['contactArithmeticDeltaCm'])<=1e-7,'Recorded strict circle/contact numeric gate differs')
 packages=g.package_paths(source['models'])+[p.split('.')[0]for p in r['materialReport']['newPackageAssets']]
 g.require(set(packages)==set(r['newPackages'])and len(r['newPackages'])==15 and set(p.split('.')[0]for p in r['importPipelineAssets'])=={g.PREFIX+'/Pipeline/'+k for k in ('Assets','Materials','Level')},'Exact6mesh/1graph5tex/3pipeline packages required')
 g.require(g.validate_content(base['content'],side(r['afterContentInventory']),r['newPackages'])==r['assetDelta'],'Map-only+15 recorded Content closure differs')
 return {'mode':'saved-384-original-periwinkle-low-garden-composition','nativeProcessId':NATIVE_PID,**g.COUNTS,
  'originalOrnamentalMembersPreserved':12,'originalFlowersPreserved':41,'originalR34FernRootsPreserved':36,
  'wholeActorCounterfactualValidated':True,'retainedRawMatrixOrderMainSeedCustomDataExact':True,
  'fullNativeF32PositionUv0Uv1TopologyProofTriangles':34350,'sourceCrownVertices':1981184,'sourceCrownInequalitiesIndependentlyExecuted':True,
  'freshDerivedRadiusHeightStatsBitEqualityRequired':False,'storedNewMatricesIndependentlyDecodedAfterSaveByCpuChecker':False,
  'executedNativeSavedNewMatrixGateAndSavedComponentHashesVerified':True,'AdditionalRandomSeedsReadbackAvailable':False,
  'perInstanceShaderRandomValuePreservationClaimed':False,'nativeNormalTangentReadbackAvailable':False,'nativeColor0Color1ReadbackAvailable':False,
  'freshNativeAssetDecodePerformedByCpuChecker':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,
  'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}


def main():
 p=argparse.ArgumentParser();p.add_argument('report',type=Path);p.add_argument('--guard-tests',action='store_true');a=p.parse_args()
 g.require(REPORT_SHA is not None and a.report.resolve()==REPORT and g.sha(REPORT)==REPORT_SHA,'Only actual unchanged successful R36 report accepted; native binding pending')
 r=g.read(REPORT);validate_terminal_and_root_audit(r);g.require(g.sha(g.PLAN)==PLAN_SHA,'Frozen selected R36 plan differs');plan,bundle=g.validate_plan();preflight=side(r['sourcePreflight'])
 result=validate_saved(r,plan,bundle,preflight)
 if a.guard_tests:
  mutations=[('status','running'),('nativeProcessId',NATIVE_PID+1),('nativeApplied',False),('fullPhotorealismAccepted',True),
   ('allOriginal12Ornamentals41Flowers36FernsRawControlsExact',False),('actualCounts',{**g.COUNTS,'savedActors':5354})]
  for key,value in mutations:
   changed=copy.deepcopy(r);changed[key]=value
   try:validate_header(changed)
   except(RuntimeError,KeyError):continue
   raise RuntimeError('Adversarial saved header accepted: '+key)
  result['adversarialHeaderGuards']=6
 print(json.dumps(result,allow_nan=False))


if __name__=='__main__':main()
