import type { GarageEnvelope } from '@/lib/floor-plan-garage';
import { Box, Label, Dimension, VerticalDimension } from './plan-svg';

const m=(n:number)=>(n/1000).toLocaleString('sk-SK',{minimumFractionDigits:2,maximumFractionDigits:2});

export function GarageShell({garage}:{garage:GarageEnvelope}) {
  const {gardenRecess,loggia,shellPath,insulation}=garage;
  return <>
    {gardenRecess&&<Box r={loggia.bounds} className="fp-terrace fp-garden-recess"/>}
    <path className="fp-shell" d={shellPath}/>
    {/* Real wall build-up: the shell reads as 300 mm masonry, the outer 200 mm as contact insulation. Solid piers are drawn over it. */}
    <g className="fp-insulation-layer">
      <defs><pattern id="fp-insulation" width="140" height="140" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><rect width="140" height="140" className="fp-insulation-ground"/><path d="M0 0V140" className="fp-insulation-hatch"/></pattern></defs>
      {insulation.map((r,i)=><Box key={i} r={r} className="fp-insulation"/>)}
      <title>Kontaktné zateplenie 200 mm na nosnom murive 300 mm</title>
    </g>
    {gardenRecess&&<g className="fp-loggia-structure">
      <path d={loggia.pierPath} className="fp-shell fp-loggia-pier"><title>Rohová podpera do L · 2,00 × 1,00 m · hrúbka 0,50 m bez zateplenia</title></path>
      <path className="fp-loggia-roof" d={`M${loggia.bounds.x0},${-loggia.bounds.y0}V${-loggia.bounds.y1}H${loggia.bounds.x1}`}><title>Hrana zastrešenia nad otvoreným zárezom</title></path>
    </g>}
  </>;
}

export function GarageLoggiaLabel({garage,dimensions}:{garage:GarageEnvelope;dimensions:boolean}) {
  const {gardenRecess,loggia}=garage;
  if(!gardenRecess)return null;
  return <g className="fp-loggia-label">
    <Label x={8540} y={10330}>Krytý zárez</Label>
    <Label x={8540} y={10070} className="fp-loggia-subtitle">otvorený do záhrady</Label>
    {dimensions&&<>
      <Dimension x0={loggia.openingStart} x1={loggia.bounds.x1} y={11420} label={`${m(loggia.openingWidth)} m otvor`}/>
      <VerticalDimension x={6800} y0={loggia.bounds.y0} y1={loggia.bounds.y1} label={`${m(loggia.depth)} m`}/>
    </>}
  </g>;
}
