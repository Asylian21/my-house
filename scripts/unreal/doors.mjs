import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const nativeBounds = r => ({ min: [r.boundsMm.min[0] / 10, -r.boundsMm.max[1] / 10, r.boundsMm.min[2] / 10],
  max: [r.boundsMm.max[0] / 10, -r.boundsMm.min[1] / 10, r.boundsMm.max[2] / 10] });
const closeBounds = (a, b) => ['min', 'max'].every(k => a[k]?.length === 3 && b[k]?.length === 3
  && a[k].every((v, i) => Number.isFinite(v) && Math.abs(v - b[k][i]) <= .05));
const identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];

export function buildDoorsContract(scene, hidden, sceneSha256, hiddenSha256) {
  const capture = scene.doorMotion;
  assert.deepEqual(scene.activeDesign, { variant: 'C', livingLayout: 'B', heatingLayout: 'B' });
  assert.equal(capture?.source, 'registered-web-door-apply-functions');
  assert.equal(capture.closedCapture, true);
  assert.equal(capture.coordinateSystem, 'UNREAL_XY_Z_CM');
  const samples = capture.progressSamples;
  assert(samples.length >= 129 && samples[0] === 0 && samples.at(-1) === 1
    && samples.every((v, i) => Number.isFinite(v) && (i === 0 || v > samples[i - 1])));
  const used = new Set(), ids = new Set();
  const doors = capture.doors.map(door => {
    assert(!ids.has(door.id) && door.id && ['HINGED', 'SLIDING', 'OVERHEAD'].includes(door.kind)); ids.add(door.id);
    assert(door.members.length && door.members.length < 100 && door.interactionPointCm.length === 3 && door.interactionPointCm.every(Number.isFinite));
    const members = door.members.map(member => {
      const candidates = member.hidden ? hidden.objects.filter(r => r.sourceId === member.sourceId && r.sourceName === member.sourceName
        && closeBounds(r.nativeBoundsCm, member.closedBoundsCm)) : scene.objects.filter(r => r.enabled
          && r.sourceId === member.sourceId && r.name === member.sourceName && closeBounds(nativeBounds(r), member.closedBoundsCm));
      assert.equal(candidates.length, 1, `Door ${door.id} source member missing/ambiguous: ${member.sourceName}`);
      const record = candidates[0];
      assert(!used.has(record.id), `Door member shared across independent motions: ${record.id}`); used.add(record.id);
      for (const poses of [member.poses, member.handlePoses]) {
        assert.equal(poses.length, samples.length);
        for (const m of poses) {
          assert(m.length === 16 && m.every(Number.isFinite), 'Nonfinite native door matrix');
          assert([3, 7, 11].every(i => Math.abs(m[i]) < 1e-6) && Math.abs(m[15] - 1) < 1e-6);
          // Every source leaf/hardware motion must remain rigid. Do not hide a
          // scale/shear mismatch behind native FTransform decomposition.
          const rows = [0, 1, 2].map(row => m.slice(row * 4, row * 4 + 3));
          for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++)
            assert(Math.abs(rows[a].reduce((sum, v, i) => sum + v * rows[b][i], 0) - Number(a === b)) < .0001, 'Non-rigid source door delta');
        }
      }
      assert(member.poses[0].every((v, i) => Math.abs(v - identity[i]) < .002), 'Source capture does not begin closed');
      const stable = sha(JSON.stringify([door.id, member.sourceId, member.sourceName,
        ...member.closedBoundsCm.min.map(v => +v.toFixed(4)), ...member.closedBoundsCm.max.map(v => +v.toFixed(4))])).slice(0, 24);
      return { ...member, sourceObjectId: record.id, runtimeTag: `BreziDoorMember=${stable}` };
    });
    return { ...door, members };
  });
  const expected = capture.architecturalInventory.map(d => d.id).sort();
  assert.deepEqual(doors.filter(d => d.architectural).map(d => d.id).sort(), expected, 'Architectural door inventory incomplete');
  const dynamic = scene.objects.filter(r => r.enabled && (r.metadata?.doorMotion || r.metadata?.dynamicCameraOccluder) && r.metadata?.doorId);
  assert(dynamic.every(r => used.has(r.id)), 'A source dynamic door member would remain frozen');
  return { schemaVersion: 1, status: 'source-door-motion-validated', coordinateSystem: 'UNREAL_XY_Z_CM',
    sourceManifestSha256: sceneSha256, sourceObjSha256: scene.objSha256, hiddenCollisionSha256: hiddenSha256,
    progressSamples: samples, interaction: capture.interaction, architecturalInventory: capture.architecturalInventory,
    doors, memberCount: used.size, initialState: 'CLOSED', motionSource: capture.source,
    interpolation: 'rigid source transforms sampled at 1/128 progress plus lift-slide breakpoints; quaternion interpolation',
    handleMotion: 'source apply(progress, 0/1), blended by original handle-depression envelope',
    collisionPolicy: 'moving source-triangle colliders; prospective capsule overlap pauses before moving into player',
    excludedTraversal: capture.excludedTraversal };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const geometry = resolve(root, process.env.UNREAL_OUTPUT ?? process.env.BREZI_GEOMETRY ?? 'output/unreal/geometry');
  const sceneBytes = await readFile(resolve(geometry, 'scene.json'));
  const hiddenBytes = await readFile(resolve(geometry, 'hidden-collision.json'));
  const contract = buildDoorsContract(JSON.parse(sceneBytes), JSON.parse(hiddenBytes), sha(sceneBytes), sha(hiddenBytes));
  contract.pipelineFiles = Object.fromEntries(await Promise.all([
    'lib/babylon-doors.ts', 'lib/babylon-door-export.ts', 'lib/babylon-scene.ts', 'scripts/archviz/scene-export.ts', 'scripts/unreal/doors.mjs',
  ].map(async path => [path, sha(await readFile(resolve(root, path)))])));
  await writeFile(resolve(geometry, 'doors.json'), JSON.stringify(contract));
  console.log(JSON.stringify({ status: contract.status, doors: contract.doors.length,
    architecturalDoors: contract.architecturalInventory.length, members: contract.memberCount }));
}
