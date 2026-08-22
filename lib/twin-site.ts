import { BREZI_6012_26_SJTSK_RING_MM } from "./twin-domain";

export type LayerId =
  | "cadastre"
  | "street"
  | "building"
  | "foundations"
  | "water"
  | "sewer"
  | "rainwater"
  | "electricity"
  | "contextNetworks";

export type ViewMode = "technical" | "realistic";
export type EvidenceKind =
  | "CURRENT_REGISTER"
  | "PROJECT_DESIGN"
  | "CLIENT_REVISION"
  | "DESIGN_PROPOSAL"
  | "PROVIDER_CONTEXT"
  | "SCAN_DOCUMENT"
  | "ARITHMETIC_DERIVATION"
  | "UNRESOLVED_AS_BUILT";

export interface Point2Mm {
  readonly x: number;
  readonly y: number;
}

export interface SourceRecord {
  readonly id: string;
  readonly title: string;
  readonly detail: string;
  readonly date: string;
  readonly page?: number;
  readonly scale?: string;
  readonly kind: EvidenceKind;
  readonly href?: string;
}

export interface CadastralParcel {
  readonly id: string;
  readonly nationalReference: string;
  readonly areaM2: number;
  readonly sjtskRingMm: readonly Point2Mm[];
  readonly sourceId: string;
  readonly isSubject: boolean;
}

export interface FoundationStrip {
  readonly id: string;
  readonly label: string;
  readonly startMm: Point2Mm;
  readonly endMm: Point2Mm;
  readonly widthMm: number;
  readonly heightMm: number;
  readonly baseElevationMm: number;
  readonly sourceId: string;
}

export interface UtilityRoute {
  readonly id: string;
  readonly label: string;
  readonly layer: Extract<
    LayerId,
    "water" | "sewer" | "rainwater" | "electricity" | "contextNetworks"
  >;
  readonly pointsMm: readonly Point2Mm[];
  readonly sourceId: string;
  readonly sourceIds?: readonly string[];
  readonly status: "EXISTING_CONTEXT" | "DESIGNED" | "FUTURE_OPTION";
  readonly revisionStatus: "COORDINATED" | "REVISION_CONFLICT";
  readonly radiusMm: number;
}

export const SOURCES = {
  cadastre: {
    id: "SRC-CUZK-CP",
    title: "ČÚZK · INSPIRE Cadastral Parcels",
    detail:
      "Aktuálna geometria parciel 613908-6012/26 a cestnej parcely 613908-6012/1 · EPSG:5514",
    date: "21. 8. 2026",
    kind: "CURRENT_REGISTER",
    href: "https://services.cuzk.gov.cz/wfs/inspire-cp-wfs.asp",
  },
  geometricPlan: {
    id: "SRC-GP-1631",
    title: "Geometrický plán č. 1631-13/2022",
    detail: "GP-sken.pdf · výkaz výmer a súradnice S-JTSK",
    date: "6/2023",
    page: 1,
    kind: "SCAN_DOCUMENT",
  },
  coordination: {
    id: "SRC-C3",
    title: "C3 · Koordinačná situácia",
    detail: "C3_celkova situace.pdf · georeferencovaná situačná revízia · konflikt mierky v razítku",
    date: "výkres 28. 4. 2026 · PDF 1. 5. 2026",
    page: 1,
    scale: "razítko 1:100 · vektory 1:200",
    kind: "PROJECT_DESIGN",
  },
  foundation: {
    id: "SRC-D11001",
    title: "D1.1.001 · Pôdorys základov",
    detail: "Pudorys zakladu.pdf · DPZS",
    date: "výkres 28. 4. 2026 · PDF 11. 5. 2026",
    page: 1,
    scale: "1:100",
    kind: "PROJECT_DESIGN",
  },
  floorPlan: {
    id: "SRC-D11002",
    title: "D1.1.002 · Pôdorys 1.NP",
    detail: "Pudorys 1.NP.pdf · aktívna návrhová geometria a orientácia domu",
    date: "výkres 28. 4. 2026 · PDF 11. 5. 2026",
    page: 1,
    scale: "1:100",
    kind: "PROJECT_DESIGN",
  },
  roofPlan: {
    id: "SRC-D11004",
    title: "D1.1.004 · Pôdorys strechy",
    detail:
      "Spojená sedlová strecha · spoločný uzol, úžľabie a nárožie · menovité sklony 30°/34°",
    date: "výkres 28. 4. 2026 · PDF 1. 5. 2026",
    page: 1,
    scale: "1:100",
    kind: "PROJECT_DESIGN",
  },
  clientRevision20260821: {
    id: "SRC-CLIENT-20260821",
    title: "Aktuálna revízia stavebníka",
    detail:
      "Ponechať komín pri hlavnom obytnom priestore, posunúť ho o 1 m hlbšie do záhrady a odstrániť druhý komín pri zóne 1.09; FV pole na dvorovej rovine krídla posunúť o 2 m hlbšie do záhrady; bočný spevnený prístup na východnej fasáde vycentrovať na dvere EAST-03; garážovú bránu presunúť na uličnú fasádu namiesto prvého garážového okna a viesť príjazd priamo od ulice.",
    date: "21. 8. 2026",
    kind: "CLIENT_REVISION",
  },
  clientRevision20260822: {
    id: "SRC-CLIENT-20260822",
    title: "Revízia stavebníka · interiér a štít terasy",
    detail:
      "Menšie krbové kachle s komínom hneď vedľa dverí na bazénovú terasu, opreté o západnú stenu obytného priestoru (murovaný pilier D1.1.002); štítová stena obytného priestoru ku krytej terase celá presklená bez plnej steny, jediné otváravé dverné krídlo; kuchyňa podľa pôdorysu D1.1.002 (zadná linka s drezom a umývačkou, polostrov s varnou doskou). Dôsledok: FV pole na dvorovej rovine posunuté o ďalších 1,1 m do záhrady kvôli odstupu od nového komína.",
    date: "22. 8. 2026",
    kind: "CLIENT_REVISION",
  },
  clientFenceMarkup20260821: {
    id: "SRC-CLIENT-FENCE-20260821",
    title: "Náčrt oplotenia stavebníka",
    detail:
      "Žltá línia uzatvára súkromnú záhradu na úrovni uličnej fasády domu a pokračuje po bočných a zadnej katastrálnej hranici; zelená vyznačuje samostatnú 4,2 m bránu v pôvodnom ľavom zjazde. Priamy príjazd k novej garážovej bráne zostáva otvorený od ulice.",
    date: "21. 8. 2026 · 16:22",
    kind: "CLIENT_REVISION",
  },
  clientGardenRevision20260821: {
    id: "SRC-CLIENT-GARDEN-20260821",
    title: "Revízia záhrady stavebníka",
    detail:
      "Bočné hranice majú byť plné a nepriehľadné, zadnú hranicu má tvoriť hustý živý plot a do stredu otvoreného L-dvora pri terase sa dopĺňa bazén s vodnou plochou 4,0 × 2,5 m.",
    date: "21. 8. 2026",
    kind: "CLIENT_REVISION",
  },
  clientExteriorRevision20260821: {
    id: "SRC-CLIENT-EXTERIOR-20260821",
    title: "Aktuálna revízia exteriéru stavebníka",
    detail:
      "Dokresliť uličnú komunikáciu a samostatné napojenia od vozovky ku garáži a hlavnému vstupu; bazén zväčšiť na vodnú plochu 5,0 × 3,0 m a jeho lem napojiť bez medzery na severnú hranu hlavnej záhradnej terasy.",
    date: "21. 8. 2026",
    kind: "CLIENT_REVISION",
  },
  fenceDesignProposal20260821: {
    id: "SRC-FENCE-DESIGN-20260821",
    title: "Dizajnový návrh oplotenia",
    detail:
      "Vizualizačný návrh kombinuje čelné zvislé hliníkové lamely RAL 7016, plné bočné hliníkové polia, trojdielnu teleskopickú bránu, plnú skrytú bránku pri EAST-03 a hustý živý plot na zadnej hranici. Materiál, výška, mechanizmus aj druh výsadby čakajú na potvrdenie stavebníka.",
    date: "21. 8. 2026",
    kind: "DESIGN_PROPOSAL",
  },
  poolDesignProposal20260821: {
    id: "SRC-POOL-DESIGN-20260821",
    title: "Dizajnový návrh záhradného bazéna",
    detail:
      "Pôvodná vodná plocha 4,0 × 2,5 m bola revíziou stavebníka nahradená rozmerom 5,0 × 3,0 m. Dlhá hrana zostáva rovnobežná s terasou a južná hrana lemu je bez medzery napojená na jej severnú hranu; technológia, hĺbka a kolízia s pôvodnou trasou dažďovej kanalizácie vyžadujú realizačnú koordináciu.",
    date: "21. 8. 2026",
    kind: "DESIGN_PROPOSAL",
  },
  section: {
    id: "SRC-D11005",
    title: "D1.1.005 · Rez A–A",
    detail: "Sklon strechy 30° · hrebeň +5,560 m",
    date: "28. 4. 2026",
    page: 1,
    scale: "1:50",
    kind: "PROJECT_DESIGN",
  },
  rainwater: {
    id: "SRC-IO01",
    title: "IO 01 · Dažďová kanalizácia",
    detail: "Akumulačná nádrž 8,5 m³ · vsakovanie: správa 8,7 m³ / detail 6,1 m³ (konflikt)",
    date: "03/2026",
    page: 1,
    scale: "1:150",
    kind: "PROJECT_DESIGN",
  },
  sewer: {
    id: "SRC-IO02",
    title: "IO 02 · Splašková kanalizácia",
    detail: "Dočasná žumpa 11,0 m³ · budúce gravitačné pripojenie",
    date: "03/2026",
    page: 1,
    scale: "1:150",
    kind: "PROJECT_DESIGN",
  },
  water: {
    id: "SRC-IO03",
    title: "IO 03 · Prípojka vody",
    detail: "Vodovodná prípojka a vodomerná šachta 1,20 × 0,90 × 1,50 m",
    date: "03/2026",
    page: 1,
    scale: "1:150",
    kind: "PROJECT_DESIGN",
  },
  networkContext: {
    id: "SRC-KOORD-2025",
    title: "Koordinačná situácia lokality Z7",
    detail: "KOORDINAČNÍ SITUACE 2025.pdf · návrh lokality Z7, nie zameranie skutočného stavu",
    date: "výkres 08/2022 · súbor 2025",
    page: 1,
    scale: "1:500",
    kind: "PROVIDER_CONTEXT",
  },
  providerStatements: {
    id: "SRC-PROVIDER-STATEMENTS",
    title: "Vyjadrenia správcov sietí",
    detail: "GasNet, CETIN a EG.D: bez nimi prevádzkovaných vedení v záujmovom území. VaK: rad vybudoval developer, zatiaľ neprevzatý.",
    date: "12/2025–03/2026",
    kind: "PROVIDER_CONTEXT",
  },
  dmvsWater: {
    id: "SRC-DMVS-WATER",
    title: "ČÚZK DMVS · verejná technická infraštruktúra",
    detail: "Vodovod v komunikácii · objekt VT_023 · vlastník Obec Březí",
    date: "vložené 25. 2. 2026",
    kind: "CURRENT_REGISTER",
    href: "https://dmvs.cuzk.gov.cz/api/wms/dtm_ti_ver",
  },
  dmvsSewer: {
    id: "SRC-DMVS-SEWER",
    title: "ČÚZK DMVS · verejná technická infraštruktúra",
    detail: "Splašková stoka v komunikácii · objekt KS_086 · vlastník Obec Březí",
    date: "vložené 25. 2. 2026",
    kind: "CURRENT_REGISTER",
    href: "https://dmvs.cuzk.gov.cz/api/wms/dtm_ti_ver",
  },
  terrain: {
    id: "SRC-DMR5G",
    title: "ČÚZK · Digitálny model reliéfu 5G",
    detail: "184,087 m Bpv v referenčnom bode · historický reliéf pred výstavbou lokality",
    date: "snímkovanie 2009–2013",
    kind: "PROVIDER_CONTEXT",
    href: "https://ags.cuzk.gov.cz/arcgis2/rest/services/dmr5g/ImageServer",
  },
  asBuiltGap: {
    id: "SRC-ASBUILT-GAP",
    title: "Skutočné vyhotovenie sietí · chýbajúci podklad",
    detail: "Odkaz z e-mailu na geodetické zameranie expiroval; trasy na pozemku sú preto stále návrhové.",
    date: "stav 18. 8. 2026",
    kind: "UNRESOLVED_AS_BUILT",
  },
} as const satisfies Record<string, SourceRecord>;

