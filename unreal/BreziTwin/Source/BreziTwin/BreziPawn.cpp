#include "BreziPawn.h"
#include "BreziPlayerController.h"
#include "BreziCharacterMovementComponent.h"
#include "BreziNavigationPolicy.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "PhysicsEngine/BodyInstance.h"
#include "PhysicsEngine/BodySetup.h"
#include "Components/CapsuleComponent.h"
#include "Components/InputComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Engine/Engine.h"
#include "Misc/AutomationTest.h"
#endif

#define LOCTEXT_NAMESPACE "BreziWalking"

namespace
{
    bool ReadVector(const TSharedPtr<FJsonObject>& Object, const TCHAR* Field, FVector& Out)
    {
        const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
        if (!Object->TryGetArrayField(Field, Values) || Values->Num() != 3) return false;
        double Components[3];
        for (int32 Index = 0; Index < 3; ++Index)
        {
            if (!(*Values)[Index]->TryGetNumber(Components[Index]) || !FMath::IsFinite(Components[Index])) return false;
        }
        Out = FVector(Components[0], Components[1], Components[2]);
        return true;
    }
}

void ABreziPawn::LoadViewpoints()
{
    FString Json;
    const FString Path = FPaths::ProjectContentDir() / TEXT("Data/viewpoints.json");
    TSharedPtr<FJsonObject> Root;
    if (!FFileHelper::LoadFileToString(Json, *Path) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), Root) || !Root.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("Březí: missing or malformed canonical viewpoint data: %s"), *Path);
        return;
    }
    FString Coordinates;
    const TArray<TSharedPtr<FJsonValue>>* Views = nullptr;
    if (!Root->TryGetStringField(TEXT("coordinateSystem"), Coordinates) || Coordinates != TEXT("unreal-centimeters") || !Root->TryGetArrayField(TEXT("views"), Views))
    {
        UE_LOG(LogTemp, Error, TEXT("Březí: viewpoint contract requires unreal-centimeters coordinates and views array."));
        return;
    }
    TSet<FString> SeenIds;
    for (const TSharedPtr<FJsonValue>& Value : *Views)
    {
        const TSharedPtr<FJsonObject>* Object = nullptr;
        FBreziViewpoint View;
        if (!Value->TryGetObject(Object) || !Object->IsValid()
            || !(*Object)->TryGetStringField(TEXT("id"), View.Id) || View.Id.IsEmpty() || SeenIds.Contains(View.Id)
            || !(*Object)->TryGetStringField(TEXT("label"), View.Label)
            || !ReadVector(*Object, TEXT("eyeCm"), View.EyeCm) || !ReadVector(*Object, TEXT("targetCm"), View.TargetCm)
            || View.EyeCm.Equals(View.TargetCm, 0.1))
        {
            UE_LOG(LogTemp, Warning, TEXT("Březí: rejected invalid or duplicate viewpoint."));
            continue;
        }
        double Fov = 75.0;
        (*Object)->TryGetNumberField(TEXT("horizontalFovDegrees"), Fov);
        if (!FMath::IsFinite(Fov) || Fov < 15.0 || Fov > 120.0)
        {
            UE_LOG(LogTemp, Warning, TEXT("Březí: rejected viewpoint with invalid FOV: %s"), *View.Id);
            continue;
        }
        View.HorizontalFovDegrees = static_cast<float>(Fov);
        // Room arrivals are authored safe standing points; overview views remain optional.
        View.bWalking = View.Id == TEXT("interior") || View.Id.StartsWith(TEXT("room-"));
        (*Object)->TryGetBoolField(TEXT("walking"), View.bWalking);
        SeenIds.Add(View.Id);
        Viewpoints.Add(MoveTemp(View));
    }
    if (!Root->TryGetStringField(TEXT("defaultView"), ActiveViewId) || !SeenIds.Contains(ActiveViewId))
    {
        ActiveViewId = Viewpoints.IsEmpty() ? FString() : Viewpoints[0].Id;
    }
    UE_LOG(LogTemp, Display, TEXT("Březí: loaded %d canonical viewpoints."), Viewpoints.Num());
}

ABreziPawn::ABreziPawn(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer.SetDefaultSubobjectClass<UBreziCharacterMovementComponent>(ACharacter::CharacterMovementComponentName))
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickGroup = TG_PrePhysics;
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("ArchitectureCamera"));
    Camera->SetupAttachment(GetCapsuleComponent());
    Camera->FieldOfView = 75;
    Camera->bConstrainAspectRatio = false;
    Camera->bUsePawnControlRotation = false;
    // A clean architectural lens keeps bright fixtures from veiling the room.
    Camera->PostProcessSettings.bOverride_BloomIntensity = true;
    Camera->PostProcessSettings.BloomIntensity = 0.0f;
    // Keep day and night adaptation inside the fixed EV 6 cached-lighting range.
    Camera->PostProcessSettings.bOverride_AutoExposureMinBrightness = true;
    Camera->PostProcessSettings.AutoExposureMinBrightness = -6.0f;
    Camera->PostProcessSettings.bOverride_AutoExposureMaxBrightness = true;
    Camera->PostProcessSettings.AutoExposureMaxBrightness = 14.0f;
    AvatarCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("AvatarPresentationCamera"));
    AvatarCamera->SetupAttachment(GetCapsuleComponent());
    AvatarCamera->bAutoActivate = false;
    AvatarCamera->bUsePawnControlRotation = false;
    AvatarCamera->bConstrainAspectRatio = false;
    bUseControllerRotationPitch = false;
    bUseControllerRotationYaw = false;
    bUseControllerRotationRoll = false;
    GetCapsuleComponent()->SetCollisionProfileName(TEXT("Pawn"));
    GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    GetCharacterMovement()->DisableMovement();
    GetMesh()->SetVisibility(false);
    GetMesh()->SetComponentTickEnabled(false);
}

UBreziCharacterMovementComponent* ABreziPawn::WalkingMovement() const
{
    return CastChecked<UBreziCharacterMovementComponent>(GetCharacterMovement());
}

void ABreziPawn::BeginPlay()
{
    Super::BeginPlay();
    // Movement consumes this actor's input, then updates the eye after its scoped move commits.
    WalkingMovement()->PrimaryComponentTick.AddPrerequisite(this, PrimaryActorTick);
    FString ContractError;
    bWalkingContractLoaded = WalkingContract.Load(ContractError);
    if (bWalkingContractLoaded)
    {
        GetCapsuleComponent()->SetCapsuleSize(WalkingContract.CapsuleRadiusCm, WalkingContract.CapsuleHalfHeightCm);
        WalkingMovement()->Configure(WalkingContract);
    }
    else
    {
        WalkingWorldErrors.Add(ContractError);
        UE_LOG(LogTemp, Error, TEXT("Březí walking: %s"), *ContractError);
    }
    InitializeAvatar();
    LoadViewpoints();
    FString RequestedView;
    if (FParse::Value(FCommandLine::Get(), TEXT("BreziView="), RequestedView))
    {
        if (Viewpoints.ContainsByPredicate([&RequestedView](const FBreziViewpoint& View) { return View.Id == RequestedView; })) ActiveViewId = RequestedView;
        else UE_LOG(LogTemp, Error, TEXT("Březí: requested viewpoint does not exist: %s"), *RequestedView);
    }
    if (!Viewpoints.IsEmpty()) SelectView(ActiveViewId, true);
    bCLIWalkingPending = FParse::Param(FCommandLine::Get(), TEXT("BreziWalk"));
    bCLIAuditPending = FParse::Param(FCommandLine::Get(), TEXT("BreziWalkAudit"));
    if (ABreziPlayerController* PC = Cast<ABreziPlayerController>(GetController())) PC->RefreshInterface();
}

void ABreziPawn::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    Input->BindAxis(TEXT("MoveForward"), this, &ABreziPawn::MoveForward);
    Input->BindAxis(TEXT("MoveRight"), this, &ABreziPawn::MoveRight);
    Input->BindAxis(TEXT("MoveUp"), this, &ABreziPawn::MoveUp);
    Input->BindAxis(TEXT("LookHorizontal"), this, &ABreziPawn::LookHorizontal);
    Input->BindAxis(TEXT("LookVertical"), this, &ABreziPawn::LookVertical);
}

