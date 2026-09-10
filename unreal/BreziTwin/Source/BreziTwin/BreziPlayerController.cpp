#include "BreziPlayerController.h"
#include "BreziPawn.h"
#include "BreziPresetKeyPolicy.h"
#include "BreziLightingTransitionMath.h"
#include "BreziRuntimeDiagnostics.h"
#include "BreziWalkingTraversal.h"
#include "BreziMotionQA.h"
#include "BreziFlameStudy.h"
#include "BreziExteriorLighting.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Camera/PlayerCameraManager.h"
#include "Camera/CameraComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/InputComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/SkyLight.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/IConsoleManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Styling/CoreStyle.h"
#include "SceneInterface.h"
#include "TimerManager.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Accessibility/SlateWidgetAccessibleTypes.h"
#include "Widgets/Layout/SBackgroundBlur.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SWindow.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "BreziTwin"

namespace
{
    void ApplyDeckNaniteFallback(UWorld* World)
    {
        check(IsInGameThread());
        if (!World || !World->IsGameWorld()) return;

        // The settled component-only A/B isolates the dark wedge to this deck's
        // Nanite representation. Keep its authored mesh/material/collision and
        // all other components unchanged; use the existing fallback at runtime.
        const FName SourceId(TEXT("DOM_01710"));
        const FString ExpectedMesh(TEXT("/Game/Brezi/Geometry/brezi-twin/StaticMeshes/DOM_01710.DOM_01710"));
        AActor* Target = nullptr;
        int32 Matches = 0;
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if (It->ActorHasTag(SourceId)) { Target = *It; ++Matches; }
        }
        if (Matches != 1 || !Target->ActorHasTag(TEXT("BreziGenerated")))
        {
            UE_LOG(LogTemp, Error, TEXT("BreziDeckNaniteFallback rejected source=DOM_01710 reason=source-identity matches=%d world=%s"), Matches, *World->GetPathName());
            return;
        }
        TArray<UStaticMeshComponent*> Components;
        Target->GetComponents(Components);
        UStaticMeshComponent* Component = Components.Num() == 1 ? Components[0] : nullptr;
        UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
        if (!Component || Component->GetClass() != UStaticMeshComponent::StaticClass()
            || !Mesh || Mesh->GetPathName() != ExpectedMesh || !Component->IsRegistered() || !Component->GetScene())
        {
            UE_LOG(LogTemp, Error, TEXT("BreziDeckNaniteFallback rejected source=DOM_01710 reason=component-identity actor=%s components=%d mesh=%s"), *Target->GetPathName(), Components.Num(), *GetPathNameSafe(Mesh));
            return;
        }
        // Match the engine's fallback eligibility before changing the bit. A
        // forced fallback without cooked LOD data or allowed proxies can vanish.
        const int32 LODCount = Mesh->GetNumLODs();
        const int32 MinimumLOD = Component->GetOverrideMinLOD()
            ? FMath::Max(Component->GetMinLOD(), Mesh->GetMinLODIdx()) : Mesh->GetMinLODIdx();
        const int32 LOD = FMath::Clamp(MinimumLOD, 0, FMath::Max(0, LODCount - 1));
        const IConsoleVariable* ProxyMode = IConsoleManager::Get().FindConsoleVariable(TEXT("r.Nanite.ProxyRenderMode"));
        const bool bHasNanite = Mesh->HasValidNaniteData();
        const bool bFallbackAvailable = LODCount > 0 && Mesh->GetNumVertices(LOD) > 0 && Mesh->GetNumTriangles(LOD) > 0
            && (!bHasNanite || (ProxyMode && ProxyMode->GetInt() == 0
                && Mesh->HasNaniteFallbackMesh(Component->GetScene()->GetShaderPlatform())));
        if (!bFallbackAvailable)
        {
            UE_LOG(LogTemp, Error, TEXT("BreziDeckNaniteFallback rejected source=DOM_01710 reason=fallback-unavailable component=%s mesh=%s lod=%d proxyMode=%d"), *Component->GetPathName(), *Mesh->GetPathName(), LOD, ProxyMode ? ProxyMode->GetInt() : -1);
            return;
        }
        const bool bBefore = Component->IsForceDisableNanite();
        Component->SetForceDisableNanite(true); // The setter invalidates the render state when needed.
        if (!Component->IsForceDisableNanite())
        {
            UE_LOG(LogTemp, Error, TEXT("BreziDeckNaniteFallback rejected source=DOM_01710 reason=setter-readback component=%s"), *Component->GetPathName());
            return;
        }
        UE_LOG(LogTemp, Display, TEXT("BreziDeckNaniteFallback applied source=DOM_01710 actor=%s component=%s mesh=%s before=%d forceDisableNanite=%d fallbackLod=%d fallbackTriangles=%d renderedProxyObserved=0"),
            *Target->GetPathName(), *Component->GetPathName(), *Mesh->GetPathName(), bBefore, Component->IsForceDisableNanite(), LOD, Mesh->GetNumTriangles(LOD));
    }

    // The active control set owns its Tab cycle in preview; Enter/Space remain
    // native widget actions until they bubble here unconsumed.
    class SBreziInterface final : public SCompoundWidget
    {
    public:
        SLATE_BEGIN_ARGS(SBreziInterface) {}
            SLATE_DEFAULT_SLOT(FArguments, Content)
            SLATE_EVENT(FOnKeyDown, OnUnhandledKey)
            SLATE_EVENT(FOnKeyDown, OnPreviewTab)
        SLATE_END_ARGS()
        void Construct(const FArguments& Args)
        {
            OnUnhandledKey = Args._OnUnhandledKey;
            OnPreviewTab = Args._OnPreviewTab;
            ChildSlot[Args._Content.Widget];
        }
        virtual FReply OnPreviewKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override
        {
            // SWidget consumes Tab for default navigation in OnKeyDown. Handle the
            // toolbar/dock or open help cycle before that child-level consumption.
            return Event.GetKey() == EKeys::Tab && OnPreviewTab.IsBound()
                ? OnPreviewTab.Execute(Geometry, Event) : FReply::Unhandled();
        }
        virtual FReply OnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override
        {
            return OnUnhandledKey.IsBound() ? OnUnhandledKey.Execute(Geometry, Event) : FReply::Unhandled();
        }
    private:
        FOnKeyDown OnUnhandledKey;
        FOnKeyDown OnPreviewTab;
    };

    const FLinearColor Ink(0.92f, 0.92f, 0.87f, 1.0f);
    const FLinearColor Quiet(0.65f, 0.70f, 0.69f, 1.0f);
    const FLinearColor Accent(0.67f, 0.78f, 0.63f, 1.0f);
    const FSlateRoundedBoxBrush PanelBrush(FLinearColor::White, 16.0f, FLinearColor(1, 1, 1, 0.15f), 1.0f);
    const FSlateRoundedBoxBrush ContrastPanelBrush(FLinearColor::White, 16.0f, FLinearColor(1, 1, 1, 0.8f), 1.0f);
    const FSlateRoundedBoxBrush SolidPanelBrush(FLinearColor(0.022f, 0.033f, 0.033f, 1), 16.0f);

    const FButtonStyle& QuietButtonStyle()
    {
        static const FButtonStyle Style = FButtonStyle()
            .SetNormal(FSlateRoundedBoxBrush(FLinearColor::Transparent, 10.0f))
            .SetHovered(FSlateRoundedBoxBrush(FLinearColor(1, 1, 1, 0.10f), 10.0f))
            .SetPressed(FSlateRoundedBoxBrush(FLinearColor(1, 1, 1, 0.17f), 10.0f))
            .SetNormalPadding(FMargin(0)).SetPressedPadding(FMargin(0));
        return Style;
    }

    const FCheckBoxStyle& QuietToggleStyle()
    {
        static const FCheckBoxStyle Style = FCheckBoxStyle()
            .SetCheckBoxType(ESlateCheckBoxType::ToggleButton)
            .SetUncheckedImage(FSlateRoundedBoxBrush(FLinearColor::Transparent, 10.0f))
            .SetUncheckedHoveredImage(FSlateRoundedBoxBrush(FLinearColor(1, 1, 1, 0.10f), 10.0f))
            .SetUncheckedPressedImage(FSlateRoundedBoxBrush(FLinearColor(1, 1, 1, 0.17f), 10.0f))
            .SetCheckedImage(FSlateRoundedBoxBrush(FLinearColor(1, 1, 1, 0.05f), 10.0f))
            .SetCheckedHoveredImage(FSlateRoundedBoxBrush(FLinearColor(1, 1, 1, 0.13f), 10.0f))
            .SetCheckedPressedImage(FSlateRoundedBoxBrush(FLinearColor(1, 1, 1, 0.20f), 10.0f))
            .SetPadding(FMargin(0));
        return Style;
    }

    FAccessibleWidgetData AccessibleControl(TAttribute<FText> Label)
    {
        FAccessibleWidgetData Data(EAccessibleBehavior::Custom, EAccessibleBehavior::Custom, false);
        Data.AccessibleText = Label;
        Data.AccessibleSummaryText = Label;
        return Data;
    }

    FSlateFontInfo Font(const char* Weight, int32 Size, int32 Tracking = 0)
    {
        FSlateFontInfo Result = FCoreStyle::GetDefaultFontStyle(Weight, Size);
        Result.LetterSpacing = Tracking;
        return Result;
    }
}

