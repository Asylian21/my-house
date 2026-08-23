import { SOURCES, type Point2Mm } from "./twin-site";

/**
 * Interior of 1.NP traced from the D1.1.002 wall vectors (1:100, 1.44 pt wall
 * outlines). Coordinates are the same local plan millimetres as `HOUSE`:
 * x grows from the garage end toward the wing, y from the street toward the
 * garden. Wall faces were converted from PDF points with the drawing scale
 * (0.02835 pt per millimetre) and rounded to the nearest millimetre; where the
 * rounded values differ from the labelled chain dimensions by a few
 * millimetres the vector value is kept so that adjoining faces stay coplanar.
 */

export type FloorFinish = "TILE" | "VINYL" | "EPOXY";
export type CeilingKind = "FLAT" | "VAULTED_TO_RIDGE";
export type InteriorWallRole = "LOAD_BEARING" | "PARTITION" | "PIER";

export interface RectMm {
  readonly x0: number;
  readonly y0: number;
  readonly x1: number;
  readonly y1: number;
}

export interface InteriorRoom {
  readonly id: string;
  readonly number: string;
  readonly name: string;
  /** Area from the D1.1.002 room legend, m². */
  readonly documentedAreaM2: number;
  /** Clear height (S.V.) from the room legend, mm. */
  readonly clearHeightMm: number;
  readonly ceiling: CeilingKind;
  readonly floor: FloorFinish;
  readonly wetRoom: boolean;
  readonly rectsMm: readonly RectMm[];
  /** Eye-level standing point for the walkthrough presets. */
  readonly standingPointMm: Point2Mm;
}

export interface InteriorWall {
  readonly id: string;
  readonly role: InteriorWallRole;
  readonly rectMm: RectMm;
}

export interface InteriorDoor {
  readonly id: string;
  readonly label: string;
  /** Axis of the wall the door sits in. */
  readonly axis: "X" | "Y";
  /** Wall face range along the perpendicular axis (the wall thickness). */
  readonly wallSpanMm: readonly [number, number];
  /** Clear opening start along the wall axis and its width. */
  readonly startMm: number;
  readonly widthMm: number;
  readonly heightMm: number;
  readonly leafWidthMm: number;
  /** Which side of the wall the leaf swings into: -1 toward lower coordinate. */
  readonly swing: -1 | 1;
  /** Hinge at the lower (-1) or upper (1) end of the opening along the wall. */
  readonly hinge: -1 | 1;
  readonly fromRoomId: string;
  readonly toRoomId: string;
}

export interface KitchenRun {
  readonly id: string;
  readonly designSourceId: string;
  readonly eastReturnSourceId: string;
  /** Back run against the 1.06/1.07 wall: sink and dishwasher (D1.1.002). */
  readonly rectMm: RectMm;
  readonly counterHeightMm: number;
  /** Dedicated integrated fridge-freezer at the west end of the back run. */
  readonly fridgeUnitRectMm: RectMm;
  readonly fridgeCabinetHeightMm: number;
  readonly sinkCenterXmm: number;
  readonly dishwasherXmm: readonly [number, number];
  /** Parallel peninsula with the hob, 1 000 mm in front of the back run. */
  readonly peninsulaRectMm: RectMm;
  /** Short return from the peninsula toward the technical-room wall. */
  readonly eastReturnRectMm: RectMm;
  readonly hobCenterXmm: number;
  /** Oven is centred directly below the peninsula hob. */
  readonly ovenCenterXmm: number;
  /** Client revision keeps the peninsula overhang visually and physically free. */
  readonly barStoolCount: 0;
  readonly upperCabinets: { readonly bottomMm: number; readonly topMm: number; readonly depthMm: number };
}

export interface TechnicalHeatingFitout {
  readonly id: string;
  readonly sourceId: string;
  readonly architecturalSourceId: string;
  readonly status: "CLIENT_DESIGN_CONCEPT";
  readonly roomId: "ROOM-1-07";
  readonly exteriorAccessOpeningId: "EAST-03";
  readonly boiler: {
    readonly footprintMm: RectMm;
    readonly heightMm: number;
    readonly front: "NORTH";
    readonly serviceRectMm: RectMm;
    readonly flueOutletDiameterMm: number;
  };
  readonly accumulator: {
    readonly centerMm: Point2Mm;
    readonly nominalVolumeL: 1000;
    readonly outerDiameterMm: number;
    readonly heightMm: number;
  };
}

