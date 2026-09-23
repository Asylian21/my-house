import { describe, expect, it } from 'vitest';
import { buildDoorsContract } from '../scripts/unreal/doors.mjs';

const matrix = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
const bounds = { min: [10, 20, 0], max: [90, 24, 200] };
function fixture() {
  const progressSamples = Array.from({ length: 129 }, (_, index) => index / 128);
  const member = { sourceId: 'current-leaf', sourceName: 'Current door leaf', hidden: false,
    collision: true, closedBoundsCm: bounds,
    poses: progressSamples.map(p => matrix.map((n, i) => i === 12 ? p * 80 : n)),
    handlePoses: progressSamples.map(p => matrix.map((n, i) => i === 12 ? p * 80 : n)) };
  const scene = { activeDesign: { variant: 'C', livingLayout: 'B', heatingLayout: 'B' }, objSha256: 'test-obj',
    objects: [{ id: 'DOM_CURRENT', sourceId: member.sourceId, name: member.sourceName, enabled: true,
      boundsMm: { min: [100, -240, 0], max: [900, -200, 2000] }, metadata: { doorId: 'CURRENT', doorMotion: 'SLIDING' } }],
    doorMotion: { source: 'registered-web-door-apply-functions', coordinateSystem: 'UNREAL_XY_Z_CM', closedCapture: true,
      progressSamples, architecturalInventory: [{ id: 'CURRENT' }], interaction: {},
      doors: [{ id: 'CURRENT', kind: 'SLIDING', architectural: true, interactionPointCm: [50, 22, 122], members: [member] }] } };
  return { scene, hidden: { objects: [] as object[] } };
}

describe('native door contract provenance and complete moving-member binding', () => {
  it('resolves current source identity and bounds, never a historical DOM ordinal', () => {
    const { scene, hidden } = fixture();
    const first = buildDoorsContract(scene, hidden, 'source', 'hidden');
    expect(first.memberCount).toBe(1);
    expect(first.doors[0].members[0].sourceObjectId).toBe('DOM_CURRENT');
    const tag = first.doors[0].members[0].runtimeTag;
    scene.objects[0].id = 'DOM_DIFFERENT_ORDINAL';
    expect(buildDoorsContract(scene, hidden, 'source', 'hidden').doors[0].members[0].runtimeTag).toBe(tag);
  });

  it('rejects a missing source leaf and any omitted dynamic hardware', () => {
    const { scene, hidden } = fixture();
    scene.objects[0].sourceId = 'not-this-leaf';
    expect(() => buildDoorsContract(scene, hidden, 'source', 'hidden')).toThrow(/missing\/ambiguous/);
    const next = fixture();
    next.scene.objects.push({ ...next.scene.objects[0], id: 'DOM_HANDLE', sourceId: 'handle' });
    expect(() => buildDoorsContract(next.scene, next.hidden, 'source', 'hidden')).toThrow(/remain frozen/);
  });

  it('rejects scale/shear and nonclosed initial state', () => {
    const first = fixture();
    first.scene.doorMotion.doors[0].members[0].poses[1][0] = 1.02;
    expect(() => buildDoorsContract(first.scene, first.hidden, 'source', 'hidden')).toThrow(/Non-rigid/);
    const second = fixture(); second.scene.doorMotion.doors[0].members[0].poses[0][12] = 2;
    expect(() => buildDoorsContract(second.scene, second.hidden, 'source', 'hidden')).toThrow(/begin closed/);
  });

  it('rejects ambiguous source identity and a member assigned to two animations', () => {
    const first = fixture(); first.scene.objects.push({ ...first.scene.objects[0], id: 'DOM_DUPLICATE' });
    expect(() => buildDoorsContract(first.scene, first.hidden, 'source', 'hidden')).toThrow(/ambiguous/);
    const second = fixture(); second.scene.doorMotion.doors.push({ ...second.scene.doorMotion.doors[0], id: 'OTHER' });
    expect(() => buildDoorsContract(second.scene, second.hidden, 'source', 'hidden')).toThrow(/shared/);
  });

  it('binds hidden blocking counterparts by their own provenance and native bounds', () => {
    const { scene, hidden } = fixture();
    const member = scene.doorMotion.doors[0].members[0];
    member.hidden = true; scene.objects = [];
    hidden.objects.push({ id: 'COLL_CURRENT', sourceId: member.sourceId, sourceName: member.sourceName, nativeBoundsCm: bounds });
    expect(buildDoorsContract(scene, hidden, 'source', 'hidden').doors[0].members[0].sourceObjectId).toBe('COLL_CURRENT');
  });
});
