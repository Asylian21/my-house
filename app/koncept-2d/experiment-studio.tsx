'use client';

import { useRef, type Dispatch, type SetStateAction } from 'react';
import Link from 'next/link';
import { ArrowLeft, ArrowUpRight, Check, Download, Expand, LockKeyhole, Minus, Plus, RotateCcw, Ruler, SlidersHorizontal } from 'lucide-react';
import { HOUSE } from '@/lib/twin-site';
import { area, rect } from '@/lib/floor-plan-concept';
import { createExperiment, DEFAULT_EXPERIMENT, normalizeExperiment, bedroomDoorOffsetMax, type ExperimentSettings } from '@/lib/floor-plan-experiment';
import './studio.css';
import { Box, Label, Dimension, VerticalDimension, Door } from './plan-svg';
import { GarageShell, GarageLoggiaLabel } from './garage-loggia';
import { EXPERIMENT_NAME, VariantTabs, type VariantNavigationProps, type PlanViewState } from './variant-tabs';
import './experiment.css';

const m = (n:number) => (n/1000).toLocaleString('sk-SK',{minimumFractionDigits:2,maximumFractionDigits:2});
const sqm = (n:number) => n.toLocaleString('sk-SK',{minimumFractionDigits:2,maximumFractionDigits:2});
const roomCenters:Record<string,[number,number]> = {'1.01':[22900,4600],'1.02':[19200,7010],'1.03':[24800,14800],'1.04':[25300,5850],'1.05':[24100,7800],'1.06':[23400,10250],'1.07':[26200,9530],'1.08':[19100,4950],'1.09':[18400,9340],'1.10':[13150,7550],'1.11':[15400,4730],'1.12':[8900,7040],'1.14':[13073,6800]};
function color(number:string) { if(number==='1.14')return 'neutral'; if(number==='1.12')return 'garage'; if(number==='1.10')return 'bedroom'; if(['1.08','1.09'].includes(number))return 'kid'; if(['1.05','1.06','1.11'].includes(number))return 'wet'; return 'neutral'; }

