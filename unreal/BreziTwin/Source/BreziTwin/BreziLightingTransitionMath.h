#pragma once

#include <algorithm>
#include <cmath>
#include <limits>

// Authored presentation timing; intermediate states are not dated solar solutions.
namespace BreziLightingTransition
{
    constexpr double DurationSeconds = 3.0;
    constexpr float ExposureSpeed = 12.0f;

    inline bool PositiveIntensity(double Value)
    {
        return std::isfinite(Value) && Value > 0.0;
    }

    inline double Progress(double ElapsedSeconds)
    {
        if (!std::isfinite(ElapsedSeconds)) return std::numeric_limits<double>::quiet_NaN();
        const double T = std::clamp(ElapsedSeconds / DurationSeconds, 0.0, 1.0);
        return T * T * T * (T * (T * 6.0 - 15.0) + 10.0);
    }

    inline double Intensity(double From, double To, double Alpha)
    {
        if (!PositiveIntensity(From) || !PositiveIntensity(To) || !std::isfinite(Alpha) || Alpha < 0.0 || Alpha > 1.0)
            return std::numeric_limits<double>::quiet_NaN();
        if (Alpha == 0.0) return From;
        if (Alpha == 1.0) return To;
        return std::exp2(std::log2(From) + (std::log2(To) - std::log2(From)) * Alpha);
    }
}
