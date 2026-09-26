#include "BreziPlayerController.h"
#include "BreziGameUI.h"
#include "BreziPawn.h"
#include "BreziPresetKeyPolicy.h"
#include "BreziLightingTransitionMath.h"
#include "BreziRuntimeDiagnostics.h"
#include "BreziWalkingTraversal.h"
#include "BreziMotionQA.h"
#include "BreziFlameStudy.h"
#include "BreziExteriorLighting.h"
#include "BreziGameViewportClient.h"
#include "BreziDoors.h"
#include "BreziDoubleGlassActor.h"
#include "BreziTouchpadPolicy.h"
#include "GenericPlatform/GenericPlatformInputDeviceMapper.h"
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
#include "Engine/UserInterfaceSettings.h"
#include "UnrealClient.h"
#include "Engine/SkyLight.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/IConsoleManager.h"
#include "GameFramework/PlayerInput.h"
#include "Materials/MaterialInterface.h"
#include "Misc/CommandLine.h"
#include "Misc/CoreDelegates.h"
#include "Misc/Parse.h"
#include "Styling/CoreStyle.h"
#include "SceneInterface.h"
#include "TimerManager.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SMenuAnchor.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Accessibility/SlateWidgetAccessibleTypes.h"
#include "Widgets/Layout/SBackgroundBlur.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SDPIScaler.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/Layout/SWrapBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SWindow.h"
#include "Widgets/Text/STextBlock.h"
#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#if WITH_ACCESSIBILITY
#include "Widgets/Accessibility/SlateAccessibleWidgets.h"
#endif
#endif

#define LOCTEXT_NAMESPACE "BreziTwin"

namespace
{
    bool ShouldStartWalkingTour(bool& bPauseAfterStartup)
    {
        const TCHAR* CLI = FCommandLine::Get();
        FString Value;
        bool bOwnsCameraScenario = false;
        for (const TCHAR* Flag : {TEXT("BreziProfileGPU"), TEXT("BreziMotionQA"), TEXT("BreziCausticsMotionQA"),
            TEXT("BreziWalk"), TEXT("BreziWalkAudit"), TEXT("BreziSolarVisibilityProbe"), TEXT("BreziCausticsProbe"),
            TEXT("BreziAXInitStress"), TEXT("BreziRealtimeOrbit")})
            bOwnsCameraScenario |= FParse::Param(CLI, Flag);
        for (const TCHAR* Key : {TEXT("BreziWalkTraversal="), TEXT("BreziWalkthrough="),
            TEXT("BreziFlameStudyScale="), TEXT("BreziFlameShape=")})
            bOwnsCameraScenario |= FParse::Value(CLI, Key, Value);
        if (FParse::Value(CLI, TEXT("BreziGameplayUI="), Value))
        {
            const auto Requested = Value == TEXT("play") ? BreziNavigation::GameplayUICapture::Play
                : Value == TEXT("pause") ? BreziNavigation::GameplayUICapture::Pause : BreziNavigation::GameplayUICapture::Invalid;
            const bool bAllowed = BreziNavigation::AllowGameplayUICapture(FParse::Param(CLI, TEXT("BreziCaptureUI")),
                Requested, bOwnsCameraScenario || FParse::Param(CLI, TEXT("BreziCapture4K")) || FParse::Param(CLI, TEXT("BreziCaptureScene")));
            if (!bAllowed)
            {
                UE_LOG(LogTemp, Error, TEXT("BreziGameplayUI rejected: use play or pause with BreziCaptureUI and without traversal or other camera studies."));
                return false;
            }
            bPauseAfterStartup = Requested == BreziNavigation::GameplayUICapture::Pause;
            return true;
        }
        const bool bDiagnostic = bOwnsCameraScenario || FParse::Param(CLI, TEXT("BreziCapture4K"))
            || FParse::Param(CLI, TEXT("BreziCaptureScene")) || FParse::Param(CLI, TEXT("BreziCaptureUI"))
            || FParse::Param(CLI, TEXT("BreziExitAfterCapture")) || FParse::Value(CLI, TEXT("BreziBenchmarkFrames="), Value);
        return BreziNavigation::StartTourOnLaunch(FParse::Value(CLI, TEXT("BreziView="), Value), bDiagnostic,
            FParse::Param(CLI, TEXT("BreziGameplay")));
    }

    void ApplyDeckNaniteFallback(UWorld* World)
    {
        check(IsInGameThread());
        if (!World || !World->IsGameWorld()) return;

        // DOM ordinals belong to one geometry export. The source-material
        // refresh reuses them for different objects, so never apply the old
        // deck correction to that profile, even if its mesh path still matches.
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if (!It->ActorHasTag(TEXT("BreziGenerated"))) continue;
            TArray<UStaticMeshComponent*> SourceComponents;
            It->GetComponents(SourceComponents);
            for (const UStaticMeshComponent* SourceComponent : SourceComponents)
            {
                const UStaticMesh* SourceMesh = SourceComponent->GetStaticMesh();
                if (!SourceMesh) continue;
                for (const FStaticMaterial& Slot : SourceMesh->GetStaticMaterials())
                {
                    const UMaterialInterface* Material = Slot.MaterialInterface;
                    if (Material && Material->GetPathName().StartsWith(
                        TEXT("/Game/Brezi/ModelRefresh/Materials/"), ESearchCase::CaseSensitive))
                    {
                        UE_LOG(LogTemp, Display, TEXT("BreziDeckNaniteFallback skipped reason=source-material-profile material=%s"), *Material->GetPathName());
                        return;
                    }
                }
            }
        }

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

    const FLinearColor Ink = BreziUI::Ink;
    const FLinearColor Quiet = BreziUI::Quiet;
    const FLinearColor Accent = BreziUI::Accent;
    const FButtonStyle& QuietButtonStyle() { return BreziUI::ButtonStyle(); }
    const FCheckBoxStyle& QuietToggleStyle() { return BreziUI::ToggleStyle(); }

    FString RoomName(const FString& Id, const FString& Fallback)
    {
        static const TMap<FString, FString> Names = {
            {TEXT("interior"), TEXT("Kuchyňa")}, {TEXT("terrace"), TEXT("Záhradná terasa")},
            {TEXT("pool"), TEXT("Bazén")}, {TEXT("street"), TEXT("Pred domom")},
            {TEXT("room-1-01"), TEXT("Zádverie")}, {TEXT("room-1-02"), TEXT("Spoločná chodba")},
            {TEXT("room-1-03"), TEXT("Obývacia izba")}, {TEXT("room-1-04"), TEXT("Pracovňa")},
            {TEXT("room-1-05"), TEXT("Kúpeľňa a práčovňa")}, {TEXT("room-1-06"), TEXT("WC")},
            {TEXT("room-1-07"), TEXT("Technická miestnosť")}, {TEXT("room-1-08"), TEXT("Detská izba · ulica")},
            {TEXT("room-1-09"), TEXT("Detská izba · dvor")}, {TEXT("room-1-10"), TEXT("Spálňa")},
            {TEXT("room-1-11"), TEXT("Súkromná kúpeľňa")}, {TEXT("room-1-12"), TEXT("Garáž")},
            {TEXT("room-dressing"), TEXT("Šatník")}};
        const FString* Found = Names.Find(Id);
        return Found ? *Found : Fallback;
    }

    TSharedRef<SWidget> Hairline()
    {
        return SNew(SBox).HeightOverride(1)[SNew(SBorder).Padding(0)
            .BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor(BreziUI::Line)];
    }

    TSharedRef<SWidget> KeyHint(const TCHAR* Key, const TCHAR* Label)
    {
        return SNew(SHorizontalBox)
            + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[BreziUI::Keycap(FText::FromString(Key))]
            + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8, 0, 0, 0)
            [SNew(STextBlock).Text(FText::FromString(Label)).Font(BreziUI::Font("Regular", 11)).ColorAndOpacity(Ink)];
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

    TSharedRef<SButton> DestinationAction(FText Label, FText Accessible, FOnClicked Action)
    {
        // SComboButton deliberately hides its inner button from AX in UE 5.8.
        // Keep the real SButton as both the keyboard and accessible action.
        return SNew(BreziUI::SGameButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(14, 10))
            .AccessibleParams(AccessibleControl(Accessible)).OnClicked(Action)
            [SNew(STextBlock).Text(Label).Font(Font("Regular", 12)).ColorAndOpacity(Ink)];
    }

    void ClearStoredMouseLook(UPlayerInput* Input)
    {
        if (!Input) return;
        // FlushPressedKeys does not clear Value, RawValueAccumulator or mouse
        // smoothing. Clear only these axes; held movement/interaction keys survive.
        for (const FKey Key : {EKeys::MouseX, EKeys::MouseY, EKeys::Mouse2D})
        {
            if (FKeyState* State = Input->GetKeyState(Key))
            {
                State->RawValue = State->Value = State->RawValueAccumulator = FVector::ZeroVector;
                State->SampleCountAccumulator = 0;
                State->PairSampledAxes = 0;
            }
        }
        Input->ClearSmoothing();
    }
}

ABreziPawn* ABreziPlayerController::TwinPawn() const { return Cast<ABreziPawn>(GetPawn()); }
UBreziDoors* ABreziPlayerController::GetDoorSystem() const { return Doors; }

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
    if (IsLocalController())
    {
        Doors = NewObject<UBreziDoors>(this);
        Doors->Initialize(GetWorld());
        ApplicationDeactivatedHandle = FCoreDelegates::ApplicationWillDeactivateDelegate.AddUObject(this, &ABreziPlayerController::OnApplicationDeactivated);
        ApplicationBackgroundHandle = FCoreDelegates::ApplicationWillEnterBackgroundDelegate.AddUObject(this, &ABreziPlayerController::OnApplicationDeactivated);
        bool bStartPaused = false;
        const bool bStartTour = ShouldStartWalkingTour(bStartPaused);
        InitialTour.Begin(bStartTour, bStartPaused);
        bControlsOpen = InitialTour.IsPending();
    }
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
    EndWalkthroughAutomation();
    TraceLightingTransition(TEXT("end-play"), TEXT("before-restore"), false, TimeOfDayElapsed);
    bTimeOfDayTransitioning = false;
    RestoreLightingTransitionExposure();
    GetWorldTimerManager().ClearTimer(WindowTitleRetry);
    ExteriorLighting->Shutdown();
    if (Doors) Doors->Shutdown();
    FCoreDelegates::ApplicationWillDeactivateDelegate.Remove(ApplicationDeactivatedHandle);
    FCoreDelegates::ApplicationWillEnterBackgroundDelegate.Remove(ApplicationBackgroundHandle);
    BreziNativeAccessibility::StopObserving(AccessibilityObserver);
    AccessibilityObserver = nullptr;
    if (InterfaceHost.IsValid() && GEngine && GEngine->GameViewport) GEngine->GameViewport->RemoveViewportWidgetContent(InterfaceHost.ToSharedRef());
    InterfaceHost.Reset();
    Interface.Reset();
    ControlsAXContainer.Reset();
    FeedbackAXContainer.Reset();
    GameplayAXContainer.Reset(); RoomsAXContainer.Reset(); AtmosphereAXContainer.Reset(); InputAXContainer.Reset();
    InteractionAXContainer.Reset(); MovementAXContainer.Reset(); InteractionButton.Reset();
    FlightMovementAXContainer.Reset();
    MenuSectionControls.Empty(); AtmosphereControls.Empty(); InputControls.Empty();
    ViewButtons.Reset();
    ControlsButton.Reset();
    NavigationButton.Reset();
    WalkingModeControl.Reset();
    NavigationFeedback.Reset();
    ControlsScrollBox.Reset();
    if (DestinationAnchor.IsValid()) DestinationAnchor->SetIsOpen(false);
    DestinationAnchor.Reset();
    DestinationButton.Reset();
    DestinationScrollBox.Reset();
    DestinationControls.Empty();
    ToolbarControls.Empty();
    ViewControls.Empty();
    PanelControls.Empty();
    RenderQualityControls.Empty();
    RenderQualityView.Reset();
    RenderQualityRoomLights.Empty();
    RenderQualityRoomLightShadows.Empty();
    FocusBeforeNavigation.Reset();
    Super::EndPlay(Reason);
}

