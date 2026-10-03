// CPU receipt fixtures only. No Unreal/GPU launch, saved native proof, visual
// acceptance, performance acceptance or Shipping proof is produced by tests.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateCurvedGrassHeader,retainedSwapIndices,validateCurvedGrassAssetDelta,validateGrassDiagnosticViews,validateStagedGrassContent,validateGrassStageHeader} from '../scripts/unreal/exterior-editor-source-r7.mjs';
const source='/fixture/output/unreal/exterior-20261002-r20d',project=source+'/Project/BreziTwin';
const header={schema:'brezi-original-curved-grass-root-replacement-r1',owner:'scripts/unreal/exterior-curved-grass-native-r4.py',
  repairSchema:'brezi-original-curved-grass-exact-native-transform-repair-r4',repairSupplement:{sha256:'0a29b1f8ea02626da5893e837ac643007c809df604b374de15cb571182735c89'},
  status:'verified-saved-original-curved-grass-root-replacement',output:source,project,
  savedMapUnloadedReloaded:true,originalR16Unchanged:true,originalContentExceptMapByteIdentical:true,all64StoredMatrixAndRecoveredTransformExactMeasuredBeforeSaveAndAfterReload:true,
  nearSourceEmptyForegroundFixed:false,nativeMaterialPackagesIndependentlyReloaded:false,nativeMeshPackagesIndependentlyReloaded:false,
  nativeAppearanceAccepted:false,fullPhotorealismAccepted:false,performanceAccepted:false,shippingPackageProduced:false,
  selectedPlan:{sha256:'f43f3d224c9d43d70091a910e5618052fa942bb593ac55d3cc900eace8a8aa68'},
  baseNativeReport:{sha256:'1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122'}};
test('CPU typed receipt fixture rejects failed native, old-owner mixing and fabricated acceptance',()=>{
  validateCurvedGrassHeader(header,{source,project});
  for(const change of [{status:'failed'},{owner:'scripts/unreal/exterior-meadow-visibility-native.py'},
    {nativeAppearanceAccepted:true},{all64StoredMatrixAndRecoveredTransformExactMeasuredBeforeSaveAndAfterReload:false},{owner:'scripts/unreal/exterior-curved-grass-native-r2.py'},
    {repairSchema:'brezi-original-curved-grass-measured-runtime-repair-r2'},{repairSupplement:{sha256:'0'.repeat(64)}},{nativeMaterialPackagesIndependentlyReloaded:true},{selectedPlan:{sha256:'0'.repeat(64)}}])
    assert.throws(()=>validateCurvedGrassHeader({...structuredClone(header),...change},{source,project}));
});
test('CPU descending RemoveAtSwap fixture preserves every unselected identity in actual permutation',()=>{
  assert.deepEqual(retainedSwapIndices(10,[1,5,8]),[0,7,2,3,4,9,6]);
  assert.notDeepEqual(retainedSwapIndices(10,[1,5,8]),[0,9,2,3,4,8,6]);
  for(const removed of [[1,1],[10],[-1],[1.5]])assert.throws(()=>retainedSwapIndices(10,removed));
});
test('CPU exact11package fixture rejects extra import assets and changed original texture',()=>{
  const before=Object.fromEntries(Array.from({length:3974},(_,i)=>[`Original/Asset${i}.uasset`,{sha256:'a'.repeat(64),bytes:1}]));
  before['Brezi/Maps/Brezi.umap']={sha256:'b'.repeat(64),bytes:1};
  const packages=Array.from({length:11},(_,i)=>`/Game/Brezi/CurvedGrass20261001R20/Pilot/Asset${i}`),after=structuredClone(before);
  after['Brezi/Maps/Brezi.umap']={sha256:'c'.repeat(64),bytes:2};
  for(const p of packages)after[p.slice('/Game/'.length)+'.uasset']={sha256:'d'.repeat(64),bytes:1};
  const delta={changedFiles:['Brezi/Maps/Brezi.umap'],newFiles:packages.map(p=>p.slice('/Game/'.length)+'.uasset').sort(),removedFiles:[],newUassetPackages:11,protectedOriginalFilesByteIdentical:3974};
  validateCurvedGrassAssetDelta(before,after,packages,delta);
  const extra=structuredClone(after);extra['Brezi/CurvedGrass20261001R20/Pilot/UnexpectedMaterial.uasset']={sha256:'d'.repeat(64),bytes:1};
  assert.throws(()=>validateCurvedGrassAssetDelta(before,extra,packages,delta));
  const changed=structuredClone(after);changed['Original/Asset0.uasset'].sha256='e'.repeat(64);
  assert.throws(()=>validateCurvedGrassAssetDelta(before,changed,packages,delta));
});

