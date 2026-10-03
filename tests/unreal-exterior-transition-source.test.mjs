// Adversarial host fixtures for source/native receipt boundaries. The simulated
// saved fields below are test data and are never published as a native receipt.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {validateNeighborhoodTransitionReceipt,validateNeighborhoodTransitionPlan} from '../scripts/unreal/exterior-transition-source.mjs';

const root=resolve(import.meta.dirname,'..');
const planPath=resolve(root,'output/unreal/exterior-neighborhood-transition-20261001-r1-study/transition-plan.json');
const bytes=await readFile(planPath),sourcePlan=JSON.parse(bytes);
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const basis=JSON.parse(await readFile(resolve(root,'output/unreal/exterior-20261001-r10/exterior-import-report.json')));
const context=JSON.parse(await readFile(sourcePlan.sourceContext.path));
const topologyPath=resolve(root,'output/unreal/exterior-validation-20260930-r1/r12-native-ground-topology-baseline.json');
const topologyBytes=await readFile(topologyPath),topology=JSON.parse(topologyBytes);
const KEY='context_continuous_unbuilt_ground';

function fixture() {
  const plan=structuredClone(sourcePlan),condition=plan.conditionTexture;
  const materials=structuredClone(basis.materials);
  materials.materials[KEY]={asset:'/Game/Brezi/Exterior20260926/Materials/M_Continuous.M_Continuous'};
  const metadata={status:'saved-continuous-unbuilt-ground-awaiting-native-reload',materialKey:KEY,
    plan:planPath,planSha256:hash(bytes),sourcePlan:{path:planPath,sha256:hash(bytes)},original40GraphsUnchanged:true,
    fieldMacroAndProtectedCameraOrthoUnchanged:true,sourceGroundBindingsChanged:false,nativeAppearanceAccepted:false,
    nativeVisualAccepted:false,fullPhotorealismAccepted:false,performanceAccepted:false,priorMaterialCount:40,finalMaterialCount:41,textureCount:74,
    condition:{path:condition.path,sha256:condition.sha256,role:'ground_condition',dimensions:[1024,1024],worldCmToUvRows:condition.worldCmToUvRows,
      sourceLicense:'LicenseRef-Project-Authored',sourcePage:resolve(root,plan.owner),sRGB:false,uncompressedRgba8:true,compressionNonePropertyExposed:false,
      uncompressedFormatBasis:'TC_VectorDisplacementmap -> NameBGRA8 (UE5.8 native source)',
      compressionSettings:'TC_VECTOR_DISPLACEMENTMAP',addressMode:'clamp',mipGenSettings:'TMGS_FROM_TEXTURE_GROUP',ordinaryMips:true,
      automaticViewMipBias:false,sourceEncodingOverride:'None',sourceEncodingReadback:'TSE_NONE'}};
  materials.neighborhoodTransition=metadata;
  materials.textures.ground_condition_fixture={role:'ground_condition',sourcePath:condition.path,sourceSha256:condition.sha256,
    sourceLicense:metadata.condition.sourceLicense,sourcePage:metadata.condition.sourcePage,addressMode:'clamp',
    sourceEncodingOverride:'None',sourceEncodingReadback:'TSE_NONE',width:1024,height:1024};
  const geometry={actors:structuredClone(basis.geometry.actors),meshes:structuredClone(basis.geometry.meshes),groups:{}};
  for(const group of plan.groups)geometry.groups[group.id]={mesh:basis.savedPlantReadback.find(row=>row.id===group.meshId).mesh,
    instances:group.instances.length,cullStartCm:3200,cullEndCm:4000,qualityDetail:false,transformsSha256:'a'.repeat(64)};
  const report={activeDesign:plan.activeDesign,inputFiles:{...plan.inputFiles,[planPath]:hash(bytes),[condition.path]:condition.sha256,[topologyPath]:hash(topologyBytes)},
    materials,geometry,savedPlantReadback:basis.savedPlantReadback,
    materialReadback:{status:'verified-saved-exterior-materials',materials:41,textures:74},
    neighborhoodTransition:{plan:planPath,planSha256:hash(bytes),nativeRenderedVerified:false,nativeVisualAccepted:false,performanceAccepted:false,
      sourceMaterialBindings:structuredClone(plan.materialBindingProposal),
      nativeTopologyBaseline:{path:topologyPath,sha256:hash(topologyBytes)},
      validation:{status:'verified-source-neighborhood-transition-native-inputs',owner:'scripts/unreal/exterior-neighborhood-transition-native.py',
        sourcePlan:{path:planPath,sha256:hash(bytes)},sourceGroundBindings:65,groups:158,instances:7000,
        allLodTriangles:[6351095,3487981,1584502],originalRemovalIndicesPreserved:47203,originalVegetationRestoredOrMoved:0,hiddenOriginalActors:0,
        sourceGeometryAndOriginalMaterialsUnchanged:true,actualAllLodFullCircularCrownsAndSourceGroundChecked:true,
        futureSharedMaterialMustPreserveFieldMacroAndProtectedCameraOrtho:true,nativeVisualAccepted:false,performanceAccepted:false,
        surveyedLandUseBotanyOrElevation:false,condition:{all1048576ConditionPixelsVerified:true},inputFiles:plan.inputFiles},
      savedReadback:{status:'verified-saved-neighborhood-transition',instances:7000,allNewVisualsNoCollision:true,
        sourceGroundBoundsTopologyAndOriginVerified:true,sourceTransformsComparedAfterReload:true,nativeVisualAccepted:false,performanceAccepted:false,
        maximumPositionErrorCm:.001,maximumScaleError:1e-7,maximumQuaternionErrorSignEquivalent:1e-7,
        groupIds:plan.groups.map(row=>row.id),materialBindings:plan.materialBindingProposal.map(row=>({sourceMeshId:row.sourceMeshId,
          actor:geometry.actors[row.sourceMeshId],mesh:geometry.meshes[row.sourceMeshId],material:materials.materials[KEY].asset,
          sourceGeometrySha256:row.sourceGeometrySha256,triangles:context.meshes.find(mesh=>mesh.id===row.sourceMeshId).indices.length/3}))}}};
  for(const row of report.neighborhoodTransition.savedReadback.materialBindings) {
    const original=topology.rows.find(item=>item.sourceMeshId===row.sourceMeshId);
    row.renderTriangles=original.renderTriangles;row.descriptionVertices=original.descriptionVertices;
  }
  return {report,plan};
}
const check=({report,plan})=>validateNeighborhoodTransitionPlan(report,plan,context,basis,topology);

