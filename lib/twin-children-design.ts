/** Client revision: matching centred windows in both children's rooms. */
export const CHILDREN_DESIGN_ID = 'C-KIDS-MATCHING-WINDOWS-2026-09-13';
/** The 17 892 mm axis matches both 900 mm room doors and the room centre. */
export const CHILDREN_DOUBLE_WINDOW = {
  startXmm:16992,widthMm:1800,heightMm:1500,sillMm:900,kind:'window' as const,frameWidthMm:45,
};
export const CHILDREN_WINDOWS: Record<string,{startXmm:number;widthMm:number;heightMm:number;sillMm:number;kind?:'fixed'|'window';frameWidthMm?:number}> = {
  'GARDEN-03':{...CHILDREN_DOUBLE_WINDOW},
  'FRONT-05':{...CHILDREN_DOUBLE_WINDOW},
};
export const CHILDREN_WINDOW_DESIGN:Record<string,{name:string;note:string;roomId:string}> = {
  'FRONT-05':{name:'Dvojkrídlové okno oproti dverám',roomId:'ROOM-1-08',note:'Jediné okno dievčenskej izby: 1 800 × 1 500 mm, parapet 900 mm. Dve rovnaké otváravé krídla, antracitové profily 45 mm. Os 17 892 mm je presne oproti dverám a v strede izby. Rovnaké okno je v chlapčenskej izbe.'},
  'GARDEN-03':{name:'Dvojkrídlové okno oproti dverám',roomId:'ROOM-1-09',note:'Jediné okno chlapčenskej izby: 1 800 × 1 500 mm, parapet 900 mm. Dve rovnaké otváravé krídla, antracitové profily 45 mm. Os 17 892 mm je presne oproti dverám a v strede izby. Nahrádza pevný pás aj samostatné okno pri stole; rovnaké okno je v dievčenskej izbe.'},
};
export function withChildrenWindow<T extends {id:string}>(opening:T) { return {...opening,...CHILDREN_WINDOWS[opening.id]}; }