const mmPoint = (xM: number, yM: number): Point2Mm => ({
  x: Math.round(xM * 1000),
  y: Math.round(yM * 1000),
});

export const SUBJECT_PARCEL_SJTSK_ORIGIN_MM = mmPoint(
  -606705.15,
  -1202056.66,
);

const parcel = (
  id: string,
  areaM2: number,
  ring: readonly (readonly [number, number])[],
  isSubject = false,
): CadastralParcel => ({
  id: `PARCEL-${id}`,
  nationalReference: `613908-${id}`,
  areaM2,
  sjtskRingMm: ring.map(([x, y]) => mmPoint(x, y)),
  sourceId: SOURCES.cadastre.id,
  isSubject,
});

export const CADASTRAL_PARCELS: readonly CadastralParcel[] = [
  {
    id: "PARCEL-6012/26",
    nationalReference: "613908-6012/26",
    areaM2: 753,
    sjtskRingMm: BREZI_6012_26_SJTSK_RING_MM.map(({ xMm, yMm }) => ({
      x: xMm,
      y: yMm,
    })),
    sourceId: SOURCES.cadastre.id,
    isSubject: true,
  },
  parcel("6012/24", 816, [
    [-606681.99, -1202098.13],
    [-606666.45, -1202080.6],
    [-606692.52, -1202057.49],
    [-606708.06, -1202075.02],
    [-606681.99, -1202098.13],
  ]),
  parcel("6012/25", 814, [
    [-606650.91, -1202063.06],
    [-606674.8, -1202041.91],
    [-606675.71, -1202041.36],
    [-606676.47, -1202041.21],
    [-606677.48, -1202041.29],
    [-606678.33, -1202041.65],
    [-606678.96, -1202042.2],
    [-606692.52, -1202057.49],
    [-606666.45, -1202080.6],
    [-606650.91, -1202063.06],
  ]),
  parcel("6012/27", 680, [
    [-606742.18, -1202065.3],
    [-606725.14, -1202079.2],
    [-606705.15, -1202056.66],
    [-606723.14, -1202041.98],
    [-606742.18, -1202065.3],
  ]),
  parcel("6013", 1839, [
    [-606529.6, -1202164.11],
    [-606518.73, -1202172.88],
    [-606490.99, -1202188.85],
    [-606485.77, -1202182.22],
    [-606500.05, -1202175.52],
    [-606517.93, -1202166.06],
    [-606534.36, -1202151.76],
    [-606539.6, -1202147.1],
    [-606633.38, -1202063.72],
    [-606695.81, -1202008.62],
    [-606699.38, -1202005.45],
    [-606710.34, -1201996.13],
    [-606716.9, -1201990.13],
    [-606723.85, -1201999.41],
    [-606716.08, -1201999.1],
    [-606703.32, -1202009.69],
    [-606699.52, -1202013.05],
    [-606617.1, -1202086.17],
    [-606534.68, -1202159.29],
    [-606529.6, -1202164.11],
  ]),
  parcel("6014", 2312, [
    [-606746.58, -1202070.69],
    [-606742.18, -1202065.3],
    [-606723.14, -1202041.98],
    [-606702.85, -1202017.13],
    [-606699.52, -1202013.05],
    [-606703.32, -1202009.69],
    [-606721.53, -1202031.82],
    [-606775.17, -1202096.82],
    [-606822.29, -1202154.83],
    [-606871.88, -1202213.67],
    [-606879, -1202221.79],
    [-606923.72, -1202277.39],
    [-606940.84, -1202297.5],
    [-606955.68, -1202315.64],
    [-606973.62, -1202338.64],
    [-606968.15, -1202340.34],
    [-606906.81, -1202265.13],
    [-606887.03, -1202241.13],
    [-606857.06, -1202204.75],
    [-606837.9, -1202181.5],
    [-606826.7, -1202167.91],
    [-606818.75, -1202158.26],
    [-606799.62, -1202135.05],
    [-606780.45, -1202111.79],
    [-606761.3, -1202088.55],
    [-606746.58, -1202070.69],
  ]),
] as const;

// The local scene frame follows the road-facing cadastral edge. Raw legal
// geometry remains untouched above; this projection is a derived render recipe.
const ROAD_EDGE_END_MM = mmPoint(-606686.45, -1202035.56);
const edgeDx = ROAD_EDGE_END_MM.x - SUBJECT_PARCEL_SJTSK_ORIGIN_MM.x;
const edgeDy = ROAD_EDGE_END_MM.y - SUBJECT_PARCEL_SJTSK_ORIGIN_MM.y;
const edgeLength = Math.hypot(edgeDx, edgeDy);
export const SITE_AXIS = Object.freeze({
  ux: edgeDx / edgeLength,
  uy: edgeDy / edgeLength,
  vx: -edgeDy / edgeLength,
  vy: edgeDx / edgeLength,
});

export function sjtskToLocalMm(point: Point2Mm): Point2Mm {
  const dx = point.x - SUBJECT_PARCEL_SJTSK_ORIGIN_MM.x;
  const dy = point.y - SUBJECT_PARCEL_SJTSK_ORIGIN_MM.y;
  return {
    x: Math.round(dx * SITE_AXIS.ux + dy * SITE_AXIS.uy),
    y: Math.round(dx * SITE_AXIS.vx + dy * SITE_AXIS.vy),
  };
}

/** Visible rainwater downpipe hung on a Z facade (xMm along it) or an X facade (yMm along it). */
export type RainwaterDownpipe =
  | {
      readonly id: string;
      readonly xMm: number;
      readonly faceYmm: number;
      readonly sourceRouteId: string;
      readonly certainty: "VISUAL_INFERENCE";
    }
  | {
      readonly id: string;
      readonly yMm: number;
      readonly faceXmm: number;
      readonly sourceRouteId: string;
      readonly certainty: "VISUAL_INFERENCE";
    };

