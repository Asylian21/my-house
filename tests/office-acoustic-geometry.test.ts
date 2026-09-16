import { describe, expect, it } from 'vitest';
import { CENTRAL_HALL_AXIS_Y_MM, DEFAULT_NESTED_CONCEPT, OFFICE_BATHROOM_FACE_MM, OFFICE_BATH_WALL_MM, OFFICE_ENTRY_SHIFT_MM, createConcept, rect } from '../lib/floor-plan-concept';
import { ACTIVE_CONCEPT, BATHROOM_FITOUT, ENTRY_FITOUT, HALLWAY_BUILT_IN_WARDROBES, INTERIOR_DOORS, INTERIOR_ROOMS, INTERIOR_WALLS, OFFICE_FITOUT, roomAreaM2, type InteriorDoor } from '../lib/twin-interior';
import { INTERIOR_DOORS as BASELINE_DOORS, INTERIOR_WALLS as BASELINE_WALLS } from '../lib/twin-interior-baseline';
import { HOUSE } from '../lib/twin-active-house';
import { contains, intersects, opening, openLeaf, swingHits, walkingPath } from './floor-plan-geometry';

const officeDoor=INTERIOR_DOORS.find(d=>d.id==='DOOR-102-104')!;
const bathroomDoor=INTERIOR_DOORS.find(d=>d.id==='DOOR-102-105')!;
const acousticWall=INTERIOR_WALLS.find(w=>w.id==='IW-STUDY-NORTH')!;
// Feed the physical hinge position into the shared quarter-disc geometry check.
const physicalSwing=(door:InteriorDoor)=>({...door,startMm:door.startMm+(door.frameInsetMm??60),widthMm:door.leafWidthMm,leafPlaneMm:door.wallSpanMm[1]});

