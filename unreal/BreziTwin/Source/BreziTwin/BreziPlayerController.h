#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "Engine/TimerHandle.h"
#include "BreziNativeAccessibility.h"
#include "BreziRenderQualityPolicy.h"
#include "BreziNavigationPolicy.h"
#include "BreziPlayerController.generated.h"

class SWidget;
class FReply;
struct FKeyEvent;
struct FPointerEvent;
class ABreziPawn;
class ADirectionalLight;
class ASkyLight;
class UCameraComponent;
class UBreziRuntimeDiagnostics;
class UBreziWalkingTraversal;
class UBreziMotionQA;
class UBreziFlameStudy;
class UBreziExteriorLighting;
class UBreziDoors;
class ISceneViewExtension;
class URectLightComponent;

UCLASS()
class ABreziPlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    ABreziPlayerController();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void SetupInputComponent() override;
    virtual void OnPossess(APawn* InPawn) override;
    virtual void PreProcessInput(float DeltaTime, bool bGamePaused) override;
    virtual void PostProcessInput(float DeltaTime, bool bGamePaused) override;
    void RefreshInterface();
    UBreziDoors* GetDoorSystem() const;
    bool IsGameplayActive() const;
    // Only the validated, explicitly requested walkthrough harness may arm this.
    // It drives engine inputs without any native pointer capture or Slate focus.
    bool BeginWalkthroughAutomation();
    void EndWalkthroughAutomation();
    bool IsWalkthroughAutomationActive() const { return bWalkthroughAutomation; }
    bool IsNavigationInputActive() const;
    // Only numeric presets; the owned inner Slate viewport also retains raw Mac key codes.
    FReply HandlePresetShortcut(const FKeyEvent& Event, bool* OutRecognized = nullptr);
    bool HandleCameraWheel(const FPointerEvent& Event);
    bool HandleCameraGesture(const FPointerEvent& Event);

