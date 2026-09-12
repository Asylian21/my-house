import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { Texture } from "@babylonjs/core/Materials/Textures/texture";
import { Color3 } from "@babylonjs/core/Maths/math.color";
import { Quaternion, Vector3, Vector4 } from "@babylonjs/core/Maths/math.vector";
import { PointLight } from "@babylonjs/core/Lights/pointLight";
import { KITCHEN_TASK_LIGHT } from "./twin-interior-lighting";
import { createKitchenTaskLight } from "./babylon-interior-lighting";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { CreatePlane } from "@babylonjs/core/Meshes/Builders/planeBuilder.pure";
import { CreateBox } from "@babylonjs/core/Meshes/Builders/boxBuilder.pure";
import { CreateCapsule } from "@babylonjs/core/Meshes/Builders/capsuleBuilder.pure";
import { CreateCylinder } from "@babylonjs/core/Meshes/Builders/cylinderBuilder.pure";
import { ExtrudePolygon } from "@babylonjs/core/Meshes/Builders/polygonBuilder.pure";
import { CreateSphere } from "@babylonjs/core/Meshes/Builders/sphereBuilder.pure";
import { CreateTorus } from "@babylonjs/core/Meshes/Builders/torusBuilder.pure";
import { CreateTube } from "@babylonjs/core/Meshes/Builders/tubeBuilder.pure";
import { Mesh } from "@babylonjs/core/Meshes/mesh";
import { VertexData } from "@babylonjs/core/Meshes/mesh.vertexData";
import { TransformNode } from "@babylonjs/core/Meshes/transformNode";
import type { Scene } from "@babylonjs/core/scene";
import earcut from "earcut";
import { warmLivingMaterial } from "./babylon-living-palette";

import {
  BATHROOM_FITOUT,
  BEDROOM_FITOUT,
  CHILDRENS_BEDROOM_FITOUTS,
  ENSUITE_BATHROOM_FITOUT,
  ENTRY_FITOUT,
  FIREPLACE_STOVE,
  GARAGE_FITOUT,
  HALLWAY_BUILT_IN_WARDROBES,
  INTERIOR_DOORS,
  INTERIOR_ROOMS,
  INTERIOR_RENDER_WALLS,
  INTERIOR_WALLS,
  INTERIOR_WALL_HEIGHT_MM,
  KITCHEN_BEARING_WALL,
  KITCHEN_BEARING_WALL_EAST,
  KITCHEN_RUN,
  OFFICE_FITOUT,
  WC_FITOUT,
  WING_RIDGE_XMM,
  ceilingElevationMm,
  roomBoundsMm,
  type ChildBedroomFitout,
  type FireplaceStove,
  type FurnitureFacing,
  type HallwayBuiltInWardrobe,
  type InteriorDoor,
  type InteriorRoom,
  type RectMm,
} from "./twin-interior";
import {
  DEFAULT_LIVING_LAYOUT_ID,
  LIVING_LAYOUTS,
  type LivingLayout,
  type LivingLayoutId,
} from "./twin-living-layouts";
import { DEFAULT_HEATING_LAYOUT_ID, HEATING_LAYOUTS, type HeatingLayoutId, type TechnicalHeatingFitout } from "./technical-design";
import { type LayerId, type Point2Mm } from "./twin-site";
import { HOUSE } from "./twin-active-house";
import { MM_TO_M, sceneXM as xM, sceneZM as zM } from "./twin-render-frame";
import {
  hingedDoorActorDisplacement,
  hingedDoorSweepIsClear,
  slidingDoorActorDisplacement,
  slidingDoorPathIsClear,
  type AnimatedDoorRegistration,
} from "./babylon-doors";
import type { WalkSurfaceKind } from "./twin-viewport-contract";
import type { WalkPassage } from "./twin-walk-assist";

export interface InteriorBuildContext {
  readonly scene: Scene;
  readonly anisotropy: number;
  readonly wall: PBRMaterial;
  readonly soffit: PBRMaterial;
  readonly glassFrame: PBRMaterial;
  readonly chimneyMetal: PBRMaterial;
  readonly timber: PBRMaterial;
  register(mesh: AbstractMesh, layer: LayerId, entityId?: string): AbstractMesh;
  realisticOnly(mesh: AbstractMesh): AbstractMesh;
  castShadow(mesh: AbstractMesh): AbstractMesh;
  registerAnimatedDoor?(door: AnimatedDoorRegistration): void;
  /** Arrangement of the living/dining zone in 1.03; the active model uses A. */
  readonly livingLayout?: LivingLayoutId;
  readonly heatingLayout?: HeatingLayoutId;
}

export interface InteriorMaterials {
  readonly plaster: PBRMaterial;
  readonly ceiling: PBRMaterial;
  readonly vinyl: PBRMaterial;
  readonly tile: PBRMaterial;
  readonly epoxy: PBRMaterial;
  readonly doorLeaf: PBRMaterial;
  readonly doorFrame: PBRMaterial;
  readonly kitchenFront: PBRMaterial;
  readonly kitchenUpper: PBRMaterial;
  readonly worktop: PBRMaterial;
  readonly steel: PBRMaterial;
  readonly blackGlass: PBRMaterial;
  readonly fireplace: PBRMaterial;
  readonly fireplaceGlass: PBRMaterial;
  readonly fireplaceEmber: PBRMaterial;
  readonly skirting: PBRMaterial;
  readonly wallTile: PBRMaterial;
  readonly livingCabinet: PBRMaterial;
  readonly mediaPanel: PBRMaterial;
  readonly upholstery: PBRMaterial;
  readonly accentFabric: PBRMaterial;
  readonly rug: PBRMaterial;
  readonly brushedBrass: PBRMaterial;
  readonly warmLight: PBRMaterial;
  readonly tvScreen: PBRMaterial;
  readonly boilerEnamel: PBRMaterial;
  readonly pelletFeedHose: PBRMaterial;
  readonly controlDisplay: PBRMaterial;
  readonly tankJacket: PBRMaterial;
  readonly copperPipe: PBRMaterial;
  readonly sanitaryCeramic: PBRMaterial;
  readonly mirrorGlass: PBRMaterial;
  readonly showerGlass: PBRMaterial;
  readonly blackCeramic: PBRMaterial;
  readonly applianceEnamel: PBRMaterial;
  readonly officeFabric: PBRMaterial;
  readonly whiteboardGlass: PBRMaterial;
  readonly bedroomLinen: PBRMaterial;
  readonly bedroomThrow: PBRMaterial;
  readonly wardrobeFront: PBRMaterial;
  readonly hallwayWardrobeOak: PBRMaterial;
  readonly hallwayWardrobeSmokedOak: PBRMaterial;
  readonly childSage: PBRMaterial;
  readonly childClay: PBRMaterial;
  readonly childMidnight: PBRMaterial;
  readonly childSand: PBRMaterial;
  readonly childCork: PBRMaterial;
}

const HOUSE_ENTITY = HOUSE.id;
const FLOOR_TOP_M = 0.0;
const VAULT_RIDGE_MM = 4850;

function texture(
  scene: Scene,
  name: string,
  anisotropy: number,
  gamma = true,
) {
  const result = new Texture(
    `/assets/textures/${name}.jpg`,
    scene,
    false,
    false,
    Texture.TRILINEAR_SAMPLINGMODE,
  );
  result.anisotropicFilteringLevel = anisotropy;
  if (!gamma) result.gammaSpace = false;
  return result;
}

function pbr(scene: Scene, name: string, color: string, roughness: number, metallic = 0) {
  const material = new PBRMaterial(name, scene);
  material.albedoColor = Color3.FromHexString(color);
  material.roughness = roughness;
  material.metallic = metallic;
  material.backFaceCulling = true;
  material.environmentIntensity = 1;
  return material;
}

function texturedPbr(
  scene: Scene,
  name: string,
  albedo: string,
  normal: string,
  anisotropy: number,
  roughness: number,
  bumpLevel: number,
  tint = "#ffffff",
) {
  const material = pbr(scene, name, tint, roughness);
  material.albedoTexture = texture(scene, albedo, anisotropy);
  const bump = texture(scene, normal, anisotropy, false);
  bump.level = bumpLevel;
  material.bumpTexture = bump;
  material.forceIrradianceInFragment = true;
  return material;
}

export function createInteriorMaterials(context: InteriorBuildContext): InteriorMaterials {
  const { scene, anisotropy } = context;
  const plaster = texturedPbr(
    scene,
    "real-interior-plaster",
    "plaster-white-albedo",
    "plaster-white-normal",
    anisotropy,
    0.96,
    0.22,
    "#f3f1ec",
  );
  const ceiling = pbr(scene, "real-interior-ceiling", "#f6f5f1", 0.97);
  // The underside of a ceiling only ever sees the ground half of the IBL,
  // which would tint it brown; a matte self-light keeps the SDK white.
  ceiling.environmentIntensity = 0.35;
  ceiling.emissiveColor = Color3.FromHexString("#9a9995");
  const vinyl = texturedPbr(
    scene,
    "real-interior-vinyl-oak",
    "vinyl-oak-albedo",
    "vinyl-oak-normal",
    anisotropy,
    0.58,
    0.35,
    "#f2e9dc",
  );
  const tile = texturedPbr(
    scene,
    "real-interior-tile",
    "tile-porcelain-albedo",
    "tile-porcelain-normal",
    anisotropy,
    0.34,
    0.45,
  );
  const epoxy = texturedPbr(
    scene,
    "real-interior-epoxy",
    "epoxy-grey-albedo",
    "epoxy-grey-normal",
    anisotropy,
    0.26,
    0.2,
  );
  const doorLeaf = pbr(scene, "real-interior-door-leaf", "#f4f3ef", 0.52);
  const doorFrame = pbr(scene, "real-interior-door-frame", "#ecebe6", 0.6);
  const kitchenFront = texturedPbr(
    scene,
    "real-interior-kitchen-front",
    "oak-veneer-albedo",
    "oak-veneer-normal",
    anisotropy,
    0.55,
    0.3,
    "#f3ebdf",
  );
  const kitchenUpper = pbr(scene, "real-interior-kitchen-upper", "#eeece6", 0.38);
  const worktop = texturedPbr(
    scene,
    "real-interior-worktop",
    "stone-dark-albedo",
    "stone-dark-normal",
    anisotropy,
    0.22,
    0.3,
  );
  const steel = pbr(scene, "real-interior-steel", "#c9cdd0", 0.28, 0.9);
  const blackGlass = pbr(scene, "real-interior-black-glass", "#0c0e10", 0.08, 0.1);
  blackGlass.clearCoat.isEnabled = true;
  blackGlass.clearCoat.intensity = 0.8;
  blackGlass.clearCoat.roughness = 0.05;
  const fireplace = pbr(scene, "real-interior-fireplace", "#1d2022", 0.48, 0.2);
  const fireplaceGlass = pbr(scene, "real-interior-fireplace-glass", "#211812", 0.06, 0.08);
  fireplaceGlass.alpha = 0.38;
  fireplaceGlass.transparencyMode = PBRMaterial.PBRMATERIAL_ALPHABLEND;
  fireplaceGlass.needDepthPrePass = true;
  fireplaceGlass.separateCullingPass = true;
  fireplaceGlass.useSpecularOverAlpha = true;
  fireplaceGlass.indexOfRefraction = 1.5;
  fireplaceGlass.clearCoat.isEnabled = true;
  fireplaceGlass.clearCoat.intensity = 1;
  fireplaceGlass.clearCoat.roughness = 0.025;
  const fireplaceEmber = pbr(scene, "real-interior-fireplace-ember", "#f06b22", 0.4);
  fireplaceEmber.emissiveColor = Color3.FromHexString("#ff7f2a");
  fireplaceEmber.environmentIntensity = 0.18;
  const skirting = pbr(scene, "real-interior-skirting", "#f7f6f2", 0.6);
  const wallTile = texturedPbr(
    scene,
    "real-interior-wall-tile",
    "tile-wall-albedo",
    "tile-wall-normal",
    anisotropy,
    0.28,
    0.4,
  );
  const livingCabinet = pbr(scene, "real-interior-living-cabinet", "#91867a", 0.42);
  const mediaPanel = pbr(scene, "real-interior-media-stone", "#57524d", 0.34);
  const upholstery = texturedPbr(
    scene,
    "real-interior-upholstery",
    "boucle-taupe-albedo",
    "boucle-taupe-normal",
    anisotropy,
    0.9,
    0.48,
  );
  upholstery.sheen.isEnabled = true;
  upholstery.sheen.intensity = 0.28;
  upholstery.sheen.color = Color3.FromHexString("#c2b7aa");
  upholstery.sheen.roughness = 0.86;
  const accentFabric = pbr(scene, "real-interior-accent-fabric", "#4f392f", 0.9);
  accentFabric.sheen.isEnabled = true;
  accentFabric.sheen.intensity = 0.18;
  const rug = texturedPbr(
    scene,
    "real-interior-rug",
    "rug-wool-taupe-albedo",
    "rug-wool-taupe-normal",
    anisotropy,
    0.97,
    0.42,
  );
  const brushedBrass = pbr(scene, "real-interior-brushed-brass", "#a77d4d", 0.3, 0.78);
  const warmLight = pbr(scene, "real-interior-warm-light", "#fff0d8", 0.2);
  warmLight.emissiveColor = Color3.FromHexString("#ffbd78");
  warmLight.environmentIntensity = 0.25;
  const tvScreen = pbr(scene, "real-interior-tv-screen", "#020507", 0.035, 0.08);
  tvScreen.emissiveColor = Color3.FromHexString("#061119");
  tvScreen.clearCoat.isEnabled = true;
  tvScreen.clearCoat.intensity = 1;
  tvScreen.clearCoat.roughness = 0.025;
  const boilerEnamel = pbr(scene, "real-technical-boiler-enamel", "#b7bdc2", 0.32, 0.28);
  boilerEnamel.clearCoat.isEnabled = true;
  boilerEnamel.clearCoat.intensity = 0.42;
  boilerEnamel.clearCoat.roughness = 0.2;
  const pelletFeedHose = pbr(scene, "real-technical-pellet-feed-hose", "#a47745", 0.24, 0.18);
  pelletFeedHose.alpha = 0.62;
  pelletFeedHose.transparencyMode = PBRMaterial.PBRMATERIAL_ALPHABLEND;
  pelletFeedHose.needDepthPrePass = true;
  pelletFeedHose.clearCoat.isEnabled = true;
  pelletFeedHose.clearCoat.intensity = 0.58;
  pelletFeedHose.clearCoat.roughness = 0.15;
  const controlDisplay = pbr(scene, "real-technical-control-display", "#1c6178", 0.12, 0.08);
  controlDisplay.emissiveColor = Color3.FromHexString("#39bce5");
  controlDisplay.environmentIntensity = 0.18;
  controlDisplay.clearCoat.isEnabled = true;
  controlDisplay.clearCoat.intensity = 0.9;
  controlDisplay.clearCoat.roughness = 0.04;
  const tankJacket = pbr(scene, "real-technical-buffer-jacket", "#8b9092", 0.46, 0.2);
  const copperPipe = pbr(scene, "real-technical-copper", "#b96f43", 0.24, 0.82);
  const sanitaryCeramic = pbr(scene, "real-sanitary-ceramic", "#f8f8f5", 0.16, 0.02);
  sanitaryCeramic.clearCoat.isEnabled = true;
  sanitaryCeramic.clearCoat.intensity = 0.78;
  sanitaryCeramic.clearCoat.roughness = 0.08;
  const mirrorGlass = pbr(scene, "real-sanitary-mirror", "#aeb9bd", 0.07, 0.48);
  mirrorGlass.clearCoat.isEnabled = true;
  mirrorGlass.clearCoat.intensity = 1;
  mirrorGlass.clearCoat.roughness = 0.02;
  const showerGlass = pbr(scene, "real-bathroom-shower-glass", "#dbe8e9", 0.06);
  showerGlass.alpha = 0.18;
  showerGlass.transparencyMode = PBRMaterial.PBRMATERIAL_ALPHABLEND;
  showerGlass.needDepthPrePass = true;
  showerGlass.separateCullingPass = true;
  showerGlass.useSpecularOverAlpha = true;
  showerGlass.indexOfRefraction = 1.5;
  showerGlass.clearCoat.isEnabled = true;
  showerGlass.clearCoat.intensity = 0.95;
  showerGlass.clearCoat.roughness = 0.025;
  const blackCeramic = pbr(scene, "real-bathroom-black-ceramic", "#08090a", 0.12, 0.02);
  blackCeramic.clearCoat.isEnabled = true;
  blackCeramic.clearCoat.intensity = 0.78;
  blackCeramic.clearCoat.roughness = 0.06;
  const applianceEnamel = pbr(scene, "real-bathroom-appliance-white", "#fafaf7", 0.25, 0.04);
  applianceEnamel.clearCoat.isEnabled = true;
  applianceEnamel.clearCoat.intensity = 0.45;
  applianceEnamel.clearCoat.roughness = 0.16;
  const officeFabric = pbr(scene, "real-office-chair-fabric", "#17191b", 0.82);
  officeFabric.sheen.isEnabled = true;
  officeFabric.sheen.intensity = 0.22;
  officeFabric.sheen.color = Color3.FromHexString("#4b4e50");
  officeFabric.sheen.roughness = 0.92;
  const whiteboardGlass = pbr(scene, "real-office-whiteboard-glass", "#f7f8f6", 0.18, 0.01);
  whiteboardGlass.clearCoat.isEnabled = true;
  whiteboardGlass.clearCoat.intensity = 0.72;
  whiteboardGlass.clearCoat.roughness = 0.12;
  const bedroomLinen = pbr(scene, "real-bedroom-washed-linen", "#eee9e1", 0.94);
  bedroomLinen.sheen.isEnabled = true;
  bedroomLinen.sheen.intensity = 0.2;
  bedroomLinen.sheen.color = Color3.FromHexString("#faf7f0");
  bedroomLinen.sheen.roughness = 0.92;
  const bedroomThrow = pbr(scene, "real-bedroom-wool-throw", "#847b70", 0.92);
  bedroomThrow.sheen.isEnabled = true;
  bedroomThrow.sheen.intensity = 0.18;
  bedroomThrow.sheen.color = Color3.FromHexString("#b5aa9d");
  bedroomThrow.sheen.roughness = 0.9;
  const wardrobeFront = pbr(scene, "real-bedroom-wardrobe-greige", "#b8afa3", 0.5);
  const hallwayWardrobeOak = texturedPbr(
    scene,
    "real-hallway-wardrobe-warm-oak",
    "oak-veneer-albedo",
    "oak-veneer-normal",
    anisotropy,
    0.43,
    0.38,
    "#c89a70",
  );
  hallwayWardrobeOak.clearCoat.isEnabled = true;
  hallwayWardrobeOak.clearCoat.intensity = 0.12;
  hallwayWardrobeOak.clearCoat.roughness = 0.42;
  const hallwayWardrobeSmokedOak = texturedPbr(
    scene,
    "real-hallway-wardrobe-smoked-oak",
    "oak-veneer-albedo",
    "oak-veneer-normal",
    anisotropy,
    0.5,
    0.42,
    "#75533d",
  );
  const childSage = pbr(scene, "real-child-room-rose", "#c28d91", 0.72);
  childSage.sheen.isEnabled = true;
  childSage.sheen.intensity = 0.12;
  childSage.sheen.color = Color3.FromHexString("#c8d0c5");
  const childClay = pbr(scene, "real-child-room-apricot", "#e2b99c", 0.8);
  childClay.sheen.isEnabled = true;
  childClay.sheen.intensity = 0.16;
  childClay.sheen.color = Color3.FromHexString("#e8b8a3");
  const childMidnight = pbr(scene, "real-child-room-blue", "#4b6c79", 0.58);
  childMidnight.clearCoat.isEnabled = true;
  childMidnight.clearCoat.intensity = 0.12;
  childMidnight.clearCoat.roughness = 0.42;
  const childSand = pbr(scene, "real-child-room-ochre", "#c59e60", 0.86);
  childSand.sheen.isEnabled = true;
  childSand.sheen.intensity = 0.2;
  childSand.sheen.color = Color3.FromHexString("#f1e8da");
  const childCork = pbr(scene, "real-child-room-cork", "#a97852", 0.9);
  return {
    plaster,
    ceiling,
    vinyl,
    tile,
    epoxy,
    doorLeaf,
    doorFrame,
    kitchenFront,
    kitchenUpper,
    worktop,
    steel,
    blackGlass,
    fireplace,
    fireplaceGlass,
    fireplaceEmber,
    skirting,
    wallTile,
    livingCabinet,
    mediaPanel,
    upholstery,
    accentFabric,
    rug,
    brushedBrass,
    warmLight,
    tvScreen,
    boilerEnamel,
    pelletFeedHose,
    controlDisplay,
    tankJacket,
    copperPipe,
    sanitaryCeramic,
    mirrorGlass,
    showerGlass,
    blackCeramic,
    applianceEnamel,
    officeFabric,
    whiteboardGlass,
    bedroomLinen,
    bedroomThrow,
    wardrobeFront,
    hallwayWardrobeOak,
    hallwayWardrobeSmokedOak,
    childSage,
    childClay,
    childMidnight,
    childSand,
    childCork,
  };
}

/** Box with per-face UVs so one shared material keeps a constant tile size. */
export function texturedBox(
  scene: Scene,
  name: string,
  centerMm: Point2Mm,
  widthMm: number,
  depthMm: number,
  heightM: number,
  elevationM: number,
  tileM: number,
) {
  const w = widthMm * MM_TO_M;
  const d = depthMm * MM_TO_M;
  const h = heightM;
  const faceUV = [
    new Vector4(0, 0, w / tileM, h / tileM),
    new Vector4(0, 0, w / tileM, h / tileM),
    new Vector4(0, 0, d / tileM, h / tileM),
    new Vector4(0, 0, d / tileM, h / tileM),
    new Vector4(0, 0, w / tileM, d / tileM),
    new Vector4(0, 0, w / tileM, d / tileM),
  ];
  const mesh = CreateBox(name, { width: w, depth: d, height: h, faceUV }, scene);
  mesh.position.set(xM(centerMm.x), elevationM + h / 2, zM(centerMm.y));
  return mesh;
}

function rectCenter(rect: RectMm): Point2Mm {
  return { x: (rect.x0 + rect.x1) / 2, y: (rect.y0 + rect.y1) / 2 };
}

function vaultElevationMm(xMm: number, wallClearMm: number, halfSpanMm: number) {
  const distance = Math.min(halfSpanMm, Math.abs(xMm - WING_RIDGE_XMM));
  return VAULT_RIDGE_MM - (VAULT_RIDGE_MM - wallClearMm) * (distance / halfSpanMm);
}

/**
 * Solid extruded from a vertical profile in a plane of constant plan-y
 * (profile `along` = plan x). Fills the thickness between `fromYmm` and
 * `toYmm`.
 */
function profileSolidY(
  scene: Scene,
  name: string,
  profile: readonly { readonly alongMm: number; readonly elevationMm: number }[],
  fromYmm: number,
  toYmm: number,
) {
  const shape = profile.map(
    (point) => new Vector3(xM(point.alongMm), 0, point.elevationMm * MM_TO_M),
  );
  const mesh = ExtrudePolygon(
    name,
    {
      shape,
      depth: Math.abs(toYmm - fromYmm) * MM_TO_M,
      sideOrientation: Mesh.DOUBLESIDE,
    },
    scene,
    earcut,
  );
  mesh.rotationQuaternion = Quaternion.RotationYawPitchRoll(0, -Math.PI / 2, 0);
  mesh.position.set(0, 0, zM(Math.max(fromYmm, toYmm)));
  return mesh;
}

function finish(
  context: InteriorBuildContext,
  mesh: Mesh,
  material: PBRMaterial,
  options: {
    collide?: boolean;
    shadow?: boolean;
    pickable?: boolean;
    cameraOccluder?: boolean;
    walkSurface?: boolean;
    walkSurfaceKind?: WalkSurfaceKind;
    walkSurfaceId?: string;
    walkSurfaceElevationOffsetM?: number;
    entityId?: string;
  } = {},
) {
  mesh.material = warmLivingMaterial(context.scene, mesh.name, material);
  mesh.receiveShadows = true;
  mesh.isPickable = options.pickable ?? false;
  mesh.checkCollisions = options.collide ?? false;
  if (options.cameraOccluder || options.walkSurface) {
    mesh.metadata = {
      ...(mesh.metadata ?? {}),
      ...(options.cameraOccluder ? { cameraOccluder: true } : {}),
      ...(options.walkSurface
        ? {
            walkSurface: true,
            walkSurfaceKind: options.walkSurfaceKind ?? "interior",
            walkSurfaceId: options.walkSurfaceId ?? mesh.name,
            walkSurfaceElevationOffsetM:
              options.walkSurfaceElevationOffsetM ?? 0,
          }
        : {}),
    };
  }
  context.realisticOnly(mesh);
  if (options.shadow) context.castShadow(mesh);
  context.register(mesh, "building", options.entityId ?? HOUSE_ENTITY);
  return mesh;
}

function floorMaterial(materials: InteriorMaterials, room: InteriorRoom) {
  switch (room.floor) {
    case "TILE":
      return materials.tile;
    case "EPOXY":
      return materials.epoxy;
    default:
      return materials.vinyl;
  }
}

function buildFloorsAndCeilings(context: InteriorBuildContext, materials: InteriorMaterials) {
  // Continuous base slab under the whole footprint: closes every gap between
  // room floors (wall footprints, thresholds) so the terrain never shows.
  for (const [index, rect] of [
    { x0: HOUSE.originMm.x, y0: HOUSE.originMm.y, x1: HOUSE.originMm.x + HOUSE.lowerBar.widthMm, y1: HOUSE.originMm.y + HOUSE.lowerBar.depthMm },
    { x0: HOUSE.originMm.x + HOUSE.wing.xMm, y0: HOUSE.originMm.y + HOUSE.wing.yMm, x1: HOUSE.originMm.x + HOUSE.wing.xMm + HOUSE.wing.widthMm, y1: HOUSE.originMm.y + HOUSE.wing.yMm + HOUSE.wing.depthMm },
  ].entries()) {
    const slab = texturedBox(
      context.scene,
      `Podkladová doska 1.NP ${index + 1}`,
      rectCenter(rect),
      rect.x1 - rect.x0,
      rect.y1 - rect.y0,
      0.05,
      FLOOR_TOP_M - 0.052,
      1.5,
    );
    finish(context, slab, materials.epoxy, {
      walkSurface: true,
      walkSurfaceId: `interior-base-${index + 1}`,
      walkSurfaceElevationOffsetM: 0.002,
    });
  }
  // Door thresholds carry the floor of the room the door opens from.
  for (const door of INTERIOR_DOORS) {
    const fromRoom = INTERIOR_ROOMS.find((room) => room.id === door.fromRoomId);
    const [wallFrom, wallTo] = door.wallSpanMm;
    const center =
      door.axis === "X"
        ? { x: door.startMm + door.widthMm / 2, y: (wallFrom + wallTo) / 2 }
        : { x: (wallFrom + wallTo) / 2, y: door.startMm + door.widthMm / 2 };
    const threshold = texturedBox(
      context.scene,
      `${door.label} · prah`,
      center,
      door.axis === "X" ? door.widthMm : wallTo - wallFrom,
      door.axis === "X" ? wallTo - wallFrom : door.widthMm,
      0.04,
      FLOOR_TOP_M - 0.04,
      fromRoom?.floor === "TILE" ? 1.2 : 1.6,
    );
    finish(
      context,
      threshold,
      fromRoom ? floorMaterial(materials, fromRoom) : materials.vinyl,
      {
        walkSurface: true,
        walkSurfaceId: `interior-threshold-${door.id}`,
      },
    );
  }
  for (const room of INTERIOR_ROOMS) {
    const floorTile = room.floor === "TILE" ? 1.2 : room.floor === "EPOXY" ? 1.5 : 1.6;
    for (const [index, rect] of room.rectsMm.entries()) {
      const floor = texturedBox(
        context.scene,
        `${room.number} ${room.name} · podlaha ${index + 1}`,
        rectCenter(rect),
        rect.x1 - rect.x0,
        rect.y1 - rect.y0,
        0.04,
        FLOOR_TOP_M - 0.04,
        floorTile,
      );
      finish(context, floor, floorMaterial(materials, room), {
        pickable: true,
        walkSurface: true,
        walkSurfaceId: `interior-room-${room.id}-${index + 1}`,
      });

      // The whole living room, including the kitchen bay up to the load-bearing
      // kitchen wall, lies under the wing roof and its cathedral ceiling.
      const vaulted = room.ceiling === "VAULTED_TO_RIDGE";
      if (!vaulted) {
        const ceiling = texturedBox(
          context.scene,
          `${room.number} ${room.name} · SDK podhľad +${(room.clearHeightMm / 1000).toFixed(3)}`,
          rectCenter(rect),
          rect.x1 - rect.x0,
          rect.y1 - rect.y0,
          0.03,
          room.clearHeightMm * MM_TO_M,
          2,
        );
        finish(context, ceiling, materials.ceiling, { cameraOccluder: true });
      }
    }
    if (room.ceiling === "VAULTED_TO_RIDGE") buildVault(context, materials, room);
  }
}

/**
 * Sloped SDK ceiling of 1.03 following the wing roof up to the ridge. Every
 * floor part of the room lies under the wing roof, so the kitchen bay between
 * the corridor spine and the east facade is vaulted up to the 300 mm
 * load-bearing kitchen wall that carries the ring beam and the steel roof
 * frames (12. 9. 2026).
 */
function buildVault(context: InteriorBuildContext, materials: InteriorMaterials, room: InteriorRoom) {
  const bounds = roomBoundsMm(room);
  const halfSpanMm = WING_RIDGE_XMM - bounds.x0;
  const wallClearMm = room.clearHeightMm;
  const elevation = (xMm: number) => vaultElevationMm(xMm, wallClearMm, halfSpanMm);
  const label = (mm: number) => (mm / 1000).toFixed(3).replace(".", ",");
  const thicknessM = 0.04;
  for (const [index, rect] of room.rectsMm.entries()) {
    for (const side of [-1, 1] as const) {
      const startX = side < 0 ? rect.x0 : Math.max(rect.x0, WING_RIDGE_XMM);
      const endX = side < 0 ? Math.min(rect.x1, WING_RIDGE_XMM) : rect.x1;
      if (endX <= startX) continue;
      const runM = (endX - startX) * MM_TO_M;
      const riseM = (elevation(endX) - elevation(startX)) * MM_TO_M;
      const lengthM = Math.hypot(runM, riseM);
      const lowMm = Math.min(elevation(startX), elevation(endX));
      const highMm = Math.max(elevation(startX), elevation(endX));
      const slab = texturedBox(
        context.scene,
        `${room.number} · šikmý SDK podhľad ${side < 0 ? "západ" : "východ"}${index ? " · kuchynský záliv" : ""} · +${label(lowMm)} → +${label(highMm)}`,
        { x: (startX + endX) / 2, y: (rect.y0 + rect.y1) / 2 },
        Math.round(lengthM * 1000),
        rect.y1 - rect.y0,
        thicknessM,
        ((elevation(startX) + elevation(endX)) / 2) * MM_TO_M,
        2,
      );
      slab.rotation.z = Math.atan2(riseM, runM);
      finish(context, slab, materials.ceiling, { cameraOccluder: true });
    }
  }
  // Closures of the vault along the room's south boundary: above the corridor
  // mouth, above the corridor spine (which stops at the general wall height)
  // and above the load-bearing kitchen wall, which runs in one line to the
  // east facade; the lintel of the technical-room door reaches the wall crown,
  // so the closure is continuous over it. The north end toward the porch is
  // the glazed gable (HOUSE.porches.wingEnd.glazing.gable).
  const main = room.rectsMm[0];
  const corridor = INTERIOR_ROOMS.find((other) => other.id === "ROOM-1-02")!;
  const spine = INTERIOR_WALLS.find((wall) => wall.id === "IW-SPINE-EAST-3")!.rectMm;
  const bearing = KITCHEN_BEARING_WALL;
  const closures = [
    { name: "južný štít podhľadu · ústie chodby", x0: main.x0, x1: spine.x0, y0: main.y0 - 139, y1: main.y0, baseMm: corridor.clearHeightMm },
    { name: "štít podhľadu · nad východnou stenou chodby", x0: spine.x0, x1: spine.x1, y0: spine.y0, y1: spine.y1, baseMm: INTERIOR_WALL_HEIGHT_MM },
    { name: "južný štít podhľadu · nad nosnou stenou kuchyne", x0: bearing.x0, x1: KITCHEN_BEARING_WALL_EAST.x1, y0: bearing.y0, y1: bearing.y1, baseMm: INTERIOR_WALL_HEIGHT_MM },
  ];
  const apex = { alongMm: WING_RIDGE_XMM, elevationMm: VAULT_RIDGE_MM };
  for (const closure of closures) {
    // Only where the vault is above the closure's base; toward the east wall
    // the soffit drops below the wall tops.
    const reachMm =
      halfSpanMm * (1 - (closure.baseMm - wallClearMm) / (VAULT_RIDGE_MM - wallClearMm));
    const xa = Math.max(closure.x0, WING_RIDGE_XMM - reachMm);
    const xb = Math.min(closure.x1, WING_RIDGE_XMM + reachMm);
    if (xb - xa < 1) continue;
    const profile = [
      { alongMm: xa, elevationMm: closure.baseMm },
      { alongMm: xb, elevationMm: closure.baseMm },
      { alongMm: xb, elevationMm: elevation(xb) },
      ...(xa < WING_RIDGE_XMM && xb > WING_RIDGE_XMM ? [apex] : []),
      { alongMm: xa, elevationMm: elevation(xa) },
    ].filter(
      (point, index, points) =>
        index === 0 ||
        Math.abs(point.elevationMm - points[index - 1].elevationMm) > 1 ||
        Math.abs(point.alongMm - points[index - 1].alongMm) > 1,
    );
    const last = profile[profile.length - 1];
    if (profile.length > 3 && Math.abs(last.alongMm - profile[0].alongMm) <= 1 && Math.abs(last.elevationMm - profile[0].elevationMm) <= 1) profile.pop();
    if (profile.length < 3) continue;
    const solid = profileSolidY(context.scene, `${room.number} · ${closure.name}`, profile, closure.y0, closure.y1);
    finish(context, solid, materials.plaster, { collide: true });
  }
}

