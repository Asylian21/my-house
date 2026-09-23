import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { mkdir, readFile, writeFile, readdir, realpath, stat } from 'node:fs/promises';
import { resolve, dirname, relative, isAbsolute } from 'node:path';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { verifyPackagedPayload } from './package-verify.mjs';
import { requireIdleApp, resolveAppLaunch, inspectLauncherExecution } from './app-launch.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const VIEWS = ['interior', 'street', 'terrace', 'pool', ...Array.from({ length: 12 }, (_, i) => `room-1-${String(i + 1).padStart(2, '0')}`), 'room-dressing'];
const MENU_SECTIONS = ['rooms', 'atmosphere', 'controls'];
const EXPERIMENTS = { 'vsync-off': 'r.VSync 0', 'software-lumen': 'r.Lumen.HardwareRayTracing 0',
  'clustered-lights': 'r.UseClusteredDeferredShading_ToBeRemoved 1',
  'local-shadows-high': 'r.Shadow.Virtual.SMRT.RayCountLocal 4',
  'lighting-high': 'sg.GlobalIlluminationQuality 2,sg.ShadowQuality 2,sg.ReflectionQuality 2' };
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const save = (path, value) => writeFile(path, JSON.stringify(value, null, 2) + '\n');
const inside = (directory, path) => {
  const rel = relative(directory, path);
  return rel !== '..' && !rel.startsWith('../') && !isAbsolute(rel);
};

function validateMenuSection(gameplayUi, menuSection) {
  assert(menuSection === null || MENU_SECTIONS.includes(menuSection), 'Unknown gameplay menu section');
  assert(menuSection === null || gameplayUi === 'pause', 'A menu section requires paused gameplay UI');
}

export function modelQaArguments(view, walk, sandbox, gameplayUi = null, night = false, profileGpu = false, experiment = null, menuSection = null) {
  assert(VIEWS.includes(view), 'Unknown model viewpoint');
  assert.equal(typeof walk, 'boolean');
  assert.equal(typeof night, 'boolean');
  assert.equal(typeof profileGpu, 'boolean');
  assert(experiment === null || Object.hasOwn(EXPERIMENTS, experiment), 'Unknown bounded renderer experiment');
  assert(isAbsolute(sandbox), 'Sandbox UserDir must be absolute');
  assert(gameplayUi === null || ['play', 'pause'].includes(gameplayUi), 'Invalid gameplay UI mode');
  assert(!gameplayUi || (view === 'interior' && !walk), 'Gameplay UI starts its own interior walk');
  validateMenuSection(gameplayUi, menuSection);
  return ['-windowed', '-ResX=1920', '-ResY=1080', `-UserDir=${sandbox}/`,
    `-abslog=${resolve(sandbox, 'runtime.log')}`, gameplayUi ? '-BreziOutput=4k' : '-BreziOutput=retina',
    // Diagnostic launches deliberately ignore saved/named profiles. Set their
    // explicit renderer inputs and verify the measured values in the report.
    '-ExecCmds=r.ScreenPercentage 50,r.TSR.History.ScreenPercentage 100' + (experiment ? ',' + EXPERIMENTS[experiment] : ''),
    `-BreziView=${view}`, gameplayUi ? '-BreziCaptureUI' : '-BreziCaptureScene', '-BreziWarmupFrames=240', '-BreziBenchmarkFrames=240',
    '-BreziExitAfterCapture', ...(night ? ['-BreziNight'] : []), ...(profileGpu ? ['-BreziProfileGPU'] : []),
    ...(menuSection ? [`-BreziMenuSection=${menuSection}`] : []),
    ...(gameplayUi ? [`-BreziGameplayUI=${gameplayUi}`] : ['-BreziWalkAudit', ...(walk ? ['-BreziWalk'] : [])])];
}

