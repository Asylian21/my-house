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
  GARAGE_SUPERB_HALF_TRACKS_M,
  GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM,
  GARAGE_SUPERB_ROOF_STATIONS,
  GARAGE_SUPERB_SIDE_WINDOWS,
  GARAGE_SUPERB_VISUAL_LENGTH_SCALE,
  GARAGE_SUPERB_WHEEL_M,
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
  sideZ: number,
) {
  return profile.map(({ x, y }) => new Vector3(x, y, sideZ));
}

export function buildGarageSuperbVehicle(
  scene: Scene,
  hooks: GarageVehicleBuildHooks,
): GarageVehicleVisual {
  const vehicle = GARAGE_VEHICLE;
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
  };
  root.setEnabled(false);

  const paint = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · Cobalt Blue metalíza",
    "#34687d",
    0.26,
    0.62,
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
    0.1,
    0.02,
    0.5,
  );
  glass.backFaceCulling = false;
  glass.indexOfRefraction = 1.52;
  glass.environmentIntensity = 1.35;
  glass.clearCoat.isEnabled = true;
  glass.clearCoat.intensity = 0.88;
  glass.clearCoat.roughness = 0.04;

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
    "Superb Combi IV · 19-palcové disky Aniara",
    "#aeb7bb",
    0.24,
    0.92,
  );
  const machinedAlloy = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · brúsené plochy diskov",
    "#d4dadd",
    0.17,
    0.96,
  );
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
  headlight.emissiveColor = Color3.FromHexString("#b9e6ff").scale(0.72);
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
    { x: 4.22, y: 0.08, z: 1.64 },
    { x: -0.02, y: 0.18, z: 0 },
    pianoBlack,
  );

  // A low dark interior floor, seats and dashboard sit behind independently
  // modeled windows. The glasshouse remains optically open instead of becoming
  // the previous opaque rectangular bubble.
  addBox(
    "podlaha kabíny",
    { x: 2.74, y: 0.1, z: 1.34 },
    { x: -0.34, y: 0.88, z: 0 },
    interior,
    false,
  );
  addBox(
    "prístrojová doska",
    { x: 0.38, y: 0.09, z: 1.18 },
    { x: 0.72, y: 0.955, z: 0 },
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
        { x: 0.47, y: 0.14, z: 0.48 },
        { x, y: 0.86, z: side * 0.37 },
        interior,
        false,
      );
      addBox(
        `${row} operadlo ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: 0.18, y: 0.48, z: 0.46 },
        { x: x - 0.13, y: 1.08, z: side * 0.37 },
        interior,
        false,
      );
      const headrest = CreateSphere(
        `${vehicle.label} · ${row} hlavová opierka ${side < 0 ? "vľavo" : "vpravo"}`,
        { diameter: 1, segments: 16 },
        scene,
      );
      headrest.position.set(x - 0.16, 1.36, side * 0.37);
      headrest.scaling.set(0.13, 0.11, 0.18);
      headrest.material = interior;
      registerVisual(headrest, false);
    }
  }

  for (const side of [-1, 1] as const) {
    const sideZ = side * 0.778;
    for (const window of GARAGE_SUPERB_SIDE_WINDOWS) {
      const pane = createPanelMesh(
        scene,
        `${vehicle.label} · ${window.id} bočné sklo ${side < 0 ? "vľavo" : "vpravo"}`,
        sidePanelPoints(window.points, sideZ),
        glass,
      );
      pane.metadata = { vehiclePart: "side-window", windowId: window.id };
      registerVisual(pane, false);
      const points = sidePanelPoints(window.points, sideZ + side * 0.004);
      addTube(
        `${window.id} rám okna ${side < 0 ? "vľavo" : "vpravo"}`,
        [...points, points[0]],
        0.012,
        pianoBlack,
      );
    }

    addTube(
      `tornado línia ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(-2.02, 0.905, side * 0.9),
        new Vector3(-1.3, 0.955, side * 0.925),
        new Vector3(-0.2, 0.965, side * 0.928),
        new Vector3(0.95, 0.945, side * 0.925),
        new Vector3(1.7, 0.86, side * 0.895),
      ],
      0.004,
      darkChrome,
    );
    addTube(
      `spodná chrómová línia okien ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(-1.7, 1.0, side * 0.79),
        new Vector3(-0.55, 1.008, side * 0.793),
        new Vector3(0.9, 1.006, side * 0.78),
      ],
      0.009,
      darkChrome,
    );

    for (const [index, x] of [-0.66, 0.3].entries()) {
      addBox(
        `zapustená kľučka ${index + 1} ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: 0.18, y: 0.022, z: 0.018 },
        { x, y: 0.895, z: side * 0.929 },
        darkChrome,
        false,
      );
    }
    for (const x of [-1.73, -0.96, 0.02, 0.96]) {
      addTube(
        `škára dverí ${x.toFixed(2)} ${side < 0 ? "vľavo" : "vpravo"}`,
        [
          new Vector3(x, 0.37, side * 0.926),
          new Vector3(x, 0.96, side * 0.926),
        ],
        0.003,
        pianoBlack,
      );
    }

    const mirrorStem = addBox(
      `držiak spätného zrkadla ${side < 0 ? "vľavo" : "vpravo"}`,
      { x: 0.11, y: 0.055, z: 0.15 },
      { x: 0.72, y: 1.17, z: side * 0.84 },
      pianoBlack,
    );
    mirrorStem.rotation.z = -0.14;
    const mirror = CreateSphere(
      `${vehicle.label} · aerodynamické spätné zrkadlo ${side < 0 ? "vľavo" : "vpravo"}`,
      { diameter: 1, segments: 20 },
      scene,
    );
    mirror.position.set(0.72, 1.19, side * 0.98);
    mirror.scaling.set(0.15, 0.065, 0.105);
    mirror.material = paint;
    registerVisual(mirror);

    const rail = addTube(
      `strešná lyžina ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(-1.68, 1.468, side * 0.59),
        new Vector3(-0.75, 1.52, side * 0.61),
        new Vector3(0.42, 1.5, side * 0.6),
      ],
      0.012,
      darkChrome,
      true,
    );
    rail.metadata = { vehiclePart: "roof-rail" };
  }

  const windshield = createPanelMesh(
    scene,
    `${vehicle.label} · akustické čelné sklo`,
    [
      new Vector3(1.1, 1.0, -0.68),
      new Vector3(1.1, 1.0, 0.68),
      new Vector3(0.68, 1.405, 0.64),
      new Vector3(0.68, 1.405, -0.64),
    ],
    glass,
  );
  windshield.metadata = { vehiclePart: "windshield" };
  registerVisual(windshield, false);
  const rearGlass = createPanelMesh(
    scene,
    `${vehicle.label} · vyhrievané sklo piatych dverí`,
    [
      new Vector3(-1.89, 1.0, 0.69),
      new Vector3(-1.89, 1.0, -0.69),
      new Vector3(-1.74, 1.385, -0.64),
      new Vector3(-1.74, 1.385, 0.64),
    ],
    glass,
  );
  rearGlass.metadata = { vehiclePart: "rear-window" };
  registerVisual(rearGlass, false);

  addBox(
    "predĺžený strešný spojler",
    { x: 0.22, y: 0.038, z: 1.34 },
    { x: -1.98, y: 1.405, z: 0 },
    paint,
  );
  for (const side of [-1, 1] as const) {
    const fin = addBox(
      `bočný finlet spojlera ${side < 0 ? "vľavo" : "vpravo"}`,
      { x: 0.19, y: 0.055, z: 0.025 },
      { x: -1.94, y: 1.38, z: side * 0.65 },
      pianoBlack,
    );
    fin.rotation.z = 0.08;
  }

  const halfLengthM = vehicle.dimensionsMm.length / 2_000;
  registerVisual(
    createPanelMesh(
      scene,
      `${vehicle.label} · výplň osemuholníkovej prednej masky`,
      [
        new Vector3(halfLengthM + 0.006, 0.72, -0.59),
        new Vector3(halfLengthM + 0.006, 0.76, -0.5),
        new Vector3(halfLengthM + 0.006, 0.76, 0.5),
        new Vector3(halfLengthM + 0.006, 0.72, 0.59),
        new Vector3(halfLengthM + 0.006, 0.42, 0.59),
        new Vector3(halfLengthM + 0.006, 0.38, 0.5),
        new Vector3(halfLengthM + 0.006, 0.38, -0.5),
        new Vector3(halfLengthM + 0.006, 0.42, -0.59),
      ],
      pianoBlack,
    ),
    false,
  );
  const grillePath = [
    new Vector3(halfLengthM + 0.019, 0.72, -0.59),
    new Vector3(halfLengthM + 0.019, 0.76, -0.5),
    new Vector3(halfLengthM + 0.019, 0.76, 0.5),
    new Vector3(halfLengthM + 0.019, 0.72, 0.59),
    new Vector3(halfLengthM + 0.019, 0.42, 0.59),
    new Vector3(halfLengthM + 0.019, 0.38, 0.5),
    new Vector3(halfLengthM + 0.019, 0.38, -0.5),
    new Vector3(halfLengthM + 0.019, 0.42, -0.59),
    new Vector3(halfLengthM + 0.019, 0.72, -0.59),
  ];
  addTube("rám osemuholníkovej masky", grillePath, 0.008, darkChrome);
  for (let index = -5; index <= 5; index += 1) {
    addBox(
      `zvislá lamela masky ${index + 6}`,
      { x: 0.012, y: 0.24, z: 0.009 },
      { x: halfLengthM + 0.019, y: 0.57, z: index * 0.092 },
      darkChrome,
      false,
    );
  }

  for (const side of [-1, 1] as const) {
    registerVisual(
      createPanelMesh(
        scene,
        `${vehicle.label} · teleso Matrix LED ${side < 0 ? "vľavo" : "vpravo"}`,
        [
          new Vector3(halfLengthM + 0.012, 0.83, side * 0.36),
          new Vector3(halfLengthM + 0.012, 0.82, side * 0.85),
          new Vector3(halfLengthM + 0.012, 0.7, side * 0.8),
          new Vector3(halfLengthM + 0.012, 0.71, side * 0.4),
        ],
        pianoBlack,
      ),
      false,
    );
    for (let moduleIndex = 0; moduleIndex < 3; moduleIndex += 1) {
      addBox(
        `Matrix LED modul ${moduleIndex + 1} ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: 0.01, y: 0.034, z: 0.12 },
        {
          x: halfLengthM + 0.025,
          y: 0.785,
          z: side * (0.45 + moduleIndex * 0.145),
        },
        headlight,
        false,
      );
    }
    addTube(
      `LED denné svetlo L ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(halfLengthM + 0.036, 0.72, side * 0.39),
        new Vector3(halfLengthM + 0.036, 0.72, side * 0.79),
      ],
      0.005,
      headlight,
    );
    addBox(
      `spodný bočný nasávací otvor ${side < 0 ? "vľavo" : "vpravo"}`,
      { x: 0.018, y: 0.1, z: 0.2 },
      { x: halfLengthM + 0.008, y: 0.36, z: side * 0.69 },
      pianoBlack,
      false,
    );
  }
  addTube(
    "centrálny hrebeň kapoty vľavo",
    [new Vector3(1.08, 1.005, -0.13), new Vector3(2.13, 0.82, -0.18)],
    0.004,
    paint,
  );
  addTube(
    "centrálny hrebeň kapoty vpravo",
    [new Vector3(1.08, 1.005, 0.13), new Vector3(2.13, 0.82, 0.18)],
    0.004,
    paint,
  );
  addBox(
    "predná evidenčná tabuľka",
    { x: 0.018, y: 0.12, z: 0.52 },
    { x: halfLengthM + 0.036, y: 0.39, z: 0 },
    plate,
    false,
  );

  addBox(
    "široký zadný difúzor",
    { x: 0.03, y: 0.13, z: 1.36 },
    { x: -halfLengthM - 0.005, y: 0.3, z: 0 },
    pianoBlack,
  );
  for (const side of [-1, 1] as const) {
    addBox(
      `teleso zadného svetla ${side < 0 ? "vľavo" : "vpravo"}`,
      { x: 0.022, y: 0.15, z: 0.49 },
      { x: -halfLengthM - 0.006, y: 0.76, z: side * 0.59 },
      pianoBlack,
      false,
    );
    addTube(
      `kryštalické zadné svetlo C ${side < 0 ? "vľavo" : "vpravo"}`,
      [
        new Vector3(-halfLengthM - 0.027, 0.83, side * 0.32),
        new Vector3(-halfLengthM - 0.027, 0.84, side * 0.79),
        new Vector3(-halfLengthM - 0.027, 0.72, side * 0.83),
        new Vector3(-halfLengthM - 0.027, 0.67, side * 0.58),
      ],
      0.011,
      brake,
    );
    addBox(
      `zadná odrazka ${side < 0 ? "vľavo" : "vpravo"}`,
      { x: 0.02, y: 0.035, z: 0.28 },
      { x: -halfLengthM - 0.026, y: 0.35, z: side * 0.62 },
      reflector,
      false,
    );
  }
  addBox(
    "zadná evidenčná tabuľka",
    { x: 0.018, y: 0.12, z: 0.52 },
    { x: -halfLengthM - 0.03, y: 0.53, z: 0 },
    plate,
    false,
  );

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

      const torusThickness =
        GARAGE_SUPERB_WHEEL_M.outerDiameter - GARAGE_SUPERB_WHEEL_M.rimDiameter;
      const tireMesh = CreateTorus(
        `${steering.name} · pneumatika 235/40 R19`,
        {
          diameter:
            GARAGE_SUPERB_WHEEL_M.outerDiameter - torusThickness,
          thickness: torusThickness,
          tessellation: 48,
        },
        scene,
      );
      tireMesh.parent = spin;
      tireMesh.rotation.x = Math.PI / 2;
      tireMesh.scaling.y = GARAGE_SUPERB_WHEEL_M.tireWidth / torusThickness;
      tireMesh.material = tire;
      tireMesh.isPickable = false;
      tireMesh.receiveShadows = true;
      hooks.castShadow(tireMesh);
      hooks.realisticOnly(tireMesh);
      hooks.register(tireMesh);

      const brakeDisc = CreateCylinder(
        `${steering.name} · ventilovaný brzdový kotúč`,
        { height: 0.024, diameter: 0.34, tessellation: 40 },
        scene,
      );
      brakeDisc.parent = spin;
      brakeDisc.position.z = side * 0.085;
      brakeDisc.rotation.x = Math.PI / 2;
      brakeDisc.material = darkChrome;
      brakeDisc.isPickable = false;
      hooks.realisticOnly(brakeDisc);
      hooks.register(brakeDisc);

      const rim = CreateCylinder(
        `${steering.name} · disk Aniara 8J × 19`,
        { height: 0.035, diameter: GARAGE_SUPERB_WHEEL_M.rimDiameter, tessellation: 48 },
        scene,
      );
      rim.parent = spin;
      rim.position.z = side * 0.1;
      rim.rotation.x = Math.PI / 2;
      rim.material = alloy;
      rim.isPickable = false;
      hooks.realisticOnly(rim);
      hooks.register(rim);

      for (let spokeIndex = 0; spokeIndex < 10; spokeIndex += 1) {
        const angle = (spokeIndex / 10) * Math.PI * 2;
        const spoke = CreateBox(
          `${steering.name} · aerodynamický lúč ${spokeIndex + 1}`,
          { width: 0.185, height: 0.024, depth: 0.026 },
          scene,
        );
        spoke.parent = spin;
        spoke.position.set(
          Math.cos(angle) * 0.105,
          Math.sin(angle) * 0.105,
          side * 0.124,
        );
        spoke.rotation.z = angle;
        spoke.material = spokeIndex % 2 === 0 ? machinedAlloy : alloy;
        spoke.isPickable = false;
        hooks.realisticOnly(spoke);
        hooks.register(spoke);
      }

      const hub = CreateCylinder(
        `${steering.name} · stred disku`,
        { height: 0.04, diameter: 0.09, tessellation: 24 },
        scene,
      );
      hub.parent = spin;
      hub.position.z = side * 0.13;
      hub.rotation.x = Math.PI / 2;
      hub.material = darkChrome;
      hub.isPickable = false;
      hooks.realisticOnly(hub);
      hooks.register(hub);

      const archPath = Array.from({ length: 17 }, (_, index) => {
        const angle = (index / 16) * Math.PI;
        return new Vector3(
          axleX + Math.cos(angle) * 0.385,
          GARAGE_SUPERB_WHEEL_M.centerY + Math.sin(angle) * 0.385,
          side * 0.929,
        );
      });
      addTube(
        `lis podbehu ${axle} ${sideName}`,
        archPath,
        0.006,
        pianoBlack,
        true,
      );
    }
  }

  // Stable, inexpensive collision proxies stay separate from the high-detail
  // display mesh and move with the same animation root.
  for (const [name, size, position] of [
    [
      "spodný kolízny obal",
      { x: 4.54, y: 0.68, z: 1.82 },
      { x: 0, y: 0.55, z: 0 },
    ],
    [
      "horný kolízny obal",
      { x: 2.92, y: 0.5, z: 1.5 },
      { x: -0.32, y: 1.22, z: 0 },
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
