#include "BreziRuntimeDiagnostics.h"

#include "GameFramework/WorldSettings.h"
#include "Misc/App.h"
#include "BreziPawn.h"
#include "BreziExteriorLighting.h"
#include "BreziGameViewportClient.h"
#include "Dom/JsonObject.h"
#include "DynamicRHI.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "GPUProfiler.h"
#include "HAL/PlatformApplicationMisc.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformMisc.h"
#include "HighResScreenshot.h"
#include "ImageCore.h"
#include "ImageUtils.h"
#include "Misc/CommandLine.h"
#include "Misc/DateTime.h"
#include "Misc/EngineVersion.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/OutputDevice.h"
#include "Misc/OutputDeviceRedirector.h"
#include "Misc/ScopeLock.h"
#include "RenderTimer.h"
#include "RHI.h"
#include "RHIStrings.h"
#include "SceneView.h"
#include "SceneManagement.h"
#include "SceneViewExtension.h"
#include "Serialization/JsonSerializer.h"
#include "UnrealClient.h"
#include "Widgets/SWindow.h"

namespace
{
    const TCHAR* AntiAliasingMethodName(EAntiAliasingMethod Method)
    {
        switch (Method)
        {
        case AAM_None: return TEXT("None");
        case AAM_FXAA: return TEXT("FXAA");
        case AAM_TemporalAA: return TEXT("TAA");
        case AAM_MSAA: return TEXT("MSAA");
        case AAM_TSR: return TEXT("TSR");
        case AAM_SMAA: return TEXT("SMAA");
        default: return TEXT("Unknown");
        }
    }

    const TCHAR* PrimaryScreenPercentageMethodName(EPrimaryScreenPercentageMethod Method)
    {
        switch (Method)
        {
        case EPrimaryScreenPercentageMethod::SpatialUpscale: return TEXT("SpatialUpscale");
        case EPrimaryScreenPercentageMethod::TemporalUpscale: return TEXT("TemporalUpscale");
        case EPrimaryScreenPercentageMethod::RawOutput: return TEXT("RawOutput");
        default: return TEXT("Unknown");
        }
    }

    TSharedRef<FJsonObject> ViewRectangleJson(const FIntRect& Rectangle)
    {
        TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
        Result->SetNumberField(TEXT("minX"), Rectangle.Min.X);
        Result->SetNumberField(TEXT("minY"), Rectangle.Min.Y);
        Result->SetNumberField(TEXT("width"), Rectangle.Width());
        Result->SetNumberField(TEXT("height"), Rectangle.Height());
        return Result;
    }
}

// This observes the composed per-view settings after camera/volume blending. It does not alter
// the view, issue renderer commands, or retain the diagnostics component across world teardown.
class FBreziFinalViewSettings final : public FWorldSceneViewExtension
{
public:
    FBreziFinalViewSettings(const FAutoRegister& AutoRegister, UWorld* World)
        : FWorldSceneViewExtension(AutoRegister, World)
        , FrontLayerEnable(IConsoleManager::Get().FindConsoleVariable(TEXT("r.Lumen.TranslucencyReflections.FrontLayer.Enable")))
        , FrontLayerAllow(IConsoleManager::Get().FindConsoleVariable(TEXT("r.Lumen.TranslucencyReflections.FrontLayer.Allow")))
        , CachedLightingExposure(IConsoleManager::Get().FindConsoleVariable(TEXT("r.EyeAdaptation.CachedLightingPreExposure")))
    {}

    virtual int32 GetPriority() const override { return -10000; }

    virtual void BeginRenderViewFamily(FSceneViewFamily& Family) override
    {
        check(IsInGameThread());
        for (const FSceneView* View : Family.Views)
        {
            if (!View || View->bIsSceneCapture || View->bIsReflectionCapture) continue;
            const FFinalPostProcessSettings& PP = View->FinalPostProcessSettings;
            TSharedRef<FJsonObject> Snapshot = MakeShared<FJsonObject>();
            Snapshot->SetStringField(TEXT("status"), TEXT("observed-composed-main-view"));
            Snapshot->SetNumberField(TEXT("autoExposureMinEV"), PP.AutoExposureMinBrightness);
            Snapshot->SetNumberField(TEXT("autoExposureMaxEV"), PP.AutoExposureMaxBrightness);
            Snapshot->SetNumberField(TEXT("autoExposureBias"), PP.AutoExposureBias);
            Snapshot->SetNumberField(TEXT("observedMainViews"), ++Samples);
            Snapshot->SetNumberField(TEXT("unscaledViewWidth"), View->UnscaledViewRect.Width());
            Snapshot->SetNumberField(TEXT("unscaledViewHeight"), View->UnscaledViewRect.Height());
            Snapshot->SetNumberField(TEXT("viewFamilyFrameNumber"), Family.FrameNumber);
            Snapshot->SetNumberField(TEXT("antiAliasingMethod"), static_cast<int32>(View->AntiAliasingMethod));
            Snapshot->SetStringField(TEXT("antiAliasingMethodName"), AntiAliasingMethodName(View->AntiAliasingMethod));
            Snapshot->SetNumberField(TEXT("primaryScreenPercentageMethod"), static_cast<int32>(View->PrimaryScreenPercentageMethod));
            Snapshot->SetStringField(TEXT("primaryScreenPercentageMethodName"), PrimaryScreenPercentageMethodName(View->PrimaryScreenPercentageMethod));
            Snapshot->SetBoolField(TEXT("showFlagPostProcessing"), Family.EngineShowFlags.PostProcessing);
            Snapshot->SetBoolField(TEXT("showFlagAntiAliasing"), Family.EngineShowFlags.AntiAliasing);
            Snapshot->SetBoolField(TEXT("showFlagTemporalAA"), Family.EngineShowFlags.TemporalAA);
            Snapshot->SetNumberField(TEXT("dynamicGlobalIlluminationMethod"), static_cast<int32>(PP.DynamicGlobalIlluminationMethod.GetValue()));
            Snapshot->SetNumberField(TEXT("reflectionMethod"), static_cast<int32>(PP.ReflectionMethod.GetValue()));
            Snapshot->SetNumberField(TEXT("lumenFinalGatherQuality"), PP.LumenFinalGatherQuality);
            Snapshot->SetNumberField(TEXT("lumenReflectionQuality"), PP.LumenReflectionQuality);
            Snapshot->SetNumberField(TEXT("lumenRayLightingModeOverride"), static_cast<int32>(PP.LumenRayLightingMode));
            Snapshot->SetBoolField(TEXT("lumenFrontLayerTranslucencyReflections"), PP.LumenFrontLayerTranslucencyReflections);
            Snapshot->SetBoolField(TEXT("showFlagLumenReflections"), Family.EngineShowFlags.LumenReflections);
            Snapshot->SetBoolField(TEXT("showFlagLumenGlobalIllumination"), Family.EngineShowFlags.LumenGlobalIllumination);
            if (FrontLayerEnable && FrontLayerAllow)
            {
                // Mirrors UE 5.8 Lumen::UseFrontLayerTranslucencyReflections, not a claim that any material draws in that pass.
                Snapshot->SetBoolField(TEXT("effectiveFrontLayerReflectionViewGate"),
                    (PP.LumenFrontLayerTranslucencyReflections || FrontLayerEnable->GetInt() != 0) && FrontLayerAllow->GetInt() != 0 && Family.EngineShowFlags.LumenReflections);
            }
            Snapshot->SetBoolField(TEXT("rhiSupportsRayTracingShaders"), GRHISupportsRayTracingShaders);
            Snapshot->SetBoolField(TEXT("rhiSupportsInlineRayTracing"), GRHISupportsInlineRayTracing);
            Snapshot->SetStringField(TEXT("method"), TEXT("Read-only game-thread FWorldSceneViewExtension::BeginRenderViewFamily snapshot after view creation and postprocess blending. Scene/reflection captures excluded. AA values here precede renderer-side fallback; compare renderThreadAntiAliasing and the GPU profile. Front-layer gate mirrors the public view settings, cvars and show flag used by UE5.8; material eligibility and pass execution still require render evidence. Ray lighting override and cvar are recorded separately because the renderer also applies hardware and GI capability checks."));
            LastSnapshot = Snapshot;
            break;
        }
    }

