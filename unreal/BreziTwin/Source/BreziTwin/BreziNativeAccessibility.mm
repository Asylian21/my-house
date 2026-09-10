#include "BreziNativeAccessibility.h"
#include "BreziAXInitializer.h"
#include "BreziGameViewportClient.h"
#include "Async/Async.h"
#include "Containers/Ticker.h"
#include "Misc/CommandLine.h"
#include "Misc/DelayedAutoRegister.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Slate/SceneViewport.h"
#include "Widgets/SViewport.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Widgets/SWindow.h"
#include "Framework/Application/SlateApplication.h"
#include "Mac/MacApplication.h"
#include "Mac/CocoaThread.h"
#if WITH_ACCESSIBILITY
#include "GenericPlatform/Accessibility/GenericAccessibleInterfaces.h"
#include "Mac/Accessibility/MacAccessibilityManager.h"
#include "Mac/Accessibility/MacAccessibilityElement.h"
#include "Widgets/Accessibility/SlateAccessibleWidgetCache.h"
#endif
#include <atomic>
#import <AppKit/AppKit.h>

namespace
{
    std::atomic<bool> NativeWidgetShuttingDown{false};
#if WITH_ACCESSIBILITY
    // Shutdown-only destination: all stock Mac widget queries execute on GT.
    // It never references Slate or forwards queries to the retired handler.
    std::atomic<uint64> ShutdownLookupDrops{0}, ShutdownOffThreadLookups{0};
    std::atomic<uint64> ShutdownSinkMainDeactivations{0}, ShutdownSinkOffMainDeactivations{0};
    TSharedPtr<FGenericAccessibleMessageHandler> RetiredSlateHandler; // Released on GT after queue drain.
    bool bSlateDeactivatedOnGameThread = false;
    bool bShutdownOriginalActive = false;
    bool bShutdownMainHandlerMatched = false;
    bool bShutdownStressRequested = false;
    bool bShutdownStressReturned = false;
    bool bShutdownStressHealthyWindow = false;
    bool bShutdownStressWindowInNativeCache = false;
    bool bShutdownNativeCacheEmpty = false;
    AccessibleWidgetId ShutdownStressWindowId = IAccessibleWidget::InvalidAccessibleWidgetId;
    int32 ShutdownStressSlateChildren = 0, ShutdownStressNativeChildren = 0, ShutdownStressCachedIds = 0;
    uint64 ShutdownStressLookupDelta = 0, ShutdownStressWindowDelta = 0;
    std::atomic<uint64> ShutdownWindowLookupDrops{0};

    class FShutdownAccessibleMessageHandler final : public FGenericAccessibleMessageHandler
    {
    public:
        virtual TSharedPtr<IAccessibleWidget> GetAccessibleWidgetFromId(AccessibleWidgetId Id) const override
        {
            if (!IsInGameThread()) ++ShutdownOffThreadLookups;
            ++ShutdownLookupDrops;
            if (Id == ShutdownStressWindowId) ++ShutdownWindowLookupDrops;
            return nullptr;
        }
    protected:
        virtual void OnDeactivate() override
        {
            // Stock FMacApplication::OnVoiceoverDisabled calls this on Main.
            // Do not call Slate's OnDeactivate/ClearAll here.
            if ([NSThread isMainThread]) ++ShutdownSinkMainDeactivations;
            else ++ShutdownSinkOffMainDeactivations;
        }
    };

    FDelegateHandle NativeWidgetShutdownHandle;
    FDelegateHandle NativeFocusChangingHandle;
    FTSTicker::FDelegateHandle NativeFocusTickerHandle;
    TWeakPtr<SWidget> PendingNativeFocus;
    std::atomic<uint64> NativeFocusRevision{0};
    bool bNativeFocusPending = false;
    int32 NativeFocusAttempts = 0;
    FTSTicker::FDelegateHandle NativeBootstrapTickerHandle;
    bool bNativeBootstrapRequested = false;
    bool bEngineInitBarrierReached = false;
    bool bSkipNativeFocusForwarding = false;
    int32 NativeBootstrapAttempts = 0;
    int32 NativeBootstrapStableFrames = 0;
    FIntPoint NativeBootstrapScenePixels = FIntPoint::ZeroValue;
    uint64 NativeBootstrapLastFrame = MAX_uint64;
    TWeakPtr<SWindow> NativeBootstrapWindow;
    TWeakPtr<SViewport> NativeBootstrapViewport;
    TWeakPtr<SWidget> NativeBootstrapWindowContent;