export interface WcFitout {
  readonly id: string;
  readonly sourceId: string;
  readonly status: "CLIENT_DESIGN_CONCEPT";
  readonly roomId: "ROOM-1-06";
  readonly expansionMm: 300;
  readonly toilet: {
    readonly footprintMm: RectMm;
    readonly concealedCisternRectMm: RectMm;
    readonly facing: "WEST";
    readonly seatElevationMm: number;
  };
  readonly basin: {
    readonly footprintMm: RectMm;
    readonly facing: "SOUTH";
    readonly rimElevationMm: number;
  };
  readonly clearFloorRectMm: RectMm;
}

export interface BathroomFitout {
  readonly id: string;
  readonly sourceId: string;
  readonly architecturalSourceId: string;
  readonly status: "CLIENT_DESIGN_CONCEPT";
  readonly roomId: "ROOM-1-05";
  readonly shower: {
    readonly footprintMm: RectMm;
    readonly glassPanelMm: RectMm;
    readonly clearEntryWidthMm: number;
    readonly linearDrainMm: RectMm;
  };
  readonly vanity: {
    readonly footprintMm: RectMm;
    readonly facing: "EAST";
    readonly rimElevationMm: number;
  };
  readonly laundryTower: {
    readonly footprintMm: RectMm;
    readonly facing: "SOUTH";
    readonly heightMm: number;
    readonly applianceCount: 2;
  };
  readonly clearFloorRectMm: RectMm;
  readonly laundryServiceRectMm: RectMm;
}

export interface FireplacePier {
  readonly id: string;
  readonly rectMm: RectMm;
}

export type FurnitureFacing = "NORTH" | "SOUTH" | "EAST" | "WEST";

export interface LivingDiningFitout {
  readonly id: string;
  readonly sourceId: string;
  readonly status: "CLIENT_DESIGN_CONCEPT";
  readonly tvWall: {
    readonly rectMm: RectMm;
    readonly heightMm: number;
    readonly centralBayYmm: readonly [number, number];
    readonly tv: {
      readonly diagonalIn: number;
      readonly widthMm: number;
      readonly heightMm: number;
      readonly centerElevationMm: number;
    };
  };
  readonly sofa: {
    readonly mainRectMm: RectMm;
    readonly chaiseRectMm: RectMm;
    readonly seatHeightMm: number;
  };
  readonly dining: {
    readonly tableCenterMm: Point2Mm;
    readonly tableLengthMm: number;
    readonly tableDepthMm: number;
    readonly tableHeightMm: number;
    readonly chairs: readonly {
      readonly id: string;
      readonly centerMm: Point2Mm;
      readonly facing: FurnitureFacing;
    }[];
  };
}

export const INTERIOR_SOURCE_ID = SOURCES.floorPlan.id;
export const INTERIOR_WALL_HEIGHT_MM = 3125;
export const INTERIOR_DOOR_HEIGHT_MM = 2100;
export const WING_RIDGE_XMM = 24540;

