// Constructed source/receipt fixtures. These do not establish native R36 import.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {validatePeriwinkleHeader,validatePeriwinkleReportNames,validatePeriwinkleContent} from '../scripts/unreal/exterior-editor-source-r27.mjs';
const root='/Users/davidzita/www/dom',source=root+'/output/unreal/exterior-20261002-r36b',project=source+'/Project/BreziTwin';
const proposal=JSON.parse(await fs.readFile(root+'/output/unreal/exterior-garden-periwinkle-20261002-r36-source-study/periwinkle-source-plan.json','utf8'));
const modelNames=Array.from({length:6},(_,i)=>`periwinkle_plant_0${i+1}_LOD0`),triangles=[11252,9096,5338,4108,3078,1478];
const prefix='Brezi/GardenPeriwinkle20261002R36/',asset='/Game/'+prefix+'Materials/M_ph_original_periwinkle_r36.M_ph_original_periwinkle_r36';
const counts={originalActors:5354,savedActors:5360,fullHismComponents:2322,fullHismInstances:676957,originalGardenRoots:473,retainedOriginalGardenRoots:53,
  preservedR34FernRoots:36,newOriginalPeriwinkleRoots:384,newMeshAssets:6,newMaterialGraphs:1,newTextureObjects:5,newPipelineAssets:3,newPackages:15,
  scopedMaterialGraphs:61,scopedTextureObjects:96,contentFiles:4086,protectedFiles:132};
