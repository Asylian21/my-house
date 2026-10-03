// Uncooked Editor-game appearance pilot. This never creates a package receipt.
import fs from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawn, execFile } from 'node:child_process';
import { promisify, parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import {loadEditorSourceEvidence,validateProjectClosure} from './megaplants-english-oak-editor-source-r1.mjs';

const root = fileURLToPath(new URL('../../', import.meta.url));
const wrapper = fileURLToPath(import.meta.url);
const sourceGuard = fileURLToPath(new URL('./megaplants-english-oak-editor-source-r1.mjs', import.meta.url));
const engine = '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor';
const engineModules = '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.modules';
const approvedEditorModuleSha256 = '2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const exec = promisify(execFile);
const scope = 'Actual isolated original English Oak USD Editor-game Development shape/constant-material pilot; no walking, package or full-realism acceptance.';
const deniedClaims = Object.freeze({ shippingVerified: false, packageVerified: false,
  nativeAppearanceAccepted: false, performanceAccepted: false, fullPhotorealismAccepted: false });
const shaBytes = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const isWithin = (parent, child) => child === parent || child.startsWith(parent + path.sep);
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const save = (file, value) => fs.writeFile(file, JSON.stringify(value, null, 2) + '\n', { flag: 'w' });

const { values, positionals } = parseArgs({ options: {
  source: { type: 'string' }, 'validation-output': { type: 'string' },
  label: { type: 'string' }, views: { type: 'string' }, help: { type: 'boolean' },
}, allowPositionals: false });
if (values.help) {
  console.log('Usage: node scripts/unreal/megaplants-english-oak-editor-qa-r1.mjs --source <candidate> --validation-output <validation-base> --label <unique-label> --views <id,id>');
  process.exit(0);
}
assert.equal(positionals.length, 0);
for (const key of ['source', 'validation-output', 'label', 'views']) assert(values[key], `Missing --${key}`);
assert(/^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$/.test(values.label), 'Label must be a short filename-safe label');
const views = values.views.split(',');
assert(views.length > 0 && views.length === new Set(views).size &&
  views.every(v => /^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$/.test(v)), 'Views must be distinct actual viewpoint IDs');
const source = path.resolve(root, values.source);
const output = path.resolve(root, values['validation-output']);
assert(!isWithin(source, output), 'Pilot evidence must be outside the source candidate');
const qa = path.join(output, 'qa');
await fs.mkdir(qa, { recursive: true });
const suiteDirectory = await fs.mkdtemp(path.join(qa, `editor-pilot-${values.label}-${Date.now()}-`));
const suiteFile = path.join(suiteDirectory, 'editor-pilot-suite.json');
const suite = { schemaVersion: 1, owner: 'scripts/unreal/megaplants-english-oak-editor-qa-r1.mjs', scope,
  status: 'preflight', source, validationOutput: output, suiteDirectory, label: values.label,
  requestedViews: views, requestedBuild: 'Development', requestedTransport: 'UnrealEditor -game',
  requestedProfile: 'cinematic', requestedOutput: 'retina', warmupFrames: 2400,
  benchmarkFrames: 300, deadlineMsPerCase: 600000, startedAt: new Date().toISOString(),
  ...deniedClaims, cases: [], errors: [] };
await save(suiteFile, suite);
console.log(JSON.stringify({ event: 'editor-pilot-created', suiteDirectory, suiteFile, scope }));

async function filesBelow(directory) {
  const rows = [];
  for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name);
    assert(!entry.isSymbolicLink(), `Unmeasured symbolic input: ${file}`);
    if (entry.isDirectory()) rows.push(...await filesBelow(file));
    else if (entry.isFile()) rows.push(file);
  }
  return rows.sort();
}
async function hashFile(file) {
  const before = await fs.stat(file);
  assert(before.isFile(), `Not a regular input: ${file}`);
  const hash = crypto.createHash('sha256');
  for await (const bytes of createReadStream(file)) hash.update(bytes);
  const after = await fs.stat(file);
  assert(before.dev === after.dev && before.ino === after.ino && before.size === after.size &&
    before.mtimeMs === after.mtimeMs, `Input changed while hashing: ${file}`);
  return { sha256: hash.digest('hex'), bytes: after.size };
}
async function hashFiles(files) {
  const records = new Map(); let cursor = 0;
  await Promise.all(Array.from({ length: Math.min(4, files.length) }, async () => {
    while (cursor < files.length) { const file = files[cursor++]; records.set(file, await hashFile(file)); }
  }));
  return Object.fromEntries([...records].sort(([a], [b]) => a.localeCompare(b)));
}
async function nativeIdle() {
  const { stdout } = await exec('ps', ['-axo', 'pid=,comm='], { maxBuffer: 4 * 1024 * 1024 });
  const active = stdout.split('\n').flatMap(line => {
    const match = /^\s*(\d+)\s+(.+)$/.exec(line);
    return match && /^(BreziTwin|BreziStartupLauncher|UnrealEditor(?:-Cmd)?|ShaderCompileWorker)$/.test(path.basename(match[2].trim()))
      ? [{ pid: Number(match[1]), command: match[2].trim() }] : [];
  });
  assert.equal(active.length, 0, `Native renderer/compiler already active: ${JSON.stringify(active)}`);
  return { observedAt: new Date().toISOString(), activeNativeProcesses: active };
}