export const INTERIOR_ROOMS: readonly InteriorRoom[] = [
  {
    id: "ROOM-1-01",
    number: "1.01",
    name: "Zádverie, chodba, vstup",
    documentedAreaM2: 4.15,
    clearHeightMm: 2600,
    ceiling: "FLAT",
    floor: "TILE",
    wetRoom: false,
    rectsMm: [{ x0: 21543, y0: 3504, x1: 23989, y1: 5201 }],
    standingPointMm: { x: 22700, y: 4400 },
  },
  {
    id: "ROOM-1-02",
    number: "1.02",
    name: "Chodba",
    documentedAreaM2: 17.2,
    clearHeightMm: 2600,
    ceiling: "FLAT",
    floor: "VINYL",
    wetRoom: false,
    rectsMm: [
      { x0: 13941, y0: 5561, x1: 15143, y1: 6462 },
      { x0: 15143, y0: 5561, x1: 16142, y1: 7601 },
      { x0: 16142, y0: 5561, x1: 16743, y1: 6420 },
      { x0: 16142, y0: 6560, x1: 21543, y1: 7601 },
      { x0: 21543, y0: 5341, x1: 22639, y1: 11550 },
      { x0: 20942, y0: 7902, x1: 21543, y1: 10699 },
    ],
    standingPointMm: { x: 22090, y: 7100 },
  },
  {
    id: "ROOM-1-03",
    number: "1.03",
    name: "Hlavný obytný priestor s kuchyňou",
    documentedAreaM2: 48.45,
    clearHeightMm: 2750,
    ceiling: "VAULTED_TO_RIDGE",
    floor: "VINYL",
    wetRoom: false,
    rectsMm: [
      { x0: 21543, y0: 11550, x1: 27541, y1: 19533 },
      { x0: 22783, y0: 10852, x1: 25691, y1: 11550 },
    ],
    standingPointMm: { x: 26300, y: 15200 },
  },
  {
    id: "ROOM-1-04",
    number: "1.04",
    name: "Pracovňa",
    documentedAreaM2: 11.1,
    clearHeightMm: 2600,
    ceiling: "FLAT",
    floor: "VINYL",
    wetRoom: false,
    rectsMm: [
      { x0: 24192, y0: 3504, x1: 27541, y1: 5400 },
      { x0: 22842, y0: 5400, x1: 27541, y1: 6412 },
    ],
    standingPointMm: { x: 25900, y: 4900 },
  },
  {
    id: "ROOM-1-05",
    number: "1.05",
    name: "Kúpeľňa a práčovňa",
    documentedAreaM2: 8.35,
    clearHeightMm: 2600,
    ceiling: "FLAT",
    floor: "TILE",
    wetRoom: true,
    rectsMm: [
      { x0: 22783, y0: 6602, x1: 25399, y1: 8972 },
      { x0: 25399, y0: 6602, x1: 27541, y1: 7601 },
    ],
    standingPointMm: { x: 23600, y: 7900 },
  },
  {
    id: "ROOM-1-06",
    number: "1.06",
    name: "WC",
    documentedAreaM2: 1.6,
    clearHeightMm: 2600,
    ceiling: "FLAT",
    floor: "TILE",
    wetRoom: true,
    rectsMm: [{ x0: 22783, y0: 9112, x1: 24082, y1: 10712 }],
    standingPointMm: { x: 23280, y: 9800 },
  },
  {
    id: "ROOM-1-07",
    number: "1.07",
    name: "Technická miestnosť",
    documentedAreaM2: 9.7,
    clearHeightMm: 2600,
    ceiling: "FLAT",
    floor: "EPOXY",
    wetRoom: true,
    rectsMm: [
      { x0: 24221, y0: 9112, x1: 25830, y1: 10712 },
      { x0: 25830, y0: 9112, x1: 27541, y1: 11411 },
      { x0: 25543, y0: 7741, x1: 27541, y1: 9112 },
    ],
    standingPointMm: { x: 25800, y: 9900 },
  },
  {
    id: "ROOM-1-08",
    number: "1.08",
    name: "Spálňa",
    documentedAreaM2: 12.3,
    clearHeightMm: 2600,
    ceiling: "FLAT",
    floor: "VINYL",
    wetRoom: false,
    rectsMm: [{ x0: 16942, y0: 3504, x1: 21242, y1: 6361 }],
    standingPointMm: { x: 19100, y: 6000 },
  },
  {
    id: "ROOM-1-09",
    number: "1.09",
    name: "Izba",
    documentedAreaM2: 16.3,
    clearHeightMm: 2600,
    ceiling: "FLAT",
    floor: "VINYL",
    wetRoom: false,
    rectsMm: [{ x0: 15143, y0: 7741, x1: 20641, y1: 10699 }],
    standingPointMm: { x: 17900, y: 9200 },
  },
  {
    id: "ROOM-1-10",
    number: "1.10",
    name: "Spálňa",
    documentedAreaM2: 15.45,
    clearHeightMm: 2600,
    ceiling: "FLAT",
    floor: "VINYL",
    wetRoom: false,
    rectsMm: [{ x0: 11143, y0: 6699, x1: 15003, y1: 10699 }],
    standingPointMm: { x: 13070, y: 8700 },
  },
  {
    id: "ROOM-1-11",
    number: "1.11",
    name: "Kúpeľňa",
    documentedAreaM2: 5.4,
    clearHeightMm: 2600,
    ceiling: "FLAT",
    floor: "TILE",
    wetRoom: true,
    rectsMm: [{ x0: 13941, y0: 3504, x1: 16743, y1: 5421 }],
    standingPointMm: { x: 15340, y: 4460 },
  },
  {
    id: "ROOM-1-12",
    number: "1.12",
    name: "Garáž",
    documentedAreaM2: 25.15,
    clearHeightMm: 2600,
    ceiling: "FLAT",
    floor: "EPOXY",
    wetRoom: false,
    rectsMm: [
      { x0: 6944, y0: 3504, x1: 13742, y1: 6462 },
      { x0: 6944, y0: 6462, x1: 10842, y1: 7749 },
    ],
    standingPointMm: { x: 10300, y: 5000 },
  },
] as const;

