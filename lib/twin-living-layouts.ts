/**
 * Switchable arrangements of the living/dining zone in room 1.03.
 *
 * Variant A is the client concept of 23. 8. 2026 that the active 3D model
 * shows. Variant B follows the client's sketch of 11. 9. 2026: the TV wall
 * moves onto the solid part of the garden gable, the L sofa turns its back to
 * the kitchen, the dining table stands along the west wall and the cylindrical
 * stove sits in the north-west corner beside the fixed glazing. The kitchen,
 * peninsula and east return are shared by both variants; since 11. 9. 2026 the
 * peninsula worktop edge sits at 13 800 (flush with the terrace-door reveal)
 * and both variants seat six at a 2 000 × 900 mm table. All values are plan
 * millimetres in the house frame (x east, y toward the garden).
 */
import { SOURCES, type Point2Mm } from "./twin-site";
import {
  FIREPLACE_STOVE,
  KITCHEN_RUN as SOURCE_KITCHEN_RUN,
  LIVING_DINING_FITOUT,
  type FireplaceStove,
  type LivingDiningFitout,
  type RectMm,
} from "./twin-interior-baseline";
// The active model's kitchen run follows the 300 mm load-bearing kitchen wall (12. 9. 2026).
import { INTERIOR_DOORS, INTERIOR_ROOMS, KITCHEN_BEARING_WALL, KITCHEN_BEARING_WALL_EAST, KITCHEN_RUN } from "./twin-interior";
import { SERVICE_CORE_REVISION } from "./technical-design";

export type LivingLayoutId = "A" | "B";

export interface CoffeeTableSpec {
  readonly centerMm: Point2Mm;
  /** Base cylinder diameter and the plan scaling that turns it into an oval. */
  readonly diameterM: number;
  readonly scaleX: number;
  readonly scaleZ: number;
  readonly topElevationM: number;
  readonly pedestalDiameterM: number;
  readonly top: "LIMESTONE" | "OAK";
}

export interface LivingLayout {
  readonly id: LivingLayoutId;
  readonly sourceId: string;
  /** Short name for the switch. */
  readonly label: string;
  /** One-sentence description shown under the switch. */
  readonly summary: string;
  readonly fitout: LivingDiningFitout;
  readonly stove: FireplaceStove;
  readonly rugRectMm: RectMm;
  readonly coffeeTables: readonly CoffeeTableSpec[];
  /** Single walk-collision envelope around both coffee tables. */
  readonly coffeeTableGuardRectMm: RectMm;
  /** Dimensional reasoning shown in the room guide ("Prečo je to takto"). */
  readonly notes: readonly string[];
}

export const DEFAULT_LIVING_LAYOUT_ID: LivingLayoutId = "A";

export function normalizeLivingLayout(value: string | null | undefined): LivingLayoutId {
  return value?.toUpperCase() === "B" ? "B" : "A";
}

/** Plan rectangle of the dining table derived from its centre, axis and size. */
export function diningTableRectMm(dining: LivingDiningFitout["dining"]): RectMm {
  const [sizeX, sizeY] =
    dining.axis === "X"
      ? [dining.tableLengthMm, dining.tableDepthMm]
      : [dining.tableDepthMm, dining.tableLengthMm];
  return {
    x0: dining.tableCenterMm.x - sizeX / 2,
    x1: dining.tableCenterMm.x + sizeX / 2,
    y0: dining.tableCenterMm.y - sizeY / 2,
    y1: dining.tableCenterMm.y + sizeY / 2,
  };
}