    void QueueNativeFocus(const TSharedPtr<SWidget>& Widget)
    {
        check(IsInGameThread());
        if (NativeWidgetShuttingDown.load()) return;
        ++NativeFocusRevision;
        PendingNativeFocus = Widget;
        NativeFocusAttempts = 0;
        bNativeFocusPending = true;
    }

    void OnNativeFocusChanging(const FFocusEvent& Event, const FWeakWidgetPath& OldPath,
        const TSharedPtr<SWidget>& OldWidget, const FWidgetPath& NewPath, const TSharedPtr<SWidget>& NewWidget)
    {
        if (FSlateApplication::IsInitialized()
            && Event.GetUser() == FSlateApplication::Get().GetUserIndexForKeyboard()) QueueNativeFocus(NewWidget);
    }

    bool ForwardPendingNativeFocus(float DeltaSeconds)
    {
        check(IsInGameThread());
        if (NativeWidgetShuttingDown.load()) return false;
        if (!bNativeFocusPending || !FSlateApplication::IsInitialized()) return true;
        // OnFocusChanging runs before Slate commits its focus path. Observe it on
        // a later ticker turn, and allow the asynchronous Mac AX cache to catch up.
        if (++NativeFocusAttempts > 60) { bNativeFocusPending = false; return true; }
        FSlateApplication& Slate = FSlateApplication::Get();
        const TSharedPtr<SWidget> Focused = Slate.GetKeyboardFocusedWidget();
        if (Focused != PendingNativeFocus.Pin()) return true;
        const TSharedPtr<SWindow> Window = GEngine && GEngine->GameViewport ? GEngine->GameViewport->GetWindow() : nullptr;
        if (!Window.IsValid() || !Window->GetNativeWindow().IsValid()) return true;
        if (Focused.IsValid() && Slate.FindWidgetWindow(Focused.ToSharedRef()) != Window)
        { bNativeFocusPending = false; return true; }
        const TSharedPtr<GenericApplication> Application = Slate.GetPlatformApplication();
        if (!Application.IsValid()) return true;
        const TSharedRef<FGenericAccessibleMessageHandler> Handler = Application->GetAccessibleMessageHandler();
        if (!Handler->IsActive()) return true;
        const TSharedPtr<IAccessibleWidget> AccessibleWindow = Handler->GetAccessibleWindow(Window->GetNativeWindow().ToSharedRef());
        if (!AccessibleWindow.IsValid()) return true;
        TSharedPtr<IAccessibleWidget> Target = FSlateAccessibleWidgetCache::GetAccessibleWidgetChecked(Focused);
        if (!Target.IsValid() || Target->IsHidden() || !Target->IsEnabled() || !Target->SupportsFocus()) Target = AccessibleWindow;
        const AccessibleWidgetId TargetId = Target->GetId();
        const AccessibleWidgetId WindowId = AccessibleWindow->GetId();
        if (TargetId == IAccessibleWidget::InvalidAccessibleWidgetId) return true;
        const uint64 Revision = NativeFocusRevision.load();
        void* NativeWindow = Window->GetNativeWindow()->GetOSWindowHandle();
        __block bool bComplete = false;
        MainThreadCall(^{
            if (NativeWidgetShuttingDown.load() || Revision != NativeFocusRevision.load()) return;
            // This bridge updates accessibility only in this app's active game
            // window. It never makes the app/window key or calls SetUserFocus.
            if (![NSApp isActive] || [NSApp keyWindow] != (NSWindow*)NativeWindow)
            { bComplete = true; return; }
            FMacAccessibilityManager* Manager = [FMacAccessibilityManager AccessibilityManager];
            // Never create a native cache entry from a focus callback. These
            // lookups cannot enqueue stale initialization after widget teardown.
            if (![Manager AccessibilityElementExists:TargetId] || ![Manager AccessibilityElementExists:WindowId]) return;
            FMacAccessibilityElement* Element = [Manager GetAccessibilityElement:TargetId];
            if (Element == nil || Element.accessibilityRole.length == 0
                || (TargetId != WindowId && Element.OwningWindowId != WindowId)) return;
            if (NSApp.accessibilityApplicationFocusedUIElement != Element)
            {
                // Assign the public AppKit property directly; the element's
                // setAccessibilityFocused: would queue focus back into Slate.
                NSApp.accessibilityApplicationFocusedUIElement = Element;
                NSAccessibilityPostNotification(Element, NSAccessibilityFocusedUIElementChangedNotification);
                UE_LOG(LogTemp, Display, TEXT("BreziAXFocus: forwarded accessibleId=%d windowFallback=%d"), TargetId, TargetId == WindowId);
            }
            bComplete = true;
        }, true);
        if (bComplete && Revision == NativeFocusRevision.load()) bNativeFocusPending = false;
        return true;
    }

