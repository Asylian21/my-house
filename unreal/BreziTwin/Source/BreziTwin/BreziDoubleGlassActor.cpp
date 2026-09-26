#include "BreziDoubleGlassActor.h"
#include "BreziDoubleGlassCapturePolicy.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/TextureRenderTarget2D.h"
#include "EngineUtils.h"
#include "Dom/JsonObject.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Math/RotationMatrix.h"

namespace
{
TAutoConsoleVariable<int32> CVarDoubleGlass(TEXT("r.Brezi.DoubleGlass"), 1,
    TEXT("Enable optional rear-interface capture/overlay actors. 0 gives the exact original primary-glass view."), ECVF_Default);
struct FWorldCaptureState
{
    uint64 Revision = 0;
    TArray<TWeakObjectPtr<ABreziDoubleGlassActor>> Actors;
    BreziDoubleGlass::FrameBudget Budget;
};
TMap<TWeakObjectPtr<UWorld>, FWorldCaptureState> WorldStates;
uint64 GlobalLastCaptureFrame = MAX_uint64;

FLinearColor V(const FVector& Value) { return FLinearColor(Value.X, Value.Y, Value.Z, 0); }
}

ABreziDoubleGlassActor::ABreziDoubleGlassActor()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickGroup = TG_PostUpdateWork;
    SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
    Overlay = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RearReflectionOverlay"));
    Overlay->SetupAttachment(RootComponent);
    Overlay->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Overlay->SetGenerateOverlapEvents(false);
    Overlay->SetCanEverAffectNavigation(false);
    Overlay->SetCastShadow(false);
    Overlay->bAffectDistanceFieldLighting = false;
    Overlay->SetVisibility(false);
    ReflectionCapture = CreateDefaultSubobject<USceneCaptureComponent2D>(TEXT("RearReflectionCapture"));
    ReflectionCapture->SetupAttachment(RootComponent);
    ReflectionCapture->bCaptureEveryFrame = false;
    ReflectionCapture->bCaptureOnMovement = false;
    ReflectionCapture->bAlwaysPersistRenderingState = false;
    ReflectionCapture->bEnableClipPlane = true;
    ReflectionCapture->CaptureSource = ESceneCaptureSource::SCS_SceneColorHDRNoAlpha;
    ReflectionCapture->ShowFlags.SetEyeAdaptation(false);
    ReflectionCapture->ShowFlags.SetMotionBlur(false);
    ReflectionCapture->ShowFlags.SetBloom(false);
    ReflectionCapture->ShowFlags.SetLensFlares(false);
    ReflectionCapture->ShowFlags.SetPostProcessing(false);
    ReflectionCapture->PostProcessSettings.bOverride_DynamicGlobalIlluminationMethod = true;
    ReflectionCapture->PostProcessSettings.DynamicGlobalIlluminationMethod = EDynamicGlobalIlluminationMethod::None;
    ReflectionCapture->PostProcessSettings.bOverride_ReflectionMethod = true;
    ReflectionCapture->PostProcessSettings.ReflectionMethod = EReflectionMethod::None;
    ReflectionCapture->PostProcessBlendWeight = 1;
}

