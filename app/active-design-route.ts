import { redirect } from 'next/navigation';
import { ACTIVE_DESIGN } from '@/lib/twin-design-selection';

export type DesignPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

/** Old bookmarks must not silently select an archived design on a main route. */
export async function requireActiveDesign(path: string, searchParams: DesignPageProps['searchParams']) {
  const params = await searchParams;
  const active = { variant: 'c', heating: ACTIVE_DESIGN.heatingLayout.toLowerCase(), living: ACTIVE_DESIGN.livingLayout.toLowerCase() };
  if (!Object.entries(active).some(([key, value]) => params[key] !== undefined && params[key] !== value) && params.mode !== 'study') return;
  const canonical = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || key in active || key === 'mode') continue;
    for (const item of Array.isArray(value) ? value : [value]) canonical.append(key, item);
  }
  for (const [key, value] of Object.entries(active)) canonical.set(key, value);
  redirect(`${path}?${canonical}`);
}
