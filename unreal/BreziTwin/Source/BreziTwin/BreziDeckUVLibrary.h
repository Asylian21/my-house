#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "BreziDeckUVLibrary.generated.h"

class UStaticMesh;

/** Editor-only UV1 commit for the five canonical deck meshes. Never saves an asset. */
UCLASS()
class BREZITWIN_API UBreziDeckUVLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** JSON baseline equality signature. Caller independently verifies source geometry first. */
    UFUNCTION(BlueprintCallable, Category="Brezi|Deck")
    static FString InspectDeckMesh(UStaticMesh* Mesh);

    /** IDs must be ascending, unique and cover every native vertex instance. UV values become float32.
     * RecipeSha256 is the caller's pinned recipe, not an authorization to overwrite foreign UV1.
     * Requires prior source proof and the immediately inspected baselineSignature.
     */
    UFUNCTION(BlueprintCallable, Category="Brezi|Deck")
    static FString ApplyDeckUV1(UStaticMesh* Mesh, const TArray<int32>& VertexInstanceIds,
        const TArray<FVector2D>& UV1, const FString& ExpectedBaselineSignature,
        const FString& RecipeSha256);
};