void ABreziPawn::ClearMovementInput()
{
    ForwardInput = RightInput = UpInput = 0;
    LookInput = FVector2D::ZeroVector;
    ConsumeMovementInputVector();
    WalkingMovement()->StopMovementImmediately();
}

void ABreziPawn::ExitWalking()
{
    if (!IsWalkingMode()) return;
    const FVector Eye = Camera->GetComponentLocation();
    const FRotator Look = Camera->GetComponentRotation();
    ClearMovementInput();
    WalkingMovement()->DisableMovement();
    SetBase(static_cast<FMovementBaseInterfaceData*>(nullptr));
    GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    CameraMode = EBreziCameraMode::Orbit;
    AvatarCamera->SetActive(false);
    Camera->SetActive(true);
    GetMesh()->SetVisibility(false);
    GetMesh()->SetComponentTickEnabled(false);
    Camera->SetRelativeLocationAndRotation(FVector::ZeroVector, FRotator::ZeroRotator);
    SetActorLocationAndRotation(Eye, Look, false, nullptr, ETeleportType::TeleportPhysics);
    OrbitRadius = FMath::Max(OrbitRadius, 200.0f);
    OrbitZoomTarget = OrbitRadius;
    OrbitTarget = Eye + Look.Vector() * OrbitRadius;
    NavigationMessage = FText::GetEmpty();
}

void ABreziPawn::SelectView(const FString& Id, bool bInstant)
{
    const FBreziViewpoint* View = Viewpoints.FindByPredicate([&Id](const FBreziViewpoint& Candidate) { return Candidate.Id == Id; });
    if (!View) return;
    if (IsFlightMode())
    {
        // A later animated preset starts along the actual flight look direction.
        OrbitTarget = Camera->GetComponentLocation() + Camera->GetForwardVector() * FMath::Max(OrbitRadius, 200.0f);
    }
    ExitWalking();
    CameraMode = EBreziCameraMode::Orbit;
    ClearMovementInput();
    NavigationMessage = FText::GetEmpty();
    ActiveViewId = Id;
    TransitionDestination = *View;
    TransitionStartEye = Camera->GetComponentLocation();
    TransitionStartTarget = OrbitTarget;
    TransitionStartFov = Camera->FieldOfView;
    TransitionElapsed = 0;
    const bool bWasTransitioning = bTransitioning;
    bTransitioning = !(bInstant || bReducedMotion);
    if (!bTransitioning)
    {
        PresetQueryReason = bReducedMotion ? TEXT("reduce-motion-immediate") : TEXT("instant-request");
        PresetQuerySourceId.Empty(); PresetQueryBlend = INDEX_NONE; PresetQueryCount = 0;
        ReleasePresetFade();
        ApplyTransitionDestination(bWasTransitioning || bReducedMotion);
        TracePresetTransition(TEXT("complete"));
        return;
    }
    const bool bObstructed = IsPresetPathObstructed(TransitionStartEye, View->EyeCm);
    TracePresetTransition(TEXT("decision"));
    if (bObstructed || PresetFade.IsActive())
    {
        // A reselect updates TransitionDestination above, including while black.
        if (!BeginOwnedPresetFade())
        {
            PresetQueryReason = TEXT("fade-unavailable-immediate-cut");
            ReleasePresetFade();
            ApplyTransitionDestination(true);
            bTransitioning = false;
            TracePresetTransition(TEXT("complete"));
        }
    }
}

void ABreziPawn::ApplyTransitionDestination(bool bCameraCut)
{
    OrbitTarget = TransitionDestination.TargetCm;
    SetActorLocationAndRotation(TransitionDestination.EyeCm,
        (TransitionDestination.TargetCm - TransitionDestination.EyeCm).Rotation());
    Camera->SetFieldOfView(TransitionDestination.HorizontalFovDegrees);
    OrbitRadius = FVector::Distance(TransitionDestination.EyeCm, OrbitTarget);
    OrbitZoomTarget = OrbitRadius;
    if (bCameraCut)
    {
        if (APlayerController* PC = Cast<APlayerController>(GetController()); PC && PC->PlayerCameraManager)
            PC->PlayerCameraManager->SetGameCameraCutThisFrame();
        TracePresetTransition(TEXT("cut-endpoint"));
    }
}

bool ABreziPawn::IsPresetPathObstructed(const FVector& Start, const FVector& End)
{
    PresetQueryReason = TEXT("clear-component-sweeps");
    PresetQuerySourceId.Empty(); PresetQueryBlend = INDEX_NONE; PresetQueryCount = 0;
    if (!GetWorld() || Start.ContainsNaN() || End.ContainsNaN())
    { PresetQueryReason = TEXT("unknown-world-or-eye"); return true; }
    if (Start.Equals(End, 0.01)) return false;
    constexpr float RadiusCm = 5; // Presentation clearance, not a full camera-frustum test.
    int32 SourceComponents = 0;
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        AActor* Actor = *It;
        if (Actor == this || Actor->IsHidden() || !Actor->ActorHasTag(TEXT("BreziGenerated"))
            || Actor->ActorHasTag(TEXT("BreziHiddenCollision")) || Actor->ActorHasTag(TEXT("BreziWalkSupportProxy"))) continue;
        TArray<UStaticMeshComponent*> Components;
        Actor->GetComponents(Components);
        for (UStaticMeshComponent* Component : Components)
        {
            if (!Component || !Component->IsRegistered() || !Component->IsVisible()
                || Component->bHiddenInGame || !Component->bRenderInMainPass
                || Component->ComponentHasTag(TEXT("BreziHiddenCollision")) || Component->ComponentHasTag(TEXT("BreziWalkSupportProxy"))) continue;
            const UStaticMesh* Mesh = Component->GetStaticMesh();
            const FString Id = FBreziWalkingContract::ObjectId(Component);
            bool bSourceId = Id.Len() == 9 && Id.StartsWith(TEXT("DOM_"));
            for (int32 Index = 4; bSourceId && Index < Id.Len(); ++Index)
                bSourceId = Id[Index] >= TEXT('0') && Id[Index] <= TEXT('9');
            // Hidden helpers and derived vegetation have no canonical geometry asset.
            if (!bSourceId || !Mesh || !Mesh->GetPathName().StartsWith(TEXT("/Game/Brezi/Geometry/"))) continue;
            ++SourceComponents;
            const FBox Bounds = Component->Bounds.GetBox().ExpandBy(RadiusCm);
            if (!Bounds.IsValid || Bounds.Min.ContainsNaN() || Bounds.Max.ContainsNaN())
            { PresetQuerySourceId = Id; PresetQueryReason = TEXT("unknown-source-bounds"); return true; }
            if (!Bounds.IsInsideOrOn(Start) && !FMath::LineBoxIntersection(Bounds, Start, End, End - Start)) continue;
            bool bAllTransparent = Component->GetNumMaterials() > 0;
            bool bMissingMaterial = Component->GetNumMaterials() == 0;
            for (int32 Slot = 0; Slot < Component->GetNumMaterials(); ++Slot)
            {
                const UMaterialInterface* Material = Component->GetMaterial(Slot);
                if (!Material) { bMissingMaterial = true; bAllTransparent = false; continue; }
                const EBlendMode Blend = Material->GetBlendMode();
                // Only explicitly transparent modes are excluded. Unknown future
                // blend modes remain conservative, as do mixed-material meshes.
                const bool bTransparent = Blend == BLEND_Translucent || Blend == BLEND_Additive
                    || Blend == BLEND_Modulate || Blend == BLEND_AlphaComposite
                    || Blend == BLEND_AlphaHoldout || Blend == BLEND_TranslucentColoredTransmittance;
                bAllTransparent &= bTransparent;
            }
            if (bAllTransparent) continue;
            PresetQuerySourceId = Id;
            if (++PresetQueryCount > 128)
            { PresetQueryReason = TEXT("unknown-query-budget"); return true; }
            if (bMissingMaterial)
            { PresetQueryReason = TEXT("unknown-source-material"); return true; }
            const UBodySetup* Body = Mesh->GetBodySetup();
            const FBodyInstance* Instance = Component->GetBodyInstance();
            if (!Body || Body->GetCollisionTraceFlag() == CTF_UseSimpleAsComplex
                || Body->bFailedToCreatePhysicsMeshes || Body->TriMeshGeometries.IsEmpty()
                || !Instance || !Instance->IsValidBodyInstance())
            {
                // NoCollision visual geometry commonly has no physics body.
                // Bounds intersection is uncertainty, never a claimed triangle hit.
                PresetQueryReason = TEXT("unknown-source-triangle-query-unavailable"); return true;
            }
            FHitResult Hit;
            // Component sweep ignores world collision response filtering; per-component
            // tests also prevent glass/helpers from hiding an opaque component behind.
            if (!Component->SweepComponent(Hit, Start, End, FQuat::Identity,
                FCollisionShape::MakeSphere(RadiusCm), true)) continue;
            int32 Section = INDEX_NONE;
            const UMaterialInterface* Material = Component->GetMaterialFromCollisionFaceIndex(Hit.FaceIndex, Section);
            if (!Material && Component->GetNumMaterials() == 1) Material = Component->GetMaterial(0);
            PresetQueryBlend = Material ? static_cast<int32>(Material->GetBlendMode()) : INDEX_NONE;
            if (Material && (Material->GetBlendMode() == BLEND_Opaque || Material->GetBlendMode() == BLEND_Masked))
                PresetQueryReason = TEXT("source-opaque-or-masked-sweep-hit");
            else
                // A translucent first face on a mixed mesh does not prove that the
                // rest of this same mesh is transparent. Do not ignore the whole mesh.
                PresetQueryReason = TEXT("unknown-hit-material-or-mixed-mesh");
            return true;
        }
    }
    PresetQuerySourceId.Empty();
    if (SourceComponents == 0) { PresetQueryReason = TEXT("unknown-source-components-missing"); return true; }
    return false;
}

