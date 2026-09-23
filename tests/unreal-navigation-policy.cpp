#include "BreziNavigationPolicy.h"
#include <iostream>
#include <limits>
#include <stdexcept>

using namespace BreziNavigation;
static int Checks = 0;
void Check(bool Value, const char* Message)
{
    ++Checks;
    if (!Value) throw std::runtime_error(Message);
}

int main()
{
    Capture Input;
    Check(!Input.Begin(CaptureSource::Latched, false), "blocked entry cannot capture navigation");
    Check(!Input.ReleasePointer(), "release without a gesture cannot change capture");
    Check(Input.Begin(CaptureSource::Latched, true), "successful walking entry can immediately capture");
    Check(!Input.Begin(CaptureSource::PointerHold, true), "right press preserves latched ownership");
    Check(!Input.ReleasePointer(), "right release cannot stop keyboard-started walking");
    Check(Input.GetSource() == CaptureSource::Latched, "latched walk remains active after right click");
    Input.Stop();
    Check(Input.GetSource() == CaptureSource::None, "Escape or menu always releases capture");
    Check(Input.Begin(CaptureSource::PointerHold, true), "temporary pointer navigation starts");
    Check(!Input.Begin(CaptureSource::PointerHold, true), "repeat presses cannot reacquire focus");
    Check(Input.ReleasePointer(), "matching pointer release ends temporary navigation");
    Check(Input.GetSource() == CaptureSource::None, "temporary gesture releases completely");
    Check(Input.Begin(CaptureSource::Latched, true), "F2 can start again after temporary navigation");
    Input.Stop();
    Check(!Input.ReleasePointer(), "late release after Escape is harmless");

    Check(!Input.Begin(CaptureSource::Latched, true, false), "background launch cannot capture the pointer");
    Check(Input.Begin(CaptureSource::Latched, true, true), "foreground Resume captures the pointer");
    Check(Input.LoseForeground(), "focus loss releases persistent capture immediately");
    Check(Input.GetSource() == CaptureSource::None, "focus return alone cannot restart capture");
    Check(!Input.LoseForeground(), "duplicate background notifications are harmless");
    Check(!Input.Begin(CaptureSource::Latched, true, false), "Resume while unfocused cannot steal input");
    Check(Input.Begin(CaptureSource::Latched, true, true), "explicit foreground Resume works after focus loss");
    Input.Stop();
    Check(!Input.BeginAutomation(CaptureSource::PointerHold, true), "automation cannot acquire a pointer gesture");
    Check(!Input.BeginAutomation(CaptureSource::Latched, false), "unavailable automation cannot acquire input ownership");
    Check(Input.BeginAutomation(CaptureSource::Latched, true), "explicit automation can own engine input without foreground assertion");
    Check(!Input.Begin(CaptureSource::Latched, true, true), "human capture cannot overlap automated input ownership");
    Input.Stop();
    for (bool Foreground : {false, true})
    {
        Check(!NavigationInputActive(false, false, Foreground, true), "automation must still start normal navigation bindings");
        Check(!NavigationInputActive(true, true, Foreground, true), "pause still stops automated engine input");
        Check(NavigationInputActive(true, false, Foreground, true), "validated automation drives engine input independently of OS focus");
        Check(NavigationInputActive(true, false, Foreground, false) == Foreground, "ordinary input always requires actual foreground");
    }
    Check(!Input.Begin(CaptureSource::Latched, true, false), "ending automation does not weaken ordinary foreground capture");
    Check(StartTourOnLaunch(false, false, false), "ordinary launch starts the living room tour");
    Check(!StartTourOnLaunch(true, false, false), "explicit architectural view preserves preview mode");
    Check(StartTourOnLaunch(true, false, true), "explicit gameplay takes precedence over an optional view");
    Check(!StartTourOnLaunch(false, true, true), "diagnostic launches retain control of camera and movement");

    TourStartup Startup;
    Startup.Begin(true, false);
    Check(Startup.CompleteIfReady(false, true) == TourStartupAction::Wait && Startup.IsPending(),
        "normal startup waits for the actual viewport and walking destination");
    Startup.RequestResume(true);
    Check(Startup.CompleteIfReady(false, true) == TourStartupAction::Wait && Startup.IsPending(),
        "early Resume cannot cancel walking entry or capture an unfinished viewport");
    Check(Startup.CompleteIfReady(true, true) == TourStartupAction::EnterAndResume,
        "queued foreground Resume enters walking before capture");
    Check(Startup.CompleteIfReady(true, true) == TourStartupAction::Wait && !Startup.IsPending(),
        "readiness consumes startup exactly once without another teleport");

    Startup.Begin(true, false);
    Startup.Pause();
    Check(Startup.IsPending() && Startup.CompleteIfReady(false, true) == TourStartupAction::Wait,
        "early Escape preserves the pending safe arrival");
    Check(Startup.CompleteIfReady(true, true) == TourStartupAction::EnterPaused,
        "readiness cannot undo early Escape and recapture the cursor");
    Check(Startup.CompleteIfReady(true, true) == TourStartupAction::Wait,
        "later foreground ticks cannot resume a startup paused by Escape");

    Startup.Begin(true, false);
    Startup.RequestResume(true);
    Startup.Pause(); // Focus loss while the requested entry is still loading.
    Check(Startup.CompleteIfReady(false, false) == TourStartupAction::Wait,
        "focus loss while loading keeps the safe arrival pending");
    Check(Startup.CompleteIfReady(true, true) == TourStartupAction::EnterPaused,
        "returning focus after deactivation cannot revive a queued Resume");

    Startup.Begin(true, false);
    Check(Startup.CompleteIfReady(true, false) == TourStartupAction::EnterPaused,
        "background readiness prepares walking without capturing native input");
    Check(Startup.CompleteIfReady(true, true) == TourStartupAction::Wait,
        "background launch never waits for new focus to automatically capture");

    Startup.Begin(true, true);
    Startup.RequestResume(false);
    Check(Startup.CompleteIfReady(true, true) == TourStartupAction::EnterPaused,
        "a background Resume request cannot arm capture for later foreground");
    Startup.Begin(true, true);
    Startup.RequestResume(true);
    Check(Startup.CompleteIfReady(true, true) == TourStartupAction::EnterAndResume,
        "explicit foreground Resume after an early pause is accepted without an extra delay");
    Startup.Begin(true, false);
    Startup.Cancel(); // An explicit preset or validated harness owns the destination.
    Startup.RequestResume(true);
    Check(Startup.CompleteIfReady(true, true) == TourStartupAction::Wait,
        "an explicit destination cannot be overwritten by a stale default arrival");
    Startup.Begin(false, false);
    Startup.RequestResume(true);
    Check(Startup.CompleteIfReady(true, true) == TourStartupAction::Wait,
        "ordinary Resume does not create startup work for diagnostic or preview launches");

    Check(AllowGameplayUICapture(true, GameplayUICapture::Play, false), "explicit UI play capture can show the real gameplay HUD");
    Check(AllowGameplayUICapture(true, GameplayUICapture::Pause, false), "explicit UI pause capture can show the real pause menu");
    Check(!AllowGameplayUICapture(true, GameplayUICapture::Play, true), "UI capture cannot take ownership from walkthrough or camera studies");
    Check(!AllowGameplayUICapture(false, GameplayUICapture::Pause, false), "UI startup option requires a Slate UI capture");
    Check(!AllowGameplayUICapture(true, GameplayUICapture::None, false)
        && !AllowGameplayUICapture(true, GameplayUICapture::Invalid, false), "missing and invalid UI requests cannot change default startup");
    Check(MovementAxis(0, true, false) == 1 && MovementAxis(0, false, true) == -1, "arrows move in both directions");
    Check(MovementAxis(1, true, false) == 1, "W plus Up cannot double walking speed");
    Check(MovementAxis(1, false, true) == 0, "opposing WASD and arrow inputs cancel");
    Check(MovementAxis(0, true, true) == 0, "opposing arrow inputs cancel");
    Check(MovementAxis(-1, false, true) == -1, "S plus Down cannot double walking speed");
    Check(MouseDegrees(10, 2) == MouseDegrees(10, 1) * 2, "mouse sensitivity scales relative look");
    Check(std::abs(MouseDegrees(100, 1) - MouseDegrees(10, 1) * 10) < 1e-9,
        "identical pointer travel turns equally regardless of render frame count");
    Check(Sensitivity(-5) == 0.25 && Sensitivity(100) == 3, "sensitivity stays within usable limits");

    const double Target = ZoomTarget(1000, 1);
    Check(std::abs(Target - 880) < 1e-9, "one wheel step preserves existing scale");
    Check(std::abs(ZoomTarget(ZoomTarget(1000, 1), 1) - ZoomTarget(1000, 2)) < 1e-9,
        "wheel bursts accumulate against the destination, independent of render frames");
    Check(std::abs(ZoomTarget(ZoomTarget(1000, 1), -1) - 1000) < 1e-9,
        "reversing the wheel restores the intended radius");
    double At20 = 1000, At60 = 1000, At240 = 1000;
    for (int Step = 0; Step < 10; ++Step) At20 = StepZoom(At20, Target, 1.0 / 20, false);
    for (int Step = 0; Step < 30; ++Step) At60 = StepZoom(At60, Target, 1.0 / 60, false);
    for (int Step = 0; Step < 120; ++Step) At240 = StepZoom(At240, Target, 1.0 / 240, false);
    Check(std::abs(At20 - At60) < 1e-8 && std::abs(At60 - At240) < 1e-8,
        "zoom response is independent of frame rate at 20, 60 and 240 Hz");
    double Radius = 1000;
    for (int Step = 0; Step < 240; ++Step)
    {
        const double Next = StepZoom(Radius, Target, 1.0 / 60, false);
        Check(Next <= Radius && Next >= Target, "zoom must approach without overshoot");
        Radius = Next;
    }
    Check(Radius == Target, "zoom reaches a stable exact endpoint");
    Check(StepZoom(1000, Target, 1.0 / 60, true) == Target, "reduced motion applies wheel immediately");
    Check(StepZoom(1000, Target, 0, false) == 1000, "zero-time frame does not move");
    Check(StepZoom(1000, Target, -1, false) == 1000, "negative time does not move");
    Check(StepZoom(1000, Target, 10, false) == StepZoom(1000, Target, 0.1, false),
        "a long pause cannot cause a large catch-up jump");
    Check(ZoomTarget(35, 100) == 35 && ZoomTarget(30000, -100) == 30000, "zoom stays within existing limits");
    const double NaN = std::numeric_limits<double>::quiet_NaN();
    Check(MouseDegrees(NaN, 1) == 0 && Sensitivity(NaN) == 1, "invalid pointer settings cannot contaminate the camera");
    Check(MovementAxis(NaN, true, false) == 1, "invalid analog input cannot suppress arrow movement");
    Check(std::isfinite(StepZoom(NaN, NaN, NaN, false)), "malformed input cannot propagate NaN");
    std::cout << Checks << " navigation policy checks passed; native capture and movement require app QA\n";
}
