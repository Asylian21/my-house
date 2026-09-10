#include "BreziMotionQA.h"
#include "BreziPawn.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformMisc.h"
#include "ImageCore.h"
#include "ImageUtils.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/ScopeLock.h"
#include "SceneView.h"
#include "SceneManagement.h"
#include "SceneViewExtension.h"
#include "Serialization/JsonSerializer.h"
#include "UnrealClient.h"

namespace
{
constexpr int32 SimulatedHz = 30;
constexpr int32 RequiredWarmup = 240;
constexpr int32 PreFrames = 4;
constexpr int32 MotionFrames = 48;
constexpr int32 TailFrames = 12;
constexpr int32 TotalFrames = PreFrames + MotionFrames + TailFrames;
TArray<TSharedPtr<FJsonValue>> XYZ(const FVector& V)
{
    return {MakeShared<FJsonValueNumber>(V.X), MakeShared<FJsonValueNumber>(V.Y), MakeShared<FJsonValueNumber>(V.Z)};
}
TArray<TSharedPtr<FJsonValue>> XY(double X, double Y)
{
    return {MakeShared<FJsonValueNumber>(X), MakeShared<FJsonValueNumber>(Y)};
}
TSharedRef<FJsonObject> ViewpointJson(const FBreziViewpoint& View)
{
    TSharedRef<FJsonObject> J = MakeShared<FJsonObject>();
    J->SetStringField(TEXT("id"), View.Id);
    J->SetArrayField(TEXT("eyeCm"), XYZ(View.EyeCm));
    J->SetArrayField(TEXT("targetCm"), XYZ(View.TargetCm));
    J->SetNumberField(TEXT("horizontalFovDegrees"), View.HorizontalFovDegrees);
    return J;
}
FString JsonText(const TSharedRef<FJsonObject>& Value)
{
    FString Text;
    FJsonSerializer::Serialize(Value, TJsonWriterFactory<>::Create(&Text));
    return Text;
}
}

// One armed capture only. No latest-frame fallback and no retained renderer resource/UObject.
struct FBreziMotionFrameState
{
    FCriticalSection Mutex;
    uint64 WantedCounter = MAX_uint64;
    uint64 WarmupStartCounter = MAX_uint64;
    int32 WarmupGameViews = 0;
    int32 WarmupRenderViews = 0;
    bool bWarmupGameConsecutive = true;
    bool bWarmupRenderConsecutive = true;
    uint64 GameCounter = 0;
    uint64 RenderCounter = 0;
    uint32 GameFamilyFrame = 0;
    uint32 RenderFamilyFrame = 0;
    int32 GameViews = 0;
    int32 RenderViews = 0;
    FVector Eye = FVector::ZeroVector;
    FVector Forward = FVector::ZeroVector;
    FVector Up = FVector::ZeroVector;
    float Fov = 0;
    float ViewFov = 0;
    FVector2D Jitter = FVector2D::ZeroVector;
    FIntPoint Target = FIntPoint::ZeroValue;
    FIntPoint ViewSize = FIntPoint::ZeroValue;
    double WorldSeconds = 0;
    double RealSeconds = 0;
    float WorldDelta = 0;
    float RealDelta = 0;
    double PreExposure = 0;
    int32 AA = -1;
    int32 ScreenPercentageMethod = -1;
    bool bCameraCut = false;
    bool bAllowTemporalJitter = false;
    bool bPostProcessing = false;
    bool bAntiAliasing = false;
    bool bTemporalAA = false;
};

