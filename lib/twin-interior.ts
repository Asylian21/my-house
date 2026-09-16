/** Active 3D revision: the same default C geometry shown in /koncept-2d?variant=c. */
import * as original from './twin-interior-baseline';
import { createConcept, DEFAULT_NESTED_CONCEPT, rect } from './floor-plan-concept';
import type { Point2Mm } from './twin-site';
import type { InteriorRoom, RectMm } from './twin-interior-baseline';
import { CHILDREN_DESIGN_ID, CHILDREN_DOUBLE_WINDOW } from './twin-children-design';
import { acousticWallLayers, acousticWallSpec } from './acoustic-walls';
import { BATHROOM_FITOUT as serviceBathroomFitout } from './technical-design';
import { OFFICE_DESK_PRODUCT } from './twin-office-desk';
export * from './twin-interior-baseline';
export { TECHNICAL_HEATING_FITOUT, WC_FITOUT } from './technical-design';

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
export const ACTIVE_ACOUSTIC_WALLS = INTERIOR_WALLS.flatMap(wall => {
  const spec = acousticWallSpec(wall);
  return spec ? [{ ...spec, rectMm: wall.rectMm, layers: acousticWallLayers(wall) }] : [];
});
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
const bathroomEntry=INTERIOR_DOORS.find(door=>door.id==='DOOR-102-105')!;
export const BATHROOM_FITOUT={
  ...serviceBathroomFitout,
  // Wall-mounted radiator follows the new bathroom face; shower and glazing stay put.
  towelRadiator:{...serviceBathroomFitout.towelRadiator,footprintMm:{...serviceBathroomFitout.towelRadiator.footprintMm,
    y0:INTERIOR_WALLS.find(w=>w.id==='IW-STUDY-NORTH')!.rectMm.y1,
    y1:INTERIOR_WALLS.find(w=>w.id==='IW-STUDY-NORTH')!.rectMm.y1 + serviceBathroomFitout.towelRadiator.footprintMm.y1-serviceBathroomFitout.towelRadiator.footprintMm.y0}},
  // The clear landing begins beyond the complete centred doorway, including its frame.
  clearFloorRectMm:{...serviceBathroomFitout.clearFloorRectMm,y0:bathroomEntry.startMm+bathroomEntry.widthMm},
};
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

