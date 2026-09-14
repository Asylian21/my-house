import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { ExportSheet } from '../../app/koncept-2d/export-sheet';
import { HOUSE } from '../../lib/twin-active-house';
import { ACTIVE_DESIGN } from '../../lib/twin-design-selection';
import { SITE_SURFACES, SITE_AXIS, ACTIVE_HOUSE_PLACEMENT, ACTIVE_LOCAL_ORIGIN_SJTSK_MM } from '../../lib/twin-active-site';
import { INTERIOR_ROOMS, INTERIOR_DOORS, INTERIOR_WALLS, BATHROOM_FITOUT, ceilingElevationMm, WING_RIDGE_XMM } from '../../lib/twin-interior';
import { ACOUSTIC_ASSEMBLIES, ACOUSTIC_WALL_SPECS } from '../../lib/acoustic-walls';
import { CODED_OPENINGS, FACADES, GRID_X, GRID_Y, FOOTPRINT, SITE_BOUNDARY, SHELL_WALL_MESHES, INTERIOR_WALL_MESHES, MATERIAL_LEGEND, PLAN_EXTENT, TERRACES } from '../../lib/plan-export';
import { ACTIVE_JOINED_ROOF_PARAMETERS, deriveJoinedRoofGeometry, roofHeightMm } from '../../lib/twin-roof';
import { HEATING_LAYOUTS } from '../../lib/technical-design';
import { LIVING_LAYOUTS } from '../../lib/twin-living-layouts';
import h200Junction from '../../lib/h200-junction.json';
import { DECK_BOARD_LAYOUT } from '../../lib/deck-boards';
import { EXTERIOR_RENDER_STABILITY } from '../../lib/twin-viewport-contract';
import generated from '../../lib/plan-geometry.generated.json';
import { derivePorchEnvelope } from './porch-envelope';
import { CLIENT_BRIEF, elevationBasis, floorFromFoundation } from './client-brief';

