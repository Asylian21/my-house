import { useId } from 'react';
import { ACOUSTIC_ASSEMBLY, ACOUSTIC_WALL_SPECS } from '@/lib/acoustic-walls';
import { ACTIVE_ACOUSTIC_WALLS } from '@/lib/twin-interior';

/** Common symbols in model millimetres, readable in colour and monochrome. */
export function AcousticHatches({prefix='ak',mono=false}:{prefix?:string;mono?:boolean}) {
  return <defs>
    <pattern id={`${prefix}-masonry`} width="80" height="80" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="80" height="80" fill={mono?'#fff':'#e7d2c0'}/><path d="M0 0V80" stroke={mono?'#333':'#805b47'} strokeWidth="9"/>
    </pattern>
    <pattern id={`${prefix}-mineral-wool`} width="100" height="120" patternUnits="userSpaceOnUse">
      <rect width="100" height="120" fill={mono?'#fff':'#f4ebc7'}/><path d="M50 0C0 0 0 60 50 60S100 120 50 120" fill="none" stroke={mono?'#333':'#847339'} strokeWidth="8"/>
    </pattern>
  </defs>;
}

export function AcousticWallMarks({roomId='',fontSize=110,color='#58492f'}:{roomId?:string;fontSize?:number;color?:string}) {
  return <g className="pd-acoustic-marks">
    {ACTIVE_ACOUSTIC_WALLS.filter(w=>!roomId||w.rooms.some(id=>id===roomId)).map(w=>{
      // AK-02's midpoint is occupied by the WC; place its callout in the clear
      // band between the toilet and bath, leaving sanitary symbols readable.
      const x=w.rectMm.x0-350, y=w.mark==='AK-02'?-(w.rectMm.y0+1050):-(w.rectMm.y0+w.rectMm.y1)/2;
      return <g key={w.mark} data-item={w.mark} data-acoustic-mark={w.mark}>
        <title>{`${w.mark} · ${w.location} · SA30 · 100 / 100 / 100 mm`}</title>
        <path d={`M${x+fontSize*1.8} ${y}H${w.rectMm.x0+50}`} stroke={color} strokeWidth="12"/>
        <rect x={x-fontSize*1.9} y={y-fontSize*.8} width={fontSize*3.8} height={fontSize*1.6} rx="20" fill="white" stroke={color} strokeWidth="10"/>
        <text x={x} y={y+fontSize*.35} textAnchor="middle" fontSize={fontSize} fontWeight="700" fill={color}>{w.mark}</text>
      </g>;
    })}
  </g>;
}

export function AcousticWallDetail({mark}:{mark?:string}) {
  const prefix=`acoustic-detail-${useId().replaceAll(':','')}`;
  const spec=ACOUSTIC_WALL_SPECS.find(w=>w.mark===mark);
  return <section className="pd-acoustic-detail" aria-label="Skladba akustickej steny SA30">
    <span className="pd-overline">{spec?.mark??'AK-01 / AK-02'} · SKLADBA SA30</span>
    <h3>Dvojplášťová akustická priečka</h3>
    {spec&&<p className="pd-acoustic-location">{spec.location}</p>}
    <svg viewBox="0 0 360 202" role="img" aria-label="Rez stenou: tehla 100 mm, minerálna vata 100 mm, tehla 100 mm. Celkom 300 mm bez povrchových úprav.">
      <AcousticHatches prefix={prefix}/>
      <g transform="translate(30 45)">
        {ACOUSTIC_ASSEMBLY.layers.map((layer,i)=><g key={layer.id}>
          <rect x={i*100} width="100" height="80" fill={`url(#${prefix}-${layer.material})`} stroke="#544b40" strokeWidth="1.2"/>
          <circle cx={i*100+50} cy="40" r="12" fill="white" stroke="#544b40"/>
          <text x={i*100+50} y="45" fontSize="14" fontWeight="700" textAnchor="middle" fill="#302c25">{i+1}</text>
        </g>)}
        <g stroke="#46515e" strokeWidth="1" fill="none"><path d="M0 -7V-25M100 -7V-25M200 -7V-25M300 -7V-25M0 -18H300M0 88V135M300 88V135M0 128H300"/>
          {[0,100,200,300].map(x=><path key={x} d={`M${x-4} -14l8 -8`}/>)}<path d="M-4 132l8 -8M296 132l8 -8"/>
        </g>
        {[50,150,250].map(x=><text key={x} x={x} y="-26" textAnchor="middle" fontSize="14" fill="#303e50">100</text>)}
        <text x="150" y="118" fontSize="16" fontWeight="700" textAnchor="middle" fill="#303e50">300 mm</text>
      </g>
      <text x="180" y="198" textAnchor="middle" fontSize="12" fill="#657080">Bez omietok a obkladov · schematický rez</text>
    </svg>
    <ol>{ACOUSTIC_ASSEMBLY.layers.map(layer=><li key={layer.id}><span>{layer.name}</span><strong>{layer.thicknessMm} mm</strong></li>)}</ol>
    <p>{ACOUSTIC_ASSEMBLY.finishNote}</p>
    <details className="pd-acoustic-notes"><summary>Konštrukčné a akustické poznámky</summary><p>{ACOUSTIC_ASSEMBLY.structuralNote}</p><p>{ACOUSTIC_ASSEMBLY.acousticNote}</p>{(!spec||spec.mark==='AK-02')&&<p>{ACOUSTIC_ASSEMBLY.bathroomNote}</p>}</details>
    <div className="pd-acoustic-sources"><a href={ACOUSTIC_ASSEMBLY.productUrl} target="_blank" rel="noreferrer">Vybraný výrobok ↗</a><a href={ACOUSTIC_ASSEMBLY.technicalSheetUrl} target="_blank" rel="noreferrer">Technický list ↗</a></div>
  </section>;
}
