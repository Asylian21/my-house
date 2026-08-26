import { describe, expect, it } from "vitest";

import type { CameraPreset } from "../lib/babylon-scene";
import { WALK_AVATARS } from "../lib/twin-avatar";
import { DEFAULT_LAYER_VISIBILITY, LAYERS } from "../lib/twin-site";
import {
  CAMERA_PRESETS,
  CAMERA_PRESET_IDS,
  COMMAND_GROUP_LABELS,
  COMMAND_GROUP_ORDER,
  MOVEMENT_OPTIONS,
  buildCommands,
  cameraPresetOption,
  filterCommands,
  groupCommands,
  movementOption,
  normalizeSearchText,
  scoreCommand,
  type CameraPresetId,
  type CommandContext,
  type TwinCommand,
} from "../lib/twin-commands";

/**
 * The palette must never drift from the engine: if a preset is added to or
 * renamed in `babylon-scene`, these two assignments stop compiling.
 */
const presetIdIsCameraPreset: CameraPreset = "focus" satisfies CameraPresetId;
const cameraPresetIsPresetId: CameraPresetId = "focus" satisfies CameraPreset;

const context = (overrides: Partial<CommandContext> = {}): CommandContext => ({
  workspace: "experience",
  movement: "orbit",
  walkView: "third",
  avatarId: "michelle",
  rooms: [
    { id: "ROOM-1-03", number: "1.03", name: "Obývacia izba s kuchyňou" },
    { id: "ROOM-1-06", number: "1.06", name: "WC" },
  ],
  avatars: WALK_AVATARS.map((avatar) => ({
    id: avatar.id,
    label: avatar.label,
    tagline: avatar.tagline,
  })),
  layers: LAYERS.map((layer) => ({
    id: layer.id,
    label: layer.label,
    source: layer.source,
  })),
  layerVisibility: DEFAULT_LAYER_VISIBILITY,
  hasSelection: false,
  ...overrides,
});

const byId = (commands: readonly TwinCommand[], id: string) =>
  commands.find((command) => command.id === id);