class FBreziMotionViewExtension final : public FWorldSceneViewExtension
{
public:
    FBreziMotionViewExtension(const FAutoRegister& AutoRegister, UWorld* World,
        TSharedRef<FBreziMotionFrameState, ESPMode::ThreadSafe> InState)
        : FWorldSceneViewExtension(AutoRegister, World), State(InState) {}
    virtual int32 GetPriority() const override { return -10001; }
    virtual void BeginRenderViewFamily(FSceneViewFamily& Family) override
    {
        check(IsInGameThread());
        FScopeLock Lock(&State->Mutex);
        for (const FSceneView* View : Family.Views)
        {
            if (!View || View->bIsSceneCapture || View->bIsReflectionCapture) continue;
            if (State->WarmupStartCounter != MAX_uint64 && Family.FrameCounter > State->WarmupStartCounter
                && Family.FrameCounter <= State->WarmupStartCounter + RequiredWarmup)
            {
                ++State->WarmupGameViews;
                State->bWarmupGameConsecutive &= Family.FrameCounter == State->WarmupStartCounter + State->WarmupGameViews;
            }
            if (Family.FrameCounter != State->WantedCounter) continue;
            ++State->GameViews;
            State->GameCounter = Family.FrameCounter;
            State->GameFamilyFrame = Family.FrameNumber;
        }
    }
    virtual void PostRenderViewFamily_RenderThread(FRDGBuilder&, FSceneViewFamily& Family) override
    {
        check(IsInRenderingThread());
        FScopeLock Lock(&State->Mutex);
        for (const FSceneView* View : Family.Views)
        {
            if (!View || View->bIsSceneCapture || View->bIsReflectionCapture) continue;
            if (State->WarmupStartCounter != MAX_uint64 && Family.FrameCounter > State->WarmupStartCounter
                && Family.FrameCounter <= State->WarmupStartCounter + RequiredWarmup)
            {
                ++State->WarmupRenderViews;
                State->bWarmupRenderConsecutive &= Family.FrameCounter == State->WarmupStartCounter + State->WarmupRenderViews;
            }
            if (Family.FrameCounter != State->WantedCounter) continue;
            ++State->RenderViews;
            State->RenderCounter = Family.FrameCounter;
            State->RenderFamilyFrame = Family.FrameNumber;
            State->Eye = View->ViewMatrices.GetViewOrigin();
            State->Forward = View->GetViewDirection();
            State->Up = View->GetViewUp();
            State->ViewFov = View->FOV;
            State->Fov = FMath::RadiansToDegrees(2.0 * FMath::Atan(1.0 / View->ViewMatrices.GetViewToClip().M[0][0]));
            State->Jitter = View->ViewMatrices.GetTemporalAAJitter();
            State->Target = Family.RenderTarget ? Family.RenderTarget->GetSizeXY() : FIntPoint::ZeroValue;
            State->ViewSize = View->UnscaledViewRect.Size();
            State->WorldSeconds = Family.Time.GetWorldTimeSeconds();
            State->RealSeconds = Family.Time.GetRealTimeSeconds();
            State->WorldDelta = Family.Time.GetDeltaWorldTimeSeconds();
            State->RealDelta = Family.Time.GetDeltaRealTimeSeconds();
            // Public FSceneView has no PreExposure scalar in UE5.8. UpdatePreExposure
            // writes the same FViewInfo value into this state and the shader uniform.
            // A synchronous screenshot blocks GT before any later engine frame exists.
            State->PreExposure = View->State ? View->State->GetPreExposure() : 0;
            State->AA = static_cast<int32>(View->AntiAliasingMethod);
            State->ScreenPercentageMethod = static_cast<int32>(View->PrimaryScreenPercentageMethod);
            State->bCameraCut = View->bCameraCut;
            State->bAllowTemporalJitter = View->bAllowTemporalJitter;
            State->bPostProcessing = Family.EngineShowFlags.PostProcessing;
            State->bAntiAliasing = Family.EngineShowFlags.AntiAliasing;
            State->bTemporalAA = Family.EngineShowFlags.TemporalAA;
        }
    }
private:
    TSharedRef<FBreziMotionFrameState, ESPMode::ThreadSafe> State;
};

UBreziMotionQA::UBreziMotionQA()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;
    PrimaryComponentTick.bTickEvenWhenPaused = true;
    PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

ABreziPawn* UBreziMotionQA::Pawn() const
{
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    return PC ? Cast<ABreziPawn>(PC->GetPawn()) : nullptr;
}

