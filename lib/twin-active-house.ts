import { HOUSE as baseline } from './twin-site';
import { ACTIVE_CONCEPT } from './twin-interior';
import { withChildrenWindow } from './twin-children-design';
/** Same exterior/roof; C suite openings and client-approved children's glazing. */
export const HOUSE={...baseline,facades:{...baseline.facades,front:{...baseline.facades.front,
  openings:baseline.facades.front.openings.map(opening=>({...withChildrenWindow(opening),
    startXmm:opening.id==='FRONT-02'?ACTIVE_CONCEPT.garageWindowStart:
      opening.id==='FRONT-03'?ACTIVE_CONCEPT.frontWindowStart:withChildrenWindow(opening).startXmm,
  })),
},garden:{...baseline.facades.garden,openings:baseline.facades.garden.openings.map(withChildrenWindow)}}};
