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
  /** Optional client revision when the handedness differs from the source plan. */
  readonly revisionSourceId?: string;
  readonly previousHinge?: -1 | 1;
  readonly fromRoomId: string;
  readonly toRoomId: string;
}

export interface KitchenRun {
  readonly id: string;
  readonly designSourceId: string;
  readonly eastReturnSourceId: string;
  readonly clearanceRevisionSourceId: string;
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
  /** Island extractor remains centred over the hob after the peninsula cut. */
  readonly extractorCenterXmm: number;
  readonly extractorWidthMm: number;
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
  readonly builtIn: {
    readonly footprintMm: RectMm;
    readonly facing: "SOUTH";
    readonly heightMm: number;
    readonly counterHeightMm: number;
    readonly overheadCabinetBottomMm: number;
    readonly basin: {
      readonly footprintMm: RectMm;
      readonly finish: "MATTE_BLACK";
      readonly rimElevationMm: number;
    };
    readonly appliances: readonly [
      {
        readonly kind: "WASHER";
        readonly footprintMm: RectMm;
        readonly finish: "WHITE";
      },
      {
        readonly kind: "DRYER";
        readonly footprintMm: RectMm;
        readonly finish: "WHITE";
      },
    ];
  };
  readonly clearFloorRectMm: RectMm;
  readonly applianceServiceRectMm: RectMm;
}

export interface EnsuiteBathroomFitout {
  readonly id: string;
  readonly sourceId: string;
  readonly architecturalSourceId: string;
  readonly status: "CLIENT_DESIGN_CONCEPT";
  readonly roomId: "ROOM-1-11";
  readonly corridorDoorId: "DOOR-102-111";
  readonly bedroomDoorId: "DOOR-108-111";
  readonly frontWindowId: "FRONT-03";
  readonly windowBacksplashTopElevationMm: number;
  readonly bathtub: {
    readonly footprintMm: RectMm;
    readonly innerBasinMm: RectMm;
    readonly facing: "EAST";
    readonly rimElevationMm: number;
  };
  readonly toilet: {
    readonly footprintMm: RectMm;
    readonly concealedCisternRectMm: RectMm;
    readonly facing: "NORTH";
    readonly seatElevationMm: number;
    readonly moduleHeightMm: number;
  };
  readonly vanity: {
    readonly footprintMm: RectMm;
    readonly basinFootprintMm: RectMm;
    readonly mirrorPlanRectMm: RectMm;
    readonly facing: "WEST";
    readonly counterElevationMm: number;
    readonly basinRimElevationMm: number;
    readonly mirrorBottomElevationMm: number;
    readonly mirrorTopElevationMm: number;
  };
  readonly clearFloorRectMm: RectMm;
  readonly vanityClearanceRectMm: RectMm;
  readonly corridorLandingRectMm: RectMm;
  readonly bedroomLandingRectMm: RectMm;
}

export interface OfficeFitout {
  readonly id: string;
  readonly sourceId: string;
  readonly architecturalSourceId: string;
  readonly status: "CLIENT_DESIGN_CONCEPT";
  readonly roomId: "ROOM-1-04";
  readonly cabinet: {
    readonly wallId: "IW-ENTRY-EAST";
    readonly footprintMm: RectMm;
    readonly facing: "EAST";
    readonly heightMm: number;
    readonly printerNiche: {
      readonly footprintMm: RectMm;
      readonly bottomElevationMm: number;
      readonly heightMm: number;
    };
  };
  readonly desk: {
    readonly footprintMm: RectMm;
    readonly facing: "SOUTH";
    readonly topElevationMm: number;
    readonly monitor: {
      readonly centerMm: Point2Mm;
      readonly screenFacing: "NORTH";
      readonly diagonalIn: 40;
      readonly aspectRatio: "21:9";
      readonly widthMm: number;
      readonly heightMm: number;
      readonly curveRadiusMm: number;
      readonly maxThicknessMm: number;
      readonly centerElevationMm: number;
    };
  };
  readonly chair: {
    readonly footprintMm: RectMm;
    readonly centerMm: Point2Mm;
    readonly facing: "SOUTH";
    readonly seatElevationMm: number;
    readonly backTopElevationMm: number;
  };
  readonly printer: {
    readonly footprintMm: RectMm;
    readonly baseElevationMm: number;
    readonly heightMm: number;
    readonly facing: "EAST";
    readonly finish: "WHITE_BLACK";
    readonly integrated: true;
  };
  readonly whiteboard: {
    readonly wallId: "IW-STUDY-NORTH";
    readonly footprintMm: RectMm;
    readonly facing: "SOUTH";
    readonly bottomElevationMm: number;
    readonly heightMm: number;
    readonly openingId: "EAST-01";
  };
  readonly clearEntryRectMm: RectMm;
}

