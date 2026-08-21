import { ArcRotateCamera } from "@babylonjs/core/Cameras/arcRotateCamera";
import type { FreeCameraMouseInput } from "@babylonjs/core/Cameras/Inputs/freeCameraMouseInput";
import { UniversalCamera } from "@babylonjs/core/Cameras/universalCamera";
import { Engine } from "@babylonjs/core/Engines/engine";
import { PhotoDome } from "@babylonjs/core/Helpers/photoDome";
import { DirectionalLight } from "@babylonjs/core/Lights/directionalLight";
import { HemisphericLight } from "@babylonjs/core/Lights/hemisphericLight";
import { ShadowGenerator } from "@babylonjs/core/Lights/Shadows/shadowGenerator";
import { ImageProcessingConfiguration } from "@babylonjs/core/Materials/imageProcessingConfiguration";
import type { Material } from "@babylonjs/core/Materials/material";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { StandardMaterial } from "@babylonjs/core/Materials/standardMaterial";
import { EquiRectangularCubeTexture } from "@babylonjs/core/Materials/Textures/equiRectangularCubeTexture";
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
import "@babylonjs/core/Meshes/thinInstanceMesh";
import { DefaultRenderingPipeline } from "@babylonjs/core/PostProcesses/RenderPipeline/Pipelines/defaultRenderingPipeline";
import { SSAO2RenderingPipeline } from "@babylonjs/core/PostProcesses/RenderPipeline/Pipelines/ssao2RenderingPipeline";
import "@babylonjs/core/Rendering/prePassRendererSceneComponent";
import "@babylonjs/core/Rendering/depthRendererSceneComponent";
import "@babylonjs/core/Rendering/geometryBufferRendererSceneComponent";
import "@babylonjs/core/Rendering/edgesRenderer";
import "@babylonjs/core/Culling/ray";
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
  STREET_CAMERA_ALPHA,
  TOP_CAMERA_ALPHA,
  gardenCameraForWidth,
  sceneDeltaForPlanSegment,
  sceneXM as xM,
  sceneYawForPlanSegment,
  sceneZM as zM,
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
import {
  deriveRenderQualityProfile,
  flightCommandForCode,
  integrateFlightPosition,
  isSelectionTap,
  type FlightCommand,
  type NavigationMode,
  type RenderQualityProfile,
} from "./twin-viewport-contract";

export type CameraPreset = "garden" | "axonometric" | "top" | "street" | "focus";

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
  material.backFaceCulling = false;
  material.environmentIntensity = 1;
  if (alpha < 1) {
    material.transparencyMode = PBRMaterial.PBRMATERIAL_ALPHABLEND;
    material.useAlphaFromAlbedoTexture = false;
  }
  return material;
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
  const normals = openRing.flatMap(() => [0, 1, 0]);
  const data = new VertexData();
  data.positions = positions;
  data.indices = indices;
  data.normals = normals;
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

