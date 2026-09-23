#include "BreziWalkingTraversal.h"
#include "BreziPresentationQA.h"

#include "BreziPawn.h"
#include "BreziDoors.h"
#include "BreziPlayerController.h"
#include "BreziGameViewportClient.h"
#include "DynamicRHI.h"
#include "RHI.h"
#include "HAL/IConsoleManager.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GenericPlatform/GenericPlatformInputDeviceMapper.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformTime.h"
#include "InputKeyEventArgs.h"
#include "ImageCore.h"
#include "ImageUtils.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Widgets/SWidget.h"

namespace
{
TArray<TSharedPtr<FJsonValue>> VectorJson(const FVector& V)
{
    return {MakeShared<FJsonValueNumber>(V.X), MakeShared<FJsonValueNumber>(V.Y), MakeShared<FJsonValueNumber>(V.Z)};
}

bool ReadVector(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field, FVector& Result)
{
    const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
    if (!Object->TryGetArrayField(Field, Values) || Values->Num() != 3) return false;
    double C[3];
    for (int32 I = 0; I < 3; ++I)
        if (!(*Values)[I]->TryGetNumber(C[I]) || !FMath::IsFinite(C[I])) return false;
    Result = FVector(C[0], C[1], C[2]);
    return true;
}

const TCHAR* PhaseName(EBreziTraversalPhase Phase)
{
    switch (Phase)
    {
        case EBreziTraversalPhase::Warmup: return TEXT("warmup");
        case EBreziTraversalPhase::Enter: return TEXT("enter");
        case EBreziTraversalPhase::Navigate: return TEXT("navigate");
        case EBreziTraversalPhase::Hold: return TEXT("hold");
        case EBreziTraversalPhase::Brake: return TEXT("brake");
        case EBreziTraversalPhase::Exit: return TEXT("exit");
        default: return TEXT("complete");
    }
}
}

UBreziWalkingTraversal::UBreziWalkingTraversal()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;
    PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

ABreziPawn* UBreziWalkingTraversal::Pawn() const
{
    return Controller() ? Cast<ABreziPawn>(Controller()->GetPawn()) : nullptr;
}

APlayerController* UBreziWalkingTraversal::Controller() const
{
    return Cast<APlayerController>(GetOwner());
}

void UBreziWalkingTraversal::BeginPlay()
{
    Super::BeginPlay();
    FString CasesPath;
    bWalkthrough = FParse::Value(FCommandLine::Get(), TEXT("BreziWalkthrough="), CasesPath);
    if (!bWalkthrough && !FParse::Value(FCommandLine::Get(), TEXT("BreziWalkTraversal="), CasesPath)) return;
    bEnabled = true;
    RunStartWallSeconds = FPlatformTime::Seconds();
    bPriorFixedStep = FApp::UseFixedTimeStep();
    PriorFixedDelta = FApp::GetFixedDeltaTime();
    bPriorFixedFrameRate = GEngine && GEngine->bUseFixedFrameRate;
    PriorFixedFrameRate = GEngine ? GEngine->FixedFrameRate : 0;
    ReportPath = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Diagnostics"),
        (bWalkthrough ? TEXT("walkthrough-") : TEXT("walking-traversal-")) + FDateTime::UtcNow().ToString(TEXT("%Y%m%dT%H%M%S")) + TEXT(".json"));
    // The render benchmark has its own completion/exit state machine. Use a separate invocation.
    const TCHAR* CLI = FCommandLine::Get();
    FString Ignored;
    if (FParse::Param(CLI, TEXT("BreziCapture4K")) || FParse::Param(CLI, TEXT("BreziCaptureUI")) || FParse::Param(CLI, TEXT("BreziCaptureScene"))
        || FParse::Param(CLI, TEXT("BreziExitAfterCapture"))
        || FParse::Param(CLI, TEXT("BreziWalk")) || FParse::Param(CLI, TEXT("BreziWalkAudit"))
        || FParse::Value(CLI, TEXT("BreziBenchmarkFrames="), Ignored)
        || FParse::Param(CLI, TEXT("BreziProfileGPU")))
    {
        LoadError = TEXT("Use the traversal harness in a separate process without entry/benchmark/capture/profile flags.");
        if (bWalkthrough) FinishWalkthrough(TEXT("failed-arguments"), LoadError); else FinishRun(TEXT("failed-arguments"));
        return;
    }
    if (bWalkthrough)
    {
        if (!LoadWalkthrough(CasesPath)) { FinishWalkthrough(TEXT("failed-fixtures"), LoadError); return; }
        bWalkthroughScreenshots = FParse::Param(CLI, TEXT("BreziWalkthroughScreenshots"));
        if (bWalkthroughScreenshots)
        {
            WalkthroughScreenshotHandle = UGameViewportClient::OnScreenshotCaptured().AddUObject(this, &UBreziWalkingTraversal::OnWalkthroughScreenshot);
            if (IConsoleVariable* DelegateEnabled = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenshotDelegate"))) DelegateEnabled->Set(1, ECVF_SetByCode);
        }
        SetComponentTickEnabled(true);
        if (!SaveWalkthrough(TEXT("running"))) FinishWalkthrough(TEXT("failed-report-write"), TEXT("Could not create walkthrough report."));
        return;
    }
    if (!LoadCases(CasesPath)) { FinishRun(TEXT("failed-fixtures")); return; }
    SetComponentTickEnabled(true);
    if (!SaveReport(TEXT("running")))
    { LoadError = TEXT("Could not create traversal report."); FinishRun(TEXT("failed-report-write")); }
}

bool UBreziWalkingTraversal::LoadCases(const FString& Path)
{
    if (!Contract.Load(LoadError)) return false;
    FString Source;
    TSharedPtr<FJsonObject> Root;
    if (!FFileHelper::LoadFileToString(Source, *Path)
        || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Source), Root) || !Root.IsValid())
    { LoadError = TEXT("Fixture JSON could not be loaded."); return false; }
    double Version = 0;
    FString Coordinates;
    const TArray<TSharedPtr<FJsonValue>>* Entries = nullptr;
    if (!Root->TryGetNumberField(TEXT("schemaVersion"), Version) || Version != 1
        || !Root->TryGetStringField(TEXT("coordinateSystem"), Coordinates) || Coordinates != TEXT("unreal-centimeters")
        || !Root->TryGetStringField(TEXT("sceneSha256"), SceneSha256) || SceneSha256 != Contract.SceneSha256
        || !Root->TryGetArrayField(TEXT("cases"), Entries) || Entries->IsEmpty() || Entries->Num() > 32)
    { LoadError = TEXT("Fixture schema, scene hash, coordinates or case count differs from the bundled source contract."); return false; }
    TSet<FString> Seen;
    for (const TSharedPtr<FJsonValue>& Entry : *Entries)
    {
        const TSharedPtr<FJsonObject>* Object = nullptr;
        FBreziTraversalCase Case;
        if (!Entry->TryGetObject(Object) || !(*Object)->TryGetStringField(TEXT("id"), Case.Id) || Case.Id.IsEmpty()
            || Seen.Contains(Case.Id) || !(*Object)->TryGetStringField(TEXT("blockerObjectId"), Case.BlockerId)
            || !(*Object)->TryGetStringField(TEXT("supportObjectId"), Case.ExpectedSupportId)
            || !ReadVector(*Object, TEXT("eyeCm"), Case.EyeCm) || !ReadVector(*Object, TEXT("forward"), Case.Forward)
            || !(*Object)->TryGetNumberField(TEXT("holdSeconds"), Case.HoldSeconds)
            || !FMath::IsFinite(Case.HoldSeconds) || Case.HoldSeconds < 1 || Case.HoldSeconds > 5
            || FMath::Abs(Case.Forward.Z) > 0.00001 || FMath::Abs(Case.Forward.Size() - 1) > 0.00001)
        { LoadError = TEXT("Malformed or duplicate traversal fixture."); return false; }
        const FBreziWalkingRecord* Blocker = Contract.Records.FindByPredicate([&Case](const FBreziWalkingRecord& R)
        { return R.ObjectId == Case.BlockerId && !R.bFloor; });
        const FBreziWalkingRecord* Floor = Contract.Records.FindByPredicate([&Case](const FBreziWalkingRecord& R)
        { return R.ObjectId == Case.ExpectedSupportId && R.bFloor; });
        if (!Blocker || !Floor)
        { LoadError = TEXT("Fixture target or floor is absent from the explicit source collision contract: ") + Case.Id; return false; }
        const TArray<TSharedPtr<FJsonValue>>* Allowed = nullptr;
        if (!(*Object)->TryGetArrayField(TEXT("allowedSupportObjectIds"), Allowed) || Allowed->IsEmpty() || Allowed->Num() > 16
            || !(*Object)->TryGetNumberField(TEXT("floorHeightCm"), Case.ExpectedFloorHeightCm) || !FMath::IsFinite(Case.ExpectedFloorHeightCm))
        { LoadError = TEXT("Missing explicit source-derived coplanar support references."); return false; }
        for (const TSharedPtr<FJsonValue>& Value : *Allowed)
        {
            FString Id;
            if (!Value->TryGetString(Id) || Case.AllowedSupportIds.Contains(Id)
                || !Contract.Records.ContainsByPredicate([&Id](const FBreziWalkingRecord& R) { return R.bFloor && R.ObjectId == Id; }))
            { LoadError = TEXT("Unknown or duplicate source-derived coplanar support."); return false; }
            Case.AllowedSupportIds.Add(Id);
        }
        if (!Case.AllowedSupportIds.Contains(Case.ExpectedSupportId))
        { LoadError = TEXT("Primary floor missing from the explicit coplanar references."); return false; }
        Seen.Add(Case.Id);
        Cases.Add(Case);
    }
    return true;
}