function fixture(){
 const r={schema:'brezi-garden-original-periwinkle-composition-native-r36',schemaVersion:2,owner:'scripts/unreal/exterior-garden-periwinkle-native-r36-r2.py',
  status:'verified-saved-384-original-periwinkle-low-garden-composition',output:source,project,nativeProcessId:1999,
  repairSchema:'brezi-original-periwinkle-source-geometry-identity-repair-r2',immutableSourceGuard:{sha256:'4dd86369ae79b80e58296329b0e1b183a45c26dd7f3b609f7795e42421804138'},
  importIdentityEvidence:{failedNativeProcess:{pid:42780,exitCode:255,sourcePinCount:560},nativeOriginalNodeLabelIdentityObserved:false,persistedPartialMeshDiagnosticAvailable:false,
   failedPartialFilesContainSavedMeshPackages:false,sixMeshIdentityVerifiedByThisSourceReceipt:false,sourceGeometryOrExpectedCornerOrderChanged:false,originalSourceControlMathChanged:false,guardRelaxed:false},
  allSixImportedMastersIdentifiedByFullSourceCorners:true,actorLabelsUsedForSourceMeshIdentity:false,observedNonrenderingImportContainers:[],importTemporaryActorInventory:{sha256:'b'.repeat(64)},
  selectedPlan:{sha256:'71de87f91926f059a7553e8553927151d8aa9873040dbb56d20d31203e37a640'},sourceProposal:{sha256:'93b4bc17203f10b5c14acd036dd942f8d2bf0b99ec1744e6638e7a29502a8b96'},
  sourcePreflight:{sha256:'0629127c96e608f34082040587a5b9c8120374290cdef7e76d89b490e799ca9c'},baseNativeReport:{sha256:'d233329bee2ffcb95419c8266ff8c1f50931ba8f642ded23ab20330f1d334cb8'},
  activeDesign:{variant:'C',heatingLayout:'B',livingLayout:'B'},setbacksMm:{street:3000,east:3000},actualCounts:counts,contactWorldBottomArithmeticCapCm:1e-7,
  newOwnedGroups:{},nativeGeometryReadback:{},sourceCrownMaskProof:[],originalSourceNodeNativeMeshBindings:[]};
 for(const k of ['nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged','originalSavedR34Unchanged','allOriginal12Ornamentals41Flowers36FernsRawControlsExact',
  'allOriginal8949GrassAnd78TreesRawControlsExact','all384SourceOriginalRootsRetiredOnceAndReplacedOnce','allOriginalSourceSixAttributesAndIndexBinBytesPreserved','sourceHeightRoleChanges384Explicit'])r[k]=true;
 for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified','ecologicalFitVerified','surveyedPlacementVerified',
  'nativeNormalTangentReadbackAvailable','nativeColor0Color1ReadbackAvailable','meshMaterialPackagesIndependentlyUnloaded','AdditionalRandomSeedsReadbackAvailable','retainedTransformRecompositionPerformed',
  'seedMutationPerformed','perInstanceShaderRandomValuePreservationClaimed','yardIntegrationApplied','derivedContactFloatingPointBitEqualityClaimed','sourceGroundElevationSurveyed'])r[k]=false;
 for(const [i,model]of modelNames.entries()){
  const ids=proposal.proposedPlacements.filter(p=>p.model===model).map(p=>p.rootId),mesh='/Game/'+prefix+`Geometry/StaticMeshes/${model}.${model}`;
  r.newOwnedGroups[model]={actor:'/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.CPU_FIXTURE_'+i,instances:ids.length,rootIds:ids,mesh,material:asset};
  const proof={asset:mesh,lodCount:1,sections:1,triangles:triangles[i],nativeCornerSha256:'a'.repeat(64),fullOrderedNativeF32PositionUV0UV1WindingVerified:true,
   allSixOriginalSourceAttributeBytesPreserved:true,nativeTangentsRequestedFromOriginalUv0:true};
  for(const k of ['originalProviderLodChainPresent','nativeNormalTangentReadbackAvailable','nativeColor0Color1ReadbackAvailable','sourceTangentsPresent','nativeTangentGenerationNumericallyVerified','nativeNaniteRequested','meshPackageIndependentlyUnloaded'])proof[k]=false;
  r.nativeGeometryReadback[model]=proof;
  r.sourceCrownMaskProof.push(...ids.map(rootId=>({rootId,allVerticesAndFullCircleInOriginalBed:true,fullCircleExcludesOriginalSteps:true,contactArithmeticDeltaCm:0,freshDerivedStatisticsBitEqualityRequired:false})));
  r.originalSourceNodeNativeMeshBindings.push({sourceNodeId:model,meshNameUsedForSourceIdentity:false,actorLabelUsedForSourceIdentity:false,uniqueTriangleCountUsedOnlyForCandidateRouting:true,
   sourceIdentityFromTriangleCountAlone:false,sourceIdentityFromActorOrMeshName:false,fullOrderedNativeF32PositionUV0UV1WindingVerified:true,triangles:triangles[i],sections:1,nativeCornerSha256:'a'.repeat(64),
   actualTemporaryActor:'/Fixture/Actor'+i,actualTemporaryActorLabel:'Arbitrary fixture label '+i,asset:'/Game/'+prefix+'Geometry/provider_'+i});
 }
 r.wholeOriginalLowGroupRetirements=proposal.retireWholeOriginalGroups.map((p,i)=>({actor:p.actor,rootIds:p.rootIds,retiredRoots:p.rootIds.length,entireComponentMembersCleared:true,
  actorOrComponentDeleted:false,survivorRecompositionPerformed:false,seedSetterPerformed:false,AdditionalRandomSeedsReadbackAvailable:false,perInstanceShaderRandomValuePreservationClaimed:false}));
 const m={schema:'brezi-original-periwinkle-five-map-material-r36',owner:'scripts/unreal/exterior-garden-periwinkle-materials-r36.py',status:'owned-original-five-map-periwinkle-material-created',
  sourceRecipe:{sha256:'04a7223f7e5ba93c88f6e7438d3776283a241782f4b00c52fba5c06c98cc1b98'},materialCount:1,textureObjectCount:5,newPackageAssets:[asset,...Array.from({length:5},(_,i)=>'/Game/'+prefix+'Textures/CPU_MAP_'+i)],
  compileErrors:[],sourceOriginalAlphaMode:'BLEND',ownedUnrealBlendMode:'MASKED',sourcePngBits:16,source16BitDoesNotProveNativePixelFormat:true,asset};
 for(const k of ['originalTexturePixelsEdited','nativeImportedPixelsDecoded','nativeSourcePixelFormatReadbackAvailable','nativeGpuPixelFormatReadbackAvailable','nativeNormalTangentReadbackAvailable',
  'materialPackagesIndependentlyUnloaded','sourceOpticalModelExactlyReproduced','physicalOpticalCalibrationAccepted','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted'])m[k]=false;
 r.materialReport=m;return r;
}
const validate=r=>validatePeriwinkleHeader(r,{source,project},{nativePid:1999});
test('known source-schema fixture keeps whole384, six original forms and all acceptance limits',()=>validate(fixture()));
test('mixed retirement, native evidence inflation and missing UV1 proof reject',()=>{
 for(const mutate of [r=>r.wholeOriginalLowGroupRetirements[0].rootIds[0]='foreign',r=>r.nativeColor0Color1ReadbackAvailable=true,
  r=>delete r.nativeGeometryReadback[modelNames[0]].fullOrderedNativeF32PositionUV0UV1WindingVerified,r=>r.materialReport.ownedUnrealBlendMode='BLEND',r=>r.schemaVersion=1,r=>r.owner='scripts/unreal/exterior-garden-periwinkle-native-r36.py',r=>r.originalSourceNodeNativeMeshBindings[0].sourceIdentityFromTriangleCountAlone=true]){
  const r=fixture();mutate(r);assert.throws(()=>validate(r));}
});
test('original node identity count and one-source-root reuse reject',()=>{
 let r=fixture();r.originalSourceNodeNativeMeshBindings[1].sourceNodeId=modelNames[0];assert.throws(()=>validate(r));
 r=fixture();r.newOwnedGroups[modelNames[1]].rootIds[0]=r.newOwnedGroups[modelNames[0]].rootIds[0];assert.throws(()=>validate(r));
});
test('only the selected typed report filename is accepted',()=>{
 validatePeriwinkleReportNames(['garden-periwinkle-native-report-r2.json','garden-periwinkle-native-r2.log.json']);
 for(const n of ['exterior-import-report.json','garden-fern-only-native-report.json','garden-periwinkle-native-report.json'])assert.throws(()=>validatePeriwinkleReportNames(['garden-periwinkle-native-report-r2.json',n]));
});
test('map-only old delta with15 own packages preserves camera/source materials',()=>{
 const before=Object.fromEntries(Array.from({length:4069},(_,i)=>['Old/'+i+'.uasset',{sha256:'a'.repeat(64),bytes:1}]));
 before['Brezi/Maps/Brezi.umap']={sha256:'a'.repeat(64),bytes:2};before['Data/viewpoints.json']={sha256:'b'.repeat(64),bytes:3};
 const packages=Array.from({length:15},(_,i)=>prefix+'CPU_PACKAGE_'+i+'.uasset'),after=structuredClone(before);after['Brezi/Maps/Brezi.umap']={sha256:'c'.repeat(64),bytes:4};
 for(const p of packages)after[p]={sha256:'d'.repeat(64),bytes:1};
 const delta={changedOriginalFiles:['Brezi/Maps/Brezi.umap'],newOwnedPackages:[...packages].sort(),originalContentFiles:4071,savedContentFiles:4086,newPackages:15};
 validatePeriwinkleContent(before,after,packages,delta);after['Data/viewpoints.json']={sha256:'e'.repeat(64),bytes:3};assert.throws(()=>validatePeriwinkleContent(before,after,packages,delta));
});
