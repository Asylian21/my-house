import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { Texture } from "@babylonjs/core/Materials/Textures/texture";
import { Color3 } from "@babylonjs/core/Maths/math.color";
import { Quaternion, Vector3, Vector4 } from "@babylonjs/core/Maths/math.vector";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { CreateBox } from "@babylonjs/core/Meshes/Builders/boxBuilder.pure";
import { CreateCylinder } from "@babylonjs/core/Meshes/Builders/cylinderBuilder.pure";
import { ExtrudePolygon } from "@babylonjs/core/Meshes/Builders/polygonBuilder.pure";
import { Mesh } from "@babylonjs/core/Meshes/mesh";
import type { Scene } from "@babylonjs/core/scene";
import earcut from "earcut";

import {
  FIREPLACE_PIER,
  INTERIOR_DOORS,
  INTERIOR_ROOMS,
  INTERIOR_WALLS,
  INTERIOR_WALL_HEIGHT_MM,
  KITCHEN_RUN,
  WING_RIDGE_XMM,
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
  const tall = k.tallUnitRectMm;

  // ---- back run: carcass, 100 mm recessed plinth, drawer fronts, worktop
  const runStart = tall.x1;
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
      barHandle(context, materials, `${k.id} · úchytka zásuvky`, { x: (x0 + x1) / 2, y: run.y1 + 14 }, x1 - x0 - 160, true, level);
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
  // Extractor hood above the hob position is on the peninsula; here a flat
  // cooker hood is not needed. Tall column: fridge-freezer + oven stack.
  const tallUnit = texturedBox(
    context.scene,
    `${k.id} · vysoká skriňa · chladnička a rúra`,
    rectCenter(tall),
    tall.x1 - tall.x0,
    tall.y1 - tall.y0 - 20,
    2.24,
    0,
    1.2,
  );
  finish(context, tallUnit, materials.kitchenFront, { collide: true, shadow: true, pickable: true });
  const oven = texturedBox(
    context.scene,
    `${k.id} · vstavaná rúra`,
    { x: (tall.x0 + tall.x1) / 2, y: tall.y1 - 4 },
    560,
    10,
    0.595,
    0.9,
    1,
  );
  finish(context, oven, materials.blackGlass);
  barHandle(context, materials, `${k.id} · madlo rúry`, { x: (tall.x0 + tall.x1) / 2, y: tall.y1 + 24 }, 480, true, 1.44);
  for (const level of [0.45, 1.9]) {
    const vertical = texturedBox(
      context.scene,
      `${k.id} · zvislá úchytka`,
      { x: tall.x1 - 40, y: tall.y1 + 14 },
      12,
      12,
      0.3,
      level - 0.15,
      1,
    );
    finish(context, vertical, materials.fireplace);
  }
  for (const level of [1.5, 0.9]) {
    const joint = texturedBox(
      context.scene,
      `${k.id} · škára vysokej skrine`,
      { x: (tall.x0 + tall.x1) / 2, y: tall.y1 + 2 },
      tall.x1 - tall.x0 - 10,
      4,
      0.004,
      level,
      1,
    );
    finish(context, joint, materials.fireplace);
  }

  // ---- peninsula with the hob (D1.1.002 symbol) and a breakfast overhang
  const pen = k.peninsulaRectMm;
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
  for (const xMm of [pen.x0 + 450, pen.x0 + 1350, pen.x0 + 2450, pen.x0 + 3550, pen.x0 + 4375]) {
    barHandle(context, materials, `${k.id} · úchytka polostrova`, { x: xMm, y: pen.y0 - 14 }, 300, true, 0.8);
  }
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
  // Three bar stools on the breakfast side.
  for (const xMm of [pen.x0 + 3150, pen.x0 + 3750, pen.x0 + 4350]) {
    const seat = CreateCylinder(`${k.id} · barová stolička`, { height: 0.04, diameter: 0.36, tessellation: 24 }, context.scene);
    seat.position.set(xM(xMm), 0.68, zM(pen.y1 + 420));
    finish(context, seat, materials.fireplace, { shadow: true });
    const stem = CreateCylinder(`${k.id} · noha stoličky`, { height: 0.66, diameter: 0.04, tessellation: 12 }, context.scene);
    stem.position.set(xM(xMm), 0.33, zM(pen.y1 + 420));
    finish(context, stem, materials.steel);
    const foot = CreateCylinder(`${k.id} · podstava stoličky`, { height: 0.012, diameter: 0.4, tessellation: 24 }, context.scene);
    foot.position.set(xM(xMm), 0.006, zM(pen.y1 + 420));
    finish(context, foot, materials.steel);
  }
  // Treat the three stools as one rounded-body obstacle. This preserves their
  // visual footprint while avoiding nine tiny seat/stem/base colliders that
  // would catch a novice walking past the breakfast side.
  const stoolNavigationGuard = texturedBox(
    context.scene,
    `${k.id} · navigačný obrys barových stoličiek`,
    { x: pen.x0 + 3750, y: pen.y1 + 420 },
    1600,
    400,
    6,
    -2,
    1,
  );
  finish(context, stoolNavigationGuard, materials.kitchenFront, { collide: true });
  stoolNavigationGuard.isVisible = false;
  stoolNavigationGuard.metadata = {
    ...(stoolNavigationGuard.metadata ?? {}),
    walkCollisionOnly: true,
  };
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