TSharedRef<FJsonObject> UBreziMotionQA::QualitySettings() const
{
    TSharedRef<FJsonObject> J = MakeShared<FJsonObject>();
    for (const TCHAR* Name : {TEXT("r.AntiAliasingMethod"), TEXT("r.ScreenPercentage"), TEXT("r.SecondaryScreenPercentage.GameViewport"),
        TEXT("r.DynamicRes.OperationMode"), TEXT("r.Lumen.HardwareRayTracing"), TEXT("r.Lumen.Reflections.HardwareRayTracing"),
        TEXT("r.Lumen.HardwareRayTracing.LightingMode"), TEXT("r.Shadow.Virtual.Enable"), TEXT("r.Nanite"),
        TEXT("r.PostProcessAAQuality"), TEXT("r.TemporalAA.Quality"), TEXT("r.SMAA.Quality"), TEXT("r.TSR.History.ScreenPercentage"),
        TEXT("sg.AntiAliasingQuality"), TEXT("sg.GlobalIlluminationQuality"), TEXT("sg.ReflectionQuality"), TEXT("sg.ShadowQuality"),
        TEXT("sg.PostProcessQuality"), TEXT("sg.TextureQuality"), TEXT("sg.EffectsQuality"), TEXT("sg.FoliageQuality")})
    {
        if (const IConsoleVariable* CVar = IConsoleManager::Get().FindConsoleVariable(Name)) J->SetStringField(Name, CVar->GetString());
        else J->SetField(Name, MakeShared<FJsonValueNull>());
    }
    return J;
}

void UBreziMotionQA::BeginPlay()
{
    Super::BeginPlay();
    const TCHAR* CLI = FCommandLine::Get();
    if (!FParse::Param(CLI, TEXT("BreziMotionQA"))) return;
    bEnabled = true;
    StartWallSeconds = FPlatformTime::Seconds();
    OutputDirectory = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("Diagnostics/motion-qa"));
    IFileManager::Get().MakeDirectory(*OutputDirectory, true);
    bClockCaptured = GEngine != nullptr;
    if (GEngine)
    {
        bPriorFixedFrameRate = GEngine->bUseFixedFrameRate;
        PriorFixedFrameRate = GEngine->FixedFrameRate;
        bPriorFixedStep = FApp::UseFixedTimeStep();
        PriorFixedDelta = FApp::GetFixedDeltaTime();
    }
    FString Ignored;
    if (!FParse::Value(CLI, TEXT("BreziMotionAA="), ExpectedAA) || !TArray<int32>{1, 2, 4, 5}.Contains(ExpectedAA)
        || FParse::Param(CLI, TEXT("BreziCapture4K")) || FParse::Param(CLI, TEXT("BreziCaptureUI"))
        || FParse::Param(CLI, TEXT("BreziExitAfterCapture")) || FParse::Param(CLI, TEXT("BreziProfileGPU"))
        || FParse::Value(CLI, TEXT("BreziBenchmarkFrames="), Ignored) || FParse::Value(CLI, TEXT("BreziWalkTraversal="), Ignored)
        || FParse::Param(CLI, TEXT("BreziWalk")) || FParse::Param(CLI, TEXT("BreziWalkAudit"))
        || FParse::Param(CLI, TEXT("BreziNight")) || FParse::Value(CLI, TEXT("BreziView="), Ignored)
        || FParse::Param(CLI, TEXT("BreziReducedMotion")))
    { Finish(TEXT("failed-arguments"), TEXT("Motion QA requires an isolated daytime process with only its explicit AA request.")); return; }
    const IConsoleVariable* ScreenshotDelegate = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenshotDelegate"));
    if (!GEngine || !ScreenshotDelegate || ScreenshotDelegate->GetInt() != 1)
    { Finish(TEXT("failed-prerequisites"), TEXT("Engine or the normal screenshot delegate is unavailable; no cvar override was applied.")); return; }
    FrameState = MakeShared<FBreziMotionFrameState, ESPMode::ThreadSafe>();
    Extension = FSceneViewExtensions::NewExtension<FBreziMotionViewExtension>(GetWorld(), FrameState.ToSharedRef());
    CapturedHandle = UGameViewportClient::OnScreenshotCaptured().AddUObject(this, &UBreziMotionQA::OnScreenshotCaptured);
    ProcessedHandle = FScreenshotRequest::OnScreenshotRequestProcessed().AddUObject(this, &UBreziMotionQA::OnScreenshotProcessed);
    SetComponentTickEnabled(true);
    if (!SaveReport(TEXT("waiting-for-4k-viewport"), FString())) Finish(TEXT("failed-report-write"));
}