export const HOUSE = Object.freeze({
  id: "HOUSE-DESIGN",
  // D1.1.002 is the active plan geometry. Its national-grid placement is an
  // explicit no-reflection alignment to the georeferenced C3 right/front/top
  // anchors. Compared with C3 only the garage (low-X) end grows by 800 mm.
  originMm: { x: 6440, y: 3000 } satisfies Point2Mm,
  lowerBar: { widthMm: 21600, depthMm: 8200 },
  wing: { xMm: 14600, yMm: 8200, widthMm: 7000, depthMm: 10835 },
  footprintMm: [
    { x: 6440, y: 3000 },
    { x: 28040, y: 3000 },
    { x: 28040, y: 22035 },
    { x: 21040, y: 22035 },
    { x: 21040, y: 11200 },
    { x: 6440, y: 11200 },
    { x: 6440, y: 3000 },
  ] as const satisfies readonly Point2Mm[],
  maximumDepthMm: 19035,
  derivedFootprintAreaM2: 252.965,
  floorAreaM2: 175.15,
  terraceAreaM2: 84.35,
  eavesElevationMm: 3125,
  ridgeElevationMm: 5560,
  chimneyElevationMm: 6160,
  chimneys: [
    {
      id: "CHIMNEY-LIVING-103",
      // 22. 8. 2026: the flue is the 347 × 500 masonry pier on the west wall
      // of 1.03, right beside the terrace door; the stove leans on that wall.
      centerMm: { x: 21716, y: 14801 } satisfies Point2Mm,
      planMm: { widthMm: 346, depthMm: 500 },
      previousCenterMm: { x: 24190, y: 12700 } satisfies Point2Mm,
      designCenterMm: { x: 24190, y: 11700 } satisfies Point2Mm,
      gardenShiftMm: 1000,
      zone: "MAIN_LIVING_AND_KITCHEN_1_03",
      baseSourceId: SOURCES.roofPlan.id,
      previousSourceId: SOURCES.clientRevision20260821.id,
      sourceId: SOURCES.clientRevision20260822.id,
    },
  ] as const,
  removedChimneys: [
    {
      id: "CHIMNEY-ROOM-109",
      centerMm: { x: 17640, y: 7250 } satisfies Point2Mm,
      zone: "ROOM_1_09_ROOF_ZONE",
      sourceId: SOURCES.clientRevision20260821.id,
    },
  ] as const,
  roofPitchDeg: 30,
  roof: {
    sourceId: SOURCES.roofPlan.id,
    topology: "JOINED_CROSS_GABLE",
    mainPlanLengthMm: 21600,
    mainHalfSpanMm: 4100,
    mainSlopeLengthMm: 4735,
    wingOverallPlanLengthMm: 19035,
    wingExtensionPlanLengthMm: 10835,
    documentedWingRoofOverallLengthMm: 19085,
    wingEndOverhangMm: 50,
    wingHalfSpanMm: 3500,
    wingPitchDeg: 34,
  },
  facades: {
    front: {
      faceYmm: 3000,
      finish: "OFF_WHITE_ETICS",
      garageDoor: {
        id: "GARAGE-DOOR",
        startXmm: 6940,
        widthMm: 3300,
        heightMm: 2400,
        sillMm: 0,
        access: "DIRECT_FROM_STREET",
        sourceId: SOURCES.clientRevision20260821.id,
      },
      openings: [
        {
          id: "FRONT-02",
          startXmm: 11715,
          widthMm: 1250,
          heightMm: 750,
          sillMm: 1750,
        },
        {
          id: "FRONT-03",
          startXmm: 14965,
          widthMm: 750,
          heightMm: 750,
          sillMm: 1750,
        },
        {
          id: "FRONT-04",
          startXmm: 17140,
          widthMm: 800,
          heightMm: 1600,
          sillMm: 900,
        },
        {
          id: "FRONT-05",
          startXmm: 19740,
          widthMm: 800,
          heightMm: 1600,
          sillMm: 900,
        },
        {
          id: "FRONT-ENTRY",
          startXmm: 21540,
          widthMm: 1250,
          heightMm: 2250,
          sillMm: 0,
        },
        {
          id: "FRONT-07",
          startXmm: 24790,
          widthMm: 2000,
          heightMm: 1600,
          sillMm: 900,
        },
      ],
    },
    garden: {
      faceYmm: 11200,
      cladding: "OFF_WHITE_ETICS_WITH_LOCAL_LARCH_FEATURE",
      larchFeature: {
        startXmm: 7440,
        widthMm: 1850,
        heightMm: 2400,
        certainty: "INFERRED_FROM_LATER_PLAN",
      },
      openings: [
        { id: "GARDEN-01", startXmm: 9290, widthMm: 1250, heightMm: 2400, sillMm: 0 },
        { id: "GARDEN-02", startXmm: 11840, widthMm: 2500, heightMm: 2400, sillMm: 0 },
        { id: "GARDEN-03", startXmm: 15840, widthMm: 2000, heightMm: 2400, sillMm: 0 },
      ],
    },
    east: {
      faceXmm: 28040,
      finish: "OFF_WHITE_ETICS",
      openings: [
        {
          id: "EAST-01",
          startYmm: 5025,
          widthMm: 1000,
          heightMm: 1600,
          sillMm: 900,
        },
        {
          id: "EAST-02",
          startYmm: 6600,
          widthMm: 600,
          heightMm: 750,
          sillMm: 1750,
        },
        {
          id: "EAST-03",
          startYmm: 9650,
          widthMm: 1000,
          heightMm: 2250,
          sillMm: 0,
        },
        {
          id: "EAST-04",
          startYmm: 12700,
          widthMm: 1000,
          heightMm: 1600,
          sillMm: 900,
        },
      ],
    },
    wingEnd: {
      faceYmm: 22035,
      startXmm: 21040,
      widthMm: 7000,
      cladding: "NATURAL_VERTICAL_LARCH",
      opening: {
        id: "WING-END-01",
        startXmm: 21590,
        widthMm: 2400,
        heightMm: 2400,
        sillMm: 0,
        roughOpeningStartXmm: 21540,
        roughOpeningWidthMm: 2500,
      },
    },
    west: {
      faceXmm: 6440,
      finish: "OFF_WHITE_ETICS",
      loggiaOpening: {
        id: "WEST-01",
        startYmm: 9300,
        widthMm: 1400,
        heightMm: 2400,
        sillMm: 0,
      },
    },
    wingWest: {
      faceXmm: 21040,
      finish: "OFF_WHITE_ETICS",
      wallStartYmm: 11200,
      wallEndYmm: 19535,
      opening: {
        id: "WING-WEST-01",
        startYmm: 11550,
        widthMm: 2250,
        heightMm: 2400,
        sillMm: 0,
      },
    },
  },
  // Both covered porches come straight from the D1.1.002 vector geometry: the
  // wing gable porch (TERASA 16,45 m²) has its glazed wall recessed 2 500 mm
  // behind the gable plane, and the garden loggia (part of TERASA 34,80 m²)
  // sits 2 953 mm behind the garden facade line.
  porches: {
    wingEnd: {
      id: "PORCH-WING-END",
      areaM2: 16.45,
      frontYmm: 22035,
      glazingFaceYmm: 19535,
      clearDepthMm: 2500,
      // 22. 8. 2026: the whole end wall of 1.03 toward the porch is a glazed
      // curtain wall from the floor up to the vaulted ceiling line, mullions
      // every 1 250 mm, with a single hinged door leaf; no solid wall.
      glazing: {
        startXmm: 21540,
        widthMm: 6000,
        heightMm: 2750,
        sillMm: 0,
        gable: "GLAZED_TO_VAULT",
        mullionXmm: [21540, 22790, 24040, 25040, 26290, 27540],
        transomMm: 2750,
        sourceId: SOURCES.clientRevision20260822.id,
      },
      door: { startXmm: 24040, widthMm: 1000, heightMm: 2400, hinge: "WEST" },
      previousGlazing: { startXmm: 21540, widthMm: 2500, heightMm: 2400, sillMm: 0 },
      previousBackWall: { startXmm: 24040, endXmm: 27540, cladding: "LARCH" },
      eastWallInnerXmm: 27540,
      cornerPillar: { startXmm: 21040, startYmm: 21535, sizeMm: 500 },
      westOpening: { startYmm: 19535, endYmm: 21535, heightMm: 3125 },
      // P04 portal: both white supports (the 500 × 500 corner pillar and the
      // 500 mm east wall end) are continued above the wall crown with a
      // sloped head that meets the boarded roof soffit, and the white rake
      // boards of the gable sit in the same plane as the supports (their
      // back face flush with the pillar front at 22 035, the outer face on
      // the 50 mm roof overhang at 22 085).
      portalFrame: {
        supportsMm: [
          { id: "PORCH-SUPPORT-WEST", startXmm: 21040, endXmm: 21540, startYmm: 21535, endYmm: 22035 },
          { id: "PORCH-SUPPORT-EAST", startXmm: 27540, endXmm: 28040, startYmm: 19535, endYmm: 22035 },
        ],
        rakeBackFaceYmm: 22035,
        rakeFrontFaceYmm: 22105,
        rakeHeightMm: 180,
      },
      // The porch is open to the roof: its ceiling follows the two wing roof
      // planes up to the ridge instead of a flat soffit, and the larch gable
      // wall sits on the recessed plane so the front stays an open frame.
      openToRoof: true,
      ceilingClearanceMm: 60,
      gablePlaneYmm: 19535,
      portal: "P04 · ocelový rám krovu HEA160",
    },
    gardenLoggia: {
      id: "PORCH-GARDEN-LOGGIA",
      faceYmm: 11200,
      backFaceYmm: 8247,
      openingStartXmm: 7440,
      openingEndXmm: 10640,
      cornerPier: { startXmm: 6440, endXmm: 7440, startYmm: 10700, endYmm: 11200 },
      backLarch: { startXmm: 7236, endXmm: 9086 },
      backDoor: { id: "LOGGIA-DOOR", startXmm: 9086, widthMm: 1250, heightMm: 2400, sillMm: 0 },
      eastInnerXmm: 10640,
      soffitElevationMm: 2750,
      beam: "P01 · ŽB věnec / 2×I180",
    },
  },
  photovoltaics: {
    moduleCount: 6,
    wattsPerModule: 405,
    layout: "2x3_CLIENT_REVISION",
    roofFace: "WING_INNER",
    facing: "COURTYARD",
    placement: "GARDENWARD_ON_WING_INNER",
    towardTerraceId: "TERR-D1-WING",
    previousFirstModuleCenterMm: { x: 21820, y: 12600 } satisfies Point2Mm,
    // 2 000 mm client shift (21. 8.) plus 1 100 mm (one column step) to clear
    // the relocated flue on the wing inner roof plane (22. 8.).
    gardenShiftMm: 3100,
    chimneyClearanceShiftMm: 1100,
    rows: 2,
    columns: 3,
    firstModuleCenterMm: { x: 21820, y: 15700 } satisfies Point2Mm,
    rowStepMm: { x: 1550, y: 0 } satisfies Point2Mm,
    columnStepMm: { x: 0, y: 1100 } satisfies Point2Mm,
    moduleSlopeLengthMm: 1720,
    moduleRidgeWidthMm: 1020,
    sourceId: SOURCES.clientRevision20260821.id,
  },
  rainwaterDownpipes: [
    {
      id: "DS-01",
      xMm: 7600,
      faceYmm: 11200,
      sourceRouteId: "UTIL-RAIN-SOUTH",
      certainty: "VISUAL_INFERENCE",
    },
    // The wing roof is a gable over the porch: its gutters run along the two
    // long eaves (x = 21 040 and x = 28 040), not along the open gable front.
    // The visible pipe therefore hangs on the east eave next to the porch
    // corner instead of standing as a loose post in the open porch frame.
    {
      id: "DS-02",
      yMm: 21700,
      faceXmm: 28040,
      sourceRouteId: "UTIL-RAIN-NORTH",
      certainty: "VISUAL_INFERENCE",
    },
  ] as const satisfies readonly RainwaterDownpipe[],
  datumElevationM: 184,
  orientation: {
    sourceId: SOURCES.floorPlan.id,
    reflection: "NONE",
    frontEdge: "LOCAL_Y_MIN",
    garageVolumeSide: "LOCAL_X_MIN",
    garageAccessSide: "LOCAL_Y_MIN",
    wingSide: "LOCAL_X_MAX",
  },
  coordinationRevision: {
    documentDate: "1. 5. 2026",
    widthMm: 20800,
    depthMm: 19044,
    documentedBuiltUpAreaM2: 246.4,
    placementStatus: "GEOREFERENCED_C3",
  },
  detailedRevision: {
    documentDate: "11. 5. 2026",
    widthMm: 21600,
    depthMm: 19035,
    areaM2: 252.965,
    active: true,
    placementStatus: "INFERRED_ALIGNMENT",
    alignmentNote: "Bez zrkadlenia zarovnané na pravú hranu, zalomenie a hornú hranu C3; garážový koniec sa predlžuje o 800 mm.",
  },
  sourceIds: [
    SOURCES.floorPlan.id,
    SOURCES.roofPlan.id,
    SOURCES.coordination.id,
    SOURCES.section.id,
    SOURCES.clientRevision20260821.id,
  ],
});