bool ABreziPawn::OwnsPresetFade() const
{
    const APlayerCameraManager* Manager = PresetFadeManager.Get();
    // Do not require a still-possessing controller: EndPlay can follow unpossess.
    return Manager && Manager->bEnableFading
        && !Manager->bFadeAudio && Manager->FadeColor.Equals(FLinearColor::Black)
        && FMath::IsNearlyEqual(Manager->FadeAmount, LastOwnedFadeAlpha, 0.00001f);
}

bool ABreziPawn::BeginOwnedPresetFade()
{
    if (PresetFade.IsActive())
    {
        const APlayerController* PC = Cast<APlayerController>(GetController());
        if (!OwnsPresetFade() || !PC || PC->PlayerCameraManager != PresetFadeManager.Get()) return false;
        PresetFade.Request();
        return true;
    }
    APlayerController* PC = Cast<APlayerController>(GetController());
    APlayerCameraManager* Manager = PC ? PC->PlayerCameraManager.Get() : nullptr;
    // Never replace a fade belonging to another system, including an alpha-zero fade.
    if (!Manager || Manager->bEnableFading) return false;
    PresetFadeManager = Manager;
    LastOwnedFadeAlpha = 0;
    Manager->SetManualCameraFade(0, FLinearColor::Black, false);
    PresetFade.Request();
    return true;
}

void ABreziPawn::ReleasePresetFade()
{
    if (OwnsPresetFade()) PresetFadeManager->StopCameraFade();
    PresetFadeManager.Reset();
    PresetFade.Cancel();
    LastOwnedFadeAlpha = 0;
}

void ABreziPawn::TickPresetFade(float DeltaSeconds)
{
    const APlayerController* PC = Cast<APlayerController>(GetController());
    if (!OwnsPresetFade() || !PC || PC->PlayerCameraManager != PresetFadeManager.Get())
    {
        PresetQueryReason = TEXT("fade-ownership-lost-immediate-cut");
        ReleasePresetFade();
        ApplyTransitionDestination(true);
        bTransitioning = false;
        TracePresetTransition(TEXT("complete"));
        return;
    }
    const BreziViewTransition::Step Step = PresetFade.Advance(DeltaSeconds);
    LastOwnedFadeAlpha = Step.Alpha;
    PresetFadeManager->SetManualCameraFade(Step.Alpha, FLinearColor::Black, false);
    if (Step.Cut) ApplyTransitionDestination(true);
    if (Step.Finished)
    {
        ReleasePresetFade();
        bTransitioning = false;
        TracePresetTransition(TEXT("complete"));
    }
}

void ABreziPawn::TracePresetTransition(const TCHAR* Event)
{
    static const bool bTrace = FParse::Param(FCommandLine::Get(), TEXT("BreziTraceControlKeys"));
    if (!bTrace || PresetTraceCount >= 64) return;
    UE_LOG(LogTemp, Display, TEXT("BreziPresetTransition: event=%s sample=%d view=%s reason=%s source=%s blend=%d queries=%d eye=(%s) targetEye=(%s) fadePhase=%d alpha=%.5f ownsFade=%d"),
        Event, ++PresetTraceCount, *ActiveViewId, *PresetQueryReason, *PresetQuerySourceId, PresetQueryBlend, PresetQueryCount,
        *Camera->GetComponentLocation().ToString(), *TransitionDestination.EyeCm.ToString(),
        static_cast<int32>(PresetFade.GetPhase()), PresetFade.GetAlpha(), OwnsPresetFade());
}

void ABreziPawn::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    InterruptTransition();
    Super::EndPlay(EndPlayReason);
}

void ABreziPawn::InterruptTransition()
{
    if (bTransitioning || PresetFade.IsActive()) TracePresetTransition(TEXT("cancel"));
    ReleasePresetFade();
    bTransitioning = false;
    OrbitRadius = FVector::Distance(Camera->GetComponentLocation(), OrbitTarget);
    OrbitZoomTarget = OrbitRadius;
}

void ABreziPawn::SetNavigating(bool bEnabled)
{
    bNavigating = bEnabled;
    if (bEnabled)
    {
        ClearMovementInput();
        InterruptTransition();
    }
    else
    {
        OrbitZoomTarget = OrbitRadius;
        ClearMovementInput();
    }
}

void ABreziPawn::SetReducedMotion(bool bEnabled)
{
    bReducedMotion = bEnabled;
    if (bReducedMotion && bTransitioning) SelectView(TransitionDestination.Id, true);
    else if (bReducedMotion && CameraMode == EBreziCameraMode::Orbit)
    {
        OrbitRadius = OrbitZoomTarget;
        SetActorLocation(OrbitTarget - GetActorForwardVector() * OrbitRadius);
    }
}

void ABreziPawn::SetLookSensitivity(float Value)
{
    LookSensitivity = static_cast<float>(BreziNavigation::Sensitivity(Value));
}

bool ABreziPawn::ValidateWalkingWorld()
{
    if (!bWalkingContractLoaded)
    {
        EntryQueryStatus = TEXT("walking-contract-unavailable");
        NavigationMessage = LOCTEXT("MissingWalkingContract", "Chôdza čaká na projektové dáta. Pohľady môžete ďalej používať.");
        return false;
    }
    // Validate again on every entry so a later editor/door implementation cannot reuse stale readiness.
    bWalkingWorldValidated = WalkingContract.ValidateWorld(GetWorld(), WalkingWorldErrors);
    if (!bWalkingWorldValidated)
    {
        EntryQueryStatus = TEXT("world-collision-contract-incomplete");
        NavigationMessage = LOCTEXT("WalkingWorldIncomplete", "Podlahy a zatvorené dvere ešte nie sú pripravené na chôdzu.");
        for (int32 Index = 0; Index < FMath::Min(16, WalkingWorldErrors.Num()); ++Index)
            UE_LOG(LogTemp, Warning, TEXT("Březí walking validation: %s"), *WalkingWorldErrors[Index]);
    }
    return bWalkingWorldValidated;
}

