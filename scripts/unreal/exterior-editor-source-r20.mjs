// A real rebuilt quality module on an unchanged, saved R29 scene.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR19,validateProjectClosure} from './exterior-editor-source-r19.mjs';
export {validateProjectClosure};
const BUILD_SHA='570dd1143c5511e3edcb07014c938baf588ff91c80df38c3b10a2f6091e21bfa';
const STAGE_SHA='d78411ffb5ef4df9caf0f97ac790412950e6117551e0367994d4d7dbf738fcb5';
const PROPOSAL_SHA='74889d9e28ef4fe28a6cacd1a30ae7c0eb745c0960fcc93769661a43490bb3da';
const MODULE_SHA='504b1cad9c268543b843e86177deca2e72a7fb6b721812a1a0178d39ce68d678';
const HEADER_SHA='cc0e1d6b80a43c6fb1f3d4d9fd3209012d9c58bfe58e376e22284689dff2b6f8';
const R19_SOURCE_SHA='6ceda937eb4b9d2ebd2a5de17bcbbd58d692cf0bf142d55cc8c2db747810ade1';
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const sha=async p=>{const h=createHash('sha256');for await(const b of createReadStream(p))h.update(b);return h.digest('hex');};
const metadata=async p=>({sha256:await sha(p),bytes:(await fs.stat(p)).size});
const digest=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
export function validateQualityBuildHeader(b,{project}){
  assert.equal(b.schema,'brezi-refined-cinematic-r31-actual-editor-build');
  assert.equal(b.status,'verified-rebuilt-editor-module-with-exact-authored-header-delta');
  assert.equal(b.project,project);assert.equal(b.actualNativeBuildPid,78064);assert.equal(b.actualNativeBuildExitCode,0);
  for(const k of ['allAuthoredBytesUnchangedAfterHeaderStage','allContentBytesUnchanged','originalSavedR29BytesUnchanged','nativeBuildExecuted','newDefaultXmlConfigHasNoOptions'])assert.equal(b[k],true);
  for(const k of ['nativeBuildReexecutedForProof','nativeRuntimeVerified','appearanceAccepted','performanceAccepted','shippingVerified','fullPhotorealismAccepted'])assert.equal(b[k],false);
  assert.equal(b.headerStage.sha256,STAGE_SHA);assert.equal(b.sourceProposal.sha256,PROPOSAL_SHA);
  assert.equal(b.newModule.sha256,MODULE_SHA);assert.equal(b.newModule.bytes,2818240);
  assert.equal(b.newModule.path,path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));
}
export async function loadEditorSourceEvidence(source,{root}={}){
  root=path.resolve(root);source=path.resolve(source);
  const delegated=fileURLToPath(new URL('./exterior-editor-source-r19.mjs',import.meta.url));
  assert(digest(R19_SOURCE_SHA),'Final R19 delegated reader pin required');assert.equal(await sha(delegated),R19_SOURCE_SHA);
  const expected=path.join(root,'output/unreal/exterior-20261002-r31a-quality');
  if(source!==expected){
    assert(!/^exterior-20261002-r31/.test(path.basename(source)),'Unknown quality candidate cannot inherit legacy evidence');
    return loadR19(source,{root});
  }
  const project=path.join(source,'Project/BreziTwin');
  const file=path.join(source,'quality-editor-build-proof-r3.json');
  const closure=new Set([file,fileURLToPath(new URL('./exterior-editor-source-r19.mjs',import.meta.url))]);
  async function pinned(row){
    assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&digest(row.sha256)&&Number.isInteger(row.bytes));
    const s=await fs.lstat(row.path);assert(s.isFile()&&!s.isSymbolicLink());assert.deepEqual(await metadata(row.path),{sha256:row.sha256,bytes:row.bytes});
    closure.add(row.path);return row.path;
  }
  const pj=async row=>read(await pinned(row));
  assert.equal(await sha(file),BUILD_SHA);
  const b=await read(file);validateQualityBuildHeader(b,{project});
  assert.equal(b.baseNative.path,path.join(root,'output/unreal/exterior-20261002-r29a/original-tree-group-native-report.json'));
  const base=await loadR19(path.dirname(b.baseNative.path),{root});
  await pinned(b.baseNative);for(const p of base.additionalClosureFiles)closure.add(p);
  const stage=await pj(b.headerStage),proposal=await pj(b.sourceProposal),initial=await pj(stage.cloneReceipt);
  assert.equal(stage.schema,'brezi-refined-cinematic-r31-header-stage');
  assert.equal(stage.status,'verified-exact-single-authored-header-delta-before-editor-build');
  assert.equal(stage.project,project);assert.deepEqual(stage.nativeBase,b.baseNative);assert.deepEqual(stage.qualitySourceProposal,b.sourceProposal);
  assert.deepEqual(stage.contentInventory,base.contentInventory);assert.deepEqual(stage.protectedBefore,base.projectProof);
  assert.deepEqual(stage.intentionalAuthoredDelta,['Source/BreziTwin/BreziRenderQualityPolicy.h']);
  assert.equal(stage.newHeader.sha256,HEADER_SHA);assert.equal(proposal.proposedHeader.sha256,HEADER_SHA);await pinned(stage.newHeader);await pinned(proposal.proposedHeader);
  assert.equal(proposal.proposedRecipeRevision,5);assert.equal(proposal.selectedActualNativeBase,null);
  assert.equal(initial.fileCount,4192);assert.equal(initial.project,project);assert.equal(initial.nativeBuildExecuted,false);
  assert.equal(initial.status,'verified-current-saved-r29-byte-identical-independent-clone-before-header-stage');
  const original={...Object.fromEntries(Object.entries(base.contentInventory).map(([k,v])=>['Content/'+k,v])),...base.projectProof};
  assert.equal(initial.files.length,Object.keys(original).length);const seen=new Set();
  for(const r of initial.files){
    assert(Object.hasOwn(original,r.relativePath)&&!seen.has(r.relativePath));seen.add(r.relativePath);
    assert.deepEqual({sha256:r.sha256,bytes:r.bytes},original[r.relativePath]);
    assert.equal(r.source,path.join(base.project,r.relativePath));assert.equal(r.destination,path.join(project,r.relativePath));assert.equal(r.independentInodes,true);
    const[a,z]=await Promise.all([fs.stat(r.source),fs.lstat(r.destination)]);assert(z.isFile()&&!z.isSymbolicLink());assert(a.dev!==z.dev||a.ino!==z.ino);
  }
  assert.deepEqual(b.protectedBeforeBuild,stage.protectedAfterHeaderStage);
  const header='Source/BreziTwin/BreziRenderQualityPolicy.h';
  assert.deepEqual(Object.keys(stage.protectedBefore).filter(k=>JSON.stringify(stage.protectedBefore[k])!==JSON.stringify(stage.protectedAfterHeaderStage[k])),[header]);
  assert.deepEqual(stage.protectedAfterHeaderStage[header],{sha256:HEADER_SHA,bytes:5335});
  const built=b.currentNonContentFiles,delta=b.exactBuildOutputDelta;
  const runtime=['Binaries/Mac/libUnrealEditor-BreziTwin.dylib','Binaries/Mac/UnrealEditor.modules','Binaries/Mac/BreziTwinEditor.target'];
  assert.equal(Object.keys(delta).length,185);assert.equal(Object.keys(built).length,316);
  const computed=Object.keys(built).filter(k=>JSON.stringify(built[k])!==JSON.stringify(b.protectedBeforeBuild[k])).sort();
  assert.deepEqual(computed,Object.keys(delta).sort());
  for(const[k,row]of Object.entries(delta)){
    assert.deepEqual(row.before,b.protectedBeforeBuild[k]??null);assert.deepEqual(row.after,built[k]);
    assert(runtime.includes(k)||k==='Saved/UnrealBuildTool/BuildConfiguration.xml'||k.startsWith('Intermediate/'));
    assert.equal(row.kind,runtime.includes(k)?'editor-runtime-product':k==='Saved/UnrealBuildTool/BuildConfiguration.xml'?'empty-generated-project-ubt-config':'generated-native-build-file');
  }
  for(const[k,row]of Object.entries(built))await pinned({path:path.join(project,k),...row});
  for(const k of Object.keys(b.protectedBeforeBuild))assert(Object.hasOwn(built,k));
  assert.deepEqual(Object.keys(b.protectedBeforeBuild).filter(k=>JSON.stringify(b.protectedBeforeBuild[k])!==JSON.stringify(built[k])),['Binaries/Mac/libUnrealEditor-BreziTwin.dylib']);
  const process=await pj(b.actualBuildProcess);assert.equal(process.exitCode,0);assert.equal(process.pid,78064);assert.equal(process.sourcePinsUnchanged,true);
  assert.deepEqual(process.command,['/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh','BreziTwinEditor','Mac','Development',path.join(project,'BreziTwin.uproject'),'-WaitMutex','-NoUBA']);
  await pinned(process.log);for(const[p,h]of Object.entries(process.sourcePinsBefore))await pinned({path:p,sha256:h,bytes:(await fs.stat(p)).size});
  for(const k of ['postbuildCpuProofProducer','originalPostcheckNoGo','editorTargetReceipt','editorModuleRegistry','newModule','explicitNewDefaultXmlConfig'])await pinned(b[k]);
  const module=b.newModule;const parent=path.join(base.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');
  const[a,z]=await Promise.all([fs.stat(parent),fs.stat(module.path)]);assert(a.dev!==z.dev||a.ino!==z.ino);
  const witness={source:parent,destination:module.path,sha256:module.sha256,bytes:module.bytes,independentInodes:true,
    origin:'actual-rebuilt-header-only-quality-module',actualBuildProcess:b.actualBuildProcess};
  const summary={mode:'actual-rebuilt-quality-module-on-unchanged-r29-scene',savedActors:5351,
    contentFiles:4060,recipeRevisionExpected:5,cinematicGroupsExpected:4,actualNativeBuildPid:78064,
    appearanceAccepted:false,performanceAccepted:false,shippingVerified:false,fullPhotorealismAccepted:false};
  return {mode:summary.mode,project,nativeReceiptPath:file,base:base.base,summary,
    contentInventory:base.contentInventory,
    projectProof:Object.fromEntries(Object.entries(built).filter(([k])=>k==='BreziTwin.uproject'||/^(Config|Source|Binaries)\//.test(k))),
    additionalClosureFiles:[...closure],
    nativeModuleWitness:witness,moduleWitnessSource:b.actualBuildProcess,
    receiptSummary:{baseNativeReport:b.baseNative,qualitySourceProposal:b.sourceProposal,actualBuildProcess:b.actualBuildProcess,
      newModule:b.newModule,sceneMapUnchangedAfterQualityBuild:true,summary}};
}
