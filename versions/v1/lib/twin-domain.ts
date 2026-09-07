/**
 * Engine-free domain primitives for the Březí digital twin.
 *
 * Stored geometry uses finite integer millimetres. Rendering engines may
 * derive metres/floats at their boundary, but those values are never the
 * canonical model.
 */

declare const millimetresBrand: unique symbol;
declare const squareMillimetresBrand: unique symbol;
declare const cubicMillimetresBrand: unique symbol;

export type Millimetres = number & {
  readonly [millimetresBrand]: "Millimetres";
};

export type SquareMillimetres = number & {
  readonly [squareMillimetresBrand]: "SquareMillimetres";
};

export type CubicMillimetres = number & {
  readonly [cubicMillimetresBrand]: "CubicMillimetres";
};

export const PROVENANCE_KINDS = {
  CADASTRE_CURRENT: "CADASTRE_CURRENT",
  PROJECT_DESIGN: "PROJECT_DESIGN",
  PROVIDER_MAP: "PROVIDER_MAP",
  EMAIL_AS_BUILT_REFERENCE: "EMAIL_AS_BUILT_REFERENCE",
  INFERRED: "INFERRED",
} as const;

export type ProvenanceKind =
  (typeof PROVENANCE_KINDS)[keyof typeof PROVENANCE_KINDS];

export interface SourceRef {
  readonly id: string;
  readonly provenance: ProvenanceKind;
  readonly title: string;
  readonly locator: string;
  readonly observedAt?: string;
  readonly featureId?: string;
  readonly nationalCadastralReference?: string;
  readonly note?: string;
}

export const TWIN_LAYER_IDS = [
  "parcel",
  "context",
  "road",
  "building",
  "foundations",
  "utilities",
] as const;

export type TwinLayerId = (typeof TWIN_LAYER_IDS)[number];

export interface TwinLayerDefinition {
  readonly id: TwinLayerId;
  readonly label: string;
  readonly order: number;
}

export const TWIN_LAYERS: readonly TwinLayerDefinition[] = Object.freeze([
  { id: "parcel", label: "Parcela", order: 0 },
  { id: "context", label: "Okolie", order: 1 },
  { id: "road", label: "Komunikácia", order: 2 },
  { id: "building", label: "Dom", order: 3 },
  { id: "foundations", label: "Základy", order: 4 },
  { id: "utilities", label: "Inžinierske siete", order: 5 },
]);

export interface PointMm {
  readonly xMm: Millimetres;
  readonly yMm: Millimetres;
}

export type LinearRingMm = readonly PointMm[];
export type PolylineMm = readonly PointMm[];

export interface BoundsMm {
  readonly minXmm: Millimetres;
  readonly minYmm: Millimetres;
  readonly maxXmm: Millimetres;
  readonly maxYmm: Millimetres;
  readonly widthMm: Millimetres;
  readonly heightMm: Millimetres;
}

export interface PolygonMm {
  readonly crs: "EPSG:5514" | "LOCAL_MM";
  readonly outerRing: LinearRingMm;
  readonly holes?: readonly LinearRingMm[];
}

function labelSuffix(label: string): string {
  return label ? ` (${label})` : "";
}

function assertFiniteInteger(value: number, label: string): void {
  if (!Number.isFinite(value) || !Number.isInteger(value)) {
    throw new TypeError(
      `Expected a finite integer millimetre value${labelSuffix(label)}.`,
    );
  }
  if (!Number.isSafeInteger(value)) {
    throw new RangeError(
      `Millimetre value is outside JavaScript's safe integer range${labelSuffix(label)}.`,
    );
  }
}

export function coordinateMm(value: number, label = "coordinate"): Millimetres {
  assertFiniteInteger(value, label);
  return value as Millimetres;
}

export function positiveMm(value: number, label = "dimension"): Millimetres {
  assertFiniteInteger(value, label);
  if (value <= 0) {
    throw new RangeError(
      `Expected a positive millimetre value${labelSuffix(label)}.`,
    );
  }
  return value as Millimetres;
}

