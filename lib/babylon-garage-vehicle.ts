import type { Material } from "@babylonjs/core/Materials/material";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { Color3 } from "@babylonjs/core/Maths/math.color";
import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { CreateBox } from "@babylonjs/core/Meshes/Builders/boxBuilder.pure";
import { CreateCylinder } from "@babylonjs/core/Meshes/Builders/cylinderBuilder.pure";
import { CreateSphere } from "@babylonjs/core/Meshes/Builders/sphereBuilder.pure";
import { CreateTorus } from "@babylonjs/core/Meshes/Builders/torusBuilder.pure";
import { CreateTube } from "@babylonjs/core/Meshes/Builders/tubeBuilder.pure";
import { Mesh } from "@babylonjs/core/Meshes/mesh";
import { VertexData } from "@babylonjs/core/Meshes/mesh.vertexData";
import { TransformNode } from "@babylonjs/core/Meshes/transformNode";
import type { Scene } from "@babylonjs/core/scene";

import { GARAGE_VEHICLE } from "./twin-garage";
import {
  GARAGE_SUPERB_AXLES_M,
  GARAGE_SUPERB_BODY_STATIONS,
  GARAGE_SUPERB_CABIN_STATIONS,
  GARAGE_SUPERB_HALF_TRACKS_M,
  GARAGE_SUPERB_LOWER_BODY_SEGMENTS,
  GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM,
  GARAGE_SUPERB_ROOF_STATIONS,
  GARAGE_SUPERB_SIDE_WINDOWS,
  GARAGE_SUPERB_VISUAL_LENGTH_SCALE,
  GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M,
  GARAGE_SUPERB_WHEEL_M,
  garageSuperbLongitudinalM,
  vehicleLoftGeometry,
  type VehicleLoftStation,
  type VehicleProfilePoint,
} from "./twin-superb-combi";

export interface GarageVehicleBuildHooks {
  readonly realisticOnly: (mesh: AbstractMesh) => void;
  readonly castShadow: (mesh: AbstractMesh) => void;
  readonly register: (mesh: AbstractMesh) => void;
}

export interface GarageVehicleVisual {
  readonly root: TransformNode;
  readonly wheelSpins: readonly TransformNode[];
  readonly frontSteering: readonly TransformNode[];
  readonly headlightMaterial: PBRMaterial;
  readonly brakeMaterial: PBRMaterial;
}

function vehiclePbrMaterial(
  scene: Scene,
  name: string,
  color: string,
  roughness: number,
  metallic = 0,
  alpha = 1,
) {
  const material = new PBRMaterial(name, scene);
  material.albedoColor = Color3.FromHexString(color);
  material.roughness = roughness;
  material.metallic = metallic;
  material.alpha = alpha;
  material.environmentIntensity = 1;
  material.enableSpecularAntiAliasing = true;
  if (alpha < 1) {
    material.transparencyMode = PBRMaterial.PBRMATERIAL_ALPHABLEND;
    material.useAlphaFromAlbedoTexture = false;
  }
  return material;
}

function createLoftMesh(
  scene: Scene,
  name: string,
  stations: readonly VehicleLoftStation[],
  material: Material,
) {
  const geometry = vehicleLoftGeometry(stations);
  const positions = [...geometry.positions];
  const indices = [...geometry.indices];
  const normals = new Array(positions.length).fill(0);
  VertexData.ComputeNormals(positions, indices, normals);
  const data = new VertexData();
  data.positions = positions;
  data.indices = indices;
  data.normals = normals;
  data.uvs = [...geometry.uvs];
  const mesh = new Mesh(name, scene);
  data.applyToMesh(mesh);
  mesh.material = material;
  return mesh;
}

function createPanelMesh(
  scene: Scene,
  name: string,
  points: readonly Vector3[],
  material: Material,
) {
  if (points.length < 3) throw new Error("Vehicle panel needs three points.");
  const positions = points.flatMap((point) => [point.x, point.y, point.z]);
  const indices: number[] = [];
  for (let index = 1; index < points.length - 1; index += 1) {
    indices.push(0, index, index + 1);
  }
  const normals = new Array(positions.length).fill(0);
  VertexData.ComputeNormals(positions, indices, normals);
  const data = new VertexData();
  data.positions = positions;
  data.indices = indices;
  data.normals = normals;
  const mesh = new Mesh(name, scene);
  data.applyToMesh(mesh);
  mesh.material = material;
  return mesh;
}

function sidePanelPoints(
  profile: readonly VehicleProfilePoint[],
  side: -1 | 1,
) {
  return profile.map(({ x, y }) => {
    const rise = Math.min(1, Math.max(0, (y - 0.85) / (1.47 - 0.85)));
    const sideZ = 0.89 + (0.72 - 0.89) * rise;
    return new Vector3(x, y, side * sideZ);
  });
}

