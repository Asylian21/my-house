#include "BreziFlameStudy.h"
#include "BreziPawn.h"
#include "Components/StaticMeshComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "StaticMeshResources.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/SecureHash.h"
#include "HAL/PlatformProcess.h"
#include "RenderingThread.h"
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
constexpr int32 FlameHz = 30;
constexpr int32 FlameWarmup = 240;
constexpr double FlameDayPreExposure = 0.0010780160082504153;
constexpr double FlameNightPreExposure = 16.0;
constexpr float StudySeconds = 2.0f;
const FName ScaleParameter(TEXT("BreziFlameEmissionScale"));
const FName TimeParameter(TEXT("BreziFlameStudyTimeSeconds"));
TArray<TSharedPtr<FJsonValue>> FlameXYZ(const FVector& V)
{
    return {MakeShared<FJsonValueNumber>(V.X), MakeShared<FJsonValueNumber>(V.Y), MakeShared<FJsonValueNumber>(V.Z)};
}
TArray<TSharedPtr<FJsonValue>> FlameXY(double X, double Y)
{
    return {MakeShared<FJsonValueNumber>(X), MakeShared<FJsonValueNumber>(Y)};
}
TSharedRef<FJsonObject> FlameViewpointJson(const FBreziViewpoint& View)
{
    TSharedRef<FJsonObject> J = MakeShared<FJsonObject>();
    J->SetStringField(TEXT("id"), View.Id);
    J->SetArrayField(TEXT("eyeCm"), FlameXYZ(View.EyeCm));
    J->SetArrayField(TEXT("targetCm"), FlameXYZ(View.TargetCm));
    J->SetNumberField(TEXT("horizontalFovDegrees"), View.HorizontalFovDegrees);
    return J;
}
FString FlameJsonText(const TSharedRef<FJsonObject>& Value)
{
    FString Text;
    FJsonSerializer::Serialize(Value, TJsonWriterFactory<>::Create(&Text));
    return Text;
}
}

