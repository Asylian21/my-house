import assert from 'node:assert/strict';

const inRect = (p, r) => p[0] >= r[0] && p[0] <= r[2] && p[1] >= r[1] && p[1] <= r[3];
const contains = (p, rects) => rects.some(r => inRect(p, r));
const blocked = (p, obstacles) => obstacles.some(b => p.every((v, i) => v > b.min[i] - 2 && v < b.max[i] + 2));

/** Inward room views from the source/collision-derived physical visit points.
 * A conservative ray fan selects room space rather than the arrival heading.
 * These are visual-review candidates; neither AABBs nor a camera preset prove
 * furnishing completeness, collision reachability, or rendered lighting.
 */
export function buildArchvizRoomViewpoints(scene, walkthrough) {
  assert.deepEqual(scene.activeDesign, { variant: 'C', heatingLayout: 'B', livingLayout: 'B' });
  assert.deepEqual(walkthrough.activeDesign, scene.activeDesign);
  assert.equal(scene.units, 'millimetres');
  assert.equal(walkthrough.coordinateSystem, 'unreal-centimeters');
  assert.match(walkthrough.sceneSha256, /^[a-f0-9]{64}$/);
  const center = scene.sceneCenterMm;
  const rooms = scene.interior.rooms;
  assert.equal(rooms.length, 13);
  const rects = room => room.rectsMm.map(r => [(r.x0-center.x)/10, (center.y-r.y1)/10, (r.x1-center.x)/10, (center.y-r.y0)/10]);
  // Merged site/fence/roof batches span empty house space in their AABB. Room
  // polygons already bound the view; only local interior/partition bounds apply.
  const obstacles = scene.objects.filter(o => o.enabled && ['Interior', 'Walls'].includes(o.group)
    && !o.metadata?.doorId && !o.metadata?.walkSurface
    && o.boundsMm.min[2] < 1800 && o.boundsMm.max[2] > 1050
    && o.materialSlots.every(slot => scene.materials[slot].alpha >= .99)).map(o => ({
      min: [o.boundsMm.min[0]/10, -o.boundsMm.max[1]/10, o.boundsMm.min[2]/10],
      max: [o.boundsMm.max[0]/10, -o.boundsMm.min[1]/10, o.boundsMm.max[2]/10],
    }));
  return rooms.map(room => {
    const visits = walkthrough.steps.filter(step => step.kind === 'visit' && step.regionId === room.id);
    assert(visits.length >= 1, `Source physical visit required for ${room.id}`);
    const eye = [...visits[0].targetCm.slice(0, 2), 165];
    const regions = rects(room);
    assert(eye.every(Number.isFinite) && contains(eye, regions), `Visit point outside ${room.id}`);
    assert(!blocked(eye, obstacles), `Camera eye blocked at source visit for ${room.id}`);
    const distance = angle => {
      const dx = Math.cos(angle), dy = Math.sin(angle);
      let clear = 0;
      for (let d = 10; d <= 1000; d += 10) {
        const p = [eye[0]+d*dx, eye[1]+d*dy, 165-Math.min(60, d*.15)];
        if (!contains(p, regions) || blocked(p, obstacles)) break;
        clear = d;
      }
      return clear;
    };
    let best;
    for (let degrees = 0; degrees < 360; degrees += 5) {
      const angle = degrees*Math.PI/180;
      const forward = distance(angle);
      const fan = [-30, -15, 15, 30].map(offset => distance(angle+offset*Math.PI/180));
      const score = forward*.5 + fan.reduce((sum, d) => sum+d, 0)*.125;
      if (!best || score > best.score) best = { angle, forward, fan, score, degrees };
    }
    assert(best.forward >= 40, `No inward source room view for ${room.id}`);
    const aimDistance = Math.min(400, best.forward*.8);
    const target = [eye[0]+Math.cos(best.angle)*aimDistance, eye[1]+Math.sin(best.angle)*aimDistance,
      165-Math.min(60, aimDistance*.15)];
    assert(contains(target, regions) && !blocked(target, obstacles));
    return { id: room.id.toLowerCase(), label: `${room.number} · ${room.name}`, eyeCm: eye, targetCm: target,
      horizontalFovDegrees: 90, source: `scene.interior.rooms[id=${room.id}]; source-derived walkthrough ${visits[0].id}`,
      presentation: { intent: 'Inspect occupied room lighting and furnishing from a source-safe inward view',
        roomId: room.id, eyeElevationMm: 1650, targetElevationMm: target[2]*10,
        derivation: { method: 'Physical source visit position; longest broad clear inward AABB ray fan',
          sceneSha256: walkthrough.sceneSha256, visitStepId: visits[0].id, forwardClearCm: best.forward,
          fanClearCm: best.fan, selectedYawDegrees: best.degrees, opaqueBoundsCount: obstacles.length,
          visualQualityVerified: false, nativeReachabilityVerifiedByThisHelper: false } } };
  });
}
