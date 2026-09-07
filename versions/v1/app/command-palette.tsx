"use client";

import {
  Command as CommandGlyph,
  CornerDownLeft,
  Search,
} from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { filterCommands, groupCommands, type TwinCommand } from "@/versions/v1/lib/twin-commands";

import { COMMAND_ICONS } from "./hud-icons";

interface CommandPaletteProps {
  readonly commands: readonly TwinCommand[];
  readonly onRun: (command: TwinCommand) => void;
  readonly onClose: () => void;
}

/**
 * One searchable surface for everything the model can do. It exists so the
 * scene can stay empty: rooms, camera presets, layers and characters are a
 * keystroke away instead of thirteen permanent buttons over the render.
 *
 * The palette is mounted only while it is open, so the query and the highlight
 * start clean every time without a reset pass.
 */
export function CommandPalette({
  commands,
  onRun,
  onClose,
}: CommandPaletteProps) {
  const listId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState("");
  const [highlight, setHighlight] = useState(0);

  const searching = query.trim().length > 0;
  const sections = useMemo(
    () => groupCommands(filterCommands(commands, query), searching),
    [commands, query, searching],
  );
  const flat = useMemo(
    () => sections.flatMap((section) => section.commands),
    [sections],
  );
  /** Keyboard position of every option, so grouping stays a visual concern. */
  const positions = useMemo(
    () => new Map(flat.map((command, index) => [command.id, index])),
    [flat],
  );

  // Typing shrinks the list under the cursor, so the highlight is clamped on
  // read rather than corrected afterwards.
  const active = highlight < flat.length ? highlight : 0;

  useEffect(() => {
    const frame = requestAnimationFrame(() => inputRef.current?.focus());
    return () => cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    listRef.current
      ?.querySelector<HTMLElement>('[data-highlighted="true"]')
      ?.scrollIntoView({ block: "nearest" });
  }, [active, flat]);

  const move = (delta: number) => {
    if (flat.length === 0) return;
    setHighlight((current) => {
      const from = current < flat.length ? current : 0;
      return (from + delta + flat.length) % flat.length;
    });
  };

  const run = (command: TwinCommand | undefined) => {
    if (!command) return;
    onRun(command);
    onClose();
  };

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      move(1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      move(-1);
    } else if (event.key === "Home") {
      event.preventDefault();
      setHighlight(0);
    } else if (event.key === "End") {
      event.preventDefault();
      setHighlight(Math.max(0, flat.length - 1));
    } else if (event.key === "Enter") {
      event.preventDefault();
      run(flat[active]);
    } else if (event.key === "Escape") {
      event.preventDefault();
      onClose();
    }
  };

  return (
    <div
      className="palette-scrim"
      role="presentation"
      onPointerDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <div
        className="palette"
        role="dialog"
        aria-modal="true"
        aria-label="Príkazy modelu"
        onKeyDown={onKeyDown}
      >
        <div className="palette-field">
          <Search size={18} aria-hidden="true" />
          <input
            ref={inputRef}
            type="text"
            role="combobox"
            aria-expanded="true"
            aria-controls={listId}
            aria-autocomplete="list"
            aria-activedescendant={
              flat[active] ? `${listId}-${flat[active].id}` : undefined
            }
            aria-label="Hľadať príkaz, miestnosť alebo pohľad"
            placeholder="Hľadať miestnosť, pohľad, vrstvu…"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setHighlight(0);
            }}
          />
          <kbd className="key">Esc</kbd>
        </div>

        <div className="palette-list" id={listId} role="listbox" ref={listRef}>
          {sections.length === 0 && (
            <p className="palette-empty">Nič sa nenašlo. Skúste iný výraz.</p>
          )}
          {sections.map((section) => (
            <div
              key={section.group}
              className="palette-section"
              role="group"
              aria-label={section.label}
            >
              <div className="palette-section-label" aria-hidden="true">
                {section.label}
              </div>
              {section.commands.map((command) => {
                const position = positions.get(command.id) ?? 0;
                const Icon = COMMAND_ICONS[command.icon];
                return (
                  <button
                    key={command.id}
                    type="button"
                    role="option"
                    id={`${listId}-${command.id}`}
                    className="palette-option"
                    aria-selected={position === active}
                    data-highlighted={position === active}
                    data-active={command.active ?? false}
                    tabIndex={-1}
                    onPointerDown={(event) => event.preventDefault()}
                    onPointerMove={() => setHighlight(position)}
                    onClick={() => run(command)}
                  >
                    <span className="palette-option-icon" aria-hidden="true">
                      <Icon size={16} strokeWidth={1.8} />
                    </span>
                    <span className="palette-option-copy">
                      <strong>{command.label}</strong>
                      <small>{command.detail}</small>
                    </span>
                    <span className="palette-option-meta">
                      {command.active && (
                        <span
                          className="palette-active-dot"
                          aria-label="aktívne"
                        />
                      )}
                      {command.shortcut && (
                        <kbd className="key">{command.shortcut}</kbd>
                      )}
                    </span>
                  </button>
                );
              })}
            </div>
          ))}
        </div>

        <div className="palette-footer" aria-hidden="true">
          <span>
            <CommandGlyph size={11} /> K otvorí príkazy
          </span>
          <span>
            <CornerDownLeft size={11} /> spustiť
          </span>
          <span>↑ ↓ pohyb v zozname</span>
        </div>
      </div>
    </div>
  );
}
