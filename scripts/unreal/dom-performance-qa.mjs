// Native Shipping measurements of the installed, receipt-bound Dom application.
// Every run owns a fresh user directory. Original app/scene/evidence are read-only.
// The caller activates the emitted PID using the native UI while warmup runs.
import assert from 'node:assert/strict';
import { spawn, execFile } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { mkdir, readFile, readdir, copyFile, writeFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import { resolve, dirname, relative, isAbsolute } from 'node:path';
import { promisify } from 'node:util';
import { pathToFileURL } from 'node:url';
import { verifyPackagedPayload } from './package-verify.mjs';
import { resolveAppLaunch, requireIdleApp, inspectLauncherExecution } from './app-launch.mjs';
import { prepareRealtimeWalk } from './realtime-walk-contract.mjs';

const root = resolve(import.meta.dirname, '../..');
const exec = promisify(execFile);
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const save = (path, value) => writeFile(path, JSON.stringify(value, null, 2) + '\n');
const sleep = ms => new Promise(accept => setTimeout(accept, ms));
const safeName = value => typeof value === 'string' && /^[a-z0-9][a-z0-9-]*$/.test(value);

export function readConfiguration(environment = process.env) {
  const select = (name, fallback) => environment[name]?.split(',').map(v => v.trim()).filter(Boolean) ?? fallback;
  const config = {
    phase: environment.DOM_PERFORMANCE_PHASE ?? 'baseline',
    currentPath: resolve(root, environment.DOM_PERFORMANCE_CURRENT ?? 'output/unreal/dom-app-current.json'),
    output: resolve(root, environment.DOM_PERFORMANCE_OUTPUT ?? 'output/unreal/dom-performance'),
    scenes: select('DOM_PERFORMANCE_SCENES', ['exterior-neighborhood-ground-r38-day', 'street-day', 'interior-day', 'pool-day']),
    profiles: select('DOM_PERFORMANCE_PROFILES', environment.DOM_PERFORMANCE_CVARS_JSON ? ['full-study']
      : environment.DOM_PERFORMANCE_EXPECTED_CVARS_JSON ? ['full'] : ['cinematic', 'native', 'balanced', 'performance']),
    cvarsPath: environment.DOM_PERFORMANCE_CVARS_JSON ? resolve(root, environment.DOM_PERFORMANCE_CVARS_JSON) : null,
    expectedCvarsPath: environment.DOM_PERFORMANCE_EXPECTED_CVARS_JSON ? resolve(root, environment.DOM_PERFORMANCE_EXPECTED_CVARS_JSON) : null,
    geometryPath: environment.DOM_PERFORMANCE_GEOMETRY ? resolve(root, environment.DOM_PERFORMANCE_GEOMETRY) : null,
    outputs: select('DOM_PERFORMANCE_OUTPUTS', ['retina']),
    motions: select('DOM_PERFORMANCE_MOTIONS', ['static', 'orbit']),
    seconds: Number(environment.DOM_PERFORMANCE_SECONDS ?? 20),
    frames: Number(environment.DOM_PERFORMANCE_FRAMES ?? 300),
    warmupFrames: Number(environment.DOM_PERFORMANCE_WARMUP_FRAMES ?? 240),
    activationWaitMs: Number(environment.DOM_PERFORMANCE_ACTIVATION_WAIT_MS ?? 1200),
    timeoutMs: Number(environment.DOM_PERFORMANCE_TIMEOUT_MS ?? 300000),
    offscreen: environment.DOM_PERFORMANCE_OFFSCREEN === '1',
    softwareLumen: environment.DOM_PERFORMANCE_SOFTWARE_LUMEN === '1',
    stopOnFailure: environment.DOM_PERFORMANCE_STOP_ON_FAILURE !== '0',
    allowCandidate: environment.DOM_PERFORMANCE_ALLOW_CANDIDATE === '1',
    allowPendingInstalled: environment.DOM_PERFORMANCE_ALLOW_PENDING_INSTALLED === '1',
  };
  assert(safeName(config.phase), 'Phase must be a safe directory component');
  for (const values of [config.scenes, config.profiles, config.outputs, config.motions]) {
    assert(values.length > 0 && new Set(values).size === values.length, 'Selections must be nonempty and unique');
  }
  assert(config.scenes.every(s => /^([a-z0-9][a-z0-9-]*)-(day|night)$/.test(s)), 'Scene must be a viewpoint followed by -day or -night');
  assert(config.profiles.every(p => ['cinematic', 'native', 'balanced', 'performance', 'full', 'full-study'].includes(p)), 'Unsupported render profile');
  assert(config.cvarsPath ? config.profiles.length === 1 && config.profiles[0] === 'full-study' : !config.profiles.includes('full-study'),
    'A complete sandbox cvar recipe requires only the full-study label; full-study requires DOM_PERFORMANCE_CVARS_JSON');
  assert(!config.cvarsPath || !config.expectedCvarsPath, 'Choose an applied study recipe or a named expected recipe, not both');
  assert(!config.expectedCvarsPath || config.profiles.length === 1, 'One expected recipe validates exactly one named profile');
  assert(!config.profiles.includes('full') || config.expectedCvarsPath, 'Named Full requires a complete DOM_PERFORMANCE_EXPECTED_CVARS_JSON runtime contract');
  assert(config.outputs.every(p => ['retina', '4k'].includes(p)), 'Unsupported output mode');
  assert(config.motions.every(p => ['static', 'orbit', 'walk'].includes(p)), 'Supported motions are static, orbit and walk');
  assert(!config.motions.includes('walk') || config.geometryPath, 'Realtime walk requires DOM_PERFORMANCE_GEOMETRY with exact scene/walking/hidden-collision inputs');
  assert(!config.motions.includes('walk') || config.scenes.every(scene => /^interior-(day|night)$/.test(scene)), 'Realtime walk starts only at interior-day/night');
  assert(Number.isFinite(config.seconds) && config.seconds >= 10 && config.seconds <= 120, 'Realtime duration must be 10–120 seconds');
  for (const name of ['frames', 'warmupFrames'])
    assert(Number.isInteger(config[name]) && config[name] >= 240 && config[name] <= 36000, name + ' must be 240–36000');
  assert(Number.isInteger(config.activationWaitMs) && config.activationWaitMs >= 0 && config.activationWaitMs <= 60000, 'Activation handoff wait must be 0–60000ms');
  assert(Number.isInteger(config.timeoutMs) && config.timeoutMs >= 30000 && config.timeoutMs <= 900000, 'Process timeout must be 30000–900000ms');
  return config;
}

export function assessTiming(runtime, { offscreen, motion }) {
  const frame = runtime.frameInterval, focus = runtime.focusDuringBenchmark;
  assert(frame?.status === 'measured' && Number.isInteger(frame.sampleCount) && frame.sampleCount >= 240, 'Missing >=240 measured wall-time frames');
  for (const field of ['meanMs', 'p95Ms', 'p99Ms', 'maxMs'])
    assert(Number.isFinite(frame[field]) && frame[field] > 0, 'Invalid frame ' + field);
  assert(frame.p95Ms <= frame.p99Ms && frame.p99Ms <= frame.maxMs, 'Frame percentiles are out of order');
  const focused = focus?.sampleCount === frame.sampleCount
    && focus.applicationForegroundSamples === frame.sampleCount
    && focus.gameWindowActiveSamples === frame.sampleCount
    && focus.applicationForegroundThroughoutBenchmark === true;
  if (motion === 'orbit') {
    assert(runtime.realtimeOrbit?.measurementCompleted === true, 'Orbit measurement did not complete');
    assert(runtime.realtimeOrbit.engineClockModifiedByStudy === false, 'Study modified the engine clock');
    assert(runtime.realtimeOrbit.movingCameraSamples > 0 && runtime.realtimeOrbit.cameraTravelCm > 0, 'Orbit had no actual camera movement');
  } else if (motion === 'walk') {
    const movement = runtime.realtimeWalk, walking = runtime.walking;
    assert(!runtime.realtimeOrbit, 'Walk unexpectedly used an orbit camera');
    assert.equal(movement?.measurementCompleted, true, 'Realtime walk measurement did not complete');
    assert.equal(movement.nativeRoutePreflightPassed, true, 'Native walk floor/sweep route preflight failed');
    assert.equal(movement.engineClockModifiedByStudy, false, 'Walk study modified the engine clock');
    assert.equal(movement.teleportsDuringMeasurement, false, 'Walk used teleports during measurement');
    assert.equal(movement.failure, '', 'Native walk reported a failure');
    assert(movement.roundTrips >= 1 && movement.reachedWaypoints >= 4, 'Walk did not complete an actual source-aisle roundtrip');
    assert(movement.movingCameraSamples > 0 && movement.pathDistanceCm > 0, 'Walk had no actual camera movement');
    assert.equal(walking?.cameraMode, 'walking');
    assert(walking.groundedEyeSamples > 0, 'Walk had no measured grounded eye samples');
    assert.equal(walking.unmeasuredOrAirborneEyeSamples, 0, 'Walk camera eye was airborne or unmeasured');
    assert(Number.isFinite(walking.maxEyeHeightErrorCm) && walking.maxEyeHeightErrorCm <= .2, 'Walk grounded eye-height error exceeds 0.2cm');
  } else assert(!runtime.realtimeOrbit && !runtime.realtimeWalk, 'Static run unexpectedly moved the camera');
  const gpu = runtime.gpuFrameFromRHITimer;
  const gpuUnreliable = gpu?.status === 'measured'
    && (!Number.isFinite(gpu.meanMs) || gpu.meanMs <= 0 || gpu.maxMs > frame.meanMs * frame.sampleCount);
  return { fps: 1000 / frame.meanMs, sampledWallSeconds: frame.meanMs * frame.sampleCount / 1000,
    focused, eligibleForPerformanceAcceptance: !offscreen && focused,
    evidenceTier: offscreen ? 'offscreen-native-diagnostic-only' : focused ? 'focused-native-onscreen-wall-time' : 'rejected-unfocused-native-onscreen',
    gpuIntegrity: gpuUnreliable ? 'unreliable-timestamp-outlier' : gpu?.status ?? 'unavailable',
    limitations: [
      ...(offscreen ? ['offscreen-diagnostic-does-not-prove-interactive-fps'] : !focused ? ['foreground-or-game-window-not-active-throughout'] : []),
      ...(gpuUnreliable ? ['gpu-timestamp-outlier-raw-values-retained'] : []),
      'wall-time-engine-ticks-do-not-measure-display-presentation-or-visual-occlusion',
      'gpu-and-cpu-distributions-are-not-paired-per-frame',
      ...(motion === 'walk' ? ['source-living-kitchen-aisle-walk-does-not-prove-whole-house-or-os-keyboard-navigation'] : []),
    ] };
}

function buildArguments(config, row, sandbox) {
  const args = ['-windowed', '-ResX=1920', '-ResY=1080', '-nosplash',
    `-UserDir=${sandbox}/`, `-abslog=${sandbox}/runtime.log`,
    `-BreziOutput=${row.mode}`, `-BreziView=${row.view}`,
    '-BreziCaptureScene', '-BreziExitAfterCapture', '-BreziBenchmarkUncapped', '-BreziWalkAudit',
    `-BreziWarmupFrames=${config.warmupFrames}`, `-BreziBenchmarkFrames=${config.frames}`];
  // Diagnostics without a named profile preserve the complete sandbox Engine.ini
  // recipe. A named recipe would overwrite these values with GameOverride priority.
  if (!config.cvarsPath) args.push(`-BreziRenderProfile=${row.profile}`);
  if (row.night) args.push('-BreziNight');
  if (row.motion === 'orbit') args.push('-BreziRealtimeOrbit', `-BreziBenchmarkSeconds=${config.seconds}`);
  if (row.motion === 'walk') args.push('-BreziRealtimeWalk', `-BreziRealtimeWalkRoute=${row.walkRoutePath}`, `-BreziBenchmarkSeconds=${config.seconds}`);
  if (config.offscreen) args.push('-RenderOffScreen', '-unattended');
  if (config.softwareLumen) args.push('-BreziSoftwareLumen');
  return args;
}

export function validateStudyRecipe(value) {
  const cvars = value?.cvars ?? value;
  assert(cvars && typeof cvars === 'object' && !Array.isArray(cvars), 'Study JSON must be a numeric cvar object, or {cvars: {...}}');
  const required = ['sg.GlobalIlluminationQuality', 'sg.ShadowQuality', 'sg.ReflectionQuality', 'sg.FoliageQuality',
    'sg.PostProcessQuality', 'sg.EffectsQuality', 'r.ScreenPercentage', 'r.TSR.History.ScreenPercentage',
    'r.ScreenPercentage.MaxResolution', 'r.Brezi.OutputLines', 'r.Lumen.Reflections.DownsampleFactor',
    'r.Shadow.Virtual.ResolutionLodBiasLocal', 'r.Brezi.Lumen.FinalGatherQuality', 'r.Brezi.Lumen.ReflectionQuality',
    'r.Brezi.Lumen.SceneLightingQuality', 'r.Brezi.Lumen.SceneDetail', 'r.Brezi.Lumen.SceneViewDistance',
    'r.Brezi.Lumen.MaxTraceDistance', 'r.Brezi.DoubleGlass', 'r.Brezi.LocalLightShadows', 'r.Brezi.DetailLighting',
    'foliage.DensityScale', 'r.AntiAliasingMethod', 'r.DynamicRes.OperationMode', 'r.SecondaryScreenPercentage.GameViewport'];
  for (const name of required) assert(Object.hasOwn(cvars, name), 'Complete study recipe is missing ' + name);
  for (const [name, number] of Object.entries(cvars))
    assert(/^[A-Za-z][A-Za-z0-9_.]*$/.test(name) && typeof number === 'number' && Number.isFinite(number), 'Unsafe or non-numeric cvar: ' + name);
  assert.equal(cvars['r.AntiAliasingMethod'], 4, 'Study must preserve the supported TSR pipeline');
  assert.equal(cvars['r.DynamicRes.OperationMode'], 0, 'Study must use a stable resolution');
  assert.equal(cvars['r.SecondaryScreenPercentage.GameViewport'], 100, 'Study must preserve the output scaling contract');
  // Scalability setters run callbacks which can write direct budgets. Apply all
  // sg.* values first, then the precise renderer and density readbacks, matching
  // the native VisitSettings recipe order rather than letting sg.* erase them.
  return Object.fromEntries(Object.entries(cvars).sort(([a], [b]) =>
    Number(!a.startsWith('sg.')) - Number(!b.startsWith('sg.')) || a.localeCompare(b)));
}

export function assertRecipeReadback(runtime, recipe, { softwareLumen = false } = {}) {
  for (const [name, requested] of Object.entries(recipe)) {
    assert(Object.hasOwn(runtime.renderSettings, name), 'No native runtime readback for expected cvar ' + name);
    const actual = runtime.renderSettings[name];
    const expected = name === 'r.VSync' || name === 't.MaxFPS' ? 0
      : softwareLumen && name === 'r.Lumen.HardwareRayTracing' ? 0 : requested;
    assert(Number.isFinite(actual) && Math.abs(actual - expected) <= 1e-4 * Math.max(1, Math.abs(expected)),
      `Recipe cvar ${name} expected ${expected}, runtime ${actual}`);
  }
  // Verify the composed view too: numeric cvar readback alone does not establish
  // that an imported unbound volume failed to override the actual Lumen budget.
  for (const [name, field] of [
    ['FinalGatherQuality', 'lumenFinalGatherQuality'], ['ReflectionQuality', 'lumenReflectionQuality'],
    ['SceneLightingQuality', 'lumenSceneLightingQuality'], ['SceneDetail', 'lumenSceneDetail'],
    ['SceneViewDistance', 'lumenSceneViewDistance'], ['MaxTraceDistance', 'lumenMaxTraceDistance'],
  ]) {
    const requested = recipe['r.Brezi.Lumen.' + name];
    if (requested >= 0) {
      const actual = runtime.finalViewPostProcessSettings?.[field];
      assert(Number.isFinite(actual) && Math.abs(actual - requested) <= 1e-4 * Math.max(1, Math.abs(requested)),
        `Composed view ${field} expected ${requested}, runtime ${actual}`);
    }
  }
}

export function assertFullSceneReadback(runtime) {
  assert.equal(runtime.renderSettings['foliage.DensityScale'], 1, 'Full must retain every vegetation instance');
  assert.equal(runtime.renderSettings['sg.FoliageQuality'], 3, 'Full must retain highest foliage quality');
  assert.equal(runtime.renderSettings['r.Brezi.DoubleGlass'], 1, 'Full must retain double-glass rendering');
  assert.equal(runtime.renderSettings['r.Brezi.LocalLightShadows'], 1, 'Full must retain authored local-light shadows');
  assert.equal(runtime.doubleGlass?.length, 19, 'Expected every source double-glass panel');
  assert(runtime.doubleGlass.every(panel => panel.configured && panel.enabled && panel.ior === 1.52), 'Full double-glass panel readback differs');
  const details = runtime.detailLightingState;
  assert(Array.isArray(details) && details.length > 0, 'Missing native vegetation lighting readback');
  const enabled = runtime.renderSettings['r.Brezi.DetailLighting'] !== 0;
  for (const detail of details) {
    assert(detail.managedDetail && detail.authoredFlagsCaptured && detail.instanceCount > 0, 'Vegetation detail binding or instances missing');
    assert.equal(detail.qualityEnabled, enabled, 'Native detail lighting policy did not apply');
    for (const [field, authored] of [['castShadow', 'authoredCastShadow'], ['visibleInRayTracing', 'authoredVisibleInRayTracing'], ['affectDistanceFieldLighting', 'authoredAffectDistanceFieldLighting']])
      assert.equal(detail[field], enabled || detail[authored], `Vegetation ${field} did not restore authored flags`);
  }
}

async function verifyWalkInputs(config, facts) {
  if (!config.motions.includes('walk')) return null;
  const expected = { 'scene.json': facts.sourceSceneSha256, 'walking.json': facts.sourceWalkingSha256,
    'hidden-collision.json': facts.sourceHiddenCollisionSha256 };
  const actual = {};
  for (const [name, digest] of Object.entries(expected)) {
    actual[name] = sha(await readFile(resolve(config.geometryPath, name)));
    assert.equal(actual[name], digest, 'Realtime source input differs from the exact packaged scene: ' + name);
  }
  return { directory: config.geometryPath, inputHashes: actual };
}

async function verifyInstalled(config, expected = null) {
  const currentBytes = await readFile(config.currentPath), installed = JSON.parse(currentBytes);
  const candidate = installed.status === 'dom-candidate-pending-native-validation';
  const pendingInstalled = installed.status === 'dom-installed-awaiting-native-verification';
  assert(installed.status === 'dom-installed-native-visually-verified' || (config.allowCandidate && candidate)
    || (config.allowPendingInstalled && pendingInstalled),
    'Unverified targets require an explicit candidate or pending-installation QA flag');
  if (pendingInstalled) assert.equal(installed.appPath, '/Applications/Dom.app',
    'Pending installation QA is restricted to the actual Dom installation');
  if (candidate) {
    const candidateRelative = relative(resolve(root, 'output/unreal'), resolve(installed.appPath));
    assert(candidateRelative && !candidateRelative.startsWith('..') && !isAbsolute(candidateRelative),
      'Candidate app must be a workspace Unreal output');
  }
  const packageBytes = await readFile(installed.packageReceiptPath), packaged = JSON.parse(packageBytes);
  assert.equal(sha(packageBytes), installed.packageReceiptSha256, 'Installed package receipt changed');
  assert.equal(packaged.status, 'dom-final-exterior-standalone-package-validated');
  assert.equal(packaged.gameConfiguration, 'Shipping');
  assert.equal(installed.activeDesign, 'C/B/B'); assert.equal(packaged.activeDesign, 'C/B/B');
  assert.equal(installed.streetAndRightSetbackMm, 3000); assert.equal(packaged.streetAndRightSetbackMm, 3000);
  const map = packaged.selection.launchMap;
  assert.equal(map.sha256, installed.sourceMapSha256, 'Installed source-map binding differs');
  const acceptedBytes = await readFile(resolve(root, 'output/unreal/exterior-final-current.json'));
  const accepted = JSON.parse(acceptedBytes);
  assert.equal(accepted.status, 'final-saved-editor-exterior-user-accepted');
  assert.equal(accepted.activeDesign, 'C/B/B');
  assert.equal(accepted.streetAndRightSetbackMm, 3000);
  const mapSha256 = sha(await readFile(accepted.launchMap.path));
  assert.equal(mapSha256, map.sha256, 'Accepted source map changed since packaging');
  assert.equal(accepted.launchMap.sha256, mapSha256, 'Installed package is not the current accepted final map');
  const payload = await verifyPackagedPayload(installed.appPath, packaged.bundle);
  await exec('/usr/bin/codesign', ['--verify', '--deep', '--strict', installed.appPath]);
  const launch = await resolveAppLaunch(installed.appPath);
  // The installed path differs from the archive path; every semantic/hash field must match.
  const { executable: ignoredArchivePath, ...archivedLaunch } = packaged.bundle.launch;
  const { executable: ignoredInstalledPath, ...installedLaunch } = launch;
  assert.deepEqual(installedLaunch, archivedLaunch, 'Installed entry differs from the validated archive');
  const project = packaged.project;
  const viewpointsBytes = await readFile(resolve(project, 'Content/Data/viewpoints.json'));
  const walkingBytes = await readFile(resolve(project, 'Content/Data/walking.json'));
  const hiddenBytes = await readFile(resolve(project, 'Content/Data/hidden-collision.json'));
  const viewpoints = JSON.parse(viewpointsBytes), walking = JSON.parse(walkingBytes);
  const facts = { currentReceiptPath: config.currentPath, currentReceiptSha256: sha(currentBytes),
    packageReceiptPath: installed.packageReceiptPath, packageReceiptSha256: sha(packageBytes),
    acceptedSelectionSha256: sha(acceptedBytes), sourceMapPath: accepted.launchMap.path,
    archivedSourceMapPath: map.path, sourceMapSha256: mapSha256,
    sourceViewpointsSha256: sha(viewpointsBytes), sourceWalkingSha256: sha(walkingBytes), sourceHiddenCollisionSha256: sha(hiddenBytes),
    sourceSceneSha256: walking.provenance.sceneSha256, appPath: installed.appPath,
    installedPayloadSha256: sha(JSON.stringify(payload.payloadHashes)), fileCount: payload.fileCount,
    installedPayloadStatus: payload.status, codeSignature: 'deep-strict-valid',
    executableSha256: launch.executableSha256,
    targetKind: candidate ? 'unpromoted-candidate' : pendingInstalled ? 'pending-installed' : 'installed' };
  if (expected) assert.deepEqual(facts, expected, 'Receipt, source-map or installed payload changed during measurement');
  return { facts, launch, viewpoints: viewpoints.viewpoints ?? viewpoints.views ?? [], walking };
}

async function runChild(launch, args, config, row) {
  await requireIdleApp();
  const chunks = [];
  const child = spawn(launch.executable, args, { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] });
  const completed = new Promise((accept, reject) => {
    let timedOut = false;
    const timeout = setTimeout(() => { timedOut = true; child.kill('SIGTERM'); }, config.timeoutMs);
    let killTimer;
    for (const stream of [child.stdout, child.stderr]) stream.on('data', bytes => chunks.push(bytes));
    child.once('error', error => { clearTimeout(timeout); clearTimeout(killTimer); reject(error); });
    child.once('close', (code, signal) => { clearTimeout(timeout); clearTimeout(killTimer); accept({ code, signal, pid: child.pid, timedOut }); });
    child.once('spawn', () => {
      console.log(JSON.stringify({ event: 'native-pid-activate-during-warmup', id: row.id, pid: child.pid,
        appPath: launch.executable, evidence: row.evidence, warmupFrames: config.warmupFrames,
        activationWaitMs: config.activationWaitMs, offscreen: config.offscreen }));
    });
    // A TERM-resistant process cannot leave the next launch overlapping it.
    killTimer = setTimeout(() => child.kill('SIGKILL'), config.timeoutMs + 10000);
  });
  if (!config.offscreen && config.activationWaitMs) await sleep(config.activationWaitMs);
  const outcome = await completed;
  await writeFile(resolve(row.evidence, 'process.log'), Buffer.concat(chunks));
  return { outcome, processLog: Buffer.concat(chunks) };
}