    virtual void PostRenderViewFamily_RenderThread(FRDGBuilder&, FSceneViewFamily& Family) override
    {
        check(IsInRenderingThread());
        for (const FSceneView* View : Family.Views)
        {
            if (!View || View->bIsSceneCapture || View->bIsReflectionCapture) continue;
            const double Value = View->State ? View->State->GetPreExposure() : 0.0;
            // Observe the renderer's copy, after its AA fallback and projection jitter setup.
            // Copy only scalar values; retain no view, widget, render target or RHI resource.
            FScopeLock Lock(&RenderObservationMutex);
            ++RenderAA.Samples;
            RenderAA.Frame = Family.FrameNumber;
            RenderAA.Method = View->AntiAliasingMethod;
            RenderAA.ScreenPercentageMethod = View->PrimaryScreenPercentageMethod;
            RenderAA.UnscaledViewRect = View->UnscaledViewRect;
            RenderAA.UnconstrainedViewRect = View->UnconstrainedViewRect;
            RenderAA.TargetPixels = Family.RenderTarget ? Family.RenderTarget->GetSizeXY() : FIntPoint::ZeroValue;
            RenderAA.ProjectionJitter = View->ViewMatrices.GetTemporalAAJitter();
            RenderAA.bAllowTemporalJitter = View->bAllowTemporalJitter;
            RenderAA.bCameraCut = View->bCameraCut;
            RenderAA.bPostProcessing = Family.EngineShowFlags.PostProcessing;
            RenderAA.bAntiAliasing = Family.EngineShowFlags.AntiAliasing;
            RenderAA.bTemporalAA = Family.EngineShowFlags.TemporalAA;
            // UE's UpdatePreExposure writes this public view state from the value used for rendering.
            // This existing cvar is ECVF_RenderThreadSafe; no AA cvars are read on this thread.
            if (FMath::IsFinite(Value) && Value > 0 && CachedLightingExposure)
            {
                RenderPreExposure = Value;
                RenderCachedExposureEV = FMath::Clamp(static_cast<double>(CachedLightingExposure->GetFloat()), -16.0, 16.0);
                RenderExposureFrame = Family.FrameNumber;
                ++RenderExposureSamples;
            }
            break;
        }
    }

    TSharedRef<FJsonObject> Read() const
    {
        check(IsInGameThread());
        if (LastSnapshot.IsValid())
        {
            TSharedRef<FJsonObject> Snapshot = MakeShared<FJsonObject>(*LastSnapshot);
            TSharedRef<FJsonObject> Exposure = MakeShared<FJsonObject>();
            FAntiAliasingObservation AntiAliasing;
            {
                FScopeLock Lock(&RenderObservationMutex);
                AntiAliasing = RenderAA;
                Exposure->SetNumberField(TEXT("observedRenderThreadSamples"), RenderExposureSamples);
                if (RenderExposureSamples > 0)
                {
                    const double EV = FMath::Log2(1.0 / RenderPreExposure);
                    Exposure->SetNumberField(TEXT("viewFamilyFrameNumber"), RenderExposureFrame);
                    Exposure->SetNumberField(TEXT("linearPreExposure"), RenderPreExposure);
                    Exposure->SetNumberField(TEXT("exposureEV"), EV);
                    Exposure->SetNumberField(TEXT("cachedLightingPreExposureEV"), RenderCachedExposureEV);
                    Exposure->SetNumberField(TEXT("safeExposureMinEV"), RenderCachedExposureEV - 12.0);
                    Exposure->SetNumberField(TEXT("safeExposureMaxEV"), RenderCachedExposureEV + 8.0);
                    Exposure->SetBoolField(TEXT("withinCachedLightingSafeRange"), EV >= RenderCachedExposureEV - 12.0 && EV <= RenderCachedExposureEV + 8.0);
                }
            }
            Exposure->SetStringField(TEXT("method"), TEXT("Public FSceneViewStateInterface::GetPreExposure read after the main view family on the render thread; scalar snapshot transferred under a mutex. EV=log2(1/preExposure); range mirrors UE5.8 CachedLighting::WriteWarnings (clamped cvar-12,+8). This may be a different frame from the latest game-thread composed postprocess snapshot. Safe-range membership is not a pixel-level clipping analysis."));
            Snapshot->SetObjectField(TEXT("renderThreadPreExposure"), Exposure);
            TSharedRef<FJsonObject> AA = MakeShared<FJsonObject>();
            AA->SetStringField(TEXT("status"), AntiAliasing.Samples > 0 ? TEXT("observed-render-thread-main-view") : TEXT("no-render-thread-main-view-observed"));
            AA->SetNumberField(TEXT("observedRenderThreadSamples"), AntiAliasing.Samples);
            if (AntiAliasing.Samples > 0)
            {
                AA->SetNumberField(TEXT("viewFamilyFrameNumber"), AntiAliasing.Frame);
                AA->SetNumberField(TEXT("antiAliasingMethod"), static_cast<int32>(AntiAliasing.Method));
                AA->SetStringField(TEXT("antiAliasingMethodName"), AntiAliasingMethodName(AntiAliasing.Method));
                AA->SetNumberField(TEXT("primaryScreenPercentageMethod"), static_cast<int32>(AntiAliasing.ScreenPercentageMethod));
                AA->SetStringField(TEXT("primaryScreenPercentageMethodName"), PrimaryScreenPercentageMethodName(AntiAliasing.ScreenPercentageMethod));
                AA->SetObjectField(TEXT("unscaledViewRectPixels"), ViewRectangleJson(AntiAliasing.UnscaledViewRect));
                AA->SetObjectField(TEXT("unconstrainedViewRectPixels"), ViewRectangleJson(AntiAliasing.UnconstrainedViewRect));
                AA->SetNumberField(TEXT("familyRenderTargetWidth"), AntiAliasing.TargetPixels.X);
                AA->SetNumberField(TEXT("familyRenderTargetHeight"), AntiAliasing.TargetPixels.Y);
                AA->SetBoolField(TEXT("projectionJitterFinite"), !AntiAliasing.ProjectionJitter.ContainsNaN());
                if (!AntiAliasing.ProjectionJitter.ContainsNaN())
                {
                    AA->SetNumberField(TEXT("projectionJitterX"), AntiAliasing.ProjectionJitter.X);
                    AA->SetNumberField(TEXT("projectionJitterY"), AntiAliasing.ProjectionJitter.Y);
                }
                AA->SetBoolField(TEXT("allowTemporalJitter"), AntiAliasing.bAllowTemporalJitter);
                AA->SetBoolField(TEXT("cameraCut"), AntiAliasing.bCameraCut);
                AA->SetBoolField(TEXT("showFlagPostProcessing"), AntiAliasing.bPostProcessing);
                AA->SetBoolField(TEXT("showFlagAntiAliasing"), AntiAliasing.bAntiAliasing);
                AA->SetBoolField(TEXT("showFlagTemporalAA"), AntiAliasing.bTemporalAA);
            }
            AA->SetStringField(TEXT("method"), TEXT("Read-only public FSceneView fields in PostRenderViewFamily_RenderThread, after renderer-side AA fallback and projection jitter setup; scalar snapshot transferred under the shared observation mutex. Projection jitter is the normalized projection-matrix offset returned by GetTemporalAAJitter, not pixels. Rectangles and family target dimensions are observed final view/presentation geometry, not private FViewInfo raster ViewRect or AA history dimensions. Use GPU pass input/output dimensions to verify internal resolution and actual pass execution. SpatialUpscale at 100 percent does not imply reduced resolution. This snapshot may differ in frame from game-thread requested settings and composed-view observations; no AA cvars are read on the render thread."));
            AA->SetStringField(TEXT("internalRasterAndHistoryDimensionsStatus"), TEXT("not-observed-by-this-public-view-snapshot; inspect-gpu-pass-input-output"));
            Snapshot->SetObjectField(TEXT("renderThreadAntiAliasing"), AA);
            return Snapshot;
        }
        TSharedRef<FJsonObject> Missing = MakeShared<FJsonObject>();
        Missing->SetStringField(TEXT("status"), TEXT("no-main-view-observed"));
        return Missing;
    }

private:
    const IConsoleVariable* FrontLayerEnable = nullptr;
    const IConsoleVariable* FrontLayerAllow = nullptr;
    const IConsoleVariable* CachedLightingExposure = nullptr;
    struct FAntiAliasingObservation
    {
        int64 Samples = 0;
        uint32 Frame = 0;
        EAntiAliasingMethod Method = AAM_None;
        EPrimaryScreenPercentageMethod ScreenPercentageMethod = EPrimaryScreenPercentageMethod::SpatialUpscale;
        FIntRect UnscaledViewRect = FIntRect(0, 0, 0, 0);
        FIntRect UnconstrainedViewRect = FIntRect(0, 0, 0, 0);
        FIntPoint TargetPixels = FIntPoint::ZeroValue;
        FVector2D ProjectionJitter = FVector2D::ZeroVector;
        bool bAllowTemporalJitter = false;
        bool bCameraCut = false;
        bool bPostProcessing = false;
        bool bAntiAliasing = false;
        bool bTemporalAA = false;
    };
    mutable FCriticalSection RenderObservationMutex;
    FAntiAliasingObservation RenderAA;
    double RenderPreExposure = 0;
    double RenderCachedExposureEV = 0;
    uint32 RenderExposureFrame = 0;
    int64 RenderExposureSamples = 0;
    int64 Samples = 0;
    TSharedPtr<FJsonObject> LastSnapshot;
};