/** Plan rectangle of a dining chair seat for its facing. */
export function diningChairSeatRectMm(
  dining: LivingDiningFitout["dining"],
  chair: LivingDiningFitout["dining"]["chairs"][number],
): RectMm {
  const alongX = chair.facing === "NORTH" || chair.facing === "SOUTH";
  const sizeX = alongX ? dining.chairSeatWidthMm : dining.chairSeatDepthMm;
  const sizeY = alongX ? dining.chairSeatDepthMm : dining.chairSeatWidthMm;
  return {
    x0: chair.centerMm.x - sizeX / 2,
    x1: chair.centerMm.x + sizeX / 2,
    y0: chair.centerMm.y - sizeY / 2,
    y1: chair.centerMm.y + sizeY / 2,
  };
}

/** Plan bounding box of an oval coffee table. */
export function coffeeTableRectMm(table: CoffeeTableSpec): RectMm {
  const halfX = (table.diameterM * table.scaleX * 1000) / 2;
  const halfY = (table.diameterM * table.scaleZ * 1000) / 2;
  return {
    x0: table.centerMm.x - halfX,
    x1: table.centerMm.x + halfX,
    y0: table.centerMm.y - halfY,
    y1: table.centerMm.y + halfY,
  };
}

/**
 * Variant B fit-out. The main sofa module faces the garden gable, so the
 * cushion layout is the variant A module turned a quarter clockwise; the
 * chaise keeps its 1 100 × 2 750 mm size and now runs north along the east
 * wall. With the peninsula worktop edge at 13 800 the sofa back stands at
 * 14 800 (a 1 000 mm walkway) and 200 mm off the east wall; the screen bay
 * follows the sofa axis. The six-seat table stands north–south by the west wall.
 */
export const LIVING_DINING_FITOUT_B: LivingDiningFitout = Object.freeze({
  id: "LIVING-DINING-FITOUT-B-2026-09-11",
  sourceId: SOURCES.clientLivingVariantB20260911.id,
  status: "CLIENT_DESIGN_CONCEPT",
  tvWall: {
    // Solid larch-clad gable wall runs 24 040–27 540; the cabinet leaves a
    // 100 mm reveal beside the fixed pane and meets the east wall.
    rectMm: { x0: 24140, y0: 18598, x1: 27541, y1: 19035 },
    facing: "SOUTH" as const,
    heightMm: 2600,
    centralBayMm: [24741, 27041] as const,
    towerLabels: ["pri presklení terasy", "pri východnej stene"] as const,
    tv: LIVING_DINING_FITOUT.tvWall.tv,
  },
  sofa: {
    mainRectMm: { x0: 24441, y0: 14800, x1: 27341, y1: 16030 },
    chaiseRectMm: { x0: 26241, y0: 14800, x1: 27341, y1: 17550 },
    facing: "NORTH" as const,
    seatHeightMm: LIVING_DINING_FITOUT.sofa.seatHeightMm,
  },
  dining: {
    tableCenterMm: { x: 22950, y: 16400 },
    axis: "Y" as const,
    tableLengthMm: LIVING_DINING_FITOUT.dining.tableLengthMm,
    tableDepthMm: LIVING_DINING_FITOUT.dining.tableDepthMm,
    tableHeightMm: LIVING_DINING_FITOUT.dining.tableHeightMm,
    chairSeatWidthMm: LIVING_DINING_FITOUT.dining.chairSeatWidthMm,
    chairSeatDepthMm: LIVING_DINING_FITOUT.dining.chairSeatDepthMm,
    // Chair centres sit 100 mm inside the table edge (330 mm tuck) at a 650 mm pitch.
    chairs: [
      { id: "DINING-CHAIR-W1", centerMm: { x: 22600, y: 15750 }, facing: "EAST" as const },
      { id: "DINING-CHAIR-W2", centerMm: { x: 22600, y: 16400 }, facing: "EAST" as const },
      { id: "DINING-CHAIR-W3", centerMm: { x: 22600, y: 17050 }, facing: "EAST" as const },
      { id: "DINING-CHAIR-E1", centerMm: { x: 23300, y: 15750 }, facing: "WEST" as const },
      { id: "DINING-CHAIR-E2", centerMm: { x: 23300, y: 16400 }, facing: "WEST" as const },
      { id: "DINING-CHAIR-E3", centerMm: { x: 23300, y: 17050 }, facing: "WEST" as const },
    ],
  },
});