export function pointMm(xMm: number, yMm: number): PointMm {
  return Object.freeze({
    xMm: coordinateMm(xMm, "x"),
    yMm: coordinateMm(yMm, "y"),
  });
}

function assertPoint(point: PointMm, label: string): void {
  if (!point || typeof point !== "object") {
    throw new TypeError(`Expected a point${labelSuffix(label)}.`);
  }
  coordinateMm(point.xMm, `${label}.xMm`);
  coordinateMm(point.yMm, `${label}.yMm`);
}

function samePoint(left: PointMm, right: PointMm): boolean {
  return left.xMm === right.xMm && left.yMm === right.yMm;
}

function ringVertices(ring: LinearRingMm): readonly PointMm[] {
  if (!Array.isArray(ring) || ring.length < 3) {
    throw new RangeError("A polygon ring requires at least three vertices.");
  }
  ring.forEach((point, index) => assertPoint(point, `ring[${index}]`));
  const vertices =
    ring.length > 3 && samePoint(ring[0], ring[ring.length - 1])
      ? ring.slice(0, -1)
      : ring.slice();
  const unique = new Set(vertices.map(({ xMm, yMm }) => `${xMm}:${yMm}`));
  if (unique.size < 3) {
    throw new RangeError("A polygon ring requires three distinct vertices.");
  }
  return vertices;
}

function assertPolyline(line: PolylineMm): void {
  if (!Array.isArray(line) || line.length < 2) {
    throw new RangeError("A polyline requires at least two points.");
  }
  line.forEach((point, index) => assertPoint(point, `line[${index}]`));
}

/**
 * Shoelace area translated to the first vertex before multiplication. The
 * translation prevents loss of precision with large national-grid ordinates.
 */
export function ringAreaMm2(ring: LinearRingMm): SquareMillimetres {
  const vertices = ringVertices(ring);
  const origin = vertices[0];
  let twiceSignedArea = 0;

  for (let index = 0; index < vertices.length; index += 1) {
    const current = vertices[index];
    const next = vertices[(index + 1) % vertices.length];
    const currentX = current.xMm - origin.xMm;
    const currentY = current.yMm - origin.yMm;
    const nextX = next.xMm - origin.xMm;
    const nextY = next.yMm - origin.yMm;
    twiceSignedArea += currentX * nextY - nextX * currentY;
  }

  if (!Number.isSafeInteger(twiceSignedArea)) {
    throw new RangeError("Polygon area exceeds the safe integer range.");
  }
  if (twiceSignedArea === 0) {
    throw new RangeError("A polygon ring must enclose a positive area.");
  }
  return (Math.abs(twiceSignedArea) / 2) as SquareMillimetres;
}

export function polygonAreaMm2(polygon: PolygonMm): SquareMillimetres {
  const outerArea = ringAreaMm2(polygon.outerRing);
  const holesArea = (polygon.holes ?? []).reduce(
    (sum, hole) => sum + ringAreaMm2(hole),
    0,
  );
  const area = outerArea - holesArea;
  if (!(area > 0)) {
    throw new RangeError("Polygon holes must not consume the outer ring area.");
  }
  return area as SquareMillimetres;
}

export function squareMillimetresToSquareMetres(area: number): number {
  if (!Number.isFinite(area) || area <= 0) {
    throw new RangeError("Area must be finite and positive.");
  }
  return area / 1_000_000;
}

export function polygonAreaSquareMetres(polygon: PolygonMm): number {
  return squareMillimetresToSquareMetres(polygonAreaMm2(polygon));
}

