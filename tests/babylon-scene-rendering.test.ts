import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { describe, expect, it } from "vitest";

import {
  PARCEL_LABEL_RENDERING_GROUP_ID,
  createTwinRenderScene,
  setSelectionHighlightForNavigation,
} from "../lib/babylon-scene";

describe("Babylon scene depth occlusion", () => {
  it("keeps house depth when the late parcel-label group renders", () => {
    const engine = new NullEngine({
      renderHeight: 64,
      renderWidth: 64,
      textureSize: 64,
    });
    const scene = createTwinRenderScene(engine);

    try {
      expect(
        scene.getAutoClearDepthStencilSetup(PARCEL_LABEL_RENDERING_GROUP_ID),
      ).toMatchObject({ autoClear: false });
    } finally {
      scene.dispose();
      engine.dispose();
    }
  });

  it("disables x-ray selection glow for both immersive cameras", () => {
    const highlight = { isEnabled: true };

    setSelectionHighlightForNavigation(highlight, "walk");
    expect(highlight.isEnabled).toBe(false);

    setSelectionHighlightForNavigation(highlight, "flight");
    expect(highlight.isEnabled).toBe(false);

    setSelectionHighlightForNavigation(highlight, "orbit");
    expect(highlight.isEnabled).toBe(true);
  });
});