/**
 * Interior walls as plan rectangles between their two faces. Exterior walls,
 * the loggia back wall and the recessed porch wall are part of the facade
 * shell and are intentionally not repeated here.
 */
export const INTERIOR_WALLS: readonly InteriorWall[] = [
  // Garage east wall up to the corridor door.
  { id: "IW-GARAGE-EAST", role: "PARTITION", rectMm: { x0: 13742, y0: 3504, x1: 13941, y1: 5561 } },
  // 240 mm load-bearing wall garage / bedroom 1.10 and its 300 mm return.
  { id: "IW-GARAGE-NORTH", role: "LOAD_BEARING", rectMm: { x0: 10842, y0: 6462, x1: 15143, y1: 6699 } },
  { id: "IW-GARAGE-LOGGIA", role: "LOAD_BEARING", rectMm: { x0: 10842, y0: 6699, x1: 11143, y1: 8249 } },
  // Bathroom 1.11 top wall with the corridor door gap 14 990 – 15 790.
  { id: "IW-BATH-111-TOP-W", role: "PARTITION", rectMm: { x0: 13742, y0: 5421, x1: 14990, y1: 5561 } },
  { id: "IW-BATH-111-TOP-E", role: "PARTITION", rectMm: { x0: 15790, y0: 5421, x1: 16743, y1: 5561 } },
  // Wall 1.11 / 1.08 with the en-suite door gap 3 601 – 4 401.
  { id: "IW-BATH-111-EAST-S", role: "PARTITION", rectMm: { x0: 16743, y0: 3504, x1: 16942, y1: 3601 } },
  { id: "IW-BATH-111-EAST-N", role: "PARTITION", rectMm: { x0: 16743, y0: 4401, x1: 16942, y1: 6560 } },
  // Bedroom 1.08 top wall, door gap 17 141 – 18 042.
  { id: "IW-BED-108-TOP-W", role: "PARTITION", rectMm: { x0: 16142, y0: 6420, x1: 17141, y1: 6560 } },
  { id: "IW-BED-108-TOP-E", role: "LOAD_BEARING", rectMm: { x0: 18042, y0: 6361, x1: 21543, y1: 6560 } },
  // 300 mm wall bedroom 1.08 / entry 1.01.
  { id: "IW-BED-108-EAST", role: "LOAD_BEARING", rectMm: { x0: 21242, y0: 3504, x1: 21543, y1: 6361 } },
  // Room 1.09 south wall, door gap 15 841 – 16 743, plus the 300 mm closet column.
  { id: "IW-ROOM-109-SOUTH-W", role: "PARTITION", rectMm: { x0: 15003, y0: 7601, x1: 15841, y1: 7741 } },
  { id: "IW-ROOM-109-SOUTH-E", role: "PARTITION", rectMm: { x0: 16743, y0: 7601, x1: 21543, y1: 7741 } },
  { id: "IW-ROOM-109-EAST", role: "LOAD_BEARING", rectMm: { x0: 20641, y0: 7741, x1: 20942, y1: 10699 } },
  { id: "IW-CLOSET-SOUTH", role: "PARTITION", rectMm: { x0: 20942, y0: 7741, x1: 21543, y1: 7902 } },
  // Wall 1.10 / 1.09; the 900 mm door of 1.10 is the gap 6 699 – 7 601.
  { id: "IW-ROOM-110-EAST", role: "PARTITION", rectMm: { x0: 15003, y0: 7741, x1: 15143, y1: 10699 } },
  // Entry 1.01 top wall with the 900 mm corridor door 21 640 – 22 542.
  { id: "IW-ENTRY-TOP-W", role: "PARTITION", rectMm: { x0: 21543, y0: 5201, x1: 21640, y1: 5341 } },
  { id: "IW-ENTRY-TOP-E", role: "PARTITION", rectMm: { x0: 22542, y0: 5201, x1: 22639, y1: 5341 } },
  { id: "IW-ENTRY-TOP-E2", role: "PARTITION", rectMm: { x0: 22639, y0: 5201, x1: 22842, y1: 5451 } },
  { id: "IW-ENTRY-STUDY", role: "LOAD_BEARING", rectMm: { x0: 22842, y0: 5201, x1: 24192, y1: 5400 } },
  { id: "IW-ENTRY-EAST", role: "LOAD_BEARING", rectMm: { x0: 23989, y0: 3504, x1: 24192, y1: 5201 } },
  // Corridor spine east wall: study door 5 451 – 6 352, bathroom door
  // 6 653 – 7 453, WC door 9 866 – 10 666.
  { id: "IW-SPINE-EAST-1", role: "PARTITION", rectMm: { x0: 22639, y0: 6352, x1: 22783, y1: 6653 } },
  { id: "IW-SPINE-EAST-2", role: "PARTITION", rectMm: { x0: 22639, y0: 7453, x1: 22783, y1: 9866 } },
  { id: "IW-SPINE-EAST-3", role: "PARTITION", rectMm: { x0: 22639, y0: 10666, x1: 22783, y1: 11550 } },
  // 190 mm load-bearing wall study 1.04 / bathroom 1.05.
  { id: "IW-STUDY-NORTH", role: "LOAD_BEARING", rectMm: { x0: 22783, y0: 6412, x1: 27541, y1: 6602 } },
  // Bathroom 1.05 east wall and its return above the technical room.
  { id: "IW-BATH-105-EAST", role: "PARTITION", rectMm: { x0: 25399, y0: 7741, x1: 25543, y1: 9112 } },
  { id: "IW-BATH-105-SOUTH-E", role: "PARTITION", rectMm: { x0: 25399, y0: 7601, x1: 27541, y1: 7741 } },
  { id: "IW-BATH-105-NORTH", role: "PARTITION", rectMm: { x0: 22783, y0: 8972, x1: 25543, y1: 9112 } },
  // Client revision 23. 8. 2026 shifts the WC / technical-room partition
  // 300 mm east while retaining its original 139 mm construction thickness.
  { id: "IW-WC-EAST", role: "PARTITION", rectMm: { x0: 24082, y0: 9112, x1: 24221, y1: 10712 } },
  // Wall behind the kitchen run (top of WC and technical room).
  { id: "IW-KITCHEN-BACK", role: "PARTITION", rectMm: { x0: 22783, y0: 10712, x1: 25830, y1: 10852 } },
  { id: "IW-TECH-WEST", role: "PARTITION", rectMm: { x0: 25691, y0: 10712, x1: 25830, y1: 11411 } },
  { id: "IW-TECH-PIER", role: "PARTITION", rectMm: { x0: 25691, y0: 11411, x1: 25881, y1: 11550 } },
  // Technical room top wall with the 800 mm door 25 881 – 26 681.
  { id: "IW-TECH-NORTH", role: "PARTITION", rectMm: { x0: 26681, y0: 11411, x1: 27541, y1: 11550 } },
] as const;

