"use client";

import {
  Building2,
  Cable,
  ChevronRight,
  CircleHelp,
  Database,
  Eye,
  EyeOff,
  Focus,
  Info,
  Layers3,
  Map,
  MapPin,
  Menu,
  PanelLeftClose,
  PanelRightClose,
  Search,
  ShieldCheck,
  TriangleAlert,
  Undo2,
  X,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
  type CSSProperties,
} from "react";

import {
  BabylonViewport,
  type BabylonViewportHandle,
} from "./babylon-viewport";
import { CommandPalette } from "./command-palette";
import { useChromeVisibility } from "./use-chrome-visibility";
import type { NavigationMode } from "@/lib/twin-viewport-contract";
import { INTERIOR_ROOMS } from "@/lib/twin-interior";
import { WALK_AVATARS, type WalkAvatarId } from "@/lib/twin-avatar";
import {
  buildCommands,
  type CameraPresetId,
  type TwinCommand,
} from "@/lib/twin-commands";
import {
  DEFAULT_WORKSPACE_MODE,
  chromeContract,
  movementForWorkspace,
  viewModeForWorkspace,
  workspaceForMovement,
  type WorkspaceMode,
} from "@/lib/twin-ui-mode";
import {
  DEFAULT_LAYER_VISIBILITY,
  FOUNDATIONS,
  GARDEN_POOL,
  HOUSE,
  LAYERS,
  POOL_SURROUND_DECK,
  POOL_TECHNOLOGY_SHAFT,
  ROAD_CONTEXT,
  SITE_FENCE,
  SOURCES,
  UTILITY_ROUTES,
  findSource,
  foundationLengthMm,
  foundationVolumeM3,
  lineLengthMm,
  updateFoundationWidth,
  type FoundationStrip,
  type LayerId,
  type SourceRecord,
} from "@/lib/twin-site";

type InspectorTab = "parameters" | "sources";

interface HistoryItem {
  readonly id: number;
  readonly foundationId: string;
  readonly beforeMm: number;
  readonly afterMm: number;
  readonly at: string;
}

interface DetailRow {
  readonly label: string;
  readonly value: string;
  readonly unit?: string;
}

interface EntityDetail {
  readonly id: string;
  readonly code: string;
  readonly eyebrow: string;
  readonly title: string;
  readonly subtitle: string;
  readonly status: string;
  readonly statusTone: "current" | "design" | "context" | "warning";
  readonly rows: readonly DetailRow[];
  readonly sourceIds: readonly string[];
  readonly note: string;
  readonly editableFoundation?: FoundationStrip;
}

const COMPACT_LAYOUT_QUERY = "(max-width: 1080px)";
const DEFAULT_SELECTION_ID = "PARCEL-6012/26";

function subscribeCompactLayout(onChange: () => void) {
  const mediaQuery = window.matchMedia(COMPACT_LAYOUT_QUERY);
  mediaQuery.addEventListener("change", onChange);
  return () => mediaQuery.removeEventListener("change", onChange);
}

function getCompactLayoutSnapshot() {
  return window.matchMedia(COMPACT_LAYOUT_QUERY).matches;
}

function getCompactLayoutServerSnapshot() {
  return false;
}

const formatter = new Intl.NumberFormat("sk-SK", {
  maximumFractionDigits: 2,
});

const fmt = (value: number) => formatter.format(value);

function utilityDetail(id: string): EntityDetail | undefined {
  const route = UTILITY_ROUTES.find((candidate) => candidate.id === id);
  if (!route) return undefined;
  const code = route.layer === "contextNetworks" ? "IS" : route.layer.slice(0, 2).toUpperCase();
  const source = findSource(route.sourceId);
  return {
    id: route.id,
    code,
    eyebrow: route.status === "EXISTING_CONTEXT" ? "VEREJNÁ INFRAŠTRUKTÚRA" : "NAVRHNUTÁ TRASA",
    title: route.label,
    subtitle: route.layer === "contextNetworks" ? "Sieť pri hranici parcely" : "Domová prípojka / rozvod",
    status:
      route.revisionStatus === "REVISION_CONFLICT"
        ? "Konflikt revízie · C3 voči D1"
        : route.status === "EXISTING_CONTEXT"
        ? "Verejný register / kontext"
        : route.status === "FUTURE_OPTION"
          ? "Budúca možnosť"
          : "Projektovaný stav",
    statusTone:
      route.revisionStatus === "REVISION_CONFLICT"
        ? "warning"
        : route.status === "EXISTING_CONTEXT"
          ? "current"
          : "design",
    rows: [
      { label: "Dĺžka modelovanej trasy", value: fmt(lineLengthMm(route.pointsMm) / 1000), unit: "m" },
      { label: "Priemer vizualizácie", value: fmt(route.radiusMm * 2), unit: "mm" },
      { label: "Stav", value: route.status === "DESIGNED" ? "DESIGNED" : route.status },
      { label: "Koordinácia revízie", value: route.revisionStatus },
      { label: "Zdroj", value: source?.title ?? route.sourceId },
    ],
    sourceIds: [
      route.sourceId,
      ...(route.layer === "electricity" || route.layer === "contextNetworks"
        ? [SOURCES.providerStatements.id]
        : []),
      SOURCES.asBuiltGap.id,
    ],
    note:
      route.revisionStatus === "REVISION_CONFLICT"
        ? "Trasa a koncový bod pochádzajú zo staršej C3. Po aktivovaní dlhšieho pôdorysu D1.1.002 koncový bod leží v garážovej hmote; vrstva je preto predvolene vypnutá a nesmie sa použiť na realizáciu."
        : route.status === "EXISTING_CONTEXT"
        ? "Verejná DTM je kontext digitálneho dvojčaťa, nie vytýčenie siete pre výkopové práce."
        : "Poloha je prenesená z projektovej situácie. Skutočné geodetické zameranie prípojky zatiaľ nie je dostupné.",
  };
}

