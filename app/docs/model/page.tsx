import '../../globals.css';
import '../../navrh-3d/preview.css';
import { TwinStudio } from '../../twin-studio';
import { ACTIVE_DESIGN } from '@/lib/twin-design-selection';
export const metadata={title:'Dom · Technický model a zdroje'};
export default function ModelPage(){return <TwinStudio design={ACTIVE_DESIGN} initialWorkspace="documentation"/>;}