function buildWalls(context: InteriorBuildContext, materials: InteriorMaterials) {
  const heightM = INTERIOR_WALL_HEIGHT_MM * MM_TO_M;
  for (const wall of INTERIOR_RENDER_WALLS) {
    const rect = wall.rectMm;
    const mesh = texturedBox(
      context.scene,
      `Vnútorná stena ${wall.id} · ${wall.role === "LOAD_BEARING" ? "nosná" : "priečka"} ${rect.x1 - rect.x0 < rect.y1 - rect.y0 ? rect.x1 - rect.x0 : rect.y1 - rect.y0} mm`,
      rectCenter(rect),
      rect.x1 - rect.x0,
      rect.y1 - rect.y0,
      heightM,
      0,
      2.4,
    );
    finish(context, mesh, materials.plaster, { collide: true, shadow: true, pickable: true });
  }
  // Wing corner pier between the garden facade and the wing west wall.
  const corner = texturedBox(
    context.scene,
    "Vnútorná stena · roh krídla 21 040 – 21 543",
    { x: (21040 + 21543) / 2, y: (10670 + 11200) / 2 },
    503,
    530,
    heightM,
    0,
    2.4,
  );
  finish(context, corner, materials.plaster, { collide: true });

}

/**
 * Slender cylindrical stove based on the client's visual reference. The dark
 * shell stays collision-authoritative while the curved glass, embers, trim and
 * handle remain non-colliding visual detail. The continuous flue itself is
 * rendered by the exterior scene from this body's top to its roof termination.
 */
export function buildLivingFireplace(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  stove: FireplaceStove = FIREPLACE_STOVE,
) {
  const center = stove.centerMm;
  const diameterM = stove.bodyDiameterMm * MM_TO_M;
  const radiusMm = stove.bodyDiameterMm / 2;
  const bodyHeightM = stove.bodyHeightMm * MM_TO_M;
  const shellBottomM = 0.03;
  const shellHeightM = bodyHeightM - shellBottomM;
  // Door direction as a plan angle; `at` places details `forward` millimetres
  // in front of the axis and `side` millimetres to the left of the fire.
  const facingRad = (stove.facingAngleDeg * Math.PI) / 180;
  const cosF = Math.cos(facingRad), sinF = Math.sin(facingRad);
  const at = (forwardMm: number, sideMm: number): Point2Mm => ({
    x: center.x + forwardMm * cosF - sideMm * sinF,
    y: center.y + forwardMm * sinF + sideMm * cosF,
  });

  const body = CreateCylinder(
    `${stove.id} · BODY · matne čierne valcové teleso Ø${stove.bodyDiameterMm}`,
    { height: shellHeightM, diameter: diameterM, tessellation: 64 },
    context.scene,
  );
  body.position.set(xM(center.x), shellBottomM + shellHeightM / 2, zM(center.y));
  body.metadata = {
    ...(body.metadata ?? {}),
    designSourceId: stove.sourceId,
    fireplaceShape: "CYLINDRICAL",
  };
  finish(context, body, materials.fireplace, {
    collide: true,
    shadow: true,
    pickable: true,
    cameraOccluder: true,
  });

  const pedestal = CreateCylinder(
    `${stove.id} · PEDESTAL · zapustený kruhový sokel`,
    { height: 0.055, diameter: diameterM + 0.02, tessellation: 64 },
    context.scene,
  );
  pedestal.position.set(xM(center.x), 0.0275, zM(center.y));
  finish(context, pedestal, materials.fireplace, { shadow: true });

  const topCap = CreateCylinder(
    `${stove.id} · TOP-CAP · horné veko`,
    { height: 0.025, diameter: diameterM + 0.008, tessellation: 64 },
    context.scene,
  );
  topCap.position.set(xM(center.x), bodyHeightM - 0.0125, zM(center.y));
  finish(context, topCap, materials.fireplace, { shadow: true });

  const arc = stove.window.arcDegrees / 360;
  const arcRotationY = -Math.PI * arc + facingRad;
  const windowBottomM = stove.window.bottomElevationMm * MM_TO_M;
  const windowHeightM = stove.window.heightMm * MM_TO_M;
  const windowCenterM = windowBottomM + windowHeightM / 2;

  const glow = CreateCylinder(
    `${stove.id} · FIRE-GLOW · žeravé ohnisko`,
    {
      height: windowHeightM - 0.045,
      diameter: diameterM + 0.006,
      tessellation: 48,
      arc,
      cap: Mesh.NO_CAP,
      sideOrientation: Mesh.DOUBLESIDE,
    },
    context.scene,
  );
  glow.position.set(xM(center.x), windowCenterM, zM(center.y));
  glow.rotation.y = arcRotationY;
  finish(context, glow, materials.fireplaceEmber, { shadow: true });

  const glass = CreateCylinder(
    `${stove.id} · CURVED-GLASS · zaoblené panoramatické dvierka ${stove.window.arcDegrees}°`,
    {
      height: windowHeightM,
      diameter: diameterM + 0.018,
      tessellation: 48,
      arc,
      cap: Mesh.NO_CAP,
      sideOrientation: Mesh.DOUBLESIDE,
    },
    context.scene,
  );
  glass.position.set(xM(center.x), windowCenterM, zM(center.y));
  glass.rotation.y = arcRotationY;
  finish(context, glass, materials.fireplaceGlass, { shadow: true, pickable: true });

  for (const [index, elevationM] of [windowBottomM, windowBottomM + windowHeightM].entries()) {
    const trim = CreateTorus(
      `${stove.id} · WINDOW-TRIM-${index + 1} · vodorovný rám dvierok`,
      { diameter: diameterM + 0.018, thickness: 0.018, tessellation: 64 },
      context.scene,
    );
    trim.position.set(xM(center.x), elevationM, zM(center.y));
    finish(context, trim, materials.fireplace, { shadow: true });
  }

  const halfArcRad = (stove.window.arcDegrees * Math.PI) / 360;
  for (const [index, side] of [-1, 1].entries()) {
    const jamb = CreateCylinder(
      `${stove.id} · WINDOW-JAMB-${index + 1} · zvislý rám dvierok`,
      { height: windowHeightM + 0.025, diameter: 0.022, tessellation: 20 },
      context.scene,
    );
    const jambAt = at(radiusMm * Math.cos(halfArcRad), side * radiusMm * Math.sin(halfArcRad));
    jamb.position.set(xM(jambAt.x), windowCenterM, zM(jambAt.y));
    finish(context, jamb, materials.fireplace, { shadow: true });
  }

  const fireFrontMm = radiusMm + 5;
  for (const [index, offsetYmm] of [-62, 54].entries()) {
    const log = CreateCylinder(
      `${stove.id} · LOG-${index + 1} · horiace poleno`,
      { height: 0.245, diameter: 0.052, tessellation: 20 },
      context.scene,
    );
    const logAt = at(fireFrontMm, offsetYmm);
    log.position.set(xM(logAt.x), 0.5 + index * 0.035, zM(logAt.y));
    log.rotation.x = Math.PI / 2;
    log.rotation.y = (index === 0 ? -0.18 : 0.22) + facingRad;
    finish(context, log, materials.fireplaceEmber, { shadow: true });
  }
  for (const [index, flame] of [
    { yMm: -75, heightM: 0.2, diameterM: 0.055, elevationM: 0.62 },
    { yMm: 0, heightM: 0.29, diameterM: 0.07, elevationM: 0.63 },
    { yMm: 82, heightM: 0.17, diameterM: 0.048, elevationM: 0.6 },
  ].entries()) {
    const flameMesh = CreateCylinder(
      `${stove.id} · FLAME-${index + 1} · plameň`,
      {
        height: flame.heightM,
        diameterBottom: flame.diameterM,
        diameterTop: 0.008,
        tessellation: 24,
      },
      context.scene,
    );
    const flameAt = at(fireFrontMm + 3, flame.yMm);
    flameMesh.position.set(
      xM(flameAt.x),
      flame.elevationM + flame.heightM / 2,
      zM(flameAt.y),
    );
    finish(context, flameMesh, materials.fireplaceEmber, { shadow: true });
  }

  const handleCenter = at(178, 279);
  const handle = CreateCylinder(
    `${stove.id} · DOOR-HANDLE · zvislá čierna rukoväť`,
    { height: 0.24, diameter: 0.026, tessellation: 24 },
    context.scene,
  );
  handle.position.set(xM(handleCenter.x), windowCenterM, zM(handleCenter.y));
  finish(context, handle, materials.fireplace, { shadow: true, pickable: true });
  for (const elevationM of [windowCenterM - 0.085, windowCenterM + 0.085]) {
    const handleMount = texturedBox(
      context.scene,
      `${stove.id} · DOOR-HANDLE-MOUNT · konzola rukoväte`,
      at(178, 252),
      24,
      58,
      0.018,
      elevationM - 0.009,
      1,
    );
    handleMount.rotation.y = facingRad;
    finish(context, handleMount, materials.fireplace, { shadow: true });
  }

  const airControl = CreateSphere(
    `${stove.id} · AIR-CONTROL · regulácia vzduchu`,
    { diameter: 0.027, segments: 20 },
    context.scene,
  );
  const airControlAt = at(radiusMm + 17, 0);
  airControl.position.set(xM(airControlAt.x), 0.322, zM(airControlAt.y));
  finish(context, airControl, context.chimneyMetal, { shadow: true, pickable: true });

  const collar = CreateCylinder(
    `${stove.id} · FLUE-COLLAR · priame horné napojenie Ø${stove.flue.outerDiameterMm}`,
    { height: 0.05, diameter: stove.flue.outerDiameterMm * MM_TO_M + 0.035, tessellation: 40 },
    context.scene,
  );
  collar.position.set(xM(center.x), bodyHeightM + 0.015, zM(center.y));
  finish(context, collar, materials.fireplace, { shadow: true });

  const fireLightAt = at(radiusMm + 320, 0);
  const fireLight = new PointLight(
    `${stove.id} · FIRE-LIGHT · teplé svetlo ohniska`,
    new Vector3(xM(fireLightAt.x), windowCenterM, zM(fireLightAt.y)),
    context.scene,
  );
  fireLight.diffuse = Color3.FromHexString("#ff9d55");
  fireLight.specular = Color3.FromHexString("#ffd2a0");
  fireLight.intensity = 0.42;
  fireLight.range = 3.2;
}

function buildDoor(context: InteriorBuildContext, materials: InteriorMaterials, door: InteriorDoor) {
  const [wallFrom, wallTo] = door.wallSpanMm;
  const thicknessMm = wallTo - wallFrom;
  const frameMm = 60;
  // C dimensions are clear apertures; flush frames sit outside that opening.
  const liningInsetMm = door.widthMm === door.leafWidthMm ? 0 : frameMm;
  const heightM = door.heightMm * MM_TO_M;
  const along = (value: number) => value;
  const plan = (alongMm: number, acrossMm: number): Point2Mm =>
    door.axis === "X" ? { x: alongMm, y: acrossMm } : { x: acrossMm, y: alongMm };
  const wallCenter = (wallFrom + wallTo) / 2;
  // Jambs and head (frame lining through the full wall thickness).
  for (const [side, alongMm] of [
    ["ľavá", door.startMm + liningInsetMm - frameMm / 2],
    ["pravá", door.startMm + door.widthMm - liningInsetMm + frameMm / 2],
  ] as const) {
    const center = plan(along(alongMm), wallCenter);
    const jamb = texturedBox(
      context.scene,
      `${door.label} · ${side} zárubňa`,
      center,
      door.axis === "X" ? frameMm : thicknessMm + 24,
      door.axis === "X" ? thicknessMm + 24 : frameMm,
      heightM,
      0,
      1,
    );
    // The structural wall already guards the opening. A second collision box
    // on each 60 mm lining left just centimetres of tolerance and caught the
    // walker's shoulder while crossing at an angle.
    finish(context, jamb, materials.doorFrame);
  }
  const headCenter = plan(door.startMm + door.widthMm / 2, wallCenter);
  const head = texturedBox(
    context.scene,
    `${door.label} · nadpražie zárubne`,
    headCenter,
    door.axis === "X" ? door.widthMm : thicknessMm + 24,
    door.axis === "X" ? thicknessMm + 24 : door.widthMm,
    frameMm * MM_TO_M,
    heightM - frameMm * MM_TO_M,
    1,
  );
  finish(context, head, materials.doorFrame, { cameraOccluder: true });
  // Lintel above the opening up to the wall crown.
  const lintel = texturedBox(
    context.scene,
    `${door.label} · preklad`,
    headCenter,
    door.axis === "X" ? door.widthMm : thicknessMm,
    door.axis === "X" ? thicknessMm : door.widthMm,
    INTERIOR_WALL_HEIGHT_MM * MM_TO_M - heightM,
    heightM,
    2.4,
  );
  finish(context, lintel, materials.plaster, { cameraOccluder: true });

  const leafThicknessMm = 40;
  if (door.motion === "POCKET_SLIDING") {
    const pocketDirection = door.pocketDirection ?? -1;
    const pocketTravelMm = door.pocketTravelMm ?? door.leafWidthMm + frameMm;
    const closedCenterAlong = door.startMm + door.widthMm / 2;
    const openCenterAlong = closedCenterAlong + pocketDirection * pocketTravelMm;
    const closedCenterPlan = plan(closedCenterAlong, wallCenter);
    const openCenterPlan = plan(openCenterAlong, wallCenter);
    const movingRoot = new TransformNode(
      `${door.id} · posuvný vozík puzdrových dverí`,
      context.scene,
    );
    movingRoot.metadata = { doorId: door.id, doorMotion: "SLIDING" };
    const leaf = texturedBox(
      context.scene,
      `${door.label} · animované krídlo`,
      closedCenterPlan,
      door.axis === "X" ? door.leafWidthMm : leafThicknessMm,
      door.axis === "X" ? leafThicknessMm : door.leafWidthMm,
      heightM - 0.07,
      0.02,
      1,
    );
    const leafWorld = leaf.position.clone();
    leaf.parent = movingRoot;
    leaf.position.copyFrom(leafWorld.subtract(movingRoot.position));
    leaf.metadata = {
      ...(leaf.metadata ?? {}),
      cameraOccluder: true,
      dynamicCameraOccluder: true,
      doorId: door.id,
      doorMotion: "SLIDING",
    };
    finish(context, leaf, materials.doorLeaf, {
      collide: true,
      shadow: true,
      pickable: true,
      cameraOccluder: true,
      entityId: door.id,
    });

    // Recessed pulls remain flush enough to disappear safely into the pocket.
    const pullAlongMm = closedCenterAlong
      - pocketDirection * (door.leafWidthMm / 2 - 105);
    const pullMeshes: Mesh[] = [];
    for (const side of [-1, 1] as const) {
      const pullPlan = plan(
        pullAlongMm,
        wallCenter + side * (leafThicknessMm / 2 + 4),
      );
      const pull = CreateCylinder(
        `${door.label} · zapustená kľučka ${side < 0 ? "A" : "B"}`,
        { height: 0.012, diameter: 0.12, tessellation: 28 },
        context.scene,
      );
      pull.position.set(xM(pullPlan.x), 1.02, zM(pullPlan.y));
      if (door.axis === "X") pull.rotation.x = Math.PI / 2;
      else pull.rotation.z = Math.PI / 2;
      const pullWorld = pull.position.clone();
      pull.parent = movingRoot;
      pull.position.copyFrom(pullWorld.subtract(movingRoot.position));
      pull.metadata = {
        ...(pull.metadata ?? {}),
        doorId: door.id,
        doorMotion: "SLIDING",
      };
      finish(context, pull, context.chimneyMetal, {
        shadow: true,
        pickable: true,
        entityId: door.id,
      });
      pullMeshes.push(pull);
    }

    // A slim edge pull remains a few millimetres visible at the pocket jamb,
    // so the fully open leaf still reads as operable in close-up and on touch.
    const edgePullAlongMm = closedCenterAlong
      - pocketDirection * (door.leafWidthMm / 2 + 14);
    const edgePullPlan = plan(edgePullAlongMm, wallCenter);
    const edgePull = texturedBox(
      context.scene,
      `${door.label} · čelné výsuvné madlo`,
      edgePullPlan,
      door.axis === "X" ? 28 : 10,
      door.axis === "X" ? 10 : 28,
      0.18,
      0.91,
      1,
    );
    const edgePullWorld = edgePull.position.clone();
    edgePull.parent = movingRoot;
    edgePull.position.copyFrom(edgePullWorld.subtract(movingRoot.position));
    edgePull.metadata = {
      ...(edgePull.metadata ?? {}),
      doorId: door.id,
      doorMotion: "SLIDING",
    };
    finish(context, edgePull, context.chimneyMetal, {
      shadow: true,
      pickable: true,
      entityId: door.id,
    });
    pullMeshes.push(edgePull);

    const closedCenterWorld = {
      x: xM(closedCenterPlan.x),
      z: zM(closedCenterPlan.y),
    };
    const openCenterWorld = {
      x: xM(openCenterPlan.x),
      z: zM(openCenterPlan.y),
    };
    const travel = {
      x: openCenterWorld.x - closedCenterWorld.x,
      z: openCenterWorld.z - closedCenterWorld.z,
    };
    const interactionPlan = plan(
      door.startMm + door.widthMm / 2,
      wallCenter,
    );
    const slidingPerpendicularClearanceM =
      leafThicknessMm * MM_TO_M / 2 + 0.04;
    context.registerAnimatedDoor?.({
      id: door.id,
      label: door.label.replace(/^Dvere\s+/u, "").replace(/\s+·.*$/u, ""),
      kind: "SLIDING",
      interactionPoint: { x: xM(interactionPlan.x), z: zM(interactionPlan.y) },
      passage: interiorDoorPassage(door, interactionPlan, thicknessMm, liningInsetMm),
      apply: (progress) => {
        movingRoot.position.x = travel.x * progress;
        movingRoot.position.z = travel.z * progress;
        leaf.computeWorldMatrix(true);
        for (const pull of pullMeshes) pull.computeWorldMatrix(true);
      },
      canOpen: (actor, progress = 0) =>
        slidingDoorPathIsClear(
          actor,
          closedCenterWorld,
          openCenterWorld,
          door.leafWidthMm * MM_TO_M / 2,
          slidingPerpendicularClearanceM,
          progress,
          1,
        ),
      canClose: (actor, progress = 1) =>
        slidingDoorPathIsClear(
          actor,
          closedCenterWorld,
          openCenterWorld,
          door.leafWidthMm * MM_TO_M / 2,
          slidingPerpendicularClearanceM,
          progress,
          0,
        ),
      actorDisplacement: (actor, progress) =>
        slidingDoorActorDisplacement(
          actor,
          closedCenterWorld,
          openCenterWorld,
          door.leafWidthMm * MM_TO_M / 2,
          slidingPerpendicularClearanceM,
          progress,
        ),
    });
    return;
  }

  // A real pivot at the documented hinge replaces the former permanently open
  // decorative slab. The controller owns the state; Babylon owns the live
  // transform, collision and shadow at every animation frame.
  const hingeAlongMm =
    door.hinge < 0 ? door.startMm + liningInsetMm : door.startMm + door.widthMm - liningInsetMm;
  const hingeAcrossMm = (door.swing < 0 ? wallFrom : wallTo) + door.swing * (door.hingeOffsetMm ?? 0);
  const alongDirection = door.hinge < 0 ? 1 : -1;
  const leafCenterAlong = hingeAlongMm + alongDirection * door.leafWidthMm / 2;
  const hingePlan = plan(hingeAlongMm, hingeAcrossMm);
  const leafCenterPlan = plan(leafCenterAlong, hingeAcrossMm);
  const hinge = new TransformNode(`${door.id} · pánt animovaných dverí`, context.scene);
  hinge.position.set(xM(hingePlan.x), 0, zM(hingePlan.y));
  hinge.metadata = { doorId: door.id, doorMotion: "HINGED" };
  const leaf = texturedBox(
    context.scene,
    `${door.label} · animované krídlo`,
    leafCenterPlan,
    door.axis === "X" ? door.leafWidthMm : leafThicknessMm,
    door.axis === "X" ? leafThicknessMm : door.leafWidthMm,
    heightM - 0.07,
    0.02,
    1,
  );
  const leafWorld = leaf.position.clone();
  leaf.parent = hinge;
  leaf.position.copyFrom(leafWorld.subtract(hinge.position));
  leaf.metadata = {
    ...(leaf.metadata ?? {}),
    cameraOccluder: true,
    dynamicCameraOccluder: true,
    doorId: door.id,
    doorMotion: "HINGED",
  };
  finish(context, leaf, materials.doorLeaf, {
    collide: true,
    shadow: true,
    pickable: true,
    cameraOccluder: true,
    entityId: door.id,
  });

  const handleDistanceMm = Math.max(180, door.leafWidthMm - 105);
  const handleAlongMm = hingeAlongMm + alongDirection * handleDistanceMm;
  const handleLevers: Mesh[] = [];
  for (const side of [-1, 1] as const) {
    const handleAcrossMm =
      hingeAcrossMm + side * (leafThicknessMm / 2 + 15);
    const handlePlan = plan(handleAlongMm, handleAcrossMm);
    const handle = CreateCylinder(
      `${door.label} · kľučka ${side < 0 ? "A" : "B"}`,
      { height: 0.13, diameter: 0.018, tessellation: 16 },
      context.scene,
    );
    handle.position.set(xM(handlePlan.x), 1.05, zM(handlePlan.y));
    if (door.axis === "X") handle.rotation.z = Math.PI / 2;
    else handle.rotation.x = Math.PI / 2;
    const handleWorld = handle.position.clone();
    handle.parent = hinge;
    handle.position.copyFrom(handleWorld.subtract(hinge.position));
    handle.metadata = {
      ...(handle.metadata ?? {}),
      doorId: door.id,
      doorMotion: "HINGED",
    };
    finish(context, handle, context.chimneyMetal, {
      shadow: true,
      pickable: true,
      entityId: door.id,
    });
    handleLevers.push(handle);
  }

  const openAngleRad =
    door.axis === "X"
      ? door.swing * -door.hinge * (Math.PI / 2)
      : door.swing * door.hinge * (Math.PI / 2);
  const closedEndPlan = plan(
    hingeAlongMm + alongDirection * door.leafWidthMm,
    hingeAcrossMm,
  );
  const hingeWorld = { x: xM(hingePlan.x), z: zM(hingePlan.y) };
  const closedEndWorld = {
    x: xM(closedEndPlan.x),
    z: zM(closedEndPlan.y),
  };
  const interactionPlan = plan(
    door.startMm + door.widthMm / 2,
    wallCenter,
  );
  context.registerAnimatedDoor?.({
    id: door.id,
    label: door.label.replace(/^Dvere\s+/u, "").replace(/\s+·.*$/u, ""),
    kind: "HINGED",
    interactionPoint: { x: xM(interactionPlan.x), z: zM(interactionPlan.y) },
    passage: interiorDoorPassage(door, interactionPlan, thicknessMm, liningInsetMm),
    apply: (progress, handleDepression) => {
      hinge.rotation.y = openAngleRad * progress;
      for (const handle of handleLevers) {
        if (door.axis === "X") {
          handle.rotation.z = Math.PI / 2 + handleDepression * 0.34;
        } else {
          handle.rotation.x = Math.PI / 2 - handleDepression * 0.34;
        }
        handle.computeWorldMatrix(true);
      }
      leaf.computeWorldMatrix(true);
    },
    canOpen: (actor, progress = 0) =>
      hingedDoorSweepIsClear(
        actor,
        hingeWorld,
        closedEndWorld,
        openAngleRad,
        leafThicknessMm * MM_TO_M,
        progress,
        1,
      ),
    canClose: (actor, progress = 1) =>
      hingedDoorSweepIsClear(
        actor,
        hingeWorld,
        closedEndWorld,
        openAngleRad,
        leafThicknessMm * MM_TO_M,
        progress,
        0,
      ),
    actorDisplacement: (actor, progress) =>
      hingedDoorActorDisplacement(
        actor,
        hingeWorld,
        closedEndWorld,
        openAngleRad,
        progress,
        leafThicknessMm * MM_TO_M,
      ),
  });
}

/**
 * Clear walk-through envelope of an interior opening: the width between the
 * two 60 mm linings, centred on the opening, through the full wall depth.
 */
export function interiorDoorPassage(
  door: InteriorDoor,
  interactionPlan: Point2Mm,
  wallThicknessMm: number,
  frameMm: number,
): WalkPassage {
  return {
    id: door.id,
    center: { x: xM(interactionPlan.x), z: zM(interactionPlan.y) },
    along: door.axis === "X" ? { x: 1, z: 0 } : { x: 0, z: 1 },
    halfClearWidthM: ((door.widthMm - 2 * frameMm) / 2) * MM_TO_M,
    halfDepthM: (wallThicknessMm / 2) * MM_TO_M,
  };
}

/** Slim black bar handle on a front. */
function barHandle(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  name: string,
  center: Point2Mm,
  lengthMm: number,
  alongX: boolean,
  elevationM: number,
) {
  const mesh = texturedBox(
    context.scene,
    name,
    center,
    alongX ? lengthMm : 12,
    alongX ? 12 : lengthMm,
    0.012,
    elevationM,
    1,
  );
  finish(context, mesh, materials.fireplace);
}

