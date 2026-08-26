import type { LayerId } from "./twin-site";
import type { WalkAvatarId } from "./twin-avatar";
import type { NavigationMode } from "./twin-viewport-contract";
import type { WorkspaceMode } from "./twin-ui-mode";

/**
 * Camera preset identifiers are duplicated here on purpose: the command model
 * has to stay engine-free like the rest of `lib/`, so it must not reach into
 * the Babylon module. The union is identical to `CameraPreset`, which keeps the
 * two structurally assignable and lets TypeScript catch any future drift.
 */
export const CAMERA_PRESET_IDS = [
  "garden",
  "street",
  "axonometric",
  "top",
  "parcels",
  "focus",
] as const;

export type CameraPresetId = (typeof CAMERA_PRESET_IDS)[number];

export type CommandIcon =
  | "garden"
  | "street"
  | "axonometric"
  | "plan"
  | "parcels"
  | "focus"
  | "orbit"
  | "flight"
  | "walk"
  | "room"
  | "avatar"
  | "layer"
  | "documentation"
  | "experience"
  | "recenter"
  | "eye"
  | "help"
  | "fullscreen";

export interface CameraPresetOption {
  readonly id: CameraPresetId;
  readonly label: string;
  readonly detail: string;
  readonly shortcut: string;
  readonly icon: CommandIcon;
  /** Focus follows the current selection and has no meaning of its own. */
  readonly contextual: boolean;
}

export const CAMERA_PRESETS = [
  {
    id: "garden",
    label: "Záhrada",
    detail: "Pohľad z terasy do otvoreného L-dvora",
    shortcut: "4",
    icon: "garden",
    contextual: false,
  },
  {
    id: "street",
    label: "Od ulice",
    detail: "Pohľad chodca z komunikácie 6012/1",
    shortcut: "3",
    icon: "street",
    contextual: false,
  },
  {
    id: "axonometric",
    label: "Axonometria",
    detail: "Celková hmota domu nad parcelou",
    shortcut: "1",
    icon: "axonometric",
    contextual: false,
  },
  {
    id: "top",
    label: "Pôdorys",
    detail: "Kolmý pohľad na parcelu a strechu",
    shortcut: "2",
    icon: "plan",
    contextual: false,
  },
  {
    id: "parcels",
    label: "Parcely",
    detail: "Prehľad susedných parciel v rade",
    shortcut: "5",
    icon: "parcels",
    contextual: false,
  },
  {
    id: "focus",
    label: "Zamerať výber",
    detail: "Priblíži práve vybraný objekt modelu",
    shortcut: "F",
    icon: "focus",
    contextual: true,
  },
] as const satisfies readonly CameraPresetOption[];

export interface MovementOption {
  readonly id: NavigationMode;
  readonly label: string;
  readonly detail: string;
  readonly shortcut: string;
  readonly icon: CommandIcon;
}

export const MOVEMENT_OPTIONS = [
  {
    id: "orbit",
    label: "Obeh",
    detail: "Otáčanie a priblíženie okolo modelu",
    shortcut: "Esc",
    icon: "orbit",
  },
  {
    id: "flight",
    label: "Prelet",
    detail: "Voľná kamera nad parcelou · WASD a Q/E",
    shortcut: "H",
    icon: "flight",
  },
  {
    id: "walk",
    label: "Prechádzka",
    detail: "Chôdza s postavou po dome a záhrade",
    shortcut: "G",
    icon: "walk",
  },
] as const satisfies readonly MovementOption[];

export function movementOption(id: NavigationMode): MovementOption {
  return MOVEMENT_OPTIONS.find((option) => option.id === id) ?? MOVEMENT_OPTIONS[0];
}

export function cameraPresetOption(id: CameraPresetId): CameraPresetOption {
  return CAMERA_PRESETS.find((option) => option.id === id) ?? CAMERA_PRESETS[0];
}

export type CommandGroup =
  | "workspace"
  | "movement"
  | "view"
  | "room"
  | "avatar"
  | "layer"
  | "system";

export const COMMAND_GROUP_ORDER = [
  "movement",
  "view",
  "room",
  "avatar",
  "layer",
  "workspace",
  "system",
] as const satisfies readonly CommandGroup[];

export const COMMAND_GROUP_LABELS: Readonly<Record<CommandGroup, string>> = {
  workspace: "Režim",
  movement: "Pohyb",
  view: "Pohľady",
  room: "Miestnosti",
  avatar: "Postava",
  layer: "Vrstvy",
  system: "Ostatné",
};