// One armed capture only. No latest-frame fallback and no retained renderer resource/UObject.
struct FBreziFlameFrameState
{
    FCriticalSection Mutex;
    bool bActive = true;
    bool bManualControl = false;
    float ManualBias = 0;
    bool bManual = false;
    bool bPhysicalExposure = true;
    bool bBiasCurve = true;
    bool bLocalExposure = true;
    bool bEyeAdaptation = false;
    float CapturedBias = 0;
    FVector Tint = FVector::ZeroVector;
    const FSceneInterface* GameSceneToken = nullptr;
    const FSceneInterface* RenderSceneToken = nullptr;
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

class FBreziFlameViewExtension final : public FWorldSceneViewExtension
{
public:
    FBreziFlameViewExtension(const FAutoRegister& AutoRegister, UWorld* World,
        TSharedRef<FBreziFlameFrameState, ESPMode::ThreadSafe> InState)
        : FWorldSceneViewExtension(AutoRegister, World), State(InState) {}
    virtual int32 GetPriority() const override { return -10002; }
    void Stop() { FScopeLock Lock(&State->Mutex); State->bActive = false; State->WantedCounter = MAX_uint64; }
    virtual void SetupView(FSceneViewFamily& Family, FSceneView& View) override
    {
        check(IsInGameThread());
        FScopeLock Lock(&State->Mutex);
        if (!State->bActive || !State->bManualControl || View.bIsSceneCapture || View.bIsReflectionCapture) return;
        // LocalPlayer calls SetupView after EndFinalPostprocessSettings. These are
        // per-view values, never saved camera, volume, material or global cvars.
        auto& P = View.FinalPostProcessSettings;
        P.AutoExposureMethod = AEM_Manual;
        P.AutoExposureApplyPhysicalCameraExposure = false;
        P.AutoExposureBias = State->ManualBias;
        P.AutoExposureBiasCurve = nullptr;
        P.SceneColorTint = FLinearColor::White;
        Family.EngineShowFlags.SetLocalExposure(false);
    }
    virtual void BeginRenderViewFamily(FSceneViewFamily& Family) override
    {
        check(IsInGameThread());
        FScopeLock Lock(&State->Mutex);
        if (!State->bActive) return;
        for (const FSceneView* View : Family.Views)
        {
            if (!View || View->bIsSceneCapture || View->bIsReflectionCapture) continue;
            if (State->WarmupStartCounter != MAX_uint64 && Family.FrameCounter > State->WarmupStartCounter
                && Family.FrameCounter <= State->WarmupStartCounter + FlameWarmup)
            {
                ++State->WarmupGameViews;
                State->bWarmupGameConsecutive &= Family.FrameCounter == State->WarmupStartCounter + State->WarmupGameViews;
            }
            if (Family.FrameCounter != State->WantedCounter) continue;
            ++State->GameViews;
            State->GameCounter = Family.FrameCounter;
            State->GameFamilyFrame = Family.FrameNumber;
            State->GameSceneToken = Family.Scene;
        }
    }
    virtual void PostRenderViewFamily_RenderThread(FRDGBuilder&, FSceneViewFamily& Family) override
    {
        check(IsInRenderingThread());
        FScopeLock Lock(&State->Mutex);
        if (!State->bActive) return;
        for (const FSceneView* View : Family.Views)
        {
            if (!View || View->bIsSceneCapture || View->bIsReflectionCapture) continue;
            if (State->WarmupStartCounter != MAX_uint64 && Family.FrameCounter > State->WarmupStartCounter
                && Family.FrameCounter <= State->WarmupStartCounter + FlameWarmup)
            {
                ++State->WarmupRenderViews;
                State->bWarmupRenderConsecutive &= Family.FrameCounter == State->WarmupStartCounter + State->WarmupRenderViews;
            }
            if (Family.FrameCounter != State->WantedCounter) continue;
            ++State->RenderViews;
            State->RenderCounter = Family.FrameCounter;
            State->RenderFamilyFrame = Family.FrameNumber;
            State->RenderSceneToken = Family.Scene;
            const auto& P = View->FinalPostProcessSettings;
            State->bManual = P.AutoExposureMethod == AEM_Manual;
            State->bPhysicalExposure = P.AutoExposureApplyPhysicalCameraExposure;
            State->bBiasCurve = P.AutoExposureBiasCurve != nullptr;
            State->CapturedBias = P.AutoExposureBias;
            State->Tint = FVector(P.SceneColorTint.R, P.SceneColorTint.G, P.SceneColorTint.B);
            State->bLocalExposure = Family.EngineShowFlags.LocalExposure;
            State->bEyeAdaptation = Family.EngineShowFlags.EyeAdaptation;
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
    TSharedRef<FBreziFlameFrameState, ESPMode::ThreadSafe> State;
};

UBreziFlameStudy::UBreziFlameStudy()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;
    PrimaryComponentTick.bTickEvenWhenPaused = true;
    PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

ABreziPawn* UBreziFlameStudy::Pawn() const
{
    const APlayerController* PC = Cast<APlayerController>(GetOwner());
    return PC ? Cast<ABreziPawn>(PC->GetPawn()) : nullptr;
}

TSharedRef<FJsonObject> UBreziFlameStudy::QualitySettings() const
{
    TSharedRef<FJsonObject> J = MakeShared<FJsonObject>();
    for (const TCHAR* Name : {TEXT("r.AntiAliasingMethod"), TEXT("r.ScreenPercentage"), TEXT("r.SecondaryScreenPercentage.GameViewport"),
        TEXT("r.DynamicRes.OperationMode"), TEXT("r.Lumen.HardwareRayTracing"), TEXT("r.Lumen.Reflections.HardwareRayTracing"),
        TEXT("r.Lumen.HardwareRayTracing.LightingMode"), TEXT("r.Shadow.Virtual.Enable"), TEXT("r.Nanite"),
        TEXT("r.TemporalAA.Quality"), TEXT("r.SMAA.Quality"), TEXT("r.TSR.History.ScreenPercentage"),
        TEXT("sg.AntiAliasingQuality"), TEXT("sg.GlobalIlluminationQuality"), TEXT("sg.ReflectionQuality"), TEXT("sg.ShadowQuality"),
        TEXT("sg.PostProcessQuality"), TEXT("sg.TextureQuality"), TEXT("sg.EffectsQuality"), TEXT("sg.FoliageQuality"), TEXT("r.EyeAdaptation.LensAttenuation"), TEXT("r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange"),
        TEXT("r.EyeAdaptation.PreExposureOverride"), TEXT("r.EyeAdaptationQuality"), TEXT("r.TranslucentSortPolicy") })
    {
        if (const IConsoleVariable* CVar = IConsoleManager::Get().FindConsoleVariable(Name)) J->SetStringField(Name, CVar->GetString());
        else J->SetField(Name, MakeShared<FJsonValueNull>());
    }
    return J;
}

void UBreziFlameStudy::BeginPlay()
{
    Super::BeginPlay();
    const TCHAR* CLI = FCommandLine::Get();
    FString ScaleText;
    if (!FParse::Value(CLI, TEXT("BreziFlameStudyScale="), ScaleText))
    {
        FString OrphanShape;
        if (FParse::Value(CLI,TEXT("BreziFlameShape="),OrphanShape) || FParse::Param(CLI,TEXT("BreziFlameShape")))
        {
            bEnabled=true; StartWallSeconds=FPlatformTime::Seconds();
            OutputDirectory=FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()/TEXT("Diagnostics/flame-study"));
            IFileManager::Get().MakeDirectory(*OutputDirectory,true);
            Finish(TEXT("failed-shape-arguments"),TEXT("Shape diagnostics require an explicit scale-one study and contract."));
        }
        return;
    }
    bEnabled = true;
    StartWallSeconds = FPlatformTime::Seconds();
    OutputDirectory = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("Diagnostics/flame-study"));
    IFileManager::Get().MakeDirectory(*OutputDirectory, true);
    FString Path, Ignored;
    if (!TArray<FString>{TEXT("1"),TEXT("4"),TEXT("16"),TEXT("64")}.Contains(ScaleText)
        || !FParse::Value(CLI, TEXT("BreziFlameStudyContract="), Path)
        || FParse::Param(CLI, TEXT("BreziMotionQA")) || FParse::Param(CLI,TEXT("BreziCapture4K"))
        || FParse::Param(CLI,TEXT("BreziCaptureUI")) || FParse::Param(CLI,TEXT("BreziProfileGPU"))
        || FParse::Param(CLI,TEXT("BreziExitAfterCapture")) || FParse::Param(CLI,TEXT("BreziWalk"))
        || FParse::Param(CLI,TEXT("BreziWalkAudit"))
        || FParse::Param(CLI,TEXT("BreziSolarVisibilityProbe")) || FParse::Param(CLI,TEXT("BreziCausticsProbe"))
        || FParse::Param(CLI,TEXT("BreziAXInitStress")) || FParse::Param(CLI,TEXT("BreziSkipNativeAccessibility"))
        || FParse::Value(CLI,TEXT("BreziWalkTraversal="),Ignored) || FParse::Value(CLI,TEXT("BreziBenchmarkFrames="),Ignored)
        || FParse::Value(CLI,TEXT("BreziView="),Ignored) || FParse::Param(CLI,TEXT("BreziReducedMotion")))
    { Finish(TEXT("failed-arguments")); return; }
    // Shape changes only pose/schedule; recipe registration below is common to all modes.
    int32 ShapeFlags=0, ScaleFlags=0, ContractFlags=0;
    const TCHAR* Cursor=CLI; FString Token;
    while (FParse::Token(Cursor,Token,false))
    {
        if (Token.StartsWith(TEXT("-BreziFlameShape"),ESearchCase::IgnoreCase))
        {
            ++ShapeFlags;
            if (Token==TEXT("-BreziFlameShape=stills")) ShapeMode=TEXT("stills");
            else if (Token==TEXT("-BreziFlameShape=sequence")) ShapeMode=TEXT("sequence");
            else { Finish(TEXT("failed-shape-arguments")); return; }
        }
        if (Token.StartsWith(TEXT("-BreziFlameStudyScale="),ESearchCase::IgnoreCase)) ++ScaleFlags;
        if (Token.StartsWith(TEXT("-BreziFlameStudyContract="),ESearchCase::IgnoreCase)) ++ContractFlags;
    }
    if (ShapeFlags>1 || (ShapeFlags==1 && (ScaleText!=TEXT("1") || ScaleFlags!=1 || ContractFlags!=1)))
    { Finish(TEXT("failed-shape-arguments")); return; }
    EmissionScale = FCString::Atof(*ScaleText);
    if (!ReadContract(Path) || FParse::Param(CLI,TEXT("BreziNight"))!=(LightingState==TEXT("night")))
    { Finish(TEXT("failed-contract")); return; }
    const auto CV = [](const TCHAR* Name) { return IConsoleManager::Get().FindConsoleVariable(Name); };
    if (!GEngine) { Finish(TEXT("failed-prerequisites"), TEXT("GEngine is absent.")); return; }
    for (const TCHAR* Name : { TEXT("r.ScreenshotDelegate"), TEXT("r.EyeAdaptation.PreExposureOverride"),
        TEXT("r.EyeAdaptationQuality"), TEXT("r.EyeAdaptation.LensAttenuation"),
        TEXT("r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange") })
    {
        if (!CV(Name)) { Finish(TEXT("failed-prerequisites"), FString::Printf(TEXT("Required console variable is absent: %s"), Name)); return; }
    }
    if (CV(TEXT("r.ScreenshotDelegate"))->GetInt() != 1)
    { Finish(TEXT("failed-prerequisites"), TEXT("r.ScreenshotDelegate must equal 1.")); return; }
    if (CV(TEXT("r.EyeAdaptation.PreExposureOverride"))->GetFloat() != 0)
    { Finish(TEXT("failed-prerequisites"), TEXT("r.EyeAdaptation.PreExposureOverride must equal 0.")); return; }
    if (CV(TEXT("r.EyeAdaptationQuality"))->GetInt() <= 0)
    { Finish(TEXT("failed-prerequisites"), TEXT("r.EyeAdaptationQuality must be positive.")); return; }
    // UE 5.8 computes pre-exposure in FViewInfo::UpdatePreExposure without the
    // removed r.UsePreExposure switch. The paired RT ViewState getter below
    // proves the actual scalar and rejects an unexpected/default value.
    bClockCaptured = true;
    bPriorFixedFrameRate = GEngine->bUseFixedFrameRate;
    PriorFixedFrameRate = GEngine->FixedFrameRate;
    bPriorFixedStep = FApp::UseFixedTimeStep();
    PriorFixedDelta = FApp::GetFixedDeltaTime();
    FrameState = MakeShared<FBreziFlameFrameState, ESPMode::ThreadSafe>();
    const double LuminanceMax = CV(TEXT("r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange"))->GetInt() != 0
        ? 0.78 / FMath::Max(CV(TEXT("r.EyeAdaptation.LensAttenuation"))->GetFloat(), 0.01f) : 1.0;
    FrameState->ManualBias = FMath::Log2(TargetPreExposure * LuminanceMax);
    CapturedHandle = UGameViewportClient::OnScreenshotCaptured().AddUObject(this, &UBreziFlameStudy::OnScreenshotCaptured);
    ProcessedHandle = FScreenshotRequest::OnScreenshotRequestProcessed().AddUObject(this, &UBreziFlameStudy::OnScreenshotProcessed);
    SetComponentTickEnabled(true);
    if (!SaveReport(TEXT("waiting-for-4k-viewport"), FString())) Finish(TEXT("failed-report-write"));
}

void UBreziFlameStudy::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction)
{
    Super::TickComponent(DeltaTime, TickType, TickFunction);
    if (!bEnabled || bFinished) return;
    if (FPlatformTime::Seconds() - StartWallSeconds > 330)
    { Finish(TEXT("failed-timeout"), TEXT("Visual sequence exceeded its 330 second wall-time limit.")); return; }
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
        const FBreziViewpoint* Interior = Character->GetViewpoints().FindByPredicate([](const FBreziViewpoint& V) { return V.Id == TEXT("interior"); });
        if (!Interior || !Interior->EyeCm.Equals(SourceInteriorEye,0.001) || !Interior->TargetCm.Equals(SourceInteriorTarget,0.001)
            || !FMath::IsNearlyEqual(Interior->HorizontalFovDegrees,ExpectedFov,0.0001f))
        { Finish(TEXT("failed-source-viewpoint")); return; }
        const auto Walking = Character->GetWalkingDiagnostics();
        if (Walking->GetStringField(TEXT("sceneSha256")) != SceneSha || Walking->GetStringField(TEXT("sourceObjSha256")) != ObjSha
            || !Walking->GetBoolField(TEXT("contractLoaded"))) { Finish(TEXT("failed-source-world")); return; }
        SourceViews = MakeShared<FJsonObject>();
        SourceViews->SetObjectField(TEXT("interior"),FlameViewpointJson(*Interior));
        InitialQuality = QualitySettings();
        ExpectedAA = FCString::Atoi(*InitialQuality->GetStringField(TEXT("r.AntiAliasingMethod")));
        if (!TArray<int32>{1,2,4,5}.Contains(ExpectedAA) || !BindFlame()) { Finish(TEXT("failed-active-flame-guard")); return; }
        if (Character->IsWalkingMode()) { Finish(TEXT("failed-preexisting-walking-mode")); return; }
        PriorViewId=Character->GetActiveViewId();
        Character->SelectView(TEXT("interior"), true);
        bStudyViewSelected=true;
        if (IsShapeStudy() && ShapePose==TEXT("oblique")
            && !Character->PrepareTraversalAuditView(ExpectedEye,(ExpectedTarget-ExpectedEye).GetSafeNormal()))
        { Finish(TEXT("failed-shape-audit-view")); return; }
        if (!Character->ToggleMovementMode() || !Character->IsWalkingMode()) { Finish(TEXT("failed-standing-entry")); return; }
        Extension = FSceneViewExtensions::NewExtension<FBreziFlameViewExtension>(GetWorld(), FrameState.ToSharedRef());
        // Public engine clock, as used by the traversal harness. Do not alter world/material time.
        FApp::SetUseFixedTimeStep(false);
        GEngine->FixedFrameRate = FlameHz;
        GEngine->bUseFixedFrameRate = true;
        bClockApplied = true;
        { FScopeLock Lock(&FrameState->Mutex); FrameState->WarmupStartCounter = GFrameCounter; }
        return;
    }
    if (!Character || !Viewport || Viewport->GetSizeXY() != FIntPoint(3840, 2160)
        || !GEngine->bUseFixedFrameRate || GEngine->FixedFrameRate != FlameHz
        || !FMath::IsNearlyEqual(DeltaTime, 1.0f / FlameHz, 0.000001f)
        || FlameJsonText(QualitySettings()) != FlameJsonText(InitialQuality.ToSharedRef()))
    { Finish(TEXT("failed-fixed-step-or-quality"), TEXT("Actual world delta, viewport or quality settings changed.")); return; }
    // Enqueue the next indexed scalar before this world's view is drawn. No wall-clock phase.
    if (StudyMaterial && ShapeMode==TEXT("sequence") && CaptureIndex>1)
        StudyMaterial->SetScalarParameterValue(TimeParameter,ExpectedStudySeconds());
    TSharedPtr<FJsonObject> BoundObservation;
    const bool bBoundValid = CheckBoundState(&BoundObservation);
    const bool bWalking = Character->IsWalkingMode();
    if (!bBoundValid || !bWalking)
    {
        const FString Predicate = !bBoundValid ? BoundObservation->GetStringField(TEXT("firstFailedPredicate")) : TEXT("walking-mode-inactive");
        CaptureFailureObservation(Predicate, BoundObservation, bWalking);
        Finish(!bBoundValid ? TEXT("failed-material-or-compositing-drift") : TEXT("failed-walking-mode-drift"), Predicate);
        return;
    }
    const auto Standing=Character->GetWalkingDiagnostics();
    if (!Standing->GetBoolField(TEXT("worldContractValidated")) || Standing->GetNumberField(TEXT("unmeasuredOrAirborneEyeSamples"))!=0
        || Standing->GetStringField(TEXT("currentSupportObjectId")).IsEmpty()) { Finish(TEXT("failed-standing-support")); return; }
    if (IsShapeStudy() && (!ShapeSupportIds.Contains(Standing->GetStringField(TEXT("currentSupportObjectId")))
        || !ShapeSupportIds.Contains(Standing->GetStringField(TEXT("entrySupportObjectId")))
        || Standing->GetNumberField(TEXT("maxEyeHeightErrorCm"))>0.02))
    { Finish(TEXT("failed-shape-standing-support")); return; }
    if (WarmupFrames < FlameWarmup) { ++WarmupFrames; return; }
    if (FScreenshotRequest::IsScreenshotRequested() || GIsHighResScreenshot || GIsDumpingMovie)
    { Finish(TEXT("failed-capture-conflict"), TEXT("A foreign screenshot/movie request is active.")); return; }
    RequestFrameCounter = GFrameCounter;
    if (CaptureIndex > 0 && RequestFrameCounter != PreviousRequestCounter + RequiredCaptureGap())
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