bool UBreziWalkingTraversal::BeginCase()
{
    ABreziPawn* Character = Pawn();
    if (!Character || !Character->HasViewpoints()) return false;
    const FBreziTraversalCase& Case = Cases[CaseIndex];
    ReleaseKeys();
    SimulatedHz = FrequencyIndex == 0 ? 20 : 60;
    // Installed UE binaries can compile WITH_FIXED_TIME_STEP_SUPPORT=0, making
    // FApp::SetUseFixedTimeStep ineffective. Engine fixed frame rate is a public
    // runtime path in UpdateTimeAndHandleMaxTickRate for these binaries too. It
    // advances the whole world/CMC at this delta even when GPU frames take longer.
    // Wall-clock intervals remain separately measured, never inferred from Hz.
    FApp::SetUseFixedTimeStep(false);
    GEngine->FixedFrameRate = static_cast<float>(SimulatedHz);
    GEngine->bUseFixedFrameRate = true;
    CurrentResult = MakeShared<FJsonObject>();
    CurrentResult->SetStringField(TEXT("id"), Case.Id);
    CurrentResult->SetStringField(TEXT("blockerObjectId"), Case.BlockerId);
    CurrentResult->SetStringField(TEXT("expectedSupportObjectId"), Case.ExpectedSupportId);
    TArray<TSharedPtr<FJsonValue>> AllowedJson;
    for (const FString& Id : Case.AllowedSupportIds) AllowedJson.Add(MakeShared<FJsonValueString>(Id));
    CurrentResult->SetArrayField(TEXT("allowedSupportObjectIds"), AllowedJson);
    CurrentResult->SetNumberField(TEXT("expectedFloorHeightCm"), Case.ExpectedFloorHeightCm);
    CurrentResult->SetNumberField(TEXT("simulationHz"), SimulatedHz);
    CurrentResult->SetNumberField(TEXT("requestedHoldSeconds"), Case.HoldSeconds);
    CurrentResult->SetArrayField(TEXT("fixtureEyeCm"), VectorJson(Case.EyeCm));
    CurrentResult->SetArrayField(TEXT("fixtureForward"), VectorJson(Case.Forward));
    CurrentResult->SetStringField(TEXT("status"), TEXT("running"));
    CurrentCaseWallStart = PreviousSampleWallSeconds = FPlatformTime::Seconds();
    FramesInPhase = 0;
    PhaseSeconds = 0;
    Phase = EBreziTraversalPhase::Warmup;
    PathSamples.Reset();
    MinPlaneClearance = TNumericLimits<double>::Max();
    MaxForwardProgress = MaxEyeErrorCm = MaxLateralDriftCm = MaxDeltaErrorSeconds = 0;
    WalkingSamples = InputDownSamples = UnexpectedOverlaps = UnsupportedSamples = MissingEyeSamples = 0;
    RenderObservationSamples = 0;
    MinScenePixels = MinTargetPixels = MinTexturePixels = FIntPoint(MAX_int32, MAX_int32);
    bNative4KRenderingThroughout = true;
    if (!Character->PrepareTraversalAuditView(Case.EyeCm, Case.Forward))
    { FinishCase(TEXT("failed"), TEXT("fixture-orbit-setup-rejected")); return true; }
    // Actor/CMC ticks have committed before each harness observation; no manual CMC ticking.
    AddTickPrerequisiteActor(Character);
    AddTickPrerequisiteComponent(Character->GetCharacterMovement());
    SaveReport(TEXT("running"));
    return true;
}

void UBreziWalkingTraversal::Key(const FKey& Code, bool bDown)
{
    if (!Controller()) return;
    if (bWalkthrough && PressedKeys.Contains(Code) == bDown && Controller()->IsInputKeyDown(Code) == bDown) return;
    const FInputDeviceId Device = IPlatformInputDeviceMapper::Get().GetDefaultInputDevice();
    FViewport* Viewport = GEngine && GEngine->GameViewport ? GEngine->GameViewport->Viewport : nullptr;
    Controller()->InputKey(FInputKeyEventArgs(Viewport, Device, Code, bDown ? IE_Pressed : IE_Released,
        bDown ? 1.0f : 0.0f, false, FPlatformTime::Cycles64()));
    if (bDown) PressedKeys.Add(Code); else PressedKeys.Remove(Code);
}

void UBreziWalkingTraversal::ReleaseKeys()
{
    const TArray<FKey> Keys = PressedKeys.Array();
    for (const FKey& Code : Keys) Key(Code, false);
}

bool UBreziWalkingTraversal::CheckBlockingSweep()
{
    const ABreziPawn* Character = Pawn();
    const FBreziTraversalCase& Case = Cases[CaseIndex];
    StartCenter = Character->GetActorLocation();
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BreziTraversalBaseline), true, Character);
    FHitResult Hit;
    SweepDistanceCm = Contract.NormalSpeed * Case.HoldSeconds;
    const FCollisionShape Shape = FCollisionShape::MakeCapsule(Contract.CapsuleRadiusCm, Contract.CapsuleHalfHeightCm);
    const bool bHit = GetWorld()->SweepSingleByChannel(Hit, StartCenter, StartCenter + Case.Forward * SweepDistanceCm,
        FQuat::Identity, ECC_Pawn, Shape, Params);
    CurrentResult->SetBoolField(TEXT("baselineSweepBlockingHit"), bHit && Hit.bBlockingHit);
    CurrentResult->SetStringField(TEXT("baselineSweepObjectId"), FBreziWalkingContract::ObjectId(Hit.GetComponent()));
    CurrentResult->SetNumberField(TEXT("baselineSweepHitDistanceCm"), Hit.Distance);
    CurrentResult->SetBoolField(TEXT("baselineSweepStartPenetrating"), Hit.bStartPenetrating);
    CurrentResult->SetArrayField(TEXT("startCapsuleCenterCm"), VectorJson(StartCenter));
    if (!bHit || !Hit.bBlockingHit || Hit.bStartPenetrating
        || FBreziWalkingContract::ObjectId(Hit.GetComponent()) != Case.BlockerId
        || FMath::Abs(Hit.ImpactNormal.Z) > 0.005 || FVector::DotProduct(Hit.ImpactNormal, Case.Forward) > -0.995
        || Hit.Distance < 20 || Hit.Distance > SweepDistanceCm - 20)
        return false;
    BlockerPoint = Hit.ImpactPoint;
    BlockerNormal = Hit.ImpactNormal.GetSafeNormal();
    CurrentResult->SetArrayField(TEXT("actualColliderPointCm"), VectorJson(BlockerPoint));
    CurrentResult->SetArrayField(TEXT("actualColliderNormal"), VectorJson(BlockerNormal));
    return true;
}

void UBreziWalkingTraversal::Sample(float DeltaTime)
{
    ABreziPawn* Character = Pawn();
    APlayerController* PC = Controller();
    const FVector Center = Character->GetActorLocation();
    const FVector Delta = Center - StartCenter;
    const FBreziTraversalCase& Case = Cases[CaseIndex];
    const double WallNow = FPlatformTime::Seconds();
    static const IConsoleVariable* Screen = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage"));
    static const IConsoleVariable* Secondary = IConsoleManager::Get().FindConsoleVariable(TEXT("r.SecondaryScreenPercentage.GameViewport"));
    static const IConsoleVariable* Dynamic = IConsoleManager::Get().FindConsoleVariable(TEXT("r.DynamicRes.OperationMode"));
    FIntPoint ScenePixels = FIntPoint::ZeroValue, TargetPixels = FIntPoint::ZeroValue, TexturePixels = FIntPoint::ZeroValue;
    bool bSeparate = false;
    if (GEngine && GEngine->GameViewport)
    {
        if (const FSceneViewport* Scene = GEngine->GameViewport->GetGameViewport())
        {
            ScenePixels = Scene->GetSizeXY();
            TargetPixels = Scene->GetRenderTargetTextureSizeXY();
            bSeparate = static_cast<const ISlateViewport*>(Scene)->UseSeparateRenderTarget();
            const FTextureRHIRef& Texture = Scene->GetRenderTargetTexture();
            if (Texture.IsValid()) TexturePixels = FIntPoint(Texture->GetSizeX(), Texture->GetSizeY());
        }
    }
    ++RenderObservationSamples;
    MinScenePixels = FIntPoint(FMath::Min(MinScenePixels.X, ScenePixels.X), FMath::Min(MinScenePixels.Y, ScenePixels.Y));
    MinTargetPixels = FIntPoint(FMath::Min(MinTargetPixels.X, TargetPixels.X), FMath::Min(MinTargetPixels.Y, TargetPixels.Y));
    MinTexturePixels = FIntPoint(FMath::Min(MinTexturePixels.X, TexturePixels.X), FMath::Min(MinTexturePixels.Y, TexturePixels.Y));
    const bool bNativeRendering = ScenePixels == FIntPoint(3840, 2160) && TargetPixels == FIntPoint(3840, 2160)
        && TexturePixels == FIntPoint(3840, 2160) && bSeparate && GDynamicRHI && FString(GDynamicRHI->GetName()) == TEXT("Metal")
        && Screen && Screen->GetFloat() == 100 && Secondary && Secondary->GetFloat() == 100 && Dynamic && Dynamic->GetInt() == 0;
    bNative4KRenderingThroughout &= bNativeRendering;
    const bool bGrounded = Character->IsWalkingMode() && Character->GetCharacterMovement()->IsMovingOnGround();
    const FString Support = FBreziWalkingContract::ObjectId(Character->GetCharacterMovement()->CurrentFloor.HitResult.GetComponent());
    if (bGrounded) ++WalkingSamples;
    if (!bGrounded || !Case.AllowedSupportIds.Contains(Support)) ++UnsupportedSamples;
    if (PC->IsInputKeyDown(EKeys::W)) ++InputDownSamples;
    MinPlaneClearance = FMath::Min(MinPlaneClearance, FVector::DotProduct(Center - BlockerPoint, BlockerNormal));
    const double ForwardProgress = FVector::DotProduct(Delta, Case.Forward);
    MaxForwardProgress = FMath::Max(MaxForwardProgress, ForwardProgress);
    MaxLateralDriftCm = FMath::Max(MaxLateralDriftCm, (Delta - Case.Forward * ForwardProgress).Size2D());
    MaxDeltaErrorSeconds = FMath::Max(MaxDeltaErrorSeconds, FMath::Abs(static_cast<double>(DeltaTime) - 1.0 / SimulatedHz));
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BreziTraversalOverlap), true, Character);
    // A 0.5 mm shrink ignores floating point skin contact; a penetration larger than this is a failure.
    const bool bOverlap = GetWorld()->OverlapBlockingTestByChannel(Center, FQuat::Identity, ECC_Pawn,
        FCollisionShape::MakeCapsule(Contract.CapsuleRadiusCm - 0.05, Contract.CapsuleHalfHeightCm - 0.05), Params);
    if (bOverlap) ++UnexpectedOverlaps;
    TSharedRef<FJsonObject> Observation = MakeShared<FJsonObject>();
    Observation->SetStringField(TEXT("phase"), PhaseName(Phase));
    Observation->SetBoolField(TEXT("native4KSceneTargetAt100Percent"), bNativeRendering);
    Observation->SetNumberField(TEXT("phaseFrame"), FramesInPhase);
    Observation->SetNumberField(TEXT("simulationDeltaSeconds"), DeltaTime);
    Observation->SetNumberField(TEXT("wallIntervalSeconds"), WallNow - PreviousSampleWallSeconds);
    Observation->SetArrayField(TEXT("capsuleCenterCm"), VectorJson(Center));
    Observation->SetArrayField(TEXT("velocityCmPerSecond"), VectorJson(Character->GetVelocity()));
    Observation->SetStringField(TEXT("supportObjectId"), Support);
    Observation->SetBoolField(TEXT("grounded"), bGrounded);
    Observation->SetBoolField(TEXT("wInputDown"), PC->IsInputKeyDown(EKeys::W));
    Observation->SetBoolField(TEXT("unexpectedOverlap"), bOverlap);
    Observation->SetNumberField(TEXT("colliderPlaneClearanceCm"), FVector::DotProduct(Center - BlockerPoint, BlockerNormal));
    const UCameraComponent* Camera = Character->GetPhysicalCamera();
    FHitResult Floor;
    const bool bFloorHit = GetWorld()->LineTraceSingleByChannel(Floor, Center,
        Center - FVector(0, 0, Contract.CapsuleHalfHeightCm + Contract.MaxStepCm + 10), ECC_Pawn, Params);
    if (Camera && bGrounded && bFloorHit && FBreziWalkingContract::IsFloor(Floor.GetComponent())
        && Case.AllowedSupportIds.Contains(FBreziWalkingContract::ObjectId(Floor.GetComponent()))
        && FMath::Abs(Floor.ImpactPoint.Z - Case.ExpectedFloorHeightCm) <= 0.02)
    {
        const double EyeHeight = Camera->GetComponentLocation().Z - Floor.ImpactPoint.Z;
        MaxEyeErrorCm = FMath::Max(MaxEyeErrorCm, FMath::Abs(EyeHeight - Contract.EyeHeightCm));
        Observation->SetArrayField(TEXT("cameraEyeCm"), VectorJson(Camera->GetComponentLocation()));
        Observation->SetStringField(TEXT("eyeReferenceFloorObjectId"), FBreziWalkingContract::ObjectId(Floor.GetComponent()));
        Observation->SetNumberField(TEXT("measuredEyeHeightCm"), EyeHeight);
        Observation->SetNumberField(TEXT("measuredFloorHeightCm"), Floor.ImpactPoint.Z);
    }
    else ++MissingEyeSamples;
    PathSamples.Add(MakeShared<FJsonValueObject>(Observation));
    PreviousSampleWallSeconds = WallNow;
}