let project, descriptor, importReportPath, importReport, cloneReceiptPath, sourceFilesBefore, closureBefore, cameraData, sourceEvidence;
const closureFiles = async () => [...new Set([
  ...await filesBelow(path.join(project, 'Content')), ...await filesBelow(path.join(project, 'Config')),
  ...await filesBelow(path.join(project, 'Source')), descriptor, importReportPath,
  ...(sourceEvidence?.projectProof ? await filesBelow(path.join(project, 'Binaries')) : []),
  cloneReceiptPath, path.join(project, 'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),
  path.join(project, 'Binaries/Mac/UnrealEditor.modules'), engine, engineModules, wrapper, sourceGuard,
  ...(sourceEvidence?.additionalClosureFiles ?? []),
  ...Object.keys(sourceEvidence?.projectProof ?? {}).map(relative => path.join(project, relative)),
].filter(Boolean))].sort();

async function preflight() {
  suite.nativeIdleBefore = await nativeIdle();
  sourceEvidence = await loadEditorSourceEvidence(source, {root});
  importReportPath = sourceEvidence.nativeReceiptPath; importReport = sourceEvidence.base;
  project = sourceEvidence.project;
  assert.equal(views.length, 1); assert.deepEqual(views, sourceEvidence.allowedViews);
  suite.probeMap = sourceEvidence.map; suite.walkingAuditRequested = false;
  descriptor = path.join(project, 'BreziTwin.uproject');
  const projectDefinition = JSON.parse(await fs.readFile(descriptor, 'utf8'));
  assert.equal(projectDefinition.EngineAssociation, '5.8');
  assert(projectDefinition.Modules?.some(m => m.Name === 'BreziTwin' && m.Type === 'Runtime'));
  const module = path.join(project, 'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');
  const moduleBytes = await fs.readFile(module);
  let clone, moduleWitness;
  if (sourceEvidence.nativeModuleWitness) {
    moduleWitness = sourceEvidence.nativeModuleWitness;
  } else {
    const approvedCloneReceipts = [
      ['protected-storage-clone-receipt.json', 'verified-byte-identical-independent-apfs-clones-protected-own-data-after-native'],
      ['storage-clone-receipt.json', 'verified-byte-identical-independent-apfs-clones-before-native'],
    ];
    for (const [filename, status] of approvedCloneReceipts) {
      const file = path.join(source, filename);
      try {
        const actual = JSON.parse(await fs.readFile(file, 'utf8'));
        assert.equal(actual.status, status, `Clone receipt has an unapproved filename/status pair: ${file}`);
        clone = actual; cloneReceiptPath = file; break;
      } catch (error) { if (error.code !== 'ENOENT') throw error; }
    }
    assert(clone && Array.isArray(clone.files), 'An actual typed source-owned module clone receipt is required');
    moduleWitness = clone.files.find(row => row.destination === module);
    assert(moduleWitness, 'Missing source-owned copied Editor-module witness');
  }
  assert.equal(moduleWitness.independentInodes, true);
  assert.equal(moduleWitness.bytes, moduleBytes.length);
  assert.equal(shaBytes(moduleBytes), moduleWitness.sha256, 'Copied Editor module differs from its actual witness');
  assert.equal(moduleWitness.sha256, approvedEditorModuleSha256, 'Editor module is not the reviewed recorder implementation');
  for (const marker of ['BreziCaptureScene', 'BreziExitAfterCapture', 'BreziBenchmarkFrames=', 'BreziWarmupFrames=',
    'BreziView=', 'BreziOutput=', 'BreziRenderProfile=', 'cinematic', 'r.Brezi.DetailLighting',
    'current-scene-render-target-preserving-view-history', 'finalViewPostProcessSettings', 'capture-complete'])
    assert(moduleBytes.includes(Buffer.from(marker, 'utf16le')), `Recorder marker absent from actual Editor module: ${marker}`);
  const nativeModuleMap = JSON.parse(await fs.readFile(path.join(project, 'Binaries/Mac/UnrealEditor.modules'), 'utf8'));
  const engineModuleMap = JSON.parse(await fs.readFile(engineModules, 'utf8'));
  assert.equal(nativeModuleMap.Modules.BreziTwin, path.basename(module));
  assert(nativeModuleMap.BuildId && nativeModuleMap.BuildId === engineModuleMap.BuildId, 'Project/engine Editor BuildId differs');
  const engineStat = await fs.lstat(engine);
  assert(engineStat.isFile() && !engineStat.isSymbolicLink() && (engineStat.mode & 0o111), 'Actual executable Editor is required');
  const config = await fs.readFile(path.join(project, 'Config/DefaultEngine.ini'), 'utf8');
  for (const required of ['GameEngine=/Script/BreziTwin.BreziGameEngine',
    'GameViewportClientClassName=/Script/BreziTwin.BreziGameViewportClient',
    'GlobalDefaultGameMode=/Script/BreziTwin.BreziGameMode']) assert(config.includes(required), `Missing game configuration: ${required}`);
  cameraData = JSON.parse(await fs.readFile(path.join(project, 'Content/Data/viewpoints.json'), 'utf8'));
  assert.equal(cameraData.coordinateSystem, 'unreal-centimeters');
  assert(Array.isArray(cameraData.views) && new Set(cameraData.views.map(v => v.id)).size === cameraData.views.length);
  for (const id of views) {
    const camera = cameraData.views.find(v => v.id === id);
    assert(camera, `Unknown saved native viewpoint: ${id}`);
    for (const key of ['eyeCm', 'targetCm']) assert(Array.isArray(camera[key]) && camera[key].length === 3 && camera[key].every(Number.isFinite));
    assert(Math.hypot(...camera.eyeCm.map((v, i) => v - camera.targetCm[i])) > .1);
    assert(Number.isFinite(camera.horizontalFovDegrees) && camera.horizontalFovDegrees >= 15 && camera.horizontalFovDegrees <= 120);
  }
  sourceFilesBefore = await closureFiles(); closureBefore = await hashFiles(sourceFilesBefore);
  validateProjectClosure({project, contentInventory: sourceEvidence.contentInventory,
    projectProof: sourceEvidence.projectProof, closure: closureBefore});
  assert(closureBefore[path.join(project, sourceEvidence.map.replace('/Game/', 'Content/') + '.umap')], 'Actual separate probe map is missing');
  assert(closureBefore[path.join(project, 'Content/Brezi/Maps/Brezi.umap')], 'Protected main map is missing');
  const beforeFile = path.join(suiteDirectory, 'inputs-before.json'); await save(beforeFile, closureBefore);
  suite.inputClosureBefore = { path: beforeFile, ...await hashFile(beforeFile), fileCount: sourceFilesBefore.length,
    logicalBytes: Object.values(closureBefore).reduce((sum, row) => sum + row.bytes, 0),
    scope: 'Own candidate Content/Config/Source, descriptor, actual selected native receipts, reviewed Editor module/maps/executable and the closed separate Oak source guards. Typed modes also pin their consumed source witnesses and original Config/Source/Binaries proof; each typed adapter pins the source closure declared by its known native receipt.' };
  suite.nativeAssetWitnessCount = Object.keys(sourceEvidence.contentInventory).length;
  suite.nativeSourceEvidence = {mode: sourceEvidence.mode,
    nativeReceipt: {path: importReportPath, ...closureBefore[importReportPath]},
    ...(sourceEvidence.receiptSummary ?? (sourceEvidence.overlay ? {
      baseNativeReport: sourceEvidence.overlay.baseNativeReport,
      selectedPlan: sourceEvidence.overlay.selectedPlan, overlaySummary: sourceEvidence.summary,
      materialPackagesIndependentlyReloaded: false, savedMapUnloadedReloaded: true} : {}))};
  suite.engine = { executable: engine, ...closureBefore[engine], engineBuildId: engineModuleMap.BuildId,
    module, moduleSha256: closureBefore[module].sha256, moduleWitness, projectBuildId: nativeModuleMap.BuildId,
    ...(clone ? {actualCloneReceipt: {path: cloneReceiptPath, status: clone.status, ...closureBefore[cloneReceiptPath]}}
      : {actualOverlayModuleWitness: moduleWitness, moduleWitnessSource: sourceEvidence.moduleWitnessSource ?? sourceEvidence.overlay.selectedPlan}) }; 
  suite.selectedSourceCameras = views.map(id => cameraData.views.find(v => v.id === id));
  suite.status = 'running'; await save(suiteFile, suite);
}

let ownChild = null;
const stopOwnChild = signal => { if (ownChild && ownChild.exitCode === null && ownChild.signalCode === null) ownChild.kill(signal); };
let interruption = null, interruptForce;
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => {
  interruption = signal; stopOwnChild('SIGTERM');
  if (ownChild && !interruptForce) interruptForce = setTimeout(() => stopOwnChild('SIGKILL'), 10000);
});