    void InstallNativeFocusForwarding()
    {
        check(IsInGameThread());
        if (NativeWidgetShuttingDown.load() || NativeFocusChangingHandle.IsValid()) return;
        // UE's Mac FocusChange event branch is a no-op. There is no public
        // getter for its single-cast delegate: retain that delegate unchanged
        // and observe the public Slate focus multicast alongside the engine.
        NativeFocusChangingHandle = FSlateApplication::Get().OnFocusChanging().AddStatic(&OnNativeFocusChanging);
        NativeFocusTickerHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateStatic(&ForwardPendingNativeFocus), 0.05f);
        QueueNativeFocus(FSlateApplication::Get().GetKeyboardFocusedWidget());
    }

    void StopNativeFocusForwarding()
    {
        check(IsInGameThread());
        if (FSlateApplication::IsInitialized() && NativeFocusChangingHandle.IsValid())
            FSlateApplication::Get().OnFocusChanging().Remove(NativeFocusChangingHandle);
        NativeFocusChangingHandle.Reset();
        if (NativeFocusTickerHandle.IsValid()) FTSTicker::RemoveTicker(NativeFocusTickerHandle);
        NativeFocusTickerHandle.Reset();
        ++NativeFocusRevision;
        bNativeFocusPending = false;
        PendingNativeFocus.Reset();
    }

    void ActivateDeferredNativeWidgetAccess()
    {
        // Keep the platform application alive throughout the synchronous native call.
        // The engine owns its later AX cache work for the application's lifetime.
        const TSharedPtr<GenericApplication> PlatformApplication = FSlateApplication::Get().GetPlatformApplication();
        if (!PlatformApplication.IsValid()) return;
        FMacApplication* Application = static_cast<FMacApplication*>(PlatformApplication.Get());
        __block bool bActive = false;
        MainThreadCall(^{
            if (NativeWidgetShuttingDown.load()) return;
            const TSharedRef<FGenericAccessibleMessageHandler> Handler = Application->GetAccessibleMessageHandler();
            if (Handler->ApplicationIsAccessible() && !Handler->IsActive())
            {
                // UE's public Mac initializer attaches every native window and starts its AX cache.
                // SetActive alone would skip this attachment. Do not repeatedly toggle the bridge:
                // UE 5.8 deliberately leaves its runtime VoiceOver on/off observer inactive.
                Application->OnVoiceoverEnabled();
            }
            bActive = Handler->IsActive();
        }, true);
        if (bActive && !bSkipNativeFocusForwarding) InstallNativeFocusForwarding();
        if (bActive && bSkipNativeFocusForwarding)
            UE_LOG(LogTemp, Display, TEXT("BreziAXBootstrap: diagnostic BreziSkipAXFocusForwarding; AX remains active, only focus forwarding is omitted."));
        UE_LOG(LogTemp, Display, TEXT("Březí native accessibility bridge: %s; native widget cache populates asynchronously."), bActive ? TEXT("active") : TEXT("disabled by engine configuration"));
    }

    bool TryDeferredNativeBootstrap(float DeltaSeconds)
    {
        check(IsInGameThread());
        if (NativeWidgetShuttingDown.load()) return false;
        if (!bEngineInitBarrierReached || !FSlateApplication::IsInitialized()) return true;
        if (NativeBootstrapLastFrame == GFrameCounter) return true;
        NativeBootstrapLastFrame = GFrameCounter;
        if (++NativeBootstrapAttempts > 300)
        {
            NativeBootstrapTickerHandle.Reset();
            UE_LOG(LogTemp, Error, TEXT("BreziAXBootstrap: readiness timed out after engine init; AX activation was not completed."));
            return false;
        }
        FSlateApplication& Slate = FSlateApplication::Get();
        UGameViewportClient* Client = GEngine ? GEngine->GameViewport.Get() : nullptr;
        const UBreziGameViewportClient* Presentation = Cast<UBreziGameViewportClient>(Client);
        const TSharedPtr<SWindow> Window = Client ? Client->GetWindow() : nullptr;
        const TSharedPtr<SViewport> Inner = Client ? Client->GetGameViewportWidget() : nullptr;
        const FSceneViewport* Scene = Client ? Client->GetGameViewport() : nullptr;
        bool bReady = Window.IsValid() && Window->GetNativeWindow().IsValid() && Inner.IsValid() && Scene;
        if (bReady)
        {
            bReady = Slate.GetGameViewport() == Inner && Slate.FindWidgetWindow(Inner.ToSharedRef()) == Window
                && Inner->GetViewportInterface().Pin().Get() == static_cast<const ISlateViewport*>(Scene)
                && static_cast<const ISlateViewport*>(Scene)->UseSeparateRenderTarget()
                && Presentation && Presentation->IsPresentationReadyForCurrentOutput()
                && Inner->GetCachedGeometry().GetLocalSize().X > 0 && Inner->GetCachedGeometry().GetLocalSize().Y > 0;
        }
        if (!bReady)
        {
            NativeBootstrapStableFrames = 0;
            NativeBootstrapScenePixels = FIntPoint::ZeroValue;
            NativeBootstrapWindow.Reset(); NativeBootstrapViewport.Reset(); NativeBootstrapWindowContent.Reset();
            return true;
        }
        const TSharedPtr<SWidget> Content = Window->GetContent();
        const FIntPoint ScenePixels = Scene->GetSizeXY();
        if (Window != NativeBootstrapWindow.Pin() || Inner != NativeBootstrapViewport.Pin()
            || Content != NativeBootstrapWindowContent.Pin() || ScenePixels != NativeBootstrapScenePixels)
            NativeBootstrapStableFrames = 0;
        NativeBootstrapScenePixels = ScenePixels;
        NativeBootstrapWindow = Window; NativeBootstrapViewport = Inner; NativeBootstrapWindowContent = Content;
        if (++NativeBootstrapStableFrames < 3) return true;
        NativeBootstrapTickerHandle.Reset();
        UE_LOG(LogTemp, Display, TEXT("BreziAXBootstrap: engine init barrier passed; inner viewport/window stable for %d frames; activating AX at frame %llu."),
            NativeBootstrapStableFrames, static_cast<unsigned long long>(GFrameCounter));
        ActivateDeferredNativeWidgetAccess();
        return false;
    }

    void StopDeferredNativeBootstrap()
    {
        if (NativeBootstrapTickerHandle.IsValid()) FTSTicker::RemoveTicker(NativeBootstrapTickerHandle);
        NativeBootstrapTickerHandle.Reset();
        NativeBootstrapWindow.Reset(); NativeBootstrapViewport.Reset(); NativeBootstrapWindowContent.Reset();
        NativeBootstrapScenePixels = FIntPoint::ZeroValue;
    }

    void ReadShutdownFixtureWindow(FMacApplication* Application)
    {
        check(IsInGameThread());
        bShutdownStressRequested = FParse::Param(FCommandLine::Get(), TEXT("BreziAXShutdownStress"));
        if (!bShutdownStressRequested || !GEngine || !GEngine->GameViewport) return;
        // All temporary Slate references die before the caller makes a Main call.
        const TSharedPtr<SWindow> Window = GEngine->GameViewport->GetWindow();
        if (!Window.IsValid() || !Window->GetNativeWindow().IsValid()) return;
        const TSharedPtr<IAccessibleWidget> Widget = Application->GetAccessibleMessageHandler()
            ->GetAccessibleWindow(Window->GetNativeWindow().ToSharedRef());
        if (!Widget.IsValid()) return;
        ShutdownStressWindowId = Widget->GetId();
        ShutdownStressSlateChildren = Widget->GetNumberOfChildren();
        const FBox2D Bounds = Widget->GetBounds();
        bShutdownStressHealthyWindow = ShutdownStressSlateChildren > 0 && Widget->IsEnabled()
            && !Widget->IsHidden() && !Widget->GetWidgetName().IsEmpty()
            && FMath::IsFinite(Bounds.Min.X) && FMath::IsFinite(Bounds.Min.Y)
            && FMath::IsFinite(Bounds.Max.X) && FMath::IsFinite(Bounds.Max.Y)
            && Bounds.GetSize().X > 0 && Bounds.GetSize().Y > 0;
    }

    void RunShutdownStockUpdaterFixtureOnMain()
    {
        check([NSThread isMainThread]);
        if (!bShutdownStressRequested) return;
        FMacAccessibilityManager* Manager = [FMacAccessibilityManager AccessibilityManager];
        // Do not seed a fake element: require an already populated real window.
        bShutdownStressWindowInNativeCache = [Manager AccessibilityElementExists:ShutdownStressWindowId];
        if (bShutdownStressWindowInNativeCache)
        {
            FMacAccessibilityElement* Window = [Manager GetAccessibilityElement:ShutdownStressWindowId];
            ShutdownStressNativeChildren = Window.ChildIds.Num();
        }
        ShutdownStressCachedIds = [Manager GetAccessibilityCacheSize];
        const uint64 Before = ShutdownLookupDrops.load();
        const uint64 WindowBefore = ShutdownWindowLookupDrops.load();
        // Unmodified engine implementation: it captures current native cache IDs,
        // queues its actual GT property block and waits. The outer GT is waiting
        // for this Main callback, reproducing the crash's nested run-loop shape.
        // Its widget lookup now resolves the inert handler and cannot reach Slate.
        [Manager UpdateAllCachedProperties];
        ShutdownStressLookupDelta = ShutdownLookupDrops.load() - Before;
        ShutdownStressWindowDelta = ShutdownWindowLookupDrops.load() - WindowBefore;
        bShutdownStressReturned = true;
        // Other already queued stock callbacks can also run in this interval;
        // these deltas are totals/lower bounds, not exclusive per-call timings.
    }

    void WriteShutdownReceipt()
    {
        check(IsInGameThread());
        const bool bStressPassed = bShutdownStressRequested && bShutdownStressHealthyWindow
            && bShutdownStressWindowInNativeCache && ShutdownStressNativeChildren > 0
            && ShutdownStressCachedIds > 1 && bShutdownStressReturned
            && ShutdownStressLookupDelta >= static_cast<uint64>(ShutdownStressCachedIds)
            && ShutdownStressWindowDelta > 0 && bShutdownOriginalActive
            && bSlateDeactivatedOnGameThread && bShutdownMainHandlerMatched
            && ShutdownSinkMainDeactivations.load() == 1 && ShutdownSinkOffMainDeactivations.load() == 0
            && ShutdownOffThreadLookups.load() == 0 && bShutdownNativeCacheEmpty;
        TSharedRef<FJsonObject> Receipt = MakeShared<FJsonObject>();
        Receipt->SetNumberField(TEXT("schemaVersion"), 1);
        Receipt->SetStringField(TEXT("phase"), TEXT("queues-drained-before-slate-shutdown"));
        Receipt->SetStringField(TEXT("status"), bShutdownStressRequested
            ? (bStressPassed ? TEXT("shutdown-stock-updater-fixture-passed") : TEXT("shutdown-stock-updater-fixture-failed"))
            : TEXT("shutdown-handler-handoff-recorded"));
        Receipt->SetNumberField(TEXT("nativeProcessId"), FPlatformProcess::GetCurrentProcessId());
        Receipt->SetBoolField(TEXT("stressRequested"), bShutdownStressRequested);
        Receipt->SetBoolField(TEXT("stressPassed"), bStressPassed);
        Receipt->SetBoolField(TEXT("oldSlateHandlerWasActive"), bShutdownOriginalActive);
        Receipt->SetBoolField(TEXT("slateDeactivatedOnGameThread"), bSlateDeactivatedOnGameThread);
        Receipt->SetBoolField(TEXT("mainObservedExactInertHandler"), bShutdownMainHandlerMatched);
        Receipt->SetNumberField(TEXT("inertMainDeactivations"), ShutdownSinkMainDeactivations.load());
        Receipt->SetNumberField(TEXT("inertOffMainDeactivations"), ShutdownSinkOffMainDeactivations.load());
        Receipt->SetNumberField(TEXT("guardedLookupDrops"), ShutdownLookupDrops.load());
        Receipt->SetNumberField(TEXT("offGameThreadLookups"), ShutdownOffThreadLookups.load());
        Receipt->SetBoolField(TEXT("liveSlateWindowHealthyBeforeHandoff"), bShutdownStressHealthyWindow);
        Receipt->SetBoolField(TEXT("realWindowAlreadyInNativeCache"), bShutdownStressWindowInNativeCache);
        Receipt->SetNumberField(TEXT("windowId"), ShutdownStressWindowId);
        Receipt->SetNumberField(TEXT("slateWindowChildCount"), ShutdownStressSlateChildren);
        Receipt->SetNumberField(TEXT("nativeWindowChildCount"), ShutdownStressNativeChildren);
        Receipt->SetNumberField(TEXT("stockUpdaterCapturedIdCount"), ShutdownStressCachedIds);
        Receipt->SetBoolField(TEXT("stockUpdaterReturned"), bShutdownStressReturned);
        Receipt->SetNumberField(TEXT("queuedLookupDropsDuringStockCall"), ShutdownStressLookupDelta);
        Receipt->SetNumberField(TEXT("windowLookupDropsDuringStockCall"), ShutdownStressWindowDelta);
        Receipt->SetBoolField(TEXT("nativeCacheEmptyAfterDrain"), bShutdownNativeCacheEmpty);
        Receipt->SetBoolField(TEXT("stockUpdaterAndCacheStringsUnchanged"), true);
        Receipt->SetStringField(TEXT("scope"), TEXT("Shutdown-only handler handoff. Real stock updater runs in nested Main/GT wait; all its lookups return null. Counters include any other pending ID-only callbacks. Source ordering plus inert OnDeactivate proves no Slate clear from this Main cleanup; this is not global thread instrumentation. Normal interactive AX and final clean process exit are separate host gates."));
        FString Text;
        FJsonSerializer::Serialize(Receipt, TJsonWriterFactory<>::Create(&Text));
        FString ReportPath;
        FParse::Value(FCommandLine::Get(), TEXT("BreziAXShutdownReport="), ReportPath);
        if (ReportPath.IsEmpty()) ReportPath = FPaths::ProjectSavedDir() / TEXT("Diagnostics/AX/shutdown.json");
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(ReportPath), true);
        if (!FFileHelper::SaveStringToFile(Text, *ReportPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
            UE_LOG(LogTemp, Error, TEXT("BreziAXShutdown: could not write shutdown receipt."));
        if (bShutdownStressRequested)
            UE_LOG(LogTemp, Display, TEXT("BreziAXShutdown stress: passed=%d stockIds=%d queuedDrops=%llu windowDrops=%llu GTDeactivate=%d inertMainDeactivate=%llu."),
                bStressPassed, ShutdownStressCachedIds, ShutdownStressLookupDelta, ShutdownStressWindowDelta,
                bSlateDeactivatedOnGameThread, ShutdownSinkMainDeactivations.load());
    }

    void BeginNativeWidgetShutdown()
    {
        check(IsInGameThread());
        StopDeferredNativeBootstrap();
        StopNativeFocusForwarding();
        if (NativeWidgetShuttingDown.exchange(true)) return;
        BreziAXInitializer::BeginShutdown();
        if (!FSlateApplication::IsInitialized()) return;
        const TSharedPtr<GenericApplication> PlatformApplication = FSlateApplication::Get().GetPlatformApplication();
        if (!PlatformApplication.IsValid()) return;
        FMacApplication* Application = static_cast<FMacApplication*>(PlatformApplication.Get());
        ReadShutdownFixtureWindow(Application);
        RetiredSlateHandler = Application->GetAccessibleMessageHandler();
        const bool bWasActive = RetiredSlateHandler->IsActive();
        bShutdownOriginalActive = bWasActive;
        // No yield/pump between deactivation and publication of the inert handler.
        // Slate's OnDeactivate clears two non-thread-safe widget maps. It must run
        // on GT, before MainThreadCall can re-enter a queued stock property update.
        RetiredSlateHandler->UnbindAccessibleEventDelegate();
        RetiredSlateHandler->SetActive(false);
        bSlateDeactivatedOnGameThread = !RetiredSlateHandler->IsActive();
        const TSharedRef<FShutdownAccessibleMessageHandler> Sink = MakeShared<FShutdownAccessibleMessageHandler>();
        Sink->SetActive(bWasActive);
        FShutdownAccessibleMessageHandler* const SinkPointer = &Sink.Get();
        // Deliberately bypass the Mac override: it registers a user/event producer
        // and schedules a new async VoiceOver bootstrap. The generic setter only
        // assigns the handler. This process-exit handoff is never restored.
        Application->GenericApplication::SetAccessibleMessageHandler(Sink);
        MainThreadCall(^{
            bShutdownMainHandlerMatched = &Application->GetAccessibleMessageHandler().Get() == SinkPointer;
            check(bShutdownMainHandlerMatched);
            RunShutdownStockUpdaterFixtureOnMain();
            // Preserve the stock private-timer/window/native-cache cleanup. Its
            // SetActive(false) now touches only the inert handler, never Slate.
            if (Application->GetAccessibleMessageHandler()->IsActive())
                Application->OnVoiceoverDisabled();
        }, true);
        UE_LOG(LogTemp, Display, TEXT("Březí native accessibility bridge: producers stopped before widget teardown."));
    }

    void ShutdownNativeWidgetAccess()
    {
        check(IsInGameThread());
        NativeWidgetShutdownHandle.Reset();
        BeginNativeWidgetShutdown();
        if (!FSlateApplication::IsInitialized()) return;
        // Cocoa's MainThreadCall is not a FIFO queue fence. Finish both sides of
        // already queued main -> game -> main property/initialization callbacks.
        // The native timer/windows and Slate event producer are already stopped,
        // and OnDeactivate has emptied the Slate ID lookup. These remaining
        // callbacks can finish, but cannot obtain a live Slate widget for new work.
        ProcessGameThreadEvents();
        MainThreadCall(^{}, true);
        ProcessGameThreadEvents();
        MainThreadCall(^{}, true);
        __block int32 LateElements = 0;
        MainThreadCall(^{
            FMacAccessibilityManager* Manager = [FMacAccessibilityManager AccessibilityManager];
            LateElements = [Manager GetAccessibilityCacheSize];
            [Manager Clear];
            // OnVoiceoverDisabled already cleared the engine's private Cocoa
            // focused-element property through its public application API.
            bShutdownNativeCacheEmpty = [Manager IsAccessibilityCacheEmpty];
            check(bShutdownNativeCacheEmpty);
        }, true);
        UE_LOG(LogTemp, Display, TEXT("Březí native accessibility bridge: queues drained; %d late elements cleared before Slate shutdown."), LateElements);
        RetiredSlateHandler.Reset(); // No retained Slate handler is released on Main.
        WriteShutdownReceipt();
        BreziAXInitializer::WriteReceipt("queues-drained-before-slate-shutdown");
    }
#endif

    FBreziDisplayPreferences ReadOnMainThread()
    {
        NSWorkspace* Workspace = [NSWorkspace sharedWorkspace];
        FBreziDisplayPreferences Preferences;
        Preferences.bReduceMotion = [Workspace accessibilityDisplayShouldReduceMotion];
        Preferences.bIncreaseContrast = [Workspace accessibilityDisplayShouldIncreaseContrast];
        Preferences.bReduceTransparency = [Workspace accessibilityDisplayShouldReduceTransparency];
        return Preferences;
    }
}