test('actual source plan and historical original graphs pass a clearly simulated host receipt',async()=>{
  const f=fixture();check(f);
  assert.equal(hash(await readFile(sourcePlan.conditionTexture.path)),sourcePlan.conditionTexture.sha256);
  assert.equal(hash(await readFile(resolve(root,sourcePlan.owner))),sourcePlan.generatorSha256);
});

test('old receipts remain optional but an orphan continuous material is rejected',()=>{
  validateNeighborhoodTransitionReceipt({materials:{}});
  assert.throws(()=>validateNeighborhoodTransitionReceipt({materials:{neighborhoodTransition:{}}}));
});

test('source substitution and unpinned masks cannot impersonate the frozen transition',()=>{
  for(const mutate of [f=>{f.report.neighborhoodTransition.planSha256='b'.repeat(64);},
    f=>{delete f.report.inputFiles[f.plan.conditionTexture.path];},f=>{f.plan.owner='other-generator.py';},
    f=>{f.plan.housePlacement.eastSetbackMm=2500;}]){const f=fixture();mutate(f);assert.throws(()=>check(f));}
});

test('source or saved checks cannot promote appearance or claim a survey',()=>{
  for(const mutate of [f=>{f.report.neighborhoodTransition.nativeRenderedVerified=true;},
    f=>{f.report.neighborhoodTransition.validation.surveyedLandUseBotanyOrElevation=true;},
    f=>{f.report.materials.neighborhoodTransition.fullPhotorealismAccepted=true;},
    f=>{f.report.neighborhoodTransition.savedReadback.performanceAccepted=true;}]){const f=fixture();mutate(f);assert.throws(()=>check(f));}
});

test('mask role, license, transfer, mip policy and world frame are independently guarded',()=>{
  for(const mutate of [f=>{f.report.materials.neighborhoodTransition.condition.role='ortho_projection';},
    f=>{f.report.materials.neighborhoodTransition.condition.sourceLicense='CC0-1.0';},
    f=>{f.report.materials.neighborhoodTransition.condition.automaticViewMipBias=true;},
    f=>{f.report.materials.neighborhoodTransition.condition.compressionNone=true;},
    f=>{f.report.materials.neighborhoodTransition.condition.worldCmToUvRows[0][0]*=2;},
    f=>{f.report.materials.textures.ground_condition_fixture.sourceEncodingReadback='TSE_S_RGB';}]){const f=fixture();mutate(f);assert.throws(()=>check(f));}
});

test('unchanged original graph and texture claims are checked against the pinned native basis',()=>{
  for(const mutate of [f=>{f.report.materials.materials.context_meadow.graphSha256='b'.repeat(64);},
    f=>{f.report.materials.materials.context_fallow.recipe.normalStrength=.1;},
    f=>{Object.values(f.report.materials.textures)[0].sourceLicense='invented';}]){const f=fixture();mutate(f);assert.throws(()=>check(f));}
});

test('saved ground bindings and topology cannot be exchanged or omit one parcel',()=>{
  for(const mutate of [f=>{f.report.neighborhoodTransition.savedReadback.materialBindings.pop();},
    f=>{f.report.neighborhoodTransition.savedReadback.materialBindings[0].mesh='wrong';},
    f=>{f.report.neighborhoodTransition.savedReadback.materialBindings[0].triangles+=1;},
    f=>{f.report.neighborhoodTransition.savedReadback.materialBindings[0].renderTriangles+=1;},
    f=>{f.report.neighborhoodTransition.sourceMaterialBindings[0].sourceGeometrySha256='b'.repeat(64);}]){const f=fixture();mutate(f);assert.throws(()=>check(f));}
});

test('saved compact clumps must retain exact inventory, culls, density and finite transform bounds',()=>{
  for(const mutate of [f=>{f.report.geometry.groups[f.plan.groups[0].id].cullEndCm=12000;},
    f=>{f.report.geometry.groups[f.plan.groups[0].id].qualityDetail=true;},
    f=>{f.report.geometry.groups[f.plan.groups[0].id].instances+=1;},
    f=>{f.report.neighborhoodTransition.savedReadback.maximumPositionErrorCm=.003;},
    f=>{f.report.neighborhoodTransition.savedReadback.maximumScaleError=NaN;},
    f=>{f.report.neighborhoodTransition.validation.originalVegetationRestoredOrMoved=1;}]){const f=fixture();mutate(f);assert.throws(()=>check(f));}
});
