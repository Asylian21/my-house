import { HOUSE as baseline } from './twin-site';
import { ACTIVE_CONCEPT } from './twin-interior';
import { withChildrenWindow } from './twin-children-design';
import { SERVICE_CORE_REVISION } from './technical-design';
/** Same exterior/roof; C suite openings and client-approved children's glazing. */
export const HOUSE={...baseline,facades:{...baseline.facades,front:{...baseline.facades.front,
  openings:[...baseline.facades.front.openings,{id:'FRONT-GIRL-BED',startXmm:15450,widthMm:1000,heightMm:1250,sillMm:1250}].map(opening=>({...withChildrenWindow(opening),
    startXmm:opening.id==='FRONT-02'?ACTIVE_CONCEPT.garageWindowStart:
      opening.id==='FRONT-03'?ACTIVE_CONCEPT.frontWindowStart:withChildrenWindow(opening).startXmm,
  })).sort((a,b)=>a.startXmm-b.startXmm),
},garden:{...baseline.facades.garden,openings:baseline.facades.garden.openings.map(withChildrenWindow)},
east:{...baseline.facades.east,openings:baseline.facades.east.openings.map(o=>o.id==='EAST-03'?{...o,...SERVICE_CORE_REVISION.exteriorDoor}:o)},
}};
