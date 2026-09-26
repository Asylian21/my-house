// Pure saved-report analysis. No application, engine, or graphics process is launched.
import {readFile, writeFile} from 'node:fs/promises';
import {resolve, basename, dirname} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

export const PACKAGE_SHA256 = '60ee4ec95c7c39d982b0f6c2ddfc312366ad434df7c07e452e811cc49ed3761a';
export const BASELINE_SESSION = 'baseline-1790193917881';
export const FINAL_SESSION = 'shipping-final-1790199522964';
export const BASELINE_PACKAGE_SHA256 = 'f3bfbbbf0746ee3f5ab6eeedda4cd0cfba2cbf353bd667330e2ab7f8164f1890';
export const WALK_BASELINE_PACKAGE_SHA256 = '0ce20dfe744a69760db5625581db18e8b8b09a443982f06c22622426a173b068';
const defaultPlan = Object.freeze({packageReportSha256:PACKAGE_SHA256, finalSession:FINAL_SESSION});
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

export function validateAcceptancePlan(plan = defaultPlan) {
  if (!plan || typeof plan !== 'object' || Array.isArray(plan)
    || Object.keys(plan).sort().join(',') !== 'finalSession,packageReportSha256')
    throw Error('Acceptance plan must contain only packageReportSha256 and finalSession');
  if (typeof plan.packageReportSha256 !== 'string' || plan.packageReportSha256.length !== 64 || !/^[a-f0-9]{64}$/.test(plan.packageReportSha256))
    throw Error('Acceptance plan packageReportSha256 must be a lowercase SHA256 hash');
  if (typeof plan.finalSession !== 'string' || plan.finalSession.trim() !== plan.finalSession || !/^shipping-final-[0-9]+$/.test(plan.finalSession))
    throw Error('Acceptance plan finalSession must be an exact shipping-final-<timestamp> session name');
  return {packageReportSha256:plan.packageReportSha256, finalSession:plan.finalSession};
}
const scenes = ['street-day', 'terrace-day', 'interior-day', 'interior-night'];
const profiles = ['performance', 'balanced', 'native'];
const outputs = ['retina', '4k'];
const stats = ['meanMs', 'p50Ms', 'p95Ms', 'p99Ms', 'maxMs'];
const finite = value => typeof value === 'number' && Number.isFinite(value);
const key = row => [row.scene, row.profile, row.output, row.motion, row.software ? 'software' : 'main'].join('/');
const session = row => basename(dirname(row.artifacts?.directory ?? ''));
const fps = row => finite(row?.frame?.meanMs) && row.frame.meanMs > 0 ? 1000 / row.frame.meanMs : null;

export function expectedCases() {
  const main = [], software = [];
  for (const profile of profiles) for (const output of outputs) {
    for (const scene of scenes) for (const motion of ['static', 'orbit']) main.push({scene, profile, output, motion, software:false});
    for (const scene of ['interior-day', 'interior-night']) main.push({scene, profile, output, motion:'walk', software:false});
  }
  for (const scene of scenes) for (const motion of ['static', 'orbit'])
    software.push({scene, profile:'balanced', output:'retina', motion, software:true});
  return {main, software};
}

function validStats(value) {
  return value?.status === 'measured' && Number.isInteger(value.sampleCount) && value.sampleCount > 0
    && stats.every(name => finite(value[name]) && value[name] >= 0)
    && value.p50Ms <= value.p95Ms && value.p95Ms <= value.p99Ms && value.p99Ms <= value.maxMs;
}

function timingIssues(row) {
  const issues = [];
  if (row.eligibleForAcceptance !== true) issues.push('measurement-report-ineligible');
  if (row.valid !== true || row.validation !== 'measured' || row.nativeStatus !== 'capture-complete') issues.push('native-or-QA-validation-incomplete');
  if (row.process?.code !== 0 || row.process?.signal != null) issues.push('producer-did-not-exit-cleanly');
  if (row.foreground !== true || row.foregroundFraction !== 1) issues.push('foreground-not-continuous');
  if (!validStats(row.frame) || row.frame.meanMs <= 0 || row.frame.sampleCount < 240) issues.push('frame-statistics-ineligible');
  if (row.motion !== 'static' && row.motionComplete !== true) issues.push('motion-incomplete');
  if (row.limitations?.includes('traced-attribution-run-not-untraced-performance')) issues.push('traced-run');
  return issues;
}

