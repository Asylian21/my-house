#pragma once

#include <initializer_list>

// Pure policy, shared by the native controller and standalone CPU tests.
namespace BreziRenderQuality
{
inline constexpr int NativeProfileSchemaVersion = 1;
inline constexpr int RecipeRevision = 2;
enum class Profile { Unknown = -1, Native, Balanced, Performance };
enum class Origin { FreshDefault, Saved, NamedCommandLine, Diagnostic, RawCommandLine, InvalidCommandLine, External, UserSelection, NamedDiagnostic };
struct Settings
{
    int ScreenPercentage, HistoryPercentage;
    int GlobalIllumination, Shadows, Reflections, Foliage, PostProcess, Effects;
    float FinalGather, ReflectionQuality, SceneLighting, SceneDetail, SceneDistanceCm, TraceDistanceCm;
    float FoliageDensity;
    bool PreferHardwareRayTracing, DoubleGlass, LocalLightShadows;
};
constexpr bool IsValid(Profile Value) { return Value >= Profile::Native && Value <= Profile::Performance; }
constexpr Settings Values(Profile Value)
{
    // Quality budgets, not measured frame-rate promises. GI and reflections stay at
    // High or above: dropping those scalability groups below 2 disables Lumen.
    return Value == Profile::Native ? Settings{100, 100, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 15000, 15000, 1, true, true, true}
        : Value == Profile::Balanced ? Settings{67, 100, 2, 2, 2, 2, 2, 2, .75f, .75f, 1, 1, 10000, 10000, .65f, true, false, true}
        : Value == Profile::Performance ? Settings{50, 100, 2, 1, 2, 1, 1, 1, .5f, .5f, .5f, .5f, 6000, 6000, .35f, false, false, false}
        : Settings{};
}
constexpr bool UseHardwareRayTracing(Profile Value, bool RuntimeSupported)
{
    return RuntimeSupported && Values(Value).PreferHardwareRayTracing;
}
constexpr Profile Match(double Screen, double History)
{
    for (Profile Value : {Profile::Native, Profile::Balanced, Profile::Performance})
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
