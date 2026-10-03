// Read-only CPU repair of one retained original profile; never launches Unreal.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
import {validateGpuProfileArtifact} from './exterior-editor-gpu-profile-r15-r2.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const OWNER='scripts/unreal/exterior-editor-gpu-profile-audit-r15-r2.mjs';
const validation=path.join(root,'output/unreal/exterior-validation-20260930-r1');
const suitePath=path.join(validation,'qa/editor-pilot-r24b-gpu-pass-r15-1790909855407-3vG4Zl/editor-pilot-suite.json');
const output=path.join(validation,'r24b-original-gpu-profile-reparse-r15-r2.json');
const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
async function pin(file){const stat=await fs.lstat(file);assert(stat.isFile()&&!stat.isSymbolicLink());const raw=await fs.readFile(file);return {path:file,sha256:digest(raw),bytes:raw.length};}
async function read(file){return JSON.parse(await fs.readFile(file,'utf8'));}
async function typedPin(row){const actual=await pin(row.path);assert.equal(actual.sha256,row.sha256);assert.equal(actual.bytes,row.bytes);return actual;}

const suitePin=await pin(suitePath),suite=await read(suitePath);
assert.equal(suite.status,'editor-game-pilot-rejected');assert.equal(suite.sourceInputsUnchanged,true);
assert.equal(suite.errors.length,1);assert.match(suite.errors[0],/Timed row has no event name/);
assert.deepEqual(suite.requestedViews,['exterior-canopy-close']);assert.equal(suite.cases.length,1);
const row=suite.cases[0];assert.equal(row.status,'editor-game-pilot-rejected');
assert.deepEqual(row.outcome,{code:0,signal:null,pid:68687});assert.deepEqual(row.shaderAndLoadErrors,[]);
assert.equal(row.sourceFovNativeReadbackAvailable,false);
assert(row.argv.includes('-BreziProfileGPU'));
const processPin=await pin(row.processReceiptPath),process=await read(row.processReceiptPath);
assert.deepEqual(process.outcome,row.outcome);assert.equal(process.status,row.status);
const beforeClosure=await typedPin(suite.inputClosureBefore),afterClosure=await typedPin(suite.inputClosureAfter);
assert.equal(beforeClosure.sha256,afterClosure.sha256);assert.equal(beforeClosure.bytes,afterClosure.bytes);
const beforeRows=await read(beforeClosure.path);assert.deepEqual(beforeRows,await read(afterClosure.path));
assert.equal(Object.keys(beforeRows).length,4792);
const runtimePin=await pin(row.originalRuntimePath),pngPin=await pin(row.originalCapturePath);
assert.equal(runtimePin.sha256,row.originalRuntimeSha256);assert.equal(pngPin.sha256,row.originalCaptureSha256);
assert.equal(process.originalRuntimeSha256,runtimePin.sha256);assert.equal(process.originalCaptureSha256,pngPin.sha256);
const runtime=await read(runtimePin.path),png=await fs.readFile(pngPin.path);
assert(png.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])));
const pixels=[png.readUInt32BE(16),png.readUInt32BE(20)];
const wrapper=path.join(root,'scripts/unreal/exterior-editor-qa-r15.mjs');
const wrapperPin=await pin(wrapper);assert.equal(wrapperPin.sha256,'004d4d005369ceadcfbcfc34afbcac31d64924337fd720da4732064254f53171');
const originalParser=await pin(path.join(root,'scripts/unreal/exterior-editor-gpu-profile-r15.mjs'));
assert.equal(originalParser.sha256,'eafeb4dd3c982ce66802a1e271dfa711d4d3cc892d3f9de02a30651ad307e103');
const sourceReader=await pin(path.join(root,'scripts/unreal/exterior-editor-source-r12.mjs'));
assert.equal(sourceReader.sha256,'74dd17380ebc1990449721a3363d65dc4cc6d371641685154fdaa3443338353a');
const primary=await pin('/Users/Shared/Epic Games/UE_5.8/Engine/Source/Runtime/RHI/Private/GPUProfiler.cpp');
assert.equal(primary.sha256,'4705b04006232a4eea4d6842321939e0aa59f1c9d66b2ed0bdf62d781556cf37');
// Execute only the already-pinned pure verifier, in an isolated assertion-only context.
// No module top-level code, preflight, child launch, or engine calls are evaluated.
const wrapperText=await fs.readFile(wrapper,'utf8');
const start=wrapperText.indexOf('function verifyRuntime(r, row, png) {');
const end=wrapperText.indexOf('\nasync function runCase(view)',start);
assert(start>=0&&end>start);
const runtimeVerifier=wrapperText.slice(start,end);
vm.runInNewContext('const input=JSON.parse(serializedInput);('+runtimeVerifier+')(...input);',
  {assert,serializedInput:JSON.stringify([runtime,row,pixels])},{timeout:1000});
