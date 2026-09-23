#include "BreziFlightPolicy.h"
#include <cstdlib>
#include <iostream>
#include <limits>

namespace
{
int Checks = 0;
void Check(bool Condition, const char* Description)
{
    ++Checks;
    if (!Condition) { std::cerr << Description << '\n'; std::exit(1); }
}
bool Near(double A, double B) { return std::abs(A - B) < 1e-7; }
}

int main()
{
    using namespace BreziFlight;
    const Bounds Limit;
    const Position Start{0, 0, 1000};
    auto Move = [&](double F, double R, double U, double Dt = 0.05, bool Boost = false, bool Precision = false)
    { return Advance(Start, 0, F, R, U, Dt, Boost, Precision, Limit); };
    Check(Near(Move(1, 0, 0).X, 12), "normal flight is 2.4 metres per second");
    Check(Near(Move(1, 0, 0).Z, 1000), "horizontal movement preserves altitude");
    Check(Near(Move(0, 0, 1).Z, 1012), "E rises independently of the look direction");
    Check(Near(Move(0, 0, -1).Z, 988), "Q descends");
    Check(Near(Move(1, 0, 0, 0.05, true).X, 30), "Shift boosts to 6 metres per second");
    Check(Near(Move(1, 0, 0, 0.05, true, true).X, 3), "Alt precision overrides boost at 0.6 metres per second");
    const Position Diagonal = Move(1, 1, 1);
    Check(Near(std::hypot(Diagonal.X, Diagonal.Y, Diagonal.Z - 1000), 12), "three-axis diagonal movement is normalized");
    Check(Near(Move(1, 0, 0, 4).X, 12), "a stalled frame cannot teleport the camera");
    Check(Near(Move(1, 0, 0, -1).X, 0), "negative time cannot move the camera");
    const Position Turned = Advance(Start, 1.5707963267948966, 1, 0, 0, 0.05, false, false, Limit);
    Check(Near(Turned.X, 0) && Near(Turned.Y, 12), "horizontal heading follows Unreal's XY frame");
    for (int Rate : {30, 60, 120})
    {
        Position Next = Start;
        for (int Frame = 0; Frame < Rate; ++Frame) Next = Advance(Next, 0, 1, 0, 0, 1.0 / Rate, false, false, Limit);
        Check(Near(Next.X, 240), "movement distance is stable at supported frame rates");
    }
    Position Edge = Advance({9599, -9599, 81}, 0, 1, -1, -1, 0.05, true, false, Limit);
    Check(Near(Edge.X, 9600) && Near(Edge.Y, -9600) && Near(Edge.Z, 80), "bounds prevent leaving the scene or flying underground");
    Check(Near(Advance({0, 0, 9199}, 0, 0, 0, 1, 0.05, true, false, Limit).Z, 9200), "maximum altitude is bounded");
    const Position Far{24000, -28000, 15000};
    const Bounds Expanded = ForEntry(Far);
    Edge = Clamp(Far, Expanded);
    Check(Near(Edge.X, Far.X) && Near(Edge.Y, Far.Y) && Near(Edge.Z, Far.Z), "a distant valid orbit entry retains its exact position");
    Check(Near(Dolly(Start, {0, 0, 1}, 1, Limit).Z, 1132), "flight wheel dolly follows the full view direction");
    Check(Near(Dolly(Start, {1, 0, 0}, 100, Limit).X, 500), "large wheel input remains bounded");
    Check(Near(Dolly({0, 0, 90}, {0, 0, -1}, 1, Limit).Z, 80), "wheel dolly also respects the ground limit");
    const double NaN = std::numeric_limits<double>::quiet_NaN();
    Edge = Advance({NaN, NaN, NaN}, NaN, NaN, NaN, NaN, NaN, false, false, Limit);
    Check(std::isfinite(Edge.X) && std::isfinite(Edge.Y) && Near(Edge.Z, 80), "invalid input cannot poison camera coordinates");
    std::cout << Checks << " free-flight policy checks passed; native UI and capture require app QA\n";
}
