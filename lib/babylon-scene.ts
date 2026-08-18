import { ArcRotateCamera } from "@babylonjs/core/Cameras/arcRotateCamera";
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
import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { CreateBox } from "@babylonjs/core/Meshes/Builders/boxBuilder.pure";
import { CreateCylinder } from "@babylonjs/core/Meshes/Builders/cylinderBuilder.pure";
import { CreateGround } from "@babylonjs/core/Meshes/Builders/groundBuilder.pure";
import {
  CreateDashedLines,
  CreateLines,
} from "@babylonjs/core/Meshes/Builders/linesBuilder.pure";
import { CreateTube } from "@babylonjs/core/Meshes/Builders/tubeBuilder.pure";
import { CreateSphere } from "@babylonjs/core/Meshes/Builders/sphereBuilder.pure";
import { LinesMesh } from "@babylonjs/core/Meshes/linesMesh";
import { Mesh } from "@babylonjs/core/Meshes/mesh";
import { VertexData } from "@babylonjs/core/Meshes/mesh.vertexData";
import { DefaultRenderingPipeline } from "@babylonjs/core/PostProcesses/RenderPipeline/Pipelines/defaultRenderingPipeline";
import "@babylonjs/core/Rendering/edgesRenderer";
import { Scene } from "@babylonjs/core/scene";
import earcut from "earcut";

import {
  CADASTRAL_PARCELS,
  HOUSE,
  LAYERS,
  ROAD_CONTEXT,
  SITE_SURFACES,
  UTILITY_ROUTES,
  sjtskToLocalMm,
  type FoundationStrip,
  type LayerId,
  type Point2Mm,
  type ViewMode,
} from "./twin-site";
import {
  AXONOMETRIC_CAMERA_ALPHA,
  GARDEN_CAMERA_ALPHA,
  GARDEN_CAMERA_BETA,
  MM_TO_M,
  SCENE_CENTER_MM,
  STREET_CAMERA_ALPHA,
  TOP_CAMERA_ALPHA,
  sceneDeltaForPlanSegment,
  sceneXM as xM,
  sceneYawForPlanSegment,
  sceneZM as zM,
} from "./twin-render-frame";

export type CameraPreset = "garden" | "axonometric" | "top" | "street" | "focus";

export interface SceneSnapshot {
  readonly foundations: readonly FoundationStrip[];
  readonly selectionId: string | null;
  readonly visibleLayers: Readonly<Record<LayerId, boolean>>;
  readonly viewMode: ViewMode;
}

