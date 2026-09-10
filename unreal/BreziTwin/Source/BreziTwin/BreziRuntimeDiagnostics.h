#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "BreziRuntimeDiagnostics.generated.h"

class FBreziGPUProfileLog;
class FBreziFinalViewSettings;
class FJsonObject;

UCLASS()
class UBreziRuntimeDiagnostics : public UActorComponent
{
    GENERATED_BODY()
public:
    UBreziRuntimeDiagnostics();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    void RequestCapture();
    void RequestGPUProfile();
    void PollGPUProfile(double Now);
    void FinishGPUProfile(const FString& Status);
    void OnScreenshotCaptured(int32 Width, int32 Height, const TArray<FColor>& Bitmap);
    void OnScreenshotProcessed();
    void Finish(const FString& Status);
    void WriteReport(const FString& Status);

    bool bEnabled = false;
    bool bCapture4K = false;
    bool bCaptureScene = false;
    bool bCaptureUI = false;
    bool bExitAfterCapture = false;
    bool bCapturePending = false;
    bool bScreenshotSaved = false;
    bool bFinished = false;
    bool bProfileGPU = false;
    bool bRealtimeOrbit = false;
    bool bRealtimeStarted = false;
    double RealtimeBenchmarkSeconds = 60.0;
    double RealtimeStartSeconds = 0.0;
    double RealtimeElapsedSeconds = 0.0;
    double RealtimeCameraTravelCm = 0.0;
    double RealtimeMinimumYaw = TNumericLimits<double>::Max();
    double RealtimeMaximumYaw = -TNumericLimits<double>::Max();
    FVector RealtimePreviousEye = FVector::ZeroVector;
    int32 RealtimeCameraSamples = 0;
    int32 RealtimeMovingSamples = 0;
    FString RealtimeSourceViewId;
    bool bGPUProfileAttempted = false;
    bool bGPUProfilePending = false;
    bool bGPUProfileObservedActive = false;
    bool bGPUProfileHeaderObserved = false;
    bool bGPUProfileArtifactSaved = false;
    bool bGPUProfileLogTruncated = false;
    int32 GPUProfileRequestTick = 0;
    int32 GPUProfileExtraWarmupFrames = 0;
    int32 GPUProfileCooldownFrames = 0;
    double GPUProfileRequestedSeconds = 0.0;
    FString GPUProfileStatus = TEXT("not-requested");
    FString GPUProfileArtifactPath;
    TSharedPtr<FBreziGPUProfileLog, ESPMode::ThreadSafe> GPUProfileLog;
    TSharedPtr<FBreziFinalViewSettings, ESPMode::ThreadSafe> FinalViewSettings;
    int32 WarmupFrames = 240;
    int32 BenchmarkFrames = 300;
    int32 Ticks = 0;
    double PreviousTickSeconds = 0.0;
    double CaptureRequestedSeconds = 0.0;
    FString OutputStem;
    FString ScreenshotPath;
    FString ScreenshotKind = TEXT("none");
    FIntPoint InitialViewport = FIntPoint::ZeroValue;
    FIntPoint FinalViewport = FIntPoint::ZeroValue;
    FIntPoint ScreenshotPixels = FIntPoint::ZeroValue;
    FIntPoint RequestedCapturePixels = FIntPoint::ZeroValue;
    bool bViewportChanged = false;
    FIntPoint MinimumSceneTargetPixels = FIntPoint(MAX_int32, MAX_int32);
    FIntPoint MinimumSceneTexturePixels = FIntPoint(MAX_int32, MAX_int32);
    FIntPoint MaximumSceneTexturePixels = FIntPoint::ZeroValue;
    bool bSceneTargetMatchesViewportThroughout = true;
    bool bSceneTargetNativeThroughout = true;
    bool bSceneSeparateThroughout = true;
    bool bRenderPercentagesNativeThroughout = true;
    int32 FocusSamples = 0;
    int32 ForegroundSamples = 0;
    int32 ActiveWindowSamples = 0;
    int32 ViewportFocusSamples = 0;
    int32 ForegroundTransitions = 0;
    bool bPreviousForeground = false;
    bool bPreviousActiveWindow = false;
    TArray<TSharedPtr<FJsonObject>> FocusEvents;
    TArray<double> FrameIntervalsMs;
    TArray<double> GameThreadMs;
    TArray<double> RenderThreadMs;
    TArray<double> GPUFrameMs;
    FDelegateHandle ScreenshotCapturedHandle;
    FDelegateHandle ScreenshotProcessedHandle;
};