bool ABreziPawn::FindWalkingEntry(FVector& Center, FFindFloorResult& Floor)
{
    ++EntryAttempts;
    EntrySupportId.Empty();
    EntryLineHitId.Empty();
    if (!HasViewpoints())
    {
        EntryQueryStatus = TEXT("viewpoint-data-unavailable");
        NavigationMessage = LOCTEXT("NoInitializedCamera", "Chôdza čaká na načítanie architektonických pohľadov.");
        return false;
    }
    if (!ValidateWalkingWorld()) return false;
    const FVector Eye = Camera->GetComponentLocation();
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BreziWalkingEntry), true, this);
    FHitResult Hit;
    const FVector End(Eye.X, Eye.Y, FMath::Min(WalkingContract.MinSupportZ - 10.0, Eye.Z - 10.0));
    if (!GetWorld()->LineTraceSingleByChannel(Hit, Eye, End, ECC_Pawn, Params) || !WalkingMovement()->IsWalkable(Hit))
    {
        EntryQueryStatus = TEXT("first-downward-hit-is-not-a-walk-surface");
        NavigationMessage = LOCTEXT("NoEntryFloor", "Pod týmto pohľadom nie je voľná podlaha na chôdzu. Zvoľte iný pohľad.");
        return false;
    }
    EntryLineHitId = FBreziWalkingContract::ObjectId(Hit.GetComponent());
    LastEntryFloor = Hit.ImpactPoint;
    const double FloorGap = (UCharacterMovementComponent::MIN_FLOOR_DIST + UCharacterMovementComponent::MAX_FLOOR_DIST) * 0.5;
    // CMC's floor solver can return a negative distance using its shortened overlap retry.
    // That settles the whole bottom sphere on ramps without raising the probe into a low ceiling.
    Center = FVector(Eye.X, Eye.Y, Hit.ImpactPoint.Z + WalkingContract.CapsuleHalfHeightCm + FloorGap);
    if (!WalkingMovement()->ProbeSupport(Center, WalkingContract.MaxStepCm + FloorGap + WalkingContract.ProbeHeadroomCm, Floor))
    {
        EntryQueryStatus = TEXT("no-radius-valid-support");
        NavigationMessage = LOCTEXT("NoEntryClearance", "Na tomto mieste nie je dosť priestoru na postavenie. Zvoľte iný pohľad.");
        return false;
    }
    Center.Z -= Floor.GetDistanceToFloor() - FloorGap;
    LastEntryCenter = Center;
    const FCollisionShape Capsule = FCollisionShape::MakeCapsule(WalkingContract.CapsuleRadiusCm, WalkingContract.CapsuleHalfHeightCm);
    FCollisionQueryParams CapsuleParams(SCENE_QUERY_STAT(BreziWalkingEntryCapsule), false, this);
    if (GetWorld()->OverlapBlockingTestByChannel(Center, FQuat::Identity, ECC_Pawn, Capsule, CapsuleParams)
        || !WalkingMovement()->ProbeSupport(Center, FloorGap + WalkingContract.ProbeHeadroomCm, Floor))
    {
        EntryQueryStatus = TEXT("capsule-blocked-or-no-radius-valid-support");
        NavigationMessage = LOCTEXT("NoEntryClearance", "Na tomto mieste nie je dosť priestoru na postavenie. Zvoľte iný pohľad.");
        return false;
    }
    // The full body must fit when standing; neither FindTeleportSpot nor a nearby-floor search may shift XY.
    EntrySupportId = FBreziWalkingContract::ObjectId(Floor.HitResult.GetComponent());
    EntryQueryStatus = TEXT("entry-floor-and-capsule-queries-passed");
    NavigationMessage = FText::GetEmpty();
    return true;
}

bool ABreziPawn::EnterWalking()
{
    FVector Center;
    FFindFloorResult Floor;
    if (!FindWalkingEntry(Center, Floor)) return false;
    const FRotator Look = Camera->GetComponentRotation();
    InterruptTransition();
    ClearMovementInput();
    // Reposition only after queries succeed, while collisions are still disabled.
    // This explicit camera-mode relocation is not simulated walking through the intervening scene.
    SetActorLocationAndRotation(Center, FRotator(0, Look.Yaw, 0), false, nullptr, ETeleportType::TeleportPhysics);
    Camera->SetRelativeRotation(FRotator(Look.Pitch, 0, 0));
    GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    CameraMode = EBreziCameraMode::Walking;
    AvatarFacingYaw = Look.Yaw;
    WalkingMovement()->SetMovementMode(MOVE_Walking);
    WalkingMovement()->AdoptValidatedFloor(Floor);
    ++SuccessfulEntries;
    UpdateWalkingCamera(0);
    UE_LOG(LogTemp, Display, TEXT("Březí walking entry: source=%s center=%s floor=%s, capsule radius=%.2f halfHeight=%.2f cm"),
        *EntrySupportId, *Center.ToString(), *LastEntryFloor.ToString(), WalkingContract.CapsuleRadiusCm, WalkingContract.CapsuleHalfHeightCm);
    return true;
}

bool ABreziPawn::ToggleMovementMode()
{
    if (IsWalkingMode()) { ExitWalking(); return true; }
    return EnterWalking();
}

bool ABreziPawn::SelectWalkingView(const FString& Id)
{
    if (!Viewpoints.ContainsByPredicate([&Id](const FBreziViewpoint& View) { return View.Id == Id; }))
    {
        NavigationMessage = LOCTEXT("MissingRoomArrival", "Vstup do miestnosti sa ešte nenačítal. Vyberte dostupný pohľad.");
        return false;
    }
    SetNavigating(false);
    SelectView(Id, true);
    return EnterWalking();
}

bool ABreziPawn::StartWalkingTour()
{
    // The importer authors this from the current C/B/B living-room arrival.
    // Actual floor and capsule queries still decide whether entry is permitted.
    return SelectWalkingView(TEXT("interior"));
}

bool ABreziPawn::StartFreeFlight()
{
    if (IsFlightMode()) return true;
    const FBreziViewpoint* Active = Viewpoints.FindByPredicate([this](const FBreziViewpoint& View) { return View.Id == ActiveViewId; });
    if (!HasViewpoints())
    {
        NavigationMessage = LOCTEXT("FlightLoading", "Prelet čaká na načítanie pohľadov na dom.");
        return false;
    }
    // Enter outside from the walking tour; keep an already selected exterior
    // camera unchanged so choosing flight does not reframe the user's view.
    if (IsWalkingMode() || !Active || Active->bWalking)
    {
        const FBreziViewpoint* Exterior = Viewpoints.FindByPredicate([](const FBreziViewpoint& View)
            { return View.Id == TEXT("aerial") && !View.bWalking; });
        if (!Exterior) Exterior = Viewpoints.FindByPredicate([](const FBreziViewpoint& View)
            { return View.Id == TEXT("street") && !View.bWalking; });
        if (!Exterior) Exterior = Viewpoints.FindByPredicate([](const FBreziViewpoint& View) { return !View.bWalking; });
        if (!Exterior)
        {
            NavigationMessage = LOCTEXT("FlightNoExterior", "Vonkajší pohľad ešte nie je pripravený. Skúste prelet po načítaní domu.");
            return false;
        }
        SelectView(Exterior->Id, true);
    }
    InterruptTransition();
    ClearMovementInput();
    bCLIWalkingPending = bCLIAuditPending = false;
    const FVector Eye = Camera->GetComponentLocation();
    const FRotator Look = Camera->GetComponentRotation();
    FlightBounds = BreziFlight::ForEntry({Eye.X, Eye.Y, Eye.Z});
    const BreziFlight::Position Entry = BreziFlight::Clamp({Eye.X, Eye.Y, Eye.Z}, FlightBounds);
    WalkingMovement()->DisableMovement();
    SetBase(static_cast<FMovementBaseInterfaceData*>(nullptr));
    GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    CameraMode = EBreziCameraMode::Flight;
    AvatarCamera->SetActive(false);
    Camera->SetActive(true);
    GetMesh()->SetVisibility(false);
    GetMesh()->SetComponentTickEnabled(false);
    Camera->SetRelativeLocationAndRotation(FVector::ZeroVector, FRotator::ZeroRotator);
    SetActorLocationAndRotation(FVector(Entry.X, Entry.Y, Entry.Z), Look, false, nullptr, ETeleportType::TeleportPhysics);
    NavigationMessage = FText::GetEmpty();
    UE_LOG(LogTemp, Display, TEXT("BreziFlight: started exteriorView=%s eyeCm=%s"), *ActiveViewId, *GetActorLocation().ToString());
    return true;
}

