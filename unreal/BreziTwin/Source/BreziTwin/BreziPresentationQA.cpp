#include "BreziPresentationQA.h"
#include "BreziAvatarPolicy.h"
#include "BreziGameViewportClient.h"
#include "BreziPawn.h"
#include "BreziPlayerController.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Input/Events.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Widgets/SViewport.h"

ABreziPawn* UBreziPresentationQA::Pawn() const
{
    return OwnerController.IsValid() ? Cast<ABreziPawn>(OwnerController->GetPawn()) : nullptr;
}

bool UBreziPresentationQA::Fail(const FString& Reason)
{
    if (Failure.IsEmpty()) Failure = Reason;
    UE_LOG(LogTemp, Error, TEXT("BreziPresentationQA: %s"), *Failure);
    return false;
}

bool UBreziPresentationQA::Begin(ABreziPlayerController* Controller)
{
    FString Fixture;
    if (bStarted || !FParse::Param(FCommandLine::Get(), TEXT("BreziPresentationQA"))
        || !FParse::Value(FCommandLine::Get(), TEXT("BreziWalkthrough="), Fixture) || Fixture.IsEmpty()
        || !Controller || !Controller->IsWalkthroughAutomationActive() || !Controller->IsNavigationInputActive())
        return Fail(TEXT("presentation QA requires the explicitly requested, already validated walking harness"));
    OwnerController = Controller;
    if (!Pawn() || !Pawn()->IsWalkingMode() || !Pawn()->IsThirdPersonCamera())
        return Fail(TEXT("presentation QA requires actual third-person walking"));
    const TSharedRef<FJsonObject> Walking = Pawn()->GetWalkingDiagnostics();
    if (!Walking->GetObjectField(TEXT("avatar"))->GetBoolField(TEXT("rigReady")))
        return Fail(TEXT("source skeletal avatar or locomotion assets are unavailable"));
    // Derive the semantic exclusion afresh from live world tags and visibility,
    // independently of the pawn cache or its reported/measured collision limit.
    for (TActorIterator<AActor> It(Pawn()->GetWorld()); It; ++It)
    {
        if (!It->ActorHasTag(TEXT("BreziHiddenCollision")) || !It->IsHidden()) continue;
        TInlineComponentArray<UPrimitiveComponent*> Components(*It);
        for (UPrimitiveComponent* Component : Components)
        {
            if (!Component->ComponentHasTag(TEXT("BreziHiddenCollision")) || !Component->bHiddenInGame
                || Component->IsVisible() || Component->ComponentHasTag(TEXT("BreziWalkSurface"))) continue;
            bool SourceObject = false, Source = false;
            for (const FName& Tag : Component->ComponentTags)
            {
                const FString Value = Tag.ToString();
                SourceObject |= Value.StartsWith(TEXT("BreziSourceObjectId=COLL_")) && Value.Len() > 25 && It->ActorHasTag(Tag);
                Source |= Value.StartsWith(TEXT("BreziSourceId=")) && Value.Len() > 14 && It->ActorHasTag(Tag);
            }
            if (SourceObject && Source) IndependentNavigationProxies.Add(Component);
        }
    }
    if (Walking->GetObjectField(TEXT("presentationCamera"))->GetNumberField(TEXT("ignoredNavigationProxyComponents")) != IndependentNavigationProxies.Num())
        return Fail(TEXT("camera navigation-proxy exclusions differ from independent world classification"));
    InitialCapsule = Pawn()->GetActorLocation();
    InitialZoomCm = Walking->GetObjectField(TEXT("presentationCamera"))->GetNumberField(TEXT("requestedBoomCm"));
    bStarted = true;
    return true;
}