describe("command registry", () => {
  it("keeps the preset union aligned with the Babylon camera presets", () => {
    expect(presetIdIsCameraPreset).toBe(cameraPresetIsPresetId);
    expect(CAMERA_PRESETS.map((preset) => preset.id).sort()).toEqual(
      [...CAMERA_PRESET_IDS].sort(),
    );
  });

  it("issues a unique id for every command, so palette keys never collide", () => {
    const commands = buildCommands(context({ movement: "walk", hasSelection: true }));
    const ids = commands.map((command) => command.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("gives every command a label, a description and a known group", () => {
    for (const command of buildCommands(context())) {
      expect(command.label.length).toBeGreaterThan(0);
      expect(command.detail.length).toBeGreaterThan(0);
      expect(COMMAND_GROUP_ORDER).toContain(command.group);
      expect(COMMAND_GROUP_LABELS[command.group].length).toBeGreaterThan(0);
    }
  });

  it("carries every room, character and layer into the palette", () => {
    const commands = buildCommands(context());
    expect(byId(commands, "room:ROOM-1-06")?.label).toBe("1.06 · WC");
    for (const avatar of WALK_AVATARS) {
      expect(byId(commands, `avatar:${avatar.id}`)).toBeDefined();
    }
    for (const layer of LAYERS) {
      expect(byId(commands, `layer:${layer.id}`)).toBeDefined();
    }
  });

  it("offers focus only when there is something to focus on", () => {
    expect(byId(buildCommands(context()), "preset:focus")).toBeUndefined();
    expect(
      byId(buildCommands(context({ hasSelection: true })), "preset:focus"),
    ).toBeDefined();
  });

  it("adds the walking-only controls only while walking", () => {
    const orbiting = buildCommands(context());
    expect(byId(orbiting, "walk-view")).toBeUndefined();
    expect(byId(orbiting, "recenter")).toBeUndefined();

    const walking = buildCommands(context({ movement: "walk" }));
    expect(byId(walking, "recenter")).toBeDefined();
    expect(byId(walking, "walk-view")?.action).toEqual({
      kind: "walk-view",
      view: "first",
    });
  });

  it("labels the eye-level toggle by what it will do, not by the state", () => {
    const fromEyes = buildCommands(
      context({ movement: "walk", walkView: "first" }),
    );
    expect(byId(fromEyes, "walk-view")?.label).toBe("Pohľad tretej osoby");
    expect(byId(fromEyes, "walk-view")?.action).toEqual({
      kind: "walk-view",
      view: "third",
    });
  });

  it("marks the current mode, movement, character and layer as active", () => {
    const commands = buildCommands(
      context({ workspace: "documentation", movement: "flight", avatarId: "vanguard" }),
    );
    expect(byId(commands, "workspace:documentation")?.active).toBe(true);
    expect(byId(commands, "workspace:experience")?.active).toBe(false);
    expect(byId(commands, "movement:flight")?.active).toBe(true);
    expect(byId(commands, "movement:orbit")?.active).toBe(false);
    expect(byId(commands, "avatar:vanguard")?.active).toBe(true);
    expect(byId(commands, "layer:cadastre")?.active).toBe(true);
    expect(byId(commands, "layer:water")?.active).toBe(false);
  });

  it("describes a layer command by the change it makes", () => {
    const commands = buildCommands(context());
    expect(byId(commands, "layer:cadastre")?.detail).toMatch(/^Skryť/);
    expect(byId(commands, "layer:water")?.detail).toMatch(/^Zobraziť/);
  });

  it("always reaches help and fullscreen, whatever the mode", () => {
    for (const movement of ["orbit", "flight", "walk"] as const) {
      const commands = buildCommands(context({ movement }));
      expect(byId(commands, "help")?.shortcut).toBe("?");
      expect(byId(commands, "fullscreen")).toBeDefined();
    }
  });

  it("keeps the movement and preset shortcuts on the commands themselves", () => {
    const commands = buildCommands(context({ hasSelection: true }));
    for (const option of MOVEMENT_OPTIONS) {
      expect(byId(commands, `movement:${option.id}`)?.shortcut).toBe(
        option.shortcut,
      );
    }
    for (const preset of CAMERA_PRESETS) {
      expect(byId(commands, `preset:${preset.id}`)?.shortcut).toBe(
        preset.shortcut,
      );
    }
  });

  it("resolves options by id and falls back instead of returning nothing", () => {
    expect(movementOption("walk").label).toBe("Prechádzka");
    expect(cameraPresetOption("parcels").label).toBe("Parcely");
  });
});

describe("command search", () => {
  const commands = buildCommands(context({ hasSelection: true }));

  it("folds Slovak diacritics so people can type without them", () => {
    expect(normalizeSearchText("Záhrada · Pôdorys")).toBe("zahrada · podorys");
    const ids = filterCommands(commands, "zahrada").map((command) => command.id);
    expect(ids).toContain("preset:garden");
  });

  it("finds a room by its number", () => {
    const ids = filterCommands(commands, "1.03").map((command) => command.id);
    expect(ids[0]).toBe("room:ROOM-1-03");
  });

  it("requires every typed word to land somewhere", () => {
    expect(filterCommands(commands, "kuchyn").length).toBeGreaterThan(0);
    expect(filterCommands(commands, "kuchyn vodovod")).toHaveLength(0);
  });

  it("ranks a label prefix above an incidental hit in the description", () => {
    const prefix = byId(commands, "preset:garden");
    const incidental = byId(commands, "movement:orbit");
    expect(prefix && incidental).toBeTruthy();
    expect(scoreCommand(prefix!, "zahrada")).toBeGreaterThan(
      scoreCommand(incidental!, "kamera"),
    );
  });

  it("rejects a command when a token matches nothing", () => {
    expect(scoreCommand(commands[0], "qwertz")).toBeLessThan(0);
  });

  it("returns the full registry for an empty query", () => {
    expect(filterCommands(commands, "   ")).toBe(commands);
  });
});

describe("command grouping", () => {
  it("orders the sections by how often they are reached", () => {
    const sections = groupCommands(
      buildCommands(context({ hasSelection: true })),
      false,
    );
    const order = sections.map((section) => section.group);
    expect(order).toEqual(
      COMMAND_GROUP_ORDER.filter((group) => order.includes(group)),
    );
    expect(order[0]).toBe("movement");
  });

  it("collapses into pure relevance while searching", () => {
    const results = filterCommands(buildCommands(context()), "vrstv");
    const sections = groupCommands(results, true);
    expect(sections).toHaveLength(1);
    expect(sections[0].label).toBe("Výsledky");
    expect(sections[0].commands).toBe(results);
  });

  it("renders nothing rather than empty headings when nothing matches", () => {
    expect(groupCommands([], true)).toHaveLength(0);
    expect(groupCommands([], false)).toHaveLength(0);
  });
});
