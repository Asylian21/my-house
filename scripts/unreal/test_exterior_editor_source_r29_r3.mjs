import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateSoftGroundHeader,validateSoftGroundReportNames,validateSoftGroundContent,
  validateSoftGroundRootAudit,counterfactualTwoSlots,actor197,donor668,materialAssets,newAssets} from './exterior-editor-source-r29-r3.mjs';
const root=path.resolve(fileURLToPath(new URL('../../',import.meta.url))),source=path.join(root,'output/unreal/exterior-20261002-r38b');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),r=read(path.join(source,'soft-ground-native-report-r2.json'));
const plan=read(r.selectedPlan.path),audit=read(path.join(source,'root-native-success-byte-audit-r38b-r2.json'));
const clone=structuredClone;

test('only actual saved R38r2 header accepted; failed/foreign/PID/evidence changes rejected',()=>{
  validateSoftGroundHeader(r,{source,root});
  for(const [k,v]of [['status','failed'],['schemaVersion',1],['owner','scripts/unreal/exterior-context-yard-soft-coherence-native-r38.py'],
    ['nativeProcessId',66232],['nativeGpuPixelFormatVerified',true],['additionalSeedRangesPreservationClaimed',true]]){
    const x=clone(r);x[k]=v;assert.throws(()=>validateSoftGroundHeader(x,{source,root}));}
  assert.throws(()=>validateSoftGroundHeader(r,{source:path.join(root,'output/unreal/exterior-20261002-r38a'),root}));
});
test('plain R1, alternate family revisions and copied parent reports reject',()=>{
  const name='soft-ground-native-report-r2.json';validateSoftGroundReportNames([name,'root-native-success-byte-audit-r38b-r2.json']);
  for(const n of ['soft-ground-native-report.json','soft-ground-native-report-r1.json','soft-ground-native-report-r3.json',
    'garden-yard-integration-native-report-r2.json','exterior-import-report.json'])assert.throws(()=>validateSoftGroundReportNames([name,n]));
  assert.throws(()=>validateSoftGroundReportNames(['soft-ground-native-report.json']));
});
test('same mapped668 path is valid; only two slot0/override arrays change',()=>{
  const component=(mesh,mat)=>({class:'/Script/Engine.StaticMeshComponent',name:'StaticMeshComponent0',mesh,materials:[mat,'retained'],overrideMaterials:[],transform:[0,0,0],visible:true});
  const before={[actor197]:{tags:['old'],components:[component('m0','a0')]},[donor668]:{tags:['yard'],components:[component('m1','a1')]},unrelated:{components:[{matrix:[-0,1]}]}};
  const targets={backdrop:{actor:actor197,component:'StaticMeshComponent0',originalMesh:'m0',originalMaterial:'a0'},
    substrate:{actor:donor668,component:'StaticMeshComponent0',originalMesh:'m1',originalMaterial:'a1'}};
  const expected=counterfactualTwoSlots(before,targets,{newActorMapping:{[donor668]:donor668}});
  assert.equal(expected[donor668].components[0].materials[0],materialAssets.substrate);
  assert.deepEqual(expected[actor197].components[0].overrideMaterials,[materialAssets.backdrop]);
  assert.deepEqual(expected.unrelated,before.unrelated);assert.deepEqual(expected[donor668].components[0].materials.slice(1),['retained']);
  assert.equal(before[donor668].components[0].materials[0],'a1');
  const bad=clone(targets);bad.substrate.originalMesh='foreign';assert.throws(()=>counterfactualTwoSlots(before,bad,{newActorMapping:{[donor668]:donor668}}));
  assert.throws(()=>counterfactualTwoSlots(before,targets,{newActorMapping:{[donor668]:'foreign'}}));
});
test('4100→4103 permits only map and exact three owned package paths',()=>{
  const before={'Brezi/Maps/Brezi.umap':{sha256:'old',bytes:1}};
  for(let i=0;i<4099;i++)before['old/'+i+'.uasset']={sha256:'h',bytes:1};
  const after=clone(before);after['Brezi/Maps/Brezi.umap']={sha256:'new',bytes:2};const added=newAssets.map(a=>a.slice(6).split('.')[0]+'.uasset').sort();
  for(const k of added)after[k]={sha256:'new',bytes:3};const delta={newPackages:3,newRelativeContentFiles:added,onlyOriginalMapChanged:true};
  validateSoftGroundContent(before,after,delta);
  // Actual native inventory serializes {bytes,sha256}, while its parent uses {sha256,bytes}.
  const reordered=Object.fromEntries(Object.entries(after).map(([k,v])=>[k,{bytes:v.bytes,sha256:v.sha256}]));
  validateSoftGroundContent(before,reordered,delta);
  const bad=clone(after);bad['old/0.uasset'].bytes=2;assert.throws(()=>validateSoftGroundContent(before,bad,delta));
  const foreign=clone(after);delete foreign[added[0]];foreign['foreign.uasset']={sha256:'new',bytes:3};assert.throws(()=>validateSoftGroundContent(before,foreign,delta));
});
test('actual current audit uses nativeReport/protectedFiles and separate1039/1048',()=>{
  const pins={reportPin:audit.nativeReport,processPin:audit.nativeProcess,rawPin:audit.rawNativeProcess};validateSoftGroundRootAudit(audit,r,pins);
  for(const[k,v]of [['sourceReceiptPins',1048],['terminalRootSourcePins',1039],['currentProjectFiles',4232],['freshNativeActorOrAttributeDecodeExecuted',true],['nativeGpuPixelFormatVerified',true]]){
    const a=clone(audit);a[k]=v;assert.throws(()=>validateSoftGroundRootAudit(a,r,pins));}
  const a=clone(audit);a.nativeReport=clone(a.nativeReport);a.nativeReport.sha256='0'.repeat(64);assert.throws(()=>validateSoftGroundRootAudit(a,r,pins));
});
test('actual target schema and native grayscale adaptation preserve historical source graph',()=>{
  assert.deepEqual(Object.keys(plan.targets).sort(),['backdrop','substrate']);assert.equal(plan.targets.substrate.actor,donor668);
  assert.equal(plan.nativeGraphAdaptation.sourceMaskSamplerType,'SAMPLERTYPE_MASKS');
  assert.equal(plan.nativeGraphAdaptation.newOwnedMaskSamplerType,'SAMPLERTYPE_LINEAR_GRAYSCALE');
  assert.equal(plan.samplingPolicy.maskMipValueMode,'TMVM_NONE');assert.equal(plan.samplingPolicy.compressionSettings,'TC_GRAYSCALE');
  assert(!Object.hasOwn(plan.samplingPolicy,'compressionNone'));assert.equal(r.newMaterials.reflectionPreflight.textureFieldCount,24);
  assert.equal(r.newMaterials.reflectionPreflight.hiddenCompressionNonePropertyAccessed,false);
});
