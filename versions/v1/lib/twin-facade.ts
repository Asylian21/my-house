export interface FacadeOpeningMm {
  readonly id: string;
  readonly startMm: number;
  readonly widthMm: number;
  readonly heightMm: number;
  readonly sillMm: number;
  readonly frameStartMm?: number;
  /** Visible face width of the perimeter frame profile. */
  readonly frameWidthMm?: number;
  readonly label?: string;
}

export interface FacadeSegmentMm {
  readonly startMm: number;
  readonly endMm: number;
  readonly bottomMm: number;
  readonly topMm: number;
}

/** Deterministically cuts an eaves-height facade into solid rectangles. */
export function segmentFacadeMm(
  startMm: number,
  endMm: number,
  heightMm: number,
  openings: readonly FacadeOpeningMm[],
): readonly FacadeSegmentMm[] {
  const sorted = [...openings].sort((left, right) => left.startMm - right.startMm);
  const segments: FacadeSegmentMm[] = [];
  let cursorMm = startMm;

  for (const opening of sorted) {
    const openingEndMm = opening.startMm + opening.widthMm;
    const openingTopMm = opening.sillMm + opening.heightMm;
    if (
      opening.startMm < cursorMm ||
      openingEndMm > endMm ||
      opening.widthMm <= 0 ||
      opening.heightMm <= 0 ||
      opening.sillMm < 0 ||
      openingTopMm > heightMm
    ) {
      throw new Error(`Neplatný alebo prekrývajúci sa fasádny otvor ${opening.id}.`);
    }
    if (opening.startMm > cursorMm) {
      segments.push({
        startMm: cursorMm,
        endMm: opening.startMm,
        bottomMm: 0,
        topMm: heightMm,
      });
    }
    if (opening.sillMm > 0) {
      segments.push({
        startMm: opening.startMm,
        endMm: openingEndMm,
        bottomMm: 0,
        topMm: opening.sillMm,
      });
    }
    if (openingTopMm < heightMm) {
      segments.push({
        startMm: opening.startMm,
        endMm: openingEndMm,
        bottomMm: openingTopMm,
        topMm: heightMm,
      });
    }
    cursorMm = openingEndMm;
  }

  if (cursorMm < endMm) {
    segments.push({
      startMm: cursorMm,
      endMm,
      bottomMm: 0,
      topMm: heightMm,
    });
  }
  return segments;
}
