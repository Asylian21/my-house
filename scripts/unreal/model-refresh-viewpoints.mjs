import assert from 'node:assert/strict';

export const MODEL_CAMERA_SOURCES = Object.freeze({
  sofa: 'LIVING-103-SOFA-L · TAILORED · hlavný modul · čalúnený rám',
  hob: 'KITCHEN-RUN · varná doska · indukcia 800',
});

function sourceObject(scene, sourceId) {
  const matches = scene.objects.filter(object => object.sourceId === sourceId);
  assert.equal(matches.length, 1, `Expected one camera source: ${sourceId}`);
  const object = matches[0];
  assert.equal(object.enabled, true, `Camera source must be active: ${sourceId}`);
  for (const key of ['min', 'max']) {
    assert(Array.isArray(object.boundsMm?.[key]) && object.boundsMm[key].length === 3
      && object.boundsMm[key].every(Number.isFinite), `Invalid source bounds: ${sourceId}`);
  }
  assert(object.boundsMm.min.every((n, index) => n < object.boundsMm.max[index]), `Degenerate source bounds: ${sourceId}`);
  return object;
}

/** Presentation-only override for the current B sofa and kitchen; never changes bridge inputs. */
export function buildModelRefreshViewpoints(scene, viewpoints) {
  assert.equal(scene.units, 'millimetres');
  assert.equal(scene.coordinateSystem, 'right-handed Z-up');
  assert.deepEqual(scene.activeDesign, { variant: 'C', livingLayout: 'B', heatingLayout: 'B' }, 'Camera requires explicit C/B/B');
  assert(Number.isFinite(scene.sceneCenterMm?.x) && Number.isFinite(scene.sceneCenterMm?.y), 'Missing source scene center');
  assert.equal(viewpoints.coordinateSystem, 'unreal-centimeters');
  assert(Array.isArray(viewpoints.views), 'Missing viewpoint list');
  const interiors = viewpoints.views.filter(view => view.id === 'interior');
  assert.equal(interiors.length, 1, 'Expected one interior preset');
  assert(Number.isFinite(interiors[0].horizontalFovDegrees) && interiors[0].horizontalFovDegrees > 0
    && interiors[0].horizontalFovDegrees < 180, 'Invalid interior field of view');
  const sofa = sourceObject(scene, MODEL_CAMERA_SOURCES.sofa);
  const hob = sourceObject(scene, MODEL_CAMERA_SOURCES.hob);
  const origin = scene.sceneCenterMm;
  // These offsets mirror livingWalkArrival(B); the aim frames the updated kitchen.
  const eyePlanMm = [sofa.boundsMm.min[0] + origin.x - 750, sofa.boundsMm.min[1] + origin.y - 400, 1650];
  const targetPlanMm = [(hob.boundsMm.min[0] + hob.boundsMm.max[0]) / 2 + origin.x,
    (hob.boundsMm.min[1] + hob.boundsMm.max[1]) / 2 + origin.y, 1100];
  const toUnreal = ([x, y, z]) => [(x - origin.x) / 10, -(y - origin.y) / 10, z / 10];
  const result = structuredClone(viewpoints);
  const interior = result.views.find(view => view.id === 'interior');
  Object.assign(interior, {
    label: 'Kuchyňa', eyeCm: toUnreal(eyePlanMm), targetCm: toUnreal(targetPlanMm),
    source: 'scene.json:activeDesign and source-object sofa/hob bounds',
    presentation: {
      intent: 'Kitchen view from the C/B/B walking arrival outside the relocated sofa',
      eyeElevationMm: 1650, targetElevationMm: 1100,
      derivation: {
        method: 'livingWalkArrival(B) offsets from sofa minimum XY; target at rear hob center',
        eyeOffsetFromSofaMinMm: [-750, -400], eyePlanMm, targetPlanMm,
        coordinateMapping: 'X=(planX-sceneCenter.x)/10; Y=-(planY-sceneCenter.y)/10; Z=elevation/10',
        sceneCenterMm: structuredClone(origin), activeDesign: structuredClone(scene.activeDesign),
        sourceObjects: Object.fromEntries(Object.entries({ sofa, hob }).map(([key, object]) => [key, {
          objectId: object.id, sourceId: object.sourceId, boundsMm: structuredClone(object.boundsMm),
        }])),
      },
    },
  });
  return result;
}