function getEntityDetail(
  id: string,
  foundations: readonly FoundationStrip[],
): EntityDetail {
  const foundation = foundations.find((candidate) => candidate.id === id);
  if (foundation) {
    return {
      id,
      code: id,
      eyebrow: "ZÁKLADOVÝ PÁS",
      title: foundation.label,
      subtitle: "Monolitický prostý betón · návrh",
      status: "Projektovaný stav · odvodené zarovnanie",
      statusTone: "design",
      rows: [
        { label: "Dĺžka", value: fmt(foundationLengthMm(foundation)), unit: "mm" },
        { label: "Šírka", value: fmt(foundation.widthMm), unit: "mm" },
        { label: "Výška", value: fmt(foundation.heightMm), unit: "mm" },
        { label: "Spodná hrana", value: fmt(foundation.baseElevationMm), unit: "mm" },
        { label: "Objem pásu", value: fmt(foundationVolumeM3(foundation)), unit: "m³" },
      ],
      sourceIds: [foundation.sourceId],
      note: "Objem jedného pásu sa počíta z tej istej geometrie, ktorú vidíte v 3D. Súčet všetkých pásov nezohľadňuje vzájomné prekrytia.",
      editableFoundation: foundation,
    };
  }

  const utility = utilityDetail(id);
  if (utility) return utility;

  if (id === SITE_FENCE.id) {
    const tracedLengthMm = SITE_FENCE.annotatedCenterlineRuns.reduce(
      (total, run) => total + lineLengthMm(run.pointsMm),
      0,
    );
    return {
      id,
      code: "OP",
      eyebrow: "OPLOTENIE SÚKROMNEJ ZÁHRADY",
      title: "Hybridný minimalistický plot",
      subtitle: "Čelné lamely · plné boky · živý plot vzadu",
      status: "Poloha podľa náčrtu · materiál čaká na výber",
      statusTone: "design",
      rows: [
        { label: "Trasa plotu podľa náčrtu", value: fmt(tracedLengthMm / 1000), unit: "m" },
        { label: "Navrhovaná výška", value: fmt(SITE_FENCE.visualProposal.proposedHeightMm), unit: "mm" },
        { label: "Predná línia", value: `lamely ${SITE_FENCE.visualProposal.slatWidthMm} / ${SITE_FENCE.visualProposal.slatPitchMm}`, unit: "mm" },
        { label: "Bočné línie", value: "plné hliníkové polia · nepriehľadné" },
        { label: "Zadná línia", value: `hustý živý plot · návrh ${SITE_FENCE.visualProposal.rearHedgeHeightMm}`, unit: "mm" },
        { label: "Povrch", value: "RAL 7016 · jemná štruktúra" },
        { label: "Uzatvorenie", value: "súkromná záhrada · y = 3 000 mm" },
        { label: "Priamy vjazd do garáže", value: "zostáva voľný" },
      ],
      sourceIds: SITE_FENCE.sourceIds,
      note: "Žltý náčrt je prenesený na líniu čelnej fasády a následne po bočných a zadnej katastrálnej hranici. Predná časť ostáva vzdušná lamelová, boky sú plné RAL 7016 a zadnú kovovú líniu nahrádza hustý živý plot. Výška, výrobok aj druh výsadby sú vizualizačný návrh; pred realizáciou treba hranice geodeticky vytýčiť.",
    };
  }

  if (
    id === SITE_FENCE.vehicleGate.id ||
    id === SITE_FENCE.sidePedestrianGate.id
  ) {
    const vehicle = id === SITE_FENCE.vehicleGate.id;
    return {
      id,
      code: vehicle ? "BR" : "PB",
      eyebrow: vehicle ? "BRÁNA DO ZÁHRADY" : "BOČNÁ PEŠIA BRÁNKA",
      title: vehicle
        ? "Trojdielna teleskopická brána"
        : "Skrytá bránka pri EAST-03",
      subtitle: vehicle
        ? "Čistý otvor 4,2 m · zasúvanie doľava"
        : "Plná výplň v bočnom plote",
      status: vehicle
        ? "Poloha podľa zeleného náčrtu · mechanizmus návrh"
        : "Funkčný dizajnový návrh · čaká na potvrdenie",
      statusTone: "design",
      rows: vehicle
        ? [
            { label: "Čistá šírka", value: fmt(SITE_FENCE.vehicleGate.clearWidthMm), unit: "mm" },
            { label: "Stred otvoru", value: "x = 4 335 · y = 3 000", unit: "mm" },
            { label: "Mechanizmus", value: "3-dielny teleskopický pojazd" },
            { label: "Smer otvorenia", value: "doľava · −X" },
            { label: "Vjazd do garáže", value: "samostatný · bez kolízie" },
          ]
        : [
            { label: "Čistá šírka", value: fmt(SITE_FENCE.sidePedestrianGate.clearWidthMm), unit: "mm" },
            { label: "Napojenie", value: SITE_FENCE.sidePedestrianGate.accessOpeningId },
            { label: "Vzhľad", value: "plná RAL 7016 · skryté kovanie" },
          ],
      sourceIds: vehicle
        ? SITE_FENCE.vehicleGate.sourceIds
        : SITE_FENCE.sidePedestrianGate.sourceIds,
      note: vehicle
        ? "Zelený otvor je na pôvodnom ľavom zjazde, nie pred novou garážovou bránou. Jedno 4,2 m posuvné krídlo sa do ľavého priestoru nezmestí, preto model navrhuje kompaktný trojdielny teleskopický systém na zapustenej koľajnici."
        : "Bránka nie je samostatne vyznačená v náčrte. Je zapustená do plného bočného poľa s rovnakým povrchom, aby zostala nenápadná a zároveň nezablokovala spevnený prístup k dverám EAST-03.",
    };
  }

  if (id === GARDEN_POOL.id) {
    return {
      id,
      code: "BZ",
      eyebrow: "ZÁHRADNÝ BAZÉN",
      title: GARDEN_POOL.label,
      subtitle: "Otvorený L-dvor pri hlavnej terase",
      status: "Klientska revízia 29. 8. · profesijná koordinácia otvorená",
      statusTone: "design",
      rows: [
        { label: "Vodná plocha", value: `${fmt(GARDEN_POOL.waterLengthMm)} × ${fmt(GARDEN_POOL.waterWidthMm)}`, unit: "mm" },
        { label: "Plocha vody", value: fmt(GARDEN_POOL.waterAreaM2), unit: "m²" },
        { label: "Svetlý lem", value: fmt(GARDEN_POOL.copingWidthMm), unit: "mm" },
        { label: "Navrhovaná hĺbka", value: fmt(GARDEN_POOL.proposedWaterDepthMm), unit: "mm" },
        { label: "Medzera lemu od terasy", value: fmt(GARDEN_POOL.terraceConnection.planGapMm), unit: "mm" },
        { label: "Dĺžka dotyku s terasou", value: fmt(GARDEN_POOL.terraceConnection.contactLengthMm), unit: "mm" },
        { label: "Nový drevený lem", value: fmt(POOL_SURROUND_DECK.nominalWidthMm), unit: "mm" },
        { label: "Nová čistá plocha dreva", value: fmt(POOL_SURROUND_DECK.netDeckAreaM2), unit: "m²" },
        { label: "Odstup od najbližšieho dažďového potrubia", value: fmt(GARDEN_POOL.modelledClearancesMm.closestRainPipeShell), unit: "mm" },
        { label: "Odstup od plášťa dažďovej nádrže", value: fmt(GARDEN_POOL.modelledClearancesMm.rainTankShell), unit: "mm" },
        { label: "Odstup od šachty", value: fmt(GARDEN_POOL.modelledClearancesMm.technologyShaftShell), unit: "mm" },
        { label: "Orientácia", value: "dlhšia strana rovnobežne s terasou" },
      ],
      sourceIds: GARDEN_POOL.sourceIds,
      note: "Aktuálna klientska revízia mení vodnú plochu na mierne dlhší a užší rozmer 6,0 × 2,7 m. Pôvodná D1 terasa ostáva zachovaná; voľné západné a južné strany dopĺňa presne 2 m široký drevený lem s čistou plochou 22,81 m² po odpočítaní poklopu. Celá kompaktná šachta aj poklop sú vycentrované v južnom páse bezprostredne za bazénom. Kríky a mulčovaný záhon pri bazéne sú odstránené. Dažďové potrubie, konštrukciu bazéna, šachtu, ZTI a elektro treba pred realizáciou odborne skoordinovať.",
    };
  }

  if (id === POOL_TECHNOLOGY_SHAFT.id) {
    const shaft = POOL_TECHNOLOGY_SHAFT;
    return {
      id,
      code: "ŠB",
      eyebrow: "PODZEMNÁ BAZÉNOVÁ TECHNOLÓGIA",
      title: shaft.label,
      subtitle: "Poklop v terase · rebrík · filtrácia · elektro",
      status: "Klientsky návrh · ZTI a elektro na potvrdenie",
      statusTone: "warning",
      rows: [
        {
          label: "Vonkajší pôdorys",
          value: `${fmt(shaft.outerFootprintMm.x1 - shaft.outerFootprintMm.x0)} × ${fmt(shaft.outerFootprintMm.y1 - shaft.outerFootprintMm.y0)}`,
          unit: "mm",
        },
        { label: "Úroveň podlahy", value: fmt(shaft.floorElevationMm), unit: "mm" },
        { label: "Svetlá výška", value: fmt(shaft.clearHeightMm), unit: "mm" },
        {
          label: "Poklop",
          value: `${fmt(shaft.hatch.clearWidthMm)} × ${fmt(shaft.hatch.clearLengthMm)}`,
          unit: "mm",
        },
        { label: "Poloha", value: "geometrický stred terasy za bazénom" },
        { label: "Odstup od dažďového potrubia", value: fmt(shaft.coordinationClearancesMm.rainPipeShell), unit: "mm" },
        { label: "Rebrík", value: `${shaft.ladder.rungCount} nerezových priečok` },
        { label: "Piesková filtrácia", value: `Ø ${fmt(shaft.sandFilter.vesselDiameterMm)}`, unit: "mm" },
        { label: "Obehové čerpadlo", value: fmt(shaft.circulationPump.motorPowerKw), unit: "kW" },
        { label: "Elektrický rozvádzač", value: `${shaft.electricalPanel.breakerCount} ističov · IP65 návrh` },
        { label: "Ovládanie", value: "E / dotyk · poklop, zostup aj návrat" },
      ],
      sourceIds: shaft.sourceIds,
      note: "Poklop je pochôdzny iba v zatvorenom stave. Po otvorení ponúkne samostatnú akciu zostupu po rebríku; prechádzka sa bezpečne presunie na podzemnú servisnú podlahu a rovnakým rebríkom sa vráti na terasu. Model obsahuje železobetónovú vaňu, filter, predfilter, 0,75 kW čerpadlo, tlakové potrubia, podlahovú vpusť, servisné svetlo a IP65 rozvádzač s ôsmimi ističmi. Ide o vizualizačný návrh, nie výrobnú ani realizačnú dokumentáciu.",
    };
  }

  if (id === "HOUSE-DESIGN") {
    return {
      id,
      code: "SO 01",
      eyebrow: "RODINNÝ DOM",
      title: "Novostavba RD Březí u Mikulova",
      subtitle: "Dve pretínajúce sa sedlové hmoty",
      status: "Projektovaný stav · aktívna D1.1.002",
      statusTone: "design",
      rows: [
        { label: "Odvodená obálka D1", value: fmt(HOUSE.derivedFootprintAreaM2), unit: "m²" },
        { label: "Úžitková plocha miestností", value: fmt(HOUSE.floorAreaM2), unit: "m²" },
        { label: "Terasy · súpis D1", value: fmt(HOUSE.terraceAreaM2), unit: "m²" },
        { label: "Aktívny pôdorys D1.1.002", value: "21 600 × 19 035", unit: "mm" },
        { label: "C3 · staršia situačná revízia", value: "20 800 × 19 044", unit: "mm" },
        { label: "Rozdiel garážového konca", value: "+800", unit: "mm" },
        { label: "Orientácia", value: "garáž vľavo · krídlo vpravo" },
        { label: "Hrebeň", value: "+5 560", unit: "mm" },
        { label: "Výškový systém", value: "±0,000 = 184,00", unit: "m Bpv" },
      ],
      sourceIds: HOUSE.sourceIds,
      note: "3D hmota vychádza z neskoršieho pôdorysu D1.1.002 bez zrkadlenia: garážový koniec je na lokálnom −X a obytné krídlo na +X. Umiestnenie do parcely je odvodené zarovnaním pravého okraja, zalomenia a hornej hrany na georeferencovanú C3; nejde o vytyčovací podklad. Aktívna revízia predlžuje garáž o 1 000 mm na úkor záhradnej lodžie a znižuje D1 terasy z pôvodných 84,35 m² na 80,15 m². Žltá plocha C3 53 m² ostáva samostatnou staršou georeferencovanou revíziou.",
    };
  }

  if (id === "ROAD-6012-1") {
    return {
      id,
      code: "6012/1",
      eyebrow: "DOPRAVNÁ INFRAŠTRUKTÚRA",
      title: "Miestna komunikácia pri parcele",
      subtitle: "Bez potvrdeného názvu ulice v RÚIAN",
      status: "Aktuálny KN + C3 rozsah + klientsky povrch",
      statusTone: "context",
      rows: [
        { label: "Parcela komunikácie", value: "6012/1" },
        { label: "Evidovaná plocha", value: fmt(ROAD_CONTEXT.registeredAreaM2), unit: "m²" },
        { label: "Kategória", value: "miestna komunikácia" },
        { label: "Kontakt s parcelou", value: "2 cestné hrany + oblúk" },
        { label: "Čelná hrana", value: "28 194", unit: "mm" },
        { label: "Koncová hrana", value: "21 497", unit: "mm" },
        { label: "C3 rezerva po vozovku", value: fmt(Math.abs(ROAD_CONTEXT.frontAsphaltEdgeYmm)), unit: "mm" },
        { label: "Vjazd ku garáži", value: "4 200", unit: "mm" },
        { label: "Chodník ku dverám", value: "1 500", unit: "mm" },
        { label: "Povrch vozovky v 3D", value: "sivá betónová bloková dlažba" },
        { label: "Vzor dlažby", value: "200 × 100 · vizualizačný modul", unit: "mm" },
        { label: "Krajnica", value: "hlina + riedka náletová vegetácia" },
        { label: "Verejné osvetlenie", value: "štíhle sivé LED stožiare · ilustračné" },
        { label: "Najbližšia evidovaná ulica", value: "Bezová · ≈185 m" },
      ],
      sourceIds: [...ROAD_CONTEXT.sourceIds, SOURCES.networkContext.id],
      note: "Parcela 6012/26 je na konci bloku: cestný pozemok 6012/1 ju obopína pozdĺž čelnej aj bočnej hrany a spája ich zaobleným rohom. Hranice cestného pozemku aj evidovaná plocha 10 647 m² sú načítané z aktuálnej služby ČÚZK. Sivá bloková dlažba, hlinená krajnica, obrubník a štíhle LED stožiare vychádzajú z fotografie stavebníka z 25. 8. 2026; modul dlažby ani rozstup stožiarov nie sú realizačnou špecifikáciou. Hrana vozovky a približne 3,104 m nespevnená cestná rezerva sú stále odvodené z C3, nie zo zamerania skutočných obrubníkov.",
    };
  }

  if (id === "OBJ-WATER-METER") {
    return {
      id,
      code: "VŠ",
      eyebrow: "VODOMERNÁ ŠACHTA",
      title: "Plastová samonosná šachta",
      subtitle: "Prípojka vody IO 03",
      status: "Projektovaný stav",
      statusTone: "design",
      rows: [
        { label: "Vnútorný rozmer", value: "1 200 × 900 × 1 500", unit: "mm" },
        { label: "Prípojka", value: "PE d32" },
        { label: "Verejný rad", value: "PE d110 · obec Březí" },
      ],
      sourceIds: [SOURCES.water.id, SOURCES.dmvsWater.id, SOURCES.providerStatements.id, SOURCES.asBuiltGap.id],
      note: "Verejný vodovod je potvrdený v DMVS; poloha a realizácia domovej prípojky ostáva návrhová.",
    };
  }

  if (id === "OBJ-RAIN-TANK" || id === "OBJ-INFILTRATION") {
    const tank = id === "OBJ-RAIN-TANK";
    return {
      id,
      code: tank ? "AN" : "VS",
      eyebrow: "HOSPODÁRENIE S DAŽĎOVOU VODOU",
      title: tank ? "Akumulačná nádrž" : "Podzemný vsakovací objekt",
      subtitle: "Domová dažďová kanalizácia IO 01",
      status: "Projektovaný stav",
      statusTone: "design",
      rows: tank
        ? [
            { label: "Využiteľný objem", value: "8,5", unit: "m³" },
            { label: "Využitie", value: "závlaha" },
            { label: "Bezpečnostný prepad", value: "do podzemného vsaku" },
          ]
        : [
            { label: "Pôdorys ryhy", value: "5,0 × 3,5", unit: "m" },
            { label: "Užitočný objem · správa", value: "8,7", unit: "m³" },
            { label: "Retenčný objem · detail", value: "6,1", unit: "m³" },
            { label: "Materiál", value: "štrk fr. 16/32" },
          ],
      sourceIds: [SOURCES.rainwater.id],
      note: tank
        ? "Nádrž je projektovaný prvok, nie potvrdené skutočné vyhotovenie."
        : "Dokumentácia IO 01 si odporuje: správa uvádza užitočný objem 8,7 m³, detail 6,1 m³. Model zachováva pôdorys 5,0 × 3,5 m a konflikt otvorene zobrazuje.",
    };
  }

  if (id === "OBJ-SEWER-TANK") {
    return {
      id,
      code: "ŽU",
      eyebrow: "SPLAŠKOVÁ KANALIZÁCIA",
      title: "Dočasná žumpa na vyvážanie",
      subtitle: "Budúce napojenie na verejnú stoku",
      status: "Projektovaný stav",
      statusTone: "design",
      rows: [
        { label: "Využiteľný objem", value: "11,0", unit: "m³" },
        { label: "Konštrukcia", value: "plastová samonosná k vybetónovaniu" },
        { label: "Budúci stav", value: "gravitačné pripojenie cez RŠ" },
      ],
      sourceIds: [SOURCES.sewer.id, SOURCES.dmvsSewer.id, SOURCES.asBuiltGap.id],
      note: "Verejná splašková stoka je potvrdená v DMVS. Projekt uvádza dočasnú žumpu do navýšenia kapacity ČOV.",
    };
  }

  return {
    id: DEFAULT_SELECTION_ID,
    code: "6012/26",
    eyebrow: "KATASTRÁLNA PARCELA",
    title: "Parcela 6012/26",
    subtitle: "k. ú. Březí u Mikulova · 613908",
    status: "Aktuálny verejný register",
    statusTone: "current",
    rows: [
      { label: "Evidovaná výmera", value: "753", unit: "m²" },
      { label: "Plocha z polygónu", value: "752,521", unit: "m²" },
      { label: "Druh pozemku", value: "orná pôda" },
      { label: "Ochrana", value: "poľnohospodársky pôdny fond" },
      { label: "BPEJ", value: "00401" },
      { label: "Poloha", value: "koncová rohová parcela" },
      { label: "Súradnicový systém", value: "S-JTSK · EPSG:5514" },
    ],
    sourceIds: [SOURCES.cadastre.id, SOURCES.geometricPlan.id, SOURCES.terrain.id],
    note: "Oranžová hranica v 3D je presný aktuálny CP polygón ČÚZK. Dve cestné hrany komunikácie 6012/1 potvrdzujú koncovú rohovú polohu parcely; výmera z vrcholov sa zaokrúhľuje na evidovaných 753 m².",
  };
}

