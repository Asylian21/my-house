/** Active 3D revision: the same default C geometry shown in /koncept-2d?variant=c. */
import * as original from './twin-interior-baseline';
import { createConcept, DEFAULT_NESTED_CONCEPT, rect } from './floor-plan-concept';
import type { Point2Mm } from './twin-site';
import type { InteriorRoom, RectMm } from './twin-interior-baseline';
import { CHILDREN_DESIGN_ID } from './twin-children-design';
export * from './twin-interior-baseline';
export { TECHNICAL_HEATING_FITOUT, WC_FITOUT, BATHROOM_FITOUT } from './technical-design';

export const ACTIVE_LAYOUT_ID = 'C-2026-09-07';
export const ACTIVE_CONCEPT = createConcept(DEFAULT_NESTED_CONCEPT);
const shift = (r: RectMm, dx: number, dy = 0): RectMm => rect(r.x0+dx,r.y0+dy,r.x1+dx,r.y1+dy);
const points: Record<string, Point2Mm> = {
  'ROOM-1-01': {x:22100,y:4550}, 'ROOM-1-02':{x:22090,y:7100},
  'ROOM-1-04': {x:25100,y:5800}, 'ROOM-1-08':{x:17800,y:4850},
  'ROOM-1-09': {x:17800,y:9200}, 'ROOM-1-10':{x:14200,y:9400},
  'ROOM-1-11':{x:13800,y:4800}, 'ROOM-DRESSING':{x:12243,y:6500},
};
export const INTERIOR_ROOMS: readonly InteriorRoom[] = ACTIVE_CONCEPT.rooms.map(room=>({
  ...room, activeDesignAreaM2:original.roomAreaM2(room),
  name:room.id==='ROOM-1-09'?'Chlapčenská izba · dvor':room.id==='ROOM-1-08'?'Dievčenská izba · ulica':room.name,
  standingPointMm:points[room.id] ?? room.standingPointMm,
}));
export const INTERIOR_WALLS: readonly original.InteriorWall[] = ACTIVE_CONCEPT.walls;
/** Remove repeated corner volumes before meshing, retaining the exact plan union. */
export function nonOverlappingWalls(walls:readonly original.InteriorWall[]):original.InteriorWall[] {
  const occupied:RectMm[]=[], result:original.InteriorWall[]=[];
  for(const wall of walls){
    let parts:RectMm[]=[wall.rectMm];
    for(const o of occupied) parts=parts.flatMap(r=>{
      const x0=Math.max(r.x0,o.x0),y0=Math.max(r.y0,o.y0),x1=Math.min(r.x1,o.x1),y1=Math.min(r.y1,o.y1);
      if(x0>=x1||y0>=y1)return [r];
      return [rect(r.x0,r.y0,x0,r.y1),rect(x1,r.y0,r.x1,r.y1),rect(x0,r.y0,x1,y0),rect(x0,y1,x1,r.y1)].filter(p=>p.x1>p.x0&&p.y1>p.y0);
    });
    parts.forEach((r,i)=>result.push({...wall,id:i===0?wall.id:`${wall.id}-PART-${i+1}`,rectMm:r}));
    occupied.push(wall.rectMm);
  }
  return result;
}
export const INTERIOR_RENDER_WALLS=nonOverlappingWalls(INTERIOR_WALLS);
export const INTERIOR_DOORS: readonly original.InteriorDoor[] = ACTIVE_CONCEPT.doors.map(door=>({
  ...door, label:door.id==='DOOR-102-108'?'Chodba → detská izba do ulice · 800 mm':door.label,
}));
export function roomAt(point:Point2Mm):InteriorRoom|null {
  return INTERIOR_ROOMS.find(room=>room.rectsMm.some(r=>point.x>=r.x0&&point.x<=r.x1&&point.y>=r.y0&&point.y<=r.y1))??null;
}
export function totalActiveFloorAreaM2() { return INTERIOR_ROOMS.reduce((sum,r)=>sum+original.roomAreaM2(r),0); }