// ProfileGPU writes asynchronously to LogRHI in UE 5.8. Record only that output
// after the requested profile's header; never interpret command acceptance as completion.
class FBreziGPUProfileLog final : public FOutputDevice
{
public:
    explicit FBreziGPUProfileLog(IConsoleVariable* ShowUI)
        : UIOverride(ShowUI, 0)
    {}

    virtual ~FBreziGPUProfileLog() override { Stop(); }

    void Start()
    {
        GLog->AddOutputDevice(this);
        bRegistered = true;
        // AddOutputDevice replays the old backlog; arm only after that returns.
        FScopeLock Lock(&Mutex);
        bArmed = true;
    }

    void Stop()
    {
        if (bRegistered && GLog) GLog->RemoveOutputDevice(this);
        bRegistered = false;
        FScopeLock Lock(&Mutex);
        bArmed = false;
    }

    virtual bool CanBeUsedOnAnyThread() const override { return true; }

    virtual void Serialize(const TCHAR* Message, ELogVerbosity::Type, const FName& Category) override
    {
        if (Category != FName(TEXT("LogRHI"))) return;
        FScopeLock Lock(&Mutex);
        if (!bArmed) return;
        bSawHeader |= FCString::Strstr(Message, TEXT("GPU Profile for Frame ")) != nullptr;
        if (!bSawHeader) return;
        LastLineSeconds = FPlatformTime::Seconds();
        constexpr int32 MaxCharacters = 2 * 1024 * 1024;
        if (Text.Len() + FCString::Strlen(Message) + 1 > MaxCharacters) bTruncated = true;
        else { Text += Message; Text += TEXT("\n"); }
    }

    bool HasSettled(double Now) const
    {
        FScopeLock Lock(&Mutex);
        return bSawHeader && Now - LastLineSeconds >= 0.25;
    }

    FString Read(bool& OutSawHeader, bool& OutTruncated) const
    {
        FScopeLock Lock(&Mutex);
        OutSawHeader = bSawHeader;
        OutTruncated = bTruncated;
        return Text;
    }

private:
    TGuardConsoleVariable<int32> UIOverride;
    mutable FCriticalSection Mutex;
    bool bRegistered = false;
    bool bArmed = false;
    bool bSawHeader = false;
    bool bTruncated = false;
    double LastLineSeconds = 0.0;
    FString Text;
};

namespace
{
    TSharedRef<FJsonObject> Distribution(const TArray<double>& Values)
    {
        TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
        Result->SetNumberField(TEXT("sampleCount"), Values.Num());
        if (Values.IsEmpty())
        {
            Result->SetStringField(TEXT("status"), TEXT("unavailable"));
            return Result;
        }
        TArray<double> Sorted = Values;
        Sorted.Sort();
        double Sum = 0.0;
        for (double Value : Sorted) Sum += Value;
        const auto Percentile = [&Sorted](double Fraction)
        {
            const int32 Index = FMath::Clamp(FMath::CeilToInt(Fraction * Sorted.Num()) - 1, 0, Sorted.Num() - 1);
            return Sorted[Index];
        };
        Result->SetStringField(TEXT("status"), TEXT("measured"));
        Result->SetNumberField(TEXT("meanMs"), Sum / Sorted.Num());
        Result->SetNumberField(TEXT("p50Ms"), Percentile(0.50));
        Result->SetNumberField(TEXT("p95Ms"), Percentile(0.95));
        Result->SetNumberField(TEXT("p99Ms"), Percentile(0.99));
        Result->SetNumberField(TEXT("maxMs"), Sorted.Last());
        return Result;
    }

    TArray<TSharedPtr<FJsonValue>> PixelArray(const FIntPoint& Size)
    {
        return { MakeShared<FJsonValueNumber>(Size.X), MakeShared<FJsonValueNumber>(Size.Y) };
    }

    void AddCycles(TArray<double>& Samples, uint32 Cycles)
    {
        const double Milliseconds = FPlatformTime::ToMilliseconds(Cycles);
        if (Cycles > 0 && FMath::IsFinite(Milliseconds)) Samples.Add(Milliseconds);
    }
}

UBreziRuntimeDiagnostics::UBreziRuntimeDiagnostics()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;
    PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

