/**
 * Pure, renderer-independent geometry for the joined L-shaped roof.
 *
 * Coordinates stay in the authoritative plan frame: X/Y are plan millimetres
 * and elevationMm is height above the 1.NP datum. Babylon conversion belongs
 * at the render boundary, never in this module.
 */

import { HOUSE } from "./twin-site";

export type RoofFaceId =
  | "MAIN_FRONT"
  | "MAIN_GARDEN"
  | "WING_INNER"
  | "WING_OUTER";

export type RoofLineKind = "RIDGE" | "VALLEY" | "HIP" | "GUTTER";

export interface RoofPointMm {
  readonly xMm: number;
  readonly yMm: number;
  readonly elevationMm: number;
}

export interface RoofVertexMm extends RoofPointMm {
  readonly id: string;
}

export interface RoofTriangle {
  readonly faceId: RoofFaceId;
  readonly vertexIndices: readonly [number, number, number];
}

export interface RoofFace {
  readonly id: RoofFaceId;
  readonly vertexIndices: readonly [number, number, number, number];
  readonly triangleIndices: readonly [number, number];
  readonly seamAxis: "X" | "Y";
}

export interface RoofLineFeature {
  readonly id: string;
  readonly kind: RoofLineKind;
  readonly startVertexIndex: number;
  readonly endVertexIndex: number;
}

export interface RoofGable {
  readonly id: "MAIN_WEST_GABLE" | "WING_END_GABLE";
  readonly vertexIndices: readonly [number, number, number];
  readonly plane:
    | { readonly axis: "X"; readonly coordinateMm: number }
    | { readonly axis: "Y"; readonly coordinateMm: number };
}

export interface RoofSeamSegment {
  readonly id: string;
  readonly faceId: RoofFaceId;
  readonly axis: "X" | "Y";
  readonly coordinateMm: number;
  readonly start: RoofPointMm;
  readonly end: RoofPointMm;
}

export interface RoofBoundsMm {
  readonly minXmm: number;
  readonly maxXmm: number;
  readonly minYmm: number;
  readonly maxYmm: number;
  readonly minElevationMm: number;
  readonly maxElevationMm: number;
}

export interface JoinedRoofParameters {
  readonly minXmm: number;
  readonly maxXmm: number;
  readonly frontEaveYmm: number;
  readonly mainRidgeYmm: number;
  readonly gardenEaveYmm: number;
  readonly wingInnerEaveXmm: number;
  readonly wingRidgeXmm: number;
  readonly wingEndYmm: number;
  readonly eavesElevationMm: number;
  readonly ridgeElevationMm: number;
  readonly mainSeamInsetMm: number;
  readonly mainSeamSpacingMm: number;
  readonly wingSeamInsetMm: number;
  readonly wingSeamSpacingMm: number;
}

export interface JoinedRoofGeometry {
  readonly parameters: JoinedRoofParameters;
  readonly vertices: readonly RoofVertexMm[];
  readonly faces: readonly RoofFace[];
  readonly triangles: readonly RoofTriangle[];
  readonly ridges: readonly RoofLineFeature[];
  readonly valley: RoofLineFeature;
  readonly hip: RoofLineFeature;
  readonly gutters: readonly RoofLineFeature[];
  readonly gables: readonly RoofGable[];
  readonly seamSegments: readonly RoofSeamSegment[];
  readonly bounds: RoofBoundsMm;
  readonly projectedAreaMm2: number;
  readonly surfaceAreaMm2: number;
}

/**
 * A renderer-ready quadrilateral. The authoritative roof keeps its documented
 * overhangs, while these patches partition visible finishes so two opaque
 * materials never claim the same depth-buffer pixels.
 */
export interface RoofRenderFace {
  readonly id: string;
  readonly faceId: RoofFaceId;
  readonly vertices: readonly [
    RoofVertexMm,
    RoofVertexMm,
    RoofVertexMm,
    RoofVertexMm,
  ];
}

