import '../globals.css';
import { DocumentLibrary } from './document-library';
import libraryData from '@/lib/document-library.generated.json';
import type { DocumentLibrary as Library } from '@/lib/document-library';
import { requireActiveDesign, type DesignPageProps } from '../active-design-route';
import { withHouseVisualizations } from '@/lib/house-visualizations';

export const metadata = { title: 'Dom · Knižnica dokumentácie', description: 'Vizualizácie domu zo všetkých strán a obývačky s katedrálovým stropom. Výkresy C/B/B, technické správy a podklady.' };
export default async function DocsPage({ searchParams }: DesignPageProps) {
  await requireActiveDesign('/docs', searchParams);
  const params = await searchParams;
  const initial = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) if (typeof value === 'string') initial.set(key, value);
  return <DocumentLibrary library={withHouseVisualizations(libraryData as Library)} initialParams={initial.toString()}/>;
}
