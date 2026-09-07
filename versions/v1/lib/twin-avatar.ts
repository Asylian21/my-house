export const WALK_AVATAR_IDS = ["michelle", "vanguard", "robot"] as const;

export type WalkAvatarId = (typeof WALK_AVATAR_IDS)[number];
export type WalkAvatarIcon = "person" | "shield" | "robot";

export interface WalkAvatarOption {
  readonly id: WalkAvatarId;
  readonly label: string;
  readonly tagline: string;
  readonly description: string;
  readonly icon: WalkAvatarIcon;
  readonly modelUrl: string;
  readonly diffuseUrl?: string;
  readonly modelScale: number;
  readonly headingOffsetRad: number;
  readonly clips: {
    readonly idle: string;
    readonly walk: string;
    readonly run: string;
  };
}

export const DEFAULT_WALK_AVATAR_ID: WalkAvatarId = "michelle";
export const WALK_AVATAR_STORAGE_KEY = "dom-6012-26.walk-avatar";

/**
 * The visual rigs are deliberately separate from the walker's collider,
 * movement and chase camera. Switching a choice must therefore never alter
 * the player's pose or the architectural collision contract.
 */
export const WALK_AVATARS = [
  {
    id: "michelle",
    label: "Michelle",
    tagline: "Pôvodná",
    description: "Pôvodná civilná postava so svetlým vzhľadom.",
    icon: "person",
    modelUrl: "/v1-assets/avatar/avatar.glb",
    diffuseUrl: "/v1-assets/avatar/michelle-light-diffuse.png",
    modelScale: 1,
    headingOffsetRad: 0,
    clips: { idle: "Idle", walk: "Walk", run: "Run" },
  },
  {
    id: "vanguard",
    label: "Vanguard",
    tagline: "Prieskumník",
    description: "Športový prieskumník v modernom taktickom oblečení.",
    icon: "shield",
    modelUrl: "/v1-assets/avatar/vanguard.glb",
    modelScale: 1,
    headingOffsetRad: Math.PI,
    clips: { idle: "Idle", walk: "Walk", run: "Run" },
  },
  {
    id: "robot",
    label: "Robo",
    tagline: "Robot",
    description: "Výrazný animovaný robot pre hravejšiu prechádzku.",
    icon: "robot",
    modelUrl: "/v1-assets/avatar/robot-expressive.glb",
    modelScale: 0.37,
    headingOffsetRad: 0,
    clips: { idle: "Idle", walk: "Walking", run: "Running" },
  },
] as const satisfies readonly WalkAvatarOption[];

export function isWalkAvatarId(value: unknown): value is WalkAvatarId {
  return (
    typeof value === "string" &&
    (WALK_AVATAR_IDS as readonly string[]).includes(value)
  );
}

export function walkAvatarOption(id: WalkAvatarId): WalkAvatarOption {
  return (
    WALK_AVATARS.find((option) => option.id === id) ?? WALK_AVATARS[0]
  );
}
