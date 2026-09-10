import { describe, expect, it } from 'vitest';
import { EXTERIOR_LIGHTING } from '../lib/twin-exterior-lighting';
import { SCENE_CENTER_MM } from '../lib/twin-render-frame';
import { buildExteriorLighting } from '../scripts/unreal/exterior-lighting.mjs';

type Mutable<T> = { -readonly [K in keyof T]: Mutable<T[K]> };
const SCENE_SHA = 'cd'.repeat(32);
const OBJ_SHA = 'ab'.repeat(32);

/** Synthetic capture records; the fixture contract is the real shared source module. */
function capture() {
  const source = structuredClone(EXTERIOR_LIGHTING) as Mutable<typeof EXTERIOR_LIGHTING>;
  return {
    units: 'millimetres',
    objSha256: OBJ_SHA,
    sceneCenterMm: { ...SCENE_CENTER_MM },
    exteriorLighting: source,
    objects: source.fixtures.map((fixture, index) => {
      const [x, y, z] = fixture.geometry.bodyCenterPlanMm;
      const center = [x - SCENE_CENTER_MM.x, y - SCENE_CENTER_MM.y, z];
      // The two original vertical bodies are Ø70×170; the three inward pool bodies Ø135×22.
      const half = index < 2 ? [35, 35, 85] : [67.5, 11, 67.5];
      return {
        id: `DOM_${50000 + index}`, name: fixture.geometry.sourceName,
        metadata: { exteriorLightId: fixture.id }, enabled: true, instances: 1, triangles: 96,
        boundsMm: { min: center.map((v, i) => v - half[i]), max: center.map((v, i) => v + half[i]) },
      };
    }),
  };
}
type Capture = ReturnType<typeof capture>;
function reject(change: (scene: Capture) => void, reason?: RegExp) {
  const scene = capture(); change(scene);
  expect(() => buildExteriorLighting(scene, SCENE_SHA)).toThrow(reason);
}

