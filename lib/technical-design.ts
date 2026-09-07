import { BATHROOM_FITOUT as bathroom, TECHNICAL_HEATING_FITOUT as heating, WC_FITOUT as wc, type RectMm } from './twin-interior-baseline';

const rect=(x0:number,y0:number,x1:number,y1:number):RectMm=>({x0,y0,x1,y1});
const shift=(r:RectMm,dx:number):RectMm=>({...r,x0:r.x0+dx,x1:r.x1+dx});

/** Dimensions checked against the Czech product drawings, 7 September 2026.
 * Agreement: supplier 16 February, client acceptance 17 February 2026.
 * Product dimensions are not a construction, hydraulic or fire-safety approval.
 */
export const SERVICE_CORE_REVISION={id:'C-HEATING-WC-2026-09-07',wcExpansionMm:230,bathroomReturnShiftMm:300,
  technicalWestMm:24451,boilerBayWestMm:25243,bathroomEastMm:25099,technicalFacadeInsideMm:27510,
  exteriorDoor:{id:'EAST-03',startYmm:9300,widthMm:1700,heightMm:2250,sillMm:0},
} as const;
export const HEATING_SOURCES={
  boiler:'https://defro.cz/nabidka-heat/firewood-duo/',
  accumulator:'https://defro.cz/nabidka-heat/dbo-s/',
  manual:'https://e-kominki24h.pl/templates/images/files/1652/1755679863-instrukcja-obslugi-firewood-duo-plus-wyd-ii-pazdziernik-2024-razem-z-gwarancja.pdf',
  loadingUnit:'https://defro.cz/nabidka-heat/defromat-78/',
  safetyGroup:'https://afriso.cz/produkt/pojistna-souprava-ksg-mini-s-izolaci-25-bar/',
};
export const TECHNICAL_HEATING_FITOUT={...heating,id:'TECHNICAL-PLUS19-DBOS1000',sourceId:SERVICE_CORE_REVISION.id,
  boiler:{...heating.boiler,referenceProductFamily:'DEFRO_FIREWOOD_DUO_PLUS',referenceOutputKw:19,
    assemblyFootprintMm:rect(25762,8291,27000,9589),heightMm:1391,baseElevationMm:50,
    body:{footprintMm:rect(26462,8504,27000,9160),heightMm:1233,controllerTopElevationMm:1389},
    hopper:{...heating.boiler.hopper,footprintMm:rect(25762,8504,26376,9118),
      depthBasis:'DERIVED_FROM_ORTHOGRAPHIC_DRAWING' as const},
    burner:{footprintMm:rect(26510,9160,26952,9589)},
    serviceRectMm:rect(26462,9160,27425,11160),frontServiceClearanceMm:2000,
    serviceMeasuredFrom:'BODY_FRONT' as const,openDoorEnvelopeWidthMm:1663,
    modeledSideClearanceMm:500,modeledRearClearanceMm:540,
    // Measured to the finished 10 mm wall lining, including the real shell at x27510.
    sideClearancesMm:{west:509,east:500},
  },
  accumulator:{...heating.accumulator,referenceProduct:'DEFRO DBO-S 1000',centerMm:{x:25104,y:10020},
    nominalVolumeL:1000,outerDiameterMm:1106,transportDiameterWithoutInsulationMm:897,heightMm:1913,
    // Fittings and their service space are planning allowances, not manufacturer nozzle dimensions.
    connectionProjectionMm:180,serviceRectMm:rect(25837,9580,26437,10573),
  },
  storage:{id:'TECHNICAL-STORAGE-RESERVE',footprintMm:rect(24481,8930,24981,9380),heightMm:1200,
    pelletBagCount:3,pelletBagMassKg:15,bagSizeMm:{width:440,depth:330,height:150},
    vacuumSizeMm:{width:340,depth:390,height:340},
    fireSeparationApprovalRequired:true,front:'EAST',frontClearanceRectMm:rect(24981,8930,25581,9380),
  },
  hydraulicReserve:{id:'TECHNICAL-HYDRAULIC-RESERVE',footprintMm:rect(24481,8930,24981,9380),
    bottomMm:1350,heightMm:1100,loadingUnitEnvelopeMm:{width:420,height:500,depth:220},
    exactLoadingUnitDimensionsVerified:false,safetyGroupMm:{width:147,height:140,depth:70},
  },
  installationStatus:'SPATIAL_DESIGN_REQUIRES_INSTALLER_AND_FIRE_REVIEW' as const,
};

export const WC_FITOUT={...wc,id:'WC-FITOUT-COMFORT-C',sourceId:SERVICE_CORE_REVISION.id,
  toilet:{...wc.toilet,footprintMm:shift(wc.toilet.footprintMm,115),concealedCisternRectMm:shift(wc.toilet.concealedCisternRectMm,115)},
  basin:{...wc.basin,footprintMm:rect(23962,9970,24312,10520)},
  clearFloorRectMm:rect(22783,9432,23962,10712),
};

export const BATHROOM_FITOUT={...bathroom,sourceId:SERVICE_CORE_REVISION.id,
  builtIn:{...bathroom.builtIn,footprintMm:{...bathroom.builtIn.footprintMm,x1:25099},
    basin:{...bathroom.builtIn.basin,footprintMm:shift(bathroom.builtIn.basin.footprintMm,-60)},
    appliances:bathroom.builtIn.appliances.map(a=>({...a,footprintMm:shift(a.footprintMm,-300)})),
  },
  clearFloorRectMm:{...bathroom.clearFloorRectMm,x1:25099},
  applianceServiceRectMm:shift(bathroom.applianceServiceRectMm,-300),
};
