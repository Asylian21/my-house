import '../globals.css';
import { FloorPlanStudio } from '../koncept-2d/studio';
import { requireActiveDesign, type DesignPageProps } from '../active-design-route';
export const metadata={title:'Dom · Pôdorys C/B/B'};
export default async function PlanPage({searchParams}:DesignPageProps){
  await requireActiveDesign('/podorys',searchParams);
  return <FloorPlanStudio/>;
}