/**
 * Variant B stove: the same Ø510 cylinder 55 mm off the west wall, moved into
 * the north-west corner 160 mm short of the gable pier. The door turns to the
 * south-east so the fire is seen from the sofa, the table and the terrace.
 */
export const FIREPLACE_STOVE_B: FireplaceStove = Object.freeze({
  ...FIREPLACE_STOVE,
  id: "FIREPLACE-STOVE-B-2026-09-11",
  sourceId: SOURCES.clientLivingVariantB20260911.id,
  facing: "SOUTH_EAST" as const,
  facingAngleDeg: -45,
  centerMm: { x: 21853, y: 18620 },
  footprintMm: { x0: 21598, y0: 18365, x1: 22108, y1: 18875 },
  window: { ...FIREPLACE_STOVE.window, handleSide: "GLAZING" as const },
  flue: { ...FIREPLACE_STOVE.flue, id: "FLUE-LIVING-103-B" as const },
});

const mm = (value: number) => String(value).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
/** Worktop edge of the peninsula on the living-room side (11. 9. 2026: flush with the terrace-door reveal). */
export const PENINSULA_WORKTOP_EDGE_YMM = KITCHEN_RUN.peninsulaRectMm.y1 + KITCHEN_RUN.peninsulaOverhangMm;
const KITCHEN_NOTE = `Polostrov je posunutý o 346 mm k obývačke: hrana jeho pracovnej dosky (${mm(PENINSULA_WORKTOP_EDGE_YMM)} mm) lícuje s ostením terasových dverí do dvora, pracovný priechod medzi zadnou linkou a polostrovom má ${mm(KITCHEN_RUN.peninsulaRectMm.y0 - KITCHEN_RUN.fridgeUnitRectMm.y1)} mm namiesto 994 mm podľa D1.1.002 a bočné rameno pri východnej stene sa predlžuje na ${mm(KITCHEN_RUN.eastReturnRectMm.y1 - KITCHEN_RUN.eastReturnRectMm.y0)} mm; pod oknom EAST-04 pokračuje len pracovná doska bez obkladu.`;
/** 12. 9. 2026: the kitchen's back wall carries the ring beam and the roof frames of the cathedral ceiling; both living layouts share it. */
const TECH_DOOR = INTERIOR_DOORS.find((door) => door.id === "DOOR-103-107")!;
const KITCHEN_BAY = INTERIOR_ROOMS.find((room) => room.id === "ROOM-1-03")!.rectsMm[1];
const BEARING_WALL_NOTE = `Stena za zadnou linkou medzi obývačkou a WC 1.06 / technickou miestnosťou 1.07 je nosné murivo hr. ${KITCHEN_BEARING_WALL.y1 - KITCHEN_BEARING_WALL.y0} mm (${mm(KITCHEN_BEARING_WALL.y0)}–${mm(KITCHEN_BEARING_WALL.y1)} mm) namiesto priečky 140 mm: stojí nad priečnym základovým pásom podľa D1.1.001 a nesie stužujúci veniec a oceľové rámy krovu katedrálového stropu obývačky. Vedie v jednej línii od ústia chodby (${mm(KITCHEN_BEARING_WALL.x0)} mm) po východnú fasádu (${mm(KITCHEN_BEARING_WALL_EAST.x1)} mm); prerušujú ju iba dvere do technickej miestnosti ${TECH_DOOR.widthMm} mm (${mm(TECH_DOOR.startMm)}–${mm(TECH_DOOR.startMm + TECH_DOOR.widthMm)} mm) s prekladom, za ktorými pokračuje ešte ${KITCHEN_BEARING_WALL_EAST.x1 - KITCHEN_BEARING_WALL_EAST.x0} mm muriva k fasáde. Zhrubla smerom do kuchyne, takže WC a jeho dvere sa nemenia; bývalý výstupok technickej miestnosti s dverami pripadol kuchynskému zálivu, ktorý má teraz ${mm(KITCHEN_BAY.x1 - KITCHEN_BAY.x0)} × ${KITCHEN_BAY.y1 - KITCHEN_BAY.y0} mm až po východnú stenu, dvere do technickej sa otvárajú do kuchyne s pántom pri východnom ostení a vonkajšie dvere ${SERVICE_CORE_REVISION.exteriorDoor.id} majú kvôli statike fasády ${SERVICE_CORE_REVISION.exteriorDoor.widthMm} mm namiesto ${mm(SERVICE_CORE_REVISION.exteriorDoorRevision.previousWidthMm)} mm. Zadná linka s chladničkou je posunutá o ${KITCHEN_RUN.rectMm.y0 - SOURCE_KITCHEN_RUN.rectMm.y0} mm k polostrovu so zachovanou inštalačnou medzerou ${KITCHEN_RUN.rectMm.y0 - KITCHEN_BEARING_WALL.y1} mm za korpusmi a jej čelo (${mm(KITCHEN_RUN.rectMm.y1)} mm) predstupuje o ${KITCHEN_RUN.rectMm.y1 - SOURCE_KITCHEN_RUN.rectMm.y1} mm pred koniec priečky chodby pri zálive; medzi jej východným koncom (${mm(KITCHEN_RUN.rectMm.x1)} mm) a dverami technickej zostáva ${TECH_DOOR.startMm - KITCHEN_RUN.rectMm.x1} mm. Nad ústím chodby (1 096 mm) prenáša zaťaženie veniec ako preklad. Rozmery prekladov, kotvenie rámov a základ posúdi statik.`;