void UBreziFlameStudy::OnScreenshotCaptured(int32 Width, int32 Height, const TArray<FColor>& Bitmap)
{
    if (!bEnabled || bFinished || !bCapturePending) return;
    if (GFrameCounter != RequestFrameCounter || Width != 3840 || Height != 2160
        || static_cast<int64>(Width) * Height != Bitmap.Num() || FScreenshotRequest::GetFilename() != ScreenshotPath)
    { Finish(TEXT("failed-capture-identity-or-size")); return; }
    TSharedRef<FJsonObject> J = MakeShared<FJsonObject>();
    FString PairError;
    {
        FScopeLock Lock(&FrameState->Mutex);
        const FBreziFlameFrameState& S = *FrameState;
        if (S.WarmupGameViews != FlameWarmup || S.WarmupRenderViews != FlameWarmup
            || !S.bWarmupGameConsecutive || !S.bWarmupRenderConsecutive)
            PairError = TEXT("Warmup did not render exactly 240 consecutive main views at the fixed simulation cadence.");
        else if (S.GameViews != 1 || S.RenderViews != 1 || S.GameCounter != RequestFrameCounter || S.RenderCounter != RequestFrameCounter
            || S.GameFamilyFrame != S.RenderFamilyFrame || S.GameSceneToken != S.RenderSceneToken || !S.GameSceneToken || (CaptureIndex > 0 && S.RenderFamilyFrame != PreviousFamilyFrame + RequiredCaptureGap()))
            PairError = TEXT("Expected exactly one GT/RT main view for the requested frame and consecutive family identity.");
        else if (S.Target != FIntPoint(3840, 2160) || S.ViewSize != FIntPoint(3840, 2160) || S.AA != ExpectedAA
            || S.Eye.ContainsNaN() || S.Forward.ContainsNaN() || S.Up.ContainsNaN() || S.Jitter.ContainsNaN() || !FMath::IsFinite(S.Fov)
            || !FMath::IsFinite(S.PreExposure) || S.PreExposure<=0
            || (CaptureIndex>=1 && (FMath::Abs(S.PreExposure / TargetPreExposure - 1) > 0.0001
                || !S.bManual || S.bPhysicalExposure || S.bBiasCurve || S.bLocalExposure || !S.bEyeAdaptation
                || !S.Tint.Equals(FVector::OneVector,0.000001) || FMath::Abs(S.CapturedBias-S.ManualBias)>0.000001))
            || (CaptureIndex==0 && S.bManual)
            || !S.Eye.Equals(ExpectedEye,0.01) || !S.Forward.Equals((ExpectedTarget-ExpectedEye).GetSafeNormal(),0.000001)
            || FMath::Abs(S.Fov-ExpectedFov)>0.0001 || S.bCameraCut || !FMath::IsNearlyEqual(S.WorldDelta, 1.0f / FlameHz, 0.000001f)
            || FMath::Abs(S.WorldSeconds - RequestWorldSeconds) > 0.00001 || FMath::Abs(S.RealSeconds - RequestRealSeconds) > 0.00001)
            PairError = TEXT("Captured render dimensions, effective AA, exposure, camera or exact-frame world time are invalid.");
        else
        {
            PreviousFamilyFrame = S.RenderFamilyFrame;
            J->SetNumberField(TEXT("warmupGameViews"),S.WarmupGameViews);
            J->SetNumberField(TEXT("warmupRenderViews"),S.WarmupRenderViews);
            J->SetBoolField(TEXT("warmupConsecutive"),S.bWarmupGameConsecutive && S.bWarmupRenderConsecutive);
            J->SetBoolField(TEXT("sceneIdentityPaired"), S.GameSceneToken == S.RenderSceneToken && S.GameSceneToken != nullptr);
            J->SetBoolField(TEXT("manualExposure"), S.bManual);
            J->SetBoolField(TEXT("physicalCameraExposure"), S.bPhysicalExposure);
            J->SetBoolField(TEXT("exposureBiasCurvePresent"), S.bBiasCurve);
            J->SetBoolField(TEXT("localExposure"), S.bLocalExposure);
            J->SetBoolField(TEXT("eyeAdaptationShowFlag"), S.bEyeAdaptation);
            J->SetNumberField(TEXT("manualExposureBias"), S.CapturedBias);
            J->SetArrayField(TEXT("sceneColorTint"), FlameXYZ(S.Tint));
            J->SetNumberField(TEXT("gameViewFrameCounter"), S.GameCounter);
            J->SetNumberField(TEXT("renderFrameCounter"), S.RenderCounter);
            J->SetNumberField(TEXT("gameViewFamilyFrameNumber"), S.GameFamilyFrame);
            J->SetNumberField(TEXT("renderFamilyFrameNumber"), S.RenderFamilyFrame);
            J->SetNumberField(TEXT("gameMainViewCount"), S.GameViews);
            J->SetNumberField(TEXT("renderMainViewCount"), S.RenderViews);
            J->SetArrayField(TEXT("eyeCm"), FlameXYZ(S.Eye));
            J->SetArrayField(TEXT("forward"), FlameXYZ(S.Forward));
            J->SetArrayField(TEXT("up"), FlameXYZ(S.Up));
            J->SetNumberField(TEXT("horizontalFovDegrees"), S.Fov);
            J->SetNumberField(TEXT("viewFovDegrees"), S.ViewFov);
            J->SetArrayField(TEXT("projectionJitter"), FlameXY(S.Jitter.X, S.Jitter.Y));
            J->SetArrayField(TEXT("renderTargetPixels"), FlameXY(S.Target.X, S.Target.Y));
            J->SetArrayField(TEXT("unscaledViewPixels"), FlameXY(S.ViewSize.X, S.ViewSize.Y));
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
    float ActualScale=0, ActualTime=0;
    const UMaterialInterface* CapturedMaterial=FlameComponent?FlameComponent->GetMaterial(0):nullptr;
    TSharedPtr<FJsonObject> BoundObservation;
    const bool bBoundValid = CheckBoundState(&BoundObservation);
    const bool bCaptureScaleRead = CapturedMaterial && CapturedMaterial->GetScalarParameterValue(FHashedMaterialParameterInfo(ScaleParameter),ActualScale);
    const bool bCaptureTimeRead = CapturedMaterial && CapturedMaterial->GetScalarParameterValue(FHashedMaterialParameterInfo(TimeParameter),ActualTime);
    if (!bBoundValid || !bCaptureScaleRead || !bCaptureTimeRead)
    {
        const FString Predicate = !bBoundValid ? BoundObservation->GetStringField(TEXT("firstFailedPredicate"))
            : !bCaptureScaleRead ? TEXT("capture-emission-scale-getter-failed") : TEXT("capture-study-time-getter-failed");
        BoundObservation->SetBoolField(TEXT("captureScaleGetterSucceeded"), bCaptureScaleRead);
        BoundObservation->SetBoolField(TEXT("captureTimeGetterSucceeded"), bCaptureTimeRead);
        CaptureFailureObservation(Predicate, BoundObservation, Pawn() && Pawn()->IsWalkingMode());
        Finish(TEXT("failed-capture-material-drift"), Predicate);
        return;
    }
    J->SetStringField(TEXT("captureKind"),CaptureIndex==0?TEXT("production-baseline"):(CaptureIndex==1?TEXT("controlled-study"):TEXT("controlled-advancing-time")));
    J->SetBoolField(TEXT("transientMaterialPointerBound"),StudyMaterial && FlameComponent->GetMaterial(0)==StudyMaterial.Get());
    J->SetObjectField(TEXT("standing"),Pawn()->GetWalkingDiagnostics());
    J->SetNumberField(TEXT("emissionScale"),ActualScale);
    J->SetNumberField(TEXT("studyTimeSeconds"),ActualTime);
    J->SetObjectField(TEXT("flameComponent"),ComponentState(FlameComponent));
    J->SetObjectField(TEXT("glassComponent"),ComponentState(GlassComponent));
    J->SetObjectField(TEXT("sun"),SunState());
    J->SetStringField(TEXT("file"), FPaths::GetCleanFilename(ScreenshotPath));
    J->SetArrayField(TEXT("screenshotPixels"), FlameXY(Width, Height));
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

void UBreziFlameStudy::OnScreenshotProcessed()
{
    if (!bEnabled || bFinished || !bCapturePending) return;
    bCapturePending = false;
    if (!bCaptureSaved) { Finish(TEXT("failed-png-write")); return; }
    PreviousRequestCounter = RequestFrameCounter;
    ++CaptureIndex;
    if (CaptureIndex == RequiredCaptureFrames())
    { Finish(IsShapeStudy()?TEXT("flame-shape-captured"):TEXT("flame-study-captured")); return; }
    if (CaptureIndex>1)
    {
        // Retain MID, exposure and established history. Next ordinary world tick arms capture.
        { FScopeLock Lock(&FrameState->Mutex); FrameState->WantedCounter=MAX_uint64; }
        if (!SaveReport(TEXT("capturing"),FString())) Finish(TEXT("failed-report-write"));
        return;
    }
    if (!ApplyStudyMaterial()) { Finish(TEXT("failed-transient-material-setup")); return; }
    { FScopeLock Lock(&FrameState->Mutex);
      FrameState->bManualControl=true;
      FrameState->WarmupStartCounter=GFrameCounter;
      FrameState->WarmupGameViews=FrameState->WarmupRenderViews=0;
      FrameState->bWarmupGameConsecutive=FrameState->bWarmupRenderConsecutive=true;
      FrameState->WantedCounter=MAX_uint64; }
    WarmupFrames=0;
    if (!SaveReport(TEXT("capturing"), FString())) Finish(TEXT("failed-report-write"));
}

void UBreziFlameStudy::RestoreClock()
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

bool UBreziFlameStudy::SaveReport(const FString& Status, const FString& Reason) const
{
    TSharedRef<FJsonObject> J = MakeShared<FJsonObject>();
    J->SetNumberField(TEXT("schemaVersion"), IsShapeStudy()?2:1);
    J->SetStringField(TEXT("status"), Status);
    J->SetStringField(TEXT("error"), Reason);
    J->SetStringField(TEXT("path"), TEXT("interior-existing-SelectView-fixed-flame-phase"));
    J->SetNumberField(TEXT("simulationHz"), FlameHz);
    J->SetNumberField(TEXT("warmupFrames"), WarmupFrames);
    if (FrameState.IsValid())
    {
        FScopeLock Lock(&FrameState->Mutex);
        J->SetNumberField(TEXT("warmupGameViews"), FrameState->WarmupGameViews);
        J->SetNumberField(TEXT("warmupRenderViews"), FrameState->WarmupRenderViews);
        J->SetBoolField(TEXT("warmupRenderFramesConsecutive"), FrameState->bWarmupGameConsecutive && FrameState->bWarmupRenderConsecutive);
    }
    J->SetNumberField(TEXT("nativeProcessId"),FPlatformProcess::GetCurrentProcessId());
    J->SetNumberField(TEXT("emissionScale"),EmissionScale);
    J->SetNumberField(TEXT("studyTimeSeconds"),StudySeconds);
    J->SetNumberField(TEXT("targetPreExposure"),TargetPreExposure);
    J->SetStringField(TEXT("lightingState"),LightingState);
    if (IsShapeStudy())
    {
        J->SetStringField(TEXT("shapeMode"),ShapeMode);
        J->SetStringField(TEXT("poseId"),ShapePose);
        J->SetStringField(TEXT("shapePhaseSource"),TEXT("indexed-MID-scalar-at-30-simulation-Hz"));
        J->SetBoolField(TEXT("nativeStoveAxisVerified"),bNativeStoveAxisVerified);
        J->SetArrayField(TEXT("sourceStoveAxisNativeCm"),FlameXYZ(NativeStoveAxis));
        J->SetBoolField(TEXT("realTimePlaybackVerified"),false);
        J->SetNumberField(TEXT("expectedCaptureFrames"),RequiredCaptureFrames());
    }
    J->SetBoolField(TEXT("cameraModeAndPriorViewRestored"),bCameraRestored);
    J->SetStringField(TEXT("contractSha1"),ContractSha1);
    J->SetStringField(TEXT("sceneSha256"),SceneSha);
    J->SetStringField(TEXT("sourceObjSha256"),ObjSha);
    J->SetBoolField(TEXT("originalMaterialPointerRestored"),bMaterialRestored);
    J->SetBoolField(TEXT("originalComponentStatesRestored"),bInvariantStateRestored);
    J->SetBoolField(TEXT("viewExtensionStoppedAndFlushed"),bExtensionStopped);
    J->SetBoolField(TEXT("physicalBrightnessCalibrated"),false);
    float DefaultScale=0,DefaultTime=0;
    const bool bDefaultsRead=OriginalMaterial && OriginalMaterial->GetScalarParameterValue(FHashedMaterialParameterInfo(ScaleParameter),DefaultScale)
        && OriginalMaterial->GetScalarParameterValue(FHashedMaterialParameterInfo(TimeParameter),DefaultTime);
    J->SetBoolField(TEXT("parentScalarDefaultsRead"),bDefaultsRead);
    J->SetNumberField(TEXT("parentDefaultEmissionScale"),DefaultScale);
    J->SetNumberField(TEXT("parentDefaultStudyTimeSeconds"),DefaultTime);
    if (InitialFlame) J->SetObjectField(TEXT("initialFlameComponent"),InitialFlame);
    if (InitialGlass) J->SetObjectField(TEXT("initialGlassComponent"),InitialGlass);
    if (InitialSun) J->SetObjectField(TEXT("initialSun"),InitialSun);
    if (FailureObservation) J->SetObjectField(TEXT("failureObservation"), FailureObservation);
    J->SetObjectField(TEXT("finalSun"), SunState());
    if (FlameComponent) J->SetObjectField(TEXT("finalFlameComponent"),ComponentState(FlameComponent));
    if (GlassComponent) J->SetObjectField(TEXT("finalGlassComponent"),ComponentState(GlassComponent));
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
    J->SetBoolField(TEXT("qualitySettingsUnchanged"), InitialQuality.IsValid() && FlameJsonText(QualitySettings()) == FlameJsonText(InitialQuality.ToSharedRef()));
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
    J->SetStringField(TEXT("limitations"), TEXT("Fixed 30 simulation Hz and synchronous PNG/readback stalls are not FPS evidence. Public unscaled/target dimensions do not expose private internal raster/history dimensions. World/real time is recorded, not frozen. Only this transient flame material has phase 2 seconds. Water/foliage may differ; numerical comparison is confined to the registered flame ROI. Manual exposure is a study control, not an authored production change. Visual comparison remains required."));
    return FFileHelper::SaveStringToFile(FlameJsonText(J), *(OutputDirectory / TEXT("runtime.json")), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
}

void UBreziFlameStudy::Finish(const FString& Status, const FString& Reason)
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
    if (Extension) Extension->Stop();
    FlushRenderingCommands();
    Extension.Reset();
    bExtensionStopped = true;
    RestoreMaterial();
    FlushRenderingCommands(); // Drain the restored component material binding before leaving the study.
    if (bStudyViewSelected && Pawn())
    {
        // The view changes before walking entry can fail. Restore both parts
        // independently, including a failed entry that never changed the mode.
        if (Pawn()->IsWalkingMode()) Pawn()->ToggleMovementMode();
        Pawn()->SelectView(PriorViewId,true);
        bCameraRestored=!Pawn()->IsWalkingMode() && Pawn()->GetActiveViewId()==PriorViewId;
        bStudyViewSelected=false;
    }
    RestoreClock();
    SetComponentTickEnabled(false);
    const FString FinalStatus = (Status == TEXT("flame-study-captured") || Status == TEXT("flame-shape-captured")) && (!bMaterialRestored || !bInvariantStateRestored || !bClockRestored || !bCameraRestored)
        ? TEXT("failed-restoration") : Status;
    const bool bSaved = SaveReport(FinalStatus, Reason);
    UE_LOG(LogTemp, Display, TEXT("BreziFlameStudy status=%s frames=%d restored=%d saved=%d reason=%s"), *FinalStatus, Frames.Num(), bClockRestored, bSaved, *Reason);
    if (FParse::Param(FCommandLine::Get(), TEXT("BreziFlameStudyExit"))) FPlatformMisc::RequestExit(false);
}

void UBreziFlameStudy::EndPlay(const EEndPlayReason::Type Reason)
{
    if (bEnabled && !bFinished) Finish(TEXT("interrupted-before-completion"));
    RestoreClock();
    Extension.Reset();
    FrameState.Reset();
    Super::EndPlay(Reason);
}

bool UBreziFlameStudy::ReadContract(const FString& Path)
{
    TArray<uint8> Bytes;
    if (!FPaths::IsRelative(Path) && FFileHelper::LoadFileToArray(Bytes,*Path) && Bytes.Num()>0 && Bytes.Num()<1024*1024)
    {
        uint8 Digest[20]; FSHA1::HashBuffer(Bytes.GetData(),Bytes.Num(),Digest);
        ContractSha1=BytesToHex(Digest,20).ToLower();
        FString Text; FFileHelper::BufferToString(Text,Bytes.GetData(),Bytes.Num());
        if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text),Contract) || !Contract) return false;
        double Version=0, Triangles=0, Phase=0, Exposure=0, Fov=0;
        FString Code;
        const auto Vec = [this](const TCHAR* Key,FVector& Out) {
            const TArray<TSharedPtr<FJsonValue>>* A=nullptr;
            if (!Contract->TryGetArrayField(Key,A) || A->Num()!=3) return false;
            double V[3];
            for (int I=0;I<3;++I) if (!(*A)[I]->TryGetNumber(V[I]) || !FMath::IsFinite(V[I])) return false;
            Out=FVector(V[0],V[1],V[2]); return true;
        };
        if (!Contract->TryGetNumberField(TEXT("schemaVersion"),Version) || Version!=(IsShapeStudy()?2:1)
            || !Contract->TryGetNumberField(TEXT("triangles"),Triangles) || Triangles!=12
            || !Contract->TryGetNumberField(TEXT("studyTimeSeconds"),Phase) || Phase!=StudySeconds
            || !Contract->TryGetStringField(TEXT("lightingState"),LightingState) || !TArray<FString>{TEXT("day"),TEXT("night")}.Contains(LightingState)
            || !Contract->TryGetNumberField(TEXT("targetPreExposure"),Exposure)
            || Exposure!=(LightingState==TEXT("night")?FlameNightPreExposure:FlameDayPreExposure)
            || !Contract->TryGetNumberField(TEXT("horizontalFovDegrees"),Fov) || Fov<=1 || Fov>=170
            || !Contract->TryGetStringField(TEXT("sourceManifestSha256"),SceneSha) || SceneSha.Len()!=64
            || !Contract->TryGetStringField(TEXT("sourceObjSha256"),ObjSha) || ObjSha.Len()!=64
            || !Contract->TryGetStringField(TEXT("flameShaderSha256"),Code)
            || (Code!=TEXT("682b7d0e89131964e95d845fa365b0a9a1d448ffe256f25be8eb36288bd2c48c")
                && Code!=TEXT("08a70ffa9d33bdddad0842b8d4a01e5737748acd6ff32cb21c4cc4ea3268172a")
                && Code!=TEXT("45b0871f6776cc197686ff19cb8e7253babdc0c1ca41943d479f504a76f137bc"))
            || !Contract->TryGetStringField(TEXT("mesh"),MeshPath) || !MeshPath.StartsWith(TEXT("/Game/Brezi/VisualDetails/Stove/V_"))
            || !MeshPath.EndsWith(TEXT("/StaticMeshes/STOVEV_FLAMES.STOVEV_FLAMES"))
            || !Contract->TryGetStringField(TEXT("material"),MaterialPath) || !MaterialPath.StartsWith(TEXT("/Game/Brezi/VisualDetails/Stove/V_"))
            || !MaterialPath.EndsWith(TEXT("/Materials/M_Stove_flames.M_Stove_flames"))
            || !Contract->TryGetStringField(TEXT("glassMesh"),GlassMeshPath)
            || GlassMeshPath!=TEXT("/Game/Brezi/Geometry/brezi-twin/StaticMeshes/DOM_00526.DOM_00526")
            || !Contract->TryGetStringField(TEXT("glassMaterial"),GlassMaterialPath) || !GlassMaterialPath.StartsWith(TEXT("/Game/Brezi/OpticsGenerated/"))
            || !Vec(TEXT("eyeCm"),ExpectedEye) || !Vec(TEXT("targetCm"),ExpectedTarget)
            || !Vec(TEXT("boundsMinCm"),ExpectedBoundsMin) || !Vec(TEXT("boundsMaxCm"),ExpectedBoundsMax)) return false;
        const bool bCandidate=Code!=TEXT("682b7d0e89131964e95d845fa365b0a9a1d448ffe256f25be8eb36288bd2c48c");
        const TCHAR* ExpectedPreviousShader=Code==TEXT("45b0871f6776cc197686ff19cb8e7253babdc0c1ca41943d479f504a76f137bc")
            ? TEXT("08a70ffa9d33bdddad0842b8d4a01e5737748acd6ff32cb21c4cc4ea3268172a")
            : TEXT("682b7d0e89131964e95d845fa365b0a9a1d448ffe256f25be8eb36288bd2c48c");
        const bool bNewProof=Contract->HasField(TEXT("emissionAndOpacityMatchPinnedShader"))
            || Contract->HasField(TEXT("alphaShapeChangedFromPreviousRevision")) || Contract->HasField(TEXT("previousShaderSha256"));
        if (bCandidate || bNewProof)
        {
            bool bMatches=false,bChanged=false; FString Previous;
            if (!Contract->TryGetBoolField(TEXT("emissionAndOpacityMatchPinnedShader"),bMatches) || !bMatches
                || !Contract->TryGetBoolField(TEXT("alphaShapeChangedFromPreviousRevision"),bChanged) || bChanged!=bCandidate
                || (bCandidate ? (!Contract->TryGetStringField(TEXT("previousShaderSha256"),Previous)
                    || Previous!=ExpectedPreviousShader)
                    : !Contract->HasTypedField<EJson::Null>(TEXT("previousShaderSha256")))
                || (bCandidate && Contract->HasField(TEXT("emissionAndOpacityShapeUnchanged")))) return false;
        } // Only the exact old recipe can read its byte-preserved legacy contract.
        SourceInteriorEye=ExpectedEye; SourceInteriorTarget=ExpectedTarget;
        if (IsShapeStudy())
        {
            FString Mode;
            const TArray<TSharedPtr<FJsonValue>>* Supports=nullptr;
            if (!Contract->TryGetStringField(TEXT("shapeMode"),Mode) || Mode!=ShapeMode
                || !Contract->TryGetStringField(TEXT("poseId"),ShapePose)
                || !TArray<FString>{TEXT("interior"),TEXT("oblique")}.Contains(ShapePose)
                || !Vec(TEXT("sourceInteriorEyeCm"),SourceInteriorEye) || !Vec(TEXT("sourceInteriorTargetCm"),SourceInteriorTarget)
                || !Vec(TEXT("sourceStoveAxisCm"),ExpectedStoveAxis)
                || !Contract->TryGetArrayField(TEXT("allowedFloorIds"),Supports) || Supports->IsEmpty() || Supports->Num()>1024) return false;
            for (const auto& Value:*Supports)
            {
                FString Id; if (!Value->TryGetString(Id) || !Id.StartsWith(TEXT("DOM_")) || Id.Len()!=9 || ShapeSupportIds.Contains(Id)) return false;
                ShapeSupportIds.Add(Id);
            }
            if (ShapePose==TEXT("interior"))
            {
                if (!ExpectedEye.Equals(SourceInteriorEye,0.00001) || !ExpectedTarget.Equals(SourceInteriorTarget,0.00001)) return false;
            }
            else
            {
                const FVector DerivedEye(ExpectedStoveAxis.X+300.0*FMath::Cos(UE_DOUBLE_PI/6.0),ExpectedStoveAxis.Y-150.0,165.0);
                const FVector DerivedTarget(ExpectedStoveAxis.X,ExpectedStoveAxis.Y,165.0);
                if (!ExpectedEye.Equals(DerivedEye,0.00001) || !ExpectedTarget.Equals(DerivedTarget,0.00001)) return false;
            }
        }
        ExpectedFov=Fov; TargetPreExposure=Exposure;
        return ExpectedBoundsMin.X<ExpectedBoundsMax.X && ExpectedBoundsMin.Y<ExpectedBoundsMax.Y && ExpectedBoundsMin.Z<ExpectedBoundsMax.Z;
    }
    return false;
}

