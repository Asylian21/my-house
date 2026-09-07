import type { Metadata } from 'next';
import '../globals.css';
import { ExperimentalFloorPlanStudio } from './studio';
export const metadata: Metadata = { title:'Dom · 2D koncept 02',description:'Alternatívny pôdorys so zalomenou priečkou, súkromným šatníkom v spálni a krátkym vstupom v tvare L.' };
export default function ExperimentalConceptPage(){return <ExperimentalFloorPlanStudio/>;}
