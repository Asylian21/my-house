#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BreziVegetationPatch.generated.h"

class UHierarchicalInstancedStaticMeshComponent;
class UStaticMesh;
class FJsonObject;

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

    // HISM's serialized density flag is not exposed to Python in UE 5.8.
    // Restrict authoring changes to this actor's collisionless root instances.
    UFUNCTION(BlueprintCallable, Category = "Březí|Rendering")
    bool SetDetailDensityScaling(bool bEnabled);

    UFUNCTION(BlueprintPure, Category = "Březí|Rendering")
    bool GetDetailDensityScaling() const;

    // Only explicit small-detail patches participate. Preserve their serialized
    // flags so leaving the highest-quality profile restores the original scene.
    bool IsQualityDetailPatch() const;
    void SetQualityDetailLighting(bool bEnabled);
    TSharedRef<FJsonObject> GetQualityDetailLightingDiagnostics() const;

private:
    bool bQualityDetailCaptured = false;
    bool bQualityDetailEnabled = false;
    bool bQualityDetailAuthoredShadow = false;
    bool bQualityDetailAuthoredRayTracing = false;
    bool bQualityDetailAuthoredDistanceField = false;
};
