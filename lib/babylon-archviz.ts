import type { AssetContainer } from "@babylonjs/core/assetContainer";
import { VertexBuffer } from "@babylonjs/core/Buffers/buffer";
import { LoadAssetContainerAsync } from "@babylonjs/core/Loading/sceneLoader";
import type { Material } from "@babylonjs/core/Materials/material";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { Matrix, Quaternion, Vector3 } from "@babylonjs/core/Maths/math.vector";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { Mesh } from "@babylonjs/core/Meshes/mesh";
import { TransformNode } from "@babylonjs/core/Meshes/transformNode";
import type { Node } from "@babylonjs/core/node";
import type { Scene } from "@babylonjs/core/scene";
import "@babylonjs/loaders/glTF";

import type { LayerId } from "./twin-site";
import { warmLivingMaterial } from "./babylon-living-palette";

export type ArchvizStatus = "loading" | "ready" | "fallback";

interface SourceExtras {
  source_name?: string;
  source_id?: string;
  source_bounds_mm?: string | { min: number[]; max: number[] };
  source_group?: string;
  source_enabled?: boolean;
  visualization_only?: boolean;
}

interface ArchvizManifest {
  files: { file: string; kind: string; bytes: number }[];
  appearanceHiddenSourceNames?: string[];
}

interface GrassPlacements {
  stride: number;
  placements: number[];
  desktopCount: number;
  mobileCount: number;
}

interface NativeSource {
  mesh: AbstractMesh;
  layer: LayerId;
  initialWorld: Matrix;
  minimum: Vector3;
  maximum: Vector3;
  technicalVisibility: number;
  originalVisibility: number;
  castsShadow: boolean;
  cullDuplicatedFaces: boolean;
}

interface ArchvizHost {
  scene: Scene;
  layers: ReadonlyMap<LayerId, AbstractMesh[]>;
  technicalVisibility: (mesh: AbstractMesh) => number;
  realisticMaterial: (mesh: AbstractMesh) => Material | null;
  castsShadow: (mesh: AbstractMesh) => boolean;
  setShadow: (mesh: AbstractMesh, enabled: boolean) => void;
  register: (mesh: AbstractMesh, layer: LayerId, entityId?: string) => void;
  unregister: (mesh: AbstractMesh) => void;
  onStatus: (status: ArchvizStatus) => void;
  compact: boolean;
}

/** Babylon DOUBLESIDE appends the same vertices with opposite normals. */
export function hasDuplicatedBackFaces(mesh: AbstractMesh) {
  const positions = mesh.getVerticesData(VertexBuffer.PositionKind);
  const normals = mesh.getVerticesData(VertexBuffer.NormalKind);
  if (!positions?.length || positions.length % 6 !== 0 || normals?.length !== positions.length) return false;
  const half = positions.length / 2;
  for (let i = 0; i < half; i++) {
    if (Math.abs(positions[i] - positions[i + half]) > 1e-6 ||
      Math.abs(normals[i] + normals[i + half]) > 1e-6) return false;
  }
  return true;
}

/** Isolate the culling fix from other meshes sharing an exported material. */
export function archvizMaterialForFaces(
  material: PBRMaterial,
  cullDuplicatedFaces: boolean,
  cache: Map<PBRMaterial, PBRMaterial>,
) {
  if (!cullDuplicatedFaces || material.backFaceCulling || material.needAlphaBlending()) return material;
  const existing = cache.get(material);
  if (existing) return existing;
  // Coplanar reverse faces otherwise write inward normals into the SSAO buffer.
  const clone = material.clone(`Culled duplicate faces | ${material.name}`);
  clone.backFaceCulling = true;
  clone.twoSidedLighting = false;
  const originalTextures = new Set(material.getActiveTextures());
  const ownedTextures = clone.getActiveTextures().filter(texture => !originalTextures.has(texture));
  const disposal = material.onDisposeObservable.addOnce(() => clone.dispose(false, false));
  clone.onDisposeObservable.addOnce(() => {
    material.onDisposeObservable.remove(disposal);
    for (const texture of ownedTextures) texture.dispose();
    cache.delete(material);
  });
  cache.set(material, clone);
  return clone;
}

