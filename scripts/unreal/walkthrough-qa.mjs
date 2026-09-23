import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { mkdir, readFile, writeFile, readdir, realpath, stat } from 'node:fs/promises';
import { resolve, dirname, relative, isAbsolute, basename } from 'node:path';
import { crc32, inflateSync } from 'node:zlib';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { isDeepStrictEqual } from 'node:util';
import { verifyPackagedPayload } from './package-verify.mjs';
import { requireIdleApp, resolveAppLaunch, inspectLauncherExecution } from './app-launch.mjs';
import { buildWalkthroughContract, insidePolygon } from './walkthrough-contract.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const save = (path, value) => writeFile(path, JSON.stringify(value, null, 2) + '\n');
const inside = (directory, path) => { const rel = relative(directory, path); return rel !== '..' && !rel.startsWith('../') && !isAbsolute(rel); };
const sameSet = (a, b) => Array.isArray(a) && a.length === new Set(a).size && isDeepStrictEqual([...a].sort(), [...b].sort());
const vector = v => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite);
const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
const contains = (region, p) => region.rectsCm?.some(r => p[0] >= r[0] && p[0] <= r[2] && p[1] >= r[1] && p[1] <= r[3])
  || (region.polygonCm && insidePolygon(p, region.polygonCm));

export function inspectWalkthroughPng(bytes, expectedPixels) {
  assert(Buffer.isBuffer(bytes) && bytes.length >= 57 && bytes.subarray(0, 8).toString('hex') === '89504e470d0a1a0a', 'Missing PNG signature');
  let offset = 8, width, height, channels, ended = false; const data = [];
  while (offset < bytes.length) {
    assert(offset + 12 <= bytes.length, 'Truncated PNG chunk');
    const length = bytes.readUInt32BE(offset), type = bytes.toString('ascii', offset + 4, offset + 8);
    assert(length <= bytes.length - offset - 12, 'Truncated PNG chunk payload');
    const payload = bytes.subarray(offset + 8, offset + 8 + length);
    assert.equal(crc32(bytes.subarray(offset + 4, offset + 8 + length)), bytes.readUInt32BE(offset + 8 + length), 'PNG CRC mismatch');
    if (offset === 8) assert.equal(type, 'IHDR');
    if (type === 'IHDR') {
      assert(width === undefined && length === 13); width = payload.readUInt32BE(0); height = payload.readUInt32BE(4);
      assert(width > 0 && height > 0 && width <= 8192 && height <= 8192 && payload[8] === 8 && [2, 6].includes(payload[9])
        && payload[10] === 0 && payload[11] === 0 && payload[12] === 0, 'Unexpected native PNG format'); channels = payload[9] === 6 ? 4 : 3;
    } else if (type === 'IDAT') data.push(payload);
    else if (type === 'IEND') { assert(length === 0 && offset + 12 === bytes.length, 'Invalid PNG ending'); ended = true; }
    offset += length + 12;
  }
  assert(ended && data.length, 'PNG lacks image data or IEND'); assert.deepEqual([width, height], expectedPixels, 'PNG size differs from native capture');
  const rowBytes = 1 + width * channels, decoded = inflateSync(Buffer.concat(data), { maxOutputLength: rowBytes * height });
  assert.equal(decoded.length, rowBytes * height, 'Decoded PNG rows are incomplete');
  for (let row = 0; row < height; ++row) assert(decoded[row * rowBytes] <= 4, 'Invalid PNG row filter');
  return { pixels: [width, height], sha256: sha(bytes), decodedPixelsVerified: true };
}

export function inspectWalkthroughScreenshots(fixture, runtime, images) {
  const errors = [], check = (condition, message) => { if (!condition) errors.push(message); };
  const expected = fixture.requiredRegions.map(r => r.id), captures = runtime?.screenshots ?? [];
  check(runtime?.screenshotsRequested === true && runtime.screenshotPending === false, 'Native room screenshots did not finish');
  check(sameSet(captures.map(c => c.regionId), expected) && sameSet(images.map(i => i.regionId), expected), 'Missing or duplicate region screenshots');
  for (const capture of captures) {
    const region = fixture.requiredRegions.find(r => r.id === capture.regionId), step = fixture.steps[capture.step];
    const image = images.find(i => i.regionId === capture.regionId);
    check(capture.saved === true && image?.decodedPixelsVerified === true && isDeepStrictEqual(capture.pixels, image.pixels)
      && isDeepStrictEqual(capture.pixels, capture.requestedPixels), `${capture.regionId}: requested capture has no valid matching PNG`);
    check(region && vector(capture.capsuleCenterCm) && contains(region, capture.capsuleCenterCm) && vector(capture.cameraEyeCm)
      && vector(capture.cameraForward) && step?.kind === 'visit' && step.regionId === capture.regionId
      && distance(capture.capsuleCenterCm, step.targetCm) <= 8, `${capture.regionId}: screenshot pose is not its physical room visit`);
  }
  return { status: errors.length ? 'failed' : 'native-region-screenshots-validated', errors, count: images.length, visualQualityAccepted: false };
}