/** 347 × 500 masonry pier on the west wall of 1.03 (D1.1.002 vector outline). */
export const FIREPLACE_PIER: FireplacePier = Object.freeze({
  id: "IW-WEST-PIER-103",
  rectMm: { x0: 21543, y0: 14551, x1: 21890, y1: 15051 },
});

/**
 * Kitchen traced from D1.1.002: a 2 900 back run (thick outline 22 791 –
 * 25 691 × 10 949 – 11 550, 600 deep) with the sink and dishwasher symbols,
 * and a 4 750 × 600 peninsula drawn 12 544 – 13 136 with the four-zone hob
 * at x ≈ 24 090. Fronts, worktop and appliances are a design finish.
 */
export const KITCHEN_RUN: KitchenRun = Object.freeze({
  id: "KITCHEN-RUN",
  designSourceId: SOURCES.clientKitchenRevision20260823.id,
  eastReturnSourceId: SOURCES.clientKitchenLRevision20260823.id,
  rectMm: { x0: 22791, y0: 10949, x1: 25691, y1: 11550 },
  counterHeightMm: 900,
  fridgeUnitRectMm: { x0: 22791, y0: 10949, x1: 23391, y1: 11550 },
  fridgeCabinetHeightMm: 2250,
  sinkCenterXmm: 24300,
  dishwasherXmm: [24700, 25300] as const,
  peninsulaRectMm: { x0: 22791, y0: 12544, x1: 27541, y1: 13144 },
  eastReturnRectMm: { x0: 26941, y0: 11550, x1: 27541, y1: 12544 },
  hobCenterXmm: 24090,
  ovenCenterXmm: 24090,
  barStoolCount: 0,
  upperCabinets: { bottomMm: 1450, topMm: 2250, depthMm: 350 },
});

