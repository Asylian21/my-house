#include "BreziWalkingTraversal.h"

#include "BreziPawn.h"
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
    if (!FParse::Value(FCommandLine::Get(), TEXT("BreziWalkTraversal="), CasesPath)) return;
    bEnabled = true;
    RunStartWallSeconds = FPlatformTime::Seconds();
    bPriorFixedStep = FApp::UseFixedTimeStep();
    PriorFixedDelta = FApp::GetFixedDeltaTime();
    bPriorFixedFrameRate = GEngine && GEngine->bUseFixedFrameRate;
    PriorFixedFrameRate = GEngine ? GEngine->FixedFrameRate : 0;
    ReportPath = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Diagnostics"),
        TEXT("walking-traversal-") + FDateTime::UtcNow().ToString(TEXT("%Y%m%dT%H%M%S")) + TEXT(".json"));
    // The render benchmark has its own completion/exit state machine. Use a separate invocation.
    const TCHAR* CLI = FCommandLine::Get();
    FString Ignored;
    if (FParse::Param(CLI, TEXT("BreziCapture4K")) || FParse::Param(CLI, TEXT("BreziCaptureUI"))
        || FParse::Param(CLI, TEXT("BreziExitAfterCapture"))
        || FParse::Param(CLI, TEXT("BreziWalk")) || FParse::Param(CLI, TEXT("BreziWalkAudit"))
        || FParse::Value(CLI, TEXT("BreziBenchmarkFrames="), Ignored)
        || FParse::Param(CLI, TEXT("BreziProfileGPU")))
    {
        LoadError = TEXT("Use the traversal harness in a separate process without entry/benchmark/capture/profile flags.");
        FinishRun(TEXT("failed-arguments"));
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
    const UCameraComponent* Camera = Character->FindComponentByClass<UCameraComponent>();
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

void UBreziWalkingTraversal::EndPlay(const EEndPlayReason::Type Reason)
{
    if (bEnabled && !bFinished) FinishRun(TEXT("interrupted"));
    Super::EndPlay(Reason);
}