/** Blender stores Z-up bounds in millimetres; the running scene is Y-up, metres. */
export function sourceBounds(extras: SourceExtras) {
  const raw = typeof extras.source_bounds_mm === "string"
    ? JSON.parse(extras.source_bounds_mm) as { min: number[]; max: number[] }
    : extras.source_bounds_mm;
  if (!raw || raw.min.length !== 3 || raw.max.length !== 3) return null;
  if (![...raw.min, ...raw.max].every(Number.isFinite)) return null;
  return {
    minimum: new Vector3(raw.min[0], raw.min[2], -raw.max[1]).scale(0.001),
    maximum: new Vector3(raw.max[0], raw.max[2], -raw.min[1]).scale(0.001),
  };
}

/** Keep a multimap: several source pieces deliberately share their Babylon id. */
export function matchingSource<T extends { mesh: AbstractMesh; minimum: Vector3; maximum: Vector3 }>(
  sources: readonly T[],
  extras: SourceExtras,
): T | null {
  const candidates = sources.filter(({ mesh }) =>
    mesh.name === extras.source_name &&
    (!extras.source_id || mesh.id === extras.source_id),
  );
  if (candidates.length === 0) return null;
  const bounds = sourceBounds(extras);
  if (!bounds) return candidates.length === 1 ? candidates[0] : null;
  let closest: T | null = null;
  let distance = Infinity;
  for (const candidate of candidates) {
    const error = Vector3.DistanceSquared(candidate.minimum, bounds.minimum) +
      Vector3.DistanceSquared(candidate.maximum, bounds.maximum);
    if (error < distance) {
      distance = error;
      closest = candidate;
    }
  }
  // A stale export must never cover a wall or doorway that has moved in source.
  if (!closest) return null;
  const error = Math.max(
    ...closest.minimum.subtract(bounds.minimum).asArray().map(Math.abs),
    ...closest.maximum.subtract(bounds.maximum).asArray().map(Math.abs),
  );
  return error <= 0.0005 ? closest : null;
}

/** Match the exporter exactly, including expanded thin instances and curved meshes. */
export function sourceRestBounds(mesh: AbstractMesh) {
  const positions = mesh.getVerticesData(VertexBuffer.PositionKind);
  const world = mesh.computeWorldMatrix(true);
  if (!positions?.length) {
    const bounds = mesh.getBoundingInfo().boundingBox;
    return { minimum: bounds.minimumWorld.clone(), maximum: bounds.maximumWorld.clone() };
  }
  const transforms = mesh instanceof Mesh && mesh.hasThinInstances
    ? mesh.thinInstanceGetWorldMatrices().map((matrix) => matrix.multiply(world))
    : [world];
  const minimum = new Vector3(Infinity, Infinity, Infinity);
  const maximum = new Vector3(-Infinity, -Infinity, -Infinity);
  const vertex = new Vector3();
  const point = new Vector3();
  for (const transform of transforms) {
    for (let i = 0; i < positions.length; i += 3) {
      vertex.set(positions[i], positions[i + 1], positions[i + 2]);
      Vector3.TransformCoordinatesToRef(vertex, transform, point);
      minimum.minimizeInPlace(point);
      maximum.maximizeInPlace(point);
    }
  }
  return { minimum, maximum };
}

/**
 * Insert a full matrix between an imported object and its live source mesh.
 * At rest it cancels the source transform; later it follows the actual door,
 * handle or hatch. Full matrices preserve non-uniform scales without lossy
 * decomposition, and shared glTF geometry stays shared.
 */
export function anchorToSource(node: TransformNode, source: AbstractMesh, initialWorld: Matrix) {
  const previousParentWorld = node.parent instanceof TransformNode
    ? node.parent.computeWorldMatrix(true).clone()
    : Matrix.Identity();
  const anchor = new TransformNode(`ArchViz anchor | ${node.name}`, source.getScene());
  anchor.setPreTransformMatrix(previousParentWorld.multiply(Matrix.Invert(initialWorld)));
  anchor.parent = source;
  node.parent = anchor;
  return anchor;
}

function sourceNode(mesh: AbstractMesh): { node: TransformNode; extras: SourceExtras } | null {
  for (let node: Node | null = mesh; node; node = node.parent) {
    const extras = node.metadata?.gltf?.extras as SourceExtras | undefined;
    if (extras?.source_name && node instanceof TransformNode) return { node, extras };
  }
  return null;
}

export function isMovingSource(mesh: AbstractMesh) {
  for (let node: Node | null = mesh; node; node = node.parent) {
    if (node.metadata?.doorId || node.metadata?.doorMotion || node.metadata?.dynamicCameraOccluder) return true;
  }
  return false;
}

