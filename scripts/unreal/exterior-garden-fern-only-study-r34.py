"""Fresh R34 source proposal:36 exact fern fits, all12 original heroes retained.

Produces geometry and a material recipe only. Root supplies a fresh R29 clone
and separately authorized native entry later; no Unreal/GPU is invoked here.
"""
from datetime import datetime, timezone
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-fern-only-study-r34.py'
s = importlib.util.spec_from_file_location('r34_owned_source_scope', ROOT/'scripts/unreal/exterior-garden-fern-only-guards-r34.py')
g = importlib.util.module_from_spec(s)
s.loader.exec_module(g)


def write(path, row):
    with Path(path).open('x') as f:
        json.dump(row, f, indent=2, allow_nan=False)
        f.write('\n')


def plot(ref):
    garden = ref['source']['garden']
    polygons = [t for faces in garden['sourceMulchTrianglesCm'].values() for t in faces]
    points = [p[:2] for t in polygons for p in t]
    x0, x1 = min(p[0] for p in points)-40, max(p[0] for p in points)+40
    y0, y1 = min(p[1] for p in points)-40, max(p[1] for p in points)+40
    width, height = 1200, 630
    scale = min(1100/(x1-x0), 500/(y1-y0))
    def xy(p):
        return 50+(p[0]-x0)*scale, 580-(p[1]-y0)*scale
    def polygon(p, color):
        return '<polygon points="'+ ' '.join('%.3f,%.3f'%xy(q) for q in p)+'" fill="'+color+'" stroke="#59655c" stroke-width=".4"/>'
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" aria-label="R34 source-only garden root plan">'%(width,height),
             '<rect width="1200" height="630" fill="#f5f4ed"/>',
             '<text x="35" y="34" font-family="sans-serif" font-size="23">R34 · 36 papraďových náhrad, pôvodné vysoké trsy zachované</text>',
             '<text x="35" y="59" font-family="sans-serif" font-size="14">Zdrojový pôdorys a obsahujúce kružnice. Nie listové pokrytie, zameranie ani natívny záber.</text>']
    for t in polygons:
        parts.append(polygon(t, '#bf9d75'))
    for faces in garden['sourceStepTrianglesCm'].values():
        for t in faces:
            parts.append(polygon(t, '#dddcd4'))
    selected = {p['rootId'] for p in ref['placements']}
    for row in garden['gardenDetailPlacements']:
        if row['id'] in selected:
            continue
        x, y = xy(row['positionCm'])
        parts.append('<circle cx="%.3f" cy="%.3f" r="%.3f" fill="#547352" fill-opacity=".26"/>'%(x,y,row['radiusCm']*scale))
    colors = {'fern_02_a': '#1b5f43', 'fern_02_c': '#438856', 'fern_02_d': '#8ec27c'}
    for row in ref['placements']:
        x, y = xy(row['positionCm'])
        parts.append('<circle cx="%.3f" cy="%.3f" r="%.3f" fill="%s" stroke="#163c2b" stroke-width="1"><title>%s</title></circle>'%
                     (x,y,row['radiusCm']*scale,colors[row['model']],html.escape(row['rootId']+' / '+row['model'])))
    for row in garden['ornamentalPlacements']:
        x,y = xy(row['positionCm'])
        parts.append('<circle cx="%.3f" cy="%.3f" r="%.3f" fill="none" stroke="#9a4e9d" stroke-width="2"/><circle cx="%.3f" cy="%.3f" r="3" fill="#9a4e9d"><title>%s · pôvodný, bez zmeny</title></circle>'%
                     (x,y,row['radiusCm']*scale,x,y,html.escape(row['id'])))
    parts.append('<text x="35" y="615" font-family="sans-serif" font-size="14">Zelená: 36 fern a/c/d. Fialová: všetkých 12 pôvodných vysokých rastlín. Zvyšných 437 koreňov sa zachováva.</text></svg>')
    return '\n'.join(parts)


