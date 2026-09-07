import { readFile } from "node:fs/promises";

import "@babylonjs/core/Collisions/collisionCoordinator";
import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { CreateBox } from "@babylonjs/core/Meshes/Builders/boxBuilder.pure";
import { CreateGround } from "@babylonjs/core/Meshes/Builders/groundBuilder.pure";
import { Scene } from "@babylonjs/core/scene";
import { describe, expect, it } from "vitest";

import { AvatarController } from "../lib/babylon-avatar";
import { walkAvatarOption, type WalkAvatarId } from "../lib/twin-avatar";
import {
  WALK_COLLISION_ELLIPSOID_M,
  WALK_COLLISION_OFFSET_M,
  WALK_SURFACE,
} from "../lib/twin-viewport-contract";

async function assetDataUrl(publicUrl: string) {
  const bytes = await readFile(new URL(`../public${publicUrl}`, import.meta.url));
  const mime = publicUrl.endsWith(".png")
    ? "image/png"
    : "model/gltf-binary";
  return `data:${mime};base64,${bytes.toString("base64")}`;
}

describe("Babylon adaptive walk surfaces", () => {
  it.each([30,60,144,240])("keeps the viewing direction while backing up at %i FPS",fps=>{
    const engine=new NullEngine(),scene=new Scene(engine);
    scene.useRightHandedSystem=true;scene.collisionsEnabled=true;
    const floor=CreateGround('backwards test floor',{width:20,height:20},scene);
    floor.metadata={walkSurface:true,walkSurfaceKind:'interior'};
    const avatar=new AvatarController(scene,()=>undefined);
    try{
      avatar.place(0,0,0);
      const initialAlpha=avatar.camera.alpha;
      for(let i=0;i<fps*3;i++)avatar.update(1000/fps,new Set(['backward']),{boost:false,precision:false});
      expect(avatar.camera.alpha).toBeCloseTo(initialAlpha,7);
      expect(avatar.pose.z).toBeLessThan(-2.5);
      expect(Math.abs(avatar.pose.x)).toBeLessThan(.02);
    }finally{avatar.dispose();scene.dispose();engine.dispose();}
  });
  it("places the feet on tagged interior and terrain geometry only", () => {
    const engine = new NullEngine();
    const scene = new Scene(engine);
    scene.useRightHandedSystem = true;

    const interior = CreateGround(
      "test interior floor",
      { width: 3, height: 3 },
      scene,
    );
    interior.position.set(-3, 0.08, 0);
    interior.metadata = {
      walkSurface: true,
      walkSurfaceKind: "interior",
      walkSurfaceId: "test-room",
    };
    const terrain = CreateGround(
      "test terrain",
      { width: 3, height: 3 },
      scene,
    );
    terrain.position.set(3, -0.13, 0);
    terrain.metadata = {
      walkSurface: true,
      walkSurfaceKind: "terrain",
      walkSurfaceId: "test-terrain",
    };
    const decorativeTexture = CreateBox(
      "untagged decorative texture",
      { width: 1.5, height: 0.04, depth: 1.5 },
      scene,
    );
    decorativeTexture.position.set(-3, 0.14, 0);

    const avatar = new AvatarController(scene, () => undefined);
    try {
      avatar.place(-3, 0, 0);
      expect(avatar.pose.y).toBeCloseTo(0.08, 6);
      expect(avatar.cameraState).toMatchObject({
        surfaceKind: "interior",
        surfaceId: "test-room",
        surfaceValid: true,
      });
      expect(avatar.cameraState.surfaceY).toBeCloseTo(0.08, 6);
      expect(avatar.cameraState.cameraSurfaceY).toBeCloseTo(0.08, 6);

      for (let frame = 0; frame < 150; frame += 1) {
        avatar.update(
          1000 / 60,
          new Set(["forward"]),
          { boost: false, precision: false },
          { x: 1, z: 0 },
        );
      }
      expect(avatar.pose.x).toBeLessThan(-1.45);
      expect(avatar.pose.y).toBeCloseTo(0.08, 6);
      expect(avatar.cameraState.surfaceValid).toBe(true);

      avatar.place(3, 0, 0);
      expect(avatar.pose.y).toBeCloseTo(-0.13, 6);
      expect(avatar.eyePosition.y).toBeCloseTo(1.49, 6);
      expect(avatar.cameraState).toMatchObject({
        surfaceKind: "terrain",
        surfaceId: "test-terrain",
        surfaceValid: true,
      });
    } finally {
      avatar.dispose();
      scene.dispose();
      engine.dispose();
    }
  });

  it("blocks an exact raised platform over terrain but ignores true overhead", () => {
    const engine = new NullEngine();
    const scene = new Scene(engine);
    scene.useRightHandedSystem = true;
    scene.collisionsEnabled = true;

    const terrain = CreateGround(
      "raised-platform test terrain",
      { width: 8, height: 4 },
      scene,
    );
    terrain.metadata = {
      walkSurface: true,
      walkSurfaceKind: "terrain",
      walkSurfaceId: "raised-platform-terrain",
    };
    const platform = CreateGround(
      "raised-platform exact blocker",
      { width: 1.2, height: 2 },
      scene,
    );
    platform.position.set(
      0.6,
      WALK_SURFACE.maxStepUpM + 0.03,
      0,
    );
    platform.metadata = {
      walkSurface: true,
      walkSurfaceKind: "exterior",
      walkSurfaceId: "raised-platform",
    };
    const overhead = CreateGround(
      "raised-platform true overhead",
      { width: 1.2, height: 2 },
      scene,
    );
    overhead.position.set(
      2.6,
      WALK_COLLISION_OFFSET_M.y + WALK_COLLISION_ELLIPSOID_M.y + 0.2,
      0,
    );
    overhead.metadata = {
      walkSurface: true,
      walkSurfaceKind: "exterior",
      walkSurfaceId: "true-overhead",
    };

    const avatar = new AvatarController(scene, () => undefined);
    const walkRight = (frames: number) => {
      for (let frame = 0; frame < frames; frame += 1) {
        avatar.update(
          1000 / 60,
          new Set(["forward"]),
          { boost: false, precision: false },
          { x: 1, z: 0 },
        );
      }
    };
    try {
      avatar.place(-0.8, 0, 0);
      walkRight(120);
      expect(avatar.pose.x).toBeLessThan(0);
      expect(avatar.pose.y).toBeCloseTo(0, 6);
      expect(avatar.cameraState).toMatchObject({
        surfaceKind: "terrain",
        surfaceId: "raised-platform-terrain",
        surfaceValid: true,
      });

      avatar.place(1.4, 0, 0);
      walkRight(120);
      expect(avatar.pose.x).toBeGreaterThan(3.2);
      expect(avatar.pose.y).toBeCloseTo(0, 6);
      expect(avatar.cameraState.surfaceId).toBe("raised-platform-terrain");
    } finally {
      avatar.dispose();
      scene.dispose();
      engine.dispose();
    }
  });

  it("does not rewind at one wall but escapes a genuine two-direction trap", () => {
    const engine = new NullEngine();
    const scene = new Scene(engine);
    scene.useRightHandedSystem = true;
    scene.collisionsEnabled = true;

    const floor = CreateGround(
      "collision test floor",
      { width: 8, height: 8 },
      scene,
    );
    floor.metadata = {
      walkSurface: true,
      walkSurfaceKind: "interior",
      walkSurfaceId: "collision-test-room",
    };
    const frontWall = CreateBox(
      "collision test front wall",
      { width: 3, height: 2.4, depth: 0.1 },
      scene,
    );
    frontWall.position.set(0, 1.2, -0.75);
    frontWall.checkCollisions = true;
    const leftWall = CreateBox(
      "collision test left wall",
      { width: 0.1, height: 2.4, depth: 1.6 },
      scene,
    );
    leftWall.position.set(-0.275, 1.2, -0.35);
    leftWall.checkCollisions = true;

    const avatar = new AvatarController(scene, () => undefined);
    const step = (
      command: "forward" | "left",
      frames: number,
      heading = { x: 0, z: -1 },
    ) => {
      for (let frame = 0; frame < frames; frame += 1) {
        avatar.update(
          1000 / 60,
          new Set([command]),
          { boost: false, precision: false },
          heading,
        );
      }
    };
    try {
      avatar.place(0, 0, 0);
      step("forward", 75);
      expect(avatar.recoveryState.needed).toBe(true);
      expect(avatar.recoveryState.autoRecoveryCount).toBe(0);
      const blockedPose = avatar.pose;

      step("forward", 30, { x: -1, z: 0 });
      step("forward", 20);
      expect(avatar.recoveryState.autoRecoveryCount).toBe(0);

      step("left", 30);
      step("forward", 20);
      expect(avatar.recoveryState.autoRecoveryCount).toBe(1);
      expect(avatar.recoveryState.needed).toBe(false);
      expect(avatar.recoveryState.awaitingRelease).toBe(true);
      expect(Math.hypot(
        avatar.pose.x - blockedPose.x,
        avatar.pose.z - blockedPose.z,
      )).toBeGreaterThan(0.08);
      expect(avatar.recoveryState.cooldownS).toBeGreaterThan(0);
      avatar.update(
        1000 / 60,
        new Set(),
        { boost: false, precision: false },
        { x: 0, z: -1 },
      );
      expect(avatar.recoveryState.awaitingRelease).toBe(false);
    } finally {
      avatar.dispose();
      scene.dispose();
      engine.dispose();
    }
  });
});

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