describe('office / shower acoustic wall and centred corridor doorway',()=>{
  it('centres the 800 mm opening, 700 mm leaf and frame on the unchanged main hall axis',()=>{
    const hall=INTERIOR_ROOMS.find(r=>r.number==='1.02')!.rectsMm[0];
    expect(hall.y1-hall.y0).toBe(1099);
    expect(CENTRAL_HALL_AXIS_Y_MM).toBe((hall.y0+hall.y1)/2);
    expect(CENTRAL_HALL_AXIS_Y_MM).toBe(7101.5);
    expect(bathroomDoor.startMm).toBe(6701.5);
    expect(bathroomDoor.startMm+bathroomDoor.widthMm).toBe(7501.5);
    expect(bathroomDoor.startMm+bathroomDoor.widthMm/2).toBe(CENTRAL_HALL_AXIS_Y_MM);
    expect(bathroomDoor.frameInsetMm).toBe(50);
    expect(bathroomDoor.startMm+bathroomDoor.frameInsetMm!+bathroomDoor.leafWidthMm/2).toBe(CENTRAL_HALL_AXIS_Y_MM);
    expect(INTERIOR_WALLS.find(w=>w.id==='IW-SPINE-EAST-1')!.rectMm.y1).toBe(bathroomDoor.startMm);
    expect(INTERIOR_WALLS.find(w=>w.id==='IW-SPINE-EAST-2')!.rectMm.y0).toBe(bathroomDoor.startMm+bathroomDoor.widthMm);
    expect(bathroomDoor.startMm-(BASELINE_DOORS.find(d=>d.id===bathroomDoor.id)!.startMm)).toBe(48.5);
  });

  it('reserves the H200 base build-up and maintains usable nibs beside both doors',()=>{
    expect(OFFICE_BATH_WALL_MM).toBe(15+100+15+45+12.5);
    expect(acousticWall.role).toBe('PARTITION');
    for(const id of ['B-STREET-KID-TOP','C-KID-HALL-POCKET-WALL','C-ENTRY-HALL-JAMB']) {
      expect(acousticWall.rectMm.y1).toBe(INTERIOR_WALLS.find(w=>w.id===id)!.rectMm.y1);
    }
    expect(acousticWall.rectMm).toEqual(rect(22783,6364.5,27541,OFFICE_BATHROOM_FACE_MM));
    expect(OFFICE_ENTRY_SHIFT_MM).toBe(30);
    expect(officeDoor.startMm).toBe(5421);
    expect(officeDoor.startMm+officeDoor.widthMm).toBe(6322);
    expect(acousticWall.rectMm.y0-officeDoor.startMm-officeDoor.widthMm).toBe(42.5);
    expect(bathroomDoor.startMm-acousticWall.rectMm.y1).toBe(149.5);
    expect(INTERIOR_WALLS.find(w=>w.id==='C-OFFICE-NORTH-JAMB')!.rectMm).toEqual(rect(22783,6322,22842,6364.5));
    expect(INTERIOR_WALLS.find(w=>w.id==='C-ENTRY-OFFICE-RETURN')!.rectMm).toEqual(rect(22842,5195,23542,5370));
    expect(officeDoor.startMm-5370).toBe(51);
    for(const door of [officeDoor,bathroomDoor]){
      expect(INTERIOR_WALLS.filter(w=>intersects(w.rectMm,opening(door)))).toEqual([]);
      expect(INTERIOR_WALLS.filter(w=>swingHits(physicalSwing(door),w.rectMm))).toEqual([]);
    }
    expect(ACTIVE_CONCEPT.structuralChanges.some(w=>w.id===acousticWall.id&&w.role==='LOAD_BEARING')).toBe(true);
  });

  it('preserves the shower, facade windows and office furniture while moving the wall-mounted board',()=>{
    const showerWindow=HOUSE.facades.east.openings.find(o=>o.id==='EAST-02')!;
    const officeWindow=HOUSE.facades.east.openings.find(o=>o.id==='EAST-01')!;
    expect(acousticWall.rectMm.y1).toBe(6552);
    // These are the approved active facade openings, not the older D1 baseline.
    expect([showerWindow.startYmm,showerWindow.widthMm]).toEqual([6801.5,600]);
    expect([officeWindow.startYmm,officeWindow.widthMm]).toEqual([5212,1000]);
    expect(showerWindow.startYmm-acousticWall.rectMm.y1).toBe(249.5);
    expect(BATHROOM_FITOUT.shower.footprintMm).toEqual(rect(26291,6652,27541,7552));
    expect(BATHROOM_FITOUT.shower.clearEntryWidthMm).toBe(600);
    expect(BATHROOM_FITOUT.towelRadiator.footprintMm.y0).toBe(acousticWall.rectMm.y1);
    expect(BATHROOM_FITOUT.clearFloorRectMm.y0).toBe(bathroomDoor.startMm+bathroomDoor.widthMm);
    expect(OFFICE_FITOUT.whiteboard.footprintMm).toEqual(rect(25240,6349.5,26940,6364.5));
    expect(OFFICE_FITOUT.whiteboard.footprintMm.y0-officeWindow.startYmm-officeWindow.widthMm).toBe(137.5);
    expect(OFFICE_FITOUT.clearEntryRectMm).toEqual(rect(23682,5400,25220,6364.5));
    const furnishings=[OFFICE_FITOUT.desk,OFFICE_FITOUT.chair,OFFICE_FITOUT.cabinet,OFFICE_FITOUT.printer,OFFICE_FITOUT.whiteboard];
    for(const fixture of furnishings){
      expect(INTERIOR_WALLS.filter(w=>intersects(w.rectMm,fixture.footprintMm))).toEqual([]);
      expect(swingHits(physicalSwing(officeDoor),fixture.footprintMm)).toBe(false);
    }
    for(const fixture of [BATHROOM_FITOUT.builtIn,BATHROOM_FITOUT.towelRadiator]){
      expect(swingHits(physicalSwing(bathroomDoor),fixture.footprintMm)).toBe(false);
    }
    expect(roomAreaM2(INTERIOR_ROOMS.find(r=>r.number==='1.04')!)).toBeCloseTo(12.1352895,6);
    expect(roomAreaM2(INTERIOR_ROOMS.find(r=>r.number==='1.05')!)).toBeCloseTo(7.214871,6);
  });

  it('keeps the furnished entry, office and bathroom connected through the centred door',()=>{
    const entryDoor=INTERIOR_DOORS.find(d=>d.id==='DOOR-101-102')!;
    const floors=[...INTERIOR_ROOMS.filter(r=>['1.01','1.02','1.04','1.05'].includes(r.number)).flatMap(r=>r.rectsMm),...[officeDoor,bathroomDoor,entryDoor].map(opening)];
    const obstacles=[...HALLWAY_BUILT_IN_WARDROBES.filter(w=>['ROOM-1-01','ROOM-1-02'].includes(w.roomId)).map(w=>w.footprintMm),ENTRY_FITOUT.bench.footprintMm,...[OFFICE_FITOUT.desk,OFFICE_FITOUT.chair,OFFICE_FITOUT.cabinet,BATHROOM_FITOUT.builtIn,BATHROOM_FITOUT.towelRadiator].map(f=>f.footprintMm),openLeaf(physicalSwing(officeDoor)),openLeaf(physicalSwing(bathroomDoor))];
    for(const destination of [[23750,5800],[21250,7100],[23600,7750]] as [number,number][]){
      expect(walkingPath(floors,obstacles,[22500,4300],destination)).toBe(true);
    }
    const entry=INTERIOR_ROOMS.find(r=>r.number==='1.01')!;
    expect(entry.rectsMm[1].y1).toBe(5195);
    expect(entry.rectsMm.some(r=>contains(r,ENTRY_FITOUT.bench.footprintMm))).toBe(true);
  });

  it('leaves the archived non-C geometry unchanged',()=>{
    for(const layout of ['private','wardrobe','vestibule'] as const){
      const archived=createConcept({...DEFAULT_NESTED_CONCEPT,layout});
      expect(archived.walls.find(w=>w.id==='IW-STUDY-NORTH')!.rectMm).toEqual(BASELINE_WALLS.find(w=>w.id==='IW-STUDY-NORTH')!.rectMm);
      for(const id of ['DOOR-102-104','DOOR-102-105']){
        expect(archived.doors.find(d=>d.id===id)!.startMm).toBe(BASELINE_DOORS.find(d=>d.id===id)!.startMm);
      }
    }
  });
});