// 2.20 x 1.80 m frame retained; a low upholstered bed leaves both glazing and doors free.
const bed=ACTIVE_CONCEPT.bed;
export const BEDROOM_FITOUT = {
  id:'C-BEDROOM-110',sourceId:ACTIVE_LAYOUT_ID,roomId:'ROOM-1-10',entryDoorId:'C-PRIVATE-BED',
  bed:{footprintMm:bed,mattressFootprintMm:rect(bed.x0+70,bed.y0+30,bed.x1-30,bed.y1-30),
    headboardRectMm:rect(bed.x0,bed.y0,bed.x0+70,bed.y1),facing:'EAST' as const,
    frameHeightMm:280,mattressTopElevationMm:540,headboardTopElevationMm:1120},
  bedsideRectsMm:[rect(11163,bed.y0-400,11563,bed.y0-80),rect(11163,bed.y1+80,11563,bed.y1+400)],
  clearancesMm:{side:ACTIVE_CONCEPT.sideClearance,foot:ACTIVE_CONCEPT.footClearance},
};

export type HallwayBuiltInWardrobe = Omit<original.HallwayBuiltInWardrobe,'roomId'|'nicheRectIndex'> & {
  roomId:string; nicheRectIndex:number; endClearanceMm?:number;
};
const wardrobeStyle=original.HALLWAY_BUILT_IN_WARDROBES[0].style;
export const HALLWAY_BUILT_IN_WARDROBES:readonly HallwayBuiltInWardrobe[] = [
  ...ACTIVE_CONCEPT.builtInCabinets.map(cabinet=>{
    const isEntry=cabinet.roomNumber==='1.01';
    const isHallEnd=cabinet.id==='C-HALL-END-CABINET';
    const room=INTERIOR_ROOMS.find(room=>room.number===cabinet.roomNumber)!;
    const r=cabinet.rectMm;
    return {
    ...original.HALLWAY_BUILT_IN_WARDROBES[0],id:cabinet.id,label:cabinet.label,
    sourceId:ACTIVE_LAYOUT_ID,roomId:room.id,
    nicheRectIndex:room.rectsMm.findIndex(floor=>r.x0>=floor.x0&&r.x1<=floor.x1&&r.y0>=floor.y0&&r.y1<=floor.y1),
    footprintMm:cabinet.rectMm,facing:'EAST' as const,
    doorCount:isEntry||isHallEnd?2 as const:4 as const,
    ...(isHallEnd?{endClearanceMm:16}:{}),
    frontClearanceRectMm:rect(r.x1,r.y0,isHallEnd?r.x1+1000:22639,r.y1),
    style:{...wardrobeStyle,reededPanelIndices:isHallEnd?[]:isEntry?[1]:[1,2]},
  };}),
  ...ACTIVE_CONCEPT.storageRuns.map((r,i)=>({
    ...original.HALLWAY_BUILT_IN_WARDROBES[0],id:`C-DRESSING-${i}`,label:'Šatník · posuvné dubové čelá',
    sourceId:ACTIVE_LAYOUT_ID,roomId:'ROOM-DRESSING',nicheRectIndex:0,footprintMm:r,
    facing:i===0?'EAST' as const:'WEST' as const,doorCount:2 as const,
    frontClearanceRectMm:rect(11743,ACTIVE_CONCEPT.dressing!.y0,12743,ACTIVE_CONCEPT.dressing!.y1),
    style:{...wardrobeStyle,reededPanelIndices:[],ledEdges:['NORTH' as const]},
  })),
];
export const ENTRY_FITOUT={
  id:'C-ENTRY-BENCH',roomId:'ROOM-1-01',sourceId:ACTIVE_LAYOUT_ID,
  bench:{footprintMm:ACTIVE_CONCEPT.entryBench!,seatElevationMm:450,cushionThicknessMm:45},
  hookPanel:{footprintMm:rect(20842,3554,20866,4404)},
};

const fixtures=ACTIVE_CONCEPT.fixtures;
const bath=fixtures.bath, basin=fixtures.basin, toilet=fixtures.toilet;
export const ENSUITE_BATHROOM_FITOUT={
  ...original.ENSUITE_BATHROOM_FITOUT,id:'C-BATHROOM-111',sourceId:ACTIVE_LAYOUT_ID,
  corridorDoorId:'C-HALL-BATH',bedroomDoorId:null,
  bathtub:{...original.ENSUITE_BATHROOM_FITOUT.bathtub,footprintMm:bath,
    innerBasinMm:rect(bath.x0+80,bath.y0+100,bath.x1-60,bath.y1-100)},
  toilet:{...original.ENSUITE_BATHROOM_FITOUT.toilet,footprintMm:toilet,
    concealedCisternRectMm:rect(toilet.x0-50,3504,toilet.x1+50,3704)},
  vanity:{...original.ENSUITE_BATHROOM_FITOUT.vanity,footprintMm:basin,
    basinFootprintMm:rect(basin.x0+40,basin.y0+60,basin.x1-70,basin.y1-60),
    mirrorPlanRectMm:rect(basin.x1-30,basin.y0+30,basin.x1-16,basin.y1-30)},
  clearFloorRectMm:rect(bath.x1+30,4204,basin.x0,5100),
  vanityClearanceRectMm:rect(basin.x0-750,basin.y0,basin.x0,basin.y1),
};

