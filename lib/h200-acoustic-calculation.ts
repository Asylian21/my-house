/** Preliminary lining model, Ziegel 2022 p. 62; not a tested assembly or site R'w. */
export function calculateH200Acoustics(boardCount: 1 | 2 = 1, plasterDensityKgM3 = 1800) {
  const baseRwDb = 35; // LeierPLAN 10 N+F, with 15 mm plaster on both faces.
  const masonryMassKgM2 = 73;
  const baseMassKgM2 = masonryMassKgM2 + 2 * 0.015 * plasterDensityKgM3;
  const liningMassKgM2 = boardCount * 17.5; // Knauf W623 Silentboard example.
  const cavityDepthM = 0.045;
  const resonanceHz = 160 * Math.sqrt(0.111 / cavityDepthM * (1 / baseMassKgM2 + 1 / liningMassKgM2));
  // Retain the previous report's conservative 50 Hz floor for comparison.
  // This is a project assumption, not the lower limit of the published formula.
  const calculationResonanceHz = Math.max(50, resonanceHz);
  const improvementDb = Math.max(0, 74.4 - 20 * Math.log10(calculationResonanceHz) - 0.5 * baseRwDb);
  return { boardCount, baseRwDb, plasterDensityKgM3, baseMassKgM2, liningMassKgM2,
    cavityDepthM, resonanceHz, calculationResonanceHz, improvementDb,
    estimatedRwDb: baseRwDb + improvementDb, evidence: 'PRELIMINARY_MODEL_NOT_MEASURED' as const };
}

export const H200_ACOUSTIC_CALCULATION = calculateH200Acoustics();