bool UBreziPresentationQA::SendZoomEvent(int32 Index)
{
    UBreziGameViewportClient* Viewport = GEngine ? Cast<UBreziGameViewportClient>(GEngine->GameViewport) : nullptr;
    const TSharedPtr<SViewport> Widget = Viewport ? Viewport->GetGameViewportWidget() : nullptr;
    if (!Widget.IsValid() || !Viewport->IsPresentationReadyForCurrentOutput()) return Fail(TEXT("owned presentation viewport is unavailable"));
    const FGeometry& Geometry = Widget->GetCachedGeometry();
    const FVector2D Position = Geometry.LocalToAbsolute(Geometry.GetLocalSize() * .5f);
    const TSet<FKey> Buttons;
    const FModifierKeysState Modifiers;
    const double Before = Pawn()->GetWalkingDiagnostics()->GetObjectField(TEXT("presentationCamera"))->GetNumberField(TEXT("requestedBoomCm"));
    bool Handled = false;
    FString Kind;
    if (Index < 4)
    {
        const bool Magnify = Index < 2;
        Kind = Magnify ? TEXT("magnify") : TEXT("two-finger-scroll");
        const FVector2D Delta = Magnify ? FVector2D(Index == 0 ? .2 : -1. / 6., 0) : FVector2D(0, Index == 2 ? 12 : -12);
        const FPointerEvent Event(Position, Position, Buttons, Modifiers,
            Magnify ? EGestureEvent::Magnify : EGestureEvent::Scroll, EGesturePhase::Update, Delta, false);
        Handled = Widget->OnTouchGesture(Geometry, Event).IsEventHandled();
    }
    else
    {
        Kind = TEXT("mouse-wheel");
        const FPointerEvent Event(0, Position, Position, Buttons, FKey(), Index == 4 ? 1 : -1, Modifiers);
        Handled = Widget->OnMouseWheel(Geometry, Event).IsEventHandled();
    }
    const double After = Pawn()->GetWalkingDiagnostics()->GetObjectField(TEXT("presentationCamera"))->GetNumberField(TEXT("requestedBoomCm"));
    TSharedRef<FJsonObject> Event = MakeShared<FJsonObject>();
    Event->SetStringField(TEXT("kind"), Kind); Event->SetBoolField(TEXT("handledByOwnedViewport"), Handled);
    Event->SetNumberField(TEXT("beforeCm"), Before); Event->SetNumberField(TEXT("afterCm"), After);
    Event->SetNumberField(TEXT("capsuleTravelCm"), FVector::Distance(InitialCapsule, Pawn()->GetActorLocation()));
    Events.Add(MakeShared<FJsonValueObject>(Event));
    if (!Handled || (Index % 2 == 0 ? After >= Before : After <= Before)) return Fail(TEXT("viewport zoom gesture did not change the requested distance in the expected direction"));
    if (FVector::Distance(InitialCapsule, Pawn()->GetActorLocation()) > .05) return Fail(TEXT("zoom input moved the physical capsule"));
    return true;
}

bool UBreziPresentationQA::TickStartup(float DeltaSeconds)
{
    if (!bStarted) { Fail(TEXT("presentation prelude was not initialized")); return true; }
    if (HasFailed() || bStartupComplete) return true;
    StartupSeconds += FMath::Clamp(DeltaSeconds, 0.0f, .1f);
    PhaseSeconds += FMath::Clamp(DeltaSeconds, 0.0f, .1f);
    if (!Sample()) return true;
    if (EventIndex < 6 && PhaseSeconds >= .35)
    {
        if (!SendZoomEvent(EventIndex++)) return true;
        PhaseSeconds = 0;
    }
    if (EventIndex == 6 && PhaseSeconds >= .65)
    {
        const double Zoom = Pawn()->GetWalkingDiagnostics()->GetObjectField(TEXT("presentationCamera"))->GetNumberField(TEXT("requestedBoomCm"));
        if (FMath::Abs(Zoom - InitialZoomCm) > .01) { Fail(TEXT("balanced gesture pairs did not restore the initial zoom preference")); return true; }
        bStartupComplete = true;
    }
    return bStartupComplete;
}

