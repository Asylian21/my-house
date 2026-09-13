import { normalizeHeatingLayout, type HeatingLayoutId } from './technical-design';
import { normalizeLivingLayout, type LivingLayoutId } from './twin-living-layouts';

export interface TwinDesignSelection {
  readonly livingLayout: LivingLayoutId;
  readonly heatingLayout: HeatingLayoutId;
}

/** Confirmed by the owner on 13 September 2026. All new work starts from C/B/B. */
export const ACTIVE_DESIGN: TwinDesignSelection = { livingLayout: 'B', heatingLayout: 'B' };
export const ARCHIVE_DESIGN: TwinDesignSelection = { livingLayout: 'A', heatingLayout: 'A' };
export const PREVIEW_DESIGN = ACTIVE_DESIGN;
export const ACTIVE_PLAN_URL = '/koncept-2d?variant=c&heating=b&living=b';

/** A URL carries one selection all the way from the plan into the live scene. */
export function designFromSearch(search: Pick<URLSearchParams, 'get'>, defaults?: TwinDesignSelection): TwinDesignSelection {
  return {
    livingLayout: normalizeLivingLayout(search.get('living') ?? defaults?.livingLayout),
    heatingLayout: normalizeHeatingLayout(search.get('heating') ?? defaults?.heatingLayout),
  };
}

export function designHref(path: '/navrh-3d' | '/koncept-2d' | '/3d' | '/podorys' | '/docs/manual', design: TwinDesignSelection = ACTIVE_DESIGN, archive = false): string {
  // Only archive routes may carry an alternative into another view.
  const selected = archive ? design : ACTIVE_DESIGN;
  const destination = archive ? (path === '/3d' || path === '/navrh-3d' ? '/archiv/3d' : '/archiv/podorys') : path;
  return `${destination}?variant=c&heating=${selected.heatingLayout.toLowerCase()}&living=${selected.livingLayout.toLowerCase()}${archive && path === '/docs/manual' ? '&view=manual' : ''}`;
}
