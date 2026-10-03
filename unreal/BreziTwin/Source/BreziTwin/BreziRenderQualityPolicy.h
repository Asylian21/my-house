#pragma once

#include <algorithm>
#include <cmath>
#include <initializer_list>

// Pure policy, shared by the native controller and standalone CPU tests.
namespace BreziRenderQuality
{
inline constexpr int NativeProfileSchemaVersion = 1;
inline constexpr int RecipeRevision = 5;
// UE5.8 FSceneViewScreenPercentageConfig::kMinTSRResolutionFraction.
inline constexpr double MinimumOutputFraction = .25;
// Append new choices: existing persisted/diagnostic numeric values stay stable.
enum class Profile { Unknown = -1, Native, Balanced, Performance, Cinematic, RealtimeFull };
enum class Origin { FreshDefault, Saved, NamedCommandLine, Diagnostic, RawCommandLine, InvalidCommandLine, External, UserSelection, NamedDiagnostic };
struct Settings
{
    int ScreenPercentage, HistoryPercentage;
    // Heights of 16:9 frames with the largest rendered and temporally upscaled pixel
    // counts; zero is unbounded. Smaller windows keep the plain percentages above.
    int RenderLines, OutputLines;
    int GlobalIllumination, Shadows, Reflections, Foliage, PostProcess, Effects;
    int ReflectionDownsample;
    float FinalGather, ReflectionQuality, SceneLighting, SceneDetail, SceneDistanceCm, TraceDistanceCm;
    float FoliageDensity, LocalShadowLodBias;
    bool PreferHardwareRayTracing, DoubleGlass, LocalLightShadows, DetailLighting;
};
constexpr bool IsValid(Profile Value) { return Value >= Profile::Native && Value <= Profile::RealtimeFull; }
constexpr Settings Values(Profile Value)
{
    // Quality budgets, not measured frame-rate promises. GI and reflections stay at
    // High or above: dropping those scalability groups below 2 disables Lumen.
    // Final gather above 1 doubles Lumen's probe tracing resolution in UE5.8.
    return Value == Profile::Native ? Settings{100, 100, 1080, 0, 3, 3, 3, 3, 3, 3, 2, 1, 1, 1, 1, 15000, 15000, 1, 1, true, true, true, false}
        : Value == Profile::Balanced ? Settings{67, 100, 900, 0, 2, 2, 2, 2, 2, 2, 2, .75f, .75f, 1, 1, 10000, 10000, .65f, 1, true, false, true, false}
        : Value == Profile::Performance ? Settings{50, 100, 720, 1440, 2, 1, 2, 1, 1, 1, 2, .5f, .5f, .5f, .5f, 6000, 6000, .35f, 1, false, false, false, false}
        : Value == Profile::Cinematic ? Settings{100, 200, 1080, 0, 3, 3, 3, 3, 3, 3, 1, 1, 2, 2, 2, 20000, 20000, 1, 1, true, true, true, true}
        // Keep the complete scene, every vegetation instance, glass and local
        // lights. Use balanced raster/Lumen budgets, sharper shadow edges and
        // authored detail flags
        // instead of forcing every small grass/meadow instance into shadows,
        // RT and distance fields. Full describes scene completeness, not equal
        // sampling or shading quality to Cinematic.
        : Value == Profile::RealtimeFull ? Settings{67, 100, 900, 0, 2, 3, 2, 3, 2, 2, 2, 1, .75f, 1, 1, 15000, 15000, 1, 1, true, true, true, false}
        : Settings{};
}
inline double LinePixels(int Lines) { return double(Lines) * Lines * 16 / 9; }
// Fraction of the viewport that TSR outputs before the engine's spatial upscale.
inline double OutputFraction(int OutputLines, int Width, int Height)
{
    const double Pixels = double(Width) * Height;
    if (OutputLines <= 0 || !(Pixels > LinePixels(OutputLines))) return 1;
    return std::max(MinimumOutputFraction, std::sqrt(LinePixels(OutputLines) / Pixels));
}
constexpr bool UseHardwareRayTracing(Profile Value, bool RuntimeSupported)
{
    return RuntimeSupported && Values(Value).PreferHardwareRayTracing;
}
constexpr Profile Match(double Screen, double History)
{
    // Legacy percentage-only classification. RealtimeFull shares Balanced's pair;
    // the UI compares every recipe setting before selecting a profile.
    for (Profile Value : {Profile::Native, Profile::Balanced, Profile::Performance, Profile::Cinematic})
    {
        const Settings Pair = Values(Value);
        if (Screen == Pair.ScreenPercentage && History == Pair.HistoryPercentage) return Value;
    }
    return Profile::Unknown;
}
constexpr bool CompatiblePipeline(int AntiAliasing, int DynamicResolution, double SecondaryPercentage)
{
    return AntiAliasing == 4 && DynamicResolution == 0 && SecondaryPercentage == 100;
}
constexpr bool CanApply(bool Locked, bool VariablesWritable, unsigned ScreenPriority, unsigned HistoryPriority,
    unsigned UserPriority, int AntiAliasing, int DynamicResolution, double SecondaryPercentage)
{
    return !Locked && VariablesWritable && ScreenPriority <= UserPriority && HistoryPriority <= UserPriority
        && CompatiblePipeline(AntiAliasing, DynamicResolution, SecondaryPercentage);
}
struct Decision { Profile Requested; Origin Source; bool Apply; bool Locked; };
constexpr Decision Startup(bool Diagnostic, bool RawOverride, bool NamedPresent, Profile Named, Profile Saved, bool Mutable,
    bool HardwareRayTracingSupported = true)
{
    // Explicit raw resolution/pipeline arguments retain ownership, including deferred
    // ExecCmds. A named benchmark profile applies once and cannot persist a QA choice.
    if (RawOverride) return {Profile::Unknown, Origin::RawCommandLine, false, true};
    if (NamedPresent && !IsValid(Named)) return {Profile::Unknown, Origin::InvalidCommandLine, false, true};
    if (Diagnostic && !NamedPresent) return {Profile::Unknown, Origin::Diagnostic, false, true};
    if (!Mutable) return {Profile::Unknown, Origin::External, false, true};
    if (Diagnostic) return {Named, Origin::NamedDiagnostic, true, true};
    if (NamedPresent) return {Named, Origin::NamedCommandLine, true, false};
    if (IsValid(Saved)) return {Saved, Origin::Saved, true, false};
    return {HardwareRayTracingSupported ? Profile::Balanced : Profile::Performance, Origin::FreshDefault, true, false};
}
constexpr bool Persist(bool DeliberateSelection, bool ApplySucceeded, bool Locked)
{
    return DeliberateSelection && ApplySucceeded && !Locked;
}
}
