import { createGarageEnvelope } from './floor-plan-garage';
import { SERVICE_CORE_REVISION } from './technical-design';
import { BEDROOM_FITOUT, INTERIOR_DOORS, INTERIOR_ROOMS, INTERIOR_WALLS, type InteriorDoor, type RectMm } from './twin-interior-baseline';

/** Studies derive from the preserved drawing; the active 3D model consumes variant C. */
export interface ConceptSettings { expansion: number; bedWidth: number; wardrobe: boolean; garageConnected: boolean; layout: 'private' | 'nested' | 'wardrobe' | 'vestibule'; wardrobeDepth: number; gardenRecess: boolean; garageBayWidth: number; nestedClosetDepth: number }
export const DEFAULT_CONCEPT: ConceptSettings = { expansion: 0, bedWidth: 1800, wardrobe: true, garageConnected: true, layout: 'private', wardrobeDepth: 2000, gardenRecess: true, garageBayWidth: 1500, nestedClosetDepth: 1700 };
export const DEFAULT_NESTED_CONCEPT: ConceptSettings = {...DEFAULT_CONCEPT,layout:'nested',garageConnected:false};
export const BED_LENGTH = 2200;
// C keeps both child rooms within 16 ± 0.5 m², including every slider step.
export const NESTED_MAX_EXPANSION = 100;
export interface ConceptCabinet {
  id: string;
  label: string;
  roomNumber: '1.01' | '1.02';
  facing: 'NORTH' | 'SOUTH' | 'EAST';
  rectMm: RectMm;
}
export const rect = (x0: number, y0: number, x1: number, y1: number): RectMm => ({ x0, y0, x1, y1 });
export const area = (rects: readonly RectMm[]) => rects.reduce((sum, r) => sum + (r.x1-r.x0)*(r.y1-r.y0)/1e6, 0);
export function normalizeConcept(input: Partial<ConceptSettings>): ConceptSettings {
  const bounded = (v: unknown, fallback: number, lo: number, hi: number) => typeof v === 'number' && Number.isFinite(v) ? Math.round(Math.max(lo, Math.min(hi, v))/50)*50 : fallback;
  const layout=input.layout==='vestibule'?'vestibule':input.layout==='wardrobe'?'wardrobe':input.layout==='nested'?'nested':'private';
  return { expansion: bounded(input.expansion, 0, 0, 600), bedWidth: bounded(input.bedWidth, 1800, 1600, 2200), wardrobe: typeof input.wardrobe === 'boolean' ? input.wardrobe : true, garageConnected: typeof input.garageConnected === 'boolean' ? input.garageConnected : layout!=='nested', layout, wardrobeDepth: bounded(input.wardrobeDepth, 2000, 2000, 2200), gardenRecess: typeof input.gardenRecess === 'boolean' ? input.gardenRecess : true, garageBayWidth: bounded(input.garageBayWidth,1500,1000,1700), nestedClosetDepth: bounded(input.nestedClosetDepth,1700,layout==='private'?1700:1600,1900) };
}
export function createVestibuleConcept(input: ConceptSettings, original = false) {
  const settings = normalizeConcept(input);
  const delta = original ? 0 : settings.expansion;
  const rooms = INTERIOR_ROOMS.map(r => ({ ...r, rectsMm: [...r.rectsMm] }));
  const walls = INTERIOR_WALLS.map(w => ({ ...w, rectMm: { ...w.rectMm }, changed: false }));
  let doors = INTERIOR_DOORS.map(d => ({ ...d }));
  const vestibule = [rect(13941,5561,15143,6462), rect(15143,5561,16142,7601), rect(16142,5561,16743,6420)];
  if (!original) {
    const bedroom = rooms.find(r => r.number === '1.10')!;
    bedroom.name = 'Spálňa do dvora';
    bedroom.rectsMm = [rect(11143,6699,15003,7741), rect(11143,7741,15003+delta,10699)];
    const kid = rooms.find(r => r.number === '1.09')!;
    kid.name = 'Detská izba · dvor';
    kid.rectsMm = [rect(15143+delta,7741,20641,10699)];
    rooms.find(r => r.number === '1.08')!.name = 'Detská izba · ulica';
    const hall = rooms.find(r => r.number === '1.02')!;
    hall.rectsMm = [rect(16282,6560,21543,7601), ...hall.rectsMm.slice(4)];
    const removed = ['IW-ROOM-110-EAST','IW-ROOM-109-SOUTH-W','IW-ROOM-109-SOUTH-E'];
    for (let i=walls.length-1;i>=0;i--) if(removed.includes(walls[i].id)) walls.splice(i,1);
    const add = (id:string, r:RectMm) => walls.push({id,role:'PARTITION',rectMm:r,changed:true});
    add('NEW-BED-KID',rect(15003+delta,7741,15143+delta,10699));
    add('NEW-KID-SOUTH-W',rect(15003,7601,17350,7741));
    add('NEW-KID-SOUTH-E',rect(18250,7601,21543,7741));
    add('NEW-SUITE-SOUTH',rect(16142,6560,16282,6690));
    add('NEW-SUITE-NORTH',rect(16142,7490,16282,7601));
    add('CLOSED-KID-BATH',rect(16743,3601,16942,4401));
    // An extension above the entrance makes a stepped room; it never narrows the vestibule.
    doors = doors.filter(d => !['DOOR-108-111','DOOR-102-109'].includes(d.id));
    doors.push({...INTERIOR_DOORS.find(d=>d.id==='DOOR-102-109')!,startMm:17350,widthMm:900});
    doors.push({id:'NEW-SUITE-ENTRY',label:'Vstup do rodičovskej zóny',axis:'Y',wallSpanMm:[16142,16282],startMm:6690,widthMm:800,heightMm:2100,leafWidthMm:800,swing:1,hinge:-1,fromRoomId:'ROOM-1-02',toRoomId:'SUITE'} satisfies InteriorDoor);
    if (!settings.garageConnected) {
      doors = doors.filter(d=>d.id!=='DOOR-102-112');
      add('CLOSED-GARAGE',rect(13742,5561,13941,6462));
    }
  }
  const sideClearance = (4000-settings.bedWidth)/2;
  const bedY = 6699+sideClearance;
  // Headboard against the solid garage wall, never across the full-height garden glazing.
  const bed = original ? BEDROOM_FITOUT.bed.footprintMm : rect(11143,bedY,13343,bedY+settings.bedWidth);
  const wardrobeRect = rect(14403+delta,7899,15003+delta,10299);
  const footClearance = 3860+delta-BED_LENGTH-(settings.wardrobe?600:0);
  return { ...createGarageEnvelope(true), rooms, walls, doors, vestibule: original ? [] : vestibule, bed, wardrobeRect, sideClearance, footClearance, bedroomArea: area(rooms.find(r=>r.number===(original?'1.08':'1.10'))!.rectsMm), kidGardenArea: area(rooms.find(r=>r.number==='1.09')!.rectsMm), kidStreetArea: area(rooms.find(r=>r.number==='1.08')!.rectsMm), bathroomArea: area(rooms.find(r=>r.number==='1.11')!.rectsMm), vestibuleArea: area(vestibule), settings };
}

