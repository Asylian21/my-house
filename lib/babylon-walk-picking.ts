import { Ray } from '@babylonjs/core/Culling/ray';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { PickingInfo } from '@babylonjs/core/Collisions/pickingInfo';
import type { Scene } from '@babylonjs/core/scene';

/** Resolve a visible finish (including a thin rug / imported GLB) onto its native floor. */
export function resolveWalkFloor(scene: Scene, hit: PickingInfo | null, elevationM: number) {
  if (!hit?.hit || !hit.pickedPoint || (hit.getNormal(true)?.y ?? 0) < 0.7) return null;
  const point = hit.pickedPoint;
  const floor = scene.pickWithRay(
    new Ray(point.add(new Vector3(0, 0.05, 0)), Vector3.Down(), 0.12),
    // Imported presentation hides native surfaces, but they still govern walking.
    mesh => mesh.isEnabled() && !mesh.isDisposed() && mesh.metadata?.walkSurface === true,
  );
  if (!floor?.hit || !floor.pickedPoint || (floor.getNormal(true)?.y ?? 0) < 0.7) return null;
  const destination = floor.pickedPoint.clone();
  destination.y += floor.pickedMesh?.metadata?.walkSurfaceElevationOffsetM ?? 0;
  if (Math.abs(point.y-destination.y) > 0.07) return null;
  const step = destination.y-elevationM;
  return step > 0.22 || step < -0.3 ? null : destination;
}