export async function runSuite(config = readConfiguration()) {
  const initial = await verifyInstalled(config);
  if (process.argv.includes('--verify-only')) { console.log(JSON.stringify(initial.facts, null, 2)); return; }
  const recipeBytes = config.cvarsPath ? await readFile(config.cvarsPath) : null;
  const recipe = recipeBytes ? validateStudyRecipe(JSON.parse(recipeBytes)) : null;
  const recipeBinding = recipeBytes ? { path: config.cvarsPath, sha256: sha(recipeBytes), cvars: recipe,
    method: 'Complete numeric recipe in fresh Saved/Config/Mac/Engine.ini; no named profile/ExecCmds argument; actual runtime readback verified.' } : null;
  const expectedRecipeBytes = config.expectedCvarsPath ? await readFile(config.expectedCvarsPath) : null;
  const expectedRecipe = expectedRecipeBytes ? validateStudyRecipe(JSON.parse(expectedRecipeBytes)) : null;
  const expectedRecipeBinding = expectedRecipeBytes ? { path: config.expectedCvarsPath, sha256: sha(expectedRecipeBytes), cvars: expectedRecipe,
    method: 'Assertion-only complete recipe; native named profile remains in argv; sandbox Engine.ini is not populated by this expected contract.' } : null;
  const walkInputBinding = await verifyWalkInputs(config, initial.facts);
  const session = resolve(config.output, `${config.phase}-${Date.now()}-${randomUUID()}`);
  await mkdir(session, { recursive: true });
  const results = [];
  await save(resolve(session, 'binding-before.json'), initial.facts);
  if (recipeBytes) await writeFile(resolve(session, 'study-recipe-input.json'), recipeBytes);
  if (expectedRecipeBytes) await writeFile(resolve(session, 'expected-recipe-input.json'), expectedRecipeBytes);
  const viewpointIds = new Set(initial.viewpoints.map(v => v.id));
  for (const scene of config.scenes) assert(viewpointIds.has(/^(.+)-(day|night)$/.exec(scene)[1]), 'Unknown source-packaged viewpoint: ' + scene);
  let after;
  try {
    suite: for (const scene of config.scenes) for (const profile of config.profiles) for (const mode of config.outputs) for (const motion of config.motions) {
      const [, view, time] = /^(.+)-(day|night)$/.exec(scene);
      const id = `${scene}-${mode}-${profile}-${motion}-${randomUUID()}`;
      const evidence = resolve(session, id);
      await mkdir(evidence);
      const sandbox = resolve(homedir(), 'Library/Containers/local.brezi.twin/Data/Library/Application Support/BreziTwin/QA', 'dom-performance-' + id);
      await mkdir(sandbox, { recursive: false });
      if (recipe) {
        const configDirectory = resolve(sandbox, 'Saved/Config/Mac');
        await mkdir(configDirectory, { recursive: true });
        const ini = ['[ConsoleVariables]', ...Object.entries(recipe).map(([name, value]) => `${name}=${value}`), ''].join('\n');
        await writeFile(resolve(configDirectory, 'Engine.ini'), ini);
        await writeFile(resolve(evidence, 'requested-Engine.ini'), ini);
      }
      const row = { id, phase: config.phase, scene, view, night: time === 'night', profile, mode, motion,
        offscreen: config.offscreen, softwareLumen: config.softwareLumen, evidence, sandbox,
        studyRecipe: recipeBinding, expectedRecipe: expectedRecipeBinding, walkSource: walkInputBinding,
        ...initial.facts, startedAt: new Date().toISOString() };
      if (motion === 'walk') {
        row.walkRoutePath = resolve(sandbox, 'walk-route.json');
        row.walkRoute = await prepareRealtimeWalk(config.geometryPath, row.walkRoutePath);
        assert.deepEqual(row.walkRoute.inputHashes, walkInputBinding.inputHashes, 'Walk planner read changed source input bytes');
        const routeBytes = await readFile(row.walkRoutePath);
        row.walkRouteSha256 = sha(routeBytes);
        await writeFile(resolve(evidence, 'walk-route.json'), routeBytes);
      }
      row.args = buildArguments(config, row, sandbox);
      await save(resolve(evidence, 'launch.json'), row);
      console.log(JSON.stringify({ event: 'start', id, session, evidence, args: row.args }));
      try {
        const { outcome, processLog } = await runChild(initial.launch, row.args, config, row);
        row.outcome = outcome;
        const log = await readFile(resolve(sandbox, 'runtime.log')).catch(error => { if (error.code === 'ENOENT') return Buffer.from(''); throw error; });
        await writeFile(resolve(evidence, 'runtime.log'), log);
        row.entry = inspectLauncherExecution(initial.launch, outcome, String(processLog) + '\n' + log);
        const diagnostics = resolve(sandbox, 'Saved/Diagnostics'), files = await readdir(diagnostics);
        const reports = files.filter(p => p.endsWith('.json')); assert.equal(reports.length, 1, 'Expected exactly one fresh native report');
        const originalReport = resolve(diagnostics, reports[0]), raw = await readFile(originalReport), runtime = JSON.parse(raw);
        await writeFile(resolve(evidence, 'runtime.json'), raw);
        assert.equal(runtime.status, 'capture-complete'); assert.equal(runtime.rhi, 'Metal');
        assert.equal(runtime.warmupFrames, config.warmupFrames, 'Native warmup request changed');
        if (motion === 'static') assert.equal(runtime.requestedBenchmarkFrames, config.frames, 'Native static frame request changed');
        else {
          const movement = motion === 'walk' ? runtime.realtimeWalk : runtime.realtimeOrbit;
          assert.equal(movement?.requestedSeconds, config.seconds, 'Native realtime duration request changed');
          assert(movement?.elapsedWallSeconds >= config.seconds, 'Native motion stopped before requested wall duration');
        }
        assert.equal(runtime.buildConfiguration, 'Shipping'); assert.equal(runtime.processId, outcome.pid);
        assert.equal(outcome.code, 0); assert.equal(outcome.signal, null); assert.equal(outcome.timedOut, false);
        assert(row.entry.errors.every(error => error === 'Engine initialization after app entry was not observed'), 'Native entry/PID proof failed');
        assert.equal(runtime.activeView, view); assert.equal(runtime.screenshotSaved, true);
        assert.deepEqual(runtime.screenshotPixels, mode === '4k' ? [3840, 2160] : [1920, 1080]);
        assert.equal(runtime.walking.worldContractValidated, true); assert.deepEqual(runtime.walking.worldContractErrors, []);
        assert.equal(runtime.walking.sceneSha256, initial.facts.sourceSceneSha256);
        assert.equal(runtime.renderSettings['r.VSync'], 0); assert.equal(runtime.renderSettings['t.MaxFPS'], 0);
        if (config.softwareLumen) assert.equal(runtime.renderSettings['r.Lumen.HardwareRayTracing'], 0);
        if (recipe) assertRecipeReadback(runtime, recipe, config);
        if (expectedRecipe) assertRecipeReadback(runtime, expectedRecipe, config);
        if (profile === 'full') assertFullSceneReadback(runtime);
        if (motion === 'walk') {
          assert.equal(runtime.realtimeWalk?.sceneSha256, initial.facts.sourceSceneSha256);
          assert.equal(runtime.realtimeWalk?.routePath, row.walkRoutePath);
          assert.equal(sha(await readFile(row.walkRoutePath)), row.walkRouteSha256, 'Native walk route changed during measurement');
        }
        const imageRelative = relative(sandbox, resolve(runtime.screenshotPath));
        assert(imageRelative && !imageRelative.startsWith('..') && !isAbsolute(imageRelative), 'Capture escaped the fresh user directory');
        const capture = await readFile(runtime.screenshotPath);
        assert(capture.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])), 'Capture is not PNG');
        assert.deepEqual([capture.readUInt32BE(16), capture.readUInt32BE(20)], runtime.screenshotPixels, 'Actual PNG dimensions differ');
        await writeFile(resolve(evidence, 'capture.png'), capture);
        for (const file of files.filter(p => p.endsWith('.log'))) await copyFile(resolve(diagnostics, file), resolve(evidence, file));
        Object.assign(row, assessTiming(runtime, row), {
          originalReport, originalCapture: runtime.screenshotPath, runtimeReportSha256: sha(raw), screenshotSha256: sha(capture),
          pixels: runtime.screenshotPixels, frame: runtime.frameInterval, gpu: runtime.gpuFrameFromRHITimer,
          cpu: runtime.cpuGameThreadActive, render: runtime.cpuRenderThreadActive, foreground: runtime.focusDuringBenchmark,
          frameBudget: runtime.frameBudget, settings: runtime.renderSettings, postprocess: runtime.finalViewPostProcessSettings,
          movement: runtime.realtimeOrbit ?? runtime.realtimeWalk ?? null, walking: runtime.walking,
          detailLightingState: runtime.detailLightingState,
          glass: runtime.doubleGlass, timingMethod: runtime.timingMethod,
        });
        if (!config.offscreen) assert.equal(row.focused, true, 'Rejected performance result: app and game window were not active throughout native measurement');
        row.status = config.offscreen ? 'diagnostic-measured' : 'measured';
      } catch (error) { row.status = 'failed'; row.error = String(error.stack ?? error); }
      row.endedAt = new Date().toISOString();
      await save(resolve(evidence, 'qa.json'), row); results.push(row);
      await save(resolve(session, 'summary.json'), { schemaVersion: 1, status: 'running', session, config, studyRecipe: recipeBinding,
        expectedRecipe: expectedRecipeBinding, walkSource: walkInputBinding, binding: initial.facts, results });
      console.log(JSON.stringify({ event: 'end', id, status: row.status, evidenceTier: row.evidenceTier,
        fps: row.fps, frame: row.frame, gpu: row.gpu, cpu: row.cpu, render: row.render, foreground: row.foreground, error: row.error }));
      if (row.status === 'failed' && config.stopOnFailure) break suite;
    }
  } finally {
    try {
      after = (await verifyInstalled(config, initial.facts)).facts;
      if (recipeBinding) assert.equal(sha(await readFile(config.cvarsPath)), recipeBinding.sha256, 'Input study recipe changed during suite');
      if (expectedRecipeBinding) assert.equal(sha(await readFile(config.expectedCvarsPath)), expectedRecipeBinding.sha256, 'Expected named recipe changed during suite');
      if (walkInputBinding) assert.deepEqual(await verifyWalkInputs(config, initial.facts), walkInputBinding, 'Walk source inputs changed during suite');
      await save(resolve(session, 'binding-after.json'), after);
    }
    catch (error) { after = { status: 'binding-verification-failed', error: String(error.stack ?? error) }; }
    const expectedRuns = config.scenes.length * config.profiles.length * config.outputs.length * config.motions.length;
    const failed = results.filter(row => row.status === 'failed').length;
    const status = failed || after.status === 'binding-verification-failed' || results.length !== expectedRuns ? 'completed-with-failures' : 'suite-complete';
    await save(resolve(session, 'summary.json'), { schemaVersion: 1, status, completedAt: new Date().toISOString(), session,
      expectedRuns, completedRuns: results.length, failedRuns: failed, config, studyRecipe: recipeBinding,
      expectedRecipe: expectedRecipeBinding, walkSource: walkInputBinding, bindingBefore: initial.facts, bindingAfter: after, results });
    const number = value => Number.isFinite(value) ? value.toFixed(2) : '—';
    await writeFile(resolve(session, 'measurements.md'), ['# Installed Dom native performance', '',
      'Actual uncapped Shipping Metal wall-time frame intervals. Only focused onscreen runs are eligible for interactive performance comparison; offscreen runs are diagnostic evidence. GPU/CPU counters are independent distributions. Static duration follows frame count; orbit/walk use ordinary wall time. Walk covers the validated living/kitchen source aisle using actual CharacterMovement and collision; whole-house or OS keyboard navigation is not established.', '',
      '| Scene | Profile | Output | Motion | Evidence | FPS | Frame mean / P95 / P99 ms | GPU mean ms | Game / render CPU mean ms | Frames |',
      '|---|---|---|---|---|---:|---|---:|---|---:|',
      ...results.map(row => `| ${row.scene} | ${row.profile} | ${row.mode} | ${row.motion} | ${row.evidenceTier ?? row.status} | ${number(row.fps)} | ${number(row.frame?.meanMs)} / ${number(row.frame?.p95Ms)} / ${number(row.frame?.p99Ms)} | ${row.gpuIntegrity === 'unreliable-timestamp-outlier' ? 'unreliable' : number(row.gpu?.meanMs)} | ${number(row.cpu?.meanMs)} / ${number(row.render?.meanMs)} | ${row.frame?.sampleCount ?? 0} |`), '',
      'All raw native JSON, screenshots, launch argv and logs are preserved per run. Before/after source-map, receipt, installed payload hashes and code-signature checks bind the session.', '',
    ].join('\n'));
    console.log(JSON.stringify({ event: 'suite-end', status, session, expectedRuns, completedRuns: results.length, failedRuns: failed, bindingAfter: after }));
    if (status !== 'suite-complete') process.exitCode = 1;
  }
  return { session, results, bindingAfter: after };
}

