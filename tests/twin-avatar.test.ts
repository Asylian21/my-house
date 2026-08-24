import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import {
  DEFAULT_WALK_AVATAR_ID,
  WALK_AVATARS,
  WALK_AVATAR_IDS,
  isWalkAvatarId,
  walkAvatarOption,
} from "../lib/twin-avatar";

interface GlbJson {
  readonly asset?: { readonly version?: string };
  readonly meshes?: readonly unknown[];
  readonly skins?: readonly unknown[];
  readonly materials?: readonly unknown[];
  readonly animations?: readonly { readonly name?: string }[];
}

async function readGlbJson(publicUrl: string): Promise<GlbJson> {
  const path = fileURLToPath(
    new URL(`../public${publicUrl}`, import.meta.url),
  );
  const bytes = await readFile(path);
  expect(bytes.subarray(0, 4).toString("ascii")).toBe("glTF");
  expect(bytes.readUInt32LE(4)).toBe(2);
  const jsonLength = bytes.readUInt32LE(12);
  expect(bytes.subarray(16, 20).toString("ascii")).toBe("JSON");
  return JSON.parse(
    bytes
      .subarray(20, 20 + jsonLength)
      .toString("utf8")
      .replace(/\0+$/u, ""),
  ) as GlbJson;
}

describe("walk avatar catalogue", () => {
  it("offers exactly three stable, unique choices and keeps Michelle as default", () => {
    expect(WALK_AVATAR_IDS).toEqual(["michelle", "vanguard", "robot"]);
    expect(WALK_AVATARS.map((avatar) => avatar.id)).toEqual(WALK_AVATAR_IDS);
    expect(new Set(WALK_AVATARS.map((avatar) => avatar.id)).size).toBe(3);
    expect(DEFAULT_WALK_AVATAR_ID).toBe("michelle");
    expect(walkAvatarOption(DEFAULT_WALK_AVATAR_ID).tagline).toBe("Pôvodná");
  });

  it("accepts only persisted catalogue ids", () => {
    for (const id of WALK_AVATAR_IDS) expect(isWalkAvatarId(id)).toBe(true);
    for (const value of [null, "", "1", "unknown", 3, {}]) {
      expect(isWalkAvatarId(value)).toBe(false);
    }
  });

  it("ships a skinned glTF with the declared locomotion clips for every choice", async () => {
    for (const avatar of WALK_AVATARS) {
      expect(avatar.modelUrl).toMatch(/^\/assets\/avatar\/[a-z0-9-]+\.glb$/u);
      expect(avatar.label.length).toBeGreaterThan(1);
      expect(avatar.description.length).toBeGreaterThan(12);
      expect(avatar.modelScale).toBeGreaterThan(0);
      const glb = await readGlbJson(avatar.modelUrl);
      const clips = new Set(
        glb.animations?.map((animation) => animation.name) ?? [],
      );
      expect(glb.asset?.version).toBe("2.0");
      expect(glb.meshes?.length ?? 0).toBeGreaterThan(0);
      expect(glb.skins?.length ?? 0).toBeGreaterThan(0);
      expect(glb.materials?.length ?? 0).toBeGreaterThan(0);
      expect(clips.has(avatar.clips.idle)).toBe(true);
      expect(clips.has(avatar.clips.walk)).toBe(true);
      expect(clips.has(avatar.clips.run)).toBe(true);
    }
  });

  it("applies the generated diffuse override only to the original Michelle rig", () => {
    expect(walkAvatarOption("michelle").diffuseUrl).toBe(
      "/assets/avatar/michelle-light-diffuse.png",
    );
    expect(walkAvatarOption("vanguard").diffuseUrl).toBeUndefined();
    expect(walkAvatarOption("robot").diffuseUrl).toBeUndefined();
  });
});