void UBreziMotionQA::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction)
{
    Super::TickComponent(DeltaTime, TickType, TickFunction);
    if (!bEnabled || bFinished) return;
    if (FPlatformTime::Seconds() - StartWallSeconds > 600)
    { Finish(TEXT("failed-timeout"), TEXT("Visual sequence exceeded its 600 second wall-time limit.")); return; }
    if (bCapturePending)
    { Finish(TEXT("failed-frame-gap"), TEXT("The preceding regular-frame screenshot was not processed before the next world tick.")); return; }
    ABreziPawn* Character = Pawn();
    const FViewport* Viewport = GEngine && GEngine->GameViewport ? GEngine->GameViewport->Viewport : nullptr;
    if (GetWorld()->IsPaused() || !GetWorld()->GetWorldSettings()
        || GetWorld()->GetWorldSettings()->GetEffectiveTimeDilation() != 1.0f)
    { Finish(TEXT("failed-world-clock"), TEXT("Motion QA requires an unpaused world with unit time dilation; preferences were not changed.")); return; }
    if (!bClockApplied)
    {
        if (!Character || !Character->HasViewpoints() || !Viewport || Viewport->GetSizeXY() != FIntPoint(3840, 2160)) return;
        const FBreziViewpoint* Terrace = Character->GetViewpoints().FindByPredicate([](const FBreziViewpoint& V) { return V.Id == TEXT("terrace"); });
        const FBreziViewpoint* Pool = Character->GetViewpoints().FindByPredicate([](const FBreziViewpoint& V) { return V.Id == TEXT("pool"); });
        if (!Terrace || !Pool) { Finish(TEXT("failed-source-viewpoints")); return; }
        SourceViews = MakeShared<FJsonObject>();
        SourceViews->SetObjectField(TEXT("terrace"), ViewpointJson(*Terrace));
        SourceViews->SetObjectField(TEXT("pool"), ViewpointJson(*Pool));
        InitialQuality = QualitySettings();
        Character->SelectView(TEXT("terrace"), true);
        // Public engine clock, as used by the traversal harness. Do not alter world/material time.
        FApp::SetUseFixedTimeStep(false);
        GEngine->FixedFrameRate = SimulatedHz;
        GEngine->bUseFixedFrameRate = true;
        bClockApplied = true;
        { FScopeLock Lock(&FrameState->Mutex); FrameState->WarmupStartCounter = GFrameCounter; }
        return;
    }
    if (!Character || !Viewport || Viewport->GetSizeXY() != FIntPoint(3840, 2160)
        || !GEngine->bUseFixedFrameRate || GEngine->FixedFrameRate != SimulatedHz
        || !FMath::IsNearlyEqual(DeltaTime, 1.0f / SimulatedHz, 0.000001f)
        || JsonText(QualitySettings()) != JsonText(InitialQuality.ToSharedRef()))
    { Finish(TEXT("failed-fixed-step-or-quality"), TEXT("Actual world delta, viewport or quality settings changed.")); return; }
    if (WarmupFrames < RequiredWarmup) { ++WarmupFrames; return; }
    if (FScreenshotRequest::IsScreenshotRequested() || GIsHighResScreenshot || GIsDumpingMovie)
    { Finish(TEXT("failed-capture-conflict"), TEXT("A foreign screenshot/movie request is active.")); return; }
    RequestFrameCounter = GFrameCounter;
    if (CaptureIndex > 0 && RequestFrameCounter != PreviousRequestCounter + 1)
    { Finish(TEXT("failed-frame-gap"), TEXT("Requested world frames are not consecutive.")); return; }
    RequestWallSeconds = FPlatformTime::Seconds();
    RequestWorldSeconds = GetWorld()->GetTimeSeconds();
    RequestRealSeconds = GetWorld()->GetRealTimeSeconds();
    RequestDeltaSeconds = DeltaTime;
    RequestAppDeltaSeconds = FApp::GetDeltaTime();
    ScreenshotPath = OutputDirectory / FString::Printf(TEXT("frame-%03d.png"), CaptureIndex);
    {
        FScopeLock Lock(&FrameState->Mutex);
        FrameState->WantedCounter = RequestFrameCounter;
        FrameState->GameViews = FrameState->RenderViews = 0;
    }
    bCapturePending = true;
    bCaptureSaved = false;
    FScreenshotRequest::RequestScreenshot(ScreenshotPath, false, false, false, FIntRect(), true);
}

