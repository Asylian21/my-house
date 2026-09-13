import '../../globals.css';
import { DocumentationStudio } from '../../koncept-2d/documentation-studio';
import { requireActiveDesign, type DesignPageProps } from '../../active-design-route';
export const metadata={title:'Dom · Manuál domu'};
export default async function ManualPage({searchParams}:DesignPageProps){
  await requireActiveDesign('/docs/manual',searchParams);
  return <DocumentationStudio initialManual/>;
}
