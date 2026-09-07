import { describe, expect, it } from 'vitest';
import { createConcept, DEFAULT_CONCEPT, normalizeConcept, area, rect } from '../lib/floor-plan-concept';
import { INTERIOR_ROOMS, INTERIOR_WALLS, INTERIOR_DOORS } from '../lib/twin-interior';
import { HOUSE } from '../lib/twin-site';
import { contains, intersects, opening, swingHits, openLeaf, walkingPath, check } from './floor-plan-geometry';

describe('private bedroom study D',()=>{
  it('preserves D sleeping space, bathroom, garage bay and exterior independently of C alignment',()=>{
    const before=JSON.stringify({HOUSE,INTERIOR_ROOMS,INTERIOR_WALLS,INTERIOR_DOORS});
    const m=createConcept(DEFAULT_CONCEPT), c=createConcept({...DEFAULT_CONCEPT,layout:'nested'});
    expect(m.isPrivate).toBe(true);
    expect(m.bed).toEqual(rect(11143,8241,13343,10041));
    expect(m.bedroomArea).toBeCloseTo(12.0239);
    expect(area([m.dressing!])).toBeCloseTo(6.562);
    expect(m.bathroomArea).toBe(c.bathroomArea);
    expect(m.garageBay).toEqual(c.garageBay);
    expect(m.fixtures).toEqual({bath:rect(12532,3554,13282,5354),basin:rect(14503,4554,15003,5454),toilet:rect(13853,3504,14253,4204)});
    expect(m.sideClearance).toBe(657);
    expect(m.storageLength).toBe(2660);
    expect(m.dressingAisle).toBe(1100);
    expect(m.structuralChanges).toEqual(c.structuralChanges.filter(w=>!['IW-BED-108-EAST','IW-BED-108-TOP-E','IW-ROOM-109-EAST','IW-ENTRY-STUDY','IW-ENTRY-EAST'].includes(w.id)));
    expect(m.walls.find(w=>w.id==='IW-BED-108-EAST')!.rectMm).toEqual(INTERIOR_WALLS.find(w=>w.id==='IW-BED-108-EAST')!.rectMm);
    expect(m.doors.filter(d=>d.fromRoomId==='ROOM-1-10'||d.toRoomId==='ROOM-1-10').map(d=>d.id)).toEqual(['D-PRIVATE-BED']);
    expect(JSON.stringify({HOUSE,INTERIOR_ROOMS,INTERIOR_WALLS,INTERIOR_DOORS})).toBe(before);
  });
  it('clamps a shallow C setting when switching to D so the hall door stays inside the lobby',()=>{
    expect(normalizeConcept({...DEFAULT_CONCEPT,layout:'nested',nestedClosetDepth:1600}).nestedClosetDepth).toBe(1600);
    expect(normalizeConcept({...DEFAULT_CONCEPT,nestedClosetDepth:1600}).nestedClosetDepth).toBe(1700);
    const m=createConcept({...DEFAULT_CONCEPT,nestedClosetDepth:1600});
    const d=m.doors.find(d=>d.id==='D-HALL-DRESSING')!;
    expect(d.startMm).toBeGreaterThan(6560);
    expect(d.startMm+d.widthMm).toBeLessThan(m.dressing!.y1);
  });
  it('keeps all control geometries and door sweeps clear',()=>{
    for(let expansion=0;expansion<=600;expansion+=50)for(let nestedClosetDepth=1700;nestedClosetDepth<=1900;nestedClosetDepth+=50)for(let garageBayWidth=1000;garageBayWidth<=1700;garageBayWidth+=50)for(const garageConnected of [false,true]){
      const m=createConcept({...DEFAULT_CONCEPT,expansion,nestedClosetDepth,garageBayWidth,garageConnected});
      const floors=m.rooms.flatMap(r=>r.rectsMm);
      for(let i=0;i<floors.length;i++){
        for(let j=i+1;j<floors.length;j++)check(!intersects(floors[i],floors[j]),'Rooms overlap');
        for(const wall of m.walls)check(!intersects(floors[i],wall.rectMm),`Wall ${wall.id} crosses floor`);
      }
      for(const bank of m.storageRuns)check(contains(m.dressing!,bank),'Cabinet outside lobby');
      const furniture=[m.bed,...m.storageRuns,...m.garageShelves,...Object.values(m.fixtures),m.car];
      for(const d of m.doors.filter(d=>d.id.startsWith('D-')||d.id==='C-GARAGE-CLOSET')){
        check(m.walls.every(w=>!intersects(w.rectMm,opening(d))),`${d.id} is blocked`);
        check(furniture.every(r=>!swingHits(d,r)),`${d.id} swings into furniture`);
      }
      check(m.dressing!.y1-600-m.dressing!.y0>=1100,'Cabinet approach narrowed');
    }
  });
  it('reaches bathroom and garage with the bedroom completely excluded from the walking floor',()=>{
    for(const expansion of [0,600])for(const nestedClosetDepth of [1700,1900])for(const garageBayWidth of [1000,1700]){
      const m=createConcept({...DEFAULT_CONCEPT,expansion,nestedClosetDepth,garageBayWidth});
      const shared=m.doors.filter(d=>['D-HALL-DRESSING','D-DRESSING-BATH','C-GARAGE-CLOSET'].includes(d.id));
      const floors=[...m.rooms.filter(r=>['1.02','1.14','1.11','1.12'].includes(r.number)).flatMap(r=>r.rectsMm),...shared.map(opening)];
      const obstacles=[...m.storageRuns,...m.garageShelves,...Object.values(m.fixtures),...shared.map(openLeaf),m.car];
      const from:[number,number]=[Math.round((m.suiteRight+1000)/50)*50,7100];
      const bath:[number,number]=[Math.round((m.bathLeft+m.bathRight)/100)*50,4550];
      expect(walkingPath(floors,obstacles,from,bath)).toBe(true);
      expect(walkingPath(floors,obstacles,from,[10300,6200])).toBe(true);
      expect(walkingPath(floors,obstacles,from,[14000,9000])).toBe(false);
    }
  });
  it('still gives the bedroom an internal route to the bathroom through its own door',()=>{
    const m=createConcept(DEFAULT_CONCEPT);
    const doors=m.doors.filter(d=>['D-PRIVATE-BED','D-DRESSING-BATH'].includes(d.id));
    const floors=[...m.rooms.filter(r=>['1.10','1.14','1.11'].includes(r.number)).flatMap(r=>r.rectsMm),...doors.map(opening)];
    const obstacles=[m.bed,...m.storageRuns,...Object.values(m.fixtures),...doors.map(openLeaf)];
    expect(walkingPath(floors,obstacles,[14000,9000],[13750,4550])).toBe(true);
    const closed=floors.slice(0,-2).concat(opening(doors.find(d=>d.id==='D-DRESSING-BATH')!));
    expect(walkingPath(closed,obstacles,[14000,9000],[13750,4550])).toBe(false);
  });
  it('closing the optional garage door preserves cabinet capacity and removes the internal route',()=>{
    const m=createConcept({...DEFAULT_CONCEPT,garageConnected:false});
    expect(m.storageLength).toBe(2660);
    expect(m.doors.some(d=>d.id==='C-GARAGE-CLOSET')).toBe(false);
    expect(m.walls.some(w=>contains(w.rectMm,rect(10842,5844,11143,6644)))).toBe(true);
  });
});