interface ExperimentStudioProps extends VariantNavigationProps {
  rawSettings: ExperimentSettings;
  setSettings: Dispatch<SetStateAction<ExperimentSettings>>;
  view: PlanViewState;
}
export function ExperimentalFloorPlanStudio({rawSettings,setSettings,variant,onVariantChange,view}:ExperimentStudioProps) {
  const settings=normalizeExperiment(rawSettings);
  const {full,setFull,dimensions,setDimensions,route,setRoute,selected,setSelected,zoom,setZoom}=view;
  const svg=useRef<SVGSVGElement>(null);
  const model=createExperiment(settings);
  const layoutName=EXPERIMENT_NAME;
  const frontStart=(id:string,start:number)=>id==='FRONT-02'?model.garageWindowStart:id==='FRONT-03'?model.frontWindowStart:start;
  const update=<K extends keyof ExperimentSettings>(key:K,value:ExperimentSettings[K])=>setSettings(s=>({...s,[key]:value}));
  const exportPlan=()=>{
    if(!svg.current)return;
    const copy=svg.current.cloneNode(true) as SVGSVGElement;
    copy.setAttribute('xmlns','http://www.w3.org/2000/svg');
    const bounds=copy.getAttribute('viewBox')!.split(' ').map(Number);
    const exportHeight=Math.round(1730*bounds[3]/bounds[2]);
    copy.setAttribute('width','1730');copy.setAttribute('height',String(exportHeight));
    copy.setAttribute('class','fp-export-plan');
    const style=document.createElementNS('http://www.w3.org/2000/svg','style');
    style.textContent=Array.from(document.styleSheets).flatMap(s=>{try{return Array.from(s.cssRules).map(r=>r.cssText).filter(t=>t.includes('fp-'));}catch{return [];}}).join('\n')+'\n.fp-export-plan{font-family:Arial,sans-serif}.fp-dimension text{font:145px monospace}';
    copy.prepend(style);
    const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(copy)],{type:'image/svg+xml;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download='dom-koncept-e-zalomenie.svg';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
  return <main className="fp-studio fp-experiment">
    <header className="fp-header"><Link href="/" className="fp-back" aria-label="Späť na 3D dom"><ArrowLeft size={18}/></Link><div className="fp-brand">DOM<span>/</span><h1>Dispozičné štúdio</h1><span className="fp-badge">VARIANT E</span></div><button className="fp-export" onClick={exportPlan}><Download size={16}/><span>Stiahnuť plán E</span></button></header>
    <div className="fp-workspace"><section className="fp-drawing" aria-label="Alternatívny pôdorys">
      <div className="fp-toolbar"><VariantTabs variant={variant} onVariantChange={onVariantChange}/><div className="fp-view-tools"><button aria-label="Oddialiť" disabled={zoom<=1} onClick={()=>setZoom(z=>Math.max(1,z-.25))}><Minus size={16}/></button><button aria-label="Priblížiť" disabled={zoom>=2.5} onClick={()=>setZoom(z=>Math.min(2.5,z+.25))}><Plus size={16}/></button><button className={dimensions?'active':''} onClick={()=>setDimensions(v=>!v)} aria-label="Zobraziť kóty" aria-pressed={dimensions}><Ruler size={18}/></button><button onClick={()=>setFull(v=>!v)} aria-label={full?'Detail nočnej časti':'Celý dom'} aria-pressed={full}><Expand size={18}/><span>{full?'Detail':'Celý dom'}</span></button></div></div>
      <div className="fp-sheet" role="tabpanel" id="floor-plan-panel" aria-labelledby={`floor-plan-tab-${variant}`}><div className="fp-sheet-heading"><span>VARIANT E / ZALOMENIE A KRYTÝ ZÁREZ</span><p>Menej priechodu. Viac miesta v garáži.</p></div><div className="fp-plan-scroll"><div className="fp-plan-canvas" style={{width:`${zoom*100}%`,height:`${zoom*100}%`}}>
<svg ref={svg} className="fp-plan" viewBox={full?'5500 -23100 23700 21500':'5550 -12350 17300 10850'} role="img" aria-label="Koncept E so spálňou do dvora, súkromným šatníkom a zalomeným vstupom">
            <title>{`Dom — ${layoutName}`}</title>
            <desc>Rozmery v milimetroch, dvor hore, ulica dole. Koncept pre diskusiu, nie realizačný výkres. Obrys 21600 × 19035 mm, nočné krídlo hlboké 8200 mm.</desc>
            <defs><pattern id="fp-grid" width="500" height="500" patternUnits="userSpaceOnUse"><path d="M500 0H0V500" fill="none" stroke="#dce2e4" strokeWidth="9"/></pattern><pattern id="fp-tile" width="400" height="400" patternUnits="userSpaceOnUse"><path d="M400 0H0V400" fill="none" stroke="#c5d8df" strokeWidth="9"/></pattern><marker id="fp-arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6" fill="none" stroke="#c06424" strokeWidth="1.4"/></marker></defs>
            <rect x="5400" y="-23100" width="24500" height="22000" fill="#fafcfc"/><rect x="5400" y="-23100" width="24500" height="22000" fill="url(#fp-grid)" opacity=".46"/>
            <path className="fp-envelope" d={`M${HOUSE.footprintMm.map(p=>`${p.x},${-p.y}`).join('L')}Z`}/>
            <GarageShell garage={model}/>
            <Box r={rect(21040,20035,28040,22035)} className="fp-terrace"/>
            <Label x={24400} y={21000} className="fp-outside">Terasa</Label>
            {/* Clear interiors are dimensioned from the source model, including the L-shaped garage. */}
            {model.rooms.map(room=><g key={room.id} className={`fp-room fp-${color(room.number)} ${selected===room.number?'fp-selected':''}`} onClick={()=>setSelected(room.number)}><title>{`${room.name}: ${sqm(area(room.rectsMm))} m²`}</title>{room.rectsMm.map((r,i)=><Box key={i} r={r}/>)}</g>)}
            <Box r={model.privateAlcove} className="fp-private-alcove"/><Box r={model.garageAddition} className="fp-garage-gain"><title>Plocha pridaná ku garáži: {sqm(model.garageGain)} m²</title></Box>
            {model.walls.map(w=><Box key={w.id} r={w.rectMm} className={`fp-wall ${w.role==='LOAD_BEARING'?'fp-bearing':''} ${w.changed?'fp-changed':''}`}/>)}
            {/* Original sill-level façade openings. Garden loggia door uses the current garage revision. */}
            {HOUSE.facades.front.openings.map(o=><g className={`fp-window ${(o.id==='FRONT-03'||o.id==='FRONT-02')?'fp-window-moved':''}`} key={o.id}><Box r={rect(frontStart(o.id,o.startXmm),3000,(frontStart(o.id,o.startXmm))+o.widthMm,3504)}/><path d={`M${frontStart(o.id,o.startXmm)},-3245h${o.widthMm}`}/></g>)}
            <Box r={rect(6440,HOUSE.facades.west.garageWindow.startYmm,6944,HOUSE.facades.west.garageWindow.startYmm+HOUSE.facades.west.garageWindow.widthMm)} className="fp-window"/><Box r={model.garageThreshold} className="fp-garage-opening"/>
            {HOUSE.facades.garden.openings.filter(o=>o.id!=='GARDEN-01').map(o=><g className="fp-window" key={o.id}><Box r={rect(o.startXmm,10699,o.startXmm+o.widthMm,11200)}/><path d={`M${o.startXmm},-10950h${o.widthMm}`}/></g>)}
            <Box r={model.garageBackOpening} className="fp-window"/>
            <g className="fp-window"><Box r={rect(21040,HOUSE.facades.wingWest.opening.startYmm,21543,HOUSE.facades.wingWest.opening.startYmm+HOUSE.facades.wingWest.opening.widthMm)}/><Box r={rect(HOUSE.porches.wingEnd.glazing.startXmm,19533,HOUSE.porches.wingEnd.glazing.startXmm+HOUSE.porches.wingEnd.glazing.widthMm,20035)}/></g>
            {HOUSE.facades.east.openings.map(o=><Box key={o.id} r={rect(27541,o.startYmm,28040,o.startYmm+o.widthMm)} className="fp-window"/>)}
            {/* Schematic furniture footprints, all in the same millimetre coordinate system. */}
            <g className="fp-furniture"><Box r={model.car} rx="380" className="fp-car"/><Box r={rect(7720,model.car.y0+1050,9330,model.car.y0+1900)} rx="130"/><Box r={rect(7720,model.car.y0+3430,9330,model.car.y0+4050)} rx="100"/>
              <Box r={model.fixtures.bath} rx="100" className="fp-fixture"/><Box r={rect(model.fixtures.bath.x0+80,model.fixtures.bath.y0+80,model.fixtures.bath.x1-80,model.fixtures.bath.y1-80)} rx="160"/><Box r={model.fixtures.basin} rx="60"/><Box r={model.fixtures.toilet} rx="180"/>
              <Box r={rect(19400,8000,20300,10000)} rx="55"/><Box r={rect(18100,10099,19300,10699)} rx="25"/>
              <><Box r={rect(18100,3630,19000,5630)} rx="55"/><Box r={rect(19900,3650,21150,4250)} rx="25"/></>
              {model.storageRuns.map((r,i)=>{const cx=(r.x0+r.x1)/2,cy=(r.y0+r.y1)/2,vertical=r.y1-r.y0>r.x1-r.x0;return <g key={i}><Box r={r} className="fp-wardrobe fp-walkin-cabinet"/><path d={vertical?`M${r.x0},${-cy}h600`:`M${cx},${-r.y0}v-600`}/><Label x={cx} y={vertical?cy:r.y0+260} transform={vertical?`rotate(-90 ${cx} ${-cy})`:undefined} className="fp-furniture-label">{m(vertical?r.y1-r.y0:r.x1-r.x0)} × 0,60 m</Label></g>;})}
              {model.garageShelves.map((r,i)=>{const cx=(r.x0+r.x1)/2,cy=(r.y0+r.y1)/2;return <g key={i}><Box r={r} className="fp-wardrobe fp-garage-shelf"/><Label x={cx} y={cy} transform={`rotate(-90 ${cx} ${-cy})`} className="fp-furniture-label">REGÁL {m(r.y1-r.y0)} × 0,50 m</Label></g>;})}
              <Box r={model.bed} rx="70" className="fp-bed"/>
              <><Box r={rect(model.bed.x0+110,model.bed.y0+110,model.bed.x0+540,model.bed.y0+settings.bedWidth/2-60)} rx="75"/><Box r={rect(model.bed.x0+110,model.bed.y0+settings.bedWidth/2+60,model.bed.x0+540,model.bed.y1-110)} rx="75"/><path d={`M${model.bed.x0+650},${-model.bed.y0}v${-settings.bedWidth}`}/></>
              <Label x={(model.bed.x0+model.bed.x1)/2+100} y={(model.bed.y0+model.bed.y1)/2} className="fp-bed-label">2,20 × {m(settings.bedWidth)}</Label>
              <Box r={rect(25500,17200,27250,19000)} rx="90"/><Box r={rect(23700,13300,25300,14200)} rx="150"/><Box r={rect(23000,10900,25450,11500)}/>
            </g>
            {model.doors.map(door=><Door key={door.id} door={door}/>)}<Door door={model.gardenDoor}/>
            <GarageLoggiaLabel garage={model} dimensions={dimensions}/>
            {route&&<g className="fp-route fp-shared-route" aria-label="Spoločný prechod mimo spálne"><path d={settings.garageConnected?`M${model.suiteRight+1000},-7100H${model.suiteRight-650}V-6244H10400`:`M${model.suiteRight+1000},-7100H${model.suiteRight-650}V-6244`} markerEnd={settings.garageConnected?'url(#fp-arrow)':undefined}/><path d={`M${model.suiteRight-650},-6244H${model.suiteRight-960}V-5140`} markerEnd="url(#fp-arrow)"/></g>}
            {model.rooms.map(room=>{const [x,y]=room.number==='1.10'?[(model.bed.x1+model.suiteRight)/2,9600]:room.number==='1.11'?[(model.bathLeft+model.bathRight)/2,4650]:room.number==='1.14'?[(model.bathLeft+model.suiteRight)/2,model.stepY-240]:roomCenters[room.number];return <g key={room.id} className="fp-room-label" pointerEvents="none"><Label x={x} y={y}>{room.number==='1.10'?'Spálňa':room.name.replace('Hlavný obytný priestor s kuchyňou','Obývačka + kuchyňa').replace('Zádverie, chodba, vstup','Zádverie')}</Label><Label x={x} y={y-220} className="fp-room-area">{sqm(area(room.rectsMm))} m²</Label></g>;})}
            <Label x={(11143+model.alcoveRight)/2} y={model.cabinetFront+230} className="fp-private-label">SÚKROMNÝ ŠATNÍK</Label>
            {model.garageBay&&<g className="fp-bay-label"><Label x={(model.garageBay.x0+model.garageBay.x1)/2} y={3740}>{m(settings.garageBayWidth)} × {m(model.garageBay.y1-model.garageBay.y0)} m</Label><Label x={(model.garageBay.x0+model.garageBay.x1)/2} y={model.stepY-180}>+{sqm(model.garageGain)} m²</Label><Label x={(model.garageBay.x0+model.garageBay.x1)/2} y={model.stepY-380}>pre garáž</Label></g>}
            <Label x={16200} y={11700} className="fp-orientation">D V O R  /  Z Á H R A D A ↑</Label><Label x={15000} y={1780} className="fp-orientation">↓ U L I C A  /  V S T U P</Label>
            {dimensions&&<><Dimension x0={11143} x1={15003+settings.expansion} y={11420}/><Dimension x0={15143+settings.expansion} x1={20641} y={11420}/><Dimension x0={model.suiteRight+140} x1={21242} y={2680}/><Dimension x0={model.bathLeft} x1={model.bathRight} y={2680}/><Dimension x0={6440} x1={28040} y={2180} label="VONKAJŠÍ ROZMER 21,60 m"/>
              <g className="fp-dimension"><path d="M6080,-3000V-11200M5980,-3000h200M5980,-11200h200"/><Label x={5900} y={7100} transform="rotate(-90 5900 -7100)">8,20 m · vonkajší rozmer</Label></g>
              <><Dimension x0={model.bed.x1} x1={model.suiteRight} y={8900} label={`${Math.round(model.footClearance)} mm`}/><Label x={12600} y={10500} className="fp-clearance-label">{Math.round(model.sideClearance)} mm k preskleniu</Label></>
            </>}
            {dimensions&&<><VerticalDimension x={model.bathLeft+250} y0={5744} y1={model.stepY} label={`${m(model.frontAisle)} m priechod`}/><Dimension x0={model.returnRight} x1={model.suiteRight} y={7500} label={`${m(model.entranceWidth)} m`}/><Label x={8400} y={settings.gardenRecess?8420:9550} className="fp-clearance-label">{m(3898)} × {m(model.garageDepth)} m</Label></>}
            {dimensions&&<g className="fp-dimension"><path d={`M${model.alcoveRight},-7741L${Math.min(model.bed.x1,model.alcoveRight)},${-model.bed.y0}`}/><Label x={model.alcoveRight+350} y={(7741+model.bed.y0)/2-170} className="fp-turn-label">roh {Math.floor(model.turnClearance)} mm</Label></g>}
            <g className="fp-scale"><path d="M6900,-2050h2000m-2000,-75v150m1000,-150v150m1000,-150v150"/><Label x={6900} y={2250}>0</Label><Label x={7900} y={2250}>1</Label><Label x={8900} y={2250}>2 m</Label></g>
          </svg></div></div><div className="fp-sheet-footer"><div className="fp-legend"><span><i className="parent"/>Súkromná spálňa</span><span><i className="private-closet"/>Súkromný šatník</span><span><i className="children"/>Detské izby</span><span><i className="walls"/>Steny a priečky</span></div><span>Oranžová trasa: spoločný prechod mimo spálne</span></div></div>
      <div className="fp-bottom-note"><LockKeyhole size={15}/><span>Pevný obrys 21,60 × 19,035 m · nočné krídlo 8,20 m</span></div>
    </section><aside className="fp-inspector" aria-label="Nastavenie experimentu E">
      <div className="fp-inspector-title"><span className="fp-eyebrow">VARIANT E / ZALOMENIE A KRYTÝ ZÁREZ</span><h2>Šatník dovnútra.<br/>Prechod okolo<span>.</span></h2><p>Priečka sa zalomí okolo súkromných skríň. {settings.garageConnected?'Rodina prejde krátkym vstupom do garáže alebo kúpeľne.':'Rodina prejde krátkym vstupom do kúpeľne. Garáž je teraz prístupná zvonka.'} Spálňa aj šatník sú za jednými dverami.</p></div>
      <div className="fp-privacy-summary"><strong><LockKeyhole size={17}/>Dve samostatné funkcie</strong><span>{settings.garageConnected?'Rodina: dom → vstup → kúpeľňa / garáž':'Rodina: dom → vstup → kúpeľňa'}</span><span>Rodičia: spálňa + vlastné skrine</span><span>Zo spálne do kúpeľne cez vstup</span></div>
      <div className="fp-metrics"><div><span>Spálňa so šatníkom</span><strong>{sqm(model.bedroomArea)} <small>m²</small></strong></div><div><span>Spoločný vstup L</span><strong>{sqm(model.foyerArea)} <small>m²</small></strong></div></div>
      <div className="fp-garage-summary"><strong>+{sqm(model.garageGain)} m² pre garáž</strong><p>Stena medzi vstupom a garážou pokračuje v línii bočnej steny kúpeľne. Garáž má spolu {sqm(model.garageArea)} m²; vstup je menší o {sqm(model.foyerReduction)} m² oproti predchádzajúcemu E.</p></div><div className="fp-secondary-metrics"><div><span>Kúpeľňa</span><strong>{sqm(model.bathroomArea)} m²</strong></div><div><span>Rozšírený výklenok garáže</span><strong>{sqm(area([model.garageBay!]))} m²</strong></div><p>Plocha spálne zahŕňa súkromný šatníkový výklenok aj pôdorys skríň ({sqm(model.storageArea)} m²).</p></div>
      {settings.gardenRecess&&<div className="fp-loggia-summary"><strong>Krytý zárez do záhrady</strong><p>Hĺbka {m(model.loggia.depth)} m · čelný otvor {m(model.loggia.openingWidth)} m. Rohový pilier, bočný vstup a zadné dvere podľa aktuálneho 3D modelu.</p><p>Čistá hĺbka garáže je {model.garageDepth.toLocaleString('sk-SK')} mm. Schematické auto 4,85 m využíva aj otvor brány, rovnako ako parkovacia poloha v 3D. Pri bráne zostáva približne 17 cm.</p></div>}
      <div className="fp-storage-summary"><strong>{m(model.storageLength)} m súkromných skríň</strong><span>Hĺbka 60 cm · čelá smerujú k posteli</span><p>Všetky skrine sa obsluhujú zo spálne. Pred nimi zostáva {Math.round(model.sideClearance)} mm po okraj postele.</p></div>
      <div className="fp-controls"><h3><SlidersHorizontal size={16}/>Hraj sa so stenami a dverami</h3>
        <label htmlFor="alcove-width">Šírka šatníkového výklenku <output>{m(settings.alcoveWidth)} m</output></label><input id="alcove-width" type="range" min="2000" max="2600" step="50" value={settings.alcoveWidth} onChange={e=>update('alcoveWidth',Number(e.target.value))}/><p className="fp-control-hint">Posúva zvislé zalomenie. Dlhšia skriňa zúži vstup k dverám spálne, teraz {m(model.entranceWidth)} m.</p>
        <label htmlFor="passage-depth">Hĺbka vstupu pri garážových dverách <output>{m(settings.passageDepth)} m</output></label><input id="passage-depth" type="range" min="1000" max="1200" step="50" value={settings.passageDepth} onChange={e=>update('passageDepth',Number(e.target.value))}/><p className="fp-control-hint">Posúva spodné rameno priečky, skriňu aj hranicu garáže. Väčšia hĺbka uberie miesto pri posteli.</p>
        <label htmlFor="bedroom-door-offset">Odsadenie dverí od pravej steny <output>{settings.doorOffset/10} cm</output></label><input id="bedroom-door-offset" type="range" min="100" max={bedroomDoorOffsetMax(settings)} step="50" value={settings.doorOffset} onChange={e=>update('doorOffset',Number(e.target.value))}/><p className="fp-control-hint">Posúva 80 cm dvere v hornej priečke. Rozsah sa prispôsobí polohe zalomenia.</p>
        <label htmlFor="bed-width">Šírka postele <output>{m(settings.bedWidth)} m</output></label><input id="bed-width" type="range" min="1600" max="2200" step="50" value={settings.bedWidth} onChange={e=>update('bedWidth',Number(e.target.value))}/><p className="fp-control-hint">Dĺžka postele je pevná: 2,20 m. Šírka 1,80 m zostáva predpoklad.</p>
        <details className="fp-extra-controls"><summary>Šírka izieb a garáž</summary><label htmlFor="expansion">Rozšírenie rodičovskej zóny <output>+{settings.expansion/10} cm</output></label><input id="expansion" type="range" min="0" max="600" step="50" value={settings.expansion} onChange={e=>update('expansion',Number(e.target.value))}/><p className="fp-control-hint">Posunie stenu smerom k detským izbám. Rozšíri spálňu, kúpeľňu aj vstup.</p><label htmlFor="garage-bay-width">Šírka výklenku v garáži <output>{m(settings.garageBayWidth)} m</output></label><input id="garage-bay-width" type="range" min="1000" max="1700" step="50" value={settings.garageBayWidth} onChange={e=>update('garageBayWidth',Number(e.target.value))}/><p className="fp-control-hint">Posúva bočnú stenu kúpeľne aj nové dvere do garáže. Väčší výklenok zúži kúpeľňu a vstup.{model.bathroomArea>6&&' Pri tomto nastavení má kúpeľňa viac ako 6 m².'}</p><label className="fp-check"><input type="checkbox" checked={settings.garageConnected} onChange={e=>update('garageConnected',e.target.checked)}/><span>Dvere do garáže <small>Zo spoločného vstupu</small></span></label><label className="fp-check"><input type="checkbox" checked={settings.gardenRecess} onChange={e=>update('gardenRecess',e.target.checked)}/><span>Krytý zárez do záhrady <small>Podľa aktuálneho 3D modelu</small></span></label></details>
        <button className="fp-reset" onClick={()=>setSettings(DEFAULT_EXPERIMENT)}><RotateCcw size={14}/>Obnoviť variant E</button>
      </div>
      <div className={`fp-fit ${Math.min(model.sideClearance,model.turnClearance)<600?'fp-tight':''}`} aria-live="polite"><strong><Check size={17}/>{Math.min(model.turnClearance,model.sideClearance)<440?'Pri skrini nevychádza overovaný priechod':Math.min(model.sideClearance,model.turnClearance)<450?'Prístup ku skriniam je veľmi tesný':Math.min(model.sideClearance,model.turnClearance)<600?'Posteľ sa zmestí, prístup je tesnejší':'Posteľ 2,20 m sa zmestí'}</strong><div><span>Medzi skriňou a posteľou</span><b>{Math.round(model.sideClearance)} mm</b></div><div><span>Posteľ → presklenie</span><b>{10699-model.bed.y1} mm</b></div><div><span>Zúženie pri rohu priečky</span><b>{Math.floor(model.turnClearance)} mm</b></div><div><span>Pred nohami postele</span><b>{model.footClearance} mm</b></div><p>Rozmery sú od hrany zakresleného rámu. Skrine sú navrhnuté s posuvnými čelami.{Math.min(model.turnClearance,model.sideClearance)<440&&' Zúženie má menej než 44 cm. Rozšír šatníkový výklenok, zmenši hĺbku vstupu alebo šírku postele.'}</p></div>
      <label className="fp-route-toggle"><input type="checkbox" checked={route} onChange={e=>setRoute(e.target.checked)}/>Ukázať rodinný prechod mimo spálne</label>
      <details className="fp-reasoning" open><summary>Čo prináša zalomenie</summary><ol><li>Skrine sa presunuli za dvere spálne. Cez rodičovský šatník už neprechádza rodina do garáže.</li><li>Spoločný vstup má {sqm(model.foyerArea)} m². Pri rovnakom rozšírení domu je to o {sqm(model.passageSaving)} m² menej než základný šatníkový vstup D.</li><li>Detská do ulice má {sqm(model.kidStreetArea)} m², detská do dvora {sqm(model.kidGardenArea)} m².</li></ol><p>Plocha sa presunula k spálni so šatníkom a ku garáži. Celková zastavaná plocha sa tým nezmenšila. Zalomenie pridáva roh a vyžaduje premyslený detail skrine.</p></details>
      <div className="fp-construction-note"><strong>Rovnaký obrys, variant E</strong><p>Kúpeľňa zostáva ako v D. Garážový výklenok pokračuje do bývalého priechodu a regál je otočený k stene kúpeľne. Náhrada pôvodnej nosnej steny pri garáži, rozvody a posunuté uličné okná zostávajú témou projektu.</p><p>{settings.gardenRecess?'Krytý zárez zostáva vonkajším priestorom pod pôvodnou strechou. Parkovanie pri bráne je tesné; poloha auta závisí od konkrétnej brány a rozmerov auta.':'Garáž využíva uzavretú krytú terasu; obrys domu sa nezväčšuje, uzavretie však znamená stavebnú prácu.'}</p></div>
      <div className="fp-source"><strong>Teoretický 2D koncept</strong><p>Rozmery a priechody sú modelované v milimetroch. Nejde o realizačný výkres ani potvrdenie statiky. Nábytok mimo rodičovskej časti je schematický.</p><Link href="/">Otvoriť existujúci 3D dom<ArrowUpRight size={14}/></Link></div>
    </aside></div>
  </main>;
}
