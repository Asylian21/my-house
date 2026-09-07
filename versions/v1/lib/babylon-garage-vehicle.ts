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
  GARAGE_SUPERB_DLO,
  GARAGE_SUPERB_HALF_LENGTH_M,
  GARAGE_SUPERB_HALF_TRACKS_M,
  GARAGE_SUPERB_LOFT_RING_POINT_COUNT,
  GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM,
  GARAGE_SUPERB_VISUAL_LENGTH_SCALE,
  GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M,
  GARAGE_SUPERB_WHEEL_M,
  garageSuperbBodySideZ,
  garageSuperbDloBottomY,
  garageSuperbDloTopY,
  garageSuperbGlassZ,
  garageSuperbSectionAt,
  vehicleLoftGeometry,
  type VehicleSection,
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
  sections: readonly VehicleSection[],
  material: Material,
) {
  const geometry = vehicleLoftGeometry(sections);
  const positions = [...geometry.positions];
  const indices = [...geometry.indices];
  const normals = new Array(positions.length).fill(0);
  VertexData.ComputeNormals(positions, indices, normals);
  // The flat end caps act as mirrors and reflect the environment's road as a
  // hard dark "V". Dome their vertex normals (shading only, geometry stays
  // flat) so the fascia and tailgate scatter reflections like curved panels.
  const stripVertexCount =
    sections.length * GARAGE_SUPERB_LOFT_RING_POINT_COUNT;
  const capVertexCount = GARAGE_SUPERB_LOFT_RING_POINT_COUNT + 1;
  for (const cap of [0, 1]) {
    const capStart = stripVertexCount + cap * capVertexCount;
    const centreIndex = capStart + capVertexCount - 1;
    const centreY = positions[centreIndex * 3 + 1];
    const axisX = Math.sign(positions[centreIndex * 3]);
    for (let offset = 0; offset < capVertexCount - 1; offset += 1) {
      const vertex = (capStart + offset) * 3;
      const radialY = positions[vertex + 1] - centreY;
      const radialZ = positions[vertex + 2];
      const radialLength = Math.hypot(radialY, radialZ) || 1;
      const domeX = axisX;
      const domeY = (radialY / radialLength) * 0.85;
      const domeZ = (radialZ / radialLength) * 0.85;
      const domeLength = Math.hypot(domeX, domeY, domeZ);
      normals[vertex] = domeX / domeLength;
      normals[vertex + 1] = domeY / domeLength;
      normals[vertex + 2] = domeZ / domeLength;
    }
  }
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

/** Curved quad-grid surface (glazing bands, windscreen, pillar covers). */
function createGridMesh(
  scene: Scene,
  name: string,
  grid: readonly (readonly Vector3[])[],
  material: Material,
) {
  const rows = grid.length;
  const cols = grid[0].length;
  const positions: number[] = [];
  for (const row of grid) {
    for (const point of row) positions.push(point.x, point.y, point.z);
  }
  const indices: number[] = [];
  for (let row = 0; row < rows - 1; row += 1) {
    for (let col = 0; col < cols - 1; col += 1) {
      const a = row * cols + col;
      const b = a + 1;
      const c = a + cols;
      const d = c + 1;
      indices.push(a, b, c, b, d, c);
    }
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
    visualReference: "client-supplied-2024-plus-superb-combi-photos-2026-08-25",
    referenceViews: ["side-profile", "front-three-quarter"],
    bodyConstruction: "single-loft-arch-cutouts",
  };
  root.setEnabled(false);

  const paint = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · šalviovo-olivová metalíza",
    "#8a9178",
    0.24,
    0.62,
  );
  paint.clearCoat.isEnabled = true;
  paint.clearCoat.intensity = 0.95;
  paint.clearCoat.roughness = 0.09;
  paint.environmentIntensity = 0.95;
  // Loft end caps stay visible on drivers that reverse procedural winding.
  paint.backFaceCulling = false;

  const glass = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · tónované bezpečnostné sklo",
    "#0a1418",
    0.06,
    0.05,
    0.93,
  );
  glass.backFaceCulling = false;
  glass.indexOfRefraction = 1.52;
  glass.environmentIntensity = 1.4;
  glass.clearCoat.isEnabled = true;
  glass.clearCoat.intensity = 0.9;
  glass.clearCoat.roughness = 0.03;

  const pianoBlack = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · lesklá čierna",
    "#0a0e10",
    0.22,
    0.45,
  );
  pianoBlack.backFaceCulling = false;
  // Matte near-black for wheel wells and underbody: fully rough so arches
  // read as deep shadow instead of reflecting the sky as light-grey rings.
  const wellShadow = vehiclePbrMaterial(
    scene,
    "Superb Combi IV · matný tieň podbehov",
    "#060708",
    1,
    0,
  );
  wellShadow.backFaceCulling = false;
  wellShadow.environmentIntensity = 0.12;
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

  const section = garageSuperbSectionAt;
  const noseX = GARAGE_SUPERB_HALF_LENGTH_M;
  const tailX = -GARAGE_SUPERB_HALF_LENGTH_M;

  // ---------------------------------------------------------------- body ---
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

  addBox(
    "aerodynamicky zakrytý podvozok",
    { x: 4.35, y: 0.09, z: 1.5 },
    { x: 0, y: 0.17, z: 0 },
    wellShadow,
  ).metadata = { vehiclePart: "underbody" };
  addBox(
    "tmavý blok podvozku medzi nápravami",
    { x: 4.05, y: 0.46, z: 1.3 },
    { x: 0.05, y: 0.38, z: 0 },
    wellShadow,
    false,
  ).metadata = { vehiclePart: "underbody-block" };

  // ------------------------------------------------------------ interior ---
  addBox(
    "podlaha kabíny",
    { x: 2.6, y: 0.1, z: 1.3 },
    { x: -0.35, y: 0.84, z: 0 },
    interior,
    false,
  );
  addBox(
    "prístrojová doska",
    { x: 0.36, y: 0.1, z: 1.24 },
    { x: 0.62, y: 0.94, z: 0 },
    interior,
    false,
  );
  for (const [row, x] of [
    ["predný", 0.12],
    ["zadný", -0.85],
  ] as const) {
    for (const side of [-1, 1] as const) {
      addBox(
        `${row} sedák ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: 0.48, y: 0.14, z: 0.46 },
        { x, y: 0.88, z: side * 0.36 },
        interior,
        false,
      );
      addBox(
        `${row} operadlo ${side < 0 ? "vľavo" : "vpravo"}`,
        { x: 0.17, y: 0.42, z: 0.44 },
        { x: x - 0.14, y: 1.06, z: side * 0.36 },
        interior,
        false,
      );
      const headrest = CreateSphere(
        `${vehicle.label} · ${row} hlavová opierka ${side < 0 ? "vľavo" : "vpravo"}`,
        { diameter: 1, segments: 16 },
        scene,
      );
      headrest.position.set(x - 0.17, 1.3, side * 0.36);
      headrest.scaling.set(0.13, 0.1, 0.17);
      headrest.material = interior;
      registerVisual(headrest, false);
    }
  }

  // ------------------------------------------------------------- glazing ---
  const windshieldXs = [0.74, 0.62, 0.48, 0.34, 0.2, 0.1, 0.03];
  const glassColumns = [-1, -0.66, -0.33, 0, 0.33, 0.66, 1];
  const windshield = createGridMesh(
    scene,
    `${vehicle.label} · akustické čelné sklo`,
    windshieldXs.map((x) => {
      const crest = section(x);
      const halfW = crest.roofHalf * 0.965;
      return glassColumns.map(
        (c) =>
          new Vector3(x + 0.012, crest.roofY + 0.012 - 0.018 * c * c, c * halfW),
      );
    }),
    glass,
  );
  windshield.metadata = { vehiclePart: "windshield" };
  registerVisual(windshield, false);

  const rearGlassXs = [-1.8, -1.92, -2.04, -2.16, -2.26, -2.34];
  const rearGlass = createGridMesh(
    scene,
    `${vehicle.label} · vyhrievané sklo piatych dverí`,
    rearGlassXs.map((x) => {
      const crest = section(x);
      const halfW = crest.roofHalf * 0.93;
      return glassColumns.map(
        (c) =>
          new Vector3(x - 0.012, crest.roofY + 0.012 - 0.016 * c * c, c * halfW),
      );
    }),
    glass,
  );
  rearGlass.metadata = { vehiclePart: "rear-window" };
  registerVisual(rearGlass, false);

  const dloXs = [
    GARAGE_SUPERB_DLO.frontTipX, 0.9, 0.76, 0.6, 0.42, 0.24, 0.06, -0.14,
    -0.36, -0.6, -0.85, -1.1, -1.35, -1.58, -1.78, -1.95,
    GARAGE_SUPERB_DLO.rearTipX,
  ];
  const dloRows = [0, 0.25, 0.5, 0.75, 1];
  for (const side of [-1, 1] as const) {
    const sideName = side < 0 ? "vľavo" : "vpravo";
    const band = createGridMesh(
      scene,
      `${vehicle.label} · bočné presklenie kabíny ${sideName}`,
      dloRows.map((t) =>
        dloXs.map((x) => {
          const bottom = garageSuperbDloBottomY(x);
          const top = Math.max(bottom, garageSuperbDloTopY(x));
          const y = bottom + (top - bottom) * t;
          return new Vector3(x, y, side * garageSuperbGlassZ(x, y));
        }),
      ),
      glass,
    );
    band.metadata = { vehiclePart: "side-glass" };
    registerVisual(band, false);

    // Gloss-black B and C pillars over the glass band, as on the real car.
    for (const [pillarId, x0, x1] of [
      ["B", 0.02, 0.12],
      ["C", -1.2, -1.08],
    ] as const) {
      const strip = createGridMesh(
        scene,
        `${vehicle.label} · ${pillarId}-stĺpik ${sideName}`,
        dloRows.map((t) =>
          [x0, (x0 + x1) / 2, x1].map((x) => {
            const bottom = garageSuperbDloBottomY(x) - 0.004;
            const top = garageSuperbDloTopY(x) + 0.004;
            const y = bottom + (top - bottom) * t;
            return new Vector3(x, y, side * (garageSuperbGlassZ(x, y) + 0.003));
          }),
        ),
        pianoBlack,
      );
      strip.metadata = { vehiclePart: "window-pillar", pillarId };
      registerVisual(strip, false);
    }

    // Continuous chrome day-light-opening surround.
    const outlineBottom = dloXs.map((x) => {
      const y = garageSuperbDloBottomY(x);
      return new Vector3(x, y, side * (garageSuperbGlassZ(x, y) + 0.003));
    });
    const outlineTop = [...dloXs].reverse().map((x) => {
      const y = Math.max(garageSuperbDloBottomY(x), garageSuperbDloTopY(x));
      return new Vector3(x, y, side * (garageSuperbGlassZ(x, y) + 0.003));
    });
    const surround = addTube(
      `chrómové orámovanie presklenia ${sideName}`,
      [...outlineBottom, ...outlineTop, outlineBottom[0]],
      0.0055,
      brightChrome,
    );
    surround.metadata = { vehiclePart: "window-chrome-surround" };
  }

  // ---------------------------------------------------------- side trim ---
  for (const side of [-1, 1] as const) {
    const sideName = side < 0 ? "vľavo" : "vpravo";

    for (const x of [1.04, 0.04, -1.1]) {
      const belt = section(x).beltY;
      const seam = addTube(
        `škára dverí ${x.toFixed(2)} ${sideName}`,
        [
          new Vector3(x, 0.32, side * (garageSuperbBodySideZ(x, 0.32) + 0.003)),
          new Vector3(x, 0.62, side * (garageSuperbBodySideZ(x, 0.62) + 0.003)),
          new Vector3(
            x,
            belt - 0.01,
            side * (garageSuperbBodySideZ(x, belt - 0.01) + 0.003),
          ),
        ],
        0.0028,
        pianoBlack,
      );
      seam.metadata = { vehiclePart: "door-seam" };
    }

    for (const [index, x] of [0.48, -0.68].entries()) {
      const y = section(x).beltY - 0.095;
      const handle = addBox(
        `zapustená kľučka ${index + 1} ${sideName}`,
        { x: 0.16, y: 0.026, z: 0.014 },
        { x, y, z: side * (garageSuperbBodySideZ(x, y) + 0.008) },
        paint,
        false,
      );
      handle.metadata = { vehiclePart: "door-handle" };
    }

    const mirrorStem = addBox(
      `držiak spätného zrkadla ${sideName}`,
      { x: 0.12, y: 0.04, z: 0.14 },
      { x: 0.8, y: 0.945, z: side * 0.86 },
      pianoBlack,
    );
    mirrorStem.rotation.z = -0.1;
    mirrorStem.metadata = { vehiclePart: "mirror-stem" };
    const mirror = CreateSphere(
      `${vehicle.label} · aerodynamické spätné zrkadlo ${sideName}`,
      { diameter: 1, segments: 24 },
      scene,
    );
    mirror.position.set(0.8, 0.985, side * 0.985);
    mirror.scaling.set(0.165, 0.075, 0.12);
    mirror.material = paint;
    mirror.metadata = { vehiclePart: "external-mirror" };
    registerVisual(mirror);

    const rail = addTube(
      `strešná lyžina ${sideName}`,
      [0.05, -0.4, -0.9, -1.4, -1.8, -2.05].map((x) => {
        const crest = section(x);
        return new Vector3(
          x,
          crest.roofY + 0.016,
          side * (crest.roofHalf + 0.008),
        );
      }),
      0.011,
      brightChrome,
      true,
    );
    rail.metadata = { vehiclePart: "roof-rail" };

    const rocker = addBox(
      `čierny prah ${sideName}`,
      { x: 2.02, y: 0.045, z: 0.02 },
      { x: 0.08, y: 0.177, z: side * 0.906 },
      pianoBlack,
      false,
    );
    rocker.metadata = { vehiclePart: "rocker-trim" };
  }

  // Gloss-black wedge under the trailing edge of the roof spoiler.
  const spoilerUnderside = addBox(
    "čierna spodná hrana spojlera",
    { x: 0.1, y: 0.045, z: 1.14 },
    { x: -2.4, y: 1.255, z: 0 },
    pianoBlack,
    false,
  );
  spoilerUnderside.metadata = { vehiclePart: "roof-spoiler-underside" };

  // ------------------------------------------------------- front fascia ---
  const grilleOutline = (inset: number) =>
    [
      [0.78 - inset, 0.27 - inset],
      [0.752 - inset, 0.33 - inset],
      [0.542 + inset, 0.33 - inset],
      [0.512 + inset, 0.27 - inset],
      [0.512 + inset, -(0.27 - inset)],
      [0.542 + inset, -(0.33 - inset)],
      [0.752 - inset, -(0.33 - inset)],
      [0.78 - inset, -(0.27 - inset)],
    ] as const;
  const grilleX = (y: number) => noseX + 0.011 - (y - 0.512) * 0.11;
  const grille = createPanelMesh(
    scene,
    `${vehicle.label} · výplň širokej osemuholníkovej prednej masky`,
    grilleOutline(0.004).map(([y, z]) => new Vector3(grilleX(y), y, z)),
    pianoBlack,
  );
  grille.metadata = { vehiclePart: "front-grille" };
  registerVisual(grille, false);
  const framePoints = grilleOutline(0).map(
    ([y, z]) => new Vector3(grilleX(y) + 0.006, y, z),
  );
  const grilleFrame = addTube(
    "svetlý chrómový rám osemuholníkovej masky",
    [...framePoints, framePoints[0]],
    0.009,
    brightChrome,
  );
  grilleFrame.metadata = { vehiclePart: "front-grille-frame" };
  for (let index = -6; index <= 6; index += 1) {
    const slat = addBox(
      `zvislá lamela masky ${index + 7}`,
      { x: 0.012, y: 0.22 - Math.abs(index) * 0.005, z: 0.009 },
      { x: grilleX(0.645) + 0.004, y: 0.645, z: index * 0.048 },
      darkChrome,
      false,
    );
    slat.rotation.z = 0.08;
    slat.metadata = { vehiclePart: "front-grille-slat" };
  }

  const badge = CreateCylinder(
    `${vehicle.label} · emblém na čele kapoty`,
    { height: 0.012, diameter: 0.09, tessellation: 32 },
    scene,
  );
  badge.position.set(grilleX(0.815), 0.815, 0);
  badge.rotation.z = Math.PI / 2;
  badge.material = darkChrome;
  badge.metadata = { vehiclePart: "bonnet-badge" };
  registerVisual(badge, false);

  for (const side of [-1, 1] as const) {
    const sideName = side < 0 ? "vľavo" : "vpravo";
    // Slim horizontal lamp band flanking the grille (never overlapping it),
    // with a short wrap onto the fender anchored to the true body surface.
    const headlamp = createPanelMesh(
      scene,
      `${vehicle.label} · zapustené teleso Matrix LED ${sideName}`,
      [
        new Vector3(noseX + 0.002, 0.784, side * 0.35),
        new Vector3(noseX + 0.002, 0.706, side * 0.35),
        new Vector3(noseX + 0.002, 0.7, side * 0.63),
        new Vector3(2.38, 0.712, side * (garageSuperbBodySideZ(2.38, 0.712) + 0.006)),
        new Vector3(2.365, 0.772, side * (garageSuperbBodySideZ(2.365, 0.772) + 0.006)),
        new Vector3(noseX + 0.002, 0.778, side * 0.62),
      ],
      pianoBlack,
    );
    headlamp.metadata = { vehiclePart: "headlamp" };
    registerVisual(headlamp, false);

    const drl = addTube(
      `dvojité LED denné svetlo ${sideName}`,
      [
        new Vector3(noseX + 0.006, 0.776, side * 0.355),
        new Vector3(noseX + 0.006, 0.772, side * 0.6),
        new Vector3(
          2.375,
          0.768,
          side * (garageSuperbBodySideZ(2.375, 0.768) + 0.008),
        ),
      ],
      0.008,
      headlight,
    );
    drl.metadata = { vehiclePart: "drl" };

    for (let moduleIndex = 0; moduleIndex < 3; moduleIndex += 1) {
      const ledModule = addBox(
        `Matrix LED modul ${moduleIndex + 1} ${sideName}`,
        { x: 0.012, y: 0.045, z: 0.06 },
        { x: noseX + 0.004, y: 0.736, z: side * (0.4 + moduleIndex * 0.085) },
        headlight,
        false,
      );
      ledModule.metadata = { vehiclePart: "headlamp-module" };
    }

    const blade = addBox(
      `zvislá bočná clona nárazníka ${sideName}`,
      { x: 0.02, y: 0.24, z: 0.016 },
      { x: 2.36, y: 0.42, z: side * (garageSuperbBodySideZ(2.36, 0.42) + 0.004) },
      pianoBlack,
      false,
    );
    blade.rotation.y = side * 0.45;
    blade.metadata = { vehiclePart: "side-intake" };
  }

  const lowerIntake = createPanelMesh(
    scene,
    `${vehicle.label} · celoplošný spodný nasávací otvor`,
    [
      new Vector3(noseX + 0.0025, 0.46, -0.545),
      new Vector3(noseX + 0.0025, 0.46, 0.545),
      new Vector3(noseX + 0.0025, 0.28, 0.49),
      new Vector3(noseX + 0.0025, 0.28, -0.49),
    ],
    pianoBlack,
  );
  lowerIntake.metadata = { vehiclePart: "lower-intake" };
  registerVisual(lowerIntake, false);
  const lowerLip = addTube(
    "spodná aerodynamická hrana",
    [
      new Vector3(noseX + 0.004, 0.272, -0.48),
      new Vector3(noseX + 0.004, 0.262, 0),
      new Vector3(noseX + 0.004, 0.272, 0.48),
    ],
    0.008,
    darkChrome,
  );
  lowerLip.metadata = { vehiclePart: "front-lower-lip" };

  const frontPlate = addBox(
    "predná evidenčná tabuľka",
    { x: 0.016, y: 0.125, z: 0.52 },
    { x: noseX + 0.007, y: 0.37, z: 0 },
    plate,
    false,
  );
  frontPlate.metadata = { vehiclePart: "front-plate" };

  // --------------------------------------------------------------- rear ---
  for (const side of [-1, 1] as const) {
    const sideName = side < 0 ? "vľavo" : "vpravo";
    const rearLampHousing = createPanelMesh(
      scene,
      `${vehicle.label} · štíhle teleso zadného svetla ${sideName}`,
      [
        new Vector3(tailX - 0.0015, 0.995, side * 0.3),
        new Vector3(tailX - 0.0015, 0.91, side * 0.3),
        new Vector3(tailX + 0.001, 0.905, side * 0.55),
        new Vector3(tailX + 0.031, 0.91, side * 0.72),
      ],
      pianoBlack,
    );
    rearLampHousing.metadata = { vehiclePart: "rear-lamp" };
    registerVisual(rearLampHousing, false);

    const wrapLamp = createPanelMesh(
      scene,
      `${vehicle.label} · bočné wrap-around zadné svetlo ${sideName}`,
      [
        new Vector3(tailX + 0.031, 0.995, side * 0.71),
        new Vector3(tailX + 0.031, 0.905, side * 0.715),
        new Vector3(tailX + 0.151, 0.93, side * 0.862),
        new Vector3(tailX + 0.121, 0.985, side * 0.856),
      ],
      pianoBlack,
    );
    wrapLamp.metadata = { vehiclePart: "rear-wrap-lamp" };
    registerVisual(wrapLamp, false);

    const upperGuide = addTube(
      `kryštalické zadné svetlo C ${sideName}`,
      [
        new Vector3(tailX - 0.005, 0.975, side * 0.32),
        new Vector3(tailX - 0.005, 0.978, side * 0.62),
        new Vector3(tailX + 0.012, 0.972, side * 0.74),
        new Vector3(tailX + 0.136, 0.952, side * 0.856),
      ],
      0.007,
      brake,
    );
    upperGuide.metadata = { vehiclePart: "rear-light-guide" };
    const lowerGuide = addTube(
      `spodná línia zadného svetla ${sideName}`,
      [
        new Vector3(tailX - 0.005, 0.925, side * 0.34),
        new Vector3(tailX - 0.005, 0.922, side * 0.6),
      ],
      0.006,
      brake,
    );
    lowerGuide.metadata = { vehiclePart: "rear-light-guide" };

    const rearReflector = addBox(
      `zadná odrazka ${sideName}`,
      { x: 0.014, y: 0.05, z: 0.16 },
      { x: tailX - 0.005, y: 0.42, z: side * 0.55 },
      reflector,
      false,
    );
    rearReflector.metadata = { vehiclePart: "rear-reflector" };
  }

  const rearBand = addBox(
    "čierny spojovací panel zadných svetiel",
    { x: 0.014, y: 0.085, z: 0.62 },
    { x: tailX - 0.0035, y: 0.952, z: 0 },
    pianoBlack,
    false,
  );
  rearBand.metadata = { vehiclePart: "rear-band" };
  const rearWordmark = addTube(
    "chrómová linka nápisu ŠKODA",
    [
      new Vector3(tailX - 0.012, 0.918, -0.24),
      new Vector3(tailX - 0.012, 0.918, 0.24),
    ],
    0.004,
    brightChrome,
  );
  rearWordmark.metadata = { vehiclePart: "rear-wordmark-line" };

  const rearDiffuser = addBox(
    "nízky lichobežníkový zadný difúzor",
    { x: 0.02, y: 0.15, z: 1.24 },
    { x: tailX - 0.0035, y: 0.315, z: 0 },
    pianoBlack,
  );
  rearDiffuser.metadata = { vehiclePart: "rear-diffuser" };
  const rearPlate = addBox(
    "zadná evidenčná tabuľka",
    { x: 0.016, y: 0.125, z: 0.52 },
    { x: tailX - 0.006, y: 0.64, z: 0 },
    plate,
    false,
  );
  rearPlate.metadata = { vehiclePart: "rear-plate" };

  // -------------------------------------------------------------- wheels ---
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
        { height: 0.03, diameter: 0.68, tessellation: 48 },
        scene,
      );
      // Slightly above the axle so the disc fills the arch apex without
      // poking through the road surface below the tyre contact patch.
      wheelWell.position.set(
        axleX,
        GARAGE_SUPERB_WHEEL_M.centerY + 0.03,
        side * 0.84,
      );
      wheelWell.rotation.x = Math.PI / 2;
      wheelWell.material = wellShadow;
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
        {
          diameter: GARAGE_SUPERB_WHEEL_M.rimDiameter - 0.018,
          thickness: 0.018,
          tessellation: 56,
        },
        scene,
      );
      rimLip.position.z = side * 0.122;
      rimLip.rotation.x = Math.PI / 2;
      rimLip.material = machinedAlloy;
      rimLip.metadata = { vehiclePart: "rim-lip" };
      registerWheelPart(rimLip, spin);

      const polarPoint = (radius: number, angle: number, z: number) =>
        new Vector3(Math.cos(angle) * radius, Math.sin(angle) * radius, z);
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

      const archZ = garageSuperbBodySideZ(axleX + 0.02, 0.6) + 0.004;
      const archPath = Array.from({ length: 25 }, (_, index) => {
        const angle = (index / 24) * Math.PI;
        return new Vector3(
          axleX + Math.cos(angle) * GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M,
          GARAGE_SUPERB_WHEEL_M.centerY +
            Math.sin(angle) * GARAGE_SUPERB_WHEEL_ARCH_RADIUS_M,
          side * archZ,
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
      { x: 3.0, y: 0.5, z: 1.5 },
      { x: -0.4, y: 1.22, z: 0 },
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