void UBreziRuntimeDiagnostics::BeginPlay()
{
    Super::BeginPlay();
    bCapture4K = FParse::Param(FCommandLine::Get(), TEXT("BreziCapture4K"));
    bCaptureScene = FParse::Param(FCommandLine::Get(), TEXT("BreziCaptureScene"));
    bCaptureUI = FParse::Param(FCommandLine::Get(), TEXT("BreziCaptureUI"));
    bExitAfterCapture = FParse::Param(FCommandLine::Get(), TEXT("BreziExitAfterCapture"));
    bProfileGPU = FParse::Param(FCommandLine::Get(), TEXT("BreziProfileGPU"));
    bRealtimeOrbit = FParse::Param(FCommandLine::Get(), TEXT("BreziRealtimeOrbit"));
    bEnabled = FParse::Value(FCommandLine::Get(), TEXT("BreziBenchmarkFrames="), BenchmarkFrames) || bCapture4K || bCaptureScene || bCaptureUI || bProfileGPU || bRealtimeOrbit || FParse::Param(FCommandLine::Get(), TEXT("BreziWalk")) || FParse::Param(FCommandLine::Get(), TEXT("BreziWalkAudit"));
    if (!bEnabled) return;
    FinalViewSettings = FSceneViewExtensions::NewExtension<FBreziFinalViewSettings>(GetWorld());
    FParse::Value(FCommandLine::Get(), TEXT("BreziWarmupFrames="), WarmupFrames);
    WarmupFrames = FMath::Clamp(WarmupFrames, 240, 36000);
    BenchmarkFrames = FMath::Clamp(BenchmarkFrames, 240, 36000);
    const FString Directory = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("Diagnostics"));
    IFileManager::Get().MakeDirectory(*Directory, true);
    FString RequestedView;
    FParse::Value(FCommandLine::Get(), TEXT("BreziView="), RequestedView);
    const FString TimeOfDay = FParse::Param(FCommandLine::Get(), TEXT("BreziNight")) ? TEXT("night") : TEXT("day");
    OutputStem = Directory / FString::Printf(TEXT("%s-%s-%s"), *FPaths::MakeValidFileName(RequestedView.IsEmpty() ? TEXT("default") : RequestedView), *TimeOfDay, *FDateTime::UtcNow().ToString(TEXT("%Y%m%dT%H%M%S")));
    ScreenshotPath = OutputStem + (bCaptureUI ? TEXT("-ui.png") : bCaptureScene ? TEXT("-scene.png") : TEXT("-4k.png"));
    GPUProfileArtifactPath = OutputStem + TEXT("-gpu-profile.log");
    if (bRealtimeOrbit)
    {
        FParse::Value(FCommandLine::Get(), TEXT("BreziBenchmarkSeconds="), RealtimeBenchmarkSeconds);
        // This mode observes ordinary wall-time frames. Historical frame-stepped
        // screenshots/traversal and GPU profiling keep their separate contracts.
        if (!bCaptureScene || bCapture4K || bCaptureUI || bProfileGPU
            || !FMath::IsFinite(RealtimeBenchmarkSeconds) || RealtimeBenchmarkSeconds < 10 || RealtimeBenchmarkSeconds > 120
            || FParse::Param(FCommandLine::Get(), TEXT("BreziMotionQA"))
            || FParse::Param(FCommandLine::Get(), TEXT("BreziCausticsMotionQA"))
            || FString(FCommandLine::Get()).Contains(TEXT("BreziWalkTraversal="), ESearchCase::IgnoreCase))
        {
            UE_LOG(LogTemp, Error, TEXT("BreziRealtimeOrbit: incompatible capture, profiler, traversal or duration arguments."));
            Finish(TEXT("realtime-orbit-invalid-arguments"));
            return;
        }
        BenchmarkFrames = 36000; // Safety ceiling, not a fixed simulation rate or requested duration.
        // UE updates the player camera cache after PostPhysics and before
        // PostUpdateWork. Apply this study's orbit before the rendered camera
        // is composed; historical diagnostics keep their original tick group.
        PrimaryComponentTick.TickGroup = TG_PostPhysics;
    }
    if (bProfileGPU) GPUProfileStatus = TEXT("waiting-for-warmup-midpoint");
    PreviousTickSeconds = FPlatformTime::Seconds();
    SetComponentTickEnabled(true);
    UE_LOG(LogTemp, Display, TEXT("Březí diagnostics: %d warmup frames then %d measured frames. Report: %s.json"), WarmupFrames, BenchmarkFrames, *OutputStem);
}

void UBreziRuntimeDiagnostics::EndPlay(const EEndPlayReason::Type Reason)
{
    if (bGPUProfilePending) FinishGPUProfile(TEXT("interrupted-unconfirmed"));
    UGameViewportClient::OnScreenshotCaptured().Remove(ScreenshotCapturedHandle);
    FScreenshotRequest::OnScreenshotRequestProcessed().Remove(ScreenshotProcessedHandle);
    if (bEnabled && !bFinished) WriteReport(TEXT("interrupted-before-completion"));
    FinalViewSettings.Reset();
    Super::EndPlay(Reason);
}