/** Visual assets augment the original interaction/collision model atomically. */
export class ArchvizPresentation {
  readonly ready: Promise<void>;
  readonly sources: NativeSource[];
  private readonly containers: AssetContainer[] = [];
  private readonly visuals: AbstractMesh[] = [];
  private readonly casters: AbstractMesh[] = [];
  private readonly replaced = new Set<NativeSource>();
  private readonly anchors: TransformNode[] = [];
  private readonly owned = new Set<AbstractMesh>();
  private readonly faceMaterials = new Map<PBRMaterial, PBRMaterial>();
  private grassContainer: AssetContainer | null = null;
  private grass: GrassPlacements | null = null;
  private readonly abort = new AbortController();
  private disposed = false;
  private applied = false;
  private realistic = true;
  private shadowMode: boolean | null = null;
  status: ArchvizStatus = "loading";

  constructor(private readonly host: ArchvizHost) {
    this.sources = [...host.layers].flatMap(([layer, meshes]) => meshes.map((mesh) => {
      mesh.computeWorldMatrix(true);
      const bounds = sourceRestBounds(mesh);
      return {
        mesh, layer,
        initialWorld: mesh.getWorldMatrix().clone(),
        minimum: bounds.minimum, maximum: bounds.maximum,
        technicalVisibility: host.technicalVisibility(mesh),
        originalVisibility: mesh.visibility,
        castsShadow: host.castsShadow(mesh),
        // Snapshot the physical policy, even if the mesh currently shows CAD.
        cullDuplicatedFaces: !!host.realisticMaterial(mesh)?.backFaceCulling && hasDuplicatedBackFaces(mesh),
      };
    }));
    this.ready = this.load();
  }

  private async load() {
    this.host.onStatus("loading");
    const timeout = setTimeout(() => this.abort.abort(), 120_000);
    try {
      const manifestResponse = await fetch("/assets/archviz/export-manifest.json", { signal: this.abort.signal });
      if (!manifestResponse.ok) throw new Error(`ArchViz manifest: ${manifestResponse.status}`);
      const manifest = await manifestResponse.json() as ArchvizManifest;
      if (!Array.isArray(manifest.files) || manifest.files.length === 0) throw new Error("Empty ArchViz manifest");
      for (const file of manifest.files) {
        if (!/^[a-z0-9-]+\.glb$/.test(file.file)) throw new Error("Invalid ArchViz asset path");
        const response = await fetch(`/assets/archviz/${file.file}`, { signal: this.abort.signal });
        if (!response.ok) throw new Error(`ArchViz asset: ${response.status}`);
        const bytes = await response.arrayBuffer();
        if (bytes.byteLength !== file.bytes) throw new Error(`Incomplete ArchViz asset: ${file.file}`);
        if (this.disposed) return;
        const container = await LoadAssetContainerAsync(new Uint8Array(bytes), this.host.scene, {
          pluginExtension: ".glb",
          name: file.file,
          pluginOptions: { gltf: { dontUseTransmissionHelper: true } },
        });
        if (this.disposed || this.abort.signal.aborted) {
          container.dispose();
          throw new Error("ArchViz loading interrupted");
        }
        this.containers.push(container);
        if (file.kind === "grass-prototype") this.grassContainer = container;
      }
      if (this.grassContainer) {
        const response = await fetch("/assets/archviz/grass-placements.json", { signal: this.abort.signal });
        if (!response.ok) throw new Error("Grass placement data unavailable");
        this.grass = await response.json() as GrassPlacements;
        if (this.grass.stride !== 5 || this.grass.placements.length % 5 !== 0 ||
          !this.grass.placements.every(Number.isFinite)) throw new Error("Invalid grass placements");
      }
      if (this.disposed) return;
      this.install(manifest);
      this.applied = true;
      this.applyViewMode(this.realistic);
      this.status = "ready";
      this.host.onStatus("ready");
    } catch (error) {
      this.releaseAssets();
      if (!this.disposed) {
        this.status = "fallback";
        this.host.onStatus("fallback");
        console.warn("Realistic house assets unavailable; using the base model.", error);
      }
    } finally {
      clearTimeout(timeout);
    }
  }