function buildKitchen(context: InteriorBuildContext, materials: InteriorMaterials) {
  const k = KITCHEN_RUN;
  const run = k.rectMm;
  const counterM = k.counterHeightMm * MM_TO_M;
  const plinthM = 0.1;
  const worktopM = 0.04;
  const fridgeUnit = k.fridgeUnitRectMm;

  // ---- back run: carcass, 100 mm recessed plinth, drawer fronts, worktop
  const runStart = fridgeUnit.x1;
  const carcass = texturedBox(
    context.scene,
    `${k.id} · spodné skrinky zadnej linky ${run.x1 - runStart} mm`,
    { x: (runStart + run.x1) / 2, y: (run.y0 + run.y1) / 2 - 10 },
    run.x1 - runStart,
    run.y1 - run.y0 - 20,
    counterM - worktopM - plinthM,
    plinthM,
    1.2,
  );
  finish(context, carcass, materials.kitchenFront, { collide: true, shadow: true, pickable: true });
  const plinth = texturedBox(
    context.scene,
    `${k.id} · sokel`,
    { x: (runStart + run.x1) / 2, y: (run.y0 + run.y1) / 2 - 40 },
    run.x1 - runStart,
    run.y1 - run.y0 - 80,
    plinthM,
    0,
    1,
  );
  finish(context, plinth, materials.fireplace);
  // Front joints: 15 mm grooves drawn as thin dark strips between fronts.
  const fronts = [runStart, 23991, 24591, k.dishwasherXmm[0], k.dishwasherXmm[1], run.x1];
  for (const [index, xMm] of fronts.entries()) {
    if (index === 0 || index === fronts.length - 1) continue;
    const joint = texturedBox(
      context.scene,
      `${k.id} · škára frontov ${index}`,
      { x: xMm, y: run.y1 + 2 },
      4,
      4,
      counterM - worktopM - plinthM,
      plinthM,
      1,
    );
    finish(context, joint, materials.fireplace);
  }
  // Horizontal drawer joints on the two drawer stacks (left of the sink).
  for (const [x0, x1] of [[runStart, 23991], [23991, 24591]] as const) {
    for (const level of [0.38, 0.62]) {
      const joint = texturedBox(
        context.scene,
        `${k.id} · škára zásuvky`,
        { x: (x0 + x1) / 2, y: run.y1 + 2 },
        x1 - x0 - 10,
        4,
        0.004,
        level,
        1,
      );
      finish(context, joint, materials.fireplace);
    }
    for (const level of [0.34, 0.58, 0.8]) {
      barHandle(
        context,
        materials,
        `${k.id} · úchytka zásuvky`,
        { x: (x0 + x1) / 2, y: run.y1 + 14 },
        x1 - x0 - 160,
        true,
        level,
      );
    }
  }
  // Dishwasher: integrated front with a handle; sink cabinet door handle.
  barHandle(context, materials, `${k.id} · úchytka umývačky`, { x: (k.dishwasherXmm[0] + k.dishwasherXmm[1]) / 2, y: run.y1 + 14 }, 400, true, 0.8);
  barHandle(context, materials, `${k.id} · úchytka drezovej skrinky`, { x: k.sinkCenterXmm, y: run.y1 + 14 }, 300, true, 0.8);
  barHandle(context, materials, `${k.id} · úchytka skrinky vpravo`, { x: (k.dishwasherXmm[1] + run.x1) / 2, y: run.y1 + 14 }, 160, true, 0.8);
  const worktop = texturedBox(
    context.scene,
    `${k.id} · pracovná doska z tmavého kremeňa`,
    { x: (runStart + run.x1 + 20) / 2, y: (run.y0 + run.y1) / 2 + 10 },
    run.x1 - runStart + 20,
    run.y1 - run.y0 + 20,
    worktopM,
    counterM - worktopM,
    1.4,
  );
  finish(context, worktop, materials.worktop, { shadow: true });
  // Undermount sink and tap.
  const sinkBowl = texturedBox(
    context.scene,
    `${k.id} · nerezový drez`,
    { x: k.sinkCenterXmm, y: run.y0 + 300 },
    500,
    400,
    0.18,
    counterM - 0.19,
    1,
  );
  finish(context, sinkBowl, materials.steel);
  const sinkRim = texturedBox(
    context.scene,
    `${k.id} · výrez drezu`,
    { x: k.sinkCenterXmm, y: run.y0 + 300 },
    520,
    420,
    0.004,
    counterM - 0.001,
    1,
  );
  finish(context, sinkRim, materials.fireplace);
  const tapRiser = CreateCylinder(`${k.id} · batéria`, { height: 0.3, diameter: 0.03, tessellation: 16 }, context.scene);
  tapRiser.position.set(xM(k.sinkCenterXmm), counterM + 0.15, zM(run.y0 + 80));
  finish(context, tapRiser, materials.steel);
  const tapSpout = CreateCylinder(`${k.id} · výtok batérie`, { height: 0.22, diameter: 0.022, tessellation: 16 }, context.scene);
  tapSpout.position.set(xM(k.sinkCenterXmm), counterM + 0.29, zM(run.y0 + 190));
  tapSpout.rotation.x = Math.PI / 2;
  finish(context, tapSpout, materials.steel);
  // Splashback: 600 mm dark quartz upstand between worktop and upper cabinets.
  const splash = texturedBox(
    context.scene,
    `${k.id} · obklad za linkou`,
    { x: (runStart + run.x1) / 2, y: run.y0 + 6 },
    run.x1 - runStart,
    12,
    k.upperCabinets.bottomMm * MM_TO_M - counterM,
    counterM,
    1.4,
  );
  finish(context, splash, materials.worktop);
  // Upper cabinets (white matt) with a lit underside strip.
  const upper = texturedBox(
    context.scene,
    `${k.id} · horné skrinky`,
    { x: (runStart + run.x1) / 2, y: run.y0 + k.upperCabinets.depthMm / 2 },
    run.x1 - runStart,
    k.upperCabinets.depthMm,
    (k.upperCabinets.topMm - k.upperCabinets.bottomMm) * MM_TO_M,
    k.upperCabinets.bottomMm * MM_TO_M,
    1.2,
  );
  finish(context, upper, materials.kitchenUpper, {
    shadow: true,
    cameraOccluder: true,
  });
  for (const xMm of [23991, 24591, 25191]) {
    const joint = texturedBox(
      context.scene,
      `${k.id} · škára horných skriniek`,
      { x: xMm, y: run.y0 + k.upperCabinets.depthMm + 2 },
      4,
      4,
      (k.upperCabinets.topMm - k.upperCabinets.bottomMm) * MM_TO_M - 0.02,
      k.upperCabinets.bottomMm * MM_TO_M + 0.01,
      1,
    );
    finish(context, joint, materials.fireplace);
  }
  const ledStrip = texturedBox(
    context.scene,
    `${k.id} · LED lišta pod skrinkami`,
    { x: (runStart + run.x1) / 2, y: run.y0 + k.upperCabinets.depthMm - 30 },
    run.x1 - runStart - 40,
    20,
    0.012,
    k.upperCabinets.bottomMm * MM_TO_M - 0.012,
    1,
  );
  finish(context, ledStrip, materials.ceiling);
  ledStrip.metadata = { ...(ledStrip.metadata ?? {}), interiorLightId: KITCHEN_TASK_LIGHT.id };
  createKitchenTaskLight(context.scene);
  // Dedicated 600 mm integrated fridge-freezer at the quiet west end. Its oak
  // fronts align with the kitchen, while the freezer split, recessed handle
  // and plinth vent make the appliance legible without a freestanding box.
  const fridge = texturedBox(
    context.scene,
    `${k.id} · FRIDGE-600 · vstavaná chladnička s mrazničkou`,
    rectCenter(fridgeUnit),
    fridgeUnit.x1 - fridgeUnit.x0,
    fridgeUnit.y1 - fridgeUnit.y0 - 20,
    k.fridgeCabinetHeightMm * MM_TO_M,
    0,
    1.2,
  );
  finish(context, fridge, materials.kitchenFront, {
    collide: true,
    shadow: true,
    pickable: true,
  });
  const freezerJoint = texturedBox(
    context.scene,
    `${k.id} · FRIDGE-600 · škára mrazničky`,
    { x: (fridgeUnit.x0 + fridgeUnit.x1) / 2, y: fridgeUnit.y1 + 2 },
    fridgeUnit.x1 - fridgeUnit.x0 - 12,
    4,
    0.005,
    0.72,
    1,
  );
  finish(context, freezerJoint, materials.fireplace);
  const fridgeHandle = texturedBox(
    context.scene,
    `${k.id} · FRIDGE-600 · zapustené zvislé madlo`,
    { x: fridgeUnit.x1 - 38, y: fridgeUnit.y1 + 14 },
    12,
    12,
    0.82,
    1.05,
    1,
  );
  finish(context, fridgeHandle, materials.fireplace);
  const fridgeVent = texturedBox(
    context.scene,
    `${k.id} · FRIDGE-600 · vetracia štrbina v sokli`,
    { x: (fridgeUnit.x0 + fridgeUnit.x1) / 2, y: fridgeUnit.y1 + 3 },
    430,
    5,
    0.025,
    0.055,
    1,
  );
  finish(context, fridgeVent, materials.fireplace);

  // ---- peninsula with the hob (D1.1.002 symbol) and a clear serving overhang
  const pen = k.peninsulaRectMm;
  const eastReturn = k.eastReturnRectMm;
  // Worktop: 10 mm nosing on the kitchen side, the serving overhang toward the room.
  const penTopDepthMm = pen.y1 - pen.y0 + 10 + k.peninsulaOverhangMm;
  const penTopCenterYmm = pen.y0 - 10 + penTopDepthMm / 2;
  const penCarcass = texturedBox(
    context.scene,
    `${k.id} · polostrov ${pen.x1 - pen.x0} × ${pen.y1 - pen.y0}`,
    rectCenter(pen),
    pen.x1 - pen.x0,
    pen.y1 - pen.y0 - 20,
    counterM - worktopM - plinthM,
    plinthM,
    1.2,
  );
  finish(context, penCarcass, materials.kitchenFront, { collide: true, shadow: true, pickable: true });
  const penPlinth = texturedBox(
    context.scene,
    `${k.id} · sokel polostrova`,
    rectCenter(pen),
    pen.x1 - pen.x0 - 80,
    pen.y1 - pen.y0 - 100,
    plinthM,
    0,
    1,
  );
  finish(context, penPlinth, materials.fireplace);
  const penTop = texturedBox(
    context.scene,
    `${k.id} · pracovná doska polostrova`,
    { x: (pen.x0 + pen.x1) / 2, y: penTopCenterYmm },
    pen.x1 - pen.x0 + 20,
    penTopDepthMm,
    worktopM,
    counterM - worktopM,
    1.4,
  );
  finish(context, penTop, materials.worktop, { shadow: true });

  // Short L-return in the free east-wall bay identified in the client's
  // walkthrough screenshot. It joins the peninsula worktop, ends before
  // window EAST-04 and stays wholly beyond the technical-room door opening.
  const returnCarcass = texturedBox(
    context.scene,
    `${k.id} · L-RETURN-EAST · dubová spodná kredencová linka`,
    rectCenter(eastReturn),
    eastReturn.x1 - eastReturn.x0,
    eastReturn.y1 - eastReturn.y0,
    counterM - worktopM - plinthM,
    plinthM,
    1.2,
  );
  finish(context, returnCarcass, materials.kitchenFront, {
    collide: true,
    shadow: true,
    pickable: true,
  });
  const returnPlinth = texturedBox(
    context.scene,
    `${k.id} · L-RETURN-EAST · zapustený sokel`,
    {
      x: (eastReturn.x0 + eastReturn.x1) / 2 + 35,
      y: (eastReturn.y0 + eastReturn.y1) / 2,
    },
    eastReturn.x1 - eastReturn.x0 - 70,
    eastReturn.y1 - eastReturn.y0 - 70,
    plinthM,
    0,
    1,
  );
  finish(context, returnPlinth, materials.fireplace);
  const returnTop = texturedBox(
    context.scene,
    `${k.id} · L-RETURN-EAST · nadväzujúca tmavá kremenná doska`,
    {
      x: (eastReturn.x0 + eastReturn.x1) / 2 - 10,
      y: (eastReturn.y0 + eastReturn.y1) / 2 + 10,
    },
    eastReturn.x1 - eastReturn.x0 + 20,
    eastReturn.y1 - eastReturn.y0 + 20,
    worktopM,
    counterM - worktopM,
    1.4,
  );
  finish(context, returnTop, materials.worktop, { shadow: true, pickable: true });
  // The return now runs on under the 900 mm sill of window EAST-04, so the
  // 180 mm quartz upstand stops 20 mm short of the window reveal.
  const eastWindow = HOUSE.facades.east.openings.find((opening) => opening.id === "EAST-04")!;
  const upstandY0 = eastReturn.y0 + 10;
  const upstandY1 = Math.min(eastReturn.y1 - 10, eastWindow.startYmm - 20);
  const returnUpstand = texturedBox(
    context.scene,
    `${k.id} · L-RETURN-EAST · kremenný obklad pri stene`,
    { x: eastReturn.x1 - 6, y: (upstandY0 + upstandY1) / 2 },
    12,
    upstandY1 - upstandY0,
    0.18,
    counterM,
    1.4,
  );
  finish(context, returnUpstand, materials.worktop);
  const returnFrontJoint = texturedBox(
    context.scene,
    `${k.id} · L-RETURN-EAST · škára dvoch frontov`,
    { x: eastReturn.x0 - 2, y: (eastReturn.y0 + eastReturn.y1) / 2 },
    4,
    4,
    counterM - worktopM - plinthM,
    plinthM,
    1,
  );
  finish(context, returnFrontJoint, materials.fireplace);
  for (const yMm of [
    eastReturn.y0 + (eastReturn.y1 - eastReturn.y0) / 4,
    eastReturn.y0 + 3 * (eastReturn.y1 - eastReturn.y0) / 4,
  ]) {
    barHandle(
      context,
      materials,
      `${k.id} · L-RETURN-EAST · úchytka kredenca`,
      { x: eastReturn.x0 - 14, y: yMm },
      300,
      false,
      0.8,
    );
  }
  const returnNavigationGuard = texturedBox(
    context.scene,
    `${k.id} · L-RETURN-EAST · hladký navigačný obrys`,
    {
      x: (eastReturn.x0 + eastReturn.x1) / 2 - 10,
      y: (eastReturn.y0 + eastReturn.y1) / 2 + 10,
    },
    eastReturn.x1 - eastReturn.x0 + 20,
    eastReturn.y1 - eastReturn.y0 + 20,
    6,
    -2,
    1,
  );
  finish(context, returnNavigationGuard, materials.kitchenFront, { collide: true });
  returnNavigationGuard.isVisible = false;
  returnNavigationGuard.metadata = {
    ...(returnNavigationGuard.metadata ?? {}),
    walkCollisionOnly: true,
  };

  // Babylon's ellipsoid can slide vertically over counter-height meshes as if
  // they were a step. A single smooth, invisible vertical guard follows the
  // worktop footprint, preventing visual traversal without snag-prone detail
  // collisions on handles, plinths or the overhang.
  const penNavigationGuard = texturedBox(
    context.scene,
    `${k.id} · navigačný obrys polostrova`,
    { x: (pen.x0 + pen.x1) / 2, y: penTopCenterYmm },
    pen.x1 - pen.x0 + 20,
    penTopDepthMm,
    6,
    -2,
    1,
  );
  finish(context, penNavigationGuard, materials.kitchenFront, { collide: true });
  penNavigationGuard.isVisible = false;
  penNavigationGuard.metadata = {
    ...(penNavigationGuard.metadata ?? {}),
    walkCollisionOnly: true,
  };
  // Preserve the original cabinet module grid east of the 600 mm client cut.
  // Filtering removes only details in the deleted fridge-opposite segment.
  const originalPeninsulaX0 = fridgeUnit.x0;
  const peninsulaFrontJointsMm = [
    originalPeninsulaX0 + 900,
    originalPeninsulaX0 + 1800,
    originalPeninsulaX0 + 3100,
    originalPeninsulaX0 + 4000,
  ].filter((xMm) => xMm > pen.x0 && xMm < pen.x1);
  for (const xMm of peninsulaFrontJointsMm) {
    const joint = texturedBox(
      context.scene,
      `${k.id} · škára frontu polostrova`,
      { x: xMm, y: pen.y0 - 2 },
      4,
      4,
      counterM - worktopM - plinthM,
      plinthM,
      1,
    );
    finish(context, joint, materials.fireplace);
  }
  const peninsulaHandleCentersMm = [
    originalPeninsulaX0 + 450,
    originalPeninsulaX0 + 2450,
    originalPeninsulaX0 + 3550,
    originalPeninsulaX0 + 4375,
  ].filter((xMm) => xMm > pen.x0 && xMm < pen.x1);
  for (const xMm of peninsulaHandleCentersMm) {
    barHandle(context, materials, `${k.id} · úchytka polostrova`, { x: xMm, y: pen.y0 - 14 }, 300, true, 0.8);
  }
  const oven = texturedBox(
    context.scene,
    `${k.id} · OVEN-UNDER-HOB · vstavaná rúra pod varnou doskou`,
    { x: k.ovenCenterXmm, y: pen.y0 - 4 },
    560,
    10,
    0.595,
    0.22,
    1,
  );
  finish(context, oven, materials.blackGlass, { pickable: true });
  barHandle(
    context,
    materials,
    `${k.id} · OVEN-UNDER-HOB · madlo rúry`,
    { x: k.ovenCenterXmm, y: pen.y0 - 24 },
    480,
    true,
    0.765,
  );
  // Induction hob: black glass flush with the worktop, four ring marks.
  const hob = texturedBox(
    context.scene,
    `${k.id} · indukčná varná doska`,
    { x: k.hobCenterXmm, y: (pen.y0 + pen.y1) / 2 },
    580,
    510,
    0.006,
    counterM,
    1,
  );
  finish(context, hob, materials.blackGlass);
  for (const [dx, dy] of [[-140, -120], [140, -120], [-140, 120], [140, 120]]) {
    const ring = CreateCylinder(
      `${k.id} · varná zóna`,
      { height: 0.002, diameter: 0.2, tessellation: 32 },
      context.scene,
    );
    ring.position.set(xM(k.hobCenterXmm + dx), counterM + 0.007, zM((pen.y0 + pen.y1) / 2 + dy));
    finish(context, ring, materials.steel);
  }
  // Island extractor above the hob.
  const hood = texturedBox(
    context.scene,
    `${k.id} · ostrovný odsávač`,
    { x: k.extractorCenterXmm, y: (pen.y0 + pen.y1) / 2 },
    k.extractorWidthMm,
    500,
    0.08,
    1.6,
    1,
  );
  finish(context, hood, materials.steel, { shadow: true });
  const duct = texturedBox(
    context.scene,
    `${k.id} · komín odsávača`,
    { x: k.extractorCenterXmm, y: (pen.y0 + pen.y1) / 2 },
    300,
    300,
    1.1,
    1.68,
    1,
  );
  finish(context, duct, materials.steel);
}

/**
 * Heating equipment in room 1.07. The combined wood / pellet assembly follows
 * the proportions of the client's product reference while the typed footprint
 * remains the source of truth for fit, service floor and walk collision.
 */
export function buildTechnicalHeatingFitout(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  fitout: TechnicalHeatingFitout = HEATING_LAYOUTS[context.heatingLayout ?? DEFAULT_HEATING_LAYOUT_ID],
) {
  const boilerMeshStart=context.scene.meshes.length;
  const installed = fitout.boiler;
  const boiler = {...installed, assemblyFootprintMm:installed.model.assemblyFootprintMm,
    body:{...installed.body,footprintMm:installed.model.body}, hopper:{...installed.hopper,footprintMm:installed.model.hopper},
    burner:{footprintMm:installed.model.burner}};
  const assemblyRect = boiler.assemblyFootprintMm;
  const bodyRect = boiler.body.footprintMm;
  const bodyCenter = rectCenter(bodyRect);
  const bodyHeightM = boiler.body.heightMm * MM_TO_M;
  const frontYmm = bodyRect.y1 + 10;

  for (const xMm of [bodyRect.x0 + 42, bodyRect.x1 - 42]) {
    for (const yMm of [bodyRect.y0 + 48, bodyRect.y1 - 48]) {
      const foot = CreateCylinder(
        `${fitout.id} · WOOD-PELLET-BOILER · nastaviteľná oceľová pätka`,
        { height: 0.08, diameter: 0.052, tessellation: 20 },
        context.scene,
      );
      foot.position.set(xM(xMm), 0.04, zM(yMm));
      finish(context, foot, materials.steel, { shadow: true });
    }
  }

  const boilerBody = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-PELLET-BOILER · kombinované teleso drevo alebo pelety`,
    bodyCenter,
    bodyRect.x1 - bodyRect.x0,
    bodyRect.y1 - bodyRect.y0,
    bodyHeightM - 0.08,
    0.08,
    1,
  );
  finish(context, boilerBody, materials.boilerEnamel, {
    shadow: true,
    pickable: true,
  });

  const frontWidthMm = bodyRect.x1 - bodyRect.x0 - 54;
  const frontBackplate = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-PELLET-BOILER · antracitový čelný rám`,
    { x: bodyCenter.x, y: frontYmm },
    frontWidthMm,
    22,
    1.03,
    0.1,
    1,
  );
  finish(context, frontBackplate, materials.fireplace, { shadow: true });

  for (const door of [
    { label: "horné prikladacie dvierka na kusové drevo", bottomM: 0.81, heightM: 0.25 },
    { label: "stredné spaľovacie dvierka", bottomM: 0.55, heightM: 0.22 },
    { label: "spodné popolníkové dvierka", bottomM: 0.10, heightM: 0.40 },
  ] as const) {
    const panel = texturedBox(
      context.scene,
      `${fitout.id} · WOOD-PELLET-BOILER · ${door.label}`,
      { x: bodyCenter.x, y: frontYmm + 13 },
      frontWidthMm - 24,
      18,
      door.heightM,
      door.bottomM,
      1,
    );
    finish(context, panel, materials.boilerEnamel, { shadow: true, pickable: true });
    const handle = texturedBox(
      context.scene,
      `${fitout.id} · WOOD-PELLET-BOILER · zvislé čierne madlo ${door.label}`,
      { x: bodyRect.x0 + 58, y: frontYmm + 29 },
      22,
      28,
      Math.min(0.25, door.heightM - 0.06),
      door.bottomM + 0.03,
      1,
    );
    finish(context, handle, materials.fireplace, { shadow: true });
  }

  const controlFascia = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-PELLET-BOILER · horná antracitová regulačná lišta`,
    { x: bodyCenter.x, y: frontYmm + 4 },
    bodyRect.x1 - bodyRect.x0 - 12,
    38,
    0.13,
    1.075,
    1,
  );
  finish(context, controlFascia, materials.fireplace, { shadow: true });

  const controllerStand = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-PELLET-BOILER · konzola regulátora`,
    { x: bodyCenter.x, y: bodyRect.y1 - 54 },
    86,
    92,
    0.09,
    bodyHeightM - 0.01,
    1,
  );
  finish(context, controllerStand, materials.fireplace, { shadow: true });
  const controllerBottomM = boiler.body.controllerTopElevationMm * MM_TO_M - 0.136;
  const controller = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-PELLET-BOILER · farebný regulátor palivových režimov`,
    { x: bodyCenter.x, y: bodyRect.y1 - 42 },
    236,
    178,
    0.136,
    controllerBottomM,
    1,
  );
  finish(context, controller, materials.fireplace, { shadow: true, pickable: true });
  const display = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-PELLET-BOILER · modrý displej regulácie`,
    { x: bodyCenter.x, y: bodyRect.y1 + 52 },
    164,
    10,
    0.067,
    controllerBottomM + 0.034,
    1,
  );
  finish(context, display, materials.controlDisplay);

  for (const [label, xMm, diameterM, material] of [
    ["žltá kontrolka", bodyRect.x0 + 74, 0.052, materials.warmLight],
    ["otočný regulátor", bodyRect.x1 - 74, 0.058, materials.blackGlass],
  ] as const) {
    const control = CreateCylinder(
      `${fitout.id} · WOOD-PELLET-BOILER · ${label}`,
      { height: 0.022, diameter: diameterM, tessellation: 28 },
      context.scene,
    );
    control.rotation.x = Math.PI / 2;
    control.position.set(xM(xMm), 1.145, zM(frontYmm + 28));
    finish(context, control, material, { shadow: true });
  }

  for (let index = 0; index < 9; index += 1) {
    const chainLink = CreateSphere(
      `${fitout.id} · WOOD-PELLET-BOILER · článok retiazky regulátora ťahu ${index + 1}`,
      { diameter: 0.017, segments: 12 },
      context.scene,
    );
    chainLink.position.set(
      xM(bodyRect.x1 - 28),
      1.08 - index * 0.072,
      zM(frontYmm + 38 + index * 2),
    );
    finish(context, chainLink, materials.steel);
  }

  const hopper = boiler.hopper;
  const hopperRect = hopper.footprintMm;
  const hopperCenter = rectCenter(hopperRect);
  for (const xMm of [hopperRect.x0 + 48, hopperRect.x1 - 48]) {
    for (const yMm of [hopperRect.y0 + 66, hopperRect.y1 - 66]) {
      const leg = texturedBox(
        context.scene,
        `${fitout.id} · PELLET-HOPPER · oceľová noha zásobníka`,
        { x: xMm, y: yMm },
        38,
        38,
        0.69,
        0,
        1,
      );
      finish(context, leg, materials.steel, { shadow: true });
    }
  }
  const hopperCone = CreateCylinder(
    `${fitout.id} · PELLET-HOPPER · štvorboké lievikové dno`,
    { height: 0.4, diameterTop: 1, diameterBottom: 0.34, tessellation: 4 },
    context.scene,
  );
  hopperCone.rotation.y = Math.PI / 4;
  hopperCone.scaling.set(0.58, 1, 0.82);
  hopperCone.position.set(xM(hopperCenter.x), 0.49, zM(hopperCenter.y));
  finish(context, hopperCone, materials.boilerEnamel, { shadow: true });
  const hopperBody = texturedBox(
    context.scene,
    `${fitout.id} · PELLET-HOPPER · zásobník peliet približne ${hopper.nominalPelletCapacityKg} kg`,
    hopperCenter,
    hopperRect.x1 - hopperRect.x0,
    hopperRect.y1 - hopperRect.y0,
    (hopper.heightMm-745)*MM_TO_M,
    0.69,
    1,
  );
  finish(context, hopperBody, materials.boilerEnamel, { shadow: true, pickable: true });
  const hopperLid = texturedBox(
    context.scene,
    `${fitout.id} · PELLET-HOPPER · výklopné plniace veko`,
    { x: hopperCenter.x, y: hopperCenter.y - 12 },
    hopperRect.x1 - hopperRect.x0 - 34,
    hopperRect.y1 - hopperRect.y0 - 34,
    0.045,
    hopper.heightMm * MM_TO_M - 0.060,
    1,
  );
  hopperLid.rotation.x = 0;
  finish(context, hopperLid, materials.boilerEnamel, { shadow: true, pickable: true });
  const hopperGrip = texturedBox(
    context.scene,
    `${fitout.id} · PELLET-HOPPER · madlo plniaceho veka`,
    { x: hopperCenter.x, y: hopperRect.y1 - 76 },
    190,
    24,
    0.025,
    hopper.heightMm * MM_TO_M - 0.025,
    1,
  );
  finish(context, hopperGrip, materials.fireplace, { shadow: true });

  // The feeder rises in front of the separate hopper, outside the boiler body.
  // L extends beyond K on this side of the manufacturer's dimensioned drawing.
  // Mounting proposal for the separate auger; length/incline need supplier confirmation.
  const augerOutlet={x:fitout.boiler.feeder.outletAcrossMm,y:assemblyRect.y1-155/2,elevationM:1.09};
  // Change the side of the pellet accessories without mirroring boiler hinges or controls.
  const accessoryDirection=fitout.boiler.feeder.accessoryDirection;
  const augerPath = [
    new Vector3(xM(hopperCenter.x + accessoryDirection*22), 0.34, zM(hopperCenter.y + 10)),
    new Vector3(xM(augerOutlet.x),augerOutlet.elevationM,zM(augerOutlet.y)),
  ];
  const auger = CreateTube(
    `${fitout.id} · PELLET-AUGER · šikmý šnekový podávač`,
    { path: augerPath, radius: 0.055, tessellation: 22, cap: Mesh.CAP_ALL },
    context.scene,
  );
  finish(context, auger, materials.steel, { shadow: true, pickable: true });
  const augerMotor = texturedBox(
    context.scene,
    `${fitout.id} · PELLET-AUGER · motor s prevodovkou`,
    { x:augerOutlet.x,y:augerOutlet.y },
    155,
    155,
    0.19,
    0.98,
    1,
  );
  finish(context, augerMotor, materials.fireplace, { shadow: true, pickable: true });

  const burnerRect = boiler.burner.footprintMm;
  const burnerSpec=fitout.boiler.burner;
  const burnerCenter = rectCenter({...burnerRect,y0:burnerRect.y0+burnerSpec.neckLengthMm});
  const burnerNeck=texturedBox(context.scene,`${fitout.id} · PELLET-BURNER · pripojovací krčok zatvorených dvierok`,
    {x:burnerCenter.x,y:burnerRect.y0+burnerSpec.neckLengthMm/2},120,burnerSpec.neckLengthMm,.13,.295,1);
  finish(context,burnerNeck,materials.steel,{shadow:true,pickable:true});
  const burnerBody = texturedBox(
    context.scene,
    `${fitout.id} · PELLET-BURNER · automaticky čistený peletový horák`,
    burnerCenter,
    burnerRect.x1 - burnerRect.x0,
    burnerSpec.housingDepthMm,
    burnerSpec.heightMm*MM_TO_M,
    burnerSpec.bottomMm*MM_TO_M,
    1,
  );
  finish(context, burnerBody, materials.fireplace, { shadow: true, pickable: true });
  const burnerFace = texturedBox(
    context.scene,
    `${fitout.id} · PELLET-BURNER · čelný servisný kryt`,
    { x: burnerCenter.x, y: burnerRect.y1 - 12 },
    burnerRect.x1 - burnerRect.x0 - 44,
    20,
    0.20,
    0.26,
    1,
  );
  finish(context, burnerFace, materials.boilerEnamel, { shadow: true, pickable: true });
  const burnerWindow = texturedBox(
    context.scene,
    `${fitout.id} · PELLET-BURNER · kontrolné okienko plameňa`,
    { x: burnerCenter.x - 32, y: burnerRect.y1 - 5 },
    80,
    8,
    0.055,
    0.34,
    1,
  );
  finish(context, burnerWindow, materials.blackGlass);

  const hoseStart = { x:augerOutlet.x+accessoryDirection*75,elevationM:augerOutlet.elevationM,y:augerOutlet.y };
  const hoseControl = { x: accessoryDirection>0?bodyRect.x1+86:bodyRect.x0-86, elevationM: 1.03, y: frontYmm + 74 };
  const hoseEnd = { x: burnerCenter.x, elevationM: (burnerSpec.bottomMm+burnerSpec.heightMm)*MM_TO_M, y: burnerRect.y0 + 195 };
  const hosePath = Array.from({ length: 13 }, (_, index) => {
    const t = index / 12;
    const oneMinusT = 1 - t;
    return new Vector3(
      xM(oneMinusT ** 2 * hoseStart.x + 2 * oneMinusT * t * hoseControl.x + t ** 2 * hoseEnd.x),
      oneMinusT ** 2 * hoseStart.elevationM
        + 2 * oneMinusT * t * hoseControl.elevationM
        + t ** 2 * hoseEnd.elevationM,
      zM(oneMinusT ** 2 * hoseStart.y + 2 * oneMinusT * t * hoseControl.y + t ** 2 * hoseEnd.y),
    );
  });
  const feedHose = CreateTube(
    `${fitout.id} · PELLET-FEED-HOSE · pružná jantárová podávacia hadica`,
    { path: hosePath, radius: 0.038, tessellation: 24, cap: Mesh.CAP_ALL },
    context.scene,
  );
  // A convex hull fills the inside of this bend and looks like an open door in plan.
  // Preserve its actual projected triangles while retaining the hull for conservative bounds.
  feedHose.metadata={...feedHose.metadata,planProjection:'TRIANGLE_SILHOUETTE'};
  finish(context, feedHose, materials.pelletFeedHose, { shadow: true, pickable: true });

  const flueCollar = CreateCylinder(
    `${fitout.id} · WOOD-PELLET-BOILER · dymovodné hrdlo`,
    { height: 0.06, diameter: 0.23, tessellation: 32 },
    context.scene,
  );
  flueCollar.rotation.x=Math.PI/2;
  flueCollar.position.set(xM(bodyCenter.x), .964, zM(bodyRect.y0-30));
  finish(context, flueCollar, materials.fireplace);
  const flueStub = CreateCylinder(
    `${fitout.id} · WOOD-PELLET-BOILER · výrobné zadné hrdlo 139 mm · Ø${boiler.flueOutletDiameterMm}`,
    { height: (bodyRect.y0-assemblyRect.y0)*MM_TO_M, diameter: boiler.flueOutletDiameterMm * MM_TO_M, tessellation: 32 },
    context.scene,
  );
  flueStub.rotation.x=Math.PI/2;
  flueStub.position.set(xM(bodyCenter.x), .964, zM((bodyRect.y0+assemblyRect.y0)/2));
  finish(context, flueStub, materials.fireplace);

  // Retain the factory outlet. The installation elbow and vertical rise are
  // separate from the catalogue envelope and stop at the ceiling connection.
  const flue=fitout.flue,fluePath=Array.from({length:25},(_,index)=>{
    const angle=index/24*Math.PI/2;
    return new Vector3(xM(bodyCenter.x),
      (flue.outletElevationMm+flue.elbowCenterlineRadiusMm*(1-Math.cos(angle)))*MM_TO_M,
      zM(-flue.stockRearProjectionMm-flue.elbowCenterlineRadiusMm*Math.sin(angle)));
  });
  fluePath.push(new Vector3(xM(bodyCenter.x),(flue.topElevationMm-boiler.baseElevationMm)*MM_TO_M,
    zM(-flue.stockRearProjectionMm-flue.elbowCenterlineRadiusMm)));
  const flueRise=CreateTube(`${fitout.id} · BOILER-FLUE · koleno nahor a zvislý dymovod · montážny návrh`,
    {path:fluePath,radius:flue.diameterMm/2*MM_TO_M,tessellation:32,cap:Mesh.CAP_START},context.scene);
  finish(context,flueRise,materials.fireplace,{shadow:true,pickable:true});

  for(const [name,r] of [['teleso',bodyRect],['zásobník',hopper.footprintMm],['horák',burnerRect]] as const)
    navigationGuard(context,materials,`${fitout.id} · WOOD-PELLET-ASSEMBLY · navigačný obrys ${name}`,r);
  for(const mesh of context.scene.meshes.slice(boilerMeshStart))mesh.position.y+=boiler.baseElevationMm*MM_TO_M;
  for(const [name,r] of [['teleso',bodyRect],['zásobník',hopperRect]] as const){
    const base=texturedBox(context.scene,`${fitout.id} · BOILER-BASE · nehorľavý podstavec 50 mm · ${name}`,rectCenter(r),r.x1-r.x0,r.y1-r.y0,.05,0,1);
    finish(context,base,materials.steel,{shadow:true});
  }

  const boilerRoot=new TransformNode(`${fitout.id} · orientácia kotla`,context.scene);
  boilerRoot.position.set(xM(0),0,zM(0));
  for(const mesh of context.scene.meshes.slice(boilerMeshStart))mesh.setParent(boilerRoot);
  boilerRoot.scaling.x=installed.mirrorX?-1:1;
  boilerRoot.rotation.y=installed.rotationDegrees*Math.PI/180;
  boilerRoot.position.set(xM(installed.originMm.x),0,zM(installed.originMm.y));

  const tank = fitout.accumulator;
  const tankRadiusMm = tank.outerDiameterMm / 2;
  const tankHeightM = tank.heightMm * MM_TO_M;
  const tankBase = CreateCylinder(
    `${fitout.id} · BUFFER-TANK-${tank.nominalVolumeL}L · podstavec`,
    { height: 0.08, diameter: tank.outerDiameterMm * MM_TO_M - 0.08, tessellation: 48 },
    context.scene,
  );
  tankBase.position.set(xM(tank.centerMm.x), 0.04, zM(tank.centerMm.y));
  finish(context, tankBase, materials.fireplace, { shadow: true });
  const tankBody = CreateCylinder(
    `${fitout.id} · BUFFER-TANK-${tank.nominalVolumeL}L · akumulačná nádrž ${tank.nominalVolumeL} l`,
    {
      height: tankHeightM - 0.14,
      diameter: tank.outerDiameterMm * MM_TO_M,
      tessellation: 48,
    },
    context.scene,
  );
  tankBody.position.set(xM(tank.centerMm.x), 0.08 + (tankHeightM - 0.14) / 2, zM(tank.centerMm.y));
  finish(context, tankBody, materials.tankJacket, {
    collide: true,
    shadow: true,
    pickable: true,
  });
  const tankTop = CreateCylinder(
    `${fitout.id} · BUFFER-TANK-${tank.nominalVolumeL}L · horné izolované veko`,
    {
      height: 0.08,
      diameterBottom: tank.outerDiameterMm * MM_TO_M,
      diameterTop: tank.outerDiameterMm * MM_TO_M - 0.16,
      tessellation: 48,
    },
    context.scene,
  );
  tankTop.position.set(xM(tank.centerMm.x), tankHeightM - 0.04, zM(tank.centerMm.y));
  finish(context, tankTop, materials.tankJacket, { shadow: true });
  for (const elevationM of [0.58, 1.48]) {
    const band = CreateCylinder(
      `${fitout.id} · BUFFER-TANK-${tank.nominalVolumeL}L · oceľová obruč`,
      { height: 0.028, diameter: tank.outerDiameterMm * MM_TO_M - 0.002, tessellation: 48 },
      context.scene,
    );
    band.position.set(xM(tank.centerMm.x), elevationM, zM(tank.centerMm.y));
    finish(context, band, materials.steel);
  }
  const connectionStart = context.scene.meshes.length;
  for (const [index, elevationM, yOffsetMm] of [
    [1, 0.34, -245],
    [2, 0.78, 245],
    [3, 1.22, -245],
    [4, 1.66, 245],
  ] as const) {
    const rootX = Math.sqrt(tankRadiusMm ** 2 - yOffsetMm ** 2) - 5;
    const tipX = tankRadiusMm + tank.connectionProjectionMm;
    const nozzle = CreateCylinder(
      `${fitout.id} · BUFFER-TANK-${tank.nominalVolumeL}L · hydraulické hrdlo ${index}`,
      { height: (tipX - rootX) * MM_TO_M, diameter: 0.055, tessellation: 20 },
      context.scene,
    );
    nozzle.rotation.z = Math.PI / 2;
    nozzle.position.set(
      xM(tank.centerMm.x + (rootX + tipX) / 2),
      elevationM,
      zM(tank.centerMm.y + yOffsetMm),
    );
    finish(context, nozzle, materials.copperPipe);
  }
  const airVent = CreateCylinder(
    `${fitout.id} · BUFFER-TANK-${tank.nominalVolumeL}L · automatický odvzdušňovač`,
    { height: 0.12, diameter: 0.045, tessellation: 20 },
    context.scene,
  );
  airVent.position.set(xM(tank.centerMm.x), tankHeightM + 0.06, zM(tank.centerMm.y));
  finish(context, airVent, materials.brushedBrass);
  const gaugeRim = CreateCylinder(
    `${fitout.id} · BUFFER-TANK-${tank.nominalVolumeL}L · teplomer`,
    { height: 0.045, diameter: 0.13, tessellation: 32 },
    context.scene,
  );
  gaugeRim.rotation.z = Math.PI / 2;
  gaugeRim.position.set(
    xM(tank.centerMm.x + tankRadiusMm + 18),
    1.45,
    zM(tank.centerMm.y),
  );
  finish(context, gaugeRim, materials.steel);
  const gaugeFace = CreateCylinder(
    `${fitout.id} · BUFFER-TANK-${tank.nominalVolumeL}L · ciferník teplomera`,
    { height: 0.012, diameter: 0.102, tessellation: 32 },
    context.scene,
  );
  gaugeFace.rotation.z = Math.PI / 2;
  gaugeFace.position.set(
    xM(tank.centerMm.x + tankRadiusMm + 43),
    1.45,
    zM(tank.centerMm.y),
  );
  finish(context, gaugeFace, materials.kitchenUpper);
  // Turn the connection bank into the right service aisle, clear of the kitchen entrance.
  // Keep the circular jacket independent so its exported diameter stays exact.
  const connectionRoot = new TransformNode(`${fitout.id} · orientácia prípojok nádrže`, context.scene);
  connectionRoot.position.set(xM(tank.centerMm.x), 0, zM(tank.centerMm.y));
  for (const mesh of context.scene.meshes.slice(connectionStart)) mesh.setParent(connectionRoot);
  connectionRoot.rotation.y = tank.connectionAzimuthDegrees * Math.PI / 180;
  buildTechnicalStorageReserve(context,materials,fitout);
  buildTechnicalShelving(context,materials,fitout);
}

/** A usable shallow rack on the wall freed by moving the exterior opening. */
function buildTechnicalShelving(context:InteriorBuildContext,materials:InteriorMaterials,fitout:TechnicalHeatingFitout){
  const shelving=fitout.shelving,r=shelving.footprintMm,c=rectCenter(r);
  const box=(label:string,center:Point2Mm,width:number,depth:number,height:number,bottom:number)=>{
    const mesh=texturedBox(context.scene,`${shelving.id} · OPEN-SHELVING · ${label}`,center,width,depth,height*MM_TO_M,bottom*MM_TO_M,1);
    finish(context,mesh,materials.steel,{shadow:true,pickable:true});
  };
  for(const x of [r.x0+10,r.x1-10])for(const y of [r.y0+10,r.y1-10])
    box('oceľová stojka',{x,y},20,20,shelving.heightMm,0);
  for(let i=0;i<shelving.shelfCount;i++)box(`polica ${i+1}`,c,r.x1-r.x0,r.y1-r.y0,18,120+i*420);
  for(const z of [420,1260,1940])box('zadná výstuha',{x:r.x1-10,y:c.y},20,r.y1-r.y0,25,z);
  navigationGuard(context,materials,`${shelving.id} · OPEN-SHELVING · navigačný obrys`,r);
}