ABreziPawn* ABreziPlayerController::TwinPawn() const { return Cast<ABreziPawn>(GetPawn()); }

ABreziPlayerController::ABreziPlayerController()
{
    Diagnostics = CreateDefaultSubobject<UBreziRuntimeDiagnostics>(TEXT("RuntimeDiagnostics"));
    WalkingTraversal = CreateDefaultSubobject<UBreziWalkingTraversal>(TEXT("WalkingTraversal"));
    MotionQA = CreateDefaultSubobject<UBreziMotionQA>(TEXT("MotionQA"));
    FlameStudy = CreateDefaultSubobject<UBreziFlameStudy>(TEXT("FlameStudy"));
    ExteriorLighting = CreateDefaultSubobject<UBreziExteriorLighting>(TEXT("ExteriorLighting"));
}

void ABreziPlayerController::BeginPlay()
{
    Super::BeginPlay();
    if (IsLocalController()) ApplyDeckNaniteFallback(GetWorld());
    InitializeRenderQuality();
    ApplyDisplayPreferences(BreziNativeAccessibility::Read());
    const TWeakObjectPtr<ABreziPlayerController> WeakThis(this);
    AccessibilityObserver = BreziNativeAccessibility::Observe([WeakThis](FBreziDisplayPreferences Preferences)
    {
        if (ABreziPlayerController* Controller = WeakThis.Get()) Controller->ApplyDisplayPreferences(Preferences);
    });
    for (TActorIterator<ADirectionalLight> It(GetWorld()); It; ++It)
    {
        if (!Sun.IsValid() || It->ActorHasTag(TEXT("BreziSun"))) Sun = *It;
        if (It->ActorHasTag(TEXT("BreziSun"))) break;
    }
    for (TActorIterator<ASkyLight> It(GetWorld()); It; ++It)
    {
        if (!Sky.IsValid() || It->ActorHasTag(TEXT("BreziSky"))) Sky = *It;
        if (It->ActorHasTag(TEXT("BreziSky"))) break;
    }
    if (Sun.IsValid())
    {
        DaySunRotation = Sun->GetActorRotation();
        DaySunIntensity = Sun->GetLightComponent()->Intensity;
    }
    if (Sky.IsValid()) DaySkyIntensity = Sky->GetLightComponent()->Intensity;
    if (IsLocalController()) ExteriorLighting->Initialize();
    TraceLightingTransition(TEXT("initial"), TEXT("no-capture"), false, TimeOfDayElapsed);
    if (FParse::Param(FCommandLine::Get(), TEXT("BreziNight"))) SetTimeOfDay(true, true);
    BuildInterface();
    EndNavigation();
    RefreshWindowTitle();
    // During BeginPlay the game viewport can still be waiting for its Slate window.
    // Recheck briefly after creation and startup fullscreen/resolution changes, then stop.
    GetWorldTimerManager().SetTimer(WindowTitleRetry, this, &ABreziPlayerController::RefreshWindowTitle, 0.1f, true);
    BreziNativeAccessibility::EnableNativeWidgetAccess();
}

void ABreziPlayerController::RefreshWindowTitle()
{
    ++WindowTitleAttempts;
    if (GEngine && GEngine->GameViewport)
    {
        if (TSharedPtr<SWindow> Window = GEngine->GameViewport->GetWindow())
        {
            const FText Title = LOCTEXT("WindowTitle", "Březí 6012/26");
            if (!Window->GetTitle().EqualTo(Title)) Window->SetTitle(Title);
        }
    }
    if (WindowTitleAttempts >= 50) GetWorldTimerManager().ClearTimer(WindowTitleRetry);
}

void ABreziPlayerController::EndPlay(const EEndPlayReason::Type Reason)
{
    TraceLightingTransition(TEXT("end-play"), TEXT("before-restore"), false, TimeOfDayElapsed);
    bTimeOfDayTransitioning = false;
    RestoreLightingTransitionExposure();
    GetWorldTimerManager().ClearTimer(WindowTitleRetry);
    ExteriorLighting->Shutdown();
    BreziNativeAccessibility::StopObserving(AccessibilityObserver);
    AccessibilityObserver = nullptr;
    if (Interface.IsValid() && GEngine && GEngine->GameViewport) GEngine->GameViewport->RemoveViewportWidgetContent(Interface.ToSharedRef());
    Interface.Reset();
    ControlsAXContainer.Reset();
    FeedbackAXContainer.Reset();
    ViewButtons.Reset();
    ControlsButton.Reset();
    NavigationButton.Reset();
    WalkingModeControl.Reset();
    NavigationFeedback.Reset();
    ControlsScrollBox.Reset();
    ToolbarControls.Empty();
    ViewControls.Empty();
    PanelControls.Empty();
    RenderQualityControls.Empty();
    FocusBeforeNavigation.Reset();
    Super::EndPlay(Reason);
}

void ABreziPlayerController::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    UpdateTimeOfDayTransition(DeltaSeconds);
    UpdateAccessibleSubtrees();
}

void ABreziPlayerController::UpdateAccessibleSubtrees()
{
    // Visibility alone does not filter UE's Mac accessibleChildren list. These stable,
    // nonaccessible container widgets exclude whole inactive subtrees without rebuilding UI.
    const bool bShowFeedback = TwinPawn() && !TwinPawn()->GetNavigationMessage().IsEmpty();
    if (!bShowFeedback && NavigationFeedback.IsValid() && FSlateApplication::IsInitialized()
        && FSlateApplication::Get().GetKeyboardFocusedWidget() == NavigationFeedback)
        FocusControl(WalkingModeControl);
    if (ControlsAXContainer.IsValid()) ControlsAXContainer->SetCanChildrenBeAccessible(bControlsOpen);
    if (FeedbackAXContainer.IsValid()) FeedbackAXContainer->SetCanChildrenBeAccessible(bShowFeedback);
}

void ABreziPlayerController::OnPossess(APawn* InPawn)
{
    if (bTimeOfDayTransitioning) FinishTimeOfDayTransition(true);
    Super::OnPossess(InPawn);
    if (HasActorBegunPlay() && InPawn && InPawn->HasActorBegunPlay()) RefreshInterface();
}

void ABreziPlayerController::RefreshInterface()
{
    if (ABreziPawn* Pawn = TwinPawn()) Pawn->SetReducedMotion(bReducedMotion);
    if (IsLocalController() && HasActorBegunPlay())
    {
        if (Interface.IsValid()) UpdateViewButtons();
        else BuildInterface();
    }
}

