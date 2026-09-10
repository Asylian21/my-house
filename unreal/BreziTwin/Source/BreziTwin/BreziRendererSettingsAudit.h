#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "BreziRendererSettingsAudit.generated.h"

class UMaterial;

/** Plain CDO values, not a render-thread uniform or transport measurement. */
USTRUCT(BlueprintType)
struct BREZITWIN_API FBreziWorkingColorSpaceReadback
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Brezi|Audit") bool bValid = false;
    UPROPERTY(BlueprintReadOnly, Category="Brezi|Audit") int32 ChoiceValue = 0;
    UPROPERTY(BlueprintReadOnly, Category="Brezi|Audit") FVector2D Red = FVector2D::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="Brezi|Audit") FVector2D Green = FVector2D::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="Brezi|Audit") FVector2D Blue = FVector2D::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="Brezi|Audit") FVector2D White = FVector2D::ZeroVector;
    UPROPERTY(BlueprintReadOnly, Category="Brezi|Audit") bool bLegacyLuminanceFactors = false;
    UPROPERTY(BlueprintReadOnly, Category="Brezi|Audit") FString SettingsClass;
    UPROPERTY(BlueprintReadOnly, Category="Brezi|Audit") FString SettingsObject;
};

/** Read-only editor bridge for a native enum without a generated Python wrapper. */
UCLASS()
class BREZITWIN_API UBreziRendererSettingsAudit : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Invalid outside the editor or off the game thread; never updates settings. */
    UFUNCTION(BlueprintCallable, Category="Brezi|Audit")
    static FBreziWorkingColorSpaceReadback ReadWorkingColorSpace();

    /** Reads the hidden material output that has no Python enum entry. */
    UFUNCTION(BlueprintCallable, Category="Brezi|Audit")
    static bool HasNoPixelDepthOffsetConnection(UMaterial* Material);
};