void ABreziDoubleGlassActor::BeginPlay()
{
    Super::BeginPlay();
    const IConsoleVariable* Clip = IConsoleManager::Get().FindConsoleVariable(TEXT("r.AllowGlobalClipPlane"));
    if (!SourceComponent || !SourceComponent->GetStaticMesh() || !OverlayMaterial || !Clip || Clip->GetInt() == 0)
    {
        LastSkip = TEXT("missing-source-material-or-global-clip");
        UE_LOG(LogTemp, Error, TEXT("BREZI_DOUBLE_GLASS disabled %s: source/material/global clip plane missing"), *GetName());
        SetActorTickEnabled(false);
        return;
    }
    FVector Min, Max;
    SourceComponent->GetLocalBounds(Min, Max);
    const FVector Size = Max - Min;
    const int32 Axis = Size.X < Size.Y ? (Size.X < Size.Z ? 0 : 2) : (Size.Y < Size.Z ? 1 : 2);
    LocalNormal[Axis] = 1;
    LocalCenter = (Min + Max) * .5;
    LocalHalfThickness = Size[Axis] * .5;
    if (LocalHalfThickness <= 0 || LocalHalfThickness > 5)
    {
        LastSkip = TEXT("invalid-thickness");
        UE_LOG(LogTemp, Error, TEXT("BREZI_DOUBLE_GLASS disabled %s: invalid pane thickness"), *GetName());
        SetActorTickEnabled(false);
        return;
    }
    Overlay->SetStaticMesh(SourceComponent->GetStaticMesh());
    Overlay->SetWorldTransform(SourceComponent->GetComponentTransform());
    Overlay->TranslucencySortPriority = SourceComponent->TranslucencySortPriority + 1;
    Material = UMaterialInstanceDynamic::Create(OverlayMaterial, this);
    Overlay->SetMaterial(0, Material);
    Material->SetScalarParameterValue(TEXT("Ready"), 0);
    // Captures retain the original scene, but cannot sample any supplemental layer.
    ReflectionCapture->HiddenComponents.Add(SourceComponent);
    for (TActorIterator<ABreziDoubleGlassActor> It(GetWorld()); It; ++It)
        ReflectionCapture->HiddenActors.Add(*It);
    // Older cooked maps serialized the previous component defaults. Enforce the
    // bounded runtime policy after loading rather than requiring reimport.
    ReflectionCapture->bCaptureEveryFrame = false;
    ReflectionCapture->bCaptureOnMovement = false;
    ReflectionCapture->bAlwaysPersistRenderingState = false;
    ReflectionCapture->ShowFlags.SetLumenGlobalIllumination(false);
    ReflectionCapture->ShowFlags.SetLumenReflections(false);
    ReflectionCapture->ShowFlags.SetTemporalAA(false);
    ReflectionCapture->PostProcessSettings.bOverride_DynamicGlobalIlluminationMethod = true;
    ReflectionCapture->PostProcessSettings.DynamicGlobalIlluminationMethod = EDynamicGlobalIlluminationMethod::None;
    ReflectionCapture->PostProcessSettings.bOverride_ReflectionMethod = true;
    ReflectionCapture->PostProcessSettings.ReflectionMethod = EReflectionMethod::None;
    WorldStates.FindOrAdd(GetWorld()).Actors.AddUnique(this);
    bConfigured = true;
    LastSkip = TEXT("awaiting-camera");
}

void ABreziDoubleGlassActor::ReleaseCapture()
{
    bCaptureEligible = false;
    bCaptured = false;
    PendingCaptures = 0;
    if (Material) Material->SetScalarParameterValue(TEXT("Ready"), 0);
    if (!Target) return;
    Material->ClearParameterValues();
    ReflectionCapture->TextureTarget = nullptr;
    ReflectionCapture->bAlwaysPersistRenderingState = false;
    ReflectionCapture->GetViewState(0); // Release any history inherited from an older cooked map.
    Target->ReleaseResource();
    Target = nullptr;
}

void ABreziDoubleGlassActor::InvalidateScene(UWorld* World)
{
    check(IsInGameThread());
    if (FWorldCaptureState* State = WorldStates.Find(World)) ++State->Revision;
}

bool ABreziDoubleGlassActor::AcquireCaptureBudget()
{
    if (GlobalLastCaptureFrame == GFrameCounter) return false;
    FWorldCaptureState& State = WorldStates.FindOrAdd(GetWorld());
    const int32 Index = State.Actors.IndexOfByPredicate([this](const auto& Actor) { return Actor.Get() == this; });
    if (Index == INDEX_NONE) return false;
    const bool Acquired = State.Budget.TryAcquire(GFrameCounter, Index, State.Actors.Num(), [&State](size_t Candidate)
    {
        const ABreziDoubleGlassActor* Actor = State.Actors[Candidate].Get();
        return Actor && Actor->bCaptureEligible && Actor->PendingCaptures > 0 && Actor->LastSceneRevision == State.Revision;
    });
    if (Acquired) GlobalLastCaptureFrame = GFrameCounter;
    return Acquired;
}

void ABreziDoubleGlassActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    bCaptureEligible = false;
    if (!bConfigured || !IsValid(SourceComponent)) return;
    if (CVarDoubleGlass.GetValueOnGameThread() == 0)
    {
        Overlay->SetVisibility(false);
        ReleaseCapture();
        bWasVisible = false;
        LastSkip = TEXT("disabled-by-cvar");
        return;
    }
    APlayerController* Controller = UGameplayStatics::GetPlayerController(this, 0);
    if (!Controller || !Controller->PlayerCameraManager) return;
    FVector Eye;
    FRotator Rotation;
    Controller->GetPlayerViewPoint(Eye, Rotation);
    const float Fov = FMath::Clamp(Controller->PlayerCameraManager->GetFOVAngle(), 10.f, 150.f);
    int32 Width = 0, Height = 0;
    Controller->GetViewportSize(Width, Height);
    if (Width <= 0 || Height <= 0) return;
    const float Aspect = float(Width) / Height;
    const float TanHalf = FMath::Tan(FMath::DegreesToRadians(Fov * .5f));
    const FRotationMatrix ViewRotation(Rotation);
    const FVector Forward = ViewRotation.GetUnitAxis(EAxis::X);
    const FVector Right = ViewRotation.GetUnitAxis(EAxis::Y);
    const FVector Up = ViewRotation.GetUnitAxis(EAxis::Z);
    const FTransform Transform = SourceComponent->GetComponentTransform();
    // Sliding HS leaves move independently of their owning imported actor.
    if (!Transform.Equals(Overlay->GetComponentTransform(), .001)) Overlay->SetWorldTransform(Transform);
    const FVector Center = Transform.TransformPosition(LocalCenter);
    const FVector AxisNormal = Transform.TransformVectorNoScale(LocalNormal).GetSafeNormal();
    const float SideDistance = FVector::DotProduct(Eye - Center, AxisNormal);
    LastDistanceCm = FMath::Abs(SideDistance);
    const FVector Normal = AxisNormal * (SideDistance >= 0 ? 1 : -1);
    const float HalfThickness = Transform.TransformVector(LocalNormal * LocalHalfThickness).Size();
    const FVector ToCenter = SourceComponent->Bounds.Origin - Eye;
    const float Radius = SourceComponent->Bounds.SphereRadius;
    const float Z = FVector::DotProduct(ToCenter, Forward);
    const bool bVisible = SourceComponent->IsVisible() && !SourceComponent->GetOwner()->IsHidden()
        && FMath::Abs(SideDistance) > HalfThickness + .1f
        && ToCenter.Size() - Radius < MaximumDistanceCm && Z + Radius > 5.f
        && FMath::Abs(FVector::DotProduct(ToCenter, Right)) <= FMath::Max(Z, 0.f) * TanHalf + Radius * FMath::Sqrt(1 + TanHalf * TanHalf)
        && FMath::Abs(FVector::DotProduct(ToCenter, Up)) <= FMath::Max(Z, 0.f) * TanHalf / Aspect + Radius * FMath::Sqrt(1 + FMath::Square(TanHalf / Aspect));
    if (!bVisible)
    {
        Overlay->SetVisibility(false);
        LastSkip = TEXT("outside-conservative-frustum-distance-or-inside-pane");
        bWasVisible = false;
        if (GetWorld()->GetTimeSeconds() - LastVisibleTime > 5.f) ReleaseCapture();
        return;
    }
    const double Now = GetWorld()->GetTimeSeconds();
    LastVisibleTime = Now;
    const int32 RTWidth = FMath::Clamp(CaptureWidth, 256, BreziDoubleGlass::MaximumCaptureWidth);
    const int32 RTHeight = FMath::Max(128, FMath::RoundToInt(RTWidth / Aspect));
    if (Target && (Target->SizeX != RTWidth || Target->SizeY != RTHeight)) ReleaseCapture();
    const uint64 Revision = WorldStates.FindOrAdd(GetWorld()).Revision;
    const bool bChanged = !bWasVisible || !Eye.Equals(LastEye, BreziDoubleGlass::CameraDistanceToleranceCm)
        || !Rotation.Equals(LastRotation, BreziDoubleGlass::CameraAngleToleranceDegrees)
        || !FMath::IsNearlyEqual(Fov, LastFov, .01f) || !FMath::IsNearlyEqual(Aspect, LastAspect, .00001f)
        || Revision != LastSceneRevision || LastRevision != SceneRevision || !Transform.Equals(LastSourceTransform, .001);
    if (bChanged)
    {
        PendingCaptures = FMath::Clamp(WarmupCaptures, 1, BreziDoubleGlass::MaximumWarmupCaptures);
        LastChangeTime = Now;
        bCaptured = false;
        Material->SetScalarParameterValue(TEXT("Ready"), 0);
        // Anchoring to the last significant change also catches accumulated slow drift.
        LastEye = Eye; LastRotation = Rotation; LastFov = Fov; LastAspect = Aspect;
        LastSceneRevision = Revision; LastRevision = SceneRevision;
        LastSourceTransform = Transform;
    }
    bWasVisible = true;
    if (!BreziDoubleGlass::IsSettled(Now, LastChangeTime))
    {
        Overlay->SetVisibility(false);
        LastSkip = TEXT("awaiting-stable-camera-and-scene");
        return;
    }
    // A deferred capture becomes visible on a following game frame. Moving
    // cameras use the unchanged primary glass, not a stale projected rear image.
    const bool bImageAvailable = bCaptured && LastCaptureFrame < GFrameCounter;
    Overlay->SetVisibility(bImageAvailable);
    Material->SetScalarParameterValue(TEXT("Ready"), bImageAvailable ? 1 : 0);
    LastSkip = PendingCaptures > 0 ? TEXT("awaiting-global-capture-budget") : TEXT("settled");
    if (PendingCaptures <= 0) return;
    bCaptureEligible = true;
    if (!AcquireCaptureBudget()) return;
    if (!Target)
    {
        Target = NewObject<UTextureRenderTarget2D>(this);
        Target->ClearColor = FLinearColor::Black;
        Target->InitCustomFormat(RTWidth, RTHeight, PF_FloatRGBA, true);
        Target->UpdateResourceImmediate(true);
        ReflectionCapture->TextureTarget = Target;
        Material->SetTextureParameterValue(TEXT("RearImage"), Target);
        UE_LOG(LogTemp, Display, TEXT("BREZI_DOUBLE_GLASS allocate %s %dx%d bytes=%lld"), *GetName(), RTWidth, RTHeight, int64(RTWidth)*RTHeight*8);
    }
    const FVector RearPlane = Center - Normal * HalfThickness;
    LastPlane = RearPlane;
    LastNormal = Normal;
    LastNoV = FMath::Clamp(float(FVector::DotProduct((Eye-Center).GetSafeNormal(), Normal)), 0.f, 1.f);
    const FVector MirroredEye = Eye - 2 * FVector::DotProduct(Eye - RearPlane, Normal) * Normal;
    const FVector MirroredForward = Forward - 2 * FVector::DotProduct(Forward, Normal) * Normal;
    const FVector MirroredUp = Up - 2 * FVector::DotProduct(Up, Normal) * Normal;
    const FRotator CaptureRotation = FRotationMatrix::MakeFromXZ(MirroredForward, MirroredUp).Rotator();
    const FRotationMatrix CaptureBasis(CaptureRotation);
    ReflectionCapture->SetWorldLocationAndRotation(MirroredEye, CaptureRotation);
    ReflectionCapture->FOVAngle = Fov;
    ReflectionCapture->ClipPlaneBase = RearPlane;
    ReflectionCapture->ClipPlaneNormal = Normal;
    Overlay->SetWorldTransform(Transform);
    Material->SetVectorParameterValue(TEXT("CaptureOrigin"), V(MirroredEye));
    Material->SetVectorParameterValue(TEXT("CaptureForward"), V(CaptureBasis.GetUnitAxis(EAxis::X)));
    Material->SetVectorParameterValue(TEXT("CaptureRight"), V(CaptureBasis.GetUnitAxis(EAxis::Y)));
    Material->SetVectorParameterValue(TEXT("CaptureUp"), V(CaptureBasis.GetUnitAxis(EAxis::Z)));
    Material->SetVectorParameterValue(TEXT("CaptureProjection"), FLinearColor(TanHalf, Aspect, 0, 0));
    Material->SetVectorParameterValue(TEXT("PaneCenter"), V(Center));
    Material->SetVectorParameterValue(TEXT("PaneNormal"), V(Normal));
    Material->SetVectorParameterValue(TEXT("RearPlane"), V(RearPlane));
    ReflectionCapture->CaptureSceneDeferred();
    ++CapturesIssued;
    --PendingCaptures;
    bCaptured = true;
    LastCaptureFrame = GFrameCounter;
    LastSkip = TEXT("capture-deferred");
    if (PendingCaptures == 0)
        UE_LOG(LogTemp, Display, TEXT("BREZI_DOUBLE_GLASS settled %s captures=%d side=%s halfThicknessCm=%.4f"), *GetName(), CapturesIssued, SideDistance >= 0 ? TEXT("positive") : TEXT("negative"), HalfThickness);
}

