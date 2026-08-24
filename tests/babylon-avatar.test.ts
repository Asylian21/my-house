import { readFile } from "node:fs/promises";

import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { Scene } from "@babylonjs/core/scene";
import { describe, expect, it } from "vitest";

import { AvatarController } from "../lib/babylon-avatar";
import { walkAvatarOption, type WalkAvatarId } from "../lib/twin-avatar";

async function assetDataUrl(publicUrl: string) {
  const bytes = await readFile(new URL(`../public${publicUrl}`, import.meta.url));
  const mime = publicUrl.endsWith(".png")
    ? "image/png"
    : "model/gltf-binary";
  return `data:${mime};base64,${bytes.toString("base64")}`;
}

describe("Babylon avatar rig switching", () => {
  it("keeps one controller pose, camera and collider while all three visual rigs switch", async () => {
    const urls = new Set<string>();
    for (const id of ["michelle", "vanguard", "robot"] as const) {
      const option = walkAvatarOption(id);
      urls.add(option.modelUrl);
      if (option.diffuseUrl) urls.add(option.diffuseUrl);
    }
    const localAssets = new Map(
      await Promise.all(
        [...urls].map(async (url) => [url, await assetDataUrl(url)] as const),
      ),
    );
    const engine = new NullEngine();
    const scene = new Scene(engine);
    scene.useRightHandedSystem = true;
    const loadedMeshes: string[] = [];
    const avatar = new AvatarController(
      scene,
      (mesh) => {
        loadedMeshes.push(mesh.name);
      },
      (url) => localAssets.get(url) ?? url,
    );

    try {
      avatar.place(3.25, -1.75, 0.62);
      await avatar.load();
      expect(avatar.avatarId).toBe("michelle");
      expect(avatar.activeAvatarId).toBe("michelle");
      expect(avatar.isLoaded).toBe(true);
      const originalPose = avatar.pose;
      const originalCamera = avatar.cameraState;
      const assertLocomotionPlaying = (id: WalkAvatarId) => {
        const clips = walkAvatarOption(id).clips;
        expect(
          scene.animationGroups
            .filter((group) => group.isPlaying)
            .map((group) => group.name)
            .sort(),
        ).toEqual([clips.idle, clips.run, clips.walk].sort());
      };
      const activeRigHeightM = () => {
        let minimumY = Number.POSITIVE_INFINITY;
        let maximumY = Number.NEGATIVE_INFINITY;
        for (const mesh of scene.meshes) {
          if (
            mesh.name.startsWith("Avatar · kolízny") ||
            mesh.getTotalVertices() === 0 ||
            !mesh.isEnabled()
          ) {
            continue;
          }
          mesh.computeWorldMatrix(true);
          const bounds = mesh.getBoundingInfo().boundingBox;
          minimumY = Math.min(minimumY, bounds.minimumWorld.y);
          maximumY = Math.max(maximumY, bounds.maximumWorld.y);
        }
        return maximumY - minimumY;
      };
      assertLocomotionPlaying("michelle");
      expect(activeRigHeightM()).toBeGreaterThan(1.6);
      expect(activeRigHeightM()).toBeLessThan(1.75);

      await avatar.setAvatar("vanguard", true);
      expect(avatar.avatarId).toBe("vanguard");
      expect(avatar.activeAvatarId).toBe("vanguard");
      expect(avatar.pose).toEqual(originalPose);
      expect(avatar.cameraState).toEqual(originalCamera);
      assertLocomotionPlaying("vanguard");
      expect(activeRigHeightM()).toBeGreaterThan(1.78);
      expect(activeRigHeightM()).toBeLessThan(1.9);

      avatar.setFirstPerson(true);
      await avatar.setAvatar("robot", true);
      expect(avatar.avatarId).toBe("robot");
      expect(avatar.activeAvatarId).toBe("robot");
      expect(avatar.isFirstPerson).toBe(true);
      expect(avatar.pose).toEqual(originalPose);
      expect(avatar.cameraState).toEqual(originalCamera);
      assertLocomotionPlaying("robot");

      avatar.setFirstPerson(false);
      expect(activeRigHeightM()).toBeGreaterThan(1.65);
      expect(activeRigHeightM()).toBeLessThan(1.75);
      await avatar.setAvatar("michelle", true);
      expect(avatar.activeAvatarId).toBe("michelle");
      expect(avatar.pose).toEqual(originalPose);
      expect(loadedMeshes.length).toBeGreaterThanOrEqual(22);
      assertLocomotionPlaying("michelle");
    } finally {
      avatar.dispose();
      scene.dispose();
      engine.dispose();
    }
  });
});