/** Recompute coverage and movement evidence; a native success label alone is insufficient. */
export function inspectWalkthrough({ fixture, runtime, walking }) {
  const errors = [], check = (condition, message) => { if (!condition && errors.length < 100) errors.push(message); };
  const required = fixture.requiredRegions.map(r => r.id), doors = fixture.portals.filter(p => p.kind === 'door').map(p => p.id);
  check(runtime?.schemaVersion === 1 && runtime.status === 'passed-continuous-walkthrough' && runtime.error === '', 'Native walkthrough did not complete');
  check(runtime?.automatedInputMode === 'background-engine-bindings-without-os-capture' && runtime.automationStarted === true
    && runtime.foregroundCaptureVerified === false, 'Explicit background QA scope is missing or claims foreground capture');
  check(isDeepStrictEqual(runtime?.fixture, fixture) && runtime?.sceneSha256 === fixture.sceneSha256, 'Native fixture or source hash differs');
  check(runtime?.completedSteps === fixture.steps.length && runtime.initialPlacements === 1, 'Route was not completed from exactly one initial placement');
  check(!fixture.exerciseCloseReopen || runtime?.inputCloseCount === doors.length, 'Not every door was closed with E');
  check(runtime?.inputOpenCount === doors.length * (fixture.exerciseCloseReopen ? 2 : 1) && sameSet(runtime?.openedDoors, doors), 'Not every architectural door was opened through E once');
  check(sameSet(runtime?.visitedRegions, required), 'Required region inventory differs');
  const observations = runtime?.path ?? [], events = runtime?.events ?? [], sampledRegions = new Set(), seenSteps = new Set();
  check(observations.length > fixture.steps.length && observations.length <= 120000, 'Missing or excessive continuous path samples');
  const finalByStep = new Map(), closedDoorInput = []; let prior = null, length = 0;
  for (const [index, sample] of observations.entries()) {
    const prefix = `Sample ${index}: `;
    if (!vector(sample.capsuleCenterCm) || !vector(sample.velocityCmPerSecond) || !Number.isFinite(sample.deltaSeconds)
      || sample.deltaSeconds <= 0 || !Number.isInteger(sample.step) || sample.step < 0 || sample.step > fixture.steps.length) {
      check(false, prefix + 'malformed physical observation'); continue;
    }
    check(sample.grounded === true && fixture.allowedSupportObjectIds.includes(sample.supportObjectId)
      && sample.unexpectedOverlap === false && Number.isFinite(sample.eyeErrorCm) && sample.eyeErrorCm <= 0.5,
    prefix + 'unsupported, penetrating or invalid eye-height movement');
    const actualRegions = fixture.requiredRegions.filter(r => contains(r, sample.capsuleCenterCm)).map(r => r.id);
    check(sameSet(sample.regions, actualRegions), prefix + 'reported regions differ from actual capsule coordinates');
    actualRegions.forEach(id => sampledRegions.add(id)); seenSteps.add(sample.step); finalByStep.set(sample.step, sample);
    if (prior) {
      const moved = Math.hypot(...sample.capsuleCenterCm.map((n, i) => n - prior.capsuleCenterCm[i])); length += moved;
      check(sample.step >= prior.step && sample.step <= prior.step + 1, prefix + 'step order skipped or reversed');
      check(Math.abs(moved - sample.travelCm) <= 0.001 && moved <= walking.speedsCmPerSecond.boost * sample.deltaSeconds + walking.maxStepHeightCm + 2,
        prefix + 'position continuity or measured displacement differs');
    }
    prior = sample;
  }
  check(sameSet([...sampledRegions], required), 'Actual capsule samples do not cover every required region');
  check(runtime?.distanceCm >= 100 && Math.abs((runtime?.distanceCm ?? NaN) - length) < 1, 'Measured route distance is inconsistent');
  for (const [index, step] of fixture.steps.entries()) {
    check(seenSteps.has(index), `Step ${index}: missing movement observation`);
    if (step.kind === 'move' || step.kind === 'visit') {
      const last = finalByStep.get(index);
      check(last && distance(last.capsuleCenterCm, step.targetCm) <= (step.kind === 'move' ? 5.5 : 8), `Step ${index}: target was not physically reached`);
    }
    if (step.kind === 'visit') check(events.some(e => e.kind === 'region-visited' && e.step === index && e.regionId === step.regionId
      && vector(e.capsuleCenterCm) && distance(e.capsuleCenterCm, step.targetCm) <= 8), `Step ${index}: source room-depth visit was not observed`);
    if (step.kind !== 'door') continue;
    const forDoor = events.filter(e => e.doorId === step.doorId && e.step === index);
    const sweep = forDoor.filter(e => e.kind === 'closed-door-sweep'), block = forDoor.filter(e => e.kind === 'closed-door-blocked-input');
    const opened = forDoor.filter(e => e.kind === 'E-open-passage-clear');
    check(sweep.length === 1 && step.closedObjectIds.includes(sweep[0].hitObjectId) && sweep[0].hitDistanceCm >= 1,
      `${step.doorId}: missing source closed capsule blocker`);
    check(block.length === 1 && block[0].wHeldSamples >= 3 && sweep.length === 1 && block[0].progressCm >= Math.max(0, sweep[0].hitDistanceCm - 3)
      && block[0].progressCm <= sweep[0].hitDistanceCm + 0.5, `${step.doorId}: W did not stop at closed leaf`);
    const holdPhase = observations.filter(s => s.step === index && s.phase === 'door-closed-hold');
    const held = holdPhase.filter(s => s.wInputDown === true);
    // Prove actual input pressure, rather than require every phase frame to
    // report W down. Unheld frames never contribute to the measured hold time.
    const heldSeconds = held.reduce((sum, s) => sum + s.deltaSeconds, 0);
    check(held.length >= 3 && holdPhase.every(s => typeof s.wInputDown === 'boolean') && heldSeconds >= 1.45,
      `${step.doorId}: missing held W input samples`);
    check(block.length === 1 && block[0].wHeldSamples === held.length, `${step.doorId}: native held W sample count differs`);
    closedDoorInput.push({ doorId: step.doorId, phaseSamples: holdPhase.length, heldSamples: held.length, heldSeconds,
      unheldSamples: holdPhase.length - held.length, unheldSeconds: holdPhase.filter(s => s.wInputDown === false)
        .reduce((sum, s) => sum + s.deltaSeconds, 0) });
    const openedState = opened[0]?.doors?.doors?.find(d => d.id === step.doorId);
    check(opened.length === 1 && openedState?.phase === 'OPEN' && openedState.progress === 1 && openedState.targetProgress === 1
      && openedState.blocked === false, `${step.doorId}: actual E-open state not observed`);
    check(Array.isArray(opened[0]?.acceptedStepSupportObjectIds) && opened[0].acceptedStepSupportObjectIds.every(id => fixture.allowedSupportObjectIds.includes(id))
      && Number.isFinite(opened[0]?.preflightRaisedByCm) && opened[0].preflightRaisedByCm >= 0 && opened[0].preflightRaisedByCm <= walking.maxStepHeightCm,
    `${step.doorId}: open preflight ignored a nonfloor blocker or excessive step`);
    if (fixture.exerciseCloseReopen) {
      const first = forDoor.filter(e => e.kind === 'E-first-open-state'), closed = forDoor.filter(e => e.kind === 'E-closed-source-sweep');
      const firstState = first[0]?.doors?.doors?.find(d => d.id === step.doorId), closedState = closed[0]?.doors?.doors?.find(d => d.id === step.doorId);
      check(first.length === 1 && firstState?.phase === 'OPEN' && firstState.progress === 1 && firstState.targetProgress === 1,
        `${step.doorId}: first E opening was not observed`);
      check(closed.length === 1 && closedState?.phase === 'CLOSED' && closedState.progress === 0 && closedState.targetProgress === 0
        && closedState.blocked === false && step.closedObjectIds.includes(closed[0].hitObjectId) && closed[0].hitDistanceCm >= 1,
      `${step.doorId}: E closing did not restore the actual source capsule blocker`);
    }
    const crossing = fixture.steps[index + 1], reached = finalByStep.get(index + 1);
    check(crossing?.kind === 'move' && crossing.portalId === step.doorId && reached && distance(reached.capsuleCenterCm, crossing.targetCm) <= 5.5,
      `${step.doorId}: open portal was not physically crossed`);
  }
  const actualDoors = runtime?.doors?.doors ?? [];
  check(runtime?.doors?.ready === true && runtime.doors.sourceManifestSha256 === fixture.sceneSha256
    && sameSet(actualDoors.filter(d => d.architectural).map(d => d.id), doors), 'Final native architectural door inventory differs');
  check(sameSet(actualDoors.map(d => d.id), fixture.interactiveDoorInventory.map(d => d.id)), 'Final native interactive door inventory differs');
  const w = runtime?.walking;
  check(w?.contractLoaded === true && w.worldContractValidated === true && w.sceneSha256 === fixture.sceneSha256
    && Array.isArray(w.worldContractErrors) && w.worldContractErrors.length === 0 && w.successfulEntries === 1
    && w.cameraMode === 'walking', 'Final native walking source validation or single-entry count differs');
  return { status: errors.length ? 'failed' : 'continuous-walkthrough-validated', errors, counts: fixture.counts,
    distanceMetres: length / 100, sampledRegions: [...sampledRegions], closedDoorInput,
    visualQualityAccepted: false, nativeOSKeyboardVerified: false };
}

