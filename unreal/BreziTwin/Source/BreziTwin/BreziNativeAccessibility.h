#pragma once

#include "CoreMinimal.h"

struct FBreziDisplayPreferences
{
    bool bReduceMotion = false;
    bool bIncreaseContrast = false;
    bool bReduceTransparency = false;
};

namespace BreziNativeAccessibility
{
    FBreziDisplayPreferences Read();
    // Listener is delivered on Unreal's game thread. The opaque observer is owned by the caller.
    void* Observe(TFunction<void(FBreziDisplayPreferences)> Listener);
    void StopObserving(void* Observer);
    // Exposes the game's Slate tree to native assistive clients; never changes system VoiceOver.
    void EnableNativeWidgetAccess();
}
