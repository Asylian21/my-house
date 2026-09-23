#include "BreziPawn.h"
#include "BreziAvatarPolicy.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/BlendSpace1D.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

void ABreziPawn::InitializeAvatar()
{
    // Navigation hulls can deliberately extend far above visible furniture.
    // Ignore only the authored, hidden source proxies in CAMERA queries. Their
    // Pawn collision profile and every visible mesh remain untouched.
    CameraNavigationProxies.Empty();
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        if (!It->ActorHasTag(TEXT("BreziHiddenCollision"))) continue;
        TInlineComponentArray<UPrimitiveComponent*> Components(*It);
        for (UPrimitiveComponent* Component : Components)
        {
            bool bSourceObject = false, bSource = false;
            for (const FName& Tag : Component->ComponentTags)
            {
                const FString Value = Tag.ToString();
                if (Value.StartsWith(TEXT("BreziSourceObjectId=COLL_")) && Value.Len() > 25 && It->ActorHasTag(Tag)) bSourceObject = true;
                if (Value.StartsWith(TEXT("BreziSourceId=")) && Value.Len() > 14 && It->ActorHasTag(Tag)) bSource = true;
            }
            if (BreziAvatar::IsNavigationProxy(true, Component->ComponentHasTag(TEXT("BreziHiddenCollision")),
                It->IsHidden() && Component->bHiddenInGame && !Component->IsVisible(), bSourceObject, bSource,
                Component->ComponentHasTag(TEXT("BreziWalkSurface")))) CameraNavigationProxies.Add(Component);
        }
    }
    bThirdPersonPreferred = !FParse::Param(FCommandLine::Get(), TEXT("BreziFirstPerson"));
    USkeletalMesh* Mesh = LoadObject<USkeletalMesh>(nullptr, TEXT("/Game/Brezi/Avatar/Michelle/SK_Michelle.SK_Michelle"));
    AvatarLocomotion = LoadObject<UBlendSpace1D>(nullptr, TEXT("/Game/Brezi/Avatar/Michelle/BS_Locomotion.BS_Locomotion"));
    if (!Mesh || !AvatarLocomotion || Mesh->GetSkeleton() != AvatarLocomotion->GetSkeleton())
    {
        AvatarStatus = TEXT("source-rig-or-locomotion-asset-missing");
        UE_LOG(LogTemp, Warning, TEXT("BreziAvatar: %s; physical walking remains available"), *AvatarStatus);
        return;
    }
    const FBoxSphereBounds Bounds = Mesh->GetBounds();
    const double Height = Bounds.BoxExtent.Z * 2;
    if (!FMath::IsFinite(Height) || Height < 80 || Height > 250)
    {
        AvatarStatus = TEXT("imported-rig-height-invalid");
        return;
    }
    const double Scale = 170.0 / Height;
    AvatarFloorOffsetCm = -(Bounds.Origin.Z - Bounds.BoxExtent.Z) * Scale;
    GetMesh()->SetSkeletalMeshAsset(Mesh);
    GetMesh()->SetRelativeScale3D(FVector(Scale));
    GetMesh()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    GetMesh()->SetGenerateOverlapEvents(false);
    GetMesh()->SetCanEverAffectNavigation(false);
    GetMesh()->SetCastShadow(true);
    GetMesh()->bCastHiddenShadow = true;
    GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    GetMesh()->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    GetMesh()->PlayAnimation(AvatarLocomotion, true);
    AvatarMaterial = GetMesh()->CreateDynamicMaterialInstance(0);
    bAvatarReady = true;
    AvatarStatus = TEXT("source-skeletal-rig-and-three-clips-ready");
    UE_LOG(LogTemp, Display, TEXT("BreziAvatar: Michelle ready importedHeightCm=%.3f visualHeightCm=170 scale=%.6f collision=disabled"), Height, Scale);
}

UCameraComponent* ABreziPawn::GetPresentationCamera() const
{
    return AvatarCamera && AvatarCamera->IsActive() ? AvatarCamera : Camera;
}

FVector ABreziPawn::GetPawnViewLocation() const
{
    return Camera ? Camera->GetComponentLocation() : Super::GetPawnViewLocation();
}

void ABreziPawn::GetInteractionView(FVector& Eye, FRotator& Look) const
{
    Eye = Camera->GetComponentLocation();
    Look = GetPresentationCamera()->GetComponentRotation();
}

void ABreziPawn::SetMouseLookEnabled(bool bEnabled)
{
    bMouseLookEnabled = bEnabled;
    LookInput = FVector2D::ZeroVector;
}

void ABreziPawn::ZoomCamera(float SignedSteps)
{
    if (!IsWalkingMode()) { Zoom(SignedSteps); return; }
    if (!FMath::IsFinite(SignedSteps) || SignedSteps == 0) return;
    if (!bThirdPersonPreferred && SignedSteps < 0)
    {
        bThirdPersonPreferred = true;
        DesiredBoomCm = ZoomBoomCm = EffectiveBoomCm = 0;
    }
    DesiredBoomCm = BreziAvatar::ZoomDistance(DesiredBoomCm, SignedSteps);
    if (bReducedMotion) UpdateAvatarCamera(0);
}

void ABreziPawn::TogglePersonCamera()
{
    bThirdPersonPreferred = !bThirdPersonPreferred;
    if (bThirdPersonPreferred && DesiredBoomCm < 65) DesiredBoomCm = BreziAvatar::DefaultBoomCm;
    UpdateAvatarCamera(0);
}