export function buildGarageSuperbVehicle(
  scene: Scene,
  hooks: GarageVehicleBuildHooks,
): GarageVehicleVisual {
  const vehicle = GARAGE_VEHICLE;
  const lx = garageSuperbLongitudinalM;
  const root = new TransformNode(
    `${vehicle.label} · automatické parkovanie`,
    scene,
  );
  root.metadata = {
    vehicleId: vehicle.id,
    vehicleModel: vehicle.label,
    vehicleGeneration: "SUPERB-IV-COMBI",
    parkingRoomId: vehicle.roomId,
    productionDimensionsMm: GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM,
    visualLengthScale: GARAGE_SUPERB_VISUAL_LENGTH_SCALE,
    visualReference: "client-supplied-2024-plus-superb-combi-photos-2026-08-25",
    referenceViews: ["side-profile", "front-three-quarter"],
    bodyConstruction: "split-wheel-arch-shell",
  };
  root.setEnabled(false);

  const paint = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · šalviovo-olivová metalíza",
    "#89917a",
    0.22,
    0.66,
  );
  paint.clearCoat.isEnabled = true;
  paint.clearCoat.intensity = 0.95;
  paint.clearCoat.roughness = 0.1;
  paint.environmentIntensity = 0.92;
  // The end caps remain visible from close interior-garage inspection even on
  // graphics drivers that reverse the procedural cap winding.
  paint.backFaceCulling = false;

  const glass = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · tónované bezpečnostné sklo",
    "#071820",
    0.075,
    0.02,
    0.82,
  );
  glass.backFaceCulling = false;
  glass.indexOfRefraction = 1.52;
  glass.environmentIntensity = 1.35;
  glass.clearCoat.isEnabled = true;
  glass.clearCoat.intensity = 0.88;
  glass.clearCoat.roughness = 0.04;
  const glassEnvelope = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · zakrivený podklad presklenia",
    "#071417",
    0.08,
    0.03,
    0.26,
  );
  glassEnvelope.backFaceCulling = false;
  glassEnvelope.indexOfRefraction = 1.52;
  glassEnvelope.environmentIntensity = 1.25;

  const pianoBlack = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · lesklá čierna",
    "#090d0f",
    0.2,
    0.48,
  );
  pianoBlack.backFaceCulling = false;
  const interior = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · interiér Suite Black",
    "#171a1c",
    0.68,
    0.02,
  );
  const tire = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · 235/40 R19 pneumatiky",
    "#111214",
    0.9,
    0.01,
  );
  const alloy = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · 19-palcové disky Veritate",
    "#343b3e",
    0.22,
    0.92,
  );
  alloy.backFaceCulling = false;
  const machinedAlloy = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · brúsené plochy diskov",
    "#d4dadd",
    0.17,
    0.96,
  );
  machinedAlloy.backFaceCulling = false;
  const brightChrome = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · svetlý chróm",
    "#c4cccd",
    0.12,
    0.96,
  );
  brightChrome.backFaceCulling = false;
  const darkChrome = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · Unique Dark Chrome",
    "#4f595e",
    0.18,
    0.92,
  );
  const headlight = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · Matrix LED Crystallinium",
    "#6f929f",
    0.08,
    0.08,
  );
  headlight.emissiveColor = Color3.FromHexString("#b9e6ff").scale(0.28);
  const brake = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · kryštalické zadné LED svetlá",
    "#8d111a",
    0.14,
    0.12,
  );
  brake.emissiveColor = Color3.FromHexString("#c41421").scale(0.46);
  const reflector = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · zadné odrazky",
    "#a62428",
    0.24,
    0.05,
  );
  const plate = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · evidenčné tabuľky",
    "#f4f5ef",
    0.54,
  );

  const registerVisual = <T extends AbstractMesh>(mesh: T, shadow = true) => {
    mesh.parent = root;
    mesh.isPickable = false;
    mesh.receiveShadows = shadow;
    if (shadow) hooks.castShadow(mesh);
    hooks.realisticOnly(mesh);
    hooks.register(mesh);
    return mesh;
  };

  const addBox = (
    name: string,
    size: { readonly x: number; readonly y: number; readonly z: number },
    position: { readonly x: number; readonly y: number; readonly z: number },
    material: Material,
    shadow = true,
  ) => {
    const mesh = CreateBox(
      `${vehicle.label} · ${name}`,
      { width: size.x, height: size.y, depth: size.z },
      scene,
    );
    mesh.position.set(position.x, position.y, position.z);
    mesh.material = material;
    return registerVisual(mesh, shadow);
  };

  const addTube = (
    name: string,
    path: readonly Vector3[],
    radius: number,
    material: Material,
    shadow = false,
    tessellation = 10,
  ) => {
    const mesh = CreateTube(
      `${vehicle.label} · ${name}`,
      {
        path: [...path],
        radius,
        tessellation,
        cap: Mesh.CAP_ALL,
      },
      scene,
    );
    mesh.material = material;
    return registerVisual(mesh, shadow);
  };

  const body = createLoftMesh(
    scene,
    `${vehicle.label} · lisovaná karoséria Modern Solid`,
    GARAGE_SUPERB_BODY_STATIONS,
    paint,
  );
  body.metadata = {
    vehiclePart: "body-shell",
    bodyWidthMm: GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.bodyWidth,
  };
  registerVisual(body);

  for (const [index, stations] of GARAGE_SUPERB_LOWER_BODY_SEGMENTS.entries()) {
    const lowerBody = createLoftMesh(
      scene,
      `${vehicle.label} · delený spodný diel karosérie ${index + 1}`,
      stations,
      paint,
    );
    lowerBody.metadata = {
      vehiclePart: "lower-body-shell",
      segmentIndex: index,
    };
    registerVisual(lowerBody);
  }

  const curvedGlasshouse = createLoftMesh(
    scene,
    `${vehicle.label} · zakrivený skleník kabíny`,
    GARAGE_SUPERB_CABIN_STATIONS,
    glassEnvelope,
  );
  curvedGlasshouse.metadata = { vehiclePart: "glasshouse-envelope" };
  registerVisual(curvedGlasshouse, false);

  const roof = createLoftMesh(
    scene,
    `${vehicle.label} · predĺžená lakovaná strecha Combi`,
    GARAGE_SUPERB_ROOF_STATIONS,
    paint,
  );
  roof.metadata = { vehiclePart: "painted-roof" };
  registerVisual(roof);

  addBox(
    "aerodynamicky zakrytý podvozok",
    { x: lx(4.22), y: 0.08, z: 1.64 },
    { x: lx(-0.02), y: 0.18, z: 0 },
    pianoBlack,
  );

  // A low dark interior floor, seats and dashboard sit behind independently
  // modeled windows. The glasshouse remains optically open instead of becoming
  // the previous opaque rectangular bubble.
  addBox(
    "podlaha kabíny",
    { x: lx(2.74), y: 0.1, z: 1.34 },
    { x: lx(-0.34), y: 0.88, z: 0 },
    interior,
    false,
  );
  addBox(
    "prístrojová doska",
    { x: lx(0.38), y: 0.09, z: 1.18 },
    { x: lx(0.72), y: 0.955, z: 0 },
    interior,
    false,
  );
  for (const [row, x] of [
    ["predný", 0.24],
    ["zadný", -0.72],
  ] as const) {
    for (const side of [-1, 1] as const) {
      addBox(
        `${row} sedák ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: lx(0.47), y: 0.14, z: 0.48 },
        { x: lx(x), y: 0.86, z: side * 0.37 },
        interior,
        false,
      );
      addBox(
        `${row} operadlo ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: lx(0.18), y: 0.48, z: 0.46 },
        { x: lx(x - 0.13), y: 1.08, z: side * 0.37 },
        interior,
        false,
      );
      const headrest = CreateSphere(
        `${vehicle.label} · ${row} hlavová opierka ${side < 0 ? "vľavo" : "vpravo"}`,
        { diameter: 1, segments: 16 },
        scene,
      );
      headrest.position.set(lx(x - 0.16), 1.36, side * 0.37);
      headrest.scaling.set(lx(0.13), 0.11, 0.18);
      headrest.material = interior;
      registerVisual(headrest, false);
    }
  }

  for (const side of [-1, 1] as const) {
    for (const window of GARAGE_SUPERB_SIDE_WINDOWS) {
      const pane = createPanelMesh(
        scene,
        `${vehicle.label} · ${window.id} bočné sklo ${side < 0 ? "vľavo" : "vpravo"}`,
        sidePanelPoints(window.points, side),
        glass,
      );
      pane.metadata = { vehiclePart: "side-window", windowId: window.id };
      registerVisual(pane, false);
      const points = sidePanelPoints(window.points, side).map(
        (point) => new Vector3(point.x, point.y, point.z + side * 0.004),
      );
      const frame = addTube(
        `${window.id} rám okna ${side < 0 ? "vľavo" : "vpravo"}`,
        [...points, points[0]],
        0.007,
        pianoBlack,
      );
      frame.metadata = { vehiclePart: "window-frame", windowId: window.id };
    }

    const glazingOutline = sidePanelPoints(
      [
        { x: lx(-1.91), y: 0.855 },
        { x: lx(-1.88), y: 1.075 },
        { x: lx(-1.54), y: 1.425 },
        { x: lx(-1.12), y: 1.448 },
        { x: lx(0.06), y: 1.458 },
        { x: lx(0.64), y: 1.415 },
        { x: lx(1.08), y: 0.852 },
      ],
      side,
    );
    const chromeOutline = addTube(
      `súvislý chrómový obvod presklenia ${side < 0 ? "vľavo" : "vpravo"}`,
      glazingOutline,
      0.008,
      brightChrome,
    );
    chromeOutline.metadata = { vehiclePart: "window-chrome-surround" };

    for (const [pillarId, lower, upper] of [
      ["B", { x: lx(0), y: 0.858 }, { x: lx(0.03), y: 1.458 }],
      ["C", { x: lx(-1.2), y: 0.858 }, { x: lx(-1.1), y: 1.45 }],
    ] as const) {
      const pillar = addTube(
        `${pillarId}-stĺpik ${side < 0 ? "vľavo" : "vpravo"}`,
        sidePanelPoints([lower, upper], side).map(
          (point) => new Vector3(point.x, point.y, point.z + side * 0.009),
        ),
        pillarId === "B" ? 0.021 : 0.017,
        pianoBlack,
      );
      pillar.metadata = { vehiclePart: "window-pillar", pillarId };
    }

    const characterLine = addTube(
      `tornado línia ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(lx(-2.08), 0.82, side * 0.9),
        new Vector3(lx(-1.35), 0.855, side * 0.925),
        new Vector3(lx(-0.2), 0.86, side * 0.928),
        new Vector3(lx(0.95), 0.855, side * 0.925),
        new Vector3(lx(1.72), 0.81, side * 0.895),
      ],
      0.004,
      darkChrome,
    );
    characterLine.metadata = { vehiclePart: "body-character-line" };
    const windowSill = addTube(
      `spodná chrómová línia okien ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(lx(-1.91), 0.855, side * 0.895),
        new Vector3(lx(-0.55), 0.86, side * 0.895),
        new Vector3(lx(1.08), 0.852, side * 0.89),
      ],
      0.009,
      brightChrome,
    );
    windowSill.metadata = { vehiclePart: "window-chrome-sill" };

    for (const [index, x] of [-0.72, 0.28].entries()) {
      const handle = addBox(
        `zapustená kľučka ${index + 1} ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: lx(0.18), y: 0.022, z: 0.018 },
        { x: lx(x), y: 0.78, z: side * 0.932 },
        brightChrome,
        false,
      );
      handle.metadata = { vehiclePart: "door-handle" };
    }
    for (const x of [-1.94, -1.2, 0.02, 1.1]) {
      const seam = addTube(
        `škára dverí ${x.toFixed(2)} ${side < 0 ? "vľavo" : "vpravo"}`,
        [
          new Vector3(lx(x), 0.34, side * 0.929),
          new Vector3(lx(x), 0.852, side * 0.929),
        ],
        0.003,
        pianoBlack,
      );
      seam.metadata = { vehiclePart: "door-seam" };
    }

    const mirrorStem = addBox(
      `držiak spätného zrkadla ${side < 0 ? "vľavo" : "vpravo"}`,
      { x: lx(0.13), y: 0.05, z: 0.16 },
      { x: lx(0.86), y: 0.985, z: side * 0.88 },
      pianoBlack,
    );
    mirrorStem.rotation.z = -0.1;
    mirrorStem.metadata = { vehiclePart: "mirror-stem" };
    const mirror = CreateSphere(
      `${vehicle.label} · aerodynamické spätné zrkadlo ${side < 0 ? "vľavo" : "vpravo"}`,
      { diameter: 1, segments: 24 },
      scene,
    );
    mirror.position.set(lx(0.86), 1.01, side * 0.985);
    mirror.scaling.set(lx(0.17), 0.075, 0.12);
    mirror.material = paint;
    mirror.metadata = { vehiclePart: "external-mirror" };
    registerVisual(mirror);

    const rail = addTube(
      `strešná lyžina ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(lx(-1.68), 1.468, side * 0.59),
        new Vector3(lx(-0.75), 1.486, side * 0.61),
        new Vector3(lx(0.48), 1.478, side * 0.6),
      ],
      0.009,
      darkChrome,
      true,
    );
    rail.metadata = { vehiclePart: "roof-rail" };
  }

  const windshield = createPanelMesh(
    scene,
    `${vehicle.label} · akustické čelné sklo`,
    [
      new Vector3(lx(1.15), 0.86, -0.81),
      new Vector3(lx(1.15), 0.86, 0.81),
      new Vector3(lx(0.64), 1.42, 0.66),
      new Vector3(lx(0.64), 1.42, -0.66),
    ],
    glass,
  );
  windshield.metadata = { vehiclePart: "windshield" };
  registerVisual(windshield, false);
  const rearGlass = createPanelMesh(
    scene,
    `${vehicle.label} · vyhrievané sklo piatych dverí`,
    [
      new Vector3(lx(-1.96), 0.86, 0.8),
      new Vector3(lx(-1.96), 0.86, -0.8),
      new Vector3(lx(-1.73), 1.39, -0.66),
      new Vector3(lx(-1.73), 1.39, 0.66),
    ],
    glass,
  );
  rearGlass.metadata = { vehiclePart: "rear-window" };
  registerVisual(rearGlass, false);

  const spoiler = addBox(
    "predĺžený strešný spojler",
    { x: lx(0.34), y: 0.038, z: 1.38 },
    { x: lx(-2.05), y: 1.41, z: 0 },
    paint,
  );
  spoiler.rotation.z = 0.035;
  spoiler.metadata = { vehiclePart: "roof-spoiler" };
  const spoilerUnderside = addBox(
    "čierna spodná hrana spojlera",
    { x: lx(0.27), y: 0.016, z: 1.3 },
    { x: lx(-2.08), y: 1.39, z: 0 },
    pianoBlack,
    false,
  );
  spoilerUnderside.metadata = { vehiclePart: "roof-spoiler-underside" };
  for (const side of [-1, 1] as const) {
    const fin = addBox(
      `bočný finlet spojlera ${side < 0 ? "vľavo" : "vpravo"}`,
      { x: lx(0.22), y: 0.05, z: 0.025 },
      { x: lx(-2.03), y: 1.385, z: side * 0.67 },
      pianoBlack,
    );
    fin.rotation.z = 0.08;
  }

  const halfLengthM = vehicle.dimensionsMm.length / 2_000;
  const grille = createPanelMesh(
    scene,
    `${vehicle.label} · výplň širokej osemuholníkovej prednej masky`,
    [
      new Vector3(halfLengthM + 0.006, 0.7, -0.62),
      new Vector3(halfLengthM + 0.006, 0.75, -0.52),
      new Vector3(halfLengthM + 0.006, 0.75, 0.52),
      new Vector3(halfLengthM + 0.006, 0.7, 0.62),
      new Vector3(halfLengthM + 0.006, 0.5, 0.62),
      new Vector3(halfLengthM + 0.006, 0.47, 0.52),
      new Vector3(halfLengthM + 0.006, 0.47, -0.52),
      new Vector3(halfLengthM + 0.006, 0.5, -0.62),
    ],
    pianoBlack,
  );
  grille.metadata = { vehiclePart: "front-grille" };
  registerVisual(grille, false);
  const grillePath = [
    new Vector3(halfLengthM + 0.014, 0.7, -0.62),
    new Vector3(halfLengthM + 0.014, 0.75, -0.52),
    new Vector3(halfLengthM + 0.014, 0.75, 0.52),
    new Vector3(halfLengthM + 0.014, 0.7, 0.62),
    new Vector3(halfLengthM + 0.014, 0.5, 0.62),
    new Vector3(halfLengthM + 0.014, 0.47, 0.52),
    new Vector3(halfLengthM + 0.014, 0.47, -0.52),
    new Vector3(halfLengthM + 0.014, 0.5, -0.62),
    new Vector3(halfLengthM + 0.014, 0.7, -0.62),
  ];
  const grilleFrame = addTube(
    "svetlý chrómový rám osemuholníkovej masky",
    grillePath,
    0.01,
    brightChrome,
  );
  grilleFrame.metadata = { vehiclePart: "front-grille-frame" };
  for (let index = -7; index <= 7; index += 1) {
    const slat = addBox(
      `zvislá lamela masky ${index + 8}`,
      { x: 0.014, y: 0.205 - Math.abs(index) * 0.004, z: 0.012 },
      { x: halfLengthM + 0.012, y: 0.61, z: index * 0.073 },
      darkChrome,
      false,
    );
    slat.metadata = { vehiclePart: "front-grille-slat" };
  }

  for (const side of [-1, 1] as const) {
    const headlamp = createPanelMesh(
      scene,
      `${vehicle.label} · zapustené teleso Matrix LED ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(halfLengthM + 0.006, 0.815, side * 0.34),
        new Vector3(halfLengthM - 0.075, 0.82, side * 0.86),
        new Vector3(halfLengthM - 0.06, 0.72, side * 0.8),
        new Vector3(halfLengthM + 0.006, 0.725, side * 0.38),
      ],
      pianoBlack,
    );
    headlamp.metadata = { vehiclePart: "headlamp" };
    registerVisual(headlamp, false);
    for (let moduleIndex = 0; moduleIndex < 4; moduleIndex += 1) {
      const moduleZ = 0.43 + moduleIndex * 0.115;
      const ledModule = addBox(
        `Matrix LED modul ${moduleIndex + 1} ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: 0.012, y: 0.028, z: 0.085 },
        {
          x: halfLengthM + 0.014 - moduleIndex * 0.014,
          y: 0.77,
          z: side * moduleZ,
        },
        headlight,
        false,
      );
      ledModule.metadata = { vehiclePart: "headlamp-module" };
    }
    const drl = addTube(
      `dvojsegmentové LED denné svetlo ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(halfLengthM + 0.019, 0.735, side * 0.38),
        new Vector3(halfLengthM + 0.012, 0.735, side * 0.68),
        new Vector3(halfLengthM - 0.045, 0.755, side * 0.81),
      ],
      0.006,
      headlight,
    );
    drl.metadata = { vehiclePart: "drl" };

    const sideIntake = createPanelMesh(
      scene,
      `${vehicle.label} · vysoká bočná vzduchová clona ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(halfLengthM + 0.004, 0.54, side * 0.68),
        new Vector3(halfLengthM - 0.025, 0.52, side * 0.83),
        new Vector3(halfLengthM - 0.015, 0.25, side * 0.8),
        new Vector3(halfLengthM + 0.004, 0.28, side * 0.67),
      ],
      pianoBlack,
    );
    sideIntake.metadata = { vehiclePart: "side-intake" };
    registerVisual(sideIntake, false);
    const intakeBlade = addTube(
      `chrómová L lišta vzduchovej clony ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(halfLengthM + 0.014, 0.53, side * 0.67),
        new Vector3(halfLengthM + 0.014, 0.27, side * 0.67),
        new Vector3(halfLengthM - 0.008, 0.24, side * 0.8),
      ],
      0.007,
      brightChrome,
    );
    intakeBlade.metadata = { vehiclePart: "side-intake-trim" };
  }

  const lowerIntake = createPanelMesh(
    scene,
    `${vehicle.label} · celoplošný spodný nasávací otvor`,
    [
      new Vector3(halfLengthM + 0.007, 0.4, -0.66),
      new Vector3(halfLengthM + 0.007, 0.4, 0.66),
      new Vector3(halfLengthM + 0.007, 0.25, 0.62),
      new Vector3(halfLengthM + 0.007, 0.25, -0.62),
    ],
    pianoBlack,
  );
  lowerIntake.metadata = { vehiclePart: "lower-intake" };
  registerVisual(lowerIntake, false);
  const lowerLip = addTube(
    "spodná aerodynamická hrana",
    [
      new Vector3(halfLengthM + 0.012, 0.235, -0.65),
      new Vector3(halfLengthM + 0.012, 0.225, 0),
      new Vector3(halfLengthM + 0.012, 0.235, 0.65),
    ],
    0.008,
    darkChrome,
  );
  lowerLip.metadata = { vehiclePart: "front-lower-lip" };

  const leftHoodCrease = addTube(
    "lis kapoty vľavo",
    [new Vector3(lx(1.12), 0.925, -0.36), new Vector3(lx(2.22), 0.795, -0.25)],
    0.004,
    darkChrome,
  );
  leftHoodCrease.metadata = { vehiclePart: "hood-crease" };
  const rightHoodCrease = addTube(
    "lis kapoty vpravo",
    [new Vector3(lx(1.12), 0.925, 0.36), new Vector3(lx(2.22), 0.795, 0.25)],
    0.004,
    darkChrome,
  );
  rightHoodCrease.metadata = { vehiclePart: "hood-crease" };

  const badge = CreateCylinder(
    `${vehicle.label} · emblém na čele kapoty`,
    { height: 0.014, diameter: 0.105, tessellation: 32 },
    scene,
  );
  badge.position.set(halfLengthM + 0.013, 0.855, 0);
  badge.rotation.z = Math.PI / 2;
  badge.material = darkChrome;
  badge.metadata = { vehiclePart: "bonnet-badge" };
  registerVisual(badge, false);

  const frontPlate = addBox(
    "predná evidenčná tabuľka",
    { x: 0.018, y: 0.12, z: 0.52 },
    { x: halfLengthM + 0.014, y: 0.33, z: 0 },
    plate,
    false,
  );
  frontPlate.metadata = { vehiclePart: "front-plate" };

  const rearDiffuser = createPanelMesh(
    scene,
    `${vehicle.label} · nízky lichobežníkový zadný difúzor`,
    [
      new Vector3(-halfLengthM - 0.006, 0.37, -0.7),
      new Vector3(-halfLengthM - 0.006, 0.37, 0.7),
      new Vector3(-halfLengthM - 0.006, 0.22, 0.62),
      new Vector3(-halfLengthM - 0.006, 0.22, -0.62),
    ],
    pianoBlack,
  );
  rearDiffuser.metadata = { vehiclePart: "rear-diffuser" };
  registerVisual(rearDiffuser);
  for (const side of [-1, 1] as const) {
    const rearLampHousing = createPanelMesh(
      scene,
      `${vehicle.label} · štíhle teleso zadného svetla ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(-halfLengthM - 0.008, 0.845, side * 0.28),
        new Vector3(-halfLengthM - 0.008, 0.845, side * 0.82),
        new Vector3(-halfLengthM - 0.008, 0.71, side * 0.78),
        new Vector3(-halfLengthM - 0.008, 0.72, side * 0.32),
      ],
      pianoBlack,
    );
    rearLampHousing.metadata = { vehiclePart: "rear-lamp" };
    registerVisual(rearLampHousing, false);
    const rearLightGuide = addTube(
      `kryštalické zadné svetlo C ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(-halfLengthM - 0.01, 0.825, side * 0.31),
        new Vector3(-halfLengthM - 0.01, 0.828, side * 0.79),
        new Vector3(-halfLengthM - 0.01, 0.745, side * 0.8),
        new Vector3(-halfLengthM - 0.01, 0.725, side * 0.55),
      ],
      0.007,
      brake,
    );
    rearLightGuide.metadata = { vehiclePart: "rear-light-guide" };

    const wrapLamp = createPanelMesh(
      scene,
      `${vehicle.label} · bočné wrap-around zadné svetlo ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(-halfLengthM + 0.015, 0.82, side * 0.835),
        new Vector3(lx(-2.05), 0.8, side * 0.91),
        new Vector3(lx(-2.04), 0.73, side * 0.9),
        new Vector3(-halfLengthM + 0.02, 0.73, side * 0.81),
      ],
      brake,
    );
    wrapLamp.metadata = { vehiclePart: "rear-wrap-lamp" };
    registerVisual(wrapLamp, false);

    const rearReflector = addBox(
      `zadná odrazka ${side < 0 ? "vľavo" : "vpravo"}`,
      { x: 0.02, y: 0.035, z: 0.28 },
      { x: -halfLengthM - 0.008, y: 0.34, z: side * 0.62 },
      reflector,
      false,
    );
    rearReflector.metadata = { vehiclePart: "rear-reflector" };
  }
  const rearPlate = addBox(
    "zadná evidenčná tabuľka",
    { x: 0.018, y: 0.12, z: 0.52 },
    { x: -halfLengthM - 0.008, y: 0.52, z: 0 },
    plate,
    false,
  );
  rearPlate.metadata = { vehiclePart: "rear-plate" };
  const rearWordmark = addTube(
    "subtílna stredová lišta piatych dverí",
    [
      new Vector3(-halfLengthM - 0.01, 0.65, -0.26),
      new Vector3(-halfLengthM - 0.01, 0.65, 0.26),
    ],
    0.006,
    darkChrome,
  );
  rearWordmark.metadata = { vehiclePart: "rear-wordmark-line" };

  const wheelSpins: TransformNode[] = [];
  const frontSteering: TransformNode[] = [];
  for (const [axle, axleX, halfTrack] of [
    ["zadné", GARAGE_SUPERB_AXLES_M.rearX, GARAGE_SUPERB_HALF_TRACKS_M.rear],
    ["predné", GARAGE_SUPERB_AXLES_M.frontX, GARAGE_SUPERB_HALF_TRACKS_M.front],
  ] as const) {
    for (const side of [-1, 1] as const) {
      const sideName = side < 0 ? "ľavé" : "pravé";
      const steering = new TransformNode(
        `${vehicle.label} · ${axle} ${sideName} koleso`,
        scene,
      );
      steering.parent = root;
      steering.position.set(axleX, GARAGE_SUPERB_WHEEL_M.centerY, side * halfTrack);
      if (axle === "predné") frontSteering.push(steering);

      const spin = new TransformNode(`${steering.name} · rotácia`, scene);
      spin.parent = steering;
      wheelSpins.push(spin);

      const registerWheelPart = <T extends AbstractMesh>(
        mesh: T,
        parent: TransformNode,
        shadow = false,
      ) => {
        mesh.parent = parent;
        mesh.isPickable = false;
        mesh.receiveShadows = shadow;
        if (shadow) hooks.castShadow(mesh);
        hooks.realisticOnly(mesh);
        hooks.register(mesh);
        return mesh;
      };

      const wheelWell = CreateCylinder(
        `${steering.name} · tmavý vnútorný podbeh`,
        { height: 0.025, diameter: GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M * 1.86, tessellation: 48 },
        scene,
      );
      wheelWell.position.set(
        axleX,
        GARAGE_SUPERB_WHEEL_M.centerY,
        side * 0.88,
      );
      wheelWell.rotation.x = Math.PI / 2;
      wheelWell.material = pianoBlack;
      wheelWell.metadata = { vehiclePart: "wheel-well" };
      registerVisual(wheelWell, false);

      const tireSectionDiameter =
        (GARAGE_SUPERB_WHEEL_M.outerDiameter -
          GARAGE_SUPERB_WHEEL_M.rimDiameter) /
        2;
      const tireMajorDiameter =
        GARAGE_SUPERB_WHEEL_M.outerDiameter - tireSectionDiameter;
      const tireMesh = CreateTorus(
        `${steering.name} · pneumatika 235/40 R19`,
        {
          diameter: tireMajorDiameter,
          thickness: tireSectionDiameter,
          tessellation: 64,
        },
        scene,
      );
      tireMesh.rotation.x = Math.PI / 2;
      tireMesh.scaling.y =
        GARAGE_SUPERB_WHEEL_M.tireWidth / tireSectionDiameter;
      tireMesh.material = tire;
      tireMesh.metadata = { vehiclePart: "tire" };
      registerWheelPart(tireMesh, spin, true);

      const brakeDisc = CreateCylinder(
        `${steering.name} · ventilovaný brzdový kotúč`,
        { height: 0.024, diameter: 0.34, tessellation: 40 },
        scene,
      );
      brakeDisc.position.z = side * 0.085;
      brakeDisc.rotation.x = Math.PI / 2;
      brakeDisc.material = darkChrome;
      brakeDisc.metadata = { vehiclePart: "brake-disc" };
      registerWheelPart(brakeDisc, spin);

      const caliper = CreateBox(
        `${steering.name} · brzdový strmeň`,
        { width: 0.055, height: 0.14, depth: 0.035 },
        scene,
      );
      caliper.position.set(-0.145, 0, side * 0.082);
      caliper.material = reflector;
      caliper.metadata = { vehiclePart: "brake-caliper" };
      registerWheelPart(caliper, steering);

      const rim = CreateCylinder(
        `${steering.name} · tmavý barrel disku Veritate 8J × 19`,
        { height: 0.035, diameter: 0.438, tessellation: 48 },
        scene,
      );
      rim.position.z = side * 0.1;
      rim.rotation.x = Math.PI / 2;
      rim.material = alloy;
      rim.metadata = { vehiclePart: "rim" };
      registerWheelPart(rim, spin);

      const rimLip = CreateTorus(
        `${steering.name} · brúsený vonkajší lem disku`,
        { diameter: GARAGE_SUPERB_WHEEL_M.rimDiameter - 0.018, thickness: 0.018, tessellation: 56 },
        scene,
      );
      rimLip.position.z = side * 0.122;
      rimLip.rotation.x = Math.PI / 2;
      rimLip.material = machinedAlloy;
      rimLip.metadata = { vehiclePart: "rim-lip" };
      registerWheelPart(rimLip, spin);

      const polarPoint = (radius: number, angle: number, z: number) =>
        new Vector3(
          Math.cos(angle) * radius,
          Math.sin(angle) * radius,
          z,
        );
      for (let bladeIndex = 0; bladeIndex < 5; bladeIndex += 1) {
        const angle = (bladeIndex / 5) * Math.PI * 2 + 0.12;
        const insert = createPanelMesh(
          scene,
          `${steering.name} · tmavá aero vložka ${bladeIndex + 1}`,
          [
            polarPoint(0.065, angle - 0.22, side * 0.126),
            polarPoint(0.074, angle + 0.18, side * 0.126),
            polarPoint(0.215, angle + 0.34, side * 0.126),
            polarPoint(0.222, angle - 0.02, side * 0.126),
          ],
          pianoBlack,
        );
        insert.metadata = { vehiclePart: "wheel-aero-insert" };
        registerWheelPart(insert, spin);

        for (const [pairIndex, offset] of [-0.105, 0.105].entries()) {
          const spokeAngle = angle + offset;
          const spoke = createPanelMesh(
            scene,
            `${steering.name} · turbínový lúč ${bladeIndex + 1}.${pairIndex + 1}`,
            [
              polarPoint(0.055, spokeAngle - 0.055, side * 0.135),
              polarPoint(0.06, spokeAngle + 0.055, side * 0.135),
              polarPoint(0.215, spokeAngle + 0.095, side * 0.135),
              polarPoint(0.22, spokeAngle - 0.025, side * 0.135),
            ],
            machinedAlloy,
          );
          spoke.metadata = { vehiclePart: "wheel-spoke" };
          registerWheelPart(spoke, spin);
        }
      }

      const hub = CreateCylinder(
        `${steering.name} · stred disku`,
        { height: 0.04, diameter: 0.09, tessellation: 24 },
        scene,
      );
      hub.position.z = side * 0.13;
      hub.rotation.x = Math.PI / 2;
      hub.material = darkChrome;
      hub.metadata = { vehiclePart: "wheel-hub" };
      registerWheelPart(hub, spin);

      const archPath = Array.from({ length: 25 }, (_, index) => {
        const angle = (index / 24) * Math.PI;
        return new Vector3(
          axleX + Math.cos(angle) * GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M,
          GARAGE_SUPERB_WHEEL_M.centerY +
            Math.sin(angle) * GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M,
          side * 0.932,
        );
      });
      const wheelArch = addTube(
        `lis podbehu ${axle} ${sideName}`,
        archPath,
        0.01,
        paint,
        true,
      );
      wheelArch.metadata = { vehiclePart: "wheel-arch" };
    }
  }

  // Stable, inexpensive collision proxies stay separate from the high-detail
  // display mesh and move with the same animation root.
  for (const [name, size, position] of [
    [
      "spodný kolízny obal",
      {
        x: GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.length / 1_000,
        y: 0.68,
        z: 1.82,
      },
      { x: 0, y: 0.55, z: 0 },
    ],
    [
      "horný kolízny obal",
      { x: lx(2.92), y: 0.5, z: 1.5 },
      { x: lx(-0.32), y: 1.22, z: 0 },
    ],
  ] as const) {
    const collider = CreateBox(
      `${vehicle.label} · ${name}`,
      { width: size.x, height: size.y, depth: size.z },
      scene,
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
    hooks.register(collider);
  }

  return {
    root,
    wheelSpins,
    frontSteering,
    headlightMaterial: headlight,
    brakeMaterial: brake,
  };
}
