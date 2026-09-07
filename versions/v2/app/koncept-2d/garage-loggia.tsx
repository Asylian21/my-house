import type { GarageEnvelope } from '@/versions/v2/lib/floor-plan-garage';
import { Box, Label, Dimension, VerticalDimension } from './plan-svg';

const m=(n:number)=>(n/1000).toLocaleString('sk-SK',{minimumFractionDigits:2,maximumFractionDigits:2});

export function GarageShell({garage}:{garage:GarageEnvelope}) {
  const {gardenRecess,loggia,shellPath}=garage;
  return <>
    {gardenRecess&&<Box r={loggia.bounds} className="fp-terrace fp-garden-recess"/>}
    <path className="fp-shell" d={shellPath}/>
    {gardenRecess&&<g className="fp-loggia-structure">
      <Box r={loggia.pier} className="fp-shell fp-loggia-pier"><title>Rohový stĺpik 1,00 × 0,50 m</title></Box>
      <Box r={loggia.westReturn} className="fp-shell"/>
      <path className="fp-loggia-roof" d={`M${loggia.bounds.x0},${-loggia.westReturn.y1}V${-loggia.bounds.y1}H${loggia.bounds.x1}`}><title>Hrana zastrešenia nad otvoreným zárezom</title></path>
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
