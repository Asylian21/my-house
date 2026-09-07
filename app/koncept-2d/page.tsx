import type { Metadata } from 'next';
import '../globals.css';
import { FloorPlanStudio } from './studio';
export const metadata: Metadata = { title: 'Dom · Dispozičné štúdio 2D', description: 'Súkromná spálňa do dvora a prístup do kúpeľne aj garáže cez šatníkový vstup. Interaktívny 2D koncept v zachovanom obryse domu.' };
export default function ConceptPage() { return <FloorPlanStudio />; }
