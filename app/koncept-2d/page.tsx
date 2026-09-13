import type { Metadata } from 'next';
import '../globals.css';
import { FloorPlanStudio } from './studio';
import { requireActiveDesign, type DesignPageProps } from '../active-design-route';
export const metadata: Metadata = { title: 'Dom · Hlavný návrh C/B/B · Pôdorys', description: 'Hlavný návrh domu: dispozícia C, technická miestnosť B a obývacia zóna B.' };
export default async function ConceptPage({searchParams}: DesignPageProps) {
  await requireActiveDesign('/koncept-2d', searchParams);
  return <FloorPlanStudio />;
}