void ABreziPlayerController::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bWalkthroughAutomation && TwinPawn() && TwinPawn()->IsNavigating() && !HasForegroundWindow()) PauseGameplay(false);
    TArray<FKey> DueReleases;
    for (const auto& Entry : HudReleaseTimes)
        if (FPlatformTime::Seconds() >= Entry.Value) DueReleases.Add(Entry.Key);
    for (const FKey& Key : DueReleases)
    {
        SendHudKey(Key, false);
        HudReleaseTimes.Remove(Key);
        HudPressTimes.Remove(Key);
        HudMovementKeys.Remove(Key);
    }
    if (bHudCursor && IsGameplayActive() && TwinPawn())
    {
        // Slate moves keyboard focus after SButton::OnPressed and the scene
        // viewport flushes PlayerInput on focus loss. Reassert only our held
        // screen keys after that transition; releases still have one owner.
        for (const FKey& Key : {EKeys::W, EKeys::S, EKeys::E, EKeys::Q})
            if (HudMovementKeys.Contains(Key) && !IsInputKeyDown(Key)) SendHudKey(Key, true);
        const float Direction = float(HudMovementKeys.Contains(EKeys::Right)) - float(HudMovementKeys.Contains(EKeys::Left));
        if (Direction != 0) TwinPawn()->TurnFromScreen(Direction * FMath::Min(DeltaSeconds, 0.05f) * 80.0f);
    }
    TryCompleteInitialTour();
    if (Doors && IsNavigationInputActive() && TwinPawn()->IsWalkingMode()) Doors->Tick(DeltaSeconds, this);
    UpdateTimeOfDayTransition(DeltaSeconds);
    RefreshRenderQualityScenePolicy();
    UpdateAccessibleSubtrees();
}

void ABreziPlayerController::TryCompleteInitialTour()
{
    if (!InitialTour.IsPending()) return;
    const UBreziGameViewportClient* Presentation = GEngine ? Cast<UBreziGameViewportClient>(GEngine->GameViewport) : nullptr;
    // The Mac inner viewport registers and fits the window after initial ticks.
    // Capturing earlier can bind the pointer before its final input host exists.
    const bool bPresentationReady = !Presentation || GIsEditor || Presentation->IsPresentationReadyForCurrentOutput();
    const bool bReady = TwinPawn() && TwinPawn()->HasViewpoints() && bPresentationReady
        && GEngine && GEngine->GameViewport && GEngine->GameViewport->GetWindow().IsValid();
    const BreziNavigation::TourStartupAction Action = InitialTour.CompleteIfReady(bReady, HasForegroundWindow());
    if (Action == BreziNavigation::TourStartupAction::Wait) return;
    const bool bEntered = TwinPawn()->StartWalkingTour();
    if (bEntered && Action == BreziNavigation::TourStartupAction::EnterAndResume) ResumeGameplay();
    else PauseGameplay(HasForegroundWindow());
}

void ABreziPlayerController::UpdateAccessibleSubtrees()
{
    // Visibility alone does not filter UE's Mac accessibleChildren list. These stable,
    // nonaccessible container widgets exclude whole inactive subtrees without rebuilding UI.
    const bool bShowFeedback = bControlsOpen && TwinPawn() && !TwinPawn()->GetNavigationMessage().IsEmpty();
    if (!bShowFeedback && bControlsOpen && HasForegroundWindow() && NavigationFeedback.IsValid() && FSlateApplication::IsInitialized()
        && FSlateApplication::Get().GetKeyboardFocusedWidget() == NavigationFeedback)
        FocusControl(WalkingModeControl);
    if (ControlsAXContainer.IsValid()) ControlsAXContainer->SetCanChildrenBeAccessible(bControlsOpen);
    if (FeedbackAXContainer.IsValid()) FeedbackAXContainer->SetCanChildrenBeAccessible(bShowFeedback);
    if (GameplayAXContainer.IsValid()) GameplayAXContainer->SetCanChildrenBeAccessible(!bControlsOpen);
    if (InteractionAXContainer.IsValid()) InteractionAXContainer->SetCanChildrenBeAccessible(!InteractionPrompt().IsEmpty());
    if (MovementAXContainer.IsValid()) MovementAXContainer->SetCanChildrenBeAccessible(!bControlsOpen && bHudCursor && TwinPawn() && (TwinPawn()->IsWalkingMode() || TwinPawn()->IsFlightMode()));
    if (FlightMovementAXContainer.IsValid()) FlightMovementAXContainer->SetCanChildrenBeAccessible(!bControlsOpen && bHudCursor && TwinPawn() && TwinPawn()->IsFlightMode());
    if (RoomsAXContainer.IsValid()) RoomsAXContainer->SetCanChildrenBeAccessible(bControlsOpen && MenuSection == 0);
    if (AtmosphereAXContainer.IsValid()) AtmosphereAXContainer->SetCanChildrenBeAccessible(bControlsOpen && MenuSection == 1);
    if (InputAXContainer.IsValid()) InputAXContainer->SetCanChildrenBeAccessible(bControlsOpen && MenuSection == 2);
}

void ABreziPlayerController::OnPossess(APawn* InPawn)
{
    if (bTimeOfDayTransitioning) FinishTimeOfDayTransition(true);
    Super::OnPossess(InPawn);
    if (HasActorBegunPlay() && InPawn && InPawn->HasActorBegunPlay()) RefreshInterface();
}

void ABreziPlayerController::RefreshInterface()
{
    if (ABreziPawn* Pawn = TwinPawn()) { Pawn->SetReducedMotion(bReducedMotion); Pawn->SetLookSensitivity(MouseSensitivity); }
    if (IsLocalController() && HasActorBegunPlay())
    {
        if (Interface.IsValid()) UpdateViewButtons();
        else BuildInterface();
    }
}

void ABreziPlayerController::SetupInputComponent()
{
    Super::SetupInputComponent();
    InputComponent->BindKey(EKeys::RightMouseButton, IE_Pressed, this, &ABreziPlayerController::BeginPointerNavigation);
    InputComponent->BindKey(EKeys::RightMouseButton, IE_Released, this, &ABreziPlayerController::EndPointerNavigation);
    InputComponent->BindKey(EKeys::Escape, IE_Pressed, this, &ABreziPlayerController::HandleEscape);
    InputComponent->BindKey(EKeys::Tab, IE_Pressed, this, &ABreziPlayerController::ToggleHudCursor);
    InputComponent->BindKey(EKeys::F1, IE_Pressed, this, &ABreziPlayerController::ToggleControls);
    InputComponent->BindKey(EKeys::F2, IE_Pressed, this, &ABreziPlayerController::ToggleNavigation);
    // E also drives the pawn's flight-height axis. Interaction is walking-only;
    // let that key reach the pawn input component in both modes.
    InputComponent->BindKey(EKeys::E, IE_Pressed, this, &ABreziPlayerController::Interact).bConsumeInput = false;
    InputComponent->BindKey(EKeys::V, IE_Pressed, this, &ABreziPlayerController::TogglePersonCamera);
    InputComponent->BindKey(EKeys::R, IE_Pressed, this, &ABreziPlayerController::RecenterPersonCamera);
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
    InputComponent->BindKey(EKeys::H, IE_Pressed, this, &ABreziPlayerController::ToggleFreeFlightShortcut);
}

void ABreziPlayerController::BeginNavigation()
{
    StartNavigation(BreziNavigation::CaptureSource::Latched);
}

void ABreziPlayerController::BeginPointerNavigation()
{
    if (TwinPawn() && !TwinPawn()->IsWalkingMode()) StartNavigation(BreziNavigation::CaptureSource::PointerHold);
}

void ABreziPlayerController::EndPointerNavigation()
{
    if (NavigationCapture.ReleasePointer()) PauseGameplay();
}

void ABreziPlayerController::StartNavigation(BreziNavigation::CaptureSource Source)
{
    ABreziPawn* Pawn = TwinPawn();
    // Repeated pointer presses must not replace the control we return to on Escape.
    if (bControlsOpen || !Pawn || !Pawn->HasViewpoints() || Pawn->IsNavigating()) return;
    if (bWalkthroughAutomation)
    {
        if (!NavigationCapture.BeginAutomation(Source, true)) return;
        Pawn->SetNavigating(true);
        if (PlayerInput) PlayerInput->FlushPressedKeys();
        return; // Synthetic engine input never changes native cursor, capture or focus.
    }
    if (!NavigationCapture.Begin(Source, true, HasForegroundWindow())) return;
    if (FSlateApplication::IsInitialized()) FocusBeforeNavigation = FSlateApplication::Get().GetKeyboardFocusedWidget();
    Pawn->SetNavigating(true);
    Pawn->SetMouseLookEnabled(true);
    bHudCursor = false;
    if (PlayerInput) PlayerInput->FlushPressedKeys();
    bShowMouseCursor = false;
    FInputModeGameOnly Mode;
    Mode.SetConsumeCaptureMouseDown(false);
    SetInputMode(Mode);
    if (GEngine && GEngine->GameViewport)
    {
        GEngine->GameViewport->SetMouseCaptureMode(EMouseCaptureMode::CapturePermanently_IncludingInitialMouseDown);
        GEngine->GameViewport->SetMouseLockMode(EMouseLockMode::LockAlways);
    }
    ClearMouseLookTransition();
}

void ABreziPlayerController::ToggleNavigation()
{
    if (TwinPawn() && TwinPawn()->IsNavigating()) PauseGameplay();
    else ResumeGameplay();
}