void ABreziPlayerController::SetupInputComponent()
{
    Super::SetupInputComponent();
    InputComponent->BindKey(EKeys::RightMouseButton, IE_Pressed, this, &ABreziPlayerController::BeginNavigation);
    InputComponent->BindKey(EKeys::RightMouseButton, IE_Released, this, &ABreziPlayerController::EndNavigation);
    InputComponent->BindKey(EKeys::Escape, IE_Pressed, this, &ABreziPlayerController::HandleEscape);
    InputComponent->BindKey(EKeys::Tab, IE_Pressed, this, &ABreziPlayerController::FocusFirstControl);
    InputComponent->BindKey(EKeys::F1, IE_Pressed, this, &ABreziPlayerController::ToggleControls);
    InputComponent->BindKey(EKeys::F2, IE_Pressed, this, &ABreziPlayerController::ToggleNavigation);
    InputComponent->BindKey(EKeys::MouseScrollUp, IE_Pressed, this, &ABreziPlayerController::ZoomIn);
    InputComponent->BindKey(EKeys::MouseScrollDown, IE_Pressed, this, &ABreziPlayerController::ZoomOut);
    // Keyboard zoom uses the same bounded orbit radius as the wheel. The extra
    // Shift chord covers the main + key; keypad +/- have native Mac key mappings.
    InputComponent->BindKey(EKeys::Equals, IE_Pressed, this, &ABreziPlayerController::ZoomIn);
    InputComponent->BindKey(FInputChord(EKeys::Equals, true, false, false, false), IE_Pressed, this, &ABreziPlayerController::ZoomIn);
    InputComponent->BindKey(EKeys::Hyphen, IE_Pressed, this, &ABreziPlayerController::ZoomOut);
    // Layout-independent fallback: macOS Fn + Up/Down emits PageUp/PageDown.
    InputComponent->BindKey(EKeys::PageUp, IE_Pressed, this, &ABreziPlayerController::ZoomIn);
    InputComponent->BindKey(EKeys::PageDown, IE_Pressed, this, &ABreziPlayerController::ZoomOut);
    InputComponent->BindKey(EKeys::Add, IE_Pressed, this, &ABreziPlayerController::ZoomIn);
    InputComponent->BindKey(EKeys::Subtract, IE_Pressed, this, &ABreziPlayerController::ZoomOut);
    InputComponent->BindKey(EKeys::N, IE_Pressed, this, &ABreziPlayerController::ToggleTimeOfDay);
#if PLATFORM_MAC
    // The packaged/standalone inner viewport preserves raw key codes. PIE keeps
    // its existing engine viewport and legacy bindings; it is a separate route.
    // Never bind this fallback in the app: BindKey permits extra Command modifiers.
    if (GIsEditor)
#endif
    {
        InputComponent->BindKey(EKeys::One, IE_Pressed, this, &ABreziPlayerController::SelectViewKey);
        InputComponent->BindKey(EKeys::Two, IE_Pressed, this, &ABreziPlayerController::SelectViewKey);
        InputComponent->BindKey(EKeys::Three, IE_Pressed, this, &ABreziPlayerController::SelectViewKey);
        InputComponent->BindKey(EKeys::Four, IE_Pressed, this, &ABreziPlayerController::SelectViewKey);
    }
    InputComponent->BindKey(EKeys::M, IE_Pressed, this, &ABreziPlayerController::ToggleCameraMode);
}

void ABreziPlayerController::BeginNavigation()
{
    ABreziPawn* Pawn = TwinPawn();
    // Repeated pointer presses must not replace the control we return to on Escape.
    if (bControlsOpen || !Pawn || !Pawn->HasViewpoints() || Pawn->IsNavigating()) return;
    if (FSlateApplication::IsInitialized()) FocusBeforeNavigation = FSlateApplication::Get().GetKeyboardFocusedWidget();
    Pawn->SetNavigating(true);
    bShowMouseCursor = false;
    SetInputMode(FInputModeGameOnly());
}

void ABreziPlayerController::ToggleNavigation()
{
    if (TwinPawn() && TwinPawn()->IsNavigating()) EndNavigation();
    else BeginNavigation();
}

void ABreziPlayerController::EndNavigation()
{
    const bool bWasNavigating = TwinPawn() && TwinPawn()->IsNavigating();
    if (ABreziPawn* Pawn = TwinPawn()) Pawn->SetNavigating(false);
    bShowMouseCursor = true;
    FInputModeGameAndUI Mode;
    Mode.SetHideCursorDuringCapture(false);
    Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    SetInputMode(Mode);
    if (bWasNavigating)
    {
        if (TSharedPtr<SWidget> Previous = FocusBeforeNavigation.Pin(); Previous.IsValid() && Previous->SupportsKeyboardFocus()) FocusControl(Previous);
        FocusBeforeNavigation.Reset();
    }
}

void ABreziPlayerController::FocusControl(const TSharedPtr<SWidget>& Widget)
{
    if (!Widget.IsValid() || !FSlateApplication::IsInitialized()) return;
    FSlateApplication::Get().SetKeyboardFocus(Widget, EFocusCause::Navigation);
    if (bControlsOpen && ControlsScrollBox.IsValid() && PanelControls.Contains(Widget))
        ControlsScrollBox->ScrollDescendantIntoView(Widget, false, EDescendantScrollDestination::IntoView, 8.0f);
}

void ABreziPlayerController::FocusFirstControl()
{
    EndNavigation();
    const TArray<TSharedPtr<SWidget>>& Controls = bControlsOpen ? PanelControls : ToolbarControls;
    if (!Controls.IsEmpty()) FocusControl(Controls[0]);
}

void ABreziPlayerController::ToggleControls()
{
    EndNavigation();
    bControlsOpen = !bControlsOpen;
    // Return focus before excluding a closing subtree from accessibility participation.
    if (!bControlsOpen) FocusControl(ControlsButton);
    UpdateAccessibleSubtrees();
    if (bControlsOpen && !PanelControls.IsEmpty()) FocusControl(PanelControls[0]);
}

void ABreziPlayerController::HandleEscape()
{
    if (bControlsOpen) ToggleControls();
    else EndNavigation();
}

FReply ABreziPlayerController::HandleInterfaceKey(const FKeyEvent& Event)
{
    const FReply PresetReply = HandlePresetShortcut(Event);
    if (PresetReply.IsEventHandled()) return PresetReply;
    // Preserve VoiceOver's Control/Option chords and native macOS Command shortcuts.
    if (Event.IsControlDown() || Event.IsAltDown() || Event.IsCommandDown()) return FReply::Unhandled();
    const FKey Key = Event.GetKey();
    if (Key == EKeys::Tab)
    {
        TArray<TSharedPtr<SWidget>> Controls = bControlsOpen ? PanelControls : ToolbarControls;
        if (!bControlsOpen)
        {
            Controls.Append(ViewControls);
            if (NavigationFeedback.IsValid() && TwinPawn() && !TwinPawn()->GetNavigationMessage().IsEmpty()) Controls.Add(NavigationFeedback);
            if (NavigationButton.IsValid()) Controls.Add(NavigationButton);
        }
        Controls.RemoveAll([](const TSharedPtr<SWidget>& Widget) { return !Widget.IsValid() || !Widget->IsEnabled() || !Widget->GetVisibility().IsVisible(); });
        if (!Controls.IsEmpty())
        {
            const int32 Current = Controls.IndexOfByKey(FSlateApplication::Get().GetKeyboardFocusedWidget());
            const int32 Next = Current == INDEX_NONE ? (Event.IsShiftDown() ? Controls.Num() - 1 : 0)
                : (Current + (Event.IsShiftDown() ? -1 : 1) + Controls.Num()) % Controls.Num();
            FocusControl(Controls[Next]);
            // Opt-in, bounded diagnostics of this known control key only. This
            // records the delivered Slate modifier; it never fabricates Shift.
            static const bool bTraceControlKeys = FParse::Param(FCommandLine::Get(), TEXT("BreziTraceControlKeys"));
            static int32 TracedHelpTabs = 0;
            if (bControlsOpen && bTraceControlKeys && TracedHelpTabs < 64)
            {
                ++TracedHelpTabs;
                const int32 Actual = Controls.IndexOfByKey(FSlateApplication::Get().GetKeyboardFocusedWidget());
                UE_LOG(LogTemp, Display, TEXT("BreziControlKey: help Tab sample=%d shift=%d repeat=%d direction=%s current=%d next=%d actual=%d controlCount=%d"),
                    TracedHelpTabs, Event.IsShiftDown(), Event.IsRepeat(), Event.IsShiftDown() ? TEXT("previous") : TEXT("next"),
                    Current, Next, Actual, Controls.Num());
            }
        }
        return FReply::Handled();
    }
    if (Key == EKeys::Escape) { HandleEscape(); return FReply::Handled(); }
    if (Event.IsRepeat()) return FReply::Unhandled();
    if (Key == EKeys::F1) { ToggleControls(); return FReply::Handled(); }
    if (Key == EKeys::F2) { ToggleNavigation(); return FReply::Handled(); }
    if (Key == EKeys::N) { ToggleTimeOfDay(); return FReply::Handled(); }
    if (Key == EKeys::M) { ToggleCameraMode(); return FReply::Handled(); }
    if (Key == EKeys::Equals || ((Key == EKeys::Add || Key == EKeys::PageUp) && !Event.IsShiftDown()))
    { ZoomIn(); return FReply::Handled(); }
    if ((Key == EKeys::Hyphen || Key == EKeys::Subtract || Key == EKeys::PageDown) && !Event.IsShiftDown())
    { ZoomOut(); return FReply::Handled(); }
    return FReply::Unhandled();
}

