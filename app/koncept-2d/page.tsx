import type { Metadata } from 'next';
import '../globals.css';
import { FloorPlanStudio } from './studio';
export const metadata: Metadata = { title: 'Dom · Dispozičné štúdio 2D', description: 'Interaktívne varianty pôdorysu v spoločnom 2D štúdiu. Spálňa do dvora, šatník a variant so zalomením a krytým zárezom pri garáži.' };
export default function ConceptPage() { return <FloorPlanStudio />; }
