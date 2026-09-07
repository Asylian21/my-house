/** Client revision: preschool rooms, garden for a boy / street for a girl. */
export const CHILDREN_DESIGN_ID = 'C-KIDS-FULL-BEDS-2026-09-07';
export const CHILDREN_WINDOWS: Record<string,{startXmm:number;widthMm:number;heightMm:number;sillMm:number}> = {
  'GARDEN-03':{startXmm:16900,widthMm:2200,heightMm:2400,sillMm:0},
  'FRONT-04':{startXmm:16900,widthMm:1050,heightMm:1600,sillMm:900},
  'FRONT-05':{startXmm:18200,widthMm:1050,heightMm:1600,sillMm:900},
};
export function withChildrenWindow<T extends {id:string}>(opening:T) { return {...opening,...CHILDREN_WINDOWS[opening.id]}; }