// The subject is the end/corner parcel: road parcel 6012/1 meets both its
// straight 160–136 frontage and the rounded 136–…–130 edge. The road fragments
// below are clipped directly from ČÚZK feature CP.94487856010. The 3.10 m front
// reserve between the legal boundary and the C3 access endpoints is rendered
// separately from the asphalt so the entrances no longer appear painted over
// the carriageway. The exact as-built kerb profile is still not surveyed.
export const ROAD_CONTEXT = Object.freeze({
  id: "ROAD-6012-1",
  featureId: "CP.94487856010",
  nationalReference: "613908-6012/1",
  registeredAreaM2: 10_647,
  observedAt: "2026-08-21",
  sourceIds: [SOURCES.cadastre.id, SOURCES.coordination.id],
  legalBoundaryStatus: "CURRENT_REGISTER",
  surfaceEnvelopeStatus: "CURRENT_REGISTER_CLIPPED_CONTEXT",
  pavedSurfaceStatus: "C3_DERIVED_NOT_AS_BUILT_SURVEY",
  touchedBoundarySegments: ["160–136", "136–135–134–133–132–131–130"],
  frontAsphaltEdgeYmm: -3_104,
  frontParcelEdgeMm: [
    { x: -15_670, y: 5 },
    { x: 0, y: 0 },
    { x: 28_194, y: 0 },
  ] as const satisfies readonly Point2Mm[],
  frontOppositeParcelEdgeMm: [
    { x: -15_670, y: -10_000 },
    { x: 7_756, y: -10_003 },
    { x: 28_193, y: -10_009 },
  ] as const satisfies readonly Point2Mm[],
  frontReservePolygonMm: [
    { x: -15_670, y: 5 },
    { x: 0, y: 0 },
    { x: 28_194, y: 0 },
    { x: 28_194, y: -3_104 },
    { x: -15_670, y: -3_104 },
    { x: -15_670, y: 5 },
  ] as const satisfies readonly Point2Mm[],
  frontReserveSurfacePolygonsMm: [
    [
      { x: -15_670, y: 5 },
      { x: 0, y: 0 },
      { x: 6_490, y: 0 },
      { x: 6_490, y: -3_104 },
      { x: -15_670, y: -3_104 },
      { x: -15_670, y: 5 },
    ],
    [
      { x: 10_690, y: 0 },
      { x: 21_415, y: 0 },
      { x: 21_415, y: -3_104 },
      { x: 10_690, y: -3_104 },
      { x: 10_690, y: 0 },
    ],
    [
      { x: 22_915, y: 0 },
      { x: 28_194, y: 0 },
      { x: 28_194, y: -3_104 },
      { x: 22_915, y: -3_104 },
      { x: 22_915, y: 0 },
    ],
  ] as const satisfies readonly (readonly Point2Mm[])[],
  frontagePolygonMm: [
    { x: -15_670, y: -3_104 },
    { x: 28_194, y: -3_104 },
    { x: 28_193, y: -10_009 },
    { x: 7_756, y: -10_003 },
    { x: -15_670, y: -10_000 },
    { x: -15_670, y: -3_104 },
  ] as const satisfies readonly Point2Mm[],
  cornerParcelEdgeMm: [
    { x: 28_194, y: 0 },
    { x: 28_922, y: 98 },
    { x: 29_721, y: 418 },
    { x: 30_613, y: 1_235 },
    { x: 31_081, y: 2_185 },
    { x: 31_187, y: 3_000 },
    { x: 31_109, y: 24_497 },
  ] as const satisfies readonly Point2Mm[],
  sideAsphaltOffsetMm: 3_104,
  cornerAsphaltEdgeMm: [
    { x: 28_194, y: -3_104 },
    { x: 29_677, y: -2_913 },
    { x: 31_301, y: -2_254 },
    { x: 33_120, y: -595 },
    { x: 34_068, y: 1_342 },
    { x: 34_291, y: 3_000 },
    { x: 34_213, y: 24_497 },
  ] as const satisfies readonly Point2Mm[],
  cornerReservePolygonMm: [
    { x: 28_194, y: 0 },
    { x: 28_922, y: 98 },
    { x: 29_721, y: 418 },
    { x: 30_613, y: 1_235 },
    { x: 31_081, y: 2_185 },
    { x: 31_187, y: 3_000 },
    { x: 31_109, y: 24_497 },
    { x: 34_213, y: 24_497 },
    { x: 34_291, y: 3_000 },
    { x: 34_068, y: 1_342 },
    { x: 33_120, y: -595 },
    { x: 31_301, y: -2_254 },
    { x: 29_677, y: -2_913 },
    { x: 28_194, y: -3_104 },
    { x: 28_194, y: 0 },
  ] as const satisfies readonly Point2Mm[],
  cornerReserveSurfacePolygonsMm: [
    [
      { x: 28_194, y: 0 },
      { x: 28_922, y: 98 },
      { x: 29_721, y: 418 },
      { x: 30_613, y: 1_235 },
      { x: 31_081, y: 2_185 },
      { x: 31_187, y: 3_000 },
      { x: 31_164, y: 9_250 },
      { x: 34_268, y: 9_250 },
      { x: 34_291, y: 3_000 },
      { x: 34_068, y: 1_342 },
      { x: 33_120, y: -595 },
      { x: 31_301, y: -2_254 },
      { x: 29_677, y: -2_913 },
      { x: 28_194, y: -3_104 },
      { x: 28_194, y: 0 },
    ],
    [
      { x: 31_158, y: 11_050 },
      { x: 31_109, y: 24_497 },
      { x: 34_213, y: 24_497 },
      { x: 34_262, y: 11_050 },
      { x: 31_158, y: 11_050 },
    ],
  ] as const satisfies readonly (readonly Point2Mm[])[],
  cornerOuterEdgeMm: [
    { x: 36_371, y: 24_711 },
    { x: 36_352, y: -12_930 },
  ] as const satisfies readonly Point2Mm[],
  cornerPolygonMm: [
    { x: 28194, y: 0 },
    { x: 28922, y: 98 },
    { x: 29721, y: 418 },
    { x: 30613, y: 1235 },
    { x: 31081, y: 2185 },
    { x: 31187, y: 3000 },
    { x: 31109, y: 24497 },
    { x: 36371, y: 24711 },
    { x: 36352, y: -12930 },
    { x: 31169, y: -12930 },
    { x: 30977, y: -11885 },
    { x: 30585, y: -11216 },
    { x: 29855, y: -10514 },
    { x: 29022, y: -10116 },
    { x: 28193, y: -10009 },
    { x: 28194, y: 0 },
  ] as const satisfies readonly Point2Mm[],
  cornerCarriagewayPolygonMm: [
    { x: 28_194, y: -3_104 },
    { x: 29_677, y: -2_913 },
    { x: 31_301, y: -2_254 },
    { x: 33_120, y: -595 },
    { x: 34_068, y: 1_342 },
    { x: 34_291, y: 3_000 },
    { x: 34_213, y: 24_497 },
    { x: 36_371, y: 24_711 },
    { x: 36_352, y: -12_930 },
    { x: 31_169, y: -12_930 },
    { x: 30_977, y: -11_885 },
    { x: 30_585, y: -11_216 },
    { x: 29_855, y: -10_514 },
    { x: 29_022, y: -10_116 },
    { x: 28_193, y: -10_009 },
    { x: 28_194, y: -3_104 },
  ] as const satisfies readonly Point2Mm[],
});

