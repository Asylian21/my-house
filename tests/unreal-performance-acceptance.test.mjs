import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {assessMeasurements, expectedCases, gpuEvidence, acceptanceMarkdown,
  validateAcceptancePlan, PACKAGE_SHA256, BASELINE_PACKAGE_SHA256, WALK_BASELINE_PACKAGE_SHA256, BASELINE_SESSION, FINAL_SESSION} from '../scripts/unreal/performance-acceptance.mjs';

const statistics=(mean=10)=>({status:'measured',sampleCount:300,meanMs:mean,p50Ms:mean,p95Ms:mean+1,p99Ms:mean+2,maxMs:mean+3});
function row(c,phase=c.software?'shipping-software1080':c.motion==='walk'?'shipping-walk':'shipping-final') {
  return {...c,phase,packageReportSha256:PACKAGE_SHA256,configuration:'Shipping',eligibleForAcceptance:true,valid:true,
    validation:'measured',nativeStatus:'capture-complete',process:{code:0,signal:null},foreground:true,foregroundFraction:1,
    motionComplete:c.motion==='static'?null:true,frame:statistics(),gpu:statistics(),gpuIntegrity:{status:'measured'},
    cpu:statistics(1),render:statistics(2),pixels:c.output==='retina'?[1920,1080]:[3840,2160],limitations:[],
    camera:{eyeCm:[1,2,3],forward:[0,1,0],activeView:c.scene.split('-')[0],mode:'orbit'},
    settings:{'r.ScreenPercentage':{native:100,balanced:67,performance:50}[c.profile],
      'r.TSR.History.ScreenPercentage':100,'r.VSync':0,'t.MaxFPS':0,
      'r.Lumen.HardwareRayTracing':c.software||c.profile==='performance'?0:1},
    artifacts:{directory:`/qa/${phase==='shipping-final'?FINAL_SESSION:phase+'-123'}/${c.scene}-${c.profile}-${c.output}-${c.motion}`}};
}
const complete=()=>{const c=expectedCases();return [...c.main,...c.software].map(x=>row(x));};
test('empty and partial reports stay pending; all 60 main and 8 separate software cases are required',()=>{
  const empty=assessMeasurements({rows:[]});assert.equal(empty.status,'pending');assert.equal(empty.mainCoverage.required,60);assert.equal(empty.softwareCoverage.required,8);
  const rs=complete();assert.equal(assessMeasurements({rows:rs.slice(0,60)}).status,'pending');
  const r=assessMeasurements({rows:rs});assert.equal(r.status,'passed');assert.equal(r.requirements.performanceRetina.required,10);
  assert.equal(r.requirements.balancedRetina.required,10);assert.equal(r.performanceSoftwarePath.verified,20);
});
test('wrong package, altered pixel/profile readback and focus loss cannot fulfill a case',()=>{
  for(const mutate of [r=>r.packageReportSha256='0'.repeat(64),r=>r.pixels=[960,540],r=>r.settings['r.ScreenPercentage']=100,r=>r.foreground=false]){
    const rs=complete();mutate(rs[0]);const r=assessMeasurements({rows:rs});assert.equal(r.status,'pending');assert.equal(r.mainCoverage.eligible,59);
  }
});
test('eligible recheck supersedes the matching final row without choosing its higher FPS; duplicates fail closed',()=>{
  const rs=complete(),original=rs[0],recheck=row(original,'shipping-recheck-gpu');recheck.frame=statistics(20);rs.push(recheck);
  let r=assessMeasurements({rows:rs});assert.equal(r.status,'failed');assert.equal(r.comparisons[0].case.selected.phase,'shipping-recheck-gpu');
  rs.push(structuredClone(recheck));r=assessMeasurements({rows:rs});assert.equal(r.mainCoverage.ambiguous,1);assert.equal(r.status,'pending');
  recheck.foreground=false;rs.pop();r=assessMeasurements({rows:rs});assert.equal(r.comparisons[0].case.selected.phase,'shipping-final');
});
test('software GPU recheck supersedes only its software case and retains the original observation',()=>{
  const rs=complete(),original=rs.find(r=>r.software&&r.scene==='interior-day'&&r.motion==='orbit');
  original.gpu.maxMs=999999;
  const recheck=row(original,'shipping-recheck-gpu');recheck.frame=statistics(15);
  const otherMode=row({...original,software:false},'shipping-recheck-gpu');
  const get=rows=>assessMeasurements({rows}).softwareCases.find(c=>c.scene==='interior-day'&&c.motion==='orbit');
  assert.equal(get([...rs,otherMode]).selected.phase,'shipping-software1080');
  const selected=get([...rs,otherMode,recheck]);
  assert.equal(selected.status,'eligible');assert.equal(selected.selected.phase,'shipping-recheck-gpu');
  assert.equal(selected.selected.frame.meanMs,15);assert.equal(selected.selected.gpu.usable,true);
  assert.match(selected.selectionReason,/supersedes/);
  assert.equal(selected.originalRows.length,1);assert.equal(selected.originalRows[0].phase,'shipping-software1080');
  assert.equal(selected.originalRows[0].gpu.usable,false);assert.equal(selected.originalRows[0].gpu.raw.maxMs,999999);
  const wrongPin=structuredClone(recheck);wrongPin.packageReportSha256='b'.repeat(64);
  assert.equal(get([...rs,wrongPin]).selected.phase,'shipping-software1080');
  assert.equal(get([...rs,recheck,structuredClone(recheck)]).status,'ambiguous');
});
test('strict Balanced p99 boundary and walks participate in thresholds; 4K/Native have no FPS threshold',()=>{
  const rs=complete(),walk=rs.find(r=>r.profile==='balanced'&&r.output==='retina'&&r.motion==='walk');
  walk.frame=statistics(30);walk.frame.p99Ms=33.3;walk.frame.maxMs=34;
  assert.equal(assessMeasurements({rows:rs}).requirements.balancedRetina.status,'failed');
  walk.frame.p99Ms=33.29;assert.equal(assessMeasurements({rows:rs}).status,'passed');
  for(const r of rs.filter(r=>r.output==='4k'||r.profile==='native'))r.frame=statistics(100);
  assert.equal(assessMeasurements({rows:rs}).status,'passed');
});
test('impossible GPU timestamp does not invalidate FPS and its raw aggregates cannot enter accepted GPU data',()=>{
  const rs=complete();rs[0].gpu.maxMs=999999;rs[0].gpu.meanMs=5000;
  const r=assessMeasurements({rows:rs});assert.equal(r.status,'passed');assert.equal(r.gpuTimingCoverage.usableGPUCases,67);
  assert.equal(gpuEvidence(rs[0]).accepted,null);assert.equal(gpuEvidence(rs[0]).raw.meanMs,5000);
  assert.match(acceptanceMarkdown(r),/unreliable-timestamp-outlier/);
});
test('only exact original baseline session is selected; camera mismatch qualifies comparison without blocking acceptance',()=>{
  const rs=complete(),original=structuredClone(rs[0]);Object.assign(original,{phase:'baseline',configuration:'Development',packageReportSha256:BASELINE_PACKAGE_SHA256});
  original.artifacts.directory=`/qa/${BASELINE_SESSION}/original`;
  const smoke=structuredClone(original);smoke.artifacts.directory='/qa/baseline-earlier/smoke';rs.push(original,smoke);
  let r=assessMeasurements({rows:rs});assert.equal(r.comparisons[0].baseline.selected.artifacts.directory,original.artifacts.directory);assert(r.comparisons[0].delta);
  original.camera.eyeCm=[54,2,3];r=assessMeasurements({rows:rs});assert.equal(r.status,'passed');assert.equal(r.comparisons[0].camera.status,'static-camera-mismatch');assert.equal(r.comparisons[0].delta,null);
  const recheck=structuredClone(smoke);recheck.phase='baseline-camera-recheck';rs.push(recheck);
  r=assessMeasurements({rows:rs});assert.equal(r.comparisons[0].baseline.selected.phase,'baseline-camera-recheck');assert(r.comparisons[0].delta);
});
test('walking baseline requires the pinned instrumented package and remains a qualified moving-run comparison',()=>{
  const rs=complete(),walk=rs.find(r=>r.motion==='walk'),before=structuredClone(walk);
  Object.assign(before,{phase:'baseline-walk',configuration:'Development',packageReportSha256:BASELINE_PACKAGE_SHA256});
  rs.push(before);let result=assessMeasurements({rows:rs}).comparisons.find(c=>c.key.includes('/walk/'));
  assert.equal(result.baseline.status,'missing');
  before.packageReportSha256=WALK_BASELINE_PACKAGE_SHA256;
  result=assessMeasurements({rows:rs}).comparisons.find(c=>c.key.includes('/walk/'));
  assert.equal(result.baseline.status,'eligible');assert.equal(result.baseline.selected.frame.meanMs,10);
  assert.match(result.baseline.instrumentationProvenance.qualification,/four diagnostic\/Pawn files/);
  assert.equal(result.camera.status,'trajectory-not-fully-recorded');assert.equal(result.delta,null);
});