export interface JoinedRoofRenderPlan {
  readonly topFaces: readonly RoofRenderFace[];
  readonly genericUndersideFaces: readonly RoofRenderFace[];
  readonly seamSegments: readonly RoofSeamSegment[];
  readonly wingPorch: {
    /** Metal roof stops where the opaque P04 rake begins. */
    readonly roofTopEndYmm: number;
    /** The generic white underside stops before the dedicated larch soffit. */
    readonly genericUndersideEndYmm: number;
    readonly larchSoffitStartYmm: number;
    readonly larchSoffitEndYmm: number;
    readonly portalRakeStartYmm: number;
    readonly portalRakeEndYmm: number;
  };
}

export const ACTIVE_JOINED_ROOF_PARAMETERS: JoinedRoofParameters = Object.freeze({
  minXmm: HOUSE.originMm.x,
  maxXmm: HOUSE.originMm.x + HOUSE.lowerBar.widthMm,
  frontEaveYmm: HOUSE.originMm.y,
  mainRidgeYmm: HOUSE.originMm.y + HOUSE.roof.mainHalfSpanMm,
  gardenEaveYmm: HOUSE.originMm.y + HOUSE.lowerBar.depthMm,
  wingInnerEaveXmm: HOUSE.originMm.x + HOUSE.wing.xMm,
  wingRidgeXmm:
    HOUSE.originMm.x + HOUSE.wing.xMm + HOUSE.roof.wingHalfSpanMm,
  wingEndYmm:
    HOUSE.originMm.y +
    HOUSE.roof.wingOverallPlanLengthMm +
    HOUSE.roof.wingEndOverhangMm,
  eavesElevationMm: HOUSE.eavesElevationMm,
  ridgeElevationMm: HOUSE.ridgeElevationMm,
  mainSeamInsetMm: 360,
  mainSeamSpacingMm: 760,
  wingSeamInsetMm: 300,
  wingSeamSpacingMm: 720,
});

export function mainFrontRoofHeightMm(
  yMm: number,
  parameters: JoinedRoofParameters = ACTIVE_JOINED_ROOF_PARAMETERS,
): number {
  return interpolateElevation(
    yMm,
    parameters.frontEaveYmm,
    parameters.mainRidgeYmm,
    parameters.eavesElevationMm,
    parameters.ridgeElevationMm,
  );
}

export function mainGardenRoofHeightMm(
  yMm: number,
  parameters: JoinedRoofParameters = ACTIVE_JOINED_ROOF_PARAMETERS,
): number {
  return interpolateElevation(
    yMm,
    parameters.mainRidgeYmm,
    parameters.gardenEaveYmm,
    parameters.ridgeElevationMm,
    parameters.eavesElevationMm,
  );
}

export function wingInnerRoofHeightMm(
  xMm: number,
  parameters: JoinedRoofParameters = ACTIVE_JOINED_ROOF_PARAMETERS,
): number {
  return interpolateElevation(
    xMm,
    parameters.wingInnerEaveXmm,
    parameters.wingRidgeXmm,
    parameters.eavesElevationMm,
    parameters.ridgeElevationMm,
  );
}

export function wingOuterRoofHeightMm(
  xMm: number,
  parameters: JoinedRoofParameters = ACTIVE_JOINED_ROOF_PARAMETERS,
): number {
  return interpolateElevation(
    xMm,
    parameters.wingRidgeXmm,
    parameters.maxXmm,
    parameters.ridgeElevationMm,
    parameters.eavesElevationMm,
  );
}

export function roofHeightMm(
  faceId: RoofFaceId,
  xMm: number,
  yMm: number,
  parameters: JoinedRoofParameters = ACTIVE_JOINED_ROOF_PARAMETERS,
): number {
  switch (faceId) {
    case "MAIN_FRONT":
      return mainFrontRoofHeightMm(yMm, parameters);
    case "MAIN_GARDEN":
      return mainGardenRoofHeightMm(yMm, parameters);
    case "WING_INNER":
      return wingInnerRoofHeightMm(xMm, parameters);
    case "WING_OUTER":
      return wingOuterRoofHeightMm(xMm, parameters);
  }
}

export interface RoofMountTransform {
  readonly elevationMm: number;
  readonly rotationXRad: number;
  readonly rotationZRad: number;
}

/**
 * Returns the Babylon tilt for an object mounted flush to a roof face.
 * Plan Y maps to negative world Z, so main-roof faces tilt around X while
 * wing faces tilt around Z.
 */