export function createLinearConcept(input: ConceptSettings, original = false) {
  const settings = normalizeConcept(input);
  const previous = createVestibuleConcept(settings, original);
  const originalFixtures = { bath: rect(13980,3600,14780,5300), basin: rect(15370,3550,16170,4000), toilet: rect(15945,4710,16355,5310) };
  if (original || settings.layout === 'vestibule') return {
    ...previous, isWardrobe: false, dressing: null as RectMm | null, storageRuns: [] as RectMm[], storageLength: 0,
    dressingAisle: 0, bedroomDepth: 4000, suiteRight: 15003+settings.expansion, bathRight: 16743,
    privateHallArea: original ? 0 : previous.vestibuleArea, fixtures: originalFixtures,
    convertedTerraceArea: 0, garageDepth: 5245, structuralChanges: [] as typeof INTERIOR_WALLS[number][],
    frontWindowStart: 14965, sharedHallArea: area(previous.rooms.find(r=>r.number==='1.02')!.rectsMm),
  };

  // B is a new architectural study. The old garage cross-wall is deliberately
  // replaced, not silently treated as a movable non-bearing partition.
  const right=15003+settings.expansion, center=(11143+right)/2;
  const bathTop=5404, dressingBottom=5544, dressingTop=dressingBottom+settings.wardrobeDepth, bedroomBottom=dressingTop+140;
  const dressing=rect(11143,dressingBottom,right,dressingTop);
  const rooms=INTERIOR_ROOMS.map(r=>({...r,rectsMm:[...r.rectsMm]}));
  const replace=(number:string,name:string,rectsMm:RectMm[])=>Object.assign(rooms.find(r=>r.number===number)!,{name,rectsMm});
  replace('1.10','Spálňa do dvora',[rect(11143,bedroomBottom,right,10699)]);
  replace('1.11','Rodičovská kúpeľňa',[rect(11143,3504,right,bathTop)]);
  replace('1.08','Detská izba · ulica',[rect(right+140,3504,21242,6361)]);
  replace('1.09','Detská izba · dvor',[rect(right+140,7741,20641,10699)]);
  replace('1.12','Garáž',[rect(6944,3504,10842,!settings.gardenRecess?10699:8749)]);
  replace('1.02','Spoločná chodba',[rect(right+140,6560,21543,7601),...INTERIOR_ROOMS.find(r=>r.number==='1.02')!.rectsMm.slice(4)]);
  rooms.push({...INTERIOR_ROOMS.find(r=>r.number==='1.10')!,id:'ROOM-DRESSING',number:'1.14',name:'Priechodný šatník',documentedAreaM2:area([dressing]),rectsMm:[dressing]});

  const removed = new Set(['IW-GARAGE-EAST','IW-GARAGE-NORTH','IW-GARAGE-LOGGIA','IW-BATH-111-TOP-W','IW-BATH-111-TOP-E','IW-BATH-111-EAST-S','IW-BATH-111-EAST-N','IW-BED-108-TOP-W','IW-ROOM-110-EAST','IW-ROOM-109-SOUTH-W','IW-ROOM-109-SOUTH-E']);
  const structuralChanges=INTERIOR_WALLS.filter(w=>removed.has(w.id)&&w.role==='LOAD_BEARING');
  const walls=INTERIOR_WALLS.filter(w=>!removed.has(w.id)).map(w=>({...w,rectMm:{...w.rectMm},changed:false}));
  const add=(id:string,r:RectMm)=>walls.push({id,role:'PARTITION',rectMm:r,changed:true});
  add('B-GARAGE-WALL-S',rect(10842,3504,11143,6650));
  add('B-GARAGE-WALL-N',rect(10842,settings.garageConnected?7450:6650,11143,10699));
  add('B-SUITE-WALL-S',rect(right,3504,right+140,6650));
  add('B-SUITE-WALL-N',rect(right,7450,right+140,10699));
  add('B-BATH-WALL-W',rect(11143,bathTop,center-400,dressingBottom));
  add('B-BATH-WALL-E',rect(center+400,bathTop,right,dressingBottom));
  add('B-BED-WALL-W',rect(11143,dressingTop,center-400,bedroomBottom));
  add('B-BED-WALL-E',rect(center+400,dressingTop,right,bedroomBottom));
  add('B-STREET-KID-TOP',rect(right+140,6361,17141,6560));
  add('B-GARDEN-KID-SOUTH-W',rect(right+140,7601,17350,7741));
  add('B-GARDEN-KID-SOUTH-E',rect(18250,7601,21543,7741));
  // Window in the former bathroom moves into the expanded street-facing child room.
  const frontWindowStart=right+440;
  const replacedDoors=new Set(['DOOR-108-111','DOOR-102-111','DOOR-102-110','DOOR-102-112','DOOR-102-109']);
  const doors=INTERIOR_DOORS.filter(d=>!replacedDoors.has(d.id)).map(d=>({...d}));
  doors.push({...INTERIOR_DOORS.find(d=>d.id==='DOOR-102-109')!,startMm:17350,widthMm:900});
  const door=(id:string,label:string,axis:'X'|'Y',wallSpanMm:readonly[number,number],startMm:number,swing:-1|1,fromRoomId:string,toRoomId:string,motion:'HINGED'|'POCKET_SLIDING'='HINGED'):InteriorDoor=>({id,label,axis,wallSpanMm,startMm,widthMm:800,heightMm:2100,leafWidthMm:800,swing,hinge:-1,fromRoomId,toRoomId,motion,...(motion==='POCKET_SLIDING'?{pocketDirection:1 as const,pocketTravelMm:850}:{})});
  doors.push(door('B-HALL-DRESSING','Chodba → šatník · 800 mm','Y',[right,right+140],6650,1,'ROOM-1-02','ROOM-DRESSING'));
  doors.push(door('B-DRESSING-BATH','Šatník → kúpeľňa · 800 mm','X',[bathTop,dressingBottom],center-400,-1,'ROOM-DRESSING','ROOM-1-11'));
  doors.push(door('B-DRESSING-BED','Šatník → spálňa · posuvné 800 mm','X',[dressingTop,bedroomBottom],center-400,1,'ROOM-DRESSING','ROOM-1-10','POCKET_SLIDING'));
  if(settings.garageConnected) doors.push(door('B-GARAGE-DRESSING','Garáž → šatník · 800 mm','Y',[10842,11143],6650,-1,'ROOM-1-12','ROOM-DRESSING'));

  const storageRuns=[rect(11143,dressingBottom,center-500,dressingBottom+600),rect(center+500,dressingBottom,right,dressingBottom+600)];
  const bedroomDepth=10699-bedroomBottom, sideClearance=Math.floor((bedroomDepth-settings.bedWidth)/2);
  const bed=rect(11143,bedroomBottom+sideClearance,13343,bedroomBottom+sideClearance+settings.bedWidth);
  return {
    ...createGarageEnvelope(settings.gardenRecess),rooms,walls,doors,settings,isWardrobe:true,dressing,storageRuns,
    storageLength:right-11143-1000,dressingAisle:settings.wardrobeDepth-600,
    vestibule:[] as RectMm[],vestibuleArea:0,privateHallArea:0,
    bed,wardrobeRect:storageRuns[0],sideClearance,footClearance:right-bed.x1,bedroomDepth,suiteRight:right,bathRight:right,
    bedroomArea:area(rooms.find(r=>r.number==='1.10')!.rectsMm),
    kidGardenArea:area(rooms.find(r=>r.number==='1.09')!.rectsMm),
    kidStreetArea:area(rooms.find(r=>r.number==='1.08')!.rectsMm),
    bathroomArea:area(rooms.find(r=>r.number==='1.11')!.rectsMm),
    fixtures:{bath:rect(11193,3604,11993,5304),basin:rect(12300,3504,13300,4004),toilet:rect(right-700,4550,right-100,5100)},
    convertedTerraceArea:!settings.gardenRecess?(10842-6944)*(10699-9247)/1e6:0,
    garageDepth:!settings.gardenRecess?7195:5245,structuralChanges,frontWindowStart,
    sharedHallArea:area(rooms.find(r=>r.number==='1.02')!.rectsMm),
  };
}