async function launchCase(row, args) {
  const stdout = await fs.open(row.stdoutPath, 'wx');
  let deadline, force;
  try {
    const outcome = await new Promise((accept, reject) => {
      ownChild = spawn(engine, args, { cwd: root, stdio: ['ignore', stdout.fd, stdout.fd] });
      row.processId = ownChild.pid; row.status = 'running';
      console.log(JSON.stringify({ event: 'editor-pilot-running', view: row.view, pid: ownChild.pid,
        processReceiptPath: row.processReceiptPath }));
      const persisted = save(row.processReceiptPath, row);
      deadline = setTimeout(() => {
        row.deadlineExceeded = true; stopOwnChild('SIGTERM');
        force = setTimeout(() => stopOwnChild('SIGKILL'), 10000);
      }, suite.deadlineMsPerCase);
      ownChild.once('error', error => persisted.then(() => reject(error), reject));
      ownChild.once('close', (code, signal) => persisted.then(() => accept({ code, signal, pid: row.processId }), reject));
    });
    return outcome;
  } finally {
    clearTimeout(deadline); clearTimeout(force); clearTimeout(interruptForce);
    interruptForce = null; ownChild = null; await stdout.close();
  }
}
function verifyRuntime(r, row, png) {
  assert.equal(r.status, 'capture-complete'); assert.equal(r.processId, row.processId);
  assert.equal(r.buildConfiguration, 'Development'); assert.equal(r.rhi, 'Metal');
  assert.equal(r.shaderPlatform, 'METAL_SM6'); assert.equal(r.activeView, row.view);
  assert.equal(r.lighting, 'imported-daylight'); assert.equal(r.warmupFrames, 2400);
  assert.equal(r.requestedBenchmarkFrames, 300); assert.equal(r.frameInterval?.sampleCount, 300);
  assert.equal(r.screenshotSaved, true); assert.deepEqual(r.screenshotPixels, [1920, 1080]);
  assert.deepEqual(png, [1920, 1080]);
  assert.equal(r.screenshotKind, 'current-scene-render-target-preserving-view-history');
  assert.equal(r.presentation?.initialized, true); assert.equal(r.presentation.outputMode, 'retina');
  assert.equal(r.presentation.outputSelectionValid, true); assert.equal(r.presentation.targetMatchesOutputContract, true);
  assert.equal(r.separateSceneRenderTargetThroughoutBenchmark, true); assert.equal(r.sceneTargetMatchesViewportThroughoutBenchmark, true);
  const expected = { 'r.ScreenPercentage': 100, 'r.TSR.History.ScreenPercentage': 200,
    'r.AntiAliasingMethod': 4, 'r.DynamicRes.OperationMode': 0, 'r.SecondaryScreenPercentage.GameViewport': 100,
    'r.ScreenPercentage.MaxResolution': 1080, 'r.Brezi.OutputLines': 0, 'foliage.DensityScale': 1,
    'sg.GlobalIlluminationQuality': 3, 'sg.ShadowQuality': 3, 'sg.ReflectionQuality': 3,
    'sg.FoliageQuality': 3, 'sg.PostProcessQuality': 3, 'sg.EffectsQuality': 3,
    'r.Brezi.DetailLighting': 1, 'r.Brezi.LocalLightShadows': 1, 'r.Lumen.Reflections.DownsampleFactor': 1 };
  for (const [name, value] of Object.entries(expected)) assert.equal(r.renderSettings?.[name], value, `Runtime profile differs: ${name}`);
  const pp = r.finalViewPostProcessSettings, rt = pp?.renderThreadAntiAliasing;
  assert.equal(pp?.status, 'observed-composed-main-view'); assert.equal(pp.dynamicGlobalIlluminationMethod, 1);
  assert.equal(pp.reflectionMethod, 1); assert.equal(pp.lumenFinalGatherQuality, 1);
  assert.equal(pp.lumenReflectionQuality, 2); assert.equal(pp.lumenSceneLightingQuality, 2);
  assert.equal(pp.unscaledViewWidth, 1920); assert.equal(pp.unscaledViewHeight, 1080);
  assert.equal(rt?.status, 'observed-render-thread-main-view'); assert.equal(rt.antiAliasingMethodName, 'TSR');
  assert.equal(rt.familyRenderTargetWidth, 1920); assert.equal(rt.familyRenderTargetHeight, 1080);
  assert.equal(r.walking?.worldContractValidated, false); assert.deepEqual(r.walking.worldContractErrors, []);
  row.walkingCollisionAcceptanceAvailable = false;
  const camera = r.walking.presentationCamera;
  assert.equal(r.walking.cameraMode, 'orbit');
  assert(Array.isArray(camera?.eyeCm) && camera.eyeCm.length === 3 && camera.eyeCm.every(Number.isFinite));
  assert(Math.hypot(...camera.eyeCm.map((v, i) => v - row.sourceCamera.eyeCm[i])) <= .5, 'Actual camera eye differs from saved viewpoint');
  const delta = row.sourceCamera.targetCm.map((v, i) => v - row.sourceCamera.eyeCm[i]);
  const distance = Math.hypot(...delta); const expectedForward = delta.map(v => v / distance);
  assert(Array.isArray(camera.forward) && camera.forward.length === 3 && camera.forward.every(Number.isFinite));
  assert(Math.hypot(...camera.forward.map((v, i) => v - expectedForward[i])) <= .001, 'Actual camera direction differs from saved viewpoint');
}