function shippingIssues(row, plan) {
  const issues = timingIssues(row);
  if (row.configuration !== 'Shipping') issues.push('not-Shipping');
  if (row.packageReportSha256 !== plan.packageReportSha256) issues.push('different-package-hash');
  const pixels = row.output === 'retina' ? [1920,1080] : [3840,2160];
  if (JSON.stringify(row.pixels) !== JSON.stringify(pixels)) issues.push('output-pixels-differ');
  if (row.settings?.['r.ScreenPercentage'] !== {native:100, balanced:67, performance:50}[row.profile]
    || row.settings?.['r.TSR.History.ScreenPercentage'] !== 100) issues.push('profile-resolution-readback-differs');
  if (row.settings?.['r.VSync'] !== 0 || row.settings?.['t.MaxFPS'] !== 0) issues.push('uncapped-readback-differs');
  if ((row.software || row.profile === 'performance') && row.settings?.['r.Lumen.HardwareRayTracing'] !== 0)
    issues.push('software-Lumen-readback-differs');
  return issues;
}

export function gpuEvidence(row) {
  if (!row) return null;
  const impossible = validStats(row.gpu) && finite(row.frame?.meanMs) && finite(row.frame?.sampleCount)
    && row.gpu.maxMs > row.frame.meanMs * row.frame.sampleCount;
  const usable = validStats(row.gpu) && row.gpuIntegrity?.status === 'measured' && !impossible;
  return {usable, status:impossible ? 'unreliable-timestamp-outlier' : row.gpuIntegrity?.status ?? 'integrity-unavailable',
    accepted:usable ? row.gpu : null, raw:row.gpu ?? null, reportedIntegrity:row.gpuIntegrity ?? null};
}

function evidence(row) {
  if (!row) return null;
  return {phase:row.phase, artifacts:row.artifacts, packageReportSha256:row.packageReportSha256,
    configuration:row.configuration, eligibleForAcceptance:row.eligibleForAcceptance, fps:fps(row),
    frame:row.frame, gpu:gpuEvidence(row), gameThread:row.cpu, renderThread:row.render,
    camera:row.camera ?? null,
    pixels:row.pixels, hardwareLumen:row.settings?.['r.Lumen.HardwareRayTracing'], statOverlays:row.statOverlays,
    limitations:row.limitations ?? []};
}

function selectShipping(rows, requested, plan) {
  const phases = requested.software ? ['shipping-recheck-gpu', 'shipping-software1080'] : requested.motion === 'walk' ? ['shipping-walk']
    : ['shipping-recheck-focus', 'shipping-recheck-gpu', 'shipping-final'];
  const candidates = rows.filter(row => key(row) === key(requested) && phases.includes(row.phase)
    && (row.phase !== 'shipping-final' || session(row) === plan.finalSession));
  let selected = null, ambiguity = null;
  for (const phase of phases) {
    const eligible = candidates.filter(row => row.phase === phase && shippingIssues(row,plan).length === 0);
    if (eligible.length > 1) { ambiguity = `multiple-eligible-${phase}-rows`; break; }
    if (eligible.length === 1) { selected = eligible[0]; break; }
  }
  const originalPhase = requested.software ? 'shipping-software1080' : requested.motion === 'walk' ? 'shipping-walk' : 'shipping-final';
  const original = candidates.filter(row => row.phase === originalPhase);
  return {...requested, key:key(requested), status:ambiguity ? 'ambiguous' : selected ? 'eligible' : candidates.length ? 'ineligible' : 'missing',
    issues:ambiguity ? [ambiguity] : selected ? [] : [...new Set(candidates.flatMap(row => shippingIssues(row,plan)))],
    selected:evidence(selected),
    selectionReason:selected && selected.phase !== originalPhase
      ? `eligible ${selected.phase} supersedes the corresponding original case, independent of its FPS value` : 'unique eligible planned phase',
    originalRows:original.map(evidence), candidates:candidates.map(row => ({...evidence(row), issues:shippingIssues(row,plan)}))};
}