/** C nests the closet beside the bedroom's entrance area and restores a garage bay. */
export function createNestedConcept(input: ConceptSettings, original = false) {
  const settings=normalizeConcept(input);
  const base=createLinearConcept(settings,original);
  if(original||settings.layout!=='nested') return {
    ...base,isNested:false,garageBay:null as RectMm|null,garageShelves:[] as RectMm[],
    bathLeft:original||settings.layout==='vestibule'?13941:11143,garageWindowStart:11715,
  };
  const right=base.suiteRight, bayRight=10842+settings.garageBayWidth, bathLeft=bayRight+140;
  const closetBottom=5744, closetTop=closetBottom+settings.nestedClosetDepth, bedroomBottom=closetTop+140;
  const dressing=rect(11143,closetBottom,13343,closetTop);
  const garageBay=rect(10842,3504,bayRight,5604);
  const rooms=base.rooms.map(r=>({...r,rectsMm:[...r.rectsMm]}));
  const replace=(number:string,name:string,rectsMm:RectMm[])=>Object.assign(rooms.find(r=>r.number===number)!,{name,rectsMm});
  replace('1.10','Spálňa do dvora',[rect(11143,bedroomBottom,right,10699),rect(13483,5744,right,bedroomBottom)]);
  replace('1.11','Kúpeľňa',[rect(bathLeft,3504,right,5604)]);
  replace('1.14','Šatník',[dressing]);
  replace('1.12','Garáž',[rect(6944,3504,10842,!settings.gardenRecess?10699:8749),garageBay]);
  const walls=base.walls.filter(w=>!w.id.startsWith('B-GARAGE-WALL')&&!w.id.startsWith('B-BATH-WALL')&&!w.id.startsWith('B-BED-WALL'));
  const add=(id:string,r:RectMm)=>walls.push({id,role:'PARTITION',rectMm:r,changed:true});
  add('C-GARAGE-BAY-EAST',rect(bayRight,3504,bathLeft,5604));
  add('C-GARAGE-BAY-RETURN',rect(10842,5604,bathLeft,5744));
  add('C-GARAGE-SPINE-S',rect(10842,5744,11143,5844));
  add('C-GARAGE-SPINE-N',rect(10842,settings.garageConnected?6644:5844,11143,10699));
  add('C-CLOSET-EAST',rect(13343,5744,13483,bedroomBottom));
  add('C-CLOSET-NORTH-W',rect(11143,closetTop,11793,bedroomBottom));
  add('C-CLOSET-NORTH-E',rect(12593,closetTop,13483,bedroomBottom));
  add('C-BATH-NORTH-W',rect(bathLeft,5604,right-1360,5744));
  add('C-BATH-NORTH-E',rect(right-560,5604,right,5744));
  const doors=base.doors.filter(d=>!['B-HALL-DRESSING','B-DRESSING-BATH','B-DRESSING-BED','B-GARAGE-DRESSING'].includes(d.id));
  const make=(id:string,label:string,axis:'X'|'Y',span:readonly[number,number],start:number,swing:-1|1,from:string,to:string,sliding=false):InteriorDoor=>({id,label,axis,wallSpanMm:span,startMm:start,widthMm:800,heightMm:2100,leafWidthMm:800,swing,hinge:-1,fromRoomId:from,toRoomId:to,motion:sliding?'POCKET_SLIDING':'HINGED',...(sliding?{pocketDirection:1 as const,pocketTravelMm:850}:{})});
  doors.push(make('C-HALL-BED','Chodba → spálňa · 800 mm','Y',[right,right+140],6650,1,'ROOM-1-02','ROOM-1-10'));
  doors.push(make('C-BED-BATH','Spálňa → kúpeľňa · 800 mm','X',[5604,5744],right-1360,-1,'ROOM-1-10','ROOM-1-11'));
  doors.push(make('C-BED-CLOSET','Spálňa → šatník · posuvné 800 mm','X',[closetTop,bedroomBottom],11793,1,'ROOM-1-10','ROOM-DRESSING',true));
  if(settings.garageConnected) doors.push(make('C-GARAGE-CLOSET','Garáž → šatník · 800 mm','Y',[10842,11143],5844,-1,'ROOM-1-12','ROOM-DRESSING'));
  const storageRuns=[rect(11143,settings.garageConnected?6744:closetBottom,11743,closetTop),rect(12743,closetBottom,13343,closetTop)];
  const sideClearance=Math.floor((10699-bedroomBottom-settings.bedWidth)/2);
  const bed=rect(11143,bedroomBottom+sideClearance,13343,bedroomBottom+sideClearance+settings.bedWidth);
  return {
    ...base,settings,rooms,walls,doors,isNested:true,dressing,storageRuns,
    storageLength:storageRuns.reduce((n,r)=>n+r.y1-r.y0,0),dressingAisle:1000,
    bed,wardrobeRect:storageRuns[0],sideClearance,footClearance:right-bed.x1,bedroomDepth:10699-bedroomBottom,
    bedroomArea:area(rooms.find(r=>r.number==='1.10')!.rectsMm),bathroomArea:area(rooms.find(r=>r.number==='1.11')!.rectsMm),
    bathLeft,bathRight:right,frontWindowStart:Math.round((bathLeft+right)/2-375),garageWindowStart:bayRight-1400,
    garageBay,garageShelves:[rect(10842,5104,bayRight,5604)],
    fixtures:{bath:rect(bathLeft+50,3554,bathLeft+800,5354),basin:rect(right-500,4554,right,5454),toilet:rect(right-1150,3504,right-750,4204)},
  };
}