/** Space allocations are visible, but never presented as certified fire compartments. */
function buildTechnicalStorageReserve(context:InteriorBuildContext,materials:InteriorMaterials,fitout:TechnicalHeatingFitout){
  const meshStart=context.scene.meshes.length;
  const storage=fitout.storage,installed=storage.footprintMm,c=rectCenter(installed);
  // Build the 720 × 261 cabinet in its canonical frame, then face it west.
  const r={x0:c.x-360,x1:c.x+360,y0:c.y-130.5,y1:c.y+130.5};
  const box=(name:string,center:Point2Mm,w:number,d:number,h:number,bottom:number,material=materials.steel)=>{
    const mesh=texturedBox(context.scene,`${storage.id} · ${name}`,center,w,d,h*MM_TO_M,bottom*MM_TO_M,1);
    finish(context,mesh,material,{shadow:true,pickable:true});return mesh;
  };
  const width=r.x1-r.x0,depth=r.y1-r.y0,bagCenter={x:r.x0+196,y:c.y},vacuumCenter={x:r.x0+548,y:c.y};
  box('STORAGE-CABINET · chrbát plytkej servisnej skrine',{x:c.x,y:r.y1-8},width,16,storage.heightMm,0);
  for(const x of [r.x0+8,r.x1-8])box('STORAGE-CABINET · oceľová bočnica',{x,y:c.y},16,depth,storage.heightMm,0);
  for(const z of [30,storage.heightMm-16])box('STORAGE-CABINET · oceľová polica',c,width-32,depth-32,16,z);
  box('STORAGE-CABINET · zvislé oddelenie vysávača',{x:r.x0+384,y:c.y},16,depth-32,storage.heightMm-32,16);
  for(const z of [540,1040,1540])box('STORAGE-CABINET · polica pre zvislé vrecia',bagCenter,360,depth-32,16,z);
  // A tambour front leaves the full shared approach clear at all times.
  for(let z=0;z<storage.heightMm;z+=100)box('STORAGE-CABINET · posuvné roletové čelo',{x:c.x,y:r.y0+8},width-32,16,Math.min(96,storage.heightMm-z),z);
  const vacuum=storage.vacuumSizeMm;
  box('VACUUM · podlahová hubica tyčového vysávača',vacuumCenter,vacuum.width,vacuum.depth,60,70,materials.fireplace);
  box('VACUUM · zvislá trubica',{x:vacuumCenter.x,y:c.y+20},30,35,830,130,materials.steel);
  box('VACUUM · motor a zberná nádoba',{x:vacuumCenter.x,y:c.y+10},105,100,215,820,materials.fireplace);
  box('VACUUM · horné držadlo',{x:vacuumCenter.x,y:c.y+15},85,45,140,1035,materials.steel);
  box('VACUUM · nástenný držiak, napájanie na dopracovanie',{x:vacuumCenter.x,y:r.y1-35},120,30,45,1100,materials.steel);
  for(let i=0;i<storage.pelletBagCount;i++)box(`PELLET-BAG-${i+1} · zvislo uložené vrece peliet 15 kg`,bagCenter,storage.bagSizeMm.width,storage.bagSizeMm.depth,storage.bagSizeMm.height,i===0?46:56+i*500,materials.childCork);
  navigationGuard(context,materials,`${storage.id} · STORAGE-CABINET · navigačný obrys`,r);
  const h=fitout.hydraulicReserve;
  // Reserved upper compartment; product selection and pipework remain separate.
  for(const y of [r.y0+10,r.y1-10])for(const x of [r.x0+10,r.x1-10])
    box('HYDRAULIC-RESERVE · rám hornej hydraulickej rezervy',{x,y},20,20,h.heightMm,h.bottomMm);
  const k=h.safetyGroupMm;
  box('SAFETY-GROUP · KSG mini 2,5 bar',{x:r.x0+150,y:r.y1-55},k.width,k.depth,k.height,1950,materials.fireplace);
  // The entire cabinet, contents, hydraulic reserve and collision guard share
  // one orientation, including their collision guard.
  const root=new TransformNode(`${storage.id} · orientácia skrine`,context.scene);
  root.position.set(xM(c.x),0,zM(c.y));
  for(const mesh of context.scene.meshes.slice(meshStart))mesh.setParent(root);
  root.rotation.y=-Math.PI/2;
}

/** Practical long-axis fitout for the enlarged room 1.06. */
function buildWcFitout(context: InteriorBuildContext, materials: InteriorMaterials) {
  const fitout = WC_FITOUT;
  const toilet = fitout.toilet;
  const toiletCenter: Point2Mm = {
    x: (toilet.footprintMm.x0 + toilet.footprintMm.x1) / 2,
    y: (toilet.footprintMm.y0 + toilet.footprintMm.y1) / 2,
  };

  const cistern = texturedBox(
    context.scene,
    `${fitout.id} · WALL-HUNG-WC · obložený modul podomietkovej nádržky`,
    rectCenter(toilet.concealedCisternRectMm),
    toilet.concealedCisternRectMm.x1 - toilet.concealedCisternRectMm.x0,
    toilet.concealedCisternRectMm.y1 - toilet.concealedCisternRectMm.y0,
    1.15,
    0,
    1.2,
  );
  finish(context, cistern, materials.wallTile, { shadow: true, pickable: true });
  const cisternCap = texturedBox(
    context.scene,
    `${fitout.id} · WALL-HUNG-WC · horná doska modulu`,
    rectCenter(toilet.concealedCisternRectMm),
    toilet.concealedCisternRectMm.x1 - toilet.concealedCisternRectMm.x0 + 12,
    toilet.concealedCisternRectMm.y1 - toilet.concealedCisternRectMm.y0 + 12,
    0.025,
    1.15,
    1,
  );
  finish(context, cisternCap, materials.sanitaryCeramic, { shadow: true });
  const flushPlate = texturedBox(
    context.scene,
    `${fitout.id} · WALL-HUNG-WC · dvojité splachovacie tlačidlo`,
    { x: toiletCenter.x, y: toilet.concealedCisternRectMm.y1 + 5 },
    185,
    10,
    0.11,
    0.84,
    1,
  );
  finish(context, flushPlate, materials.steel, { pickable: true });
  for (const xOffsetMm of [-42, 42]) {
    const button = CreateCylinder(
      `${fitout.id} · WALL-HUNG-WC · tlačidlo splachovania`,
      { height: 0.012, diameter: xOffsetMm < 0 ? 0.052 : 0.038, tessellation: 24 },
      context.scene,
    );
    button.rotation.x = Math.PI / 2;
    button.position.set(
      xM(toiletCenter.x + xOffsetMm),
      0.895,
      zM(toilet.concealedCisternRectMm.y1 + 12),
    );
    finish(context, button, materials.blackGlass);
  }

  softEllipsoid(
    context,
    `${fitout.id} · WALL-HUNG-WC · keramická misa`,
    { x: toiletCenter.x, y: toiletCenter.y },
    [0.37, 0.28, 0.52],
    0.32,
    materials.sanitaryCeramic,
  );
  softEllipsoid(
    context,
    `${fitout.id} · WALL-HUNG-WC · vnútro misy`,
    { x: toiletCenter.x, y: toiletCenter.y + 55 },
    [0.2, 0.024, 0.31],
    0.455,
    materials.mirrorGlass,
  );
  const toiletSeat = CreateTorus(
    `${fitout.id} · WALL-HUNG-WC · tenké sedadlo`,
    { diameter: 0.355, thickness: 0.035, tessellation: 40 },
    context.scene,
  );
  toiletSeat.position.set(
    xM(toiletCenter.x),
    toilet.seatElevationMm * MM_TO_M,
    zM(toiletCenter.y),
  );
  toiletSeat.scaling.set(0.94, 0.68, 1.28);
  finish(context, toiletSeat, materials.sanitaryCeramic, { shadow: true, pickable: true });

  const basin = fitout.basin;
  const basinCenter: Point2Mm = {
    x: (basin.footprintMm.x0 + basin.footprintMm.x1) / 2,
    y: (basin.footprintMm.y0 + basin.footprintMm.y1) / 2,
  };
  const basinWidth=basin.footprintMm.x1-basin.footprintMm.x0,basinLength=basin.footprintMm.y1-basin.footprintMm.y0;
  softEllipsoid(
    context,
    `${fitout.id} · COMPACT-BASIN · keramické umývadlo ${basinLength} × ${basinWidth}`,
    basinCenter,
    [basinWidth*MM_TO_M, 0.16, basinLength*MM_TO_M],
    0.77,
    materials.sanitaryCeramic,
  );
  softEllipsoid(
    context,
    `${fitout.id} · COMPACT-BASIN · vnútorná misa`,
    { x: basinCenter.x - 18, y: basinCenter.y },
    [(basinWidth-60)*MM_TO_M, 0.025, (basinLength-90)*MM_TO_M],
    basin.rimElevationMm * MM_TO_M + 0.008,
    materials.mirrorGlass,
  );
  const basinRim = CreateTorus(
    `${fitout.id} · COMPACT-BASIN · oválny keramický lem`,
    { diameter: 0.285, thickness: 0.026, tessellation: 40 },
    context.scene,
  );
  basinRim.position.set(
    xM(basinCenter.x),
    basin.rimElevationMm * MM_TO_M + 0.018,
    zM(basinCenter.y),
  );
  basinRim.scaling.set((basinWidth-24)/311, 0.65, (basinLength-24)/311);
  finish(context, basinRim, materials.sanitaryCeramic, { shadow: true });
  const drain = CreateCylinder(
    `${fitout.id} · COMPACT-BASIN · chrómový odtok`,
    { height: 0.008, diameter: 0.052, tessellation: 24 },
    context.scene,
  );
  drain.position.set(
    xM(basinCenter.x - 38),
    basin.rimElevationMm * MM_TO_M + 0.024,
    zM(basinCenter.y),
  );
  finish(context, drain, materials.steel);
  const tapRiser = CreateCylinder(
    `${fitout.id} · COMPACT-BASIN · stojanková batéria`,
    { height: 0.18, diameter: 0.027, tessellation: 20 },
    context.scene,
  );
  tapRiser.position.set(xM(basin.footprintMm.x1 - 68), 0.95, zM(basinCenter.y));
  finish(context, tapRiser, materials.steel);
  const tapSpout = CreateCylinder(
    `${fitout.id} · COMPACT-BASIN · výtok batérie`,
    { height: 0.14, diameter: 0.021, tessellation: 20 },
    context.scene,
  );
  tapSpout.rotation.z = Math.PI / 2;
  tapSpout.position.set(xM(basin.footprintMm.x1 - 130), 1.03, zM(basinCenter.y));
  finish(context, tapSpout, materials.steel);
  const trap = CreateCylinder(
    `${fitout.id} · COMPACT-BASIN · pohľadový sifón`,
    { height: 0.28, diameter: 0.045, tessellation: 20 },
    context.scene,
  );
  trap.position.set(xM(basinCenter.x + 12), 0.56, zM(basinCenter.y));
  finish(context, trap, materials.steel);
  const mirrorFrame = texturedBox(
    context.scene,
    `${fitout.id} · COMPACT-BASIN · zrkadlo s tenkým rámom`,
    { x: basin.footprintMm.x1 - 6, y: basinCenter.y },
    14,
    420,
    0.68,
    1.08,
    1,
  );
  finish(context, mirrorFrame, materials.fireplace, { shadow: true });
  const mirror = texturedBox(
    context.scene,
    `${fitout.id} · COMPACT-BASIN · zrkadlová plocha`,
    { x: basin.footprintMm.x1 - 14, y: basinCenter.y },
    7,
    390,
    0.64,
    1.1,
    1,
  );
  finish(context, mirror, materials.mirrorGlass, { pickable: true });

  navigationGuard(
    context,
    materials,
    `${fitout.id} · WALL-HUNG-WC · hladký navigačný obrys`,
    toilet.footprintMm,
  );
  navigationGuard(
    context,
    materials,
    `${fitout.id} · COMPACT-BASIN · hladký navigačný obrys`,
    basin.footprintMm,
  );
}

type BathroomLaundryAppliance =
  (typeof BATHROOM_FITOUT.builtIn.appliances)[number];

/** One real pivoted drum door, registered in the same controller as house doors. */
function buildStackedLaundryAppliance(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  fitoutId: string,
  run: RectMm,
  appliance: BathroomLaundryAppliance,
) {
  const center = rectCenter(appliance.footprintMm);
  const label = appliance.kind === "WASHER" ? "Práčka" : "Sušička";
  const token = appliance.kind === "WASHER" ? "WASHER" : "DRYER";
  const body = texturedBox(
    context.scene,
    `${fitoutId} · LAUNDRY-TOWER · ${token} · ${label.toLocaleLowerCase("sk-SK")}`,
    { x: center.x, y: run.y0 - 4 },
    570,
    26,
    appliance.heightMm * MM_TO_M,
    appliance.baseElevationMm * MM_TO_M,
    1,
  );
  body.metadata = { ...(body.metadata ?? {}), applianceId: appliance.id };
  finish(context, body, materials.applianceEnamel, {
    shadow: true,
    pickable: true,
  });

  const controlsElevationM =
    (appliance.baseElevationMm + appliance.heightMm - 105) * MM_TO_M;
  const controls = texturedBox(
    context.scene,
    `${fitoutId} · LAUNDRY-TOWER · ${token} · ovládací panel`,
    { x: center.x + 145, y: run.y0 - 34 },
    150,
    16,
    0.06,
    controlsElevationM,
    1,
  );
  finish(context, controls, materials.blackGlass, { pickable: true });
  const selector = CreateCylinder(
    `${fitoutId} · LAUNDRY-TOWER · ${token} · volič programu`,
    { height: 0.024, diameter: 0.06, tessellation: 24 },
    context.scene,
  );
  selector.rotation.x = Math.PI / 2;
  selector.position.set(
    xM(center.x - 150),
    controlsElevationM + 0.03,
    zM(run.y0 - 43),
  );
  finish(context, selector, materials.applianceEnamel, { pickable: true });

  const frontPlanYmm = run.y0 - 45;
  const radiusM = appliance.door.diameterMm * MM_TO_M / 2;
  const hingeXmm = center.x - appliance.door.diameterMm / 2;
  const hinge = new TransformNode(
    `${fitoutId} · LAUNDRY-TOWER · ${token} · pánt dvierok`,
    context.scene,
  );
  hinge.position.set(
    xM(hingeXmm),
    appliance.door.centerElevationMm * MM_TO_M,
    zM(frontPlanYmm),
  );
  hinge.metadata = {
    doorId: appliance.door.id,
    doorMotion: "HINGED",
    doorSubject: "APPLIANCE_DOOR",
  };

  const doorMetadata = {
    doorId: appliance.door.id,
    doorMotion: "HINGED",
    doorSubject: "APPLIANCE_DOOR",
    dynamicCameraOccluder: true,
  };
  const doorRim = CreateCylinder(
    `${fitoutId} · LAUNDRY-TOWER · ${token} · otváravé dvierka · rám`,
    {
      height: 0.05,
      diameter: appliance.door.diameterMm * MM_TO_M,
      tessellation: 48,
    },
    context.scene,
  );
  doorRim.rotation.x = Math.PI / 2;
  doorRim.parent = hinge;
  doorRim.position.set(radiusM, 0, 0);
  doorRim.metadata = doorMetadata;
  finish(context, doorRim, materials.applianceEnamel, {
    collide: true,
    shadow: true,
    pickable: true,
    cameraOccluder: true,
    entityId: appliance.door.id,
  });

  const doorGlass = CreateCylinder(
    `${fitoutId} · LAUNDRY-TOWER · ${token} · otváravé dvierka · sklo`,
    {
      height: 0.042,
      diameter: (appliance.door.diameterMm - 90) * MM_TO_M,
      tessellation: 48,
    },
    context.scene,
  );
  doorGlass.rotation.x = Math.PI / 2;
  doorGlass.parent = hinge;
  doorGlass.position.set(radiusM, 0, 0.024);
  doorGlass.metadata = doorMetadata;
  finish(context, doorGlass, materials.blackGlass, {
    shadow: true,
    pickable: true,
    cameraOccluder: true,
    entityId: appliance.door.id,
  });

  const latch = CreateBox(
    `${fitoutId} · LAUNDRY-TOWER · ${token} · madlo dvierok`,
    { width: 0.075, height: 0.028, depth: 0.055 },
    context.scene,
  );
  latch.parent = hinge;
  latch.position.set(radiusM * 1.84, 0, 0.035);
  latch.metadata = doorMetadata;
  finish(context, latch, materials.steel, {
    shadow: true,
    pickable: true,
    entityId: appliance.door.id,
  });

  const openAngleRad = -(appliance.door.openAngleDegrees * Math.PI) / 180;
  const hingeWorld = { x: xM(hingeXmm), z: zM(frontPlanYmm) };
  const closedEndWorld = {
    x: xM(hingeXmm + appliance.door.diameterMm),
    z: zM(frontPlanYmm),
  };
  context.registerAnimatedDoor?.({
    id: appliance.door.id,
    label,
    kind: "HINGED",
    subject: "APPLIANCE_DOOR",
    interactionPoint: {
      x: xM(center.x),
      y: appliance.door.centerElevationMm * MM_TO_M,
      z: zM(frontPlanYmm),
    },
    apply: (progress) => {
      hinge.rotation.y = openAngleRad * progress;
      doorRim.computeWorldMatrix(true);
      doorGlass.computeWorldMatrix(true);
      latch.computeWorldMatrix(true);
    },
    canOpen: (actor, progress = 0) =>
      hingedDoorSweepIsClear(
        actor,
        hingeWorld,
        closedEndWorld,
        openAngleRad,
        0.05,
        progress,
        1,
      ),
    canClose: (actor, progress = 1) =>
      hingedDoorSweepIsClear(
        actor,
        hingeWorld,
        closedEndWorld,
        openAngleRad,
        0.05,
        progress,
        0,
      ),
  });
}

/**
 * Final client fitout for the L-shaped bathroom/laundry 1.05. The small east
 * window terminates a premium walk-in shower, while the complete north recess
 * reads as one fitted furniture wall with a black basin and white appliances.
 */
function buildBathroomFitout(context: InteriorBuildContext, materials: InteriorMaterials) {
  const fitout = BATHROOM_FITOUT;
  const shower = fitout.shower;

  const showerFeatureWall = texturedBox(
    context.scene,
    `${fitout.id} · WALK-IN-1250 · tmavá veľkoformátová stena pod oknom`,
    { x: shower.footprintMm.x1 - 12, y: (shower.footprintMm.y0 + shower.footprintMm.y1) / 2 },
    24,
    shower.footprintMm.y1 - shower.footprintMm.y0,
    1.7,
    0,
    1.2,
  );
  finish(context, showerFeatureWall, materials.mediaPanel, { shadow: true });
  const showerFeatureLed = texturedBox(
    context.scene,
    `${fitout.id} · WALK-IN-1250 · nepriame svetlo pod vysokým oknom`,
    { x: shower.footprintMm.x1 - 27, y: (shower.footprintMm.y0 + shower.footprintMm.y1) / 2 },
    12,
    shower.footprintMm.y1 - shower.footprintMm.y0 - 80,
    0.012,
    1.685,
    1,
  );
  finish(context, showerFeatureLed, materials.warmLight);

  const showerFloor = texturedBox(
    context.scene,
    `${fitout.id} · WALK-IN-1250 · bezprahová sprchová plocha`,
    rectCenter(shower.footprintMm),
    shower.footprintMm.x1 - shower.footprintMm.x0,
    shower.footprintMm.y1 - shower.footprintMm.y0,
    0.012,
    0.001,
    0.6,
  );
  finish(context, showerFloor, materials.wallTile, { pickable: true });
  const drain = texturedBox(
    context.scene,
    `${fitout.id} · WALK-IN-1250 · lineárny nerezový žľab`,
    rectCenter(shower.linearDrainMm),
    shower.linearDrainMm.x1 - shower.linearDrainMm.x0,
    shower.linearDrainMm.y1 - shower.linearDrainMm.y0,
    0.008,
    0.014,
    1,
  );
  finish(context, drain, materials.steel, { pickable: true });
  for (let slot = 0; slot < 6; slot += 1) {
    const drainSlot = texturedBox(
      context.scene,
      `${fitout.id} · WALK-IN-1250 · štrbina žľabu ${slot + 1}`,
      {
        x: shower.linearDrainMm.x0 + 20 + slot * 11,
        y: (shower.linearDrainMm.y0 + shower.linearDrainMm.y1) / 2,
      },
      4,
      shower.linearDrainMm.y1 - shower.linearDrainMm.y0 - 40,
      0.004,
      0.023,
      1,
    );
    finish(context, drainSlot, materials.fireplace);
  }

  const panel = shower.glassPanelMm;
  const glass = texturedBox(
    context.scene,
    `${fitout.id} · WALK-IN-1250 · číre bezpečnostné sklo`,
    rectCenter(panel),
    panel.x1 - panel.x0,
    panel.y1 - panel.y0,
    2.1,
    0,
    1,
  );
  finish(context, glass, materials.showerGlass, { shadow: true, pickable: true });
  for (const [index, yMm] of [panel.y0, panel.y1].entries()) {
    const post = texturedBox(
      context.scene,
      `${fitout.id} · WALK-IN-1250 · čierny profil ${index + 1}`,
      { x: (panel.x0 + panel.x1) / 2, y: yMm },
      22,
      18,
      2.12,
      0,
      1,
    );
    finish(context, post, materials.fireplace, { shadow: true });
  }
  const topRail = texturedBox(
    context.scene,
    `${fitout.id} · WALK-IN-1250 · horný stabilizačný profil`,
    rectCenter(panel),
    20,
    panel.y1 - panel.y0,
    0.018,
    2.1,
    1,
  );
  finish(context, topRail, materials.fireplace, { shadow: true });

  // Shower controls sit on the solid south wall outside the high east window.
  const showerColumnXmm = 27020;
  const showerWallYmm = 6680;
  const riser = CreateCylinder(
    `${fitout.id} · WALK-IN-1250 · matne čierna sprchová tyč`,
    { height: 1.55, diameter: 0.026, tessellation: 20 },
    context.scene,
  );
  riser.position.set(xM(showerColumnXmm), 1.13, zM(showerWallYmm));
  finish(context, riser, materials.fireplace, { shadow: true });
  const overheadArm = CreateCylinder(
    `${fitout.id} · WALK-IN-1250 · rameno hlavovej sprchy`,
    { height: 0.32, diameter: 0.024, tessellation: 20 },
    context.scene,
  );
  overheadArm.rotation.x = Math.PI / 2;
  overheadArm.position.set(xM(showerColumnXmm), 2.04, zM(showerWallYmm + 150));
  finish(context, overheadArm, materials.fireplace, { shadow: true });
  const rainHead = CreateCylinder(
    `${fitout.id} · WALK-IN-1250 · čierna hlavová sprcha 240`,
    { height: 0.025, diameter: 0.24, tessellation: 36 },
    context.scene,
  );
  rainHead.position.set(xM(showerColumnXmm), 2.035, zM(showerWallYmm + 300));
  finish(context, rainHead, materials.fireplace, { shadow: true, pickable: true });
  const mixer = texturedBox(
    context.scene,
    `${fitout.id} · WALK-IN-1250 · čierna termostatická batéria`,
    { x: showerColumnXmm, y: showerWallYmm - 3 },
    260,
    35,
    0.075,
    1.03,
    1,
  );
  finish(context, mixer, materials.fireplace, { pickable: true });

  const builtIn = fitout.builtIn;
  const run = builtIn.footprintMm;
  const basin = builtIn.basin;
  const basinCenter = rectCenter(basin.footprintMm);
  const vanityX1 = builtIn.appliances[0].footprintMm.x0 - 36;

  // The vanity adapts to the straight service-core partition; the 600 mm
  // laundry tower retains its appliance and ventilation clearances.
  const vanityCabinet = texturedBox(
    context.scene,
    `${fitout.id} · BUILT-IN-2616 · plávajúca bezúchytková skrinka`,
    { x: (run.x0 + vanityX1) / 2, y: (run.y0 + run.y1) / 2 },
    vanityX1 - run.x0,
    run.y1 - run.y0 - 24,
    0.7,
    0.1,
    1,
  );
  finish(context, vanityCabinet, materials.kitchenFront, { shadow: true, pickable: true });
  const vanityPlinth = texturedBox(
    context.scene,
    `${fitout.id} · BUILT-IN-2616 · zapustený čierny sokel`,
    { x: (run.x0 + vanityX1) / 2, y: run.y0 + 70 },
    vanityX1 - run.x0 - 80,
    100,
    0.1,
    0,
    1,
  );
  finish(context, vanityPlinth, materials.fireplace);
  const counter = texturedBox(
    context.scene,
    `${fitout.id} · BUILT-IN-2616 · súvislá tmavá doska pod umývadlom`,
    { x: (run.x0 + vanityX1) / 2, y: (run.y0 + run.y1) / 2 },
    vanityX1 - run.x0,
    run.y1 - run.y0,
    0.035,
    builtIn.counterHeightMm * MM_TO_M - 0.035,
    1,
  );
  finish(context, counter, materials.worktop, { shadow: true });
  softEllipsoid(
    context,
    `${fitout.id} · BUILT-IN-2616 · veľké matne čierne umývadlo`,
    basinCenter,
    [(basin.footprintMm.x1-basin.footprintMm.x0)*MM_TO_M, 0.16, 0.39],
    basin.rimElevationMm * MM_TO_M + 0.035,
    materials.blackCeramic,
  );
  softEllipsoid(
    context,
    `${fitout.id} · BUILT-IN-2616 · vnútorná čierna misa`,
    { x: basinCenter.x, y: basinCenter.y - 8 },
    [(basin.footprintMm.x1-basin.footprintMm.x0-160)*MM_TO_M, 0.028, 0.27],
    basin.rimElevationMm * MM_TO_M + 0.095,
    materials.blackGlass,
  );
  const basinDrain = CreateCylinder(
    `${fitout.id} · BUILT-IN-2616 · čierna výpusť umývadla`,
    { height: 0.009, diameter: 0.058, tessellation: 24 },
    context.scene,
  );
  basinDrain.position.set(
    xM(basinCenter.x),
    basin.rimElevationMm * MM_TO_M + 0.115,
    zM(basinCenter.y - 10),
  );
  finish(context, basinDrain, materials.fireplace);

  const mirrorWidthMm = Math.min(1_400, vanityX1 - run.x0 - 240);
  const mirrorGlow = texturedBox(
    context.scene,
    `${fitout.id} · BUILT-IN-2616 · nepriame LED za zrkadlom`,
    { x: basinCenter.x, y: run.y1 - 8 },
    mirrorWidthMm + 40,
    18,
    0.82,
    1.1,
    1,
  );
  finish(context, mirrorGlow, materials.warmLight, { shadow: true });
  const mirror = texturedBox(
    context.scene,
    `${fitout.id} · BUILT-IN-2616 · veľké bezrámové zrkadlo`,
    { x: basinCenter.x, y: run.y1 - 19 },
    mirrorWidthMm,
    9,
    0.78,
    1.12,
    1,
  );
  finish(context, mirror, materials.mirrorGlass, { pickable: true });
  const wallTap = CreateCylinder(
    `${fitout.id} · BUILT-IN-2616 · nástenná čierna batéria`,
    { height: 0.18, diameter: 0.03, tessellation: 20 },
    context.scene,
  );
  wallTap.rotation.x = Math.PI / 2;
  wallTap.position.set(xM(basinCenter.x), 1.18, zM(run.y1 - 95));
  finish(context, wallTap, materials.fireplace, { shadow: true });
  const tapMouth = CreateCylinder(
    `${fitout.id} · BUILT-IN-2616 · ústie čiernej batérie`,
    { height: 0.065, diameter: 0.034, tessellation: 20 },
    context.scene,
  );
  tapMouth.position.set(xM(basinCenter.x), 1.145, zM(run.y1 - 180));
  finish(context, tapMouth, materials.fireplace, { shadow: true });

  const basinTopCabinet = texturedBox(
    context.scene,
    `${fitout.id} · BUILT-IN-2616 · horná skrinka nad zrkadlom`,
    { x: (run.x0 + vanityX1) / 2, y: (run.y0 + run.y1) / 2 },
    vanityX1 - run.x0,
    run.y1 - run.y0,
    0.35,
    builtIn.heightMm * MM_TO_M - 0.35,
    1,
  );
  finish(context, basinTopCabinet, materials.kitchenFront, {
    shadow: true,
    pickable: true,
    cameraOccluder: true,
  });
  const applianceUpperX0 = vanityX1;
  const applianceUpper = texturedBox(
    context.scene,
    `${fitout.id} · LAUNDRY-TOWER · vetraná horná skrinka`,
    { x: (applianceUpperX0 + run.x1) / 2, y: (run.y0 + run.y1) / 2 },
    run.x1 - applianceUpperX0,
    run.y1 - run.y0,
    (builtIn.heightMm - builtIn.overheadCabinetBottomMm) * MM_TO_M,
    builtIn.overheadCabinetBottomMm * MM_TO_M,
    1,
  );
  finish(context, applianceUpper, materials.kitchenFront, {
    shadow: true,
    pickable: true,
    cameraOccluder: true,
  });
  const cabinetJoint = texturedBox(
    context.scene,
    `${fitout.id} · BUILT-IN-2616 · deliaca škára umývadlovej skrinky a práčovňovej veže`,
    { x: vanityX1, y: run.y0 - 4 },
    5,
    14,
    builtIn.heightMm * MM_TO_M - 0.08,
    0.04,
    1,
  );
  finish(context, cabinetJoint, materials.fireplace);
  const applianceLed = texturedBox(
    context.scene,
    `${fitout.id} · BUILT-IN-2616 · zapustené LED nad spotrebičmi`,
    { x: (applianceUpperX0 + run.x1) / 2, y: run.y0 + 35 },
    run.x1 - applianceUpperX0 - 60,
    22,
    0.012,
    builtIn.overheadCabinetBottomMm * MM_TO_M - 0.014,
    1,
  );
  finish(context, applianceLed, materials.warmLight);

  for (const appliance of builtIn.appliances) {
    buildStackedLaundryAppliance(
      context,
      materials,
      fitout.id,
      run,
      appliance,
    );
  }

  const washer = builtIn.appliances[0];
  const stackingShelf = texturedBox(
    context.scene,
    `${fitout.id} · LAUNDRY-TOWER · antivibračná medzipolica`,
    rectCenter(washer.footprintMm),
    washer.footprintMm.x1 - washer.footprintMm.x0 + 20,
    washer.footprintMm.y1 - washer.footprintMm.y0 + 20,
    0.026,
    (washer.baseElevationMm + washer.heightMm + 7) * MM_TO_M,
    1,
  );
  finish(context, stackingShelf, materials.steel, { shadow: true });

  for (let slot = 0; slot < 5; slot += 1) {
    const vent = texturedBox(
      context.scene,
      `${fitout.id} · LAUNDRY-TOWER · odvetrávacia štrbina ${slot + 1}`,
      {
        x: (applianceUpperX0 + run.x1) / 2,
        y: run.y0 - 10,
      },
      390,
      12,
      0.012,
      (1.98 + slot * 0.052),
      1,
    );
    finish(context, vent, materials.fireplace);
  }

  for (const xMm of [builtIn.appliances[0].footprintMm.x0 - 18, run.x1 - 24]) {
    const sidePanel = texturedBox(
      context.scene,
      `${fitout.id} · LAUNDRY-TOWER · zvislý skriňový panel`,
      { x: xMm, y: (run.y0 + run.y1) / 2 },
      32,
      run.y1 - run.y0,
      builtIn.heightMm * MM_TO_M,
      0,
      1,
    );
    finish(context, sidePanel, materials.kitchenFront, { shadow: true });
  }
  const topCornice = texturedBox(
    context.scene,
    `${fitout.id} · BUILT-IN-2616 · súvislá horná línia`,
    rectCenter(run),
    run.x1 - run.x0,
    run.y1 - run.y0,
    0.055,
    builtIn.heightMm * MM_TO_M - 0.055,
    1,
  );
  finish(context, topCornice, materials.kitchenFront, { shadow: true });

  buildTowelRadiator(context, materials, fitout.id, fitout.towelRadiator);

  navigationGuard(
    context,
    materials,
    `${fitout.id} · BUILT-IN-2616 · hladký navigačný obrys`,
    run,
  );
  navigationGuard(
    context,
    materials,
    `${fitout.id} · WALK-IN-1250 · navigačný obrys skla`,
    { x0: panel.x0 - 10, y0: panel.y0, x1: panel.x1 + 10, y1: panel.y1 },
  );

}