describe('native exterior lighting compiler', () => {
  it('converts original body and separate emitter positions once, with native inward/down signs and physical units', () => {
    const result = buildExteriorLighting(capture(), SCENE_SHA);
    expect([result.sceneSha256, result.objSha256, result.coordinateSystem]).toEqual([SCENE_SHA, OBJ_SHA, 'UNREAL_XY_Z_CM']);
    expect(result.fixtures.map((f: { bodyCenterCm: number[] }) => f.bodyCenterCm)).toEqual([
      [740, -881, 393.5], [1120, -881, 393.5],
      [-161, -529.2, -65.2], [-46, -529.2, -65.2], [69, -529.2, -65.2],
    ]);
    expect(result.fixtures.map((f: { positionCm: number[] }) => f.positionCm)).toEqual([
      [740, -881, 382.8], [1120, -881, 382.8],
      [-161, -522.4, -65.2], [-46, -522.4, -65.2], [69, -522.4, -65.2],
    ]);
    for (const [index, fixture] of result.fixtures.entries()) {
      const wall = index < 2;
      // Numeric equality intentionally ignores IEEE -0 in the native Y conversion.
      expect(fixture.direction.every((v: number, axis: number) => v === (wall ? [0, 0, -1] : [0, 1, 0])[axis])).toBe(true);
      expect([fixture.nominalConeLumens, fixture.temperatureK, fixture.innerConeHalfAngleDeg, fixture.outerConeHalfAngleDeg,
        fixture.sourceRadiusCm, fixture.attenuationRadiusCm, fixture.castsShadows])
        .toEqual(wall ? [300, 2700, 25, 40, 2, 600, true] : [400, 4000, 35, 55, 5.5, 450, true]);
      expect(fixture.meshPath).toBe(`/Game/Brezi/Geometry/brezi-twin/StaticMeshes/DOM_${50000 + index}.DOM_${50000 + index}`);
    }
  });

  it('joins stable metadata IDs rather than capture order or fixed DOM numbers, without mutating the source', () => {
    const scene = capture(); scene.objects.reverse();
    scene.objects.forEach((object, i) => { object.id = `DOM_${60000 + i}`; });
    const before = structuredClone(scene);
    const result = buildExteriorLighting(scene, SCENE_SHA);
    for (const fixture of result.fixtures) {
      const object = scene.objects.find(o => o.metadata.exteriorLightId === fixture.id)!;
      expect(fixture.sourceTag).toBe(object.id);
      expect(fixture.sourceName).toBe(object.name);
    }
    expect(scene).toEqual(before);
  });

  it('refuses duplicate or missing fixture/source IDs and mismatched source names', () => {
    reject(s => { s.exteriorLighting.fixtures[1].id = s.exteriorLighting.fixtures[0].id; }, /five source fixtures/);
    reject(s => { s.exteriorLighting.fixtures.pop(); }, /five source fixtures/);
    reject(s => { s.objects.pop(); }, /ambiguous\/missing source mesh/);
    reject(s => { s.objects.push(structuredClone(s.objects[0])); }, /ambiguous\/missing source mesh/);
    reject(s => { s.objects[0].name = 'Unrelated lamp'; }, /source name mismatch/);
    reject(s => { s.objects[1].id = s.objects[0].id; }, /Source mesh reused/);
    reject(s => { s.objects[0].enabled = false; }, /source mesh unavailable/);
  });

  it('refuses shifted, nonfinite and inverted source bounds', () => {
    reject(s => { s.objects[0].boundsMm.min[0] += 5; s.objects[0].boundsMm.max[0] += 5; }, /fixture centre differs/);
    reject(s => { s.objects[0].boundsMm.min[1] = NaN; }, /finite/);
    reject(s => { s.objects[0].boundsMm.max[2] = Infinity; }, /finite/);
    reject(s => { s.objects[0].boundsMm.min[0] = s.objects[0].boundsMm.max[0] + 1; }, /Inverted source bounds/);
  });

  it('refuses wrong body size even when the stable ID, source name and AABB centre match', () => {
    reject(s => { s.objects[0].boundsMm.min[0] -= 500; s.objects[0].boundsMm.max[0] += 500; });
    reject(s => {
      const b = s.objects[2].boundsMm, y = (b.min[1] + b.max[1]) / 2;
      b.min[1] = y; b.max[1] = y;
    });
  });

  it('refuses invalid geometry/light vectors, nonfinite power and inverted cones', () => {
    reject(s => { s.exteriorLighting.fixtures[0].geometry.bodyCenterPlanMm[0] = NaN; }, /plan point/);
    reject(s => { s.exteriorLighting.fixtures[0].light.positionPlanMm[1] = Infinity; }, /plan point/);
    reject(s => { s.exteriorLighting.fixtures[0].light.directionPlan = [0, -2, 0]; }, /normalized/);
    reject(s => { s.exteriorLighting.fixtures[0].light.directionPlan = [0, NaN, 0]; }, /light direction/);
    reject(s => { s.exteriorLighting.fixtures[0].light.nominalConeLumens = Infinity; }, /lumens/);
    reject(s => { s.exteriorLighting.fixtures[0].light.nominalConeLumens = 0; }, /lumens/);
    reject(s => { s.exteriorLighting.fixtures[0].light.temperatureK = NaN; }, /temperature/);
    reject(s => { s.exteriorLighting.fixtures[0].light.innerConeHalfAngleDeg = 60; }, /spotlight half angles/);
    reject(s => { s.exteriorLighting.fixtures[0].light.outerConeHalfAngleDeg = Infinity; }, /spotlight half angles/);
    reject(s => { s.exteriorLighting.fixtures[0].light.sourceRadiusMm = Infinity; }, /source radius/);
    reject(s => { s.exteriorLighting.fixtures[0].light.attenuationRadiusMm = 1; });
  });
});