const CENTER_X_M = SCENE_CENTER_MM.x * MM_TO_M;
const GROUND_Y = -0.035;
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
  material.environmentIntensity = 0.72;
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
) {
  const mesh = new Mesh(name, scene);
  const data = new VertexData();
  data.positions = points.flatMap((point) => [point.x, point.y, point.z]);
  data.indices = [0, 2, 1];
  data.normals = [0, 0, 0, 0, 0, 0, 0, 0, 0];
  VertexData.ComputeNormals(data.positions, data.indices, data.normals);
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

export class TwinSceneController {
  private readonly engine: Engine;
  private readonly scene: Scene;
  private readonly camera: ArcRotateCamera;
  private readonly layerMeshes = new Map<LayerId, AbstractMesh[]>();
  private readonly entityMeshes = new Map<string, AbstractMesh[]>();
  private readonly foundationMeshes = new Map<string, Mesh>();
  private readonly materials: Record<string, StandardMaterial>;
  private readonly realisticMaterials: Record<string, PBRMaterial>;
  private readonly appearances = new Map<
    AbstractMesh,
    { technical: Material; realistic: Material }
  >();
  private readonly realisticOnlyMeshes: AbstractMesh[] = [];
  private readonly technicalOverlayMeshes: AbstractMesh[] = [];
  private readonly shadowGenerator: ShadowGenerator;
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
  private snapshot: SceneSnapshot | null = null;

  constructor(
    private readonly canvas: HTMLCanvasElement,
    private readonly onSelect: (id: string) => void,
  ) {
    this.engine = new Engine(canvas, true, {
      preserveDrawingBuffer: false,
      stencil: false,
      adaptToDeviceRatio: true,
    });
    this.engine.setHardwareScalingLevel(
      Math.max(1, Math.min(2, window.devicePixelRatio) / 1.65),
    );
    this.scene = new Scene(this.engine);
    this.scene.useRightHandedSystem = true;
    this.scene.clearColor = Color4.FromHexString("#aebfbdff");
    this.scene.ambientColor = Color3.FromHexString("#59615f");
    const environment = new EquiRectangularCubeTexture(
      "/assets/environment/overcast-garden.jpg",
      this.scene,
      canvas.clientWidth < 700 ? 128 : 256,
      false,
      false,
      () => {
        this.scene.environmentTexture = environment;
        this.scene.environmentIntensity = 0.72;
      },
    );
    const sky = new PhotoDome(
      "Ilustračné záhradné prostredie",
      "/assets/environment/overcast-garden.jpg",
      { resolution: 32, size: 170, useDirectMapping: false },
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
    this.scene.imageProcessingConfiguration.contrast = 1.13;
    this.scene.imageProcessingConfiguration.vignetteEnabled = true;
    this.scene.imageProcessingConfiguration.vignetteWeight = 1.16;
    this.scene.imageProcessingConfiguration.vignetteColor =
      Color4.FromHexString("#42504b32");

    this.camera = new ArcRotateCamera(
      "architect-camera",
      GARDEN_CAMERA_ALPHA,
      GARDEN_CAMERA_BETA,
      canvas.clientWidth < 600 ? 62 : 42,
      new Vector3(2.5, 1.4, -1.5),
      this.scene,
    );
    this.camera.lowerRadiusLimit = 7;
    this.camera.upperRadiusLimit = 86;
    this.camera.lowerBetaLimit = 0.06;
    this.camera.upperBetaLimit = Math.PI / 2.02;
    this.camera.wheelPrecision = 38;
    this.camera.panningSensibility = 95;
    this.camera.pinchPrecision = 72;
    this.camera.inertia = 0.72;
    this.camera.fov = canvas.clientWidth < 600 ? 0.72 : 0.62;
    this.camera.attachControl(canvas, true);

    const ambient = new HemisphericLight(
      "ambient-light",
      new Vector3(0.3, 1, 0.08),
      this.scene,
    );
    ambient.intensity = 0.84;
    ambient.diffuse = Color3.FromHexString("#eef5f2");
    ambient.groundColor = Color3.FromHexString("#61705f");
    const sun = new DirectionalLight(
      "architectural-sun",
      new Vector3(-0.56, -1, 0.34),
      this.scene,
    );
    sun.position = new Vector3(28, 42, -24);
    sun.intensity = 3.15;
    sun.diffuse = Color3.FromHexString("#fff4dc");
    sun.specular = Color3.FromHexString("#fff8e9");
    this.shadowGenerator = new ShadowGenerator(
      canvas.clientWidth < 700 ? 1024 : 2048,
      sun,
    );
    this.shadowGenerator.usePercentageCloserFiltering = true;
    this.shadowGenerator.filteringQuality = ShadowGenerator.QUALITY_MEDIUM;
    this.shadowGenerator.bias = 0.0005;
    this.shadowGenerator.normalBias = 0.018;
    this.shadowGenerator.setDarkness(0.28);

    const highQuality =
      canvas.clientWidth >= 760 && !window.matchMedia("(pointer: coarse)").matches;
    const post = new DefaultRenderingPipeline(
      "architectural-photo-pipeline",
      true,
      this.scene,
      [this.camera],
    );
    post.samples = highQuality
      ? Math.max(1, Math.min(4, this.engine.getCaps().maxMSAASamples))
      : 1;
    post.fxaaEnabled = !highQuality;
    post.bloomEnabled = false;
    post.imageProcessingEnabled = true;

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
      selection: surfaceMaterial(this.scene, "selection", "#ff5738", 0.55, 0.82),
    };
    this.materials.parcel.disableDepthWrite = true;
    this.materials.selection.emissiveColor = Color3.FromHexString("#58180f");

    this.realisticMaterials = {
      terrain: pbrMaterial(this.scene, "real-terrain", "#697f61", 0.98),
      grass: pbrMaterial(this.scene, "real-grass", "#668a55", 0.94),
      grassLight: pbrMaterial(this.scene, "real-grass-light", "#82a867", 0.94),
      grassDark: pbrMaterial(this.scene, "real-grass-dark", "#456d43", 0.96),
      road: pbrMaterial(this.scene, "real-road", "#606768", 0.92),
      paving: pbrMaterial(this.scene, "real-paving", "#a5a9a4", 0.84),
      timber: pbrMaterial(this.scene, "real-timber", "#a46b38", 0.72),
      timberDark: pbrMaterial(this.scene, "real-timber-dark", "#70401f", 0.8),
      deck: pbrMaterial(this.scene, "real-deck", "#ad7a4e", 0.76),
      wall: pbrMaterial(this.scene, "real-wall", "#f3f0e6", 0.86),
      roof: pbrMaterial(this.scene, "real-roof", "#242a2c", 0.32, 0.68),
      roofEdge: pbrMaterial(this.scene, "real-roof-edge", "#161b1d", 0.28, 0.76),
      glass: pbrMaterial(this.scene, "real-glass", "#20363c", 0.12, 0.18, 0.9),
      glassFrame: pbrMaterial(this.scene, "real-glass-frame", "#171d1f", 0.25, 0.76),
      solar: pbrMaterial(this.scene, "real-solar", "#102b3d", 0.18, 0.54),
      solarGrid: pbrMaterial(this.scene, "real-solar-grid", "#b6c2c5", 0.22, 0.76),
      foliage: pbrMaterial(this.scene, "real-foliage", "#3f713e", 0.92),
      foliageLight: pbrMaterial(this.scene, "real-foliage-light", "#668f49", 0.94),
      trunk: pbrMaterial(this.scene, "real-trunk", "#66513a", 0.95),
      flower: pbrMaterial(this.scene, "real-flower", "#e9d8c9", 0.82),
      flowerPurple: pbrMaterial(this.scene, "real-flower-purple", "#75597f", 0.84),
      stone: pbrMaterial(this.scene, "real-stone", "#d2cec2", 0.9),
      fabric: pbrMaterial(this.scene, "real-fabric", "#d8d2c5", 0.96),
      interiorDark: pbrMaterial(this.scene, "real-interior-dark", "#172324", 0.7),
      warmInterior: pbrMaterial(this.scene, "real-interior", "#d5a76a", 0.82),
    };
    this.realisticMaterials.glass.indexOfRefraction = 1.5;
    this.realisticMaterials.glass.metallicF0Factor = 0.55;
    this.realisticMaterials.warmInterior.emissiveColor =
      Color3.FromHexString("#624524");
    const lawnTexture = new Texture(
      "/assets/textures/lawn-albedo.jpg",
      this.scene,
      false,
      false,
      Texture.TRILINEAR_SAMPLINGMODE,
    );
    lawnTexture.uScale = 12;
    lawnTexture.vScale = 10;
    lawnTexture.anisotropicFilteringLevel = 8;
    this.realisticMaterials.grass.albedoTexture = lawnTexture;
    const terrainLawnTexture = lawnTexture.clone();
    terrainLawnTexture.uScale = 48;
    terrainLawnTexture.vScale = 42;
    this.realisticMaterials.terrain.albedoTexture = terrainLawnTexture;

    for (const layer of LAYERS) this.layerMeshes.set(layer.id, []);
    this.buildTerrainAndGrid();
    this.buildCadastre();
    this.buildStreetAndSite();
    this.buildHouse();
    this.buildLandscape();
    this.buildUtilities();

    this.scene.onPointerDown = (_, pick) => {
      const id = pick?.pickedMesh?.metadata?.entityId;
      if (typeof id === "string") this.onSelect(id);
    };

    const render = () => this.scene.render();
    this.engine.runRenderLoop(render);
    this.onVisibilityChange = () => {
      if (document.hidden) this.engine.stopRenderLoop(render);
      else this.engine.runRenderLoop(render);
    };
    document.addEventListener("visibilitychange", this.onVisibilityChange);
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
      this.appearance(curb, this.materials.paving, this.realisticMaterials.paving);
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
      "Navrhnutá drevená terasa · 53 m²",
      SITE_SURFACES.timberTerrace.polygonMm,
      0.035,
    );
    this.appearance(deck, this.materials.timber, this.realisticMaterials.timber);
    deck.receiveShadows = true;
    this.technicalOverlay(deck);
    this.register(deck, "street", SITE_SURFACES.timberTerrace.id);

    for (const surface of [SITE_SURFACES.driveway, SITE_SURFACES.entry, SITE_SURFACES.binPad]) {
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
      this.appearance(body, this.materials.wall, this.realisticMaterials.wall);
      body.receiveShadows = true;
      this.castShadow(body);
      body.enableEdgesRendering();
      body.edgesColor = Color4.FromHexString("#f5f2e95a");
      body.edgesWidth = 0.8;
      this.register(body, "building", HOUSE.id);
    }

    this.buildGables();

    const slopeLength = HOUSE.roof.mainSlopeLengthMm * MM_TO_M;
    const pitch = (HOUSE.roofPitchDeg * Math.PI) / 180;
    let solarRoof: Mesh | null = null;
    for (const side of [-1, 1]) {
      const panel = CreateBox(
        `Strecha hlavného traktu ${side}`,
        {
          width: HOUSE.roof.mainPlanLengthMm * MM_TO_M,
          depth: slopeLength,
          height: 0.14,
        },
        this.scene,
      );
      panel.position.set(
        xM(HOUSE.originMm.x + HOUSE.lowerBar.widthMm / 2),
        (HOUSE.eavesElevationMm + 1217.5) * MM_TO_M,
        zM(HOUSE.originMm.y + HOUSE.lowerBar.depthMm / 2 + side * 2050),
      );
      panel.rotation.x = -side * pitch;
      this.appearance(panel, this.materials.roof, this.realisticMaterials.roof);
      panel.receiveShadows = true;
      this.castShadow(panel);
      panel.enableEdgesRendering();
      panel.edgesColor = Color4.FromHexString("#aeb8bb66");
      this.register(panel, "building", HOUSE.id);
      if (side === -1) solarRoof = panel;

      for (
        let offsetMm = -HOUSE.roof.mainPlanLengthMm / 2 + 360;
        offsetMm < HOUSE.roof.mainPlanLengthMm / 2;
        offsetMm += 540
      ) {
        const seam = CreateBox(
          `Falc hlavnej strechy ${side} · ${offsetMm}`,
          { width: 0.026, depth: slopeLength, height: 0.028 },
          this.scene,
        );
        seam.position.copyFrom(panel.position);
        seam.position.x += offsetMm * MM_TO_M;
        seam.position.y += 0.085;
        seam.rotation.x = panel.rotation.x;
        seam.material = this.realisticMaterials.roofEdge;
        seam.isPickable = false;
        this.realisticOnly(seam);
        this.register(seam, "building");
      }
    }

    const wingPitch = (HOUSE.roof.wingPitchDeg * Math.PI) / 180;
    const wingSlopeLength =
      (HOUSE.roof.wingHalfSpanMm * MM_TO_M) / Math.cos(wingPitch);
    for (const side of [-1, 1]) {
      const panel = CreateBox(
        `Strecha krídla ${side}`,
        {
          width: wingSlopeLength,
          depth: HOUSE.roof.wingPlanLengthMm * MM_TO_M,
          height: 0.14,
        },
        this.scene,
      );
      panel.position.set(
        xM(
          HOUSE.originMm.x +
            HOUSE.wing.xMm +
            HOUSE.roof.wingHalfSpanMm +
            side * (HOUSE.roof.wingHalfSpanMm / 2),
        ),
        ((HOUSE.eavesElevationMm + HOUSE.ridgeElevationMm) / 2) * MM_TO_M,
        zM(
          HOUSE.originMm.y +
            HOUSE.wing.yMm +
            HOUSE.roof.wingPlanLengthMm / 2,
        ),
      );
      panel.rotation.z = -side * wingPitch;
      this.appearance(panel, this.materials.roof, this.realisticMaterials.roof);
      panel.receiveShadows = true;
      this.castShadow(panel);
      panel.enableEdgesRendering();
      panel.edgesColor = Color4.FromHexString("#aeb8bb66");
      this.register(panel, "building", HOUSE.id);

      for (
        let offsetMm = -HOUSE.roof.wingPlanLengthMm / 2 + 300;
        offsetMm < HOUSE.roof.wingPlanLengthMm / 2;
        offsetMm += 520
      ) {
        const seam = CreateBox(
          `Falc strechy krídla ${side} · ${offsetMm}`,
          { width: wingSlopeLength, depth: 0.026, height: 0.028 },
          this.scene,
        );
        seam.position.copyFrom(panel.position);
        seam.position.z -= offsetMm * MM_TO_M;
        seam.position.y += 0.085;
        seam.rotation.z = panel.rotation.z;
        seam.material = this.realisticMaterials.roofEdge;
        seam.isPickable = false;
        this.realisticOnly(seam);
        this.register(seam, "building");
      }
    }

    if (solarRoof) this.buildSolarArray(solarRoof);

    this.buildRoofEdges();
    this.buildGardenFacades();

    const openings = [
      [2050, 1250, 1500, 1000],
      [5275, 1250, 1500, 1000],
      [8525, 750, 750, 1750],
      [10700, 800, 1600, 900],
      [13300, 800, 1600, 900],
      [15100, 1250, 2250, 0],
      [18350, 2000, 1600, 900],
    ] as const;
    for (const [offsetX, widthMm, heightMm, sillMm] of openings) {
      this.buildWindowOnZFace(
        `Výplň otvoru ${offsetX}`,
        HOUSE.originMm.x + offsetX + widthMm / 2,
        HOUSE.originMm.y - 42,
        widthMm,
        heightMm,
        sillMm,
      );
    }

    const rightOpenings = [
      [2025, 1000, 1600, 900],
      [3600, 600, 750, 1750],
      [6650, 1000, 2250, 0],
      [9700, 1000, 1600, 900],
    ] as const;
    for (const [offsetY, widthMm, heightMm, sillMm] of rightOpenings) {
      this.buildWindowOnXFace(
        `Bočná výplň otvoru ${offsetY}`,
        HOUSE.originMm.x + HOUSE.lowerBar.widthMm + 42,
        HOUSE.originMm.y + offsetY + widthMm / 2,
        widthMm,
        heightMm,
        sillMm,
      );
    }

    const garageDoor = boxAtPlan(
      this.scene,
      "Garážová brána · 3 300 × 2 400 mm",
      {
        x: HOUSE.originMm.x - 36,
        y: HOUSE.originMm.y + 675 + 1650,
      },
      80,
      3300,
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

    for (let offset = -1.4; offset <= 1.4; offset += 0.28) {
      const joint = boxAtPlan(
        this.scene,
        `Lamela garážovej brány ${offset}`,
        { x: HOUSE.originMm.x - 88, y: HOUSE.originMm.y + 2325 + offset * 1000 },
        42,
        22,
        2.36,
        0.02,
      );
      joint.material = this.realisticMaterials.glassFrame;
      joint.isPickable = false;
      this.realisticOnly(joint);
      this.register(joint, "building");
    }

    for (const [index, center] of [
      { x: HOUSE.originMm.x + 11200, y: HOUSE.originMm.y + 4250 },
      { x: HOUSE.originMm.x + 17750, y: HOUSE.originMm.y + 8700 },
    ].entries()) {
      const chimney = boxAtPlan(
        this.scene,
        `Komín ${index + 1} · +6,160 m`,
        center,
        540,
        540,
        3.16,
        3,
      );
      this.appearance(
        chimney,
        this.materials.roof,
        this.realisticMaterials.solarGrid,
      );
      this.castShadow(chimney);
      chimney.isPickable = false;
      this.register(chimney, "building");
    }
  }

  private buildGables() {
    const eave = HOUSE.eavesElevationMm * MM_TO_M;
    const ridge = HOUSE.ridgeElevationMm * MM_TO_M;
    const mainMidY = HOUSE.originMm.y + HOUSE.lowerBar.depthMm / 2;
    for (const [name, xMm] of [
      ["Garážový štít", HOUSE.originMm.x - 45],
      ["Východný štít", HOUSE.originMm.x + HOUSE.lowerBar.widthMm + 45],
    ] as const) {
      const triangle = createVerticalTriangle(this.scene, name, [
        new Vector3(xM(xMm), eave, zM(HOUSE.originMm.y)),
        new Vector3(
          xM(xMm),
          eave,
          zM(HOUSE.originMm.y + HOUSE.lowerBar.depthMm),
        ),
        new Vector3(xM(xMm), ridge, zM(mainMidY)),
      ]);
      this.appearance(triangle, this.materials.wall, this.realisticMaterials.wall);
      triangle.receiveShadows = true;
      this.castShadow(triangle);
      this.register(triangle, "building", HOUSE.id);
    }

    const wingEndY = HOUSE.originMm.y + HOUSE.maximumDepthMm + 45;
    const wingLeftX = HOUSE.originMm.x + HOUSE.wing.xMm;
    const wingRightX = wingLeftX + HOUSE.wing.widthMm;
    const wingGable = createVerticalTriangle(this.scene, "Drevený záhradný štít", [
      new Vector3(xM(wingLeftX), eave, zM(wingEndY)),
      new Vector3(xM(wingRightX), eave, zM(wingEndY)),
      new Vector3(xM((wingLeftX + wingRightX) / 2), ridge, zM(wingEndY)),
    ]);
    this.appearance(
      wingGable,
      this.materials.wall,
      this.realisticMaterials.timber,
    );
    this.castShadow(wingGable);
    this.register(wingGable, "building", HOUSE.id);

    const wingMidX = (wingLeftX + wingRightX) / 2;
    const gableRise = ridge - eave;
    for (let xMm = wingLeftX + 180; xMm < wingRightX; xMm += 280) {
      const normalizedDistance =
        Math.abs(xMm - wingMidX) / (HOUSE.wing.widthMm / 2);
      const battenHeight = Math.max(
        0.08,
        gableRise * (1 - normalizedDistance),
      );
      const batten = boxAtPlan(
        this.scene,
        `Zvislá lamela záhradného štítu ${xMm}`,
        { x: xMm, y: wingEndY + 18 },
        18,
        42,
        battenHeight,
        eave,
      );
      batten.material = this.realisticMaterials.timberDark;
      batten.isPickable = false;
      this.realisticOnly(batten);
      this.register(batten, "building");
    }

    const halfSpanM = (HOUSE.wing.widthMm * MM_TO_M) / 2;
    const gableEdgeLength = Math.hypot(halfSpanM, gableRise);
    const edgeAngle = Math.atan2(gableRise, halfSpanM);
    for (const side of [-1, 1]) {
      const edge = CreateBox(
        `Biely rám záhradného štítu ${side}`,
        { width: gableEdgeLength, depth: 0.1, height: 0.09 },
        this.scene,
      );
      edge.position.set(
        xM(wingMidX + side * HOUSE.wing.widthMm / 4),
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

  private buildRoofEdges() {
    const specs = [
      {
        name: "Predná odkvapová hrana",
        center: {
          x: HOUSE.originMm.x + HOUSE.lowerBar.widthMm / 2,
          y: HOUSE.originMm.y - 130,
        },
        widthMm: HOUSE.lowerBar.widthMm + 260,
        depthMm: 105,
      },
      {
        name: "Záhradná odkvapová hrana",
        center: {
          x: HOUSE.originMm.x + HOUSE.lowerBar.widthMm / 2,
          y: HOUSE.originMm.y + HOUSE.lowerBar.depthMm + 130,
        },
        widthMm: HOUSE.lowerBar.widthMm + 260,
        depthMm: 105,
      },
    ];
    for (const spec of specs) {
      const edge = boxAtPlan(
        this.scene,
        spec.name,
        spec.center,
        spec.widthMm,
        spec.depthMm,
        0.13,
        3.02,
      );
      edge.material = this.realisticMaterials.roofEdge;
      edge.isPickable = false;
      this.realisticOnly(edge);
      this.castShadow(edge);
      this.register(edge, "building");
    }
  }

  private buildSolarArray(roof: Mesh) {
    const rows = 2;
    const columns = HOUSE.photovoltaics.moduleCount / rows;
    for (let column = 0; column < columns; column += 1) {
      for (let row = 0; row < rows; row += 1) {
        const panel = CreateBox(
          `Fotovoltický panel ${column + 1}.${row + 1} · vizualizačná referencia`,
          { width: 1.02, depth: 1.72, height: 0.045 },
          this.scene,
        );
        panel.parent = roof;
        panel.position.set(1.65 + column * 1.08, 0.12, -0.92 + row * 1.82);
        panel.material = this.realisticMaterials.solar;
        panel.isPickable = false;
        this.realisticOnly(panel);
        this.castShadow(panel);
        this.register(panel, "building");

        const frame = CreateBox(
          `Rám FV ${column + 1}.${row + 1}`,
          { width: 1.06, depth: 1.76, height: 0.018 },
          this.scene,
        );
        frame.parent = roof;
        frame.position.set(1.65 + column * 1.08, 0.09, -0.92 + row * 1.82);
        frame.material = this.realisticMaterials.solarGrid;
        frame.isPickable = false;
        this.realisticOnly(frame);
        this.register(frame, "building");
      }
    }
  }

  private buildGardenFacades() {
    const gardenFacade = HOUSE.facades.garden;
    const wingEnd = HOUSE.facades.wingEnd;
    this.buildCladdingOnZFace(
      "Drevený obklad dennej zóny",
      HOUSE.originMm.x,
      HOUSE.originMm.x + HOUSE.wing.xMm,
      gardenFacade.faceYmm + 48,
    );
    this.buildCladdingOnZFace(
      "Drevený obklad koncového štítu",
      wingEnd.startXmm,
      wingEnd.startXmm + wingEnd.widthMm,
      wingEnd.faceYmm + 48,
    );

    for (const opening of gardenFacade.openings) {
      this.buildWindowOnZFace(
        `Terasové presklenie ${opening.widthMm} · D1.1.002`,
        opening.startXmm + opening.widthMm / 2,
        gardenFacade.faceYmm + 66,
        opening.widthMm,
        opening.heightMm,
        opening.sillMm,
      );
    }

    this.buildWindowOnZFace(
      "Severné terasové presklenie 2 400 · D1.1.002",
      wingEnd.opening.startXmm + wingEnd.opening.widthMm / 2,
      wingEnd.faceYmm + 66,
      wingEnd.opening.widthMm,
      wingEnd.opening.heightMm,
      wingEnd.opening.sillMm,
    );
  }

  private buildCladdingOnZFace(
    name: string,
    startXmm: number,
    endXmm: number,
    yMm: number,
  ) {
    const panel = boxAtPlan(
      this.scene,
      name,
      { x: (startXmm + endXmm) / 2, y: yMm },
      endXmm - startXmm,
      96,
      2.84,
      0.08,
    );
    panel.material = this.realisticMaterials.timber;
    panel.isPickable = false;
    this.realisticOnly(panel);
    this.castShadow(panel);
    this.register(panel, "building");
    for (let xMm = startXmm + 130; xMm < endXmm; xMm += 255) {
      const seam = boxAtPlan(
        this.scene,
        `${name} · škára ${xMm}`,
        { x: xMm, y: yMm + 55 },
        16,
        25,
        2.82,
        0.09,
      );
      seam.material = this.realisticMaterials.timberDark;
      seam.isPickable = false;
      this.realisticOnly(seam);
      this.register(seam, "building");
    }
  }

  private buildWindowOnZFace(
    name: string,
    centerXmm: number,
    yMm: number,
    widthMm: number,
    heightMm: number,
    sillMm: number,
  ) {
    const opening = boxAtPlan(
      this.scene,
      name,
      { x: centerXmm, y: yMm },
      widthMm,
      92,
      heightMm * MM_TO_M,
      sillMm * MM_TO_M,
    );
    this.appearance(opening, this.materials.glass, this.realisticMaterials.glass);
    opening.isPickable = false;
    this.register(opening, "building");
    this.buildWindowFrameZ(name, centerXmm, yMm + 54, widthMm, heightMm, sillMm);
  }

  private buildWindowFrameZ(
    name: string,
    centerXmm: number,
    yMm: number,
    widthMm: number,
    heightMm: number,
    sillMm: number,
  ) {
    const frame = 58;
    const horizontal = [sillMm, sillMm + heightMm];
    const vertical = [centerXmm - widthMm / 2, centerXmm + widthMm / 2];
    if (widthMm >= 1800) vertical.push(centerXmm);
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
      bar.material = this.realisticMaterials.glassFrame;
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
      bar.material = this.realisticMaterials.glassFrame;
      bar.isPickable = false;
      this.realisticOnly(bar);
      this.register(bar, "building");
    }
  }

  private buildWindowOnXFace(
    name: string,
    xMm: number,
    centerYmm: number,
    widthMm: number,
    heightMm: number,
    sillMm: number,
  ) {
    const opening = boxAtPlan(
      this.scene,
      name,
      { x: xMm, y: centerYmm },
      92,
      widthMm,
      heightMm * MM_TO_M,
      sillMm * MM_TO_M,
    );
    this.appearance(opening, this.materials.glass, this.realisticMaterials.glass);
    opening.isPickable = false;
    this.register(opening, "building");

    const frame = 58;
    const horizontal = [sillMm, sillMm + heightMm];
    const vertical = [centerYmm - widthMm / 2, centerYmm + widthMm / 2];
    if (widthMm >= 1800) vertical.push(centerYmm);
    for (const yMm of vertical) {
      const bar = boxAtPlan(
        this.scene,
        `${name} · rám zvislý`,
        { x: xMm + 54, y: yMm },
        72,
        frame,
        heightMm * MM_TO_M + 0.06,
        sillMm * MM_TO_M - 0.03,
      );
      bar.material = this.realisticMaterials.glassFrame;
      bar.isPickable = false;
      this.realisticOnly(bar);
      this.register(bar, "building");
    }
    for (const levelMm of horizontal) {
      const bar = boxAtPlan(
        this.scene,
        `${name} · rám vodorovný`,
        { x: xMm + 54, y: centerYmm },
        72,
        widthMm + frame,
        0.058,
        levelMm * MM_TO_M - 0.029,
      );
      bar.material = this.realisticMaterials.glassFrame;
      bar.isPickable = false;
      this.realisticOnly(bar);
      this.register(bar, "building");
    }
  }

  private buildLandscape() {
    const deckZones = [
      {
        name: "Terasa D1 · záhradná časť · vizualizačný rozsah",
        center: { x: 13740, y: 12850 },
        widthMm: 14100,
        depthMm: 3300,
      },
      {
        name: "Terasa D1 · vnútorné rameno · vizualizačný rozsah",
        center: { x: 19540, y: 17750 },
        widthMm: 3000,
        depthMm: 6500,
      },
      {
        name: "Terasa D1 · koncová časť 16,45 m²",
        center: { x: 24540, y: 23210 },
        widthMm: 7000,
        depthMm: 2350,
      },
    ] as const;
    for (const zone of deckZones) {
      const deck = boxAtPlan(
        this.scene,
        zone.name,
        zone.center,
        zone.widthMm,
        zone.depthMm,
        0.075,
        0.012,
      );
      deck.material = this.realisticMaterials.deck;
      deck.receiveShadows = true;
      deck.isPickable = false;
      this.realisticOnly(deck);
      this.register(deck, "street");

      for (
        let offsetMm = -zone.widthMm / 2 + 160;
        offsetMm < zone.widthMm / 2;
        offsetMm += 185
      ) {
        const joint = boxAtPlan(
          this.scene,
          `${zone.name} · škára ${offsetMm}`,
          { x: zone.center.x + offsetMm, y: zone.center.y },
          10,
          zone.depthMm - 70,
          0.014,
          0.088,
        );
        joint.material = this.realisticMaterials.timberDark;
        joint.isPickable = false;
        this.realisticOnly(joint);
        this.register(joint, "street");
      }
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

    const treeSpecs = [
      { x: -3200, y: 7600, h: 4.2, crown: 3.1 },
      { x: -2200, y: 18000, h: 3.8, crown: 2.8 },
      { x: 33000, y: 6800, h: 4.5, crown: 3.2 },
      { x: 36000, y: 5000, h: 3.9, crown: 2.9 },
    ] as const;
    for (const [index, tree] of treeSpecs.entries()) {
      this.buildTree(`Strom ${index + 1} · ilustračný záhradný koncept`, tree);
    }

    const shrubs = [
      { x: 5200, y: 15400, s: 1.2 },
      { x: 6900, y: 16000, s: 1.0 },
      { x: 8700, y: 16400, s: 1.25 },
      { x: 10500, y: 16550, s: 0.92 },
      { x: 12600, y: 16900, s: 1.18 },
      { x: 15000, y: 17500, s: 1.05 },
      { x: 17500, y: 19000, s: 1.3 },
      { x: 19200, y: 21600, s: 1.08 },
      { x: 28600, y: 18800, s: 1.25 },
      { x: 29400, y: 20500, s: 0.94 },
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
      { x: 11200, y: 17450, s: 0.94 },
      { x: 14300, y: 18100, s: 1.12 },
      { x: 17800, y: 20500, s: 1.2 },
      { x: 28900, y: 17100, s: 1.08 },
      { x: 29600, y: 22100, s: 1.16 },
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
    for (let bladeIndex = 0; bladeIndex < 9; bladeIndex += 1) {
      const angle = (bladeIndex / 9) * Math.PI * 2;
      const radius = bladeIndex % 3 === 0 ? 0.13 : 0.08;
      const bladeHeight = (0.52 + (bladeIndex % 4) * 0.07) * scale;
      const blade = CreateCylinder(
        `${name} · steblo ${bladeIndex + 1}`,
        {
          height: bladeHeight,
          diameterTop: 0.008,
          diameterBottom: 0.032,
          tessellation: 5,
        },
        this.scene,
      );
      blade.position.set(
        xM(xMm) + Math.cos(angle) * radius,
        bladeHeight / 2,
        zM(yMm) + Math.sin(angle) * radius,
      );
      blade.rotation.x = Math.sin(angle) * 0.18;
      blade.rotation.z = Math.cos(angle) * 0.18;
      blade.material =
        bladeIndex % 3 === 0
          ? this.realisticMaterials.grassLight
          : this.realisticMaterials.grassDark;
      blade.isPickable = false;
      this.realisticOnly(blade);
      this.register(blade, "street");
    }
  }

  private buildTree(
    name: string,
    tree: { x: number; y: number; h: number; crown: number },
  ) {
    const trunk = CreateCylinder(
      `${name} · kmeň`,
      { height: tree.h, diameterTop: 0.18, diameterBottom: 0.34, tessellation: 10 },
      this.scene,
    );
    trunk.position.set(xM(tree.x), tree.h / 2 - 0.04, zM(tree.y));
    trunk.material = this.realisticMaterials.trunk;
    trunk.isPickable = false;
    this.realisticOnly(trunk);
    this.castShadow(trunk);
    this.register(trunk, "street");

    const crownOffsets = [
      { x: 0, y: 0, z: 0, scale: 1 },
      { x: -0.55, y: -0.25, z: 0.25, scale: 0.72 },
      { x: 0.58, y: -0.12, z: -0.18, scale: 0.76 },
    ] as const;
    for (const [index, offset] of crownOffsets.entries()) {
      const crown = CreateSphere(
        `${name} · koruna ${index + 1}`,
        { diameter: tree.crown * offset.scale, segments: 10 },
        this.scene,
      );
      crown.position.set(
        xM(tree.x) + offset.x,
        tree.h + tree.crown * 0.32 + offset.y,
        zM(tree.y) + offset.z,
      );
      crown.scaling.y = 1.16;
      crown.material =
        index === 1
          ? this.realisticMaterials.foliageLight
          : this.realisticMaterials.foliage;
      crown.isPickable = false;
      this.realisticOnly(crown);
      this.castShadow(crown);
      this.register(crown, "street");
    }
  }

  private buildShrub(
    name: string,
    xMm: number,
    yMm: number,
    scale: number,
    variant: number,
  ) {
    const shrub = CreateSphere(
      name,
      { diameter: 0.9 * scale, segments: 9 },
      this.scene,
    );
    shrub.position.set(xM(xMm), 0.34 * scale, zM(yMm));
    shrub.scaling.set(1.18, 0.74, 0.9);
    shrub.material =
      variant % 2 === 0
        ? this.realisticMaterials.foliageLight
        : this.realisticMaterials.foliage;
    shrub.isPickable = false;
    this.realisticOnly(shrub);
    this.castShadow(shrub);
    this.register(shrub, "street");

    for (let petal = 0; petal < 3; petal += 1) {
      const bloom = CreateSphere(
        `${name} · kvet ${petal + 1}`,
        { diameter: 0.13 + scale * 0.025, segments: 6 },
        this.scene,
      );
      bloom.position.set(
        xM(xMm) + (petal - 1) * 0.19,
        0.61 * scale + (petal % 2) * 0.08,
        zM(yMm) + (petal === 1 ? -0.17 : 0.09),
      );
      bloom.material =
        variant % 3 === 0
          ? this.realisticMaterials.flowerPurple
          : this.realisticMaterials.flower;
      bloom.isPickable = false;
      this.realisticOnly(bloom);
      this.register(bloom, "street");
    }
  }

  private buildGardenFurniture() {
    const table = CreateCylinder(
      "Terasový stolík · ilustračný koncept",
      { height: 0.08, diameter: 0.88, tessellation: 24 },
      this.scene,
    );
    table.position.set(xM(17900), 0.42, zM(13350));
    table.material = this.realisticMaterials.roofEdge;
    table.isPickable = false;
    this.realisticOnly(table);
    this.castShadow(table);
    this.register(table, "street");
    const leg = CreateCylinder(
      "Noha terasového stolíka",
      { height: 0.42, diameter: 0.12, tessellation: 12 },
      this.scene,
    );
    leg.position.set(xM(17900), 0.2, zM(13350));
    leg.material = this.realisticMaterials.roofEdge;
    leg.isPickable = false;
    this.realisticOnly(leg);
    this.castShadow(leg);
    this.register(leg, "street");

    for (const [index, center] of [
      { x: 16450, y: 13400, r: -0.14 },
      { x: 19050, y: 14000, r: 0.18 },
    ].entries()) {
      const seat = boxAtPlan(
        this.scene,
        `Terasové kreslo ${index + 1} · ilustračný koncept`,
        center,
        950,
        900,
        0.22,
        0.18,
      );
      seat.rotation.y = center.r;
      seat.material = this.realisticMaterials.fabric;
      seat.isPickable = false;
      this.realisticOnly(seat);
      this.castShadow(seat);
      this.register(seat, "street");
      const back = boxAtPlan(
        this.scene,
        `Operadlo kresla ${index + 1}`,
        { x: center.x, y: center.y + 360 },
        950,
        140,
        0.62,
        0.34,
      );
      back.rotation.y = center.r;
      back.material = this.realisticMaterials.fabric;
      back.isPickable = false;
      this.realisticOnly(back);
      this.castShadow(back);
      this.register(back, "street");
    }
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
      realistic ? "#b8c9c6ff" : "#101313ff",
    );
    this.scene.imageProcessingConfiguration.exposure = realistic ? 1.08 : 1;
    this.scene.imageProcessingConfiguration.contrast = realistic ? 1.13 : 1.04;
    this.scene.imageProcessingConfiguration.vignetteEnabled = realistic;
    this.scene.fogMode = realistic ? Scene.FOGMODE_EXP2 : Scene.FOGMODE_NONE;
    this.scene.fogDensity = 0.0032;
    this.scene.fogColor = Color3.FromHexString("#b8c9c6");

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
    if (preset === "garden") {
      this.camera.alpha = GARDEN_CAMERA_ALPHA;
      this.camera.beta = GARDEN_CAMERA_BETA;
      this.camera.radius = this.canvas.clientWidth < 600 ? 62 : 42;
      this.camera.fov = this.canvas.clientWidth < 600 ? 0.72 : 0.62;
      this.camera.target.set(2.5, 1.4, -1.5);
      return;
    }
    if (preset === "top") {
      this.camera.alpha = TOP_CAMERA_ALPHA;
      this.camera.beta = 0.065;
      this.camera.radius = this.canvas.clientWidth < 600 ? 56 : 44;
      this.camera.fov = 0.72;
      this.camera.target.set(0, 0, 0.5);
      return;
    }
    if (preset === "street") {
      this.camera.alpha = STREET_CAMERA_ALPHA;
      this.camera.beta = Math.PI * 0.39;
      this.camera.radius = this.canvas.clientWidth < 600 ? 43 : 31;
      this.camera.fov = 0.68;
      this.camera.target.set(-1, 1.4, 4.8);
      return;
    }
    if (preset === "focus") {
      const meshes = this.snapshot?.selectionId
        ? this.entityMeshes.get(this.snapshot.selectionId)
        : undefined;
      const mesh = meshes?.find((candidate) => candidate.isEnabled());
      if (mesh) {
        this.camera.target.copyFrom(mesh.getBoundingInfo().boundingBox.centerWorld);
        const extent = mesh.getBoundingInfo().boundingBox.extendSizeWorld.length();
        this.camera.radius = Math.max(7, Math.min(35, extent * 3.2));
      }
      return;
    }
    this.camera.alpha = AXONOMETRIC_CAMERA_ALPHA;
    this.camera.beta = Math.PI * 0.34;
    this.camera.radius = this.canvas.clientWidth < 600 ? 58 : 42;
    this.camera.fov = 0.72;
    this.camera.target.set(0, 1.25, 0.5);
  }

  resize() {
    this.engine.resize();
  }

  dispose() {
    document.removeEventListener("visibilitychange", this.onVisibilityChange);
    this.clearSelection();
    this.scene.dispose();
    this.engine.dispose();
  }
}

export function createTwinScene(
  canvas: HTMLCanvasElement,
  onSelect: (id: string) => void,
) {
  return new TwinSceneController(canvas, onSelect);
}
