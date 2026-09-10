#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "Engine/TimerHandle.h"
#include "BreziNativeAccessibility.h"
#include "BreziRenderQualityPolicy.h"
#include "BreziPlayerController.generated.h"

class SWidget;
class FReply;
struct FKeyEvent;
class ABreziPawn;
class ADirectionalLight;
class ASkyLight;
class UCameraComponent;
class UBreziRuntimeDiagnostics;
class UBreziWalkingTraversal;
class UBreziMotionQA;
class UBreziFlameStudy;
class UBreziExteriorLighting;

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
    void RefreshInterface();
    // Only numeric presets; the owned inner Slate viewport also retains raw Mac key codes.
    FReply HandlePresetShortcut(const FKeyEvent& Event, bool* OutRecognized = nullptr);

private:
    UPROPERTY() TObjectPtr<UBreziRuntimeDiagnostics> Diagnostics;
    UPROPERTY() TObjectPtr<UBreziWalkingTraversal> WalkingTraversal;
    UPROPERTY() TObjectPtr<UBreziMotionQA> MotionQA;
    UPROPERTY() TObjectPtr<UBreziFlameStudy> FlameStudy;
    UPROPERTY() TObjectPtr<UBreziExteriorLighting> ExteriorLighting;
    ABreziPawn* TwinPawn() const;
    void BuildInterface();
    void UpdateAccessibleSubtrees();
    void BeginNavigation();
    void ToggleNavigation();
    void EndNavigation();
    void HandleEscape();
    void ToggleControls();
    void FocusFirstControl();
    void FocusControl(const TSharedPtr<SWidget>& Widget);
    FReply HandleInterfaceKey(const FKeyEvent& Event);
    void ZoomIn();
    void ZoomOut();
    void ToggleTimeOfDay();
    void SetTimeOfDay(bool bTargetNight, bool bInstant);
    void UpdateTimeOfDayTransition(float DeltaSeconds);
    void FinishTimeOfDayTransition(bool bResetExposure);
    bool BeginLightingTransitionExposure();
    void RestoreLightingTransitionExposure(double ObservedElapsed = -1.0, bool bResetIntent = false);
    void TraceLightingTransition(const TCHAR* Event, const TCHAR* RestoreState, bool bResetIntent, double ObservedElapsed);
    void SelectNumberedView(int32 Index);
    void SelectViewKey(FKey Key);
    void ToggleCameraMode();
    void ToggleReducedMotion();
    void UseSystemMotionPreference();
    void ApplyDisplayPreferences(FBreziDisplayPreferences Preferences);
    void InitializeRenderQuality();
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
    float GetViewDockWidth() const;
    void RefreshWindowTitle();
    FTimerHandle WindowTitleRetry;
    int32 WindowTitleAttempts = 0;

    TSharedPtr<SWidget> Interface;
    TSharedPtr<SWidget> ControlsAXContainer;
    TSharedPtr<SWidget> FeedbackAXContainer;
    TSharedPtr<SWidget> WalkingModeControl;
    TSharedPtr<class SButton> NavigationFeedback;
    TSharedPtr<class SButton> ControlsButton;
    TSharedPtr<class SButton> NavigationButton;
    TSharedPtr<class SScrollBox> ControlsScrollBox;
    TArray<TSharedPtr<SWidget>> ToolbarControls;
    TArray<TSharedPtr<SWidget>> ViewControls;
    TArray<TSharedPtr<SWidget>> PanelControls;
    TArray<TSharedPtr<SWidget>> RenderQualityControls;
    TWeakPtr<SWidget> FocusBeforeNavigation;
    bool bControlsOpen = false;
    BreziRenderQuality::Origin RenderQualityOrigin = BreziRenderQuality::Origin::FreshDefault;
    bool bRenderQualityLocked = false;
    bool bRenderQualityApplyFailed = false;
    bool bRenderQualitySaveFailed = false;
    int32 RenderQualityTraceEvents = 0;
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