export async function prepareWalkthrough(output, closeReopen = false) {
  const paths = ['scene.json', 'walking.json', 'hidden-collision.json'];
  const bytes = await Promise.all(paths.map(name => readFile(resolve(output, 'geometry', name))));
  const [scene, walking, hidden] = bytes.map(b => JSON.parse(b));
  const fixture = buildWalkthroughContract(scene, walking, hidden, {
    sceneSha256: sha(bytes[0]), walkingSha256: sha(bytes[1]), hiddenCollisionSha256: sha(bytes[2]),
    helperSha256: sha(await readFile(resolve(ROOT, 'scripts/unreal/walkthrough-contract.mjs'))) });
  if (closeReopen) fixture.exerciseCloseReopen = true;
  const path = resolve(output, closeReopen ? 'walkthrough-close-reopen-fixture.json' : 'walkthrough-fixture.json'); await save(path, fixture);
  return { path, fixture, walking, bytes: await readFile(path) };
}

export async function runWalkthrough(output, closeReopen = false, screenshots = false, presentation = false) {
  const packagePath = resolve(output, 'model-package.json'), packageBytes = await readFile(packagePath), receipt = JSON.parse(packageBytes);
  assert.equal(receipt.status, 'current-model-packaged');
  const prepared = await prepareWalkthrough(output, closeReopen);
  assert.equal(prepared.fixture.sceneSha256, receipt.sourceManifestSha256);
  for (const name of ['BreziWalkingTraversal.cpp', 'BreziWalkingTraversal.h', 'BreziDoors.cpp', 'BreziDoors.h', 'BreziPawn.cpp', 'BreziPlayerController.cpp']) {
    const staged = resolve(output, 'Project/BreziTwin/Source/BreziTwin', name);
    assert.equal(sha(await readFile(staged)), receipt.inputs[staged], `Unpinned packaged QA source: ${name}`);
    assert.equal(sha(await readFile(resolve(ROOT, 'unreal/BreziTwin/Source/BreziTwin', name))), receipt.inputs[staged], `Changed QA source: ${name}`);
  }
  const before = await verifyPackagedPayload(receipt.appPath, receipt.bundle), launch = await resolveAppLaunch(receipt.appPath, receipt.bundle);
  await requireIdleApp();
  const invocation = `walkthrough-${randomUUID()}`, evidence = resolve(output, 'qa', invocation);
  const sandbox = resolve(homedir(), 'Library/Containers/local.brezi.twin/Data/Library/Application Support/BreziTwin/QA', invocation);
  await mkdir(dirname(sandbox), { recursive: true }); await mkdir(sandbox);
  await mkdir(dirname(evidence), { recursive: true }); await mkdir(evidence);
  const fixturePath = resolve(sandbox, 'fixture.json'); await writeFile(fixturePath, prepared.bytes);
  await writeFile(resolve(evidence, 'fixture.json'), prepared.bytes); await writeFile(resolve(evidence, 'package.json'), packageBytes);
  const args = ['-windowed', '-ResX=1920', '-ResY=1080', `-UserDir=${sandbox}/`, `-abslog=${resolve(sandbox, 'runtime.log')}`,
    '-BreziOutput=retina', '-BreziRenderProfile=performance', `-BreziWalkthrough=${fixturePath}`, '-BreziTraversalExit', ...(presentation ? ['-BreziPresentationQA'] : []),
    ...(screenshots ? ['-BreziWalkthroughScreenshots'] : [])];
  const helperHashes = Object.fromEntries(await Promise.all(['walkthrough-qa.mjs', 'walkthrough-contract.mjs'].map(async name => [name, sha(await readFile(resolve(ROOT, 'scripts/unreal', name)))])));
  await save(resolve(evidence, 'invocation.json'), { invocation, output, sandbox, evidence, launch, args, fixtureSha256: sha(prepared.bytes), helperHashes });
  const startedAt = new Date().toISOString(), chunks = [], stdout = [], stderr = [];
  let totalBytes = 0, timedOut = false, logTruncated = false, processError = null;
  const outcome = await new Promise(accept => {
    const child = spawn(launch.executable, args, { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'] });
    let killTimer;
    const stop = () => { child.kill('SIGTERM'); killTimer ??= setTimeout(() => child.kill('SIGKILL'), 10000); };
    const timeout = setTimeout(() => { timedOut = true; stop(); }, 1560000);
    for (const [stream, target] of [[child.stdout, stdout], [child.stderr, stderr]]) stream.on('data', chunk => {
      totalBytes += chunk.length;
      if (totalBytes <= 128 * 1024 * 1024) { chunks.push(chunk); target.push(chunk); process.stdout.write(chunk); }
      else { logTruncated = true; stop(); }
    });
    child.once('error', error => { processError = error.message; });
    child.once('close', (code, signal) => {
      clearTimeout(timeout); clearTimeout(killTimer);
      accept({ code, signal, pid: child.pid ?? null, startedAt, endedAt: new Date().toISOString(), timedOut, logTruncated, error: processError });
    });
  });
  const processLog = Buffer.concat(chunks); let nativeLog = null, runtime = null, runtimeBytes = null, after = null;
  const images = [];
  const errors = [];
  await Promise.all([writeFile(resolve(evidence, 'process.log'), processLog), writeFile(resolve(evidence, 'stdout.log'), Buffer.concat(stdout)),
    writeFile(resolve(evidence, 'stderr.log'), Buffer.concat(stderr)), save(resolve(evidence, 'process.json'), outcome)]);
  try { nativeLog = await readFile(resolve(sandbox, 'runtime.log')); await writeFile(resolve(evidence, 'runtime.log'), nativeLog); }
  catch (error) { errors.push('Native log: ' + error.message); }
  const launchValidation = inspectLauncherExecution(launch, outcome, processLog.toString() + '\n' + (nativeLog?.toString() ?? ''));
  if (launchValidation.errors.length || outcome.timedOut || outcome.logTruncated || outcome.error) errors.push(...launchValidation.errors, 'Native process did not finish cleanly');
  try {
    const diagnostics = await realpath(resolve(sandbox, 'Saved/Diagnostics'));
    assert(inside(await realpath(sandbox), diagnostics));
    const names = (await readdir(diagnostics)).filter(n => /^walkthrough-.*\.json$/.test(n)); assert.equal(names.length, 1);
    const path = await realpath(resolve(diagnostics, names[0])); assert(inside(diagnostics, path));
    const modified = (await stat(path)).mtimeMs; assert(modified >= Date.parse(startedAt) - 1000 && modified <= Date.parse(outcome.endedAt) + 1000);
    runtimeBytes = await readFile(path); runtime = JSON.parse(runtimeBytes); await writeFile(resolve(evidence, 'runtime.json'), runtimeBytes);
    const recorded = Date.parse(runtime.recordedAtUtc); assert(recorded >= Date.parse(startedAt) - 1000 && recorded <= Date.parse(outcome.endedAt) + 1000);
    assert.equal(sha(await readFile(fixturePath)), sha(prepared.bytes));
    if (screenshots) {
      await mkdir(resolve(evidence, 'rooms'));
      for (const capture of runtime.screenshots ?? []) {
        try {
          assert(capture.saved === true, 'Screenshot was requested but not saved');
          const imagePath = await realpath(capture.path); assert(inside(diagnostics, imagePath) && imagePath.endsWith('.png'), 'Screenshot escaped diagnostics');
          const modified = (await stat(imagePath)).mtimeMs, capturedAt = Date.parse(capture.recordedAtUtc);
          assert(modified >= Date.parse(startedAt) - 1000 && modified <= Date.parse(outcome.endedAt) + 1000
            && capturedAt >= Date.parse(startedAt) - 1000 && capturedAt <= Date.parse(outcome.endedAt) + 1000, 'Stale screenshot');
          const png = await readFile(imagePath), metadata = inspectWalkthroughPng(png, capture.pixels), target = resolve(evidence, 'rooms', basename(imagePath));
          await writeFile(target, png); images.push({ regionId: capture.regionId, path: target, sourcePath: imagePath, ...metadata });
        } catch (error) { errors.push(`Screenshot ${capture.regionId}: ${error.message}`); }
      }
    }
  } catch (error) { errors.push('Fresh runtime evidence: ' + error.message); }
  try {
    after = await verifyPackagedPayload(receipt.appPath, receipt.bundle); assert.equal(sha(await readFile(packagePath)), sha(packageBytes));
    for (const [name, hash] of Object.entries(helperHashes)) assert.equal(sha(await readFile(resolve(ROOT, 'scripts/unreal', name))), hash);
  } catch (error) { errors.push('Post-run package/helper integrity: ' + error.message); }
  const validation = inspectWalkthrough({ fixture: prepared.fixture, runtime, walking: prepared.walking });
  const screenshotValidation = screenshots ? inspectWalkthroughScreenshots(prepared.fixture, runtime, images) : null;
  if (screenshotValidation) validation.errors.push(...screenshotValidation.errors);
  const p = runtime?.presentationQA;
  if (presentation && (!p || p.status !== 'passed-native-presentation' || p.failure !== '' || !p.startupComplete
    || p.skeletalBoneCount < 50 || p.visibleRecentlyRenderedRigSamples < 1 || p.idlePoseChanges < 1 || p.walkingPoseChanges < 1
    || p.obstructedCameraSamples < 1 || p.maxCameraCacheErrorCm > 1 || p.maxBoomBeyondCollisionLimitCm > .1
    || p.zoomEvents?.length !== 6 || p.zoomEvents.some((e, i) => !e.handledByOwnedViewport || e.capsuleTravelCm > .05
      || !(i % 2 === 0 ? e.afterCm < e.beforeCm : e.afterCm > e.beforeCm))))
    validation.errors.push('Native presentation, animated avatar or viewport gestures did not validate');
  validation.errors.push(...errors); if (validation.errors.length) validation.status = 'failed';
  const report = { ...validation, generatedAt: new Date().toISOString(), invocation, evidence, sandbox, outcome, launch, launchValidation,
    payloadBefore: before.status, payloadAfter: after?.status, packageSha256: sha(packageBytes), fixtureSha256: sha(prepared.bytes), helperHashes,
    sourceManifestSha256: receipt.sourceManifestSha256, runtimeSha256: runtimeBytes ? sha(runtimeBytes) : null,
    processLogSha256: sha(processLog), nativeLogSha256: nativeLog ? sha(nativeLog) : null, screenshotValidation, images, presentationRequested: presentation, presentation: p ?? null,
    scope: 'Explicit background standalone QA uses engine-input M/F2/W/Q/E from one initial placement with no OS input capture or Slate focus changes. Physical path and complete architectural region/door coverage. Native room images when requested. Foreground behavior, visual quality, OS keyboard operation and frame-rate acceptance remain separate.' };
  await save(resolve(evidence, 'qa.json'), report);
  console.log(JSON.stringify({ status: report.status, report: resolve(evidence, 'qa.json'), counts: report.counts, distanceMetres: report.distanceMetres, errors: report.errors }, null, 2));
  if (report.status === 'failed') process.exitCode = 1;
  return report;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const output = resolve(ROOT, process.env.BREZI_MODEL_OUTPUT ?? 'output/unreal/walk-game-20260922');
  const flags = process.argv.slice(2);
  assert(new Set(flags).size === flags.length && flags.every(f => ['--prepare', '--close-reopen', '--screenshots', '--presentation'].includes(f)), 'Usage: walkthrough-qa.mjs [--prepare] [--close-reopen] [--screenshots]');
  if (flags.includes('--prepare')) { const result = await prepareWalkthrough(output, flags.includes('--close-reopen')); console.log(JSON.stringify({ path: result.path, counts: result.fixture.counts })); }
  else await runWalkthrough(output, flags.includes('--close-reopen'), flags.includes('--screenshots'), flags.includes('--presentation'));
}
