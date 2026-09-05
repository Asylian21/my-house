import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { Texture } from "@babylonjs/core/Materials/Textures/texture";
import { CreatePlane } from "@babylonjs/core/Meshes/Builders/planeBuilder.pure";
import type { Vector3 } from "@babylonjs/core/Maths/math.vector";
import type { Scene } from "@babylonjs/core/scene";

/** Small readable model plates and tailgate lettering, authored for this scene. */
export function createVehicleLettering(scene: Scene, asset: "superb-model-plate" | "superb-rear-wordmark",
  position: Vector3, direction: -1 | 1, width: number, height: number) {
  const name = `Superb Combi IV · ${asset}`;
  let material = scene.getMaterialByName(name) as PBRMaterial | null;
  if (!material) {
    material = new PBRMaterial(name, scene);
    material.metallic = 0;
    material.roughness = 0.7;
    material.backFaceCulling = false;
    if (typeof document !== "undefined") {
      material.albedoTexture = new Texture(`/assets/vehicles/${asset}.svg`, scene);
      material.albedoTexture.hasAlpha = true;
      material.useAlphaFromAlbedoTexture = true;
      material.transparencyMode = PBRMaterial.PBRMATERIAL_ALPHATEST;
    }
  }
  const mesh = CreatePlane(name, { width, height }, scene);
  mesh.position.copyFrom(position);
  mesh.rotation.y = direction * Math.PI / 2;
  mesh.material = material;
  mesh.metadata = { vehiclePart: "vehicle-lettering" };
  return mesh;
}
