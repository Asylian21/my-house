import test from 'node:test';
import assert from 'node:assert/strict';
import {validateGpuProfileMetadata,parseGpuProfileText,validateGpuProfileArtifact} from '../scripts/unreal/exterior-editor-gpu-profile-r15-r2.mjs';
// CPU fixtures follow installed GPUProfiler.cpp formatting; these are not native evidence.
const caseDirectory='/tmp/r15-own-case',runtimePath=caseDirectory+'/userdir/Saved/Diagnostics/exterior-canopy-close-day-20261002T050000.json';
const p={requestedByCLI:true,status:'profile-log-observed',backend:'UE5.8 ProfileGPU command to LogRHI; no trace session requested',
  requestWarmupFrame:1200,extraExcludedWarmupFrames:3,profilerActiveObserved:false,profileHeaderObserved:true,artifactSaved:true,
  artifactTruncated:false,artifactPath:runtimePath.slice(0,-5)+'-gpu-profile.log'};
const unicode='GPU Profile for Frame 1210 - Graphics\n    ┃ 0.01 ms │ 0.03 ms ┃ Frame ┃\n    ┃ 0.02 ms │ 0.02 ms ┃   Nanite::CullRasterize ┃\n';

test('observed output is required separately from accepted command or active polling',()=>{
  validateGpuProfileMetadata({gpuProfile:p},{runtimePath,caseDirectory});
  for(const[k,v]of [['requestedByCLI',false],['status','requested-unconfirmed'],['profileHeaderObserved',false],['artifactSaved',false],
    ['artifactTruncated',true],['requestWarmupFrame',0],['extraExcludedWarmupFrames',-1]]){
    const bad={...p,[k]:v};assert.throws(()=>validateGpuProfileMetadata({gpuProfile:bad},{runtimePath,caseDirectory}));
  }
  const result=validateGpuProfileArtifact({gpuProfile:p},{runtimePath,caseDirectory,text:unicode});
  assert.equal(result.profilerActivePollingObserved,false);assert.equal(result.profileOutputHeaderObserved,true);
});

test('only the exact own recorder Diagnostics sibling artifact is allowed',()=>{
  for(const path of ['/tmp/foreign.log',caseDirectory+'/userdir/Saved/Diagnostics/other-gpu-profile.log'])
    assert.throws(()=>validateGpuProfileMetadata({gpuProfile:{...p,artifactPath:path}},{runtimePath,caseDirectory}));
  assert.throws(()=>validateGpuProfileMetadata({gpuProfile:p},{runtimePath:'/tmp/outside.json',caseDirectory}));
});

test('Unicode and ASCII timed event tables follow the installed UE5.8 layout',()=>{
  const u=parseGpuProfileText(unicode);assert.equal(u.namedTimedRowCount,2);assert.deepEqual(u.namedTimedRows[1].reportedMilliseconds,[.02,.02]);
  const ascii='GPU Profile for Frame 1210 - Graphics\n | 1 | 0.01 ms | 0.04 ms | Frame |\n | 7 | 0.03 ms | 0.03 ms | BasePass |\n';
  assert.equal(parseGpuProfileText(ascii).namedTimedRows[1].event,'BasePass');
});

test('a header or frame summary without meaningful named per-pass timing is rejected',()=>{
  for(const text of ['GPU Profile for Frame 1 - Graphics\n','GPU Profile for Frame 1 - Graphics\n100.0% 30.00ms Frame\n',
    'GPU Profile for Frame 1 - Graphics\n100.0% 0.00ms Frame\n0.0% 0.00ms BasePass\n'])assert.throws(()=>parseGpuProfileText(text));
  assert.throws(()=>parseGpuProfileText('100.0% 30.00ms Frame\n50.0% 15.00ms BasePass\n'));
});

test('legacy inclusive names are retained while Nanite presence stays aggregate and unaccepted',()=>{
  const text='GPU Profile for Frame 18 - Graphics\n100.0% 3.00ms Frame\n 50.0% 1.50ms + 0.02 Wait Nanite::EmitGBuffer\n';
  const r=parseGpuProfileText(text);assert.equal(r.globalPositiveNaniteTimingObserved,true);
  assert.equal(r.selectedTreeNaniteRenderPassVerified,false);assert.equal(r.selectedTreeEventAttributionAvailable,false);assert.equal(r.performanceAccepted,false);
  const ordinary=parseGpuProfileText(text.replace('Nanite::EmitGBuffer','BasePass'));assert.equal(ordinary.globalNaniteNamedEventsObserved,false);
});

test('negative durations, corrupted artifact and aggregate hidden children cannot establish pass proof',()=>{
  assert.throws(()=>parseGpuProfileText(unicode.replace('0.02 ms','-0.02 ms')));
  assert.throws(()=>parseGpuProfileText(unicode+'\0'));
  assert.throws(()=>parseGpuProfileText('GPU Profile for Frame 1 - Graphics\n100.0% 3.00ms Frame\n50.0% 1.50ms 9 Other Children\n'));
});

test('empty actual Events cells are separate observations and never named pass proof',()=>{
  const empty='    ┃ 0 │ 0 │ 0 │ 0 │ 0.2% ┊ │ 0.072 ms ┃ 0 │ 0 │ 0 │ 0 │ 0.2% ┊ │ 0.072 ms ┃     ┃\n';
  const result=parseGpuProfileText(unicode+empty);
  assert.equal(result.namedTimedRowCount,2);
  assert.equal(result.unnamedTimedRowCount,1);
  assert.deepEqual(result.unnamedTimedRows[0].reportedMilliseconds,[.072,.072]);
  assert.equal(result.unnamedTimedRows[0].establishesNamedPassEvidence,false);
  assert.throws(()=>parseGpuProfileText('GPU Profile for Frame 1 - Graphics\n'+empty+empty));
  assert.throws(()=>parseGpuProfileText(unicode+empty.replace('0.072 ms','-0.072 ms')));
  assert.throws(()=>parseGpuProfileText(unicode+empty.replace('┃     ┃','┃ 0.072 ms ┃')));
});

test('ASCII empty final columns do not acquire the previous timing cell name',()=>{
  const blank=' | 0.02 ms | 0.02 ms |   |\n';
  const result=parseGpuProfileText(unicode+blank);
  assert.equal(result.unnamedTimedRows[0].format,'ue58-table');
  assert.equal(result.namedTimedRowCount,2);
  assert.throws(()=>parseGpuProfileText('GPU Profile for Frame 1 - Graphics\n | 3.00 ms | 3.00 ms | Frame |\n'+blank));
});

test('the installed synthetic root plus Frame summary is still not per-pass proof',()=>{
  assert.throws(()=>parseGpuProfileText('GPU Profile for Frame 1 - Graphics\n | 3.00 ms | 3.00 ms | <root> |\n | 3.00 ms | 3.00 ms | Frame 1 |\n'));
});
