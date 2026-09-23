#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BreziDoubleGlassActor.generated.h"

class UStaticMeshComponent;
class USceneCaptureComponent2D;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UTextureRenderTarget2D;
class FJsonObject;

/** Optional presentation-only rear-interface image. Inert unless explicitly placed. */
UCLASS()
class ABreziDoubleGlassActor : public AActor
{
    GENERATED_BODY()
public:
    ABreziDoubleGlassActor();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    TSharedRef<FJsonObject> Diagnostics() const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Double Glass")
    TObjectPtr<UStaticMeshComponent> SourceComponent;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Double Glass")
    TObjectPtr<UMaterialInterface> OverlayMaterial;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Double Glass", meta=(ClampMin="256", ClampMax="2048"))
    int32 CaptureWidth = 1024;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Double Glass", meta=(ClampMin="1", ClampMax="64"))
    int32 WarmupCaptures = 16;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Double Glass")
    float MaximumDistanceCm = 20000.0f;
    /** Increment for material-parameter or procedural-scene changes without transforms. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Double Glass")
    int32 SceneRevision = 0;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Double Glass")
    TObjectPtr<UStaticMeshComponent> Overlay;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Double Glass")
    TObjectPtr<USceneCaptureComponent2D> ReflectionCapture;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Double Glass")
    int32 CapturesIssued = 0;

private:
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> Material;
    UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> Target;
    bool bConfigured = false;
    bool bCaptured = false;
    bool bWasVisible = false;
    int32 PendingCaptures = 0;
    uint32 LastSceneSignature = 0;
    int32 LastRevision = INDEX_NONE;
    float LastVisibleTime = 0;
    FVector LastEye = FVector::ZeroVector;
    FRotator LastRotation = FRotator::ZeroRotator;
    float LastFov = -1;
    float LastAspect = -1;
    FTransform LastSourceTransform = FTransform::Identity;
    FString LastSkip = TEXT("not-initialized");
    FVector LastPlane = FVector::ZeroVector;
    FVector LastNormal = FVector::ZeroVector;
    float LastNoV = 0;
    float LastDistanceCm = 0;
    FVector LocalCenter = FVector::ZeroVector;
    FVector LocalNormal = FVector::ZeroVector;
    float LocalHalfThickness = 0;
    void ReleaseCapture();
};