TSharedRef<FJsonObject> UBreziFlameStudy::ComponentState(UStaticMeshComponent* C) const
{
    const auto J=MakeShared<FJsonObject>();
    if (!C || !C->GetStaticMesh() || !C->GetMaterial(0)) return J;
    const UMaterialInterface* M=C->GetMaterial(0);
    // Normalize only our own known transient pointer; the caller separately proves
    // exact pointer identity before every capture and after restoration.
    if (M==StudyMaterial.Get()) M=OriginalMaterial.Get();
    if (!M || !C->GetOwner()) return J; // Failure observation must remain safe if a retained binding is missing.
    const UMaterial* Base=M->GetMaterial();
    const FStaticMeshRenderData* Data=C->GetStaticMesh()->GetRenderData();
    J->SetStringField(TEXT("mesh"),C->GetStaticMesh()->GetPathName());
    J->SetStringField(TEXT("sourceMaterial"),M->GetPathName());
    J->SetNumberField(TEXT("materialSlots"),C->GetNumMaterials());
    J->SetNumberField(TEXT("triangles"),Data && Data->LODResources.Num()>0 ? Data->LODResources[0].GetNumTriangles() : -1);
    J->SetStringField(TEXT("transform"),C->GetComponentTransform().ToString());
    const FBox Box=C->Bounds.GetBox();
    J->SetArrayField(TEXT("boundsMinCm"),FlameXYZ(Box.Min));
    J->SetArrayField(TEXT("boundsMaxCm"),FlameXYZ(Box.Max));
    J->SetBoolField(TEXT("visible"),C->IsVisible());
    J->SetBoolField(TEXT("hiddenInGame"),C->bHiddenInGame);
    J->SetBoolField(TEXT("actorHidden"),C->GetOwner()->IsHidden());
    J->SetBoolField(TEXT("castShadow"),C->CastShadow);
    J->SetBoolField(TEXT("castHiddenShadow"),C->bCastHiddenShadow);
    J->SetBoolField(TEXT("visibleInRayTracing"),C->bVisibleInRayTracing);
    J->SetBoolField(TEXT("affectDistanceFieldLighting"),C->bAffectDistanceFieldLighting);
    J->SetBoolField(TEXT("affectDynamicIndirectLighting"),C->bAffectDynamicIndirectLighting);
    J->SetNumberField(TEXT("collisionMode"),static_cast<int32>(C->GetCollisionEnabled()));
    J->SetStringField(TEXT("collisionProfile"),C->GetCollisionProfileName().ToString());
    J->SetNumberField(TEXT("translucencySortPriority"),C->TranslucencySortPriority);
    J->SetNumberField(TEXT("translucencySortDistanceOffset"),C->TranslucencySortDistanceOffset);
    J->SetNumberField(TEXT("translucencyPass"),Base?static_cast<int32>(Base->TranslucencyPass):-1);
    J->SetBoolField(TEXT("disableDepthTest"),!Base || Base->bDisableDepthTest);
    J->SetNumberField(TEXT("refractionMethod"),Base?static_cast<int32>(Base->RefractionMethod):-1);
    J->SetNumberField(TEXT("blendMode"),static_cast<int32>(M->GetBlendMode()));
    J->SetBoolField(TEXT("unlit"),M->GetShadingModels().HasOnlyShadingModel(MSM_Unlit));
    J->SetBoolField(TEXT("twoSided"),M->IsTwoSided());
    return J;
}

