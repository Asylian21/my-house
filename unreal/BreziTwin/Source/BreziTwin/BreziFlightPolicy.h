#pragma once

#include <algorithm>
#include <cmath>

namespace BreziFlight
{
struct Position { double X = 0, Y = 0, Z = 80; };
struct Bounds
{
    double MinX = -9600, MaxX = 9600, MinY = -9600, MaxY = 9600;
    double MinZ = 80, MaxZ = 9200;
};

inline double Finite(double Value, double Fallback = 0)
{
    return std::isfinite(Value) ? Value : Fallback;
}

// Match the web's house-centred flight limits, expanding for a valid distant
// orbit entry instead of unexpectedly moving its camera. Z is height in UE.
inline Bounds ForEntry(Position Entry)
{
    Bounds Result;
    Result.MinX = std::min(Result.MinX, Finite(Entry.X) - 100);
    Result.MaxX = std::max(Result.MaxX, Finite(Entry.X) + 100);
    Result.MinY = std::min(Result.MinY, Finite(Entry.Y) - 100);
    Result.MaxY = std::max(Result.MaxY, Finite(Entry.Y) + 100);
    Result.MaxZ = std::max(Result.MaxZ, Finite(Entry.Z) + 100);
    return Result;
}

inline Position Clamp(Position Value, const Bounds& Limit)
{
    return {std::clamp(Finite(Value.X), Limit.MinX, Limit.MaxX),
        std::clamp(Finite(Value.Y), Limit.MinY, Limit.MaxY),
        std::clamp(Finite(Value.Z, Limit.MinZ), Limit.MinZ, Limit.MaxZ)};
}

inline Position Advance(Position Current, double YawRadians, double Forward, double Right, double Up,
    double DeltaSeconds, bool Boost, bool Precision, const Bounds& Limit)
{
    Current = Clamp(Current, Limit);
    const double Yaw = Finite(YawRadians);
    const double F = std::clamp(Finite(Forward), -1.0, 1.0);
    const double R = std::clamp(Finite(Right), -1.0, 1.0);
    const double U = std::clamp(Finite(Up), -1.0, 1.0);
    const double Length = std::hypot(F, R, U);
    if (Length < 1e-9) return Current;
    const double SpeedCm = Precision ? 60 : Boost ? 600 : 240;
    const double Step = SpeedCm * std::clamp(Finite(DeltaSeconds), 0.0, 0.05) / Length;
    return Clamp({Current.X + (std::cos(Yaw) * F - std::sin(Yaw) * R) * Step,
        Current.Y + (std::sin(Yaw) * F + std::cos(Yaw) * R) * Step, Current.Z + U * Step}, Limit);
}

inline Position Dolly(Position Current, Position Direction, double WheelSteps, const Bounds& Limit)
{
    Current = Clamp(Current, Limit);
    const double X = Finite(Direction.X), Y = Finite(Direction.Y), Z = Finite(Direction.Z);
    const double Length = std::hypot(X, Y, Z);
    if (Length < 1e-9) return Current;
    // A conventional 120-pixel wheel notch matches the web's 0.011 m/pixel.
    const double Step = std::clamp(Finite(WheelSteps) * 132, -500.0, 500.0) / Length;
    return Clamp({Current.X + X * Step, Current.Y + Y * Step, Current.Z + Z * Step}, Limit);
}
}
