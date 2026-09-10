#include "../unreal/BreziTwin/Source/BreziTwin/BreziPresetKeyPolicy.h"
#include <iostream>
#include <stdexcept>

using namespace BreziPresetKeys;
static int Checks = 0;
void Check(bool Value, const char* Message)
{
    ++Checks;
    if (!Value) throw std::runtime_error(Message);
}

int main()
{
    // Independent macOS SDK positions. Translated logical identity is deliberately
    // varied: SK/CZ nonnumeric glyph, US numeric key, and a conflicting numeric key.
    const std::uint32_t Positions[2][4] = {{0x12, 0x13, 0x14, 0x15}, {0x53, 0x54, 0x55, 0x56}};
    for (const auto& Row : Positions)
        for (int Index = 0; Index < 4; ++Index)
            for (int Logical = -1; Logical <= 4; ++Logical)
                Check(Resolve(true, Row[Index], Logical) == Index, "physical position must beat translated logical key");

    // Original codes for Equal, keypad Plus, Minus, keypad Minus, PageUp/Down,
    // 0 and 5 are outside the four preset positions, even if logical data conflicts.
    for (std::uint32_t Code : {0x18u, 0x45u, 0x1Bu, 0x4Eu, 0x74u, 0x79u, 0x1Du, 0x17u})
        for (int Logical = -1; Logical < 4; ++Logical)
            Check(Resolve(true, Code, Logical) == -1, "zoom/navigation/other number position cannot become preset");

    for (int Logical = 0; Logical < 4; ++Logical)
    {
        Check(Resolve(true, 0, Logical) == Logical, "exact synthetic logical numeric event works");
        Check(Resolve(false, 0x45, Logical) == Logical, "non-Mac logical behavior does not use Mac codes");
    }
    Check(Resolve(true, 0, -1) == -1, "synthetic plus glyph is not a numeric alias");
    Check(Resolve(true, 0, 4) == -1, "out-of-range source index rejected");

    // Press/auto-repeat pairs cannot restart camera selection. Every forbidden
    // modifier combination remains unhandled, also when the key repeats.
    for (int Index = 0; Index < 4; ++Index)
    {
        Check(Decide(Index, false, false, false, false) == Action::Select, "unmodified press selects");
        Check(Decide(Index, false, false, false, true) == Action::ConsumeRepeat, "repeat consumed without selecting");
        for (unsigned Modifiers = 1; Modifiers < 8; ++Modifiers)
            for (bool Repeat : {false, true})
                Check(Decide(Index, Modifiers & 1, Modifiers & 2, Modifiers & 4, Repeat) == Action::Unhandled,
                    "Control Option Command must bypass presets");
    }
    Check(Decide(-1, false, false, false, false) == Action::Unhandled, "unrecognized key is unhandled");
    Check(Decide(4, false, false, false, true) == Action::Unhandled, "invalid index repeat is unhandled");
    std::cout << Checks << " preset policy checks passed; no native keyboard/UI proof\n";
}