/**
 * Client heating concept placed in the equipment zones already indicated in
 * D1.1.002: the circular accumulator in the west bay and the boiler in the
 * south recess. Product-specific fire, combustion-air, hydraulic and chimney
 * requirements remain a professional-design input rather than an as-built
 * assertion of this visualization.
 */
export const TECHNICAL_HEATING_FITOUT: TechnicalHeatingFitout = Object.freeze({
  id: "TECHNICAL-HEATING-FITOUT-2026-08-23",
  sourceId: SOURCES.clientTechnicalHeatingRevision20260823.id,
  architecturalSourceId: SOURCES.floorPlan.id,
  status: "CLIENT_DESIGN_CONCEPT",
  roomId: "ROOM-1-07",
  exteriorAccessOpeningId: "EAST-03",
  boiler: {
    footprintMm: { x0: 26142, y0: 7841, x1: 26942, y1: 8741 },
    heightMm: 1450,
    front: "NORTH",
    serviceRectMm: { x0: 26092, y0: 8741, x1: 26992, y1: 9641 },
    flueOutletDiameterMm: 180,
  },
  accumulator: {
    centerMm: { x: 25026, y: 9912 },
    nominalVolumeL: 1000,
    outerDiameterMm: 1000,
    heightMm: 2100,
  },
});

/** Compact sanitary fitout after moving the 1.06 / 1.07 partition by 300 mm. */
export const WC_FITOUT: WcFitout = Object.freeze({
  id: "WC-FITOUT-2026-08-23",
  sourceId: SOURCES.clientWcRevision20260823.id,
  status: "CLIENT_DESIGN_CONCEPT",
  roomId: "ROOM-1-06",
  expansionMm: 300,
  toilet: {
    footprintMm: { x0: 23562, y0: 9327, x1: 24082, y1: 9697 },
    concealedCisternRectMm: { x0: 23962, y0: 9252, x1: 24082, y1: 9772 },
    facing: "WEST",
    seatElevationMm: 450,
  },
  basin: {
    footprintMm: { x0: 23602, y0: 10392, x1: 24052, y1: 10712 },
    facing: "SOUTH",
    rimElevationMm: 850,
  },
  clearFloorRectMm: { x0: 22783, y0: 9697, x1: 23562, y1: 10392 },
});

/**
 * Compact client layout for the L-shaped room 1.05. The fixed architecture
 * stays unchanged: the 900 mm-deep east leg becomes one walk-in wet zone,
 * while a floating vanity and a vertical laundry tower release the centre.
 */
export const BATHROOM_FITOUT: BathroomFitout = Object.freeze({
  id: "BATHROOM-FITOUT-2026-08-23",
  sourceId: SOURCES.clientBathroomRevision20260823.id,
  architecturalSourceId: SOURCES.floorPlan.id,
  status: "CLIENT_DESIGN_CONCEPT",
  roomId: "ROOM-1-05",
  shower: {
    footprintMm: { x0: 26141, y0: 6652, x1: 27541, y1: 7552 },
    // A longitudinal panel protects the dry room while the complete 900 mm
    // west edge remains an open, threshold-free entrance.
    glassPanelMm: { x0: 26141, y0: 7537, x1: 27041, y1: 7552 },
    clearEntryWidthMm: 900,
    linearDrainMm: { x0: 27291, y0: 6762, x1: 27371, y1: 7442 },
  },
  vanity: {
    footprintMm: { x0: 22783, y0: 7822, x1: 23243, y1: 8822 },
    facing: "EAST",
    rimElevationMm: 860,
  },
  laundryTower: {
    footprintMm: { x0: 24749, y0: 8322, x1: 25399, y1: 8972 },
    facing: "SOUTH",
    heightMm: 2350,
    applianceCount: 2,
  },
  clearFloorRectMm: { x0: 23243, y0: 7453, x1: 24749, y1: 8322 },
  laundryServiceRectMm: { x0: 24749, y0: 7422, x1: 25399, y1: 8322 },
});

/**
 * Client interior concept from 23. 8. 2026. The composition deliberately uses
 * the uninterrupted west-wall bay after the fireplace pier and stops before
 * the fixed glazing at the rear gable. The sofa faces that wall from the east,
 * while the dining table occupies the clear band between the kitchen peninsula
 * and the sofa without narrowing the east-side circulation route.
 */
