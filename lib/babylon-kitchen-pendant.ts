import { VertexBuffer } from "@babylonjs/core/Buffers/buffer";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { Color3 } from "@babylonjs/core/Maths/math.color";
import { CreateBox } from "@babylonjs/core/Meshes/Builders/boxBuilder.pure";
import { CreateCylinder } from "@babylonjs/core/Meshes/Builders/cylinderBuilder.pure";
import type { Mesh } from "@babylonjs/core/Meshes/mesh";
import { VertexData } from "@babylonjs/core/Meshes/mesh.vertexData";
import type { Scene } from "@babylonjs/core/scene";
import { registerKitchenLightEmitter } from "./babylon-interior-lighting";
import { KITCHEN_ISLAND_LIGHT } from "./twin-interior-lighting";
import { MM_TO_M, sceneXM, sceneZM } from "./twin-render-frame";

export interface KitchenPendantContext {
  scene: Scene;
  finish(mesh: Mesh, material: PBRMaterial): void;
}

/** One quiet horizontal line; its two fine suspensions follow the cathedral roof. */
export function buildKitchenPendant({ scene, finish }: KitchenPendantContext): void {
  const f = KITCHEN_ISLAND_LIGHT;
  const [x, y, elevation] = f.geometry.bodyCenterPlanMm;
  const [width, depth, height] = f.geometry.dimensionsMm;
  const metal = new PBRMaterial("kitchen-pendant · graphite anodised aluminium", scene);
  metal.albedoColor = Color3.FromHexString("#252723").toLinearSpace();
  metal.metallic = 0.5;
  metal.roughness = 0.6;
  const opal = new PBRMaterial("kitchen-pendant · recessed opal diffuser", scene);
  opal.albedoColor = Color3.FromHexString("#e8e3d9").toLinearSpace();
  opal.metallic = 0;
  opal.roughness = 0.65;

  const body = CreateBox(f.geometry.sourceName, {
    width: width * MM_TO_M, depth: depth * MM_TO_M, height: height * MM_TO_M,
  }, scene);
  body.position.set(sceneXM(x), elevation * MM_TO_M, sceneZM(y));
  finish(body, metal);
  body.metadata = { ...(body.metadata ?? {}), interiorLightId: f.id };

  const diffuser = CreateBox("KITCHEN-RUN · ISLAND-LIGHT · opálový difúzor", {
    width: f.light.sourceWidthMm * MM_TO_M, depth: f.light.sourceHeightMm * MM_TO_M, height: 0.001,
  }, scene);
  diffuser.position.set(sceneXM(x), (elevation - height / 2 - 0.5) * MM_TO_M, sceneZM(y));
  finish(diffuser, opal);
  diffuser.metadata = { ...(diffuser.metadata ?? {}), interiorLightEmitterId: f.id };
  registerKitchenLightEmitter(scene, f.id, opal);

  for (const [index, suspension] of f.suspension.entries()) {
    const ceilingCenterMm = (suspension.ceilingLeftMm + suspension.ceilingRightMm) / 2;
    const cableTopMm = ceilingCenterMm - suspension.mountThicknessMm;
    const cable = CreateCylinder(`KITCHEN-RUN · ISLAND-LIGHT · jemný záves ${index + 1}`, {
      diameter: suspension.cableDiameterMm * MM_TO_M,
      height: (cableTopMm - suspension.bottomMm) * MM_TO_M, tessellation: 12,
    }, scene);
    cable.position.set(sceneXM(suspension.xMm), (cableTopMm + suspension.bottomMm) / 2 * MM_TO_M, sceneZM(suspension.yMm));
    finish(cable, metal);

    const mount = CreateBox(`KITCHEN-RUN · ISLAND-LIGHT · kotvenie do šikmého stropu ${index + 1}`, {
      width: suspension.mountWidthMm * MM_TO_M,
      depth: suspension.mountDepthMm * MM_TO_M,
      height: suspension.mountThicknessMm * MM_TO_M, updatable: true,
    }, scene);
    const vertices = mount.getVerticesData(VertexBuffer.PositionKind)!;
    for (let i = 0; i < vertices.length; i += 3) {
      const roofAtEdgeMm = vertices[i] < 0 ? suspension.ceilingLeftMm : suspension.ceilingRightMm;
      vertices[i + 1] += (roofAtEdgeMm - ceilingCenterMm) * MM_TO_M;
    }
    mount.updateVerticesData(VertexBuffer.PositionKind, vertices, true);
    const normals: number[] = [];
    VertexData.ComputeNormals(vertices, mount.getIndices()!, normals);
    mount.updateVerticesData(VertexBuffer.NormalKind, normals);
    mount.refreshBoundingInfo();
    mount.position.set(sceneXM(suspension.xMm), (ceilingCenterMm - suspension.mountThicknessMm / 2) * MM_TO_M, sceneZM(suspension.yMm));
    finish(mount, metal);
  }
}
