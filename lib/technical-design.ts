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
    assemblyFootprintMm:rect(26012,7788,27250,9086),heightMm:1391,baseElevationMm:50,
    body:{footprintMm:rect(26712,8001,27250,8657),heightMm:1233,controllerTopElevationMm:1389},
    hopper:{...heating.boiler.hopper,footprintMm:rect(26012,8001,26626,8615),
      depthBasis:'DERIVED_FROM_ORTHOGRAPHIC_DRAWING' as const},
    burner:{footprintMm:rect(26760,8657,27202,9086)},
    serviceRectMm:rect(26712,8657,27500,10657),frontServiceClearanceMm:2000,
    serviceMeasuredFrom:'BODY_FRONT' as const,openDoorEnvelopeWidthMm:1663,
    // Client-requested corner position. Both 250 mm gaps are below the manufacturer's 500 mm.
    modeledSideClearanceMm:250,modeledRearClearanceMm:250,rearServiceMeasuredFrom:'BODY_REAR' as const,
    modeledRearConnectionClearanceMm:37,clearanceStatus:'BELOW_MANUFACTURER_RECOMMENDATION' as const,
    // Measured to the finished 10 mm wall lining, including the real shell at x27510.
    sideClearancesMm:{west:759,east:250},
  },
  accumulator:{...heating.accumulator,referenceProduct:'DEFRO DBO-S 1000',centerMm:{x:25771.5,y:9812},
    // A planning zone, not an additional wall: centred in the left side before the boiler service strip.
    placementZoneMm:rect(24831,8922,26712,10702),
    transportRouteMm:[{x:29000,y:10200},{x:26250,y:10150},{x:25771.5,y:9812}],
    nominalVolumeL:1000,outerDiameterMm:1106,transportDiameterWithoutInsulationMm:897,heightMm:1913,
    // Fittings and their service space are planning allowances, not manufacturer nozzle dimensions.
    connectionProjectionMm:180,connectionAzimuthDegrees:30,serviceRectMm:rect(26560,9700,27160,10440),
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
