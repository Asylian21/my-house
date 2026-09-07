'use client';

import { useRef, useState, type KeyboardEvent } from 'react';

export const EXPERIMENT_NAME='E · Zalomenie a krytý zárez';
const variants=[
  {id:'existing',label:'Existujúci model'},
  {id:'a',label:'A · Predsieň'},
  {id:'b',label:'B · Šatník'},
  {id:'c',label:'C · Výklenok'},
  {id:'d',label:'D · Súkromie'},
  {id:'e',label:EXPERIMENT_NAME},
] as const;
export type PlanVariant=typeof variants[number]['id'];
export interface VariantNavigationProps {
  variant: PlanVariant;
  onVariantChange: (variant:PlanVariant)=>void;
}
export function normalizeVariant(value:string|null):PlanVariant {
  return variants.find(variant=>variant.id===value)?.id??'d';
}

export function usePlanView() {
  const [full,setFull]=useState(false);
  const [dimensions,setDimensions]=useState(true);
  const [route,setRoute]=useState(true);
  const [selected,setSelected]=useState('1.10');
  const [zoom,setZoom]=useState(1);
  return {full,setFull,dimensions,setDimensions,route,setRoute,selected,setSelected,zoom,setZoom};
}
export type PlanViewState=ReturnType<typeof usePlanView>;

export function VariantTabs({variant,onVariantChange}:VariantNavigationProps) {
  const tabs=useRef<HTMLDivElement>(null);
  const onKeyDown=(event:KeyboardEvent<HTMLButtonElement>,index:number)=>{
    const next=event.key==='ArrowRight'?(index+1)%variants.length
      :event.key==='ArrowLeft'?(index-1+variants.length)%variants.length
      :event.key==='Home'?0:event.key==='End'?variants.length-1:null;
    if(next===null)return;
    event.preventDefault();
    // Manual activation: arrows move focus; Enter or Space selects the variant.
    tabs.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')[next]?.focus();
  };
  return <div ref={tabs} className="fp-segments" role="tablist" aria-label="Varianty pôdorysu">
    {variants.map((item,index)=><button key={item.id} type="button" role="tab"
      id={`floor-plan-tab-${item.id}`} aria-controls="floor-plan-panel"
      aria-selected={variant===item.id} tabIndex={variant===item.id?0:-1}
      onKeyDown={event=>onKeyDown(event,index)} onClick={()=>onVariantChange(item.id)}>
      {item.label}
    </button>)}
  </div>;
}
