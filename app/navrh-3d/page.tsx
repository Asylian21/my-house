import { TwinStudio } from '../twin-studio';
import { designFromSearch, PREVIEW_DESIGN } from '@/lib/twin-design-selection';
import '../globals.css';
import './preview.css';

type PreviewProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

async function selectedDesign({searchParams}: PreviewProps) {
  const params = await searchParams;
  const get = (key: string) => {
    const value = params[key];
    return typeof value === 'string' ? value : null;
  };
  return designFromSearch({get}, PREVIEW_DESIGN);
}

export async function generateMetadata(props: PreviewProps) {
  const design=await selectedDesign(props);
  return {
    title: `Dom · Návrh C / Obývačka ${design.livingLayout} / Technická ${design.heatingLayout}`,
    description: 'Aktuálny priestorový návrh domu. Prehliadka interiéru Babylon s rozložením obývačky a technickej miestnosti podľa pôdorysu C.',
  };
}

export default async function DesignPreview(props: PreviewProps) {
  const design=await selectedDesign(props);
  return <TwinStudio key={`${design.livingLayout}-${design.heatingLayout}`} design={design}/>;
}