FReply ABreziPlayerController::HandlePresetShortcut(const FKeyEvent& Event, bool* OutRecognized)
{
    const FKey Key = Event.GetKey();
    const int32 LogicalIndex = Key == EKeys::One || Key == EKeys::NumPadOne ? 0
        : Key == EKeys::Two || Key == EKeys::NumPadTwo ? 1
        : Key == EKeys::Three || Key == EKeys::NumPadThree ? 2
        : Key == EKeys::Four || Key == EKeys::NumPadFour ? 3 : INDEX_NONE;
    const int32 Index = BreziPresetKeys::Resolve(PLATFORM_MAC != 0, Event.GetKeyCode(), LogicalIndex);
    if (OutRecognized) *OutRecognized = Index != INDEX_NONE;
    if (Index == INDEX_NONE) return FReply::Unhandled();
    const auto Action = BreziPresetKeys::Decide(Index, Event.IsControlDown(), Event.IsAltDown(), Event.IsCommandDown(), Event.IsRepeat());
    const ABreziPawn* Pawn = TwinPawn();
    const bool bAvailable = IsLocalController() && Pawn && Pawn->GetViewpoints().IsValidIndex(Index);
    const bool bSelect = Action == BreziPresetKeys::Action::Select && bAvailable;
    if (bSelect) SelectNumberedView(Index);

    static const bool bTrace = FParse::Param(FCommandLine::Get(), TEXT("BreziTraceControlKeys"));
    static int32 Samples = 0;
    if (bTrace && Samples < 64)
    {
        const bool bPanelFocus = bControlsOpen && PanelControls.ContainsByPredicate([](const TSharedPtr<SWidget>& Widget)
        { return Widget.IsValid() && (Widget->HasKeyboardFocus() || Widget->HasFocusedDescendants()); });
        const TCHAR* Result = Action == BreziPresetKeys::Action::Unhandled ? TEXT("modifier-unhandled")
            : !bAvailable ? TEXT("unavailable") : bSelect ? TEXT("select") : TEXT("repeat-consumed");
        UE_LOG(LogTemp, Display, TEXT("BreziPresetKey: sample=%d index=%d key=%s keyCode=%u character=%u shift=%d control=%d alt=%d command=%d repeat=%d action=%s panelOpen=%d panelFocus=%d"),
            ++Samples, Index, *Key.GetFName().ToString(), Event.GetKeyCode(), Event.GetCharacter(), Event.IsShiftDown(), Event.IsControlDown(),
            Event.IsAltDown(), Event.IsCommandDown(), Event.IsRepeat(), Result, bControlsOpen, bPanelFocus);
    }
    return Action != BreziPresetKeys::Action::Unhandled && bAvailable ? FReply::Handled() : FReply::Unhandled();
}

void ABreziPlayerController::ZoomIn() { if (ABreziPawn* Pawn = TwinPawn(); Pawn && !bControlsOpen) Pawn->Zoom(1.0f); }
void ABreziPlayerController::ZoomOut() { if (ABreziPawn* Pawn = TwinPawn(); Pawn && !bControlsOpen) Pawn->Zoom(-1.0f); }

void ABreziPlayerController::SelectNumberedView(int32 Index)
{
    if (ABreziPawn* Pawn = TwinPawn(); Pawn && Pawn->GetViewpoints().IsValidIndex(Index))
    {
        EndNavigation();
        Pawn->SelectView(Pawn->GetViewpoints()[Index].Id);
        if (bControlsOpen)
        {
            // A global preset does not move keyboard focus behind the open panel.
            const auto Usable = [](const TSharedPtr<SWidget>& Widget)
            { return Widget.IsValid() && Widget->IsEnabled() && Widget->GetVisibility().IsVisible(); };
            const bool bInsidePanel = PanelControls.ContainsByPredicate([&Usable](const TSharedPtr<SWidget>& Widget)
            { return Usable(Widget) && (Widget->HasKeyboardFocus() || Widget->HasFocusedDescendants()); });
            if (!bInsidePanel)
                if (const TSharedPtr<SWidget>* First = PanelControls.FindByPredicate(Usable)) FocusControl(*First);
        }
        else if (ViewControls.IsValidIndex(Index)) FocusControl(ViewControls[Index]);
    }
}

void ABreziPlayerController::SelectViewKey(FKey Key)
{
    if (Key == EKeys::One) SelectNumberedView(0);
    else if (Key == EKeys::Two) SelectNumberedView(1);
    else if (Key == EKeys::Three) SelectNumberedView(2);
    else if (Key == EKeys::Four) SelectNumberedView(3);
}

void ABreziPlayerController::ToggleCameraMode()
{
    EndNavigation();
    if (ABreziPawn* Pawn = TwinPawn())
    {
        if (!Pawn->ToggleMovementMode()) FocusControl(NavigationFeedback);
        else FocusControl(WalkingModeControl);
    }
}

void ABreziPlayerController::ToggleReducedMotion()
{
    bUseSystemMotion = false;
    bReducedMotion = !bReducedMotion;
    if (bReducedMotion && bTimeOfDayTransitioning) FinishTimeOfDayTransition(true);
    if (ABreziPawn* Pawn = TwinPawn()) Pawn->SetReducedMotion(bReducedMotion);
}

void ABreziPlayerController::UseSystemMotionPreference()
{
    bUseSystemMotion = true;
    ApplyDisplayPreferences(SystemPreferences);
}

void ABreziPlayerController::ApplyDisplayPreferences(FBreziDisplayPreferences Preferences)
{
    SystemPreferences = Preferences;
    bIncreaseContrast = Preferences.bIncreaseContrast;
    bReduceTransparency = Preferences.bReduceTransparency;
    if (bUseSystemMotion) bReducedMotion = Preferences.bReduceMotion;
    if (bReducedMotion && bTimeOfDayTransitioning) FinishTimeOfDayTransition(true);
    if (ABreziPawn* Pawn = TwinPawn()) Pawn->SetReducedMotion(bReducedMotion);
    // Slate attributes read these values in-place; changing accessibility never rebuilds or steals focus.
}

void ABreziPlayerController::ToggleTimeOfDay()
{
    SetTimeOfDay(!bNight, false);
}

bool ABreziPlayerController::BeginLightingTransitionExposure()
{
    ABreziPawn* Pawn = TwinPawn();
    UCameraComponent* Camera = Pawn ? Pawn->FindComponentByClass<UCameraComponent>() : nullptr;
    if (!Camera || Camera->GetFName() != FName(TEXT("ArchitectureCamera")) || Camera->PostProcessBlendWeight != 1.0f)
        return false;
    if (bLightingExposureCaptured && LightingExposureCamera.Get() != Camera) RestoreLightingTransitionExposure();
    FPostProcessSettings& Settings = Camera->PostProcessSettings;
    if (!bLightingExposureCaptured)
    {
        LightingExposureCamera = Camera;
        bPriorExposureSpeedUpOverride = Settings.bOverride_AutoExposureSpeedUp;
        bPriorExposureSpeedDownOverride = Settings.bOverride_AutoExposureSpeedDown;
        PriorExposureSpeedUp = Settings.AutoExposureSpeedUp;
        PriorExposureSpeedDown = Settings.AutoExposureSpeedDown;
        bLightingExposureCaptured = true;
    }
    // Capture once across reversals: never save our temporary values as originals.
    Settings.bOverride_AutoExposureSpeedUp = true;
    Settings.bOverride_AutoExposureSpeedDown = true;
    Settings.AutoExposureSpeedUp = BreziLightingTransition::ExposureSpeed;
    Settings.AutoExposureSpeedDown = BreziLightingTransition::ExposureSpeed;
    return true;
}

