#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BreziVegetationPatch.generated.h"

class UHierarchicalInstancedStaticMeshComponent;
class UStaticMesh;

// Serialized source-derived planting instances; meshes and transforms are supplied by import.
UCLASS()
class ABreziVegetationPatch : public AActor
{
    GENERATED_BODY()
public:
    ABreziVegetationPatch();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Březí")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Instances;

    // Commandlet-safe asset preparation. Runtime builds never generate geometry.
    UFUNCTION(BlueprintCallable, Category = "Březí|Editor")
    static TArray<int32> ConfigureDetailLods(UStaticMesh* Mesh);

    // Explicitly update the serialized HISM tree and world bounds in a NullRHI commandlet.
    UFUNCTION(BlueprintCallable, Category = "Březí|Editor")
    void SynchronizeInstanceBounds();
};