TSharedRef<FJsonObject> ABreziDoubleGlassActor::Diagnostics() const
{
    TSharedRef<FJsonObject> Result = MakeShared<FJsonObject>();
    FString SourceId;
    if (SourceComponent && SourceComponent->GetOwner())
        for (const FName Tag : SourceComponent->GetOwner()->Tags)
            if (Tag.ToString().StartsWith(TEXT("DOM_"))) { SourceId = Tag.ToString(); break; }
    Result->SetStringField(TEXT("actor"), GetPathName());
    Result->SetStringField(TEXT("sourceId"), SourceId);
    Result->SetBoolField(TEXT("configured"), bConfigured);
    Result->SetBoolField(TEXT("enabled"), CVarDoubleGlass.GetValueOnGameThread() != 0);
    Result->SetBoolField(TEXT("ready"), bCaptured && bWasVisible && PendingCaptures == 0 && LastCaptureFrame < GFrameCounter);
    Result->SetNumberField(TEXT("captureBudgetPerFrame"), 1);
    Result->SetNumberField(TEXT("warmupCaptureBudget"), FMath::Clamp(WarmupCaptures, 1, BreziDoubleGlass::MaximumWarmupCaptures));
    Result->SetNumberField(TEXT("cameraSettleSeconds"), BreziDoubleGlass::QuietSeconds);
    Result->SetBoolField(TEXT("captureUsesLumen"), ReflectionCapture &&
        (ReflectionCapture->PostProcessSettings.DynamicGlobalIlluminationMethod == EDynamicGlobalIlluminationMethod::Lumen
        || ReflectionCapture->PostProcessSettings.ReflectionMethod == EReflectionMethod::Lumen));
    Result->SetBoolField(TEXT("capturePersistsHistory"), ReflectionCapture && ReflectionCapture->bAlwaysPersistRenderingState);
    Result->SetStringField(TEXT("sceneInvalidation"), TEXT("event-revision"));
    Result->SetBoolField(TEXT("overlayVisible"), Overlay && Overlay->IsVisible());
    Result->SetStringField(TEXT("state"), LastSkip);
    Result->SetNumberField(TEXT("captureCount"), CapturesIssued);
    Result->SetNumberField(TEXT("pendingCaptures"), PendingCaptures);
    Result->SetNumberField(TEXT("ior"), 1.52);
    Result->SetNumberField(TEXT("viewCosineAtCenter"), LastNoV);
    Result->SetNumberField(TEXT("distanceToPlaneCm"), LastDistanceCm);
    Result->SetNumberField(TEXT("renderTargetWidth"), Target ? Target->SizeX : 0);
    Result->SetNumberField(TEXT("renderTargetHeight"), Target ? Target->SizeY : 0);
    Result->SetNumberField(TEXT("renderTargetBytes"), Target ? int64(Target->SizeX)*Target->SizeY*8 : 0);
    auto Array = [](const FVector& Vector)
    {
        TArray<TSharedPtr<FJsonValue>> Values;
        Values.Add(MakeShared<FJsonValueNumber>(Vector.X));
        Values.Add(MakeShared<FJsonValueNumber>(Vector.Y));
        Values.Add(MakeShared<FJsonValueNumber>(Vector.Z));
        return Values;
    };
    Result->SetArrayField(TEXT("rearPlaneCm"), Array(LastPlane));
    Result->SetArrayField(TEXT("cameraFacingNormal"), Array(LastNormal));
    const double F0 = FMath::Square((1.52-1)/(1.52+1));
    const double F = F0 + (1-F0)*FMath::Pow(1-LastNoV, 5);
    const FVector Tint(.986,.994,.990);
    FVector Weight;
    for (int32 Axis=0; Axis<3; ++Axis)
        Weight[Axis] = F*FMath::Square(1-F)*FMath::Pow(Tint[Axis],2/FMath::Max(double(LastNoV),.001));
    Result->SetArrayField(TEXT("rearEnergyAtCenter"), Array(Weight));
    Result->SetStringField(TEXT("opticalModel"), TEXT("rear-plane mirror approximation; first return; no Snell lateral correction"));
    return Result;
}

void ABreziDoubleGlassActor::EndPlay(const EEndPlayReason::Type Reason)
{
    UE_LOG(LogTemp, Display, TEXT("BREZI_DOUBLE_GLASS end %s captures=%d"), *GetName(), CapturesIssued);
    ReleaseCapture();
    if (FWorldCaptureState* State = WorldStates.Find(GetWorld()))
    {
        State->Actors.RemoveAll([this](const auto& Actor) { return !Actor.IsValid() || Actor.Get() == this; });
        if (State->Actors.IsEmpty()) WorldStates.Remove(GetWorld());
    }
    Super::EndPlay(Reason);
}