export function polygonBoundsMm(polygon: PolygonMm): BoundsMm {
  const outer = ringVertices(polygon.outerRing);
  let minX = outer[0].xMm as number;
  let minY = outer[0].yMm as number;
  let maxX = minX;
  let maxY = minY;

  for (const point of outer.slice(1)) {
    minX = Math.min(minX, point.xMm);
    minY = Math.min(minY, point.yMm);
    maxX = Math.max(maxX, point.xMm);
    maxY = Math.max(maxY, point.yMm);
  }

  return Object.freeze({
    minXmm: coordinateMm(minX, "bounds.minX"),
    minYmm: coordinateMm(minY, "bounds.minY"),
    maxXmm: coordinateMm(maxX, "bounds.maxX"),
    maxYmm: coordinateMm(maxY, "bounds.maxY"),
    widthMm: positiveMm(maxX - minX, "bounds.width"),
    heightMm: positiveMm(maxY - minY, "bounds.height"),
  });
}

/** Returns total polyline length rounded once to the canonical millimetre. */
export function lineLengthMm(line: PolylineMm): Millimetres {
  assertPolyline(line);
  let length = 0;
  for (let index = 1; index < line.length; index += 1) {
    length += Math.hypot(
      line[index].xMm - line[index - 1].xMm,
      line[index].yMm - line[index - 1].yMm,
    );
  }
  if (!(length > 0)) {
    throw new RangeError("A polyline must have a positive length.");
  }
  return positiveMm(Math.round(length), "line length");
}

export const CONSTRUCTION_STATES = ["DESIGNED", "PLANNED", "AS_BUILT"] as const;
export type ConstructionState = (typeof CONSTRUCTION_STATES)[number];

export interface FoundationStrip {
  readonly id: string;
  readonly name: string;
  readonly layer: "foundations";
  readonly path: PolylineMm;
  readonly widthMm: Millimetres;
  readonly heightMm: Millimetres;
  readonly baseElevationMm: Millimetres;
  readonly concreteType: string;
  readonly status: ConstructionState;
  readonly sourceRefs: readonly SourceRef[];
}

export interface FoundationStripInput {
  readonly id: string;
  readonly name: string;
  readonly path: readonly { readonly xMm: number; readonly yMm: number }[];
  readonly widthMm: number;
  readonly heightMm: number;
  readonly baseElevationMm: number;
  readonly concreteType: string;
  readonly status: ConstructionState;
  readonly sourceRefs: readonly SourceRef[];
}

function assertNonEmpty(value: string, label: string): void {
  if (typeof value !== "string" || value.trim() === "") {
    throw new TypeError(`${label} must be a non-empty string.`);
  }
}

function validateSourceRef(source: SourceRef, label: string): void {
  if (!source || typeof source !== "object") {
    throw new TypeError(`${label} must be a source reference.`);
  }
  assertNonEmpty(source.id, `${label}.id`);
  assertNonEmpty(source.title, `${label}.title`);
  assertNonEmpty(source.locator, `${label}.locator`);
  if (!Object.values(PROVENANCE_KINDS).includes(source.provenance)) {
    throw new RangeError(`${label}.provenance is not supported.`);
  }
}

export function createFoundationStrip(input: FoundationStripInput): FoundationStrip {
  assertNonEmpty(input.id, "Foundation id");
  assertNonEmpty(input.name, "Foundation name");
  assertNonEmpty(input.concreteType, "Concrete type");
  if (!CONSTRUCTION_STATES.includes(input.status)) {
    throw new RangeError("Foundation status is not supported.");
  }
  input.sourceRefs.forEach((source, index) =>
    validateSourceRef(source, `sourceRefs[${index}]`),
  );

  const path = Object.freeze(
    input.path.map((point) => pointMm(point.xMm, point.yMm)),
  );
  assertPolyline(path);
  // Reject a valid-looking path whose total length is nevertheless zero.
  lineLengthMm(path);

  return Object.freeze({
    id: input.id,
    name: input.name,
    layer: "foundations" as const,
    path,
    widthMm: positiveMm(input.widthMm, "foundation width"),
    heightMm: positiveMm(input.heightMm, "foundation height"),
    baseElevationMm: coordinateMm(
      input.baseElevationMm,
      "foundation base elevation",
    ),
    concreteType: input.concreteType,
    status: input.status,
    sourceRefs: Object.freeze(input.sourceRefs.slice()),
  });
}

