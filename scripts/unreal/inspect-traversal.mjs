import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const finiteVector = (v) => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite);
const dot = (a,b) => a.reduce((sum,n,i) => sum + n*b[i],0);
const length = (v) => Math.hypot(...v);
const subtract = (a,b) => a.map((n,i) => n-b[i]);
const close = (n, expected, epsilon) => Number.isFinite(n) && Math.abs(n-expected)<=epsilon;

/** Pure evidence gate. The caller separately verifies the app payload, process exit and runtime log. */
export function inspectTraversal({ runtime, contract, fixtures }) {
  const errors = [], check = (condition, text) => { if (!condition) errors.push(text); };
  check(fixtures?.schemaVersion === 1 && fixtures?.cases?.length === 6
    && JSON.stringify(fixtures?.simulationHz) === '[20,60]', 'Missing bounded six-leg source fixture set');
  if (!Array.isArray(fixtures?.cases) || !Array.isArray(contract?.walkSurfaces)
    || !Array.isArray(contract?.capturedClosedBlockers)) return {status:'failed',errors:[...errors,'Malformed fixture or walking contract'],verifiedScope:[]};
  check(runtime?.schemaVersion === 1 && runtime.status === 'passed-bounded-cases', 'Traversal did not complete successfully');
  check(runtime?.sceneSha256 === contract?.provenance?.sceneSha256 && runtime?.sceneSha256 === fixtures?.sceneSha256, 'Source provenance differs');
  const expected = new Map(fixtures.cases.flatMap(c => [20,60].map(hz=>[`${c.id}:${hz}`,{...c,hz}])));
  check(runtime?.expectedCasesIncludingRates === expected.size && runtime?.completedCases === expected.size
    && runtime?.failedCases === 0 && runtime?.results?.length === expected.size, 'Missing or failed cases');
  const seen = new Set();
  for (const result of runtime?.results ?? []) {
    const key = `${result.id}:${result.simulationHz}`, fixture=expected.get(key);
    check(!!fixture && !seen.has(key), `Unknown or duplicate case ${key}`); seen.add(key);
    if (!fixture) continue;
    const prefix = text => `${key}: ${text}`;
    const r=contract.capsuleRadiusCm, holdFrames=Math.ceil(fixture.holdSeconds*fixture.hz), brakeFrames=fixture.hz/2;
    check(result.status==='passed',prefix('native case failed'));
    check(JSON.stringify([...(result.allowedSupportObjectIds??[])].sort())===JSON.stringify([...fixture.allowedSupportObjectIds].sort()),prefix('source-derived coplanar floor references differ'));
    check(result.blockerObjectId===fixture.blockerObjectId && result.expectedSupportObjectId===fixture.supportObjectId, prefix('target IDs differ'));
    check(result.baselineSweepBlockingHit===true && result.baselineSweepStartPenetrating===false
      && result.baselineSweepObjectId===fixture.blockerObjectId, prefix('required collider was not the actual first capsule hit'));
    const entry=result.entryObservation??{};
    check(entry.worldContractValidated===true && entry.worldContractErrors?.length===0 && entry.sceneSha256===fixtures.sceneSha256
      && fixture.allowedSupportObjectIds.includes(entry.entrySupportObjectId)
      && fixture.allowedSupportObjectIds.includes(entry.entryLineHitObjectId) && entry.cameraMode==='walking'
      && entry.entryQueryStatus==='entry-floor-and-capsule-queries-passed',prefix('source world or entry invalid'));
    check(entry.expectedFloorObjects===contract.walkSurfaces.length
      && entry.expectedOffsetObjects===contract.walkSurfaces.filter(x=>x.supportOffsetCm!==0).length
      && entry.expectedClosedBlockers===contract.capturedClosedBlockers.length,prefix('source counts differ'));
    check(finiteVector(entry.lastEntryCapsuleCenterCm) && entry.lastEntryCapsuleCenterCm.slice(0,2)
      .every((n,i)=>close(n,fixture.eyeCm[i],.002)),prefix('entry changed fixture XY'));
    check(result.actualHoldFrames===holdFrames && result.holdWInputDownSamples===holdFrames
      && close(result.actualHoldSimulationSeconds,holdFrames/fixture.hz,1e-4),prefix('W hold timing or input missing'));
    check(result.releasedWInputDown===false && close(result.releasedSpeedCmPerSecond,0,.1),prefix('key release did not stop movement'));
    check(result.focusWasObservedBeforeNavigation===true && result.focusRestoredAfterEscape===true
      && result.cursorVisibleAfterEscape===true,prefix('Escape did not restore engine focus/cursor'));
    check(result.path?.length===holdFrames+brakeFrames,prefix('missing committed movement observations'));
    const rendering = result.rendering ?? {};
    check(rendering.sampleCount === holdFrames+brakeFrames && rendering.native4KThroughout === true
      && rendering.RHI === 'Metal' && rendering['r.ScreenPercentage'] === 100
      && rendering['r.SecondaryScreenPercentage.GameViewport'] === 100 && rendering['r.DynamicRes.OperationMode'] === 0
      && ['minimumSceneViewportPixels','minimumSceneRenderTargetPixels','minimumRHITexturePixels']
        .every(name=>JSON.stringify(rendering[name])==='[3840,2160]'),prefix('native 4K rendering was not continuously observed'));
    const point=result.actualColliderPointCm, normal=result.actualColliderNormal, start=result.startCapsuleCenterCm;
    check(finiteVector(point)&&finiteVector(normal)&&finiteVector(start),prefix('missing actual collider/start vectors'));
    if(!finiteVector(point)||!finiteVector(normal)||!finiteVector(start))continue;
    check(close(length(normal),1,1e-4)&&dot(normal,fixture.forward)<-.995,prefix('collider normal is not facing the approach'));
    const axis=fixture.forward.findIndex(n=>Math.abs(n)>.99), near=fixture.forward[axis]>0?'min':'max';
    check(close(point[axis],fixture.sourceBoundsCm[near][axis],.02),prefix('actual plane differs from source geometry'));
    let maxProgress=0;
    for(const [i,sample] of (result.path??[]).entries()) {
      const hold=i<holdFrames, phaseIndex=hold?i:i-holdFrames;
      check(sample.phase===(hold?'hold':'brake')&&sample.phaseFrame===phaseIndex+1,prefix(`sample ${i} phase discontinuity`));
      check(sample.grounded===true && fixture.allowedSupportObjectIds.includes(sample.supportObjectId),prefix(`sample ${i} unsupported`));
      check(sample.wInputDown===hold,prefix(`sample ${i} wrong key state`));
      check(sample.native4KSceneTargetAt100Percent===true,prefix(`sample ${i} did not render native 4K`));
      check(sample.unexpectedOverlap===false,prefix(`sample ${i} capsule penetration`));
      check(close(sample.simulationDeltaSeconds,1/fixture.hz,1e-5)
        && Number.isFinite(sample.wallIntervalSeconds)&&sample.wallIntervalSeconds>0,prefix(`sample ${i} invalid simulation/wall timing`));
      check(close(sample.measuredEyeHeightCm,contract.eyeHeightCm,.2)
        && close(sample.measuredFloorHeightCm,fixture.floorHeightCm,.02)
        && fixture.allowedSupportObjectIds.includes(sample.eyeReferenceFloorObjectId),prefix(`sample ${i} eye/floor reference differs`));
      check(finiteVector(sample.capsuleCenterCm)&&finiteVector(sample.cameraEyeCm)&&finiteVector(sample.velocityCmPerSecond),prefix(`sample ${i} vectors invalid`));
      if(!finiteVector(sample.capsuleCenterCm))continue;
      const delta=subtract(sample.capsuleCenterCm,start), progress=dot(delta,fixture.forward);
      const clearance=dot(subtract(sample.capsuleCenterCm,point),normal);
      maxProgress=Math.max(maxProgress,progress);
      check(clearance>=r-.05 && close(sample.colliderPlaneClearanceCm,clearance,.002),prefix(`sample ${i} crossed source collider plane`));
      check(Math.hypot(delta[0]-fixture.forward[0]*progress,delta[1]-fixture.forward[1]*progress)<=.2,prefix(`sample ${i} lateral drift`));
    }
    const last=result.path?.at(-1);
    check(maxProgress>=20,prefix('the character did not actually advance'));
    if(finiteVector(last?.capsuleCenterCm)) {
      const clearance=dot(subtract(last.capsuleCenterCm,point),normal);
      check(clearance>=r-.05&&clearance<=r+1,prefix('character did not stop at the target collider'));
      check(finiteVector(last.velocityCmPerSecond)&&length(last.velocityCmPerSecond)<=.1,prefix('final velocity not stopped'));
    }
  }
  return {status:errors.length?'failed':'bounded-native-observations-valid', errors,
    requiredProcessChecks:['clean-zero-exit','no-runtime-fatal-or-shader-fallback','package-payload-verified-before-and-after'],
    verifiedScope:errors.length?[]:['source-vertical-entry','listed-straight-collider-approaches','engine-input-release','engine-Escape-focus'],
    pending:['native-macOS-keyboard','VoiceOver','diagonal-wall-sliding','step-and-drop-traversal','precision-and-boost','physical-20-or-60-FPS'],
    rateMeaning:'20/60 describe simulation Hz only. No physical frame-rate acceptance is inferred.'};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const [runtimePath,contractPath,fixturesPath]=process.argv.slice(2);
  if(!runtimePath||!contractPath||!fixturesPath)throw Error('Pass traversal.json walking.json cases.json');
  const [runtime,contract,fixtures]=await Promise.all([runtimePath,contractPath,fixturesPath].map(async p=>JSON.parse(await readFile(p,'utf8'))));
  const result=inspectTraversal({runtime,contract,fixtures});
  console.log(JSON.stringify(result,null,2));
  if(result.errors.length)process.exitCode=1;
}
