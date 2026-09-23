#include "BreziTouchpadPolicy.h"
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>

static int Checks = 0;
void Check(bool Valid, const char* Message) { ++Checks; if (!Valid) throw std::runtime_error(Message); }
int main()
{
    using namespace BreziTouchpad;
    const auto Distance = [](double Steps) { return 260.0 * std::pow(0.88, Steps); };
    Check(MagnifySteps(.2) > 0 && MagnifySteps(-.2) < 0, "spreading fingers moves closer; pinching closed moves away");
    Check(std::abs(Distance(MagnifySteps(.5)) - 260.0 / 1.5) < 1e-9, "native 1.5 scale must produce a 1.5 camera zoom");
    for (int Events : {1, 10, 60, 120, 240})
    {
        const double PerEvent = std::pow(1.5, 1.0 / Events) - 1;
        const double Steps = Events * MagnifySteps(PerEvent);
        Check(std::abs(Distance(Steps) - 260.0 / 1.5) < 1e-8, "same native scale must not depend on gesture event frequency");
        Check(std::abs(Events * ScrollSteps(100.0 / Events) - ScrollSteps(100.0)) < 1e-10,
            "high resolution scroll must preserve fractional motion");
    }
    Check(std::abs(MagnifySteps(.5) + MagnifySteps(1.0/1.5-1.0)) < 1e-10, "inverse pinch restores requested distance");
    Check(WheelSteps(.08) == .08 && WheelSteps(-.08) == -.08, "small wheel deltas may not be rounded to notches");
    Check(ScrollSteps(0) == 0 && MagnifySteps(0) == 0 && WheelSteps(0) == 0, "gesture end cannot jump camera");
    for (double Invalid : {std::numeric_limits<double>::quiet_NaN(), std::numeric_limits<double>::infinity(), -std::numeric_limits<double>::infinity()})
        Check(WheelSteps(Invalid) == 0 && ScrollSteps(Invalid) == 0 && MagnifySteps(Invalid) == 0, "invalid native events cannot poison camera");
    Check(std::isfinite(MagnifySteps(-10)) && std::isfinite(MagnifySteps(1e20)), "bad scale events are bounded");
    std::cout << Checks << " touchpad scale/scroll checks passed\n";
}
