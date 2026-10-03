// Focused R39/R3 saved-source dispatch and exact recorded-pose guards; no UE.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {test} from 'node:test';
import {fileURLToPath} from 'node:url';
import {requireActualBinding,validatePropsReportNames,validatePropsHeader,validatePropsContent,
  validateOriginalActorPreservation,validateConstructorMeasurements,validatePlanReportBindings,COUNTS} from './exterior-editor-source-r30.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const source=path.join(root,'output/unreal/exterior-20261002-r39c');
const data=async p=>JSON.parse(await fs.readFile(path.join(root,p),'utf8'));
const plan=await data('output/unreal/exterior-neighbor-props-20261002-r39-native-study-r3/neighbor-props-native-plan-r3.json');
const clone=v=>structuredClone(v);
const actual={reportSha:'1'.repeat(64),processSha:'2'.repeat(64),rawSha:'3'.repeat(64),auditSha:'4'.repeat(64),
  checkerSha:'5'.repeat(64),nativePid:999999,terminalPins:1293}; // fixture-only; no successful process is asserted.

test('actual saved-success closure remains mandatory and incomplete bindings reject',()=>{
  assert.throws(()=>requireActualBinding({...actual,reportSha:null}));
  assert.throws(()=>requireActualBinding({...actual,nativePid:null}));
  assert.throws(()=>requireActualBinding({...actual,terminalPins:1287}));
  requireActualBinding(actual);
});

test('failed, prior-version or copied report families cannot coexist with R3',()=>{
  validatePropsReportNames(['neighbor-props-native-report-r3.json','Project']);
  for(const name of ['neighbor-props-native-report.json','neighbor-props-native-report-r2.json','exterior-import-report.json'])
    assert.throws(()=>validatePropsReportNames(['neighbor-props-native-report-r3.json',name]));
  assert.throws(()=>validatePropsReportNames(['neighbor-props-native-report-r2.json']));
});

function header(){
  const row={schema:plan.schema,schemaVersion:3,owner:plan.nativeOwner,repairSchema:plan.repairSchema,
    binding:plan.binding,status:'verified-saved-six-whole-original-neighbor-prop-assemblies',nativeProcessId:actual.nativePid,
    project:path.join(source,'Project/BreziTwin'),output:source,actualCounts:COUNTS,baseNativeReport:plan.selectedNativeReport,
    selectedPlan:{sha256:'85ec3bb423fe8205b551629b2c4f374c715cd2adb2f5ea265c5dc38ada6aa7c5'},
    sourcePreflight:{sha256:'3bc9b4cb47603c572afb1502b4e591406d03b810084555bfc64f43f2d60be0b7'},
    inputFiles:{...plan.inputFiles,[path.join(root,'fixture-only-source-plan')]: '0'.repeat(64)},
    activeDesign:{variant:'C',heatingLayout:'B',livingLayout:'B'},setbacksMm:{street:3000,east:3000}};
  for(const k of ['nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged','allOriginal5364ActorsAnd2325RawControlsExact',
    'allOriginal66MaterialGraphsAuxObservedUsageExact','allOriginal97TextureSettingsAndSourceBytesExact','allFourOriginalPartsFullNativeIdentityVerified',
    'allSixIntendedAssembliesAndOriginalHoseNodePosesIndependentlyCompared','allEightMeasuredPosesExactBeforeAppliedAndSaved'])row[k]=true;
  for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified','activeOutputPromoted',
    'nativeNormalTangentReadbackAvailable','nativeGpuPixelFormatVerified','sourceOriginalGeometryAndPhotoPixelsEdited',
    'originalActorTransformInstanceOrMaterialSettersCalled','allSixAssemblyActorsIndividuallyVisibleVerified',
    'actualNativeSurfaceContactCollisionOrSurveyVerified','oldAdditionalRandomSeedRangesPreservationClaimed','nativeTangentsNumericallyVerified'])row[k]=false;
  return row;
}

