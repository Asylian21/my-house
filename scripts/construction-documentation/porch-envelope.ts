import { HOUSE } from '../../lib/twin-active-house';
import {
  deriveJoinedRoofGeometry,
  deriveJoinedRoofRenderPlan,
  deriveWingPorchPortalHeadProfiles,
  wingInnerRoofHeightMm,
  wingOuterRoofHeightMm,
} from '../../lib/twin-roof';

/** An unclosed polygon in plan X / elevation Z, extruded along plan Y; all mm. */
export interface PorchEnvelopePartMm {
  readonly id: string;
  readonly meshName: string;
  readonly kind: 'SUPPORT_HEAD' | 'LARCH_SOFFIT';
  readonly polygonXZMm: readonly (readonly [xMm: number, elevationMm: number])[];
  readonly startYmm: number;
  readonly endYmm: number;
  readonly status: 'MODEL_ENVELOPE_ONLY';
  readonly sources: readonly string[];
}

export interface PorchSoffitPanelMm extends PorchEnvelopePartMm {
  readonly kind: 'LARCH_SOFFIT';
  /** Rendered box thickness normal to the roof slope, not vertical thickness. */
  readonly normalThicknessMm: number;
  /** Vertical offset of the unrounded centreline endpoints below the roof. */
  readonly centerlineDropMm: number;
  readonly eaveInsetMm: number;
  readonly boxLengthMm: number;
  readonly rotationRadians: number;
}

/**
 * Existing visible porch geometry only, without a proposed structural assembly.
 *
 * Head profiles come directly from the roof model. The soffits reproduce the
 * CreateBox dimensions and rotation in TwinSceneController.buildWingPorch:
 * notably, box length is rounded to whole mm BEFORE rotation. A rectangular
 * bounding box or a vertical 45 mm strip would change the section at the ridge.
 * Existing exterior gable profiles are intentionally supplied by source.tsx.
 */
export function derivePorchEnvelope(): {
  supportHeads: PorchEnvelopePartMm[];
  soffitPanels: PorchSoffitPanelMm[];
} {
  const porch = HOUSE.porches.wingEnd;
  const roof = deriveJoinedRoofGeometry();
  const parameters = roof.parameters;
  const renderPlan = deriveJoinedRoofRenderPlan(roof);

  const supportHeads: PorchEnvelopePartMm[] =
    deriveWingPorchPortalHeadProfiles(parameters).map(head => ({
      id: head.id,
      meshName: `${head.id} · hlava podpory portálu P04`,
      kind: 'SUPPORT_HEAD',
      polygonXZMm: head.profile.map(point => [point.alongMm, point.elevationMm] as const),
      startYmm: head.startYmm,
      endYmm: head.endYmm,
      status: 'MODEL_ENVELOPE_ONLY',
      sources: [
        'lib/twin-roof.ts:deriveWingPorchPortalHeadProfiles',
        'lib/babylon-scene.ts:TwinSceneController.buildWingPorch',
      ],
    }));

  // This constant is local to buildWingPorch; preserve its rendered envelope.
  const normalThicknessMm = 45;
  const wingRunMm = HOUSE.roof.wingHalfSpanMm;
  const wingRiseMm = HOUSE.ridgeElevationMm - HOUSE.eavesElevationMm;
  const wingSlopeMm = Math.hypot(wingRunMm, wingRiseMm);
  const eaveInsetMm = Math.ceil((normalThicknessMm / 2) * (wingRiseMm / wingSlopeMm));
  const slopes = [
    {
      id: 'PORCH-SOFFIT-WEST',
      name: 'západná',
      startXmm: parameters.wingInnerEaveXmm + eaveInsetMm,
      endXmm: parameters.wingRidgeXmm,
      heightAt: wingInnerRoofHeightMm,
    },
    {
      id: 'PORCH-SOFFIT-EAST',
      name: 'východná',
      startXmm: parameters.wingRidgeXmm,
      endXmm: parameters.maxXmm - eaveInsetMm,
      heightAt: wingOuterRoofHeightMm,
    },
  ];

  const soffitPanels: PorchSoffitPanelMm[] = slopes.map(slope => {
    // Retain the renderer's metre arithmetic and the whole-mm box-length snap.
    const startM = (slope.heightAt(slope.startXmm, parameters) - porch.ceilingClearanceMm) * 0.001;
    const endM = (slope.heightAt(slope.endXmm, parameters) - porch.ceilingClearanceMm) * 0.001;
    const runM = (slope.endXmm - slope.startXmm) * 0.001;
    const riseM = endM - startM;
    const boxLengthMm = Math.round(Math.hypot(runM, riseM) * 1000);
    const rotationRadians = Math.atan2(riseM, runM);
    const cos = Math.cos(rotationRadians);
    const sin = Math.sin(rotationRadians);
    const centerXmm = (slope.startXmm + slope.endXmm) / 2;
    const centerElevationMm = ((startM + endM) / 2) * 1000;
    const halfLengthMm = boxLengthMm / 2;
    const halfThicknessMm = normalThicknessMm / 2;
    const localCorners = [
      [-halfLengthMm, -halfThicknessMm],
      [halfLengthMm, -halfThicknessMm],
      [halfLengthMm, halfThicknessMm],
      [-halfLengthMm, halfThicknessMm],
    ];
    return {
      id: slope.id,
      meshName: `Krytá terasa · ${slope.name} strešná podbitka`,
      kind: 'LARCH_SOFFIT',
      polygonXZMm: localCorners.map(([along, normal]) => [
        centerXmm + along * cos - normal * sin,
        centerElevationMm + along * sin + normal * cos,
      ] as const),
      startYmm: renderPlan.wingPorch.larchSoffitStartYmm,
      endYmm: renderPlan.wingPorch.larchSoffitEndYmm,
      normalThicknessMm,
      centerlineDropMm: porch.ceilingClearanceMm,
      eaveInsetMm,
      boxLengthMm,
      rotationRadians,
      status: 'MODEL_ENVELOPE_ONLY',
      sources: [
        'lib/babylon-scene.ts:TwinSceneController.buildWingPorch',
        'lib/babylon-scene.ts:boxAtPlan',
        'lib/twin-roof.ts:deriveJoinedRoofRenderPlan',
      ],
    };
  });

  return { supportHeads, soffitPanels };
}
