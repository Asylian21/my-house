/** Client revision: preschool rooms, garden for a boy / street for a girl. */
export const CHILDREN_DESIGN_ID = 'C-KIDS-FULL-BEDS-2026-09-07';
export const CHILDREN_WINDOWS: Record<string,{startXmm:number;widthMm:number;heightMm:number;sillMm:number;kind?:'fixed'|'window';frameWidthMm?:number}> = {
  // Refined client brief: a narrow vertical fixed strip retains 217 mm to the
  // bed. The larger square window follows after a 200 mm pier; its right jamb
  // stops before the desk (x=19241). Its single sash hinges at the strip side.
  // Both heads follow the 2400 mm garden portal datum, with 45 mm profiles.
  'GARDEN-03':{startXmm:17000,widthMm:800,heightMm:2400,sillMm:0,kind:'fixed',frameWidthMm:45},
  'GARDEN-BOY-DESK':{startXmm:18000,widthMm:1200,heightMm:1200,sillMm:1200,kind:'window',frameWidthMm:45},
  // One ordinary double window at the desk replaces all three street windows.
  // Its east jamb leaves 200 mm of masonry before the room's bearing wall.
  'FRONT-05':{startXmm:18741,widthMm:1600,heightMm:1350,sillMm:900,kind:'window'},
};
export const GIRL_WINDOW_DESIGN:Record<string,{name:string;note:string}> = {
  'FRONT-05':{name:'Dvojkrídlové okno pri pracovnom stole',note:'Jediné okno dievčenskej izby: 1 600 × 1 350 mm, parapet 900 mm. Dve otváravé krídla pri stole; stredové presklenie aj okno pri posteli sú odstránené. Nástenka zostáva na bočnej stene.'},
};
export function withChildrenWindow<T extends {id:string}>(opening:T) { return {...opening,...CHILDREN_WINDOWS[opening.id]}; }
