import assert from 'node:assert/strict';
import test from 'node:test';
import { existsSync, readFileSync } from 'node:fs';
import { buildArchvizRoomViewpoints } from '../scripts/unreal/archviz-room-viewpoints.mjs';

function sourceFixture() {
  const rooms = Array.from({ length: 13 }, (_, i) => ({ id: i < 12 ? `ROOM-1-${String(i+1).padStart(2, '0')}` : 'ROOM-DRESSING',
    number: `1.${i+1}`, name: `Room ${i+1}`, rectsMm: [{ x0: i*10000, y0: 0, x1: i*10000+6000, y1: 3000 }] }));
  const scene = { units: 'millimetres', activeDesign: { variant: 'C', heatingLayout: 'B', livingLayout: 'B' },
    sceneCenterMm: { x: 500, y: 1000 }, interior: { rooms }, materials: { OPAQUE: { alpha: 1 } }, objects: [] };
  const walkthrough = { activeDesign: scene.activeDesign, coordinateSystem: 'unreal-centimeters', sceneSha256: 'a'.repeat(64),
    steps: rooms.map((room, i) => ({ id: `visit-${i}`, kind: 'visit', regionId: room.id,
      targetCm: [(room.rectsMm[0].x1-1000-scene.sceneCenterMm.x)/10, -50, 0] })) };
  return { scene, walkthrough };
}

test('13 presets use unchanged physical visit points and aim into room space', () => {
  const { scene, walkthrough } = sourceFixture();
  const before = structuredClone({ scene, walkthrough });
  const views = buildArchvizRoomViewpoints(scene, walkthrough);
  assert.equal(views.length, 13);
  assert.equal(new Set(views.map(v => v.id)).size, 13);
  for (const [i, view] of views.entries()) {
    assert.deepEqual(view.eyeCm, [...walkthrough.steps[i].targetCm.slice(0, 2), 165]);
    assert(view.targetCm[0] < view.eyeCm[0]-300, 'Arrival near east wall must face inward to the west');
    assert.equal(view.horizontalFovDegrees, 90);
    assert.equal(view.presentation.derivation.visualQualityVerified, false);
  }
  assert.deepEqual({ scene, walkthrough }, before);
});

test('large merged site bounds do not fake an indoor obstruction', () => {
  const { scene, walkthrough } = sourceFixture();
  const baseline = buildArchvizRoomViewpoints(scene, walkthrough);
  scene.objects.push({ enabled: true, group: 'Fence', metadata: {}, materialSlots: ['OPAQUE'],
    boundsMm: { min: [-1000000, -1000000, 0], max: [1000000, 1000000, 2000] } });
  assert.deepEqual(buildArchvizRoomViewpoints(scene, walkthrough), baseline);
});

test('an opaque local partition changes the usable direction', () => {
  const { scene, walkthrough } = sourceFixture();
  const baseline = buildArchvizRoomViewpoints(scene, walkthrough)[0];
  scene.objects.push({ enabled: true, group: 'Walls', metadata: {}, materialSlots: ['OPAQUE'],
    boundsMm: { min: [2500, -1000, 0], max: [2600, 1200, 2600] } });
  const actual = buildArchvizRoomViewpoints(scene, walkthrough)[0];
  assert(actual.presentation.derivation.forwardClearCm < baseline.presentation.derivation.forwardClearCm);
  assert.notEqual(actual.presentation.derivation.selectedYawDegrees, baseline.presentation.derivation.selectedYawDegrees);
  for (let t = 0; t <= 1; t += .02) {
    const p = actual.eyeCm.map((v, i) => v+(actual.targetCm[i]-v)*t);
    assert(!(p[0] >= 250 && p[0] <= 260 && p[1] >= -120 && p[1] <= 100));
  }
});

test('missing visit and visit inside an opaque cabinet fail instead of inventing a position', () => {
  const { scene, walkthrough } = sourceFixture();
  assert.throws(() => buildArchvizRoomViewpoints(scene, { ...walkthrough, steps: walkthrough.steps.slice(1) }), /physical visit/);
  scene.objects.push({ enabled: true, group: 'Interior', metadata: {}, materialSlots: ['OPAQUE'],
    boundsMm: { min: [4400, 400, 0], max: [4600, 600, 2500] } });
  assert.throws(() => buildArchvizRoomViewpoints(scene, walkthrough), /Camera eye blocked/);
});

test('return visits preserve the original safe source entry point', () => {
  const { scene, walkthrough } = sourceFixture();
  const baseline = buildArchvizRoomViewpoints(scene, walkthrough);
  walkthrough.steps.push({ ...walkthrough.steps[0], id: 'return-visit', targetCm: [123, 123, 0] });
  assert.deepEqual(buildArchvizRoomViewpoints(scene, walkthrough), baseline);
});

test('current all-room source fixture supplies 13 inward native views', t => {
  const scenePath = new URL('../output/unreal/walk-game-20260922/geometry/scene.json', import.meta.url);
  const fixturePath = new URL('../output/unreal/walk-game-20260922/walkthrough-fixture.json', import.meta.url);
  if (!existsSync(scenePath) || !existsSync(fixturePath)) return t.skip('Local native baseline is unavailable');
  const views = buildArchvizRoomViewpoints(JSON.parse(readFileSync(scenePath)), JSON.parse(readFileSync(fixturePath)));
  assert.equal(views.length, 13);
  assert(views.every(v => v.presentation.derivation.forwardClearCm >= 100));
  assert(views.find(v => v.id === 'room-1-02').presentation.derivation.forwardClearCm > 700);
});
