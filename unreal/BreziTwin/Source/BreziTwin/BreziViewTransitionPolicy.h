#pragma once

#include <cmath>

// Small value-only policy, also compiled by the standalone CPU regression test.
// The pawn owns the latest destination and the engine fade; this owns only time.
namespace BreziViewTransition
{
enum class Phase { Idle, FadeOut, BlackBeforeCut, BlackAfterCut, FadeIn };
struct Step
{
    float Alpha = 0;
    bool Cut = false;
    bool Finished = false;
};

class Fade
{
public:
    bool IsActive() const { return State != Phase::Idle; }
    Phase GetPhase() const { return State; }
    float GetAlpha() const { return Alpha; }

    void Request()
    {
        // While fading out, only the pawn's destination changes. While fading
        // in, reverse from the current alpha without a jump in brightness.
        if (State == Phase::Idle || State == Phase::FadeIn)
        {
            StartAlpha = Alpha;
            Elapsed = 0;
            State = Phase::FadeOut;
        }
        else if (State == Phase::BlackAfterCut) State = Phase::BlackBeforeCut;
    }

    Step Advance(float DeltaSeconds)
    {
        if (!IsActive()) return { Alpha, false, false };
        if (!std::isfinite(DeltaSeconds) || DeltaSeconds < 0)
        {
            // A broken clock must not strand an owned black screen.
            Cancel();
            return { 0, true, true };
        }
        if (State == Phase::BlackBeforeCut)
        {
            State = Phase::BlackAfterCut;
            return { 1, true, false };
        }
        if (State == Phase::BlackAfterCut)
        {
            State = Phase::FadeIn;
            Elapsed = 0;
            return { 1, false, false };
        }
        Elapsed += DeltaSeconds;
        const float Duration = State == Phase::FadeOut ? 0.12f : 0.18f;
        const float T = Elapsed >= Duration ? 1.0f : Elapsed / Duration;
        const float Smooth = T * T * (3.0f - 2.0f * T);
        Alpha = State == Phase::FadeOut ? StartAlpha + (1 - StartAlpha) * Smooth : 1 - Smooth;
        if (T == 1)
        {
            if (State == Phase::FadeOut) State = Phase::BlackBeforeCut;
            else { Cancel(); return { 0, false, true }; }
        }
        // At most one phase per tick: a large delta cannot jump over the black
        // states. This is a simulation-tick guarantee, not rendered-frame proof.
        return { Alpha, false, false };
    }

    void Cancel() { State = Phase::Idle; Alpha = StartAlpha = Elapsed = 0; }

private:
    Phase State = Phase::Idle;
    float Alpha = 0;
    float StartAlpha = 0;
    float Elapsed = 0;
};
}
