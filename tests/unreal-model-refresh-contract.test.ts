import { describe, expect, it } from 'vitest';
import { EXPECTED_MODEL, MODEL_SOURCE_NAMES, OAK_FRONT_NAMES, verifyModelRefresh } from '../scripts/unreal/model-refresh-contract.mjs';
import { KITCHEN_DESIGN, KITCHEN_ISLAND, KITCHEN_RUN } from '../lib/twin-interior';
import { HOUSE } from '../lib/twin-active-house';
import { ACTIVE_DESIGN } from '../lib/twin-design-selection';
import { SCENE_CENTER_MM } from '../lib/twin-render-frame';

type Box = { x0: number; x1: number; y0: number; y1: number; z0: number; z1: number };
function fixture() {
  const objects: { id: string; sourceId: string; name: string; enabled: boolean;
    boundsMm: { min: number[]; max: number[] }; materialSlots: string[] }[] = [];
  const add = (name: string, b: Box, slot = 'renumbered-stone') => objects.push({
    id: `DOM_${70000 + objects.length}`, sourceId: name, name, enabled: true,
    boundsMm: { min: [b.x0 - SCENE_CENTER_MM.x, b.y0 - SCENE_CENTER_MM.y, b.z0],
      max: [b.x1 - SCENE_CENTER_MM.x, b.y1 - SCENE_CENTER_MM.y, b.z1] }, materialSlots: [slot],
  });
  const top = (rect: Omit<Box, 'z0' | 'z1'>): Box => ({ ...rect, z0: 880, z1: KITCHEN_RUN.counterHeightMm });
  add(MODEL_SOURCE_NAMES.island + '_merged', top(KITCHEN_ISLAND.worktopRectMm));
  add(MODEL_SOURCE_NAMES.back, top(KITCHEN_DESIGN.backWorktopRectMm));
  add(MODEL_SOURCE_NAMES.right, top(KITCHEN_ISLAND.eastReturnWorktopRectMm));
  add(MODEL_SOURCE_NAMES.sink, { ...KITCHEN_DESIGN.sinkBowlRectMm, z0: 700, z1: 703 });
  add(MODEL_SOURCE_NAMES.hob, { ...KITCHEN_DESIGN.hobRectMm, z0: 900, z1: 905 });
  add(MODEL_SOURCE_NAMES.oven, { x0: KITCHEN_RUN.ovenCenterXmm - KITCHEN_DESIGN.oven.widthMm / 2,
    x1: KITCHEN_RUN.ovenCenterXmm + KITCHEN_DESIGN.oven.widthMm / 2,
    y0: KITCHEN_RUN.rectMm.y1, y1: KITCHEN_RUN.rectMm.y1 + 12,
    z0: KITCHEN_DESIGN.oven.bottomMm, z1: KITCHEN_DESIGN.oven.bottomMm + KITCHEN_DESIGN.oven.heightMm });
  add(MODEL_SOURCE_NAMES.dishwasher, { ...KITCHEN_DESIGN.dishwasherRectMm,
    x0: KITCHEN_DESIGN.dishwasherRectMm.x0 + 2, x1: KITCHEN_DESIGN.dishwasherRectMm.x1 - 2,
    z0: 120, z1: 860 }, 'renumbered-oak');
  for (const name of OAK_FRONT_NAMES.filter(name => name !== MODEL_SOURCE_NAMES.dishwasher))
    add(name, top(KITCHEN_ISLAND.worktopRectMm), 'renumbered-oak');
  for (const [opening, prefix] of [
    [HOUSE.facades.front.openings.find(o => o.id === 'FRONT-07')!, 'Výplň otvoru FRONT-07 · D1.1.002'],
    [HOUSE.facades.garden.openings.find(o => o.id === 'GARDEN-02')!, 'Terasové presklenie 2200 · D1.1.002'],
  ] as const) {
    const width = 'frameWidthMm' in opening ? opening.frameWidthMm! : 78;
    const body = { x0: opening.startXmm, x1: opening.startXmm + opening.widthMm,
      y0: 3000, y1: 3100, z0: opening.sillMm, z1: opening.sillMm + opening.heightMm };
    add(`${prefix} · rám ľavý stĺpik`, { ...body, x1: body.x0 + width });
    add(`${prefix} · rám pravý stĺpik`, { ...body, x0: body.x1 - width });
    add(`${prefix} · rám horný priečnik`, { ...body, x0: body.x0 + width, x1: body.x1 - width, z0: body.z1 - width });
  }
  return { units: 'millimetres', activeDesign: { variant: 'C', ...ACTIVE_DESIGN }, sceneCenterMm: SCENE_CENTER_MM,
    house: structuredClone(HOUSE), objects, materials: {
      'renumbered-stone': { texture: '/assets/textures/stone-dark-albedo.jpg', color: [.1, .1, .1], metallic: 0 },
      'renumbered-oak': { texture: '/assets/textures/living-natural-oak-albedo.jpg', color: [.7, .6, .5], metallic: 0 },
    } };
}

describe('Unreal model refresh semantic gate', () => {
  it('matches the live kitchen and opening source contracts without relying on old ordinal IDs', () => {
    expect(EXPECTED_MODEL.island).toMatchObject(KITCHEN_ISLAND.worktopRectMm);
    expect(EXPECTED_MODEL.sink).toMatchObject(KITCHEN_DESIGN.sinkBowlRectMm);
    expect(EXPECTED_MODEL.hob).toEqual(KITCHEN_DESIGN.hobRectMm);
    expect(EXPECTED_MODEL.sidePassageMm).toBe(KITCHEN_ISLAND.sidePassageMm);
    expect(EXPECTED_MODEL.workAisleMm).toBe(KITCHEN_ISLAND.workAisleMm);
    expect(HOUSE.facades.front.openings.find(o => o.id === 'FRONT-07')).toMatchObject(EXPECTED_MODEL.office);
    expect(HOUSE.facades.garden.openings.find(o => o.id === 'GARDEN-02')).toMatchObject(EXPECTED_MODEL.portal);
    const scene = fixture(); scene.objects.reverse();
    const report = verifyModelRefresh(scene);
    expect(report.kitchen.islandDimensionsMm).toEqual([2640, 920, 20]);
    expect(report.kitchen.checkedOakElevations).toBe(8);
    expect(report.windows.office.measured.x0).toBe(24442);
  });

  it('rejects stale selection, geometry, materials, window size and ambiguous source names', () => {
    const mutations = [
      (s: ReturnType<typeof fixture>) => { s.activeDesign.heatingLayout = 'A'; },
      (s: ReturnType<typeof fixture>) => { s.objects[0].boundsMm.max[0] += 100; },
      (s: ReturnType<typeof fixture>) => { s.objects.find(o => o.sourceId === MODEL_SOURCE_NAMES.sink)!.boundsMm.min[1] -= 500; },
      (s: ReturnType<typeof fixture>) => { s.materials['renumbered-stone'].color = [.8, .8, .8]; },
      (s: ReturnType<typeof fixture>) => { s.materials['renumbered-oak'].texture = '/foreign.jpg'; },
      (s: ReturnType<typeof fixture>) => { s.objects.push(structuredClone(s.objects[0])); },
      (s: ReturnType<typeof fixture>) => { Reflect.set(s.house.facades.garden.openings.find(o => o.id === 'GARDEN-02')!, 'widthMm', 2500); },
    ];
    for (const mutate of mutations) {
      const scene = fixture(); mutate(scene);
      expect(() => verifyModelRefresh(scene)).toThrow();
    }
  });
});
