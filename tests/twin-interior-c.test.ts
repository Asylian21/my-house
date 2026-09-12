import { describe, expect, it } from 'vitest';
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Scene } from '@babylonjs/core/scene';
import { createConcept, DEFAULT_NESTED_CONCEPT, rect } from '../lib/floor-plan-concept';
import * as baseline from '../lib/twin-interior-baseline';
import { HOUSE as originalHouse } from '../lib/twin-site';
import { HOUSE } from '../lib/twin-active-house';
import { ACTIVE_CONCEPT, BEDROOM_FITOUT, CHILDRENS_BEDROOM_FITOUTS, ENTRY_FITOUT, ENSUITE_BATHROOM_FITOUT, GARAGE_FITOUT, HALLWAY_BUILT_IN_WARDROBES, INTERIOR_ROOMS, INTERIOR_WALLS, INTERIOR_RENDER_WALLS, INTERIOR_DOORS, KITCHEN_BEARING_WALL, KITCHEN_BEARING_WALL_EAST, KITCHEN_RUN, OFFICE_FITOUT, roomAt, roomAreaM2, type RectMm } from '../lib/twin-interior';
import { LIVING_LAYOUTS } from '../lib/twin-living-layouts';
import { buildInterior } from '../lib/babylon-interior';
import type { AnimatedDoorRegistration } from '../lib/babylon-doors';
import { sceneXM, sceneZM, SCENE_CENTER_MM } from '../lib/twin-render-frame';
import { contains, intersects, opening, openLeaf, swingHits, walkingPath } from './floor-plan-geometry';

const furniture:{id:string;room:string;rect:RectMm}[]=[
  {id:'primary-bed',room:'ROOM-1-10',rect:BEDROOM_FITOUT.bed.footprintMm},
  ...BEDROOM_FITOUT.bedsideRectsMm.map((r,i)=>({id:`bedside-${i}`,room:'ROOM-1-10',rect:r})),
  ...HALLWAY_BUILT_IN_WARDROBES.map(w=>({id:w.id,room:w.roomId,rect:w.footprintMm})),
  {id:'entry-bench',room:'ROOM-1-01',rect:ENTRY_FITOUT.bench.footprintMm},
  ...[ENSUITE_BATHROOM_FITOUT.bathtub,ENSUITE_BATHROOM_FITOUT.toilet,ENSUITE_BATHROOM_FITOUT.vanity,ENSUITE_BATHROOM_FITOUT.towelRadiator].map((f,i)=>({id:`bath-${i}`,room:'ROOM-1-11',rect:f.footprintMm})),
  ...[GARAGE_FITOUT.utilitySink,GARAGE_FITOUT.storageRack,GARAGE_FITOUT.mower].map((f,i)=>({id:`garage-${i}`,room:'ROOM-1-12',rect:f.footprintMm})),
  ...[OFFICE_FITOUT.desk,OFFICE_FITOUT.chair,OFFICE_FITOUT.cabinet].map((f,i)=>({id:`office-${i}`,room:'ROOM-1-04',rect:f.footprintMm})),
  ...CHILDRENS_BEDROOM_FITOUTS.flatMap(f=>[f.bed,f.wardrobe,f.desk,f.chair].map((piece,i)=>({id:`${f.id}-${i}`,room:f.roomId,rect:piece.footprintMm}))),
  ...CHILDRENS_BEDROOM_FITOUTS.flatMap(f=>[f.readingRectMm,f.bookcaseRectMm].map((r,i)=>({id:`${f.id}-play-storage-${i}`,room:f.roomId,rect:r}))),
];

