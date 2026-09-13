"use client";

import { useEffect, useRef } from "react";
import { BookOpen, ChevronDown, CircleHelp, Fullscreen, MapPin, MoreHorizontal, X } from "lucide-react";
import { INTERIOR_ROOMS } from "@/lib/twin-interior";

interface PreviewToolbarProps {
  readonly exitHref: string;
  readonly roomId: string | null;
  readonly ready: boolean;
  readonly busy: boolean;
  readonly onRoomChange: (roomId: string) => void;
  readonly onDocumentation: () => void;
  readonly onHelp: () => void;
}

export function PreviewToolbar({ exitHref, roomId, ready, busy, onRoomChange, onDocumentation, onHelp }: PreviewToolbarProps) {
  const optionsRef = useRef<HTMLDetailsElement>(null);

  useEffect(() => {
    const closeOutside = (event: PointerEvent) => {
      const options = optionsRef.current;
      if (options?.open && !options.contains(event.target as Node)) options.open = false;
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      const options = optionsRef.current;
      if (event.key !== "Escape" || !options?.open) return;
      event.preventDefault();
      event.stopPropagation();
      options.open = false;
      options.querySelector("summary")?.focus();
    };
    document.addEventListener("pointerdown", closeOutside);
    document.addEventListener("keydown", closeOnEscape, true);
    return () => {
      document.removeEventListener("pointerdown", closeOutside);
      document.removeEventListener("keydown", closeOnEscape, true);
    };
  }, []);

  const chooseOption = (action: () => void) => {
    if (optionsRef.current) {
      optionsRef.current.open = false;
      optionsRef.current.querySelector("summary")?.focus();
    }
    action();
  };

  return (
    <div className="preview-toolbar" role="group" aria-label="Ovládanie 3D náhľadu">
      <label className="preview-room glass">
        <MapPin size={17} aria-hidden="true" />
        <span className="sr-only">Prejsť do miestnosti</span>
        <select value={roomId ?? ""} disabled={!ready || busy} onChange={event => onRoomChange(event.target.value)}>
          <option value="" disabled>{ready ? "Dom a záhrada" : "Načítavam 3D…"}</option>
          {INTERIOR_ROOMS.map(room => <option key={room.id} value={room.id}>{room.number} · {room.name}</option>)}
        </select>
        <ChevronDown size={15} aria-hidden="true" />
      </label>
      <div className="preview-toolbar-actions">
        <details ref={optionsRef} className="preview-options" onBlur={event => {
          if (event.relatedTarget && !event.currentTarget.contains(event.relatedTarget as Node)) event.currentTarget.open = false;
        }}>
          <summary className="preview-more glass" aria-label="Ďalšie možnosti 3D" title="Ďalšie možnosti 3D"><MoreHorizontal size={21} aria-hidden="true" /></summary>
          <div className="preview-options-panel glass">
            <button type="button" disabled={!ready || busy} onClick={() => chooseOption(onDocumentation)}><BookOpen size={18} aria-hidden="true" />Dokumentácia</button>
            <button type="button" onClick={() => chooseOption(() => {
              if (document.fullscreenElement) void document.exitFullscreen();
              else void document.documentElement.requestFullscreen();
            })}><Fullscreen size={18} aria-hidden="true" />Celá obrazovka</button>
            <button type="button" disabled={!ready} onClick={() => chooseOption(onHelp)}><CircleHelp size={18} aria-hidden="true" />Ovládanie a skratky</button>
          </div>
        </details>
        <a className="preview-exit" href={exitHref} aria-label="Ukončiť 3D náhľad" title="Ukončiť 3D náhľad">
          <X size={20} strokeWidth={1.8} aria-hidden="true" />
          <span>Ukončiť 3D náhľad</span>
        </a>
      </div>
    </div>
  );
}
