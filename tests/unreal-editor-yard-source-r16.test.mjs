// CPU source receipt guards only; never an Unreal or appearance run.
import test from 'node:test';
import assert from 'node:assert/strict';
import {validateYardHeader,validateYardReportNames,validateYardContent} from '../scripts/unreal/exterior-editor-source-r16.mjs';
const clone=v=>structuredClone(v),source='/fixture/own-r28b',project=source+'/Project/BreziTwin';
function header(){return {schema:'brezi-context-yard-purposeful-ground-and-shrubs-r28-r2',owner:'scripts/unreal/exterior-context-yard-native-r28-r2.py',
  status:'verified-saved-purposeful-context-yards-overlay',output:source,project,
  sourceGeometryPlan:{sha256:'f0f03736fc1c6d0992e2746626e35750dcacd575770b06f5f1308511a0358cb3'},
  sourcePreflight:{sha256:'3482b79d8060305004ed9132c6bd67549fce634295e1fe39dfd14d60c221399a'},
  nativeApiRepairSupplement:{sha256:'ba75c0022da1a5ad9294a05a68beb6d33de02c1207b663d9c51226ab7255889a'},
  baseNativeReport:{sha256:'5575c0e37a9d48733b5c7ed3746f1731cc2b7958634a845c87b9700ff4fc9498'},
  nativeAppearanceAccepted:false,fullPhotorealismAccepted:false,performanceAccepted:false,shippingVerified:false,
  materialPackagesIndependentlyUnloaded:false,nativeNormalTangentReadbackAvailable:false,landUseOrDoorObserved:false,measuredElevation:false,
  nativeApplied:true,savedMapUnloadedReloaded:true,originalSavedR27Unchanged:true,sourceInputsUnchanged:true,
  allOriginalActorPoliciesAndTransformsPreserved:true,originalPlantAssetsBytePreserved:true,
  staticMeshEditorSubsystemVerifiedAvailable:true,assetEditorSubsystemVerifiedAvailable:true,
  activeDesign:{variant:'C',heatingLayout:'B',livingLayout:'B'},setbacksMm:{street:3000,east:3000},
  originalActorCount:5343,savedActorCount:5350,newGroundActors:4,newHismGroups:3,newShrubRoots:13,newPackageCount:9,
  scopedMaterialGraphs:56,scopedTextureObjects:77,newTextureObjects:0,originalGrassMembersPreserved:8949,
  savedReadback:{fullHismComponents:2312,fullHismInstances:676957,fullActorCounterfactualValidated:true}};}
test('typed header permits only the repaired saved source scope with open acceptance',()=>{
  validateYardHeader(header(),{source,project});
  for(const [key,value]of [['status','failed'],['owner','scripts/unreal/exterior-context-yard-native-r28.py'],
    ['nativeAppearanceAccepted',true],['nativeNormalTangentReadbackAvailable',true],['newShrubRoots',14]]){
    const r=header();r[key]=value;assert.throws(()=>validateYardHeader(r,{source,project}));
  }
});
test('original/donor/plain-R1 report coexistence is rejected',()=>{
  const selected='context-yard-native-report-r2.json';validateYardReportNames([selected]);
  for(const old of ['context-yard-native-report.json','context-yard-native-report-r3.json','exterior-import-report.json',
    'realism-clean-integration-native-report.json','foreground-overlay-report-r2.json'])assert.throws(()=>validateYardReportNames([selected,old]));
});
function content(){
  const before=Object.fromEntries(Array.from({length:4032},(_,i)=>['Brezi/Old/'+i+'.uasset',{sha256:'a'.repeat(64),bytes:1}]));
  before['Brezi/Maps/Brezi.umap']={sha256:'b'.repeat(64),bytes:2};before['Data/viewpoints.json']={sha256:'c'.repeat(64),bytes:3};
  const packages=Array.from({length:9},(_,i)=>'Brezi/ContextYard20261002R28/Own/'+i+'.uasset');
  const after=clone(before);after['Brezi/Maps/Brezi.umap']={sha256:'d'.repeat(64),bytes:4};
  for(const k of packages)after[k]={sha256:'e'.repeat(64),bytes:5};
  const delta={changedOriginalFiles:['Brezi/Maps/Brezi.umap'],newPackageFiles:[...packages].sort(),originalContentFiles:4034,savedContentFiles:4043,newPackages:9};
  return {before,after,packages,delta};
}
test('exact nine-package map-only Content delta rejects camera or original asset mutations',()=>{
  const r=content();validateYardContent(r.before,r.after,r.packages,r.delta);
  for(const key of ['Data/viewpoints.json','Brezi/Old/0.uasset']){
    const after=clone(r.after);after[key]={sha256:'f'.repeat(64),bytes:6};assert.throws(()=>validateYardContent(r.before,after,r.packages,r.delta));
  }
});
test('unowned new package and missing inherited asset cannot hide in matching counts',()=>{
  const r=content(),after=clone(r.after);delete after[r.packages[0]];after['Brezi/Unowned.uasset']={sha256:'f'.repeat(64),bytes:9};
  assert.throws(()=>validateYardContent(r.before,after,r.packages,r.delta));
  const changed=clone(r.after);delete changed['Brezi/Old/1.uasset'];changed['Brezi/ReplacedOld.uasset']={sha256:'f'.repeat(64),bytes:9};
  assert.throws(()=>validateYardContent(r.before,changed,r.packages,r.delta));
});
