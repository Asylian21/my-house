import { BATHROOM_FITOUT as bathroom, TECHNICAL_HEATING_FITOUT as heating, WC_FITOUT as wc, type RectMm } from './twin-interior-baseline';

const rect=(x0:number,y0:number,x1:number,y1:number):RectMm=>({x0,y0,x1,y1});
const shift=(r:RectMm,dx:number):RectMm=>({...r,x0:r.x0+dx,x1:r.x1+dx});

/** Dimensions checked against the Czech product drawings, 7 September 2026.
 * Agreement: supplier 16 February, client acceptance 17 February 2026.
 * Product dimensions are not a construction, hydraulic or fire-safety approval.
 */
export const SERVICE_CORE_REVISION={id:'C-HEATING-STRAIGHT-WALL-2026-09-12',wcExpansionMm:600,bathroomReturnShiftMm:717,
  // The laundry partition meets both faces of the retained WC partition (139 mm).
  // The technical room becomes one 2 689 × 2 971 mm rectangle.
  technicalWestMm:24821,boilerBayWestMm:24821,bathroomEastMm:24682,technicalFacadeInsideMm:27510,
  previousBoilerBayWestMm:25243,previousBathroomEastMm:25099,
  // 12. 9. 2026: a 900 mm single leaf instead of the 1 700 mm transport door, for the
  // statics of the east facade next to the load-bearing kitchen wall (10 712–11 012).
  // Moving the opening 300 mm south frees 812 mm of masonry at the kitchen end.
  exteriorDoor:{id:'EAST-03',startYmm:9000,widthMm:900,heightMm:2250,sillMm:0},
  exteriorDoorRevision:{sourceId:'C-KITCHEN-BEARING-WALL-2026-09-12',previousWidthMm:1700,layout:'SINGLE_LEAF_OUTWARD',hinge:'SOUTH_JAMB'},
} as const;
export const HEATING_SOURCES={
  boiler:'https://defro.cz/nabidka-heat/firewood-duo/',
  accumulator:'https://defro.cz/nabidka-heat/dbo-s/',
  manual:'https://e-kominki24h.pl/templates/images/files/1652/1755679863-instrukcja-obslugi-firewood-duo-plus-wyd-ii-pazdziernik-2024-razem-z-gwarancja.pdf',
  loadingUnit:'https://defro.cz/nabidka-heat/defromat-78/',
  vacuum:'https://www.electrolux.sk/vacuums-home-comfort/vacuum-cleaners/stick-vacuum-cleaners/cordless-sticks/wq61-40og/',
  safetyGroup:'https://afriso.cz/produkt/pojistna-souprava-ksg-mini-s-izolaci-25-bar/',
};
export const HEATING_LAYOUT_IDS=['A','B'] as const;
export type HeatingLayoutId=typeof HEATING_LAYOUT_IDS[number];
export const DEFAULT_HEATING_LAYOUT_ID:HeatingLayoutId='A';
export const normalizeHeatingLayout=(value:string|null|undefined):HeatingLayoutId=>value?.toLowerCase()==='b'?'B':'A';

/** Catalogue frame: front +Y. Installed front faces east, hopper south.
 * The manufacturer permits the hopper on either side; doors are drawn closed.
 * A 420 mm rear gap accommodates the stock outlet and proposed upward elbow.
 * Separate hopper / auger positions are a mounting proposal, not a catalogue approval.
 */
