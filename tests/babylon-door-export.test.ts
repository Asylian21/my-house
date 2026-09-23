import { describe, expect, it } from 'vitest';
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { Scene } from '@babylonjs/core/scene';
import { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import { CreateBox } from '@babylonjs/core/Meshes/Builders/boxBuilder.pure';
import { Matrix, Vector3 } from '@babylonjs/core/Maths/math.vector';
import { BabylonDoorController, INTERACTIVE_DOOR_INVENTORY } from '../lib/babylon-doors';
import { captureNativeDoorMotion } from '../lib/babylon-door-export';

describe('native capture of actual door callbacks', () => {
  it('captures rigid native motion, untagged hardware, collision and restores closed source geometry', () => {
    const engine = new NullEngine(); const scene = new Scene(engine); scene.useRightHandedSystem = true;
    const controller = new BabylonDoorController();
    for (const [index, entry] of INTERACTIVE_DOOR_INVENTORY.entries()) {
      const pivot = new TransformNode(entry.id, scene); pivot.position.set(index * 3, 0, 2);
      const leaf = CreateBox(entry.id + '-leaf', { width: .8, height: 2, depth: .04 }, scene);
      leaf.parent = pivot; leaf.position.set(.4, 1, 0); leaf.checkCollisions = true;
      const hardware = CreateBox(entry.id + '-hardware', { size: .05 }, scene);
      hardware.parent = pivot; hardware.position.set(.65, 1, .05);
      controller.register({ ...entry, label: entry.id, interactionPoint: { x: index * 3 + .4, z: 2 },
        apply: progress => { pivot.rotation.y = progress * Math.PI / 2; } });
    }
    try {
      const result = captureNativeDoorMotion(scene, controller);
      expect(result.doors).toHaveLength(19);
      expect(result.doors.filter(door => door.architectural)).toHaveLength(16);
      expect(result.doors.every(door => door.members.length === 2)).toBe(true);
      const first = result.doors[0];
      const leaf = first.members.find(member => member.collision)!;
      const rest = scene.getMeshById(leaf.sourceId)!;
      const closedCenter = rest.getBoundingInfo().boundingBox.centerWorld;
      const native = new Vector3(closedCenter.x * 100, closedCenter.z * 100, closedCenter.y * 100);
      const moved = Vector3.TransformCoordinates(native, Matrix.FromArray(leaf.poses.at(-1)!));
      const parent = rest.parent as TransformNode;
      expect(moved.x).toBeCloseTo(parent.position.x * 100, 3);
      expect(moved.y).toBeCloseTo((parent.position.z - .4) * 100, 3);
      expect(moved.z).toBeCloseTo(100, 3);
      expect(parent.rotation.y).toBe(0);
      expect(controller.debugState().every(door => door.progress === 0 && door.phase === 'CLOSED')).toBe(true);
    } finally { scene.dispose(); engine.dispose(); }
  });

  it('rejects a capture during interactive motion instead of exporting a partially open house', () => {
    const controller = new BabylonDoorController();
    for (const entry of INTERACTIVE_DOOR_INVENTORY) controller.register({ ...entry, label: entry.id,
      interactionPoint: { x: 0, z: 0 }, apply: () => {} });
    controller.setOpen(INTERACTIVE_DOOR_INVENTORY[0].id, true);
    expect(() => controller.captureNativeExport(() => null)).toThrow(/initial closed/);
  });
});
