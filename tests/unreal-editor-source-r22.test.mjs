// Stored native receipts used as CPU fixtures; these tests are not new native evidence.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {validateYardGroundHeader,validateYardGroundContent,validateYardGroundReportNames} from '../scripts/unreal/exterior-editor-source-r22.mjs';
const source='/Users/davidzita/www/dom/output/unreal/exterior-20261002-r32a',project=source+'/Project/BreziTwin';
const r=JSON.parse(await fs.readFile(source+'/context-yard-ground-native-report.json'));
const before=JSON.parse(await fs.readFile(r.baseContentInventory.path)),after=JSON.parse(await fs.readFile(r.afterContentInventory.path));
const packages=r.newPackages.map(p=>p.split('.')[0].replace('/Game/','')+'.uasset');
test('actual typed saved R32 header and exact8 package map-only source fixture',()=>{
 validateYardGroundHeader(r,{source,project});validateYardGroundContent(before,after,packages,r.assetDelta);
});
test('failed owner/process/acceptance cannot inherit saved R32 identity',()=>{
 for(const edit of [{owner:'scripts/unreal/exterior-context-yard-native-r28-r2.py'},{status:'failed'},
  {nativeProcessId:69104},{performanceAccepted:true},{materialPackagesIndependentlyUnloaded:true},{existingMemberTransformOrSeedSetterUsed:true}])
  assert.throws(()=>validateYardGroundHeader({...r,...edit},{source,project}));
});
test('full native ground census and1274 unique mask-bound roots are enforced',()=>{
 for(const change of [x=>x.savedReadback.meshProofs[2].triangles--,
  x=>x.savedReadback.footprints[1].rootId=x.savedReadback.footprints[0].rootId,
  x=>x.savedReadback.footprints[0].originalShrubClearancePreserved=false,
  x=>x.actualCounts.newRoots=1273,x=>x.savedReadback.meshProofs[0].nativeNormalTangentReadbackAvailable=true]){
   const v=structuredClone(r);change(v);assert.throws(()=>validateYardGroundHeader(v,{source,project}));
 }
});
test('viewpoint mutation, foreign packages and missing original content reject',()=>{
 const views=structuredClone(after);views['Data/viewpoints.json'].sha256='0'.repeat(64);
 assert.throws(()=>validateYardGroundContent(before,views,packages,r.assetDelta));
 const foreign=[...packages];foreign[0]='Brezi/Other/foreign.uasset';assert.throws(()=>validateYardGroundContent(before,after,foreign,r.assetDelta));
 const missing=structuredClone(after);delete missing[Object.keys(before)[0]];assert.throws(()=>validateYardGroundContent(before,missing,packages,r.assetDelta));
});
test('unknown or copied native reports reject beside the selected R32 receipt',()=>{
 const selected='context-yard-ground-native-report.json';validateYardGroundReportNames([selected,'root-native-byte-audit-r32a.json']);
 for(const other of ['context-yard-ground-native-report-r2.json','garden-composition-native-report-r3.json','exterior-import-report.json','foreign-overlay-report.json'])
  assert.throws(()=>validateYardGroundReportNames([selected,other]));
});
