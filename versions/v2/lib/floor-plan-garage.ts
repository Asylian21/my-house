import type { InteriorDoor, RectMm } from './twin-interior';
import { HOUSE, GARAGE_DEPTH_REVISION } from './twin-site';
import { GARAGE_VEHICLE } from './twin-garage';

const rect=(x0:number,y0:number,x1:number,y1:number):RectMm=>({x0,y0,x1,y1});

/** The same source-dimensioned garden loggia, gate and parking position in every 2D study. */
export function createGarageEnvelope(gardenRecess=true) {
  const porch=HOUSE.porches.gardenLoggia, pier=porch.cornerPier;
  const loggia={
    bounds:rect(pier.startXmm,porch.backFaceYmm,porch.eastInnerXmm,porch.faceYmm),
    pier:rect(pier.startXmm,pier.startYmm,pier.endXmm,pier.endYmm),
    westReturn:rect(pier.startXmm,porch.backFaceYmm,6944,HOUSE.facades.west.loggiaOpening.startYmm),
    depth:porch.faceYmm-porch.backFaceYmm,openingWidth:porch.openingEndXmm-porch.openingStartXmm,
    openingStart:porch.openingStartXmm,
  };
  const backFace=gardenRecess?porch.backFaceYmm:porch.faceYmm;
  const garageBackOpening=rect(porch.backDoor.startXmm,gardenRecess?GARAGE_DEPTH_REVISION.revisedGarageRearInnerFaceYmm:10699,porch.backDoor.startXmm+porch.backDoor.widthMm,backFace);
  // The 900 mm inward leaf occupies only part of the 1250 mm glazed opening.
  const gardenDoor:InteriorDoor & {leafPlaneMm:number}={id:'GARDEN-LOGGIA-DOOR',label:'Garáž → záhrada · 900 mm + bočné presklenie',axis:'X',wallSpanMm:[garageBackOpening.y0,backFace],leafPlaneMm:backFace-150,startMm:porch.backDoor.startXmm,widthMm:900,leafWidthMm:900,heightMm:porch.backDoor.heightMm,swing:-1,hinge:-1,motion:'HINGED',fromRoomId:'ROOM-1-12',toRoomId:'GARDEN'};
  // The retained recess needs the native 3D parking position within the gate reveal.
  const carCenter=gardenRecess?GARAGE_VEHICLE.route.parkedMm.y:6275;
  const car=rect(7600,carCenter-2425,9450,carCenter+2425);
  const gate=HOUSE.facades.front.garageDoor;
  const garageThreshold=rect(gate.startXmm,HOUSE.facades.front.faceYmm,gate.startXmm+gate.widthMm,3504);
  const shellPath=gardenRecess
    ? `M6440,-3000H28040V-20035H21040V-11200H${loggia.bounds.x1}V-${loggia.bounds.y0}H6440Z`
    : 'M6440,-3000H28040V-20035H21040V-11200H6440Z';
  return {gardenRecess,loggia,garageBackOpening,gardenDoor,car,garageThreshold,shellPath};
}
export type GarageEnvelope=ReturnType<typeof createGarageEnvelope>;