void ABreziPlayerController::RestoreLightingTransitionExposure(double ObservedElapsed, bool bResetIntent)
{
    const double TraceElapsed = ObservedElapsed >= 0.0 ? ObservedElapsed : TimeOfDayElapsed;
    if (!bLightingExposureCaptured)
    {
        TraceLightingTransition(TEXT("restore"), TEXT("no-capture"), bResetIntent, TraceElapsed);
        return;
    }
    if (UCameraComponent* Camera = LightingExposureCamera.Get())
    {
        FPostProcessSettings& Settings = Camera->PostProcessSettings;
        Settings.AutoExposureSpeedUp = PriorExposureSpeedUp;
        Settings.AutoExposureSpeedDown = PriorExposureSpeedDown;
        Settings.bOverride_AutoExposureSpeedUp = bPriorExposureSpeedUpOverride;
        Settings.bOverride_AutoExposureSpeedDown = bPriorExposureSpeedDownOverride;
        TraceLightingTransition(TEXT("restore"), TEXT("restored"), bResetIntent, TraceElapsed);
    }
    else TraceLightingTransition(TEXT("restore"), TEXT("camera-unavailable"), bResetIntent, TraceElapsed);
    bLightingExposureCaptured = false;
    LightingExposureCamera.Reset();
}

void ABreziPlayerController::TraceLightingTransition(const TCHAR* Event, const TCHAR* RestoreState, bool bResetIntent, double ObservedElapsed)
{
    static const bool bTrace = FParse::Param(FCommandLine::Get(), TEXT("BreziTraceControlKeys"));
    if (!bTrace || LightingTraceEvents >= 32) return;
    ++LightingTraceEvents;
    const ABreziPawn* Pawn = TwinPawn();
    // While restoring, inspect the captured camera itself. Never substitute a
    // replacement pawn camera for an unavailable captured object.
    const UCameraComponent* Camera = bLightingExposureCaptured ? LightingExposureCamera.Get()
        : (Pawn ? Pawn->FindComponentByClass<UCameraComponent>() : nullptr);
    const FPostProcessSettings* Settings = Camera ? &Camera->PostProcessSettings : nullptr;
    const FQuat Rotation = Sun.IsValid() ? Sun->GetActorQuat() : FQuat::Identity;
    const bool bPriorMatches = bLightingExposureCaptured && Settings
        && Settings->AutoExposureSpeedUp == PriorExposureSpeedUp && Settings->AutoExposureSpeedDown == PriorExposureSpeedDown
        && Settings->bOverride_AutoExposureSpeedUp == bPriorExposureSpeedUpOverride
        && Settings->bOverride_AutoExposureSpeedDown == bPriorExposureSpeedDownOverride;
    // Read-only component values, not the composed exposure or rendered camera-cut flag.
    // Presence/capture flags qualify zero placeholders and previously captured values.
    UE_LOG(LogTemp, Display, TEXT("BreziLightingTransition: event=%s sample=%d frame=%llu elapsedBeforeReset=%.9g elapsedNow=%.9g targetNight=%d transitioning=%d reducedMotion=%d resetIntent=%d cameraManagerPresent=%d restore=%s sunPresent=%d sunLux=%.9g sunQuat=(%.17g,%.17g,%.17g,%.17g) skyPresent=%d skyIntensity=%.9g cameraPresent=%d architectureCamera=%d cameraBlend=%.9g captureValid=%d priorUp=%.9g priorDown=%.9g priorOverrideUp=%d priorOverrideDown=%d currentUp=%.9g currentDown=%.9g currentOverrideUp=%d currentOverrideDown=%d priorMatches=%d"),
        Event, LightingTraceEvents, static_cast<unsigned long long>(GFrameCounter), ObservedElapsed, TimeOfDayElapsed,
        bNight, bTimeOfDayTransitioning, bReducedMotion, bResetIntent, PlayerCameraManager != nullptr, RestoreState,
        Sun.IsValid(), Sun.IsValid() ? Sun->GetLightComponent()->Intensity : 0.0f, Rotation.X, Rotation.Y, Rotation.Z, Rotation.W,
        Sky.IsValid(), Sky.IsValid() ? Sky->GetLightComponent()->Intensity : 0.0f,
        Camera != nullptr, Camera && Camera->GetFName() == FName(TEXT("ArchitectureCamera")), Camera ? Camera->PostProcessBlendWeight : 0.0f,
        bLightingExposureCaptured, PriorExposureSpeedUp, PriorExposureSpeedDown, bPriorExposureSpeedUpOverride, bPriorExposureSpeedDownOverride,
        Settings ? Settings->AutoExposureSpeedUp : 0.0f, Settings ? Settings->AutoExposureSpeedDown : 0.0f,
        Settings ? static_cast<int32>(Settings->bOverride_AutoExposureSpeedUp) : 0,
        Settings ? static_cast<int32>(Settings->bOverride_AutoExposureSpeedDown) : 0, bPriorMatches);
}

void ABreziPlayerController::SetTimeOfDay(bool bTargetNight, bool bInstant)
{
    const bool bWasTransitioning = bTimeOfDayTransitioning;
    const double PreviousElapsed = TimeOfDayElapsed;
    if (!Sun.IsValid())
    {
        bTimeOfDayTransitioning = false;
        ExteriorLighting->SetNightAlpha(0);
        RestoreLightingTransitionExposure();
        return;
    }
    bNight = bTargetNight;
    ExteriorLightStartAlpha = ExteriorLighting->GetNightAlpha();
    TimeOfDayStartRotation = Sun->GetActorQuat();
    TimeOfDayStartSunIntensity = Sun->GetLightComponent()->Intensity;
    TimeOfDayStartSkyIntensity = Sky.IsValid() ? Sky->GetLightComponent()->Intensity : DaySkyIntensity;
    if (bInstant || bReducedMotion || (Sky.IsValid() && !Sky->GetLightComponent()->IsRealTimeCaptureEnabled())
        || TimeOfDayStartRotation.ContainsNaN()
        || !BreziLightingTransition::PositiveIntensity(TimeOfDayStartSunIntensity)
        || !BreziLightingTransition::PositiveIntensity(DaySunIntensity)
        || !BreziLightingTransition::PositiveIntensity(TimeOfDayStartSkyIntensity)
        || !BreziLightingTransition::PositiveIntensity(DaySkyIntensity)
        || !BeginLightingTransitionExposure())
    {
        FinishTimeOfDayTransition(true);
        return;
    }
    // Reversing starts at actual in-flight light values; no target or camera jump.
    TimeOfDayElapsed = 0.0;
    bTimeOfDayTransitioning = true;
    TraceLightingTransition(bWasTransitioning ? TEXT("reverse") : TEXT("start"), TEXT("captured"), false, PreviousElapsed);
}

void ABreziPlayerController::UpdateTimeOfDayTransition(float DeltaSeconds)
{
    if (!bTimeOfDayTransitioning) return;
    if (!Sun.IsValid() || !LightingExposureCamera.IsValid() || LightingExposureCamera->GetOwner() != TwinPawn()
        || (Sky.IsValid() && !Sky->GetLightComponent()->IsRealTimeCaptureEnabled())
        || bReducedMotion || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds < 0.0f)
    {
        FinishTimeOfDayTransition(true);
        return;
    }
    TimeOfDayElapsed += DeltaSeconds;
    if (TimeOfDayElapsed >= BreziLightingTransition::DurationSeconds)
    {
        FinishTimeOfDayTransition(false);
        return;
    }
    const double Alpha = BreziLightingTransition::Progress(TimeOfDayElapsed);
    // Zero is a real off state: the positive-only sun/sky logarithmic interpolation cannot represent it.
    ExteriorLighting->SetNightAlpha(FMath::Lerp(ExteriorLightStartAlpha, bNight ? 1.0 : 0.0, Alpha));
    const FRotator TargetRotation = bNight ? FRotator(-25.0f, DaySunRotation.Yaw + 150.0f, 0.0f) : DaySunRotation;
    Sun->SetActorRotation(FQuat::Slerp(TimeOfDayStartRotation, TargetRotation.Quaternion(), Alpha).GetNormalized());
    Sun->GetLightComponent()->SetIntensity(static_cast<float>(BreziLightingTransition::Intensity(
        TimeOfDayStartSunIntensity, bNight ? 0.15f : DaySunIntensity, Alpha)));
    if (Sky.IsValid()) Sky->GetLightComponent()->SetIntensity(static_cast<float>(BreziLightingTransition::Intensity(
        TimeOfDayStartSkyIntensity, bNight ? DaySkyIntensity * 0.035f : DaySkyIntensity, Alpha)));
    // Real-time sky capture and Lumen retain history; this is not a convergence fence.
}