async function runCase(view) {
  const caseDirectory = await fs.mkdtemp(path.join(suiteDirectory, `${view}-`));
  const userDirectory = path.join(caseDirectory, 'userdir'); await fs.mkdir(userDirectory);
  const row = { schemaVersion: 1, scope, ...deniedClaims, view, caseDirectory, userDirectory,
    sourceCamera: cameraData.views.find(v => v.id === view), sourceFovNativeReadbackAvailable: false,
    nativeEvidenceValidated: false,
    processReceiptPath: path.join(caseDirectory, 'process.json'), stdoutPath: path.join(caseDirectory, 'stdout.log'),
    runtimeLogPath: path.join(caseDirectory, 'runtime.log'), status: 'starting', startedAt: new Date().toISOString() };
  suite.cases.push(row); await save(suiteFile, suite);
  const args = [descriptor, sourceEvidence.map, '-game', '-windowed', '-ResX=1920', '-ResY=1080',
    '-BreziOutput=retina', `-BreziView=${view}`, '-BreziRenderProfile=cinematic', '-BreziCaptureScene',
    '-BreziExitAfterCapture', '-BreziWarmupFrames=2400', '-BreziBenchmarkFrames=300', '-BreziBenchmarkUncapped',
    '-unattended', '-nosplash', `-UserDir=${userDirectory}/`, `-abslog=${row.runtimeLogPath}`];
  row.argv = [engine, ...args];
  try {
    row.nativeIdleBefore = await nativeIdle(); await save(row.processReceiptPath, row);
    console.log(JSON.stringify({ event: 'editor-pilot-start', view, caseDirectory, processReceiptPath: row.processReceiptPath }));
    row.outcome = await launchCase(row, args); row.endedAt = new Date().toISOString();
    assert.equal(row.outcome.code, 0, `Editor exit ${row.outcome.code}/${row.outcome.signal}`);
    assert.equal(row.outcome.signal, null); assert(!row.deadlineExceeded && !interruption, 'Own Editor run interrupted or timed out');
    const nativeLog = await fs.readFile(row.runtimeLogPath, 'utf8');
    const stdout = await fs.readFile(row.stdoutPath, 'utf8');
    row.rawLogHashes = { runtime: await hashFile(row.runtimeLogPath), stdout: await hashFile(row.stdoutPath) };
    const combined = nativeLog + '\n' + stdout;
    const bad = combined.split('\n').filter(line => /Fatal error:|Assertion failed:|Ensure condition failed:|Shader compilation failures|Failed to compile.*shader|Failed to compile Material|Failed to load.*(?:uasset|Brezi|\/Game\/)/i.test(line));
    row.shaderAndLoadErrors = bad;
    assert.equal(bad.length, 0, 'Native shader, asset load or assertion errors observed');
    assert(combined.includes('Engine is initialized. Leaving FEngineLoop::Init()'), 'Native engine initialization was not observed');
    row.shaderReadiness = { source: 'raw native logs retained', pendingShaderCountAtCaptureObserved: false,
      note: 'The original recorder does not report a pending shader count. Absence of compilation errors alone does not prove complete shader/asset readiness; inspect the actual image.' };
    const emittedFiles = await filesBelow(caseDirectory);
    // The native AX initializer/shutdown writes separate nested metadata.
    // Only direct Diagnostics children are recorder runtime reports; all
    // nested originals remain retained and hashed in emittedNativeDiagnostics.
    const diagnostics = emittedFiles.filter(p => path.basename(path.dirname(p)) === 'Diagnostics' && p.endsWith('.json'));
    assert.equal(diagnostics.length, 1, 'Expected exactly one actual native runtime diagnostic');
    const runtimePath = diagnostics[0], raw = await fs.readFile(runtimePath);
    const runtime = JSON.parse(raw); const capturePath = path.resolve(runtime.screenshotPath ?? '');
    assert(isWithin(caseDirectory, capturePath), 'Native screenshot path escapes the fresh own case');
    const image = await fs.readFile(capturePath);
    row.originalRuntimePath = runtimePath; row.originalCapturePath = capturePath;
    row.originalRuntimeSha256 = shaBytes(raw); row.originalCaptureSha256 = shaBytes(image);
    assert(image.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])) && image.toString('ascii', 12, 16) === 'IHDR', 'Actual capture is not a PNG');
    const dimensions = [image.readUInt32BE(16), image.readUInt32BE(20)];
    verifyRuntime(runtime, row, dimensions);
    row.observed = { buildConfiguration: runtime.buildConfiguration, processId: runtime.processId,
      rhi: runtime.rhi, shaderPlatform: runtime.shaderPlatform, activeView: runtime.activeView,
      screenshotKind: runtime.screenshotKind, screenshotPixels: runtime.screenshotPixels,
      actualCamera: runtime.walking.presentationCamera, renderSettings: runtime.renderSettings,
      foregroundTimingFacts: runtime.focusDuringBenchmark, frameIntervalFacts: runtime.frameInterval,
      timingInterpretation: 'Editor-process samples are retained as observations; no Shipping comparison or performance acceptance.' };
    row.nativeEvidenceValidated = true;
    row.status = 'editor-game-capture-recorded-awaiting-visual-review';
  } catch (error) {
    row.status = 'editor-game-pilot-rejected'; row.errors = [error.stack ?? String(error)]; throw error;
  } finally {
    // Even a rejected process may have emitted useful native evidence. Discover,
    // reference and hash it without rewriting the native JSON or PNG.
    try {
      const emitted = await filesBelow(caseDirectory);
      row.emittedNativeDiagnostics = await Promise.all(emitted.filter(file =>
        file.includes(path.sep + 'Diagnostics' + path.sep) && /\.(json|png|log)$/.test(file))
        .map(async file => ({ path: file, ...await hashFile(file) })));
      for (const [extension, pathKey, hashKey] of [
        ['.png', 'originalCapturePath', 'originalCaptureSha256'],
        ['.json', 'originalRuntimePath', 'originalRuntimeSha256'],
      ]) {
        const actual = row.emittedNativeDiagnostics.filter(file => file.path.endsWith(extension));
        if (!row[pathKey] && actual.length === 1) { row[pathKey] = actual[0].path; row[hashKey] = actual[0].sha256; }
      }
    } catch (error) { row.evidenceDiscoveryError = error.stack ?? String(error); }
    row.endedAt ??= new Date().toISOString(); await save(row.processReceiptPath, row); await save(suiteFile, suite);
    console.log(JSON.stringify({ event: 'editor-pilot-case-finished', view, status: row.status,
      originalCapturePath: row.originalCapturePath ?? null, originalRuntimePath: row.originalRuntimePath ?? null,
      processReceiptPath: row.processReceiptPath, errors: row.errors ?? [] }));
  }
}

