#include "BreziPawn.h"
#include "BreziPlayerController.h"
#include "BreziCharacterMovementComponent.h"
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
    Input->BindAxis(TEXT("LookHorizontal"), this, &ABreziPawn::LookHorizontal);
    Input->BindAxis(TEXT("LookVertical"), this, &ABreziPawn::LookVertical);
}

void ABreziPawn::ClearMovementInput()
{
    ForwardInput = RightInput = 0;
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
    Camera->SetRelativeLocationAndRotation(FVector::ZeroVector, FRotator::ZeroRotator);
    SetActorLocationAndRotation(Eye, Look, false, nullptr, ETeleportType::TeleportPhysics);
    OrbitRadius = FMath::Max(OrbitRadius, 200.0f);
    OrbitTarget = Eye + Look.Vector() * OrbitRadius;
    NavigationMessage = FText::GetEmpty();
}

void ABreziPawn::SelectView(const FString& Id, bool bInstant)
{
    const FBreziViewpoint* View = Viewpoints.FindByPredicate([&Id](const FBreziViewpoint& Candidate) { return Candidate.Id == Id; });
    if (!View) return;
    ExitWalking();
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
}

void ABreziPawn::SetNavigating(bool bEnabled)
{
    bNavigating = bEnabled;
    if (bEnabled) InterruptTransition();
    else ClearMovementInput();
}

void ABreziPawn::SetReducedMotion(bool bEnabled)
{
    bReducedMotion = bEnabled;
    if (bReducedMotion && bTransitioning) SelectView(TransitionDestination.Id, true);
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

bool ABreziPawn::PrepareTraversalAuditView(const FVector& Eye, const FVector& Forward)
{
    FString ScenarioPath,ShapeMode,ShapeContract,ShapeScale;
    const TCHAR* CLI=FCommandLine::Get();
    const bool bTraversal=FParse::Value(CLI,TEXT("BreziWalkTraversal="),ScenarioPath);
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
    SetActorRotation(Rotation);
    SetActorLocation(OrbitTarget - Rotation.Vector() * OrbitRadius);
    Camera->SetFieldOfView(View->HorizontalFovDegrees);
    return true;
}

void ABreziPawn::Zoom(float Direction)
{
    if (!HasViewpoints() || IsWalkingMode()) return;
    InterruptTransition();
    const float PriorRadius = OrbitRadius;
    OrbitRadius = FMath::Clamp(OrbitRadius * FMath::Pow(0.88f, Direction), 35.0f, 30000.0f);
    SetActorLocation(OrbitTarget - GetActorForwardVector() * OrbitRadius);
    static const bool bTrace = FParse::Param(FCommandLine::Get(), TEXT("BreziTraceControlKeys"));
    static int32 ZoomTraceCount = 0;
    if (bTrace && ZoomTraceCount < 32)
        UE_LOG(LogTemp, Display, TEXT("BreziZoom: sample=%d direction=%.0f radiusBeforeCm=%.5f radiusAfterCm=%.5f"),
            ++ZoomTraceCount, Direction, PriorRadius, OrbitRadius);
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
        bTransitioning = T < 1;
        if (!bTransitioning) TracePresetTransition(TEXT("complete"));
    }
    const APlayerController* PC = Cast<APlayerController>(GetController());
    const auto Down = [PC](const FKey& Key) { return PC && PC->IsInputKeyDown(Key); };
    const bool bSystemChord = Down(EKeys::LeftControl) || Down(EKeys::RightControl) || Down(EKeys::LeftAlt)
        || Down(EKeys::RightAlt) || Down(EKeys::LeftCommand) || Down(EKeys::RightCommand);
    if (bNavigating && HasViewpoints() && !bSystemChord)
    {
        // Pointer deltas are already per frame; only keyboard look rates use elapsed time.
        const float KeyboardYaw = (Down(EKeys::Right) ? 1.0f : 0.0f) - (Down(EKeys::Left) ? 1.0f : 0.0f);
        const float KeyboardPitch = (Down(EKeys::Up) ? 1.0f : 0.0f) - (Down(EKeys::Down) ? 1.0f : 0.0f);
        FRotator Rotation = Camera->GetComponentRotation();
        Rotation.Yaw += LookInput.X * 0.16f + KeyboardYaw * 80.0f * FMath::Min(DeltaSeconds, 0.1f);
        Rotation.Pitch = FMath::Clamp(Rotation.Pitch + LookInput.Y * 0.16f + KeyboardPitch * 60.0f * FMath::Min(DeltaSeconds, 0.1f), -87.0f, 87.0f);
        Rotation.Roll = 0;
        if (IsWalkingMode())
        {
            SetActorRotation(FRotator(0, Rotation.Yaw, 0));
            Camera->SetRelativeRotation(FRotator(Rotation.Pitch, 0, 0));
            WalkingMovement()->SetWalkingSpeed(Down(EKeys::Q) ? WalkingContract.PrecisionSpeed
                : Down(EKeys::LeftShift) || Down(EKeys::RightShift) ? WalkingContract.BoostSpeed : WalkingContract.NormalSpeed);
            if (WalkingMovement()->IsMovingOnGround())
            {
                const FVector Desired = (GetActorForwardVector() * ForwardInput + GetActorRightVector() * RightInput).GetClampedToMaxSize(1);
                AddMovementInput(Desired, 1);
            }
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
            return;
        }
    }
    ++UnsupportedEyeSamples;
    CurrentSupportId.Empty();
    Camera->SetRelativeLocation(FVector(0, 0, LocalEyeZ));
}

TSharedRef<FJsonObject> ABreziPawn::GetWalkingDiagnostics() const
{
    const auto Vec = [](const FVector& Value) -> TArray<TSharedPtr<FJsonValue>>
    { return {MakeShared<FJsonValueNumber>(Value.X), MakeShared<FJsonValueNumber>(Value.Y), MakeShared<FJsonValueNumber>(Value.Z)}; };
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("cameraMode"), IsWalkingMode() ? TEXT("walking") : TEXT("orbit"));
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

#undef LOCTEXT_NAMESPACE