/** C keeps the closet, bedroom entrance and child's corridor wall in one line. */
function encloseNestedBedroom(base:ReturnType<typeof createNestedConcept>) {
  const right=base.suiteRight;
  const hallWall=base.walls.find(w=>w.id==='B-GARDEN-KID-SOUTH-W')!.rectMm;
  const top=hallWall.y0, bedroomBottom=hallWall.y1;
  // This alignment fixes the closet's depth; old slider values cannot restore a step.
  const dressing={...base.dressing!,y1:top};
  const settings={...base.settings,nestedClosetDepth:top-dressing.y0};
  const storageRuns=base.storageRuns.map(r=>({...r,y1:top}));
  const bedroomDepth=10699-bedroomBottom, sideClearance=Math.floor((bedroomDepth-settings.bedWidth)/2);
  const bed=rect(base.bed.x0,bedroomBottom+sideClearance,base.bed.x1,bedroomBottom+sideClearance+settings.bedWidth);
  const doorStart=right-1000, doorEnd=right-200;
  // The WC backs onto the street wall; the vanity sits on the east wall.
  // Reserve their approaches as well as the inward swing of the aligned door.
  const fixtures={...base.fixtures,
    basin:rect(right-500,4204,right,4804),
    toilet:rect(right-1400,3504,right-1000,4204),
  };
  const rooms=base.rooms.map(room=>({...room,rectsMm:[...room.rectsMm]}));
  Object.assign(rooms.find(room=>room.number==='1.10')!,{
    rectsMm:[rect(11143,bedroomBottom,right,10699)],
  });
  rooms.find(room=>room.number==='1.14')!.rectsMm=[dressing];
  const hall=rooms.find(room=>room.number==='1.02')!;
  hall.rectsMm.push(rect(13483,5744,right,top),rect(right,6560,right+140,top));
  const walls=base.walls.filter(w=>!['B-SUITE-WALL-S','B-SUITE-WALL-N'].includes(w.id))
    .map(w=>w.id==='C-CLOSET-EAST'?{...w,rectMm:{...w.rectMm,y1:bedroomBottom}}
      :['C-CLOSET-NORTH-W','C-CLOSET-NORTH-E'].includes(w.id)?{...w,rectMm:{...w.rectMm,y0:top,y1:bedroomBottom}}
      :w.id==='C-BATH-NORTH-W'?{...w,rectMm:{...w.rectMm,x1:doorStart}}
      :w.id==='C-BATH-NORTH-E'?{...w,rectMm:{...w.rectMm,x0:doorEnd}}:w);
  const add=(id:string,r:RectMm)=>walls.push({id,role:'PARTITION',rectMm:r,changed:true});
  add('C-BED-PRIVACY-W',rect(13483,top,doorStart,bedroomBottom));
  add('C-BED-PRIVACY-E',rect(doorEnd,top,right,bedroomBottom));
  add('C-OPEN-HALL-S',rect(right,3504,right+140,6560));
  add('C-OPEN-HALL-N',rect(right,top,right+140,10699));
  const doors=base.doors.filter(d=>d.id!=='C-HALL-BED').map(d=>d.id==='C-BED-BATH'
    ? {...d,id:'C-HALL-BATH',label:'Otvorený vstup z chodby → kúpeľňa · 800 mm',startMm:doorStart,hinge:1 as const,fromRoomId:'ROOM-1-02'}
    : d.id==='C-BED-CLOSET'?{...d,wallSpanMm:[top,bedroomBottom] as const}:d);
  doors.push({id:'C-PRIVATE-BED',label:'Spálňa za novou priečkou · dvere 800 mm',axis:'X',wallSpanMm:[top,bedroomBottom],startMm:doorStart,widthMm:800,heightMm:2100,leafWidthMm:800,swing:1,hinge:1,motion:'HINGED',fromRoomId:'ROOM-1-02',toRoomId:'ROOM-1-10'});
  return {...base,settings,rooms,walls,doors,dressing,storageRuns,fixtures,wardrobeRect:storageRuns[0],
    storageLength:storageRuns.reduce((sum,r)=>sum+r.y1-r.y0,0),bed,sideClearance,bedroomDepth,
    bedroomArea:area(rooms.find(room=>room.number==='1.10')!.rectsMm),sharedHallArea:area(hall.rectsMm)};
}

