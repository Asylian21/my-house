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
import { Mesh } from "@babylonjs/core/Meshes/mesh";
import type { Scene } from "@babylonjs/core/scene";
import earcut from "earcut";

import {
  BATHROOM_FITOUT,
  FIREPLACE_PIER,
  INTERIOR_DOORS,
  INTERIOR_ROOMS,
  INTERIOR_WALLS,
  INTERIOR_WALL_HEIGHT_MM,
  KITCHEN_RUN,
  LIVING_DINING_FITOUT,
  TECHNICAL_HEATING_FITOUT,
  WC_FITOUT,
  WING_RIDGE_XMM,
  ceilingElevationMm,
  roomBoundsMm,
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
  readonly tankJacket: PBRMaterial;
  readonly copperPipe: PBRMaterial;
  readonly sanitaryCeramic: PBRMaterial;
  readonly mirrorGlass: PBRMaterial;
  readonly showerGlass: PBRMaterial;
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
  const boilerEnamel = pbr(scene, "real-technical-boiler-enamel", "#67241f", 0.38, 0.22);
  boilerEnamel.clearCoat.isEnabled = true;
  boilerEnamel.clearCoat.intensity = 0.35;
  boilerEnamel.clearCoat.roughness = 0.24;
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
    tankJacket,
    copperPipe,
    sanitaryCeramic,
    mirrorGlass,
    showerGlass,
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

  // The pier is the plastered flue (HOUSE.chimneys[0]); its finish box sits
  // 10 mm proud of the concrete column so the interior reads as plaster.
  const pier = texturedBox(
    context.scene,
    `${FIREPLACE_PIER.id} · omietnutý komínový pilier`,
    rectCenter(FIREPLACE_PIER.rectMm),
    FIREPLACE_PIER.rectMm.x1 - FIREPLACE_PIER.rectMm.x0 + 20,
    FIREPLACE_PIER.rectMm.y1 - FIREPLACE_PIER.rectMm.y0 + 20,
    heightM,
    0,
    2.4,
  );
  finish(context, pier, materials.plaster, { collide: true, shadow: true, pickable: true });

  // Compact stove leaning on the west wall right beside the terrace door
  // (22. 8. 2026 revision): 450 × 450 × 1 000 steel body, glass front, flue
  // pipe rising and turning into the pier.
  const stoveX0 = FIREPLACE_PIER.rectMm.x0 + 10;
  const stoveY0 = 13900;
  const stove = texturedBox(
    context.scene,
    "Krbové kachle vedľa dverí na terasu · ilustračný koncept",
    { x: stoveX0 + 225, y: stoveY0 + 225 },
    450,
    450,
    1.0,
    0.06,
    1,
  );
  finish(context, stove, materials.fireplace, { collide: true, shadow: true });
  const stoveGlass = texturedBox(
    context.scene,
    "Krbové kachle · presklené dvierka",
    { x: stoveX0 + 450 + 6, y: stoveY0 + 225 },
    10,
    320,
    0.4,
    0.36,
    1,
  );
  finish(context, stoveGlass, context.glassFrame);
  for (const [index, legY] of [stoveY0 + 60, stoveY0 + 390].entries()) {
    const leg = texturedBox(
      context.scene,
      `Krbové kachle · nožička ${index + 1}`,
      { x: stoveX0 + 225, y: legY },
      380,
      30,
      0.06,
      0,
      1,
    );
    finish(context, leg, materials.fireplace);
  }
  const riser = CreateCylinder(
    "Krbové kachle · dymovod zvislý",
    { height: 0.55, diameter: 0.15, tessellation: 24 },
    context.scene,
  );
  riser.position.set(xM(stoveX0 + 225), 1.06 + 0.275, zM(stoveY0 + 225));
  finish(context, riser, materials.fireplace);
  const runLengthMm = FIREPLACE_PIER.rectMm.y0 + 60 - (stoveY0 + 225);
  const run = CreateCylinder(
    "Krbové kachle · dymovod do komína",
    { height: runLengthMm * MM_TO_M, diameter: 0.15, tessellation: 24 },
    context.scene,
  );
  run.position.set(xM(stoveX0 + 225), 1.06 + 0.55, zM(stoveY0 + 225 + runLengthMm / 2));
  run.rotation.x = Math.PI / 2;
  finish(context, run, materials.fireplace);
  const elbow = CreateCylinder(
    "Krbové kachle · koleno dymovodu",
    { height: 0.16, diameter: 0.17, tessellation: 24 },
    context.scene,
  );
  elbow.position.set(xM(stoveX0 + 225), 1.06 + 0.55, zM(stoveY0 + 225));
  finish(context, elbow, materials.fireplace);
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
  for (const xMm of [pen.x0 + 900, pen.x0 + 1800, pen.x0 + 3100, pen.x0 + 4000]) {
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
  for (const xMm of [pen.x0 + 450, pen.x0 + 2450, pen.x0 + 3550, pen.x0 + 4375]) {
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
    { x: k.hobCenterXmm, y: (pen.y0 + pen.y1) / 2 },
    900,
    500,
    0.08,
    1.6,
    1,
  );
  finish(context, hood, materials.steel, { shadow: true });
  const duct = texturedBox(
    context.scene,
    `${k.id} · komín odsávača`,
    { x: k.hobCenterXmm, y: (pen.y0 + pen.y1) / 2 },
    300,
    300,
    1.1,
    1.68,
    1,
  );
  finish(context, duct, materials.steel);
}

/**
 * Heating equipment in room 1.07. The bodies and reserved service geometry
 * come from `TECHNICAL_HEATING_FITOUT`; detailed fittings are intentionally
 * generic until a manufacturer and the professional heating design are known.
 */
function buildTechnicalHeatingFitout(
  context: InteriorBuildContext,
  materials: InteriorMaterials,
) {
  const fitout = TECHNICAL_HEATING_FITOUT;
  const boiler = fitout.boiler;
  const boilerRect = boiler.footprintMm;
  const boilerCenter = rectCenter(boilerRect);
  const boilerHeightM = boiler.heightMm * MM_TO_M;

  const boilerPlinth = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-GASIFICATION-BOILER · oceľový sokel`,
    boilerCenter,
    boilerRect.x1 - boilerRect.x0 - 90,
    boilerRect.y1 - boilerRect.y0 - 90,
    0.1,
    0,
    1,
  );
  finish(context, boilerPlinth, materials.fireplace, { shadow: true });
  const boilerBody = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-GASIFICATION-BOILER · drevosplyňovací kotol`,
    boilerCenter,
    boilerRect.x1 - boilerRect.x0,
    boilerRect.y1 - boilerRect.y0,
    boilerHeightM - 0.1,
    0.1,
    1,
  );
  finish(context, boilerBody, materials.boilerEnamel, {
    collide: true,
    shadow: true,
    pickable: true,
  });

  const frontYmm = boilerRect.y1 + 8;
  const frontWidthMm = boilerRect.x1 - boilerRect.x0 - 90;
  const loadingDoor = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-GASIFICATION-BOILER · prikladacie dvierka`,
    { x: boilerCenter.x, y: frontYmm },
    frontWidthMm,
    18,
    0.48,
    0.72,
    1,
  );
  finish(context, loadingDoor, materials.fireplace, { shadow: true, pickable: true });
  const combustionDoor = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-GASIFICATION-BOILER · spaľovacie a popolníkové dvierka`,
    { x: boilerCenter.x, y: frontYmm },
    frontWidthMm,
    18,
    0.35,
    0.21,
    1,
  );
  finish(context, combustionDoor, materials.fireplace, { shadow: true, pickable: true });
  const flameWindow = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-GASIFICATION-BOILER · kontrolné sklo spaľovania`,
    { x: boilerCenter.x, y: frontYmm + 12 },
    250,
    8,
    0.15,
    0.88,
    1,
  );
  finish(context, flameWindow, materials.blackGlass);
  const ember = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-GASIFICATION-BOILER · žiara spaľovacej komory`,
    { x: boilerCenter.x, y: frontYmm + 17 },
    205,
    4,
    0.1,
    0.905,
    1,
  );
  finish(context, ember, materials.warmLight);
  barHandle(
    context,
    materials,
    `${fitout.id} · WOOD-GASIFICATION-BOILER · madlo prikladacích dvierok`,
    { x: boilerCenter.x, y: frontYmm + 24 },
    460,
    true,
    1.12,
  );
  barHandle(
    context,
    materials,
    `${fitout.id} · WOOD-GASIFICATION-BOILER · madlo popolníka`,
    { x: boilerCenter.x, y: frontYmm + 24 },
    380,
    true,
    0.48,
  );
  const controlPanel = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-GASIFICATION-BOILER · regulácia`,
    { x: boilerCenter.x, y: frontYmm + 10 },
    frontWidthMm,
    12,
    0.16,
    1.25,
    1,
  );
  finish(context, controlPanel, materials.fireplace);
  const display = texturedBox(
    context.scene,
    `${fitout.id} · WOOD-GASIFICATION-BOILER · displej regulácie`,
    { x: boilerCenter.x - 175, y: frontYmm + 18 },
    185,
    6,
    0.07,
    1.295,
    1,
  );
  finish(context, display, materials.blackGlass);
  for (const xMm of [boilerRect.x0 + 45, boilerRect.x1 - 45]) {
    for (const elevationM of [0.34, 0.92]) {
      const hinge = CreateCylinder(
        `${fitout.id} · WOOD-GASIFICATION-BOILER · pánt`,
        { height: 0.12, diameter: 0.026, tessellation: 16 },
        context.scene,
      );
      hinge.position.set(xM(xMm), elevationM, zM(frontYmm + 24));
      finish(context, hinge, materials.steel);
    }
  }
  const flueCollar = CreateCylinder(
    `${fitout.id} · WOOD-GASIFICATION-BOILER · dymovodné hrdlo`,
    { height: 0.1, diameter: 0.25, tessellation: 32 },
    context.scene,
  );
  flueCollar.position.set(xM(boilerCenter.x), boilerHeightM + 0.05, zM(boilerRect.y0 + 165));
  finish(context, flueCollar, materials.fireplace);
  const flueStub = CreateCylinder(
    `${fitout.id} · WOOD-GASIFICATION-BOILER · koncept napojenia dymovodu Ø${boiler.flueOutletDiameterMm}`,
    { height: 0.36, diameter: boiler.flueOutletDiameterMm * MM_TO_M, tessellation: 32 },
    context.scene,
  );
  flueStub.position.set(xM(boilerCenter.x), boilerHeightM + 0.23, zM(boilerRect.y0 + 165));
  finish(context, flueStub, materials.fireplace);

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
 * Compact fitout for the L-shaped bathroom/laundry 1.05. The east recess is
 * kept as a single flush walk-in shower; all dry functions are lifted from
 * the floor or stacked vertically so the room reads as one calm open space.
 */
function buildBathroomFitout(context: InteriorBuildContext, materials: InteriorMaterials) {
  const fitout = BATHROOM_FITOUT;
  const shower = fitout.shower;

  const showerFloor = texturedBox(
    context.scene,
    `${fitout.id} · WALK-IN-1400 · bezprahová sprchová plocha`,
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
    `${fitout.id} · WALK-IN-1400 · lineárny nerezový žľab`,
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
      `${fitout.id} · WALK-IN-1400 · štrbina žľabu ${slot + 1}`,
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
    `${fitout.id} · WALK-IN-1400 · číre bezpečnostné sklo`,
    rectCenter(panel),
    panel.x1 - panel.x0,
    panel.y1 - panel.y0,
    2.1,
    0,
    1,
  );
  finish(context, glass, materials.showerGlass, { shadow: true, pickable: true });
  for (const [index, xMm] of [panel.x0, panel.x1].entries()) {
    const post = texturedBox(
      context.scene,
      `${fitout.id} · WALK-IN-1400 · čierny profil ${index + 1}`,
      { x: xMm, y: (panel.y0 + panel.y1) / 2 },
      18,
      22,
      2.12,
      0,
      1,
    );
    finish(context, post, materials.fireplace, { shadow: true });
  }
  const topRail = texturedBox(
    context.scene,
    `${fitout.id} · WALK-IN-1400 · horný stabilizačný profil`,
    rectCenter(panel),
    panel.x1 - panel.x0,
    20,
    0.018,
    2.1,
    1,
  );
  finish(context, topRail, materials.fireplace, { shadow: true });

  // Shower controls sit on the solid south wall outside the high east window.
  const showerColumnXmm = 27020;
  const showerWallYmm = 6680;
  const riser = CreateCylinder(
    `${fitout.id} · WALK-IN-1400 · sprchová tyč`,
    { height: 1.55, diameter: 0.026, tessellation: 20 },
    context.scene,
  );
  riser.position.set(xM(showerColumnXmm), 1.13, zM(showerWallYmm));
  finish(context, riser, materials.steel, { shadow: true });
  const overheadArm = CreateCylinder(
    `${fitout.id} · WALK-IN-1400 · rameno hlavovej sprchy`,
    { height: 0.32, diameter: 0.024, tessellation: 20 },
    context.scene,
  );
  overheadArm.rotation.x = Math.PI / 2;
  overheadArm.position.set(xM(showerColumnXmm), 2.04, zM(showerWallYmm + 150));
  finish(context, overheadArm, materials.steel, { shadow: true });
  const rainHead = CreateCylinder(
    `${fitout.id} · WALK-IN-1400 · hlavová sprcha 240`,
    { height: 0.025, diameter: 0.24, tessellation: 36 },
    context.scene,
  );
  rainHead.position.set(xM(showerColumnXmm), 2.035, zM(showerWallYmm + 300));
  finish(context, rainHead, materials.steel, { shadow: true, pickable: true });
  const mixer = texturedBox(
    context.scene,
    `${fitout.id} · WALK-IN-1400 · termostatická batéria`,
    { x: showerColumnXmm, y: showerWallYmm - 3 },
    260,
    35,
    0.075,
    1.03,
    1,
  );
  finish(context, mixer, materials.steel, { pickable: true });

  const vanity = fitout.vanity;
  const vanityCenter = rectCenter(vanity.footprintMm);
  const vanityCabinet = texturedBox(
    context.scene,
    `${fitout.id} · FLOATING-VANITY-1000 · bezúchytková dubová skrinka`,
    { x: vanityCenter.x + 8, y: vanityCenter.y },
    vanity.footprintMm.x1 - vanity.footprintMm.x0 - 16,
    vanity.footprintMm.y1 - vanity.footprintMm.y0 - 40,
    0.42,
    0.37,
    1,
  );
  finish(context, vanityCabinet, materials.kitchenFront, {
    shadow: true,
    pickable: true,
  });
  const vanityJoint = texturedBox(
    context.scene,
    `${fitout.id} · FLOATING-VANITY-1000 · deliaca škára zásuviek`,
    { x: vanity.footprintMm.x1 + 3, y: vanityCenter.y },
    7,
    vanity.footprintMm.y1 - vanity.footprintMm.y0 - 70,
    0.005,
    0.575,
    1,
  );
  finish(context, vanityJoint, materials.fireplace);
  const vanityTop = texturedBox(
    context.scene,
    `${fitout.id} · FLOATING-VANITY-1000 · tenká kamenná doska`,
    vanityCenter,
    vanity.footprintMm.x1 - vanity.footprintMm.x0,
    vanity.footprintMm.y1 - vanity.footprintMm.y0,
    0.035,
    0.79,
    1,
  );
  finish(context, vanityTop, materials.worktop, { shadow: true });
  softEllipsoid(
    context,
    `${fitout.id} · FLOATING-VANITY-1000 · keramické umývadlo`,
    { x: vanityCenter.x + 35, y: vanityCenter.y },
    [0.37, 0.15, 0.64],
    vanity.rimElevationMm * MM_TO_M - 0.015,
    materials.sanitaryCeramic,
  );
  softEllipsoid(
    context,
    `${fitout.id} · FLOATING-VANITY-1000 · vnútorná misa`,
    { x: vanityCenter.x + 58, y: vanityCenter.y },
    [0.25, 0.025, 0.45],
    vanity.rimElevationMm * MM_TO_M + 0.02,
    materials.mirrorGlass,
  );
  const basinDrain = CreateCylinder(
    `${fitout.id} · FLOATING-VANITY-1000 · odtok`,
    { height: 0.008, diameter: 0.052, tessellation: 24 },
    context.scene,
  );
  basinDrain.position.set(
    xM(vanityCenter.x + 76),
    vanity.rimElevationMm * MM_TO_M + 0.035,
    zM(vanityCenter.y),
  );
  finish(context, basinDrain, materials.steel);
  const tapRiser = CreateCylinder(
    `${fitout.id} · FLOATING-VANITY-1000 · vysoká batéria`,
    { height: 0.25, diameter: 0.03, tessellation: 20 },
    context.scene,
  );
  tapRiser.position.set(xM(vanity.footprintMm.x0 + 110), 0.965, zM(vanityCenter.y));
  finish(context, tapRiser, materials.steel, { shadow: true });
  const tapSpout = CreateCylinder(
    `${fitout.id} · FLOATING-VANITY-1000 · výtok batérie`,
    { height: 0.19, diameter: 0.023, tessellation: 20 },
    context.scene,
  );
  tapSpout.rotation.z = Math.PI / 2;
  tapSpout.position.set(xM(vanity.footprintMm.x0 + 190), 1.075, zM(vanityCenter.y));
  finish(context, tapSpout, materials.steel, { shadow: true });
  const mirrorFrame = texturedBox(
    context.scene,
    `${fitout.id} · FLOATING-VANITY-1000 · zrkadlo s nepriamym LED`,
    { x: vanity.footprintMm.x0 + 8, y: vanityCenter.y },
    16,
    910,
    0.9,
    1.05,
    1,
  );
  finish(context, mirrorFrame, materials.warmLight, { shadow: true });
  const mirror = texturedBox(
    context.scene,
    `${fitout.id} · FLOATING-VANITY-1000 · zrkadlová plocha`,
    { x: vanity.footprintMm.x0 + 18, y: vanityCenter.y },
    9,
    880,
    0.86,
    1.07,
    1,
  );
  finish(context, mirror, materials.mirrorGlass, { pickable: true });

  const tower = fitout.laundryTower;
  const towerCenter = rectCenter(tower.footprintMm);
  const towerCabinet = texturedBox(
    context.scene,
    `${fitout.id} · LAUNDRY-TOWER-650 · odvetraná vysoká skriňa`,
    towerCenter,
    tower.footprintMm.x1 - tower.footprintMm.x0,
    tower.footprintMm.y1 - tower.footprintMm.y0,
    tower.heightMm * MM_TO_M,
    0,
    1,
  );
  finish(context, towerCabinet, materials.kitchenFront, {
    shadow: true,
    pickable: true,
  });
  const applianceLevels = [0.65, 1.48] as const;
  for (const [index, elevationM] of applianceLevels.entries()) {
    const applianceFront = texturedBox(
      context.scene,
      `${fitout.id} · LAUNDRY-TOWER-650 · ${index === 0 ? "práčka" : "sušička"}`,
      { x: towerCenter.x, y: tower.footprintMm.y0 - 5 },
      570,
      20,
      0.7,
      elevationM - 0.35,
      1,
    );
    finish(context, applianceFront, materials.kitchenUpper, { pickable: true });
    const doorRim = CreateCylinder(
      `${fitout.id} · LAUNDRY-TOWER-650 · rám dvierok ${index + 1}`,
      { height: 0.035, diameter: 0.46, tessellation: 40 },
      context.scene,
    );
    doorRim.rotation.x = Math.PI / 2;
    doorRim.position.set(xM(towerCenter.x), elevationM, zM(tower.footprintMm.y0 - 22));
    finish(context, doorRim, materials.steel, { shadow: true });
    const doorGlass = CreateCylinder(
      `${fitout.id} · LAUNDRY-TOWER-650 · tmavé sklo dvierok ${index + 1}`,
      { height: 0.042, diameter: 0.38, tessellation: 40 },
      context.scene,
    );
    doorGlass.rotation.x = Math.PI / 2;
    doorGlass.position.set(xM(towerCenter.x), elevationM, zM(tower.footprintMm.y0 - 38));
    finish(context, doorGlass, materials.blackGlass, { pickable: true });
    const controls = texturedBox(
      context.scene,
      `${fitout.id} · LAUNDRY-TOWER-650 · ovládací panel ${index + 1}`,
      { x: towerCenter.x + 155, y: tower.footprintMm.y0 - 31 },
      140,
      14,
      0.055,
      elevationM + 0.24,
      1,
    );
    finish(context, controls, materials.blackGlass, { pickable: true });
  }
  for (let vent = 0; vent < 5; vent += 1) {
    const ventSlot = texturedBox(
      context.scene,
      `${fitout.id} · LAUNDRY-TOWER-650 · horné odvetranie ${vent + 1}`,
      { x: towerCenter.x - 120 + vent * 60, y: tower.footprintMm.y0 - 31 },
      38,
      14,
      0.012,
      2.22,
      1,
    );
    finish(context, ventSlot, materials.fireplace);
  }

  navigationGuard(
    context,
    materials,
    `${fitout.id} · FLOATING-VANITY-1000 · hladký navigačný obrys`,
    vanity.footprintMm,
  );
  navigationGuard(
    context,
    materials,
    `${fitout.id} · LAUNDRY-TOWER-650 · hladký navigačný obrys`,
    tower.footprintMm,
  );
  navigationGuard(
    context,
    materials,
    `${fitout.id} · WALK-IN-1400 · navigačný obrys skla`,
    { x0: panel.x0, y0: panel.y0 - 10, x1: panel.x1, y1: panel.y1 + 10 },
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
      alongX ? 470 : 460,
      alongX ? 460 : 470,
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
  for (const door of INTERIOR_DOORS) buildDoor(context, materials, door);
  buildKitchen(context, materials);
  buildTechnicalHeatingFitout(context, materials);
  buildWcFitout(context, materials);
  buildBathroomFitout(context, materials);
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