void UBreziMotionQA::OnScreenshotCaptured(int32 Width, int32 Height, const TArray<FColor>& Bitmap)
{
    if (!bEnabled || bFinished || !bCapturePending) return;
    if (GFrameCounter != RequestFrameCounter || Width != 3840 || Height != 2160
        || static_cast<int64>(Width) * Height != Bitmap.Num() || FScreenshotRequest::GetFilename() != ScreenshotPath)
    { Finish(TEXT("failed-capture-identity-or-size")); return; }
    TSharedRef<FJsonObject> J = MakeShared<FJsonObject>();
    FString PairError;
    {
        FScopeLock Lock(&FrameState->Mutex);
        const FBreziMotionFrameState& S = *FrameState;
        if (S.WarmupGameViews != RequiredWarmup || S.WarmupRenderViews != RequiredWarmup
            || !S.bWarmupGameConsecutive || !S.bWarmupRenderConsecutive)
            PairError = TEXT("Warmup did not render exactly 240 consecutive main views at the fixed simulation cadence.");
        else if (S.GameViews != 1 || S.RenderViews != 1 || S.GameCounter != RequestFrameCounter || S.RenderCounter != RequestFrameCounter
            || S.GameFamilyFrame != S.RenderFamilyFrame || (CaptureIndex > 0 && S.RenderFamilyFrame != PreviousFamilyFrame + 1))
            PairError = TEXT("Expected exactly one GT/RT main view for the requested frame and consecutive family identity.");
        else if (S.Target != FIntPoint(3840, 2160) || S.ViewSize != FIntPoint(3840, 2160) || S.AA != ExpectedAA
            || S.Eye.ContainsNaN() || S.Forward.ContainsNaN() || S.Up.ContainsNaN() || S.Jitter.ContainsNaN() || !FMath::IsFinite(S.Fov)
            || !FMath::IsFinite(S.PreExposure) || S.PreExposure <= 0 || !FMath::IsNearlyEqual(S.WorldDelta, 1.0f / SimulatedHz, 0.000001f)
            || FMath::Abs(S.WorldSeconds - RequestWorldSeconds) > 0.00001 || FMath::Abs(S.RealSeconds - RequestRealSeconds) > 0.00001)
            PairError = TEXT("Captured render dimensions, effective AA, exposure, camera or exact-frame world time are invalid.");
        else
        {
            PreviousFamilyFrame = S.RenderFamilyFrame;
            J->SetNumberField(TEXT("gameViewFrameCounter"), S.GameCounter);
            J->SetNumberField(TEXT("renderFrameCounter"), S.RenderCounter);
            J->SetNumberField(TEXT("gameViewFamilyFrameNumber"), S.GameFamilyFrame);
            J->SetNumberField(TEXT("renderFamilyFrameNumber"), S.RenderFamilyFrame);
            J->SetNumberField(TEXT("gameMainViewCount"), S.GameViews);
            J->SetNumberField(TEXT("renderMainViewCount"), S.RenderViews);
            J->SetArrayField(TEXT("eyeCm"), XYZ(S.Eye));
            J->SetArrayField(TEXT("forward"), XYZ(S.Forward));
            J->SetArrayField(TEXT("up"), XYZ(S.Up));
            J->SetNumberField(TEXT("horizontalFovDegrees"), S.Fov);
            J->SetNumberField(TEXT("viewFovDegrees"), S.ViewFov);
            J->SetArrayField(TEXT("projectionJitter"), XY(S.Jitter.X, S.Jitter.Y));
            J->SetArrayField(TEXT("renderTargetPixels"), XY(S.Target.X, S.Target.Y));
            J->SetArrayField(TEXT("unscaledViewPixels"), XY(S.ViewSize.X, S.ViewSize.Y));
            J->SetNumberField(TEXT("worldSeconds"), S.WorldSeconds);
            J->SetNumberField(TEXT("realSeconds"), S.RealSeconds);
            J->SetNumberField(TEXT("worldDeltaSeconds"), S.WorldDelta);
            J->SetNumberField(TEXT("realDeltaSeconds"), S.RealDelta);
            J->SetNumberField(TEXT("linearPreExposure"), S.PreExposure);
            J->SetNumberField(TEXT("exposureEV"), FMath::Log2(1.0 / S.PreExposure));
            J->SetNumberField(TEXT("antiAliasingMethod"), S.AA);
            J->SetNumberField(TEXT("primaryScreenPercentageMethod"), S.ScreenPercentageMethod);
            J->SetBoolField(TEXT("cameraCut"), S.bCameraCut);
            J->SetBoolField(TEXT("allowTemporalJitter"), S.bAllowTemporalJitter);
            J->SetBoolField(TEXT("showFlagPostProcessing"), S.bPostProcessing);
            J->SetBoolField(TEXT("showFlagAntiAliasing"), S.bAntiAliasing);
            J->SetBoolField(TEXT("showFlagTemporalAA"), S.bTemporalAA);
        }
    }
    if (!PairError.IsEmpty()) { Finish(TEXT("failed-render-frame-pairing"), PairError); return; }
    J->SetNumberField(TEXT("index"), CaptureIndex);
    J->SetStringField(TEXT("phase"), CaptureIndex < PreFrames ? TEXT("pre") : CaptureIndex < PreFrames + MotionFrames ? TEXT("motion") : TEXT("tail"));
    J->SetNumberField(TEXT("motionStep"), FMath::Clamp(CaptureIndex - PreFrames + 1, 0, MotionFrames));
    J->SetStringField(TEXT("file"), FPaths::GetCleanFilename(ScreenshotPath));
    J->SetArrayField(TEXT("screenshotPixels"), XY(Width, Height));
    J->SetNumberField(TEXT("requestFrameCounter"), RequestFrameCounter);
    J->SetNumberField(TEXT("captureFrameCounter"), GFrameCounter);
    J->SetNumberField(TEXT("requestWorldSeconds"), RequestWorldSeconds);
    J->SetNumberField(TEXT("requestRealSeconds"), RequestRealSeconds);
    J->SetNumberField(TEXT("requestDeltaSeconds"), RequestDeltaSeconds);
    J->SetNumberField(TEXT("appDeltaSeconds"), RequestAppDeltaSeconds);
    J->SetNumberField(TEXT("requestWallSeconds"), RequestWallSeconds);
    J->SetNumberField(TEXT("captureWallSeconds"), FPlatformTime::Seconds());
    bCaptureSaved = FImageUtils::SaveImageByExtension(*ScreenshotPath, FImageView(Bitmap.GetData(), Width, Height))
        && IFileManager::Get().FileSize(*ScreenshotPath) > 0;
    J->SetNumberField(TEXT("pngWriteCompleteWallSeconds"), FPlatformTime::Seconds());
    J->SetBoolField(TEXT("pngSaved"), bCaptureSaved);
    if (bCaptureSaved) Frames.Add(MakeShared<FJsonValueObject>(J));
}