const fp = (
  id: string,
  label: string,
  startMm: Point2Mm,
  endMm: Point2Mm,
  widthMm: number,
  heightMm: number,
  baseElevationMm: number,
): FoundationStrip => ({
  id,
  label,
  startMm,
  endMm,
  widthMm,
  heightMm,
  baseElevationMm,
  sourceId: SOURCES.foundation.id,
});

// D1.1.001 is a later, larger foundation revision without its own national-grid
// tie. Aligning its right/top outer edges to C3 is an explicit model inference.
const OX = 6140;
const OY = 2653;
export const FOUNDATIONS: readonly FoundationStrip[] = [
  fp("F-01", "Juhovýchodný obvodový pás", { x: OX, y: OY }, { x: OX + 21900, y: OY }, 800, 750, -1150),
  fp("F-02", "Severovýchodný obvodový pás", { x: OX + 21900, y: OY }, { x: OX + 21900, y: OY + 19385 }, 800, 750, -1150),
  fp("F-03", "Severný obvodový pás", { x: OX + 14600, y: OY + 19385 }, { x: OX + 21900, y: OY + 19385 }, 800, 750, -1150),
  fp("F-04", "Západný pás krídla", { x: OX + 14600, y: OY + 8200 }, { x: OX + 14600, y: OY + 19385 }, 800, 750, -1150),
  fp("F-05", "Horný pás hlavného traktu", { x: OX, y: OY + 8200 }, { x: OX + 14600, y: OY + 8200 }, 800, 750, -1150),
  fp("F-06", "Juhozápadný obvodový pás", { x: OX, y: OY }, { x: OX, y: OY + 8200 }, 800, 750, -1150),
  fp("F-07", "Vnútorný pás · garáž", { x: OX + 7250, y: OY }, { x: OX + 7250, y: OY + 8200 }, 600, 500, -900),
  fp("F-08", "Vnútorný pás · jadro", { x: OX + 10250, y: OY }, { x: OX + 10250, y: OY + 8200 }, 600, 500, -900),
  fp("F-09", "Vnútorný pás · denná zóna", { x: OX + 14800, y: OY }, { x: OX + 14800, y: OY + 8200 }, 600, 750, -1150),
  fp("F-10", "Vnútorný pás · krídlo", { x: OX + 18450, y: OY }, { x: OX + 18450, y: OY + 8200 }, 500, 500, -900),
  fp("F-11", "Priečny pás · technické jadro", { x: OX + 7250, y: OY + 4100 }, { x: OX + 14800, y: OY + 4100 }, 600, 500, -900),
] as const;

export const SITE_SURFACES = Object.freeze({
  timberTerrace: {
    id: "SITE-TERRACE",
    areaM2: 53,
    polygonMm: [
      { x: 21035, y: 22038 },
      { x: 21041, y: 18649 },
      { x: 21036, y: 11201 },
      { x: 19723, y: 11202 },
      { x: 8921, y: 11199 },
      { x: 7236, y: 11199 },
      { x: 7237, y: 13100 },
      { x: 18038, y: 13103 },
      { x: 18037, y: 14584 },
      { x: 18037, y: 22039 },
      { x: 21035, y: 22038 },
    ] as const satisfies readonly Point2Mm[],
  },
  driveway: {
    id: "SITE-DRIVEWAY",
    areaM2: 25.637,
    sourceAreaM2: 48.603,
    placementStatus: "CLIENT_REVISION_WITH_C3_DERIVED_STREET_EDGE",
    sourceId: SOURCES.clientRevision20260821.id,
    sourceIds: [
      SOURCES.clientRevision20260821.id,
      SOURCES.clientExteriorRevision20260821.id,
      SOURCES.coordination.id,
      SOURCES.floorPlan.id,
    ],
    accessOpeningId: "GARAGE-DOOR",
    streetConnection: {
      cadastralBoundaryYmm: 0,
      asphaltEdgeYmm: -3_104,
      houseFaceYmm: 3_000,
      privateAreaM2: 12.6,
      roadReserveAreaM2: 13.037,
    },
    polygonMm: [
      { x: 6490, y: 3000 },
      { x: 10690, y: 3000 },
      { x: 10690, y: -3104 },
      { x: 6490, y: -3104 },
      { x: 6490, y: 3000 },
    ] as const satisfies readonly Point2Mm[],
  },
  supersededSideDriveway: {
    id: "SITE-DRIVEWAY-SIDE-SUPERSEDED",
    areaM2: 40.855,
    placementStatus: "SUPERSEDED_BY_CLIENT_DIRECT_GARAGE_ACCESS",
    sourceId: SOURCES.coordination.id,
    supersededById: "SITE-DRIVEWAY",
    polygonMm: [
      { x: 6440, y: 6970 },
      { x: 6440, y: 632 },
      { x: 6440, y: -3099 },
      { x: 2242, y: -3104 },
      { x: 2235, y: 2546 },
      { x: 2237, y: 6270 },
      { x: 6440, y: 6970 },
    ] as const satisfies readonly Point2Mm[],
  },
  entry: {
    id: "SITE-ENTRY",
    areaM2: 9.156,
    accessOpeningId: "FRONT-ENTRY",
    placementStatus: "DESIGN_PROPOSAL_CENTERED_ON_MAIN_ENTRY",
    sourceIds: [
      SOURCES.clientExteriorRevision20260821.id,
      SOURCES.coordination.id,
      SOURCES.floorPlan.id,
    ],
    streetConnection: {
      cadastralBoundaryYmm: 0,
      asphaltEdgeYmm: -3_104,
      houseFaceYmm: 3_000,
      privateAreaM2: 4.5,
      roadReserveAreaM2: 4.656,
    },
    polygonMm: [
      { x: 22_915, y: 3_000 },
      { x: 22_915, y: -3_104 },
      { x: 21_415, y: -3_104 },
      { x: 21_415, y: 3_000 },
      { x: 22_915, y: 3_000 },
    ] as const satisfies readonly Point2Mm[],
    sourceEnvelopePolygonMm: [
      { x: 23_343, y: 2_995 },
      { x: 23_337, y: 513 },
      { x: 23_342, y: -3_080 },
      { x: 21_141, y: -3_085 },
      { x: 21_141, y: -596 },
      { x: 21_136, y: 2_996 },
      { x: 23_343, y: 2_995 },
    ] as const satisfies readonly Point2Mm[],
  },
  sideEntryApproach: {
    id: "SITE-SIDE-ENTRY-APPROACH",
    areaM2: 11.202,
    accessOpeningId: "EAST-03",
    placementStatus: "CLIENT_REVISION_ALIGNED_TO_SIDE_DOOR",
    sourceSurfaceId: "SITE-BIN-PAD",
    sourceId: SOURCES.clientRevision20260821.id,
    streetConnection: {
      sideAsphaltOffsetMm: 3_104,
      privateAreaM2: 5.578,
      roadReserveAreaM2: 5.624,
    },
    polygonMm: [
      { x: 34262, y: 11049 },
      { x: 34268, y: 9250 },
      { x: 29633, y: 9251 },
      { x: 28038, y: 9251 },
      { x: 28038, y: 11050 },
      { x: 29543, y: 11050 },
      { x: 34262, y: 11049 },
    ] as const satisfies readonly Point2Mm[],
    privatePolygonMm: [
      { x: 31157, y: 11049 },
      { x: 31163, y: 9250 },
      { x: 29633, y: 9251 },
      { x: 28038, y: 9251 },
      { x: 28038, y: 11050 },
      { x: 29543, y: 11050 },
      { x: 31157, y: 11049 },
    ] as const satisfies readonly Point2Mm[],
    roadReservePolygonMm: [
      { x: 34262, y: 11049 },
      { x: 34268, y: 9250 },
      { x: 31138, y: 9250 },
      { x: 31139, y: 11049 },
      { x: 34262, y: 11049 },
    ] as const satisfies readonly Point2Mm[],
  },
  supersededBinPad: {
    id: "SITE-BIN-PAD",
    areaM2: 5.578,
    placementStatus: "SUPERSEDED_BY_CLIENT_SIDE_ENTRY_ALIGNMENT",
    sourceId: SOURCES.coordination.id,
    polygonMm: [
      { x: 31139, y: 12247 },
      { x: 31138, y: 10448 },
      { x: 29633, y: 10449 },
      { x: 28038, y: 10449 },
      { x: 28038, y: 12248 },
      { x: 29543, y: 12248 },
      { x: 31139, y: 12247 },
    ] as const satisfies readonly Point2Mm[],
  },
});

export interface FenceRunMm {
  readonly id: string;
  readonly label: string;
  readonly pointsMm: readonly Point2Mm[];
  readonly alignment: "CLIENT_FRONT_DATUM" | "CADASTRAL_BOUNDARY";
}

export interface PhysicalFenceRunMm {
  readonly id: string;
  readonly label: string;
  readonly pointsMm: readonly Point2Mm[];
  readonly referenceRunIds: readonly string[];
  readonly treatment:
    | "SLATTED_ALUMINIUM"
    | "SOLID_ALUMINIUM"
    | "LIVING_HEDGE";
  readonly status: "DESIGN_PROPOSAL_REQUIRES_SURVEY_AND_CLIENT_CONFIRMATION";
}

