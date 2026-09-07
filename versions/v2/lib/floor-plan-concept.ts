import { createGarageEnvelope } from './floor-plan-garage';
import { BEDROOM_FITOUT, INTERIOR_DOORS, INTERIOR_ROOMS, INTERIOR_WALLS, type InteriorDoor, type RectMm } from './twin-interior';

/** Separate study in plan millimetres. Never mutates the canonical 3D model. */
export interface ConceptSettings { expansion: number; bedWidth: number; wardrobe: boolean; garageConnected: boolean; layout: 'private' | 'nested' | 'wardrobe' | 'vestibule'; wardrobeDepth: number; gardenRecess: boolean; garageBayWidth: number; nestedClosetDepth: number }
export const DEFAULT_CONCEPT: ConceptSettings = { expansion: 0, bedWidth: 1800, wardrobe: true, garageConnected: true, layout: 'private', wardrobeDepth: 2000, gardenRecess: true, garageBayWidth: 1500, nestedClosetDepth: 1700 };
export const BED_LENGTH = 2200;
export const rect = (x0: number, y0: number, x1: number, y1: number): RectMm => ({ x0, y0, x1, y1 });
export const area = (rects: readonly RectMm[]) => rects.reduce((sum, r) => sum + (r.x1-r.x0)*(r.y1-r.y0)/1e6, 0);
export function normalizeConcept(input: Partial<ConceptSettings>): ConceptSettings {
  const bounded = (v: unknown, fallback: number, lo: number, hi: number) => typeof v === 'number' && Number.isFinite(v) ? Math.round(Math.max(lo, Math.min(hi, v))/50)*50 : fallback;
  const layout=input.layout==='vestibule'?'vestibule':input.layout==='wardrobe'?'wardrobe':input.layout==='nested'?'nested':'private';
  return { expansion: bounded(input.expansion, 0, 0, 600), bedWidth: bounded(input.bedWidth, 1800, 1600, 2200), wardrobe: typeof input.wardrobe === 'boolean' ? input.wardrobe : true, garageConnected: typeof input.garageConnected === 'boolean' ? input.garageConnected : true, layout, wardrobeDepth: bounded(input.wardrobeDepth, 2000, 2000, 2200), gardenRecess: typeof input.gardenRecess === 'boolean' ? input.gardenRecess : true, garageBayWidth: bounded(input.garageBayWidth,1500,1000,1700), nestedClosetDepth: bounded(input.nestedClosetDepth,1700,layout==='private'?1700:1600,1900) };
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

/** C's added bedroom wall leaves the bathroom approach open to the shared hall. */
function encloseNestedBedroom(base:ReturnType<typeof createNestedConcept>) {
  const right=base.suiteRight, top=base.dressing!.y1, bedroomBottom=top+140;
  const entranceTop=Math.min(top,7601);
  const rooms=base.rooms.map(room=>({...room,rectsMm:[...room.rectsMm]}));
  Object.assign(rooms.find(room=>room.number==='1.10')!,{
    rectsMm:[rect(11143,bedroomBottom,right,10699)],
  });
  const hall=rooms.find(room=>room.number==='1.02')!;
  hall.rectsMm.push(rect(13483,5744,right,top),rect(right,6560,right+140,entranceTop));
  const walls=base.walls.filter(w=>!['B-SUITE-WALL-S','B-SUITE-WALL-N'].includes(w.id));
  const add=(id:string,r:RectMm)=>walls.push({id,role:'PARTITION',rectMm:r,changed:true});
  add('C-BED-PRIVACY-W',rect(13483,top,right-1000,bedroomBottom));
  add('C-BED-PRIVACY-E',rect(right-200,top,right,bedroomBottom));
  add('C-OPEN-HALL-S',rect(right,3504,right+140,6560));
  add('C-OPEN-HALL-N',rect(right,entranceTop,right+140,10699));
  const doors=base.doors.filter(d=>d.id!=='C-HALL-BED').map(d=>d.id==='C-BED-BATH'
    ? {...d,id:'C-HALL-BATH',label:'Otvorený vstup z chodby → kúpeľňa · 800 mm',fromRoomId:'ROOM-1-02'}
    : d);
  doors.push({id:'C-PRIVATE-BED',label:'Spálňa za novou priečkou · dvere 800 mm',axis:'X',wallSpanMm:[top,bedroomBottom],startMm:right-1000,widthMm:800,heightMm:2100,leafWidthMm:800,swing:1,hinge:1,motion:'HINGED',fromRoomId:'ROOM-1-02',toRoomId:'ROOM-1-10'});
  return {...base,rooms,walls,doors,bedroomArea:area(rooms.find(room=>room.number==='1.10')!.rectsMm),sharedHallArea:area(hall.rectsMm)};
}

/** D separates sleeping from the shared routes, within C's existing suite. */
export function createConcept(input: ConceptSettings, original = false) {
  const settings=normalizeConcept(input);
  const base=createNestedConcept(settings.layout==='private'?{...settings,layout:'nested'}:settings,original);
  if(original||settings.layout!=='private') return {...(!original&&settings.layout==='nested'?encloseNestedBedroom(base):base),isPrivate:false};
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
  return {...base,settings,isPrivate:true,rooms,walls,doors,dressing,storageRuns,wardrobeRect:storageRuns[0],
    storageLength:right-1200-11143,dressingAisle:settings.nestedClosetDepth-600,
    bedroomArea:area(rooms.find(r=>r.number==='1.10')!.rectsMm)};
}
