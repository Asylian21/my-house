/** Client revision: preschool rooms, garden for a boy / street for a girl. */
export const CHILDREN_DESIGN_ID = 'C-KIDS-FULL-BEDS-2026-09-07';
export const CHILDREN_WINDOWS: Record<string,{startXmm:number;widthMm:number;heightMm:number;sillMm:number;kind?:'fixed'|'window';frameWidthMm?:number}> = {
  // Both child rooms now start at 15243; the garden glazing follows the boy's
  // bed 100 mm east so 217 mm stays between the bed frame and the glass.
  'GARDEN-03':{startXmm:17000,widthMm:2200,heightMm:2400,sillMm:0},
  // The girl's room is 5 298 mm long between two 300 mm bearing walls (faces
  // 15243 and 20541). The three windows keep their sizes; 600 mm piers remain
  // between them and 224 mm piers stay beside both bearing walls.
  'FRONT-GIRL-BED':{startXmm:15467,widthMm:1000,heightMm:1250,sillMm:1250},
  'FRONT-04':{startXmm:17067,widthMm:1600,heightMm:1950,sillMm:550,kind:'fixed',frameWidthMm:45},
  'FRONT-05':{startXmm:19267,widthMm:1050,heightMm:1600,sillMm:900},
};
export const GIRL_WINDOW_DESIGN:Record<string,{name:string;note:string}> = {
  'FRONT-GIRL-BED':{name:'Okno nad posteľou',note:'Parapet 1 250 mm ponecháva 200 mm nad čelom postele. Vyššie okno osvetľuje pokojovú časť a zachováva súkromie pri ulici.'},
  'FRONT-04':{name:'Panoramatické okno pri hre',note:'Pevné presklenie so zníženým parapetom 550 mm otvára výhľad aj zo sedu a z detskej výšky. Pred oknom ostáva voľná plocha. Navrhnúť bezpečnostné zasklenie a vonkajšie tienenie.'},
  'FRONT-05':{name:'Okno nad pracovným stolom',note:'Denné svetlo priamo pri stole. Parapet 900 mm je 360 mm nad dnešnou doskou; nástenka je na bočnej stene a okno nezakrýva.'},
};
export function withChildrenWindow<T extends {id:string}>(opening:T) { return {...opening,...CHILDREN_WINDOWS[opening.id]}; }