const fenceRun = (
  id: string,
  label: string,
  pointsMm: readonly Point2Mm[],
  alignment: FenceRunMm["alignment"],
): FenceRunMm => ({ id, label, pointsMm, alignment });

const physicalFenceRun = (
  id: string,
  label: string,
  pointsMm: readonly Point2Mm[],
  referenceRunIds: readonly string[],
  treatment: PhysicalFenceRunMm["treatment"],
): PhysicalFenceRunMm => ({
  id,
  label,
  pointsMm,
  referenceRunIds,
  treatment,
  status: "DESIGN_PROPOSAL_REQUIRES_SURVEY_AND_CLIENT_CONFIRMATION",
});

interface FenceLineMm {
  readonly start: Point2Mm;
  readonly end: Point2Mm;
}

const offsetFenceLine = (
  start: Point2Mm,
  end: Point2Mm,
  insetMm: number,
): FenceLineMm => {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const lengthMm = Math.hypot(dx, dy);
  const offset = { x: (-dy / lengthMm) * insetMm, y: (dx / lengthMm) * insetMm };
  return {
    start: { x: start.x + offset.x, y: start.y + offset.y },
    end: { x: end.x + offset.x, y: end.y + offset.y },
  };
};

const intersectFenceLines = (
  first: FenceLineMm,
  second: FenceLineMm,
): Point2Mm => {
  const firstDx = first.end.x - first.start.x;
  const firstDy = first.end.y - first.start.y;
  const secondDx = second.end.x - second.start.x;
  const secondDy = second.end.y - second.start.y;
  const denominator = firstDx * secondDy - firstDy * secondDx;
  if (Math.abs(denominator) < 1e-9) {
    throw new Error("Odsadené línie plotu nemajú jednoznačný priesečník.");
  }
  const originDx = second.start.x - first.start.x;
  const originDy = second.start.y - first.start.y;
  const ratio = (originDx * secondDy - originDy * secondDx) / denominator;
  return {
    x: first.start.x + firstDx * ratio,
    y: first.start.y + firstDy * ratio,
  };
};

const fencePointAlong = (
  start: Point2Mm,
  end: Point2Mm,
  distanceMm: number,
): Point2Mm => {
  const lengthMm = Math.hypot(end.x - start.x, end.y - start.y);
  return {
    x: start.x + ((end.x - start.x) / lengthMm) * distanceMm,
    y: start.y + ((end.y - start.y) / lengthMm) * distanceMm,
  };
};

// The markup encloses the private garden at the front-facade datum y=3000.
// It deliberately does not fence the cadastral street frontage y=0, so the
// revised direct garage driveway remains open. The west datum point is the
// rounded intersection of the cadastral edge (0,0)–(-946,23200) with y=3000.
const FENCE_WEST_DATUM = { x: -122, y: 3000 } as const satisfies Point2Mm;
const FENCE_EAST_SIDE_GATE_START = {
  x: 31163,
  y: 9550,
} as const satisfies Point2Mm;
const FENCE_EAST_SIDE_GATE_END = {
  x: 31159,
  y: 10750,
} as const satisfies Point2Mm;
const FENCE_PHYSICAL_BOUNDARY_INSET_MM = 100;
const FENCE_FRONT_LEFT_LINE: FenceLineMm = {
  start: FENCE_WEST_DATUM,
  end: { x: 2235, y: 3000 },
};
const FENCE_FRONT_RIGHT_LINE: FenceLineMm = {
  start: { x: 28040, y: 3000 },
  end: { x: 31187, y: 3000 },
};
const FENCE_EAST_PHYSICAL_LINE = offsetFenceLine(
  { x: 31187, y: 3000 },
  { x: 31109, y: 24497 },
  FENCE_PHYSICAL_BOUNDARY_INSET_MM,
);
const FENCE_REAR_PHYSICAL_LINE = offsetFenceLine(
  { x: 31109, y: 24497 },
  { x: -946, y: 23200 },
  FENCE_PHYSICAL_BOUNDARY_INSET_MM,
);
const FENCE_WEST_PHYSICAL_LINE = offsetFenceLine(
  { x: -946, y: 23200 },
  FENCE_WEST_DATUM,
  FENCE_PHYSICAL_BOUNDARY_INSET_MM,
);
const FENCE_MITER_FRONT_EAST = intersectFenceLines(
  FENCE_FRONT_RIGHT_LINE,
  FENCE_EAST_PHYSICAL_LINE,
);
const FENCE_MITER_EAST_REAR = intersectFenceLines(
  FENCE_EAST_PHYSICAL_LINE,
  FENCE_REAR_PHYSICAL_LINE,
);
const FENCE_MITER_REAR_WEST = intersectFenceLines(
  FENCE_REAR_PHYSICAL_LINE,
  FENCE_WEST_PHYSICAL_LINE,
);
const FENCE_MITER_WEST_FRONT = intersectFenceLines(
  FENCE_WEST_PHYSICAL_LINE,
  FENCE_FRONT_LEFT_LINE,
);
const FENCE_EAST_OFFSET = {
  x: FENCE_EAST_PHYSICAL_LINE.start.x - 31187,
  y: FENCE_EAST_PHYSICAL_LINE.start.y - 3000,
};
const FENCE_SIDE_GATE_PHYSICAL_START = {
  x: FENCE_EAST_SIDE_GATE_START.x + FENCE_EAST_OFFSET.x,
  y: FENCE_EAST_SIDE_GATE_START.y + FENCE_EAST_OFFSET.y,
} satisfies Point2Mm;
const FENCE_SIDE_GATE_PHYSICAL_END = {
  x: FENCE_EAST_SIDE_GATE_END.x + FENCE_EAST_OFFSET.x,
  y: FENCE_EAST_SIDE_GATE_END.y + FENCE_EAST_OFFSET.y,
} satisfies Point2Mm;

