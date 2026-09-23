#pragma once

#include <algorithm>
#include <cmath>

namespace BreziNavigation
{
enum class CaptureSource { None, PointerHold, Latched };

// A temporary overview gesture must not release persistent first-person capture.
class Capture
{
public:
    bool Begin(CaptureSource Requested, bool Available, bool Foreground = true)
    {
        return Foreground && BeginOwned(Requested, Available);
    }
    // Explicit harness ownership is not a claim of foreground mouse capture.
    bool BeginAutomation(CaptureSource Requested, bool Available)
    {
        return Requested == CaptureSource::Latched && BeginOwned(Requested, Available);
    }
    bool ReleasePointer()
    {
        if (Source != CaptureSource::PointerHold) return false;
        Stop();
        return true;
    }
    void Stop() { Source = CaptureSource::None; }
    bool LoseForeground()
    {
        const bool WasCaptured = Source != CaptureSource::None;
        Stop();
        return WasCaptured;
    }
    CaptureSource GetSource() const { return Source; }

private:
    bool BeginOwned(CaptureSource Requested, bool Available)
    {
        if (!Available || Requested == CaptureSource::None || Source != CaptureSource::None) return false;
        Source = Requested;
        return true;
    }
    CaptureSource Source = CaptureSource::None;
};

inline bool NavigationInputActive(bool Navigating, bool MenuOpen, bool Foreground, bool ValidatedAutomation)
{
    return Navigating && !MenuOpen && (Foreground || ValidatedAutomation);
}

inline double Sensitivity(double Value)
{
    return std::isfinite(Value) ? std::clamp(Value, 0.25, 3.0) : 1.0;
}

// Mouse values are frame deltas: never scale them by frame duration.
inline double MouseDegrees(double Delta, double Scale)
{
    return std::isfinite(Delta) ? Delta * 0.16 * Sensitivity(Scale) : 0;
}

inline double MovementAxis(double Wasd, bool PositiveArrow, bool NegativeArrow)
{
    return std::clamp((std::isfinite(Wasd) ? Wasd : 0) + int(PositiveArrow) - int(NegativeArrow), -1.0, 1.0);
}

inline bool StartTourOnLaunch(bool HasExplicitView, bool IsDiagnostic, bool ExplicitGameplay)
{
    return !IsDiagnostic && (!HasExplicitView || ExplicitGameplay);
}

enum class TourStartupAction { Wait, EnterPaused, EnterAndResume };

// Readiness and the user's intent are independent. A click while loading cannot
// skip walking entry, and becoming ready or regaining focus cannot undo a pause.
class TourStartup
{
public:
    void Begin(bool Enabled, bool StartPaused)
    {
        Pending = Enabled;
        CaptureRequested = Enabled && !StartPaused;
    }
    bool IsPending() const { return Pending; }
    void Pause() { CaptureRequested = false; }
    void RequestResume(bool Foreground)
    {
        if (Pending && Foreground) CaptureRequested = true;
    }
    void Cancel() { Pending = CaptureRequested = false; }
    TourStartupAction CompleteIfReady(bool Ready, bool Foreground)
    {
        if (!Pending || !Ready) return TourStartupAction::Wait;
        const bool Resume = CaptureRequested && Foreground;
        Cancel();
        return Resume ? TourStartupAction::EnterAndResume : TourStartupAction::EnterPaused;
    }

private:
    bool Pending = false;
    bool CaptureRequested = false;
};

enum class GameplayUICapture { None, Play, Pause, Invalid };

inline bool AllowGameplayUICapture(bool CapturesSlateUI, GameplayUICapture Requested, bool OwnsCameraScenario)
{
    return CapturesSlateUI && !OwnsCameraScenario
        && (Requested == GameplayUICapture::Play || Requested == GameplayUICapture::Pause);
}

inline double ZoomTarget(double Radius, double Direction)
{
    if (!std::isfinite(Radius)) Radius = 1000;
    Radius = std::clamp(Radius, 35.0, 30000.0);
    if (!std::isfinite(Direction)) return Radius;
    return std::clamp(Radius * std::pow(0.88, std::clamp(Direction, -100.0, 100.0)), 35.0, 30000.0);
}

inline double StepZoom(double Current, double Target, double DeltaSeconds, bool ReducedMotion)
{
    Target = ZoomTarget(Target, 0);
    if (!std::isfinite(Current) || ReducedMotion) return Target;
    const double Delta = std::isfinite(DeltaSeconds) ? std::clamp(DeltaSeconds, 0.0, 0.1) : 0;
    const double Next = Current + (Target - Current) * (1 - std::exp(-Delta / 0.09));
    return std::abs(Target - Next) < 0.01 ? Target : Next;
}
}
