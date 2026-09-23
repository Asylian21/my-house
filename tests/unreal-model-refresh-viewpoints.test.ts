import { describe, expect, it } from 'vitest';
import { buildModelRefreshViewpoints, MODEL_CAMERA_SOURCES } from '../scripts/unreal/model-refresh-viewpoints.mjs';
import { ACTIVE_DESIGN } from '../lib/twin-design-selection';
import { LIVING_LAYOUTS, livingWalkArrival } from '../lib/twin-living-layouts';
import { KITCHEN_DESIGN } from '../lib/twin-interior';
import { SCENE_CENTER_MM } from '../lib/twin-render-frame';

function fixture(origin = SCENE_CENTER_MM) {
  const record = (sourceId: string, rect: { x0: number; y0: number; x1: number; y1: number }, z0: number, z1: number) => ({
    id: sourceId === MODEL_CAMERA_SOURCES.sofa ? 'DOM_91234' : 'DOM_98765', sourceId, enabled: true,
    boundsMm: { min: [rect.x0 - origin.x, rect.y0 - origin.y, z0], max: [rect.x1 - origin.x, rect.y1 - origin.y, z1] },
  });
  const scene = { units: 'millimetres', coordinateSystem: 'right-handed Z-up',
    activeDesign: { variant: 'C', ...ACTIVE_DESIGN }, sceneCenterMm: origin,
    objects: [record(MODEL_CAMERA_SOURCES.hob, KITCHEN_DESIGN.hobRectMm, 900, 905),
      record(MODEL_CAMERA_SOURCES.sofa, LIVING_LAYOUTS.B.fitout.sofa.mainRectMm, 140, 240)] };
  const viewpoints = { coordinateSystem: 'unreal-centimeters', defaultView: 'street', sun: { dayLux: 80000 },
    views: [{ id: 'interior', label: 'Obývačka', eyeCm: [1110, -440, 165], targetCm: [630, -300, 165],
      horizontalFovDegrees: 76.09408506365219, source: 'legacy-camera' },
    { id: 'street', label: 'Ulica', eyeCm: [-1001, 2190, 180], targetCm: [100, 400, 180],
      horizontalFovDegrees: 65, source: 'source-camera' }] };
  return { scene, viewpoints };
}

describe('current model kitchen camera', () => {
  it('uses the actual B walking arrival and rear hob while preserving unrelated viewpoints and inputs', () => {
    const { scene, viewpoints } = fixture();
    const before = structuredClone({ scene, viewpoints });
    const result = buildModelRefreshViewpoints(scene, viewpoints);
    const interior = result.views.find(view => view.id === 'interior')!;
    const arrival = livingWalkArrival('B')!.standing;
    expect(interior.eyeCm).toEqual([(arrival.x - SCENE_CENTER_MM.x) / 10, -(arrival.y - SCENE_CENTER_MM.y) / 10, 165]);
    const hob = KITCHEN_DESIGN.hobRectMm;
    expect(interior.targetCm).toEqual([((hob.x0 + hob.x1) / 2 - SCENE_CENTER_MM.x) / 10,
      -((hob.y0 + hob.y1) / 2 - SCENE_CENTER_MM.y) / 10, 110]);
    expect(interior.label).toBe('Kuchyňa');
    expect(interior.horizontalFovDegrees).toBe(viewpoints.views[0].horizontalFovDegrees);
    expect(interior.presentation.derivation.sourceObjects.sofa.objectId).toBe('DOM_91234');
    expect(result.views[1]).toEqual(viewpoints.views[1]);
    expect(result.sun).toEqual(viewpoints.sun);
    expect(result.defaultView).toBe(viewpoints.defaultView);
    expect({ scene, viewpoints }).toEqual(before);
  });

  it('converts a different scene origin exactly once and follows measured source motion', () => {
    const { scene, viewpoints } = fixture({ x: 16000, y: 12000 });
    const sofa = scene.objects.find(object => object.sourceId === MODEL_CAMERA_SOURCES.sofa)!;
    sofa.boundsMm.min[0] += 250; sofa.boundsMm.max[0] += 250;
    const result = buildModelRefreshViewpoints(scene, viewpoints);
    const arrival = livingWalkArrival('B')!.standing;
    expect(result.views[0].eyeCm).toEqual([(arrival.x + 250 - 16000) / 10, -(arrival.y - 12000) / 10, 165]);
    expect(result.views[0].presentation.derivation.eyePlanMm).toEqual([arrival.x + 250, arrival.y, 1650]);
  });

  it('rejects stale design, missing or duplicate sources, invalid bounds and ambiguous interior presets', () => {
    const mutations = [
      (s: ReturnType<typeof fixture>) => { s.scene.activeDesign.livingLayout = 'A'; },
      (s: ReturnType<typeof fixture>) => { s.scene.objects.pop(); },
      (s: ReturnType<typeof fixture>) => { s.scene.objects.push(structuredClone(s.scene.objects[0])); },
      (s: ReturnType<typeof fixture>) => { s.scene.objects[0].enabled = false; },
      (s: ReturnType<typeof fixture>) => { s.scene.objects[0].boundsMm.min[0] = NaN; },
      (s: ReturnType<typeof fixture>) => { s.scene.objects[1].boundsMm.max[0] = s.scene.objects[1].boundsMm.min[0]; },
      (s: ReturnType<typeof fixture>) => { s.viewpoints.views.push(structuredClone(s.viewpoints.views[0])); },
    ];
    for (const mutate of mutations) {
      const candidate = fixture(); mutate(candidate);
      expect(() => buildModelRefreshViewpoints(candidate.scene, candidate.viewpoints)).toThrow();
    }
  });
});
