'use client';

import { memo, useCallback, useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from 'react';
import { flushSync } from 'react-dom';
import Link from '@/app/project-link';
import { ArrowDownToLine, ArrowLeft, ArrowUpRight, BookOpen, Check, ChevronDown, ChevronRight, CircleHelp, Contrast, FileSpreadsheet, Focus, Hand, ImageDown, Layers3, List, Maximize2, Minus, MousePointer2, Palette, PanelLeftClose, PanelLeftOpen, Plus, Printer, Ruler, Search, X } from 'lucide-react';
import { PLAN_CATEGORIES, PLAN_FULL_BOUNDS, PLAN_ITEM_BY_ID, PLAN_MESH_BY_ID, PLAN_ROOMS, fitPlanRect, formatMm, numberSk, planItemsFor, planRoomNotes, rectSize, searchPlanItems, zoomPlanAt, type PlanCategory, type PlanItem } from '@/lib/plan-documentation';
import { EXPORT_LEVELS, type ExportLevel } from '@/lib/plan-export';
import { rasterizePlanView } from '@/lib/plan-png';
import { DEFAULT_LIVING_LAYOUT_ID, normalizeLivingLayout, LIVING_LAYOUTS, LIVING_LAYOUT_IDS, type LivingLayoutId } from '@/lib/twin-living-layouts';
import type { RectMm } from '@/lib/twin-interior';
import { HEATING_SOURCES, normalizeHeatingLayout, HEATING_LAYOUTS, HEATING_LAYOUT_IDS, type HeatingLayoutId } from '@/lib/technical-design';
import { Box } from './plan-svg';
import { ItemMiniature, PlanDimensions, PlanGeometry, ROOM_COLORS, StaticPlan, TechnicalClearances, TechnicalLegend } from './documentation-plan';
import { ExportSheet, PX_PER_MM, SHEET } from './export-sheet';
import './documentation.css';
import { ACTIVE_DESIGN, designHref } from '@/lib/twin-design-selection';
import { useSearchParams } from 'next/navigation';
import { ProjectNav } from '../project-nav';
import { ParcelGeometry } from '../site-drawing';
import { HOUSE_SETBACKS, PARCEL_BOUNDS } from '@/lib/plan-site';
import { ACOUSTIC_ASSEMBLY, OFFICE_ACOUSTIC_ASSEMBLY, ACOUSTIC_WALL_SPECS } from '@/lib/acoustic-walls';
import { AcousticWallDetail } from './acoustic-wall-detail';
import './workspace.css';
import './inspector.css';

type Point={x:number;y:number};
type Units='mm'|'cm'|'m';
const INSPECTOR_TABS=[['selection','Výber',MousePointer2],['design','O návrhu',Layers3]] as const;
const INITIAL_LAYERS={furniture:true,equipment:true,lighting:false,walls:true,openings:true,finishes:true};
const defaultView=fitPlanRect(PLAN_FULL_BOUNDS,1.25,0);
const partsCount=(items:readonly PlanItem[])=>items.reduce((sum,item)=>sum+item.meshes.length,0);
/** File-name suffix so exports of the alternative living-room layout do not overwrite the default ones. */
const layoutFileSuffix=(layout:LivingLayoutId)=>layout===DEFAULT_LIVING_LAYOUT_ID?'':`-obyvacka-${layout.toLowerCase()}`;
function download(name:string,content:string|Blob,type:string){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
interface ExportJob { level:ExportLevel; color:boolean; livingLayout:LivingLayoutId; heatingLayout:HeatingLayoutId }
/** Rasterises the hidden export sheet to a PNG; falls back to a smaller canvas when the browser refuses the full size. */
function rasterizeSheet(source:SVGSVGElement,scales:number[]):Promise<{blob:Blob;scale:number}> {
  const markup=new XMLSerializer().serializeToString(source);
  const url=URL.createObjectURL(new Blob([markup],{type:'image/svg+xml;charset=utf-8'}));
  return new Promise((resolve,reject)=>{
    const image=new Image();
    image.onerror=()=>{URL.revokeObjectURL(url);reject(new Error('SVG sa nepodarilo vykresliť.'));};
    image.onload=()=>{
      const attempt=(index:number)=>{
        const scale=scales[index];if(scale===undefined){URL.revokeObjectURL(url);reject(new Error('Prehliadač odmietol vytvoriť PNG.'));return;}
        const canvas=document.createElement('canvas');canvas.width=Math.round(SHEET.w*scale);canvas.height=Math.round(SHEET.h*scale);
        const ctx=canvas.getContext('2d');if(!ctx){attempt(index+1);return;}
        ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(image,0,0,canvas.width,canvas.height);
        canvas.toBlob(blob=>{if(blob){URL.revokeObjectURL(url);resolve({blob,scale});}else attempt(index+1);},'image/png');
      };
      attempt(0);
    };
    image.src=url;
  });
}
function Dimensions({rect,height,unit}:{rect:RectMm;height:number;unit:Units}) {
  const [x,y]=rectSize(rect);
  return <dl className="pd-dimension-grid"><div><dt>Rozmer ↔</dt><dd>{formatMm(x,unit)}</dd></div><div><dt>Rozmer ↕</dt><dd>{formatMm(y,unit)}</dd></div><div><dt>Výška</dt><dd>{formatMm(height,unit)}</dd></div></dl>;
}

export function DocumentationStudio({archive=false,initialManual=false,initialLivingLayout=ACTIVE_DESIGN.livingLayout,initialHeatingLayout=ACTIVE_DESIGN.heatingLayout}:{archive?:boolean;initialManual?:boolean;initialLivingLayout?:LivingLayoutId;initialHeatingLayout?:HeatingLayoutId}) {
  const searchParams=useSearchParams();
  const siteVisible=searchParams.get('site')==='1';
  const [viewScope,setViewScope]=useState(siteVisible);
  const siteVisibleRef=useRef(siteVisible);
  const planBounds=siteVisible?PARCEL_BOUNDS:PLAN_FULL_BOUNDS;
  const svg=useRef<SVGSVGElement>(null),canvas=useRef<HTMLDivElement>(null),help=useRef<HTMLDialogElement>(null),inspectorTitle=useRef<HTMLHeadingElement>(null);
  const [view,setView]=useState(defaultView),[selectedId,setSelectedId]=useState<string|null>(null),[componentId,setComponentId]=useState<string|null>(null);
  const livingLayout=archive?normalizeLivingLayout(searchParams.get('living')??initialLivingLayout):ACTIVE_DESIGN.livingLayout;
  const heatingLayout=archive?normalizeHeatingLayout(searchParams.get('heating')??initialHeatingLayout):ACTIVE_DESIGN.heatingLayout;
  const items=useMemo(()=>planItemsFor(livingLayout,heatingLayout),[livingLayout,heatingLayout]);
  const allParts=useMemo(()=>partsCount(items),[items]);
  const [roomId,setRoomId]=useState(''),[query,setQuery]=useState(''),[category,setCategory]=useState<PlanCategory|'all'>('all');
  const [layers,setLayers]=useState(INITIAL_LAYERS),[details,setDetails]=useState(false),[overhead,setOverhead]=useState(false),[dimensions,setDimensions]=useState(true),[clearances,setClearances]=useState(true),[unit,setUnit]=useState<Units>('cm');
  const [tool,setTool]=useState<'select'|'pan'|'measure'>('select'),[measurement,setMeasurement]=useState<Point[]>([]),[hoverPoint,setHoverPoint]=useState<Point|null>(null);
  const [libraryOpen,setLibraryOpen]=useState(false);
  const libraryToggle=useRef<HTMLButtonElement>(null),mobileLibraryToggle=useRef<HTMLButtonElement>(null),librarySearch=useRef<HTMLInputElement>(null);
  const [leftTab,setLeftTab]=useState<'rooms'|'objects'>('rooms'),[mobilePanel,setMobilePanel]=useState<'rooms'|'plan'|'detail'>('plan');
  const [inspectorTab,setInspectorTab]=useState<'selection'|'design'>('selection');
  const selectionPanel=useRef<HTMLDivElement>(null);
  const closeLibrary=useCallback(()=>{setLibraryOpen(false);setMobilePanel('plan');(window.matchMedia('(max-width: 800px)').matches?mobileLibraryToggle:libraryToggle).current?.focus();},[]);
  useEffect(()=>{if((window.matchMedia('(max-width: 800px)').matches?mobilePanel==='rooms':libraryOpen))librarySearch.current?.focus({preventScroll:true});},[libraryOpen,mobilePanel]);
  useEffect(()=>{
    if(!libraryOpen&&mobilePanel!=='rooms')return;
    const onEscape=(event:KeyboardEvent)=>{if(event.key==='Escape'&&event.target instanceof Node&&document.getElementById('pd-library')?.contains(event.target)){event.preventDefault();closeLibrary();}};
    window.addEventListener('keydown',onEscape);return()=>window.removeEventListener('keydown',onEscape);
  },[libraryOpen,mobilePanel,closeLibrary]);
  const [manualOpen,setManualOpen]=useState(initialManual),[printParts,setPrintParts]=useState(false),[announcement,setAnnouncement]=useState('');
  const [canvasWidth,setCanvasWidth]=useState(800),[partsQuery,setPartsQuery]=useState('');
  const [exportJob,setExportJob]=useState<ExportJob|null>(null),[exportColor,setExportColor]=useState(true);
  const [exportingView,setExportingView]=useState(false);
  const [viewExportError,setViewExportError]=useState('');
  const viewExportPending=useRef(false);
  const exportHost=useRef<HTMLDivElement>(null);
  const aspectRef=useRef(1.25);
  const viewRef=useRef(view);const pointers=useRef(new Map<number,Point>());const moved=useRef(false);const suppressClick=useRef(false);
  const lastGesture=useRef<{point:Point;distance:number}|null>(null);const pointerOrigin=useRef<Point|null>(null);
  if(viewScope!==siteVisible){setViewScope(siteVisible);setView(fitPlanRect(siteVisible?PARCEL_BOUNDS:PLAN_FULL_BOUNDS,view.width/view.height,0));setRoomId('');setSelectedId(null);}
  useEffect(()=>{siteVisibleRef.current=siteVisible;},[siteVisible]);
  useEffect(()=>{viewRef.current=view;},[view]);
  useEffect(()=>{
    const preparePrint=()=>flushSync(()=>setManualOpen(true));
    const finishPrint=()=>setManualOpen(initialManual);
    window.addEventListener('beforeprint',preparePrint);window.addEventListener('afterprint',finishPrint);
    return()=>{window.removeEventListener('beforeprint',preparePrint);window.removeEventListener('afterprint',finishPrint);};
  },[initialManual]);
  useEffect(()=>{
    const el=canvas.current;if(!el)return;
    let first=true;
    const observer=new ResizeObserver(entries=>{
      const {width,height}=entries[0].contentRect;if(!width||!height)return;
      const previousAspect=aspectRef.current;
      setCanvasWidth(width);aspectRef.current=width/height;
      const fitInitial=first;first=false;
      setView(current=>{
        const bounds=siteVisibleRef.current?PARCEL_BOUNDS:PLAN_FULL_BOUNDS;
        const previousFit=fitPlanRect(bounds,previousAspect,0);
        const wasFitted=Math.abs(current.width-previousFit.width)<1&&Math.abs(current.x-previousFit.x)<1&&Math.abs(current.y-previousFit.y)<1;
        return fitInitial||wasFitted?fitPlanRect(bounds,width/height,0):{...current,y:current.y+current.height/2-current.width/(width/height)/2,height:current.width/(width/height)};
      });
    });observer.observe(el);return()=>observer.disconnect();
  },[]);
  useEffect(()=>{
    const el=svg.current;if(!el)return;
    const wheel=(event:WheelEvent)=>{event.preventDefault();const r=el.getBoundingClientRect();const v=viewRef.current;
      const anchor={x:v.x+(event.clientX-r.left)/r.width*v.width,y:v.y+(event.clientY-r.top)/r.height*v.height};
      setView(zoomPlanAt(v,Math.exp(Math.max(-100,Math.min(100,event.deltaY))*.003),anchor));};
    el.addEventListener('wheel',wheel,{passive:false});return()=>el.removeEventListener('wheel',wheel);
  },[]);
  useEffect(()=>{selectionPanel.current?.scrollTo({top:0});},[selectedId,roomId,componentId,inspectorTab,mobilePanel]);
  useEffect(()=>{
    if(mobilePanel==='detail'&&window.matchMedia('(max-width: 800px)').matches)inspectorTitle.current?.focus({preventScroll:true});
  },[selectedId,roomId,mobilePanel]);
  const selected=selectedId?PLAN_ITEM_BY_ID.get(selectedId):undefined;
  const component=componentId?PLAN_MESH_BY_ID.get(componentId)?.mesh:undefined;
  const room=PLAN_ROOMS.find(r=>r.id===roomId),selectedRoom=PLAN_ROOMS.find(r=>r.id===selected?.roomId);
  const results=useMemo(()=>searchPlanItems(query,roomId,category,livingLayout,heatingLayout),[query,roomId,category,livingLayout,heatingLayout]);
  const zoom=Math.round(fitPlanRect(PLAN_FULL_BOUNDS,view.width/view.height,0).width/view.width*100);
  const fit=(rect:RectMm=PLAN_FULL_BOUNDS,padding=700)=>{const r=canvas.current?.getBoundingClientRect();setView(fitPlanRect(rect,r&&r.height?r.width/r.height:aspectRef.current,padding));};
  const revealSelection=()=>{setInspectorTab('selection');selectionPanel.current?.scrollTo({top:0});};
  const openLibrary=(tab:'rooms'|'objects')=>{setLeftTab(tab);setLibraryOpen(true);setMobilePanel('rooms');};
  const choose=(item:PlanItem,meshId:string|null=null,focus=false)=>{
    revealSelection();
    setSelectedId(item.id);setComponentId(meshId);setPartsQuery('');setMobilePanel('detail');
    setLayers(l=>({...l,[item.category]:true}));setAnnouncement(`${item.name}, ${PLAN_ROOMS.find(r=>r.id===item.roomId)?.name}. Detail a rozmery sú otvorené.`);
    if(focus)fit(meshId?PLAN_MESH_BY_ID.get(meshId)!.mesh.rect:item.rect,900);
  };
  const chooseRoom=(id:string)=>{revealSelection();setRoomId(id);setSelectedId(null);setComponentId(null);setQuery('');setMobilePanel('plan');const r=PLAN_ROOMS.find(room=>room.id===id);fit(r?.bounds??PLAN_FULL_BOUNDS,id?1100:0);};
  const chooseLivingLayout=(next:LivingLayoutId)=>{
    if(!archive||next===livingLayout)return;
    // A selected piece of the other arrangement would no longer be drawn.
    if(selected?.layout){setSelectedId(null);setComponentId(null);}
    const url=new URL(window.location.href);
    url.searchParams.set('living',next.toLowerCase());
    window.history.replaceState(null,'',url);
    setAnnouncement(`Obývačka vo variante ${next}: ${LIVING_LAYOUTS[next].label}. Pôdorys, súpis aj exporty sú prepnuté.`);
  };
  const chooseHeatingLayout=(next:HeatingLayoutId)=>{
    if(!archive||next===heatingLayout)return;
    setSelectedId(null);setComponentId(null);setPartsQuery('');
    setRoomId('ROOM-1-07');setQuery('');setMobilePanel('plan');
    fit(PLAN_ROOMS.find(r=>r.id==='ROOM-1-07')!.bounds,1100);
    const url=new URL(window.location.href);url.searchParams.set('heating',next.toLowerCase());
    window.history.replaceState(null,'',url);
    setAnnouncement(`Technická miestnosť ${next}: ${HEATING_LAYOUTS[next].label}. Rozmery, súpis a exporty sú prepnuté.`);
  };
  const pointAt=(client:Point):Point=>{const r=svg.current!.getBoundingClientRect(),v=viewRef.current;return {x:v.x+(client.x-r.left)/r.width*v.width,y:v.y+(client.y-r.top)/r.height*v.height};};
  const onPointerDown=(event:ReactPointerEvent<SVGSVGElement>)=>{
    if(event.button!==0&&event.button!==1)return;
    const p={x:event.clientX,y:event.clientY};pointers.current.set(event.pointerId,p);event.currentTarget.setPointerCapture(event.pointerId);
    if(pointers.current.size===1){moved.current=false;pointerOrigin.current=p;lastGesture.current={point:p,distance:0};}
    else{moved.current=true;const [a,b]=[...pointers.current.values()];lastGesture.current={point:{x:(a.x+b.x)/2,y:(a.y+b.y)/2},distance:Math.hypot(a.x-b.x,a.y-b.y)};}
  };
  const onPointerMove=(event:ReactPointerEvent<SVGSVGElement>)=>{
    const p={x:event.clientX,y:event.clientY};
    if(tool==='measure')setHoverPoint(pointAt(p));
    if(!pointers.current.has(event.pointerId)||!lastGesture.current)return;
    pointers.current.set(event.pointerId,p);const r=svg.current!.getBoundingClientRect(),v=viewRef.current,previous=lastGesture.current;
    if(pointers.current.size>1){const [a,b]=[...pointers.current.values()],mid={x:(a.x+b.x)/2,y:(a.y+b.y)/2},distance=Math.hypot(a.x-b.x,a.y-b.y);
      if(distance>0&&previous.distance>0){const next=zoomPlanAt(v,previous.distance/distance,pointAt(previous.point));setView({...next,x:next.x-(mid.x-previous.point.x)/r.width*next.width,y:next.y-(mid.y-previous.point.y)/r.height*next.height});}
      lastGesture.current={point:mid,distance};moved.current=true;
    }else{
      if(pointerOrigin.current&&Math.hypot(p.x-pointerOrigin.current.x,p.y-pointerOrigin.current.y)>4)moved.current=true;
      if(moved.current){setView({...v,x:v.x-(p.x-previous.point.x)/r.width*v.width,y:v.y-(p.y-previous.point.y)/r.height*v.height});}
      lastGesture.current={point:p,distance:0};
    }
  };
  const onPointerUp=(event:ReactPointerEvent<SVGSVGElement>)=>{
    pointers.current.delete(event.pointerId);suppressClick.current=moved.current||event.type==='pointercancel';
    if(event.currentTarget.hasPointerCapture(event.pointerId))event.currentTarget.releasePointerCapture(event.pointerId);
    const remaining=[...pointers.current.values()][0];lastGesture.current=remaining?{point:remaining,distance:0}:null;
  };
  const onPlanClick=(event:React.MouseEvent<SVGSVGElement>)=>{
    if(suppressClick.current){suppressClick.current=false;return;}
    if(tool==='measure') {const p=pointAt({x:event.clientX,y:event.clientY});setMeasurement(previous=>previous.length===1?[previous[0],p]:[p]);return;}
    if(tool==='pan')return;
    // Pointer capture retargets the click to the SVG; hit-test the final point.
    const target=document.elementFromPoint(event.clientX,event.clientY)?.closest('[data-item],[data-room]');
    const id=target?.getAttribute('data-item');if(id&&PLAN_ITEM_BY_ID.has(id)){choose(PLAN_ITEM_BY_ID.get(id)!,details?target?.getAttribute('data-component')??null:null);return;}
    const pickedRoom=target?.getAttribute('data-room');if(pickedRoom){revealSelection();setRoomId(pickedRoom);setSelectedId(null);setComponentId(null);setMobilePanel('detail');setAnnouncement(`Vybraná miestnosť: ${PLAN_ROOMS.find(r=>r.id===pickedRoom)?.name}.`);return;}
    setSelectedId(null);setComponentId(null);
  };
  const changeTool=(next:typeof tool)=>{setTool(next);if(next!=='measure'){setMeasurement([]);setHoverPoint(null);}};
  const zoomBy=(factor:number)=>setView(v=>zoomPlanAt(v,factor,{x:v.x+v.width/2,y:v.y+v.height/2}));
  const exportCsv=()=>{
    const rows=[['Miestnosť','Prvok','Súčasť','ID','X min (mm)','Y min (mm)','Rozmer X (mm)','Rozmer Y (mm)','Výška (mm)','Spodná hrana (mm)','Horná hrana (mm)'],...items.flatMap(item=>item.meshes.map(mesh=>[PLAN_ROOMS.find(r=>r.id===item.roomId)?.name??'Terasy pri dome',item.name,mesh.name,mesh.id,mesh.rect.x0,mesh.rect.y0,mesh.rect.x1-mesh.rect.x0,mesh.rect.y1-mesh.rect.y0,mesh.z1-mesh.z0,mesh.z0,mesh.z1]))];
    const csv=rows.map(row=>row.map(v=>`"${String(v).replaceAll('"','""')}"`).join(';')).join('\r\n');download(`dom-variant-c${layoutFileSuffix(livingLayout)}-technicka-${heatingLayout.toLowerCase()}-kompletny-supis.csv`,'\uFEFF'+csv,'text/csv;charset=utf-8');setAnnouncement('Kompletný súpis bol stiahnutý.');
  };
  const exportSvg=()=>{
    const source=siteVisible?svg.current:document.getElementById('pd-export-source')?.querySelector('svg');if(!source)return;
    const copy=source.cloneNode(true) as SVGSVGElement;copy.setAttribute('xmlns','http://www.w3.org/2000/svg');copy.setAttribute('width','1600');copy.setAttribute('height','1500');
    if(siteVisible){const b=PARCEL_BOUNDS;copy.setAttribute('viewBox',`${b.x0} ${-b.y1} ${b.x1-b.x0} ${b.y1-b.y0}`);copy.setAttribute('height',String(Math.round(1600*(b.y1-b.y0)/(b.x1-b.x0))));}
    const style=document.createElementNS('http://www.w3.org/2000/svg','style');style.textContent='text{font-family:Arial,sans-serif}.pd-doors path{fill:none;stroke:#536478;stroke-width:12}.fp-door-gap{fill:#fff}.pd-room-labels text{paint-order:stroke}';copy.prepend(style);
    download(`dom-variant-c${layoutFileSuffix(livingLayout)}-technicka-${heatingLayout.toLowerCase()}-${siteVisible?'dom-na-parcele':'podorys'}.svg`,new XMLSerializer().serializeToString(copy),'image/svg+xml');setAnnouncement('Vektorový pôdorys bol stiahnutý.');
  };
  const exportViewPng=async()=>{
    if(viewExportPending.current||exportJob)return;
    const source=svg.current,host=canvas.current;
    if(!source||!host){const message='Export PNG sa nepodaril: najprv zobrazte 2D pôdorys.';setViewExportError(message);setAnnouncement(message);return;}
    viewExportPending.current=true;setExportingView(true);setViewExportError('');setAnnouncement('Pripravujem PNG aktuálneho 2D pohľadu.');
    try {
      const result=await rasterizePlanView(source,getComputedStyle(host).backgroundColor);
      download(`dom-variant-c${layoutFileSuffix(livingLayout)}-technicka-${heatingLayout.toLowerCase()}-${siteVisible?'dom-na-parcele':'interier'}-aktualny-pohlad.png`,result.blob,'image/png');
      setAnnouncement(`Aktuálny 2D pohľad bol stiahnutý ako PNG ${result.width} × ${result.height} px.`);
    } catch(error) {
      const message=`Export PNG sa nepodaril: ${error instanceof Error?error.message:'Skúste to znova.'}`;
      setViewExportError(message);setAnnouncement(message);
    } finally {
      viewExportPending.current=false;setExportingView(false);
    }
  };
  useEffect(()=>{
    if(!exportJob)return;
    const source=exportHost.current?.querySelector('svg');
    if(!source){setExportJob(null);setAnnouncement('Export PNG sa nepodaril: výkres sa nevykreslil.');return;}
    let cancelled=false;
    const mode=exportJob.color?'farebny':'ciernobiely';
    rasterizeSheet(source,[PX_PER_MM,PX_PER_MM*.66,PX_PER_MM*.45]).then(({blob,scale})=>{
      if(cancelled)return;
      download(`dom-variant-c${layoutFileSuffix(exportJob.livingLayout)}-technicka-${exportJob.heatingLayout.toLowerCase()}-podorys-L${exportJob.level}-${mode}.png`,blob,'image/png');
      setAnnouncement(`Pôdorys úrovne ${exportJob.level} (${exportJob.color?'farebný':'čiernobiely'}) bol stiahnutý ako PNG ${Math.round(SHEET.w*scale)} × ${Math.round(SHEET.h*scale)} px.`);
    }).catch((error:Error)=>{if(!cancelled)setAnnouncement(`Export PNG sa nepodaril: ${error.message}`);}).finally(()=>{if(!cancelled)setExportJob(null);});
    return ()=>{cancelled=true;};
  },[exportJob]);
  const startExport=(level:ExportLevel)=>{setExportJob({level,color:exportColor,livingLayout,heatingLayout});setAnnouncement(`Pripravujem PNG pôdorysu úrovne ${level}.`);};
  const measureEnd=measurement[1]??hoverPoint,measureDistance=measurement[0]&&measureEnd?Math.hypot(measureEnd.x-measurement[0].x,measureEnd.y-measurement[0].y):null;
  const toggleSite=(show:boolean)=>{setRoomId('');setSelectedId(null);const url=new URL(window.location.href);if(show)url.searchParams.set('site','1');else url.searchParams.delete('site');window.history.replaceState(null,'',url);};
  const scaleMm=view.width>50000?5000:view.width>7000?1000:100;
  return <main className="pd-root" data-library-open={libraryOpen} data-mobile-panel={mobilePanel} data-manual={manualOpen}>
    <h1 className="pd-visually-hidden">{manualOpen?'Manuál domu':'Pôdorys domu'}</h1>
    <ProjectNav compact archived={archive} active={archive?'archive':manualOpen?'docs':'plan'} design={{livingLayout,heatingLayout}} actions={archive?
      <details className="pd-menu"><summary aria-label="Zobrazenia archívnej zostavy" title="Zobrazenia archívnej zostavy"><Layers3 size={17}/></summary><div className="pd-menu-panel pd-downloads">
        <Link href={designHref('/3d',{livingLayout,heatingLayout},true)}><Layers3 size={16}/>3D archívnej zostavy</Link>
        <Link href={designHref(manualOpen?'/podorys':'/docs/manual',{livingLayout,heatingLayout},true)}><BookOpen size={16}/>{manualOpen?'Späť na pôdorys':'Manuál domu'}</Link>
      </div></details>:
      <Link className="pd-manual-link" title={manualOpen?'Späť na pôdorys':'Manuál domu'} aria-label={manualOpen?'Späť na pôdorys':'Manuál domu'} href={designHref(manualOpen?'/podorys':'/docs/manual')}><BookOpen size={17}/><span>{manualOpen?'Pôdorys':'Manuál domu'}</span></Link>}/>
    <div className="pd-mobile-tabs" aria-label="Panely dokumentácie">{([['rooms','Miestnosti',List],['plan','Pôdorys',Layers3],['detail','Detail',Ruler]] as const).map(([id,label,Icon])=><button key={id} ref={id==='rooms'?mobileLibraryToggle:undefined} aria-controls={id==='rooms'?'pd-library':undefined} aria-expanded={id==='rooms'?mobilePanel==='rooms':undefined} aria-pressed={mobilePanel===id} onClick={()=>setMobilePanel(id==='rooms'&&mobilePanel==='rooms'?'plan':id)}><Icon size={16}/>{label}</button>)}</div>
    <div className="pd-workspace">
      <aside id="pd-library" className="pd-library" aria-label="Miestnosti a súpis predmetov"><div className="pd-library-heading"><strong>Miestnosti a prvky</strong><button aria-label="Zavrieť zoznam miestností" title="Zavrieť zoznam miestností (Esc)" onClick={closeLibrary}><PanelLeftClose size={19}/></button></div><div className="pd-search"><Search size={17}/><input ref={librarySearch} aria-label="Hľadať prvky v zvolenej oblasti" value={query} placeholder="Nájsť nábytok, stenu…" onChange={event=>{setQuery(event.target.value);setLeftTab('objects');}}/>{query&&<button aria-label="Vymazať hľadanie" onClick={()=>setQuery('')}><X size={14}/></button>}</div>
        <div className="pd-library-tabs"><button aria-pressed={leftTab==='rooms'} onClick={()=>setLeftTab('rooms')}>Miestnosti <span>{PLAN_ROOMS.length}</span></button><button aria-pressed={leftTab==='objects'} onClick={()=>setLeftTab('objects')}>Prvky <span>{items.length}</span></button></div>
        <div className="pd-library-scroll">
          {leftTab==='rooms'?<><button className={`pd-room-row pd-all-rooms ${!roomId?'active':''}`} onClick={()=>chooseRoom('')}><Layers3 size={19}/><span>Celý dom<small>Prízemie · variant C</small></span><Focus size={16}/></button><div className="pd-list-caption">MIESTNOSŤ <span>PLOCHA</span></div>{PLAN_ROOMS.map((r,i)=><button className={`pd-room-row ${roomId===r.id?'active':''}`} key={r.id} onClick={()=>chooseRoom(r.id)}><span className="pd-room-number" style={{background:ROOM_COLORS[i]}}>{r.number.slice(2)}</span><span>{r.name}<small>{numberSk(r.area,2)} m²</small></span><ChevronRight size={14}/></button>)}<button className="pd-room-row" onClick={()=>{setRoomId('EXTERIOR');setLeftTab('objects');fit(planBounds,0);}}><Layers3 size={18}/><span>Terasy pri dome<small>Vonkajšie sedenie</small></span><ChevronRight size={14}/></button></>:<>
            <div className="pd-inventory-filters"><label>Oblasť<select value={roomId} onChange={event=>setRoomId(event.target.value)}><option value="">Celý dom</option><option value="EXTERIOR">Terasy pri dome</option>{PLAN_ROOMS.map(r=><option key={r.id} value={r.id}>{r.number} · {r.name}</option>)}</select></label><label>Kategória<select value={category} onChange={event=>setCategory(event.target.value as typeof category)}><option value="all">Všetky prvky</option>{Object.entries(PLAN_CATEGORIES).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label></div>
            <p className="pd-results-count">{results.length} prvkov{query&&' vo výsledkoch'}</p>
            {results.length===0?<div className="pd-empty"><Search/><strong>Nič sa nenašlo</strong><p>Skús kratší názov alebo vyhľadávanie v celom dome.</p><button onClick={()=>{setQuery('');setRoomId('');setCategory('all');}}>Zobraziť všetky prvky</button></div>:results.map(item=><button className={`pd-object-row ${item.id===selectedId?'active':''}`} key={item.id} onClick={()=>choose(item,null,true)}><span className={`pd-category-dot ${item.category}`}/><span>{item.name}<small>{PLAN_ROOMS.find(r=>r.id===item.roomId)?.name??'Terasy pri dome'}</small></span><ChevronRight size={14}/></button>)}
          </>}
        </div><div className="pd-library-footer"><Check size={14}/><span>Geometria prevzatá z 3D<small>{numberSk(allParts)} merateľných súčastí</small></span></div>
      </aside>
      <section className="pd-drawing" aria-label="Interaktívny pôdorys">
        <div className="pd-drawing-top">
          <div className="pd-workspace-tools"><button ref={libraryToggle} className="pd-library-toggle" aria-controls="pd-library" aria-expanded={libraryOpen} aria-label={libraryOpen?'Zavrieť zoznam miestností':'Otvoriť zoznam miestností'} title="Miestnosti a prvky" onClick={()=>setLibraryOpen(open=>!open)}>{libraryOpen?<PanelLeftClose size={18}/>:<PanelLeftOpen size={18}/>}<span>Miestnosti</span></button>
          <div className="pd-site-switch" role="group" aria-label="Rozsah pôdorysu"><button aria-pressed={!siteVisible} onClick={()=>toggleSite(false)}>Interiér<span> domu</span></button><button aria-pressed={siteVisible} onClick={()=>toggleSite(true)}><span className="pd-scope-desktop">Dom na parcele</span><span className="pd-scope-mobile">Pozemok</span></button></div></div>
          {roomId&&<div className="pd-room-selection" role="group" aria-label="Vybraná miestnosť"><span title={room?.name??'Terasy pri dome'}>{room?.name??'Terasy pri dome'}</span><button aria-label="Zrušiť výber miestnosti" title="Zrušiť výber · zobraziť celý dom" onClick={()=>{chooseRoom('');svg.current?.focus({preventScroll:true});}}><X size={16}/></button></div>}
          <div className="pd-drawing-options">
          <details className="pd-menu"><summary aria-label="Vrstvy plánu"><Layers3 size={17}/><span>Vrstvy</span><ChevronDown size={12}/></summary><div className="pd-menu-panel"><b>Zobraziť v pláne</b>{Object.entries(PLAN_CATEGORIES).map(([id,label])=><label key={id}><input type="checkbox" checked={layers[id as PlanCategory]} onChange={event=>setLayers(prev=>({...prev,[id]:event.target.checked}))}/>{label}</label>)}<hr/><label><input type="checkbox" checked={clearances} onChange={e=>setClearances(e.target.checked)}/>Obsluha technickej miestnosti</label><label><input type="checkbox" checked={overhead} onChange={e=>setOverhead(e.target.checked)}/>Horné skrinky a stropné prvky</label><label><input type="checkbox" checked={details} onChange={e=>setDetails(e.target.checked)}/>Všetky drobné súčasti</label><label><input type="checkbox" checked={dimensions} onChange={e=>setDimensions(e.target.checked)}/>Kóty pôdorysu</label></div></details>
          <details className="pd-menu pd-export-menu"><summary aria-label="Export pôdorysu do PNG"><ImageDown size={17}/><span>Export PNG</span><ChevronDown size={12}/></summary><div className="pd-menu-panel pd-export-panel">
            <button className="pd-export-view" disabled={exportingView||exportJob!==null} aria-busy={exportingView} onClick={exportViewPng}><ImageDown size={19}/><span><strong>{exportingView?'Pripravujem PNG…':'Aktuálny 2D pohľad PNG'}</strong><small>Rovnaký výrez, farby a zapnuté vrstvy.</small></span></button>
            {viewExportError&&<p className="pd-export-error">{viewExportError}</p>}
            <hr/><b>Technický výkres · A1 · 1 : 50 · PNG</b>
            <div className="pd-export-mode" role="group" aria-label="Farebnosť exportu"><button aria-pressed={exportColor} onClick={()=>setExportColor(true)}><Palette size={14}/>Farebný</button><button aria-pressed={!exportColor} onClick={()=>setExportColor(false)}><Contrast size={14}/>Čiernobiely</button></div>
            <p>Úroveň podrobnosti kótovania</p>
            {EXPORT_LEVELS.map(spec=><button key={spec.level} className="pd-export-level" disabled={exportJob!==null||exportingView} onClick={()=>startExport(spec.level)}><span>L{spec.level}</span><span><strong>{spec.title}</strong><small>{spec.summary}</small></span></button>)}
            <small className="pd-export-note">{exportJob?`Pripravujem PNG úrovne ${exportJob.level}…`:'Modulové osi A–F (šírka) a 1–6 (hĺbka), kódy stien, otvorov a prvkov robia výkres čitateľným aj v čiernobielej tlači.'}</small>
          </div></details>
          <details className="pd-menu"><summary aria-label="Stiahnuť dokumentáciu"><ArrowDownToLine size={17}/></summary><div className="pd-menu-panel pd-downloads"><Link href={designHref('/docs/manual',{livingLayout,heatingLayout},archive)}><BookOpen size={16}/>Manuál a tlač do PDF</Link><button onClick={exportSvg}><ArrowDownToLine size={16}/>{siteVisible?'Dom na parcele SVG':'Vektorový pôdorys SVG'}</button><button disabled={exportingView||exportJob!==null} aria-busy={exportingView} onClick={exportViewPng}><ImageDown size={16}/>{exportingView?'Pripravujem PNG…':'Aktuálny 2D pohľad PNG'}</button>{viewExportError&&<p className="pd-export-error">{viewExportError}</p>}<button onClick={exportCsv}><FileSpreadsheet size={16}/>Kompletný súpis CSV</button><Link href="/archiv"><Layers3 size={16}/>Archív dispozičných štúdií</Link></div></details>
        </div></div>
        <div className={`pd-canvas pd-tool-${tool}`} ref={canvas}>
          <svg ref={svg} className="pd-plan" viewBox={`${view.x} ${view.y} ${view.width} ${view.height}`} tabIndex={0} aria-label="Pôdorys. Ťahaním posúvajte, kolieskom približujte. Prvok vyberiete kliknutím alebo zo zoznamu." onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerCancel={onPointerUp} onClick={onPlanClick} onDoubleClick={()=>{if(tool!=='measure')fit(component?.rect??selected?.rect??room?.bounds??PLAN_FULL_BOUNDS);}} onKeyDown={event=>{
            if(event.key==='Escape'){setSelectedId(null);setComponentId(null);setMeasurement([]);setTool('select');}
            if(event.key==='+'||event.key==='='){event.preventDefault();zoomBy(.8);}if(event.key==='-'){event.preventDefault();zoomBy(1.25);}
            if(event.key==='0'){event.preventDefault();fit(planBounds,0);}
            if(event.key.toLowerCase()==='v')changeTool('select');if(event.key.toLowerCase()==='h')changeTool('pan');if(event.key.toLowerCase()==='m')changeTool('measure');
            if(event.key.startsWith('Arrow')){event.preventDefault();setView(v=>({...v,x:v.x+(event.key==='ArrowRight'?1:event.key==='ArrowLeft'?-1:0)*v.width*.08,y:v.y+(event.key==='ArrowDown'?1:event.key==='ArrowUp'?-1:0)*v.height*.08}));}
          }}>
            {siteVisible&&<ParcelGeometry dimensions={dimensions}/>}
            <PlanGeometry layers={layers} details={details||zoom>250} overhead={overhead} selectedId={selectedId} componentId={componentId} roomId={roomId} labels={zoom<600&&!(roomId==='ROOM-1-07'&&clearances)} dimensions={dimensions} unit={unit} unitsPerPixel={view.width/canvasWidth} livingLayout={livingLayout} heatingLayout={heatingLayout}/>
            {roomId==='ROOM-1-07'&&clearances&&<TechnicalClearances heatingLayout={heatingLayout}/>}
            {selected&&<g pointerEvents="none"><Box r={component?.rect??selected.nominal??selected.rect} fill="none" stroke="#2763d5" strokeWidth="1.5" vectorEffect="non-scaling-stroke" strokeDasharray="5 3"/><PlanDimensions rect={component?.rect??selected.nominal??selected.rect} unit={unit} size={view.width/canvasWidth*12}/></g>}
            {measurement[0]&&<g pointerEvents="none" className="pd-measure-line"><circle cx={measurement[0].x} cy={measurement[0].y} r={view.width/canvasWidth*4}/>{measureEnd&&<><path d={`M${measurement[0].x},${measurement[0].y}L${measureEnd.x},${measureEnd.y}`} vectorEffect="non-scaling-stroke"/><circle cx={measureEnd.x} cy={measureEnd.y} r={view.width/canvasWidth*4}/></>}</g>}
          </svg>
          <div className="pd-canvas-tools" role="toolbar" aria-label="Nástroje pôdorysu">{([['select','Vybrať prvok (V)',MousePointer2],['pan','Posúvať plátno (H)',Hand],['measure','Zmerať vzdialenosť (M)',Ruler]] as const).map(([id,label,Icon])=><button key={id} title={label} aria-label={label} aria-pressed={tool===id} onClick={()=>changeTool(id)}><Icon size={19}/></button>)}<i/><button title="Zobraziť celý dom (0)" aria-label="Zobraziť celý dom" onClick={()=>{fit(planBounds,0);setRoomId('');}}><Maximize2 size={19}/></button><button title="Pomoc s ovládaním" aria-label="Pomoc s ovládaním" onClick={()=>help.current?.showModal()}><CircleHelp size={19}/></button></div>
          <div className="pd-zoom"><button aria-label="Oddialiť" onClick={()=>zoomBy(1.25)}><Minus size={16}/></button><button title="Prispôsobiť celý dom" onClick={()=>fit(planBounds,0)}>{zoom}%</button><button aria-label="Priblížiť" onClick={()=>zoomBy(.8)}><Plus size={16}/></button></div>
          {tool==='measure'?<div className="pd-measure-card"><Ruler size={17}/><div><strong>{measureDistance!==null?formatMm(measureDistance,unit):'Klikni na prvý bod'}</strong><span>{measurement.length===2?'Vzdialenosť medzi zvolenými bodmi':measurement.length===1?'Klikni na druhý bod':'Potom označ druhý koniec vzdialenosti'}</span>{measurement.length===2&&<small>↔ {formatMm(Math.abs(measurement[1].x-measurement[0].x),unit)} &nbsp; ↕ {formatMm(Math.abs(measurement[1].y-measurement[0].y),unit)}</small>}</div><button aria-label="Vymazať meranie" onClick={()=>{setMeasurement([]);setHoverPoint(null);}}><X size={16}/></button></div>:<div className="pd-canvas-hint"><Hand size={13}/>Ťahaním posúvaj · kolieskom približuj · kliknutím vyber</div>}
          <div className="pd-scale"><span style={{width:scaleMm/view.width*canvasWidth}}/><small>{formatMm(scaleMm,'m')}</small></div>
        </div>
        <footer className="pd-drawing-footer"><span><span className="pd-live-dot"/>{`${archive?'Archív':'Hlavný návrh'} · C / ${heatingLayout} / ${livingLayout}`}</span><label>Jednotky <select aria-label="Jednotky rozmerov" value={unit} onChange={e=>setUnit(e.target.value as Units)}><option value="mm">mm</option><option value="cm">cm</option><option value="m">m</option></select></label></footer>
      </section>
      <aside id="pd-inspector" className="pd-inspector" aria-label="Výber a informácie o návrhu">
        <div className="pd-inspector-tabs" role="tablist" aria-label="Obsah pravého panela">
          {INSPECTOR_TABS.map(([id,label,Icon],index)=><button key={id} id={`pd-inspector-tab-${id}`} type="button" role="tab" aria-selected={inspectorTab===id} aria-controls={`pd-inspector-panel-${id}`} tabIndex={inspectorTab===id?0:-1} onClick={()=>setInspectorTab(id)} onKeyDown={event=>{
            const next=event.key==='Home'?0:event.key==='End'?1:event.key==='ArrowLeft'||event.key==='ArrowRight'?1-index:null;
            if(next===null)return;
            event.preventDefault();const nextId=INSPECTOR_TABS[next][0];setInspectorTab(nextId);document.getElementById(`pd-inspector-tab-${nextId}`)?.focus();
          }}><Icon size={17} aria-hidden="true"/>{label}</button>)}
        </div>
        <div ref={selectionPanel} id="pd-inspector-panel-selection" className="pd-inspector-content" role="tabpanel" aria-labelledby="pd-inspector-tab-selection" tabIndex={0} hidden={inspectorTab!=='selection'}>
        {selected?<><div className="pd-inspector-heading"><span className="pd-overline">{PLAN_CATEGORIES[selected.category]}</span><button aria-label="Zavrieť detail" onClick={()=>{setSelectedId(null);setComponentId(null);setMobilePanel('plan');requestAnimationFrame(()=>svg.current?.focus({preventScroll:true}));}}><X size={18}/></button></div><h2 ref={inspectorTitle} tabIndex={-1}>{selected.name}</h2><p className="pd-item-room">{selectedRoom?`${selectedRoom.number} · ${selectedRoom.name}`:'Terasy pri dome'}{selected.layout&&` · obývačka vo variante ${selected.layout}`}</p>
          {ACOUSTIC_WALL_SPECS.some(w=>w.mark===selected.id)?<AcousticWallDetail mark={selected.id}/>:<div className="pd-item-preview"><ItemMiniature item={selected} componentId={componentId}/><span>POHĽAD ZHORA</span></div>}
          <button className="pd-focus-item" onClick={()=>{fit(component?.rect??selected.rect,700);setMobilePanel('plan');}}><Focus size={17}/>Zobraziť v pláne<ArrowUpRight size={15}/></button>
          {component?<div className="pd-selected-component"><button onClick={()=>setComponentId(null)}><ArrowLeft size={14}/>Celý prvok</button><strong>{component.name.split(' · ').slice(-1)[0]}</strong><span>Rozmery konkrétnej súčasti modelu</span></div>:null}
          <h3>{component?'Rozmery súčasti':selected.opening?'Stavebný otvor':selected.nominal?'Rozmery podľa zadania modelu':'Celkový rozmer modelu'}</h3>
          {selected.opening&&!component?<dl className="pd-dimension-grid"><div><dt>Šírka otvoru</dt><dd>{formatMm(selected.opening.width,unit)}</dd></div><div><dt>Výška otvoru</dt><dd>{formatMm(selected.opening.height,unit)}</dd></div><div><dt>Parapet od podlahy</dt><dd>{formatMm(selected.opening.sill,unit)}</dd></div></dl>:<Dimensions rect={component?.rect??selected.nominal??selected.rect} height={component?component.z1-component.z0:selected.z1-selected.z0} unit={unit}/>}
          <p className="pd-dimension-note">↔ vodorovne, ↕ zvislo v pôdoryse. Výška je zvislý rozmer prvku; osadenie od podlahy je uvedené nižšie.</p>
          {selected.product&&!component&&<div className="pd-product-spec"><span>{selected.product.label}</span><strong>{selected.product.dimensions}</strong><a href={selected.product.source} target="_blank" rel="noreferrer">Technický list výrobcu ↗</a></div>}{selected.opening?.clearWidth&&!component&&<p className="pd-object-note"><strong>Čistý priechod {formatMm(selected.opening.clearWidth,unit)}</strong></p>}{selected.note&&!component&&<p className="pd-object-note">{selected.note}</p>}
          <details className="pd-precise" open={!!component}><summary>Presná poloha a priestorový rozsah<ChevronDown size={14}/></summary><dl><div><dt>Spodná hrana</dt><dd>{formatMm(component?.z0??selected.z0,unit)}</dd></div><div><dt>Horná hrana</dt><dd>{formatMm(component?.z1??selected.z1,unit)}</dd></div><div><dt>Rozsah ↔</dt><dd>{formatMm((component?.rect??selected.rect).x1-(component?.rect??selected.rect).x0,unit)}</dd></div><div><dt>Rozsah ↕</dt><dd>{formatMm((component?.rect??selected.rect).y1-(component?.rect??selected.rect).y0,unit)}</dd></div></dl><p>Rozsah zahŕňa všetky diely a presahy. Pri natočených alebo oblých prvkoch ide o najmenší obdĺžnik okolo modelu. Zobrazenie je zaokrúhlené na 1 mm.</p></details>
          <div className="pd-parts-heading"><h3>Súčasti prvku</h3><span>{selected.meshes.length}</span></div><p className="pd-dimension-note">Aj drobné alebo prekryté diely vyberieš tu.</p>
          {selected.meshes.length>12&&<input className="pd-parts-search" aria-label="Hľadať súčasť vybraného prvku" placeholder="Nájsť súčasť…" value={partsQuery} onChange={e=>setPartsQuery(e.target.value)}/>}
          <div className="pd-parts-list">{selected.meshes.filter(m=>!partsQuery||m.name.toLocaleLowerCase('sk').includes(partsQuery.toLocaleLowerCase('sk'))).map((mesh,i)=><button key={mesh.id} aria-pressed={componentId===mesh.id} onClick={()=>{setComponentId(mesh.id);setAnnouncement(`Vybraná súčasť: ${mesh.name}`);}}><span>{String(i+1).padStart(2,'0')}</span><span>{mesh.name.split(' · ').slice(-1)[0]}<small>{formatMm(mesh.rect.x1-mesh.rect.x0,unit)} × {formatMm(mesh.rect.y1-mesh.rect.y0,unit)}</small></span><ChevronRight size={13}/></button>)}</div>
        </>:room?<>
          <div className="pd-inspector-heading"><span className="pd-overline">MIESTNOSŤ {room.number}</span><button aria-label="Zrušiť výber miestnosti" onClick={()=>chooseRoom('')}><X size={18}/></button></div>
          <h2 ref={inspectorTitle} tabIndex={-1}>{room.name}</h2>
          <div className="pd-summary-metric"><span>Čistá plocha miestnosti</span><strong>{numberSk(room.area,2)}<small>m²</small></strong><span>{`Výška ${formatMm(room.clearHeightMm,'m')}${room.ceiling==='VAULTED_TO_RIDGE'?' · šikmý strop':''}`}</span></div>
          <button className="pd-focus-item" onClick={()=>openLibrary('objects')}>Prvky v tejto miestnosti<ChevronRight size={16}/></button>
          <h3>Rozsah miestnosti</h3><Dimensions rect={room.bounds} height={room.clearHeightMm} unit={unit}/><p className="pd-dimension-note">Pri členitej miestnosti ide o celkový obal. Jednotlivé obdĺžnikové časti sú rozpísané v manuáli.</p>
          <RoomGuidance roomId={room.id} livingLayout={livingLayout} heatingLayout={heatingLayout}/>
          {room.id==='ROOM-1-07'&&clearances&&<TechnicalLegend heatingLayout={heatingLayout}/>}
          {ACOUSTIC_WALL_SPECS.some(w=>w.rooms.some(id=>id===room.id))&&<section className="pd-acoustic-index"><h3>Akustické steny v miestnosti</h3>{ACOUSTIC_WALL_SPECS.filter(w=>w.rooms.some(id=>id===room.id)).map(w=><button key={w.mark} onClick={()=>{const item=PLAN_ITEM_BY_ID.get(w.mark);if(item)choose(item,null,true);}}><strong>{w.mark}</strong><span>{w.location}</span><ChevronRight size={14}/></button>)}</section>}
        </>:<div className="pd-selection-empty">
          <div className="pd-selection-icon"><MousePointer2 size={25} strokeWidth={1.5} aria-hidden="true"/></div>
          <span className="pd-overline">DETAIL VÝBERU</span>
          <h2 ref={inspectorTitle} tabIndex={-1}>Vyber si prvok<br/>v pôdoryse.</h2>
          <p>Klikni na miestnosť, nábytok alebo stenu. Tu nájdeš ich rozmery a súčasti.</p>
          <button className="pd-focus-item" onClick={()=>openLibrary('rooms')}><List size={17}/>Prejsť miestnosti<ChevronRight size={16}/></button>
          <button className="pd-selection-help" onClick={()=>help.current?.showModal()}><CircleHelp size={16}/>Ovládanie pôdorysu</button>
        </div>}
        </div>
        <div id="pd-inspector-panel-design" className="pd-inspector-content pd-design-content" role="tabpanel" aria-labelledby="pd-inspector-tab-design" tabIndex={0} hidden={inspectorTab!=='design'}>
          <span className="pd-overline">{archive?'ARCHÍVNA ZOSTAVA':'HLAVNÝ NÁVRH'}</span><h2>C / {heatingLayout} / {livingLayout}</h2><p className="pd-design-caption">Dispozícia · technická miestnosť · obývacia zóna</p>
          <div className="pd-summary-metric"><span>Čistá plocha prízemia</span><strong>{numberSk(PLAN_ROOMS.reduce((sum,r)=>sum+r.area,0),2)}<small>m²</small></strong><span>13 miestností vrátane garáže</span></div>
          {siteVisible&&<details className="pd-design-section"><summary><span>Osadenie domu<small>Parcela 6012/26 · 753 m²</small></span><ChevronDown size={17}/></summary><section className="pd-parcel-info"><p>Hranica z katastra ČÚZK. Situácia C3 s upraveným osadením: uličný aj pravý odstup 3,00 m.</p><dl>{HOUSE_SETBACKS.map(s=><div key={s.side}><dt>{s.side}</dt><dd>{formatMm(s.distance,'m')}</dd></div>)}</dl><small>Kolmé vzdialenosti od obrysu domu k hlavným hranám parcely. Zaoblený roh ulice je zachovaný. Nejde o geodetické zameranie stavby.</small></section></details>}
          <details className="pd-design-section"><summary><span>Technická miestnosť<small>{heatingLayout} · {HEATING_LAYOUTS[heatingLayout].label}</small></span><ChevronDown size={17}/></summary><HeatingLayoutSwitch value={heatingLayout} onChange={chooseHeatingLayout} allowChanges={archive}/></details>
          <details className="pd-design-section"><summary><span>Obývacia zóna<small>{livingLayout} · {LIVING_LAYOUTS[livingLayout].label}</small></span><ChevronDown size={17}/></summary><LivingLayoutSwitch value={livingLayout} onChange={chooseLivingLayout} allowChanges={archive}/></details>
          <details className="pd-design-section"><summary><span>Akustické steny<small>SM30 · tehla 300 mm / H200 · 187,5 mm</small></span><ChevronDown size={17}/></summary><section className="pd-acoustic-index"><p>AK-01 a AK-02: jedna vrstva klasickej obvodovej tehly 300 mm. Účel odhlučnenia zostáva; bežné povrchy sú navyše. AK-03: LeierPLAN 10 a predstena s jednou Silentboard, spolu 187,5 mm vrátane omietok.</p>{ACOUSTIC_WALL_SPECS.map(w=><button key={w.mark} onClick={()=>{const item=PLAN_ITEM_BY_ID.get(w.mark);if(item)choose(item,null,true);}}><strong>{w.mark}</strong><span>{w.location}</span><ChevronRight size={14}/></button>)}</section></details>
          <button className="pd-design-help" onClick={()=>help.current?.showModal()}><Ruler size={17}/><span>Ako čítať rozmery</span><ChevronRight size={16}/></button>
          <div className="pd-inspector-bottom"><span>{numberSk(items.length)} prvkov</span><span>{numberSk(allParts)} súčastí</span></div>
        </div>
      </aside>
    </div>
    <ExportPlan livingLayout={livingLayout} heatingLayout={heatingLayout}/>
    <div ref={exportHost} hidden aria-hidden="true">{exportJob&&<ExportSheet level={exportJob.level} color={exportJob.color} livingLayout={exportJob.livingLayout} heatingLayout={exportJob.heatingLayout}/>}</div>
    {manualOpen&&<DocumentationManual archive={archive} printParts={printParts} setPrintParts={setPrintParts} livingLayout={livingLayout} heatingLayout={heatingLayout}/>}
    <dialog className="pd-help" ref={help} aria-labelledby="pd-help-title"><form method="dialog"><button aria-label="Zavrieť pomoc"><X size={20}/></button></form><span className="pd-overline">RÝCHLY SPRIEVODCA</span><h2 id="pd-help-title">Dom pod kontrolou.</h2><p>Začni výberom miestnosti. Nábytok a steny môžeš vybrať priamo v pláne alebo v zozname prvkov.</p><dl><dt>Posun plánu</dt><dd>Ťahanie myšou alebo jedným prstom. Na klávesnici šípky.</dd><dt>Priblíženie</dt><dd>Koliesko, dva prsty alebo + / −. Kláves 0 zobrazí celý dom.</dd><dt>Detail</dt><dd>Klikni na predmet. Drobný diel vyber v zozname „Súčasti prvku“.</dd><dt>Meranie</dt><dd>Nástroj pravítko (M), potom dva body. Presnosť závisí od miesta kliknutia.</dd><dt>Ukončiť výber</dt><dd>Escape zruší výber aj meranie. V = výber, H = posun.</dd></dl><h3>Čo znamenajú rozmery</h3><p>↔ a ↕ sú vodorovný a zvislý smer plánu. Výška je tretí rozmer. „Rozmery podľa zadania“ pochádzajú zo špecifikácie nábytku; „priestorový rozsah“ zahŕňa všetky jeho diely a presahy. Najmenšie súčasti sú dostupné aj vtedy, keď nie sú pri oddialení viditeľné.</p><p>Manuál dokumentuje geometriu modelu. Pre výrobu nábytku a realizáciu treba rozmery overiť na stavbe.</p></dialog>
    <div className="sr-only" aria-live="polite" aria-atomic="true">{announcement}</div>
  </main>;
}

const ExportPlan=memo(function ExportPlan({livingLayout,heatingLayout}:{livingLayout:LivingLayoutId;heatingLayout:HeatingLayoutId}){return <div id="pd-export-source" hidden><StaticPlan viewBox={fitPlanRect(PLAN_FULL_BOUNDS,1.2,0)} livingLayout={livingLayout} heatingLayout={heatingLayout}/></div>;});

function HeatingLayoutSwitch({value,onChange,allowChanges}:{value:HeatingLayoutId;onChange:(next:HeatingLayoutId)=>void;allowChanges:boolean}){
  const h=HEATING_LAYOUTS[value],t=h.accumulator,b=h.boiler;
  return <div className="pd-living-switch pd-heating-switch" data-testid={allowChanges?'pd-heating-switch':'pd-heating-summary'}>
    <span className="pd-overline">TECHNICKÁ 1.07 · VEĽKOSŤ ZOSTAVY</span>
    {allowChanges?<div role="group" aria-label="Variant technickej miestnosti">{HEATING_LAYOUT_IDS.map(id=><button key={id} type="button" aria-pressed={value===id} onClick={()=>onChange(id)}><b>{id}</b><span>{HEATING_LAYOUTS[id].label}<small>{id==='A'?'Archívna zostava':'Zostava B'}</small></span></button>)}</div>:<strong>B · {h.label}</strong>}
    <p>{h.summary}</p>
    <dl className="pd-heating-specs"><div><dt>Nádrž s izoláciou</dt><dd>Ø{numberSk(t.outerDiameterMm)} × {numberSk(t.heightMm)} mm</dd></div><div><dt>Bez izolácie</dt><dd>Ø{t.transportDiameterWithoutInsulationMm} mm</dd></div><div><dt>Kotol + násypka · š × h × v</dt><dd>{numberSk(b.catalogueSizeMm.width)} × {numberSk(b.catalogueSizeMm.depth)} × 1 391 mm</dd></div></dl>
    {value==='B'&&<small>Užšia nádrž o 14,8 cm, vyššia o 19,3 cm. Konečný výkon potvrdí výpočet tepelnej straty.</small>}
  </div>;
}

/** Right-panel switch between the documented arrangements of the living zone 1.03. */
function LivingLayoutSwitch({value,onChange,allowChanges}:{value:LivingLayoutId;onChange:(next:LivingLayoutId)=>void;allowChanges:boolean}){
  const layout=LIVING_LAYOUTS[value];
  return <div className="pd-living-switch" data-testid={allowChanges?'pd-living-switch':'pd-living-summary'}><span className="pd-overline">OBÝVAČKA 1.03 · VARIANT ROZLOŽENIA</span>
    {allowChanges?<div role="group" aria-label="Variant obývacej zóny">{LIVING_LAYOUT_IDS.map(id=><button key={id} type="button" aria-pressed={value===id} onClick={()=>onChange(id)}><b>{id}</b><span>{LIVING_LAYOUTS[id].label}</span></button>)}</div>:<strong>B · {layout.label}</strong>}
    <p>{layout.summary}</p>
    <small>Rovnaké rozloženie je dostupné aj v aktuálnom 3D náhľade.</small>
  </div>;
}

function RoomGuidance({roomId,livingLayout,heatingLayout}:{roomId:string;livingLayout:LivingLayoutId;heatingLayout:HeatingLayoutId}){
  const notes=planRoomNotes(roomId,livingLayout,heatingLayout);
  if(!notes)return null;
  return <div className="pd-room-guidance"><h3>Prečo je to takto</h3>{notes.map(note=><p key={note}>{note}</p>)}{roomId==='ROOM-1-07'&&<div className="pd-source-links"><a href={HEATING_SOURCES.boiler} target="_blank" rel="noreferrer">Kotol ↗</a><a href={HEATING_SOURCES.accumulator} target="_blank" rel="noreferrer">Nádrž ↗</a><a href={HEATING_SOURCES.manual} target="_blank" rel="noreferrer">Návod PLUS · s. 13, 16 ↗</a></div>}</div>;
}

const DocumentationManual=memo(function DocumentationManual({archive,printParts,setPrintParts,livingLayout,heatingLayout}:{archive:boolean;printParts:boolean;setPrintParts:(value:boolean)=>void;livingLayout:LivingLayoutId;heatingLayout:HeatingLayoutId}) {
  const items=planItemsFor(livingLayout,heatingLayout),allParts=partsCount(items),living=LIVING_LAYOUTS[livingLayout];
  return <div className="pd-print" aria-label="Manuál domu"><div className="pd-manual-toolbar"><Link href={designHref('/podorys',{livingLayout,heatingLayout},archive)}><ArrowLeft size={17}/>Späť na pôdorys</Link><label><input type="checkbox" checked={printParts} onChange={e=>setPrintParts(e.target.checked)}/>Priložiť všetkých {numberSk(allParts)} súčastí</label><button className="pd-primary" onClick={()=>window.print()}><Printer size={17}/>Tlačiť / uložiť PDF</button></div>
      <section className="pd-paper pd-cover"><span className="pd-overline">{`${archive?'ARCHÍVNA ZOSTAVA':'HLAVNÝ NÁVRH'} · C / ${heatingLayout} / ${livingLayout} · PRÍZEMIE`}</span><h2>Manuál vášho domu.</h2><p>{`Variant C · pôdorys a súpis aktuálneho 3D modelu · obývačka 1.03 vo variante ${living.id}: ${living.label} · technická ${heatingLayout}: ${HEATING_LAYOUTS[heatingLayout].label}`}</p><div id="pd-print-overview"><StaticPlan viewBox={fitPlanRect(PLAN_FULL_BOUNDS,1.2,0)} livingLayout={livingLayout} heatingLayout={heatingLayout}/></div><div className="pd-cover-metrics"><span>{PLAN_ROOMS.length} miestností</span><span>{items.length} prvkov</span><span>{numberSk(allParts)} súčastí</span></div><h3>Ako čítať tento manuál</h3><p>Všetky tabuľkové rozmery sú v milimetroch. X (↔) a Y (↕) sú rozmery v pôdoryse, výška smeruje nahor. Rozsah modelu zahŕňa presahy a všetky súčasti. Pri oblých a natočených prvkoch uvádzame obdĺžnik, ktorý ich obopína. Kóty majú prednosť pred meraním na vytlačenej stránke.</p><p>Dokumentácia pokrýva prízemie: interiér, obvodové steny, výplne a kryté priestory a vonkajšie sedenie pri dome. Podklady zachytávajú model, nie zameranie stavby ani výrobný výkres. Záhrada, podzemné rozvody a strešný plášť nie sú obsahom týchto listov.</p><p>Pri voľnom meraní v aplikácii záleží na presnosti vybraných bodov. Presné rozmery jednotlivých prvkov nájdeš v ich detaile a súpise.</p></section>
      <section className="pd-paper pd-acoustic-sheet pd-sm30-sheet"><div className="pd-paper-heading"><div><span className="pd-overline">DETAIL SM30 · 16. 9. 2026</span><h2>Steny s požiadavkou odhlučnenia</h2></div><strong>Murivo 300 mm</strong></div><div className="pd-acoustic-sheet-grid"><div><StaticPlan viewBox={{x:12800,y:-11200,width:4200,height:8500}} labels={false} livingLayout={livingLayout} heatingLayout={heatingLayout}/></div><AcousticWallDetail/></div><table><thead><tr><th>Označenie</th><th>Umiestnenie</th><th>Konštrukčná skladba</th></tr></thead><tbody>{ACOUSTIC_WALL_SPECS.filter(w=>w.assembly.code==='SM30').map(w=><tr key={w.mark}><td>{w.mark}</td><td>{w.location}</td><td>SM30 · klasická obvodová tehla 300 mm</td></tr>)}</tbody></table><p>{ACOUSTIC_ASSEMBLY.structuralNote}</p><p>{ACOUSTIC_ASSEMBLY.acousticNote}</p><p>{ACOUSTIC_ASSEMBLY.bathroomNote}</p><footer>DOM · C/B/B · Rozmery v mm · Murivo 300 mm; omietky a kúpeľňové povrchy navyše.</footer></section>
      <section className="pd-paper pd-acoustic-sheet pd-office-acoustic-sheet"><div className="pd-paper-heading"><div><span className="pd-overline">DETAIL AK-03 · H200</span><h2>Pracovňa a sprcha</h2></div><strong>187,5 mm · Rw ≈ 56 dB*</strong></div><div className="pd-acoustic-sheet-grid"><div><StaticPlan viewBox={{x:21100,y:-9100,width:7000,height:6000}} labels={false} livingLayout={livingLayout} heatingLayout={heatingLayout}/><p>Stavebný otvor kúpeľne 800 mm a krídlo 700 mm sú súmerné podľa pozdĺžnej osi X chodby. Os Y = 7 101,5 mm; chodba má 1 099 mm.</p><table><thead><tr><th>Kontrolná kóta</th><th>mm</th></tr></thead><tbody><tr><td>Južné ostenie otvoru kúpeľne · Y</td><td>6 701,5</td></tr><tr><td>Severné ostenie otvoru kúpeľne · Y</td><td>7 501,5</td></tr><tr><td>Ostenie pri pracovni / pri kúpeľni</td><td>42,5 / 149,5</td></tr><tr><td>Posun dverí a vstupného rohu pracovne k ulici</td><td>30</td></tr></tbody></table></div><AcousticWallDetail mark="AK-03"/></div><p>{OFFICE_ACOUSTIC_ASSEMBLY.acousticNote}</p><p>{OFFICE_ACOUSTIC_ASSEMBLY.structuralNote}</p><p>{OFFICE_ACOUSTIC_ASSEMBLY.bathroomNote}</p><footer>DOM · C/B/B · Rozmery v mm · 187,5 mm vrátane omietok a jednej dosky, bez finálnych povrchov · * Predbežný výpočet Rw, presnú zostavu potvrdiť.</footer></section>
      {PLAN_ROOMS.map(r=><section className="pd-paper pd-room-sheet" key={r.id}><div className="pd-paper-heading"><div><span className="pd-overline">LIST {r.number}</span><h2>{r.name}</h2></div><strong>{numberSk(r.area,2)} m²</strong></div><div className="pd-room-sheet-plan"><StaticPlan viewBox={fitPlanRect(r.bounds,1.6,800)} roomId={r.id} livingLayout={livingLayout} heatingLayout={heatingLayout}/></div><div className="pd-room-specs"><span>Svetlá výška: {formatMm(r.clearHeightMm)}{r.ceiling==='VAULTED_TO_RIDGE'?' pri stene · šikmý strop do 4 850 mm':''}</span><span>Podlaha: {r.floor==='VINYL'?'vinyl':r.floor==='TILE'?'dlažba':'epoxid'}</span>{r.id==='ROOM-1-03'&&<span>Obývacia zóna: variant {living.id} · {living.label}</span>}</div><RoomGuidance roomId={r.id} livingLayout={livingLayout} heatingLayout={heatingLayout}/>{r.id==='ROOM-1-07'&&<TechnicalLegend heatingLayout={heatingLayout}/>}<p>Časti čistej podlahy: {r.rectsMm.map(p=>`${numberSk(p.x1-p.x0)} × ${numberSk(p.y1-p.y0)}`).join(' + ')} mm. Plocha je súčtom týchto častí.</p><table><thead><tr><th>Prvok</th><th>X ↔</th><th>Y ↕</th><th>Výška</th><th>Diely</th></tr></thead><tbody>{items.filter(item=>item.roomId===r.id).map(item=><tr key={item.id}><td>{item.name}{item.product&&<small>{item.product.dimensions} · katalóg</small>}{item.nominal&&<small>Rozmer podľa zadania modelu</small>}{item.opening&&<small>Rozmery otvoru: {numberSk(item.opening.width)} × {numberSk(item.opening.height)} mm</small>}</td><td>{numberSk((item.nominal??item.rect).x1-(item.nominal??item.rect).x0)}</td><td>{numberSk((item.nominal??item.rect).y1-(item.nominal??item.rect).y0)}</td><td>{numberSk(item.z1-item.z0)}</td><td>{item.meshes.length}</td></tr>)}</tbody></table><footer>DOM · C · Rozmery v mm · Rozsah celku vrátane presahov, ak nie je uvedené inak.</footer></section>)}
      <section className="pd-paper"><span className="pd-overline">VONKAJŠIE SEDENIE</span><h2>Terasy pri dome</h2><p>Nábytok z aktuálneho 3D modelu. Rozmery v mm.</p><table><thead><tr><th>Prvok</th><th>X ↔</th><th>Y ↕</th><th>Výška</th></tr></thead><tbody>{items.filter(item=>item.roomId==='EXTERIOR').map(item=><tr key={item.id}><td>{item.name}</td><td>{numberSk(item.rect.x1-item.rect.x0)}</td><td>{numberSk(item.rect.y1-item.rect.y0)}</td><td>{numberSk(item.z1-item.z0)}</td></tr>)}</tbody></table></section>
      {printParts&&<section className="pd-paper pd-appendix"><h2>Kompletný rozpis súčastí</h2><p>Každá viditeľná fyzická súčasť exportovaných zostáv. Rozmery sú v mm.</p>{items.map(item=><div key={item.id}><h3>{PLAN_ROOMS.find(r=>r.id===item.roomId)?.number} · {item.name}</h3><table><thead><tr><th>Súčasť</th><th>X ↔</th><th>Y ↕</th><th>Výška</th><th>Od podlahy</th></tr></thead><tbody>{item.meshes.map(mesh=><tr key={mesh.id}><td>{mesh.name.split(' · ').slice(-1)[0]}</td><td>{numberSk(mesh.rect.x1-mesh.rect.x0)}</td><td>{numberSk(mesh.rect.y1-mesh.rect.y0)}</td><td>{numberSk(mesh.z1-mesh.z0)}</td><td>{numberSk(mesh.z0)}</td></tr>)}</tbody></table></div>)}</section>}
    </div>;
});