export function roofMountTransform(
  faceId: RoofFaceId,
  xMm: number,
  yMm: number,
  parameters: JoinedRoofParameters = ACTIVE_JOINED_ROOF_PARAMETERS,
): RoofMountTransform {
  const mainPitch = Math.atan2(
    parameters.ridgeElevationMm - parameters.eavesElevationMm,
    parameters.mainRidgeYmm - parameters.frontEaveYmm,
  );
  const wingPitch = Math.atan2(
    parameters.ridgeElevationMm - parameters.eavesElevationMm,
    parameters.wingRidgeXmm - parameters.wingInnerEaveXmm,
  );

  switch (faceId) {
    case "MAIN_FRONT":
      return {
        elevationMm: roofHeightMm(faceId, xMm, yMm, parameters),
        rotationXRad: mainPitch,
        rotationZRad: 0,
      };
    case "MAIN_GARDEN":
      return {
        elevationMm: roofHeightMm(faceId, xMm, yMm, parameters),
        rotationXRad: -mainPitch,
        rotationZRad: 0,
      };
    case "WING_INNER":
      return {
        elevationMm: roofHeightMm(faceId, xMm, yMm, parameters),
        rotationXRad: 0,
        rotationZRad: wingPitch,
      };
    case "WING_OUTER":
      return {
        elevationMm: roofHeightMm(faceId, xMm, yMm, parameters),
        rotationXRad: 0,
        rotationZRad: -wingPitch,
      };
  }
}

export function deriveJoinedRoofGeometry(
  parameters: JoinedRoofParameters = ACTIVE_JOINED_ROOF_PARAMETERS,
): JoinedRoofGeometry {
  validateParameters(parameters);

  const eaves = parameters.eavesElevationMm;
  const ridge = parameters.ridgeElevationMm;
  const vertices: readonly RoofVertexMm[] = [
    vertex("FRONT_WEST_EAVE", parameters.minXmm, parameters.frontEaveYmm, eaves),
    vertex("FRONT_EAST_EAVE", parameters.maxXmm, parameters.frontEaveYmm, eaves),
    vertex("MAIN_WEST_RIDGE", parameters.minXmm, parameters.mainRidgeYmm, ridge),
    vertex("ROOF_JUNCTION", parameters.wingRidgeXmm, parameters.mainRidgeYmm, ridge),
    vertex("GARDEN_WEST_EAVE", parameters.minXmm, parameters.gardenEaveYmm, eaves),
    vertex(
      "VALLEY_EAVE",
      parameters.wingInnerEaveXmm,
      parameters.gardenEaveYmm,
      eaves,
    ),
    vertex(
      "WING_END_INNER_EAVE",
      parameters.wingInnerEaveXmm,
      parameters.wingEndYmm,
      eaves,
    ),
    vertex("WING_END_RIDGE", parameters.wingRidgeXmm, parameters.wingEndYmm, ridge),
    vertex("WING_END_OUTER_EAVE", parameters.maxXmm, parameters.wingEndYmm, eaves),
  ];

  const faces: readonly RoofFace[] = [
    face("MAIN_FRONT", [0, 1, 3, 2], [0, 1], "X"),
    face("MAIN_GARDEN", [2, 3, 5, 4], [2, 3], "X"),
    face("WING_INNER", [5, 3, 7, 6], [4, 5], "Y"),
    face("WING_OUTER", [3, 1, 8, 7], [6, 7], "Y"),
  ];

  const triangles: readonly RoofTriangle[] = [
    triangle("MAIN_FRONT", [0, 1, 3]),
    triangle("MAIN_FRONT", [0, 3, 2]),
    triangle("MAIN_GARDEN", [2, 3, 5]),
    triangle("MAIN_GARDEN", [2, 5, 4]),
    triangle("WING_INNER", [5, 3, 7]),
    triangle("WING_INNER", [5, 7, 6]),
    triangle("WING_OUTER", [3, 1, 8]),
    triangle("WING_OUTER", [3, 8, 7]),
  ];

  const ridges: readonly RoofLineFeature[] = [
    line("MAIN_RIDGE", "RIDGE", 2, 3),
    line("WING_RIDGE", "RIDGE", 3, 7),
  ];
  const valley = line("JOIN_VALLEY", "VALLEY", 5, 3);
  const hip = line("JOIN_HIP", "HIP", 3, 1);
  const gutters: readonly RoofLineFeature[] = [
    line("FRONT_GUTTER", "GUTTER", 0, 1),
    line("GARDEN_GUTTER", "GUTTER", 4, 5),
    line("WING_INNER_GUTTER", "GUTTER", 5, 6),
    line("WING_OUTER_GUTTER", "GUTTER", 1, 8),
  ];
  const gables: readonly RoofGable[] = [
    {
      id: "MAIN_WEST_GABLE",
      vertexIndices: [0, 2, 4],
      plane: { axis: "X", coordinateMm: parameters.minXmm },
    },
    {
      id: "WING_END_GABLE",
      vertexIndices: [6, 7, 8],
      plane: { axis: "Y", coordinateMm: parameters.wingEndYmm },
    },
  ];

  const seamSegments = faces.flatMap((roofFace) =>
    deriveFaceSeams(roofFace, vertices, parameters),
  );

  return {
    parameters,
    vertices,
    faces,
    triangles,
    ridges,
    valley,
    hip,
    gutters,
    gables,
    seamSegments,
    bounds: boundsOf(vertices),
    projectedAreaMm2: triangles.reduce(
      (total, roofTriangle) =>
        total + projectedTriangleAreaMm2(roofTriangle, vertices),
      0,
    ),
    surfaceAreaMm2: triangles.reduce(
      (total, roofTriangle) => total + triangleAreaMm2(roofTriangle, vertices),
      0,
    ),
  };
}