export function foundationVolumeMm3(
  foundation: Pick<FoundationStrip, "path" | "widthMm" | "heightMm">,
): CubicMillimetres {
  const length = lineLengthMm(foundation.path);
  const width = positiveMm(foundation.widthMm, "foundation width");
  const height = positiveMm(foundation.heightMm, "foundation height");
  const volume = length * width * height;
  if (!Number.isSafeInteger(volume) || volume <= 0) {
    throw new RangeError("Foundation volume exceeds the safe integer range.");
  }
  return volume as CubicMillimetres;
}

export function cubicMillimetresToCubicMetres(volume: number): number {
  if (!Number.isFinite(volume) || volume <= 0) {
    throw new RangeError("Volume must be finite and positive.");
  }
  return volume / 1_000_000_000;
}

export function foundationVolumeCubicMetres(
  foundation: Pick<FoundationStrip, "path" | "widthMm" | "heightMm">,
): number {
  return cubicMillimetresToCubicMetres(foundationVolumeMm3(foundation));
}

export interface ChangeMetadata {
  readonly id: string;
  readonly changedAt: string;
  readonly reason: string;
  readonly sourceRef: SourceRef;
}

export interface FoundationWidthHistoryEntry {
  readonly type: "FOUNDATION_WIDTH_CHANGED";
  readonly id: string;
  readonly foundationId: string;
  readonly beforeWidthMm: Millimetres;
  readonly afterWidthMm: Millimetres;
  readonly changedAt: string;
  readonly reason: string;
  readonly sourceRef: SourceRef;
  readonly appliedRevision: number;
  readonly status: "APPLIED" | "UNDONE";
  readonly undoneRevision?: number;
}

export interface TwinDomainState {
  readonly revision: number;
  readonly foundations: readonly FoundationStrip[];
  readonly history: readonly FoundationWidthHistoryEntry[];
}

function assertChangeMetadata(metadata: ChangeMetadata): void {
  assertNonEmpty(metadata.id, "Change id");
  assertNonEmpty(metadata.changedAt, "Change timestamp");
  assertNonEmpty(metadata.reason, "Change reason");
  if (Number.isNaN(Date.parse(metadata.changedAt))) {
    throw new RangeError("Change timestamp must be an ISO-compatible date.");
  }
  validateSourceRef(metadata.sourceRef, "Change source");
}

export function createTwinDomainState(
  foundations: readonly FoundationStrip[],
): TwinDomainState {
  const ids = new Set<string>();
  for (const foundation of foundations) {
    if (ids.has(foundation.id)) {
      throw new RangeError(`Duplicate foundation id: ${foundation.id}`);
    }
    ids.add(foundation.id);
    positiveMm(foundation.widthMm, `${foundation.id}.widthMm`);
    positiveMm(foundation.heightMm, `${foundation.id}.heightMm`);
    lineLengthMm(foundation.path);
  }
  return Object.freeze({
    revision: 0,
    foundations: Object.freeze(foundations.slice()),
    history: Object.freeze([]),
  });
}

export function updateFoundationWidth(
  state: TwinDomainState,
  foundationId: string,
  nextWidthMm: number,
  metadata: ChangeMetadata,
): TwinDomainState {
  assertNonEmpty(foundationId, "Foundation id");
  assertChangeMetadata(metadata);
  const width = positiveMm(nextWidthMm, "foundation width");
  const foundationIndex = state.foundations.findIndex(
    (foundation) => foundation.id === foundationId,
  );
  if (foundationIndex < 0) {
    throw new RangeError(`Unknown foundation: ${foundationId}`);
  }
  if (state.history.some((entry) => entry.id === metadata.id)) {
    throw new RangeError(`Duplicate change id: ${metadata.id}`);
  }
  const current = state.foundations[foundationIndex];
  if (current.widthMm === width) return state;

  const revision = state.revision + 1;
  const nextFoundation = Object.freeze({ ...current, widthMm: width });
  const foundations = state.foundations.slice();
  foundations[foundationIndex] = nextFoundation;
  const entry: FoundationWidthHistoryEntry = Object.freeze({
    type: "FOUNDATION_WIDTH_CHANGED",
    id: metadata.id,
    foundationId,
    beforeWidthMm: current.widthMm,
    afterWidthMm: width,
    changedAt: metadata.changedAt,
    reason: metadata.reason,
    sourceRef: metadata.sourceRef,
    appliedRevision: revision,
    status: "APPLIED",
  });

  return Object.freeze({
    revision,
    foundations: Object.freeze(foundations),
    history: Object.freeze([...state.history, entry]),
  });
}

