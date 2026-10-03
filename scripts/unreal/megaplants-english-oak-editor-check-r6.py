"""CPU closure for the actual separate scene-only original-Oak R6 receipt.

No Unreal calls or native geometry decoding. Full scene/property cloning,
wind, walking, native normals/tangents and appearance remain unestablished.
"""
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
_p = Path(__file__).with_name('megaplants-english-oak-scene-guards-r6.py')
_s = importlib.util.spec_from_file_location('oak_editor_scene_guard_r6', _p)
g = importlib.util.module_from_spec(_s); _s.loader.exec_module(g)
_p = Path(__file__).with_name('megaplants-english-oak-scene-native-r6.py')
_s = importlib.util.spec_from_file_location('oak_frozen_scene_source_r6', _p)
n = importlib.util.module_from_spec(_s); _s.loader.exec_module(n)
OWNER = 'scripts/unreal/megaplants-english-oak-scene-native-r6.py'
NATIVE_SHA = '83c1cd9071e64a63c08d300a80dbfa6ae23ffad0ee9d895f79da24bfd9d4f667'
PLAN_SHA = 'fcbae7cab8c5c10db4c36bf0affd9b9020363a14db5d6ea9b92ab750874841d8'
FINAL_REPORT_SHA = '933739a45dad7d95babb3dfc77231b2126ed9c0f022f8dba9c00d01ffc1633e9'
FINAL_NATIVE_PID = 30697