void ABreziPlayerController::EndNavigation()
{
    StopHudMovement();
    bHudCursor = false;
    NavigationCapture.Stop();
    if (ABreziPawn* Pawn = TwinPawn()) { Pawn->SetNavigating(false); Pawn->SetMouseLookEnabled(false); }
    if (PlayerInput) PlayerInput->FlushPressedKeys();
    if (bWalkthroughAutomation) return;
    bShowMouseCursor = true;
    FInputModeGameAndUI Mode;
    Mode.SetHideCursorDuringCapture(false);
    Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    SetInputMode(Mode);
    if (GEngine && GEngine->GameViewport)
    {
        GEngine->GameViewport->SetMouseCaptureMode(EMouseCaptureMode::NoCapture);
        GEngine->GameViewport->SetMouseLockMode(EMouseLockMode::DoNotLock);
    }
    ClearMouseLookTransition();
    FocusBeforeNavigation.Reset();
}

void ABreziPlayerController::ClearMouseLookTransition()
{
    ClearStoredMouseLook(PlayerInput);
    bDiscardMouseLookOnNextInput = true;
}

void ABreziPlayerController::PreProcessInput(float DeltaTime, bool bGamePaused)
{
    Super::PreProcessInput(DeltaTime, bGamePaused);
    if (bDiscardMouseLookOnNextInput) ClearStoredMouseLook(PlayerInput);
}

void ABreziPlayerController::PostProcessInput(float DeltaTime, bool bGamePaused)
{
    Super::PostProcessInput(DeltaTime, bGamePaused);
    if (!bDiscardMouseLookOnNextInput) return;
    // A capture-mode bind can run inside this very input pass, after axis
    // delegates were gathered. Drop that pass's queued look as well as any
    // cursor-warp samples. WASD is processed normally, with no timer or focus change.
    bDiscardMouseLookOnNextInput = false;
    ClearStoredMouseLook(PlayerInput);
    if (ABreziPawn* Pawn = TwinPawn())
        Pawn->SetMouseLookEnabled(!bControlsOpen && !bHudCursor && Pawn->IsNavigating());
}

bool ABreziPlayerController::HasForegroundWindow() const
{
    if (!IsLocalController() || !FSlateApplication::IsInitialized() || !FSlateApplication::Get().IsActive()
        || !GEngine || !GEngine->GameViewport) return false;
    const TSharedPtr<SWindow> Window = GEngine->GameViewport->GetWindow();
    return Window.IsValid() && Window->IsActive();
}

bool ABreziPlayerController::IsGameplayActive() const
{
    return !bWalkthroughAutomation && IsNavigationInputActive();
}

bool ABreziPlayerController::IsNavigationInputActive() const
{
    return BreziNavigation::NavigationInputActive(TwinPawn() && TwinPawn()->IsNavigating(), bControlsOpen,
        bWalkthroughAutomation ? false : HasForegroundWindow(), bWalkthroughAutomation);
}

bool ABreziPlayerController::BeginWalkthroughAutomation()
{
    FString Fixture;
    if (bWalkthroughAutomation || !IsLocalController() || !GetWorld() || !GetWorld()->IsGameWorld()
        || !TwinPawn() || !PlayerInput || TwinPawn()->IsNavigating()
        || NavigationCapture.GetSource() != BreziNavigation::CaptureSource::None
        || !FParse::Value(FCommandLine::Get(), TEXT("BreziWalkthrough="), Fixture) || Fixture.IsEmpty()) return false;
    bWalkthroughAutomation = true;
    InitialTour.Cancel();
    bControlsOpen = false;
    TwinPawn()->SetNavigating(false);
    PlayerInput->FlushPressedKeys();
    UE_LOG(LogTemp, Display, TEXT("BreziWalkthroughAutomation started engineInputOnly=1 nativeMouseCapture=0 nativeKeyboardFocusVerified=0"));
    return true;
}

void ABreziPlayerController::EndWalkthroughAutomation()
{
    if (!bWalkthroughAutomation) return;
    EndNavigation(); // Clear synthetic input while the no-focus branch is still active.
    bWalkthroughAutomation = false;
    bControlsOpen = true;
    InitialTour.Cancel();
    UE_LOG(LogTemp, Display, TEXT("BreziWalkthroughAutomation ended engineInputCleared=1 nativeMouseCapture=0"));
}

void ABreziPlayerController::PauseGameplay(bool bFocusMenu)
{
    if (DestinationAnchor.IsValid()) DestinationAnchor->SetIsOpen(false);
    InitialTour.Pause();
    EndNavigation();
    bControlsOpen = true;
    UpdateAccessibleSubtrees();
    if (!bWalkthroughAutomation && bFocusMenu && HasForegroundWindow()) FocusControl(NavigationButton);
}

void ABreziPlayerController::ResumeGameplay()
{
    if (!bWalkthroughAutomation && !HasForegroundWindow()) return;
    if (InitialTour.IsPending())
    {
        InitialTour.RequestResume(HasForegroundWindow());
        TryCompleteInitialTour();
        return;
    }
    if (bHudCursor) EndNavigation();
    bControlsOpen = false;
    BeginNavigation();
    if (!TwinPawn() || !TwinPawn()->IsNavigating()) bControlsOpen = true;
    UpdateAccessibleSubtrees();
}

void ABreziPlayerController::OnApplicationDeactivated()
{
    if (bWalkthroughAutomation) return;
    NavigationCapture.LoseForeground();
    PauseGameplay(false);
}

void ABreziPlayerController::Interact()
{
    if (Doors && IsNavigationInputActive() && TwinPawn()->IsWalkingMode()) Doors->Interact();
}

FText ABreziPlayerController::InteractionPrompt() const
{
    return Doors && IsGameplayActive() && TwinPawn()->IsWalkingMode() ? Doors->GetPrompt() : FText::GetEmpty();
}

void ABreziPlayerController::FocusControl(const TSharedPtr<SWidget>& Widget)
{
    if (bWalkthroughAutomation || !Widget.IsValid() || !FSlateApplication::IsInitialized()) return;
    FSlateApplication::Get().SetKeyboardFocus(Widget, EFocusCause::Navigation);
    if (bControlsOpen && ControlsScrollBox.IsValid() && (ViewControls.Contains(Widget) || AtmosphereControls.Contains(Widget) || InputControls.Contains(Widget)))
    {
        // Keep the slider's adjacent label and numeric value visible in short windows.
        const bool bSensitivity = InputControls.IsValidIndex(0) && InputControls[0] == Widget;
        ControlsScrollBox->ScrollDescendantIntoView(Widget, false,
            bSensitivity ? EDescendantScrollDestination::Center : EDescendantScrollDestination::IntoView, 8.0f);
    }
}

void ABreziPlayerController::FocusFirstControl()
{
    PauseGameplay();
}

void ABreziPlayerController::ToggleControls()
{
    if (bControlsOpen) ResumeGameplay();
    else PauseGameplay();
}

void ABreziPlayerController::HandleEscape()
{
    if (bControlsOpen) ResumeGameplay();
    else PauseGameplay();
}

