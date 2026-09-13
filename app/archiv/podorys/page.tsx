import '../../globals.css';
import { FloorPlanStudio } from '../../koncept-2d/studio';

export const metadata = { title: 'Dom · Archív pôdorysov' };
export default function ArchivedPlanPage() {
  return <FloorPlanStudio archive />;
}
