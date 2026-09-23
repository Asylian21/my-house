#pragma once

#include <algorithm>
#include <cmath>

namespace BreziTouchpad
{
// Signed fractional wheel steps; positive moves the camera closer.
inline double WheelSteps(double Delta)
{
    return std::isfinite(Delta) ? std::clamp(Delta, -12.0, 12.0) : 0.0;
}

inline double ScrollSteps(double DeltaY)
{
    // macOS already applies the user's natural-scroll preference. Preserve the
    // delivered sign and high-resolution delta instead of synthesising clicks.
    return std::isfinite(DeltaY) ? std::clamp(DeltaY * 0.035, -8.0, 8.0) : 0.0;
}

inline double MagnifySteps(double Magnification)
{
    // NSEvent magnification is an incremental scale change, not a wheel notch.
    // Convert scale to the same exponential distance domain as wheel/buttons.
    if (!std::isfinite(Magnification)) return 0.0;
    return std::log1p(std::clamp(Magnification, -0.8, 4.0)) / -std::log(0.88);
}
}
