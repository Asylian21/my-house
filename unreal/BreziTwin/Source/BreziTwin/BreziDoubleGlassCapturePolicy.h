#pragma once

#include <cstddef>
#include <cstdint>

namespace BreziDoubleGlass
{
constexpr int MaximumCaptureWidth = 512;
constexpr int MaximumWarmupCaptures = 2;
constexpr double QuietSeconds = 0.25;
constexpr double CameraDistanceToleranceCm = 0.25;
constexpr double CameraAngleToleranceDegrees = 0.05;

inline bool IsSettled(double Now, double LastChange)
{
    return Now >= LastChange && Now - LastChange >= QuietSeconds;
}

// All actors share one budget. Selection starts after the last serviced pane,
// so actor tick order cannot starve other eligible panes during warmup.
struct FrameBudget
{
    std::uint64_t LastFrame = UINT64_MAX;
    std::size_t Next = 0;

    template <typename Eligible>
    bool TryAcquire(std::uint64_t Frame, std::size_t Request, std::size_t Count, Eligible IsEligible)
    {
        if (LastFrame == Frame || !Count || Request >= Count) return false;
        for (std::size_t Offset = 0; Offset < Count; ++Offset)
        {
            const std::size_t Candidate = (Next + Offset) % Count;
            if (!IsEligible(Candidate)) continue;
            if (Candidate != Request) return false;
            LastFrame = Frame;
            Next = (Candidate + 1) % Count;
            return true;
        }
        return false;
    }
};
}