export const installedBoilerRect=(r:RectMm,bodyWidthMm:number):RectMm=>rect(25251+r.y0,8551+bodyWidthMm-r.x1,25251+r.y1,8551+bodyWidthMm-r.x0);
function heatingFitout(layout:HeatingLayoutId){
  const compact=layout==='B',output=compact?15:19,volume=compact?800:1000;
  const width=compact?488:538,depth=compact?1296:1298,diameter=compact?958:1106;
  // Drawing: K = 1 224, I = 656, J = 429. Rear projection = K − I − J = 139.
  // L includes the feeder's additional FRONT projection, not a longer rear pipe.
  const rearProjection=1224-656-429;
  const model={assemblyFootprintMm:rect(0,-rearProjection,width+700,depth-rearProjection),
    body:rect(0,0,width,656),hopper:rect(width+86,-70,width+700,544),burner:rect(width/2-110,656,width/2+110,1085)};
  const installed=(r:RectMm)=>installedBoilerRect(r,width);
  const body=installed(model.body),assembly=installed(model.assemblyFootprintMm);
  const openDoorEnvelopeWidth=compact?1566:1663,doorSideExtension=openDoorEnvelopeWidth-(width+700);
  const tankCenter={x:24831+100+diameter/2,y:10702-100-diameter/2};
  const storageId=compact?'TECHNICAL-STORAGE-COMPACT-RESERVE':'TECHNICAL-STORAGE-RESERVE';
  return {...heating,id:`TECHNICAL-PLUS${output}-DBOS${volume}`,sourceId:SERVICE_CORE_REVISION.id,layout,
    label:compact?'15 kW + 800 l':'19 kW + 1 000 l',
    summary:compact?'Menšia zostava na dopracovanie · pelety, drevo ako záloha.':'Pôvodne navrhnutá veľkosť v novom rozložení.',
    boiler:{...heating.boiler,referenceProductFamily:'DEFRO_FIREWOOD_DUO_PLUS',referenceOutputKw:output,
      pelletOutputRangeKw:compact?[4.2,15.2] as const:[5.3,19.3] as const,
      catalogueSizeMm:{width:width+700,depth,height:1391},model,
      originMm:{x:25251,y:8551+width},rotationDegrees:-90,mirrorX:false,front:'EAST' as const,doorState:'CLOSED' as const,
      assemblyFootprintMm:assembly,heightMm:1391,baseElevationMm:50,
      body:{footprintMm:body,heightMm:compact?1213:1233,controllerTopElevationMm:1389},
      hopper:{...heating.boiler.hopper,footprintMm:installed(model.hopper),forwardOffsetMm:-70,side:'SOUTH' as const,
        fillingStandingPointMm:{x:26110,y:8063},depthBasis:'DERIVED_FROM_ORTHOGRAPHIC_DRAWING' as const},
      feeder:{outletAcrossMm:width-32,accessoryDirection:-1,installationStatus:'POSITION_LENGTH_AND_INCLINE_REQUIRE_SUPPLIER_CONFIRMATION' as const},
      burner:{footprintMm:installed(model.burner),housingWidthMm:220,housingDepthMm:350,heightMm:260,bottomMm:230,neckLengthMm:79,
        shapeBasis:'DRAWING_PROPORTION_ESTIMATE' as const,closedProjectionMm:429},
      serviceRectMm:rect(body.x1,body.y0,27500,body.y1),frontServiceClearanceMm:27500-body.x1,
      previousFrontServiceClearanceMm:1920,manufacturerFrontRecommendationMm:2000,
      clearFloorBeyondBurnerMm:27500-body.x1-429,clearFloorBeyondFeederMm:27500-assembly.x1,serviceMeasuredFrom:'BODY_FRONT' as const,
      openDoorEnvelopeWidthMm:openDoorEnvelopeWidth,doorSideExtensionMm:doorSideExtension,
      // Conservative room allocation: body width ahead of the front, C1−C beyond its south side.
      // Does not certify a hinge mechanism or clearance from removable pellet accessories.
      doorOpeningReserveMm:rect(body.x1,body.y0-doorSideExtension,body.x1+width,body.y1),
      doorOpeningStatus:'ROOM_ENVELOPE_ONLY_ACCESSORIES_REQUIRE_SERVICE_PROCEDURE' as const,
      modeledSideClearanceMm:tankCenter.y-diameter/2-body.y1,sideServiceMeasuredFrom:'NORTH_BODY_TO_TANK' as const,
      modeledRearClearanceMm:body.x0-24831,rearServiceMeasuredFrom:'BODY_REAR' as const,
      modeledRearConnectionClearanceMm:assembly.x0-24831,clearanceStatus:'BELOW_MANUFACTURER_RECOMMENDATION' as const,
      sideClearancesMm:{west:assembly.x0-24831,east:27500-assembly.x1},
    },
    flue:{id:`TECHNICAL-PLUS${output}-DBOS${volume}-FLUE`,stockRearProjectionMm:rearProjection,
      diameterMm:159,elbowCenterlineRadiusMm:100,outletElevationMm:964,topElevationMm:2600,
      centerMm:{x:body.x0-rearProjection-100,y:(body.y0+body.y1)/2},
      wallClearanceMm:body.x0-rearProjection-100-159/2-24831,
      fittingSelectionStatus:'COMPACT_ELBOW_REQUIRES_SUPPLIER_CONFIRMATION' as const,
      termination:'ROOM_CEILING_CONNECTION_RESERVE' as const},
    accumulator:{...heating.accumulator,referenceProduct:`DEFRO DBO-S ${volume}`,centerMm:tankCenter,
      placementZoneMm:rect(24831,tankCenter.y-diameter/2-100,tankCenter.x+diameter/2+100,10702),wallClearanceMm:100,
      nominalVolumeL:volume,outerDiameterMm:diameter,transportDiameterWithoutInsulationMm:compact?745:897,heightMm:compact?2106:1913,
      transport:{openingId:'EAST-03',openingWidthMm:900,clearWidthMm:648,
        passesInsulated:false,passesWithoutInsulation:false,passesBareThroughTrue900MmClear:true,
        clearanceAtTrue900Mm:900-(compact?745:897),status:'VERIFY_FINISHED_CLEAR_OPENING' as const,
        method:'REMOVE_INSULATION_VERIFY_CLEAR_OPENING' as const},
      connectionProjectionMm:180,connectionAzimuthDegrees:330,
      serviceRectMm:rect(26320,9400,26920,10100),
    },
    storage:{id:storageId,footprintMm:rect(27239,7751,27500,8471),heightMm:1750,
      pelletBagCount:3,pelletBagMassKg:15,bagSizeMm:{width:330,depth:190,height:430},
      vacuumSizeMm:{width:255,depth:140,height:1105},fireSeparationApprovalRequired:true,
      front:'WEST',frontClearanceRectMm:rect(26639,7751,27239,8471)},
    hydraulicReserve:{id:`${storageId}-HYDRAULIC`,footprintMm:rect(27239,7751,27500,8471),bottomMm:1850,heightMm:650,
      loadingUnitEnvelopeMm:{width:420,height:500,depth:220},exactLoadingUnitDimensionsVerified:false,
      safetyGroupMm:{width:147,height:140,depth:70}},
    shelving:{id:`TECHNICAL-SHELVING-${layout}`,footprintMm:rect(27200,9942,27500,10692),heightMm:2000,
      shelfCount:5,front:'WEST' as const,frontClearanceRectMm:rect(26600,9942,27200,10692)},
    installationStatus:'SPATIAL_DESIGN_REQUIRES_INSTALLER_AND_FIRE_REVIEW' as const,
  };
}
export type TechnicalHeatingFitout=ReturnType<typeof heatingFitout>;
export const HEATING_LAYOUTS:Record<HeatingLayoutId,TechnicalHeatingFitout>={A:heatingFitout('A'),B:heatingFitout('B')};
export const TECHNICAL_HEATING_FITOUT=HEATING_LAYOUTS[DEFAULT_HEATING_LAYOUT_ID];
export const HEATING_OPERATION_NOTES=[
  'Primárne pelety; kusové drevo v kotle iba ako núdzová záloha. Samostatné kachle v obývačke sa neodpočítavajú od potrebného výkonu hlavného zdroja.',
  'Podlahovka: dve detské izby, pracovňa, spálňa, obývačka s kuchyňou a WC pri kuchyni. V kúpeľniach iba rebríky, v chladnejšej garáži malé vykurovacie teleso.',
  'Rekuperácia v spálni, oboch detských izbách a pracovni; klimatizácia v obývačke a pracovni. Účinnosť, prietoky a spôsob vetrania ostatných miestností ešte nie sú určené.',
  '15 kW + 800 l je vhodný kandidát na preverenie pri peletovej prevádzke. PENB opisuje ročnú energetickú bilanciu; predchádzajúci odhad 8–10 kW nie je výpočtová tepelná strata podľa miestností. Čiastočná rekuperácia ho mení, ale bez prietokov ju nemožno presne vyčísliť. Výkon aj akumuláciu pre záložné drevo musí potvrdiť projekt vykurovania.',
];
export function heatingTransportNote(layout:HeatingLayoutId){
  const tank=HEATING_LAYOUTS[layout].accumulator;
  return `Izolácia je odnímateľná: na prepravu má nádrž Ø${tank.transportDiameterWithoutInsulationMm} mm. Pri skutočne voľných 900 mm zostáva ${tank.transport.clearanceAtTrue900Mm} mm celkovej rezervy. Označenie dverí „90“ samo nepotvrdzuje čistý priechod; súčasná kresba rámu a otvoreného krídla modeluje 648 mm. Pred objednaním overiť konkrétnu zárubňu, demontáž krídla, presahy hrdiel a celú trasu. Izolácia sa montuje späť v miestnosti.`;
}
export function heatingRoomNotes(layout:HeatingLayoutId){
  const h=HEATING_LAYOUTS[layout],b=h.boiler,t=h.accumulator;
  return [
    'Technická miestnosť má rovnú priečku bez zuba: 2 689 × 2 971 mm, spolu 7,99 m². Nádrž stojí vľavo hore, 100 mm od hotových stien. Pod nádržou je teleso kotla čelom doprava do miestnosti, pod kotlom násypka. Technológia tak tvorí jeden pás pri ľavej stene. Dvierka sú zatvorené. Výrobca umožňuje násypku na oboch stranách. Prípojky nádrže smerujú šikmo doprava dolu, mimo kuchynského vstupu.',
    `Variant ${layout}: DEFRO Firewood Duo Plus ${b.referenceOutputKw} kW + DBO-S ${t.nominalVolumeL} l. Katalógová zostava kotla ${b.catalogueSizeMm.width} × ${b.catalogueSizeMm.depth} × 1 391 mm, podstavec +50 mm. Nádrž s izoláciou Ø${t.outerDiameterMm} × ${t.heightMm} mm.`,
    '800 l nádrž je oproti 1 000 l o 148 mm užšia a o 193 mm vyššia; ušetrí približne 0,24 m² kruhového pôdorysu. Samotné teleso 15 kW má 488 × 656 mm, teleso 19 kW má 538 × 656 mm. Obe zostavy používajú rovnakú násypku približne 180 kg so šírkou 614 mm. Nižší výkon preto nemení zostavu na výrazne menší kotol.',
    `Zobrazený je zatvorený kotol: predný presah horáka 429 mm patrí aj k zatvoreným dvierkam. Horák je úzky stredový diel; jeho tvar 220 × 350 × 260 mm a krčok 79 mm sú odvodené z mierky výrobného výkresu, nie samostatne okótované výrobcom. Za telesom je ${b.modeledRearClearanceMm} mm, výrobné hrdlo 139 mm a návrh kolena nahor; zvislý dymovod Ø159 mm je ${h.flue.wallClearanceMm} mm od ľavej steny. Pred telesom je ${b.frontServiceClearanceMm} mm, pred horákom ${b.clearFloorBeyondBurnerMm} mm. Návod uvádza 2 000 mm vpredu a 500 mm po bokoch a vzadu; tieto odstupy nie sú všetky dodržané. Koleno, podávač a servisné otváranie s peletovým príslušenstvom musí vyriešiť dodávateľ.`,
    heatingTransportNote(layout),
    'Vonkajšie dvere sú posunuté o 300 mm smerom k sprche a otvárajú sa von. Pri kuchyni zostáva 812 mm muriva; vojde sa sem otvorený oceľový regál 750 × 300 × 2 000 mm s piatimi policami a prístupom 600 mm. Plytká servisná skriňa vpravo dole pri východnej stene má 720 × 261 × 1 750 mm a čelo doľava, nad ňou je rezerva pre hydrauliku. Medzi skriňou a regálom ostáva napravo voľná plocha aspoň 1 050 × 1 330 mm. Slúži aj na obsluhu a priechod k vonkajším dverám; trvalé zariadenie tu potrebuje nové preverenie prístupu. Rozvody a expanzná nádoba ešte nemajú montážny návrh. Tri vrecia peliet predstavujú priestorovú rezervu; požiarne oddelenie musí byť vyriešené.',
    ...HEATING_OPERATION_NOTES,
  ];
}

