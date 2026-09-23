#include "BreziDoorSelectionPolicy.h"
#include <iostream>
#include <stdexcept>
using BreziDoorSelection::Score;
void Check(bool Value, const char* Message) { if (!Value) throw std::runtime_error(Message); }
int main()
{
    // Actual stacked source points: shared XY913.2/272.3, dryerZ139,
    // washerZ50. Standing eyeZ165, first 82.3cm and then40cm in front.
    for (const double Distance : {82.3, 40.})
    {
        const std::array<double, 3> Dryer {0, Distance, 139 - 165};
        const std::array<double, 3> Washer {0, Distance, 50 - 165};
        Check(Score(Distance, 1, true, Washer, Washer) < Score(Distance, 1, true, Washer, Dryer), "Looking down must select washer");
        Check(Score(Distance, 1, true, Dryer, Dryer) < Score(Distance, 1, true, Dryer, Washer), "Looking higher must select dryer");
        Check(Score(Distance, 1, false, Washer, Dryer) == Distance, "Architectural door score must ignore vertical aim");
    }
    Check(Score(120, .5, false, {0, 1, 0}, {0, 120, -43}) == 144, "Normal door ranking unchanged");
    const std::array<double, 3> Hatch {0, 90, 10 - 165};
    Check(Score(90, 1, true, Hatch, Hatch) == 90, "Standing eye can aim at hatch below");
    Check(std::isfinite(Score(90, 1, true, {0, 1, 0}, Hatch)), "Horizontal hatch gaze only changes rank, not reach");
    std::cout << "Stacked appliance aim, architectural parity and hatch standing aim passed\n";
}
