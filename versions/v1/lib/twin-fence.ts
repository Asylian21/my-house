/**
 * Centers a fixed-pitch slat raster inside one panel.
 *
 * The pitch remains exact; any remainder is shared equally by both edge
 * margins so a short panel never stretches the architectural rhythm.
 */
export function slatCenterDistancesMm(
  panelLengthMm: number,
  slatWidthMm: number,
  pitchMm: number,
): readonly number[] {
  if (
    !Number.isFinite(panelLengthMm) ||
    !Number.isFinite(slatWidthMm) ||
    !Number.isFinite(pitchMm) ||
    panelLengthMm <= 0 ||
    slatWidthMm <= 0 ||
    pitchMm < slatWidthMm
  ) {
    throw new Error("Rozmery lamelového rastra nie sú platné.");
  }
  if (panelLengthMm < slatWidthMm) return [];
  const count = Math.floor((panelLengthMm - slatWidthMm) / pitchMm) + 1;
  const occupiedLengthMm = slatWidthMm + (count - 1) * pitchMm;
  const edgeMarginMm = (panelLengthMm - occupiedLengthMm) / 2;
  return Array.from(
    { length: count },
    (_, index) => edgeMarginMm + slatWidthMm / 2 + index * pitchMm,
  );
}