def validate_report(report, plan, source, base, before):
    g.require(report['schema'] == g.SCHEMA and report['owner'] == OWNER
              and report['status'] == n.STATUS, 'Only the scene-only R6 native success is accepted')
    g.require(report['selectedPlan'] == g.pin(g.PLAN)
              and report['selectedPlan']['sha256'] == PLAN_SHA, 'Selected scene-only source differs')
    g.require(report['project'] == str(g.PROJECT) and report['map'] == g.MAP
              and report['nativeProcessId'] == FINAL_NATIVE_PID, 'Own R6 project/map/process differs')
    for key in ('nativeApplied', 'probeMapUnloadedReloaded', 'originalMainMapUnchanged',
                'originalSavedR32ProjectUnchanged', 'all39SavedOriginalUsdPackagesByteExact',
                'originalConstantMaterialsPreserved', 'explicitObservedLightingSubsetCopiedAndReloaded',
                'exactMeasuredSetterAndReloadedLightingSubsetVerified'):
        g.require(report[key] is True, 'Recorded saved gate missing: ' + key)
    for key in ('assetImportExecuted', 'nativeAppearanceAccepted', 'fullPhotorealismAccepted',
                'performanceAccepted', 'shippingVerified', 'packageVerified', 'windSidecarImported',
                'dynamicWindEvaluated', 'nativeFullGeometryCornerReadbackAvailable',
                'importedNormalsTangentsPreserved', 'actualNaniteGpuPassAttributedToTree',
                'walkingCollisionAccepted', 'matchedExteriorLightingPairClaimed',
                'fullLightingPropertyCloneClaimed', 'daylightCopiedByNativeActorDuplication', 'numericalToleranceApplied'):
        g.require(report[key] is False, 'Unestablished pilot claim: ' + key)
    g.require(report['savedOriginalUsdPackages'] == 39 and report['nativeTextureObjectsImported'] == 0,
              'Exactly preserved original assets, without replacement textures, required')
    for key in ('originalSourcePlan', 'sourceExtraction', 'usdInspection', 'baseNativeReport',
                'initialRootClone', 'projectPreparation', 'crashedImportByteAudit', 'failedSceneByteAudit',
                'beforeInventory', 'measuredLightingReference'):
        g.require(report[key] == plan[key], 'Selected source pin differs: ' + key)
    g.require(g.read(g.check_pin(report['beforeInventory'])) == before and len(before) == 4259,
              'Independent 4218 original +39 preserved packages +2 failed maps basis differs')
    g.require(g.validate_delta(before, report['afterInventory']) == report['projectDelta']
              and len(report['afterInventory']) == 4261, 'Recorded new map/material/Data delta differs')
    g.require(report['nativeStartupReadback'] == {'r.Nanite.AllowAssemblies': 1, 'r.Nanite.Foliage': 0}
              and report['selectedRootUsdPrimPath'] == source['stageRoot'], 'Native startup/source root differs')
    g.require(report['activeEditorMapInitialization'] == {
        'newLevelReturnedTrue': True, 'editorWorld': g.MAP + '.EnglishOakPilotR6',
        'currentLevel': g.MAP + '.EnglishOakPilotR6:PersistentLevel'}, 'Active editor map creation not established')
    preparation = g.read(g.check_pin(report['projectPreparation']))
    g.require(preparation['schema'] == g.original.SCHEMA
              and preparation['status'] == 'verified-own-usd-plugin-and-startup-assembly-only-stage-native-pending-r3'
              and preparation['selectedPlan'] == plan['originalSourcePlan']
              and preparation['pluginAddition'] == g.original.PLUGIN
              and preparation['nativeExecuted'] is False
              and preparation['startupConfigDelta'] == source['startupConfigDelta']
              and preparation['startupConfigBefore'] == source['startupConfigOriginal'],
              'Only the exact existing R3 startup/plugin stage is admitted')
    g.require(preparation['descriptorBefore'] == g.pin(g.BASE / 'Project/BreziTwin/BreziTwin.uproject')
              and preparation['startupConfigAfter'] == g.pin(g.PROJECT / 'Config/DefaultEngine.ini')
              and (g.PROJECT / 'Config/DefaultEngine.ini').read_text() == g.original.startup_config(
                  Path(preparation['startupConfigBefore']['path']).read_text()), 'Current startup bytes differ')
    camera = report['cameraDataDelta']
    g.require(camera['before'] == g.pin(g.BASE / 'Project/BreziTwin/Content/Data/viewpoints.json')
              and camera['originalPrefixExact'] is True and camera['addedCamera'] == plan['camera'],
              'Source camera prefix/own exact camera differs')
    original_views = g.read(camera['before']['path'])
    g.require(g.read(g.PROJECT / 'Content/Data/viewpoints.json') == {
        **original_views, 'views': [*original_views['views'], plan['camera']]}
        and camera['after'] == g.pin(g.PROJECT / 'Content/Data/viewpoints.json'),
        'Only the exact one-camera Data append is admitted')
    assets = report['assets']
    g.require(len(assets) == 39 and len({r['path'] for r in assets}) == 39
              and all(r['path'].startswith(g.PREFIX + '/OriginalUSD/') for r in assets)
              and not any('Texture' in r['class'] for r in assets), 'Preserved own39 asset census differs')
    selected = n.n.whole_tree_observation(assets, source)
    g.require(selected['path'] == report['wholeTreeMesh']
              and len(selected['assemblyPartPaths']) == 11
              and all(p in {r['path'] for r in assets if r['class'] == '/Script/Engine.SkeletalMesh'}
                      for p in selected['assemblyPartPaths'])
              and selected['softObjectPathReadbackRoute'] ==
              'actual-R2-diagnostic-to_tuple-single-string-and-get_object_from_soft_path',
              'Original root metadata and eleven resolved native skeletal references required')
    g.require(isinstance(report['nativeAssemblyNodesReadbackAvailable'], bool)
              and report['nativeAssemblyNodesReadbackAvailable'] == selected['nativeAssemblyNodesReadbackAvailable'],
              'Protected native assembly-node availability differs')
    colors = {tuple(r['vectorParameters']['BaseColor'][:3]) for r in assets
              if 'BaseColor' in r.get('vectorParameters', {})}
    g.require(colors == {(.1420000046491623, .06599999964237213, .03099999949336052),
                         (.08699999749660492, .15299999713897705, .020999999716877937)}
              and all(r.get('authoredTextureParameterCount', 0) == 0 for r in assets),
              'Faithful constant USD material colors differ')
    g.require(report['treeActor'].startswith(g.MAP + '.') and report['groundActor'].startswith(g.MAP + '.')
              and report['treeActor'] != report['groundActor'], 'Owned scene actors must belong to own map')
    lights = g.read(g.check_pin(report['sourceLightingObserved']))
    measured_source, measured_copied, measured_difference = g.measured_lighting(plan['measuredLightingReference'])
    copied = g.read(g.check_pin(report['copiedLightingObserved']))
    saved = g.read(g.check_pin(report['savedLightingObserved']))
    saved_difference = g.read(g.check_pin(report['savedLightingDifferences']))
    actual_difference = g.read(g.check_pin(report['lightingDifferences']))
    g.require(g.binary64_equal(lights, measured_source)
              and g.binary64_equal(copied, measured_copied)
              and g.binary64_equal(saved, sorted(measured_copied, key=lambda r: r['class']))
              and g.binary64_equal(sorted(report['savedLightingObservedSubset'], key=lambda r: r['class']), saved)
              and report['lightingScope'] == plan['lightingScope'], 'Exact original/copied/saved measured subset differs')
    g.require(saved_difference['nativeProcessId'] == FINAL_NATIVE_PID
              and saved_difference['differenceCount'] == 0 and saved_difference['differences'] == []
              and saved_difference['numericalToleranceApplied'] is False
              and saved_difference['measuredReference'] == plan['measuredLightingReference']
              and saved_difference['saved'] == report['savedLightingObserved'], 'Actual saved difference gate differs')
    g.require(actual_difference['nativeProcessId'] == FINAL_NATIVE_PID
              and actual_difference['source'] == report['sourceLightingObserved']
              and actual_difference['copied'] == report['copiedLightingObserved']
              and actual_difference['numericalToleranceApplied'] is False
              and actual_difference['differences'] == measured_difference['differences']
              and {**report['actualDirectionalQuaternionDifference'], 'source': actual_difference['source'],
                   'copied': actual_difference['copied'], 'nativeProcessId': FINAL_NATIVE_PID, 'schema': g.SCHEMA,
                   'owner': OWNER, 'numericalToleranceApplied': False, 'nativeAppearanceAccepted': False} == actual_difference
              and g.binary64_equal(report['sourceDirectionalQuaternion'], measured_source[0]['transform'][1])
              and g.binary64_equal(report['expectedNativeCopiedDirectionalQuaternion'], measured_copied[0]['transform'][1]),
              'Actual quaternion diagnostic or exact measured-pair annotation differs')
    g.require(sum(r['class'] == '/Script/Engine.DirectionalLight' for r in lights) == 1
              and sum(r['class'] == '/Script/Engine.SkyLight' for r in lights) == 1,
              'Original observed native day sun and sky required')
    for light in lights:
        for component in light['components']:
            g.require(set(component['properties']) == {'mobility', *n.n.LIGHT_FIELDS[component['class']]},
                      'Lighting copy exceeds or omits recorded component-field scope')
        if light['class'] == '/Script/Engine.PostProcessVolume':
            g.require(set(light['postProcess']) == {'unbound', 'properties', 'overrides'}
                      and set(light['postProcess']['properties']) == set(n.PP_FIELDS)
                      and set(light['postProcess']['overrides']) == set(n.PP_FIELDS),
                      'Seven PP fields and overrides required')
    original_log = g.check_pin(g.read(g.check_pin(report['crashedImportByteAudit']))['nativeLog']).read_text(errors='replace')
    warnings = [line for line in original_log.splitlines() if 'Compute a zero length normal vector' in line
                or 'LogSkeletalMesh: Warning:' in line]
    g.require(report['observedOriginalImportWarnings'] == warnings, 'Actual preserved importer warnings differ')
    return {'mode': 'original-licensed-whole-D-preserved-USD-isolated-editor-scene-r6',
        'nativeProcessId': report['nativeProcessId'], 'map': report['map'],
        'preservedOriginalUsdAssets': 39, 'nativeAssemblyPartReferences': 11,
        'sourceUniqueBuildFanTriangles': source['sourceUniqueBuildFanTriangles'],
        'sourceExpandedFanTrianglesEstimate': source['sourceBasePlusExpandedFanTrianglesEstimate'],
        'nativeAssemblyNodesReadbackAvailable': report['nativeAssemblyNodesReadbackAvailable'],
        'nativeFullGeometryCornerReadbackAvailable': False, 'importedNormalsTangentsPreserved': False,
        'observedOriginalImportWarnings': warnings, 'nativeStartupReadback': report['nativeStartupReadback'],
        'editorRuntimeAssemblyCvarReadbackAvailable': False, 'originalConstantMaterialsPreserved': True,
        'explicitLightingSubsetCopiedAndReloaded': True, 'fullLightingPropertyCloneClaimed': False,
        'exactMeasuredDirectionalSetterAndReloadVerified': True, 'numericalToleranceApplied': False,
        'walkingAuditAvailable': False, 'walkingCollisionAccepted': False,
        'nativeAppearanceAccepted': False, 'performanceAccepted': False,
        'fullPhotorealismAccepted': False, 'shippingVerified': False, 'packageVerified': False}


def main():
    g.require(FINAL_REPORT_SHA is not None and FINAL_NATIVE_PID is not None, 'Actual scene success binding is pending')
    file = Path(sys.argv[1]).resolve()
    g.require(file == g.OUTPUT / n.REPORT and g.sha(file) == FINAL_REPORT_SHA, 'Only exact actual saved R6 report accepted')
    g.require(g.sha(g.ROOT / OWNER) == NATIVE_SHA, 'Consumed native scene helper changed')
    plan, source, base, before = g.validate_plan()
    print(json.dumps(validate_report(g.read(file), plan, source, base, before), allow_nan=False))


if __name__ == '__main__': main()