void ABreziPlayerController::FinishTimeOfDayTransition(bool bResetExposure)
{
    const double CompletedElapsed = TimeOfDayElapsed;
    bTimeOfDayTransitioning = false;
    TimeOfDayElapsed = 0.0;
    if (Sun.IsValid())
    {
        // Exact existing endpoints, not the result of a final interpolated float.
        Sun->SetActorRotation(bNight ? FRotator(-25.0f, DaySunRotation.Yaw + 150.0f, 0.0f) : DaySunRotation);
        Sun->GetLightComponent()->SetIntensity(bNight ? 0.15f : DaySunIntensity);
    }
    if (Sky.IsValid())
    {
        Sky->GetLightComponent()->SetIntensity(bNight ? DaySkyIntensity * 0.035f : DaySkyIntensity);
        if (bResetExposure && !Sky->GetLightComponent()->IsRealTimeCaptureEnabled()) Sky->GetLightComponent()->RecaptureSky();
    }
    ExteriorLighting->SetNightAlpha(Sun.IsValid() && bNight ? 1.0 : 0.0);
    RestoreLightingTransitionExposure(CompletedElapsed, bResetExposure);
    // Only instant/reduced-motion/interrupted lifecycle paths reset exposure/history.
    if (bResetExposure && PlayerCameraManager) PlayerCameraManager->SetGameCameraCutThisFrame();
    TraceLightingTransition(TEXT("finish"), TEXT("see-restore-event"), bResetExposure, CompletedElapsed);
}

float ABreziPlayerController::GetViewDockWidth() const
{
    // The root overlay fills the viewport. Read its independent Slate-space geometry,
    // not the dock's desired size or pixel backbuffer, so Retina scaling stays correct.
    const float ViewportWidth = Interface.IsValid() ? Interface->GetCachedGeometry().GetLocalSize().X : 0.0f;
    constexpr float HorizontalSafeInsets = 28.0f * 2.0f;
    return ViewportWidth > 0.0f ? FMath::Min(560.0f, FMath::Max(1.0f, ViewportWidth - HorizontalSafeInsets)) : 560.0f;
}

void ABreziPlayerController::UpdateViewButtons()
{
    if (!ViewButtons.IsValid()) return;
    const ABreziPawn* Pawn = TwinPawn();
    if (!Pawn) return;
    TArray<FString> NewIds;
    for (const FBreziViewpoint& View : Pawn->GetViewpoints()) NewIds.Add(View.Id + TEXT("|") + View.Label);
    if (NewIds == InterfaceViewIds) return;
    InterfaceViewIds = MoveTemp(NewIds);
    ViewButtons->ClearChildren();
    ViewControls.Empty();
    int32 Index = 0;
    for (const FBreziViewpoint& View : Pawn->GetViewpoints())
    {
        const FString Id = View.Id;
        const int32 Shortcut = ++Index;
        const FText Label = FText::FromString(View.Label);
        TSharedPtr<SButton> ViewButton;
        ViewButtons->AddSlot()
        [
            SAssignNew(ViewButton, SButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(20, 13))
            .AccessibleParams(AccessibleControl(TAttribute<FText>::CreateLambda([this, Id, Label]
            { return TwinPawn() && TwinPawn()->GetActiveViewId() == Id ? FText::Format(LOCTEXT("CurrentView", "{0}, aktuálny pohľad"), Label) : Label; })))
            .ToolTipText(FText::Format(LOCTEXT("ViewHint", "{0} · kláves {1}"), FText::FromString(View.Label), FText::AsNumber(Shortcut)))
            .OnClicked_Lambda([this, Id] { EndNavigation(); if (ABreziPawn* Current = TwinPawn()) Current->SelectView(Id); return FReply::Handled(); })
            [
                SNew(SVerticalBox)
                + SVerticalBox::Slot().AutoHeight()
                [SNew(STextBlock).Text(FText::FromString(View.Label)).Font(Font("Regular", 14, 10)).ColorAndOpacity_Lambda([this, Id]
                { return FSlateColor(bIncreaseContrast ? FLinearColor::White : TwinPawn() && TwinPawn()->GetActiveViewId() == Id ? Accent : Ink); })]
                + SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0, 5, 0, 0)
                [SNew(SBox).WidthOverride(16).HeightOverride(2)
                    [SNew(SBorder).Padding(0).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor_Lambda([this, Id]
                    { return TwinPawn() && TwinPawn()->GetActiveViewId() == Id ? (bIncreaseContrast ? FLinearColor::White : Accent) : FLinearColor::Transparent; })]]
            ]
        ];
        ViewControls.Add(ViewButton);
    }
}

TSharedRef<SWidget> ABreziPlayerController::BuildRenderQualityChoices()
{
    using BreziRenderQuality::Profile;
    RenderQualityControls.Empty();
    const auto Visible = [this] { return bControlsOpen ? EVisibility::Visible : EVisibility::Collapsed; };
    TSharedRef<SVerticalBox> Choices = SNew(SVerticalBox);
    Choices->AddSlot().AutoHeight().Padding(8, 3, 8, 6)
    [SNew(STextBlock).Visibility_Lambda(Visible).Text(LOCTEXT("QualityTitle", "KVALITA OBRAZU"))
        .Font(Font("Bold", 10, 80)).ColorAndOpacity(Ink)];
    for (Profile Value : {Profile::Native, Profile::Balanced, Profile::Performance})
    {
        const FText Label = Value == Profile::Native ? LOCTEXT("QualityNative", "Natívny detail")
            : Value == Profile::Balanced ? LOCTEXT("QualityBalanced", "Vyvážené") : LOCTEXT("QualityPerformance", "Plynulosť");
        const FText Detail = Value == Profile::Native ? LOCTEXT("QualityNativeDetail", "Najjemnejšie detaily")
            : Value == Profile::Balanced ? LOCTEXT("QualityBalancedDetail", "Rovnováha detailov a plynulosti")
            : LOCTEXT("QualityPerformanceDetail", "Nižšie vnútorné rozlíšenie");
        TSharedPtr<SCheckBox> Choice;
        Choices->AddSlot().AutoHeight().Padding(0, 1)
        [SAssignNew(Choice, SCheckBox).Style(&QuietToggleStyle()).Padding(FMargin(8, 8)).Visibility_Lambda(Visible)
            .IsEnabled_Lambda([this] { return CanChangeRenderQuality(); })
            .AccessibleParams(AccessibleControl(TAttribute<FText>::CreateLambda([this, Value, Label, Detail]
            { return FText::Format(IsRenderQualitySelected(Value) ? LOCTEXT("QualitySelectedAX", "{0}, vybrané. {1}")
                : LOCTEXT("QualityChoiceAX", "{0}. {1}"), Label, Detail); })))
            .IsChecked_Lambda([this, Value] { return IsRenderQualitySelected(Value) ? ECheckBoxState::Checked : ECheckBoxState::Unchecked; })
            .OnCheckStateChanged_Lambda([this, Value](ECheckBoxState)
            {
                // A deliberate click on the already-selected launch/default choice must save it too.
                // The actual-value binding keeps this radio-like group selected after an Unchecked event.
                SelectRenderQuality(Value);
            })
            [SNew(SVerticalBox)
                + SVerticalBox::Slot().AutoHeight()
                [SNew(STextBlock).Text(Label).Font(Font("Regular", 12)).ColorAndOpacity(Ink)]
                + SVerticalBox::Slot().AutoHeight().Padding(0, 2, 0, 0)
                [SNew(STextBlock).Text(Detail).Font(Font("Regular", 10)).AutoWrapText(true)
                    .ColorAndOpacity_Lambda([this] { return FSlateColor(bIncreaseContrast ? Ink : Quiet); })]]];
        RenderQualityControls.Add(Choice);
    }
    Choices->AddSlot().AutoHeight().Padding(8, 7, 8, 15)
    [SNew(STextBlock).Visibility_Lambda(Visible).Text_Lambda([this] { return RenderQualityStatus(); })
        .Font(Font("Regular", 10)).AutoWrapText(true)
        .ColorAndOpacity_Lambda([this] { return FSlateColor(bIncreaseContrast ? Ink : Quiet); })];
    return Choices;
}