export const WC_FITOUT={...wc,id:'WC-FITOUT-COMFORT-C',sourceId:SERVICE_CORE_REVISION.id,
  toilet:{...wc.toilet,footprintMm:shift(wc.toilet.footprintMm,300),concealedCisternRectMm:shift(wc.toilet.concealedCisternRectMm,300)},
  basin:{...wc.basin,footprintMm:rect(24332,9970,24682,10520)},
  clearFloorRectMm:rect(22783,9432,24332,10712),
};

export const BATHROOM_FITOUT={...bathroom,sourceId:SERVICE_CORE_REVISION.id,
  builtIn:{...bathroom.builtIn,footprintMm:{...bathroom.builtIn.footprintMm,x1:SERVICE_CORE_REVISION.bathroomEastMm},
    // 1 213 mm vanity beside the ventilated 600 mm tower; basin and mirror follow it.
    basin:{...bathroom.builtIn.basin,footprintMm:rect(22989.5,8222,23789.5,8672)},
    appliances:bathroom.builtIn.appliances.map(a=>({...a,footprintMm:shift(a.footprintMm,-SERVICE_CORE_REVISION.bathroomReturnShiftMm)})),
  },
  clearFloorRectMm:{...bathroom.clearFloorRectMm,x1:SERVICE_CORE_REVISION.bathroomEastMm},
  applianceServiceRectMm:shift(bathroom.applianceServiceRectMm,-SERVICE_CORE_REVISION.bathroomReturnShiftMm),
};
