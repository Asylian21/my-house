import { normalizeHeatingLayout, type HeatingLayoutId } from './technical-design';
import { normalizeLivingLayout, type LivingLayoutId } from './twin-living-layouts';

export interface TwinDesignSelection {
  readonly livingLayout: LivingLayoutId;
  readonly heatingLayout: HeatingLayoutId;
}

export const PREVIEW_DESIGN: TwinDesignSelection = { livingLayout: 'B', heatingLayout: 'B' };

/** A URL carries one selection all the way from the plan into the live scene. */
export function designFromSearch(search: Pick<URLSearchParams, 'get'>, defaults?: TwinDesignSelection): TwinDesignSelection {
  return {
    livingLayout: normalizeLivingLayout(search.get('living') ?? defaults?.livingLayout),
    heatingLayout: normalizeHeatingLayout(search.get('heating') ?? defaults?.heatingLayout),
  };
}

export function designHref(path: '/navrh-3d' | '/koncept-2d', design: TwinDesignSelection): string {
  return `${path}?variant=c&heating=${design.heatingLayout.toLowerCase()}&living=${design.livingLayout.toLowerCase()}`;
}
