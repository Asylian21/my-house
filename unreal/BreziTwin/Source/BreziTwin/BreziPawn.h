#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "BreziWalkingContract.h"
#include "BreziViewTransitionPolicy.h"
#include "BreziFlightPolicy.h"
#include "BreziPawn.generated.h"

class UCameraComponent;
class APlayerCameraManager;
class UBreziCharacterMovementComponent;
class UBlendSpace1D;
class UMaterialInstanceDynamic;
class UPrimitiveComponent;
class FJsonObject;
struct FFindFloorResult;

struct FBreziViewpoint
{
    FString Id;
    FString Label;
    FVector EyeCm = FVector::ZeroVector;
    FVector TargetCm = FVector::ZeroVector;
    float HorizontalFovDegrees = 75.0f;
    bool bWalking = false;
};

enum class EBreziCameraMode : uint8 { Orbit, Walking, Flight };

UCLASS()
class ABreziPawn : public ACharacter
{
    GENERATED_BODY()
public:
    ABreziPawn(const FObjectInitializer& ObjectInitializer);
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    void SelectView(const FString& Id, bool bInstant = false);
    bool ToggleMovementMode();
    bool StartWalkingTour();
    bool StartFreeFlight();
    bool SelectWalkingView(const FString& Id);
    void SetNavigating(bool bEnabled);
    void Zoom(float Direction);
    void ZoomCamera(float SignedSteps);
    void TogglePersonCamera();
    void RecenterCamera();
    void TurnFromScreen(float DeltaDegrees);
    bool IsThirdPersonCamera() const { return bThirdPersonPreferred; }
    void SetMouseLookEnabled(bool bEnabled);
    void StopWalkingInput() { ClearMovementInput(); }
    void GetInteractionView(FVector& Eye, FRotator& Look) const;
    UCameraComponent* GetPhysicalCamera() const { return Camera; }
    UCameraComponent* GetPresentationCamera() const;
    virtual FVector GetPawnViewLocation() const override;
    void SetReducedMotion(bool bEnabled);
    void SetLookSensitivity(float Value);
    bool IsWalkingMode() const { return CameraMode == EBreziCameraMode::Walking; }
    bool IsFlightMode() const { return CameraMode == EBreziCameraMode::Flight; }
    bool IsNavigating() const { return bNavigating; }
    bool HasViewpoints() const { return !Viewpoints.IsEmpty(); }
    const FText& GetNavigationMessage() const { return NavigationMessage; }
    void DismissNavigationMessage() { NavigationMessage = FText::GetEmpty(); }
    const FString& GetActiveViewId() const { return ActiveViewId; }
    const TArray<FBreziViewpoint>& GetViewpoints() const { return Viewpoints; }
    TSharedRef<FJsonObject> GetWalkingDiagnostics() const;
    bool PrepareTraversalAuditView(const FVector& Eye, const FVector& Forward);
    bool AimWalkingTraversal(const FVector& Forward);
    bool SetRealtimeStudyOrbit(double OffsetDegrees);
    bool PrepareRealtimeStudyWalk(const TArray<FVector>& Points, const FString& SceneSha256);
    bool SetRealtimeStudyWalkTarget(const FVector& Target);
    void StopRealtimeStudyWalk();
    // Called after the CharacterMovement tick has committed its movement update.
    void UpdateWalkingCamera(float DeltaSeconds);

private:
    friend class FBreziFreeFlightTest;
    void LoadViewpoints();
    void MoveForward(float Value) { ForwardInput = Value; }
    void MoveRight(float Value) { RightInput = Value; }
    void MoveUp(float Value) { UpInput = Value; }
    void LookHorizontal(float Value) { LookInput.X = bMouseLookEnabled ? Value : 0; }
    void LookVertical(float Value) { LookInput.Y = bMouseLookEnabled ? Value : 0; }
    void InitializeAvatar();
    void UpdateAvatarCamera(float DeltaSeconds);
    void InterruptTransition();
    bool IsPresetPathObstructed(const FVector& Start, const FVector& End);
    void ApplyTransitionDestination(bool bCameraCut);
    bool BeginOwnedPresetFade();
    bool OwnsPresetFade() const;
    void ReleasePresetFade();
    void TickPresetFade(float DeltaSeconds);
    void TracePresetTransition(const TCHAR* Event);
    bool ValidateWalkingWorld();
    bool FindWalkingEntry(FVector& Center, FFindFloorResult& Floor);
    bool EnterWalking();
    void ExitWalking();
    void ClearMovementInput();
    UBreziCharacterMovementComponent* WalkingMovement() const;

