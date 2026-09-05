import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import { Texture } from "@babylonjs/core/Materials/Textures/texture";
import { Color3 } from "@babylonjs/core/Maths/math.color";
import type { Scene } from "@babylonjs/core/scene";

const FINISHES = {
  fabric: { color: "#D8C8B2", texture: "living-boucle-ecru-albedo", roughness: 0.92 },
  cabinet: { color: "#CEA087", texture: null, roughness: 0.82 },
  stone: { color: "#BDAF98", texture: "living-warm-stone-albedo", roughness: 0.72 },
  oak: { color: "#BE9566", texture: "living-natural-oak-albedo", roughness: 0.55 },
  rug: { color: "#BCAE96", texture: "living-wool-sand-albedo", roughness: 0.98 },
  accent: { color: "#B67E63", texture: null, roughness: 0.94 },
} as const;
type LivingFinish = keyof typeof FINISHES;

/** Original material names are shared by bedrooms, the kitchen and bathroom. */
export function livingFinishFor(sourceName: string, materialName: string): LivingFinish | null {
  if (!sourceName.startsWith("LIVING-103-")) return null;
  const roles: Record<string, LivingFinish> = {
    "real-interior-upholstery": "fabric",
    "real-interior-living-cabinet": "cabinet",
    "real-interior-media-stone": "stone",
    "real-interior-kitchen-front": "oak",
    "real-interior-rug": "rug",
    "real-interior-accent-fabric": "accent",
    "real-interior-worktop": "stone",
  };
  return Object.entries(roles).find(([name]) => materialName === name || materialName.endsWith(` | ${name}`))?.[1] ?? null;
}

const caches = new WeakMap<Scene, Map<string, PBRMaterial>>();

/** One room-scoped clone per source finish, shared by native and GLB builders. */
export function warmLivingMaterial(scene: Scene, sourceName: string, original: PBRMaterial) {
  const role = livingFinishFor(sourceName, original.name);
  if (!role) return original;
  let cache = caches.get(scene);
  if (!cache) { cache = new Map(); caches.set(scene, cache); }
  const key = `${original.uniqueId}:${role}`;
  const existing = cache.get(key);
  if (existing) return existing;
  const finish = FINISHES[role];
  const material = original.clone(`Living warm ${role} | ${original.name}`);
  const originalTextures = new Set(original.getActiveTextures());
  const ownedTextures = new Set(material.getActiveTextures().filter(texture => !originalTextures.has(texture)));
  material.roughness = finish.roughness;
  material.metallic = 0;
  material.environmentIntensity = 0.85;
  material.albedoColor = finish.texture ? Color3.White() : Color3.FromHexString(finish.color).toLinearSpace();
  // Warm the actual surface reflectance: the saved blue daylight otherwise
  // makes neutral textiles and limestone read cold inside the shaded room.
  if (role === "fabric" || role === "rug") material.albedoColor.set(1, 0.9, 0.74);
  if (role === "stone") material.albedoColor.set(1, 0.76, 0.63);
  if (finish.texture) {
    const texture = new Texture(`/assets/textures/${finish.texture}.jpg`, scene, false, false, Texture.TRILINEAR_SAMPLINGMODE);
    texture.gammaSpace = true;
    texture.anisotropicFilteringLevel = 8;
    const previous = original.albedoTexture;
    if (previous instanceof Texture) {
      for (const property of ["uScale", "vScale", "uOffset", "vOffset", "uAng", "vAng", "wAng", "coordinatesIndex", "wrapU", "wrapV"] as const) {
        texture[property] = previous[property];
      }
    }
    material.albedoTexture = texture;
    ownedTextures.add(texture);
  } else material.albedoTexture = null;
  // PBRMaterial.clone also clones texture wrappers. Release the discarded
  // albedo wrapper without touching any wrapper retained by another channel.
  const activeTextures = new Set(material.getActiveTextures());
  for (const texture of ownedTextures) {
    if (!activeTextures.has(texture)) { texture.dispose(); ownedTextures.delete(texture); }
  }
  if (role === "fabric" || role === "accent") {
    material.sheen.isEnabled = true;
    material.sheen.intensity = 0.2;
    material.sheen.color = Color3.FromHexString(finish.color).toLinearSpace();
    material.sheen.roughness = 0.9;
  }
  // AssetContainer owns the imported original. Follow its lifetime so a
  // failed import/fallback also releases these room-scoped replacements.
  const originalDisposal = original.onDisposeObservable.addOnce(() => material.dispose(false, false));
  material.onDisposeObservable.addOnce(() => {
    original.onDisposeObservable.remove(originalDisposal);
    for (const texture of ownedTextures) texture.dispose();
    ownedTextures.clear();
    cache.delete(key);
  });
  cache.set(key, material);
  return material;
}