bool UBreziPresentationQA::Sample()
{
    if (!bStarted || HasFailed() || !OwnerController.IsValid() || !Pawn()) return false;
    if (!OwnerController->IsWalkthroughAutomationActive() || !OwnerController->IsNavigationInputActive())
        return Fail(TEXT("presentation observer lost its validated input owner"));
    const TSharedRef<FJsonObject> Walking = Pawn()->GetWalkingDiagnostics();
    const TSharedPtr<FJsonObject> Camera = Walking->GetObjectField(TEXT("presentationCamera"));
    const TSharedPtr<FJsonObject> Avatar = Walking->GetObjectField(TEXT("avatar"));
    const bool VisibilityTarget = Avatar->GetBoolField(TEXT("visibilityTarget"));
    const double Opacity = Avatar->GetNumberField(TEXT("opacity"));
    if (VisibilityTarget != bPriorVisibilityTarget || Opacity <= .001 || Opacity >= .999) FractionalOpacitySeconds = 0;
    else FractionalOpacitySeconds += FMath::Clamp(Pawn()->GetWorld()->GetDeltaSeconds(), 0.0f, .1f);
    bPriorVisibilityTarget = VisibilityTarget;
    if (FractionalOpacitySeconds > .3) return Fail(TEXT("avatar opacity did not settle to fully opaque or hidden after its brief transition"));
    const UCameraComponent* Lens = Pawn()->GetPresentationCamera();
    const UCameraComponent* Eye = Pawn()->GetPhysicalCamera();
    if (!Lens || !Lens->IsActive() || !Eye || Lens == Eye)
        return Fail(TEXT("third-person QA is observing an inactive or physical-only lens"));
    const double Effective = Camera->GetNumberField(TEXT("effectiveBoomCm"));
    const double Limit = Camera->GetNumberField(TEXT("collisionLimitCm"));
    MaximumBoomLimitErrorCm = FMath::Max(MaximumBoomLimitErrorCm, Effective - Limit);
    if (Effective > Limit + .1 || !FMath::IsFinite(Effective)) return Fail(TEXT("active camera exceeded its measured obstruction limit"));
    if (Camera->GetBoolField(TEXT("occluded"))) ++ObstructedSamples;
    // The first frame can precede the player-camera-manager update after M/F2.
    if (StartupSeconds > .15 && OwnerController->PlayerCameraManager)
    {
        const double Error = FVector::Distance(Lens->GetComponentLocation(), OwnerController->PlayerCameraManager->GetCameraLocation());
        MaximumCameraCacheErrorCm = FMath::Max(MaximumCameraCacheErrorCm, Error);
        if (Error > 1) return Fail(TEXT("rendered player camera does not match the active third-person lens"));
    }
    if (Effective > 1)
    {
        FHitResult Hit;
        FCollisionQueryParams Params(SCENE_QUERY_STAT(BreziPresentationIndependentBoom), true, Pawn());
        Params.AddIgnoredComponents(IndependentNavigationProxies);
        if (Pawn()->GetWorld()->SweepSingleByChannel(Hit, Eye->GetComponentLocation(), Lens->GetComponentLocation(),
            FQuat::Identity, ECC_Camera, FCollisionShape::MakeSphere(BreziAvatar::ProbeRadiusCm), Params)
            && (Hit.bStartPenetrating || Hit.Distance < Effective - .5))
            return Fail(TEXT("independent sphere sweep found an obstacle before the rendered lens"));
        FCollisionQueryParams RawParams(SCENE_QUERY_STAT(BreziPresentationProxyComparison), true, Pawn());
        if (Pawn()->GetWorld()->SweepSingleByChannel(Hit, Eye->GetComponentLocation(), Lens->GetComponentLocation(),
            FQuat::Identity, ECC_Camera, FCollisionShape::MakeSphere(BreziAvatar::ProbeRadiusCm), RawParams)
            && IndependentNavigationProxies.ContainsByPredicate([&Hit](const TWeakObjectPtr<UPrimitiveComponent>& Component)
                { return Component.Get() == Hit.GetComponent(); }) && Hit.Distance < Effective - .5)
            ++NavigationProxyBypassSamples;
    }
    const USkeletalMeshComponent* Mesh = Pawn()->GetMesh();
    const TArray<FTransform>& Pose = Mesh->GetComponentSpaceTransforms();
    BoneCount = FMath::Max(BoneCount, Pose.Num());
    if (Mesh->IsVisible() && Mesh->WasRecentlyRendered(.5f)) ++VisibleRigSamples;
    if (Pose.Num() >= 50 && Pose.Num() == PriorPose.Num())
    {
        double MaxAngle = 0;
        for (int32 I = 0; I < Pose.Num(); ++I)
            MaxAngle = FMath::Max(MaxAngle, Pose[I].GetRotation().AngularDistance(PriorPose[I].GetRotation()));
        if (Pawn()->GetVelocity().Size2D() > 10)
        {
            MaximumWalkingBoneAngle = FMath::Max(MaximumWalkingBoneAngle, MaxAngle);
            if (MaxAngle > 0.001) ++WalkingPoseChanges;
        }
        else
        {
            MaximumIdleBoneAngle = FMath::Max(MaximumIdleBoneAngle, MaxAngle);
            if (MaxAngle > 0.0001) ++IdlePoseChanges;
        }
    }
    PriorPose = Pose;
    ++Samples;
    return true;
}