export class TwinSceneController {
  private readonly engine: Engine;
  private readonly scene: Scene;
  private readonly orbitCamera: ArcRotateCamera;
  private readonly flightCamera: UniversalCamera;
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
  private readonly shadowGenerator: ShadowGenerator;
  private readonly postPipeline: DefaultRenderingPipeline;
  private readonly ssaoPipeline: SSAO2RenderingPipeline | null;
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
  private resizeFrame = 0;
  private snapshot: SceneSnapshot | null = null;

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
      stencil: false,
      adaptToDeviceRatio: false,
      powerPreference: "high-performance",
    });
    this.renderQuality = this.deriveCurrentRenderQuality();
    this.engine.setHardwareScalingLevel(
      this.renderQuality.hardwareScalingLevel,
    );
    this.scene = new Scene(this.engine);
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
    sky.rotation.y = Math.PI * 0.18;
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
    this.orbitCamera.lowerRadiusLimit = 6;
    this.orbitCamera.upperRadiusLimit = 86;
    this.orbitCamera.lowerBetaLimit = 0.06;
    this.orbitCamera.upperBetaLimit = Math.PI / 2.02;
    this.orbitCamera.wheelPrecision = 38;
    this.orbitCamera.panningSensibility = 95;
    this.orbitCamera.pinchPrecision = 72;
    this.orbitCamera.inertia = 0.72;
    this.orbitCamera.minZ = 0.18;
    this.orbitCamera.maxZ = 220;
    this.orbitCamera.fov = gardenCamera.fov;
    this.orbitCamera.attachControl(canvas, true);

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
    this.scene.activeCamera = this.orbitCamera;

    const ambient = new HemisphericLight(
      "ambient-light",
      new Vector3(0.25, 1, -0.12),
      this.scene,
    );
    ambient.intensity = 0.22;
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
    sun.intensity = 1.4;
    sun.diffuse = Color3.FromHexString("#fff6e6");
    sun.specular = Color3.FromHexString("#fff9ef");
    this.shadowGenerator = new ShadowGenerator(
      this.renderQuality.shadowMapSize,
      sun,
    );
    this.shadowGenerator.usePercentageCloserFiltering = true;
    this.shadowGenerator.filteringQuality =
      this.renderQuality.tier === "ULTRA"
      ? ShadowGenerator.QUALITY_HIGH
      : ShadowGenerator.QUALITY_MEDIUM;
    this.shadowGenerator.bias = 0.00055;
    this.shadowGenerator.normalBias = 0.007;
    this.shadowGenerator.setDarkness(0.25);

    this.postPipeline = new DefaultRenderingPipeline(
      "architectural-photo-pipeline",
      true,
      this.scene,
      [this.orbitCamera, this.flightCamera],
    );
    this.postPipeline.samples = this.renderQuality.msaaSamples;
    this.postPipeline.fxaaEnabled = this.renderQuality.fxaaEnabled;
    this.postPipeline.bloomEnabled = false;
    this.postPipeline.imageProcessingEnabled = true;
    this.postPipeline.sharpenEnabled = true;
    this.postPipeline.sharpen.edgeAmount =
      this.renderQuality.sharpenEdgeAmount;
    this.postPipeline.sharpen.colorAmount = 1;
    const renderCameras = [this.orbitCamera, this.flightCamera];
    let ssaoPipeline: SSAO2RenderingPipeline | null = null;
    if (this.renderQuality.ssaoEnabled && SSAO2RenderingPipeline.IsSupported) {
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
        ssaoPipeline.radius = 0.82;
        ssaoPipeline.totalStrength = 0.82;
        ssaoPipeline.samples = 16;
        ssaoPipeline.expensiveBlur = true;
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
      road: pbrMaterial(this.scene, "real-road", "#7c8283", 0.94),
      paving: pbrMaterial(this.scene, "real-paving", "#c9cbc6", 0.88),
      gravel: pbrMaterial(this.scene, "real-gravel", "#ffffff", 0.96),
      timber: pbrMaterial(this.scene, "real-timber", "#ffffff", 0.68),
      timberDark: pbrMaterial(this.scene, "real-timber-dark", "#8a5c30", 0.74),
      deck: pbrMaterial(this.scene, "real-deck", "#ffffff", 0.74),
      wall: pbrMaterial(this.scene, "real-wall", "#ffffff", 0.92),
      soffit: pbrMaterial(this.scene, "real-soffit", "#f4f2ec", 0.9),
      concrete: pbrMaterial(this.scene, "real-concrete", "#ffffff", 0.86),
      roof: pbrMaterial(this.scene, "real-roof", "#ffffff", 0.72, 0),
      roofEdge: pbrMaterial(this.scene, "real-roof-edge", "#282d31", 0.6, 0),
      glass: pbrMaterial(this.scene, "real-glass", "#36494d", 0.07, 0, 0.3),
      glassFrame: pbrMaterial(this.scene, "real-glass-frame", "#26292b", 0.34, 0.55),
      glassFrameWood: pbrMaterial(this.scene, "real-glass-frame-wood", "#77522c", 0.5),
      solar: pbrMaterial(this.scene, "real-solar", "#0b1824", 0.12, 0.45),
      solarGrid: pbrMaterial(this.scene, "real-solar-grid", "#aeb6ba", 0.3, 0.8),
      chimney: pbrMaterial(this.scene, "real-chimney", "#787f7f", 0.32, 0.75),
      fenceMetal: pbrMaterial(this.scene, "real-fence-metal", "#252a2c", 0.66, 0.05),
      fenceTrack: pbrMaterial(this.scene, "real-fence-track", "#8d9496", 0.32, 0.72),
      hedgeDark: pbrMaterial(this.scene, "real-hedge-dark", "#244a2b", 0.94),
      hedgeMid: pbrMaterial(this.scene, "real-hedge-mid", "#356438", 0.92),
      hedgeLight: pbrMaterial(this.scene, "real-hedge-light", "#477746", 0.9),
      poolWater: pbrMaterial(this.scene, "real-pool-water", "#2da7c8", 0.06, 0, 0.76),
      poolBasin: pbrMaterial(this.scene, "real-pool-basin", "#123f4c", 0.62),
      poolLed: pbrMaterial(this.scene, "real-pool-led", "#d7fbff", 0.12),
      mulch: pbrMaterial(this.scene, "real-mulch", "#2e2317", 1),
      stone: pbrMaterial(this.scene, "real-stone", "#d6d2c6", 0.9),
      fabric: pbrMaterial(this.scene, "real-fabric", "#e6e2d8", 0.95),
      upholsteryDark: pbrMaterial(this.scene, "real-upholstery-dark", "#22292a", 0.94),
      curtain: pbrMaterial(this.scene, "real-curtain", "#e2e0d8", 0.96, 0, 0.6),
      interiorDark: pbrMaterial(this.scene, "real-interior-dark", "#1a2325", 0.75),
      warmInterior: pbrMaterial(this.scene, "real-interior", "#d5a76a", 0.82),
      plantGrass: pbrMaterial(this.scene, "real-plant-grass", "#ffffff", 0.9),
      plantPerennial: pbrMaterial(this.scene, "real-plant-perennial", "#ffffff", 0.9),
    };
    this.realisticMaterials.glass.indexOfRefraction = 1.5;
    this.realisticMaterials.glass.metallicF0Factor = 0.06;
    this.realisticMaterials.glass.environmentIntensity = 1.15;
    this.realisticMaterials.glass.useSpecularOverAlpha = true;
    this.realisticMaterials.glass.backFaceCulling = true;
    this.realisticMaterials.glass.needDepthPrePass = true;
    this.realisticMaterials.warmInterior.emissiveColor =
      Color3.FromHexString("#4b3418");
    this.realisticMaterials.poolWater.indexOfRefraction = 1.333;
    this.realisticMaterials.poolWater.environmentIntensity = 1.35;
    this.realisticMaterials.poolWater.useSpecularOverAlpha = true;
    this.realisticMaterials.poolWater.needDepthPrePass = true;
    this.realisticMaterials.poolWater.emissiveColor =
      Color3.FromHexString("#062f38");
    this.realisticMaterials.poolLed.emissiveColor =
      Color3.FromHexString("#b7f5ff");

    this.applyTexture(this.realisticMaterials.grass, "lawn-albedo", 12, 10, "lawn-normal", 0.4);
    this.applyTexture(
      this.realisticMaterials.terrain,
      "lawn-albedo",
      46,
      40,
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
    this.applyTexture(this.realisticMaterials.gravel, "gravel-albedo", 6, 1.1, "gravel-normal", 0.9);
    this.applyTexture(this.realisticMaterials.concrete, "concrete-albedo", 2.2, 2.2, "concrete-normal", 0.5);
    this.applyTexture(this.realisticMaterials.paving, "concrete-albedo", 5, 2.5, "concrete-normal", 0.45);
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
    this.buildFence();
    this.buildLandscape();
    this.buildUtilities();

    this.scene.onPointerDown = (event) => {
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
      const gesture = this.pointerGesture;
      if (!gesture || gesture.pointerId !== event.pointerId) return;
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
        isSelectionTap({
          travelPx: gesture.travelPx,
          durationMs: performance.now() - gesture.startedAt,
          maximumPointers: gesture.maximumPointers,
          button: gesture.button,
        })
      ) {
        const id = pick?.pickedMesh?.metadata?.entityId;
        if (typeof id === "string") this.onSelect(id);
      }
      this.pointerGesture = null;
    };

    this.canvas.addEventListener("keydown", this.handleFlightKeyDown);
    this.canvas.addEventListener("keyup", this.handleFlightKeyUp);
    this.canvas.addEventListener("blur", this.clearFlightInput);
    this.canvas.addEventListener("pointercancel", this.cancelPointerGesture);
    this.scene.onBeforeRenderObservable.add(() => this.updateFlightMotion());

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

  private readonly handleFlightKeyDown = (event: KeyboardEvent) => {
    if (this.navigationMode !== "flight" || event.metaKey || event.ctrlKey) return;
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

  private updateFlightMotion() {
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
    material.opacityTexture = texture;
    material.useAlphaFromAlbedoTexture = true;
    material.transparencyMode = PBRMaterial.PBRMATERIAL_ALPHATESTANDBLEND;
    material.alphaCutOff = 0.22;
    material.backFaceCulling = false;
    material.unlit = true;
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
    entityId: string,
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
      { diameter: 1, segments: 7 },
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
      { width: 140, height: 118 },
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
    for (let coordinate = -30; coordinate <= 45; coordinate += 1) {
      const color = coordinate % 5 === 0 ? major : minor;
      const alpha = coordinate % 5 === 0 ? 0.42 : 0.14;
      const xLine = CreateLines(
        `grid-x-${coordinate}`,
        {
          points: [
            new Vector3(coordinate - CENTER_X_M, -0.112, -30),
            new Vector3(coordinate - CENTER_X_M, -0.112, 31),
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
            new Vector3(-39, -0.111, zM(coordinate * 1000)),
            new Vector3(39, -0.111, zM(coordinate * 1000)),
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
      if (parcel.isSubject) {
        const fill = createFlatPolygon(
          this.scene,
          "Parcela 6012/26 · 753 m²",
          localRing,
          -0.075,
        );
        this.appearance(
          fill,
          this.materials.parcel,
          this.realisticMaterials.grass,
        );
        fill.receiveShadows = true;
        this.register(fill, "cadastre");
      }
      const outline = CreateLines(
        `Katastrálna hranica ${parcel.nationalReference}`,
        { points: localRing.map((point) => point3(point, -0.018)) },
        this.scene,
      );
      outline.color = Color3.FromHexString(
        parcel.isSubject ? "#ff5738" : "#715443",
      );
      outline.alpha = parcel.isSubject ? 1 : 0.46;
      outline.isPickable = parcel.isSubject;
      this.technicalOverlay(outline);
      this.register(outline, "cadastre", parcel.isSubject ? parcel.id : undefined);
    }
  }

  private buildStreetAndSite() {
    const frontage = createFlatPolygon(
      this.scene,
      "Miestna komunikácia 6012/1 · čelná vetva",
      ROAD_CONTEXT.frontagePolygonMm,
      -0.115,
    );
    this.appearance(frontage, this.materials.road, this.realisticMaterials.road);
    frontage.receiveShadows = true;
    this.register(frontage, "street", ROAD_CONTEXT.id);

    const corner = createFlatPolygon(
      this.scene,
      "Miestna komunikácia 6012/1 · koncový roh",
      ROAD_CONTEXT.cornerPolygonMm,
      -0.114,
    );
    this.appearance(corner, this.materials.road, this.realisticMaterials.road);
    corner.receiveShadows = true;
    this.register(corner, "street", ROAD_CONTEXT.id);

    for (const curbSpec of [
      {
        name: "Obrubník čelnej hrany parcely",
        centerMm: { x: 10097, y: -180 },
        widthMm: 36194,
      },
      {
        name: "Vonkajší okraj čelnej komunikácie",
        centerMm: { x: 17000, y: -7580 },
        widthMm: 50000,
      },
    ]) {
      const curb = boxAtPlan(
        this.scene,
        curbSpec.name,
        curbSpec.centerMm,
        curbSpec.widthMm,
        120,
        0.14,
        -0.04,
      );
      this.appearance(curb, this.materials.paving, this.realisticMaterials.concrete);
      curb.receiveShadows = true;
      curb.isPickable = false;
      this.register(curb, "street");
    }

    const cornerCurb = CreateLines(
      "Obrubník koncového rohu 6012/1",
      {
        points: ROAD_CONTEXT.cornerPolygonMm
          .slice(0, 7)
          .map((point) => point3(point, -0.039)),
      },
      this.scene,
    );
    cornerCurb.color = Color3.FromHexString("#aab3b4");
    cornerCurb.alpha = 0.82;
    cornerCurb.isPickable = false;
    this.technicalOverlay(cornerCurb);
    this.register(cornerCurb, "street");

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
      const paving = createFlatPolygon(
        this.scene,
        `Navrhnutá betónová dlažba · ${surface.areaM2} m²`,
        surface.polygonMm,
        0.025,
      );
      this.appearance(
        paving,
        this.materials.paving,
        this.realisticMaterials.paving,
      );
      paving.receiveShadows = true;
      this.register(paving, "street", surface.id);
    }
  }

  private buildFence() {
    const style = SITE_FENCE.visualProposal;
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
      if (run.treatment === "LIVING_HEDGE") continue;
      for (let index = 1; index < run.pointsMm.length; index += 1) {
        const start = run.pointsMm[index - 1];
        const end = run.pointsMm[index];
        const lengthMm = Math.hypot(end.x - start.x, end.y - start.y);
        const yawRad = sceneYawForPlanSegment(start, end);
        if (run.treatment === "SLATTED_ALUMINIUM") {
          fixedSlats.push(
            ...slatInstancesForSegment(
              start,
              end,
              style.slatWidthMm,
              style.slatDepthMm,
              style.slatPitchMm,
              fixedSlatHeightMm,
              fixedSlatBottomMm,
            ),
          );
          for (const railBaseElevationMm of [420, 1320]) {
            fixedRails.push(
              segmentBox(
                start,
                end,
                style.railDepthMm,
                style.railWidthMm,
                railBaseElevationMm,
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
                style.curbHeightMm,
              ),
            );
          }
        }
        fixedCurbs.push(
          segmentBox(
            start,
            end,
            style.curbDepthMm,
            style.curbHeightMm,
            0,
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
            heightMm: style.proposedHeightMm,
            baseElevationMm: 0,
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
    for (const run of SITE_FENCE.physicalFixedRuns) {
      if (run.treatment !== "LIVING_HEDGE") continue;
      for (let index = 1; index < run.pointsMm.length; index += 1) {
        const start = run.pointsMm[index - 1];
        const end = run.pointsMm[index];
        const lengthMm = Math.hypot(end.x - start.x, end.y - start.y);
        const yawRad = sceneYawForPlanSegment(start, end);
        const rowOffsetsMm = [
          style.rearHedgeCenterlineOffsetMm - style.rearHedgeDepthMm / 6,
          style.rearHedgeCenterlineOffsetMm + style.rearHedgeDepthMm / 6,
        ];
        for (const [row, inwardMm] of rowOffsetsMm.entries()) {
          const inward = inwardOffsetForSegment(start, end, inwardMm);
          const rowStartMm = 450 + row * 310;
          for (
            let distanceMm = rowStartMm;
            distanceMm <= lengthMm - 450;
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
              baseElevationMm: -40,
              yawRad,
            });
          }
        }
      }
    }
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
              gateSlatBottomMm,
            ),
          );
        } else {
          infill.push(
            segmentBox(
              panelStart,
              panelEnd,
              style.solidPanelDepthMm,
              gateSlatHeightMm,
              gateSlatBottomMm,
            ),
          );
        }
        frame.push(
          segmentBox(panelStart, panelEnd, 44, 80, gateSlatBottomMm),
          segmentBox(
            panelStart,
            panelEnd,
            44,
            80,
            style.proposedHeightMm - 80,
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
            baseElevationMm: gateSlatBottomMm,
            yawRad: gateYaw,
          });
        }
      }
      const gatePosts: PlanBoxInstance[] = supportPostCentersMm.map(
        (centerMm) => ({
          centerMm,
          widthMm: style.gatePostSizeMm,
          depthMm: style.gatePostSizeMm,
          heightMm: style.proposedHeightMm,
          baseElevationMm: 0,
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
      -0.025,
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
          22,
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
    this.buildJoinedRoof();

    const garageDoorSpec = HOUSE.facades.front.garageDoor;
    const garageDoor = boxAtPlan(
      this.scene,
      "Garážová brána od ulice · 3 300 × 2 400 mm · RAL 7016",
      {
        x: garageDoorSpec.startXmm + garageDoorSpec.widthMm / 2,
        y: HOUSE.facades.front.faceYmm - 36,
      },
      garageDoorSpec.widthMm,
      80,
      2.4,
      0,
    );
    this.appearance(
      garageDoor,
      this.materials.glass,
      this.realisticMaterials.roofEdge,
    );
    garageDoor.receiveShadows = true;
    garageDoor.isPickable = false;
    this.register(garageDoor, "building");

    for (let levelM = 0.3; levelM < 2.4; levelM += 0.3) {
      const joint = boxAtPlan(
        this.scene,
        `Horizontálna škára garážovej brány ${levelM.toFixed(1)}`,
        {
          x: garageDoorSpec.startXmm + garageDoorSpec.widthMm / 2,
          y: HOUSE.facades.front.faceYmm - 82,
        },
        garageDoorSpec.widthMm - 60,
        34,
        0.018,
        levelM,
      );
      joint.material = this.realisticMaterials.glassFrame;
      joint.isPickable = false;
      this.realisticOnly(joint);
      this.register(joint, "building");
    }

    for (const [index, chimneySpec] of HOUSE.chimneys.entries()) {
      const center = chimneySpec.centerMm;
      const chimney = boxAtPlan(
        this.scene,
        `Komín ${index + 1} · ${chimneySpec.id} · +6,160 m`,
        center,
        540,
        540,
        3.16,
        3,
      );
      this.appearance(
        chimney,
        this.materials.roof,
        this.realisticMaterials.chimney,
      );
      this.castShadow(chimney);
      chimney.isPickable = false;
      this.register(chimney, "building");

      const cap = boxAtPlan(
        this.scene,
        `Nerezové ukončenie komína ${index + 1}`,
        center,
        580,
        580,
        0.02,
        HOUSE.chimneyElevationMm * MM_TO_M - 0.02,
      );
      cap.material = this.realisticMaterials.chimney;
      cap.isPickable = false;
      this.realisticOnly(cap);
      this.castShadow(cap);
      this.register(cap, "building");
    }

    for (const downpipe of HOUSE.rainwaterDownpipes) {
      const heightM = HOUSE.eavesElevationMm * MM_TO_M - 0.03;
      const porch = HOUSE.porches.wingEnd;
      // The IO01 route stays authoritative; only the visual pipe steps aside
      // when it would cross the open porch front.
      const insidePorchFront =
        downpipe.faceYmm === porch.frontYmm &&
        downpipe.xMm > porch.glazing.startXmm &&
        downpipe.xMm < porch.backWall.endXmm;
      const visualXmm = insidePorchFront ? porch.backWall.endXmm + 380 : downpipe.xMm;
      const pipe = CreateCylinder(
        `${downpipe.id} · dažďový zvod · vizualizačný detail IO01`,
        { height: heightM, diameter: 0.1, tessellation: 16 },
        this.scene,
      );
      pipe.position.set(
        xM(visualXmm),
        0.03 + heightM / 2,
        zM(downpipe.faceYmm + 65),
      );
      pipe.material = this.realisticMaterials.roofEdge;
      pipe.isPickable = false;
      this.realisticOnly(pipe);
      this.castShadow(pipe);
      this.register(pipe, "building");
    }
  }

  private buildJoinedRoof() {
    const roof = deriveJoinedRoofGeometry();

    for (const face of roof.faces) {
      const panel = createRoofFace(
        this.scene,
        `Spojená strešná rovina · ${face.id}`,
        face.vertexIndices.map((index) => roof.vertices[index]),
      );
      this.appearance(panel, this.materials.roof, this.realisticMaterials.roof);
      panel.receiveShadows = false;
      this.castShadow(panel);
      panel.enableEdgesRendering();
      panel.edgesColor = Color4.FromHexString("#aeb8bb66");
      panel.edgesWidth = 0.65;
      this.register(panel, "building", HOUSE.id);
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
    garageGable.receiveShadows = false;
    this.register(garageGable, "building", HOUSE.id);

    const wingEndY = HOUSE.originMm.y + HOUSE.maximumDepthMm + 8;
    const wingLeftX = HOUSE.originMm.x + HOUSE.wing.xMm;
    const wingRightX = wingLeftX + HOUSE.wing.widthMm;
    // The gable itself is the recessed porch wall, 2 500 mm behind the roof
    // line: the front stays an open frame of white rakes, exactly as the
    // approved reference photograph and the D1.1.006 elevation read.
    const gableYmm = HOUSE.porches.wingEnd.gablePlaneYmm + 20;
    const wingGable = createVerticalTriangle(
      this.scene,
      "Modřínový štít krytej terasy · zapustený 2 500 mm",
      [
        new Vector3(xM(wingLeftX), eave, zM(gableYmm)),
        new Vector3(xM(wingRightX), eave, zM(gableYmm)),
        new Vector3(xM((wingLeftX + wingRightX) / 2), ridge, zM(gableYmm)),
      ],
      new Vector3(0, 0, -1),
    );
    // 7 m gable ÷ 50 mm boards = 140 boards; the tile carries 20 boards and
    // the triangle's planar UVs span 2.45, hence uScale 7 / 2.45.
    this.appearance(
      wingGable,
      this.materials.wall,
      this.larchFor(2.86, 2.44, "wing-gable"),
    );
    this.register(wingGable, "building", HOUSE.id);

    const gableRise = ridge - eave;
    for (const [index, lamp] of [
      { x: 22600, elevationM: 3.5 },
      { x: 26400, elevationM: 3.5 },
    ].entries()) {
      const fixture = boxAtPlan(
        this.scene,
        `Nástenné svietidlo štítu ${index + 1} · ilustračný koncept`,
        { x: lamp.x, y: gableYmm + 30 },
        95,
        70,
        0.17,
        lamp.elevationM,
      );
      fixture.material = this.realisticMaterials.glassFrame;
      fixture.isPickable = false;
      this.realisticOnly(fixture);
      this.register(fixture, "building");
    }

    const halfSpanM = (HOUSE.wing.widthMm * MM_TO_M) / 2;
    const gableEdgeLength = Math.hypot(halfSpanM, gableRise);
    const edgeAngle = Math.atan2(gableRise, halfSpanM);
    for (const side of [-1, 1]) {
      const edge = CreateBox(
        `Biely rám záhradného štítu ${side}`,
        { width: gableEdgeLength, depth: 0.12, height: 0.16 },
        this.scene,
      );
      edge.position.set(
        xM(wingLeftX + HOUSE.wing.widthMm / 2 + side * HOUSE.wing.widthMm / 4),
        eave + gableRise / 2,
        zM(wingEndY + 72),
      );
      edge.rotation.z = -side * edgeAngle;
      edge.material = this.realisticMaterials.wall;
      edge.isPickable = false;
      this.realisticOnly(edge);
      this.castShadow(edge);
      this.register(edge, "building");
    }
  }

  private buildRoofEdges(roof: JoinedRoofGeometry) {
    const { parameters } = roof;
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
      {
        name: "Vnútorná okapová hrana krídla · vizualizačný profil",
        center: {
          x: parameters.wingInnerEaveXmm - 60,
          y: (parameters.gardenEaveYmm + parameters.wingEndYmm) / 2,
        },
        widthMm: 105,
        depthMm: parameters.wingEndYmm - parameters.gardenEaveYmm + 120,
      },
      {
        name: "Vonkajšia okapová hrana krídla · vizualizačný profil",
        center: {
          x: parameters.maxXmm + 60,
          y: (parameters.frontEaveYmm + parameters.wingEndYmm) / 2,
        },
        widthMm: 105,
        depthMm: parameters.wingEndYmm - parameters.frontEaveYmm + 120,
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

    for (const ridge of [
      {
        name: "Hrebeňový profil hlavného traktu",
        center: {
          x: (parameters.minXmm + parameters.wingRidgeXmm) / 2,
          y: parameters.mainRidgeYmm,
        },
        widthMm: parameters.wingRidgeXmm - parameters.minXmm + 100,
        depthMm: 125,
      },
      {
        name: "Hrebeňový profil krídla",
        center: {
          x: parameters.wingRidgeXmm,
          y: (parameters.mainRidgeYmm + parameters.wingEndYmm) / 2,
        },
        widthMm: 125,
        depthMm: parameters.wingEndYmm - parameters.mainRidgeYmm + 100,
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

        const frame = CreateBox(
          `Rám FV ${column + 1}.${row + 1}`,
          {
            width: (photovoltaics.moduleSlopeLengthMm + 40) * MM_TO_M,
            depth: (photovoltaics.moduleRidgeWidthMm + 40) * MM_TO_M,
            height: 0.016,
          },
          this.scene,
        );
        frame.position.set(
          xM(centerXmm),
          surfaceElevationM + 0.03,
          zM(centerYmm),
        );
        frame.rotation.x = mount.rotationXRad;
        frame.rotation.z = mount.rotationZRad;
        frame.material = this.realisticMaterials.solarGrid;
        frame.isPickable = false;
        this.realisticOnly(frame);
        this.register(frame, "building");
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
      );
    }
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
    );
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

  /** Covered gable porch of the wing — glazing recessed 2.5 m (D1.1.002). */
  private buildWingPorch() {
    const porch = HOUSE.porches.wingEnd;
    const wallTopM = HOUSE.eavesElevationMm * MM_TO_M;
    const roofParameters = deriveJoinedRoofGeometry().parameters;
    const clearanceMm = porch.ceilingClearanceMm;

    const backSegments = segmentFacadeMm(
      porch.glazing.startXmm,
      porch.backWall.endXmm,
      HOUSE.eavesElevationMm,
      [
        {
          id: "PORCH-GLAZING",
          startMm: porch.glazing.startXmm,
          widthMm: porch.glazing.widthMm,
          heightMm: porch.glazing.heightMm,
          sillMm: porch.glazing.sillMm,
        },
      ],
    );
    for (const [index, segment] of backSegments.entries()) {
      const mesh = boxAtPlan(
        this.scene,
        `Krytá terasa · zadná stena ${index + 1}`,
        {
          x: (segment.startMm + segment.endMm) / 2,
          y: porch.glazingFaceYmm - 250,
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
    // Larch cladding on the recessed masonry (24 040 – 27 540).
    const backLarchWidthM = (porch.backWall.endXmm - porch.backWall.startXmm) * MM_TO_M;
    const backLarch = boxAtPlan(
      this.scene,
      "Krytá terasa · modřínový obklad zadnej steny",
      {
        x: (porch.backWall.startXmm + porch.backWall.endXmm) / 2,
        y: porch.glazingFaceYmm + 18,
      },
      porch.backWall.endXmm - porch.backWall.startXmm,
      36,
      wallTopM,
      0,
    );
    backLarch.material = this.larchFor(backLarchWidthM, wallTopM, "porch-back");
    backLarch.receiveShadows = true;
    backLarch.isPickable = false;
    this.realisticOnly(backLarch);
    this.register(backLarch, "building", HOUSE.id);

    // Recessed glazed wall (fixed pane + door per the drawing dashes).
    this.buildWindowOnZFace(
      "Krytá terasa · presklená stena 2 500 · D1.1.002",
      porch.glazing.startXmm + porch.glazing.widthMm / 2,
      porch.glazingFaceYmm,
      porch.glazing.widthMm,
      porch.glazing.heightMm,
      porch.glazing.sillMm,
      1,
      this.realisticMaterials.wall,
      this.realisticMaterials.glassFrameWood,
    );

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

    // Two concrete entry steps down to the lawn (reference photograph).
    for (const [index, step] of [
      { y0: porch.frontYmm, y1: porch.frontYmm + 380, top: -0.04 },
      { y0: porch.frontYmm + 380, y1: porch.frontYmm + 760, top: -0.095 },
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

  private buildWindowOnZFace(
    name: string,
    centerXmm: number,
    faceYmm: number,
    widthMm: number,
    heightMm: number,
    sillMm: number,
    outwardY: -1 | 1,
    revealMaterial: PBRMaterial,
    frameMaterial?: PBRMaterial,
  ) {
    const frameMat = frameMaterial ?? this.realisticMaterials.glassFrame;
    const recess = boxAtPlan(
      this.scene,
      `${name} · interiérová hĺbka`,
      { x: centerXmm, y: faceYmm - outwardY * 740 },
      widthMm + 120,
      26,
      (heightMm + 120) * MM_TO_M,
      Math.max(0, sillMm - 60) * MM_TO_M,
    );
    recess.material = this.realisticMaterials.interiorDark;
    recess.isPickable = false;
    this.realisticOnly(recess);
    this.register(recess, "building");

    const curtainWidthMm = Math.max(150, Math.min(420, widthMm * 0.18));
    for (let index = 0; index < 2; index += 1) {
      const curtain = boxAtPlan(
        this.scene,
        `${name} · záclona ${index + 1}`,
        {
          x:
            centerXmm +
            (index === 0 ? -1 : 1) *
              (widthMm / 2 - curtainWidthMm / 2 - 55),
          y: faceYmm - outwardY * (640 + (index % 2) * 18),
        },
        curtainWidthMm,
        16,
        Math.max(0.2, (heightMm - 130) * MM_TO_M),
        (sillMm + 65) * MM_TO_M,
      );
      curtain.material = this.realisticMaterials.curtain;
      curtain.isPickable = false;
      this.realisticOnly(curtain);
      this.register(curtain, "building");
    }

    const interiorSill = boxAtPlan(
      this.scene,
      `${name} · interiérový parapet`,
      { x: centerXmm, y: faceYmm - outwardY * 620 },
      Math.max(180, widthMm - 90),
      440,
      0.035,
      Math.max(0.018, sillMm * MM_TO_M),
    );
    interiorSill.material = this.realisticMaterials.warmInterior;
    interiorSill.isPickable = false;
    this.realisticOnly(interiorSill);
    this.register(interiorSill, "building");

    this.buildZOpeningReveals(
      name,
      centerXmm,
      faceYmm,
      widthMm,
      heightMm,
      sillMm,
      outwardY,
      revealMaterial,
    );

    const opening = boxAtPlan(
      this.scene,
      name,
      { x: centerXmm, y: faceYmm - outwardY * 112 },
      widthMm,
      22,
      heightMm * MM_TO_M,
      sillMm * MM_TO_M,
    );
    this.appearance(opening, this.materials.glass, this.realisticMaterials.glass);
    opening.metadata = { ...(opening.metadata ?? {}), entityId: HOUSE.id };
    opening.isPickable = true;
    this.register(opening, "building");
    this.buildWindowFrameZ(
      name,
      centerXmm,
      faceYmm - outwardY * 84,
      widthMm,
      heightMm,
      sillMm,
      frameMat,
    );
  }

  private buildZOpeningReveals(
    name: string,
    centerXmm: number,
    faceYmm: number,
    widthMm: number,
    heightMm: number,
    sillMm: number,
    outwardY: -1 | 1,
    finish: PBRMaterial,
  ) {
    const revealDepthMm = 130;
    const jambMm = 42;
    const revealYmm = faceYmm - outwardY * revealDepthMm / 2;
    for (const [side, xMm] of [
      ["ľavé", centerXmm - widthMm / 2 + jambMm / 2],
      ["pravé", centerXmm + widthMm / 2 - jambMm / 2],
    ] as const) {
      const jamb = boxAtPlan(
        this.scene,
        `${name} · ${side} ostenie`,
        { x: xMm, y: revealYmm },
        jambMm,
        revealDepthMm,
        heightMm * MM_TO_M,
        sillMm * MM_TO_M,
      );
      jamb.material = finish;
      jamb.isPickable = false;
      this.realisticOnly(jamb);
      this.register(jamb, "building");
    }

    for (const [part, elevationMm, material] of [
      ["nadpražie", sillMm + heightMm - jambMm, finish],
      [
        sillMm === 0 ? "prahový profil" : "parapetné ostenie",
        sillMm,
        sillMm === 0 ? this.realisticMaterials.glassFrame : finish,
      ],
    ] as const) {
      const reveal = boxAtPlan(
        this.scene,
        `${name} · ${part}`,
        { x: centerXmm, y: revealYmm },
        widthMm,
        revealDepthMm,
        part === "prahový profil" ? 0.025 : jambMm * MM_TO_M,
        elevationMm * MM_TO_M,
      );
      reveal.material = material;
      reveal.isPickable = false;
      this.realisticOnly(reveal);
      this.register(reveal, "building");
    }
  }

  private buildXOpeningReveals(
    name: string,
    faceXmm: number,
    centerYmm: number,
    widthMm: number,
    heightMm: number,
    sillMm: number,
    outwardX: -1 | 1,
    finish: PBRMaterial,
  ) {
    const revealDepthMm = 130;
    const jambMm = 42;
    const revealXmm = faceXmm - outwardX * revealDepthMm / 2;
    for (const [side, yMm] of [
      ["ľavé", centerYmm - widthMm / 2 + jambMm / 2],
      ["pravé", centerYmm + widthMm / 2 - jambMm / 2],
    ] as const) {
      const jamb = boxAtPlan(
        this.scene,
        `${name} · ${side} ostenie`,
        { x: revealXmm, y: yMm },
        revealDepthMm,
        jambMm,
        heightMm * MM_TO_M,
        sillMm * MM_TO_M,
      );
      jamb.material = finish;
      jamb.isPickable = false;
      this.realisticOnly(jamb);
      this.register(jamb, "building");
    }

    for (const [part, elevationMm, material] of [
      ["nadpražie", sillMm + heightMm - jambMm, finish],
      [
        sillMm === 0 ? "prahový profil" : "parapetné ostenie",
        sillMm,
        sillMm === 0 ? this.realisticMaterials.glassFrame : finish,
      ],
    ] as const) {
      const reveal = boxAtPlan(
        this.scene,
        `${name} · ${part}`,
        { x: revealXmm, y: centerYmm },
        revealDepthMm,
        widthMm,
        part === "prahový profil" ? 0.025 : jambMm * MM_TO_M,
        elevationMm * MM_TO_M,
      );
      reveal.material = material;
      reveal.isPickable = false;
      this.realisticOnly(reveal);
      this.register(reveal, "building");
    }
  }

  private buildWindowFrameZ(
    name: string,
    centerXmm: number,
    yMm: number,
    widthMm: number,
    heightMm: number,
    sillMm: number,
    frameMaterial?: PBRMaterial,
  ) {
    const material = frameMaterial ?? this.realisticMaterials.glassFrame;
    const frame = 58;
    const horizontal = [sillMm, sillMm + heightMm];
    const vertical = [centerXmm - widthMm / 2, centerXmm + widthMm / 2];
    if (widthMm >= 1800) vertical.push(centerXmm + widthMm * 0.08);
    for (const xMm of vertical) {
      const bar = boxAtPlan(
        this.scene,
        `${name} · rám zvislý`,
        { x: xMm, y: yMm },
        frame,
        72,
        heightMm * MM_TO_M + 0.06,
        sillMm * MM_TO_M - 0.03,
      );
      bar.material = material;
      bar.isPickable = false;
      this.realisticOnly(bar);
      this.register(bar, "building");
    }
    for (const levelMm of horizontal) {
      const bar = boxAtPlan(
        this.scene,
        `${name} · rám vodorovný`,
        { x: centerXmm, y: yMm },
        widthMm + frame,
        72,
        0.058,
        levelMm * MM_TO_M - 0.029,
      );
      bar.material = material;
      bar.isPickable = false;
      this.realisticOnly(bar);
      this.register(bar, "building");
    }
  }

  private buildWindowOnXFace(
    name: string,
    faceXmm: number,
    centerYmm: number,
    widthMm: number,
    heightMm: number,
    sillMm: number,
    outwardX: -1 | 1,
    revealMaterial: PBRMaterial,
    frameMaterial?: PBRMaterial,
  ) {
    const frameMat = frameMaterial ?? this.realisticMaterials.glassFrame;
    const recess = boxAtPlan(
      this.scene,
      `${name} · interiérová hĺbka`,
      { x: faceXmm - outwardX * 740, y: centerYmm },
      26,
      widthMm + 120,
      (heightMm + 120) * MM_TO_M,
      Math.max(0, sillMm - 60) * MM_TO_M,
    );
    recess.material = this.realisticMaterials.interiorDark;
    recess.isPickable = false;
    this.realisticOnly(recess);
    this.register(recess, "building");

    const curtainWidthMm = Math.max(150, Math.min(420, widthMm * 0.18));
    for (let index = 0; index < 2; index += 1) {
      const curtain = boxAtPlan(
        this.scene,
        `${name} · záclona ${index + 1}`,
        {
          x: faceXmm - outwardX * (640 + (index % 2) * 18),
          y:
            centerYmm +
            (index === 0 ? -1 : 1) *
              (widthMm / 2 - curtainWidthMm / 2 - 55),
        },
        16,
        curtainWidthMm,
        Math.max(0.2, (heightMm - 130) * MM_TO_M),
        (sillMm + 65) * MM_TO_M,
      );
      curtain.material = this.realisticMaterials.curtain;
      curtain.isPickable = false;
      this.realisticOnly(curtain);
      this.register(curtain, "building");
    }

    const interiorSill = boxAtPlan(
      this.scene,
      `${name} · interiérový parapet`,
      { x: faceXmm - outwardX * 620, y: centerYmm },
      440,
      Math.max(180, widthMm - 90),
      0.035,
      Math.max(0.018, sillMm * MM_TO_M),
    );
    interiorSill.material = this.realisticMaterials.warmInterior;
    interiorSill.isPickable = false;
    this.realisticOnly(interiorSill);
    this.register(interiorSill, "building");

    this.buildXOpeningReveals(
      name,
      faceXmm,
      centerYmm,
      widthMm,
      heightMm,
      sillMm,
      outwardX,
      revealMaterial,
    );

    const opening = boxAtPlan(
      this.scene,
      name,
      { x: faceXmm - outwardX * 112, y: centerYmm },
      22,
      widthMm,
      heightMm * MM_TO_M,
      sillMm * MM_TO_M,
    );
    this.appearance(opening, this.materials.glass, this.realisticMaterials.glass);
    opening.metadata = { ...(opening.metadata ?? {}), entityId: HOUSE.id };
    opening.isPickable = true;
    this.register(opening, "building");

    const frame = 58;
    const horizontal = [sillMm, sillMm + heightMm];
    const vertical = [centerYmm - widthMm / 2, centerYmm + widthMm / 2];
    if (widthMm >= 1800) vertical.push(centerYmm + widthMm * 0.08);
    for (const yMm of vertical) {
      const bar = boxAtPlan(
        this.scene,
        `${name} · rám zvislý`,
        { x: faceXmm - outwardX * 84, y: yMm },
        72,
        frame,
        heightMm * MM_TO_M + 0.06,
        sillMm * MM_TO_M - 0.03,
      );
      bar.material = frameMat;
      bar.isPickable = false;
      this.realisticOnly(bar);
      this.register(bar, "building");
    }
    for (const levelMm of horizontal) {
      const bar = boxAtPlan(
        this.scene,
        `${name} · rám vodorovný`,
        { x: faceXmm - outwardX * 84, y: centerYmm },
        72,
        widthMm + frame,
        0.058,
        levelMm * MM_TO_M - 0.029,
      );
      bar.material = frameMat;
      bar.isPickable = false;
      this.realisticOnly(bar);
      this.register(bar, "building");
    }
  }

  /** Real board-by-board decking for one documented D1 terrace zone. */
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
        const lengthM = (rect.x1 - rect.x0) * MM_TO_M;
        const u0 = (rowIndex * 0.317) % 0.8;
        const uSpan = Math.min(0.98 - u0, Math.max(0.25, lengthM / 4.6));
        const v0 = (rowIndex % 4) * 0.25;
        const faceUV: Vector4[] = [];
        for (let face = 0; face < 6; face += 1) {
          faceUV.push(new Vector4(u0, v0, u0 + uSpan, v0 + 0.24));
        }
        const plank = CreateBox(
          `${zone.label} · doska ${rowIndex + 1}`,
          {
            width: lengthM - 0.012,
            depth: (y1 - y) * MM_TO_M,
            height: thicknessM,
            faceUV,
            wrap: true,
          },
          this.scene,
        );
        plank.position.set(
          xM((rect.x0 + rect.x1) / 2),
          topM - thicknessM / 2,
          zM((y + y1) / 2),
        );
        planks.push(plank);
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
    this.register(merged, "street", zone.id);
  }

  private buildGardenPool() {
    const pool = GARDEN_POOL;
    const basin = boxAtPlan(
      this.scene,
      `${pool.label} · tmavý bazénový plášť`,
      pool.centerMm,
      pool.waterLengthMm + 140,
      pool.waterWidthMm + 140,
      0.42,
      -0.49,
    );
    this.appearance(
      basin,
      this.materials.poolWater,
      this.realisticMaterials.poolBasin,
    );
    basin.receiveShadows = true;
    this.register(basin, "street", pool.id);

    const water = boxAtPlan(
      this.scene,
      `${pool.label} · vodná plocha presne 4 000 × 2 500 mm`,
      pool.centerMm,
      pool.waterLengthMm,
      pool.waterWidthMm,
      0.045,
      -0.055,
    );
    this.appearance(
      water,
      this.materials.poolWater,
      this.realisticMaterials.poolWater,
    );
    water.receiveShadows = true;
    this.register(water, "street", pool.id);

    const coping = pool.copingWidthMm;
    const outerLengthMm = pool.waterLengthMm + 2 * coping;
    const copingSegments = [
      {
        centerMm: {
          x: pool.centerMm.x,
          y: pool.centerMm.y - pool.waterWidthMm / 2 - coping / 2,
        },
        widthMm: outerLengthMm,
        depthMm: coping,
      },
      {
        centerMm: {
          x: pool.centerMm.x,
          y: pool.centerMm.y + pool.waterWidthMm / 2 + coping / 2,
        },
        widthMm: outerLengthMm,
        depthMm: coping,
      },
      {
        centerMm: {
          x: pool.centerMm.x - pool.waterLengthMm / 2 - coping / 2,
          y: pool.centerMm.y,
        },
        widthMm: coping,
        depthMm: pool.waterWidthMm,
      },
      {
        centerMm: {
          x: pool.centerMm.x + pool.waterLengthMm / 2 + coping / 2,
          y: pool.centerMm.y,
        },
        widthMm: coping,
        depthMm: pool.waterWidthMm,
      },
    ];
    for (const [index, segment] of copingSegments.entries()) {
      const copingMesh = boxAtPlan(
        this.scene,
        `${pool.label} · svetlý porcelánový lem ${index + 1}`,
        segment.centerMm,
        segment.widthMm,
        segment.depthMm,
        0.09,
        -0.045,
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

    const ledSegments = [
      {
        centerMm: {
          x: pool.centerMm.x,
          y: pool.centerMm.y - pool.waterWidthMm / 2 + 22,
        },
        widthMm: pool.waterLengthMm - 80,
        depthMm: 18,
      },
      {
        centerMm: {
          x: pool.centerMm.x,
          y: pool.centerMm.y + pool.waterWidthMm / 2 - 22,
        },
        widthMm: pool.waterLengthMm - 80,
        depthMm: 18,
      },
      {
        centerMm: {
          x: pool.centerMm.x - pool.waterLengthMm / 2 + 22,
          y: pool.centerMm.y,
        },
        widthMm: 18,
        depthMm: pool.waterWidthMm - 80,
      },
      {
        centerMm: {
          x: pool.centerMm.x + pool.waterLengthMm / 2 - 22,
          y: pool.centerMm.y,
        },
        widthMm: 18,
        depthMm: pool.waterWidthMm - 80,
      },
    ];
    for (const [index, segment] of ledSegments.entries()) {
      const led = boxAtPlan(
        this.scene,
        `${pool.label} · zapustený LED pás ${index + 1}`,
        segment.centerMm,
        segment.widthMm,
        segment.depthMm,
        0.018,
        -0.032,
      );
      this.appearance(
        led,
        this.materials.poolWater,
        this.realisticMaterials.poolLed,
      );
      this.register(led, "street", pool.id);
    }

    for (const [index, step] of [
      { x: 9_930, widthMm: 360, topM: -0.14 },
      { x: 10_250, widthMm: 280, topM: -0.27 },
      { x: 10_510, widthMm: 240, topM: -0.4 },
    ].entries()) {
      const heightM = 0.1;
      const stair = boxAtPlan(
        this.scene,
        `${pool.label} · ponorený schod ${index + 1}`,
        { x: step.x, y: pool.centerMm.y },
        step.widthMm,
        1_250,
        heightM,
        step.topM - heightM,
      );
      this.appearance(
        stair,
        this.materials.paving,
        this.realisticMaterials.stone,
      );
      stair.receiveShadows = true;
      this.register(stair, "street", pool.id);
    }

    const outline = CreateLines(
      `${pool.label} · koordinačný obrys lemu`,
      {
        points: pool.copingFootprintMm.map((point) => point3(point, 0.055)),
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
        -0.01,
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
        { x: 8900, y: 15300 },
        { x: 9200, y: 16500 },
        { x: 9200, y: 17550 },
        { x: 11200, y: 18150 },
        { x: 14400, y: 18800 },
        { x: 17400, y: 19900 },
        { x: 17600, y: 20600 },
        { x: 15800, y: 19900 },
        { x: 13900, y: 19200 },
        { x: 11000, y: 18700 },
        { x: 8800, y: 18000 },
        { x: 7400, y: 16900 },
        { x: 5400, y: 16000 },
        { x: 3600, y: 15000 },
        { x: 3600, y: 14200 },
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
        -0.012,
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
      { x: 8700, y: 16400, s: 1.25 },
      { x: 9000, y: 17650, s: 0.92 },
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
    const plane = CreatePlane(
      `${name} · botanická karta`,
      { width: widthM, height: heightM },
      this.scene,
    );
    plane.position.set(xM(xMm), heightM * 0.48 - 0.06, zM(yMm));
    plane.billboardMode = Mesh.BILLBOARDMODE_Y;
    plane.scaling.x = Math.sin(rotation) < 0 ? -1 : 1;
    plane.material = material;
    plane.isPickable = false;
    this.realisticOnly(plane);
    this.register(plane, "street");
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
      { x: 26650, y: 20500 },
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
      { x: 26650, y: 20500 },
      1850,
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
      { x: 26650, y: 20870 },
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
    rainTank.position.set(xM(16230), 0.12, zM(17165));
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
      for (const mesh of meshes) mesh.setEnabled(snapshot.visibleLayers[layer]);
    }
    this.applyViewMode(snapshot.viewMode);
    if (snapshot.selectionId) {
      const emphasizeEdges =
        snapshot.selectionId === HOUSE.id || snapshot.selectionId.startsWith("F-");
      for (const mesh of this.entityMeshes.get(snapshot.selectionId) ?? []) {
        if (mesh.isEnabled() && mesh.visibility > 0.01) {
          this.selectedOriginals.set(mesh, {
            material: mesh.material,
            lineColor: mesh instanceof LinesMesh ? mesh.color.clone() : undefined,
            edgeColor:
              emphasizeEdges && mesh instanceof Mesh
                ? mesh.edgesColor.clone()
                : undefined,
            edgeWidth:
              emphasizeEdges && mesh instanceof Mesh
                ? mesh.edgesWidth
                : undefined,
          });
          if (mesh instanceof LinesMesh) {
            mesh.color = Color3.FromHexString("#ff5738");
          } else if (emphasizeEdges && mesh instanceof Mesh) {
            mesh.edgesColor = Color4.FromHexString("#ff5738ff");
            mesh.edgesWidth = 2.2;
          } else {
            mesh.material = this.materials.selection;
          }
        }
      }
    }
  }

  private clearSelection() {
    for (const [mesh, original] of this.selectedOriginals) {
      if (mesh.isDisposed()) continue;
      mesh.material = original.material;
      if (original.lineColor && mesh instanceof LinesMesh) {
        mesh.color = original.lineColor;
      }
      if (original.edgeColor && mesh instanceof Mesh) {
        mesh.edgesColor = original.edgeColor;
        mesh.edgesWidth = original.edgeWidth ?? mesh.edgesWidth;
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
    this.setNavigationMode("orbit");
    this.resetOrbitInertia();
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
    if (preset === "street") {
      this.orbitCamera.alpha = STREET_CAMERA_ALPHA;
      this.orbitCamera.beta = Math.PI * 0.39;
      this.orbitCamera.radius = this.canvas.clientWidth < 600 ? 43 : 31;
      this.orbitCamera.fov = 0.68;
      this.orbitCamera.target.set(-1, 1.4, 4.8);
      return;
    }
    if (preset === "focus") {
      const meshes = this.snapshot?.selectionId
        ? this.entityMeshes.get(this.snapshot.selectionId)
        : undefined;
      const mesh = meshes?.find((candidate) => candidate.isEnabled());
      if (mesh) {
        this.orbitCamera.target.copyFrom(
          mesh.getBoundingInfo().boundingBox.centerWorld,
        );
        const extent = mesh.getBoundingInfo().boundingBox.extendSizeWorld.length();
        this.orbitCamera.radius = Math.max(7, Math.min(35, extent * 3.2));
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
    if (mode === this.navigationMode) return;
    if (mode === "flight") {
      const orbitPosition = this.orbitCamera.globalPosition.clone();
      this.orbitFocusDistance = Math.max(
        8,
        Math.min(32, Vector3.Distance(orbitPosition, this.orbitCamera.target)),
      );
      const boundedEntry = integrateFlightPosition({
        position: orbitPosition,
        heading: { x: 0, z: -1 },
        commands: new Set(),
        deltaMs: 0,
      });
      this.flightCamera.position.set(
        boundedEntry.x,
        boundedEntry.y,
        boundedEntry.z,
      );
      this.flightCamera.rotationQuaternion = null;
      this.flightCamera.fov = this.orbitCamera.fov;
      this.flightCamera.setTarget(this.orbitCamera.target);
      const forward = this.flightCamera.getForwardRay(1).direction;
      const horizontalLength = Math.hypot(forward.x, forward.z);
      if (horizontalLength > 0.04) {
        this.flightHeading = {
          x: forward.x / horizontalLength,
          z: forward.z / horizontalLength,
        };
      }
      this.orbitCamera.detachControl();
      this.scene.activeCamera = this.flightCamera;
      this.flightCamera.attachControl(false);
      this.navigationMode = "flight";
      this.canvas.focus({ preventScroll: true });
    } else {
      const forward = this.flightCamera.getForwardRay(1).direction.normalize();
      const target = this.flightCamera.position.add(
        forward.scale(this.orbitFocusDistance),
      );
      this.flightCamera.detachControl();
      this.clearFlightInput();
      this.orbitCamera.target.copyFrom(target);
      this.orbitCamera.setPosition(this.flightCamera.position.clone());
      this.orbitCamera.fov = this.flightCamera.fov;
      this.resetOrbitInertia();
      this.scene.activeCamera = this.orbitCamera;
      this.orbitCamera.attachControl(this.canvas, true);
      this.navigationMode = "orbit";
    }
    this.onNavigationModeChange(this.navigationMode);
  }

  setFlightCommand(command: FlightCommand, active: boolean) {
    if (active) this.manualFlightCommands.add(command);
    else this.manualFlightCommands.delete(command);
  }

  nudgeFlight(command: FlightCommand) {
    if (this.navigationMode !== "flight") return;
    const next = integrateFlightPosition({
      position: this.flightCamera.position,
      heading: this.flightHeading,
      commands: new Set([command]),
      deltaMs: 220,
    });
    this.flightCamera.position.set(next.x, next.y, next.z);
  }

  getNavigationMode() {
    return this.navigationMode;
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
      if (this.ssaoPipeline) {
        if (previous.tier !== next.tier) {
          this.ssaoPipeline.samples = next.tier === "ULTRA" ? 16 : 12;
        }
        const cameras = [this.orbitCamera, this.flightCamera];
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
    this.clearFlightInput();
    this.clearSelection();
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