FBreziDisplayPreferences BreziNativeAccessibility::Read()
{
    __block FBreziDisplayPreferences Preferences;
    MainThreadCall(^{ Preferences = ReadOnMainThread(); }, true);
    return Preferences;
}

void* BreziNativeAccessibility::Observe(TFunction<void(FBreziDisplayPreferences)> Listener)
{
    __block void* Observer = nullptr;
    MainThreadCall(^{
        id Token = [[[NSWorkspace sharedWorkspace] notificationCenter]
            addObserverForName:NSWorkspaceAccessibilityDisplayOptionsDidChangeNotification
            object:nil queue:[NSOperationQueue mainQueue]
            usingBlock:^(NSNotification* Notification)
            {
                if (NativeWidgetShuttingDown.load()) return;
                const FBreziDisplayPreferences Preferences = ReadOnMainThread();
                AsyncTask(ENamedThreads::GameThread, [Listener, Preferences]() {
                    if (!NativeWidgetShuttingDown.load()) Listener(Preferences);
                });
            }];
        Observer = (void*)[Token retain];
    }, true);
    return Observer;
}

void BreziNativeAccessibility::StopObserving(void* Observer)
{
#if WITH_ACCESSIBILITY
    // PlayerController calls this before RemoveViewportWidgetContent in EndPlay.
    // A normal map change still only removes its observer; process exit closes
    // the application bridge while the old widget hierarchy is intact.
    if (IsInGameThread() && IsEngineExitRequested()) BeginNativeWidgetShutdown();
#endif
    if (!Observer) return;
    MainThreadCall(^{
        id Token = (id)Observer;
        [[[NSWorkspace sharedWorkspace] notificationCenter] removeObserver:Token];
        [Token release];
    }, true);
}