TSharedRef<FJsonObject> UBreziFlameStudy::SunState() const
{
    const auto J=MakeShared<FJsonObject>(); int Count=0;
    for (TActorIterator<AActor> It(GetWorld());It;++It) if (It->ActorHasTag(TEXT("BreziSun")))
    {
        TInlineComponentArray<UDirectionalLightComponent*> Lights(*It);
        for (const auto* Light:Lights)
        {
            ++Count;
            J->SetArrayField(TEXT("direction"),FlameXYZ(Light->GetDirection()));
            J->SetNumberField(TEXT("lux"),Light->Intensity);
            J->SetBoolField(TEXT("visible"),Light->IsVisible() && !It->IsHidden() && Light->bAffectsWorld && Light->IsRegistered());
        }
    }
    J->SetNumberField(TEXT("count"),Count); return J;
}

bool UBreziFlameStudy::BindFlame()
{
    int FlameCount=0, GlassCount=0, StoveCount=0;
    for (TActorIterator<AActor> It(GetWorld());It;++It)
    {
        TInlineComponentArray<UStaticMeshComponent*> Components(*It);
        for (UStaticMeshComponent* C:Components)
        {
            if (!C || !C->GetStaticMesh()) continue;
            if (IsShapeStudy() && It->ActorHasTag(TEXT("DOM_00522")))
            {
                ++StoveCount;
                if (Components.Num()!=1 || C->GetStaticMesh()->GetPathName()!=TEXT("/Game/Brezi/Geometry/brezi-twin/StaticMeshes/DOM_00522.DOM_00522")) return false;
                const FVector Center=C->Bounds.GetBox().GetCenter();
                NativeStoveAxis=FVector(Center.X,Center.Y,0);
            }
            if (It->ActorHasTag(TEXT("BreziStoveVisualDetail")) && C->GetStaticMesh()->GetName()==TEXT("STOVEV_FLAMES")
                && C->IsVisible() && !C->bHiddenInGame && !It->IsHidden())
            { ++FlameCount; if (Components.Num()!=1 || C->GetStaticMesh()->GetPathName()!=MeshPath) return false; FlameComponent=C; }
            if (It->ActorHasTag(TEXT("DOM_00526")))
            { ++GlassCount; if (Components.Num()!=1 || C->GetStaticMesh()->GetPathName()!=GlassMeshPath) return false; GlassComponent=C; }
        }
    }
    if (FlameCount!=1 || GlassCount!=1 || FlameComponent->GetNumMaterials()!=1 || GlassComponent->GetNumMaterials()!=1) return false;
    if (IsShapeStudy())
    {
        bNativeStoveAxisVerified=StoveCount==1 && NativeStoveAxis.Equals(ExpectedStoveAxis,0.005);
        if (!bNativeStoveAxisVerified) return false;
    }
    OriginalMaterial=FlameComponent->GetMaterial(0); OriginalGlassMaterial=GlassComponent->GetMaterial(0);
    if (!OriginalMaterial || !OriginalGlassMaterial || OriginalMaterial->GetPathName()!=MaterialPath
        || OriginalGlassMaterial->GetPathName()!=GlassMaterialPath) return false;
    float Scale=0,Time=0;
    if (!OriginalMaterial->GetScalarParameterValue(FHashedMaterialParameterInfo(ScaleParameter),Scale) || Scale!=1
        || !OriginalMaterial->GetScalarParameterValue(FHashedMaterialParameterInfo(TimeParameter),Time) || Time!=-1) return false;
    InitialFlame=ComponentState(FlameComponent); InitialGlass=ComponentState(GlassComponent); InitialSun=SunState();
    const FBox Box=FlameComponent->Bounds.GetBox();
    if (InitialFlame->GetNumberField(TEXT("triangles"))!=12 || InitialGlass->GetNumberField(TEXT("triangles"))!=192
        || OriginalMaterial->GetBlendMode()!=BLEND_Additive || !OriginalMaterial->GetShadingModels().HasOnlyShadingModel(MSM_Unlit)
        || !OriginalMaterial->IsTwoSided() || InitialFlame->GetBoolField(TEXT("disableDepthTest"))
        || InitialGlass->GetBoolField(TEXT("disableDepthTest")) || !InitialGlass->GetBoolField(TEXT("visible"))
        || InitialGlass->GetBoolField(TEXT("hiddenInGame")) || InitialGlass->GetBoolField(TEXT("actorHidden"))
        || FlameComponent->GetCollisionProfileName()!=TEXT("NoCollision") || FlameComponent->GetCollisionEnabled()!=ECollisionEnabled::NoCollision
        || !Box.Min.Equals(ExpectedBoundsMin,0.005) || !Box.Max.Equals(ExpectedBoundsMax,0.005)
        || InitialSun->GetNumberField(TEXT("count"))!=1 || !InitialSun->GetBoolField(TEXT("visible"))
        || FMath::Abs(InitialSun->GetNumberField(TEXT("lux"))-(LightingState==TEXT("night")?0.15:80000.0))>0.01) return false;
    return CheckBoundState();
}

