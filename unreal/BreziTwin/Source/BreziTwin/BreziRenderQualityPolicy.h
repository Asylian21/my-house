#pragma once

#include <initializer_list>

// Pure policy, shared by the native controller and standalone CPU tests.
namespace BreziRenderQuality
{
inline constexpr int NativeProfileSchemaVersion = 1;
enum class Profile { Unknown = -1, Native, Balanced, Performance };
enum class Origin { FreshDefault, Saved, NamedCommandLine, Diagnostic, RawCommandLine, InvalidCommandLine, External, UserSelection };
struct Settings { int ScreenPercentage; int HistoryPercentage; };
constexpr bool IsValid(Profile Value) { return Value >= Profile::Native && Value <= Profile::Performance; }
constexpr Settings Values(Profile Value)
{
    return Value == Profile::Native ? Settings{100, 200}
        : Value == Profile::Balanced ? Settings{67, 100}
        : Value == Profile::Performance ? Settings{50, 100} : Settings{0, 0};
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
constexpr Decision Startup(bool Diagnostic, bool RawOverride, bool NamedPresent, Profile Named, Profile Saved, bool Mutable)
{
    // Diagnostic and raw renderer arguments own their entire launch, including deferred ExecCmds.
    if (Diagnostic) return {Profile::Unknown, Origin::Diagnostic, false, true};
    if (RawOverride) return {Profile::Unknown, Origin::RawCommandLine, false, true};
    if (NamedPresent && !IsValid(Named)) return {Profile::Unknown, Origin::InvalidCommandLine, false, true};
    if (!Mutable) return {Profile::Unknown, Origin::External, false, true};
    if (NamedPresent) return {Named, Origin::NamedCommandLine, true, false};
    if (IsValid(Saved)) return {Saved, Origin::Saved, true, false};
    return {Profile::Balanced, Origin::FreshDefault, true, false};
}
constexpr bool Persist(bool DeliberateSelection, bool ApplySucceeded, bool Locked)
{
    return DeliberateSelection && ApplySucceeded && !Locked;
}
}