test('CPU pinned-camera fixtures reject changed old views, invented native visibility and changed map in data-only clone',()=>{
  const base=new URL('../output/unreal/exterior-curved-grass-20261002-camera-r1-supplement/',import.meta.url);
  const supplement=JSON.parse(fs.readFileSync(new URL('curved-grass-camera-supplement.json',base),'utf8'));
  const original=JSON.parse(fs.readFileSync(supplement.originalViewpoints.path,'utf8')),appended=JSON.parse(fs.readFileSync(supplement.appendedViewpoints.path,'utf8'));
  validateGrassDiagnosticViews(original,supplement,appended);
  const changed=structuredClone(appended);changed.views[0].eyeCm[0]+=1;assert.throws(()=>validateGrassDiagnosticViews(original,supplement,changed));
  const invented=structuredClone(supplement);invented.sourceCameraAudit.nativeCameraVerified=true;assert.throws(()=>validateGrassDiagnosticViews(original,invented,appended));
  const before={'Data/viewpoints.json':{sha256:supplement.originalViewpoints.sha256,bytes:supplement.originalViewpoints.bytes},'Brezi/Maps/Brezi.umap':{sha256:'a'.repeat(64),bytes:2}};
  const after=structuredClone(before);after['Data/viewpoints.json']={sha256:supplement.appendedViewpoints.sha256,bytes:supplement.appendedViewpoints.bytes};validateStagedGrassContent(before,after,supplement);
  after['Brezi/Maps/Brezi.umap'].sha256='b'.repeat(64);assert.throws(()=>validateStagedGrassContent(before,after,supplement));
});

test('CPU staged-camera owner dispatch admits exact historical R16 baseline and only R4 candidate',()=>{
  const root='/fixture',source=root+'/output/unreal/exterior-20261002-r20-close-baseline',receiptSha256='0ea7f3ed1b34642e1b9a9a751d33a8151d7c6c405f25f50d85916c0805d692cb';
  const baseline={schema:'brezi-curved-grass-close-camera-diagnostic-clone-r1',owner:'scripts/unreal/exterior-curved-grass-camera-stage-r1.py',sourceKind:'original-r16',stagingHelper:{path:root+'/scripts/unreal/exterior-curved-grass-camera-stage-r1.py',sha256:'e8028d31e82c9a8e7bfce324b2ea4e9fd8910703db90ca5cfe76880ad8e01015'}};
  assert.equal(validateGrassStageHeader(baseline,{source,root,receiptSha256}),true);
  for(const change of [{sourceKind:'saved-curved-grass-r20-r4'},{sourceKind:'saved-curved-grass-r20-r3'}])assert.throws(()=>validateGrassStageHeader({...baseline,...change},{source,root,receiptSha256}));
  assert.throws(()=>validateGrassStageHeader(baseline,{source:source+'-copied',root,receiptSha256}));
  assert.throws(()=>validateGrassStageHeader(baseline,{source,root,receiptSha256:'0'.repeat(64)}));
  const candidate={schema:'brezi-curved-grass-close-camera-diagnostic-clone-r2',owner:'scripts/unreal/exterior-curved-grass-camera-stage-r2.py',sourceKind:'saved-curved-grass-r20-r4',stagingHelper:{path:root+'/scripts/unreal/exterior-curved-grass-camera-stage-r2.py',sha256:'64d492b16e6b6966a481d997ca0d6f2b79a8044ca166a9ad619ed1acbfeb8238'}};
  assert.equal(validateGrassStageHeader(candidate,{source:source+'-candidate',root}),false);
  for(const sourceKind of ['original-r16','saved-curved-grass-r20-r3'])assert.throws(()=>validateGrassStageHeader({...candidate,sourceKind},{source:source+'-candidate',root}));
});
