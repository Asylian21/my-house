'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { DEFAULT_CONCEPT } from '@/versions/v2/lib/floor-plan-concept';
import { DEFAULT_EXPERIMENT } from '@/versions/v2/lib/floor-plan-experiment';
import { StandardFloorPlanStudio } from './standard-studio';
import { ExperimentalFloorPlanStudio } from './experiment-studio';
import { normalizeVariant, usePlanView, type PlanVariant } from './variant-tabs';

export function FloorPlanStudio() {
  const searchParams=useSearchParams();
  const variant=normalizeVariant(searchParams.get('variant'));
  const [standardSettings,setStandardSettings]=useState(DEFAULT_CONCEPT);
  const [experimentSettings,setExperimentSettings]=useState(DEFAULT_EXPERIMENT);
  const view=usePlanView();
  const onVariantChange=(next:PlanVariant)=>{
    const restoreTabFocus=document.activeElement?.getAttribute('role')==='tab';
    const url=new URL(window.location.href);
    if(next==='d')url.searchParams.delete('variant');
    else url.searchParams.set('variant',next);
    // Shallow navigation keeps both sets of dimensions while updating shareable links.
    window.history.replaceState(null,'',url);
    if(restoreTabFocus)requestAnimationFrame(()=>document.getElementById(`floor-plan-tab-${next}`)?.focus());
  };
  const navigation={variant,onVariantChange,view};
  return variant==='e'
    ? <ExperimentalFloorPlanStudio {...navigation} rawSettings={experimentSettings} setSettings={setExperimentSettings}/>
    : <StandardFloorPlanStudio {...navigation} rawSettings={standardSettings} setSettings={setStandardSettings}/>;
}