bool ABreziPawn::PrepareTraversalAuditView(const FVector& Eye, const FVector& Forward)
{
    FString ScenarioPath,ShapeMode,ShapeContract,ShapeScale;
    const TCHAR* CLI=FCommandLine::Get();
    const bool bTraversal=FParse::Value(CLI,TEXT("BreziWalkTraversal="),ScenarioPath)
        || FParse::Value(CLI,TEXT("BreziWalkthrough="),ScenarioPath);
    const bool bShape=FParse::Value(CLI,TEXT("BreziFlameShape="),ShapeMode)
        && (ShapeMode==TEXT("stills") || ShapeMode==TEXT("sequence"))
        && FParse::Value(CLI,TEXT("BreziFlameStudyContract="),ShapeContract) && !ShapeContract.IsEmpty()
        && FParse::Value(CLI,TEXT("BreziFlameStudyScale="),ShapeScale) && ShapeScale==TEXT("1");
    if ((!bTraversal && !bShape) || !HasViewpoints()
        || Eye.ContainsNaN() || Forward.ContainsNaN() || Forward.SizeSquared2D() < 0.5 || FMath::Abs(Forward.Z) > 0.001) return false;
    ExitWalking();
    SetNavigating(false);
    InterruptTransition();
    NavigationMessage = FText::GetEmpty();
    Camera->SetRelativeLocationAndRotation(FVector::ZeroVector, FRotator::ZeroRotator);
    SetActorLocationAndRotation(Eye, Forward.Rotation(), false, nullptr, ETeleportType::TeleportPhysics);
    OrbitTarget = Eye + Forward.GetSafeNormal() * 200;
    OrbitRadius = 200;
    OrbitZoomTarget = OrbitRadius;
    return true;
}

bool ABreziPawn::SetRealtimeStudyOrbit(double OffsetDegrees)
{
    if (!FParse::Param(FCommandLine::Get(), TEXT("BreziRealtimeOrbit")) || IsWalkingMode()
        || bTransitioning || PresetFade.IsActive() || bNavigating || !Camera
        || !FMath::IsFinite(OffsetDegrees) || FMath::Abs(OffsetDegrees) > 12.0) return false;
    const FBreziViewpoint* View = Viewpoints.FindByPredicate(
        [this](const FBreziViewpoint& Candidate) { return Candidate.Id == ActiveViewId; });
    if (!View) return false;
    const double Radius = FVector::Distance(View->EyeCm, View->TargetCm);
    if (!FMath::IsFinite(Radius) || Radius <= UE_SMALL_NUMBER) return false;
    // Absolute offset from the authored view, using the same orbit equation as
    // normal navigation. The caller owns cadence; this never changes any clock.
    FRotator Rotation = (View->TargetCm - View->EyeCm).Rotation();
    Rotation.Yaw += OffsetDegrees;
    OrbitTarget = View->TargetCm;
    OrbitRadius = static_cast<float>(Radius);
    OrbitZoomTarget = OrbitRadius;
    SetActorRotation(Rotation);
    SetActorLocation(OrbitTarget - Rotation.Vector() * OrbitRadius);
    Camera->SetFieldOfView(View->HorizontalFovDegrees);
    return true;
}

bool ABreziPawn::AimWalkingTraversal(const FVector& Forward)
{
    FString Scenario;
    if (!FParse::Value(FCommandLine::Get(), TEXT("BreziWalkthrough="), Scenario) || Scenario.IsEmpty()
        || !IsWalkingMode() || Forward.ContainsNaN() || Forward.SizeSquared2D() < 0.5) return false;
    const FRotator Look = Forward.Rotation();
    SetActorRotation(FRotator(0, Look.Yaw, 0));
    Camera->SetRelativeRotation(FRotator(FMath::Clamp(Look.Pitch, -87.0, 87.0), 0, 0));
    return true;
}

bool ABreziPawn::PrepareRealtimeStudyWalk(const TArray<FVector>& Points, const FString& SceneSha256)
{
    if (!FParse::Param(FCommandLine::Get(), TEXT("BreziRealtimeWalk")) || Points.Num() < 3 || Points.Num() > 32
        || !bWalkingContractLoaded || SceneSha256 != WalkingContract.SceneSha256) return false;
    const FBreziViewpoint* View = Viewpoints.FindByPredicate(
        [](const FBreziViewpoint& V) { return V.Id == TEXT("interior"); });
    if (!View || FVector::Dist2D(View->EyeCm, Points[0]) > 0.1) return false;
    for (const FVector& Point : Points) if (Point.ContainsNaN() || FMath::Abs(Point.Z) > 0.01) return false;
    // The single source arrival and floor/capsule entry happen before warmup.
    if (!StartWalkingTour()) return false;
    if (IsThirdPersonCamera()) TogglePersonCamera();
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BreziRealtimeWalkRoute), false, this);
    const FCollisionShape Shape = FCollisionShape::MakeCapsule(WalkingContract.CapsuleRadiusCm, WalkingContract.CapsuleHalfHeightCm);
    const double Z = GetActorLocation().Z;
    for (int32 Index = 0; Index < Points.Num(); ++Index)
    {
        const FVector Center(Points[Index].X, Points[Index].Y, Z);
        FFindFloorResult Floor;
        if (!WalkingMovement()->ProbeSupport(Center, WalkingContract.MaxStepCm + WalkingContract.ProbeHeadroomCm, Floor)) return false;
        if (Index > 0)
        {
            FHitResult Hit;
            const FVector Previous(Points[Index-1].X, Points[Index-1].Y, Z);
            if (GetWorld()->SweepSingleByChannel(Hit, Previous, Center, FQuat::Identity, ECC_Pawn, Shape, Params)) return false;
        }
    }
    StopRealtimeStudyWalk();
    return true;
}

bool ABreziPawn::SetRealtimeStudyWalkTarget(const FVector& Target)
{
    if (!FParse::Param(FCommandLine::Get(), TEXT("BreziRealtimeWalk")) || !IsWalkingMode()
        || bTransitioning || bNavigating || Target.ContainsNaN()) return false;
    RealtimeStudyWalkTarget = Target;
    bRealtimeStudyWalking = true;
    return true;
}

void ABreziPawn::StopRealtimeStudyWalk()
{
    bRealtimeStudyWalking = false;
    ClearMovementInput();
    if (IsWalkingMode()) WalkingMovement()->StopMovementImmediately();
}

void ABreziPawn::Zoom(float Direction)
{
    if (IsWalkingMode()) { ZoomCamera(Direction); return; }
    if (IsFlightMode())
    {
        const FVector Eye = Camera->GetComponentLocation(), Forward = Camera->GetForwardVector();
        const BreziFlight::Position Next = BreziFlight::Dolly({Eye.X, Eye.Y, Eye.Z},
            {Forward.X, Forward.Y, Forward.Z}, Direction, FlightBounds);
        SetActorLocation(FVector(Next.X, Next.Y, Next.Z));
        return;
    }
    if (!HasViewpoints() || IsWalkingMode()) return;
    if (bTransitioning || PresetFade.IsActive()) InterruptTransition();
    const float PriorRadius = OrbitRadius;
    OrbitZoomTarget = BreziNavigation::ZoomTarget(OrbitZoomTarget, Direction);
    if (bReducedMotion)
    {
        OrbitRadius = OrbitZoomTarget;
        SetActorLocation(OrbitTarget - GetActorForwardVector() * OrbitRadius);
    }
    static const bool bTrace = FParse::Param(FCommandLine::Get(), TEXT("BreziTraceControlKeys"));
    static int32 ZoomTraceCount = 0;
    if (bTrace && ZoomTraceCount < 32)
        UE_LOG(LogTemp, Display, TEXT("BreziZoom: sample=%d direction=%.0f radiusBeforeCm=%.5f radiusAfterCm=%.5f targetRadiusCm=%.5f"),
            ++ZoomTraceCount, Direction, PriorRadius, OrbitRadius, OrbitZoomTarget);
}

