import { afterEach, describe, expect, it, vi } from 'vitest';
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { Scene } from '@babylonjs/core/scene';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { buildInterior } from '../lib/babylon-interior';
import type { TwinSceneOptions } from '../lib/babylon-scene';
import { ACTIVE_DESIGN } from '../lib/twin-design-selection';
import { LIVING_LAYOUTS } from '../lib/twin-living-layouts';

const renderer = vi.hoisted(() => ({ createTwinScene: vi.fn() }));
vi.mock('../lib/babylon-scene', () => renderer);

describe('active ArchViz and Unreal scene capture', () => {
  let engine: NullEngine | undefined;
  let scene: Scene | undefined;
  afterEach(() => {
    vi.unstubAllGlobals();
    scene?.dispose();
    engine?.dispose();
    vi.resetAllMocks();
  });

  it('passes the main design into the renderer and captures B/B geometry with matching provenance', async () => {
    const canvas = { dataset: {} };
    const captureWindow: {
      archvizReady?: boolean;
      captureArchviz?: () => {
        model: { activeDesign: { variant: string; livingLayout: string; heatingLayout: string } };
        meshes: { name: string }[];
      };
    } = {};
    vi.stubGlobal('document', { querySelector: () => canvas });
    vi.stubGlobal('window', captureWindow);
    renderer.createTwinScene.mockImplementation((_canvas, _a, _b, _c, options: TwinSceneOptions) => {
      engine = new NullEngine();
      scene = new Scene(engine);
      scene.useRightHandedSystem = true;
      const material = new PBRMaterial('export-test', scene);
      // Exercise actual interior selection using the export entry point's options.
      // The underlying builders retain A/A defaults for archived studies.
      buildInterior({
        scene, ...options, anisotropy: 1, wall: material, soffit: material,
        glassFrame: material, chimneyMetal: material, timber: material,
        register: mesh => mesh, realisticOnly: mesh => mesh, castShadow: mesh => mesh,
      });
      return { update: vi.fn(), captureNativeDoorMotion: vi.fn(() => ({ source: 'test-double' })) };
    });

    await import('../scripts/archviz/scene-export');
    expect(renderer.createTwinScene).toHaveBeenCalledExactlyOnceWith(
      canvas, expect.any(Function), expect.any(Function), expect.any(Function),
      { ...ACTIVE_DESIGN, loadArchviz: false },
    );
    expect(captureWindow.archvizReady).toBe(true);
    const captured = captureWindow.captureArchviz!();
    expect(captured.model.activeDesign).toEqual({ variant: 'C', heatingLayout: 'B', livingLayout: 'B' });
    expect(captured.meshes.some(mesh => mesh.name.startsWith(LIVING_LAYOUTS.B.stove.id))).toBe(true);
    expect(captured.meshes.some(mesh => mesh.name.startsWith(LIVING_LAYOUTS.A.stove.id))).toBe(false);
    expect(captured.meshes.some(mesh => mesh.name.startsWith('TECHNICAL-PLUS19-'))).toBe(false);
  });
});