FReply ABreziPlayerController::HandleInterfaceKey(const FKeyEvent& Event)
{
    // The popup shares our native window. Its parent preview must not steal
    // Tab for the underlying toolbar before the destination list sees it.
    if (DestinationAnchor.IsValid() && DestinationAnchor->IsOpen()) return HandleDestinationKey(Event);
    const FReply PresetReply = HandlePresetShortcut(Event);
    if (PresetReply.IsEventHandled()) return PresetReply;
    // Preserve VoiceOver's Control/Option chords and native macOS Command shortcuts.
    if (Event.IsControlDown() || Event.IsAltDown() || Event.IsCommandDown()) return FReply::Unhandled();
    const FKey Key = Event.GetKey();
    if (Key == EKeys::Tab)
    {
        if (!bControlsOpen && !bHudCursor) { ToggleHudCursor(); return FReply::Handled(); }
        TArray<TSharedPtr<SWidget>> Controls = bControlsOpen ? MenuSectionControls : ToolbarControls;
        if (bControlsOpen)
        {
            Controls.Append(MenuSection == 0 ? ViewControls : MenuSection == 1 ? AtmosphereControls : InputControls);
            Controls.Append(PanelControls);
            if (NavigationFeedback.IsValid() && TwinPawn() && !TwinPawn()->GetNavigationMessage().IsEmpty()) Controls.Add(NavigationFeedback);
        }
        Controls.RemoveAll([](const TSharedPtr<SWidget>& Widget) { return !Widget.IsValid() || !Widget->IsEnabled()
            || !Widget->GetVisibility().IsVisible() || !Widget->SupportsKeyboardFocus(); });
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
    if (Key == EKeys::H) { ToggleFreeFlight(); return FReply::Handled(); }
    if (Key == EKeys::V) { TogglePersonCamera(); return FReply::Handled(); }
    if (Key == EKeys::R) { RecenterPersonCamera(); return FReply::Handled(); }
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

void ABreziPlayerController::ZoomIn() { if (ABreziPawn* Pawn = TwinPawn(); Pawn && !bControlsOpen) Pawn->ZoomCamera(1.0f); }
void ABreziPlayerController::ZoomOut() { if (ABreziPawn* Pawn = TwinPawn(); Pawn && !bControlsOpen) Pawn->ZoomCamera(-1.0f); }

bool ABreziPlayerController::HandleCameraWheel(const FPointerEvent& Event)
{
    if (bControlsOpen || (!HasForegroundWindow() && !bWalkthroughAutomation) || !TwinPawn() || Event.IsCommandDown() || Event.IsAltDown()) return false;
    TwinPawn()->ZoomCamera(BreziTouchpad::WheelSteps(Event.GetWheelDelta()));
    return true;
}

bool ABreziPlayerController::HandleCameraGesture(const FPointerEvent& Event)
{
    if (bControlsOpen || (!HasForegroundWindow() && !bWalkthroughAutomation) || !TwinPawn() || Event.IsCommandDown() || Event.IsAltDown()) return false;
    double Steps = 0;
    if (Event.GetGestureType() == EGestureEvent::Magnify) Steps = BreziTouchpad::MagnifySteps(Event.GetGestureDelta().X);
    else if (Event.GetGestureType() == EGestureEvent::Scroll) Steps = BreziTouchpad::ScrollSteps(Event.GetGestureDelta().Y);
    else return false;
    TwinPawn()->ZoomCamera(Steps);
    return true;
}

void ABreziPlayerController::TogglePersonCamera()
{
    if (ABreziPawn* Pawn = TwinPawn(); Pawn && Pawn->IsWalkingMode() && !bControlsOpen) Pawn->TogglePersonCamera();
}

void ABreziPlayerController::RecenterPersonCamera()
{
    if (ABreziPawn* Pawn = TwinPawn(); Pawn && !bControlsOpen) Pawn->RecenterCamera();
}

void ABreziPlayerController::ToggleHudCursor()
{
    if (bWalkthroughAutomation || !HasForegroundWindow()) return;
    if (InitialTour.IsPending()) { PauseGameplay(); return; }
    if (bHudCursor) { ResumeGameplay(); return; }
    EndNavigation();
    bControlsOpen = false;
    bHudCursor = true;
    if (ABreziPawn* Pawn = TwinPawn()) { Pawn->SetNavigating(true); Pawn->SetMouseLookEnabled(false); }
    UpdateAccessibleSubtrees();
    FocusControl(DestinationButton);
}

void ABreziPlayerController::SendHudKey(FKey Key, bool bDown)
{
    if (Key == EKeys::Left || Key == EKeys::Right) return; // HUD arrows rotate; physical arrows retain native WASD parity.
    const FInputDeviceId Device = IPlatformInputDeviceMapper::Get().GetDefaultInputDevice();
    FViewport* Viewport = GEngine && GEngine->GameViewport ? GEngine->GameViewport->Viewport : nullptr;
    InputKey(FInputKeyEventArgs(Viewport, Device, Key, bDown ? IE_Pressed : IE_Released,
        bDown ? 1.0f : 0.0f, false, FPlatformTime::Cycles64()));
}

void ABreziPlayerController::BeginHudMovement(FKey Key)
{
    if (!bHudCursor || bControlsOpen || !IsGameplayActive()
        || !(TwinPawn()->IsWalkingMode() || TwinPawn()->IsFlightMode())) return;
    HudReleaseTimes.Remove(Key);
    HudPressTimes.Add(Key, FPlatformTime::Seconds());
    HudMovementKeys.Add(Key);
    SendHudKey(Key, true);
}

void ABreziPlayerController::EndHudMovement(FKey Key)
{
    if (const double* Started = HudPressTimes.Find(Key))
        HudReleaseTimes.Add(Key, FMath::Max(FPlatformTime::Seconds(), *Started + 0.12));
}

void ABreziPlayerController::StopHudMovement()
{
    for (FKey Key : HudMovementKeys) SendHudKey(Key, false);
    HudMovementKeys.Empty();
    HudPressTimes.Empty();
    HudReleaseTimes.Empty();
    if (ABreziPawn* Pawn = TwinPawn()) Pawn->StopWalkingInput();
    if (PlayerInput) PlayerInput->FlushPressedKeys();
}

void ABreziPlayerController::SelectNumberedView(int32 Index, bool bInstant)
{
    if (ABreziPawn* Pawn = TwinPawn(); Pawn && Pawn->GetViewpoints().IsValidIndex(Index))
    {
        InitialTour.Cancel(); // An explicit destination supersedes the default arrival.
        PauseGameplay();
        const FBreziViewpoint& View = Pawn->GetViewpoints()[Index];
        if (View.bWalking) Pawn->SelectWalkingView(View.Id);
        else Pawn->SelectView(View.Id, bInstant);
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
    if (InitialTour.IsPending()) { ResumeGameplay(); return; }
    if (ABreziPawn* Pawn = TwinPawn())
    {
        FString Traversal;
        if (FParse::Value(FCommandLine::Get(), TEXT("BreziWalkTraversal="), Traversal)
            || FParse::Value(FCommandLine::Get(), TEXT("BreziWalkthrough="), Traversal))
        {
            // Opt-in traversal owns its one initial fixture placement. Its
            // next F2 input separately proves capture through the engine route.
            EndNavigation();
            Pawn->ToggleMovementMode();
            return;
        }
        if (Pawn->IsWalkingMode()) SelectNumberedView(0);
        else
        {
            PauseGameplay();
            if (Pawn->StartWalkingTour()) ResumeGameplay();
            else FocusControl(NavigationFeedback);
        }
    }
}

void ABreziPlayerController::ToggleFreeFlightShortcut()
{
    // Legacy BindKey accepts additional modifiers; leave native Cmd+H and
    // accessibility Control/Option chords to macOS even with viewport focus.
    if (IsInputKeyDown(EKeys::LeftCommand) || IsInputKeyDown(EKeys::RightCommand)
        || IsInputKeyDown(EKeys::LeftControl) || IsInputKeyDown(EKeys::RightControl)
        || IsInputKeyDown(EKeys::LeftAlt) || IsInputKeyDown(EKeys::RightAlt)) return;
    ToggleFreeFlight();
}

void ABreziPlayerController::ToggleFreeFlight()
{
    ABreziPawn* Pawn = TwinPawn();
    if (!Pawn || !Pawn->HasViewpoints() || (!bWalkthroughAutomation && !HasForegroundWindow())) return;
    InitialTour.Cancel();
    PauseGameplay(false);
    const bool bEntered = Pawn->IsFlightMode() ? Pawn->StartWalkingTour() : Pawn->StartFreeFlight();
    if (bEntered) ResumeGameplay();
    else FocusControl(NavigationFeedback);
}

TSharedRef<SWidget> ABreziPlayerController::BuildFlightControl(bool bMenu)
{
    const auto IsFlying = [this] { return TwinPawn() && TwinPawn()->IsFlightMode(); };
    const TAttribute<FText> Hint = TAttribute<FText>::CreateLambda([IsFlying]
    {
        return IsFlying() ? LOCTEXT("FlightReturnAX", "Vrátiť sa do prechádzky v obývačke · H")
            : LOCTEXT("FlightStartAX", "Spustiť voľný prelet okolo domu · H. WASD pohyb, E nahor, Q nadol.");
    });
    TSharedRef<BreziUI::SGameButton> Button = SNew(BreziUI::SGameButton)
        .ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(12, 8))
        .IsEnabled_Lambda([this] { return TwinPawn() && TwinPawn()->HasViewpoints(); })
        .AccessibleParams(AccessibleControl(Hint)).ToolTipText(Hint)
        .OnClicked_Lambda([this] { ToggleFreeFlight(); return FReply::Handled(); })
        [SNew(SHorizontalBox)
            + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[BreziUI::Glyph(BreziUI::Icon::Flight, 20, Accent)]
            + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(9, 0, 9, 0)
            [SNew(STextBlock).Text_Lambda([IsFlying, bMenu]
                { return IsFlying() ? LOCTEXT("FlightReturn", "Prechádzka")
                    : bMenu ? LOCTEXT("FlightStartMenu", "Prelet okolo domu") : LOCTEXT("FlightStart", "Prelet"); })
                .Font(Font("Medium", 12)).ColorAndOpacity(Ink)]
            + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[BreziUI::Keycap(FText::FromString(TEXT("H")))]];
    if (bMenu) PanelControls.Add(Button);
    else ToolbarControls.Add(Button);
    return Button;
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
    UCameraComponent* Camera = Pawn ? Pawn->GetPhysicalCamera() : nullptr;
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
        : (Pawn ? Pawn->GetPhysicalCamera() : nullptr);
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
    ABreziDoubleGlassActor::InvalidateScene(GetWorld());
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
    ABreziDoubleGlassActor::InvalidateScene(GetWorld());
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
    return ViewportWidth > 0.0f ? FMath::Min(760.0f, FMath::Max(240.0f, ViewportWidth - HorizontalSafeInsets)) : 760.0f;
}

void ABreziPlayerController::SetMenuSection(int32 Section)
{
    MenuSection = FMath::Clamp(Section, 0, 2);
    if (bControlsOpen && MenuSectionControls.IsValidIndex(MenuSection)) FocusControl(MenuSectionControls[MenuSection]);
    if (ControlsScrollBox.IsValid()) ControlsScrollBox->ScrollToStart();
    UpdateAccessibleSubtrees();
}

void ABreziPlayerController::UpdateViewButtons()
{
    if (!ViewButtons.IsValid() || !TwinPawn()) return;
    TArray<FString> NewIds;
    for (const FBreziViewpoint& View : TwinPawn()->GetViewpoints()) NewIds.Add(View.Id + TEXT("|") + View.Label);
    if (NewIds == InterfaceViewIds) return;
    InterfaceViewIds = MoveTemp(NewIds);
    ViewButtons->ClearChildren();
    ViewControls.Empty();
    int32 Index = 0;
    for (const FBreziViewpoint& View : TwinPawn()->GetViewpoints())
    {
        const FString Id = View.Id;
        const int32 Choice = Index++;
        const FText Label = FText::FromString(RoomName(Id, View.Label));
        const FText Detail = FText::FromString(Id.StartsWith(TEXT("room-1-")) ? TEXT("1.") + Id.Right(2)
            : Id == TEXT("room-dressing") ? TEXT("1.14") : Choice == 0 ? TEXT("OBĽÚBENÝ POHĽAD") : TEXT("EXTERIÉR"));
        TSharedPtr<BreziUI::SGameButton> Button;
        ViewButtons->AddSlot()[SNew(SBox)
            .WidthOverride_Lambda([this] { return FMath::Max(120.0f, (GetViewDockWidth() - 80.0f) / 2.0f); })
            [SAssignNew(Button, BreziUI::SGameButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(14, 11))
                .Visibility_Lambda([this] { return bControlsOpen && MenuSection == 0 ? EVisibility::Visible : EVisibility::Collapsed; })
                .AccessibleParams(AccessibleControl(FText::FromString(View.Label))).ToolTipText(FText::FromString(View.Label))
                .OnClicked_Lambda([this, Choice] { SelectNumberedView(Choice, true); ResumeGameplay(); return FReply::Handled(); })
                [SNew(SHorizontalBox)
                    + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 12, 0)
                    [BreziUI::Glyph(Choice > 0 && Choice < 4 ? BreziUI::Icon::Sun : BreziUI::Icon::Rooms, 20, Quiet)]
                    + SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)
                    [SNew(SVerticalBox)
                        + SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(Detail).Font(Font("Bold", 8, 100)).ColorAndOpacity(Quiet)]
                        + SVerticalBox::Slot().AutoHeight().Padding(0, 4, 0, 0)
                        [SNew(STextBlock).Text(Label).Font(Font("Medium", 12)).ColorAndOpacity(Ink).AutoWrapText(true)]]
                    + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8, 0, 0, 0)
                    [SNew(SBox).Visibility_Lambda([this, Id] { return TwinPawn() && TwinPawn()->GetActiveViewId() == Id ? EVisibility::HitTestInvisible : EVisibility::Hidden; })
                        [BreziUI::Glyph(BreziUI::Icon::Check, 16, Accent)]]]]];
        ViewControls.Add(Button);
    }
}