export interface EntryFitout {
  readonly id: string;
  readonly sourceId: string;
  readonly architecturalSourceId: string;
  readonly status: "CLIENT_DESIGN_CONCEPT";
  readonly roomId: "ROOM-1-01";
  readonly wallId: "IW-ENTRY-EAST";
  readonly exteriorOpeningId: "FRONT-ENTRY";
  readonly corridorDoorId: "DOOR-101-102";
  readonly facing: "WEST";
  readonly footprintMm: RectMm;
  readonly heightMm: number;
  readonly wardrobe: {
    readonly footprintMm: RectMm;
    readonly doorCount: 2;
    readonly coatRailElevationMm: number;
    readonly upperShelfElevationMm: number;
  };
  readonly bench: {
    readonly footprintMm: RectMm;
    readonly seatElevationMm: number;
    readonly cushionThicknessMm: number;
    readonly shoeDrawerCount: 2;
  };
  readonly hookPanel: {
    readonly footprintMm: RectMm;
    readonly bottomElevationMm: number;
    readonly topElevationMm: number;
    readonly hookCentersMm: readonly [Point2Mm, Point2Mm, Point2Mm];
    readonly hookElevationMm: number;
  };
  readonly overheadCabinet: {
    readonly footprintMm: RectMm;
    readonly bottomElevationMm: number;
  };
  readonly clearFloorRectMm: RectMm;
}

export interface BedroomFitout {
  readonly id: string;
  readonly sourceId: string;
  readonly architecturalSourceId: string;
  readonly status: "CLIENT_DESIGN_CONCEPT";
  readonly roomId: "ROOM-1-08";
  readonly entryDoorId: "DOOR-102-108";
  readonly bathroomDoorId: "DOOR-108-111";
  readonly frontWindowIds: readonly ["FRONT-04", "FRONT-05"];
  readonly bed: {
    /** Flush upholstered platform, kept to the exact requested bed footprint. */
    readonly footprintMm: RectMm;
    readonly mattressFootprintMm: RectMm;
    readonly mattressWidthMm: 1800;
    readonly mattressLengthMm: 2200;
    readonly frameHeightMm: number;
    readonly mattressTopElevationMm: number;
    readonly headboardRectMm: RectMm;
    readonly headboardTopElevationMm: number;
    readonly facing: "NORTH";
  };
  readonly wardrobe: {
    readonly footprintMm: RectMm;
    readonly facing: "WEST";
    readonly heightMm: number;
    readonly slidingPanelCount: 3;
    readonly mirroredPanelIndex: 1;
  };
  readonly clearancesMm: {
    readonly westToBathroom: number;
    readonly eastAtWardrobe: number;
    readonly foot: number;
    readonly openEntryLeaf: number;
  };
  readonly westBathroomAccessRectMm: RectMm;
  readonly eastBedsideAccessRectMm: RectMm;
  readonly footAccessRectMm: RectMm;
}

export interface FireplacePier {
  readonly id: string;
  readonly rectMm: RectMm;
}

export type FurnitureFacing = "NORTH" | "SOUTH" | "EAST" | "WEST";

export type ChildBedroomTheme = "SAGE_GLOW" | "MIDNIGHT_SAND";

