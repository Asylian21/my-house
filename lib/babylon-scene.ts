import { ArcRotateCamera } from "@babylonjs/core/Cameras/arcRotateCamera";
import type { FreeCameraMouseInput } from "@babylonjs/core/Cameras/Inputs/freeCameraMouseInput";
import { UniversalCamera } from "@babylonjs/core/Cameras/universalCamera";
import { Engine } from "@babylonjs/core/Engines/engine";
import { PhotoDome } from "@babylonjs/core/Helpers/photoDome";
import { DirectionalLight } from "@babylonjs/core/Lights/directionalLight";
import { HemisphericLight } from "@babylonjs/core/Lights/hemisphericLight";
import { CascadedShadowGenerator } from "@babylonjs/core/Lights/Shadows/cascadedShadowGenerator";
import { ShadowGenerator } from "@babylonjs/core/Lights/Shadows/shadowGenerator";
import { HighlightLayer } from "@babylonjs/core/Layers/highlightLayer";
import { ImageProcessingConfiguration } from "@babylonjs/core/Materials/imageProcessingConfiguration";
import type { Material } from "@babylonjs/core/Materials/material";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { StandardMaterial } from "@babylonjs/core/Materials/standardMaterial";
import { EquiRectangularCubeTexture } from "@babylonjs/core/Materials/Textures/equiRectangularCubeTexture";
import { DynamicTexture } from "@babylonjs/core/Materials/Textures/dynamicTexture";
import { Texture } from "@babylonjs/core/Materials/Textures/texture";
import { Color3, Color4 } from "@babylonjs/core/Maths/math.color";
import {
  Matrix,
  Quaternion,
  Vector3,
  Vector4,
} from "@babylonjs/core/Maths/math.vector";
import { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { CreateBox } from "@babylonjs/core/Meshes/Builders/boxBuilder.pure";
import { CreateCylinder } from "@babylonjs/core/Meshes/Builders/cylinderBuilder.pure";
import { ExtrudePolygon } from "@babylonjs/core/Meshes/Builders/polygonBuilder.pure";
import { CreateGround } from "@babylonjs/core/Meshes/Builders/groundBuilder.pure";
import { CreatePlane } from "@babylonjs/core/Meshes/Builders/planeBuilder.pure";
import { CreateSphere } from "@babylonjs/core/Meshes/Builders/sphereBuilder.pure";
import {
  CreateDashedLines,
  CreateLines,
} from "@babylonjs/core/Meshes/Builders/linesBuilder.pure";
import { CreateTube } from "@babylonjs/core/Meshes/Builders/tubeBuilder.pure";
import { LinesMesh } from "@babylonjs/core/Meshes/linesMesh";
import { Mesh } from "@babylonjs/core/Meshes/mesh";
import { VertexData } from "@babylonjs/core/Meshes/mesh.vertexData";
import { TransformNode } from "@babylonjs/core/Meshes/transformNode";
import "@babylonjs/core/Meshes/thinInstanceMesh";
import { Ray } from "@babylonjs/core/Culling/ray";
import { DefaultRenderingPipeline } from "@babylonjs/core/PostProcesses/RenderPipeline/Pipelines/defaultRenderingPipeline";
import { SSAO2RenderingPipeline } from "@babylonjs/core/PostProcesses/RenderPipeline/Pipelines/ssao2RenderingPipeline";
import "@babylonjs/core/Rendering/prePassRendererSceneComponent";
import "@babylonjs/core/Rendering/depthRendererSceneComponent";
import "@babylonjs/core/Rendering/geometryBufferRendererSceneComponent";
import "@babylonjs/core/Rendering/edgesRenderer";
import "@babylonjs/core/Collisions/collisionCoordinator";
import { Scene } from "@babylonjs/core/scene";
import earcut from "earcut";

import {
  CADASTRAL_PARCELS,
  GARDEN_POOL,
  HOUSE,
  LAYERS,
  ROAD_CONTEXT,
  SITE_FENCE,
  SITE_SURFACES,
  TERRACE_ZONES_D1,
  UTILITY_ROUTES,
  sjtskToLocalMm,
  type CadastralParcel,
  type FoundationStrip,
  type LayerId,
  type Point2Mm,
  type TerraceZoneD1,
  type ViewMode,
} from "./twin-site";
import {
  segmentFacadeMm,
  type FacadeOpeningMm,
} from "./twin-facade";
import {
  AXONOMETRIC_CAMERA_ALPHA,
  MM_TO_M,
  SCENE_CENTER_MM,
  TOP_CAMERA_ALPHA,
  gardenCameraForWidth,
  focusRadiusForBoundingSphere,
  sceneDeltaForPlanSegment,
  sceneXM as xM,
  sceneYawForPlanSegment,
  sceneZM as zM,
  parcelCameraForWidth,
  parcelLabelScaleForRadius,
  streetCameraForWidth,
} from "./twin-render-frame";
import {
  deriveJoinedRoofGeometry,
  roofMountTransform,
  wingInnerRoofHeightMm,
  wingOuterRoofHeightMm,
  type JoinedRoofGeometry,
  type RoofPointMm,
  type RoofVertexMm,
} from "./twin-roof";
import { slatCenterDistancesMm } from "./twin-fence";
import { buildInterior } from "./babylon-interior";
import { AvatarController } from "./babylon-avatar";
import type { WalkAvatarId } from "./twin-avatar";
import {
  buildOpening,
  resolveFacadeOpeningStyle,
  type OpeningKind,
  type OpeningInteraction,
} from "./babylon-openings";
import {
  ARCHITECTURAL_DOOR_INVENTORY,
  BabylonDoorController,
  type AnimatedDoorRegistration,
  type DoorInteractionSnapshot,
} from "./babylon-doors";
import {
  INTERIOR_ROOMS,
  roomAt,
  type InteriorRoom,
} from "./twin-interior";
import {
  GARAGE_SEQUENCE,
  GARAGE_VEHICLE,
  garageActionForState,
  garageAnimationFrame,
  garageCinematicRequiresSafePosition,
  garageDoorPanelPose,
  garageVehicleSurfaceElevationM,
  type GarageAnimationFrame,
  type GarageParkingState,
  type GarageVehicleAction,
} from "./twin-garage";
import {
  GARAGE_SUPERB_AXLES_M,
  GARAGE_SUPERB_BODY_STATIONS,
  GARAGE_SUPERB_CABIN_STATIONS,
  vehicleLoftGeometry,
  type VehicleLoftStation,
} from "./twin-garage-model";
import {
  ORBIT_ZOOM,
  clampOrbitRadius,
  deriveRenderQualityProfile,
  flightCommandForCode,
  flightWheelDollyDistanceM,
  integrateFlightDolly,
  integrateFlightPosition,
  isSelectionTap,
  normalizeWheelPixels,
  orbitZoomMultiplier,
  stepOrbitZoom,
  wheelZoomGesture,
  type FlightCommand,
  type NavigationMode,
  type RenderQualityProfile,
} from "./twin-viewport-contract";

export type CameraPreset =
  | "garden"
  | "axonometric"
  | "top"
  | "parcels"
  | "street"
  | "focus";
type OpeningVisualKind = OpeningKind;

interface PointerGestureState {
  readonly pointerId: number;
  readonly button: number;
  readonly startedAt: number;
  readonly startX: number;
  readonly startY: number;
  maximumPointers: number;
  travelPx: number;
}

export interface SceneSnapshot {
  readonly foundations: readonly FoundationStrip[];
  readonly selectionId: string | null;
  readonly visibleLayers: Readonly<Record<LayerId, boolean>>;
  readonly viewMode: ViewMode;
}

const CENTER_X_M = SCENE_CENTER_MM.x * MM_TO_M;
const GROUND_Y = -0.035;
const EAVES_M = HOUSE.eavesElevationMm * MM_TO_M;
const point3 = (point: Point2Mm, elevationM = GROUND_Y) =>
  new Vector3(xM(point.x), elevationM, zM(point.y));

function surfaceMaterial(
  scene: Scene,
  name: string,
  color: string,
  roughness = 0.9,
  alpha = 1,
) {
  const material = new StandardMaterial(name, scene);
  material.diffuseColor = Color3.FromHexString(color);
  const specular = Math.max(0.035, (1 - roughness) * 0.5);
  material.specularColor = new Color3(specular, specular, specular);
  material.specularPower = roughness < 0.5 ? 96 : 32;
  material.alpha = alpha;
  material.backFaceCulling = false;
  return material;
}

function pbrMaterial(
  scene: Scene,
  name: string,
  color: string,
  roughness: number,
  metallic = 0,
  alpha = 1,
) {
  const material = new PBRMaterial(name, scene);
  material.albedoColor = Color3.FromHexString(color);
  material.metallic = metallic;
  material.roughness = roughness;
  material.alpha = alpha;
  material.backFaceCulling = true;
  material.environmentIntensity = 1;
  if (alpha < 1) {
    material.transparencyMode = PBRMaterial.PBRMATERIAL_ALPHABLEND;
    material.useAlphaFromAlbedoTexture = false;
  }
  return material;
}

function createVehicleLoftMesh(
  scene: Scene,
  name: string,
  stations: readonly VehicleLoftStation[],
  material: Material,
) {
  const geometry = vehicleLoftGeometry(stations);
  const positions = [...geometry.positions];
  const indices = [...geometry.indices];
  const mesh = new Mesh(name, scene);
  const normals = new Array(positions.length).fill(0);
  VertexData.ComputeNormals(positions, indices, normals);
  const data = new VertexData();
  data.positions = positions;
  data.indices = indices;
  data.normals = normals;
  data.uvs = [...geometry.uvs];
  data.applyToMesh(mesh);
  mesh.material = material;
  return mesh;
}

function createVerticalTriangle(
  scene: Scene,
  name: string,
  points: readonly [Vector3, Vector3, Vector3],
  outward: Vector3,
) {
  const mesh = new Mesh(name, scene);
  const data = new VertexData();
  data.positions = points.flatMap((point) => [point.x, point.y, point.z]);
  const indices = [0, 2, 1];
  const normals = [0, 0, 0, 0, 0, 0, 0, 0, 0];
  VertexData.ComputeNormals(data.positions, indices, normals);
  // Gable planes must be lit from their exterior side: flip the winding if
  // the computed normal points into the house.
  if (normals[0] * outward.x + normals[1] * outward.y + normals[2] * outward.z < 0) {
    indices.reverse();
    for (let index = 0; index < normals.length; index += 1) normals[index] *= -1;
  }
  data.indices = indices;
  data.normals = normals;
  const ys = points.map((point) => point.y);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  data.uvs = points.flatMap((point) => [
    (point.x + point.z) * 0.35,
    (point.y - minY) / Math.max(0.001, maxY - minY),
  ]);
  data.applyToMesh(mesh);
  return mesh;
}

function createFlatPolygon(
  scene: Scene,
  name: string,
  ring: readonly Point2Mm[],
  elevationM: number,
  worldUvRepeatMm?: number,
) {
  const openRing =
    ring.length > 1 &&
    ring[0].x === ring[ring.length - 1].x &&
    ring[0].y === ring[ring.length - 1].y
      ? ring.slice(0, -1)
      : ring;
  const mesh = new Mesh(name, scene);
  const planar = openRing.flatMap((point) => [xM(point.x), zM(point.y)]);
  const positions = openRing.flatMap((point) => [xM(point.x), elevationM, zM(point.y)]);
  const minX = Math.min(...openRing.map((point) => point.x));
  const maxX = Math.max(...openRing.map((point) => point.x));
  const minY = Math.min(...openRing.map((point) => point.y));
  const maxY = Math.max(...openRing.map((point) => point.y));
  const uvs = worldUvRepeatMm
    ? openRing.flatMap((point) => [
        point.x / worldUvRepeatMm,
        point.y / worldUvRepeatMm,
      ])
    : openRing.flatMap((point) => [
        (point.x - minX) / Math.max(1, maxX - minX),
        (point.y - minY) / Math.max(1, maxY - minY),
      ]);
  const triangulated = earcut(planar, undefined, 2);
  const indices: number[] = [];
  for (let index = 0; index < triangulated.length; index += 3) {
    indices.push(
      triangulated[index],
      triangulated[index + 2],
      triangulated[index + 1],
    );
  }
  const normals = openRing.flatMap(() => [0, 1, 0]);
  const data = new VertexData();
  data.positions = positions;
  data.indices = indices;
  data.normals = normals;
  data.uvs = uvs;
  data.applyToMesh(mesh);
  return mesh;
}

function createGradedPolygon(
  scene: Scene,
  name: string,
  ring: readonly Point2Mm[],
  elevationForPoint: (point: Point2Mm) => number,
) {
  const openRing =
    ring.length > 1 &&
    ring[0].x === ring[ring.length - 1].x &&
    ring[0].y === ring[ring.length - 1].y
      ? ring.slice(0, -1)
      : ring;
  const mesh = new Mesh(name, scene);
  const planar = openRing.flatMap((point) => [xM(point.x), zM(point.y)]);
  const positions = openRing.flatMap((point) => [
    xM(point.x),
    elevationForPoint(point),
    zM(point.y),
  ]);
  const minX = Math.min(...openRing.map((point) => point.x));
  const maxX = Math.max(...openRing.map((point) => point.x));
  const minY = Math.min(...openRing.map((point) => point.y));
  const maxY = Math.max(...openRing.map((point) => point.y));
  const uvs = openRing.flatMap((point) => [
    (point.x - minX) / Math.max(1, maxX - minX),
    (point.y - minY) / Math.max(1, maxY - minY),
  ]);
  const triangulated = earcut(planar, undefined, 2);
  const indices: number[] = [];
  for (let index = 0; index < triangulated.length; index += 3) {
    indices.push(
      triangulated[index],
      triangulated[index + 2],
      triangulated[index + 1],
    );
  }
  const normals = new Array(positions.length).fill(0);
  VertexData.ComputeNormals(positions, indices, normals);
  const data = new VertexData();
  data.positions = positions;
  data.indices = indices;
  data.normals = normals;
  data.uvs = uvs;
  data.applyToMesh(mesh);
  return mesh;
}

function createGradedPolygonEdgeSkirt(
  scene: Scene,
  name: string,
  ring: readonly Point2Mm[],
  elevationForPoint: (point: Point2Mm) => number,
  baseElevationM: number,
) {
  const openRing =
    ring.length > 1 &&
    ring[0].x === ring[ring.length - 1].x &&
    ring[0].y === ring[ring.length - 1].y
      ? ring.slice(0, -1)
      : ring;
  const positions: number[] = [];
  const indices: number[] = [];

  for (let index = 0; index < openRing.length; index += 1) {
    const start = openRing[index];
    const end = openRing[(index + 1) % openRing.length];
    const topStart = elevationForPoint(start);
    const topEnd = elevationForPoint(end);
    const vertexOffset = positions.length / 3;
    const quad = [
      xM(start.x), topStart, zM(start.y),
      xM(end.x), topEnd, zM(end.y),
      xM(end.x), baseElevationM, zM(end.y),
      xM(start.x), baseElevationM, zM(start.y),
    ];
    // Duplicate each face with the opposite winding. The restraints are visible
    // from both the grass and paving sides without changing shared materials.
    positions.push(...quad, ...quad);
    indices.push(
      vertexOffset,
      vertexOffset + 1,
      vertexOffset + 2,
      vertexOffset,
      vertexOffset + 2,
      vertexOffset + 3,
      vertexOffset + 4,
      vertexOffset + 6,
      vertexOffset + 5,
      vertexOffset + 4,
      vertexOffset + 7,
      vertexOffset + 6,
    );
  }

  const mesh = new Mesh(name, scene);
  const normals = new Array(positions.length).fill(0);
  VertexData.ComputeNormals(positions, indices, normals);
  const data = new VertexData();
  data.positions = positions;
  data.indices = indices;
  data.normals = normals;
  data.applyToMesh(mesh);
  return mesh;
}

function createFlatPolygonWithHoles(
  scene: Scene,
  name: string,
  outerRing: readonly Point2Mm[],
  holeRings: readonly (readonly Point2Mm[])[],
  elevationM: number,
) {
  const openRing = (ring: readonly Point2Mm[]) =>
    ring.length > 1 &&
    ring[0].x === ring[ring.length - 1].x &&
    ring[0].y === ring[ring.length - 1].y
      ? ring.slice(0, -1)
      : [...ring];
  const rings = [openRing(outerRing), ...holeRings.map(openRing)];
  const points = rings.flat();
  const holeIndices: number[] = [];
  let vertexOffset = rings[0].length;
  for (let index = 1; index < rings.length; index += 1) {
    holeIndices.push(vertexOffset);
    vertexOffset += rings[index].length;
  }

  const mesh = new Mesh(name, scene);
  const planar = points.flatMap((point) => [xM(point.x), zM(point.y)]);
  const positions = points.flatMap((point) => [
    xM(point.x),
    elevationM,
    zM(point.y),
  ]);
  const minX = Math.min(...points.map((point) => point.x));
  const maxX = Math.max(...points.map((point) => point.x));
  const minY = Math.min(...points.map((point) => point.y));
  const maxY = Math.max(...points.map((point) => point.y));
  const uvs = points.flatMap((point) => [
    (point.x - minX) / Math.max(1, maxX - minX),
    (point.y - minY) / Math.max(1, maxY - minY),
  ]);
  const triangulated = earcut(planar, holeIndices, 2);
  const indices: number[] = [];
  for (let index = 0; index < triangulated.length; index += 3) {
    indices.push(
      triangulated[index],
      triangulated[index + 2],
      triangulated[index + 1],
    );
  }
  const data = new VertexData();
  data.positions = positions;
  data.indices = indices;
  data.normals = points.flatMap(() => [0, 1, 0]);
  data.uvs = uvs;
  data.applyToMesh(mesh);
  return mesh;
}

function createRoofFace(
  scene: Scene,
  name: string,
  vertices: readonly RoofVertexMm[],
) {
  const mesh = new Mesh(name, scene);
  const positions = vertices.flatMap((point) => [
    xM(point.xMm),
    point.elevationMm * MM_TO_M,
    zM(point.yMm),
  ]);
  const indices = [0, 1, 2, 0, 2, 3];
  const normals = vertices.flatMap(() => [0, 0, 0]);
  VertexData.ComputeNormals(positions, indices, normals);
  // The roof must always be lit from above: flip winding if the computed
  // plane normal points below the horizon.
  if (normals[1] < 0) {
    indices.reverse();
    for (let index = 0; index < normals.length; index += 1) normals[index] *= -1;
  }
  const minX = Math.min(...vertices.map(({ xMm }) => xMm));
  const minY = Math.min(...vertices.map(({ yMm }) => yMm));
  const uvs = vertices.flatMap(({ xMm, yMm }) => [
    (xMm - minX) / 1000 / 1.08,
    (yMm - minY) / 1000 / 1.08,
  ]);
  const data = new VertexData();
  data.positions = positions;
  data.indices = indices;
  data.normals = normals;
  data.uvs = uvs;
  data.applyToMesh(mesh);
  return mesh;
}

function boxAtPlan(
  scene: Scene,
  name: string,
  centerMm: Point2Mm,
  widthMm: number,
  depthMm: number,
  heightM: number,
  elevationM: number,
) {
  const mesh = CreateBox(
    name,
    {
      width: widthMm * MM_TO_M,
      depth: depthMm * MM_TO_M,
      height: heightM,
    },
    scene,
  );
  mesh.position.set(xM(centerMm.x), elevationM + heightM / 2, zM(centerMm.y));
  return mesh;
}

/**
 * Solid extruded from a vertical profile. `plane === "Y"` keeps the profile in
 * a plane of constant plan-y (profile `along` = plan x), `plane === "X"` in a
 * plane of constant plan-x (profile `along` = plan y). The solid fills the
 * thickness between `fromMm` and `toMm` on the perpendicular axis.
 */
function verticalProfileSolid(
  scene: Scene,
  name: string,
  plane: "X" | "Y",
  profile: readonly { readonly alongMm: number; readonly elevationMm: number }[],
  fromMm: number,
  toMm: number,
) {
  const thicknessM = Math.abs(toMm - fromMm) * MM_TO_M;
  const shape = profile.map((point) =>
    plane === "Y"
      ? new Vector3(xM(point.alongMm), 0, point.elevationMm * MM_TO_M)
      : new Vector3(-zM(point.alongMm), 0, point.elevationMm * MM_TO_M),
  );
  const mesh = ExtrudePolygon(
    name,
    { shape, depth: thicknessM, sideOrientation: Mesh.DOUBLESIDE },
    scene,
    earcut,
  );
  // Pitch the XZ polygon upright (profile z → world y, extrusion -y → +z),
  // then yaw X-plane profiles so the extrusion runs along world x.
  const yaw = plane === "Y" ? 0 : Math.PI / 2;
  mesh.rotationQuaternion = Quaternion.RotationYawPitchRoll(yaw, -Math.PI / 2, 0);
  if (plane === "Y") {
    mesh.position.set(0, 0, zM(Math.max(fromMm, toMm)));
  } else {
    mesh.position.set(xM(Math.min(fromMm, toMm)), 0, 0);
  }
  return mesh;
}

interface PlanBoxInstance {
  readonly centerMm: Point2Mm;
  readonly widthMm: number;
  readonly depthMm: number;
  readonly heightMm: number;
  readonly baseElevationMm: number;
  readonly yawRad: number;
}

function pointAlongSegment(
  start: Point2Mm,
  end: Point2Mm,
  distanceMm: number,
): Point2Mm {
  const lengthMm = Math.hypot(end.x - start.x, end.y - start.y);
  if (lengthMm === 0) return start;
  const ratio = distanceMm / lengthMm;
  return {
    x: start.x + (end.x - start.x) * ratio,
    y: start.y + (end.y - start.y) * ratio,
  };
}

function slatInstancesForSegment(
  start: Point2Mm,
  end: Point2Mm,
  widthMm: number,
  depthMm: number,
  pitchMm: number,
  heightMm: number,
  baseElevationMm: number,
): PlanBoxInstance[] {
  const lengthMm = Math.hypot(end.x - start.x, end.y - start.y);
  const centerDistancesMm = slatCenterDistancesMm(
    lengthMm,
    widthMm,
    pitchMm,
  );
  const yawRad = sceneYawForPlanSegment(start, end);
  return centerDistancesMm.map((distanceMm) => ({
    centerMm: pointAlongSegment(start, end, distanceMm),
    widthMm,
    depthMm,
    heightMm,
    baseElevationMm,
    yawRad,
  }));
}

function segmentBox(
  start: Point2Mm,
  end: Point2Mm,
  depthMm: number,
  heightMm: number,
  baseElevationMm: number,
): PlanBoxInstance {
  return {
    centerMm: {
      x: (start.x + end.x) / 2,
      y: (start.y + end.y) / 2,
    },
    widthMm: Math.hypot(end.x - start.x, end.y - start.y),
    depthMm,
    heightMm,
    baseElevationMm,
    yawRad: sceneYawForPlanSegment(start, end),
  };
}

function longestParcelAxisYaw(localRing: readonly Point2Mm[]) {
  let longest = 0;
  let yaw = 0;
  for (let index = 1; index < localRing.length; index += 1) {
    const start = localRing[index - 1];
    const end = localRing[index];
    const length = Math.hypot(end.x - start.x, end.y - start.y);
    if (length > longest) {
      longest = length;
      yaw = sceneYawForPlanSegment(start, end);
    }
  }
  // Ground typography is easiest to read when its baseline stays within ±90°
  // of the local road axis rather than appearing upside down from above.
  if (yaw > Math.PI / 2) yaw -= Math.PI;
  if (yaw < -Math.PI / 2) yaw += Math.PI;
  return yaw;
}

function roundedLabelPath(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
) {
  const r = Math.min(radius, width / 2, height / 2);
  context.beginPath();
  context.moveTo(x + r, y);
  context.lineTo(x + width - r, y);
  context.quadraticCurveTo(x + width, y, x + width, y + r);
  context.lineTo(x + width, y + height - r);
  context.quadraticCurveTo(
    x + width,
    y + height,
    x + width - r,
    y + height,
  );
  context.lineTo(x + r, y + height);
  context.quadraticCurveTo(x, y + height, x, y + height - r);
  context.lineTo(x, y + r);
  context.quadraticCurveTo(x, y, x + r, y);
  context.closePath();
}

function parcelLabelMaterial(
  scene: Scene,
  parcel: CadastralParcel,
  anisotropy: number,
) {
  const subject = parcel.isSubject;
  const texture = new DynamicTexture(
    `parcel-label-${parcel.parcelNumber}`,
    { width: 768, height: 240 },
    scene,
    true,
  );
  texture.hasAlpha = true;
  texture.anisotropicFilteringLevel = anisotropy;
  const context = texture.getContext();
  context.clearRect(0, 0, 768, 240);
  context.save();
  context.shadowColor = "rgba(8, 12, 10, 0.56)";
  context.shadowBlur = 18;
  context.shadowOffsetY = 8;
  roundedLabelPath(context, 20, 20, 728, 200, 28);
  context.fillStyle = subject
    ? "rgba(38, 28, 24, 0.94)"
    : "rgba(24, 30, 27, 0.86)";
  context.fill();
  context.shadowColor = "transparent";
  context.lineWidth = subject ? 7 : 4;
  context.strokeStyle = subject
    ? "rgba(255, 103, 76, 0.98)"
    : "rgba(244, 238, 224, 0.84)";
  context.stroke();
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillStyle = subject ? "#ffb09f" : "#d7ded8";
  context.font = "700 25px Arial, sans-serif";
  context.letterSpacing = "4px";
  context.fillText(subject ? "MOJA PARCELA" : "KATASTER", 384, 70);
  context.letterSpacing = "0px";
  context.fillStyle = "#fffdf6";
  context.font = subject
    ? "700 92px Arial, sans-serif"
    : "700 84px Arial, sans-serif";
  context.fillText(parcel.parcelNumber, 384, 146);
  context.restore();
  texture.update(false);

  const material = new StandardMaterial(
    `parcel-label-material-${parcel.parcelNumber}`,
    scene,
  );
  material.diffuseTexture = texture;
  material.diffuseColor = Color3.White();
  material.emissiveColor = Color3.FromHexString("#92958e");
  material.specularColor = Color3.Black();
  material.useAlphaFromDiffuseTexture = true;
  material.backFaceCulling = false;
  material.disableLighting = true;
  material.zOffset = -2;
  return material;
}

function inwardOffsetForSegment(
  start: Point2Mm,
  end: Point2Mm,
  distanceMm: number,
): Point2Mm {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const lengthMm = Math.hypot(dx, dy);
  if (lengthMm === 0 || distanceMm === 0) return { x: 0, y: 0 };
  return {
    x: (-dy / lengthMm) * distanceMm,
    y: (dx / lengthMm) * distanceMm,
  };
}

function translatedPoint(point: Point2Mm, offset: Point2Mm): Point2Mm {
  return { x: point.x + offset.x, y: point.y + offset.y };
}

/** Where a walker entering a room looks first: toward its largest glazing. */
function walkLookTargetMm(room: InteriorRoom): Point2Mm {
  switch (room.id) {
    case "ROOM-1-03":
      return { x: 24540, y: 21000 };
    case "ROOM-1-02":
      return { x: 22090, y: 11000 };
    case "ROOM-1-01":
      return { x: 22100, y: 6500 };
    case "ROOM-1-12":
      return { x: 8500, y: 3000 };
    case "ROOM-1-09":
    case "ROOM-1-10":
      return { x: room.standingPointMm.x, y: 11500 };
    case "ROOM-1-04":
      // The office is entered through its north-west bay; frame the rotated
      // desk and 40-inch ultrawide instead of looking past them at FRONT-07.
      return { x: 26230, y: 4100 };
    case "ROOM-1-08":
    case "ROOM-1-11":
      return { x: room.standingPointMm.x, y: 2500 };
    case "ROOM-1-06":
      // The WC is too narrow for a useful chase view across its short axis.
      // Face the open door instead: the first W press naturally exits to the
      // corridor, rather than driving a novice straight into the east wall.
      return { x: 22000, y: 10266 };
    case "ROOM-1-05":
    case "ROOM-1-07":
      return { x: 28500, y: room.standingPointMm.y };
    default:
      return { x: room.standingPointMm.x + 1000, y: room.standingPointMm.y };
  }
}

export class TwinSceneController {
  private readonly engine: Engine;
  private readonly scene: Scene;
  private readonly orbitCamera: ArcRotateCamera;
  private readonly flightCamera: UniversalCamera;
  private readonly garageCinematicCamera: UniversalCamera;
  private readonly layerMeshes = new Map<LayerId, AbstractMesh[]>();
  private readonly entityMeshes = new Map<string, AbstractMesh[]>();
  private readonly foundationMeshes = new Map<string, Mesh>();
  private readonly materials: Record<string, StandardMaterial>;
  private readonly realisticMaterials: Record<string, PBRMaterial>;
  private readonly larchClones = new Map<string, PBRMaterial>();
  private readonly appearances = new Map<
    AbstractMesh,
    { technical: Material; realistic: Material }
  >();
  private readonly realisticOnlyMeshes: AbstractMesh[] = [];
  private readonly technicalOverlayMeshes: AbstractMesh[] = [];
  private readonly parcelLabelMeshes: Mesh[] = [];
  private readonly shadowGenerator: ShadowGenerator;
  private readonly cascadedShadowGenerator: CascadedShadowGenerator | null;
  private readonly selectionHighlight: HighlightLayer;
  private readonly doors: BabylonDoorController;
  private readonly postPipeline: DefaultRenderingPipeline;
  private readonly ssaoPipeline: SSAO2RenderingPipeline | null;
  private readonly poolWaterNormal: Texture;
  private readonly selectedOriginals = new Map<
    AbstractMesh,
    {
      material: Material | null;
      lineColor?: Color3;
      edgeColor?: Color4;
      edgeWidth?: number;
    }
  >();
  private readonly onVisibilityChange: () => void;
  private readonly keyboardFlightCommands = new Set<FlightCommand>();
  private readonly manualFlightCommands = new Set<FlightCommand>();
  private readonly flightModifierCodes = new Set<string>();
  private readonly activePointers = new Set<number>();
  private pointerGesture: PointerGestureState | null = null;
  private navigationMode: NavigationMode = "orbit";
  private renderQuality: RenderQualityProfile;
  private ssaoAttached = false;
  private flightHeading = { x: 0, z: -1 };
  private orbitFocusDistance = 18;
  private orbitZoomTargetM = ORBIT_ZOOM.upperRadiusLimitM;
  private orbitZoomActive = false;
  private resizeFrame = 0;
  private snapshot: SceneSnapshot | null = null;
  private readonly garageDoorPanels: Mesh[] = [];
  private garageVehicleRoot: TransformNode | null = null;
  private readonly garageVehicleWheelSpins: TransformNode[] = [];
  private readonly garageVehicleFrontSteering: TransformNode[] = [];
  private garageVehicleBrakeMaterial: PBRMaterial | null = null;
  private garageVehicleHeadlightMaterial: PBRMaterial | null = null;
  private garageParkingState: GarageParkingState = "away";
  private garageVehicleAction: GarageVehicleAction | null = null;
  private garageVehicleElapsedMs = 0;
  private garageDoorProgress = 0;
  private garageVehicleLastPose: GarageAnimationFrame["vehiclePose"] | null = null;
  private garageVehicleWheelAngle = 0;
  private garageVehicleSteeringAngle = 0;
  private garageCinematicActive = false;
  private garageCinematicReturnCamera:
    | ArcRotateCamera
    | UniversalCamera
    | null = null;

  constructor(
    private readonly canvas: HTMLCanvasElement,
    private readonly onSelect: (id: string) => void,
    private readonly onNavigationModeChange: (mode: NavigationMode) => void,
    private readonly onRenderQualityChange: (
      profile: RenderQualityProfile,
    ) => void,
  ) {
    this.engine = new Engine(canvas, true, {
      preserveDrawingBuffer: false,
      stencil: true,
      adaptToDeviceRatio: false,
      powerPreference: "high-performance",
    });
    this.renderQuality = this.deriveCurrentRenderQuality();
    this.engine.setHardwareScalingLevel(
      this.renderQuality.hardwareScalingLevel,
    );
    this.scene = new Scene(this.engine);
    this.doors = new BabylonDoorController(
      window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0.18 : 1,
    );
    this.scene.useRightHandedSystem = true;
    this.scene.skipPointerMovePicking = true;
    this.scene.clearColor = Color4.FromHexString("#c6cfd2ff");
    this.scene.ambientColor = Color3.FromHexString("#5d6462");

    // A dedicated 2K source avoids the very large transient float buffers that
    // Babylon's equirectangular cube conversion would allocate from the 8K
    // panorama. The resulting 512 px IBL cube remains visually lossless here.
    const environment = new EquiRectangularCubeTexture(
      "/assets/environment/suburban-field-01-2k.jpg",
      this.scene,
      this.renderQuality.environmentTextureSize,
      false,
      false,
      () => {
        this.scene.environmentTexture = environment;
        this.scene.environmentIntensity = 0.95;
      },
    );
    const panoramaUrl =
      this.renderQuality.tier === "ULTRA" &&
      this.engine.getCaps().maxTextureSize >= 8192 &&
      this.renderQuality.renderWidthPx >= 2_000
        ? "/assets/environment/suburban-field-01-8k.jpg"
        : "/assets/environment/suburban-field-01-4k.jpg";
    const sky = new PhotoDome(
      "Ilustračné záhradné prostredie",
      panoramaUrl,
      { resolution: 64, size: 360, useDirectMapping: false },
      this.scene,
    );
    // Keep the visible panorama and the equirectangular IBL in the same world
    // orientation so reflections and the apparent light source agree.
    sky.rotation.y = 0;
    sky.mesh.isPickable = false;
    sky.mesh.applyFog = false;
    this.realisticOnlyMeshes.push(sky.mesh);
    this.scene.imageProcessingConfiguration.toneMappingEnabled = true;
    this.scene.imageProcessingConfiguration.toneMappingType =
      ImageProcessingConfiguration.TONEMAPPING_ACES;
    this.scene.imageProcessingConfiguration.exposure = 1.08;
    this.scene.imageProcessingConfiguration.contrast = 1.12;
    this.scene.imageProcessingConfiguration.vignetteEnabled = false;
    this.scene.imageProcessingConfiguration.vignetteWeight = 0.72;
    this.scene.imageProcessingConfiguration.vignetteColor =
      Color4.FromHexString("#42504b32");

    const gardenCamera = gardenCameraForWidth(canvas.clientWidth);
    this.orbitCamera = new ArcRotateCamera(
      "architect-camera",
      gardenCamera.alpha,
      gardenCamera.beta,
      gardenCamera.radius,
      new Vector3(...gardenCamera.target),
      this.scene,
    );
    this.orbitCamera.lowerRadiusLimit = ORBIT_ZOOM.lowerRadiusLimitM;
    this.orbitCamera.upperRadiusLimit = ORBIT_ZOOM.upperRadiusLimitM;
    this.orbitCamera.lowerBetaLimit = 0.06;
    this.orbitCamera.upperBetaLimit = Math.PI / 2.02;
    // Wheel zoom is handled by the dedicated exponential controller below;
    // the built-in percentage model cannot keep up with Mac trackpad deltas.
    this.orbitCamera.inputs.removeByType("ArcRotateCameraMouseWheelInput");
    this.orbitCamera.panningSensibility = 95;
    this.orbitCamera.useNaturalPinchZoom = ORBIT_ZOOM.useNaturalPinchZoom;
    this.orbitCamera.inertia = 0.72;
    this.orbitCamera.minZ = 0.18;
    this.orbitCamera.maxZ = 220;
    this.orbitCamera.fov = gardenCamera.fov;
    this.orbitCamera.attachControl(canvas, !ORBIT_ZOOM.preventBrowserGesture);
    this.orbitZoomTargetM = this.orbitCamera.radius;

    this.flightCamera = new UniversalCamera(
      "helicopter-camera",
      this.orbitCamera.globalPosition.clone(),
      this.scene,
    );
    this.flightCamera.inputs.removeByType("FreeCameraKeyboardMoveInput");
    this.flightCamera.inputs.removeByType("FreeCameraTouchInput");
    this.flightCamera.inputs.removeByType("FreeCameraGamepadInput");
    const flightMouseInput = this.flightCamera.inputs.attached[
      "mouse"
    ] as FreeCameraMouseInput | undefined;
    if (flightMouseInput) flightMouseInput.touchEnabled = true;
    this.flightCamera.angularSensibility = 2600;
    this.flightCamera.inertia = 0.68;
    this.flightCamera.minZ = 0.18;
    this.flightCamera.maxZ = 220;
    this.flightCamera.fov = this.orbitCamera.fov;
    this.flightCamera.setTarget(this.orbitCamera.target);
    this.flightCamera.detachControl();

    this.garageCinematicCamera = new UniversalCamera(
      "garage-street-cinematic-camera",
      new Vector3(0, 3, 28),
      this.scene,
    );
    this.garageCinematicCamera.inputs.clear();
    this.garageCinematicCamera.minZ = 0.12;
    this.garageCinematicCamera.maxZ = 220;
    this.garageCinematicCamera.detachControl();
    this.configureGarageCinematicCamera(
      garageAnimationFrame("park", 0).vehiclePose,
    );
    this.scene.activeCamera = this.orbitCamera;
    this.canvas.dataset.garageCameraView = "garage";
    // The walker's chase camera exists from the start so every post-process
    // pipeline can own it; the rigged glTF itself loads on the first walk.
    this.avatar = new AvatarController(this.scene, (mesh) => {
      this.castShadow(mesh);
      this.realisticOnly(mesh);
    });

    const ambient = new HemisphericLight(
      "ambient-light",
      new Vector3(0.25, 1, -0.12),
      this.scene,
    );
    ambient.intensity = 0.3;
    ambient.diffuse = Color3.FromHexString("#eef4f6");
    ambient.groundColor = Color3.FromHexString("#6a755f");
    // Soft high sun angled so the garden facade and porch corner read like the
    // approved reference photograph (bright overcast with gentle shadows).
    const sun = new DirectionalLight(
      "architectural-sun",
      new Vector3(0.18, -1, 0.52),
      this.scene,
    );
    sun.position = new Vector3(-26, 46, -26);
    sun.intensity = 1.04;
    sun.diffuse = Color3.FromHexString("#fffaf1");
    sun.specular = Color3.FromHexString("#ffffff");
    this.cascadedShadowGenerator = CascadedShadowGenerator.IsSupported
      ? new CascadedShadowGenerator(
          this.renderQuality.shadowMapSize,
          sun,
          true,
        )
      : null;
    this.shadowGenerator =
      this.cascadedShadowGenerator ??
      new ShadowGenerator(this.renderQuality.shadowMapSize, sun);
    if (this.cascadedShadowGenerator) {
      this.cascadedShadowGenerator.numCascades = 4;
      this.cascadedShadowGenerator.stabilizeCascades = true;
      this.cascadedShadowGenerator.cascadeBlendPercentage = 0.12;
      this.cascadedShadowGenerator.lambda = 0.72;
      this.cascadedShadowGenerator.shadowMaxZ = 78;
      this.cascadedShadowGenerator.depthClamp = true;
    }
    this.shadowGenerator.usePercentageCloserFiltering = true;
    this.shadowGenerator.filteringQuality =
      this.renderQuality.tier === "ULTRA"
      ? ShadowGenerator.QUALITY_HIGH
      : ShadowGenerator.QUALITY_MEDIUM;
    this.shadowGenerator.bias = 0.00018;
    this.shadowGenerator.normalBias = 0.0018;
    this.shadowGenerator.transparencyShadow = true;
    this.shadowGenerator.setDarkness(0.14);

    this.selectionHighlight = new HighlightLayer(
      "selection-outline",
      this.scene,
      { blurHorizontalSize: 0.55, blurVerticalSize: 0.55 },
    );
    this.selectionHighlight.innerGlow = false;
    this.selectionHighlight.outerGlow = true;

    this.postPipeline = new DefaultRenderingPipeline(
      "architectural-photo-pipeline",
      true,
      this.scene,
      [
        this.orbitCamera,
        this.flightCamera,
        this.garageCinematicCamera,
        this.avatar.camera,
      ],
    );
    this.postPipeline.samples = this.renderQuality.msaaSamples;
    this.postPipeline.fxaaEnabled = this.renderQuality.fxaaEnabled;
    // HDR bloom only catches true highlights (sun glints on water, metal
    // seams, glass edges); the sky stays clean below the threshold.
    this.postPipeline.bloomEnabled = false;
    this.postPipeline.bloomThreshold = 1;
    this.postPipeline.bloomWeight = 0.055;
    this.postPipeline.bloomKernel = 48;
    this.postPipeline.bloomScale = 0.5;
    this.postPipeline.imageProcessingEnabled = true;
    this.postPipeline.sharpenEnabled = true;
    this.postPipeline.sharpen.edgeAmount =
      this.renderQuality.sharpenEdgeAmount;
    this.postPipeline.sharpen.colorAmount = 1;
    // Animated fine grain gives flat outdoor gradients a photographic
    // texture; it is enabled together with bloom in realistic mode only.
    this.postPipeline.grainEnabled = false;
    this.postPipeline.grain.intensity = 9;
    this.postPipeline.grain.animated = true;
    const renderCameras = [
      this.orbitCamera,
      this.flightCamera,
      this.garageCinematicCamera,
    ];
    let ssaoPipeline: SSAO2RenderingPipeline | null = null;
    // Construct once even when the initial mobile tier is HIGH. This allows a
    // later resize/promotion to ULTRA to attach SSAO instead of silently losing
    // contact shading for the rest of the session.
    if (SSAO2RenderingPipeline.IsSupported) {
      try {
        ssaoPipeline = new SSAO2RenderingPipeline(
          "architectural-ssao",
          this.scene,
          {
            ssaoRatio: 1,
            blurRatio: 1,
          },
          renderCameras,
          false,
        );
        ssaoPipeline.radius = 0.62;
        ssaoPipeline.totalStrength = 0.62;
        ssaoPipeline.samples = 16;
        ssaoPipeline.expensiveBlur = true;
        ssaoPipeline.bilateralSamples = 12;
        ssaoPipeline.bilateralSoften = 0.42;
        ssaoPipeline.bilateralTolerance = 0.38;
      } catch {
        // SSAO is a progressive enhancement; WebGL fallbacks skip it.
      }
    }
    this.ssaoPipeline = ssaoPipeline;
    this.ssaoAttached = Boolean(ssaoPipeline);
    if (ssaoPipeline && !this.renderQuality.ssaoEnabled) {
      this.scene.postProcessRenderPipelineManager.detachCamerasFromRenderPipeline(
        ssaoPipeline.name,
        renderCameras,
      );
      this.ssaoAttached = false;
    } else if (!ssaoPipeline && this.renderQuality.ssaoEnabled) {
      this.renderQuality = {
        ...this.renderQuality,
        ssaoEnabled: false,
        ssaoRatio: 0,
      };
    }
    this.onRenderQualityChange(this.renderQuality);

    this.materials = {
      terrain: surfaceMaterial(this.scene, "terrain", "#171d1b", 1),
      parcel: surfaceMaterial(this.scene, "parcel", "#27332c", 0.98, 0.88),
      parcelBoundary: surfaceMaterial(
        this.scene,
        "parcel-boundary",
        "#e8e0d3",
        0.95,
        0.9,
      ),
      parcelBoundarySubject: surfaceMaterial(
        this.scene,
        "parcel-boundary-subject",
        "#ff654b",
        0.82,
      ),
      road: surfaceMaterial(this.scene, "road", "#333a3b", 0.96),
      paving: surfaceMaterial(this.scene, "paving", "#777f7f", 0.96),
      timber: surfaceMaterial(this.scene, "timber", "#9c6235", 0.92),
      wall: surfaceMaterial(this.scene, "wall", "#ebe9e0", 0.93, 0.42),
      roof: surfaceMaterial(this.scene, "roof", "#2c3132", 0.74, 0.62),
      glass: surfaceMaterial(this.scene, "glass", "#182124", 0.36, 0.78),
      foundation: surfaceMaterial(this.scene, "foundation", "#929da0", 0.94),
      water: surfaceMaterial(this.scene, "water", "#398cff", 0.72),
      sewer: surfaceMaterial(this.scene, "sewer", "#a76b35", 0.8),
      rainwater: surfaceMaterial(this.scene, "rainwater", "#4aae7a", 0.8),
      electricity: surfaceMaterial(this.scene, "electricity", "#ec4ec6", 0.72),
      contextNetworks: surfaceMaterial(this.scene, "context-networks", "#62d8ff", 0.72),
      fence: surfaceMaterial(this.scene, "fence", "#252a2c", 0.92, 0.7),
      hedge: surfaceMaterial(this.scene, "hedge", "#315d35", 0.96),
      poolWater: surfaceMaterial(this.scene, "pool-water", "#3ebbe0", 0.28, 0.82),
      selection: surfaceMaterial(this.scene, "selection", "#ff5738", 0.55, 0.82),
    };
    this.materials.parcel.disableDepthWrite = true;
    this.materials.selection.emissiveColor = Color3.FromHexString("#58180f");

    this.realisticMaterials = {
      terrain: pbrMaterial(this.scene, "real-terrain", "#ffffff", 0.97),
      grass: pbrMaterial(this.scene, "real-grass", "#ffffff", 0.95),
      parcelBoundary: pbrMaterial(
        this.scene,
        "real-parcel-boundary",
        "#f1eadb",
        0.92,
        0,
        0.86,
      ),
      parcelBoundarySubject: pbrMaterial(
        this.scene,
        "real-parcel-boundary-subject",
        "#ff6b50",
        0.78,
        0,
        0.98,
      ),
      road: pbrMaterial(this.scene, "real-road", "#7c8283", 0.94),
      roadReserve: pbrMaterial(this.scene, "real-road-reserve", "#807e72", 0.98),
      paving: pbrMaterial(this.scene, "real-paving", "#c9cbc6", 0.88),
      pavingEntry: pbrMaterial(this.scene, "real-paving-entry", "#d6d2c8", 0.9),
      gravel: pbrMaterial(this.scene, "real-gravel", "#ffffff", 0.96),
      timber: pbrMaterial(this.scene, "real-timber", "#ffffff", 0.68),
      timberDark: pbrMaterial(this.scene, "real-timber-dark", "#8a5c30", 0.74),
      deck: pbrMaterial(this.scene, "real-deck", "#ffffff", 0.74),
      wall: pbrMaterial(this.scene, "real-wall", "#ffffff", 0.92),
      soffit: pbrMaterial(this.scene, "real-soffit", "#f4f2ec", 0.9),
      concrete: pbrMaterial(this.scene, "real-concrete", "#ffffff", 0.86),
      roof: pbrMaterial(this.scene, "real-roof", "#ffffff", 0.52, 0.18),
      roofEdge: pbrMaterial(this.scene, "real-roof-edge", "#282d31", 0.48, 0.28),
      glass: pbrMaterial(this.scene, "real-glass", "#819491", 0.045, 0, 0.34),
      glassFrame: pbrMaterial(this.scene, "real-glass-frame", "#26292b", 0.34, 0.55),
      glassFrameWood: pbrMaterial(this.scene, "real-glass-frame-wood", "#77522c", 0.5),
      solar: pbrMaterial(this.scene, "real-solar", "#0b1824", 0.16, 0),
      solarGrid: pbrMaterial(this.scene, "real-solar-grid", "#aeb6ba", 0.26, 0.82),
      chimney: pbrMaterial(this.scene, "real-chimney", "#b8b8b3", 0.78, 0.03),
      chimneyMetal: pbrMaterial(this.scene, "real-chimney-metal", "#b8c0c1", 0.24, 0.88),
      fenceMetal: pbrMaterial(this.scene, "real-fence-metal", "#252a2c", 0.66, 0.05),
      fenceTrack: pbrMaterial(this.scene, "real-fence-track", "#8d9496", 0.32, 0.72),
      hedgeDark: pbrMaterial(this.scene, "real-hedge-dark", "#244a2b", 0.94),
      hedgeMid: pbrMaterial(this.scene, "real-hedge-mid", "#356438", 0.92),
      hedgeLight: pbrMaterial(this.scene, "real-hedge-light", "#477746", 0.9),
      poolWater: pbrMaterial(this.scene, "real-pool-water", "#72c3ce", 0.035, 0, 0.76),
      poolBasin: pbrMaterial(this.scene, "real-pool-basin", "#d3e3e1", 0.7),
      poolTile: pbrMaterial(this.scene, "real-pool-tile", "#d8e8e6", 0.64),
      poolLed: pbrMaterial(this.scene, "real-pool-led", "#d7fbff", 0.12),
      mulch: pbrMaterial(this.scene, "real-mulch", "#2e2317", 1),
      stone: pbrMaterial(this.scene, "real-stone", "#d6d2c6", 0.9),
      fabric: pbrMaterial(this.scene, "real-fabric", "#e6e2d8", 0.95),
      upholsteryDark: pbrMaterial(this.scene, "real-upholstery-dark", "#22292a", 0.94),
      curtain: pbrMaterial(this.scene, "real-curtain", "#e2e0d8", 0.96, 0, 0.6),
      sillInterior: pbrMaterial(this.scene, "real-sill-interior", "#f4f3ef", 0.42),
      interiorDark: pbrMaterial(this.scene, "real-interior-dark", "#1a2325", 0.75),
      warmInterior: pbrMaterial(this.scene, "real-interior", "#d5a76a", 0.82),
      plantGrass: pbrMaterial(this.scene, "real-plant-grass", "#ffffff", 0.9),
      plantPerennial: pbrMaterial(this.scene, "real-plant-perennial", "#ffffff", 0.9),
    };
    this.realisticMaterials.glass.indexOfRefraction = 1.5;
    // Preserve the dielectric Fresnel response. The old 0.06 factor almost
    // removed reflections, which made the glazing read as flat black panels.
    this.realisticMaterials.glass.metallicF0Factor = 1;
    this.realisticMaterials.glass.environmentIntensity = 1.55;
    this.realisticMaterials.glass.useSpecularOverAlpha = true;
    this.realisticMaterials.glass.backFaceCulling = true;
    this.realisticMaterials.glass.needDepthPrePass = true;
    // Real transmission: the glazing is alpha-blended over whatever stands
    // behind it — the fitted-out interior from the garden, the terrace and
    // garden from inside. The former IBL refraction only ever showed the
    // panorama, which read as fog from the walkthrough.
    this.realisticMaterials.glass.subSurface.isRefractionEnabled = false;
    this.realisticMaterials.glass.transparencyMode =
      PBRMaterial.PBRMATERIAL_ALPHABLEND;
    this.realisticMaterials.glass.alpha = 0.14;
    this.realisticMaterials.glass.albedoColor = Color3.FromHexString("#8fa6a3");
    this.realisticMaterials.glass.separateCullingPass = true;
    this.realisticMaterials.glass.clearCoat.isEnabled = true;
    this.realisticMaterials.glass.clearCoat.intensity = 0.9;
    this.realisticMaterials.glass.clearCoat.roughness = 0.035;
    this.realisticMaterials.warmInterior.emissiveColor =
      Color3.FromHexString("#4b3418");
    this.realisticMaterials.poolWater.indexOfRefraction = 1.333;
    this.realisticMaterials.poolWater.environmentIntensity = 1.65;
    this.realisticMaterials.poolWater.useSpecularOverAlpha = true;
    this.realisticMaterials.poolWater.needDepthPrePass = true;
    this.realisticMaterials.poolWater.subSurface.isRefractionEnabled = true;
    this.realisticMaterials.poolWater.subSurface.refractionTexture = environment;
    this.realisticMaterials.poolWater.subSurface.indexOfRefraction = 1.333;
    this.realisticMaterials.poolWater.subSurface.linkRefractionWithTransparency = true;
    this.realisticMaterials.poolWater.subSurface.minimumThickness = 0.55;
    this.realisticMaterials.poolWater.subSurface.maximumThickness = 1.4;
    this.realisticMaterials.poolWater.subSurface.useThicknessAsDepth = true;
    this.realisticMaterials.poolWater.subSurface.tintColor =
      Color3.FromHexString("#54aeb8");
    this.realisticMaterials.poolWater.subSurface.tintColorAtDistance = 2.2;
    this.realisticMaterials.poolWater.emissiveColor = Color3.Black();
    this.realisticMaterials.poolLed.emissiveColor =
      Color3.FromHexString("#21484d");

    for (const material of [
      this.realisticMaterials.glassFrame,
      this.realisticMaterials.roofEdge,
      this.realisticMaterials.fenceMetal,
      this.realisticMaterials.solar,
    ]) {
      material.clearCoat.isEnabled = true;
      material.clearCoat.intensity = 0.38;
      material.clearCoat.roughness = 0.28;
    }

    const solarCells = new DynamicTexture(
      "photovoltaic-cell-grid",
      { width: 1024, height: 640 },
      this.scene,
      true,
    );
    const solarContext = solarCells.getContext();
    solarContext.fillStyle = "#07141f";
    solarContext.fillRect(0, 0, 1024, 640);
    const cellColumns = 10;
    const cellRows = 6;
    const cellGap = 7;
    const cellWidth = 1024 / cellColumns;
    const cellHeight = 640 / cellRows;
    for (let row = 0; row < cellRows; row += 1) {
      for (let column = 0; column < cellColumns; column += 1) {
        const gradient = solarContext.createLinearGradient(
          column * cellWidth,
          row * cellHeight,
          (column + 1) * cellWidth,
          (row + 1) * cellHeight,
        );
        gradient.addColorStop(0, row % 2 === 0 ? "#102d43" : "#0c273b");
        gradient.addColorStop(0.52, "#183d55");
        gradient.addColorStop(1, "#091e31");
        solarContext.fillStyle = gradient;
        solarContext.fillRect(
          column * cellWidth + cellGap,
          row * cellHeight + cellGap,
          cellWidth - cellGap * 2,
          cellHeight - cellGap * 2,
        );
        solarContext.strokeStyle = "rgba(189, 216, 225, 0.36)";
        solarContext.lineWidth = 2;
        solarContext.strokeRect(
          column * cellWidth + cellGap,
          row * cellHeight + cellGap,
          cellWidth - cellGap * 2,
          cellHeight - cellGap * 2,
        );
      }
    }
    solarContext.strokeStyle = "rgba(224, 235, 238, 0.55)";
    solarContext.lineWidth = 3;
    for (const x of [1024 / 3, (1024 * 2) / 3]) {
      solarContext.beginPath();
      solarContext.moveTo(x, 0);
      solarContext.lineTo(x, 640);
      solarContext.stroke();
    }
    solarCells.update(false);
    solarCells.anisotropicFilteringLevel = this.renderQuality.anisotropy;
    this.realisticMaterials.solar.albedoColor = Color3.White();
    this.realisticMaterials.solar.albedoTexture = solarCells;
    this.realisticMaterials.solar.environmentIntensity = 1.28;
    this.realisticMaterials.solar.clearCoat.intensity = 0.9;
    this.realisticMaterials.solar.clearCoat.roughness = 0.07;

    const paverTexture = new DynamicTexture(
      "street-grey-block-paver-albedo",
      { width: 1024, height: 1024 },
      this.scene,
      true,
    );
    const paverContext = paverTexture.getContext();
    paverContext.fillStyle = "#525755";
    paverContext.fillRect(0, 0, 1024, 1024);
    const paverLengthPx = 128;
    const paverWidthPx = 64;
    const paverJointPx =
      (ROAD_CONTEXT.surfaceFinish.visualJointMm /
        ROAD_CONTEXT.surfaceFinish.visualModuleMm.length) *
      paverLengthPx;
    const paverJointInsetPx = paverJointPx / 2;
    for (let row = 0; row < 16; row += 1) {
      const offset = row % 2 === 0 ? 0 : -paverLengthPx / 2;
      for (let column = -1; column < 9; column += 1) {
        const x = column * paverLengthPx + offset + paverJointInsetPx;
        const y = row * paverWidthPx + paverJointInsetPx;
        const variation = ((row * 31 + column * 47 + 97) % 25) - 12;
        const base = 151 + variation;
        const gradient = paverContext.createLinearGradient(
          x,
          y,
          x,
          y + paverWidthPx,
        );
        gradient.addColorStop(0, `rgb(${base + 10}, ${base + 12}, ${base + 11})`);
        gradient.addColorStop(0.42, `rgb(${base + 3}, ${base + 5}, ${base + 4})`);
        gradient.addColorStop(1, `rgb(${base - 5}, ${base - 3}, ${base - 4})`);
        paverContext.fillStyle = gradient;
        paverContext.fillRect(
          x,
          y,
          paverLengthPx - paverJointPx,
          paverWidthPx - paverJointPx,
        );
        paverContext.strokeStyle = "rgba(229, 232, 228, 0.15)";
        paverContext.lineWidth = 1;
        paverContext.strokeRect(
          x + 1,
          y + 1,
          paverLengthPx - paverJointPx - 2,
          paverWidthPx - paverJointPx - 2,
        );
      }
    }
    // Deterministic mineral aggregate keeps the blocks from reading as a flat
    // checkerboard without introducing unstable random output between loads.
    for (let index = 0; index < 22_000; index += 1) {
      const x = (index * 73 + (index % 37) * 19) % 1024;
      const y = (index * 151 + (index % 53) * 11) % 1024;
      const tone = 84 + ((index * 29) % 72);
      paverContext.fillStyle = `rgba(${tone}, ${tone + 2}, ${tone + 1}, ${0.035 + (index % 5) * 0.012})`;
      const size = index % 13 === 0 ? 2 : 1;
      paverContext.fillRect(x, y, size, size);
    }
    paverTexture.update(false);
    paverTexture.wrapU = Texture.WRAP_ADDRESS;
    paverTexture.wrapV = Texture.WRAP_ADDRESS;
    paverTexture.anisotropicFilteringLevel = this.renderQuality.anisotropy;

    const paverNormal = new DynamicTexture(
      "street-grey-block-paver-normal",
      { width: 1024, height: 1024 },
      this.scene,
      true,
    );
    paverNormal.gammaSpace = false;
    const normalContext = paverNormal.getContext();
    normalContext.fillStyle = "#8080ff";
    normalContext.fillRect(0, 0, 1024, 1024);
    for (let row = 0; row < 16; row += 1) {
      const offset = row % 2 === 0 ? 0 : -paverLengthPx / 2;
      for (let column = -1; column < 9; column += 1) {
        const x = column * paverLengthPx + offset + paverJointInsetPx;
        const y = row * paverWidthPx + paverJointInsetPx;
        const width = paverLengthPx - paverJointPx;
        const height = paverWidthPx - paverJointPx;
        normalContext.fillStyle = "#8080ff";
        normalContext.fillRect(x, y, width, height);
        normalContext.fillStyle = "#8096fa";
        normalContext.fillRect(x, y, width, 3);
        normalContext.fillStyle = "#806afa";
        normalContext.fillRect(x, y + height - 3, width, 3);
        normalContext.fillStyle = "#9680fa";
        normalContext.fillRect(x, y, 3, height);
        normalContext.fillStyle = "#6a80fa";
        normalContext.fillRect(x + width - 3, y, 3, height);
      }
    }
    paverNormal.update(false);
    paverNormal.wrapU = Texture.WRAP_ADDRESS;
    paverNormal.wrapV = Texture.WRAP_ADDRESS;
    paverNormal.anisotropicFilteringLevel = this.renderQuality.anisotropy;
    this.realisticMaterials.road.albedoColor = Color3.White();
    this.realisticMaterials.road.albedoTexture = paverTexture;
    this.realisticMaterials.road.bumpTexture = paverNormal;
    this.realisticMaterials.road.environmentIntensity = 0.56;
    // These triangulated ground rings use a flipped plan-to-world Z axis. Keep
    // both faces visible so the realistic PBR pass cannot cull the carriageway
    // and reveal the broad green terrain below it.
    this.realisticMaterials.road.backFaceCulling = false;
    this.realisticMaterials.roadReserve.backFaceCulling = false;

    this.poolWaterNormal = new Texture(
      "/assets/textures/pool-water-normal.png",
      this.scene,
      false,
      false,
      Texture.TRILINEAR_SAMPLINGMODE,
    );
    this.poolWaterNormal.gammaSpace = false;
    this.poolWaterNormal.uScale = 2.35;
    this.poolWaterNormal.vScale = 1.65;
    this.poolWaterNormal.level = 0.42;
    this.poolWaterNormal.anisotropicFilteringLevel =
      this.renderQuality.anisotropy;
    this.realisticMaterials.poolWater.bumpTexture = this.poolWaterNormal;

    this.applyTexture(this.realisticMaterials.grass, "lawn-albedo", 12, 10, "lawn-normal", 0.4);
    this.applyTexture(
      this.realisticMaterials.terrain,
      "lawn-albedo",
      78,
      66,
      "lawn-normal",
      0.3,
    );
    this.applyTexture(this.realisticMaterials.wall, "plaster-white-albedo", 3.2, 1.4, "plaster-white-normal", 0.55);
    this.applyTexture(this.realisticMaterials.timber, "larch-albedo", 1.15, 1, "larch-normal", 0.85);
    this.applyTexture(this.realisticMaterials.deck, "deck-plank-albedo", 2.4, 1, "deck-plank-normal", 0.35);
    this.applyTexture(this.realisticMaterials.roof, "metal-anthracite-albedo", 7, 5, "metal-anthracite-normal", 0.3);
    this.realisticMaterials.roof.environmentIntensity = 0.35;
    this.realisticMaterials.roofEdge.environmentIntensity = 0.4;
    this.realisticMaterials.fenceMetal.environmentIntensity = 0.55;
    // Material tints keep the procedural source textures plausible under the
    // neutral HDRI: warm beige plaster, natural larch and a maintained lawn
    // without the synthetic pure-white texture multiplier.
    this.realisticMaterials.wall.albedoColor = Color3.FromHexString("#f3efe5");
    this.realisticMaterials.timber.albedoColor = Color3.FromHexString("#e2c39f");
    this.realisticMaterials.deck.albedoColor = Color3.FromHexString("#d7c4aa");
    this.realisticMaterials.grass.albedoColor = Color3.FromHexString("#c6d2bc");
    this.realisticMaterials.terrain.albedoColor = Color3.FromHexString("#aebca5");
    this.realisticMaterials.roadReserve.albedoColor =
      Color3.FromHexString("#d6c9ae");
    this.realisticMaterials.roadReserve.environmentIntensity = 0.72;
    this.applyTexture(
      this.realisticMaterials.fenceMetal,
      "metal-anthracite-albedo",
      9,
      6,
      "metal-anthracite-normal",
      0.22,
    );
    this.applyTexture(this.realisticMaterials.gravel, "gravel-albedo", 6, 1.1, "gravel-normal", 0.9);
    this.applyTexture(this.realisticMaterials.concrete, "concrete-albedo", 2.2, 2.2, "concrete-normal", 0.5);
    this.applyTexture(this.realisticMaterials.chimney, "concrete-albedo", 1.2, 3, "concrete-normal", 0.24);
    this.applyTexture(this.realisticMaterials.paving, "concrete-albedo", 5, 2.5, "concrete-normal", 0.45);
    this.applyTexture(this.realisticMaterials.pavingEntry, "concrete-albedo", 3.2, 5.8, "concrete-normal", 0.34);
    this.applyTexture(this.realisticMaterials.roadReserve, "gravel-albedo", 12, 3.4, "gravel-normal", 0.72);
    for (const [index, material] of [
      this.realisticMaterials.hedgeDark,
      this.realisticMaterials.hedgeMid,
      this.realisticMaterials.hedgeLight,
    ].entries()) {
      const foliage = new Texture(
        "/assets/textures/hedge-privet-albedo.png",
        this.scene,
        false,
        false,
        Texture.TRILINEAR_SAMPLINGMODE,
      );
      foliage.uScale = 1.7 + index * 0.13;
      foliage.vScale = 1.35 + index * 0.11;
      foliage.uOffset = index * 0.217;
      foliage.vOffset = index * 0.137;
      foliage.anisotropicFilteringLevel = this.renderQuality.anisotropy;
      material.albedoColor = Color3.FromHexString(
        ["#b9cab7", "#d1ddca", "#e0e8d8"][index],
      );
      material.albedoTexture = foliage;
      material.environmentIntensity = 0.68;
      material.subSurface.isTranslucencyEnabled = true;
      material.subSurface.translucencyIntensity = 0.16;
      material.subSurface.useAlbedoToTintTranslucency = true;
    }
    this.configurePlantCardMaterial(
      this.realisticMaterials.plantGrass,
      "/assets/vegetation/ornamental-grass-card.png",
    );
    this.configurePlantCardMaterial(
      this.realisticMaterials.plantPerennial,
      "/assets/vegetation/perennial-cluster-card.png",
    );

    for (const layer of LAYERS) this.layerMeshes.set(layer.id, []);
    this.buildTerrainAndGrid();
    this.buildCadastre();
    this.buildStreetAndSite();
    this.buildHouse();
    this.doors.assertInventory(ARCHITECTURAL_DOOR_INVENTORY);
    this.buildFence();
    this.buildLandscape();
    this.buildUtilities();
    if (this.cascadedShadowGenerator) {
      this.cascadedShadowGenerator.freezeShadowCastersBoundingInfo = true;
    }

    this.scene.onPointerDown = (event) => {
      if (this.garageCinematicActive) return;
      if (this.navigationMode === "orbit") this.cancelOrbitZoomGlide();
      if (
        this.navigationMode === "walk" &&
        this.scene.activeCamera === this.avatar.camera
      ) {
        this.avatar.noteCameraInput();
      }
      this.activePointers.add(event.pointerId);
      if (this.pointerGesture) {
        this.pointerGesture.maximumPointers = Math.max(
          this.pointerGesture.maximumPointers,
          this.activePointers.size,
        );
        return;
      }
      this.pointerGesture = {
        pointerId: event.pointerId,
        button: event.button,
        startedAt: performance.now(),
        startX: event.clientX,
        startY: event.clientY,
        maximumPointers: this.activePointers.size,
        travelPx: 0,
      };
    };
    this.scene.onPointerMove = (event) => {
      if (this.garageCinematicActive) return;
      const gesture = this.pointerGesture;
      if (!gesture || gesture.pointerId !== event.pointerId) return;
      if (
        this.navigationMode === "walk" &&
        this.scene.activeCamera === this.avatar.camera
      ) {
        this.avatar.noteCameraInput();
      }
      gesture.travelPx = Math.max(
        gesture.travelPx,
        Math.hypot(
          event.clientX - gesture.startX,
          event.clientY - gesture.startY,
        ),
      );
      gesture.maximumPointers = Math.max(
        gesture.maximumPointers,
        this.activePointers.size,
      );
    };
    this.scene.onPointerUp = (event, pick) => {
      if (this.garageCinematicActive) return;
      const gesture = this.pointerGesture;
      this.activePointers.delete(event.pointerId);
      if (!gesture || gesture.pointerId !== event.pointerId) return;
      gesture.travelPx = Math.max(
        gesture.travelPx,
        Math.hypot(
          event.clientX - gesture.startX,
          event.clientY - gesture.startY,
        ),
      );
      if (
        this.navigationMode === "orbit" &&
        isSelectionTap({
          travelPx: gesture.travelPx,
          durationMs: performance.now() - gesture.startedAt,
          maximumPointers: gesture.maximumPointers,
          button: gesture.button,
        })
      ) {
        const id = pick?.pickedMesh?.metadata?.entityId;
        if (typeof id === "string") this.onSelect(id);
      } else if (
        this.navigationMode === "walk" &&
        isSelectionTap({
          travelPx: gesture.travelPx,
          durationMs: performance.now() - gesture.startedAt,
          maximumPointers: gesture.maximumPointers,
          button: gesture.button,
        })
      ) {
        const doorId = pick?.pickedMesh?.metadata?.doorId;
        if (
          typeof doorId === "string" &&
          this.doors.getInteraction()?.id === doorId
        ) {
          this.toggleDoorInteraction();
        }
      }
      this.pointerGesture = null;
    };

    this.canvas.addEventListener("keydown", this.handleFlightKeyDown);
    this.canvas.addEventListener("keyup", this.handleFlightKeyUp);
    this.canvas.addEventListener("blur", this.clearFlightInput);
    this.canvas.addEventListener("pointercancel", this.cancelPointerGesture);
    this.canvas.addEventListener("wheel", this.handleCanvasWheel, {
      passive: false,
    });
    this.scene.onBeforeRenderObservable.add(() => {
      this.updateGarageParkingAnimation();
      this.updateDoorMotion();
      this.updateFlightMotion();
      this.updateOrbitZoomGlide();
      this.updateParcelLabelScale();
      this.animateWaterSurface();
      if (this.canvas.dataset.navigationMode !== this.navigationMode) {
        this.canvas.dataset.navigationMode = this.navigationMode;
      }
      const cameraRadius = this.orbitCamera.radius.toFixed(3);
      if (this.canvas.dataset.cameraRadius !== cameraRadius) {
        this.canvas.dataset.cameraRadius = cameraRadius;
      }
    });

    const render = () => this.scene.render();
    this.engine.runRenderLoop(render);
    this.onVisibilityChange = () => {
      if (document.hidden) {
        this.clearFlightInput();
        this.engine.stopRenderLoop(render);
      }
      else this.engine.runRenderLoop(render);
    };
    document.addEventListener("visibilitychange", this.onVisibilityChange);
  }

  private deriveCurrentRenderQuality() {
    return deriveRenderQualityProfile({
      widthPx: this.canvas.clientWidth,
      heightPx: this.canvas.clientHeight,
      devicePixelRatio: window.devicePixelRatio,
      maxMsaaSamples: this.engine.getCaps().maxMSAASamples,
      isCoarsePointer: window.matchMedia("(pointer: coarse)").matches,
      deviceMemoryGb: (
        navigator as Navigator & { readonly deviceMemory?: number }
      ).deviceMemory,
    });
  }

  private updateParcelLabelScale() {
    const scale =
      this.navigationMode === "orbit"
        ? parcelLabelScaleForRadius(this.orbitCamera.radius)
        : 1;
    for (const label of this.parcelLabelMeshes) {
      if (!label.isDisposed() && label.scaling.x !== scale) {
        label.scaling.set(scale, 1, scale);
      }
    }
  }

  private readonly handleFlightKeyDown = (event: KeyboardEvent) => {
    if (this.garageCinematicActive) {
      if (
        event.code === "KeyE" ||
        event.code.startsWith("Shift") ||
        event.code.startsWith("Alt") ||
        flightCommandForCode(event.code)
      ) {
        event.preventDefault();
      }
      return;
    }
    if (
      (this.navigationMode !== "flight" && this.navigationMode !== "walk") ||
      event.metaKey ||
      event.ctrlKey
    ) {
      return;
    }
    if (this.navigationMode === "walk" && event.code === "KeyE") {
      if (!event.repeat) this.toggleDoorInteraction();
      event.preventDefault();
      return;
    }
    if (event.code.startsWith("Shift") || event.code.startsWith("Alt")) {
      this.flightModifierCodes.add(event.code);
      event.preventDefault();
      return;
    }
    const command = flightCommandForCode(event.code);
    if (!command) return;
    this.keyboardFlightCommands.add(command);
    event.preventDefault();
  };

  private readonly handleFlightKeyUp = (event: KeyboardEvent) => {
    if (this.garageCinematicActive) {
      this.clearFlightInput();
      return;
    }
    if (this.navigationMode === "walk" && event.code === "KeyE") {
      event.preventDefault();
      return;
    }
    if (event.code.startsWith("Shift") || event.code.startsWith("Alt")) {
      this.flightModifierCodes.delete(event.code);
      return;
    }
    const command = flightCommandForCode(event.code);
    if (command) this.keyboardFlightCommands.delete(command);
  };

  private readonly clearFlightInput = () => {
    this.keyboardFlightCommands.clear();
    this.manualFlightCommands.clear();
    this.flightModifierCodes.clear();
    this.flightCamera.cameraDirection.setAll(0);
    this.flightCamera.cameraRotation.setAll(0);
  };

  private readonly cancelPointerGesture = (event: PointerEvent) => {
    this.activePointers.delete(event.pointerId);
    if (this.pointerGesture?.pointerId === event.pointerId) {
      this.pointerGesture = null;
    }
  };

  /**
   * Exponential orbit zoom and flight dolly driven straight from the DOM
   * wheel stream. Trackpad scroll, momentum, physical notches and the
   * ctrl-key pinch all normalize into pixels and compose multiplicatively,
   * which keeps the response identical at every radius.
   */
  private readonly handleCanvasWheel = (event: WheelEvent) => {
    event.preventDefault();
    event.stopPropagation();
    if (this.garageCinematicActive) return;
    const pixels = normalizeWheelPixels(event);
    if (!pixels) return;
    if (this.navigationMode === "walk") {
      if (this.scene.activeCamera === this.avatar.camera) this.avatar.zoom(pixels);
      return;
    }
    if (this.navigationMode === "flight") {
      const distanceM = flightWheelDollyDistanceM(pixels);
      if (!distanceM) return;
      const forward = this.flightCamera.getForwardRay(1).direction;
      const next = integrateFlightDolly(
        this.flightCamera.position,
        { x: forward.x, y: forward.y, z: forward.z },
        distanceM,
      );
      this.flightCamera.position.set(next.x, next.y, next.z);
      return;
    }
    const gesture = wheelZoomGesture(event);
    const multiplier = orbitZoomMultiplier(pixels, gesture);
    const pending = this.orbitZoomActive
      ? this.orbitZoomTargetM
      : this.orbitCamera.radius;
    this.orbitZoomTargetM = clampOrbitRadius(pending * multiplier);
    this.orbitZoomActive =
      Math.abs(this.orbitZoomTargetM - this.orbitCamera.radius) >
      ORBIT_ZOOM.settleEpsilonM;
  };

  /** Framerate-independent exponential glide toward the zoom target. */
  private updateOrbitZoomGlide() {
    if (this.navigationMode !== "orbit") return;
    if (!this.orbitZoomActive) {
      // Follow native touch pinch and any external/programmatic camera move.
      this.orbitZoomTargetM = this.orbitCamera.radius;
      return;
    }
    const step = stepOrbitZoom(
      this.orbitCamera.radius,
      this.orbitZoomTargetM,
      this.engine.getDeltaTime(),
    );
    this.orbitCamera.radius = step.radiusM;
    this.orbitZoomActive = !step.settled;
  }

  private cancelOrbitZoomGlide() {
    this.orbitZoomActive = false;
    this.orbitZoomTargetM = this.orbitCamera.radius;
  }

  /** Fixed eye on the street with a pan that keeps the moving car in frame. */
  private configureGarageCinematicCamera(
    pose: GarageAnimationFrame["vehiclePose"],
  ) {
    const mobile = this.canvas.clientWidth < 600;
    this.garageCinematicCamera.position.set(
      xM(GARAGE_VEHICLE.route.queueMm.x) + (mobile ? 2.2 : 3.4),
      mobile ? 3.25 : 2.85,
      zM(GARAGE_VEHICLE.route.streetStartMm.y) + (mobile ? 11.2 : 7.2),
    );
    this.garageCinematicCamera.fov = mobile ? 0.72 : 0.58;
    this.garageCinematicCamera.setTarget(
      new Vector3(
        xM(pose.centerMm.x),
        garageVehicleSurfaceElevationM(pose.centerMm) + 0.82,
        zM(pose.centerMm.y),
      ),
    );
  }

  private ensureGarageCinematicAvatarClearance() {
    const pose = this.avatar.pose;
    const pointMm = {
      x: Math.round(pose.x * 1_000 + SCENE_CENTER_MM.x),
      y: Math.round(SCENE_CENTER_MM.y - pose.z * 1_000),
    };
    if (!garageCinematicRequiresSafePosition(pointMm)) {
      this.canvas.dataset.garageAvatarRelocated = "false";
      return;
    }
    const garage = INTERIOR_ROOMS.find(
      (room) => room.id === GARAGE_VEHICLE.roomId,
    );
    if (!garage) return;
    const standing = garage.standingPointMm;
    const look = walkLookTargetMm(garage);
    const yaw = Math.atan2(
      xM(look.x) - xM(standing.x),
      zM(look.y) - zM(standing.y),
    );
    this.avatar.place(xM(standing.x), zM(standing.y), yaw);
    this.flightHeading = { x: Math.sin(yaw), z: Math.cos(yaw) };
    this.applyWalkView();
    this.canvas.dataset.garageAvatarRelocated = "true";
  }

  private beginGarageCinematic() {
    if (
      this.garageCinematicActive ||
      this.navigationMode !== "walk" ||
      this.getWalkRoom()?.id !== GARAGE_VEHICLE.roomId
    ) {
      return false;
    }
    this.ensureGarageCinematicAvatarClearance();
    const active = this.scene.activeCamera;
    if (active !== this.avatar.camera && active !== this.flightCamera) {
      return false;
    }
    this.clearFlightInput();
    this.activePointers.clear();
    this.pointerGesture = null;
    active.detachControl();
    this.garageCinematicReturnCamera = active;
    this.garageCinematicActive = true;
    this.configureGarageCinematicCamera(
      garageAnimationFrame(
        garageActionForState(this.garageParkingState) ?? "park",
        0,
      ).vehiclePose,
    );
    this.scene.activeCamera = this.garageCinematicCamera;
    this.canvas.dataset.garageCameraView = "street";
    return true;
  }

  private endGarageCinematic(restoreControl = true) {
    if (!this.garageCinematicActive) return;
    const returnCamera = this.garageCinematicReturnCamera;
    this.garageCinematicActive = false;
    this.garageCinematicReturnCamera = null;
    this.garageCinematicCamera.detachControl();
    this.clearFlightInput();
    this.activePointers.clear();
    this.pointerGesture = null;
    this.canvas.dataset.garageCameraView = "garage";
    if (!restoreControl || !returnCamera) return;
    if (returnCamera === this.avatar.camera) {
      this.flightCamera.detachControl();
      this.avatar.setFirstPerson(false);
      this.scene.activeCamera = returnCamera;
      returnCamera.attachControl(this.canvas, true);
    } else {
      this.avatar.camera.detachControl();
      this.avatar.setFirstPerson(true);
      this.scene.activeCamera = returnCamera;
      returnCamera.attachControl(false);
    }
    this.canvas.focus({ preventScroll: true });
  }

  private applyGarageAnimationFrame(frame: GarageAnimationFrame) {
    const previousState = this.garageParkingState;
    const stateChanged = frame.state !== previousState;
    if (
      stateChanged &&
      (frame.state === "opening-to-park" ||
        frame.state === "opening-to-leave")
    ) {
      this.doors.setOpen(GARAGE_VEHICLE.garageDoorId, true);
    }
    if (
      stateChanged &&
      (frame.state === "closing-after-park" ||
        frame.state === "closing-after-leave")
    ) {
      this.doors.setOpen(GARAGE_VEHICLE.garageDoorId, false);
    }

    const root = this.garageVehicleRoot;
    if (root) {
      root.setEnabled(frame.vehicleVisible);
      if (frame.vehicleVisible) {
        const current = frame.vehiclePose;
        const previous = this.garageVehicleLastPose;
        if (previous) {
          const distanceM =
            Math.hypot(
              current.centerMm.x - previous.centerMm.x,
              current.centerMm.y - previous.centerMm.y,
            ) * MM_TO_M;
          const direction = current.motion === "reverse" ? -1 : 1;
          this.garageVehicleWheelAngle +=
            (distanceM / 0.345) * direction;
          if (distanceM > 0.005 && current.motion !== "still") {
            let headingDelta = current.headingRad - previous.headingRad;
            while (headingDelta > Math.PI) headingDelta -= Math.PI * 2;
            while (headingDelta < -Math.PI) headingDelta += Math.PI * 2;
            const wheelbaseM = GARAGE_VEHICLE.dimensionsMm.wheelbase * MM_TO_M;
            this.garageVehicleSteeringAngle = Math.max(
              -0.48,
              Math.min(
                0.48,
                Math.atan((wheelbaseM * headingDelta) / (distanceM * direction)),
              ),
            );
          }
        } else {
          this.garageVehicleSteeringAngle = 0;
        }
        root.position.set(
          xM(current.centerMm.x),
          garageVehicleSurfaceElevationM(current.centerMm) -
            GARAGE_VEHICLE.wheelGroundOffsetM,
          zM(current.centerMm.y),
        );
        root.rotation.y = current.headingRad;
        for (const steering of this.garageVehicleFrontSteering) {
          steering.rotation.y = this.garageVehicleSteeringAngle;
        }
        for (const wheel of this.garageVehicleWheelSpins) {
          wheel.rotation.z = this.garageVehicleWheelAngle;
        }
        this.avatar.invalidateDynamicCameraOccluders();
      }
    }
    if (this.garageVehicleBrakeMaterial) {
      const sequenceRunning = Boolean(this.garageVehicleAction) && !frame.complete;
      const intensity = !frame.vehicleVisible
        ? 0
        : sequenceRunning && frame.vehiclePose.motion === "still"
          ? 0.94
          : sequenceRunning
            ? 0.28
            : frame.state === "parked"
              ? 0.08
              : 0;
      this.garageVehicleBrakeMaterial.emissiveColor =
        Color3.FromHexString("#d3121c").scale(intensity);
    }
    if (this.garageVehicleHeadlightMaterial) {
      const intensity =
        frame.vehicleVisible && this.garageVehicleAction && !frame.complete
          ? 0.72
          : frame.state === "parked"
            ? 0.06
            : 0;
      this.garageVehicleHeadlightMaterial.emissiveColor =
        Color3.FromHexString("#bddfff").scale(intensity);
    }
    this.garageVehicleLastPose = frame.vehicleVisible
      ? frame.vehiclePose
      : null;
    this.garageParkingState = frame.state;
    this.garageDoorProgress = frame.doorProgress;
    this.canvas.dataset.garageParkingState = frame.state;
    this.canvas.dataset.garageVehicleVisible = frame.vehicleVisible
      ? "true"
      : "false";
    if (this.garageCinematicActive) {
      this.configureGarageCinematicCamera(frame.vehiclePose);
    }
  }

  /** Render-loop sequence; capped frame deltas prevent jumps after tab sleep. */
  private updateGarageParkingAnimation() {
    const action = this.garageVehicleAction;
    if (!action) {
      this.canvas.dataset.garageParkingState = this.garageParkingState;
      return;
    }
    this.garageVehicleElapsedMs += Math.min(
      50,
      Math.max(0, this.engine.getDeltaTime()),
    );
    const frame = garageAnimationFrame(action, this.garageVehicleElapsedMs);
    this.applyGarageAnimationFrame(frame);
    if (!frame.complete) return;

    const door = this.doors
      .debugState()
      .find(({ id }) => id === GARAGE_VEHICLE.garageDoorId);
    if (door && door.progress > 0.0001) {
      // If a person stood in the closing plane, preserve the safety stop and
      // retry only after the doorway becomes clear. Never restart an active
      // close animation on every frame.
      this.garageParkingState =
        action === "park" ? "closing-after-park" : "closing-after-leave";
      this.canvas.dataset.garageParkingState = this.garageParkingState;
      if (door.phase === "OPEN") {
        this.doors.setOpen(GARAGE_VEHICLE.garageDoorId, false);
      }
      return;
    }
    this.garageVehicleAction = null;
    this.endGarageCinematic();
  }

  /** Door transforms and collision matrices settle before walker movement. */
  private updateDoorMotion() {
    if (this.navigationMode === "walk") {
      const pose = this.avatar.pose;
      const fallback = new Vector3(
        Math.sin(pose.yaw),
        0,
        Math.cos(pose.yaw),
      );
      const cameraForward = this.garageCinematicActive
        ? fallback
        : (this.scene.activeCamera?.getForwardRay(1).direction ?? fallback);
      const horizontalLength = Math.hypot(cameraForward.x, cameraForward.z);
      this.doors.setActor({
        position: { x: pose.x, z: pose.z },
        facing:
          horizontalLength > 1e-6
            ? {
                x: cameraForward.x / horizontalLength,
                z: cameraForward.z / horizontalLength,
              }
            : { x: fallback.x, z: fallback.z },
      });
    } else {
      this.doors.setActor(null);
    }
    if (this.doors.update(this.engine.getDeltaTime())) {
      this.avatar.invalidateDynamicCameraOccluders();
    }
    const interaction = this.doors.getInteraction();
    this.canvas.dataset.doorCount = this.doors.count.toString();
    this.canvas.dataset.doorTarget = interaction?.id ?? "";
    this.canvas.dataset.doorPhase = interaction?.phase ?? "";
  }

  private updateFlightMotion() {
    if (this.garageCinematicActive) return;
    if (this.navigationMode === "walk") {
      this.updateWalkMotion();
      return;
    }
    if (this.navigationMode !== "flight") return;
    const forward = this.flightCamera.getForwardRay(1).direction;
    const horizontalLength = Math.hypot(forward.x, forward.z);
    if (horizontalLength > 0.04) {
      this.flightHeading = {
        x: forward.x / horizontalLength,
        z: forward.z / horizontalLength,
      };
    }
    const commands = new Set<FlightCommand>([
      ...this.keyboardFlightCommands,
      ...this.manualFlightCommands,
    ]);
    const next = integrateFlightPosition({
      position: this.flightCamera.position,
      heading: this.flightHeading,
      commands,
      deltaMs: this.engine.getDeltaTime(),
      boost: [...this.flightModifierCodes].some((code) =>
        code.startsWith("Shift"),
      ),
      precision: [...this.flightModifierCodes].some((code) =>
        code.startsWith("Alt"),
      ),
    });
    this.flightCamera.position.set(next.x, next.y, next.z);
    this.flightCamera.rotation.x = Math.max(
      -Math.PI * 0.444,
      Math.min(Math.PI * 0.444, this.flightCamera.rotation.x),
    );
    this.flightCamera.rotation.z = 0;
  }

  private updateWalkMotion() {
    const avatar = this.avatar;
    const commands = new Set<FlightCommand>([
      ...this.keyboardFlightCommands,
      ...this.manualFlightCommands,
    ]);
    const modifiers = {
      boost: [...this.flightModifierCodes].some((code) => code.startsWith("Shift")),
      precision: [...this.flightModifierCodes].some((code) => code.startsWith("Alt")),
    };
    const third = this.scene.activeCamera === avatar.camera;
    if (third) {
      avatar.update(this.engine.getDeltaTime(), commands, modifiers);
    } else {
      // First person: the walker follows the eyes; mouse look stays on the
      // free camera, the body (and its collider) walks underneath it.
      const forward = this.flightCamera.getForwardRay(1).direction;
      const horizontalLength = Math.hypot(forward.x, forward.z);
      if (horizontalLength > 0.04) {
        this.flightHeading = {
          x: forward.x / horizontalLength,
          z: forward.z / horizontalLength,
        };
      }
      avatar.update(this.engine.getDeltaTime(), commands, modifiers, this.flightHeading);
      this.flightCamera.position.copyFrom(avatar.eyePosition);
      this.flightCamera.rotation.x = Math.max(
        -Math.PI * 0.4,
        Math.min(Math.PI * 0.4, this.flightCamera.rotation.x),
      );
      this.flightCamera.rotation.z = 0;
    }
    const room = this.getWalkRoom();
    const roomId = room?.id ?? null;
    if (roomId !== this.walkRoomId) {
      this.walkRoomId = roomId;
      this.canvas.dataset.walkRoom = room?.number ?? "";
    }
  }

  private animateWaterSurface() {
    const deltaSeconds = Math.min(0.05, this.engine.getDeltaTime() / 1000);
    this.poolWaterNormal.uOffset =
      (this.poolWaterNormal.uOffset + deltaSeconds * 0.0065) % 1;
    this.poolWaterNormal.vOffset =
      (this.poolWaterNormal.vOffset - deltaSeconds * 0.0042 + 1) % 1;
  }

  private applyTexture(
    material: PBRMaterial,
    albedoName: string,
    uScale: number,
    vScale: number,
    normalName?: string,
    bumpLevel = 0.6,
  ) {
    const albedo = new Texture(
      `/assets/textures/${albedoName}.jpg`,
      this.scene,
      false,
      false,
      Texture.TRILINEAR_SAMPLINGMODE,
    );
    albedo.uScale = uScale;
    albedo.vScale = vScale;
    albedo.anisotropicFilteringLevel = this.renderQuality.anisotropy;
    material.albedoTexture = albedo;
    if (normalName) {
      const bump = new Texture(
        `/assets/textures/${normalName}.jpg`,
        this.scene,
        false,
        false,
        Texture.TRILINEAR_SAMPLINGMODE,
      );
      bump.uScale = uScale;
      bump.vScale = vScale;
      bump.level = bumpLevel;
      bump.gammaSpace = false;
      bump.anisotropicFilteringLevel = this.renderQuality.anisotropy;
      material.bumpTexture = bump;
      material.forceIrradianceInFragment = true;
    }
    return albedo;
  }

  /** Larch cladding whose 50 mm boards keep true scale on any element. */
  private larchFor(widthM: number, heightM: number, tag: string) {
    const key = `${tag}:${widthM.toFixed(2)}x${heightM.toFixed(2)}`;
    const existing = this.larchClones.get(key);
    if (existing) return existing;
    const clone = this.realisticMaterials.timber.clone(`real-larch-${key}`) as PBRMaterial;
    const baseAlbedo = this.realisticMaterials.timber.albedoTexture as Texture | null;
    const baseBump = this.realisticMaterials.timber.bumpTexture as Texture | null;
    if (baseAlbedo) {
      const albedo = baseAlbedo.clone() as Texture;
      albedo.uScale = Math.max(0.35, widthM);
      albedo.vScale = Math.max(0.5, heightM / 2.75);
      albedo.uOffset = (this.larchClones.size * 0.23) % 1;
      clone.albedoTexture = albedo;
      if (baseBump) {
        const bump = baseBump.clone() as Texture;
        bump.uScale = albedo.uScale;
        bump.vScale = albedo.vScale;
        bump.uOffset = albedo.uOffset;
        clone.bumpTexture = bump;
      }
    }
    this.larchClones.set(key, clone);
    return clone;
  }

  private configurePlantCardMaterial(material: PBRMaterial, url: string) {
    const texture = new Texture(
      url,
      this.scene,
      false,
      false,
      Texture.TRILINEAR_SAMPLINGMODE,
    );
    texture.hasAlpha = true;
    texture.anisotropicFilteringLevel = this.renderQuality.anisotropy;
    material.albedoTexture = texture;
    material.opacityTexture = null;
    material.useAlphaFromAlbedoTexture = true;
    material.transparencyMode = PBRMaterial.PBRMATERIAL_ALPHATEST;
    material.alphaCutOff = 0.28;
    material.backFaceCulling = false;
    material.twoSidedLighting = true;
    material.unlit = false;
    material.needDepthPrePass = true;
    material.forceDepthWrite = true;
    material.environmentIntensity = 0.72;
    material.subSurface.isTranslucencyEnabled = true;
    material.subSurface.translucencyIntensity = 0.2;
    material.subSurface.useAlbedoToTintTranslucency = true;
  }

  private register(mesh: AbstractMesh, layer: LayerId, entityId?: string) {
    this.layerMeshes.get(layer)?.push(mesh);
    if (entityId) {
      mesh.metadata = { ...(mesh.metadata ?? {}), entityId };
      const registered = this.entityMeshes.get(entityId) ?? [];
      registered.push(mesh);
      this.entityMeshes.set(entityId, registered);
    }
    return mesh;
  }

  private appearance(
    mesh: AbstractMesh,
    technical: Material,
    realistic: Material,
  ) {
    mesh.material = technical;
    this.appearances.set(mesh, { technical, realistic });
    return mesh;
  }

  private realisticOnly(mesh: AbstractMesh) {
    this.realisticOnlyMeshes.push(mesh);
    return mesh;
  }

  private technicalOverlay(mesh: AbstractMesh) {
    this.technicalOverlayMeshes.push(mesh);
    return mesh;
  }

  private castShadow(mesh: AbstractMesh) {
    this.shadowGenerator.addShadowCaster(mesh);
    return mesh;
  }

  private buildThinBoxes(
    name: string,
    instances: readonly PlanBoxInstance[],
    technical: Material,
    realistic: Material,
    layer: LayerId,
    entityId?: string,
    castsShadow = true,
  ) {
    if (instances.length === 0) return null;
    const mesh = CreateBox(name, { size: 1 }, this.scene);
    const matrices = new Float32Array(instances.length * 16);
    for (const [index, instance] of instances.entries()) {
      const matrix = Matrix.Compose(
        new Vector3(
          instance.widthMm * MM_TO_M,
          instance.heightMm * MM_TO_M,
          instance.depthMm * MM_TO_M,
        ),
        Quaternion.RotationYawPitchRoll(instance.yawRad, 0, 0),
        new Vector3(
          xM(instance.centerMm.x),
          (instance.baseElevationMm + instance.heightMm / 2) * MM_TO_M,
          zM(instance.centerMm.y),
        ),
      );
      matrix.copyToArray(matrices, index * 16);
    }
    mesh.thinInstanceSetBuffer("matrix", matrices, 16, true);
    mesh.thinInstanceRefreshBoundingInfo(true);
    mesh.thinInstanceEnablePicking = true;
    mesh.receiveShadows = true;
    this.appearance(mesh, technical, realistic);
    if (castsShadow) this.castShadow(mesh);
    return this.register(mesh, layer, entityId);
  }

  private buildThinEllipsoids(
    name: string,
    instances: readonly PlanBoxInstance[],
    technical: Material,
    realistic: Material,
    layer: LayerId,
    entityId: string,
  ) {
    if (instances.length === 0) return null;
    const mesh = CreateSphere(
      name,
      { diameter: 1, segments: 10 },
      this.scene,
    );
    const matrices = new Float32Array(instances.length * 16);
    for (const [index, instance] of instances.entries()) {
      const matrix = Matrix.Compose(
        new Vector3(
          instance.widthMm * MM_TO_M,
          instance.heightMm * MM_TO_M,
          instance.depthMm * MM_TO_M,
        ),
        Quaternion.RotationYawPitchRoll(instance.yawRad, 0, 0),
        new Vector3(
          xM(instance.centerMm.x),
          (instance.baseElevationMm + instance.heightMm / 2) * MM_TO_M,
          zM(instance.centerMm.y),
        ),
      );
      matrix.copyToArray(matrices, index * 16);
    }
    mesh.thinInstanceSetBuffer("matrix", matrices, 16, true);
    mesh.thinInstanceRefreshBoundingInfo(true);
    mesh.thinInstanceEnablePicking = true;
    mesh.receiveShadows = true;
    this.appearance(mesh, technical, realistic);
    this.castShadow(mesh);
    return this.register(mesh, layer, entityId);
  }

  private buildTerrainAndGrid() {
    const terrain = CreateGround(
      "Terén · DMR 5G kontext",
      { width: 240, height: 200, subdivisions: 2 },
      this.scene,
    );
    terrain.position.set(0, -0.13, 0);
    this.appearance(
      terrain,
      this.materials.terrain,
      this.realisticMaterials.terrain,
    );
    terrain.receiveShadows = true;
    terrain.isPickable = false;

    const minor = Color3.FromHexString("#313a37");
    const major = Color3.FromHexString("#55605c");
    // Cover the complete road and cadastral overview, including its extended
    // western frontage and the southern continuation of parcel 6013.
    for (let coordinate = -105; coordinate <= 100; coordinate += 1) {
      const color = coordinate % 5 === 0 ? major : minor;
      const alpha = coordinate % 5 === 0 ? 0.42 : 0.14;
      const xLine = CreateLines(
        `grid-x-${coordinate}`,
        {
          points: [
            new Vector3(coordinate - CENTER_X_M, -0.112, -95),
            new Vector3(coordinate - CENTER_X_M, -0.112, 100),
          ],
        },
        this.scene,
      );
      xLine.color = color;
      xLine.alpha = alpha;
      xLine.isPickable = false;
      this.technicalOverlay(xLine);
      const zLine = CreateLines(
        `grid-z-${coordinate}`,
        {
          points: [
            new Vector3(-120, -0.111, zM(coordinate * 1000)),
            new Vector3(110, -0.111, zM(coordinate * 1000)),
          ],
        },
        this.scene,
      );
      zLine.color = color;
      zLine.alpha = alpha;
      zLine.isPickable = false;
      this.technicalOverlay(zLine);
    }
  }

  private buildCadastre() {
    for (const parcel of CADASTRAL_PARCELS) {
      const localRing = parcel.sjtskRingMm.map(sjtskToLocalMm);
      const localHoleRings =
        parcel.sjtskHoleRingsMm?.map((ring) => ring.map(sjtskToLocalMm)) ?? [];
      if (parcel.isSubject) {
        const fill = createFlatPolygonWithHoles(
          this.scene,
          "Parcela 6012/26 · 753 m²",
          localRing,
          [SITE_SURFACES.sideEntryApproach.privatePolygonMm],
          GROUND_Y,
        );
        this.appearance(
          fill,
          this.materials.parcel,
          this.realisticMaterials.grass,
        );
        fill.receiveShadows = true;
        this.register(fill, "cadastre");
      }

      if (parcel.overviewVisibility === "ORIENTATION") {
        const subject = parcel.isSubject;
        this.buildThinBoxes(
          `Pozemné katastrálne čiary ${parcel.parcelNumber}`,
          localRing.slice(1).map((end, index) =>
            segmentBox(
              localRing[index],
              end,
              subject ? 120 : 72,
              subject ? 22 : 14,
              -24,
            ),
          ),
          subject
            ? this.materials.parcelBoundarySubject
            : this.materials.parcelBoundary,
          subject
            ? this.realisticMaterials.parcelBoundarySubject
            : this.realisticMaterials.parcelBoundary,
          "cadastre",
          subject ? parcel.id : undefined,
          false,
        );
      }

      for (const [ringIndex, ring] of [localRing, ...localHoleRings].entries()) {
        const outline = CreateLines(
          ringIndex === 0
            ? `Katastrálna hranica ${parcel.nationalReference}`
            : `Katastrálny vnútorný obvod ${parcel.nationalReference} · ${ringIndex}`,
          { points: ring.map((point) => point3(point, -0.006)) },
          this.scene,
        );
        outline.color = Color3.FromHexString(
          parcel.isSubject
            ? "#ff5d42"
            : parcel.overviewVisibility === "ORIENTATION"
              ? "#f1eadb"
              : "#c8c0b1",
        );
        outline.alpha = parcel.isSubject
          ? 1
          : parcel.overviewVisibility === "ORIENTATION"
            ? 0.84
            : 0.42;
        outline.isPickable = parcel.isSubject && ringIndex === 0;
        this.register(
          outline,
          "cadastre",
          parcel.isSubject && ringIndex === 0 ? parcel.id : undefined,
        );
      }

      if (parcel.displayLabel) {
        const anchor = sjtskToLocalMm(parcel.referencePointSjtskMm);
        const label = CreateGround(
          `Orientačný popis parcely ${parcel.parcelNumber}`,
          {
            width: 3.7,
            height: 1.18,
            subdivisions: 1,
          },
          this.scene,
        );
        label.position.set(xM(anchor.x), 0.012, zM(anchor.y));
        label.rotation.y = longestParcelAxisYaw(localRing);
        label.isPickable = false;
        label.receiveShadows = false;
        label.renderingGroupId = 2;
        label.material = parcelLabelMaterial(
          this.scene,
          parcel,
          this.renderQuality.anisotropy,
        );
        this.parcelLabelMeshes.push(label);
        this.register(label, "cadastre");
      }
    }
  }

  private buildStreetAndSite() {
    const paverRepeatMm =
      ROAD_CONTEXT.surfaceFinish.visualModuleMm.length * 8;
    for (const [index, ring] of ROAD_CONTEXT.frontReserveSurfacePolygonsMm.entries()) {
      const roadReserve = createGradedPolygon(
        this.scene,
        `Cestná rezerva 6012/1 · hlinená krajnica ${index + 1} s otvormi pre vstupy`,
        ring,
        (point) =>
          -0.02 -
          ((point.y - ROAD_CONTEXT.frontAsphaltEdgeYmm) /
            Math.abs(ROAD_CONTEXT.frontAsphaltEdgeYmm)) *
            0.015,
      );
      this.appearance(
        roadReserve,
        this.materials.road,
        this.realisticMaterials.roadReserve,
      );
      roadReserve.receiveShadows = true;
      this.register(roadReserve, "street", ROAD_CONTEXT.id);
    }

    const road = createFlatPolygon(
      this.scene,
      "Miestna komunikácia 6012/1 + 6013 · súvislá vozovka cez celý parcelný prehľad",
      ROAD_CONTEXT.visibleCarriagewayPolygonMm,
      -0.115,
      paverRepeatMm,
    );
    this.appearance(road, this.materials.road, this.realisticMaterials.road);
    road.receiveShadows = true;
    this.register(road, "street", ROAD_CONTEXT.id);

    for (const [index, ring] of ROAD_CONTEXT.cornerReserveSurfacePolygonsMm.entries()) {
      const sideReserve = createFlatPolygon(
        this.scene,
        `Bočná cestná rezerva 6012/1 · hlinená krajnica ${index + 1} s otvorom EAST-03`,
        ring,
        -0.02,
      );
      this.appearance(
        sideReserve,
        this.materials.road,
        this.realisticMaterials.roadReserve,
      );
      sideReserve.receiveShadows = true;
      this.register(sideReserve, "street", ROAD_CONTEXT.id);
    }

    for (const [index, cluster] of ROAD_CONTEXT.visualReference.vergeClustersMm.entries()) {
      this.buildPlantCard(
        `Riedka náletová vegetácia krajnice ${index + 1} · fotografia stavebníka`,
        cluster.x,
        cluster.y,
        0.46 * cluster.scale,
        0.68 * cluster.scale,
        this.realisticMaterials.plantGrass,
        index * 0.73,
      );
    }

    for (const [index, pole] of ROAD_CONTEXT.streetLighting.polesMm.entries()) {
      const lighting = ROAD_CONTEXT.streetLighting;
      const poleHeightM = lighting.poleHeightMm * MM_TO_M;
      const poleMesh = CreateCylinder(
        `Stožiar verejného osvetlenia ${index + 1} · fotografia stavebníka`,
        {
          height: poleHeightM,
          diameter: lighting.poleDiameterMm * MM_TO_M,
          tessellation: 24,
        },
        this.scene,
      );
      poleMesh.position.set(
        xM(pole.x),
        -0.11 + poleHeightM / 2,
        zM(pole.y),
      );
      poleMesh.isPickable = false;
      this.appearance(
        poleMesh,
        this.materials.paving,
        this.realisticMaterials.fenceTrack,
      );
      this.castShadow(poleMesh);
      this.register(poleMesh, "street", ROAD_CONTEXT.id);

      const arm = boxAtPlan(
        this.scene,
        `Rameno verejného osvetlenia ${index + 1}`,
        { x: pole.x, y: pole.y + lighting.armLengthMm / 2 },
        lighting.poleDiameterMm,
        lighting.armLengthMm,
        0.075,
        -0.11 + poleHeightM - 0.04,
      );
      arm.isPickable = false;
      this.appearance(
        arm,
        this.materials.paving,
        this.realisticMaterials.fenceTrack,
      );
      this.castShadow(arm);
      this.register(arm, "street", ROAD_CONTEXT.id);

      const luminaire = boxAtPlan(
        this.scene,
        `LED hlavica verejného osvetlenia ${index + 1}`,
        {
          x: pole.x,
          y:
            pole.y +
            lighting.armLengthMm +
            lighting.luminaireLengthMm / 2 -
            90,
        },
        165,
        lighting.luminaireLengthMm,
        0.085,
        -0.11 + poleHeightM - 0.065,
      );
      luminaire.rotation.x = -0.035;
      luminaire.isPickable = false;
      this.appearance(
        luminaire,
        this.materials.fence,
        this.realisticMaterials.fenceMetal,
      );
      this.castShadow(luminaire);
      this.register(luminaire, "street", ROAD_CONTEXT.id);
    }

    const frontOpenings = [
      { id: "GARAGE-DOOR", x0: 6_490, x1: 10_690 },
      { id: "FRONT-ENTRY", x0: 21_415, x1: 22_915 },
    ] as const;
    const curbTransitionLengthMm = 500;
    const frontCurbSegments = [
      {
        x0: ROAD_CONTEXT.frontParcelEdgeMm[0].x,
        x1: frontOpenings[0].x0 - curbTransitionLengthMm,
      },
      {
        x0: frontOpenings[0].x1 + curbTransitionLengthMm,
        x1: frontOpenings[1].x0 - curbTransitionLengthMm,
      },
      {
        x0: frontOpenings[1].x1 + curbTransitionLengthMm,
        x1: 28_194,
      },
    ];
    this.buildThinBoxes(
      "Obrubník pri čelnej vozovke · prerušený pre garáž a hlavný vstup",
      frontCurbSegments.map(({ x0, x1 }) =>
        segmentBox(
          { x: x0, y: ROAD_CONTEXT.frontAsphaltEdgeYmm },
          { x: x1, y: ROAD_CONTEXT.frontAsphaltEdgeYmm },
          120,
          100,
          -115,
        ),
      ),
      this.materials.paving,
      this.realisticMaterials.concrete,
      "street",
      ROAD_CONTEXT.id,
      false,
    );
    const frontTransitionCurbs = frontOpenings.flatMap(({ x0, x1 }) => [
      ...Array.from({ length: 5 }, (_, index) => {
        const startX = x0 - curbTransitionLengthMm + index * 100;
        return segmentBox(
          { x: startX, y: ROAD_CONTEXT.frontAsphaltEdgeYmm },
          { x: startX + 100, y: ROAD_CONTEXT.frontAsphaltEdgeYmm },
          150,
          100 - (index + 0.5) * 19,
          -115,
        );
      }),
      ...Array.from({ length: 5 }, (_, index) => {
        const startX = x1 + index * 100;
        return segmentBox(
          { x: startX, y: ROAD_CONTEXT.frontAsphaltEdgeYmm },
          { x: startX + 100, y: ROAD_CONTEXT.frontAsphaltEdgeYmm },
          150,
          5 + (index + 0.5) * 19,
          -115,
        );
      }),
    ]);
    this.buildThinBoxes(
      "Päťstupňové nábehové obrubníky pri čelných vstupoch",
      frontTransitionCurbs,
      this.materials.paving,
      this.realisticMaterials.concrete,
      "street",
      ROAD_CONTEXT.id,
      false,
    );
    this.buildThinBoxes(
      "Znížené obrubníky · vjazd do garáže a chodník k dverám",
      frontOpenings.map(({ x0, x1 }) =>
        segmentBox(
          { x: x0, y: ROAD_CONTEXT.frontAsphaltEdgeYmm },
          { x: x1, y: ROAD_CONTEXT.frontAsphaltEdgeYmm },
          180,
          5,
          -115,
        ),
      ),
      this.materials.paving,
      this.realisticMaterials.concrete,
      "street",
      ROAD_CONTEXT.id,
      false,
    );

    const sideTransitionStart = { x: 34_270, y: 8_750 };
    const sideGateStart = { x: 34_268, y: 9_250 };
    const sideGateEnd = { x: 34_262, y: 11_050 };
    const sideTransitionEnd = { x: 34_260, y: 11_550 };
    const innerCornerRuns = [
      [...ROAD_CONTEXT.cornerAsphaltEdgeMm.slice(0, 6), sideTransitionStart],
      [sideTransitionEnd, ROAD_CONTEXT.cornerAsphaltEdgeMm.at(-1)!],
    ];
    const innerCornerCurbs = innerCornerRuns.flatMap((run) =>
      run
        .slice(1)
        .map((end, index) => segmentBox(run[index], end, 120, 99, -114)),
    );
    this.buildThinBoxes(
      "Obrubník rohovej vetvy · prerušený pri bočnej bránke",
      innerCornerCurbs,
      this.materials.paving,
      this.realisticMaterials.concrete,
      "street",
      ROAD_CONTEXT.id,
      false,
    );
    const sideTransitionCurbs = [
      ...Array.from({ length: 5 }, (_, index) =>
        segmentBox(
          pointAlongSegment(sideTransitionStart, sideGateStart, index * 100),
          pointAlongSegment(
            sideTransitionStart,
            sideGateStart,
            (index + 1) * 100,
          ),
          150,
          99 - (index + 0.5) * 19,
          -114,
        ),
      ),
      ...Array.from({ length: 5 }, (_, index) =>
        segmentBox(
          pointAlongSegment(sideGateEnd, sideTransitionEnd, index * 100),
          pointAlongSegment(
            sideGateEnd,
            sideTransitionEnd,
            (index + 1) * 100,
          ),
          150,
          4 + (index + 0.5) * 19,
          -114,
        ),
      ),
    ];
    this.buildThinBoxes(
      "Päťstupňové nábehové obrubníky pri EAST-03",
      sideTransitionCurbs,
      this.materials.paving,
      this.realisticMaterials.concrete,
      "street",
      ROAD_CONTEXT.id,
      false,
    );
    this.buildThinBoxes(
      "Znížený obrubník pri bočnom vstupe EAST-03",
      [segmentBox(sideGateStart, sideGateEnd, 180, 4, -114)],
      this.materials.paving,
      this.realisticMaterials.concrete,
      "street",
      ROAD_CONTEXT.id,
      false,
    );

    const outerCadastralEdges = [
      ROAD_CONTEXT.frontOppositeParcelEdgeMm,
      ROAD_CONTEXT.overviewOuterRoadEdgeMm,
    ];
    for (const [index, edge] of outerCadastralEdges.entries()) {
      const boundary = CreateLines(
        `Vonkajšia hranica cestnej parcely 6012/1 podľa KN ${index + 1} · nie fyzický obrubník`,
        { points: edge.map((point) => point3(point, -0.11)) },
        this.scene,
      );
      boundary.color = Color3.FromHexString("#8f7f71");
      boundary.alpha = 0.62;
      boundary.isPickable = false;
      this.technicalOverlay(boundary);
      this.register(boundary, "street", ROAD_CONTEXT.id);
    }

    const deck = createFlatPolygon(
      this.scene,
      "Navrhnutá drevená terasa · 53 m² · staršia C3 revízia",
      SITE_SURFACES.timberTerrace.polygonMm,
      0.035,
    );
    this.appearance(deck, this.materials.timber, this.realisticMaterials.timber);
    deck.receiveShadows = true;
    this.technicalOverlay(deck);
    this.register(deck, "street", SITE_SURFACES.timberTerrace.id);

    for (const surface of [
      SITE_SURFACES.driveway,
      SITE_SURFACES.entry,
      SITE_SURFACES.sideEntryApproach,
    ]) {
      const isStreetRamp =
        surface.id === SITE_SURFACES.driveway.id ||
        surface.id === SITE_SURFACES.entry.id;
      const isSideStreetRamp =
        surface.id === SITE_SURFACES.sideEntryApproach.id;
      const yValues = surface.polygonMm.map((point) => point.y);
      const xValues = surface.polygonMm.map((point) => point.x);
      const minY = Math.min(...yValues);
      const maxY = Math.max(...yValues);
      const minX = Math.min(...xValues);
      const maxX = Math.max(...xValues);
      const elevationForPoint = (point: Point2Mm) =>
        isSideStreetRamp
          ? -0.11 +
            ((maxX - point.x) / Math.max(1, maxX - minX)) * 0.095
          : point.y <= 0
            ? -0.11 +
              ((point.y - minY) / Math.max(1, -minY)) * 0.08
            : -0.03 + (point.y / Math.max(1, maxY)) * 0.015;
      const paving = isStreetRamp || isSideStreetRamp
        ? createGradedPolygon(
            this.scene,
            `Spádované samostatné napojenie ${surface.accessOpeningId} · ${surface.areaM2} m²`,
            surface.polygonMm,
            elevationForPoint,
          )
        : createFlatPolygon(
            this.scene,
            `Navrhnutá betónová dlažba · ${surface.areaM2} m²`,
            surface.polygonMm,
            0.025,
          );
      this.appearance(
        paving,
        this.materials.paving,
        surface.id === SITE_SURFACES.driveway.id
          ? this.realisticMaterials.paving
          : this.realisticMaterials.pavingEntry,
      );
      paving.receiveShadows = true;
      this.register(paving, "street", surface.id);

      if (isStreetRamp || isSideStreetRamp) {
        const edgeRestraint = createGradedPolygonEdgeSkirt(
          this.scene,
          `Bočné výškové uzavretie napojenia ${surface.accessOpeningId}`,
          surface.polygonMm,
          elevationForPoint,
          -0.12,
        );
        this.appearance(
          edgeRestraint,
          this.materials.paving,
          this.realisticMaterials.concrete,
        );
        edgeRestraint.receiveShadows = true;
        this.register(edgeRestraint, "street", surface.id);
      }
    }
  }

  private buildFence() {
    const style = SITE_FENCE.visualProposal;
    const fenceGradeMm = GROUND_Y / MM_TO_M;
    const fixedSlatBottomMm = Math.max(
      style.curbHeightMm + 50,
      style.groundClearanceMm,
    );
    const fixedSlatHeightMm = style.proposedHeightMm - fixedSlatBottomMm;
    const gateSlatBottomMm = style.groundClearanceMm;
    const gateSlatHeightMm = style.proposedHeightMm - gateSlatBottomMm;
    const fixedSlats: PlanBoxInstance[] = [];
    const fixedSolidPanels: PlanBoxInstance[] = [];
    const fixedRails: PlanBoxInstance[] = [];
    const fixedCaps: PlanBoxInstance[] = [];
    const fixedCurbs: PlanBoxInstance[] = [];
    const fixedPosts = new Map<string, PlanBoxInstance>();
    const unsupportedEndpointKeys = new Set(
      [
        SITE_FENCE.vehicleGate.startMm,
        SITE_FENCE.vehicleGate.endMm,
        SITE_FENCE.sidePedestrianGate.physicalStartMm,
        SITE_FENCE.sidePedestrianGate.physicalEndMm,
        SITE_FENCE.houseClosure.startMm,
        SITE_FENCE.houseClosure.endMm,
      ].map(({ x, y }) => `${Math.round(x)}:${Math.round(y)}`),
    );

    for (const run of SITE_FENCE.physicalFixedRuns) {
      for (let index = 1; index < run.pointsMm.length; index += 1) {
        const start = run.pointsMm[index - 1];
        const end = run.pointsMm[index];
        const lengthMm = Math.hypot(end.x - start.x, end.y - start.y);
        const yawRad = sceneYawForPlanSegment(start, end);
        // Invisible collider so the walker cannot pass the fence or hedge.
        const fenceCollider = CreateBox(
          `${run.id} · kolízny pás ${index}`,
          {
            width: lengthMm * MM_TO_M,
            depth: run.treatment === "LIVING_HEDGE" ? 0.6 : 0.12,
            height: 1.6,
          },
          this.scene,
        );
        fenceCollider.position.set(
          xM((start.x + end.x) / 2),
          0.8,
          zM((start.y + end.y) / 2),
        );
        fenceCollider.rotation.y = yawRad;
        fenceCollider.isVisible = false;
        fenceCollider.isPickable = false;
        fenceCollider.checkCollisions = true;
        if (run.treatment === "LIVING_HEDGE") continue;
        if (run.treatment === "SLATTED_ALUMINIUM") {
          fixedSlats.push(
            ...slatInstancesForSegment(
              start,
              end,
              style.slatWidthMm,
              style.slatDepthMm,
              style.slatPitchMm,
              fixedSlatHeightMm,
              fenceGradeMm + fixedSlatBottomMm,
            ),
          );
          for (const railBaseElevationMm of [420, 1320]) {
            fixedRails.push(
              segmentBox(
                start,
                end,
                style.railDepthMm,
                style.railWidthMm,
                fenceGradeMm + railBaseElevationMm,
              ),
            );
          }
        } else {
          const panelCount = Math.max(
            1,
            Math.ceil(lengthMm / style.maximumPostSpacingMm),
          );
          const panelSpanMm = lengthMm / panelCount;
          for (let panel = 0; panel < panelCount; panel += 1) {
            const panelStart = pointAlongSegment(
              start,
              end,
              panel * panelSpanMm + style.solidPanelJointMm / 2,
            );
            const panelEnd = pointAlongSegment(
              start,
              end,
              (panel + 1) * panelSpanMm - style.solidPanelJointMm / 2,
            );
            fixedSolidPanels.push(
              segmentBox(
                panelStart,
                panelEnd,
                style.solidPanelDepthMm,
                style.proposedHeightMm - style.curbHeightMm,
                fenceGradeMm + style.curbHeightMm,
              ),
            );
          }
          fixedCaps.push(
            segmentBox(
              start,
              end,
              style.solidPanelDepthMm + 24,
              28,
              fenceGradeMm + style.proposedHeightMm - 14,
            ),
          );
        }
        fixedCurbs.push(
          segmentBox(
            start,
            end,
            style.curbDepthMm,
            style.curbHeightMm + 20,
            fenceGradeMm - 20,
          ),
        );

        const bayCount = Math.max(
          1,
          Math.ceil(lengthMm / style.maximumPostSpacingMm),
        );
        for (let bay = 0; bay <= bayCount; bay += 1) {
          const centerMm = pointAlongSegment(
            start,
            end,
            (lengthMm * bay) / bayCount,
          );
          const key = `${Math.round(centerMm.x)}:${Math.round(centerMm.y)}`;
          if (unsupportedEndpointKeys.has(key) || fixedPosts.has(key)) continue;
          fixedPosts.set(key, {
            centerMm,
            widthMm: style.postSizeMm,
            depthMm: style.postSizeMm,
            heightMm: style.proposedHeightMm + 50,
            baseElevationMm: fenceGradeMm - 50,
            yawRad,
          });
        }
      }
    }

    this.buildThinBoxes(
      "Plot · zvislé hliníkové lamely RAL 7016",
      fixedSlats,
      this.materials.fence,
      this.realisticMaterials.fenceMetal,
      "building",
      SITE_FENCE.id,
    );
    this.buildThinBoxes(
      "Bočný plot · plné veľkoformátové polia RAL 7016",
      fixedSolidPanels,
      this.materials.fence,
      this.realisticMaterials.fenceMetal,
      "building",
      SITE_FENCE.id,
    );
    this.buildThinBoxes(
      "Plot · skryté nosné priečniky",
      fixedRails,
      this.materials.fence,
      this.realisticMaterials.fenceMetal,
      "building",
      SITE_FENCE.id,
    );
    this.buildThinBoxes(
      "Bočný plot · presné horné krytky",
      fixedCaps,
      this.materials.fence,
      this.realisticMaterials.fenceMetal,
      "building",
      SITE_FENCE.id,
    );
    this.buildThinBoxes(
      "Plot · subtílne stĺpiky",
      [...fixedPosts.values()],
      this.materials.fence,
      this.realisticMaterials.fenceMetal,
      "building",
      SITE_FENCE.id,
    );
    this.buildThinBoxes(
      "Plot · nízky pohľadový sokel",
      fixedCurbs,
      this.materials.paving,
      this.realisticMaterials.concrete,
      "building",
      SITE_FENCE.id,
      false,
    );

    const hedgeVariants: PlanBoxInstance[][] = [[], [], []];
    const hedgeCores: PlanBoxInstance[] = [];
    const hedgeBeds: PlanBoxInstance[] = [];
    for (const run of SITE_FENCE.physicalFixedRuns) {
      if (run.treatment !== "LIVING_HEDGE") continue;
      for (let index = 1; index < run.pointsMm.length; index += 1) {
        const start = run.pointsMm[index - 1];
        const end = run.pointsMm[index];
        const lengthMm = Math.hypot(end.x - start.x, end.y - start.y);
        const yawRad = sceneYawForPlanSegment(start, end);
        const hedgeCenter = inwardOffsetForSegment(
          start,
          end,
          style.rearHedgeCenterlineOffsetMm,
        );
        hedgeCores.push(
          segmentBox(
            translatedPoint(start, hedgeCenter),
            translatedPoint(end, hedgeCenter),
            style.rearHedgeDepthMm * 0.68,
            style.rearHedgeHeightMm * 0.86,
            fenceGradeMm - 45,
          ),
        );
        hedgeBeds.push(
          segmentBox(
            translatedPoint(start, hedgeCenter),
            translatedPoint(end, hedgeCenter),
            style.rearHedgeDepthMm + 240,
            55,
            fenceGradeMm - 22,
          ),
        );
        const rowOffsetsMm = [
          style.rearHedgeCenterlineOffsetMm - style.rearHedgeDepthMm / 4,
          style.rearHedgeCenterlineOffsetMm,
          style.rearHedgeCenterlineOffsetMm + style.rearHedgeDepthMm / 4,
        ];
        for (const [row, inwardMm] of rowOffsetsMm.entries()) {
          const inward = inwardOffsetForSegment(start, end, inwardMm);
          const rowStartMm = 160 + row * 190;
          for (
            let distanceMm = rowStartMm;
            distanceMm <= lengthMm - 150;
            distanceMm += style.rearHedgeClusterSpacingMm
          ) {
            const seed = Math.round(distanceMm / 10) + row * 17;
            const heightFactor = 0.9 + ((seed * 37) % 19) / 100;
            const widthFactor = 1.14 + ((seed * 23) % 18) / 100;
            const depthFactor = 0.59 + ((seed * 11) % 8) / 100;
            const centerMm = translatedPoint(
              pointAlongSegment(start, end, distanceMm),
              inward,
            );
            hedgeVariants[(seed + row) % hedgeVariants.length].push({
              centerMm,
              widthMm: style.rearHedgeClusterSpacingMm * widthFactor,
              depthMm: style.rearHedgeDepthMm * depthFactor,
              heightMm: style.rearHedgeHeightMm * heightFactor,
              baseElevationMm: fenceGradeMm - 55,
              yawRad,
            });
          }
        }
      }
    }
    this.buildThinBoxes(
      "Zadná hranica · súvislé tmavé jadro živého plota",
      hedgeCores,
      this.materials.hedge,
      this.realisticMaterials.hedgeDark,
      "building",
      SITE_FENCE.id,
    );
    this.buildThinBoxes(
      "Zadná hranica · zapustený mulčovací pás",
      hedgeBeds,
      this.materials.hedge,
      this.realisticMaterials.mulch,
      "building",
      SITE_FENCE.id,
      false,
    );
    for (const [index, instances] of hedgeVariants.entries()) {
      const material = [
        this.realisticMaterials.hedgeDark,
        this.realisticMaterials.hedgeMid,
        this.realisticMaterials.hedgeLight,
      ][index];
      this.buildThinEllipsoids(
        `Zadná hranica · hustý živý plot · tón ${index + 1}`,
        instances,
        this.materials.hedge,
        material,
        "building",
        SITE_FENCE.id,
      );
    }

    const buildGate = (
      id: string,
      label: string,
      start: Point2Mm,
      closureEnd: Point2Mm,
      panelCount: number,
      infillTreatment: "SLATTED_ALUMINIUM" | "SOLID_ALUMINIUM",
      terminalFrameCenterMm: Point2Mm,
      supportPostCentersMm: readonly Point2Mm[],
    ) => {
      const gateYaw = sceneYawForPlanSegment(start, closureEnd);
      const lengthMm = Math.hypot(
        closureEnd.x - start.x,
        closureEnd.y - start.y,
      );
      const panelOverlapMm =
        panelCount > 1 ? style.telescopicPanelOverlapMm : 0;
      const panelPlaneOffsetMm =
        panelCount > 1 ? style.telescopicPanelPlaneOffsetMm : 0;
      const panelSpanMm =
        (lengthMm + (panelCount - 1) * panelOverlapMm) / panelCount;
      const panelAdvanceMm = panelSpanMm - panelOverlapMm;
      const infill: PlanBoxInstance[] = [];
      const frame: PlanBoxInstance[] = [];
      for (let panel = 0; panel < panelCount; panel += 1) {
        const panelStartDistanceMm = panel * panelAdvanceMm;
        const panelEndDistanceMm = Math.min(
          lengthMm,
          panelStartDistanceMm + panelSpanMm,
        );
        const planeOffsetMm =
          (panelCount - 1 - panel) * panelPlaneOffsetMm;
        const planeOffset = inwardOffsetForSegment(
          start,
          closureEnd,
          planeOffsetMm,
        );
        const panelStart = translatedPoint(
          pointAlongSegment(start, closureEnd, panelStartDistanceMm),
          planeOffset,
        );
        const panelEnd = translatedPoint(
          pointAlongSegment(start, closureEnd, panelEndDistanceMm),
          planeOffset,
        );
        if (infillTreatment === "SLATTED_ALUMINIUM") {
          infill.push(
            ...slatInstancesForSegment(
              panelStart,
              panelEnd,
              style.slatWidthMm,
              style.slatDepthMm,
              style.slatPitchMm,
              gateSlatHeightMm,
              fenceGradeMm + gateSlatBottomMm,
            ),
          );
        } else {
          infill.push(
            segmentBox(
              panelStart,
              panelEnd,
              style.solidPanelDepthMm,
              gateSlatHeightMm,
              fenceGradeMm + gateSlatBottomMm,
            ),
          );
        }
        frame.push(
          segmentBox(
            panelStart,
            panelEnd,
            44,
            80,
            fenceGradeMm + gateSlatBottomMm,
          ),
          segmentBox(
            panelStart,
            panelEnd,
            44,
            80,
            fenceGradeMm + style.proposedHeightMm - 80,
          ),
        );
        const frameEnd =
          panel === panelCount - 1 ? terminalFrameCenterMm : panelEnd;
        for (const centerMm of [panelStart, frameEnd]) {
          frame.push({
            centerMm,
            widthMm: 70,
            depthMm: 44,
            heightMm: gateSlatHeightMm,
            baseElevationMm: fenceGradeMm + gateSlatBottomMm,
            yawRad: gateYaw,
          });
        }
      }
      const gatePosts: PlanBoxInstance[] = supportPostCentersMm.map(
        (centerMm) => ({
          centerMm,
          widthMm: style.gatePostSizeMm,
          depthMm: style.gatePostSizeMm,
          heightMm: style.proposedHeightMm + 50,
          baseElevationMm: fenceGradeMm - 50,
          yawRad: gateYaw,
        }),
      );
      this.buildThinBoxes(
        `${label} · ${infillTreatment === "SLATTED_ALUMINIUM" ? "lamely" : "plná výplň"}`,
        infill,
        this.materials.fence,
        this.realisticMaterials.fenceMetal,
        "building",
        id,
      );
      this.buildThinBoxes(
        `${label} · rám`,
        frame,
        this.materials.fence,
        this.realisticMaterials.fenceMetal,
        "building",
        id,
      );
      this.buildThinBoxes(
        `${label} · zosilnené stĺpiky`,
        gatePosts,
        this.materials.fence,
        this.realisticMaterials.fenceMetal,
        "building",
        id,
      );
    };

    buildGate(
      SITE_FENCE.vehicleGate.id,
      SITE_FENCE.vehicleGate.label,
      SITE_FENCE.vehicleGate.startMm,
      SITE_FENCE.vehicleGate.leafClosureEndMm,
      SITE_FENCE.vehicleGate.panelCount,
      SITE_FENCE.vehicleGate.infillTreatment,
      SITE_FENCE.vehicleGate.terminalFrameCenterMm,
      SITE_FENCE.vehicleGate.supportPostCentersMm,
    );
    buildGate(
      SITE_FENCE.sidePedestrianGate.id,
      SITE_FENCE.sidePedestrianGate.label,
      SITE_FENCE.sidePedestrianGate.physicalStartMm,
      SITE_FENCE.sidePedestrianGate.physicalEndMm,
      SITE_FENCE.sidePedestrianGate.panelCount,
      SITE_FENCE.sidePedestrianGate.infillTreatment,
      SITE_FENCE.sidePedestrianGate.terminalFrameCenterMm,
      SITE_FENCE.sidePedestrianGate.supportPostCentersMm,
    );

    const wicketLengthMm = Math.hypot(
      SITE_FENCE.sidePedestrianGate.physicalEndMm.x -
        SITE_FENCE.sidePedestrianGate.physicalStartMm.x,
      SITE_FENCE.sidePedestrianGate.physicalEndMm.y -
        SITE_FENCE.sidePedestrianGate.physicalStartMm.y,
    );
    const wicketHandlePoint = pointAlongSegment(
      SITE_FENCE.sidePedestrianGate.physicalStartMm,
      SITE_FENCE.sidePedestrianGate.physicalEndMm,
      Math.max(180, wicketLengthMm - 220),
    );
    const wicketHandle = CreateCylinder(
      "Bočná bránka · nerezové zvislé madlo",
      { height: 0.3, diameter: 0.026, tessellation: 20 },
      this.scene,
    );
    wicketHandle.position.set(
      xM(wicketHandlePoint.x - 55),
      1.02,
      zM(wicketHandlePoint.y),
    );
    wicketHandle.material = this.realisticMaterials.chimneyMetal;
    wicketHandle.isPickable = false;
    this.realisticOnly(wicketHandle);
    this.castShadow(wicketHandle);
    this.register(
      wicketHandle,
      "building",
      SITE_FENCE.sidePedestrianGate.id,
    );

    const facadeReceiver = boxAtPlan(
      this.scene,
      "Teleskopická brána · subtílna prijímacia konzola na fasáde",
      SITE_FENCE.vehicleGate.facadeReceiver.centerMm,
      SITE_FENCE.vehicleGate.facadeReceiver.widthMm,
      SITE_FENCE.vehicleGate.facadeReceiver.depthMm,
      SITE_FENCE.vehicleGate.facadeReceiver.heightMm * MM_TO_M,
      SITE_FENCE.vehicleGate.facadeReceiver.baseElevationMm * MM_TO_M,
    );
    this.appearance(
      facadeReceiver,
      this.materials.fence,
      this.realisticMaterials.fenceMetal,
    );
    this.castShadow(facadeReceiver);
    this.register(
      facadeReceiver,
      "building",
      SITE_FENCE.vehicleGate.id,
    );

    const trackStart = SITE_FENCE.vehicleGate.stackPocketStartMm;
    const trackEnd = SITE_FENCE.vehicleGate.leafClosureEndMm;
    const trackCenter = {
      x: (trackStart.x + trackEnd.x) / 2,
      y:
        trackStart.y +
        ((SITE_FENCE.vehicleGate.panelCount - 1) *
          style.telescopicPanelPlaneOffsetMm) /
          2,
    };
    const threshold = boxAtPlan(
      this.scene,
      "Teleskopická brána · zapustený betónový prah",
      trackCenter,
      trackEnd.x - trackStart.x,
      style.gateThresholdDepthMm,
      0.05,
      GROUND_Y - 0.015,
    );
    this.appearance(
      threshold,
      this.materials.paving,
      this.realisticMaterials.concrete,
    );
    threshold.receiveShadows = true;
    this.register(threshold, "building", SITE_FENCE.vehicleGate.id);

    const gateTracks = Array.from(
      { length: SITE_FENCE.vehicleGate.panelCount },
      (_, panel) => {
        const offset = inwardOffsetForSegment(
          trackStart,
          trackEnd,
          panel * style.telescopicPanelPlaneOffsetMm,
        );
        return segmentBox(
          translatedPoint(trackStart, offset),
          translatedPoint(trackEnd, offset),
          28,
          14,
          fenceGradeMm + 18,
        );
      },
    );
    this.buildThinBoxes(
      "Teleskopická brána · tri zapustené koľajnice",
      gateTracks,
      this.materials.fence,
      this.realisticMaterials.fenceTrack,
      "building",
      SITE_FENCE.vehicleGate.id,
      false,
    );

    for (const run of SITE_FENCE.annotatedCenterlineRuns) {
      const centerline = CreateLines(
        `${run.label} · referenčná os náčrtu`,
        {
          points: run.pointsMm.map((point) => point3(point, 1.64)),
        },
        this.scene,
      );
      centerline.color = Color3.FromHexString("#aebbb8");
      centerline.alpha = 0.72;
      centerline.isPickable = false;
      this.technicalOverlay(centerline);
      this.register(centerline, "building", SITE_FENCE.id);
    }

    const clearOpeningLine = CreateLines(
      "Brána do záhrady · čistý otvor 4,2 m",
      {
        points: [
          point3(SITE_FENCE.vehicleGate.startMm, 1.7),
          point3(SITE_FENCE.vehicleGate.endMm, 1.7),
        ],
      },
      this.scene,
    );
    clearOpeningLine.color = Color3.FromHexString("#4aae7a");
    clearOpeningLine.isPickable = false;
    this.technicalOverlay(clearOpeningLine);
    this.register(clearOpeningLine, "building", SITE_FENCE.vehicleGate.id);

    const stackEnvelope = CreateDashedLines(
      "Brána do záhrady · teleskopická skladacia kapsa",
      {
        points: [
          point3(SITE_FENCE.vehicleGate.startMm, 1.74),
          point3(SITE_FENCE.vehicleGate.stackPocketStartMm, 1.74),
        ],
        dashSize: 0.22,
        gapSize: 0.12,
      },
      this.scene,
    );
    stackEnvelope.color = Color3.FromHexString("#aebbb8");
    stackEnvelope.isPickable = false;
    this.technicalOverlay(stackEnvelope);
    this.register(stackEnvelope, "building", SITE_FENCE.vehicleGate.id);
  }

  private buildHouse() {
    const lowerCenter = {
      x: HOUSE.originMm.x + HOUSE.lowerBar.widthMm / 2,
      y: HOUSE.originMm.y + HOUSE.lowerBar.depthMm / 2,
    };
    const wingCenter = {
      x: HOUSE.originMm.x + HOUSE.wing.xMm + HOUSE.wing.widthMm / 2,
      y: HOUSE.originMm.y + HOUSE.wing.yMm + HOUSE.wing.depthMm / 2,
    };
    const bodies = [
      boxAtPlan(
        this.scene,
        "Dom · hlavný trakt",
        lowerCenter,
        HOUSE.lowerBar.widthMm,
        HOUSE.lowerBar.depthMm,
        3.125,
        0,
      ),
      boxAtPlan(
        this.scene,
        "Dom · severné krídlo",
        wingCenter,
        HOUSE.wing.widthMm,
        HOUSE.wing.depthMm,
        3.125,
        0,
      ),
    ];
    for (const body of bodies) {
      body.material = this.materials.wall;
      body.receiveShadows = false;
      this.technicalOverlay(body);
      body.enableEdgesRendering();
      body.edgesColor = Color4.FromHexString("#f5f2e95a");
      body.edgesWidth = 0.8;
      this.register(body, "building", HOUSE.id);
    }

    this.buildGables();
    this.buildRealisticHouseShell();
    this.buildInteriorFitOut();
    this.buildJoinedRoof();
    // Every plastered shell wall stops the walkthrough collider.
    for (const mesh of this.layerMeshes.get("building") ?? []) {
      if (
        mesh instanceof Mesh &&
        mesh.material === this.realisticMaterials.wall &&
        mesh.getTotalVertices() > 0
      ) {
        mesh.checkCollisions = true;
      }
    }

    this.buildInteractiveGarageDoor();
    this.buildGarageVehicle();

    for (const [index, flueSpec] of HOUSE.flues.entries()) {
      const center = flueSpec.centerMm;
      const roofMount = roofMountTransform(
        flueSpec.roofFace,
        center.x,
        center.y,
        deriveJoinedRoofGeometry().parameters,
      );
      const pipeDiameterM = flueSpec.outerDiameterMm * MM_TO_M;
      const flashing = CreateCylinder(
        `Kruhové oplechovanie zvislého dymovodu ${index + 1}`,
        {
          height: 0.035,
          diameter: flueSpec.flashingDiameterMm * MM_TO_M,
          tessellation: 64,
        },
        this.scene,
      );
      flashing.position.set(
        xM(center.x),
        roofMount.elevationMm * MM_TO_M + 0.028,
        zM(center.y),
      );
      flashing.rotation.x = roofMount.rotationXRad;
      flashing.rotation.z = roofMount.rotationZRad;
      flashing.material = this.realisticMaterials.roofEdge;
      flashing.isPickable = false;
      this.realisticOnly(flashing);
      this.castShadow(flashing);
      this.register(flashing, "building", flueSpec.id);

      // One coaxial matte-black pipe replaces the former 347 × 500 masonry
      // column. It starts at the stove top and runs without an elbow through
      // the vaulted ceiling and roof to its documented termination.
      const pipeHeightM =
        (flueSpec.terminationElevationMm - flueSpec.baseElevationMm) * MM_TO_M;
      const flue = CreateCylinder(
        `Zvislý dymovod ${index + 1} · ${flueSpec.id} · Ø${flueSpec.outerDiameterMm}`,
        { height: pipeHeightM, diameter: pipeDiameterM, tessellation: 48 },
        this.scene,
      );
      flue.position.set(
        xM(center.x),
        (flueSpec.baseElevationMm + flueSpec.terminationElevationMm) * MM_TO_M / 2,
        zM(center.y),
      );
      flue.checkCollisions = false;
      this.appearance(
        flue,
        this.materials.roof,
        this.realisticMaterials.roofEdge,
      );
      this.castShadow(flue);
      flue.isPickable = false;
      flue.metadata = {
        ...(flue.metadata ?? {}),
        flueShape: flueSpec.shape,
        finish: flueSpec.finish,
      };
      this.register(flue, "building", flueSpec.id);

      const roofCollar = CreateCylinder(
        `Tesniaca manžeta dymovodu ${index + 1}`,
        {
          height: 0.12,
          diameter: pipeDiameterM + 0.07,
          tessellation: 48,
        },
        this.scene,
      );
      roofCollar.position.set(
        xM(center.x),
        roofMount.elevationMm * MM_TO_M + 0.045,
        zM(center.y),
      );
      roofCollar.material = this.realisticMaterials.roofEdge;
      roofCollar.isPickable = false;
      this.realisticOnly(roofCollar);
      this.castShadow(roofCollar);
      this.register(roofCollar, "building", flueSpec.id);

      const rainCap = CreateCylinder(
        `Matne čierna dažďová hlavica dymovodu ${index + 1}`,
        {
          height: 0.035,
          diameter: flueSpec.rainCapDiameterMm * MM_TO_M,
          tessellation: 48,
        },
        this.scene,
      );
      rainCap.position.set(
        xM(center.x),
        flueSpec.terminationElevationMm * MM_TO_M + 0.02,
        zM(center.y),
      );
      rainCap.material = this.realisticMaterials.roofEdge;
      rainCap.isPickable = false;
      this.realisticOnly(rainCap);
      this.castShadow(rainCap);
      this.register(rainCap, "building", flueSpec.id);
    }

    for (const downpipe of HOUSE.rainwaterDownpipes) {
      const heightM = HOUSE.eavesElevationMm * MM_TO_M - 0.03;
      const porch = HOUSE.porches.wingEnd;
      const loggia = HOUSE.porches.gardenLoggia;
      let pipeXmm: number;
      let pipeYmm: number;
      if ("faceYmm" in downpipe) {
        // The IO01 route stays authoritative; only the visual pipe steps
        // aside when it would cross the OPEN porch front (the glazing
        // stretch) or the open loggia bay. Over a solid wall the pipe simply
        // runs down the facade like any real downpipe.
        const insidePorchFront =
          downpipe.faceYmm === porch.frontYmm &&
          downpipe.xMm > porch.glazing.startXmm &&
          downpipe.xMm < porch.glazing.startXmm + porch.glazing.widthMm;
        const insideLoggiaFront =
          downpipe.faceYmm === loggia.faceYmm &&
          downpipe.xMm > loggia.openingStartXmm &&
          downpipe.xMm < loggia.openingEndXmm;
        pipeXmm = insidePorchFront
          ? porch.eastWallInnerXmm + 380
          : insideLoggiaFront
            ? loggia.cornerPier.startXmm + 650
            : downpipe.xMm;
        pipeYmm = downpipe.faceYmm + 65;
        if (pipeXmm !== downpipe.xMm) {
          const offsetLink = CreateTube(
            `${downpipe.id} · viditeľné pododkvapové odsadenie`,
            {
              path: [downpipe.xMm, pipeXmm].map(
                (xMm) =>
                  new Vector3(
                    xM(xMm),
                    HOUSE.eavesElevationMm * MM_TO_M - 0.04,
                    zM(pipeYmm),
                  ),
              ),
              radius: 0.05,
              tessellation: 16,
              cap: Mesh.CAP_ALL,
            },
            this.scene,
          );
          offsetLink.material = this.realisticMaterials.roofEdge;
          offsetLink.isPickable = false;
          this.realisticOnly(offsetLink);
          this.castShadow(offsetLink);
          this.register(offsetLink, "building");
        }
      } else {
        // Pipe on an X facade (east eave of the wing): hangs 65 mm off the
        // plaster, directly under the covered gutter profile.
        pipeXmm = downpipe.faceXmm + 65;
        pipeYmm = downpipe.yMm;
      }
      const pipe = CreateCylinder(
        `${downpipe.id} · dažďový zvod · vizualizačný detail IO01`,
        { height: heightM, diameter: 0.1, tessellation: 16 },
        this.scene,
      );
      pipe.position.set(xM(pipeXmm), 0.03 + heightM / 2, zM(pipeYmm));
      pipe.material = this.realisticMaterials.roofEdge;
      pipe.isPickable = false;
      this.realisticOnly(pipe);
      this.castShadow(pipe);
      this.register(pipe, "building");

      // Gutter outlet elbow tying the pipe to the eave profile.
      const elbow = CreateTube(
        `${downpipe.id} · odbočka zo žľabu`,
        {
          path: [
            new Vector3(xM(pipeXmm), HOUSE.eavesElevationMm * MM_TO_M - 0.04, zM(pipeYmm)),
            new Vector3(
              xM("faceYmm" in downpipe ? pipeXmm : downpipe.faceXmm + 10),
              HOUSE.eavesElevationMm * MM_TO_M - 0.04,
              zM("faceYmm" in downpipe ? downpipe.faceYmm + 10 : pipeYmm),
            ),
          ],
          radius: 0.05,
          tessellation: 16,
          cap: Mesh.CAP_ALL,
        },
        this.scene,
      );
      elbow.material = this.realisticMaterials.roofEdge;
      elbow.isPickable = false;
      this.realisticOnly(elbow);
      this.register(elbow, "building");
    }
  }

  /** Sectional door follows vertical tracks, a curved rail and the garage ceiling. */
  private buildInteractiveGarageDoor() {
    const spec = HOUSE.facades.front.garageDoor;
    const door = GARAGE_VEHICLE.door;
    const panelCount = door.panelCount;
    const panelPitchM = door.panelHeightM;
    const closedWorldZ = zM(door.faceYmm);

    for (let index = 0; index < panelCount; index += 1) {
      const panel = boxAtPlan(
        this.scene,
        `GARAGE-DOOR · sekcia ${index + 1} z ${panelCount}`,
        {
          x: spec.startXmm + spec.widthMm / 2,
          y: HOUSE.facades.front.faceYmm - 36,
        },
        spec.widthMm,
        76,
        panelPitchM - 0.009,
        index * panelPitchM + 0.0045,
      );
      this.appearance(
        panel,
        this.materials.glass,
        this.realisticMaterials.roofEdge,
      );
      panel.receiveShadows = true;
      panel.isPickable = true;
      panel.checkCollisions = true;
      panel.metadata = {
        ...(panel.metadata ?? {}),
        entityId: spec.id,
        doorId: spec.id,
        doorMotion: "OVERHEAD",
        cameraOccluder: true,
        dynamicCameraOccluder: true,
      };
      this.castShadow(panel);
      this.register(panel, "building", spec.id);
      this.garageDoorPanels.push(panel);
    }

    const apply = (progress: number) => {
      for (const [index, panel] of this.garageDoorPanels.entries()) {
        const pose = garageDoorPanelPose(index, progress);
        panel.position.y = pose.elevationM;
        panel.position.z = closedWorldZ - pose.inwardOffsetM;
        panel.rotation.x = -pose.pitchRad;
        panel.computeWorldMatrix(true);
      }
    };

    this.doors.register({
      id: spec.id,
      label: "Sekčná garážová brána",
      kind: "OVERHEAD",
      interactionPoint: {
        x: xM(spec.startXmm + spec.widthMm / 2),
        z: closedWorldZ,
      },
      apply,
      canClose: (actor) => {
        const halfWidthM = spec.widthMm * MM_TO_M / 2 + 0.38;
        const centerX = xM(spec.startXmm + spec.widthMm / 2);
        // A sectional leaf travels above head height once it leaves the
        // threshold. Only the descending facade plane can sweep through the
        // walker; standing safely inside the garage must not block closing.
        const insideTrack =
          actor.position.z <= closedWorldZ + 0.42 &&
          actor.position.z >= closedWorldZ - 0.62;
        return !(
          Math.abs(actor.position.x - centerX) < halfWidthM && insideTrack
        );
      },
    });
  }

  /** Local, dependency-free visual model with the proportions of a Superb. */
  private buildGarageVehicle() {
    const vehicle = GARAGE_VEHICLE;
    const root = new TransformNode(
      `${vehicle.label} · automatické parkovanie`,
      this.scene,
    );
    root.metadata = {
      vehicleId: vehicle.id,
      vehicleModel: vehicle.label,
      parkingRoomId: vehicle.roomId,
    };
    root.position.set(
      xM(vehicle.route.streetStartMm.x),
      garageVehicleSurfaceElevationM(vehicle.route.streetStartMm) -
        vehicle.wheelGroundOffsetM,
      zM(vehicle.route.streetStartMm.y),
    );
    root.setEnabled(false);
    this.garageVehicleRoot = root;

    const paint = pbrMaterial(
      this.scene,
      "Superb · metalická modrá karoséria",
      "#123047",
      0.24,
      0.56,
    );
    paint.clearCoat.isEnabled = true;
    paint.clearCoat.intensity = 1;
    paint.clearCoat.roughness = 0.055;
    paint.environmentIntensity = 0.88;
    const glass = pbrMaterial(
      this.scene,
      "Superb · tónované sklá",
      "#07151d",
      0.1,
      0.04,
      0.9,
    );
    glass.transparencyMode = PBRMaterial.PBRMATERIAL_ALPHABLEND;
    glass.environmentIntensity = 1.6;
    glass.clearCoat.isEnabled = true;
    glass.clearCoat.intensity = 0.85;
    glass.clearCoat.roughness = 0.035;
    const dark = pbrMaterial(
      this.scene,
      "Superb · lesklé čierne detaily",
      "#111517",
      0.28,
      0.34,
    );
    const tire = pbrMaterial(
      this.scene,
      "Superb · pneumatiky",
      "#101112",
      0.94,
      0.02,
    );
    const alloy = pbrMaterial(
      this.scene,
      "Superb · brúsené disky",
      "#aeb6ba",
      0.24,
      0.9,
    );
    const chrome = pbrMaterial(
      this.scene,
      "Superb · chróm",
      "#d9e0e2",
      0.12,
      0.94,
    );
    const darkChrome = pbrMaterial(
      this.scene,
      "Superb · Unique Dark Chrome",
      "#4e565a",
      0.18,
      0.95,
    );
    const headlight = pbrMaterial(
      this.scene,
      "Superb · LED svetlomety",
      "#eaf7ff",
      0.08,
      0.16,
    );
    headlight.emissiveColor = Color3.FromHexString("#bddfff").scale(0.72);
    this.garageVehicleHeadlightMaterial = headlight;
    const brake = pbrMaterial(
      this.scene,
      "Superb · zadné LED svetlá",
      "#8b1016",
      0.16,
      0.12,
    );
    brake.emissiveColor = Color3.FromHexString("#b20f18").scale(0.46);
    this.garageVehicleBrakeMaterial = brake;
    const plate = pbrMaterial(
      this.scene,
      "Superb · evidenčné tabuľky",
      "#f2f3ed",
      0.58,
      0,
    );

    const addBox = (
      name: string,
      size: { readonly x: number; readonly y: number; readonly z: number },
      position: { readonly x: number; readonly y: number; readonly z: number },
      material: Material,
      rotationZ = 0,
      shadow = true,
      collision = false,
    ) => {
      const mesh = CreateBox(
        `${vehicle.label} · ${name}`,
        { width: size.x, height: size.y, depth: size.z },
        this.scene,
      );
      mesh.parent = root;
      mesh.position.set(position.x, position.y, position.z);
      mesh.rotation.z = rotationZ;
      mesh.material = material;
      mesh.isPickable = false;
      mesh.checkCollisions = collision;
      mesh.receiveShadows = shadow;
      if (shadow) this.castShadow(mesh);
      this.realisticOnly(mesh);
      this.register(mesh, "building", vehicle.id);
      return mesh;
    };

    const halfVehicleLengthM = vehicle.dimensionsMm.length * MM_TO_M / 2;
    const halfVehicleWidthM = vehicle.dimensionsMm.width * MM_TO_M / 2;
    const registerVisual = (mesh: Mesh, shadow = true) => {
      mesh.parent = root;
      mesh.isPickable = false;
      mesh.receiveShadows = shadow;
      if (shadow) this.castShadow(mesh);
      this.realisticOnly(mesh);
      this.register(mesh, "building", vehicle.id);
      return mesh;
    };

    const body = createVehicleLoftMesh(
      this.scene,
      `${vehicle.label} · hladká karoséria Modern Solid`,
      GARAGE_SUPERB_BODY_STATIONS,
      paint,
    );
    body.metadata = { vehicleGeneration: "SUPERB-IV-INSPIRED" };
    registerVisual(body);
    const cabin = createVehicleLoftMesh(
      this.scene,
      `${vehicle.label} · plynulá presklená kabína`,
      GARAGE_SUPERB_CABIN_STATIONS,
      glass,
    );
    cabin.metadata = { vehicleGeneration: "SUPERB-IV-INSPIRED" };
    registerVisual(cabin, false);

    // Simple hidden colliders keep walkthrough response stable; the smooth
    // display shell is intentionally never used for per-triangle collision.
    for (const [name, size, position] of [
      [
        "spodný kolízny obal",
        { x: 4.54, y: 0.68, z: 1.82 },
        { x: 0, y: 0.55, z: 0 },
      ],
      [
        "horný kolízny obal",
        { x: 2.38, y: 0.5, z: 1.46 },
        { x: -0.15, y: 1.22, z: 0 },
      ],
    ] as const) {
      const collider = CreateBox(
        `${vehicle.label} · ${name}`,
        { width: size.x, height: size.y, depth: size.z },
        this.scene,
      );
      collider.parent = root;
      collider.position.set(position.x, position.y, position.z);
      collider.isPickable = false;
      collider.isVisible = false;
      collider.checkCollisions = true;
      collider.metadata = {
        vehicleCollider: true,
        cameraOccluder: true,
        dynamicCameraOccluder: true,
      };
      this.register(collider, "building", vehicle.id);
    }

    for (const side of [-1, 1] as const) {
      addBox(
        `A stĺpik ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: 0.075, y: 0.5, z: 0.026 },
        { x: 0.78, y: 1.22, z: side * 0.69 },
        paint,
        -0.58,
      );
      addBox(
        `B stĺpik ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: 0.075, y: 0.47, z: 0.026 },
        { x: -0.2, y: 1.235, z: side * 0.752 },
        dark,
      );
      addBox(
        `C stĺpik ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: 0.11, y: 0.38, z: 0.026 },
        { x: -1.03, y: 1.18, z: side * 0.707 },
        paint,
        0.33,
      );
      addBox(
        `spätné zrkadlo ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: 0.23, y: 0.105, z: 0.19 },
        { x: 0.63, y: 1.2, z: side * (halfVehicleWidthM - 0.095) },
        paint,
      );
      for (let segment = 0; segment < 3; segment += 1) {
        addBox(
          `Matrix LED ${side < 0 ? "vľavo" : "vpravo"} · segment ${segment + 1}`,
          { x: 0.026, y: 0.09, z: 0.13 },
          {
            x: halfVehicleLengthM - 0.018,
            y: 0.765 + segment * 0.008,
            z: side * (0.45 + segment * 0.145),
          },
          headlight,
          0,
          false,
        );
      }
      addBox(
        `zadné LED svetlo ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: 0.026, y: 0.14, z: 0.5 },
        { x: -halfVehicleLengthM + 0.018, y: 0.745, z: side * 0.59 },
        brake,
        0,
        false,
      );
      for (const x of [-0.92, 0.24]) {
        addBox(
          `kľučka dverí ${side < 0 ? "vľavo" : "vpravo"}`,
          { x: 0.17, y: 0.024, z: 0.018 },
          { x, y: 0.9, z: side * 0.929 },
          darkChrome,
          0,
          false,
        );
      }
      for (const x of [-1.38, -0.2, 0.83]) {
        addBox(
          `škára dverí ${side < 0 ? "vľavo" : "vpravo"}`,
          { x: 0.012, y: 0.5, z: 0.01 },
          { x, y: 0.67, z: side * 0.927 },
          dark,
          0,
          false,
        );
      }
    }

    addBox(
      "zadná svetelná línia",
      { x: 0.024, y: 0.035, z: 1.32 },
      { x: -halfVehicleLengthM + 0.016, y: 0.755, z: 0 },
      brake,
      0,
      false,
    );
    addBox("predná maska", { x: 0.028, y: 0.34, z: 1.04 }, { x: halfVehicleLengthM - 0.018, y: 0.58, z: 0 }, dark);
    const grilleOutline = CreateTube(
      `${vehicle.label} · oktagonálny rám masky`,
      {
        path: [
          new Vector3(halfVehicleLengthM - 0.014, 0.75, -0.52),
          new Vector3(halfVehicleLengthM - 0.014, 0.79, -0.43),
          new Vector3(halfVehicleLengthM - 0.014, 0.79, 0.43),
          new Vector3(halfVehicleLengthM - 0.014, 0.75, 0.52),
          new Vector3(halfVehicleLengthM - 0.014, 0.43, 0.52),
          new Vector3(halfVehicleLengthM - 0.014, 0.38, 0.43),
          new Vector3(halfVehicleLengthM - 0.014, 0.38, -0.43),
          new Vector3(halfVehicleLengthM - 0.014, 0.43, -0.52),
          new Vector3(halfVehicleLengthM - 0.014, 0.75, -0.52),
        ],
        radius: 0.012,
        tessellation: 8,
      },
      this.scene,
    );
    grilleOutline.material = darkChrome;
    registerVisual(grilleOutline, false);
    for (const z of [-0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4]) {
      addBox("zvislá lamela masky", { x: 0.012, y: 0.27, z: 0.012 }, { x: halfVehicleLengthM - 0.012, y: 0.585, z }, darkChrome, 0, false);
    }
    addBox("predná tabuľka", { x: 0.018, y: 0.13, z: 0.52 }, { x: halfVehicleLengthM - 0.014, y: 0.39, z: 0 }, plate, 0, false);
    addBox("zadná tabuľka", { x: 0.018, y: 0.13, z: 0.52 }, { x: -halfVehicleLengthM + 0.014, y: 0.51, z: 0 }, plate, 0, false);
    addBox("chrómová línia okien vľavo", { x: 2.28, y: 0.018, z: 0.018 }, { x: -0.16, y: 1.015, z: -0.754 }, chrome, 0, false);
    addBox("chrómová línia okien vpravo", { x: 2.28, y: 0.018, z: 0.018 }, { x: -0.16, y: 1.015, z: 0.754 }, chrome, 0, false);

    for (const axleX of [
      GARAGE_SUPERB_AXLES_M.rearX,
      GARAGE_SUPERB_AXLES_M.frontX,
    ]) {
      for (const side of [-1, 1] as const) {
        const arch = CreateCylinder(
          `${vehicle.label} · podbeh ${axleX > 0 ? "predný" : "zadný"} ${side < 0 ? "vľavo" : "vpravo"}`,
          { height: 0.018, diameter: 0.76, tessellation: 40 },
          this.scene,
        );
        arch.parent = root;
        arch.position.set(axleX, 0.36, side * 0.931);
        arch.rotation.x = Math.PI / 2;
        arch.material = dark;
        arch.isPickable = false;
        this.realisticOnly(arch);
        this.register(arch, "building", vehicle.id);
      }
    }

    for (const axleX of [
      GARAGE_SUPERB_AXLES_M.rearX,
      GARAGE_SUPERB_AXLES_M.frontX,
    ]) {
      for (const side of [-1, 1] as const) {
        const steeringAnchor = new TransformNode(
          `${vehicle.label} · koleso ${axleX > 0 ? "predné" : "zadné"} ${side < 0 ? "ľavé" : "pravé"}`,
          this.scene,
        );
        steeringAnchor.parent = root;
        steeringAnchor.position.set(axleX, 0.36, side * 0.85);
        if (axleX > 0) this.garageVehicleFrontSteering.push(steeringAnchor);

        const wheelSpin = new TransformNode(
          `${steeringAnchor.name} · rotácia pneumatiky`,
          this.scene,
        );
        wheelSpin.parent = steeringAnchor;
        this.garageVehicleWheelSpins.push(wheelSpin);

        const wheel = CreateCylinder(
          `${steeringAnchor.name} · pneumatika`,
          { height: 0.23, diameter: 0.69, tessellation: 32 },
          this.scene,
        );
        wheel.parent = wheelSpin;
        wheel.rotation.x = Math.PI / 2;
        wheel.material = tire;
        wheel.isPickable = false;
        this.castShadow(wheel);
        this.realisticOnly(wheel);
        this.register(wheel, "building", vehicle.id);

        const rim = CreateCylinder(
          `${steeringAnchor.name} · disk`,
          { height: 0.236, diameter: 0.43, tessellation: 20 },
          this.scene,
        );
        rim.parent = wheelSpin;
        rim.rotation.x = Math.PI / 2;
        rim.material = alloy;
        rim.isPickable = false;
        this.realisticOnly(rim);
        this.register(rim, "building", vehicle.id);

        const brakeDisc = CreateCylinder(
          `${steeringAnchor.name} · brzdový kotúč`,
          { height: 0.242, diameter: 0.31, tessellation: 28 },
          this.scene,
        );
        brakeDisc.parent = wheelSpin;
        brakeDisc.rotation.x = Math.PI / 2;
        brakeDisc.material = darkChrome;
        brakeDisc.isPickable = false;
        this.realisticOnly(brakeDisc);
        this.register(brakeDisc, "building", vehicle.id);

        const hub = CreateCylinder(
          `${steeringAnchor.name} · stred disku`,
          { height: 0.248, diameter: 0.08, tessellation: 20 },
          this.scene,
        );
        hub.parent = wheelSpin;
        hub.rotation.x = Math.PI / 2;
        hub.material = alloy;
        hub.isPickable = false;
        this.realisticOnly(hub);
        this.register(hub, "building", vehicle.id);

        for (let spokeIndex = 0; spokeIndex < 10; spokeIndex += 1) {
          const angle = (spokeIndex / 10) * Math.PI * 2;
          const spoke = CreateBox(
            `${steeringAnchor.name} · lúč disku ${spokeIndex + 1}`,
            { width: 0.18, height: 0.018, depth: 0.246 },
            this.scene,
          );
          spoke.parent = wheelSpin;
          spoke.position.set(
            Math.cos(angle) * 0.105,
            Math.sin(angle) * 0.105,
            0,
          );
          spoke.rotation.z = angle;
          spoke.material = alloy;
          spoke.isPickable = false;
          this.realisticOnly(spoke);
          this.register(spoke, "building", vehicle.id);
        }
      }
    }
  }

  private buildJoinedRoof() {
    const roof = deriveJoinedRoofGeometry();

    for (const face of roof.faces) {
      const faceVertices = face.vertexIndices.map((index) => roof.vertices[index]);
      const panel = createRoofFace(
        this.scene,
        `Spojená strešná rovina · ${face.id}`,
        faceVertices,
      );
      this.appearance(panel, this.materials.roof, this.realisticMaterials.roof);
      panel.metadata = { ...(panel.metadata ?? {}), cameraOccluder: true };
      panel.receiveShadows = true;
      this.castShadow(panel);
      panel.enableEdgesRendering();
      panel.edgesColor = Color4.FromHexString("#aeb8bb66");
      panel.edgesWidth = 0.65;
      this.register(panel, "building", HOUSE.id);

      const underside = createRoofFace(
        this.scene,
        `Súvislý podhľad strešnej roviny · ${face.id}`,
        faceVertices.map((vertex) => ({
          ...vertex,
          elevationMm: vertex.elevationMm - 70,
        })),
      );
      underside.flipFaces(true);
      underside.material = this.realisticMaterials.soffit;
      underside.metadata = {
        ...(underside.metadata ?? {}),
        cameraOccluder: true,
      };
      underside.receiveShadows = true;
      underside.isPickable = false;
      this.realisticOnly(underside);
      this.register(underside, "building", HOUSE.id);
    }

    for (const seamSegment of roof.seamSegments) {
      const seam = this.createRoofLine(
        `Orezaný falc · ${seamSegment.id}`,
        seamSegment.start,
        seamSegment.end,
        0.008,
        0.016,
      );
      seam.material = this.realisticMaterials.roofEdge;
      seam.isPickable = false;
      this.realisticOnly(seam);
      this.register(seam, "building");
    }

    this.buildRoofEdges(roof);
    this.buildSolarArray();
  }

  private createRoofLine(
    name: string,
    start: RoofPointMm,
    end: RoofPointMm,
    radiusM: number,
    elevationOffsetM = 0,
  ) {
    return CreateTube(
      name,
      {
        path: [start, end].map(
          (point) =>
            new Vector3(
              xM(point.xMm),
              point.elevationMm * MM_TO_M + elevationOffsetM,
              zM(point.yMm),
            ),
        ),
        radius: radiusM,
        tessellation: 6,
        cap: Mesh.CAP_ALL,
      },
      this.scene,
    );
  }

  private buildGables() {
    const eave = HOUSE.eavesElevationMm * MM_TO_M;
    const ridge = HOUSE.ridgeElevationMm * MM_TO_M;
    const mainMidY = HOUSE.originMm.y + HOUSE.lowerBar.depthMm / 2;
    const garageGableX = HOUSE.originMm.x - 8;
    const garageGable = createVerticalTriangle(
      this.scene,
      "Garážový štít",
      [
        new Vector3(xM(garageGableX), eave, zM(HOUSE.originMm.y)),
        new Vector3(
          xM(garageGableX),
          eave,
          zM(HOUSE.originMm.y + HOUSE.lowerBar.depthMm),
        ),
        new Vector3(xM(garageGableX), ridge, zM(mainMidY)),
      ],
      new Vector3(-1, 0, 0),
    );
    this.appearance(
      garageGable,
      this.materials.wall,
      this.realisticMaterials.wall,
    );
    garageGable.receiveShadows = true;
    this.register(garageGable, "building", HOUSE.id);

    const wingLeftX = HOUSE.originMm.x + HOUSE.wing.xMm;
    const wingRightX = wingLeftX + HOUSE.wing.widthMm;
    // The gable itself is the recessed porch wall, 2 500 mm behind the roof
    // line: the front stays an open frame of white rakes, exactly as the
    // approved reference photograph and the D1.1.006 elevation read.
    const gableYmm = HOUSE.porches.wingEnd.gablePlaneYmm + 20;
    // 22. 8. 2026: the end wall of 1.03 is a glazed gable up to the vaulted
    // ceiling line; only the band between that line and the roof stays larch.
    const vaultWallMm = 2750;
    const vaultRidgeMm = 4850;
    const livingWestXmm = 21543;
    const livingEastXmm = 27541;
    const gableWindow = HOUSE.porches.wingEnd.gableWindow;
    const ringBeamTopMm = HOUSE.porches.wingEnd.ringBeam.topMm;
    const roofAt = (xMm: number) =>
      xMm < (wingLeftX + wingRightX) / 2
        ? wingInnerRoofHeightMm(xMm)
        : wingOuterRoofHeightMm(xMm);
    const vaultHalfSpan = (wingLeftX + wingRightX) / 2 - livingWestXmm;
    const vaultAtX = (xMm: number) =>
      vaultRidgeMm -
      (vaultRidgeMm - vaultWallMm) *
        Math.min(1, Math.abs(xMm - (wingLeftX + wingRightX) / 2) / vaultHalfSpan);
    const apexMm = vaultAtX(gableWindow.apexXmm) - 30;
    // The larch gable above the ring beam, in three pieces around the
    // triangular light: west of it, the wedge above its hypotenuse, and east.
    const larchPieces: ReadonlyArray<readonly { readonly alongMm: number; readonly elevationMm: number }[]> = [
      [
        { alongMm: wingLeftX, elevationMm: HOUSE.eavesElevationMm },
        { alongMm: gableWindow.startXmm, elevationMm: roofAt(gableWindow.startXmm) },
        { alongMm: gableWindow.startXmm, elevationMm: ringBeamTopMm },
        { alongMm: livingWestXmm, elevationMm: ringBeamTopMm },
        { alongMm: livingWestXmm, elevationMm: HOUSE.eavesElevationMm },
      ],
      [
        { alongMm: gableWindow.startXmm, elevationMm: gableWindow.bottomMm },
        { alongMm: gableWindow.endXmm, elevationMm: apexMm },
        { alongMm: gableWindow.endXmm, elevationMm: roofAt(gableWindow.endXmm) },
        { alongMm: gableWindow.startXmm, elevationMm: roofAt(gableWindow.startXmm) },
      ],
      [
        { alongMm: gableWindow.endXmm, elevationMm: ringBeamTopMm },
        { alongMm: livingEastXmm, elevationMm: ringBeamTopMm },
        { alongMm: livingEastXmm, elevationMm: HOUSE.eavesElevationMm },
        { alongMm: wingRightX, elevationMm: HOUSE.eavesElevationMm },
        { alongMm: (wingLeftX + wingRightX) / 2, elevationMm: HOUSE.ridgeElevationMm },
        { alongMm: gableWindow.endXmm, elevationMm: roofAt(gableWindow.endXmm) },
      ],
    ];
    const larchGable = this.larchFor(2.86, 2.44, "wing-gable");
    for (const [index, profile] of larchPieces.entries()) {
      if (index === 0) continue;
      const piece = verticalProfileSolid(
        this.scene,
        `Modřínový štít krytej terasy · diel ${index + 1}`,
        "Y",
        profile,
        gableYmm - 20,
        gableYmm + 36,
      );
      this.appearance(piece, this.materials.wall, larchGable);
      piece.receiveShadows = true;
      piece.checkCollisions = true;
      this.castShadow(piece);
      this.register(piece, "building", HOUSE.id);
    }
    const wingGable = verticalProfileSolid(
      this.scene,
      "Modřínový štít krytej terasy · diel 1",
      "Y",
      larchPieces[0],
      gableYmm - 20,
      gableYmm + 36,
    );
    this.appearance(wingGable, this.materials.wall, larchGable);
    wingGable.receiveShadows = true;
    wingGable.checkCollisions = true;
    this.castShadow(wingGable);
    this.register(wingGable, "building", HOUSE.id);

    const gableRise = ridge - eave;
    for (const [index, lamp] of [
      { x: 22600, elevationM: 3.85 },
      { x: 26400, elevationM: 3.85 },
    ].entries()) {
      const fixture = CreateCylinder(
        `Nástenné svietidlo štítu ${index + 1} · ilustračný koncept`,
        { height: 0.17, diameter: 0.07, tessellation: 24 },
        this.scene,
      );
      fixture.position.set(xM(lamp.x), lamp.elevationM + 0.085, zM(gableYmm + 55));
      fixture.material = this.realisticMaterials.fenceTrack;
      fixture.isPickable = false;
      this.realisticOnly(fixture);
      this.castShadow(fixture);
      this.register(fixture, "building");
      const bracket = boxAtPlan(
        this.scene,
        `Nástenné svietidlo štítu ${index + 1} · konzola`,
        { x: lamp.x, y: gableYmm + 24 },
        24,
        48,
        0.03,
        lamp.elevationM + 0.07,
      );
      bracket.material = this.realisticMaterials.fenceTrack;
      bracket.isPickable = false;
      this.realisticOnly(bracket);
      this.register(bracket, "building");
    }

    // White rake boards of the P04 portal. Their underside runs exactly
    // through the crown corner of each white support (x = 21 040 / 28 040 at
    // +3,125) and their back face is flush with the support front, so the
    // gable frame reads as one continuous white outline standing on the two
    // supports — the defect of a rake floating 80 mm in front of the pillar
    // is gone.
    const portal = HOUSE.porches.wingEnd.portalFrame;
    const halfSpanM = (HOUSE.wing.widthMm * MM_TO_M) / 2;
    const edgeAngle = Math.atan2(gableRise, halfSpanM);
    const rakeHeightM = portal.rakeHeightMm * MM_TO_M;
    const rakeDepthM = (portal.rakeFrontFaceYmm - portal.rakeBackFaceYmm) * MM_TO_M;
    const rakeZ = zM((portal.rakeBackFaceYmm + portal.rakeFrontFaceYmm) / 2);
    // Extend each board past the apex so the two meet in a clean mitre.
    const apexExtensionM = (rakeHeightM / 2) * Math.tan(edgeAngle);
    const gableEdgeLength = Math.hypot(halfSpanM, gableRise) + apexExtensionM;
    const liftM = rakeHeightM / 2 / Math.cos(edgeAngle);
    for (const side of [-1, 1]) {
      const edge = CreateBox(
        `Biely rám záhradného štítu ${side}`,
        { width: gableEdgeLength, depth: rakeDepthM, height: rakeHeightM },
        this.scene,
      );
      const startX = xM(wingLeftX + (side < 0 ? 0 : HOUSE.wing.widthMm));
      const direction = -side;
      const centerAlong = gableEdgeLength / 2;
      edge.position.set(
        startX + direction * Math.cos(edgeAngle) * centerAlong,
        eave + Math.sin(edgeAngle) * centerAlong + liftM,
        rakeZ,
      );
      edge.rotation.z = -side * edgeAngle;
      edge.material = this.realisticMaterials.wall;
      edge.isPickable = false;
      this.realisticOnly(edge);
      this.castShadow(edge);
      this.register(edge, "building");
    }
    // Apex cover plate hiding the mitre joint of the two rakes.
    const apexPlate = CreateBox(
      "Biely rám záhradného štítu · vrcholový spoj",
      { width: 0.2, depth: rakeDepthM + 0.004, height: rakeHeightM * 0.6 },
      this.scene,
    );
    apexPlate.position.set(
      xM(wingLeftX + HOUSE.wing.widthMm / 2),
      ridge + liftM + rakeHeightM * 0.1,
      rakeZ,
    );
    apexPlate.material = this.realisticMaterials.wall;
    apexPlate.isPickable = false;
    this.realisticOnly(apexPlate);
    this.register(apexPlate, "building");
  }

  private buildRoofEdges(roof: JoinedRoofGeometry) {
    const { parameters } = roof;
    const rakeFrontYmm = HOUSE.porches.wingEnd.portalFrame.rakeFrontFaceYmm;
    const specs = [
      {
        name: "Predný krytý žľab · vizualizačný profil",
        center: {
          x: (parameters.minXmm + parameters.maxXmm) / 2,
          y: parameters.frontEaveYmm - 60,
        },
        widthMm: parameters.maxXmm - parameters.minXmm + 120,
        depthMm: 105,
      },
      {
        name: "Záhradný krytý žľab · vizualizačný profil",
        center: {
          x: (parameters.minXmm + parameters.wingInnerEaveXmm) / 2,
          y: parameters.gardenEaveYmm + 60,
        },
        widthMm: parameters.wingInnerEaveXmm - parameters.minXmm + 120,
        depthMm: 105,
      },
      // Both wing gutters stop flush with the front face of the white rake
      // boards so nothing pokes past the P04 portal frame.
      {
        name: "Vnútorná okapová hrana krídla · vizualizačný profil",
        center: {
          x: parameters.wingInnerEaveXmm - 60,
          y: (parameters.gardenEaveYmm - 60 + rakeFrontYmm) / 2,
        },
        widthMm: 105,
        depthMm: rakeFrontYmm - parameters.gardenEaveYmm + 60,
      },
      {
        name: "Vonkajšia okapová hrana krídla · vizualizačný profil",
        center: {
          x: parameters.maxXmm + 60,
          y: (parameters.frontEaveYmm - 60 + rakeFrontYmm) / 2,
        },
        widthMm: 105,
        depthMm: rakeFrontYmm - parameters.frontEaveYmm + 60,
      },
    ];
    for (const spec of specs) {
      const edge = boxAtPlan(
        this.scene,
        spec.name,
        spec.center,
        spec.widthMm,
        spec.depthMm,
        0.105,
        3.02,
      );
      edge.material = this.realisticMaterials.roofEdge;
      edge.isPickable = false;
      this.realisticOnly(edge);
      this.castShadow(edge);
      this.register(edge, "building");
    }

    const ridgeJointClearanceMm = 90;
    for (const ridge of [
      {
        name: "Hrebeňový profil hlavného traktu",
        center: {
          x:
            (parameters.minXmm +
              parameters.wingRidgeXmm -
              ridgeJointClearanceMm) /
            2,
          y: parameters.mainRidgeYmm,
        },
        widthMm:
          parameters.wingRidgeXmm -
          ridgeJointClearanceMm -
          parameters.minXmm,
        depthMm: 125,
      },
      {
        name: "Hrebeňový profil krídla",
        center: {
          x: parameters.wingRidgeXmm,
          y:
            (parameters.mainRidgeYmm +
              ridgeJointClearanceMm +
              parameters.wingEndYmm) /
            2,
        },
        widthMm: 125,
        depthMm:
          parameters.wingEndYmm -
          parameters.mainRidgeYmm -
          ridgeJointClearanceMm,
      },
    ]) {
      const cap = boxAtPlan(
        this.scene,
        ridge.name,
        ridge.center,
        ridge.widthMm,
        ridge.depthMm,
        0.06,
        HOUSE.ridgeElevationMm * MM_TO_M - 0.015,
      );
      cap.material = this.realisticMaterials.roofEdge;
      cap.isPickable = false;
      this.realisticOnly(cap);
      this.castShadow(cap);
      this.register(cap, "building");
    }

    const ridgeJunction = boxAtPlan(
      this.scene,
      "Tvarovaný spoj krížových hrebeňov",
      { x: parameters.wingRidgeXmm, y: parameters.mainRidgeYmm },
      245,
      245,
      0.075,
      HOUSE.ridgeElevationMm * MM_TO_M - 0.005,
    );
    ridgeJunction.material = this.realisticMaterials.roofEdge;
    ridgeJunction.isPickable = false;
    this.realisticOnly(ridgeJunction);
    this.castShadow(ridgeJunction);
    this.register(ridgeJunction, "building");

    for (const feature of [roof.valley, roof.hip]) {
      const profile = this.createRoofLine(
        feature.kind === "VALLEY"
          ? "Úžľabný lem · D1.1.004"
          : "Nárožný lem · D1.1.004",
        roof.vertices[feature.startVertexIndex],
        roof.vertices[feature.endVertexIndex],
        feature.kind === "VALLEY" ? 0.024 : 0.046,
        feature.kind === "VALLEY" ? 0.008 : 0.024,
      );
      profile.material = this.realisticMaterials.roofEdge;
      profile.isPickable = false;
      this.realisticOnly(profile);
      this.castShadow(profile);
      this.register(profile, "building");
    }

    for (const gable of roof.gables) {
      const [leftIndex, ridgeIndex, rightIndex] = gable.vertexIndices;
      for (const [segmentIndex, [startIndex, endIndex]] of [
        [0, [leftIndex, ridgeIndex]],
        [1, [ridgeIndex, rightIndex]],
      ] as const) {
        const rake = this.createRoofLine(
          `${gable.id} · strešná hrana ${segmentIndex + 1}`,
          roof.vertices[startIndex],
          roof.vertices[endIndex],
          0.038,
          0.008,
        );
        rake.material = this.realisticMaterials.roofEdge;
        rake.isPickable = false;
        this.realisticOnly(rake);
        this.castShadow(rake);
        this.register(rake, "building");
      }
    }
  }

  private buildSolarArray() {
    const roof = deriveJoinedRoofGeometry();
    const { parameters } = roof;
    const photovoltaics = HOUSE.photovoltaics;
    if (
      photovoltaics.rows * photovoltaics.columns !==
      photovoltaics.moduleCount
    ) {
      throw new Error("FV rozloženie nezodpovedá počtu modulov.");
    }
    if (photovoltaics.roofFace !== "WING_INNER") {
      throw new Error("FV pole posunuté do záhrady musí zostať na dvorovej rovine krídla.");
    }
    for (let column = 0; column < photovoltaics.columns; column += 1) {
      for (let row = 0; row < photovoltaics.rows; row += 1) {
        const centerXmm =
          photovoltaics.firstModuleCenterMm.x +
          row * photovoltaics.rowStepMm.x +
          column * photovoltaics.columnStepMm.x;
        const centerYmm =
          photovoltaics.firstModuleCenterMm.y +
          row * photovoltaics.rowStepMm.y +
          column * photovoltaics.columnStepMm.y;
        const mount = roofMountTransform(
          photovoltaics.roofFace,
          centerXmm,
          centerYmm,
          parameters,
        );
        const surfaceElevationM = mount.elevationMm * MM_TO_M;
        const panel = CreateBox(
          `Fotovoltický panel ${column + 1}.${row + 1} · dvorová rovina posunutá do záhrady`,
          {
            width: photovoltaics.moduleSlopeLengthMm * MM_TO_M,
            depth: photovoltaics.moduleRidgeWidthMm * MM_TO_M,
            height: 0.035,
          },
          this.scene,
        );
        panel.position.set(
          xM(centerXmm),
          surfaceElevationM + 0.05,
          zM(centerYmm),
        );
        panel.rotation.x = mount.rotationXRad;
        panel.rotation.z = mount.rotationZRad;
        panel.material = this.realisticMaterials.solar;
        panel.isPickable = false;
        this.realisticOnly(panel);
        this.castShadow(panel);
        this.register(panel, "building");

        const panelWidthM = photovoltaics.moduleSlopeLengthMm * MM_TO_M;
        const panelDepthM = photovoltaics.moduleRidgeWidthMm * MM_TO_M;
        const frameProfiles = [
          {
            name: "horný",
            width: panelWidthM + 0.038,
            depth: 0.032,
            x: 0,
            z: panelDepthM / 2 + 0.003,
          },
          {
            name: "dolný",
            width: panelWidthM + 0.038,
            depth: 0.032,
            x: 0,
            z: -panelDepthM / 2 - 0.003,
          },
          {
            name: "ľavý",
            width: 0.032,
            depth: panelDepthM,
            x: -panelWidthM / 2 - 0.003,
            z: 0,
          },
          {
            name: "pravý",
            width: 0.032,
            depth: panelDepthM,
            x: panelWidthM / 2 + 0.003,
            z: 0,
          },
        ];
        for (const profile of frameProfiles) {
          const frame = CreateBox(
            `Rám FV ${column + 1}.${row + 1} · ${profile.name}`,
            { width: profile.width, depth: profile.depth, height: 0.026 },
            this.scene,
          );
          frame.parent = panel;
          frame.position.set(profile.x, 0.031, profile.z);
          frame.material = this.realisticMaterials.solarGrid;
          frame.isPickable = false;
          this.realisticOnly(frame);
          this.castShadow(frame);
          this.register(frame, "building");
        }

        for (const [railIndex, localX] of [
          -panelWidthM * 0.28,
          panelWidthM * 0.28,
        ].entries()) {
          const rail = CreateBox(
            `Montážna lišta FV ${column + 1}.${row + 1}.${railIndex + 1}`,
            { width: 0.055, depth: panelDepthM * 0.9, height: 0.035 },
            this.scene,
          );
          rail.parent = panel;
          rail.position.set(localX, -0.038, 0);
          rail.material = this.realisticMaterials.solarGrid;
          rail.isPickable = false;
          this.realisticOnly(rail);
          this.castShadow(rail);
          this.register(rail, "building");

          for (const localZ of [-panelDepthM * 0.36, panelDepthM * 0.36]) {
            const clamp = CreateBox(
              `Príchytka FV ${column + 1}.${row + 1}`,
              { width: 0.09, depth: 0.045, height: 0.025 },
              this.scene,
            );
            clamp.parent = panel;
            clamp.position.set(localX, 0.028, localZ);
            clamp.material = this.realisticMaterials.solarGrid;
            clamp.isPickable = false;
            this.realisticOnly(clamp);
            this.register(clamp, "building");
          }
        }
      }
    }
  }

  private buildRealisticHouseShell() {
    const heightMm = HOUSE.eavesElevationMm;
    const porch = HOUSE.porches.wingEnd;
    const loggia = HOUSE.porches.gardenLoggia;

    const frontOpenings: readonly FacadeOpeningMm[] = [
      {
        id: HOUSE.facades.front.garageDoor.id,
        startMm: HOUSE.facades.front.garageDoor.startXmm,
        widthMm: HOUSE.facades.front.garageDoor.widthMm,
        heightMm: HOUSE.facades.front.garageDoor.heightMm,
        sillMm: HOUSE.facades.front.garageDoor.sillMm,
      },
      ...HOUSE.facades.front.openings.map((opening) => ({
        id: opening.id,
        startMm: opening.startXmm,
        widthMm: opening.widthMm,
        heightMm: opening.heightMm,
        sillMm: opening.sillMm,
      })),
    ];
    const eastOpenings: readonly FacadeOpeningMm[] =
      HOUSE.facades.east.openings.map((opening) => ({
        id: opening.id,
        startMm: opening.startYmm,
        widthMm: opening.widthMm,
        heightMm: opening.heightMm,
        sillMm: opening.sillMm,
      }));
    // Garden facade: two flush glazed openings plus the open loggia bay taken
    // straight from D1.1.002 (P01 beam over a 3 200 mm opening).
    const gardenOpenings: readonly FacadeOpeningMm[] = [
      {
        id: loggia.id,
        startMm: loggia.openingStartXmm,
        widthMm: loggia.openingEndXmm - loggia.openingStartXmm,
        heightMm: 2400,
        sillMm: 0,
      },
      ...HOUSE.facades.garden.openings
        .filter((opening) => opening.id !== "GARDEN-01")
        .map((opening) => ({
          id: opening.id,
          startMm: opening.startXmm,
          widthMm: opening.widthMm,
          heightMm: opening.heightMm,
          sillMm: opening.sillMm,
        })),
    ];
    const westOpenings: readonly FacadeOpeningMm[] = [
      {
        id: HOUSE.facades.west.garageWindow.id,
        startMm: HOUSE.facades.west.garageWindow.startYmm,
        widthMm: HOUSE.facades.west.garageWindow.widthMm,
        heightMm: HOUSE.facades.west.garageWindow.heightMm,
        sillMm: HOUSE.facades.west.garageWindow.sillMm,
      },
      {
        id: HOUSE.facades.west.loggiaOpening.id,
        startMm: HOUSE.facades.west.loggiaOpening.startYmm,
        widthMm: HOUSE.facades.west.loggiaOpening.widthMm,
        heightMm: HOUSE.facades.west.loggiaOpening.heightMm,
        sillMm: HOUSE.facades.west.loggiaOpening.sillMm,
      },
    ];
    // Wing west wall ends at 19 535; beyond it the porch is open with the
    // 500 × 500 corner pillar carrying the P03 beam.
    const wingWestOpenings: readonly FacadeOpeningMm[] = [
      {
        id: HOUSE.facades.wingWest.opening.id,
        startMm: HOUSE.facades.wingWest.opening.startYmm,
        widthMm: HOUSE.facades.wingWest.opening.widthMm,
        heightMm: HOUSE.facades.wingWest.opening.heightMm,
        sillMm: HOUSE.facades.wingWest.opening.sillMm,
      },
      {
        id: "PORCH-WEST-OPEN",
        startMm: porch.westOpening.startYmm,
        widthMm: porch.westOpening.endYmm - porch.westOpening.startYmm,
        heightMm: porch.westOpening.heightMm,
        sillMm: 0,
      },
    ];

    this.buildRealisticZFacade(
      "Južná fasáda",
      HOUSE.facades.front.faceYmm,
      HOUSE.originMm.x,
      HOUSE.facades.east.faceXmm,
      -1,
      heightMm,
      frontOpenings,
      this.realisticMaterials.wall,
    );
    this.buildRealisticZFacade(
      "Záhradná fasáda",
      HOUSE.facades.garden.faceYmm,
      HOUSE.originMm.x,
      HOUSE.originMm.x + HOUSE.wing.xMm,
      1,
      heightMm,
      gardenOpenings,
      this.realisticMaterials.wall,
    );
    this.buildRealisticXFacade(
      "Východná fasáda",
      HOUSE.facades.east.faceXmm,
      HOUSE.originMm.y,
      HOUSE.originMm.y + HOUSE.maximumDepthMm,
      1,
      heightMm,
      eastOpenings,
      this.realisticMaterials.wall,
    );
    this.buildRealisticXFacade(
      "Garážový štít",
      HOUSE.facades.west.faceXmm,
      HOUSE.originMm.y,
      HOUSE.originMm.y + HOUSE.lowerBar.depthMm,
      -1,
      heightMm,
      westOpenings,
      this.realisticMaterials.wall,
    );
    this.buildRealisticXFacade(
      "Západná stena krídla",
      HOUSE.facades.wingWest.faceXmm,
      HOUSE.facades.wingWest.wallStartYmm,
      porch.frontYmm,
      -1,
      heightMm,
      wingWestOpenings,
      this.realisticMaterials.wall,
      500,
    );

    this.buildGardenLoggia();
    this.buildWingPorch();

    // Larch cladding fields between the flush garden windows (reference look).
    for (const [index, span] of [
      { startXmm: 10640, endXmm: 11840 },
      { startXmm: 14340, endXmm: 15840 },
    ].entries()) {
      const widthM = (span.endXmm - span.startXmm) * MM_TO_M;
      const field = boxAtPlan(
        this.scene,
        `Modřínové pole záhradnej fasády ${index + 1}`,
        {
          x: (span.startXmm + span.endXmm) / 2,
          y: HOUSE.facades.garden.faceYmm + 20,
        },
        span.endXmm - span.startXmm,
        40,
        2.75,
        0,
      );
      field.material = this.larchFor(widthM, 2.75, `garden-field-${index}`);
      field.receiveShadows = true;
      field.isPickable = false;
      this.realisticOnly(field);
      this.castShadow(field);
      this.register(field, "building", HOUSE.id);
    }

    for (const opening of HOUSE.facades.front.openings) {
      const style = resolveFacadeOpeningStyle(opening, "FRONT-ENTRY");
      this.buildWindowOnZFace(
        `Výplň otvoru ${opening.id} · D1.1.002`,
        opening.startXmm + opening.widthMm / 2,
        HOUSE.facades.front.faceYmm,
        opening.widthMm,
        opening.heightMm,
        opening.sillMm,
        -1,
        this.realisticMaterials.wall,
        this.realisticMaterials.glassFrame,
        style.kind,
        530,
        style.frameWidthMm,
        opening.id === "FRONT-ENTRY"
          ? { id: opening.id, label: "Hlavné vstupné dvere" }
          : undefined,
      );
    }
    for (const opening of HOUSE.facades.garden.openings) {
      if (opening.id === "GARDEN-01") continue;
      this.buildWindowOnZFace(
        `Terasové presklenie ${opening.widthMm} · D1.1.002`,
        opening.startXmm + opening.widthMm / 2,
        HOUSE.facades.garden.faceYmm,
        opening.widthMm,
        opening.heightMm,
        opening.sillMm,
        1,
        this.realisticMaterials.wall,
        this.realisticMaterials.glassFrameWood,
        "sliding",
        530,
        undefined,
        { id: opening.id, label: `Terasové posuvné dvere ${opening.id}` },
      );
    }
    for (const opening of eastOpenings) {
      this.buildWindowOnXFace(
        `Bočná výplň otvoru ${opening.id} · D1.1.002`,
        HOUSE.facades.east.faceXmm,
        opening.startMm + opening.widthMm / 2,
        opening.widthMm,
        opening.heightMm,
        opening.sillMm,
        1,
        this.realisticMaterials.wall,
        this.realisticMaterials.glassFrame,
        opening.id === "EAST-03" ? "door" : "window",
        530,
        opening.id === "EAST-03"
          ? { id: opening.id, label: "Bočné dvere technickej miestnosti" }
          : undefined,
      );
    }
    const garageSideWindow = HOUSE.facades.west.garageWindow;
    this.buildWindowOnXFace(
      `Bočné garážové okno ${garageSideWindow.id} · podľa FRONT-02`,
      HOUSE.facades.west.faceXmm,
      garageSideWindow.startYmm + garageSideWindow.widthMm / 2,
      garageSideWindow.widthMm,
      garageSideWindow.heightMm,
      garageSideWindow.sillMm,
      -1,
      this.realisticMaterials.wall,
      this.realisticMaterials.glassFrame,
      "window",
    );
    // Wing west sliding glazing onto the terrace walkway.
    this.buildWindowOnXFace(
      "Terasové posuvné presklenie 2 250 · D1.1.002",
      HOUSE.facades.wingWest.faceXmm,
      HOUSE.facades.wingWest.opening.startYmm + HOUSE.facades.wingWest.opening.widthMm / 2,
      HOUSE.facades.wingWest.opening.widthMm,
      HOUSE.facades.wingWest.opening.heightMm,
      HOUSE.facades.wingWest.opening.sillMm,
      -1,
      this.realisticMaterials.wall,
      this.realisticMaterials.glassFrameWood,
      "sliding",
      500,
      {
        id: HOUSE.facades.wingWest.opening.id,
        label: "Posuvné dvere z obývacej izby na terasu",
      },
    );
  }

  /** Interior fit-out of 1.NP traced from D1.1.002 (see twin-interior.ts). */
  private buildInteriorFitOut() {
    buildInterior({
      scene: this.scene,
      anisotropy: this.renderQuality.anisotropy,
      wall: this.realisticMaterials.wall,
      soffit: this.realisticMaterials.soffit,
      glassFrame: this.realisticMaterials.glassFrame,
      chimneyMetal: this.realisticMaterials.chimneyMetal,
      timber: this.realisticMaterials.timber,
      register: (mesh, layer, entityId) => this.register(mesh, layer, entityId),
      realisticOnly: (mesh) => this.realisticOnly(mesh),
      castShadow: (mesh) => this.castShadow(mesh),
      registerAnimatedDoor: (door: AnimatedDoorRegistration) =>
        this.doors.register(door),
    });
  }

  /** Garden loggia recessed 2 953 mm behind the garden facade (D1.1.002). */
  private buildGardenLoggia() {
    const loggia = HOUSE.porches.gardenLoggia;
    const soffitM = loggia.soffitElevationMm * MM_TO_M;

    const backOpenings: readonly FacadeOpeningMm[] = [
      {
        id: loggia.backDoor.id,
        startMm: loggia.backDoor.startXmm,
        widthMm: loggia.backDoor.widthMm,
        heightMm: loggia.backDoor.heightMm,
        sillMm: loggia.backDoor.sillMm,
      },
    ];
    for (const [index, segment] of segmentFacadeMm(
      loggia.cornerPier.startXmm + 500,
      loggia.eastInnerXmm,
      loggia.soffitElevationMm,
      backOpenings,
    ).entries()) {
      const mesh = boxAtPlan(
        this.scene,
        `Lodžia · zadná stena ${index + 1}`,
        {
          x: (segment.startMm + segment.endMm) / 2,
          y: loggia.backFaceYmm - 250,
        },
        segment.endMm - segment.startMm,
        500,
        (segment.topMm - segment.bottomMm) * MM_TO_M,
        segment.bottomMm * MM_TO_M,
      );
      mesh.material = this.realisticMaterials.wall;
      mesh.receiveShadows = true;
      this.realisticOnly(mesh);
      this.register(mesh, "building", HOUSE.id);
    }
    // Larch cladding band on the back wall (7 236 – 9 086 per plan).
    const larchWidthM = (loggia.backLarch.endXmm - loggia.backLarch.startXmm) * MM_TO_M;
    const backLarch = boxAtPlan(
      this.scene,
      "Lodžia · modřínový obklad zadnej steny",
      {
        x: (loggia.backLarch.startXmm + loggia.backLarch.endXmm) / 2,
        y: loggia.backFaceYmm + 18,
      },
      loggia.backLarch.endXmm - loggia.backLarch.startXmm,
      36,
      soffitM,
      0,
    );
    backLarch.material = this.larchFor(larchWidthM, soffitM, "loggia-back");
    backLarch.receiveShadows = true;
    backLarch.isPickable = false;
    this.realisticOnly(backLarch);
    this.register(backLarch, "building", HOUSE.id);

    this.buildWindowOnZFace(
      "Lodžia · presklené dvere 1 250 · D1.1.002",
      loggia.backDoor.startXmm + loggia.backDoor.widthMm / 2,
      loggia.backFaceYmm,
      loggia.backDoor.widthMm,
      loggia.backDoor.heightMm,
      loggia.backDoor.sillMm,
      1,
      this.realisticMaterials.wall,
      this.realisticMaterials.glassFrameWood,
      "door",
      530,
      undefined,
      { id: loggia.backDoor.id, label: "Dvere zo záhradnej lodžie" },
    );

    // East inner cheek of the loggia (room 1.10 west wall).
    const cheek = boxAtPlan(
      this.scene,
      "Lodžia · východná bočná stena",
      { x: loggia.eastInnerXmm + 200, y: (loggia.backFaceYmm + loggia.faceYmm) / 2 },
      400,
      loggia.faceYmm - loggia.backFaceYmm,
      EAVES_M,
      0,
    );
    cheek.material = this.realisticMaterials.wall;
    cheek.receiveShadows = true;
    this.realisticOnly(cheek);
    this.castShadow(cheek);
    this.register(cheek, "building", HOUSE.id);

    // Flat white soffit over the loggia.
    const soffit = boxAtPlan(
      this.scene,
      "Lodžia · podhľad +2,750",
      {
        x: (loggia.cornerPier.startXmm + loggia.eastInnerXmm) / 2,
        y: (loggia.backFaceYmm + loggia.faceYmm) / 2,
      },
      loggia.eastInnerXmm - loggia.cornerPier.startXmm,
      loggia.faceYmm - loggia.backFaceYmm,
      0.06,
      soffitM,
    );
    soffit.material = this.realisticMaterials.soffit;
    soffit.isPickable = false;
    this.realisticOnly(soffit);
    this.register(soffit, "building", HOUSE.id);
  }

  /**
   * End wall of 1.03 toward the covered porch (22. 8. 2026, final client
   * wording with the reference photograph): a 500 mm pier beside the corner
   * pillar, a single FIXED 2 000 glass pane (no door), a closed ring-beam
   * band above it, and above the band only a small right-triangle light of
   * the pane width — sloped side along the vaulted ceiling, vertical side on
   * the pane's east edge. The remaining 3 500 is the larch-clad solid wall;
   * every other part of the gable is larch outside and plaster inside.
   */
  private buildPorchCurtainWall() {
    const porch = HOUSE.porches.wingEnd;
    const glazing = porch.glazing;
    const gable = porch.gableWindow;
    const beam = porch.ringBeam;
    const faceYmm = porch.glazingFaceYmm;
    const frame = this.realisticMaterials.glassFrame;
    const vaultWallMm = 2750;
    const vaultRidgeMm = 4850;
    const ridgeXmm = HOUSE.originMm.x + HOUSE.wing.xMm + HOUSE.roof.wingHalfSpanMm;
    const westXmm = 21543;
    const vaultAt = (xMm: number) =>
      vaultRidgeMm -
      (vaultRidgeMm - vaultWallMm) *
        Math.min(1, Math.abs(xMm - ridgeXmm) / (ridgeXmm - westXmm));
    const planeYmm = faceYmm - 150;
    const barDepthMm = 100;
    const barWidthMm = 70;

    // ---- fixed pane 0 → +2,750 (real joinery, no sash, no door)
    this.buildWindowOnZFace(
      "Krytá terasa · pevné presklenie 2 000 · revízia 22. 8. 2026",
      glazing.startXmm + glazing.widthMm / 2,
      faceYmm,
      glazing.widthMm,
      glazing.heightMm,
      glazing.sillMm,
      1,
      this.realisticMaterials.wall,
      frame,
      "fixed",
      500,
    );

    // ---- masonry below the ring beam: west pier and the back wall
    const masonry = (label: string, startXmm: number, endXmm: number, bottomMm: number, topMm: number) => {
      const block = boxAtPlan(
        this.scene,
        label,
        { x: (startXmm + endXmm) / 2, y: faceYmm - 250 },
        endXmm - startXmm,
        500,
        (topMm - bottomMm) * MM_TO_M,
        bottomMm * MM_TO_M,
      );
      block.material = this.realisticMaterials.wall;
      block.receiveShadows = true;
      block.checkCollisions = true;
      this.castShadow(block);
      this.realisticOnly(block);
      this.register(block, "building", HOUSE.id);
      const widthM = (endXmm - startXmm) * MM_TO_M;
      const heightM = (topMm - bottomMm) * MM_TO_M;
      const larch = boxAtPlan(
        this.scene,
        `${label} · modřínový obklad`,
        { x: (startXmm + endXmm) / 2, y: faceYmm + 18 },
        endXmm - startXmm,
        36,
        heightM,
        bottomMm * MM_TO_M,
      );
      larch.material = this.larchFor(widthM, heightM, `porch-${startXmm}-${bottomMm}`);
      larch.receiveShadows = true;
      larch.isPickable = false;
      this.realisticOnly(larch);
      this.register(larch, "building", HOUSE.id);
    };
    masonry("Krytá terasa · murovaný pilier pri rohu", porch.westPier.startXmm, porch.westPier.endXmm, 0, beam.bottomMm);
    masonry("Krytá terasa · plná zadná stena", porch.backWall.startXmm, porch.backWall.endXmm, 0, porch.backWall.topMm);
    // Ring beam band across the whole end wall, closed above the pane.
    masonry("Krytá terasa · pás venca +2,750 → +3,050", beam.spanStartXmm, beam.spanEndXmm, beam.bottomMm, beam.topMm);

    // ---- interior plaster above the band up to the vault line, leaving the
    // triangular light open
    const closure = verticalProfileSolid(
      this.scene,
      "Krytá terasa · štít nad vencom · interiérová omietka",
      "Y",
      [
        { alongMm: westXmm, elevationMm: beam.topMm },
        { alongMm: porch.backWall.endXmm + 1, elevationMm: beam.topMm },
        { alongMm: ridgeXmm, elevationMm: vaultAt(ridgeXmm) },
        { alongMm: gable.endXmm, elevationMm: vaultAt(gable.endXmm) },
        { alongMm: gable.endXmm, elevationMm: gable.bottomMm },
        { alongMm: gable.startXmm, elevationMm: gable.bottomMm },
        { alongMm: gable.startXmm, elevationMm: vaultAt(gable.startXmm) },
      ],
      faceYmm - 500,
      faceYmm,
    );
    closure.material = this.realisticMaterials.wall;
    closure.receiveShadows = true;
    closure.checkCollisions = true;
    this.realisticOnly(closure);
    this.register(closure, "building", HOUSE.id);

    // ---- triangular light above the band: base = pane width, apex on the
    // east edge at the vault line, hypotenuse along the ceiling slope.
    const apexMm = vaultAt(gable.apexXmm) - 30;
    const x0 = gable.startXmm;
    const x1 = gable.endXmm;
    const baseMm = gable.bottomMm;
    const pane = verticalProfileSolid(
      this.scene,
      "Štítový trojuholníkový svetlík · zasklenie",
      "Y",
      [
        { alongMm: x0 + barWidthMm, elevationMm: baseMm + barWidthMm },
        { alongMm: x1 - barWidthMm, elevationMm: baseMm + barWidthMm },
        { alongMm: x1 - barWidthMm, elevationMm: apexMm - barWidthMm },
      ],
      planeYmm - 12,
      planeYmm + 12,
    );
    this.appearance(pane, this.materials.glass, this.realisticMaterials.glass);
    pane.isPickable = false;
    pane.checkCollisions = true;
    this.register(pane, "building");
    const bottomRail = boxAtPlan(
      this.scene,
      "Štítový trojuholníkový svetlík · spodný priečnik",
      { x: (x0 + x1) / 2, y: planeYmm },
      x1 - x0,
      barDepthMm,
      barWidthMm * MM_TO_M,
      baseMm * MM_TO_M,
    );
    const post = boxAtPlan(
      this.scene,
      "Štítový trojuholníkový svetlík · zvislý stĺpik",
      { x: x1 - barWidthMm / 2, y: planeYmm },
      barWidthMm,
      barDepthMm,
      (apexMm - baseMm) * MM_TO_M,
      baseMm * MM_TO_M,
    );
    const runM = (x1 - x0) * MM_TO_M;
    const riseM = (apexMm - baseMm) * MM_TO_M;
    const rail = boxAtPlan(
      this.scene,
      "Štítový trojuholníkový svetlík · šikmý rám",
      { x: (x0 + x1) / 2, y: planeYmm },
      Math.round(Math.hypot(runM, riseM) * 1000) + barWidthMm,
      barDepthMm,
      barWidthMm * MM_TO_M,
      ((baseMm + apexMm) / 2) * MM_TO_M - (barWidthMm / 2) * MM_TO_M,
    );
    rail.rotation.z = Math.atan2(riseM, runM);
    for (const bar of [bottomRail, post, rail]) {
      bar.material = frame;
      bar.isPickable = false;
      bar.checkCollisions = true;
      this.realisticOnly(bar);
      this.castShadow(bar);
      this.register(bar, "building", HOUSE.id);
    }
  }

  /** Covered gable porch of the wing — glazing recessed 2.5 m (D1.1.002). */
  private buildWingPorch() {
    const porch = HOUSE.porches.wingEnd;
    const roofParameters = deriveJoinedRoofGeometry().parameters;
    const clearanceMm = porch.ceilingClearanceMm;

    this.buildPorchCurtainWall();

    // Larch lining on the east porch cheek (inner face of the east wall).
    const cheekDepthM = (porch.frontYmm - porch.glazingFaceYmm) * MM_TO_M;
    const eastLiningTopM =
      (wingOuterRoofHeightMm(porch.eastWallInnerXmm, roofParameters) -
        clearanceMm) *
      MM_TO_M;
    const eastLining = boxAtPlan(
      this.scene,
      "Krytá terasa · modřínový obklad východnej steny",
      {
        x: porch.eastWallInnerXmm + 18,
        y: (porch.glazingFaceYmm + porch.frontYmm) / 2,
      },
      36,
      porch.frontYmm - porch.glazingFaceYmm,
      eastLiningTopM,
      0,
    );
    eastLining.material = this.larchFor(cheekDepthM, eastLiningTopM, "porch-cheek");
    eastLining.receiveShadows = true;
    eastLining.isPickable = false;
    this.realisticOnly(eastLining);
    this.register(eastLining, "building", HOUSE.id);

    // The porch is open to the roof: instead of a flat ceiling, two boarded
    // panels follow the wing roof planes up to the ridge, so the space reads
    // as tall and uncovered from the garden.
    const porchDepthMm = porch.frontYmm - porch.glazingFaceYmm;
    const porchCenterYmm = (porch.glazingFaceYmm + porch.frontYmm) / 2;
    for (const [index, slope] of [
      {
        name: "západná",
        startXmm: roofParameters.wingInnerEaveXmm,
        endXmm: roofParameters.wingRidgeXmm,
        heightAt: wingInnerRoofHeightMm,
      },
      {
        name: "východná",
        startXmm: roofParameters.wingRidgeXmm,
        endXmm: roofParameters.maxXmm,
        heightAt: wingOuterRoofHeightMm,
      },
    ].entries()) {
      const startM =
        (slope.heightAt(slope.startXmm, roofParameters) - clearanceMm) * MM_TO_M;
      const endM =
        (slope.heightAt(slope.endXmm, roofParameters) - clearanceMm) * MM_TO_M;
      const runM = (slope.endXmm - slope.startXmm) * MM_TO_M;
      const riseM = endM - startM;
      const lengthM = Math.hypot(runM, riseM);
      const thicknessM = 0.045;
      const panel = boxAtPlan(
        this.scene,
        `Krytá terasa · ${slope.name} strešná podbitka`,
        { x: (slope.startXmm + slope.endXmm) / 2, y: porchCenterYmm },
        Math.round(lengthM * 1000),
        porchDepthMm,
        thicknessM,
        (startM + endM) / 2 - thicknessM / 2,
      );
      panel.rotation.z = Math.atan2(riseM, runM);
      panel.material = this.larchFor(lengthM, porchDepthMm * MM_TO_M, `porch-ceiling-${index}`);
      panel.receiveShadows = true;
      panel.isPickable = false;
      this.realisticOnly(panel);
      this.register(panel, "building", HOUSE.id);
    }

    // P04 portal supports: continue both white supports above the +3,125
    // wall crown with a sloped head that follows the roof plane, so the
    // pillar and the east wall end meet the boarded soffit and the rake
    // without any gap — one continuous white frame from the deck to the apex.
    for (const support of porch.portalFrame.supportsMm) {
      const heightAt =
        support.startXmm < roofParameters.wingRidgeXmm
          ? wingInnerRoofHeightMm
          : wingOuterRoofHeightMm;
      const crownMm = HOUSE.eavesElevationMm;
      const profile = [
        { alongMm: support.startXmm, elevationMm: crownMm },
        { alongMm: support.endXmm, elevationMm: crownMm },
        { alongMm: support.endXmm, elevationMm: heightAt(support.endXmm, roofParameters) },
        { alongMm: support.startXmm, elevationMm: heightAt(support.startXmm, roofParameters) },
      ].filter(
        (point, index, points) =>
          index === 0 ||
          Math.abs(point.elevationMm - points[index - 1].elevationMm) > 1 ||
          Math.abs(point.alongMm - points[index - 1].alongMm) > 1,
      );
      // Drop a duplicated closing vertex when the outer edge sits on the crown.
      const last = profile[profile.length - 1];
      if (
        profile.length > 3 &&
        Math.abs(last.alongMm - profile[0].alongMm) < 1 &&
        Math.abs(last.elevationMm - profile[0].elevationMm) < 1
      ) {
        profile.pop();
      }
      const head = verticalProfileSolid(
        this.scene,
        `${support.id} · hlava podpory portálu P04`,
        "Y",
        profile,
        support.startYmm,
        support.endYmm,
      );
      head.material = this.realisticMaterials.wall;
      head.receiveShadows = true;
      head.isPickable = false;
      head.checkCollisions = true;
      this.realisticOnly(head);
      this.castShadow(head);
      this.register(head, "building", HOUSE.id);
    }

    // Two concrete entry steps down to the lawn (reference photograph).
    for (const [index, step] of [
      { y0: porch.frontYmm, y1: porch.frontYmm + 380, top: 0.015 },
      {
        y0: porch.frontYmm + 380,
        y1: porch.frontYmm + 760,
        top: GROUND_Y + 0.01,
      },
    ].entries()) {
      const stepMesh = boxAtPlan(
        this.scene,
        `Krytá terasa · betónový stupeň ${index + 1}`,
        { x: 24540, y: (step.y0 + step.y1) / 2 },
        2400,
        step.y1 - step.y0,
        0.07,
        step.top - 0.07,
      );
      stepMesh.material = this.realisticMaterials.concrete;
      stepMesh.receiveShadows = true;
      stepMesh.isPickable = false;
      this.realisticOnly(stepMesh);
      this.register(stepMesh, "building");
    }
  }

  private buildRealisticZFacade(
    name: string,
    faceYmm: number,
    startXmm: number,
    endXmm: number,
    outwardY: -1 | 1,
    heightMm: number,
    openings: readonly FacadeOpeningMm[],
    finish: PBRMaterial,
    thicknessMmOverride?: number,
  ) {
    const thicknessMm = thicknessMmOverride ?? 530;
    for (const [index, segment] of segmentFacadeMm(startXmm, endXmm, heightMm, openings).entries()) {
      const mesh = boxAtPlan(
        this.scene,
        `${name} · plášť ${index + 1}`,
        {
          x: (segment.startMm + segment.endMm) / 2,
          y: faceYmm - outwardY * thicknessMm / 2,
        },
        segment.endMm - segment.startMm,
        thicknessMm,
        (segment.topMm - segment.bottomMm) * MM_TO_M,
        segment.bottomMm * MM_TO_M,
      );
      mesh.material = finish;
      mesh.receiveShadows = true;
      this.castShadow(mesh);
      this.realisticOnly(mesh);
      this.register(mesh, "building", HOUSE.id);
    }
  }

  private buildRealisticXFacade(
    name: string,
    faceXmm: number,
    startYmm: number,
    endYmm: number,
    outwardX: -1 | 1,
    heightMm: number,
    openings: readonly FacadeOpeningMm[],
    finish: PBRMaterial,
    thicknessMmOverride?: number,
  ) {
    const thicknessMm = thicknessMmOverride ?? 530;
    for (const [index, segment] of segmentFacadeMm(startYmm, endYmm, heightMm, openings).entries()) {
      const mesh = boxAtPlan(
        this.scene,
        `${name} · plášť ${index + 1}`,
        {
          x: faceXmm - outwardX * thicknessMm / 2,
          y: (segment.startMm + segment.endMm) / 2,
        },
        thicknessMm,
        segment.endMm - segment.startMm,
        (segment.topMm - segment.bottomMm) * MM_TO_M,
        segment.bottomMm * MM_TO_M,
      );
      mesh.material = finish;
      mesh.receiveShadows = true;
      this.castShadow(mesh);
      this.realisticOnly(mesh);
      this.register(mesh, "building", HOUSE.id);
    }
  }

  private openingContext() {
    return {
      scene: this.scene,
      materials: {
        glass: this.realisticMaterials.glass,
        technicalGlass: this.materials.glass,
        sillInterior: this.realisticMaterials.sillInterior,
        sillExterior: this.realisticMaterials.fenceMetal,
        handle: this.realisticMaterials.chimneyMetal,
        doorLeaf: this.realisticMaterials.roofEdge,
        curtain: this.realisticMaterials.curtain,
        track: this.realisticMaterials.glassFrame,
      },
      register: (mesh: AbstractMesh, layer: LayerId, entityId?: string) =>
        this.register(mesh, layer, entityId),
      realisticOnly: (mesh: AbstractMesh) => this.realisticOnly(mesh),
      castShadow: (mesh: AbstractMesh) => this.castShadow(mesh),
      appearance: (mesh: AbstractMesh, technical: Material, realistic: Material) =>
        this.appearance(mesh, technical, realistic),
      registerAnimatedDoor: (door: AnimatedDoorRegistration) =>
        this.doors.register(door),
    };
  }

  private buildWindowOnZFace(
    name: string,
    centerXmm: number,
    faceYmm: number,
    widthMm: number,
    heightMm: number,
    sillMm: number,
    outwardY: -1 | 1,
    _revealMaterial: PBRMaterial,
    frameMaterial?: PBRMaterial,
    kind: OpeningVisualKind = sillMm === 0 ? "sliding" : "window",
    wallThicknessMm = 530,
    frameWidthMm?: number,
    interaction?: OpeningInteraction,
  ) {
    buildOpening(this.openingContext(), {
      name,
      axis: "Z",
      faceMm: faceYmm,
      centerMm: centerXmm,
      widthMm,
      heightMm,
      sillMm,
      outward: outwardY,
      wallThicknessMm,
      kind,
      frameMaterial: frameMaterial ?? this.realisticMaterials.glassFrame,
      frameWidthMm,
      entityId: interaction?.id ?? HOUSE.id,
      interaction,
    });
  }

  private buildWindowOnXFace(
    name: string,
    faceXmm: number,
    centerYmm: number,
    widthMm: number,
    heightMm: number,
    sillMm: number,
    outwardX: -1 | 1,
    _revealMaterial: PBRMaterial,
    frameMaterial?: PBRMaterial,
    kind: OpeningVisualKind = sillMm === 0 ? "sliding" : "window",
    wallThicknessMm = 530,
    interaction?: OpeningInteraction,
  ) {
    buildOpening(this.openingContext(), {
      name,
      axis: "X",
      faceMm: faceXmm,
      centerMm: centerYmm,
      widthMm,
      heightMm,
      sillMm,
      outward: outwardX,
      wallThicknessMm,
      kind,
      frameMaterial: frameMaterial ?? this.realisticMaterials.glassFrame,
      entityId: interaction?.id ?? HOUSE.id,
      interaction,
    });
  }

  private buildDeckZone(zone: TerraceZoneD1) {
    const plankMm = 145;
    const gapMm = 8;
    const stepMm = plankMm + gapMm;
    const thicknessM = 0.028;
    const topM = 0.02;
    const material = this.realisticMaterials.deck.clone(
      `${zone.id} · PBR materiál`,
    ) as PBRMaterial;
    const baseAlbedo = this.realisticMaterials.deck.albedoTexture as Texture | null;
    if (baseAlbedo) {
      const albedo = baseAlbedo.clone() as Texture;
      albedo.uScale = 1;
      albedo.vScale = 1;
      material.albedoTexture = albedo;
    }
    const baseBump = this.realisticMaterials.deck.bumpTexture as Texture | null;
    if (baseBump) {
      const bump = baseBump.clone() as Texture;
      bump.uScale = 1;
      bump.vScale = 1;
      material.bumpTexture = bump;
    }

    for (const rect of zone.rectsMm) {
      const underlay = boxAtPlan(
        this.scene,
        `${zone.label} · podkladový rošt`,
        { x: (rect.x0 + rect.x1) / 2, y: (rect.y0 + rect.y1) / 2 },
        rect.x1 - rect.x0,
        rect.y1 - rect.y0,
        0.02,
        topM - thicknessM - 0.021,
      );
      underlay.material = this.realisticMaterials.interiorDark;
      underlay.isPickable = false;
      this.realisticOnly(underlay);
      this.register(underlay, "street", zone.id);
    }

    const planks: Mesh[] = [];
    let rowIndex = 0;
    for (const rect of zone.rectsMm) {
      for (let y = rect.y0 + gapMm; y < rect.y1 - 40; y += stepMm) {
        const y1 = Math.min(y + plankMm, rect.y1);
        const totalLengthMm = rect.x1 - rect.x0;
        const segmentCount = Math.max(1, Math.ceil(totalLengthMm / 3_600));
        const boundaries = [rect.x0];
        for (let segment = 1; segment < segmentCount; segment += 1) {
          const staggerMm = (((rowIndex + segment) % 3) - 1) * 170;
          boundaries.push(
            rect.x0 + (totalLengthMm * segment) / segmentCount + staggerMm,
          );
        }
        boundaries.push(rect.x1);
        for (let segment = 0; segment < boundaries.length - 1; segment += 1) {
          const segmentStartMm = boundaries[segment] + (segment > 0 ? 4 : 0);
          const segmentEndMm =
            boundaries[segment + 1] -
            (segment < boundaries.length - 2 ? 4 : 0);
          const lengthM = (segmentEndMm - segmentStartMm) * MM_TO_M;
          const u0 = (rowIndex * 0.317 + segment * 0.19) % 0.72;
          const uSpan = Math.min(0.98 - u0, Math.max(0.22, lengthM / 4.1));
          const v0 = (rowIndex % 4) * 0.25;
          const faceUV: Vector4[] = [];
          for (let face = 0; face < 6; face += 1) {
            faceUV.push(new Vector4(u0, v0, u0 + uSpan, v0 + 0.24));
          }
          const plank = CreateBox(
            `${zone.label} · doska ${rowIndex + 1}.${segment + 1}`,
            {
              width: lengthM,
              depth: (y1 - y) * MM_TO_M,
              height: thicknessM,
              faceUV,
              wrap: true,
            },
            this.scene,
          );
          plank.position.set(
            xM((segmentStartMm + segmentEndMm) / 2),
            topM - thicknessM / 2,
            zM((y + y1) / 2),
          );
          planks.push(plank);
        }
        rowIndex += 1;
      }
    }
    if (planks.length === 0) return;
    const merged = Mesh.MergeMeshes(planks, true, true, undefined, false, false);
    if (!merged) return;
    merged.name = zone.label;
    merged.material = material;
    merged.receiveShadows = true;
    merged.isPickable = false;
    this.realisticOnly(merged);
    this.castShadow(merged);
    this.register(merged, "street", zone.id);
  }

  private buildGardenPool() {
    const pool = GARDEN_POOL;
    const waterSurfaceM = -0.012;
    const sharedTerraceTopM =
      pool.terraceConnection.sharedTopElevationMm * MM_TO_M;
    const floorTopM = waterSurfaceM - pool.proposedWaterDepthMm * MM_TO_M;
    const wallThicknessMm = 120;

    const floor = boxAtPlan(
      this.scene,
      `${pool.label} · konštrukčné dno v hĺbke ${pool.proposedWaterDepthMm} mm`,
      pool.centerMm,
      pool.waterLengthMm,
      pool.waterWidthMm,
      0.12,
      floorTopM - 0.12,
    );
    this.appearance(
      floor,
      this.materials.poolWater,
      this.realisticMaterials.poolTile,
    );
    floor.receiveShadows = true;
    this.register(floor, "street", pool.id);

    const poolWalls = [
      {
        centerMm: {
          x: pool.centerMm.x,
          y: pool.centerMm.y - pool.waterWidthMm / 2 - wallThicknessMm / 2,
        },
        widthMm: pool.waterLengthMm + wallThicknessMm * 2,
        depthMm: wallThicknessMm,
      },
      {
        centerMm: {
          x: pool.centerMm.x,
          y: pool.centerMm.y + pool.waterWidthMm / 2 + wallThicknessMm / 2,
        },
        widthMm: pool.waterLengthMm + wallThicknessMm * 2,
        depthMm: wallThicknessMm,
      },
      {
        centerMm: {
          x: pool.centerMm.x - pool.waterLengthMm / 2 - wallThicknessMm / 2,
          y: pool.centerMm.y,
        },
        widthMm: wallThicknessMm,
        depthMm: pool.waterWidthMm,
      },
      {
        centerMm: {
          x: pool.centerMm.x + pool.waterLengthMm / 2 + wallThicknessMm / 2,
          y: pool.centerMm.y,
        },
        widthMm: wallThicknessMm,
        depthMm: pool.waterWidthMm,
      },
    ];
    for (const [index, wall] of poolWalls.entries()) {
      const mesh = boxAtPlan(
        this.scene,
        `${pool.label} · svetlá vnútorná stena ${index + 1}`,
        wall.centerMm,
        wall.widthMm,
        wall.depthMm,
        pool.proposedWaterDepthMm * MM_TO_M,
        floorTopM,
      );
      this.appearance(
        mesh,
        this.materials.poolWater,
        this.realisticMaterials.poolBasin,
      );
      mesh.receiveShadows = true;
      this.register(mesh, "street", pool.id);
    }

    // Invisible collider over the basin: the walker stops at the coping.
    const poolCollider = boxAtPlan(
      this.scene,
      `${pool.label} · kolízny blok vodnej plochy`,
      pool.centerMm,
      pool.waterLengthMm + 2 * wallThicknessMm,
      pool.waterWidthMm + 2 * wallThicknessMm,
      0.9,
      -0.4,
    );
    poolCollider.isVisible = false;
    poolCollider.isPickable = false;
    poolCollider.checkCollisions = true;

    const water = CreateGround(
      `${pool.label} · refrakčná vodná plocha presne ${pool.waterLengthMm.toLocaleString("sk-SK")} × ${pool.waterWidthMm.toLocaleString("sk-SK")} mm`,
      {
        width: pool.waterLengthMm * MM_TO_M,
        height: pool.waterWidthMm * MM_TO_M,
        subdivisions: 48,
      },
      this.scene,
    );
    water.position.set(xM(pool.centerMm.x), waterSurfaceM, zM(pool.centerMm.y));
    this.appearance(
      water,
      this.materials.poolWater,
      this.realisticMaterials.poolWater,
    );
    water.receiveShadows = false;
    this.register(water, "street", pool.id);

    const coping = pool.copingWidthMm;
    const outerLengthMm = pool.waterLengthMm + 2 * coping;
    const copingSegments: Array<{
      centerMm: Point2Mm;
      widthMm: number;
      depthMm: number;
    }> = [];
    const jointMm = 8;
    const terraceDrainGapMm = 26;
    const longSlabs = 9;
    const longSlabMm =
      (outerLengthMm - jointMm * (longSlabs - 1)) / longSlabs;
    for (const side of [-1, 1]) {
      for (let index = 0; index < longSlabs; index += 1) {
        const slabDepthMm =
          side === -1 ? coping - terraceDrainGapMm : coping;
        copingSegments.push({
          centerMm: {
            x:
              pool.centerMm.x -
              outerLengthMm / 2 +
              longSlabMm / 2 +
              index * (longSlabMm + jointMm),
            y:
              pool.centerMm.y +
              side * (pool.waterWidthMm / 2 + slabDepthMm / 2),
          },
          widthMm: longSlabMm,
          depthMm: slabDepthMm,
        });
      }
    }
    const shortSlabs = 5;
    const shortSlabMm =
      (pool.waterWidthMm - jointMm * (shortSlabs - 1)) / shortSlabs;
    for (const side of [-1, 1]) {
      for (let index = 0; index < shortSlabs; index += 1) {
        copingSegments.push({
          centerMm: {
            x: pool.centerMm.x + side * (pool.waterLengthMm / 2 + coping / 2),
            y:
              pool.centerMm.y -
              pool.waterWidthMm / 2 +
              shortSlabMm / 2 +
              index * (shortSlabMm + jointMm),
          },
          widthMm: coping,
          depthMm: shortSlabMm,
        });
      }
    }
    for (const [index, segment] of copingSegments.entries()) {
      const copingMesh = boxAtPlan(
        this.scene,
        `${pool.label} · porcelánová platňa lemu ${index + 1}`,
        segment.centerMm,
        segment.widthMm,
        segment.depthMm,
        0.055,
        sharedTerraceTopM - 0.055,
      );
      this.appearance(
        copingMesh,
        this.materials.paving,
        this.realisticMaterials.stone,
      );
      copingMesh.receiveShadows = true;
      this.castShadow(copingMesh);
      this.register(copingMesh, "street", pool.id);
    }

    const drainSlot = boxAtPlan(
      this.scene,
      `${pool.label} · tienistá lineárna odvodňovacia škára`,
      {
        x: pool.centerMm.x,
        y:
          pool.centerMm.y -
          pool.waterWidthMm / 2 -
          coping +
          terraceDrainGapMm / 2,
      },
      outerLengthMm - 140,
      18,
      0.008,
      sharedTerraceTopM - 0.008,
    );
    drainSlot.material = this.realisticMaterials.fenceTrack;
    drainSlot.isPickable = false;
    this.realisticOnly(drainSlot);
    this.register(drainSlot, "street", pool.id);

    const stepWidthMm = 275;
    for (const [index, dropM] of [0.24, 0.51, 0.78, 1.05].entries()) {
      const topM = waterSurfaceM - dropM;
      const stair = boxAtPlan(
        this.scene,
        `${pool.label} · plný ponorený stupeň ${index + 1}`,
        {
          x:
            pool.centerMm.x -
            pool.waterLengthMm / 2 +
            stepWidthMm / 2 +
            index * stepWidthMm,
          y: pool.centerMm.y,
        },
        stepWidthMm,
        1_250,
        topM - floorTopM,
        floorTopM,
      );
      this.appearance(
        stair,
        this.materials.paving,
        this.realisticMaterials.poolTile,
      );
      stair.receiveShadows = true;
      this.register(stair, "street", pool.id);
    }

    for (const [index, offsetMm] of [-1_150, 0, 1_150].entries()) {
      const light = CreateCylinder(
        `${pool.label} · diskrétne zapustené podvodné svetlo ${index + 1}`,
        { height: 0.022, diameter: 0.135, tessellation: 24 },
        this.scene,
      );
      light.position.set(
        xM(pool.centerMm.x + offsetMm),
        waterSurfaceM - 0.64,
        zM(pool.centerMm.y + pool.waterWidthMm / 2 - 8),
      );
      light.rotation.x = Math.PI / 2;
      light.material = this.realisticMaterials.poolLed;
      light.isPickable = false;
      this.realisticOnly(light);
      this.register(light, "street", pool.id);
    }

    const skimmer = boxAtPlan(
      this.scene,
      `${pool.label} · skimmer v krátkej stene`,
      {
        x: pool.centerMm.x + pool.waterLengthMm / 2 - 10,
        y: pool.centerMm.y,
      },
      28,
      320,
      0.16,
      waterSurfaceM - 0.28,
    );
    skimmer.material = this.realisticMaterials.glassFrame;
    skimmer.isPickable = false;
    this.realisticOnly(skimmer);
    this.register(skimmer, "street", pool.id);

    for (const [index, offsetMm] of [-520, 520].entries()) {
      const returnJet = CreateCylinder(
        `${pool.label} · vratná tryska ${index + 1}`,
        { height: 0.018, diameter: 0.075, tessellation: 24 },
        this.scene,
      );
      returnJet.position.set(
        xM(pool.centerMm.x - pool.waterLengthMm / 2 + 7),
        waterSurfaceM - 0.72,
        zM(pool.centerMm.y + offsetMm),
      );
      returnJet.rotation.z = Math.PI / 2;
      returnJet.material = this.realisticMaterials.fenceTrack;
      returnJet.isPickable = false;
      this.realisticOnly(returnJet);
      this.register(returnJet, "street", pool.id);
    }

    const floorDrain = CreateCylinder(
      `${pool.label} · kruhový dnový odtok`,
      { height: 0.018, diameter: 0.22, tessellation: 32 },
      this.scene,
    );
    floorDrain.position.set(
      xM(pool.centerMm.x + 520),
      floorTopM + 0.01,
      zM(pool.centerMm.y),
    );
    floorDrain.material = this.realisticMaterials.fenceTrack;
    floorDrain.isPickable = false;
    this.realisticOnly(floorDrain);
    this.register(floorDrain, "street", pool.id);

    const outline = CreateLines(
      `${pool.label} · koordinačný obrys lemu`,
      {
        points: pool.copingFootprintMm.map((point) =>
          point3(point, sharedTerraceTopM + 0.002),
        ),
      },
      this.scene,
    );
    outline.color = Color3.FromHexString("#5ed9f1");
    outline.alpha = 0.88;
    outline.isPickable = false;
    this.technicalOverlay(outline);
    this.register(outline, "street", pool.id);
  }

  private buildLandscape() {
    for (const zone of TERRACE_ZONES_D1) {
      this.buildDeckZone(zone);
    }
    this.buildGardenPool();

    // Gravel maintenance strip along the plastered facades.
    for (const strip of [
      { name: "Kačírek · južná fasáda", x0: 6440, x1: 21040, y0: 2550, y1: 3000 },
      { name: "Kačírek · východná fasáda", x0: 28040, x1: 28490, y0: 3000, y1: 22035 },
      { name: "Kačírek · severný štít", x0: 21040, x1: 28040, y0: 22035, y1: 22485 },
    ]) {
      const gravel = boxAtPlan(
        this.scene,
        strip.name,
        { x: (strip.x0 + strip.x1) / 2, y: (strip.y0 + strip.y1) / 2 },
        strip.x1 - strip.x0,
        strip.y1 - strip.y0,
        0.03,
        -0.075,
      );
      const gravelMaterial = this.realisticMaterials.gravel.clone(
        `${strip.name} · PBR`,
      ) as PBRMaterial;
      const baseGravel = this.realisticMaterials.gravel.albedoTexture as Texture | null;
      if (baseGravel) {
        const gravelAlbedo = baseGravel.clone() as Texture;
        gravelAlbedo.uScale = Math.max(1, ((strip.x1 - strip.x0) * MM_TO_M) / 0.9);
        gravelAlbedo.vScale = Math.max(0.5, ((strip.y1 - strip.y0) * MM_TO_M) / 0.9);
        gravelMaterial.albedoTexture = gravelAlbedo;
      }
      gravel.material = gravelMaterial;
      gravel.receiveShadows = true;
      gravel.isPickable = false;
      this.realisticOnly(gravel);
      this.register(gravel, "street");
    }

    for (const stone of [
      { x: 4100, y: 12250, w: 900, d: 520, r: -0.08 },
      { x: 4750, y: 13050, w: 840, d: 500, r: 0.12 },
      { x: 5450, y: 13820, w: 980, d: 540, r: -0.04 },
      { x: 6100, y: 14620, w: 900, d: 510, r: 0.1 },
    ]) {
      const step = boxAtPlan(
        this.scene,
        "Záhradný nášľap · ilustračný koncept",
        stone,
        stone.w,
        stone.d,
        0.06,
        GROUND_Y - 0.03,
      );
      step.rotation.y = stone.r;
      step.material = this.realisticMaterials.stone;
      step.receiveShadows = true;
      step.isPickable = false;
      this.realisticOnly(step);
      this.register(step, "street");
    }

    const plantingBeds = [
      [
        { x: 3600, y: 14200 },
        { x: 6900, y: 14650 },
        { x: 8350, y: 15100 },
        { x: 8350, y: 16400 },
        { x: 7600, y: 16900 },
        { x: 5400, y: 16000 },
        { x: 3600, y: 15000 },
        { x: 3600, y: 14200 },
      ],
      [
        { x: 7600, y: 17450 },
        { x: 11200, y: 17450 },
        { x: 14500, y: 17800 },
        { x: 17400, y: 19000 },
        { x: 17600, y: 20600 },
        { x: 15800, y: 19900 },
        { x: 13900, y: 19200 },
        { x: 11000, y: 18700 },
        { x: 8800, y: 18000 },
        { x: 7600, y: 17450 },
      ],
      [
        { x: 28700, y: 15100 },
        { x: 30500, y: 15800 },
        { x: 30600, y: 22500 },
        { x: 28800, y: 22900 },
        { x: 29000, y: 19600 },
        { x: 28700, y: 15100 },
      ],
    ] as const;
    for (const [index, ring] of plantingBeds.entries()) {
      const bed = createFlatPolygon(
        this.scene,
        `Mulčovaný trvalkový záhon ${index + 1} · ilustračný koncept`,
        ring,
        GROUND_Y + 0.006,
      );
      bed.material = this.realisticMaterials.mulch;
      bed.receiveShadows = true;
      bed.isPickable = false;
      this.realisticOnly(bed);
      this.register(bed, "street");
    }

    const shrubs = [
      { x: 5200, y: 15400, s: 1.2 },
      { x: 6900, y: 16000, s: 1.0 },
      { x: 7700, y: 16550, s: 1.18 },
      { x: 9200, y: 17750, s: 0.92 },
      { x: 11400, y: 18300, s: 1.18 },
      { x: 14500, y: 18900, s: 1.05 },
      { x: 16700, y: 18800, s: 1.3 },
      { x: 17100, y: 20300, s: 1.08 },
      { x: 29200, y: 18800, s: 1.25 },
      { x: 29800, y: 20500, s: 0.94 },
      { x: 4200, y: 7100, s: 1.1 },
    ] as const;
    for (const [index, shrub] of shrubs.entries()) {
      this.buildShrub(
        `Trvalkový záhon ${index + 1} · ilustračný koncept`,
        shrub.x,
        shrub.y,
        shrub.s,
        index,
      );
    }

    for (const [index, grass] of [
      { x: 4700, y: 15100, s: 1.05 },
      { x: 7600, y: 16800, s: 1.18 },
      { x: 10200, y: 18100, s: 0.94 },
      { x: 13600, y: 18700, s: 1.12 },
      { x: 16400, y: 20100, s: 1.2 },
      { x: 22300, y: 23300, s: 1.24 },
      { x: 27400, y: 23050, s: 1.02 },
      { x: 29100, y: 17100, s: 1.08 },
      { x: 29900, y: 22100, s: 1.16 },
    ].entries()) {
      this.buildGrassCluster(
        `Okrasná tráva ${index + 1} · ilustračný koncept`,
        grass.x,
        grass.y,
        grass.s,
      );
    }

    this.buildGardenFurniture();
  }

  private buildGrassCluster(
    name: string,
    xMm: number,
    yMm: number,
    scale: number,
  ) {
    this.buildPlantCard(
      name,
      xMm,
      yMm,
      1.22 * scale,
      1.28 * scale,
      this.realisticMaterials.plantGrass,
      (xMm + yMm) * 0.00037,
    );
  }

  private buildShrub(
    name: string,
    xMm: number,
    yMm: number,
    scale: number,
    variant: number,
  ) {
    this.buildPlantCard(
      name,
      xMm,
      yMm,
      1.52 * scale,
      1.06 * scale,
      this.realisticMaterials.plantPerennial,
      variant * 0.47,
    );
  }

  private buildPlantCard(
    name: string,
    xMm: number,
    yMm: number,
    widthM: number,
    heightM: number,
    material: PBRMaterial,
    rotation: number,
  ) {
    for (let card = 0; card < 3; card += 1) {
      const plane = CreatePlane(
        `${name} · krížená botanická karta ${card + 1}`,
        {
          width: widthM * (card === 2 ? 0.88 : 1),
          height: heightM * (card === 1 ? 0.94 : 1),
        },
        this.scene,
      );
      const angle = rotation + (card * Math.PI) / 3;
      const radialOffset = card === 0 ? 0 : 0.055;
      plane.position.set(
        xM(xMm) + Math.cos(angle) * radialOffset,
        heightM * 0.48 + (card === 2 ? 0.025 : 0) + GROUND_Y,
        zM(yMm) + Math.sin(angle) * radialOffset,
      );
      plane.rotation.y = angle;
      plane.material = material;
      plane.receiveShadows = true;
      plane.isPickable = false;
      this.realisticOnly(plane);
      this.castShadow(plane);
      this.register(plane, "street");
    }
  }

  private buildGardenFurniture() {
    // Two light garden chairs on the loggia deck (reference photograph).
    for (const [index, center] of [
      { x: 8300, y: 12150, r: -0.12 },
      { x: 9500, y: 12250, r: 0.16 },
    ].entries()) {
      const seat = boxAtPlan(
        this.scene,
        `Záhradné kreslo ${index + 1} · ilustračný koncept`,
        center,
        620,
        700,
        0.1,
        0.32,
      );
      seat.rotation.y = center.r;
      seat.material = this.realisticMaterials.fabric;
      seat.isPickable = false;
      this.realisticOnly(seat);
      this.castShadow(seat);
      this.register(seat, "street");
      const back = boxAtPlan(
        this.scene,
        `Operadlo záhradného kresla ${index + 1}`,
        { x: center.x, y: center.y + 300 },
        620,
        90,
        0.52,
        0.3,
      );
      back.rotation.y = center.r;
      back.rotation.x = -0.32;
      back.material = this.realisticMaterials.fabric;
      back.isPickable = false;
      this.realisticOnly(back);
      this.castShadow(back);
      this.register(back, "street");
      for (const legOffset of [
        { dx: -250, dy: -280 },
        { dx: 250, dy: -280 },
        { dx: -250, dy: 280 },
        { dx: 250, dy: 280 },
      ]) {
        const leg = boxAtPlan(
          this.scene,
          `Noha kresla ${index + 1}`,
          { x: center.x + legOffset.dx, y: center.y + legOffset.dy },
          40,
          40,
          0.3,
          0.02,
        );
        leg.material = this.realisticMaterials.glassFrame;
        leg.isPickable = false;
        this.realisticOnly(leg);
        this.register(leg, "street");
      }
    }

    // Graphite lounge set inside the covered porch (reference photograph).
    const sofaSeat = boxAtPlan(
      this.scene,
      "Lounge pohovka · sedák · ilustračný koncept",
      { x: 26550, y: 20500 },
      1800,
      850,
      0.24,
      0.2,
    );
    sofaSeat.material = this.realisticMaterials.upholsteryDark;
    sofaSeat.isPickable = false;
    this.realisticOnly(sofaSeat);
    this.castShadow(sofaSeat);
    this.register(sofaSeat, "street");
    const sofaBase = boxAtPlan(
      this.scene,
      "Lounge pohovka · podnož",
      { x: 26550, y: 20500 },
      1780,
      870,
      0.05,
      0.13,
    );
    sofaBase.material = this.realisticMaterials.fabric;
    sofaBase.isPickable = false;
    this.realisticOnly(sofaBase);
    this.register(sofaBase, "street");
    const sofaBack = boxAtPlan(
      this.scene,
      "Lounge pohovka · operadlo",
      { x: 26550, y: 20870 },
      1800,
      160,
      0.4,
      0.36,
    );
    sofaBack.material = this.realisticMaterials.upholsteryDark;
    sofaBack.isPickable = false;
    this.realisticOnly(sofaBack);
    this.castShadow(sofaBack);
    this.register(sofaBack, "street");

    const chaise = boxAtPlan(
      this.scene,
      "Lounge ležadlo · ilustračný koncept",
      { x: 22750, y: 20500 },
      750,
      1650,
      0.22,
      0.16,
    );
    chaise.rotation.y = 0.08;
    chaise.material = this.realisticMaterials.upholsteryDark;
    chaise.isPickable = false;
    this.realisticOnly(chaise);
    this.castShadow(chaise);
    this.register(chaise, "street");
    const chaiseBack = boxAtPlan(
      this.scene,
      "Lounge ležadlo · opierka",
      { x: 22750, y: 19980 },
      750,
      420,
      0.1,
      0.36,
    );
    chaiseBack.rotation.y = 0.08;
    chaiseBack.rotation.x = 0.62;
    chaiseBack.material = this.realisticMaterials.upholsteryDark;
    chaiseBack.isPickable = false;
    this.realisticOnly(chaiseBack);
    this.register(chaiseBack, "street");

    const loungeTable = boxAtPlan(
      this.scene,
      "Nízky stolík · doska · ilustračný koncept",
      { x: 24800, y: 20650 },
      900,
      520,
      0.05,
      0.3,
    );
    loungeTable.material = this.larchFor(0.9, 0.55, "table");
    loungeTable.isPickable = false;
    this.realisticOnly(loungeTable);
    this.castShadow(loungeTable);
    this.register(loungeTable, "street");
    const loungeTableBase = boxAtPlan(
      this.scene,
      "Nízky stolík · podnož",
      { x: 24800, y: 20650 },
      820,
      440,
      0.28,
      0.02,
    );
    loungeTableBase.material = this.realisticMaterials.fabric;
    loungeTableBase.isPickable = false;
    this.realisticOnly(loungeTableBase);
    this.register(loungeTableBase, "street");
  }

  private utilityMaterial(routeId: string, layer: LayerId) {
    if (layer !== "contextNetworks") return this.materials[layer];
    if (routeId.includes("WATER")) return this.materials.water;
    if (routeId.includes("SEWER")) return this.materials.sewer;
    if (routeId.includes("POWER")) return this.materials.electricity;
    return this.materials.contextNetworks;
  }

  private buildUtilities() {
    for (const route of UTILITY_ROUTES) {
      const path = route.pointsMm.map((point) => point3(point, 0.105));
      let mesh: AbstractMesh;
      if (
        route.status === "FUTURE_OPTION" ||
        route.revisionStatus === "REVISION_CONFLICT"
      ) {
        const dashed = CreateDashedLines(
          route.label,
          { points: path, dashSize: 0.22, gapSize: 0.16, dashNb: 22 },
          this.scene,
        );
        dashed.color = Color3.FromHexString(
          route.revisionStatus === "REVISION_CONFLICT" ? "#ec4ec6" : "#d49a58",
        );
        mesh = dashed;
      } else {
        const tube = CreateTube(
          route.label,
          {
            path,
            radius: route.radiusMm * MM_TO_M,
            tessellation: 8,
            cap: Mesh.CAP_ALL,
          },
          this.scene,
        );
        tube.material = this.utilityMaterial(route.id, route.layer);
        mesh = tube;
      }
      this.technicalOverlay(mesh);
      this.register(mesh, route.layer, route.id);
    }

    const meter = boxAtPlan(
      this.scene,
      "Vodomerná šachta · 1,20 × 0,90 × 1,50 m",
      { x: 13181, y: 937 },
      900,
      1200,
      0.28,
      0,
    );
    meter.material = this.materials.water;
    this.technicalOverlay(meter);
    this.register(meter, "water", "OBJ-WATER-METER");

    const rainTank = CreateCylinder(
      "Akumulačná nádrž dažďovej vody · 8,5 m³",
      { diameter: 2.55, height: 0.34, tessellation: 28 },
      this.scene,
    );
    // Moved south onto open lawn so the enlarged pool can sit flush in the
    // inner-L corner (client revision); modelled clearance 1 787 mm to the
    // pool coping shell.
    rainTank.position.set(xM(16_600), 0.12, zM(19_400));
    rainTank.material = this.materials.rainwater;
    this.technicalOverlay(rainTank);
    this.register(rainTank, "rainwater", "OBJ-RAIN-TANK");

    const infiltration = boxAtPlan(
      this.scene,
      "Podzemný vsakovací objekt · 6,1 m³",
      { x: 10481, y: 19878 },
      5000,
      3500,
      0.2,
      -0.02,
    );
    infiltration.material = this.materials.rainwater;
    this.technicalOverlay(infiltration);
    this.register(infiltration, "rainwater", "OBJ-INFILTRATION");

    const sewerTank = boxAtPlan(
      this.scene,
      "Dočasná žumpa · 11,0 m³",
      { x: 18294, y: 1483 },
      3160,
      2000,
      0.34,
      -0.05,
    );
    sewerTank.material = this.materials.sewer;
    this.technicalOverlay(sewerTank);
    this.register(sewerTank, "sewer", "OBJ-SEWER-TANK");
  }

  private updateFoundations(foundations: readonly FoundationStrip[]) {
    const incoming = new Set(foundations.map((item) => item.id));
    for (const [id, mesh] of this.foundationMeshes) {
      if (!incoming.has(id)) {
        mesh.dispose();
        this.foundationMeshes.delete(id);
        this.entityMeshes.delete(id);
      }
    }
    for (const item of foundations) {
      const { dx, dz } = sceneDeltaForPlanSegment(item.startMm, item.endMm);
      const length = Math.hypot(dx, dz);
      let mesh = this.foundationMeshes.get(item.id);
      if (!mesh) {
        mesh = CreateBox(item.label, { size: 1 }, this.scene);
        mesh.material = this.materials.foundation;
        mesh.enableEdgesRendering();
        mesh.edgesColor = Color4.FromHexString("#e8ece9db");
        mesh.edgesWidth = 0.82;
        this.foundationMeshes.set(item.id, mesh);
        this.technicalOverlay(mesh);
        this.register(mesh, "foundations", item.id);
      }
      mesh.scaling.set(length, item.heightMm * MM_TO_M, item.widthMm * MM_TO_M);
      mesh.position.set(
        xM((item.startMm.x + item.endMm.x) / 2),
        (item.baseElevationMm + item.heightMm / 2) * MM_TO_M,
        zM((item.startMm.y + item.endMm.y) / 2),
      );
      mesh.rotation.y = sceneYawForPlanSegment(item.startMm, item.endMm);
    }
  }

  update(snapshot: SceneSnapshot) {
    this.clearSelection();
    this.snapshot = snapshot;
    this.updateFoundations(snapshot.foundations);
    for (const [layer, meshes] of this.layerMeshes) {
      const visible =
        snapshot.visibleLayers[layer] ||
        (this.navigationMode === "walk" && layer === "building");
      for (const mesh of meshes) mesh.setEnabled(visible);
    }
    this.applyViewMode(snapshot.viewMode);
    if (snapshot.selectionId) {
      for (const mesh of this.entityMeshes.get(snapshot.selectionId) ?? []) {
        if (mesh.isEnabled() && mesh.visibility > 0.01) {
          this.selectedOriginals.set(mesh, {
            material: mesh.material,
            lineColor: mesh instanceof LinesMesh ? mesh.color.clone() : undefined,
          });
          if (mesh instanceof LinesMesh) {
            mesh.color = Color3.FromHexString("#ff5738");
          } else if (mesh instanceof Mesh) {
            // Preserve glass, water, foliage and every other PBR material.
            // Selection is a restrained outline, never an opaque replacement.
            this.selectionHighlight.addMesh(
              mesh,
              Color3.FromHexString("#ff765e"),
            );
          }
        }
      }
    }
  }

  private clearSelection() {
    this.selectionHighlight.removeAllMeshes();
    for (const [mesh, original] of this.selectedOriginals) {
      if (mesh.isDisposed()) continue;
      mesh.material = original.material;
      if (original.lineColor && mesh instanceof LinesMesh) {
        mesh.color = original.lineColor;
      }
    }
    this.selectedOriginals.clear();
  }

  private applyViewMode(mode: ViewMode) {
    const realistic = mode === "realistic";
    this.scene.clearColor = Color4.FromHexString(
      realistic ? "#c6cfd2ff" : "#101313ff",
    );
    this.scene.imageProcessingConfiguration.exposure = realistic ? 1.02 : 1;
    this.scene.imageProcessingConfiguration.contrast = realistic ? 1.08 : 1.04;
    this.scene.imageProcessingConfiguration.vignetteEnabled = realistic;
    this.scene.imageProcessingConfiguration.vignetteWeight = 0.32;
    // Photographic finish belongs to the reality view; the technical model
    // stays a clean, grain-free linework document.
    this.postPipeline.bloomEnabled = realistic;
    this.postPipeline.grainEnabled = realistic && !this.renderQuality.fxaaEnabled;
    this.postPipeline.grain.intensity = 9;
    this.postPipeline.grain.animated = true;
    this.scene.fogMode = realistic ? Scene.FOGMODE_EXP2 : Scene.FOGMODE_NONE;
    this.scene.fogDensity = 0.0026;
    this.scene.fogColor = Color3.FromHexString("#c2cccc");

    for (const [mesh, appearance] of this.appearances) {
      if (!mesh.isDisposed()) {
        mesh.material = realistic ? appearance.realistic : appearance.technical;
        if (mesh instanceof Mesh) {
          mesh.edgesColor = realistic
            ? Color4.FromHexString("#11171900")
            : Color4.FromHexString("#f5f2e95a");
        }
      }
    }
    for (const mesh of this.realisticOnlyMeshes) {
      if (!mesh.isDisposed()) mesh.visibility = realistic ? 1 : 0;
    }
    for (const mesh of this.technicalOverlayMeshes) {
      if (!mesh.isDisposed()) mesh.visibility = realistic ? 0 : 1;
    }

    this.materials.parcel.alpha = 0.16;
    this.materials.wall.alpha = 0.24;
    this.materials.roof.alpha = 0.34;
    this.scene.getMeshByName("Terén · DMR 5G kontext")?.setEnabled(realistic);
  }

  setCameraPreset(preset: CameraPreset) {
    if (this.garageCinematicActive) return;
    this.setNavigationMode("orbit");
    this.resetOrbitInertia();
    this.applyCameraPreset(preset);
    // A preset jumps the radius programmatically; drop any pending wheel
    // glide so it cannot fight the new framing.
    this.cancelOrbitZoomGlide();
  }

  private applyCameraPreset(preset: CameraPreset) {
    if (preset === "garden") {
      const garden = gardenCameraForWidth(this.canvas.clientWidth);
      this.orbitCamera.alpha = garden.alpha;
      this.orbitCamera.beta = garden.beta;
      this.orbitCamera.radius = garden.radius;
      this.orbitCamera.fov = garden.fov;
      this.orbitCamera.target.set(...garden.target);
      return;
    }
    if (preset === "top") {
      this.orbitCamera.alpha = TOP_CAMERA_ALPHA;
      this.orbitCamera.beta = 0.065;
      this.orbitCamera.radius = this.canvas.clientWidth < 600 ? 56 : 44;
      this.orbitCamera.fov = 0.72;
      this.orbitCamera.target.set(0, 0, 0.5);
      return;
    }
    if (preset === "parcels") {
      const parcels = parcelCameraForWidth(this.canvas.clientWidth);
      this.orbitCamera.alpha = parcels.alpha;
      this.orbitCamera.beta = parcels.beta;
      this.orbitCamera.radius = parcels.radius;
      this.orbitCamera.fov = parcels.fov;
      this.orbitCamera.target.set(...parcels.target);
      return;
    }
    if (preset === "street") {
      const street = streetCameraForWidth(this.canvas.clientWidth);
      this.orbitCamera.alpha = street.alpha;
      this.orbitCamera.beta = street.beta;
      this.orbitCamera.radius = street.radius;
      this.orbitCamera.fov = street.fov;
      this.orbitCamera.target.set(...street.target);
      return;
    }
    if (preset === "focus") {
      const meshes = this.snapshot?.selectionId
        ? this.entityMeshes.get(this.snapshot.selectionId)
        : undefined;
      const visibleMeshes = (meshes ?? []).filter(
        (mesh) =>
          mesh.isEnabled() &&
          mesh.isVisible &&
          mesh.visibility > 0.01 &&
          mesh.getTotalVertices() > 0,
      );
      if (visibleMeshes.length > 0) {
        const minimum = new Vector3(
          Number.POSITIVE_INFINITY,
          Number.POSITIVE_INFINITY,
          Number.POSITIVE_INFINITY,
        );
        const maximum = new Vector3(
          Number.NEGATIVE_INFINITY,
          Number.NEGATIVE_INFINITY,
          Number.NEGATIVE_INFINITY,
        );
        for (const mesh of visibleMeshes) {
          const bounds = mesh.getBoundingInfo().boundingBox;
          minimum.minimizeInPlace(bounds.minimumWorld);
          maximum.maximizeInPlace(bounds.maximumWorld);
        }
        const center = minimum.add(maximum).scale(0.5);
        const sphereRadius = maximum.subtract(minimum).scale(0.5).length();
        const verticalFov = 0.68;
        const aspect = Math.max(
          0.2,
          this.canvas.clientWidth / Math.max(1, this.canvas.clientHeight),
        );
        this.orbitCamera.target.copyFrom(center);
        this.orbitCamera.alpha = gardenCameraForWidth(
          this.canvas.clientWidth,
        ).alpha;
        this.orbitCamera.beta = 1.34;
        this.orbitCamera.fov = verticalFov;
        this.orbitCamera.radius = focusRadiusForBoundingSphere(
          sphereRadius,
          verticalFov,
          aspect,
        );
      }
      return;
    }
    this.orbitCamera.alpha = AXONOMETRIC_CAMERA_ALPHA;
    this.orbitCamera.beta = Math.PI * 0.34;
    this.orbitCamera.radius = this.canvas.clientWidth < 600 ? 58 : 42;
    this.orbitCamera.fov = 0.72;
    this.orbitCamera.target.set(0, 1.25, 0.5);
  }

  private resetOrbitInertia() {
    this.orbitCamera.inertialAlphaOffset = 0;
    this.orbitCamera.inertialBetaOffset = 0;
    this.orbitCamera.inertialRadiusOffset = 0;
    this.orbitCamera.inertialPanningX = 0;
    this.orbitCamera.inertialPanningY = 0;
  }

  setNavigationMode(mode: NavigationMode) {
    if (this.garageCinematicActive) return;
    if (mode === this.navigationMode) return;
    if (mode === "walk") {
      this.enterWalkthrough();
      return;
    }
    if (mode === "flight") {
      const fromWalk = this.navigationMode === "walk";
      if (fromWalk && this.scene.activeCamera === this.avatar.camera) {
        this.flightCamera.position.copyFrom(this.avatar.camera.position);
        this.flightCamera.rotationQuaternion = null;
        this.flightCamera.setTarget(this.avatar.camera.target.clone());
      }
      const orbitPosition = fromWalk
        ? this.flightCamera.position.clone()
        : this.orbitCamera.globalPosition.clone();
      if (!fromWalk) {
        this.orbitFocusDistance = Math.max(
          8,
          Math.min(32, Vector3.Distance(orbitPosition, this.orbitCamera.target)),
        );
      }
      const boundedEntry = integrateFlightPosition({
        position: orbitPosition,
        heading: { x: 0, z: -1 },
        commands: new Set(),
        deltaMs: 0,
      });
      this.leaveWalkCollisions();
      this.flightCamera.position.set(
        boundedEntry.x,
        boundedEntry.y,
        boundedEntry.z,
      );
      this.flightCamera.rotationQuaternion = null;
      if (!fromWalk) {
        this.flightCamera.fov = this.orbitCamera.fov;
        this.flightCamera.setTarget(this.orbitCamera.target);
      }
      const forward = this.flightCamera.getForwardRay(1).direction;
      const horizontalLength = Math.hypot(forward.x, forward.z);
      if (horizontalLength > 0.04) {
        this.flightHeading = {
          x: forward.x / horizontalLength,
          z: forward.z / horizontalLength,
        };
      }
      if (!fromWalk) this.orbitCamera.detachControl();
      if (this.scene.activeCamera !== this.flightCamera) {
        this.scene.activeCamera = this.flightCamera;
        this.flightCamera.attachControl(false);
      }
      this.navigationMode = "flight";
      this.canvas.focus({ preventScroll: true });
    } else {
      if (this.scene.activeCamera === this.avatar.camera) {
        // Leave the chase view from the chase camera's own pose.
        this.flightCamera.position.copyFrom(this.avatar.camera.position);
        this.flightCamera.rotationQuaternion = null;
        this.flightCamera.setTarget(this.avatar.camera.target.clone());
      }
      const forward = this.flightCamera.getForwardRay(1).direction.normalize();
      const target = this.flightCamera.position.add(
        forward.scale(this.orbitFocusDistance),
      );
      this.leaveWalkCollisions();
      this.flightCamera.detachControl();
      this.clearFlightInput();
      this.orbitCamera.target.copyFrom(target);
      this.orbitCamera.setPosition(this.flightCamera.position.clone());
      this.orbitCamera.fov = this.flightCamera.fov;
      this.resetOrbitInertia();
      this.cancelOrbitZoomGlide();
      this.scene.activeCamera = this.orbitCamera;
      this.orbitCamera.attachControl(
        this.canvas,
        !ORBIT_ZOOM.preventBrowserGesture,
      );
      this.navigationMode = "orbit";
    }
    this.onNavigationModeChange(this.navigationMode);
  }

  /**
   * Walkthrough: stand at eye level inside a room of the D1.1.002 plan. With
   * no room given the walker enters the main living space looking toward the
   * covered porch; the collider keeps the walker out of walls while open
   * doors and the glazed terrace doors stay passable.
   */
  enterWalkthrough(roomId?: string) {
    if (this.garageCinematicActive) return;
    const room =
      INTERIOR_ROOMS.find((candidate) => candidate.id === roomId) ??
      INTERIOR_ROOMS.find((candidate) => candidate.id === "ROOM-1-03") ??
      INTERIOR_ROOMS[0];
    const standing = room.standingPointMm;
    const look = walkLookTargetMm(room);
    if (this.navigationMode === "orbit") {
      this.orbitFocusDistance = 6;
      this.orbitCamera.detachControl();
    }
    this.clearFlightInput();
    const avatar = this.ensureAvatar();
    // Keyboard entry (G) can bypass the toolbar's React layer update. Make
    // the authoritative shell/collision geometry live before the first walk
    // frame; the parent callback synchronises the visible-layer UI next.
    for (const mesh of this.layerMeshes.get("building") ?? []) {
      mesh.setEnabled(true);
    }
    const yaw = Math.atan2(xM(look.x) - xM(standing.x), zM(look.y) - zM(standing.y));
    avatar.place(xM(standing.x), zM(standing.y), yaw);
    this.flightHeading = { x: Math.sin(yaw), z: Math.cos(yaw) };
    this.flightCamera.fov = 1.05;
    this.scene.collisionsEnabled = true;
    this.navigationMode = "walk";
    this.walkRoomId = room.id;
    this.applyWalkView();
    // Once the glTF arrives, hand over to the chase camera.
    void avatar.load().then(() => {
      this.canvas.dataset.walkAvatar = avatar.avatarId;
      if (this.navigationMode === "walk" && !this.garageCinematicActive) {
        this.applyWalkView();
      }
    }).catch(() => undefined);
    this.canvas.focus({ preventScroll: true });
    this.onNavigationModeChange(this.navigationMode);
  }

  /** Room the walker currently stands in, or null outside the house. */
  getWalkRoom(): InteriorRoom | null {
    if (this.navigationMode !== "walk") return null;
    const position = this.avatar.pose;
    return roomAt({
      x: Math.round(position.x * 1000 + SCENE_CENTER_MM.x),
      y: Math.round(SCENE_CENTER_MM.y - position.z * 1000),
    });
  }

  private walkRoomId: string | null = null;
  private readonly avatar: AvatarController;
  private walkView: "third" | "first" = "third";

  private leaveWalkCollisions() {
    this.flightCamera.checkCollisions = false;
    this.flightCamera.minZ = 0.18;
    this.avatar.camera.detachControl();
    this.avatar.deactivate();
  }

  private ensureAvatar() {
    if (!this.avatar.isLoaded) {
      void this.avatar.load().catch(() => {
        // Without the glTF the walkthrough silently stays first-person.
        this.walkView = "first";
        if (!this.garageCinematicActive) this.applyWalkView();
      });
    }
    return this.avatar;
  }

  /** Switches between the chase camera and the walker's own eyes. */
  setWalkView(view: "third" | "first") {
    if (this.garageCinematicActive) return;
    this.walkView = view;
    if (this.navigationMode === "walk") this.applyWalkView();
  }

  getWalkView() {
    return this.walkView;
  }

  private applyWalkView() {
    if (this.garageCinematicActive) return;
    const avatar = this.ensureAvatar();
    const third = this.walkView === "third" && avatar.isLoaded;
    if (third) {
      this.flightCamera.detachControl();
      this.flightCamera.checkCollisions = false;
      this.flightCamera.minZ = 0.18;
      avatar.setFirstPerson(false);
      this.scene.activeCamera = avatar.camera;
      avatar.camera.attachControl(this.canvas, true);
    } else {
      avatar.camera.detachControl();
      avatar.setFirstPerson(true);
      const eye = avatar.eyePosition;
      const { yaw } = avatar.pose;
      this.flightCamera.position.copyFrom(eye);
      this.flightCamera.rotationQuaternion = null;
      this.flightCamera.setTarget(eye.add(new Vector3(Math.sin(yaw), -0.04, Math.cos(yaw))));
      this.flightCamera.checkCollisions = false;
      this.flightCamera.minZ = 0.04;
      if (this.scene.activeCamera !== this.flightCamera) {
        this.scene.activeCamera = this.flightCamera;
        this.flightCamera.attachControl(false);
      }
    }
  }

  setFlightCommand(command: FlightCommand, active: boolean) {
    if (this.garageCinematicActive) {
      this.manualFlightCommands.delete(command);
      return;
    }
    if (active) this.manualFlightCommands.add(command);
    else this.manualFlightCommands.delete(command);
  }

  nudgeFlight(command: FlightCommand) {
    if (this.garageCinematicActive) return;
    if (this.navigationMode === "walk") {
      // A tap is a short step: hold the command for a few frames.
      this.manualFlightCommands.add(command);
      window.setTimeout(() => this.manualFlightCommands.delete(command), 220);
      return;
    }
    if (this.navigationMode !== "flight") return;
    const next = integrateFlightPosition({
      position: this.flightCamera.position,
      heading: this.flightHeading,
      commands: new Set([command]),
      deltaMs: 220,
    });
    this.flightCamera.position.set(next.x, next.y, next.z);
  }

  getDoorInteraction(): DoorInteractionSnapshot | null {
    if (this.navigationMode !== "walk") return null;
    const interaction = this.doors.getInteraction();
    if (interaction && !this.doorInteractionHasLineOfSight(interaction)) {
      return null;
    }
    if (
      interaction &&
      this.garageVehicleAction &&
      interaction.id === GARAGE_VEHICLE.garageDoorId
    ) {
      return { ...interaction, action: null };
    }
    return interaction;
  }

  /** A nearby leaf behind an unrelated wall must never steal the E prompt. */
  private doorInteractionHasLineOfSight(
    interaction: DoorInteractionSnapshot,
  ) {
    const pose = this.avatar.pose;
    const origin = new Vector3(pose.x, 1.22, pose.z);
    const target = new Vector3(
      interaction.interactionPoint.x,
      1.22,
      interaction.interactionPoint.z,
    );
    const direction = target.subtract(origin);
    const distance = direction.length();
    if (distance < 0.02) return true;
    direction.scaleInPlace(1 / distance);
    const pick = this.scene.pickWithRay(
      new Ray(origin, direction, distance + 0.08),
      (mesh) =>
        mesh.isEnabled() &&
        mesh.isVisible &&
        mesh.visibility > 0.02 &&
        mesh.isPickable,
    );
    if (!pick?.hit || !pick.pickedMesh) return true;
    const metadata = pick.pickedMesh.metadata as {
      readonly doorId?: string;
      readonly entityId?: string;
    } | null;
    return (
      metadata?.doorId === interaction.id ||
      metadata?.entityId === interaction.id
    );
  }

  /** Shared action for E, a nearby leaf tap and the accessible touch button. */
  toggleDoorInteraction(restoreCanvasFocus = true) {
    if (this.navigationMode !== "walk" || this.garageCinematicActive) {
      return false;
    }
    const interaction = this.getDoorInteraction();
    if (!interaction?.action) return false;
    if (
      this.garageVehicleAction &&
      interaction.id === GARAGE_VEHICLE.garageDoorId
    ) {
      return false;
    }
    const changed = this.doors.toggle(interaction.id);
    if (changed && interaction.action === "OPEN") {
      this.avatar.clearBlockedIndicator();
    }
    if (restoreCanvasFocus) this.canvas.focus({ preventScroll: true });
    return changed;
  }

  setDoorOpen(id: string, open: boolean, immediate = false) {
    const changed = this.doors.setOpen(id, open, immediate);
    if (changed && immediate) this.avatar.invalidateDynamicCameraOccluders();
    return changed;
  }

  getDoorDebugState() {
    return this.doors.debugState();
  }

  getGarageParkingState(): GarageParkingState {
    return this.garageParkingState;
  }

  requestGarageVehicleAction(action: GarageVehicleAction) {
    if (
      this.navigationMode !== "walk" ||
      this.getWalkRoom()?.id !== GARAGE_VEHICLE.roomId ||
      this.garageVehicleAction ||
      garageActionForState(this.garageParkingState) !== action
    ) {
      return false;
    }

    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reducedMotion) {
      this.ensureGarageCinematicAvatarClearance();
      const totalMs =
        action === "park"
          ? GARAGE_SEQUENCE.park.totalMs
          : GARAGE_SEQUENCE.unpark.totalMs;
      // Reduced motion resolves atomically to the safe closed-door state.
      if (!this.doors.setOpen(GARAGE_VEHICLE.garageDoorId, false, true)) {
        return false;
      }
      this.applyGarageAnimationFrame(
        garageAnimationFrame(action, totalMs),
      );
      this.garageVehicleAction = null;
      this.canvas.dataset.garageReducedMotion = "true";
      return true;
    }

    if (!this.beginGarageCinematic()) return false;
    this.garageVehicleAction = action;
    this.garageVehicleElapsedMs = 0;
    this.garageVehicleLastPose = null;
    this.canvas.dataset.garageReducedMotion = "false";
    this.applyGarageAnimationFrame(garageAnimationFrame(action, 0));
    return true;
  }

  getGarageParkingDebugState() {
    const door = this.doors
      .debugState()
      .find(({ id }) => id === GARAGE_VEHICLE.garageDoorId);
    return {
      state: this.garageParkingState,
      action: this.garageVehicleAction,
      elapsedMs: this.garageVehicleElapsedMs,
      vehicleVisible: this.garageVehicleRoot?.isEnabled() ?? false,
      vehiclePose: this.garageVehicleLastPose,
      wheelAngle: this.garageVehicleWheelAngle,
      steeringAngle: this.garageVehicleSteeringAngle,
      commandedDoorProgress: this.garageDoorProgress,
      actualDoorProgress: door?.progress ?? 0,
      actualDoorPhase: door?.phase ?? "CLOSED",
      cinematicActive: this.garageCinematicActive,
      cameraView: this.canvas.dataset.garageCameraView ?? "garage",
      activeCameraName: this.scene.activeCamera?.name ?? null,
      returnCameraName: this.garageCinematicReturnCamera?.name ?? null,
      navigationMode: this.navigationMode,
      avatarPose: this.avatar.pose,
    } as const;
  }

  isGarageCinematicActive() {
    return this.garageCinematicActive;
  }

  getNavigationMode() {
    return this.navigationMode;
  }

  /** Changes only the walker's visual rig; pose, camera and collider persist. */
  async setWalkAvatar(id: WalkAvatarId) {
    this.canvas.dataset.walkAvatar = id;
    try {
      await this.avatar.setAvatar(id, this.navigationMode === "walk");
      if (this.navigationMode === "walk" && !this.garageCinematicActive) {
        this.applyWalkView();
      }
    } catch (error) {
      this.canvas.dataset.walkAvatar =
        this.avatar.activeAvatarId ?? this.avatar.avatarId;
      throw error;
    }
  }

  getWalkAvatar() {
    return this.avatar.avatarId;
  }

  recoverWalkthrough() {
    if (this.navigationMode !== "walk" || this.garageCinematicActive) return;
    this.clearFlightInput();
    this.avatar.recover();
    this.applyWalkView();
    this.canvas.focus({ preventScroll: true });
  }

  isWalkBlocked() {
    return this.navigationMode === "walk" && this.avatar.isBlocked;
  }

  getWalkDebugState() {
    return {
      mode: this.navigationMode,
      view: this.walkView,
      roomId: this.getWalkRoom()?.id ?? null,
      avatarId: this.avatar.avatarId,
      activeAvatarId: this.avatar.activeAvatarId,
      pose: this.avatar.pose,
      camera: this.avatar.cameraState,
      blocked: this.avatar.isBlocked,
    } as const;
  }

  getRenderQuality() {
    return this.renderQuality;
  }

  whenReady() {
    return this.scene.whenReadyAsync();
  }

  resize() {
    if (this.resizeFrame) return;
    this.resizeFrame = window.requestAnimationFrame(() => {
      this.resizeFrame = 0;
      let next = this.deriveCurrentRenderQuality();
      if (!this.ssaoPipeline && next.ssaoEnabled) {
        next = { ...next, ssaoEnabled: false, ssaoRatio: 0 };
      }
      const previous = this.renderQuality;
      const scalingChanged =
        previous.hardwareScalingLevel !== next.hardwareScalingLevel;
      if (scalingChanged) {
        // Babylon resizes internally when the hardware scaling level changes.
        this.engine.setHardwareScalingLevel(next.hardwareScalingLevel);
      }
      if (previous.msaaSamples !== next.msaaSamples) {
        this.postPipeline.samples = next.msaaSamples;
      }
      if (previous.fxaaEnabled !== next.fxaaEnabled) {
        this.postPipeline.fxaaEnabled = next.fxaaEnabled;
      }
      if (previous.sharpenEdgeAmount !== next.sharpenEdgeAmount) {
        this.postPipeline.sharpen.edgeAmount = next.sharpenEdgeAmount;
      }
      if (previous.shadowMapSize !== next.shadowMapSize) {
        this.shadowGenerator.mapSize = next.shadowMapSize;
      }
      if (previous.tier !== next.tier) {
        this.shadowGenerator.filteringQuality =
          next.tier === "ULTRA"
            ? ShadowGenerator.QUALITY_HIGH
            : ShadowGenerator.QUALITY_MEDIUM;
      }
      if (this.ssaoPipeline) {
        if (previous.tier !== next.tier) {
          this.ssaoPipeline.samples = next.tier === "ULTRA" ? 16 : 12;
        }
        const cameras = [
          this.orbitCamera,
          this.flightCamera,
          this.garageCinematicCamera,
          this.avatar.camera,
        ];
        if (next.ssaoEnabled && !this.ssaoAttached) {
          this.scene.postProcessRenderPipelineManager.attachCamerasToRenderPipeline(
            this.ssaoPipeline.name,
            cameras,
            true,
          );
          this.ssaoAttached = true;
        } else if (!next.ssaoEnabled && this.ssaoAttached) {
          this.scene.postProcessRenderPipelineManager.detachCamerasFromRenderPipeline(
            this.ssaoPipeline.name,
            cameras,
          );
          this.ssaoAttached = false;
        }
      }
      if (!scalingChanged) this.engine.resize();
      if (this.garageCinematicActive && this.garageVehicleLastPose) {
        this.configureGarageCinematicCamera(this.garageVehicleLastPose);
      }
      this.renderQuality = next;
      this.onRenderQualityChange(next);
    });
  }

  dispose() {
    if (this.resizeFrame) window.cancelAnimationFrame(this.resizeFrame);
    document.removeEventListener("visibilitychange", this.onVisibilityChange);
    this.canvas.removeEventListener("keydown", this.handleFlightKeyDown);
    this.canvas.removeEventListener("keyup", this.handleFlightKeyUp);
    this.canvas.removeEventListener("blur", this.clearFlightInput);
    this.canvas.removeEventListener("pointercancel", this.cancelPointerGesture);
    this.canvas.removeEventListener("wheel", this.handleCanvasWheel);
    this.clearFlightInput();
    this.endGarageCinematic(false);
    this.clearSelection();
    this.avatar.dispose();
    this.scene.dispose();
    this.engine.dispose();
  }
}

export function createTwinScene(
  canvas: HTMLCanvasElement,
  onSelect: (id: string) => void,
  onNavigationModeChange: (mode: NavigationMode) => void,
  onRenderQualityChange: (profile: RenderQualityProfile) => void,
) {
  return new TwinSceneController(
    canvas,
    onSelect,
    onNavigationModeChange,
    onRenderQualityChange,
  );
}