  private install(manifest: ArchvizManifest) {
    type Registration = { mesh: AbstractMesh; source: NativeSource | null; layer: LayerId };
    const registrations: Registration[] = [];
    const nodeSources = new Map<TransformNode, NativeSource>();
    for (const container of this.containers) {
      for (const material of container.materials) {
        if (material instanceof PBRMaterial) {
          material.enableSpecularAntiAliasing = true;
          material.useRadianceOverAlpha = false;
          material.useSpecularOverAlpha = false;
          // Thin window/shower panes show the live room at full resolution.
          // Screen-space glTF refraction otherwise redraws the entire house
          // into a small buffer and visibly pixelates the view through glass.
          if (material.subSurface.isRefractionEnabled) {
            material.subSurface.isRefractionEnabled = false;
            if (material.name.includes("glass")) {
              material.transparencyMode = PBRMaterial.PBRMATERIAL_ALPHABLEND;
              material.alpha = material.name.includes("fireplace") ? 0.28 : 0.14;
              material.backFaceCulling = true;
              material.needDepthPrePass = true;
              material.separateCullingPass = true;
            }
          }
          for (const texture of material.getActiveTextures()) texture.anisotropicFilteringLevel = 8;
        }
      }
      for (const mesh of container.meshes) {
        if (mesh.getTotalVertices() === 0) continue;
        if (container === this.grassContainer) continue;
        const provenance = sourceNode(mesh);
        const source = provenance ? matchingSource(this.sources, provenance.extras) : null;
        if (provenance && (
          provenance.extras.source_enabled === false ||
          (!source && provenance.extras.visualization_only !== true)
        )) {
          // Keep source geometry when the export no longer matches it.
          mesh.setEnabled(false);
          continue;
        }
        if (provenance && source) nodeSources.set(provenance.node, source);
        if (provenance && mesh.material instanceof PBRMaterial) {
          mesh.material = archvizMaterialForFaces(mesh.material, source?.cullDuplicatedFaces ?? false, this.faceMaterials);
          mesh.material = warmLivingMaterial(this.host.scene, provenance.extras.source_name ?? "", mesh.material);
        }
        registrations.push({ mesh, source, layer: source?.layer ?? "street" });
      }
    }
    if (nodeSources.size < 500) throw new Error("ArchViz house does not match the architectural model");
    for (const container of this.containers) container.addAllToScene();
    for (const [node, source] of nodeSources) {
      if (isMovingSource(source.mesh)) {
        this.anchors.push(anchorToSource(node, source.mesh, source.initialWorld));
      }
      this.replaced.add(source);
    }

    // Hundreds of cabinetry/roof details share a material and an entity. Batch
    // only their static, opaque visual geometry; all original colliders and
    // every moving door/handle stay separate. This cuts browser draw calls
    // without reducing the Blender geometry or losing layer/entity selection.
    const staticGroups = new Map<string, Registration[]>();
    const rendered: Registration[] = [];
    for (const item of registrations) {
      const { mesh, source, layer } = item;
      if (!source || !(mesh instanceof Mesh) || mesh.hasInstances ||
        isMovingSource(source.mesh) || !mesh.material || mesh.material.needAlphaBlendingForMesh(mesh)) {
        rendered.push(item);
        continue;
      }
      const key = [layer, source.mesh.metadata?.entityId ?? "", mesh.material.uniqueId,
        source.castsShadow, source.mesh.isPickable, source.mesh.layerMask, source.mesh.renderingGroupId].join("|");
      const group = staticGroups.get(key) ?? [];
      group.push(item);
      staticGroups.set(key, group);
    }
    for (const group of staticGroups.values()) {
      if (group.length < 2) { rendered.push(...group); continue; }
      const merged = Mesh.MergeMeshes(group.map(({ mesh }) => mesh as Mesh), true, true);
      if (!merged) { rendered.push(...group); continue; }
      this.owned.add(merged);
      merged.name = `ArchViz | ${group[0].source?.mesh.metadata?.entityId ?? group[0].layer} | ${merged.material?.name}`;
      rendered.push({ ...group[0], mesh: merged });
    }

    for (const { mesh, source, layer } of rendered) {
      mesh.receiveShadows = true;
      mesh.checkCollisions = false;
      mesh.isPickable = source?.mesh.isPickable ?? false;
      if (source) {
        mesh.renderingGroupId = source.mesh.renderingGroupId;
        mesh.layerMask = source.mesh.layerMask;
      }
      const original = source?.mesh.metadata;
      mesh.metadata = {
        archviz: true,
        sourceName: source?.mesh.name,
        ...(typeof original?.entityId === "string" ? { entityId: original.entityId } : {}),
        ...(typeof original?.doorId === "string" ? { doorId: original.doorId } : {}),
      };
      this.visuals.push(mesh);
      if (source?.castsShadow ?? true) this.casters.push(mesh);
      this.host.register(mesh, layer, original?.entityId);
    }
    for (const name of manifest.appearanceHiddenSourceNames ?? []) {
      for (const source of this.sources) {
        if (source.mesh.name === name) this.replaced.add(source);
      }
    }
    this.installGrass();
  }

