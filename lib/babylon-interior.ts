import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { Texture } from "@babylonjs/core/Materials/Textures/texture";
import { Color3 } from "@babylonjs/core/Maths/math.color";
import { Quaternion, Vector3, Vector4 } from "@babylonjs/core/Maths/math.vector";
import { PointLight } from "@babylonjs/core/Lights/pointLight";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { CreateBox } from "@babylonjs/core/Meshes/Builders/boxBuilder.pure";
import { CreateCapsule } from "@babylonjs/core/Meshes/Builders/capsuleBuilder.pure";
import { CreateCylinder } from "@babylonjs/core/Meshes/Builders/cylinderBuilder.pure";
import { ExtrudePolygon } from "@babylonjs/core/Meshes/Builders/polygonBuilder.pure";
import { CreateSphere } from "@babylonjs/core/Meshes/Builders/sphereBuilder.pure";
import { CreateTorus } from "@babylonjs/core/Meshes/Builders/torusBuilder.pure";
import { CreateTube } from "@babylonjs/core/Meshes/Builders/tubeBuilder.pure";
import { Mesh } from "@babylonjs/core/Meshes/mesh";
import type { Scene } from "@babylonjs/core/scene";
import earcut from "earcut";

import {
  BATHROOM_FITOUT,
  BEDROOM_FITOUT,
  CHILDRENS_BEDROOM_FITOUTS,
  ENSUITE_BATHROOM_FITOUT,
  ENTRY_FITOUT,
  FIREPLACE_STOVE,
  HALLWAY_BUILT_IN_WARDROBES,
  INTERIOR_DOORS,
  INTERIOR_ROOMS,
  INTERIOR_WALLS,
  INTERIOR_WALL_HEIGHT_MM,
  KITCHEN_RUN,
  LIVING_DINING_FITOUT,
  OFFICE_FITOUT,
  TECHNICAL_HEATING_FITOUT,
  WC_FITOUT,
  WING_RIDGE_XMM,
  ceilingElevationMm,
  roomBoundsMm,
  type ChildBedroomFitout,
  type FurnitureFacing,
  type HallwayBuiltInWardrobe,
  type InteriorDoor,
  type InteriorRoom,
  type RectMm,
} from "./twin-interior";
import { HOUSE, type LayerId, type Point2Mm } from "./twin-site";
import { MM_TO_M, sceneXM as xM, sceneZM as zM } from "./twin-render-frame";

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
  const childSage = pbr(scene, "real-child-room-sage", "#788878", 0.72);
  childSage.sheen.isEnabled = true;
  childSage.sheen.intensity = 0.12;
  childSage.sheen.color = Color3.FromHexString("#c8d0c5");
  const childClay = pbr(scene, "real-child-room-clay", "#bd7861", 0.8);
  childClay.sheen.isEnabled = true;
  childClay.sheen.intensity = 0.16;
  childClay.sheen.color = Color3.FromHexString("#e8b8a3");
  const childMidnight = pbr(scene, "real-child-room-midnight", "#34495b", 0.58);
  childMidnight.clearCoat.isEnabled = true;
  childMidnight.clearCoat.intensity = 0.12;
  childMidnight.clearCoat.roughness = 0.42;
  const childSand = pbr(scene, "real-child-room-sand", "#d7c8b3", 0.86);
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
  } = {},
) {
  mesh.material = material;
  mesh.receiveShadows = true;
  mesh.isPickable = options.pickable ?? false;
  mesh.checkCollisions = options.collide ?? false;
  if (options.cameraOccluder) {
    mesh.metadata = { ...(mesh.metadata ?? {}), cameraOccluder: true };
  }
  context.realisticOnly(mesh);
  if (options.shadow) context.castShadow(mesh);
  context.register(mesh, "building", HOUSE_ENTITY);
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
    finish(context, slab, materials.epoxy);
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
    finish(context, threshold, fromRoom ? floorMaterial(materials, fromRoom) : materials.vinyl);
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
      finish(context, floor, floorMaterial(materials, room), { pickable: true });

      const vaulted = room.ceiling === "VAULTED_TO_RIDGE" && index === 0;
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

/** Sloped SDK ceiling of 1.03 following the wing roof up to the ridge. */
function buildVault(context: InteriorBuildContext, materials: InteriorMaterials, room: InteriorRoom) {
  const rect = room.rectsMm[0];
  const bounds = roomBoundsMm(room);
  const halfSpanMm = WING_RIDGE_XMM - bounds.x0;
  const wallClearMm = room.clearHeightMm;
  const ridgeM = VAULT_RIDGE_MM * MM_TO_M;
  const wallM = wallClearMm * MM_TO_M;
  const thicknessM = 0.04;
  const depthMm = rect.y1 - rect.y0;
  const centerY = (rect.y0 + rect.y1) / 2;
  for (const side of [-1, 1] as const) {
    const startX = side < 0 ? bounds.x0 : WING_RIDGE_XMM;
    const endX = side < 0 ? WING_RIDGE_XMM : bounds.x1;
    const runM = (endX - startX) * MM_TO_M;
    const riseM = ridgeM - wallM;
    const lengthM = Math.hypot(runM, riseM);
    const slab = texturedBox(
      context.scene,
      `${room.number} · šikmý SDK podhľad ${side < 0 ? "západ" : "východ"} · +2,750 → +4,850`,
      { x: (startX + endX) / 2, y: centerY },
      Math.round(lengthM * 1000),
      depthMm,
      thicknessM,
      (wallM + ridgeM) / 2,
      2,
    );
    slab.rotation.z = side < 0 ? Math.atan2(riseM, runM) : -Math.atan2(riseM, runM);
    finish(context, slab, materials.ceiling, { cameraOccluder: true });
  }
  // Triangular closures of the vault above the south and north walls.
  const apex = { alongMm: WING_RIDGE_XMM, elevationMm: VAULT_RIDGE_MM };
  // Only the south end is closed; the north end toward the porch is the
  // glazed gable (HOUSE.porches.wingEnd.glazing.gable).
  for (const [label, y0, y1] of [["južný", rect.y0 - 139, rect.y0]] as const) {
    const closure = profileSolidY(
      context.scene,
      `${room.number} · ${label} štít podhľadu`,
      [
        { alongMm: bounds.x0, elevationMm: wallClearMm },
        { alongMm: bounds.x1, elevationMm: wallClearMm },
        { alongMm: bounds.x1, elevationMm: vaultElevationMm(bounds.x1, wallClearMm, halfSpanMm) },
        apex,
        { alongMm: bounds.x0, elevationMm: vaultElevationMm(bounds.x0, wallClearMm, halfSpanMm) },
      ].filter(
        (point, index, points) =>
          index === 0 ||
          Math.abs(point.elevationMm - points[index - 1].elevationMm) > 1 ||
          Math.abs(point.alongMm - points[index - 1].alongMm) > 1,
      ),
      y0,
      y1,
    );
    finish(context, closure, materials.plaster, { collide: true });
  }
}

function buildWalls(context: InteriorBuildContext, materials: InteriorMaterials) {
  const heightM = INTERIOR_WALL_HEIGHT_MM * MM_TO_M;
  for (const wall of INTERIOR_WALLS) {
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
function buildLivingFireplace(context: InteriorBuildContext, materials: InteriorMaterials) {
  const stove = FIREPLACE_STOVE;
  const center = stove.centerMm;
  const diameterM = stove.bodyDiameterMm * MM_TO_M;
  const radiusMm = stove.bodyDiameterMm / 2;
  const bodyHeightM = stove.bodyHeightMm * MM_TO_M;
  const shellBottomM = 0.03;
  const shellHeightM = bodyHeightM - shellBottomM;

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
  const arcRotationY = -Math.PI * arc;
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
    jamb.position.set(
      xM(center.x + radiusMm * Math.cos(halfArcRad)),
      windowCenterM,
      zM(center.y + side * radiusMm * Math.sin(halfArcRad)),
    );
    finish(context, jamb, materials.fireplace, { shadow: true });
  }

  const fireFrontXmm = center.x + radiusMm + 5;
  for (const [index, offsetYmm] of [-62, 54].entries()) {
    const log = CreateCylinder(
      `${stove.id} · LOG-${index + 1} · horiace poleno`,
      { height: 0.245, diameter: 0.052, tessellation: 20 },
      context.scene,
    );
    log.position.set(xM(fireFrontXmm), 0.5 + index * 0.035, zM(center.y + offsetYmm));
    log.rotation.x = Math.PI / 2;
    log.rotation.y = index === 0 ? -0.18 : 0.22;
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
    flameMesh.position.set(
      xM(fireFrontXmm + 3),
      flame.elevationM + flame.heightM / 2,
      zM(center.y + flame.yMm),
    );
    finish(context, flameMesh, materials.fireplaceEmber, { shadow: true });
  }

  const handleCenter = { x: center.x + 178, y: center.y + 279 };
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
      { x: handleCenter.x, y: center.y + 252 },
      24,
      58,
      0.018,
      elevationM - 0.009,
      1,
    );
    finish(context, handleMount, materials.fireplace, { shadow: true });
  }

  const airControl = CreateSphere(
    `${stove.id} · AIR-CONTROL · regulácia vzduchu`,
    { diameter: 0.027, segments: 20 },
    context.scene,
  );
  airControl.position.set(xM(center.x + radiusMm + 17), 0.322, zM(center.y));
  finish(context, airControl, context.chimneyMetal, { shadow: true, pickable: true });

  const collar = CreateCylinder(
    `${stove.id} · FLUE-COLLAR · priame horné napojenie Ø${stove.flue.outerDiameterMm}`,
    { height: 0.05, diameter: stove.flue.outerDiameterMm * MM_TO_M + 0.035, tessellation: 40 },
    context.scene,
  );
  collar.position.set(xM(center.x), bodyHeightM + 0.015, zM(center.y));
  finish(context, collar, materials.fireplace, { shadow: true });

  const fireLight = new PointLight(
    `${stove.id} · FIRE-LIGHT · teplé svetlo ohniska`,
    new Vector3(xM(center.x + radiusMm + 320), windowCenterM, zM(center.y)),
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
  const heightM = door.heightMm * MM_TO_M;
  const along = (value: number) => value;
  const plan = (alongMm: number, acrossMm: number): Point2Mm =>
    door.axis === "X" ? { x: alongMm, y: acrossMm } : { x: acrossMm, y: alongMm };
  const wallCenter = (wallFrom + wallTo) / 2;
  // Jambs and head (frame lining through the full wall thickness).
  for (const [side, alongMm] of [
    ["ľavá", door.startMm + frameMm / 2],
    ["pravá", door.startMm + door.widthMm - frameMm / 2],
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

  // Leaf standing open at 90°, hinged on the `hinge` end and swung into the
  // `swing` side, so every room stays walkable.
  const leafThicknessMm = 40;
  const hingeAlongMm =
    door.hinge < 0 ? door.startMm + frameMm : door.startMm + door.widthMm - frameMm;
  const hingeAcrossMm = door.swing < 0 ? wallFrom : wallTo;
  const leafCenterAcross = hingeAcrossMm + door.swing * (door.leafWidthMm / 2 + 10);
  const leafCenterAlong = hingeAlongMm + (door.hinge < 0 ? 1 : -1) * (leafThicknessMm / 2 + 8);
  const leaf = texturedBox(
    context.scene,
    `${door.label} · otvorené krídlo`,
    plan(leafCenterAlong, leafCenterAcross),
    door.axis === "X" ? leafThicknessMm : door.leafWidthMm + 20,
    door.axis === "X" ? door.leafWidthMm + 20 : leafThicknessMm,
    heightM - 0.07,
    0.02,
    1,
  );
  finish(context, leaf, materials.doorLeaf, { shadow: true, pickable: true });
  const handle = CreateCylinder(
    `${door.label} · kľučka`,
    { height: 0.12, diameter: 0.018, tessellation: 12 },
    context.scene,
  );
  const handleAcross = hingeAcrossMm + door.swing * (door.leafWidthMm - 60);
  const handleAlong = leafCenterAlong + (door.hinge < 0 ? 1 : -1) * 0.04 * 1000;
  const handlePlan = plan(handleAlong, handleAcross);
  handle.position.set(xM(handlePlan.x), 1.05, zM(handlePlan.y));
  // Lever parallel to the open leaf: along plan y for X-axis walls.
  handle.rotation.x = door.axis === "X" ? Math.PI / 2 : 0;
  handle.rotation.z = door.axis === "X" ? 0 : Math.PI / 2;
  finish(context, handle, context.chimneyMetal);
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
  finish(context, upper, materials.kitchenUpper, { shadow: true });
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
    { x: (pen.x0 + pen.x1) / 2, y: (pen.y0 + pen.y1) / 2 + 150 },
    pen.x1 - pen.x0 + 20,
    pen.y1 - pen.y0 + 320,
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
  const returnUpstand = texturedBox(
    context.scene,
    `${k.id} · L-RETURN-EAST · kremenný obklad pri stene`,
    { x: eastReturn.x1 - 6, y: (eastReturn.y0 + eastReturn.y1) / 2 },
    12,
    eastReturn.y1 - eastReturn.y0 - 20,
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
    { x: (pen.x0 + pen.x1) / 2, y: (pen.y0 + pen.y1) / 2 + 150 },
    pen.x1 - pen.x0 + 20,
    pen.y1 - pen.y0 + 320,
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
function buildTechnicalHeatingFitout(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
) {
  const fitout = TECHNICAL_HEATING_FITOUT;
  const boiler = fitout.boiler;
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
    { label: "horné prikladacie dvierka na kusové drevo", bottomM: 0.69, heightM: 0.37 },
    { label: "stredné spaľovacie dvierka", bottomM: 0.36, heightM: 0.28 },
    { label: "spodné popolníkové dvierka", bottomM: 0.12, heightM: 0.19 },
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
    bodyRect.x1 - bodyRect.x0 + 28,
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
    hopperRect.y1 - hopperRect.y0 - 92,
    0.7,
    0.69,
    1,
  );
  finish(context, hopperBody, materials.boilerEnamel, { shadow: true, pickable: true });
  const hopperLid = texturedBox(
    context.scene,
    `${fitout.id} · PELLET-HOPPER · výklopné plniace veko`,
    { x: hopperCenter.x, y: hopperCenter.y - 12 },
    hopperRect.x1 - hopperRect.x0 - 34,
    hopperRect.y1 - hopperRect.y0 - 126,
    0.045,
    hopper.heightMm * MM_TO_M - 0.045,
    1,
  );
  hopperLid.rotation.x = -0.055;
  finish(context, hopperLid, materials.boilerEnamel, { shadow: true, pickable: true });
  const hopperGrip = texturedBox(
    context.scene,
    `${fitout.id} · PELLET-HOPPER · madlo plniaceho veka`,
    { x: hopperCenter.x, y: hopperRect.y1 - 76 },
    190,
    24,
    0.025,
    hopper.heightMm * MM_TO_M + 0.004,
    1,
  );
  finish(context, hopperGrip, materials.fireplace, { shadow: true });

  const augerPath = [
    new Vector3(xM(hopperCenter.x + 22), 0.34, zM(hopperCenter.y + 10)),
    new Vector3(xM(hopperRect.x1 + 118), 1.09, zM(bodyRect.y0 + 250)),
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
    { x: hopperRect.x1 + 116, y: bodyRect.y0 + 250 },
    155,
    155,
    0.19,
    0.98,
    1,
  );
  finish(context, augerMotor, materials.fireplace, { shadow: true, pickable: true });

  const burnerRect = boiler.burner.footprintMm;
  const burnerCenter = rectCenter(burnerRect);
  const burnerBody = texturedBox(
    context.scene,
    `${fitout.id} · PELLET-BURNER · automaticky čistený peletový horák`,
    burnerCenter,
    burnerRect.x1 - burnerRect.x0,
    burnerRect.y1 - burnerRect.y0,
    0.34,
    0.34,
    1,
  );
  finish(context, burnerBody, materials.fireplace, { shadow: true, pickable: true });
  const burnerFace = texturedBox(
    context.scene,
    `${fitout.id} · PELLET-BURNER · čelný servisný kryt`,
    { x: burnerCenter.x, y: burnerRect.y1 + 10 },
    burnerRect.x1 - burnerRect.x0 - 44,
    20,
    0.25,
    0.385,
    1,
  );
  finish(context, burnerFace, materials.boilerEnamel, { shadow: true, pickable: true });
  const burnerWindow = texturedBox(
    context.scene,
    `${fitout.id} · PELLET-BURNER · kontrolné okienko plameňa`,
    { x: burnerCenter.x - 82, y: burnerRect.y1 + 23 },
    80,
    8,
    0.055,
    0.47,
    1,
  );
  finish(context, burnerWindow, materials.blackGlass);

  const hoseStart = { x: bodyRect.x0 + 18, elevationM: 1.08, y: frontYmm + 32 };
  const hoseControl = { x: bodyRect.x1 + 86, elevationM: 1.03, y: frontYmm + 74 };
  const hoseEnd = { x: burnerCenter.x, elevationM: 0.68, y: burnerRect.y0 + 195 };
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
  finish(context, feedHose, materials.pelletFeedHose, { shadow: true, pickable: true });

  const flueCollar = CreateCylinder(
    `${fitout.id} · WOOD-PELLET-BOILER · dymovodné hrdlo`,
    { height: 0.06, diameter: 0.23, tessellation: 32 },
    context.scene,
  );
  flueCollar.position.set(xM(bodyCenter.x), bodyHeightM + 0.03, zM(bodyRect.y0 + 145));
  finish(context, flueCollar, materials.fireplace);
  const flueStub = CreateCylinder(
    `${fitout.id} · WOOD-PELLET-BOILER · koncept napojenia dymovodu Ø${boiler.flueOutletDiameterMm}`,
    { height: 0.14, diameter: boiler.flueOutletDiameterMm * MM_TO_M, tessellation: 32 },
    context.scene,
  );
  flueStub.position.set(xM(bodyCenter.x), bodyHeightM + 0.1, zM(bodyRect.y0 + 145));
  finish(context, flueStub, materials.fireplace);

  navigationGuard(
    context,
    materials,
    `${fitout.id} · WOOD-PELLET-ASSEMBLY · navigačný obrys celej zostavy`,
    assemblyRect,
  );

  const tank = fitout.accumulator;
  const tankRadiusMm = tank.outerDiameterMm / 2;
  const tankHeightM = tank.heightMm * MM_TO_M;
  const tankBase = CreateCylinder(
    `${fitout.id} · BUFFER-TANK-1000L · podstavec`,
    { height: 0.08, diameter: tank.outerDiameterMm * MM_TO_M - 0.08, tessellation: 48 },
    context.scene,
  );
  tankBase.position.set(xM(tank.centerMm.x), 0.04, zM(tank.centerMm.y));
  finish(context, tankBase, materials.fireplace, { shadow: true });
  const tankBody = CreateCylinder(
    `${fitout.id} · BUFFER-TANK-1000L · akumulačná nádrž ${tank.nominalVolumeL} l`,
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
    `${fitout.id} · BUFFER-TANK-1000L · horné izolované veko`,
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
      `${fitout.id} · BUFFER-TANK-1000L · oceľová obruč`,
      { height: 0.028, diameter: tank.outerDiameterMm * MM_TO_M + 0.018, tessellation: 48 },
      context.scene,
    );
    band.position.set(xM(tank.centerMm.x), elevationM, zM(tank.centerMm.y));
    finish(context, band, materials.steel);
  }
  for (const [index, elevationM, yOffsetMm] of [
    [1, 0.34, -245],
    [2, 0.78, 245],
    [3, 1.22, -245],
    [4, 1.66, 245],
  ] as const) {
    const nozzle = CreateCylinder(
      `${fitout.id} · BUFFER-TANK-1000L · hydraulické hrdlo ${index}`,
      { height: 0.18, diameter: 0.055, tessellation: 20 },
      context.scene,
    );
    nozzle.rotation.z = Math.PI / 2;
    nozzle.position.set(
      xM(tank.centerMm.x + tankRadiusMm + 90),
      elevationM,
      zM(tank.centerMm.y + yOffsetMm),
    );
    finish(context, nozzle, materials.copperPipe);
  }
  const airVent = CreateCylinder(
    `${fitout.id} · BUFFER-TANK-1000L · automatický odvzdušňovač`,
    { height: 0.12, diameter: 0.045, tessellation: 20 },
    context.scene,
  );
  airVent.position.set(xM(tank.centerMm.x), tankHeightM + 0.06, zM(tank.centerMm.y));
  finish(context, airVent, materials.brushedBrass);
  const gaugeRim = CreateCylinder(
    `${fitout.id} · BUFFER-TANK-1000L · teplomer`,
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
    `${fitout.id} · BUFFER-TANK-1000L · ciferník teplomera`,
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
}

/** Modern compact fitout for the enlarged room 1.06. */
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
    { x: toilet.concealedCisternRectMm.x0 - 5, y: toiletCenter.y },
    10,
    185,
    0.11,
    0.84,
    1,
  );
  finish(context, flushPlate, materials.steel, { pickable: true });
  for (const yOffsetMm of [-42, 42]) {
    const button = CreateCylinder(
      `${fitout.id} · WALL-HUNG-WC · tlačidlo splachovania`,
      { height: 0.012, diameter: yOffsetMm < 0 ? 0.052 : 0.038, tessellation: 24 },
      context.scene,
    );
    button.rotation.z = Math.PI / 2;
    button.position.set(
      xM(toilet.concealedCisternRectMm.x0 - 12),
      0.895,
      zM(toiletCenter.y + yOffsetMm),
    );
    finish(context, button, materials.blackGlass);
  }

  softEllipsoid(
    context,
    `${fitout.id} · WALL-HUNG-WC · keramická misa`,
    { x: toiletCenter.x - 10, y: toiletCenter.y },
    [0.52, 0.28, 0.37],
    0.32,
    materials.sanitaryCeramic,
  );
  softEllipsoid(
    context,
    `${fitout.id} · WALL-HUNG-WC · vnútro misy`,
    { x: toiletCenter.x - 55, y: toiletCenter.y },
    [0.31, 0.024, 0.2],
    0.455,
    materials.mirrorGlass,
  );
  const toiletSeat = CreateTorus(
    `${fitout.id} · WALL-HUNG-WC · tenké sedadlo`,
    { diameter: 0.355, thickness: 0.035, tessellation: 40 },
    context.scene,
  );
  toiletSeat.position.set(xM(toiletCenter.x - 35), toilet.seatElevationMm * MM_TO_M, zM(toiletCenter.y));
  toiletSeat.scaling.set(1.42, 0.68, 0.98);
  finish(context, toiletSeat, materials.sanitaryCeramic, { shadow: true, pickable: true });

  const basin = fitout.basin;
  const basinCenter: Point2Mm = {
    x: (basin.footprintMm.x0 + basin.footprintMm.x1) / 2,
    y: (basin.footprintMm.y0 + basin.footprintMm.y1) / 2,
  };
  softEllipsoid(
    context,
    `${fitout.id} · COMPACT-BASIN · keramické umývadlo 450`,
    basinCenter,
    [0.45, 0.16, 0.32],
    0.77,
    materials.sanitaryCeramic,
  );
  softEllipsoid(
    context,
    `${fitout.id} · COMPACT-BASIN · vnútorná misa`,
    { x: basinCenter.x, y: basinCenter.y - 18 },
    [0.31, 0.025, 0.19],
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
    zM(basinCenter.y - 15),
  );
  basinRim.scaling.set(1.45, 0.65, 0.88);
  finish(context, basinRim, materials.sanitaryCeramic, { shadow: true });
  const drain = CreateCylinder(
    `${fitout.id} · COMPACT-BASIN · chrómový odtok`,
    { height: 0.008, diameter: 0.052, tessellation: 24 },
    context.scene,
  );
  drain.position.set(
    xM(basinCenter.x),
    basin.rimElevationMm * MM_TO_M + 0.024,
    zM(basinCenter.y - 38),
  );
  finish(context, drain, materials.steel);
  const tapRiser = CreateCylinder(
    `${fitout.id} · COMPACT-BASIN · stojanková batéria`,
    { height: 0.18, diameter: 0.027, tessellation: 20 },
    context.scene,
  );
  tapRiser.position.set(xM(basinCenter.x), 0.95, zM(basin.footprintMm.y1 - 68));
  finish(context, tapRiser, materials.steel);
  const tapSpout = CreateCylinder(
    `${fitout.id} · COMPACT-BASIN · výtok batérie`,
    { height: 0.14, diameter: 0.021, tessellation: 20 },
    context.scene,
  );
  tapSpout.rotation.x = Math.PI / 2;
  tapSpout.position.set(xM(basinCenter.x), 1.03, zM(basin.footprintMm.y1 - 130));
  finish(context, tapSpout, materials.steel);
  const trap = CreateCylinder(
    `${fitout.id} · COMPACT-BASIN · pohľadový sifón`,
    { height: 0.28, diameter: 0.045, tessellation: 20 },
    context.scene,
  );
  trap.position.set(xM(basinCenter.x), 0.56, zM(basinCenter.y + 12));
  finish(context, trap, materials.steel);
  const mirrorFrame = texturedBox(
    context.scene,
    `${fitout.id} · COMPACT-BASIN · zrkadlo s tenkým rámom`,
    { x: basinCenter.x, y: basin.footprintMm.y1 - 6 },
    470,
    14,
    0.68,
    1.08,
    1,
  );
  finish(context, mirrorFrame, materials.fireplace, { shadow: true });
  const mirror = texturedBox(
    context.scene,
    `${fitout.id} · COMPACT-BASIN · zrkadlová plocha`,
    { x: basinCenter.x, y: basin.footprintMm.y1 - 14 },
    440,
    7,
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

  // One continuous 2 616 mm cabinet composition: the vanity, appliance bays,
  // mirror and overhead storage share the same datum and flush top line.
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
    [1.0, 0.16, 0.39],
    basin.rimElevationMm * MM_TO_M + 0.035,
    materials.blackCeramic,
  );
  softEllipsoid(
    context,
    `${fitout.id} · BUILT-IN-2616 · vnútorná čierna misa`,
    { x: basinCenter.x, y: basinCenter.y - 8 },
    [0.82, 0.028, 0.27],
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

  const mirrorGlow = texturedBox(
    context.scene,
    `${fitout.id} · BUILT-IN-2616 · nepriame LED za zrkadlom`,
    { x: basinCenter.x, y: run.y1 - 8 },
    1060,
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
    1020,
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
  finish(context, basinTopCabinet, materials.kitchenFront, { shadow: true, pickable: true });
  const applianceUpperX0 = vanityX1;
  const applianceUpper = texturedBox(
    context.scene,
    `${fitout.id} · BUILT-IN-2616 · horné skrinky nad spotrebičmi`,
    { x: (applianceUpperX0 + run.x1) / 2, y: (run.y0 + run.y1) / 2 },
    run.x1 - applianceUpperX0,
    run.y1 - run.y0,
    (builtIn.heightMm - builtIn.overheadCabinetBottomMm) * MM_TO_M,
    builtIn.overheadCabinetBottomMm * MM_TO_M,
    1,
  );
  finish(context, applianceUpper, materials.kitchenFront, { shadow: true, pickable: true });
  for (const xMm of [vanityX1, builtIn.appliances[1].footprintMm.x0 - 50]) {
    const cabinetJoint = texturedBox(
      context.scene,
      `${fitout.id} · BUILT-IN-2616 · zvislá škára horných skriniek`,
      { x: xMm, y: run.y0 - 4 },
      5,
      14,
      (builtIn.heightMm - builtIn.overheadCabinetBottomMm) * MM_TO_M - 0.04,
      builtIn.overheadCabinetBottomMm * MM_TO_M + 0.02,
      1,
    );
    finish(context, cabinetJoint, materials.fireplace);
  }
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

  for (const [index, appliance] of builtIn.appliances.entries()) {
    const applianceCenter = rectCenter(appliance.footprintMm);
    const label = appliance.kind === "WASHER" ? "biela práčka" : "biela sušička";
    const body = texturedBox(
      context.scene,
      `${fitout.id} · BUILT-IN-2616 · ${label}`,
      { x: applianceCenter.x, y: run.y0 - 4 },
      570,
      26,
      0.86,
      0.08,
      1,
    );
    finish(context, body, materials.applianceEnamel, { shadow: true, pickable: true });
    const doorRim = CreateCylinder(
      `${fitout.id} · BUILT-IN-2616 · biely rám bubna ${index + 1}`,
      { height: 0.038, diameter: 0.47, tessellation: 40 },
      context.scene,
    );
    doorRim.rotation.x = Math.PI / 2;
    doorRim.position.set(xM(applianceCenter.x), 0.48, zM(run.y0 - 28));
    finish(context, doorRim, materials.applianceEnamel, { shadow: true });
    const doorGlass = CreateCylinder(
      `${fitout.id} · BUILT-IN-2616 · sklo bubna ${index + 1}`,
      { height: 0.046, diameter: 0.38, tessellation: 40 },
      context.scene,
    );
    doorGlass.rotation.x = Math.PI / 2;
    doorGlass.position.set(xM(applianceCenter.x), 0.48, zM(run.y0 - 45));
    finish(context, doorGlass, materials.blackGlass, { pickable: true });
    const controls = texturedBox(
      context.scene,
      `${fitout.id} · BUILT-IN-2616 · ovládací panel ${index + 1}`,
      { x: applianceCenter.x + 145, y: run.y0 - 34 },
      150,
      16,
      0.06,
      0.8,
      1,
    );
    finish(context, controls, materials.blackGlass, { pickable: true });
    const selector = CreateCylinder(
      `${fitout.id} · BUILT-IN-2616 · volič programu ${index + 1}`,
      { height: 0.024, diameter: 0.06, tessellation: 24 },
      context.scene,
    );
    selector.rotation.x = Math.PI / 2;
    selector.position.set(xM(applianceCenter.x - 150), 0.83, zM(run.y0 - 43));
    finish(context, selector, materials.applianceEnamel, { pickable: true });
  }
  for (const xMm of [builtIn.appliances[0].footprintMm.x0 - 18, 24699, run.x1 - 24]) {
    const sidePanel = texturedBox(
      context.scene,
      `${fitout.id} · BUILT-IN-2616 · zvislý skriňový panel`,
      { x: xMm, y: (run.y0 + run.y1) / 2 },
      32,
      run.y1 - run.y0,
      1.08,
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

  const windowBacksplash = texturedBox(
    context.scene,
    `${fitout.id} · WINDOW · súvislý veľkoformátový obklad pod vysokým oknom`,
    { x: 15340, y: 3514 },
    750,
    20,
    fitout.windowBacksplashTopElevationMm * MM_TO_M,
    0,
    1.2,
  );
  finish(context, windowBacksplash, materials.wallTile, { shadow: true });

  const bathBody = texturedBox(
    context.scene,
    `${fitout.id} · BATH-1800 · čistá biela vaňa so zaobleným vnútrom`,
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
    `${fitout.id} · BATH-1800 · tenký oválny lem`,
    { diameter: 1, thickness: 0.05, tessellation: 56 },
    context.scene,
  );
  bathRim.position.set(xM(bathCenter.x), bathtub.rimElevationMm * MM_TO_M, zM(bathCenter.y));
  bathRim.scaling.set(0.57, 0.72, 1.57);
  finish(context, bathRim, materials.sanitaryCeramic, { shadow: true, pickable: true });
  softEllipsoid(
    context,
    `${fitout.id} · BATH-1800 · hladké vnútro vane`,
    rectCenter(bathtub.innerBasinMm),
    [0.5, 0.018, 1.45],
    bathtub.rimElevationMm * MM_TO_M + 0.004,
    materials.mirrorGlass,
  );
  const bathDrain = CreateCylinder(
    `${fitout.id} · BATH-1800 · matne čierna výpusť`,
    { height: 0.008, diameter: 0.055, tessellation: 28 },
    context.scene,
  );
  bathDrain.position.set(xM(bathCenter.x), 0.586, zM(bathtub.innerBasinMm.y1 - 120));
  finish(context, bathDrain, materials.fireplace, { pickable: true });

  const bathMixer = texturedBox(
    context.scene,
    `${fitout.id} · BATH-1800 · podomietková čierna batéria`,
    { x: bathRect.x0 + 12, y: bathRect.y0 + 280 },
    24,
    220,
    0.1,
    0.76,
    1,
  );
  finish(context, bathMixer, materials.fireplace, { pickable: true });
  const bathSpout = CreateCylinder(
    `${fitout.id} · BATH-1800 · nástenný výtok`,
    { height: 0.2, diameter: 0.026, tessellation: 24 },
    context.scene,
  );
  bathSpout.rotation.z = Math.PI / 2;
  bathSpout.position.set(xM(bathRect.x0 + 105), 0.81, zM(bathRect.y0 + 280));
  finish(context, bathSpout, materials.fireplace, { shadow: true });

  const toilet = fitout.toilet;
  const toiletCenter = rectCenter(toilet.footprintMm);
  const cistern = texturedBox(
    context.scene,
    `${fitout.id} · WC · podomietkový modul pod vysokým oknom`,
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
  const flushPlate = texturedBox(
    context.scene,
    `${fitout.id} · WC · matne čierne dvojité splachovanie`,
    { x: toiletCenter.x, y: toilet.concealedCisternRectMm.y1 + 6 },
    190,
    12,
    0.11,
    0.84,
    1,
  );
  finish(context, flushPlate, materials.fireplace, { pickable: true });
  for (const xOffsetMm of [-42, 42]) {
    const button = CreateCylinder(
      `${fitout.id} · WC · splachovacie tlačidlo`,
      { height: 0.012, diameter: xOffsetMm < 0 ? 0.052 : 0.038, tessellation: 24 },
      context.scene,
    );
    button.rotation.x = Math.PI / 2;
    button.position.set(
      xM(toiletCenter.x + xOffsetMm),
      0.895,
      zM(toilet.concealedCisternRectMm.y1 + 13),
    );
    finish(context, button, materials.blackGlass);
  }
  softEllipsoid(
    context,
    `${fitout.id} · WC · kompaktná závesná misa`,
    { x: toiletCenter.x, y: 3844 },
    [0.34, 0.28, 0.44],
    0.32,
    materials.sanitaryCeramic,
  );
  softEllipsoid(
    context,
    `${fitout.id} · WC · vnútro misy`,
    { x: toiletCenter.x, y: 3890 },
    [0.23, 0.024, 0.3],
    0.455,
    materials.mirrorGlass,
  );
  const toiletSeat = CreateTorus(
    `${fitout.id} · WC · subtílne sedadlo`,
    { diameter: 0.31, thickness: 0.032, tessellation: 40 },
    context.scene,
  );
  toiletSeat.position.set(xM(toiletCenter.x), toilet.seatElevationMm * MM_TO_M, zM(3848));
  toiletSeat.scaling.set(1, 0.7, 1.32);
  finish(context, toiletSeat, materials.sanitaryCeramic, { shadow: true, pickable: true });

  const vanity = fitout.vanity;
  const vanityRect = vanity.footprintMm;
  const vanityCenter = rectCenter(vanityRect);
  const vanityShadow = texturedBox(
    context.scene,
    `${fitout.id} · VANITY-900 · tieň pod plávajúcou skrinkou`,
    { x: vanityCenter.x + 35, y: vanityCenter.y },
    vanityRect.x1 - vanityRect.x0 - 70,
    vanityRect.y1 - vanityRect.y0 - 60,
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
  softEllipsoid(
    context,
    `${fitout.id} · VANITY-900 · veľké biele integrované umývadlo`,
    basinCenter,
    [0.36, 0.14, 0.68],
    vanity.basinRimElevationMm * MM_TO_M - 0.05,
    materials.sanitaryCeramic,
  );
  softEllipsoid(
    context,
    `${fitout.id} · VANITY-900 · vnútorná misa`,
    { x: basinCenter.x - 20, y: basinCenter.y },
    [0.24, 0.024, 0.52],
    vanity.basinRimElevationMm * MM_TO_M + 0.008,
    materials.mirrorGlass,
  );
  const vanityDrain = CreateCylinder(
    `${fitout.id} · VANITY-900 · čierna výpusť`,
    { height: 0.008, diameter: 0.052, tessellation: 24 },
    context.scene,
  );
  vanityDrain.position.set(
    xM(basinCenter.x - 58),
    vanity.basinRimElevationMm * MM_TO_M + 0.022,
    zM(basinCenter.y),
  );
  finish(context, vanityDrain, materials.fireplace, { pickable: true });

  const mirrorGlow = texturedBox(
    context.scene,
    `${fitout.id} · VANITY-900 · nepriame LED za zrkadlom`,
    { x: vanity.mirrorPlanRectMm.x1 - 2, y: vanityCenter.y },
    4,
    vanity.mirrorPlanRectMm.y1 - vanity.mirrorPlanRectMm.y0 + 40,
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
  wallTap.rotation.z = Math.PI / 2;
  wallTap.position.set(xM(vanityRect.x1 - 90), 1.08, zM(vanityCenter.y));
  finish(context, wallTap, materials.fireplace, { shadow: true });

  const ceilingLight = CreateCylinder(
    `${fitout.id} · LIGHT · zapustené kruhové svietidlo`,
    { height: 0.018, diameter: 0.28, tessellation: 40 },
    context.scene,
  );
  ceilingLight.position.set(xM(15340), 2.565, zM(4560));
  finish(context, ceilingLight, materials.warmLight, { shadow: true });
  const roomLight = new PointLight(
    `${fitout.id} · LIGHT · mäkké teplé svetlo`,
    new Vector3(xM(15340), 2.42, zM(4560)),
    context.scene,
  );
  roomLight.diffuse = Color3.FromHexString("#ffd7ad");
  roomLight.specular = Color3.FromHexString("#756556");
  roomLight.intensity = 0.22;
  roomLight.range = 2.9;

  navigationGuard(context, materials, `${fitout.id} · BATH-1800 · navigačný obrys`, bathRect);
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

function hallwayWardrobeFrontX(
  wardrobe: HallwayBuiltInWardrobe,
  insetMm: number,
) {
  return wardrobe.facing === "EAST"
    ? wardrobe.footprintMm.x1 - insetMm
    : wardrobe.footprintMm.x0 + insetMm;
}

/**
 * Full-height, handleless oak cabinetry fitted into the two corridor recesses
 * marked by the client. Every visible layer stays inside the measured 601 mm
 * niche depth; one smooth invisible guard per cabinet provides stable avatar
 * collision without catching on panel reveals or the reeded accent.
 */
function buildHallwayBuiltInWardrobes(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
) {
  for (const wardrobe of HALLWAY_BUILT_IN_WARDROBES) {
    const rect = wardrobe.footprintMm;
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
      rect,
    );
  }
}

/**
 * Calm primary-bedroom composition for the compact en-suite room 1.08. The
 * fit-out keeps the exact 1 800 × 2 200 mm mattress requested by the client,
 * uses a flush platform to preserve the 657 mm foot aisle, and fills the east
 * wall with three sliding fronts so no wardrobe leaf can narrow the route
 * between the corridor and bathroom doors.
 */
function buildBedroomFitout(context: InteriorBuildContext, materials: InteriorMaterials) {
  const fitout = BEDROOM_FITOUT;
  const bed = fitout.bed;
  const bedRect = bed.footprintMm;
  const mattressRect = bed.mattressFootprintMm;

  const rugRect: RectMm = { x0: 17742, y0: 3504, x1: 20142, y1: 5904 };
  const rug = texturedBox(
    context.scene,
    `${fitout.id} · BED · veľký vlnený koberec pod posteľou`,
    rectCenter(rugRect),
    rugRect.x1 - rugRect.x0,
    rugRect.y1 - rugRect.y0,
    0.012,
    0.004,
    1,
  );
  finish(context, rug, materials.rug);

  const floatingShadow = texturedBox(
    context.scene,
    `${fitout.id} · BED · tieň pod plávajúcou platformou`,
    rectCenter({
      x0: bedRect.x0 + 90,
      y0: bedRect.y0 + 120,
      x1: bedRect.x1 - 90,
      y1: bedRect.y1 - 90,
    }),
    bedRect.x1 - bedRect.x0 - 180,
    bedRect.y1 - bedRect.y0 - 210,
    0.08,
    0.025,
    1,
  );
  finish(context, floatingShadow, materials.fireplace);

  const platformTopM = bed.frameHeightMm * MM_TO_M;
  const platform = texturedBox(
    context.scene,
    `${fitout.id} · BED · subtílna čalúnená platforma 1 800 × 2 200`,
    rectCenter(bedRect),
    bedRect.x1 - bedRect.x0,
    bedRect.y1 - bedRect.y0,
    platformTopM - 0.08,
    0.08,
    1,
  );
  finish(context, platform, materials.upholstery, { shadow: true, pickable: true });

  const mattressTopM = bed.mattressTopElevationMm * MM_TO_M;
  const mattress = texturedBox(
    context.scene,
    `${fitout.id} · BED · matrac ${bed.mattressWidthMm} × ${bed.mattressLengthMm}`,
    rectCenter(mattressRect),
    mattressRect.x1 - mattressRect.x0,
    mattressRect.y1 - mattressRect.y0,
    mattressTopM - platformTopM,
    platformTopM,
    1,
  );
  finish(context, mattress, materials.bedroomLinen, { shadow: true, pickable: true });

  const headboard = texturedBox(
    context.scene,
    `${fitout.id} · BED · nízke čalúnené čelo pod parapetom +0,900`,
    rectCenter(bed.headboardRectMm),
    bed.headboardRectMm.x1 - bed.headboardRectMm.x0,
    bed.headboardRectMm.y1 - bed.headboardRectMm.y0,
    bed.headboardTopElevationMm * MM_TO_M - 0.04,
    0.04,
    1,
  );
  finish(context, headboard, materials.upholstery, { shadow: true, pickable: true });
  for (const [index, seamX] of [18492, 18942, 19392].entries()) {
    const seam = texturedBox(
      context.scene,
      `${fitout.id} · BED · zvislé prešívanie čela ${index + 1}`,
      { x: seamX, y: bed.headboardRectMm.y1 + 4 },
      7,
      8,
      0.72,
      0.1,
      1,
    );
    finish(context, seam, materials.accentFabric);
  }

  const duvetRect: RectMm = { x0: 18092, y0: 4180, x1: 19792, y1: 5640 };
  const duvet = texturedBox(
    context.scene,
    `${fitout.id} · BED · mäkká ľanová prikrývka`,
    rectCenter(duvetRect),
    duvetRect.x1 - duvetRect.x0,
    duvetRect.y1 - duvetRect.y0,
    0.07,
    mattressTopM - 0.005,
    1,
  );
  finish(context, duvet, materials.bedroomLinen, { shadow: true, pickable: true });
  const throwRect: RectMm = { x0: 18112, y0: 5150, x1: 19772, y1: 5595 };
  const bedThrow = texturedBox(
    context.scene,
    `${fitout.id} · BED · vlnený prehoz pri nohách`,
    rectCenter(throwRect),
    throwRect.x1 - throwRect.x0,
    throwRect.y1 - throwRect.y0,
    0.04,
    mattressTopM + 0.064,
    1,
  );
  finish(context, bedThrow, materials.bedroomThrow, { shadow: true, pickable: true });

  for (const [index, pillowX] of [18520, 19404].entries()) {
    const pillow = softEllipsoid(
      context,
      `${fitout.id} · BED · ergonomický vankúš ${index + 1}`,
      { x: pillowX, y: 3850 },
      [0.72, 0.18, 0.48],
      mattressTopM + 0.105,
      materials.bedroomLinen,
    );
    pillow.rotation.y = index === 0 ? -0.035 : 0.035;
  }
  const lumbar = softEllipsoid(
    context,
    `${fitout.id} · BED · akcentový bedrový vankúš`,
    { x: 18962, y: 4040 },
    [0.9, 0.2, 0.28],
    mattressTopM + 0.145,
    materials.bedroomThrow,
  );
  lumbar.rotation.y = 0.025;

  const wardrobe = fitout.wardrobe;
  const wardrobeRect = wardrobe.footprintMm;
  const wardrobeHeightM = wardrobe.heightMm * MM_TO_M;
  // The 600 mm contract includes every visible layer: a 40 mm body setback
  // leaves the sliding fronts and black accents entirely inside the footprint.
  const wardrobeBodyRect: RectMm = {
    ...wardrobeRect,
    x0: wardrobeRect.x0 + 40,
  };
  const carcase = texturedBox(
    context.scene,
    `${fitout.id} · WARDROBE · celostenová vstavaná skriňa ${wardrobeRect.y1 - wardrobeRect.y0} × ${wardrobeRect.x1 - wardrobeRect.x0}`,
    rectCenter(wardrobeBodyRect),
    wardrobeBodyRect.x1 - wardrobeBodyRect.x0,
    wardrobeBodyRect.y1 - wardrobeBodyRect.y0,
    wardrobeHeightM,
    0,
    1.2,
  );
  finish(context, carcase, materials.wardrobeFront, {
    shadow: true,
    pickable: true,
    cameraOccluder: true,
  });

  const toeKick = texturedBox(
    context.scene,
    `${fitout.id} · WARDROBE · zapustený čierny sokel`,
    { x: wardrobeRect.x0 + 36, y: (wardrobeRect.y0 + wardrobeRect.y1) / 2 },
    32,
    wardrobeRect.y1 - wardrobeRect.y0 - 70,
    0.08,
    0,
    1,
  );
  finish(context, toeKick, materials.fireplace);

  const panelSpanMm = (wardrobeRect.y1 - wardrobeRect.y0) / wardrobe.slidingPanelCount;
  for (let index = 0; index < wardrobe.slidingPanelCount; index += 1) {
    const panelY0 = wardrobeRect.y0 + index * panelSpanMm;
    const panelY1 = panelY0 + panelSpanMm;
    const panel = texturedBox(
      context.scene,
      `${fitout.id} · WARDROBE · posuvný panel ${index + 1}${index === wardrobe.mirroredPanelIndex ? " · zrkadlo" : " · matný greige"}`,
      { x: wardrobeRect.x0 + 17, y: (panelY0 + panelY1) / 2 },
      30,
      panelSpanMm - 10,
      wardrobeHeightM - 0.09,
      0.045,
      1,
    );
    finish(
      context,
      panel,
      index === wardrobe.mirroredPanelIndex ? materials.mirrorGlass : materials.wardrobeFront,
      { shadow: true, pickable: true },
    );
    if (index > 0) {
      const joint = texturedBox(
        context.scene,
        `${fitout.id} · WARDROBE · tieňová škára posuvných dverí ${index}`,
        { x: wardrobeRect.x0 + 6, y: panelY0 },
        12,
        9,
        wardrobeHeightM - 0.16,
        0.08,
        1,
      );
      finish(context, joint, materials.fireplace);
    }
  }
  const endLed = texturedBox(
    context.scene,
    `${fitout.id} · WARDROBE · vertikálne ambientné svetlo 2700 K`,
    { x: wardrobeRect.x0 + 8, y: wardrobeRect.y0 + 16 },
    16,
    18,
    2.18,
    0.18,
    1,
  );
  finish(context, endLed, materials.warmLight);

  const lightCenter = { x: 18962, y: 4800 };
  const ceilingHousing = texturedBox(
    context.scene,
    `${fitout.id} · LIGHT · subtílny čierny lineárny profil`,
    lightCenter,
    52,
    1320,
    0.035,
    2.55,
    1,
  );
  finish(context, ceilingHousing, materials.fireplace, { shadow: true });
  const ceilingDiffuser = texturedBox(
    context.scene,
    `${fitout.id} · LIGHT · neoslňujúci teplý difúzor`,
    lightCenter,
    28,
    1260,
    0.012,
    2.538,
    1,
  );
  finish(context, ceilingDiffuser, materials.warmLight);
  const bedroomLight = new PointLight(
    `${fitout.id} · LIGHT · mäkké večerné svetlo`,
    new Vector3(xM(lightCenter.x), 2.42, zM(lightCenter.y)),
    context.scene,
  );
  bedroomLight.diffuse = Color3.FromHexString("#ffd3a2");
  bedroomLight.specular = Color3.FromHexString("#8b7259");
  bedroomLight.intensity = 0.24;
  bedroomLight.range = 3.2;

  navigationGuard(context, materials, `${fitout.id} · BED · navigačný obrys`, bedRect);
  navigationGuard(
    context,
    materials,
    `${fitout.id} · WARDROBE · navigačný obrys`,
    wardrobeRect,
  );
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
  const frame = texturedBox(
    context.scene,
    `${fitout.id} · BED · úložná plávajúca posteľ`,
    rectCenter(bedRect),
    bedRect.x1 - bedRect.x0,
    bedRect.y1 - bedRect.y0,
    frameTopM - 0.065,
    0.065,
    1,
  );
  finish(context, frame, theme.primary, { shadow: true, pickable: true });

  const mattressTopM = bed.mattressTopElevationMm * MM_TO_M;
  const mattress = texturedBox(
    context.scene,
    `${fitout.id} · BED · matrac ${bed.mattressWidthMm} × ${bed.mattressLengthMm}`,
    rectCenter(mattressRect),
    mattressRect.x1 - mattressRect.x0,
    mattressRect.y1 - mattressRect.y0,
    mattressTopM - frameTopM,
    frameTopM,
    1,
  );
  finish(context, mattress, materials.bedroomLinen, { shadow: true, pickable: true });

  const headboard = texturedBox(
    context.scene,
    `${fitout.id} · BED · vysoké mäkké čelo`,
    rectCenter(bed.headboardRectMm),
    bed.headboardRectMm.x1 - bed.headboardRectMm.x0,
    bed.headboardRectMm.y1 - bed.headboardRectMm.y0,
    bed.headboardTopElevationMm * MM_TO_M - 0.05,
    0.05,
    1,
  );
  finish(context, headboard, theme.secondary, { shadow: true, pickable: true });

  const duvetRect: RectMm = {
    x0: mattressRect.x0 + 70,
    y0: mattressRect.y0 + 55,
    x1: mattressRect.x1 - 70,
    y1: mattressRect.y1 - 55,
  };
  const duvet = texturedBox(
    context.scene,
    `${fitout.id} · BED · pokojná ľanová prikrývka`,
    rectCenter(duvetRect),
    duvetRect.x1 - duvetRect.x0,
    duvetRect.y1 - duvetRect.y0,
    0.055,
    mattressTopM - 0.004,
    1,
  );
  finish(context, duvet, materials.bedroomLinen, { shadow: true, pickable: true });

  const forward = furnitureForward(bed.facing);
  const mattressCenter = rectCenter(mattressRect);
  const pillowCenter: Point2Mm = {
    x: mattressCenter.x - forward.x * (bed.mattressLengthMm / 2 - 270),
    y: mattressCenter.y - forward.y * (bed.mattressLengthMm / 2 - 270),
  };
  softEllipsoid(
    context,
    `${fitout.id} · BED · veľký ergonomický vankúš`,
    pillowCenter,
    [0.42, 0.17, 0.72],
    mattressTopM + 0.1,
    materials.bedroomLinen,
  );

  const throwCenter: Point2Mm = {
    x: mattressCenter.x + forward.x * (bed.mattressLengthMm / 2 - 270),
    y: mattressCenter.y + forward.y * (bed.mattressLengthMm / 2 - 270),
  };
  const throwLengthMm = 430;
  const throwRect: RectMm = {
    x0: throwCenter.x - throwLengthMm / 2,
    y0: mattressRect.y0 + 65,
    x1: throwCenter.x + throwLengthMm / 2,
    y1: mattressRect.y1 - 65,
  };
  const throwBlanket = texturedBox(
    context.scene,
    `${fitout.id} · BED · farebný vlnený prehoz`,
    rectCenter(throwRect),
    throwRect.x1 - throwRect.x0,
    throwRect.y1 - throwRect.y0,
    0.035,
    mattressTopM + 0.05,
    1,
  );
  finish(context, throwBlanket, theme.secondary, { shadow: true, pickable: true });

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
  const bodyRect: RectMm = { ...rect, x1: rect.x1 - 34 };
  const body = texturedBox(
    context.scene,
    `${fitout.id} · WARDROBE · celovýšková vstavaná skriňa`,
    rectCenter(bodyRect),
    bodyRect.x1 - bodyRect.x0,
    bodyRect.y1 - bodyRect.y0,
    heightM,
    0,
    1.2,
  );
  finish(context, body, theme.primary, {
    shadow: true,
    pickable: true,
    cameraOccluder: true,
  });

  const frontSpanMm = (rect.y1 - rect.y0) / wardrobe.doorCount;
  for (let index = 0; index < wardrobe.doorCount; index += 1) {
    const y0 = rect.y0 + index * frontSpanMm;
    const y1 = y0 + frontSpanMm;
    const front = texturedBox(
      context.scene,
      `${fitout.id} · WARDROBE · bezúchytkové čelo ${index + 1}`,
      { x: rect.x1 - 15, y: (y0 + y1) / 2 },
      30,
      frontSpanMm - 8,
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
        { x: rect.x1 - 3, y: y0 },
        10,
        8,
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
    { x: rect.x1 - 24, y: (rect.y0 + rect.y1) / 2 },
    42,
    rect.y1 - rect.y0 - 50,
    0.075,
    0,
    1,
  );
  finish(context, plinth, materials.fireplace);
  const verticalLight = texturedBox(
    context.scene,
    `${fitout.id} · WARDROBE · integrované ambientné svetlo`,
    { x: rect.x1 - 4, y: rect.y0 + 16 },
    12,
    20,
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
    desk.facing === "SOUTH" ? 620 : 220,
    desk.facing === "SOUTH" ? 220 : 620,
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
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  fitout: ChildBedroomFitout,
  theme: ChildRoomThemeMaterials,
) {
  const chair = fitout.chair;
  const center = chair.centerMm;
  const seatM = chair.seatElevationMm * MM_TO_M;
  const hub = CreateCylinder(
    `${fitout.id} · CHAIR · centrálna päťramenná báza`,
    { height: 0.075, diameter: 0.12, tessellation: 24 },
    context.scene,
  );
  hub.position.set(xM(center.x), 0.1, zM(center.y));
  finish(context, hub, materials.fireplace, { shadow: true });
  const liftHeightM = Math.max(0.2, seatM - 0.18);
  const lift = CreateCylinder(
    `${fitout.id} · CHAIR · nastaviteľný plynový piest`,
    { height: liftHeightM, diameter: 0.05, tessellation: 20 },
    context.scene,
  );
  lift.position.set(xM(center.x), 0.14 + liftHeightM / 2, zM(center.y));
  finish(context, lift, materials.steel, { shadow: true });

  for (let index = 0; index < chair.wheelCount; index += 1) {
    const angle = (index / chair.wheelCount) * Math.PI * 2;
    const spokeLengthMm = 315;
    const spokeCenter: Point2Mm = {
      x: center.x + Math.cos(angle) * spokeLengthMm * 0.5,
      y: center.y + Math.sin(angle) * spokeLengthMm * 0.5,
    };
    const spoke = texturedBox(
      context.scene,
      `${fitout.id} · CHAIR · rameno pojazdu ${index + 1}`,
      spokeCenter,
      spokeLengthMm,
      30,
      0.028,
      0.06,
      1,
    );
    spoke.rotation.y = angle;
    finish(context, spoke, materials.fireplace, { shadow: true });
    const caster = CreateTorus(
      `${fitout.id} · CHAIR · tiché koliesko ${index + 1}`,
      { diameter: 0.064, thickness: 0.017, tessellation: 18 },
      context.scene,
    );
    caster.rotation.z = Math.PI / 2;
    caster.rotation.y = angle;
    caster.position.set(
      xM(center.x + Math.cos(angle) * spokeLengthMm),
      0.052,
      zM(center.y + Math.sin(angle) * spokeLengthMm),
    );
    finish(context, caster, materials.fireplace, { shadow: true });
  }

  const seat = softEllipsoid(
    context,
    `${fitout.id} · CHAIR · mäkký otočný sedák`,
    center,
    [0.55, 0.13, 0.52],
    seatM,
    theme.chair,
  );
  seat.rotation.y = chair.facing === "EAST" ? Math.PI / 2 : 0;
  const forward = furnitureForward(chair.facing);
  const backCenter: Point2Mm = {
    x: center.x - forward.x * 230,
    y: center.y - forward.y * 230,
  };
  const backBottomM = seatM + 0.08;
  const backTopM = chair.backTopElevationMm * MM_TO_M;
  const back = softCapsule(
    context,
    `${fitout.id} · CHAIR · ergonomické čalúnené operadlo`,
    backCenter,
    (backBottomM + backTopM) / 2,
    backTopM - backBottomM,
    0.17,
    new Vector3(0, 1, 0),
    [1.25, 1, 0.3],
    theme.chair,
  );
  back.rotation.y = chair.facing === "EAST" ? Math.PI / 2 : 0;
  const right = furnitureRight(chair.facing);
  for (const [index, side] of [-1, 1].entries()) {
    const armCenter: Point2Mm = {
      x: center.x + right.x * side * 235,
      y: center.y + right.y * side * 235,
    };
    softCapsule(
      context,
      `${fitout.id} · CHAIR · mäkká podrúčka ${index + 1}`,
      armCenter,
      seatM + 0.22,
      0.28,
      0.035,
      new Vector3(forward.x, 0, forward.y),
      [1, 0.8, 1],
      theme.chair,
    );
  }

  navigationGuard(
    context,
    materials,
    `${fitout.id} · CHAIR · navigačný obrys pojazdu`,
    chair.footprintMm,
  );
}

function buildChildFeatureWall(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
  fitout: ChildBedroomFitout,
  theme: ChildRoomThemeMaterials,
) {
  const feature = fitout.featureWall;
  const rect = feature.footprintMm;
  const panel = texturedBox(
    context.scene,
    `${fitout.id} · FEATURE · farebný akustický panel`,
    rectCenter(rect),
    rect.x1 - rect.x0,
    rect.y1 - rect.y0,
    feature.topElevationMm * MM_TO_M,
    0,
    1,
  );
  finish(context, panel, theme.primary, { shadow: true, pickable: true });

  const wallX = feature.facing === "WEST" ? rect.x0 - 10 : rect.x1 + 10;
  if (feature.motif === "GLOW_HALO") {
    for (let index = 0; index < 7; index += 1) {
      const slatY = rect.y0 + 105 + index * ((rect.y1 - rect.y0 - 210) / 6);
      const slat = texturedBox(
        context.scene,
        `${fitout.id} · FEATURE · jemná dubová lamela ${index + 1}`,
        { x: wallX, y: slatY },
        22,
        34,
        1.72,
        0.24,
        1,
      );
      finish(context, slat, materials.kitchenFront, { shadow: true });
    }
    const halo = CreateTorus(
      `${fitout.id} · FEATURE · svetelný kruh`,
      { diameter: 0.78, thickness: 0.026, tessellation: 48 },
      context.scene,
    );
    halo.rotation.z = Math.PI / 2;
    halo.position.set(xM(wallX - 12), 1.55, zM((rect.y0 + rect.y1) / 2));
    finish(context, halo, materials.warmLight, { shadow: true, pickable: true });
  } else {
    for (let index = 0; index < 6; index += 1) {
      const slatY = rect.y0 + 110 + index * ((rect.y1 - rect.y0 - 220) / 5);
      const slat = texturedBox(
        context.scene,
        `${fitout.id} · FEATURE · rytmická dubová lamela ${index + 1}`,
        { x: wallX, y: slatY },
        24,
        52,
        index % 2 === 0 ? 1.72 : 1.46,
        0.28,
        1,
      );
      finish(context, slat, materials.kitchenFront, { shadow: true, pickable: true });
    }
    const ribbon = texturedBox(
      context.scene,
      `${fitout.id} · FEATURE · horizontálna svetelná stuha`,
      { x: wallX + 4, y: (rect.y0 + rect.y1) / 2 },
      18,
      rect.y1 - rect.y0 - 210,
      0.018,
      1.63,
      1,
    );
    finish(context, ribbon, materials.warmLight);
  }
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

  const alongX = pinboard.facing === "SOUTH";
  const longStart = alongX ? rect.x0 : rect.y0;
  const longEnd = alongX ? rect.x1 : rect.y1;
  const noteMaterials = [theme.secondary, materials.kitchenUpper, theme.primary];
  for (let index = 0; index < 3; index += 1) {
    const along = longStart + (index + 1) * ((longEnd - longStart) / 4);
    const noteCenter: Point2Mm = alongX
      ? { x: along, y: rect.y0 - 6 }
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
  const center = fitout.roomId === "ROOM-1-09"
    ? { x: 17880, y: 9050 }
    : { x: 12950, y: 9000 };
  const alongX = bounds.x1 - bounds.x0 > bounds.y1 - bounds.y0;
  const housing = texturedBox(
    context.scene,
    `${fitout.id} · LIGHT · minimalistický stropný profil`,
    center,
    alongX ? 1450 : 54,
    alongX ? 54 : 1450,
    0.034,
    room.clearHeightMm * MM_TO_M - 0.04,
    1,
  );
  finish(context, housing, materials.fireplace, { shadow: true });
  const diffuser = texturedBox(
    context.scene,
    `${fitout.id} · LIGHT · teplý stmievateľný difúzor`,
    center,
    alongX ? 1380 : 28,
    alongX ? 28 : 1380,
    0.012,
    room.clearHeightMm * MM_TO_M - 0.052,
    1,
  );
  finish(context, diffuser, materials.warmLight);
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
  }
}

/**
 * Compact entry composition in the 1.01 recess: closed coat storage at the
 * corridor end, a low shoe cabinet/bench at the front door and an illuminated
 * oak hook niche between them. The two floor guards deliberately follow only
 * the solid modules, leaving the generous central circulation area untouched.
 */
function buildEntryFitout(context: InteriorBuildContext, materials: InteriorMaterials) {
  const fitout = ENTRY_FITOUT;
  const wardrobe = fitout.wardrobe;
  const wardrobeRect = wardrobe.footprintMm;
  const wardrobeHeightM = fitout.heightMm * MM_TO_M;

  const wardrobeBody = texturedBox(
    context.scene,
    `${fitout.id} · COATS · celovýšková bezúchytková skriňa na kabáty`,
    rectCenter(wardrobeRect),
    wardrobeRect.x1 - wardrobeRect.x0,
    wardrobeRect.y1 - wardrobeRect.y0,
    wardrobeHeightM,
    0,
    1.2,
  );
  finish(context, wardrobeBody, materials.livingCabinet, { shadow: true, pickable: true });

  const wardrobeJoint = texturedBox(
    context.scene,
    `${fitout.id} · COATS · stredová tieňová škára dverí`,
    { x: wardrobeRect.x0 - 3, y: (wardrobeRect.y0 + wardrobeRect.y1) / 2 },
    7,
    4,
    wardrobeHeightM - 0.11,
    0.055,
    1,
  );
  finish(context, wardrobeJoint, materials.fireplace);

  for (const elevationM of [0.055, wardrobe.upperShelfElevationMm * MM_TO_M]) {
    const joint = texturedBox(
      context.scene,
      `${fitout.id} · COATS · horizontálna škára ${elevationM.toFixed(3)}`,
      { x: wardrobeRect.x0 - 3, y: (wardrobeRect.y0 + wardrobeRect.y1) / 2 },
      7,
      wardrobeRect.y1 - wardrobeRect.y0 - 26,
      0.006,
      elevationM,
      1,
    );
    finish(context, joint, materials.fireplace);
  }

  const wardrobePlinth = texturedBox(
    context.scene,
    `${fitout.id} · COATS · zapustený čierny sokel`,
    { x: wardrobeRect.x0 - 4, y: (wardrobeRect.y0 + wardrobeRect.y1) / 2 },
    12,
    wardrobeRect.y1 - wardrobeRect.y0 - 28,
    0.055,
    0,
    1,
  );
  finish(context, wardrobePlinth, materials.fireplace);

  const overhead = fitout.overheadCabinet;
  const overheadHeightM = wardrobeHeightM - overhead.bottomElevationMm * MM_TO_M;
  const overheadBody = texturedBox(
    context.scene,
    `${fitout.id} · OVERHEAD · horná úložná skriňa nad sedením`,
    rectCenter(overhead.footprintMm),
    overhead.footprintMm.x1 - overhead.footprintMm.x0,
    overhead.footprintMm.y1 - overhead.footprintMm.y0,
    overheadHeightM,
    overhead.bottomElevationMm * MM_TO_M,
    1.2,
  );
  finish(context, overheadBody, materials.livingCabinet, { shadow: true, pickable: true });

  const overheadJoint = texturedBox(
    context.scene,
    `${fitout.id} · OVERHEAD · stredová tieňová škára`,
    {
      x: overhead.footprintMm.x0 - 3,
      y: (overhead.footprintMm.y0 + overhead.footprintMm.y1) / 2,
    },
    7,
    4,
    overheadHeightM - 0.08,
    overhead.bottomElevationMm * MM_TO_M + 0.04,
    1,
  );
  finish(context, overheadJoint, materials.fireplace);

  const panel = fitout.hookPanel;
  const panelBody = texturedBox(
    context.scene,
    `${fitout.id} · NICHE · zvislý dubový panel na kabáty`,
    rectCenter(panel.footprintMm),
    panel.footprintMm.x1 - panel.footprintMm.x0,
    panel.footprintMm.y1 - panel.footprintMm.y0,
    (panel.topElevationMm - panel.bottomElevationMm) * MM_TO_M,
    panel.bottomElevationMm * MM_TO_M,
    1.1,
  );
  finish(context, panelBody, materials.kitchenFront, { shadow: true, pickable: true });

  for (const [index, hookCenter] of panel.hookCentersMm.entries()) {
    const peg = CreateCylinder(
      `${fitout.id} · HOOKS · matný čierny háčik ${index + 1}`,
      { height: 0.08, diameter: 0.032, tessellation: 24 },
      context.scene,
    );
    peg.rotation.z = Math.PI / 2;
    peg.position.set(xM(hookCenter.x), panel.hookElevationMm * MM_TO_M, zM(hookCenter.y));
    finish(context, peg, materials.fireplace, { shadow: true, pickable: true });

    const stop = CreateSphere(
      `${fitout.id} · HOOKS · koncovka háčika ${index + 1}`,
      { diameter: 0.046, segments: 20 },
      context.scene,
    );
    stop.position.set(
      xM(hookCenter.x - 30),
      panel.hookElevationMm * MM_TO_M + 0.018,
      zM(hookCenter.y),
    );
    finish(context, stop, materials.fireplace, { shadow: true, pickable: true });
  }

  const bench = fitout.bench;
  const benchRect = bench.footprintMm;
  const shoeBodyHeightM = (bench.seatElevationMm - bench.cushionThicknessMm) * MM_TO_M;
  const shoeBody = texturedBox(
    context.scene,
    `${fitout.id} · SHOES · dvojzásuvkový botník pod lavicou`,
    rectCenter(benchRect),
    benchRect.x1 - benchRect.x0,
    benchRect.y1 - benchRect.y0,
    shoeBodyHeightM,
    0,
    1.1,
  );
  finish(context, shoeBody, materials.livingCabinet, { shadow: true, pickable: true });

  const drawerJoint = texturedBox(
    context.scene,
    `${fitout.id} · SHOES · deliaca škára dvoch zásuviek`,
    { x: benchRect.x0 - 3, y: (benchRect.y0 + benchRect.y1) / 2 },
    7,
    4,
    shoeBodyHeightM - 0.075,
    0.055,
    1,
  );
  finish(context, drawerJoint, materials.fireplace);

  const benchPlinth = texturedBox(
    context.scene,
    `${fitout.id} · SHOES · zapustený čierny sokel`,
    { x: benchRect.x0 - 4, y: (benchRect.y0 + benchRect.y1) / 2 },
    12,
    benchRect.y1 - benchRect.y0 - 24,
    0.055,
    0,
    1,
  );
  finish(context, benchPlinth, materials.fireplace);

  const cushion = softEllipsoid(
    context,
    `${fitout.id} · SEAT · mäkký čalúnený sedák`,
    rectCenter(benchRect),
    [0.43, bench.cushionThicknessMm * MM_TO_M, 0.62],
    (bench.seatElevationMm - bench.cushionThicknessMm / 2) * MM_TO_M,
    materials.accentFabric,
  );
  cushion.scaling.z *= 0.96;

  const led = texturedBox(
    context.scene,
    `${fitout.id} · LIGHT · skrytý 2700 K pás v nike`,
    {
      x: overhead.footprintMm.x0 - 8,
      y: (benchRect.y0 + benchRect.y1) / 2,
    },
    16,
    benchRect.y1 - benchRect.y0 - 60,
    0.014,
    overhead.bottomElevationMm * MM_TO_M - 0.02,
    1,
  );
  finish(context, led, materials.warmLight);

  const nicheLight = new PointLight(
    `${fitout.id} · LIGHT · teplé svetlo zádveria`,
    new Vector3(
      xM(overhead.footprintMm.x0 - 160),
      1.78,
      zM((benchRect.y0 + benchRect.y1) / 2),
    ),
    context.scene,
  );
  nicheLight.diffuse = Color3.FromHexString("#ffd1a0");
  nicheLight.specular = Color3.FromHexString("#6f5a48");
  nicheLight.intensity = 0.18;
  nicheLight.range = 1.7;

  navigationGuard(context, materials, `${fitout.id} · COATS · navigačný obrys`, wardrobeRect);
  navigationGuard(context, materials, `${fitout.id} · SHOES · navigačný obrys`, benchRect);
}

/**
 * Client home-office concept for room 1.04. The fixed geometry comes from
 * `OFFICE_FITOUT`; this builder adds the calm greige/oak finish, convincingly
 * thin technology and soft ergonomic forms without compromising the clear
 * entry bay.
 */
function buildOfficeFitout(context: InteriorBuildContext, materials: InteriorMaterials) {
  const fitout = OFFICE_FITOUT;
  const cabinet = fitout.cabinet;
  const cabinetRect = cabinet.footprintMm;
  const niche = cabinet.printerNiche;
  const nicheRect = niche.footprintMm;
  const cabinetHeightM = cabinet.heightMm * MM_TO_M;
  const nicheBottomM = niche.bottomElevationMm * MM_TO_M;
  const nicheHeightM = niche.heightMm * MM_TO_M;

  // Full-height handleless wall. The printer bay is modelled as a real void
  // between lower and upper carcasses, not as a dark decal on a solid box.
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
    rectCenter({ ...nicheRect, x0: cabinetRect.x0 }),
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
    rectCenter({ ...nicheRect, x0: cabinetRect.x0 }),
    cabinetRect.x1 - cabinetRect.x0,
    nicheRect.y1 - nicheRect.y0,
    cabinetHeightM - upperBottomM,
    upperBottomM,
    1.2,
  );
  finish(context, nicheUpper, materials.livingCabinet, { shadow: true, pickable: true });

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
    { x: nicheRect.x0 + 8, y: (nicheRect.y0 + nicheRect.y1) / 2 },
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
    { x: nicheRect.x1 - 18, y: (nicheRect.y0 + nicheRect.y1) / 2 },
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
      { x: cabinetRect.x1 + 3, y: seamY },
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
    { x: cabinetRect.x1 + 4, y: (cabinetRect.y0 + cabinetRect.y1) / 2 },
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
    { x: printer.footprintMm.x1 + 4, y: printerCenter.y },
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
    { x: printer.footprintMm.x1 + 7, y: printer.footprintMm.y0 + 78 },
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
    { x: printer.footprintMm.x1 + 16, y: printerCenter.y },
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
  for (const [frameIndex, frameX] of [deskRect.x0 + 135, deskRect.x1 - 135].entries()) {
    for (const yMm of [deskRect.y0 + 72, deskRect.y1 - 72]) {
      const leg = texturedBox(
        context.scene,
        `${fitout.id} · DESK · čierna noha rámu ${frameIndex + 1}`,
        { x: frameX, y: yMm },
        42,
        36,
        legHeightM,
        0.015,
        1,
      );
      finish(context, leg, materials.fireplace, { shadow: true });
    }
    const frameRail = texturedBox(
      context.scene,
      `${fitout.id} · DESK · horná priečka rámu ${frameIndex + 1}`,
      { x: frameX, y: (deskRect.y0 + deskRect.y1) / 2 },
      42,
      deskRect.y1 - deskRect.y0 - 126,
      0.036,
      deskTopM - deskThicknessM - 0.052,
      1,
    );
    finish(context, frameRail, materials.fireplace, { shadow: true });
  }
  const cableTray = texturedBox(
    context.scene,
    `${fitout.id} · DESK · skrytý káblový žľab`,
    { x: (deskRect.x0 + deskRect.x1) / 2, y: deskRect.y0 + 150 },
    880,
    150,
    0.09,
    deskTopM - 0.14,
    1,
  );
  finish(context, cableTray, materials.fireplace, { shadow: true });

  // Curved 40-inch 21:9 ultrawide. Nine tangential panels run along plan X;
  // their concave face points north toward the chair while the compact 2500R
  // shell remains visually thin above the oak top.
  const monitor = desk.monitor;
  const segmentCount = 9;
  const segmentWidthMm = monitor.widthMm / segmentCount;
  const curveRadiusMm = monitor.curveRadiusMm;
  const shellBottomM = (monitor.centerElevationMm - monitor.heightMm / 2) * MM_TO_M;
  for (let index = 0; index < segmentCount; index += 1) {
    const offsetMm = -monitor.widthMm / 2 + segmentWidthMm * (index + 0.5);
    const radiusAlongMm = Math.sqrt(Math.max(1, curveRadiusMm ** 2 - offsetMm ** 2));
    const curveDepthMm = curveRadiusMm - radiusAlongMm;
    const yaw = Math.asin(offsetMm / curveRadiusMm);
    const shellCenter: Point2Mm = {
      x: monitor.centerMm.x + offsetMm,
      y: monitor.centerMm.y + curveDepthMm,
    };
    const shell = texturedBox(
      context.scene,
      `${fitout.id} · MONITOR-40-21:9 · zakrivený zadný segment ${index + 1}`,
      shellCenter,
      segmentWidthMm + 5,
      monitor.maxThicknessMm,
      monitor.heightMm * MM_TO_M,
      shellBottomM,
      1,
    );
    shell.rotation.y = yaw;
    finish(context, shell, materials.fireplace, { shadow: true, pickable: true });

    const normalX = -offsetMm / curveRadiusMm;
    const normalY = radiusAlongMm / curveRadiusMm;
    const glassOffsetMm = monitor.maxThicknessMm / 2 + 3;
    const glass = texturedBox(
      context.scene,
      `${fitout.id} · MONITOR-40-21:9 · obrazový segment ${index + 1}`,
      {
        x: shellCenter.x + normalX * glassOffsetMm,
        y: shellCenter.y + normalY * glassOffsetMm,
      },
      segmentWidthMm + 1,
      4,
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
    { x: monitor.centerMm.x, y: monitor.centerMm.y - 35 },
    410,
    220,
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
    { x: monitor.centerMm.x, y: monitor.centerMm.y - 20 },
    54,
    46,
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
  const chairWidthM = (chair.footprintMm.x1 - chair.footprintMm.x0) * MM_TO_M;
  const chairDepthM = (chair.footprintMm.y1 - chair.footprintMm.y0) * MM_TO_M;
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
    { x: chairCenter.x, y: chairCenter.y - 45 },
    [chairWidthM * 0.72, 0.135, chairDepthM * 0.7],
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

  const backCenterY = chairCenter.y + 250;
  const backBottomM = seatM + 0.08;
  const backTopM = chair.backTopElevationMm * MM_TO_M;
  softCapsule(
    context,
    `${fitout.id} · CHAIR · vysoké ergonomické operadlo`,
    { x: chairCenter.x, y: backCenterY },
    (backBottomM + backTopM) / 2,
    backTopM - backBottomM,
    0.18,
    new Vector3(0, 1, 0),
    [1.45, 1, 0.34],
    materials.officeFabric,
  );
  softEllipsoid(
    context,
    `${fitout.id} · CHAIR · nastaviteľná bedrová opora`,
    { x: chairCenter.x, y: backCenterY - 72 },
    [0.48, 0.24, 0.095],
    seatM + 0.26,
    materials.accentFabric,
  );
  softEllipsoid(
    context,
    `${fitout.id} · CHAIR · mäkká hlavová opierka`,
    { x: chairCenter.x, y: backCenterY + 12 },
    [0.43, 0.17, 0.13],
    backTopM - 0.07,
    materials.officeFabric,
  );
  for (const [index, sideX] of [chairCenter.x - 255, chairCenter.x + 255].entries()) {
    const armPost = texturedBox(
      context.scene,
      `${fitout.id} · CHAIR · nastaviteľná podrúčka ${index + 1}`,
      { x: sideX, y: chairCenter.y - 15 },
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
      { x: sideX, y: chairCenter.y - 75 },
      seatM + 0.245,
      0.31,
      0.04,
      new Vector3(0, 0, 1),
      [1, 0.65, 1],
      materials.officeFabric,
    );
    armPad.rotation.z = 0.02;
  }

  // Frameless marker board spans the solid north-wall bay, left after entering
  // and directly opposite the desk. Its generous corner gap keeps EAST-01
  // visually independent instead of pinning the board to the window reveal.
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

  // One restrained linear ceiling luminaire follows the rotated desk axis.
  const ceilingHousing = texturedBox(
    context.scene,
    `${fitout.id} · LIGHT · čierny lineárny stropný profil`,
    { x: (deskRect.x0 + deskRect.x1) / 2, y: (deskRect.y0 + deskRect.y1) / 2 },
    1260,
    58,
    0.035,
    2.565,
    1,
  );
  finish(context, ceilingHousing, materials.fireplace, { shadow: true });
  const ceilingDiffuser = texturedBox(
    context.scene,
    `${fitout.id} · LIGHT · teplý súvislý difúzor`,
    { x: (deskRect.x0 + deskRect.x1) / 2, y: (deskRect.y0 + deskRect.y1) / 2 },
    1210,
    34,
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
export function buildLivingDiningFitout(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
) {
  const fitout = LIVING_DINING_FITOUT;

  // ---- handleless TV wall: warm greige storage, a stone media bay and oak
  // floating console. It starts 329 mm after the flue pier and stops before
  // the rear gable lining, so the fireplace and fixed glazing remain legible.
  const wall = fitout.tvWall.rectMm;
  const [bayY0, bayY1] = fitout.tvWall.centralBayYmm;
  const bayCenterY = (bayY0 + bayY1) / 2;
  const towerRanges = [
    [wall.y0, bayY0, "pri krbe"],
    [bayY1, wall.y1, "pri zadnom okne"],
  ] as const;
  for (const [towerY0, towerY1, label] of towerRanges) {
    const tower = texturedBox(
      context.scene,
      `LIVING-103-TV-WALL · vysoká bezúchytková skriňa ${label}`,
      { x: (wall.x0 + wall.x1) / 2, y: (towerY0 + towerY1) / 2 },
      wall.x1 - wall.x0,
      towerY1 - towerY0,
      fitout.tvWall.heightMm * MM_TO_M,
      0,
      1.2,
    );
    finish(context, tower, materials.livingCabinet, { shadow: true, pickable: true });
    for (const levelM of [0.86, 1.72]) {
      const joint = texturedBox(
        context.scene,
        `LIVING-103-TV-WALL · tieňová škára skrine ${label}`,
        { x: wall.x1 + 7, y: (towerY0 + towerY1) / 2 },
        14,
        towerY1 - towerY0 - 34,
        0.009,
        levelM,
        1,
      );
      finish(context, joint, materials.fireplace);
    }
  }
  const mediaPanel = texturedBox(
    context.scene,
    "LIVING-103-TV-WALL · veľkoformátový greige kamenný panel",
    { x: wall.x1 + 12, y: bayCenterY },
    24,
    bayY1 - bayY0 - 70,
    2.18,
    0.18,
    1.6,
  );
  finish(context, mediaPanel, materials.mediaPanel, { shadow: true, pickable: true });
  const bridge = texturedBox(
    context.scene,
    "LIVING-103-TV-WALL · horný úložný most",
    { x: (wall.x0 + wall.x1) / 2, y: bayCenterY },
    wall.x1 - wall.x0,
    bayY1 - bayY0,
    0.27,
    2.33,
    1.2,
  );
  finish(context, bridge, materials.livingCabinet, { shadow: true, pickable: true });
  const console = texturedBox(
    context.scene,
    "LIVING-103-TV-WALL · plávajúca dubová mediálna skrinka",
    { x: (wall.x0 + wall.x1) / 2 + 8, y: bayCenterY },
    wall.x1 - wall.x0 - 16,
    bayY1 - bayY0 - 170,
    0.28,
    0.17,
    1.2,
  );
  finish(context, console, materials.kitchenFront, { shadow: true, pickable: true });
  const consoleShadow = texturedBox(
    context.scene,
    "LIVING-103-TV-WALL · tieň pod plávajúcou skrinkou",
    { x: wall.x1 + 13, y: bayCenterY },
    18,
    bayY1 - bayY0 - 230,
    0.025,
    0.14,
    1,
  );
  finish(context, consoleShadow, materials.fireplace);

  const tv = fitout.tvWall.tv;
  const tvFrame = texturedBox(
    context.scene,
    `LIVING-103-TV-WALL · ${tv.diagonalIn}-palcový televízor · rám`,
    { x: wall.x1 + 42, y: bayCenterY },
    58,
    tv.widthMm + 28,
    (tv.heightMm + 28) * MM_TO_M,
    (tv.centerElevationMm - tv.heightMm / 2 - 14) * MM_TO_M,
    1,
  );
  finish(context, tvFrame, materials.fireplace, { shadow: true, pickable: true });
  const tvScreen = texturedBox(
    context.scene,
    `LIVING-103-TV-WALL · ${tv.diagonalIn}-palcový televízor · čierne sklo`,
    { x: wall.x1 + 73, y: bayCenterY },
    8,
    tv.widthMm,
    tv.heightMm * MM_TO_M,
    (tv.centerElevationMm - tv.heightMm / 2) * MM_TO_M,
    1,
  );
  finish(context, tvScreen, materials.tvScreen, { pickable: true });
  const soundbar = texturedBox(
    context.scene,
    "LIVING-103-TV-WALL · subtílny soundbar",
    { x: wall.x1 + 83, y: bayCenterY },
    48,
    1120,
    0.065,
    0.49,
    1,
  );
  finish(context, soundbar, materials.fireplace, { shadow: true });
  for (const [index, edgeY] of [bayY0 + 24, bayY1 - 24].entries()) {
    const led = texturedBox(
      context.scene,
      `LIVING-103-TV-WALL · 2700 K vertikálna LED ${index + 1}`,
      { x: wall.x1 + 31, y: edgeY },
      20,
      24,
      2.08,
      0.2,
      1,
    );
    finish(context, led, materials.warmLight);
  }
  navigationGuard(context, materials, "LIVING-103-TV-WALL · hladký navigačný obrys", wall);

  // ---- soft low-profile L sofa, oriented to the TV. The chaise terminates on
  // the solid gable section east of the fixed pane rather than obscuring it.
  const sofa = fitout.sofa;
  const rugRect: RectMm = { x0: 22520, y0: 15580, x1: 27190, y1: 18880 };
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
  for (const [rect, label] of [
    [sofa.mainRectMm, "hlavný modul"],
    [sofa.chaiseRectMm, "ležadlo"],
  ] as const) {
    const base = texturedBox(
      context.scene,
      `LIVING-103-SOFA-L · ${label} · skrytá nízka báza`,
      rectCenter(rect),
      rect.x1 - rect.x0,
      rect.y1 - rect.y0,
      0.18,
      0.08,
      1,
    );
    finish(context, base, materials.upholstery, { shadow: true, pickable: true });
  }
  const backRail = texturedBox(
    context.scene,
    "LIVING-103-SOFA-L · mäkké chrbtové jadro",
    { x: sofa.mainRectMm.x1 - 150, y: (sofa.mainRectMm.y0 + sofa.mainRectMm.y1) / 2 },
    300,
    sofa.mainRectMm.y1 - sofa.mainRectMm.y0 - 180,
    0.55,
    0.23,
    1,
  );
  finish(context, backRail, materials.upholstery, { shadow: true, pickable: true });
  for (const [index, centerY] of [16320, 17220].entries()) {
    softCapsule(
      context,
      `LIVING-103-SOFA-L · sedací vankúš ${index + 1}`,
      { x: 26490, y: centerY },
      0.355,
      0.82,
      0.22,
      new Vector3(0, 0, 1),
      [2.18, 0.4, 1],
      materials.upholstery,
    );
  }
  softCapsule(
    context,
    "LIVING-103-SOFA-L · predĺžený vankúš ležadla",
    { x: 25830, y: 18210 },
    0.36,
    2.5,
    0.22,
    new Vector3(1, 0, 0),
    [1, 0.42, 1.72],
    materials.upholstery,
  );
  for (const [index, centerY] of [16320, 17220, 18200].entries()) {
    const backCushion = softCapsule(
      context,
      `LIVING-103-SOFA-L · chrbtový vankúš ${index + 1}`,
      { x: 27060, y: centerY },
      0.67,
      index === 2 ? 0.84 : 0.79,
      0.2,
      new Vector3(0, 0, 1),
      [0.7, 1.5, 1],
      materials.upholstery,
    );
    backCushion.rotation.z = -0.055;
  }
  softCapsule(
    context,
    "LIVING-103-SOFA-L · južná mäkká podrúčka",
    { x: 26580, y: sofa.mainRectMm.y0 + 95 },
    0.44,
    1.02,
    0.18,
    new Vector3(1, 0, 0),
    [1, 1.34, 0.58],
    materials.upholstery,
  );
  softCapsule(
    context,
    "LIVING-103-SOFA-L · zadná mäkká podrúčka ležadla",
    { x: 25860, y: sofa.chaiseRectMm.y1 - 95 },
    0.43,
    2.5,
    0.18,
    new Vector3(1, 0, 0),
    [1, 1.28, 0.58],
    materials.upholstery,
  );
  softEllipsoid(
    context,
    "LIVING-103-SOFA-L · akcentový vankúš koňak",
    { x: 26820, y: 17740 },
    [0.24, 0.5, 0.48],
    0.66,
    materials.accentFabric,
  );
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

  // Two quiet sculptural tables sit completely inside the conversation zone.
  for (const [index, spec] of [
    { center: { x: 24380, y: 16680 }, diameter: 1.15, scaleX: 1.12, scaleZ: 0.7, top: 0.34 },
    { center: { x: 25020, y: 17140 }, diameter: 0.78, scaleX: 1.05, scaleZ: 0.76, top: 0.42 },
  ].entries()) {
    const top = CreateCylinder(
      `LIVING-103-SOFA-L · oválny konferenčný stolík ${index + 1}`,
      { height: 0.045, diameter: spec.diameter, tessellation: 48 },
      context.scene,
    );
    top.position.set(xM(spec.center.x), spec.top, zM(spec.center.y));
    top.scaling.set(spec.scaleX, 1, spec.scaleZ);
    finish(context, top, index === 0 ? materials.worktop : materials.livingCabinet, {
      shadow: true,
      pickable: true,
    });
    const pedestal = CreateCylinder(
      `LIVING-103-SOFA-L · podnož konferenčného stolíka ${index + 1}`,
      { height: spec.top - 0.025, diameter: index === 0 ? 0.34 : 0.24, tessellation: 32 },
      context.scene,
    );
    pedestal.position.set(xM(spec.center.x), (spec.top - 0.025) / 2, zM(spec.center.y));
    finish(context, pedestal, materials.brushedBrass, { shadow: true });
  }
  navigationGuard(context, materials, "LIVING-103-SOFA-L · navigačný obrys stolíkov", {
    x0: 23700,
    y0: 16220,
    x1: 25480,
    y1: 17580,
  });

  // ---- compact four-seat dining zone: a classic rectangular oak table with
  // a proper apron, four tapered legs, framed chairs and one calm pendant.
  const dining = fitout.dining;
  const tableHeightM = dining.tableHeightMm * MM_TO_M;
  const topThicknessM = 0.052;
  const tableTop = texturedBox(
    context.scene,
    "LIVING-103-DINING · klasický dubový stôl · doska",
    dining.tableCenterMm,
    dining.tableLengthMm,
    dining.tableDepthMm,
    topThicknessM,
    tableHeightM - topThicknessM,
    1.2,
  );
  finish(context, tableTop, materials.kitchenFront, { shadow: true, pickable: true });

  const apronHeightM = 0.13;
  const apronElevationM = tableHeightM - topThicknessM - apronHeightM;
  for (const [index, yOffsetMm] of [-1, 1].entries()) {
    const rail = texturedBox(
      context.scene,
      `LIVING-103-DINING · dubová lubová výstuha pozdĺžna ${index + 1}`,
      {
        x: dining.tableCenterMm.x,
        y: dining.tableCenterMm.y + yOffsetMm * (dining.tableDepthMm / 2 - 62),
      },
      dining.tableLengthMm - 160,
      48,
      apronHeightM,
      apronElevationM,
      1,
    );
    finish(context, rail, materials.kitchenFront, { shadow: true });
  }
  for (const [index, xOffsetMm] of [-1, 1].entries()) {
    const rail = texturedBox(
      context.scene,
      `LIVING-103-DINING · dubová lubová výstuha priečna ${index + 1}`,
      {
        x: dining.tableCenterMm.x + xOffsetMm * (dining.tableLengthMm / 2 - 62),
        y: dining.tableCenterMm.y,
      },
      48,
      dining.tableDepthMm - 160,
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
        xM(dining.tableCenterMm.x + xSide * (dining.tableLengthMm / 2 - 105)),
        tableLegHeightM / 2,
        zM(dining.tableCenterMm.y + ySide * (dining.tableDepthMm / 2 - 105)),
      );
      leg.rotation.y = Math.PI / 4;
      finish(context, leg, materials.kitchenFront, { shadow: true });
    }
  }
  navigationGuard(context, materials, "LIVING-103-DINING · hladký navigačný obrys stola", {
    x0: dining.tableCenterMm.x - dining.tableLengthMm / 2,
    x1: dining.tableCenterMm.x + dining.tableLengthMm / 2,
    y0: dining.tableCenterMm.y - dining.tableDepthMm / 2,
    y1: dining.tableCenterMm.y + dining.tableDepthMm / 2,
  });

  const facingVector = (facing: (typeof dining.chairs)[number]["facing"]) => {
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
  };
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

  const livingRoom = INTERIOR_ROOMS.find((room) => room.id === "ROOM-1-03")!;
  const lampElevationM = 2.08;
  const ceilingM = ceilingElevationMm(livingRoom, dining.tableCenterMm.x) * MM_TO_M - 0.07;
  const cordHeightM = Math.max(0.15, ceilingM - lampElevationM - 0.08);
  const cord = CreateCylinder(
    "LIVING-103-DINING · centrálne závesné svietidlo · kábel",
    { height: cordHeightM, diameter: 0.012, tessellation: 12 },
    context.scene,
  );
  cord.position.set(
    xM(dining.tableCenterMm.x),
    lampElevationM + 0.08 + cordHeightM / 2,
    zM(dining.tableCenterMm.y),
  );
  finish(context, cord, materials.fireplace);
  const shade = CreateCylinder(
    "LIVING-103-DINING · centrálne závesné svietidlo · klasické tienidlo",
    { height: 0.22, diameterTop: 0.18, diameterBottom: 0.48, tessellation: 48 },
    context.scene,
  );
  shade.position.set(xM(dining.tableCenterMm.x), lampElevationM, zM(dining.tableCenterMm.y));
  finish(context, shade, materials.brushedBrass, { shadow: true });
  const diffuser = CreateSphere(
    "LIVING-103-DINING · centrálne závesné svietidlo · 2700 K difúzor",
    { diameter: 0.2, segments: 24 },
    context.scene,
  );
  diffuser.position.set(
    xM(dining.tableCenterMm.x),
    lampElevationM - 0.095,
    zM(dining.tableCenterMm.y),
  );
  finish(context, diffuser, materials.warmLight, { shadow: true });
  const light = new PointLight(
    "LIVING-103-DINING · centrálne závesné svietidlo · svetlo",
    new Vector3(xM(dining.tableCenterMm.x), lampElevationM - 0.15, zM(dining.tableCenterMm.y)),
    context.scene,
  );
  light.diffuse = Color3.FromHexString("#ffd2a0");
  light.specular = Color3.FromHexString("#8f7254");
  light.intensity = 0.25;
  light.range = 3.2;
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
  buildFloorsAndCeilings(context, materials);
  buildWalls(context, materials);
  buildLivingFireplace(context, materials);
  for (const door of INTERIOR_DOORS) buildDoor(context, materials, door);
  buildKitchen(context, materials);
  buildTechnicalHeatingFitout(context, materials);
  buildWcFitout(context, materials);
  buildBathroomFitout(context, materials);
  buildEnsuiteBathroomFitout(context, materials);
  buildHallwayBuiltInWardrobes(context, materials);
  buildEntryFitout(context, materials);
  buildBedroomFitout(context, materials);
  buildChildrensBedroomFitouts(context, materials);
  buildOfficeFitout(context, materials);
  buildLivingDiningFitout(context, materials);
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