const A: LivingLayout = {
  id: "A",
  sourceId: LIVING_DINING_FITOUT.sourceId,
  label: "TV stena pri západnej stene",
  summary:
    "TV zostava medzi kachľami a záhradným presklením, L-sedačka pri východnej stene oproti nej a jedálenský stôl pre šesť medzi kuchynským polostrovom a sedačkou.",
  fitout: LIVING_DINING_FITOUT,
  stove: FIREPLACE_STOVE,
  // Unchanged: the shipped ArchViz rug asset is matched to these exact bounds.
  rugRectMm: { x0: 22520, y0: 15580, x1: 27190, y1: 18880 },
  coffeeTables: [
    { centerMm: { x: 24380, y: 16680 }, diameterM: 1.15, scaleX: 1.12, scaleZ: 0.7, topElevationM: 0.34, pedestalDiameterM: 0.34, top: "LIMESTONE" },
    { centerMm: { x: 25020, y: 17140 }, diameterM: 0.78, scaleX: 1.05, scaleZ: 0.76, topElevationM: 0.42, pedestalDiameterM: 0.24, top: "OAK" },
  ],
  coffeeTableGuardRectMm: { x0: 23700, y0: 16220, x1: 25480, y1: 17580 },
  notes: [
    "TV zostava 437 × 3 370 mm stojí pri západnej stene medzi kachľami a pevným presklením štítu; 98″ televízor je v strednom poli 2 300 mm. Čelo hlavného modulu sedačky je 4 040 mm od čela TV zostavy.",
    "L-sedačka 1 230 × 2 900 mm s ležadlom 2 750 × 1 100 mm stojí pri východnej stene, 291 mm od nej. Jedálenský stôl 2 000 × 900 mm pre šesť osôb (23 800–25 800 × 14 580–15 480 mm) stojí rovnobežne s polostrovom s tromi stoličkami na každej dlhšej strane: za južnými stoličkami ostáva 650 mm k hrane pracovnej dosky, severné stoja nohami tesne pred kobercom a končia 240 mm pred líniou sedačky, k TV zostave ostáva 1 820 mm voľného nástupu; východný priechod k technickej miestnosti zostáva voľný.",
    "Krbové kachle Ø510 mm stoja 55 mm od západnej steny, 420 mm za koncom terasových dverí a 650 mm pred TV zostavou; dymovod stúpa zvislo v ich osi.",
    KITCHEN_NOTE,
    BEARING_WALL_NOTE,
  ],
};

