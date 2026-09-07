import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { Scene } from '@babylonjs/core/scene';
import { Ray } from '@babylonjs/core/Culling/ray';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { CreateBox } from '@babylonjs/core/Meshes/Builders/boxBuilder';
import { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial';
import { describe, expect, it } from 'vitest';
import { resolveWalkFloor } from '../lib/babylon-walk-picking';
import { WalkDestination } from '../lib/twin-walk-navigation';

describe('walk destination picking with imported presentation', () => {
  it('accepts a GLB floor or thin rug over hidden native floors, rejects furniture and walls', () => {
    const engine = new NullEngine();
    const scene = new Scene(engine);
    try {
      const floor = CreateBox('native floor', {width:8, depth:8, height:0.02}, scene);
      floor.material = new StandardMaterial('floor material', scene);
      floor.position.y = -0.01;
      floor.visibility = 0;
      floor.isPickable = false;
      floor.metadata = {walkSurface:true, walkSurfaceElevationOffsetM:0.002};
      const finish = CreateBox('imported visual', {width:3, depth:3, height:0.02}, scene);
      finish.material = floor.material;
      finish.position.y = 0.01;
      const pickTop = () => {
        scene.meshes.forEach(mesh => mesh.computeWorldMatrix(true));
        return scene.pickWithRay(new Ray(new Vector3(0,2,0), Vector3.Down(), 3), mesh => mesh === finish);
      };
      expect(resolveWalkFloor(scene, pickTop(), 0)?.y).toBeCloseTo(0.002);
      const destination = resolveWalkFloor(scene, pickTop(), 0)!;
      const trip = new WalkDestination();
      expect(trip.start(new Vector3(0,0,1), destination)).toBe(true);
      expect(trip.step(new Vector3(0,0,0.5),16)?.heading).toEqual({x:0,z:-1});
      expect(trip.step(new Vector3(0,0,0.1),16)).toBeNull();
      expect(trip.status).toBe('arrived');
      finish.position.y = 0.04;
      expect(resolveWalkFloor(scene, pickTop(), 0)).not.toBeNull();
      finish.position.y = 0.54;
      expect(resolveWalkFloor(scene, pickTop(), 0)).toBeNull();
      const wallHit = scene.pickWithRay(new Ray(new Vector3(0,0.54,3), new Vector3(0,0,-1), 5), mesh => mesh === finish);
      expect(resolveWalkFloor(scene, wallHit, 0)).toBeNull();
      finish.position.y = 0.01;
      expect(resolveWalkFloor(scene, pickTop(), 1)).toBeNull();
    } finally { scene.dispose(); engine.dispose(); }
  });
});