def main():
    out = g.STUDY
    g.require(not out.exists(), 'Fresh R34 source output only')
    ref = g.reference()
    old, source, base = ref['old'], ref['source'], ref['base']
    # The current immediate parent is audited now; no future native report is invented.
    g.require(old.old.guard.yard.guard.clean.g.inventory(base['project']/'Content') == base['content']
              and old.old.guard.yard.guard.clean.g.project_proof(base['project']) == base['protected'], 'Current actual R29 bytes differ')
    proof = g.footprints(ref)
    controls = g.retained_controls(ref)
    all_rows = source['garden']['gardenDetailPlacements']+source['garden']['ornamentalPlacements']
    ids = {p['rootId'] for p in ref['placements']}
    retained = [r for r in all_rows if r['id'] not in ids]
    hero_ids = [r['id'] for r in source['garden']['ornamentalPlacements']]
    out.mkdir()
    raw = g.export_glb(ref['models'])
    geometry_audit = g.decode_export(raw, ref['models'])
    (out/'fern-only-originals.glb').write_bytes(raw)
    descriptor = {'schema': 'brezi-garden-fern-only-original-geometry-r34', 'owner': OWNER,
                  'status': 'source-three-original-fern-models-exported-native-pending',
                  'models': [{k: v for k, v in ref['models'][m].items() if not k.startswith('_')} for m in g.MODELS],
                  'audit': geometry_audit, 'originalSourceAttributesPreservedExceptDeclaredBottomShift': True,
                  'nativeNormalTangentReadbackAvailable': False, 'nativeR34Applied': False}
    write(out/'geometry-descriptor.json', descriptor)
    write(out/'planned-retained-native-controls.json', {'schema': 'brezi-r34-source-planned437-retained-native-controls', 'owner': OWNER,
          'controls': controls, 'rootCount': 437, 'basis': 'Exact actual R29 controls recorded before R30; two source index filters only.',
          'nativeR34FilteringPerformed': False, 'AdditionalRandomSeedsReadbackAvailable': False,
          'perInstanceShaderRandomValuePreservationClaimed': False, 'survivorTransformReconstructionAllowed': False})
    write(out/'source-crown-proof.json', {'schema': 'brezi-r34-source-original-fern-complete-circle-and-vertex-proof', 'owner': OWNER,
          'historicalNativeMeasurements': ref['r30']['newSourceNativeMeasurements'], 'proof': proof,
          'sourceVerticesChecked': 32124, 'roots': 36, 'nativeR34Applied': False, 'nativeR34FrameMeasurementPerformed': False,
          'freshNativeNormalTangentReadbackAvailable': False, 'sourceCircleIsLeafOrVisibleCoverage': False})
    recipe = {'schema': 'brezi-garden-fern-only-material-recipe-r34', 'owner': OWNER,
              'status': 'source-one-original-fern-map-recipe-native-pending', 'prefix': g.PREFIX+'/Fern', 'newOwnerTag': 'BreziGardenFernOnlyR34:',
              'sourcePlan': source['recipe']['fernSourceStudy'], 'sourceDelegate': source['recipe']['fernDelegate'],
              'privateSourceDelegateKeyMustRemainOriginal': 'ph_original_fern_02_b_r25',
              'sourceVariants': list(g.MODELS), 'sameOriginalProviderMaterialAndAtlasForAllVariants': True,
              'originalAlphaMode': 'MASK', 'originalDoubleSided': True, 'alphaRoute': 'unchanged original 16-bit PNG normalized R -> OpacityMask cutoff0.5',
              'albedo': 'original JPEG sRGB', 'normal': 'original GL normal, linear TCNormalmap, flipGreen true',
              'roughness': 'original ARM.G linear; metallic ARM.B times original metallic0; no glTF occlusion route',
              'engineShadingModel': 'TwoSidedFoliage artistic proposal', 'sourcePixelsEdited': False,
              'materialCount': 1, 'textureObjectCount': 4, 'nativeR34Applied': False, 'nativeAppearanceAccepted': False}
    provider = g.read(ref['models']['fern_02_a']['providerGltf']['path'])
    material_ids = {provider['meshes'][node['mesh']]['primitives'][0]['material'] for node in provider['nodes'] if node['name'] in g.MODELS}
    g.require(len(material_ids) == 1 and provider['materials'][next(iter(material_ids))]['alphaMode'] == 'MASK'
              and provider['materials'][next(iter(material_ids))]['doubleSided'] is True, 'All3 variants must retain original common masked material')
    write(out/'material-recipe.json', recipe)
    (out/'source-layout.svg').write_text(plot(ref))
    (out/'source-producer.py').write_bytes((ROOT/OWNER).read_bytes())
    paired = ROOT/'output/unreal/exterior-validation-20260930-r1/r30b-garden-composition-paired-review-r1.json'
    pair = g.read(paired)
    g.require(pair['pair']['visualReview']['narrowFernMorphologyGainObserved'] is True
              and pair['pair']['visualReview']['tallHeroVolumeRegressionObserved'] is True
              and pair['fullPhotorealismAccepted'] is False, 'Actual original-image reason for fern-only scope required')
    donor_path = ROOT/'output/unreal/exterior-20261002-r32a/context-yard-ground-native-report.json'
    donor = g.read(donor_path)
    g.require(g.sha(donor_path) == '99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19'
              and donor['nativeApplied'] is donor['savedMapUnloadedReloaded'] is True and len(donor['newPackages']) == 8
              and len(donor['addedActors']) == 4, 'Actual closed R32 donor scope required, no copied map')
    inputs = {row['path']: row for row in source['proposal']['inputFiles']}
    for row in [g.pin(ROOT/OWNER), g.pin(ROOT/g.OWNER), base['reportPin'], base['audit'], base['process']['receipt'], base['process']['raw'],
                base['process']['log'], base['report']['savedActorWitness'], base['report']['afterContentInventory'], base['report']['protectedProjectProof'],
                ref['r30Pin'], ref['r30']['originalGardenControls'], ref['r30']['newSourceNativeMeasurements'], g.pin(paired),
                g.pin(donor_path), g.pin(ROOT/'scripts/unreal/exterior-garden-composition-geometry-r30.py'), source['draft']['geometry'],
                source['draft']['materialRecipes'], source['recipe']['fernSourceStudy'], source['recipe']['fernDelegate']]:
        inputs[row['path']] = row
    plan = {'schema': 'brezi-garden-fern-only-source-r34', 'schemaVersion': 1, 'owner': OWNER,
            'status': 'source-only-36-fern-fits-original-ornamentals-retained-native-pending', 'createdAt': datetime.now(timezone.utc).isoformat(),
            'inputFiles': list(inputs.values()), 'activeDesign': source['proposal']['activeDesign'], 'setbacksMm': {'street': 3000, 'east': 3000},
            'actualNativeBase': {'report': base['reportPin'], 'process': base['process'], 'currentByteAudit': base['audit'],
                                'currentContent4060Protected132BytesVerifiedByProducer': True},
            'nativeClone': None, 'candidateOutputProposed': str(ROOT/'output/unreal/exterior-20261002-r34a'),
            'requiredCloneReceipt': {'filename': 'garden-fern-only-project-clone.json',
                                    'status': 'verified-original-r29a-independent-apfs-r34-clone-before-fern-only-native',
                                    'sourceProject': str(base['project']), 'originalProjectFiles': 4192, 'contentFiles': 4060, 'protectedFiles': 132,
                                    'selectedPlanInitially': None, 'nativeExecutedInitially': False},
            'priorVisualReason': {'actualOriginalPair': g.pin(paired), 'fernMorphologyGainVisible': True, 'twoTallHeroVolumeRegressionVisible': True,
                                 'all36IndividualFernVisibleCountMeasured': False, 'ownR34NativeAppearanceAccepted': False},
            'expectedCounts': g.COUNTS, 'proposedPlacements': ref['placements'], 'originalAllRowsSha256': g.digest(all_rows),
            'retainedSourceRowsSha256': g.digest(retained), 'preservedOrnamentalRootIds': hero_ids,
            'sourceGroupFilters': source['proposal']['sourceGroupFilters'], 'wholeOneMemberHeroGroupRetirements': [],
            'originalGardenGroupBindings': {key: {k: v[k] for k in ('actor', 'component', 'oldMesh')} for key, v in ref['groups'].items()},
            'geometryDescriptor': g.pin(out/'geometry-descriptor.json'), 'sourceGlb': g.pin(out/'fern-only-originals.glb'),
            'sourceCrownProof': g.pin(out/'source-crown-proof.json'), 'plannedRetainedNativeControls': g.pin(out/'planned-retained-native-controls.json'),
            'materialRecipe': g.pin(out/'material-recipe.json'), 'sourceLayout': g.pin(out/'source-layout.svg'), 'producerSnapshot': g.pin(out/'source-producer.py'),
            'budget': {'uniqueSourceTriangles': 3848, 'uniqueSourceVertices': 2677, 'instancedSourceTriangles': 46176,
                       'sourceCrownVerticesChecked': 32124, 'providerLodsPerMaster': 1, 'newHismGroups': 3, 'retiredWholeOriginalGroups': 0,
                       'partiallyFilteredOriginalGroups': 2, 'proposedAdditionalNonemptyDrawGroups': 3, 'performanceVerified': False},
            'nativeExecutionRequirements': {'twoExactOriginalIndexFiltersOnly': True, 'all437RawMatricesRecoveredOrderMainSeedAndCustomDataExact': True,
              'all12OriginalOrnamentalActorsAndMembersUnchanged': True, 'all41FlowersUnchanged': True, 'remaining384LowStarsUnchanged': True,
              'wrappedOriginalXYZAndQuaternionCopiedForNewRoots': True, 'remeasureUnregisteredMeshlessTransientBeforeMutation': True,
              'retainedTransformRecompositionAllowed': False, 'seedSetterAllowed': False, 'AdditionalRandomSeedsReadbackAvailable': False,
              'shaderRandomIdentityPreservationClaimed': False, 'threeWholeOriginalSingleLodMasterMeshesOnly': True,
              'originalNormalsUV0IndicesWindingOrderPreserved': True, 'derivedBottomShiftOnly': True,
              'nativeNormalsTangentsReadbackAvailable': False, 'ownedF32Full3848TriangleProofRequired': True,
              'noSourcePixelBakingOrNewTangentAttribute': True, 'allOriginal59Graphs87TexturesAndProjectBytesProtected': True,
              'onlyOldMapAnd11OwnedPackagesMayChange': True, 'savedMapUnloadReloadRequired': True},
            'futureYardIntegration': {'gardenNativeReport': None, 'ownGardenVisualAcceptanceRequired': True,
              'yardDonorNativeReport': g.pin(donor_path), 'onlyExactDonor8Packages': donor['newPackages'], 'onlyExactDonor4ActorTemplates': donor['addedActors'],
              'donorOldGroundRebindings': donor['targets'], 'copyDonorMapOrR30GardenAllowed': False, 'integrationApplied': False},
            'limits': ['The36 low fern height-role changes remain explicitly artist-authored; original root/contact/yaw/circle masks are preserved.',
                      'All12 original ornamental heights and volumes remain original; no blanket all-fern or remaining384star-leaf replacement.',
                      'Containing circles and source-frustum bounds are neither leaf-area coverage nor visibility/occlusion proof.',
                      'Prior actual R30 native matrices are source-proof evidence only; R34 must independently remeasure and save its own scene.',
                      'AdditionalRandomSeeds ranges are unavailable. No range reconstruction/setter or per-instance shader-random identity claim.',
                      'Ecological suitability, garden elevation and legal parcel accuracy are not surveyed. Native/visual proof remains pending.'],
            'sourceValidated': True, 'nativeApplied': False, 'nativeGeometryVerified': False, 'nativeAppearanceAccepted': False,
            'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'shippingVerified': False, 'packageVerified': False}
    g.selection(plan, ref)
    write(out/'fern-only-source-plan.json', plan)
    g.load_source()
    print(json.dumps({'plan': g.pin(out/'fern-only-source-plan.json'), 'glb': plan['sourceGlb'], 'geometry': plan['geometryDescriptor'],
                      'recipe': plan['materialRecipe'], 'layout': plan['sourceLayout'], 'expectedCounts': g.COUNTS, 'nativeExecuted': False}))


if __name__ == '__main__':
    main()