void UBreziMotionQA::OnScreenshotProcessed()
{
    if (!bEnabled || bFinished || !bCapturePending) return;
    bCapturePending = false;
    if (!bCaptureSaved) { Finish(TEXT("failed-png-write")); return; }
    PreviousRequestCounter = RequestFrameCounter;
    ++CaptureIndex;
    if (CaptureIndex == PreFrames)
    {
        if (!Pawn()) { Finish(TEXT("failed-pawn-lost")); return; }
        // The next pawn tick advances the existing 1.6-second quintic transition once.
        Pawn()->SelectView(TEXT("pool"));
    }
    if (CaptureIndex == TotalFrames) { Finish(TEXT("motion-sequence-captured")); return; }
    if (!SaveReport(TEXT("capturing"), FString())) Finish(TEXT("failed-report-write"));
}

void UBreziMotionQA::RestoreClock()
{
    if (!bClockCaptured) return;
    bClockCaptured = false; // A later EndPlay must not overwrite settings changed after completion.
    if (GEngine)
    {
        GEngine->FixedFrameRate = PriorFixedFrameRate;
        GEngine->bUseFixedFrameRate = bPriorFixedFrameRate;
    }
    FApp::SetFixedDeltaTime(PriorFixedDelta);
    FApp::SetUseFixedTimeStep(bPriorFixedStep);
    bClockRestored = GEngine && GEngine->FixedFrameRate == PriorFixedFrameRate && GEngine->bUseFixedFrameRate == bPriorFixedFrameRate
        && FApp::GetFixedDeltaTime() == PriorFixedDelta && FApp::UseFixedTimeStep() == bPriorFixedStep;
}

