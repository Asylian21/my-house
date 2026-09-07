"use client";

import { ArrowDown, ArrowUp, RotateCcw, RotateCw, Square } from "lucide-react";
import { useRef, type PointerEvent } from "react";
import type { WalkTravelStatus, WalkTurn } from "@/lib/twin-walk-navigation";

type Direction = 'forward' | 'backward';
interface Props {
  readonly disabled: boolean;
  readonly travel: WalkTravelStatus;
  readonly onMove: (direction: Direction, active: boolean) => void;
  readonly onStep: (direction: Direction) => void;
  readonly onTurn: (direction: WalkTurn, active: boolean) => void;
  readonly onTurnStep: (direction: WalkTurn) => void;
  readonly onStop: () => void;
}

const directions = [
  {id:'left', label:'Otočiť doľava', short:'Doľava', icon:RotateCcw, turn:true},
  {id:'forward', label:'Kráčať dopredu', short:'Dopredu', icon:ArrowUp, turn:false},
  {id:'right', label:'Otočiť doprava', short:'Doprava', icon:RotateCw, turn:true},
  {id:'backward', label:'Kráčať dozadu', short:'Dozadu', icon:ArrowDown, turn:false},
] as const;

export function WalkControls({disabled,travel,onMove,onStep,onTurn,onTurnStep,onStop}:Props) {
  const presses=useRef(new Map<number,number>());
  const hold = (event:PointerEvent<HTMLButtonElement>, active:boolean, index:number) => {
    event.stopPropagation();
    const started=presses.current.get(event.pointerId);
    if(!active&&started===undefined)return;
    if(active){ event.preventDefault(); presses.current.set(event.pointerId,event.timeStamp);event.currentTarget.setPointerCapture(event.pointerId); }
    const direction=directions[index];
    if(direction.turn) onTurn(direction.id,active);
    else onMove(direction.id,active);
    if(!active){
      presses.current.delete(event.pointerId);
      if(event.type==='pointerup'&&started!==undefined&&event.timeStamp-started<160){
        if(direction.turn)onTurnStep(direction.id);else onStep(direction.id);
      }
    }
  };
  return <div className="walk-controls glass" role="group" aria-label="Jednoduché ovládanie prechádzky">
    <p className="walk-controls-tip">Kliknite na voľnú podlahu<br/><span> alebo podržte šípky.</span></p>
    <div className="walk-controls-buttons">
      {directions.map((direction,index)=><button key={direction.id} type="button" className={`walk-control-${direction.id}`}
        disabled={disabled} aria-label={direction.label}
        onPointerDown={e=>hold(e,true,index)} onPointerUp={e=>hold(e,false,index)}
        onPointerCancel={e=>hold(e,false,index)} onLostPointerCapture={e=>hold(e,false,index)}
        onClick={e=>{e.stopPropagation();if(e.detail===0){if(direction.turn)onTurnStep(direction.id);else onStep(direction.id);}}}>
        <direction.icon size={21} aria-hidden="true"/><span>{direction.short}</span>
      </button>)}
      <button type="button" className="walk-control-stop" disabled={disabled} aria-label="Zastaviť chôdzu" onClick={onStop}>
        <Square size={16} aria-hidden="true"/><span>Stop</span>
      </button>
    </div>
    <p className="walk-controls-status" aria-live="polite">{travel==='walking'?'Kráčam na vybrané miesto…':travel==='blocked'?'Prekážka. Vyberte bližšie miesto.':'Pohľad otočíte potiahnutím.'}</p>
  </div>;
}
