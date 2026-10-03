// Actual receipts used as CPU fixtures; these tests are not new native evidence.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {validateFernOnlyHeader,validateFernOnlyContent,validateFernOnlyReportNames} from '../scripts/unreal/exterior-editor-source-r24.mjs';
const source='/Users/davidzita/www/dom/output/unreal/exterior-20261002-r34a',project=source+'/Project/BreziTwin';
const r=JSON.parse(await fs.readFile(source+'/garden-fern-only-native-report.json'));
const before=JSON.parse(await fs.readFile(r.baseContentInventory.path)),after=JSON.parse(await fs.readFile(r.afterContentInventory.path));
const packages=r.newPackages.map(p=>p.replace('/Game/','')+'.uasset');
test('typed actual saved R34 fern-only receipt and11 package delta satisfy source guards',()=>{
  validateFernOnlyHeader(r,{source,project});validateFernOnlyContent(before,after,packages,r.assetDelta);
});
test('failed/older/differently scoped owners cannot inherit the saved R34 identity',()=>{
  for(const edit of [{schemaVersion:2},{status:'failed'},{owner:'scripts/unreal/exterior-garden-fern-only-study-r34.py'},
    {nativeProcessId:85419},{performanceAccepted:true},{AdditionalRandomSeedsReadbackAvailable:true}])
    assert.throws(()=>validateFernOnlyHeader({...r,...edit},{source,project}));
});
test('unique36 fern roots and full original/native corner census are enforced',()=>{
  for(const change of [x=>x.newOwnedGroups.fern_02_c.rootIds[0]=x.newOwnedGroups.fern_02_a.rootIds[0],
    x=>x.nativeGeometryReadback.fern_02_c.triangles--,x=>x.actualCounts.retainedOriginalGardenRoots=436,
    x=>x.nativeGeometryReadback.fern_02_a.nativeNormalTangentReadbackAvailable=true,
    x=>x.newOwnedGroups.fern_02_a.rootIds[0]='garden_ornamental_6',x=>x.allOriginal12OrnamentalActorsAndMembersUnchanged=false]){
    const fixture=structuredClone(r);change(fixture);assert.throws(()=>validateFernOnlyHeader(fixture,{source,project}));
  }
});
test('foreign packages, original view changes, missing original files and extra actor assets reject',()=>{
  const changedViews=structuredClone(after);changedViews['Data/viewpoints.json'].sha256='0'.repeat(64);
  assert.throws(()=>validateFernOnlyContent(before,changedViews,packages,r.assetDelta));
  const missing=structuredClone(after);delete missing[Object.keys(before).find(k=>k!=='Brezi/Maps/Brezi.umap')];
  assert.throws(()=>validateFernOnlyContent(before,missing,packages,r.assetDelta));
  const foreign=[...packages];foreign[0]='Brezi/Other/foreign.uasset';assert.throws(()=>validateFernOnlyContent(before,after,foreign,r.assetDelta));
  const extra={...after,'Brezi/GardenFernOnly20261002R34/Geometry/extra.uasset':{sha256:'0'.repeat(64),bytes:1}};
  assert.throws(()=>validateFernOnlyContent(before,extra,packages,r.assetDelta));
});
test('copied parent/failed/unknown report names cannot masquerade as a single selected native owner',()=>{
  const selected='garden-fern-only-native-report.json';validateFernOnlyReportNames([selected,'root-native-byte-audit-r34a.json']);
  for(const other of ['garden-composition-native-report-r3.json','garden-fern-only-native-report-r2.json','garden-fern-only-native-report-r9.json',
    'original-tree-group-native-report.json','exterior-import-report.json'])assert.throws(()=>validateFernOnlyReportNames([selected,other]));
});