void ABreziPawn::RecenterCamera()
{
    if (!IsWalkingMode()) return;
    if (bAvatarReady) SetActorRotation(FRotator(0, AvatarFacingYaw, 0));
    Camera->SetRelativeRotation(FRotator::ZeroRotator);
    LookInput = FVector2D::ZeroVector;
    UpdateAvatarCamera(0);
}

void ABreziPawn::TurnFromScreen(float DeltaDegrees)
{
    if ((!IsWalkingMode() && !IsFlightMode()) || !FMath::IsFinite(DeltaDegrees)) return;
    if (IsFlightMode())
    {
        FRotator Look = GetActorRotation();
        Look.Yaw += DeltaDegrees;
        SetActorRotation(Look);
        return;
    }
    const double Yaw = GetActorRotation().Yaw + FMath::Clamp(DeltaDegrees, -180.0f, 180.0f);
    SetActorRotation(FRotator(0, Yaw, 0));
}

void ABreziPawn::UpdateAvatarCamera(float DeltaSeconds)
{
    if (!IsWalkingMode()) return;
    const FVector Eye = Camera->GetComponentLocation();
    const FRotator Look = Camera->GetComponentRotation();
    const FVector Velocity = GetVelocity();
    if (bAvatarReady)
    {
        GetMesh()->SetComponentTickEnabled(true);
        const double TargetYaw = Velocity.SizeSquared2D() > 9 ? Velocity.Rotation().Yaw : GetActorRotation().Yaw;
        const double Blend = DeltaSeconds > 0 ? 1 - FMath::Exp(-FMath::Min(DeltaSeconds, 0.1f) / 0.075f) : 1;
        AvatarFacingYaw += FMath::FindDeltaAngleDegrees(AvatarFacingYaw, TargetYaw) * Blend;
        // glTF +Z forward becomes Unreal +Y. This visual offset has no effect on the capsule.
        GetMesh()->SetWorldRotation(FRotator(0, AvatarFacingYaw - 90, 0));
        GetMesh()->SetWorldLocation(FVector(Eye.X, Eye.Y, Eye.Z - WalkingContract.EyeHeightCm + AvatarFloorOffsetCm));
        if (UAnimSingleNodeInstance* Animation = GetMesh()->GetSingleNodeInstance())
        {
            Animation->SetBlendSpacePosition(FVector(Velocity.Size2D(), 0, 0));
            ++AvatarAnimatedSamples;
        }
    }
    const bool bUseBoom = bThirdPersonPreferred && bAvatarReady;
    Camera->SetActive(!bUseBoom);
    AvatarCamera->SetActive(bUseBoom);
    if (!bUseBoom)
    {
        bAvatarVisibilityTarget = false;
        AvatarOpacity = 0;
        GetMesh()->SetVisibility(false);
        if (AvatarMaterial) AvatarMaterial->SetScalarParameterValue(TEXT("AvatarOpacity"), 0);
        return;
    }
    ZoomBoomCm = BreziAvatar::SmoothDistance(ZoomBoomCm, DesiredBoomCm, DeltaSeconds, bReducedMotion);
    const double ShoulderBlend = FMath::Clamp(ZoomBoomCm / 130.0, 0.0, 1.0);
    const FVector Offset = -Look.Vector() * ZoomBoomCm + FRotationMatrix(Look).GetUnitAxis(EAxis::Y) * (28 * ShoulderBlend)
        + FVector(0, 0, -20 * ShoulderBlend);
    const double RequestedDistance = Offset.Size();
    double Limit = RequestedDistance;
    FHitResult Hit;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(BreziAvatarCamera), true, this);
    Params.AddIgnoredComponents(CameraNavigationProxies);
    BoomObstacleId.Empty();
    bBoomOccluded = GetWorld()->SweepSingleByChannel(Hit, Eye, Eye + Offset, FQuat::Identity,
        ECC_Camera, FCollisionShape::MakeSphere(BreziAvatar::ProbeRadiusCm), Params);
    if (bBoomOccluded)
    {
        Limit = Hit.bStartPenetrating ? 0 : FMath::Max(0.0, Hit.Distance - BreziAvatar::CollisionPaddingCm);
        BoomObstacleId = FBreziWalkingContract::ObjectId(Hit.GetComponent());
        ++BoomOccludedSamples;
    }
    ++BoomSamples;
    LastBoomLimitCm = Limit;
    EffectiveBoomCm = BreziAvatar::SafeBoom(EffectiveBoomCm, RequestedDistance, Limit, DeltaSeconds, bReducedMotion);
    AvatarCamera->SetWorldLocationAndRotation(Eye + Offset.GetSafeNormal() * EffectiveBoomCm, Look);
    // Day/night and image-quality policy still has one authoritative lens. Copy
    // its current composed camera settings to the active presentation lens.
    AvatarCamera->FieldOfView = Camera->FieldOfView;
    AvatarCamera->PostProcessSettings = Camera->PostProcessSettings;
    AvatarCamera->PostProcessBlendWeight = Camera->PostProcessBlendWeight;
    bAvatarVisibilityTarget = BreziAvatar::AvatarVisibilityTarget(EffectiveBoomCm, bAvatarVisibilityTarget);
    AvatarOpacity = BreziAvatar::StepAvatarOpacity(AvatarOpacity, bAvatarVisibilityTarget, DeltaSeconds, bReducedMotion,
        EffectiveBoomCm <= BreziAvatar::FirstPersonCm);
    GetMesh()->SetVisibility(AvatarOpacity > 0.001);
    if (AvatarMaterial) AvatarMaterial->SetScalarParameterValue(TEXT("AvatarOpacity"), AvatarOpacity);
}
