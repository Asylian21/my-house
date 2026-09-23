import test from 'node:test';
import assert from 'node:assert/strict';
import { planWalkPath, transformBounds, insidePolygon } from '../scripts/unreal/walkthrough-contract.mjs';
import { inspectWalkthrough, inspectWalkthroughPng, inspectWalkthroughScreenshots } from '../scripts/unreal/walkthrough-qa.mjs';
import { crc32, deflateSync } from 'node:zlib';

test('planning goes around a source furniture blocker with capsule clearance and cannot cut a diagonal corner', () => {
  const obstacle = { min: [40, 0, 0], max: [60, 70, 200] };
  const path = planWalkPath([10, 10], [90, 10], { contains: p => p[0] >= 0 && p[0] <= 100 && p[1] >= 0 && p[1] <= 100,
    obstacles: [obstacle], radiusCm: 10, gridCm: 5 });
  assert(path.some(p => p[1] >= 80));
  for (let i = 1; i < path.length; ++i) for (let t = 0; t <= 1; t += 0.01) {
    const x = path[i - 1][0] + (path[i][0] - path[i - 1][0]) * t, y = path[i - 1][1] + (path[i][1] - path[i - 1][1]) * t;
    assert(!(x > 30 && x < 70 && y > -10 && y < 80));
  }
  assert.throws(() => planWalkPath([10, 10], [90, 10], { contains: p => p[0] >= 0 && p[0] <= 100 && p[1] >= 0 && p[1] <= 75,
    obstacles: [obstacle], radiusCm: 10, gridCm: 5 }), /No conservative source path/);
});

test('actual exported relative native door poses rotate and translate all eight bounds corners', () => {
  const transformed = transformBounds({ min: [10, 20, 0], max: [50, 24, 200] }, [0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1, 0, 100, 30, 0, 1]);
  assert.deepEqual(transformed, { min: [76, 40, 0], max: [80, 80, 200] });
  assert(insidePolygon([2, 2], [[0, 0], [5, 0], [5, 5], [0, 5]]));
  assert(!insidePolygon([7, 2], [[0, 0], [5, 0], [5, 5], [0, 5]]));
});