export interface ChildBedroomFitout {
  readonly id: string;
  readonly sourceId: string;
  readonly architecturalSourceId: string;
  readonly status: "CLIENT_DESIGN_CONCEPT";
  readonly roomId: "ROOM-1-09" | "ROOM-1-10";
  readonly entryDoorId: "DOOR-102-109" | "DOOR-102-110";
  readonly gardenWindowId: "GARDEN-03" | "GARDEN-02";
  readonly theme: ChildBedroomTheme;
  readonly bed: {
    readonly footprintMm: RectMm;
    readonly mattressFootprintMm: RectMm;
    readonly mattressWidthMm: 1200;
    readonly mattressLengthMm: 2100;
    readonly frameHeightMm: number;
    readonly mattressTopElevationMm: number;
    readonly headboardRectMm: RectMm;
    readonly headboardTopElevationMm: number;
    readonly facing: "EAST" | "WEST";
  };
  readonly wardrobe: {
    readonly footprintMm: RectMm;
    readonly facing: "EAST";
    readonly heightMm: number;
    readonly doorCount: 3;
  };
  readonly desk: {
    readonly footprintMm: RectMm;
    readonly facing: "SOUTH" | "WEST";
    readonly topElevationMm: number;
  };
  readonly chair: {
    readonly footprintMm: RectMm;
    readonly centerMm: Point2Mm;
    readonly facing: "NORTH" | "EAST";
    readonly seatElevationMm: number;
    readonly backTopElevationMm: number;
    readonly wheelCount: 5;
  };
  readonly featureWall: {
    readonly footprintMm: RectMm;
    readonly facing: "EAST" | "WEST";
    readonly topElevationMm: number;
    readonly motif: "GLOW_HALO" | "OAK_RIBBON";
  };
  readonly pinboard: {
    readonly footprintMm: RectMm;
    readonly facing: "SOUTH" | "WEST";
    readonly bottomElevationMm: number;
    readonly heightMm: number;
  };
  /** Clear landing immediately beyond the fully open door leaf. */
  readonly clearEntryRectMm: RectMm;
  /** Unfurnished floor area large enough for play and a walkthrough preset. */
  readonly clearPlayRectMm: RectMm;
  /** Furniture-free apron across the glazing; the walk path targets its sliding half. */
  readonly windowClearanceRectMm: RectMm;
}

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
    readonly chairSeatWidthMm: number;
    readonly chairSeatDepthMm: number;
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
    standingPointMm: { x: 25000, y: 5850 },
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
    standingPointMm: { x: 19100, y: 6030 },
  },
  {
    id: "ROOM-1-09",
    number: "1.09",
    name: "Detská izba 1",
    documentedAreaM2: 16.3,
    clearHeightMm: 2600,
    ceiling: "FLAT",
    floor: "VINYL",
    wetRoom: false,
    rectsMm: [{ x0: 15143, y0: 7741, x1: 20641, y1: 10699 }],
    standingPointMm: { x: 17450, y: 9200 },
  },
  {
    id: "ROOM-1-10",
    number: "1.10",
    name: "Detská izba 2",
    documentedAreaM2: 15.45,
    clearHeightMm: 2600,
    ceiling: "FLAT",
    floor: "VINYL",
    wetRoom: false,
    rectsMm: [{ x0: 11143, y0: 6699, x1: 15003, y1: 10699 }],
    standingPointMm: { x: 12650, y: 9400 },
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
 * at x ≈ 24 090. The 24. 8. 2026 client revision removes its westernmost
 * 600 mm, exactly opposite the fridge, while preserving the appliance axis
 * and the eastern L-return. Fronts, worktop and appliances are a design finish.
 */
export const KITCHEN_RUN: KitchenRun = Object.freeze({
  id: "KITCHEN-RUN",
  designSourceId: SOURCES.clientKitchenRevision20260823.id,
  eastReturnSourceId: SOURCES.clientKitchenLRevision20260823.id,
  clearanceRevisionSourceId: SOURCES.clientKitchenClearanceRevision20260824.id,
  rectMm: { x0: 22791, y0: 10949, x1: 25691, y1: 11550 },
  counterHeightMm: 900,
  fridgeUnitRectMm: { x0: 22791, y0: 10949, x1: 23391, y1: 11550 },
  fridgeCabinetHeightMm: 2250,
  sinkCenterXmm: 24300,
  dishwasherXmm: [24700, 25300] as const,
  peninsulaRectMm: { x0: 23391, y0: 12544, x1: 27541, y1: 13144 },
  eastReturnRectMm: { x0: 26941, y0: 11550, x1: 27541, y1: 12544 },
  hobCenterXmm: 24090,
  ovenCenterXmm: 24090,
  extractorCenterXmm: 24090,
  extractorWidthMm: 900,
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
 * Final client layout for the L-shaped room 1.05. The fixed architecture stays
 * unchanged: the east leg is the walk-in wet zone and the complete north
 * recess becomes one 2 616 mm built-in wall with a basin and two appliances.
 */
export const BATHROOM_FITOUT: BathroomFitout = Object.freeze({
  id: "BATHROOM-FITOUT-BUILTIN-2026-08-23",
  sourceId: SOURCES.clientBathroomBuiltInRevision20260823.id,
  architecturalSourceId: SOURCES.floorPlan.id,
  status: "CLIENT_DESIGN_CONCEPT",
  roomId: "ROOM-1-05",
  shower: {
    footprintMm: { x0: 26291, y0: 6652, x1: 27541, y1: 7552 },
    // A narrow fixed return protects the dry room while leaving a 600 mm
    // threshold-free entrance on the west edge of the shower.
    glassPanelMm: { x0: 26291, y0: 6652, x1: 26306, y1: 6952 },
    clearEntryWidthMm: 600,
    linearDrainMm: { x0: 27391, y0: 6752, x1: 27471, y1: 7452 },
  },
  builtIn: {
    footprintMm: { x0: 22783, y0: 8322, x1: 25399, y1: 8972 },
    facing: "SOUTH",
    heightMm: 2350,
    counterHeightMm: 900,
    overheadCabinetBottomMm: 1100,
    basin: {
      footprintMm: { x0: 22883, y0: 8422, x1: 23983, y1: 8872 },
      finish: "MATTE_BLACK",
      rimElevationMm: 900,
    },
    appliances: [
      {
        kind: "WASHER",
        footprintMm: { x0: 24049, y0: 8352, x1: 24649, y1: 8952 },
        finish: "WHITE",
      },
      {
        kind: "DRYER",
        footprintMm: { x0: 24749, y0: 8352, x1: 25349, y1: 8952 },
        finish: "WHITE",
      },
    ],
  },
  clearFloorRectMm: { x0: 22783, y0: 7453, x1: 25399, y1: 8322 },
  applianceServiceRectMm: { x0: 24049, y0: 7422, x1: 25349, y1: 8322 },
});

/**
 * Plan-faithful en-suite bathroom in 1.11. A slim 1 800 × 700 mm bath follows
 * the west wall, a compact wall-hung WC stays centred under FRONT-03 and the
 * floating vanity occupies the east wall beyond both open door leaves.
 */
export const ENSUITE_BATHROOM_FITOUT: EnsuiteBathroomFitout = Object.freeze({
  id: "ENSUITE-BATHROOM-FITOUT-2026-08-24",
  sourceId: SOURCES.clientEnsuiteBathroomRevision20260824.id,
  architecturalSourceId: SOURCES.floorPlan.id,
  status: "CLIENT_DESIGN_CONCEPT",
  roomId: "ROOM-1-11",
  corridorDoorId: "DOOR-102-111",
  bedroomDoorId: "DOOR-108-111",
  frontWindowId: "FRONT-03",
  windowBacksplashTopElevationMm: 1680,
  bathtub: {
    footprintMm: { x0: 13941, y0: 3563, x1: 14641, y1: 5363 },
    innerBasinMm: { x0: 14021, y0: 3663, x1: 14581, y1: 5263 },
    facing: "EAST",
    rimElevationMm: 570,
  },
  toilet: {
    footprintMm: { x0: 15160, y0: 3504, x1: 15520, y1: 4064 },
    concealedCisternRectMm: { x0: 15090, y0: 3504, x1: 15590, y1: 3704 },
    facing: "NORTH",
    seatElevationMm: 450,
    moduleHeightMm: 1150,
  },
  vanity: {
    footprintMm: { x0: 16263, y0: 4461, x1: 16743, y1: 5361 },
    basinFootprintMm: { x0: 16273, y0: 4561, x1: 16633, y1: 5261 },
    mirrorPlanRectMm: { x0: 16713, y0: 4521, x1: 16727, y1: 5301 },
    facing: "WEST",
    counterElevationMm: 820,
    basinRimElevationMm: 880,
    mirrorBottomElevationMm: 1050,
    mirrorTopElevationMm: 1950,
  },
  clearFloorRectMm: { x0: 15100, y0: 4064, x1: 15580, y1: 4874 },
  vanityClearanceRectMm: { x0: 15563, y0: 4461, x1: 16263, y1: 5361 },
  corridorLandingRectMm: { x0: 15170, y0: 4821, x1: 15610, y1: 5261 },
  bedroomLandingRectMm: { x0: 16172.5, y0: 3781, x1: 16612.5, y1: 4221 },
});

/** Reoriented minimalist home-office composition fitted around both study windows. */
export const OFFICE_FITOUT: OfficeFitout = Object.freeze({
  id: "OFFICE-FITOUT-2026-08-24",
  sourceId: SOURCES.clientOfficeRelayoutRevision20260824.id,
  architecturalSourceId: SOURCES.floorPlan.id,
  status: "CLIENT_DESIGN_CONCEPT",
  roomId: "ROOM-1-04",
  cabinet: {
    wallId: "IW-ENTRY-EAST",
    footprintMm: { x0: 24192, y0: 3504, x1: 24730, y1: 5201 },
    facing: "EAST",
    heightMm: 2550,
    printerNiche: {
      footprintMm: { x0: 24232, y0: 4590, x1: 24730, y1: 5151 },
      bottomElevationMm: 650,
      heightMm: 500,
    },
  },
  desk: {
    footprintMm: { x0: 25330, y0: 3600, x1: 27130, y1: 4400 },
    facing: "SOUTH",
    topElevationMm: 750,
    monitor: {
      centerMm: { x: 26230, y: 3850 },
      screenFacing: "NORTH",
      diagonalIn: 40,
      aspectRatio: "21:9",
      widthMm: 934,
      heightMm: 400,
      curveRadiusMm: 2500,
      maxThicknessMm: 35,
      centerElevationMm: 1120,
    },
  },
  chair: {
    footprintMm: { x0: 25830, y0: 4520, x1: 26630, y1: 5320 },
    centerMm: { x: 26230, y: 4920 },
    facing: "SOUTH",
    seatElevationMm: 460,
    backTopElevationMm: 1300,
  },
  printer: {
    footprintMm: { x0: 24300, y0: 4650, x1: 24720, y1: 5090 },
    baseElevationMm: 760,
    heightMm: 230,
    facing: "EAST",
    finish: "WHITE_BLACK",
    integrated: true,
  },
  whiteboard: {
    wallId: "IW-STUDY-NORTH",
    footprintMm: { x0: 25240, y0: 6397, x1: 26940, y1: 6412 },
    facing: "SOUTH",
    bottomElevationMm: 950,
    heightMm: 1000,
    openingId: "EAST-01",
  },
  clearEntryRectMm: { x0: 23682, y0: 5400, x1: 25220, y1: 6412 },
} as const);

/** Full-height coat, shoe and seating composition in the 1.01 wall recess. */
export const ENTRY_FITOUT: EntryFitout = Object.freeze({
  id: "ENTRY-FITOUT-2026-08-24",
  sourceId: SOURCES.clientEntryFitoutRevision20260824.id,
  architecturalSourceId: SOURCES.floorPlan.id,
  status: "CLIENT_DESIGN_CONCEPT",
  roomId: "ROOM-1-01",
  wallId: "IW-ENTRY-EAST",
  exteriorOpeningId: "FRONT-ENTRY",
  corridorDoorId: "DOOR-101-102",
  facing: "WEST",
  footprintMm: { x0: 23409, y0: 3504, x1: 23989, y1: 5201 },
  heightMm: 2550,
  wardrobe: {
    footprintMm: { x0: 23409, y0: 4251, x1: 23989, y1: 5201 },
    doorCount: 2,
    coatRailElevationMm: 1650,
    upperShelfElevationMm: 2050,
  },
  bench: {
    footprintMm: { x0: 23529, y0: 3544, x1: 23989, y1: 4204 },
    seatElevationMm: 460,
    cushionThicknessMm: 35,
    shoeDrawerCount: 2,
  },
  hookPanel: {
    footprintMm: { x0: 23965, y0: 3544, x1: 23989, y1: 4204 },
    bottomElevationMm: 460,
    topElevationMm: 1900,
    hookCentersMm: [
      { x: 23925, y: 3690 },
      { x: 23925, y: 3874 },
      { x: 23925, y: 4058 },
    ],
    hookElevationMm: 1550,
  },
  overheadCabinet: {
    footprintMm: { x0: 23409, y0: 3504, x1: 23989, y1: 4251 },
    bottomElevationMm: 1900,
  },
  clearFloorRectMm: { x0: 21543, y0: 3504, x1: 23289, y1: 5201 },
} as const);

/**
 * Minimalist primary bedroom in 1.08. D1.1.002 gives a clear 4 300 × 2 857 mm
 * room with two 800 mm south windows, a corridor door at the north-west and
 * direct access to bathroom 1.11 on the west wall. The slim 1 800 × 2 200 mm
 * bed is shifted 150 mm west of the room centre so a full-wall 600 mm-deep
 * wardrobe still leaves an 800 mm bedside passage, while the west side remains
 * the direct bathroom route. FRONT-05 moves 200 mm west to leave a clean pier
 * before the wardrobe; the low headboard stays below both 900 mm window sills.
 */
export const BEDROOM_FITOUT: BedroomFitout = Object.freeze({
  id: "BEDROOM-FITOUT-2026-08-24",
  sourceId: SOURCES.clientBedroomDoorWindowRevision20260824.id,
  architecturalSourceId: SOURCES.floorPlan.id,
  status: "CLIENT_DESIGN_CONCEPT",
  roomId: "ROOM-1-08",
  entryDoorId: "DOOR-102-108",
  bathroomDoorId: "DOOR-108-111",
  frontWindowIds: ["FRONT-04", "FRONT-05"],
  bed: {
    footprintMm: { x0: 18042, y0: 3504, x1: 19842, y1: 5704 },
    mattressFootprintMm: { x0: 18042, y0: 3504, x1: 19842, y1: 5704 },
    mattressWidthMm: 1800,
    mattressLengthMm: 2200,
    frameHeightMm: 300,
    mattressTopElevationMm: 540,
    headboardRectMm: { x0: 18042, y0: 3504, x1: 19842, y1: 3584 },
    headboardTopElevationMm: 840,
    facing: "NORTH",
  },
  wardrobe: {
    footprintMm: { x0: 20642, y0: 3504, x1: 21242, y1: 6361 },
    facing: "WEST",
    heightMm: 2550,
    slidingPanelCount: 3,
    mirroredPanelIndex: 1,
  },
  clearancesMm: {
    westToBathroom: 1100,
    eastAtWardrobe: 800,
    foot: 657,
    openEntryLeaf: 793,
  },
  westBathroomAccessRectMm: { x0: 17249, y0: 4401, x1: 18042, y1: 5704 },
  eastBedsideAccessRectMm: { x0: 19842, y0: 3504, x1: 20642, y1: 5704 },
  footAccessRectMm: { x0: 18042, y0: 5704, x1: 20642, y1: 6361 },
} as const);

/**
 * Two related but non-identical children's rooms. Room 1.09 keeps the direct
 * south-door / north-glazing axis clear and concentrates storage on the short
 * west bay, with the bed and desk on the solid east side. Room 1.10 uses the
 * west wall for the bed and wardrobe and the east wall north of the door for
 * the desk. Both layouts preserve a real play zone, the open door leaf and an
 * unobstructed approach to the 2.0 / 2.5 m garden glazing.
 */
export const CHILDRENS_BEDROOM_FITOUTS: readonly [
  ChildBedroomFitout,
  ChildBedroomFitout,
] = Object.freeze([
  {
    id: "CHILD-BEDROOM-109-FITOUT-2026-08-24",
    sourceId: SOURCES.clientChildrensRoomsRevision20260824.id,
    architecturalSourceId: SOURCES.floorPlan.id,
    status: "CLIENT_DESIGN_CONCEPT",
    roomId: "ROOM-1-09",
    entryDoorId: "DOOR-102-109",
    gardenWindowId: "GARDEN-03",
    theme: "SAGE_GLOW",
    bed: {
      footprintMm: { x0: 18391, y0: 7841, x1: 20641, y1: 9141 },
      mattressFootprintMm: { x0: 18491, y0: 7891, x1: 20591, y1: 9091 },
      mattressWidthMm: 1200,
      mattressLengthMm: 2100,
      frameHeightMm: 280,
      mattressTopElevationMm: 530,
      headboardRectMm: { x0: 20591, y0: 7841, x1: 20641, y1: 9141 },
      headboardTopElevationMm: 1420,
      facing: "WEST",
    },
    wardrobe: {
      footprintMm: { x0: 15143, y0: 8241, x1: 15743, y1: 10699 },
      facing: "EAST",
      heightMm: 2550,
      doorCount: 3,
    },
    desk: {
      footprintMm: { x0: 18341, y0: 10099, x1: 19941, y1: 10699 },
      facing: "SOUTH",
      topElevationMm: 740,
    },
    chair: {
      footprintMm: { x0: 18741, y0: 9250, x1: 19541, y1: 10050 },
      centerMm: { x: 19141, y: 9650 },
      facing: "NORTH",
      seatElevationMm: 440,
      backTopElevationMm: 1050,
      wheelCount: 5,
    },
    featureWall: {
      footprintMm: { x0: 20616, y0: 7741, x1: 20641, y1: 9341 },
      facing: "WEST",
      topElevationMm: 2200,
      motif: "GLOW_HALO",
    },
    pinboard: {
      footprintMm: { x0: 18341, y0: 10674, x1: 19941, y1: 10699 },
      facing: "SOUTH",
      bottomElevationMm: 1040,
      heightMm: 700,
    },
    clearEntryRectMm: { x0: 16743, y0: 7741, x1: 18341, y1: 10099 },
    clearPlayRectMm: { x0: 15843, y0: 8561, x1: 18341, y1: 9699 },
    windowClearanceRectMm: { x0: 15840, y0: 9699, x1: 17840, y1: 10699 },
  },
  {
    id: "CHILD-BEDROOM-110-FITOUT-2026-08-24",
    sourceId: SOURCES.clientChildrensRoomsRevision20260824.id,
    architecturalSourceId: SOURCES.floorPlan.id,
    status: "CLIENT_DESIGN_CONCEPT",
    roomId: "ROOM-1-10",
    entryDoorId: "DOOR-102-110",
    gardenWindowId: "GARDEN-02",
    theme: "MIDNIGHT_SAND",
    bed: {
      footprintMm: { x0: 11243, y0: 6699, x1: 13543, y1: 7999 },
      mattressFootprintMm: { x0: 11343, y0: 6749, x1: 13443, y1: 7949 },
      mattressWidthMm: 1200,
      mattressLengthMm: 2100,
      frameHeightMm: 280,
      mattressTopElevationMm: 530,
      headboardRectMm: { x0: 11243, y0: 6699, x1: 11293, y1: 7999 },
      headboardTopElevationMm: 1480,
      facing: "EAST",
    },
    wardrobe: {
      footprintMm: { x0: 11143, y0: 8299, x1: 11743, y1: 10699 },
      facing: "EAST",
      heightMm: 2550,
      doorCount: 3,
    },
    desk: {
      footprintMm: { x0: 14403, y0: 8400, x1: 15003, y1: 10000 },
      facing: "WEST",
      topElevationMm: 740,
    },
    chair: {
      footprintMm: { x0: 13400, y0: 9000, x1: 14200, y1: 9800 },
      centerMm: { x: 13800, y: 9400 },
      facing: "EAST",
      seatElevationMm: 440,
      backTopElevationMm: 1050,
      wheelCount: 5,
    },
    featureWall: {
      footprintMm: { x0: 11143, y0: 6699, x1: 11168, y1: 8199 },
      facing: "EAST",
      topElevationMm: 2200,
      motif: "OAK_RIBBON",
    },
    pinboard: {
      footprintMm: { x0: 14978, y0: 8400, x1: 15003, y1: 9800 },
      facing: "WEST",
      bottomElevationMm: 1040,
      heightMm: 700,
    },
    clearEntryRectMm: { x0: 13543, y0: 7601, x1: 14403, y1: 8899 },
    clearPlayRectMm: { x0: 11843, y0: 8299, x1: 13400, y1: 10699 },
    windowClearanceRectMm: { x0: 11840, y0: 9800, x1: 14340, y1: 10699 },
  },
] as const);

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
    chairSeatWidthMm: 470,
    chairSeatDepthMm: 460,
    chairs: [
      { id: "DINING-CHAIR-SW", centerMm: { x: 24175, y: 14450 }, facing: "NORTH" },
      { id: "DINING-CHAIR-SE", centerMm: { x: 24725, y: 14450 }, facing: "NORTH" },
      { id: "DINING-CHAIR-NW", centerMm: { x: 24175, y: 15050 }, facing: "SOUTH" },
      { id: "DINING-CHAIR-NE", centerMm: { x: 24725, y: 15050 }, facing: "SOUTH" },
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
    hinge: -1,
    revisionSourceId: SOURCES.clientBedroomDoorWindowRevision20260824.id,
    previousHinge: 1,
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
