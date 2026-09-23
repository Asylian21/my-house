#include "BreziAvatarPolicy.h"
#include <iostream>
#include <limits>
#include <stdexcept>

using namespace BreziAvatar;
static int Checks = 0;
void Check(bool Value, const char* Message)
{
    ++Checks;
    if (!Value) throw std::runtime_error(Message);
}

int main()
{
    Check(ZoomDistance(DefaultBoomCm, 1) < DefaultBoomCm, "positive wheel/pinch zoom approaches the avatar");
    Check(ZoomDistance(DefaultBoomCm, -1) > DefaultBoomCm, "negative wheel/pinch zoom moves outward");
    double Fractional = DefaultBoomCm;
    for (int I = 0; I < 10; ++I) Fractional = ZoomDistance(Fractional, .1);
    Check(std::abs(Fractional - ZoomDistance(DefaultBoomCm, 1)) < 1e-9,
        "fractional trackpad events accumulate independently of event grouping");
    Check(ZoomDistance(65, 1) == 0, "close zoom enters first person without crossing the character");
    Check(ZoomDistance(0, -.1) > 65, "small outward pinch can leave first person");
    Check(ZoomDistance(450, -100) == 450, "large gesture cannot escape the bounded boom");
    Check(SafeBoom(260, 260, 42, 0, false) == 42,
        "a newly closed door retracts the camera immediately even on a zero-time update");
    Check(SafeBoom(260, 260, 0, 0, false) == 0,
        "starting penetration falls back to the validated physical eye");
    Check(SafeBoom(42, 260, 260, .016, false) > 42 && SafeBoom(42, 260, 260, .016, false) < 260,
        "opening a door restores the boom smoothly without an outward snap");
    for (int I = 0; I <= 100; ++I)
    {
        const double Limit = I * 4.5;
        for (double Dt : {0., .001, .016, .05, 1.})
            Check(SafeBoom(450, 450, Limit, Dt, false) <= Limit,
                "camera interpolation can never exceed a measured collision limit");
    }
    double At20 = 42, At60 = 42, At240 = 42;
    for (int I = 0; I < 10; ++I) At20 = SafeBoom(At20, 260, 260, 1. / 20, false);
    for (int I = 0; I < 30; ++I) At60 = SafeBoom(At60, 260, 260, 1. / 60, false);
    for (int I = 0; I < 120; ++I) At240 = SafeBoom(At240, 260, 260, 1. / 240, false);
    Check(std::abs(At20 - At60) < 1e-8 && std::abs(At60 - At240) < 1e-8,
        "boom recovery is equivalent at 20, 60 and 240 Hz");
    Check(SafeBoom(42, 260, 120, .016, true) == 120,
        "reduced motion removes interpolation but still obeys the wall");
    for (int Mask = 0; Mask < 64; ++Mask)
        Check(IsNavigationProxy(Mask & 1, Mask & 2, Mask & 4, Mask & 8, Mask & 16, Mask & 32) == (Mask == 31),
            "only a hidden actor/component with matching source identity and no floor role can be excluded");
    Check(!IsNavigationProxy(false, false, false, true, true, false),
        "real visible furniture and doors remain camera obstacles even with source IDs");
    Check(!IsNavigationProxy(true, true, true, false, true, false),
        "a hidden object without the explicit navigation COLL_ identity remains blocking");
    Check(!AvatarVisibilityTarget(112.36, true), "the observed close kitchen camera hides the oversized foreground head");
    Check(!AvatarVisibilityTarget(130, false) && AvatarVisibilityTarget(130, true),
        "small camera distance fluctuations cannot repeatedly toggle visibility");
    Check(AvatarVisibilityTarget(145, false) && !AvatarVisibilityTarget(120, true),
        "avatar returns only with comfortable space and hides at the close threshold");
    Check(AvatarVisibilityTarget(260, false), "normal unobstructed third person restores the visible avatar");
    double Alpha20 = 1, Alpha60 = 1, Alpha240 = 1;
    for (int I = 0; I < 2; ++I) Alpha20 = StepAvatarOpacity(Alpha20, false, 1. / 20, false, false);
    for (int I = 0; I < 6; ++I) Alpha60 = StepAvatarOpacity(Alpha60, false, 1. / 60, false, false);
    for (int I = 0; I < 24; ++I) Alpha240 = StepAvatarOpacity(Alpha240, false, 1. / 240, false, false);
    Check(std::abs(Alpha20 - Alpha60) < 1e-8 && std::abs(Alpha60 - Alpha240) < 1e-8,
        "opacity transition duration does not depend on render frame rate");
    for (int I = 0; I < 240; ++I) Alpha240 = StepAvatarOpacity(Alpha240, false, 1. / 240, false, false);
    Check(Alpha240 == 0, "stationary close camera settles completely hidden without permanent stipple");
    for (int I = 0; I < 240; ++I) Alpha240 = StepAvatarOpacity(Alpha240, true, 1. / 240, false, false);
    Check(Alpha240 == 1, "stationary clear camera settles completely opaque without permanent stipple");
    Check(StepAvatarOpacity(.5, false, 0, false, false) == .5, "zero-time update does not advance a transient fade");
    Check(StepAvatarOpacity(1, false, 0, false, true) == 0, "face-close obstruction hides immediately even without elapsed time");
    Check(StepAvatarOpacity(.4, true, 0, true, false) == 1 && StepAvatarOpacity(.8, false, 0, true, false) == 0,
        "reduced motion applies exact opaque or hidden target immediately");
    const double NaN = std::numeric_limits<double>::quiet_NaN();
    Check(std::isfinite(ZoomDistance(NaN, NaN)), "malformed zoom remains finite");
    Check(SafeBoom(100, 260, NaN, .016, false) == 0, "invalid obstruction data fails toward the physical eye");
    Check(!AvatarVisibilityTarget(NaN, true), "invalid lens distance cannot reveal an obstructing avatar");
    std::cout << Checks << " avatar camera policy checks passed; native rig, boom sweeps and rendering require app QA\n";
}
