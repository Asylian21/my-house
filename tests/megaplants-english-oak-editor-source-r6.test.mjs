import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateOakHeader,validateProjectClosure,OAK_MAP} from '../scripts/unreal/megaplants-english-oak-editor-source-r6.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const source=path.join(root,'output/unreal/megaplants-english-oak-native-20261002-r3');
const report=JSON.parse(await fs.readFile(path.join(source,'oak-usd-scene-native-report-r6.json'),'utf8'));
const context={root,source,names:['oak-usd-scene-native-report-r4.json','oak-usd-scene-native-report-r5.json','oak-usd-scene-native-report-r6.json']};

test('actual saved R6 header keeps the two pinned failed attempts as history',()=>{
  validateOakHeader(report,context);assert.equal(report.map,OAK_MAP);
});
test('failed report, copied legacy exterior report and unknown Oak report reject',()=>{
  assert.throws(()=>validateOakHeader({...report,status:'failed-scene-only-attempt-preserved'},context));
  for(const name of ['exterior-import-report.json','oak-usd-scene-native-report.json','oak-usd-scene-native-report-r7.json','oak-usd-native-pilot-report-r3.json'])
    assert.throws(()=>validateOakHeader(report,{...context,names:[...context.names,name]}));
});
test('different source/map/PID and general numerical acceptance reject',()=>{
  for(const delta of [{map:'/Game/Brezi/Maps/Brezi'},{nativeProcessId:29290},{numericalToleranceApplied:true}])
    assert.throws(()=>validateOakHeader({...report,...delta},context));
  assert.throws(()=>validateOakHeader(report,{...context,source:path.join(root,'output/unreal/exterior-20261002-r32a')}));
});
test('walking, wind, full geometry, lighting clone and GPU claims reject',()=>{
  for(const key of ['walkingCollisionAccepted','windSidecarImported','nativeFullGeometryCornerReadbackAvailable','importedNormalsTangentsPreserved',
    'fullLightingPropertyCloneClaimed','matchedExteriorLightingPairClaimed','actualNaniteGpuPassAttributedToTree','performanceAccepted','shippingVerified'])
    assert.throws(()=>validateOakHeader({...report,[key]:true},context),key);
});
test('protected Content and Binaries additions, removals or bytes reject',()=>{
  const project='/cpu-fixture/Project';
  const contentInventory={'Brezi/Test.umap':{sha256:'map',bytes:1}};
  const projectProof={'BreziTwin.uproject':{sha256:'descriptor',bytes:1},'Binaries/lib.dylib':{sha256:'module',bytes:1}};
  const closure=Object.fromEntries([...Object.entries(contentInventory).map(([p,v])=>[path.join(project,'Content',p),v]),
    ...Object.entries(projectProof).map(([p,v])=>[path.join(project,p),v])]);
  const args={project,contentInventory,projectProof,closure};validateProjectClosure(args);
  assert.throws(()=>validateProjectClosure({...args,closure:{...closure,[project+'/Binaries/unapproved.dylib']:{}}}));
  assert.throws(()=>validateProjectClosure({...args,closure:{...closure,[project+'/Content/extra.uasset']:{}}}));
  const missing={...closure};delete missing[project+'/Binaries/lib.dylib'];assert.throws(()=>validateProjectClosure({...args,closure:missing}));
  assert.throws(()=>validateProjectClosure({...args,closure:{...closure,[project+'/Content/Brezi/Test.umap']:{sha256:'changed',bytes:1}}}));
});
test('isolated runtime uses own map and keeps original camera/render flags without walk audit',async()=>{
  const code=await fs.readFile(path.join(root,'scripts/unreal/megaplants-english-oak-editor-qa-r6.mjs'),'utf8');
  assert(code.includes("[descriptor, sourceEvidence.map, '-game'"));
  for(const flag of ['-BreziWarmupFrames=2400','-BreziBenchmarkFrames=300','-BreziRenderProfile=cinematic','-BreziOutput=retina'])assert(code.includes(flag));
  assert(!code.includes('-BreziWalkAudit'));assert(code.includes('sourceEvidence.originalSourceProject'));
});
