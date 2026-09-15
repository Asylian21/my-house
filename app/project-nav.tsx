import type { ReactNode } from 'react';
import Link from '@/app/project-link';
import { Archive, BookOpen, Box, House, LayoutDashboard, PanelsTopLeft } from 'lucide-react';
import { ACTIVE_DESIGN, designHref, type TwinDesignSelection } from '@/lib/twin-design-selection';
import './project.css';

export type ProjectSection='overview'|'docs'|'3d'|'plan'|'archive';
export function ProjectNav({active,design=ACTIVE_DESIGN,archived=false,compact=false,actions}:{active:ProjectSection;design?:TwinDesignSelection;archived?:boolean;compact?:boolean;actions?:ReactNode}) {
  const links=[{id:'overview',href:'/',label:'Prehľad',Icon:LayoutDashboard},{id:'docs',href:'/docs',label:'Dokumentácia',Icon:BookOpen},{id:'3d',href:designHref('/3d'),label:'3D dom',Icon:Box},{id:'plan',href:designHref('/podorys'),label:'Pôdorys',Icon:PanelsTopLeft},{id:'archive',href:'/archiv',label:'Archív',Icon:Archive}];
  const displayedDesign=archived?design:ACTIVE_DESIGN;
  return <header className={`project-nav${compact?' project-nav-compact':''}`}><Link className="project-logo" href="/" aria-label="Dom 6012/26 · prehľad"><House size={23} strokeWidth={1.5}/><span>DOM <b>6012/26</b></span></Link><nav aria-label="Sekcie projektu">{links.map(({id,href,label,Icon})=><Link key={id} href={href} title={label} aria-label={label} aria-current={active===id?'page':undefined}><Icon size={17}/><span>{label}</span></Link>)}</nav><div className="project-nav-end"><span className="project-nav-version">{archived?'ARCHÍVNA ZOSTAVA':'HLAVNÝ NÁVRH'} <b>{`C / ${displayedDesign.heatingLayout} / ${displayedDesign.livingLayout}`}</b></span>{actions}</div></header>;
}