const B: LivingLayout = {
  id: "B",
  sourceId: SOURCES.clientLivingVariantB20260911.id,
  label: "TV stena pri záhradnom štíte",
  summary:
    "TV zostava na plnej časti severnej steny, L-sedačka chrbtom ku kuchyni s ležadlom pri východnej stene, jedálenský stôl pre šesť pozdĺž západnej steny a kachle v severozápadnom rohu pri presklení.",
  fitout: LIVING_DINING_FITOUT_B,
  stove: FIREPLACE_STOVE_B,
  rugRectMm: { x0: 24241, y0: 14900, x1: 27391, y1: 18300 },
  coffeeTables: [
    { centerMm: { x: 25221, y: 17520 }, diameterM: 1.15, scaleX: 0.7, scaleZ: 1.12, topElevationM: 0.34, pedestalDiameterM: 0.34, top: "LIMESTONE" },
    { centerMm: { x: 25681, y: 16880 }, diameterM: 0.78, scaleX: 0.76, scaleZ: 1.05, topElevationM: 0.42, pedestalDiameterM: 0.24, top: "OAK" },
  ],
  coffeeTableGuardRectMm: { x0: 24770, y0: 16420, x1: 26030, y1: 18210 },
  notes: [
    "TV zostava 3 401 × 437 mm stojí na plnej časti záhradného štítu (24 140–27 541 mm), 100 mm od rámu pevného presklenia. Stred 98″ televízora leží na osi sedačky; od čela hlavného modulu je 2 568 mm, od očí sediaceho približne 3,2 m, čo dáva zorný uhol ≈ 37° (odporúčaných 30–40°).",
    "L-sedačka 2 900 × 1 230 mm s ležadlom 1 100 × 2 750 mm je otočená chrbtom ku kuchyni a stojí 200 mm od východnej steny. Medzi operadlom (14 800 mm) a hranou pracovnej dosky polostrova (13 800 mm) zostáva priechod 1 000 mm k jeho obslužnej strane; koberec 3 150 × 3 400 mm spája sedačku s TV stenou a dva oválne stolíky sú v rohu L.",
    "Jedálenský stôl 900 × 2 000 mm pre šesť osôb stojí pozdĺž západnej steny (22 500–23 400 × 15 400–17 400 mm) s tromi stoličkami na každej dlhšej strane: pri stene ostáva 957 mm na odsunutie stoličky, na východ 1 041 mm k sedačke (911 mm za sediacim). Terasové posuvné dvere, nástup z chodby aj pás 1 838 mm pri polostrove zostávajú voľné.",
    "Krbové kachle Ø510 mm sú v severozápadnom rohu 55 mm od západnej steny a 160 mm od piliera štítu; oheň je natočený na juhovýchod, takže ho vidno zo sedačky, od stola aj z terasy cez presklenie. Dymovod stúpa zvislo v osi kachlí (21 853; 18 620 mm), 415 mm pred rovinou štítu.",
    "Kuchynská linka, polostrov s varnou doskou aj bočné rameno pri východnej stene sú v oboch variantoch rovnaké; mení sa len obývacia a jedálenská zóna.",
    KITCHEN_NOTE,
    BEARING_WALL_NOTE,
  ],
};

export const LIVING_LAYOUTS: Readonly<Record<LivingLayoutId, LivingLayout>> = Object.freeze({ A, B });
export const LIVING_LAYOUT_IDS: readonly LivingLayoutId[] = ["A", "B"];