function compareCamera(before, after, motion) {
  if (motion !== 'static') return {status:'trajectory-not-fully-recorded', matched:false,
    limitation:'A terminal orbit/walk camera pose does not prove the full trajectory matched. Raw timings remain descriptive.'};
  const a=before?.camera, b=after?.camera;
  const vector=v => Array.isArray(v) && v.length===3 && v.every(finite);
  if (!vector(a?.eyeCm) || !vector(b?.eyeCm) || !vector(a?.forward) || !vector(b?.forward))
    return {status:'camera-evidence-unavailable', matched:false};
  const distance=(v,w)=>Math.hypot(...v.map((n,i)=>n-w[i]));
  const eyeDistanceCm=distance(a.eyeCm,b.eyeCm), forwardDifference=distance(a.forward,b.forward);
  const matched=eyeDistanceCm<=0.1 && forwardDifference<=1e-5 && a.activeView===b.activeView && a.mode===b.mode;
  return {status:matched?'static-camera-matched':'static-camera-mismatch', matched, eyeDistanceCm, forwardDifference,
    tolerance:{eyeCm:0.1,forwardVector:1e-5},before:a,after:b};
}

function selectBaseline(rows, requested) {
  if (requested.software) return {status:'not-measured-for-this-case', selected:null, issues:[]};
  if (requested.motion === 'walk') {
    const candidates=rows.filter(row=>row.phase==='baseline-walk' && key(row)===key(requested)
      && row.packageReportSha256===WALK_BASELINE_PACKAGE_SHA256);
    if(candidates.length!==1)return {status:candidates.length?'ambiguous':'missing',selected:null,
      issues:['expected-one-pinned-instrumented-walking-baseline']};
    const issues=timingIssues(candidates[0]);
    return {status:issues.length?'observed-but-ineligible':'eligible',selected:evidence(candidates[0]),issues,
      instrumentationProvenance:{packageReportSha256:WALK_BASELINE_PACKAGE_SHA256,
        report:'output/unreal/performance-baseline-instrumented-20260923-r1/baseline-instrumentation.json',
        qualification:'Original donor renderer and scene, with four diagnostic/Pawn files replaced for opt-in wall-time walking. Development build; descriptive moving-run comparison, not a trajectory-matched causal experiment.'}};
  }
  const rechecks=rows.filter(row=>row.phase==='baseline-camera-recheck' && key(row)===key(requested)
    && row.packageReportSha256===BASELINE_PACKAGE_SHA256 && timingIssues(row).length===0
    && compareCamera(row,requested.selected,requested.motion).matched);
  if(rechecks.length>1)return {status:'ambiguous',selected:null,issues:['multiple-eligible-camera-rechecks']};
  if(rechecks.length===1)return {status:'eligible',selected:evidence(rechecks[0]),issues:[],replacement:'eligible original-package camera-matched recheck'};
  const candidates = rows.filter(row => row.phase === 'baseline' && session(row) === BASELINE_SESSION
    && row.packageReportSha256===BASELINE_PACKAGE_SHA256 && key(row) === key(requested));
  if (candidates.length !== 1) return {status:candidates.length ? 'ambiguous' : 'missing', selected:null, issues:['expected-one-original-baseline-row']};
  const issues = timingIssues(candidates[0]);
  return {status:issues.length ? 'observed-but-ineligible' : 'eligible', selected:evidence(candidates[0]), issues};
}

function deltaStats(before, after) {
  if (!validStats(before) || !validStats(after)) return null;
  return Object.fromEntries(stats.map(name => [name, after[name] - before[name]]));
}

function compare(rows, selected) {
  const baseline = selectBaseline(rows, selected), before = baseline.selected, after = selected.selected;
  const camera=compareCamera(before,after,selected.motion);
  const comparable = baseline.status === 'eligible' && selected.status === 'eligible'
    && JSON.stringify(before.pixels) === JSON.stringify(after.pixels) && camera.matched;
  return {key:selected.key, case:selected, baseline, camera,
    comparisonStatus:comparable ? 'eligible-before-after-with-stated-scope-limits' : 'qualified-observations-only-or-missing',
    delta:comparable ? {fps:after.fps-before.fps, meanFrameSpeedup:before.frame.meanMs/after.frame.meanMs,
      frameMs:deltaStats(before.frame, after.frame), gameThreadMs:deltaStats(before.gameThread, after.gameThread),
      renderThreadMs:deltaStats(before.renderThread, after.renderThread),
      gpuMs:before.gpu?.usable && after.gpu?.usable ? deltaStats(before.gpu.accepted, after.gpu.accepted) : null} : null};
}

function coverage(cases) {
  const counts = Object.fromEntries(['eligible','missing','ineligible','ambiguous'].map(status => [status,cases.filter(c => c.status === status).length]));
  return {required:cases.length, ...counts, complete:counts.eligible === cases.length,
    outstanding:cases.filter(c => c.status !== 'eligible').map(c => ({key:c.key,status:c.status,issues:c.issues}))};
}

