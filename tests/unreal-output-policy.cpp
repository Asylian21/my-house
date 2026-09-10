#include "../unreal/BreziTwin/Source/BreziTwin/BreziOutputPolicy.h"
#include <iostream>
#include <stdexcept>
using namespace BreziOutput;
static int Checks = 0;
void Check(bool Value, const char* Message)
{
    ++Checks;
    if (!Value) throw std::runtime_error(Message);
}
int main()
{
    Check(Select(false, Mode::Invalid, false, false, false).Output == Mode::Retina, "ordinary launch follows drawable");
    Check(Select(false, Mode::Invalid, false, false, true).Output == Mode::Retina, "scene capture uses adaptive default");
    for (Mode M : {Mode::Retina, Mode::FourK})
    {
        Check(Select(true, M, false, false, false).Output == M, "explicit output respected");
        Check(Select(true, M, false, false, true).Output == M, "generic scene capture respects explicit output");
    }
    for (bool UI : {false, true})
    {
        Check(Select(false, Mode::Invalid, !UI, UI, false).Output == Mode::FourK, "legacy QA retains fixed 4K");
        Check(Select(true, Mode::FourK, !UI, UI, false).Output == Mode::FourK, "explicit 4K and legacy QA agree");
        Check(Select(true, Mode::Retina, !UI, UI, false).Problem == Error::ConflictingOutput, "adaptive cannot masquerade as legacy 4K QA");
        Check(Select(false, Mode::Invalid, !UI, UI, true).Problem == Error::ConflictingCapture, "two capture contracts rejected");
    }
    Check(Select(true, Mode::Invalid, true, false, false).Problem == Error::InvalidArgument, "invalid output cannot be hidden by QA override");
    Check(Select(false, Mode::Invalid, true, true, false).Output == Mode::FourK, "existing combined scene/UI 4K flags remain compatible");
    const Pixels UHD{3840, 2160}, Missing{0, 0};
    // Inputs are Slate's already-scaled and endpoint-rounded draw dimensions.
    // Window points, profile percentages, and a second DPI multiplier have no role.
    for (Pixels Draw : {Pixels{1600, 900}, Pixels{2560, 1440}, Pixels{3024, 1701}, UHD})
    {
        Check(Matches(Mode::Retina, false, true, Draw, Draw, Draw, Draw), "adaptive accepts actual drawable dimensions, not one fixed 1440p size");
        const Pixels Twice{Draw.X * 2, Draw.Y * 2};
        Check(!Matches(Mode::Retina, false, true, Draw, Twice, Twice, Twice), "second DPI scaling rejected");
        Check(!Matches(Mode::Retina, true, true, Draw, Draw, Draw, Draw), "fixed-size viewport is not adaptive");
        Check(!Matches(Mode::Retina, false, false, Draw, Draw, Draw, Draw), "no readiness before valid geometry");
        Check(!Matches(Mode::Retina, false, true, Draw, Draw, Draw, Missing), "metadata alone cannot certify an absent RHI texture");
        Check(Matches(Mode::FourK, true, true, Draw, UHD, UHD, UHD), "legacy scene 4K independent of presentation window size");
        Check(!Matches(Mode::FourK, false, true, Draw, UHD, UHD, UHD), "accidental current 4K dimensions are not a fixed contract");
    }
    const Pixels Before{1600, 900}, After{2400, 1350};
    Check(!Matches(Mode::Retina, false, true, After, Before, Before, Before), "resize before paint is not target-ready");
    Check(!Matches(Mode::Retina, false, true, After, After, After, Before), "resize with stale RHI texture is not target-ready");
    Check(Matches(Mode::Retina, false, true, After, After, After, After), "resized target becomes ready when actual RHI matches");
    Check(!Matches(Mode::Retina, false, true, Missing, Missing, Missing, Missing), "minimized/zero geometry never accepted");
    Check(!Matches(Mode::Retina, false, true, Pixels{-1, 900}, Before, Before, Before), "invalid rectangle rejected");
    Check(!Matches(Mode::Invalid, false, true, Before, Before, Before, Before), "invalid CLI cannot claim readiness");
    std::cout << Checks << " output policy checks passed\n";
}