  private installGrass() {
    const prototype = this.grassContainer?.meshes.find((mesh) => mesh.getTotalVertices() > 0);
    if (!(prototype instanceof Mesh) || !this.grass) return;
    const sourceWorld = prototype.computeWorldMatrix(true).clone();
    const count = Math.min(this.grass.placements.length / 5,
      this.host.compact ? this.grass.mobileCount : this.grass.desktopCount);
    const patches = new Map<string, number[][]>();
    for (let i = 0; i < count; i++) {
      const placement = this.grass.placements.slice(i * 5, i * 5 + 5);
      const key = `${Math.floor(placement[0] / 6)},${Math.floor(placement[2] / 6)}`;
      const patch = patches.get(key) ?? [];
      patch.push(placement);
      patches.set(key, patch);
    }
    for (const [key, placements] of patches) {
      const patch = prototype.clone(`ArchViz grass | ${key}`, null, true);
      this.owned.add(patch);
      // Thin-instance vertex bindings belong to each patch. Sharing a VAO
      // across buffers of different lengths causes invalid instanced draws.
      patch.makeGeometryUnique();
      patch.parent = null;
      patch.position.setAll(0);
      patch.rotationQuaternion = null;
      patch.rotation.setAll(0);
      patch.scaling.setAll(1);
      const matrices = new Float32Array(placements.length * 16);
      for (const [index, [x, y, z, yaw, scale]] of placements.entries()) {
        sourceWorld.multiply(Matrix.Compose(new Vector3(scale, scale, scale),
          Quaternion.RotationAxis(Vector3.UpReadOnly, yaw), new Vector3(x, y, z))).copyToArray(matrices, index * 16);
      }
      patch.thinInstanceSetBuffer("matrix", matrices, 16, true);
      patch.thinInstanceRefreshBoundingInfo(true);
      patch.addLODLevel(this.host.compact ? 22 : 38, null);
      patch.receiveShadows = true;
      patch.isPickable = false;
      patch.checkCollisions = false;
      patch.metadata = { archviz: true, grass: true };
      patch.setEnabled(true);
      this.visuals.push(patch);
      this.host.register(patch, "street");
    }
    prototype.setEnabled(false);
  }

  applyViewMode(realistic: boolean) {
    this.realistic = realistic;
    if (!this.applied) return;
    for (const source of this.replaced) {
      source.mesh.visibility = realistic ? 0 : source.technicalVisibility;
    }
    for (const mesh of this.visuals) mesh.visibility = realistic ? 1 : 0;
    if (this.shadowMode !== realistic) {
      for (const source of this.replaced) {
        if (source.castsShadow) this.host.setShadow(source.mesh, !realistic);
      }
      for (const mesh of this.casters) this.host.setShadow(mesh, realistic);
      this.shadowMode = realistic;
    }
  }

  get statistics() {
    return { status: this.status, visuals: this.visuals.length, replaced: this.replaced.size };
  }

  private releaseAssets() {
    this.applied = false;
    for (const source of this.replaced) {
      if (!source.mesh.isDisposed()) {
        source.mesh.visibility = source.originalVisibility;
        this.host.setShadow(source.mesh, source.castsShadow);
      }
    }
    for (const mesh of this.visuals) {
      this.host.setShadow(mesh, false);
      this.host.unregister(mesh);
    }
    for (const mesh of this.owned) mesh.dispose();
    for (const container of this.containers) container.dispose();
    for (const anchor of this.anchors) anchor.dispose();
    this.containers.length = this.visuals.length = this.casters.length = this.anchors.length = 0;
    this.owned.clear();
    this.replaced.clear();
    this.shadowMode = null;
  }

  dispose() {
    this.disposed = true;
    this.abort.abort();
    // Assets are also owned by the scene. Explicitly dispose containers here
    // so an unmount during loading cannot leave a late glTF result alive.
    this.releaseAssets();
  }
}
