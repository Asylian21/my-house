// New constructed changed-contract fixtures. They do not establish native integration.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {validateGardenYardHeader,validateGardenYardReportNames,validateGardenYardContent,validateGardenYardRootAudit} from '../scripts/unreal/exterior-editor-source-r28.mjs';
const root='/Users/davidzita/www/dom',source=root+'/output/unreal/exterior-20261002-r37b',project=source+'/Project/BreziTwin';
const plan=JSON.parse(await fs.readFile(root+'/output/unreal/exterior-garden-yard-integration-20261002-r37-native-study-r2/garden-yard-integration-plan-r2.json','utf8'));
const repair=JSON.parse(await fs.readFile(root+'/output/unreal/exterior-20261002-r35b/context-yard-repair-native-report-r2.json','utf8'));
function fixture(){
 const r={schema:plan.schema,schemaVersion:2,owner:plan.nativeOwner,status:'verified-saved-clean-selected-garden-and-yard-integration',output:source,project,nativeProcessId:1999,
  selectedPlan:{sha256:'e571d1eab5d9635aa5ac9a43e71d5cdd0795633121318c2fdc24e664066aa303'},sourcePreflight:{sha256:'85814b5295b6157c3c8a421eb27c54c2604ad3ed863aea070768a36b6d6f93e5'},baseNativeReport:plan.baseNativeReport,repairSchema:plan.repairSchema,priorFailedAttempt:plan.priorFailedAttempt,materialReaderDispatch:plan.materialReaderDispatch,materialGraphDiagnosticFiles:{before:Array(61).fill({}),saved:Array(61).fill({})},
  activeDesign:plan.activeDesign,setbacksMm:plan.setbacksMm,actualCounts:plan.expectedCounts,newActorMapping:Object.fromEntries(Object.keys(plan.addedActorTemplates).map((p,i)=>[p,'/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.CPU_NEW_'+i])),
  materialReadback:{scopedMaterialGraphs:64,graphs:Object.fromEntries(Array.from({length:64},(_,i)=>['/Fixture/Graph'+i,{graphSha256:'a'.repeat(64)}])),scopedTextureObjects:96,
   textureAssets:Array.from({length:96},(_,i)=>'/Fixture/Texture'+i),newTextureObjects:0,originalTexturePackageBytesProtected:true,sharedNewYardTextureSettingsVerified:true,all96NativeTextureSettingsRecomputed:false,materialPackagesIndependentlyUnloaded:false},
  geometryReadback:{ground:{entry:{triangles:1996},court:{triangles:2523},substrate:{triangles:28359}},originalEcology:repair.repairA.nativeSelectedEcologyGeometry,newLowRootFootprints:Array.from({length:1274},(_,i)=>({rootId:'CPU_'+i})),all1274ContainingCirclesAndNativeThreeLodVerticesInsideSourceMasks:true,nativeNormalTangentReadbackAvailable:false},
  newPackages:plan.copiedPackageScope.map(v=>v.asset)};
 for(const k of ['nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged','originalSelectedGardenUnchanged','all384Periwinkle36Ferns12Heroes41FlowersRawControlsExact',
  'all78Trees8949GrassAnd13YardShrubsRawControlsExact','all1274ConstructorInputRecoveredStoredMatricesBinary64Exact','all1919SurvivorRawMatricesOrderMainSeedCustomDataExact'])r[k]=true;
 for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified','wholeR35MapOrR30GardenImported','materialPackagesIndependentlyUnloaded',
  'nativeNormalTangentReadbackAvailable','AdditionalRandomSeedsReadbackAvailable','perInstanceShaderRandomValuePreservationClaimed','existingTransformOrSeedSetterUsed'])r[k]=false;
 return r;
}
const validate=r=>validateGardenYardHeader(r,{source,project},{nativePid:1999});
test('selected garden plus scoped14-package fixture keeps exact full census and evidence limits',()=>validate(fixture()));
test('whole donor map, old seed mutation and inflated material/LOD evidence reject',()=>{
 for(const mutate of [r=>r.wholeR35MapOrR30GardenImported=true,r=>r.existingTransformOrSeedSetterUsed=true,r=>r.materialReadback.all96NativeTextureSettingsRecomputed=true,
  r=>r.geometryReadback.originalEcology[Object.keys(r.geometryReadback.originalEcology)[0]].lods[0].fullNativeSourcePositionUvTopologyWindingVerified=false,r=>r.actualCounts.newRoots=1300]){
  const r=structuredClone(fixture());mutate(r);assert.throws(()=>validate(r));}
});
test('colliding relocated actor identities or wrong selected garden base reject',()=>{
 let r=fixture();const ids=Object.keys(r.newActorMapping);r.newActorMapping[ids[1]]=r.newActorMapping[ids[0]];assert.throws(()=>validate(r));
 r=fixture();r.baseNativeReport={sha256:'d233329bee2ffcb95419c8266ff8c1f50931ba8f642ded23ab20330f1d334cb8'};assert.throws(()=>validate(r));
});
test('only known combined report names may dispatch, no copied or failed native family',()=>{
 validateGardenYardReportNames(['garden-yard-integration-native-report-r2.json']);
 for(const n of ['garden-yard-integration-native-report.json','garden-periwinkle-native-report-r2.json','context-yard-repair-native-report-r2.json','exterior-import-report.json'])assert.throws(()=>validateGardenYardReportNames(['garden-yard-integration-native-report-r2.json',n]));
});
test('copied exact donor packages permit only original map delta; camera and periwinkle bytes stay exact',()=>{
 const before=Object.fromEntries(Array.from({length:4083},(_,i)=>['Old/'+i+'.uasset',{sha256:'a'.repeat(64),bytes:1}]));
 before['Brezi/Maps/Brezi.umap']={sha256:'a'.repeat(64),bytes:2};before['Data/viewpoints.json']={sha256:'b'.repeat(64),bytes:3};before['Brezi/GardenPeriwinkle20261002R36/Materials/M_original.uasset']={sha256:'c'.repeat(64),bytes:4};
 const copies=plan.copiedPackageScope,after=structuredClone(before);after['Brezi/Maps/Brezi.umap']={sha256:'d'.repeat(64),bytes:5};for(const row of copies)after[row.relativeContentPath]={sha256:row.source.sha256,bytes:row.source.bytes};
 const delta={newPackages:14,newPackageBytes:1787793,onlyOriginalMapChanged:true};validateGardenYardContent(before,after,copies,delta);
 for(const key of ['Data/viewpoints.json','Brezi/GardenPeriwinkle20261002R36/Materials/M_original.uasset',copies[0].relativeContentPath]){
  const bad=structuredClone(after);bad[key]={sha256:'e'.repeat(64),bytes:9};assert.throws(()=>validateGardenYardContent(before,bad,copies,delta));}
});

test('actual root byte-audit shape binds exact graph diagnostics and preserves CPU evidence limits',async()=>{
 const folder=root+'/output/unreal/exterior-20261002-r37b',r=JSON.parse(await fs.readFile(folder+'/garden-yard-integration-native-report-r2.json','utf8'));
 const a=JSON.parse(await fs.readFile(folder+'/root-native-success-byte-audit-r37b-r2.json','utf8'));
 const context={reportPin:a.report,processPin:a.process};validateGardenYardRootAudit(a,r,context);
 for(const mutate of [v=>v.stored1919EcologySurvivorsRawOrderSeedCustomExact=false,v=>v.currentContentFiles=4086,
  v=>v.nativeCreatedAssetPackages=1,v=>v.newNativeActorOrGeometryDecodeByThisCpuAudit=true,v=>v.actualCompleteGraphDiagnosticPins.pop(),
  v=>v.exactReaderDispatch.basic.pop(),v=>v.sourcePinsBeforeAfterAndCurrentExact=850]){
  const bad=structuredClone(a);mutate(bad);assert.throws(()=>validateGardenYardRootAudit(bad,r,context));}
});
