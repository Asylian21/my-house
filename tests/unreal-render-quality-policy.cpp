#include "../unreal/BreziTwin/Source/BreziTwin/BreziRenderQualityPolicy.h"
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
    constexpr unsigned User = 0x09000000, Project = 0x04000000, Console = 0x10000000;
    Check(Values(Profile::Native).ScreenPercentage == 100 && Values(Profile::Native).HistoryPercentage == 200, "native pair");
    Check(Values(Profile::Balanced).ScreenPercentage == 67 && Values(Profile::Balanced).HistoryPercentage == 100, "balanced pair");
    Check(Values(Profile::Performance).ScreenPercentage == 50 && Values(Profile::Performance).HistoryPercentage == 100, "performance pair");
    for (Profile P : {Profile::Native, Profile::Balanced, Profile::Performance})
    {
        auto Pair = Values(P);
        Check(Match(Pair.ScreenPercentage, Pair.HistoryPercentage) == P, "actual pair classified");
        Check(Match(Pair.ScreenPercentage + .01, Pair.HistoryPercentage) == Profile::Unknown, "partial percentage is not selected");
    }
    Check(Match(100, 100) == Profile::Unknown, "native100 study is not native200 UI");
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
    for (Profile Saved : {Profile::Native, Profile::Balanced, Profile::Performance})
    {
        auto Restore = Startup(false, false, false, Profile::Unknown, Saved, true);
        Check(Restore.Apply && Restore.Requested == Saved && Restore.Source == Origin::Saved, "valid explicit saved choice restored");
        auto Named = Startup(false, false, true, Profile::Native, Saved, true);
        Check(Named.Apply && !Named.Locked && Named.Requested == Profile::Native && Named.Source == Origin::NamedCommandLine, "named CLI wins once and remains editable");
        for (bool Raw : {false, true}) for (bool IsQA : {false, true})
        {
            if (!Raw && !IsQA) continue;
            auto D = Startup(IsQA, Raw, true, Profile::Balanced, Saved, true);
            Check(!D.Apply && D.Locked && D.Requested == Profile::Unknown, "QA/raw CLI never briefly applies remembered/default setting");
            Check(!Persist(true, true, D.Locked), "QA/raw cannot persist even simulated UI callback");
        }
    }
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
