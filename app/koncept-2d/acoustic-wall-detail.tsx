import { useId } from 'react';
import { ACOUSTIC_ASSEMBLY, ACOUSTIC_WALL_SPECS } from '@/lib/acoustic-walls';
import { ACTIVE_ACOUSTIC_WALLS, INTERIOR_DOORS } from '@/lib/twin-interior';
import { CENTRAL_HALL_AXIS_Y_MM } from '@/lib/floor-plan-concept';

/** Common symbols in model millimetres, readable in colour and monochrome. */
export function AcousticHatches({prefix='ak',mono=false}:{prefix?:string;mono?:boolean}) {
  return <defs>
    <pattern id={`${prefix}-masonry`} width="80" height="80" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="80" height="80" fill={mono?'#fff':'#434a55'}/><path d="M0 0V80" stroke={mono?'#333':'#343e49'} strokeWidth="9"/>
    </pattern>
    <pattern id={`${prefix}-mineral-wool`} width="100" height="120" patternUnits="userSpaceOnUse">
      <rect width="100" height="120" fill={mono?'#fff':'#f4ebc7'}/><path d="M50 0C0 0 0 60 50 60S100 120 50 120" fill="none" stroke={mono?'#333':'#847339'} strokeWidth="8"/>
    </pattern>
    <pattern id={`${prefix}-gypsum-board`} width="32" height="32" patternUnits="userSpaceOnUse">
      <rect width="32" height="32" fill={mono?'#b8b8b8':'#52768a'}/><path d="M0 16H32" stroke={mono?'#555':'#345568'} strokeWidth="3"/>
    </pattern>
    <pattern id={`${prefix}-plaster`} width="32" height="32" patternUnits="userSpaceOnUse">
      <rect width="32" height="32" fill={mono?'#f5f5f5':'#dfe4e5'}/><circle cx="16" cy="16" r="3" fill={mono?'#777':'#789096'}/>
    </pattern>
  </defs>;
}

export function AcousticWallMarks({roomId='',fontSize=110,color='#58492f'}:{roomId?:string;fontSize?:number;color?:string}) {
  return <g className="pd-acoustic-marks">
    {ACTIVE_ACOUSTIC_WALLS.filter(w=>!roomId||w.rooms.some(id=>id===roomId)).map(w=>{
      // AK-02's midpoint is occupied by the WC; place its callout in the clear
      // band between the toilet and bath, leaving sanitary symbols readable.
      const horizontal=w.axis==='y';
      const x=horizontal?w.rectMm.x0+850:w.rectMm.x0-350, y=horizontal?-(w.rectMm.y0-250):w.mark==='AK-02'?-(w.rectMm.y0+1050):-(w.rectMm.y0+w.rectMm.y1)/2;
      return <g key={w.mark} data-item={w.mark} data-acoustic-mark={w.mark}>
        <title>{`${w.mark} · ${w.location} · ${w.assembly.code} · ${w.assembly.totalMm} mm`}</title>
        <path d={horizontal?`M${x} ${y-fontSize*.8}V${-(w.rectMm.y0+w.rectMm.y1)/2}`:`M${x+fontSize*1.8} ${y}H${w.rectMm.x0+50}`} stroke={color} strokeWidth="12"/>
        <rect x={x-fontSize*1.9} y={y-fontSize*.8} width={fontSize*3.8} height={fontSize*1.6} rx="20" fill="white" stroke={color} strokeWidth="10"/>
        <text x={x} y={y+fontSize*.35} textAnchor="middle" fontSize={fontSize} fontWeight="700" fill={color}>{w.mark}</text>
        {w.mark==='AK-03'&&<g data-acoustic-junction="D-AK03-01">
          <title>D1 · Napojenie H200 pri dverách: utesnený obvodový profil a dve oddeľovacie škáry J1/J2</title>
          <path d={`M${w.rectMm.x0+230} ${-(w.rectMm.y0-560)}V${-(w.rectMm.y0-220)}L${w.rectMm.x0+30} ${-w.rectMm.y0}`} fill="none" stroke={color} strokeWidth="10"/>
          <circle cx={w.rectMm.x0+230} cy={-(w.rectMm.y0-650)} r="90" fill="white" stroke={color} strokeWidth="10"/>
          <text x={w.rectMm.x0+230} y={-(w.rectMm.y0-650)+30} textAnchor="middle" fontSize="80" fontWeight="700" fill={color}>D1</text>
        </g>}
      </g>;
    })}
  </g>;
}