try {
  await preflight();
  for (const view of views) { assert(!interruption, 'Pilot interrupted'); await runCase(view); }
} catch (error) {
  suite.errors.push(error.stack ?? String(error)); process.exitCode = 1;
} finally {
  if (closureBefore) {
    try {
      const afterFiles = await closureFiles(), after = await hashFiles(afterFiles);
      const afterFile = path.join(suiteDirectory, 'inputs-after.json'); await save(afterFile, after);
      suite.inputClosureAfter = { path: afterFile, ...await hashFile(afterFile), fileCount: afterFiles.length };
      suite.sourceInputsUnchanged = same(sourceFilesBefore, afterFiles) && same(closureBefore, after);
      assert(suite.sourceInputsUnchanged, 'Actual source Content/Config/Source or native binary closure changed during pilot');
      suite.nativeIdleAfter = await nativeIdle();
    } catch (error) { suite.errors.push(error.stack ?? String(error)); process.exitCode = 1; }
  }
  suite.endedAt = new Date().toISOString(); suite.interruption = interruption;
  suite.status = suite.errors.length ? 'editor-game-pilot-rejected'
    : 'editor-game-suite-recorded-awaiting-independent-visual-review';
  await save(suiteFile, suite);
  console.log(JSON.stringify({ event: 'editor-pilot-suite-finished', status: suite.status, suiteDirectory,
    suiteFile, sourceInputsUnchanged: suite.sourceInputsUnchanged ?? null, ...deniedClaims,
    captures: suite.cases.map(row => ({ view: row.view, path: row.originalCapturePath ?? null,
      runtime: row.originalRuntimePath ?? null, status: row.status })), errors: suite.errors }));
}