function threshold(cases, minimumMeanFPS, maximumP99Ms = null) {
  const available = cases.filter(c => c.status === 'eligible');
  const failures = available.flatMap(c => {
    const issues = [];
    if (c.selected.fps < minimumMeanFPS) issues.push(`mean FPS below ${minimumMeanFPS}`);
    if (maximumP99Ms !== null && c.selected.frame.p99Ms >= maximumP99Ms) issues.push(`frame p99 not strictly below ${maximumP99Ms} ms`);
    return issues.length ? [{key:c.key, fps:c.selected.fps, p99Ms:c.selected.frame.p99Ms, issues}] : [];
  });
  const complete = available.length === cases.length;
  return {status:!complete ? 'pending' : failures.length ? 'failed' : 'passed', required:cases.length, eligible:available.length,
    minimumMeanFPS, maximumP99MsExclusive:maximumP99Ms,
    observedMinimumMeanFPS:available.length ? Math.min(...available.map(c => c.selected.fps)) : null,
    observedWorstP99Ms:available.length ? Math.max(...available.map(c => c.selected.frame.p99Ms)) : null,
    knownFailures:failures, outstanding:cases.filter(c => c.status !== 'eligible').map(c => c.key)};
}

export function assessMeasurements(input, generatedAt = new Date().toISOString(), requestedPlan) {
  if (!Array.isArray(input?.rows)) throw Error('measurements.json must contain rows');
  const plan = validateAcceptancePlan(requestedPlan);
  const expected = expectedCases(), main = expected.main.map(c => selectShipping(input.rows,c,plan)), software = expected.software.map(c => selectShipping(input.rows,c,plan));
  const mainCoverage = coverage(main), softwareCoverage = coverage(software);
  const requirements = {
    performanceRetina:threshold(main.filter(c => c.profile === 'performance' && c.output === 'retina'),60),
    balancedRetina:threshold(main.filter(c => c.profile === 'balanced' && c.output === 'retina'),30,33.3),
    softwareBalanced1080:threshold(software,30),
  };
  const allCases = [...main,...software], complete = mainCoverage.complete && softwareCoverage.complete;
  const failures = Object.values(requirements).flatMap(r => r.knownFailures);
  const performance = main.filter(c => c.profile === 'performance');
  return {schemaVersion:1, generatedAt, measurementsGeneratedAt:input.generatedAt ?? null,
    status:!complete ? 'pending' : failures.length ? 'failed' : 'passed',
    scope:'Saved-report acceptance for the pinned Shipping package; no native processes launched.',
    packageReportSha256:plan.packageReportSha256, originalBaselineSession:BASELINE_SESSION, originalFinalSession:plan.finalSession,
    plan:{...plan, sha256:sha(JSON.stringify(plan)), sha256Scope:'normalized-plan-json', source:requestedPlan === undefined ? 'pinned-defaults' : 'explicit-plan'},
    instrumentedWalkingBaselinePackageSha256:WALK_BASELINE_PACKAGE_SHA256,
    inputRows:input.rows.length, mainCoverage, softwareCoverage, requirements,
    performanceSoftwarePath:{required:performance.length, verified:performance.filter(c => c.status === 'eligible' && c.selected.hardwareLumen === 0).length,
      interpretation:'Performance itself selects software Lumen. The separate Balanced 1080p software study retains Balanced quality; neither is physical M1/M2 evidence.'},
    gpuTimingCoverage:{eligibleFPSCases:allCases.filter(c => c.status === 'eligible').length,
      usableGPUCases:allCases.filter(c => c.status === 'eligible' && c.selected.gpu?.usable).length,
      qualifiedCases:allCases.filter(c => c.status === 'eligible' && !c.selected.gpu?.usable).map(c => ({key:c.key, gpu:c.selected.gpu}))},
    selectionPolicy:{allowedReplacementPhases:['shipping-recheck-focus','shipping-recheck-gpu'],
      order:'Eligible focus recheck, then eligible GPU recheck, then original final. No ranking by FPS. Multiple eligible rows within the chosen phase are ambiguous.',
      softwareReplacementPhases:['shipping-recheck-gpu'],
      softwareOrder:'Eligible software=true GPU recheck, then the original shipping-software1080 case. No ranking by FPS; original rows are retained.',
      walkPhase:'shipping-walk', walkBaselinePhase:'baseline-walk', softwarePhase:'shipping-software1080',
      excluded:'Smoke, attribution, other baseline sessions, unrelated phases and different package hashes cannot satisfy a planned case.'},
    limitations:[
      'FPS is 1000 / mean wall-clock frame interval. Minimum FPS here is the minimum of per-run means across the required cases, not 1000 / maximum individual frame time.',
      'Performance Retina requires each of 10 cases >=60 mean FPS. Balanced Retina requires each of 10 cases >=30 mean FPS and p99 strictly <33.3ms. Both include two interior walks. All 60 main cases must be eligible, including Native and 4K cases without an imposed FPS target.',
      'The separate software study requires eight Balanced 1920x1080 static/orbit cases at >=30 mean FPS. It does not substitute for the main matrix or prove performance on physical M1/M2 hardware.',
      'GPU integrity and wall-frame FPS eligibility are separate. A GPU maximum longer than the entire measured wall-time window invalidates GPU aggregates only. Raw metrics are retained; invalid GPU means and deltas are never accepted.',
      'The GPU sanity check is necessary but not proof of timestamp accuracy; Unreal Insights trace GPU integrity findings remain a separate qualification.',
      'Original static/orbit baseline is exclusively baseline-1790193917881. Walking uses only the separately pinned baseline-walk package: original donor renderer and scene, plus four diagnostic/Pawn files for opt-in wall-time walking (see baseline-instrumentation.json). Ineligible baseline observations remain visible but cannot generate accepted before/after deltas.',
      'An eligible baseline-camera-recheck may replace only its matching case and must use the original package hash and match the static Shipping eye/forward pose. Static camera mismatches suppress comparison deltas without affecting Shipping FPS acceptance. Terminal moving-camera poses cannot certify a whole matching trajectory, so moving-run timing tables remain qualified observations.',
      'Baseline is Development and optimized is Shipping, with combined renderer and scene changes. Baseline static runs also request stat overlays and ProfileGPU. These are observed end-to-end comparisons, not isolated-cvar or configuration-equivalent causal experiments.',
      'Retina in this matrix is an observed 1920x1080 render target at a requested window size; it is not a guarantee for every display scale, larger window, or native 4K.',
      'The report assesses saved measurements only. Visual quality, grass popping, user preference persistence, walking geometry and package promotion require their separate evidence.',
    ],
    comparisons:main.map(c => compare(input.rows,c)), softwareCases:software};
}

