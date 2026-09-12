'use client';

import { memo, useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from 'react';
import { flushSync } from 'react-dom';
import Link from 'next/link';
import { ArrowDownToLine, ArrowLeft, ArrowUpRight, BookOpen, Box as BoxIcon, Check, ChevronDown, ChevronRight, CircleHelp, Contrast, FileSpreadsheet, Focus, Hand, ImageDown, Layers3, List, Maximize2, Minus, MousePointer2, Palette, Plus, Printer, Ruler, Search, X } from 'lucide-react';
import { PLAN_CATEGORIES, PLAN_FULL_BOUNDS, PLAN_ITEM_BY_ID, PLAN_MESH_BY_ID, PLAN_ROOMS, fitPlanRect, formatMm, numberSk, planItemsFor, planRoomNotes, rectSize, searchPlanItems, zoomPlanAt, type PlanCategory, type PlanItem } from '@/lib/plan-documentation';
import { EXPORT_LEVELS, type ExportLevel } from '@/lib/plan-export';
import { DEFAULT_LIVING_LAYOUT_ID, LIVING_LAYOUTS, LIVING_LAYOUT_IDS, type LivingLayoutId } from '@/lib/twin-living-layouts';
import type { RectMm } from '@/lib/twin-interior';
import { HEATING_SOURCES } from '@/lib/technical-design';
import { Box } from './plan-svg';
import { ItemMiniature, PlanDimensions, PlanGeometry, ROOM_COLORS, StaticPlan, TechnicalClearances, TechnicalLegend } from './documentation-plan';
import { ExportSheet, PX_PER_MM, SHEET } from './export-sheet';
import './documentation.css';

type Point={x:number;y:number};
type Units='mm'|'cm'|'m';
const INITIAL_LAYERS={furniture:true,equipment:true,lighting:false,walls:true,openings:true,finishes:true};
const defaultView=fitPlanRect(PLAN_FULL_BOUNDS,1.25,0);
const partsCount=(items:readonly PlanItem[])=>items.reduce((sum,item)=>sum+item.meshes.length,0);
/** File-name suffix so exports of the alternative living-room layout do not overwrite the default ones. */
const layoutFileSuffix=(layout:LivingLayoutId)=>layout===DEFAULT_LIVING_LAYOUT_ID?'':`-obyvacka-${layout.toLowerCase()}`;
function download(name:string,content:string|Blob,type:string){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
interface ExportJob { level:ExportLevel; color:boolean; livingLayout:LivingLayoutId }
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

export function DocumentationStudio({initialManual=false,initialLivingLayout=DEFAULT_LIVING_LAYOUT_ID}:{initialManual?:boolean;initialLivingLayout?:LivingLayoutId}) {
  const svg=useRef<SVGSVGElement>(null),canvas=useRef<HTMLDivElement>(null),help=useRef<HTMLDialogElement>(null),inspectorTitle=useRef<HTMLHeadingElement>(null);
  const [view,setView]=useState(defaultView),[selectedId,setSelectedId]=useState<string|null>(null),[componentId,setComponentId]=useState<string|null>(null);
  const [livingLayout,setLivingLayout]=useState<LivingLayoutId>(initialLivingLayout);
  const items=useMemo(()=>planItemsFor(livingLayout),[livingLayout]);
  const allParts=useMemo(()=>partsCount(items),[items]);
  const [roomId,setRoomId]=useState(''),[query,setQuery]=useState(''),[category,setCategory]=useState<PlanCategory|'all'>('all');
  const [layers,setLayers]=useState(INITIAL_LAYERS),[details,setDetails]=useState(false),[overhead,setOverhead]=useState(false),[dimensions,setDimensions]=useState(true),[clearances,setClearances]=useState(true),[unit,setUnit]=useState<Units>('cm');
  const [tool,setTool]=useState<'select'|'pan'|'measure'>('select'),[measurement,setMeasurement]=useState<Point[]>([]),[hoverPoint,setHoverPoint]=useState<Point|null>(null);
  const [leftTab,setLeftTab]=useState<'rooms'|'objects'>('rooms'),[mobilePanel,setMobilePanel]=useState<'rooms'|'plan'|'detail'>('plan');
  const [manualOpen,setManualOpen]=useState(initialManual),[printParts,setPrintParts]=useState(false),[announcement,setAnnouncement]=useState('');
  const [canvasWidth,setCanvasWidth]=useState(800),[partsQuery,setPartsQuery]=useState('');
  const [exportJob,setExportJob]=useState<ExportJob|null>(null),[exportColor,setExportColor]=useState(true);
  const exportHost=useRef<HTMLDivElement>(null);
  const aspectRef=useRef(1.25);
  const viewRef=useRef(view);const pointers=useRef(new Map<number,Point>());const moved=useRef(false);const suppressClick=useRef(false);
  const lastGesture=useRef<{point:Point;distance:number}|null>(null);const pointerOrigin=useRef<Point|null>(null);
  useEffect(()=>{viewRef.current=view;},[view]);
  useEffect(()=>{
    const preparePrint=()=>flushSync(()=>setManualOpen(true));
    window.addEventListener('beforeprint',preparePrint);
    return()=>window.removeEventListener('beforeprint',preparePrint);
  },[]);
  useEffect(()=>{
    const el=canvas.current;if(!el)return;
    let first=true;
    const observer=new ResizeObserver(entries=>{
      const {width,height}=entries[0].contentRect;if(!width||!height)return;
      setCanvasWidth(width);aspectRef.current=width/height;
      setView(current=>first?fitPlanRect(PLAN_FULL_BOUNDS,width/height,0):{...current,y:current.y+current.height/2-current.width/(width/height)/2,height:current.width/(width/height)});
      first=false;
    });observer.observe(el);return()=>observer.disconnect();
  },[]);
  useEffect(()=>{
    const el=svg.current;if(!el)return;
    const wheel=(event:WheelEvent)=>{event.preventDefault();const r=el.getBoundingClientRect();const v=viewRef.current;
      const anchor={x:v.x+(event.clientX-r.left)/r.width*v.width,y:v.y+(event.clientY-r.top)/r.height*v.height};
      setView(zoomPlanAt(v,Math.exp(Math.max(-100,Math.min(100,event.deltaY))*.003),anchor));};
    el.addEventListener('wheel',wheel,{passive:false});return()=>el.removeEventListener('wheel',wheel);
  },[]);
  useEffect(()=>{
    if(!selectedId)return;
    inspectorTitle.current?.parentElement?.scrollTo({top:0});
    if(window.matchMedia('(max-width: 800px)').matches)inspectorTitle.current?.focus({preventScroll:true});
  },[selectedId]);
  const selected=selectedId?PLAN_ITEM_BY_ID.get(selectedId):undefined;
  const component=componentId?PLAN_MESH_BY_ID.get(componentId)?.mesh:undefined;
  const room=PLAN_ROOMS.find(r=>r.id===roomId),selectedRoom=PLAN_ROOMS.find(r=>r.id===selected?.roomId);
  const results=useMemo(()=>searchPlanItems(query,roomId,category,livingLayout),[query,roomId,category,livingLayout]);
  const zoom=Math.round(fitPlanRect(PLAN_FULL_BOUNDS,view.width/view.height,0).width/view.width*100);
  const fit=(rect:RectMm=PLAN_FULL_BOUNDS,padding=700)=>{const r=canvas.current?.getBoundingClientRect();setView(fitPlanRect(rect,r&&r.height?r.width/r.height:aspectRef.current,padding));};
  const choose=(item:PlanItem,meshId:string|null=null,focus=false)=>{
    setSelectedId(item.id);setComponentId(meshId);setPartsQuery('');setMobilePanel('detail');
    setLayers(l=>({...l,[item.category]:true}));setAnnouncement(`${item.name}, ${PLAN_ROOMS.find(r=>r.id===item.roomId)?.name}. Detail a rozmery sú otvorené.`);
    if(focus)fit(meshId?PLAN_MESH_BY_ID.get(meshId)!.mesh.rect:item.rect,900);
  };
  const chooseRoom=(id:string)=>{setRoomId(id);setSelectedId(null);setComponentId(null);setQuery('');setMobilePanel('plan');const r=PLAN_ROOMS.find(room=>room.id===id);fit(r?.bounds??PLAN_FULL_BOUNDS,id?1100:0);};
  const chooseLivingLayout=(next:LivingLayoutId)=>{
    if(next===livingLayout)return;
    setLivingLayout(next);
    // A selected piece of the other arrangement would no longer be drawn.
    if(selected?.layout){setSelectedId(null);setComponentId(null);}
    const url=new URL(window.location.href);
    if(next===DEFAULT_LIVING_LAYOUT_ID)url.searchParams.delete('living');else url.searchParams.set('living',next.toLowerCase());
    window.history.replaceState(null,'',url);
    setAnnouncement(`Obývačka vo variante ${next}: ${LIVING_LAYOUTS[next].label}. Pôdorys, súpis aj exporty sú prepnuté.`);
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
    const pickedRoom=target?.getAttribute('data-room');if(pickedRoom){setRoomId(pickedRoom);setSelectedId(null);setComponentId(null);return;}
    setSelectedId(null);setComponentId(null);
  };
  const changeTool=(next:typeof tool)=>{setTool(next);if(next!=='measure'){setMeasurement([]);setHoverPoint(null);}};
  const zoomBy=(factor:number)=>setView(v=>zoomPlanAt(v,factor,{x:v.x+v.width/2,y:v.y+v.height/2}));
  const exportCsv=()=>{
    const rows=[['Miestnosť','Prvok','Súčasť','ID','X min (mm)','Y min (mm)','Rozmer X (mm)','Rozmer Y (mm)','Výška (mm)','Spodná hrana (mm)','Horná hrana (mm)'],...items.flatMap(item=>item.meshes.map(mesh=>[PLAN_ROOMS.find(r=>r.id===item.roomId)?.name??'Terasy pri dome',item.name,mesh.name,mesh.id,mesh.rect.x0,mesh.rect.y0,mesh.rect.x1-mesh.rect.x0,mesh.rect.y1-mesh.rect.y0,mesh.z1-mesh.z0,mesh.z0,mesh.z1]))];
    const csv=rows.map(row=>row.map(v=>`"${String(v).replaceAll('"','""')}"`).join(';')).join('\r\n');download(`dom-variant-c${layoutFileSuffix(livingLayout)}-kompletny-supis.csv`,'\uFEFF'+csv,'text/csv;charset=utf-8');setAnnouncement('Kompletný súpis bol stiahnutý.');
  };
  const exportSvg=()=>{
    const source=document.getElementById('pd-export-source')?.querySelector('svg');if(!source)return;
    const copy=source.cloneNode(true) as SVGSVGElement;copy.setAttribute('xmlns','http://www.w3.org/2000/svg');copy.setAttribute('width','1600');copy.setAttribute('height','1500');
    const style=document.createElementNS('http://www.w3.org/2000/svg','style');style.textContent='text{font-family:Arial,sans-serif}.pd-doors path{fill:none;stroke:#536478;stroke-width:12}.fp-door-gap{fill:#fff}.pd-room-labels text{paint-order:stroke}';copy.prepend(style);
    download(`dom-variant-c${layoutFileSuffix(livingLayout)}-podorys.svg`,new XMLSerializer().serializeToString(copy),'image/svg+xml');setAnnouncement('Vektorový pôdorys bol stiahnutý.');
  };
  useEffect(()=>{
    if(!exportJob)return;
    const source=exportHost.current?.querySelector('svg');
    if(!source){setExportJob(null);setAnnouncement('Export PNG sa nepodaril: výkres sa nevykreslil.');return;}
    let cancelled=false;
    const mode=exportJob.color?'farebny':'ciernobiely';
    rasterizeSheet(source,[PX_PER_MM,PX_PER_MM*.66,PX_PER_MM*.45]).then(({blob,scale})=>{
      if(cancelled)return;
      download(`dom-variant-c${layoutFileSuffix(exportJob.livingLayout)}-podorys-L${exportJob.level}-${mode}.png`,blob,'image/png');
      setAnnouncement(`Pôdorys úrovne ${exportJob.level} (${exportJob.color?'farebný':'čiernobiely'}) bol stiahnutý ako PNG ${Math.round(SHEET.w*scale)} × ${Math.round(SHEET.h*scale)} px.`);
    }).catch((error:Error)=>{if(!cancelled)setAnnouncement(`Export PNG sa nepodaril: ${error.message}`);}).finally(()=>{if(!cancelled)setExportJob(null);});
    return ()=>{cancelled=true;};
  },[exportJob]);
  const startExport=(level:ExportLevel)=>{setExportJob({level,color:exportColor,livingLayout});setAnnouncement(`Pripravujem PNG pôdorysu úrovne ${level}.`);};
  const measureEnd=measurement[1]??hoverPoint,measureDistance=measurement[0]&&measureEnd?Math.hypot(measureEnd.x-measurement[0].x,measureEnd.y-measurement[0].y):null;
  const scaleMm=view.width>50000?5000:view.width>7000?1000:100;
  return <main className="pd-root" data-mobile-panel={mobilePanel} data-manual={manualOpen}>
    <header className="pd-header"><div className="pd-brand"><Link href="/" aria-label="Späť do 3D domu"><BoxIcon size={23}/></Link><span className="pd-header-divider"/><div><span className="pd-overline">DOM / DOKUMENTÁCIA</span><h1>Pôdorys & manuál</h1></div></div>
      <span className="pd-model-badge"><span/>Aktuálny 3D model <b>C</b></span>
      <div className="pd-header-actions"><Link href="/" className="pd-text-button">Otvoriť 3D<ArrowUpRight size={16}/></Link><button className="pd-primary" onClick={()=>setManualOpen(!manualOpen)}><BookOpen size={17}/>{manualOpen?'Späť na pôdorys':'Manuál domu'}</button></div>
    </header>
    <div className="pd-mobile-tabs" aria-label="Panely dokumentácie">{([['rooms','Miestnosti',List],['plan','Pôdorys',Layers3],['detail','Detail',Ruler]] as const).map(([id,label,Icon])=><button key={id} aria-pressed={mobilePanel===id} onClick={()=>setMobilePanel(id)}><Icon size={16}/>{label}</button>)}</div>
    <div className="pd-workspace">
      <aside className="pd-library" aria-label="Miestnosti a súpis predmetov"><div className="pd-search"><Search size={17}/><input aria-label="Hľadať prvky v zvolenej oblasti" value={query} placeholder="Nájsť nábytok, stenu…" onChange={event=>{setQuery(event.target.value);setLeftTab('objects');}}/>{query&&<button aria-label="Vymazať hľadanie" onClick={()=>setQuery('')}><X size={14}/></button>}</div>
        <div className="pd-library-tabs"><button aria-pressed={leftTab==='rooms'} onClick={()=>setLeftTab('rooms')}>Miestnosti <span>{PLAN_ROOMS.length}</span></button><button aria-pressed={leftTab==='objects'} onClick={()=>setLeftTab('objects')}>Prvky <span>{items.length}</span></button></div>
        <div className="pd-library-scroll">
          {leftTab==='rooms'?<><button className={`pd-room-row pd-all-rooms ${!roomId?'active':''}`} onClick={()=>chooseRoom('')}><Layers3 size={19}/><span>Celý dom<small>Prízemie · variant C</small></span><Focus size={16}/></button><div className="pd-list-caption">MIESTNOSŤ <span>PLOCHA</span></div>{PLAN_ROOMS.map((r,i)=><button className={`pd-room-row ${roomId===r.id?'active':''}`} key={r.id} onClick={()=>chooseRoom(r.id)}><span className="pd-room-number" style={{background:ROOM_COLORS[i]}}>{r.number.slice(2)}</span><span>{r.name}<small>{numberSk(r.area,2)} m²</small></span><ChevronRight size={14}/></button>)}<button className="pd-room-row" onClick={()=>{setRoomId('EXTERIOR');setLeftTab('objects');fit(PLAN_FULL_BOUNDS,0);}}><Layers3 size={18}/><span>Terasy pri dome<small>Vonkajšie sedenie</small></span><ChevronRight size={14}/></button></>:<>
            <div className="pd-inventory-filters"><label>Oblasť<select value={roomId} onChange={event=>setRoomId(event.target.value)}><option value="">Celý dom</option><option value="EXTERIOR">Terasy pri dome</option>{PLAN_ROOMS.map(r=><option key={r.id} value={r.id}>{r.number} · {r.name}</option>)}</select></label><label>Kategória<select value={category} onChange={event=>setCategory(event.target.value as typeof category)}><option value="all">Všetky prvky</option>{Object.entries(PLAN_CATEGORIES).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label></div>
            <p className="pd-results-count">{results.length} prvkov{query&&' vo výsledkoch'}</p>
            {results.length===0?<div className="pd-empty"><Search/><strong>Nič sa nenašlo</strong><p>Skús kratší názov alebo vyhľadávanie v celom dome.</p><button onClick={()=>{setQuery('');setRoomId('');setCategory('all');}}>Zobraziť všetky prvky</button></div>:results.map(item=><button className={`pd-object-row ${item.id===selectedId?'active':''}`} key={item.id} onClick={()=>choose(item,null,true)}><span className={`pd-category-dot ${item.category}`}/><span>{item.name}<small>{PLAN_ROOMS.find(r=>r.id===item.roomId)?.name??'Terasy pri dome'}</small></span><ChevronRight size={14}/></button>)}
          </>}
        </div><div className="pd-library-footer"><Check size={14}/><span>Geometria prevzatá z 3D<small>{numberSk(allParts)} merateľných súčastí</small></span></div>
      </aside>
      <section className="pd-drawing" aria-label="Interaktívny pôdorys">
        <div className="pd-drawing-top"><div><span className="pd-overline">01 / PÔDORYS PRÍZEMIA</span><strong>{room?.name??(roomId==='EXTERIOR'?'Terasy pri dome':'Celý dom')}{roomId&&<button title="Celý dom" aria-label="Zrušiť výber miestnosti" onClick={()=>chooseRoom('')}><X size={14}/></button>}</strong></div><div className="pd-drawing-options">
          <details className="pd-menu"><summary aria-label="Vrstvy plánu"><Layers3 size={17}/><span>Vrstvy</span><ChevronDown size={12}/></summary><div className="pd-menu-panel"><b>Zobraziť v pláne</b>{Object.entries(PLAN_CATEGORIES).map(([id,label])=><label key={id}><input type="checkbox" checked={layers[id as PlanCategory]} onChange={event=>setLayers(prev=>({...prev,[id]:event.target.checked}))}/>{label}</label>)}<hr/><label><input type="checkbox" checked={clearances} onChange={e=>setClearances(e.target.checked)}/>Obsluha technickej miestnosti</label><label><input type="checkbox" checked={overhead} onChange={e=>setOverhead(e.target.checked)}/>Prvky nad 2,10 m</label><label><input type="checkbox" checked={details} onChange={e=>setDetails(e.target.checked)}/>Všetky drobné súčasti</label><label><input type="checkbox" checked={dimensions} onChange={e=>setDimensions(e.target.checked)}/>Kóty pôdorysu</label></div></details>
          <details className="pd-menu pd-export-menu"><summary aria-label="Export pôdorysu do PNG"><ImageDown size={17}/><span>Export PNG</span><ChevronDown size={12}/></summary><div className="pd-menu-panel pd-export-panel"><b>Jeden ucelený výkres · A1 · 1 : 50 · PNG</b>
            <div className="pd-export-mode" role="group" aria-label="Farebnosť exportu"><button aria-pressed={exportColor} onClick={()=>setExportColor(true)}><Palette size={14}/>Farebný</button><button aria-pressed={!exportColor} onClick={()=>setExportColor(false)}><Contrast size={14}/>Čiernobiely</button></div>
            <p>Úroveň podrobnosti kótovania</p>
            {EXPORT_LEVELS.map(spec=><button key={spec.level} className="pd-export-level" disabled={exportJob!==null} onClick={()=>startExport(spec.level)}><span>L{spec.level}</span><span><strong>{spec.title}</strong><small>{spec.summary}</small></span></button>)}
            <small className="pd-export-note">{exportJob?`Pripravujem PNG úrovne ${exportJob.level}…`:'Modulové osi A–F (šírka) a 1–6 (hĺbka), kódy stien, otvorov a prvkov robia výkres čitateľným aj v čiernobielej tlači.'}</small>
          </div></details>
          <details className="pd-menu"><summary aria-label="Stiahnuť dokumentáciu"><ArrowDownToLine size={17}/></summary><div className="pd-menu-panel pd-downloads"><button onClick={()=>setManualOpen(true)}><BookOpen size={16}/>Manuál a tlač do PDF</button><button onClick={exportSvg}><ArrowDownToLine size={16}/>Vektorový pôdorys SVG</button><button onClick={exportCsv}><FileSpreadsheet size={16}/>Kompletný súpis CSV</button><Link href="/koncept-2d?variant=c&amp;mode=study"><Layers3 size={16}/>Dispozičné štúdie</Link></div></details>
        </div></div>
        <div className={`pd-canvas pd-tool-${tool}`} ref={canvas}>
          <svg ref={svg} className="pd-plan" viewBox={`${view.x} ${view.y} ${view.width} ${view.height}`} tabIndex={0} aria-label="Pôdorys. Ťahaním posúvajte, kolieskom približujte. Prvok vyberiete kliknutím alebo zo zoznamu." onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerCancel={onPointerUp} onClick={onPlanClick} onDoubleClick={()=>{if(tool!=='measure')fit(component?.rect??selected?.rect??room?.bounds??PLAN_FULL_BOUNDS);}} onKeyDown={event=>{
            if(event.key==='Escape'){setSelectedId(null);setComponentId(null);setMeasurement([]);setTool('select');}
            if(event.key==='+'||event.key==='='){event.preventDefault();zoomBy(.8);}if(event.key==='-'){event.preventDefault();zoomBy(1.25);}
            if(event.key==='0'){event.preventDefault();fit(PLAN_FULL_BOUNDS,0);}
            if(event.key.toLowerCase()==='v')changeTool('select');if(event.key.toLowerCase()==='h')changeTool('pan');if(event.key.toLowerCase()==='m')changeTool('measure');
            if(event.key.startsWith('Arrow')){event.preventDefault();setView(v=>({...v,x:v.x+(event.key==='ArrowRight'?1:event.key==='ArrowLeft'?-1:0)*v.width*.08,y:v.y+(event.key==='ArrowDown'?1:event.key==='ArrowUp'?-1:0)*v.height*.08}));}
          }}>
            <PlanGeometry layers={layers} details={details||zoom>250} overhead={overhead} selectedId={selectedId} componentId={componentId} roomId={roomId} labels={zoom<600&&!(roomId==='ROOM-1-07'&&clearances)} dimensions={dimensions} unit={unit} unitsPerPixel={view.width/canvasWidth} livingLayout={livingLayout}/>
            {roomId==='ROOM-1-07'&&clearances&&<TechnicalClearances/>}
            {selected&&<g pointerEvents="none"><Box r={component?.rect??selected.nominal??selected.rect} fill="none" stroke="#2763d5" strokeWidth="1.5" vectorEffect="non-scaling-stroke" strokeDasharray="5 3"/><PlanDimensions rect={component?.rect??selected.nominal??selected.rect} unit={unit} size={view.width/canvasWidth*12}/></g>}
            {measurement[0]&&<g pointerEvents="none" className="pd-measure-line"><circle cx={measurement[0].x} cy={measurement[0].y} r={view.width/canvasWidth*4}/>{measureEnd&&<><path d={`M${measurement[0].x},${measurement[0].y}L${measureEnd.x},${measureEnd.y}`} vectorEffect="non-scaling-stroke"/><circle cx={measureEnd.x} cy={measureEnd.y} r={view.width/canvasWidth*4}/></>}</g>}
          </svg>
          <div className="pd-canvas-tools" role="toolbar" aria-label="Nástroje pôdorysu">{([['select','Vybrať prvok (V)',MousePointer2],['pan','Posúvať plátno (H)',Hand],['measure','Zmerať vzdialenosť (M)',Ruler]] as const).map(([id,label,Icon])=><button key={id} title={label} aria-label={label} aria-pressed={tool===id} onClick={()=>changeTool(id)}><Icon size={19}/></button>)}<i/><button title="Zobraziť celý dom (0)" aria-label="Zobraziť celý dom" onClick={()=>{fit(PLAN_FULL_BOUNDS,0);setRoomId('');}}><Maximize2 size={19}/></button><button title="Pomoc s ovládaním" aria-label="Pomoc s ovládaním" onClick={()=>help.current?.showModal()}><CircleHelp size={19}/></button></div>
          <div className="pd-zoom"><button aria-label="Oddialiť" onClick={()=>zoomBy(1.25)}><Minus size={16}/></button><button title="Prispôsobiť celý dom" onClick={()=>fit(PLAN_FULL_BOUNDS,0)}>{zoom}%</button><button aria-label="Priblížiť" onClick={()=>zoomBy(.8)}><Plus size={16}/></button></div>
          {tool==='measure'?<div className="pd-measure-card"><Ruler size={17}/><div><strong>{measureDistance!==null?formatMm(measureDistance,unit):'Klikni na prvý bod'}</strong><span>{measurement.length===2?'Vzdialenosť medzi zvolenými bodmi':measurement.length===1?'Klikni na druhý bod':'Potom označ druhý koniec vzdialenosti'}</span>{measurement.length===2&&<small>↔ {formatMm(Math.abs(measurement[1].x-measurement[0].x),unit)} &nbsp; ↕ {formatMm(Math.abs(measurement[1].y-measurement[0].y),unit)}</small>}</div><button aria-label="Vymazať meranie" onClick={()=>{setMeasurement([]);setHoverPoint(null);}}><X size={16}/></button></div>:<div className="pd-canvas-hint"><Hand size={13}/>Ťahaním posúvaj · kolieskom približuj · kliknutím vyber</div>}
          <div className="pd-scale"><span style={{width:scaleMm/view.width*canvasWidth}}/><small>{formatMm(scaleMm,'m')}</small></div>
        </div>
        <footer className="pd-drawing-footer"><span><span className="pd-live-dot"/>Rozmery z modelu</span><span className="pd-footer-scope">Nábytok · vybavenie · steny · výplne</span><label>Jednotky <select aria-label="Jednotky rozmerov" value={unit} onChange={e=>setUnit(e.target.value as Units)}><option value="mm">mm</option><option value="cm">cm</option><option value="m">m</option></select></label></footer>
      </section>
      <aside className="pd-inspector" aria-label="Detail a rozmery vybraného prvku">
        {selected?<><div className="pd-inspector-heading"><span className="pd-overline">{PLAN_CATEGORIES[selected.category]}</span><button aria-label="Zavrieť detail" onClick={()=>{setSelectedId(null);setComponentId(null);setMobilePanel('plan');requestAnimationFrame(()=>svg.current?.focus({preventScroll:true}));}}><X size={18}/></button></div><h2 ref={inspectorTitle} tabIndex={-1}>{selected.name}</h2><p className="pd-item-room">{selectedRoom?`${selectedRoom.number} · ${selectedRoom.name}`:'Terasy pri dome'}{selected.layout&&` · obývačka vo variante ${selected.layout}`}</p>
          <div className="pd-item-preview"><ItemMiniature item={selected} componentId={componentId}/><span>POHĽAD ZHORA</span></div>
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
        </>:<><span className="pd-overline">{room?'MIESTNOSŤ':'SPRIEVODCA DOMOM'}</span><h2>{room?.name??'Od celku\nk detailu.'}</h2><p className="pd-intro">{room?'Vyber nábytok, vybavenie alebo stenu. Každý prvok má vlastný detail s rozmermi.':'Celý dom v jednom pláne. Vyber miestnosť alebo klikni na ľubovoľný prvok.'}</p>
          <LivingLayoutSwitch value={livingLayout} onChange={chooseLivingLayout}/>
          <div className="pd-summary-metric"><span>{room?'Čistá plocha miestnosti':'Čistá plocha prízemia'}</span><strong>{numberSk(room?.area??PLAN_ROOMS.reduce((sum,r)=>sum+r.area,0),2)}<small>m²</small></strong><span>{room?`Výška ${formatMm(room.clearHeightMm,'m')}${room.ceiling==='VAULTED_TO_RIDGE'?' · šikmý strop':''}`:'13 miestností vrátane garáže'}</span></div>
          {room?<><RoomGuidance roomId={room.id} livingLayout={livingLayout}/>{room.id==='ROOM-1-07'&&clearances&&<TechnicalLegend/>}<h3>Rozsah miestnosti</h3><Dimensions rect={room.bounds} height={room.clearHeightMm} unit={unit}/><p className="pd-dimension-note">Pri členitej miestnosti ide o celkový obal. Jednotlivé obdĺžnikové časti sú rozpísané v manuáli.</p><button className="pd-focus-item" onClick={()=>{setLeftTab('objects');setMobilePanel('rooms');}}>Prvky v tejto miestnosti<ChevronRight size={16}/></button></>:<div className="pd-steps"><div><span>01</span><p><strong>Nájdi miestnosť</strong>Výberom vľavo sa pôdorys priblíži.</p></div><div><span>02</span><p><strong>Rozklikni predmet</strong>Uvidíš jeho rozmery a jednotlivé diely.</p></div><div><span>03</span><p><strong>Vezmi si manuál</strong>Prehľad miestností a vybavenia si môžeš vytlačiť.</p></div></div>}
          <div className="pd-info-card"><Ruler size={20}/><strong>Ako čítať rozmery</strong><p>Čísla vychádzajú z aktuálnej geometrie 3D. Rozmer matraca, rámu a celého priestoru okolo postele môže byť odlišný.</p><button onClick={()=>help.current?.showModal()}>Vysvetlenie a ovládanie<ArrowUpRight size={14}/></button></div>
          <div className="pd-inspector-bottom"><span>{numberSk(items.length)} prvkov</span><span>{numberSk(allParts)} súčastí</span></div>
        </>}
      </aside>
    </div>
    <ExportPlan livingLayout={livingLayout}/>
    <div ref={exportHost} hidden aria-hidden="true">{exportJob&&<ExportSheet level={exportJob.level} color={exportJob.color} livingLayout={exportJob.livingLayout}/>}</div>
    {manualOpen&&<DocumentationManual printParts={printParts} setPrintParts={setPrintParts} setManualOpen={setManualOpen} livingLayout={livingLayout}/>}
    <dialog className="pd-help" ref={help} aria-labelledby="pd-help-title"><form method="dialog"><button aria-label="Zavrieť pomoc"><X size={20}/></button></form><span className="pd-overline">RÝCHLY SPRIEVODCA</span><h2 id="pd-help-title">Dom pod kontrolou.</h2><p>Začni výberom miestnosti. Nábytok a steny môžeš vybrať priamo v pláne alebo v zozname prvkov.</p><dl><dt>Posun plánu</dt><dd>Ťahanie myšou alebo jedným prstom. Na klávesnici šípky.</dd><dt>Priblíženie</dt><dd>Koliesko, dva prsty alebo + / −. Kláves 0 zobrazí celý dom.</dd><dt>Detail</dt><dd>Klikni na predmet. Drobný diel vyber v zozname „Súčasti prvku“.</dd><dt>Meranie</dt><dd>Nástroj pravítko (M), potom dva body. Presnosť závisí od miesta kliknutia.</dd><dt>Ukončiť výber</dt><dd>Escape zruší výber aj meranie. V = výber, H = posun.</dd></dl><h3>Čo znamenajú rozmery</h3><p>↔ a ↕ sú vodorovný a zvislý smer plánu. Výška je tretí rozmer. „Rozmery podľa zadania“ pochádzajú zo špecifikácie nábytku; „priestorový rozsah“ zahŕňa všetky jeho diely a presahy. Najmenšie súčasti sú dostupné aj vtedy, keď nie sú pri oddialení viditeľné.</p><p>Manuál dokumentuje geometriu modelu. Pre výrobu nábytku a realizáciu treba rozmery overiť na stavbe.</p></dialog>
    <div className="sr-only" aria-live="polite" aria-atomic="true">{announcement}</div>
  </main>;
}

const ExportPlan=memo(function ExportPlan({livingLayout}:{livingLayout:LivingLayoutId}){return <div id="pd-export-source" hidden><StaticPlan viewBox={fitPlanRect(PLAN_FULL_BOUNDS,1.2,0)} livingLayout={livingLayout}/></div>;});

/** Right-panel switch between the documented arrangements of the living zone 1.03. */
function LivingLayoutSwitch({value,onChange}:{value:LivingLayoutId;onChange:(next:LivingLayoutId)=>void}){
  const layout=LIVING_LAYOUTS[value];
  return <div className="pd-living-switch" data-testid="pd-living-switch"><span className="pd-overline">OBÝVAČKA 1.03 · VARIANT ROZLOŽENIA</span>
    <div role="group" aria-label="Variant obývacej zóny">{LIVING_LAYOUT_IDS.map(id=><button key={id} type="button" aria-pressed={value===id} onClick={()=>onChange(id)}><b>{id}</b><span>{LIVING_LAYOUTS[id].label}</span></button>)}</div>
    <p>{layout.summary}</p>
    {value!==DEFAULT_LIVING_LAYOUT_ID&&<small>3D model zatiaľ ukazuje variant A. Tento pôdorys, súpis, manuál aj exporty už platia pre variant {value}.</small>}
  </div>;
}

function RoomGuidance({roomId,livingLayout}:{roomId:string;livingLayout:LivingLayoutId}){
  const notes=planRoomNotes(roomId,livingLayout);
  if(!notes)return null;
  return <div className="pd-room-guidance"><h3>Prečo je to takto</h3>{notes.map(note=><p key={note}>{note}</p>)}{roomId==='ROOM-1-07'&&<div className="pd-source-links"><a href={HEATING_SOURCES.boiler} target="_blank" rel="noreferrer">Kotol ↗</a><a href={HEATING_SOURCES.accumulator} target="_blank" rel="noreferrer">Nádrž ↗</a><a href={HEATING_SOURCES.manual} target="_blank" rel="noreferrer">Návod PLUS · s. 13, 16 ↗</a></div>}</div>;
}

const DocumentationManual=memo(function DocumentationManual({printParts,setPrintParts,setManualOpen,livingLayout}:{printParts:boolean;setPrintParts:(value:boolean)=>void;setManualOpen:(value:boolean)=>void;livingLayout:LivingLayoutId}) {
  const items=planItemsFor(livingLayout),allParts=partsCount(items),living=LIVING_LAYOUTS[livingLayout];
  return <div className="pd-print" aria-label="Manuál domu"><div className="pd-manual-toolbar"><button onClick={()=>setManualOpen(false)}><ArrowLeft size={17}/>Späť na pôdorys</button><label><input type="checkbox" checked={printParts} onChange={e=>setPrintParts(e.target.checked)}/>Priložiť všetkých {numberSk(allParts)} súčastí</label><button className="pd-primary" onClick={()=>window.print()}><Printer size={17}/>Tlačiť / uložiť PDF</button></div>
      <section className="pd-paper pd-cover"><span className="pd-overline">DOM / 01 / PRÍZEMIE</span><h2>Manuál vášho domu.</h2><p>{`Variant C · pôdorys a súpis aktuálneho 3D modelu · obývačka 1.03 vo variante ${living.id}: ${living.label}`}</p><div id="pd-print-overview"><StaticPlan viewBox={fitPlanRect(PLAN_FULL_BOUNDS,1.2,0)} livingLayout={livingLayout}/></div><div className="pd-cover-metrics"><span>{PLAN_ROOMS.length} miestností</span><span>{items.length} prvkov</span><span>{numberSk(allParts)} súčastí</span></div><h3>Ako čítať tento manuál</h3><p>Všetky tabuľkové rozmery sú v milimetroch. X (↔) a Y (↕) sú rozmery v pôdoryse, výška smeruje nahor. Rozsah modelu zahŕňa presahy a všetky súčasti. Pri oblých a natočených prvkoch uvádzame obdĺžnik, ktorý ich obopína. Kóty majú prednosť pred meraním na vytlačenej stránke.</p><p>Dokumentácia pokrýva prízemie: interiér, obvodové steny, výplne a kryté priestory a vonkajšie sedenie pri dome. Podklady zachytávajú model, nie zameranie stavby ani výrobný výkres. Záhrada, podzemné rozvody a strešný plášť nie sú obsahom týchto listov.</p><p>Pri voľnom meraní v aplikácii záleží na presnosti vybraných bodov. Presné rozmery jednotlivých prvkov nájdeš v ich detaile a súpise.</p></section>
      {PLAN_ROOMS.map(r=><section className="pd-paper pd-room-sheet" key={r.id}><div className="pd-paper-heading"><div><span className="pd-overline">LIST {r.number}</span><h2>{r.name}</h2></div><strong>{numberSk(r.area,2)} m²</strong></div><div className="pd-room-sheet-plan"><StaticPlan viewBox={fitPlanRect(r.bounds,1.6,800)} roomId={r.id} livingLayout={livingLayout}/></div><div className="pd-room-specs"><span>Svetlá výška: {formatMm(r.clearHeightMm)}{r.ceiling==='VAULTED_TO_RIDGE'?' pri stene · šikmý strop do 4 850 mm':''}</span><span>Podlaha: {r.floor==='VINYL'?'vinyl':r.floor==='TILE'?'dlažba':'epoxid'}</span>{r.id==='ROOM-1-03'&&<span>Obývacia zóna: variant {living.id} · {living.label}</span>}</div><RoomGuidance roomId={r.id} livingLayout={livingLayout}/>{r.id==='ROOM-1-07'&&<TechnicalLegend/>}<p>Časti čistej podlahy: {r.rectsMm.map(p=>`${numberSk(p.x1-p.x0)} × ${numberSk(p.y1-p.y0)}`).join(' + ')} mm. Plocha je súčtom týchto častí.</p><table><thead><tr><th>Prvok</th><th>X ↔</th><th>Y ↕</th><th>Výška</th><th>Diely</th></tr></thead><tbody>{items.filter(item=>item.roomId===r.id).map(item=><tr key={item.id}><td>{item.name}{item.product&&<small>{item.product.dimensions} · katalóg</small>}{item.nominal&&<small>Rozmer podľa zadania modelu</small>}{item.opening&&<small>Rozmery otvoru: {numberSk(item.opening.width)} × {numberSk(item.opening.height)} mm</small>}</td><td>{numberSk((item.nominal??item.rect).x1-(item.nominal??item.rect).x0)}</td><td>{numberSk((item.nominal??item.rect).y1-(item.nominal??item.rect).y0)}</td><td>{numberSk(item.z1-item.z0)}</td><td>{item.meshes.length}</td></tr>)}</tbody></table><footer>DOM · C · Rozmery v mm · Rozsah celku vrátane presahov, ak nie je uvedené inak.</footer></section>)}
      <section className="pd-paper"><span className="pd-overline">VONKAJŠIE SEDENIE</span><h2>Terasy pri dome</h2><p>Nábytok z aktuálneho 3D modelu. Rozmery v mm.</p><table><thead><tr><th>Prvok</th><th>X ↔</th><th>Y ↕</th><th>Výška</th></tr></thead><tbody>{items.filter(item=>item.roomId==='EXTERIOR').map(item=><tr key={item.id}><td>{item.name}</td><td>{numberSk(item.rect.x1-item.rect.x0)}</td><td>{numberSk(item.rect.y1-item.rect.y0)}</td><td>{numberSk(item.z1-item.z0)}</td></tr>)}</tbody></table></section>
      {printParts&&<section className="pd-paper pd-appendix"><h2>Kompletný rozpis súčastí</h2><p>Každá viditeľná fyzická súčasť exportovaných zostáv. Rozmery sú v mm.</p>{items.map(item=><div key={item.id}><h3>{PLAN_ROOMS.find(r=>r.id===item.roomId)?.number} · {item.name}</h3><table><thead><tr><th>Súčasť</th><th>X ↔</th><th>Y ↕</th><th>Výška</th><th>Od podlahy</th></tr></thead><tbody>{item.meshes.map(mesh=><tr key={mesh.id}><td>{mesh.name.split(' · ').slice(-1)[0]}</td><td>{numberSk(mesh.rect.x1-mesh.rect.x0)}</td><td>{numberSk(mesh.rect.y1-mesh.rect.y0)}</td><td>{numberSk(mesh.z1-mesh.z0)}</td><td>{numberSk(mesh.z0)}</td></tr>)}</tbody></table></div>)}</section>}
    </div>;
});