TSharedRef<SWidget> ABreziPlayerController::BuildRenderQualityChoices()
{
    using BreziRenderQuality::Profile;
    RenderQualityControls.Empty();
    const auto Visible = [this] { return bControlsOpen ? EVisibility::Visible : EVisibility::Collapsed; };
    TSharedRef<SVerticalBox> Choices = SNew(SVerticalBox);
    Choices->AddSlot().AutoHeight().Padding(0, 0, 0, 10)
    [SNew(STextBlock).Visibility_Lambda(Visible).Text(LOCTEXT("QualityTitle", "KVALITA OBRAZU"))
        .Font(Font("Bold", 10, 80)).ColorAndOpacity(Ink)];
    TSharedRef<SHorizontalBox> Cards = SNew(SHorizontalBox);
    Choices->AddSlot().AutoHeight()[Cards];
    for (Profile Value : {Profile::Native, Profile::Balanced, Profile::Performance})
    {
        const FText Label = Value == Profile::Native ? LOCTEXT("QualityNative", "Maximálny detail")
            : Value == Profile::Balanced ? LOCTEXT("QualityBalanced", "Vyvážené") : LOCTEXT("QualityPerformance", "Plynulosť");
        const FText Detail = Value == Profile::Native ? LOCTEXT("QualityNativeDetail", "Najjemnejšie detaily")
            : Value == Profile::Balanced ? LOCTEXT("QualityBalancedDetail", "Rovnováha detailov a plynulosti")
            : LOCTEXT("QualityPerformanceDetail", "Uprednostniť rýchlu odozvu");
        TSharedPtr<SCheckBox> Choice;
        Cards->AddSlot().FillWidth(1).Padding(Value == Profile::Native ? 0 : 8, 0, 0, 0)
        [SAssignNew(Choice, BreziUI::SGameCheckBox).Style(&QuietToggleStyle()).Padding(FMargin(14, 12)).Visibility_Lambda(Visible)
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
                [SNew(STextBlock).Text(Label).Font(Font("Medium", 12)).AutoWrapText(true).ColorAndOpacity(Ink)]
                + SVerticalBox::Slot().AutoHeight().Padding(0, 6, 0, 0)
                [SNew(STextBlock).Text(Detail).Font(Font("Regular", 10)).AutoWrapText(true)
                    .ColorAndOpacity_Lambda([this] { return FSlateColor(bIncreaseContrast ? Ink : Quiet); })]]];
        RenderQualityControls.Add(Choice);
    }
    Choices->AddSlot().AutoHeight().Padding(0, 10, 0, 4)
    [SNew(STextBlock).Visibility_Lambda(Visible).Text_Lambda([this] { return RenderQualityStatus(); })
        .Font(Font("Regular", 10)).AutoWrapText(true)
        .ColorAndOpacity_Lambda([this] { return FSlateColor(bIncreaseContrast ? Ink : Quiet); })];
    return Choices;
}

TSharedRef<SWidget> ABreziPlayerController::BuildControlsMenu()
{
    PanelControls.Empty();
    const auto Visible = [this] { return bControlsOpen ? EVisibility::Visible : EVisibility::Collapsed; };
    FString RequestedSection;
    if (FParse::Value(FCommandLine::Get(), TEXT("BreziMenuSection="), RequestedSection))
        MenuSection = RequestedSection == TEXT("atmosphere") ? 1 : RequestedSection == TEXT("controls") ? 2 : 0;
    TSharedPtr<BreziUI::SGameButton> LivingButton, SystemButton;
    TSharedPtr<SCheckBox> NightToggle, MotionToggle;
    TSharedPtr<SSlider> SensitivitySlider;
    TSharedRef<SVerticalBox> Settings = SNew(SVerticalBox);
    Settings->AddSlot().AutoHeight().Padding(0, 0, 0, 18)
        [SAssignNew(NightToggle, BreziUI::SGameCheckBox).Style(&QuietToggleStyle()).Padding(FMargin(16, 14))
            .IsEnabled_Lambda([this] { return Sun.IsValid(); })
            .AccessibleParams(AccessibleControl(LOCTEXT("NightModeLabel", "Nočné osvetlenie")))
            .IsChecked_Lambda([this] { return bNight ? ECheckBoxState::Checked : ECheckBoxState::Unchecked; })
            .OnCheckStateChanged_Lambda([this](ECheckBoxState State) { if ((State == ECheckBoxState::Checked) != bNight) ToggleTimeOfDay(); })
            [SNew(SHorizontalBox)
                + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 14, 0)[BreziUI::Glyph(BreziUI::Icon::Moon, 22, Accent)]
                + SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)
                [SNew(SVerticalBox)
                    + SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(LOCTEXT("NightSceneTitle", "Nočná atmosféra")).Font(Font("Medium", 13)).ColorAndOpacity(Ink)]
                    + SVerticalBox::Slot().AutoHeight().Padding(0, 4, 0, 0)
                    [SNew(STextBlock).Text_Lambda([this] { return bNight ? LOCTEXT("LightOn", "Zapnutá · teplé svetlo interiéru") : LOCTEXT("LightOff", "Vypnutá · denné svetlo"); })
                        .Font(Font("Regular", 11)).ColorAndOpacity(Quiet)]]
                + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[BreziUI::Keycap(FText::FromString(TEXT("N")))]]];
    Settings->AddSlot().AutoHeight()[BuildRenderQualityChoices()];
    AtmosphereControls = {NightToggle};
    AtmosphereControls.Append(RenderQualityControls);

    TSharedRef<SWrapBox> Inputs = SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(24, 20));
    const auto InputColumnWidth = [this] { const float Width = GetViewDockWidth() - 72.0f;
        return GetViewDockWidth() < 600 ? Width : (Width - 24.0f) / 2.0f; };
    TSharedRef<SVerticalBox> Shortcuts = SNew(SVerticalBox);
    TSharedRef<SVerticalBox> Preferences = SNew(SVerticalBox);
    Inputs->AddSlot()[SNew(SBox).WidthOverride_Lambda(InputColumnWidth)[Shortcuts]];
    Inputs->AddSlot()[SNew(SBox).WidthOverride_Lambda(InputColumnWidth)[Preferences]];
    TSharedRef<SWrapBox> Legend = SNew(SWrapBox).UseAllottedSize(true).InnerSlotPadding(FVector2D(24, 14));
    for (const auto& Pair : TArray<TPair<FString, FString>>{
        {TEXT("W A S D"), TEXT("Pohyb")}, {TEXT("SHIFT"), TEXT("Rýchlejšie")}, {TEXT("H"), TEXT("Prelet / prechádzka")},
        {TEXT("E / Q"), TEXT("Let: nahor / nadol")}, {TEXT("ALT"), TEXT("Let: pomalšie")},
        {TEXT("Q"), TEXT("Chôdza: pomalšie")}, {TEXT("E"), TEXT("Chôdza: dvere")},
        {TEXT("V"), TEXT("Postava / oči")}, {TEXT("R"), TEXT("Vystrediť")},
        {TEXT("TAB"), TEXT("Voľný kurzor")}, {TEXT("ESC"), TEXT("Pauza / návrat")}})
        Legend->AddSlot()[KeyHint(*Pair.Key, *Pair.Value)];
    Shortcuts->AddSlot().AutoHeight().Padding(0, 0, 0, 16)[Legend];
    Shortcuts->AddSlot().AutoHeight()
        [SNew(STextBlock).Text(LOCTEXT("LookAndZoom", "Myšou sa rozhliadate. Kolieskom alebo gestom dvoch prstov približujete kameru."))
            .Font(Font("Regular", 11)).AutoWrapText(true).ColorAndOpacity(Quiet)];
    Preferences->AddSlot().AutoHeight().Padding(0, 0, 0, 4)
        [SNew(SHorizontalBox)
            + SHorizontalBox::Slot().FillWidth(1)[SNew(STextBlock).Text(LOCTEXT("LookSensitivity", "Citlivosť rozhliadania")).Font(Font("Medium", 13)).ColorAndOpacity(Ink)]
            + SHorizontalBox::Slot().AutoWidth()[SNew(STextBlock).Text_Lambda([this] { return FText::Format(LOCTEXT("LookSensitivityNumber", "{0}×"), FText::AsNumber(MouseSensitivity)); })
                .Font(Font("Bold", 12)).ColorAndOpacity(Accent)]];
    Preferences->AddSlot().AutoHeight().Padding(6, 0, 6, 12)
        [SNew(SBox).HeightOverride(44)
        [SAssignNew(SensitivitySlider, BreziUI::SGameSlider).Style(&BreziUI::SliderStyle())
            .RequiresControllerLock(false).MinValue(0.25f).MaxValue(3.0f).StepSize(0.05f)
            .SliderBarColor_Lambda([this] { return BreziUI::SliderRailColor(bIncreaseContrast); }).SliderHandleColor(Accent).Value_Lambda([this] { return MouseSensitivity; })
            .AccessibleParams(AccessibleControl(LOCTEXT("MouseSensitivity", "Citlivosť myši, od 0,25 po 3 násobok. Šípky menia hodnotu.")))
            .OnValueChanged_Lambda([this](float Value)
            { MouseSensitivity = BreziNavigation::Sensitivity(Value); if (TwinPawn()) TwinPawn()->SetLookSensitivity(MouseSensitivity); })]];
    Preferences->AddSlot().AutoHeight().Padding(0, 0, 0, 8)
        [SAssignNew(MotionToggle, BreziUI::SGameCheckBox).Style(&QuietToggleStyle()).Padding(FMargin(14, 14))
            .AccessibleParams(AccessibleControl(LOCTEXT("MotionLabel", "Obmedziť pohyb kamery")))
            .IsChecked_Lambda([this] { return bReducedMotion ? ECheckBoxState::Checked : ECheckBoxState::Unchecked; })
            .OnCheckStateChanged_Lambda([this](ECheckBoxState State) { if ((State == ECheckBoxState::Checked) != bReducedMotion) ToggleReducedMotion(); })
            [SNew(SHorizontalBox)
                + SHorizontalBox::Slot().FillWidth(1)[SNew(STextBlock).Text(LOCTEXT("ReducedMotionTitle", "Pokojnejšia kamera")).Font(Font("Medium", 12)).ColorAndOpacity(Ink)]
                + SHorizontalBox::Slot().AutoWidth()[SNew(STextBlock).Text_Lambda([this] { return bReducedMotion ? LOCTEXT("On", "Zapnuté") : LOCTEXT("Off", "Vypnuté"); })
                    .Font(Font("Regular", 11)).ColorAndOpacity(Accent)]]];
    Preferences->AddSlot().AutoHeight()
        [SAssignNew(SystemButton, BreziUI::SGameButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(14, 8))
            .AccessibleParams(AccessibleControl(LOCTEXT("SystemMotion", "Použiť nastavenie pohybu macOS")))
            .OnClicked_Lambda([this] { UseSystemMotionPreference(); return FReply::Handled(); })
            [SNew(STextBlock).Text_Lambda([this] { return bUseSystemMotion ? LOCTEXT("SystemFollowed", "Používa sa nastavenie pohybu macOS") : LOCTEXT("SystemResume", "Prevziať nastavenie z macOS"); })
                .Font(Font("Regular", 11)).ColorAndOpacity(Quiet).AutoWrapText(true)]];
    InputControls = {SensitivitySlider, MotionToggle, SystemButton};

    TSharedRef<SHorizontalBox> Tabs = SNew(SHorizontalBox);
    const TArray<FText> Names = {LOCTEXT("MenuRooms", "Miestnosti"), LOCTEXT("MenuAtmosphere", "Atmosféra"), LOCTEXT("MenuInputs", "Ovládanie")};
    const TArray<BreziUI::Icon> Icons = {BreziUI::Icon::Rooms, BreziUI::Icon::Sun, BreziUI::Icon::Mouse};
    MenuSectionControls.Empty();
    for (int32 Section = 0; Section < Names.Num(); ++Section)
    {
        TSharedPtr<BreziUI::SGameButton> Tab;
        Tabs->AddSlot().FillWidth(1).Padding(Section ? 6 : 0, 0, 0, 0)
            [SAssignNew(Tab, BreziUI::SGameButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(8, 10))
                .AccessibleParams(AccessibleControl(TAttribute<FText>::CreateLambda([this, Section, Names]
                { return MenuSection == Section ? FText::Format(LOCTEXT("SelectedSection", "{0}, vybraná sekcia"), Names[Section]) : Names[Section]; })))
                .OnClicked_Lambda([this, Section] { SetMenuSection(Section); return FReply::Handled(); })
                [SNew(SVerticalBox)
                    + SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)
                    [SNew(SHorizontalBox)
                        + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 8, 0)[BreziUI::Glyph(Icons[Section], 18, Quiet)]
                        + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
                        [SNew(STextBlock).Text(Names[Section]).Font(Font("Medium", 12)).ColorAndOpacity_Lambda([this, Section] { return MenuSection == Section ? Accent : Ink; })]]
                    + SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0, 7, 0, 0)
                    [SNew(SBox).WidthOverride(24).HeightOverride(2)[SNew(SBorder).Padding(0)
                        .BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush")).BorderBackgroundColor_Lambda([this, Section] { return MenuSection == Section ? Accent : FLinearColor::Transparent; })]]]];
        MenuSectionControls.Add(Tab);
    }
    TSharedRef<SWidget> Panel = SNew(SBox)
        .WidthOverride_Lambda([this] { return GetViewDockWidth(); })
        .HeightOverride_Lambda([this] { const float H = Interface.IsValid() ? Interface->GetCachedGeometry().GetLocalSize().Y : 0;
            return H > 0 ? FMath::Clamp(H - (H < 440 ? 32.0f : 56.0f), 200.0f, 650.0f) : 500.0f; })
        .Visibility_Lambda(Visible)
        [SNew(SBorder).BorderImage_Lambda([this] { return &BreziUI::PanelBrush(bIncreaseContrast); })
            .Padding_Lambda([this] { return FMargin(Interface.IsValid() && Interface->GetCachedGeometry().GetLocalSize().Y < 440 ? 12 : 20); })
            [SNew(SVerticalBox)
                + SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 6)
                [SNew(SHorizontalBox)
                    + SHorizontalBox::Slot().FillWidth(1)[SNew(STextBlock).Text(LOCTEXT("MenuBrand", "BŘEZÍ  /  HLAVNÝ NÁVRH C / B / B")).Font(Font("Bold", 9, 150)).ColorAndOpacity(Accent)]
                    + SHorizontalBox::Slot().AutoWidth()[SNew(STextBlock).Text(LOCTEXT("PauseState", "POZASTAVENÉ")).Font(Font("Bold", 8, 100)).ColorAndOpacity(Quiet)]]
                + SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 10)
                [SNew(STextBlock).Text_Lambda([this] { return TwinPawn() && TwinPawn()->IsFlightMode()
                    ? LOCTEXT("FlightPauseTitle", "Voľný prelet okolo domu") : LOCTEXT("PauseTitle", "Prechádzka domom"); }).Font(Font("Light", 22)).ColorAndOpacity(Ink)
                    .Visibility_Lambda([this] { return Interface.IsValid() && Interface->GetCachedGeometry().GetLocalSize().Y < 440 ? EVisibility::Collapsed : EVisibility::HitTestInvisible; })]
                + SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 12)[Tabs]
                + SVerticalBox::Slot().FillHeight(1)
                [SAssignNew(ControlsScrollBox, SScrollBox).ScrollWhenFocusChanges(EScrollWhenFocusChanges::InstantScroll)
                    .NavigationDestination(EDescendantScrollDestination::IntoView).NavigationScrollPadding(8)
                    + SScrollBox::Slot()
                    [SNew(SVerticalBox)
                        + SVerticalBox::Slot().AutoHeight()
                        [SAssignNew(RoomsAXContainer, SBox).Visibility_Lambda([this] { return MenuSection == 0 ? EVisibility::SelfHitTestInvisible : EVisibility::Collapsed; })
                            [SNew(SVerticalBox)
                                + SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 14)
                                [SNew(STextBlock).Text(LOCTEXT("RoomsIntro", "Vyberte si, kde chcete pokračovať."))
                                    .Font(Font("Regular", 12)).ColorAndOpacity(Quiet)]
                                + SVerticalBox::Slot().AutoHeight()[ViewButtons.ToSharedRef()]]]
                        + SVerticalBox::Slot().AutoHeight()
                        [SAssignNew(AtmosphereAXContainer, SBox).Visibility_Lambda([this] { return MenuSection == 1 ? EVisibility::SelfHitTestInvisible : EVisibility::Collapsed; })[Settings]]
                        + SVerticalBox::Slot().AutoHeight()
                        [SAssignNew(InputAXContainer, SBox).Visibility_Lambda([this] { return MenuSection == 2 ? EVisibility::SelfHitTestInvisible : EVisibility::Collapsed; })[Inputs]]
                    ]]
                + SVerticalBox::Slot().AutoHeight().Padding(0, 10, 0, 10)[Hairline()]
                + SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 8)[BuildFlightControl(true)]
                + SVerticalBox::Slot().AutoHeight()
                [SAssignNew(FeedbackAXContainer, SBox)
                    .Visibility_Lambda([this] { return bControlsOpen && TwinPawn() && !TwinPawn()->GetNavigationMessage().IsEmpty() ? EVisibility::SelfHitTestInvisible : EVisibility::Collapsed; })
                    [SAssignNew(NavigationFeedback, SButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(8, 10))
                        .AccessibleParams(AccessibleControl(TAttribute<FText>::CreateLambda([this] { return TwinPawn() ? TwinPawn()->GetNavigationMessage() : FText::GetEmpty(); })))
                        .OnClicked_Lambda([this] { if (TwinPawn()) TwinPawn()->DismissNavigationMessage(); FocusControl(NavigationButton); return FReply::Handled(); })
                        [SNew(STextBlock).Text_Lambda([this] { return TwinPawn() ? TwinPawn()->GetNavigationMessage() : FText::GetEmpty(); })
                            .AutoWrapText(true).Font(Font("Regular", 11)).ColorAndOpacity(Ink)]]]
                + SVerticalBox::Slot().AutoHeight()
                [SNew(SHorizontalBox)
                    + SHorizontalBox::Slot().FillWidth(1).Padding(0, 0, 10, 0)
                    [SAssignNew(LivingButton, BreziUI::SGameButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(12, 10))
                        .AccessibleParams(AccessibleControl(LOCTEXT("LivingArrival", "Začať z obývačky")))
                        .OnClicked_Lambda([this]
                        { if (InitialTour.IsPending()) { ResumeGameplay(); return FReply::Handled(); }
                            EndNavigation(); if (TwinPawn() && TwinPawn()->StartWalkingTour()) ResumeGameplay(); else FocusControl(NavigationFeedback); return FReply::Handled(); })
                        [SNew(STextBlock).Text(LOCTEXT("LivingRestart", "Od začiatku")).Font(Font("Medium", 12)).ColorAndOpacity(Ink)]]
                    + SHorizontalBox::Slot().FillWidth(1.4f)
                    [SAssignNew(NavigationButton, BreziUI::SGameButton).ButtonStyle(&BreziUI::ButtonStyle(true)).ContentPadding(FMargin(16, 12))
                        .IsEnabled_Lambda([this] { return TwinPawn() && TwinPawn()->HasViewpoints(); })
                        .AccessibleParams(AccessibleControl(LOCTEXT("ResumeAX", "Pokračovať. Escape zatvorí menu a vráti herné ovládanie.")))
                        .OnClicked_Lambda([this] { ResumeGameplay(); return FReply::Handled(); })
                        [SNew(SHorizontalBox)
                            + SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)
                            [SNew(STextBlock).Text(LOCTEXT("ResumeShort", "Pokračovať")).Font(Font("Bold", 13)).ColorAndOpacity(BreziUI::Inset)]
                            + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[BreziUI::Glyph(BreziUI::Icon::Play, 18, BreziUI::Inset)]]]]
            ]];
    ControlsAXContainer = Panel;
    WalkingModeControl = LivingButton;
    PanelControls.Add(LivingButton);
    PanelControls.Add(NavigationButton);
    return Panel;
}