/**
 * Reverts the newest still-applied width change. History is retained and the
 * reverted entry is marked UNDONE so the audit trail remains truthful.
 */
export function undoLastFoundationWidthChange(
  state: TwinDomainState,
  foundationId?: string,
): TwinDomainState {
  let historyIndex = -1;
  for (let index = state.history.length - 1; index >= 0; index -= 1) {
    const entry = state.history[index];
    if (
      entry.status === "APPLIED" &&
      (foundationId === undefined || entry.foundationId === foundationId)
    ) {
      historyIndex = index;
      break;
    }
  }
  if (historyIndex < 0) return state;

  const entry = state.history[historyIndex];
  const foundationIndex = state.foundations.findIndex(
    (foundation) => foundation.id === entry.foundationId,
  );
  if (foundationIndex < 0) {
    throw new RangeError(`History references unknown foundation: ${entry.foundationId}`);
  }
  const current = state.foundations[foundationIndex];
  if (current.widthMm !== entry.afterWidthMm) {
    throw new RangeError(
      `Cannot undo ${entry.id}: current width no longer matches its applied value.`,
    );
  }

  const revision = state.revision + 1;
  const foundations = state.foundations.slice();
  foundations[foundationIndex] = Object.freeze({
    ...current,
    widthMm: entry.beforeWidthMm,
  });
  const history = state.history.map((item, index) =>
    index === historyIndex
      ? Object.freeze({
          ...item,
          status: "UNDONE" as const,
          undoneRevision: revision,
        })
      : item,
  );

  return Object.freeze({
    revision,
    foundations: Object.freeze(foundations),
    history: Object.freeze(history),
  });
}

export const CUZK_CADASTRE_WFS_SOURCE: SourceRef = Object.freeze({
  id: "cuzk:inspire-cp-wfs",
  provenance: PROVENANCE_KINDS.CADASTRE_CURRENT,
  title: "ČÚZK INSPIRE - Cadastral Parcels WFS",
  locator: "https://services.cuzk.gov.cz/wfs/inspire-cp-wfs.asp",
  observedAt: "2026-08-18",
});

export const CUZK_PARCEL_6012_26_SOURCE: SourceRef = Object.freeze({
  ...CUZK_CADASTRE_WFS_SOURCE,
  id: "cuzk:CP.94487880010",
  featureId: "CP.94487880010",
  nationalCadastralReference: "613908-6012/26",
  note: "Live EPSG:5514 outer ring; registered area is 753 m².",
});

export const S_JTSK_LOCAL_ORIGIN_MM: PointMm = pointMm(
  -606_703_380,
  -1_202_038_880,
);

export function sjtskMetresToMm(valueMetres: number, label = "S-JTSK ordinate") {
  if (!Number.isFinite(valueMetres)) {
    throw new TypeError(`${label} must be finite.`);
  }
  const scaled = valueMetres * 1_000;
  const rounded = Math.round(scaled);
  if (Math.abs(scaled - rounded) > 1e-6) {
    throw new RangeError(`${label} must resolve exactly to integer millimetres.`);
  }
  return coordinateMm(rounded, label);
}

export function sjtskPointMetresToMm(
  xMetres: number,
  yMetres: number,
): PointMm {
  return pointMm(
    sjtskMetresToMm(xMetres, "S-JTSK x"),
    sjtskMetresToMm(yMetres, "S-JTSK y"),
  );
}

