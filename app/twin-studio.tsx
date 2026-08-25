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
  Footprints,
  Fullscreen,
  House,
  Info,
  Layers3,
  Map,
  MapPin,
  Menu,
  Orbit,
  Plane,
  PanelLeftClose,
  PanelRightClose,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Trees,
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
import type { CameraPreset } from "@/lib/babylon-scene";
import type { NavigationMode } from "@/lib/twin-viewport-contract";
import {
  DEFAULT_LAYER_VISIBILITY,
  FOUNDATIONS,
  GARDEN_POOL,
  HOUSE,
  LAYERS,
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
  type ViewMode,
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
      status: "Rozmer a dotyk terasy podľa revízie · koordinačný návrh",
      statusTone: "design",
      rows: [
        { label: "Vodná plocha", value: `${fmt(GARDEN_POOL.waterLengthMm)} × ${fmt(GARDEN_POOL.waterWidthMm)}`, unit: "mm" },
        { label: "Plocha vody", value: fmt(GARDEN_POOL.waterAreaM2), unit: "m²" },
        { label: "Svetlý lem", value: fmt(GARDEN_POOL.copingWidthMm), unit: "mm" },
        { label: "Navrhovaná hĺbka", value: fmt(GARDEN_POOL.proposedWaterDepthMm), unit: "mm" },
        { label: "Medzera lemu od terasy", value: fmt(GARDEN_POOL.terraceConnection.planGapMm), unit: "mm" },
        { label: "Dĺžka dotyku s terasou", value: fmt(GARDEN_POOL.terraceConnection.contactLengthMm), unit: "mm" },
        { label: "Odstup od najbližšieho dažďového potrubia", value: fmt(GARDEN_POOL.modelledClearancesMm.closestRainPipeShell), unit: "mm" },
        { label: "Odstup od plášťa dažďovej nádrže", value: fmt(GARDEN_POOL.modelledClearancesMm.rainTankShell), unit: "mm" },
        { label: "Orientácia", value: "dlhšia strana rovnobežne s terasou" },
      ],
      sourceIds: GARDEN_POOL.sourceIds,
      note: "Modelovaný variant má po dorovnaní do vnútorného rohu L vodnú plochu 5,6 × 3,0 m, teda o 0,6 m dlhšiu než posledná doložená požiadavka 5,0 × 3,0 m. Lem sa bez medzery dotýka hlavnej aj bočnej terasy a všetky tri plochy majú spoločnú hornú úroveň. Dažďová trasa je predbežne odklonená; od potrubia zostáva približne 0,63 m a od plášťa nádrže 1,787 m. Rozmer variantu, trasu, nádrž, technológiu aj skutočné vedenie potrubí treba pred realizáciou potvrdiť a odborne skoordinovať.",
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
      note: "3D hmota vychádza z neskoršieho pôdorysu D1.1.002 bez zrkadlenia: garážový koniec je na lokálnom −X a obytné krídlo na +X. Umiestnenie do parcely je odvodené zarovnaním pravého okraja, zalomenia a hornej hrany na georeferencovanú C3; nejde o vytyčovací podklad. Žltá terasa je zatiaľ samostatná georeferencovaná revízia C3 s plochou 53 m², nie zlúčená plocha 84,35 m² zo súpisu D1.",
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
    id: "PARCEL-6012/26",
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
  const flightTriggerRef = useRef<HTMLButtonElement>(null);
  const isCompact = useSyncExternalStore(
    subscribeCompactLayout,
    getCompactLayoutSnapshot,
    getCompactLayoutServerSnapshot,
  );
  const [foundations, setFoundations] = useState<readonly FoundationStrip[]>(FOUNDATIONS);
  const [selectionId, setSelectionId] = useState("PARCEL-6012/26");
  const [visibleLayers, setVisibleLayers] = useState(DEFAULT_LAYER_VISIBILITY);
  const [viewMode, setViewMode] = useState<ViewMode>("realistic");
  const [navigationMode, setNavigationMode] =
    useState<NavigationMode>("orbit");
  const [search, setSearch] = useState("");
  const [explorerOpen, setExplorerOpen] = useState(false);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [inspectorTab, setInspectorTab] = useState<InspectorTab>("parameters");
  const [helpOpen, setHelpOpen] = useState(false);
  const [draftWidth, setDraftWidth] = useState("");
  const [inputError, setInputError] = useState("");
  const [history, setHistory] = useState<readonly HistoryItem[]>([]);
  const useOverlayPanels = isCompact || viewMode === "realistic";

  const detail = useMemo(
    () => getEntityDetail(selectionId, foundations),
    [selectionId, foundations],
  );

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.defaultPrevented) return;
      const target = event.target as HTMLElement | null;
      const isTyping =
        target?.tagName === "INPUT" || target?.tagName === "TEXTAREA";
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setInspectorOpen(false);
        setExplorerOpen(true);
        requestAnimationFrame(() => searchRef.current?.focus());
      }
      if (event.key === "Escape" && !isTyping) {
        if (viewportRef.current?.isGarageCinematicActive()) {
          event.preventDefault();
          return;
        }
        if (navigationMode === "flight" || navigationMode === "walk") {
          event.preventDefault();
          setNavigationMode("orbit");
          viewportRef.current?.setNavigationMode("orbit");
          requestAnimationFrame(() => flightTriggerRef.current?.focus());
          return;
        }
        const restoreFocus = inspectorOpen
          ? inspectorTriggerRef
          : explorerOpen
            ? explorerTriggerRef
            : null;
        setHelpOpen(false);
        if (explorerOpen || inspectorOpen) {
          setExplorerOpen(false);
          setInspectorOpen(false);
          requestAnimationFrame(() => restoreFocus?.current?.focus());
        } else {
          setSelectionId("PARCEL-6012/26");
          setDraftWidth("");
          setInputError("");
        }
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [explorerOpen, inspectorOpen, navigationMode]);

  const openExplorer = () => {
    setInspectorOpen(false);
    setExplorerOpen(true);
  };

  const closeExplorer = () => {
    setExplorerOpen(false);
    requestAnimationFrame(() => explorerTriggerRef.current?.focus());
  };

  const openInspector = () => {
    setExplorerOpen(false);
    setInspectorOpen(true);
  };

  const closeInspector = () => {
    setInspectorOpen(false);
    requestAnimationFrame(() => inspectorTriggerRef.current?.focus());
  };

  const dismissPanels = () => {
    const restoreFocus = inspectorOpen ? inspectorTriggerRef : explorerTriggerRef;
    setExplorerOpen(false);
    setInspectorOpen(false);
    requestAnimationFrame(() => restoreFocus.current?.focus());
  };

  const select = (id: string) => {
    const selectedFromExplorer = useOverlayPanels && explorerOpen;
    setSelectionId(id);
    const selectedFoundation = foundations.find((foundation) => foundation.id === id);
    setDraftWidth(selectedFoundation?.widthMm.toString() ?? "");
    setInputError("");
    if (useOverlayPanels) setExplorerOpen(false);
    setInspectorOpen(true);
    if (selectedFromExplorer) {
      requestAnimationFrame(() => inspectorPanelRef.current?.focus());
    }
  };

  const toggleLayer = (layer: LayerId) => {
    if (navigationMode === "walk" && layer === "building") return;
    setVisibleLayers((current) => ({ ...current, [layer]: !current[layer] }));
  };

  const showCameraPreset = (preset: CameraPreset) => {
    if (viewportRef.current?.isGarageCinematicActive()) return;
    if (preset === "parcels") {
      setVisibleLayers((current) =>
        current.cadastre ? current : { ...current, cadastre: true },
      );
    }
    setNavigationMode("orbit");
    viewportRef.current?.setCameraPreset(preset);
  };

  const handleViewportNavigationModeChange = (next: NavigationMode) => {
    setNavigationMode(next);
    if (next === "walk") {
      setVisibleLayers((current) =>
        current.building ? current : { ...current, building: true },
      );
      setViewMode("realistic");
    }
  };

  const toggleFlight = () => {
    if (viewportRef.current?.isGarageCinematicActive()) return;
    const next = navigationMode === "flight" ? "orbit" : "flight";
    setNavigationMode(next);
    viewportRef.current?.setNavigationMode(next);
  };

  const toggleWalk = () => {
    if (viewportRef.current?.isGarageCinematicActive()) return;
    const next = navigationMode === "walk" ? "orbit" : "walk";
    setNavigationMode(next);
    if (next === "walk") {
      // Walkthrough always needs both the shell collision layer and the
      // realistic fit-out. This also recovers from a previously hidden house.
      setVisibleLayers((current) =>
        current.building ? current : { ...current, building: true },
      );
      setViewMode("realistic");
      viewportRef.current?.enterWalkthrough();
    } else {
      viewportRef.current?.setNavigationMode("orbit");
    }
  };

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
    <main className={`twin-shell ${viewMode === "realistic" ? "is-presentation" : ""}`}>
      <a className="skip-link" href="#scene-explorer">Preskočiť na prieskumník modelu</a>
      <header className="top-rail">
        <div className="top-rail-start">
          <button
            ref={explorerTriggerRef}
            className="rail-icon mobile-panel-trigger"
            aria-label={`${explorerOpen ? "Zavrieť" : "Otvoriť"} prieskumník modelu`}
            aria-expanded={explorerOpen}
            onClick={explorerOpen ? closeExplorer : openExplorer}
          >
            <Menu size={19} />
          </button>
          <div className="brand-mark" aria-hidden="true"><span /><span /><span /></div>
          <div className="brand-copy">
            <span>DIGITÁLNE DVOJČA</span>
            <strong>DOM 6012/26</strong>
          </div>
        </div>
        <div className="project-locator" aria-label="Lokalita projektu">
          <MapPin size={15} aria-hidden="true" />
          <span>Březí u Mikulova</span>
          <i />
          <span>48.817716° N · 16.552789° E</span>
        </div>
        <div className="top-rail-end">
          <div className="save-state" title="Zmeny sa neukladajú na server">
            <span />
            <div><strong>NÁVRHOVÝ MODEL</strong><small>session-only</small></div>
          </div>
          <button
            className="rail-icon"
            aria-label="Zobraziť pomoc a klávesové skratky"
            aria-expanded={helpOpen}
            onClick={() => setHelpOpen((open) => !open)}
          >
            <CircleHelp size={19} />
          </button>
          <button
            ref={inspectorTriggerRef}
            className="rail-icon mobile-panel-trigger"
            aria-label={`${inspectorOpen ? "Zavrieť" : "Otvoriť"} detail vybraného objektu`}
            aria-expanded={inspectorOpen}
            onClick={inspectorOpen ? closeInspector : openInspector}
          >
            <Info size={19} />
          </button>
        </div>
      </header>

      <button
        className={`panel-scrim ${explorerOpen || inspectorOpen ? "is-active" : ""}`}
        aria-label="Zavrieť otvorený panel"
        onClick={dismissPanels}
      />

      <aside
        id="scene-explorer"
        className={`scene-panel ${explorerOpen ? "panel-open" : ""}`}
        aria-label="Prieskumník digitálneho dvojčaťa"
        aria-hidden={useOverlayPanels ? !explorerOpen : undefined}
        inert={useOverlayPanels && !explorerOpen}
      >
        <div className="panel-header">
          <div><span className="micro-label">SCÉNA / 9 VRSTIEV</span><h1>Živý výkres</h1></div>
          <button className="panel-close" aria-label="Zavrieť prieskumník" onClick={closeExplorer}>
            <PanelLeftClose size={18} />
          </button>
        </div>
        <label className="model-search">
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
          ) : <kbd>⌘K</kbd>}
        </label>

        <div className="scene-tree" role="tree" aria-label="Objekty modelu">
          {matches("parcela 6012/26 kataster") && (
            <button
              role="treeitem"
              aria-selected={selectionId === "PARCEL-6012/26"}
              className={`tree-object root-object ${selectionId === "PARCEL-6012/26" ? "selected" : ""}`}
              onClick={() => select("PARCEL-6012/26")}
            >
              <span className="entity-token cadastral">KN</span>
              <span><strong>Parcela 6012/26</strong><small>ČÚZK · 753 m²</small></span>
              <ShieldCheck size={15} aria-label="Aktuálny register" />
            </button>
          )}

          <details open>
            <summary><Map size={15} /><span>Areál a komunikácia</span><small>6</small></summary>
            <div role="group">
              {matches("miestna komunikácia 6012/1") && (
                <button role="treeitem" aria-selected={selectionId === "ROAD-6012-1"} className={`tree-object ${selectionId === "ROAD-6012-1" ? "selected" : ""}`} onClick={() => select("ROAD-6012-1")}>
                  <span className="entity-token road">UL</span><span><strong>Miestna komunikácia</strong><small>parc. 6012/1 · dve hrany</small></span>
                </button>
              )}
              {matches("dom rodinný so 01") && (
                <button role="treeitem" aria-selected={selectionId === HOUSE.id} className={`tree-object ${selectionId === HOUSE.id ? "selected" : ""}`} onClick={() => select(HOUSE.id)}>
                  <span className="entity-token house">RD</span><span><strong>Rodinný dom</strong><small>SO 01 · návrh</small></span>
                </button>
              )}
              {matches("terasy spevnené plochy") && (
                <div className="tree-static"><span className="entity-token terrain">SP</span><span><strong>Spevnené plochy</strong><small>C3/D1 · návrh</small></span></div>
              )}
              {matches(`${GARDEN_POOL.label} bazén dvor terasa`) && (
                <button role="treeitem" aria-selected={selectionId === GARDEN_POOL.id} className={`tree-object ${selectionId === GARDEN_POOL.id ? "selected" : ""}`} onClick={() => select(GARDEN_POOL.id)}>
                  <span className="entity-token utility" style={{ "--entity-color": "#3ebbe0" } as CSSProperties}>BZ</span><span><strong>{GARDEN_POOL.label}</strong><small>vodná plocha {fmt(GARDEN_POOL.waterAreaM2)} m² · v rohu terás</small></span>
                </button>
              )}
              {matches("plot oplotenie súkromná záhrada") && (
                <button role="treeitem" aria-selected={selectionId === SITE_FENCE.id} className={`tree-object ${selectionId === SITE_FENCE.id ? "selected" : ""}`} onClick={() => select(SITE_FENCE.id)}>
                  <span className="entity-token house">OP</span><span><strong>Oplotenie záhrady</strong><small>náčrt stavebníka · návrh</small></span>
                </button>
              )}
              {matches("brána teleskopická záhrada") && (
                <button role="treeitem" aria-selected={selectionId === SITE_FENCE.vehicleGate.id} className={`tree-object ${selectionId === SITE_FENCE.vehicleGate.id ? "selected" : ""}`} onClick={() => select(SITE_FENCE.vehicleGate.id)}>
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
                  className={`tree-object ${selectionId === foundation.id ? "selected" : ""}`}
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
                <button key={id} role="treeitem" aria-selected={selectionId === id} className={`tree-object ${selectionId === id ? "selected" : ""}`} onClick={() => select(id)}>
                  <span className="entity-token utility" style={{ "--entity-color": LAYERS.find((item) => item.id === layer)?.color } as CSSProperties}>{code}</span>
                  <span><strong>{label}</strong><small>{source}</small></span>
                </button>
              ))}
            </div>
          </details>
        </div>

        <section className="layer-control" aria-labelledby="layers-heading">
          <div className="section-heading"><span id="layers-heading">VIDITEĽNOSŤ VRSTIEV</span><Layers3 size={15} /></div>
          <div className="layer-list">
            {LAYERS.map((layer) => (
              <button
                key={layer.id}
                className={visibleLayers[layer.id] ? "is-visible" : ""}
                aria-pressed={visibleLayers[layer.id]}
                onClick={() => toggleLayer(layer.id)}
              >
                <i style={{ backgroundColor: layer.color }} />
                <span>{layer.label}<small>{layer.source}</small></span>
                {visibleLayers[layer.id] ? <Eye size={15} /> : <EyeOff size={15} />}
              </button>
            ))}
          </div>
        </section>
      </aside>

      <section className={`viewport ${viewMode === "realistic" ? "is-realistic" : ""} ${navigationMode === "flight" ? "is-flight" : ""} ${navigationMode === "walk" ? "is-flight is-walk" : ""}`} aria-label="3D pracovný priestor">
        <BabylonViewport
          ref={viewportRef}
          foundations={foundations}
          selectionId={selectionId}
          visibleLayers={visibleLayers}
          viewMode={viewMode}
          navigationMode={navigationMode}
          onSelect={select}
          onNavigationModeChange={handleViewportNavigationModeChange}
          onParcelOverviewRequest={() =>
            setVisibleLayers((current) =>
              current.cadastre ? current : { ...current, cadastre: true },
            )
          }
        />

        <div className="truth-card">
          <div className="truth-live"><span /> AKTUÁLNY KATASTER · ROHOVÁ</div>
          <strong>6012/26</strong>
          <div><span>753 m²</span><i /><span>EPSG:5514</span></div>
          <small>ČÚZK · overené 24. 8. 2026</small>
        </div>

        <div className="camera-dock" role="toolbar" aria-label="Kamera a navigácia">
          <button aria-label="Záhradný prezentačný pohľad" aria-keyshortcuts="4" onClick={() => showCameraPreset("garden")}><Trees size={17} /><span>Záhrada</span><kbd>4</kbd></button>
          <button aria-label="Prehľad parciel v mojom rade a oproti" aria-keyshortcuts="5" onClick={() => showCameraPreset("parcels")}><MapPin size={17} /><span>Parcely</span><kbd>5</kbd></button>
          <button aria-label="Axonometrický pohľad" aria-keyshortcuts="1" onClick={() => showCameraPreset("axonometric")}><Orbit size={17} /><span>Axonometria</span><kbd>1</kbd></button>
          <button aria-label="Pôdorysný pohľad" aria-keyshortcuts="2" onClick={() => showCameraPreset("top")}><Map size={17} /><span>Pôdorys</span><kbd>2</kbd></button>
          <button aria-label="Pohľad od ulice" aria-keyshortcuts="3" onClick={() => showCameraPreset("street")}><House size={17} /><span>Od ulice</span><kbd>3</kbd></button>
          <button
            ref={flightTriggerRef}
            className={navigationMode === "flight" ? "active" : ""}
            aria-label={navigationMode === "flight" ? "Ukončiť voľný 3D prelet" : "Spustiť voľný 3D prelet"}
            aria-pressed={navigationMode === "flight"}
            aria-keyshortcuts="H"
            onClick={toggleFlight}
          ><Plane size={17} /><span>Prelet</span><kbd>H</kbd></button>
          <button
            className={navigationMode === "walk" ? "active" : ""}
            aria-label={navigationMode === "walk" ? "Ukončiť prechádzku interiérom" : "Prejsť sa interiérom domu"}
            aria-pressed={navigationMode === "walk"}
            aria-keyshortcuts="G"
            onClick={toggleWalk}
          ><Footprints size={17} /><span>Interiér</span><kbd>G</kbd></button>
          <button aria-label="Zamerať vybraný objekt" aria-keyshortcuts="F" onClick={() => showCameraPreset("focus")}><Focus size={17} /><span>Výber</span><kbd>F</kbd></button>
          <button
            aria-label="Zobraziť na celej obrazovke"
            onClick={() => {
              if (document.fullscreenElement) void document.exitFullscreen();
              else void document.documentElement.requestFullscreen();
            }}
          ><Fullscreen size={17} /><span className="visually-hidden">Celá obrazovka</span></button>
        </div>

        <div className="view-mode" role="group" aria-label="Režim zobrazenia">
          <button className={viewMode === "technical" ? "active" : ""} aria-pressed={viewMode === "technical"} onClick={() => {
            setViewMode("technical");
            setNavigationMode("orbit");
            setExplorerOpen(false);
            setInspectorOpen(false);
            requestAnimationFrame(() => showCameraPreset("axonometric"));
          }}>
            <SlidersHorizontal size={15} /> Technický
          </button>
          <button className={viewMode === "realistic" ? "active" : ""} aria-pressed={viewMode === "realistic"} onClick={() => {
            setViewMode("realistic");
            setNavigationMode("orbit");
            setExplorerOpen(false);
            setInspectorOpen(false);
            requestAnimationFrame(() => showCameraPreset("garden"));
          }}>
            <House size={15} /> Realita
          </button>
        </div>

        <div className="north-compass" aria-label="Smer kladnej osi Y lokálneho pôdorysu">
          <span>Y</span><i /><small>+ do parcely</small>
        </div>

        <div className="viewport-legend" aria-label="Legenda dôvery dát">
          <span><i className="legend-current" />register</span>
          <span><i className="legend-design" />projekt</span>
          <span><i className="legend-gap" />chýba as-built</span>
        </div>

        {viewMode === "realistic" && (
          <div className="visualization-note">
            <Trees size={13} /> D1 architektúra · ČÚZK parcelný kontext · ilustračná vegetácia
          </div>
        )}

        {helpOpen && (
          <aside className="shortcut-card" aria-label="Ovládanie modelu">
            <div><strong>Ovládanie modelu</strong><button aria-label="Zavrieť pomoc" onClick={() => setHelpOpen(false)}><X size={16} /></button></div>
            <dl>
              <div><dt>Orbit</dt><dd>ťahanie / 1 prst</dd></div>
              <div><dt>Posun a zoom</dt><dd>pravé / koliesko / pinch</dd></div>
              <div><dt>Pohľady</dt><dd>1 · 2 · 3 · 4 · 5 · F</dd></div>
              <div><dt>Voľný prelet</dt><dd>H · potom WASD</dd></div>
              <div><dt>Výška preletu</dt><dd>Q / E</dd></div>
              <div><dt>Dvere a dvierka v prechádzke</dt><dd>E · dotyk na výzvu</dd></div>
              <div><dt>Rýchlosť</dt><dd>Shift turbo · Alt presne</dd></div>
              <div><dt>Ukončiť prelet</dt><dd>Esc</dd></div>
            </dl>
          </aside>
        )}

        <button className="mobile-explorer-button" onClick={openExplorer}><Layers3 size={18} /> Vrstvy</button>
      </section>

      <aside
        ref={inspectorPanelRef}
        className={`inspector ${inspectorOpen ? "panel-open" : ""}`}
        aria-label="Detail vybraného objektu"
        aria-hidden={useOverlayPanels ? !inspectorOpen : undefined}
        inert={useOverlayPanels && !inspectorOpen}
        tabIndex={-1}
      >
        <div className="inspector-hero">
          <span className={`selection-code ${detail.statusTone}`}>{detail.code}</span>
          <div><span className="micro-label">{detail.eyebrow}</span><h2>{detail.title}</h2><p>{detail.subtitle}</p></div>
          <button className="panel-close" aria-label="Zavrieť detail" onClick={closeInspector}><PanelRightClose size={18} /></button>
        </div>
        <div className={`evidence-status ${detail.statusTone}`}>
          {detail.statusTone === "current" ? <ShieldCheck size={15} /> : detail.statusTone === "warning" ? <TriangleAlert size={15} /> : <Database size={15} />}
          <span>{detail.status}</span>
          <button aria-label="Zamerať objekt v 3D" onClick={() => showCameraPreset("focus")}><Focus size={16} /></button>
        </div>
        <div className="inspector-tabs" role="tablist" aria-label="Detail a zdroje">
          <button id="tab-parameters" role="tab" aria-controls="panel-parameters" aria-selected={inspectorTab === "parameters"} className={inspectorTab === "parameters" ? "active" : ""} onClick={() => setInspectorTab("parameters")}>Parametre</button>
          <button id="tab-sources" role="tab" aria-controls="panel-sources" aria-selected={inspectorTab === "sources"} className={inspectorTab === "sources" ? "active" : ""} onClick={() => setInspectorTab("sources")}>Zdroje <span>{sourceRecords.length}</span></button>
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
                  <label className={inputError ? "number-control has-error" : "number-control"}>
                    <span>Šírka pásu</span>
                    <div><input type="number" inputMode="numeric" min="300" max="1200" step="50" value={draftWidth} onChange={(event) => setDraftWidth(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") applyWidth(); }} aria-invalid={Boolean(inputError)} aria-describedby="width-hint" /><em>mm</em></div>
                  </label>
                  <p id="width-hint" className={inputError ? "field-message error" : "field-message"}>{inputError || "Zmena prepočíta 3D geometriu aj objem jedným krokom."}</p>
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
                <article key={source.id} className={`source-card ${source.kind === "UNRESOLVED_AS_BUILT" ? "source-warning" : ""}`}>
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

      <footer className="data-rail" aria-label="Stav dátových zdrojov">
        <div className="data-rail-title"><Database size={15} /><span>DÁTOVÁ STOPA</span></div>
        <div className="data-facts">
          <span className="fact current"><i />ČÚZK <strong>753 m²</strong><small>aktuálne</small></span>
          <span className="fact design"><i />C3 <strong>28. 4. 2026</strong><small>projekt</small></span>
          <span className="fact current"><i />DMVS <strong>voda + stoka</strong><small>verejné dáta</small></span>
          <span className="fact context"><i />DMR 5G <strong>184,087 m</strong><small>Bpv</small></span>
          <span className="fact warning"><TriangleAlert size={14} />Skutočné prípojky <strong>nepotvrdené</strong></span>
        </div>
        <div className="coordinate-readout"><span>LOCAL</span><strong>X → pozdĺž komunikácie</strong><small>Y → do parcely · Z ↑ výška</small></div>
      </footer>

      <div className="sr-only" aria-live="polite">Vybraný objekt: {detail.title}. {detail.status}.</div>
    </main>
  );
}