/**
 * Splits the visual roof at the covered wing porch.
 *
 * The architectural roof still ends at the documented 50 mm overhang. In the
 * rendered assembly, however, the P04 rake owns that end strip and the larch
 * soffit owns the porch ceiling. Clipping the generic metal/white surfaces at
 * those two construction joints removes coplanar and intersecting opaque
 * layers instead of relying on camera-dependent depth bias.
 */
export function deriveJoinedRoofRenderPlan(
  roof: JoinedRoofGeometry = deriveJoinedRoofGeometry(),
): JoinedRoofRenderPlan {
  const porch = HOUSE.porches.wingEnd;
  const roofTopEndYmm = porch.portalFrame.rakeBackFaceYmm;
  const genericUndersideEndYmm = porch.glazingFaceYmm;

  if (
    porch.frontYmm !== roofTopEndYmm ||
    genericUndersideEndYmm >= roofTopEndYmm ||
    roofTopEndYmm > roof.parameters.wingEndYmm ||
    roof.parameters.wingEndYmm > porch.portalFrame.rakeFrontFaceYmm
  ) {
    throw new Error("Invalid wing-porch roof finish partition");
  }

  const renderFace = (
    face: RoofFace,
    maximumWingYmm: number,
    purpose: "top" | "generic-underside",
  ): RoofRenderFace => {
    const wing = face.id === "WING_INNER" || face.id === "WING_OUTER";
    const renderVertex = (vertexIndex: number): RoofVertexMm => {
      const source = roof.vertices[vertexIndex];
      if (!wing || source.yMm <= maximumWingYmm) return source;
      return {
        ...source,
        id: `${source.id}_${purpose.toUpperCase()}_CLIP`,
        yMm: maximumWingYmm,
        elevationMm: roofHeightMm(
          face.id,
          source.xMm,
          maximumWingYmm,
          roof.parameters,
        ),
      };
    };
    const [first, second, third, fourth] = face.vertexIndices;
    const vertices = [
      renderVertex(first),
      renderVertex(second),
      renderVertex(third),
      renderVertex(fourth),
    ] as const;
    return {
      id: `${face.id}_${purpose.toUpperCase()}`,
      faceId: face.id,
      vertices,
    };
  };

  const topFaces = roof.faces.map((face) =>
    renderFace(face, roofTopEndYmm, "top"),
  );
  const genericUndersideFaces = roof.faces.map((face) =>
    renderFace(face, genericUndersideEndYmm, "generic-underside"),
  );
  const seamSegments = roof.seamSegments.filter(
    (segment) =>
      (segment.faceId !== "WING_INNER" &&
        segment.faceId !== "WING_OUTER") ||
      segment.coordinateMm < roofTopEndYmm,
  );

  return {
    topFaces,
    genericUndersideFaces,
    seamSegments,
    wingPorch: {
      roofTopEndYmm,
      genericUndersideEndYmm,
      larchSoffitStartYmm: porch.glazingFaceYmm,
      larchSoffitEndYmm: porch.frontYmm,
      portalRakeStartYmm: porch.portalFrame.rakeBackFaceYmm,
      portalRakeEndYmm: porch.portalFrame.rakeFrontFaceYmm,
    },
  };
}