type TowelRadiator = Omit<typeof BATHROOM_FITOUT.towelRadiator,'id'|'wallId'|'facing'> & {facing:'NORTH'|'EAST'};
function buildTowelRadiator(context:InteriorBuildContext, materials:InteriorMaterials, fitoutId:string, radiator:TowelRadiator) {
  const r=radiator.footprintMm, alongY=radiator.facing==='EAST';
  const point=(along:number,depth:number):Point2Mm=>alongY?{x:r.x0+depth,y:r.y0+along}:{x:r.x0+along,y:r.y0+depth};
  const railRadius=radiator.railDiameterMm/2;
  for(const [i,along] of [railRadius,radiator.widthMm-railRadius].entries()) {
    const rail=CreateCylinder(`${fitoutId} · TOWEL-RADIATOR-600 · zvislý kolektor ${i+1}`,
      {height:radiator.heightMm*MM_TO_M,diameter:radiator.railDiameterMm*MM_TO_M,tessellation:24},context.scene);
    const p=point(along,radiator.projectionMm-railRadius);
    rail.position.set(xM(p.x),(radiator.bottomElevationMm+radiator.heightMm/2)*MM_TO_M,zM(p.y));
    finish(context,rail,materials.fireplace,{shadow:true,pickable:true});
  }
  for(let i=0;i<radiator.rungCount;i++) {
    const rung=CreateCylinder(`${fitoutId} · TOWEL-RADIATOR-600 · vodorovná priečka ${i+1}`,
      {height:(radiator.widthMm-radiator.railDiameterMm*1.25)*MM_TO_M,diameter:0.022,tessellation:24},context.scene);
    if(alongY) rung.rotation.x=Math.PI/2; else rung.rotation.z=Math.PI/2;
    const p=point(radiator.widthMm/2,radiator.projectionMm);
    rung.position.set(xM(p.x),(radiator.bottomElevationMm+55+i*(radiator.heightMm-110)/(radiator.rungCount-1))*MM_TO_M,zM(p.y));
    finish(context,rung,materials.fireplace,{shadow:true,pickable:true});
  }
  for(const [along,height] of [[70,120],[radiator.widthMm-70,radiator.heightMm-120]]) {
    const mount=CreateCylinder(`${fitoutId} · TOWEL-RADIATOR-600 · nástenná konzola`,
      {height:radiator.projectionMm*MM_TO_M,diameter:0.026,tessellation:20},context.scene);
    if(alongY) mount.rotation.z=Math.PI/2; else mount.rotation.x=Math.PI/2;
    const p=point(along,radiator.projectionMm/2);
    mount.position.set(xM(p.x),(radiator.bottomElevationMm+height)*MM_TO_M,zM(p.y));
    finish(context,mount,materials.fireplace,{shadow:true});
  }
  navigationGuard(context,materials,`${fitoutId} · TOWEL-RADIATOR-600 · hladký navigačný obrys`,r);
}

/**
 * Calm, plan-faithful second bathroom: a back-to-wall bath, compact wall-hung
 * WC and one floating oak vanity. All detail meshes stay decorative while one
 * smooth guard per fixture keeps the two-door circulation predictable.
 */
function buildEnsuiteBathroomFitout(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
) {
  const fitout = ENSUITE_BATHROOM_FITOUT;
  const bathtub = fitout.bathtub;
  const bathRect = bathtub.footprintMm;
  const bathCenter = rectCenter(bathRect);
  // A bath along the street wall runs east–west with its taps at the west end;
  // one along a side wall runs north–south with its taps at the street end.
  // `bathWallX` is the wall the taps hang on, `bathIn` points into the room.
  const bathAlongX = bathtub.facing === "NORTH";
  const bathWallX = bathtub.facing === "WEST" ? bathRect.x1 : bathRect.x0;
  const bathIn = bathtub.facing === "WEST" ? -1 : 1;
  const bathWindow = HOUSE.facades.front.openings.find((opening) => opening.id === fitout.frontWindowId)!;

  const windowBacksplash = texturedBox(
    context.scene,
    `${fitout.id} · WINDOW · súvislý veľkoformátový obklad pod vysokým oknom`,
    { x: bathWindow.startXmm + bathWindow.widthMm / 2, y: 3514 },
    bathWindow.widthMm,
    20,
    fitout.windowBacksplashTopElevationMm * MM_TO_M,
    0,
    1.2,
  );
  finish(context, windowBacksplash, materials.wallTile, { shadow: true });

  const bathBody = texturedBox(
    context.scene,
    `${fitout.id} · BATH-WALL · čistá biela vaňa so zaobleným vnútrom`,
    bathCenter,
    bathRect.x1 - bathRect.x0,
    bathRect.y1 - bathRect.y0,
    0.52,
    0.04,
    1,
  );
  finish(context, bathBody, materials.sanitaryCeramic, {
    shadow: true,
    pickable: true,
    cameraOccluder: true,
  });
  const bathRim = CreateTorus(
    `${fitout.id} · BATH-WALL · tenký oválny lem`,
    { diameter: 1, thickness: 0.05, tessellation: 56 },
    context.scene,
  );
  bathRim.position.set(xM(bathCenter.x), bathtub.rimElevationMm * MM_TO_M, zM(bathCenter.y));
  bathRim.scaling.set((bathRect.x1-bathRect.x0-(bathAlongX?130:180))*MM_TO_M, 0.72, (bathRect.y1-bathRect.y0-(bathAlongX?180:130))*MM_TO_M);
  finish(context, bathRim, materials.sanitaryCeramic, { shadow: true, pickable: true });
  softEllipsoid(
    context,
    `${fitout.id} · BATH-WALL · hladké vnútro vane`,
    rectCenter(bathtub.innerBasinMm),
    [(bathtub.innerBasinMm.x1-bathtub.innerBasinMm.x0-(bathAlongX?50:110))*MM_TO_M, 0.018, (bathtub.innerBasinMm.y1-bathtub.innerBasinMm.y0-(bathAlongX?110:50))*MM_TO_M],
    bathtub.rimElevationMm * MM_TO_M + 0.004,
    materials.mirrorGlass,
  );
  const bathDrain = CreateCylinder(
    `${fitout.id} · BATH-WALL · matne čierna výpusť`,
    { height: 0.008, diameter: 0.055, tessellation: 28 },
    context.scene,
  );
  // The drain sits under the spout at the tap end.
  bathDrain.position.set(
    xM(bathAlongX ? bathtub.innerBasinMm.x0 + 120 : bathCenter.x),
    0.586,
    zM(bathAlongX ? bathCenter.y : bathtub.innerBasinMm.y0 + 120),
  );
  finish(context, bathDrain, materials.fireplace, { pickable: true });

  // The concealed mixer sits on the wall behind the bath, 280 mm from the tap end.
  const bathMixer = texturedBox(
    context.scene,
    `${fitout.id} · BATH-WALL · podomietková čierna batéria`,
    bathAlongX ? { x: bathRect.x0 + 280, y: bathRect.y0 + 12 } : { x: bathWallX + bathIn * 12, y: bathRect.y0 + 280 },
    bathAlongX ? 220 : 24,
    bathAlongX ? 24 : 220,
    0.1,
    0.76,
    1,
  );
  finish(context, bathMixer, materials.fireplace, { pickable: true });
  const bathSpout = CreateCylinder(
    `${fitout.id} · BATH-WALL · nástenný výtok`,
    { height: 0.2, diameter: 0.026, tessellation: 24 },
    context.scene,
  );
  if (bathAlongX) {
    bathSpout.rotation.x = Math.PI / 2;
    bathSpout.position.set(xM(bathRect.x0 + 280), 0.81, zM(bathRect.y0 + 105));
  } else {
    bathSpout.rotation.z = Math.PI / 2;
    bathSpout.position.set(xM(bathWallX + bathIn * 105), 0.81, zM(bathRect.y0 + 280));
  }
  finish(context, bathSpout, materials.fireplace, { shadow: true });

  const toilet = fitout.toilet;
  const toiletCenter = rectCenter(toilet.footprintMm);
  // The bowl points away from its cistern wall:
  // `along` is measured from that wall on the bowl's axis, `across` sideways.
  const wcAlongX = toilet.facing === "EAST" || toilet.facing === "WEST";
  const wcOut = toilet.facing === "SOUTH" || toilet.facing === "WEST" ? -1 : 1;
  const wcWall = wcAlongX
    ? (wcOut > 0 ? toilet.footprintMm.x0 : toilet.footprintMm.x1)
    : (wcOut > 0 ? toilet.footprintMm.y0 : toilet.footprintMm.y1);
  const wcPoint = (alongMm: number, acrossMm = 0): Point2Mm => wcAlongX
    ? { x: wcWall + wcOut * alongMm, y: toiletCenter.y + acrossMm }
    : { x: toiletCenter.x + acrossMm, y: wcWall + wcOut * alongMm };
  const wcSize = <T>(along: T, across: T): [T, T] => wcAlongX ? [along, across] : [across, along];
  const cistern = texturedBox(
    context.scene,
    `${fitout.id} · WC · podomietkový modul v predstene`,
    rectCenter(toilet.concealedCisternRectMm),
    toilet.concealedCisternRectMm.x1 - toilet.concealedCisternRectMm.x0,
    toilet.concealedCisternRectMm.y1 - toilet.concealedCisternRectMm.y0,
    toilet.moduleHeightMm * MM_TO_M,
    0,
    1.2,
  );
  finish(context, cistern, materials.wallTile, { shadow: true, pickable: true });
  const cisternCap = texturedBox(
    context.scene,
    `${fitout.id} · WC · horná keramická doska modulu`,
    rectCenter(toilet.concealedCisternRectMm),
    toilet.concealedCisternRectMm.x1 - toilet.concealedCisternRectMm.x0 + 12,
    toilet.concealedCisternRectMm.y1 - toilet.concealedCisternRectMm.y0 + 12,
    0.025,
    toilet.moduleHeightMm * MM_TO_M,
    1,
  );
  finish(context, cisternCap, materials.sanitaryCeramic, { shadow: true });
  const cisternDepthMm = wcAlongX
    ? toilet.concealedCisternRectMm.x1 - toilet.concealedCisternRectMm.x0
    : toilet.concealedCisternRectMm.y1 - toilet.concealedCisternRectMm.y0;
  const flushPlatePoint = wcPoint(cisternDepthMm + 6);
  const flushPlate = texturedBox(
    context.scene,
    `${fitout.id} · WC · matne čierne dvojité splachovanie`,
    flushPlatePoint,
    ...wcSize(12, 190),
    0.11,
    0.84,
    1,
  );
  finish(context, flushPlate, materials.fireplace, { pickable: true });
  for (const offsetMm of [-42, 42]) {
    const button = CreateCylinder(
      `${fitout.id} · WC · splachovacie tlačidlo`,
      { height: 0.012, diameter: offsetMm < 0 ? 0.052 : 0.038, tessellation: 24 },
      context.scene,
    );
    if (wcAlongX) button.rotation.z = Math.PI / 2;
    else button.rotation.x = Math.PI / 2;
    const buttonPoint = wcPoint(cisternDepthMm + 13, offsetMm);
    button.position.set(xM(buttonPoint.x), 0.895, zM(buttonPoint.y));
    finish(context, button, materials.blackGlass);
  }
  const [bowlX, bowlY] = wcSize(0.44, 0.34);
  softEllipsoid(
    context,
    `${fitout.id} · WC · kompaktná závesná misa`,
    wcPoint(340),
    [bowlX, 0.28, bowlY],
    0.32,
    materials.sanitaryCeramic,
  );
  const [bowlInnerX, bowlInnerY] = wcSize(0.3, 0.23);
  softEllipsoid(
    context,
    `${fitout.id} · WC · vnútro misy`,
    wcPoint(386),
    [bowlInnerX, 0.024, bowlInnerY],
    0.455,
    materials.mirrorGlass,
  );
  const toiletSeat = CreateTorus(
    `${fitout.id} · WC · subtílne sedadlo`,
    { diameter: 0.31, thickness: 0.032, tessellation: 40 },
    context.scene,
  );
  const seatPoint = wcPoint(344);
  const [seatX, seatZ] = wcSize(1.32, 1);
  toiletSeat.position.set(xM(seatPoint.x), toilet.seatElevationMm * MM_TO_M, zM(seatPoint.y));
  toiletSeat.scaling.set(seatX, 0.7, seatZ);
  finish(context, toiletSeat, materials.sanitaryCeramic, { shadow: true, pickable: true });

  const vanity = fitout.vanity;
  const vanityRect = vanity.footprintMm;
  const vanityCenter = rectCenter(vanityRect);
  // `vanityIn` points from either side wall (or the street wall) into the room.
  const vanityAlongX = vanity.facing === "WEST" || vanity.facing === "EAST";
  const vanityIn = vanity.facing === "WEST" ? -1 : 1;
  const vanityDepthMm = vanityAlongX ? vanityRect.x1 - vanityRect.x0 : vanityRect.y1 - vanityRect.y0;
  const vanityLengthMm = vanityAlongX ? vanityRect.y1 - vanityRect.y0 : vanityRect.x1 - vanityRect.x0;
  const vanityWallMm = vanityAlongX ? (vanityIn > 0 ? vanityRect.x0 : vanityRect.x1) : vanityRect.y0;
  /** A point `inMm` from the wall on the vanity's axis, `alongMm` from its centre. */
  const vanityPoint = (inMm: number, alongMm = 0): Point2Mm => vanityAlongX
    ? { x: vanityWallMm + vanityIn * inMm, y: vanityCenter.y + alongMm }
    : { x: vanityCenter.x + alongMm, y: vanityWallMm + vanityIn * inMm };
  const vanitySize = <T>(inward: T, along: T): [T, T] => vanityAlongX ? [inward, along] : [along, inward];
  const vanityShadow = texturedBox(
    context.scene,
    `${fitout.id} · VANITY-900 · tieň pod plávajúcou skrinkou`,
    vanityPoint(vanityDepthMm / 2 - 35),
    ...vanitySize(vanityDepthMm - 70, vanityLengthMm - 60),
    0.07,
    0.15,
    1,
  );
  finish(context, vanityShadow, materials.fireplace);
  const vanityBody = texturedBox(
    context.scene,
    `${fitout.id} · VANITY-900 · plávajúca bezúchytková dubová skrinka`,
    vanityCenter,
    vanityRect.x1 - vanityRect.x0,
    vanityRect.y1 - vanityRect.y0,
    0.56,
    0.22,
    1,
  );
  finish(context, vanityBody, materials.kitchenFront, { shadow: true, pickable: true });
  const vanityTop = texturedBox(
    context.scene,
    `${fitout.id} · VANITY-900 · tenká kamenná doska`,
    vanityCenter,
    vanityRect.x1 - vanityRect.x0,
    vanityRect.y1 - vanityRect.y0,
    0.04,
    vanity.counterElevationMm * MM_TO_M - 0.04,
    1,
  );
  finish(context, vanityTop, materials.worktop, { shadow: true, pickable: true });
  const basinCenter = rectCenter(vanity.basinFootprintMm);
  const [basinInX, basinInZ] = vanitySize((vanityDepthMm - 100) * MM_TO_M, 0.36);
  softEllipsoid(
    context,
    `${fitout.id} · VANITY-900 · veľké biele integrované umývadlo`,
    basinCenter,
    [basinInX, 0.14, basinInZ],
    vanity.basinRimElevationMm * MM_TO_M - 0.05,
    materials.sanitaryCeramic,
  );
  const [innerInX, innerInZ] = vanitySize((vanityDepthMm - 210) * MM_TO_M, 0.24);
  const basinInnerCenter = vanityAlongX
    ? { x: basinCenter.x + vanityIn * 20, y: basinCenter.y }
    : { x: basinCenter.x, y: basinCenter.y + 20 };
  softEllipsoid(
    context,
    `${fitout.id} · VANITY-900 · vnútorná misa`,
    basinInnerCenter,
    [innerInX, 0.024, innerInZ],
    vanity.basinRimElevationMm * MM_TO_M + 0.008,
    materials.mirrorGlass,
  );
  const vanityDrain = CreateCylinder(
    `${fitout.id} · VANITY-900 · čierna výpusť`,
    { height: 0.008, diameter: 0.052, tessellation: 24 },
    context.scene,
  );
  const drainPoint = vanityAlongX
    ? { x: basinCenter.x + vanityIn * 58, y: basinCenter.y }
    : { x: basinCenter.x, y: basinCenter.y + 58 };
  vanityDrain.position.set(
    xM(drainPoint.x),
    vanity.basinRimElevationMm * MM_TO_M + 0.022,
    zM(drainPoint.y),
  );
  finish(context, vanityDrain, materials.fireplace, { pickable: true });

  const mirrorRect = vanity.mirrorPlanRectMm;
  const mirrorLengthMm = vanityAlongX ? mirrorRect.y1 - mirrorRect.y0 : mirrorRect.x1 - mirrorRect.x0;
  const mirrorGlow = texturedBox(
    context.scene,
    `${fitout.id} · VANITY-900 · nepriame LED za zrkadlom`,
    vanityAlongX ? { x: vanityIn > 0 ? mirrorRect.x0 + 2 : mirrorRect.x1 - 2, y: vanityCenter.y } : { x: vanityCenter.x, y: mirrorRect.y0 + 2 },
    ...vanitySize(4, mirrorLengthMm + 40),
    (vanity.mirrorTopElevationMm - vanity.mirrorBottomElevationMm + 40) * MM_TO_M,
    (vanity.mirrorBottomElevationMm - 20) * MM_TO_M,
    1,
  );
  finish(context, mirrorGlow, materials.warmLight, { shadow: true });
  const mirror = texturedBox(
    context.scene,
    `${fitout.id} · VANITY-900 · veľké bezrámové zrkadlo`,
    rectCenter(vanity.mirrorPlanRectMm),
    vanity.mirrorPlanRectMm.x1 - vanity.mirrorPlanRectMm.x0,
    vanity.mirrorPlanRectMm.y1 - vanity.mirrorPlanRectMm.y0,
    (vanity.mirrorTopElevationMm - vanity.mirrorBottomElevationMm) * MM_TO_M,
    vanity.mirrorBottomElevationMm * MM_TO_M,
    1,
  );
  finish(context, mirror, materials.mirrorGlass, { pickable: true });
  const wallTap = CreateCylinder(
    `${fitout.id} · VANITY-900 · nástenná čierna batéria`,
    { height: 0.18, diameter: 0.028, tessellation: 24 },
    context.scene,
  );
  if (vanityAlongX) wallTap.rotation.z = Math.PI / 2;
  else wallTap.rotation.x = Math.PI / 2;
  const tapPoint = vanityPoint(90);
  wallTap.position.set(xM(tapPoint.x), 1.08, zM(tapPoint.y));
  finish(context, wallTap, materials.fireplace, { shadow: true });

  const ceilingLight = CreateCylinder(
    `${fitout.id} · LIGHT · zapustené kruhové svietidlo`,
    { height: 0.018, diameter: 0.28, tessellation: 40 },
    context.scene,
  );
  // Over the free floor between the WC bowl, the bath rim and the vanity.
  const lightCenter = rectCenter(fitout.clearFloorRectMm);
  ceilingLight.position.set(xM(lightCenter.x), 2.565, zM(lightCenter.y));
  finish(context, ceilingLight, materials.warmLight, { shadow: true });
  const roomLight = new PointLight(
    `${fitout.id} · LIGHT · mäkké teplé svetlo`,
    new Vector3(xM(lightCenter.x), 2.42, zM(lightCenter.y)),
    context.scene,
  );
  roomLight.diffuse = Color3.FromHexString("#ffd7ad");
  roomLight.specular = Color3.FromHexString("#756556");
  roomLight.intensity = 0.22;
  roomLight.range = 2.9;

  buildTowelRadiator(context,materials,fitout.id,fitout.towelRadiator);
  navigationGuard(context, materials, `${fitout.id} · BATH-WALL · navigačný obrys`, bathRect);
  navigationGuard(
    context,
    materials,
    `${fitout.id} · WC · navigačný obrys`,
    toilet.footprintMm,
  );
  navigationGuard(
    context,
    materials,
    `${fitout.id} · VANITY-900 · navigačný obrys`,
    vanityRect,
  );
}

function buildGarageFitout(context: InteriorBuildContext, materials: InteriorMaterials) {
  const fitout = GARAGE_FITOUT;
  const sink = fitout.utilitySink;
  const sinkRect = sink.footprintMm;
  const sinkCenter = rectCenter(sinkRect);
  const sinkTopM = sink.rimElevationMm * MM_TO_M;

  const sinkBody = texturedBox(
    context.scene,
    `${fitout.id} · UTILITY-SINK · hlboká nerezová pracovná vaňa`,
    sinkCenter,
    sinkRect.x1 - sinkRect.x0,
    sinkRect.y1 - sinkRect.y0,
    0.285,
    sinkTopM - 0.285,
    1,
  );
  sinkBody.metadata = {
    ...(sinkBody.metadata ?? {}),
    designSourceId: fitout.sourceId,
    plumbingStatus: fitout.plumbingStatus,
  };
  finish(context, sinkBody, materials.steel, { shadow: true, pickable: true });

  const inner = sink.innerBasinMm;
  const innerCenter = rectCenter(inner);
  const basinShadow = texturedBox(
    context.scene,
    `${fitout.id} · UTILITY-SINK · zapustené tmavé vnútro`,
    innerCenter,
    inner.x1 - inner.x0,
    inner.y1 - inner.y0,
    0.035,
    sinkTopM - 0.075,
    1,
  );
  finish(context, basinShadow, materials.blackGlass, { pickable: true });
  const basinWater = texturedBox(
    context.scene,
    `${fitout.id} · UTILITY-SINK · tenká vrstva vody`,
    { x: innerCenter.x - 12, y: innerCenter.y },
    inner.x1 - inner.x0 - 42,
    inner.y1 - inner.y0 - 42,
    0.009,
    sinkTopM - 0.045,
    1,
  );
  finish(context, basinWater, materials.showerGlass, { pickable: true });

  const rimPieces = [
    { label: "predný", center: { x: sinkRect.x0 + 22, y: sinkCenter.y }, width: 44, depth: sinkRect.y1 - sinkRect.y0 },
    { label: "zadný", center: { x: sinkRect.x1 - 22, y: sinkCenter.y }, width: 44, depth: sinkRect.y1 - sinkRect.y0 },
    { label: "južný", center: { x: sinkCenter.x, y: sinkRect.y0 + 22 }, width: sinkRect.x1 - sinkRect.x0 - 88, depth: 44 },
    { label: "severný", center: { x: sinkCenter.x, y: sinkRect.y1 - 22 }, width: sinkRect.x1 - sinkRect.x0 - 88, depth: 44 },
  ] as const;
  for (const piece of rimPieces) {
    const rim = texturedBox(
      context.scene,
      `${fitout.id} · UTILITY-SINK · ${piece.label} zosilnený lem`,
      piece.center,
      piece.width,
      piece.depth,
      0.035,
      sinkTopM - 0.012,
      1,
    );
    finish(context, rim, materials.steel, { shadow: true });
  }

  const backsplash = texturedBox(
    context.scene,
    `${fitout.id} · UTILITY-SINK · nerezový chrbtový lem pri mokrej stene`,
    { x: sinkRect.x1 - 14, y: sinkCenter.y },
    28,
    sinkRect.y1 - sinkRect.y0,
    (sink.backsplashTopElevationMm - sink.rimElevationMm) * MM_TO_M,
    sinkTopM,
    1,
  );
  finish(context, backsplash, materials.steel, { shadow: true, pickable: true });

  for (const yMm of [sinkRect.y0 + 92, sinkRect.y1 - 92]) {
    const leg = CreateCylinder(
      `${fitout.id} · UTILITY-SINK · nastaviteľná predná noha`,
      { height: sinkTopM - 0.26, diameter: 0.042, tessellation: 20 },
      context.scene,
    );
    leg.position.set(xM(sinkRect.x0 + 56), (sinkTopM - 0.26) / 2, zM(yMm));
    finish(context, leg, materials.steel, { shadow: true });
    const foot = CreateCylinder(
      `${fitout.id} · UTILITY-SINK · gumová pätka`,
      { height: 0.035, diameter: 0.075, tessellation: 20 },
      context.scene,
    );
    foot.position.set(xM(sinkRect.x0 + 56), 0.0175, zM(yMm));
    finish(context, foot, materials.fireplace, { shadow: true });
  }

  const sinkDrain = CreateCylinder(
    `${fitout.id} · UTILITY-SINK · sitkový odtok`,
    { height: 0.012, diameter: 0.072, tessellation: 28 },
    context.scene,
  );
  sinkDrain.position.set(xM(innerCenter.x - 35), sinkTopM - 0.031, zM(innerCenter.y));
  finish(context, sinkDrain, materials.steel, { pickable: true });

  const trap = CreateTube(
    `${fitout.id} · UTILITY-SINK · pohľadový sifón a odpad`,
    {
      path: [
        new Vector3(xM(innerCenter.x), sinkTopM - 0.23, zM(innerCenter.y)),
        new Vector3(xM(innerCenter.x), 0.47, zM(innerCenter.y)),
        new Vector3(xM(innerCenter.x + 95), 0.4, zM(innerCenter.y)),
        new Vector3(xM(sinkRect.x1 - 18), 0.4, zM(innerCenter.y)),
      ],
      radius: 0.026,
      tessellation: 20,
      cap: Mesh.CAP_ALL,
    },
    context.scene,
  );
  finish(context, trap, materials.steel, { shadow: true });

  const tapRiser = CreateCylinder(
    `${fitout.id} · UTILITY-SINK · robustná nástenná batéria`,
    { height: 0.25, diameter: 0.034, tessellation: 24 },
    context.scene,
  );
  tapRiser.position.set(xM(sinkRect.x1 - 38), 1.19, zM(sinkCenter.y));
  finish(context, tapRiser, materials.steel, { shadow: true, pickable: true });
  const tapSpout = CreateCylinder(
    `${fitout.id} · UTILITY-SINK · dlhý otočný výtok`,
    { height: 0.22, diameter: 0.027, tessellation: 24 },
    context.scene,
  );
  tapSpout.rotation.z = Math.PI / 2;
  tapSpout.position.set(xM(sinkRect.x1 - 135), 1.285, zM(sinkCenter.y));
  finish(context, tapSpout, materials.steel, { shadow: true });
  for (const yOffsetMm of [-72, 72]) {
    const valve = CreateTorus(
      `${fitout.id} · UTILITY-SINK · krížová rukoväť batérie`,
      { diameter: 0.072, thickness: 0.012, tessellation: 24 },
      context.scene,
    );
    valve.rotation.z = Math.PI / 2;
    valve.position.set(xM(sinkRect.x1 - 52), 1.18, zM(sinkCenter.y + yOffsetMm));
    finish(context, valve, materials.fireplace, { shadow: true, pickable: true });
  }

  const bucket = CreateCylinder(
    `${fitout.id} · GARAGE-CLUTTER · vedro pod umývadlom`,
    { height: 0.32, diameterTop: 0.3, diameterBottom: 0.24, tessellation: 28 },
    context.scene,
  );
  bucket.position.set(xM(sinkCenter.x + 60), 0.16, zM(sinkCenter.y - 95));
  finish(context, bucket, materials.childMidnight, { shadow: true, pickable: true });

  const rack = fitout.storageRack;
  const rackRect = rack.footprintMm;
  const rackHeightM = rack.heightMm * MM_TO_M;
  for (const xMm of [rackRect.x0 + 20, rackRect.x1 - 20]) {
    for (const yMm of [rackRect.y0 + 20, rackRect.y1 - 20]) {
      const post = texturedBox(
        context.scene,
        `${fitout.id} · GARAGE-RACK · pozinkovaný stojan`,
        { x: xMm, y: yMm },
        36,
        36,
        rackHeightM,
        0,
        1,
      );
      finish(context, post, materials.steel, { shadow: true });
    }
  }
  for (const shelfMm of rack.shelfElevationsMm) {
    const shelf = texturedBox(
      context.scene,
      `${fitout.id} · GARAGE-RACK · nosná polica +${shelfMm}`,
      rectCenter(rackRect),
      rackRect.x1 - rackRect.x0,
      rackRect.y1 - rackRect.y0,
      0.045,
      shelfMm * MM_TO_M,
      1,
    );
    finish(context, shelf, materials.steel, { shadow: true, pickable: true });
  }

  // Accessories stay within the shelf even when the garage bay changes width.
  const rackCenter=rectCenter(rackRect);
  for (let i=0;i<rack.cardboardBoxCount;i++) {
    const x=rackRect.x0+260+(i%2)*850;
    const base=i<2?.765:1.905;
    const carton=texturedBox(context.scene,`${fitout.id} · GARAGE-CLUTTER · kartónová krabica ${i+1}`,
      {x,y:rackCenter.y},350,300,.28,base,.55);
    finish(context,carton,materials.childSand,{shadow:true,pickable:true});
    const tape=texturedBox(context.scene,`${fitout.id} · GARAGE-CLUTTER · páska krabice ${i+1}`,
      {x,y:rackCenter.y},42,304,.008,base+.28,1);finish(context,tape,materials.kitchenFront);
  }
  for(let i=0;i<rack.plasticBinCount;i++) {
    const body=texturedBox(context.scene,`${fitout.id} · GARAGE-CLUTTER · plastový box ${i+1}`,
      {x:rackRect.x0+250+i*480,y:rackCenter.y+20},370,220,.29,1.335,1);
    finish(context,body,[materials.childMidnight,materials.childClay,materials.childSage][i],{shadow:true,pickable:true});
  }
  for(let i=0;i<rack.paintCanCount;i++) {
    const can=CreateCylinder(`${fitout.id} · GARAGE-CLUTTER · plechovka farby ${i+1}`,
      {height:.205,diameter:.17,tessellation:28},context.scene);
    can.position.set(xM(rackRect.x0+150+i*220),.2975,zM(rackCenter.y));
    finish(context,can,materials.applianceEnamel,{shadow:true,pickable:true});
  }
  const toolbox=texturedBox(context.scene,`${fitout.id} · GARAGE-CLUTTER · kufrík na náradie`,
    {x:rackCenter.x,y:rackCenter.y},350,240,.17,.765,1);
  finish(context,toolbox,materials.childClay,{shadow:true,pickable:true});

  const overSink = fitout.overSinkShelves;
  for (const shelfMm of overSink.elevationsMm) {
    const shelf = texturedBox(
      context.scene,
      `${fitout.id} · GARAGE-SHELF · polica nad pracovným umývadlom +${shelfMm}`,
      rectCenter(overSink.footprintMm),
      overSink.footprintMm.x1 - overSink.footprintMm.x0,
      overSink.footprintMm.y1 - overSink.footprintMm.y0,
      0.04,
      shelfMm * MM_TO_M,
      1,
    );
    finish(context, shelf, materials.steel, { shadow: true, pickable: true });
    for (const yMm of [overSink.footprintMm.y0 + 70, overSink.footprintMm.y1 - 70]) {
      const bracket = CreateTube(
        `${fitout.id} · GARAGE-SHELF · trojuholníková konzola`,
        {
          path: [
            new Vector3(xM(overSink.footprintMm.x1 - 18), shelfMm * MM_TO_M - 0.24, zM(yMm)),
            new Vector3(xM(overSink.footprintMm.x0 + 24), shelfMm * MM_TO_M - 0.025, zM(yMm)),
          ],
          radius: 0.014,
          tessellation: 16,
          cap: Mesh.CAP_ALL,
        },
        context.scene,
      );
      finish(context, bracket, materials.fireplace, { shadow: true });
    }
  }

  const pegboard = texturedBox(
    context.scene,
    `${fitout.id} · PEGBOARD · dierovaná stena na ručné náradie`,
    { x: sinkRect.x1 - 12, y: sinkCenter.y },
    24,
    sinkRect.y1 - sinkRect.y0 + 40,
    0.66,
    1.29,
    0.35,
  );
  finish(context, pegboard, materials.childCork, {
    shadow: true,
    pickable: true,
    cameraOccluder: true,
  });
  for (const elevationM of [1.39, 1.54, 1.69, 1.84]) {
    for (const yMm of [sinkCenter.y - 210, sinkCenter.y - 70, sinkCenter.y + 70, sinkCenter.y + 210]) {
      const hole = CreateCylinder(
        `${fitout.id} · PEGBOARD · otvor`,
        { height: 0.012, diameter: 0.018, tessellation: 12 },
        context.scene,
      );
      hole.rotation.z = Math.PI / 2;
      hole.position.set(xM(sinkRect.x1 - 27), elevationM, zM(yMm));
      finish(context, hole, materials.fireplace);
    }
  }
  for (const [index, tool] of [
    { y: sinkCenter.y - 165, elevation: 1.55, length: 0.34 },
    { y: sinkCenter.y + 15, elevation: 1.61, length: 0.45 },
    { y: sinkCenter.y + 180, elevation: 1.58, length: 0.28 },
  ].entries()) {
    const handTool = texturedBox(
      context.scene,
      `${fitout.id} · PEGBOARD · zavesené ručné náradie ${index + 1}`,
      { x: sinkRect.x1 - 34, y: tool.y },
      26,
      38,
      tool.length,
      tool.elevation,
      1,
    );
    finish(context, handTool, index === 1 ? materials.childClay : materials.fireplace, {
      shadow: true,
      pickable: true,
    });
  }

  const hose = CreateTorus(
    `${fitout.id} · GARAGE-CLUTTER · navinutá záhradná hadica`,
    { diameter: 0.4, thickness: 0.032, tessellation: 40 },
    context.scene,
  );
  hose.rotation.z = Math.PI / 2;
  hose.position.set(xM(sinkRect.x1-54), 2.32, zM(sinkCenter.y));
  finish(context, hose, materials.childSage, { shadow: true, pickable: true });

  for (const [index, tool] of [
    { y: 4520, shaft: materials.kitchenFront, blade: materials.fireplace },
    { y: 4650, shaft: materials.steel, blade: materials.childClay },
  ].entries()) {
    const shaft = CreateCylinder(
      `${fitout.id} · LONG-TOOL · ${index === 0 ? "metla" : "lopata"} · násada`,
      { height: 1.58, diameter: 0.03, tessellation: 16 },
      context.scene,
    );
    shaft.position.set(xM(sinkRect.x1-62), 0.88, zM(tool.y));
    shaft.rotation.z = index === 0 ? 0.04 : -0.035;
    finish(context, shaft, tool.shaft, { shadow: true, pickable: true });
    const head = index === 0
      ? texturedBox(
        context.scene,
        `${fitout.id} · LONG-TOOL · metla · pracovná hlava`,
        { x: sinkRect.x1-87, y: tool.y },
        100,
        170,
        0.1,
        0.04,
        1,
      )
      : softEllipsoid(
        context,
        `${fitout.id} · LONG-TOOL · lopata · oceľový list`,
        { x: sinkRect.x1-87, y: tool.y },
        [0.16, 0.035, 0.22],
        0.15,
        tool.blade,
      );
    if (index === 0) finish(context, head, tool.blade, { shadow: true, pickable: true });
  }

  const mower = fitout.mower;
  const mowerRect = mower.footprintMm;
  const mowerCenter = rectCenter(mowerRect);
  const deckCenter = { x: mowerCenter.x, y: mowerRect.y0 + 205 };
  const deck = CreateCylinder(
    `${fitout.id} · MOWER · zelené oceľové šasi`,
    { height: 0.13, diameter: mower.deckDiameterMm * MM_TO_M, tessellation: 48 },
    context.scene,
  );
  deck.position.set(xM(deckCenter.x), 0.155, zM(deckCenter.y));
  deck.scaling.z = 1.08;
  finish(context, deck, materials.childSage, { shadow: true, pickable: true });
  const engine = CreateCylinder(
    `${fitout.id} · MOWER · motor s čiernym krytom`,
    { height: 0.22, diameterBottom: 0.29, diameterTop: 0.24, tessellation: 32 },
    context.scene,
  );
  engine.position.set(xM(deckCenter.x), 0.33, zM(deckCenter.y - 10));
  finish(context, engine, materials.fireplace, { shadow: true, pickable: true });
  const fuelCap = CreateCylinder(
    `${fitout.id} · MOWER · uzáver palivovej nádrže`,
    { height: 0.028, diameter: 0.075, tessellation: 24 },
    context.scene,
  );
  fuelCap.position.set(xM(deckCenter.x + 62), 0.454, zM(deckCenter.y - 15));
  finish(context, fuelCap, materials.childClay, { shadow: true, pickable: true });

  for (const [index, wheel] of [
    { x: mowerRect.x0 + 36, y: deckCenter.y - 135 },
    { x: mowerRect.x1 - 36, y: deckCenter.y - 135 },
    { x: mowerRect.x0 + 36, y: deckCenter.y + 145 },
    { x: mowerRect.x1 - 36, y: deckCenter.y + 145 },
  ].entries()) {
    const wheelMesh = CreateCylinder(
      `${fitout.id} · MOWER · gumové koleso ${index + 1}`,
      { height: 0.072, diameter: index < 2 ? 0.15 : 0.18, tessellation: 28 },
      context.scene,
    );
    wheelMesh.rotation.z = Math.PI / 2;
    wheelMesh.position.set(xM(wheel.x), index < 2 ? 0.12 : 0.14, zM(wheel.y));
    finish(context, wheelMesh, materials.fireplace, { shadow: true, pickable: true });
  }

  const grassBag = texturedBox(
    context.scene,
    `${fitout.id} · MOWER · textilný zberný kôš`,
    { x: mowerCenter.x, y: deckCenter.y + 235 },
    330,
    245,
    0.255,
    0.23,
    0.45,
  );
  grassBag.rotation.x = -0.08;
  finish(context, grassBag, materials.officeFabric, { shadow: true, pickable: true });

  const handleTopY = mowerRect.y1 - 45;
  for (const side of [-1, 1] as const) {
    const handle = CreateTube(
      `${fitout.id} · MOWER · sklopná oceľová rukoväť ${side < 0 ? "ľavá" : "pravá"}`,
      {
        path: [
          new Vector3(xM(mowerCenter.x + side * 135), 0.39, zM(deckCenter.y + 135)),
          new Vector3(xM(mowerCenter.x + side * 185), 0.85, zM(deckCenter.y + 330)),
          new Vector3(xM(mowerCenter.x + side * 185), mower.handleTopElevationMm * MM_TO_M, zM(handleTopY)),
        ],
        radius: 0.017,
        tessellation: 18,
        cap: Mesh.CAP_ALL,
      },
      context.scene,
    );
    finish(context, handle, materials.steel, { shadow: true, pickable: true });
  }
  const mowerGrip = CreateTube(
    `${fitout.id} · MOWER · mäkké priečne madlo`,
    {
      path: [
        new Vector3(xM(mowerCenter.x - 185), mower.handleTopElevationMm * MM_TO_M, zM(handleTopY)),
        new Vector3(xM(mowerCenter.x + 185), mower.handleTopElevationMm * MM_TO_M, zM(handleTopY)),
      ],
      radius: 0.025,
      tessellation: 20,
      cap: Mesh.CAP_ALL,
    },
    context.scene,
  );
  finish(context, mowerGrip, materials.fireplace, { shadow: true, pickable: true });

  navigationGuard(context, materials, `${fitout.id} · UTILITY-SINK · navigačný obrys`, sinkRect);
  navigationGuard(context, materials, `${fitout.id} · GARAGE-RACK · navigačný obrys`, rackRect);
  navigationGuard(context, materials, `${fitout.id} · MOWER · navigačný obrys`, mowerRect);
  cameraOcclusionProxy(
    context,
    materials,
    `${fitout.id} · GARAGE-RACK · súvislý objem pre kameru`,
    rackRect,
    0,
    rackHeightM,
  );
  cameraOcclusionProxy(
    context,
    materials,
    `${fitout.id} · GARAGE-SHELF · súvislý objem pre kameru`,
    overSink.footprintMm,
    Math.min(...overSink.elevationsMm) * MM_TO_M - 0.04,
    Math.max(...overSink.elevationsMm) * MM_TO_M + 0.08,
  );
}

