#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "BreziWalkingContract.h"
#include "BreziViewTransitionPolicy.h"
#include "BreziPawn.generated.h"

class UCameraComponent;
class APlayerCameraManager;
class UBreziCharacterMovementComponent;
class FJsonObject;
struct FFindFloorResult;

struct FBreziViewpoint
{
    FString Id;
    FString Label;
    FVector EyeCm = FVector::ZeroVector;
    FVector TargetCm = FVector::ZeroVector;
    float HorizontalFovDegrees = 75.0f;
};

enum class EBreziCameraMode : uint8 { Orbit, Walking };

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
    void SetNavigating(bool bEnabled);
    void Zoom(float Direction);
    void SetReducedMotion(bool bEnabled);
    bool IsWalkingMode() const { return CameraMode == EBreziCameraMode::Walking; }
    bool IsNavigating() const { return bNavigating; }
    bool HasViewpoints() const { return !Viewpoints.IsEmpty(); }
    const FText& GetNavigationMessage() const { return NavigationMessage; }
    void DismissNavigationMessage() { NavigationMessage = FText::GetEmpty(); }
    const FString& GetActiveViewId() const { return ActiveViewId; }
    const TArray<FBreziViewpoint>& GetViewpoints() const { return Viewpoints; }
    TSharedRef<FJsonObject> GetWalkingDiagnostics() const;
    bool PrepareTraversalAuditView(const FVector& Eye, const FVector& Forward);
    bool SetRealtimeStudyOrbit(double OffsetDegrees);
    // Called after the CharacterMovement tick has committed its movement update.
    void UpdateWalkingCamera(float DeltaSeconds);

private:
    void LoadViewpoints();
    void MoveForward(float Value) { ForwardInput = Value; }
    void MoveRight(float Value) { RightInput = Value; }
    void LookHorizontal(float Value) { LookInput.X = Value; }
    void LookVertical(float Value) { LookInput.Y = Value; }
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
    TArray<FBreziViewpoint> Viewpoints;
    FString ActiveViewId;
    FVector OrbitTarget = FVector::ZeroVector;
    float OrbitRadius = 1000;
    float ForwardInput = 0;
    float RightInput = 0;
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
