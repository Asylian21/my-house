'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { DEFAULT_CONCEPT, DEFAULT_NESTED_CONCEPT } from '@/lib/floor-plan-concept';
import { DEFAULT_EXPERIMENT } from '@/lib/floor-plan-experiment';
import { StandardFloorPlanStudio } from './standard-studio';
import { ExperimentalFloorPlanStudio } from './experiment-studio';
import { normalizeVariant, usePlanView, type PlanVariant } from './variant-tabs';

export function FloorPlanStudio() {
  const searchParams=useSearchParams();
  const variant=normalizeVariant(searchParams.get('variant'));
  const [standardSettings,setStandardSettings]=useState(DEFAULT_CONCEPT);
  const [nestedSettings,setNestedSettings]=useState(DEFAULT_NESTED_CONCEPT);
  const [experimentSettings,setExperimentSettings]=useState(DEFAULT_EXPERIMENT);
  const view=usePlanView();
  const onVariantChange=(next:PlanVariant)=>{
    const restoreTabFocus=document.activeElement?.getAttribute('role')==='tab';
    const url=new URL(window.location.href);
    if(next==='d')url.searchParams.delete('variant');
    else url.searchParams.set('variant',next);
    // Shallow navigation preserves each study's dimensions while updating links.
    window.history.replaceState(null,'',url);
    if(restoreTabFocus)requestAnimationFrame(()=>document.getElementById(`floor-plan-tab-${next}`)?.focus());
  };
  const navigation={variant,onVariantChange,view};
  return variant==='e'
    ? <ExperimentalFloorPlanStudio {...navigation} rawSettings={experimentSettings} setSettings={setExperimentSettings}/>
    : <StandardFloorPlanStudio {...navigation} rawSettings={variant==='c'?nestedSettings:standardSettings} setSettings={variant==='c'?setNestedSettings:setStandardSettings}/>;
}