void ABreziPawn::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bCLIWalkingPending)
    {
        bCLIWalkingPending = false;
        bCLIAuditPending = false;
        EnterWalking();
    }
    if (bCLIAuditPending)
    {
        bCLIAuditPending = false;
        if (!IsWalkingMode()) { FVector Candidate; FFindFloorResult Floor; FindWalkingEntry(Candidate, Floor); }
    }
    if (bTransitioning && PresetFade.IsActive()) TickPresetFade(DeltaSeconds);
    else if (bTransitioning)
    {
        TransitionElapsed += DeltaSeconds;
        const float T = FMath::Clamp(TransitionElapsed / TransitionDuration, 0.0f, 1.0f);
        const float Smooth = T * T * T * (T * (T * 6 - 15) + 10);
        const FVector Eye = FMath::Lerp(TransitionStartEye, TransitionDestination.EyeCm, Smooth);
        OrbitTarget = FMath::Lerp(TransitionStartTarget, TransitionDestination.TargetCm, Smooth);
        SetActorLocationAndRotation(Eye, (OrbitTarget - Eye).Rotation());
        Camera->SetFieldOfView(FMath::Lerp(TransitionStartFov, TransitionDestination.HorizontalFovDegrees, Smooth));
        OrbitRadius = FVector::Distance(Eye, OrbitTarget);
        OrbitZoomTarget = OrbitRadius;
        bTransitioning = T < 1;
        if (!bTransitioning) TracePresetTransition(TEXT("complete"));
    }
    if (!bTransitioning && CameraMode == EBreziCameraMode::Orbit && OrbitRadius != OrbitZoomTarget)
    {
        OrbitRadius = BreziNavigation::StepZoom(OrbitRadius, OrbitZoomTarget, DeltaSeconds, bReducedMotion);
        SetActorLocation(OrbitTarget - GetActorForwardVector() * OrbitRadius);
    }
    const APlayerController* PC = Cast<APlayerController>(GetController());
    const auto Down = [PC](const FKey& Key) { return PC && PC->IsInputKeyDown(Key); };
    const bool bSystemChord = Down(EKeys::LeftControl) || Down(EKeys::RightControl)
        || (!IsFlightMode() && (Down(EKeys::LeftAlt) || Down(EKeys::RightAlt)))
        || Down(EKeys::LeftCommand) || Down(EKeys::RightCommand);
    if (bRealtimeStudyWalking && IsWalkingMode())
    {
        // Actual CMC input and collision; no camera/character translation,
        // synthetic delta, fixed timestep or time dilation in this study.
        const FVector Delta = FVector(RealtimeStudyWalkTarget.X, RealtimeStudyWalkTarget.Y, GetActorLocation().Z) - GetActorLocation();
        const double Distance = Delta.Size2D();
        const FVector Direction = Delta.GetSafeNormal2D();
        const FRotator Wanted(0, Direction.Rotation().Yaw, 0);
        SetActorRotation(FMath::RInterpConstantTo(GetActorRotation(), Wanted, DeltaSeconds, 120.0f));
        Camera->SetRelativeRotation(FRotator(-8.0f, 0, 0));
        WalkingMovement()->SetWalkingSpeed(FMath::Min(WalkingContract.NormalSpeed, FMath::Max(5.0, Distance * 3.0)));
        if (WalkingMovement()->IsMovingOnGround() && Distance > 1.0) AddMovementInput(Direction, 1.0f);
    }
    else if (bNavigating && HasViewpoints() && !bSystemChord)
    {
        // Pointer deltas are already per frame; only keyboard look rates use elapsed time.
        const float KeyboardYaw = CameraMode != EBreziCameraMode::Orbit ? 0.0f : (Down(EKeys::Right) ? 1.0f : 0.0f) - (Down(EKeys::Left) ? 1.0f : 0.0f);
        const float KeyboardPitch = CameraMode != EBreziCameraMode::Orbit ? 0.0f : (Down(EKeys::Up) ? 1.0f : 0.0f) - (Down(EKeys::Down) ? 1.0f : 0.0f);
        FRotator Rotation = Camera->GetComponentRotation();
        Rotation.Yaw += BreziNavigation::MouseDegrees(LookInput.X, LookSensitivity) + KeyboardYaw * 80.0f * FMath::Min(DeltaSeconds, 0.1f);
        Rotation.Pitch = FMath::Clamp(Rotation.Pitch + BreziNavigation::MouseDegrees(LookInput.Y, LookSensitivity)
            + KeyboardPitch * 60.0f * FMath::Min(DeltaSeconds, 0.1f), -87.0, 87.0);
        Rotation.Roll = 0;
        if (IsWalkingMode())
        {
            SetActorRotation(FRotator(0, Rotation.Yaw, 0));
            Camera->SetRelativeRotation(FRotator(Rotation.Pitch, 0, 0));
            WalkingMovement()->SetWalkingSpeed(Down(EKeys::Q) ? WalkingContract.PrecisionSpeed
                : Down(EKeys::LeftShift) || Down(EKeys::RightShift) ? WalkingContract.BoostSpeed : WalkingContract.NormalSpeed);
            if (WalkingMovement()->IsMovingOnGround())
            {
                const double Forward = BreziNavigation::MovementAxis(ForwardInput, Down(EKeys::Up), Down(EKeys::Down));
                const double Right = BreziNavigation::MovementAxis(RightInput, Down(EKeys::Right), Down(EKeys::Left));
                const FVector Desired = (GetActorForwardVector() * Forward + GetActorRightVector() * Right).GetClampedToMaxSize(1);
                AddMovementInput(Desired, 1);
            }
        }
        else if (IsFlightMode())
        {
            SetActorRotation(Rotation);
            const FVector Eye = GetActorLocation();
            const BreziFlight::Position Next = BreziFlight::Advance({Eye.X, Eye.Y, Eye.Z}, FMath::DegreesToRadians(Rotation.Yaw),
                BreziNavigation::MovementAxis(ForwardInput, Down(EKeys::Up), Down(EKeys::Down)),
                BreziNavigation::MovementAxis(RightInput, Down(EKeys::Right), Down(EKeys::Left)), UpInput, DeltaSeconds,
                Down(EKeys::LeftShift) || Down(EKeys::RightShift), Down(EKeys::LeftAlt) || Down(EKeys::RightAlt), FlightBounds);
            SetActorLocation(FVector(Next.X, Next.Y, Next.Z));
        }
        else
        {
            SetActorRotation(Rotation);
            SetActorLocation(OrbitTarget - Rotation.Vector() * OrbitRadius);
        }
    }
    else if (IsWalkingMode()) ConsumeMovementInputVector();
    LookInput = FVector2D::ZeroVector;
}

