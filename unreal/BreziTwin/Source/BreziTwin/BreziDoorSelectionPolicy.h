#pragma once
#include <algorithm>
#include <array>
#include <cmath>

namespace BreziDoorSelection
{
    // Architectural doors keep their web planar selection. Closures stacked
    // at the same XY must respond to where the eye is pointing vertically.
    inline double Score(double DistanceCm, double HorizontalDot, bool bSpatialAim,
        const std::array<double, 3>& ViewDirection, const std::array<double, 3>& EyeToTarget)
    {
        double Alignment = HorizontalDot;
        if (bSpatialAim)
        {
            double Dot = 0, ViewSquared = 0, TargetSquared = 0;
            for (int I = 0; I < 3; ++I)
            {
                Dot += ViewDirection[I] * EyeToTarget[I];
                ViewSquared += ViewDirection[I] * ViewDirection[I];
                TargetSquared += EyeToTarget[I] * EyeToTarget[I];
            }
            const double LengthProduct = std::sqrt(ViewSquared * TargetSquared);
            Alignment = LengthProduct > 1.e-8 ? std::clamp(Dot / LengthProduct, -1., 1.) : 1.;
        }
        return DistanceCm + (1. - Alignment) * 48.;
    }
}
