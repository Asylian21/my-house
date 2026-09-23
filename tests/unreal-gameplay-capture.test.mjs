import assert from 'node:assert/strict';
import test from 'node:test';
import { modelQaArguments, inspectModelQaCapture, runModelQa } from '../scripts/unreal/model-refresh-qa.mjs';

function capture(mode) {
  const png = Buffer.alloc(24);
  Buffer.from('89504e470d0a1a0a', 'hex').copy(png);
  png.write('IHDR', 12); png.writeUInt32BE(1920, 16); png.writeUInt32BE(1080, 20);
  return { gameplayUi: mode, view: 'interior', walk: false, png, sourceManifestSha256: 'source',
    outcome: { code: 0, signal: null, startedAt: '2026-09-22T08:00:00Z', endedAt: '2026-09-22T08:00:30Z' },
    launchValidation: { status: 'recorded-self-exec-entry-chain', errors: [] },
    runtime: { recordedAtUtc: '2026-09-22T08:00:20Z', status: 'capture-complete', activeView: 'interior',
      screenshotSaved: true, screenshotPixels: [1920, 1080], rhi: 'Metal', warmupFrames: 240,
      requestedBenchmarkFrames: 240, frameInterval: { sampleCount: 240 },
      renderSettings: { 'r.ScreenPercentage': 50, 'r.TSR.History.ScreenPercentage': 100, 'r.AntiAliasingMethod': 4 },
      screenshotKind: 'fitted-slate-ui-capture-actual-window-pixels', doors: { ready: true },
      walking: { contractLoaded: true, worldContractValidated: true, worldContractErrors: [], sceneSha256: 'source',
        cameraMode: 'walking', characterMovementMode: 'Walking', successfulEntries: 1,
        entryQueryStatus: 'entry-floor-and-capsule-queries-passed', navigationActive: mode === 'play' } } };
}

test('gameplay UI uses its actual startup without a second walk audit or scene-only capture', () => {
  const args = modelQaArguments('interior', false, '/tmp/fresh', 'play');
  assert(args.includes('-BreziCaptureUI') && args.includes('-BreziGameplayUI=play'));
  assert(args.includes('-BreziOutput=4k') && !args.includes('-BreziOutput=retina'));
  assert(!args.includes('-BreziWalkAudit') && !args.includes('-BreziWalk') && !args.includes('-BreziCaptureScene'));
  assert.throws(() => modelQaArguments('street', false, '/tmp/fresh', 'play'));
  assert.throws(() => modelQaArguments('interior', true, '/tmp/fresh', 'pause'));
});

test('each requested menu section preserves paused gameplay and the fixed 4K UI capture', () => {
  for (const section of ['rooms', 'atmosphere', 'controls']) {
    const args = modelQaArguments('interior', false, '/tmp/fresh', 'pause', false, false, null, section);
    assert.deepEqual(args.filter(arg => arg.startsWith('-BreziMenuSection=')), [`-BreziMenuSection=${section}`]);
    assert(args.includes('-BreziGameplayUI=pause') && args.includes('-BreziCaptureUI'));
    assert(args.includes('-BreziOutput=4k') && !args.includes('-BreziOutput=retina'));
    assert(!args.includes('-BreziWalkAudit') && !args.includes('-BreziCaptureScene'));
  }
  for (const mode of [null, 'play', 'pause']) {
    const args = modelQaArguments('interior', false, '/tmp/fresh', mode);
    assert(!args.some(arg => arg.startsWith('-BreziMenuSection=')));
  }
});

test('menu sections reject unknown names and non-paused captures before package or process access', async () => {
  for (const mode of [null, 'play']) {
    assert.throws(() => modelQaArguments('interior', false, '/tmp/fresh', mode, false, false, null, 'rooms'),
      /requires paused gameplay UI/);
    await assert.rejects(runModelQa('interior', false, mode, false, false, null, 'rooms'),
      /requires paused gameplay UI/);
  }
  for (const section of ['', 'settings', 'ROOMS', 'rooms,controls']) {
    assert.throws(() => modelQaArguments('interior', false, '/tmp/fresh', 'pause', false, false, null, section),
      /Unknown gameplay menu section/);
    await assert.rejects(runModelQa('interior', false, 'pause', false, false, null, section),
      /Unknown gameplay menu section/);
  }
});

test('UI capture cannot pass with the wrong input state, missing doors, stale report or scene-only image', () => {
  for (const mode of ['play', 'pause']) {
    assert.equal(inspectModelQaCapture(capture(mode)).status, 'standalone-capture-validated');
    for (const mutate of [
      c => { c.runtime.walking.navigationActive = !c.runtime.walking.navigationActive; },
      c => { c.runtime.doors.ready = false; },
      c => { c.runtime.renderSettings['r.ScreenPercentage'] = 100; },
      c => { c.runtime.recordedAtUtc = '2026-09-21T08:00:20Z'; },
      c => { c.runtime.screenshotKind = 'current-scene-render-target-preserving-view-history'; },
    ]) {
      const input = capture(mode); mutate(input);
      assert.equal(inspectModelQaCapture(input).status, 'failed');
    }
  }
});
