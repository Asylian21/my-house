/** Exact client-selected bundle, checked against Alza on 13 September 2026. */
export const OFFICE_DESK_PRODUCT = {
  id: 'BUNAEY0806dq',
  label: 'AlzaErgo Table ET1 NewGen · čierne lamino',
  source: 'https://www.alza.cz/alzaergo-table-et1-newgen-cerny-deska-14080-cm-lamino-cerna-d13366453.htm',
  // The selected bundle's listing explicitly gives 140 × 80 × 1.8 cm.
  widthMm: 1400,
  depthMm: 800,
  topThicknessMm: 18,
  listedHeightRangeMm: [620, 1280],
  topFinish: 'BLACK_LAMINATE',
  frameFinish: 'BLACK_POWDER_COATED_STEEL',
  motorCount: 2,
  columnSegments: 3,
} as const;