export function inspectModelQaCapture({ runtime, png, view, walk, gameplayUi = null, sourceManifestSha256, outcome, launchValidation }) {
  const errors = [], check = (condition, message) => { if (!condition) errors.push(message); };
  check(outcome.code === 0 && outcome.signal == null && !outcome.timedOut && !outcome.logTruncated && !outcome.error,
    'Native capture process did not exit cleanly');
  check(launchValidation?.status === 'recorded-self-exec-entry-chain' && launchValidation.errors.length === 0,
    'Current process PID/startup chain was not validated');
  const recordedAt = Date.parse(runtime?.recordedAtUtc);
  check(Number.isFinite(recordedAt) && recordedAt >= Date.parse(outcome.startedAt) - 1000
    && recordedAt <= Date.parse(outcome.endedAt) + 1000, 'Runtime report does not belong to this process interval');
  check(runtime?.status === 'capture-complete' && runtime.activeView === view && runtime.screenshotSaved === true,
    'Missing or incorrect completed runtime capture');
  check(runtime?.frameInterval?.sampleCount === 240 && runtime.warmupFrames === 240 && runtime.requestedBenchmarkFrames === 240,
    'Expected 240 warmup and 240 measured frames');
  check(runtime?.rhi === 'Metal', 'Native Metal rendering was not observed');
  check(runtime?.renderSettings?.['r.ScreenPercentage'] === 50
    && runtime?.renderSettings?.['r.TSR.History.ScreenPercentage'] === 100
    && runtime?.renderSettings?.['r.AntiAliasingMethod'] === 4, 'Measured renderer settings differ from the performance profile');
  const pixels = png?.length >= 24 && png.subarray(0, 8).toString('hex') === '89504e470d0a1a0a'
    && png.toString('ascii', 12, 16) === 'IHDR' ? [png.readUInt32BE(16), png.readUInt32BE(20)] : [];
  check(pixels.length === 2 && pixels.every(n => n > 0) && JSON.stringify(pixels) === JSON.stringify(runtime?.screenshotPixels)
    && (gameplayUi || JSON.stringify(pixels) === JSON.stringify(runtime?.requestedSceneCapturePixels)), 'PNG dimensions differ from the native capture');
  check(runtime?.screenshotKind === (gameplayUi ? 'fitted-slate-ui-capture-actual-window-pixels'
    : 'current-scene-render-target-preserving-view-history'), 'Unexpected capture mode');
  const walking = runtime?.walking ?? {};
  check(walking.contractLoaded === true && walking.worldContractValidated === true
    && Array.isArray(walking.worldContractErrors) && walking.worldContractErrors.length === 0
    && walking.sceneSha256 === sourceManifestSha256, 'Walking world does not match the packaged source model');
  if (walk || gameplayUi) {
    check(walking.cameraMode === 'walking' && walking.characterMovementMode === 'Walking'
      && walking.successfulEntries === 1 && walking.entryQueryStatus === 'entry-floor-and-capsule-queries-passed',
    'Requested walking entry did not remain in native walking mode');
  } else {
    check(walking.cameraMode === 'orbit' && walking.successfulEntries === 0 && walking.entryAttempts === 1,
      'Entry audit did not execute once without switching to walking');
  }
  if (gameplayUi) {
    check(walking.navigationActive === (gameplayUi === 'play'), 'Gameplay capture did not reach the requested play/pause state');
    check(runtime?.doors?.ready === true, 'Gameplay door system did not initialize');
  }
  return { status: errors.length ? 'failed' : 'standalone-capture-validated', errors, pixels,
    visualQualityAccepted: false, smoothnessAccepted: false, keyboardTraversalVerified: false };
}

