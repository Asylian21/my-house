#pragma once

#include <algorithm>
#include <cmath>

namespace BreziAvatar
{
constexpr double DefaultBoomCm = 260;
constexpr double MaximumBoomCm = 450;
constexpr double FirstPersonCm = 55;
constexpr double ProbeRadiusCm = 17;
constexpr double CollisionPaddingCm = 9;

inline double ZoomDistance(double Current, double Steps)
{
    if (!std::isfinite(Current)) Current = DefaultBoomCm;
    if (!std::isfinite(Steps) || Steps == 0) return std::clamp(Current, 0.0, MaximumBoomCm);
    const double Next = std::max(Current, 65.0) * std::pow(0.88, std::clamp(Steps, -100.0, 100.0));
    return Next < 65 ? 0 : std::min(Next, MaximumBoomCm);
}

inline double SmoothDistance(double Current, double Target, double DeltaSeconds, bool ReducedMotion)
{
    Target = std::clamp(std::isfinite(Target) ? Target : 0, 0.0, MaximumBoomCm);
    if (!std::isfinite(Current) || ReducedMotion) return Target;
    const double Dt = std::clamp(std::isfinite(DeltaSeconds) ? DeltaSeconds : 0, 0.0, 0.1);
    const double Next = Current + (Target - Current) * (1 - std::exp(-Dt / 0.12));
    return std::abs(Next - Target) < 0.05 ? Target : Next;
}

// Obstruction always wins immediately; only recovery is damped. Smoothing must
// never let the lens remain beyond the newly measured wall/door limit.
inline double SafeBoom(double Current, double Desired, double CollisionLimit, double Dt, bool ReducedMotion)
{
    const double Limit = std::clamp(std::isfinite(CollisionLimit) ? CollisionLimit : 0, 0.0, MaximumBoomCm);
    const double Target = std::min(std::clamp(Desired, 0.0, MaximumBoomCm), Limit);
    return std::min(SmoothDistance(Current, Target, Dt, ReducedMotion), Limit);
}

inline bool IsNavigationProxy(bool ActorTagged, bool ComponentTagged, bool Hidden,
    bool MatchingSourceObjectId, bool MatchingSourceId, bool WalkSurface)
{
    return ActorTagged && ComponentTagged && Hidden && MatchingSourceObjectId && MatchingSourceId && !WalkSurface;
}

inline bool AvatarVisibilityTarget(double CameraDistance, bool WasVisible)
{
    if (!std::isfinite(CameraDistance)) return false;
    return WasVisible ? CameraDistance > 120 : CameraDistance >= 145;
}

inline double StepAvatarOpacity(double Current, bool Show, double DeltaSeconds, bool ReducedMotion, bool FaceClose)
{
    const double Target = Show ? 1 : 0;
    if (FaceClose) return 0;
    if (ReducedMotion || !std::isfinite(Current)) return Target;
    const double Dt = std::clamp(std::isfinite(DeltaSeconds) ? DeltaSeconds : 0, 0.0, 0.1);
    Current = std::clamp(Current, 0.0, 1.0);
    // Finite-time fade settles to exact opaque/hidden, never sustained stipple.
    return Show ? std::min(1.0, Current + Dt / .15) : std::max(0.0, Current - Dt / .15);
}
}
