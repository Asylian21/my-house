'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { DEFAULT_CONCEPT, DEFAULT_NESTED_CONCEPT } from '@/lib/floor-plan-concept';
import { DEFAULT_EXPERIMENT } from '@/lib/floor-plan-experiment';
import { StandardFloorPlanStudio } from './standard-studio';
import { ExperimentalFloorPlanStudio } from './experiment-studio';
import { normalizeVariant, usePlanView, type PlanVariant } from './variant-tabs';
import { DocumentationStudio } from './documentation-studio';
import { ACTIVE_DESIGN, ARCHIVE_DESIGN, designFromSearch } from '@/lib/twin-design-selection';

export function FloorPlanStudio({archive=false}:{archive?:boolean}) {
  const searchParams=useSearchParams();
  const variant=archive?normalizeVariant(searchParams.get('variant')):'c';
  const [standardSettings,setStandardSettings]=useState(DEFAULT_CONCEPT);
  const [nestedSettings,setNestedSettings]=useState(DEFAULT_NESTED_CONCEPT);
  const [experimentSettings,setExperimentSettings]=useState(DEFAULT_EXPERIMENT);
  const view=usePlanView();
  const onVariantChange=(next:PlanVariant)=>{
    const restoreTabFocus=document.activeElement?.getAttribute('role')==='tab';
    const url=new URL(window.location.href);
    url.searchParams.set('variant',next);
    // Shallow navigation preserves each study's dimensions while updating links.
    window.history.replaceState(null,'',url);
    if(restoreTabFocus)requestAnimationFrame(()=>document.getElementById(`floor-plan-tab-${next}`)?.focus());
  };
  const navigation={variant,onVariantChange,view};
  const design=archive?designFromSearch(searchParams,ARCHIVE_DESIGN):ACTIVE_DESIGN;
  if(!archive||(variant==='c'&&searchParams.get('mode')!=='study'))return <DocumentationStudio key={`${archive}-${searchParams.get('view')}`} archive={archive} initialManual={searchParams.get('view')==='manual'} initialLivingLayout={design.livingLayout} initialHeatingLayout={design.heatingLayout}/>;
  return variant==='e'
    ? <ExperimentalFloorPlanStudio {...navigation} rawSettings={experimentSettings} setSettings={setExperimentSettings}/>
    : <StandardFloorPlanStudio {...navigation} rawSettings={variant==='c'?nestedSettings:standardSettings} setSettings={variant==='c'?setNestedSettings:setStandardSettings}/>;
}