void ABreziPawn::UpdateWalkingCamera(float DeltaSeconds)
{
    if (!IsWalkingMode()) return;
    UBreziCharacterMovementComponent* Movement = WalkingMovement();
    const FVector Center = GetActorLocation();
    double LocalEyeZ = WalkingContract.EyeHeightCm - WalkingContract.CapsuleHalfHeightCm;
    if (Movement->IsMovingOnGround() && Movement->CurrentFloor.IsWalkableFloor())
    {
        // The CMC's 1.9–2.4 cm floor gap must not raise the architectural eye height.
        LocalEyeZ -= Movement->CurrentFloor.GetDistanceToFloor();
        double FloorZ = Center.Z - WalkingContract.CapsuleHalfHeightCm - Movement->CurrentFloor.GetDistanceToFloor();
        FHitResult Hit;
        FCollisionQueryParams Params(SCENE_QUERY_STAT(BreziWalkingEyeFloor), true, this);
        const FVector Start(Center.X, Center.Y, Center.Z);
        const FVector End(Center.X, Center.Y, FloorZ - WalkingContract.MaxStepCm - 5);
        if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Pawn, Params) && Movement->IsWalkable(Hit))
        {
            FloorZ = Hit.ImpactPoint.Z;
            CurrentSupportId = FBreziWalkingContract::ObjectId(Hit.GetComponent());
            LocalEyeZ = FloorZ + WalkingContract.EyeHeightCm - Center.Z;
            // Eye height is exact at rest and on ramps. No head bob or camera lag outside the capsule.
            const double TopClearance = WalkingContract.CapsuleHalfHeightCm - 2;
            LocalEyeZ = FMath::Min(LocalEyeZ, TopClearance);
            Camera->SetRelativeLocation(FVector(0, 0, LocalEyeZ));
            LastMeasuredEyeHeight = Camera->GetComponentLocation().Z - FloorZ;
            ++GroundedEyeSamples;
            MinMeasuredEyeHeight = FMath::Min(MinMeasuredEyeHeight, LastMeasuredEyeHeight);
            MaxMeasuredEyeHeight = FMath::Max(MaxMeasuredEyeHeight, LastMeasuredEyeHeight);
            MaxEyeHeightError = FMath::Max(MaxEyeHeightError, FMath::Abs(LastMeasuredEyeHeight - WalkingContract.EyeHeightCm));
            UpdateAvatarCamera(DeltaSeconds);
            return;
        }
    }
    ++UnsupportedEyeSamples;
    CurrentSupportId.Empty();
    Camera->SetRelativeLocation(FVector(0, 0, LocalEyeZ));
    UpdateAvatarCamera(DeltaSeconds);
}