type WardrobeStyle=original.HallwayBuiltInWardrobe['style'];
export type HallwayBuiltInWardrobe = Omit<original.HallwayBuiltInWardrobe,'roomId'|'nicheRectIndex'|'style'> & {
  roomId:string; nicheRectIndex:number; endClearanceMm?:number;
  /** Narrow cabinetry may use hinged fronts instead of sliding panels. */
  style:Omit<WardrobeStyle,'opening'>&{opening:WardrobeStyle['opening']|'HANDLELESS_HINGED_SOFT_CLOSE'};
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
    // The door lining projects 12 mm past the wall face at the hall-end cabinet's door-side end.
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
type OriginalEnsuite=typeof original.ENSUITE_BATHROOM_FITOUT;
/** C's bathroom is L-shaped and entered from the hall only; every fixture faces differently from the source plan. */
export type EnsuiteBathroomFitout=Omit<OriginalEnsuite,'id'|'sourceId'|'corridorDoorId'|'bedroomDoorId'|'bathtub'|'toilet'|'vanity'>&{
  id:string;sourceId:string;corridorDoorId:string;bedroomDoorId:null;
  /** The bath's open long side: EAST along the west wall, NORTH along the street wall, WEST along the east wall. */
  bathtub:Omit<OriginalEnsuite['bathtub'],'facing'>&{facing:'EAST'|'NORTH'|'WEST'};
  /** Direction the bowl points, away from its cistern wall. */
  toilet:Omit<OriginalEnsuite['toilet'],'facing'>&{facing:'NORTH'|'EAST'|'SOUTH'|'WEST'};
  /** Side the user stands on, away from the vanity's wall. */
  vanity:Omit<OriginalEnsuite['vanity'],'facing'>&{facing:'WEST'|'NORTH'|'EAST'};
  towelRadiator:Omit<typeof original.BATHROOM_FITOUT.towelRadiator,'id'|'wallId'|'facing'>&{id:string;wallId:string;facing:'EAST'};
};
// Shared by living layouts A/B: the client's sketch puts the bath under the
// window, the WC on the right and the vanity on the left, after a 500 mm shift.
export const ENSUITE_BATHROOM_FITOUT:EnsuiteBathroomFitout={
  ...original.ENSUITE_BATHROOM_FITOUT,id:'C-BATHROOM-111',sourceId:ACTIVE_LAYOUT_ID,
  corridorDoorId:'C-HALL-BATH',bedroomDoorId:null,
  bathtub:{...original.ENSUITE_BATHROOM_FITOUT.bathtub,footprintMm:bath,facing:'NORTH',
    innerBasinMm:rect(bath.x0+100,bath.y0+60,bath.x1-100,bath.y1-80)},
  toilet:{...original.ENSUITE_BATHROOM_FITOUT.toilet,footprintMm:toilet,facing:'WEST',
    concealedCisternRectMm:rect(toilet.x1-200,toilet.y0-50,toilet.x1,toilet.y1+50)},
  vanity:{...original.ENSUITE_BATHROOM_FITOUT.vanity,footprintMm:basin,facing:'EAST',
    basinFootprintMm:rect(basin.x0+70,basin.y0+60,basin.x1-40,basin.y1-60),
    mirrorPlanRectMm:rect(basin.x0+26,basin.y0+30,basin.x0+40,basin.y1-30),mirrorTopElevationMm:2000},
  towelRadiator:{...original.BATHROOM_FITOUT.towelRadiator,id:'C-BATHROOM-111-TOWEL-RADIATOR',wallId:'C-CLOSET-EAST',
    footprintMm:ACTIVE_CONCEPT.bathroomRadiator!,facing:'EAST'},
  clearFloorRectMm:rect(basin.x1,bath.y1,toilet.x0,basin.y1),
  vanityClearanceRectMm:rect(basin.x1,basin.y0,basin.x1+750,basin.y1),
};

// Sink and shelves use the new alcove; the full parking lane and garden door stay free.
const garageBay=ACTIVE_CONCEPT.garageBay!;
const garagePartition=INTERIOR_WALLS.find(wall=>wall.id==='C-GARAGE-PARTITION')!.rectMm;
const originalMower=original.GARAGE_FITOUT.mower;
export const GARAGE_FITOUT={
  ...original.GARAGE_FITOUT,id:'C-GARAGE-FITOUT',sourceId:ACTIVE_LAYOUT_ID,entryDoorId:null,
  utilitySink:{...original.GARAGE_FITOUT.utilitySink,
    footprintMm:rect(garageBay.x1-500,3704,garageBay.x1,4304),innerBasinMm:rect(garageBay.x1-445,3774,garageBay.x1-65,4234)},
  storageRack:{...original.GARAGE_FITOUT.storageRack,
    footprintMm:ACTIVE_CONCEPT.garageShelves[0],facing:'SOUTH' as const},
  mower:{...originalMower,
    footprintMm:shift(originalMower.footprintMm,garagePartition.x0-20-originalMower.footprintMm.x1)},
  overSinkShelves:{...original.GARAGE_FITOUT.overSinkShelves,
    footprintMm:rect(garageBay.x1-290,3654,garageBay.x1,4354)},
  sinkServiceRectMm:rect(garageBay.x1-1300,3704,garageBay.x1-500,4304),
  entryApproachRectMm:rect(garageBay.x0,4404,garageBay.x1-500,5104),
};
const officeNorthFace=INTERIOR_WALLS.find(wall=>wall.id==='IW-STUDY-NORTH')!.rectMm.y0;
// Preserve the accepted west-facing workstation axis and its wall position.
// Width runs along plan Y; depth runs along X, into the room.
const officeDeskCenterY=4404;
const officeDeskWest=original.OFFICE_FITOUT.desk.footprintMm.x0-650;
export const OFFICE_FITOUT={
  ...original.OFFICE_FITOUT,sourceId:ACTIVE_LAYOUT_ID,
  desk:{...original.OFFICE_FITOUT.desk,wallId:'C-ENTRY-OFFICE-EAST',
    product:OFFICE_DESK_PRODUCT,
    topThicknessMm:OFFICE_DESK_PRODUCT.topThicknessMm,
    footprintMm:rect(officeDeskWest,officeDeskCenterY-OFFICE_DESK_PRODUCT.widthMm/2,
      officeDeskWest+OFFICE_DESK_PRODUCT.depthMm,officeDeskCenterY+OFFICE_DESK_PRODUCT.widthMm/2),
    monitor:{...original.OFFICE_FITOUT.desk.monitor,centerMm:{x:23792,y:4404}}},
  chair:{...original.OFFICE_FITOUT.chair,footprintMm:shift(original.OFFICE_FITOUT.chair.footprintMm,-650),centerMm:{x:24862,y:4404}},
  whiteboard:{...original.OFFICE_FITOUT.whiteboard,
    footprintMm:{...original.OFFICE_FITOUT.whiteboard.footprintMm,y0:officeNorthFace-15,y1:officeNorthFace}},
  clearEntryRectMm:{...original.OFFICE_FITOUT.clearEntryRectMm,y1:officeNorthFace},
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
// chair by the facade on the east wall, and the 2.15 m wardrobe backed onto
// the hall wall in the east corner. Its end is 49 mm beyond the door opening;
// the east-hinged leaf and handle clear it throughout the inward 90-degree swing.
const boyRoom=ACTIVE_CONCEPT.rooms.find(r=>r.number==='1.09')!.rectsMm[0];
const girlRoom=ACTIVE_CONCEPT.rooms.find(r=>r.number==='1.08')!.rectsMm[0];
const mirrorY=(y:number)=>girlRoom.y0+boyRoom.y1-y;
/** Reflect a boy's-room footprint across the hall axis into the girl's room. */
const mirror=(r:RectMm):RectMm=>rect(r.x0,mirrorY(r.y1),r.x1,mirrorY(r.y0));
const boy:ChildBedroomFitout={
  ...garden,id:'C-BOY-109',sourceId:CHILDREN_DESIGN_ID,theme:'MIDNIGHT_SAND',childAgeRange:[3,7],
  bed:{...garden.bed,footprintMm:rect(15243,8519,16783,10699),mattressFootprintMm:rect(15313,8599,16713,10599),headboardRectMm:rect(15243,10599,16783,10699),facing:'SOUTH',mattressWidthMm:1400,mattressLengthMm:2000,frameHeightMm:260,mattressTopElevationMm:460,headboardTopElevationMm:1050},
  wardrobe:{...garden.wardrobe,footprintMm:rect(18391,7791,20541,8391),facing:'NORTH',heightMm:2450,doorCount:3},
  desk:{...garden.desk,footprintMm:rect(19241,10149,20541,10699),facing:'SOUTH',topElevationMm:540},
  chair:{...garden.chair,footprintMm:rect(19641,9549,20141,10049),centerMm:{x:19891,y:9799},facing:'NORTH',seatElevationMm:300,backTopElevationMm:580,wheelCount:0},
  featureWall:{...garden.featureWall,footprintMm:rect(15243,7791,15265,10699),facing:'EAST',topElevationMm:1080,motif:'OAK_RIBBON'},
  // The centred double window leaves the desk and board on the east side.
  pinboard:{...garden.pinboard,footprintMm:rect(20519,9549,20541,10649),facing:'WEST',bottomElevationMm:800,heightMm:650},
  readingRectMm:rect(15293,7881,16043,8361),bookcaseRectMm:rect(16293,7791,16943,8091),storageFacing:'NORTH',artUrl:'/assets/textures/child-woodland-albedo.png',
  // The entry zone ends before the extended wardrobe beside the east hinge.
  clearEntryRectMm:rect(17412,7791,18361,8591),clearPlayRectMm:rect(16903,8641,19541,10049),windowClearanceRectMm:rect(CHILDREN_DOUBLE_WINDOW.startXmm,10099,CHILDREN_DOUBLE_WINDOW.startXmm+CHILDREN_DOUBLE_WINDOW.widthMm,10699),
};
const girl:ChildBedroomFitout={
  ...garden,id:'C-GIRL-108',sourceId:CHILDREN_DESIGN_ID,roomId:'ROOM-1-08',entryDoorId:'DOOR-102-108',gardenWindowId:'FRONT-05',theme:'SAGE_GLOW',childAgeRange:[3,7],
  bed:{...boy.bed,footprintMm:mirror(boy.bed.footprintMm),mattressFootprintMm:mirror(boy.bed.mattressFootprintMm),headboardRectMm:mirror(boy.bed.headboardRectMm),facing:'NORTH'},
  wardrobe:{...boy.wardrobe,footprintMm:mirror(boy.wardrobe.footprintMm),facing:'SOUTH'},
  desk:{...boy.desk,footprintMm:mirror(boy.desk.footprintMm),facing:'NORTH'},
  chair:{...boy.chair,footprintMm:mirror(boy.chair.footprintMm),centerMm:{x:boy.chair.centerMm.x,y:mirrorY(boy.chair.centerMm.y)},facing:'SOUTH'},
  featureWall:{...boy.featureWall,footprintMm:mirror(boy.featureWall.footprintMm)},
  // Matching centred street window; the pinboard stays on the east wall.
  pinboard:{...garden.pinboard,footprintMm:rect(20519,3554,20541,4654),facing:'WEST',bottomElevationMm:800,heightMm:650},
  readingRectMm:mirror(boy.readingRectMm),bookcaseRectMm:mirror(boy.bookcaseRectMm),storageFacing:'SOUTH',artUrl:'/assets/textures/child-garden-albedo.png',
  // The same east hinge and clear entry zone, reflected across the hall.
  clearEntryRectMm:rect(17412,5612,18361,6412),clearPlayRectMm:mirror(boy.clearPlayRectMm),windowClearanceRectMm:mirror(boy.windowClearanceRectMm),
};
export const CHILDRENS_BEDROOM_FITOUTS:readonly ChildBedroomFitout[]=[boy,girl];

// 12. 9. 2026: the kitchen's back wall is 300 mm load-bearing masonry (ring beam
// and steel roof frames of the cathedral ceiling), running in one line from the
// corridor mouth to the east facade with the technical-room door in it. The back
// run keeps its 97 mm installation gap behind the carcasses and follows the
// wall's north face; the peninsula and appliances stay
// where they are; the east return now reaches this same back wall. The rear
// counter stops 80 mm before the door opening. The 13–14. 9. 2026 revisions move
// the door 150 + 50 mm east; this shared edge extends the rear cabinets, worktop,
// splashback and upper cabinets by 200 mm. The working aisle is 1 180 mm. Shared by
// living layouts A and B.
export const KITCHEN_BEARING_WALL:RectMm=ACTIVE_CONCEPT.kitchenBearingWall!;
/** The 660 mm piece between the technical-room door and the east facade. */
export const KITCHEN_BEARING_WALL_EAST:RectMm=ACTIVE_CONCEPT.kitchenBearingWallEast!;
const kitchenGapMm=original.KITCHEN_RUN.rectMm.y0-original.INTERIOR_WALLS.find(w=>w.id==='IW-KITCHEN-BACK')!.rectMm.y1;
const kitchenShiftMm=KITCHEN_BEARING_WALL.y1+kitchenGapMm-original.KITCHEN_RUN.rectMm.y0;
// 14 Sep correction: align the island's finished east edge with the back
// worktop, and retain the full former peninsula depth beside the east wall.
const kitchenBackRunRectMm={...shift(original.KITCHEN_RUN.rectMm,0,kitchenShiftMm),x1:KITCHEN_BEARING_WALL.x1-80};
export const KITCHEN_RUN:original.KitchenRun=Object.freeze({
  ...original.KITCHEN_RUN,backRunRevisionSourceId:'C-KITCHEN-DOOR-SHIFT-2026-09-14',
  designSourceId:'C-KITCHEN-OAK-BLACK-EAST-DW-2026-09-14',
  rectMm:kitchenBackRunRectMm,
  eastReturnRectMm:{...original.KITCHEN_RUN.eastReturnRectMm,y0:KITCHEN_BEARING_WALL.y1+kitchenGapMm,
    y1:original.KITCHEN_RUN.peninsulaRectMm.y1},
  fridgeUnitRectMm:shift(original.KITCHEN_RUN.fridgeUnitRectMm,0,kitchenShiftMm),
  sinkCenterXmm:24391,
  dishwasherXmm:[25391,25991] as const,
  hobCenterXmm:24996,
  ovenCenterXmm:23691,
  extractorCenterXmm:24996,
  extractorWidthMm:880,
  upperCabinets:{bottomMm:1600,topMm:2250,depthMm:500},
  peninsulaRectMm:{...original.KITCHEN_RUN.peninsulaRectMm,
    // Back worktop: 20 mm side nosing. Island: 10 mm side nosing.
    x1:kitchenBackRunRectMm.x1+20-10},
});
/** Finished outlines shared by the native 3D model, its collision guards and documentation.
 * The historical `peninsulaRectMm` key remains compatible with archived source geometry.
 */
export const KITCHEN_ISLAND=Object.freeze({
  revisionSourceId:'C-KITCHEN-OAK-BLACK-EAST-DW-2026-09-14',
  worktopRectMm:rect(KITCHEN_RUN.peninsulaRectMm.x0-10,KITCHEN_RUN.peninsulaRectMm.y0-10,
    KITCHEN_RUN.peninsulaRectMm.x1+10,KITCHEN_RUN.peninsulaRectMm.y1+KITCHEN_RUN.peninsulaOverhangMm),
  eastReturnWorktopRectMm:rect(KITCHEN_RUN.eastReturnRectMm.x0-20,KITCHEN_RUN.eastReturnRectMm.y0,
    KITCHEN_RUN.eastReturnRectMm.x1,KITCHEN_RUN.peninsulaRectMm.y1+KITCHEN_RUN.peninsulaOverhangMm),
  sidePassageMm:KITCHEN_RUN.eastReturnRectMm.x0-20-(KITCHEN_RUN.peninsulaRectMm.x1+10),
  // Front-to-front clearance of the two finished stone worktops, not the carcasses.
  workAisleMm:KITCHEN_RUN.peninsulaRectMm.y0-10-(KITCHEN_RUN.rectMm.y1+20),
  preparationWidthMm:KITCHEN_RUN.peninsulaRectMm.x1+10-(KITCHEN_RUN.sinkCenterXmm+300),
});

/** Authored kitchen fitout. All appliance zones are explicit: an X axis alone
 * cannot distinguish the wall run from the island. Historical source stays intact.
 */
export const KITCHEN_DESIGN=Object.freeze({
  id:KITCHEN_RUN.designSourceId,
  worktopThicknessMm:20,
  ovenTowerRectMm:rect(23391,kitchenBackRunRectMm.y0,23991,kitchenBackRunRectMm.y1),
  backWorktopRectMm:rect(23991,kitchenBackRunRectMm.y0,kitchenBackRunRectMm.x1+20,kitchenBackRunRectMm.y1+20),
  oven:{bottomMm:850,heightMm:595,widthMm:596,depthMm:548,door:'fully-retracting' as const},
  hobRectMm:rect(24596,11174,25396,11684),
  sinkBowlRectMm:rect(24091,12990,24691,13390),
  sinkDepthMm:200,
  dishwasherRectMm:rect(25391,12890,25991,13490),
  dishwasherOpenRectMm:rect(25391,12290,25991,12890),
  // Last 600 mm module toward EAST-04. It opens into the work aisle,
  // leaving the 900 mm side passage clear; one drawer unit separates it from the sink.
  islandModules:[
    {x0:23391,x1:23991,kind:'drawers'},
    {x0:23991,x1:24791,kind:'sink-waste'},
    {x0:24791,x1:25391,kind:'drawers'},
    {x0:25391,x1:25991,kind:'dishwasher'},
  ] as const,
  backModules:[23991,24501,25491,26001] as const,
  livingStorageRectMm:rect(23391,13510,26011,13770),
  eastStorageRectMm:rect(26941,11109,27541,13780),
  hood:{bottomMm:1600,bodyHeightMm:350,depthMm:293,ductDiameterMm:150,
    ventilation:'recirculation-with-top-return' as const},
  materials:{timber:'natural-oak',fronts:'natural-oak',stone:'black-stone-satin'} as const,
});