    UPROPERTY() TObjectPtr<UCameraComponent> Camera;
    UPROPERTY() TObjectPtr<UCameraComponent> AvatarCamera;
    UPROPERTY() TObjectPtr<UBlendSpace1D> AvatarLocomotion;
    UPROPERTY() TObjectPtr<UMaterialInstanceDynamic> AvatarMaterial;
    TArray<TWeakObjectPtr<UPrimitiveComponent>> CameraNavigationProxies;
    bool bThirdPersonPreferred = true;
    bool bMouseLookEnabled = true;
    bool bAvatarReady = false;
    bool bBoomOccluded = false;
    bool bAvatarVisibilityTarget = true;
    double DesiredBoomCm = 260;
    double ZoomBoomCm = 260;
    double EffectiveBoomCm = 260;
    double LastBoomLimitCm = 260;
    double AvatarOpacity = 1;
    double AvatarFacingYaw = 0;
    double AvatarFloorOffsetCm = 0;
    int64 BoomSamples = 0;
    int64 BoomOccludedSamples = 0;
    int64 AvatarAnimatedSamples = 0;
    FString BoomObstacleId;
    FString AvatarStatus = TEXT("not-loaded");
    TArray<FBreziViewpoint> Viewpoints;
    FString ActiveViewId;
    FVector OrbitTarget = FVector::ZeroVector;
    float OrbitRadius = 1000;
    float OrbitZoomTarget = 1000;
    float ForwardInput = 0;
    bool bRealtimeStudyWalking = false;
    FVector RealtimeStudyWalkTarget = FVector::ZeroVector;
    float RightInput = 0;
    float UpInput = 0;
    BreziFlight::Bounds FlightBounds;
    float LookSensitivity = 1.0f;
    FVector2D LookInput = FVector2D::ZeroVector;
    EBreziCameraMode CameraMode = EBreziCameraMode::Orbit;
    bool bNavigating = false;
    bool bReducedMotion = false;
    bool bTransitioning = false;
    float TransitionElapsed = 0;
    float TransitionDuration = 1.6f;
    FVector TransitionStartEye = FVector::ZeroVector;
    FVector TransitionStartTarget = FVector::ZeroVector;
    FBreziViewpoint TransitionDestination;
    float TransitionStartFov = 75;
    BreziViewTransition::Fade PresetFade;
    TWeakObjectPtr<APlayerCameraManager> PresetFadeManager;
    float LastOwnedFadeAlpha = 0;
    FString PresetQueryReason = TEXT("not-requested");
    FString PresetQuerySourceId;
    int32 PresetQueryBlend = INDEX_NONE;
    int32 PresetQueryCount = 0;
    int32 PresetTraceCount = 0;

    FBreziWalkingContract WalkingContract;
    bool bWalkingContractLoaded = false;
    bool bWalkingWorldValidated = false;
    bool bCLIWalkingPending = false;
    bool bCLIAuditPending = false;
    TArray<FString> WalkingWorldErrors;
    FText NavigationMessage;
    FString EntryQueryStatus = TEXT("not-requested");
    FString EntrySupportId;
    FString EntryLineHitId;
    FString CurrentSupportId;
    int32 EntryAttempts = 0;
    int32 SuccessfulEntries = 0;
    int64 GroundedEyeSamples = 0;
    int64 UnsupportedEyeSamples = 0;
    double MinMeasuredEyeHeight = TNumericLimits<double>::Max();
    double MaxMeasuredEyeHeight = -TNumericLimits<double>::Max();
    double MaxEyeHeightError = 0;
    double LastMeasuredEyeHeight = 0;
    FVector LastEntryCenter = FVector::ZeroVector;
    FVector LastEntryFloor = FVector::ZeroVector;
};
