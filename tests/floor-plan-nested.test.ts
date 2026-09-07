import { describe, expect, it } from 'vitest';
import { area, createConcept, DEFAULT_CONCEPT as BASE_DEFAULT, rect } from '../lib/floor-plan-concept';
import { INTERIOR_DOORS, INTERIOR_ROOMS, INTERIOR_WALLS } from '../lib/twin-interior';
import { HOUSE } from '../lib/twin-site';

const DEFAULT_CONCEPT={...BASE_DEFAULT,layout:'nested' as const};
import { intersects, contains, check, opening, swingHits, openLeaf, walkingPath } from './floor-plan-geometry';

describe('nested bedroom, closet and garage study C', () => {
  it('defaults to a compact bath, separate closet and useful garage storage recess', () => {
    const m = createConcept(DEFAULT_CONCEPT);
    expect(m.isNested).toBe(true);
    expect(m.privateHallArea).toBe(0);
    expect(m.bedroomArea).toBeCloseTo(12.0239, 6);
    expect(m.bathroomArea).toBeCloseTo(5.2941, 6);
    expect(area([m.dressing!])).toBeCloseTo(3.74, 6);
    expect(area([m.garageBay!])).toBeCloseTo(3.15, 6);
    expect(area(m.rooms.find(r => r.number === '1.12')!.rectsMm)).toBeCloseTo(23.59501, 6);
    expect(m.dressingAisle).toBe(1000);
    expect(m.storageLength).toBe(2400);
    expect(m.sideClearance).toBe(657);
    expect(m.footClearance).toBe(1660);
    expect(m.rooms.find(r => r.number === '1.10')!.rectsMm).toHaveLength(1);
    expect(m.doors.find(d => d.id === 'C-HALL-BATH')?.fromRoomId).toBe('ROOM-1-02');
    expect(m.doors.some(d => d.id === 'C-HALL-BED')).toBe(false);
    expect(m.doors.find(d => d.id === 'C-PRIVATE-BED')?.widthMm).toBe(800);
  });

  it('does not mutate the source model and tracks every replaced bearing wall', () => {
    const before = JSON.stringify({ HOUSE, INTERIOR_ROOMS, INTERIOR_WALLS, INTERIOR_DOORS });
    for (const expansion of [0, 600]) for (const garageConnected of [false, true]) {
      const m = createConcept({ ...DEFAULT_CONCEPT, expansion, garageConnected });
      expect(m.structuralChanges.map(w => w.id)).toEqual(['IW-GARAGE-NORTH', 'IW-GARAGE-LOGGIA']);
      for (const source of INTERIOR_WALLS.filter(w => w.role === 'LOAD_BEARING')) {
        const replaced = m.structuralChanges.some(w => w.id === source.id);
        expect(m.walls.find(w => w.id === source.id)?.rectMm).toEqual(replaced ? undefined : source.rectMm);
      }
    }
    expect(JSON.stringify({ HOUSE, INTERIOR_ROOMS, INTERIOR_WALLS, INTERIOR_DOORS })).toBe(before);
  });

  it('keeps every combination of spatial controls disjoint and doors, fixtures and windows clear', () => {
    let combinations = 0;
    for (let expansion = 0; expansion <= 600; expansion += 50)
      for (let garageBayWidth = 1000; garageBayWidth <= 1700; garageBayWidth += 50)
        for (let nestedClosetDepth = 1600; nestedClosetDepth <= 1900; nestedClosetDepth += 50)
          for (const garageConnected of [false, true]) for (const gardenRecess of [false, true]) {
            const m = createConcept({ ...DEFAULT_CONCEPT, expansion, garageBayWidth, nestedClosetDepth, garageConnected, gardenRecess });
            const context = `expansion=${expansion}, bay=${garageBayWidth}, closet=${nestedClosetDepth}, garage=${garageConnected}, loggia=${gardenRecess}`;
            const floors = m.rooms.flatMap(room => room.rectsMm.map(r => ({ r, room: room.number })));
            for (let i = 0; i < floors.length; i++) {
              const a = floors[i];
              check(a.r.x1 > a.r.x0 && a.r.y1 > a.r.y0, `Invalid floor ${a.room}: ${context}`);
              for (let j = i + 1; j < floors.length; j++) check(!intersects(a.r, floors[j].r), `Overlapping floors ${a.room}/${floors[j].room}: ${context}`);
              for (const wall of m.walls) check(!intersects(a.r, wall.rectMm), `Wall ${wall.id} crosses ${a.room}: ${context}`);
            }
            for (const bank of m.storageRuns) {
              check(contains(m.dressing!, bank), `Storage outside closet: ${context}`);
              check(bank.x1 - bank.x0 === 600 && bank.y1 > bank.y0, `Invalid storage: ${context}`);
            }
            check(m.storageRuns[1].x0 - m.storageRuns[0].x1 === 1000, `Closet aisle narrowed: ${context}`);
            check(m.storageLength === nestedClosetDepth * 2 - (garageConnected ? 1000 : 0), `Storage frontage wrong: ${context}`);
            for (const shelf of m.garageShelves) check(contains(m.garageBay!, shelf), `Shelf outside garage recess: ${context}`);
            const bath = m.rooms.find(r => r.number === '1.11')!.rectsMm[0];
            const furniture = [m.bed, ...m.storageRuns, ...m.garageShelves, ...Object.values(m.fixtures)];
            for (const fixture of Object.values(m.fixtures)) check(contains(bath, fixture), `Fixture outside bathroom: ${context}`);
            for (let i = 0; i < furniture.length; i++) for (let j = i + 1; j < furniture.length; j++) check(!intersects(furniture[i], furniture[j]), `Overlapping furniture: ${context}`);
            for (const d of m.doors.filter(d => d.id.startsWith('C-'))) {
              check(m.walls.every(w => !intersects(w.rectMm, opening(d))), `Blocked ${d.id} aperture: ${context}`);
              if (d.motion !== 'POCKET_SLIDING') check(furniture.every(r => !swingHits(d, r)), `${d.id} sweep hits furniture: ${context}`);
            }
            const pocket = m.doors.find(d => d.id === 'C-BED-CLOSET')!;
            const stored = rect(pocket.startMm + pocket.pocketTravelMm!, pocket.wallSpanMm[0], pocket.startMm + pocket.pocketTravelMm! + pocket.leafWidthMm, pocket.wallSpanMm[1]);
            check(m.walls.some(w => contains(w.rectMm, stored)), `Pocket leaf exceeds wall: ${context}`);
            check(m.frontWindowStart >= m.bathLeft && m.frontWindowStart + 750 <= m.bathRight, `Bathroom window crosses wall: ${context}`);
            check(m.garageWindowStart > 10240 && m.garageWindowStart + 1250 < m.garageBay!.x1, `Garage window crosses door/divider: ${context}`);
            check(m.suiteRight + 140 < 15840, `Partition blocks child garden glazing: ${context}`);
            check(m.bed.y1 < 10699 && m.bed.x1 - m.bed.x0 === 2200, `Bed blocks facade or changes length: ${context}`);
            combinations++;
          }
    expect(combinations).toBe(5460);
  }, 15000);

  it('keeps every bed-width and closet-depth step inside the bedroom and reports tight limits', () => {
    for (let nestedClosetDepth = 1600; nestedClosetDepth <= 1900; nestedClosetDepth += 50)
      for (let bedWidth = 1600; bedWidth <= 2200; bedWidth += 50) {
        const m = createConcept({ ...DEFAULT_CONCEPT, nestedClosetDepth, bedWidth });
        const sleeping = m.rooms.find(r => r.number === '1.10')!.rectsMm[0];
        expect(contains(sleeping, m.bed)).toBe(true);
        expect(m.bed.y1 - m.bed.y0).toBe(bedWidth);
        expect(m.sideClearance).toBe(m.bed.y0 - sleeping.y0);
        expect(sleeping.y1 - m.bed.y1 - m.sideClearance).toBeLessThanOrEqual(1);
      }
    expect(createConcept({ ...DEFAULT_CONCEPT, nestedClosetDepth: 1900, bedWidth: 2200 }).sideClearance).toBe(357);
    expect(createConcept({ ...DEFAULT_CONCEPT, garageBayWidth: 1000, expansion: 600 }).bathroomArea).toBeCloseTo(7.6041, 6);
  });

  it('trades garage access for one metre of closet frontage and keeps terrace retention measurable', () => {
    const on = createConcept(DEFAULT_CONCEPT), off = createConcept({ ...DEFAULT_CONCEPT, garageConnected: false, gardenRecess: true });
    expect(on.doors.some(d => d.id === 'C-GARAGE-CLOSET')).toBe(true);
    expect(off.doors.some(d => d.id === 'C-GARAGE-CLOSET')).toBe(false);
    expect(off.storageLength - on.storageLength).toBe(1000);
    expect(off.garageDepth).toBe(5245);
    expect(off.convertedTerraceArea).toBe(0);
    expect(area(off.rooms.find(r => r.number === '1.12')!.rectsMm)).toBeCloseTo(23.59501, 6);
    expect(off.walls.some(w => contains(w.rectMm, rect(10842, 5844, 11143, 6644)))).toBe(true);
  });

  it('routes a 440 mm disc to the bath through the new bedroom door, with the closet excluded', () => {
    for (const expansion of [0, 600]) for (const garageBayWidth of [1000, 1700]) for (const nestedClosetDepth of [1600, 1900]) {
      const m = createConcept({ ...DEFAULT_CONCEPT, expansion, garageBayWidth, nestedClosetDepth, bedWidth: 1800 });
      const bathDoor = m.doors.find(d => d.id === 'C-HALL-BATH')!;
      const bedroomDoor = m.doors.find(d => d.id === 'C-PRIVATE-BED')!;
      const floors = [...m.rooms.filter(r => ['1.02', '1.10', '1.11'].includes(r.number)).flatMap(r => r.rectsMm), opening(bedroomDoor), opening(bathDoor)];
      const obstacles = [m.bed, ...m.storageRuns, ...Object.values(m.fixtures), openLeaf(bathDoor), openLeaf(bedroomDoor)];
      const target: [number, number] = [Math.round((m.bathLeft + m.bathRight) / 100) * 50, 4550];
      expect(walkingPath(floors, obstacles, [14000, 9000], target), `Direct bath route, expansion=${expansion}, bay=${garageBayWidth}, closet=${nestedClosetDepth}`).toBe(true);
      expect(walkingPath(floors.filter(r => r !== floors[floors.length - 1]), obstacles, [14000, 9000], target), 'Closing the bath doorway must break the route').toBe(false);
      expect(walkingPath(floors.filter(r => r !== floors[floors.length - 2]), obstacles, [14000, 9000], target), 'Closing the new bedroom doorway must break the private route').toBe(false);
      const hallFloors=[...m.rooms.filter(r => ['1.02','1.11'].includes(r.number)).flatMap(r => r.rectsMm),opening(bathDoor)];
      const hallStart:[number,number]=[Math.round((m.suiteRight+1000)/50)*50,7100];
      expect(walkingPath(hallFloors,obstacles,hallStart,target),'Hall to bathroom remains open with bedroom excluded').toBe(true);
      expect(walkingPath(hallFloors,obstacles,hallStart,[14000,9000]),'Bedroom stays private behind its door').toBe(false);
    }
  }, 15000);

  it('routes a 440 mm disc from the bedroom to the closet with the actual 1800 mm bed', () => {
    for (const garageConnected of [false, true]) for (const nestedClosetDepth of [1600, 1700, 1900]) {
      const m = createConcept({ ...DEFAULT_CONCEPT, garageConnected, nestedClosetDepth, bedWidth: 1800 });
      const closetDoor = m.doors.find(d => d.id === 'C-BED-CLOSET')!;
      const floors = [...m.rooms.filter(r => ['1.10', '1.14'].includes(r.number)).flatMap(r => r.rectsMm), opening(closetDoor)];
      expect(walkingPath(floors, [m.bed, ...m.storageRuns], [14000, 9000], [12250, 6500]), `Closet route, garage=${garageConnected}, depth=${nestedClosetDepth}`).toBe(true);
    }
  }, 15000);
});
