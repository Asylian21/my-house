import { describe, expect, it } from 'vitest';
import { HOUSE } from '../lib/twin-active-house';
import { GARAGE_DEPTH_REVISION, HOUSE as baseline } from '../lib/twin-site';
import { ACTIVE_LAYOUT_ID, INTERIOR_ROOMS } from '../lib/twin-interior';

describe('active export room-area authority', () => {
  it('serializes current C area from every room rectangle, including garage', () => {
    const serialized = JSON.parse(JSON.stringify({house: HOUSE, layoutId: ACTIVE_LAYOUT_ID, interior: {rooms: INTERIOR_ROOMS}}));
    const expected = serialized.interior.rooms.reduce((sum: number, room: typeof INTERIOR_ROOMS[number]) => sum + room.rectsMm.reduce((roomSum, r) => roomSum + (r.x1-r.x0)*(r.y1-r.y0)/1e6, 0), 0);
    expect(serialized.house.floorAreaM2).toBeCloseTo(expected, 9);
    // 1.625 m² less than before the three 300 mm bearing walls were introduced,
    // then +0.459964 m² as the central hall gains 59 mm from its 140 mm south
    // partition, then +0.00712 m² as the centred hall narrows to 1 099 mm,
    // then −0.46528 m² as the kitchen's back wall becomes 300 mm load-bearing
    // masonry growing 160 mm into the 2 908 mm kitchen bay (12. 9. 2026), then
    // −0.17902 m² as that wall runs to the east facade: the technical room's
    // 1 680 × 699 mm protrusion (−1.17432 m²) becomes 1 850 × 538 mm of kitchen
    // bay (+0.9953 m²), the rest is the new 860 mm wall piece and the door.
    // +0.005855 m² when the 144 mm laundry return aligns with the 139 mm WC wall.
    expect(expected).toBeCloseTo(179.629458, 9);
    expect(serialized.house.floorAreaAuthority).toEqual({kind: 'ACTIVE_ROOM_RECTANGLE_SUM', layoutId: serialized.layoutId, source: 'lib/twin-interior.ts:INTERIOR_ROOMS', includesGarage: true});
    expect(serialized.interior.rooms.some((r: typeof INTERIOR_ROOMS[number]) => r.id === 'ROOM-1-12')).toBe(true);
  });

  it('retains the historical room-legend method and revision without overwriting baseline', () => {
    expect(HOUSE.historicalFloorArea).toEqual({areaM2: 179.023, originalD1LegendAreaM2: 175.15, kind: 'D1_ROOM_LEGEND_PLUS_CLIENT_GARAGE_REVISION', sourceId: GARAGE_DEPTH_REVISION.sourceId});
    expect(baseline.floorAreaM2).toBe(179.023);
    expect(GARAGE_DEPTH_REVISION.revisedGarageAreaM2).toBe(29.023);
    expect(HOUSE.floorAreaM2).not.toBe(HOUSE.historicalFloorArea.areaM2);
    for (const key of ['footprintMm','originMm','lowerBar','wing','roof','porches','derivedFootprintAreaM2'] as const) expect(HOUSE[key]).toEqual(baseline[key]);
  });
});