void UBreziRuntimeDiagnostics::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!bEnabled || bFinished) return;
    const double Now = FPlatformTime::Seconds();
    if (bCapturePending)
    {
        if (Now - CaptureRequestedSeconds > 120.0) Finish(TEXT("screenshot-timeout"));
        return;
    }
    const double FrameMs = (Now - PreviousTickSeconds) * 1000.0;
    PreviousTickSeconds = Now;
    if (!GEngine || !GEngine->GameViewport || !GEngine->GameViewport->Viewport) return;
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    ABreziPawn* Pawn = PC ? Cast<ABreziPawn>(PC->GetPawn()) : nullptr;
    if (!Pawn || !Pawn->HasViewpoints())
    {
        if (++Ticks > WarmupFrames) Finish(TEXT("missing-viewpoint-data"));
        return;
    }
    ++Ticks;
    if (bProfileGPU && !bGPUProfileAttempted && Ticks >= WarmupFrames / 2) RequestGPUProfile();
    const bool bProfileWasPending = bGPUProfilePending;
    PollGPUProfile(Now);
    if (bFinished) return;
    if (bProfileWasPending && !bGPUProfilePending) GPUProfileCooldownFrames = 2;
    if (GPUProfileCooldownFrames > 0)
    {
        // Exclude log serialization and its lagged CPU counters even if an unusual
        // profiler delay moved completion beyond the requested warmup interval.
        --GPUProfileCooldownFrames;
        if (Ticks > WarmupFrames) ++GPUProfileExtraWarmupFrames;
        return;
    }
    if (Ticks <= WarmupFrames) return;
    // Normally the one-frame profile is long finished before frame 240. If the
    // RHI is delayed, keep its work out of benchmark samples and report the extension.
    if (bGPUProfilePending) { ++GPUProfileExtraWarmupFrames; return; }
    if (bRealtimeOrbit)
    {
        if (bRealtimeStarted && Pawn->GetActiveViewId() != RealtimeSourceViewId)
        {
            UE_LOG(LogTemp, Error, TEXT("BreziRealtimeOrbit: active source viewpoint changed during measurement."));
            Finish(TEXT("realtime-orbit-view-changed"));
            return;
        }
        const AWorldSettings* WorldSettings = GetWorld() ? GetWorld()->GetWorldSettings() : nullptr;
        if (GEngine->bUseFixedFrameRate || FApp::UseFixedTimeStep() || FApp::IsBenchmarking()
            || !WorldSettings || !FMath::IsNearlyEqual(WorldSettings->GetEffectiveTimeDilation(), 1.0f)
            || !FMath::IsNearlyEqual(Pawn->CustomTimeDilation, 1.0f))
        {
            UE_LOG(LogTemp, Error, TEXT("BreziRealtimeOrbit: fixed or dilated simulation clock is not a real-time performance measurement."));
            Finish(TEXT("realtime-orbit-clock-rejected"));
            return;
        }
        if (!bRealtimeStarted)
        {
            if (!Pawn->SetRealtimeStudyOrbit(0.0))
            {
                UE_LOG(LogTemp, Error, TEXT("BreziRealtimeOrbit: source orbit could not start."));
                Finish(TEXT("realtime-orbit-camera-rejected"));
                return;
            }
            bRealtimeStarted = true;
            RealtimeStartSeconds = Now;
            RealtimeSourceViewId = Pawn->GetActiveViewId();
            // FrameMs still spans the last warmup tick. Start the source camera
            // now, and accept only intervals wholly inside the real-time window.
            return;
        }
        RealtimeElapsedSeconds = Now - RealtimeStartSeconds;
        const double OffsetDegrees = 8.0 * FMath::Sin(2.0 * PI * RealtimeElapsedSeconds / 12.0);
        if (!Pawn->SetRealtimeStudyOrbit(OffsetDegrees))
        {
            UE_LOG(LogTemp, Error, TEXT("BreziRealtimeOrbit: source orbit unavailable or user/mode/transition interference."));
            Finish(TEXT("realtime-orbit-camera-rejected"));
            return;
        }
        const FVector Eye = Pawn->GetActorLocation();
        const double Yaw = Pawn->GetActorRotation().Yaw;
        if (RealtimeCameraSamples > 0)
        {
            const double Travel = FVector::Distance(Eye, RealtimePreviousEye);
            RealtimeCameraTravelCm += Travel;
            RealtimeMovingSamples += Travel > 0.01 ? 1 : 0;
        }
        RealtimePreviousEye = Eye;
        RealtimeMinimumYaw = FMath::Min(RealtimeMinimumYaw, Yaw);
        RealtimeMaximumYaw = FMath::Max(RealtimeMaximumYaw, Yaw);
        ++RealtimeCameraSamples;
    }
    FViewport* Viewport = GEngine->GameViewport->Viewport;
    FinalViewport = Viewport->GetSizeXY();
    if (FrameIntervalsMs.IsEmpty()) InitialViewport = FinalViewport;
    bViewportChanged |= InitialViewport != FinalViewport;
    if (FMath::IsFinite(FrameMs) && FrameMs > 0.0)
    {
        FrameIntervalsMs.Add(FrameMs);
        const FIntPoint TargetPixels = Viewport->GetRenderTargetTextureSizeXY();
        const FTextureRHIRef& Texture = Viewport->GetRenderTargetTexture();
        const FIntPoint TexturePixels = Texture.IsValid() ? FIntPoint(Texture->GetSizeX(), Texture->GetSizeY()) : FIntPoint::ZeroValue;
        MinimumSceneTargetPixels = FIntPoint(FMath::Min(MinimumSceneTargetPixels.X, TargetPixels.X), FMath::Min(MinimumSceneTargetPixels.Y, TargetPixels.Y));
        MinimumSceneTexturePixels = FIntPoint(FMath::Min(MinimumSceneTexturePixels.X, TexturePixels.X), FMath::Min(MinimumSceneTexturePixels.Y, TexturePixels.Y));
        MaximumSceneTexturePixels = FIntPoint(FMath::Max(MaximumSceneTexturePixels.X, TexturePixels.X), FMath::Max(MaximumSceneTexturePixels.Y, TexturePixels.Y));
        bSceneTargetMatchesViewportThroughout &= FinalViewport.X > 0 && FinalViewport.Y > 0
            && TargetPixels == FinalViewport && TexturePixels == FinalViewport;
        bSceneTargetNativeThroughout &= TargetPixels == FIntPoint(3840, 2160) && TexturePixels == FIntPoint(3840, 2160);
        const FSceneViewport* Scene = GEngine->GameViewport->GetGameViewport();
        bSceneSeparateThroughout &= Scene && static_cast<const ISlateViewport*>(Scene)->UseSeparateRenderTarget();
        static const IConsoleVariable* Screen = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage"));
        static const IConsoleVariable* Secondary = IConsoleManager::Get().FindConsoleVariable(TEXT("r.SecondaryScreenPercentage.GameViewport"));
        static const IConsoleVariable* Dynamic = IConsoleManager::Get().FindConsoleVariable(TEXT("r.DynamicRes.OperationMode"));
        bRenderPercentagesNativeThroughout &= Screen && Screen->GetFloat() == 100 && Secondary && Secondary->GetFloat() == 100 && Dynamic && Dynamic->GetInt() == 0;
        // On Mac this public platform query checks NSApp active state plus workspace session.
        // Window focus is separate from scene keyboard focus, which may legitimately be in Slate.
        const bool bForeground = FPlatformApplicationMisc::IsThisApplicationForeground();
        const TSharedPtr<SWindow> Window = GEngine->GameViewport->GetWindow();
        const bool bActiveWindow = Window.IsValid() && Window->IsActive();
        if (FocusSamples == 0 || bPreviousForeground != bForeground || bPreviousActiveWindow != bActiveWindow)
        {
            // Initial state plus changes establish direction; aggregate counts alone do not.
            TSharedPtr<FJsonObject> Event = MakeShared<FJsonObject>();
            Event->SetNumberField(TEXT("sampleIndex"), FocusSamples);
            Event->SetNumberField(TEXT("gameFrameCounter"), static_cast<double>(GFrameCounter));
            Event->SetNumberField(TEXT("platformSeconds"), Now);
            Event->SetBoolField(TEXT("applicationForeground"), bForeground);
            Event->SetBoolField(TEXT("gameWindowActive"), bActiveWindow);
            FocusEvents.Add(Event);
        }
        if (FocusSamples > 0 && bPreviousForeground != bForeground) ++ForegroundTransitions;
        bPreviousForeground = bForeground;
        bPreviousActiveWindow = bActiveWindow;
        ++FocusSamples;
        ForegroundSamples += bForeground ? 1 : 0;
        ActiveWindowSamples += bActiveWindow ? 1 : 0;
        ViewportFocusSamples += Viewport->HasFocus() ? 1 : 0;
    }
    AddCycles(GameThreadMs, GGameThreadTime);
    AddCycles(RenderThreadMs, GRenderThreadTime);
    if (GDynamicRHI) AddCycles(GPUFrameMs, RHIGetGPUFrameCycles());
    if (bRealtimeOrbit ? RealtimeElapsedSeconds < RealtimeBenchmarkSeconds && FrameIntervalsMs.Num() < BenchmarkFrames
        : FrameIntervalsMs.Num() < BenchmarkFrames) return;
    if (bCapture4K || bCaptureScene || bCaptureUI) RequestCapture();
    else Finish(TEXT("benchmark-complete"));
}

void UBreziRuntimeDiagnostics::RequestGPUProfile()
{
    bGPUProfileAttempted = true;
    GPUProfileRequestTick = Ticks;
    IConsoleObject* Object = IConsoleManager::Get().FindConsoleObject(TEXT("ProfileGPU"));
    IConsoleCommand* Command = Object ? Object->AsCommand() : nullptr;
    IConsoleVariable* ShowUI = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ProfileGPU.ShowUI"));
    if (!Command || !ShowUI || !GLog)
    {
        GPUProfileStatus = TEXT("profiler-command-or-output-unavailable");
        return;
    }
    if (UE::RHI::GPUProfiler::IsProfiling())
    {
        GPUProfileStatus = TEXT("skipped-another-profile-is-active");
        Finish(TEXT("gpu-profile-conflict-during-warmup"));
        return;
    }
    GPUProfileLog = MakeShared<FBreziGPUProfileLog, ESPMode::ThreadSafe>(ShowUI);
    if (ShowUI->GetInt() != 0)
    {
        GPUProfileStatus = TEXT("cannot-disable-profiler-ui");
        GPUProfileLog.Reset();
        return;
    }
    GPUProfileLog->Start();
    GPUProfileRequestedSeconds = FPlatformTime::Seconds();
    bGPUProfilePending = Command->Execute(TArray<FString>(), GetWorld(), *GLog);
    bGPUProfileObservedActive = UE::RHI::GPUProfiler::IsProfiling();
    GPUProfileStatus = bGPUProfilePending ? TEXT("requested-unconfirmed") : TEXT("command-rejected");
    if (!bGPUProfilePending) GPUProfileLog.Reset();
    UE_LOG(LogTemp, Display, TEXT("Březí GPU profile request at warmup frame %d: %s. Expected log artifact: %s"), Ticks, *GPUProfileStatus, *GPUProfileArtifactPath);
}

