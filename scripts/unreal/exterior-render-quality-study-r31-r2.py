"""One isolated CPU-only rendering-policy proposal; root owns future UE builds."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-render-quality-study-r31-r2.py'
OUT = ROOT / 'output/unreal/exterior-render-quality-20261002-r31-r2-source-proposal'
OLD = ROOT / 'output/unreal/exterior-render-quality-20261002-r31-source-proposal'
BASE = ROOT / 'output/unreal/exterior-20261002-r28b/Project/BreziTwin'
ENGINE = Path('/Users/Shared/Epic Games/UE_5.8/Engine')
HEADER = BASE / 'Source/BreziTwin/BreziRenderQualityPolicy.h'
CONTROLLER = BASE / 'Source/BreziTwin/BreziRenderQuality.cpp'
PRIMARY = {
    'scalabilityConfig': ENGINE / 'Config/BaseScalability.ini',
    'scalabilityImplementation': ENGINE / 'Source/Runtime/Engine/Private/Scalability.cpp',
    'lumenProbeImplementation': ENGINE / 'Source/Runtime/Renderer/Private/Lumen/LumenScreenProbeGather.cpp',
    'lumenReflectionImplementation': ENGINE / 'Source/Runtime/Renderer/Private/Lumen/LumenReflections.cpp',
    'lumenRadiosityImplementation': ENGINE / 'Source/Runtime/Renderer/Private/Lumen/LumenRadiosity.cpp',
    'engineVersion': ENGINE / 'Build/Build.version',
}
ORIGINAL_CINE = 'Settings{100, 200, 1080, 0, 3, 3, 3, 3, 3, 3, 1, 1, 2, 2, 2, 20000, 20000, 1, 1, true, true, true, true}'
NEW_CINE = 'Settings{100, 200, 0, 0, 4, 4, 4, 4, 4, 4, 1, 1, 4, 4, 4, 30000, 30000, 1, 0, true, true, true, true}'
OLD_COMMENT = '    // Final gather above 1 doubles Lumen\'s probe tracing resolution in UE5.8.\n'
NEW_COMMENT = ('    // Installed UE5.8 Cine sets probe tracing resolution 16; the renderer clamps\n'
               '    // normal tracing to 16. FinalGather 1 retains that budget; reference mode\n'
               '    // is a separate path. This policy does not claim a tracing-resolution gain.\n')


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    with Path(path).open('rb') as f:
        h = hashlib.sha256()
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
        return h.hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def write(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def replace_once(text, old, new):
    require(text.count(old) == 1, 'Exact frozen source fragment missing or repeated')
    return text.replace(old, new, 1)


def section(text, name):
    match = re.search(r'^\[' + re.escape(name) + r'\]\s*\n(.*?)(?=^\[|\Z)', text, re.M | re.S)
    require(match is not None, 'Installed scalability section missing: ' + name)
    return dict(re.findall(r'^([^;\s=]+)\s*=\s*([^;\n]+)', match.group(1), re.M))


def main():
    require(not OUT.exists(), 'Fresh immutable R31-r2 source directory required')
    historical = json.loads((OLD / 'source-cpu-audit-r31.json').read_text())
    inputs = {str(ROOT / OWNER): pin(ROOT / OWNER)}
    for name in ('render-quality-source-proposal.json', 'source-cpu-audit-r31.json',
                 'BreziRenderQualityPolicy.h', 'render-quality-policy-r31.cpp'):
        path = OLD / name
        inputs[str(path)] = pin(path)
    for path, row in historical['inputFiles'].items():
        require(sha(path) == row['sha256'] and Path(path).stat().st_size == row['bytes'],
                'Original R31 history changed: ' + path)
        inputs[path] = pin(path)
    for path in [HEADER, CONTROLLER, *PRIMARY.values()]:
        inputs[str(path)] = pin(path)
    require(sha(HEADER) == 'e03da4f8dd09fe07425e3c2fe875534e9322b51f8e2eb401bba26e61f02d4f49',
            'Exact unchanged R28 Recipe4 baseline required')
    original = HEADER.read_text()
    proposed = replace_once(original, 'RecipeRevision = 4;', 'RecipeRevision = 5;')
    proposed = replace_once(proposed, ORIGINAL_CINE, NEW_CINE)
    proposed = replace_once(proposed, OLD_COMMENT, NEW_COMMENT)
    reconstructed = replace_once(proposed, NEW_COMMENT, OLD_COMMENT)
    reconstructed = replace_once(reconstructed, NEW_CINE, ORIGINAL_CINE)
    reconstructed = replace_once(reconstructed, 'RecipeRevision = 5;', 'RecipeRevision = 4;')
    require(reconstructed == original, 'Header widened the declared three-fragment delta')

    scalability = PRIMARY['scalabilityConfig'].read_text()
    cine_names = ['GlobalIlluminationQuality', 'ShadowQuality', 'ReflectionQuality',
                  'FoliageQuality', 'PostProcessQuality', 'EffectsQuality']
    sections = {name: section(scalability, name + '@Cine') for name in cine_names}
    gi = sections['GlobalIlluminationQuality']
    require(gi['r.Lumen.ScreenProbeGather.TracingOctahedronResolution'] == '16'
            and gi['r.Lumen.ScreenProbeGather.DownsampleFactor'] == '8', 'Installed Cine GI budgets differ')
    require(section(scalability, 'GlobalIlluminationQuality@3')['r.Lumen.ScreenProbeGather.DownsampleFactor'] == '16',
            'Installed Epic GI downsample differs')
    require(sections['ReflectionQuality']['r.Lumen.Reflections.DownsampleFactor'] == '1'
            and sections['ShadowQuality']['r.Shadow.Virtual.ResolutionLodBiasLocal'] == '0.0',
            'Installed reflection/shadow Cine budgets differ')
    engine_scalability = PRIMARY['scalabilityImplementation'].read_text()
    for name in cine_names:
        require(re.search(r'CVar' + name + r'_NumLevels\(\s*TEXT\("sg\.' + name + r'\.NumLevels"\),\s*5,', engine_scalability),
                'Installed Cine level4 missing: ' + name)
    require('TEXT("%s@Cine")' in engine_scalability and 'InQualityLevel == MaxLevel' in engine_scalability,
            'Installed maximum-level Cine dispatch differs')
    probe = PRIMARY['lumenProbeImplementation'].read_text()
    require('FMath::Sqrt(FMath::Max(View.FinalPostProcessSettings.LumenFinalGatherQuality, 0.0f))' in probe
            and 'FMath::Clamp(FMath::RoundUpToPowerOfTwo(SqrtQuality * GLumenScreenProbeTracingOctahedronResolution), 4, 16)' in probe
            and 'GLumenScreenProbeGatherReferenceMode ? 32 : TracingOctahedronResolution' in probe,
            'Installed probe clamp/reference-mode rule differs')
    controller = CONTROLLER.read_text()
    for name, maximum in [('LumenFinalGatherQuality', '4.f'), ('LumenReflectionQuality', '4.f'),
                          ('LumenSceneLightingQuality', '4.f'), ('LumenSceneDetail', '4.f')]:
        require(re.search(r'Override\(PP\.' + name + r', [^,]+, \.25f, ' + re.escape(maximum) + r'\);', controller),
                'Existing explicit PP cap differs: ' + name)
    for name in ('LumenSceneViewDistance', 'LumenMaxTraceDistance'):
        require(re.search(r'Override\(PP\.' + name + r', [^,]+, 100\.f, 30000\.f\);', controller),
                'Existing effective distance cap differs: ' + name)
    for name in cine_names:
        require('TEXT("sg.' + name + '")' in controller, 'Controller does not set known group: ' + name)
    reflections = PRIMARY['lumenReflectionImplementation'].read_text()
    radiosity = PRIMARY['lumenRadiosityImplementation'].read_text()
    require('View.FinalPostProcessSettings.LumenReflectionQuality * GLumenReflectionScreenSpaceReconstructionNumSamples' in reflections,
            'Installed reflection quality consumer differs')
    require('FMath::Clamp<float>(View.FinalPostProcessSettings.LumenSceneLightingQuality, .5f, 4.0f)' in radiosity,
            'Installed scene-lighting maximum differs')
    compiler = Path(shutil.which('clang++')).resolve()
    version_command = [str(compiler), '--version']
    compiler_version = subprocess.run(version_command, text=True, capture_output=True, timeout=30)
    require(compiler_version.returncode == 0, 'Standalone compiler version unavailable')
    inputs[str(compiler)] = pin(compiler)

    cpp = (OLD / 'render-quality-policy-r31.cpp').read_text()
    cpp = replace_once(cpp, '#include "BreziRenderQualityPolicy.h"',
        '#include "BreziRenderQualityPolicy.h"\n'
        '#define BreziRenderQuality BreziRenderQualityOriginal\n'
        '#include "original-r28-BreziRenderQualityPolicy.h"\n'
        '#undef BreziRenderQuality\n#include <tuple>')
    cpp = replace_once(cpp, 'Max.FinalGather == 2', 'Max.FinalGather == 1')
    cpp = replace_once(cpp, 'only cinematic increases probe tracing resolution', 'final gather does not claim Cine tracing gain')
    cpp = replace_once(cpp, 'Cinematic ? 2 : Values(P).FinalGather', 'Cinematic ? 1 : Values(P).FinalGather')
    cpp = replace_once(cpp, 'Cinematic ? 40000 : 15000', 'Cinematic ? 30000 : 15000')
    extra = r'''
template<typename T> auto SettingsKey(const T& S)
{
    return std::make_tuple(S.ScreenPercentage,S.HistoryPercentage,S.RenderLines,S.OutputLines,
        S.GlobalIllumination,S.Shadows,S.Reflections,S.Foliage,S.PostProcess,S.Effects,S.ReflectionDownsample,
        S.FinalGather,S.ReflectionQuality,S.SceneLighting,S.SceneDetail,S.SceneDistanceCm,S.TraceDistanceCm,
        S.FoliageDensity,S.LocalShadowLodBias,S.PreferHardwareRayTracing,S.DoubleGlass,S.LocalLightShadows,S.DetailLighting);
}
// Explicit CPU model of the pinned primary-source clamp, not execution of UE.
int SourceTracingModel(float Quality, unsigned Base)
{
    unsigned Value = static_cast<unsigned>(std::sqrt(std::max(Quality,0.f))*Base), Power = 1;
    while (Power < Value) Power <<= 1;
    return std::clamp(static_cast<int>(Power),4,16);
}
'''
    cpp = replace_once(cpp, 'int main()', extra + '\nint main()')
    additions = r'''
    static_assert(BreziRenderQualityOriginal::RecipeRevision == 4);
    for (Profile P : {Profile::Native,Profile::Balanced,Profile::Performance})
        Check(SettingsKey(Values(P)) == SettingsKey(BreziRenderQualityOriginal::Values(
            static_cast<BreziRenderQualityOriginal::Profile>(P))), "all non-Cinematic fields exactly match frozen Recipe4");
    Check(Max.SceneDistanceCm == 30000 && Max.TraceDistanceCm == 30000, "requested distances equal effective unchanged controller caps");
    Check(std::clamp(Max.SceneDistanceCm,100.f,30000.f) == Max.SceneDistanceCm &&
        std::clamp(Max.TraceDistanceCm,100.f,30000.f) == Max.TraceDistanceCm, "future effective distance model does not silently narrow proposal");
    Check(std::clamp(40000.f,100.f,30000.f) != 40000.f, "rejected R1 distance would be narrowed by unchanged controller");
    Check(SourceTracingModel(1,16) == 16 && SourceTracingModel(2,16) == 16, "installed Cine source model has no FinalGather1 to2 trace-resolution gain");
    Check(Values(Profile::Cinematic).FinalGather == BreziRenderQualityOriginal::Values(
        BreziRenderQualityOriginal::Profile::Cinematic).FinalGather, "Cine final gather is retained exactly");
    Check(BreziRenderQualityOriginal::Startup(false,false,false,BreziRenderQualityOriginal::Profile::Unknown,
        BreziRenderQualityOriginal::Profile::Unknown,true).Requested == BreziRenderQualityOriginal::Profile::Balanced,
        "baseline fresh hardware default remains Balanced");
'''
    cpp = replace_once(cpp, '    std::cout << Checks', additions + '\n    std::cout << Checks')
    OUT.mkdir()
    (OUT / 'BreziRenderQualityPolicy.h').write_text(proposed)
    (OUT / 'original-r28-BreziRenderQualityPolicy.h').write_bytes(HEADER.read_bytes())
    (OUT / 'render-quality-policy-r31-r2.cpp').write_text(cpp)
    (OUT / Path(OWNER).name).write_bytes((ROOT / OWNER).read_bytes())
    build = OUT / 'cpu-build'
    build.mkdir()
    (build / 'compiler-version.log').write_text(compiler_version.stdout + compiler_version.stderr)
    executions = []
    for name, flags in [('debug', ['-O0', '-g']), ('optimized', ['-O2', '-DNDEBUG'])]:
        binary = build / ('render-quality-policy-r31-r2-' + name)
        command = [str(compiler), '-std=c++17', '-Wall', '-Wextra', '-Werror', *flags,
                   str(OUT / 'render-quality-policy-r31-r2.cpp'), '-o', str(binary)]
        compiled = subprocess.run(command, text=True, capture_output=True, timeout=90)
        (build / (name + '-compile.log')).write_text(compiled.stdout + compiled.stderr)
        require(compiled.returncode == 0, 'Standalone CPU compile failed: ' + name)
        run = subprocess.run([str(binary)], text=True, capture_output=True, timeout=30)
        (build / (name + '-run.log')).write_text(run.stdout + run.stderr)
        require(run.returncode == 0, 'Standalone CPU policy tests failed: ' + name)
        match = re.fullmatch(r'(\d+) render quality policy checks passed\n', run.stdout)
        require(match is not None and int(match.group(1)) >= 150, 'Meaningful baseline policy checks missing')
        executions.append({'optimization': name, 'compileCommand': command, 'compileExitCode': 0,
            'binary': pin(binary), 'compileLog': pin(build / (name + '-compile.log')),
            'runCommand': [str(binary)], 'exitCode': 0, 'checksPassed': int(match.group(1)),
            'runLog': pin(build / (name + '-run.log')), 'unrealBinary': False})
    for path, row in inputs.items():
        require(sha(path) == row['sha256'] and Path(path).stat().st_size == row['bytes'], 'Consumed source drifted: ' + path)
    flags = {k: False for k in ('originalOrCanonicalFilesModified', 'unrealProjectWritten', 'unrealBuildExecuted',
        'nativeBuildExecuted', 'nativeRuntimeVerified', 'nativeQualityAccepted', 'performanceAccepted',
        'appearanceAccepted', 'fullPhotorealismAccepted', 'shippingVerified', 'packageVerified')}
    proposal = {'schema': 'brezi-exterior-render-quality-source-proposal-r31-r2', 'owner': OWNER,
        'status': 'source-only-refined-cinematic-policy-native-build-pending', 'createdAt': datetime.now(timezone.utc).isoformat(),
        'existingSource': pin(HEADER), 'unchangedController': pin(CONTROLLER),
        'historicalR1Proposal': pin(OLD / 'render-quality-source-proposal.json'),
        'proposedHeader': pin(OUT / 'BreziRenderQualityPolicy.h'), 'primaryEngine': {k: pin(p) for k,p in PRIMARY.items()},
        'inputFiles': inputs, 'engineVersion': '5.8 Build55116800', 'sourceOnly': True,
        'baselineRecipeRevision': 4, 'proposedRecipeRevision': 5, 'changedHeaderFragmentsOnly': ['RecipeRevision4to5','CinematicSettingsOnly','CorrectedInstalledTracingComment'],
        'allOtherHeaderBytesReconstructedExactly': True, 'otherProfilesDefaultsStartupPersistenceEnumAndResolutionPairsUnchanged': True,
        'deltas': {'cinematicSixScalabilityGroups': [3,4], 'renderLineCap': [1080,0],
            'finalGatherRetained': [1,1], 'reflectionSceneLightingSceneDetail': [2,4], 'sceneAndTraceDistanceCm': [20000,30000],
            'localShadowLodBias': [1,0], 'screenAndHistoryPercentagesRetained': [100,200]},
        'installedSourceReview': {'changedScalabilityGroupsOnly': cine_names, 'otherScalabilityGroupsChanged': False,
            'CineTracingOctahedronBaseAndMaximum': 16, 'FinalGather1And2CineTracingResolutionSourceModel': [16,16],
            'referenceMode32Selected': False, 'CineGiDownsample': 8, 'EpicGiDownsample': 16,
            'controllerEffectiveDistanceMaximumCm': 30000, 'controllerEffectiveOtherPpMaximum': 4,
            'allRequestedKnownPpBudgetsWithinUnchangedControllerCaps': True,
            'engineSourceReviewIsNativeExecution': False, 'maximumOfAllPossibleEngineFeaturesClaimed': False},
        'selectedActualNativeBase': None, 'selectedActualNativeBasePending': True,
        'futureSourceBuildContract': {
            'ownerOfUnrealBuildAndGpuLaunch': 'root', 'selectedBaseMustBeActualSavedAndClosedBeforeClone': True,
            'freshIndependentProjectCloneRequired': True, 'intentionalSourceFileDeltaOnly': ['Source/BreziTwin/BreziRenderQualityPolicy.h'],
            'expectedOriginalHeaderSha256': sha(HEADER), 'expectedNewHeaderSha256': sha(OUT / 'BreziRenderQualityPolicy.h'),
            'controllerConfigDescriptorMapsMaterialsGeometryCamerasAndDefaultSelectionUnchanged': True,
            'editorBuildTarget': 'BreziTwinEditor', 'platform': 'Mac', 'configuration': 'Development',
            'actualRebuiltEditorModuleRequired': True, 'buildOutputDeltaMustBeMeasuredAndTypedNotWildcardAllowed': True,
            'originalModuleAndOldProtectedProjectRowsRemainImmutable': True,
            'adapterMustAdmitOnlyExactNewHeaderAndMeasuredNewModuleProof': True,
            'legacyModule2dbRequiredForUnchangedBaselineOnly': True,
            'runtimeRecipeRevisionExpected': 5, 'sixRuntimeScalabilityGroupsExpected': 4,
            'runtimeScreenHistoryExpected': [100,200], 'runtimePpBudgetsExpected': {'finalGather':1,'reflection':4,'sceneLighting':4,'sceneDetail':4,'sceneDistanceCm':30000,'traceDistanceCm':30000},
            'sameCameraLightingOutputWarmupAndSamplesRequired': True, 'measuredAutoExposureMustBeReportedSeparately': True,
            'cpuExecutionsProveUnrealCompileRenderOrPerformance': False}, **flags}
    write(OUT / 'render-quality-source-proposal.json', proposal)
    write(OUT / 'source-cpu-audit-r31-r2.json', {'schema': 'brezi-exterior-render-quality-source-cpu-audit-r31-r2',
        'owner': OWNER, 'status': 'verified-standalone-debug-and-optimized-policy-source-only',
        'proposal': pin(OUT / 'render-quality-source-proposal.json'), 'inputFiles': inputs,
        'producerSnapshot': pin(OUT / Path(OWNER).name), 'testSource': pin(OUT / 'render-quality-policy-r31-r2.cpp'),
        'proposedHeader': pin(OUT / 'BreziRenderQualityPolicy.h'), 'originalHeaderSnapshot': pin(OUT / 'original-r28-BreziRenderQualityPolicy.h'),
        'executions': executions, 'allConsumedSourcePinsUnchangedBeforeAfter': True,
        'compilerVersionCommand': version_command, 'compilerVersionExitCode': 0,
        'compilerVersionLog': pin(build / 'compiler-version.log'),
        'originalR1ArtifactsPreservedExact': True, **flags})
    print(json.dumps({'proposal': pin(OUT / 'render-quality-source-proposal.json'),
        'audit': pin(OUT / 'source-cpu-audit-r31-r2.json'), 'unrealBuildExecuted': False}))


if __name__ == '__main__':
    main()