export type CommandAction =
  | { readonly kind: "workspace"; readonly workspace: WorkspaceMode }
  | { readonly kind: "movement"; readonly movement: NavigationMode }
  | { readonly kind: "preset"; readonly preset: CameraPresetId }
  | { readonly kind: "room"; readonly roomId: string }
  | { readonly kind: "avatar"; readonly avatarId: WalkAvatarId }
  | { readonly kind: "layer"; readonly layer: LayerId }
  | { readonly kind: "recenter" }
  | { readonly kind: "walk-view"; readonly view: "first" | "third" }
  | { readonly kind: "fullscreen" }
  | { readonly kind: "help" };

export interface TwinCommand {
  readonly id: string;
  readonly group: CommandGroup;
  readonly label: string;
  readonly detail: string;
  readonly icon: CommandIcon;
  readonly action: CommandAction;
  readonly shortcut?: string;
  /** Extra spellings a person may type; never rendered. */
  readonly keywords?: readonly string[];
  /** Rendered as the current value of a toggle or exclusive choice. */
  readonly active?: boolean;
}

export interface CommandRoom {
  readonly id: string;
  readonly number: string;
  readonly name: string;
}

export interface CommandAvatar {
  readonly id: WalkAvatarId;
  readonly label: string;
  readonly tagline: string;
}

export interface CommandLayer {
  readonly id: LayerId;
  readonly label: string;
  readonly source: string;
}

export interface CommandContext {
  readonly workspace: WorkspaceMode;
  readonly movement: NavigationMode;
  readonly walkView: "first" | "third";
  readonly avatarId: WalkAvatarId;
  readonly rooms: readonly CommandRoom[];
  readonly avatars: readonly CommandAvatar[];
  readonly layers: readonly CommandLayer[];
  readonly layerVisibility: Readonly<Record<LayerId, boolean>>;
  /** Focus is offered only when something is actually selected. */
  readonly hasSelection: boolean;
}

/**
 * One registry feeds both the palette and the contextual dock, so a control can
 * never exist in one surface and quietly go missing from the other.
 */
export function buildCommands(context: CommandContext): readonly TwinCommand[] {
  const commands: TwinCommand[] = [];

  for (const option of MOVEMENT_OPTIONS) {
    commands.push({
      id: `movement:${option.id}`,
      group: "movement",
      label: option.label,
      detail: option.detail,
      icon: option.icon,
      shortcut: option.shortcut,
      action: { kind: "movement", movement: option.id },
      active: context.movement === option.id,
      keywords: ["pohyb", "kamera", "navigacia"],
    });
  }

  if (context.movement === "walk") {
    const firstPerson = context.walkView === "first";
    commands.push({
      id: "walk-view",
      group: "movement",
      label: firstPerson ? "Pohľad tretej osoby" : "Pohľad z očí",
      detail: firstPerson
        ? "Kamera sa vráti za postavu"
        : "Kamera sa presunie do výšky očí postavy",
      icon: "eye",
      shortcut: "V",
      action: { kind: "walk-view", view: firstPerson ? "third" : "first" },
      keywords: ["prvá osoba", "third person", "pohlad"],
    });
    commands.push({
      id: "recenter",
      group: "movement",
      label: "Vystrediť kameru",
      detail: "Zarovná kameru za postavu a uvoľní zaseknutie",
      icon: "recenter",
      shortcut: "R",
      action: { kind: "recenter" },
      keywords: ["vyslobodit", "reset", "zaseknuta"],
    });
  }

  for (const preset of CAMERA_PRESETS) {
    if (preset.contextual && !context.hasSelection) continue;
    commands.push({
      id: `preset:${preset.id}`,
      group: "view",
      label: preset.label,
      detail: preset.detail,
      icon: preset.icon,
      shortcut: preset.shortcut,
      action: { kind: "preset", preset: preset.id },
      keywords: ["pohlad", "kamera", "preset"],
    });
  }

  for (const room of context.rooms) {
    commands.push({
      id: `room:${room.id}`,
      group: "room",
      label: `${room.number} · ${room.name}`,
      detail: "Prejsť do miestnosti a pokračovať pešo",
      icon: "room",
      action: { kind: "room", roomId: room.id },
      keywords: ["miestnost", "izba", room.number],
    });
  }

  for (const avatar of context.avatars) {
    commands.push({
      id: `avatar:${avatar.id}`,
      group: "avatar",
      label: avatar.label,
      detail: `${avatar.tagline} · postava prechádzky`,
      icon: "avatar",
      action: { kind: "avatar", avatarId: avatar.id },
      active: context.avatarId === avatar.id,
      keywords: ["postava", "avatar", "figura"],
    });
  }

  for (const layer of context.layers) {
    const visible = context.layerVisibility[layer.id];
    commands.push({
      id: `layer:${layer.id}`,
      group: "layer",
      label: layer.label,
      detail: `${visible ? "Skryť" : "Zobraziť"} vrstvu · ${layer.source}`,
      icon: "layer",
      action: { kind: "layer", layer: layer.id },
      active: visible,
      keywords: ["vrstva", "viditelnost", "zobrazit", "skryt"],
    });
  }

  for (const option of [
    { id: "documentation", label: "Dokumentácia" },
    { id: "experience", label: "Zážitok" },
  ] as const) {
    commands.push({
      id: `workspace:${option.id}`,
      group: "workspace",
      label: `Režim ${option.label}`,
      detail:
        option.id === "documentation"
          ? "Výkres, parametre a dôkazová stopa"
          : "Prehliadka domu, záhrady a interiéru",
      icon: option.id,
      shortcut: "M",
      action: { kind: "workspace", workspace: option.id },
      active: context.workspace === option.id,
      keywords: ["rezim", "mode", "prepnut"],
    });
  }

  commands.push({
    id: "fullscreen",
    group: "system",
    label: "Celá obrazovka",
    detail: "Prepne prehliadač do režimu celej obrazovky",
    icon: "fullscreen",
    action: { kind: "fullscreen" },
    keywords: ["fullscreen", "cela obrazovka"],
  });
  commands.push({
    id: "help",
    group: "system",
    label: "Ovládanie a skratky",
    detail: "Prehľad klávesov a gest",
    icon: "help",
    shortcut: "?",
    action: { kind: "help" },
    keywords: ["pomoc", "help", "skratky", "klavesy"],
  });

  return commands;
}