function interpolateElevation(
  coordinateMm: number,
  startMm: number,
  endMm: number,
  startElevationMm: number,
  endElevationMm: number,
): number {
  return (
    startElevationMm +
    ((coordinateMm - startMm) / (endMm - startMm)) *
      (endElevationMm - startElevationMm)
  );
}

function vertex(
  id: string,
  xMm: number,
  yMm: number,
  elevationMm: number,
): RoofVertexMm {
  return { id, xMm, yMm, elevationMm };
}

function face(
  id: RoofFaceId,
  vertexIndices: readonly [number, number, number, number],
  triangleIndices: readonly [number, number],
  seamAxis: "X" | "Y",
): RoofFace {
  return { id, vertexIndices, triangleIndices, seamAxis };
}

function triangle(
  faceId: RoofFaceId,
  vertexIndices: readonly [number, number, number],
): RoofTriangle {
  return { faceId, vertexIndices };
}

function line(
  id: string,
  kind: RoofLineKind,
  startVertexIndex: number,
  endVertexIndex: number,
): RoofLineFeature {
  return { id, kind, startVertexIndex, endVertexIndex };
}

function deriveFaceSeams(
  roofFace: RoofFace,
  vertices: readonly RoofVertexMm[],
  parameters: JoinedRoofParameters,
): readonly RoofSeamSegment[] {
  const polygon = roofFace.vertexIndices.map((index) => vertices[index]);
  const seams: RoofSeamSegment[] = [];
  const startMm =
    roofFace.seamAxis === "X"
      ? parameters.minXmm + parameters.mainSeamInsetMm
      : parameters.frontEaveYmm + parameters.wingSeamInsetMm;
  const endMm =
    roofFace.seamAxis === "X" ? parameters.maxXmm : parameters.wingEndYmm;
  const spacingMm =
    roofFace.seamAxis === "X"
      ? parameters.mainSeamSpacingMm
      : parameters.wingSeamSpacingMm;

  for (let coordinateMm = startMm; coordinateMm < endMm; coordinateMm += spacingMm) {
    const clipped = clipAxisAlignedLine(polygon, roofFace.seamAxis, coordinateMm);
    if (clipped === null) continue;
    const [first, second] = clipped;
    const start = pointOnRoof(roofFace.id, first.xMm, first.yMm, parameters);
    const end = pointOnRoof(roofFace.id, second.xMm, second.yMm, parameters);
    seams.push({
      id: `${roofFace.id}_SEAM_${coordinateMm}`,
      faceId: roofFace.id,
      axis: roofFace.seamAxis,
      coordinateMm,
      start,
      end,
    });
  }
  return seams;
}

function pointOnRoof(
  faceId: RoofFaceId,
  xMm: number,
  yMm: number,
  parameters: JoinedRoofParameters,
): RoofPointMm {
  return {
    xMm,
    yMm,
    elevationMm: roofHeightMm(faceId, xMm, yMm, parameters),
  };
}

