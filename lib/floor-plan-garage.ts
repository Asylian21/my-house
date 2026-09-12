import type { InteriorDoor, RectMm } from './twin-interior';
import { HOUSE, GARAGE_DEPTH_REVISION } from './twin-site';
import { GARAGE_VEHICLE } from './twin-garage';

const rect=(x0:number,y0:number,x1:number,y1:number):RectMm=>({x0,y0,x1,y1});
/** West face of the garage spine wall (B/C concepts): the masonry of the loggia's east cheek. */
const SPINE_WEST_XMM=10842;

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
  return {gardenRecess,loggia,garageBackOpening,gardenDoor,car,garageThreshold,shellPath,insulation:insulationBands(gardenRecess,loggia)};
}
export type GarageEnvelope=ReturnType<typeof createGarageEnvelope>;

/**
 * Outer 200 mm of every insulated exterior wall (client, 11. 9. 2026: 300 mm
 * masonry + 200 mm contact insulation = 500). Drawn over the solid shell, so
 * the shell reads as masonry and these bands as insulation. The insulation
 * wraps outer corners; the loggia corner pier and rear return are solid.
 */
function insulationBands(gardenRecess:boolean,loggia:{bounds:RectMm}):RectMm[] {
  const t=HOUSE.exteriorWall.insulationMm;
  const west=HOUSE.facades.west.faceXmm, east=HOUSE.facades.east.faceXmm, front=HOUSE.facades.front.faceYmm, garden=HOUSE.facades.garden.faceYmm, wingWest=HOUSE.facades.wingWest.faceXmm;
  const wingEnd=20035;
  const bands=[
    rect(west,front,east,front+t),
    rect(east-t,front,east,wingEnd),
    rect(wingWest,wingEnd-t,east,wingEnd),
    rect(wingWest,garden,wingWest+t,wingEnd),
    // With the recess the garden facade starts east of the loggia opening; the corner pier stays solid.
    rect(gardenRecess?loggia.bounds.x1:west,garden-t,wingWest,garden),
    rect(west,front,west+t,gardenRecess?loggia.bounds.y0:garden),
  ];
  if(gardenRecess){
    // Garage back wall towards the loggia and the room 1.10 cheek, flush with the spine wall.
    bands.push(rect(6944,loggia.bounds.y0-t,loggia.bounds.x1,loggia.bounds.y0),rect(loggia.bounds.x1,loggia.bounds.y0,SPINE_WEST_XMM,garden));
  }
  return bands;
}
