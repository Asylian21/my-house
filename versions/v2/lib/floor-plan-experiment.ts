import { area, createConcept, DEFAULT_CONCEPT, normalizeConcept, rect, type ConceptSettings } from './floor-plan-concept';
import type { InteriorDoor } from './twin-interior';

export interface ExperimentSettings extends Pick<ConceptSettings,'expansion'|'bedWidth'|'garageBayWidth'|'garageConnected'> {
  gardenRecess: boolean;
  alcoveWidth: number;
  passageDepth: number;
  doorOffset: number;
}
export const DEFAULT_EXPERIMENT: ExperimentSettings = {
  expansion:0,bedWidth:1800,garageBayWidth:1500,garageConnected:true,gardenRecess:true,
  alcoveWidth:2600,passageDepth:1000,doorOffset:200,
};
export function bedroomDoorOffsetMax(input: Pick<ExperimentSettings,'expansion'|'alcoveWidth'>) {
  return Math.min(600,Math.floor((3860+input.expansion-input.alcoveWidth-140-900)/50)*50);
}
export function normalizeExperiment(input: Partial<ExperimentSettings>): ExperimentSettings {
  const base=normalizeConcept({...DEFAULT_CONCEPT,...input});
  const bound=(v:unknown,fallback:number,min:number,max:number)=>typeof v==='number'&&Number.isFinite(v)?Math.max(min,Math.min(max,Math.round(v/50)*50)):fallback;
  const alcoveWidth=bound(input.alcoveWidth,2600,2000,2600);
  return {
    expansion:base.expansion,bedWidth:base.bedWidth,garageBayWidth:base.garageBayWidth,
    garageConnected:base.garageConnected,gardenRecess:typeof input.gardenRecess==='boolean'?input.gardenRecess:true,
    alcoveWidth,passageDepth:bound(input.passageDepth,1000,1000,1200),
    doorOffset:bound(input.doorOffset,200,100,bedroomDoorOffsetMax({expansion:base.expansion,alcoveWidth})),
  };
}