function softEllipsoid(
  context: InteriorBuildContext,
  name: string,
  centerMm: Point2Mm,
  sizeM: readonly [planXM: number, heightM: number, planYM: number],
  centerElevationM: number,
  material: PBRMaterial,
) {
  const mesh = CreateSphere(name, { diameter: 2, segments: 32 }, context.scene);
  mesh.position.set(xM(centerMm.x), centerElevationM, zM(centerMm.y));
  mesh.scaling.set(sizeM[0] / 2, sizeM[1] / 2, sizeM[2] / 2);
  return finish(context, mesh, material, { shadow: true, pickable: true });
}

function softCapsule(
  context: InteriorBuildContext,
  name: string,
  centerMm: Point2Mm,
  centerElevationM: number,
  lengthM: number,
  radiusM: number,
  orientation: Vector3,
  scaling: readonly [x: number, y: number, z: number],
  material: PBRMaterial,
) {
  const mesh = CreateCapsule(
    name,
    {
      height: lengthM,
      radius: radiusM,
      tessellation: 28,
      capSubdivisions: 8,
      subdivisions: 2,
      orientation,
    },
    context.scene,
  );
  mesh.position.set(xM(centerMm.x), centerElevationM, zM(centerMm.y));
  mesh.scaling.set(scaling[0], scaling[1], scaling[2]);
  return finish(context, mesh, material, { shadow: true, pickable: true });
}

function navigationGuard(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  name: string,
  rect: RectMm,
) {
  const guard = texturedBox(
    context.scene,
    name,
    rectCenter(rect),
    rect.x1 - rect.x0,
    rect.y1 - rect.y0,
    6,
    -2,
    1,
  );
  finish(context, guard, materials.livingCabinet, { collide: true });
  guard.isVisible = false;
  guard.metadata = { ...(guard.metadata ?? {}), walkCollisionOnly: true };
  return guard;
}

/**
 * One stable camera volume for a visually busy storage assembly. Individual
 * shelves and boxes stay pickable, while the chase boom cannot thread through
 * their gaps and end up inside a texture.
 */
function cameraOcclusionProxy(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  name: string,
  rect: RectMm,
  bottomM: number,
  topM: number,
) {
  const proxy = texturedBox(
    context.scene,
    name,
    rectCenter(rect),
    rect.x1 - rect.x0,
    rect.y1 - rect.y0,
    Math.max(0.01, topM - bottomM),
    bottomM,
    1,
  );
  finish(context, proxy, materials.livingCabinet, {
    cameraOccluder: true,
  });
  proxy.isVisible = false;
  proxy.receiveShadows = false;
  proxy.metadata = {
    ...(proxy.metadata ?? {}),
    cameraOcclusionProxy: true,
  };
  return proxy;
}

function hallwayWardrobeFrontX(
  wardrobe: HallwayBuiltInWardrobe,
  insetMm: number,
) {
  return wardrobe.facing === "EAST"
    ? wardrobe.footprintMm.x1 - insetMm
    : wardrobe.footprintMm.x0 + insetMm;
}

/**
 * Full-height, handleless oak cabinetry fitted into the measured recesses.
 * End clearances leave room for projecting door linings beside the hall end.
 * One smooth invisible guard per cabinet provides stable avatar
 * collision without catching on panel reveals or the reeded accent.
 */
function buildHallwayBuiltInWardrobes(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
) {
  for (const wardrobe of HALLWAY_BUILT_IN_WARDROBES) {
    const endClearance = wardrobe.endClearanceMm ?? 0;
    const rect = { ...wardrobe.footprintMm,
      y0: wardrobe.footprintMm.y0 + endClearance,
      y1: wardrobe.footprintMm.y1 - endClearance,
    };
    const heightM = wardrobe.heightMm * MM_TO_M;
    const bodyRect: RectMm = wardrobe.facing === "EAST"
      ? { ...rect, x1: rect.x1 - 38 }
      : { ...rect, x0: rect.x0 + 38 };
    const carcase = texturedBox(
      context.scene,
      `${wardrobe.id} · CARCASE · celovýšková zapustená korpusová skriňa`,
      rectCenter(bodyRect),
      bodyRect.x1 - bodyRect.x0,
      bodyRect.y1 - bodyRect.y0,
      heightM,
      0,
      1.2,
    );
    carcase.metadata = {
      ...(carcase.metadata ?? {}),
      fitoutId: wardrobe.id,
      designSourceId: wardrobe.sourceId,
      architecturalSourceId: wardrobe.architecturalSourceId,
      roomId: wardrobe.roomId,
      furnitureKind: "HALLWAY_BUILT_IN_WARDROBE",
      embeddedInArchitecturalNiche: true,
      facing: wardrobe.facing,
      finish: wardrobe.style.finish,
      opening: wardrobe.style.opening,
    };
    finish(context, carcase, materials.hallwayWardrobeSmokedOak, {
      shadow: true,
      pickable: true,
      cameraOccluder: true,
    });

    const panelSpanMm = (rect.y1 - rect.y0) / wardrobe.doorCount;
    const frontX = hallwayWardrobeFrontX(wardrobe, 15);
    for (let index = 0; index < wardrobe.doorCount; index += 1) {
      const panelY0 = rect.y0 + index * panelSpanMm;
      const panelY1 = panelY0 + panelSpanMm;
      const isReeded = wardrobe.style.reededPanelIndices.includes(index);
      const front = texturedBox(
        context.scene,
        `${wardrobe.id} · DOOR · bezúchytkové dubové čelo ${index + 1}${isReeded ? " · dymový lamelový akcent" : " · zrkadlovo radená dyha"}`,
        { x: frontX, y: (panelY0 + panelY1) / 2 },
        30,
        panelSpanMm - wardrobe.style.panelRevealMm,
        heightM - 0.1,
        0.05,
        1.2,
      );
      front.metadata = {
        ...(front.metadata ?? {}),
        fitoutId: wardrobe.id,
        panelIndex: index,
        veneerPattern: "BOOKMATCHED_VERTICAL_GRAIN",
        handleless: true,
        reededAccent: isReeded,
      };
      finish(
        context,
        front,
        isReeded ? materials.hallwayWardrobeSmokedOak : materials.hallwayWardrobeOak,
        { shadow: true, pickable: true },
      );

      if (isReeded) {
        for (
          let grooveIndex = 0;
          grooveIndex < wardrobe.style.reededGrooveCountPerPanel;
          grooveIndex += 1
        ) {
          const grooveY = panelY0
            + ((grooveIndex + 1) * panelSpanMm)
              / (wardrobe.style.reededGrooveCountPerPanel + 1);
          const groove = texturedBox(
            context.scene,
            `${wardrobe.id} · REEDED-ACCENT · vertikálna dubová lamela ${grooveIndex + 1}`,
            { x: hallwayWardrobeFrontX(wardrobe, 3), y: grooveY },
            6,
            8,
            heightM - 0.2,
            0.1,
            1,
          );
          finish(context, groove, materials.hallwayWardrobeOak, {
            shadow: true,
            pickable: true,
          });
        }
      }

      if (index > 0) {
        const reveal = texturedBox(
          context.scene,
          `${wardrobe.id} · REVEAL · zvislá tieňová škára ${index}`,
          { x: hallwayWardrobeFrontX(wardrobe, 4), y: panelY0 },
          8,
          wardrobe.style.panelRevealMm,
          heightM - 0.17,
          0.085,
          1,
        );
        finish(context, reveal, materials.fireplace);
      }
    }

    const plinth = texturedBox(
      context.scene,
      `${wardrobe.id} · PLINTH · zapustený dymový sokel`,
      {
        x: hallwayWardrobeFrontX(wardrobe, 22),
        y: (rect.y0 + rect.y1) / 2,
      },
      44,
      rect.y1 - rect.y0 - 32,
      wardrobe.style.plinthHeightMm * MM_TO_M,
      0,
      1,
    );
    finish(context, plinth, materials.fireplace, { shadow: true });

    const topReveal = texturedBox(
      context.scene,
      `${wardrobe.id} · REVEAL · horná tieňová škára`,
      {
        x: hallwayWardrobeFrontX(wardrobe, 8),
        y: (rect.y0 + rect.y1) / 2,
      },
      16,
      rect.y1 - rect.y0 - 24,
      0.02,
      heightM - 0.02,
      1,
    );
    finish(context, topReveal, materials.fireplace);

    for (const edge of wardrobe.style.ledEdges) {
      const edgeY = edge === "SOUTH" ? rect.y0 + 12 : rect.y1 - 12;
      const led = texturedBox(
        context.scene,
        `${wardrobe.id} · LED · ${edge === "SOUTH" ? "južná" : "severná"} vertikálna línia ${wardrobe.style.ledCctK} K`,
        { x: hallwayWardrobeFrontX(wardrobe, 3), y: edgeY },
        6,
        20,
        2.22,
        0.18,
        1,
      );
      led.metadata = {
        ...(led.metadata ?? {}),
        fitoutId: wardrobe.id,
        cctK: wardrobe.style.ledCctK,
        integratedCabinetLight: true,
      };
      finish(context, led, materials.warmLight);
    }

    const lightX = wardrobe.facing === "EAST" ? rect.x1 + 150 : rect.x0 - 150;
    const cabinetLight = new PointLight(
      `${wardrobe.id} · LIGHT · mäkké odrazené svetlo chodby`,
      new Vector3(xM(lightX), 1.55, zM((rect.y0 + rect.y1) / 2)),
      context.scene,
    );
    cabinetLight.diffuse = Color3.FromHexString("#ffd0a0");
    cabinetLight.specular = Color3.FromHexString("#765a43");
    cabinetLight.intensity = wardrobe.doorCount === 4 ? 0.16 : 0.1;
    cabinetLight.range = wardrobe.doorCount === 4 ? 3.1 : 2.2;

    navigationGuard(
      context,
      materials,
      `${wardrobe.id} · WARDROBE · hladký navigačný obrys niky`,
      wardrobe.footprintMm,
    );
  }
}

/** Garden-facing parent bedroom with furniture expressed relative to the active bed. */
function buildBedroomFitout(context: InteriorBuildContext, materials: InteriorMaterials) {
  const fitout=BEDROOM_FITOUT, bed=fitout.bed, r=bed.footprintMm, m=bed.mattressFootprintMm;
  const box=(label:string,rect:RectMm,height:number,base:number,material:PBRMaterial,solid=false)=>{
    const mesh=texturedBox(context.scene,`${fitout.id} · ${label}`,rectCenter(rect),rect.x1-rect.x0,rect.y1-rect.y0,height,base,1);
    finish(context,mesh,material,{shadow:solid,pickable:solid,cameraOccluder:solid});
    return mesh;
  };
  box('BED · vlnený koberec', {x0:r.x0,y0:r.y0-160,x1:r.x1+240,y1:r.y1+160},.012,.003,materials.rug);
  box('BED · zapustená podnož',{x0:r.x0+90,y0:r.y0+90,x1:r.x1-90,y1:r.y1-90},.1,.02,materials.fireplace);
  box('BED · čalúnená platforma',r,.19,.1,materials.upholstery,true);
  box('BED · matrac',m,.25,.29,materials.bedroomLinen,true);
  box('BED · čalúnené čelo',bed.headboardRectMm,1.08,.04,materials.upholstery,true);
  for(let i=1;i<4;i++){
    const y=r.y0+(r.y1-r.y0)*i/4;
    box(`BED · šev čela ${i}`,{x0:r.x0+70,y0:y-2,x1:r.x0+74,y1:y+2},.94,.1,materials.accentFabric);
  }
  box('BED · ľanová prikrývka',{x0:m.x0+570,y0:m.y0+20,x1:m.x1-25,y1:m.y1-20},.075,.53,materials.bedroomLinen,true);
  box('BED · vlnený prehoz',{x0:m.x1-560,y0:m.y0+30,x1:m.x1-100,y1:m.y1-30},.035,.605,materials.bedroomThrow,true);
  for(const [i,y] of [r.y0+455,r.y1-455].entries()){
    const pillow=softEllipsoid(context,`${fitout.id} · BED · ľanový vankúš ${i+1}`,{x:m.x0+280,y},[.48,.18,.72],.64,materials.bedroomLinen);
    pillow.rotation.y=i===0?-.035:.035;
  }
  for(const [i,nightstand] of fitout.bedsideRectsMm.entries()){
    box(`NIGHTSTAND · plávajúca dubová zásuvka ${i+1}`,nightstand,.18,.39,materials.hallwayWardrobeOak,true);
    box(`NIGHTSTAND · jemná škára ${i+1}`,{...nightstand,x0:nightstand.x1-3,x1:nightstand.x1},.008,.5,materials.fireplace);
    const center=rectCenter(nightstand);
    const fixture=CreateCylinder(`${fitout.id} · LIGHT · mosadzné čítacie svetlo ${i+1}`,{height:.11,diameter:.065,tessellation:24},context.scene);
    fixture.rotation.z=Math.PI/2;
    fixture.position.set(xM(r.x0+110),1.2,zM(center.y));
    finish(context,fixture,materials.brushedBrass,{shadow:true});
    const led=CreateSphere(`${fitout.id} · LIGHT · teplý difúzor ${i+1}`,{diameter:.046,segments:16},context.scene);
    led.position.set(xM(r.x0+170),1.2,zM(center.y));finish(context,led,materials.warmLight);
    navigationGuard(context,materials,`${fitout.id} · NIGHTSTAND ${i+1} · navigačný obrys`,nightstand);
  }
  const lightCenter={x:14000,y:9300};
  box('LIGHT · stropný profil',{x0:lightCenter.x-20,y0:8700,x1:lightCenter.x+20,y1:9900},.035,2.55,materials.fireplace);
  box('LIGHT · teplý difúzor',{x0:lightCenter.x-12,y0:8720,x1:lightCenter.x+12,y1:9880},.012,2.538,materials.warmLight);
  const light=new PointLight(`${fitout.id} · LIGHT · nepriame osvetlenie`,new Vector3(xM(13350),2.42,zM(9300)),context.scene);
  light.diffuse=Color3.FromHexString('#ffd7b2');light.specular=Color3.FromHexString('#807363');light.intensity=.22;light.range=3.6;
  navigationGuard(context,materials,`${fitout.id} · BED · navigačný obrys`,r);
}

interface ChildRoomThemeMaterials {
  readonly primary: PBRMaterial;
  readonly secondary: PBRMaterial;
  readonly chair: PBRMaterial;
  readonly lightDiffuse: string;
  readonly lightSpecular: string;
}

function childRoomTheme(
  fitout: ChildBedroomFitout,
  materials: InteriorMaterials,
): ChildRoomThemeMaterials {
  return fitout.theme === "SAGE_GLOW"
    ? {
        primary: materials.childSage,
        secondary: materials.childClay,
        chair: materials.childSage,
        lightDiffuse: "#ffd9b0",
        lightSpecular: "#8f735c",
      }
    : {
        primary: materials.childMidnight,
        secondary: materials.childSand,
        chair: materials.childMidnight,
        lightDiffuse: "#ffe0b7",
        lightSpecular: "#756d67",
      };
}

function furnitureForward(facing: FurnitureFacing): Point2Mm {
  switch (facing) {
    case "NORTH":
      return { x: 0, y: 1 };
    case "SOUTH":
      return { x: 0, y: -1 };
    case "EAST":
      return { x: 1, y: 0 };
    default:
      return { x: -1, y: 0 };
  }
}

function furnitureRight(facing: FurnitureFacing): Point2Mm {
  const forward = furnitureForward(facing);
  return { x: forward.y, y: -forward.x };
}

/** A closed, gently lofted textile surface with relaxed folds and a soft hem. */
function childBedding(context: InteriorBuildContext, name: string, rect: RectMm, baseM: number, puffM: number, material: PBRMaterial) {
  const columns=24, rows=40, stride=columns+1, layerSize=stride*(rows+1);
  const positions:number[]=[], indices:number[]=[], uvs:number[]=[], normals:number[]=[];
  for(let layer=0;layer<2;layer++)for(let row=0;row<=rows;row++)for(let col=0;col<=columns;col++){
    const u=col/columns,v=row/rows;
    const loft=Math.pow(Math.sin(Math.PI*u)*Math.sin(Math.PI*v),.4);
    const folds=.009*Math.sin(u*21+v*9)*Math.sin(Math.PI*u)*Math.sin(Math.PI*v);
    positions.push(xM(rect.x0+u*(rect.x1-rect.x0)),baseM+puffM*loft+folds-(layer?.012:0),zM(rect.y0+v*(rect.y1-rect.y0)));
    uvs.push(u,v);
  }
  for(let row=0;row<rows;row++)for(let col=0;col<columns;col++){
    const a=row*stride+col,b=a+1,c=a+stride,d=c+1;
    indices.push(a,b,c,b,d,c, a+layerSize,c+layerSize,b+layerSize,b+layerSize,c+layerSize,d+layerSize);
  }
  const edge=(a:number,b:number)=>indices.push(a,a+layerSize,b,b,a+layerSize,b+layerSize);
  for(let col=0;col<columns;col++){edge(col+1,col);edge(rows*stride+col,rows*stride+col+1);}
  for(let row=0;row<rows;row++){edge(row*stride,(row+1)*stride);edge((row+1)*stride+columns,row*stride+columns);}
  for(let i=0;i<indices.length;i+=3)[indices[i+1],indices[i+2]]=[indices[i+2],indices[i+1]];
  VertexData.ComputeNormals(positions,indices,normals);
  const data=new VertexData();data.positions=positions;data.indices=indices;data.normals=normals;data.uvs=uvs;
  const mesh=new Mesh(name,context.scene);data.applyToMesh(mesh);
  finish(context,mesh,material,{shadow:true,pickable:true});return mesh;
}

/** Keep the existing interior registration and finish around the shared geometry. */
function upholsteredBox(
  context: InteriorBuildContext, name: string, rect: RectMm,
  heightM: number, baseM: number, radiusM: number, material: PBRMaterial,
) {
  const mesh = createUpholsteredBox(context.scene, name, rect, heightM, baseM, radiusM);
  finish(context,mesh,material,{shadow:true,pickable:true});return mesh;
}

/** Rounded upholstery geometry; callers retain their own material and registration. */
export function createUpholsteredBox(
  scene: Scene, name: string, rect: RectMm,
  heightM: number, baseM: number, radiusM: number,
) {
  const half = [(rect.x1-rect.x0)*MM_TO_M/2, heightM/2, (rect.y1-rect.y0)*MM_TO_M/2];
  const radius = Math.min(radiusM, ...half.map(value => value*.95));
  const core = half.map(value => value-radius);
  const samples = half.map(h => [-h,-h+radius*.12,-h+radius*.35,-h+radius*.65,-h+radius,0,h-radius,h-radius*.65,h-radius*.35,h-radius*.12,h]);
  const positions:number[]=[], normals:number[]=[], uvs:number[]=[], indices:number[]=[];
  for(let axis=0;axis<3;axis++)for(const sign of [-1,1]){
    const uAxis=(axis+1)%3, vAxis=(axis+2)%3;
    const us=samples[uAxis], vs=samples[vAxis], start=positions.length/3;
    for(const v of vs)for(const u of us){
      const p=[0,0,0];p[axis]=sign*half[axis];p[uAxis]=u;p[vAxis]=v;
      const q=p.map((value,i)=>Math.max(-core[i],Math.min(core[i],value)));
      const delta=p.map((value,i)=>value-q[i]);
      const length=Math.hypot(...delta);
      const normal=delta.map(value=>value/length);
      positions.push(...q.map((value,i)=>value+normal[i]*radius));
      normals.push(...normal);uvs.push(u+half[uAxis],v+half[vAxis]);
    }
    for(let row=0;row<vs.length-1;row++)for(let col=0;col<us.length-1;col++){
      const a=start+row*us.length+col,b=a+1,c=a+us.length,d=c+1;
      // Match Babylon's clockwise front faces; the exporter preserves this convention.
      if(sign>0)indices.push(a,c,b,b,c,d);else indices.push(a,b,c,b,d,c);
    }
  }
  const data=new VertexData();data.positions=positions;data.normals=normals;data.uvs=uvs;data.indices=indices;
  const mesh=new Mesh(name,scene);data.applyToMesh(mesh);
  const center=rectCenter(rect);mesh.position.set(xM(center.x),baseM+heightM/2,zM(center.y));
  return mesh;
}

function buildChildBed(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  fitout: ChildBedroomFitout,
  theme: ChildRoomThemeMaterials,
) {
  const room = INTERIOR_ROOMS.find((candidate) => candidate.id === fitout.roomId)!;
  const roomRect = roomBoundsMm(room);
  const bed = fitout.bed;
  const bedRect = bed.footprintMm;
  const mattressRect = bed.mattressFootprintMm;
  const rugRect: RectMm = {
    x0: Math.max(roomRect.x0, bedRect.x0 - 170),
    y0: Math.max(roomRect.y0, bedRect.y0 - 150),
    x1: Math.min(roomRect.x1, bedRect.x1 + 110),
    y1: Math.min(roomRect.y1, bedRect.y1 + 150),
  };
  const rug = texturedBox(
    context.scene,
    `${fitout.id} · BED · mäkký vlnený koberec`,
    rectCenter(rugRect),
    rugRect.x1 - rugRect.x0,
    rugRect.y1 - rugRect.y0,
    0.014,
    0.003,
    1,
  );
  finish(context, rug, materials.rug);

  const shadowRect: RectMm = {
    x0: bedRect.x0 + 95,
    y0: bedRect.y0 + 80,
    x1: bedRect.x1 - 95,
    y1: bedRect.y1 - 80,
  };
  const floatingShadow = texturedBox(
    context.scene,
    `${fitout.id} · BED · tieň plávajúceho rámu`,
    rectCenter(shadowRect),
    shadowRect.x1 - shadowRect.x0,
    shadowRect.y1 - shadowRect.y0,
    0.065,
    0.018,
    1,
  );
  finish(context, floatingShadow, materials.fireplace);

  const frameTopM = bed.frameHeightMm * MM_TO_M;
  const upholstery=pbr(context.scene,`${fitout.id}-woven-bed-upholstery`,theme.primary.albedoColor.toHexString(),.98);
  upholstery.sheen.isEnabled=true;upholstery.sheen.intensity=.18;upholstery.sheen.roughness=.95;
  upholsteredBox(context,`${fitout.id} · BED · zaoblený čalúnený rám`,bedRect,
    frameTopM-.065,.065,.055,upholstery);

  const mattressTopM = bed.mattressTopElevationMm * MM_TO_M;
  upholsteredBox(context,`${fitout.id} · BED · matrac ${bed.mattressWidthMm} × ${bed.mattressLengthMm}`,mattressRect,
    mattressTopM-frameTopM,frameTopM,.042,materials.bedroomLinen);

  // Two broad padded panels give the headboard a soft seam without a hard slab silhouette.
  const head=bed.headboardRectMm, middle=(head.x0+head.x1)/2;
  for(const [index,rect] of [{...head,x1:middle-3},{...head,x0:middle+3}].entries()){
    upholsteredBox(context,`${fitout.id} · BED · čalúnené čelo ${index+1}`,rect,
      bed.headboardTopElevationMm*MM_TO_M-.065,.065,.048,upholstery);
  }

  const duvetRect: RectMm = {
    x0: mattressRect.x0 - 15,
    y0: mattressRect.y0 + (bed.facing==='NORTH'?420:20),
    x1: mattressRect.x1 + 15,
    y1: mattressRect.y1 - (bed.facing==='SOUTH'?420:20),
  };
  childBedding(context,`${fitout.id} · BED · mäkko skladaná ľanová prikrývka`,duvetRect,mattressTopM+.008,.065,materials.bedroomLinen);

  const forward = furnitureForward(bed.facing);
  const mattressCenter = rectCenter(mattressRect);
  const pillowCenter: Point2Mm = {
    x: mattressCenter.x - forward.x * (bed.mattressLengthMm / 2 - 270),
    y: mattressCenter.y - forward.y * (bed.mattressLengthMm / 2 - 270),
  };
  for(const [index,offset] of [-335,335].entries()){
    childBedding(context,`${fitout.id} · BED · ľanový vankúš s mäkkým lemom ${index+1}`,
      {x0:pillowCenter.x+offset-300,x1:pillowCenter.x+offset+300,y0:pillowCenter.y-210,y1:pillowCenter.y+210},
      mattressTopM+.025,.13,materials.bedroomLinen);
  }

  const throwCenter: Point2Mm = {
    x: mattressCenter.x + forward.x * (bed.mattressLengthMm / 2 - 270),
    y: mattressCenter.y + forward.y * (bed.mattressLengthMm / 2 - 270),
  };
  const throwLengthMm = 430;
  const throwRect: RectMm = {
    x0: mattressRect.x0 + 35,
    y0: throwCenter.y - throwLengthMm / 2,
    x1: mattressRect.x1 - 35,
    y1: throwCenter.y + throwLengthMm / 2,
  };
  childBedding(context,`${fitout.id} · BED · zložený farebný vlnený prehoz`,throwRect,mattressTopM+.064,.032,theme.secondary);

  navigationGuard(context, materials, `${fitout.id} · BED · navigačný obrys`, bedRect);
}

function buildChildWardrobe(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  fitout: ChildBedroomFitout,
  theme: ChildRoomThemeMaterials,
) {
  const wardrobe = fitout.wardrobe;
  const rect = wardrobe.footprintMm;
  const heightM = wardrobe.heightMm * MM_TO_M;
  // The fronts sit on the face towards the room. Every part is placed by its
  // depth behind that face and its position along it, so the same carcass
  // works backed onto a side wall (facing WEST) or the hall wall (NORTH/SOUTH).
  const forward = furnitureForward(wardrobe.facing);
  const alongY = forward.x !== 0;
  const frontPlane = alongY ? (forward.x < 0 ? rect.x0 : rect.x1) : (forward.y < 0 ? rect.y0 : rect.y1);
  const along0 = alongY ? rect.y0 : rect.x0;
  const along1 = alongY ? rect.y1 : rect.x1;
  const at = (depthMm: number, alongMm: number): Point2Mm => alongY
    ? { x: frontPlane - forward.x * depthMm, y: alongMm }
    : { x: alongMm, y: frontPlane - forward.y * depthMm };
  const size = (thicknessMm: number, spanMm: number): [number, number] => alongY ? [thicknessMm, spanMm] : [spanMm, thicknessMm];
  const bodyDepthMm = (alongY ? rect.x1 - rect.x0 : rect.y1 - rect.y0) - 34;
  const body = texturedBox(
    context.scene,
    `${fitout.id} · WARDROBE · celovýšková vstavaná skriňa`,
    at(34 + bodyDepthMm / 2, (along0 + along1) / 2),
    ...size(bodyDepthMm, along1 - along0),
    heightM,
    0,
    1.2,
  );
  finish(context, body, theme.primary, {
    shadow: true,
    pickable: true,
    cameraOccluder: true,
  });

  const frontSpanMm = (along1 - along0) / wardrobe.doorCount;
  for (let index = 0; index < wardrobe.doorCount; index += 1) {
    const a0 = along0 + index * frontSpanMm;
    const a1 = a0 + frontSpanMm;
    const front = texturedBox(
      context.scene,
      `${fitout.id} · WARDROBE · bezúchytkové čelo ${index + 1}`,
      at(15, (a0 + a1) / 2),
      ...size(30, frontSpanMm - 8),
      heightM - 0.1,
      0.05,
      1,
    );
    finish(context, front, index === 1 ? theme.secondary : theme.primary, {
      shadow: true,
      pickable: true,
    });
    if (index > 0) {
      const joint = texturedBox(
        context.scene,
        `${fitout.id} · WARDROBE · tieňová škára ${index}`,
        at(3, a0),
        ...size(10, 8),
        heightM - 0.17,
        0.085,
        1,
      );
      finish(context, joint, materials.fireplace);
    }
  }
  const plinth = texturedBox(
    context.scene,
    `${fitout.id} · WARDROBE · zapustený sokel`,
    at(24, (along0 + along1) / 2),
    ...size(42, along1 - along0 - 50),
    0.075,
    0,
    1,
  );
  finish(context, plinth, materials.fireplace);
  const verticalLight = texturedBox(
    context.scene,
    `${fitout.id} · WARDROBE · integrované ambientné svetlo`,
    at(4, along0 + 16),
    ...size(12, 20),
    2.18,
    0.18,
    1,
  );
  finish(context, verticalLight, materials.warmLight);

  navigationGuard(context, materials, `${fitout.id} · WARDROBE · navigačný obrys`, rect);
}

