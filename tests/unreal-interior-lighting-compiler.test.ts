import { describe, expect, it } from 'vitest';
import { INTERIOR_LIGHTING } from '../lib/twin-interior-lighting';
import { SCENE_CENTER_MM } from '../lib/twin-render-frame';
import { buildInteriorLighting } from '../scripts/unreal/interior-lighting.mjs';

function capture() {
  return {
    units: 'millimetres', objSha256: 'ab'.repeat(32), sceneCenterMm: SCENE_CENTER_MM,
    interiorLighting: structuredClone(INTERIOR_LIGHTING),
    objects: INTERIOR_LIGHTING.fixtures.map((fixture, index) => {
      const [x, y, z] = fixture.geometry.bodyCenterPlanMm;
      const center = [x - SCENE_CENTER_MM.x, y - SCENE_CENTER_MM.y, z];
      return {
        id: `DOM_${50000 + index}`, name: fixture.geometry.sourceName,
        metadata: { interiorLightId: fixture.id }, enabled: true, instances: 1, triangles: 12,
        boundsMm: {
          min: center.map((n, i) => n - fixture.geometry.dimensionsMm[i] / 2),
          max: center.map((n, i) => n + fixture.geometry.dimensionsMm[i] / 2),
        },
      };
    }),
  };
}

describe('native interior lighting compiler', () => {
  it('exports both authored kitchen sources independently of mesh order and converts units once', () => {
    const scene = capture(); scene.objects.reverse();
    const before = structuredClone(scene);
    const result = buildInteriorLighting(scene, 'cd'.repeat(32));
    expect(result.fixtures).toHaveLength(2);
    for (const [index, fixture] of result.fixtures.entries()) {
      const original = INTERIOR_LIGHTING.fixtures[index];
      expect(fixture.id).toBe(original.id);
      expect(fixture.sourceTag).toBe(scene.objects.find(mesh => mesh.metadata.interiorLightId === original.id)!.id);
      expect(fixture.sourceWidthCm).toBe(original.light.sourceWidthMm / 10);
      expect(fixture.positionCm[2]).toBe(original.light.positionPlanMm[2] / 10);
      expect(fixture.lumens).toBe(original.light.lumens);
      expect(fixture.direction).toEqual([0, 0, -1]);
    }
    expect(scene).toEqual(before);
  });

  it('rejects missing and duplicate bodies, shifted geometry, invalid power and emitter positions', () => {
    const changes: ((scene: ReturnType<typeof capture>) => void)[] = [
      scene => { scene.objects.pop(); },
      scene => { scene.objects[1].metadata.interiorLightId = scene.objects[0].metadata.interiorLightId; },
      scene => { scene.objects[0].boundsMm.min[0] += 30; scene.objects[0].boundsMm.max[0] += 30; },
      scene => { Reflect.set(scene.interiorLighting.fixtures[1].light, 'lumens', NaN); },
      scene => { Reflect.set(scene.interiorLighting.fixtures[0].light, 'positionPlanMm', [1, 2, 3]); },
      scene => { Reflect.set(scene.interiorLighting.fixtures[1], 'id', scene.interiorLighting.fixtures[0].id); },
    ];
    for (const change of changes) {
      const scene = capture(); change(scene);
      expect(() => buildInteriorLighting(scene, 'cd'.repeat(32))).toThrow();
    }
  });
});