const artifact=runtime.gpuProfile.artifactPath,artifactPin=await pin(artifact),text=await fs.readFile(artifact,'utf8');
const parsed=validateGpuProfileArtifact(runtime,{runtimePath:runtimePin.path,caseDirectory:row.caseDirectory,text});
assert.equal(parsed.namedTimedRowCount,765);assert.equal(parsed.unnamedTimedRowCount,3);
assert.deepEqual(parsed.unnamedTimedRows.map(r=>[r.line,r.reportedMilliseconds]),[[243,[.072,.072]],[247,[.068,.068]],[697,[.082,.082]]]);
const sourceLines=text.split(/\r?\n/);
const emptyRows=parsed.unnamedTimedRows.map(r=>({...r,raw:sourceLines[r.line-1]}));
const unambiguousNaniteRenderRows=parsed.namedTimedRows.filter(r=>/^Nanite::(?:VisBuffer|DrawGeometry|BasePass)$/.test(r.event)&&r.reportedMilliseconds.some(v=>v>0));
assert(unambiguousNaniteRenderRows.length>0);
const self=await pin(path.join(root,OWNER));
const nativeReport=await typedPin(suite.nativeSourceEvidence.nativeReceipt);
assert.equal(nativeReport.sha256,'869ed396ed7946cb0ea562d3f2da77f8dbd9f3d65777250b9686171697aa10f1');
const receipt={schemaVersion:2,owner:OWNER,status:'actual-original-gpu-profile-cpu-reparse-validated-original-wrapper-rejection-preserved',
  producer:self,parser:await pin(path.join(root,'scripts/unreal/exterior-editor-gpu-profile-r15-r2.mjs')),
  cpuFixtureSource:await pin(path.join(root,'tests/unreal-editor-gpu-profile-r15-r2.test.mjs')),
  cpuChecks:{command:'node --test tests/unreal-editor-gpu-profile-r15-r2.test.mjs',passed:9,failed:0,
    rawTestLogPersisted:false,verificationSource:'Actual tool stdout; this audit does not rerun or synthesize the fixture log.'},
  originalFrozenWrapper:wrapperPin,originalFrozenParser:originalParser,originalFrozenR12Reader:sourceReader,
  installedPrimaryFormatter:primary,originalRejectedSuite:suitePin,originalProcess:processPin,actualEditorProcessId:68687,actualEditorExitCode:0,
  originalWrapperRejected:true,originalWrapperStatus:suite.status,originalWrapperFailure:suite.errors,
  originalRuntime:runtimePin,originalPng:pngPin,originalGpuArtifact:artifactPin,
  sourceInputClosure:{before:beforeClosure,after:afterClosure,fileCount:4792,capturedClosuresIdentical:true,currentFullClosureRehashedByThisAudit:false},
  originalNativeTreeReport:nativeReport,
  runtimeVerification:{source:'Exact pure verifyRuntime function extracted from frozen R15 wrapper',functionSha256:digest(runtimeVerifier),
    actualCpuVerificationPassed:true,scenePixels:pixels,sourceCamera:row.sourceCamera,observedCamera:runtime.walking.presentationCamera,
    actualComposedView:runtime.finalViewPostProcessSettings,nativeFovDirectReadbackAvailable:false,shaderAndLoadErrors:[],
    pendingShaderCountAtCaptureObserved:false},
  measuredFailure:{cause:'Filtering empty table cells removed the blank Events column and used the preceding Time column as the event name.',
    sourceColumn:'GPUProfiler.cpp FTable::AddRow Events = padded Name; blank Name is emitted without an assertion.',
    sourcePrimaryLines:[435,481,1783],emptyEventsRows:emptyRows,unchangedHeaderAndNumericTimingGuards:true,
    unnamedRowsEstablishPassProof:false},
  actualProfile:parsed,globalNaniteRenderPassObserved:true,unambiguousNaniteRenderRows,
  selectedTreeNaniteRenderPassVerified:false,selectedTreeEventAttributionAvailable:false,
  naniteInterpretation:'Positive Nanite::VisBuffer/DrawGeometry/BasePass timings are global render-pass observations. They do not identify the selected tree or establish per-mesh rendering/resource quality.',
  originalArtifactsEdited:false,originalRejectedSuiteRewritten:false,newEngineRunPerformed:false,nativeAppearanceAccepted:false,
  fullPhotorealismAccepted:false,performanceAccepted:false,shippingVerified:false,packageVerified:false,activeSelectorPromotionApproved:false,
  goNoGo:'GLOBAL_NANITE_RENDER_PASS_OBSERVED; SELECTED_TREE_ATTRIBUTION_UNVERIFIED; FULL_REALISM_NO_GO'};
assert.deepEqual(await pin(suitePath),suitePin);assert.deepEqual(await pin(artifact),artifactPin);
await fs.writeFile(output,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({audit:await pin(output),parser:receipt.parser,namedTimedRows:parsed.namedTimedRowCount,
  emptyTimedRows:parsed.unnamedTimedRowCount,globalNaniteRenderPassObserved:true,selectedTreeNaniteRenderPassVerified:false,originalWrapperRejected:true}));
