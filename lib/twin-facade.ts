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

export type WallLayerKind = "masonry" | "insulation" | "solid";

/** One plan layer of a facade segment; `offsetMm` is measured inward from the outer face. */
export interface WallLayerMm extends FacadeSegmentMm {
  readonly kind: WallLayerKind;
  readonly offsetMm: number;
  readonly depthMm: number;
}

export interface WallLayerOptions {
  /** Depth of the rendered wall from the outer face (includes any room-side overlap). */
  readonly thicknessMm: number;
  /** Contact insulation measured from the outer face. */
  readonly insulationMm: number;
  /** Along-facade ranges with exterior space on both sides: solid uninsulated masonry of the full thickness. */
  readonly solidMm?: readonly (readonly [number, number])[];
  /** Outer corners: the masonry layer ending at the key stops at the value, where the perpendicular wall's insulation wraps around. */
  readonly masonryInsetMm?: Readonly<Record<number, number>>;
  /** Junctions where the insulation layer ending at the key stops at the value (a perpendicular solid wall). */
  readonly insulationInsetMm?: Readonly<Record<number, number>>;
}

const clampInset = (
  startMm: number,
  endMm: number,
  inset: Readonly<Record<number, number>> | undefined,
): readonly [number, number] => {
  if (!inset) return [startMm, endMm];
  const start = inset[startMm] !== undefined ? Math.max(startMm, inset[startMm]) : startMm;
  const end = inset[endMm] !== undefined ? Math.min(endMm, inset[endMm]) : endMm;
  return [start, end];
};

/**
 * Splits a solid facade segment into its real build-up: masonry on the room
 * side and contact insulation on the outer face, or one solid block where the
 * wall stands free on a terrace. Vertical extent is inherited from the segment.
 */
export function exteriorWallLayers(
  segment: FacadeSegmentMm,
  options: WallLayerOptions,
): readonly WallLayerMm[] {
  const cuts = new Set<number>([segment.startMm, segment.endMm]);
  for (const [a, b] of options.solidMm ?? []) {
    if (a > segment.startMm && a < segment.endMm) cuts.add(a);
    if (b > segment.startMm && b < segment.endMm) cuts.add(b);
  }
  const points = [...cuts].sort((left, right) => left - right);
  const layers: WallLayerMm[] = [];
  for (let index = 0; index < points.length - 1; index += 1) {
    const startMm = points[index];
    const endMm = points[index + 1];
    const solid = (options.solidMm ?? []).some(([a, b]) => startMm >= a && endMm <= b);
    if (solid) {
      layers.push({ ...segment, startMm, endMm, kind: "solid", offsetMm: 0, depthMm: options.thicknessMm });
      continue;
    }
    const [masonryStart, masonryEnd] = clampInset(startMm, endMm, options.masonryInsetMm);
    const [insulationStart, insulationEnd] = clampInset(startMm, endMm, options.insulationInsetMm);
    if (masonryEnd > masonryStart) {
      layers.push({
        ...segment,
        startMm: masonryStart,
        endMm: masonryEnd,
        kind: "masonry",
        offsetMm: options.insulationMm,
        depthMm: options.thicknessMm - options.insulationMm,
      });
    }
    if (insulationEnd > insulationStart) {
      layers.push({
        ...segment,
        startMm: insulationStart,
        endMm: insulationEnd,
        kind: "insulation",
        offsetMm: 0,
        depthMm: options.insulationMm,
      });
    }
  }
  return layers;
}

/** Mesh-name suffix of a layer, shared by the 3D shell and the 2D documentation. */
export const WALL_LAYER_LABEL: Record<WallLayerKind, string> = {
  masonry: "murivo",
  insulation: "izolácia",
  solid: "plné murivo",
};