export const LIVING_DINING_FITOUT: LivingDiningFitout = Object.freeze({
  id: "LIVING-DINING-FITOUT-2026-08-23",
  sourceId: SOURCES.clientRevision20260823.id,
  status: "CLIENT_DESIGN_CONCEPT",
  tvWall: {
    rectMm: { x0: 21543, y0: 15380, x1: 21980, y1: 18750 },
    heightMm: 2600,
    centralBayYmm: [15900, 18200] as const,
    tv: {
      diagonalIn: 98,
      widthMm: 2170,
      heightMm: 1220,
      centerElevationMm: 1180,
    },
  },
  sofa: {
    mainRectMm: { x0: 26020, y0: 15850, x1: 27250, y1: 18750 },
    chaiseRectMm: { x0: 24500, y0: 17650, x1: 27250, y1: 18750 },
    seatHeightMm: 430,
  },
  dining: {
    tableCenterMm: { x: 24450, y: 14750 },
    tableLengthMm: 1400,
    tableDepthMm: 800,
    tableHeightMm: 760,
    chairs: [
      { id: "DINING-CHAIR-SW", centerMm: { x: 24050, y: 14000 }, facing: "NORTH" },
      { id: "DINING-CHAIR-SE", centerMm: { x: 24850, y: 14000 }, facing: "NORTH" },
      { id: "DINING-CHAIR-NW", centerMm: { x: 24050, y: 15500 }, facing: "SOUTH" },
      { id: "DINING-CHAIR-NE", centerMm: { x: 24850, y: 15500 }, facing: "SOUTH" },
    ],
  },
});

export const INTERIOR_DOORS: readonly InteriorDoor[] = [
  {
    id: "DOOR-101-102",
    label: "Dvere zádverie → chodba · 900/2100",
    axis: "X",
    wallSpanMm: [5201, 5341],
    startMm: 21640,
    widthMm: 902,
    heightMm: 2100,
    leafWidthMm: 800,
    swing: 1,
    hinge: -1,
    fromRoomId: "ROOM-1-01",
    toRoomId: "ROOM-1-02",
  },
  {
    id: "DOOR-102-104",
    label: "Dvere chodba → pracovňa · 800/2100",
    axis: "Y",
    wallSpanMm: [22639, 22842],
    startMm: 5451,
    widthMm: 901,
    heightMm: 2100,
    leafWidthMm: 800,
    swing: 1,
    hinge: -1,
    fromRoomId: "ROOM-1-02",
    toRoomId: "ROOM-1-04",
  },
  {
    id: "DOOR-102-105",
    label: "Dvere chodba → kúpeľňa 1.05 · 700/2100",
    axis: "Y",
    wallSpanMm: [22639, 22783],
    startMm: 6653,
    widthMm: 800,
    heightMm: 2100,
    leafWidthMm: 700,
    swing: 1,
    hinge: -1,
    fromRoomId: "ROOM-1-02",
    toRoomId: "ROOM-1-05",
  },
  {
    id: "DOOR-102-106",
    label: "Dvere chodba → WC · 700/2100",
    axis: "Y",
    wallSpanMm: [22639, 22783],
    startMm: 9866,
    widthMm: 800,
    heightMm: 2100,
    leafWidthMm: 700,
    swing: 1,
    hinge: 1,
    fromRoomId: "ROOM-1-02",
    toRoomId: "ROOM-1-06",
  },
  {
    id: "DOOR-103-107",
    label: "Dvere obytný priestor → technická miestnosť · 700/2100",
    axis: "X",
    wallSpanMm: [11411, 11550],
    startMm: 25881,
    widthMm: 800,
    heightMm: 2100,
    leafWidthMm: 700,
    swing: -1,
    hinge: -1,
    fromRoomId: "ROOM-1-03",
    toRoomId: "ROOM-1-07",
  },
  {
    id: "DOOR-102-108",
    label: "Dvere chodba → spálňa 1.08 · 800/2100",
    axis: "X",
    wallSpanMm: [6361, 6560],
    startMm: 17141,
    widthMm: 901,
    heightMm: 2100,
    leafWidthMm: 800,
    swing: -1,
    hinge: 1,
    fromRoomId: "ROOM-1-02",
    toRoomId: "ROOM-1-08",
  },
  {
    id: "DOOR-102-109",
    label: "Dvere chodba → izba 1.09 · 800/2100",
    axis: "X",
    wallSpanMm: [7601, 7741],
    startMm: 15841,
    widthMm: 902,
    heightMm: 2100,
    leafWidthMm: 800,
    swing: 1,
    hinge: 1,
    fromRoomId: "ROOM-1-02",
    toRoomId: "ROOM-1-09",
  },
  {
    id: "DOOR-102-110",
    label: "Dvere chodba → spálňa 1.10 · 800/2100",
    axis: "Y",
    wallSpanMm: [15003, 15143],
    startMm: 6699,
    widthMm: 902,
    heightMm: 2100,
    leafWidthMm: 800,
    swing: -1,
    hinge: 1,
    fromRoomId: "ROOM-1-02",
    toRoomId: "ROOM-1-10",
  },
  {
    id: "DOOR-102-111",
    label: "Dvere chodba → kúpeľňa 1.11 · 700/2100",
    axis: "X",
    wallSpanMm: [5421, 5561],
    startMm: 14990,
    widthMm: 800,
    heightMm: 2100,
    leafWidthMm: 700,
    swing: -1,
    hinge: -1,
    fromRoomId: "ROOM-1-02",
    toRoomId: "ROOM-1-11",
  },
  {
    id: "DOOR-108-111",
    label: "Dvere spálňa 1.08 → kúpeľňa 1.11 · 700/2100",
    axis: "Y",
    wallSpanMm: [16743, 16942],
    startMm: 3601,
    widthMm: 800,
    heightMm: 2100,
    leafWidthMm: 700,
    swing: -1,
    hinge: 1,
    fromRoomId: "ROOM-1-08",
    toRoomId: "ROOM-1-11",
  },
  {
    id: "DOOR-102-112",
    label: "Dvere chodba → garáž · 800/2100",
    axis: "Y",
    wallSpanMm: [13742, 13941],
    startMm: 5561,
    widthMm: 901,
    heightMm: 2100,
    leafWidthMm: 800,
    swing: -1,
    hinge: -1,
    fromRoomId: "ROOM-1-02",
    toRoomId: "ROOM-1-12",
  },
] as const;