bool UBreziFlameStudy::ApplyStudyMaterial()
{
    if (!CheckBoundState() || StudyMaterial) return false;
    StudyMaterial=UMaterialInstanceDynamic::Create(OriginalMaterial,this);
    if (!StudyMaterial) return false;
    StudyMaterial->SetScalarParameterValue(ScaleParameter,EmissionScale);
    StudyMaterial->SetScalarParameterValue(TimeParameter,StudySeconds);
    FlameComponent->SetMaterial(0,StudyMaterial);
    return CheckBoundState();
}

bool UBreziFlameStudy::CheckBoundState(TSharedPtr<FJsonObject>* Observation) const
{
    // Each predicate and its diagnostic values use the same GT reads. No relaxed
    // equality and no post-restoration reconstruction of the failed observation.
    float Scale=0, Time=0;
    const UMaterialInterface* Expected=StudyMaterial?StudyMaterial.Get():OriginalMaterial.Get();
    const UMaterialInterface* Bound=FlameComponent?FlameComponent->GetMaterial(0):nullptr;
    const UMaterialInterface* GlassBound=GlassComponent?GlassComponent->GetMaterial(0):nullptr;
    const bool bScaleRead=Expected && Expected->GetScalarParameterValue(FHashedMaterialParameterInfo(ScaleParameter),Scale);
    const bool bTimeRead=Expected && Expected->GetScalarParameterValue(FHashedMaterialParameterInfo(TimeParameter),Time);
    const float ExpectedScale=StudyMaterial?EmissionScale:1.0f;
    const float ExpectedTime=StudyMaterial?ExpectedStudySeconds():-1.0f;
    const auto FlameNow=ComponentState(FlameComponent);
    const auto GlassNow=ComponentState(GlassComponent);
    const auto SunNow=SunState();
    const bool bFlameStateMatches=InitialFlame && FlameJsonText(FlameNow)==FlameJsonText(InitialFlame.ToSharedRef());
    const bool bGlassStateMatches=InitialGlass && FlameJsonText(GlassNow)==FlameJsonText(InitialGlass.ToSharedRef());
    const bool bSunStateMatches=InitialSun && FlameJsonText(SunNow)==FlameJsonText(InitialSun.ToSharedRef());
    FString Predicate;
    const auto Require=[&Predicate](bool bPass,const TCHAR* Name) { if (!bPass && Predicate.IsEmpty()) Predicate=Name; };
    Require(FlameComponent!=nullptr,TEXT("flame-component-missing"));
    Require(GlassComponent!=nullptr,TEXT("glass-component-missing"));
    Require(Expected!=nullptr,TEXT("expected-flame-material-missing"));
    Require(InitialFlame.IsValid() && InitialGlass.IsValid() && InitialSun.IsValid(),TEXT("initial-source-snapshot-missing"));
    Require(Bound==Expected,TEXT("flame-material-pointer-mismatch"));
    Require(GlassBound==OriginalGlassMaterial.Get(),TEXT("glass-material-pointer-mismatch"));
    Require(bScaleRead,TEXT("emission-scale-getter-failed"));
    Require(Scale==ExpectedScale,TEXT("emission-scale-value-mismatch"));
    Require(bTimeRead,TEXT("study-time-getter-failed"));
    Require(Time==ExpectedTime,TEXT("study-time-value-mismatch"));
    Require(bFlameStateMatches,TEXT("flame-component-state-mismatch"));
    Require(bGlassStateMatches,TEXT("glass-component-state-mismatch"));
    Require(bSunStateMatches,TEXT("source-sun-state-mismatch"));
    if (Observation)
    {
        const auto J=MakeShared<FJsonObject>();
        J->SetBoolField(TEXT("valid"),Predicate.IsEmpty());
        J->SetStringField(TEXT("firstFailedPredicate"),Predicate.IsEmpty()?TEXT("none"):Predicate);
        const auto ObservedMaterialPath=[](const UMaterialInterface* M) { return M?M->GetPathName():FString(); };
        J->SetStringField(TEXT("expectedMaterialPath"),ObservedMaterialPath(Expected));
        J->SetStringField(TEXT("boundMaterialPath"),ObservedMaterialPath(Bound));
        J->SetStringField(TEXT("originalMaterialPath"),ObservedMaterialPath(OriginalMaterial.Get()));
        J->SetStringField(TEXT("studyMaterialPath"),ObservedMaterialPath(StudyMaterial.Get()));
        J->SetStringField(TEXT("expectedGlassMaterialPath"),ObservedMaterialPath(OriginalGlassMaterial.Get()));
        J->SetStringField(TEXT("boundGlassMaterialPath"),ObservedMaterialPath(GlassBound));
        J->SetBoolField(TEXT("boundMaterialMatchesExpected"),Expected && Bound==Expected);
        J->SetBoolField(TEXT("boundMaterialIsStudy"),StudyMaterial && Bound==StudyMaterial.Get());
        J->SetBoolField(TEXT("glassMaterialMatchesExpected"),OriginalGlassMaterial && GlassBound==OriginalGlassMaterial.Get());
        J->SetNumberField(TEXT("expectedEmissionScale"),ExpectedScale);
        J->SetNumberField(TEXT("expectedStudyTimeSeconds"),ExpectedTime);
        const auto Scalar=[](const TSharedRef<FJsonObject>& D,const TCHAR* Name,bool bRead,float Value) {
            const auto V=MakeShared<FJsonObject>();
            V->SetBoolField(TEXT("getterSucceeded"),bRead);
            V->SetBoolField(TEXT("finite"),bRead && FMath::IsFinite(Value));
            if (bRead && FMath::IsFinite(Value)) V->SetNumberField(TEXT("value"),Value);
            else V->SetField(TEXT("value"),MakeShared<FJsonValueNull>());
            D->SetObjectField(Name,V);
        };
        Scalar(J,TEXT("expectedMaterialEmissionScale"),bScaleRead,Scale);
        Scalar(J,TEXT("expectedMaterialStudyTime"),bTimeRead,Time);
        float BoundScale=Scale,BoundTime=Time;
        const bool bBoundScaleRead=Bound==Expected?bScaleRead:Bound && Bound->GetScalarParameterValue(FHashedMaterialParameterInfo(ScaleParameter),BoundScale);
        const bool bBoundTimeRead=Bound==Expected?bTimeRead:Bound && Bound->GetScalarParameterValue(FHashedMaterialParameterInfo(TimeParameter),BoundTime);
        Scalar(J,TEXT("boundMaterialEmissionScale"),bBoundScaleRead,BoundScale);
        Scalar(J,TEXT("boundMaterialStudyTime"),bBoundTimeRead,BoundTime);
        J->SetBoolField(TEXT("flameStateMatchesInitial"),bFlameStateMatches);
        J->SetBoolField(TEXT("glassStateMatchesInitial"),bGlassStateMatches);
        J->SetBoolField(TEXT("sunStateMatchesInitial"),bSunStateMatches);
        J->SetObjectField(TEXT("flameComponent"),FlameNow);
        J->SetObjectField(TEXT("glassComponent"),GlassNow);
        J->SetObjectField(TEXT("sun"),SunNow);
        *Observation=J;
    }
    return Predicate.IsEmpty();
}