const format = value => finite(value) ? value.toFixed(2) : '—';
const distribution = value => validStats(value) ? ['meanMs','p50Ms','p95Ms','p99Ms'].map(n => format(value[n])).join(' / ') : '—';
const link = value => value?.artifacts?.directory ? `[${value.phase}](<${value.artifacts.directory}>)` : '—';
export function acceptanceMarkdown(report) {
  const md = ['# BreziTwin — acceptance from saved native measurements','',`Status: **${report.status.toUpperCase()}**.`,
    `Pinned Shipping package: \`${report.packageReportSha256}\`.`,
    `Final session: \`${report.originalFinalSession}\`. Plan SHA256: \`${report.plan.sha256}\` (${report.plan.sha256Scope}).`,
    `Main cases: ${report.mainCoverage.eligible}/${report.mainCoverage.required} eligible. Separate software cases: ${report.softwareCoverage.eligible}/${report.softwareCoverage.required} eligible.`,
    '', '| Requirement | Status | Eligible / required | Minimum run-mean FPS | Worst frame p99 ms | Known misses |',
    '|---|---|---:|---:|---:|---:|',
    ...Object.entries(report.requirements).map(([name,r]) => `| ${name} | ${r.status} | ${r.eligible}/${r.required} | ${format(r.observedMinimumMeanFPS)} | ${format(r.observedWorstP99Ms)} | ${r.knownFailures.length} |`),
    '', `Usable GPU timing: ${report.gpuTimingCoverage.usableGPUCases}/${report.gpuTimingCoverage.eligibleFPSCases} eligible FPS cases. GPU timer failures do not invalidate otherwise eligible wall-frame FPS.`,
    '', '## Outstanding cases','',
    ...[...report.mainCoverage.outstanding,...report.softwareCoverage.outstanding].map(c => `- ${c.key}: ${c.status}${c.issues.length ? ` (${c.issues.join(', ')})` : ''}`)];
  if (!report.mainCoverage.outstanding.length && !report.softwareCoverage.outstanding.length) md.push('None.');
  const failed = Object.values(report.requirements).flatMap(r => r.knownFailures);
  if (failed.length) md.push('', '## Measured threshold misses','', ...failed.map(c => `- ${c.key}: ${c.issues.join('; ')} (${format(c.fps)} FPS, p99 ${format(c.p99Ms)} ms).`));
  md.push('', '## Main frame comparisons','', 'B = selected original baseline; A = accepted Shipping case. Distributions are mean / p50 / p95 / p99 in ms. Baseline rows marked ineligible are descriptive only; speedup is withheld.',
    '', '| Case | Baseline eligibility / camera | Shipping source / eligibility | FPS B → A | Frame B | Frame A | Mean frame speedup |',
    '|---|---|---|---:|---|---|---:|',
    ...report.comparisons.map(c => `| ${c.key} | ${c.baseline.status} / ${c.camera.status} | ${link(c.case.selected)} / ${c.case.status} | ${format(c.baseline.selected?.fps)} → ${format(c.case.selected?.fps)} | ${distribution(c.baseline.selected?.frame)} | ${distribution(c.case.selected?.frame)} | ${format(c.delta?.meanFrameSpeedup)} |`));
  for (const [title,field] of [['GPU','gpu'],['Game thread','gameThread'],['Render thread','renderThread']]) {
    const get = e => field === 'gpu' ? e?.gpu?.accepted : e?.[field];
    const render = e => field === 'gpu' && e && !e.gpu?.usable ? `unreliable/unavailable (${e.gpu?.status})` : distribution(get(e));
    md.push('', `## ${title} comparisons`, '', 'Mean / p50 / p95 / p99 ms; eligibility qualifications are in the frame table and JSON.', '',
      '| Case | Baseline | Shipping |', '|---|---|---|', ...report.comparisons.map(c => `| ${c.key} | ${render(c.baseline.selected)} | ${render(c.case.selected)} |`));
  }
  md.push('', '## Separate Balanced software Lumen study','', '| Case | Source / eligibility | FPS | Frame mean / p50 / p95 / p99 ms | GPU mean / p50 / p95 / p99 ms |',
    '|---|---|---:|---|---|', ...report.softwareCases.map(c => `| ${c.key} | ${link(c.selected)} / ${c.status} | ${format(c.selected?.fps)} | ${distribution(c.selected?.frame)} | ${c.selected?.gpu?.usable ? distribution(c.selected.gpu.accepted) : '—'} |`),
    '', '## Limits and interpretation','', ...report.limitations.map(s => `- ${s}`),'');
  return md.join('\n');
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const output = resolve(process.argv[2] ?? 'output/unreal/performance-20260923-r1');
  const planPath = process.argv[3] ? resolve(process.argv[3]) : null;
  const planBytes = planPath ? await readFile(planPath) : null;
  const plan = planBytes ? validateAcceptancePlan(JSON.parse(planBytes)) : undefined;
  const path = resolve(output,'measurements.json'), bytes = await readFile(path);
  const input=JSON.parse(bytes);
  // Small read-only sidecar reads supply camera evidence absent from measurements.json.
  await Promise.all(input.rows.filter(row=>row.motion==='static' && row.artifacts?.directory).map(async row=>{
    try {
      const raw=await readFile(resolve(row.artifacts.directory,'runtime.json'));
      if(createHash('sha256').update(raw).digest('hex')!==row.artifacts.runtimeSha256)throw Error('runtime-hash-mismatch');
      const runtime=JSON.parse(raw),camera=runtime.walking?.presentationCamera;
      row.camera={eyeCm:camera?.eyeCm,forward:camera?.forward,activeView:runtime.activeView,mode:runtime.walking?.cameraMode};
    }catch(error){row.camera={unavailable:String(error.message)};}
  }));
  const report = assessMeasurements(input, undefined, plan);
  if (planBytes) report.plan = {...report.plan, path:planPath, sha256:sha(planBytes), sha256Scope:'exact-input-file-bytes', source:'explicit-plan-file'};
  report.input = {path, sha256:sha(bytes)};
  await writeFile(resolve(output,'acceptance.json'),JSON.stringify(report,null,2)+'\n');
  await writeFile(resolve(output,'acceptance.md'),acceptanceMarkdown(report));
  console.log(JSON.stringify({status:report.status, mainCoverage:report.mainCoverage, softwareCoverage:report.softwareCoverage,
    report:resolve(output,'acceptance.md')}));
  // Pending is a valid analysis result. Consumers must inspect status, not command success.
}