/** C pairs deeper storage with a continuous, furnished entrance lobby. */
function balanceNestedChildRooms(base:ReturnType<typeof encloseNestedBedroom>) {
  const streetEast=20702, gardenEast=20541, storageBack=20842, hallLine=21543;
  const rooms=base.rooms.map(room=>({...room,rectsMm:[...room.rectsMm]}));
  const core=SERVICE_CORE_REVISION;
  const wc=rooms.find(room=>room.number==='1.06')!;
  wc.rectsMm=wc.rectsMm.map(r=>({...r,x1:r.x1+core.wcExpansionMm}));
  wc.standingPointMm={x:23733,y:9900};
  const technical=rooms.find(room=>room.number==='1.07')!;
  technical.rectsMm=[rect(core.technicalWestMm,8912,core.boilerBayWestMm,10712),rect(core.boilerBayWestMm,9112,25830,10712),rect(25830,9112,core.technicalFacadeInsideMm,11411),rect(core.boilerBayWestMm,7741,core.technicalFacadeInsideMm,9112)];
  technical.standingPointMm={x:26500,y:10750};
  const bathroom=rooms.find(room=>room.number==='1.05')!;
  bathroom.rectsMm=[rect(22783,6602,core.bathroomEastMm,8772),rect(core.bathroomEastMm,6602,27541,7601)];
  const street=rooms.find(room=>room.number==='1.08')!;
  street.rectsMm=[rect(base.suiteRight+140,3504,streetEast,6361)];
  const garden=rooms.find(room=>room.number==='1.09')!;
  garden.rectsMm=[rect(base.suiteRight+140,7741,gardenEast,10699)];
  // Move the office return 650 mm into the lobby, aligning it with the open door leaf.
  const office=rooms.find(room=>room.number==='1.04')!;
  office.rectsMm=[rect(23542,3504,27541,5400),...office.rectsMm.slice(1)];
  const entry=rooms.find(room=>room.number==='1.01')!;
  entry.rectsMm=[rect(storageBack,3504,22639,6361),rect(22639,3504,23339,5201)];
  const hall=rooms.find(room=>room.number==='1.02')!;
  // The former door approach is now inside the entrance lobby. Cabinet fronts
  // stay on the same corridor line; the extra 100 mm comes from both rooms.
  hall.rectsMm=hall.rectsMm.map(r=>r.x0===21543&&r.y0===5341
    ?rect(r.x0,6560,r.x1,r.y1)
    :r.x0===20942&&r.y0===7902?rect(storageBack,r.y0,r.x1,r.y1):r);
  const removed=new Set(['IW-BED-108-EAST','IW-BED-108-TOP-E','IW-ROOM-109-EAST','IW-CLOSET-SOUTH','IW-ENTRY-TOP-W','IW-ENTRY-TOP-E','IW-ENTRY-EAST','IW-ENTRY-STUDY']);
  const walls=base.walls.filter(w=>!removed.has(w.id)).map(w=>w.id==='IW-WC-EAST'?{...w,changed:true,rectMm:rect(24082+core.wcExpansionMm,8912,core.technicalWestMm,10712)}
    :w.id==='IW-BATH-105-NORTH'?{...w,changed:true,rectMm:{...w.rectMm,x1:core.boilerBayWestMm}}
    :w.id==='IW-BATH-105-SOUTH-E'?{...w,changed:true,rectMm:{...w.rectMm,x0:core.bathroomEastMm}}
    :w.rectMm.x0===25399&&w.rectMm.x1===25543&&w.rectMm.y0===7741?{...w,changed:true,rectMm:rect(core.bathroomEastMm,7741,core.boilerBayWestMm,8772)}:w);
  walls.push(
    {id:'C-KID-ENTRY-PARTITION',role:'PARTITION',changed:true,rectMm:rect(streetEast,3504,storageBack,6361)},
    {id:'C-KID-HALL-POCKET-WALL',role:'PARTITION',changed:true,rectMm:rect(18042,6361,21640,6560)},
    {id:'C-ENTRY-HALL-JAMB',role:'PARTITION',changed:true,rectMm:rect(22540,6361,22639,6560)},
    {id:'C-GARDEN-KID-EAST',role:'LOAD_BEARING',changed:true,rectMm:rect(gardenEast,7741,storageBack,10699)},
    {id:'C-GARDEN-CLOSET-SOUTH',role:'PARTITION',changed:true,rectMm:rect(storageBack,7741,hallLine,7902)},
    {id:'C-ENTRY-OFFICE-EAST',role:'LOAD_BEARING',changed:true,rectMm:rect(23339,3504,23542,5201)},
    {id:'C-ENTRY-OFFICE-RETURN',role:'LOAD_BEARING',changed:true,rectMm:rect(22842,5201,23542,5400)},
    // Close the change in thickness between the office jamb and corridor spine.
    {id:'C-OFFICE-NORTH-JAMB',role:'PARTITION',changed:true,rectMm:rect(22783,6352,22842,6412)},
  );
  const structuralChanges=[...base.structuralChanges,...INTERIOR_WALLS.filter(w=>removed.has(w.id)&&w.role==='LOAD_BEARING')];
  const doors=base.doors.map(d=>d.id==='DOOR-101-102'
    ?{...d,label:'Zádverie → centrálna chodba · posuvné 900 mm',wallSpanMm:[6361,6560] as const,startMm:21640,widthMm:900,leafWidthMm:900,motion:'POCKET_SLIDING' as const,pocketDirection:-1 as const,pocketTravelMm:950}
    :d.id==='DOOR-102-106'?{...d,label:'Dvere chodba → WC · otváravé 700/2100',motion:'HINGED' as const,hinge:1 as const,swing:1 as const,hingeOffsetMm:34,pocketDirection:undefined,pocketTravelMm:undefined,revisionSourceId:'C-WC-HINGED-2026-09-08'}
    :d.id==='DOOR-102-104'?{...d,label:'Zádverie → pracovňa · 800 mm',fromRoomId:'ROOM-1-01'}:d);
  const entryCabinet=rect(storageBack,4461,hallLine,6361);
  const entryBench=rect(storageBack,3554,storageBack+450,4404);
  const builtInCabinets:ConceptCabinet[]=[
    {id:'C-ENTRY-CABINET',label:'Súvislá skriňa v zádverí · posuvné čelá',roomNumber:'1.01',facing:'EAST',rectMm:entryCabinet},
    {id:'C-GARDEN-HALL-CABINET',label:'Vstavaná skriňa z chodby · dvor',roomNumber:'1.02',facing:'EAST',rectMm:rect(storageBack,7902,hallLine,10699)},
    // Stop at both door jambs, leaving a full metre between bedroom and bathroom.
    {id:'C-HALL-END-CABINET',label:'Vstavaná skriňa na konci chodby · posuvné dubové čelá',roomNumber:'1.02',facing:'EAST',rectMm:rect(13483,base.dressing!.y0,base.suiteRight-1000,base.dressing!.y1)},
  ];
  return {...base,rooms,walls,doors,structuralChanges,builtInCabinets,entryBench,
    kidStreetArea:area(street.rectsMm),kidGardenArea:area(garden.rectsMm),entryArea:area(entry.rectsMm),officeArea:area(office.rectsMm),
    entryClearArea:area(entry.rectsMm)-area([entryCabinet,entryBench]),
    sharedHallArea:area(hall.rectsMm),
    streetKidDesk:rect(19400,3650,20650,4250),gardenKidBed:rect(gardenEast-900,8000,gardenEast,10000),
  };
}