void UBreziRuntimeDiagnostics::PollGPUProfile(double Now)
{
    if (!bGPUProfilePending) return;
    const bool bActive = UE::RHI::GPUProfiler::IsProfiling();
    bGPUProfileObservedActive |= bActive;
    if (!bActive && GPUProfileLog.IsValid() && GPUProfileLog->HasSettled(Now))
    {
        FinishGPUProfile(TEXT("profile-log-observed"));
    }
    else if (Now - GPUProfileRequestedSeconds > 30.0)
    {
        FinishGPUProfile(TEXT("request-timed-out-unconfirmed"));
        // Do not publish steady-state benchmark numbers while profile work is unresolved.
        Finish(TEXT("gpu-profile-unconfirmed-during-warmup"));
    }
}

void UBreziRuntimeDiagnostics::FinishGPUProfile(const FString& Status)
{
    GPUProfileStatus = Status;
    if (GPUProfileLog.IsValid())
    {
        GPUProfileLog->Stop();
        const FString ProfileText = GPUProfileLog->Read(bGPUProfileHeaderObserved, bGPUProfileLogTruncated);
        if (!ProfileText.IsEmpty())
        {
            bGPUProfileArtifactSaved = FFileHelper::SaveStringToFile(ProfileText, *GPUProfileArtifactPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)
                && IFileManager::Get().FileSize(*GPUProfileArtifactPath) > 0;
        }
        GPUProfileLog.Reset(); // Also restores the previous profiler UI setting.
    }
    bGPUProfilePending = false;
    if (Status == TEXT("profile-log-observed") && !bGPUProfileArtifactSaved) GPUProfileStatus = TEXT("profile-log-observed-artifact-save-failed");
}