function buildChildDesk(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  fitout: ChildBedroomFitout,
  theme: ChildRoomThemeMaterials,
) {
  const desk = fitout.desk;
  const rect = desk.footprintMm;
  const topM = desk.topElevationMm * MM_TO_M;
  const topThicknessM = 0.036;
  const desktop = texturedBox(
    context.scene,
    `${fitout.id} · DESK · subtílna dubová pracovná doska`,
    rectCenter(rect),
    rect.x1 - rect.x0,
    rect.y1 - rect.y0,
    topThicknessM,
    topM - topThicknessM,
    1.2,
  );
  finish(context, desktop, materials.kitchenFront, { shadow: true, pickable: true });

  const legHeightM = topM - topThicknessM - 0.02;
  for (const [index, point] of [
    { x: rect.x0 + 90, y: rect.y0 + 80 },
    { x: rect.x1 - 90, y: rect.y0 + 80 },
    { x: rect.x0 + 90, y: rect.y1 - 80 },
    { x: rect.x1 - 90, y: rect.y1 - 80 },
  ].entries()) {
    const leg = texturedBox(
      context.scene,
      `${fitout.id} · DESK · štíhla kovová noha ${index + 1}`,
      point,
      34,
      34,
      legHeightM,
      0.02,
      1,
    );
    finish(context, leg, materials.fireplace, { shadow: true });
  }

  const forward = furnitureForward(desk.facing);
  const deskCenter = rectCenter(rect);
  const drawerCenter: Point2Mm = {
    x: deskCenter.x - forward.x * 80,
    y: deskCenter.y - forward.y * 80,
  };
  const drawer = texturedBox(
    context.scene,
    `${fitout.id} · DESK · plávajúca zásuvka`,
    drawerCenter,
    620,
    220,
    0.12,
    topM - 0.17,
    1,
  );
  finish(context, drawer, theme.primary, { shadow: true, pickable: true });

  const lampBase = CreateCylinder(
    `${fitout.id} · DESK · bezdrôtová stolová lampa`,
    { height: 0.045, diameter: 0.18, tessellation: 32 },
    context.scene,
  );
  const right = furnitureRight(desk.facing);
  const lampCenter: Point2Mm = {
    x: deskCenter.x + right.x * 520 - forward.x * 120,
    y: deskCenter.y + right.y * 520 - forward.y * 120,
  };
  lampBase.position.set(xM(lampCenter.x), topM + 0.023, zM(lampCenter.y));
  finish(context, lampBase, materials.brushedBrass, { shadow: true, pickable: true });
  const lampGlow = CreateSphere(
    `${fitout.id} · DESK · mäkké svetlo lampy`,
    { diameter: 0.16, segments: 24 },
    context.scene,
  );
  lampGlow.position.set(xM(lampCenter.x), topM + 0.22, zM(lampCenter.y));
  finish(context, lampGlow, materials.warmLight);

  navigationGuard(context, materials, `${fitout.id} · DESK · navigačný obrys`, rect);
}

function buildChildRollingChair(
  context: InteriorBuildContext, materials: InteriorMaterials,
  fitout: ChildBedroomFitout, theme: ChildRoomThemeMaterials,
) {
  const chair=fitout.chair, c=chair.centerMm, seat=chair.seatElevationMm*MM_TO_M;
  for(const dx of [-145,145])for(const dy of [-135,135]){
    const leg=CreateCylinder(`${fitout.id} · CHAIR · pevná dubová noha ${dx}/${dy}`,{height:seat-.04,diameter:.035,tessellation:16},context.scene);
    leg.position.set(xM(c.x+dx),(seat-.04)/2,zM(c.y+dy));finish(context,leg,materials.kitchenFront,{shadow:true});
  }
  softEllipsoid(context,`${fitout.id} · CHAIR · zaoblený detský sedák`,c,[.39,.07,.36],seat,theme.chair);
  const f=furnitureForward(chair.facing);
  softEllipsoid(context,`${fitout.id} · CHAIR · nízke zaoblené operadlo`,{x:c.x-f.x*145,y:c.y-f.y*145},[.37,.27,.055],seat+.16,theme.chair);
  navigationGuard(context,materials,`${fitout.id} · CHAIR · navigačný obrys`,chair.footprintMm);
}

function buildChildFeatureWall(
  context: InteriorBuildContext, materials: InteriorMaterials,
  fitout: ChildBedroomFitout, theme: ChildRoomThemeMaterials,
) {
  const r=fitout.featureWall.footprintMm, center=rectCenter(r);
  const panel=texturedBox(context.scene,`${fitout.id} · FEATURE · nízky umývateľný farebný panel`,center,r.x1-r.x0,r.y1-r.y0,1.08,0,1);
  finish(context,panel,theme.primary,{shadow:true});
  const trim=texturedBox(context.scene,`${fitout.id} · FEATURE · dubová krycia lišta`,{x:r.x1+6,y:center.y},18,r.y1-r.y0,.025,1.08,1);
  finish(context,trim,materials.kitchenFront,{shadow:true});
  const artY=(fitout.bed.footprintMm.y0+fitout.bed.footprintMm.y1)/2;
  const frame=texturedBox(context.scene,`${fitout.id} · ART · dubový rám obrazu`,{x:r.x1+22,y:artY},35,680,.84,1.34,1);
  finish(context,frame,materials.kitchenFront,{shadow:true});
  const art=CreatePlane(`${fitout.id} · ART · autorská detská ilustrácia`,{width:.64,height:.80,sideOrientation:Mesh.DOUBLESIDE},context.scene);
  art.rotation.y=-Math.PI/2;art.position.set(xM(r.x1+41),1.76,zM(artY));
  const mat=pbr(context.scene,`${fitout.id}-print-art`,"#ffffff",.98);
  mat.albedoTexture=new Texture(fitout.artUrl,context.scene,false,false);
  mat.backFaceCulling=false;finish(context,art,mat);
}

function buildChildPinboard(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  fitout: ChildBedroomFitout,
  theme: ChildRoomThemeMaterials,
) {
  const pinboard = fitout.pinboard;
  const rect = pinboard.footprintMm;
  const bottomM = pinboard.bottomElevationMm * MM_TO_M;
  const heightM = pinboard.heightMm * MM_TO_M;
  const board = texturedBox(
    context.scene,
    `${fitout.id} · DESK · veľká korková moodboard plocha`,
    rectCenter(rect),
    rect.x1 - rect.x0,
    rect.y1 - rect.y0,
    heightM,
    bottomM,
    1,
  );
  finish(context, board, materials.childCork, { shadow: true, pickable: true });

  const alongX = pinboard.facing !== 'WEST';
  const longStart = alongX ? rect.x0 : rect.y0;
  const longEnd = alongX ? rect.x1 : rect.y1;
  const noteMaterials = [theme.secondary, materials.kitchenUpper, theme.primary];
  for (let index = 0; index < 3; index += 1) {
    const along = longStart + (index + 1) * ((longEnd - longStart) / 4);
    const noteCenter: Point2Mm = alongX
      ? { x: along, y: pinboard.facing === "SOUTH" ? rect.y0 - 6 : rect.y1 + 6 }
      : { x: rect.x0 - 6, y: along };
    const note = texturedBox(
      context.scene,
      `${fitout.id} · DESK · moodboard karta ${index + 1}`,
      noteCenter,
      alongX ? 180 : 8,
      alongX ? 8 : 180,
      0.15,
      bottomM + 0.12 + index * 0.1,
      1,
    );
    finish(context, note, noteMaterials[index], { pickable: true });
  }
}

function buildChildRoomLighting(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  fitout: ChildBedroomFitout,
  theme: ChildRoomThemeMaterials,
) {
  const room = INTERIOR_ROOMS.find((candidate) => candidate.id === fitout.roomId)!;
  const bounds = roomBoundsMm(room);
  const center = rectCenter(bounds);
  const housing=CreateCylinder(`${fitout.id} · LIGHT · okrúhle stropné svietidlo`,{height:.11,diameter:.62,tessellation:48},context.scene);
  housing.position.set(xM(center.x),room.clearHeightMm*MM_TO_M-.07,zM(center.y));finish(context,housing,materials.kitchenFront);
  const diffuser=CreateCylinder(`${fitout.id} · LIGHT · teplý opálový difúzor`,{height:.02,diameter:.57,tessellation:48},context.scene);
  diffuser.position.set(xM(center.x),room.clearHeightMm*MM_TO_M-.13,zM(center.y));finish(context,diffuser,materials.warmLight);
  const light = new PointLight(
    `${fitout.id} · LIGHT · mäkké večerné svetlo`,
    new Vector3(xM(center.x), 2.42, zM(center.y)),
    context.scene,
  );
  light.diffuse = Color3.FromHexString(theme.lightDiffuse);
  light.specular = Color3.FromHexString(theme.lightSpecular);
  light.intensity = 0.22;
  light.range = 3.4;
}

function buildChildPlayAndStorage(context:InteriorBuildContext,materials:InteriorMaterials,fitout:ChildBedroomFitout,theme:ChildRoomThemeMaterials){
  const box=(label:string,r:RectMm,h:number,base:number,mat:PBRMaterial)=>{
    const m=texturedBox(context.scene,`${fitout.id} · ${label}`,rectCenter(r),r.x1-r.x0,r.y1-r.y0,h,base,1);
    finish(context,m,mat,{shadow:true,pickable:true});return m;
  };
  // The low toy shelf on the hall wall gave way to the wardrobe; the bookcase stays.
  const north=fitout.storageFacing==='NORTH';
  const b=fitout.bookcaseRectMm;
  box('BOOKS · nízka dubová knižnica',b,.065,.03,materials.kitchenFront);
  for(const x of [b.x0,b.x1-20])box('BOOKS · bočnica',{...b,x0:x,x1:x+20},.62,.03,materials.kitchenFront);
  for(const base of [.10,.34]){
    box(`BOOKS · polica ${base}`,b,.025,base,materials.kitchenFront);
    for(let i=0;i<5;i++){
      const y=north?b.y0+100:b.y1-140;
      box(`BOOKS · obrázková kniha ${base}/${i}`,{x0:b.x0+40+i*110,y0:y,x1:b.x0+125+i*110,y1:y+35},.16+(i%2)*.03,base+.025,i%3===0?theme.primary:i%3===1?theme.secondary:materials.bedroomLinen);
    }
  }
  navigationGuard(context,materials,`${fitout.id} · BOOKS · navigačný obrys`,b);
  const read=fitout.readingRectMm,c=rectCenter(read),w=(read.x1-read.x0)*MM_TO_M,d=(read.y1-read.y0)*MM_TO_M;
  softEllipsoid(context,`${fitout.id} · READING · mäkký čitateľský puf`,c,[w,.23,d],.14,theme.secondary);
  softEllipsoid(context,`${fitout.id} · READING · oporný vankúš`,{x:read.x0+150,y:c.y},[.25,.39,d*.8],.29,theme.primary);
  navigationGuard(context,materials,`${fitout.id} · READING · navigačný obrys`,read);
  const play=fitout.clearPlayRectMm;
  box('PLAY · mäkký centrálny koberec',play,.012,.005,materials.rug);
  box('PLAY · farebný lem koberca',{...play,x0:play.x0+30,x1:play.x0+55},.004,.018,theme.secondary);
  // Drawing supplies stay on the tabletop; the play/circulation floor stays clear.
  const desk=fitout.desk.footprintMm,dc=rectCenter(desk),top=fitout.desk.topElevationMm*MM_TO_M;
  box('DRAWING · papier na kreslenie',{x0:dc.x-200,y0:dc.y-140,x1:dc.x+200,y1:dc.y+140},.004,top+.003,materials.bedroomLinen);
  for(let i=0;i<5;i++)box(`DRAWING · pastelka ${i}`,{x0:dc.x-90+i*34,y0:dc.y-75,x1:dc.x-83+i*34,y1:dc.y+60},.007,top+.008,i%2?theme.primary:theme.secondary);
}

/**
 * Premium but restrained children's rooms: one sage/clay composition and one
 * midnight/sand composition, both using the same ergonomic furniture contract
 * and collision envelopes while respecting their very different plans.
 */
function buildChildrensBedroomFitouts(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
) {
  for (const fitout of CHILDRENS_BEDROOM_FITOUTS) {
    const theme = childRoomTheme(fitout, materials);
    buildChildFeatureWall(context, materials, fitout, theme);
    buildChildBed(context, materials, fitout, theme);
    buildChildWardrobe(context, materials, fitout, theme);
    buildChildDesk(context, materials, fitout, theme);
    buildChildRollingChair(context, materials, fitout, theme);
    buildChildPinboard(context, materials, fitout, theme);
    buildChildRoomLighting(context, materials, fitout, theme);
    buildChildPlayAndStorage(context,materials,fitout,theme);
  }
}

/**
 * Compact entry composition in the 1.01 recess: closed coat storage at the
 * corridor end, a low shoe cabinet/bench at the front door and an illuminated
 * oak hook niche between them. The two floor guards deliberately follow only
 * the solid modules, leaving the generous central circulation area untouched.
 */
function buildEntryFitout(context: InteriorBuildContext, materials: InteriorMaterials) {
  const fitout=ENTRY_FITOUT, r=fitout.bench.footprintMm, panel=fitout.hookPanel.footprintMm;
  const box=(label:string,rect:RectMm,height:number,base:number,material:PBRMaterial)=>{
    const mesh=texturedBox(context.scene,`${fitout.id} · ${label}`,rectCenter(rect),rect.x1-rect.x0,rect.y1-rect.y0,height,base,1);
    finish(context,mesh,material,{shadow:true,pickable:true,cameraOccluder:true});return mesh;
  };
  box('BENCH · dubový botník',r,.35,.07,materials.hallwayWardrobeOak);
  box('BENCH · zapustený sokel',{x0:r.x0+30,y0:r.y0+30,x1:r.x1-30,y1:r.y1-30},.07,0,materials.fireplace);
  box('BENCH · tieňová škára zásuviek',{x0:r.x1-3,y0:(r.y0+r.y1)/2-3,x1:r.x1,y1:(r.y0+r.y1)/2+3},.28,.1,materials.fireplace);
  box('BENCH · čalúnený sedák',{x0:r.x0+15,y0:r.y0+15,x1:r.x1-15,y1:r.y1-15},.05,.42,materials.officeFabric);
  box('HOOKS · dubový závesný panel',panel,1.45,.45,materials.hallwayWardrobeOak);
  for(const [i,y] of [r.y0+170,(r.y0+r.y1)/2,r.y1-170].entries()){
    const hook=CreateCylinder(`${fitout.id} · HOOKS · mosadzný háčik ${i+1}`,{height:.075,diameter:.025,tessellation:20},context.scene);
    hook.rotation.z=Math.PI/2;hook.position.set(xM(panel.x1+37),1.55,zM(y));finish(context,hook,materials.brushedBrass,{shadow:true,pickable:true});
  }
  box('OVERHEAD · horná úložná skriňa',{x0:r.x0,y0:r.y0,x1:r.x0+320,y1:r.y1},.48,2.02,materials.hallwayWardrobeOak);
  box('LIGHT · skryté svetlo nad lavičkou',{x0:r.x0+300,y0:r.y0+30,x1:r.x0+312,y1:r.y1-30},.012,2.008,materials.warmLight);
  // Mirror on the solid office-side wall leaves the entrance glazing unobstructed.
  // It hangs 13 mm off the west face of the 300 mm bearing wall of the office.
  const officeWallFace=INTERIOR_WALLS.find(w=>w.id==='C-ENTRY-OFFICE-EAST')!.rectMm.x0;
  box('MIRROR · vysoké zrkadlo',{x0:officeWallFace-27,y0:3670,x1:officeWallFace-13,y1:4220},1.65,.38,materials.mirrorGlass);
  navigationGuard(context,materials,`${fitout.id} · BENCH · navigačný obrys`,r);
}

function buildOfficeFitout(context: InteriorBuildContext, materials: InteriorMaterials) {
  const fitout = OFFICE_FITOUT;
  const cabinet = fitout.cabinet;
  const cabinetRect = cabinet.footprintMm;
  const niche = cabinet.printerNiche;
  const nicheRect = niche.footprintMm;
  const cabinetHeightM = cabinet.heightMm * MM_TO_M;
  const nicheBottomM = niche.bottomElevationMm * MM_TO_M;
  const nicheHeightM = niche.heightMm * MM_TO_M;

  // Full-height handleless wall. The cabinet now sits on the east facade and
  // opens west into the room; the printer bay remains a real void between the
  // lower and upper carcasses rather than a decal on a solid box.
  const closedBay: RectMm = {
    x0: cabinetRect.x0,
    y0: cabinetRect.y0,
    x1: cabinetRect.x1,
    y1: nicheRect.y0,
  };
  const closedBody = texturedBox(
    context.scene,
    `${fitout.id} · CABINET · plná bezúchytková skriňová stena`,
    rectCenter(closedBay),
    closedBay.x1 - closedBay.x0,
    closedBay.y1 - closedBay.y0,
    cabinetHeightM,
    0,
    1.2,
  );
  finish(context, closedBody, materials.livingCabinet, { shadow: true, pickable: true });

  const nicheLower = texturedBox(
    context.scene,
    `${fitout.id} · CABINET · spodný blok tlačiarňového výklenku`,
    rectCenter({ ...nicheRect, x1: cabinetRect.x1 }),
    cabinetRect.x1 - cabinetRect.x0,
    nicheRect.y1 - nicheRect.y0,
    nicheBottomM,
    0,
    1.2,
  );
  finish(context, nicheLower, materials.livingCabinet, { shadow: true, pickable: true });

  const upperBottomM = nicheBottomM + nicheHeightM;
  const nicheUpper = texturedBox(
    context.scene,
    `${fitout.id} · CABINET · horný blok nad tlačiarňou`,
    rectCenter({ ...nicheRect, x1: cabinetRect.x1 }),
    cabinetRect.x1 - cabinetRect.x0,
    nicheRect.y1 - nicheRect.y0,
    cabinetHeightM - upperBottomM,
    upperBottomM,
    1.2,
  );
  finish(context, nicheUpper, materials.livingCabinet, {
    shadow: true,
    pickable: true,
    cameraOccluder: true,
  });

  if (nicheRect.y1 < cabinetRect.y1) {
    const endPanelRect: RectMm = {
      x0: cabinetRect.x0,
      y0: nicheRect.y1,
      x1: cabinetRect.x1,
      y1: cabinetRect.y1,
    };
    const endPanel = texturedBox(
      context.scene,
      `${fitout.id} · CABINET · severný ukončovací panel`,
      rectCenter(endPanelRect),
      endPanelRect.x1 - endPanelRect.x0,
      endPanelRect.y1 - endPanelRect.y0,
      cabinetHeightM,
      0,
      1.2,
    );
    finish(context, endPanel, materials.livingCabinet, { shadow: true });
  }

  const nicheBack = texturedBox(
    context.scene,
    `${fitout.id} · CABINET · tmavý chrbát tlačiarňového výklenku`,
    { x: nicheRect.x1 - 8, y: (nicheRect.y0 + nicheRect.y1) / 2 },
    16,
    nicheRect.y1 - nicheRect.y0 - 26,
    nicheHeightM - 0.026,
    nicheBottomM + 0.013,
    1,
  );
  finish(context, nicheBack, materials.fireplace, { shadow: true });

  for (const [index, sideY] of [nicheRect.y0 + 12, nicheRect.y1 - 12].entries()) {
    const lining = texturedBox(
      context.scene,
      `${fitout.id} · CABINET · bočnica výklenku ${index + 1}`,
      { x: (nicheRect.x0 + nicheRect.x1) / 2, y: sideY },
      nicheRect.x1 - nicheRect.x0,
      24,
      nicheHeightM,
      nicheBottomM,
      1,
    );
    finish(context, lining, materials.fireplace, { shadow: true });
  }
  const nicheShelf = texturedBox(
    context.scene,
    `${fitout.id} · CABINET · dubová polica pod tlačiarňou`,
    rectCenter(nicheRect),
    nicheRect.x1 - nicheRect.x0 + 12,
    nicheRect.y1 - nicheRect.y0 - 8,
    0.026,
    nicheBottomM,
    1.1,
  );
  finish(context, nicheShelf, materials.kitchenFront, { shadow: true, pickable: true });
  const nicheLight = texturedBox(
    context.scene,
    `${fitout.id} · CABINET · 2700 K svetlo vo výklenku`,
    { x: nicheRect.x0 + 18, y: (nicheRect.y0 + nicheRect.y1) / 2 },
    18,
    nicheRect.y1 - nicheRect.y0 - 70,
    0.018,
    upperBottomM - 0.024,
    1,
  );
  finish(context, nicheLight, materials.warmLight);

  // Subtle front joints preserve the scale of the floor-to-ceiling joinery.
  for (const [index, seamY] of [
    closedBay.y0 + (closedBay.y1 - closedBay.y0) / 3,
    closedBay.y0 + (2 * (closedBay.y1 - closedBay.y0)) / 3,
  ].entries()) {
    const seam = texturedBox(
      context.scene,
      `${fitout.id} · CABINET · zvislá tieňová škára ${index + 1}`,
      { x: cabinetRect.x0 - 3, y: seamY },
      7,
      4,
      cabinetHeightM - 0.12,
      0.06,
      1,
    );
    finish(context, seam, materials.fireplace);
  }
  const cabinetPlinth = texturedBox(
    context.scene,
    `${fitout.id} · CABINET · zapustená tmavá soklová línia`,
    { x: cabinetRect.x0 - 4, y: (cabinetRect.y0 + cabinetRect.y1) / 2 },
    12,
    cabinetRect.y1 - cabinetRect.y0 - 28,
    0.055,
    0,
    1,
  );
  finish(context, cabinetPlinth, materials.fireplace);

  // Integrated printer: calm white body, black output slot and a minimal
  // touch panel remain visible within the open cabinet bay.
  const printer = fitout.printer;
  const printerCenter = rectCenter(printer.footprintMm);
  const printerBaseM = printer.baseElevationMm * MM_TO_M;
  const printerHeightM = printer.heightMm * MM_TO_M;
  const printerBody = texturedBox(
    context.scene,
    `${fitout.id} · PRINTER · biele telo integrovanej tlačiarne`,
    printerCenter,
    printer.footprintMm.x1 - printer.footprintMm.x0,
    printer.footprintMm.y1 - printer.footprintMm.y0,
    printerHeightM,
    printerBaseM,
    0.8,
  );
  finish(context, printerBody, materials.applianceEnamel, { shadow: true, pickable: true });
  const outputSlot = texturedBox(
    context.scene,
    `${fitout.id} · PRINTER · čierny výstup papiera`,
    { x: printer.footprintMm.x0 - 4, y: printerCenter.y },
    10,
    300,
    0.052,
    printerBaseM + 0.085,
    1,
  );
  finish(context, outputSlot, materials.blackGlass, { pickable: true });
  const printerPanel = texturedBox(
    context.scene,
    `${fitout.id} · PRINTER · dotykový ovládací panel`,
    { x: printer.footprintMm.x0 - 7, y: printer.footprintMm.y0 + 78 },
    12,
    104,
    0.052,
    printerBaseM + printerHeightM - 0.072,
    1,
  );
  finish(context, printerPanel, materials.blackGlass, { pickable: true });
  const paper = texturedBox(
    context.scene,
    `${fitout.id} · PRINTER · čistý papier vo výstupe`,
    { x: printer.footprintMm.x0 - 16, y: printerCenter.y },
    130,
    255,
    0.006,
    printerBaseM + 0.13,
    1,
  );
  finish(context, paper, materials.kitchenUpper);

  // Slim oak desk with a powder-coated frame and concealed cable tray.
  const desk = fitout.desk;
  const deskRect = desk.footprintMm;
  const deskTopM = desk.topElevationMm * MM_TO_M;
  const deskThicknessM = 0.035;
  const desktop = texturedBox(
    context.scene,
    `${fitout.id} · DESK · subtílna dubová pracovná doska`,
    rectCenter(deskRect),
    deskRect.x1 - deskRect.x0,
    deskRect.y1 - deskRect.y0,
    deskThicknessM,
    deskTopM - deskThicknessM,
    1.2,
  );
  finish(context, desktop, materials.kitchenFront, { shadow: true, pickable: true });

  const legHeightM = deskTopM - deskThicknessM - 0.015;
  for (const [frameIndex, frameY] of [deskRect.y0 + 135, deskRect.y1 - 135].entries()) {
    for (const xMm of [deskRect.x0 + 72, deskRect.x1 - 72]) {
      const leg = texturedBox(
        context.scene,
        `${fitout.id} · DESK · čierna noha rámu ${frameIndex + 1}`,
        { x: xMm, y: frameY },
        36,
        42,
        legHeightM,
        0.015,
        1,
      );
      finish(context, leg, materials.fireplace, { shadow: true });
    }
    const frameRail = texturedBox(
      context.scene,
      `${fitout.id} · DESK · horná priečka rámu ${frameIndex + 1}`,
      { x: (deskRect.x0 + deskRect.x1) / 2, y: frameY },
      deskRect.x1 - deskRect.x0 - 126,
      42,
      0.036,
      deskTopM - deskThicknessM - 0.052,
      1,
    );
    finish(context, frameRail, materials.fireplace, { shadow: true });
  }
  const cableTray = texturedBox(
    context.scene,
    `${fitout.id} · DESK · skrytý káblový žľab`,
    { x: deskRect.x0 + 150, y: (deskRect.y0 + deskRect.y1) / 2 },
    150,
    880,
    0.09,
    deskTopM - 0.14,
    1,
  );
  finish(context, cableTray, materials.fireplace, { shadow: true });

  // Curved 40-inch 21:9 ultrawide. Nine tangential panels run along plan Y;
  // their concave face points east toward the chair while the compact 2500R
  // shell stays close to the west wall above the oak top.
  const monitor = desk.monitor;
  const segmentCount = 9;
  const segmentWidthMm = monitor.widthMm / segmentCount;
  const curveRadiusMm = monitor.curveRadiusMm;
  const shellBottomM = (monitor.centerElevationMm - monitor.heightMm / 2) * MM_TO_M;
  for (let index = 0; index < segmentCount; index += 1) {
    const offsetMm = -monitor.widthMm / 2 + segmentWidthMm * (index + 0.5);
    const radiusAlongMm = Math.sqrt(Math.max(1, curveRadiusMm ** 2 - offsetMm ** 2));
    const curveDepthMm = curveRadiusMm - radiusAlongMm;
    const yaw = -Math.asin(offsetMm / curveRadiusMm);
    const shellCenter: Point2Mm = {
      x: monitor.centerMm.x + curveDepthMm,
      y: monitor.centerMm.y + offsetMm,
    };
    const shell = texturedBox(
      context.scene,
      `${fitout.id} · MONITOR-40-21:9 · zakrivený zadný segment ${index + 1}`,
      shellCenter,
      monitor.maxThicknessMm,
      segmentWidthMm + 5,
      monitor.heightMm * MM_TO_M,
      shellBottomM,
      1,
    );
    shell.rotation.y = yaw;
    finish(context, shell, materials.fireplace, { shadow: true, pickable: true });

    const normalX = radiusAlongMm / curveRadiusMm;
    const normalY = -offsetMm / curveRadiusMm;
    const glassOffsetMm = monitor.maxThicknessMm / 2 + 3;
    const glass = texturedBox(
      context.scene,
      `${fitout.id} · MONITOR-40-21:9 · obrazový segment ${index + 1}`,
      {
        x: shellCenter.x + normalX * glassOffsetMm,
        y: shellCenter.y + normalY * glassOffsetMm,
      },
      4,
      segmentWidthMm + 1,
      (monitor.heightMm - 16) * MM_TO_M,
      shellBottomM + 0.008,
      1,
    );
    glass.rotation.y = yaw;
    finish(context, glass, materials.tvScreen, { pickable: true });
  }
  const monitorBase = texturedBox(
    context.scene,
    `${fitout.id} · MONITOR-40-21:9 · subtílna stolová základňa`,
    { x: monitor.centerMm.x + 35, y: monitor.centerMm.y },
    220,
    410,
    0.018,
    deskTopM + 0.002,
    1,
  );
  finish(context, monitorBase, materials.fireplace, { shadow: true });
  const screenBottomM = monitor.centerElevationMm * MM_TO_M - monitor.heightMm * MM_TO_M / 2;
  const postHeightM = Math.max(0.12, screenBottomM - deskTopM + 0.035);
  const monitorPost = texturedBox(
    context.scene,
    `${fitout.id} · MONITOR-40-21:9 · centrálny stojan`,
    { x: monitor.centerMm.x - 20, y: monitor.centerMm.y },
    46,
    54,
    postHeightM,
    deskTopM + 0.018,
    1,
  );
  finish(context, monitorPost, materials.fireplace, { shadow: true });

  // Premium ergonomic chair: five-star base, adjustable arms, deep seat,
  // articulated lumbar support and a soft high back with headrest.
  const chair = fitout.chair;
  const chairCenter = chair.centerMm;
  const seatM = chair.seatElevationMm * MM_TO_M;
  const chairWidthM = (chair.footprintMm.y1 - chair.footprintMm.y0) * MM_TO_M;
  const chairDepthM = (chair.footprintMm.x1 - chair.footprintMm.x0) * MM_TO_M;
  const hub = CreateCylinder(
    `${fitout.id} · CHAIR · centrálna päťramenná báza`,
    { height: 0.09, diameter: 0.13, tessellation: 28 },
    context.scene,
  );
  hub.position.set(xM(chairCenter.x), 0.105, zM(chairCenter.y));
  finish(context, hub, materials.fireplace, { shadow: true });
  const lift = CreateCylinder(
    `${fitout.id} · CHAIR · plynový piest`,
    { height: Math.max(0.2, seatM - 0.18), diameter: 0.055, tessellation: 24 },
    context.scene,
  );
  lift.position.set(xM(chairCenter.x), 0.15 + Math.max(0.2, seatM - 0.18) / 2, zM(chairCenter.y));
  finish(context, lift, materials.steel, { shadow: true });

  for (let index = 0; index < 5; index += 1) {
    const angle = (index / 5) * Math.PI * 2;
    const spokeLengthMm = 335;
    const spokeCenter: Point2Mm = {
      x: chairCenter.x + Math.cos(angle) * spokeLengthMm * 0.5,
      y: chairCenter.y + Math.sin(angle) * spokeLengthMm * 0.5,
    };
    const spoke = texturedBox(
      context.scene,
      `${fitout.id} · CHAIR · rameno pojazdu ${index + 1}`,
      spokeCenter,
      spokeLengthMm,
      34,
      0.032,
      0.065,
      1,
    );
    spoke.rotation.y = angle;
    finish(context, spoke, materials.fireplace, { shadow: true });

    const caster = CreateTorus(
      `${fitout.id} · CHAIR · tiché koliesko ${index + 1}`,
      { diameter: 0.068, thickness: 0.018, tessellation: 20 },
      context.scene,
    );
    caster.rotation.z = Math.PI / 2;
    caster.rotation.y = angle;
    caster.position.set(
      xM(chairCenter.x + Math.cos(angle) * spokeLengthMm),
      0.055,
      zM(chairCenter.y + Math.sin(angle) * spokeLengthMm),
    );
    finish(context, caster, materials.fireplace, { shadow: true });
  }

  softEllipsoid(
    context,
    `${fitout.id} · CHAIR · ergonomický čalúnený sedák`,
    { x: chairCenter.x - 45, y: chairCenter.y },
    [chairDepthM * 0.7, 0.135, chairWidthM * 0.72],
    seatM,
    materials.officeFabric,
  );
  const seatShell = texturedBox(
    context.scene,
    `${fitout.id} · CHAIR · tenká nosná škrupina sedáka`,
    { x: chairCenter.x, y: chairCenter.y },
    chair.footprintMm.x1 - chair.footprintMm.x0 - 180,
    chair.footprintMm.y1 - chair.footprintMm.y0 - 170,
    0.045,
    seatM - 0.105,
    0.8,
  );
  finish(context, seatShell, materials.fireplace, { shadow: true });

  const backCenterX = chairCenter.x + 250;
  const backBottomM = seatM + 0.08;
  const backTopM = chair.backTopElevationMm * MM_TO_M;
  softCapsule(
    context,
    `${fitout.id} · CHAIR · vysoké ergonomické operadlo`,
    { x: backCenterX, y: chairCenter.y },
    (backBottomM + backTopM) / 2,
    backTopM - backBottomM,
    0.18,
    new Vector3(0, 1, 0),
    [0.34, 1, 1.45],
    materials.officeFabric,
  );
  softEllipsoid(
    context,
    `${fitout.id} · CHAIR · nastaviteľná bedrová opora`,
    { x: backCenterX - 72, y: chairCenter.y },
    [0.095, 0.24, 0.48],
    seatM + 0.26,
    materials.accentFabric,
  );
  softEllipsoid(
    context,
    `${fitout.id} · CHAIR · mäkká hlavová opierka`,
    { x: backCenterX + 12, y: chairCenter.y },
    [0.13, 0.17, 0.43],
    backTopM - 0.07,
    materials.officeFabric,
  );
  for (const [index, sideY] of [chairCenter.y - 255, chairCenter.y + 255].entries()) {
    const armPost = texturedBox(
      context.scene,
      `${fitout.id} · CHAIR · nastaviteľná podrúčka ${index + 1}`,
      { x: chairCenter.x - 15, y: sideY },
      42,
      42,
      0.22,
      seatM + 0.02,
      1,
    );
    finish(context, armPost, materials.fireplace, { shadow: true });
    const armPad = softCapsule(
      context,
      `${fitout.id} · CHAIR · mäkká opierka ruky ${index + 1}`,
      { x: chairCenter.x - 75, y: sideY },
      seatM + 0.245,
      0.31,
      0.04,
      new Vector3(1, 0, 0),
      [1, 0.65, 1],
      materials.officeFabric,
    );
    armPad.rotation.z = 0.02;
  }

  // The frameless marker board stays on the only uninterrupted north-wall bay.
  // Its generous corner gap keeps EAST-01 visually independent while the desk
  // and cabinet exchange the west and east sides of the room.
  const whiteboard = fitout.whiteboard;
  const boardRect = whiteboard.footprintMm;
  const boardBottomM = whiteboard.bottomElevationMm * MM_TO_M;
  const boardHeightM = whiteboard.heightMm * MM_TO_M;
  const boardShadow = texturedBox(
    context.scene,
    `${fitout.id} · WHITEBOARD · tenký čierny tieňový podklad`,
    { x: (boardRect.x0 + boardRect.x1) / 2, y: (boardRect.y0 + boardRect.y1) / 2 + 3 },
    boardRect.x1 - boardRect.x0 + 28,
    boardRect.y1 - boardRect.y0 + 8,
    boardHeightM + 0.028,
    boardBottomM - 0.014,
    1,
  );
  finish(context, boardShadow, materials.fireplace, { shadow: true });
  const board = texturedBox(
    context.scene,
    `${fitout.id} · WHITEBOARD · bezrámová magnetická plocha`,
    rectCenter(boardRect),
    boardRect.x1 - boardRect.x0,
    boardRect.y1 - boardRect.y0,
    boardHeightM,
    boardBottomM,
    1,
  );
  finish(context, board, materials.whiteboardGlass, { shadow: true, pickable: true });
  const markerTray = texturedBox(
    context.scene,
    `${fitout.id} · WHITEBOARD · subtílna magnetická polička na fixky`,
    { x: (boardRect.x0 + boardRect.x1) / 2, y: boardRect.y0 - 42 },
    760,
    84,
    0.024,
    boardBottomM - 0.052,
    1,
  );
  finish(context, markerTray, materials.fireplace, { shadow: true, pickable: true });
  const markerMaterials = [materials.blackGlass, materials.accentFabric, materials.brushedBrass];
  for (const [index, markerX] of [
    (boardRect.x0 + boardRect.x1) / 2 - 120,
    (boardRect.x0 + boardRect.x1) / 2,
    (boardRect.x0 + boardRect.x1) / 2 + 120,
  ].entries()) {
    const marker = texturedBox(
      context.scene,
      `${fitout.id} · WHITEBOARD · fixa ${index + 1}`,
      { x: markerX, y: boardRect.y0 - 66 },
      15,
      105,
      0.016,
      boardBottomM - 0.027,
      1,
    );
    finish(context, marker, markerMaterials[index], { pickable: true });
  }

  // One restrained linear ceiling luminaire follows the wall-facing desk axis.
  const ceilingHousing = texturedBox(
    context.scene,
    `${fitout.id} · LIGHT · čierny lineárny stropný profil`,
    { x: (deskRect.x0 + deskRect.x1) / 2, y: (deskRect.y0 + deskRect.y1) / 2 },
    58,
    1260,
    0.035,
    2.565,
    1,
  );
  finish(context, ceilingHousing, materials.fireplace, { shadow: true });
  const ceilingDiffuser = texturedBox(
    context.scene,
    `${fitout.id} · LIGHT · teplý súvislý difúzor`,
    { x: (deskRect.x0 + deskRect.x1) / 2, y: (deskRect.y0 + deskRect.y1) / 2 },
    34,
    1210,
    0.012,
    2.553,
    1,
  );
  finish(context, ceilingDiffuser, materials.warmLight);
  const officeLight = new PointLight(
    `${fitout.id} · LIGHT · mäkké pracovné svetlo`,
    new Vector3(
      xM((deskRect.x0 + deskRect.x1) / 2),
      2.47,
      zM((deskRect.y0 + deskRect.y1) / 2),
    ),
    context.scene,
  );
  officeLight.diffuse = Color3.FromHexString("#ffd5a6");
  officeLight.specular = Color3.FromHexString("#8f7861");
  officeLight.intensity = 0.24;
  officeLight.range = 3.1;

  navigationGuard(context, materials, `${fitout.id} · CABINET · navigačný obrys`, cabinetRect);
  navigationGuard(context, materials, `${fitout.id} · DESK · navigačný obrys`, deskRect);
  navigationGuard(
    context,
    materials,
    `${fitout.id} · CHAIR · navigačný obrys pojazdu`,
    chair.footprintMm,
  );
}