/**
 * Slovak users type without diacritics far more often than with them, so search
 * folds the query and the haystack to a bare Latin form before comparing.
 */
export function normalizeSearchText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("sk");
}

function haystack(command: TwinCommand): {
  readonly label: string;
  readonly rest: string;
} {
  return {
    label: normalizeSearchText(command.label),
    rest: normalizeSearchText(
      `${command.detail} ${(command.keywords ?? []).join(" ")} ${
        COMMAND_GROUP_LABELS[command.group]
      }`,
    ),
  };
}

/**
 * Relevance rather than plain filtering: a label prefix beats a word start,
 * which beats an incidental hit in the description. Every whitespace-separated
 * token has to land somewhere, so "1.03 kuchyn" narrows instead of widening.
 */
export function scoreCommand(command: TwinCommand, query: string): number {
  const tokens = normalizeSearchText(query).split(/\s+/).filter(Boolean);
  if (tokens.length === 0) return 0;
  const { label, rest } = haystack(command);
  let score = 0;
  for (const token of tokens) {
    if (label.startsWith(token)) {
      score += 100;
      continue;
    }
    if (new RegExp(`(^|[\\s·.\\-])${escapeToken(token)}`).test(label)) {
      score += 70;
      continue;
    }
    if (label.includes(token)) {
      score += 45;
      continue;
    }
    if (rest.includes(token)) {
      score += 18;
      continue;
    }
    return -1;
  }
  return score;
}

function escapeToken(token: string): string {
  return token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function filterCommands(
  commands: readonly TwinCommand[],
  query: string,
): readonly TwinCommand[] {
  if (!query.trim()) return commands;
  return commands
    .map((command, index) => ({
      command,
      index,
      score: scoreCommand(command, query),
    }))
    .filter((entry) => entry.score >= 0)
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .map((entry) => entry.command);
}

export interface CommandSection {
  readonly group: CommandGroup;
  readonly label: string;
  readonly commands: readonly TwinCommand[];
}

/**
 * Grouping is kept out of the component so the palette renders exactly what the
 * model decided, including the rule that a search collapses the group order
 * into pure relevance.
 */
export function groupCommands(
  commands: readonly TwinCommand[],
  searching: boolean,
): readonly CommandSection[] {
  if (searching) {
    return commands.length
      ? [{ group: "system", label: "Výsledky", commands }]
      : [];
  }
  const sections: CommandSection[] = [];
  for (const group of COMMAND_GROUP_ORDER) {
    const matching = commands.filter((command) => command.group === group);
    if (matching.length === 0) continue;
    sections.push({
      group,
      label: COMMAND_GROUP_LABELS[group],
      commands: matching,
    });
  }
  return sections;
}