TSharedRef<SWidget> ABreziPlayerController::BuildControlsMenu()
{
    // Mac's AX wrapper checks each widget's own visibility, not its ancestors.
    // Bind every accessible panel element so closed-panel controls never leak into AX.
    const auto PanelVisibility = [this] { return bControlsOpen ? EVisibility::Visible : EVisibility::Collapsed; };
    TSharedPtr<SCheckBox> MotionToggle;
    TSharedPtr<SButton> SystemButton;
    TSharedPtr<SButton> CloseButton;
    TSharedRef<SWidget> Panel = SNew(SBox).WidthOverride(340)
    .Visibility_Lambda(PanelVisibility)
    .MaxDesiredHeight_Lambda([this]
    {
        const float Height = Interface.IsValid() ? Interface->GetCachedGeometry().GetLocalSize().Y : 0.0f;
        return FOptionalSize(Height > 0.0f ? FMath::Max(180.0f, Height - 140.0f) : 500.0f);
    })
    [
        SNew(SBorder).BorderImage_Lambda([this] { return bIncreaseContrast ? &ContrastPanelBrush : &PanelBrush; })
        .BorderBackgroundColor(FLinearColor(0.022f, 0.033f, 0.033f, 1)).Padding(18)
        [
            SAssignNew(ControlsScrollBox, SScrollBox)
            // Focusable Slate children consume Tab before the interface's bubbling key handler.
            // Follow actual descendant focus as well as our explicit F1/Escape focus changes.
            .ScrollWhenFocusChanges(EScrollWhenFocusChanges::InstantScroll)
            .NavigationDestination(EDescendantScrollDestination::IntoView)
            .NavigationScrollPadding(8.0f)
            + SScrollBox::Slot()
            [SNew(SVerticalBox)
            + SVerticalBox::Slot().AutoHeight().Padding(8, 4, 8, 12)
            [SNew(SHorizontalBox)
                + SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)
                [SNew(STextBlock).Visibility_Lambda(PanelVisibility).Text(LOCTEXT("ControlsTitle", "OVLÁDANIE")).Font(Font("Bold", 11, 100)).ColorAndOpacity(Ink)]
                + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
                [SAssignNew(CloseButton, SButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(8, 10)).Visibility_Lambda(PanelVisibility)
                    .AccessibleParams(AccessibleControl(LOCTEXT("CloseControlsLabel", "Zavrieť ovládanie")))
                    .ToolTipText(LOCTEXT("CloseControlsHint", "Zavrieť panel a vrátiť fokus na Ovládanie · Escape"))
                    .OnClicked_Lambda([this] { if (bControlsOpen) ToggleControls(); return FReply::Handled(); })
                    [SNew(STextBlock).Text(LOCTEXT("CloseControls", "Zavrieť")).Font(Font("Regular", 12)).ColorAndOpacity(Ink)]]]
            + SVerticalBox::Slot().AutoHeight()
            [BuildRenderQualityChoices()]
            + SVerticalBox::Slot().AutoHeight().Padding(8, 0, 8, 14)
            [SNew(STextBlock).Visibility_Lambda(PanelVisibility).Text(LOCTEXT("ControlsDetail", "Tab / Shift+Tab    Výber ovládača\nEnter / Medzerník    Potvrdenie\nF1    Ovládanie    Esc    Zavrieť / kurzor\n1–4    Architektonické pohľady\nHorný rad / numerická klávesnica\nM    Orbit / chôdza    N    Deň / noc\n\nF2    Navigácia bez držania myši\nPravé tlačidlo + myš    Otáčanie\nŠípky    Rozhliadanie\nKoliesko / Fn + ↑ ↓    Zoom v orbite\nPage Up / Down alebo num. + −\n\nChôdza počas navigácie:\nWASD    Pohyb po podlahe\nQ    Pomalšie    Shift    Rýchlejšie\nZatvorené dvere zostávajú zatvorené."))
                .Font(Font("Regular", 12)).ColorAndOpacity(Ink).LineHeightPercentage(1.45f)]
            + SVerticalBox::Slot().AutoHeight()
            [SAssignNew(MotionToggle, SCheckBox).Style(&QuietToggleStyle()).Padding(FMargin(8, 12)).Visibility_Lambda(PanelVisibility)
                .AccessibleParams(AccessibleControl(LOCTEXT("MotionLabel", "Obmedziť pohyb kamery")))
                .IsChecked_Lambda([this] { return bReducedMotion ? ECheckBoxState::Checked : ECheckBoxState::Unchecked; })
                .ToolTipText(LOCTEXT("MotionHint", "Zmeniť pohyb kamery pre túto reláciu"))
                .OnCheckStateChanged_Lambda([this](ECheckBoxState State) { if ((State == ECheckBoxState::Checked) != bReducedMotion) ToggleReducedMotion(); })
                [SNew(STextBlock).Text_Lambda([this] { return bReducedMotion ? LOCTEXT("ReducedOn", "Obmedziť pohyb  ·  Zapnuté") : LOCTEXT("ReducedOff", "Obmedziť pohyb  ·  Vypnuté"); })
                    .Font(Font("Regular", 12)).ColorAndOpacity(Ink)]]
            + SVerticalBox::Slot().AutoHeight()
            [SAssignNew(SystemButton, SButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(8, 10)).Visibility_Lambda(PanelVisibility)
                .AccessibleParams(AccessibleControl(TAttribute<FText>::CreateLambda([this]
                { return bUseSystemMotion ? LOCTEXT("SystemActiveLabel", "Nastavenie pohybu podľa macOS, aktívne") : LOCTEXT("SystemResume", "Použiť nastavenie macOS"); })))
                .ToolTipText(LOCTEXT("SystemMotionHint", "Znovu sledovať nastavenie Obmedziť pohyb v macOS"))
                .OnClicked_Lambda([this] { UseSystemMotionPreference(); return FReply::Handled(); })
                [SNew(STextBlock).Text_Lambda([this] { return bUseSystemMotion ? LOCTEXT("SystemFollowed", "Podľa macOS  ·  Aktívne") : LOCTEXT("SystemResume", "Použiť nastavenie macOS"); })
                    .Font(Font("Regular", 11)).ColorAndOpacity_Lambda([this] { return FSlateColor(bIncreaseContrast ? Ink : Quiet); })]]]
        ]
    ];
    ControlsAXContainer = Panel;
    ControlsAXContainer->SetCanChildrenBeAccessible(bControlsOpen);
    // F1 focuses the first control. Keep it at the top so opening help shows
    // its title and initial instructions instead of jumping to a lower setting.
    PanelControls = { CloseButton };
    PanelControls.Append(RenderQualityControls);
    PanelControls.Add(MotionToggle);
    PanelControls.Add(SystemButton);
    return Panel;
}