void UBreziWalkingTraversal::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction)
{
    Super::TickComponent(DeltaTime, TickType, TickFunction);
    if (!bEnabled || bFinished) return;
    if (bWalkthrough) { TickWalkthrough(DeltaTime); return; }
    if (FPlatformTime::Seconds() - RunStartWallSeconds > 180)
    { LoadError = TEXT("Traversal exceeded the 180 second wall-time limit."); FinishRun(TEXT("failed-timeout")); return; }
    if (!CurrentResult.IsValid())
    {
        if (!BeginCase() && FPlatformTime::Seconds() - RunStartWallSeconds > 15)
        { LoadError = TEXT("Player or viewpoints unavailable."); FinishRun(TEXT("failed-startup")); }
        return;
    }
    if (!Pawn() || !Controller()) { FinishCase(TEXT("failed"), TEXT("player-lost")); return; }
    ++FramesInPhase;
    PhaseSeconds += DeltaTime;
    const auto Advance = [this](EBreziTraversalPhase Next)
    {
        Phase = Next; FramesInPhase = 0; PhaseSeconds = 0;
        if (!SaveReport(TEXT("running")))
        { LoadError = TEXT("Could not persist traversal progress."); FinishRun(TEXT("failed-report-write")); }
    };
    switch (Phase)
    {
    case EBreziTraversalPhase::Warmup:
        if (FramesInPhase >= SimulatedHz / 2)
        { Key(EKeys::M, true); Key(EKeys::M, false); Advance(EBreziTraversalPhase::Enter); }
        break;
    case EBreziTraversalPhase::Enter:
        if (FramesInPhase >= 3)
        {
            const TSharedRef<FJsonObject> Walking = Pawn()->GetWalkingDiagnostics();
            CurrentResult->SetObjectField(TEXT("entryObservation"), Walking);
            if (!Pawn()->IsWalkingMode()
                || !Cases[CaseIndex].AllowedSupportIds.Contains(Walking->GetStringField(TEXT("entrySupportObjectId")))
                || !Cases[CaseIndex].AllowedSupportIds.Contains(Walking->GetStringField(TEXT("entryLineHitObjectId"))))
            { FinishCase(TEXT("failed"), TEXT("native-vertical-entry-or-support-rejected")); break; }
            if (!CheckBlockingSweep())
            { FinishCase(TEXT("failed"), TEXT("native-capsule-baseline-does-not-hit-required-collider")); break; }
            if (FSlateApplication::IsInitialized()) FocusBeforeNavigation = FSlateApplication::Get().GetKeyboardFocusedWidget();
            Key(EKeys::F2, true); Key(EKeys::F2, false);
            Advance(EBreziTraversalPhase::Navigate);
        }
        break;
    case EBreziTraversalPhase::Navigate:
        if (FramesInPhase >= 2)
        {
            if (!Pawn()->IsNavigating() || Controller()->bShowMouseCursor)
            { FinishCase(TEXT("failed"), TEXT("F2-engine-input-did-not-start-navigation")); break; }
            Key(EKeys::W, true);
            PreviousSampleWallSeconds = FPlatformTime::Seconds();
            Advance(EBreziTraversalPhase::Hold);
        }
        break;
    case EBreziTraversalPhase::Hold:
        Sample(DeltaTime);
        if (FramesInPhase >= FMath::CeilToInt(Cases[CaseIndex].HoldSeconds * SimulatedHz))
        {
            CurrentResult->SetNumberField(TEXT("actualHoldFrames"), FramesInPhase);
            CurrentResult->SetNumberField(TEXT("actualHoldSimulationSeconds"), PhaseSeconds);
            CurrentResult->SetNumberField(TEXT("holdWInputDownSamples"), InputDownSamples);
            Key(EKeys::W, false);
            Advance(EBreziTraversalPhase::Brake);
        }
        break;
    case EBreziTraversalPhase::Brake:
        Sample(DeltaTime);
        if (FramesInPhase >= SimulatedHz / 2)
        {
            CurrentResult->SetNumberField(TEXT("releasedSpeedCmPerSecond"), Pawn()->GetVelocity().Size());
            const double StopClearance = FVector::DotProduct(Pawn()->GetActorLocation() - BlockerPoint, BlockerNormal);
            CurrentResult->SetNumberField(TEXT("stoppedPlaneClearanceCm"), StopClearance);
            CurrentResult->SetBoolField(TEXT("releasedWInputDown"), Controller()->IsInputKeyDown(EKeys::W));
            if (Pawn()->GetVelocity().Size() > 0.1 || Controller()->IsInputKeyDown(EKeys::W)
                || StopClearance > Contract.CapsuleRadiusCm + 1.0 || StopClearance < Contract.CapsuleRadiusCm - 0.05
                || MaxForwardProgress < 20 || MaxLateralDriftCm > 0.2 || MinPlaneClearance < Contract.CapsuleRadiusCm - 0.05
                || UnexpectedOverlaps > 0 || UnsupportedSamples > 0 || MissingEyeSamples > 0 || MaxEyeErrorCm > 0.2
                || MaxDeltaErrorSeconds > 0.00001 || !bNative4KRenderingThroughout
                || CurrentResult->GetNumberField(TEXT("holdWInputDownSamples")) != CurrentResult->GetNumberField(TEXT("actualHoldFrames")))
            { FinishCase(TEXT("failed"), TEXT("movement-path-stop-collision-support-eye-or-fixed-delta-assertion-failed")); break; }
            Key(EKeys::Escape, true); Key(EKeys::Escape, false);
            Advance(EBreziTraversalPhase::Exit);
        }
        break;
    case EBreziTraversalPhase::Exit:
        if (FramesInPhase >= 2)
        {
            const bool bFocusObserved = FocusBeforeNavigation.IsValid();
            const bool bFocusRestored = bFocusObserved && FSlateApplication::IsInitialized()
                && FSlateApplication::Get().GetKeyboardFocusedWidget() == FocusBeforeNavigation.Pin();
            CurrentResult->SetBoolField(TEXT("focusWasObservedBeforeNavigation"), bFocusObserved);
            CurrentResult->SetBoolField(TEXT("focusRestoredAfterEscape"), bFocusRestored);
            CurrentResult->SetBoolField(TEXT("cursorVisibleAfterEscape"), Controller()->bShowMouseCursor);
            if (Pawn()->IsNavigating() || !Controller()->bShowMouseCursor || !bFocusRestored)
                FinishCase(TEXT("failed"), TEXT("Escape-engine-input-did-not-restore-navigation-cursor-and-focus"));
            else FinishCase(TEXT("passed"), TEXT("native-entry-straight-blocking-engine-input-release-focus-observed"));
        }
        break;
    default: break;
    }
}