// Sink and shelves use the new alcove; the full parking lane and garden door stay free.
export const GARAGE_FITOUT={
  ...original.GARAGE_FITOUT,id:'C-GARAGE-FITOUT',sourceId:ACTIVE_LAYOUT_ID,entryDoorId:null,
  utilitySink:{...original.GARAGE_FITOUT.utilitySink,
    footprintMm:rect(11842,3704,12342,4304),innerBasinMm:rect(11897,3774,12277,4234)},
  storageRack:{...original.GARAGE_FITOUT.storageRack,
    footprintMm:rect(10842,5104,12342,5604),facing:'SOUTH' as const},
  overSinkShelves:{...original.GARAGE_FITOUT.overSinkShelves,
    footprintMm:rect(12052,3654,12342,4354)},
  sinkServiceRectMm:rect(11042,3704,11842,4304),
  entryApproachRectMm:rect(10842,4404,11842,5104),
};
export const OFFICE_FITOUT={
  ...original.OFFICE_FITOUT,sourceId:ACTIVE_LAYOUT_ID,
  desk:{...original.OFFICE_FITOUT.desk,wallId:'C-ENTRY-OFFICE-EAST',
    footprintMm:shift(original.OFFICE_FITOUT.desk.footprintMm,-650),
    monitor:{...original.OFFICE_FITOUT.desk.monitor,centerMm:{x:23792,y:4404}}},
  chair:{...original.OFFICE_FITOUT.chair,footprintMm:shift(original.OFFICE_FITOUT.chair.footprintMm,-650),centerMm:{x:24862,y:4404}},
  cameraLookTargetMm:{x:25000,y:4350},
};

