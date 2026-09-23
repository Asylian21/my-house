#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "BreziAvatarBlendSpace.generated.h"

class UAnimSequence;
class UBlendSpace1D;

// Authored once by the bounded avatar importer. Runtime uses the ordinary
// engine blend-space evaluator; no procedural substitute for the source rig.
UCLASS()
class UBreziAvatarBlendSpace : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Brezi|Avatar")
    static UBlendSpace1D* CreateLocomotionAsset(const FString& PackagePath,
        UAnimSequence* Idle, UAnimSequence* Walk, UAnimSequence* Run);
};