void UBreziWalkingTraversal::FinishCase(const FString& Status, const FString& Reason)
{
    ReleaseKeys();
    if (Pawn() && Pawn()->IsNavigating()) { Key(EKeys::Escape, true); Key(EKeys::Escape, false); }
    if (CurrentResult.IsValid())
    {
        CurrentResult->SetStringField(TEXT("status"), Status);
        CurrentResult->SetStringField(TEXT("reason"), Reason);
        CurrentResult->SetNumberField(TEXT("wallDurationSeconds"), FPlatformTime::Seconds() - CurrentCaseWallStart);
        CurrentResult->SetNumberField(TEXT("walkingSamples"), WalkingSamples);
        TSharedRef<FJsonObject> Rendering = MakeShared<FJsonObject>();
        Rendering->SetNumberField(TEXT("sampleCount"), RenderObservationSamples);
        Rendering->SetBoolField(TEXT("native4KThroughout"), RenderObservationSamples > 0 && bNative4KRenderingThroughout);
        if (RenderObservationSamples > 0)
        {
            const auto Pixels = [](FIntPoint Size) -> TArray<TSharedPtr<FJsonValue>>
            { return {MakeShared<FJsonValueNumber>(Size.X), MakeShared<FJsonValueNumber>(Size.Y)}; };
            Rendering->SetArrayField(TEXT("minimumSceneViewportPixels"), Pixels(MinScenePixels));
            Rendering->SetArrayField(TEXT("minimumSceneRenderTargetPixels"), Pixels(MinTargetPixels));
            Rendering->SetArrayField(TEXT("minimumRHITexturePixels"), Pixels(MinTexturePixels));
        }
        for (const TCHAR* Name : {TEXT("r.ScreenPercentage"), TEXT("r.SecondaryScreenPercentage.GameViewport"), TEXT("r.DynamicRes.OperationMode")})
            if (const IConsoleVariable* CVar = IConsoleManager::Get().FindConsoleVariable(Name)) Rendering->SetNumberField(Name, CVar->GetFloat());
        Rendering->SetStringField(TEXT("RHI"), GDynamicRHI ? FString(GDynamicRHI->GetName()) : TEXT("unavailable"));
        Rendering->SetStringField(TEXT("scope"), TEXT("Per-movement-sample Metal scene viewport, render target and actual RHI texture dimensions plus 100/100 render percentages and dynamic-resolution-off. These are independent of the fitted OS window; no smoothness, physical-display-resolution or completed GPU-frame claim."));
        CurrentResult->SetObjectField(TEXT("rendering"), Rendering);
        if (const UBreziGameViewportClient* Presentation = GEngine ? Cast<UBreziGameViewportClient>(GEngine->GameViewport) : nullptr)
            CurrentResult->SetObjectField(TEXT("presentation"), Presentation->GetPresentationDiagnostics());
        CurrentResult->SetNumberField(TEXT("unsupportedSamples"), UnsupportedSamples);
        CurrentResult->SetNumberField(TEXT("missingEyeSamples"), MissingEyeSamples);
        CurrentResult->SetNumberField(TEXT("unexpectedOverlapSamples"), UnexpectedOverlaps);
        CurrentResult->SetNumberField(TEXT("maxEyeHeightErrorCm"), MaxEyeErrorCm);
        CurrentResult->SetNumberField(TEXT("maxForwardProgressCm"), MaxForwardProgress);
        CurrentResult->SetNumberField(TEXT("maxLateralDriftCm"), MaxLateralDriftCm);
        CurrentResult->SetNumberField(TEXT("maxSimulationDeltaErrorSeconds"), MaxDeltaErrorSeconds);
        if (!PathSamples.IsEmpty()) CurrentResult->SetNumberField(TEXT("minimumColliderPlaneClearanceCm"), MinPlaneClearance);
        if (Pawn()) CurrentResult->SetObjectField(TEXT("finalWalkingObservation"), Pawn()->GetWalkingDiagnostics());
        CurrentResult->SetArrayField(TEXT("path"), PathSamples);
        Results.Add(MakeShared<FJsonValueObject>(CurrentResult));
        CurrentResult.Reset();
    }
    if (Status != TEXT("passed")) ++FailedCases;
    ++FrequencyIndex;
    if (FrequencyIndex == 2) { FrequencyIndex = 0; ++CaseIndex; }
    if (CaseIndex >= Cases.Num()) FinishRun(FailedCases == 0 ? TEXT("passed-bounded-cases") : TEXT("failed-cases"));
    else SaveReport(TEXT("running"));
}

bool UBreziWalkingTraversal::SaveReport(const FString& Status) const
{
    TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetNumberField(TEXT("schemaVersion"), 1);
    Root->SetStringField(TEXT("status"), Status);
    Root->SetStringField(TEXT("sceneSha256"), SceneSha256);
    Root->SetStringField(TEXT("error"), LoadError);
    Root->SetNumberField(TEXT("expectedCasesIncludingRates"), Cases.Num() * 2);
    Root->SetNumberField(TEXT("completedCases"), Results.Num());
    Root->SetNumberField(TEXT("failedCases"), FailedCases);
    Root->SetNumberField(TEXT("wallDurationSeconds"), FPlatformTime::Seconds() - RunStartWallSeconds);
    Root->SetArrayField(TEXT("results"), Results);
    if (CurrentResult.IsValid())
    {
        Root->SetObjectField(TEXT("inProgressCase"), CurrentResult);
        Root->SetStringField(TEXT("inProgressPhase"), PhaseName(Phase));
        Root->SetArrayField(TEXT("inProgressPath"), PathSamples);
    }
    Root->SetStringField(TEXT("inputMethod"), TEXT("APlayerController::InputKey -> registered input bindings -> Pawn AddMovementInput -> real CharacterMovement ticks. Fixture setup teleports only the disabled orbit capsule before entry. No manual position changes during measured traversal."));
    Root->SetStringField(TEXT("rateMeaning"), TEXT("20/60 are fixed simulation Hz, not measured display/GPU FPS. Per-frame wall intervals are recorded separately. Fixed step is restored on completion and EndPlay."));
    Root->SetStringField(TEXT("simulationClock"), TEXT("UEngine bUseFixedFrameRate / FixedFrameRate; actual world component delta independently checked in every movement sample."));
    Root->SetStringField(TEXT("scope"), TEXT("Only the listed actual source obstacles, both sides, vertical entry, straight movement, release and engine-level F2/M/Escape routing. No full-house coverage, diagonal sliding, step/drop threshold, native macOS keyboard, VoiceOver, or rendering-quality certification."));
    Root->SetArrayField(TEXT("pending"), {MakeShared<FJsonValueString>(TEXT("diagonal-wall-sliding")),
        MakeShared<FJsonValueString>(TEXT("source-step-and-terrace-seams")), MakeShared<FJsonValueString>(TEXT("source-drops-and-unsupported-edges")),
        MakeShared<FJsonValueString>(TEXT("precision-boost-and-diagonal-speed")), MakeShared<FJsonValueString>(TEXT("native-keyboard-and-VoiceOver"))});
    FString Text;
    FJsonSerializer::Serialize(Root, TJsonWriterFactory<>::Create(&Text));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(ReportPath), true);
    const FString Temporary = ReportPath + TEXT(".tmp");
    return FFileHelper::SaveStringToFile(Text, *Temporary, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)
        && IFileManager::Get().Move(*ReportPath, *Temporary, true, false, false, true);
}

void UBreziWalkingTraversal::FinishRun(const FString& Status)
{
    if (bFinished) return;
    ReleaseKeys();
    if (Pawn() && Pawn()->IsNavigating()) { Key(EKeys::Escape, true); Key(EKeys::Escape, false); }
    FApp::SetFixedDeltaTime(PriorFixedDelta);
    FApp::SetUseFixedTimeStep(bPriorFixedStep);
    if (GEngine)
    {
        GEngine->FixedFrameRate = PriorFixedFrameRate;
        GEngine->bUseFixedFrameRate = bPriorFixedFrameRate;
    }
    bFinished = true;
    Phase = EBreziTraversalPhase::Complete;
    SetComponentTickEnabled(false);
    const bool bSaved = SaveReport(Status);
    UE_LOG(LogTemp, Display, TEXT("BreziTraversal status=%s saved=%d path=%s"), *Status, bSaved, *ReportPath);
    if (FParse::Param(FCommandLine::Get(), TEXT("BreziTraversalExit")))
        FPlatformMisc::RequestExitWithStatus(false, bSaved && Status == TEXT("passed-bounded-cases") ? 0 : 1);
}

bool UBreziWalkingTraversal::LoadWalkthrough(const FString& Path)
{
    if (!Contract.Load(LoadError)) return false;
    FString Text;
    if (!FFileHelper::LoadFileToString(Text, *Path)
        || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), WalkthroughFixture) || !WalkthroughFixture.IsValid())
    { LoadError = TEXT("Walkthrough JSON could not be loaded."); return false; }
    double Version = 0;
    FString Coordinates;
    const TArray<TSharedPtr<FJsonValue>>* Steps = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* Regions = nullptr;
    const TArray<TSharedPtr<FJsonValue>>* Supports = nullptr;
    if (!WalkthroughFixture->TryGetNumberField(TEXT("schemaVersion"), Version) || Version != 1
        || !WalkthroughFixture->TryGetStringField(TEXT("coordinateSystem"), Coordinates) || Coordinates != TEXT("unreal-centimeters")
        || !WalkthroughFixture->TryGetStringField(TEXT("sceneSha256"), SceneSha256) || SceneSha256 != Contract.SceneSha256
        || !ReadVector(WalkthroughFixture, TEXT("startEyeCm"), WalkthroughStartEye)
        || !ReadVector(WalkthroughFixture, TEXT("startForward"), WalkthroughStartForward)
        || FMath::Abs(WalkthroughStartForward.SizeSquared2D() - 1) > 0.001 || FMath::Abs(WalkthroughStartForward.Z) > 0.001
        || !WalkthroughFixture->TryGetArrayField(TEXT("steps"), Steps) || Steps->IsEmpty() || Steps->Num() > 800
        || !WalkthroughFixture->TryGetArrayField(TEXT("requiredRegions"), Regions) || Regions->IsEmpty() || Regions->Num() > 40
        || !WalkthroughFixture->TryGetArrayField(TEXT("allowedSupportObjectIds"), Supports) || Supports->IsEmpty())
    { LoadError = TEXT("Walkthrough schema, scene, start, steps or coverage differs from the source contract."); return false; }
    TSet<FString> Ids;
    for (const auto& Value : *Regions)
    {
        const auto Region = Value->AsObject(); FString Id;
        if (!Region.IsValid() || !Region->TryGetStringField(TEXT("id"), Id) || Id.IsEmpty() || Ids.Contains(Id)
            || (!Region->HasTypedField<EJson::Array>(TEXT("rectsCm")) && !Region->HasTypedField<EJson::Array>(TEXT("polygonCm"))))
        { LoadError = TEXT("Malformed or duplicated coverage region."); return false; }
        Ids.Add(Id); WalkthroughRegions.Add(Region);
    }
    for (const auto& Value : *Steps)
    {
        const auto Step = Value->AsObject(); FString Id, Kind, Region; FVector Target;
        if (!Step.IsValid() || !Step->TryGetStringField(TEXT("id"), Id) || Id.IsEmpty()
            || !Step->TryGetStringField(TEXT("kind"), Kind) || (Kind != TEXT("move") && Kind != TEXT("visit") && Kind != TEXT("door"))
            || !Step->TryGetStringField(TEXT("regionId"), Region) || !Ids.Contains(Region)
            || !ReadVector(Step, TEXT("targetCm"), Target))
        { LoadError = TEXT("Malformed walkthrough step."); return false; }
        if (Kind == TEXT("door"))
        {
            FString DoorId; FVector Approach;
            const TArray<TSharedPtr<FJsonValue>>* Blockers = nullptr;
            if (!Step->TryGetStringField(TEXT("doorId"), DoorId) || DoorId.IsEmpty()
                || !ReadVector(Step, TEXT("approachCm"), Approach)
                || !Step->TryGetArrayField(TEXT("closedObjectIds"), Blockers) || Blockers->IsEmpty())
            { LoadError = TEXT("Door step lacks its source blocker and approach."); return false; }
            for (const auto& Blocker : *Blockers)
            {
                const FString ObjectId = Blocker->AsString();
                if (!Contract.Records.ContainsByPredicate([&](const FBreziWalkingRecord& Record) { return Record.ObjectId == ObjectId && Record.bClosed; }))
                { LoadError = TEXT("Door step blocker is absent from the source collision contract: ") + ObjectId; return false; }
            }
            if (!ReadVector(Step, TEXT("interactionPointCm"), Approach)) { LoadError = TEXT("Missing source interaction point."); return false; }
            for (const TCHAR* Field : {TEXT("retreatPathCm"), TEXT("returnPathCm")})
            {
                const TArray<TSharedPtr<FJsonValue>>* Route = nullptr;
                if (!Step->TryGetArrayField(Field, Route) || Route->IsEmpty() || Route->Num() > 40)
                { LoadError = TEXT("Missing or excessive physical interaction route."); return false; }
                for (const auto& Point : *Route)
                {
                    const auto& Components = Point->AsArray();
                    if (Components.Num() != 3 || Components.ContainsByPredicate([](const auto& C) { double N; return !C->TryGetNumber(N) || !FMath::IsFinite(N); }))
                    { LoadError = TEXT("Invalid interaction waypoint."); return false; }
                }
            }
        }
        WalkthroughSteps.Add(Step);
    }
    for (const auto& Value : *Supports)
    {
        const FString Id = Value->AsString();
        if (!Contract.Records.ContainsByPredicate([&](const FBreziWalkingRecord& Record) { return Record.ObjectId == Id && Record.bFloor; }))
        { LoadError = TEXT("Walkthrough support is not a source floor: ") + Id; return false; }
        WalkthroughSupports.Add(Id);
    }
    return true;
}

