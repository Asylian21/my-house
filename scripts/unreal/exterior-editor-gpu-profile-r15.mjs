// CPU parsing only. UE5.8 ProfileGPU is aggregate pass evidence, not mesh attribution.
import assert from 'node:assert/strict';
import path from 'node:path';
export const OWNER='scripts/unreal/exterior-editor-gpu-profile-r15.mjs';

export function validateGpuProfileMetadata(runtime,{runtimePath,caseDirectory}){
  const p=runtime?.gpuProfile;assert(p,'Actual recorder gpuProfile is missing');
  assert.equal(p.requestedByCLI,true);assert.equal(p.status,'profile-log-observed');
  assert.equal(p.backend,'UE5.8 ProfileGPU command to LogRHI; no trace session requested');
  assert.equal(p.profileHeaderObserved,true);assert.equal(p.artifactSaved,true);assert.equal(p.artifactTruncated,false);
  assert.equal(typeof p.profilerActiveObserved,'boolean');
  assert.equal(p.requestWarmupFrame,1200);assert(Number.isInteger(p.extraExcludedWarmupFrames)&&p.extraExcludedWarmupFrames>=0);
  assert(path.isAbsolute(runtimePath)&&path.resolve(runtimePath)===runtimePath&&runtimePath.endsWith('.json'));
  assert(path.dirname(runtimePath).endsWith(path.sep+'Diagnostics')&&runtimePath.startsWith(path.resolve(caseDirectory)+path.sep));
  const expected=runtimePath.slice(0,-5)+'-gpu-profile.log';assert.equal(p.artifactPath,expected);
  assert.equal(path.resolve(p.artifactPath),p.artifactPath);return expected;
}

export function parseGpuProfileText(text){
  assert(typeof text==='string'&&text.length>0&&text.length<=2*1024*1024,'Original profile is empty/oversized');
  assert(!text.includes('\u0000'),'Original profile contains NUL');
  const headers=[],rows=[];let frame=null;
  for(const [i,line]of text.split(/\r?\n/).entries()){
    const trimmed=line.trim(),h=/^GPU Profile for Frame (\d+) - (.+)$/.exec(trimmed);
    if(h){frame=Number(h[1]);assert(Number.isSafeInteger(frame)&&frame>=0);headers.push({line:i+1,frame,heading:h[2]});continue;}
    if(frame===null)continue;
    let name,times,format;
    if(/^[┃|].*[┃|]$/.test(trimmed)){
      times=[...trimmed.matchAll(/(-?\d+(?:\.\d+)?)\s*ms\b/g)].map(m=>Number(m[1]));
      if(!times.length)continue;
      const cells=trimmed.split(/[┃│|]/).map(v=>v.trim()).filter(Boolean);name=cells.at(-1);format='ue58-table';
      assert(times.length<=2,'Unexpected ProfileGPU table timing-column count');
    }else{
      const m=/^\s*\d+(?:\.\d+)?%\s+(-?\d+(?:\.\d+)?)ms(?:\s+\+\s+\d+(?:\.\d+)?\s+Wait)?\s+(.+)$/.exec(line);
      if(!m)continue;times=[Number(m[1])];name=m[2].trim();format='ue58-indented-inclusive';
    }
    assert(times.every(v=>Number.isFinite(v)&&v>=0),'Negative/nonfinite actual pass timing');
    assert(name&&/[A-Za-z]/.test(name)&&!/^[-+\d.\s%]+(?:ms)?$/.test(name),'Timed row has no event name');
    if(/^\d+ Other Children$/.test(name))continue; // Engine aggregate for hidden children is not a named pass.
    rows.push({line:i+1,frame,event:name,reportedMilliseconds:times,format});
  }
  assert(headers.length>0,'No exact original GPU Profile for Frame header');
  assert(rows.length>=2&&new Set(rows.map(r=>r.event)).size>=2,
    'Profile header/frame summary alone is not meaningful named per-pass data');
  assert(rows.some(r=>!/^Frame(?:\s+\d+)?$/i.test(r.event)&&r.reportedMilliseconds.some(v=>v>0)),
    'No positive non-frame GPU pass timing was observed');
  const nanite=rows.filter(r=>/\bNanite\b/i.test(r.event));
  return {profileHeaders:headers,namedTimedRows:rows,namedTimedRowCount:rows.length,globalNaniteTimedRows:nanite,
    globalNaniteNamedEventsObserved:nanite.length>0,globalPositiveNaniteTimingObserved:nanite.some(r=>r.reportedMilliseconds.some(v=>v>0)),
    selectedTreeNaniteRenderPassVerified:false,selectedTreeEventAttributionAvailable:false,performanceAccepted:false,
    scope:'Aggregate named GPU passes; no per-selected-tree attribution or stable performance comparison.'};
}

export function validateGpuProfileArtifact(runtime,{runtimePath,caseDirectory,text}){
  const artifactPath=validateGpuProfileMetadata(runtime,{runtimePath,caseDirectory}),parsed=parseGpuProfileText(text);
  return {owner:OWNER,status:'original-untruncated-gpu-profile-with-named-timings-validated',artifactPath,
    profilerActivePollingObserved:runtime.gpuProfile.profilerActiveObserved,profileOutputHeaderObserved:true,
    extraExcludedWarmupFrames:runtime.gpuProfile.extraExcludedWarmupFrames,...parsed};
}
