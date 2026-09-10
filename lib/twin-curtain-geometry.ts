/** Authored gathered side curtain, in mm: X across the panel, Y up, Z depth.
 * Clockwise outward triangles match Babylon's left-handed mesh convention.
 * This is a static fabric interpretation, not a measured textile simulation.
 */
export interface CurtainGeometry {
  readonly positionsMm: number[];
  readonly normals: number[];
  /** Physical UVs: one texture repeat per metre of unfolded fabric. */
  readonly uvs: number[];
  readonly indices: number[];
  readonly foldPitchMm: number;
  readonly foldDepthMm: number;
  readonly thicknessMm: number;
  readonly horizontalSegments: number;
  readonly verticalSegments: number;
}

type V3 = readonly [number, number, number];
const subtract = (a: V3, b: V3): V3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const unit = (v: V3): V3 => {
  const length = Math.hypot(...v);
  return [v[0] / length, v[1] / length, v[2] / length];
};

export function createFoldedCurtainGeometry(widthMm: number, heightMm: number): CurtainGeometry {
  if (!Number.isFinite(widthMm) || !Number.isFinite(heightMm) || widthMm < 120 || heightMm < 200 || heightMm > 4000) {
    throw new RangeError("Gathered curtain requires finite width >=120 mm and height 200–4000 mm");
  }
  const thicknessMm = 0.7;
  const foldDepthMm = 40;
  // Half cycles end at a crest or trough with zero lateral derivative, keeping
  // both shell edges at the exact source width after the normal offset.
  const halfWaves = Math.round(widthMm / (67.5 / 2));
  const horizontalSegments = halfWaves * 4;
  const verticalSegments = 2;
  const triangles = 4 * horizontalSegments * verticalSegments + 4 * (horizontalSegments + verticalSegments);
  if (triangles > 1000) throw new RangeError("Gathered side curtain exceeds the 1000-triangle budget");
  const positionsMm: number[] = [], normals: number[] = [], uvs: number[] = [], indices: number[] = [];
  const middle: V3[] = [], surfaceNormals: V3[] = [], surfaceU: number[] = [];
  const stride = horizontalSegments + 1;

  for (let row = 0; row <= verticalSegments; row += 1) {
    const t = row / verticalSegments;
    const smooth = t * t * (3 - 2 * t);
    const amplitude = foldDepthMm / 2 * (1 - 0.06 * smooth);
    const amplitudeT = -foldDepthMm / 2 * 0.06 * 6 * t * (1 - t);
    let fabricLength = 0;
    for (let column = 0; column <= horizontalSegments; column += 1) {
      const s = column / horizontalSegments;
      const phase = Math.PI * halfWaves * s;
      const sine = column % 4 === 0 ? 0 : Math.sin(phase);
      const cosine = Math.cos(phase);
      const phaseS = Math.PI * halfWaves;
      // At most 2 mm of hem lift; the lowest points and top remain at their
      // original elevations. The lower pleats open by only 6% under gravity.
      const hem = 1 - cosine;
      const y = -heightMm / 2 + heightMm * t + hem * (1 - t) ** 3;
      const yS = sine * phaseS * (1 - t) ** 3;
      const yT = heightMm - 3 * hem * (1 - t) ** 2;
      const zS = -amplitude * sine * phaseS;
      const zT = amplitudeT * cosine;
      const p: V3 = [(s - 0.5) * widthMm, y, amplitude * cosine];
      const n = unit(cross([widthMm, yS, zS], [0, yT, zT]));
      if (column > 0) fabricLength += Math.hypot(...subtract(p, middle[middle.length - 1]));
      middle.push(p); surfaceNormals.push(n); surfaceU.push(fabricLength / 1000);
    }
  }

  const gridSize = middle.length;
  for (const side of [1, -1]) {
    for (let i = 0; i < gridSize; i += 1) {
      const p = middle[i], n = surfaceNormals[i];
      positionsMm.push(...p.map((v, axis) => v + side * thicknessMm / 2 * n[axis]));
      normals.push(...n.map(v => side * v));
      uvs.push(surfaceU[i], Math.floor(i / stride) / verticalSegments * heightMm / 1000);
    }
    const start = side === 1 ? 0 : gridSize;
    for (let row = 0; row < verticalSegments; row += 1) {
      for (let column = 0; column < horizontalSegments; column += 1) {
        const a = start + row * stride + column, b = a + 1, d = a + stride, c = d + 1;
        indices.push(...(side === 1 ? [a, c, b, a, d, c] : [a, b, c, a, c, d]));
      }
    }
  }

  // Closed 0.7 mm shell. Edge vertices intentionally split the fabric normals
  // and UVs; their positions exactly reuse the two surfaces, without cracks.
  const boundary: number[] = [];
  for (let x = 0; x < horizontalSegments; x += 1) boundary.push(x);
  for (let y = 0; y < verticalSegments; y += 1) boundary.push(y * stride + horizontalSegments);
  for (let x = horizontalSegments; x > 0; x -= 1) boundary.push(verticalSegments * stride + x);
  for (let y = verticalSegments; y > 0; y -= 1) boundary.push(y * stride);
  const point = (i: number): V3 => [positionsMm[i * 3], positionsMm[i * 3 + 1], positionsMm[i * 3 + 2]];
  let perimeterMm = 0;
  for (let i = 0; i < boundary.length; i += 1) {
    const a = boundary[i], b = boundary[(i + 1) % boundary.length];
    const corners = [point(a), point(b), point(b + gridSize), point(a + gridSize)];
    const edgeLength = Math.hypot(...subtract(middle[b], middle[a]));
    const n1 = cross(subtract(corners[0], corners[1]), subtract(corners[2], corners[1]));
    const n2 = cross(subtract(corners[0], corners[2]), subtract(corners[3], corners[2]));
    const n = unit([n1[0] + n2[0], n1[1] + n2[1], n1[2] + n2[2]]);
    const start = positionsMm.length / 3;
    for (const p of corners) { positionsMm.push(...p); normals.push(...n); }
    uvs.push(perimeterMm / 1000, 0, (perimeterMm + edgeLength) / 1000, 0,
      (perimeterMm + edgeLength) / 1000, thicknessMm / 1000, perimeterMm / 1000, thicknessMm / 1000);
    indices.push(start, start + 1, start + 2, start, start + 2, start + 3);
    perimeterMm += edgeLength;
  }
  return { positionsMm, normals, uvs, indices, foldPitchMm: widthMm * 2 / halfWaves,
    foldDepthMm, thicknessMm, horizontalSegments, verticalSegments };
}