describe('active 3D house matches the approved default C plan',()=>{
  it('uses identical walls, room polygons and door openings without modifying the baseline studies',()=>{
    const c=createConcept(DEFAULT_NESTED_CONCEPT);
    expect(INTERIOR_WALLS).toEqual(c.walls);
    expect(INTERIOR_ROOMS.map(r=>r.rectsMm)).toEqual(c.rooms.map(r=>r.rectsMm));
    expect(INTERIOR_DOORS.map(d=>({...d,label:undefined}))).toEqual(c.doors.map(d=>({...d,label:undefined})));
    expect(baseline.INTERIOR_ROOMS.find(r=>r.number==='1.08')!.name).toBe('Spálňa');
    expect(INTERIOR_ROOMS).toHaveLength(13);
    expect(roomAreaM2(INTERIOR_ROOMS.find(r=>r.number==='1.04')!)).toBeCloseTo(12.337492,6);
    expect(INTERIOR_DOORS.some(d=>d.id==='DOOR-102-112'||d.id==='DOOR-108-111')).toBe(false);
    // The living room keeps its main floor; the kitchen bay gives 160 mm to the
    // load-bearing kitchen wall and runs to the east facade over the former
    // technical-room protrusion.
    const [living,bay]=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-03')!.rectsMm;
    const [sourceLiving,sourceBay]=baseline.INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-03')!.rectsMm;
    expect(living).toEqual(sourceLiving);
    expect(bay).toEqual({...sourceBay,y0:sourceBay.y0+160,x1:sourceLiving.x1});
  });
  it('carries the wing roof frames on a 300 mm load-bearing kitchen wall running in one line to the east facade',()=>{
    // Client, 12 Sep 2026: the wall between 1.03 and 1.06/1.07 carries the ring
    // beam and the steel roof frames of the cathedral ceiling and stands on the
    // cross foundation strip. It grows north into the kitchen bay only, and in a
    // second step runs to the east facade: EAST-03 shrinks to a 900 mm single
    // leaf, the technical room's protrusion goes to the kitchen and its door
    // sits in the bearing wall with 860 mm of masonry east of it.
    const wall=INTERIOR_WALLS.find(w=>w.id==='C-KITCHEN-BEARING-WALL')!;
    const east=INTERIOR_WALLS.find(w=>w.id==='C-KITCHEN-BEARING-WALL-E')!;
    expect(wall).toMatchObject({role:'LOAD_BEARING',changed:true});
    expect(east).toMatchObject({role:'LOAD_BEARING',changed:true});
    expect(wall.rectMm).toEqual(rect(22639,10712,25881,11012));
    expect(east.rectMm).toEqual(rect(26681,10712,27541,11012));
    expect(east.rectMm.x1-east.rectMm.x0).toBe(860);
    expect(wall.rectMm.y1-wall.rectMm.y0).toBe(300);
    expect(KITCHEN_BEARING_WALL).toEqual(wall.rectMm);
    expect(KITCHEN_BEARING_WALL_EAST).toEqual(east.rectMm);
    for(const id of ['IW-KITCHEN-BACK','IW-TECH-WEST','IW-TECH-PIER','IW-TECH-NORTH']) expect(INTERIOR_WALLS.some(w=>w.id===id),id).toBe(false);
    // The wall's south face is the source partition's south face: the WC and its door stay.
    expect(wall.rectMm.y0).toBe(baseline.INTERIOR_WALLS.find(w=>w.id==='IW-KITCHEN-BACK')!.rectMm.y0);
    for(const id of ['ROOM-1-06','ROOM-1-07']){
      expect(INTERIOR_ROOMS.find(r=>r.id===id)!.rectsMm).toEqual(createConcept(DEFAULT_NESTED_CONCEPT).rooms.find(r=>r.id===id)!.rectsMm);
      // Nothing of either room lies north of the wall's south face any more.
      expect(INTERIOR_ROOMS.find(r=>r.id===id)!.rectsMm.every(r=>r.y1<=wall.rectMm.y0)).toBe(true);
    }
    expect(INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-06')!.rectsMm).toEqual([rect(22783,8912,24682,10712)]);
    const technical=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-07')!;
    expect(technical.rectsMm).toEqual([rect(24821,7741,27510,10712)]);
    // The straight laundry/WC wall gives one 2 689 × 2 971 mm rectangle.
    expect(roomAreaM2(technical)).toBeCloseTo(7.989019,6);
    expect(roomAreaM2(technical)-7.494857).toBeCloseTo(0.494162,6);
    expect(roomAt(technical.standingPointMm)?.id).toBe('ROOM-1-07');
    expect(INTERIOR_DOORS.find(d=>d.id==='DOOR-102-106')).toMatchObject({startMm:9866,widthMm:800});
    // The technical-room door keeps its 800 mm opening at 25 881 but sits in the
    // bearing wall, swinging into the kitchen with the hinge on the east jamb.
    const techDoor=INTERIOR_DOORS.find(d=>d.id==='DOOR-103-107')!;
    expect(techDoor).toMatchObject({wallSpanMm:[10712,11012],startMm:25881,widthMm:800,leafWidthMm:700,swing:1,hinge:1,hingeOffsetMm:34,fromRoomId:'ROOM-1-03',toRoomId:'ROOM-1-07'});
    expect(techDoor.startMm).toBe(wall.rectMm.x1);
    expect(techDoor.startMm+techDoor.widthMm).toBe(east.rectMm.x0);
    expect(baseline.INTERIOR_DOORS.find(d=>d.id==='DOOR-103-107')).toMatchObject({wallSpanMm:[11411,11550],startMm:25881});
    // The rebated leaf closes before the kitchen-side lining; open, it clears the back run's east end, the east return and the peninsula.
    const leaf=openLeaf(techDoor);
    expect(leaf.y0).toBe(techDoor.wallSpanMm[1]+34);
    for(const piece of [KITCHEN_RUN.rectMm,KITCHEN_RUN.eastReturnRectMm,KITCHEN_RUN.peninsulaRectMm]){
      expect(intersects(leaf,piece)).toBe(false);
      expect(swingHits(techDoor,piece)).toBe(false);
    }
    expect(techDoor.startMm-KITCHEN_RUN.rectMm.x1).toBe(80);
    expect(KITCHEN_RUN.eastReturnRectMm.x0-(techDoor.startMm+techDoor.widthMm)).toBe(260);
    // From the corridor mouth to the facade; the spine starts on the wall's north face.
    expect(INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-02')!.rectsMm.some(r=>r.x1===wall.rectMm.x0&&r.y1===11550)).toBe(true);
    expect(INTERIOR_WALLS.find(w=>w.id==='IW-SPINE-EAST-3')!.rectMm).toEqual(rect(22639,11012,22783,11550));
    expect(INTERIOR_WALLS.find(w=>w.id==='C-WC-DOOR-JAMB')!.rectMm).toEqual(rect(22639,10666,22783,10712));
    // The kitchen bay starts on the wall's north face and reaches the east facade; the back run follows with its 97 mm installation gap.
    const [living,bay]=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-03')!.rectsMm;
    expect(bay).toEqual(rect(22783,11012,27541,11550));
    expect(bay.y0).toBe(wall.rectMm.y1);
    expect(east.rectMm.x1).toBe(living.x1);
    // 5 998 × 7 983 + 4 758 × 538: 0.9953 m² more than the first step's bay, 0.53002 m² more than the source.
    expect(roomAreaM2(INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-03')!)).toBeCloseTo(50.441838,6);
    expect(roomAreaM2(INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-03')!)-roomAreaM2(baseline.INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-03')!)).toBeCloseTo(0.53002,6);
    expect(KITCHEN_RUN.rectMm).toEqual(rect(22791,11109,25801,11710));
    expect(KITCHEN_RUN.eastReturnRectMm.y0).toBe(11109);
    expect(baseline.KITCHEN_RUN.eastReturnRectMm.y0-KITCHEN_RUN.eastReturnRectMm.y0).toBe(441);
    expect(KITCHEN_RUN.fridgeUnitRectMm).toEqual(rect(22791,11109,23391,11710));
    expect(KITCHEN_RUN.rectMm.y0-wall.rectMm.y1).toBe(baseline.KITCHEN_RUN.rectMm.y0-baseline.INTERIOR_WALLS.find(w=>w.id==='IW-KITCHEN-BACK')!.rectMm.y1);
    expect(KITCHEN_RUN.rectMm.y0-baseline.KITCHEN_RUN.rectMm.y0).toBe(160);
    expect(KITCHEN_RUN.peninsulaRectMm.y0-KITCHEN_RUN.fridgeUnitRectMm.y1).toBe(1180);
    for(const key of ['peninsulaRectMm','sinkCenterXmm','dishwasherXmm','hobCenterXmm','upperCabinets'] as const) expect(KITCHEN_RUN[key]).toEqual(baseline.KITCHEN_RUN[key]);
    // The 601 mm deep run stays in the bay and stands 160 mm proud of the spine's north end, inside the main floor.
    expect(KITCHEN_RUN.rectMm.x0).toBeGreaterThanOrEqual(bay.x0);
    expect(KITCHEN_RUN.rectMm.x1).toBeLessThanOrEqual(bay.x1);
    expect(KITCHEN_RUN.rectMm.y1-bay.y1).toBe(160);
    expect(contains(living,rect(KITCHEN_RUN.rectMm.x0,bay.y1,KITCHEN_RUN.rectMm.x1,KITCHEN_RUN.rectMm.y1))).toBe(true);
    expect(baseline.KITCHEN_RUN.rectMm.y0).toBe(10949);
    // The exterior door of the technical room is a 900 mm single leaf moved 300 mm south to free storage wall.
    expect(HOUSE.facades.east.openings.find(o=>o.id==='EAST-03')).toEqual({id:'EAST-03',startYmm:9000,widthMm:900,heightMm:2250,sillMm:0});
    expect(east.rectMm.y0-(9000+900)).toBe(812);
    // Both living layouts document the wall, the door and the 1 180 mm aisle.
    for(const layout of Object.values(LIVING_LAYOUTS)){
      expect(layout.notes.some(n=>/nosné murivo hr\. 300 mm \(10 712–11 012 mm\)/.test(n))).toBe(true);
      expect(layout.notes.some(n=>/po východnú fasádu \(27 541 mm\); prerušujú ju iba dvere do technickej miestnosti 800 mm \(25 881–26 681 mm\)/.test(n))).toBe(true);
      expect(layout.notes.some(n=>/ešte 860 mm muriva/.test(n)&&/EAST-03 majú kvôli statike fasády 900 mm namiesto 1 700 mm/.test(n))).toBe(true);
      expect(layout.notes.some(n=>/polostrovom má 1 180 mm/.test(n))).toBe(true);
    }
  });
  it('meshes wall corners only once while retaining every boundary',()=>{
    INTERIOR_RENDER_WALLS.forEach((a,i)=>INTERIOR_RENDER_WALLS.slice(i+1).forEach(b=>expect(intersects(a.rectMm,b.rectMm),`${a.id} / ${b.id}`).toBe(false)));
    for(const wall of INTERIOR_WALLS){
      for(let x=wall.rectMm.x0+1;x<wall.rectMm.x1;x+=50)for(let y=wall.rectMm.y0+1;y<wall.rectMm.y1;y+=50){
        expect(INTERIOR_RENDER_WALLS.some(w=>x>=w.rectMm.x0&&x<=w.rectMm.x1&&y>=w.rectMm.y0&&y<=w.rectMm.y1),wall.id).toBe(true);
      }
    }
  });
  it('preserves the envelope, roof and recess and places both small windows in their new rooms',()=>{
    for(const key of ['footprintMm','roof','porches','lowerBar','wing'] as const) expect(HOUSE[key]).toEqual(originalHouse[key]);
    const garage=HOUSE.facades.front.openings.find(o=>o.id==='FRONT-02')!;
    const bath=HOUSE.facades.front.openings.find(o=>o.id==='FRONT-03')!;
    expect([garage.startXmm,bath.startXmm]).toEqual([10942,13338]);
    expect(garage.startXmm+garage.widthMm).toBeLessThan(ACTIVE_CONCEPT.garageBay!.x1);
    expect(bath.startXmm).toBeGreaterThan(ACTIVE_CONCEPT.bathLeft);
    expect(bath.startXmm+bath.widthMm).toBeLessThan(ACTIVE_CONCEPT.bathRight);
  });
  it('keeps furniture in its actual rooms, clear of walls, door swings and other furniture',()=>{
    for(const item of furniture){
      const room=INTERIOR_ROOMS.find(r=>r.id===item.room)!;
      expect(room.rectsMm.some(r=>contains(r,item.rect)),`${item.id} inside ${item.room}`).toBe(true);
      expect(INTERIOR_WALLS.filter(w=>intersects(w.rectMm,item.rect)).map(w=>w.id),`${item.id} walls`).toEqual([]);
      for(const d of INTERIOR_DOORS.filter(d=>d.motion!=='POCKET_SLIDING')) expect(swingHits(d,item.rect),`${item.id} door ${d.id}`).toBe(false);
    }
    furniture.forEach((a,i)=>furniture.slice(i+1).forEach(b=>expect(intersects(a.rect,b.rect),`${a.id} / ${b.id}`).toBe(false)));
    for(const room of INTERIOR_ROOMS){
      expect(roomAt(room.standingPointMm)?.id,room.id).toBe(room.id);
      for(const f of furniture.filter(f=>f.room===room.id)){
        const p=room.standingPointMm;
        expect(intersects(f.rect,rect(p.x-220,p.y-220,p.x+220,p.y+220)),`${room.id} spawn versus ${f.id}`).toBe(false);
      }
    }
  });
  it('fits storage against the dressing-room wall without narrowing either end-of-hall doorway',()=>{
    const cabinet=HALLWAY_BUILT_IN_WARDROBES.find(w=>w.id==='C-HALL-END-CABINET')!;
    const wall=INTERIOR_WALLS.find(w=>w.id==='C-CLOSET-EAST')!.rectMm;
    // The cabinet fills the hall end between the bathroom's hall wall (6552) and the 7651 plane.
    expect(cabinet.footprintMm).toEqual(rect(13483,6552,13943,7651));
    expect(cabinet.footprintMm.x0).toBe(wall.x1);
    expect(cabinet.footprintMm.y0).toBe(INTERIOR_WALLS.find(w=>w.id==='C-BATH-HALL-W')!.rectMm.y1);
    expect(cabinet.frontClearanceRectMm).toEqual(rect(13943,6552,14943,7651));
    expect(INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-02')!.rectsMm.some(r=>contains(r,cabinet.footprintMm)&&contains(r,cabinet.frontClearanceRectMm))).toBe(true);
    // The bathroom is L-shaped up to the hall plane; the extension holds the door sweep.
    const bathroom=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-11')!;
    expect(bathroom.rectsMm).toEqual([rect(12982,3504,14943,5604),rect(13483,5604,14943,6412)]);
    expect(roomAreaM2(bathroom)).toBeCloseTo(5.29778,6);
    expect(INTERIOR_DOORS.find(d=>d.id==='C-HALL-BATH')!.wallSpanMm).toEqual([6412,6552]);
    for(const run of HALLWAY_BUILT_IN_WARDROBES.filter(w=>w.roomId==='ROOM-DRESSING')){
      expect([run.footprintMm.y0,run.footprintMm.y1]).toEqual([5744,7651]);
      expect(run.frontClearanceRectMm).toEqual(rect(11743,5744,12743,7651));
    }
    expect(cabinet).toMatchObject({roomId:'ROOM-1-02',facing:'EAST',doorCount:2,heightMm:2550});
    for(const id of ['C-HALL-BATH','C-PRIVATE-BED']){
      const door=INTERIOR_DOORS.find(d=>d.id===id)!;
      expect(cabinet.footprintMm.x1).toBe(door.startMm);
      expect(swingHits(door,cabinet.footprintMm)).toBe(false);
      expect(contains(cabinet.frontClearanceRectMm,rect(door.startMm,6560,door.startMm+door.widthMm,7601))).toBe(true);
    }
  });
  it('matches the bathroom sketch after moving the garage partition 500 mm and keeps every fixture reachable',()=>{
    const door=INTERIOR_DOORS.find(d=>d.id==='C-HALL-BATH')!;
    const [street,extension]=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-11')!.rectsMm;
    expect(HALLWAY_BUILT_IN_WARDROBES.some(w=>w.roomId==='ROOM-1-11')).toBe(false);
    const radiator=ENSUITE_BATHROOM_FITOUT.towelRadiator;
    expect(radiator).toMatchObject({widthMm:600,heightMm:1500,projectionMm:100,bottomElevationMm:200,rungCount:15,facing:'EAST'});
    expect(radiator.footprintMm).toEqual(rect(13483,5708,13583,6308));
    expect(radiator.footprintMm.x0).toBe(INTERIOR_WALLS.find(w=>w.id===radiator.wallId)!.rectMm.x1);
    expect(contains(extension,radiator.footprintMm)).toBe(true);
    expect(swingHits(door,radiator.footprintMm)).toBe(false);
    const {bathtub,toilet,vanity}=ENSUITE_BATHROOM_FITOUT;
    expect(bathtub.footprintMm).toEqual(rect(12982,3504,14943,4254));
    expect(bathtub.facing).toBe('NORTH');
    expect(bathtub.footprintMm.y0).toBe(street.y0);
    expect([bathtub.footprintMm.x0,bathtub.footprintMm.x1]).toEqual([street.x0,street.x1]);
    expect(contains(bathtub.footprintMm,bathtub.innerBasinMm)).toBe(true);
    expect(toilet.footprintMm).toEqual(rect(14243,4804,14943,5204));
    expect(toilet.facing).toBe('WEST');
    expect(toilet.concealedCisternRectMm).toEqual(rect(14743,4754,14943,5254));
    expect(INTERIOR_WALLS.find(w=>w.id==='C-OPEN-HALL-S')!.rectMm.x0).toBe(toilet.concealedCisternRectMm.x1);
    expect(vanity.footprintMm).toEqual(rect(12982,4704,13482,5604));
    expect(vanity.facing).toBe('EAST');
    expect(vanity.footprintMm.x0).toBe(street.x0);
    expect(contains(vanity.footprintMm,vanity.basinFootprintMm)).toBe(true);
    expect(vanity.mirrorPlanRectMm).toEqual(rect(13008,4734,13022,5574));
    expect(toilet.footprintMm.x0-vanity.footprintMm.x1).toBe(761);
    expect(ENSUITE_BATHROOM_FITOUT.clearFloorRectMm).toEqual(rect(13482,4254,14243,5604));
    expect(ENSUITE_BATHROOM_FITOUT.vanityClearanceRectMm).toEqual(rect(13482,4704,14232,5604));
    const toiletApproach=rect(13643,4704,14243,5304);
    const bathApproach=rect(13482,4254,14243,4854);
    for(const zone of [ENSUITE_BATHROOM_FITOUT.clearFloorRectMm,ENSUITE_BATHROOM_FITOUT.vanityClearanceRectMm,toiletApproach,bathApproach]){
      expect(contains(street,zone)).toBe(true);
      for(const f of furniture.filter(f=>f.room==='ROOM-1-11'))expect(intersects(zone,f.rect),f.id).toBe(false);
      expect(swingHits(door,zone)).toBe(false);
    }
    const obstacles=[...furniture.filter(f=>f.room==='ROOM-1-11').map(f=>f.rect),openLeaf(door)];
    for(const goal of [[13800,5000],[13950,5000],[13850,4550]] as [number,number][])
      expect(walkingPath([street,extension,opening(door)],obstacles,[14350,6300],goal),goal.join()).toBe(true);
    expect(GARAGE_FITOUT.utilitySink.footprintMm.x1).toBe(ACTIVE_CONCEPT.garageBay!.x1);
    expect(GARAGE_FITOUT.storageRack.footprintMm.x1-GARAGE_FITOUT.storageRack.footprintMm.x0).toBe(2000);
  });
  it('provides 440mm walking paths between entrance, office, bath, bedroom and closet',()=>{
    const floors=INTERIOR_ROOMS.flatMap(r=>[...r.rectsMm]);
    const obstacles=[...furniture.map(f=>f.rect),...INTERIOR_DOORS.filter(d=>d.motion!=='POCKET_SLIDING').map(openLeaf)];
    const openFloors=[...floors,...INTERIOR_DOORS.map(opening)];
    const entry:[number,number]=[22100,4550];
    for(const goal of [[25100,5800],[13800,4800],[14200,9400],[12250,6500]] as [number,number][]){
      expect(walkingPath(openFloors,obstacles,entry,goal),`entry to ${goal}`).toBe(true);
    }
    // A visit to the shared bathroom must never cross the parents' sleeping room.
    const withoutBedroom=INTERIOR_ROOMS.filter(r=>r.id!=='ROOM-1-10').flatMap(r=>[...r.rectsMm]);
    expect(walkingPath([...withoutBedroom,...INTERIOR_DOORS.filter(d=>d.toRoomId!=='ROOM-1-10').map(opening)],obstacles,entry,[13800,4800])).toBe(true);
  });
  it('fits full-size beds, preschool furniture and daylight with unobstructed play and entry',()=>{
    for(const f of CHILDRENS_BEDROOM_FITOUTS){
      expect(f.childAgeRange).toEqual([3,7]);
      expect(f.bed.mattressWidthMm).toBe(1400);
      expect(f.bed.mattressLengthMm).toBe(2000);
      expect(f.bed.mattressFootprintMm.x1-f.bed.mattressFootprintMm.x0).toBe(1400);
      expect(f.bed.mattressFootprintMm.y1-f.bed.mattressFootprintMm.y0).toBe(2000);
      expect(f.bed.mattressTopElevationMm).toBe(460);
      expect(f.bed.headboardTopElevationMm).toBe(1050);
      expect(f.windowClearanceRectMm.x0-f.bed.footprintMm.x1).toBeGreaterThanOrEqual(200);
      expect(f.chair.wheelCount).toBe(0);
      expect(f.desk.topElevationMm).toBe(540);
      const play=f.clearPlayRectMm;
      expect((play.x1-play.x0)*(play.y1-play.y0)/1e6).toBeGreaterThan(3.7);
      for(const item of furniture.filter(item=>item.room===f.roomId)){
        expect(intersects(play,item.rect),`${item.id} in play zone`).toBe(false);
        expect(intersects(f.windowClearanceRectMm,item.rect),`${item.id} in glazing approach`).toBe(false);
      }
      const floors=INTERIOR_ROOMS.flatMap(r=>[...r.rectsMm]);
      expect(walkingPath([...floors,...INTERIOR_DOORS.map(opening)],
        [...furniture.map(item=>item.rect),...INTERIOR_DOORS.filter(d=>d.motion!=='POCKET_SLIDING').map(openLeaf)],
        [17800,7100],f.roomId==='ROOM-1-09'?[17800,9200]:[17800,4850]),f.roomId).toBe(true);
    }
    expect(INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-09')!.name).toContain('Chlapčenská');
    expect(INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-08')!.name).toContain('Dievčenská');
    expect(HOUSE.facades.garden.openings.find(o=>o.id==='GARDEN-03')).toMatchObject({startXmm:17000,widthMm:2200,sillMm:0});
    const windows=HOUSE.facades.front.openings.filter(o=>['FRONT-GIRL-BED','FRONT-04','FRONT-05'].includes(o.id));
    expect(windows).toHaveLength(3);
    expect(windows.map(w=>[w.startXmm,w.widthMm,w.sillMm,w.heightMm])).toEqual([[15467,1000,1250,1250],[17067,1600,550,1950],[19267,1050,900,1600]]);
    expect(windows.every(w=>w.sillMm+w.heightMm===2500)).toBe(true);
    expect(windows.reduce((sum,w)=>sum+w.widthMm*w.heightMm/1e6,0)).toBeCloseTo(6.05,6);
    expect(windows[1]).toMatchObject({kind:'fixed',frameWidthMm:45});
    for(let i=1;i<windows.length;i++)expect(windows[i].startXmm-windows[i-1].startXmm-windows[i-1].widthMm).toBeGreaterThanOrEqual(600);
    // Every window stays inside the girl's room, with a masonry pier beside both walls.
    const girlRoom=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-08')!.rectsMm[0];
    expect(windows[0].startXmm-girlRoom.x0).toBeGreaterThanOrEqual(190);
    expect(girlRoom.x1-windows[2].startXmm-windows[2].widthMm).toBeGreaterThanOrEqual(190);
    const girl=CHILDRENS_BEDROOM_FITOUTS.find(f=>f.roomId==='ROOM-1-08')!;
    const boy=CHILDRENS_BEDROOM_FITOUTS.find(f=>f.roomId==='ROOM-1-09')!;
    const boyRoom=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-09')!.rectsMm[0];
    // Both rooms are 5 298 × 2 908 mm and the girl's room mirrors the boy's across
    // the hall: wardrobes back onto the hall wall beside the centred doors (facing
    // into the room), beds on the west wall, desks by the facade on the east wall.
    expect(girlRoom).toEqual(rect(15243,3504,20541,6412));
    expect(boyRoom).toEqual(rect(15243,7791,20541,10699));
    const mirror=(r:RectMm)=>rect(r.x0,girlRoom.y0+boyRoom.y1-r.y1,r.x1,girlRoom.y0+boyRoom.y1-r.y0);
    expect(girl.wardrobe.footprintMm).toEqual(rect(18941,5812,20541,6412));
    expect(boy.wardrobe.footprintMm).toEqual(rect(18941,7791,20541,8391));
    for(const [a,b] of [[girl.bed.footprintMm,boy.bed.footprintMm],[girl.wardrobe.footprintMm,boy.wardrobe.footprintMm],[girl.desk.footprintMm,boy.desk.footprintMm],[girl.chair.footprintMm,boy.chair.footprintMm],[girl.readingRectMm,boy.readingRectMm],[girl.bookcaseRectMm,boy.bookcaseRectMm],[girl.clearPlayRectMm,boy.clearPlayRectMm]]){
      expect(a).toEqual(mirror(b));
    }
    expect([girl.wardrobe.facing,boy.wardrobe.facing]).toEqual(['SOUTH','NORTH']);
    expect(girl.wardrobe.footprintMm.y1).toBe(girlRoom.y1);
    expect(boy.wardrobe.footprintMm.y0).toBe(boyRoom.y0);
    for(const [f,id] of [[girl,'DOOR-102-108'],[boy,'DOOR-102-109']] as const){
      const door=INTERIOR_DOORS.find(d=>d.id===id)!;
      expect([door.startMm,door.widthMm]).toEqual([17442,900]);
      expect(f.wardrobe.footprintMm.x0-(door.startMm+door.widthMm)).toBe(599);
      expect(f.bed.footprintMm.x0).toBe(girlRoom.x0);
    }
    expect(girl.wardrobe.footprintMm.x1).toBe(girlRoom.x1);
    expect(girl.desk.footprintMm.x1).toBe(girlRoom.x1);
    expect(windows[2].startXmm).toBeGreaterThanOrEqual(girl.desk.footprintMm.x0);
    expect(windows[2].startXmm+windows[2].widthMm).toBeLessThanOrEqual(girl.desk.footprintMm.x1);
    expect(windows[0].sillMm-girl.bed.headboardTopElevationMm).toBe(200);
    expect(windows[2].sillMm-girl.desk.topElevationMm).toBe(360);
    expect(girl.pinboard.facing).toBe('WEST');
  });
  it('renders moved accessories, lights and collision guards in the same room, with clear 80/90cm doors',()=>{
    const engine=new NullEngine({renderWidth:256,renderHeight:256,textureSize:256,deterministicLockstep:false,lockstepMaxSteps:4});
    const scene=new Scene(engine), doors:AnimatedDoorRegistration[]=[];
    const mat=(n:string)=>new PBRMaterial(n,scene);
    try {
      buildInterior({scene,anisotropy:1,wall:mat('wall'),soffit:mat('soffit'),glassFrame:mat('frame'),chimneyMetal:mat('metal'),timber:mat('timber'),register:()=>{},realisticOnly:()=>{},castShadow:()=>{},registerAnimatedDoor:d=>doors.push(d)});
      // The door linings project 12 mm into the alcove. Include their actual
      // meshes, since floor-plan door swings alone cannot catch this overlap.
      const endCabinet=scene.meshes.filter(m=>m.name.startsWith('C-HALL-END-CABINET')&&!m.metadata?.walkCollisionOnly);
      for(const id of ['C-HALL-BATH','C-PRIVATE-BED']){
        const door=INTERIOR_DOORS.find(d=>d.id===id)!;
        const jamb=scene.meshes.find(m=>m.name===`${door.label} · ľavá zárubňa`)!;
        jamb.computeWorldMatrix(true);
        for(const mesh of endCabinet){
          mesh.computeWorldMatrix(true);
          expect(mesh.intersectsMesh(jamb,false),`${mesh.name} clears ${id} lining`).toBe(false);
        }
      }
      const groups=[BEDROOM_FITOUT,ENTRY_FITOUT,ENSUITE_BATHROOM_FITOUT,GARAGE_FITOUT,OFFICE_FITOUT,...CHILDRENS_BEDROOM_FITOUTS,...HALLWAY_BUILT_IN_WARDROBES];
      for(const group of groups){
        const room=INTERIOR_ROOMS.find(r=>r.id===group.roomId)!;
        for(const mesh of scene.meshes.filter(m=>m.name.startsWith(group.id))){
          mesh.computeWorldMatrix(true);
          const b=mesh.getBoundingInfo().boundingBox;
          const x=b.centerWorld.x*1000+SCENE_CENTER_MM.x, y=SCENE_CENTER_MM.y-b.centerWorld.z*1000;
          expect(room.rectsMm.some(r=>x>=r.x0-10&&x<=r.x1+10&&y>=r.y0-10&&y<=r.y1+10),mesh.name).toBe(true);
        }
      }
      for(const id of ['C-HALL-BATH','C-PRIVATE-BED','C-BED-CLOSET','DOOR-101-102']){
        const spec=INTERIOR_DOORS.find(d=>d.id===id)!,registration=doors.find(d=>d.id===id)!;
        expect(registration.passage!.halfClearWidthM*2).toBeCloseTo(spec.widthMm/1000,6);
        const leaf=scene.meshes.find(m=>m.metadata?.doorId===id&&m.name.includes('animované krídlo'))!;
        registration.apply(0,0);leaf.computeWorldMatrix(true);
        const b=leaf.getBoundingInfo().boundingBox;
        expect(b.minimumWorld.x).toBeCloseTo(sceneXM(spec.startMm),5);
        expect(b.maximumWorld.x).toBeCloseTo(sceneXM(spec.startMm+spec.widthMm),5);
        registration.apply(1,0);leaf.computeWorldMatrix(true);
        expect(leaf.checkCollisions).toBe(true);
        if(spec.motion==='POCKET_SLIDING') expect(Math.abs(leaf.getBoundingInfo().boundingBox.centerWorld.z-sceneZM((spec.wallSpanMm[0]+spec.wallSpanMm[1])/2))).toBeLessThan(.001);
      }
      expect(scene.meshes.some(m=>m.name.startsWith(baseline.BEDROOM_FITOUT.id))).toBe(false);
      // Both pieces of the load-bearing kitchen wall are meshed as 300 mm masonry;
      // the cathedral ceiling continues over the kitchen bay to the east facade
      // and is closed above the whole wall line (the door lintel reaches the wall
      // crown), above the corridor spine's top and above the corridor mouth.
      expect(scene.meshes.some(m=>m.name==='Vnútorná stena C-KITCHEN-BEARING-WALL · nosná 300 mm')).toBe(true);
      expect(scene.meshes.some(m=>m.name==='Vnútorná stena C-KITCHEN-BEARING-WALL-E · nosná 300 mm')).toBe(true);
      expect(scene.meshes.some(m=>/IW-TECH-(WEST|PIER|NORTH)/.test(m.name))).toBe(false);
      expect(scene.meshes.some(m=>/^1\.03 .* · SDK podhľad/.test(m.name))).toBe(false);
      for(const name of ['1.03 · šikmý SDK podhľad západ · kuchynský záliv · +3,619 → +4,850','1.03 · šikmý SDK podhľad východ · kuchynský záliv · +2,750 → +4,850',
        '1.03 · južný štít podhľadu · ústie chodby','1.03 · štít podhľadu · nad východnou stenou chodby','1.03 · južný štít podhľadu · nad nosnou stenou kuchyne']){
        expect(scene.meshes.some(m=>m.name===name),name).toBe(true);
      }
      expect(scene.meshes.some(m=>/technickej miestnosti|nad technickou miestnosťou/.test(m.name)&&m.name.startsWith('1.03'))).toBe(false);
      const gable=scene.meshes.find(m=>m.name==='1.03 · južný štít podhľadu · nad nosnou stenou kuchyne')!;
      gable.computeWorldMatrix(true);
      const gableBox=gable.getBoundingInfo().boundingBox;
      expect(gableBox.minimumWorld.y).toBeCloseTo(3.125,3);
      expect(gableBox.maximumWorld.y).toBeCloseTo(4.85,3);
      expect(gableBox.minimumWorld.x).toBeCloseTo(sceneXM(KITCHEN_BEARING_WALL.x0),3);
      expect(Math.abs(gableBox.minimumWorld.z-sceneZM(KITCHEN_BEARING_WALL.y1))+Math.abs(gableBox.maximumWorld.z-sceneZM(KITCHEN_BEARING_WALL.y0))).toBeLessThan(.002);
      // The technical-room door in the bearing wall has a 300 mm deep lining and a lintel to the wall crown; its leaf opens into the kitchen.
      const techDoor=INTERIOR_DOORS.find(d=>d.id==='DOOR-103-107')!;
      const lintel=scene.meshes.find(m=>m.name===`${techDoor.label} · preklad`)!;
      lintel.computeWorldMatrix(true);
      const lintelBox=lintel.getBoundingInfo().boundingBox;
      expect(lintelBox.maximumWorld.y).toBeCloseTo(3.125,3);
      expect(lintelBox.minimumWorld.y).toBeCloseTo(2.1,3);
      expect(Math.abs(lintelBox.minimumWorld.z-sceneZM(techDoor.wallSpanMm[1]))+Math.abs(lintelBox.maximumWorld.z-sceneZM(techDoor.wallSpanMm[0]))).toBeLessThan(.002);
      const techRegistration=doors.find(d=>d.id==='DOOR-103-107')!;
      const techLeaf=scene.meshes.find(m=>m.metadata?.doorId==='DOOR-103-107'&&m.name.includes('animované krídlo'))!;
      techRegistration.apply(1,0);techLeaf.computeWorldMatrix(true);
      const openLeafBox=techLeaf.getBoundingInfo().boundingBox;
      expect(openLeafBox.minimumWorld.z).toBeLessThan(sceneZM(techDoor.wallSpanMm[1]));
      expect(openLeafBox.maximumWorld.x).toBeCloseTo(sceneXM(techDoor.startMm+techDoor.widthMm),1);
      techRegistration.apply(0,0);techLeaf.computeWorldMatrix(true);
    } finally {scene.dispose();engine.dispose();}
  });
});
