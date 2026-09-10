#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "BreziFlameStudy.generated.h"

class ABreziPawn;
class UStaticMeshComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class FJsonObject;
class FJsonValue;
class FBreziFlameViewExtension;
struct FBreziFlameFrameState;

/** Dormant without an explicit isolated flame-study flag. Never saves assets. */
UCLASS()
class UBreziFlameStudy : public UActorComponent
{
    GENERATED_BODY()
public:
    UBreziFlameStudy();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction) override;
private:
    ABreziPawn* Pawn() const;
    bool ReadContract(const FString& Path);
    bool BindFlame();
    bool ApplyStudyMaterial();
    bool CheckBoundState(TSharedPtr<FJsonObject>* Observation = nullptr) const;
    void CaptureFailureObservation(const FString& Predicate, const TSharedPtr<FJsonObject>& BoundState, bool bWalking);
    void RestoreMaterial();
    TSharedRef<FJsonObject> ComponentState(UStaticMeshComponent* Component) const;
    TSharedRef<FJsonObject> SunState() const;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> FlameComponent;
    UPROPERTY() TObjectPtr<UStaticMeshComponent> GlassComponent;
    UPROPERTY() TObjectPtr<UMaterialInterface> OriginalMaterial;
    UPROPERTY() TObjectPtr<UMaterialInterface> OriginalGlassMaterial;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> StudyMaterial;
    TSharedPtr<FJsonObject> Contract;
    TSharedPtr<FJsonObject> InitialFlame;
    TSharedPtr<FJsonObject> InitialGlass;
    TSharedPtr<FJsonObject> InitialSun;
    TSharedPtr<FJsonObject> FailureObservation;
    FString ContractSha1;
    FString MeshPath, MaterialPath, GlassMeshPath, GlassMaterialPath;
    FString SceneSha, ObjSha;
    FVector ExpectedEye, ExpectedTarget, ExpectedBoundsMin, ExpectedBoundsMax;
    float ExpectedFov = 0;
    float EmissionScale = 0;
    double TargetPreExposure = 0;
    FString LightingState;
    FString ShapeMode, ShapePose;
    FVector SourceInteriorEye = FVector::ZeroVector;
    FVector SourceInteriorTarget = FVector::ZeroVector;
    FVector ExpectedStoveAxis = FVector::ZeroVector;
    FVector NativeStoveAxis = FVector::ZeroVector;
    TArray<FString> ShapeSupportIds;
    bool bNativeStoveAxisVerified = false;
    bool IsShapeStudy() const { return !ShapeMode.IsEmpty(); }
    int32 RequiredCaptureFrames() const { return ShapeMode == TEXT("sequence") ? 62 : 2; }
    uint64 RequiredCaptureGap() const { return ShapeMode == TEXT("sequence") && CaptureIndex > 1 ? 1 : 241; }
    float ExpectedStudySeconds() const { return ShapeMode == TEXT("sequence") && CaptureIndex > 1
        ? static_cast<float>(2.0 + static_cast<double>(CaptureIndex - 1) / 30.0) : 2.0f; }
    FString PriorViewId;
    bool bStudyViewSelected = false;
    bool bCameraRestored = false;
    bool bMaterialRestored = false;
    bool bExtensionStopped = false;
    bool bInvariantStateRestored = false;
    void OnScreenshotCaptured(int32 Width, int32 Height, const TArray<FColor>& Bitmap);
    void OnScreenshotProcessed();
    void Finish(const FString& Status, const FString& Reason = FString());
    bool SaveReport(const FString& Status, const FString& Reason) const;
    void RestoreClock();
    TSharedRef<FJsonObject> QualitySettings() const;

    TSharedPtr<FBreziFlameViewExtension, ESPMode::ThreadSafe> Extension;
    TSharedPtr<FBreziFlameFrameState, ESPMode::ThreadSafe> FrameState;
    TSharedPtr<FJsonObject> InitialQuality;
    TSharedPtr<FJsonObject> SourceViews;
    TArray<TSharedPtr<FJsonValue>> Frames;
    FDelegateHandle CapturedHandle;
    FDelegateHandle ProcessedHandle;
    FString OutputDirectory;
    FString ScreenshotPath;
    bool bEnabled = false;
    bool bFinished = false;
    bool bClockCaptured = false;
    bool bClockApplied = false;
    bool bClockRestored = false;
    bool bCapturePending = false;
    bool bCaptureSaved = false;
    bool bPriorFixedStep = false;
    bool bPriorFixedFrameRate = false;
    double PriorFixedDelta = 0;
    float PriorFixedFrameRate = 0;
    int32 ExpectedAA = -1;
    int32 WarmupFrames = 0;
    int32 CaptureIndex = 0;
    uint64 RequestFrameCounter = 0;
    uint64 PreviousRequestCounter = 0;
    uint32 PreviousFamilyFrame = 0;
    double StartWallSeconds = 0;
    double RequestWallSeconds = 0;
    double RequestWorldSeconds = 0;
    double RequestRealSeconds = 0;
    float RequestDeltaSeconds = 0;
    double RequestAppDeltaSeconds = 0;
};
