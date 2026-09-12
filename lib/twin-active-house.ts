import { GARAGE_DEPTH_REVISION, HOUSE as baseline } from './twin-site';
import { ACTIVE_CONCEPT, ACTIVE_LAYOUT_ID, totalActiveFloorAreaM2 } from './twin-interior';
import { CHILDREN_WINDOWS, withChildrenWindow } from './twin-children-design';
import { SERVICE_CORE_REVISION } from './technical-design';
/** Same exterior/roof; C suite openings and client-approved children's glazing. */
export const HOUSE={...baseline,
  // Current room geometry, including garage; never change the preserved D1 legend.
  floorAreaM2: totalActiveFloorAreaM2(),
  floorAreaAuthority: {
    kind: 'ACTIVE_ROOM_RECTANGLE_SUM',
    layoutId: ACTIVE_LAYOUT_ID,
    source: 'lib/twin-interior.ts:INTERIOR_ROOMS',
    includesGarage: true,
  } as const,
  historicalFloorArea: {
    areaM2: baseline.floorAreaM2,
    originalD1LegendAreaM2: baseline.originalFloorAreaM2,
    kind: 'D1_ROOM_LEGEND_PLUS_CLIENT_GARAGE_REVISION',
    sourceId: GARAGE_DEPTH_REVISION.sourceId,
  } as const,
  facades:{...baseline.facades,front:{...baseline.facades.front,
  openings:[...baseline.facades.front.openings,{id:'FRONT-GIRL-BED',...CHILDREN_WINDOWS['FRONT-GIRL-BED']}].map(opening=>({...withChildrenWindow(opening),
    startXmm:opening.id==='FRONT-02'?ACTIVE_CONCEPT.garageWindowStart:
      opening.id==='FRONT-03'?ACTIVE_CONCEPT.frontWindowStart:withChildrenWindow(opening).startXmm,
  })).sort((a,b)=>a.startXmm-b.startXmm),
},garden:{...baseline.facades.garden,openings:baseline.facades.garden.openings.map(withChildrenWindow)},
east:{...baseline.facades.east,openings:baseline.facades.east.openings.map(o=>o.id==='EAST-03'?{...o,...SERVICE_CORE_REVISION.exteriorDoor}:o)},
}};