function evidence() {
  const digest = 'a'.repeat(64), sourceDoor = { id: 'door', kind: 'HINGED', subject: 'DOOR', architectural: true };
  const state = { ...sourceDoor, phase: 'OPEN', progress: 1, targetProgress: 1, blocked: false };
  const doorSystem = { ready: true, sourceManifestSha256: digest, doors: [state] };
  const fixture = { sceneSha256: digest, allowedSupportObjectIds: ['floor'], interactiveDoorInventory: [sourceDoor], counts: { rooms: 2, doors: 1 },
    requiredRegions: [{ id: 'A', rectsCm: [[-200, -100, -0.01, 100]] }, { id: 'B', rectsCm: [[0, -100, 200, 100]] }],
    portals: [{ id: 'door', kind: 'door' }], steps: [
      { kind: 'visit', regionId: 'A', targetCm: [-100, 0, 0] },
      { kind: 'move', regionId: 'A', targetCm: [-50, 0, 0] },
      { kind: 'door', regionId: 'A', doorId: 'door', targetCm: [50, 0, 0], closedObjectIds: ['leaf'] },
      { kind: 'move', regionId: 'B', portalId: 'door', targetCm: [50, 0, 0] },
      { kind: 'visit', regionId: 'B', targetCm: [50, 0, 0] },
    ] };
  const runtime = { schemaVersion: 1, status: 'passed-continuous-walkthrough', error: '', fixture: structuredClone(fixture), sceneSha256: digest,
    automatedInputMode: 'background-engine-bindings-without-os-capture', automationStarted: true, foregroundCaptureVerified: false,
    completedSteps: 5, initialPlacements: 1, inputOpenCount: 1, openedDoors: ['door'], visitedRegions: ['A', 'B'], doors: doorSystem,
    walking: { contractLoaded: true, worldContractValidated: true, sceneSha256: digest, worldContractErrors: [], successfulEntries: 1, cameraMode: 'walking' },
    path: [], events: [
      { kind: 'region-visited', regionId: 'A', step: 0, capsuleCenterCm: [-100, 0, 87] },
      { kind: 'closed-door-sweep', doorId: 'door', step: 2, hitObjectId: 'leaf', hitDistanceCm: 28 },
      { kind: 'closed-door-blocked-input', doorId: 'door', step: 2, progressCm: 28, wHeldSamples: 15 },
      { kind: 'E-open-passage-clear', doorId: 'door', step: 2, doors: doorSystem, acceptedStepSupportObjectIds: [], preflightRaisedByCm: 0 },
      { kind: 'region-visited', regionId: 'B', step: 4, capsuleCenterCm: [50, 0, 87] },
    ], distanceCm: 0 };
  let prior = -100;
  const sample = (step, x, phase = 'step') => {
    const travel = Math.abs(x - prior); runtime.distanceCm += travel; prior = x;
    runtime.path.push({ step, phase, capsuleCenterCm: [x, 0, 87], velocityCmPerSecond: [0, 0, 0], deltaSeconds: 0.1, travelCm: travel,
      regions: [x < 0 ? 'A' : 'B'], grounded: true, supportObjectId: 'floor', unexpectedOverlap: false, eyeErrorCm: 0,
      wInputDown: phase === 'door-closed-hold' });
  };
  sample(0, -100); for (const x of [-90, -80, -70, -60, -50]) sample(1, x);
  sample(2, -40, 'door-closed-hold'); sample(2, -30, 'door-closed-hold');
  for (let i = 0; i < 13; ++i) sample(2, -22, 'door-closed-hold');
  sample(2, -30, 'door-retreat'); sample(2, -40, 'door-retreat'); sample(2, -50, 'door-return');
  for (let x = -40; x <= 50; x += 10) sample(3, x);
  sample(4, 50); sample(5, 50);
  return { fixture, runtime, walking: { speedsCmPerSecond: { boost: 240 }, maxStepHeightCm: 15 } };
}

test('complete physical room and closed-W / E-open / crossed-door evidence passes independently', () => {
  const result = inspectWalkthrough(evidence()); assert.deepEqual(result.errors, []); assert.equal(result.status, 'continuous-walkthrough-validated');
});

test('an unheld stationary phase sample is excluded when actual held input still proves closed-door pressure', () => {
  const value = evidence(), at = value.runtime.path.findIndex(s => s.phase === 'door-retreat');
  const released = { ...structuredClone(value.runtime.path[at - 1]), wInputDown: false, deltaSeconds: 0.040535, travelCm: 0 };
  value.runtime.path.splice(at, 0, released);
  const result = inspectWalkthrough(value);
  assert.deepEqual(result.errors, []);
  assert.equal(result.closedDoorInput[0].phaseSamples, 16);
  assert.equal(result.closedDoorInput[0].heldSamples, 15);
  assert(Math.abs(result.closedDoorInput[0].heldSeconds - 1.5) < 1e-9);
  assert.equal(result.closedDoorInput[0].unheldSeconds, 0.040535);
  assert.equal(value.runtime.events[2].wHeldSamples, 15);
});

test('unheld elapsed time cannot inflate insufficient real W pressure, even when native count agrees', () => {
  const value = evidence(), phase = value.runtime.path.filter(s => s.phase === 'door-closed-hold');
  phase.at(-1).wInputDown = false; phase.at(-1).deltaSeconds = 10;
  value.runtime.events[2].wHeldSamples = phase.length - 1;
  const result = inspectWalkthrough(value);
  assert(result.errors.includes('door: missing held W input samples'));
  assert(!result.errors.includes('door: native held W sample count differs'));
  assert(Math.abs(result.closedDoorInput[0].heldSeconds - 1.4) < 1e-9);
  assert.equal(result.closedDoorInput[0].unheldSeconds, 10);
});