function SourceBadge({ kind }: { kind: SourceRecord["kind"] }) {
  const map: Record<SourceRecord["kind"], string> = {
    CURRENT_REGISTER: "AKTUÁLNY REGISTER",
    PROJECT_DESIGN: "PROJEKT",
    PROVIDER_CONTEXT: "KONTEXT",
    SCAN_DOCUMENT: "GEODETICKÝ PODKLAD",
    ARITHMETIC_DERIVATION: "ODVODENÉ",
    UNRESOLVED_AS_BUILT: "CHÝBA PODKLAD",
    CLIENT_REVISION: "REVÍZIA STAVEBNÍKA",
    DESIGN_PROPOSAL: "DIZAJNOVÝ NÁVRH",
  };
  return <span className={`source-badge ${kind.toLowerCase()}`}>{map[kind]}</span>;
}

export function TwinStudio() {
  const viewportRef = useRef<BabylonViewportHandle>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const explorerTriggerRef = useRef<HTMLButtonElement>(null);
  const inspectorTriggerRef = useRef<HTMLButtonElement>(null);
  const inspectorPanelRef = useRef<HTMLElement>(null);
  const isCompact = useSyncExternalStore(
    subscribeCompactLayout,
    getCompactLayoutSnapshot,
    getCompactLayoutServerSnapshot,
  );

  const [workspace, setWorkspace] = useState<WorkspaceMode>(
    DEFAULT_WORKSPACE_MODE,
  );
  const [movement, setMovement] = useState<NavigationMode>("orbit");
  const [foundations, setFoundations] = useState<readonly FoundationStrip[]>(FOUNDATIONS);
  const [selectionId, setSelectionId] = useState(DEFAULT_SELECTION_ID);
  const [visibleLayers, setVisibleLayers] = useState(DEFAULT_LAYER_VISIBILITY);
  const [search, setSearch] = useState("");
  const [explorerOpen, setExplorerOpen] = useState(false);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [inspectorTab, setInspectorTab] = useState<InspectorTab>("parameters");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [walkAvatarId, setWalkAvatarId] = useState<WalkAvatarId>("michelle");
  const [walkView, setWalkView] = useState<"first" | "third">("third");
  const [draftWidth, setDraftWidth] = useState("");
  const [inputError, setInputError] = useState("");
  const [history, setHistory] = useState<readonly HistoryItem[]>([]);

  const viewMode = viewModeForWorkspace(workspace);
  const chrome = chromeContract(workspace, movement);
  const overlayPanels = !chrome.dockedPanels || isCompact;
  const panelOpen = explorerOpen || inspectorOpen;
  const chromeVisible = useChromeVisibility({
    autoHide: chrome.autoHide,
    pinned: panelOpen || paletteOpen || helpOpen,
  });

  const detail = useMemo(
    () => getEntityDetail(selectionId, foundations),
    [selectionId, foundations],
  );

  const commands = useMemo(
    () =>
      buildCommands({
        workspace,
        movement,
        walkView,
        avatarId: walkAvatarId,
        rooms: INTERIOR_ROOMS.map((room) => ({
          id: room.id,
          number: room.number,
          name: room.name,
        })),
        avatars: WALK_AVATARS.map((avatar) => ({
          id: avatar.id,
          label: avatar.label,
          tagline: avatar.tagline,
        })),
        layers: LAYERS.map((layer) => ({
          id: layer.id,
          label: layer.label,
          source: layer.source,
        })),
        layerVisibility: visibleLayers,
        hasSelection: selectionId !== DEFAULT_SELECTION_ID,
      }),
    [workspace, movement, walkView, walkAvatarId, visibleLayers, selectionId],
  );

  const closeExplorer = () => {
    setExplorerOpen(false);
    requestAnimationFrame(() => explorerTriggerRef.current?.focus());
  };

  const openExplorer = () => {
    setInspectorOpen(false);
    setExplorerOpen(true);
  };

  const closeInspector = () => {
    setInspectorOpen(false);
    requestAnimationFrame(() => inspectorTriggerRef.current?.focus());
  };

  const openInspector = (tab: InspectorTab = "parameters") => {
    setExplorerOpen(false);
    setInspectorTab(tab);
    setInspectorOpen(true);
  };

  const dismissPanels = () => {
    const restoreFocus = inspectorOpen ? inspectorTriggerRef : explorerTriggerRef;
    setExplorerOpen(false);
    setInspectorOpen(false);
    requestAnimationFrame(() => restoreFocus.current?.focus());
  };

  const toggleFullscreen = () => {
    if (document.fullscreenElement) void document.exitFullscreen();
    else void document.documentElement.requestFullscreen();
  };

  const showCameraPreset = (preset: CameraPresetId) => {
    if (viewportRef.current?.isGarageCinematicActive()) return;
    if (preset === "parcels") {
      setVisibleLayers((current) =>
        current.cadastre ? current : { ...current, cadastre: true },
      );
    }
    // Tell the controller before React re-renders: a preset always lands in
    // orbit, and the camera must not be framed while the walker still owns it.
    setMovement("orbit");
    viewportRef.current?.setNavigationMode("orbit");
    viewportRef.current?.setCameraPreset(preset);
  };

  /** Walking needs the shell collision layer even if it was hidden earlier. */
  const ensureBuildingLayer = () =>
    setVisibleLayers((current) =>
      current.building ? current : { ...current, building: true },
    );

  const changeMovement = (next: NavigationMode) => {
    if (viewportRef.current?.isGarageCinematicActive()) return;
    setWorkspace((current) => workspaceForMovement(current, next));
    setMovement(next);
    if (next === "walk") {
      ensureBuildingLayer();
      setExplorerOpen(false);
      setInspectorOpen(false);
      viewportRef.current?.enterWalkthrough();
      return;
    }
    viewportRef.current?.setNavigationMode(next);
  };

  const enterRoom = (roomId: string) => {
    if (viewportRef.current?.isGarageCinematicActive()) return;
    setWorkspace("experience");
    setMovement("walk");
    ensureBuildingLayer();
    setExplorerOpen(false);
    setInspectorOpen(false);
    viewportRef.current?.enterWalkthrough(roomId);
  };

  const changeWorkspace = (next: WorkspaceMode) => {
    if (viewportRef.current?.isGarageCinematicActive()) return;
    if (next === workspace) return;
    const nextMovement = movementForWorkspace(next, movement);
    setWorkspace(next);
    setMovement(nextMovement);
    setExplorerOpen(false);
    setInspectorOpen(false);
    setHelpOpen(false);
    if (nextMovement !== movement) {
      viewportRef.current?.setNavigationMode(nextMovement);
    }
    // Each mode has a signature framing, so the switch reads as a real change
    // of intent rather than a restyle of the same picture.
    requestAnimationFrame(() =>
      viewportRef.current?.setCameraPreset(
        next === "documentation" ? "axonometric" : "garden",
      ),
    );
  };

  const toggleLayer = (layer: LayerId) => {
    if (movement === "walk" && layer === "building") return;
    setVisibleLayers((current) => ({ ...current, [layer]: !current[layer] }));
  };

  const select = (id: string) => {
    const selectedFromExplorer = overlayPanels && explorerOpen;
    setSelectionId(id);
    const selectedFoundation = foundations.find((foundation) => foundation.id === id);
    setDraftWidth(selectedFoundation?.widthMm.toString() ?? "");
    setInputError("");
    if (overlayPanels) setExplorerOpen(false);
    // While flying or walking, a click belongs to the scene. Panels would break
    // the sense of being inside the model.
    if (movement !== "orbit") return;
    setInspectorTab("parameters");
    setInspectorOpen(true);
    if (selectedFromExplorer) {
      requestAnimationFrame(() => inspectorPanelRef.current?.focus());
    }
  };

  const handleViewportNavigationModeChange = (next: NavigationMode) => {
    setMovement(next);
    setWorkspace((current) => workspaceForMovement(current, next));
    if (next === "walk") ensureBuildingLayer();
  };

  const runCommand = (command: TwinCommand) => {
    const { action } = command;
    switch (action.kind) {
      case "workspace":
        changeWorkspace(action.workspace);
        break;
      case "movement":
        changeMovement(action.movement);
        break;
      case "preset":
        showCameraPreset(action.preset);
        break;
      case "room":
        enterRoom(action.roomId);
        break;
      case "avatar":
        void viewportRef.current?.setWalkAvatar(action.avatarId);
        break;
      case "layer":
        toggleLayer(action.layer);
        break;
      case "recenter":
        viewportRef.current?.recoverWalkthrough();
        break;
      case "walk-view":
        viewportRef.current?.setWalkView(action.view);
        break;
      case "fullscreen":
        toggleFullscreen();
        break;
      case "help":
        setHelpOpen(true);
        break;
    }
  };

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.defaultPrevented) return;
      const target = event.target as HTMLElement | null;
      const isTyping =
        target?.tagName === "INPUT" || target?.tagName === "TEXTAREA";

      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setExplorerOpen(false);
        setInspectorOpen(false);
        setPaletteOpen((open) => !open);
        return;
      }
      if (isTyping || event.metaKey || event.ctrlKey || event.altKey) return;

      if (event.key.toLowerCase() === "m") {
        event.preventDefault();
        changeWorkspace(
          workspace === "documentation" ? "experience" : "documentation",
        );
        return;
      }
      if (event.key === "?") {
        event.preventDefault();
        setHelpOpen((open) => !open);
        return;
      }
      if (event.key !== "Escape") return;

      if (viewportRef.current?.isGarageCinematicActive()) {
        event.preventDefault();
        return;
      }
      event.preventDefault();
      if (paletteOpen) {
        setPaletteOpen(false);
        return;
      }
      if (helpOpen) {
        setHelpOpen(false);
        return;
      }
      if (panelOpen) {
        dismissPanels();
        return;
      }
      if (movement !== "orbit") {
        setMovement("orbit");
        viewportRef.current?.setNavigationMode("orbit");
        return;
      }
      setSelectionId(DEFAULT_SELECTION_ID);
      setDraftWidth("");
      setInputError("");
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  const applyWidth = () => {
    const foundation = detail.editableFoundation;
    if (!foundation) return;
    const parsed = Number(draftWidth);
    if (!Number.isInteger(parsed) || parsed < 300 || parsed > 1200) {
      setInputError("Zadajte celé číslo 300–1 200 mm.");
      return;
    }
    if (parsed === foundation.widthMm) {
      setInputError("");
      return;
    }
    try {
      setFoundations((current) => updateFoundationWidth(current, foundation.id, parsed));
      setHistory((current) => [
        ...current,
        {
          id: Date.now(),
          foundationId: foundation.id,
          beforeMm: foundation.widthMm,
          afterMm: parsed,
          at: new Intl.DateTimeFormat("sk-SK", {
            hour: "2-digit",
            minute: "2-digit",
          }).format(new Date()),
        },
      ]);
      setInputError("");
    } catch (error) {
      setInputError(error instanceof Error ? error.message : "Hodnota nie je platná.");
    }
  };

  const undoLast = () => {
    const last = history.at(-1);
    if (!last) return;
    setFoundations((current) => updateFoundationWidth(current, last.foundationId, last.beforeMm));
    setHistory((current) => current.slice(0, -1));
    if (selectionId === last.foundationId) setDraftWidth(last.beforeMm.toString());
  };

  const sourceRecords = detail.sourceIds
    .map(findSource)
    .filter((source): source is SourceRecord => Boolean(source));
  const query = search.trim().toLocaleLowerCase("sk");
  const matches = (value: string) => !query || value.toLocaleLowerCase("sk").includes(query);
  const visibleFoundations = foundations.filter((foundation) =>
    matches(`${foundation.id} ${foundation.label}`),
  );

  return (
    <main
      className="twin-shell"
      data-workspace={workspace}
      data-panels={overlayPanels ? "overlay" : "docked"}
    >
      <a className="skip-link" href="#scene-explorer">Preskočiť na prieskumník modelu</a>

      {chrome.appRails && (
        <header className="app-rail">
          <div className="rail-start">
            <button
              ref={explorerTriggerRef}
              className="rail-button"
              aria-label={`${explorerOpen ? "Zavrieť" : "Otvoriť"} prieskumník modelu`}
              aria-expanded={explorerOpen}
              onClick={explorerOpen ? closeExplorer : openExplorer}
            >
              <Menu size={19} />
            </button>
            <div className="brand">
              <div className="brand-mark" aria-hidden="true"><span /><span /><span /></div>
              <div className="brand-copy">
                <span>DIGITÁLNE DVOJČA</span>
                <strong>DOM 6012/26</strong>
              </div>
            </div>
          </div>
          <div className="rail-locator" aria-label="Lokalita projektu">
            <MapPin size={14} aria-hidden="true" />
            <span>Březí u Mikulova</span>
            <i aria-hidden="true" />
            <span>48.817716° N · 16.552789° E</span>
          </div>
          <div className="rail-end">
            <div className="rail-status" title="Zmeny sa neukladajú na server">
              <i aria-hidden="true" />
              <div><strong>NÁVRHOVÝ MODEL</strong><small>session-only</small></div>
            </div>
            <button
              className="rail-button"
              aria-label="Zobraziť pomoc a klávesové skratky"
              aria-expanded={helpOpen}
              onClick={() => setHelpOpen((open) => !open)}
            >
              <CircleHelp size={19} />
            </button>
            <button
              ref={inspectorTriggerRef}
              className="rail-button"
              aria-label={`${inspectorOpen ? "Zavrieť" : "Otvoriť"} detail vybraného objektu`}
              aria-expanded={inspectorOpen}
              onClick={inspectorOpen ? closeInspector : () => openInspector()}
            >
              <Info size={19} />
            </button>
          </div>
        </header>
      )}

      <button
        className="panel-scrim"
        data-active={overlayPanels && panelOpen}
        aria-label="Zavrieť otvorený panel"
        tabIndex={overlayPanels && panelOpen ? 0 : -1}
        onClick={dismissPanels}
      />

      <aside
        id="scene-explorer"
        className="scene-panel"
        data-open={explorerOpen}
        aria-label="Prieskumník digitálneho dvojčaťa"
        aria-hidden={overlayPanels ? !explorerOpen : undefined}
        inert={overlayPanels && !explorerOpen}
      >
        <div className="panel-head">
          <div><span className="micro-label">SCÉNA / 9 VRSTIEV</span><h1>Živý výkres</h1></div>
          <button className="panel-close" aria-label="Zavrieť prieskumník" onClick={closeExplorer}>
            <PanelLeftClose size={18} />
          </button>
        </div>
        <label className="panel-search">
          <Search size={16} aria-hidden="true" />
          <input
            ref={searchRef}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Hľadať objekt alebo sieť"
            aria-label="Hľadať objekt alebo sieť"
          />
          {search ? (
            <button aria-label="Vymazať vyhľadávanie" onClick={() => setSearch("")}><X size={15} /></button>
          ) : <kbd className="key">⌘K</kbd>}
        </label>

        <div className="scene-tree" role="tree" aria-label="Objekty modelu">
          {matches("parcela 6012/26 kataster") && (
            <button
              role="treeitem"
              aria-selected={selectionId === DEFAULT_SELECTION_ID}
              className="tree-item tree-root"
              onClick={() => select(DEFAULT_SELECTION_ID)}
            >
              <span className="entity-token cadastral">KN</span>
              <span><strong>Parcela 6012/26</strong><small>ČÚZK · 753 m²</small></span>
              <ShieldCheck size={15} aria-label="Aktuálny register" />
            </button>
          )}

          <details open>
            <summary><Map size={15} /><span>Areál a komunikácia</span><small>7</small></summary>
            <div role="group">
              {matches("miestna komunikácia 6012/1") && (
                <button role="treeitem" aria-selected={selectionId === "ROAD-6012-1"} className="tree-item" onClick={() => select("ROAD-6012-1")}>
                  <span className="entity-token road">UL</span><span><strong>Miestna komunikácia</strong><small>parc. 6012/1 · dve hrany</small></span>
                </button>
              )}
              {matches("dom rodinný so 01") && (
                <button role="treeitem" aria-selected={selectionId === HOUSE.id} className="tree-item" onClick={() => select(HOUSE.id)}>
                  <span className="entity-token house">RD</span><span><strong>Rodinný dom</strong><small>SO 01 · návrh</small></span>
                </button>
              )}
              {matches("terasy spevnené plochy") && (
                <div className="tree-static"><span className="entity-token terrain">SP</span><span><strong>Spevnené plochy</strong><small>C3/D1 · návrh</small></span></div>
              )}
              {matches(`${GARDEN_POOL.label} bazén dvor terasa`) && (
                <button role="treeitem" aria-selected={selectionId === GARDEN_POOL.id} className="tree-item" onClick={() => select(GARDEN_POOL.id)}>
                  <span className="entity-token utility" style={{ "--entity-color": "#3ebbe0" } as CSSProperties}>BZ</span><span><strong>{GARDEN_POOL.label}</strong><small>vodná plocha {fmt(GARDEN_POOL.waterAreaM2)} m² · v rohu terás</small></span>
                </button>
              )}
              {matches(`${POOL_TECHNOLOGY_SHAFT.label} šachta rebrík filter čerpadlo poistky ističe`) && (
                <button role="treeitem" aria-selected={selectionId === POOL_TECHNOLOGY_SHAFT.id} className="tree-item" onClick={() => select(POOL_TECHNOLOGY_SHAFT.id)}>
                  <span className="entity-token utility" style={{ "--entity-color": "#8d9496" } as CSSProperties}>ŠB</span><span><strong>{POOL_TECHNOLOGY_SHAFT.label}</strong><small>poklop · rebrík · filtrácia · elektro</small></span>
                </button>
              )}
              {matches("plot oplotenie súkromná záhrada") && (
                <button role="treeitem" aria-selected={selectionId === SITE_FENCE.id} className="tree-item" onClick={() => select(SITE_FENCE.id)}>
                  <span className="entity-token house">OP</span><span><strong>Oplotenie záhrady</strong><small>náčrt stavebníka · návrh</small></span>
                </button>
              )}
              {matches("brána teleskopická záhrada") && (
                <button role="treeitem" aria-selected={selectionId === SITE_FENCE.vehicleGate.id} className="tree-item" onClick={() => select(SITE_FENCE.vehicleGate.id)}>
                  <span className="entity-token house">BR</span><span><strong>Teleskopická brána</strong><small>4 200 mm · zelený náčrt</small></span>
                </button>
              )}
            </div>
          </details>

          <details open>
            <summary><Building2 size={15} /><span>Základy D1.1.001</span><small>{foundations.length}</small></summary>
            <div role="group" className="foundation-list">
              {visibleFoundations.map((foundation) => (
                <button
                  key={foundation.id}
                  role="treeitem"
                  aria-selected={selectionId === foundation.id}
                  className="tree-item"
                  onClick={() => select(foundation.id)}
                >
                  <span className="entity-token foundation">{foundation.id.replace("F-", "")}</span>
                  <span><strong>{foundation.id}</strong><small>{foundation.widthMm} × {foundation.heightMm} mm</small></span>
                </button>
              ))}
            </div>
          </details>

          <details open>
            <summary><Cable size={15} /><span>Inžinierske siete</span><small>7</small></summary>
            <div role="group">
              {[
                ["UTIL-WATER", "VO", "Vodovodná prípojka", "IO 03", "water"],
                ["UTIL-SEWER", "SK", "Splašková kanalizácia", "IO 02", "sewer"],
                ["OBJ-RAIN-TANK", "DA", "Dažďová voda + vsakovanie", "IO 01", "rainwater"],
                ["UTIL-ELECTRICITY", "NN", "Elektrina NN", "C3 · konflikt", "electricity"],
                ["UTIL-WATER-STREET", "IS", "Verejné siete v komunikácii", "DMVS", "contextNetworks"],
              ].filter(([, , label]) => matches(label)).map(([id, code, label, source, layer]) => (
                <button key={id} role="treeitem" aria-selected={selectionId === id} className="tree-item" onClick={() => select(id)}>
                  <span className="entity-token utility" style={{ "--entity-color": LAYERS.find((item) => item.id === layer)?.color } as CSSProperties}>{code}</span>
                  <span><strong>{label}</strong><small>{source}</small></span>
                </button>
              ))}
            </div>
          </details>
        </div>

        <section className="layer-block" aria-labelledby="layers-heading">
          <div className="section-heading"><span id="layers-heading">VIDITEĽNOSŤ VRSTIEV</span><Layers3 size={15} /></div>
          <div>
            {LAYERS.map((layer) => (
              <button
                key={layer.id}
                className="layer-item"
                aria-pressed={visibleLayers[layer.id]}
                onClick={() => toggleLayer(layer.id)}
              >
                <i style={{ backgroundColor: layer.color, color: layer.color }} />
                <span>{layer.label}<small>{layer.source}</small></span>
                {visibleLayers[layer.id] ? <Eye size={15} /> : <EyeOff size={15} />}
              </button>
            ))}
          </div>
        </section>
      </aside>

      <section
        className="viewport"
        data-workspace={workspace}
        aria-label="3D pracovný priestor"
      >
        <BabylonViewport
          ref={viewportRef}
          foundations={foundations}
          selectionId={selectionId}
          visibleLayers={visibleLayers}
          viewMode={viewMode}
          navigationMode={movement}
          workspace={workspace}
          chrome={chrome}
          chromeVisible={chromeVisible}
          helpOpen={helpOpen}
          onSelect={select}
          onNavigationModeChange={handleViewportNavigationModeChange}
          onWorkspaceChange={changeWorkspace}
          onParcelOverviewRequest={() =>
            setVisibleLayers((current) =>
              current.cadastre ? current : { ...current, cadastre: true },
            )
          }
          onCameraPreset={showCameraPreset}
          onOpenPalette={() => setPaletteOpen(true)}
          onToggleHelp={() => setHelpOpen((open) => !open)}
          onWalkAvatarChange={setWalkAvatarId}
          onWalkViewChange={setWalkView}
        />
      </section>

      <aside
        ref={inspectorPanelRef}
        className="inspector"
        data-open={inspectorOpen}
        aria-label="Detail vybraného objektu"
        aria-hidden={overlayPanels ? !inspectorOpen : undefined}
        inert={overlayPanels && !inspectorOpen}
        tabIndex={-1}
      >
        <div className="inspector-hero">
          <span className="selection-code" data-tone={detail.statusTone}>{detail.code}</span>
          <div><span className="micro-label">{detail.eyebrow}</span><h2>{detail.title}</h2><p>{detail.subtitle}</p></div>
          <button className="panel-close" aria-label="Zavrieť detail" onClick={closeInspector}><PanelRightClose size={18} /></button>
        </div>
        <div className="evidence-status" data-tone={detail.statusTone}>
          {detail.statusTone === "current" ? <ShieldCheck size={15} /> : detail.statusTone === "warning" ? <TriangleAlert size={15} /> : <Database size={15} />}
          <span>{detail.status}</span>
          <button aria-label="Zamerať objekt v 3D" onClick={() => showCameraPreset("focus")}><Focus size={16} /></button>
        </div>
        <div className="inspector-tabs" role="tablist" aria-label="Detail a zdroje">
          <button id="tab-parameters" role="tab" aria-controls="panel-parameters" aria-selected={inspectorTab === "parameters"} onClick={() => setInspectorTab("parameters")}>Parametre</button>
          <button id="tab-sources" role="tab" aria-controls="panel-sources" aria-selected={inspectorTab === "sources"} onClick={() => setInspectorTab("sources")}>Zdroje <span>{sourceRecords.length}</span></button>
        </div>

        <div className="inspector-scroll">
          {inspectorTab === "parameters" ? (
            <div id="panel-parameters" role="tabpanel" aria-labelledby="tab-parameters">
              <section className="inspector-section">
                <div className="section-heading"><span>{detail.statusTone === "current" ? "OVERENÉ ÚDAJE" : detail.statusTone === "design" ? "NÁVRHOVÉ ÚDAJE" : "KONTEXTOVÉ ÚDAJE"}</span><span>mm / m² / m³</span></div>
                <dl className="property-list">
                  {detail.rows.map((row) => (
                    <div key={row.label}><dt>{row.label}</dt><dd>{row.value}{row.unit && <small>{row.unit}</small>}</dd></div>
                  ))}
                </dl>
              </section>

              {detail.editableFoundation && (
                <section className="inspector-section edit-section">
                  <div className="section-heading"><span>PARAMETRICKÁ ÚPRAVA</span><span>SESSION</span></div>
                  <label className="number-control" data-error={Boolean(inputError)}>
                    <span>Šírka pásu</span>
                    <div><input type="number" inputMode="numeric" min="300" max="1200" step="50" value={draftWidth} onChange={(event) => setDraftWidth(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") applyWidth(); }} aria-invalid={Boolean(inputError)} aria-describedby="width-hint" /><em>mm</em></div>
                  </label>
                  <p id="width-hint" className="field-message" data-error={Boolean(inputError)}>{inputError || "Zmena prepočíta 3D geometriu aj objem jedným krokom."}</p>
                  <div className="edit-actions">
                    <button className="apply-button" onClick={applyWidth}>Použiť zmenu</button>
                    <button className="undo-button" disabled={!history.length} onClick={undoLast}><Undo2 size={15} /> Späť</button>
                  </div>
                  {history.length > 0 && <p className="history-note">Posledná zmena: {history.at(-1)?.foundationId} · {history.at(-1)?.beforeMm} → {history.at(-1)?.afterMm} mm · {history.at(-1)?.at}</p>}
                </section>
              )}

              <section className="inspector-section insight-section">
                <div className="section-heading"><span>INTERPRETÁCIA</span><Info size={14} /></div>
                <p>{detail.note}</p>
              </section>
            </div>
          ) : (
            <section id="panel-sources" className="source-list" role="tabpanel" aria-labelledby="tab-sources">
              {sourceRecords.map((source) => (
                <article key={source.id} className="source-card" data-warning={source.kind === "UNRESOLVED_AS_BUILT"}>
                  <div><SourceBadge kind={source.kind} />{source.href && <a href={source.href} target="_blank" rel="noreferrer" aria-label={`Otvoriť zdroj ${source.title}`}><ChevronRight size={16} /></a>}</div>
                  <h3>{source.title}</h3>
                  <p>{source.detail}</p>
                  <dl><div><dt>Dátum</dt><dd>{source.date}</dd></div>{source.page && <div><dt>Strana</dt><dd>{source.page}</dd></div>}{source.scale && <div><dt>Mierka</dt><dd>{source.scale}</dd></div>}</dl>
                </article>
              ))}
            </section>
          )}
        </div>
      </aside>

      {chrome.appRails && (
        <footer className="evidence-rail" aria-label="Stav dátových zdrojov">
          <button type="button" className="evidence-rail-title" aria-label="Otvoriť zdroje vybraného objektu" onClick={() => openInspector("sources")}><Database size={15} /><span>DÁTOVÁ STOPA</span></button>
          {/* `data-drop` is the order in which a fact gives up its place when
              the rail runs short. The registered area and the missing-as-built
              warning carry no order: they are never dropped. */}
          <div className="evidence-facts">
            <span className="fact" data-tone="current"><i />ČÚZK <strong>753 m²</strong><small>aktuálne</small></span>
            <span className="fact" data-tone="design" data-drop="3"><i />C3 <strong>28. 4. 2026</strong><small>projekt</small></span>
            <span className="fact" data-tone="current" data-drop="2"><i />DMVS <strong>voda + stoka</strong><small>verejné dáta</small></span>
            <span className="fact" data-tone="context" data-drop="1"><i />DMR 5G <strong>184,087 m</strong><small>Bpv</small></span>
            <span className="fact" data-tone="warning"><TriangleAlert size={13} />Skutočné prípojky <strong>nepotvrdené</strong></span>
          </div>
          <div className="coordinate-readout"><span>LOCAL</span><strong>X → pozdĺž komunikácie</strong><small>Y → do parcely · Z ↑ výška</small></div>
        </footer>
      )}

      {paletteOpen && (
        <CommandPalette
          commands={commands}
          onRun={runCommand}
          onClose={() => setPaletteOpen(false)}
        />
      )}

      <div className="sr-only" aria-live="polite">Vybraný objekt: {detail.title}. {detail.status}.</div>
    </main>
  );
}
