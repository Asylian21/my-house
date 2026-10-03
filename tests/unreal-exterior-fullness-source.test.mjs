import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,rm,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import test from 'node:test';
import {validateGrovePlanOwner,validateGrovePlanReceipt} from '../scripts/unreal/exterior-source.mjs';
import {validateMeadowInfillPlan} from '../scripts/unreal/exterior-meadow-infill-source.mjs';

const root=resolve(import.meta.dirname,'..');
const directory=resolve(root,'output/unreal/exterior-canopy-fullness-integration-20261001-r2');
const read=async path=>JSON.parse(await readFile(path));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const sha=async path=>hash(await readFile(path));
const fullPath=resolve(directory,'geometry-manifest.json');
const full=await read(fullPath);
const preservedLibraryPin=full.validatedOriginal126Subset;
const plants=await read(preservedLibraryPin.path);
const oldPlan=await read(resolve(root,'output/unreal/exterior-meadow-infill-integration-20261001-r1/meadow-infill-plan.json'));
const plan=await read(full.sourceFullnessPlan.path);
const validation=await read(resolve(directory,'integration-validation.json'));
const baseline=await read(resolve(root,'output/unreal/exterior-20261001-r14a/exterior-import-report.json'));

// Constructed fixtures use the R14 receipt schema and actual frozen sources.
// They do not prove an R15 native import, saved135 library, rendering or performance.
const report={inputFiles:{...baseline.inputFiles,...full.inputFiles},pipelineFiles:{...baseline.pipelineFiles},
  plantGeometryManifest:fullPath,savedGeometryReadback:structuredClone(baseline.savedGeometryReadback),
  geometry:{groups:structuredClone(baseline.geometry.groups)},savedPlantReadback:structuredClone(baseline.savedPlantReadback),
  materials:structuredClone(baseline.materials),meadowInfill:structuredClone(baseline.meadowInfill),
  canopyReplacement:{...structuredClone(baseline.canopyReplacement),plan:full.sourceFullnessPlan.path,
    planSha256:full.sourceFullnessPlan.sha256,audit:structuredClone(plan.audit),validation:structuredClone(validation.audit)}};
for(const path of [fullPath,preservedLibraryPin.path,full.sourceFullnessPlan.path])report.inputFiles[path]=await sha(path);
for(const relative of ['scripts/unreal/exterior-meadow-infill-native.py','scripts/unreal/exterior-meadow-infill-integration.py']) {
  const path=resolve(root,relative);report.pipelineFiles[path]=await sha(path);
}

// Repin each mutated parent to its real temporary bytes. Negative cases must
// reach the owner/prefix/subset checks rather than fail only on a stale hash.
async function withParent(mutate,verify) {
  const temporary=await mkdtemp(resolve(root,'output/unreal/fullness-node-source-fixture-'));
  try {
    const parent=structuredClone(full);mutate(parent);
    const path=resolve(temporary,'geometry-manifest.json'),bytes=Buffer.from(JSON.stringify(parent));
    await writeFile(path,bytes);
    const fixture=structuredClone(report);fixture.plantGeometryManifest=path;fixture.inputFiles[path]=hash(bytes);
    assert.equal(await sha(path),fixture.inputFiles[path]);
    await verify(fixture,parent);
  } finally {await rm(temporary,{recursive:true,force:true});}
}

test('source fixture accepts the typed fullness owner/status and rejects growth or unknown owner substitutions',()=>{
  assert.equal(plan.owner,'scripts/unreal/exterior-canopy-fullness-study.py');
  assert.equal(report.canopyReplacement.validation.status,'verified-source-grove-canopy-fullness');
  validateGrovePlanOwner(plan,'canopyReplacement');validateGrovePlanReceipt(report,plan,'canopyReplacement');
  const wrongStatus=structuredClone(report);wrongStatus.canopyReplacement.validation.status='verified-source-grove-canopy-growth';
  assert.throws(()=>validateGrovePlanReceipt(wrongStatus,plan,'canopyReplacement'),/owner\/native status pair differs/);
  const wrongOwner=structuredClone(plan);wrongOwner.owner='scripts/unreal/exterior-canopy-growth.py';
  assert.throws(()=>validateGrovePlanReceipt(report,wrongOwner,'canopyReplacement'),/owner\/native status pair differs/);
  wrongOwner.owner='scripts/unreal/unreviewed-fullness.py';
  assert.throws(()=>validateGrovePlanOwner(wrongOwner,'canopyReplacement'),/Grove plan owner differs/);
});

test('source fixture validates genuine126 meadow against the actual pinned full135 parent',async()=>{
  assert.equal(full.meshes.length,135);assert.equal(full.meshes.reduce((n,m)=>n+m.lods.length,0),405);
  assert.equal(plants.owner,'scripts/unreal/exterior-meadow-infill-integration.py');
  assert.equal(preservedLibraryPin.sha256,'a39e13e9b58821815fd783857e09e58d1023e4a64ab10e45a2a4da608954ceb9');
  assert.deepEqual(full.meshes.slice(0,126),plants.meshes);
  assert.deepEqual(await validateMeadowInfillPlan(report,oldPlan,plants,{preservedLibraryPin}),
    {groups:101,instances:33483,partialGroundCover:true,nativeAppearanceAccepted:false});
});

test('self-consistently repinned full135 parent cannot borrow the original growth owner',async()=>{
  await withParent(parent=>{parent.owner='scripts/unreal/exterior-canopy-growth.py';},async fixture=>{
    await assert.rejects(validateMeadowInfillPlan(fixture,oldPlan,plants,{preservedLibraryPin}),
      /exterior-canopy-fullness-integration\.py/);
  });
});

test('self-consistently repinned full135 parent cannot change its original126 prefix',async()=>{
  await withParent(parent=>{parent.meshes[0].heightCm+=1;},async fixture=>{
    await assert.rejects(validateMeadowInfillPlan(fixture,oldPlan,plants,{preservedLibraryPin}),
      /Fuller canopy changed the imported meadow126 prefix/);
  });
});

test('a swapped genuine120 subset cannot stand in for the preserved126 pin',async()=>{
  await assert.rejects(validateMeadowInfillPlan(report,oldPlan,plants,
    {preservedLibraryPin:full.validatedOriginal120Subset}),assert.AssertionError);
  await withParent(parent=>{parent.validatedOriginal126Subset=parent.validatedOriginal120Subset;},async(fixture,parent)=>{
    assert.notEqual(parent.validatedOriginal126Subset.sha256,preservedLibraryPin.sha256);
    await assert.rejects(validateMeadowInfillPlan(fixture,oldPlan,plants,
      {preservedLibraryPin:parent.validatedOriginal126Subset}),assert.AssertionError);
  });
});
