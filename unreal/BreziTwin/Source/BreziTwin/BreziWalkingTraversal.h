#pragma once

#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#include "Components/ActorComponent.h"
#include "BreziWalkingContract.h"
#include "BreziWalkingTraversal.generated.h"

class ABreziPawn;
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