FReply ABreziPlayerController::HandleDestinationKey(const FKeyEvent& Event)
{
    if (Event.IsControlDown() || Event.IsAltDown() || Event.IsCommandDown()) return FReply::Unhandled();
    if (Event.GetKey() == EKeys::Escape)
    {
        if (DestinationAnchor.IsValid()) DestinationAnchor->SetIsOpen(false);
        FocusControl(DestinationButton);
        return FReply::Handled();
    }
    if (Event.GetKey() != EKeys::Tab || DestinationControls.IsEmpty()) return FReply::Unhandled();
    const int32 Current = DestinationControls.IndexOfByKey(FSlateApplication::Get().GetKeyboardFocusedWidget());
    const int32 Next = Current == INDEX_NONE ? (Event.IsShiftDown() ? DestinationControls.Num() - 1 : 0)
        : (Current + (Event.IsShiftDown() ? -1 : 1) + DestinationControls.Num()) % DestinationControls.Num();
    FocusControl(DestinationControls[Next]);
    if (DestinationScrollBox.IsValid())
        DestinationScrollBox->ScrollDescendantIntoView(DestinationControls[Next], false, EDescendantScrollDestination::IntoView, 5.0f);
    return FReply::Handled();
}

TSharedRef<SWidget> ABreziPlayerController::BuildDestinationMenu()
{
    DestinationControls.Empty();
    TSharedRef<SVerticalBox> Items = SNew(SVerticalBox);
    if (const ABreziPawn* Pawn = TwinPawn())
    {
        int32 Index = 0;
        for (const FBreziViewpoint& View : Pawn->GetViewpoints())
        {
            const int32 Choice = Index++;
            TSharedRef<SButton> Button = DestinationAction(FText::FromString(RoomName(View.Id, View.Label)), FText::FromString(View.Label), FOnClicked::CreateLambda([this, Choice]
            {
                if (DestinationAnchor.IsValid()) DestinationAnchor->SetIsOpen(false);
                SelectNumberedView(Choice, true);
                ToggleHudCursor();
                return FReply::Handled();
            }));
            Items->AddSlot().AutoHeight().Padding(0, 0, 0, 4)[Button];
            DestinationControls.Add(Button);
        }
    }
    return SNew(SBreziInterface)
        .OnPreviewTab_Lambda([this](const FGeometry&, const FKeyEvent& Event) { return HandleDestinationKey(Event); })
        .OnUnhandledKey_Lambda([this](const FGeometry&, const FKeyEvent& Event) { return HandleDestinationKey(Event); })
        [SNew(SBorder).BorderImage_Lambda([this] { return &BreziUI::PanelBrush(bIncreaseContrast); }).Padding(12)
            [SNew(SBox).WidthOverride(272).MaxDesiredHeight_Lambda([this]
                { const float H = Interface.IsValid() ? Interface->GetCachedGeometry().GetLocalSize().Y : 540; return FMath::Max(100.0f, FMath::Min(440.0f, H - 160.0f)); })
                [SNew(SVerticalBox)
                    + SVerticalBox::Slot().AutoHeight().Padding(4, 2, 4, 12)
                    [SNew(STextBlock).Text(LOCTEXT("QuickRooms", "PRESKÚMAŤ DOM")).Font(Font("Bold", 9, 130)).ColorAndOpacity(Accent)]
                    + SVerticalBox::Slot().FillHeight(1)
                    [SAssignNew(DestinationScrollBox, SScrollBox) + SScrollBox::Slot()[Items]]]]];
}