test('held duration requires at least three samples and agrees exactly with the native counter', () => {
  for (const count of [0, 2, 14, 16, 15.5, undefined]) {
    const value = evidence(); value.runtime.events[2].wHeldSamples = count;
    assert(inspectWalkthrough(value).errors.includes('door: native held W sample count differs'));
  }
  const value = evidence(), phase = value.runtime.path.filter(s => s.phase === 'door-closed-hold');
  phase.forEach((s, index) => { s.wInputDown = index >= phase.length - 2; s.deltaSeconds = 1; });
  value.runtime.events[2].wHeldSamples = 2;
  assert(inspectWalkthrough(value).errors.includes('door: missing held W input samples'));
});

test('unheld phase samples retain physical guards and must still record a boolean input state', () => {
  for (const mutate of [
    s => { s.unexpectedOverlap = true; },
    s => { s.supportObjectId = 'unmeasured'; },
    s => { s.capsuleCenterCm[0] += 500; },
    s => { delete s.wInputDown; },
  ]) {
    const value = evidence(), at = value.runtime.path.findIndex(s => s.phase === 'door-retreat');
    const sample = { ...structuredClone(value.runtime.path[at - 1]), wInputDown: false, travelCm: 0 };
    value.runtime.path.splice(at, 0, sample); mutate(sample);
    assert.equal(inspectWalkthrough(value).status, 'failed');
  }
});

for (const [name, mutate] of [
  ['teleport between rooms', x => { x.runtime.path[25].capsuleCenterCm[0] += 500; }],
  ['two entry placements', x => { x.runtime.initialPlacements = 2; }],
  ['claimed room without physical samples', x => { x.fixture.requiredRegions.push({ id: 'missing', rectsCm: [[300, 300, 400, 400]] }); x.runtime.visitedRegions.push('missing'); }],
  ['standing only then claimed finished route', x => { x.runtime.path = x.runtime.path.slice(0, 2); }],
  ['wrong closed source blocker', x => { x.runtime.events[1].hitObjectId = 'different-leaf'; }],
  ['closed leaf crossed while W held', x => { x.runtime.events[2].progressCm = 70; }],
  ['no real W input', x => { x.runtime.path.filter(s => s.phase === 'door-closed-hold').forEach(s => { s.wInputDown = false; }); }],
  ['too brief closed input test', x => { x.runtime.path.filter(s => s.phase === 'door-closed-hold').forEach(s => { s.deltaSeconds = 0.01; }); }],
  ['door still opening', x => { x.runtime.doors.doors[0].phase = 'OPENING'; }],
  ['door opened with direct setter only', x => { x.runtime.inputOpenCount = 0; }],
  ['open door never physically crossed', x => { x.runtime.path.filter(s => s.step === 3).forEach(s => { s.capsuleCenterCm[0] = -22; }); }],
  ['unmeasured capsule penetration', x => { x.runtime.path[10].unexpectedOverlap = true; }],
  ['unsupported floor', x => { x.runtime.path[10].supportObjectId = 'unknown'; }],
  ['missing interactive inventory', x => { x.fixture.interactiveDoorInventory.push({ id: 'hatch', architectural: false }); }],
  ['repeated successful walking entry', x => { x.runtime.walking.successfulEntries = 2; }],
  ['door collider mistaken for legal threshold', x => { x.runtime.events[3].acceptedStepSupportObjectIds = ['leaf']; }],
  ['step higher than source walking limit', x => { x.runtime.events[3].acceptedStepSupportObjectIds = ['floor']; x.runtime.events[3].preflightRaisedByCm = 16; }],
  ['background QA claims foreground capture', x => { x.runtime.foregroundCaptureVerified = true; }],
]) test(`rejects ${name}`, () => {
  const value = evidence(); mutate(value); const result = inspectWalkthrough(value);
  assert.equal(result.status, 'failed'); assert(result.errors.length > 0);
});

function cycleEvidence() {
  const value = evidence(), { fixture, runtime } = value;
  fixture.exerciseCloseReopen = true; runtime.fixture = structuredClone(fixture);
  runtime.inputOpenCount = 2; runtime.inputCloseCount = 1;
  const closed = structuredClone(runtime.doors); Object.assign(closed.doors[0], { phase: 'CLOSED', progress: 0, targetProgress: 0 });
  runtime.events.push({ kind: 'E-first-open-state', doorId: 'door', step: 2, doors: structuredClone(runtime.doors) },
    { kind: 'E-closed-source-sweep', doorId: 'door', step: 2, hitObjectId: 'leaf', hitDistanceCm: 28, doors: closed });
  return value;
}