async function executeCapture(launch, args, evidence) {
  const startedAt = new Date().toISOString();
  const chunks = [], stdout = [], stderr = [];
  let bytes = 0, timedOut = false, logTruncated = false, spawnError = null;
  const outcome = await new Promise(accept => {
    const child = spawn(launch.executable, args, { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'] });
    let forcedExit;
    const stop = () => { child.kill('SIGTERM'); forcedExit ??= setTimeout(() => child.kill('SIGKILL'), 10000); };
    const timeout = setTimeout(() => { timedOut = true; stop(); }, 600000);
    for (const [stream, destination] of [[child.stdout, stdout], [child.stderr, stderr]]) stream.on('data', chunk => {
      bytes += chunk.length;
      if (bytes <= 64 * 1024 * 1024) { chunks.push(chunk); destination.push(chunk); process.stdout.write(chunk); }
      else { logTruncated = true; stop(); }
    });
    child.once('error', error => { spawnError = error.message; });
    child.once('close', (code, signal) => {
      clearTimeout(timeout); clearTimeout(forcedExit);
      accept({ code, signal, pid: child.pid ?? null, startedAt, endedAt: new Date().toISOString(),
        timedOut, logTruncated, error: spawnError, executable: launch.executable, args, timeoutSeconds: 600 });
    });
  });
  const log = Buffer.concat(chunks);
  await Promise.all([writeFile(resolve(evidence, 'process.log'), log),
    writeFile(resolve(evidence, 'stdout.log'), Buffer.concat(stdout)), writeFile(resolve(evidence, 'stderr.log'), Buffer.concat(stderr))]);
  await save(resolve(evidence, 'process.json'), outcome);
  return { outcome, log };
}

export async function runModelQa(view = 'interior', walk = false, gameplayUi = null, night = false, profileGpu = false, experiment = null, menuSection = null) {
  assert(VIEWS.includes(view), 'Use a packaged named viewpoint, optionally followed by --walk');
  validateMenuSection(gameplayUi, menuSection);
  const output = resolve(ROOT, process.env.BREZI_MODEL_OUTPUT ?? 'output/unreal/model-refresh-20260922');
  const packagePath = resolve(output, 'model-package.json');
  const packageBytes = await readFile(packagePath), receipt = JSON.parse(packageBytes);
  assert.equal(receipt.status, 'current-model-packaged', 'Current model has no completed package');
  assert(receipt.viewpoints.includes(view), 'Selected package lacks this viewpoint');
  const before = await verifyPackagedPayload(receipt.appPath, receipt.bundle);
  const launch = await resolveAppLaunch(receipt.appPath, receipt.bundle);
  await requireIdleApp();
  const invocation = `${view}${experiment ? '-' + experiment : ''}${profileGpu ? '-gpu' : ''}${night ? '-night' : ''}${walk ? '-walk' : ''}${gameplayUi ? '-ui-' + gameplayUi : ''}${menuSection ? '-' + menuSection : ''}-${randomUUID()}`;
  const sandboxParent = resolve(homedir(), 'Library/Containers/local.brezi.twin/Data/Library/Application Support/BreziTwin/QA');
  const sandbox = resolve(sandboxParent, invocation), evidence = resolve(output, 'qa', invocation);
  await mkdir(sandboxParent, { recursive: true }); await mkdir(sandbox);
  await mkdir(dirname(evidence), { recursive: true }); await mkdir(evidence);
  const args = modelQaArguments(view, walk, sandbox, gameplayUi, night, profileGpu, experiment, menuSection);
  await writeFile(resolve(evidence, 'package.json'), packageBytes);
  const helperSha256 = sha(await readFile(fileURLToPath(import.meta.url)));
  await save(resolve(evidence, 'invocation.json'), { invocation, view, walk, gameplayUi, night, profileGpu, experiment, menuSection, sandbox, evidence, args, launch,
    packageReportSha256: sha(packageBytes), qaHelperSha256: helperSha256, startedAt: new Date().toISOString() });
  const { outcome, log } = await executeCapture(launch, args, evidence);
  let runtime = null, runtimeBytes = null, png = null, engineLog = null, after = null;
  const artifactErrors = [];
  try {
    engineLog = await readFile(resolve(sandbox, 'runtime.log'));
    await writeFile(resolve(evidence, 'runtime.log'), engineLog);
  } catch (error) { artifactErrors.push('Native log: ' + error.message); }
  const launchValidation = inspectLauncherExecution(launch, outcome, log.toString('utf8') + '\n' + (engineLog?.toString('utf8') ?? ''));
  await save(resolve(evidence, 'process.json'), { ...outcome, launch, launchValidation });
  try {
    const diagnostics = await realpath(resolve(sandbox, 'Saved/Diagnostics'));
    assert(inside(await realpath(sandbox), diagnostics), 'Diagnostics escaped this invocation');
    const reports = (await readdir(diagnostics)).filter(name => name.endsWith('.json'));
    assert.equal(reports.length, 1, 'Expected one report from this fresh runtime invocation');
    const runtimePath = await realpath(resolve(diagnostics, reports[0]));
    assert(inside(diagnostics, runtimePath), 'Runtime report escaped this invocation');
    runtimeBytes = await readFile(runtimePath); runtime = JSON.parse(runtimeBytes);
    await writeFile(resolve(evidence, 'runtime.json'), runtimeBytes);
    const screenshot = await realpath(runtime.screenshotPath);
    assert(inside(diagnostics, screenshot) && screenshot.endsWith('.png'), 'Screenshot escaped this invocation');
    for (const path of [runtimePath, screenshot]) {
      const modified = (await stat(path)).mtimeMs;
      assert(modified >= Date.parse(outcome.startedAt) - 1000 && modified <= Date.parse(outcome.endedAt) + 1000, 'Stale runtime artifact: ' + path);
    }
    png = await readFile(screenshot); await writeFile(resolve(evidence, 'capture.png'), png);
  } catch (error) { artifactErrors.push('Capture artifacts: ' + error.message); }
  try {
    after = await verifyPackagedPayload(receipt.appPath, receipt.bundle);
    assert.equal(sha(await readFile(packagePath)), sha(packageBytes), 'Package receipt changed during capture');
    assert.equal(sha(await readFile(fileURLToPath(import.meta.url))), helperSha256, 'QA helper changed during capture');
  } catch (error) { artifactErrors.push('Package/helper integrity: ' + error.message); }
  const validation = inspectModelQaCapture({ runtime, png, view, walk, gameplayUi, sourceManifestSha256: receipt.sourceManifestSha256, outcome, launchValidation });
  validation.errors.push(...artifactErrors);
  if (validation.errors.length) validation.status = 'failed';
  const report = { ...validation, generatedAt: new Date().toISOString(), view, walk, gameplayUi, night, profileGpu, experiment, menuSection, invocation,
    sandboxDirectory: sandbox, evidenceDirectory: evidence, packageReportSha256: sha(packageBytes), qaHelperSha256: helperSha256,
    sourceManifestSha256: receipt.sourceManifestSha256, sourceGlbSha256: receipt.sourceGlbSha256,
    process: outcome, launch, launchValidation, payloadBefore: before.status, payloadAfter: after?.status ?? 'failed',
    runtimeReportSha256: runtimeBytes ? sha(runtimeBytes) : null, screenshotSha256: png ? sha(png) : null,
    processLogSha256: sha(log), nativeLogSha256: engineLog ? sha(engineLog) : null,
    frameInterval: runtime?.frameInterval ?? null, walking: runtime?.walking ?? null, doors: runtime?.doors ?? null,
    measuredRenderSettings: runtime?.renderSettings ?? null,
    scope: 'Standalone native scene capture and source-world entry audit/standing observation. Visual quality, smoothness and user-driven traversal require separate review.' };
  await save(resolve(evidence, 'qa.json'), report);
  console.log(JSON.stringify({ status: report.status, reportPath: resolve(evidence, 'qa.json'),
    screenshotPath: png ? resolve(evidence, 'capture.png') : null, frameInterval: report.frameInterval, errors: report.errors }, null, 2));
  if (report.status === 'failed') process.exitCode = 1;
  return report;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [view = 'interior', flag, ...extra] = process.argv.slice(2);
  assert(extra.length === 0 && [undefined, '--walk', '--ui-play', '--ui-pause'].includes(flag),
    'Usage: model-refresh-qa.mjs [interior|street|terrace|pool] [--walk|--ui-play|--ui-pause]');
  await runModelQa(view, flag === '--walk', flag?.startsWith('--ui-') ? flag.slice(5) : null);
}