export function sjtskToLocalMm(
  point: PointMm,
  origin: PointMm = S_JTSK_LOCAL_ORIGIN_MM,
): PointMm {
  assertPoint(point, "S-JTSK point");
  assertPoint(origin, "S-JTSK origin");
  return pointMm(point.xMm - origin.xMm, point.yMm - origin.yMm);
}

export function localToSjtskMm(
  point: PointMm,
  origin: PointMm = S_JTSK_LOCAL_ORIGIN_MM,
): PointMm {
  assertPoint(point, "local point");
  assertPoint(origin, "S-JTSK origin");
  return pointMm(point.xMm + origin.xMm, point.yMm + origin.yMm);
}

export function polygonToLocalMm(
  polygon: PolygonMm,
  origin: PointMm = S_JTSK_LOCAL_ORIGIN_MM,
): PolygonMm {
  return Object.freeze({
    crs: "LOCAL_MM" as const,
    outerRing: Object.freeze(
      polygon.outerRing.map((point) => sjtskToLocalMm(point, origin)),
    ),
    holes: polygon.holes
      ? Object.freeze(
          polygon.holes.map((hole) =>
            Object.freeze(hole.map((point) => sjtskToLocalMm(point, origin))),
          ),
        )
      : undefined,
  });
}

export const BREZI_6012_26_SJTSK_RING_MM: LinearRingMm = Object.freeze([
  pointMm(-606_686_450, -1_202_035_560),
  pointMm(-606_686_040, -1_202_034_950),
  pointMm(-606_685_750, -1_202_034_140),
  pointMm(-606_685_770, -1_202_032_930),
  pointMm(-606_686_170, -1_202_031_950),
  pointMm(-606_686_710, -1_202_031_330),
  pointMm(-606_702_850, -1_202_017_130),
  pointMm(-606_723_140, -1_202_041_980),
  pointMm(-606_705_150, -1_202_056_660),
  pointMm(-606_686_450, -1_202_035_560),
]);

export interface ParcelFeature {
  readonly id: string;
  readonly layer: "parcel";
  readonly parcelNumber: string;
  readonly nationalCadastralReference: string;
  readonly cadastralUnit: string;
  readonly registeredAreaSquareMetres: number;
  readonly geometry: PolygonMm;
  readonly sourceRefs: readonly SourceRef[];
}

export const BREZI_6012_26_PARCEL: ParcelFeature = Object.freeze({
  id: "parcel:613908-6012/26",
  layer: "parcel",
  parcelNumber: "6012/26",
  nationalCadastralReference: "613908-6012/26",
  cadastralUnit: "Březí u Mikulova",
  registeredAreaSquareMetres: 753,
  geometry: Object.freeze({
    crs: "EPSG:5514" as const,
    outerRing: BREZI_6012_26_SJTSK_RING_MM,
  }),
  sourceRefs: Object.freeze([CUZK_PARCEL_6012_26_SOURCE]),
});

export const BREZI_6012_26_LOCAL_POLYGON_MM = polygonToLocalMm(
  BREZI_6012_26_PARCEL.geometry,
);

export interface NearbyParcelReference {
  readonly id: string;
  readonly layer: "context";
  readonly parcelNumber: string;
  readonly geometryStatus: "IDENTIFIER_ONLY";
  readonly sourceRefs: readonly SourceRef[];
}

/**
 * Nearby identifiers observed around the target parcel. Their rings are not
 * embedded until individually verified from WFS; no inferred geometry is used.
 */
export const NEARBY_PARCEL_REFERENCES: readonly NearbyParcelReference[] =
  Object.freeze(
    ["6012/24", "6012/25", "6012/27", "6013", "6014", "6015"].map(
      (parcelNumber) =>
        Object.freeze({
          id: `parcel-context:${parcelNumber}`,
          layer: "context" as const,
          parcelNumber,
          geometryStatus: "IDENTIFIER_ONLY" as const,
          sourceRefs: Object.freeze([CUZK_CADASTRE_WFS_SOURCE]),
        }),
    ),
  );
