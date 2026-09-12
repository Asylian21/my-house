import { GARAGE_DEPTH_REVISION, HOUSE as baseline, SITE_SURFACES, type Point2Mm } from './twin-site';
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

// Fan the existing approach toward the relocated door. The boundary gate and
// lowered street kerb stay aligned with each other; only the house end moves.
const originalSideDoor=baseline.facades.east.openings.find(o=>o.id==='EAST-03')!;
const sideDoorShiftMm=SERVICE_CORE_REVISION.exteriorDoor.startYmm+SERVICE_CORE_REVISION.exteriorDoor.widthMm/2
  -originalSideDoor.startYmm-originalSideDoor.widthMm/2;
const alignHouseEdge=(points:readonly Point2Mm[])=>points.map(p=>Math.abs(p.x-HOUSE.facades.east.faceXmm)<=2?{...p,y:p.y+sideDoorShiftMm}:p);
const polygonAreaM2=(points:readonly Point2Mm[])=>Math.abs(points.reduce((sum,p,i)=>{
  const q=points[(i+1)%points.length];return sum+p.x*q.y-q.x*p.y;
},0))/2_000_000;
const sidePolygon=alignHouseEdge(SITE_SURFACES.sideEntryApproach.polygonMm);
const sidePrivatePolygon=alignHouseEdge(SITE_SURFACES.sideEntryApproach.privatePolygonMm);
export const SIDE_ENTRY_APPROACH={...SITE_SURFACES.sideEntryApproach,
  sourceId:SERVICE_CORE_REVISION.id,placementStatus:'CURRENT_DOOR_WITH_RETAINED_BOUNDARY_GATE',
  polygonMm:sidePolygon,privatePolygonMm:sidePrivatePolygon,areaM2:polygonAreaM2(sidePolygon),
  streetConnection:{...SITE_SURFACES.sideEntryApproach.streetConnection,privateAreaM2:polygonAreaM2(sidePrivatePolygon)},
};