test('E open-close-reopen requires exact states and physically restored closed source collision', () => {
  assert.deepEqual(inspectWalkthrough(cycleEvidence()).errors, []);
  for (const mutate of [
    x => { x.runtime.inputCloseCount = 0; },
    x => { x.runtime.inputOpenCount = 1; },
    x => { x.runtime.events.at(-1).hitObjectId = 'wrong'; },
    x => { x.runtime.events.at(-1).doors.doors[0].progress = 0.1; },
    x => { x.runtime.events.at(-1).doors.doors[0].blocked = true; },
    x => { x.runtime.events.pop(); },
  ]) { const value = cycleEvidence(); mutate(value); assert.equal(inspectWalkthrough(value).status, 'failed'); }
});

test('a bounded authored floor step is permitted only before a separately measured full capsule crossing', () => {
  const value = evidence(); value.runtime.events[3].acceptedStepSupportObjectIds = ['floor']; value.runtime.events[3].preflightRaisedByCm = 2;
  assert.deepEqual(inspectWalkthrough(value).errors, []);
  value.runtime.path = value.runtime.path.filter(s => s.step < 3);
  assert.equal(inspectWalkthrough(value).status, 'failed');
});

function png() {
  const chunk = (name, bytes) => {
    const type = Buffer.from(name), length = Buffer.alloc(4), crc = Buffer.alloc(4);
    length.writeUInt32BE(bytes.length); crc.writeUInt32BE(crc32(Buffer.concat([type, bytes])));
    return Buffer.concat([length, type, bytes, crc]);
  };
  const header = Buffer.alloc(13); header.writeUInt32BE(2); header.writeUInt32BE(1, 4); header[8] = 8; header[9] = 2;
  return Buffer.concat([Buffer.from('89504e470d0a1a0a', 'hex'), chunk('IHDR', header),
    chunk('IDAT', deflateSync(Buffer.from([0, 255, 0, 0, 0, 0, 255]))), chunk('IEND', Buffer.alloc(0))]);
}

test('saved screenshot means matching native pixels with intact PNG chunks and decoded image data', () => {
  assert.equal(inspectWalkthroughPng(png(), [2, 1]).decodedPixelsVerified, true);
  assert.throws(() => inspectWalkthroughPng(png(), [4, 2]), /size differs/);
  assert.throws(() => inspectWalkthroughPng(png().subarray(0, 50), [2, 1]), /signature|Truncated/);
  const corrupt = png(); corrupt[45] ^= 1; assert.throws(() => inspectWalkthroughPng(corrupt, [2, 1]), /CRC/);
});

test('all-room screenshots require actual PNGs at the recorded physical room visits', () => {
  const { fixture, runtime } = evidence();
  runtime.screenshotsRequested = true; runtime.screenshotPending = false;
  runtime.screenshots = [['A', 0, -100], ['B', 4, 50]].map(([regionId, step, x]) => ({
    regionId, step, saved: true, pixels: [2, 1], requestedPixels: [2, 1], capsuleCenterCm: [x, 0, 87], cameraEyeCm: [x, 0, 165], cameraForward: [1, 0, 0],
  }));
  const images = ['A', 'B'].map(regionId => ({ regionId, ...inspectWalkthroughPng(png(), [2, 1]) }));
  assert.deepEqual(inspectWalkthroughScreenshots(fixture, runtime, images).errors, []);
  assert.equal(inspectWalkthroughScreenshots(fixture, runtime, []).status, 'failed');
  runtime.screenshots[1].saved = false; assert.equal(inspectWalkthroughScreenshots(fixture, runtime, images).status, 'failed');
  runtime.screenshots[1].saved = true; runtime.screenshots[1].capsuleCenterCm[0] = -100;
  assert.equal(inspectWalkthroughScreenshots(fixture, runtime, images).status, 'failed');
});