namespace
{
bool RegionContains(const TSharedPtr<FJsonObject>& Region, const FVector& Point)
{
    const TArray<TSharedPtr<FJsonValue>>* Rects = nullptr;
    if (Region->TryGetArrayField(TEXT("rectsCm"), Rects))
        for (const auto& Value : *Rects)
        {
            const auto& R = Value->AsArray();
            if (R.Num() == 4 && Point.X >= R[0]->AsNumber() && Point.Y >= R[1]->AsNumber()
                && Point.X <= R[2]->AsNumber() && Point.Y <= R[3]->AsNumber()) return true;
        }
    const TArray<TSharedPtr<FJsonValue>>* Polygon = nullptr;
    if (!Region->TryGetArrayField(TEXT("polygonCm"), Polygon) || Polygon->Num() < 3) return false;
    bool Inside = false;
    for (int32 I = 0, J = Polygon->Num() - 1; I < Polygon->Num(); J = I++)
    {
        const auto& A = (*Polygon)[I]->AsArray(); const auto& B = (*Polygon)[J]->AsArray();
        if (A.Num() != 2 || B.Num() != 2) return false;
        const double AX = A[0]->AsNumber(), AY = A[1]->AsNumber(), BX = B[0]->AsNumber(), BY = B[1]->AsNumber();
        if ((AY > Point.Y) != (BY > Point.Y) && Point.X < (BX - AX) * (Point.Y - AY) / (BY - AY) + AX) Inside = !Inside;
    }
    return Inside;
}
}

bool UBreziWalkingTraversal::SampleWalkthrough(float DeltaTime)
{
    const FVector Center = Pawn()->GetActorLocation();
    const UCharacterMovementComponent* Movement = Pawn()->GetCharacterMovement();
    const FString Support = FBreziWalkingContract::ObjectId(Movement->CurrentFloor.HitResult.GetComponent());
    const bool Grounded = Pawn()->IsWalkingMode() && Movement->IsMovingOnGround();
    const double Travel = FVector::Distance(Center, WalkthroughPriorCenter);
    WalkthroughDistanceCm += Travel; WalkthroughMaxSampleTravelCm = FMath::Max(WalkthroughMaxSampleTravelCm, Travel);
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BreziWalkthroughSample), true, Pawn());
    const bool Overlap = GetWorld()->OverlapBlockingTestByChannel(Center, FQuat::Identity, ECC_Pawn,
        FCollisionShape::MakeCapsule(Contract.CapsuleRadiusCm - 0.05, Contract.CapsuleHalfHeightCm - 0.05), Params);
    FHitResult Floor;
    const UCameraComponent* Camera = Pawn()->GetPhysicalCamera();
    const bool FloorHit = GetWorld()->LineTraceSingleByChannel(Floor, Center,
        Center - FVector(0, 0, Contract.CapsuleHalfHeightCm + Contract.MaxStepCm + 10), ECC_Pawn, Params);
    const bool EyeMeasured = Camera && FloorHit && FBreziWalkingContract::IsFloor(Floor.GetComponent());
    const double EyeError = EyeMeasured ? FMath::Abs(Camera->GetComponentLocation().Z - Floor.ImpactPoint.Z - Contract.EyeHeightCm) : 1000;
    TSharedRef<FJsonObject> Sample = MakeShared<FJsonObject>();
    Sample->SetNumberField(TEXT("step"), WalkthroughStep); Sample->SetStringField(TEXT("phase"), WalkthroughPhase);
    Sample->SetNumberField(TEXT("deltaSeconds"), DeltaTime); Sample->SetNumberField(TEXT("simulationSeconds"), WalkthroughSimulationSeconds);
    Sample->SetArrayField(TEXT("capsuleCenterCm"), VectorJson(Center)); Sample->SetNumberField(TEXT("travelCm"), Travel);
    Sample->SetArrayField(TEXT("velocityCmPerSecond"), VectorJson(Pawn()->GetVelocity()));
    Sample->SetStringField(TEXT("supportObjectId"), Support); Sample->SetBoolField(TEXT("grounded"), Grounded);
    Sample->SetBoolField(TEXT("unexpectedOverlap"), Overlap); Sample->SetNumberField(TEXT("eyeErrorCm"), EyeError);
    Sample->SetBoolField(TEXT("wInputDown"), Controller()->IsInputKeyDown(EKeys::W));
    Sample->SetBoolField(TEXT("precisionInputDown"), Controller()->IsInputKeyDown(EKeys::Q));
    TArray<TSharedPtr<FJsonValue>> Regions;
    for (const auto& Region : WalkthroughRegions) if (RegionContains(Region, Center))
    { const FString Id = Region->GetStringField(TEXT("id")); Regions.Add(MakeShared<FJsonValueString>(Id)); VisitedRegions.Add(Id); }
    Sample->SetArrayField(TEXT("regions"), Regions); PathSamples.Add(MakeShared<FJsonValueObject>(Sample));
    WalkthroughPriorCenter = Center;
    if (!Grounded || !WalkthroughSupports.Contains(Support) || Overlap || !EyeMeasured || EyeError > 0.5
        || Travel > Contract.BoostSpeed * DeltaTime + Contract.MaxStepCm + 2 || PathSamples.Num() > 120000)
    {
        FinishWalkthrough(TEXT("failed-sample"), FString::Printf(TEXT("step=%d phase=%s grounded=%d support=%s overlap=%d eyeError=%.3f travel=%.3f"),
            WalkthroughStep, *WalkthroughPhase, Grounded, *Support, Overlap, EyeError, Travel)); return false;
    }
    return true;
}

bool UBreziWalkingTraversal::DriveWalkthroughTo(const FVector& Target)
{
    const FVector Delta = Target - Pawn()->GetActorLocation();
    if (Delta.Size2D() <= 5)
    { Key(EKeys::W, false); Key(EKeys::Q, false); return Pawn()->GetVelocity().Size2D() < 1; }
    if (!Pawn()->AimWalkingTraversal(FVector(Delta.X, Delta.Y, 0)))
    { FinishWalkthrough(TEXT("failed-aim"), TEXT("Guarded walking direction could not be applied.")); return false; }
    Key(EKeys::Q, Delta.Size2D() < 80); Key(EKeys::W, true); return false;
}

bool UBreziWalkingTraversal::WalkthroughDoorSweep(FHitResult& Hit) const
{
    const FVector Center = Pawn()->GetActorLocation();
    FVector Destination = WalkthroughTarget; Destination.Z = Center.Z;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BreziWalkthroughDoor), true, Pawn());
    return GetWorld()->SweepSingleByChannel(Hit, Center, Destination, FQuat::Identity, ECC_Pawn,
        FCollisionShape::MakeCapsule(Contract.CapsuleRadiusCm, Contract.CapsuleHalfHeightCm), Params) && Hit.bBlockingHit;
}