export function rectAreaMm2(rect: RectMm): number {
  return (rect.x1 - rect.x0) * (rect.y1 - rect.y0);
}

export function roomAreaM2(room: InteriorRoom): number {
  return room.rectsMm.reduce((sum, rect) => sum + rectAreaMm2(rect), 0) / 1_000_000;
}

export function roomBoundsMm(room: InteriorRoom): RectMm {
  return room.rectsMm.reduce(
    (bounds, rect) => ({
      x0: Math.min(bounds.x0, rect.x0),
      y0: Math.min(bounds.y0, rect.y0),
      x1: Math.max(bounds.x1, rect.x1),
      y1: Math.max(bounds.y1, rect.y1),
    }),
    {
      x0: Number.POSITIVE_INFINITY,
      y0: Number.POSITIVE_INFINITY,
      x1: Number.NEGATIVE_INFINITY,
      y1: Number.NEGATIVE_INFINITY,
    },
  );
}

/** Ceiling elevation of a room at a plan position, mm above ±0,000. */
export function ceilingElevationMm(room: InteriorRoom, xMm: number): number {
  if (room.ceiling === "FLAT") return room.clearHeightMm;
  const bounds = roomBoundsMm(room);
  const halfSpan = Math.max(1, WING_RIDGE_XMM - bounds.x0);
  const distance = Math.abs(xMm - WING_RIDGE_XMM);
  const ridgeClearanceMm = 4850;
  return Math.round(
    ridgeClearanceMm -
      (ridgeClearanceMm - room.clearHeightMm) * Math.min(1, distance / halfSpan),
  );
}

/** True when the point is inside any room rectangle. */
export function roomAt(point: Point2Mm): InteriorRoom | null {
  for (const room of INTERIOR_ROOMS) {
    for (const rect of room.rectsMm) {
      if (
        point.x >= rect.x0 &&
        point.x <= rect.x1 &&
        point.y >= rect.y0 &&
        point.y <= rect.y1
      ) {
        return room;
      }
    }
  }
  return null;
}

export function totalDocumentedFloorAreaM2(): number {
  return INTERIOR_ROOMS.reduce((sum, room) => sum + room.documentedAreaM2, 0);
}