/**
 * High-end living/dining concept requested on 23. 8. 2026. The source-backed
 * plan positions live in `LIVING_DINING_FITOUT`; this builder only adds finish,
 * soft geometry, integrated lighting and navigation-safe collision envelopes.
 */
/** Unit plan vector a piece of furniture faces. */
function facingVector(facing: FurnitureFacing): Point2Mm {
  switch (facing) {
    case "NORTH":
      return { x: 0, y: 1 };
    case "SOUTH":
      return { x: 0, y: -1 };
    case "EAST":
      return { x: 1, y: 0 };
    default:
      return { x: -1, y: 0 };
  }
}

/**
 * Local frame of a rectangular furniture module: `u` runs along the module
 * from left to right when looking the way it faces, `v` runs from the back
 * edge toward the front. `rect(u0,u1,v0,v1)` returns the plan rectangle and
 * `local(rect)` the inverse, so cushion layouts can be written once for any
 * orientation. `tilt` leans a mesh backward about the module's long axis.
 */
function moduleFrame(body: RectMm, facing: FurnitureFacing) {
  const V = facingVector(facing);
  const U = { x: V.y, y: -V.x };
  const origin: Point2Mm = {
    x: U.x + V.x > 0 ? body.x0 : body.x1,
    y: U.y + V.y > 0 ? body.y0 : body.y1,
  };
  const point = (u: number, v: number): Point2Mm => ({
    x: origin.x + u * U.x + v * V.x,
    y: origin.y + u * U.y + v * V.y,
  });
  const rect = (u0: number, u1: number, v0: number, v1: number): RectMm => {
    const a = point(u0, v0), b = point(u1, v1);
    return { x0: Math.min(a.x, b.x), x1: Math.max(a.x, b.x), y0: Math.min(a.y, b.y), y1: Math.max(a.y, b.y) };
  };
  const local = (r: RectMm) => {
    const corners = [
      { x: r.x0, y: r.y0 }, { x: r.x1, y: r.y0 }, { x: r.x0, y: r.y1 }, { x: r.x1, y: r.y1 },
    ];
    const us = corners.map((c) => (c.x - origin.x) * U.x + (c.y - origin.y) * U.y);
    const vs = corners.map((c) => (c.x - origin.x) * V.x + (c.y - origin.y) * V.y);
    return { u0: Math.min(...us), u1: Math.max(...us), v0: Math.min(...vs), v1: Math.max(...vs) };
  };
  const tilt = (mesh: Mesh, radians: number) => {
    if (V.x !== 0) mesh.rotation.z = radians * V.x;
    else mesh.rotation.x = radians * V.y;
  };
  return { rect, local, tilt, length: local(body).u1, depth: local(body).v1 };
}

/**
 * High-end living/dining concept requested on 23. 8. 2026, with the client's
 * 11. 9. 2026 variant B as a switchable alternative. The source-backed plan
 * positions live in `LIVING_LAYOUTS`; this builder only adds finish, soft
 * geometry, integrated lighting and navigation-safe collision envelopes.
 */
export function buildLivingDiningFitout(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  layout: LivingLayout = LIVING_LAYOUTS[DEFAULT_LIVING_LAYOUT_ID],
) {
  const fitout = layout.fitout;

  // ---- handleless TV wall: natural oak storage, a limestone media bay and oak
  // floating console. In variant A it starts after the flue pier and stops
  // before the rear gable lining; in variant B it stands on the solid part of
  // the gable. `wallBox` places parts by their position along the wall and
  // their distance in front of the cabinet face (negative = inside the body).
  const wall = fitout.tvWall.rectMm;
  const facing = fitout.tvWall.facing;
  const alongY = facing === "EAST" || facing === "WEST";
  const wallDepth = alongY ? wall.x1 - wall.x0 : wall.y1 - wall.y0;
  const [wallAlong0, wallAlong1] = alongY ? [wall.y0, wall.y1] : [wall.x0, wall.x1];
  const frontFace = facing === "EAST" ? wall.x1 : facing === "WEST" ? wall.x0 : facing === "NORTH" ? wall.y1 : wall.y0;
  const outSign = facing === "EAST" || facing === "NORTH" ? 1 : -1;
  const wallBox = (
    name: string,
    alongCenter: number,
    alongSize: number,
    outCenter: number,
    outSize: number,
    heightM: number,
    elevationM: number,
    tileM: number,
  ) => {
    const depthCoordinate = frontFace + outSign * outCenter;
    return texturedBox(
      context.scene,
      name,
      alongY ? { x: depthCoordinate, y: alongCenter } : { x: alongCenter, y: depthCoordinate },
      alongY ? outSize : alongSize,
      alongY ? alongSize : outSize,
      heightM,
      elevationM,
      tileM,
    );
  };
  const [bay0, bay1] = fitout.tvWall.centralBayMm;
  const bayCenter = (bay0 + bay1) / 2;
  const towerRanges = [
    [wallAlong0, bay0, fitout.tvWall.towerLabels[0]],
    [bay1, wallAlong1, fitout.tvWall.towerLabels[1]],
  ] as const;
  for (const [tower0, tower1, label] of towerRanges) {
    const tower = wallBox(
      `LIVING-103-TV-WALL · vysoká bezúchytková skriňa ${label}`,
      (tower0 + tower1) / 2,
      tower1 - tower0,
      -wallDepth / 2,
      wallDepth,
      fitout.tvWall.heightMm * MM_TO_M,
      0,
      1.2,
    );
    finish(context, tower, materials.livingCabinet, { shadow: true, pickable: true });
    for (const levelM of [0.86, 1.72]) {
      const joint = wallBox(
        `LIVING-103-TV-WALL · tieňová škára skrine ${label}`,
        (tower0 + tower1) / 2,
        tower1 - tower0 - 34,
        7,
        14,
        0.009,
        levelM,
        1,
      );
      finish(context, joint, materials.fireplace);
    }
  }
  const mediaPanel = wallBox(
    "LIVING-103-TV-WALL · veľkoformátový greige kamenný panel",
    bayCenter,
    bay1 - bay0 - 70,
    12,
    24,
    2.18,
    0.18,
    1.6,
  );
  finish(context, mediaPanel, materials.mediaPanel, { shadow: true, pickable: true });
  const bridge = wallBox(
    "LIVING-103-TV-WALL · horný úložný most",
    bayCenter,
    bay1 - bay0,
    -wallDepth / 2,
    wallDepth,
    0.27,
    2.33,
    1.2,
  );
  finish(context, bridge, materials.livingCabinet, {
    shadow: true,
    pickable: true,
    cameraOccluder: true,
  });
  const console = wallBox(
    "LIVING-103-TV-WALL · plávajúca dubová mediálna skrinka",
    bayCenter,
    bay1 - bay0 - 170,
    -wallDepth / 2 + 8,
    wallDepth - 16,
    0.28,
    0.17,
    1.2,
  );
  finish(context, console, materials.kitchenFront, { shadow: true, pickable: true });
  const consoleShadow = wallBox(
    "LIVING-103-TV-WALL · tieň pod plávajúcou skrinkou",
    bayCenter,
    bay1 - bay0 - 230,
    13,
    18,
    0.025,
    0.14,
    1,
  );
  finish(context, consoleShadow, materials.fireplace);

  const tv = fitout.tvWall.tv;
  const tvFrame = wallBox(
    `LIVING-103-TV-WALL · ${tv.diagonalIn}-palcový televízor · rám`,
    bayCenter,
    tv.widthMm + 28,
    42,
    58,
    (tv.heightMm + 28) * MM_TO_M,
    (tv.centerElevationMm - tv.heightMm / 2 - 14) * MM_TO_M,
    1,
  );
  finish(context, tvFrame, materials.fireplace, { shadow: true, pickable: true });
  const tvScreen = wallBox(
    `LIVING-103-TV-WALL · ${tv.diagonalIn}-palcový televízor · čierne sklo`,
    bayCenter,
    tv.widthMm,
    73,
    8,
    tv.heightMm * MM_TO_M,
    (tv.centerElevationMm - tv.heightMm / 2) * MM_TO_M,
    1,
  );
  // An off TV uses the existing non-emissive black glazing; office screens stay unchanged.
  finish(context, tvScreen, materials.blackGlass, { pickable: true });
  const soundbar = wallBox(
    "LIVING-103-TV-WALL · subtílny soundbar",
    bayCenter,
    1120,
    83,
    48,
    0.065,
    0.49,
    1,
  );
  finish(context, soundbar, materials.fireplace, { shadow: true });
  for (const [index, edge] of [bay0 + 24, bay1 - 24].entries()) {
    const led = wallBox(
      `LIVING-103-TV-WALL · 2700 K vertikálna LED ${index + 1}`,
      edge,
      24,
      31,
      20,
      2.08,
      0.2,
      1,
    );
    finish(context, led, materials.warmLight);
  }
  navigationGuard(context, materials, "LIVING-103-TV-WALL · hladký navigačný obrys", wall);

  // ---- tailored L sofa: broad flat cushions, narrow eased edges and an oak
  // plinth. Keep the plan footprints and navigation envelopes authoritative.
  const sofa = fitout.sofa;
  const rugRect = layout.rugRectMm;
  const rug = texturedBox(
    context.scene,
    "LIVING-103-SOFA-L · ručne tkaný greige koberec",
    rectCenter(rugRect),
    rugRect.x1 - rugRect.x0,
    rugRect.y1 - rugRect.y0,
    0.012,
    0.004,
    1,
  );
  finish(context, rug, materials.rug);
  // New source names prevent the older capsule-shaped GLB export from
  // replacing these pieces; both presentation modes use this upholstery.
  const tailored = (label: string, rect: RectMm, height: number, base: number, radius: number, material = materials.upholstery) =>
    upholsteredBox(context, `LIVING-103-SOFA-L · TAILORED · ${label}`, rect, height, base, radius, material);
  const main = sofa.mainRectMm, chaise = sofa.chaiseRectMm;
  // Cushions are laid out in the module frame: `u` along the main module from
  // the arm toward the chaise, `v` from the backrest toward the front edge.
  const frame = moduleFrame(main, sofa.facing);
  const L = frame.rect, mainLength = frame.length, mainDepth = frame.depth;
  const chaiseLocal = frame.local(chaise);
  const seatTop = sofa.seatHeightMm * MM_TO_M, seatThickness = 0.19;
  const seatBase = seatTop - seatThickness;
  for (const [rect, label] of [
    [L(0, chaiseLocal.u0, 0, mainDepth), "hlavný modul"],
    [chaise, "ležadlo"],
  ] as const) {
    const { u0, u1, v0, v1 } = frame.local(rect);
    tailored(`${label} · zapustený dubový sokel`, L(u0 + 50, u1 - 50, v0 + 65, v1 - 65), 0.1, 0.055, 0.012, materials.kitchenFront);
    tailored(`${label} · čalúnený rám`, rect, seatBase - 0.14, 0.14, 0.025);
  }
  tailored("rovné čalúnené operadlo", L(20, mainLength - 20, 20, 210), 0.56, 0.24, 0.03);
  const seatRanges = [[175, 970], [985, 1780], [1820, 2715]] as const;
  for (const [index, [u0, u1]] of seatRanges.entries()) {
    tailored(`sedák ${index+1} · piesková tkanina`, L(u0, u1, 245, mainDepth - 20), seatThickness, seatBase, 0.035);
    const back = tailored(`chrbtový vankúš ${index+1}`, L(u0, u1, 155, 370), 0.49, seatTop - 0.025, 0.045);
    frame.tilt(back, 0.085);
  }
  tailored("sedák ležadla · piesková tkanina", L(chaiseLocal.u0 + 20, 2715, mainDepth - 5, chaiseLocal.v1 - 20), seatThickness, seatBase, 0.035);
  tailored("rovná podrúčka pri kraji", L(0, 155, 0, mainDepth), 0.46, 0.18, 0.035);
  tailored("rovná podrúčka ležadla", L(mainLength - 160, mainLength, 0, chaiseLocal.v1), 0.46, 0.18, 0.035);
  const accent = tailored("ľanový vankúš · tlmená oliva", L(1350, 1750, 350, 530), 0.4, seatTop - 0.015, 0.055, materials.accentFabric);
  frame.tilt(accent, 0.15);
  navigationGuard(
    context,
    materials,
    "LIVING-103-SOFA-L · hladký navigačný obrys hlavného modulu",
    sofa.mainRectMm,
  );
  navigationGuard(
    context,
    materials,
    "LIVING-103-SOFA-L · hladký navigačný obrys ležadla",
    sofa.chaiseRectMm,
  );

  // Limestone and natural oak tables sit inside the conversation zone.
  for (const [index, spec] of layout.coffeeTables.entries()) {
    const top = CreateCylinder(
      `LIVING-103-SOFA-L · oválny konferenčný stolík ${index + 1}`,
      { height: 0.045, diameter: spec.diameterM, tessellation: 48 },
      context.scene,
    );
    top.position.set(xM(spec.centerMm.x), spec.topElevationM, zM(spec.centerMm.y));
    top.scaling.set(spec.scaleX, 1, spec.scaleZ);
    finish(context, top, spec.top === "LIMESTONE" ? materials.worktop : materials.livingCabinet, {
      shadow: true,
      pickable: true,
    });
    const pedestal = CreateCylinder(
      `LIVING-103-SOFA-L · dubová podnož konferenčného stolíka ${index + 1}`,
      { height: spec.topElevationM - 0.025, diameter: spec.pedestalDiameterM, tessellation: 32 },
      context.scene,
    );
    pedestal.position.set(xM(spec.centerMm.x), (spec.topElevationM - 0.025) / 2, zM(spec.centerMm.y));
    finish(context, pedestal, materials.kitchenFront, { shadow: true });
  }
  navigationGuard(context, materials, "LIVING-103-SOFA-L · navigačný obrys stolíkov", layout.coffeeTableGuardRectMm);

  // ---- six-seat dining zone: a classic rectangular oak table with a proper
  // apron, four tapered legs, framed chairs and a pair of calm pendants.
  const dining = fitout.dining;
  const tableHeightM = dining.tableHeightMm * MM_TO_M;
  const topThicknessM = 0.052;
  // The table's length runs along `dining.axis`; sizes below are plan X × Y.
  const [tableSizeX, tableSizeY] =
    dining.axis === "X"
      ? [dining.tableLengthMm, dining.tableDepthMm]
      : [dining.tableDepthMm, dining.tableLengthMm];
  const tableTop = texturedBox(
    context.scene,
    "LIVING-103-DINING · klasický dubový stôl · doska",
    dining.tableCenterMm,
    tableSizeX,
    tableSizeY,
    topThicknessM,
    tableHeightM - topThicknessM,
    1.2,
  );
  finish(context, tableTop, materials.kitchenFront, { shadow: true, pickable: true });

  const apronHeightM = 0.13;
  const apronElevationM = tableHeightM - topThicknessM - apronHeightM;
  // Long rails run along the table's length, short rails across it.
  const rails = [
    [-1, "pozdĺžna", true], [1, "pozdĺžna", true],
    [-1, "priečna", false], [1, "priečna", false],
  ] as const;
  for (const [side, label, longitudinal] of rails) {
    const alongX = longitudinal === (dining.axis === "X");
    const rail = texturedBox(
      context.scene,
      `LIVING-103-DINING · dubová lubová výstuha ${label} ${side < 0 ? 1 : 2}`,
      {
        x: dining.tableCenterMm.x + (alongX ? 0 : side * (tableSizeX / 2 - 62)),
        y: dining.tableCenterMm.y + (alongX ? side * (tableSizeY / 2 - 62) : 0),
      },
      alongX ? tableSizeX - 160 : 48,
      alongX ? 48 : tableSizeY - 160,
      apronHeightM,
      apronElevationM,
      1,
    );
    finish(context, rail, materials.kitchenFront, { shadow: true });
  }
  const tableLegHeightM = tableHeightM - topThicknessM - 0.012;
  for (const xSide of [-1, 1]) {
    for (const ySide of [-1, 1]) {
      const leg = CreateCylinder(
        "LIVING-103-DINING · klasická zúžená dubová noha stola",
        {
          height: tableLegHeightM,
          diameterTop: 0.058,
          diameterBottom: 0.078,
          tessellation: 4,
        },
        context.scene,
      );
      leg.position.set(
        xM(dining.tableCenterMm.x + xSide * (tableSizeX / 2 - 105)),
        tableLegHeightM / 2,
        zM(dining.tableCenterMm.y + ySide * (tableSizeY / 2 - 105)),
      );
      leg.rotation.y = Math.PI / 4;
      finish(context, leg, materials.kitchenFront, { shadow: true });
    }
  }
  navigationGuard(context, materials, "LIVING-103-DINING · hladký navigačný obrys stola", {
    x0: dining.tableCenterMm.x - tableSizeX / 2,
    x1: dining.tableCenterMm.x + tableSizeX / 2,
    y0: dining.tableCenterMm.y - tableSizeY / 2,
    y1: dining.tableCenterMm.y + tableSizeY / 2,
  });

  for (const chair of dining.chairs) {
    const forward = facingVector(chair.facing);
    const right = { x: forward.y, y: -forward.x };
    const alongX = chair.facing === "NORTH" || chair.facing === "SOUTH";
    const seat = texturedBox(
      context.scene,
      `LIVING-103-DINING · ${chair.id} · klasický čalúnený sedák`,
      chair.centerMm,
      alongX ? dining.chairSeatWidthMm : dining.chairSeatDepthMm,
      alongX ? dining.chairSeatDepthMm : dining.chairSeatWidthMm,
      0.082,
      0.425,
      0.8,
    );
    finish(context, seat, materials.upholstery, { shadow: true, pickable: true });

    for (const rightSide of [-1, 1]) {
      for (const forwardSide of [-1, 1]) {
        const leg = CreateCylinder(
          `LIVING-103-DINING · ${chair.id} · zúžená dubová noha`,
          { height: 0.43, diameterTop: 0.038, diameterBottom: 0.055, tessellation: 4 },
          context.scene,
        );
        leg.position.set(
          xM(chair.centerMm.x + right.x * rightSide * 168 + forward.x * forwardSide * 145),
          0.215,
          zM(chair.centerMm.y + right.y * rightSide * 168 + forward.y * forwardSide * 145),
        );
        leg.rotation.y = Math.PI / 4;
        finish(context, leg, materials.kitchenFront, { shadow: true });
      }
    }

    const backCenter = {
      x: chair.centerMm.x - forward.x * 205,
      y: chair.centerMm.y - forward.y * 205,
    };
    for (const side of [-1, 1]) {
      const post = texturedBox(
        context.scene,
        `LIVING-103-DINING · ${chair.id} · dubový stĺpik operadla`,
        {
          x: backCenter.x + right.x * side * 195,
          y: backCenter.y + right.y * side * 195,
        },
        42,
        42,
        0.47,
        0.43,
        1,
      );
      finish(context, post, materials.kitchenFront, { shadow: true });
    }
    const backPad = texturedBox(
      context.scene,
      `LIVING-103-DINING · ${chair.id} · čalúnená výplň operadla`,
      backCenter,
      alongX ? 350 : 44,
      alongX ? 44 : 350,
      0.245,
      0.57,
      0.8,
    );
    finish(context, backPad, materials.upholstery, { shadow: true });
    const topRail = texturedBox(
      context.scene,
      `LIVING-103-DINING · ${chair.id} · horná dubová priečka`,
      backCenter,
      alongX ? 440 : 52,
      alongX ? 52 : 440,
      0.065,
      0.855,
      1,
    );
    finish(context, topRail, materials.kitchenFront, { shadow: true });
  }

  // Two pendants a quarter of the table length either side of its centre,
  // along the table axis; one warm point light serves the whole table.
  const livingRoom = INTERIOR_ROOMS.find((room) => room.id === "ROOM-1-03")!;
  const lampElevationM = 2.08;
  const pendantOffsetMm = dining.tableLengthMm / 4;
  for (const [index, offset] of [-pendantOffsetMm, pendantOffsetMm].entries()) {
    const at = {
      x: dining.tableCenterMm.x + (dining.axis === "X" ? offset : 0),
      y: dining.tableCenterMm.y + (dining.axis === "Y" ? offset : 0),
    };
    const label = `LIVING-103-DINING · závesné svietidlo ${index + 1}`;
    const ceilingM = ceilingElevationMm(livingRoom, at.x) * MM_TO_M - 0.07;
    const cordHeightM = Math.max(0.15, ceilingM - lampElevationM - 0.08);
    const cord = CreateCylinder(
      `${label} · kábel`,
      { height: cordHeightM, diameter: 0.012, tessellation: 12 },
      context.scene,
    );
    cord.position.set(xM(at.x), lampElevationM + 0.08 + cordHeightM / 2, zM(at.y));
    finish(context, cord, materials.fireplace);
    const shade = CreateCylinder(
      `${label} · klasické tienidlo`,
      { height: 0.22, diameterTop: 0.18, diameterBottom: 0.48, tessellation: 48 },
      context.scene,
    );
    shade.position.set(xM(at.x), lampElevationM, zM(at.y));
    finish(context, shade, materials.brushedBrass, { shadow: true });
    const diffuser = CreateSphere(
      `${label} · 2700 K difúzor`,
      { diameter: 0.2, segments: 24 },
      context.scene,
    );
    diffuser.position.set(xM(at.x), lampElevationM - 0.095, zM(at.y));
    finish(context, diffuser, materials.warmLight, { shadow: true });
  }
  const light = new PointLight(
    "LIVING-103-DINING · závesné svietidlá nad stolom · svetlo",
    new Vector3(xM(dining.tableCenterMm.x), lampElevationM - 0.15, zM(dining.tableCenterMm.y)),
    context.scene,
  );
  light.diffuse = Color3.FromHexString("#ffd2a0");
  light.specular = Color3.FromHexString("#8f7254");
  light.intensity = 0.3;
  light.range = 3.8;
}

interface Interval {
  readonly start: number;
  readonly end: number;
}

function subtractIntervals(base: Interval, holes: readonly Interval[]): Interval[] {
  let pieces: Interval[] = [base];
  for (const hole of holes) {
    const next: Interval[] = [];
    for (const piece of pieces) {
      if (hole.end <= piece.start || hole.start >= piece.end) {
        next.push(piece);
        continue;
      }
      if (hole.start > piece.start) next.push({ start: piece.start, end: hole.start });
      if (hole.end < piece.end) next.push({ start: hole.end, end: piece.end });
    }
    pieces = next;
  }
  return pieces.filter((piece) => piece.end - piece.start > 40);
}

/**
 * Openings in the exterior shell that a wall band must not cross, keyed by
 * the inner face of the facade they sit in (plan mm).
 */
function exteriorOpeningsOn(axis: "X" | "Y", faceMm: number): Interval[] {
  const near = (value: number, target: number) => Math.abs(value - target) <= 45;
  const holes: Interval[] = [];
  const front = HOUSE.facades.front;
  const garden = HOUSE.facades.garden;
  const east = HOUSE.facades.east;
  const west = HOUSE.facades.west;
  const wingWest = HOUSE.facades.wingWest;
  const porch = HOUSE.porches.wingEnd;
  const loggia = HOUSE.porches.gardenLoggia;
  if (axis === "X" && near(faceMm, front.faceYmm + 530)) {
    holes.push({ start: front.garageDoor.startXmm, end: front.garageDoor.startXmm + front.garageDoor.widthMm });
    for (const opening of front.openings) holes.push({ start: opening.startXmm, end: opening.startXmm + opening.widthMm });
  }
  if (axis === "X" && near(faceMm, garden.faceYmm - 530)) {
    for (const opening of garden.openings) holes.push({ start: opening.startXmm, end: opening.startXmm + opening.widthMm });
    holes.push({ start: loggia.openingStartXmm, end: loggia.openingEndXmm });
  }
  if (axis === "X" && near(faceMm, loggia.backFaceYmm)) {
    holes.push({ start: loggia.backDoor.startXmm, end: loggia.backDoor.startXmm + loggia.backDoor.widthMm });
  }
  if (axis === "X" && near(faceMm, porch.glazingFaceYmm)) {
    holes.push({ start: porch.glazing.startXmm, end: porch.glazing.startXmm + porch.glazing.widthMm });
  }
  if (axis === "Y" && near(faceMm, east.faceXmm - 530)) {
    for (const opening of east.openings) holes.push({ start: opening.startYmm, end: opening.startYmm + opening.widthMm });
  }
  if (axis === "Y" && near(faceMm, west.faceXmm + 530)) {
    holes.push({ start: west.garageWindow.startYmm, end: west.garageWindow.startYmm + west.garageWindow.widthMm });
    holes.push({ start: west.loggiaOpening.startYmm, end: west.loggiaOpening.startYmm + west.loggiaOpening.widthMm });
  }
  if (axis === "Y" && near(faceMm, wingWest.faceXmm + 500)) {
    holes.push({ start: wingWest.opening.startYmm, end: wingWest.opening.startYmm + wingWest.opening.widthMm });
  }
  return holes;
}

interface WallBandSpec {
  readonly label: string;
  readonly heightM: number;
  readonly thicknessMm: number;
  readonly material: PBRMaterial;
  readonly tileM: number;
  readonly rooms: (room: InteriorRoom) => boolean;
}

/**
 * Thin bands along every exposed room edge: edges shared with another
 * rectangle of the same room, door openings and exterior window or door
 * openings are left out. Used for skirting boards and wet-room wall tiles.
 */
function buildWallBands(context: InteriorBuildContext, spec: WallBandSpec) {
  for (const room of INTERIOR_ROOMS) {
    if (!spec.rooms(room)) continue;
    for (const rect of room.rectsMm) {
      const others = room.rectsMm.filter((other) => other !== rect);
      const edges = [
        { label: "juh", axis: "X" as const, at: rect.y0, base: { start: rect.x0, end: rect.x1 }, inward: 1 },
        { label: "sever", axis: "X" as const, at: rect.y1, base: { start: rect.x0, end: rect.x1 }, inward: -1 },
        { label: "západ", axis: "Y" as const, at: rect.x0, base: { start: rect.y0, end: rect.y1 }, inward: 1 },
        { label: "východ", axis: "Y" as const, at: rect.x1, base: { start: rect.y0, end: rect.y1 }, inward: -1 },
      ];
      for (const edge of edges) {
        const holes: Interval[] = exteriorOpeningsOn(edge.axis, edge.at);
        for (const other of others) {
          const touches =
            edge.axis === "X"
              ? other.y0 <= edge.at && other.y1 >= edge.at
              : other.x0 <= edge.at && other.x1 >= edge.at;
          if (!touches) continue;
          holes.push(
            edge.axis === "X"
              ? { start: other.x0, end: other.x1 }
              : { start: other.y0, end: other.y1 },
          );
        }
        for (const door of INTERIOR_DOORS) {
          const [wallFrom, wallTo] = door.wallSpanMm;
          const sameAxis = door.axis === edge.axis;
          const onEdge = sameAxis && (Math.abs(wallFrom - edge.at) < 2 || Math.abs(wallTo - edge.at) < 2);
          if (onEdge) holes.push({ start: door.startMm, end: door.startMm + door.widthMm });
        }
        // Open corridor mouths (no door) toward other rooms.
        for (const other of INTERIOR_ROOMS) {
          if (other === room) continue;
          for (const otherRect of other.rectsMm) {
            const shares =
              edge.axis === "X"
                ? Math.abs(otherRect.y0 - edge.at) < 2 || Math.abs(otherRect.y1 - edge.at) < 2
                : Math.abs(otherRect.x0 - edge.at) < 2 || Math.abs(otherRect.x1 - edge.at) < 2;
            if (!shares) continue;
            holes.push(
              edge.axis === "X"
                ? { start: otherRect.x0, end: otherRect.x1 }
                : { start: otherRect.y0, end: otherRect.y1 },
            );
          }
        }
        const inset = spec.thicknessMm / 2;
        for (const [index, piece] of subtractIntervals(edge.base, holes).entries()) {
          const center =
            edge.axis === "X"
              ? { x: (piece.start + piece.end) / 2, y: edge.at + edge.inward * inset }
              : { x: edge.at + edge.inward * inset, y: (piece.start + piece.end) / 2 };
          const band = texturedBox(
            context.scene,
            `${room.number} · ${spec.label} ${edge.label} ${index + 1}`,
            center,
            edge.axis === "X" ? piece.end - piece.start : spec.thicknessMm,
            edge.axis === "X" ? spec.thicknessMm : piece.end - piece.start,
            spec.heightM,
            FLOOR_TOP_M,
            spec.tileM,
          );
          finish(context, band, spec.material);
        }
      }
    }
  }
}

export function buildInterior(context: InteriorBuildContext) {
  const materials = createInteriorMaterials(context);
  const livingLayout = LIVING_LAYOUTS[context.livingLayout ?? DEFAULT_LIVING_LAYOUT_ID];
  buildFloorsAndCeilings(context, materials);
  buildWalls(context, materials);
  buildLivingFireplace(context, materials, livingLayout.stove);
  for (const door of INTERIOR_DOORS) buildDoor(context, materials, door);
  buildKitchen(context, materials);
  buildTechnicalHeatingFitout(context, materials);
  buildWcFitout(context, materials);
  buildBathroomFitout(context, materials);
  buildEnsuiteBathroomFitout(context, materials);
  buildGarageFitout(context, materials);
  buildHallwayBuiltInWardrobes(context, materials);
  buildEntryFitout(context, materials);
  buildBedroomFitout(context, materials);
  buildChildrensBedroomFitouts(context, materials);
  buildOfficeFitout(context, materials);
  buildLivingDiningFitout(context, materials, livingLayout);
  buildWallBands(context, {
    label: "soklová lišta",
    heightM: 0.06,
    thicknessMm: 12,
    material: materials.skirting,
    tileM: 1,
    rooms: (room) => !room.wetRoom && room.floor !== "EPOXY",
  });
  buildWallBands(context, {
    label: "keramický obklad v. 2 100",
    heightM: 2.1,
    thicknessMm: 10,
    material: materials.wallTile,
    tileM: 1.2,
    rooms: (room) => room.wetRoom,
  });
  return materials;
}