void UBreziFlameStudy::CaptureFailureObservation(const FString& Predicate,const TSharedPtr<FJsonObject>& BoundState,bool bWalking)
{
    check(IsInGameThread());
    if (FailureObservation) return; // Preserve the first pre-cleanup failure only.
    FailureObservation=MakeShared<FJsonObject>();
    FailureObservation->SetStringField(TEXT("phase"),TEXT("game-thread-before-Finish-and-RestoreMaterial"));
    FailureObservation->SetStringField(TEXT("firstFailedPredicate"),Predicate);
    FailureObservation->SetNumberField(TEXT("gameFrameCounter"),GFrameCounter);
    FailureObservation->SetNumberField(TEXT("captureIndex"),CaptureIndex);
    FailureObservation->SetNumberField(TEXT("warmupFrames"),WarmupFrames);
    FailureObservation->SetNumberField(TEXT("wallSeconds"),FPlatformTime::Seconds());
    if (GetWorld())
    {
        FailureObservation->SetNumberField(TEXT("worldSeconds"),GetWorld()->GetTimeSeconds());
        FailureObservation->SetNumberField(TEXT("realSeconds"),GetWorld()->GetRealTimeSeconds());
    }
    FailureObservation->SetBoolField(TEXT("walkingModeValid"),bWalking);
    FailureObservation->SetBoolField(TEXT("boundStateValid"),BoundState && BoundState->GetBoolField(TEXT("valid")));
    if (BoundState) FailureObservation->SetObjectField(TEXT("boundState"),BoundState);
    if (const ABreziPawn* Character=Pawn())
    {
        FailureObservation->SetStringField(TEXT("activeViewId"),Character->GetActiveViewId());
        FailureObservation->SetObjectField(TEXT("walking"),Character->GetWalkingDiagnostics());
    }
}

void UBreziFlameStudy::RestoreMaterial()
{
    if (!StudyMaterial) return;
    // An unexpected foreign binding is evidence failure, never overwritten.
    if (FlameComponent && FlameComponent->GetMaterial(0)==StudyMaterial.Get()) FlameComponent->SetMaterial(0,OriginalMaterial);
    bMaterialRestored=FlameComponent && OriginalMaterial && FlameComponent->GetMaterial(0)==OriginalMaterial.Get();
    bInvariantStateRestored=bMaterialRestored && GlassComponent && GlassComponent->GetMaterial(0)==OriginalGlassMaterial.Get()
        && InitialFlame && InitialGlass && FlameJsonText(ComponentState(FlameComponent))==FlameJsonText(InitialFlame.ToSharedRef())
        && FlameJsonText(ComponentState(GlassComponent))==FlameJsonText(InitialGlass.ToSharedRef());
}