bool UBreziWalkingTraversal::WalkthroughOpenPassage(FHitResult& Hit, TArray<FString>& StepSupports, double& RaisedByCm) const
{
    const FVector Center = Pawn()->GetActorLocation(); FVector Destination = WalkthroughTarget; Destination.Z = Center.Z;
    const auto Movement = Pawn()->GetCharacterMovement();
    const double FloorZ = Center.Z - Contract.CapsuleHalfHeightCm - Movement->CurrentFloor.GetDistanceToFloor();
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BreziWalkthroughOpenPassage), true, Pawn());
    const auto Shape = FCollisionShape::MakeCapsule(Contract.CapsuleRadiusCm, Contract.CapsuleHalfHeightCm);
    RaisedByCm = 0;
    for (int32 I = 0; I < 12; ++I)
    {
        if (!GetWorld()->SweepSingleByChannel(Hit, Center, Destination, FQuat::Identity, ECC_Pawn, Shape, Params) || !Hit.bBlockingHit)
        {
            // A horizontal capsule can hit a legal floor riser. Check head/body clearance at
            // the source step height as well; the subsequent real CMC crossing remains required.
            const FVector Lift(0, 0, RaisedByCm);
            return RaisedByCm <= 0 || !GetWorld()->SweepSingleByChannel(Hit, Center + Lift, Destination + Lift,
                FQuat::Identity, ECC_Pawn, Shape, Params) || !Hit.bBlockingHit;
        }
        const FString Id = FBreziWalkingContract::ObjectId(Hit.GetComponent());
        const auto Record = Contract.Records.FindByPredicate([&](const auto& R) { return R.ObjectId == Id && R.bFloor; });
        if (Hit.bStartPenetrating || !Record || !FBreziWalkingContract::IsFloor(Hit.GetComponent())
            || !WalkthroughSupports.Contains(Id)
            || Contract.Records.ContainsByPredicate([&](const auto& R) { return R.ObjectId == Id && R.bClosed; })) return false;
        const double Top = Record->BoundsCm.Max.Z + Record->SupportOffsetCm;
        if (Top < FloorZ - Contract.MaxDropCm || Top > FloorZ + Contract.MaxStepCm) return false;
        RaisedByCm = FMath::Max(RaisedByCm, FMath::Max(0.0, Top - FloorZ));
        StepSupports.AddUnique(Id); Params.AddIgnoredComponent(Hit.GetComponent());
    }
    return false;
}

void UBreziWalkingTraversal::NextWalkthroughStep()
{
    Key(EKeys::W, false); Key(EKeys::Q, false);
    ++WalkthroughStep; WalkthroughStepSeconds = 0; WalkthroughPhaseSeconds = 0; WalkthroughPhase = TEXT("step"); WalkthroughDoorCycle = 0;
    if (!SaveWalkthrough(TEXT("running"))) FinishWalkthrough(TEXT("failed-report-write"));
}