TSharedRef<FJsonObject> ABreziPawn::GetWalkingDiagnostics() const
{
    const auto Vec = [](const FVector& Value) -> TArray<TSharedPtr<FJsonValue>>
    { return {MakeShared<FJsonValueNumber>(Value.X), MakeShared<FJsonValueNumber>(Value.Y), MakeShared<FJsonValueNumber>(Value.Z)}; };
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("cameraMode"), IsWalkingMode() ? TEXT("walking") : IsFlightMode() ? TEXT("flight") : TEXT("orbit"));
    Result->SetBoolField(TEXT("navigationActive"), bNavigating);
    Result->SetNumberField(TEXT("lookSensitivity"), LookSensitivity);
    Result->SetBoolField(TEXT("contractLoaded"), bWalkingContractLoaded);
    Result->SetBoolField(TEXT("worldContractValidated"), bWalkingWorldValidated);
    Result->SetStringField(TEXT("sceneSha256"), WalkingContract.SceneSha256);
    Result->SetStringField(TEXT("entryQueryStatus"), EntryQueryStatus);
    Result->SetNumberField(TEXT("entryAttempts"), EntryAttempts);
    Result->SetNumberField(TEXT("successfulEntries"), SuccessfulEntries);
    Result->SetNumberField(TEXT("expectedFloorObjects"), WalkingContract.FloorCount);
    Result->SetNumberField(TEXT("expectedOffsetObjects"), WalkingContract.OffsetCount);
    Result->SetNumberField(TEXT("expectedClosedBlockers"), WalkingContract.ClosedCount);
    Result->SetNumberField(TEXT("expectedAuxiliaryBlockers"), WalkingContract.AuxiliaryCount);
    Result->SetStringField(TEXT("sourceObjSha256"), WalkingContract.SourceObjSha256);
    Result->SetStringField(TEXT("entrySupportObjectId"), EntrySupportId);
    Result->SetStringField(TEXT("entryLineHitObjectId"), EntryLineHitId);
    Result->SetStringField(TEXT("currentSupportObjectId"), CurrentSupportId);
    Result->SetArrayField(TEXT("lastEntryCapsuleCenterCm"), Vec(LastEntryCenter));
    Result->SetArrayField(TEXT("lastEntryFloorHitCm"), Vec(LastEntryFloor));
    Result->SetArrayField(TEXT("currentCapsuleCenterCm"), Vec(GetActorLocation()));
    Result->SetArrayField(TEXT("currentCameraEyeCm"), Vec(Camera->GetComponentLocation()));
    TSharedRef<FJsonObject> Avatar = MakeShared<FJsonObject>();
    Avatar->SetStringField(TEXT("id"), TEXT("michelle"));
    Avatar->SetStringField(TEXT("status"), AvatarStatus);
    Avatar->SetBoolField(TEXT("rigReady"), bAvatarReady);
    Avatar->SetBoolField(TEXT("thirdPersonRequested"), bThirdPersonPreferred);
    Avatar->SetBoolField(TEXT("visible"), GetMesh()->IsVisible());
    Avatar->SetNumberField(TEXT("opacity"), AvatarOpacity);
    Avatar->SetBoolField(TEXT("visibilityTarget"), bAvatarVisibilityTarget);
    Avatar->SetNumberField(TEXT("animatedSamples"), AvatarAnimatedSamples);
    Avatar->SetStringField(TEXT("locomotion"), TEXT("source Michelle Idle/Walk/Run native skeletal blendspace"));
    Result->SetObjectField(TEXT("avatar"), Avatar);
    TSharedRef<FJsonObject> Presentation = MakeShared<FJsonObject>();
    Presentation->SetArrayField(TEXT("eyeCm"), Vec(GetPresentationCamera()->GetComponentLocation()));
    Presentation->SetArrayField(TEXT("forward"), Vec(GetPresentationCamera()->GetForwardVector()));
    Presentation->SetArrayField(TEXT("physicalEyeCm"), Vec(Camera->GetComponentLocation()));
    Presentation->SetNumberField(TEXT("requestedBoomCm"), DesiredBoomCm);
    Presentation->SetNumberField(TEXT("effectiveBoomCm"), EffectiveBoomCm);
    Presentation->SetNumberField(TEXT("collisionLimitCm"), LastBoomLimitCm);
    Presentation->SetNumberField(TEXT("boomSamples"), BoomSamples);
    Presentation->SetNumberField(TEXT("occludedSamples"), BoomOccludedSamples);
    Presentation->SetNumberField(TEXT("ignoredNavigationProxyComponents"), CameraNavigationProxies.Num());
    Presentation->SetStringField(TEXT("cameraProxyFilter"), TEXT("hidden actor+component tagged BreziHiddenCollision, matching COLL_ object/source tags, never a walk surface; query-only ignore"));
    Presentation->SetBoolField(TEXT("occluded"), bBoomOccluded);
    Presentation->SetBoolField(TEXT("firstPersonFallback"), bThirdPersonPreferred && EffectiveBoomCm < 55);
    Presentation->SetBoolField(TEXT("mouseLookEnabled"), bMouseLookEnabled);
    Presentation->SetStringField(TEXT("obstacleId"), BoomObstacleId);
    Presentation->SetStringField(TEXT("scope"), TEXT("Rendered lens uses a separate swept boom; physical eye and capsule retain source walking validation."));
    Result->SetObjectField(TEXT("presentationCamera"), Presentation);
    Result->SetNumberField(TEXT("capsuleRadiusCm"), WalkingContract.CapsuleRadiusCm);
    Result->SetNumberField(TEXT("capsuleHalfHeightCm"), WalkingContract.CapsuleHalfHeightCm);
    Result->SetNumberField(TEXT("expectedEyeHeightCm"), WalkingContract.EyeHeightCm);
    Result->SetNumberField(TEXT("groundedEyeSamples"), GroundedEyeSamples);
    Result->SetNumberField(TEXT("unmeasuredOrAirborneEyeSamples"), UnsupportedEyeSamples);
    if (GroundedEyeSamples > 0)
    {
        Result->SetNumberField(TEXT("lastMeasuredEyeHeightCm"), LastMeasuredEyeHeight);
        Result->SetNumberField(TEXT("minMeasuredEyeHeightCm"), MinMeasuredEyeHeight);
        Result->SetNumberField(TEXT("maxMeasuredEyeHeightCm"), MaxMeasuredEyeHeight);
        Result->SetNumberField(TEXT("maxEyeHeightErrorCm"), MaxEyeHeightError);
    }
    const UBreziCharacterMovementComponent* Movement = WalkingMovement();
    Result->SetStringField(TEXT("characterMovementMode"), Movement->GetMovementName());
    Result->SetNumberField(TEXT("supportQueries"), Movement->SupportQueryCount);
    Result->SetNumberField(TEXT("rejectedNonFloorHits"), Movement->RejectedFloorHitCount);
    Result->SetNumberField(TEXT("rejectedDropAttempts"), Movement->RejectedDropCount);
    Result->SetNumberField(TEXT("controlledVerticalDrops"), Movement->ControlledDropCount);
    Result->SetNumberField(TEXT("discardedHitchSeconds"), Movement->DiscardedHitchSeconds);
    Result->SetNumberField(TEXT("engineFloorGapCm"), Movement->CurrentFloor.IsWalkableFloor() ? Movement->CurrentFloor.GetDistanceToFloor() : 0);
    TArray<TSharedPtr<FJsonValue>> Errors;
    for (const FString& Error : WalkingWorldErrors) Errors.Add(MakeShared<FJsonValueString>(Error));
    Result->SetArrayField(TEXT("worldContractErrors"), Errors);
    Result->SetStringField(TEXT("verification"), TEXT("World validation checks serialized collision/tags and source bounds, not every traversal. Entry uses actual line/capsule queries. Eye samples use a downward source-floor hit after CharacterMovement. Walking traversal, sliding, steps and closed-door coverage still require native movement QA; an orbit-only benchmark is not walking proof."));
    return Result;
}

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBreziFreeFlightTest, "Brezi.Controls.Flight.PawnTransitions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FBreziFreeFlightTest::RunTest(const FString& Parameters)
{
    UWorld* World = nullptr;
    if (GEngine)
        for (const FWorldContext& Context : GEngine->GetWorldContexts())
            if (Context.World()) { World = Context.World(); break; }
    if (!TestNotNull(TEXT("Free-flight transition test has an initialized engine world"), World)) return false;
    FActorSpawnParameters Spawn;
    Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ABreziPawn* Pawn = World->SpawnActor<ABreziPawn>(FVector::ZeroVector, FRotator::ZeroRotator, Spawn);
    if (!TestNotNull(TEXT("Isolated free-flight pawn spawned"), Pawn)) return false;
    // This pawn has no controller/capture and uses isolated authored camera
    // fixtures. It exercises native transitions without moving the live player.
    FBreziViewpoint Street;
    Street.Id = TEXT("street"); Street.EyeCm = FVector(-650, 1620, 180); Street.TargetCm = FVector(100, 400, 180);
    FBreziViewpoint Interior;
    Interior.Id = TEXT("interior"); Interior.EyeCm = FVector(1110, -440, 165); Interior.TargetCm = FVector(630, -300, 165); Interior.bWalking = true;
    Pawn->Viewpoints = {Street, Interior};
    Pawn->SelectView(Interior.Id, true);
    TestTrue(TEXT("Free flight can start from an interior view"), Pawn->StartFreeFlight());
    TestTrue(TEXT("Interior entry selects the authored exterior arrival"), Pawn->GetActorLocation().Equals(Street.EyeCm, 0.001));
    TestTrue(TEXT("Flight disables grounded movement, capsule and avatar"), Pawn->IsFlightMode()
        && Pawn->GetCharacterMovement()->MovementMode == MOVE_None
        && Pawn->GetCapsuleComponent()->GetCollisionEnabled() == ECollisionEnabled::NoCollision
        && !Pawn->GetMesh()->IsVisible() && Pawn->GetPresentationCamera() == Pawn->Camera);
    Pawn->SetNavigating(true);
    Pawn->MoveUp(1);
    Pawn->Tick(0.05f);
    TestTrue(TEXT("Native flight tick raises the camera independently"), FMath::IsNearlyEqual(Pawn->GetActorLocation().Z, 192.0, 0.001));
    Pawn->MoveUp(-1);
    Pawn->Tick(0.05f);
    TestTrue(TEXT("Q axis lowers the native flight camera"), Pawn->GetActorLocation().Equals(Street.EyeCm, 0.001));
    Pawn->MoveUp(0);
    Pawn->MoveForward(1);
    Pawn->Tick(0.05f);
    const FVector ForwardEye = Pawn->GetActorLocation();
    TestTrue(TEXT("W axis translates the native camera horizontally"), FMath::IsNearlyEqual(FVector::Distance(ForwardEye, Street.EyeCm), 12.0, 0.001)
        && FMath::IsNearlyEqual(ForwardEye.Z, Street.EyeCm.Z, 0.001));
    Pawn->MoveForward(-1);
    Pawn->Tick(0.05f);
    TestTrue(TEXT("S axis reverses the horizontal movement"), Pawn->GetActorLocation().Equals(Street.EyeCm, 0.001));
    Pawn->MoveForward(0);
    Pawn->MoveRight(1);
    Pawn->Tick(0.05f);
    const FVector RightEye = Pawn->GetActorLocation();
    TestTrue(TEXT("D axis strafes independently of forward movement"), FMath::IsNearlyEqual(FVector::Distance(RightEye, Street.EyeCm), 12.0, 0.001)
        && FMath::Abs(FVector::DotProduct(RightEye - Street.EyeCm, ForwardEye - Street.EyeCm)) < 0.001);
    Pawn->MoveRight(-1);
    Pawn->Tick(0.05f);
    TestTrue(TEXT("A axis reverses the strafe"), Pawn->GetActorLocation().Equals(Street.EyeCm, 0.001));
    Pawn->ClearMovementInput();
    const FVector BeforeLook = Pawn->GetActorLocation();
    const FRotator PriorLook = Pawn->GetActorRotation();
    Pawn->LookHorizontal(20);
    Pawn->LookVertical(10);
    Pawn->Tick(0.05f);
    TestTrue(TEXT("Mouse look rotates in place without orbit coupling"), Pawn->GetActorLocation().Equals(BeforeLook, 0.001)
        && !Pawn->GetActorRotation().Equals(PriorLook, 0.001));
    Pawn->MoveUp(1);
    const FVector BeforeReduce = Pawn->GetActorLocation();
    Pawn->SetReducedMotion(true);
    TestTrue(TEXT("Reduce Motion retains the flight position"), Pawn->IsFlightMode() && Pawn->GetActorLocation().Equals(BeforeReduce, 0.001));
    Pawn->SetNavigating(false);
    Pawn->Tick(0.05f);
    TestTrue(TEXT("Pausing clears held vertical movement"), Pawn->GetActorLocation().Equals(BeforeReduce, 0.001));
    const FVector BeforeDolly = Pawn->GetActorLocation();
    Pawn->Zoom(1);
    TestTrue(TEXT("Flight zoom moves along the view without returning to orbit"), Pawn->IsFlightMode()
        && FMath::IsNearlyEqual(FVector::Distance(BeforeDolly, Pawn->GetActorLocation()), 132.0, 0.001));
    TestEqual(TEXT("Runtime diagnostics identify flight"), Pawn->GetWalkingDiagnostics()->GetStringField(TEXT("cameraMode")), FString(TEXT("flight")));
    Pawn->SelectView(Street.Id, true);
    TestTrue(TEXT("Selecting a preset restores orbit"), !Pawn->IsFlightMode() && !Pawn->IsWalkingMode());
    Pawn->SetActorLocation(FVector(24000, -26000, 12000));
    const FVector DistantEye = Pawn->GetActorLocation();
    TestTrue(TEXT("Exterior entry succeeds and preserves a distant current orbit pose"), Pawn->StartFreeFlight()
        && Pawn->GetActorLocation().Equals(DistantEye, 0.001));
    Pawn->Destroy();
    return true;
}
#endif

#undef LOCTEXT_NAMESPACE
