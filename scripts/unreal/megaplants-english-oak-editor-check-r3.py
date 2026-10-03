"""CPU-only closure of an actually saved, separate original-D USD probe.

This checks the recorded native gates and immutable source. It never loads
Unreal, decodes native geometry, or accepts appearance/performance.
"""
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
_path = Path(__file__).with_name('megaplants-english-oak-pilot-guards-r3.py')
_spec = importlib.util.spec_from_file_location('oak_editor_source_guard', _path)
g = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g)
OWNER = 'scripts/unreal/megaplants-english-oak-pilot-native-r3.py'
NATIVE_SHA = '65c40b4217715cfb06e8994ffe2b5b5ab47b727a817cb36d13a3d19806c59978'
PLAN_SHA = '5428489ce735bba97ef800bba5d632f728c39e24e734827234b92ce1088af772'
STATUS = 'saved-original-whole-D-usd-experimental-probe-materials-constant'
_native_path = g.ROOT / OWNER
_native_spec = importlib.util.spec_from_file_location('oak_frozen_native_source_only', _native_path)
n = importlib.util.module_from_spec(_native_spec)
_native_spec.loader.exec_module(n)


def validate_report(report, plan, base, preparation):
    g.require(report['schema'] == g.SCHEMA and report['owner'] == OWNER
              and report['status'] == STATUS, 'Only the known successful original-D native report is accepted')
    g.require(report['selectedPlan'] == g.pin(g.PLAN)
              and report['selectedPlan']['sha256'] == PLAN_SHA, 'Selected original-D source plan differs')
    g.require(report['project'] == str(g.PROJECT) and report['map'] == g.MAP, 'Separate probe map/project differs')
    g.require(isinstance(report['nativeProcessId'], int) and report['nativeProcessId'] > 0, 'Actual process ID required')
    for key in ('nativeApplied', 'probeMapUnloadedReloaded', 'originalMainMapUnchanged',
                'originalSavedR32ProjectUnchanged', 'originalUsdSourceUnmodified',
                'originalConstantMaterialsPreserved', 'daylightCopiedByNativeActorDuplication'):
        g.require(report[key] is True, 'Actual saved native gate missing: ' + key)
    for key in ('nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted',
                'shippingVerified', 'packageVerified', 'windSidecarImported', 'dynamicWindEvaluated',
                'nativeFullGeometryCornerReadbackAvailable', 'importedNormalsTangentsPreserved',
                'actualNaniteGpuPassAttributedToTree', 'nativeScratchCapEnforced'):
        g.require(report[key] is False, 'Unestablished pilot claim: ' + key)
    g.require(report['nativeTextureObjectsImported'] == 0 and report['nativeScratchBytesEstimated'] is None,
              'No photo replacement or invented native storage estimate allowed')
    for key in ('sourceArchive', 'sourceExtraction', 'usdInspection', 'baseNativeReport', 'initialRootClone'):
        g.require(report[key] == plan[key], 'Original source/base pin differs: ' + key)
    g.require(report['projectPreparation'] == g.pin(g.OUTPUT / 'oak-usd-project-preparation-r3.json'),
              'Actual descriptor-stage witness required')
    g.require(preparation['schema'] == g.SCHEMA and preparation['selectedPlan'] == g.pin(g.PLAN)
              and preparation['status'] == 'verified-own-usd-plugin-and-startup-assembly-only-stage-native-pending-r3'
              and preparation['descriptorBefore'] == g.pin(g.BASE / 'Project/BreziTwin/BreziTwin.uproject')
              and preparation['pluginAddition'] == g.PLUGIN and preparation['nativeExecuted'] is False
              and preparation['startupConfigDelta'] == plan['startupConfigDelta']
              and preparation['startupConfigBefore'] == plan['startupConfigOriginal'],
              'Only exact own plugin and startup assembly additions are admitted')
    g.require(preparation['startupConfigAfter'] == g.pin(g.PROJECT / 'Config/DefaultEngine.ini')
              and (g.PROJECT / 'Config/DefaultEngine.ini').read_text() ==
              g.startup_config(Path(preparation['startupConfigBefore']['path']).read_text()),
              'Current startup config must equal the exact one-line source delta')
    g.require(report['startupReadback'] == {'r.Nanite.AllowAssemblies': 1, 'r.Nanite.Foliage': 0}
              and report['selectedRootUsdPrimPath'] == plan['stageRoot']
              and report['nameOnlySelectionUsed'] is False
              and report['allSourcePrototypePartReferencesMeasured'] is True,
              'Actual fresh startup and source-root assembly selection required')
    original_content = g.read(g.check_pin(base['afterContentInventory']))
    original_protected = g.read(g.check_pin(base['protectedProjectProof']))
    original = {**{'Content/' + k: v for k, v in original_content.items()}, **original_protected}
    g.require(len(original_content) == 4086 and len(original_protected) == 132, 'Actual saved R32 scope differs')
    expected_before = dict(original)
    expected_before['BreziTwin.uproject'] = {k: preparation['descriptorAfter'][k] for k in ('sha256', 'bytes')}
    expected_before['Config/DefaultEngine.ini'] = {k: preparation['startupConfigAfter'][k] for k in ('sha256', 'bytes')}
    g.require(report['beforeInventory'] == expected_before, 'Original native input inventory differs')
    g.require(g.validate_delta(report['beforeInventory'], report['afterInventory']) == report['projectDelta'],
              'Declared native delta differs from its independently reconstructed scope')
    g.require('Content/Brezi/EnglishOakPilot20261002R3/Maps/EnglishOakPilot.umap'
              in report['projectDelta']['newFiles'], 'Separate saved probe map is missing')
    camera = report['cameraDataDelta']
    g.require(camera['before'] == g.pin(g.BASE / 'Project/BreziTwin/Content/Data/viewpoints.json')
              and camera['originalPrefixExact'] is True and camera['addedCamera'] == plan['camera'],
              'Original camera prefix/own pilot camera differs')
    source_views = g.read(camera['before']['path'])
    actual_views = g.read(g.PROJECT / 'Content/Data/viewpoints.json')
    expected_views = dict(source_views)
    expected_views['views'] = [*source_views['views'], plan['camera']]
    g.require(actual_views == expected_views and camera['after'] == g.pin(g.PROJECT / 'Content/Data/viewpoints.json'),
              'Only the exact one-camera append is allowed')
    g.require(report['usdImportFactory'] == 'UsdStageAssetImportFactory'
              and report['optionsReadback']['import_actors'] is False
              and report['optionsReadback']['import_geometry'] is True
              and report['optionsReadback']['import_materials'] is True
              and report['optionsReadback']['use_existing_asset_cache'] is False
              and report['optionsReadback']['prims_to_import'] == [plan['stageRoot']]
              and report['importCollapseCvarDuring'] == 0, 'Original assembly import route differs')
    assets = report['assets']
    g.require(assets and len({r['path'] for r in assets}) == len(assets)
              and all(r['path'].startswith(g.PREFIX + '/OriginalUSD/') for r in assets),
              'Native source assets escape the isolated namespace')
    g.require(not any('Texture' in r['class'] for r in assets), 'Unexpected native tree texture objects')
    selected = n.whole_tree_observation(assets, plan)
    g.require(selected['path'] == report['wholeTreeMesh']
              and report['selectedRootNativeName'] == selected['path'].split('.')[-1],
              'Recorded selected source-root asset differs from independently resolved source metadata')
    native_parts = selected['assemblyPartPaths']
    skeletal_paths = {r['path'] for r in assets if r['class'] == '/Script/Engine.SkeletalMesh'}
    g.require(all(p in skeletal_paths for p in native_parts), 'All eleven parts must bind actual own skeletal assets')
    g.require(selected['softObjectPathReadbackRoute'] ==
              'actual-R2-diagnostic-to_tuple-single-string-and-get_object_from_soft_path'
              and isinstance(report['nativeAssemblyNodeCountReadbackAvailable'], bool)
              and report['nativeAssemblyNodeCountReadbackAvailable'] == selected['nativeAssemblyNodesReadbackAvailable'],
              'Actual soft-path/node availability annotation differs')
    expected_colors = {(0.1420000046491623, 0.06599999964237213, 0.03099999949336052),
                       (0.08699999749660492, 0.15299999713897705, 0.020999999716877937)}
    actual_colors = {tuple(r['vectorParameters']['BaseColor'][:3]) for r in assets
                     if 'BaseColor' in r.get('vectorParameters', {})}
    g.require(actual_colors == expected_colors, 'Original constant USD colors differ')
    g.require(all(r.get('authoredTextureParameterCount', 0) == 0 for r in assets), 'Tree texture substitution is forbidden')
    g.require(report['treeActor'].startswith(g.MAP + '.') and report['groundActor'].startswith(g.MAP + '.')
              and report['treeActor'] != report['groundActor'], 'Tree and neutral ground must belong to the separate map')
    lights = report['nativeSourceLightingObserved']
    g.require(sum(r['class'] == '/Script/Engine.DirectionalLight' for r in lights) == 1
              and sum(r['class'] == '/Script/Engine.SkyLight' for r in lights) == 1,
              'Actual observed native day sun/sky required')
    return {'mode': 'original-licensed-whole-D-usd-isolated-editor-pilot',
            'nativeProcessId': report['nativeProcessId'], 'map': report['map'],
            'nativeImportedAssets': len(assets), 'nativeAssemblyPartReferences': len(native_parts),
            'sourceUniqueBuildFanTriangles': plan['sourceUniqueBuildFanTriangles'],
            'sourceExpandedFanTrianglesEstimate': plan['sourceBasePlusExpandedFanTrianglesEstimate'],
            'nativeFullGeometryCornerReadbackAvailable': False,
            'nativeAssemblyNodeCountReadbackAvailable': report['nativeAssemblyNodeCountReadbackAvailable'],
            'importedNormalsTangentsPreserved': False,
            'observedImporterWarnings': report['observedImporterWarnings'],
            'startupReadback': report['startupReadback'],
            'nativeTextureObjectsImported': 0, 'originalConstantMaterialsPreserved': True,
            'probeMapUnloadedReloaded': True, 'originalMainMapUnchanged': True,
            'lightingSnapshotScope': 'observed authored subset copied by native full actor duplication',
            'walkingAuditAvailableInIsolatedMap': False, 'windSidecarImported': False,
            'nativeAppearanceAccepted': False, 'performanceAccepted': False,
            'fullPhotorealismAccepted': False, 'shippingVerified': False, 'packageVerified': False}


def main():
    report_path = Path(sys.argv[1]).resolve()
    g.require(report_path == g.OUTPUT / 'oak-usd-native-pilot-report-r3.json', 'Only the exact own native report is accepted')
    g.require(g.sha(g.ROOT / OWNER) == NATIVE_SHA, 'Frozen native pilot helper changed')
    plan, base = g.validate_plan()
    preparation = g.read(g.OUTPUT / 'oak-usd-project-preparation-r3.json')
    result = validate_report(g.read(report_path), plan, base, preparation)
    print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    main()
