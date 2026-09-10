#pragma once
#include "CoreMinimal.h"

// Explicit opt-in primary-floor provider; controls, frozen-phase transport and continuous transport.
class IBreziFloorCausticsDiagnostic
{
public:
    virtual ~IBreziFloorCausticsDiagnostic() = default;
    virtual void Stop() = 0;
};
// Closed mode parsing is required; continuous mode is dormant without explicit opt-in.
TUniquePtr<IBreziFloorCausticsDiagnostic> CreateBreziFloorCausticsDiagnostic(const FString& ContractPath, const FString& Mode);