void UBreziWalkingTraversal::TickWalkthrough(float DeltaTime)
{
    if (FPlatformTime::Seconds() - RunStartWallSeconds > 1500 || WalkthroughSimulationSeconds > 900)
    { FinishWalkthrough(TEXT("failed-timeout"), TEXT("Bounded walkthrough time limit exceeded.")); return; }
    ABreziPlayerController* PC = Cast<ABreziPlayerController>(Controller());
    if (!Pawn() || !PC || !PC->GetDoorSystem())
    { if (FPlatformTime::Seconds() - RunStartWallSeconds > 20) FinishWalkthrough(TEXT("failed-startup"), TEXT("Player or door system unavailable.")); return; }
    if (!bWalkthroughStarted)
    {
        if (!PC->GetDoorSystem()->GetDiagnostics()->GetBoolField(TEXT("ready")))
        { FinishWalkthrough(TEXT("failed-door-initialization")); return; }
        if (!bWalkthroughAutomationStarted)
        {
            if (!PC->BeginWalkthroughAutomation()) { FinishWalkthrough(TEXT("failed-automation-startup")); return; }
            bWalkthroughAutomationStarted = true;
        }
        if (!Pawn()->PrepareTraversalAuditView(WalkthroughStartEye, WalkthroughStartForward))
        { if (FPlatformTime::Seconds() - RunStartWallSeconds > 20) FinishWalkthrough(TEXT("failed-viewpoint-startup")); return; }
        ++WalkthroughInitialPlacements; bWalkthroughStarted = true;
        AddTickPrerequisiteActor(Pawn()); AddTickPrerequisiteComponent(Pawn()->GetCharacterMovement());
        for (const auto& Step : WalkthroughSteps) if (Step->GetStringField(TEXT("kind")) == TEXT("door"))
            PC->GetDoorSystem()->SetOpen(Step->GetStringField(TEXT("doorId")), false);
        WalkthroughPhase = TEXT("warmup"); WalkthroughPhaseSeconds = 0;
    }
    WalkthroughPhaseSeconds += DeltaTime; WalkthroughSimulationSeconds += DeltaTime;
    if (WalkthroughPhase == TEXT("warmup"))
    {
        if (WalkthroughPhaseSeconds >= 1.5)
        { Key(EKeys::M, true); Key(EKeys::M, false); WalkthroughPhase = TEXT("enter"); WalkthroughPhaseSeconds = 0; }
        return;
    }
    if (WalkthroughPhase == TEXT("enter"))
    {
        if (WalkthroughPhaseSeconds < 0.3) return;
        if (!Pawn()->IsWalkingMode()) { FinishWalkthrough(TEXT("failed-entry"), TEXT("M did not enter source walking.")); return; }
        if (!Pawn()->IsNavigating()) { Key(EKeys::F2, true); Key(EKeys::F2, false); }
        WalkthroughPhase = TEXT("navigate"); WalkthroughPhaseSeconds = 0; return;
    }
    if (WalkthroughPhase == TEXT("navigate"))
    {
        if (WalkthroughPhaseSeconds < 0.2) return;
        if (!Pawn()->IsNavigating() || !PC->IsNavigationInputActive() || !PC->IsWalkthroughAutomationActive()) { FinishWalkthrough(TEXT("failed-navigation")); return; }
        if (FParse::Param(FCommandLine::Get(), TEXT("BreziPresentationQA")))
        {
            PresentationQA = NewObject<UBreziPresentationQA>(this);
            if (!PresentationQA->Begin(PC)) { FinishWalkthrough(TEXT("failed-presentation"), PresentationQA->GetFailure()); return; }
            WalkthroughPhase = TEXT("presentation-startup"); WalkthroughPhaseSeconds = 0; return;
        }
        WalkthroughPriorCenter = Pawn()->GetActorLocation(); WalkthroughPhase = TEXT("step"); WalkthroughPhaseSeconds = 0;
    }
    if (WalkthroughPhase == TEXT("presentation-startup"))
    {
        if (!PresentationQA->TickStartup(DeltaTime)) return;
        if (PresentationQA->HasFailed()) { FinishWalkthrough(TEXT("failed-presentation"), PresentationQA->GetFailure()); return; }
        WalkthroughPriorCenter = Pawn()->GetActorLocation(); WalkthroughPhase = TEXT("step");
        WalkthroughPhaseSeconds = 0; WalkthroughStepSeconds = 0;
    }
    if (PresentationQA && !PresentationQA->Sample())
    { FinishWalkthrough(TEXT("failed-presentation"), PresentationQA->GetFailure()); return; }
    WalkthroughStepSeconds += DeltaTime;
    if (!SampleWalkthrough(DeltaTime)) return;
    if (WalkthroughStep >= WalkthroughSteps.Num())
    {
        TSet<FString> ExpectedDoors;
        for (const auto& Step : WalkthroughSteps) if (Step->GetStringField(TEXT("kind")) == TEXT("door")) ExpectedDoors.Add(Step->GetStringField(TEXT("doorId")));
        if (VisitedRegions.Num() != WalkthroughRegions.Num() || OpenedDoors.Num() != ExpectedDoors.Num() || WalkthroughInitialPlacements != 1)
            FinishWalkthrough(TEXT("failed-coverage"));
        else if (PresentationQA && !PresentationQA->Finish()) FinishWalkthrough(TEXT("failed-presentation"), PresentationQA->GetFailure());
        else FinishWalkthrough(TEXT("passed-continuous-walkthrough"));
        return;
    }
    if (WalkthroughStepSeconds > 35) { FinishWalkthrough(TEXT("failed-stalled-step"), FString::FromInt(WalkthroughStep)); return; }
    const auto Step = WalkthroughSteps[WalkthroughStep]; const FString Kind = Step->GetStringField(TEXT("kind"));
    ReadVector(Step, TEXT("targetCm"), WalkthroughTarget);
    if (Kind == TEXT("visit"))
    {
        const FString Id = Step->GetStringField(TEXT("regionId"));
        const auto Region = WalkthroughRegions.FindByPredicate([&](const auto& Candidate) { return Candidate->GetStringField(TEXT("id")) == Id; });
        if (!Region || !RegionContains(*Region, Pawn()->GetActorLocation()) || FVector::Dist2D(Pawn()->GetActorLocation(), WalkthroughTarget) > 8)
        { FinishWalkthrough(TEXT("failed-room-visit"), Id); return; }
        if (WalkthroughPhase == TEXT("step"))
        {
            TSharedRef<FJsonObject> Event = MakeShared<FJsonObject>(); Event->SetStringField(TEXT("kind"), TEXT("region-visited"));
            Event->SetStringField(TEXT("regionId"), Id); Event->SetNumberField(TEXT("step"), WalkthroughStep);
            Event->SetArrayField(TEXT("capsuleCenterCm"), VectorJson(Pawn()->GetActorLocation())); WalkthroughEvents.Add(MakeShared<FJsonValueObject>(Event));
            if (!bWalkthroughScreenshots || WalkthroughCapturedRegions.Contains(Id)) { NextWalkthroughStep(); return; }
            Key(EKeys::W, false); Key(EKeys::Q, false);
            WalkthroughPhase = TEXT("visit-capture-settle"); WalkthroughPhaseSeconds = 0; return;
        }
        if (WalkthroughPhase == TEXT("visit-capture-settle"))
        {
            if (WalkthroughPhaseSeconds < 0.3 || Pawn()->GetVelocity().Size2D() >= 1) return;
            if (!GEngine || !GEngine->GameViewport || !GEngine->GameViewport->Viewport)
            { FinishWalkthrough(TEXT("failed-capture-viewport"), Id); return; }
            WalkthroughRequestedPixels = GEngine->GameViewport->Viewport->GetSizeXY();
            if (WalkthroughRequestedPixels.X <= 0 || WalkthroughRequestedPixels.Y <= 0)
            { FinishWalkthrough(TEXT("failed-capture-viewport-size"), Id); return; }
            WalkthroughCaptureRegion = Id;
            WalkthroughCapturePath = FPaths::Combine(FPaths::GetPath(ReportPath), TEXT("region-") + FPaths::MakeValidFileName(Id) + TEXT(".png"));
            bWalkthroughCapturePending = true; bWalkthroughCaptureSaved = false; WalkthroughCapturePixels = FIntPoint::ZeroValue;
            WalkthroughCaptureStartWall = FPlatformTime::Seconds();
            FScreenshotRequest::RequestScreenshot(WalkthroughCapturePath, false, false, false, FIntRect(), true);
            WalkthroughPhase = TEXT("visit-capture-pending"); WalkthroughPhaseSeconds = 0; return;
        }
        if (WalkthroughPhase == TEXT("visit-capture-pending"))
        {
            if (bWalkthroughCapturePending)
            { if (FPlatformTime::Seconds() - WalkthroughCaptureStartWall > 10) FinishWalkthrough(TEXT("failed-capture-timeout"), Id); return; }
            if (!bWalkthroughCaptureSaved || WalkthroughCapturePixels != WalkthroughRequestedPixels)
            { FinishWalkthrough(TEXT("failed-capture-save-or-size"), Id); return; }
            WalkthroughCapturedRegions.Add(Id); NextWalkthroughStep(); return;
        }
        FinishWalkthrough(TEXT("failed-visit-phase"), WalkthroughPhase); return;
    }
    if (Kind == TEXT("move"))
    { if (DriveWalkthroughTo(WalkthroughTarget)) NextWalkthroughStep(); return; }
    const FString DoorId = Step->GetStringField(TEXT("doorId"));
    if (WalkthroughPhase == TEXT("step"))
    {
        FHitResult Hit; const FString HitId = WalkthroughDoorSweep(Hit) ? FBreziWalkingContract::ObjectId(Hit.GetComponent()) : FString();
        const bool Expected = Step->GetArrayField(TEXT("closedObjectIds")).ContainsByPredicate([&](const auto& V) { return V->AsString() == HitId; });
        if (!Expected || Hit.bStartPenetrating || Hit.Distance < 1)
        { FinishWalkthrough(TEXT("failed-closed-door-sweep"), DoorId + TEXT(" hit=") + HitId); return; }
        WalkthroughDoorStart = Pawn()->GetActorLocation(); WalkthroughDoorNormal = (WalkthroughTarget - WalkthroughDoorStart).GetSafeNormal2D();
        WalkthroughClosedHitDistance = Hit.Distance; WalkthroughClosedHoldSamples = 0;
        Pawn()->AimWalkingTraversal(WalkthroughDoorNormal); Key(EKeys::Q, false); Key(EKeys::W, true);
        WalkthroughPhase = TEXT("door-closed-hold"); WalkthroughPhaseSeconds = 0;
        TSharedRef<FJsonObject> Event = MakeShared<FJsonObject>(); Event->SetStringField(TEXT("kind"), TEXT("closed-door-sweep"));
        Event->SetStringField(TEXT("doorId"), DoorId); Event->SetStringField(TEXT("hitObjectId"), HitId);
        Event->SetNumberField(TEXT("hitDistanceCm"), Hit.Distance); Event->SetNumberField(TEXT("step"), WalkthroughStep);
        Event->SetObjectField(TEXT("doors"), PC->GetDoorSystem()->GetDiagnostics()); WalkthroughEvents.Add(MakeShared<FJsonValueObject>(Event));
    }
    else if (WalkthroughPhase == TEXT("door-closed-hold"))
    {
        Key(EKeys::W, true);
        if (Controller()->IsInputKeyDown(EKeys::W)) ++WalkthroughClosedHoldSamples;
        if (WalkthroughPhaseSeconds < 1.5) return;
        Key(EKeys::W, false);
        const double Progress = FVector::DotProduct(Pawn()->GetActorLocation() - WalkthroughDoorStart, WalkthroughDoorNormal);
        if (WalkthroughClosedHoldSamples < 3 || Pawn()->GetVelocity().Size2D() > 1 || Progress > WalkthroughClosedHitDistance + 0.5
            || Progress < FMath::Max(0.0, WalkthroughClosedHitDistance - 3))
        { FinishWalkthrough(TEXT("failed-closed-door-block"), DoorId); return; }
        TSharedRef<FJsonObject> Event = MakeShared<FJsonObject>(); Event->SetStringField(TEXT("kind"), TEXT("closed-door-blocked-input"));
        Event->SetStringField(TEXT("doorId"), DoorId); Event->SetNumberField(TEXT("progressCm"), Progress);
        Event->SetNumberField(TEXT("wHeldSamples"), WalkthroughClosedHoldSamples); Event->SetNumberField(TEXT("step"), WalkthroughStep);
        WalkthroughEvents.Add(MakeShared<FJsonValueObject>(Event)); WalkthroughPhase = TEXT("door-retreat"); WalkthroughPhaseSeconds = 0; WalkthroughDoorWaypoint = 0;
    }
    else if (WalkthroughPhase == TEXT("door-retreat"))
    {
        const auto& Route = Step->GetArrayField(TEXT("retreatPathCm"));
        const auto& P = Route[WalkthroughDoorWaypoint]->AsArray();
        if (!DriveWalkthroughTo(FVector(P[0]->AsNumber(), P[1]->AsNumber(), P[2]->AsNumber()))) return;
        if (++WalkthroughDoorWaypoint < Route.Num()) return;
        FVector Interaction; ReadVector(Step, TEXT("interactionPointCm"), Interaction);
        Pawn()->AimWalkingTraversal((Interaction - Pawn()->GetActorLocation()).GetSafeNormal2D());
        WalkthroughPhase = TEXT("door-aim"); WalkthroughPhaseSeconds = 0;
    }
    else if (WalkthroughPhase == TEXT("door-aim"))
    {
        if (WalkthroughPhaseSeconds < 0.2) return;
        if (PC->GetDoorSystem()->GetDiagnostics()->GetStringField(TEXT("selectedDoorId")) != DoorId)
        { FinishWalkthrough(TEXT("failed-door-selection"), DoorId); return; }
        Key(EKeys::E, true); Key(EKeys::E, false); ++WalkthroughInputOpenCount;
        WalkthroughPhase = TEXT("door-opening"); WalkthroughPhaseSeconds = 0;
    }
    else if (WalkthroughPhase == TEXT("door-opening"))
    {
        if (WalkthroughPhaseSeconds < 2) return;
        const auto Doors = PC->GetDoorSystem()->GetDiagnostics();
        const auto Found = Doors->GetArrayField(TEXT("doors")).FindByPredicate([&](const auto& Value) { return Value->AsObject()->GetStringField(TEXT("id")) == DoorId; });
        if (!Found || (*Found)->AsObject()->GetStringField(TEXT("phase")) != TEXT("OPEN")
            || (*Found)->AsObject()->GetNumberField(TEXT("progress")) != 1 || (*Found)->AsObject()->GetBoolField(TEXT("blocked")))
        {
            if (WalkthroughPhaseSeconds < 4) return;
            FinishWalkthrough(TEXT("failed-E-door-open-state"), DoorId); return;
        }
        bool ExerciseCloseReopen = false;
        WalkthroughFixture->TryGetBoolField(TEXT("exerciseCloseReopen"), ExerciseCloseReopen);
        if (ExerciseCloseReopen && WalkthroughDoorCycle == 0)
        {
            TSharedRef<FJsonObject> Event = MakeShared<FJsonObject>(); Event->SetStringField(TEXT("kind"), TEXT("E-first-open-state"));
            Event->SetStringField(TEXT("doorId"), DoorId); Event->SetNumberField(TEXT("step"), WalkthroughStep);
            Event->SetObjectField(TEXT("doors"), Doors); WalkthroughEvents.Add(MakeShared<FJsonValueObject>(Event));
            WalkthroughDoorCycle = 1; WalkthroughPhase = TEXT("door-close-aim"); WalkthroughPhaseSeconds = 0;
        }
        else { WalkthroughPhase = TEXT("door-return"); WalkthroughPhaseSeconds = 0; WalkthroughDoorWaypoint = 0; }
    }
    else if (WalkthroughPhase == TEXT("door-close-aim"))
    {
        if (WalkthroughPhaseSeconds < 0.2) return;
        if (PC->GetDoorSystem()->GetDiagnostics()->GetStringField(TEXT("selectedDoorId")) != DoorId)
        { FinishWalkthrough(TEXT("failed-close-door-selection"), DoorId); return; }
        Key(EKeys::E, true); Key(EKeys::E, false); ++WalkthroughInputCloseCount;
        WalkthroughPhase = TEXT("door-closing"); WalkthroughPhaseSeconds = 0;
    }
    else if (WalkthroughPhase == TEXT("door-closing"))
    {
        if (WalkthroughPhaseSeconds < 2) return;
        const auto Doors = PC->GetDoorSystem()->GetDiagnostics();
        const auto Found = Doors->GetArrayField(TEXT("doors")).FindByPredicate([&](const auto& Value) { return Value->AsObject()->GetStringField(TEXT("id")) == DoorId; });
        if (!Found || (*Found)->AsObject()->GetStringField(TEXT("phase")) != TEXT("CLOSED")
            || (*Found)->AsObject()->GetNumberField(TEXT("progress")) != 0 || (*Found)->AsObject()->GetNumberField(TEXT("targetProgress")) != 0
            || (*Found)->AsObject()->GetBoolField(TEXT("blocked")))
        {
            if (WalkthroughPhaseSeconds < 4) return;
            FinishWalkthrough(TEXT("failed-E-door-closed-state"), DoorId); return;
        }
        WalkthroughPhase = TEXT("door-reclosed-approach"); WalkthroughPhaseSeconds = 0;
        WalkthroughDoorWaypoint = Step->GetArrayField(TEXT("retreatPathCm")).Num() - 2;
    }
    else if (WalkthroughPhase == TEXT("door-reclosed-approach"))
    {
        // Reverse the path that was planned against the closed leaf, then probe it again.
        const auto& Route = Step->GetArrayField(TEXT("retreatPathCm"));
        const auto& P = Route[WalkthroughDoorWaypoint]->AsArray();
        if (!DriveWalkthroughTo(FVector(P[0]->AsNumber(), P[1]->AsNumber(), P[2]->AsNumber()))) return;
        if (--WalkthroughDoorWaypoint >= 0) return;
        FHitResult Hit; const FString HitId = WalkthroughDoorSweep(Hit) ? FBreziWalkingContract::ObjectId(Hit.GetComponent()) : FString();
        const bool Expected = Step->GetArrayField(TEXT("closedObjectIds")).ContainsByPredicate([&](const auto& V) { return V->AsString() == HitId; });
        if (!Expected || Hit.bStartPenetrating || Hit.Distance < 1)
        { FinishWalkthrough(TEXT("failed-reclosed-door-collision"), DoorId + TEXT(" hit=") + HitId); return; }
        TSharedRef<FJsonObject> Event = MakeShared<FJsonObject>(); Event->SetStringField(TEXT("kind"), TEXT("E-closed-source-sweep"));
        Event->SetStringField(TEXT("doorId"), DoorId); Event->SetStringField(TEXT("hitObjectId"), HitId);
        Event->SetNumberField(TEXT("hitDistanceCm"), Hit.Distance); Event->SetNumberField(TEXT("step"), WalkthroughStep);
        Event->SetObjectField(TEXT("doors"), PC->GetDoorSystem()->GetDiagnostics()); WalkthroughEvents.Add(MakeShared<FJsonValueObject>(Event));
        WalkthroughDoorCycle = 2; WalkthroughDoorWaypoint = 0;
        WalkthroughPhase = TEXT("door-retreat"); WalkthroughPhaseSeconds = 0;
    }
    else if (WalkthroughPhase == TEXT("door-return"))
    {
        const auto& Route = Step->GetArrayField(TEXT("returnPathCm"));
        const auto& P = Route[WalkthroughDoorWaypoint]->AsArray();
        if (!DriveWalkthroughTo(FVector(P[0]->AsNumber(), P[1]->AsNumber(), P[2]->AsNumber()))) return;
        if (++WalkthroughDoorWaypoint < Route.Num()) return;
        FHitResult Hit; TArray<FString> StepSupports; double RaisedByCm = 0;
        if (!WalkthroughOpenPassage(Hit, StepSupports, RaisedByCm))
        { FinishWalkthrough(TEXT("failed-open-capsule-passage"), DoorId + TEXT(" hit=") + FBreziWalkingContract::ObjectId(Hit.GetComponent())); return; }
        OpenedDoors.Add(DoorId);
        TSharedRef<FJsonObject> Event = MakeShared<FJsonObject>(); Event->SetStringField(TEXT("kind"), TEXT("E-open-passage-clear"));
        Event->SetStringField(TEXT("doorId"), DoorId); Event->SetNumberField(TEXT("step"), WalkthroughStep);
        TArray<TSharedPtr<FJsonValue>> Supports;
        for (const auto& Id : StepSupports) Supports.Add(MakeShared<FJsonValueString>(Id));
        Event->SetArrayField(TEXT("acceptedStepSupportObjectIds"), Supports); Event->SetNumberField(TEXT("preflightRaisedByCm"), RaisedByCm);
        Event->SetObjectField(TEXT("doors"), PC->GetDoorSystem()->GetDiagnostics()); WalkthroughEvents.Add(MakeShared<FJsonValueObject>(Event));
        NextWalkthroughStep();
    }
}