export const SITE_FENCE = Object.freeze({
  id: "SITE-FENCE",
  parcelId: "PARCEL-6012/26",
  enclosure: "PRIVATE_GARDEN",
  datumYmm: HOUSE.facades.front.faceYmm,
  sourceIds: [
    SOURCES.clientFenceMarkup20260821.id,
    SOURCES.clientGardenRevision20260821.id,
    SOURCES.fenceDesignProposal20260821.id,
    SOURCES.cadastre.id,
    SOURCES.coordination.id,
  ],
  // Exact centerlines represented by the user's yellow trace. Openings and
  // the house facade together complete this private-garden enclosure.
  annotatedCenterlineRuns: [
    fenceRun(
      "FENCE-MARKUP-FRONT-LEFT",
      "Ľavé čelné uzatvorenie záhrady",
      [FENCE_WEST_DATUM, { x: 2235, y: 3000 }],
      "CLIENT_FRONT_DATUM",
    ),
    fenceRun(
      "FENCE-MARKUP-FRONT-RIGHT",
      "Pravé čelné uzatvorenie záhrady",
      [{ x: 28040, y: 3000 }, { x: 31187, y: 3000 }],
      "CLIENT_FRONT_DATUM",
    ),
    fenceRun(
      "FENCE-MARKUP-EAST",
      "Východná hranica záhrady",
      [{ x: 31187, y: 3000 }, { x: 31109, y: 24497 }],
      "CADASTRAL_BOUNDARY",
    ),
    fenceRun(
      "FENCE-MARKUP-REAR",
      "Zadná hranica záhrady",
      [{ x: 31109, y: 24497 }, { x: -946, y: 23200 }],
      "CADASTRAL_BOUNDARY",
    ),
    fenceRun(
      "FENCE-MARKUP-WEST",
      "Západná hranica záhrady",
      [{ x: -946, y: 23200 }, FENCE_WEST_DATUM],
      "CADASTRAL_BOUNDARY",
    ),
  ] as const satisfies readonly FenceRunMm[],
  // Renderable fixed runs subtract the flush side wicket proposed at EAST-03.
  fixedRuns: [
    fenceRun(
      "FENCE-FIXED-FRONT-LEFT",
      "Pevné čelné pole vľavo od brány",
      [FENCE_WEST_DATUM, { x: 2235, y: 3000 }],
      "CLIENT_FRONT_DATUM",
    ),
    fenceRun(
      "FENCE-FIXED-FRONT-RIGHT",
      "Pravé čelné pole pri dome",
      [{ x: 28040, y: 3000 }, { x: 31187, y: 3000 }],
      "CLIENT_FRONT_DATUM",
    ),
    fenceRun(
      "FENCE-FIXED-EAST-UPPER",
      "Východný plot pred bočnou bránkou",
      [{ x: 31187, y: 3000 }, FENCE_EAST_SIDE_GATE_START],
      "CADASTRAL_BOUNDARY",
    ),
    fenceRun(
      "FENCE-FIXED-EAST-LOWER",
      "Východný plot za bočnou bránkou",
      [FENCE_EAST_SIDE_GATE_END, { x: 31109, y: 24497 }],
      "CADASTRAL_BOUNDARY",
    ),
    fenceRun(
      "FENCE-FIXED-REAR",
      "Zadný plot",
      [{ x: 31109, y: 24497 }, { x: -946, y: 23200 }],
      "CADASTRAL_BOUNDARY",
    ),
    fenceRun(
      "FENCE-FIXED-WEST",
      "Západný plot",
      [{ x: -946, y: 23200 }, FENCE_WEST_DATUM],
      "CADASTRAL_BOUNDARY",
    ),
  ] as const satisfies readonly FenceRunMm[],
  // Physical centerlines are trimmed to common miter points and shifted
  // 100 mm inside the parcel on cadastral sides. They are the renderer input;
  // annotatedCenterlineRuns above remain the exact legal/client reference.
  physicalFixedRuns: [
    physicalFenceRun(
      "FENCE-PHYSICAL-FRONT-LEFT",
      "Fyzické ľavé čelné pole",
      [FENCE_MITER_WEST_FRONT, { x: 2235, y: 3000 }],
      ["FENCE-FIXED-FRONT-LEFT", "FENCE-FIXED-WEST"],
      "SLATTED_ALUMINIUM",
    ),
    physicalFenceRun(
      "FENCE-PHYSICAL-FRONT-RIGHT",
      "Fyzické pravé čelné pole",
      [{ x: 28040, y: 3000 }, FENCE_MITER_FRONT_EAST],
      ["FENCE-FIXED-FRONT-RIGHT", "FENCE-FIXED-EAST-UPPER"],
      "SLATTED_ALUMINIUM",
    ),
    physicalFenceRun(
      "FENCE-PHYSICAL-EAST-UPPER",
      "Fyzický východný plot pred bočnou bránkou",
      [FENCE_MITER_FRONT_EAST, FENCE_SIDE_GATE_PHYSICAL_START],
      ["FENCE-FIXED-EAST-UPPER"],
      "SOLID_ALUMINIUM",
    ),
    physicalFenceRun(
      "FENCE-PHYSICAL-EAST-LOWER",
      "Fyzický východný plot za bočnou bránkou",
      [FENCE_SIDE_GATE_PHYSICAL_END, FENCE_MITER_EAST_REAR],
      ["FENCE-FIXED-EAST-LOWER"],
      "SOLID_ALUMINIUM",
    ),
    physicalFenceRun(
      "FENCE-PHYSICAL-REAR",
      "Fyzický zadný plot",
      [FENCE_MITER_EAST_REAR, FENCE_MITER_REAR_WEST],
      ["FENCE-FIXED-REAR"],
      "LIVING_HEDGE",
    ),
    physicalFenceRun(
      "FENCE-PHYSICAL-WEST",
      "Fyzický západný plot",
      [FENCE_MITER_REAR_WEST, FENCE_MITER_WEST_FRONT],
      ["FENCE-FIXED-WEST"],
      "SOLID_ALUMINIUM",
    ),
  ] as const satisfies readonly PhysicalFenceRunMm[],
  vehicleGate: {
    id: "GATE-GARDEN-VEHICLE",
    label: "Teleskopická brána do súkromnej záhrady",
    role: "SECONDARY_GARDEN_VEHICLE_GATE",
    startMm: { x: 2235, y: 3000 } as const satisfies Point2Mm,
    endMm: { x: 6435, y: 3000 } as const satisfies Point2Mm,
    leafClosureEndMm: { x: 6440, y: 3000 } as const satisfies Point2Mm,
    centerMm: { x: 4335, y: 3000 } as const satisfies Point2Mm,
    clearWidthMm: 4200,
    accessGarageDoorId: null,
    alignmentSourceId: SITE_SURFACES.supersededSideDriveway.id,
    markupStatus: "CLIENT_MARKUP_EXACT",
    mechanismProposal: "TRIPLE_TELESCOPIC_TRACKED_SLIDING",
    mechanismStatus: "DESIGN_PROPOSAL_REQUIRES_CLIENT_CONFIRMATION",
    panelCount: 3,
    infillTreatment: "SLATTED_ALUMINIUM" as const,
    openingDirection: "LOCAL_X_NEGATIVE",
    availableStackPocketMm: 2357,
    proposedStackEnvelopeMm: 1900,
    stackPocketStartMm: { x: 335, y: 3000 } as const satisfies Point2Mm,
    endSupport: "HOUSE_FACADE_BRACKET",
    terminalFrameCenterMm: { x: 6400, y: 3000 } as const satisfies Point2Mm,
    facadeReceiver: {
      centerMm: { x: 6434, y: 3045 } as const satisfies Point2Mm,
      widthMm: 12,
      depthMm: 130,
      heightMm: 1420,
      baseElevationMm: 100,
    },
    supportPostCentersMm: [
      { x: 2175, y: 3045 } as const satisfies Point2Mm,
    ],
    sourceIds: [
      SOURCES.clientFenceMarkup20260821.id,
      SOURCES.fenceDesignProposal20260821.id,
      SOURCES.coordination.id,
    ],
  },
  sidePedestrianGate: {
    id: "GATE-SIDE-PEDESTRIAN",
    label: "Skrytá pešia bránka pri EAST-03",
    startMm: FENCE_EAST_SIDE_GATE_START,
    endMm: FENCE_EAST_SIDE_GATE_END,
    clearWidthMm: 1200,
    accessOpeningId: "EAST-03",
    panelCount: 1,
    infillTreatment: "SOLID_ALUMINIUM" as const,
    endSupport: "POST",
    physicalStartMm: FENCE_SIDE_GATE_PHYSICAL_START,
    physicalEndMm: FENCE_SIDE_GATE_PHYSICAL_END,
    terminalFrameCenterMm: FENCE_SIDE_GATE_PHYSICAL_END,
    supportPostCentersMm: [
      fencePointAlong(
        FENCE_SIDE_GATE_PHYSICAL_START,
        FENCE_SIDE_GATE_PHYSICAL_END,
        -60,
      ),
      fencePointAlong(
        FENCE_SIDE_GATE_PHYSICAL_START,
        FENCE_SIDE_GATE_PHYSICAL_END,
        Math.hypot(
          FENCE_SIDE_GATE_PHYSICAL_END.x - FENCE_SIDE_GATE_PHYSICAL_START.x,
          FENCE_SIDE_GATE_PHYSICAL_END.y - FENCE_SIDE_GATE_PHYSICAL_START.y,
        ) + 60,
      ),
    ],
    status: "DESIGN_PROPOSAL_REQUIRES_CLIENT_CONFIRMATION",
    sourceIds: [
      SOURCES.clientGardenRevision20260821.id,
      SOURCES.fenceDesignProposal20260821.id,
      SOURCES.floorPlan.id,
      SOURCES.clientRevision20260821.id,
    ],
  },
  houseClosure: {
    startMm: { x: 6440, y: 3000 } as const satisfies Point2Mm,
    endMm: { x: 28040, y: 3000 } as const satisfies Point2Mm,
    role: "HOUSE_FRONT_FACADE_CLOSES_ENCLOSURE",
  },
  specificationStatus: "CLIENT_SELECTION_PENDING",
  approvedHeightMm: null,
  approvedMaterial: null,
  visualProposal: {
    status: "DESIGN_PROPOSAL",
    style: "HYBRID_LUXURY_PRIVACY",
    frontTreatment: "SLATTED_ALUMINIUM",
    sideTreatment: "SOLID_ALUMINIUM",
    rearTreatment: "LIVING_HEDGE",
    proposedHeightMm: 1600,
    finish: "FINE_TEXTURE_POWDER_COAT_RAL_7016",
    colorHex: "#252a2c",
    slatWidthMm: 60,
    slatDepthMm: 25,
    slatPitchMm: 110,
    groundClearanceMm: 70,
    railWidthMm: 60,
    railDepthMm: 24,
    postSizeMm: 80,
    gatePostSizeMm: 120,
    maximumPostSpacingMm: 2000,
    solidPanelDepthMm: 52,
    solidPanelJointMm: 22,
    curbHeightMm: 100,
    curbDepthMm: 120,
    physicalBoundaryInsetMm: FENCE_PHYSICAL_BOUNDARY_INSET_MM,
    telescopicPanelOverlapMm: 100,
    telescopicPanelPlaneOffsetMm: 45,
    gateThresholdDepthMm: 260,
    rearHedgeHeightMm: 1850,
    rearHedgeDepthMm: 900,
    rearHedgeCenterlineOffsetMm: 450,
    rearHedgeClusterSpacingMm: 620,
  },
  legacyC3: {
    proposedHeightMm: 1600,
    material: "WIRE_MESH",
    sourceId: SOURCES.coordination.id,
    status: "UNCONFIRMED_LEGACY_PROPOSAL",
  },
});

export interface TerraceZoneRectMm {
  readonly x0: number;
  readonly y0: number;
  readonly x1: number;
  readonly y1: number;
}

export interface TerraceZoneD1 {
  readonly id: string;
  readonly label: string;
  readonly documentedAreaM2: number;
  readonly covered: boolean;
  /** Axis-aligned rectangles in plan millimetres; boards run along X. */
  readonly rectsMm: readonly TerraceZoneRectMm[];
  readonly sourceId: string;
}

/**
 * The three documented D1.1.002 timber terrace zones (34,80 + 33,10 + 16,45 =
 * 84,35 m² per the room legend). They supersede the older C3 53 m² surface,
 * which is kept above as provenance. Rectangles are traced from the deck
 * hatch vectors of the drawing.
 */
export const TERRACE_ZONES_D1: readonly TerraceZoneD1[] = [
  {
    id: "TERR-D1-GARDEN",
    label: "Terasa D1 · záhradná časť s lodžiou · 34,80 m²",
    documentedAreaM2: 34.8,
    covered: false,
    rectsMm: [
      { x0: 6440, y0: 8247, x1: 10640, y1: 11200 },
      { x0: 6440, y0: 11200, x1: 18040, y1: 13100 },
    ],
    sourceId: SOURCES.floorPlan.id,
  },
  {
    id: "TERR-D1-WING",
    label: "Terasa D1 · západné rameno krídla · 33,10 m²",
    documentedAreaM2: 33.1,
    covered: false,
    rectsMm: [{ x0: 18040, y0: 11200, x1: 21040, y1: 22035 }],
    sourceId: SOURCES.floorPlan.id,
  },
  {
    id: "TERR-D1-PORCH",
    label: "Terasa D1 · krytá terasa pod štítom · 16,45 m²",
    documentedAreaM2: 16.45,
    covered: true,
    rectsMm: [
      { x0: 21040, y0: 19535, x1: 21540, y1: 21535 },
      { x0: 21540, y0: 19535, x1: 27540, y1: 22035 },
    ],
    sourceId: SOURCES.floorPlan.id,
  },
] as const;

