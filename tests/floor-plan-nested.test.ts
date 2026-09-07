import { describe, expect, it } from 'vitest';
import { area, createConcept, DEFAULT_CONCEPT as BASE_DEFAULT, DEFAULT_NESTED_CONCEPT, normalizeConcept, rect } from '../lib/floor-plan-concept';
import { INTERIOR_DOORS, INTERIOR_ROOMS, INTERIOR_WALLS } from '../lib/twin-interior-baseline';
import { HOUSE } from '../lib/twin-site';

const DEFAULT_CONCEPT=DEFAULT_NESTED_CONCEPT;
import { intersects, contains, check, opening, swingHits, openLeaf, walkingPath } from './floor-plan-geometry';

describe('nested bedroom, closet and garage study C', () => {
  it('defaults to a compact bath, separate closet and useful garage storage recess', () => {
    const m = createConcept(DEFAULT_CONCEPT);
    expect(m.isNested).toBe(true);
    expect(m.privateHallArea).toBe(0);
    expect(m.bedroomArea).toBeCloseTo(11.41788, 6);
    expect(m.bathroomArea).toBeCloseTo(5.2941, 6);
    expect(area([m.dressing!])).toBeCloseTo(4.0854, 6);
    expect(area([m.garageBay!])).toBeCloseTo(3.15, 6);
    expect(area(m.rooms.find(r => r.number === '1.12')!.rectsMm)).toBeCloseTo(23.59501, 6);
    expect(m.dressingAisle).toBe(1000);
    expect(m.storageLength).toBe(3714);
    expect(m.settings.garageConnected).toBe(false);
    expect(normalizeConcept({layout:'nested'}).garageConnected).toBe(false);
    expect(m.doors.some(d=>d.id==='C-GARAGE-CLOSET')).toBe(false);
    expect(m.sideClearance).toBe(579);
    expect(m.footClearance).toBe(1660);
    expect(m.rooms.find(r => r.number === '1.10')!.rectsMm).toHaveLength(1);
    expect(m.doors.find(d => d.id === 'C-HALL-BATH')?.fromRoomId).toBe('ROOM-1-02');
    expect(m.doors.some(d => d.id === 'C-HALL-BED')).toBe(false);
    expect(m.doors.find(d => d.id === 'C-PRIVATE-BED')?.widthMm).toBe(800);
  });

  it('balances child rooms around 16 m², excludes corridor cabinets and widens the entry', () => {
    const baseline = createConcept(DEFAULT_CONCEPT);
    expect(baseline.kidStreetArea).toBeCloseTo(15.882063, 6);
    expect(baseline.kidGardenArea).toBeCloseTo(15.967284, 6);
    expect(baseline.entryArea).toBeCloseTo(6.321929, 6);
    expect(baseline.entryClearArea).toBeCloseTo(4.607529, 6);
    const originalOffice = INTERIOR_ROOMS.find(r => r.number === '1.04')!;
    expect(baseline.officeArea).toBeCloseTo(12.337492, 6);
    expect(baseline.officeArea-area(originalOffice.rectsMm)).toBeCloseTo(1.2324, 6);
    expect(baseline.rooms.find(r=>r.number==='1.04')!.rectsMm[0].x0).toBe(23542);
    expect(baseline.rooms.find(r=>r.number==='1.04')!.rectsMm[1]).toEqual(originalOffice.rectsMm[1]);
    expect(baseline.walls.find(w=>w.id==='C-ENTRY-OFFICE-EAST')!.rectMm).toEqual(rect(23339,3504,23542,5201));
    expect(baseline.walls.find(w=>w.id==='C-ENTRY-OFFICE-RETURN')!.rectMm).toEqual(rect(22842,5201,23542,5400));
    const originalEntry = INTERIOR_ROOMS.find(r => r.number === '1.01')!;
    expect(baseline.entryClearArea - area(originalEntry.rectsMm)).toBeCloseTo(0.456667, 6);
    for (let expansion = 0; expansion <= 600; expansion += 50) {
      const m = createConcept({ ...DEFAULT_CONCEPT, expansion });
      expect(m.settings.expansion).toBe(Math.min(expansion, 100));
      const children = m.rooms.filter(r => ['1.08', '1.09'].includes(r.number));
      for (const child of children) {
        expect(area(child.rectsMm)).toBeGreaterThanOrEqual(15.5);
        expect(area(child.rectsMm)).toBeLessThanOrEqual(16.5);
      }
      expect(Math.abs(m.kidStreetArea - m.kidGardenArea)).toBeLessThanOrEqual(0.5);
      expect(m.kidStreetArea).toBe(area(children[0].rectsMm));
      expect(m.kidGardenArea).toBe(area(children[1].rectsMm));
      expect(contains(children[0].rectsMm[0], m.streetKidDesk)).toBe(true);
      expect(m.builtInCabinets).toHaveLength(3);
      expect(contains(m.rooms.find(r=>r.number==='1.01')!.rectsMm[0],m.entryBench!)).toBe(true);
      expect(contains(children[1].rectsMm[0],m.gardenKidBed)).toBe(true);
      expect(m.builtInCabinets.map(c => c.facing)).toEqual(['EAST', 'EAST', 'EAST']);
      for (const cabinet of m.builtInCabinets) {
        const r = cabinet.rectMm;
        expect(m.rooms.find(room => room.number === cabinet.roomNumber)!.rectsMm.some(floor => contains(floor, r))).toBe(true);
        expect(children.every(room => room.rectsMm.every(floor => !intersects(floor, r)))).toBe(true);
        expect(m.walls.every(wall => !intersects(wall.rectMm, r))).toBe(true);
      }
      expect(m.builtInCabinets.map(c => [c.rectMm.x1-c.rectMm.x0, c.rectMm.y1-c.rectMm.y0])).toEqual([[701,1900],[701,2797],[520+m.settings.expansion,1857]]);
    }
    for (const layout of ['private', 'wardrobe', 'vestibule'] as const) {
      const other = createConcept({ ...BASE_DEFAULT, layout, expansion: 600 });
      expect(other.settings.expansion).toBe(600);
      expect(other.rooms.find(r => r.number === '1.01')!.rectsMm).toEqual(originalEntry.rectsMm);
      expect(other.walls.find(w => w.id === 'IW-BED-108-EAST')!.changed).toBe(false);
    }
  });

  it('keeps the furnished entrance connected to storage, the office and the central hall', () => {
    const m=createConcept(DEFAULT_CONCEPT);
    const entryDoor=m.doors.find(d=>d.id==='DOOR-101-102')!;
    const officeDoor=m.doors.find(d=>d.id==='DOOR-102-104')!;
    expect(entryDoor.motion).toBe('POCKET_SLIDING');
    expect(entryDoor.widthMm).toBe(900);
    expect(entryDoor.pocketDirection).toBe(-1);
    expect(officeDoor.fromRoomId).toBe('ROOM-1-01');
    const northJamb=m.walls.find(w=>w.id==='C-OFFICE-NORTH-JAMB')!.rectMm;
    const office=m.rooms.find(r=>r.number==='1.04')!.rectsMm[1];
    const spine=m.walls.find(w=>w.id==='IW-SPINE-EAST-1')!.rectMm;
    expect(northJamb).toEqual(rect(spine.x1,officeDoor.startMm+officeDoor.widthMm,office.x0,office.y1));
    expect(m.rooms.every(room=>room.rectsMm.every(floor=>!intersects(floor,northJamb)))).toBe(true);
    for (const id of ['C-ENTRY-OFFICE-EAST','C-ENTRY-OFFICE-RETURN']) {
      expect(swingHits(officeDoor,m.walls.find(w=>w.id===id)!.rectMm)).toBe(false);
    }
    const stored=rect(entryDoor.startMm-entryDoor.pocketTravelMm!,6361,entryDoor.startMm-entryDoor.pocketTravelMm!+entryDoor.leafWidthMm,6560);
    expect(m.walls.some(w=>contains(w.rectMm,stored))).toBe(true);
    const floors=[...m.rooms.filter(r=>['1.01','1.02','1.04'].includes(r.number)).flatMap(r=>r.rectsMm),opening(officeDoor),opening(entryDoor)];
    const obstacles=[...m.builtInCabinets.map(c=>c.rectMm),m.entryBench!,openLeaf(officeDoor),stored];
    for (const cabinet of m.builtInCabinets) {
      const r=cabinet.rectMm, approach=rect(r.x1,r.y0,r.x1+1000,r.y1);
      expect(m.rooms.find(room=>room.number===cabinet.roomNumber)!.rectsMm.some(floor=>contains(floor,approach))).toBe(true);
      expect(m.walls.every(w=>!intersects(w.rectMm,approach))).toBe(true);
      expect(m.doors.filter(d=>d.motion!=='POCKET_SLIDING').every(d=>!swingHits(d,approach))).toBe(true);
    }
    for(const point of [[21800,3950],[22000,5800],[23750,5800],[24050,4300]] as [number,number][]) {
      expect(walkingPath(floors,obstacles,[22500,4300],point)).toBe(true);
      expect(walkingPath(floors.slice(0,-1),obstacles,[22500,4300],point)).toBe(true);
    }
    for(const point of [[21250,7100],[22000,9500]] as [number,number][]) {
      expect(walkingPath(floors,obstacles,[22500,4300],point)).toBe(true);
      expect(walkingPath(floors.slice(0,-1),obstacles,[22500,4300],point)).toBe(false);
    }
    const dressingSpace=rect(21640,3554,23140,5054);
    expect(m.rooms.filter(r=>r.number==='1.01').flatMap(r=>r.rectsMm).reduce((sum,r)=>sum+area([rect(Math.max(r.x0,dressingSpace.x0),Math.max(r.y0,dressingSpace.y0),Math.min(r.x1,dressingSpace.x1),Math.min(r.y1,dressingSpace.y1))]),0)).toBeCloseTo(2.25,6);
    expect(obstacles.every(r=>!intersects(r,dressingSpace))).toBe(true);
    expect(m.walls.some(w=>w.id==='IW-ENTRY-TOP-W'||w.id==='IW-ENTRY-TOP-E')).toBe(false);
  });

  it('does not mutate the source model and tracks every replaced bearing wall', () => {
    const before = JSON.stringify({ HOUSE, INTERIOR_ROOMS, INTERIOR_WALLS, INTERIOR_DOORS });
    for (const expansion of [0, 600]) for (const garageConnected of [false, true]) {
      const m = createConcept({ ...DEFAULT_CONCEPT, expansion, garageConnected });
      expect(m.structuralChanges.map(w => w.id)).toEqual(['IW-GARAGE-NORTH', 'IW-GARAGE-LOGGIA', 'IW-BED-108-TOP-E', 'IW-BED-108-EAST', 'IW-ROOM-109-EAST', 'IW-ENTRY-STUDY', 'IW-ENTRY-EAST']);
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
            check(m.storageLength === m.settings.nestedClosetDepth * 2 - (garageConnected ? 1000 : 0), `Storage frontage wrong: ${context}`);
            for (const shelf of m.garageShelves) check(contains(m.garageBay!, shelf), `Shelf outside garage recess: ${context}`);
            const bath = m.rooms.find(r => r.number === '1.11')!.rectsMm[0];
            const furniture = [m.bed, ...m.storageRuns, ...m.garageShelves, ...m.builtInCabinets.map(c=>c.rectMm), m.streetKidDesk, m.entryBench!, rect(18100,3630,19000,5630), m.gardenKidBed, rect(18100,10099,19300,10699), ...Object.values(m.fixtures)];
            for (const fixture of Object.values(m.fixtures)) check(contains(bath, fixture), `Fixture outside bathroom: ${context}`);
            for (let i = 0; i < furniture.length; i++) for (let j = i + 1; j < furniture.length; j++) check(!intersects(furniture[i], furniture[j]), `Overlapping furniture: ${context}`);
            for (const d of m.doors) {
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

  it('keeps every bed width inside the aligned bedroom and reports tight limits', () => {
    for (let nestedClosetDepth = 1600; nestedClosetDepth <= 1900; nestedClosetDepth += 50)
      for (let bedWidth = 1600; bedWidth <= 2200; bedWidth += 50) {
        const m = createConcept({ ...DEFAULT_CONCEPT, nestedClosetDepth, bedWidth });
        const sleeping = m.rooms.find(r => r.number === '1.10')!.rectsMm[0];
        expect(contains(sleeping, m.bed)).toBe(true);
        expect(m.bed.y1 - m.bed.y0).toBe(bedWidth);
        expect(m.sideClearance).toBe(Math.min(m.bed.y0-(m.dressing!.y1+140),sleeping.y1-m.bed.y1));
        expect(sleeping.y1-m.bed.y1-m.sideClearance).toBeLessThanOrEqual(1);
      }
    expect(createConcept({ ...DEFAULT_CONCEPT, nestedClosetDepth: 1900, bedWidth: 2200 }).sideClearance).toBe(379);
    expect(createConcept({ ...DEFAULT_CONCEPT, garageBayWidth: 1000, expansion: 600 }).bathroomArea).toBeCloseTo(6.5541, 6);
  });

  it('keeps the closet, bedroom and child corridor wall aligned even with old depth settings', () => {
    for (let nestedClosetDepth=1600;nestedClosetDepth<=1900;nestedClosetDepth+=50) {
      const m=createConcept({...DEFAULT_CONCEPT,nestedClosetDepth});
      const childWall=m.walls.find(w=>w.id==='B-GARDEN-KID-SOUTH-W')!.rectMm;
      const bedroomDoor=m.doors.find(d=>d.id==='C-PRIVATE-BED')!;
      expect(bedroomDoor.wallSpanMm).toEqual([childWall.y0,childWall.y1]);
      expect(m.doors.find(d=>d.id==='C-BED-CLOSET')!.wallSpanMm).toEqual(bedroomDoor.wallSpanMm);
      for (const id of ['C-BED-PRIVACY-W','C-BED-PRIVACY-E','C-CLOSET-NORTH-W','C-CLOSET-NORTH-E']) {
        const wall=m.walls.find(w=>w.id===id)!.rectMm;
        expect([wall.y0,wall.y1]).toEqual([childWall.y0,childWall.y1]);
      }
      const hall=m.rooms.find(r=>r.number==='1.02')!.rectsMm;
      for (let x=13500;x<=17000;x+=50) {
        expect(hall.some(r=>contains(r,rect(x,7500,x+1,7601)))).toBe(true);
      }
      expect(m.walls.filter(w=>w.rectMm.y0>=childWall.y1).every(w=>!swingHits(bedroomDoor,w.rectMm))).toBe(true);
      expect(m.dressing!.y1).toBe(childWall.y0);
      expect(m.settings.nestedClosetDepth).toBe(1857);
      expect(m.dressing!.y1-m.dressing!.y0).toBe(m.settings.nestedClosetDepth);
      expect(m.storageRuns.every(r=>r.y1===m.dressing!.y1)).toBe(true);
    }
  });

  it('trades garage access for one metre of closet frontage and keeps terrace retention measurable', () => {
    const on = createConcept({...DEFAULT_CONCEPT,garageConnected:true}), off = createConcept(DEFAULT_CONCEPT);
    expect(on.doors.some(d => d.id === 'C-GARAGE-CLOSET')).toBe(true);
    expect(off.doors.some(d => d.id === 'C-GARAGE-CLOSET')).toBe(false);
    expect(off.storageLength - on.storageLength).toBe(1000);
    expect(off.garageDepth).toBe(5245);
    expect(off.convertedTerraceArea).toBe(0);
    expect(area(off.rooms.find(r => r.number === '1.12')!.rectsMm)).toBeCloseTo(23.59501, 6);
    expect(off.walls.some(w => contains(w.rectMm, rect(10842, 5844, 11143, 6644)))).toBe(true);
  });

  it('aligns the bathroom and bedroom doors while keeping fixture approaches and the garage clear', () => {
    for (const expansion of [0,50,100]) for (let garageBayWidth=1000;garageBayWidth<=1700;garageBayWidth+=50) {
      const m=createConcept({...DEFAULT_CONCEPT,expansion,garageBayWidth});
      const bathDoor=m.doors.find(d=>d.id==='C-HALL-BATH')!;
      const bedroomDoor=m.doors.find(d=>d.id==='C-PRIVATE-BED')!;
      expect(bathDoor.startMm).toBe(bedroomDoor.startMm);
      expect(bathDoor.widthMm).toBe(bedroomDoor.widthMm);
      expect(bathDoor.hinge).toBe(1);
      expect(bathDoor.swing).toBe(-1);
      const floor=m.rooms.find(r=>r.number==='1.11')!.rectsMm[0];
      const {bath,basin,toilet}=m.fixtures;
      expect(basin.x1).toBe(floor.x1);
      expect(basin.y1-basin.y0).toBe(600);
      expect(basin.x1-basin.x0).toBe(500);
      expect(toilet.y0).toBe(floor.y0);
      expect(toilet.y1-toilet.y0).toBe(700);
      expect(toilet.x1-toilet.x0).toBe(400);
      expect((bathDoor.wallSpanMm[0]+bathDoor.wallSpanMm[1])/2-bathDoor.leafWidthMm-basin.y1).toBeGreaterThanOrEqual(70);
      expect(bath.y1-bath.y0).toBe(1800);
      const approaches=[
        rect(bath.x1,bath.y0+800,bath.x1+600,bath.y0+1400),
        rect(basin.x0-600,basin.y0,basin.x0,basin.y1),
        rect(toilet.x0,toilet.y1,toilet.x1,toilet.y1+600),
      ];
      for (const approach of approaches) {
        expect(contains(floor,approach)).toBe(true);
        expect(Object.values(m.fixtures).every(r=>!intersects(r,approach))).toBe(true);
        expect(swingHits(bathDoor,approach)).toBe(false);
      }
      expect(m.garageBay!.x1-m.garageBay!.x0).toBe(garageBayWidth);
      expect(m.bathroomArea).toBeCloseTo((m.bathRight-m.bathLeft)*2100/1e6,6);
    }
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
