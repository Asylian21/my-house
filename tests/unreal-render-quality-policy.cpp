#include "../unreal/BreziTwin/Source/BreziTwin/BreziRenderQualityPolicy.h"
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
using namespace BreziRenderQuality;
static int Checks = 0;
void Check(bool Value, const char* Message)
{
    ++Checks;
    if (!Value) throw std::runtime_error(Message);
}
int main()
{
    static_assert(NativeProfileSchemaVersion == 1);
    static_assert(RecipeRevision == 4);
    static_assert(static_cast<int>(Profile::Native) == 0 && static_cast<int>(Profile::Balanced) == 1
        && static_cast<int>(Profile::Performance) == 2 && static_cast<int>(Profile::Cinematic) == 3);
    constexpr unsigned User = 0x09000000, Project = 0x04000000, Console = 0x10000000;
    Check(Values(Profile::Native).ScreenPercentage == 100 && Values(Profile::Native).HistoryPercentage == 100, "native pair avoids doubled history");
    Check(Values(Profile::Balanced).ScreenPercentage == 67 && Values(Profile::Balanced).HistoryPercentage == 100, "balanced pair");
    Check(Values(Profile::Performance).ScreenPercentage == 50 && Values(Profile::Performance).HistoryPercentage == 100, "performance pair");
    Check(Values(Profile::Cinematic).ScreenPercentage == 100 && Values(Profile::Cinematic).HistoryPercentage == 200, "cinematic retains native sampling and doubled temporal history");
    for (Profile P : {Profile::Native, Profile::Balanced, Profile::Performance, Profile::Cinematic})
    {
        auto Pair = Values(P);
        Check(Match(Pair.ScreenPercentage, Pair.HistoryPercentage) == P, "actual pair classified");
        Check(Match(Pair.ScreenPercentage + .01, Pair.HistoryPercentage) == Profile::Unknown, "partial percentage is not selected");
        Check(Pair.GlobalIllumination >= 2 && Pair.Reflections >= 2, "interactive profiles retain Lumen");
        const bool Cinematic = P == Profile::Cinematic;
        const int Budget = Cinematic ? 2 : 1;
        Check(Pair.FinalGather <= 1, "no profile doubles Lumen probe tracing resolution");
        Check(Pair.ReflectionQuality <= Budget && Pair.SceneLighting <= Budget, "profile bounds expensive imported volume quality");
        Check(Pair.ReflectionDownsample == (Cinematic ? 1 : 2), "full-resolution Lumen reflections are reserved for cinematic");
        Check(Pair.LocalShadowLodBias == 1, "local virtual shadow pages use the halved-resolution budget");
        // The 1080p frames that validated the percentage recipe stay uncapped.
        Check(Pair.RenderLines >= Pair.ScreenPercentage * 1080 / 100, "render cap is inactive in a 1080p viewport");
        Check(OutputFraction(Pair.OutputLines, 1920, 1080) == 1, "temporal output is full in a 1080p viewport");
        Check(Pair.RenderLines > 0 && (Pair.OutputLines == 0 || Pair.OutputLines >= Pair.RenderLines), "render budget never exceeds output budget");
        const int Distance = Cinematic ? 20000 : 15000;
        Check(Pair.SceneDistanceCm <= Distance && Pair.TraceDistanceCm <= Distance, "profile bounds Lumen scene range");
        Check(Pair.DetailLighting == Cinematic, "detail lighting is explicitly restored only in cinematic");
        Check(Pair.FoliageDensity > 0 && Pair.FoliageDensity <= 1, "density is a valid fraction");
        Check(!UseHardwareRayTracing(P, false), "unsupported RHI always falls back to software Lumen");
    }
    Check(Values(Profile::Performance).RenderLines < Values(Profile::Balanced).RenderLines
        && Values(Profile::Balanced).RenderLines < Values(Profile::Native).RenderLines
        && Values(Profile::Native).RenderLines <= Values(Profile::Cinematic).RenderLines, "render budgets follow profile order");
    Check(Values(Profile::Performance).OutputLines == 1440 && Values(Profile::Balanced).OutputLines == 0
        && Values(Profile::Native).OutputLines == 0 && Values(Profile::Cinematic).OutputLines == 0, "only performance caps temporal output");
    Check(std::abs(OutputFraction(1440, 3840, 2160) - 2. / 3) < 1e-9, "4K performance output is 2560x1440");
    Check(std::abs(OutputFraction(1440, 3456, 1944) - 1440. / 1944) < 1e-9, "16:9 Retina output keeps the 1440-line pixel budget");
    Check(std::abs(OutputFraction(1440, 3456, 2160) * OutputFraction(1440, 3456, 2160) * 3456 * 2160 - LinePixels(1440)) < 1,
        "non-16:9 output keeps the pixel budget");
    Check(OutputFraction(0, 3840, 2160) == 1 && OutputFraction(1440, 2560, 1440) == 1 && OutputFraction(1440, 1920, 1200) == 1,
        "unbounded and smaller viewports keep full output");
    Check(OutputFraction(1440, 100000, 100000) == MinimumOutputFraction, "output never drops below TSR's supported fraction");
    Check(OutputFraction(1440, 0, 2160) == 1 && OutputFraction(1440, -1, 2160) == 1
        && OutputFraction(1440, std::numeric_limits<int>::max(), std::numeric_limits<int>::max()) == MinimumOutputFraction,
        "degenerate viewports never produce an invalid fraction");
    Check(Match(100, 200) == Profile::Cinematic, "doubled-history pair identifies cinematic without changing native");
    Check(Match(67, 200) == Profile::Unknown, "mixed pair is not selected");
    Check(Match(std::numeric_limits<double>::quiet_NaN(), 100) == Profile::Unknown, "NaN is not selected");
    Check(CanApply(false, true, Project, Project, User, 4, 0, 100), "project defaults allow explicit user settings");
    Check(CanApply(false, true, User, User, User, 4, 0, 100), "subsequent deliberate user selection allowed");
    Check(!CanApply(false, true, Console, Project, User, 4, 0, 100), "screen console override protected");
    Check(!CanApply(false, true, Project, Console, User, 4, 0, 100), "history console override protected");
    Check(!CanApply(true, true, Project, Project, User, 4, 0, 100), "early CLI/QA lock protected");
    Check(!CanApply(false, false, Project, Project, User, 4, 0, 100), "read-only/missing variables protected");
    for (int AA : {0, 1, 2, 3, 5}) Check(!CompatiblePipeline(AA, 0, 100), "non-TSR must not appear selected or be overwritten");
    Check(!CompatiblePipeline(4, 1, 100) && !CompatiblePipeline(4, 0, 50), "dynamic or secondary resolution not overwritten");
    auto Fresh = Startup(false, false, false, Profile::Unknown, Profile::Unknown, true);
    Check(Fresh.Apply && !Fresh.Locked && Fresh.Requested == Profile::Balanced && Fresh.Source == Origin::FreshDefault, "fresh-install balanced");
    Check(!Persist(false, true, false), "default/restore/CLI startup never writes persistence");
    Check(Startup(false, false, false, Profile::Unknown, Profile::Unknown, true, false).Requested == Profile::Performance,
        "first launch without hardware RT takes conservative software profile");
    Check(UseHardwareRayTracing(Profile::Balanced, true) && UseHardwareRayTracing(Profile::Native, true)
        && !UseHardwareRayTracing(Profile::Performance, true), "profiles choose their capability-aware tracing preference");
    Check(!Values(Profile::Balanced).DoubleGlass && !Values(Profile::Performance).DoubleGlass
        && Values(Profile::Native).DoubleGlass, "supplemental captures reserved for presentation");
    Check(!Values(Profile::Performance).LocalLightShadows && Values(Profile::Balanced).LocalLightShadows,
        "performance disables local-light shadows without removing sun shadows");
    for (Profile Saved : {Profile::Native, Profile::Balanced, Profile::Performance, Profile::Cinematic})
    {
        auto Restore = Startup(false, false, false, Profile::Unknown, Saved, true);
        Check(Restore.Apply && Restore.Requested == Saved && Restore.Source == Origin::Saved, "valid explicit saved choice restored");
        auto Named = Startup(false, false, true, Profile::Native, Saved, true);
        Check(Named.Apply && !Named.Locked && Named.Requested == Profile::Native && Named.Source == Origin::NamedCommandLine, "named CLI wins once and remains editable");
        for (bool Raw : {false, true}) for (bool IsQA : {false, true})
        {
            if (!Raw && !IsQA) continue;
            auto D = Startup(IsQA, Raw, true, Profile::Balanced, Saved, true);
            Check(D.Locked, "diagnostic and raw launches stay locked after initial setup");
            if (Raw) Check(!D.Apply && D.Requested == Profile::Unknown, "raw pipeline arguments own the launch");
            else Check(D.Apply && D.Requested == Profile::Balanced && D.Source == Origin::NamedDiagnostic,
                "explicit diagnostic profile applies exactly once despite benchmark/capture flags");
            Check(!Persist(true, true, D.Locked), "QA/raw cannot persist even simulated UI callback");
        }
    }
    auto UnnamedDiagnostic = Startup(true, false, false, Profile::Unknown, Profile::Performance, true);
    Check(!UnnamedDiagnostic.Apply && UnnamedDiagnostic.Locked && UnnamedDiagnostic.Source == Origin::Diagnostic,
        "unnamed diagnostic never reads remembered/default profile into a raw comparison");
    auto InvalidDiagnostic = Startup(true, false, true, Profile::Unknown, Profile::Performance, true);
    Check(!InvalidDiagnostic.Apply && InvalidDiagnostic.Source == Origin::InvalidCommandLine,
        "invalid named diagnostic profile fails closed instead of silently benchmarking native");
    auto Invalid = Startup(false, false, true, Profile::Unknown, Profile::Performance, true);
    Check(!Invalid.Apply && Invalid.Locked && Invalid.Source == Origin::InvalidCommandLine, "invalid named flag fails closed");
    auto External = Startup(false, false, false, Profile::Unknown, Profile::Performance, false);
    Check(!External.Apply && External.Locked && External.Source == Origin::External, "unsupported current pipeline remains unchanged");
    Check(Persist(true, true, false) && !Persist(true, false, false), "only successful deliberate selection persists");
    // Reopen sequence: named Native never replaces stored Performance; a later successful UI Balanced does.
    Profile Saved = Profile::Performance;
    auto Temporary = Startup(false, false, true, Profile::Native, Saved, true);
    if (Persist(false, Temporary.Apply, Temporary.Locked)) Saved = Temporary.Requested;
    Check(Startup(false, false, false, Profile::Unknown, Saved, true).Requested == Profile::Performance, "temporary CLI does not contaminate next launch");
    if (Persist(true, true, false)) Saved = Profile::Balanced;
    Check(Startup(false, false, false, Profile::Unknown, Saved, true).Requested == Profile::Balanced, "deliberate selection survives next launch");
    Saved = Profile::Performance;
    auto AlreadySelected = Startup(false, false, true, Profile::Balanced, Saved, true);
    if (Persist(true, AlreadySelected.Apply, AlreadySelected.Locked)) Saved = AlreadySelected.Requested;
    Check(Startup(false, false, false, Profile::Unknown, Saved, true).Requested == Profile::Balanced,
        "clicking already-selected temporary/default choice persists the deliberate selection");
    std::cout << Checks << " render quality policy checks passed\n";
}