export function terraceZoneAreaM2(zone: TerraceZoneD1): number {
  return (
    zone.rectsMm.reduce(
      (sum, rect) => sum + (rect.x1 - rect.x0) * (rect.y1 - rect.y0),
      0,
    ) / 1_000_000
  );
}

export const GARDEN_POOL = Object.freeze({
  id: "POOL-COURTYARD-56X3",
  label: "Bazén 5,6 × 3 m",
  targetZone: "OPEN_L_COURTYARD_BY_MAIN_TERRACE",
  placementStatus:
    "CLIENT_REQUESTED_LAYOUT_REQUIRES_RAINWATER_COORDINATION",
  centerMm: { x: 14_940, y: 14_900 } as const satisfies Point2Mm,
  orientation: "LONG_EDGE_PARALLEL_TO_MAIN_TERRACE_LOCAL_X",
  terraceConnection: {
    terraceId: "TERR-D1-GARDEN",
    edge: "NORTH_Y_13100",
    copingEdgeYmm: 13_100,
    planGapMm: 0,
    contactLengthMm: 6_200,
    sharedTopElevationMm: 20,
  },
  // The pool lies in the inner corner of the L: its coping east edge sits
  // flush against the wing deck west edge, same zero-gap rule as the main
  // terrace connection above.
  wingDeckContact: {
    deckId: "TERR-D1-WING",
    edgeXmm: 18_040,
    planGapMm: 0,
    sharedTopElevationMm: 20,
  } as const,
  waterLengthMm: 5_600,
  waterWidthMm: 3_000,
  waterAreaM2: 16.8,
  copingWidthMm: 300,
  proposedWaterDepthMm: 1_400,
  waterFootprintMm: [
    { x: 12_140, y: 13_400 },
    { x: 17_740, y: 13_400 },
    { x: 17_740, y: 16_400 },
    { x: 12_140, y: 16_400 },
    { x: 12_140, y: 13_400 },
  ] as const satisfies readonly Point2Mm[],
  copingFootprintMm: [
    { x: 11_840, y: 13_100 },
    { x: 18_040, y: 13_100 },
    { x: 18_040, y: 16_700 },
    { x: 11_840, y: 16_700 },
    { x: 11_840, y: 13_100 },
  ] as const satisfies readonly Point2Mm[],
  modelledClearancesMm: {
    mainTerrace: 0,
    wingTerrace: 0,
    rainTankShell: 1_787,
    infiltrationObject: 1_428,
    closestRainPipeShell: 630,
  },
  sourceIds: [
    SOURCES.clientExteriorRevision20260821.id,
    SOURCES.poolDesignProposal20260821.id,
    SOURCES.floorPlan.id,
    SOURCES.rainwater.id,
    SOURCES.asBuiltGap.id,
  ],
});

const route = (
  id: string,
  label: string,
  layer: UtilityRoute["layer"],
  points: readonly (readonly [number, number])[],
  sourceId: string,
  status: UtilityRoute["status"],
  radiusMm = 65,
  revisionStatus: UtilityRoute["revisionStatus"] = "COORDINATED",
  additionalSourceIds: readonly string[] = [],
): UtilityRoute => ({
  id,
  label,
  layer,
  pointsMm: points.map(([x, y]) => ({ x, y })),
  sourceId,
  sourceIds: [sourceId, ...additionalSourceIds],
  status,
  revisionStatus,
  radiusMm,
});

export const UTILITY_ROUTES: readonly UtilityRoute[] = [
  route("UTIL-WATER-STREET", "Verejný vodovod v komunikácii", "contextNetworks", [[-5000, -4300], [36000, -4300]], SOURCES.dmvsWater.id, "EXISTING_CONTEXT", 90),
  route("UTIL-SEWER-STREET", "Verejná splašková stoka v komunikácii", "contextNetworks", [[-5000, -5600], [36000, -5600]], SOURCES.dmvsSewer.id, "EXISTING_CONTEXT", 115),
  route("UTIL-POWER-STREET", "Projektový kontext podzemného NN", "contextNetworks", [[-5000, -2800], [36000, -2800]], SOURCES.coordination.id, "EXISTING_CONTEXT", 55),
  route("UTIL-LIGHTING-STREET", "Verejné osvetlenie", "contextNetworks", [[-5000, -6800], [36000, -6800]], SOURCES.networkContext.id, "EXISTING_CONTEXT", 40),
  route("UTIL-WATER", "Navrhnutá vodovodná prípojka", "water", [[13500, -1689], [13500, 1415], [12861, 1415], [12861, 3000]], SOURCES.water.id, "DESIGNED", 80),
  route("UTIL-SEWER", "Navrhnutá splašková kanalizácia", "sewer", [[15794, 3000], [15712, 1483], [16814, 1483]], SOURCES.sewer.id, "DESIGNED", 95),
  route("UTIL-SEWER-FUTURE", "Budúce gravitačné prepojenie", "sewer", [[15712, 1483], [15640, -400], [15400, -5600]], SOURCES.sewer.id, "FUTURE_OPTION", 45),
  route("UTIL-RAIN-SOUTH", "Dažďová kanalizácia · prítok k ŠD · predbežne obídený bazén", "rainwater", [[7600, 10800], [7600, 12400], [11000, 12400], [11000, 17400], [16900, 17400]], SOURCES.rainwater.id, "DESIGNED", 70, "REVISION_CONFLICT", [SOURCES.clientExteriorRevision20260821.id, SOURCES.poolDesignProposal20260821.id]),
  route("UTIL-RAIN-NORTH", "Dažďová kanalizácia · ŠD–Šf–AN", "rainwater", [[26300, 21000], [22400, 15600], [18800, 15600], [18800, 17400], [16900, 17400]], SOURCES.rainwater.id, "DESIGNED", 70),
  route("UTIL-RAIN-OVERFLOW", "Bezpečnostný prepad do vsaku", "rainwater", [[15416, 18147], [13981, 19878], [12981, 19878]], SOURCES.rainwater.id, "DESIGNED", 55),
  route("UTIL-ELECTRICITY", "Domové vedenie NN · staršia C3 trasa", "electricity", [[0, 3500], [2600, 4200], [5200, 4750], [7236, 5327]], SOURCES.coordination.id, "DESIGNED", 55, "REVISION_CONFLICT"),
] as const;

export const LAYERS = [
  { id: "cadastre", label: "Kataster", shortLabel: "KN", color: "#ff5738", source: "ČÚZK · aktuálne" },
  { id: "street", label: "Ulica a spevnené plochy", shortLabel: "UL", color: "#9aa3a6", source: "KN + C3 · návrh" },
  { id: "building", label: "Dom, strecha a plot", shortLabel: "RD", color: "#f5f2e9", source: "D1.1 + revízia" },
  { id: "foundations", label: "Základy", shortLabel: "ZA", color: "#929da0", source: "D1.1.001" },
  { id: "water", label: "Vodovod", shortLabel: "VO", color: "#398cff", source: "IO 03" },
  { id: "sewer", label: "Splašková kanalizácia", shortLabel: "SK", color: "#a76b35", source: "IO 02" },
  { id: "rainwater", label: "Dažďová voda", shortLabel: "DA", color: "#4aae7a", source: "IO 01" },
  { id: "electricity", label: "Elektrina NN", shortLabel: "NN", color: "#ec4ec6", source: "C3 · konflikt revízie" },
  { id: "contextNetworks", label: "Siete v ulici", shortLabel: "IS", color: "#62d8ff", source: "C3 / Z7" },
] as const satisfies readonly {
  id: LayerId;
  label: string;
  shortLabel: string;
  color: string;
  source: string;
}[];

export const DEFAULT_LAYER_VISIBILITY: Readonly<Record<LayerId, boolean>> = {
  cadastre: true,
  street: true,
  building: true,
  foundations: false,
  water: false,
  sewer: false,
  rainwater: false,
  electricity: false,
  contextNetworks: false,
};

export function lineLengthMm(points: readonly Point2Mm[]): number {
  let length = 0;
  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1];
    const current = points[index];
    length += Math.hypot(current.x - previous.x, current.y - previous.y);
  }
  return Math.round(length);
}

export function foundationLengthMm(strip: FoundationStrip): number {
  return lineLengthMm([strip.startMm, strip.endMm]);
}

export function foundationVolumeM3(strip: FoundationStrip): number {
  return (
    (foundationLengthMm(strip) * strip.widthMm * strip.heightMm) /
    1_000_000_000
  );
}

export function updateFoundationWidth(
  strips: readonly FoundationStrip[],
  id: string,
  widthMm: number,
): readonly FoundationStrip[] {
  if (!Number.isFinite(widthMm) || !Number.isInteger(widthMm) || widthMm <= 0) {
    throw new Error("Šírka musí byť kladné celé číslo v milimetroch.");
  }
  return strips.map((strip) =>
    strip.id === id ? { ...strip, widthMm } : strip,
  );
}

export function polygonAreaM2(points: readonly Point2Mm[]): number {
  if (points.length < 4) return 0;
  let twiceArea = 0;
  for (let index = 0; index < points.length - 1; index += 1) {
    const current = points[index];
    const next = points[index + 1];
    twiceArea += current.x * next.y - next.x * current.y;
  }
  return Math.abs(twiceArea) / 2 / 1_000_000;
}

export function findSource(sourceId: string): SourceRecord | undefined {
  return Object.values(SOURCES).find((source) => source.id === sourceId);
}