TSharedRef<SWidget> ABreziPlayerController::BuildVisibleControls()
{
    using BreziUI::Icon;
    ToolbarControls.Empty();
    TSharedRef<SWrapBox> Dock = SNew(SWrapBox).UseAllottedSize(false)
        .PreferredSize_Lambda([this] { const float W = Interface.IsValid() ? Interface->GetCachedGeometry().GetLocalSize().X : 960;
            return FMath::Min(780.0f, FMath::Max(240.0f, W - 64.0f)); }).InnerSlotPadding(FVector2D(5, 5));
    const auto Add = [this, Dock](Icon Symbol, const TCHAR* Key, TAttribute<FText> Hint, TFunction<void()> Action)
    {
        TSharedPtr<BreziUI::SGameButton> Button;
        Dock->AddSlot()[SAssignNew(Button, BreziUI::SGameButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(12, 8))
            .IsEnabled_Lambda([this, Symbol] { return (Symbol != Icon::Person && Symbol != Icon::Recenter)
                || (TwinPawn() && TwinPawn()->IsWalkingMode()); })
            .AccessibleParams(AccessibleControl(Hint)).ToolTipText(Hint)
            .OnClicked_Lambda([Action] { Action(); return FReply::Handled(); })
            [SNew(SHorizontalBox)
                + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[BreziUI::Glyph(Symbol, 20)]
                + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(Key[0] ? 7 : 0, 0, 0, 0)
                [SNew(STextBlock).Text_Lambda([this, Symbol, Key] { return Symbol == Icon::Cursor && bHudCursor
                    ? LOCTEXT("HUDReturnGame", "HRA") : FText::FromString(Key); }).Font(Font("Bold", 9)).ColorAndOpacity(Quiet)]]];
        ToolbarControls.Add(Button);
    };
    DestinationButton = DestinationAction(LOCTEXT("HUDRoom", "Priestory"),
        LOCTEXT("HUDDestinationAX", "Vybrať miestnosť alebo pohľad na dom"), FOnClicked::CreateLambda([this]
        {
            FReply Reply = FReply::Handled();
            if (!DestinationAnchor.IsValid()) return Reply;
            StopHudMovement();
            DestinationAnchor->SetIsOpen(DestinationAnchor->ShouldOpenDueToClick(), false);
            if (DestinationAnchor->IsOpen() && !DestinationControls.IsEmpty())
            {
                FocusControl(DestinationControls[0]);
                Reply.SetUserFocus(DestinationControls[0].ToSharedRef(), EFocusCause::SetDirectly);
            }
            return Reply;
        }));
    DestinationButton->SetContent(SNew(SHorizontalBox)
        + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[BreziUI::Glyph(Icon::Rooms, 20, Accent)]
        + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(10, 0, 4, 0)
        [SNew(STextBlock).Text(LOCTEXT("HUDRoom", "Priestory")).Font(Font("Medium", 12)).ColorAndOpacity(Ink)]);
    Dock->AddSlot()[SAssignNew(DestinationAnchor, SMenuAnchor).Placement(MenuPlacement_AboveAnchor)
        .Method(EPopupMethod::UseCurrentWindow).OnGetMenuContent_Lambda([this] { return BuildDestinationMenu(); })[DestinationButton.ToSharedRef()]];
    ToolbarControls.Add(DestinationButton);
    Dock->AddSlot()[BuildFlightControl(false)];
    Add(Icon::Person, TEXT("V"), TAttribute<FText>::CreateLambda([this] { return TwinPawn() && TwinPawn()->IsThirdPersonCamera()
        ? LOCTEXT("HUDEyes", "Pohľad z očí · V") : LOCTEXT("HUDPerson", "Kamera za postavou · V"); }), [this] { TogglePersonCamera(); });
    Add(Icon::Recenter, TEXT("R"), LOCTEXT("HUDCenterAX", "Vystrediť kameru za postavou · R"), [this] { RecenterPersonCamera(); });
    Add(Icon::Minus, TEXT(""), LOCTEXT("HUDZoomOutAX", "Oddialiť kameru · koliesko alebo touchpad"), [this] { ZoomOut(); });
    Add(Icon::Plus, TEXT(""), LOCTEXT("HUDZoomInAX", "Priblížiť kameru · koliesko alebo touchpad"), [this] { ZoomIn(); });
    Add(Icon::Sun, TEXT("N"), TAttribute<FText>::CreateLambda([this] { return bNight ? LOCTEXT("HUDDay", "Denné svetlo · N") : LOCTEXT("HUDNight", "Nočná atmosféra · N"); }), [this] { ToggleTimeOfDay(); });
    Add(Icon::Settings, TEXT(""), LOCTEXT("HUDSettingsAX", "Atmosféra a kvalita obrazu"), [this] { SetMenuSection(1); PauseGameplay(); });
    Add(Icon::Cursor, TEXT("TAB"), TAttribute<FText>::CreateLambda([this] { return bHudCursor ? LOCTEXT("HUDGameMouse", "Vrátiť herné ovládanie") : LOCTEXT("HUDCursor", "Uvoľniť kurzor · Tab"); }), [this] { ToggleHudCursor(); });

    TSharedRef<SHorizontalBox> Movement = SNew(SHorizontalBox);
    for (const auto& Item : TArray<TPair<FKey, Icon>>{{EKeys::Left, Icon::ArrowLeft}, {EKeys::W, Icon::ArrowUp}, {EKeys::S, Icon::ArrowDown}, {EKeys::Right, Icon::ArrowRight}})
    {
        const FKey Key = Item.Key;
        const FText Name = Key == EKeys::W ? LOCTEXT("HUDForwardAX", "Pohyb dopredu. Podržte alebo kliknite pre krátky posun.")
            : Key == EKeys::S ? LOCTEXT("HUDBackAX", "Pohyb dozadu") : Key == EKeys::Left ? LOCTEXT("HUDLeftAX", "Otočiť doľava") : LOCTEXT("HUDRightAX", "Otočiť doprava");
        TSharedPtr<BreziUI::SGameButton> Button;
        Movement->AddSlot().AutoWidth().Padding(3, 0)
            [SAssignNew(Button, BreziUI::SGameButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(12, 10))
                .Visibility_Lambda([this] { return bHudCursor && TwinPawn() && (TwinPawn()->IsWalkingMode() || TwinPawn()->IsFlightMode()) ? EVisibility::Visible : EVisibility::Collapsed; })
                .AccessibleParams(AccessibleControl(Name)).ToolTipText(Name)
                .OnPressed_Lambda([this, Key] { BeginHudMovement(Key); }).OnReleased_Lambda([this, Key] { EndHudMovement(Key); })
                .OnClicked_Lambda([this, Key]
                {
                    // Native AX activation calls OnClicked without press/release.
                    // A real held button already owns its bounded release pulse.
                    if (!HudMovementKeys.Contains(Key)) { BeginHudMovement(Key); EndHudMovement(Key); }
                    return FReply::Handled();
                })
                [BreziUI::Glyph(Item.Value, 20)]];
        ToolbarControls.Add(Button);
    }
    TSharedRef<SHorizontalBox> Altitude = SNew(SHorizontalBox);
    for (const FKey Key : {EKeys::E, EKeys::Q})
    {
        const FText Name = Key == EKeys::E ? LOCTEXT("HUDAscendAX", "Letieť nahor · E") : LOCTEXT("HUDDescendAX", "Letieť nadol · Q");
        TSharedPtr<BreziUI::SGameButton> Button;
        Altitude->AddSlot().AutoWidth().Padding(3, 0)
            [SAssignNew(Button, BreziUI::SGameButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(12, 10))
                .Visibility_Lambda([this] { return bHudCursor && TwinPawn() && TwinPawn()->IsFlightMode() ? EVisibility::Visible : EVisibility::Collapsed; })
                .AccessibleParams(AccessibleControl(Name)).ToolTipText(Name)
                .OnPressed_Lambda([this, Key] { BeginHudMovement(Key); }).OnReleased_Lambda([this, Key] { EndHudMovement(Key); })
                .OnClicked_Lambda([this, Key]
                {
                    // Native AX activation calls OnClicked without press/release.
                    // A real held button already owns its bounded release pulse.
                    if (!HudMovementKeys.Contains(Key)) { BeginHudMovement(Key); EndHudMovement(Key); }
                    return FReply::Handled();
                })
                [SNew(SHorizontalBox)
                    + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[BreziUI::Glyph(Key == EKeys::E ? Icon::ArrowUp : Icon::ArrowDown, 20, Accent)]
                    + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(5, 0, 0, 0)
                    [SNew(STextBlock).Text(FText::FromString(Key == EKeys::E ? TEXT("E") : TEXT("Q"))).Font(Font("Bold", 9)).ColorAndOpacity(Quiet)]]];
        ToolbarControls.Add(Button);
    }
    Movement->AddSlot().AutoWidth()
        [SAssignNew(FlightMovementAXContainer, SBox)
            .Visibility_Lambda([this] { return bHudCursor && TwinPawn() && TwinPawn()->IsFlightMode() ? EVisibility::SelfHitTestInvisible : EVisibility::Collapsed; })[Altitude]];
    TSharedPtr<BreziUI::SGameButton> Stop;
    Movement->AddSlot().AutoWidth().Padding(8, 0, 3, 0)
        [SAssignNew(Stop, BreziUI::SGameButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(12, 10))
            .Visibility_Lambda([this] { return bHudCursor && TwinPawn() && (TwinPawn()->IsWalkingMode() || TwinPawn()->IsFlightMode()) ? EVisibility::Visible : EVisibility::Collapsed; })
            .AccessibleParams(AccessibleControl(LOCTEXT("HUDStopAX", "Zastaviť pohyb"))).ToolTipText(LOCTEXT("HUDStopAX", "Zastaviť pohyb"))
            .OnClicked_Lambda([this] { StopHudMovement(); return FReply::Handled(); })[BreziUI::Glyph(Icon::Stop, 20, Accent)]];
    ToolbarControls.Add(Stop);
    return SNew(SVerticalBox)
        + SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0, 0, 0, 10)
        [SAssignNew(MovementAXContainer, SBox).Visibility_Lambda([this] { return bHudCursor && TwinPawn() && (TwinPawn()->IsWalkingMode() || TwinPawn()->IsFlightMode()) ? EVisibility::SelfHitTestInvisible : EVisibility::Collapsed; })
            [SNew(SBorder).BorderImage(&BreziUI::PanelBrush()).Padding(6)[Movement]]]
        + SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)
        [SNew(SBorder).BorderImage_Lambda([this] { return &BreziUI::PanelBrush(bIncreaseContrast); }).Padding(7)[Dock]]
        + SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0, 9, 0, 0)
        [SNew(STextBlock).Text_Lambda([this] { return bHudCursor
            ? LOCTEXT("HUDPointerHint", "VOĽNÝ KURZOR   ·   TAB VÝBER   ·   ENTER POTVRDIŤ")
            : TwinPawn() && TwinPawn()->IsFlightMode()
                ? LOCTEXT("HUDFlightHint", "PRELET   ·   WASD POHYB   ·   E / Q VÝŠKA   ·   SHIFT RÝCHLEJŠIE   ·   H PRECHÁDZKA")
                : LOCTEXT("HUDGameHint", "WASD POHYB   ·   MYŠ ROZHĽAD   ·   SHIFT RÝCHLEJŠIE"); })
            .Font(Font("Medium", 8, 90)).ColorAndOpacity(Ink).ShadowOffset(FVector2D(0, 1)).ShadowColorAndOpacity(FLinearColor::Black)];
}