private:
    UPROPERTY() TObjectPtr<UBreziRuntimeDiagnostics> Diagnostics;
    UPROPERTY() TObjectPtr<UBreziWalkingTraversal> WalkingTraversal;
    UPROPERTY() TObjectPtr<UBreziMotionQA> MotionQA;
    UPROPERTY() TObjectPtr<UBreziFlameStudy> FlameStudy;
    UPROPERTY() TObjectPtr<UBreziExteriorLighting> ExteriorLighting;
    UPROPERTY() TObjectPtr<UBreziDoors> Doors;
    ABreziPawn* TwinPawn() const;
    void BuildInterface();
    bool HasForegroundWindow() const;
    void TryCompleteInitialTour();
    void PauseGameplay(bool bFocusMenu = true);
    void ResumeGameplay();
    void OnApplicationDeactivated();
    void Interact();
    FText InteractionPrompt() const;
    void UpdateAccessibleSubtrees();
    void BeginNavigation();
    void BeginPointerNavigation();
    void EndPointerNavigation();
    void StartNavigation(BreziNavigation::CaptureSource Source);
    void ToggleNavigation();
    void EndNavigation();
    void HandleEscape();
    void ToggleControls();
    void FocusFirstControl();
    void FocusControl(const TSharedPtr<SWidget>& Widget);
    FReply HandleInterfaceKey(const FKeyEvent& Event);
    FReply HandleDestinationKey(const FKeyEvent& Event);
    TSharedRef<SWidget> BuildDestinationMenu();
    void ClearMouseLookTransition();
    void ZoomIn();
    void ZoomOut();
    void TogglePersonCamera();
    void RecenterPersonCamera();
    void ToggleHudCursor();
    void BeginHudMovement(FKey Key);
    void EndHudMovement(FKey Key);
    void StopHudMovement();
    void SendHudKey(FKey Key, bool bDown);
    TSharedRef<SWidget> BuildVisibleControls();
    void ToggleTimeOfDay();
    void SetTimeOfDay(bool bTargetNight, bool bInstant);
    void UpdateTimeOfDayTransition(float DeltaSeconds);
    void FinishTimeOfDayTransition(bool bResetExposure);
    bool BeginLightingTransitionExposure();
    void RestoreLightingTransitionExposure(double ObservedElapsed = -1.0, bool bResetIntent = false);
    void TraceLightingTransition(const TCHAR* Event, const TCHAR* RestoreState, bool bResetIntent, double ObservedElapsed);
    void SelectNumberedView(int32 Index, bool bInstant = false);
    void SelectViewKey(FKey Key);
    void ToggleCameraMode();
    void ToggleFreeFlight();
    void ToggleFreeFlightShortcut();
    TSharedRef<SWidget> BuildFlightControl(bool bMenu);
    void ToggleReducedMotion();
    void UseSystemMotionPreference();
    void ApplyDisplayPreferences(FBreziDisplayPreferences Preferences);
    void InitializeRenderQuality();
    void RefreshRenderQualityScenePolicy();
    bool CanChangeRenderQuality() const;
    bool IsRenderQualitySelected(BreziRenderQuality::Profile Profile) const;
    void SelectRenderQuality(BreziRenderQuality::Profile Profile);
    bool ApplyRenderQuality(BreziRenderQuality::Profile Profile, bool bDeliberateSelection);
    FText RenderQualityStatus() const;
    void TraceRenderQuality(const TCHAR* Event, BreziRenderQuality::Profile Profile,
        float PriorScreen, float PriorHistory, bool bSaved);
    TSharedRef<SWidget> BuildRenderQualityChoices();
    TSharedRef<SWidget> BuildControlsMenu();
    void UpdateViewButtons();
    void SetMenuSection(int32 Section);
    float GetViewDockWidth() const;
    void RefreshWindowTitle();
    FTimerHandle WindowTitleRetry;
    int32 WindowTitleAttempts = 0;

    TSharedPtr<SWidget> Interface;
    TSharedPtr<SWidget> InterfaceHost;
    TSharedPtr<SWidget> ControlsAXContainer;
    TSharedPtr<SWidget> FeedbackAXContainer;
    TSharedPtr<SWidget> GameplayAXContainer;
    TSharedPtr<SWidget> RoomsAXContainer;
    TSharedPtr<SWidget> AtmosphereAXContainer;
    TSharedPtr<SWidget> InputAXContainer;
    TSharedPtr<SWidget> InteractionAXContainer;
    TSharedPtr<SWidget> MovementAXContainer;
    TSharedPtr<SWidget> FlightMovementAXContainer;
    TSharedPtr<class SButton> InteractionButton;
    TArray<TSharedPtr<SWidget>> MenuSectionControls;
    TArray<TSharedPtr<SWidget>> AtmosphereControls;
    TArray<TSharedPtr<SWidget>> InputControls;
    int32 MenuSection = 0;
    TSharedPtr<SWidget> WalkingModeControl;
    TSharedPtr<class SButton> NavigationFeedback;
    TSharedPtr<class SButton> ControlsButton;
    TSharedPtr<class SButton> NavigationButton;
    TSharedPtr<class SScrollBox> ControlsScrollBox;
    TSharedPtr<class SMenuAnchor> DestinationAnchor;
    TSharedPtr<class SButton> DestinationButton;
    TSharedPtr<class SScrollBox> DestinationScrollBox;
    TArray<TSharedPtr<SWidget>> DestinationControls;
    TArray<TSharedPtr<SWidget>> ToolbarControls;
    TArray<TSharedPtr<SWidget>> ViewControls;
    TArray<TSharedPtr<SWidget>> PanelControls;
    TArray<TSharedPtr<SWidget>> RenderQualityControls;
    TWeakPtr<SWidget> FocusBeforeNavigation;
    BreziNavigation::Capture NavigationCapture;
    bool bControlsOpen = false;
    BreziNavigation::TourStartup InitialTour;
    bool bWalkthroughAutomation = false;
    bool bHudCursor = false;
    bool bDiscardMouseLookOnNextInput = false;
    TSet<FKey> HudMovementKeys;
    TMap<FKey, double> HudPressTimes;
    TMap<FKey, double> HudReleaseTimes;
    float MouseSensitivity = 1.0f;
    FDelegateHandle ApplicationDeactivatedHandle;
    FDelegateHandle ApplicationBackgroundHandle;
    BreziRenderQuality::Origin RenderQualityOrigin = BreziRenderQuality::Origin::FreshDefault;
    bool bRenderQualityLocked = false;
    bool bRenderQualityApplyFailed = false;
    bool bRenderQualitySaveFailed = false;
    int32 RenderQualityTraceEvents = 0;
    TSharedPtr<ISceneViewExtension, ESPMode::ThreadSafe> RenderQualityView;
    TArray<TWeakObjectPtr<URectLightComponent>> RenderQualityRoomLights;
    TArray<bool> RenderQualityRoomLightShadows;
    int32 RenderQualityLastLocalShadows = -1;
    TWeakObjectPtr<ADirectionalLight> Sun;
    TWeakObjectPtr<ASkyLight> Sky;
    FRotator DaySunRotation = FRotator::ZeroRotator;
    float DaySunIntensity = 80000.0f;
    float DaySkyIntensity = 1.0f;
    // bNight is the requested UI endpoint, including while transitioning.
    bool bNight = false;
    bool bTimeOfDayTransitioning = false;
    double TimeOfDayElapsed = 0.0;
    double ExteriorLightStartAlpha = 0.0;
    FQuat TimeOfDayStartRotation = FQuat::Identity;
    float TimeOfDayStartSunIntensity = 0.0f;
    float TimeOfDayStartSkyIntensity = 0.0f;
    TWeakObjectPtr<UCameraComponent> LightingExposureCamera;
    bool bLightingExposureCaptured = false;
    int32 LightingTraceEvents = 0;
    bool bPriorExposureSpeedUpOverride = false;
    bool bPriorExposureSpeedDownOverride = false;
    float PriorExposureSpeedUp = 0.0f;
    float PriorExposureSpeedDown = 0.0f;
    bool bReducedMotion = false;
    bool bUseSystemMotion = true;
    bool bIncreaseContrast = false;
    bool bReduceTransparency = false;
    FBreziDisplayPreferences SystemPreferences;
    void* AccessibilityObserver = nullptr;
    TSharedPtr<class SWrapBox> ViewButtons;
    TArray<FString> InterfaceViewIds;
};
