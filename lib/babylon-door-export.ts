import { Matrix } from "@babylonjs/core/Maths/math.vector";
import { VertexBuffer } from "@babylonjs/core/Buffers/buffer";
import type { Scene } from "@babylonjs/core/scene";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { ARCHITECTURAL_DOOR_INVENTORY, DOOR_INTERACTION, doorMotionDurationMs, type BabylonDoorController } from "./babylon-doors";

const nativeMatrix = (source: Matrix) => {
  const m = source.asArray(), axes = [0, 2, 1, 3];
  return axes.flatMap((row) => axes.map((column) => m[row * 4 + column] * (row === 3 && column !== 3 ? 100 : 1)));
};
const snapshot = (mesh: AbstractMesh) => mesh.computeWorldMatrix(true).clone();
const differs = (a: Matrix, b: Matrix) => a.asArray().some((value, i) => Math.abs(value - b.asArray()[i]) > 1e-7);
const pointCm = (point: { x: number; z: number; y?: number }) => [point.x * 100, point.z * 100, (point.y ?? 1.22) * 100];

/** Sample the actual web apply(progress, handleDepression) closures. No native
 * hinge angles, pivots, slide distances or garage track shapes are guessed. */
export function captureNativeDoorMotion(scene: Scene, controller: BabylonDoorController) {
  const candidates = scene.meshes.filter((mesh) => mesh.isEnabled()
    && mesh.getVerticesData(VertexBuffer.PositionKind)?.length && mesh.getIndices()?.length
    && ((mesh.isVisible && mesh.visibility >= .01) || mesh.checkCollisions));
  const steps = [...new Set([...Array.from({ length: 129 }, (_, i) => i / 128), .0125, .025, .05, .075])].sort((a, b) => a - b);
  const doors = controller.captureNativeExport((door) => {
    const before = new Map(candidates.map((mesh) => [mesh, snapshot(mesh)]));
    door.apply(1, 1);
    const moving = candidates.filter((mesh) => differs(before.get(mesh)!, snapshot(mesh)));
    door.apply(0, 0);
    if (!moving.length) throw new Error(`Door ${door.id} has no moving source geometry`);
    const members = moving.map((mesh) => {
      mesh.computeWorldMatrix(true);
      const box = mesh.getBoundingInfo().boundingBox;
      return {
        sourceId: mesh.id, sourceName: mesh.name,
        hidden: !mesh.isVisible || mesh.visibility < .01,
        collision: mesh.checkCollisions || mesh.metadata?.cameraOccluder === true || mesh.metadata?.walkSurface === true,
        walkSurface: mesh.metadata?.walkSurface === true,
        closedBoundsCm: { min: [box.minimumWorld.x * 100, box.minimumWorld.z * 100, box.minimumWorld.y * 100],
          max: [box.maximumWorld.x * 100, box.maximumWorld.z * 100, box.maximumWorld.y * 100] },
        sourceClosedWorldMatrix: Array.from(before.get(mesh)!.asArray()),
        poses: [] as number[][], handlePoses: [] as number[][],
      };
    });
    const inverses = moving.map((mesh) => Matrix.Invert(before.get(mesh)!));
    for (const progress of steps) {
      for (const depression of [0, 1]) {
        door.apply(progress, depression);
        for (const [index, mesh] of moving.entries()) {
          const delta = nativeMatrix(inverses[index].multiply(snapshot(mesh)));
          (depression === 0 ? members[index].poses : members[index].handlePoses).push(delta);
        }
      }
    }
    door.apply(0, 0);
    for (const mesh of moving) if (differs(before.get(mesh)!, snapshot(mesh))) throw new Error(`Door ${door.id} failed to restore its source closed pose`);
    return { id: door.id, label: door.label, kind: door.kind, subject: door.subject ?? "DOOR",
      architectural: ARCHITECTURAL_DOOR_INVENTORY.some((entry) => entry.id === door.id),
      interactionPointCm: pointCm(door.interactionPoint),
      openingSeconds: doorMotionDurationMs(door.kind, 1) / 1000,
      closingSeconds: doorMotionDurationMs(door.kind, 0) / 1000,
      passage: door.passage ?? null, members };
  });
  return { schemaVersion: 1, coordinateSystem: "UNREAL_XY_Z_CM", source: "registered-web-door-apply-functions",
    closedCapture: true, progressSamples: steps, interaction: DOOR_INTERACTION,
    architecturalInventory: ARCHITECTURAL_DOOR_INVENTORY, doors,
    excludedTraversal: "Pool ladder changes actor/camera position and is not a moving door member." };
}
