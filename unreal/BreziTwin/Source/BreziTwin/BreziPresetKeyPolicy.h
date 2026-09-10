#pragma once

#include <cstdint>

// Value-only policy shared by both Slate routes and the portable CPU checks.
namespace BreziPresetKeys
{
constexpr int Resolve(bool Mac, std::uint32_t HardwareCode, int LogicalIndex)
{
    if (Mac && HardwareCode != 0)
    {
        // macOS SDK Events.h: kVK_ANSI_1..4 and kVK_ANSI_Keypad1..4.
        // The original position wins even when SK/CZ translation names it '+'.
        if (HardwareCode >= 0x12 && HardwareCode <= 0x15) return int(HardwareCode - 0x12);
        if (HardwareCode >= 0x53 && HardwareCode <= 0x56) return int(HardwareCode - 0x53);
        return -1;
    }
    // Zero-code synthetic events must name an exact numeric FKey, not a glyph.
    return LogicalIndex >= 0 && LogicalIndex < 4 ? LogicalIndex : -1;
}

enum class Action { Unhandled, ConsumeRepeat, Select };
constexpr Action Decide(int Index, bool Control, bool Alt, bool Command, bool Repeat)
{
    if (Index < 0 || Index >= 4 || Control || Alt || Command) return Action::Unhandled;
    return Repeat ? Action::ConsumeRepeat : Action::Select;
}
}