function selfTest() {
  const frame = { status: 'measured', sampleCount: 300, meanMs: 16, p95Ms: 19, p99Ms: 21, maxMs: 24 };
  const runtime = { frameInterval: frame, gpuFrameFromRHITimer: { status: 'measured', meanMs: 12, maxMs: 19 },
    focusDuringBenchmark: { sampleCount: 300, applicationForegroundSamples: 300, gameWindowActiveSamples: 300, applicationForegroundThroughoutBenchmark: true } };
  assert.equal(assessTiming(runtime, { offscreen: false, motion: 'static' }).eligibleForPerformanceAcceptance, true);
  assert.equal(assessTiming({ ...runtime, focusDuringBenchmark: { ...runtime.focusDuringBenchmark, gameWindowActiveSamples: 299 } }, { offscreen: false, motion: 'static' }).evidenceTier, 'rejected-unfocused-native-onscreen');
  assert.equal(assessTiming(runtime, { offscreen: true, motion: 'static' }).eligibleForPerformanceAcceptance, false);
  assert.equal(assessTiming({ ...runtime, gpuFrameFromRHITimer: { status: 'measured', meanMs: 12, maxMs: 5000 } }, { offscreen: false, motion: 'static' }).gpuIntegrity, 'unreliable-timestamp-outlier');
  assert.throws(() => assessTiming({ ...runtime, frameInterval: { ...frame, sampleCount: 239 } }, { offscreen: false, motion: 'static' }));
  assert.throws(() => assessTiming(runtime, { offscreen: false, motion: 'orbit' }));
  assert.throws(() => readConfiguration({ DOM_PERFORMANCE_PROFILES: 'typo' }));
  assert.throws(() => readConfiguration({ DOM_PERFORMANCE_PHASE: '../baseline' }));
  const config = readConfiguration({ DOM_PERFORMANCE_OFFSCREEN: '1', DOM_PERFORMANCE_MOTIONS: 'orbit' });
  const args = buildArguments(config, { mode: 'retina', view: 'interior', profile: 'native', motion: 'orbit', night: false }, '/fresh-userdir');
  assert(args.includes('-BreziBenchmarkUncapped') && args.includes('-BreziRealtimeOrbit') && args.includes('-RenderOffScreen'));
  assert(!args.some(argument => argument.startsWith('-ExecCmds')));
  const studyConfig = readConfiguration({ DOM_PERFORMANCE_CVARS_JSON: '/example/recipe.json' });
  assert.deepEqual(studyConfig.profiles, ['full-study']);
  assert(!buildArguments(studyConfig, { mode: 'retina', view: 'interior', profile: 'full-study', motion: 'static' }, '/fresh-userdir').some(argument => argument.startsWith('-BreziRenderProfile')));
  assert.throws(() => validateStudyRecipe({ 'r.ScreenPercentage': 100 }));
  assert.throws(() => readConfiguration({ DOM_PERFORMANCE_PROFILES: 'full-study' }));
  assert.throws(() => readConfiguration({ DOM_PERFORMANCE_PROFILES: 'full' }));
  const fullConfig = readConfiguration({ DOM_PERFORMANCE_EXPECTED_CVARS_JSON: '/example/expected.json' });
  assert.deepEqual(fullConfig.profiles, ['full']);
  assert(buildArguments(fullConfig, { mode: 'retina', view: 'interior', profile: 'full', motion: 'static' }, '/fresh-userdir').includes('-BreziRenderProfile=full'));
  assert.throws(() => readConfiguration({ DOM_PERFORMANCE_CVARS_JSON: '/example/applied.json', DOM_PERFORMANCE_EXPECTED_CVARS_JSON: '/example/expected.json' }));
  assert.throws(() => readConfiguration({ DOM_PERFORMANCE_MOTIONS: 'walk', DOM_PERFORMANCE_SCENES: 'interior-day' }));
  assert.throws(() => readConfiguration({ DOM_PERFORMANCE_MOTIONS: 'walk', DOM_PERFORMANCE_GEOMETRY: '/example/geometry', DOM_PERFORMANCE_SCENES: 'street-day' }));
  const walkConfig = readConfiguration({ DOM_PERFORMANCE_MOTIONS: 'walk', DOM_PERFORMANCE_GEOMETRY: '/example/geometry',
    DOM_PERFORMANCE_SCENES: 'interior-day,interior-night', DOM_PERFORMANCE_SECONDS: '45' });
  const walkArgs = buildArguments(walkConfig, { mode: 'retina', view: 'interior', profile: 'native', motion: 'walk', walkRoutePath: '/fresh-userdir/walk-route.json' }, '/fresh-userdir');
  assert(walkArgs.includes('-BreziRealtimeWalk') && walkArgs.includes('-BreziRealtimeWalkRoute=/fresh-userdir/walk-route.json')
    && walkArgs.includes('-BreziBenchmarkSeconds=45') && !walkArgs.includes('-BreziRealtimeOrbit'));
  const walkRuntime = { ...runtime, realtimeWalk: { measurementCompleted: true, nativeRoutePreflightPassed: true,
    engineClockModifiedByStudy: false, teleportsDuringMeasurement: false, failure: '', roundTrips: 2, reachedWaypoints: 8,
    movingCameraSamples: 290, pathDistanceCm: 1900 }, walking: { cameraMode: 'walking', groundedEyeSamples: 300,
    unmeasuredOrAirborneEyeSamples: 0, maxEyeHeightErrorCm: .1 } };
  assert.equal(assessTiming(walkRuntime, { offscreen: false, motion: 'walk' }).eligibleForPerformanceAcceptance, true);
  assert.throws(() => assessTiming({ ...walkRuntime, realtimeWalk: { ...walkRuntime.realtimeWalk, teleportsDuringMeasurement: true } }, { offscreen: false, motion: 'walk' }));
  assert.throws(() => assessTiming({ ...walkRuntime, walking: { ...walkRuntime.walking, maxEyeHeightErrorCm: .3 } }, { offscreen: false, motion: 'walk' }));
  const recipe = { 'r.ScreenPercentage': 67, 'r.Brezi.Lumen.FinalGatherQuality': 1 };
  const recipeRuntime = { renderSettings: { ...recipe }, finalViewPostProcessSettings: { lumenFinalGatherQuality: 1 } };
  assertRecipeReadback(recipeRuntime, recipe);
  assert.throws(() => assertRecipeReadback({ ...recipeRuntime, renderSettings: { ...recipe, 'r.ScreenPercentage': 100 } }, recipe));
  assert.throws(() => assertRecipeReadback({ ...recipeRuntime, finalViewPostProcessSettings: { lumenFinalGatherQuality: .5 } }, recipe));
  const fullRuntime = { renderSettings: { 'foliage.DensityScale': 1, 'sg.FoliageQuality': 3, 'r.Brezi.DoubleGlass': 1,
    'r.Brezi.LocalLightShadows': 1, 'r.Brezi.DetailLighting': 0 },
    doubleGlass: Array.from({ length: 19 }, () => ({ configured: true, enabled: true, ior: 1.52 })),
    detailLightingState: [{ managedDetail: true, authoredFlagsCaptured: true, instanceCount: 300, qualityEnabled: false,
      castShadow: false, authoredCastShadow: false, visibleInRayTracing: true, authoredVisibleInRayTracing: true,
      affectDistanceFieldLighting: false, authoredAffectDistanceFieldLighting: false }] };
  assertFullSceneReadback(fullRuntime);
  assert.throws(() => assertFullSceneReadback({ ...fullRuntime, renderSettings: { ...fullRuntime.renderSettings, 'foliage.DensityScale': .65 } }));
  assert.throws(() => assertFullSceneReadback({ ...fullRuntime, detailLightingState: [{ ...fullRuntime.detailLightingState[0], visibleInRayTracing: false }] }));
  console.log('30 native timing/configuration/Full/walk contract checks passed; no application launched.');
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  if (process.argv.includes('--self-test')) selfTest();
  else await runSuite();
}