export type ChildBedroomFitout=Omit<original.ChildBedroomFitout,'roomId'|'entryDoorId'|'gardenWindowId'|'bed'|'wardrobe'|'desk'|'chair'|'pinboard'> & {
  roomId:string;entryDoorId:string;gardenWindowId:string;
  bed:Omit<original.ChildBedroomFitout['bed'],'facing'|'mattressWidthMm'|'mattressLengthMm'> & {facing:'NORTH'|'SOUTH';mattressWidthMm:number;mattressLengthMm:number};
  /** Backed onto the hall wall east of the centred door; the fronts face into the room. */
  wardrobe:Omit<original.ChildBedroomFitout['wardrobe'],'facing'|'doorCount'> & {facing:'NORTH'|'SOUTH';doorCount:number};
  desk:Omit<original.ChildBedroomFitout['desk'],'facing'> & {facing:'NORTH'|'SOUTH'};
  chair:Omit<original.ChildBedroomFitout['chair'],'facing'|'wheelCount'> & {facing:'NORTH'|'SOUTH';wheelCount:0};
  pinboard:Omit<original.ChildBedroomFitout['pinboard'],'facing'> & {facing:'NORTH'|'SOUTH'|'WEST'};
  childAgeRange:readonly [3,7];
  readingRectMm:RectMm; bookcaseRectMm:RectMm;
  storageFacing:'NORTH'|'SOUTH'; artUrl:string;
};
const garden=original.CHILDRENS_BEDROOM_FITOUTS[0];
// Both rooms are 5 298 × 2 908 mm: from the 300 mm bearing wall's face at 15243
// to 20541, and from a facade to a hall wall (7791 in the boy's room, 6412 in
// the girl's). The girl's room is the boy's room reflected across the hall's
// axis: bed, panel, reading corner and bookcase on the west wall, desk and
// chair by the facade on the east wall, and the 1.6 m wardrobe backed onto the
// hall wall in the east corner, 599 mm from the centred door's jamb, where the
// former toy shelf stood. Both door leaves swing away from the wardrobes.
const boyRoom=ACTIVE_CONCEPT.rooms.find(r=>r.number==='1.09')!.rectsMm[0];
const girlRoom=ACTIVE_CONCEPT.rooms.find(r=>r.number==='1.08')!.rectsMm[0];
const mirrorY=(y:number)=>girlRoom.y0+boyRoom.y1-y;
/** Reflect a boy's-room footprint across the hall axis into the girl's room. */
const mirror=(r:RectMm):RectMm=>rect(r.x0,mirrorY(r.y1),r.x1,mirrorY(r.y0));
const boy:ChildBedroomFitout={
  ...garden,id:'C-BOY-109',sourceId:CHILDREN_DESIGN_ID,theme:'MIDNIGHT_SAND',childAgeRange:[3,7],
  bed:{...garden.bed,footprintMm:rect(15243,8519,16783,10699),mattressFootprintMm:rect(15313,8599,16713,10599),headboardRectMm:rect(15243,10599,16783,10699),facing:'SOUTH',mattressWidthMm:1400,mattressLengthMm:2000,frameHeightMm:260,mattressTopElevationMm:460,headboardTopElevationMm:1050},
  wardrobe:{...garden.wardrobe,footprintMm:rect(18941,7791,20541,8391),facing:'NORTH',heightMm:2450,doorCount:3},
  desk:{...garden.desk,footprintMm:rect(19241,10149,20541,10699),facing:'SOUTH',topElevationMm:540},
  chair:{...garden.chair,footprintMm:rect(19641,9549,20141,10049),centerMm:{x:19891,y:9799},facing:'NORTH',seatElevationMm:300,backTopElevationMm:580,wheelCount:0},
  featureWall:{...garden.featureWall,footprintMm:rect(15243,7791,15265,10699),facing:'EAST',topElevationMm:1080,motif:'OAK_RIBBON'},
  pinboard:{...garden.pinboard,footprintMm:rect(19291,10677,20491,10699),facing:'SOUTH',bottomElevationMm:800,heightMm:650},
  readingRectMm:rect(15293,7881,16043,8361),bookcaseRectMm:rect(16293,7791,16943,8091),storageFacing:'NORTH',artUrl:'/assets/textures/child-woodland-albedo.png',
  // The entry zone covers the leaf's sweep: hinged east, it opens towards the west.
  clearEntryRectMm:rect(16972,7791,18372,8591),clearPlayRectMm:rect(16903,8641,19541,10049),windowClearanceRectMm:rect(17000,10099,19200,10699),
};
const girl:ChildBedroomFitout={
  ...garden,id:'C-GIRL-108',sourceId:CHILDREN_DESIGN_ID,roomId:'ROOM-1-08',entryDoorId:'DOOR-102-108',gardenWindowId:'FRONT-05',theme:'SAGE_GLOW',childAgeRange:[3,7],
  bed:{...boy.bed,footprintMm:mirror(boy.bed.footprintMm),mattressFootprintMm:mirror(boy.bed.mattressFootprintMm),headboardRectMm:mirror(boy.bed.headboardRectMm),facing:'NORTH'},
  wardrobe:{...boy.wardrobe,footprintMm:mirror(boy.wardrobe.footprintMm),facing:'SOUTH'},
  desk:{...boy.desk,footprintMm:mirror(boy.desk.footprintMm),facing:'NORTH'},
  chair:{...boy.chair,footprintMm:mirror(boy.chair.footprintMm),centerMm:{x:boy.chair.centerMm.x,y:mirrorY(boy.chair.centerMm.y)},facing:'SOUTH'},
  featureWall:{...boy.featureWall,footprintMm:mirror(boy.featureWall.footprintMm)},
  // The street windows sit over the bed and desk, so the pinboard moves to the east wall.
  pinboard:{...garden.pinboard,footprintMm:rect(20519,3554,20541,4654),facing:'WEST',bottomElevationMm:800,heightMm:650},
  readingRectMm:mirror(boy.readingRectMm),bookcaseRectMm:mirror(boy.bookcaseRectMm),storageFacing:'SOUTH',artUrl:'/assets/textures/child-garden-albedo.png',
  // Hinged west, the leaf opens towards the east; the zone is the boy's, mirrored about the door's centre.
  clearEntryRectMm:rect(17412,5612,18812,6412),clearPlayRectMm:mirror(boy.clearPlayRectMm),windowClearanceRectMm:mirror(boy.windowClearanceRectMm),
};
export const CHILDRENS_BEDROOM_FITOUTS:readonly ChildBedroomFitout[]=[boy,girl];