bool UBreziPresentationQA::Finish()
{
    bFinished = true;
    if (HasFailed()) return false;
    if (!bStartupComplete || Events.Num() != 6) return Fail(TEXT("native viewport gesture prelude is incomplete"));
    if (BoneCount < 50 || VisibleRigSamples == 0 || IdlePoseChanges == 0 || WalkingPoseChanges == 0)
        return Fail(TEXT("native visible skeletal rig did not produce both idle and moving bone poses"));
    if (ObstructedSamples == 0) return Fail(TEXT("route never exercised a blocked camera boom"));
    return true;
}

TSharedRef<FJsonObject> UBreziPresentationQA::GetDiagnostics() const
{
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    Result->SetStringField(TEXT("status"), HasFailed() ? TEXT("failed") : bFinished ? TEXT("passed-native-presentation") : TEXT("in-progress"));
    Result->SetStringField(TEXT("failure"), Failure);
    Result->SetBoolField(TEXT("startupComplete"), bStartupComplete);
    Result->SetStringField(TEXT("inputMethod"), TEXT("synthetic FPointerEvent through owned SViewport::OnTouchGesture/OnMouseWheel inside validated engine-input walkthrough"));
    Result->SetBoolField(TEXT("physicalMacOSTrackpadVerified"), false);
    Result->SetBoolField(TEXT("foregroundCaptureVerified"), false);
    Result->SetNumberField(TEXT("samples"), Samples);
    Result->SetNumberField(TEXT("skeletalBoneCount"), BoneCount);
    Result->SetNumberField(TEXT("visibleRecentlyRenderedRigSamples"), VisibleRigSamples);
    Result->SetNumberField(TEXT("idlePoseChanges"), IdlePoseChanges);
    Result->SetNumberField(TEXT("walkingPoseChanges"), WalkingPoseChanges);
    Result->SetNumberField(TEXT("maxIdleBoneRotationRadians"), MaximumIdleBoneAngle);
    Result->SetNumberField(TEXT("maxWalkingBoneRotationRadians"), MaximumWalkingBoneAngle);
    Result->SetNumberField(TEXT("obstructedCameraSamples"), ObstructedSamples);
    Result->SetNumberField(TEXT("independentlyIgnoredNavigationProxyComponents"), IndependentNavigationProxies.Num());
    Result->SetNumberField(TEXT("navigationProxyBypassSamples"), NavigationProxyBypassSamples);
    Result->SetNumberField(TEXT("maxCameraCacheErrorCm"), MaximumCameraCacheErrorCm);
    Result->SetNumberField(TEXT("maxBoomBeyondCollisionLimitCm"), MaximumBoomLimitErrorCm);
    Result->SetArrayField(TEXT("zoomEvents"), Events);
    Result->SetStringField(TEXT("scope"), TEXT("Native active camera/cache, independent boom sphere sweeps, viewport gesture dispatch and component-space skeletal pose changes. Existing harness owns all capsule movement and source-room validation; visual screenshots remain separate evidence."));
    return Result;
}
