import { BATHROOM_FITOUT as bathroom, TECHNICAL_HEATING_FITOUT as heating, WC_FITOUT as wc, type RectMm } from './twin-interior-baseline';

const rect=(x0:number,y0:number,x1:number,y1:number):RectMm=>({x0,y0,x1,y1});
const shift=(r:RectMm,dx:number):RectMm=>({...r,x0:r.x0+dx,x1:r.x1+dx});

/** Dimensions checked against the Czech product drawings, 7 September 2026.
 * Agreement: supplier 16 February, client acceptance 17 February 2026.
 * Product dimensions are not a construction, hydraulic or fire-safety approval.
 */
export const SERVICE_CORE_REVISION={id:'C-HEATING-WC-2026-09-07',wcExpansionMm:600,bathroomReturnShiftMm:300,
  technicalWestMm:24821,boilerBayWestMm:25243,bathroomEastMm:25099,technicalFacadeInsideMm:27510,
  exteriorDoor:{id:'EAST-03',startYmm:9300,widthMm:1700,heightMm:2250,sillMm:0},
} as const;
export const HEATING_SOURCES={
  boiler:'https://defro.cz/nabidka-heat/firewood-duo/',
  accumulator:'https://defro.cz/nabidka-heat/dbo-s/',
  manual:'https://e-kominki24h.pl/templates/images/files/1652/1755679863-instrukcja-obslugi-firewood-duo-plus-wyd-ii-pazdziernik-2024-razem-z-gwarancja.pdf',
  loadingUnit:'https://defro.cz/nabidka-heat/defromat-78/',
  vacuum:'https://www.electrolux.sk/vacuums-home-comfort/vacuum-cleaners/stick-vacuum-cleaners/cordless-sticks/wq61-40og/',
  safetyGroup:'https://afriso.cz/produkt/pojistna-souprava-ksg-mini-s-izolaci-25-bar/',
};
export const TECHNICAL_HEATING_FITOUT={...heating,id:'TECHNICAL-PLUS19-DBOS1000',sourceId:SERVICE_CORE_REVISION.id,
  boiler:{...heating.boiler,referenceProductFamily:'DEFRO_FIREWOOD_DUO_PLUS',referenceOutputKw:19,
    assemblyFootprintMm:rect(25757.5,8251,26995.5,9549),heightMm:1391,baseElevationMm:50,
    body:{footprintMm:rect(26457.5,8464,26995.5,9120),heightMm:1233,controllerTopElevationMm:1389},
    hopper:{...heating.boiler.hopper,footprintMm:rect(25757.5,8464,26371.5,9078),
      depthBasis:'DERIVED_FROM_ORTHOGRAPHIC_DRAWING' as const},
    burner:{footprintMm:rect(26505.5,9120,26947.5,9549)},
    serviceRectMm:rect(26457.5,9120,27500,11120),frontServiceClearanceMm:2000,
    serviceMeasuredFrom:'BODY_FRONT' as const,openDoorEnvelopeWidthMm:1663,
    modeledSideClearanceMm:504.5,modeledRearClearanceMm:500,
    // Measured to the finished 10 mm wall lining, including the real shell at x27510.
    sideClearancesMm:{west:504.5,east:504.5},
  },
  accumulator:{...heating.accumulator,referenceProduct:'DEFRO DBO-S 1000',centerMm:{x:25500,y:10100},
    nominalVolumeL:1000,outerDiameterMm:1106,transportDiameterWithoutInsulationMm:897,heightMm:1913,
    // Fittings and their service space are planning allowances, not manufacturer nozzle dimensions.
    connectionProjectionMm:180,connectionAzimuthDegrees:30,serviceRectMm:rect(26280,10000,26880,10700),
  },
  storage:{id:'TECHNICAL-STORAGE-RESERVE',footprintMm:rect(26760,11140,27480,11401),heightMm:1750,
    pelletBagCount:3,pelletBagMassKg:15,bagSizeMm:{width:330,depth:190,height:430},
    vacuumSizeMm:{width:255,depth:140,height:1105},
    fireSeparationApprovalRequired:true,front:'SOUTH',frontClearanceRectMm:rect(26760,10540,27480,11140),
  },
  hydraulicReserve:{id:'TECHNICAL-HYDRAULIC-RESERVE',footprintMm:rect(26760,11140,27480,11401),
    bottomMm:1850,heightMm:650,loadingUnitEnvelopeMm:{width:420,height:500,depth:220},
    exactLoadingUnitDimensionsVerified:false,safetyGroupMm:{width:147,height:140,depth:70},
  },
  installationStatus:'SPATIAL_DESIGN_REQUIRES_INSTALLER_AND_FIRE_REVIEW' as const,
};

export const WC_FITOUT={...wc,id:'WC-FITOUT-COMFORT-C',sourceId:SERVICE_CORE_REVISION.id,
  toilet:{...wc.toilet,footprintMm:shift(wc.toilet.footprintMm,300),concealedCisternRectMm:shift(wc.toilet.concealedCisternRectMm,300)},
  basin:{...wc.basin,footprintMm:rect(24332,9970,24682,10520)},
  clearFloorRectMm:rect(22783,9432,24332,10712),
};

export const BATHROOM_FITOUT={...bathroom,sourceId:SERVICE_CORE_REVISION.id,
  builtIn:{...bathroom.builtIn,footprintMm:{...bathroom.builtIn.footprintMm,x1:25099},
    basin:{...bathroom.builtIn.basin,footprintMm:shift(bathroom.builtIn.basin.footprintMm,-60)},
    appliances:bathroom.builtIn.appliances.map(a=>({...a,footprintMm:shift(a.footprintMm,-300)})),
  },
  clearFloorRectMm:{...bathroom.clearFloorRectMm,x1:25099},
  applianceServiceRectMm:shift(bathroom.applianceServiceRectMm,-300),
};
