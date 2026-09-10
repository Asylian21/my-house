#include "BreziViewTransitionPolicy.h"
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
using BreziViewTransition::Fade;
using BreziViewTransition::Phase;
#define CHECK(x) do { if (!(x)) throw std::runtime_error(std::string(#x) + " line " + std::to_string(__LINE__)); } while (false)
static bool Near(float A, float B) { return std::abs(A - B) < 0.00001f; }
int main()
{
    int Groups = 0;
    for (const float Hz : {20.f, 60.f, 240.f})
    {
        Fade State;
        State.Request();
        int Cuts = 0, Finished = 0, Steps = 0;
        Phase Prior = State.GetPhase();
        while (State.IsActive() && Steps++ < 200)
        {
            const auto S = State.Advance(1 / Hz);
            CHECK(std::isfinite(S.Alpha) && S.Alpha >= 0 && S.Alpha <= 1);
            if (S.Cut) { CHECK(Prior == Phase::BlackBeforeCut); CHECK(S.Alpha == 1); ++Cuts; }
            if (S.Finished) { ++Finished; CHECK(S.Alpha == 0); }
            Prior = State.GetPhase();
        }
        CHECK(Cuts == 1 && Finished == 1 && !State.IsActive());
        ++Groups;
    }
    {
        Fade F; F.Request();
        CHECK(!F.Advance(100).Cut); CHECK(F.GetPhase() == Phase::BlackBeforeCut);
        CHECK(F.Advance(100).Cut); CHECK(F.GetPhase() == Phase::BlackAfterCut);
        CHECK(!F.Advance(100).Cut); CHECK(F.GetPhase() == Phase::FadeIn);
        CHECK(F.Advance(100).Finished); CHECK(!F.IsActive());
        ++Groups;
    }
    {
        Fade F; F.Request(); F.Advance(.04f);
        const float Alpha = F.GetAlpha();
        F.Request(); CHECK(F.GetPhase() == Phase::FadeOut && F.GetAlpha() == Alpha);
        F.Advance(.08f); CHECK(F.GetPhase() == Phase::BlackBeforeCut);
        F.Request(); CHECK(F.Advance(0).Cut); // Latest destination consumed by pawn.
        F.Request(); CHECK(F.GetPhase() == Phase::BlackBeforeCut); // Reselect while black.
        CHECK(F.Advance(0).Cut); F.Advance(0); F.Advance(.09f);
        CHECK(F.GetPhase() == Phase::FadeIn && Near(F.GetAlpha(), .5f));
        F.Request(); CHECK(Near(F.GetAlpha(), .5f));
        CHECK(F.Advance(.06f).Alpha > .5f); // Reversal has no alpha discontinuity.
        ++Groups;
    }
    {
        for (int PhaseIndex = 0; PhaseIndex < 4; ++PhaseIndex)
        {
            Fade F; F.Request();
            if (PhaseIndex > 0) F.Advance(.12f);
            if (PhaseIndex > 1) F.Advance(0);
            if (PhaseIndex > 2) F.Advance(0);
            F.Cancel(); CHECK(!F.IsActive() && F.GetAlpha() == 0);
            const auto S = F.Advance(1); CHECK(!S.Cut && !S.Finished && S.Alpha == 0);
            F.Request(); CHECK(F.GetPhase() == Phase::FadeOut && F.GetAlpha() == 0);
        }
        ++Groups;
    }
    {
        for (float Invalid : {-1.f, std::numeric_limits<float>::infinity(), std::numeric_limits<float>::quiet_NaN()})
        {
            Fade F; F.Request(); F.Advance(.1f);
            const auto S = F.Advance(Invalid);
            CHECK(S.Cut && S.Finished && !F.IsActive() && S.Alpha == 0);
        }
        ++Groups;
    }
    {
        Fade F; F.Request();
        for (int I = 0; I < 100; ++I) { const auto S = F.Advance(0); CHECK(S.Alpha == 0 && !S.Cut); }
        CHECK(F.GetPhase() == Phase::FadeOut); F.Cancel();
        ++Groups;
    }
    std::cout << "PASS " << Groups << " actual policy groups (CPU only; no UE, collision, rendered-frame or input delivery proof)\n";
}