/** The horizontal longitudinal axis of the main hall, not a building grid axis. */
export function BathroomDoorAxis({roomId='',color='#356979',minX=-Infinity}:{roomId?:string;color?:string;minX?:number}) {
  if(roomId&&!['ROOM-1-02','ROOM-1-05'].includes(roomId))return null;
  const door=INTERIOR_DOORS.find(d=>d.id==='DOOR-102-105')!;
  const y=-CENTRAL_HALL_AXIS_Y_MM,x=door.wallSpanMm[0];
  return <g data-bathroom-door-axis={CENTRAL_HALL_AXIS_Y_MM} pointerEvents="none">
    <title>Os X centrálnej chodby = os otvoru aj zatvoreného krídla dverí kúpeľne · Y 7 101,5 mm</title>
    <path d={`M${Math.max(x-3200,minX)} ${y}H${x+650}`} fill="none" stroke={color} strokeWidth="10" strokeDasharray="130 35 25 35"/>
    <circle cx={x} cy={y} r="32" fill="white" stroke={color} strokeWidth="10"/>
    <text x={Math.max(x-2800,minX+150)} y={y-65} fontSize="85" fill={color} paintOrder="stroke" stroke="white" strokeWidth="24">OS CHODBY X</text>
  </g>;
}

export function AcousticWallDetail({mark}:{mark?:string}) {
  const prefix=`acoustic-detail-${useId().replaceAll(':','')}`;
  const spec=ACOUSTIC_WALL_SPECS.find(w=>w.mark===mark);
  const assembly=spec?.assembly??ACOUSTIC_ASSEMBLY, office=spec?.mark==='AK-03';
  const layers=office?[...assembly.layers].reverse():assembly.layers;
  const detailTotalMm=assembly.totalMm;
  // Dimensioned schematic: thin finish and board bands are widened for legible numbering.
  const weights=layers.map(l=>Math.max(l.thicknessMm,60));
  const weightSum=weights.reduce((sum,n)=>sum+n,0);
  const positions=weights.map((n,i)=>({x:weights.slice(0,i).reduce((sum,v)=>sum+v,0)/weightSum*300,width:n/weightSum*300}));
  const edges=[0,...positions.map(p=>p.x+p.width)];
  return <section className="pd-acoustic-detail" aria-label={`Skladba akustickej steny ${assembly.code}`}>
    <span className="pd-overline">{spec?.mark??'AK-01 / AK-02'} · SKLADBA {assembly.code}</span>
    <h3>{assembly.name}</h3>
    {spec&&<p className="pd-acoustic-location">{spec.location}</p>}
    {office&&<p className="pd-acoustic-rating"><strong>Rw ≈ 56 dB · výpočet</strong><span>Požiadavka ≥ 51 dB · predbežný odhad, presnú zostavu potvrdiť</span></p>}
    {!office&&<p className="pd-acoustic-rating"><strong>Účel: odhlučnenie miestností</strong><span>Jednovrstvové murivo 300 mm · nepriezvučnosť zatiaľ nedoložená</span></p>}
    {office&&<p className="pd-acoustic-location">Finálne zvolená H200 · od sprchy do pracovne</p>}
    <svg viewBox="0 0 360 202" role="img" aria-label={`${layers.map(l=>`${l.name} ${l.thicknessMm.toLocaleString('sk-SK')} mm`).join(', ')}. Celkom ${detailTotalMm.toLocaleString('sk-SK')} mm.`}>
      <AcousticHatches prefix={prefix}/>
      <g transform="translate(30 45)">
        {layers.map((layer,i)=><g key={layer.id}>
          <rect x={positions[i].x} width={positions[i].width} height="80" fill={`url(#${prefix}-${layer.material})`} stroke="#544b40" strokeWidth="1.2"/>
          <circle cx={positions[i].x+positions[i].width/2} cy="40" r="12" fill="white" stroke="#544b40"/>
          <text x={positions[i].x+positions[i].width/2} y="45" fontSize="14" fontWeight="700" textAnchor="middle" fill="#302c25">{i+1}</text>
        </g>)}
        <g stroke="#46515e" strokeWidth="1" fill="none">
          {edges.map(x=><path key={x} d={`M${x} -7V-25M${x-4} -14l8 -8`}/>)}
          <path d="M0 -18H300M0 88V135M300 88V135M0 128H300M-4 132l8 -8M296 132l8 -8"/>
        </g>
        {layers.map((l,i)=><text key={l.id} x={positions[i].x+positions[i].width/2} y="-26" textAnchor="middle" fontSize="14" fill="#303e50">{l.thicknessMm.toLocaleString('sk-SK')}</text>)}
        <text x="150" y="118" fontSize="16" fontWeight="700" textAnchor="middle" fill="#303e50">{detailTotalMm.toLocaleString('sk-SK')} mm</text>
      </g>
      <text x="180" y="198" textAnchor="middle" fontSize="12" fill="#657080">{office?'Vrátane omietok · bez obkladu · schéma':'Murivo 300 mm · povrchy navyše · schéma'}</text>
    </svg>
    <ol>{layers.map(layer=><li key={layer.id}><span>{layer.name}</span><strong>{layer.thicknessMm.toLocaleString('sk-SK')} mm</strong></li>)}</ol>
    <p>{assembly.finishNote}</p>
    {office&&<div className="pd-acoustic-placement"><h4>Dvere na osi chodby</h4><p>Os X: Y = 7 101,5 mm. Otvor 800 mm, krídlo 700 mm. Dvere kúpeľne posunuté o 48,5 mm; dvere a vstupný roh pracovne o 30 mm smerom k ulici.</p><p>Líce kúpeľne aj chodby Y = 6 552 mm; líce pracovne Y = 6 364,5 mm. Ostenie pri pracovni 42,5 mm, pri kúpeľni 149,5 mm. Konečnú zárubňu a obklad zosúladiť s týmito rozmermi.</p></div>}
    {office&&'junctionDetailUrl' in assembly&&<div className="pd-acoustic-placement pd-acoustic-junction"><h4>D1 · Napojenie pri zárubniach</h4><p>Pevné ostenie zostáva podkladom dverí. Predstena: podtesnený obvodový profil a súvislé oddelenie J1/J2 aj pri krátkom dorovnaní ostenia. Veľký pôdorys zobrazuje obálku; škáry sa vyhotovia podľa detailu.</p><a href={assembly.junctionDetailUrl}>Zväčšený detail D1 a montážny postup ↗</a></div>}
    <details className="pd-acoustic-notes"><summary>Konštrukčné a akustické podmienky</summary><p>{assembly.structuralNote}</p><p>{assembly.acousticNote}</p>{(!spec||spec.mark!=='AK-01')&&<p>{assembly.bathroomNote}</p>}</details>
    <div className="pd-acoustic-sources">{'productUrl' in assembly&&<a href={assembly.productUrl} target="_blank" rel="noreferrer">Vybraný výrobok ↗</a>}{'technicalSheetUrl' in assembly&&<a href={assembly.technicalSheetUrl} target="_blank" rel="noreferrer">Technický list ↗</a>}{'liningSystemUrl' in assembly&&<a href={assembly.liningSystemUrl} target="_blank" rel="noreferrer">Systém predsteny W623 ↗</a>}{'calculationSourceUrl' in assembly&&<a href={assembly.calculationSourceUrl} target="_blank" rel="noreferrer">Metodika výpočtu ↗</a>}{'scientificReportUrl' in assembly&&<a href={assembly.scientificReportUrl}>Odborné zdôvodnenie H200 ↗</a>}{'panelOrderSourceUrl' in assembly&&<a href={assembly.panelOrderSourceUrl} target="_blank" rel="noreferrer">Výskum NRC · poradie dosiek ↗</a>}</div>
  </section>;
}