void ABreziPlayerController::BuildInterface()
{
    if (!GEngine || !GEngine->GameViewport || Interface.IsValid()) return;
    SAssignNew(ViewButtons, SWrapBox).UseAllottedSize(false)
        .PreferredSize_Lambda([this] { return FMath::Max(1.0f, GetViewDockWidth() - 64.0f); })
        .InnerSlotPadding(FVector2D(8, 8));
    UpdateViewButtons();
    Interface = SNew(SBreziInterface)
        .OnPreviewTab_Lambda([this](const FGeometry&, const FKeyEvent& Event) { return HandleInterfaceKey(Event); })
        .OnUnhandledKey_Lambda([this](const FGeometry&, const FKeyEvent& Event) { return HandleInterfaceKey(Event); })
        [SNew(SOverlay)
            + SOverlay::Slot()
            [SAssignNew(GameplayAXContainer, SBox)
                .Visibility_Lambda([this] { return bControlsOpen ? EVisibility::Collapsed : EVisibility::SelfHitTestInvisible; })
                [SNew(SOverlay)
                    + SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Top).Padding(24, 22)
                    [SNew(SBorder).BorderImage(&BreziUI::PanelBrush()).Padding(FMargin(15, 11))
                        [SNew(SVerticalBox)
                            + SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).Text(LOCTEXT("BrandHUD", "BŘEZÍ"))
                                .Font(Font("Bold", 14, 220)).ColorAndOpacity(Ink)]
                            + SVerticalBox::Slot().AutoHeight().Padding(0, 4, 0, 0)
                            [SNew(STextBlock).Text(LOCTEXT("DesignHUD", "HLAVNÝ NÁVRH C / B / B")).Font(Font("Regular", 8, 70)).ColorAndOpacity(Quiet)]]]
                    + SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Top).Padding(24, 22)
                    [SAssignNew(ControlsButton, BreziUI::SGameButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(13, 10))
                        .AccessibleParams(AccessibleControl(LOCTEXT("PauseMenuAX", "Otvoriť menu a pozastaviť pohyb. Escape.")))
                        .OnClicked_Lambda([this] { SetMenuSection(0); PauseGameplay(); return FReply::Handled(); })
                        [SNew(SHorizontalBox)
                            + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[BreziUI::Glyph(BreziUI::Icon::Menu, 18)]
                            + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(9, 0)
                            [SNew(STextBlock).Text(LOCTEXT("MenuLabel", "Menu")).Font(Font("Medium", 11)).ColorAndOpacity(Ink)]
                            + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[BreziUI::Keycap(FText::FromString(TEXT("ESC")))]]]
                    + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
                    [SNew(SBox).Visibility_Lambda([this] { return IsGameplayActive() && !bHudCursor && TwinPawn()->IsWalkingMode() ? EVisibility::HitTestInvisible : EVisibility::Collapsed; })
                        [BreziUI::Glyph(BreziUI::Icon::Plus, 8, FLinearColor(1, 1, 1, 0.6f))]]
                    + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center).Padding(20, 100, 20, 0)
                    [SAssignNew(InteractionAXContainer, SBox).MaxDesiredWidth(420)
                        .Visibility_Lambda([this] { return InteractionPrompt().IsEmpty() ? EVisibility::Collapsed : EVisibility::Visible; })
                        [SAssignNew(InteractionButton, BreziUI::SGameButton).ButtonStyle(&QuietButtonStyle()).ContentPadding(FMargin(12, 10))
                            .Visibility_Lambda([this] { return InteractionPrompt().IsEmpty() ? EVisibility::Collapsed : EVisibility::Visible; })
                            .AccessibleParams(AccessibleControl(TAttribute<FText>::CreateLambda([this] { return InteractionPrompt(); })))
                            .OnClicked_Lambda([this] { Interact(); return FReply::Handled(); })
                            [SNew(SHorizontalBox)
                                + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 10, 0)[BreziUI::Keycap(FText::FromString(TEXT("E")), true)]
                                + SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)
                                [SNew(STextBlock).Text_Lambda([this] { FString Prompt = InteractionPrompt().ToString(); Prompt.RemoveFromStart(TEXT("E · ")); return FText::FromString(Prompt); })
                                    .Font(Font("Medium", 12)).AutoWrapText(true).ColorAndOpacity(Ink)]]]]
                    + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(24, 18)
                    [BuildVisibleControls()]
                ]]
            + SOverlay::Slot()
            [SNew(SBorder).Padding(0).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
                .BorderBackgroundColor_Lambda([this] { return FLinearColor(0.006f, 0.009f, 0.012f, bReduceTransparency ? 1.0f : 0.70f); })
                .Visibility_Lambda([this] { return bControlsOpen ? EVisibility::Visible : EVisibility::Collapsed; })]
            + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center).Padding(24)
            [BuildControlsMenu()]
        ];
    ToolbarControls.Add(InteractionButton);
    ToolbarControls.Add(ControlsButton);
    UpdateAccessibleSubtrees();
    // GameLayerManager normalizes its pixel-based DPI curve by the platform
    // scale. Restore native point sizing so a 1080p Retina window does not
    // halve every label/control; keep the 3D render target independent.
    InterfaceHost = SNew(SDPIScaler).DPIScale_Lambda([]
    {
        const UGameViewportClient* Viewport = GEngine ? GEngine->GameViewport : nullptr;
        const TSharedPtr<SWindow> Window = Viewport ? Viewport->GetWindow() : nullptr;
        if (!Window.IsValid() || !Viewport->Viewport) return 1.0f;
        const float Curve = GetDefault<UUserInterfaceSettings>()->GetDPIScaleBasedOnSize(Viewport->Viewport->GetSizeXY());
        return FMath::Clamp(Window->GetDPIScaleFactor() / FMath::Max(0.1f, Curve), 0.25f, 4.0f);
    })[Interface.ToSharedRef()];
    GEngine->GameViewport->AddViewportWidgetContent(InterfaceHost.ToSharedRef(), 10);
}

#if WITH_DEV_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBreziMouseTransitionTest, "Brezi.Controls.Hud.MouseTransition",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FBreziMouseTransitionTest::RunTest(const FString& Parameters)
{
    UWorld* World = nullptr;
    if (GEngine)
        for (const FWorldContext& Context : GEngine->GetWorldContexts())
            if (Context.World()) { World = Context.World(); break; }
    if (!TestNotNull(TEXT("Input event timestamps have an initialized engine world"), World)) return false;
    // A separate world-owned input object exercises public event processing;
    // it has no live controller or input-component stack to move the player.
    UPlayerInput* Input = NewObject<UPlayerInput>(World);
    Input->DebugExecBindings.Empty();
    Input->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W, IE_Pressed, 1.0f, 1));
    Input->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::MouseX, IE_Axis, 380.0f, 4));
    Input->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::MouseY, IE_Axis, -270.0f, 4));
    Input->ProcessInputStack(TArray<UInputComponent*>(), 1.0f / 60.0f, false);
    Input->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W, IE_Repeat, 1.0f, 1));
    Input->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::MouseX, IE_Axis, 380.0f, 4));
    Input->InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::MouseY, IE_Axis, -270.0f, 4));
    Input->SmoothedMouse[0] = 20;
    Input->SmoothedMouse[1] = -35;
    ClearStoredMouseLook(Input);
    for (const FKey Key : {EKeys::MouseX, EKeys::MouseY, EKeys::Mouse2D})
    {
        const FKeyState* Mouse = Input->GetKeyState(Key);
        if (!TestNotNull(TEXT("Real mouse events created this axis, including paired Mouse2D"), Mouse)) return false;
        TestTrue(TEXT("Pending and evaluated mouse values are discarded"), Mouse->RawValue.IsZero()
            && Mouse->Value.IsZero() && Mouse->RawValueAccumulator.IsZero());
        TestTrue(TEXT("Old capture samples cannot enter smoothing"), Mouse->SampleCountAccumulator == 0 && Mouse->PairSampledAxes == 0);
    }
    TestTrue(TEXT("Mouse smoothing is reset"), Input->SmoothedMouse[0] == 0 && Input->SmoothedMouse[1] == 0);
    const FKeyState* Preserved = Input->GetKeyState(EKeys::W);
    if (!TestNotNull(TEXT("Real W events created the walking key"), Preserved)) return false;
    TestTrue(TEXT("Held walking and its actual key event survive the mouse-only transition"), Preserved->bDown
        && Preserved->RawValueAccumulator.X == 1 && Preserved->EventCounts[IE_Pressed].Num() == 1
        && Preserved->EventAccumulator[IE_Repeat].Num() == 1);
    return true;
}

#if WITH_ACCESSIBILITY
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBreziDestinationActionTest, "Brezi.Controls.Hud.DestinationAction",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FBreziDestinationActionTest::RunTest(const FString& Parameters)
{
    int32 Activations = 0;
    const FText Label = FText::FromString(TEXT("Miestnosť / pohľad"));
    const TSharedRef<SButton> Button = DestinationAction(Label, Label, FOnClicked::CreateLambda([&Activations]
    {
        ++Activations;
        return FReply::Handled();
    }));
    TestTrue(TEXT("The toolbar stores the actual keyboard focus target"), Button->SupportsKeyboardFocus());
    TestTrue(TEXT("The destination action is accessible"), Button->IsAccessible());
    const TSharedRef<FSlateAccessibleWidget> Accessible = Button->CreateAccessibleWidget();
    TestTrue(TEXT("AX exposes a real button rather than the unknown combo wrapper"), Accessible->GetWidgetType() == EAccessibleWidgetType::Button);
    TestTrue(TEXT("AX supports keyboard focus"), Accessible->SupportsFocus());
    IAccessibleActivatable* Action = Accessible->AsActivatable();
    if (!TestNotNull(TEXT("AX exposes the same real activation path as pointer and keyboard"), Action)) return false;
    Action->Activate();
    TestEqual(TEXT("Native accessibility activation reaches the destination delegate exactly once"), Activations, 1);
    return true;
}
#endif
#endif

#undef LOCTEXT_NAMESPACE