/** D separates sleeping from the shared routes, within C's existing suite. */
export function createConcept(input: ConceptSettings, original = false) {
  const settings=normalizeConcept(input);
  if(!original&&settings.layout==='nested') settings.expansion=Math.min(settings.expansion,NESTED_MAX_EXPANSION);
  const base=createNestedConcept(settings.layout==='private'?{...settings,layout:'nested'}:settings,original);
  const entryArea=area(base.rooms.find(r=>r.number==='1.01')!.rectsMm);
  const entryDefaults={builtInCabinets:[] as ConceptCabinet[],entryBench:null as RectMm|null,entryArea,entryClearArea:entryArea,officeArea:area(base.rooms.find(r=>r.number==='1.04')!.rectsMm),streetKidDesk:rect(19900,3650,21150,4250),gardenKidBed:rect(19400,8000,20300,10000)};
  if(original||settings.layout!=='private') return {...entryDefaults,...(!original&&settings.layout==='nested'?balanceNestedChildRooms(encloseNestedBedroom(base)):base),isPrivate:false};
  const right=base.suiteRight, top=base.dressing!.y1, bedroomBottom=top+140;
  const dressing=rect(11143,5744,right,top);
  const rooms=base.rooms.map(room=>({...room,rectsMm:[...room.rectsMm]}));
  Object.assign(rooms.find(r=>r.number==='1.10')!,{name:'Súkromná spálňa',rectsMm:[rect(11143,bedroomBottom,right,10699)]});
  Object.assign(rooms.find(r=>r.number==='1.14')!,{name:'Šatníkový vstup',rectsMm:[dressing]});
  const walls=base.walls.filter(w=>!['C-CLOSET-EAST','C-CLOSET-NORTH-W','C-CLOSET-NORTH-E','B-SUITE-WALL-S','B-SUITE-WALL-N'].includes(w.id));
  const add=(id:string,r:RectMm)=>walls.push({id,role:'PARTITION',rectMm:r,changed:true});
  add('D-BED-PRIVACY-W',rect(11143,top,right-1000,bedroomBottom));
  add('D-BED-PRIVACY-E',rect(right-200,top,right,bedroomBottom));
  add('D-SUITE-WALL-S',rect(right,3504,right+140,6600));
  add('D-SUITE-WALL-N',rect(right,7400,right+140,10699));
  const doors=base.doors.filter(d=>!['C-HALL-BED','C-BED-BATH','C-BED-CLOSET'].includes(d.id));
  doors.push({...base.doors.find(d=>d.id==='C-HALL-BED')!,id:'D-HALL-DRESSING',label:'Dom → šatníkový vstup · 800 mm',startMm:6600,toRoomId:'ROOM-DRESSING'});
  doors.push({...base.doors.find(d=>d.id==='C-BED-BATH')!,id:'D-DRESSING-BATH',label:'Šatníkový vstup → kúpeľňa · 800 mm',fromRoomId:'ROOM-DRESSING'});
  doors.push({id:'D-PRIVATE-BED',label:'Súkromná spálňa · zatvárateľné dvere 800 mm',axis:'X',wallSpanMm:[top,bedroomBottom],startMm:right-1000,widthMm:800,heightMm:2100,leafWidthMm:800,swing:1,hinge:-1,motion:'HINGED',fromRoomId:'ROOM-DRESSING',toRoomId:'ROOM-1-10'});
  // A single straight bank has fully accessible frontage; no double-counted L corner.
  const storageRuns=[rect(11143,top-600,right-1200,top)];
  return {...base,...entryDefaults,settings,isPrivate:true,rooms,walls,doors,dressing,storageRuns,wardrobeRect:storageRuns[0],
    storageLength:right-1200-11143,dressingAisle:settings.nestedClosetDepth-600,
    bedroomArea:area(rooms.find(r=>r.number==='1.10')!.rectsMm)};
}
