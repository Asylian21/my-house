#pragma once
#include "CoreMinimal.h"

// Independent diagnostic lifetime. No transport/material/light binding.
class IBreziSolarVisibilityProbe
{
public:
    virtual ~IBreziSolarVisibilityProbe() = default;
    virtual void Stop() = 0;
};

TUniquePtr<IBreziSolarVisibilityProbe> CreateBreziSolarVisibilityProbe(const FString& CasesPath, bool bCaptureRequested);