void ABreziPlayerController::BuildInterface()
{
    if (!GEngine || !GEngine->GameViewport || Interface.IsValid()) return;
    auto Glass = [this](TSharedRef<SWidget> Content, FMargin Padding)
    {
        // Blur is bounded to these three small panels, with a fixed five-tap kernel.
        return SNew(SBackgroundBlur).Padding(0).BlurRadius(TOptional<int32>(5))
            .BlurStrength_Lambda([this] { return bReduceTransparency || bIncreaseContrast ? 0.0f : 2.4f; })
            .CornerRadius(FVector4(16, 16, 16, 16)).LowQualityFallbackBrush(&SolidPanelBrush)
            [SNew(SBorder).Padding(Padding)
                .BorderImage_Lambda([this] { return bIncreaseContrast ? &ContrastPanelBrush : &PanelBrush; })
                .BorderBackgroundColor_Lambda([this] { return FLinearColor(0.022f, 0.033f, 0.033f, bReduceTransparency || bIncreaseContrast ? 1.0f : 0.76f); })
                [Content]];
    };
    TSharedPtr<SCheckBox> NightToggle;
    TSharedPtr<SCheckBox> WalkToggle;
    SAssignNew(ViewButtons, SWrapBox)
        .UseAllottedSize(false)
        .PreferredSize_Lambda([this] { return FMath::Max(1.0f, GetViewDockWidth() - 10.0f); })
        .HAlign(HAlign_Center)
        .InnerSlotPadding(FVector2D(2, 0));
    UpdateViewButtons();

    Interface = SNew(SBreziInterface)
    .OnPreviewTab_Lambda([this](const FGeometry&, const FKeyEvent& Event)
    { return HandleInterfaceKey(Event); })
    .OnUnhandledKey_Lambda([this](const FGeometry&, const FKeyEvent& Event) { return HandleInterfaceKey(Event); })
    [SNew(SOverlay)
    + SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Top).Padding(28)
    [
        SNew(SHorizontalBox)
        + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top)
        [Glass(SNew(SVerticalBox)
            + SVerticalBox::Slot().AutoHeight()
            [SNew(STextBlock).Text(LOCTEXT("Project", "BŘEZÍ 6012/26")).Font(Font("Bold", 19, 60)).ColorAndOpacity(Ink)]
            + SVerticalBox::Slot().AutoHeight().Padding(0, 6, 0, 0)
            [SNew(STextBlock).Text(LOCTEXT("Subtitle", "Architektonická štúdia")).Font(Font("Regular", 10, 70))
                .ColorAndOpacity_Lambda([this] { return FSlateColor(bIncreaseContrast ? Ink : Quiet); })], FMargin(22, 17))]
        + SHorizontalBox::Slot().FillWidth(1)[SNew(SSpacer)]
        + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top)
        [Glass(SNew(SHorizontalBox)
            + SHorizontalBox::Slot().AutoWidth()
            [SAssignNew(NightToggle, SCheckBox).Style(&QuietToggleStyle()).Padding(FMargin(17, 13))
                .AccessibleParams(AccessibleControl(LOCTEXT("NightModeLabel", "Nočný režim")))
                .IsEnabled_Lambda([this] { return Sun.IsValid(); })
                .IsChecked_Lambda([this] { return bNight ? ECheckBoxState::Checked : ECheckBoxState::Unchecked; })
                .OnCheckStateChanged_Lambda([this](ECheckBoxState State) { if ((State == ECheckBoxState::Checked) != bNight) ToggleTimeOfDay(); })
                .ToolTipText(LOCTEXT("DayHint", "Prepnúť svetlo · N"))
                [SNew(STextBlock).Text_Lambda([this] { return bNight ? LOCTEXT("Night", "Noc") : LOCTEXT("Day", "Deň"); })
                    .ColorAndOpacity(Ink).Font(Font("Regular", 12, 10))]]
            + SHorizontalBox::Slot().AutoWidth()
            [SAssignNew(WalkToggle, SCheckBox).Style(&QuietToggleStyle()).Padding(FMargin(17, 13))
                .AccessibleParams(AccessibleControl(LOCTEXT("WalkingModeLabel", "Chôdza po podlahe, pri vypnutí orbit")))
                .IsEnabled_Lambda([this] { return TwinPawn() != nullptr; })
                .IsChecked_Lambda([this] { return TwinPawn() && TwinPawn()->IsWalkingMode() ? ECheckBoxState::Checked : ECheckBoxState::Unchecked; })
                .OnCheckStateChanged_Lambda([this](ECheckBoxState State) { if (TwinPawn() && ((State == ECheckBoxState::Checked) != TwinPawn()->IsWalkingMode())) ToggleCameraMode(); })
                .ToolTipText(LOCTEXT("ModeHint", "Orbit / chôdza · M. Chôdza vyžaduje voľnú podlahu pod pohľadom."))
                [SNew(STextBlock).Text_Lambda([this] { return TwinPawn() && TwinPawn()->IsWalkingMode() ? LOCTEXT("Walk", "Chôdza") : LOCTEXT("Orbit", "Orbit"); })
                    .ColorAndOpacity(Ink).Font(Font("Regular", 12, 10))]]
            + SHorizontalBox::Slot().AutoWidth()
            [SAssignNew(ControlsButton, SButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(17, 13))
                .AccessibleParams(AccessibleControl(TAttribute<FText>::CreateLambda([this]
                { return bControlsOpen ? LOCTEXT("ControlsOpenLabel", "Ovládanie, panel otvorený") : LOCTEXT("Controls", "Ovládanie"); })))
                .ToolTipText(LOCTEXT("ControlsHint", "Ovládanie a prístupnosť · F1"))
                .OnClicked_Lambda([this] { ToggleControls(); return FReply::Handled(); })
                [SNew(STextBlock).Text(LOCTEXT("Controls", "Ovládanie")).Font(Font("Regular", 12, 10)).ColorAndOpacity(Ink)]], FMargin(5))]
    ]
    + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(28)
    [
        SNew(SBox).WidthOverride_Lambda([this] { return FOptionalSize(GetViewDockWidth()); })
        [Glass(SNew(SVerticalBox)
            + SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Fill)[ViewButtons.ToSharedRef()]
            + SVerticalBox::Slot().AutoHeight()
            [SAssignNew(FeedbackAXContainer, SBox).Padding(FMargin(8, 4, 8, 8))
                .Visibility_Lambda([this] { return TwinPawn() && !TwinPawn()->GetNavigationMessage().IsEmpty() ? EVisibility::SelfHitTestInvisible : EVisibility::Collapsed; })
            [SAssignNew(NavigationFeedback, SButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(12, 10))
                .Visibility_Lambda([this] { return TwinPawn() && !TwinPawn()->GetNavigationMessage().IsEmpty() ? EVisibility::Visible : EVisibility::Collapsed; })
                .AccessibleParams(AccessibleControl(TAttribute<FText>::CreateLambda([this]
                { return FText::Format(LOCTEXT("WalkingFeedbackAX", "{0} Potvrdiť hlásenie."), TwinPawn() ? TwinPawn()->GetNavigationMessage() : FText::GetEmpty()); })))
                .OnClicked_Lambda([this] { if (TwinPawn()) TwinPawn()->DismissNavigationMessage(); FocusControl(WalkingModeControl); return FReply::Handled(); })
                [SNew(STextBlock).Text_Lambda([this] { return TwinPawn() ? TwinPawn()->GetNavigationMessage() : FText::GetEmpty(); })
                    .AutoWrapText(true).Justification(ETextJustify::Center).Font(Font("Regular", 12)).ColorAndOpacity(Ink)]]]
            + SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(12, 0, 12, 5)
            [SAssignNew(NavigationButton, SButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(16, 7))
                .IsEnabled_Lambda([this] { return !bControlsOpen && TwinPawn() && TwinPawn()->HasViewpoints(); })
                .AccessibleParams(AccessibleControl(TAttribute<FText>::CreateLambda([this]
                {
                    if (TwinPawn() && TwinPawn()->IsNavigating()) return LOCTEXT("StopNavigationAX", "Ukončiť navigáciu a zobraziť kurzor. Escape alebo F2.");
                    return TwinPawn() && TwinPawn()->IsWalkingMode()
                        ? LOCTEXT("StartWalkingAX", "Začať chôdzu. WASD pohyb, myš alebo šípky rozhliadanie, Escape späť.")
                        : LOCTEXT("StartOrbitAX", "Preskúmať pohľad. Myš alebo šípky otáčanie, koliesko, plus a mínus alebo Page Up a Page Down priblíženie. Na Macu Fn so šípkou hore alebo dole, Escape späť.");
                })))
                .ToolTipText_Lambda([this]
                {
                    return TwinPawn() && TwinPawn()->IsWalkingMode()
                        ? LOCTEXT("StartWalkingHint", "Bez držania tlačidla myši · WASD pohyb, myš alebo šípky rozhliadanie · Esc späť")
                        : LOCTEXT("StartOrbitHint", "Bez držania tlačidla myši · myš alebo šípky otáčanie, koliesko, + / − alebo Fn + ↑ / ↓ priblíženie · Esc späť");
                })
                .OnClicked_Lambda([this]
                {
                    // AX activation need not focus the button first. Record a stable
                    // return target for both pointer/keyboard and accessible actions.
                    FocusControl(NavigationButton);
                    ToggleNavigation();
                    return FReply::Handled();
                })
                [SNew(STextBlock).Text_Lambda([this]
                {
                    if (!TwinPawn() || !TwinPawn()->HasViewpoints()) return LOCTEXT("MissingViewData", "Pohľady sa načítavajú");
                    if (TwinPawn()->IsNavigating()) return LOCTEXT("StopNavigation", "Späť k ovládaniu · Esc");
                    return TwinPawn()->IsWalkingMode() ? LOCTEXT("StartWalking", "Začať chôdzu · F2") : LOCTEXT("StartOrbit", "Preskúmať pohľad · F2");
                }).Font(Font("Regular", 12, 10)).ColorAndOpacity_Lambda([this] { return FSlateColor(bIncreaseContrast ? Ink : Accent); })]], FMargin(5))]
    ]
    + SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Top).Padding(28, 108, 28, 28)
    [BuildControlsMenu()]];
    WalkingModeControl = WalkToggle;
    ToolbarControls = { NightToggle, WalkToggle, ControlsButton };
    UpdateAccessibleSubtrees();
    GEngine->GameViewport->AddViewportWidgetContent(Interface.ToSharedRef(), 10);
}

#undef LOCTEXT_NAMESPACE