bool UBreziWalkingTraversal::SaveWalkthrough(const FString& Status) const
{
    TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetNumberField(TEXT("schemaVersion"), 1); Root->SetStringField(TEXT("status"), Status);
    Root->SetStringField(TEXT("recordedAtUtc"), FDateTime::UtcNow().ToIso8601()); Root->SetStringField(TEXT("sceneSha256"), SceneSha256);
    Root->SetStringField(TEXT("error"), LoadError); Root->SetNumberField(TEXT("completedSteps"), WalkthroughStep);
    Root->SetNumberField(TEXT("initialPlacements"), WalkthroughInitialPlacements); Root->SetNumberField(TEXT("inputOpenCount"), WalkthroughInputOpenCount);
    Root->SetNumberField(TEXT("inputCloseCount"), WalkthroughInputCloseCount);
    Root->SetBoolField(TEXT("screenshotsRequested"), bWalkthroughScreenshots); Root->SetArrayField(TEXT("screenshots"), WalkthroughScreenshots);
    Root->SetBoolField(TEXT("screenshotPending"), bWalkthroughCapturePending);
    if (bWalkthroughCapturePending) Root->SetStringField(TEXT("pendingScreenshotPath"), WalkthroughCapturePath);
    Root->SetStringField(TEXT("automatedInputMode"), TEXT("background-engine-bindings-without-os-capture"));
    Root->SetBoolField(TEXT("automationStarted"), bWalkthroughAutomationStarted); Root->SetBoolField(TEXT("foregroundCaptureVerified"), false);
    Root->SetNumberField(TEXT("wallSeconds"), FPlatformTime::Seconds() - RunStartWallSeconds);
    Root->SetNumberField(TEXT("simulationSeconds"), WalkthroughSimulationSeconds); Root->SetNumberField(TEXT("distanceCm"), WalkthroughDistanceCm);
    Root->SetNumberField(TEXT("maximumSampleTravelCm"), WalkthroughMaxSampleTravelCm);
    Root->SetStringField(TEXT("phase"), WalkthroughPhase); Root->SetArrayField(TEXT("path"), PathSamples); Root->SetArrayField(TEXT("events"), WalkthroughEvents);
    TArray<TSharedPtr<FJsonValue>> Rooms, Doors;
    for (const FString& Id : VisitedRegions) Rooms.Add(MakeShared<FJsonValueString>(Id));
    for (const FString& Id : OpenedDoors) Doors.Add(MakeShared<FJsonValueString>(Id));
    Root->SetArrayField(TEXT("visitedRegions"), Rooms); Root->SetArrayField(TEXT("openedDoors"), Doors);
    if (PresentationQA) Root->SetObjectField(TEXT("presentationQA"), PresentationQA->GetDiagnostics());
    if (WalkthroughFixture.IsValid()) Root->SetObjectField(TEXT("fixture"), WalkthroughFixture);
    if (Pawn()) Root->SetObjectField(TEXT("walking"), Pawn()->GetWalkingDiagnostics());
    if (const auto PC = Cast<ABreziPlayerController>(Controller()); PC && PC->GetDoorSystem()) Root->SetObjectField(TEXT("doors"), PC->GetDoorSystem()->GetDiagnostics());
    Root->SetStringField(TEXT("inputMethod"), TEXT("Explicit background QA lifecycle with engine M/F2/W/Q/E bindings, guarded yaw-only aiming and real CharacterMovement ticks. No OS mouse capture, Slate focus changes or foreground-behavior claim. One initial disabled-capsule placement. Closed doors are reset only before walking; all openings use E. No position writes after initial entry."));
    Root->SetStringField(TEXT("scope"), TEXT("Required source rooms, terraces, approaches and architectural doors along one continuous recorded capsule path. Physical support, eye and overlap samples and closed-input/open-passage door observations. No native macOS keyboard, visual quality, frame-rate or unrestricted exploration certification."));
    FString Text; FJsonSerializer::Serialize(Root, TJsonWriterFactory<>::Create(&Text));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(ReportPath), true);
    const FString Temporary = ReportPath + TEXT(".tmp");
    return FFileHelper::SaveStringToFile(Text, *Temporary, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)
        && IFileManager::Get().Move(*ReportPath, *Temporary, true, false, false, true);
}

void UBreziWalkingTraversal::FinishWalkthrough(const FString& Status, const FString& Error)
{
    if (bFinished) return;
    ReleaseKeys(); LoadError = Error; bFinished = true; SetComponentTickEnabled(false);
    UGameViewportClient::OnScreenshotCaptured().Remove(WalkthroughScreenshotHandle);
    if (const auto PC = Cast<ABreziPlayerController>(Controller()); PC && bWalkthroughAutomationStarted) PC->EndWalkthroughAutomation();
    const bool Saved = SaveWalkthrough(Status);
    UE_LOG(LogTemp, Display, TEXT("BreziWalkthrough status=%s saved=%d step=%d path=%s error=%s"), *Status, Saved, WalkthroughStep, *ReportPath, *Error);
    if (FParse::Param(FCommandLine::Get(), TEXT("BreziTraversalExit")))
        FPlatformMisc::RequestExitWithStatus(false, Saved && Status == TEXT("passed-continuous-walkthrough") ? 0 : 1);
}

void UBreziWalkingTraversal::OnWalkthroughScreenshot(int32 Width, int32 Height, const TArray<FColor>& Bitmap)
{
    if (!bWalkthroughCapturePending || bFinished || Width <= 0 || Height <= 0 || static_cast<int64>(Width) * Height != Bitmap.Num()) return;
    WalkthroughCapturePixels = FIntPoint(Width, Height);
    bWalkthroughCaptureSaved = FImageUtils::SaveImageByExtension(*WalkthroughCapturePath, FImageView(Bitmap.GetData(), Width, Height))
        && IFileManager::Get().FileSize(*WalkthroughCapturePath) > 0;
    TSharedRef<FJsonObject> Capture = MakeShared<FJsonObject>();
    Capture->SetStringField(TEXT("regionId"), WalkthroughCaptureRegion); Capture->SetStringField(TEXT("path"), WalkthroughCapturePath);
    Capture->SetBoolField(TEXT("saved"), bWalkthroughCaptureSaved); Capture->SetNumberField(TEXT("step"), WalkthroughStep);
    Capture->SetStringField(TEXT("recordedAtUtc"), FDateTime::UtcNow().ToIso8601());
    Capture->SetArrayField(TEXT("pixels"), {MakeShared<FJsonValueNumber>(Width), MakeShared<FJsonValueNumber>(Height)});
    Capture->SetArrayField(TEXT("requestedPixels"), {MakeShared<FJsonValueNumber>(WalkthroughRequestedPixels.X), MakeShared<FJsonValueNumber>(WalkthroughRequestedPixels.Y)});
    Capture->SetArrayField(TEXT("capsuleCenterCm"), VectorJson(Pawn()->GetActorLocation()));
    if (const auto Camera = Pawn()->GetPresentationCamera())
    { Capture->SetArrayField(TEXT("cameraEyeCm"), VectorJson(Camera->GetComponentLocation())); Capture->SetArrayField(TEXT("cameraForward"), VectorJson(Camera->GetForwardVector())); }
    Capture->SetStringField(TEXT("kind"), TEXT("current-scene-render-target-preserving-view-history"));
    WalkthroughScreenshots.Add(MakeShared<FJsonValueObject>(Capture)); bWalkthroughCapturePending = false;
}

void UBreziWalkingTraversal::EndPlay(const EEndPlayReason::Type Reason)
{
    if (bEnabled && !bFinished)
    {
        if (bWalkthrough) FinishWalkthrough(TEXT("interrupted")); else FinishRun(TEXT("interrupted"));
    }
    Super::EndPlay(Reason);
}