bool UBreziMotionQA::SaveReport(const FString& Status, const FString& Reason) const
{
    TSharedRef<FJsonObject> J = MakeShared<FJsonObject>();
    J->SetNumberField(TEXT("schemaVersion"), 1);
    J->SetStringField(TEXT("status"), Status);
    J->SetStringField(TEXT("error"), Reason);
    J->SetStringField(TEXT("path"), TEXT("terrace-to-pool-existing-SelectView-quintic"));
    J->SetNumberField(TEXT("simulationHz"), SimulatedHz);
    J->SetNumberField(TEXT("warmupFrames"), WarmupFrames);
    if (FrameState.IsValid())
    {
        FScopeLock Lock(&FrameState->Mutex);
        J->SetNumberField(TEXT("warmupGameViews"), FrameState->WarmupGameViews);
        J->SetNumberField(TEXT("warmupRenderViews"), FrameState->WarmupRenderViews);
        J->SetBoolField(TEXT("warmupRenderFramesConsecutive"), FrameState->bWarmupGameConsecutive && FrameState->bWarmupRenderConsecutive);
    }
    J->SetNumberField(TEXT("preFrames"), PreFrames);
    J->SetNumberField(TEXT("motionFrames"), MotionFrames);
    J->SetNumberField(TEXT("tailFrames"), TailFrames);
    J->SetNumberField(TEXT("requestedAA"), ExpectedAA);
    J->SetBoolField(TEXT("fixedClockRestored"), bClockRestored);
    TSharedRef<FJsonObject> Clock = MakeShared<FJsonObject>();
    Clock->SetBoolField(TEXT("priorUseFixedFrameRate"), bPriorFixedFrameRate);
    Clock->SetNumberField(TEXT("priorFixedFrameRate"), PriorFixedFrameRate);
    Clock->SetBoolField(TEXT("priorUseFixedTimeStep"), bPriorFixedStep);
    Clock->SetNumberField(TEXT("priorFixedDeltaSeconds"), PriorFixedDelta);
    Clock->SetBoolField(TEXT("currentUseFixedFrameRate"), GEngine && GEngine->bUseFixedFrameRate);
    Clock->SetNumberField(TEXT("currentFixedFrameRate"), GEngine ? GEngine->FixedFrameRate : 0);
    Clock->SetBoolField(TEXT("currentUseFixedTimeStep"), FApp::UseFixedTimeStep());
    Clock->SetNumberField(TEXT("currentFixedDeltaSeconds"), FApp::GetFixedDeltaTime());
    J->SetObjectField(TEXT("clock"), Clock);
    J->SetBoolField(TEXT("qualitySettingsUnchanged"), InitialQuality.IsValid() && JsonText(QualitySettings()) == JsonText(InitialQuality.ToSharedRef()));
    J->SetBoolField(TEXT("worldTimeArtificiallyFrozen"), false);
    J->SetBoolField(TEXT("fpsMeasured"), false);
    J->SetBoolField(TEXT("uiIncluded"), false);
    J->SetBoolField(TEXT("highResolutionScreenshotUsed"), false);
    if (InitialQuality.IsValid()) J->SetObjectField(TEXT("qualitySettings"), InitialQuality);
    if (SourceViews.IsValid()) J->SetObjectField(TEXT("sourceViewpoints"), SourceViews);
    J->SetArrayField(TEXT("frames"), Frames);
    J->SetStringField(TEXT("pairingMethod"), TEXT("Normal no-UI screenshot: request and capture GFrameCounter equal GT and RT Family.FrameCounter; exactly one main view; GT/RT Family.FrameNumber equal. Synchronous viewport readback precedes screenshot delegate. No latest observation fallback."));
    J->SetStringField(TEXT("exposureMethod"), TEXT("Public view-state GetPreExposure in the exact paired RT family; UE5.8 UpdatePreExposure assigns this state scalar from the same FViewInfo scalar used for shader View.PreExposure. No later engine frame can run before the synchronous screenshot callback. This is CPU pre-exposure used by shaders, not a GPU luminance/tonemap-output readback."));
    J->SetStringField(TEXT("cameraMethod"), TEXT("Actual RT view-matrix origin, forward and up; horizontal FOV=2*atan(1/projection.M00). Public View.FOV recorded independently. Jitter is normalized projection offset, not pixels."));
    J->SetStringField(TEXT("limitations"), TEXT("Fixed 30 simulation Hz and synchronous PNG/readback stalls are not FPS evidence. Public unscaled/target dimensions do not expose private internal raster/history dimensions. World/real/material time is recorded, not frozen; exclude animated water, flames and foliage from numerical static-quality metrics. Visual comparison remains required."));
    return FFileHelper::SaveStringToFile(JsonText(J), *(OutputDirectory / TEXT("runtime.json")), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
}

void UBreziMotionQA::Finish(const FString& Status, const FString& Reason)
{
    if (bFinished) return;
    bFinished = true;
    bCapturePending = false;
    if (!ScreenshotPath.IsEmpty() && FScreenshotRequest::IsScreenshotRequested()
        && FScreenshotRequest::GetFilename() == ScreenshotPath)
    {
        FScreenshotRequest::Reset();
        // Normally ProcessScreenShots restores this after its processed delegate.
        // Cancelling before that call must restore the owned request's saved state too.
        GAreScreenMessagesEnabled = GScreenMessagesRestoreState;
    }
    UGameViewportClient::OnScreenshotCaptured().Remove(CapturedHandle);
    FScreenshotRequest::OnScreenshotRequestProcessed().Remove(ProcessedHandle);
    if (FrameState.IsValid()) { FScopeLock Lock(&FrameState->Mutex); FrameState->WantedCounter = MAX_uint64; }
    RestoreClock();
    SetComponentTickEnabled(false);
    const bool bSaved = SaveReport(Status, Reason);
    UE_LOG(LogTemp, Display, TEXT("BreziMotionQA status=%s frames=%d restored=%d saved=%d reason=%s"), *Status, Frames.Num(), bClockRestored, bSaved, *Reason);
    if (FParse::Param(FCommandLine::Get(), TEXT("BreziMotionExit"))) FPlatformMisc::RequestExit(false);
}

void UBreziMotionQA::EndPlay(const EEndPlayReason::Type Reason)
{
    if (bEnabled && !bFinished) Finish(TEXT("interrupted-before-completion"));
    RestoreClock();
    Extension.Reset();
    FrameState.Reset();
    Super::EndPlay(Reason);
}
