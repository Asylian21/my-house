#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "BreziCollisionAudit.generated.h"

class UStaticMesh;

/** Read-only editor evidence for the separately owned source collision meshes. */
UCLASS()
class BREZITWIN_API UBreziCollisionAudit : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Flatten LOD0 triangles in local centimetres. Empty on invalid input or outside the editor. */
    UFUNCTION(BlueprintCallable, Category="Brezi|Audit")
    static TArray<FVector> ReadLod0Triangles(UStaticMesh* Mesh);
};