/** Direct snapshot: never copy a second set of architectural dimensions. */
export function drawingSource() {
  const rooms = INTERIOR_ROOMS.map(r => ({...r, ceilingPoints: [...new Set(r.rectsMm.flatMap(v => [v.x0,WING_RIDGE_XMM,v.x1]))].sort((a,b)=>a-b).map(x=>({x,z:ceilingElevationMm(r,x)}))}));
  const living=INTERIOR_ROOMS.find(r=>r.number==='1.03')!;
  const westXmm=Math.min(...living.rectsMm.map(r=>r.x0));
  const vaultAt=(x:number)=>4850-(4850-living.clearHeightMm)*Math.min(1,Math.abs(x-WING_RIDGE_XMM)/(WING_RIDGE_XMM-westXmm));
  const porch=HOUSE.porches.wingEnd,g=porch.gableWindow;
  // Same profile equations as buildPorchCurtainWall; 30 mm is its frame clearance.
  const triangle={code:'O11',source:'lib/babylon-scene.ts:buildPorchCurtainWall',vertices:[[g.startXmm,g.bottomMm],[g.endXmm,g.bottomMm],[g.apexXmm,vaultAt(g.apexXmm)-30]],closure:[[westXmm,porch.ringBeam.topMm],[porch.backWall.endXmm+1,porch.ringBeam.topMm],[WING_RIDGE_XMM,vaultAt(WING_RIDGE_XMM)],[g.endXmm,vaultAt(g.endXmm)],[g.endXmm,g.bottomMm],[g.startXmm,g.bottomMm],[g.startXmm,vaultAt(g.startXmm)]]};
  const rp=ACTIVE_JOINED_ROOF_PARAMETERS,clearance=porch.ceilingClearanceMm;
  const roofAtX=(x:number)=>roofHeightMm(x<WING_RIDGE_XMM?'WING_INNER':'WING_OUTER',x,porch.gablePlaneYmm)-clearance;
  const crossing=clearance*HOUSE.roof.wingHalfSpanMm/(HOUSE.ridgeElevationMm-HOUSE.eavesElevationMm);
  const porchExteriorProfiles=[
    [[rp.wingInnerEaveXmm+crossing,HOUSE.eavesElevationMm],[g.startXmm,roofAtX(g.startXmm)],[g.startXmm,porch.ringBeam.topMm],[westXmm,porch.ringBeam.topMm],[westXmm,HOUSE.eavesElevationMm]],
    [[g.startXmm,g.bottomMm],[g.endXmm,triangle.vertices[2][1]],[g.endXmm,roofAtX(g.endXmm)],[g.startXmm,roofAtX(g.startXmm)]],
    [[g.endXmm,porch.ringBeam.topMm],[Math.max(...living.rectsMm.map(r=>r.x1)),porch.ringBeam.topMm],[Math.max(...living.rectsMm.map(r=>r.x1)),HOUSE.eavesElevationMm],[rp.maxXmm-crossing,HOUSE.eavesElevationMm],[WING_RIDGE_XMM,HOUSE.ridgeElevationMm-clearance],[g.endXmm,roofAtX(g.endXmm)]],
  ];
  // buildGables uses a vertical surface, not a specified structural wall assembly.
  const garageGable={source:'lib/babylon-scene.ts:buildGables',planeMm:HOUSE.originMm.x-8,vertices:[[HOUSE.originMm.y,HOUSE.eavesElevationMm],[HOUSE.originMm.y+HOUSE.lowerBar.depthMm/2,HOUSE.ridgeElevationMm],[HOUSE.originMm.y+HOUSE.lowerBar.depthMm,HOUSE.eavesElevationMm]]};
  const h200Joints=Object.fromEntries(['J1','J2'].map(code=>{
    const row=h200Junction.geometry.find(([label])=>label.startsWith(code));
    const values=row?.[1].match(/X ([\d ]+)–([\d ]+); Y ([\d ]+)–([\d ]+) mm/);
    if(!values)throw new Error(`Missing source geometry for ${code}`);
    const [x0,x1,y0,y1]=values.slice(1).map(v=>Number(v.replaceAll(' ','')));
    return [code,{x0,x1,y0,y1}];
  }));
  const entry=SITE_SURFACES.entry;
  const entryOpening=CODED_OPENINGS.find(o=>o.item.id.endsWith(` ${entry.accessOpeningId}`));
  if(!entryOpening?.facade)throw new Error('Main entry opening is missing from the canonical plan');
  const entryProposal={status:CLIENT_BRIEF.entrance.designStatus,doorCode:entryOpening.code,sourceId:entry.id,
    landingRectMm:{x0:Math.min(...entry.polygonMm.map(p=>p.x)),x1:Math.max(...entry.polygonMm.map(p=>p.x)),
      y0:entryOpening.facade.outer-CLIENT_BRIEF.entrance.proposedLandingDepthMm,y1:entryOpening.facade.outer},
    stepHeightMm:CLIENT_BRIEF.entrance.proposedRiserMm,minimumStepCount:CLIENT_BRIEF.entrance.minimumStepCount,
    absoluteElevations:CLIENT_BRIEF.entrance.absoluteElevations};
  return {design:ACTIVE_DESIGN,house:HOUSE,rooms,doors:INTERIOR_DOORS,walls:INTERIOR_WALLS,triangle,garageGable,
    clientBrief:CLIENT_BRIEF,entryProposal,showerFootprint:BATHROOM_FITOUT.shower.footprintMm,
    foundationFloorLevelMm:floorFromFoundation(CLIENT_BRIEF.foundations.reportedExistingLowerStrip.topAboveRoadMm,CLIENT_BRIEF.foundations.slab.topAboveUpperStripMm,CLIENT_BRIEF.services.floorAssemblyThicknessMm),
    elevations:{floor:elevationBasis(0),roofEdge:elevationBasis(HOUSE.eavesElevationMm),ridgePlane:elevationBasis(HOUSE.ridgeElevationMm)},
    h200Joints,exteriorSteps:generated.meshes.filter(m=>/betónový stupeň/.test(m.name)),porchEnvelope:derivePorchEnvelope(),
    porchExteriorProfiles,upperMeshes:generated.meshes.filter(m=>/štít podhľadu|štít nad vencom|pás venca/.test(m.name)),
    facades:FACADES,openings:CODED_OPENINGS,gridX:GRID_X,gridY:GRID_Y,footprint:FOOTPRINT,siteBoundary:SITE_BOUNDARY,
    siteAxis:SITE_AXIS,placement:ACTIVE_HOUSE_PLACEMENT,originSjtsk:ACTIVE_LOCAL_ORIGIN_SJTSK_MM,surfaces:SITE_SURFACES,
    shellMeshes:SHELL_WALL_MESHES,interiorMeshes:INTERIOR_WALL_MESHES,materials:MATERIAL_LEGEND,planExtent:PLAN_EXTENT,
    terraces:TERRACES,acousticAssemblies:ACOUSTIC_ASSEMBLIES,acousticWalls:ACOUSTIC_WALL_SPECS,h200Junction,
    roof:deriveJoinedRoofGeometry(),roofParameters:ACTIVE_JOINED_ROOF_PARAMETERS,
    heating:HEATING_LAYOUTS.B,living:LIVING_LAYOUTS.B,deck:DECK_BOARD_LAYOUT,renderTerrain:EXTERIOR_RENDER_STABILITY,
    livingFlueRoofMm:roofHeightMm('WING_INNER',LIVING_LAYOUTS.B.stove.centerMm.x,LIVING_LAYOUTS.B.stove.centerMm.y),
  };
}

export function originalPlanSvg(color:boolean) {
  return renderToStaticMarkup(createElement(ExportSheet,{level:3,color,livingLayout:'B',heatingLayout:'B'}));
}