void UBreziRuntimeDiagnostics::RequestCapture()
{
    bCapturePending = true;
    CaptureRequestedSeconds = FPlatformTime::Seconds();
    ScreenshotCapturedHandle = UGameViewportClient::OnScreenshotCaptured().AddUObject(this, &UBreziRuntimeDiagnostics::OnScreenshotCaptured);
    ScreenshotProcessedHandle = FScreenshotRequest::OnScreenshotRequestProcessed().AddUObject(this, &UBreziRuntimeDiagnostics::OnScreenshotProcessed);
    if (IConsoleVariable* DelegateEnabled = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenshotDelegate"))) DelegateEnabled->Set(1, ECVF_SetByCode);
    if (bCaptureUI)
    {
        ScreenshotKind = TEXT("fitted-slate-ui-capture-actual-window-pixels");
        FScreenshotRequest::RequestScreenshot(ScreenshotPath, true, false, false, FIntRect(), true);
    }
    else if (bCaptureScene)
    {
        // Read the next ordinary frame at the current drawable resolution. Do not
        // invoke HighResShot: that would measure a different render and reset history.
        RequestedCapturePixels = GEngine->GameViewport->Viewport->GetSizeXY();
        if (RequestedCapturePixels.X <= 0 || RequestedCapturePixels.Y <= 0)
        {
            Finish(TEXT("scene-capture-viewport-unavailable"));
            return;
        }
        ScreenshotKind = TEXT("current-scene-render-target-preserving-view-history");
        FScreenshotRequest::RequestScreenshot(ScreenshotPath, false, false, false, FIntRect(), true);
    }
    else if (GEngine->GameViewport->Viewport->GetSizeXY() == FIntPoint(3840, 2160))
    {
        // Capture the next regular frame, preserving the warmed Lumen/TSR view state.
        ScreenshotKind = TEXT("fixed-4k-scene-render-target-preserving-view-history");
        FScreenshotRequest::RequestScreenshot(ScreenshotPath, false, false, false, FIntRect(), true);
    }
    else
    {
        ScreenshotKind = TEXT("high-resolution-scene-capture-not-proof-of-native-backbuffer");
        FHighResScreenshotConfig& Config = GetHighResScreenshotConfig();
        Config.SetHDRCapture(false);
        Config.FilenameOverride = ScreenshotPath;
        if (!Config.SetResolution(3840, 2160, 1.0f) || !GEngine->GameViewport->Viewport->TakeHighResScreenShot())
        {
            Finish(TEXT("screenshot-request-failed"));
        }
    }
}

void UBreziRuntimeDiagnostics::OnScreenshotCaptured(int32 Width, int32 Height, const TArray<FColor>& Bitmap)
{
    if (!bCapturePending || bFinished || Width <= 0 || Height <= 0 || static_cast<int64>(Width) * Height != Bitmap.Num()) return;
    ScreenshotPixels = FIntPoint(Width, Height);
    // The capture delegate replaces Unreal's disk writer. Save synchronously before allowing exit.
    bScreenshotSaved = FImageUtils::SaveImageByExtension(*ScreenshotPath, FImageView(Bitmap.GetData(), Width, Height));
    bScreenshotSaved &= IFileManager::Get().FileSize(*ScreenshotPath) > 0;
}

void UBreziRuntimeDiagnostics::OnScreenshotProcessed()
{
    if (!bCapturePending || bFinished) return;
    const bool bCorrectDimensions = bCaptureUI || (bCaptureScene
        ? RequestedCapturePixels.X > 0 && RequestedCapturePixels.Y > 0 && ScreenshotPixels == RequestedCapturePixels
        : ScreenshotPixels == FIntPoint(3840, 2160));
    Finish(bScreenshotSaved && bCorrectDimensions ? TEXT("capture-complete") : TEXT("screenshot-save-or-dimensions-failed"));
}

void UBreziRuntimeDiagnostics::Finish(const FString& Status)
{
    bFinished = true;
    bCapturePending = false;
    UGameViewportClient::OnScreenshotCaptured().Remove(ScreenshotCapturedHandle);
    FScreenshotRequest::OnScreenshotRequestProcessed().Remove(ScreenshotProcessedHandle);
    WriteReport(Status);
    SetComponentTickEnabled(false);
    // Finish runs only after the screenshot callback synchronously writes the PNG and its report.
    if (bExitAfterCapture) FPlatformMisc::RequestExit(false);
}

void UBreziRuntimeDiagnostics::WriteReport(const FString& Status)
{
    check(IsInGameThread());
    const bool bMeasurementComplete = bRealtimeOrbit
        ? FrameIntervalsMs.Num() >= 240 && RealtimeElapsedSeconds >= RealtimeBenchmarkSeconds
        : FrameIntervalsMs.Num() >= BenchmarkFrames;
    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("status"), Status);
    Report->SetStringField(TEXT("recordedAtUtc"), FDateTime::UtcNow().ToIso8601());
    Report->SetStringField(TEXT("engineVersion"), FEngineVersion::Current().ToString());
    Report->SetStringField(TEXT("cpu"), FPlatformMisc::GetCPUBrand());
    Report->SetStringField(TEXT("gpu"), GRHIAdapterName);
    Report->SetStringField(TEXT("rhi"), GDynamicRHI ? GDynamicRHI->GetName() : TEXT("unavailable"));
    Report->SetStringField(TEXT("shaderPlatform"), LexToString(GMaxRHIShaderPlatform));
    Report->SetBoolField(TEXT("rhiReportsRayTracingSupport"), GRHISupportsRayTracing);
    FString OS, OSDetail;
    FPlatformMisc::GetOSVersions(OS, OSDetail);
    Report->SetStringField(TEXT("os"), OS + TEXT(" ") + OSDetail);
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    const ABreziPawn* Pawn = PC ? Cast<ABreziPawn>(PC->GetPawn()) : nullptr;
    Report->SetStringField(TEXT("activeView"), Pawn ? Pawn->GetActiveViewId() : TEXT("unavailable"));
    if (Pawn) Report->SetObjectField(TEXT("walking"), Pawn->GetWalkingDiagnostics());
    Report->SetStringField(TEXT("lighting"), FParse::Param(FCommandLine::Get(), TEXT("BreziNight")) ? TEXT("night-study") : TEXT("imported-daylight"));
    Report->SetNumberField(TEXT("warmupFrames"), WarmupFrames);
    Report->SetNumberField(TEXT("requestedBenchmarkFrames"), BenchmarkFrames);
    if (bRealtimeOrbit)
    {
        TSharedRef<FJsonObject> Motion = MakeShared<FJsonObject>();
        Motion->SetStringField(TEXT("mode"), TEXT("source-orbit-wall-time"));
        Motion->SetStringField(TEXT("sourceViewId"), RealtimeSourceViewId);
        Motion->SetNumberField(TEXT("requestedSeconds"), RealtimeBenchmarkSeconds);
        Motion->SetNumberField(TEXT("elapsedWallSeconds"), RealtimeElapsedSeconds);
        Motion->SetNumberField(TEXT("yawAmplitudeDegrees"), 8.0);
        Motion->SetNumberField(TEXT("periodSeconds"), 12.0);
        Motion->SetNumberField(TEXT("cameraSamples"), RealtimeCameraSamples);
        Motion->SetNumberField(TEXT("movingCameraSamples"), RealtimeMovingSamples);
        Motion->SetNumberField(TEXT("cameraTravelCm"), RealtimeCameraTravelCm);
        if (RealtimeCameraSamples > 0)
        {
            Motion->SetNumberField(TEXT("minimumCameraYaw"), RealtimeMinimumYaw);
            Motion->SetNumberField(TEXT("maximumCameraYaw"), RealtimeMaximumYaw);
        }
        Motion->SetBoolField(TEXT("measurementCompleted"), bMeasurementComplete);
        Motion->SetBoolField(TEXT("engineClockModifiedByStudy"), false);
        Motion->SetStringField(TEXT("scope"), TEXT("Ordinary wall-time frames while the source orbit camera sweeps +/-8 degrees over 12 seconds. Fixed-step/fixed-rate/benchmark and dilated clocks are rejected each measured tick. No keyboard, walking, collision or compositor presentation-event claim. One regular screenshot after timing."));
        Report->SetObjectField(TEXT("realtimeOrbit"), Motion);
    }
    int32 Over30HzBudget = 0, Over50Ms = 0, Over100Ms = 0;
    for (double Interval : FrameIntervalsMs)
    {
        Over30HzBudget += Interval > 1000.0 / 30.0 ? 1 : 0;
        Over50Ms += Interval > 50.0 ? 1 : 0;
        Over100Ms += Interval > 100.0 ? 1 : 0;
    }
    TSharedRef<FJsonObject> FrameBudget = MakeShared<FJsonObject>();
    FrameBudget->SetNumberField(TEXT("targetFps"), 30);
    FrameBudget->SetNumberField(TEXT("sampleCount"), FrameIntervalsMs.Num());
    FrameBudget->SetNumberField(TEXT("intervalsOver33_333Ms"), Over30HzBudget);
    FrameBudget->SetNumberField(TEXT("intervalsOver50Ms"), Over50Ms);
    FrameBudget->SetNumberField(TEXT("intervalsOver100Ms"), Over100Ms);
    Report->SetObjectField(TEXT("frameBudget"), FrameBudget);
    TSharedRef<FJsonObject> Profile = MakeShared<FJsonObject>();
    Profile->SetBoolField(TEXT("requestedByCLI"), bProfileGPU);
    Profile->SetStringField(TEXT("status"), GPUProfileStatus);
    Profile->SetStringField(TEXT("backend"), TEXT("UE5.8 ProfileGPU command to LogRHI; no trace session requested"));
    Profile->SetNumberField(TEXT("requestWarmupFrame"), GPUProfileRequestTick);
    Profile->SetNumberField(TEXT("extraExcludedWarmupFrames"), GPUProfileExtraWarmupFrames);
    Profile->SetBoolField(TEXT("profilerActiveObserved"), bGPUProfileObservedActive);
    Profile->SetBoolField(TEXT("profileHeaderObserved"), bGPUProfileHeaderObserved);
    Profile->SetBoolField(TEXT("artifactSaved"), bGPUProfileArtifactSaved);
    Profile->SetBoolField(TEXT("artifactTruncated"), bGPUProfileLogTruncated);
    if (bGPUProfileArtifactSaved) Profile->SetStringField(TEXT("artifactPath"), GPUProfileArtifactPath);
    Profile->SetStringField(TEXT("verification"), TEXT("Command acceptance is not completion. Profile output is observed only after a GPU Profile for Frame header, an idle engine profiler, and 250ms without further LogRHI lines. Saved output must still be inspected for meaningful per-pass timing data."));
    Report->SetObjectField(TEXT("gpuProfile"), Profile);
    TSharedRef<FJsonObject> Focus = MakeShared<FJsonObject>();
    Focus->SetNumberField(TEXT("sampleCount"), FocusSamples);
    Focus->SetNumberField(TEXT("applicationForegroundSamples"), ForegroundSamples);
    Focus->SetNumberField(TEXT("gameWindowActiveSamples"), ActiveWindowSamples);
    Focus->SetNumberField(TEXT("sceneViewportKeyboardFocusSamples"), ViewportFocusSamples);
    Focus->SetNumberField(TEXT("applicationForegroundTransitions"), ForegroundTransitions);
    Focus->SetBoolField(TEXT("applicationForegroundThroughoutBenchmark"), bMeasurementComplete && FocusSamples == FrameIntervalsMs.Num() && ForegroundSamples == FocusSamples);
    TArray<TSharedPtr<FJsonValue>> FocusEventValues;
    for (const TSharedPtr<FJsonObject>& Event : FocusEvents) FocusEventValues.Add(MakeShared<FJsonValueObject>(Event));
    Focus->SetArrayField(TEXT("initialStateAndChanges"), FocusEventValues);
    if (FocusSamples > 0)
    {
        Focus->SetBoolField(TEXT("lastApplicationForeground"), bPreviousForeground);
        Focus->SetBoolField(TEXT("lastGameWindowActive"), bPreviousActiveWindow);
    }
    Focus->SetStringField(TEXT("method"), TEXT("Sampled with accepted frame intervals. Foreground: FPlatformApplicationMisc::IsThisApplicationForeground (Mac NSApp active and workspace session active). Window: SWindow::IsActive. Scene keyboard focus: FViewport::HasFocus; false may mean an in-window Slate control has focus. These states do not measure visual occlusion."));
    Report->SetObjectField(TEXT("focusDuringBenchmark"), Focus);
    Report->SetArrayField(TEXT("initialGameViewportPixels"), PixelArray(InitialViewport));
    Report->SetArrayField(TEXT("finalGameViewportPixels"), PixelArray(FinalViewport));
    Report->SetBoolField(TEXT("viewportChangedDuringBenchmark"), bViewportChanged);
    if (!FrameIntervalsMs.IsEmpty())
    {
        Report->SetArrayField(TEXT("minimumSceneRenderTargetPixelsDuringBenchmark"), PixelArray(MinimumSceneTargetPixels));
        Report->SetArrayField(TEXT("minimumSceneRHITexturePixelsDuringBenchmark"), PixelArray(MinimumSceneTexturePixels));
        Report->SetArrayField(TEXT("maximumSceneRHITexturePixelsDuringBenchmark"), PixelArray(MaximumSceneTexturePixels));
    }
    Report->SetBoolField(TEXT("sceneRenderTargetWas4KThroughoutBenchmark"), bMeasurementComplete && bSceneTargetNativeThroughout);
    Report->SetBoolField(TEXT("separateSceneRenderTargetThroughoutBenchmark"), bMeasurementComplete && bSceneSeparateThroughout);
    Report->SetBoolField(TEXT("sceneTargetMatchesViewportThroughoutBenchmark"), bMeasurementComplete && bSceneTargetMatchesViewportThroughout);
    if (bCaptureScene) Report->SetArrayField(TEXT("requestedSceneCapturePixels"), PixelArray(RequestedCapturePixels));
    Report->SetBoolField(TEXT("renderPercentagesNativeThroughoutBenchmark"), bMeasurementComplete && bRenderPercentagesNativeThroughout);
    Report->SetBoolField(TEXT("gameViewportWasAtLeast4KThroughoutBenchmark"), bMeasurementComplete && !bViewportChanged && InitialViewport.X >= 3840 && InitialViewport.Y >= 2160);
    if (GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport)
    {
        FViewport* Viewport = GEngine->GameViewport->Viewport;
        Report->SetArrayField(TEXT("reportedRenderTargetPixels"), PixelArray(Viewport->GetRenderTargetTextureSizeXY()));
        const FTextureRHIRef& Texture = Viewport->GetRenderTargetTexture();
        if (Texture.IsValid()) Report->SetArrayField(TEXT("rhiRenderTargetTexturePixels"), PixelArray(FIntPoint(Texture->GetSizeX(), Texture->GetSizeY())));
        else Report->SetStringField(TEXT("rhiRenderTargetTextureStatus"), TEXT("unavailable-on-game-thread"));
    }
    if (const UBreziGameViewportClient* Presentation = GEngine ? Cast<UBreziGameViewportClient>(GEngine->GameViewport) : nullptr)
        Report->SetObjectField(TEXT("presentation"), Presentation->GetPresentationDiagnostics());
    Report->SetStringField(TEXT("resolutionInterpretation"), TEXT("Game viewport and scene RT pixels describe 3D rendering. The fitted window, Slate/UI presentation and actual UI screenshot can be smaller. A 4K scene capture does not prove a 4K physical display or OS backbuffer."));
    TSharedRef<FJsonObject> Settings = MakeShared<FJsonObject>();
    for (const TCHAR* Name : {
        TEXT("r.EyeAdaptation.CachedLightingPreExposure"),
        TEXT("r.ScreenPercentage"),
        TEXT("r.SecondaryScreenPercentage.GameViewport"),
        TEXT("r.DynamicRes.OperationMode"),
        TEXT("r.AntiAliasingMethod"),
        TEXT("r.TemporalAA.Quality"),
        TEXT("r.TemporalAA.Upsampling"),
        TEXT("r.TemporalAA.Upscaler"),
        TEXT("r.TemporalAA.HistoryScreenPercentage"),
        TEXT("r.TemporalAA.R11G11B10History"),
        TEXT("r.TemporalAA.UseMobileConfig"),
        TEXT("r.TemporalAACurrentFrameWeight"),
        TEXT("r.TemporalAAFilterSize"),
        TEXT("r.TemporalAACatmullRom"),
        TEXT("r.TemporalAASamples"),
        TEXT("r.SMAA.Quality"),
        TEXT("r.SMAA.EdgeMode"),
        TEXT("r.SMAA.DebugVisualization"),
        TEXT("r.TSR.History.ScreenPercentage"),
        TEXT("r.Lumen.RadianceCache.SortTraceTiles"),
        TEXT("r.TSR.History.UpdateQuality"),
        TEXT("r.TSR.History.R11G11B10"),
        TEXT("r.TSR.ReprojectionField"),
        TEXT("r.TSR.16BitVALU"),
        TEXT("r.TSR.WaveOps"),
        TEXT("r.TSR.AsyncCompute"),
        TEXT("rhi.Metal.SampleComputeEncoderTimings"),
        TEXT("r.DynamicGlobalIlluminationMethod"),
        TEXT("r.ReflectionMethod"),
        TEXT("r.RayTracing"),
        TEXT("r.Lumen.HardwareRayTracing"),
        TEXT("r.Lumen.HardwareRayTracing.LightingMode"),
        TEXT("r.Lumen.AsyncCompute"),
        TEXT("r.Lumen.DiffuseIndirect.AsyncCompute"),
        TEXT("r.Lumen.ScreenProbeGather.DownsampleFactor"),
        TEXT("r.Lumen.ScreenProbeGather.TracingOctahedronResolution"),
        TEXT("r.Lumen.ScreenProbeGather.RadianceCache.NumProbesToTraceBudget"),
        TEXT("r.Lumen.Reflections.DownsampleFactor"),
        TEXT("r.Lumen.TranslucencyReflections.FrontLayer.Enable"),
        TEXT("r.Lumen.TranslucencyReflections.FrontLayer.EnableForProject"),
        TEXT("r.Lumen.TranslucencyReflections.FrontLayer.Allow"),
        TEXT("r.TranslucencyLightingVolume.Dim"),
        TEXT("r.Nanite"),
        TEXT("r.Nanite.ProjectEnabled"),
        TEXT("r.SkinCache.CompileShaders"),
        TEXT("r.SkinCache.Mode"),
        TEXT("r.Shadow.Virtual.Enable"),
        TEXT("r.VSync"),
        TEXT("Slate.AllowBackgroundBlurWidgets"),
        TEXT("Slate.ForceBackgroundBlurLowQualityOverride")
    })
    {
        if (const IConsoleVariable* Variable = IConsoleManager::Get().FindConsoleVariable(Name)) Settings->SetNumberField(Name, Variable->GetFloat());
    }
    Report->SetObjectField(TEXT("renderSettings"), Settings);
    Report->SetStringField(TEXT("renderSettingsMethod"), TEXT("Console variables read once on the game thread while writing this report. These are requested settings; inactive-method TAA/SMAA/TSR values may still be present. Actual composed and render-thread AA methods are reported separately; shader permutation and pass execution require GPU evidence."));
    if (FinalViewSettings.IsValid()) Report->SetObjectField(TEXT("finalViewPostProcessSettings"), FinalViewSettings->Read());
    if (const auto* Exterior = GetOwner()->FindComponentByClass<UBreziExteriorLighting>())
        Report->SetObjectField(TEXT("exteriorLighting"), Exterior->Readback());
    if (GEngine && GEngine->GameViewport)
        if (TSharedPtr<SWindow> Window = GEngine->GameViewport->GetWindow()) Report->SetStringField(TEXT("gameWindowTitle"), Window->GetTitle().ToString());
    Report->SetObjectField(TEXT("frameInterval"), Distribution(FrameIntervalsMs));
    Report->SetObjectField(TEXT("cpuGameThreadActive"), Distribution(GameThreadMs));
    Report->SetObjectField(TEXT("cpuRenderThreadActive"), Distribution(RenderThreadMs));
    Report->SetObjectField(TEXT("gpuFrameFromRHITimer"), Distribution(GPUFrameMs));
    Report->SetStringField(TEXT("timingMethod"), TEXT("Frame intervals are measured wall clock between game ticks, including waits. CPU counters exclude idle time. GPU uses RHIGetGPUFrameCycles only when nonzero. GPU and thread counters may lag; they are independent distributions, not paired per-frame timings. Capture work is excluded from benchmark samples."));
    Report->SetStringField(TEXT("screenshotKind"), ScreenshotKind);
    Report->SetBoolField(TEXT("screenshotSaved"), bScreenshotSaved);
    Report->SetArrayField(TEXT("screenshotPixels"), PixelArray(ScreenshotPixels));
    if (bScreenshotSaved) Report->SetStringField(TEXT("screenshotPath"), ScreenshotPath);
    FString Json;
    FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Json));
    if (FFileHelper::SaveStringToFile(Json, *(OutputStem + TEXT(".json")), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
    {
        UE_LOG(LogTemp, Display, TEXT("Březí diagnostics %s: %s.json"), *Status, *OutputStem);
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("Březí diagnostics report could not be saved: %s.json"), *OutputStem);
    }
}
