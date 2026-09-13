import { TwinStudio } from '../twin-studio';
import { ACTIVE_DESIGN } from '@/lib/twin-design-selection';
import { requireActiveDesign, type DesignPageProps } from '../active-design-route';
import '../globals.css';
import './preview.css';

export function generateMetadata() {
  return {
    title: `Dom · Hlavný návrh C / ${ACTIVE_DESIGN.heatingLayout} / ${ACTIVE_DESIGN.livingLayout} · 3D`,
    description: 'Prehliadka hlavného návrhu domu: dispozícia C, technická miestnosť B a obývacia zóna B.',
  };
}

export default async function DesignPreview({searchParams}: DesignPageProps) {
  await requireActiveDesign('/3d', searchParams);
  return <TwinStudio key="main-design" design={ACTIVE_DESIGN}/>;
}