void BreziNativeAccessibility::EnableNativeWidgetAccess()
{
#if WITH_ACCESSIBILITY
    check(IsInGameThread());
    if (NativeWidgetShuttingDown.load() || !FSlateApplication::IsInitialized()) return;
    if (bNativeBootstrapRequested) return;
    if (!BreziAXInitializer::VerifyInstalled())
    {
        UE_LOG(LogTemp, Fatal, TEXT("Březí cannot initialize native accessibility: the required initializer repair does not match this engine build. See BreziAXInitializer receipt."));
        return;
    }
    BreziAXInitializer::RunStressIfRequested();
    bNativeBootstrapRequested = true;
    bSkipNativeFocusForwarding = FParse::Param(FCommandLine::Get(), TEXT("BreziSkipAXFocusForwarding"));
    if (!NativeWidgetShutdownHandle.IsValid())
        NativeWidgetShutdownHandle = FSlateApplication::Get().OnPreShutdown().AddStatic(&ShutdownNativeWidgetAccess);
    // EndOfEngineInit follows OnFEngineLoopInitComplete in LaunchEngineLoop.
    // The public helper executes immediately when the phase already passed,
    // unlike subscribing only to a one-shot delegate after engine startup.
    FDelayedAutoRegisterHelper(EDelayedRegisterRunPhase::EndOfEngineInit, []
    {
        check(IsInGameThread());
        if (!NativeWidgetShuttingDown.load()) bEngineInitBarrierReached = true;
    });
    NativeBootstrapTickerHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateStatic(&TryDeferredNativeBootstrap), 0.05f);
    UE_LOG(LogTemp, Display, TEXT("BreziAXBootstrap: requested; waiting for completed engine init and stable attached inner viewport/window."));
#endif
}
