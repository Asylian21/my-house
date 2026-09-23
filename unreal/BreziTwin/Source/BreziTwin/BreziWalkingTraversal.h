#pragma once

#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#include "Components/ActorComponent.h"
#include "BreziWalkingContract.h"
#include "BreziWalkingTraversal.generated.h"

class ABreziPawn;
class UBreziPresentationQA;
class APlayerController;
class FJsonObject;
class FJsonValue;
class SWidget;

struct FBreziTraversalCase
{
    FString Id;
    FString BlockerId;
    FString ExpectedSupportId;
    TArray<FString> AllowedSupportIds;
    double ExpectedFloorHeightCm = 0;
    FVector EyeCm = FVector::ZeroVector;
    FVector Forward = FVector::ForwardVector;
    double HoldSeconds = 2.0;
};

enum class EBreziTraversalPhase : uint8 { Warmup, Enter, Navigate, Hold, Brake, Exit, Complete };

/** Opt-in deterministic integration harness. It injects engine input, not macOS keyboard events. */
UCLASS()
class UBreziWalkingTraversal : public UActorComponent
{
    GENERATED_BODY()
public:
    UBreziWalkingTraversal();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    bool LoadCases(const FString& Path);
    bool BeginCase();
    void FinishCase(const FString& Status, const FString& Reason);
    void FinishRun(const FString& Status);
    bool SaveReport(const FString& Status) const;
    void Sample(float DeltaTime);
    void Key(const FKey& Code, bool bDown);
    void ReleaseKeys();
    bool CheckBlockingSweep();
    ABreziPawn* Pawn() const;
    APlayerController* Controller() const;

    bool LoadWalkthrough(const FString& Path);
    void TickWalkthrough(float DeltaTime);
    bool SampleWalkthrough(float DeltaTime);
    bool SaveWalkthrough(const FString& Status) const;
    void FinishWalkthrough(const FString& Status, const FString& Error = FString());
    void NextWalkthroughStep();
    bool DriveWalkthroughTo(const FVector& Target);
    bool WalkthroughDoorSweep(FHitResult& Hit) const;
    bool WalkthroughOpenPassage(FHitResult& Hit, TArray<FString>& StepSupports, double& RaisedByCm) const;
    void OnWalkthroughScreenshot(int32 Width, int32 Height, const TArray<FColor>& Bitmap);

    bool bWalkthrough = false;
    UPROPERTY() TObjectPtr<UBreziPresentationQA> PresentationQA;
    bool bWalkthroughStarted = false;
    bool bWalkthroughAutomationStarted = false;
    bool bWalkthroughScreenshots = false;
    bool bWalkthroughCapturePending = false;
    bool bWalkthroughCaptureSaved = false;
    FString WalkthroughCapturePath;
    FString WalkthroughCaptureRegion;
    FIntPoint WalkthroughCapturePixels = FIntPoint::ZeroValue;
    FIntPoint WalkthroughRequestedPixels = FIntPoint::ZeroValue;
    double WalkthroughCaptureStartWall = 0;
    FDelegateHandle WalkthroughScreenshotHandle;
    TSet<FString> WalkthroughCapturedRegions;
    TArray<TSharedPtr<FJsonValue>> WalkthroughScreenshots;
    FString WalkthroughPhase = TEXT("startup");
    TSharedPtr<FJsonObject> WalkthroughFixture;
    TArray<TSharedPtr<FJsonObject>> WalkthroughSteps;
    TArray<TSharedPtr<FJsonObject>> WalkthroughRegions;
    TArray<TSharedPtr<FJsonValue>> WalkthroughEvents;
    TSet<FString> VisitedRegions;
    TSet<FString> OpenedDoors;
    TSet<FString> WalkthroughSupports;
    int32 WalkthroughStep = 0;
    int32 WalkthroughInitialPlacements = 0;
    int32 WalkthroughInputOpenCount = 0;
    double WalkthroughPhaseSeconds = 0;
    double WalkthroughStepSeconds = 0;
    double WalkthroughSimulationSeconds = 0;
    double WalkthroughDistanceCm = 0;
    double WalkthroughMaxSampleTravelCm = 0;
    FVector WalkthroughPriorCenter = FVector::ZeroVector;
    FVector WalkthroughStartEye = FVector::ZeroVector;
    FVector WalkthroughStartForward = FVector::ForwardVector;
    FVector WalkthroughTarget = FVector::ZeroVector;
    FVector WalkthroughDoorStart = FVector::ZeroVector;
    FVector WalkthroughDoorNormal = FVector::ZeroVector;
    double WalkthroughClosedHitDistance = 0;
    int32 WalkthroughClosedHoldSamples = 0;
    int32 WalkthroughDoorWaypoint = 0;
    int32 WalkthroughDoorCycle = 0;
    int32 WalkthroughInputCloseCount = 0;

    bool bEnabled = false;
    bool bFinished = false;
    bool bPriorFixedStep = false;
    double PriorFixedDelta = 0;
    bool bPriorFixedFrameRate = false;
    float PriorFixedFrameRate = 0;
    double RunStartWallSeconds = 0;
    double PreviousSampleWallSeconds = 0;
    FString ReportPath;
    FString SceneSha256;
    FString LoadError;
    FBreziWalkingContract Contract;
    TArray<FBreziTraversalCase> Cases;
    TArray<TSharedPtr<FJsonValue>> Results;
    TArray<TSharedPtr<FJsonValue>> PathSamples;
    TSharedPtr<FJsonObject> CurrentResult;
    TSet<FKey> PressedKeys;
    TWeakPtr<SWidget> FocusBeforeNavigation;
    int32 CaseIndex = 0;
    int32 FrequencyIndex = 0;
    int32 FramesInPhase = 0;
    int32 SimulatedHz = 20;
    int32 FailedCases = 0;
    EBreziTraversalPhase Phase = EBreziTraversalPhase::Warmup;
    double PhaseSeconds = 0;
    double CurrentCaseWallStart = 0;
    FVector StartCenter = FVector::ZeroVector;
    FVector BlockerPoint = FVector::ZeroVector;
    FVector BlockerNormal = FVector::ZeroVector;
    double MinPlaneClearance = TNumericLimits<double>::Max();
    double MaxForwardProgress = 0;
    double MaxEyeErrorCm = 0;
    int32 WalkingSamples = 0;
    int32 InputDownSamples = 0;
    int32 UnexpectedOverlaps = 0;
    int32 UnsupportedSamples = 0;
    int32 MissingEyeSamples = 0;
    int32 RenderObservationSamples = 0;
    FIntPoint MinScenePixels = FIntPoint(MAX_int32, MAX_int32);
    FIntPoint MinTargetPixels = FIntPoint(MAX_int32, MAX_int32);
    FIntPoint MinTexturePixels = FIntPoint(MAX_int32, MAX_int32);
    bool bNative4KRenderingThroughout = true;
    double MaxLateralDriftCm = 0;
    double SweepDistanceCm = 0;
    double MaxDeltaErrorSeconds = 0;
};
