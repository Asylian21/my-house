"""CPU-only R12 reader for the actual saved R24b R2 tree; no Unreal import."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-original-tree-editor-check-r12.py'
NATIVE = 'scripts/unreal/exterior-original-tree-native-r2.py'
NATIVE_SHA = 'c719f61f70bafd53e296cc2ac7167233a604e0f69692381bb6951e3a0a381f87'
REPORT_SHA = '869ed396ed7946cb0ea562d3f2da77f8dbd9f3d65777250b9686171697aa10f1'
s = importlib.util.spec_from_file_location('r12_actual_saved_tree', ROOT/NATIVE)
n = importlib.util.module_from_spec(s); s.loader.exec_module(n)
g = n.guard


def validate_saved(r, bundle, base, pf):
    q = n.require
    read = lambda key: n.read(n.check_pin(r[key]))
    q(r['schemaVersion'] == 2 and r['owner'] == NATIVE and r['status'] == 'verified-saved-single-original-tree-overlay'
      and r['output'] == str(g.CANDIDATE) and r['project'] == str(g.CANDIDATE/'Project/BreziTwin')
      and r['savedMapUnloadedReloaded'] is True, 'Only actual saved R24b R2 is eligible')
    q(r['baseNativeReport'] == base['pin'] and r['baseNativeProcess'] == base['process']
      and r['baseNativeHelper'] == base['nativeHelperPin'] and r['projectClone'] == pf['candidateProjectClone']
      and r['importOrderRepair'] == pf['importOrderRepair'] and r['inputFiles'] == pf['inputFiles']
      and r['pipelineFiles'] == pf['pipelineFiles'], 'Actual source/base/repair scope changed')
    for k in ('nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified', 'packageVerified',
              'ecologicalFitVerified', 'naniteRenderPassVerified', 'nativeNormalTangentReadbackAvailable',
              'nativeGeometryPackagesIndependentlyReloaded', 'nativeMaterialsPackagesIndependentlyReloaded', 'sourceRootGroundElevationSurveyed'):
        q(r[k] is False, 'Unsupported acceptance: '+k)
    q(r['activeDesign'] == {'variant':'C', 'heatingLayout':'B', 'livingLayout':'B'}
      and r['setbacksMm'] == {'street':3000, 'east':3000} and r['originalSavedR22Unchanged'] is True,
      'Architecture/base protection changed')
    before, expected, saved = [read(k) for k in ('beforeActorWitness','expectedActorWitness','savedActorWitness')]
    q(before == base['witness'] and len(before) == r['originalActorCount'] == 5346, 'Original full actor state changed')
    q(expected == saved and len(saved) == r['savedActorCount'] == 5347
      and [n.digest(x) for x in (before, expected, saved)] == [r[k] for k in
          ('beforeActorWitnessSha256','expectedActorWitnessSha256','savedActorWitnessSha256')], 'Actual complete counterfactual differs')
    path = bundle['selection']['originalNativeActor']; added = r['newTree']['actor']
    old = copy.deepcopy(before)
    old[path]['components'][0]['instanceCount'] = 3
    old[path]['components'][0]['orderedInstanceTransformsSha256'] = saved[path]['components'][0]['orderedInstanceTransformsSha256']
    q(all(saved[k] == v for k,v in old.items()) and set(saved)-set(before) == {added}, 'Any unlisted original actor policy changed')
    retire = r['originalRootRetirement']
    q(retire['retiredOriginalIndex'] == 0 and retire['retainedOriginalIndices'] == [1,2,3]
      and len(retire['storedMatricesBefore']) == 4 and retire['storedMatricesRetained'] == retire['storedMatricesBefore'][1:]
      and retire['allRetainedNativeMatrixAndRecoveredTransformBytesExact'] is True
      and retire['nativeRemovalInitialOrder'] == [3,1,2]
      and retire['retainedSourceOrderRestoredWithoutTransformRecomposition'] is True
      and r['newTreeActors'] == r['retiredTreeInstances'] == 1 and r['retainedOriginalTreeInstances'] == 3,
      'Retained original tree matrix/order proof changed')
    actor = saved[added]; c = actor['components'][0]; tree = r['newTree']
    q(actor['class'] == '/Script/BreziTwin.BreziVegetationPatch' and len(actor['components']) == 1
      and actor['tags'] == ['BreziGenerated','BreziOriginalTree20261002R24'] and actor['actorTick'] is False
      and actor['detailDensityScaling'] is False and actor['hidden'] is False,
      'Owned tree identity/runtime classification changed')
    identity = [[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]]
    q(actor['transform'] == c['transform'] == identity and c['mesh'] == r['newMesh'] and c['instanceCount'] == 1
      and c['orderedInstanceTransformsSha256'] == n.digest([tree['actualRecoveredTransform']])
      and c['overrideMaterials'] == [] and c['visible'] is True and c['hiddenInGame'] is False
      and c['collision'] == '<CollisionEnabled.NO_COLLISION: 0>' and c['collisionProfile'] == 'NoCollision'
      and c['navigation'] is False and c['overlapEvents'] is False and c['componentTick'] is False
      and c['instanceCullCm'] == [62500,125000] and c['renderFlags']['cast_shadow'] is True
      and c['renderFlags']['visible_in_ray_tracing'] is True, 'New HISM transform/NoCollision/render policy changed')
    q(tree['instanceCount'] == 1 and tree['sourceNodeFit'] == pf['nativePlacementContract']
      and tree['originalRootRotationCopiedBeforeInsertion'] is True and tree['nativeVisualAccepted'] is False
      and tree['nativeNormalsTangentsHandednessReadbackAvailable'] is False,
      'Owned matrix/source fit acceptance changed')
    footprint = r['actualStoredMatrixFullVertexMaskProof']
    q(footprint['decodedFullOriginalVertices'] == 1777278 and footprint['completeOriginalTriangleInteriorsConservativelyProven'] == 2062487
      and footprint['nativeStoredMatrixReadbackUsed'] is True and footprint['float32ProjectionIsGpuReadback'] is False
      and footprint['sourceLandUseAndElevationSurveyed'] is False and footprint['normalTangentNativeReadbackAvailable'] is False
      and all(x > 75 for x in footprint['sourceExclusionCircleClearancesCm'].values())
      and set(footprint['sourceExclusionCircleClearancesCm']) == {'protected','subject','roads','buildings','cultivatedGround','managedLawn'}
      and footprint['originalGroveCircleClearanceCm'] > 0 and footprint['allVertexContainingCircleRadiusCm'] < bundle['selection']['originalSourceRow']['radiusCm'],
      'Actual matrix all-vertex source mask proof changed')
    geo = r['nativeSourceGeometry']
    q(geo['mesh'] == r['newMesh'] and geo['sourceTriangles'] == 2062487 and geo['sourceDescriptionVertices'] == 1777278
      and geo['sourceDescriptionVertexInstances'] == 6187461 and geo['sourceLODCount'] == 1
      and geo['sampledNativeTriangles'] == 4096 and geo['unsampledNativeTriangles'] == 2058391
      and geo['nativeSampledPositionUV0UV1SectionOrderVerified'] is True and geo['nativeSourceSectionPolygonCountsVerified'] is True
      and geo['nativeFullPositionUV0UV1CornerReadbackPerformed'] is False and geo['nativeNormalTangentReadbackAvailable'] is False
      and geo['nativeTangentHandednessVerified'] is False and geo['sourceDerivedTangentRequestOnly'] is True
      and geo['renderFallbackTriangles'] == 2247 and geo['renderFallbackSections'] == 3, 'Source/Nanite/fallback/sample limits were conflated')
    q(len(geo['sourceSections']) == 3, 'All original sections required')
    for row,wanted in zip(geo['sourceSections'], pf['nativeExpectedSections']):
        q(row == {'section':wanted['section'], 'material':wanted['material'], 'sourceSectionPolygonCount':wanted['triangles'],
          'sampleTriangleIndices':wanted['sampleTriangleIndices'], 'sampleTriangles':wanted['sampleTriangles'],
          'sampledFloat32PositionUV0UV1OrderedCornerSha256':wanted['sampledFloat32PositionUV0UV1OrderedCornerSha256'],
          'fullSourceCornerHashCpuOnly':wanted['orderedFloat32PositionUV0UV1CornersSha256']}, 'Actual exact ordered UV0/UV1 sample differs')
    nanite = r['naniteResourceReadback']
    q(r['nativeNaniteResourcesBuilt'] is True and nanite['enabled'] is True and nanite['actualNonemptyResourceGetterVerified'] is True
      and nanite['nativeResourceInputTriangles'] == 2062487 and nanite['nativeResourceInputVertices'] == 1777276
      and nanite['nativeRenderPassVerified'] is False and nanite['performanceAccepted'] is False and nanite['shippingVerified'] is False,
      'Built input census cannot claim an actual Nanite render pass')
    old_material = read('originalMaterialTextureSaved')
    q(old_material == read('originalMaterialTextureBefore') == n.read(n.check_pin(base['report']['materialsSaved']))
      and r['originalMaterialGraphsPreserved'] == old_material['scopedMaterialGraphs'] == 56
      and r['originalTextureObjectsPreserved'] == old_material['scopedTextureObjects'] == 84, 'Existing56/84 graphs/textures changed')
    material = r['materials']; maps = g.module('r12_frozen_tree_materials', 'exterior-original-tree-materials.py')
    q(material['owner'] == maps.OWNER and material['materialCount'] == 3 and material['textureCount'] == 10
      and material['nativeAppearanceAccepted'] is False and material['nativeNormalTangentReadbackAvailable'] is False,
      'Exact3/10 new unaccepted materials required')
    paths = []
    for recipe in bundle['recipes']:
        row = material['materials'][recipe['id']]; q(row['recipe'] == recipe and row['compileErrors'] == [], 'Original recipe/compile failure')
        paths.append(row['asset']); maps.check_graph(row['graph'], recipe, {key:v['asset'] for key,v in row['textures'].items()})
        policy = row['policy']; leaf = recipe['alphaSource'] is not None
        q(maps.token(policy['blendMode']) == ('BLENDMASKED' if leaf else 'BLENDOPAQUE')
          and maps.token(policy['shadingModel']) == ('MSMTWOSIDEDFOLIAGE' if leaf else 'MSMDEFAULTLIT')
          and policy['twoSided'] is True and policy['tangentSpaceNormal'] is True and policy['useMaterialAttributes'] is False
          and policy['opacityMaskClipValue'] == .5 and policy['naniteUsage'] is True and policy['instancedStaticMeshUsage'] is True
          and policy['nativeBasisReadbackAvailable'] is False, 'Source-defined material optical/UV interpretation differs')
        for key,v in row['textures'].items():
            source = recipe['alphaSource'] if key == 'alpha' else recipe['sourceMaps'][key]
            q(v['source'] == source, 'Original photograph pixels changed')
            snap = v['snapshot']; normal = key == 'normalGL'; mask = key in ('ARM','alpha'); color = key == 'albedo'
            q(snap['srgb'] == color and snap['flip_green_channel'] == normal and snap['pixels'] == [2048,2048]
              and maps.token(snap['compression_settings']) == ('TCNORMALMAP' if normal else 'TCMASKS' if mask else 'TCDEFAULT')
              and maps.token(snap['sourceEncoding']) == ('TSESRGB' if color else 'TSENONE'), 'Native texture color/normal/mask policy changed')
    q(c['materials'] == paths, 'All three owned section bindings differ')
    before_content, content, protected = [read(k) for k in ('baseContentInventory','afterContentInventory','protectedProjectProof')]
    q(before_content == base['content'] and protected == base['protected'] and len(protected) == 132, 'Original project inventory changed')
    packages = [r['newMesh'], *r['importPipelineAssets'], *paths,
      *[v['asset'] for m in material['materials'].values() for v in m['textures'].values()]]
    packages = [p.split('.')[0].removeprefix('/Game/')+'.uasset' for p in packages]
    q(packages == r['newContentPackages'] and g.validate_content(before_content, content, packages) == r['assetDelta'], 'Actual17-package/map-only Content delta changed')
    hisms = [c for a in saved.values() for c in a['components'] if c['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent']
    q(len(hisms) == 2313 and sum(c['instanceCount'] for c in hisms) == 676944, 'Actual whole-scene HISM census differs')
    return {'mode':'saved-single-original-tree-overlay','originalActors':5346,'savedActors':5347,'fullSceneHismComponents':2313,
      'fullSceneHismInstances':676944,'retiredTreeRoots':1,'retainedExactOriginalTreeRoots':3,'newTreeRoots':1,
      'contentFiles':4066,'newPackages':17,'protectedProjectFiles':132,'preservedMaterialGraphs':56,'preservedTextureObjects':84,
      'newMaterialGraphs':3,'newTextureObjects':10,'sourceDescriptionTriangles':2062487,'sampledNativeTriangles':4096,
      'unsampledNativeTriangles':2058391,'nativeFallbackTriangles':2247,'nativeFallbackSections':3,
      'naniteResourceInputTriangles':2062487,'naniteResourceInputVertices':1777276,'nativeNaniteRenderPassVerified':False,
      'fullNativeCornerReadbackPerformed':False,'nativeNormalTangentReadbackAvailable':False,'performanceAccepted':False,
      'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'sourceRootGroundElevationSurveyed':False}


def main():
    n.require(n.sha(ROOT/NATIVE) == NATIVE_SHA, 'Frozen successful helper changed')
    path = Path(sys.argv[1]).resolve(); n.require(path == g.CANDIDATE/n.REPORT and n.sha(path) == REPORT_SHA, 'Exact actual saved R24b report required')
    r = n.read(path); bundle = g.load_source(); base = g.load_saved_base()
    pf,_ = n.validated_preflight(n.check_pin(r['sourcePreflight']), bundle, base)
    summary = validate_saved(r,bundle,base,pf)
    terminal = base['guard'].actual_terminal(path,path.parent/'original-tree-native-r2-process.json',NATIVE,'original-tree-native-r2')
    n.require(len(n.read(terminal['receipt']['path'])['sourcePinsBeforeNative']) == 566, 'Actual566 terminal source pins required')
    project = Path(r['project']); policy = base['guard'].g
    n.require(policy.inventory(project/'Content') == n.read(n.check_pin(r['afterContentInventory']))
      and policy.project_proof(project) == base['protected']
      and policy.inventory(g.BASE/'Project/BreziTwin/Content') == base['content']
      and policy.project_proof(g.BASE/'Project/BreziTwin') == base['protected'], 'Actual project/base bytes differ')
    print(json.dumps(summary))


if __name__ == '__main__': main()
