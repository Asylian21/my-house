#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "BreziMotionQA.generated.h"

class ABreziPawn;
class FJsonObject;
class FJsonValue;
class FBreziMotionViewExtension;
struct FBreziMotionFrameState;

/** Explicit CLI-only visual sequence. Fixed simulation Hz never certifies GPU/display FPS. */
UCLASS()
class UBreziMotionQA : public UActorComponent
{
    GENERATED_BODY()
public:
    UBreziMotionQA();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction) override;
private:
    ABreziPawn* Pawn() const;
    void OnScreenshotCaptured(int32 Width, int32 Height, const TArray<FColor>& Bitmap);
    void OnScreenshotProcessed();
    void Finish(const FString& Status, const FString& Reason = FString());
    bool SaveReport(const FString& Status, const FString& Reason) const;
    void RestoreClock();
    TSharedRef<FJsonObject> QualitySettings() const;

    TSharedPtr<FBreziMotionViewExtension, ESPMode::ThreadSafe> Extension;
    TSharedPtr<FBreziMotionFrameState, ESPMode::ThreadSafe> FrameState;
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