const newPlan={packageReportSha256:'a'.repeat(64),finalSession:'shipping-final-1790999999999'};
function plannedRows() {
  return complete().map(r=>({...r,packageReportSha256:newPlan.packageReportSha256,
    artifacts:{...r.artifacts,directory:r.artifacts.directory.replace(FINAL_SESSION,newPlan.finalSession)}}));
}
test('explicit plan selects only its new package and final session while baseline pins remain historical',()=>{
  const current=plannedRows(),old=complete(),wrongSession=structuredClone(current[0]),wrongHash=structuredClone(current[0]);
  wrongSession.artifacts.directory='/qa/shipping-final-123/unplanned';wrongSession.frame=statistics(1);
  wrongHash.packageReportSha256='b'.repeat(64);wrongHash.artifacts.directory+= '-wrong-hash';
  const oldRecheck=row(old[0],'shipping-recheck-focus');oldRecheck.frame=statistics(1);
  const baseline={...structuredClone(old[0]),phase:'baseline',configuration:'Development',packageReportSha256:BASELINE_PACKAGE_SHA256,
    artifacts:{directory:`/qa/${BASELINE_SESSION}/original`}};
  const changedBaseline={...structuredClone(baseline),packageReportSha256:newPlan.packageReportSha256};
  const input={rows:[...old,...current,wrongSession,wrongHash,oldRecheck,baseline,changedBaseline]};
  const r=assessMeasurements(input,undefined,newPlan);
  assert.equal(r.status,'passed');assert.equal(r.mainCoverage.eligible,60);assert.equal(r.softwareCoverage.eligible,8);
  assert.equal(r.packageReportSha256,newPlan.packageReportSha256);assert.equal(r.originalFinalSession,newPlan.finalSession);
  assert.equal(r.comparisons[0].case.selected.artifacts.directory,current[0].artifacts.directory);
  assert.equal(r.comparisons[0].baseline.selected.packageReportSha256,BASELINE_PACKAGE_SHA256);
  assert.equal(r.originalBaselineSession,BASELINE_SESSION);assert.equal(r.instrumentedWalkingBaselinePackageSha256,WALK_BASELINE_PACKAGE_SHA256);
  assert(r.comparisons[0].delta);assert.equal(assessMeasurements({rows:current}).mainCoverage.eligible,0);
  current[0].artifacts.directory='/qa/shipping-final-123/wrong-session';
  assert.equal(assessMeasurements({rows:[...old,...current]},undefined,newPlan).mainCoverage.eligible,59);
});
test('explicit acceptance plans reject malformed hashes, session paths and undeclared overrides without falling back',()=>{
  for (const plan of [null,[],{}, {...newPlan,packageReportSha256:'A'.repeat(64)}, {...newPlan,packageReportSha256:'abc'},
    {...newPlan,finalSession:'../shipping-final-123'}, {...newPlan,finalSession:'shipping-final-123/child'},
    {...newPlan,finalSession:'shipping-final-123\n'}, {...newPlan,finalSession:'baseline-123'},
    {...newPlan,finalSession:123}, {...newPlan,baselineSession:'replacement'}])
    assert.throws(()=>assessMeasurements({rows:complete()},undefined,plan),/Acceptance plan/);
  assert.deepEqual(validateAcceptancePlan(),{packageReportSha256:PACKAGE_SHA256,finalSession:FINAL_SESSION});
});
test('acceptance CLI third argument records the exact plan file SHA and uses the new pins',async t=>{
  const dir=await mkdtemp(resolve(tmpdir(),'brezi-acceptance-plan-'));t.after(()=>rm(dir,{recursive:true,force:true}));
  const input=JSON.stringify({rows:plannedRows()}),planBytes=JSON.stringify(newPlan,null,2)+'\n';
  const planPath=resolve(dir,'plan.json');await writeFile(planPath,planBytes);await writeFile(resolve(dir,'measurements.json'),input);
  await promisify(execFile)(process.execPath,[resolve(import.meta.dirname,'../scripts/unreal/performance-acceptance.mjs'),dir,planPath]);
  const result=JSON.parse(await readFile(resolve(dir,'acceptance.json'),'utf8'));
  assert.equal(result.status,'passed');assert.equal(result.packageReportSha256,newPlan.packageReportSha256);
  assert.equal(result.originalFinalSession,newPlan.finalSession);assert.equal(result.plan.path,planPath);
  assert.equal(result.plan.sha256,createHash('sha256').update(planBytes).digest('hex'));
  assert.equal(result.plan.sha256Scope,'exact-input-file-bytes');
  assert.equal(await readFile(resolve(dir,'measurements.json'),'utf8'),input);assert.equal(await readFile(planPath,'utf8'),planBytes);
});