/** Independent E study. The approved A–D model and its route are not changed. */
export function createExperiment(input: Partial<ExperimentSettings> = DEFAULT_EXPERIMENT) {
  const settings=normalizeExperiment(input);
  const base=createConcept({...DEFAULT_CONCEPT,...settings,layout:'private'});
  const right=base.suiteRight,stepY=5744+settings.passageDepth;
  const alcoveRight=11143+settings.alcoveWidth,returnRight=alcoveRight+140;
  const bedroomBottom=7741,doorStart=right-settings.doorOffset-800;
  const privateAlcove=rect(11143,stepY+140,alcoveRight,bedroomBottom);
  const foyerRects=[rect(base.bathLeft,5744,right,stepY),rect(returnRight,stepY,right,7601)];
  const bayRight=base.bathLeft-140;
  const garageBay=rect(10842,3504,bayRight,stepY);
  const garageAddition=rect(10842,5604,bayRight,stepY);
  const garageShelves=[rect(bayRight-500,5604-settings.garageBayWidth,bayRight,5604)];
  const rooms=base.rooms.map(r=>({...r,rectsMm:[...r.rectsMm]}));
  Object.assign(rooms.find(r=>r.number==='1.10')!,{name:'Spálňa + súkromný šatník',rectsMm:[rect(11143,bedroomBottom,right,10699),privateAlcove]});
  Object.assign(rooms.find(r=>r.number==='1.14')!,{name:'Vstup v tvare L',rectsMm:foyerRects});
  Object.assign(rooms.find(r=>r.number==='1.12')!,{rectsMm:[base.rooms.find(r=>r.number==='1.12')!.rectsMm[0],garageBay]});
  const replacedGarageWalls=new Set(['C-GARAGE-BAY-EAST','C-GARAGE-BAY-RETURN','C-GARAGE-SPINE-S','C-GARAGE-SPINE-N']);
  const walls=base.walls.filter(w=>!w.id.startsWith('D-BED-PRIVACY')&&!replacedGarageWalls.has(w.id));
  const add=(id:string,x0:number,y0:number,x1:number,y1:number)=>walls.push({id,role:'PARTITION',rectMm:rect(x0,y0,x1,y1),changed:true});
  add('E-GARAGE-SEPARATOR-S',bayRight,3504,base.bathLeft,5844);
  add('E-GARAGE-SEPARATOR-N',bayRight,settings.garageConnected?6644:5844,base.bathLeft,stepY);
  add('E-GARAGE-MAIN-RETURN',10842,stepY,11143,10699);
  add('E-ALCOVE-FRONT',11143,stepY,returnRight,stepY+140);
  add('E-ALCOVE-RETURN',alcoveRight,stepY+140,returnRight,bedroomBottom);
  add('E-BED-WALL-W',returnRight,7601,doorStart,bedroomBottom);
  add('E-BED-WALL-E',doorStart+800,7601,right,bedroomBottom);
  const doors=base.doors.filter(d=>!['D-PRIVATE-BED','C-GARAGE-CLOSET'].includes(d.id)).map(d=>({...d,
    label:d.id==='D-HALL-DRESSING'?'Dom → vstup v tvare L · 800 mm':d.id==='D-DRESSING-BATH'?'Vstup → kúpeľňa · 800 mm':d.label,
  }));
  if(settings.garageConnected) doors.push({id:'E-GARAGE-ENTRY',label:'Vstup → zväčšená garáž · 800 mm',axis:'Y',wallSpanMm:[bayRight,base.bathLeft],startMm:5844,widthMm:800,heightMm:2100,leafWidthMm:800,swing:-1,hinge:-1,motion:'HINGED',fromRoomId:'ROOM-DRESSING',toRoomId:'ROOM-1-12'} satisfies InteriorDoor);
  doors.push({id:'E-PRIVATE-BED',label:'Vstup za zalomením → súkromná spálňa · 800 mm',axis:'X',wallSpanMm:[7601,7741],startMm:doorStart,widthMm:800,heightMm:2100,leafWidthMm:800,swing:1,hinge:1,motion:'HINGED',fromRoomId:'ROOM-DRESSING',toRoomId:'ROOM-1-10'} satisfies InteriorDoor);
  const storageRuns=[rect(11143,stepY+140,alcoveRight,stepY+740)];
  const cabinetFront=stepY+740;
  const sideClearance=Math.floor((10699-cabinetFront-settings.bedWidth)/2);
  const bed=rect(11143,cabinetFront+sideClearance,13343,cabinetFront+sideClearance+settings.bedWidth);
  const turnClearance=Math.hypot(Math.max(0,alcoveRight-bed.x1),bed.y0-bedroomBottom);
  const bedroomArea=area(rooms.find(r=>r.number==='1.10')!.rectsMm);
  return {...base,settings,rooms,walls,doors,garageBay,garageAddition,garageShelves,
    garageArea:area(rooms.find(r=>r.number==='1.12')!.rectsMm),garageGain:area([garageAddition]),
    foyerReduction:(base.bathLeft-11143)*settings.passageDepth/1e6,privateAlcove,foyerRects,storageRuns,bed,sideClearance,turnClearance,
    dressing:privateAlcove,wardrobeRect:storageRuns[0],dressingAisle:sideClearance,
    bedroomArea,foyerArea:area(foyerRects),storageLength:settings.alcoveWidth,storageArea:area(storageRuns),
    bedroomFreeArea:bedroomArea-area(storageRuns),frontAisle:settings.passageDepth,
    entranceWidth:right-returnRight,stepY,alcoveRight,returnRight,doorStart,
    cabinetFront,bedroomDepth:10699-cabinetFront,footClearance:right-13343,
    passageSaving:area([base.dressing!])-area(foyerRects),
  };
}
