import { TwinStudio } from '../../twin-studio';
import { ARCHIVE_DESIGN, designFromSearch } from '@/lib/twin-design-selection';
import type { DesignPageProps } from '../../active-design-route';
import '../../globals.css';
import '../../navrh-3d/preview.css';

async function selectedDesign({searchParams}: DesignPageProps) {
  const params = await searchParams;
  return designFromSearch({get: key => typeof params[key] === 'string' ? params[key] : null}, ARCHIVE_DESIGN);
}

export async function generateMetadata(props: DesignPageProps) {
  const design = await selectedDesign(props);
  return {title: `Dom · Archív C / ${design.heatingLayout} / ${design.livingLayout} · 3D`};
}

export default async function ArchivedPreview(props: DesignPageProps) {
  const design = await selectedDesign(props);
  return <TwinStudio key={`archive-${design.livingLayout}-${design.heatingLayout}`} archive design={design}/>;
}
