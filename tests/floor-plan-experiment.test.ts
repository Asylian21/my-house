import { describe, expect, it } from 'vitest';
import { createExperiment, DEFAULT_EXPERIMENT, normalizeExperiment, bedroomDoorOffsetMax } from '../lib/floor-plan-experiment';
import { createConcept, DEFAULT_CONCEPT, rect } from '../lib/floor-plan-concept';
import { HOUSE, GARAGE_DEPTH_REVISION } from '../lib/twin-site';
import { GARAGE_VEHICLE } from '../lib/twin-garage';
import { INTERIOR_ROOMS, INTERIOR_WALLS, INTERIOR_DOORS } from '../lib/twin-interior-baseline';
import { contains, intersects, opening, swingHits, openLeaf, walkingPath, check } from './floor-plan-geometry';

describe('independent stepped private wardrobe study E',()=>{
  it('preserves approved D and the source house while assigning the wardrobe to the bedroom',()=>{
    const before=JSON.stringify({HOUSE,INTERIOR_ROOMS,INTERIOR_WALLS,INTERIOR_DOORS,d:createConcept(DEFAULT_CONCEPT)});
    const m=createExperiment(), d=createConcept(DEFAULT_CONCEPT);
    expect(m.bedroomArea).toBeCloseTo(13.64608);
    expect(m.foyerArea).toBeCloseTo(3.48084);
    expect(m.storageLength).toBe(2600);
    expect(m.entranceWidth).toBe(1120);
    expect(m.sideClearance).toBe(707);
    expect(m.turnClearance).toBeCloseTo(Math.hypot(400,450));
    expect(m.bed.x1-m.bed.x0).toBe(2200);
    expect(m.garageBay!.y1).toBe(m.stepY);
    expect(m.garageGain).toBeCloseTo(1.71);
    expect(m.garageArea).toBeCloseTo(25.30501);
    expect(m.foyerReduction).toBeCloseTo(1.339);
    expect(m.fixtures).toEqual(d.fixtures);
    for(const number of ['1.08','1.09','1.11'])expect(m.rooms.find(r=>r.number===number)?.rectsMm).toEqual(d.rooms.find(r=>r.number===number)?.rectsMm);
    expect(m.doors.filter(d=>d.toRoomId==='ROOM-1-10'||d.fromRoomId==='ROOM-1-10').map(d=>d.id)).toEqual(['E-PRIVATE-BED']);
    expect(JSON.stringify({HOUSE,INTERIOR_ROOMS,INTERIOR_WALLS,INTERIOR_DOORS,d:createConcept(DEFAULT_CONCEPT)})).toBe(before);
  });
  it('restores the current garden recess without consuming bedroom or bathroom space',()=>{
    const m=createExperiment({}), enclosed=createExperiment({gardenRecess:false});
    const porch=HOUSE.porches.gardenLoggia;
    expect(m.settings.gardenRecess).toBe(true);
    expect(m.loggia.depth).toBe(1953);
    expect(m.loggia.openingWidth).toBe(2200);
    expect(m.loggia.bounds).toEqual(rect(6440,porch.backFaceYmm,10640,11200));
    expect(m.loggia.pier).toEqual(rect(6440,10700,8440,11200));
    expect(m.loggia.pierReturn).toEqual(rect(6440,10200,6940,10700));
    for(const r of m.rooms.flatMap(r=>r.rectsMm))expect(intersects(r,m.loggia.bounds)).toBe(false);
    expect(m.garageBackOpening.y0).toBe(GARAGE_DEPTH_REVISION.revisedGarageRearInnerFaceYmm);
    expect(m.garageBackOpening.y1).toBe(porch.backFaceYmm);
    expect(m.garageDepth).toBe(5245);
    expect(enclosed.garageDepth).toBe(7195);
    expect(enclosed.garageArea-m.garageArea).toBeCloseTo(7.6011);
    expect(enclosed.garageBay).toEqual(m.garageBay);
    for(const number of ['1.10','1.11','1.14'])expect(m.rooms.find(r=>r.number===number)).toEqual(enclosed.rooms.find(r=>r.number===number));
  });
  it('keeps the parked car behind the gate and clear of the complete garden-door swing',()=>{
    for(const gardenRecess of [true,false]){
      const m=createExperiment({gardenRecess});
      expect(m.car.y1-m.car.y0).toBe(4850);
      expect(swingHits(m.gardenDoor,m.car)).toBe(false);
      expect(m.car.y0-(GARAGE_VEHICLE.door.faceYmm+38)).toBeGreaterThanOrEqual(140);
      expect(m.car.y1).toBeLessThan(m.garageBackOpening.y0);
      if(gardenRecess){
        expect((m.car.y0+m.car.y1)/2).toBe(GARAGE_VEHICLE.route.parkedMm.y);
        expect(contains(m.garageThreshold,rect(m.car.x0,m.car.y0,m.car.x1,3504))).toBe(true);
      }
      const floors=[...m.rooms.find(r=>r.number==='1.12')!.rectsMm,opening(m.gardenDoor),rect(9086,m.garageBackOpening.y1,9986,11200)];
      // Garage to garden remains reachable with the bedroom excluded and car parked.
      if(gardenRecess)expect(walkingPath(floors,[m.car,...m.garageShelves,openLeaf(m.gardenDoor)],[10300,6200],[9550,10200])).toBe(true);
    }
  });
  it('moves the garage entry onto the bathroom divider and reclaims the former passage',()=>{
    const m=createExperiment();
    const door=m.doors.find(d=>d.id==='E-GARAGE-ENTRY')!;
    expect(door.wallSpanMm).toEqual([m.garageBay!.x1,m.bathLeft]);
    expect(door.startMm).toBe(5844);
    expect(m.foyerRects[0].x0).toBe(m.bathLeft);
    expect(contains(m.garageBay!,rect(11143,5744,12342,6744))).toBe(true);
    expect(m.garageShelves[0]).toEqual(rect(11842,4104,12342,5604));
    const closed=createExperiment({garageConnected:false});
    expect(closed.walls.some(w=>contains(w.rectMm,opening(door)))).toBe(true);
    expect(closed.doors.some(d=>d.id==='E-GARAGE-ENTRY')).toBe(false);
  });
  it('keeps dynamic bedroom door limits inside both jambs after changing the wall jog',()=>{
    const m=createExperiment({alcoveWidth:2600,doorOffset:600,expansion:0});
    expect(m.settings.doorOffset).toBe(200);
    expect(normalizeExperiment({alcoveWidth:NaN,passageDepth:0,doorOffset:Infinity})).toEqual({...DEFAULT_EXPERIMENT,passageDepth:1000});
    expect(m.doorStart-m.returnRight).toBeGreaterThanOrEqual(100);
    expect(m.suiteRight-m.doorStart-800).toBeGreaterThanOrEqual(100);
    expect(m.doors.find(d=>d.id==='E-PRIVATE-BED')?.hinge).toBe(1);
  });
  it('keeps rooms, walls, private storage and door sweeps disjoint across wall and door controls',()=>{
    for(const expansion of [0,300,600])for(let alcoveWidth=2000;alcoveWidth<=2600;alcoveWidth+=50)for(const passageDepth of [1000,1100,1200])for(const doorOffset of [100,bedroomDoorOffsetMax({expansion,alcoveWidth})])for(const bedWidth of [1600,1800,2200])for(const garageBayWidth of [1000,1700]){
      const m=createExperiment({expansion,alcoveWidth,passageDepth,doorOffset,bedWidth,garageBayWidth});
      const floors=m.rooms.flatMap(r=>r.rectsMm);
      for(let i=0;i<floors.length;i++){
        for(let j=i+1;j<floors.length;j++)check(!intersects(floors[i],floors[j]),'Overlapping rooms');
        for(const w of m.walls)check(!intersects(floors[i],w.rectMm),`Wall ${w.id} crosses a room`);
      }
      check(m.bed.y0>=7741,'Bed crosses stepped boundary');
      for(const bank of m.storageRuns)check(contains(m.privateAlcove,bank),'Cabinet outside private alcove');
      for(const shelf of m.garageShelves){
        check(contains(m.garageBay!,shelf),'Garage shelf outside enlarged bay');
        check(shelf.x1-shelf.x0===500&&shelf.y1-shelf.y0===garageBayWidth,'Rotated shelf dimensions changed');
      }
      const furniture=[m.bed,...m.storageRuns,...m.garageShelves,...Object.values(m.fixtures),m.car];
      for(const d of m.doors.filter(d=>['D-HALL-DRESSING','D-DRESSING-BATH','E-GARAGE-ENTRY','E-PRIVATE-BED'].includes(d.id))){
        check(m.walls.every(w=>!intersects(w.rectMm,opening(d))),`Blocked ${d.id}`);
        check(furniture.every(r=>!swingHits(d,r)),`${d.id} swings into furniture`);
      }
      check(m.entranceWidth>=1100,'Narrow entrance leg');
      check(m.frontAisle>=1000,'Narrow garage approach');
    }
  });
  it('provides a 440 mm route to garage and bathroom with all bedroom and private wardrobe floors excluded',()=>{
    for(const expansion of [0,600])for(const alcoveWidth of [2000,2600])for(const passageDepth of [1000,1200])for(const garageBayWidth of [1000,1700]){
      const m=createExperiment({expansion,alcoveWidth,passageDepth,garageBayWidth});
      const ds=m.doors.filter(d=>['D-HALL-DRESSING','D-DRESSING-BATH','E-GARAGE-ENTRY'].includes(d.id));
      const floors=[...m.rooms.filter(r=>['1.02','1.14','1.11','1.12'].includes(r.number)).flatMap(r=>r.rectsMm),...ds.map(opening)];
      const obstacles=[...m.storageRuns,...m.garageShelves,...Object.values(m.fixtures),...ds.map(openLeaf),m.car];
      const from:[number,number]=[Math.round((m.suiteRight+1000)/50)*50,7100];
      const bath:[number,number]=[Math.round((m.bathLeft+m.bathRight)/100)*50,4550];
      expect(walkingPath(floors,obstacles,from,bath)).toBe(true);
      expect(walkingPath(floors,obstacles,from,[10300,6200])).toBe(true);
      expect(walkingPath(floors,obstacles,from,[12300,7800])).toBe(false);
    }
  });
  it('provides an entirely private 440 mm route around the actual return corner to the wardrobe',()=>{
    for(const expansion of [0,600])for(const doorOffset of [100,200]){
      const m=createExperiment({expansion,doorOffset});
      const floors=m.rooms.find(r=>r.number==='1.10')!.rectsMm;
      const obstacles=[m.bed,...m.storageRuns,openLeaf(m.doors.find(d=>d.id==='E-PRIVATE-BED')!)];
      expect(walkingPath(floors,obstacles,[14200,9000],[12300,7750])).toBe(true);
    }
  });
  it('detects that a wide bed and narrow alcove can block the wardrobe turn despite apparent front clearance',()=>{
    const m=createExperiment({alcoveWidth:2200,bedWidth:2200});
    expect(m.sideClearance).toBeGreaterThan(440);
    expect(m.turnClearance).toBeLessThan(440);
    expect(walkingPath(m.rooms.find(r=>r.number==='1.10')!.rectsMm,[m.bed,...m.storageRuns],[14200,9000],[12300,7750])).toBe(false);
  });
  it('also detects a cabinet-front pinch even when the return corner itself is wide enough',()=>{
    const m=createExperiment({alcoveWidth:2600,passageDepth:1200,bedWidth:2200});
    expect(m.sideClearance).toBe(407);
    expect(m.turnClearance).toBeGreaterThan(440);
    expect(walkingPath(m.rooms.find(r=>r.number==='1.10')!.rectsMm,[m.bed,...m.storageRuns],[14200,9000],[12300,7900])).toBe(false);
  });
  it('retains bedroom to bathroom access and closes the optional internal garage route',()=>{
    const m=createExperiment({garageConnected:false,gardenRecess:true});
    expect(m.doors.some(d=>d.id==='E-GARAGE-ENTRY')).toBe(false);
    expect(m.garageDepth).toBe(5245);
    const ds=m.doors.filter(d=>['E-PRIVATE-BED','D-DRESSING-BATH'].includes(d.id));
    const floors=[...m.rooms.filter(r=>['1.10','1.14','1.11'].includes(r.number)).flatMap(r=>r.rectsMm),...ds.map(opening)];
    const obstacles=[m.bed,...m.storageRuns,...Object.values(m.fixtures),...ds.map(openLeaf)];
    expect(walkingPath(floors,obstacles,[14200,9000],[13750,4550])).toBe(true);
  });
});