function clipAxisAlignedLine(
  polygon: readonly RoofPointMm[],
  axis: "X" | "Y",
  coordinateMm: number,
): readonly [RoofPointMm, RoofPointMm] | null {
  const intersections: RoofPointMm[] = [];
  for (let index = 0; index < polygon.length; index += 1) {
    const start = polygon[index];
    const end = polygon[(index + 1) % polygon.length];
    const startCoordinate = axis === "X" ? start.xMm : start.yMm;
    const endCoordinate = axis === "X" ? end.xMm : end.yMm;

    if (startCoordinate === endCoordinate) {
      if (coordinateMm === startCoordinate) {
        intersections.push(start, end);
      }
      continue;
    }
    const ratio = (coordinateMm - startCoordinate) / (endCoordinate - startCoordinate);
    if (ratio < 0 || ratio > 1) continue;
    intersections.push({
      xMm:
        axis === "X"
          ? coordinateMm
          : start.xMm + ratio * (end.xMm - start.xMm),
      yMm:
        axis === "Y"
          ? coordinateMm
          : start.yMm + ratio * (end.yMm - start.yMm),
      elevationMm:
        start.elevationMm + ratio * (end.elevationMm - start.elevationMm),
    });
  }

  const unique = intersections.filter(
    (candidate, index) =>
      intersections.findIndex(
        (point) =>
          Math.abs(point.xMm - candidate.xMm) < 1e-7 &&
          Math.abs(point.yMm - candidate.yMm) < 1e-7,
      ) === index,
  );
  if (unique.length < 2) return null;
  unique.sort((left, right) =>
    axis === "X" ? left.yMm - right.yMm : left.xMm - right.xMm,
  );
  const first = unique[0];
  const last = unique[unique.length - 1];
  if (Math.hypot(last.xMm - first.xMm, last.yMm - first.yMm) < 1e-7) {
    return null;
  }
  return [first, last];
}

function projectedTriangleAreaMm2(
  triangleValue: RoofTriangle,
  vertices: readonly RoofVertexMm[],
): number {
  const [first, second, third] = triangleValue.vertexIndices.map(
    (index) => vertices[index],
  );
  return (
    Math.abs(
      (second.xMm - first.xMm) * (third.yMm - first.yMm) -
        (second.yMm - first.yMm) * (third.xMm - first.xMm),
    ) / 2
  );
}

function triangleAreaMm2(
  triangleValue: RoofTriangle,
  vertices: readonly RoofVertexMm[],
): number {
  const [first, second, third] = triangleValue.vertexIndices.map(
    (index) => vertices[index],
  );
  const firstVector = [
    second.xMm - first.xMm,
    second.yMm - first.yMm,
    second.elevationMm - first.elevationMm,
  ] as const;
  const secondVector = [
    third.xMm - first.xMm,
    third.yMm - first.yMm,
    third.elevationMm - first.elevationMm,
  ] as const;
  const cross = [
    firstVector[1] * secondVector[2] - firstVector[2] * secondVector[1],
    firstVector[2] * secondVector[0] - firstVector[0] * secondVector[2],
    firstVector[0] * secondVector[1] - firstVector[1] * secondVector[0],
  ] as const;
  return Math.hypot(...cross) / 2;
}

function boundsOf(vertices: readonly RoofVertexMm[]): RoofBoundsMm {
  return {
    minXmm: Math.min(...vertices.map(({ xMm }) => xMm)),
    maxXmm: Math.max(...vertices.map(({ xMm }) => xMm)),
    minYmm: Math.min(...vertices.map(({ yMm }) => yMm)),
    maxYmm: Math.max(...vertices.map(({ yMm }) => yMm)),
    minElevationMm: Math.min(...vertices.map(({ elevationMm }) => elevationMm)),
    maxElevationMm: Math.max(...vertices.map(({ elevationMm }) => elevationMm)),
  };
}

function validateParameters(parameters: JoinedRoofParameters): void {
  const values = Object.values(parameters);
  if (values.some((value) => !Number.isFinite(value))) {
    throw new Error("Strešná geometria obsahuje neplatnú číselnú hodnotu.");
  }
  if (
    !(
      parameters.minXmm < parameters.wingInnerEaveXmm &&
      parameters.wingInnerEaveXmm < parameters.wingRidgeXmm &&
      parameters.wingRidgeXmm < parameters.maxXmm &&
      parameters.frontEaveYmm < parameters.mainRidgeYmm &&
      parameters.mainRidgeYmm < parameters.gardenEaveYmm &&
      parameters.gardenEaveYmm < parameters.wingEndYmm &&
      parameters.eavesElevationMm < parameters.ridgeElevationMm &&
      parameters.mainSeamInsetMm >= 0 &&
      parameters.wingSeamInsetMm >= 0 &&
      parameters.mainSeamSpacingMm > 0 &&
      parameters.wingSeamSpacingMm > 0
    )
  ) {
    throw new Error("Strešná geometria nemá platné usporiadanie bodov a rozstupov.");
  }
}