test('saved header rejects wrong constructor-repair version, process, census and promoted evidence',()=>{
  validatePropsHeader(header(),{root,source,actual});
  for(const [key,value]of [['schemaVersion',2],['nativeProcessId',actual.nativePid+1],['nativeApplied',false],
    ['performanceAccepted',true],['repairSchema','brezi-r39-measured-f64-source-node-pose-repair-r2']]){
    const row=header();row[key]=value;assert.throws(()=>validatePropsHeader(row,{root,source,actual}));
  }
  assert.throws(()=>validatePropsHeader(header(),{root,source:source.replace('r39c','r39b'),actual}));
  const actualPlanFields={sourceProposal:plan.sourceProposal,baseNativeReport:plan.selectedNativeReport,
    selectedRootImageDecision:plan.selectedRootImageDecision,projectClone:plan.projectClone,
    baseNativeProcess:plan.selectedNativeProcess,baseCurrentByteAudit:plan.selectedCurrentByteAudit};
  validatePlanReportBindings(plan,actualPlanFields);
  const wrongParent=clone(actualPlanFields);wrongParent.baseNativeReport=plan.repairEvidence.failedNativeReport;
  assert.throws(()=>validatePlanReportBindings(plan,wrongParent));
});

test('content delta compares inventory structure independent of JSON key order and protects every old package',()=>{
  const before={'Brezi/Maps/Brezi.umap':{sha256:'a'.repeat(64),bytes:9}};
  for(let i=0;i<4102;i++)before[`old/${i}.uasset`]={sha256:'b'.repeat(64),bytes:11};
  const assets=plan.expectedNewPackageAssets;
  const added=assets.map(a=>a.slice(6).split('.')[0]+'.uasset').sort();
  const after=Object.fromEntries(Object.entries(before).map(([key,v])=>[key,{bytes:v.bytes,sha256:v.sha256}]));
  after['Brezi/Maps/Brezi.umap']={bytes:12,sha256:'c'.repeat(64)};
  for(const key of added)after[key]={sha256:'d'.repeat(64),bytes:21};
  const delta={newPackages:assets,newRelativeContentFiles:added,onlyOriginalMapChanged:true};
  validatePropsContent(before,after,assets,delta);
  const bad=clone(after);bad['old/0.uasset'].sha256='e'.repeat(64);assert.throws(()=>validatePropsContent(before,bad,assets,delta));
  assert.throws(()=>validatePropsContent(before,after,[...assets.slice(0,20),assets[0]],delta));
});

test('all old actor fields and signed-zero spellings survive four new groups',()=>{
  const before={};
  for(let i=0;i<5364;i++)before[`old_${i}`]={origin:[0.,-0.],components:i<2325?[{class:'/Script/Engine.HierarchicalInstancedStaticMeshComponent',instanceCount:i===0?675873:1}]:[]};
  const saved=clone(before),groups={};
  for(let i=0;i<4;i++){groups[`part_${i}`]={actor:`new_${i}`};saved[`new_${i}`]={components:[{class:'/Script/Engine.HierarchicalInstancedStaticMeshComponent',instanceCount:2}]};}
  validateOriginalActorPreservation(before,saved,groups);
  const changed=clone(saved);changed.old_0.origin[1]=0.;assert.throws(()=>validateOriginalActorPreservation(before,changed,groups));
});

test('exact actual eight-part constructor and native serialization arrays reject changes without canonicalizing zero',()=>{
  const calibration=plan.constructorCalibration;
  const measured=Object.fromEntries(Object.entries(calibration.compositions).map(([key,row])=>[key,clone(row)]));
  validateConstructorMeasurements(measured,calibration);
  const first=Object.keys(measured)[0];
  for(const field of ['assemblyInputValues','originalImportedNodeValues','composedInputValues','recoveredValues','storedMatrices']){
    const bad=clone(measured);bad[first][field][0][0][0]+=1e-9;assert.throws(()=>validateConstructorMeasurements(bad,calibration));
  }
  const roots=clone(calibration);Object.values(roots.sixRootConstructors)[0].actualValues[1][1]=-0.;
  assert.throws(()=>validateConstructorMeasurements(measured,roots));
});
