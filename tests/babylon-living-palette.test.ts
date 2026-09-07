import { afterEach, describe, expect, it } from 'vitest';
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { Scene } from '@babylonjs/core/scene';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { RawTexture } from '@babylonjs/core/Materials/Textures/rawTexture';
import { Texture } from '@babylonjs/core/Materials/Textures/texture';
import { livingFinishFor, warmLivingMaterial } from '../lib/babylon-living-palette';

const livingCabinetName = 'LIVING-103-TV-WALL · vysoká bezúchytková skriňa pri krbe';
let engine: NullEngine | undefined;
let scene: Scene | undefined;

afterEach(() => {
  scene?.dispose();
  engine?.dispose();
  scene = undefined;
  engine = undefined;
});

function fixture() {
  engine = new NullEngine();
  scene = new Scene(engine);
  const original = new PBRMaterial('MAT_0066 | real-interior-living-cabinet', scene);
  // Real one-pixel RGBA buffers need neither DOM Image nor XMLHttpRequest.
  const albedo = RawTexture.CreateRGBATexture(new Uint8Array([220, 200, 170, 255]), 1, 1, scene, false, false, Texture.NEAREST_SAMPLINGMODE);
  const normal = RawTexture.CreateRGBATexture(new Uint8Array([128, 128, 255, 255]), 1, 1, scene, false, false, Texture.NEAREST_SAMPLINGMODE);
  original.albedoTexture = albedo;
  original.bumpTexture = normal;
  normal.gammaSpace = false;
  original.invertNormalMapX = true;
  const originalTextures = new Set(scene.textures);
  return { scene, original, albedo, normal, originalTextures };
}

describe('warm living material resource lifetime', () => {
  it('releases the abandoned cloned albedo while retaining the source maps and cloned normal texture', () => {
    const { scene, original, albedo, normal, originalTextures } = fixture();
    const warm = warmLivingMaterial(scene, livingCabinetName, original);
    expect(warm).not.toBe(original);
    expect((warm.albedoTexture as Texture).url).toBe('/assets/textures/living-natural-oak-albedo.jpg');
    expect(scene.textures).toContain(albedo);
    expect(scene.textures).toContain(normal);
    const retainedNormal = warm.bumpTexture as Texture;
    expect(retainedNormal).not.toBe(normal);
    expect(retainedNormal.gammaSpace).toBe(false);
    expect(warm.invertNormalMapX).toBe(true);
    const addedTextures = scene.textures.filter(texture => !originalTextures.has(texture));
    expect(new Set(addedTextures)).toEqual(new Set([retainedNormal,warm.albedoTexture]));
  });

  it('disposes the warm clone and only its owned texture wrappers when the source material is disposed', () => {
    const { scene, original, albedo, normal, originalTextures } = fixture();
    const warm = warmLivingMaterial(scene, livingCabinetName, original);
    const warmNormal = warm.bumpTexture!;
    original.dispose();
    expect(scene.materials).not.toContain(warm);
    expect(scene.textures).not.toContain(warmNormal);
    expect(scene.textures.filter(texture => !originalTextures.has(texture))).toEqual([]);
    // Original textures may have their own container owners and must survive.
    expect(scene.textures).toContain(albedo);
    expect(scene.textures).toContain(normal);
  });

  it('evicts an explicitly disposed clone so a live source can resolve a fresh material', () => {
    const { scene, original, albedo, normal, originalTextures } = fixture();
    const first = warmLivingMaterial(scene, livingCabinetName, original);
    const firstNormal = first.bumpTexture!;
    expect(warmLivingMaterial(scene, livingCabinetName, original)).toBe(first);
    first.dispose();
    expect(scene.textures).not.toContain(firstNormal);
    expect(scene.textures.filter(texture => !originalTextures.has(texture))).toEqual([]);
    const second = warmLivingMaterial(scene, livingCabinetName, original);
    expect(second).not.toBe(first);
    expect(scene.materials).toContain(second);
    expect(second.bumpTexture).not.toBe(firstNormal);
    expect(scene.materials).toContain(original);
    expect(scene.textures).toContain(albedo);
    expect(scene.textures).toContain(normal);
    original.dispose();
    expect(scene.materials).not.toContain(second);
    expect(scene.textures.filter(texture => !originalTextures.has(texture))).toEqual([]);
  });

  it('uses matte oak for both the TV storage and smaller table, with no changes to other rooms',()=>{
    const { scene, original }=fixture();
    const cabinet=warmLivingMaterial(scene,livingCabinetName,original);
    const table=warmLivingMaterial(scene,'LIVING-103-SOFA-L · oválny konferenčný stolík 2',original);
    expect(table).toBe(cabinet);
    expect(cabinet.metallic).toBe(0);
    expect(cabinet.roughness).toBeGreaterThanOrEqual(.7);
    expect(cabinet.clearCoat.isEnabled).toBe(false);
    expect(warmLivingMaterial(scene,'C-BEDROOM-110 · skrinka',original)).toBe(original);
    expect(livingFinishFor('LIVING-103-SOFA-L · TAILORED · sedák','real-interior-upholstery')).toBe('sofa');
    const fabric=new PBRMaterial('real-interior-upholstery',scene);
    const sofa=warmLivingMaterial(scene,'LIVING-103-SOFA-L · TAILORED · sedák',fabric);
    expect(sofa.albedoColor.asArray()).toEqual([.69,.72,.72]);
    expect(sofa.roughness).toBe(.99);
    expect(sofa.metallic).toBe(0);
    const seating=warmLivingMaterial(scene,'LIVING-103-DINING · stolička',fabric);
    expect(seating).not.toBe(sofa);
    expect(seating.albedoColor.asArray()).toEqual([1,.9,.74]);
  });
});
